"""stage5 V2 的契约与负例测试。

TDD 顺序：本文件里的测试先于实现存在。Task 5 完成前，
test_blocked_plan_cannot_generate_code 应当 FAIL（这正是预期的 RED）。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(os.path.dirname(HERE), "pipeline")
S5 = os.path.join(PIPE, "s5_mutator.py")


def run_generator(plan_path, out_dir, extra=None):
    """调用 s5_mutator.py 的 generate 阶段；返回 CompletedProcess。"""
    cmd = [sys.executable, S5, "generate", "--plan", str(plan_path), "--out", str(out_dir)]
    return subprocess.run(cmd + (extra or []), capture_output=True, text=True, timeout=600)


def test_blocked_plan_cannot_generate_code(tmp_path):
    """plan.status=blocked 时，生成器必须非零退出，且不创建 mutator.c。"""
    plan = {"schema_version": "stage5.mutation_plan.v1", "status": "blocked",
            "blockers": ["no complete field-to-condition mapping"]}
    p = tmp_path / "mutation_plan.json"
    p.write_text(json.dumps(plan), encoding="utf-8")
    r = run_generator(p, tmp_path)
    assert r.returncode != 0, "blocked plan 不应成功退出"
    assert not (tmp_path / "mutator.c").exists(), "blocked plan 不应生成 mutator.c"
    # 防止"脚本不存在"导致的空过：必须看到生成器自己的拒绝理由
    blob = (r.stdout + r.stderr).lower()
    assert ("blocked" in blob) or ("plan_status" in blob), \
        f"生成器不是因 plan 状态而拒绝（空过）：stdout={r.stdout[:200]!r} stderr={r.stderr[:200]!r}"


def test_missing_plan_cannot_generate_code(tmp_path):
    """plan 文件不存在时也必须拒绝。"""
    r = run_generator(tmp_path / "nope.json", tmp_path)
    assert r.returncode != 0
    assert not (tmp_path / "mutator.c").exists()
    blob = (r.stdout + r.stderr).lower()
    assert ("not found" in blob) or ("不存在" in blob) or ("plan" in blob), \
        f"拒绝理由不明确（空过）：stdout={r.stdout[:200]!r} stderr={r.stderr[:200]!r}"


# ─────────── Task 2：candidate_findings ───────────

sys.path.insert(0, PIPE)
import s5_mutator as CF  # noqa: E402  （合并后 normalize_findings 在 s5_mutator.py 里）


def _surface():
    return {"target": {"osv_id": "T", "commit": "abc1234"},
            "call_surface": {"direct_calls": ["api_read"], "reachable_functions": ["api_read", "parse"],
                             "reachable_files": ["src/a.c"]},
            "fields": [{"field_id": "record.group_code.0", "locator": {"kind": "record_sequence"}}],
            "validation": {"field_mapping_complete": True}}


def test_evidence_verification_rejects_bad_line(tmp_path):
    """证据行越界 / 原文不符 → status=rejected。"""
    f = tmp_path / "src" / "a.c"
    f.parent.mkdir(parents=True)
    f.write_text("int api_read(void) {\n  return 0;\n}\nint parse(void) {\n  return 1;\n}\n",
                 encoding="utf-8")
    audit = {"candidates": [
        {"vuln_type": "use-after-free", "function": "api_read", "lines": [1],
         "mechanism": "m", "evidence_lines": [[999, "nothing"]], "confidence": "high"},
        {"vuln_type": "use-after-free", "function": "parse", "lines": [4],
         "mechanism": "m", "evidence_lines": [[4, "int parse(void) {"]], "confidence": "high"},
    ]}
    got = CF.normalize_findings(audit, {"hypotheses": []}, None, None, _surface(), str(tmp_path))
    by_ev = sorted(x["evidence_ok"] for x in got["findings"])
    assert by_ev == [False, True], got["findings"]
    bad = [x for x in got["findings"] if not x["evidence_ok"]]
    assert bad and bad[0]["status"] == "rejected"


def test_dedup_merges_overlapping_evidence(tmp_path):
    """LLM 候选与机械假设：同 family/file/function 且证据行有交集 → 合并，sources 保留两个。"""
    f = tmp_path / "src" / "a.c"
    f.parent.mkdir(parents=True)
    f.write_text("x\nfree_pair(p);\ny\nwhile (p->code)\n", encoding="utf-8")
    audit = {"candidates": [
        {"vuln_type": "use-after-free", "function": "api_read", "lines": [2, 4],
         "mechanism": "llm", "evidence_lines": [[2, "free_pair(p);"], [4, "while (p->code)"]],
         "confidence": "high"},
    ]}
    mech = {"hypotheses": [
        {"vuln_type": "use-after-free", "function": "api_read", "file": "src/a.c",
         "free_line": 2, "use_line": 4, "mechanism": "mech",
         "evidence_lines": [[2, "free_pair(p);"], [4, "while (p->code)"]]},
    ]}
    got = CF.normalize_findings(audit, mech, None, None, _surface(), str(tmp_path))
    assert len(got["findings"]) == 1, got["findings"]
    assert len(got["findings"][0]["sources"]) == 2
