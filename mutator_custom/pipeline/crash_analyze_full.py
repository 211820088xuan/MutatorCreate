#!/usr/bin/env python3
# crash_analyze_full.py —— 生成全面的崩溃报告（输入结构/崩溃信息/崩溃原因/复现）
# usage: python3 crash_analyze_full.py <mode> <suffix>
import sys, subprocess, glob, os, re, hashlib

BIN = "/root/gyx/mutator_create/mutator_custom/blosc2_bins/decompress_chunk_nocov"
BASE = "/root/gyx/mutator_create/mutator_custom/fuzz_exp_3h"

CODEC_NAME = {0: "blosclz", 1: "lz4", 2: "lz4hc", 4: "zlib", 5: "zstd", 6: "ndlz"}

# 已知崩溃点的根因说明
ROOT_CAUSE = {
    "ndlz4_decompress": "ndlz4_decompress 中 memset(op,0,blockshape[0]*blockshape[1]) 越界写："
                        "blockshape 两个值来自输入 payload，乘积巨大，超过输出缓冲区",
    "ndlz8_decompress": "ndlz8_decompress 中 memset 按 blockshape 乘积越界写（同 ndlz4 的 blockshape 溢出）",
}

mode, suffix = sys.argv[1], sys.argv[2]
run_dir = f"{BASE}/{mode}_{suffix}"
rep_dir = f"{BASE}/replay/{mode}_{suffix}"
os.makedirs(f"{rep_dir}/crash", exist_ok=True)

le32 = lambda b: int.from_bytes(b, 'little')

def parse_header(data):
    if len(data) < 16:
        return None
    return {
        "version": data[0], "versionlz": data[1], "flags": data[2], "typesize": data[3],
        "nbytes": le32(data[4:8]), "blocksize": le32(data[8:12]), "cbytes": le32(data[12:16]),
    }

parts = []
arts = sorted(glob.glob(f"{run_dir}/art/*"))
parts.append(f"# {mode}_{suffix} 崩溃报告\n")
parts.append(f"崩溃总数：{len(arts)}\n")

for idx, cf_path in enumerate(arts):
    if not os.path.isfile(cf_path):
        continue
    name = os.path.basename(cf_path)
    data = open(cf_path, 'rb').read()
    sha = hashlib.sha1(data).hexdigest()
    hdr = parse_header(data)
    codec_id = (hdr["flags"] >> 5) if hdr else None
    codec = CODEC_NAME.get(codec_id, f"unknown({codec_id})") if codec_id is not None else "?"

    # 重放复现
    r = subprocess.run([BIN, "-runs=1", cf_path], capture_output=True, text=True, timeout=60)
    log = r.stdout + r.stderr
    with open(f"{rep_dir}/crash/{name}.log", "w") as f:
        f.write(log)

    m_type = re.search(r"ERROR: AddressSanitizer: (\S+)", log)
    m_rw = re.search(r"(READ|WRITE) of size (\d+)", log)
    top = None
    frames = []
    for ln in log.splitlines():
        if re.search(r"#\d+ 0x[0-9a-f]+ in \w+ .*\.(c|h):\d+", ln):
            f = ln.split(' in ', 1)[1] if ' in ' in ln else ln
            if top is None:
                top = f
            frames.append(f.split(' ')[0] if f else ln)  # 只取函数名+位置
    top_fn = top.split(' ')[0] if top else "?"

    # 崩溃原因
    rw = (m_rw.group(1), int(m_rw.group(2))) if m_rw else ("?", "?")
    ctype = m_type.group(1) if m_type else "?"
    if ctype == "heap-buffer-overflow":
        direct = f"堆缓冲区越界{'写' if rw[0]=='WRITE' else '读'}，大小 {rw[1]} 字节"
    elif ctype == "SEGV":
        direct = "段错误（非法内存访问）"
    else:
        direct = ctype
    root = ROOT_CAUSE.get(top_fn, "（见完整调用栈）")

    parts.append(f"\n## 崩溃 #{idx+1}\n")
    parts.append(f"### 输入信息\n")
    parts.append(f"- 文件：`{name}`")
    parts.append(f"- SHA1：`{sha}`")
    parts.append(f"- 大小：{len(data)} 字节")
    parts.append(f"- codec：{codec}（flags=0x{hdr['flags']:02x}，codec_id={codec_id}）" if hdr else "- codec：?")
    if hdr:
        parts.append(f"- blosc2 头：version={hdr['version']} versionlz={hdr['versionlz']} "
                     f"flags=0x{hdr['flags']:02x} typesize={hdr['typesize']}")
        parts.append(f"- nbytes={hdr['nbytes']} blocksize={hdr['blocksize']} cbytes={hdr['cbytes']}")
        parts.append(f"- payload 大小：{len(data)-16} 字节")
    parts.append(f"- 输入 hex：`{data.hex()}`")

    parts.append(f"\n### 崩溃信息\n")
    parts.append(f"- 类型：{ctype}")
    parts.append(f"- 操作：{rw[0]} {rw[1]} 字节")
    parts.append(f"- 崩溃位置：`{top}`")
    parts.append(f"- 完整 ASan 输出：`replay/{mode}_{suffix}/crash/{name}.log`")

    parts.append(f"\n### 崩溃原因\n")
    parts.append(f"- 直接原因：{direct}")
    parts.append(f"- 根因：{root}")

    parts.append(f"\n### 复现\n")
    parts.append(f"- 命令：`{BIN} -runs=1 <输入文件>`")
    parts.append(f"- 复现结果：{'复现成功' if (m_type or 'ERROR' in log) else '未复现'}")

with open(f"{rep_dir}/crash_report_full.md", "w") as f:
    f.write("\n".join(parts) + "\n")

print(f"{mode}_{suffix}: 已生成 crash_report_full.md（{len(arts)} 个崩溃）")
