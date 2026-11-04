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
  "osv_id": "ARVO-42509256",
  "project": "libvips",
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
    "fn": "g_malloc0 (/out/thumbnail_fuzzer+0x3bc8b50)",
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
    "line": 181,
    "fn": "vips_rect_intersectrect",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vips_rect_intersectrect",
    "file": "/src/libvips/libvips/iofuncs/rect.c",
    "line": 181
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vips_rect_intersectrect",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42509256/report.log",
   "cpg": null,
   "testcase_size": 79
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
   "dedup_token": "vips_rect_intersectrect--vips_foreign_load_pdf_generate--vips_region_generate"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vips_rect_intersectrect"
  }
 },
 {
  "osv_id": "ARVO-42509342",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "path",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "line": 1322,
    "size": null,
    "type": "sc_path*"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "sc_file_new",
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 619
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1351,
    "fn": "do_fileid",
    "code": "memcpy(path->value + path->len, temp.value, 2) | path->value + path->len | path->value | path->len",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "do_fileid",
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "line": 1351
   },
   "code": "memcpy(path->value + path->len, temp.value, 2) | path->value + path->len | path->value | path->len",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "do_fileid",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1324,IF:1334,IF:1340,IF:1341,IF:1345"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_path*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509342/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 50863
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
   "dedup_token": "__asan_memcpy--do_fileid--process_command"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*path = NULL",
     "line": 1322
    },
    {
     "code": "path = &file->path",
     "line": 1329
    }
   ],
   "entity_decl": {
    "line": 1322,
    "type": "sc_path*"
   },
   "entity_name_cpg": "path",
   "func_lines": [
    1317,
    1356
   ],
   "func_params": {
    "names": [
     "cur",
     "argc",
     "argv"
    ],
    "types": [
     "state*",
     "int",
     "char**"
    ]
   },
   "guards": [
    {
     "code": "temp.len != 2",
     "line": 1334
    },
    {
     "code": "df->path.len + 2 > sizeof(df->path.value)",
     "line": 1345
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "memcpy(path->value + path->len, temp.value, 2)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "path->value + path->len",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "path->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "path->len",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "temp.value",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "path",
    "temp"
   ],
   "osv_id": "ARVO-42509342",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "do_fileid"
  }
 },
 {
  "osv_id": "ARVO-42509477",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "profile",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "line": 1214,
    "size": null,
    "type": "sc_profile_t*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1254,
    "fn": "new_file",
    "code": "profile->df[df_type] = file | profile->df[df_type] | profile->df",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "new_file",
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "line": 1254
   },
   "code": "profile->df[df_type] = file | profile->df[df_type] | profile->df",
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "new_file",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1219,IF:1224,ELSE:1226,IF:1226,IF:1227,ELSE:1233,IF:1233,IF:1234,ELSE:1240,IF:1240,IF:1241,ELSE:1247"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_profile_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "cur"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509477/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 5989
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
   "dedup_token": "new_file--process_ef--process_block"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*profile = cur->profile",
     "line": 1214
    },
    {
     "code": "profile->df[df_type] = file",
     "line": 1254
    }
   ],
   "entity_decl": {
    "line": 1214,
    "type": "sc_profile_t*"
   },
   "entity_name_cpg": "profile",
   "func_lines": [
    1211,
    1275
   ],
   "func_params": {
    "names": [
     "cur",
     "name",
     "type"
    ],
    "types": [
     "state*",
     "char*",
     "unsigned int"
    ]
   },
   "guards": [
    {
     "code": "(info = sc_profile_find_file(profile, NULL, name)) != NULL",
     "line": 1219
    },
    {
     "code": "file->type != type",
     "line": 1257
    },
    {
     "code": "file->type == SC_FILE_TYPE_DF",
     "line": 1259
    },
    {
     "code": "file->type == SC_FILE_TYPE_BSO",
     "line": 1260
    },
    {
     "code": "info == NULL",
     "line": 1269
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "profile->df[df_type] = file",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "profile->df[df_type]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "profile->df",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "profile",
    "df_type",
    "file"
   ],
   "osv_id": "ARVO-42509477",
   "sites": [
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 1264
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "new_file"
  }
 },
 {
  "osv_id": "ARVO-42509978",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "file",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-epass2003.c",
    "line": 310,
    "size": null,
    "type": "sc_file*"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "sc_file_new",
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 619
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 379,
    "fn": "cosm_new_file",
    "code": "file->path.value[file->path.len - 1] = (num & 0xFF) | file->path.value[file->path.len - 1] | file->path.value | file->path",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "cosm_new_file",
    "file": "/src/opensc/src/pkcs15init/pkcs15-epass2003.c",
    "line": 379
   },
   "code": "file->path.value[file->path.len - 1] = (num & 0xFF) | file->path.value[file->path.len - 1] | file->path.value | file->path",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cosm_new_file",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:314,WHILE:317,SWITCH:318,BREAK:323,BREAK:328,BREAK:333,BREAK:338,BREAK:342,BREAK:346,BREAK:350,IF:352,BREAK:353"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_file*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "num"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509978/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 14971
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
   "dedup_token": "cosm_new_file--epass2003_pkcs15_generate_key--sc_pkcs15init_generate_key"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "file->path.value[file->path.len - 1] = (num & 0xFF)",
     "line": 379
    },
    {
     "code": "file->type = SC_FILE_TYPE_INTERNAL_EF",
     "line": 380
    },
    {
     "code": "file->ef_structure = structure",
     "line": 381
    }
   ],
   "entity_decl": {
    "line": 310,
    "type": "sc_file*"
   },
   "entity_name_cpg": "file",
   "func_lines": [
    306,
    392
   ],
   "func_params": {
    "names": [
     "profile",
     "card",
     "type",
     "num",
     "out"
    ],
    "types": [
     "sc_profile*",
     "sc_card*",
     "unsigned int",
     "unsigned int",
     "sc_file**"
    ]
   },
   "guards": [
    {
     "code": "sc_profile_get_file(profile, _template, &file) < 0",
     "line": 369
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "file->path.value[file->path.len - 1] = (num & 0xFF)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "file->path.value[file->path.len - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "file->path.value",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "file->path",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "file->path.len - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "file->path.len",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "file->path",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "num & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    }
   ],
   "line_ids": [
    "file",
    "num"
   ],
   "osv_id": "ARVO-42509978",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "cosm_new_file"
  }
 },
 {
  "osv_id": "ARVO-42510029",
  "project": "fluent-bit",
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
    "fn": "flb_malloc",
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "line": 56
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "onig_node_str_cat",
    "file": "/src/fluent-bit/lib/onigmo/regparse.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 3,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "onig_node_str_cat",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42510029/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_dbe29a1a77b5.cpg",
   "testcase_size": 724
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
   "dedup_token": "__interceptor_memcpy--onig_node_str_cat--node_new_str"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    1375,
    1409
   ],
   "func_params": {
    "names": [
     "node",
     "s",
     "end"
    ],
    "types": [
     "Node*",
     "OnigUChar*",
     "OnigUChar*"
    ]
   },
   "guards": [
    {
     "code": "addlen > 0",
     "line": 1380
    },
    {
     "code": "NSTR(node)->capa > 0",
     "line": 1383
    },
    {
     "code": "len + addlen > NODE_STR_BUF_SIZE - 1",
     "line": 1383
    },
    {
     "code": "NSTR(node)->s == NSTR(node)->buf",
     "line": 1391
    },
    {
     "code": "((void *)(p)) == (void *)0",
     "line": 1397
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42510029",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "onig_node_str_cat"
  }
 },
 {
  "osv_id": "ARVO-42510070",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "reg",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/lib/onigmo/regcomp.c",
    "line": 287,
    "size": null,
    "type": "regex_t*"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "node_new",
    "file": "/src/fluent-bit/lib/onigmo/regparse.c",
    "line": 1125
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "(((reg)))->p ;; (((reg)))->alloc",
   "size_expr_cpg_callee": "realloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 289,
    "fn": "add_bytes",
    "code": "BBUF_ADD(reg, bytes, len) | int | ((reg)->used) + (int)((len)) | (reg)->used",
    "origin": "report:crash",
    "args": "(((reg)))->p ;; (((reg)))->alloc"
   },
   {
    "code": "realloc((((reg)))->p, (((reg)))->alloc)",
    "fn": "add_bytes",
    "kind": "realloc",
    "line": 289,
    "origin": "cpg",
    "args": "(((reg)))->p ;; (((reg)))->alloc"
   }
  ],
  "crash": {
   "site": {
    "fn": "add_bytes",
    "file": "/src/fluent-bit/lib/onigmo/regcomp.c",
    "line": 289
   },
   "code": "BBUF_ADD(reg, bytes, len) | int | ((reg)->used) + (int)((len)) | (reg)->used",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "add_bytes",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:289,IF:289,DO:289,DO:289,IF:289,IF:289"
  },
  "call_chain": [],
  "types": {
   "entity_type": "regex_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "reg",
   "bytes",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42510070/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_dbe29a1a77b5.cpg",
   "testcase_size": 1024
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
   "dedup_token": "__interceptor_memcpy--add_bytes--add_compile_string"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 287,
    "type": "regex_t*"
   },
   "entity_name_cpg": "reg",
   "func_lines": [
    286,
    291
   ],
   "func_params": {
    "names": [
     "reg",
     "bytes",
     "len"
    ],
    "types": [
     "regex_t*",
     "OnigUChar*",
     "OnigDistance"
    ]
   },
   "guards": [
    {
     "code": "((reg))->alloc < (unsigned int)used",
     "line": 289
    },
    {
     "code": "(((reg)))->alloc < (unsigned int)used",
     "line": 289
    },
    {
     "code": "((void *)(tmp)) == (void *)0",
     "line": 289
    },
    {
     "code": "((reg))->used < (unsigned int)used",
     "line": 289
    }
   ],
   "line_call_count": 33,
   "line_calls": [
    {
     "code": "BBUF_ADD(reg, bytes, len)",
     "name": "BBUF_ADD",
     "nargs": 3
    },
    {
     "code": "int",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "((reg)->used) + (int)((len))",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(reg)->used",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(int)((len))",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "((reg))->alloc < (unsigned int)used",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "((reg))->alloc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(unsigned int)used",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(((reg)))->alloc *= 2",
     "name": "<operator>.assignmentMultiplication",
     "nargs": 2
    },
    {
     "code": "(((reg)))->alloc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(((reg)))->alloc < (unsigned int)used",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "(((reg)))->alloc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(unsigned int)used",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "tmp = (OnigUChar *)realloc((((reg)))->p, (((reg)))->alloc)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(OnigUChar *)realloc((((reg)))->p, (((reg)))->alloc)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "realloc((((reg)))->p, (((reg)))->alloc)",
     "name": "realloc",
     "nargs": 2
    },
    {
     "code": "(((reg)))->p",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(((reg)))->alloc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "((void *)(tmp)) == (void *)0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "(void *)(tmp)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(void *)0",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "-5",
     "name": "<operator>.minus",
     "nargs": 1
    },
    {
     "code": "(((reg)))->p = tmp",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(((reg)))->p",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "memcpy(((reg))->p + ((reg)->used), ((bytes)), ((len)))",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "((reg))->p + ((reg)->used)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "((reg))->p",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(reg)->used",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "((reg))->used < (unsigned int)used",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "((reg))->used",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(unsigned int)used",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "((reg))->used = used",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "((reg))->used",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "reg",
    "bytes",
    "len",
    "used",
    "tmp"
   ],
   "osv_id": "ARVO-42510070",
   "sites": [
    {
     "args": "(((reg)))->p ;; (((reg)))->alloc",
     "callee": "realloc",
     "code": "realloc((((reg)))->p, (((reg)))->alloc)",
     "line": 289
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "add_bytes"
  }
 },
 {
  "osv_id": "ARVO-42510312",
  "project": "libvips",
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
    "fn": "jxl::CacheAligned::Allocate(unsigned long, unsigned long)",
    "file": "/src/libjxl/lib/jxl/base/cache_aligned.cc",
    "line": 87
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 380,
    "fn": "vips_foreign_load_jxl_process",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vips_foreign_load_jxl_process",
    "file": "/src/libvips/libvips/foreign/jxlload.c",
    "line": 380
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vips_foreign_load_jxl_process",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42510312/report.log",
   "cpg": null,
   "testcase_size": 857
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
   "dedup_token": "__asan_memcpy--jxl::N_AVX3::BlendingStage::ProcessPaddingRow(std::__1::vector<std::__1::vector<float*, std::__1::allocator<float*> >, std::__1::allocator<std::_"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vips_foreign_load_jxl_process"
  }
 },
 {
  "osv_id": "ARVO-42510459",
  "project": "kimageformats",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "device",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/kimageformats/src/imageformats/psd.cpp",
    "line": 544,
    "size": null,
    "type": "QIODevice*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "QImageData::create(QSize const&, QImage::Format)",
    "file": "/src/qtbase/src/gui/image/qimage.cpp",
    "line": 164
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 557,
    "fn": "void (anonymous namespace)::planarToChunchy<unsigned short>(unsigned char*, char const*, int, int, int)",
    "code": "device->isReadable() && ANIHandler::canRead(device) | device->isReadable() | ANIHandler::canRead(device)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "void (anonymous namespace)::planarToChunchy<unsigned short>(unsigned char*, char const*, int, int, int)",
    "file": "/src/kimageformats/src/imageformats/psd.cpp",
    "line": 557
   },
   "code": "device->isReadable() && ANIHandler::canRead(device) | device->isReadable() | ANIHandler::canRead(device)",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "capabilities",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:546,IF:549,IF:552,IF:557"
  },
  "call_chain": [],
  "types": {
   "entity_type": "QIODevice*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "device"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kimageformats/address/98f19c60aed45e81cad631825c212005889b459b/ARVO-42510459/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_98f19c60aed4.cpg",
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
   "dedup_token": "void (anonymous namespace)::planarToChunchy<unsigned short>(unsigned char*, char const*, int, int, int)--(anonymous namespace)::LoadPSD(QDataStream&, (anonymous"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 544,
    "type": "QIODevice*"
   },
   "entity_name_cpg": "device",
   "func_lines": [
    544,
    561
   ],
   "func_params": {
    "names": [
     "device",
     "format"
    ],
    "types": [
     "QIODevice*",
     "QByteArray&"
    ]
   },
   "guards": [
    {
     "code": "format == \"ani\"",
     "line": 546
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "device->isReadable() && ANIHandler::canRead(device)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "device->isReadable()",
     "name": "isReadable",
     "nargs": 1
    },
    {
     "code": "ANIHandler::canRead(device)",
     "name": "canRead",
     "nargs": 1
    }
   ],
   "line_ids": [
    "device"
   ],
   "osv_id": "ARVO-42510459",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "void (anonymous namespace)::planarToChunchy<unsigned short>(unsigned char*, char const*, int, int, int)"
  }
 },
 {
  "osv_id": "ARVO-42510485",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "content",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1362,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x240b2)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(blosc2_metalayer) ;; 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc(sizeof(blosc2_metalayer), 1)",
    "fn": "get_meta_from_header",
    "kind": "calloc",
    "line": 1304,
    "origin": "cpg",
    "args": "sizeof(blosc2_metalayer) ;; 1"
   },
   {
    "code": "malloc((size_t)nslen + 1)",
    "fn": "get_meta_from_header",
    "kind": "malloc",
    "line": 1314,
    "origin": "cpg",
    "args": "(size_t)nslen + 1"
   },
   {
    "code": "malloc((size_t)content_len)",
    "fn": "get_meta_from_header",
    "kind": "malloc",
    "line": 1362,
    "origin": "cpg",
    "args": "(size_t)content_len"
   },
   {
    "kind": "unknown",
    "line": 1363,
    "fn": "get_meta_from_header",
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_meta_from_header",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1363
   },
   "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
   "access": {
    "dir": "READ",
    "width": 2147483647,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_meta_from_header",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "content_len < 0",
   "guard_count": 1,
   "control_structures": "IF:1268,IF:1276,IF:1279,IF:1285,IF:1290,FOR:1296,IF:1298,IF:1301,IF:1311,IF:1323,IF:1326,IF:1332"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "header",
   "header_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/5f5213c23cc8608537b234e93ee5dae31a77aaff/ARVO-42510485/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5f5213c23cc8.cpg",
   "testcase_size": 100
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
   "dedup_token": "__asan_memcpy--get_meta_from_header--frame_get_metalayers"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* content = malloc((size_t)content_len)",
     "line": 1362
    }
   ],
   "entity_decl": {
    "line": 1362,
    "type": "char*"
   },
   "entity_name_cpg": "content",
   "func_lines": [
    1260,
    1368
   ],
   "func_params": {
    "names": [
     "frame",
     "schunk",
     "header",
     "header_len"
    ],
    "types": [
     "blosc2_frame_s*",
     "blosc2_schunk*",
     "uint8_t*",
     "int32_t"
    ]
   },
   "guards": [
    {
     "code": "header_len < header_pos",
     "line": 1268
    },
    {
     "code": "header_len < header_pos",
     "line": 1276
    },
    {
     "code": "metalayers_idx[0] != 0xde",
     "line": 1279
    },
    {
     "code": "header_len < header_pos",
     "line": 1285
    },
    {
     "code": "nmetalayers > BLOSC2_MAX_METALAYERS",
     "line": 1290
    },
    {
     "code": "nmetalayer < nmetalayers",
     "line": 1296
    },
    {
     "code": "header_len < header_pos",
     "line": 1298
    },
    {
     "code": "(*idxp & 0xe0u) != 0xa0u",
     "line": 1301
    },
    {
     "code": "header_len < header_pos",
     "line": 1311
    },
    {
     "code": "header_len < header_pos",
     "line": 1323
    },
    {
     "code": "(*idxp & 0xffu) != 0xd2u",
     "line": 1326
    },
    {
     "code": "header_len < header_pos",
     "line": 1332
    },
    {
     "code": "offset < 0",
     "line": 1337
    },
    {
     "code": "header_len < offset + 1 + 4",
     "line": 1343
    },
    {
     "code": "*content_marker != 0xc6",
     "line": 1346
    },
    {
     "code": "content_len < 0",
     "line": 1353
    },
    {
     "code": "header_len < offset + 1 + 4 + content_len",
     "line": 1359
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "content_marker + 1 + 4",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "content_marker + 1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(size_t)content_len",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "content",
    "content_marker",
    "content_len"
   ],
   "osv_id": "ARVO-42510485",
   "sites": [
    {
     "args": "sizeof(blosc2_metalayer) ;; 1",
     "callee": "calloc",
     "code": "calloc(sizeof(blosc2_metalayer), 1)",
     "line": 1304
    },
    {
     "args": "(size_t)nslen + 1",
     "callee": "malloc",
     "code": "malloc((size_t)nslen + 1)",
     "line": 1314
    },
    {
     "args": "(size_t)content_len",
     "callee": "malloc",
     "code": "malloc((size_t)content_len)",
     "line": 1362
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "get_meta_from_header"
  }
 },
 {
  "osv_id": "ARVO-42510527",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet_payload",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tinc.c",
    "line": 32,
    "size": null,
    "type": "u_int8_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 105,
    "fn": "ndpi_check_tinc",
    "code": "(packet_payload[i] >= '0' && packet_payload[i] <= '9') | | packet_payload[i] >= '0' && packet_payload[i] <= '9' | packet_payload[i] >= '0' | packet_payload[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_tinc",
    "file": "/src/ndpi/src/lib/protocols/tinc.c",
    "line": 105
   },
   "code": "(packet_payload[i] >= '0' && packet_payload[i] <= '9') | | packet_payload[i] >= '0' && packet_payload[i] <= '9' | packet_payload[i] >= '0' | packet_payload[i]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_tinc",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < payload_len",
   "guard_count": 1,
   "control_structures": "IF:35,IF:36,IF:49,ELSE:64,IF:64,IF:65,IF:66,SWITCH:74,IF:77,WHILE:79,IF:80,BREAK:85"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/a6029d250d9c5dd0d7346fe47de838c243c20cac/ARVO-42510527/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_a6029d250d9c.cpg",
   "testcase_size": 230
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
   "dedup_token": "ndpi_check_tinc--ndpi_search_tinc--check_ndpi_detection_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet_payload = packet->payload",
     "line": 32
    }
   ],
   "entity_decl": {
    "line": 32,
    "type": "u_int8_t*"
   },
   "entity_name_cpg": "packet_payload",
   "func_lines": [
    29,
    129
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
     "code": "packet->udp != NULL",
     "line": 35
    },
    {
     "code": "ndpi_struct->tinc_cache != NULL",
     "line": 36
    },
    {
     "code": "cache_remove(ndpi_struct->tinc_cache, &tinc_cache_entry1, sizeof(tinc_cache_entry1)) == CACHE_NO_ERROR",
     "line": 49
    },
    {
     "code": "cache_remove(ndpi_struct->tinc_cache, &tinc_cache_entry2, sizeof(tinc_cache_entry2)) == CACHE_NO_ERROR",
     "line": 50
    },
    {
     "code": "packet->tcp != NULL",
     "line": 64
    },
    {
     "code": "payload_len == 0",
     "line": 65
    },
    {
     "code": "packet->tcp->syn == 1",
     "line": 66
    },
    {
     "code": "packet->tcp->ack == 0",
     "line": 66
    },
    {
     "code": "payload_len > 6",
     "line": 77
    },
    {
     "code": "memcmp(packet_payload, \"0 \", 2) == 0",
     "line": 77
    },
    {
     "code": "packet_payload[2] != ' '",
     "line": 77
    },
    {
     "code": "i < payload_len",
     "line": 79
    },
    {
     "code": "packet_payload[i++] != ' '",
     "line": 79
    },
    {
     "code": "i+3 == payload_len",
     "line": 80
    },
    {
     "code": "memcmp((packet_payload+i), \"17\\n\", 3) == 0",
     "line": 80
    },
    {
     "code": "payload_len > 11",
     "line": 89
    },
    {
     "code": "memcmp(packet_payload, \"1 \", 2) == 0",
     "line": 89
    },
    {
     "code": "packet_payload[2] != ' '",
     "line": 89
    },
    {
     "code": "packet_payload[i++] == ' '",
     "line": 97
    },
    {
     "code": "packet_payload[i] == '\\n'",
     "line": 110
    },
    {
     "code": "++flow->tinc_state > 3",
     "line": 111
    },
    {
     "code": "ndpi_struct->tinc_cache == NULL",
     "line": 112
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "(packet_payload[i] >= '0' && packet_payload[i] <= '9') ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "packet_payload[i] >= '0' && packet_payload[i] <= '9'",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "packet_payload[i] >= '0'",
     "name": "<operator>.greaterEqualsThan",
     "nargs": 2
    },
    {
     "code": "packet_payload[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet_payload[i] <= '9'",
     "name": "<operator>.lessEqualsThan",
     "nargs": 2
    },
    {
     "code": "packet_payload[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet_payload",
    "i"
   ],
   "osv_id": "ARVO-42510527",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_check_tinc"
  }
 },
 {
  "osv_id": "ARVO-42510536",
  "project": "lwan",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "error",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lwan/src/lib/lwan-h2-huffman.c",
    "line": 40,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x240b2)",
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
    "line": 43,
    "fn": "read64be",
    "code": "printf(\"Error: %s\\n\", error)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read64be",
    "file": "/src/lwan/src/lib/lwan-h2-huffman.c",
    "line": 43
   },
   "code": "printf(\"Error: %s\\n\", error)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dump",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:14,WHILE:17,SWITCH:18,DO:20,DO:21,DO:22,DO:23,BREAK:24,IF:27,IF:33,BREAK:36,IF:42"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "config"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lwan/address/0e9355a0aac992fe321abcc5b547602306fe4343/ARVO-42510536/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_0e9355a0aac9.cpg",
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
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "read64be--peek_byte--lwan_h2_huffman_decode_for_fuzzing"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*error = config_last_error(config)",
     "line": 40
    }
   ],
   "entity_decl": {
    "line": 40,
    "type": "char*"
   },
   "entity_name_cpg": "error",
   "func_lines": [
    10,
    48
   ],
   "func_params": {
    "names": [
     "config",
     "indent_level"
    ],
    "types": [
     "config*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "indent_level > 64",
     "line": 14
    },
    {
     "code": "indent_level == 0",
     "line": 27
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "printf(\"Error: %s\\n\", error)",
     "name": "printf",
     "nargs": 2
    }
   ],
   "line_ids": [
    "error"
   ],
   "osv_id": "ARVO-42510536",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "read64be"
  }
 },
 {
  "osv_id": "ARVO-42510699",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "path",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "line": 576,
    "size": null,
    "type": "sc_path"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "sc_file_new",
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 619
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 628,
    "fn": "sc_pkcs15init_delete_by_path",
    "code": "path.value[0] = file_path->value[file_path->len - 2] | path.value[0] | path.value | file_path->value[file_path->len - 2]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15init_delete_by_path",
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "line": 628
   },
   "code": "path.value[0] = file_path->value[file_path->len - 2] | path.value[0] | path.value | file_path->value[file_path->len - 2]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_pkcs15init_delete_by_path",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:580,DO:593,IF:593,IF:595,ELSE:600,IF:600,ELSE:605,IF:608,DO:612,IF:612,DO:616,IF:616"
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
   "file_path"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42510699/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 130885
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
   "dedup_token": "sc_pkcs15init_delete_by_path--sc_pkcs15init_store_data--sc_pkcs15init_store_data_object"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "path = *file_path",
     "line": 591
    },
    {
     "code": "path = *file_path",
     "line": 622
    },
    {
     "code": "path.type = SC_PATH_TYPE_FILE_ID",
     "line": 627
    },
    {
     "code": "path.value[0] = file_path->value[file_path->len - 2]",
     "line": 628
    },
    {
     "code": "path.value[1] = file_path->value[file_path->len - 1]",
     "line": 629
    },
    {
     "code": "path.len = 2",
     "line": 630
    }
   ],
   "entity_decl": {
    "line": 576,
    "type": "sc_path"
   },
   "entity_name_cpg": "path",
   "func_lines": [
    570,
    643
   ],
   "func_params": {
    "names": [
     "profile",
     "p15card",
     "file_path"
    ],
    "types": [
     "sc_profile*",
     "sc_pkcs15_card*",
     "sc_path*"
    ]
   },
   "guards": [
    {
     "code": "_ret < 0",
     "line": 593
    },
    {
     "code": "_ret < 0",
     "line": 612
    },
    {
     "code": "_ret < 0",
     "line": 616
    },
    {
     "code": "_ret < 0",
     "line": 619
    },
    {
     "code": "_ret < 0",
     "line": 624
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "path.value[0] = file_path->value[file_path->len - 2]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "path.value[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "path.value",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "file_path->value[file_path->len - 2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "file_path->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "file_path->len - 2",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "file_path->len",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "path",
    "file_path"
   ],
   "osv_id": "ARVO-42510699",
   "sites": [
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 598
    },
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 603
    },
    {
     "args": "parent",
     "callee": "sc_file_free",
     "code": "sc_file_free(parent)",
     "line": 615
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_pkcs15init_delete_by_path"
  }
 },
 {
  "osv_id": "ARVO-42510718",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dst",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 203,
    "size": null,
    "type": "char*const"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x240b2)",
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
    "line": 208,
    "fn": "strncpy_lower",
    "code": "strncpy(dst, src, dst_len)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "strncpy_lower",
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 208
   },
   "code": "strncpy(dst, src, dst_len)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "strncpy_lower",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < dst_len",
   "guard_count": 1,
   "control_structures": "FOR:211"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*const",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "dst",
   "dst_siz",
   "src",
   "src_siz"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/06a0abb6fdf8fb7a446ef5aafdf2c7d24608977f/ARVO-42510718/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_06a0abb6fdf8.cpg",
   "testcase_size": 158
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
   "dedup_token": "__interceptor_strncpy--strncpy_lower--krb_parse"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "dst[dst_len] = '\\0'",
     "line": 209
    },
    {
     "code": "dst[i] = tolower(dst[i])",
     "line": 213
    }
   ],
   "entity_decl": {
    "line": 203,
    "type": "char*const"
   },
   "entity_name_cpg": "dst",
   "func_lines": [
    203,
    215
   ],
   "func_params": {
    "names": [
     "dst",
     "dst_siz",
     "src",
     "src_siz"
    ],
    "types": [
     "char*const",
     "size_t",
     "char*const",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "i < dst_len",
     "line": 211
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "strncpy(dst, src, dst_len)",
     "name": "strncpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "dst",
    "src",
    "dst_len"
   ],
   "osv_id": "ARVO-42510718",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "strncpy_lower"
  }
 },
 {
  "osv_id": "ARVO-42511065",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "tbl",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/decode.c",
    "line": 273,
    "size": null,
    "type": "Dwg_Section*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "decode_preR13",
    "file": "/src/libredwg/src/decode.c",
    "line": 728
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 274,
    "fn": "decode_preR13_section_hdr",
    "code": "tbl->size = bit_read_RS (dat) | tbl->size | bit_read_RS (dat)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "decode_preR13_section_hdr",
    "file": "/src/libredwg/src/decode.c",
    "line": 274
   },
   "code": "tbl->size = bit_read_RS (dat) | tbl->size | bit_read_RS (dat)",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "decode_preR13_section_hdr",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:280,IF:284,IF:286,IF:286"
  },
  "call_chain": [],
  "types": {
   "entity_type": "Dwg_Section*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "id",
   "dat"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/fc96e7e65dd763ed20eae58ead3f0a1f686bb51f/ARVO-42511065/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_fc96e7e65dd7.cpg",
   "testcase_size": 58
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
   "dedup_token": "decode_preR13_section_hdr--decode_preR13--dwg_decode"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*tbl = &dwg->header.section[id]",
     "line": 273
    },
    {
     "code": "tbl->size = bit_read_RS (dat)",
     "line": 274
    },
    {
     "code": "tbl->number = bit_read_RS (dat)",
     "line": 275
    },
    {
     "code": "tbl->flags = bit_read_RS (dat)",
     "line": 276
    },
    {
     "code": "tbl->address = bit_read_RL (dat)",
     "line": 277
    },
    {
     "code": "tbl->name[63] = '\\0'",
     "line": 279
    }
   ],
   "entity_decl": {
    "line": 273,
    "type": "Dwg_Section*"
   },
   "entity_name_cpg": "tbl",
   "func_lines": [
    269,
    290
   ],
   "func_params": {
    "names": [
     "name",
     "id",
     "dat",
     "dwg"
    ],
    "types": [
     "char*restrict",
     "Dwg_Section_Type_r11",
     "Bit_Chain*restrict",
     "Dwg_Data*restrict"
    ]
   },
   "guards": [
    {
     "code": "tbl->address + (tbl->number * tbl->size) > dat->size",
     "line": 284
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "tbl->size = bit_read_RS (dat)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "tbl->size",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "bit_read_RS (dat)",
     "name": "bit_read_RS",
     "nargs": 1
    }
   ],
   "line_ids": [
    "tbl",
    "dat"
   ],
   "osv_id": "ARVO-42511065",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "decode_preR13_section_hdr"
  }
 },
 {
  "osv_id": "ARVO-42511372",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "_obj",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/common_entity_handle_data.spec",
    "line": 1114,
    "size": null,
    "type": "Dwg_Object_Entity*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "dwg_setup_LAYOUT",
    "file": "/src/libredwg/src/./dwg.spec",
    "line": 4677
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 73,
    "fn": "json_common_entity_data",
    "code": "_obj->next_entity | !(dat->opts & 0x20) | dat->opts & 0x20 | dat->opts",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "json_common_entity_data",
    "file": "/src/libredwg/src/common_entity_handle_data.spec",
    "line": 73
   },
   "code": "_obj->next_entity | !(dat->opts & 0x20) | dat->opts & 0x20 | dat->opts",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_common_entity_data",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:9,IF:11,IF:11,ELSE:11,ELSE:11,IF:11,ELSE:11,IF:37,IF:37,ELSE:37,FOR:37,IF:37"
  },
  "call_chain": [],
  "types": {
   "entity_type": "Dwg_Object_Entity*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dat"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/a7c2bd168507d426036003f26cad7e603c7a1045/ARVO-42511372/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_a7c2bd168507.cpg",
   "testcase_size": 2048
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
   "dedup_token": "json_common_entity_data--dwg_json_REPEAT--dwg_json_object"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "_obj = ent",
     "line": 1119
    }
   ],
   "entity_decl": {
    "line": 1114,
    "type": "Dwg_Object_Entity*"
   },
   "entity_name_cpg": "_obj",
   "func_lines": [
    1110,
    1129
   ],
   "func_params": {
    "names": [
     "dat",
     "obj"
    ],
    "types": [
     "Bit_Chain*restrict",
     "Dwg_Object*restrict"
    ]
   },
   "guards": [
    {
     "code": "FIELD_VALUE (entmode) == 0",
     "line": 9
    },
    {
     "code": "vcount < ent->num_reactors",
     "line": 37
    },
    {
     "code": "dat->version < R_2004",
     "line": 38
    },
    {
     "code": "ent->is_xdic_missing != 0",
     "line": 38
    },
    {
     "code": "ent->xdicobjhandle != NULL",
     "line": 38
    },
    {
     "code": "ent->xdicobjhandle->handleref.value != 0",
     "line": 38
    },
    {
     "code": "FIELD_VALUE (ltype_flags) == 3",
     "line": 89
    },
    {
     "code": "FIELD_VALUE (material_flags) == 3",
     "line": 105
    },
    {
     "code": "FIELD_VALUE (shadow_flags) == 3",
     "line": 107
    },
    {
     "code": "FIELD_VALUE (plotstyle_flags) == 3",
     "line": 113
    },
    {
     "code": "ent->preview_size < 210210",
     "line": 30
    },
    {
     "code": "_j < (long)ent->preview_size",
     "line": 32
    },
    {
     "code": "dat->version < R_2004",
     "line": 86
    },
    {
     "code": "ent->color.index != 256",
     "line": 172
    },
    {
     "code": "_buf[k - 1] == '0'",
     "line": 180
    },
    {
     "code": "k > 1",
     "line": 180
    },
    {
     "code": "_buf[k - 1] != '.'",
     "line": 180
    },
    {
     "code": "_buf[k] == '0'",
     "line": 180
    }
   ],
   "line_call_count": 36,
   "line_calls": [
    {
     "code": "_obj->next_entity",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "!(dat->opts & 0x20)",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "dat->opts & 0x20",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "dat->opts",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "fprintf(dat->fh, \",\\n\")",
     "name": "fprintf",
     "nargs": 2
    },
    {
     "code": "dat->fh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dat->opts &= ~0x20",
     "name": "<operators>.assignmentAnd",
     "nargs": 2
    },
    {
     "code": "dat->opts",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "~0x20",
     "name": "<operator>.not",
     "nargs": 1
    },
    {
     "code": "_prefix(dat)",
     "name": "_prefix",
     "nargs": 1
    },
    {
     "code": "fprintf(dat->fh, \"\\\"%s\\\": [%u, %u, %lu, %lu]\", _path_field(\"next_entity\"), _obj->next_entity->handleref.code, _obj->next_entity->handleref.size, _obj->next_entity->handleref.value, _obj->next_entity->",
     "name": "fprintf",
     "nargs": 7
    },
    {
     "code": "dat->fh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_path_field(\"next_entity\")",
     "name": "_path_field",
     "nargs": 1
    },
    {
     "code": "_obj->next_entity->handleref.code",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity->handleref",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity->handleref.size",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity->handleref",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity->handleref.value",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity->handleref",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity->absolute_ref",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_obj->next_entity",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "!(dat->opts & 0x20)",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "dat->opts & 0x20",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "dat->opts",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "fprintf(dat->fh, \",\\n\")",
     "name": "fprintf",
     "nargs": 2
    },
    {
     "code": "dat->fh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dat->opts &= ~0x20",
     "name": "<operators>.assignmentAnd",
     "nargs": 2
    },
    {
     "code": "dat->opts",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "~0x20",
     "name": "<operator>.not",
     "nargs": 1
    },
    {
     "code": "_prefix(dat)",
     "name": "_prefix",
     "nargs": 1
    },
    {
     "code": "fprintf(dat->fh, \"\\\"%s\\\": [0, 0]\", _path_field(\"next_entity\"))",
     "name": "fprintf",
     "nargs": 3
    },
    {
     "code": "dat->fh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "_path_field(\"next_entity\")",
     "name": "_path_field",
     "nargs": 1
    }
   ],
   "line_ids": [
    "_obj",
    "dat"
   ],
   "osv_id": "ARVO-42511372",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "char []",
     "line": 180
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "json_common_entity_data"
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