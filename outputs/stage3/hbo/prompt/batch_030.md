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
  "osv_id": "ARVO-42528947",
  "project": "libxml2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 4898,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "xmlFuzzRealloc",
    "file": "/src/libxslt/tests/fuzz/fuzz.c",
    "line": 437
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "size",
   "size_expr_cpg_callee": "xmlMallocAtomic"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 4981,
    "fn": "xmlParseCommentComplex",
    "code": "buf[len] = 0 | buf[len]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlParseCommentComplex",
    "file": "/src/libxml2/parser.c",
    "line": 4981
   },
   "code": "buf[len] = 0 | buf[len]",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlParseCommentComplex",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "buf == NULL | buf == NULL | len > maxLength",
   "guard_count": 3,
   "control_structures": "IF:4910,IF:4914,IF:4920,GOTO:4921,IF:4922,DO:4929,IF:4929,ELSE:4929,IF:4931,GOTO:4932,IF:4933,DO:4940"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ctxt",
   "buf",
   "len",
   "size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libxml2/address/b76d81dab3869f16a5c3506d9902526dff583b3e/ARVO-42528947/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b76d81dab386.cpg",
   "testcase_size": 23
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "xmlParseCommentComplex--xmlParseComment--xmlParseMisc"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf = (xmlChar *) xmlMallocAtomic(size)",
     "line": 4913
    },
    {
     "code": "buf = new_buf",
     "line": 4961
    },
    {
     "code": "buf[len++] = q",
     "line": 4964
    },
    {
     "code": "buf[len] = 0",
     "line": 4981
    }
   ],
   "entity_decl": {
    "line": 4898,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    4897,
    5011
   ],
   "func_params": {
    "names": [
     "ctxt",
     "buf",
     "len",
     "size"
    ],
    "types": [
     "xmlParserCtxtPtr",
     "xmlChar*",
     "size_t",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "buf == NULL",
     "line": 4910
    },
    {
     "code": "buf == NULL",
     "line": 4914
    },
    {
     "code": "q == 0",
     "line": 4920
    },
    {
     "code": "*(ctxt->input->cur) == '\\n'",
     "line": 4929
    },
    {
     "code": "r == 0",
     "line": 4931
    },
    {
     "code": "*(ctxt->input->cur) == '\\n'",
     "line": 4940
    },
    {
     "code": "cur == 0",
     "line": 4942
    },
    {
     "code": "cur != '>'",
     "line": 4945
    },
    {
     "code": "r != '-'",
     "line": 4946
    },
    {
     "code": "q != '-'",
     "line": 4946
    },
    {
     "code": "r == '-'",
     "line": 4947
    },
    {
     "code": "q == '-'",
     "line": 4947
    },
    {
     "code": "new_buf == NULL",
     "line": 4956
    },
    {
     "code": "ql == 1",
     "line": 4964
    },
    {
     "code": "len > maxLength",
     "line": 4965
    },
    {
     "code": "*(ctxt->input->cur) == '\\n'",
     "line": 4977
    },
    {
     "code": "ctxt->instate == XML_PARSER_EOF",
     "line": 4982
    },
    {
     "code": "cur == 0",
     "line": 4986
    },
    {
     "code": "inputid != ctxt->input->id",
     "line": 4994
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5000
    },
    {
     "code": "ctxt->sax->comment != NULL",
     "line": 5000
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "buf[len] = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "buf[len]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "len"
   ],
   "osv_id": "ARVO-42528947",
   "sites": [
    {
     "args": "size",
     "callee": "xmlMallocAtomic",
     "code": "xmlMallocAtomic(size)",
     "line": 4913
    },
    {
     "args": "buf",
     "callee": "xmlFree",
     "code": "xmlFree (buf)",
     "line": 4926
    },
    {
     "args": "buf",
     "callee": "xmlFree",
     "code": "xmlFree (buf)",
     "line": 4937
    },
    {
     "args": "buf ;; new_size",
     "callee": "xmlRealloc",
     "code": "xmlRealloc(buf, new_size)",
     "line": 4955
    },
    {
     "args": "buf",
     "callee": "xmlFree",
     "code": "xmlFree (buf)",
     "line": 4957
    },
    {
     "args": "buf",
     "callee": "xmlFree",
     "code": "xmlFree (buf)",
     "line": 4968
    },
    {
     "args": "buf",
     "callee": "xmlFree",
     "code": "xmlFree(buf)",
     "line": 4983
    },
    {
     "args": "buf",
     "callee": "xmlFree",
     "code": "xmlFree(buf)",
     "line": 5004
    },
    {
     "args": "buf",
     "callee": "xmlFree",
     "code": "xmlFree(buf)",
     "line": 5009
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlParseCommentComplex"
  }
 },
 {
  "osv_id": "ARVO-42528951",
  "project": "libxml2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "out",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/parserInternals.c",
    "line": 1071,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "xmlFuzzRealloc",
    "file": "/src/libxml2/fuzz/fuzz.c",
    "line": 99
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1095,
    "fn": "xmlCopyCharMultiByte",
    "code": "*out++= ((val >> bits) & 0x3F) | 0x80 | *out++ | out++ | ((val >> bits) & 0x3F) | 0x80",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlCopyCharMultiByte",
    "file": "/src/libxml2/parserInternals.c",
    "line": 1095
   },
   "code": "*out++= ((val >> bits) & 0x3F) | 0x80 | *out++ | out++ | ((val >> bits) & 0x3F) | 0x80",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlCopyCharMultiByte",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "out == NULL | val < 0 | val >= 0x80",
   "guard_count": 7,
   "control_structures": "IF:1072,IF:1082,IF:1085,ELSE:1086,IF:1086,ELSE:1087,IF:1087,ELSE:1088,FOR:1094"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "out",
   "val"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libxml2/address/b76d81dab3869f16a5c3506d9902526dff583b3e/ARVO-42528951/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b76d81dab386.cpg",
   "testcase_size": 52
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "xmlCopyCharMultiByte--xmlParseCommentComplex--xmlParseComment"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1071,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "out",
   "func_lines": [
    1070,
    1100
   ],
   "func_params": {
    "names": [
     "out",
     "val"
    ],
    "types": [
     "xmlChar*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "out == NULL",
     "line": 1072
    },
    {
     "code": "val < 0",
     "line": 1072
    },
    {
     "code": "val <   0x800",
     "line": 1085
    },
    {
     "code": "val < 0x10000",
     "line": 1086
    },
    {
     "code": "val < 0x110000",
     "line": 1087
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "*out++= ((val >> bits) & 0x3F) ",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "*out++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "out++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "((val >> bits) & 0x3F) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(val >> bits) & 0x3F",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "val >> bits",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out",
    "val",
    "bits"
   ],
   "osv_id": "ARVO-42528951",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlCopyCharMultiByte"
  }
 },
 {
  "osv_id": "ARVO-42529037",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "x",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 418,
    "size": null,
    "type": "float"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "iasecc_parse_get_tlv",
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 430
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 433,
    "fn": "iasecc_parse_get_tlv",
    "code": "x <= 0.75",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "iasecc_parse_get_tlv",
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 433
   },
   "code": "x <= 0.75",
   "access": {
    "dir": "READ",
    "width": 32,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "list_findpos",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "x <= 0.25 | x < 0.5 | x <= 0.75",
   "guard_count": 3,
   "control_structures": "IF:421,IF:424,IF:427,FOR:429,ELSE:430,IF:430,FOR:432,ELSE:433,IF:433,FOR:435,ELSE:436,FOR:438"
  },
  "call_chain": [],
  "types": {
   "entity_type": "float",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "l",
   "posstart"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/fa709de8dc5045f390f321cb65c9c73c36d52dd0/ARVO-42529037/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_fa709de8dc50.cpg",
   "testcase_size": 96
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
   "dedup_token": "__asan_memcpy--iasecc_parse_get_tlv--iasecc_parse_docp"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "x = l->numels ? (float)(posstart+1) / l->numels : 0",
     "line": 426
    }
   ],
   "entity_decl": {
    "line": 418,
    "type": "float"
   },
   "entity_name_cpg": "x",
   "func_lines": [
    416,
    442
   ],
   "func_params": {
    "names": [
     "l",
     "posstart"
    ],
    "types": [
     "list_t*simclist_restrict",
     "int"
    ]
   },
   "guards": [
    {
     "code": "l->head_sentinel == NULL",
     "line": 421
    },
    {
     "code": "l->tail_sentinel == NULL",
     "line": 421
    },
    {
     "code": "posstart < -1",
     "line": 424
    },
    {
     "code": "posstart > (int)l->numels",
     "line": 424
    },
    {
     "code": "i < posstart",
     "line": 429
    },
    {
     "code": "x < 0.5",
     "line": 430
    },
    {
     "code": "i > posstart",
     "line": 432
    },
    {
     "code": "i < posstart",
     "line": 435
    },
    {
     "code": "i > posstart",
     "line": 438
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "x <= 0.75",
     "name": "<operator>.lessEqualsThan",
     "nargs": 2
    }
   ],
   "line_ids": [
    "x"
   ],
   "osv_id": "ARVO-42529037",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "iasecc_parse_get_tlv"
  }
 },
 {
  "osv_id": "ARVO-42529054",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "str",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "line": 2786,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc_wrapper",
    "file": "/src/ndpi/fuzz/fuzz_common_code.c",
    "line": 16
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2801,
    "fn": "ndpi_vsnprintf",
    "code": "vsnprintf(str, size, format, va_args)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_vsnprintf",
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "line": 2801
   },
   "code": "vsnprintf(str, size, format, va_args)",
   "access": {
    "dir": "WRITE",
    "width": 11,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_vsnprintf",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "str",
   "size",
   "format",
   "va_args"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/a76b9d151f58e000980abffc29b0192b08c5bb4e/ARVO-42529054/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_a76b9d151f58.cpg",
   "testcase_size": 12
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
   "dedup_token": "__interceptor_vsnprintf--ndpi_vsnprintf--ndpi_snprintf"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 2786,
    "type": "char*"
   },
   "entity_name_cpg": "str",
   "func_lines": [
    2786,
    2803
   ],
   "func_params": {
    "names": [
     "str",
     "size",
     "format",
     "va_args"
    ],
    "types": [
     "char*",
     "size_t",
     "char*",
     "va_list"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "vsnprintf(str, size, format, va_args)",
     "name": "vsnprintf",
     "nargs": 4
    }
   ],
   "line_ids": [
    "str",
    "size",
    "format",
    "va_args"
   ],
   "osv_id": "ARVO-42529054",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_vsnprintf"
  }
 },
 {
  "osv_id": "ARVO-42529370",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "obj",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/decode.c",
    "line": 6502,
    "size": null,
    "type": "Dwg_Object*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: e678fe54a5d2c2092f8e47eb0b33105e380f7340)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "REFS_PER_REALLOC ;; sizeof (Dwg_Object)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc (REFS_PER_REALLOC, sizeof (Dwg_Object))",
    "fn": "decode_preR13_entities",
    "kind": "calloc",
    "line": 6508,
    "origin": "cpg",
    "args": "REFS_PER_REALLOC ;; sizeof (Dwg_Object)"
   },
   {
    "code": "realloc (",
    "fn": "decode_preR13_entities",
    "kind": "realloc",
    "line": 6513,
    "origin": "cpg"
   },
   {
    "code": "strdup (_hdr->name)",
    "fn": "decode_preR13_entities",
    "kind": "strdup",
    "line": 6647,
    "origin": "cpg",
    "args": "_hdr->name"
   },
   {
    "code": "calloc (offset, 1)",
    "fn": "decode_preR13_entities",
    "kind": "calloc",
    "line": 6895,
    "origin": "cpg",
    "args": "offset ;; 1"
   },
   {
    "kind": "unknown",
    "line": 6898,
    "fn": "decode_preR13_entities",
    "code": "memcpy (obj->unknown_rest, &dat->chain[dat->byte],",
    "origin": "report:crash"
   },
   {
    "code": "realloc(_hdr->entities, (_hdr->num_owned + 1) * sizeof (BITCODE_H))",
    "fn": "decode_preR13_entities",
    "kind": "realloc",
    "line": 6959,
    "origin": "cpg",
    "args": "_hdr->entities ;; (_hdr->num_owned + 1) * sizeof (BITCODE_H)"
   }
  ],
  "crash": {
   "site": {
    "fn": "decode_preR13_entities",
    "file": "/src/libredwg/src/decode.c",
    "line": 6898
   },
   "code": "memcpy (obj->unknown_rest, &dat->chain[dat->byte],",
   "access": {
    "dir": "READ",
    "width": 8406,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "decode_preR13_entities",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:6434,IF:6437,IF:6438,IF:6441,IF:6446,IF:6449,IF:6456,IF:6460,IF:6462,IF:6462,IF:6463,IF:6465"
  },
  "call_chain": [],
  "types": {
   "entity_type": "Dwg_Object*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "start",
   "end",
   "size",
   "dat",
   "dwg"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/2584efe46a41eae2c41f2d936286c7785093eb04/ARVO-42529370/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_2584efe46a41.cpg",
   "testcase_size": 496
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
   "dedup_token": "__asan_memcpy--memcpy--decode_preR13_entities"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "obj = &dwg->object[num]",
     "line": 6524
    },
    {
     "code": "obj->index = num",
     "line": 6527
    },
    {
     "code": "obj->parent = dwg",
     "line": 6528
    },
    {
     "code": "obj->address = dat->byte",
     "line": 6529
    },
    {
     "code": "obj->supertype = DWG_SUPERTYPE_ENTITY",
     "line": 6530
    },
    {
     "code": "obj->type = bit_read_RS (dat)",
     "line": 6535
    },
    {
     "code": "obj->type = bit_read_RC (dat)",
     "line": 6549
    },
    {
     "code": "obj->handle.value = dwg_next_handle (dwg)",
     "line": 6629
    },
    {
     "code": "obj->tio.entity->tio.BLOCK->name",
     "line": 6646
    },
    {
     "code": "obj->size = (dat->byte - oldpos) & 0xFFFFFFFF",
     "line": 6875
    },
    {
     "code": "obj->num_unknown_rest = 8 * offset",
     "line": 6894
    },
    {
     "code": "obj->unknown_rest = (BITCODE_TF)calloc (offset, 1)",
     "line": 6895
    },
    {
     "code": "obj->num_unknown_rest = 0",
     "line": 6905
    },
    {
     "code": "obj->num_unknown_rest = 8 * offset",
     "line": 6923
    },
    {
     "code": "obj->unknown_rest = bit_read_TF (dat, offset)",
     "line": 6924
    },
    {
     "code": "obj->num_unknown_rest = 0",
     "line": 6932
    },
    {
     "code": "obj->handle.value = dwg_next_handle (dwg)",
     "line": 6952
    },
    {
     "code": "obj->tio.entity->ownerhandle",
     "line": 6960
    },
    {
     "code": "obj->tio.entity->ownerhandle->r11_idx = block_idx",
     "line": 6962
    }
   ],
   "entity_decl": {
    "line": 6502,
    "type": "Dwg_Object*"
   },
   "entity_name_cpg": "obj",
   "func_lines": [
    6417,
    7007
   ],
   "func_params": {
    "names": [
     "start",
     "end",
     "num_entities",
     "size",
     "dat",
     "dwg",
     "entity_section"
    ],
    "types": [
     "BITCODE_RL",
     "BITCODE_RL",
     "unsigned",
     "BITCODE_RL",
     "Bit_Chain*restrict",
     "Dwg_Data*restrict",
     "EntitySectionIndexR11"
    ]
   },
   "guards": [
    {
     "code": "entity_section != BLOCKS_SECTION_INDEX",
     "line": 6438
    },
    {
     "code": "hdr->fixedtype == DWG_TYPE_BLOCK_HEADER",
     "line": 6441
    },
    {
     "code": "start != end",
     "line": 6460
    },
    {
     "code": "real_start > 0",
     "line": 6460
    },
    {
     "code": "(BITCODE_RL)dat->byte != real_start",
     "line": 6460
    },
    {
     "code": "(BITCODE_RL)dat->byte < real_start",
     "line": 6463
    },
    {
     "code": "real_start > dat->size",
     "line": 6465
    },
    {
     "code": "dat->byte < (size_t)(dat->size)",
     "line": 6467
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6467
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6467
    },
    {
     "code": "dat->byte < (size_t)(real_start)",
     "line": 6471
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6471
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6471
    },
    {
     "code": "end > start",
     "line": 6496
    },
    {
     "code": "start == dat->byte",
     "line": 6496
    },
    {
     "code": "dat->byte < oldpos + size",
     "line": 6500
    },
    {
     "code": "dat->from_version < R_2_0b",
     "line": 6533
    },
    {
     "code": "obj->type > 127",
     "line": 6537
    },
    {
     "code": "obj->type > 127",
     "line": 6551
    },
    {
     "code": "dat->version > R_2_22",
     "line": 6601
    },
    {
     "code": "entity_section == BLOCKS_SECTION_INDEX",
     "line": 6608
    },
    {
     "code": "i < dwg->num_objects",
     "line": 6610
    },
    {
     "code": "o->fixedtype == DWG_TYPE_BLOCK_HEADER",
     "line": 6613
    },
    {
     "code": "cur_offset",
     "line": 6615
    },
    {
     "code": "obj->fixedtype == DWG_TYPE_BLOCK",
     "line": 6658
    },
    {
     "code": "dat->from_version < R_11",
     "line": 6724
    },
    {
     "code": "dat->from_version < R_11",
     "line": 6789
    },
    {
     "code": "dat->size < dat->byte",
     "line": 6865
    },
    {
     "code": "0UL > 0",
     "line": 6865
    },
    {
     "code": "dat->byte + rs > 0UL",
     "line": 6865
    },
    {
     "code": "dat->byte + rs > dat->size",
     "line": 6865
    },
    {
     "code": "_i < (unsigned)(rs)",
     "line": 6865
    },
    {
     "code": "_i < (unsigned)(rs)",
     "line": 6865
    },
    {
     "code": "bb != 3",
     "line": 6865
    },
    {
     "code": "dat->from_version < R_2_0b",
     "line": 6873
    },
    {
     "code": "num + 1 > dwg->num_objects",
     "line": 6876
    },
    {
     "code": "obj->type != DWG_TYPE_JUMP_r11",
     "line": 6879
    },
    {
     "code": "dat->from_version < R_11",
     "line": 6883
    },
    {
     "code": "obj->address + obj->size != dat->byte",
     "line": 6885
    },
    {
     "code": "obj->address + obj->size > dat->byte",
     "line": 6889
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6900
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6900
    },
    {
     "code": "obj->size > 2",
     "line": 6908
    },
    {
     "code": "obj->address + obj->size != dat->byte + 2",
     "line": 6914
    },
    {
     "code": "obj->address + obj->size > dat->byte + 2",
     "line": 6918
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6927
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6927
    },
    {
     "code": "start > 60",
     "line": 6935
    },
    {
     "code": "obj->supertype == DWG_SUPERTYPE_ENTITY",
     "line": 6944
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_UNUSED",
     "line": 6945
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_JUMP",
     "line": 6946
    },
    {
     "code": "obj->type != DWG_TYPE_VERTEX_r11",
     "line": 6947
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_SEQEND",
     "line": 6948
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_BLOCK",
     "line": 6958
    },
    {
     "code": "dat->byte < oldpos + size",
     "line": 6967
    },
    {
     "code": "(BITCODE_RL)dat->byte != end",
     "line": 6969
    },
    {
     "code": "(BITCODE_RL)dat->byte != end",
     "line": 6976
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "memcpy (obj->unknown_rest, &dat->chain[dat->byte],",
     "name": "memcpy",
     "nargs": null
    },
    {
     "code": "obj->unknown_rest",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "&dat->chain[dat->byte]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "dat->chain[dat->byte]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "dat->chain",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dat->byte",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "obj",
    "dat"
   ],
   "osv_id": "ARVO-42529370",
   "sites": [
    {
     "args": "unknown",
     "callee": "free",
     "code": "free(unknown)",
     "line": 6467
    },
    {
     "args": "unknown",
     "callee": "free",
     "code": "free(unknown)",
     "line": 6471
    },
    {
     "args": "REFS_PER_REALLOC ;; sizeof (Dwg_Object)",
     "callee": "calloc",
     "code": "calloc (REFS_PER_REALLOC, sizeof (Dwg_Object))",
     "line": 6508
    },
    {
     "args": "",
     "callee": "REFS_PER_REALLOC",
     "code": "REFS_PER_REALLOC",
     "line": 6508
    },
    {
     "args": null,
     "callee": "realloc",
     "code": "realloc (",
     "line": 6513
    },
    {
     "args": "_hdr->name",
     "callee": "strdup",
     "code": "strdup (_hdr->name)",
     "line": 6647
    },
    {
     "args": "tmp",
     "callee": "free",
     "code": "free(tmp)",
     "line": 6865
    },
    {
     "args": "offset ;; 1",
     "callee": "calloc",
     "code": "calloc (offset, 1)",
     "line": 6895
    },
    {
     "args": "_hdr->entities ;; (_hdr->num_owned + 1) * sizeof (BITCODE_H)",
     "callee": "realloc",
     "code": "realloc(_hdr->entities, (_hdr->num_owned + 1) * sizeof (BITCODE_H))",
     "line": 6959
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "decode_preR13_entities"
  }
 },
 {
  "osv_id": "ARVO-42529392",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ref",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/dwg.spec",
    "line": 4375,
    "size": null,
    "type": "Dwg_Object_Ref*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "decode_preR13_section",
    "file": "/src/libredwg/src/decode_r11.c",
    "line": 491
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "1 ;; sizeof (Dwg_Object_Ref)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc (1, sizeof (Dwg_Object_Ref))",
    "fn": "dwg_json_VPORT_private",
    "kind": "calloc",
    "line": 4375,
    "origin": "cpg",
    "args": "1 ;; sizeof (Dwg_Object_Ref)"
   },
   {
    "code": "free (ref)",
    "fn": "dwg_json_VPORT_private",
    "kind": "free",
    "line": 4383,
    "origin": "cpg",
    "args": "ref"
   },
   {
    "code": "free (ref)",
    "fn": "dwg_json_VPORT_private",
    "kind": "free",
    "line": 4393,
    "origin": "cpg",
    "args": "ref"
   },
   {
    "code": "free (ref)",
    "fn": "dwg_json_VPORT_private",
    "kind": "free",
    "line": 4401,
    "origin": "cpg",
    "args": "ref"
   },
   {
    "kind": "unknown",
    "line": 4433,
    "fn": "dwg_json_VPORT_private",
    "code": "ref->handleref.code | ref->handleref",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dwg_json_VPORT_private",
    "file": "/src/libredwg/src/dwg.spec",
    "line": 4433
   },
   "code": "ref->handleref.code | ref->handleref",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dwg_decode_handleref",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:4376,IF:4378,IF:4378,IF:4381,IF:4389,IF:4391,ELSE:4397,IF:4397,IF:4399,IF:4411,IF:4413,IF:4419"
  },
  "call_chain": [],
  "types": {
   "entity_type": "Dwg_Object_Ref*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dat",
   "obj"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/2584efe46a41eae2c41f2d936286c7785093eb04/ARVO-42529392/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_2584efe46a41.cpg",
   "testcase_size": 20551
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
  "free_related": {
   "free_sites_in_func": [
    4383,
    4393,
    4401
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "dwg_json_VPORT_private--dwg_json_VPORT--dwg_json_object"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*ref = (Dwg_Object_Ref *)calloc (1, sizeof (Dwg_Object_Ref))",
     "line": 4375
    },
    {
     "code": "ref->absolute_ref = 0",
     "line": 4404
    },
    {
     "code": "ref->obj = NULL",
     "line": 4405
    },
    {
     "code": "ref->absolute_ref = ref->handleref.value",
     "line": 4415
    },
    {
     "code": "ref->obj = NULL",
     "line": 4416
    },
    {
     "code": "ref->obj = NULL",
     "line": 4423
    },
    {
     "code": "ref->absolute_ref = (obj->handle.value + 1)",
     "line": 4436
    },
    {
     "code": "ref->absolute_ref = (obj->handle.value - 1)",
     "line": 4439
    },
    {
     "code": "ref->absolute_ref = (obj->handle.value + ref->handleref.value)",
     "line": 4442
    },
    {
     "code": "ref->absolute_ref = (obj->handle.value - ref->handleref.value)",
     "line": 4445
    },
    {
     "code": "ref->absolute_ref = obj->handle.value",
     "line": 4448
    },
    {
     "code": "ref->absolute_ref = ref->handleref.value",
     "line": 4454
    },
    {
     "code": "ref->absolute_ref = ref->handleref.value",
     "line": 4457
    },
    {
     "code": "ref->absolute_ref = 0",
     "line": 4462
    },
    {
     "code": "ref->obj = NULL",
     "line": 4463
    }
   ],
   "entity_decl": {
    "line": 4375,
    "type": "Dwg_Object_Ref*"
   },
   "entity_name_cpg": "ref",
   "func_lines": [
    4370,
    4468
   ],
   "func_params": {
    "names": [
     "dat",
     "obj",
     "dwg"
    ],
    "types": [
     "Bit_Chain*restrict",
     "Dwg_Object*restrict",
     "Dwg_Data*restrict"
    ]
   },
   "guards": [
    {
     "code": "ref->handleref.code > 5",
     "line": 4389
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "ref->handleref.code",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ref->handleref",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ref"
   ],
   "osv_id": "ARVO-42529392",
   "sites": [
    {
     "args": "1 ;; sizeof (Dwg_Object_Ref)",
     "callee": "calloc",
     "code": "calloc (1, sizeof (Dwg_Object_Ref))",
     "line": 4375
    },
    {
     "args": "ref",
     "callee": "free",
     "code": "free (ref)",
     "line": 4383
    },
    {
     "args": "ref",
     "callee": "free",
     "code": "free (ref)",
     "line": 4393
    },
    {
     "args": "ref",
     "callee": "free",
     "code": "free (ref)",
     "line": 4401
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "dwg_json_VPORT_private",
   "use_fn": "dwg_json_VPORT_private"
  }
 },
 {
  "osv_id": "ARVO-42529484",
  "project": "matio",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 231
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3162,
    "fn": "Mat_VarReadNextInfo73",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_VarReadNextInfo73",
    "file": "/src/matio/src/mat73.c",
    "line": 3162
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 169,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_VarReadNextInfo73",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/77d8c989bc802b81354d86056386a762ef1fcfa1/ARVO-42529484/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_77d8c989bc80.cpg",
   "testcase_size": 14157
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
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "strdup--H5MM_xstrdup--H5G__ent_to_link"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    44,
    44
   ],
   "func_params": {
    "names": [
     "mat",
     "pred",
     "user_data"
    ],
    "types": [
     "mat_t*",
     "mat_iter_pred_t",
     "void*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42529484",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_VarReadNextInfo73"
  }
 },
 {
  "osv_id": "ARVO-42529507",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "card",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 381,
    "size": null,
    "type": "sc_card_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "iasecc_parse_get_tlv",
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 430
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 392,
    "fn": "iasecc_parse_size",
    "code": "LOG_TEST_RET(card->ctx, r, \"APDU transmit failed\") | card->ctx | int | _ret < 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "iasecc_parse_size",
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 392
   },
   "code": "LOG_TEST_RET(card->ctx, r, \"APDU transmit failed\") | card->ctx | int | _ret < 0",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "akis_get_data",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "_ret < 0",
   "guard_count": 1,
   "control_structures": "DO:392,IF:392"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_card_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "card",
   "buf",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/fa709de8dc5045f390f321cb65c9c73c36d52dd0/ARVO-42529507/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_fa709de8dc50.cpg",
   "testcase_size": 82
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
   "dedup_token": "iasecc_parse_size--iasecc_parse_get_tlv--iasecc_parse_docp"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 381,
    "type": "sc_card_t*"
   },
   "entity_name_cpg": "card",
   "func_lines": [
    380,
    395
   ],
   "func_params": {
    "names": [
     "card",
     "dataid",
     "buf",
     "len"
    ],
    "types": [
     "sc_card_t*",
     "unsigned int",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "_ret < 0",
     "line": 392
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "LOG_TEST_RET(card->ctx, r, \"APDU transmit failed\")",
     "name": "LOG_TEST_RET",
     "nargs": 2
    },
    {
     "code": "card->ctx",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "int",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "_ret < 0",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "sc_do_log_color((card->ctx), SC_LOG_DEBUG_NORMAL, \"/tmp/arvo_work/42529909/src/opensc/src/libopensc/card-akis.c\", 392, NULL, 0x0001, \"%s: %d (%s)\\n\", ((\"APDU transmit failed\")), _ret, sc_strerror(_ret",
     "name": "sc_do_log_color",
     "nargs": 10
    },
    {
     "code": "card->ctx",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "sc_strerror(_ret)",
     "name": "sc_strerror",
     "nargs": 1
    }
   ],
   "line_ids": [
    "card",
    "r",
    "_ret",
    "SC_LOG_DEBUG_NORMAL",
    "NULL"
   ],
   "osv_id": "ARVO-42529507",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "iasecc_parse_size"
  }
 },
 {
  "osv_id": "ARVO-42529681",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2856,
    "type": "uint8_t",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 237
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2859,
    "fn": "H5F_addr_decode_len",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5F_addr_decode_len",
    "file": "/src/hdf5/src/H5Fint.c",
    "line": 2859
   },
   "code": "c = *(*pp)++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5F_addr_decode_len",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42529681/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "testcase_size": 6032
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "H5F_addr_decode_len--H5F_addr_decode--H5O__shared_decode"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = *(*pp)++",
     "line": 2859
    }
   ],
   "entity_decl": {
    "line": 2856,
    "type": "uint8_t"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    2838,
    2885
   ],
   "func_params": {
    "names": [
     "addr_len",
     "pp",
     "addr_p"
    ],
    "types": [
     "size_t",
     "uint8_t**",
     "haddr_t*"
    ]
   },
   "guards": [
    {
     "code": "'_' != ((const char *)__func__)[2]",
     "line": 2845
    },
    {
     "code": "'_' != ((const char *)__func__)[3]",
     "line": 2845
    },
    {
     "code": "'_' == ((const char *)__func__)[4]",
     "line": 2845
    },
    {
     "code": "u < addr_len",
     "line": 2855
    },
    {
     "code": "c != 0xff",
     "line": 2862
    },
    {
     "code": "u < sizeof(*addr_p)",
     "line": 2865
    },
    {
     "code": "0 == **pp",
     "line": 2875
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "c = *(*pp)++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*(*pp)++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(*pp)++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "*pp",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "c",
    "pp"
   ],
   "osv_id": "ARVO-42529681",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5F_addr_decode_len"
  }
 },
 {
  "osv_id": "ARVO-42529717",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "obj",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/decode.c",
    "line": 6502,
    "size": null,
    "type": "Dwg_Object*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: e678fe54a5d2c2092f8e47eb0b33105e380f7340)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "REFS_PER_REALLOC ;; sizeof (Dwg_Object)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc (REFS_PER_REALLOC, sizeof (Dwg_Object))",
    "fn": "decode_preR13_entities",
    "kind": "calloc",
    "line": 6508,
    "origin": "cpg",
    "args": "REFS_PER_REALLOC ;; sizeof (Dwg_Object)"
   },
   {
    "code": "realloc (",
    "fn": "decode_preR13_entities",
    "kind": "realloc",
    "line": 6513,
    "origin": "cpg"
   },
   {
    "code": "strdup (_hdr->name)",
    "fn": "decode_preR13_entities",
    "kind": "strdup",
    "line": 6647,
    "origin": "cpg",
    "args": "_hdr->name"
   },
   {
    "code": "calloc (offset, 1)",
    "fn": "decode_preR13_entities",
    "kind": "calloc",
    "line": 6895,
    "origin": "cpg",
    "args": "offset ;; 1"
   },
   {
    "kind": "unknown",
    "line": 6898,
    "fn": "decode_preR13_entities",
    "code": "memcpy (obj->unknown_rest, &dat->chain[dat->byte],",
    "origin": "report:crash"
   },
   {
    "code": "realloc(_hdr->entities, (_hdr->num_owned + 1) * sizeof (BITCODE_H))",
    "fn": "decode_preR13_entities",
    "kind": "realloc",
    "line": 6959,
    "origin": "cpg",
    "args": "_hdr->entities ;; (_hdr->num_owned + 1) * sizeof (BITCODE_H)"
   }
  ],
  "crash": {
   "site": {
    "fn": "decode_preR13_entities",
    "file": "/src/libredwg/src/decode.c",
    "line": 6898
   },
   "code": "memcpy (obj->unknown_rest, &dat->chain[dat->byte],",
   "access": {
    "dir": "READ",
    "width": 17,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "decode_preR13_entities",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:6434,IF:6437,IF:6438,IF:6441,IF:6446,IF:6449,IF:6456,IF:6460,IF:6462,IF:6462,IF:6463,IF:6465"
  },
  "call_chain": [],
  "types": {
   "entity_type": "Dwg_Object*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "start",
   "end",
   "size",
   "dat",
   "dwg"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/2584efe46a41eae2c41f2d936286c7785093eb04/ARVO-42529717/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_2584efe46a41.cpg",
   "testcase_size": 496
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
   "dedup_token": "__asan_memcpy--memcpy--decode_preR13_entities"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "obj = &dwg->object[num]",
     "line": 6524
    },
    {
     "code": "obj->index = num",
     "line": 6527
    },
    {
     "code": "obj->parent = dwg",
     "line": 6528
    },
    {
     "code": "obj->address = dat->byte",
     "line": 6529
    },
    {
     "code": "obj->supertype = DWG_SUPERTYPE_ENTITY",
     "line": 6530
    },
    {
     "code": "obj->type = bit_read_RS (dat)",
     "line": 6535
    },
    {
     "code": "obj->type = bit_read_RC (dat)",
     "line": 6549
    },
    {
     "code": "obj->handle.value = dwg_next_handle (dwg)",
     "line": 6629
    },
    {
     "code": "obj->tio.entity->tio.BLOCK->name",
     "line": 6646
    },
    {
     "code": "obj->size = (dat->byte - oldpos) & 0xFFFFFFFF",
     "line": 6875
    },
    {
     "code": "obj->num_unknown_rest = 8 * offset",
     "line": 6894
    },
    {
     "code": "obj->unknown_rest = (BITCODE_TF)calloc (offset, 1)",
     "line": 6895
    },
    {
     "code": "obj->num_unknown_rest = 0",
     "line": 6905
    },
    {
     "code": "obj->num_unknown_rest = 8 * offset",
     "line": 6923
    },
    {
     "code": "obj->unknown_rest = bit_read_TF (dat, offset)",
     "line": 6924
    },
    {
     "code": "obj->num_unknown_rest = 0",
     "line": 6932
    },
    {
     "code": "obj->handle.value = dwg_next_handle (dwg)",
     "line": 6952
    },
    {
     "code": "obj->tio.entity->ownerhandle",
     "line": 6960
    },
    {
     "code": "obj->tio.entity->ownerhandle->r11_idx = block_idx",
     "line": 6962
    }
   ],
   "entity_decl": {
    "line": 6502,
    "type": "Dwg_Object*"
   },
   "entity_name_cpg": "obj",
   "func_lines": [
    6417,
    7007
   ],
   "func_params": {
    "names": [
     "start",
     "end",
     "num_entities",
     "size",
     "dat",
     "dwg",
     "entity_section"
    ],
    "types": [
     "BITCODE_RL",
     "BITCODE_RL",
     "unsigned",
     "BITCODE_RL",
     "Bit_Chain*restrict",
     "Dwg_Data*restrict",
     "EntitySectionIndexR11"
    ]
   },
   "guards": [
    {
     "code": "entity_section != BLOCKS_SECTION_INDEX",
     "line": 6438
    },
    {
     "code": "hdr->fixedtype == DWG_TYPE_BLOCK_HEADER",
     "line": 6441
    },
    {
     "code": "start != end",
     "line": 6460
    },
    {
     "code": "real_start > 0",
     "line": 6460
    },
    {
     "code": "(BITCODE_RL)dat->byte != real_start",
     "line": 6460
    },
    {
     "code": "(BITCODE_RL)dat->byte < real_start",
     "line": 6463
    },
    {
     "code": "real_start > dat->size",
     "line": 6465
    },
    {
     "code": "dat->byte < (size_t)(dat->size)",
     "line": 6467
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6467
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6467
    },
    {
     "code": "dat->byte < (size_t)(real_start)",
     "line": 6471
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6471
    },
    {
     "code": "_i < (unsigned)(len)",
     "line": 6471
    },
    {
     "code": "end > start",
     "line": 6496
    },
    {
     "code": "start == dat->byte",
     "line": 6496
    },
    {
     "code": "dat->byte < oldpos + size",
     "line": 6500
    },
    {
     "code": "dat->from_version < R_2_0b",
     "line": 6533
    },
    {
     "code": "obj->type > 127",
     "line": 6537
    },
    {
     "code": "obj->type > 127",
     "line": 6551
    },
    {
     "code": "dat->version > R_2_22",
     "line": 6601
    },
    {
     "code": "entity_section == BLOCKS_SECTION_INDEX",
     "line": 6608
    },
    {
     "code": "i < dwg->num_objects",
     "line": 6610
    },
    {
     "code": "o->fixedtype == DWG_TYPE_BLOCK_HEADER",
     "line": 6613
    },
    {
     "code": "cur_offset",
     "line": 6615
    },
    {
     "code": "obj->fixedtype == DWG_TYPE_BLOCK",
     "line": 6658
    },
    {
     "code": "dat->from_version < R_11",
     "line": 6724
    },
    {
     "code": "dat->from_version < R_11",
     "line": 6789
    },
    {
     "code": "dat->size < dat->byte",
     "line": 6865
    },
    {
     "code": "0UL > 0",
     "line": 6865
    },
    {
     "code": "dat->byte + rs > 0UL",
     "line": 6865
    },
    {
     "code": "dat->byte + rs > dat->size",
     "line": 6865
    },
    {
     "code": "_i < (unsigned)(rs)",
     "line": 6865
    },
    {
     "code": "_i < (unsigned)(rs)",
     "line": 6865
    },
    {
     "code": "bb != 3",
     "line": 6865
    },
    {
     "code": "dat->from_version < R_2_0b",
     "line": 6873
    },
    {
     "code": "num + 1 > dwg->num_objects",
     "line": 6876
    },
    {
     "code": "obj->type != DWG_TYPE_JUMP_r11",
     "line": 6879
    },
    {
     "code": "dat->from_version < R_11",
     "line": 6883
    },
    {
     "code": "obj->address + obj->size != dat->byte",
     "line": 6885
    },
    {
     "code": "obj->address + obj->size > dat->byte",
     "line": 6889
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6900
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6900
    },
    {
     "code": "obj->size > 2",
     "line": 6908
    },
    {
     "code": "obj->address + obj->size != dat->byte + 2",
     "line": 6914
    },
    {
     "code": "obj->address + obj->size > dat->byte + 2",
     "line": 6918
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6927
    },
    {
     "code": "_i < (unsigned)(offset)",
     "line": 6927
    },
    {
     "code": "start > 60",
     "line": 6935
    },
    {
     "code": "obj->supertype == DWG_SUPERTYPE_ENTITY",
     "line": 6944
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_UNUSED",
     "line": 6945
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_JUMP",
     "line": 6946
    },
    {
     "code": "obj->type != DWG_TYPE_VERTEX_r11",
     "line": 6947
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_SEQEND",
     "line": 6948
    },
    {
     "code": "obj->fixedtype != DWG_TYPE_BLOCK",
     "line": 6958
    },
    {
     "code": "dat->byte < oldpos + size",
     "line": 6967
    },
    {
     "code": "(BITCODE_RL)dat->byte != end",
     "line": 6969
    },
    {
     "code": "(BITCODE_RL)dat->byte != end",
     "line": 6976
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "memcpy (obj->unknown_rest, &dat->chain[dat->byte],",
     "name": "memcpy",
     "nargs": null
    },
    {
     "code": "obj->unknown_rest",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "&dat->chain[dat->byte]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "dat->chain[dat->byte]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "dat->chain",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dat->byte",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "obj",
    "dat"
   ],
   "osv_id": "ARVO-42529717",
   "sites": [
    {
     "args": "unknown",
     "callee": "free",
     "code": "free(unknown)",
     "line": 6467
    },
    {
     "args": "unknown",
     "callee": "free",
     "code": "free(unknown)",
     "line": 6471
    },
    {
     "args": "REFS_PER_REALLOC ;; sizeof (Dwg_Object)",
     "callee": "calloc",
     "code": "calloc (REFS_PER_REALLOC, sizeof (Dwg_Object))",
     "line": 6508
    },
    {
     "args": "",
     "callee": "REFS_PER_REALLOC",
     "code": "REFS_PER_REALLOC",
     "line": 6508
    },
    {
     "args": null,
     "callee": "realloc",
     "code": "realloc (",
     "line": 6513
    },
    {
     "args": "_hdr->name",
     "callee": "strdup",
     "code": "strdup (_hdr->name)",
     "line": 6647
    },
    {
     "args": "tmp",
     "callee": "free",
     "code": "free(tmp)",
     "line": 6865
    },
    {
     "args": "offset ;; 1",
     "callee": "calloc",
     "code": "calloc (offset, 1)",
     "line": 6895
    },
    {
     "args": "_hdr->entities ;; (_hdr->num_owned + 1) * sizeof (BITCODE_H)",
     "callee": "realloc",
     "code": "realloc(_hdr->entities, (_hdr->num_owned + 1) * sizeof (BITCODE_H))",
     "line": 6959
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "decode_preR13_entities"
  }
 },
 {
  "osv_id": "ARVO-42529718",
  "project": "serenity",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ch",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/serenity/Userland/Libraries/LibGfx/Font/OpenType/Font.cpp",
    "line": 37,
    "size": null,
    "type": "auto"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
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
    "line": 37,
    "fn": "OpenType::be_u32(unsigned char const*)",
    "code": "ch = static_cast<unsigned char>(input[offset++]) | static_cast<unsigned char>(input[offset++]) | input[offset++] | offset++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OpenType::be_u32(unsigned char const*)",
    "file": "/src/serenity/Userland/Libraries/LibGfx/Font/OpenType/Font.cpp",
    "line": 37
   },
   "code": "ch = static_cast<unsigned char>(input[offset++]) | static_cast<unsigned char>(input[offset++]) | input[offset++] | offset++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<lambda>0",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "offset < input.length() | offset >= input.length() | ch == '='",
   "guard_count": 3,
   "control_structures": "WHILE:33,IF:35,IF:39,IF:40,IF:46"
  },
  "call_chain": [],
  "types": {
   "entity_type": "auto",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "offset"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/2258fc273c9eb0db404a8020b8621fab31d1f7f7/ARVO-42529718/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_2258fc273c9e.cpg",
   "testcase_size": 290
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
   "dedup_token": "OpenType::be_u32(unsigned char const*)--OpenType::Cmap::subtable(unsigned int) const--OpenType::Font::try_load_from_offset(AK::Span<unsigned char const>, unsign"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ch = static_cast<unsigned char>(input[offset++])",
     "line": 37
    }
   ],
   "entity_decl": {
    "line": 37,
    "type": "auto"
   },
   "entity_name_cpg": "ch",
   "func_lines": [
    32,
    50
   ],
   "func_params": {
    "names": [
     "offset",
     "is_padding",
     "parsed_something"
    ],
    "types": [
     "size_t&",
     "bool*",
     "bool&"
    ]
   },
   "guards": [
    {
     "code": "offset < input.length()",
     "line": 33
    },
    {
     "code": "ch == '='",
     "line": 39
    },
    {
     "code": "result < 0",
     "line": 46
    },
    {
     "code": "result < 256",
     "line": 48
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "ch = static_cast<unsigned char>(input[offset++])",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "static_cast<unsigned char>(input[offset++])",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "input[offset++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "offset++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "ch",
    "input",
    "offset"
   ],
   "osv_id": "ARVO-42529718",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OpenType::be_u32(unsigned char const*)"
  }
 },
 {
  "osv_id": "ARVO-42529760",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "byte",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 317,
    "size": null,
    "type": "unsigned char"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
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
    "line": 328,
    "fn": "bit_read_RC",
    "code": "byte = dat->chain[dat->byte + 1] | dat->chain[dat->byte + 1] | dat->chain | dat->byte + 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_read_RC",
    "file": "/src/libredwg/src/bits.c",
    "line": 328
   },
   "code": "byte = dat->chain[dat->byte + 1] | dat->chain[dat->byte + 1] | dat->chain | dat->byte + 1",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_read_RC",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:319,IF:319,IF:319,IF:321,ELSE:324,IF:326,ELSE:332,IF:334,IF:334"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "dat"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/5f3f20ac19fe50419d4acec642b932569e3ee092/ARVO-42529760/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_5f3f20ac19fe.cpg",
   "testcase_size": 619
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "dedup_token": "bit_read_RC--bit_read_fixed--bit_read_TF"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "byte = dat->chain[dat->byte]",
     "line": 320
    },
    {
     "code": "byte = dat->chain[dat->byte + 1]",
     "line": 328
    }
   ],
   "entity_decl": {
    "line": 317,
    "type": "unsigned char"
   },
   "entity_name_cpg": "byte",
   "func_lines": [
    313,
    341
   ],
   "func_params": {
    "names": [
     "dat"
    ],
    "types": [
     "Bit_Chain*"
    ]
   },
   "guards": [
    {
     "code": "dat->byte + 1 > dat->size",
     "line": 319
    },
    {
     "code": "((dat->byte + 1) * 8) + dat->bit > dat->size * 8",
     "line": 319
    },
    {
     "code": "dat->bit == 0",
     "line": 321
    },
    {
     "code": "dat->byte < dat->size - 1",
     "line": 326
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "byte = dat->chain[dat->byte + 1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "dat->chain[dat->byte + 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "dat->chain",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dat->byte + 1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "dat->byte",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "byte",
    "dat"
   ],
   "osv_id": "ARVO-42529760",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_read_RC"
  }
 },
 {
  "osv_id": "ARVO-42529812",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmsnamed.c",
    "line": 403,
    "size": null,
    "type": "wchar_t*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 98
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 406,
    "fn": "mywcslen",
    "code": "*p",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mywcslen",
    "file": "/src/lcms/src/cmsnamed.c",
    "line": 406
   },
   "code": "*p",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mywcslen",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:406"
  },
  "call_chain": [],
  "types": {
   "entity_type": "wchar_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "s"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/5262c5df0adab6ef1eb3f54675fc4dbd2b0883c5/ARVO-42529812/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_5262c5df0ada.cpg",
   "testcase_size": 328
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
   "dedup_token": "mywcslen--cmsMLUsetWide--Type_Text_Description_Read"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "p = s",
     "line": 405
    }
   ],
   "entity_decl": {
    "line": 403,
    "type": "wchar_t*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    400,
    410
   ],
   "func_params": {
    "names": [
     "s"
    ],
    "types": [
     "wchar_t*"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "*p",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "p"
   ],
   "osv_id": "ARVO-42529812",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mywcslen"
  }
 },
 {
  "osv_id": "ARVO-42529909",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "mod",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 50,
    "size": null,
    "type": "sc_pkcs11_module_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "iasecc_parse_get_tlv",
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 430
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "1 ;; sizeof(*mod)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc(1, sizeof(*mod))",
    "fn": "iasecc_parse_acls",
    "kind": "calloc",
    "line": 53,
    "origin": "cpg",
    "args": "1 ;; sizeof(*mod)"
   },
   {
    "kind": "free",
    "line": 60,
    "fn": "iasecc_parse_acls",
    "code": "free(mod)",
    "origin": "report:crash",
    "args": "mod"
   },
   {
    "code": "free(mod)",
    "fn": "iasecc_parse_acls",
    "kind": "free",
    "line": 102,
    "origin": "cpg",
    "args": "mod"
   }
  ],
  "crash": {
   "site": {
    "fn": "iasecc_parse_acls",
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 60
   },
   "code": "free(mod)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "C_LoadModule",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "mod == NULL",
   "guard_count": 1,
   "control_structures": "IF:54,IF:59,IF:64,GOTO:66,IF:71,IF:76,ELSE:82,IF:90,GOTO:91,IF:93,ELSE:95,IF:98"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_pkcs11_module_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/fa709de8dc5045f390f321cb65c9c73c36d52dd0/ARVO-42529909/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_fa709de8dc50.cpg",
   "testcase_size": 429
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
  "free_related": {
   "free_sites_in_func": [
    60,
    102
   ],
   "reassign_between": true,
   "reassign_sites": [
    {
     "lhs": "mod",
     "line": 99,
     "rhs": "NULL"
    }
   ],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "iasecc_parse_acls--iasecc_parse_docp--iasecc_sdo_parse_data"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "mod = calloc(1, sizeof(*mod))",
     "line": 53
    },
    {
     "code": "mod->_magic = MAGIC",
     "line": 57
    },
    {
     "code": "mod->handle = sc_dlopen(mspec)",
     "line": 63
    },
    {
     "code": "mod = NULL",
     "line": 99
    }
   ],
   "entity_decl": {
    "line": 50,
    "type": "sc_pkcs11_module_t*"
   },
   "entity_name_cpg": "mod",
   "func_lines": [
    47,
    104
   ],
   "func_params": {
    "names": [
     "mspec",
     "funcs"
    ],
    "types": [
     "char*",
     "CK_FUNCTION_LIST_PTR_PTR"
    ]
   },
   "guards": [
    {
     "code": "mod == NULL",
     "line": 54
    },
    {
     "code": "mspec == NULL",
     "line": 59
    },
    {
     "code": "mod->handle == NULL",
     "line": 64
    },
    {
     "code": "rv == CKR_OK",
     "line": 76
    },
    {
     "code": "rv == CKR_OK",
     "line": 93
    },
    {
     "code": "rv == CKR_OK",
     "line": 98
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "free(mod)",
     "name": "free",
     "nargs": 1
    }
   ],
   "line_ids": [
    "mod"
   ],
   "osv_id": "ARVO-42529909",
   "sites": [
    {
     "args": "1 ;; sizeof(*mod)",
     "callee": "calloc",
     "code": "calloc(1, sizeof(*mod))",
     "line": 53
    },
    {
     "args": "mod",
     "callee": "free",
     "code": "free(mod)",
     "line": 60
    },
    {
     "args": "mod",
     "callee": "free",
     "code": "free(mod)",
     "line": 102
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "iasecc_parse_acls",
   "use_fn": "iasecc_parse_acls"
  }
 },
 {
  "osv_id": "ARVO-42530098",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dest",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 1574,
    "size": null,
    "type": "BITCODE_RC*restrict"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
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
    "line": 1588,
    "fn": "bit_read_fixed",
    "code": "memcpy (dest, &dat->chain[dat->byte], length) | &dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_read_fixed",
    "file": "/src/libredwg/src/bits.c",
    "line": 1588
   },
   "code": "memcpy (dest, &dat->chain[dat->byte], length) | &dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain",
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_read_fixed",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < length",
   "guard_count": 1,
   "control_structures": "IF:1577,IF:1580,IF:1580,IF:1586,ELSE:1592,FOR:1593"
  },
  "call_chain": [],
  "types": {
   "entity_type": "BITCODE_RC*restrict",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "dat",
   "dest",
   "length"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/524364b216354e5a4297861456f3811f3e697ead/ARVO-42530098/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_524364b21635.cpg",
   "testcase_size": 496
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
   "dedup_token": "__asan_memcpy--memcpy--bit_read_fixed"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "dest[i] = bit_read_RC (dat)",
     "line": 1595
    }
   ],
   "entity_decl": {
    "line": 1574,
    "type": "BITCODE_RC*restrict"
   },
   "entity_name_cpg": "dest",
   "func_lines": [
    1573,
    1598
   ],
   "func_params": {
    "names": [
     "dat",
     "dest",
     "length"
    ],
    "types": [
     "Bit_Chain*restrict",
     "BITCODE_RC*restrict",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "dat->byte + length > dat->size",
     "line": 1577
    },
    {
     "code": "dat->bit == 0",
     "line": 1586
    },
    {
     "code": "i < length",
     "line": 1593
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "memcpy (dest, &dat->chain[dat->byte], length)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&dat->chain[dat->byte]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "dat->chain[dat->byte]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "dat->chain",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dat->byte",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dest",
    "dat",
    "length"
   ],
   "osv_id": "ARVO-42530098",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_read_fixed"
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