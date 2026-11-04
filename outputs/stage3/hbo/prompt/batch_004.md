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
  "osv_id": "ARVO-42473294",
  "project": "readstat",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "tmp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 91,
    "type": "uint32_t",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "readstat_parse_sas7bdat",
    "file": "/src/readstat/src/sas/readstat_sas7bdat_read.c",
    "line": 1044
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 92,
    "fn": "sas_read4",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sas_read4",
    "file": "/src/readstat/src/sas/readstat_sas.c",
    "line": 92
   },
   "code": "memcpy(&tmp, data, 4)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sas_read4",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/readstat/address/d2b73886878945df2b95d3c76d13df508f41f0b4/ARVO-42473294/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/readstat_d2b738868789.cpg",
   "testcase_size": 5120
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
   "dedup_token": "sas_read4--sas7bdat_parse_page_pass2--sas7bdat_parse_all_pages_pass2"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 91,
    "type": "uint32_t"
   },
   "entity_name_cpg": "tmp",
   "func_lines": [
    90,
    94
   ],
   "func_params": {
    "names": [
     "data",
     "bswap"
    ],
    "types": [
     "char*",
     "int"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(&tmp, data, 4)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&tmp",
     "name": "<operator>.addressOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "tmp",
    "data"
   ],
   "osv_id": "ARVO-42473294",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sas_read4"
  }
 },
 {
  "osv_id": "ARVO-42473403",
  "project": "readstat",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "n_missing_values",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1177,
    "type": "char",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "sav_parse_records_pass2",
    "file": "/src/readstat/src/spss/readstat_sav_read.c",
    "line": 1300
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256*4+1",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1177,
    "fn": "sav_parse_long_string_missing_values_record",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sav_parse_long_string_missing_values_record",
    "file": "/src/readstat/src/spss/readstat_sav_read.c",
    "line": 1177
   },
   "code": "n_missing_values = *data_ptr++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sav_parse_long_string_missing_values_record",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/readstat/address/08c364729507a7ea8317941f3330330c30daef07/ARVO-42473403/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/readstat_08c364729507.cpg",
   "testcase_size": 4384
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
   "dedup_token": "sav_parse_long_string_missing_values_record--sav_parse_records_pass2--readstat_parse_sav"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "n_missing_values = *data_ptr++",
     "line": 1177
    }
   ],
   "entity_decl": {
    "line": 1177,
    "type": "char"
   },
   "entity_name_cpg": "n_missing_values",
   "func_lines": [
    1161,
    1210
   ],
   "func_params": {
    "names": [
     "data",
     "size",
     "count",
     "ctx"
    ],
    "types": [
     "void*",
     "size_t",
     "size_t",
     "sav_ctx_t*"
    ]
   },
   "guards": [
    {
     "code": "size != 1",
     "line": 1162
    },
    {
     "code": "data_ptr < data_end",
     "line": 1171
    },
    {
     "code": "retval != READSTAT_OK",
     "line": 1174
    },
    {
     "code": "n_missing_values < 1",
     "line": 1178
    },
    {
     "code": "n_missing_values > 3",
     "line": 1178
    },
    {
     "code": "i<ctx->var_index",
     "line": 1183
    },
    {
     "code": "strcmp(var_name_buf, info->longname) == 0",
     "line": 1185
    },
    {
     "code": "j<n_missing_values",
     "line": 1187
    },
    {
     "code": "retval != READSTAT_OK",
     "line": 1191
    },
    {
     "code": "i == ctx->var_index",
     "line": 1198
    },
    {
     "code": "data_ptr != data_end",
     "line": 1204
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "n_missing_values = *data_ptr++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*data_ptr++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "data_ptr++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "n_missing_values",
    "data_ptr"
   ],
   "osv_id": "ARVO-42473403",
   "sites": [
    {
     "args": "256*4+1",
     "callee": "<operator>.alloc",
     "code": "var_name_buf[256*4+1]",
     "line": 1169
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sav_parse_long_string_missing_values_record"
  }
 },
 {
  "osv_id": "ARVO-42473565",
  "project": "file",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "bf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/file/src/encoding.c",
    "line": 460,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 516
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 486,
    "fn": "looks_ucs32",
    "code": "bf[i + 2] << 16 | bf[i + 2] | i + 2 | bf[i + 3] << 24",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "looks_ucs32",
    "file": "/src/file/src/encoding.c",
    "line": 486
   },
   "code": "bf[i + 2] << 16 | bf[i + 2] | i + 2 | bf[i + 3] << 24",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "looks_ucs32",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:466,IF:469,ELSE:471,IF:471,ELSE:474,FOR:478,IF:481,ELSE:485,IF:488,IF:490"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "bf"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/8305d1cc5ec466b2d50d1b6000e7b3c8c4b08853/ARVO-42473565/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/file_8305d1cc5ec4.cpg",
   "testcase_size": 6
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
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "looks_ucs32--file_encoding--file_buffer"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 460,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "bf",
   "func_lines": [
    459,
    496
   ],
   "func_params": {
    "names": [
     "bf",
     "nbytes",
     "ubf",
     "ulen"
    ],
    "types": [
     "unsigned char*",
     "size_t",
     "unichar*",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "nbytes < 4",
     "line": 466
    },
    {
     "code": "bf[0] == 0xff",
     "line": 469
    },
    {
     "code": "bf[1] == 0xfe",
     "line": 469
    },
    {
     "code": "bf[2] == 0",
     "line": 469
    },
    {
     "code": "bf[3] == 0",
     "line": 469
    },
    {
     "code": "bf[0] == 0",
     "line": 471
    },
    {
     "code": "bf[1] == 0",
     "line": 471
    },
    {
     "code": "bf[2] == 0xfe",
     "line": 471
    },
    {
     "code": "bf[3] == 0xff",
     "line": 471
    },
    {
     "code": "i + 1 < nbytes",
     "line": 478
    },
    {
     "code": "ubf[*ulen - 1] == 0xfffe",
     "line": 488
    },
    {
     "code": "ubf[*ulen - 1] < 128",
     "line": 490
    },
    {
     "code": "text_chars[CAST(size_t, ubf[*ulen - 1])] != T",
     "line": 491
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "bf[i + 2] << 16",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "bf[i + 2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i + 2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "bf[i + 3] << 24",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "bf[i + 3]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i + 3",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "bf",
    "i"
   ],
   "osv_id": "ARVO-42473565",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "looks_ucs32"
  }
 },
 {
  "osv_id": "ARVO-42473801",
  "project": "libarchive",
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
    "fn": "init_unpack",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 1850
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "circular_memcpy",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 52,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "circular_memcpy",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/b52dd6c9e4ef7cf95c2a6ae5ab7ccac7f6d462a1/ARVO-42473801/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_b52dd6c9e4ef.cpg",
   "testcase_size": 282
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
   "dedup_token": "__asan_memcpy--circular_memcpy--run_e8e9_filter"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    463,
    475
   ],
   "func_params": {
    "names": [
     "dst",
     "window",
     "mask",
     "start",
     "end"
    ],
    "types": [
     "uint8_t*",
     "uint8_t*",
     "int",
     "int64_t",
     "int64_t"
    ]
   },
   "guards": [
    {
     "code": "(start & mask) > (end & mask)",
     "line": 466
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42473801",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "circular_memcpy"
  }
 },
 {
  "osv_id": "ARVO-42474124",
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
    "fn": "r_bin_open_io",
    "file": "/src/radare2/libr/bin/bin.c",
    "line": 364
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 578,
    "fn": "r_utf8_strlen",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "r_utf8_strlen",
    "file": "/src/radare2/libr/util/utf8.c",
    "line": 578
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "r_utf8_strlen",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/6b64734e6fae4b275e85421a459385a482118b40/ARVO-42474124/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_6b64734e6fae.cpg",
   "testcase_size": 6146
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
   "dedup_token": "r_utf8_strlen--getstr--parse_class"
  },
  "deep": {
   "osv_id": "ARVO-42474124"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "r_utf8_strlen"
  }
 },
 {
  "osv_id": "ARVO-42474135",
  "project": "harfbuzz",
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
    "fn": "_hb_subset_cff2(OT::cff2::accelerator_templ_t<CFF::cff2_private_dict_opset_subset_t, CFF::cff2_private_dict_values_base_t<CFF::op_str_t> > const&, char const*, hb_subset_plan_t*, hb_blob_t**)",
    "file": "/src/harfbuzz/src/hb-subset-cff2.cc",
    "line": 589
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "this->pos ;; new_allocated * sizeof (pos[0])",
   "size_expr_cpg_callee": "realloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 685,
    "fn": "BEInt<unsigned char, 1>::set(unsigned char)",
    "code": "HB_BUFFER_MAX_OPS_DEFAULT",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "BEInt<unsigned char, 1>::set(unsigned char)",
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 685
   },
   "code": "HB_BUFFER_MAX_OPS_DEFAULT",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<global>",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/8aaab78efcac81a05ec919be13792c98741ea1b5/ARVO-42474135/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_8aaab78efcac.cpg",
   "testcase_size": 210
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "BEInt<unsigned char, 1>::set(unsigned char)--CFF::CFFIndex<OT::IntType<unsigned int, 4u> >::set_offset_at(unsigned int, unsigned int)--bool CFF::FDArray<OT::Int"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    1,
    2032
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [
    {
     "code": "a->direction == b->direction",
     "line": 61
    },
    {
     "code": "a->script    == b->script",
     "line": 62
    },
    {
     "code": "a->language  == b->language",
     "line": 63
    },
    {
     "code": "a->reserved1 == b->reserved1",
     "line": 64
    },
    {
     "code": "a->reserved2 == b->reserved2",
     "line": 65
    },
    {
     "code": "size > max_len",
     "line": 117
    },
    {
     "code": "out_info != info",
     "line": 126
    },
    {
     "code": "sizeof (info[0]) == sizeof (pos[0])",
     "line": 134
    },
    {
     "code": "out_info == info",
     "line": 164
    },
    {
     "code": "out_len + num_out > idx + num_in",
     "line": 165
    },
    {
     "code": "idx + count > len",
     "line": 183
    },
    {
     "code": "(uintptr_t) pos % sizeof (scratch_buffer_t) == 0",
     "line": 208
    },
    {
     "code": "out_info != info",
     "line": 338
    },
    {
     "code": "i < num_out",
     "line": 369
    },
    {
     "code": "out_len < i",
     "line": 394
    },
    {
     "code": "out_len > i",
     "line": 403
    },
    {
     "code": "idx < count",
     "line": 416
    },
    {
     "code": "cluster_start == 0",
     "line": 441
    },
    {
     "code": "cluster_end == (unsigned int)-1",
     "line": 441
    },
    {
     "code": "i < count",
     "line": 443
    },
    {
     "code": "i < count",
     "line": 449
    },
    {
     "code": "info[i].cluster < cluster_end",
     "line": 450
    },
    {
     "code": "end - start < 2",
     "line": 460
    },
    {
     "code": "i < j",
     "line": 463
    },
    {
     "code": "i < j",
     "line": 472
    },
    {
     "code": "i < count",
     "line": 504
    },
    {
     "code": "last_cluster != info[i].cluster",
     "line": 505
    },
    {
     "code": "cluster_level == HB_BUFFER_CLUSTER_LEVEL_CHARACTERS",
     "line": 518
    },
    {
     "code": "i < end",
     "line": 526
    },
    {
     "code": "end < len",
     "line": 530
    },
    {
     "code": "info[end - 1].cluster == info[end].cluster",
     "line": 530
    },
    {
     "code": "idx < start",
     "line": 534
    },
    {
     "code": "info[start - 1].cluster == info[start].cluster",
     "line": 534
    },
    {
     "code": "idx == start",
     "line": 538
    },
    {
     "code": "out_info[i - 1].cluster == info[start].cluster",
     "line": 539
    },
    {
     "code": "i < end",
     "line": 542
    },
    {
     "code": "cluster_level == HB_BUFFER_CLUSTER_LEVEL_CHARACTERS",
     "line": 549
    },
    {
     "code": "end - start < 2",
     "line": 552
    },
    {
     "code": "i < end",
     "line": 557
    },
    {
     "code": "out_info[start - 1].cluster == out_info[start].cluster",
     "line": 561
    },
    {
     "code": "end < out_len",
     "line": 565
    },
    {
     "code": "out_info[end - 1].cluster == out_info[end].cluster",
     "line": 565
    },
    {
     "code": "end == out_len",
     "line": 569
    },
    {
     "code": "i < len",
     "line": 570
    },
    {
     "code": "info[i].cluster == out_info[end - 1].cluster",
     "line": 570
    },
    {
     "code": "i < end",
     "line": 573
    },
    {
     "code": "idx + 1 < len",
     "line": 582
    },
    {
     "code": "cluster == info[idx + 1].cluster",
     "line": 582
    },
    {
     "code": "cluster < out_info[out_len - 1].cluster",
     "line": 591
    },
    {
     "code": "out_info[i - 1].cluster == old_cluster",
     "line": 595
    },
    {
     "code": "idx + 1 < len",
     "line": 601
    },
    {
     "code": "content_type == HB_BUFFER_CONTENT_TYPE_UNICODE",
     "line": 641
    },
    {
     "code": "content_type == HB_BUFFER_CONTENT_TYPE_INVALID",
     "line": 642
    },
    {
     "code": "props.script == HB_SCRIPT_INVALID",
     "line": 645
    },
    {
     "code": "i < len",
     "line": 646
    },
    {
     "code": "script != HB_SCRIPT_COMMON",
     "line": 648
    },
    {
     "code": "script != HB_SCRIPT_INHERITED",
     "line": 648
    },
    {
     "code": "script != HB_SCRIPT_UNKNOWN",
     "line": 648
    },
    {
     "code": "props.direction == HB_DIRECTION_INVALID",
     "line": 658
    },
    {
     "code": "props.direction == HB_DIRECTION_INVALID",
     "line": 660
    },
    {
     "code": "props.language == HB_LANGUAGE_INVALID",
     "line": 665
    },
    {
     "code": "length == 0",
     "line": 1333
    },
    {
     "code": "length > buffer->len",
     "line": 1339
    },
    {
     "code": "buffer->content_type == HB_BUFFER_CONTENT_TYPE_UNICODE",
     "line": 1535
    },
    {
     "code": "buffer->content_type == HB_BUFFER_CONTENT_TYPE_INVALID",
     "line": 1536
    },
    {
     "code": "text_length == -1",
     "line": 1541
    },
    {
     "code": "item_length == -1",
     "line": 1544
    },
    {
     "code": "item_offset > 0",
     "line": 1556
    },
    {
     "code": "start < prev",
     "line": 1562
    },
    {
     "code": "buffer->context_len[0] < buffer->CONTEXT_LENGTH",
     "line": 1562
    },
    {
     "code": "next < end",
     "line": 1572
    },
    {
     "code": "next < end",
     "line": 1583
    },
    {
     "code": "buffer->context_len[1] < buffer->CONTEXT_LENGTH",
     "line": 1583
    },
    {
     "code": "buffer->have_positions == source->have_positions",
     "line": 1752
    },
    {
     "code": "buffer->content_type == source->content_type",
     "line": 1754
    },
    {
     "code": "end > source->len",
     "line": 1757
    },
    {
     "code": "start > end",
     "line": 1759
    },
    {
     "code": "start == end",
     "line": 1761
    },
    {
     "code": "buffer->len + (end - start) < buffer->len",
     "line": 1769
    },
    {
     "code": "i < end",
     "line": 1803
    },
    {
     "code": "i < end",
     "line": 1810
    },
    {
     "code": "i < end",
     "line": 1833
    },
    {
     "code": "buffer->content_type == HB_BUFFER_CONTENT_TYPE_GLYPHS",
     "line": 1856
    },
    {
     "code": "buffer->content_type == HB_BUFFER_CONTENT_TYPE_INVALID",
     "line": 1857
    },
    {
     "code": "(((unsigned int)(buffer->props.direction)) & ~2U) == 5",
     "line": 1859
    },
    {
     "code": "end < count",
     "line": 1867
    },
    {
     "code": "info[start].cluster != info[end].cluster",
     "line": 1868
    },
    {
     "code": "i < end",
     "line": 1879
    },
    {
     "code": "j > start",
     "line": 1882
    },
    {
     "code": "compar (&info[j - 1], &info[i]) > 0",
     "line": 1882
    },
    {
     "code": "i == j",
     "line": 1884
    },
    {
     "code": "buffer->content_type != reference->content_type",
     "line": 1920
    },
    {
     "code": "dottedcircle_glyph != (hb_codepoint_t) -1",
     "line": 1924
    },
    {
     "code": "buffer->len != count",
     "line": 1928
    },
    {
     "code": "i < count",
     "line": 1936
    },
    {
     "code": "info[i].codepoint == dottedcircle_glyph",
     "line": 1938
    },
    {
     "code": "info[i].codepoint == 0",
     "line": 1940
    },
    {
     "code": "i < count",
     "line": 1952
    },
    {
     "code": "buf_info->codepoint != ref_info->codepoint",
     "line": 1954
    },
    {
     "code": "buf_info->cluster != ref_info->cluster",
     "line": 1956
    },
    {
     "code": "ref_info->codepoint == dottedcircle_glyph",
     "line": 1960
    },
    {
     "code": "ref_info->codepoint == 0",
     "line": 1962
    },
    {
     "code": "buffer->content_type == HB_BUFFER_CONTENT_TYPE_GLYPHS",
     "line": 1968
    },
    {
     "code": "i < count",
     "line": 1973
    },
    {
     "code": "(unsigned int) abs (buf_pos->x_advance - ref_pos->x_advance) > position_fuzz",
     "line": 1975
    },
    {
     "code": "(unsigned int) abs (buf_pos->y_advance - ref_pos->y_advance) > position_fuzz",
     "line": 1976
    },
    {
     "code": "(unsigned int) abs (buf_pos->x_offset - ref_pos->x_offset) > position_fuzz",
     "line": 1977
    },
    {
     "code": "(unsigned int) abs (buf_pos->y_offset - ref_pos->y_offset) > position_fuzz",
     "line": 1978
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "HB_BUFFER_MAX_OPS_DEFAULT",
     "name": "HB_BUFFER_MAX_OPS_DEFAULT",
     "nargs": 0
    }
   ],
   "line_ids": [],
   "osv_id": "ARVO-42474135",
   "sites": [
    {
     "args": "this->pos ;; new_allocated * sizeof (pos[0])",
     "callee": "realloc",
     "code": "realloc (pos, new_allocated * sizeof (pos[0]))",
     "line": 138
    },
    {
     "args": "this->info ;; new_allocated * sizeof (info[0])",
     "callee": "realloc",
     "code": "realloc (info, new_allocated * sizeof (info[0]))",
     "line": 139
    },
    {
     "args": "",
     "callee": "deallocate_var_all",
     "code": "deallocate_var_all ()",
     "line": 257
    },
    {
     "args": "buffer->info",
     "callee": "free",
     "code": "free (buffer->info)",
     "line": 777
    },
    {
     "args": "buffer->pos",
     "callee": "free",
     "code": "free (buffer->pos)",
     "line": 778
    },
    {
     "args": "buffer",
     "callee": "free",
     "code": "free (buffer)",
     "line": 782
    },
    {
     "args": "100",
     "callee": "<operator>.alloc",
     "code": "buf[100]",
     "line": 2029
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "BEInt<unsigned char, 1>::set(unsigned char)"
  }
 },
 {
  "osv_id": "ARVO-42474270",
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
    "fn": "Elf32_r_bin_elf_compiler",
    "file": "/src/radare2/libr/../libr/bin/p/../format/elf/elf.c",
    "line": 3871
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3889,
    "fn": "Elf32_r_bin_elf_compiler",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Elf32_r_bin_elf_compiler",
    "file": "/src/radare2/libr/bin/format/elf/elf.c",
    "line": 3889
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Elf32_r_bin_elf_compiler",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/059b335bb22f9eaf98a5479200572494a1aea8d4/ARVO-42474270/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_059b335bb22f.cpg",
   "testcase_size": 5965
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "Elf32_r_bin_elf_compiler--info--r_bin_object_set_items"
  },
  "deep": {
   "osv_id": "ARVO-42474270"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Elf32_r_bin_elf_compiler"
  }
 },
 {
  "osv_id": "ARVO-42474568",
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
    "fn": "get_relocs_64",
    "file": "/src/radare2/libr/../libr/bin/p/../format/mach0/mach0.c",
    "line": 2077
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 177,
    "fn": "r_buf_cpy",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "r_buf_cpy",
    "file": "/src/radare2/libr/util/buf.c",
    "line": 177
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 34,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "r_buf_cpy",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/460d55ea83d00d8c4b5b1d13620ae05236b76323/ARVO-42474568/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_460d55ea83d0.cpg",
   "testcase_size": 94
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
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memmove--r_buf_cpy--get_relocs_64"
  },
  "deep": {
   "osv_id": "ARVO-42474568"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "r_buf_cpy"
  }
 },
 {
  "osv_id": "ARVO-42474837",
  "project": "zstd",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "val",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 171,
    "type": "U32",
    "size": null
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
    "line": 171,
    "fn": "MEM_read32",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "MEM_read32",
    "file": "/src/zstd/lib/common/mem.h",
    "line": 171
   },
   "code": "memcpy(&val, memPtr, sizeof(val))",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "MEM_read32",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/zstd/address/9ad7ea44ec9644c618c2e82be5960d868e48745d/ARVO-42474837/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/zstd_9ad7ea44ec96.cpg",
   "testcase_size": 43
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "dedup_token": "MEM_read32--ZSTDv05_decodeSequence--ZSTDv05_decompressSequences"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 171,
    "type": "U32"
   },
   "entity_name_cpg": "val",
   "func_lines": [
    169,
    172
   ],
   "func_params": {
    "names": [
     "memPtr"
    ],
    "types": [
     "void*"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memcpy(&val, memPtr, sizeof(val))",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&val",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "sizeof(val)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "val",
    "memPtr"
   ],
   "osv_id": "ARVO-42474837",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "MEM_read32"
  }
 },
 {
  "osv_id": "ARVO-42474963",
  "project": "net-snmp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "string",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/net-snmp/agent/mibgroup/agentx/protocol.c",
    "line": 1238,
    "size": null,
    "type": "rszbuf*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 238
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": null,
   "size_expr_cpg_callee": "sprint_realloc_asciistring"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1248,
    "fn": "agentx_parse_string",
    "code": "memmove(string->buf, data + 4, len) | string->buf | data + 4",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "agentx_parse_string",
    "file": "/src/net-snmp/agent/mibgroup/agentx/protocol.c",
    "line": 1248
   },
   "code": "memmove(string->buf, data + 4, len) | string->buf | data + 4",
   "access": {
    "dir": "READ",
    "width": 538976288,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "agentx_parse_string",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1244,IF:1254,IF:1266,ELSE:1269,IF:1272"
  },
  "call_chain": [],
  "types": {
   "entity_type": "rszbuf*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "data",
   "string"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/1db5d4df050768a7d93fab12f2e0ffec19a830e1/ARVO-42474963/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_1db5d4df0507.cpg",
   "testcase_size": 26
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
   "dedup_token": "__asan_memmove--agentx_parse_string--agentx_parse"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "string->used = len",
     "line": 1250
    }
   ],
   "entity_decl": {
    "line": 1238,
    "type": "rszbuf*"
   },
   "entity_name_cpg": "string",
   "func_lines": [
    1237,
    1277
   ],
   "func_params": {
    "names": [
     "data",
     "length",
     "string",
     "network_byte_order"
    ],
    "types": [
     "u_char*",
     "size_t*",
     "rszbuf*",
     "u_int"
    ]
   },
   "guards": [
    {
     "code": "*length < len + 4",
     "line": 1254
    },
    {
     "code": "buf != NULL",
     "line": 1272
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memmove(string->buf, data + 4, len)",
     "name": "memmove",
     "nargs": 3
    },
    {
     "code": "string->buf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "data + 4",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "string",
    "data",
    "len"
   ],
   "osv_id": "ARVO-42474963",
   "sites": [
    {
     "args": null,
     "callee": "sprint_realloc_asciistring",
     "code": "sprint_realloc_asciistring(&buf, &buf_len, &out_len, 1,",
     "line": 1266
    },
    {
     "args": "buf",
     "callee": "free",
     "code": "free(buf)",
     "line": 1273
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "agentx_parse_string"
  }
 },
 {
  "osv_id": "ARVO-42475066",
  "project": "libarchive",
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
    "fn": "init_unpack",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 1850
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "circular_memcpy",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "circular_memcpy",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/b52dd6c9e4ef7cf95c2a6ae5ab7ccac7f6d462a1/ARVO-42475066/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_b52dd6c9e4ef.cpg",
   "testcase_size": 246
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
   "dedup_token": "__asan_memcpy--circular_memcpy--run_arm_filter"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    463,
    475
   ],
   "func_params": {
    "names": [
     "dst",
     "window",
     "mask",
     "start",
     "end"
    ],
    "types": [
     "uint8_t*",
     "uint8_t*",
     "int",
     "int64_t",
     "int64_t"
    ]
   },
   "guards": [
    {
     "code": "(start & mask) > (end & mask)",
     "line": 466
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42475066",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "circular_memcpy"
  }
 },
 {
  "osv_id": "ARVO-42475116",
  "project": "open62541",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "parseCtx",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/src/ua_types_encoding_json.c",
    "line": 2249,
    "size": null,
    "type": "ParseCtx*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "UA_memoryManager_malloc",
    "file": "/src/open62541/tests/fuzz/custom_memory_manager.c",
    "line": 132
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2296,
    "fn": "searchObjectForKeyRec",
    "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJEC | parseCtx->tokenArray[parseCtx->index].type | parseCtx->tokenArray[parseCtx->index] | parseCtx->tokenArray",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "searchObjectForKeyRec",
    "file": "/src/open62541/src/ua_types_encoding_json.c",
    "line": 2296
   },
   "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJEC | parseCtx->tokenArray[parseCtx->index].type | parseCtx->tokenArray[parseCtx->index] | parseCtx->tokenArray",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "searchObjectForKeyRec",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJECT | parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJECT | parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJECT",
   "guard_count": 3,
   "control_structures": "DO:2252,IF:2252,IF:2254,DO:2258,IF:2258,FOR:2261,DO:2263,IF:2263,IF:2264,IF:2265,BREAK:2270,DO:2275"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ParseCtx*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "parseCtx"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/open62541/address/ac0d94217d06a229c9c671cfa0e37b497114848a/ARVO-42475116/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_ac0d94217d06.cpg",
   "testcase_size": 2286
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
   "dedup_token": "searchObjectForKeyRec--searchObjectForKeyRec--searchObjectForKeyRec"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 2249,
    "type": "ParseCtx*"
   },
   "entity_name_cpg": "parseCtx",
   "func_lines": [
    2247,
    2309
   ],
   "func_params": {
    "names": [
     "searchKey",
     "ctx",
     "parseCtx",
     "resultIndex",
     "depth"
    ],
    "types": [
     "char*",
     "CtxJson*",
     "ParseCtx*",
     "size_t*",
     "UA_UInt16"
    ]
   },
   "guards": [
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJECT",
     "line": 2254
    },
    {
     "code": "i < objectCount",
     "line": 2261
    },
    {
     "code": "depth == 0",
     "line": 2264
    },
    {
     "code": "jsoneq((char*)ctx->pos, &parseCtx->tokenArray[parseCtx->index], searchKey) == 0",
     "line": 2265
    },
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJECT",
     "line": 2277
    },
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_ARRAY",
     "line": 2280
    },
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_ARRAY",
     "line": 2288
    },
    {
     "code": "i < arraySize",
     "line": 2295
    },
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJECT",
     "line": 2296
    },
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_ARRAY",
     "line": 2299
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type == JSMN_OBJECT",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "parseCtx->tokenArray[parseCtx->index].type",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "parseCtx->tokenArray[parseCtx->index]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "parseCtx->tokenArray",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "parseCtx->index",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "parseCtx",
    "JSMN_OBJECT"
   ],
   "osv_id": "ARVO-42475116",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "searchObjectForKeyRec"
  }
 },
 {
  "osv_id": "ARVO-42475119",
  "project": "open62541",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "bin",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/deps/base64.c",
    "line": 125,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "UA_unbase64",
    "file": "/src/open62541/deps/base64.c",
    "line": 140
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "(size_t) (*flen)",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "code": "malloc( (size_t) (*flen) )",
    "fn": "UA_unbase64",
    "kind": "malloc",
    "line": 140,
    "origin": "cpg",
    "args": "(size_t) (*flen)"
   },
   {
    "kind": "unknown",
    "line": 167,
    "fn": "UA_unbase64",
    "code": "bin[cb++] = (unsigned char)((B<<4) | (C>>2)) | bin[cb++] | cb++ | (unsigned char)((B<<4) | (C>>2))",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "UA_unbase64",
    "file": "/src/open62541/deps/base64.c",
    "line": 167
   },
   "code": "bin[cb++] = (unsigned char)((B<<4) | (C>>2)) | bin[cb++] | cb++ | (unsigned char)((B<<4) | (C>>2))",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "UA_unbase64",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:130,IF:136,IF:137,IF:141,FOR:148,IF:160,ELSE:169,IF:169"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/open62541/address/ac0d94217d06a229c9c671cfa0e37b497114848a/ARVO-42475119/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_ac0d94217d06.cpg",
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "UA_unbase64--ByteString_decodeJson--decodeFields"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "bin = (unsigned char*)malloc( (size_t) (*flen) )",
     "line": 140
    },
    {
     "code": "bin[cb++] = (unsigned char)((A<<2) ",
     "line": 155
    },
    {
     "code": "bin[cb++] = (unsigned char)((B<<4) ",
     "line": 156
    },
    {
     "code": "bin[cb++] = (unsigned char)((C<<6) ",
     "line": 157
    },
    {
     "code": "bin[cb++] = (unsigned char)((A<<2) ",
     "line": 166
    },
    {
     "code": "bin[cb++] = (unsigned char)((B<<4) ",
     "line": 167
    },
    {
     "code": "bin[cb++] = (unsigned char)((A<<2) ",
     "line": 174
    }
   ],
   "entity_decl": {
    "line": 125,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "bin",
   "func_lines": [
    122,
    178
   ],
   "func_params": {
    "names": [
     "ascii",
     "len",
     "flen"
    ],
    "types": [
     "char*",
     "int",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "len < 2",
     "line": 130
    },
    {
     "code": "safeAsciiPtr[ len-1 ]=='='",
     "line": 136
    },
    {
     "code": "safeAsciiPtr[ len-2 ]=='='",
     "line": 137
    },
    {
     "code": "pad==1",
     "line": 160
    },
    {
     "code": "pad==2",
     "line": 169
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "bin[cb++] = (unsigned char)((B<<4) ",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "bin[cb++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "cb++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "(unsigned char)((B<<4) ",
     "name": "<operator>.cast",
     "nargs": null
    },
    {
     "code": "(B<<4) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "B<<4",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "C>>2",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    }
   ],
   "line_ids": [
    "bin",
    "cb",
    "B",
    "C"
   ],
   "osv_id": "ARVO-42475119",
   "sites": [
    {
     "args": "(size_t) (*flen)",
     "callee": "malloc",
     "code": "malloc( (size_t) (*flen) )",
     "line": 140
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "UA_unbase64"
  }
 },
 {
  "osv_id": "ARVO-42475136",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "info",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-open-type.hh",
    "line": 218,
    "size": null,
    "type": "hb_glyph_info_t"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 441,
    "fn": "OT::UnsizedArrayOf<OT::IntType<unsigned char, 1u> >::copy(hb_serialize_context_t*, unsigned int) const",
    "code": "&info.codepoint | info.codepoint",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OT::UnsizedArrayOf<OT::IntType<unsigned char, 1u> >::copy(hb_serialize_context_t*, unsigned int) const",
    "file": "/src/harfbuzz/src/hb-open-type.hh",
    "line": 441
   },
   "code": "&info.codepoint | info.codepoint",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_hb_buffer_deserialize_glyphs_text",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:209,IF:211,IF:228,GOTO:229,IF:230,GOTO:231,IF:236,IF:239,ELSE:242,ELSE:244,GOTO:248,IF:253"
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_glyph_info_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "buffer",
   "buf",
   "buf_len",
   "font"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/5c0f62adc969696b46c1ceb57cd3c2fa408eb94f/ARVO-42475136/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_5c0f62adc969.cpg",
   "testcase_size": 34
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
   "dedup_token": "OT::UnsizedArrayOf<OT::IntType<unsigned char, 1u> >::copy(hb_serialize_context_t*, unsigned int) const--bool OT::OffsetTo<OT::UnsizedArrayOf<OT::IntType<unsigne"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "info = {0}",
     "line": 218
    }
   ],
   "entity_decl": {
    "line": 218,
    "type": "hb_glyph_info_t"
   },
   "entity_name_cpg": "info",
   "func_lines": [
    197,
    528
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
     "line": 209
    },
    {
     "code": "p < pe",
     "line": 211
    },
    {
     "code": "*p == (buffer->len ? '",
     "line": 211
    },
    {
     "code": "p == pe",
     "line": 228
    },
    {
     "code": "cs == 0",
     "line": 230
    },
    {
     "code": "_deserialize_text_cond_actions[_trans] == 0",
     "line": 253
    },
    {
     "code": "cs == 0",
     "line": 399
    },
    {
     "code": "p != pe",
     "line": 402
    },
    {
     "code": "p == eof",
     "line": 406
    },
    {
     "code": "_deserialize_text_eof_cond_spaces[cs] != -1",
     "line": 408
    },
    {
     "code": "_upper < _lower",
     "line": 417
    },
    {
     "code": "_cpc < (int)(*( _mid))",
     "line": 421
    },
    {
     "code": "_cpc > (int)(*( _mid))",
     "line": 423
    },
    {
     "code": "p == pe",
     "line": 527
    },
    {
     "code": "*(p-1) != ']'",
     "line": 527
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "&info.codepoint",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "info.codepoint",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "info"
   ],
   "osv_id": "ARVO-42475136",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OT::UnsizedArrayOf<OT::IntType<unsigned char, 1u> >::copy(hb_serialize_context_t*, unsigned int) const"
  }
 },
 {
  "osv_id": "ARVO-42475265",
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
    "line": 30
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 46,
    "fn": "perfetto::base::Hash::Update(char const*, unsigned long)",
    "code": "!GetService() | GetService()",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "perfetto::base::Hash::Update(char const*, unsigned long)",
    "file": "/src/perfetto/include/perfetto/base/hash.h",
    "line": 46
   },
   "code": "!GetService() | GetService()",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "GetCategories",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/perfetto/address/b141eea0b61a6087927aba85f2f03ce7a7b78c59/ARVO-42475265/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_b141eea0b61a.cpg",
   "testcase_size": 13192
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
   "dedup_token": "perfetto::base::Hash::Update(char const*, unsigned long)--perfetto::base::StringView::Hash() const--perfetto::trace_processor::StringPool::InternString(perfetto"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    43,
    65
   ],
   "func_params": {
    "names": [
     "categories",
     "size_of_arr"
    ],
    "types": [
     "TracingVendorCategory*",
     "size_t*"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "!GetService()",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "GetService()",
     "name": "GetService",
     "nargs": 0
    }
   ],
   "line_ids": [],
   "osv_id": "ARVO-42475265",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "perfetto::base::Hash::Update(char const*, unsigned long)"
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