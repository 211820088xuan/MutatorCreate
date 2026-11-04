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
  "osv_id": "ARVO-42509373",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "oid",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 265,
    "size": null,
    "type": "sc_object_id*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 278,
    "fn": "sc_format_oid",
    "code": "oid->value[ii] = strtol(p, &q, 10) | oid->value[ii] | oid->value | strtol(p, &q, 10)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_format_oid",
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 278
   },
   "code": "oid->value[ii] = strtol(p, &q, 10) | oid->value[ii] | oid->value | strtol(p, &q, 10)",
   "access": {
    "dir": "READ",
    "width": 17,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_format_oid",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "oid == NULL | ii < SC_MAX_OBJECT_ID_OCTETS",
   "guard_count": 2,
   "control_structures": "IF:271,FOR:277,IF:279,BREAK:280,IF:282,GOTO:283,IF:288,GOTO:289,IF:293"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_object_id*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "oid",
   "in"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509373/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 101
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 800,
   "loc_kind": "stack_frame",
   "dedup_token": "StrtolFixAndCheck(void*, char const*, char**, char*, int)--__interceptor_strtol--sc_format_oid"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "oid->value[ii] = strtol(p, &q, 10)",
     "line": 278
    }
   ],
   "entity_decl": {
    "line": 265,
    "type": "sc_object_id*"
   },
   "entity_name_cpg": "oid",
   "func_lines": [
    265,
    297
   ],
   "func_params": {
    "names": [
     "oid",
     "in"
    ],
    "types": [
     "sc_object_id*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "oid == NULL",
     "line": 271
    },
    {
     "code": "in == NULL",
     "line": 271
    },
    {
     "code": "ii < SC_MAX_OBJECT_ID_OCTETS",
     "line": 277
    },
    {
     "code": "q[0] == '.'",
     "line": 282
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "oid->value[ii] = strtol(p, &q, 10)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "oid->value[ii]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "oid->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "strtol(p, &q, 10)",
     "name": "strtol",
     "nargs": 3
    },
    {
     "code": "&q",
     "name": "<operator>.addressOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "oid",
    "ii",
    "p",
    "q"
   ],
   "osv_id": "ARVO-42509373",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_format_oid"
  }
 },
 {
  "osv_id": "ARVO-42510727",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "line": 901,
    "size": null,
    "type": "u8*"
   }
  },
  "alloc": {
   "size_expr_cpg": "MAX_EXT_APDU_LENGTH",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 927,
    "fn": "sc_hsm_list_files",
    "code": "memcpy(buf, recvbuf, buflen)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_hsm_list_files",
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "line": 927
   },
   "code": "memcpy(buf, recvbuf, buflen)",
   "access": {
    "dir": "READ",
    "width": 65538,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_hsm_list_files",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:908,ELSE:910,IF:919,DO:925,IF:925,DO:929,IF:929,ELSE:929"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf",
   "buflen"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b35993db095c14be95fc0f40b96b44e2850b7990/ARVO-42510727/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b35993db095c.cpg",
   "testcase_size": 21
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_offset": 1190,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--sc_hsm_list_files--sc_list_files"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 901,
    "type": "u8*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    901,
    930
   ],
   "func_params": {
    "names": [
     "card",
     "buf",
     "buflen"
    ],
    "types": [
     "sc_card_t*",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "r == SC_ERROR_TRANSMIT_FAILED",
     "line": 919
    },
    {
     "code": "_ret < 0",
     "line": 925
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(buf, recvbuf, buflen)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "buf",
    "recvbuf",
    "buflen"
   ],
   "osv_id": "ARVO-42510727",
   "sites": [
    {
     "args": "MAX_EXT_APDU_LENGTH",
     "callee": "<operator>.alloc",
     "code": "recvbuf[MAX_EXT_APDU_LENGTH]",
     "line": 904
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_hsm_list_files"
  }
 },
 {
  "osv_id": "ARVO-42510993",
  "project": "libredwg",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {
   "size_expr_cpg": "strlen (*(char**)value)+1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3093,
    "fn": "dynapi_set_helper",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dynapi_set_helper",
    "file": "/src/libredwg/src/gen-dynapi.pl",
    "line": 3093
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 256,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dynapi_set_helper",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/libredwg/address/d8911aa11479953ca8ebda8367302767dcbc68f0/ARVO-42510993/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_d8911aa11479.cpg",
   "testcase_size": 36
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 184,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--memcpy--dynapi_set_helper"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    14239,
    14287
   ],
   "func_params": {
    "names": [
     "old",
     "f",
     "dwg_version",
     "value",
     "is_utf8"
    ],
    "types": [
     "void*restrict",
     "Dwg_DYNAPI_field*restrict",
     "Dwg_Version_Type",
     "void*restrict",
     "bool"
    ]
   },
   "guards": [
    {
     "code": "dwg_version < R_2007",
     "line": 14254
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42510993",
   "sites": [
    {
     "args": "strlen (*(char**)value)+1",
     "callee": "malloc",
     "code": "malloc (strlen (*(char**)value)+1)",
     "line": 14256
    },
    {
     "args": "2 * length",
     "callee": "malloc",
     "code": "malloc (2 * length)",
     "line": 14276
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dynapi_set_helper"
  }
 },
 {
  "osv_id": "ARVO-42511654",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-cardos.c",
    "line": 495,
    "size": null,
    "type": "u8*"
   }
  },
  "alloc": {
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 544,
    "fn": "cardos_list_files",
    "code": "buf[fids++] = q[1] | buf[fids++] | fids++ | q[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "cardos_list_files",
    "file": "/src/opensc/src/libopensc/card-cardos.c",
    "line": 544
   },
   "code": "buf[fids++] = q[1] | buf[fids++] | fids++ | q[1]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cardos_list_files",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "q == NULL | q != NULL",
   "guard_count": 2,
   "control_structures": "DO:503,DO:516,IF:516,DO:518,IF:518,IF:520,WHILE:525,IF:529,IF:533,BREAK:535,IF:537,IF:542"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b35993db095c14be95fc0f40b96b44e2850b7990/ARVO-42511654/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b35993db095c.cpg",
   "testcase_size": 375
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 432,
   "loc_kind": "stack_frame",
   "dedup_token": "cardos_list_files--sc_list_files--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf[fids++] = q[0]",
     "line": 543
    },
    {
     "code": "buf[fids++] = q[1]",
     "line": 544
    }
   ],
   "entity_decl": {
    "line": 495,
    "type": "u8*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    495,
    562
   ],
   "func_params": {
    "names": [
     "card",
     "buf",
     "buflen"
    ],
    "types": [
     "sc_card_t*",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "_ret < 0",
     "line": 516
    },
    {
     "code": "_ret < 0",
     "line": 518
    },
    {
     "code": "apdu.resplen > 256",
     "line": 520
    },
    {
     "code": "len != 0",
     "line": 525
    },
    {
     "code": "p == NULL",
     "line": 529
    },
    {
     "code": "tlen == 0",
     "line": 533
    },
    {
     "code": "q == NULL",
     "line": 537
    },
    {
     "code": "ilen != 2",
     "line": 537
    },
    {
     "code": "q != NULL",
     "line": 551
    },
    {
     "code": "ilen == 1",
     "line": 551
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "buf[fids++] = q[1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "buf[fids++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "fids++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "q[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "fids",
    "q"
   ],
   "osv_id": "ARVO-42511654",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "rbuf[256]",
     "line": 498
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "cardos_list_files"
  }
 },
 {
  "osv_id": "ARVO-42511896",
  "project": "ndpi",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "str",
   "kind": "array",
   "storage": "stack",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1218,
    "size": null,
    "type": "char[64]"
   }
  },
  "alloc": {
   "size_expr_cpg": "64",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1224,
    "fn": "tlsCheckUncommonALPN",
    "code": "strncpy(str, alpn_start, alpn_len)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tlsCheckUncommonALPN",
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1224
   },
   "code": "strncpy(str, alpn_start, alpn_len)",
   "access": {
    "dir": "WRITE",
    "width": 116,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tlsCheckUncommonALPN",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:1207,IF:1212,IF:1217,BREAK:1226"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[64]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/897f8314b29cd7de9eeab9af15b3e189ae6724a1/ARVO-42511896/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_897f8314b29c.cpg",
   "testcase_size": 295
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 96,
   "loc_kind": "stack_frame",
   "dedup_token": "__interceptor_strncpy--tlsCheckUncommonALPN--processClientServerHello"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "str[64] = { '\\0' }",
     "line": 1218
    },
    {
     "code": "str[64] = { '\\0' }",
     "line": 1218
    }
   ],
   "entity_decl": {
    "line": 1218,
    "type": "char[64]"
   },
   "entity_name_cpg": "str",
   "func_lines": [
    1203,
    1231
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*"
    ]
   },
   "guards": [
    {
     "code": "comma_or_nul == NULL",
     "line": 1212
    },
    {
     "code": "*(comma_or_nul++) != '\\0'",
     "line": 1230
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "strncpy(str, alpn_start, alpn_len)",
     "name": "strncpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "str",
    "alpn_start",
    "alpn_len"
   ],
   "osv_id": "ARVO-42511896",
   "sites": [
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64] = { '\\0' }",
     "line": 1218
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tlsCheckUncommonALPN"
  }
 },
 {
  "osv_id": "ARVO-42514948",
  "project": "wireshark",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 1015,
    "fn": "get_transaction",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_transaction",
    "file": "/src/wireshark/epan/dissectors/packet-atalk.c",
    "line": 1015
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_transaction",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/3307397da14b543a289191c23af9a61fb32eeb46/ARVO-42514948/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_3307397da14b.cpg",
   "testcase_size": 960
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_offset": 84,
   "loc_kind": "stack_frame",
   "dedup_token": "get_transaction--dissect_asp--call_dissector_through_handle"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "get_transaction"
  }
 },
 {
  "osv_id": "ARVO-42515176",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "out",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "line": 1032,
    "size": null,
    "type": "u8*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1083,
    "fn": "sc_hsm_decode_ecdsa_signature",
    "code": "memcpy(out + fieldsizebytes*i + fieldsizebytes - taglen  | out + fieldsizebytes*i + fieldsizebytes - taglen | out + fieldsizebytes*i + fieldsizebytes | out + fieldsizebytes*i",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_hsm_decode_ecdsa_signature",
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "line": 1083
   },
   "code": "memcpy(out + fieldsizebytes*i + fieldsizebytes - taglen  | out + fieldsizebytes*i + fieldsizebytes - taglen | out + fieldsizebytes*i + fieldsizebytes | out + fieldsizebytes*i",
   "access": {
    "dir": "WRITE",
    "width": 256,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_hsm_decode_ecdsa_signature",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i<2 | taglen > fieldsizebytes",
   "guard_count": 2,
   "control_structures": "IF:1040,ELSE:1042,IF:1042,ELSE:1044,IF:1044,ELSE:1046,IF:1046,ELSE:1048,IF:1048,ELSE:1050,IF:1050,ELSE:1052"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "data",
   "out",
   "outlen"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/4edb7ceffb6d704688be20a71c77d302dea0e82a/ARVO-42515176/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_4edb7ceffb6d.cpg",
   "testcase_size": 41798
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 1056,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--sc_hsm_decode_ecdsa_signature--sc_hsm_compute_signature"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1032,
    "type": "u8*"
   },
   "entity_name_cpg": "out",
   "func_lines": [
    1030,
    1096
   ],
   "func_params": {
    "names": [
     "card",
     "data",
     "datalen",
     "out",
     "outlen"
    ],
    "types": [
     "sc_card_t*",
     "u8*",
     "size_t",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "outlen < (fieldsizebytes * 2)",
     "line": 1060
    },
    {
     "code": "_ret < 0",
     "line": 1061
    },
    {
     "code": "i<2",
     "line": 1068
    },
    {
     "code": "taglen > fieldsizebytes",
     "line": 1075
    },
    {
     "code": "*tag != 0x00",
     "line": 1076
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "memcpy(out + fieldsizebytes*i + fieldsizebytes - taglen , tag, taglen)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "out + fieldsizebytes*i + fieldsizebytes - taglen",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "out + fieldsizebytes*i + fieldsizebytes",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "out + fieldsizebytes*i",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "fieldsizebytes*i",
     "name": "<operator>.multiplication",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out",
    "fieldsizebytes",
    "i",
    "taglen",
    "tag"
   ],
   "osv_id": "ARVO-42515176",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_hsm_decode_ecdsa_signature"
  }
 },
 {
  "osv_id": "ARVO-42516818",
  "project": "ndpi",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "msg",
   "kind": "array",
   "storage": "stack",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 668,
    "size": null,
    "type": "char[64]"
   }
  },
  "alloc": {
   "size_expr_cpg": "16",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 670,
    "fn": "ndpi_check_http_server",
    "code": "snprintf(msg, sizeof(msg), \"Obsolete nginx server %s\", b | sizeof(msg)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_http_server",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 670
   },
   "code": "snprintf(msg, sizeof(msg), \"Obsolete nginx server %s\", b | sizeof(msg)",
   "access": {
    "dir": "READ",
    "width": 17,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_http_server",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:645,IF:648,ELSE:651,IF:651,FOR:656,IF:659,IF:662,ELSE:667,IF:667"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[64]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "server"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/37c88b129f6f5a3475dc6364cc4a898df9ff37ab/ARVO-42516818/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_37c88b129f6f.cpg",
   "testcase_size": 64
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 288,
   "loc_kind": "stack_frame",
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--__interceptor_snprintf--ndpi_check_http_server"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "msg[64]",
     "line": 663
    },
    {
     "code": "msg[64]",
     "line": 668
    }
   ],
   "entity_decl": {
    "line": 663,
    "type": "char[64]"
   },
   "entity_name_cpg": "msg",
   "func_lines": [
    642,
    676
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow",
     "server",
     "server_len"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*",
     "char*",
     "u_int"
    ]
   },
   "guards": [
    {
     "code": "server_len > 7",
     "line": 645
    },
    {
     "code": "strncmp((const char *)server, \"ntopng \", 7) == 0",
     "line": 648
    },
    {
     "code": "strncasecmp(server, \"Apache/\", off = 7) == 0",
     "line": 651
    },
    {
     "code": "strncasecmp(server, \"nginx/\", off = 6) == 0",
     "line": 652
    },
    {
     "code": "i<server_len",
     "line": 656
    },
    {
     "code": "server[i] != ' '",
     "line": 656
    },
    {
     "code": "j<sizeof(buf)",
     "line": 656
    },
    {
     "code": "sscanf(buf, \"%d.%d.%d\", &a, &b, &c) == 3",
     "line": 659
    },
    {
     "code": "off == 7",
     "line": 662
    },
    {
     "code": "version < MIN_APACHE_VERSION",
     "line": 662
    },
    {
     "code": "off == 6",
     "line": 667
    },
    {
     "code": "version < MIN_NGINX_VERSION",
     "line": 667
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "snprintf(msg, sizeof(msg), \"Obsolete nginx server %s\", buf)",
     "name": "snprintf",
     "nargs": 4
    },
    {
     "code": "sizeof(msg)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "msg",
    "buf"
   ],
   "osv_id": "ARVO-42516818",
   "sites": [
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "buf[16] = { '\\0' }",
     "line": 654
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "msg[64]",
     "line": 663
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "msg[64]",
     "line": 668
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_check_http_server"
  }
 },
 {
  "osv_id": "ARVO-42517300",
  "project": "wireshark",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 15203,
    "fn": "dissect_he_feedback_matrix",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dissect_he_feedback_matrix",
    "file": "/src/wireshark/epan/dissectors/packet-ieee80211.c",
    "line": 15203
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 9,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dissect_he_feedback_matrix",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/139e46898dfd4aeed90da6f0684f8e32475340c8/ARVO-42517300/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_139e46898dfd.cpg",
   "testcase_size": 131
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 561,
   "loc_kind": "stack_frame",
   "dedup_token": "vsnprintf--__interceptor_snprintf--dissect_he_feedback_matrix"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dissect_he_feedback_matrix"
  }
 },
 {
  "osv_id": "ARVO-42517374",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "argv",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-authentic.c",
    "line": 142,
    "size": null,
    "type": "char[]*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 160,
    "fn": "authentic_parse_size",
    "code": "(argv[my_optind][0] == '-') &&",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "authentic_parse_size",
    "file": "/src/opensc/src/libopensc/card-authentic.c",
    "line": 160
   },
   "code": "(argv[my_optind][0] == '-') &&",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_my_getopt_internal",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "my_optind >= argc | k+1<my_optind | my_optind > argc",
   "guard_count": 3,
   "control_structures": "IF:149,ELSE:150,IF:151,IF:152,IF:154,IF:159,ELSE:165,IF:165,IF:171,ELSE:172,IF:172,FOR:176"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[]*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "argc",
   "argv"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b35993db095c14be95fc0f40b96b44e2850b7990/ARVO-42517374/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b35993db095c.cpg",
   "testcase_size": 1248
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 432,
   "loc_kind": "stack_frame",
   "dedup_token": "authentic_parse_size--authentic_get_tagged_data--authentic_parse_credential_data"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "argv[k]=argv[k+1]",
     "line": 185
    },
    {
     "code": "argv[--my_optind]=tmp",
     "line": 186
    }
   ],
   "entity_decl": {
    "line": 142,
    "type": "char[]*"
   },
   "entity_name_cpg": "argv",
   "func_lines": [
    142,
    267
   ],
   "func_params": {
    "names": [
     "argc",
     "argv",
     "shortopts",
     "longopts",
     "longind",
     "long_only"
    ],
    "types": [
     "int",
     "char[]*",
     "char*",
     "option*",
     "int*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "(colon_mode = *shortopts) == ':'",
     "line": 151
    },
    {
     "code": "(mode = shortopts[shortoff]) == '+'",
     "line": 152
    },
    {
     "code": "mode == '-'",
     "line": 152
    },
    {
     "code": "colon_mode != ':'",
     "line": 154
    },
    {
     "code": "(colon_mode = shortopts[shortoff]) == ':'",
     "line": 154
    },
    {
     "code": "argv[my_optind][0] == '-'",
     "line": 160
    },
    {
     "code": "argv[my_optind][1] == '-'",
     "line": 161
    },
    {
     "code": "argv[my_optind][2] == '\\0'",
     "line": 162
    },
    {
     "code": "argv[my_optind][0] != '-'",
     "line": 165
    },
    {
     "code": "argv[my_optind][1] == '\\0'",
     "line": 166
    },
    {
     "code": "mode == '+'",
     "line": 171
    },
    {
     "code": "mode == '-'",
     "line": 172
    },
    {
     "code": "i<argc",
     "line": 176
    },
    {
     "code": "argv[i][0] == '-'",
     "line": 176
    },
    {
     "code": "argv[i][1] != '\\0'",
     "line": 177
    },
    {
     "code": "i > j",
     "line": 182
    },
    {
     "code": "k+1<my_optind",
     "line": 184
    },
    {
     "code": "argv[my_optind][1] != '-'",
     "line": 190
    },
    {
     "code": "(my_optopt = argv[my_optind][1]) != '-'",
     "line": 196
    },
    {
     "code": "shortopts[ind] == ':'",
     "line": 201
    },
    {
     "code": "c == 'W'",
     "line": 202
    },
    {
     "code": "shortopts[ind] == ';'",
     "line": 202
    },
    {
     "code": "shortopts[++ind] == ':'",
     "line": 203
    },
    {
     "code": "my_optopt == c",
     "line": 205
    },
    {
     "code": "argv[my_optind][1] != '-'",
     "line": 208
    },
    {
     "code": "argv[my_optind][charind] != '\\0'",
     "line": 210
    },
    {
     "code": "argv[my_optind][charind] != '='",
     "line": 211
    },
    {
     "code": "strlen(longopts[ind].name) == (size_t) (charind - offset)",
     "line": 214
    },
    {
     "code": "strncmp(longopts[ind].name,",
     "line": 215
    },
    {
     "code": "strncmp(longopts[ind].name,",
     "line": 219
    },
    {
     "code": "hits == 1",
     "line": 222
    },
    {
     "code": "argv[my_optind][charind] == '='",
     "line": 225
    },
    {
     "code": "longopts[found].has_arg == 0",
     "line": 226
    },
    {
     "code": "longopts[found].has_arg == 1",
     "line": 236
    },
    {
     "code": "colon_mode == ':'",
     "line": 238
    },
    {
     "code": "offset == 1",
     "line": 251
    },
    {
     "code": "my_optind > argc",
     "line": 265
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "(argv[my_optind][0] == '-') &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "(argv[my_optind][0] == '-') &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "argv[my_optind][0] == '-'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "argv[my_optind][0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "argv[my_optind]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "argv",
    "my_optind"
   ],
   "osv_id": "ARVO-42517374",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "authentic_parse_size"
  }
 },
 {
  "osv_id": "ARVO-42517499",
  "project": "kimageformats",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "x",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/kimageformats/src/imageformats/raw.cpp",
    "line": 608,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "size_expr_cpg": "avif ;; AVIF_PLANES_YUV",
   "size_expr_cpg_callee": "avifImageAllocatePlanes"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 608,
    "fn": "(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)",
    "code": "x = 0 | x < tmpgrayimage.width() | tmpgrayimage.width() | x++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)",
    "file": "/src/kimageformats/src/imageformats/raw.cpp",
    "line": 608
   },
   "code": "x = 0 | x < tmpgrayimage.width() | tmpgrayimage.width() | x++",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "write",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "x < tmpgrayimage.width() | x < tmpgrayimage.width()",
   "guard_count": 2,
   "control_structures": "IF:468,IF:473,IF:474,IF:479,IF:484,ELSE:487,IF:493,IF:499,IF:500,ELSE:502,SWITCH:519,BREAK:525"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "image"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/kimageformats/address/d881a7bbb1562af383bbb6ca20340ad739fb0d13/ARVO-42517499/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_d881a7bbb156.cpg",
   "testcase_size": 471
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_offset": 512,
   "loc_kind": "stack_frame",
   "dedup_token": "LibRaw::xtrans_interpolate(int)--LibRaw::dcraw_process()--(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "x = 0",
     "line": 597
    },
    {
     "code": "x = 0",
     "line": 608
    }
   ],
   "entity_decl": {
    "line": 597,
    "type": "int"
   },
   "entity_name_cpg": "x",
   "func_lines": [
    466,
    828
   ],
   "func_params": {
    "names": [
     "this",
     "image"
    ],
    "types": [
     "QAVIFHandler",
     "QImage&"
    ]
   },
   "guards": [
    {
     "code": "image.format() == QImage::Format_Invalid",
     "line": 468
    },
    {
     "code": "image.width() > 0",
     "line": 473
    },
    {
     "code": "image.height() > 0",
     "line": 473
    },
    {
     "code": "image.width() > 65535",
     "line": 474
    },
    {
     "code": "image.height() > 65535",
     "line": 474
    },
    {
     "code": "image.width() > ((16384 * 16384) / image.height())",
     "line": 479
    },
    {
     "code": "image.width() > 32768",
     "line": 484
    },
    {
     "code": "image.height() > 32768",
     "line": 484
    },
    {
     "code": "image.depth() > 32",
     "line": 547
    },
    {
     "code": "maxQuantizer > 20",
     "line": 556
    },
    {
     "code": "maxQuantizer > 40",
     "line": 558
    },
    {
     "code": "save_depth > 8",
     "line": 564
    },
    {
     "code": "save_depth > 8",
     "line": 593
    },
    {
     "code": "y < tmpgrayimage.height()",
     "line": 594
    },
    {
     "code": "x < tmpgrayimage.width()",
     "line": 597
    },
    {
     "code": "y < tmpgrayimage.height()",
     "line": 605
    },
    {
     "code": "x < tmpgrayimage.width()",
     "line": 608
    },
    {
     "code": "save_depth > 8",
     "line": 617
    },
    {
     "code": "maxQuantizer < 20",
     "line": 634
    },
    {
     "code": "maxQuantizer < 10",
     "line": 635
    },
    {
     "code": "qAbs(tmpcolorimage.colorSpace().gamma() - 2.2f) < 0.1f",
     "line": 676
    },
    {
     "code": "qAbs(tmpcolorimage.colorSpace().gamma() - 2.8f) < 0.1f",
     "line": 679
    },
    {
     "code": "primaries_to_save == 2",
     "line": 698
    },
    {
     "code": "transfer_to_save == 2",
     "line": 698
    },
    {
     "code": "save_depth == 8",
     "line": 703
    },
    {
     "code": "primaries_to_save == 2",
     "line": 712
    },
    {
     "code": "transfer_to_save != 2",
     "line": 712
    },
    {
     "code": "primaries_to_save != 2",
     "line": 731
    },
    {
     "code": "transfer_to_save == 2",
     "line": 731
    },
    {
     "code": "iccprofile.size() > 0",
     "line": 744
    },
    {
     "code": "pixel_format == AVIF_PIXEL_FORMAT_YUV444",
     "line": 749
    },
    {
     "code": "iccprofile.size() > 0",
     "line": 758
    },
    {
     "code": "save_depth > 8",
     "line": 767
    },
    {
     "code": "res != AVIF_RESULT_OK",
     "line": 790
    },
    {
     "code": "res == AVIF_RESULT_OK",
     "line": 813
    },
    {
     "code": "status > 0",
     "line": 817
    },
    {
     "code": "status == -1",
     "line": 819
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "x = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "x < tmpgrayimage.width()",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "tmpgrayimage.width()",
     "name": "width",
     "nargs": 1
    },
    {
     "code": "x++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "x",
    "tmpgrayimage"
   ],
   "osv_id": "ARVO-42517499",
   "sites": [
    {
     "args": "avif ;; AVIF_PLANES_YUV",
     "callee": "avifImageAllocatePlanes",
     "code": "avifImageAllocatePlanes(avif, AVIF_PLANES_YUV)",
     "line": 572
    },
    {
     "args": "&raw",
     "callee": "avifRWDataFree",
     "code": "avifRWDataFree(&raw)",
     "line": 815
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)"
  }
 },
 {
  "osv_id": "ARVO-42518213",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 449,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 467,
    "fn": "sc_path_print",
    "code": "snprintf(buf + strlen(buf), buflen - strlen(buf), \"%02x\" | buf + strlen(buf) | strlen(buf) | buflen - strlen(buf)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_path_print",
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 467
   },
   "code": "snprintf(buf + strlen(buf), buflen - strlen(buf), \"%02x\" | buf + strlen(buf) | strlen(buf) | buflen - strlen(buf)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_path_print",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "buf == NULL | path == NULL | buflen < path->len * 2 + path->aid.len * 2 + 3",
   "guard_count": 5,
   "control_structures": "IF:453,IF:456,IF:460,FOR:461,FOR:466,IF:468"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf",
   "buflen",
   "path"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42518213/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 4945
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 1248,
   "loc_kind": "stack_frame",
   "dedup_token": "sc_path_print--sc_select_file--sc_pkcs15init_rmdir"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf[0] = '\\0'",
     "line": 459
    }
   ],
   "entity_decl": {
    "line": 449,
    "type": "char*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    449,
    472
   ],
   "func_params": {
    "names": [
     "buf",
     "buflen",
     "path"
    ],
    "types": [
     "char*",
     "size_t",
     "sc_path_t*"
    ]
   },
   "guards": [
    {
     "code": "buf == NULL",
     "line": 453
    },
    {
     "code": "path == NULL",
     "line": 453
    },
    {
     "code": "buflen < path->len * 2 + path->aid.len * 2 + 3",
     "line": 456
    },
    {
     "code": "i < path->aid.len",
     "line": 461
    },
    {
     "code": "i < path->len",
     "line": 466
    },
    {
     "code": "path->type == SC_PATH_TYPE_DF_NAME",
     "line": 468
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "snprintf(buf + strlen(buf), buflen - strlen(buf), \"%02x\", path->value[i])",
     "name": "snprintf",
     "nargs": 4
    },
    {
     "code": "buf + strlen(buf)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "strlen(buf)",
     "name": "strlen",
     "nargs": 1
    },
    {
     "code": "buflen - strlen(buf)",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "strlen(buf)",
     "name": "strlen",
     "nargs": 1
    },
    {
     "code": "path->value[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "path->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "buflen",
    "path",
    "i"
   ],
   "osv_id": "ARVO-42518213",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_path_print"
  }
 },
 {
  "osv_id": "ARVO-42518451",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "zeroBuffer",
   "kind": "array",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/muscle.c",
    "line": 128,
    "size": null,
    "type": "u8[512]"
   }
  },
  "alloc": {
   "size_expr_cpg": "MSC_MAX_APDU",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 132,
    "fn": "msc_zero_object",
    "code": "memset(zeroBuffer, 0, max_write_unit)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "msc_zero_object",
    "file": "/src/opensc/src/libopensc/muscle.c",
    "line": 132
   },
   "code": "memset(zeroBuffer, 0, max_write_unit)",
   "access": {
    "dir": "WRITE",
    "width": 65526,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "msc_zero_object",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "(dataLength - i) < (max_write_unit)",
   "guard_count": 1,
   "control_structures": "FOR:133,DO:135,IF:135"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8[512]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42518451/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 104
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 560,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memset--msc_zero_object--msc_create_object"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "zeroBuffer[MSC_MAX_APDU]",
     "line": 128
    }
   ],
   "entity_decl": {
    "line": 128,
    "type": "u8[512]"
   },
   "entity_name_cpg": "zeroBuffer",
   "func_lines": [
    126,
    138
   ],
   "func_params": {
    "names": [
     "card",
     "objectId",
     "dataLength"
    ],
    "types": [
     "sc_card_t*",
     "msc_id",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "card->max_send_size > 0",
     "line": 130
    },
    {
     "code": "i < dataLength",
     "line": 133
    },
    {
     "code": "(dataLength - i) < (max_write_unit)",
     "line": 134
    },
    {
     "code": "_ret < 0",
     "line": 135
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memset(zeroBuffer, 0, max_write_unit)",
     "name": "memset",
     "nargs": 3
    }
   ],
   "line_ids": [
    "zeroBuffer",
    "max_write_unit"
   ],
   "osv_id": "ARVO-42518451",
   "sites": [
    {
     "args": "MSC_MAX_APDU",
     "callee": "<operator>.alloc",
     "code": "zeroBuffer[MSC_MAX_APDU]",
     "line": 128
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "msc_zero_object"
  }
 },
 {
  "osv_id": "ARVO-42518779",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "path",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "line": 657,
    "size": null,
    "type": "sc_path"
   }
  },
  "alloc": {
   "size_expr_cpg": "1024",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 679,
    "fn": "sc_pkcs15init_rmdir",
    "code": "path.value[path.len-1] = buffer[2*nfids+1] | path.value[path.len-1] | path.value | path.len-1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15init_rmdir",
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "line": 679
   },
   "code": "path.value[path.len-1] = buffer[2*nfids+1] | path.value[path.len-1] | path.value | path.len-1",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_pkcs15init_rmdir",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:661,IF:665,IF:667,IF:670,WHILE:677,IF:681,IF:682,CONTINUE:683,BREAK:684,IF:690,IF:698,IF:702"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_path",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "p15card",
   "df"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42518779/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 5386
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 1183,
   "loc_kind": "stack_frame",
   "dedup_token": "sc_pkcs15init_rmdir--sc_pkcs15init_erase_card_recursively--cardos_erase"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "path = df->path",
     "line": 673
    },
    {
     "code": "path.value[path.len-2] = buffer[2*nfids]",
     "line": 678
    },
    {
     "code": "path.value[path.len-1] = buffer[2*nfids+1]",
     "line": 679
    },
    {
     "code": "path = df->path",
     "line": 695
    },
    {
     "code": "path.type = SC_PATH_TYPE_FILE_ID",
     "line": 712
    },
    {
     "code": "path.value[0] = df->id >> 8",
     "line": 713
    },
    {
     "code": "path.value[1] = df->id & 0xFF",
     "line": 714
    },
    {
     "code": "path.len = 2",
     "line": 715
    }
   ],
   "entity_decl": {
    "line": 657,
    "type": "sc_path"
   },
   "entity_name_cpg": "path",
   "func_lines": [
    651,
    724
   ],
   "func_params": {
    "names": [
     "p15card",
     "profile",
     "df"
    ],
    "types": [
     "sc_pkcs15_card*",
     "sc_profile*",
     "sc_file*"
    ]
   },
   "guards": [
    {
     "code": "df == NULL",
     "line": 661
    },
    {
     "code": "df->type == SC_FILE_TYPE_DF",
     "line": 665
    },
    {
     "code": "r < 0",
     "line": 667
    },
    {
     "code": "r < 0",
     "line": 670
    },
    {
     "code": "r < 0",
     "line": 681
    },
    {
     "code": "r == SC_ERROR_FILE_NOT_FOUND",
     "line": 682
    },
    {
     "code": "r < 0",
     "line": 690
    },
    {
     "code": "r < 0",
     "line": 698
    },
    {
     "code": "r < 0",
     "line": 702
    },
    {
     "code": "r < 0",
     "line": 708
    },
    {
     "code": "r < 0",
     "line": 719
    },
    {
     "code": "r != SC_ERROR_NOT_SUPPORTED",
     "line": 719
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "path.value[path.len-1] = buffer[2*nfids+1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "path.value[path.len-1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "path.value",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "path.len-1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "path.len",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "buffer[2*nfids+1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "2*nfids+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "2*nfids",
     "name": "<operator>.multiplication",
     "nargs": 2
    }
   ],
   "line_ids": [
    "path",
    "buffer",
    "nfids"
   ],
   "osv_id": "ARVO-42518779",
   "sites": [
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "buffer[1024]",
     "line": 656
    },
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 687
    },
    {
     "args": "parent",
     "callee": "sc_file_free",
     "code": "sc_file_free(parent)",
     "line": 703
    },
    {
     "args": "parent",
     "callee": "sc_file_free",
     "code": "sc_file_free(parent)",
     "line": 707
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_pkcs15init_rmdir"
  }
 },
 {
  "osv_id": "ARVO-42523836",
  "project": "flac",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 219,
    "type": "double",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 219,
    "fn": "dump_stats",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dump_stats",
    "file": "/src/flac/src/flac/analyze.c",
    "line": 219
   },
   "code": "p = stats->buckets[stats->peak_index].count",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dump_stats",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/flac/address/9382c5375bb66872cdedb0fd36e68e371fae8721/ARVO-42523836/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/flac_9382c5375bb6.cpg",
   "testcase_size": 126
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 1164,
   "loc_kind": "stack_frame",
   "dedup_token": "dump_stats--flac__analyze_frame--write_callback"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "p = stats->buckets[stats->peak_index].count",
     "line": 219
    }
   ],
   "entity_decl": {
    "line": 219,
    "type": "double"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    213,
    247
   ],
   "func_params": {
    "names": [
     "stats",
     "filename"
    ],
    "types": [
     "subframe_stats_t*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "0 == outfile",
     "line": 223
    },
    {
     "code": "i < stats->nbuckets",
     "line": 230
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "p = stats->buckets[stats->peak_index].count",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "stats->buckets[stats->peak_index].count",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "stats->buckets[stats->peak_index]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "stats->buckets",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "stats->peak_index",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p",
    "stats"
   ],
   "osv_id": "ARVO-42523836",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dump_stats"
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