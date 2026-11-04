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

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "osv_id": "ARVO-42522277",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "global",
   "decl": null
  },
  "alloc": {},
  "sites": [],
  "crash": {
   "site": {
    "fn": "xmlParseQName",
    "file": "/src/libxml2/parser.c",
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
   "fn": "xmlParseQName",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522277/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "testcase_size": 241
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
   "shadow_byte": "f9",
   "shadow_legend_size": 21,
   "dedup_token": "xmlParseQName--xmlParseStartTag2--xmlParseElementStart"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    8859,
    8929
   ],
   "func_params": {
    "names": [
     "ctxt",
     "prefix"
    ],
    "types": [
     "xmlParserCtxtPtr",
     "xmlChar**"
    ]
   },
   "guards": [
    {
     "code": "ctxt->progressive == 0",
     "line": 8863
    },
    {
     "code": "ctxt->input->end - ctxt->input->cur < INPUT_CHUNK",
     "line": 8863
    },
    {
     "code": "l == NULL",
     "line": 8866
    },
    {
     "code": "CUR == ':'",
     "line": 8867
    },
    {
     "code": "l != NULL",
     "line": 8869
    },
    {
     "code": "CUR == ':'",
     "line": 8878
    },
    {
     "code": "l == NULL",
     "line": 8882
    },
    {
     "code": "ctxt->instate == XML_PARSER_EOF",
     "line": 8885
    },
    {
     "code": "l == NULL",
     "line": 8890
    },
    {
     "code": "ctxt->instate == XML_PARSER_EOF",
     "line": 8891
    },
    {
     "code": "tmp != NULL",
     "line": 8899
    },
    {
     "code": "CUR == ':'",
     "line": 8903
    },
    {
     "code": "tmp != NULL",
     "line": 8910
    },
    {
     "code": "tmp != NULL",
     "line": 8913
    },
    {
     "code": "ctxt->instate == XML_PARSER_EOF",
     "line": 8917
    },
    {
     "code": "tmp != NULL",
     "line": 8921
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42522277",
   "sites": [
    {
     "args": "(char *)l",
     "callee": "xmlFree",
     "code": "xmlFree((char *)l)",
     "line": 8896
    },
    {
     "args": "tmp",
     "callee": "xmlFree",
     "code": "xmlFree(tmp)",
     "line": 8899
    },
    {
     "args": "tmp",
     "callee": "xmlFree",
     "code": "xmlFree(tmp)",
     "line": 8913
    },
    {
     "args": "tmp",
     "callee": "xmlFree",
     "code": "xmlFree(tmp)",
     "line": 8921
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlParseQName"
  }
 },
 {
  "osv_id": "ARVO-42522281",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "cur",
   "kind": "pointer",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 2117,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 2122,
    "fn": "xmlSkipBlankChars",
    "code": "IS_BLANK_CH(*cur) | *cur",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlSkipBlankChars",
    "file": "/src/libxml2/parser.c",
    "line": 2122
   },
   "code": "IS_BLANK_CH(*cur) | *cur",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlSkipBlankChars",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:2115,WHILE:2122,IF:2123,ELSE:2125,IF:2129,IF:2131,ELSE:2138,WHILE:2141,IF:2142,ELSE:2144,IF:2144,IF:2148"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522281/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "testcase_size": 1799
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
   "dedup_token": "xmlSkipBlankChars--xmlParseMisc--xmlParseDocument"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cur = ctxt->input->cur",
     "line": 2121
    },
    {
     "code": "cur = ctxt->input->cur",
     "line": 2134
    }
   ],
   "entity_decl": {
    "line": 2117,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "cur",
   "func_lines": [
    2107,
    2193
   ],
   "func_params": {
    "names": [
     "ctxt"
    ],
    "types": [
     "xmlParserCtxtPtr"
    ]
   },
   "guards": [
    {
     "code": "ctxt->inputNr == 1",
     "line": 2115
    },
    {
     "code": "ctxt->instate != XML_PARSER_DTD",
     "line": 2115
    },
    {
     "code": "ctxt->instate == XML_PARSER_START",
     "line": 2116
    },
    {
     "code": "*cur == '\\n'",
     "line": 2123
    },
    {
     "code": "res < INT_MAX",
     "line": 2129
    },
    {
     "code": "*cur == 0",
     "line": 2131
    },
    {
     "code": "ctxt->external != 0",
     "line": 2139
    },
    {
     "code": "ctxt->inputNr != 1",
     "line": 2139
    },
    {
     "code": "ctxt->instate != XML_PARSER_EOF",
     "line": 2141
    },
    {
     "code": "CUR == '%'",
     "line": 2144
    },
    {
     "code": "expandPE == 0",
     "line": 2148
    },
    {
     "code": "NXT(1) == 0",
     "line": 2148
    },
    {
     "code": "CUR == 0",
     "line": 2151
    },
    {
     "code": "ent->etype == XML_EXTERNAL_PARAMETER_ENTITY",
     "line": 2167
    },
    {
     "code": "(ent->flags & XML_ENT_PARSED) == 0",
     "line": 2168
    },
    {
     "code": "res < INT_MAX",
     "line": 2188
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "IS_BLANK_CH(*cur)",
     "name": "IS_BLANK_CH",
     "nargs": 1
    },
    {
     "code": "*cur",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "cur"
   ],
   "osv_id": "ARVO-42522281",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlSkipBlankChars"
  }
 },
 {
  "osv_id": "ARVO-42522285",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "ctxt",
   "kind": "struct",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 9945,
    "size": null,
    "type": "xmlParserCtxtPtr"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 9949,
    "fn": "xmlParseContentInternal",
    "code": "(RAW != 0) &&",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlParseContentInternal",
    "file": "/src/libxml2/parser.c",
    "line": 9949
   },
   "code": "(RAW != 0) &&",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlParseContentInternal",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:9948,WHILE:9949,IF:9956,ELSE:9964,IF:9964,ELSE:9971,IF:9971,ELSE:9980,IF:9980,IF:9981,IF:9982,BREAK:9983"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlParserCtxtPtr",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ctxt"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522285/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "testcase_size": 228
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
   "dedup_token": "xmlParseContentInternal--xmlParseContent--xmlParseExternalEntityPrivate"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ctxt->instate = XML_PARSER_CONTENT",
     "line": 9974
    }
   ],
   "entity_decl": {
    "line": 9945,
    "type": "xmlParserCtxtPtr"
   },
   "entity_name_cpg": "ctxt",
   "func_lines": [
    9944,
    10009
   ],
   "func_params": {
    "names": [
     "ctxt"
    ],
    "types": [
     "xmlParserCtxtPtr"
    ]
   },
   "guards": [
    {
     "code": "ctxt->progressive == 0",
     "line": 9948
    },
    {
     "code": "ctxt->input->end - ctxt->input->cur < INPUT_CHUNK",
     "line": 9948
    },
    {
     "code": "RAW != 0",
     "line": 9949
    },
    {
     "code": "ctxt->instate != XML_PARSER_EOF",
     "line": 9950
    },
    {
     "code": "*cur == '<'",
     "line": 9956
    },
    {
     "code": "cur[1] == '?'",
     "line": 9956
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[0] == '<'",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[1] == '!'",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[2] == '['",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[3] == 'C'",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[4] == 'D'",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[5] == 'A'",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[6] == 'T'",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[7] == 'A'",
     "line": 9964
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[8] == '['",
     "line": 9964
    },
    {
     "code": "*cur == '<'",
     "line": 9971
    },
    {
     "code": "NXT(1) == '!'",
     "line": 9971
    },
    {
     "code": "NXT(2) == '-'",
     "line": 9972
    },
    {
     "code": "NXT(3) == '-'",
     "line": 9972
    },
    {
     "code": "*cur == '<'",
     "line": 9980
    },
    {
     "code": "NXT(1) == '/'",
     "line": 9981
    },
    {
     "code": "*cur == '&'",
     "line": 9995
    },
    {
     "code": "ctxt->progressive == 0",
     "line": 10006
    },
    {
     "code": "ctxt->input->end - ctxt->input->cur < INPUT_CHUNK",
     "line": 10006
    },
    {
     "code": "ctxt->progressive == 0",
     "line": 10007
    },
    {
     "code": "ctxt->input->cur - ctxt->input->base > 2 * INPUT_CHUNK",
     "line": 10007
    },
    {
     "code": "ctxt->input->end - ctxt->input->cur < 2 * INPUT_CHUNK",
     "line": 10007
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "(RAW != 0) &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "RAW != 0",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "RAW",
     "name": "RAW",
     "nargs": 0
    },
    {
     "code": "*ctxt->input->cur",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "ctxt->input->cur",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ctxt->input",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ctxt"
   ],
   "osv_id": "ARVO-42522285",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlParseContentInternal"
  }
 },
 {
  "osv_id": "ARVO-42522315",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "value",
   "kind": "struct",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/dict.c",
    "line": 434,
    "size": null,
    "type": "long unsigned"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 437,
    "fn": "xmlDictComputeFastKey",
    "code": "value += *name | *name",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlDictComputeFastKey",
    "file": "/src/libxml2/dict.c",
    "line": 437
   },
   "code": "value += *name | *name",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlDictComputeFastKey",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "name == NULL",
   "guard_count": 1,
   "control_structures": "IF:436,IF:439,SWITCH:443,BREAK:462"
  },
  "call_chain": [],
  "types": {
   "entity_type": "long unsigned",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "name",
   "namelen",
   "seed"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522315/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "testcase_size": 111
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
   "dedup_token": "xmlDictComputeFastKey--xmlDictLookup--xmlParseNCNameComplex"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "value = seed",
     "line": 434
    }
   ],
   "entity_decl": {
    "line": 434,
    "type": "long unsigned"
   },
   "entity_name_cpg": "value",
   "func_lines": [
    432,
    465
   ],
   "func_params": {
    "names": [
     "name",
     "namelen",
     "seed"
    ],
    "types": [
     "xmlChar*",
     "int",
     "int"
    ]
   },
   "guards": [
    {
     "code": "name == NULL",
     "line": 436
    },
    {
     "code": "namelen > 10",
     "line": 439
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "value += *name",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "*name",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "value",
    "name"
   ],
   "osv_id": "ARVO-42522315",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlDictComputeFastKey"
  }
 },
 {
  "osv_id": "ARVO-42522507",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "ret",
   "kind": "pointer",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/xmlstring.c",
    "line": 46,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {
   "size_expr_cpg": "(size_t) len + 1",
   "size_expr_cpg_callee": "xmlMallocAtomic"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 53,
    "fn": "xmlStrndup",
    "code": "memcpy(ret, cur, len)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlStrndup",
    "file": "/src/libxml2/xmlstring.c",
    "line": 53
   },
   "code": "memcpy(ret, cur, len)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlStrndup",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "cur == NULL | len < 0 | ret == NULL",
   "guard_count": 3,
   "control_structures": "IF:48,IF:50"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "cur",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/ca2bfecea9c23f8d2e11741fff7c6a5372c56bb8/ARVO-42522507/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_ca2bfecea9c2.cpg",
   "testcase_size": 752
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
   "dedup_token": "__asan_memcpy--xmlStrndup--htmlParseSystemLiteral"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ret = (xmlChar *) xmlMallocAtomic((size_t) len + 1)",
     "line": 49
    },
    {
     "code": "ret[len] = 0",
     "line": 54
    }
   ],
   "entity_decl": {
    "line": 46,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "ret",
   "func_lines": [
    44,
    56
   ],
   "func_params": {
    "names": [
     "cur",
     "len"
    ],
    "types": [
     "xmlChar*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "cur == NULL",
     "line": 48
    },
    {
     "code": "len < 0",
     "line": 48
    },
    {
     "code": "ret == NULL",
     "line": 50
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(ret, cur, len)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "ret",
    "cur",
    "len"
   ],
   "osv_id": "ARVO-42522507",
   "sites": [
    {
     "args": "(size_t) len + 1",
     "callee": "xmlMallocAtomic",
     "code": "xmlMallocAtomic((size_t) len + 1)",
     "line": 49
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlStrndup"
  }
 },
 {
  "osv_id": "ARVO-42522518",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "ctxt",
   "kind": "struct",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 5346,
    "size": null,
    "type": "xmlParserCtxtPtr"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 5362,
    "fn": "xmlParseEntityDecl",
    "code": "SKIP(6) | ctxt->input->cur += (6), ctxt->input->col += (6) | ctxt->input->cur += (6) | ctxt->input->cur",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlParseEntityDecl",
    "file": "/src/libxml2/parser.c",
    "line": 5362
   },
   "code": "SKIP(6) | ctxt->input->cur += (6), ctxt->input->col += (6) | ctxt->input->cur += (6) | ctxt->input->cur",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlParseEntityDecl",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "ctxt->userData==ctxt",
   "guard_count": 1,
   "control_structures": "IF:5354,DO:5356,IF:5356,IF:5359,IF:5361,DO:5362,IF:5362,IF:5363,IF:5368,IF:5370,IF:5378,IF:5383"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlParserCtxtPtr",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ctxt"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/9ef2a9abf357f747c2fb03841b7f479cc0dfd3ef/ARVO-42522518/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_9ef2a9abf357.cpg",
   "testcase_size": 639
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "xmlParseEntityDecl--xmlParseMarkupDecl--xmlParseInternalSubset"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ctxt->instate = XML_PARSER_ENTITY_DECL",
     "line": 5393
    },
    {
     "code": "ctxt->myDoc->properties = XML_DOC_INTERNAL",
     "line": 5462
    },
    {
     "code": "ctxt->myDoc->properties = XML_DOC_INTERNAL",
     "line": 5533
    }
   ],
   "entity_decl": {
    "line": 5346,
    "type": "xmlParserCtxtPtr"
   },
   "entity_name_cpg": "ctxt",
   "func_lines": [
    5345,
    5591
   ],
   "func_params": {
    "names": [
     "ctxt"
    ],
    "types": [
     "xmlParserCtxtPtr"
    ]
   },
   "guards": [
    {
     "code": "CUR != '<'",
     "line": 5354
    },
    {
     "code": "NXT(1) != '!'",
     "line": 5354
    },
    {
     "code": "*ctxt->input->cur == 0",
     "line": 5356
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[0] == 'E'",
     "line": 5359
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[1] == 'N'",
     "line": 5359
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[2] == 'T'",
     "line": 5359
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[3] == 'I'",
     "line": 5359
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[4] == 'T'",
     "line": 5359
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[5] == 'Y'",
     "line": 5359
    },
    {
     "code": "ctxt->progressive == 0",
     "line": 5361
    },
    {
     "code": "ctxt->input->cur - ctxt->input->base > 2 * INPUT_CHUNK",
     "line": 5361
    },
    {
     "code": "ctxt->input->end - ctxt->input->cur < 2 * INPUT_CHUNK",
     "line": 5361
    },
    {
     "code": "*ctxt->input->cur == 0",
     "line": 5362
    },
    {
     "code": "SKIP_BLANKS == 0",
     "line": 5363
    },
    {
     "code": "RAW == '%'",
     "line": 5368
    },
    {
     "code": "SKIP_BLANKS == 0",
     "line": 5370
    },
    {
     "code": "name == NULL",
     "line": 5378
    },
    {
     "code": "xmlStrchr(name, ':') != NULL",
     "line": 5383
    },
    {
     "code": "SKIP_BLANKS == 0",
     "line": 5388
    },
    {
     "code": "RAW == '\"'",
     "line": 5398
    },
    {
     "code": "RAW == '\\''",
     "line": 5398
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5401
    },
    {
     "code": "ctxt->sax->entityDecl != NULL",
     "line": 5402
    },
    {
     "code": "URI == NULL",
     "line": 5409
    },
    {
     "code": "literal == NULL",
     "line": 5409
    },
    {
     "code": "uri == NULL",
     "line": 5416
    },
    {
     "code": "uri->fragment != NULL",
     "line": 5425
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5432
    },
    {
     "code": "ctxt->sax->entityDecl != NULL",
     "line": 5434
    },
    {
     "code": "RAW == '\"'",
     "line": 5444
    },
    {
     "code": "RAW == '\\''",
     "line": 5444
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5446
    },
    {
     "code": "ctxt->sax->entityDecl != NULL",
     "line": 5447
    },
    {
     "code": "ctxt->myDoc == NULL",
     "line": 5456
    },
    {
     "code": "ctxt->myDoc == NULL",
     "line": 5458
    },
    {
     "code": "URI == NULL",
     "line": 5473
    },
    {
     "code": "literal == NULL",
     "line": 5473
    },
    {
     "code": "uri == NULL",
     "line": 5480
    },
    {
     "code": "uri->fragment != NULL",
     "line": 5489
    },
    {
     "code": "RAW != '>'",
     "line": 5499
    },
    {
     "code": "SKIP_BLANKS == 0",
     "line": 5499
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[0] == 'N'",
     "line": 5503
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[1] == 'D'",
     "line": 5503
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[2] == 'A'",
     "line": 5503
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[3] == 'T'",
     "line": 5503
    },
    {
     "code": "((unsigned char *)ctxt->input->cur)[4] == 'A'",
     "line": 5503
    },
    {
     "code": "*ctxt->input->cur == 0",
     "line": 5504
    },
    {
     "code": "SKIP_BLANKS == 0",
     "line": 5505
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5510
    },
    {
     "code": "ctxt->sax->unparsedEntityDecl != NULL",
     "line": 5511
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5515
    },
    {
     "code": "ctxt->sax->entityDecl != NULL",
     "line": 5516
    },
    {
     "code": "ctxt->myDoc == NULL",
     "line": 5527
    },
    {
     "code": "ctxt->myDoc == NULL",
     "line": 5529
    },
    {
     "code": "ctxt->instate == XML_PARSER_EOF",
     "line": 5546
    },
    {
     "code": "RAW != '>'",
     "line": 5549
    },
    {
     "code": "inputid != ctxt->input->id",
     "line": 5554
    },
    {
     "code": "orig != NULL",
     "line": 5561
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5568
    },
    {
     "code": "ctxt->sax->getParameterEntity != NULL",
     "line": 5569
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 5572
    },
    {
     "code": "ctxt->sax->getEntity != NULL",
     "line": 5573
    },
    {
     "code": "cur == NULL",
     "line": 5575
    },
    {
     "code": "ctxt->userData==ctxt",
     "line": 5575
    },
    {
     "code": "cur != NULL",
     "line": 5579
    },
    {
     "code": "cur->orig == NULL",
     "line": 5579
    },
    {
     "code": "value != NULL",
     "line": 5586
    },
    {
     "code": "URI != NULL",
     "line": 5587
    },
    {
     "code": "literal != NULL",
     "line": 5588
    },
    {
     "code": "orig != NULL",
     "line": 5589
    }
   ],
   "line_call_count": 13,
   "line_calls": [
    {
     "code": "SKIP(6)",
     "name": "SKIP",
     "nargs": 1
    },
    {
     "code": "ctxt->input->cur += (6), ctxt->input->col += (6)",
     "name": "<operator>.expressionList",
     "nargs": 2
    },
    {
     "code": "ctxt->input->cur += (6)",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "ctxt->input->cur",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ctxt->input",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ctxt->input->col += (6)",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "ctxt->input->col",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ctxt->input",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "*ctxt->input->cur == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*ctxt->input->cur",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "ctxt->input->cur",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ctxt->input",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "xmlParserGrow(ctxt)",
     "name": "xmlParserGrow",
     "nargs": 1
    }
   ],
   "line_ids": [
    "ctxt"
   ],
   "osv_id": "ARVO-42522518",
   "sites": [
    {
     "args": "uri",
     "callee": "xmlFreeURI",
     "code": "xmlFreeURI(uri)",
     "line": 5439
    },
    {
     "args": "uri",
     "callee": "xmlFreeURI",
     "code": "xmlFreeURI(uri)",
     "line": 5496
    },
    {
     "args": "value",
     "callee": "xmlFree",
     "code": "xmlFree(value)",
     "line": 5586
    },
    {
     "args": "URI",
     "callee": "xmlFree",
     "code": "xmlFree(URI)",
     "line": 5587
    },
    {
     "args": "literal",
     "callee": "xmlFree",
     "code": "xmlFree(literal)",
     "line": 5588
    },
    {
     "args": "orig",
     "callee": "xmlFree",
     "code": "xmlFree(orig)",
     "line": 5589
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlParseEntityDecl"
  }
 },
 {
  "osv_id": "ARVO-42522530",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "in",
   "kind": "pointer",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/HTMLparser.c",
    "line": 3345,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 3371,
    "fn": "htmlParsePI",
    "code": "in++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "htmlParsePI",
    "file": "/src/libxml2/HTMLparser.c",
    "line": 3371
   },
   "code": "in++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlParseName",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:3352,IF:3362,WHILE:3366,IF:3372,IF:3374,IF:3381"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522530/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "testcase_size": 373
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "htmlParsePI--htmlParseDocument--htmlDoRead"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "in = ctxt->input->cur",
     "line": 3361
    }
   ],
   "entity_decl": {
    "line": 3345,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "in",
   "func_lines": [
    3343,
    3388
   ],
   "func_params": {
    "names": [
     "ctxt"
    ],
    "types": [
     "xmlParserCtxtPtr"
    ]
   },
   "guards": [
    {
     "code": "ctxt->progressive == 0",
     "line": 3352
    },
    {
     "code": "ctxt->input->end - ctxt->input->cur < INPUT_CHUNK",
     "line": 3352
    },
    {
     "code": "*in == '_'",
     "line": 3364
    },
    {
     "code": "*in == ':'",
     "line": 3364
    },
    {
     "code": "*in == '_'",
     "line": 3369
    },
    {
     "code": "*in == '-'",
     "line": 3369
    },
    {
     "code": "*in == ':'",
     "line": 3370
    },
    {
     "code": "*in == '.'",
     "line": 3370
    },
    {
     "code": "*in > 0",
     "line": 3372
    },
    {
     "code": "*in < 0x80",
     "line": 3372
    },
    {
     "code": "count > maxLength",
     "line": 3374
    },
    {
     "code": "ret == NULL",
     "line": 3381
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "in++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "in"
   ],
   "osv_id": "ARVO-42522530",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "htmlParsePI"
  }
 },
 {
  "osv_id": "ARVO-42525210",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "cur",
   "kind": "pointer",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/HTMLparser.c",
    "line": 2748,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {
   "size_expr_cpg": "XML_MAX_NAMELEN + 5",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2759,
    "fn": "htmlParseHTMLAttribute",
    "code": "cur[2] == 'l' | cur[2] | cur[3] == ':' | cur[3]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "htmlParseHTMLAttribute",
    "file": "/src/libxml2/HTMLparser.c",
    "line": 2759
   },
   "code": "cur[2] == 'l' | cur[2] | cur[3] == ':' | cur[3]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlSplitQName",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "cur == NULL",
   "guard_count": 1,
   "control_structures": "IF:2751,IF:2754,IF:2758,IF:2764,WHILE:2768,IF:2772,IF:2780,WHILE:2785,IF:2786,IF:2791,IF:2804,IF:2805"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "name",
   "prefix"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/20f5c73457df065df21bf25aa081a0a4cd028046/ARVO-42525210/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_20f5c73457df.cpg",
   "testcase_size": 994
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "htmlParseHTMLAttribute--htmlParseAttValue--htmlParseAttribute"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*cur = name",
     "line": 2748
    }
   ],
   "entity_decl": {
    "line": 2748,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "cur",
   "func_lines": [
    2741,
    2890
   ],
   "func_params": {
    "names": [
     "ctxt",
     "name",
     "prefix"
    ],
    "types": [
     "xmlParserCtxtPtr",
     "xmlChar*",
     "xmlChar**"
    ]
   },
   "guards": [
    {
     "code": "prefix == NULL",
     "line": 2751
    },
    {
     "code": "cur == NULL",
     "line": 2754
    },
    {
     "code": "cur[0] == 'x'",
     "line": 2758
    },
    {
     "code": "cur[1] == 'm'",
     "line": 2758
    },
    {
     "code": "cur[2] == 'l'",
     "line": 2759
    },
    {
     "code": "cur[3] == ':'",
     "line": 2759
    },
    {
     "code": "cur[0] == ':'",
     "line": 2764
    },
    {
     "code": "c != 0",
     "line": 2768
    },
    {
     "code": "c != ':'",
     "line": 2768
    },
    {
     "code": "len < max",
     "line": 2768
    },
    {
     "code": "buffer == NULL",
     "line": 2780
    },
    {
     "code": "c != 0",
     "line": 2785
    },
    {
     "code": "c != ':'",
     "line": 2785
    },
    {
     "code": "len + 10 > max",
     "line": 2786
    },
    {
     "code": "tmp == NULL",
     "line": 2791
    },
    {
     "code": "c == ':'",
     "line": 2804
    },
    {
     "code": "*cur == 0",
     "line": 2804
    },
    {
     "code": "buffer != NULL",
     "line": 2805
    },
    {
     "code": "buffer == NULL",
     "line": 2811
    },
    {
     "code": "c == ':'",
     "line": 2820
    },
    {
     "code": "c == 0",
     "line": 2823
    },
    {
     "code": "c == '_'",
     "line": 2834
    },
    {
     "code": "c == ':'",
     "line": 2834
    },
    {
     "code": "first != '_'",
     "line": 2838
    },
    {
     "code": "c != 0",
     "line": 2846
    },
    {
     "code": "len < max",
     "line": 2846
    },
    {
     "code": "buffer == NULL",
     "line": 2858
    },
    {
     "code": "c != 0",
     "line": 2863
    },
    {
     "code": "len + 10 > max",
     "line": 2864
    },
    {
     "code": "tmp == NULL",
     "line": 2869
    },
    {
     "code": "buffer == NULL",
     "line": 2882
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "cur[2] == 'l'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "cur[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "cur[3] == ':'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "cur[3]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cur"
   ],
   "osv_id": "ARVO-42525210",
   "sites": [
    {
     "args": "XML_MAX_NAMELEN + 5",
     "callee": "<operator>.alloc",
     "code": "buf[XML_MAX_NAMELEN + 5]",
     "line": 2743
    },
    {
     "args": "name",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(name)",
     "line": 2760
    },
    {
     "args": "name",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(name)",
     "line": 2765
    },
    {
     "args": "max",
     "callee": "xmlMallocAtomic",
     "code": "xmlMallocAtomic(max)",
     "line": 2779
    },
    {
     "args": "buffer ;; max",
     "callee": "xmlRealloc",
     "code": "xmlRealloc(buffer, max)",
     "line": 2790
    },
    {
     "args": "buffer",
     "callee": "xmlFree",
     "code": "xmlFree(buffer)",
     "line": 2792
    },
    {
     "args": "buffer",
     "callee": "xmlFree",
     "code": "xmlFree(buffer)",
     "line": 2806
    },
    {
     "args": "name",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(name)",
     "line": 2808
    },
    {
     "args": "buf ;; len",
     "callee": "xmlStrndup",
     "code": "xmlStrndup(buf, len)",
     "line": 2812
    },
    {
     "args": "max",
     "callee": "xmlMallocAtomic",
     "code": "xmlMallocAtomic(max)",
     "line": 2857
    },
    {
     "args": "buffer ;; max",
     "callee": "xmlRealloc",
     "code": "xmlRealloc(buffer, max)",
     "line": 2868
    },
    {
     "args": "buffer",
     "callee": "xmlFree",
     "code": "xmlFree(buffer)",
     "line": 2871
    },
    {
     "args": "buf ;; len",
     "callee": "xmlStrndup",
     "code": "xmlStrndup(buf, len)",
     "line": 2883
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "htmlParseHTMLAttribute"
  }
 },
 {
  "osv_id": "ARVO-42530289",
  "project": "wireshark",
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
    "line": 1748,
    "fn": "dissect_zcl_read_attr_struct",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dissect_zcl_read_attr_struct",
    "file": "/src/wireshark/epan/dissectors/packet-zbee-zcl.c",
    "line": 1748
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dissect_zcl_read_attr_struct",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/wireshark/address/855c445d14feca90a1568a033f754f8e69313776/ARVO-42530289/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_855c445d14fe.cpg",
   "testcase_size": 952
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
   "shadow_legend_size": 0,
   "dedup_token": "dissect_zcl_read_attr_struct--dissect_zbee_zcl--call_dissector_through_handle"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dissect_zcl_read_attr_struct"
  }
 },
 {
  "osv_id": "ARVO-42531092",
  "project": "libxml2",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "i",
   "kind": "struct",
   "storage": "global",
   "decl": {
    "file": "/src/libxml2/dict.c",
    "line": 467,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 471,
    "fn": "xmlDictHashName",
    "code": "i = 0 | i < maxLen && data[i] | i < maxLen | data[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlDictHashName",
    "file": "/src/libxml2/dict.c",
    "line": 471
   },
   "code": "i = 0 | i < maxLen && data[i] | i < maxLen | data[i]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlDictHashName",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < maxLen",
   "guard_count": 1,
   "control_structures": "DO:469,FOR:471,DO:472,DO:475"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "seed",
   "data",
   "maxLen",
   "plen"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/4e23892cf04cdbe470b4e09c81cc1ed79c86fd10/ARVO-42531092/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_4e23892cf04c.cpg",
   "testcase_size": 207
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
   "shadow_legend_size": 0,
   "dedup_token": "xmlDictHashName--xmlDictLookupInternal--xmlDictLookupHashed"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "i = 0",
     "line": 471
    }
   ],
   "entity_decl": {
    "line": 467,
    "type": "size_t"
   },
   "entity_name_cpg": "i",
   "func_lines": [
    463,
    479
   ],
   "func_params": {
    "names": [
     "seed",
     "data",
     "maxLen",
     "plen"
    ],
    "types": [
     "unsigned",
     "xmlChar*",
     "size_t",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "i < maxLen",
     "line": 471
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "i = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "i < maxLen && data[i]",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "i < maxLen",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "data[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "i",
    "maxLen",
    "data"
   ],
   "osv_id": "ARVO-42531092",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlDictHashName"
  }
 },
 {
  "osv_id": "ARVO-42533290",
  "project": "igraph",
  "crash_type": "global-buffer-overflow",
  "entity": {
   "name": "this",
   "kind": null,
   "storage": "global",
   "decl": {
    "file": null,
    "line": 3535,
    "type": "fitHRG.simpleGraph",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 3536,
    "fn": "igraph_dl_yylex",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "igraph_dl_yylex",
    "file": "/src/igraph/build/src/io/parsers/dl-lexer.c",
    "line": 3536
   },
   "code": "this->m",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "igraph_dl_yylex",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/igraph/address/74b2e25f02b82b583ee6c38c52e024337571f443/ARVO-42533290/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/igraph_74b2e25f02b8.cpg",
   "testcase_size": 2
  },
  "type_reconciliation": {
   "report_fault_kind": "global-buffer-overflow",
   "ledger_crash_type": "global-buffer-overflow",
   "used": "global-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f9",
   "shadow_legend_size": 21,
   "dedup_token": "igraph_dl_yylex--igraph_dl_yyparse--igraph_read_graph_dl"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 3535,
    "type": "fitHRG.simpleGraph"
   },
   "entity_name_cpg": "this",
   "func_lines": [
    3535,
    3537
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "fitHRG.simpleGraph"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "this->m",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "this"
   ],
   "osv_id": "ARVO-42533290",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "igraph_dl_yylex"
  }
 },
 {
  "osv_id": "OSV-2016-5",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2016-5.log",
   "cpg": null,
   "testcase_size": 4874
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
  "osv_id": "OSV-2017-121",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2017-121.log",
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
  "osv_id": "OSV-2017-157",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2017-157.log",
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
  "osv_id": "OSV-2017-167",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2017-167.log",
   "cpg": null,
   "testcase_size": 1920
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