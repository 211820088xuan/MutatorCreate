#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：**N33 的离线预测器** —— 在建镜像**之前**判断「era Dockerfile 是否会因包已下架而构建失败」。

为什么值得做：`dockerfile_drift` 是 W5 两个新项目（openh264 0/3、flatbuffers 剩余 3 条）的死因，
而它**在建镜像之前就可判**：
  ① 取该 crash 当年的 **era Dockerfile**（oss-fuzz 仓库里 `projects/<p>/Dockerfile` 在
     crash 日期之前最后一次修改的版本）；
  ② 抽出它 `apt-get install` 的包名；
  ③ 在**本地已有的 base-builder 镜像**里跑一次 `apt-cache policy` 批量查可安装性。
成本：每项目 1–2 次 GitHub API + **全部项目共用 1 次 docker run**（秒级），
对比「建镜像 2.3–2.9GB + 探针 ~10–30min」→ 便宜两三个数量级。

✅ 已知答案校验（这是它有没有用的唯一标准）：
  * openh264 的 era Dockerfile 含 `libstdc++-5-dev` → 必须判**不可安装** → 预测 ⛔（实测 0/3）
  * c-blosc2 / hunspell（实测 98%/100% 可构建）→ 必须判**全部可安装** → 预测 ✅（否则就是误报）

复算：python3 preflight/w5_predict_dockerfile_drift.py [--projects a,b] [--selftest]
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import repro_common as rc            # noqa: E402

MANIFEST = os.path.join(rc.ARTIFACTS, "repro_manifest.jsonl")
DATASET = os.path.join(rc.REPRO_DIR, "repro_dataset.jsonl")
# apt-get install 的包名：支持 `-y`/`--no-install-recommends` 等 flag、多行续行、`=版本` 钉定
# ⚠ [W5 修] 原写法用 `re.S` + `(.*?)(?:&&|…|$)` → `.` 跨行、`$` 在非 MULTILINE 下只匹配串尾，
#   于是一路吃到下一条 `RUN git clone …`，把 `git/clone/1/https/openh264` 全当成包名
#   （✅ 被本文件的自测抓到）。改为**按行**捕获，再在行内切 `&&`/`||`/`;`。
APT_RE = re.compile(r"apt-get\s+(?:install|build-dep)\s+([^\n]*)")
CMD_SEP_RE = re.compile(r"&&|\|\||;")
PKG_RE = re.compile(r"(?<![\w.-])([a-z0-9][a-z0-9.+-]{1,})(?::[a-z0-9]+)?(?:=[\w.+-]+)?(?![\w.-])")
APT_FLAGS = {"-y", "--yes", "-q", "--quiet", "--no-install-recommends", "--no-upgrade",
             "-qq", "install", "update", "&&", "apt-get", "sudo"}


def extract_apt_packages(dockerfile_text):
    """从 Dockerfile 文本抽出所有 `apt-get install` 的包名（去 flag、去版本钉定、去重保序）。

    纯函数、可单测。多行续行（`\\`）先拼回一行，再**按行**取 `apt-get install` 之后的部分，
    并在行内切掉 `&&`/`||`/`;` 之后的命令（避免把 `make`/`git clone` 的词当包名）。
    """
    if not dockerfile_text:
        return []
    txt = dockerfile_text.replace("\\\n", " ")          # 续行拼回一行
    pkgs, seen = [], set()
    for m in APT_RE.finditer(txt):
        blob = CMD_SEP_RE.split(m.group(1), 1)[0]        # 只保留 install 自己的参数段
        for tok in re.split(r"[\s]+", blob):
            t = tok.strip().strip("'\"")
            if not t or t in APT_FLAGS or t.startswith("-"):
                continue
            t = t.split("=", 1)[0]                       # 去掉 =版本 钉定
            if t.count(":") == 1 and not t.startswith("lib"):
                t = t.split(":", 1)[0]                   # 去掉 :arch（libstdc++-9-dev:i386 除外）
            if not re.match(r"^[a-z0-9][a-z0-9.+-]*$", t):
                continue
            if t not in seen:
                seen.add(t)
                pkgs.append(t)
    return pkgs


