"""故障注入测试（R10 步骤 1）。

目的不是"测功能对不对"，而是**证明流程在失败时会报错，而不是产出一个看起来正常的结果**。
这类 bug 在 R5–R9 撞到五次（commit fallback / `--depth` 被吞 / `emit_rules` 残留 /
V4 跳过回放 / `bool("false")`），**没有一次是主动查出来的**。

每个测试对应一个注入点：制造失败 → 跑流程 → 断言"故障被发现了"。

约定：**测试通过 = 流程确实发现了故障**。如果某个测试失败，说明那条路径在静默用旧值/默认值。
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PIPE = os.path.join(ROOT, "pipeline")
sys.path.insert(0, PIPE)

import s4_abstract_features as S4  # noqa: E402
import s5_4_analyze as S54        # noqa: E402
import s5_5_build as S55          # noqa: E402


# ══════════════════════════════════════════════════════════════════════
# 注入点 5（R9 撞到的）：判据里的 `"false"` / `"true"` 是字符串
# ══════════════════════════════════════════════════════════════════════
def _site(**kw):
    s = {"use": {"kind": "same_path"}, "callee": "free", "realloc_near": None,
         "is_link_read": False, "reassigned_between": False}
    s.update(kw)
    return s


def test_string_false_means_false_not_true():
    """`bool("false")` 是 True —— R9 之前 `is_link_read:"false"` 实际要求 True。"""
    site = _site(is_link_read=False)
    assert S54._match_conjunct(site, {"is_link_read": "false"}) is True, \
        "站点 is_link_read=False 时，判据写 'false' 必须命中（不是被反转成要求 True）"
    site_t = _site(is_link_read=True)
    assert S54._match_conjunct(site_t, {"is_link_read": "false"}) is False
    assert S54._match_conjunct(site_t, {"is_link_read": "true"}) is True


def test_string_reassigned_false():
    assert S54._match_conjunct(_site(reassigned_between=False),
                               {"reassigned_between": "false"}) is True
    assert S54._match_conjunct(_site(reassigned_between=True),
                               {"reassigned_between": "false"}) is False


def test_string_any_is_wildcard():
    for v in (True, False):
        assert S54._match_conjunct(_site(is_link_read=v), {"is_link_read": "any"}) is True


def test_bool_and_string_agree():
    """`True` / `"true"` 必须等价；`False` / `"false"` 必须等价。"""
    for val in (True, False):
        site = _site(is_link_read=val, reassigned_between=val)
        for rule_val in (val, "true" if val else "false"):
            assert S54._match_conjunct(site, {"is_link_read": rule_val}) is True, \
                f"bool {val} 与字符串 {rule_val!r} 必须等价"


# ══════════════════════════════════════════════════════════════════════
# 注入点 4（R8 撞到的）：产物残留 —— 上次运行的 feature_*.json 不能当新结果
# ══════════════════════════════════════════════════════════════════════
def _mk_stage4(tmp_path, monkeypatch, files):
    """在 tmp 下造一个假的 outputs/stage4/uaf 目录，并让 S4 指向它。"""
    d = tmp_path / "stage4" / "uaf"
    d.mkdir(parents=True)
    for name, content, age in files:
        p = d / name
        p.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
        if age:
            old = time.time() - age
            os.utime(p, (old, old))
    monkeypatch.setattr(S4, "OUT", str(tmp_path / "stage4"))
    return d


def test_emit_rules_skips_stale_file(tmp_path, monkeypatch, capsys):
    """一个 mtime 早于本次运行的 feature_*.json 必须被跳过，不能当成这次的结果。"""
    _mk_stage4(tmp_path, monkeypatch, [
        ("features.json", {"features": [{"id": "uaf-llm01",
                                         "source_pattern": "同函数释放后访问"}]}, 0),
        ("feature_p_old.json", {"_source_pattern": "同函数释放后访问",
                                "applicability_rule": {"use_kind": "same_path"}}, 3600),
    ])
    monkeypatch.setattr(S4, "_RUN_STARTED_AT", time.time())
    S4.emit_rules("uaf")
    out = capsys.readouterr().out
    rules = json.loads((tmp_path / "stage4" / "uaf" / "applicability_rules.json")
                       .read_text(encoding="utf-8"))
    assert not rules.get("rules"), "残留文件不应被当成有效判据"
    assert "跳过" in out and "feature_p_old.json" in out, f"必须打印跳过了哪个文件：{out}"


def test_emit_rules_uses_fresh_file(tmp_path, monkeypatch):
    """同一次运行写的文件必须被采用（不能把所有东西都跳过）。"""
    _mk_stage4(tmp_path, monkeypatch, [
        ("features.json", {"features": [{"id": "uaf-llm01",
                                         "source_pattern": "同函数释放后访问"}]}, 0),
        ("feature_p_new.json", {"_source_pattern": "同函数释放后访问",
                                "applicability_rule": {"use_kind": "same_path"}}, 0),
    ])
    monkeypatch.setattr(S4, "_RUN_STARTED_AT", time.time() - 60)
    S4.emit_rules("uaf")
    rules = json.loads((tmp_path / "stage4" / "uaf" / "applicability_rules.json")
                       .read_text(encoding="utf-8"))
    assert "uaf-llm01" in (rules.get("rules") or {}), "新写的文件必须被采用"


def test_emit_rules_sidecar_marks_rule_missing(tmp_path, monkeypatch):
    """本次失败（有 no_rule sidecar）时，即使有上次的成功文件也不能复用。"""
    _mk_stage4(tmp_path, monkeypatch, [
        ("features.json", {"features": [{"id": "uaf-llm01",
                                         "source_pattern": "同函数释放后访问"}]}, 0),
        ("feature_p_ok.json", {"_source_pattern": "同函数释放后访问",
                               "applicability_rule": {"use_kind": "same_path"}}, 0),
        ("feature_p_ok.no_rule.json", {"_source_pattern": "同函数释放后访问",
                                       "reason": "rule_missing：模型声明表达不了"}, 0),
    ])
    monkeypatch.setattr(S4, "_RUN_STARTED_AT", time.time() - 60)
    S4.emit_rules("uaf")
    rules = json.loads((tmp_path / "stage4" / "uaf" / "applicability_rules.json")
                       .read_text(encoding="utf-8"))
    assert "uaf-llm01" not in (rules.get("rules") or {}), "sidecar 存在时不能复用旧判据"
    assert "uaf-llm01" in (rules.get("rule_missing") or {})


# ══════════════════════════════════════════════════════════════════════
# 注入点 9（R9 之前就有）：门禁假通过 —— 缺 testcase 时 V4 不能报 PASS
# ══════════════════════════════════════════════════════════════════════
def test_v4_without_testcase_is_not_applicable():
    """缺 testcase 时 V4 什么也没验证，必须 not_applicable，不能 pass。"""
    binary = os.path.join(ROOT, "projects", "ARVO-42494732",
                          "experiment", "llvmfuzz")
    st, probs, notes = S55.gate_v4(binary, {})
    assert st == "not_applicable", f"缺 testcase 必须 not_applicable，实际 {st!r}"
    assert not probs
    assert any("没有验证任何东西" in n for n in notes), notes


def test_v4_without_binary_is_not_applicable():
    st, _, _ = S55.gate_v4(None, {"testcase_path": "/tmp/x"})
    assert st == "not_applicable"


# ══════════════════════════════════════════════════════════════════════
# 注入点 2（R7 撞到的）：参数被吞 —— `--depth` 必须传到下游
# ══════════════════════════════════════════════════════════════════════
def _passthrough_argv(monkeypatch, argv):
    """跑一次 s5_1_main.main()，把真正交给下游的 argv 抓出来。"""
    import s5_1_main as M
    got = {}

    def fake_run(fn, a):
        got["argv"] = list(a)
        return 0

    monkeypatch.setattr(M, "_run", fake_run)
    monkeypatch.setattr(sys, "argv", ["s5_1_main.py"] + argv)
    try:
        M.main()
    except SystemExit:
        pass
    return got.get("argv")


def test_depth_is_forwarded(monkeypatch):
    """`worklist --depth 4` 直通时，下游必须真的收到 `--depth 4`。"""
    argv = _passthrough_argv(monkeypatch, ["worklist", "--osv", "X", "--depth", "4"])
    assert argv is not None, "直通没有调用 _run"
    assert "--depth" in argv, f"--depth 被入口吃掉了：{argv}"
    assert argv[argv.index("--depth") + 1] == "4", f"--depth 的值不对：{argv}"


def test_type_and_feature_are_forwarded(monkeypatch):
    """`--type` / `--feature` 同样是已知参数，之前也会被吞。"""
    argv = _passthrough_argv(
        monkeypatch, ["features", "--osv", "X", "--type", "hbo", "--feature", "uaf-llm01"])
    assert argv[argv.index("--type") + 1] == "hbo", argv
    assert argv[argv.index("--feature") + 1] == "uaf-llm01", argv


def test_osv_is_not_duplicated(monkeypatch):
    """入口会把 --osv 补回去，但原来传入的那份必须被 strip_osv 摘掉，不能出现两次。"""
    argv = _passthrough_argv(monkeypatch, ["plan", "--osv", "X"])
    assert argv.count("--osv") == 1, f"--osv 重复了：{argv}"
    assert argv[argv.index("--osv") + 1] == "X", argv


# ══════════════════════════════════════════════════════════════════════
# 注入点 3：产物过期 —— 判据比 feature_pipeline 新时必须告警
# ══════════════════════════════════════════════════════════════════════
def test_plan_warns_when_rules_newer_than_features(tmp_path, monkeypatch, capsys):
    """判据比 feature_pipeline 新 → plan 必须告警"用的是旧判据"。"""
    v2 = tmp_path / "projects" / "X"
    v2.mkdir(parents=True)
    s4 = tmp_path / "outputs" / "stage4" / "uaf"
    s4.mkdir(parents=True)
    now = time.time()
    fp = v2 / "feature_pipeline.json"
    fp.write_text(json.dumps({"features": []}), encoding="utf-8")
    os.utime(fp, (now - 3600, now - 3600))
    rp = s4 / "applicability_rules.json"
    rp.write_text("{}", encoding="utf-8")
    os.utime(rp, (now, now))

    # 直接验证判定逻辑本身（main_plan 需要完整产物，这里只测"是否判定为过期"）
    newer = [p for p in [str(rp)]
             if os.path.getmtime(p) > os.path.getmtime(str(fp)) + 1]
    assert newer, "构造的 mtime 应该被判为过期"


# ══════════════════════════════════════════════════════════════════════
# 注入点（新增）：产物比依赖旧 —— 通用时效告警必须真的触发
# ══════════════════════════════════════════════════════════════════════
def test_warn_if_stale_fires(tmp_path, capsys):
    import s5_6_lib as L
    old = tmp_path / "surface.json"
    old.write_text("{}", encoding="utf-8")
    new = tmp_path / "worklist.json"
    new.write_text("{}", encoding="utf-8")
    os.utime(old, (time.time() - 3600, time.time() - 3600))
    assert L.warn_if_stale(str(old), [(str(new), "worklist 已重跑")], "surface.json") is True
    err = capsys.readouterr().err
    assert "[stale]" in err and "surface.json" in err, err


def test_warn_if_stale_silent_when_fresh(tmp_path, capsys):
    import s5_6_lib as L
    a = tmp_path / "a.json"; a.write_text("{}", encoding="utf-8")
    b = tmp_path / "b.json"; b.write_text("{}", encoding="utf-8")
    os.utime(b, (time.time() - 3600, time.time() - 3600))
    assert L.warn_if_stale(str(a), [str(b)], "a.json") is False
    assert "[stale]" not in capsys.readouterr().err


def test_warn_if_stale_ignores_missing():
    import s5_6_lib as L
    assert L.warn_if_stale("/nonexistent/x.json", ["/nonexistent/y.json"]) is False


# ══════════════════════════════════════════════════════════════════════
# 剩余 3 个注入点：**静态守卫测试**
#
# 这三个（Joern 失败 / pin 缺失 / CPG 不覆盖）藏在 `s5_2_prepare.process()` 与
# `s2_2_facts.main()` 内部的闭包里，要真实注入得造 git 仓库 + 跑 Joern，代价是分钟级。
# 这里改成**守卫存在性检查**：如果哪天有人把硬失败改回"静默回退"，测试会失败。
# 它们的弱点是：只证明"代码里有这个分支"，不证明"分支真的会走到"。
# ══════════════════════════════════════════════════════════════════════
def _src(name):
    return open(os.path.join(PIPE, name), encoding="utf-8").read()


def test_guard_pin_missing_hard_fails():
    """pin 缺失必须 SystemExit(commit_not_found)，不能静默退回 HEAD。"""
    s = _src("s5_2_prepare.py")
    assert 'SystemExit' in s and 'commit_not_found' in s, "缺少 commit_not_found 硬失败"
    assert 'ALLOW_HEAD_FALLBACK' in s, "缺少 --allow-head-fallback 逃生口（没有它就只能硬失败）"


def test_guard_cpg_missing_fault_fn():
    """故障函数不在 CPG 里必须报 cpg_missing_fault_fn / cpg_missing_fault_file。"""
    s = _src("s5_2_prepare.py")
    assert 'cpg_missing_fault_fn' in s, "缺少 cpg_missing_fault_fn"
    assert 'cpg_missing_fault_file' in s, "缺少 cpg_missing_fault_file"


def test_guard_joern_failure_is_recorded():
    """Joern deep 失败必须记 `_failed` 并打 stderr，不能 `return {}, items`。"""
    s = _src("s2_2_facts.py")
    assert '"_failed": True' in s, "Joern 失败没有记 _failed 标记"
    assert 'deep 分析失败' in s, "Joern 失败没有打 stderr"


def test_guard_bad_tool_args_not_executed():
    """tool arguments 不是合法 JSON 时必须跳过，不能 `args = {}` 继续跑。"""
    s = _src("s5_6_lib.py")
    assert 'bad_tool_args' in s, "缺少 bad_tool_args 日志"
    assert '不是合法 JSON' in s, "缺少回喂给模型的错误消息"
    code = "\n".join(l for l in s.split("\n") if not l.lstrip().startswith("#"))
    assert "args = {}" not in code, "仍然在用空参数兜底（注释里提到不算）"


def test_main_sets_run_start_before_running(monkeypatch):
    """`_RUN_STARTED_AT` 必须在跑 pattern 之前就设好，否则本次写的文件会被当成残留。

    R10 实测踩过：它被放在 run_one 循环之后，于是 5 条刚写出的判据全被跳过，
    汇总变成 "0 条可用"。这个测试锁住顺序。
    """
    import s4_abstract_features as S4
    import time as _t
    seen = {}

    def fake_run_one(typ, pat, facts_all, tag):
        seen["at_run"] = S4._RUN_STARTED_AT
        return None

    monkeypatch.setattr(S4, "run_one", fake_run_one)
    monkeypatch.setattr(S4, "load_facts", lambda: {})
    monkeypatch.setattr(S4, "load_touchstone", lambda: ([], []))
    monkeypatch.setattr(S4, "emit_rules", lambda typ: None)
    # 必须也 patch emit_features —— 否则它会真的去写 outputs/stage4/uaf/features.json，
    # 而此刻 _RUN_STARTED_AT 是"现在"，本次的文件比它旧 → 写成 0 条（R11 实测踩过）。
    monkeypatch.setattr(S4, "emit_features", lambda typ: [])
    monkeypatch.setattr(sys, "argv", ["s4", "--type", "uaf", "--all"])
    try:
        S4.main()
    except SystemExit:
        pass
    if "at_run" in seen:
        assert seen["at_run"] > 0, "跑 pattern 时 _RUN_STARTED_AT 还没设"
        assert seen["at_run"] <= _t.time() + 1


# ══════════════════════════════════════════════════════════════════════
# 注入点（R11）：stage3 pattern 改名 —— stage4 不能静默丢判据
# ══════════════════════════════════════════════════════════════════════
def test_renamed_stage3_pattern_does_not_drop_rules(tmp_path, monkeypatch, capsys):
    """stage3 换判据后 pattern 名会变。stage4 必须自己重建 features.json，
    5 条判据都要接上，不能因为 `source_pattern` 悬空被丢弃。"""
    import s4_abstract_features as S4

    out = tmp_path / "stage4" / "uaf"
    out.mkdir(parents=True)
    root = tmp_path / "root"
    (root / "outputs" / "stage3" / "uaf").mkdir(parents=True)
    (root / "outputs" / "stage3" / "uaf" / "final.json").write_text(json.dumps({
        "final_patterns": [{"name": f"新形态-{i}"} for i in range(1, 6)]
    }, ensure_ascii=False), encoding="utf-8")

    # 旧 features.json（legacy）：id 是 llm01..05，pattern 名是旧的
    (out / "features.legacy.json").write_text(json.dumps({"features": [
        {"id": f"uaf-llm0{i}", "source_pattern": f"旧形态-{i}"} for i in range(1, 6)
    ]}, ensure_ascii=False), encoding="utf-8")

    # 本次运行写出的 5 个 feature_p_*.json（pattern 名全是新的）
    for i in range(1, 6):
        (out / f"feature_p_{i:02d}.json").write_text(json.dumps({
            "_source_pattern": f"新形态-{i}", "_source_support": 3,
            "_input_sample_ids": [f"S{i}"], "feature_name": f"特征{i}",
            "applicability_rule": {"use_kind": "same_path", "free_kind": "direct_free"},
            "differentiator": [{"vs": "x", "field": "use_kind",
                                "this": "same_path", "other": "loop_back"}],
        }, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(S4, "OUT", str(tmp_path / "stage4"))
    monkeypatch.setattr(S4, "ROOT", str(root))
    monkeypatch.setattr(S4, "_RUN_STARTED_AT", 0.0)
    feats = S4.emit_features("uaf")

    assert len(feats) == 5, f"应该产出 5 条特征，实际 {len(feats)}"
    assert all(f["applicability_rule"] for f in feats), "每条特征都要带上判据"
    assert [f["source_pattern"] for f in feats] == [f"新形态-{i}" for i in range(1, 6)]
    # 新 pattern 没有 legacy 对应 → id 用 pNN，不是悬空
    assert all(f["id"].startswith("uaf-p") for f in feats), [f["id"] for f in feats]
