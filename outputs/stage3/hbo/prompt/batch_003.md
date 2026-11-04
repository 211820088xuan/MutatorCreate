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
  "osv_id": "ARVO-42471116",
  "project": "libarchive",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "rar",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 2370,
    "size": null,
    "type": "rar5*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "init_unpack",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 1834
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2424,
    "fn": "do_uncompress_block",
    "code": "rar->cstate.window_buf[write_idx & cmask] = (uint8_t) nu | rar->cstate.window_buf[write_idx & cmask] | rar->cstate.window_buf | rar->cstate",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "do_uncompress_block",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 2424
   },
   "code": "rar->cstate.window_buf[write_idx & cmask] = (uint8_t) nu | rar->cstate.window_buf[write_idx & cmask] | rar->cstate.window_buf | rar->cstate",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "do_uncompress_block",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "num < 256 | num >= 262 | num == 256",
   "guard_count": 5,
   "control_structures": "WHILE:2378,IF:2379,BREAK:2386,IF:2389,BREAK:2396,IF:2400,IF:2418,CONTINUE:2425,ELSE:2426,IF:2426,IF:2432,IF:2439"
  },
  "call_chain": [],
  "types": {
   "entity_type": "rar5*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/d5f35a90a4cb1eeb918213bff9d78e8b0471dc0a/ARVO-42471116/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_d5f35a90a4cb.cpg",
   "testcase_size": 109
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
   "dedup_token": "do_uncompress_block--process_block--do_uncompress_file"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* rar = get_context(a)",
     "line": 2370
    },
    {
     "code": "rar->cstate.block_parsing_finished = 1",
     "line": 2395
    },
    {
     "code": "rar->cstate.window_buf[write_idx & cmask] = (uint8_t) num",
     "line": 2424
    },
    {
     "code": "rar->cstate.last_len = len",
     "line": 2508
    },
    {
     "code": "rar->cstate.last_len = len",
     "line": 2543
    }
   ],
   "entity_decl": {
    "line": 2370,
    "type": "rar5*"
   },
   "entity_name_cpg": "rar",
   "func_lines": [
    2369,
    2559
   ],
   "func_params": {
    "names": [
     "a",
     "p"
    ],
    "types": [
     "archive_read*",
     "uint8_t*"
    ]
   },
   "guards": [
    {
     "code": "rar->cstate.write_ptr - rar->cstate.last_write_ptr >",
     "line": 2379
    },
    {
     "code": "rar->bits.in_addr > rar->cstate.cur_block_size - 1",
     "line": 2389
    },
    {
     "code": "rar->bits.in_addr == rar->cstate.cur_block_size - 1",
     "line": 2390
    },
    {
     "code": "ARCHIVE_OK != decode_number(a, &rar->cstate.ld, p, &num)",
     "line": 2400
    },
    {
     "code": "num < 256",
     "line": 2418
    },
    {
     "code": "len == -1",
     "line": 2432
    },
    {
     "code": "ARCHIVE_OK != decode_number(a, &rar->cstate.dd, p, &dist_slot)",
     "line": 2439
    },
    {
     "code": "dist_slot < 4",
     "line": 2447
    },
    {
     "code": "dbits > 0",
     "line": 2455
    },
    {
     "code": "dbits > 4",
     "line": 2460
    },
    {
     "code": "ARCHIVE_OK != read_bits_32(rar, p, &add)",
     "line": 2461
    },
    {
     "code": "ARCHIVE_OK != decode_number(a, &rar->cstate.ldd, p,",
     "line": 2471
    },
    {
     "code": "ARCHIVE_OK != read_consume_bits(rar, p, dbits, &add)",
     "line": 2486
    },
    {
     "code": "dist > 0x100",
     "line": 2495
    },
    {
     "code": "dist > 0x2000",
     "line": 2498
    },
    {
     "code": "dist > 0x40000",
     "line": 2501
    },
    {
     "code": "ARCHIVE_OK != copy_string(a, len, dist)",
     "line": 2510
    },
    {
     "code": "num == 256",
     "line": 2514
    },
    {
     "code": "ret != ARCHIVE_OK",
     "line": 2517
    },
    {
     "code": "num == 257",
     "line": 2521
    },
    {
     "code": "rar->cstate.last_len != 0",
     "line": 2522
    },
    {
     "code": "ARCHIVE_OK != copy_string(a, rar->cstate.last_len,",
     "line": 2523
    },
    {
     "code": "num < 262",
     "line": 2531
    },
    {
     "code": "ARCHIVE_OK != decode_number(a, &rar->cstate.rd, p, &len_slot)",
     "line": 2538
    },
    {
     "code": "ARCHIVE_OK != copy_string(a, len, dist)",
     "line": 2545
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "rar->cstate.window_buf[write_idx & cmask] = (uint8_t) num",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "rar->cstate.window_buf[write_idx & cmask]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "rar->cstate.window_buf",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "rar->cstate",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "write_idx & cmask",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint8_t) num",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "rar",
    "write_idx",
    "cmask",
    "num"
   ],
   "osv_id": "ARVO-42471116",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "do_uncompress_block"
  }
 },
 {
  "osv_id": "ARVO-42471192",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "cc",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 650,
    "size": null,
    "type": "unsigned int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "hb_vector_t<char, 8u>::alloc(unsigned int)",
    "file": "/src/harfbuzz/src/./hb-vector.hh",
    "line": 96
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "HB_OT_SHAPE_COMPLEX_MAX_COMBINING_MARKS",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 650,
    "fn": "BEInt<unsigned short, 2>::set(unsigned short)",
    "code": "cc = 220 | cc <= 230 | cc += 10",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "BEInt<unsigned short, 2>::set(unsigned short)",
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 650
   },
   "code": "cc = 220 | cc <= 230 | cc += 10",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "reorder_marks_arabic",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "cc <= 230 | info_cc(info[i]) < cc | info_cc(info[i]) > cc",
   "guard_count": 5,
   "control_structures": "FOR:650,WHILE:653,IF:657,BREAK:658,IF:660,CONTINUE:661,WHILE:664,IF:667,CONTINUE:668,WHILE:695"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "buffer",
   "start",
   "end"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/fda994e1d45c4d34601af7272f37ea257f92a3d8/ARVO-42471192/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_fda994e1d45c.cpg",
   "testcase_size": 880
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
   "dedup_token": "BEInt<unsigned short, 2>::set(unsigned short)--OT::Script::subset(hb_subset_context_t*) const--void OT::OffsetTo<OT::Script, OT::IntType<unsigned short, 2u> >::"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cc = 220",
     "line": 650
    }
   ],
   "entity_decl": {
    "line": 650,
    "type": "unsigned int"
   },
   "entity_name_cpg": "cc",
   "func_lines": [
    639,
    703
   ],
   "func_params": {
    "names": [
     "plan",
     "buffer",
     "start",
     "end"
    ],
    "types": [
     "hb_ot_shape_plan_t*",
     "hb_buffer_t*",
     "unsigned int",
     "unsigned int"
    ]
   },
   "guards": [
    {
     "code": "i < end",
     "line": 653
    },
    {
     "code": "info_cc(info[i]) < cc",
     "line": 653
    },
    {
     "code": "i == end",
     "line": 657
    },
    {
     "code": "info_cc(info[i]) > cc",
     "line": 660
    },
    {
     "code": "j < end",
     "line": 664
    },
    {
     "code": "info_cc(info[j]) == cc",
     "line": 664
    },
    {
     "code": "i == j",
     "line": 667
    },
    {
     "code": "cc == 220",
     "line": 694
    },
    {
     "code": "start < new_start",
     "line": 695
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "cc = 220",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "cc <= 230",
     "name": "<operator>.lessEqualsThan",
     "nargs": 2
    },
    {
     "code": "cc += 10",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cc"
   ],
   "osv_id": "ARVO-42471192",
   "sites": [
    {
     "args": "HB_OT_SHAPE_COMPLEX_MAX_COMBINING_MARKS",
     "callee": "<operator>.alloc",
     "code": "temp[HB_OT_SHAPE_COMPLEX_MAX_COMBINING_MARKS]",
     "line": 674
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "BEInt<unsigned short, 2>::set(unsigned short)"
  }
 },
 {
  "osv_id": "ARVO-42471280",
  "project": "openvswitch",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "s",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 5405,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "main",
    "file": "/src/libfuzzer/afl/afl_driver.cpp",
    "line": 339
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "3",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 5451,
    "fn": "parse_odp_key_mask_attr",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_odp_key_mask_attr",
    "file": "/src/openvswitch/lib/odp-util.c",
    "line": 5451
   },
   "code": "nl_msg_end_nested(mask, mask_offset)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_odp_key_mask_attr",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/b47e7e2bac7f21f8c81aaeb1068598a6064c348b/ARVO-42471280/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_b47e7e2bac7f.cpg",
   "testcase_size": 19
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
   "dedup_token": "parse_odp_key_mask_attr--odp_flow_from_string--parse_keys"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 5405,
    "type": "char*"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    5404,
    5591
   ],
   "func_params": {
    "names": [
     "s",
     "port_names",
     "key",
     "mask"
    ],
    "types": [
     "char*",
     "simap*",
     "ofpbuf*",
     "ofpbuf*"
    ]
   },
   "guards": [
    {
     "code": "strncmp(s, \"skb_priority(\", strlen(\"skb_priority(\")) == 0",
     "line": 5408
    },
    {
     "code": "len == 0",
     "line": 5408
    },
    {
     "code": "*s++ != ')'",
     "line": 5408
    },
    {
     "code": "strncmp(s, \"skb_mark(\", strlen(\"skb_mark(\")) == 0",
     "line": 5409
    },
    {
     "code": "len == 0",
     "line": 5409
    },
    {
     "code": "*s++ != ')'",
     "line": 5409
    },
    {
     "code": "strncmp(s, \"recirc_id(\", strlen(\"recirc_id(\")) == 0",
     "line": 5410
    },
    {
     "code": "len == 0",
     "line": 5410
    },
    {
     "code": "*s++ != ')'",
     "line": 5410
    },
    {
     "code": "strncmp(s, \"dp_hash(\", strlen(\"dp_hash(\")) == 0",
     "line": 5412
    },
    {
     "code": "len == 0",
     "line": 5412
    },
    {
     "code": "*s++ != ')'",
     "line": 5412
    },
    {
     "code": "strncmp(s, \"ct_state(\", strlen(\"ct_state(\")) == 0",
     "line": 5414
    },
    {
     "code": "len == 0",
     "line": 5414
    },
    {
     "code": "*s++ != ')'",
     "line": 5414
    },
    {
     "code": "strncmp(s, \"ct_zone(\", strlen(\"ct_zone(\")) == 0",
     "line": 5415
    },
    {
     "code": "len == 0",
     "line": 5415
    },
    {
     "code": "*s++ != ')'",
     "line": 5415
    },
    {
     "code": "strncmp(s, \"ct_mark(\", strlen(\"ct_mark(\")) == 0",
     "line": 5416
    },
    {
     "code": "len == 0",
     "line": 5416
    },
    {
     "code": "*s++ != ')'",
     "line": 5416
    },
    {
     "code": "strncmp(s, \"ct_label(\", strlen(\"ct_label(\")) == 0",
     "line": 5417
    },
    {
     "code": "len == 0",
     "line": 5417
    },
    {
     "code": "*s++ != ')'",
     "line": 5417
    },
    {
     "code": "strncmp(s, \"ct_tuple4(\", strlen(\"ct_tuple4(\")) == 0",
     "line": 5419
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5420
    },
    {
     "code": "len == 0",
     "line": 5420
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5421
    },
    {
     "code": "len == 0",
     "line": 5421
    },
    {
     "code": "strncmp(s, \"proto=\", strlen(\"proto=\")) == 0",
     "line": 5422
    },
    {
     "code": "len == 0",
     "line": 5422
    },
    {
     "code": "strncmp(s, \"tp_src=\", strlen(\"tp_src=\")) == 0",
     "line": 5423
    },
    {
     "code": "len == 0",
     "line": 5423
    },
    {
     "code": "strncmp(s, \"tp_dst=\", strlen(\"tp_dst=\")) == 0",
     "line": 5424
    },
    {
     "code": "len == 0",
     "line": 5424
    },
    {
     "code": "*s++ == ','",
     "line": 5425
    },
    {
     "code": "len != 0",
     "line": 5425
    },
    {
     "code": "s[-1] != ')'",
     "line": 5425
    },
    {
     "code": "strncmp(s, \"ct_tuple6(\", strlen(\"ct_tuple6(\")) == 0",
     "line": 5427
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5428
    },
    {
     "code": "len == 0",
     "line": 5428
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5429
    },
    {
     "code": "len == 0",
     "line": 5429
    },
    {
     "code": "strncmp(s, \"proto=\", strlen(\"proto=\")) == 0",
     "line": 5430
    },
    {
     "code": "len == 0",
     "line": 5430
    },
    {
     "code": "strncmp(s, \"tp_src=\", strlen(\"tp_src=\")) == 0",
     "line": 5431
    },
    {
     "code": "len == 0",
     "line": 5431
    },
    {
     "code": "strncmp(s, \"tp_dst=\", strlen(\"tp_dst=\")) == 0",
     "line": 5432
    },
    {
     "code": "len == 0",
     "line": 5432
    },
    {
     "code": "*s++ == ','",
     "line": 5433
    },
    {
     "code": "len != 0",
     "line": 5433
    },
    {
     "code": "s[-1] != ')'",
     "line": 5433
    },
    {
     "code": "strncmp(s, \"tunnel(\", strlen(\"tunnel(\")) == 0",
     "line": 5435
    },
    {
     "code": "strncmp(s, \"tun_id=\", strlen(\"tun_id=\")) == 0",
     "line": 5436
    },
    {
     "code": "len == 0",
     "line": 5436
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5437
    },
    {
     "code": "len == 0",
     "line": 5437
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5438
    },
    {
     "code": "len == 0",
     "line": 5438
    },
    {
     "code": "strncmp(s, \"ipv6_src=\", strlen(\"ipv6_src=\")) == 0",
     "line": 5439
    },
    {
     "code": "len == 0",
     "line": 5439
    },
    {
     "code": "strncmp(s, \"ipv6_dst=\", strlen(\"ipv6_dst=\")) == 0",
     "line": 5440
    },
    {
     "code": "len == 0",
     "line": 5440
    },
    {
     "code": "strncmp(s, \"tos=\", strlen(\"tos=\")) == 0",
     "line": 5441
    },
    {
     "code": "len == 0",
     "line": 5441
    },
    {
     "code": "strncmp(s, \"ttl=\", strlen(\"ttl=\")) == 0",
     "line": 5442
    },
    {
     "code": "len == 0",
     "line": 5442
    },
    {
     "code": "strncmp(s, \"tp_src=\", strlen(\"tp_src=\")) == 0",
     "line": 5443
    },
    {
     "code": "len == 0",
     "line": 5443
    },
    {
     "code": "strncmp(s, \"tp_dst=\", strlen(\"tp_dst=\")) == 0",
     "line": 5444
    },
    {
     "code": "len == 0",
     "line": 5444
    },
    {
     "code": "strncmp(s, \"erspan(\", strlen(\"erspan(\")) == 0",
     "line": 5445
    },
    {
     "code": "len == 0",
     "line": 5445
    },
    {
     "code": "strncmp(s, \"vxlan(gbp(\", strlen(\"vxlan(gbp(\")) == 0",
     "line": 5447
    },
    {
     "code": "len == 0",
     "line": 5447
    },
    {
     "code": "strncmp(s, \"geneve(\", strlen(\"geneve(\")) == 0",
     "line": 5448
    },
    {
     "code": "len == 0",
     "line": 5448
    },
    {
     "code": "strncmp(s, \"flags(\", strlen(\"flags(\")) == 0",
     "line": 5450
    },
    {
     "code": "len == 0",
     "line": 5450
    },
    {
     "code": "*s++ == ','",
     "line": 5451
    },
    {
     "code": "len != 0",
     "line": 5451
    },
    {
     "code": "s[-1] != ')'",
     "line": 5451
    },
    {
     "code": "strncmp(s, \"in_port(\", strlen(\"in_port(\")) == 0",
     "line": 5453
    },
    {
     "code": "len == 0",
     "line": 5453
    },
    {
     "code": "*s++ != ')'",
     "line": 5453
    },
    {
     "code": "strncmp(s, \"eth(\", strlen(\"eth(\")) == 0",
     "line": 5455
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5456
    },
    {
     "code": "len == 0",
     "line": 5456
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5457
    },
    {
     "code": "len == 0",
     "line": 5457
    },
    {
     "code": "*s++ == ','",
     "line": 5458
    },
    {
     "code": "len != 0",
     "line": 5458
    },
    {
     "code": "s[-1] != ')'",
     "line": 5458
    },
    {
     "code": "strncmp(s, \"vlan(\", strlen(\"vlan(\")) == 0",
     "line": 5460
    },
    {
     "code": "strncmp(s, \"vid=\", strlen(\"vid=\")) == 0",
     "line": 5462
    },
    {
     "code": "len == 0",
     "line": 5462
    },
    {
     "code": "strncmp(s, \"pcp=\", strlen(\"pcp=\")) == 0",
     "line": 5463
    },
    {
     "code": "len == 0",
     "line": 5463
    },
    {
     "code": "strncmp(s, \"cfi=\", strlen(\"cfi=\")) == 0",
     "line": 5464
    },
    {
     "code": "len == 0",
     "line": 5464
    },
    {
     "code": "*s++ == ','",
     "line": 5465
    },
    {
     "code": "len != 0",
     "line": 5465
    },
    {
     "code": "s[-1] != ')'",
     "line": 5465
    },
    {
     "code": "strncmp(s, \"eth_type(\", strlen(\"eth_type(\")) == 0",
     "line": 5467
    },
    {
     "code": "len == 0",
     "line": 5467
    },
    {
     "code": "*s++ != ')'",
     "line": 5467
    },
    {
     "code": "strncmp(s, \"mpls(\", strlen(\"mpls(\")) == 0",
     "line": 5469
    },
    {
     "code": "strncmp(s, \"label=\", strlen(\"label=\")) == 0",
     "line": 5470
    },
    {
     "code": "++idx == cnt",
     "line": 5470
    },
    {
     "code": "len == 0",
     "line": 5470
    },
    {
     "code": "strncmp(s, \"tc=\", strlen(\"tc=\")) == 0",
     "line": 5471
    },
    {
     "code": "++idx == cnt",
     "line": 5471
    },
    {
     "code": "len == 0",
     "line": 5471
    },
    {
     "code": "strncmp(s, \"ttl=\", strlen(\"ttl=\")) == 0",
     "line": 5472
    },
    {
     "code": "++idx == cnt",
     "line": 5472
    },
    {
     "code": "len == 0",
     "line": 5472
    },
    {
     "code": "strncmp(s, \"bos=\", strlen(\"bos=\")) == 0",
     "line": 5473
    },
    {
     "code": "++idx == cnt",
     "line": 5473
    },
    {
     "code": "len == 0",
     "line": 5473
    },
    {
     "code": "*s++ == ','",
     "line": 5474
    },
    {
     "code": "len != 0",
     "line": 5474
    },
    {
     "code": "s[-1] != ')'",
     "line": 5474
    },
    {
     "code": "idx == cnt",
     "line": 5474
    },
    {
     "code": "strncmp(s, \"ipv4(\", strlen(\"ipv4(\")) == 0",
     "line": 5476
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5477
    },
    {
     "code": "len == 0",
     "line": 5477
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5478
    },
    {
     "code": "len == 0",
     "line": 5478
    },
    {
     "code": "strncmp(s, \"proto=\", strlen(\"proto=\")) == 0",
     "line": 5479
    },
    {
     "code": "len == 0",
     "line": 5479
    },
    {
     "code": "strncmp(s, \"tos=\", strlen(\"tos=\")) == 0",
     "line": 5480
    },
    {
     "code": "len == 0",
     "line": 5480
    },
    {
     "code": "strncmp(s, \"ttl=\", strlen(\"ttl=\")) == 0",
     "line": 5481
    },
    {
     "code": "len == 0",
     "line": 5481
    },
    {
     "code": "strncmp(s, \"frag=\", strlen(\"frag=\")) == 0",
     "line": 5482
    },
    {
     "code": "len == 0",
     "line": 5482
    },
    {
     "code": "*s++ == ','",
     "line": 5483
    },
    {
     "code": "len != 0",
     "line": 5483
    },
    {
     "code": "s[-1] != ')'",
     "line": 5483
    },
    {
     "code": "strncmp(s, \"ipv6(\", strlen(\"ipv6(\")) == 0",
     "line": 5485
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5486
    },
    {
     "code": "len == 0",
     "line": 5486
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5487
    },
    {
     "code": "len == 0",
     "line": 5487
    },
    {
     "code": "strncmp(s, \"label=\", strlen(\"label=\")) == 0",
     "line": 5488
    },
    {
     "code": "len == 0",
     "line": 5488
    },
    {
     "code": "strncmp(s, \"proto=\", strlen(\"proto=\")) == 0",
     "line": 5489
    },
    {
     "code": "len == 0",
     "line": 5489
    },
    {
     "code": "strncmp(s, \"tclass=\", strlen(\"tclass=\")) == 0",
     "line": 5490
    },
    {
     "code": "len == 0",
     "line": 5490
    },
    {
     "code": "strncmp(s, \"hlimit=\", strlen(\"hlimit=\")) == 0",
     "line": 5491
    },
    {
     "code": "len == 0",
     "line": 5491
    },
    {
     "code": "strncmp(s, \"frag=\", strlen(\"frag=\")) == 0",
     "line": 5492
    },
    {
     "code": "len == 0",
     "line": 5492
    },
    {
     "code": "*s++ == ','",
     "line": 5493
    },
    {
     "code": "len != 0",
     "line": 5493
    },
    {
     "code": "s[-1] != ')'",
     "line": 5493
    },
    {
     "code": "strncmp(s, \"tcp(\", strlen(\"tcp(\")) == 0",
     "line": 5495
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5496
    },
    {
     "code": "len == 0",
     "line": 5496
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5497
    },
    {
     "code": "len == 0",
     "line": 5497
    },
    {
     "code": "*s++ == ','",
     "line": 5498
    },
    {
     "code": "len != 0",
     "line": 5498
    },
    {
     "code": "s[-1] != ')'",
     "line": 5498
    },
    {
     "code": "strncmp(s, \"tcp_flags(\", strlen(\"tcp_flags(\")) == 0",
     "line": 5500
    },
    {
     "code": "len == 0",
     "line": 5500
    },
    {
     "code": "*s++ != ')'",
     "line": 5500
    },
    {
     "code": "strncmp(s, \"udp(\", strlen(\"udp(\")) == 0",
     "line": 5502
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5503
    },
    {
     "code": "len == 0",
     "line": 5503
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5504
    },
    {
     "code": "len == 0",
     "line": 5504
    },
    {
     "code": "*s++ == ','",
     "line": 5505
    },
    {
     "code": "len != 0",
     "line": 5505
    },
    {
     "code": "s[-1] != ')'",
     "line": 5505
    },
    {
     "code": "strncmp(s, \"sctp(\", strlen(\"sctp(\")) == 0",
     "line": 5507
    },
    {
     "code": "strncmp(s, \"src=\", strlen(\"src=\")) == 0",
     "line": 5508
    },
    {
     "code": "len == 0",
     "line": 5508
    },
    {
     "code": "strncmp(s, \"dst=\", strlen(\"dst=\")) == 0",
     "line": 5509
    },
    {
     "code": "len == 0",
     "line": 5509
    },
    {
     "code": "*s++ == ','",
     "line": 5510
    },
    {
     "code": "len != 0",
     "line": 5510
    },
    {
     "code": "s[-1] != ')'",
     "line": 5510
    },
    {
     "code": "strncmp(s, \"icmp(\", strlen(\"icmp(\")) == 0",
     "line": 5512
    },
    {
     "code": "strncmp(s, \"type=\", strlen(\"type=\")) == 0",
     "line": 5513
    },
    {
     "code": "len == 0",
     "line": 5513
    },
    {
     "code": "strncmp(s, \"code=\", strlen(\"code=\")) == 0",
     "line": 5514
    },
    {
     "code": "len == 0",
     "line": 5514
    },
    {
     "code": "*s++ == ','",
     "line": 5515
    },
    {
     "code": "len != 0",
     "line": 5515
    },
    {
     "code": "s[-1] != ')'",
     "line": 5515
    },
    {
     "code": "strncmp(s, \"icmpv6(\", strlen(\"icmpv6(\")) == 0",
     "line": 5517
    },
    {
     "code": "strncmp(s, \"type=\", strlen(\"type=\")) == 0",
     "line": 5518
    },
    {
     "code": "len == 0",
     "line": 5518
    },
    {
     "code": "strncmp(s, \"code=\", strlen(\"code=\")) == 0",
     "line": 5519
    },
    {
     "code": "len == 0",
     "line": 5519
    },
    {
     "code": "*s++ == ','",
     "line": 5520
    },
    {
     "code": "len != 0",
     "line": 5520
    },
    {
     "code": "s[-1] != ')'",
     "line": 5520
    },
    {
     "code": "strncmp(s, \"arp(\", strlen(\"arp(\")) == 0",
     "line": 5522
    },
    {
     "code": "strncmp(s, \"sip=\", strlen(\"sip=\")) == 0",
     "line": 5523
    },
    {
     "code": "len == 0",
     "line": 5523
    },
    {
     "code": "strncmp(s, \"tip=\", strlen(\"tip=\")) == 0",
     "line": 5524
    },
    {
     "code": "len == 0",
     "line": 5524
    },
    {
     "code": "strncmp(s, \"op=\", strlen(\"op=\")) == 0",
     "line": 5525
    },
    {
     "code": "len == 0",
     "line": 5525
    },
    {
     "code": "strncmp(s, \"sha=\", strlen(\"sha=\")) == 0",
     "line": 5526
    },
    {
     "code": "len == 0",
     "line": 5526
    },
    {
     "code": "strncmp(s, \"tha=\", strlen(\"tha=\")) == 0",
     "line": 5527
    },
    {
     "code": "len == 0",
     "line": 5527
    },
    {
     "code": "*s++ == ','",
     "line": 5528
    },
    {
     "code": "len != 0",
     "line": 5528
    },
    {
     "code": "s[-1] != ')'",
     "line": 5528
    },
    {
     "code": "strncmp(s, \"nd(\", strlen(\"nd(\")) == 0",
     "line": 5530
    },
    {
     "code": "strncmp(s, \"target=\", strlen(\"target=\")) == 0",
     "line": 5531
    },
    {
     "code": "len == 0",
     "line": 5531
    },
    {
     "code": "strncmp(s, \"sll=\", strlen(\"sll=\")) == 0",
     "line": 5532
    },
    {
     "code": "len == 0",
     "line": 5532
    },
    {
     "code": "strncmp(s, \"tll=\", strlen(\"tll=\")) == 0",
     "line": 5533
    },
    {
     "code": "len == 0",
     "line": 5533
    },
    {
     "code": "*s++ == ','",
     "line": 5534
    },
    {
     "code": "len != 0",
     "line": 5534
    },
    {
     "code": "s[-1] != ')'",
     "line": 5534
    },
    {
     "code": "strncmp(s, \"packet_type(\", strlen(\"packet_type(\")) == 0",
     "line": 5540
    },
    {
     "code": "strncmp(s, \"ns=\", strlen(\"ns=\")) == 0",
     "line": 5541
    },
    {
     "code": "len == 0",
     "line": 5541
    },
    {
     "code": "strncmp(s, \"id=\", strlen(\"id=\")) == 0",
     "line": 5542
    },
    {
     "code": "len == 0",
     "line": 5542
    },
    {
     "code": "*s++ == ','",
     "line": 5543
    },
    {
     "code": "len != 0",
     "line": 5543
    },
    {
     "code": "s[-1] != ')'",
     "line": 5543
    },
    {
     "code": "ret < 0",
     "line": 5547
    },
    {
     "code": "*s == ')'",
     "line": 5570
    },
    {
     "code": "retval < 0",
     "line": 5575
    }
   ],
   "line_call_count": 13,
   "line_calls": [
    {
     "code": "SCAN_END_NESTED()",
     "name": "SCAN_END_NESTED",
     "nargs": 0
    },
    {
     "code": "*s++ == ',' && len != 0",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "*s++ == ','",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*s++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "s++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "len != 0",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "s[-1] != ')'",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "s[-1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "-1",
     "name": "<operator>.minus",
     "nargs": 1
    },
    {
     "code": "-EINVAL",
     "name": "<operator>.minus",
     "nargs": 1
    },
    {
     "code": "nl_msg_end_nested(key, key_offset)",
     "name": "nl_msg_end_nested",
     "nargs": 2
    },
    {
     "code": "nl_msg_end_nested(mask, mask_offset)",
     "name": "nl_msg_end_nested",
     "nargs": 2
    },
    {
     "code": "s - start",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "s",
    "len",
    "EINVAL",
    "key",
    "key_offset",
    "mask",
    "mask_offset",
    "start"
   ],
   "osv_id": "ARVO-42471280",
   "sites": [
    {
     "args": "3",
     "callee": "<operator>.alloc",
     "code": "ovs_key_mpls []",
     "line": 5469
    },
    {
     "args": "3",
     "callee": "<operator>.alloc",
     "code": "ovs_key_mpls []",
     "line": 5469
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse_odp_key_mask_attr"
  }
 },
 {
  "osv_id": "ARVO-42471287",
  "project": "libgit2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 361,
    "type": "unsigned char",
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
    "line": 367,
    "fn": "parse_mode",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_mode",
    "file": "/src/libgit2/src/tree.c",
    "line": 367
   },
   "code": "(c = *buffer++) != ' '",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_mode",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471287/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_7615794c1256.cpg",
   "testcase_size": 1
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
   "dedup_token": "parse_mode--git_tree__parse_raw--git_object__from_raw"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = *buffer++",
     "line": 367
    }
   ],
   "entity_decl": {
    "line": 361,
    "type": "unsigned char"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    359,
    376
   ],
   "func_params": {
    "names": [
     "modep",
     "buffer",
     "buffer_out"
    ],
    "types": [
     "unsigned int*",
     "char*",
     "char**"
    ]
   },
   "guards": [
    {
     "code": "*buffer == ' '",
     "line": 364
    },
    {
     "code": "(c = *buffer++) != ' '",
     "line": 367
    },
    {
     "code": "c < '0'",
     "line": 368
    },
    {
     "code": "c > '7'",
     "line": 368
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "(c = *buffer++) != ' '",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "c = *buffer++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*buffer++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "buffer++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "c",
    "buffer"
   ],
   "osv_id": "ARVO-42471287",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse_mode"
  }
 },
 {
  "osv_id": "ARVO-42471319",
  "project": "libarchive",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "bits",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 951,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "merge_block",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 2666
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 953,
    "fn": "read_bits_16",
    "code": "bits |= (int) p[rar->bits.in_addr + 2] | (int) p[rar->bits.in_addr + 2] | p[rar->bits.in_addr + 2] | rar->bits.in_addr + 2",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_bits_16",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 953
   },
   "code": "bits |= (int) p[rar->bits.in_addr + 2] | (int) p[rar->bits.in_addr + 2] | p[rar->bits.in_addr + 2] | rar->bits.in_addr + 2",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "read_bits_16",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "rar",
   "p"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/d5f35a90a4cb1eeb918213bff9d78e8b0471dc0a/ARVO-42471319/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_d5f35a90a4cb.cpg",
   "testcase_size": 304
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "read_bits_16--decode_number--do_uncompress_block"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "bits = (int) p[rar->bits.in_addr] << 16",
     "line": 951
    }
   ],
   "entity_decl": {
    "line": 951,
    "type": "int"
   },
   "entity_name_cpg": "bits",
   "func_lines": [
    950,
    957
   ],
   "func_params": {
    "names": [
     "rar",
     "p",
     "value"
    ],
    "types": [
     "rar5*",
     "uint8_t*",
     "uint16_t*"
    ]
   },
   "guards": [],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "bits ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "(int) p[rar->bits.in_addr + 2]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "p[rar->bits.in_addr + 2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "rar->bits.in_addr + 2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "rar->bits.in_addr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "rar->bits",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "bits",
    "p",
    "rar"
   ],
   "osv_id": "ARVO-42471319",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "read_bits_16"
  }
 },
 {
  "osv_id": "ARVO-42471374",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "data",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 644,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "size_expr_cpg": "allocated",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "code": "malloc (allocated)",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "kind": "malloc",
    "line": 644,
    "origin": "cpg",
    "args": "allocated"
   },
   {
    "code": "realloc (data, allocated)",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "kind": "realloc",
    "line": 658,
    "origin": "cpg",
    "args": "data ;; allocated"
   },
   {
    "kind": "unknown",
    "line": 660,
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "code": "data = new_data",
    "origin": "report:crash"
   },
   {
    "code": "free (data)",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "kind": "free",
    "line": 680,
    "origin": "cpg",
    "args": "data"
   }
  ],
  "crash": {
   "site": {
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 660
   },
   "code": "data = new_data",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "hb_blob_create_from_file",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "data == nullptr | new_data == nullptr",
   "guard_count": 2,
   "control_structures": "IF:645,IF:648,GOTO:648,WHILE:650,IF:652,IF:657,GOTO:657,IF:659,GOTO:659,IF:669,GOTO:669"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "file_name"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/2c68f34bddbe506d0b22948562f2f59b9a5b6050/ARVO-42471374/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2c68f34bddbe.cpg",
   "testcase_size": 36
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
   "dedup_token": "BEInt<unsigned char, 1>::operator unsigned char() const--OT::KernSubTableFormat3::get_kerning(unsigned int, unsigned int) const--hb_kern_machine_t<OT::KernSubTa"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*data = (char *) malloc (allocated)",
     "line": 644
    },
    {
     "code": "data = new_data",
     "line": 660
    }
   ],
   "entity_decl": {
    "line": 644,
    "type": "char*"
   },
   "entity_name_cpg": "data",
   "func_lines": [
    547,
    682
   ],
   "func_params": {
    "names": [
     "file_name"
    ],
    "types": [
     "char*"
    ]
   },
   "guards": [
    {
     "code": "data == nullptr",
     "line": 645
    },
    {
     "code": "fp == nullptr",
     "line": 648
    },
    {
     "code": "allocated - len < BUFSIZ",
     "line": 652
    },
    {
     "code": "allocated > (2 << 28)",
     "line": 657
    },
    {
     "code": "new_data == nullptr",
     "line": 659
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "data = new_data",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "data",
    "new_data"
   ],
   "osv_id": "ARVO-42471374",
   "sites": [
    {
     "args": "allocated",
     "callee": "malloc",
     "code": "malloc (allocated)",
     "line": 644
    },
    {
     "args": "data ;; allocated",
     "callee": "realloc",
     "code": "realloc (data, allocated)",
     "line": 658
    },
    {
     "args": "data",
     "callee": "free",
     "code": "free (data)",
     "line": 680
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
   "use_fn": "BEInt<unsigned char, 1>::operator unsigned char() const"
  }
 },
 {
  "osv_id": "ARVO-42471383",
  "project": "openvswitch",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "b",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 469,
    "type": "ofpbuf*",
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
    "line": 473,
    "fn": "ofpbuf_insert",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ofpbuf_insert",
    "file": "/src/openvswitch/lib/ofpbuf.c",
    "line": 473
   },
   "code": "memmove((char *) b->data + offset + n, (char *) b->data + offset,",
   "access": {
    "dir": "WRITE",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ofpbuf_insert",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/aa1a0f1aaf6a772327b712d0507735af5b8c791d/ARVO-42471383/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_aa1a0f1aaf6a.cpg",
   "testcase_size": 32
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
   "dedup_token": "__asan_memmove--ofpbuf_insert--nx_put_raw"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 469,
    "type": "ofpbuf*"
   },
   "entity_name_cpg": "b",
   "func_lines": [
    468,
    480
   ],
   "func_params": {
    "names": [
     "b",
     "offset",
     "data",
     "n"
    ],
    "types": [
     "ofpbuf*",
     "size_t",
     "void*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "offset < b->size",
     "line": 471
    },
    {
     "code": "offset == b->size",
     "line": 477
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "memmove((char *) b->data + offset + n, (char *) b->data + offset,",
     "name": "memmove",
     "nargs": null
    },
    {
     "code": "(char *) b->data + offset + n",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(char *) b->data + offset",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(char *) b->data",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "b->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(char *) b->data + offset",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(char *) b->data",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "b->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "b",
    "offset",
    "n"
   ],
   "osv_id": "ARVO-42471383",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ofpbuf_insert"
  }
 },
 {
  "osv_id": "ARVO-42471394",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "blob",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "line": 204,
    "size": null,
    "type": "hb_blob_t**"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 257
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 214,
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "line": 214
   },
   "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
   "access": {
    "dir": "READ",
    "width": 94,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_get_kerx",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:206,IF:208,IF:213"
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_blob_t**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "face",
   "blob"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/b605db2f65e62ad6727a61481f78015933dbf207/ARVO-42471394/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_b605db2f65e6.cpg",
   "testcase_size": 1816
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
   "dedup_token": "__interceptor_memcmp.part.78--OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)--sort_r_cmpswap(char*, char*, unsigned long, int (*)(void const"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 204,
    "type": "hb_blob_t**"
   },
   "entity_name_cpg": "blob",
   "func_lines": [
    203,
    216
   ],
   "func_params": {
    "names": [
     "face",
     "blob"
    ],
    "types": [
     "hb_face_t*",
     "hb_blob_t**"
    ]
   },
   "guards": [],
   "line_call_count": 9,
   "line_calls": [
    {
     "code": "*blob = hb_ot_face_data (face)->kerx.get_blob ()",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*blob",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "hb_ot_face_data (face)->kerx.get_blob ()",
     "name": "hb_ot_face_data",
     "nargs": 1
    },
    {
     "code": "((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed())->kerx.get_blob()",
     "name": "get_blob",
     "nargs": 1
    },
    {
     "code": "((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed())->kerx",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "face->shaper_data.ot.get_relaxed()",
     "name": "get_relaxed",
     "nargs": 1
    },
    {
     "code": "face->shaper_data.ot",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "face->shaper_data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "blob",
    "face"
   ],
   "osv_id": "ARVO-42471394",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)"
  }
 },
 {
  "osv_id": "ARVO-42471424",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "blob",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "line": 204,
    "size": null,
    "type": "hb_blob_t**"
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
    "line": 214,
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "line": 214
   },
   "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
   "access": {
    "dir": "READ",
    "width": 5,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_get_kerx",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:206,IF:208,IF:213"
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_blob_t**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "face",
   "blob"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/b605db2f65e62ad6727a61481f78015933dbf207/ARVO-42471424/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_b605db2f65e6.cpg",
   "testcase_size": 16731
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
   "dedup_token": "__interceptor_memcmp.part.78--OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)--sort_r_cmpswap(char*, char*, unsigned long, int (*)(void const"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 204,
    "type": "hb_blob_t**"
   },
   "entity_name_cpg": "blob",
   "func_lines": [
    203,
    216
   ],
   "func_params": {
    "names": [
     "face",
     "blob"
    ],
    "types": [
     "hb_face_t*",
     "hb_blob_t**"
    ]
   },
   "guards": [],
   "line_call_count": 9,
   "line_calls": [
    {
     "code": "*blob = hb_ot_face_data (face)->kerx.get_blob ()",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*blob",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "hb_ot_face_data (face)->kerx.get_blob ()",
     "name": "hb_ot_face_data",
     "nargs": 1
    },
    {
     "code": "((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed())->kerx.get_blob()",
     "name": "get_blob",
     "nargs": 1
    },
    {
     "code": "((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed())->kerx",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "face->shaper_data.ot.get_relaxed()",
     "name": "get_relaxed",
     "nargs": 1
    },
    {
     "code": "face->shaper_data.ot",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "face->shaper_data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "blob",
    "face"
   ],
   "osv_id": "ARVO-42471424",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)"
  }
 },
 {
  "osv_id": "ARVO-42471519",
  "project": "openthread",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "sSrcMatchExtData",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/openthread/tests/fuzz/radio_receive_done.cpp",
    "line": 61
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1586,
    "fn": "ot::MeshForwarder::GetFramePriority(unsigned char*, unsigned char, ot::Mac::Address const&, ot::Mac::Address const&, unsigned char&)",
    "code": "sSrcMatchExtData.srcMatchEn[idx / 32] |= (1 << (idx % 32 | sSrcMatchExtData.srcMatchEn[idx / 32] | sSrcMatchExtData.srcMatchEn | idx / 32",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::MeshForwarder::GetFramePriority(unsigned char*, unsigned char, ot::Mac::Address const&, ot::Mac::Address const&, unsigned char&)",
    "file": "/src/openthread/src/core/thread/mesh_forwarder.cpp",
    "line": 1586
   },
   "code": "sSrcMatchExtData.srcMatchEn[idx / 32] |= (1 << (idx % 32 | sSrcMatchExtData.srcMatchEn[idx / 32] | sSrcMatchExtData.srcMatchEn | idx / 32",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "otPlatRadioAddSrcMatchExtEntry",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "idx == CC1352_SRC_MATCH_NONE",
   "guard_count": 1,
   "control_structures": "IF:1570,IF:1577,ELSE:1583"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openthread/address/08747cf7a7b5d14e301d174f8d095f18b68e17aa/ARVO-42471519/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_08747cf7a7b5.cpg",
   "testcase_size": 13
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
   "dedup_token": "ot::MeshForwarder::GetFramePriority(unsigned char*, unsigned char, ot::Mac::Address const&, ot::Mac::Address const&, unsigned char&)--ot::MeshForwarder::HandleF"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "sSrcMatchExtData.extAddrEnt[idx] = *((uint64_t *)aExtAddress)",
     "line": 1574
    }
   ],
   "entity_name_cpg": "sSrcMatchExtData",
   "func_lines": [
    1564,
    1591
   ],
   "func_params": {
    "names": [
     "aInstance",
     "aExtAddress"
    ],
    "types": [
     "otInstance*",
     "otExtAddress*"
    ]
   },
   "guards": [
    {
     "code": "idx == CC1352_SRC_MATCH_NONE",
     "line": 1570
    },
    {
     "code": "(idx = rfCoreFindEmptyExtSrcMatchIdx()) != CC1352_SRC_MATCH_NONE",
     "line": 1573
    },
    {
     "code": "sReceiveCmd.status == ACTIVE",
     "line": 1577
    },
    {
     "code": "sReceiveCmd.status == IEEE_SUSPENDED",
     "line": 1577
    },
    {
     "code": "rfCoreModifySourceMatchEntry(idx, EXT_ADDRESS, true) == CMDSTA_Done",
     "line": 1580
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "sSrcMatchExtData.srcMatchEn[idx / 32] ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "sSrcMatchExtData.srcMatchEn[idx / 32]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "sSrcMatchExtData.srcMatchEn",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "idx / 32",
     "name": "<operator>.division",
     "nargs": 2
    },
    {
     "code": "1 << (idx % 32)",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "idx % 32",
     "name": "<operator>.modulo",
     "nargs": 2
    }
   ],
   "line_ids": [
    "sSrcMatchExtData",
    "idx"
   ],
   "osv_id": "ARVO-42471519",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::MeshForwarder::GetFramePriority(unsigned char*, unsigned char, ot::Mac::Address const&, ot::Mac::Address const&, unsigned char&)"
  }
 },
 {
  "osv_id": "ARVO-42471829",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 728,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 558
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
    "line": 728,
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "code": "*p = buf",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 728
   },
   "code": "*p = buf",
   "access": {
    "dir": "READ",
    "width": 2,
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
   "control_structures": "IF:736"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "end"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/2087f5a2a743380b36399ba8a2b4ff9e93890fcf/ARVO-42471829/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2087f5a2a743.cpg",
   "testcase_size": 648
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
   "dedup_token": "BEInt<unsigned short, 2>::operator unsigned short() const--OT::IntType<unsigned short, 2u>::operator unsigned int() const--CFF::Charset1_2<OT::IntType<unsigned "
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*p = buf",
     "line": 728
    }
   ],
   "entity_decl": {
    "line": 728,
    "type": "char*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    720,
    742
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
     "line": 736
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "*p = buf",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p",
    "buf"
   ],
   "osv_id": "ARVO-42471829",
   "sites": [
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "buf[32]",
     "line": 723
    }
   ]
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
  "osv_id": "ARVO-42471892",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "uint32_t",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 558
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 127,
    "fn": "CFF::CFF2VariationStore::serialize(hb_serialize_context_t*, CFF::CFF2VariationStore const*)",
    "code": "{HB_TAG ('v','h','a','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TE | HB_TAG ('v','h','a','l') | (hb_tag_t)((((uint32_t)('v') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('v') & 0xFF) << 24) | (((uint32_t)('h') & 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "CFF::CFF2VariationStore::serialize(hb_serialize_context_t*, CFF::CFF2VariationStore const*)",
    "file": "/src/harfbuzz/src/hb-ot-cff2-table.hh",
    "line": 127
   },
   "code": "{HB_TAG ('v','h','a','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TE | HB_TAG ('v','h','a','l') | (hb_tag_t)((((uint32_t)('v') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('v') & 0xFF) << 24) | (((uint32_t)('h') & 0",
   "access": {
    "dir": "READ",
    "width": 62017,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<global>",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:193,IF:200,IF:222,IF:231,FOR:245,IF:246"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/2087f5a2a743380b36399ba8a2b4ff9e93890fcf/ARVO-42471892/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2087f5a2a743.cpg",
   "testcase_size": 383
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--CFF::CFF2VariationStore::serialize(hb_serialize_context_t*, CFF::CFF2VariationStore const*)--_write_cff2(cff2_subset_plan const&, OT::cff2::accel"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "uint32_t",
   "func_lines": [
    1,
    372
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [
    {
     "code": "i < count",
     "line": 245
    },
    {
     "code": "info[i].codepoint == AAT::DELETED_GLYPH",
     "line": 246
    },
    {
     "code": "info->codepoint == AAT::DELETED_GLYPH",
     "line": 253
    }
   ],
   "line_call_count": 18,
   "line_calls": [
    {
     "code": "{HB_TAG ('v','h','a','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TEXT_SPACING,            HB_AAT_LAYOUT_FEATURE_SELECTOR_ALT_HALF_WIDTH_TEXT,            (hb_aat_layout_feature_selector_t) 7}",
     "name": "<operator>.arrayInitializer",
     "nargs": 4
    },
    {
     "code": "HB_TAG ('v','h','a','l')",
     "name": "HB_TAG",
     "nargs": 4
    },
    {
     "code": "(hb_tag_t)((((uint32_t)('v') & 0xFF) << 24) ",
     "name": "<operator>.cast",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('v') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('v') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('v') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "((uint32_t)('v') & 0xFF) << 24",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('v') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('v')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "((uint32_t)('h') & 0xFF) << 16",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('h') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('h')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "((uint32_t)('a') & 0xFF) << 8",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('a') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('a')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('l') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('l')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "(hb_aat_layout_feature_selector_t) 7",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "uint32_t",
    "HB_AAT_LAYOUT_FEATURE_TYPE_TEXT_SPACING",
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_ALT_HALF_WIDTH_TEXT"
   ],
   "osv_id": "ARVO-42471892",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "CFF::CFF2VariationStore::serialize(hb_serialize_context_t*, CFF::CFF2VariationStore const*)"
  }
 },
 {
  "osv_id": "ARVO-42472056",
  "project": "openvswitch",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "spec",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 43,
    "type": "ofpact_learn_spec*",
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
    "line": 51,
    "fn": "learn_check",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "learn_check",
    "file": "/src/openvswitch/lib/learn.c",
    "line": 51
   },
   "code": "spec->src_type == NX_LEARN_SRC_FIELD",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "learn_check",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/aa1a0f1aaf6a772327b712d0507735af5b8c791d/ARVO-42472056/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_aa1a0f1aaf6a.cpg",
   "testcase_size": 148
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
   "dedup_token": "learn_check--ofpacts_check--parse_ofp_str__"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "(spec) = (learn)->specs",
     "line": 47
    },
    {
     "code": "(spec) = ofpact_learn_spec_next(spec)",
     "line": 47
    }
   ],
   "entity_decl": {
    "line": 43,
    "type": "ofpact_learn_spec*"
   },
   "entity_name_cpg": "spec",
   "func_lines": [
    40,
    85
   ],
   "func_params": {
    "names": [
     "learn",
     "src_match"
    ],
    "types": [
     "ofpact_learn*",
     "match*"
    ]
   },
   "guards": [
    {
     "code": "(spec) < ofpact_learn_spec_end(learn)",
     "line": 47
    },
    {
     "code": "spec->src_type == NX_LEARN_SRC_FIELD",
     "line": 51
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "spec->src_type == NX_LEARN_SRC_FIELD",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "spec->src_type",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "NX_LEARN_SRC_FIELD",
     "name": "NX_LEARN_SRC_FIELD",
     "nargs": 0
    },
    {
     "code": "0 << 13",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    }
   ],
   "line_ids": [
    "spec"
   ],
   "osv_id": "ARVO-42472056",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "learn_check"
  }
 },
 {
  "osv_id": "ARVO-42472801",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-aat-layout-kerx-table.hh",
    "line": 442,
    "size": null,
    "type": "hb_buffer_t*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 557,
    "fn": "AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::driver_context_t::transition(AAT::StateTableDriver<AAT::ExtendedTypes, AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData>*, AAT::Entry<AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData> const*)",
    "code": "unlikely (!buffer->successful) | !buffer->successful | buffer->successful | !buffer->successful",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::driver_context_t::transition(AAT::StateTableDriver<AAT::ExtendedTypes, AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData>*, AAT::Entry<AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData> const*)",
    "file": "/src/harfbuzz/src/hb-aat-layout-kerx-table.hh",
    "line": 557
   },
   "code": "unlikely (!buffer->successful) | !buffer->successful | buffer->successful | !buffer->successful",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_hb_buffer_deserialize_glyphs_json",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:453,IF:455,IF:476,GOTO:477,IF:478,GOTO:479,IF:491,GOTO:492,SWITCH:494,BREAK:501,IF:506,BREAK:511"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/574d888c8a409295a952361a39c8e83a52a0fc3d/ARVO-42472801/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_574d888c8a40.cpg",
   "testcase_size": 407
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
   "dedup_token": "AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::driver_context_t::transition(AAT::StateTableDriver<AAT::ExtendedTypes, AAT::KerxSubTableFormat4<AAT::KerxSubT"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 508
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 559
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 571
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 583
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 595
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 607
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 619
    }
   ],
   "entity_decl": {
    "line": 442,
    "type": "hb_buffer_t*"
   },
   "entity_name_cpg": "buffer",
   "func_lines": [
    441,
    641
   ],
   "func_params": {
    "names": [
     "buffer",
     "buf",
     "buf_len",
     "end_ptr",
     "font"
    ],
    "types": [
     "hb_buffer_t*",
     "char*",
     "unsigned int",
     "char**",
     "hb_font_t*"
    ]
   },
   "guards": [
    {
     "code": "p < pe",
     "line": 453
    },
    {
     "code": "p < pe",
     "line": 455
    },
    {
     "code": "*p == (buffer->len ? ',' : '[')",
     "line": 455
    },
    {
     "code": "p == pe",
     "line": 476
    },
    {
     "code": "cs == 0",
     "line": 478
    },
    {
     "code": "_slen > 0",
     "line": 485
    },
    {
     "code": "_deserialize_json_trans_actions[_trans] == 0",
     "line": 491
    },
    {
     "code": "cs == 0",
     "line": 627
    },
    {
     "code": "++p != pe",
     "line": 629
    },
    {
     "code": "p == pe",
     "line": 640
    },
    {
     "code": "*(p-1) != ']'",
     "line": 640
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "unlikely (!buffer->successful)",
     "name": "unlikely",
     "nargs": 1
    },
    {
     "code": "!buffer->successful",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "buffer->successful",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "!buffer->successful",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "buffer->successful",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buffer"
   ],
   "osv_id": "ARVO-42472801",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::driver_context_t::transition(AAT::StateTableDriver<AAT::ExtendedTypes, AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData>*, AAT::Entry<AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData> const*)"
  }
 },
 {
  "osv_id": "ARVO-42472970",
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
    "line": 535
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 176,
    "fn": "r_read_le32",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "r_read_le32",
    "file": "/src/radare2/libr/include/r_endian.h",
    "line": 176
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "r_read_le32",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/ea833632f1eb47e2dba4c5fa174d1880acec3f93/ARVO-42472970/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_ea833632f1eb.cpg",
   "testcase_size": 17410
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
   "shadow_legend_size": 0,
   "dedup_token": "r_read_le32--dex_method_signature2--dex_parse_debug_item"
  },
  "deep": {
   "osv_id": "ARVO-42472970"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "r_read_le32"
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