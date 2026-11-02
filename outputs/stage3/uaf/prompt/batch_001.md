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
heap-use-after-free

## 该类型的机制背景
UAF 的必要条件链：
- N1 对象是堆分配
- N2 存在 free(p) 调用
- N3 p 在 free 之后被解引用（执行顺序）
- N4 free 与解引用之间 p 未被重新赋值
- N5 free 与解引用之间 p 未重新 malloc
- N6 free 的实参是 p 本身（非 p+off）
- N7 解引用对象与 free 对象是同一对象（含别名）
- N8 free 与解引用在同一可达路径上
- N9 p 解引用时未被置空
- N10 解引用发生在 free 生效后（非同一语句）

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/fuzz/fuzz.c",
    "fn": "xmlFuzzMalloc",
    "line": 81
   },
   "size_bytes": 64,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:5957,IF:5964,IF:5966,WHILE:5972,IF:5974,WHILE:5980,WHILE:5982,IF:5983,IF:5989,IF:5991,IF:6006,IF:6008",
   "fn": "xmlSearchNsSafe",
   "guard_count": 6,
   "guards": "prefix != NULL | cur == NULL | cur != NULL",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 64,
    "width": 4
   },
   "code": "xmlStrEqual(cur->prefix, prefix) | cur->prefix",
   "site": {
    "file": "/src/libxml2/valid.c",
    "fn": "xmlValidateOneElement",
    "line": 5992
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/valid.c",
    "line": 5952,
    "size": null,
    "type": "xmlNsPtr"
   },
   "kind": "struct",
   "name": "cur",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_d4d1f3f33d6d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/d4d1f3f33d6d4a5e31511281637a857944946e65/ARVO-372547409/report.log",
   "testcase_size": 26
  },
  "input_reachability": [
   "node",
   "prefix",
   "out"
  ],
  "osv_id": "ARVO-372547409",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlFreeAttribute",
    "kind": "free",
    "line": 1625,
    "origin": "report:freed_by"
   },
   {
    "code": "xmlStrEqual(cur->prefix, prefix) | cur->prefix",
    "fn": "xmlValidateOneElement",
    "kind": "unknown",
    "line": 5992,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "xmlNsPtr",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/net-snmp/testing/fuzzing/ada_fuzz_header.h",
    "fn": "af_get_null_terminated",
    "line": 67
   },
   "size_bytes": 76,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "netsnmp_hex_to_binary",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 76,
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/net-snmp/snmplib/tools.c",
    "fn": "netsnmp_hex_to_binary",
    "line": 581
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-396777457/report.log",
   "testcase_size": 328
  },
  "input_reachability": [],
  "osv_id": "ARVO-396777457",
  "project": "net-snmp",
  "sites": [
   {
    "code": null,
    "fn": "af_gb_cleanup",
    "kind": "free",
    "line": 56,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "netsnmp_hex_to_binary",
    "kind": "unknown",
    "line": 581,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/src/openvswitch/lib/util.c",
    "fn": "xrealloc",
    "line": 134
   },
   "size_bytes": 64,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "parse_odp_action",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 64,
    "width": 2
   },
   "code": null,
   "site": {
    "file": "/src/openvswitch/lib/odp-util.c",
    "fn": "parse_odp_action",
    "line": 2246
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_bc9bbc4ea264.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openvswitch/address/bc9bbc4ea2645e5bbb3c02d986f26fdc83283d72/ARVO-42470878/report.log",
   "testcase_size": 12
  },
  "input_reachability": [],
  "osv_id": "ARVO-42470878",
  "project": "openvswitch",
  "sites": [
   {
    "code": null,
    "fn": "xrealloc",
    "kind": "free",
    "line": 134,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "parse_odp_action",
    "kind": "unknown",
    "line": 2246,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/radare2/libr/core/task.c",
    "fn": "r_core_task_new",
    "line": 192
   },
   "size_bytes": 104,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "r_core_task_decref",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 104,
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/radare2/libr/core/task.c",
    "fn": "r_core_task_decref",
    "line": 250
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_8f03b2a42fcc.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/radare2/address/8f03b2a42fccf6fb7c3d78ca1adeea0bf9d78757/ARVO-42471500/report.log",
   "testcase_size": 0
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471500",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "r_core_task_decref",
    "kind": "free",
    "line": 248,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "r_core_task_decref",
    "kind": "unknown",
    "line": 250,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "line": 72
   },
   "size_bytes": 499,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:170,FOR:174,IF:175,IF:180",
   "fn": "Init",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 499,
    "width": 8
   },
   "code": "WELS_THREAD_ERROR_GENERAL | (uint32_t)(-1) | -1",
   "site": {
    "file": "/src/openh264/codec/decoder/core/src/decoder.cpp",
    "fn": "WelsDec::ResetRefPicReferences(WelsDec::TagWelsDecoderContext* const&, WelsDec::SPicture* const&)",
    "line": 176
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "uint32_t",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_be82ccf42fc0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/be82ccf42fc044ae1ea0792837a9415eaf535002/ARVO-42473818/report.log",
   "testcase_size": 70
  },
  "input_reachability": [],
  "osv_id": "ARVO-42473818",
  "project": "openh264",
  "sites": [
   {
    "code": "WELS_THREAD_ERROR_GENERAL | (uint32_t)(-1) | -1",
    "fn": "WelsDec::ResetRefPicReferences(WelsDec::TagWelsDecoderContext* const&, WelsDec::SPicture* const&)",
    "kind": "unknown",
    "line": 176,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "WelsDec::DecreasePicBuff(WelsDec::TagWelsDecoderContext*, WelsDec::TagPicBuff**, int, int, int, int)",
    "kind": "free",
    "line": 234,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/radare2/shlr/sdb/src/sdb.c",
    "fn": "sdb_new",
    "line": 56
   },
   "size_bytes": 11568,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "sdb_free",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 11568,
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/radare2/shlr/sdb/src/sdb.c",
    "fn": "sdb_free",
    "line": 217
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_0c9ccb45de8a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/radare2/address/0c9ccb45de8a22700fe51bcda0d4baa99f09cfe9/ARVO-42474100/report.log",
   "testcase_size": 4
  },
  "input_reachability": [],
  "osv_id": "ARVO-42474100",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "sdb_free",
    "kind": "unknown",
    "line": 217,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "sdb_free",
    "kind": "free",
    "line": 223,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "line": 72
   },
   "size_bytes": 499,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1128,GOTO:1130,IF:1133,GOTO:1134,ELSE:1135,IF:1136,IF:1137,IF:1139,GOTO:1140,ELSE:1141,IF:1141,ELSE:1143",
   "fn": "main",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 499,
    "width": 4
   },
   "code": "* pSVCEncoder = NULL",
   "site": {
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "fn": "WelsDec::MapColToList0(WelsDec::TagWelsDecoderContext*&, signed char const&, int const&)",
    "line": 1113
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "line": 1113,
    "size": null,
    "type": "ISVCEncoder*"
   },
   "kind": "pointer",
   "name": "pSVCEncoder",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_72974a4fcc65.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/72974a4fcc65c595bacb3d2c12d418d680cb063d/ARVO-42474468/report.log",
   "testcase_size": 80
  },
  "input_reachability": [],
  "osv_id": "ARVO-42474468",
  "project": "openh264",
  "sites": [
   {
    "code": null,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "kind": "free",
    "line": 113,
    "origin": "report:freed_by"
   },
   {
    "code": "* pSVCEncoder = NULL",
    "fn": "WelsDec::MapColToList0(WelsDec::TagWelsDecoderContext*&, signed char const&, int const&)",
    "kind": "unknown",
    "line": 1113,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "ISVCEncoder*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "calloc",
   "cross_function": true,
   "site": {
    "file": "/src/open62541/tests/fuzz/custom_memory_manager.c",
    "fn": "UA_memoryManager_calloc",
    "line": 142
   },
   "size_bytes": 144,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "fn": "String_clear",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 144,
    "width": 8
   },
   "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
   "site": {
    "file": "/src/open62541/src/ua_types.c",
    "fn": "String_clear",
    "line": 136
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 135,
    "size": null,
    "type": "UA_String*"
   },
   "kind": "pointer",
   "name": "s",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_4e38d391dde9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/4e38d391dde9e5d74463f0a17de245f8917675ca/ARVO-42474969/report.log",
   "testcase_size": 4
  },
  "input_reachability": [
   "s"
  ],
  "osv_id": "ARVO-42474969",
  "project": "open62541",
  "sites": [
   {
    "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
    "fn": "String_clear",
    "kind": "unknown",
    "line": 136,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "deleteMembers_default",
    "kind": "free",
    "line": 196,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "UA_String*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/radare2/libr/util/unum.c",
    "fn": "r_num_tail",
    "line": 731
   },
   "size_bytes": 14,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "cin_get",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 14,
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/radare2/libr/util/calc.c",
    "fn": "cin_get",
    "line": 216
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_ade7df45e8bd.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/radare2/address/ade7df45e8bd1c64e5d646d5aaf8943302205947/ARVO-42475763/report.log",
   "testcase_size": 3995
  },
  "input_reachability": [],
  "osv_id": "ARVO-42475763",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "cin_get",
    "kind": "unknown",
    "line": 216,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "r_num_tail",
    "kind": "free",
    "line": 742,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libspng/build/../spng.c",
    "fn": "spng_set_png_stream",
    "line": 2382
   },
   "size_bytes": 8192,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "read_chunks_before_idat",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 8192,
    "width": 2
   },
   "code": null,
   "site": {
    "file": "/src/libspng/spng.c",
    "fn": "read_chunks_before_idat",
    "line": 1321
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_9fcecef4100b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libspng/address/9fcecef4100bfa40b3b2b106790a97af70096ae0/ARVO-42476708/report.log",
   "testcase_size": 8472
  },
  "input_reachability": [],
  "osv_id": "ARVO-42476708",
  "project": "libspng",
  "sites": [
   {
    "code": null,
    "fn": "read_data",
    "kind": "free",
    "line": 292,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "read_chunks_before_idat",
    "kind": "unknown",
    "line": 1321,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libspng/build/../spng.c",
    "fn": "spng_set_png_stream",
    "line": 2382
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "read_chunks_after_idat",
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
    "width": 8289
   },
   "code": null,
   "site": {
    "file": "/src/libspng/spng.c",
    "fn": "read_chunks_after_idat",
    "line": 1560
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_9fcecef4100b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libspng/address/9fcecef4100bfa40b3b2b106790a97af70096ae0/ARVO-42476741/report.log",
   "testcase_size": 8471
  },
  "input_reachability": [],
  "osv_id": "ARVO-42476741",
  "project": "libspng",
  "sites": [
   {
    "code": null,
    "fn": "read_data",
    "kind": "free",
    "line": 292,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "read_chunks_after_idat",
    "kind": "unknown",
    "line": 1560,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libspng/build/../spng.c",
    "fn": "spng_set_png_stream",
    "line": 2382
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "read_chunks_before_idat",
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
    "width": 8224
   },
   "code": null,
   "site": {
    "file": "/src/libspng/spng.c",
    "fn": "read_chunks_before_idat",
    "line": 1454
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_9fcecef4100b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libspng/address/9fcecef4100bfa40b3b2b106790a97af70096ae0/ARVO-42476946/report.log",
   "testcase_size": 24604
  },
  "input_reachability": [],
  "osv_id": "ARVO-42476946",
  "project": "libspng",
  "sites": [
   {
    "code": null,
    "fn": "read_data",
    "kind": "free",
    "line": 292,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "read_chunks_before_idat",
    "kind": "unknown",
    "line": 1454,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/tests/fuzzing/fuzz_pkcs15_decode.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 56
   },
   "size_bytes": 2776,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1880,SWITCH:1882,BREAK:1885,BREAK:1888,BREAK:1891,BREAK:1894,BREAK:1897",
   "fn": "sc_pkcs15_free_object",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 2776,
    "width": 4
   },
   "code": "obj->type & SC_PKCS15_TYPE_CLASS_MASK | obj->type | SC_PKCS15_TYPE_CLASS_MASK",
   "site": {
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "fn": "sc_pkcs15_free_object",
    "line": 1882
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "line": 1878,
    "size": null,
    "type": "sc_pkcs15_object*"
   },
   "kind": "pointer",
   "name": "obj",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3b632e64a192.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/opensc/address/3b632e64a19235636ab0a93fc2a4b5a7caf078a3/ARVO-42477951/report.log",
   "testcase_size": 36
  },
  "free_related": {
   "free_sites_in_func": [
    58,
    1899,
    1904
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "input_reachability": [
   "obj"
  ],
  "osv_id": "ARVO-42477951",
  "project": "opensc",
  "sites": [
   {
    "code": null,
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "free",
    "line": 58,
    "origin": "report:freed_by"
   },
   {
    "code": "obj->type & SC_PKCS15_TYPE_CLASS_MASK | obj->type | SC_PKCS15_TYPE_CLASS_MASK",
    "fn": "sc_pkcs15_free_object",
    "kind": "unknown",
    "line": 1882,
    "origin": "report:crash"
   },
   {
    "code": "free(obj->data)",
    "fn": "sc_pkcs15_free_object",
    "kind": "free",
    "line": 1899,
    "origin": "cpg"
   },
   {
    "code": "free(obj)",
    "fn": "sc_pkcs15_free_object",
    "kind": "free",
    "line": 1904,
    "origin": "cpg"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "sc_pkcs15_object*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "g_malloc (/out/fuzzshark_ip_proto-udp+0x276a7e8)",
    "line": null
   },
   "size_bytes": 40,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "wmem_strbuf_get_str",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 40,
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/wireshark/epan/wmem/wmem_strbuf.c",
    "fn": "wmem_strbuf_get_str",
    "line": 258
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_828ff6ddb0a8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/wireshark/address/828ff6ddb0a824de7f48af8b2018c3d4506a48ce/ARVO-42478101/report.log",
   "testcase_size": 39
  },
  "input_reachability": [],
  "osv_id": "ARVO-42478101",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "wmem_simple_free",
    "kind": "free",
    "line": 54,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "wmem_strbuf_get_str",
    "kind": "unknown",
    "line": 258,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "line": 72
   },
   "size_bytes": 515,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:78,IF:82,IF:91,WHILE:95",
   "fn": "Start",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 515,
    "width": 1
   },
   "code": "(LPWELS_THREAD_ROUTINE)TheThread",
   "site": {
    "file": "/src/openh264/codec/decoder/core/src/manage_dec_ref.cpp",
    "fn": "WelsDec::SetUnRef(WelsDec::SPicture*)",
    "line": 89
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/manage_dec_ref.cpp",
    "line": 76,
    "size": null,
    "type": "WelsCommon.CWelsThread"
   },
   "kind": "struct",
   "name": "this",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_c185ac351eff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/c185ac351eff0ae277bfe14a3b2ad52e9ed8ab81/ARVO-42479359/report.log",
   "testcase_size": 62
  },
  "input_reachability": [
   "this"
  ],
  "osv_id": "ARVO-42479359",
  "project": "openh264",
  "sites": [
   {
    "code": "(LPWELS_THREAD_ROUTINE)TheThread",
    "fn": "WelsDec::SetUnRef(WelsDec::SPicture*)",
    "kind": "unknown",
    "line": 89,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "kind": "free",
    "line": 113,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "WelsCommon.CWelsThread",
   "is_signed": null,
   "ptr_origin": "param"
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