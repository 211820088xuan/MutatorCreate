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
stack-buffer-overflow

## 该类型的机制背景
stack-BOF 的必要条件链：
- N1 对象是函数内栈数组
- N2 数组声明维度
- N3 访问宽度
- N4 是否 VLA（char buf[n]，n 来自输入）
- N5 数组所在栈帧
- N6 写入形式：memcpy 还是逐字节循环
- N7 栈增长方向 + 覆盖对象
- N8 是否经由 alloca / 变长分配

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "fn": "getNumberValue",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 1
   },
   "code": "digits[i]='\\0' | digits[i]",
   "site": {
    "file": "/src/icu/icu4c/source/i18n/plurrule.cpp",
    "fn": "getNumberValue",
    "line": 1265
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/icu/icu4c/source/i18n/plurrule.cpp",
    "line": 1262,
    "size": null,
    "type": "char[128]"
   },
   "kind": "array",
   "name": "digits",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_539e8f41a35f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/icu/address/539e8f41a35fec30fba4cfb3a65ea4db67978f85/ARVO-42532047/report.log",
   "testcase_size": 282
  },
  "input_reachability": [
   "token"
  ],
  "osv_id": "ARVO-42532047",
  "project": "icu",
  "sites": [
   {
    "code": "digits[i]='\\0' | digits[i]",
    "fn": "getNumberValue",
    "kind": "unknown",
    "line": 1265,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char[128]",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "WHILE:183,IF:185,IF:186,IF:190,IF:191,ELSE:196,IF:199,ELSE:201,IF:201,FOR:207,FOR:217,IF:229",
   "fn": "shoco_decompress",
   "guard_count": 2,
   "guards": "in < in_end | mark < 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "mark = decode_header(*in) | decode_header(*in) | *in",
   "site": {
    "file": "/src/ndpi/src/lib/third_party/src/shoco.c",
    "fn": "shoco_decompress",
    "line": 184
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/third_party/src/shoco.c",
    "line": 180,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "mark",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_246e972f9c1b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/246e972f9c1bf2780c348ae43030119ad417c153/ARVO-42534646/report.log",
   "testcase_size": 2086
  },
  "input_reachability": [
   "original",
   "complen"
  ],
  "osv_id": "ARVO-42534646",
  "project": "ndpi",
  "sites": [
   {
    "code": "mark = decode_header(*in) | decode_header(*in) | *in",
    "fn": "shoco_decompress",
    "kind": "unknown",
    "line": 184,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:113,IF:115,ELSE:121,IF:122,FOR:126,IF:133,IF:136,IF:143,IF:147",
   "fn": "UnrollChunkyBytes",
   "guard_count": 1,
   "guards": "v > 0xffff",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "v = FROM_8_TO_16(*accum) | FROM_8_TO_16(*accum) | *accum | (cmsUInt16Number)((((cmsUInt16Number)(*accum)) << 8) | (",
   "site": {
    "file": "/src/lcms/src/cmspack.c",
    "fn": "UnrollChunkyBytes",
    "line": 130
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lcms/src/cmspack.c",
    "line": 109,
    "size": null,
    "type": "cmsUInt32Number"
   },
   "kind": "struct",
   "name": "v",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_d2c7f4360e9a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/lcms/address/d2c7f4360e9a6fdf3a9949bc9a12ab5eeb02b538/ARVO-42537072/report.log",
   "testcase_size": 386
  },
  "input_reachability": [
   "info",
   "accum"
  ],
  "osv_id": "ARVO-42537072",
  "project": "lcms",
  "sites": [
   {
    "code": "v = FROM_8_TO_16(*accum) | FROM_8_TO_16(*accum) | *accum | (cmsUInt16Number)((((cmsUInt16Number)(*accum)) << 8) | (",
    "fn": "UnrollChunkyBytes",
    "kind": "unknown",
    "line": 130,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "cmsUInt32Number",
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
   "fn": "vvc_push_ref_poc",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/gpac/src/media_tools/av_parsers.c",
    "fn": "vvc_push_ref_poc",
    "line": 12536
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/gpac_a012d226ec8d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/gpac/address/a012d226ec8de965159f8477e8929bb5d2f57c31/ARVO-42537243/report.log",
   "testcase_size": 121
  },
  "input_reachability": [],
  "osv_id": "ARVO-42537243",
  "project": "gpac",
  "sites": [
   {
    "code": null,
    "fn": "vvc_push_ref_poc",
    "kind": "unknown",
    "line": 12536,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "gf_hevc_compute_ref_list",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/gpac/src/media_tools/av_parsers.c",
    "fn": "gf_hevc_compute_ref_list",
    "line": 7541
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/gpac_df8121066cf8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/gpac/address/df8121066cf8fb25cc70adf7ca8b35bda82fe216/ARVO-42537907/report.log",
   "testcase_size": 1445
  },
  "input_reachability": [],
  "osv_id": "ARVO-42537907",
  "project": "gpac",
  "sites": [
   {
    "code": null,
    "fn": "gf_hevc_compute_ref_list",
    "kind": "unknown",
    "line": 7541,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "control_structures": "IF:92,IF:97,ELSE:103,IF:129,IF:135,ELSE:143,ELSE:151",
   "fn": "otLwfRegisterDevice",
   "guard_count": 1,
   "guards": "FilterDeviceExtension == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 16
   },
   "code": "FilterDeviceExtension->Signature = 'FTDR' | FilterDeviceExtension->Signature",
   "site": {
    "file": "/src/openthread/src/core/thread/key_manager.cpp",
    "fn": "ot::KeyManager::SetMasterKey(otMasterKey const&)",
    "line": 107
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "FilterDeviceExtension",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_bf52ed706fac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/bf52ed706facbbbd12b2d86c902c0f71b2b72bb0/ARVO-42539272/report.log",
   "testcase_size": 324
  },
  "input_reachability": [],
  "osv_id": "ARVO-42539272",
  "project": "openthread",
  "sites": [
   {
    "code": "FilterDeviceExtension->Signature = 'FTDR' | FilterDeviceExtension->Signature",
    "fn": "ot::KeyManager::SetMasterKey(otMasterKey const&)",
    "kind": "unknown",
    "line": 107,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "control_structures": "FOR:1776,IF:1781,IF:1785,ELSE:1787,IF:1787,IF:1789,IF:1792,IF:1798,IF:1803,IF:1808,IF:1813,WHILE:1817",
   "fn": "TranslateNumber_1",
   "guard_count": 5,
   "guards": "n_digits == group_len | n_digits == 3 | n_digits == 2",
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
   "code": "(n_digits == group_len) && (word[-2] == tr->langopts.tho | (n_digits == group_len) && (word[-2] == tr->langopts.tho | n_digits == group_len | word[-2] == tr->langopts.thousands_sep",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "fn": "TranslateNumber_1",
    "line": 1785
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "line": 1738,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "n_digits",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_cd33c4042a02.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1631.log",
   "testcase_size": 96
  },
  "input_reachability": [
   "tr",
   "word"
  ],
  "osv_id": "OSV-2021-1631",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "(n_digits == group_len) && (word[-2] == tr->langopts.tho | (n_digits == group_len) && (word[-2] == tr->langopts.tho | n_digits == group_len | word[-2] == tr->langopts.thousands_sep",
    "fn": "TranslateNumber_1",
    "kind": "unknown",
    "line": 1785,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
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
   "call_chain"
  ],
  "context": {
   "fn": "IsLetterGroup",
   "guard_count": 1,
   "guards": "p == NULL",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "(*p == *w) && (*w != 0) | *p == *w | *p | *w",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "fn": "IsLetterGroup",
    "line": 714
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "p",
   "storage": "stack"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1636.log",
   "testcase_size": 6625
  },
  "input_reachability": [
   "word"
  ],
  "osv_id": "OSV-2021-1636",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "(*p == *w) && (*w != 0) | *p == *w | *p | *w",
    "fn": "IsLetterGroup",
    "kind": "unknown",
    "line": 714,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "control_structures": "FOR:1776,IF:1781,IF:1785,ELSE:1787,IF:1787,IF:1789,IF:1792,IF:1798,IF:1803,IF:1808,IF:1813,WHILE:1817",
   "fn": "TranslateNumber_1",
   "guard_count": 5,
   "guards": "n_digits == group_len | n_digits == 3 | n_digits == 2",
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
   "code": "(n_digits == group_len) && (word[-2] == tr->langopts.tho | (n_digits == group_len) && (word[-2] == tr->langopts.tho | n_digits == group_len | word[-2] == tr->langopts.thousands_sep",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "fn": "TranslateNumber_1",
    "line": 1785
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "line": 1738,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "n_digits",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_cd33c4042a02.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-764.log",
   "testcase_size": 34
  },
  "input_reachability": [
   "tr",
   "word"
  ],
  "osv_id": "OSV-2021-764",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "(n_digits == group_len) && (word[-2] == tr->langopts.tho | (n_digits == group_len) && (word[-2] == tr->langopts.tho | n_digits == group_len | word[-2] == tr->langopts.thousands_sep",
    "fn": "TranslateNumber_1",
    "kind": "unknown",
    "line": 1785,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1964,IF:1972,FOR:1976,IF:1980,IF:1981,ELSE:1984,IF:1992,FOR:1995,IF:1996,BREAK:1997,IF:1999,IF:2003",
   "fn": "TranslateClause",
   "guard_count": 3,
   "guards": "pn < &number_buf[sizeof(number_buf)-20] | pn < &number_buf[sizeof(number_buf)-20] | pw < pn",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 16
   },
   "code": "memcpy(pn, pw, 16)",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/translate.c",
    "fn": "TranslateClause",
    "line": 2584
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/translate.c",
    "line": 2494,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "pn",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_7b9c99cec7b0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-769.log",
   "testcase_size": 754
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-769",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "memcpy(pn, pw, 16)",
    "fn": "TranslateClause",
    "kind": "unknown",
    "line": 2584,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
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
   "call_chain"
  ],
  "context": {
   "fn": "suffix_check",
   "guard_count": 1,
   "guards": "len == 0",
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
   "code": "sp = word[start + len - 1] | word[start + len - 1] | start + len - 1 | start + len",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::suffix_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, int, int, PfxEntry*, unsigned short, unsigned short, char)",
    "line": 2797
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "sp",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_fd76b3322308.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1049.log",
   "testcase_size": 1824
  },
  "input_reachability": [
   "word",
   "start",
   "len"
  ],
  "osv_id": "OSV-2022-1049",
  "project": "hunspell",
  "sites": [
   {
    "code": "sp = word[start + len - 1] | word[start + len - 1] | start + len - 1 | start + len",
    "fn": "AffixMgr::suffix_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, int, int, PfxEntry*, unsigned short, unsigned short, char)",
    "kind": "unknown",
    "line": 2797,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "fn": "suffix_check",
   "guard_count": 1,
   "guards": "len == 0",
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
   "code": "sp = word[start + len - 1] | word[start + len - 1] | start + len - 1 | start + len",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::suffix_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, int, int, PfxEntry*, unsigned short, unsigned short, char)",
    "line": 2797
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "sp",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_fd76b3322308.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1058.log",
   "testcase_size": 1925
  },
  "input_reachability": [
   "word",
   "start",
   "len"
  ],
  "osv_id": "OSV-2022-1058",
  "project": "hunspell",
  "sites": [
   {
    "code": "sp = word[start + len - 1] | word[start + len - 1] | start + len - 1 | start + len",
    "fn": "AffixMgr::suffix_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, int, int, PfxEntry*, unsigned short, unsigned short, char)",
    "kind": "unknown",
    "line": 2797,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "fn": "Lookup",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 197
   },
   "code": "",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "fn": "Lookup",
    "line": 2886
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_2f705ee5bb5b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-595.log",
   "testcase_size": 92
  },
  "input_reachability": [],
  "osv_id": "OSV-2022-595",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "",
    "fn": "Lookup",
    "kind": "unknown",
    "line": 2886,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "fn": "test_condition",
   "guard_count": 6,
   "guards": "st < s.size() | st < s.size() | st == s.size()",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "s[st] == *p | s[st] | *p",
   "site": {
    "file": "/src/hunspell/src/hunspell/affentry.cxx",
    "fn": "PfxEntry::test_condition(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&)",
    "line": 177
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "s",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_3809b8e9389b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-872.log",
   "testcase_size": 124
  },
  "input_reachability": [
   "s"
  ],
  "osv_id": "OSV-2022-872",
  "project": "hunspell",
  "sites": [
   {
    "code": "s[st] == *p | s[st] | *p",
    "fn": "PfxEntry::test_condition(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&)",
    "kind": "unknown",
    "line": 177,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "decNumberCopy",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 2
   },
   "code": "s=src->lsu+1 | src->lsu+1 | src->lsu | s<smsup",
   "site": {
    "file": "/src/jq/src/decNumber/decNumber.c",
    "fn": "decNumberCopy",
    "line": 3375
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/jq_c5fd64ba975e.cpg",
   "report": "artifacts/by_crash_type/stack-buffer-overflow/jq/address/c5fd64ba975ee35df17bb0c335efb00bffce4d91/OSV-2023-1268",
   "testcase_size": 19
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-1268",
  "project": "jq",
  "sites": [
   {
    "code": "s=src->lsu+1 | src->lsu+1 | src->lsu | s<smsup",
    "fn": "decNumberCopy",
    "kind": "unknown",
    "line": 3375,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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