def era_dockerfile(project, before_date, repo="google/oss-fuzz"):
    """取 `projects/<p>/Dockerfile` 在 `before_date`（YYYY-MM-DD）之前最后一次修改的版本。

    → (text, commit_sha, err)。用 GitHub API 列该路径的历史（1 次调用），再走 raw 取内容。
    """
    path = f"projects/{project}/Dockerfile"
    url = (f"https://api.github.com/repos/{repo}/commits?path={path}"
           f"&until={before_date}T23:59:59Z&per_page=1")
    txt, code = rc.http_get(url, tries=2, timeout=25)
    if code not in (200, "cache"):
        return None, None, f"api_{code}"
    try:
        arr = json.loads(txt)
        sha = arr[0]["sha"] if arr else None
    except (ValueError, KeyError, IndexError):
        return None, None, "parse"
    if not sha:
        return None, None, "no_commit_before_date"
    raw, c2 = rc.http_get(f"https://raw.githubusercontent.com/{repo}/{sha}/{path}",
                          tries=2, timeout=25)
    if c2 not in (200, "cache"):
        return None, sha, f"raw_{c2}"
    return raw, sha, None


def check_installable(packages, image="gcr.io/oss-fuzz-base/base-builder:latest", timeout=600):
    """在本地 base-builder 里一次性查全部包的可安装性 → {pkg: bool}。

    **全部项目共用这一次 docker run**（`apt-cache policy` 只读缓存，不装东西）。
    """
    if not packages:
        return {}
    pkgs = sorted(set(packages))
    cmd = ["docker", "run", "--rm", "--network=host", image, "bash", "-c",
           "apt-get update -qq >/dev/null 2>&1; "
           "for p in " + " ".join(pkgs) + "; do "
           "c=$(apt-cache policy $p 2>/dev/null | sed -n 's/^  Candidate: //p'); "
           "echo \"$p=$c\"; done"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError) as e:
        return {p: None for p in pkgs}, f"docker_error:{e}"
    out = {}
    for line in r.stdout.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in pkgs or k.replace("-", "_") in pkgs:
            out[k] = bool(v) and v.lower() != "(none)"
    return out, None


