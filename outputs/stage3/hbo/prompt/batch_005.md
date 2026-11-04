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
  "osv_id": "ARVO-42475280",
  "project": "perfetto",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "result",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/perfetto/src/trace_processor/fuchsia_trace_utils.cc",
    "line": 54,
    "size": null,
    "type": "TracingVendorCategory&"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 58,
    "fn": "perfetto::trace_processor::fuchsia_trace_utils::ReadTimestamp(unsigned long const**, unsigned long)",
    "code": "result.name[sizeof(result.name) - 1] = '\\0' | result.name[sizeof(result.name) - 1] | result.name | sizeof(result.name) - 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "perfetto::trace_processor::fuchsia_trace_utils::ReadTimestamp(unsigned long const**, unsigned long)",
    "file": "/src/perfetto/src/trace_processor/fuchsia_trace_utils.cc",
    "line": 58
   },
   "code": "result.name[sizeof(result.name) - 1] = '\\0' | result.name[sizeof(result.name) - 1] | result.name | sizeof(result.name) - 1",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<lambda>0",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:52"
  },
  "call_chain": [],
  "types": {
   "entity_type": "TracingVendorCategory&",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "r"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/perfetto/address/b141eea0b61a6087927aba85f2f03ce7a7b78c59/ARVO-42475280/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_b141eea0b61a.cpg",
   "testcase_size": 19984
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "perfetto::trace_processor::fuchsia_trace_utils::ReadTimestamp(unsigned long const**, unsigned long)--perfetto::trace_processor::FuchsiaTraceParser::ParseTracePa"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "& result = categories[i]",
     "line": 54
    },
    {
     "code": "result.name[sizeof(result.name) - 1] = '\\0'",
     "line": 58
    },
    {
     "code": "result.description[sizeof(result.description) - 1] = '\\0'",
     "line": 59
    }
   ],
   "entity_decl": {
    "line": 54,
    "type": "TracingVendorCategory&"
   },
   "entity_name_cpg": "result",
   "func_lines": [
    49,
    61
   ],
   "func_params": {
    "names": [
     "r"
    ],
    "types": [
     "hidl_vec<TracingCategory>"
    ]
   },
   "guards": [
    {
     "code": "i < *size_of_arr",
     "line": 52
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "result.name[sizeof(result.name) - 1] = '\\0'",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "result.name[sizeof(result.name) - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "result.name",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "sizeof(result.name) - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "sizeof(result.name)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "result.name",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "result"
   ],
   "osv_id": "ARVO-42475280",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "perfetto::trace_processor::fuchsia_trace_utils::ReadTimestamp(unsigned long const**, unsigned long)"
  }
 },
 {
  "osv_id": "ARVO-42475544",
  "project": "radare2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "get_whole_buf",
    "file": "/src/radare2/libr/util/buf.c",
    "line": 66
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 37,
    "fn": "check_buffer",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "check_buffer",
    "file": "/src/radare2/libr/bin/p/bin_omf.c",
    "line": 37
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "check_buffer",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/fa0a9828fe61da5b9858174d1e422fe42a248348/ARVO-42475544/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_fa0a9828fe61.cpg",
   "testcase_size": 1
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "check_buffer--r_bin_get_binplugin_by_buffer--get_plugin_from_buffer"
  },
  "deep": {
   "osv_id": "ARVO-42475544"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "check_buffer"
  }
 },
 {
  "osv_id": "ARVO-42475545",
  "project": "radare2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 261,
    "fn": "symbols",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "symbols",
    "file": "/src/radare2/libr/bin/p/bin_xbe.c",
    "line": 261
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "symbols",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/fa0a9828fe61da5b9858174d1e422fe42a248348/ARVO-42475545/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_fa0a9828fe61.cpg",
   "testcase_size": 300
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "symbols--r_bin_object_set_items--r_bin_object_new"
  },
  "deep": {
   "osv_id": "ARVO-42475545"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "symbols"
  }
 },
 {
  "osv_id": "ARVO-42475709",
  "project": "open62541",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 1011,
    "size": null,
    "type": "void*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "RefTree_double",
    "file": "/src/open62541/src/server/ua_services_view.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1012,
    "fn": "UA_copy",
    "code": "memset(dst, 0, type->memSize) | type->memSize",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "UA_copy",
    "file": "/src/open62541/src/ua_types.c",
    "line": 1012
   },
   "code": "memset(dst, 0, type->memSize) | type->memSize",
   "access": {
    "dir": "WRITE",
    "width": 24,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "UA_copy",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1014"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "src",
   "dst",
   "type"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/open62541/address/d871105cc2bf1c01b36018d2dd9de551c1a621d5/ARVO-42475709/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_d871105cc2bf.cpg",
   "testcase_size": 4
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memset--UA_copy--UA_NodeId_copy"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1011,
    "type": "void*"
   },
   "entity_name_cpg": "dst",
   "func_lines": [
    1010,
    1017
   ],
   "func_params": {
    "names": [
     "src",
     "dst",
     "type"
    ],
    "types": [
     "void*",
     "void*",
     "UA_DataType*"
    ]
   },
   "guards": [
    {
     "code": "retval != UA_STATUSCODE_GOOD",
     "line": 1014
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memset(dst, 0, type->memSize)",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "type->memSize",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dst",
    "type"
   ],
   "osv_id": "ARVO-42475709",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "UA_copy"
  }
 },
 {
  "osv_id": "ARVO-42476019",
  "project": "libarchive",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "b",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 616,
    "size": null,
    "type": "uint8_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "init_unpack",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 2133
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 619,
    "fn": "run_arm_filter",
    "code": "b[3] == 0xEB | b[3]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "run_arm_filter",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 619
   },
   "code": "b[3] == 0xEB | b[3]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "run_arm_filter",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:615,IF:619"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "rar",
   "flt"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/94ca3f0734f71a0d9389ceaa237ce5a4ed8a21cd/ARVO-42476019/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_94ca3f0734f7.cpg",
   "testcase_size": 241
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "run_arm_filter--run_filter--apply_filters"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* b = &rar->cstate.window_buf[(rar->cstate.solid_offset +",
     "line": 616
    }
   ],
   "entity_decl": {
    "line": 616,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "b",
   "func_lines": [
    604,
    631
   ],
   "func_params": {
    "names": [
     "rar",
     "flt"
    ],
    "types": [
     "rar5*",
     "filter_info*"
    ]
   },
   "guards": [
    {
     "code": "i < flt->block_length - 3",
     "line": 615
    },
    {
     "code": "b[3] == 0xEB",
     "line": 619
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "b[3] == 0xEB",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "b[3]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "b"
   ],
   "osv_id": "ARVO-42476019",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "run_arm_filter"
  }
 },
 {
  "osv_id": "ARVO-42476089",
  "project": "perfetto",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "perfetto::trace_processor::FuzzTraceProcessor(unsigned char const*, unsigned long)",
    "file": "/work/build/../../src/perfetto/src/trace_processor/trace_parsing_fuzzer.cc",
    "line": 28
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 662,
    "fn": "inflate",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "inflate",
    "file": "/src/perfetto/buildtools/zlib/src/inflate.c",
    "line": 662
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "inflate",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/perfetto/address/b05aa6f24261e9f5af0acc9ae0ff0091bf04f0f5/ARVO-42476089/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_b05aa6f24261.cpg",
   "testcase_size": 6
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "inflate--perfetto::trace_processor::GzipTraceParser::Parse(std::__1::unique_ptr<unsigned char [], std::__1::default_delete<unsigned char []> >, unsigned long)--"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    -1,
    -1
   ],
   "func_params": {
    "names": [
     "p1",
     "p2"
    ],
    "types": [
     "ANY",
     "ANY"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42476089",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "inflate"
  }
 },
 {
  "osv_id": "ARVO-42476093",
  "project": "icu",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/icu/icu4c/source/test/fuzzer/collator_compare_fuzzer.cpp",
    "line": 19
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 20,
    "fn": "LLVMFuzzerTestOneInput",
    "code": "printf(\"\\t(not MemberFunction)\\n\")",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/icu/icu4c/source/test/fuzzer/collator_compare_fuzzer.cpp",
    "line": 20
   },
   "code": "printf(\"\\t(not MemberFunction)\\n\")",
   "access": {
    "dir": "WRITE",
    "width": 3,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "showSym",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/icu/address/6e5755a2a833bc64852eae12967d0a54d7adf629/ARVO-42476093/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_6e5755a2a833.cpg",
   "testcase_size": 6
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    8,
    22
   ],
   "func_params": {
    "names": [
     "str"
    ],
    "types": [
     "char*"
    ]
   },
   "guards": [
    {
     "code": "name->Kind() == MemberFunction",
     "line": 14
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "printf(\"\\t(not MemberFunction)\\n\")",
     "name": "printf",
     "nargs": 1
    }
   ],
   "line_ids": [],
   "osv_id": "ARVO-42476093",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "LLVMFuzzerTestOneInput"
  }
 },
 {
  "osv_id": "ARVO-42476221",
  "project": "icu",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/icu/icu4c/source/i18n/collationiterator.cpp",
    "line": 324,
    "size": null,
    "type": "UChar"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 360,
    "fn": "icu_64::CollationIterator::appendCEsFromCE32(icu_64::CollationData const*, int, unsigned int, signed char, UErrorCode&)",
    "code": "!containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts | containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts[ | U16_GET_SUPPLEMENTARY(c, c2) | ((UChar32)(c) << 10UL) + (UChar32)(c2) - ((0xd800 << 10U",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "icu_64::CollationIterator::appendCEsFromCE32(icu_64::CollationData const*, int, unsigned int, signed char, UErrorCode&)",
    "file": "/src/icu/icu4c/source/i18n/collationiterator.cpp",
    "line": 360
   },
   "code": "!containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts | containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts[ | U16_GET_SUPPLEMENTARY(c, c2) | ((UChar32)(c) << 10UL) + (UChar32)(c2) - ((0xd800 << 10U",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "span",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "c<=0xff | c<=0x7ff | c<0xd800",
   "guard_count": 12,
   "control_structures": "IF:326,DO:328,IF:330,IF:331,BREAK:332,ELSE:334,IF:334,IF:335,BREAK:336,ELSE:338,IF:338,IF:341"
  },
  "call_chain": [],
  "types": {
   "entity_type": "UChar",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "this",
   "s"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/icu/address/6e5755a2a833bc64852eae12967d0a54d7adf629/ARVO-42476221/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_6e5755a2a833.cpg",
   "testcase_size": 283
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "icu_64::CollationIterator::appendCEsFromCE32(icu_64::CollationData const*, int, unsigned int, signed char, UErrorCode&)--icu_64::DataBuilderCollationIterator::f"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c=*s",
     "line": 329
    },
    {
     "code": "c=*s",
     "line": 369
    }
   ],
   "entity_decl": {
    "line": 324,
    "type": "UChar"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    322,
    408
   ],
   "func_params": {
    "names": [
     "this",
     "s",
     "limit",
     "spanCondition"
    ],
    "types": [
     "icu_64.BMPSet",
     "UChar*",
     "UChar*",
     "USetSpanCondition"
    ]
   },
   "guards": [
    {
     "code": "(table7FF[c&0x3f]&((uint32_t)1<<(c>>6)))==0",
     "line": 335
    },
    {
     "code": "c<0xd800",
     "line": 338
    },
    {
     "code": "twoBits==0",
     "line": 344
    },
    {
     "code": "(s+1)==limit",
     "line": 353
    },
    {
     "code": "(c2=s[1])<0xdc00",
     "line": 353
    },
    {
     "code": "++s<limit",
     "line": 365
    },
    {
     "code": "(table7FF[c&0x3f]&((uint32_t)1<<(c>>6)))!=0",
     "line": 375
    },
    {
     "code": "c<0xd800",
     "line": 378
    },
    {
     "code": "twoBits!=0",
     "line": 384
    },
    {
     "code": "(s+1)==limit",
     "line": 393
    },
    {
     "code": "(c2=s[1])<0xdc00",
     "line": 393
    },
    {
     "code": "++s<limit",
     "line": 405
    }
   ],
   "line_call_count": 15,
   "line_calls": [
    {
     "code": "!containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts[0x10], list4kStarts[0x11])",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "containsSlow(U16_GET_SUPPLEMENTARY(c, c2), list4kStarts[0x10], list4kStarts[0x11])",
     "name": "containsSlow",
     "nargs": 3
    },
    {
     "code": "U16_GET_SUPPLEMENTARY(c, c2)",
     "name": "U16_GET_SUPPLEMENTARY",
     "nargs": 2
    },
    {
     "code": "((UChar32)(c) << 10UL) + (UChar32)(c2) - ((0xd800 << 10UL) + 0xdc00 - 0x10000)",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "((UChar32)(c) << 10UL) + (UChar32)(c2)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(UChar32)(c) << 10UL",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(UChar32)(c)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(UChar32)(c2)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(0xd800 << 10UL) + 0xdc00 - 0x10000",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "(0xd800 << 10UL) + 0xdc00",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "0xd800 << 10UL",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "list4kStarts[0x10]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "this->list4kStarts",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "list4kStarts[0x11]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "this->list4kStarts",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c",
    "c2",
    "this"
   ],
   "osv_id": "ARVO-42476221",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "icu_64::CollationIterator::appendCEsFromCE32(icu_64::CollationData const*, int, unsigned int, signed char, UErrorCode&)"
  }
 },
 {
  "osv_id": "ARVO-42477212",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ppv_top_mv_pred_addr",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_thread_compute_bs.c",
    "line": 148,
    "size": null,
    "type": "void**"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 291,
    "fn": "ih264d_compute_bs_non_mbaff_thread",
    "code": "ppv_top_mv_pred_addr[1] = pu4_map_ref_idx_to_poc_l1[p1_r | ppv_top_mv_pred_addr[1] | pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]] | p1_refTop0[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_compute_bs_non_mbaff_thread",
    "file": "/src/libavc/decoder/ih264d_thread_compute_bs.c",
    "line": 291
   },
   "code": "ppv_top_mv_pred_addr[1] = pu4_map_ref_idx_to_poc_l1[p1_r | ppv_top_mv_pred_addr[1] | pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]] | p1_refTop0[1]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_compute_bs_non_mbaff_thread",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:141,IF:180,ELSE:190,IF:197,IF:214,IF:216,IF:222,IF:228,IF:234,ELSE:247,IF:261,IF:264"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ps_dec",
   "u4_mb_num"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/9046ac21822cbb46358b5731294e6e47db571e34/ARVO-42477212/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_9046ac21822c.cpg",
   "testcase_size": 42
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "ih264d_compute_bs_non_mbaff_thread--ih264d_recon_deblk_slice--ih264d_recon_deblk_thread"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "** ppv_top_mv_pred_addr = ps_cur_mb_info->ps_curmb->u4_pic_addrress",
     "line": 148
    },
    {
     "code": "ppv_top_mv_pred_addr[0] = apv_map_ref_idx_to_poc[p1_refTop0[0]]",
     "line": 158
    },
    {
     "code": "ppv_top_mv_pred_addr[1] = pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]]",
     "line": 159
    },
    {
     "code": "ppv_top_mv_pred_addr[2] = apv_map_ref_idx_to_poc[p1_refTop1[0]]",
     "line": 162
    },
    {
     "code": "ppv_top_mv_pred_addr[3] = pu4_map_ref_idx_to_poc_l1[p1_refTop1[1]]",
     "line": 164
    },
    {
     "code": "** ppv_top_mv_pred_addr = ps_cur_mb_info->ps_curmb->u4_pic_addrress",
     "line": 281
    },
    {
     "code": "ppv_top_mv_pred_addr[0] = apv_map_ref_idx_to_poc[p1_refTop0[0]]",
     "line": 290
    },
    {
     "code": "ppv_top_mv_pred_addr[1] = pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]]",
     "line": 291
    },
    {
     "code": "ppv_top_mv_pred_addr[2] = apv_map_ref_idx_to_poc[p1_refTop1[0]]",
     "line": 294
    },
    {
     "code": "ppv_top_mv_pred_addr[3] = pu4_map_ref_idx_to_poc_l1[p1_refTop1[1]]",
     "line": 296
    }
   ],
   "entity_decl": {
    "line": 281,
    "type": "void**"
   },
   "entity_name_cpg": "ppv_top_mv_pred_addr",
   "func_lines": [
    89,
    315
   ],
   "func_params": {
    "names": [
     "ps_dec",
     "ps_cur_mb_info",
     "u4_mb_num"
    ],
    "types": [
     "dec_struct_t*",
     "dec_mb_info_t*",
     "UWORD32"
    ]
   },
   "guards": [
    {
     "code": "ps_dec->ps_cur_sps->u1_profile_idc == HIGH_PROFILE_IDC",
     "line": 214
    },
    {
     "code": "ps_cur_mb_info->u1_tran_form8x8 == 1",
     "line": 216
    },
    {
     "code": "ps_cur_mb_info->ps_left_mb->u1_tran_form8x8 == 1",
     "line": 222
    },
    {
     "code": "ps_cur_mb_info->ps_top_mb->u1_tran_form8x8 == 1",
     "line": 228
    },
    {
     "code": "ps_dec->ps_computebs_cur_slice->slice_type == B_SLICE",
     "line": 250
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "ppv_top_mv_pred_addr[1] = pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ppv_top_mv_pred_addr[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pu4_map_ref_idx_to_poc_l1[p1_refTop0[1]]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "p1_refTop0[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ppv_top_mv_pred_addr",
    "pu4_map_ref_idx_to_poc_l1",
    "p1_refTop0"
   ],
   "osv_id": "ARVO-42477212",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_compute_bs_non_mbaff_thread"
  }
 },
 {
  "osv_id": "ARVO-42477222",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "u4_lev_prefix",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "line": 773,
    "size": null,
    "type": "UWORD32"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "ih264d_video_decode",
    "file": "/src/libavc/decoder/ih264d_api.c",
    "line": 2092
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "19",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 857,
    "fn": "ih264d_cavlc_4x4res_block_totalcoeff_11to16",
    "code": "FIND_ONE_IN_STREAM_32(u4_lev_prefix, u4_bitstream_offset | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_cavlc_4x4res_block_totalcoeff_11to16",
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "line": 857
   },
   "code": "FIND_ONE_IN_STREAM_32(u4_lev_prefix, u4_bitstream_offset | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_cavlc_4x4res_block_totalcoeff_11to16",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "15 <= u4_lev_prefix | u4_lev_prefix < 15 | 16 <= u4_lev_prefix",
   "guard_count": 10,
   "control_structures": "IF:743,IF:754,WHILE:758,IF:765,IF:775,IF:783,IF:789,IF:794,ELSE:800,IF:807,IF:817,ELSE:819"
  },
  "call_chain": [],
  "types": {
   "entity_type": "UWORD32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "u4_total_coeff_trail_one",
   "ps_bitstrm"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/9046ac21822cbb46358b5731294e6e47db571e34/ARVO-42477222/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_9046ac21822c.cpg",
   "testcase_size": 257161
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "ih264d_cavlc_4x4res_block_totalcoeff_11to16--ih264d_cavlc_parse4x4coeff_n0to7--ih264d_cavlc_parse_8x8block_both_available"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "u4_lev_prefix = CLZ(u4_word)",
     "line": 783
    },
    {
     "code": "u4_lev_prefix = CLZ(u4_word)",
     "line": 807
    },
    {
     "code": "u4_lev_prefix = CLZ(u4_word)",
     "line": 857
    }
   ],
   "entity_decl": {
    "line": 773,
    "type": "UWORD32"
   },
   "entity_name_cpg": "u4_lev_prefix",
   "func_lines": [
    718,
    972
   ],
   "func_params": {
    "names": [
     "u4_isdc",
     "u4_total_coeff_trail_one",
     "ps_bitstrm"
    ],
    "types": [
     "UWORD32",
     "UWORD32",
     "dec_bit_stream_t*"
    ]
   },
   "guards": [
    {
     "code": "u4_trailing_ones < 3",
     "line": 775
    },
    {
     "code": "u4_lev_prefix < 15",
     "line": 791
    },
    {
     "code": "15 < u4_lev_prefix",
     "line": 813
    },
    {
     "code": "3 == u4_trailing_ones",
     "line": 815
    },
    {
     "code": "14 == u4_lev_prefix",
     "line": 817
    },
    {
     "code": "u2_abs_value > 3",
     "line": 846
    },
    {
     "code": "15 < u4_lev_prefix",
     "line": 869
    },
    {
     "code": "u4_suffix_len < 6",
     "line": 889
    },
    {
     "code": "u2_abs_value",
     "line": 890
    },
    {
     "code": "u4_total_coeff < (16 - u4_isdc)",
     "line": 902
    },
    {
     "code": "u4_zeroes_left > 0",
     "line": 932
    },
    {
     "code": "u4_zeroes_left < 0",
     "line": 953
    }
   ],
   "line_call_count": 18,
   "line_calls": [
    {
     "code": "FIND_ONE_IN_STREAM_32(u4_lev_prefix, u4_bitstream_offset,",
     "name": "FIND_ONE_IN_STREAM_32",
     "nargs": null
    },
    {
     "code": "UWORD32 *",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "UWORD32",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(u4_bitstream_offset) >> 5",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "UWORD32",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(u4_bitstream_offset) & 0x1F",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "u4_word = pu4_buf[u4_word_off++] << u4_bit_off",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off++] << u4_bit_off",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "u4_word_off++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "u4_word ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "pu4_buf[u4_word_off] >> (32 - u4_bit_off)",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "32 - u4_bit_off",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "u4_lev_prefix = CLZ(u4_word)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "CLZ(u4_word)",
     "name": "CLZ",
     "nargs": 1
    },
    {
     "code": "(u4_bitstream_offset) += (u4_lev_prefix + 1)",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "u4_lev_prefix + 1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "u4_lev_prefix",
    "u4_bitstream_offset",
    "pu4_bitstrm_buf",
    "pu4_buf",
    "u4_word_off",
    "u4_bit_off",
    "u4_word"
   ],
   "osv_id": "ARVO-42477222",
   "sites": [
    {
     "args": "19",
     "callee": "<operator>.alloc",
     "code": "ai2_level_arr[19]",
     "line": 731
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "(*ppi2_trlone_lkup)[3] =",
     "line": 750
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "(*ppu1_total_zero_lkup)[16] =",
     "line": 905
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_cavlc_4x4res_block_totalcoeff_11to16"
  }
 },
 {
  "osv_id": "ARVO-42477302",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "u4_code",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "line": 1280,
    "size": null,
    "type": "UWORD32"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "ih264d_video_decode",
    "file": "/src/libavc/decoder/ih264d_api.c",
    "line": 2092
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1283,
    "fn": "ih264d_cavlc_parse4x4coeff_n8",
    "code": "GETBITS(u4_code, u4_bitstream_offset, pu4_bitstrm_buf, 6 | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_cavlc_parse4x4coeff_n8",
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "line": 1283
   },
   "code": "GETBITS(u4_code, u4_bitstream_offset, pu4_bitstrm_buf, 6 | UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_cavlc_parse4x4coeff_n8",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "u4_code != 3",
   "guard_count": 1,
   "control_structures": "IF:1283,IF:1287"
  },
  "call_chain": [],
  "types": {
   "entity_type": "UWORD32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ps_dec"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/cd79b679b155097ffcb92c8f1582a7e949c46ef5/ARVO-42477302/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_cd79b679b155.cpg",
   "testcase_size": 263699
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "ih264d_cavlc_parse4x4coeff_n8--ih264d_cavlc_parse_8x8block_both_available--ih264d_parse_residual4x4_cavlc"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "u4_code = pu4_buf[u4_word_off++] << u4_bit_off",
     "line": 1283
    },
    {
     "code": "u4_code = u4_code >> (32 - 6)",
     "line": 1283
    }
   ],
   "entity_decl": {
    "line": 1280,
    "type": "UWORD32"
   },
   "entity_name_cpg": "u4_code",
   "func_lines": [
    1270,
    1303
   ],
   "func_params": {
    "names": [
     "pi2_coeff_block",
     "u4_isdc",
     "u4_n",
     "ps_dec",
     "pu4_total_coeff"
    ],
    "types": [
     "WORD16*",
     "UWORD32",
     "WORD32",
     "dec_struct_t*",
     "UWORD32*"
    ]
   },
   "guards": [
    {
     "code": "u4_code != 3",
     "line": 1287
    }
   ],
   "line_call_count": 18,
   "line_calls": [
    {
     "code": "GETBITS(u4_code, u4_bitstream_offset, pu4_bitstrm_buf, 6)",
     "name": "GETBITS",
     "nargs": 4
    },
    {
     "code": "UWORD32 *",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "UWORD32",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(u4_bitstream_offset) >> 5",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "UWORD32",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(u4_bitstream_offset) & 0x1F",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "u4_code = pu4_buf[u4_word_off++] << u4_bit_off",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off++] << u4_bit_off",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "u4_word_off++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "u4_code ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "pu4_buf[u4_word_off] >> (32 - u4_bit_off)",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "32 - u4_bit_off",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "u4_code = u4_code >> (32 - 6)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "u4_code >> (32 - 6)",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "32 - 6",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "(u4_bitstream_offset) += 6",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    }
   ],
   "line_ids": [
    "u4_code",
    "u4_bitstream_offset",
    "pu4_bitstrm_buf",
    "pu4_buf",
    "u4_word_off",
    "u4_bit_off"
   ],
   "osv_id": "ARVO-42477302",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_cavlc_parse4x4coeff_n8"
  }
 },
 {
  "osv_id": "ARVO-42477333",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "zero_bits",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 573,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 573,
    "fn": "decode_bit_string",
    "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "decode_bit_string",
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 573
   },
   "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "decode_bit_string",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:579,IF:581,WHILE:583,IF:590,ELSE:593,IF:594,FOR:595,ELSE:598"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "inbuf"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/b0241eefa1b47f1420456f5dbc43564d59961a54/ARVO-42477333/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b0241eefa1b4.cpg",
   "testcase_size": 2
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "decode_bit_string--sc_asn1_print_bit_string--print_tags_recursive"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "zero_bits = *in & 0x07",
     "line": 573
    }
   ],
   "entity_decl": {
    "line": 573,
    "type": "int"
   },
   "entity_name_cpg": "zero_bits",
   "func_lines": [
    568,
    607
   ],
   "func_params": {
    "names": [
     "inbuf",
     "inlen",
     "outbuf",
     "outlen",
     "invert"
    ],
    "types": [
     "u8*",
     "size_t",
     "void*",
     "size_t",
     "int"
    ]
   },
   "guards": [
    {
     "code": "outlen < octets_left",
     "line": 579
    },
    {
     "code": "inlen < 1",
     "line": 581
    },
    {
     "code": "octets_left == 1",
     "line": 590
    },
    {
     "code": "i < bits_to_go",
     "line": 595
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "zero_bits = *in & 0x07",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*in & 0x07",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "*in",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "zero_bits",
    "in"
   ],
   "osv_id": "ARVO-42477333",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "decode_bit_string"
  }
 },
 {
  "osv_id": "ARVO-42477334",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "zero_bits",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 573,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 573,
    "fn": "decode_bit_string",
    "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "decode_bit_string",
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 573
   },
   "code": "zero_bits = *in & 0x07 | *in & 0x07 | *in",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "decode_bit_string",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:579,IF:581,WHILE:583,IF:590,ELSE:593,IF:594,FOR:595,ELSE:598"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "inbuf"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/b0241eefa1b47f1420456f5dbc43564d59961a54/ARVO-42477334/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b0241eefa1b4.cpg",
   "testcase_size": 21
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "decode_bit_string--decode_bit_field--asn1_decode_entry"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "zero_bits = *in & 0x07",
     "line": 573
    }
   ],
   "entity_decl": {
    "line": 573,
    "type": "int"
   },
   "entity_name_cpg": "zero_bits",
   "func_lines": [
    568,
    607
   ],
   "func_params": {
    "names": [
     "inbuf",
     "inlen",
     "outbuf",
     "outlen",
     "invert"
    ],
    "types": [
     "u8*",
     "size_t",
     "void*",
     "size_t",
     "int"
    ]
   },
   "guards": [
    {
     "code": "outlen < octets_left",
     "line": 579
    },
    {
     "code": "inlen < 1",
     "line": 581
    },
    {
     "code": "octets_left == 1",
     "line": 590
    },
    {
     "code": "i < bits_to_go",
     "line": 595
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "zero_bits = *in & 0x07",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*in & 0x07",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "*in",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "zero_bits",
    "in"
   ],
   "osv_id": "ARVO-42477334",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "decode_bit_string"
  }
 },
 {
  "osv_id": "ARVO-42477355",
  "project": "file",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "inp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/file/src/cdf.c",
    "line": 964,
    "size": null,
    "type": "cdf_property_info_t*"
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "cdf_realloc",
    "file": "/src/file/src/cdf.c",
    "line": 106
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1074,
    "fn": "cdf_read_property_info",
    "code": "inp[i].pi_str.s_len = l | inp[i].pi_str.s_len | inp[i].pi_str | inp[i].pi_str",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "cdf_read_property_info",
    "file": "/src/file/src/cdf.c",
    "line": 1074
   },
   "code": "inp[i].pi_str.s_len = l | inp[i].pi_str.s_len | inp[i].pi_str | inp[i].pi_str",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cdf_read_property_info",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "inp == NULL | i < sh.sh_properties | inp == NULL",
   "guard_count": 4,
   "control_structures": "IF:966,GOTO:968,IF:972,GOTO:973,IF:975,GOTO:977,IF:980,GOTO:981,IF:986,GOTO:987,IF:989,GOTO:990"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cdf_property_info_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/07d847a8d4c440da564fbef4992bca2531fe676f/ARVO-42477355/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/file_07d847a8d4c4.cpg",
   "testcase_size": 512
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "cdf_read_property_info--cdf_unpack_summary_info--cdf_file_summary_info"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "inp = cdf_grow_info(info, maxcount, sh.sh_properties)",
     "line": 988
    },
    {
     "code": "inp[i].pi_id = CDF_GETUINT32(p, i << 1)",
     "line": 1001
    },
    {
     "code": "inp[i].pi_type = CDF_GETUINT32(q, 0)",
     "line": 1007
    },
    {
     "code": "inp = cdf_grow_info(info, maxcount, nelements)",
     "line": 1054
    },
    {
     "code": "inp[i].pi_str.s_len = l",
     "line": 1074
    },
    {
     "code": "inp[i].pi_str.s_buf = CAST(const char *,",
     "line": 1075
    }
   ],
   "entity_decl": {
    "line": 964,
    "type": "cdf_property_info_t*"
   },
   "entity_name_cpg": "inp",
   "func_lines": [
    956,
    1111
   ],
   "func_params": {
    "names": [
     "sst",
     "h",
     "offs",
     "info",
     "count",
     "maxcount"
    ],
    "types": [
     "cdf_stream_t*",
     "cdf_header_t*",
     "uint32_t",
     "cdf_property_info_t**",
     "size_t*",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "offs > UINT32_MAX / 4",
     "line": 966
    },
    {
     "code": "cdf_check_stream_offset(sst, h, shp, sizeof(*shp), __LINE__) == -1",
     "line": 972
    },
    {
     "code": "cdf_bo.u == ((uint32_t)(0x01020304))",
     "line": 974
    },
    {
     "code": "sh.sh_len > CDF_SHLEN_LIMIT",
     "line": 975
    },
    {
     "code": "cdf_check_stream_offset(sst, h, shp, sh.sh_len, __LINE__) == -1",
     "line": 980
    },
    {
     "code": "cdf_bo.u == ((uint32_t)(0x01020304))",
     "line": 983
    },
    {
     "code": "sh.sh_properties > CDF_PROP_LIMIT",
     "line": 986
    },
    {
     "code": "inp == NULL",
     "line": 989
    },
    {
     "code": "cdf_check_stream_offset(sst, h, e, 0, __LINE__) == -1",
     "line": 995
    },
    {
     "code": "i < sh.sh_properties",
     "line": 998
    },
    {
     "code": "(q = cdf_get_property_info_pos(sst, h, p, e, i)) == NULL",
     "line": 999
    },
    {
     "code": "left < sizeof(uint32_t)",
     "line": 1003
    },
    {
     "code": "left < sizeof(uint32_t) * 2",
     "line": 1011
    },
    {
     "code": "nelements == 0",
     "line": 1016
    },
    {
     "code": "nelements > 1",
     "line": 1052
    },
    {
     "code": "inp == NULL",
     "line": 1055
    },
    {
     "code": "j < nelements",
     "line": 1061
    },
    {
     "code": "i < sh.sh_properties",
     "line": 1061
    },
    {
     "code": "o4 + sizeof(uint32_t) > left",
     "line": 1066
    },
    {
     "code": "o4 + l > left",
     "line": 1071
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "inp[i].pi_str.s_len = l",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "inp[i].pi_str.s_len",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "inp[i].pi_str",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "inp[i].pi_str",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "inp[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "inp",
    "i",
    "l"
   ],
   "osv_id": "ARVO-42477355",
   "sites": [
    {
     "args": "*info",
     "callee": "free",
     "code": "free(*info)",
     "line": 1105
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "cdf_read_property_info"
  }
 },
 {
  "osv_id": "ARVO-42477466",
  "project": "curl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib32/libc.so.6+0x18636)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": null,
    "file": null,
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
   "fn": null,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/curl/address/0a5d28fa2ec872de55c8d3f3b62675f17ca9cd45/ARVO-42477466/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_0a5d28fa2ec8.cpg",
   "testcase_size": 8
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "to_u32(unsigned char const*)--fuzz_get_tlv_comn(fuzz_data*, tlv*)--fuzz_add_mime_part(tlv*, curl_mimepart_s*)"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": null
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
        "free_cross_function": "true | false | unknown",
        "cross_frame_count": "number | unknown"
      },
      "dimension_distributions": {"维度名": {"取值": "样本数"}},
      "evidence": ["string"],
      "confidence": "high | medium | low"
    }
  ],
  "unclassified": [{"sample_id": "string", "reason": "string", "missing_fields": ["string"]}],
  "batch_observations": "string"
}

直接输出 JSON，不要任何解释文字。