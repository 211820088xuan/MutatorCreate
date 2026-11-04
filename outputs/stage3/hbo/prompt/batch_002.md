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
  "osv_id": "ARVO-398053010",
  "project": "net-snmp",
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
    "fn": "setup_engineID",
    "file": "/src/net-snmp/snmplib/snmpv3.c",
    "line": 587
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "1 ;; len",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "setup_engineID",
    "file": "/src/net-snmp/snmplib/snmpv3.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "setup_engineID",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-398053010/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "testcase_size": 301
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
   "loc_size": 1,
   "loc_offset": 2,
   "loc_kind": "region",
   "dedup_token": "setup_engineID--init_snmpv3_post_premib_config--snmp_call_callbacks",
   "overshoot_ratio": 2.0
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    469,
    711
   ],
   "func_params": {
    "names": [
     "eidp",
     "text"
    ],
    "types": [
     "u_char**",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "NULL != text",
     "line": 534
    },
    {
     "code": "NULL == text",
     "line": 543
    },
    {
     "code": "len == 0",
     "line": 583
    },
    {
     "code": "bufp == NULL",
     "line": 588
    },
    {
     "code": "localEngineIDType == ENGINEID_TYPE_NETSNMP_RND",
     "line": 592
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-398053010",
   "sites": [
    {
     "args": "1 ;; len",
     "callee": "calloc",
     "code": "calloc(1, len)",
     "line": 587
    },
    {
     "args": "engineID",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(engineID)",
     "line": 700
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "setup_engineID"
  }
 },
 {
  "osv_id": "ARVO-398067543",
  "project": "net-snmp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "cp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/net-snmp/snmplib/mib.c",
    "line": 2364,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/net-snmp/testing/fuzzing/snmp_parse_args_fuzzer.c",
    "line": 41
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2396,
    "fn": "snmp_in_options",
    "code": "cp = argv[optind++] | argv[optind++] | optind++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "snmp_in_options",
    "file": "/src/net-snmp/snmplib/mib.c",
    "line": 2396
   },
   "code": "cp = argv[optind++] | argv[optind++] | optind++",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "snmp_in_options",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:2366,SWITCH:2367,BREAK:2370,BREAK:2373,BREAK:2376,BREAK:2379,BREAK:2382,IF:2384,IF:2386,IF:2395,IF:2397"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "optarg",
   "argc",
   "argv"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-398067543/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "testcase_size": 151
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
   "loc_size": 16,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "snmp_in_options--netsnmp_parse_args--LLVMFuzzerTestOneInput",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cp = optarg",
     "line": 2366
    },
    {
     "code": "cp = argv[optind++]",
     "line": 2385
    },
    {
     "code": "cp = argv[optind++]",
     "line": 2396
    }
   ],
   "entity_decl": {
    "line": 2364,
    "type": "char*"
   },
   "entity_name_cpg": "cp",
   "func_lines": [
    2361,
    2414
   ],
   "func_params": {
    "names": [
     "optarg",
     "argc",
     "argv"
    ],
    "types": [
     "char*",
     "int",
     "char*const*"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "cp = argv[optind++]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "argv[optind++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "optind++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "cp",
    "argv",
    "optind"
   ],
   "osv_id": "ARVO-398067543",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "snmp_in_options"
  }
 },
 {
  "osv_id": "ARVO-399458050",
  "project": "net-snmp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "key",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 4505,
    "type": "u_char**",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "read_config_read_octet_string_const",
    "file": "/src/net-snmp/snmplib/read_config.c",
    "line": 2051
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "SNMP_MAXBUF_SMALL",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 4552,
    "fn": "usm_set_user_password",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "usm_set_user_password",
    "file": "/src/net-snmp/snmplib/snmpusm.c",
    "line": 4552
   },
   "code": "memset(*key, 0, *keyLen)",
   "access": {
    "dir": "WRITE",
    "width": 9,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "usm_set_user_password",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-399458050/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "testcase_size": 1432
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_size": 4,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--usm_set_user_password--usm_set_password",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "key = &user->authKey",
     "line": 4518
    },
    {
     "code": "key = &user->privKey",
     "line": 4522
    },
    {
     "code": "key = &user->authKey",
     "line": 4526
    },
    {
     "code": "key = &user->privKey",
     "line": 4530
    },
    {
     "code": "key = &user->authKey",
     "line": 4534
    },
    {
     "code": "key = &user->privKey",
     "line": 4538
    }
   ],
   "entity_decl": {
    "line": 4505,
    "type": "u_char**"
   },
   "entity_name_cpg": "key",
   "func_lines": [
    4498,
    4625
   ],
   "func_params": {
    "names": [
     "user",
     "token",
     "line"
    ],
    "types": [
     "usmUser*",
     "char*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "strcmp(token, \"userSetAuthPass\") == 0",
     "line": 4517
    },
    {
     "code": "strcmp(token, \"userSetPrivPass\") == 0",
     "line": 4521
    },
    {
     "code": "strcmp(token, \"userSetAuthKey\") == 0",
     "line": 4525
    },
    {
     "code": "strcmp(token, \"userSetPrivKey\") == 0",
     "line": 4529
    },
    {
     "code": "strcmp(token, \"userSetAuthLocalKey\") == 0",
     "line": 4533
    },
    {
     "code": "strcmp(token, \"userSetPrivLocalKey\") == 0",
     "line": 4537
    },
    {
     "code": "type == 0",
     "line": 4556
    },
    {
     "code": "cp == NULL",
     "line": 4560
    },
    {
     "code": "ret != SNMPERR_SUCCESS",
     "line": 4567
    },
    {
     "code": "userKey == user->privKey",
     "line": 4573
    },
    {
     "code": "userKey == user->authKey",
     "line": 4576
    },
    {
     "code": "type == 1",
     "line": 4581
    },
    {
     "code": "cp == NULL",
     "line": 4584
    },
    {
     "code": "type < 2",
     "line": 4590
    },
    {
     "code": "ret != SNMPERR_SUCCESS",
     "line": 4596
    },
    {
     "code": "cp == NULL",
     "line": 4612
    },
    {
     "code": "key == &user->privKey",
     "line": 4618
    },
    {
     "code": "SNMPERR_SUCCESS != ret",
     "line": 4620
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memset(*key, 0, *keyLen)",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "*key",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*keyLen",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "key",
    "keyLen"
   ],
   "osv_id": "ARVO-399458050",
   "sites": [
    {
     "args": "SNMP_MAXBUF_SMALL",
     "callee": "<operator>.alloc",
     "code": "userKey[SNMP_MAXBUF_SMALL]",
     "line": 4507
    },
    {
     "args": "*key",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(*key)",
     "line": 4553
    },
    {
     "args": "SNMP_MAXBUF_SMALL",
     "callee": "malloc",
     "code": "malloc(SNMP_MAXBUF_SMALL)",
     "line": 4591
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "usm_set_user_password"
  }
 },
 {
  "osv_id": "ARVO-420198855",
  "project": "readstat",
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
    "fn": "build_lookup_table",
    "file": "/src/readstat/src/spss/readstat_sav_parse.rl",
    "line": 55
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "8+1",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 121,
    "fn": "sav_parse_long_variable_names_record",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sav_parse_long_variable_names_record",
    "file": "/src/readstat/src/spss/readstat_sav_parse.rl",
    "line": 121
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sav_parse_long_variable_names_record",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/readstat/address/24de678e9439fff01b27c0bc8e8b745369888664/ARVO-420198855/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/readstat_24de678e9439.cpg",
   "testcase_size": 237
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
   "loc_size": 40,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__interceptor_strcmp--sav_parse_long_variable_names_record--sav_parse_records_pass2",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    284,
    527
   ],
   "func_params": {
    "names": [
     "data",
     "count",
     "ctx"
    ],
    "types": [
     "void*",
     "int",
     "sav_ctx_t*"
    ]
   },
   "guards": [
    {
     "code": "p == pe",
     "line": 318
    },
    {
     "code": "cs == 0",
     "line": 320
    },
    {
     "code": "_klen > 0",
     "line": 327
    },
    {
     "code": "_upper < _lower",
     "line": 332
    },
    {
     "code": "(*p) < *_mid",
     "line": 336
    },
    {
     "code": "(*p) > *_mid",
     "line": 338
    },
    {
     "code": "_klen > 0",
     "line": 350
    },
    {
     "code": "_upper < _lower",
     "line": 355
    },
    {
     "code": "(*p) < _mid[0]",
     "line": 359
    },
    {
     "code": "(*p) > _mid[1]",
     "line": 361
    },
    {
     "code": "_sav_long_variable_parse_trans_actions[_trans] == 0",
     "line": 375
    },
    {
     "code": "_nacts-- > 0",
     "line": 380
    },
    {
     "code": "strcmp(iter_match->name, temp_key) == 0",
     "line": 414
    },
    {
     "code": "strcmp(iter_match->name, temp_key) == 0",
     "line": 420
    },
    {
     "code": "iter_match - table < var_count",
     "line": 420
    },
    {
     "code": "cs == 0",
     "line": 448
    },
    {
     "code": "++p != pe",
     "line": 450
    },
    {
     "code": "p == eof",
     "line": 453
    },
    {
     "code": "__nacts-- > 0",
     "line": 457
    },
    {
     "code": "strcmp(iter_match->name, temp_key) == 0",
     "line": 474
    },
    {
     "code": "strcmp(iter_match->name, temp_key) == 0",
     "line": 480
    },
    {
     "code": "iter_match - table < var_count",
     "line": 480
    },
    {
     "code": "cs < 11",
     "line": 510
    },
    {
     "code": "p != pe",
     "line": 510
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-420198855",
   "sites": [
    {
     "args": "8+1",
     "callee": "<operator>.alloc",
     "code": "temp_key[8+1]",
     "line": 289
    },
    {
     "args": "64+1",
     "callee": "<operator>.alloc",
     "code": "temp_val[64+1]",
     "line": 290
    },
    {
     "args": "8192",
     "callee": "<operator>.alloc",
     "code": "error_buf[8192]",
     "line": 294
    },
    {
     "args": "table",
     "callee": "free",
     "code": "free(table)",
     "line": 521
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sav_parse_long_variable_names_record"
  }
 },
 {
  "osv_id": "ARVO-422832557",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "msg",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 979,
    "size": null,
    "type": "char[64]"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 5792732f783158c66fb4f3756458ca24e46e827d)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "16",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 981,
    "fn": "ndpi_check_http_server",
    "code": "snprintf(msg, sizeof(msg), \"Suspicious Agent [%s]\", serv | sizeof(msg)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_http_server",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 981
   },
   "code": "snprintf(msg, sizeof(msg), \"Suspicious Agent [%s]\", serv | sizeof(msg)",
   "access": {
    "dir": "READ",
    "width": 11,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_http_server",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:941,IF:942,IF:945,FOR:950,IF:954,IF:958,IF:959,ELSE:962,ELSE:965,IF:965,IF:966,ELSE:969"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/a9433488cd090a5da68179b52bb8c200d42649fa/ARVO-422832557/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_a9433488cd09.cpg",
   "testcase_size": 48
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
   "loc_size": 48,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--__interceptor_vsnprintf--__interceptor_snprintf",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "msg[64]",
     "line": 956
    },
    {
     "code": "msg[64]",
     "line": 979
    }
   ],
   "entity_decl": {
    "line": 956,
    "type": "char[64]"
   },
   "entity_name_cpg": "msg",
   "func_lines": [
    938,
    989
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
     "code": "server[0] != '\\0'",
     "line": 941
    },
    {
     "code": "server_len > 7",
     "line": 942
    },
    {
     "code": "strncasecmp(server, \"Apache/\", off = 7) == 0",
     "line": 945
    },
    {
     "code": "strncasecmp(server, \"nginx/\", off = 6) == 0",
     "line": 946
    },
    {
     "code": "i<server_len",
     "line": 950
    },
    {
     "code": "j<sizeof(buf)-1",
     "line": 950
    },
    {
     "code": "server[i] == '.'",
     "line": 951
    },
    {
     "code": "sscanf(buf, \"%d.%d.%d\", &a, &b, &c) == 3",
     "line": 954
    },
    {
     "code": "off == 7",
     "line": 958
    },
    {
     "code": "version < MIN_APACHE_VERSION",
     "line": 958
    },
    {
     "code": "off == 6",
     "line": 965
    },
    {
     "code": "version < MIN_NGINX_VERSION",
     "line": 965
    },
    {
     "code": "i<server_len",
     "line": 977
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "snprintf(msg, sizeof(msg), \"Suspicious Agent [%s]\", server)",
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
    "server"
   ],
   "osv_id": "ARVO-422832557",
   "sites": [
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "buf[16] = { '\\0' }",
     "line": 948
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "msg[64]",
     "line": 956
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "msg[64]",
     "line": 979
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
  "osv_id": "ARVO-42470093",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "scripts",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-layout-gsub-table.hh",
    "line": 752,
    "size": null,
    "type": "hb_tag_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "hb_blob_t::try_make_writable()",
    "file": "/src/harfbuzz/src/hb-blob.cc",
    "line": 464
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 778,
    "fn": "OT::LigatureSubstFormat1::closure(OT::hb_closure_context_t*) const",
    "code": "*scripts",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OT::LigatureSubstFormat1::closure(OT::hb_closure_context_t*) const",
    "file": "/src/harfbuzz/src/hb-ot-layout-gsub-table.hh",
    "line": 778
   },
   "code": "*scripts",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "hb_ot_layout_collect_features",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:757,FOR:763,ELSE:772,FOR:773,IF:776"
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_tag_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "scripts"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a26806801005c28115ae9e48bdcf3bbbc1bcd767/ARVO-42470093/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a26806801005.cpg",
   "testcase_size": 2648
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
   "dedup_token": "OT::LigatureSubstFormat1::closure(OT::hb_closure_context_t*) const--_hb_void_t const* OT::hb_closure_context_t::dispatch<OT::LigatureSubstFormat1>(OT::LigatureS"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 752,
    "type": "hb_tag_t*"
   },
   "entity_name_cpg": "scripts",
   "func_lines": [
    749,
    788
   ],
   "func_params": {
    "names": [
     "face",
     "table_tag",
     "scripts",
     "languages",
     "features",
     "feature_indexes"
    ],
    "types": [
     "hb_face_t*",
     "hb_tag_t",
     "hb_tag_t*",
     "hb_tag_t*",
     "hb_tag_t*",
     "hb_set_t*"
    ]
   },
   "guards": [
    {
     "code": "script_index < count",
     "line": 763
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "*scripts",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "scripts"
   ],
   "osv_id": "ARVO-42470093",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OT::LigatureSubstFormat1::closure(OT::hb_closure_context_t*) const"
  }
 },
 {
  "osv_id": "ARVO-42470096",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "line": 948,
    "size": null,
    "type": "hb_buffer_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 562
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 952,
    "fn": "OT::Coverage::intersects(hb_set_t const*) const",
    "code": "unlikely (hb_object_is_inert (buffer)) | hb_object_is_inert(buffer) | hb_object_is_inert(buffer)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OT::Coverage::intersects(hb_set_t const*) const",
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "line": 952
   },
   "code": "unlikely (hb_object_is_inert (buffer)) | hb_object_is_inert(buffer) | hb_object_is_inert(buffer)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "hb_buffer_set_direction",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:952"
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_buffer_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buffer"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a26806801005c28115ae9e48bdcf3bbbc1bcd767/ARVO-42470096/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a26806801005.cpg",
   "testcase_size": 64
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
   "dedup_token": "OT::Coverage::intersects(hb_set_t const*) const--OT::ContextFormat2::closure(OT::hb_closure_context_t*) const--_hb_void_t const* OT::hb_closure_context_t::dispa"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buffer->props.direction = direction",
     "line": 955
    }
   ],
   "entity_decl": {
    "line": 948,
    "type": "hb_buffer_t*"
   },
   "entity_name_cpg": "buffer",
   "func_lines": [
    947,
    956
   ],
   "func_params": {
    "names": [
     "buffer",
     "direction"
    ],
    "types": [
     "hb_buffer_t*",
     "hb_direction_t"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "unlikely (hb_object_is_inert (buffer))",
     "name": "unlikely",
     "nargs": 1
    },
    {
     "code": "hb_object_is_inert(buffer)",
     "name": "hb_object_is_inert",
     "nargs": 1
    },
    {
     "code": "hb_object_is_inert(buffer)",
     "name": "hb_object_is_inert",
     "nargs": 1
    }
   ],
   "line_ids": [
    "buffer"
   ],
   "osv_id": "ARVO-42470096",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OT::Coverage::intersects(hb_set_t const*) const"
  }
 },
 {
  "osv_id": "ARVO-42470250",
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
    "fn": "r_buf_set_bytes",
    "file": "/src/radare2/libr/util/buf.c",
    "line": 341
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 33,
    "fn": "r_bin_mdmp_get_mem_info",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "r_bin_mdmp_get_mem_info",
    "file": "/src/radare2/libr/bin/format/mdmp/mdmp.c",
    "line": 33
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "r_bin_mdmp_get_mem_info",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/eccc36f6b2df1d99bf0dcd09faccba8b3b892e0a/ARVO-42470250/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_eccc36f6b2df.cpg",
   "testcase_size": 1720
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
   "dedup_token": "r_bin_mdmp_get_mem_info--r_bin_mdmp_get_srwx--sections"
  },
  "deep": {
   "osv_id": "ARVO-42470250"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "r_bin_mdmp_get_mem_info"
  }
 },
 {
  "osv_id": "ARVO-42470379",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 652,
    "size": null,
    "type": "char**"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 655,
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "code": "(*pp)++ | *pp",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 655
   },
   "code": "(*pp)++ | *pp",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_space",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:654"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "pp",
   "end"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/ca746f261e1e54cec2f9c8bc7a6f930491e19418/ARVO-42470379/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_ca746f261e1e.cpg",
   "testcase_size": 256
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
   "dedup_token": "BEInt<unsigned short, 2>::operator unsigned short() const--OT::Offset<OT::IntType<unsigned short, 2u>, true>::is_null() const--OT::OffsetTo<OT::ArrayOfM1<OT::Re"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 652,
    "type": "char**"
   },
   "entity_name_cpg": "pp",
   "func_lines": [
    651,
    657
   ],
   "func_params": {
    "names": [
     "pp",
     "end"
    ],
    "types": [
     "char**",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "*pp < end",
     "line": 654
    }
   ],
   "line_call_count": 2,
   "line_calls": [
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
    "pp"
   ],
   "osv_id": "ARVO-42470379",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "BEInt<unsigned short, 2>::operator unsigned short() const"
  }
 },
 {
  "osv_id": "ARVO-42470538",
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
    "fn": "r_buf_set_bytes",
    "file": "/src/radare2/libr/util/buf.c",
    "line": 341
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2128,
    "fn": "r_str_utf16_to_utf8",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "r_str_utf16_to_utf8",
    "file": "/src/radare2/libr/util/str.c",
    "line": 2128
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "r_str_utf16_to_utf8",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/49b9ffcf9d21745146407ee2701c25eb120a70e3/ARVO-42470538/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_49b9ffcf9d21.cpg",
   "testcase_size": 527
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
   "dedup_token": "r_str_utf16_to_utf8--sections--r_bin_object_set_items"
  },
  "deep": {
   "osv_id": "ARVO-42470538"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "r_str_utf16_to_utf8"
  }
 },
 {
  "osv_id": "ARVO-42470938",
  "project": "openvswitch",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ds",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2515,
    "type": "ds*",
    "size": null
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "xrealloc",
    "file": "/src/openvswitch/lib/util.c",
    "line": 134
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2527,
    "fn": "format_generic_odp_key",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "format_generic_odp_key",
    "file": "/src/openvswitch/lib/odp-util.c",
    "line": 2527
   },
   "code": "ds_put_format(ds, \"%02x\", unspec[i])",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "format_generic_odp_key",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/bc9bbc4ea2645e5bbb3c02d986f26fdc83283d72/ARVO-42470938/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_bc9bbc4ea264.cpg",
   "testcase_size": 47
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
   "shadow_legend_size": 0,
   "dedup_token": "format_generic_odp_key--check_attr_len--format_odp_key_attr"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 2515,
    "type": "ds*"
   },
   "entity_name_cpg": "ds",
   "func_lines": [
    2514,
    2530
   ],
   "func_params": {
    "names": [
     "a",
     "ds"
    ],
    "types": [
     "nlattr*",
     "ds*"
    ]
   },
   "guards": [
    {
     "code": "i < len",
     "line": 2523
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "ds_put_format(ds, \"%02x\", unspec[i])",
     "name": "ds_put_format",
     "nargs": 3
    },
    {
     "code": "unspec[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ds",
    "unspec",
    "i"
   ],
   "osv_id": "ARVO-42470938",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "format_generic_odp_key"
  }
 },
 {
  "osv_id": "ARVO-42470972",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "v",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 688,
    "size": null,
    "type": "unsigned int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 557
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "32",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 693,
    "fn": "BEInt<unsigned int, 4>::operator unsigned int() const",
    "code": "v = strtol (p, &pend, 0) | strtol (p, &pend, 0) | &pend",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "BEInt<unsigned int, 4>::operator unsigned int() const",
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 693
   },
   "code": "v = strtol (p, &pend, 0) | strtol (p, &pend, 0) | &pend",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_uint",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "p == pend",
   "guard_count": 1,
   "control_structures": "IF:694"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "end"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/4035158de46ce373b7521daf61c5b6df83312968/ARVO-42470972/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_4035158de46c.cpg",
   "testcase_size": 28
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
   "dedup_token": "BEInt<unsigned int, 4>::operator unsigned int() const--OT::kern::has_data() const--hb_ot_layout_has_kerning(hb_face_t*)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "v = strtol (p, &pend, 0)",
     "line": 693
    }
   ],
   "entity_decl": {
    "line": 688,
    "type": "unsigned int"
   },
   "entity_name_cpg": "v",
   "func_lines": [
    678,
    700
   ],
   "func_params": {
    "names": [
     "pp",
     "end",
     "pv"
    ],
    "types": [
     "char**",
     "char*",
     "unsigned int*"
    ]
   },
   "guards": [
    {
     "code": "p == pend",
     "line": 694
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "v = strtol (p, &pend, 0)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "strtol (p, &pend, 0)",
     "name": "strtol",
     "nargs": 3
    },
    {
     "code": "&pend",
     "name": "<operator>.addressOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "v",
    "p",
    "pend"
   ],
   "osv_id": "ARVO-42470972",
   "sites": [
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "buf[32]",
     "line": 681
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "BEInt<unsigned int, 4>::operator unsigned int() const"
  }
 },
 {
  "osv_id": "ARVO-42471100",
  "project": "libgit2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "search",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 76,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 557
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "&alloc_len ;; text_len ;; 1",
   "size_expr_cpg_callee": "GITERR_CHECK_ALLOC_ADD"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 142,
    "fn": "tag_parse",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tag_parse",
    "file": "/src/libgit2/src/tag.c",
    "line": 142
   },
   "code": "search = strstr(buffer, \"\\n\\n\")",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tag_parse",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471100/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_7615794c1256.cpg",
   "testcase_size": 73
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "StrstrCheck(void*, char*, char const*, char const*)--__interceptor_strstr--tag_parse"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "search = memchr(buffer, '\\n', buffer_end - buffer)",
     "line": 114
    },
    {
     "code": "search = strstr(buffer, \"\\n\\n\")",
     "line": 142
    }
   ],
   "entity_decl": {
    "line": 76,
    "type": "char*"
   },
   "entity_name_cpg": "search",
   "func_lines": [
    68,
    160
   ],
   "func_params": {
    "names": [
     "tag",
     "buffer",
     "buffer_end"
    ],
    "types": [
     "git_tag*",
     "char*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "git_oid__parse(&tag->target, &buffer, buffer_end, \"object \") < 0",
     "line": 78
    },
    {
     "code": "memcmp(buffer, \"type \", 5) != 0",
     "line": 84
    },
    {
     "code": "i < ARRAY_SIZE(tag_types)",
     "line": 90
    },
    {
     "code": "memcmp(buffer, tag_types[i], type_length) == 0",
     "line": 96
    },
    {
     "code": "tag->type == GIT_OBJ_BAD",
     "line": 103
    },
    {
     "code": "memcmp(buffer, \"tag \", 4) != 0",
     "line": 109
    },
    {
     "code": "search == NULL",
     "line": 115
    },
    {
     "code": "tag->tag_name == NULL",
     "line": 122
    },
    {
     "code": "buffer < buffer_end",
     "line": 130
    },
    {
     "code": "*buffer != '\\n'",
     "line": 130
    },
    {
     "code": "tag->tagger == NULL",
     "line": 132
    },
    {
     "code": "git_signature__parse(tag->tagger, &buffer, buffer_end, \"tagger \", '\\n') < 0",
     "line": 134
    },
    {
     "code": "buffer < buffer_end",
     "line": 139
    },
    {
     "code": "*buffer != '\\n'",
     "line": 141
    },
    {
     "code": "tag->message == NULL",
     "line": 153
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "search = strstr(buffer, \"\\n\\n\")",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "strstr(buffer, \"\\n\\n\")",
     "name": "strstr",
     "nargs": 2
    }
   ],
   "line_ids": [
    "search",
    "buffer"
   ],
   "osv_id": "ARVO-42471100",
   "sites": [
    {
     "args": "&alloc_len ;; text_len ;; 1",
     "callee": "GITERR_CHECK_ALLOC_ADD",
     "code": "GITERR_CHECK_ALLOC_ADD(&alloc_len, text_len, 1)",
     "line": 120
    },
    {
     "args": "alloc_len",
     "callee": "git__malloc",
     "code": "git__malloc(alloc_len)",
     "line": 121
    },
    {
     "args": "tag->tag_name",
     "callee": "GITERR_CHECK_ALLOC",
     "code": "GITERR_CHECK_ALLOC(tag->tag_name)",
     "line": 122
    },
    {
     "args": "",
     "callee": "git__malloc",
     "code": "git__malloc(sizeof(git_signature))",
     "line": 131
    },
    {
     "args": "tag->tagger",
     "callee": "GITERR_CHECK_ALLOC",
     "code": "GITERR_CHECK_ALLOC(tag->tagger)",
     "line": 132
    },
    {
     "args": "&alloc_len ;; text_len ;; 1",
     "callee": "GITERR_CHECK_ALLOC_ADD",
     "code": "GITERR_CHECK_ALLOC_ADD(&alloc_len, text_len, 1)",
     "line": 151
    },
    {
     "args": "alloc_len",
     "callee": "git__malloc",
     "code": "git__malloc(alloc_len)",
     "line": 152
    },
    {
     "args": "tag->message",
     "callee": "GITERR_CHECK_ALLOC",
     "code": "GITERR_CHECK_ALLOC(tag->message)",
     "line": 153
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tag_parse"
  }
 },
 {
  "osv_id": "ARVO-42471108",
  "project": "libgit2",
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
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 557
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "len",
   "size_expr_cpg_callee": "__coverity_alloc__"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 506,
    "fn": "git_buf_vprintf",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "git_buf_vprintf",
    "file": "/src/libgit2/src/buffer.c",
    "line": 506
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 13,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "git_buf_vprintf",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471108/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_7615794c1256.cpg",
   "testcase_size": 71
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--vsnprintf--git_buf_vprintf"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    42,
    58
   ],
   "func_params": {
    "names": [
     "buf",
     "format",
     "ap"
    ],
    "types": [
     "git_buf*",
     "char*",
     "va_list"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42471108",
   "sites": [
    {
     "args": "len",
     "callee": "__coverity_alloc__",
     "code": "__coverity_alloc__(len)",
     "line": 53
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "git_buf_vprintf"
  }
 },
 {
  "osv_id": "ARVO-42471111",
  "project": "libgit2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "s",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 259,
    "type": "int",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 557
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 262,
    "fn": "prefixcmp",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "prefixcmp",
    "file": "/src/libgit2/src/util.c",
    "line": 262
   },
   "code": "s = (unsigned char)*str++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "prefixcmp",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471111/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_7615794c1256.cpg",
   "testcase_size": 63
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "prefixcmp--git__prefixcmp--git_commit__parse_raw"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "s = (unsigned char)*str++",
     "line": 262
    },
    {
     "code": "s = git__tolower(s)",
     "line": 266
    }
   ],
   "entity_decl": {
    "line": 259,
    "type": "int"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    257,
    278
   ],
   "func_params": {
    "names": [
     "str",
     "str_n",
     "prefix",
     "icase"
    ],
    "types": [
     "char*",
     "size_t",
     "char*",
     "bool"
    ]
   },
   "guards": [
    {
     "code": "s != p",
     "line": 273
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "s = (unsigned char)*str++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(unsigned char)*str++",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "*str++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "str++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "s",
    "str"
   ],
   "osv_id": "ARVO-42471111",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "prefixcmp"
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