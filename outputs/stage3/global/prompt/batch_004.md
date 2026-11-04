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
  "osv_id": "OSV-2020-1448",
  "project": "libtsm",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "global",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 514,
    "fn": "vte_write_debug",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vte_write_debug",
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "line": 514
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vte_write_debug",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-1448.log",
   "cpg": null,
   "testcase_size": 2
  },
  "type_reconciliation": {
   "report_fault_kind": "global-buffer-overflow",
   "ledger_crash_type": "global-buffer-overflow",
   "used": "global-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f9",
   "shadow_legend_size": 21,
   "loc_size": 24,
   "loc_global_var": ".str.131",
   "loc_offset": 48,
   "loc_kind": "global",
   "dedup_token": "vte_write_debug--do_trans--tsm_vte_input",
   "overshoot_ratio": 2.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vte_write_debug"
  }
 },
 {
  "osv_id": "OSV-2021-1373",
  "project": "libtsm",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "global",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 514,
    "fn": "vte_write_debug",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vte_write_debug",
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "line": 514
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vte_write_debug",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1373.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libtsm_b73acb4c7169.cpg",
   "testcase_size": 7270
  },
  "type_reconciliation": {
   "report_fault_kind": "global-buffer-overflow",
   "ledger_crash_type": "global-buffer-overflow",
   "used": "global-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f9",
   "shadow_legend_size": 21,
   "loc_size": 24,
   "loc_global_var": ".str.131",
   "loc_offset": 48,
   "loc_kind": "global",
   "dedup_token": "vte_write_debug--do_trans--tsm_vte_input",
   "overshoot_ratio": 2.0
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    504,
    533
   ],
   "func_params": {
    "names": [
     "vte",
     "u8",
     "len",
     "raw",
     "file",
     "line"
    ],
    "types": [
     "tsm_vte*",
     "char*",
     "size_t",
     "bool",
     "char*",
     "int"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "OSV-2021-1373",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vte_write_debug"
  }
 },
 {
  "osv_id": "OSV-2021-289",
  "project": "libtsm",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "global",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 514,
    "fn": "vte_write_debug",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vte_write_debug",
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "line": 514
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vte_write_debug",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-289.log",
   "cpg": null,
   "testcase_size": 2
  },
  "type_reconciliation": {
   "report_fault_kind": "global-buffer-overflow",
   "ledger_crash_type": "global-buffer-overflow",
   "used": "global-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f9",
   "shadow_legend_size": 21,
   "loc_size": 24,
   "loc_global_var": ".str.131",
   "loc_offset": 48,
   "loc_kind": "global",
   "dedup_token": "vte_write_debug--do_trans--parse_data",
   "overshoot_ratio": 2.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vte_write_debug"
  }
 },
 {
  "osv_id": "OSV-2021-808",
  "project": "espeak-ng",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "word",
   "kind": null,
   "storage": "global",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 427,
    "fn": "DoEmbedded2",
    "code": "word = embedded_list[(*embix)++] | embedded_list[(*embix)++] | (*embix)++ | *embix",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "DoEmbedded2",
    "file": "/src/espeak-ng/src/libespeak-ng/setlengths.c",
    "line": 427
   },
   "code": "word = embedded_list[(*embix)++] | embedded_list[(*embix)++] | (*embix)++ | *embix",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "DoEmbedded2",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "embix"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-808.log",
   "cpg": null,
   "testcase_size": 780
  },
  "type_reconciliation": {
   "report_fault_kind": "global-buffer-overflow",
   "ledger_crash_type": "global-buffer-overflow",
   "used": "global-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f9",
   "shadow_legend_size": 21,
   "loc_size": 1000,
   "loc_global_var": "embedded_list",
   "loc_offset": 0,
   "loc_kind": "global",
   "dedup_token": "DoEmbedded2--CalcLengths--SpeakNextClause",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "DoEmbedded2"
  }
 },
 {
  "osv_id": "OSV-2021-810",
  "project": "espeak-ng",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "plist2",
   "kind": "pointer",
   "storage": "global",
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/phonemelist.c",
    "line": 58,
    "size": null,
    "type": "PHONEME_LIST2*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 75,
    "fn": "SubstitutePhonemes",
    "code": "(plist2+1)->sourceix || ((next != 0) && (next->type == p | (plist2+1)->sourceix | plist2+1 | (next != 0) && (next->type == phPAUSE)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "SubstitutePhonemes",
    "file": "/src/espeak-ng/src/libespeak-ng/phonemelist.c",
    "line": 75
   },
   "code": "(plist2+1)->sourceix || ((next != 0) && (next->type == p | (plist2+1)->sourceix | plist2+1 | (next != 0) && (next->type == phPAUSE)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "SubstitutePhonemes",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "next != 0",
   "guard_count": 1,
   "control_structures": "FOR:62,IF:64,IF:70,IF:71,IF:75,FOR:79,IF:80,IF:83,CONTINUE:84,IF:86,CONTINUE:87,IF:89"
  },
  "call_chain": [],
  "types": {
   "entity_type": "PHONEME_LIST2*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-810.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_7b9c99cec7b0.cpg",
   "testcase_size": 972
  },
  "type_reconciliation": {
   "report_fault_kind": "global-buffer-overflow",
   "ledger_crash_type": "global-buffer-overflow",
   "used": "global-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f9",
   "shadow_legend_size": 21,
   "loc_size": 8000,
   "loc_global_var": "ph_list2",
   "loc_offset": 4,
   "loc_kind": "global",
   "dedup_token": "SubstitutePhonemes--MakePhonemeList--TranslateClause",
   "overshoot_ratio": 0.0005
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "plist2 = &ph_list2[ix]",
     "line": 63
    },
    {
     "code": "plist2->sourceix = deleted_sourceix",
     "line": 65
    },
    {
     "code": "plist2->phcode = replace_phonemes[k].new_ph",
     "line": 93
    },
    {
     "code": "plist2->stresslevel = 0",
     "line": 95
    }
   ],
   "entity_decl": {
    "line": 58,
    "type": "PHONEME_LIST2*"
   },
   "entity_name_cpg": "plist2",
   "func_lines": [
    49,
    113
   ],
   "func_params": {
    "names": [
     "plist_out"
    ],
    "types": [
     "PHONEME_LIST*"
    ]
   },
   "guards": [
    {
     "code": "ix < n_ph_list2",
     "line": 62
    },
    {
     "code": "n_plist_out < N_PHONEME_LIST",
     "line": 62
    },
    {
     "code": "deleted_sourceix != -1",
     "line": 64
    },
    {
     "code": "ix < (n_ph_list2 -1)",
     "line": 71
    },
    {
     "code": "next != 0",
     "line": 75
    },
    {
     "code": "next->type == phPAUSE",
     "line": 75
    },
    {
     "code": "k < n_replace_phonemes",
     "line": 79
    },
    {
     "code": "plist2->phcode == replace_phonemes[k].old_ph",
     "line": 80
    },
    {
     "code": "word_end == false",
     "line": 83
    },
    {
     "code": "(plist2->stresslevel & 0x7) > 3",
     "line": 86
    },
    {
     "code": "plist2->sourceix == 0",
     "line": 89
    },
    {
     "code": "plist2->stresslevel > 1",
     "line": 94
    },
    {
     "code": "plist2->phcode == 0",
     "line": 100
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "(plist2+1)->sourceix ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "(plist2+1)->sourceix",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "plist2+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(next != 0) && (next->type == phPAUSE)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "next != 0",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "next->type == phPAUSE",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "next->type",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "phPAUSE",
     "name": "phPAUSE",
     "nargs": 0
    }
   ],
   "line_ids": [
    "plist2",
    "next"
   ],
   "osv_id": "OSV-2021-810",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "SubstitutePhonemes"
  }
 },
 {
  "osv_id": "OSV-2023-48",
  "project": "libavc",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "global",
   "decl": null
  },
  "alloc": null,
  "sites": [],
  "crash": {
   "site": {
    "fn": "isvce_write_coeff4x4_cavlc",
    "file": "/src/libavc/encoder/svc/isvce_cavlc.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "isvce_write_coeff4x4_cavlc",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-48.log",
   "cpg": null,
   "testcase_size": 16946
  },
  "type_reconciliation": {
   "report_fault_kind": "global-buffer-overflow",
   "ledger_crash_type": "global-buffer-overflow",
   "used": "global-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_size": 15,
   "loc_global_var": "gu1_index_zero_table",
   "loc_offset": 54,
   "loc_kind": "global",
   "dedup_token": "isvce_write_coeff4x4_cavlc--isvce_encode_residue--isvce_write_pslice_mb_cavlc",
   "overshoot_ratio": 3.6
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "isvce_write_coeff4x4_cavlc"
  }
 }
]

## 任务
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、dimensions、evidence、confidence。
   **样本里的 `measured_dims` 是 stage2 实测出来的值，不是让你猜的**：
   `reassigned_between` / `cross_frame_count` 直接照抄（`null` 才写 unknown），
   `cross_frame_exact=false` 表示跳数算不出精确值，此时 `cross_frame_count` 写 unknown。
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