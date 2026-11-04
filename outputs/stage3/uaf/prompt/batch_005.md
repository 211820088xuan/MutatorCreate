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
  "osv_id": "ARVO-42507154",
  "project": "open62541",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 1018,
    "size": null,
    "type": "void**"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Array_decodeBinary",
    "file": "/src/open62541/src/ua_types_encoding_binary.c",
    "line": 551
   },
   "size_expr": null,
   "size_bytes": 2,
   "cross_function": true,
   "size_expr_cpg": "size ;; type->memSize",
   "size_expr_cpg_callee": "UA_calloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 979,
    "fn": "deleteMembers_noInit",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1036,
    "fn": "UA_Array_copy",
    "code": "memcpy(*dst, src, type->memSize * size) | *dst | type->memSize * size | type->memSize",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "UA_Array_copy",
    "file": "/src/open62541/src/ua_types.c",
    "line": 1036
   },
   "code": "memcpy(*dst, src, type->memSize * size) | *dst | type->memSize * size | type->memSize",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": 2
   }
  },
  "context": {
   "fn": "UA_Array_copy",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "size == 0 | src == NULL | i < size",
   "guard_count": 3,
   "control_structures": "IF:1019,IF:1020,ELSE:1023,IF:1027,IF:1032,IF:1035,FOR:1043,IF:1048"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "src",
   "size",
   "dst",
   "type"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/b916bd061121852f7025f3610ae0074f8d597f7f/ARVO-42507154/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_b916bd061121.cpg",
   "testcase_size": 21
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 2,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--UA_Array_copy--copy_noInit",
   "region_size": 2
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1018,
    "type": "void**"
   },
   "entity_name_cpg": "dst",
   "func_lines": [
    1016,
    1053
   ],
   "func_params": {
    "names": [
     "src",
     "size",
     "dst",
     "type"
    ],
    "types": [
     "void*",
     "size_t",
     "void**",
     "UA_DataType*"
    ]
   },
   "guards": [
    {
     "code": "size == 0",
     "line": 1019
    },
    {
     "code": "src == NULL",
     "line": 1020
    },
    {
     "code": "i < size",
     "line": 1043
    },
    {
     "code": "retval != UA_STATUSCODE_GOOD",
     "line": 1048
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(*dst, src, type->memSize * size)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "*dst",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "type->memSize * size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "type->memSize",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dst",
    "src",
    "type",
    "size"
   ],
   "osv_id": "ARVO-42507154",
   "sites": [
    {
     "args": "size ;; type->memSize",
     "callee": "UA_calloc",
     "code": "UA_calloc(size, type->memSize)",
     "line": 1031
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "deleteMembers_noInit",
   "use_fn": "UA_Array_copy"
  }
 },
 {
  "osv_id": "ARVO-42507972",
  "project": "harfbuzz",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "hb_malloc_impl",
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "line": 45
   },
   "size_expr": null,
   "size_bytes": 704,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 60,
    "fn": "hb_free_impl",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 242,
    "fn": "next",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "next",
    "file": "/src/harfbuzz/src/hb-bit-set-invertible.hh",
    "line": 242
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 704
   }
  },
  "context": {
   "fn": "next",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/harfbuzz/address/bc899650c7976df7bc62ed55da5268f1d10b9a43/ARVO-42507972/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_bc899650c797.cpg",
   "testcase_size": 1700
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 704,
   "loc_offset": 696,
   "loc_kind": "region",
   "dedup_token": "next--hb_bit_set_invertible_t::intersects(unsigned int, unsigned int) const--intersects",
   "region_size": 704
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    39,
    106
   ],
   "func_params": {
    "names": [
     "text",
     "end",
     "unicode",
     "replacement"
    ],
    "types": [
     "codepoint_t*",
     "codepoint_t*",
     "hb_codepoint_t*",
     "hb_codepoint_t"
    ]
   },
   "guards": [
    {
     "code": "c > 0x7Fu",
     "line": 51
    },
    {
     "code": "hb_in_range<hb_codepoint_t> (c, 0xC2u, 0xDFu)",
     "line": 53
    },
    {
     "code": "hb_in_range<hb_codepoint_t",
     "line": 53
    },
    {
     "code": "text < end",
     "line": 56
    },
    {
     "code": "hb_in_range<hb_codepoint_t> (c, 0xE0u, 0xEFu)",
     "line": 65
    },
    {
     "code": "hb_in_range<hb_codepoint_t",
     "line": 65
    },
    {
     "code": "1 < end - text",
     "line": 68
    },
    {
     "code": "c < 0x0800u",
     "line": 73
    },
    {
     "code": "hb_in_range < hb_codepoint_t > (c, 0xD800u, 0xDFFFu)",
     "line": 73
    },
    {
     "code": "hb_in_range < hb_codepoint_t",
     "line": 73
    },
    {
     "code": "hb_in_range<hb_codepoint_t> (c, 0xF0u, 0xF4u)",
     "line": 80
    },
    {
     "code": "hb_in_range<hb_codepoint_t",
     "line": 80
    },
    {
     "code": "2 < end - text",
     "line": 83
    },
    {
     "code": "!hb_in_range < hb_codepoint_t > (c, 0x10000u, 0x10FFFFu)",
     "line": 89
    },
    {
     "code": "!hb_in_range < hb_codepoint_t",
     "line": 89
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42507972",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 4,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "hb_free_impl",
   "use_fn": "next"
  }
 },
 {
  "osv_id": "ARVO-42508038",
  "project": "harfbuzz",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "hb_malloc_impl",
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "line": 45
   },
   "size_expr": null,
   "size_bytes": 512,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 60,
    "fn": "hb_free_impl",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 153,
    "fn": "as_array",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "as_array",
    "file": "/src/harfbuzz/src/hb-vector.hh",
    "line": 153
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 512
   }
  },
  "context": {
   "fn": "as_array",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/harfbuzz/address/bc899650c7976df7bc62ed55da5268f1d10b9a43/ARVO-42508038/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_bc899650c797.cpg",
   "testcase_size": 2288
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 512,
   "loc_offset": 492,
   "loc_kind": "region",
   "dedup_token": "as_array--bsearch<hb_bit_set_t::page_map_t, true, nullptr>--page_for",
   "region_size": 512
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    -1,
    -1
   ],
   "func_params": {
    "names": [
     "p1"
    ],
    "types": [
     "ANY"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42508038",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "hb_free_impl",
   "use_fn": "as_array"
  }
 },
 {
  "osv_id": "ARVO-42508045",
  "project": "harfbuzz",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "buf_size",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-bit-set-invertible.hh",
    "line": 209,
    "size": null,
    "type": "unsigned int"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "hb_malloc_impl",
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "line": 45
   },
   "size_expr": null,
   "size_bytes": 704,
   "cross_function": true,
   "size_expr_cpg": "1024",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 60,
    "fn": "hb_free_impl",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 242,
    "fn": "hb_bit_set_invertible_t::next(unsigned int*) const",
    "code": "buf_size > l",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hb_bit_set_invertible_t::next(unsigned int*) const",
    "file": "/src/harfbuzz/src/hb-bit-set-invertible.hh",
    "line": 242
   },
   "code": "buf_size > l",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 704
   }
  },
  "context": {
   "fn": "_hb_buffer_serialize_unicode_json",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "buf_size > l",
   "guard_count": 1,
   "control_structures": "FOR:216,IF:221,ELSE:224,DO:228,IF:232,IF:238,IF:242,ELSE:250"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf",
   "buf_size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/harfbuzz/address/bc899650c7976df7bc62ed55da5268f1d10b9a43/ARVO-42508045/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_bc899650c797.cpg",
   "testcase_size": 526225
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 704,
   "loc_offset": 696,
   "loc_kind": "region",
   "dedup_token": "hb_bit_set_invertible_t::next(unsigned int*) const--hb_bit_set_invertible_t::intersects(unsigned int, unsigned int) const--hb_sparseset_t<hb_bit_set_invertible_",
   "region_size": 704
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 209,
    "type": "unsigned int"
   },
   "entity_name_cpg": "buf_size",
   "func_lines": [
    204,
    255
   ],
   "func_params": {
    "names": [
     "buffer",
     "start",
     "end",
     "buf",
     "buf_size",
     "buf_consumed",
     "flags"
    ],
    "types": [
     "hb_buffer_t*",
     "unsigned int",
     "unsigned int",
     "char*",
     "unsigned int",
     "unsigned int*",
     "hb_buffer_serialize_flags_t"
    ]
   },
   "guards": [
    {
     "code": "i < end",
     "line": 216
    },
    {
     "code": "i == end-1",
     "line": 238
    },
    {
     "code": "buf_size > l",
     "line": 242
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "buf_size > l",
     "name": "<operator>.greaterThan",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf_size",
    "l"
   ],
   "osv_id": "ARVO-42508045",
   "sites": [
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "b[1024]",
     "line": 218
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "hb_free_impl",
   "use_fn": "hb_bit_set_invertible_t::next(unsigned int*) const"
  }
 },
 {
  "osv_id": "ARVO-42508326",
  "project": "curl",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "CURLOPT_FTP_SSL_CCC",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "curl_dbg_realloc",
    "file": "/src/curl/lib/memdebug.c",
    "line": 260
   },
   "size_expr": null,
   "size_bytes": 76,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 292,
    "fn": "curl_dbg_free",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1612,
    "fn": "h2_session_send",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "h2_session_send",
    "file": "/src/curl/lib/http2.c",
    "line": 1612
   },
   "code": "CURLOPT(CURLOPT_FTP_SSL_CCC, CURLOPTTYPE_LONG, 154)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 76
   }
  },
  "context": {
   "fn": "h2_session_send",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/curl/address/5c55fe6df605b822bb637bdf0cf05b6812dcd732/ARVO-42508326/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_5c55fe6df605.cpg",
   "testcase_size": 342
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 76,
   "loc_offset": 4,
   "loc_kind": "region",
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned int), void const*, void const*, unsigned int)--memcmp--nghttp2_http_record_request_met",
   "region_size": 76
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "CURLOPT_FTP_SSL_CCC",
   "func_lines": [
    1063,
    -1
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "CURLOPT(CURLOPT_FTP_SSL_CCC, CURLOPTTYPE_LONG, 154)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "0 + 154",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "CURLOPT_FTP_SSL_CCC"
   ],
   "osv_id": "ARVO-42508326",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "curl_dbg_free",
   "use_fn": "h2_session_send"
  }
 },
 {
  "osv_id": "ARVO-42509881",
  "project": "fluent-bit",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 129
   },
   "size_expr": null,
   "size_bytes": 8200,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 111,
    "fn": "__interceptor_free",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 179,
    "fn": "cb_stdout_flush",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "cb_stdout_flush",
    "file": "/src/fluent-bit/plugins/out_stdout/stdout.c",
    "line": 179
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 24,
    "region_bytes": 8200
   }
  },
  "context": {
   "fn": "cb_stdout_flush",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/fluent-bit/address/8e310e6586ed66d1ac4e6880b2c89d2180b38916/ARVO-42509881/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_8e310e6586ed.cpg",
   "testcase_size": 218
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 8200,
   "loc_offset": 32,
   "loc_kind": "region",
   "dedup_token": "cb_stdout_flush--output_pre_cb_flush--",
   "region_size": 8200
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "__interceptor_free",
   "use_fn": "cb_stdout_flush"
  }
 },
 {
  "osv_id": "ARVO-42510333",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cur",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/tree.c",
    "line": 3691,
    "size": null,
    "type": "xmlNodePtr"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "xmlStaticCopyNode",
    "file": "/src/libxml2/tree.c",
    "line": 4247
   },
   "size_expr": null,
   "size_bytes": 120,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3704,
    "fn": "xmlFreeNodeList",
    "code": "(cur->children != NULL) &&",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 3751,
    "fn": "xmlFreeNodeList",
    "code": "xmlFree(cur)",
    "origin": "report:freed_by",
    "args": "cur"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlFreeNodeList",
    "file": "/src/libxml2/tree.c",
    "line": 3704
   },
   "code": "(cur->children != NULL) &&",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 120
   }
  },
  "context": {
   "fn": "xmlFreeNodeList",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "cur == NULL | cur->doc != NULL | cur->children != NULL",
   "guard_count": 8,
   "control_structures": "IF:3697,IF:3698,IF:3702,WHILE:3703,WHILE:3704,IF:3715,ELSE:3718,IF:3718,IF:3720,IF:3723,IF:3728,IF:3733"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlNodePtr",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "cur"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/f0ba4da18c17d3f1dd73007ce0888c978319e6f1/ARVO-42510333/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_f0ba4da18c17.cpg",
   "testcase_size": 233
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 120,
   "loc_offset": 24,
   "loc_kind": "region",
   "dedup_token": "xmlFreeNodeList--xmlXIncludeIncludeNode--xmlXIncludeDoProcess",
   "region_size": 120
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cur = cur->children",
     "line": 3709
    },
    {
     "code": "cur = next",
     "line": 3755
    },
    {
     "code": "cur = parent",
     "line": 3760
    },
    {
     "code": "cur->children = NULL",
     "line": 3761
    }
   ],
   "entity_decl": {
    "line": 3691,
    "type": "xmlNodePtr"
   },
   "entity_name_cpg": "cur",
   "func_lines": [
    3690,
    3764
   ],
   "func_params": {
    "names": [
     "cur"
    ],
    "types": [
     "xmlNodePtr"
    ]
   },
   "guards": [
    {
     "code": "cur == NULL",
     "line": 3697
    },
    {
     "code": "cur->type == XML_NAMESPACE_DECL",
     "line": 3698
    },
    {
     "code": "cur->doc != NULL",
     "line": 3702
    },
    {
     "code": "cur->children != NULL",
     "line": 3704
    },
    {
     "code": "cur->type != XML_DOCUMENT_NODE",
     "line": 3705
    },
    {
     "code": "cur->type != XML_HTML_DOCUMENT_NODE",
     "line": 3706
    },
    {
     "code": "cur->type != XML_DTD_NODE",
     "line": 3707
    },
    {
     "code": "cur->type != XML_ENTITY_REF_NODE",
     "line": 3708
    },
    {
     "code": "cur->type == XML_DOCUMENT_NODE",
     "line": 3715
    },
    {
     "code": "cur->type == XML_HTML_DOCUMENT_NODE",
     "line": 3716
    },
    {
     "code": "cur->type != XML_DTD_NODE",
     "line": 3718
    },
    {
     "code": "cur->type == XML_ELEMENT_NODE",
     "line": 3723
    },
    {
     "code": "cur->type == XML_XINCLUDE_START",
     "line": 3724
    },
    {
     "code": "cur->type == XML_XINCLUDE_END",
     "line": 3725
    },
    {
     "code": "cur->properties != NULL",
     "line": 3726
    },
    {
     "code": "cur->type != XML_ELEMENT_NODE",
     "line": 3728
    },
    {
     "code": "cur->type != XML_XINCLUDE_START",
     "line": 3729
    },
    {
     "code": "cur->type != XML_XINCLUDE_END",
     "line": 3730
    },
    {
     "code": "cur->type != XML_ENTITY_REF_NODE",
     "line": 3731
    },
    {
     "code": "cur->content != (xmlChar *) &(cur->properties)",
     "line": 3732
    },
    {
     "code": "xmlDictOwns(dict, (const xmlChar *)(cur->content)) == 0",
     "line": 3733
    },
    {
     "code": "cur->type == XML_ELEMENT_NODE",
     "line": 3735
    },
    {
     "code": "cur->type == XML_XINCLUDE_START",
     "line": 3736
    },
    {
     "code": "cur->type == XML_XINCLUDE_END",
     "line": 3737
    },
    {
     "code": "cur->nsDef != NULL",
     "line": 3738
    },
    {
     "code": "cur->name != NULL",
     "line": 3747
    },
    {
     "code": "cur->type != XML_TEXT_NODE",
     "line": 3748
    },
    {
     "code": "cur->type != XML_COMMENT_NODE",
     "line": 3749
    },
    {
     "code": "xmlDictOwns(dict, (const xmlChar *)(cur->name)) == 0",
     "line": 3750
    },
    {
     "code": "next != NULL",
     "line": 3754
    },
    {
     "code": "depth == 0",
     "line": 3757
    },
    {
     "code": "parent == NULL",
     "line": 3757
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "(cur->children != NULL) &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "(cur->children != NULL) &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "(cur->children != NULL) &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "(cur->children != NULL) &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "cur->children != NULL",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "cur->children",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cur",
    "NULL"
   ],
   "osv_id": "ARVO-42510333",
   "sites": [
    {
     "args": "(xmlNsPtr) cur",
     "callee": "xmlFreeNsList",
     "code": "xmlFreeNsList((xmlNsPtr) cur)",
     "line": 3699
    },
    {
     "args": "(xmlDocPtr) cur",
     "callee": "xmlFreeDoc",
     "code": "xmlFreeDoc((xmlDocPtr) cur)",
     "line": 3717
    },
    {
     "args": "cur->properties",
     "callee": "xmlFreePropList",
     "code": "xmlFreePropList(cur->properties)",
     "line": 3727
    },
    {
     "args": "cur->content",
     "callee": "DICT_FREE",
     "code": "DICT_FREE(cur->content)",
     "line": 3733
    },
    {
     "args": "(char *)(cur->content)",
     "callee": "xmlFree",
     "code": "xmlFree((char *)(cur->content))",
     "line": 3733
    },
    {
     "args": "cur->nsDef",
     "callee": "xmlFreeNsList",
     "code": "xmlFreeNsList(cur->nsDef)",
     "line": 3739
    },
    {
     "args": "cur->name",
     "callee": "DICT_FREE",
     "code": "DICT_FREE(cur->name)",
     "line": 3750
    },
    {
     "args": "(char *)(cur->name)",
     "callee": "xmlFree",
     "code": "xmlFree((char *)(cur->name))",
     "line": 3750
    },
    {
     "args": "cur",
     "callee": "xmlFree",
     "code": "xmlFree(cur)",
     "line": 3751
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": false,
   "free_fn": "xmlFreeNodeList",
   "use_fn": "xmlFreeNodeList"
  }
 },
 {
  "osv_id": "ARVO-42510346",
  "project": "libvips",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "alloc_small",
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "line": 312
   },
   "size_expr": null,
   "size_bytes": 16247,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 875,
    "fn": "read_jpeg_image",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 1043,
    "fn": "free_pool",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_jpeg_image",
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "line": 875
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": 16247
   }
  },
  "context": {
   "fn": "read_jpeg_image",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510346/report.log",
   "cpg": null,
   "testcase_size": 2048
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 16247,
   "loc_offset": 2760,
   "loc_kind": "region",
   "dedup_token": "decode_mcu--consume_data--jpeg_start_decompress",
   "region_size": 16247
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "free_pool",
   "use_fn": "read_jpeg_image"
  }
 },
 {
  "osv_id": "ARVO-42510349",
  "project": "libvips",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "alloc_small",
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "line": 312
   },
   "size_expr": null,
   "size_bytes": 16343,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 875,
    "fn": "read_jpeg_image",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 1043,
    "fn": "free_pool",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_jpeg_image",
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "line": 875
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": 16343
   }
  },
  "context": {
   "fn": "read_jpeg_image",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510349/report.log",
   "cpg": null,
   "testcase_size": 161
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 16343,
   "loc_offset": 3560,
   "loc_kind": "region",
   "dedup_token": "start_pass_phuff_decoder--start_input_pass--master_selection",
   "region_size": 16343
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "free_pool",
   "use_fn": "read_jpeg_image"
  }
 },
 {
  "osv_id": "ARVO-42510355",
  "project": "libvips",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "alloc_small",
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "line": 312
   },
   "size_expr": null,
   "size_bytes": 16343,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 875,
    "fn": "read_jpeg_image",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 1043,
    "fn": "free_pool",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_jpeg_image",
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "line": 875
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": 16343
   }
  },
  "context": {
   "fn": "read_jpeg_image",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510355/report.log",
   "cpg": null,
   "testcase_size": 1061
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 16343,
   "loc_offset": 3120,
   "loc_kind": "region",
   "dedup_token": "jpeg_fill_bit_buffer--jpeg_huff_decode--decode_mcu_slow",
   "region_size": 16343
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "free_pool",
   "use_fn": "read_jpeg_image"
  }
 },
 {
  "osv_id": "ARVO-42510367",
  "project": "libvips",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "alloc_small",
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "line": 312
   },
   "size_expr": null,
   "size_bytes": 16151,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 833,
    "fn": "read_jpeg_generate",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 1043,
    "fn": "free_pool",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_jpeg_generate",
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "line": 833
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 16151
   }
  },
  "context": {
   "fn": "read_jpeg_generate",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510367/report.log",
   "cpg": null,
   "testcase_size": 495
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 16151,
   "loc_offset": 2592,
   "loc_kind": "region",
   "dedup_token": "decode_mcu_slow--decode_mcu--decompress_onepass",
   "region_size": 16151
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "free_pool",
   "use_fn": "read_jpeg_generate"
  }
 },
 {
  "osv_id": "ARVO-42510442",
  "project": "libvips",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "alloc_large",
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "line": 385
   },
   "size_expr": null,
   "size_bytes": 65591,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 500,
    "fn": "read_jpeg_header",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 1030,
    "fn": "free_pool",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_jpeg_header",
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "line": 500
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": 65591
   }
  },
  "context": {
   "fn": "read_jpeg_header",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510442/report.log",
   "cpg": null,
   "testcase_size": 4
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 65591,
   "loc_offset": 102,
   "loc_kind": "region",
   "dedup_token": "save_marker--read_markers--consume_markers",
   "region_size": 65591
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "free_pool",
   "use_fn": "read_jpeg_header"
  }
 },
 {
  "osv_id": "ARVO-42511322",
  "project": "mruby",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/vm.c",
    "line": 99,
    "size": null,
    "type": "mrb_value*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": 1024,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 69,
    "fn": "mrb_default_allocf",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 101,
    "fn": "stack_copy",
    "code": "memcpy(dst, src, sizeof(mrb_value)*size) | sizeof(mrb_value)*size | sizeof(mrb_value)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "stack_copy",
    "file": "/src/mruby/src/vm.c",
    "line": 101
   },
   "code": "memcpy(dst, src, sizeof(mrb_value)*size) | sizeof(mrb_value)*size | sizeof(mrb_value)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 1024
   }
  },
  "context": {
   "fn": "stack_copy",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "mrb_value*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "dst",
   "src",
   "size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/mruby/address/23ce122fc2b1d29ee7241813bbab1c7e150e23ae/ARVO-42511322/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_23ce122fc2b1.cpg",
   "testcase_size": 7270
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 1024,
   "loc_offset": 976,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--stack_copy--mrb_funcall_with_block",
   "region_size": 1024
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 99,
    "type": "mrb_value*"
   },
   "entity_name_cpg": "dst",
   "func_lines": [
    98,
    102
   ],
   "func_params": {
    "names": [
     "dst",
     "src",
     "size"
    ],
    "types": [
     "mrb_value*",
     "mrb_value*",
     "size_t"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memcpy(dst, src, sizeof(mrb_value)*size)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "sizeof(mrb_value)*size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "sizeof(mrb_value)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "dst",
    "src",
    "mrb_value",
    "size"
   ],
   "osv_id": "ARVO-42511322",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 3,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "mrb_default_allocf",
   "use_fn": "stack_copy"
  }
 },
 {
  "osv_id": "ARVO-42511795",
  "project": "open62541",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "UA_ByteString_allocBuffer",
    "file": "/src/open62541/src/ua_types.c",
    "line": 187
   },
   "size_expr": null,
   "size_bytes": 65535,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 236,
    "fn": "UInt32_encodeBinary",
    "code": "",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 1064,
    "fn": "UA_Array_delete",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "UInt32_encodeBinary",
    "file": "/src/open62541/src/ua_types_encoding_binary.c",
    "line": 236
   },
   "code": "",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": 65535
   }
  },
  "context": {
   "fn": "UInt32_encodeBinary",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/92b1758a64c8adf945dd8a2306cf2d139963fb95/ARVO-42511795/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_92b1758a64c8.cpg",
   "testcase_size": 326
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 65535,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "UInt32_encodeBinary--UA_encodeBinaryInternal--UA_encodeBinary",
   "region_size": 65535
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    231,
    242
   ],
   "func_params": {
    "names": [
     "src",
     "_"
    ],
    "types": [
     "u32*",
     "UA_DataType*"
    ]
   },
   "guards": [
    {
     "code": "g_pos + sizeof(u32) > g_end",
     "line": 233
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42511795",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "UA_Array_delete",
   "use_fn": "UInt32_encodeBinary"
  }
 },
 {
  "osv_id": "ARVO-42513913",
  "project": "lcms",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "v",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmsnamed.c",
    "line": 574,
    "size": null,
    "type": "cmsNAMEDCOLORLIST*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": 88,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 121,
    "fn": "_cmsFreeDefaultFn",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 577,
    "fn": "cmsFreeNamedColorList",
    "code": "v ->List | _cmsFree(v ->ContextID, v ->List) | v ->ContextID | v ->List",
    "origin": "report:crash",
    "args": "v ->ContextID ;; v ->List"
   }
  ],
  "crash": {
   "site": {
    "fn": "cmsFreeNamedColorList",
    "file": "/src/lcms/src/cmsnamed.c",
    "line": 577
   },
   "code": "v ->List | _cmsFree(v ->ContextID, v ->List) | v ->ContextID | v ->List",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 88
   }
  },
  "context": {
   "fn": "cmsFreeNamedColorList",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "v == NULL",
   "guard_count": 1,
   "control_structures": "IF:576,IF:577"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cmsNAMEDCOLORLIST*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "v"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/lcms/address/a9796f61c682f5320ff572c888062ee34315b836/ARVO-42513913/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_a9796f61c682.cpg",
   "testcase_size": 448
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 88,
   "loc_offset": 80,
   "loc_kind": "region",
   "dedup_token": "cmsFreeNamedColorList--Type_NamedColor_Free--freeOneTag",
   "region_size": 88
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 574,
    "type": "cmsNAMEDCOLORLIST*"
   },
   "entity_name_cpg": "v",
   "func_lines": [
    574,
    579
   ],
   "func_params": {
    "names": [
     "v"
    ],
    "types": [
     "cmsNAMEDCOLORLIST*"
    ]
   },
   "guards": [
    {
     "code": "v == NULL",
     "line": 576
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "v ->List",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_cmsFree(v ->ContextID, v ->List)",
     "name": "_cmsFree",
     "nargs": 2
    },
    {
     "code": "v ->ContextID",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "v ->List",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "v"
   ],
   "osv_id": "ARVO-42513913",
   "sites": [
    {
     "args": "v ->ContextID ;; v ->List",
     "callee": "_cmsFree",
     "code": "_cmsFree(v ->ContextID, v ->List)",
     "line": 577
    },
    {
     "args": "v ->ContextID ;; v",
     "callee": "_cmsFree",
     "code": "_cmsFree(v ->ContextID, v)",
     "line": 578
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "_cmsFreeDefaultFn",
   "use_fn": "cmsFreeNamedColorList"
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