def selftest():
    """纯函数部分的已知答案自测（不碰网络/docker）。"""
    fails = []

    def ck(c, m):
        print(("  ✅ " if c else "  ❌ ") + m)
        if not c:
            fails.append(m)

    print("═" * 78)
    print("自测：extract_apt_packages（era Dockerfile 解析）")
    print("═" * 78)
    # ✅ openh264 的 era Dockerfile 实际形态（W5 实测日志里的那一行）
    oh = ("FROM gcr.io/oss-fuzz-base/base-builder\n"
          "RUN apt-get update && apt-get install -y libstdc++-5-dev nasm subversion\n"
          "RUN git clone --depth 1 https://github.com/cisco/openh264.git openh264\n")
    got = extract_apt_packages(oh)
    ck("libstdc++-5-dev" in got, f"openh264 era 形态 → 抓到 libstdc++-5-dev（实得 {got}）")
    ck("nasm" in got and "subversion" in got, f"同行多包都抓到（{got}）")
    ck("git" not in got and "clone" not in got, f"不把 `git clone` 的词当包名（{got}）")

    # 多行续行 + --no-install-recommends + 版本钉定
    multi = ("RUN apt-get update && apt-get install -y --no-install-recommends \\\n"
             "    autoconf \\\n"
             "    libtool=2.4.6-0.1 \\\n"
             "    texinfo\n")
    got2 = extract_apt_packages(multi)
    ck(got2 == ["autoconf", "libtool", "texinfo"], f"续行/flag/版本钉定都正确处理（{got2}）")

    # 架构限定包名（libstdc++-9-dev:i386）→ 去掉 :arch
    arch = "RUN apt-get install -y ffmpeg libstdc++-9-dev libstdc++-9-dev:i386 nasm\n"
    got3 = extract_apt_packages(arch)
    ck("ffmpeg" in got3 and "libstdc++-9-dev" in got3,
       f"含 :i386 的包也能归一到包名（{got3}）")
    ck(extract_apt_packages("") == [] and extract_apt_packages(None) == [],
       "空输入 → 空列表（不抛异常）")
    ck(extract_apt_packages("FROM x\nRUN make install\n") == [],
       "没有 apt-get install → 空列表（不误抓 `make install`）")

    print("\n" + (f"❌ {len(fails)} 项未通过：{fails}" if fails else "✅ 全部通过"))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--projects", default=None, help="逗号分隔；默认 = 未试过且池 ≥20 的候选")
    ap.add_argument("--min-pool", type=int, default=20)
    ap.add_argument("--json", default=os.path.join(HERE, "w5_predict_dockerfile_drift.json"))
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    man = [json.loads(l) for l in open(MANIFEST, encoding="utf-8")]
    done = {json.loads(l)["osv_id"] for l in open(DATASET, encoding="utf-8")}
    pool = collections.defaultdict(list)
    for r in man:
        if r.get("skip_reason") or r["osv_id"] in done or not r.get("fixed_commit"):
            continue
        pool[r["project"]].append(r)
    if a.projects:
        targets = [p.strip() for p in a.projects.split(",") if p.strip()]
    else:
        targets = [p for p, rs in sorted(pool.items(), key=lambda kv: -len(kv[1]))
                   if len(rs) >= a.min_pool][:12]

    print("═" * 96)
    print("W5 N33 离线预测器：era Dockerfile 的 apt 包是否还装得上（建镜像**之前**判）")
    print("═" * 96)
    allpkgs, per = {}, {}
    allrows = collections.defaultdict(list)
    for r in man:
        if not r.get("skip_reason"):
            allrows[r["project"]].append(r)
    for p in targets:
        rs = pool.get(p) or []
        # [W5] 显式点名的项目即使池已榨干也要能查 —— 否则**没法用已知答案校验预测器**
        # （c-blosc2/hunspell 池为 0，但它们实测 98%/100% 可构建，是必须过的正对照）。
        if not rs:
            rs = allrows.get(p) or []
            if rs:
                print(f"  ⓘ {p}: 未采样池为 0 → 用该项目全部 {len(rs)} 条主线记录取 era 年份（仅作已知答案校验）")
        if not rs:
            print(f"  ⓘ {p}: 无任何记录，跳过")
            continue
        # 用池里**最老**那条 crash 的年份作 era 上界（最老 = 最容易踩下架包）
        yrs = sorted(str(r.get("osv_year")) for r in rs if r.get("osv_year"))
        date = f"{yrs[0]}-12-31" if yrs else "2021-12-31"
        txt, sha, err = era_dockerfile(p, date)
        if err:
            print(f"  ⓘ {p:<16}取 era Dockerfile 失败（{err}）→ 无法判定")
            per[p] = {"pool": len(rs), "era_date": date, "error": err}
            continue
        pkgs = extract_apt_packages(txt)
        per[p] = {"pool": len(rs), "era_date": date, "era_sha": sha[:12], "packages": pkgs}
        allpkgs[p] = pkgs
        print(f"  {p:<16}池 {len(rs):>3} | era@{date[:4]} {sha[:10]} | apt 包 {len(pkgs)} 个: "
              f"{', '.join(pkgs[:6])}{'…' if len(pkgs) > 6 else ''}")

    flat = sorted({x for v in allpkgs.values() for x in v})
    if not flat:
        print("\n没有可查的包 → 结束")
        return 0
    print(f"\n在本地 base-builder 里一次性查 {len(flat)} 个包的可安装性（1 次 docker run）…")
    res, derr = check_installable(flat)
    if derr:
        print(f"  ⚠ {derr} → 无法判定")
        return 1
    bad = sorted(k for k, v in res.items() if v is False)
    print(f"  可安装 {sum(1 for v in res.values() if v)} / 不可安装 **{len(bad)}**"
          + (f"：{bad}" if bad else ""))

    print(f"\n{'项目':<16}{'池':>5}{'apt包':>7}{'不可安装':>9}  预测")
    print("─" * 96)
    verdicts = {}
    for p, info in per.items():
        pkgs = info.get("packages") or []
        if info.get("error"):
            print(f"{p:<16}{info['pool']:>5}{'—':>7}{'—':>9}  ⓘ 无法判定（{info['error']}）")
            verdicts[p] = "undecidable"
            continue
        dead = [x for x in pkgs if res.get(x) is False]
        v = "⛔ 预测 dockerfile_drift" if dead else "✅ 包都装得上（该维度无风险）"
        verdicts[p] = "block" if dead else "pass"
        print(f"{p:<16}{info['pool']:>5}{len(pkgs):>7}{len(dead):>9}  {v}"
              + (f"：{dead}" if dead else ""))

    with open(a.json, "w", encoding="utf-8") as f:
        json.dump({"per_project": per, "installability": res, "verdicts": verdicts},
                  f, ensure_ascii=False, indent=1)
    print(f"\n→ 落盘 {os.path.relpath(a.json, ROOT)}")
    print("⚠ 这只覆盖 N33 一个维度；`-Werror`（opensc 0/3 的死因）**离线仍判不了** → 探针不可省")
    return 0


if __name__ == "__main__":
    sys.exit(main())
