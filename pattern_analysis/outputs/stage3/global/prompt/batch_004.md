你是一名内存安全崩溃分析专家，专门研究模糊测试发现的崩溃的成因机制。
你的读者是后续要设计"变异策略"的工程师——他们需要知道：这类崩溃是怎么被触发的，以及哪个输入字段控制触发的关键环节。

你的任务：从一批同类型的崩溃样本中，提取它们共享的"机制形态"（pattern）。

严格遵守以下规则：
1. 只使用输入数据中存在的字段，绝对不要推测或编造。
2. 如果某个条件在样本中为 null（数据缺失），在该 pattern 的 evidence 中标注 "unknown:<字段名>"，不要当作 false。
3. 每个 pattern 必须给出 support（该 pattern 的样本数）和 sample_ids（具体样本 ID）。
4. 无法归入任何 pattern 的样本，必须原样列在 unclassified 中，不要强行归类。
5. 输出的 JSON 必须严格符合给定 schema，不要添加额外字段，不要用 markdown 包裹。
6. pattern 数量控制在 2-5 个。
7. 每个 pattern 的 name 用中文，不超过 12 个字。
8. narrative 用 2-4 句话说清"这个 pattern 的崩溃是怎么发生的"，必须引用具体样本的函数名、行号或字段值作为依据。
9. trigger_condition 必须回答"改哪个输入、让什么条件成立，就能触发"，如果数据不足以回答，写 "unknown" 并说明缺什么。
10. 当 support > 1 时：narrative 要描述这 N 条的共同机制（可用 2-3 条做例证）；evidence 要用跨样本统计的写法（如 "7/7 样本..."、"5/7 样本...（例外：xxx、yyy）"）；dimensions 取多数值并注明例外。

## 崩溃类型
global-buffer-overflow

## 该类型的机制背景
global-BOF 的必要条件链：
- N1 访问对象是全局数组/表
- N2 访问宽度
- N3 下标表达式及其来源
- N4 常量表 vs 可变全局缓冲区
- N5 下标是单字节还是多字节
- N6 表长是否是 2 的幂（256/512）
- N7 同一输入索引是否访问多个全局表

## 样本（共 6 条，完整 facts + interpretation）

[
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "vte_write_debug",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "",
   "site": {
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "fn": "vte_write_debug",
    "line": 514
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-1448.log",
   "testcase_size": 2
  },
  "input_reachability": [],
  "osv_id": "OSV-2020-1448",
  "project": "libtsm",
  "sites": [
   {
    "code": "",
    "fn": "vte_write_debug",
    "kind": "unknown",
    "line": 514,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "vte_write_debug",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "",
   "site": {
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "fn": "vte_write_debug",
    "line": 514
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libtsm_b73acb4c7169.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1373.log",
   "testcase_size": 7270
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-1373",
  "project": "libtsm",
  "sites": [
   {
    "code": "",
    "fn": "vte_write_debug",
    "kind": "unknown",
    "line": 514,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "vte_write_debug",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "",
   "site": {
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "fn": "vte_write_debug",
    "line": 514
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-289.log",
   "testcase_size": 2
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-289",
  "project": "libtsm",
  "sites": [
   {
    "code": "",
    "fn": "vte_write_debug",
    "kind": "unknown",
    "line": 514,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "DoEmbedded2",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 4
   },
   "code": "word = embedded_list[(*embix)++] | embedded_list[(*embix)++] | (*embix)++ | *embix",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/setlengths.c",
    "fn": "DoEmbedded2",
    "line": 427
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "word",
   "storage": "global"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-808.log",
   "testcase_size": 780
  },
  "input_reachability": [
   "embix"
  ],
  "osv_id": "OSV-2021-808",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "word = embedded_list[(*embix)++] | embedded_list[(*embix)++] | (*embix)++ | *embix",
    "fn": "DoEmbedded2",
    "kind": "unknown",
    "line": 427,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "FOR:62,IF:64,IF:70,IF:71,IF:75,FOR:79,IF:80,IF:83,CONTINUE:84,IF:86,CONTINUE:87,IF:89",
   "fn": "SubstitutePhonemes",
   "guard_count": 1,
   "guards": "next != 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 2
   },
   "code": "(plist2+1)->sourceix || ((next != 0) && (next->type == p | (plist2+1)->sourceix | plist2+1 | (next != 0) && (next->type == phPAUSE)",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/phonemelist.c",
    "fn": "SubstitutePhonemes",
    "line": 75
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/phonemelist.c",
    "line": 58,
    "size": null,
    "type": "PHONEME_LIST2*"
   },
   "kind": "pointer",
   "name": "plist2",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_7b9c99cec7b0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-810.log",
   "testcase_size": 972
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-810",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "(plist2+1)->sourceix || ((next != 0) && (next->type == p | (plist2+1)->sourceix | plist2+1 | (next != 0) && (next->type == phPAUSE)",
    "fn": "SubstitutePhonemes",
    "kind": "unknown",
    "line": 75,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "PHONEME_LIST2*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "isvce_write_coeff4x4_cavlc",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/libavc/encoder/svc/isvce_cavlc.c",
    "fn": "isvce_write_coeff4x4_cavlc",
    "line": null
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-48.log",
   "testcase_size": 16946
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-48",
  "project": "libavc",
  "sites": [],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 }
]

## 任务
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、dimensions、evidence、confidence。
3. 无法归类的样本放入 unclassified，并说明缺什么数据。

## 输出 JSON schema
{
  "crash_type": "string",
  "batch_id": "string",
  "sample_count": number,
  "patterns": [
    {
      "name": "string",
      "narrative": "string",
      "support": number,
      "sample_ids": ["string"],
      "trigger_condition": {
        "where_alloc": "string",
        "where_free": "string",
        "where_use": "string",
        "what_input_controls": "string",
        "minimal_requirement": "string"
      },
      "dimensions": {
        "alloc_kind": "heap | stack | global | unknown",
        "free_before_use": "true | false | unknown",
        "free_and_use_same_function": "true | false | unknown",
        "reassigned_between": "true | false | unknown",
        "in_loop": "true | false | unknown",
        "access_kind": "read | write | call | unknown",
        "cross_frame_count": "number | unknown"
      },
      "evidence": ["string"],
      "confidence": "high | medium | low"
    }
  ],
  "unclassified": [{"sample_id": "string", "reason": "string", "missing_fields": ["string"]}],
  "batch_observations": "string"
}

直接输出 JSON，不要任何解释文字。