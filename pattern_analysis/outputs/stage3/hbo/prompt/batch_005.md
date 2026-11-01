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
heap-buffer-overflow

## 该类型的机制背景
HBO 的必要条件链：
- N1 访问对象是堆分配
- N2 一次访问的字节宽度
- N3 缓冲区大小 S
- N4 是否存在边界检查
- N5 访问基址是 B 还是 B+off
- N6 下标/长度表达式及其来源
- N7 元素类型（int* vs char*）
- N8 下标运算是否有整数溢出（i*4）
- N9 下标有无符号
- N10 分配大小是否输入控制
- N11 是否循环内多次访问累积越界

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "context": {
   "control_structures": "FOR:52",
   "fn": "<lambda>0",
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
    "width": 8
   },
   "code": "result.name[sizeof(result.name) - 1] = '\\0' | result.name[sizeof(result.name) - 1] | result.name | sizeof(result.name) - 1",
   "site": {
    "file": "/src/perfetto/src/trace_processor/fuchsia_trace_utils.cc",
    "fn": "perfetto::trace_processor::fuchsia_trace_utils::ReadTimestamp(unsigned long const**, unsigned long)",
    "line": 58
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/perfetto/src/trace_processor/fuchsia_trace_utils.cc",
    "line": 54,
    "size": null,
    "type": "TracingVendorCategory&"
   },
   "kind": "struct",
   "name": "result",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_b141eea0b61a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/perfetto/address/b141eea0b61a6087927aba85f2f03ce7a7b78c59/ARVO-42475280/report.log",
   "testcase_size": 19984
  },
  "input_reachability": [
   "r"
  ],
  "osv_id": "ARVO-42475280",
  "project": "perfetto",
  "sites": [
   {
    "code": "result.name[sizeof(result.name) - 1] = '\\0' | result.name[sizeof(result.name) - 1] | result.name | sizeof(result.name) - 1",
    "fn": "perfetto::trace_processor::fuchsia_trace_utils::ReadTimestamp(unsigned long const**, unsigned long)",
    "kind": "unknown",
    "line": 58,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "TracingVendorCategory&",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/radare2/libr/util/buf.c",
    "fn": "get_whole_buf",
    "line": 66
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
   "fn": "check_buffer",
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
    "file": "/src/radare2/libr/bin/p/bin_omf.c",
    "fn": "check_buffer",
    "line": 37
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_fa0a9828fe61.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/fa0a9828fe61da5b9858174d1e422fe42a248348/ARVO-42475544/report.log",
   "testcase_size": 1
  },
  "input_reachability": [],
  "osv_id": "ARVO-42475544",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "check_buffer",
    "kind": "unknown",
    "line": 37,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
   "alloc",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "symbols",
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
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/radare2/libr/bin/p/bin_xbe.c",
    "fn": "symbols",
    "line": 261
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_fa0a9828fe61.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/fa0a9828fe61da5b9858174d1e422fe42a248348/ARVO-42475545/report.log",
   "testcase_size": 300
  },
  "input_reachability": [],
  "osv_id": "ARVO-42475545",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "symbols",
    "kind": "unknown",
    "line": 261,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/open62541/src/server/ua_services_view.c",
    "fn": "RefTree_double",
    "line": 97
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1014",
   "fn": "UA_copy",
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
    "width": 24
   },
   "code": "memset(dst, 0, type->memSize) | type->memSize",
   "site": {
    "file": "/src/open62541/src/ua_types.c",
    "fn": "UA_copy",
    "line": 1012
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 1011,
    "size": null,
    "type": "void*"
   },
   "kind": "pointer",
   "name": "dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_d871105cc2bf.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/open62541/address/d871105cc2bf1c01b36018d2dd9de551c1a621d5/ARVO-42475709/report.log",
   "testcase_size": 4
  },
  "input_reachability": [
   "src",
   "dst",
   "type"
  ],
  "osv_id": "ARVO-42475709",
  "project": "open62541",
  "sites": [
   {
    "code": "memset(dst, 0, type->memSize) | type->memSize",
    "fn": "UA_copy",
    "kind": "unknown",
    "line": 1012,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "void*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "init_unpack",
    "line": 2133
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "FOR:615,IF:619",
   "fn": "run_arm_filter",
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
    "width": 1
   },
   "code": "b[3] == 0xEB | b[3]",
   "site": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "run_arm_filter",
    "line": 619
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 616,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "b",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_94ca3f0734f7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/94ca3f0734f71a0d9389ceaa237ce5a4ed8a21cd/ARVO-42476019/report.log",
   "testcase_size": 241
  },
  "input_reachability": [
   "rar",
   "flt"
  ],
  "osv_id": "ARVO-42476019",
  "project": "libarchive",
  "sites": [
   {
    "code": "b[3] == 0xEB | b[3]",
    "fn": "run_arm_filter",
    "kind": "unknown",
    "line": 619,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/work/build/../../src/perfetto/src/trace_processor/trace_parsing_fuzzer.cc",
    "fn": "perfetto::trace_processor::FuzzTraceProcessor(unsigned char const*, unsigned long)",
    "line": 28
   },
   "size_bytes": null,
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
   "fn": "inflate",
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
    "file": "/src/perfetto/buildtools/zlib/src/inflate.c",
    "fn": "inflate",
    "line": 662
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_b05aa6f24261.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/perfetto/address/b05aa6f24261e9f5af0acc9ae0ff0091bf04f0f5/ARVO-42476089/report.log",
   "testcase_size": 6
  },
  "input_reachability": [],
  "osv_id": "ARVO-42476089",
  "project": "perfetto",
  "sites": [
   {
    "code": "",
    "fn": "inflate",
    "kind": "unknown",
    "line": 662,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
   "cross_function": false,
   "site": {
    "file": "/src/icu/icu4c/source/test/fuzzer/collator_compare_fuzzer.cpp",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 19
   },
   "size_bytes": null,
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
   "fn": "showSym",
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
    "width": 3
   },
   "code": "printf(\"\\t(not MemberFunction)\\n\")",
   "site": {
    "file": "/src/icu/icu4c/source/test/fuzzer/collator_compare_fuzzer.cpp",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 20
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_6e5755a2a833.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/icu/address/6e5755a2a833bc64852eae12967d0a54d7adf629/ARVO-42476093/report.log",
   "testcase_size": 6
  },
  "input_reachability": [],
  "osv_id": "ARVO-42476093",
  "project": "icu",
  "sites": [
   {
    "code": "printf(\"\\t(not MemberFunction)\\n\")",
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "unknown",
    "line": 20,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
   "alloc",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:326,DO:328,IF:330,IF:331,BREAK:332,ELSE:334,IF:334,IF:335,BREAK:336,ELSE:338,IF:338,IF:341",
   "fn": "span",
   "guard_count": 12,
   "guards": "c<=0xff | c<=0x7ff | c<0xd800",
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
   "code": "!containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts | containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts[ | U16_GET_SUPPLEMENTARY(c, c2) | ((UChar32)(c) << 10UL) + (UChar32)(c2) - ((0xd800 << 10U",
   "site": {
    "file": "/src/icu/icu4c/source/i18n/collationiterator.cpp",
    "fn": "icu_64::CollationIterator::appendCEsFromCE32(icu_64::CollationData const*, int, unsigned int, signed char, UErrorCode&)",
    "line": 360
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/icu/icu4c/source/i18n/collationiterator.cpp",
    "line": 324,
    "size": null,
    "type": "UChar"
   },
   "kind": "struct",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_6e5755a2a833.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/icu/address/6e5755a2a833bc64852eae12967d0a54d7adf629/ARVO-42476221/report.log",
   "testcase_size": 283
  },
  "input_reachability": [
   "this",
   "s"
  ],
  "osv_id": "ARVO-42476221",
  "project": "icu",
  "sites": [
   {
    "code": "!containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts | containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts[ | U16_GET_SUPPLEMENTARY(c, c2) | ((UChar32)(c) << 10UL) + (UChar32)(c2) - ((0xd800 << 10U",
    "fn": "icu_64::CollationIterator::appendCEsFromCE32(icu_64::CollationData const*, int, unsigned int, signed char, UErrorCode&)",
    "kind": "unknown",
    "line": 360,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "UChar",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:141,IF:180,ELSE:190,IF:197,IF:214,IF:216,IF:222,IF:228,IF:234,ELSE:247,IF:261,IF:264",
   "fn": "ih264d_compute_bs_non_mbaff_thread",
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
    "width": 8
   },
   "code": "ppv_top_mv_pred_addr[1] = pu4_map_ref_idx_to_poc_l1[p1_r | ppv_top_mv_pred_addr[1] | pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]] | p1_refTop0[1]",
   "site": {
    "file": "/src/libavc/decoder/ih264d_thread_compute_bs.c",
    "fn": "ih264d_compute_bs_non_mbaff_thread",
    "line": 291
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_thread_compute_bs.c",
    "line": 148,
    "size": null,
    "type": "void**"
   },
   "kind": "pointer",
   "name": "ppv_top_mv_pred_addr",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_9046ac21822c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/9046ac21822cbb46358b5731294e6e47db571e34/ARVO-42477212/report.log",
   "testcase_size": 42
  },
  "input_reachability": [
   "ps_dec",
   "u4_mb_num"
  ],
  "osv_id": "ARVO-42477212",
  "project": "libavc",
  "sites": [
   {
    "code": "ppv_top_mv_pred_addr[1] = pu4_map_ref_idx_to_poc_l1[p1_r | ppv_top_mv_pred_addr[1] | pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]] | p1_refTop0[1]",
    "fn": "ih264d_compute_bs_non_mbaff_thread",
    "kind": "unknown",
    "line": 291,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "void**",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/decoder/ih264d_api.c",
    "fn": "ih264d_video_decode",
    "line": 2092
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:743,IF:754,WHILE:758,IF:765,IF:775,IF:783,IF:789,IF:794,ELSE:800,IF:807,IF:817,ELSE:819",
   "fn": "ih264d_cavlc_4x4res_block_totalcoeff_11to16",
   "guard_count": 10,
   "guards": "15 <= u4_lev_prefix | u4_lev_prefix < 15 | 16 <= u4_lev_prefix",
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
   "code": "FIND_ONE_IN_STREAM_32(u4_lev_prefix, u4_bitstream_offset | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "fn": "ih264d_cavlc_4x4res_block_totalcoeff_11to16",
    "line": 857
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "line": 773,
    "size": null,
    "type": "UWORD32"
   },
   "kind": "struct",
   "name": "u4_lev_prefix",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_9046ac21822c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/9046ac21822cbb46358b5731294e6e47db571e34/ARVO-42477222/report.log",
   "testcase_size": 257161
  },
  "input_reachability": [
   "u4_total_coeff_trail_one",
   "ps_bitstrm"
  ],
  "osv_id": "ARVO-42477222",
  "project": "libavc",
  "sites": [
   {
    "code": "FIND_ONE_IN_STREAM_32(u4_lev_prefix, u4_bitstream_offset | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
    "fn": "ih264d_cavlc_4x4res_block_totalcoeff_11to16",
    "kind": "unknown",
    "line": 857,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "UWORD32",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/decoder/ih264d_api.c",
    "fn": "ih264d_video_decode",
    "line": 2092
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1283,IF:1287",
   "fn": "ih264d_cavlc_parse4x4coeff_n8",
   "guard_count": 1,
   "guards": "u4_code != 3",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 4
   },
   "code": "GETBITS(u4_code, u4_bitstream_offset, pu4_bitstrm_buf, 6 | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "fn": "ih264d_cavlc_parse4x4coeff_n8",
    "line": 1283
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "line": 1280,
    "size": null,
    "type": "UWORD32"
   },
   "kind": "struct",
   "name": "u4_code",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_cd79b679b155.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/cd79b679b155097ffcb92c8f1582a7e949c46ef5/ARVO-42477302/report.log",
   "testcase_size": 263699
  },
  "input_reachability": [
   "ps_dec"
  ],
  "osv_id": "ARVO-42477302",
  "project": "libavc",
  "sites": [
   {
    "code": "GETBITS(u4_code, u4_bitstream_offset, pu4_bitstrm_buf, 6 | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
    "fn": "ih264d_cavlc_parse4x4coeff_n8",
    "kind": "unknown",
    "line": 1283,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "UWORD32",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "line": null
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:579,IF:581,WHILE:583,IF:590,ELSE:593,IF:594,FOR:595,ELSE:598",
   "fn": "decode_bit_string",
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
   "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
   "site": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "fn": "decode_bit_string",
    "line": 573
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 573,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "zero_bits",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b0241eefa1b4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/b0241eefa1b47f1420456f5dbc43564d59961a54/ARVO-42477333/report.log",
   "testcase_size": 2
  },
  "input_reachability": [
   "inbuf"
  ],
  "osv_id": "ARVO-42477333",
  "project": "opensc",
  "sites": [
   {
    "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
    "fn": "decode_bit_string",
    "kind": "unknown",
    "line": 573,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "line": null
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:579,IF:581,WHILE:583,IF:590,ELSE:593,IF:594,FOR:595,ELSE:598",
   "fn": "decode_bit_string",
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
   "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
   "site": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "fn": "decode_bit_string",
    "line": 573
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 573,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "zero_bits",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b0241eefa1b4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/b0241eefa1b47f1420456f5dbc43564d59961a54/ARVO-42477334/report.log",
   "testcase_size": 21
  },
  "input_reachability": [
   "inbuf"
  ],
  "osv_id": "ARVO-42477334",
  "project": "opensc",
  "sites": [
   {
    "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
    "fn": "decode_bit_string",
    "kind": "unknown",
    "line": 573,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/src/file/src/cdf.c",
    "fn": "cdf_realloc",
    "line": 106
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:966,GOTO:968,IF:972,GOTO:973,IF:975,GOTO:977,IF:980,GOTO:981,IF:986,GOTO:987,IF:989,GOTO:990",
   "fn": "cdf_read_property_info",
   "guard_count": 4,
   "guards": "inp == NULL | i < sh.sh_properties | inp == NULL",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 4
   },
   "code": "inp[i].pi_str.s_len = l | inp[i].pi_str.s_len | inp[i].pi_str | inp[i].pi_str",
   "site": {
    "file": "/src/file/src/cdf.c",
    "fn": "cdf_read_property_info",
    "line": 1074
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/file/src/cdf.c",
    "line": 964,
    "size": null,
    "type": "cdf_property_info_t*"
   },
   "kind": "pointer",
   "name": "inp",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/file_07d847a8d4c4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/07d847a8d4c440da564fbef4992bca2531fe676f/ARVO-42477355/report.log",
   "testcase_size": 512
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477355",
  "project": "file",
  "sites": [
   {
    "code": "inp[i].pi_str.s_len = l | inp[i].pi_str.s_len | inp[i].pi_str | inp[i].pi_str",
    "fn": "cdf_read_property_info",
    "kind": "unknown",
    "line": 1074,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "cdf_property_info_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "__libc_start_main (/lib32/libc.so.6+0x18636)",
    "line": null
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
   "fn": null,
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
    "file": null,
    "fn": null,
    "line": null
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_0a5d28fa2ec8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/curl/address/0a5d28fa2ec872de55c8d3f3b62675f17ca9cd45/ARVO-42477466/report.log",
   "testcase_size": 8
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477466",
  "project": "curl",
  "sites": [],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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