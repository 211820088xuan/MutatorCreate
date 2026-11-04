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
  "osv_id": "ARVO-42517623",
  "project": "kimageformats",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "x",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/kimageformats/src/imageformats/raw.cpp",
    "line": 608,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "api": "calloc",
   "site": {
    "fn": "libraw_memmgr::calloc(unsigned long, unsigned long)",
    "file": "/src/LibRaw/./libraw/libraw_alloc.h",
    "line": 56
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
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
    "dir": "READ",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kimageformats/address/d881a7bbb1562af383bbb6ca20340ad739fb0d13/ARVO-42517623/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_d881a7bbb156.cpg",
   "testcase_size": 6471
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
   "dedup_token": "LibRaw::phase_one_correct()--LibRaw::raw2image_ex(int)--LibRaw::dcraw_process()"
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
   "osv_id": "ARVO-42517623",
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
  "osv_id": "ARVO-42517712",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 438,
    "size": null,
    "type": "uint8_t*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 169
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 443,
    "origin": "cpg",
    "args": "cell_size"
   },
   {
    "kind": "unknown",
    "line": 463,
    "fn": "ndlz8_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   },
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 475,
    "origin": "cpg",
    "args": "cell_size"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz8_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 463
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 3959948288,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz8_decompress",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:445,IF:452,FOR:466,FOR:476,FOR:477,IF:478,IF:482,ELSE:484,IF:487,ELSE:489,IF:494,ELSE:497"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42517712/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memset--ndlz8_decompress--ndlz_decompress"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* op = (uint8_t*)output",
     "line": 438
    }
   ],
   "entity_decl": {
    "line": 438,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "op",
   "func_lines": [
    431,
    569
   ],
   "func_params": {
    "names": [
     "input",
     "input_len",
     "output",
     "output_len",
     "meta",
     "dparams"
    ],
    "types": [
     "uint8_t*",
     "int32_t",
     "uint8_t*",
     "int32_t",
     "uint8_t",
     "blosc2_dparams*"
    ]
   },
   "guards": [
    {
     "code": "ndim != 2",
     "line": 452
    },
    {
     "code": "i < 2",
     "line": 466
    },
    {
     "code": "ii[0] < i_stop[0]",
     "line": 476
    },
    {
     "code": "ii[1] < i_stop[1]",
     "line": 477
    },
    {
     "code": "ip > ip_limit",
     "line": 478
    },
    {
     "code": "ii[0] == i_stop[0] - 1",
     "line": 482
    },
    {
     "code": "blockshape[0] % cell_shape == 0",
     "line": 483
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 487
    },
    {
     "code": "blockshape[1] % cell_shape == 0",
     "line": 488
    },
    {
     "code": "token == 0",
     "line": 494
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 497
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 501
    },
    {
     "code": "match_type == 21",
     "line": 505
    },
    {
     "code": "l < 3",
     "line": 510
    },
    {
     "code": "l < cell_shape",
     "line": 514
    },
    {
     "code": "l < row",
     "line": 515
    },
    {
     "code": "l > row + 2",
     "line": 515
    },
    {
     "code": "match_type == 17",
     "line": 520
    },
    {
     "code": "l < 2",
     "line": 525
    },
    {
     "code": "l < cell_shape",
     "line": 529
    },
    {
     "code": "l < row",
     "line": 530
    },
    {
     "code": "l > row + 1",
     "line": 530
    },
    {
     "code": "i < cell_shape",
     "line": 541
    },
    {
     "code": "i < padding[0]",
     "line": 542
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 548
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 559
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 563
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memset(op, 0, blockshape[0] * blockshape[1])",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "blockshape[0] * blockshape[1]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "blockshape[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "blockshape[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "op",
    "blockshape"
   ],
   "osv_id": "ARVO-42517712",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "blockshape[2]",
     "line": 440
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "eshape[2]",
     "line": 441
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 443
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 465
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 472
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 473
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 475
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 556
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 557
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz8_decompress"
  }
 },
 {
  "osv_id": "ARVO-42517725",
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
    "width": 8,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42517725/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_dbe29a1a77b5.cpg",
   "testcase_size": 386
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
   "osv_id": "ARVO-42517725",
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
  "osv_id": "ARVO-42517782",
  "project": "mongoose",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "n",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 652,
    "type": "size_t",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/mongoose/test/fuzz.c",
    "line": 70
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "40",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 720,
    "fn": "rx_ip(mip_if*, pkt*)",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "rx_ip(mip_if*, pkt*)",
    "file": "/src/mongoose/mip/mip.c",
    "line": 720
   },
   "code": "n += scpy(out, param, (char *) &hex[p[j] & 15], 1)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rx_ip(mip_if*, pkt*)",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mongoose/address/1f85fcc9b040635483b775fae4ae74a5c945e60a/ARVO-42517782/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mongoose_1f85fcc9b040.cpg",
   "testcase_size": 34
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "rx_ip(mip_if*, pkt*)--mip_rx(mip_if*, void*, unsigned long)--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "n = 0",
     "line": 652
    }
   ],
   "entity_decl": {
    "line": 652,
    "type": "size_t"
   },
   "entity_name_cpg": "n",
   "func_lines": [
    650,
    753
   ],
   "func_params": {
    "names": [
     "out",
     "param",
     "fmt",
     "ap"
    ],
    "types": [
     "void",
     "void*",
     "char*",
     "va_list*"
    ]
   },
   "guards": [
    {
     "code": "fmt[i] != '\\0'",
     "line": 653
    },
    {
     "code": "fmt[i] == '%'",
     "line": 654
    },
    {
     "code": "c == '#'",
     "line": 657
    },
    {
     "code": "c == '-'",
     "line": 658
    },
    {
     "code": "c == '0'",
     "line": 659
    },
    {
     "code": "c == '.'",
     "line": 661
    },
    {
     "code": "c == '*'",
     "line": 663
    },
    {
     "code": "c == 'h'",
     "line": 671
    },
    {
     "code": "c == 'l'",
     "line": 672
    },
    {
     "code": "c == 'l'",
     "line": 674
    },
    {
     "code": "c == 'p'",
     "line": 676
    },
    {
     "code": "c == 'd'",
     "line": 677
    },
    {
     "code": "c == 'u'",
     "line": 677
    },
    {
     "code": "c == 'x'",
     "line": 677
    },
    {
     "code": "c == 'X'",
     "line": 677
    },
    {
     "code": "c == 'p'",
     "line": 677
    },
    {
     "code": "c == 'g'",
     "line": 678
    },
    {
     "code": "c == 'f'",
     "line": 678
    },
    {
     "code": "c == 'd'",
     "line": 679
    },
    {
     "code": "c == 'x'",
     "line": 679
    },
    {
     "code": "c == 'X'",
     "line": 679
    },
    {
     "code": "c == 'p'",
     "line": 679
    },
    {
     "code": "c == 'g'",
     "line": 682
    },
    {
     "code": "c == 'f'",
     "line": 682
    },
    {
     "code": "pr == ~0U",
     "line": 684
    },
    {
     "code": "is_long == 2",
     "line": 686
    },
    {
     "code": "is_long == 1",
     "line": 689
    },
    {
     "code": "j < xl",
     "line": 696
    },
    {
     "code": "w > 0",
     "line": 696
    },
    {
     "code": "pad == ' '",
     "line": 697
    },
    {
     "code": "k < w",
     "line": 697
    },
    {
     "code": "j + k < w",
     "line": 697
    },
    {
     "code": "pad == '0'",
     "line": 700
    },
    {
     "code": "k < w",
     "line": 700
    },
    {
     "code": "j + k < w",
     "line": 700
    },
    {
     "code": "pad == ' '",
     "line": 703
    },
    {
     "code": "k < w",
     "line": 703
    },
    {
     "code": "j + k < w",
     "line": 703
    },
    {
     "code": "c == 'M'",
     "line": 705
    },
    {
     "code": "c == 'c'",
     "line": 708
    },
    {
     "code": "c == 'H'",
     "line": 712
    },
    {
     "code": "j < bl",
     "line": 718
    },
    {
     "code": "c == 'V'",
     "line": 723
    },
    {
     "code": "c == 's'",
     "line": 728
    },
    {
     "code": "c == 'Q'",
     "line": 728
    },
    {
     "code": "c == 'q'",
     "line": 728
    },
    {
     "code": "c == 'Q'",
     "line": 731
    },
    {
     "code": "c == 'q'",
     "line": 732
    },
    {
     "code": "pr == ~0U",
     "line": 733
    },
    {
     "code": "p == NULL",
     "line": 733
    },
    {
     "code": "pr < w",
     "line": 734
    },
    {
     "code": "j + pr < w",
     "line": 734
    },
    {
     "code": "pr < w",
     "line": 737
    },
    {
     "code": "j + pr < w",
     "line": 737
    },
    {
     "code": "c == '%'",
     "line": 739
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "n += scpy(out, param, (char *) &hex[p[j] & 15], 1)",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "scpy(out, param, (char *) &hex[p[j] & 15], 1)",
     "name": "scpy",
     "nargs": 4
    },
    {
     "code": "(char *) &hex[p[j] & 15]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "&hex[p[j] & 15]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "hex[p[j] & 15]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "p[j] & 15",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "p[j]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "n",
    "out",
    "param",
    "hex",
    "p",
    "j"
   ],
   "osv_id": "ARVO-42517782",
   "sites": [
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "tmp[40]",
     "line": 680
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "rx_ip(mip_if*, pkt*)"
  }
 },
 {
  "osv_id": "ARVO-42517792",
  "project": "mongoose",
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
    "line": 177,
    "fn": "mg_mqtt_parse",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mg_mqtt_parse",
    "file": "/src/mongoose/src/mqtt.c",
    "line": 177
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mg_mqtt_parse",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mongoose/address/1f85fcc9b040635483b775fae4ae74a5c945e60a/ARVO-42517792/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mongoose_1f85fcc9b040.cpg",
   "testcase_size": 4
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "mg_mqtt_parse--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    3146,
    3209
   ],
   "func_params": {
    "names": [
     "buf",
     "len",
     "version",
     "m"
    ],
    "types": [
     "uint8_t*",
     "size_t",
     "uint8_t",
     "mg_mqtt_message*"
    ]
   },
   "guards": [
    {
     "code": "len < 2",
     "line": 3153
    },
    {
     "code": "(size_t) (p - buf) < len",
     "line": 3159
    },
    {
     "code": "end > buf + len",
     "line": 3167
    },
    {
     "code": "end - p < 2",
     "line": 3172
    },
    {
     "code": "p + 2 > end",
     "line": 3183
    },
    {
     "code": "p + 2 > end",
     "line": 3188
    },
    {
     "code": "p > end",
     "line": 3192
    },
    {
     "code": "m->qos > 0",
     "line": 3193
    },
    {
     "code": "p + 2 > end",
     "line": 3194
    },
    {
     "code": "p > end",
     "line": 3198
    },
    {
     "code": "version == 5",
     "line": 3199
    },
    {
     "code": "p > end",
     "line": 3200
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42517792",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mg_mqtt_parse"
  }
 },
 {
  "osv_id": "ARVO-42518409",
  "project": "libarchive",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "a",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read.c",
    "line": 804,
    "size": null,
    "type": "archive_read*"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "archive_read_new",
    "file": "/src/libarchive/libarchive/archive_read.c",
    "line": 96
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 805,
    "fn": "archive_read_format_capabilities",
    "code": "a && a->format && a->format->format_capabilties | a && a->format | a->format | a->format->format_capabilties",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "archive_read_format_capabilities",
    "file": "/src/libarchive/libarchive/archive_read.c",
    "line": 805
   },
   "code": "a && a->format && a->format->format_capabilties | a && a->format | a->format | a->format->format_capabilties",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "archive_read_format_capabilities",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:805"
  },
  "call_chain": [],
  "types": {
   "entity_type": "archive_read*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "_a"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/fa4b613f2e2510bd036f2eeed2fece97cd18b079/ARVO-42518409/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_fa4b613f2e25.cpg",
   "testcase_size": 800
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
   "dedup_token": "archive_read_format_capabilities--archive_read_has_encrypted_entries--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*a = (struct archive_read *)_a",
     "line": 804
    }
   ],
   "entity_decl": {
    "line": 804,
    "type": "archive_read*"
   },
   "entity_name_cpg": "a",
   "func_lines": [
    801,
    809
   ],
   "func_params": {
    "names": [
     "_a"
    ],
    "types": [
     "archive*"
    ]
   },
   "guards": [],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "a && a->format && a->format->format_capabilties",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "a && a->format",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "a->format",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->format->format_capabilties",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->format",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "a"
   ],
   "osv_id": "ARVO-42518409",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "archive_read_format_capabilities"
  }
 },
 {
  "osv_id": "ARVO-42518543",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "hb_realloc_impl",
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "line": 55
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 778,
    "fn": "check_glyph_property",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "check_glyph_property",
    "file": "/src/harfbuzz/src/hb-ot-layout-gsubgpos.hh",
    "line": 778
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "check_glyph_property",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/3b43096ef336cf3ba149518c82541c0079ef0f92/ARVO-42518543/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_3b43096ef336.cpg",
   "testcase_size": 285
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
   "shadow_legend_size": 0,
   "dedup_token": "check_glyph_property--may_skip--OT::hb_ot_apply_context_t::skipping_iterator_t::next(unsigned int*)"
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
     "p2",
     "p3"
    ],
    "types": [
     "ANY",
     "ANY",
     "ANY"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42518543",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "check_glyph_property"
  }
 },
 {
  "osv_id": "ARVO-42519041",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "byte",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 151,
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
    "line": 154,
    "fn": "bit_read_B",
    "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_read_B",
    "file": "/src/libredwg/src/bits.c",
    "line": 154
   },
   "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_read_B",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:153,IF:153,IF:153"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dat"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/45e5371477dc4a07809d97e109a62f3f84d8672e/ARVO-42519041/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_45e5371477dc.cpg",
   "testcase_size": 1014
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
   "dedup_token": "bit_read_B--dwg_decode_header_variables--decode_R13_R2000"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "byte = dat->chain[dat->byte]",
     "line": 154
    }
   ],
   "entity_decl": {
    "line": 151,
    "type": "unsigned char"
   },
   "entity_name_cpg": "byte",
   "func_lines": [
    147,
    159
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
     "code": "(dat->byte * 8) + dat->bit > dat->size * 8",
     "line": 153
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "byte = dat->chain[dat->byte]",
     "name": "<operator>.assignment",
     "nargs": 2
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
    "byte",
    "dat"
   ],
   "osv_id": "ARVO-42519041",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_read_B"
  }
 },
 {
  "osv_id": "ARVO-42519042",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "byte",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 183,
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
    "line": 186,
    "fn": "bit_read_BB",
    "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_read_BB",
    "file": "/src/libredwg/src/bits.c",
    "line": 186
   },
   "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_read_BB",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:185,IF:185,IF:185,IF:187,ELSE:190,IF:192"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dat"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/45e5371477dc4a07809d97e109a62f3f84d8672e/ARVO-42519042/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_45e5371477dc.cpg",
   "testcase_size": 205
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
   "dedup_token": "bit_read_BB--bit_read_BD--dwg_decode_header_variables"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "byte = dat->chain[dat->byte]",
     "line": 186
    },
    {
     "code": "byte = dat->chain[dat->byte + 1]",
     "line": 194
    }
   ],
   "entity_decl": {
    "line": 183,
    "type": "unsigned char"
   },
   "entity_name_cpg": "byte",
   "func_lines": [
    179,
    201
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
     "code": "(dat->byte * 8) + dat->bit > dat->size * 8",
     "line": 185
    },
    {
     "code": "dat->bit < 7",
     "line": 187
    },
    {
     "code": "dat->byte < dat->size - 1",
     "line": 192
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "byte = dat->chain[dat->byte]",
     "name": "<operator>.assignment",
     "nargs": 2
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
    "byte",
    "dat"
   ],
   "osv_id": "ARVO-42519042",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_read_BB"
  }
 },
 {
  "osv_id": "ARVO-42519068",
  "project": "assimp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pcIn",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/assimp/code/AssetLib/Obj/ObjFileImporter.cpp",
    "line": 411,
    "size": null,
    "type": "D3DS.Node*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)",
    "file": "/src/assimp/code/AssetLib/Obj/ObjFileImporter.cpp",
    "line": 421
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "12",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 502,
    "fn": "Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)",
    "code": "aiMatrix4x4::RotationZ(AI_DEG_TO_RAD(-pcIn->aCameraRollK | AI_DEG_TO_RAD(-pcIn->aCameraRollKeys[0].mValue) | -pcIn->aCameraRollKeys[0].mValue | pcIn->aCameraRollKeys[0].mValue",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)",
    "file": "/src/assimp/code/AssetLib/Obj/ObjFileImporter.cpp",
    "line": 502
   },
   "code": "aiMatrix4x4::RotationZ(AI_DEG_TO_RAD(-pcIn->aCameraRollK | AI_DEG_TO_RAD(-pcIn->aCameraRollKeys[0].mValue) | -pcIn->aCameraRollKeys[0].mValue | pcIn->aCameraRollKeys[0].mValue",
   "access": {
    "dir": "WRITE",
    "width": 12,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "AddNodeToGraph",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:418,IF:422,IF:425,FOR:439,IF:443,FOR:449,IF:455,FOR:457,IF:465,FOR:466,ELSE:473,IF:482"
  },
  "call_chain": [],
  "types": {
   "entity_type": "D3DS.Node*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "pcOut",
   "pcIn"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/985a5b9667b25390a00e217ee2086882a101d74a/ARVO-42519068/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_985a5b9667b2.cpg",
   "testcase_size": 563
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
   "dedup_token": "__asan_memcpy--Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)--A"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 411,
    "type": "D3DS.Node*"
   },
   "entity_name_cpg": "pcIn",
   "func_lines": [
    410,
    655
   ],
   "func_params": {
    "names": [
     "this",
     "pcSOut",
     "pcOut",
     "pcIn"
    ],
    "types": [
     "Assimp.Discreet3DSImporter",
     "aiScene*",
     "aiNode*",
     "D3DS.Node*",
     "aiMatrix4x4&"
    ]
   },
   "guards": [
    {
     "code": "a < pcSOut->mNumMeshes",
     "line": 418
    },
    {
     "code": "nullptr != pcMesh",
     "line": 420
    },
    {
     "code": "pcIn->mName == pcMesh->mName",
     "line": 422
    },
    {
     "code": "i < iArray.size()",
     "line": 439
    },
    {
     "code": "mesh->mColors[1] == nullptr",
     "line": 443
    },
    {
     "code": "pvCurrent != pvEnd",
     "line": 449
    },
    {
     "code": "imesh->mMat.Determinant() < 0.0f",
     "line": 455
    },
    {
     "code": "pvCurrent != pvEnd",
     "line": 457
    },
    {
     "code": "pvCurrent != pvEnd",
     "line": 466
    },
    {
     "code": "pcIn->mInstanceNumber > 1",
     "line": 482
    },
    {
     "code": "it != pcIn->aRotationKeys.end()",
     "line": 496
    },
    {
     "code": "pcIn->aPositionKeys.size() > 1",
     "line": 530
    },
    {
     "code": "pcIn->aRotationKeys.size() > 1",
     "line": 530
    },
    {
     "code": "pcIn->aScalingKeys.size() > 1",
     "line": 531
    },
    {
     "code": "pcIn->aCameraRollKeys.size() > 1",
     "line": 531
    },
    {
     "code": "pcIn->aTargetPositionKeys.size() > 1",
     "line": 532
    },
    {
     "code": "nullptr != anim",
     "line": 534
    },
    {
     "code": "pcIn->aCameraRollKeys.size() > 1",
     "line": 536
    },
    {
     "code": "i < pcIn->aCameraRollKeys.size()",
     "line": 543
    },
    {
     "code": "n < pcSOut->mNumCameras",
     "line": 596
    },
    {
     "code": "pcSOut->mCameras[n]->mName == pcOut->mName",
     "line": 597
    },
    {
     "code": "n < pcSOut->mNumLights",
     "line": 601
    },
    {
     "code": "pcSOut->mLights[n]->mName == pcOut->mName",
     "line": 602
    },
    {
     "code": "pcIn->aPositionKeys.size() > 0",
     "line": 612
    },
    {
     "code": "pcIn->aRotationKeys.size() > 0",
     "line": 620
    },
    {
     "code": "n < nda->mNumRotationKeys",
     "line": 626
    },
    {
     "code": "pcIn->aScalingKeys.size() > 0",
     "line": 636
    },
    {
     "code": "i < size",
     "line": 650
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "aiMatrix4x4::RotationZ(AI_DEG_TO_RAD(-pcIn->aCameraRollKeys[0].mValue),",
     "name": "RotationZ",
     "nargs": null
    },
    {
     "code": "AI_DEG_TO_RAD(-pcIn->aCameraRollKeys[0].mValue)",
     "name": "AI_DEG_TO_RAD",
     "nargs": 1
    },
    {
     "code": "-pcIn->aCameraRollKeys[0].mValue",
     "name": "<operator>.minus",
     "nargs": 1
    },
    {
     "code": "pcIn->aCameraRollKeys[0].mValue",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "pcIn->aCameraRollKeys[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pcIn->aCameraRollKeys",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pcIn"
   ],
   "osv_id": "ARVO-42519068",
   "sites": [
    {
     "args": "12",
     "callee": "<operator>.alloc",
     "code": "tmp[12]",
     "line": 483
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)"
  }
 },
 {
  "osv_id": "ARVO-42519114",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/dwg.spec",
    "line": 447,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "120",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 699,
    "fn": "dwg_decode_INSERT_private",
    "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = %d.%d.%X\", &s1[0], & | &s1[0] | s1[0] | &i1",
    "origin": "report:crash"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 809,
    "origin": "cpg",
    "args": "pts"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 820,
    "origin": "cpg",
    "args": "pts"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 831,
    "origin": "cpg",
    "args": "pts"
   },
   {
    "code": "free (fitpts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 867,
    "origin": "cpg",
    "args": "fitpts"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 879,
    "origin": "cpg",
    "args": "pts"
   }
  ],
  "crash": {
   "site": {
    "fn": "dwg_decode_INSERT_private",
    "file": "/src/libredwg/src/dwg.spec",
    "line": 699
   },
   "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = %d.%d.%X\", &s1[0], & | &s1[0] | s1[0] | &i1",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dwg_add_dat",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "p < end | ent.type != DWG_TYPE_MTEXT | ent.type != DWG_TYPE_MTEXT",
   "guard_count": 6,
   "control_structures": "IF:523,IF:527,IF:529,IF:531,IF:534,IF:536,IF:536,ELSE:542,IF:542,IF:542,IF:545,IF:547"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/7a44f5e43b2a49bf244e24b796a657c9c78f31a1/ARVO-42519114/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_7a44f5e43b2a.cpg",
   "testcase_size": 70
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
    809,
    820,
    831,
    867,
    879
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "dwg_decode_INSERT_private--dwg_decode_INSERT--dwg_decode_add_object"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*p = NULL",
     "line": 447
    },
    {
     "code": "p = strstr ((char*)dat->chain, \"\\nreaddwg\")",
     "line": 527
    },
    {
     "code": "p = next_line (p, end)",
     "line": 539
    },
    {
     "code": "p = strstr ((char*)dat->chain, \"\\nreaddxf\")",
     "line": 545
    },
    {
     "code": "p = next_line (p, end)",
     "line": 557
    },
    {
     "code": "p = strstr ((char*)dat->chain, \"\\nreadjson\")",
     "line": 564
    },
    {
     "code": "p = next_line (p, end)",
     "line": 580
    },
    {
     "code": "p = strstr ((char*)dat->chain, \"\\nimperial\\n\")",
     "line": 586
    },
    {
     "code": "p = next_line (p, end)",
     "line": 590
    },
    {
     "code": "p = strstr ((char*)dat->chain, \"\\nversion\")",
     "line": 592
    },
    {
     "code": "p = next_line (p, end)",
     "line": 620
    },
    {
     "code": "p = next_line (p, end)",
     "line": 970
    }
   ],
   "entity_decl": {
    "line": 447,
    "type": "char*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    441,
    974
   ],
   "func_params": {
    "names": [
     "dwgp",
     "dat"
    ],
    "types": [
     "Dwg_Data**",
     "Bit_Chain*"
    ]
   },
   "guards": [
    {
     "code": "*p == '\\n'",
     "line": 529
    },
    {
     "code": "(error = dwg_read_file (text, *dwgp)) > DWG_ERR_CRITICAL",
     "line": 534
    },
    {
     "code": "*p == '\\n'",
     "line": 547
    },
    {
     "code": "(error = dxf_read_file (text, *dwgp)) > DWG_ERR_CRITICAL",
     "line": 552
    },
    {
     "code": "*p == '\\n'",
     "line": 566
    },
    {
     "code": "(error = dwg_read_json (&in_dat, *dwgp)) > DWG_ERR_CRITICAL",
     "line": 574
    },
    {
     "code": "*p == '\\n'",
     "line": 597
    },
    {
     "code": "version < R_13",
     "line": 615
    },
    {
     "code": "p < end",
     "line": 635
    },
    {
     "code": "ent.type != DWG_TYPE_LINE",
     "line": 679
    },
    {
     "code": "ent.type != DWG_TYPE_LINE",
     "line": 679
    },
    {
     "code": "ent.type != DWG_TYPE_LINE",
     "line": 679
    },
    {
     "code": "ent.type != DWG_TYPE_LINE",
     "line": 679
    },
    {
     "code": "ent.type != DWG_TYPE_RAY",
     "line": 684
    },
    {
     "code": "ent.type != DWG_TYPE_RAY",
     "line": 684
    },
    {
     "code": "ent.type != DWG_TYPE_RAY",
     "line": 684
    },
    {
     "code": "ent.type != DWG_TYPE_RAY",
     "line": 684
    },
    {
     "code": "ent.type != DWG_TYPE_XLINE",
     "line": 689
    },
    {
     "code": "ent.type != DWG_TYPE_XLINE",
     "line": 689
    },
    {
     "code": "ent.type != DWG_TYPE_XLINE",
     "line": 689
    },
    {
     "code": "ent.type != DWG_TYPE_XLINE",
     "line": 689
    },
    {
     "code": "ent.type != DWG_TYPE_TEXT",
     "line": 694
    },
    {
     "code": "ent.type != DWG_TYPE_TEXT",
     "line": 694
    },
    {
     "code": "ent.type != DWG_TYPE_TEXT",
     "line": 694
    },
    {
     "code": "ent.type != DWG_TYPE_TEXT",
     "line": 694
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "line": 699
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "line": 699
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "line": 699
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "line": 699
    },
    {
     "code": "ent.type != DWG_TYPE_BLOCK",
     "line": 703
    },
    {
     "code": "ent.type != DWG_TYPE_BLOCK",
     "line": 703
    },
    {
     "code": "ent.type != DWG_TYPE_BLOCK",
     "line": 703
    },
    {
     "code": "ent.type != DWG_TYPE_BLOCK",
     "line": 703
    },
    {
     "code": "ent.type != DWG_TYPE_INSERT",
     "line": 711
    },
    {
     "code": "ent.type != DWG_TYPE_INSERT",
     "line": 711
    },
    {
     "code": "ent.type != DWG_TYPE_INSERT",
     "line": 711
    },
    {
     "code": "ent.type != DWG_TYPE_INSERT",
     "line": 711
    },
    {
     "code": "ent.type != DWG_TYPE_MINSERT",
     "line": 719
    },
    {
     "code": "ent.type != DWG_TYPE_MINSERT",
     "line": 719
    },
    {
     "code": "ent.type != DWG_TYPE_MINSERT",
     "line": 719
    },
    {
     "code": "ent.type != DWG_TYPE_MINSERT",
     "line": 719
    },
    {
     "code": "ent.type != DWG_TYPE_POINT",
     "line": 723
    },
    {
     "code": "ent.type != DWG_TYPE_POINT",
     "line": 723
    },
    {
     "code": "ent.type != DWG_TYPE_POINT",
     "line": 723
    },
    {
     "code": "ent.type != DWG_TYPE_POINT",
     "line": 723
    },
    {
     "code": "ent.type != DWG_TYPE_CIRCLE",
     "line": 728
    },
    {
     "code": "ent.type != DWG_TYPE_CIRCLE",
     "line": 728
    },
    {
     "code": "ent.type != DWG_TYPE_CIRCLE",
     "line": 728
    },
    {
     "code": "ent.type != DWG_TYPE_CIRCLE",
     "line": 728
    },
    {
     "code": "ent.type != DWG_TYPE_ARC",
     "line": 733
    },
    {
     "code": "ent.type != DWG_TYPE_ARC",
     "line": 733
    },
    {
     "code": "ent.type != DWG_TYPE_ARC",
     "line": 733
    },
    {
     "code": "ent.type != DWG_TYPE_ARC",
     "line": 733
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ALIGNED",
     "line": 740
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ALIGNED",
     "line": 740
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ALIGNED",
     "line": 740
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ALIGNED",
     "line": 740
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_LINEAR",
     "line": 747
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_LINEAR",
     "line": 747
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_LINEAR",
     "line": 747
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_LINEAR",
     "line": 747
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG2LN",
     "line": 754
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG2LN",
     "line": 754
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG2LN",
     "line": 754
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG2LN",
     "line": 754
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG3PT",
     "line": 761
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG3PT",
     "line": 761
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG3PT",
     "line": 761
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ANG3PT",
     "line": 761
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_DIAMETER",
     "line": 766
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_DIAMETER",
     "line": 766
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_DIAMETER",
     "line": 766
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_DIAMETER",
     "line": 766
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ORDINATE",
     "line": 771
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ORDINATE",
     "line": 771
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ORDINATE",
     "line": 771
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_ORDINATE",
     "line": 771
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_RADIUS",
     "line": 776
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_RADIUS",
     "line": 776
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_RADIUS",
     "line": 776
    },
    {
     "code": "ent.type != DWG_TYPE_DIMENSION_RADIUS",
     "line": 776
    },
    {
     "code": "ent.type != DWG_TYPE__3DFACE",
     "line": 789
    },
    {
     "code": "ent.type != DWG_TYPE__3DFACE",
     "line": 789
    },
    {
     "code": "ent.type != DWG_TYPE__3DFACE",
     "line": 789
    },
    {
     "code": "ent.type != DWG_TYPE__3DFACE",
     "line": 789
    },
    {
     "code": "ent.type != DWG_TYPE_SOLID",
     "line": 795
    },
    {
     "code": "ent.type != DWG_TYPE_SOLID",
     "line": 795
    },
    {
     "code": "ent.type != DWG_TYPE_SOLID",
     "line": 795
    },
    {
     "code": "ent.type != DWG_TYPE_SOLID",
     "line": 795
    },
    {
     "code": "ent.type != DWG_TYPE_TRACE",
     "line": 801
    },
    {
     "code": "ent.type != DWG_TYPE_TRACE",
     "line": 801
    },
    {
     "code": "ent.type != DWG_TYPE_TRACE",
     "line": 801
    },
    {
     "code": "ent.type != DWG_TYPE_TRACE",
     "line": 801
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_2D",
     "line": 812
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_2D",
     "line": 812
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_2D",
     "line": 812
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_2D",
     "line": 812
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_3D",
     "line": 823
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_3D",
     "line": 823
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_3D",
     "line": 823
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_3D",
     "line": 823
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_MESH",
     "line": 834
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_MESH",
     "line": 834
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_MESH",
     "line": 834
    },
    {
     "code": "ent.type != DWG_TYPE_POLYLINE_MESH",
     "line": 834
    },
    {
     "code": "ent.type != DWG_TYPE_DICTIONARY",
     "line": 838
    },
    {
     "code": "ent.type != DWG_TYPE_DICTIONARY",
     "line": 838
    },
    {
     "code": "ent.type != DWG_TYPE_DICTIONARY",
     "line": 838
    },
    {
     "code": "ent.type != DWG_TYPE_DICTIONARY",
     "line": 838
    },
    {
     "code": "ent.type == DWG_TYPE_DICTIONARY",
     "line": 839
    },
    {
     "code": "ent.type != DWG_TYPE_XRECORD",
     "line": 843
    },
    {
     "code": "ent.type != DWG_TYPE_XRECORD",
     "line": 843
    },
    {
     "code": "ent.type != DWG_TYPE_XRECORD",
     "line": 843
    },
    {
     "code": "ent.type != DWG_TYPE_XRECORD",
     "line": 843
    },
    {
     "code": "ent.type != DWG_TYPE_SHAPE",
     "line": 848
    },
    {
     "code": "ent.type != DWG_TYPE_SHAPE",
     "line": 848
    },
    {
     "code": "ent.type != DWG_TYPE_SHAPE",
     "line": 848
    },
    {
     "code": "ent.type != DWG_TYPE_SHAPE",
     "line": 848
    },
    {
     "code": "ent.type != DWG_TYPE_VIEWPORT",
     "line": 852
    },
    {
     "code": "ent.type != DWG_TYPE_VIEWPORT",
     "line": 852
    },
    {
     "code": "ent.type != DWG_TYPE_VIEWPORT",
     "line": 852
    },
    {
     "code": "ent.type != DWG_TYPE_VIEWPORT",
     "line": 852
    },
    {
     "code": "ent.type != DWG_TYPE_ELLIPSE",
     "line": 857
    },
    {
     "code": "ent.type != DWG_TYPE_ELLIPSE",
     "line": 857
    },
    {
     "code": "ent.type != DWG_TYPE_ELLIPSE",
     "line": 857
    },
    {
     "code": "ent.type != DWG_TYPE_ELLIPSE",
     "line": 857
    },
    {
     "code": "ent.type != DWG_TYPE_SPLINE",
     "line": 869
    },
    {
     "code": "ent.type != DWG_TYPE_SPLINE",
     "line": 869
    },
    {
     "code": "ent.type != DWG_TYPE_SPLINE",
     "line": 869
    },
    {
     "code": "ent.type != DWG_TYPE_SPLINE",
     "line": 869
    },
    {
     "code": "ent.type == DWG_TYPE_MTEXT",
     "line": 870
    },
    {
     "code": "ent.type != DWG_TYPE_LEADER",
     "line": 881
    },
    {
     "code": "ent.type != DWG_TYPE_LEADER",
     "line": 881
    },
    {
     "code": "ent.type != DWG_TYPE_LEADER",
     "line": 881
    },
    {
     "code": "ent.type != DWG_TYPE_LEADER",
     "line": 881
    },
    {
     "code": "ent.type != DWG_TYPE_TOLERANCE",
     "line": 886
    },
    {
     "code": "ent.type != DWG_TYPE_TOLERANCE",
     "line": 886
    },
    {
     "code": "ent.type != DWG_TYPE_TOLERANCE",
     "line": 886
    },
    {
     "code": "ent.type != DWG_TYPE_TOLERANCE",
     "line": 886
    },
    {
     "code": "ent.type != DWG_TYPE_MLINESTYLE",
     "line": 890
    },
    {
     "code": "ent.type != DWG_TYPE_MLINESTYLE",
     "line": 890
    },
    {
     "code": "ent.type != DWG_TYPE_MLINESTYLE",
     "line": 890
    },
    {
     "code": "ent.type != DWG_TYPE_MLINESTYLE",
     "line": 890
    },
    {
     "code": "ent.type != DWG_TYPE_LAYER",
     "line": 894
    },
    {
     "code": "ent.type != DWG_TYPE_LAYER",
     "line": 894
    },
    {
     "code": "ent.type != DWG_TYPE_LAYER",
     "line": 894
    },
    {
     "code": "ent.type != DWG_TYPE_LAYER",
     "line": 894
    },
    {
     "code": "ent.type != DWG_TYPE_STYLE",
     "line": 898
    },
    {
     "code": "ent.type != DWG_TYPE_STYLE",
     "line": 898
    },
    {
     "code": "ent.type != DWG_TYPE_STYLE",
     "line": 898
    },
    {
     "code": "ent.type != DWG_TYPE_STYLE",
     "line": 898
    },
    {
     "code": "ent.type != DWG_TYPE_LTYPE",
     "line": 902
    },
    {
     "code": "ent.type != DWG_TYPE_LTYPE",
     "line": 902
    },
    {
     "code": "ent.type != DWG_TYPE_LTYPE",
     "line": 902
    },
    {
     "code": "ent.type != DWG_TYPE_LTYPE",
     "line": 902
    },
    {
     "code": "ent.type != DWG_TYPE_VIEW",
     "line": 906
    },
    {
     "code": "ent.type != DWG_TYPE_VIEW",
     "line": 906
    },
    {
     "code": "ent.type != DWG_TYPE_VIEW",
     "line": 906
    },
    {
     "code": "ent.type != DWG_TYPE_VIEW",
     "line": 906
    },
    {
     "code": "ent.type != DWG_TYPE_VPORT",
     "line": 910
    },
    {
     "code": "ent.type != DWG_TYPE_VPORT",
     "line": 910
    },
    {
     "code": "ent.type != DWG_TYPE_VPORT",
     "line": 910
    },
    {
     "code": "ent.type != DWG_TYPE_VPORT",
     "line": 910
    },
    {
     "code": "ent.type != DWG_TYPE_DIMSTYLE",
     "line": 914
    },
    {
     "code": "ent.type != DWG_TYPE_DIMSTYLE",
     "line": 914
    },
    {
     "code": "ent.type != DWG_TYPE_DIMSTYLE",
     "line": 914
    },
    {
     "code": "ent.type != DWG_TYPE_DIMSTYLE",
     "line": 914
    },
    {
     "code": "ent.type != DWG_TYPE_GROUP",
     "line": 918
    },
    {
     "code": "ent.type != DWG_TYPE_GROUP",
     "line": 918
    },
    {
     "code": "ent.type != DWG_TYPE_GROUP",
     "line": 918
    },
    {
     "code": "ent.type != DWG_TYPE_GROUP",
     "line": 918
    },
    {
     "code": "ent.type != DWG_TYPE_UCS",
     "line": 924
    },
    {
     "code": "ent.type != DWG_TYPE_UCS",
     "line": 924
    },
    {
     "code": "ent.type != DWG_TYPE_UCS",
     "line": 924
    },
    {
     "code": "ent.type != DWG_TYPE_UCS",
     "line": 924
    },
    {
     "code": "ent.type == DWG_TYPE_VIEWPORT",
     "line": 925
    },
    {
     "code": "ent.type != DWG_TYPE__3DSOLID",
     "line": 962
    },
    {
     "code": "ent.type != DWG_TYPE__3DSOLID",
     "line": 962
    },
    {
     "code": "ent.type != DWG_TYPE__3DSOLID",
     "line": 962
    },
    {
     "code": "ent.type != DWG_TYPE__3DSOLID",
     "line": 962
    },
    {
     "code": "dwg->num_objects - orig_num > 1",
     "line": 973
    }
   ],
   "line_call_count": 63,
   "line_calls": [
    {
     "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = %d.%d.%X\", &s1[0], &i1, &i2, &u)",
     "name": "sscanf",
     "nargs": 6
    },
    {
     "code": "&s1[0]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "s1[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "&i1",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "&i2",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "&u",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "!ent.u.mtext ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "!ent.u.mtext",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "ent.type",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "fn_error(\"Invalid type mtext. Empty or wrong type\\n\")",
     "name": "fn_error",
     "nargs": 1
    },
    {
     "code": "hdl = dwg_add_handleref(dwg, i1, u, NULL)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "dwg_add_handleref(dwg, i1, u, NULL)",
     "name": "dwg_add_handleref",
     "nargs": 4
    },
    {
     "code": "dwg_dynapi_entity_set_value(ent.u.mtext, \"MTEXT\", s1, hdl, 0)",
     "name": "dwg_dynapi_entity_set_value",
     "nargs": 5
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = %d\", &s1[0], &i1)",
     "name": "sscanf",
     "nargs": 4
    },
    {
     "code": "&s1[0]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "s1[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "&i1",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "!ent.u.mtext ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "!ent.u.mtext",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "ent.type",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "fn_error(\"Invalid type mtext. Empty or wrong type\\n\")",
     "name": "fn_error",
     "nargs": 1
    },
    {
     "code": "dwg_dynapi_entity_set_value(ent.u.mtext, \"MTEXT\", s1, &i1, 0)",
     "name": "dwg_dynapi_entity_set_value",
     "nargs": 5
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "&i1",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = %lf\", &s1[0], &f1)",
     "name": "sscanf",
     "nargs": 4
    },
    {
     "code": "&s1[0]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "s1[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "&f1",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "!ent.u.mtext ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "!ent.u.mtext",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "ent.type",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "fn_error(\"Invalid type mtext. Empty or wrong type\\n\")",
     "name": "fn_error",
     "nargs": 1
    },
    {
     "code": "dwg_dynapi_entity_set_value(ent.u.mtext, \"MTEXT\", s1, &f1, 0)",
     "name": "dwg_dynapi_entity_set_value",
     "nargs": 5
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "&f1",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = \\\"%119s\\\"\", &s1[0], &text[0])",
     "name": "sscanf",
     "nargs": 4
    },
    {
     "code": "&s1[0]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "s1[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "&text[0]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "text[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "!ent.u.mtext ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "!ent.u.mtext",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.type != DWG_TYPE_MTEXT",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "ent.type",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "fn_error(\"Invalid type mtext. Empty or wrong type\\n\")",
     "name": "fn_error",
     "nargs": 1
    },
    {
     "code": "dwg_dynapi_entity_set_value(ent.u.mtext, \"MTEXT\", s1, text, 1)",
     "name": "dwg_dynapi_entity_set_value",
     "nargs": 5
    },
    {
     "code": "ent.u.mtext",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ent.u",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p",
    "s1",
    "i1",
    "i2",
    "u",
    "ent",
    "DWG_TYPE_MTEXT",
    "hdl",
    "dwg",
    "NULL",
    "f1",
    "text"
   ],
   "osv_id": "ARVO-42519114",
   "sites": [
    {
     "args": "120",
     "callee": "<operator>.alloc",
     "code": "text[120]",
     "line": 504
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "s_ver[16]",
     "line": 596
    },
    {
     "args": "120",
     "callee": "<operator>.alloc",
     "code": "s1[120]",
     "line": 637
    },
    {
     "args": "pts",
     "callee": "free",
     "code": "free (pts)",
     "line": 809
    },
    {
     "args": "pts",
     "callee": "free",
     "code": "free (pts)",
     "line": 820
    },
    {
     "args": "pts",
     "callee": "free",
     "code": "free (pts)",
     "line": 831
    },
    {
     "args": "fitpts",
     "callee": "free",
     "code": "free (fitpts)",
     "line": 867
    },
    {
     "args": "pts",
     "callee": "free",
     "code": "free (pts)",
     "line": 879
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "dwg_decode_INSERT_private",
   "use_fn": "dwg_decode_INSERT_private"
  }
 },
 {
  "osv_id": "ARVO-42519344",
  "project": "assimp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "writer",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Assimp::MD5Importer::LoadFileIntoMemory(Assimp::IOStream*)",
    "file": "/src/assimp/code/AssetLib/MD5/MD5Loader.cpp",
    "line": 182
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 259,
    "fn": "Assimp::MD5::MD5MeshParser::MD5MeshParser(std::__1::vector<Assimp::MD5::Section, std::__1::allocator<Assimp::MD5::Section> >&)",
    "code": "chunk(writer, Discreet3DS::CHUNK_TRACKOBJNAME) | Discreet3DS::CHUNK_TRACKOBJNAME",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Assimp::MD5::MD5MeshParser::MD5MeshParser(std::__1::vector<Assimp::MD5::Section, std::__1::allocator<Assimp::MD5::Section> >&)",
    "file": "/src/assimp/code/AssetLib/MD5/MD5Parser.cpp",
    "line": 259
   },
   "code": "chunk(writer, Discreet3DS::CHUNK_TRACKOBJNAME) | Discreet3DS::CHUNK_TRACKOBJNAME",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "WriteHierarchy",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:231,FOR:246,FOR:251"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "seq",
   "sibling_level"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/1e2cff63830847118cd54992b554c6b069ae2e33/ARVO-42519344/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_1e2cff638308.cpg",
   "testcase_size": 20947
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "Assimp::MD5::MD5MeshParser::MD5MeshParser(std::__1::vector<Assimp::MD5::Section, std::__1::allocator<Assimp::MD5::Section> >&)--Assimp::MD5Importer::LoadMD5Mesh"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "writer",
   "func_lines": [
    215,
    268
   ],
   "func_params": {
    "names": [
     "node",
     "seq",
     "sibling_level"
    ],
    "types": [
     "aiNode&",
     "int",
     "int"
    ]
   },
   "guards": [
    {
     "code": "sibling_level != -1",
     "line": 231
    },
    {
     "code": "i < node.mNumChildren",
     "line": 246
    },
    {
     "code": "i == 0",
     "line": 247
    },
    {
     "code": "i < node.mNumMeshes",
     "line": 251
    },
    {
     "code": "node.mNumChildren == 0",
     "line": 252
    },
    {
     "code": "i == 0",
     "line": 252
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "chunk(writer, Discreet3DS::CHUNK_TRACKOBJNAME)",
     "name": "chunk",
     "nargs": 2
    },
    {
     "code": "Discreet3DS::CHUNK_TRACKOBJNAME",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "writer",
    "Discreet3DS"
   ],
   "osv_id": "ARVO-42519344",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Assimp::MD5::MD5MeshParser::MD5MeshParser(std::__1::vector<Assimp::MD5::Section, std::__1::allocator<Assimp::MD5::Section> >&)"
  }
 },
 {
  "osv_id": "ARVO-42519555",
  "project": "libredwg",
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
    "fn": "json_preR13_header_write_private",
    "file": "/src/libredwg/src/./header_variables_r11.spec",
    "line": 145
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "json_cquote",
    "file": "/src/libredwg/src/out_json.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_cquote",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/a8656c2dc58d2deb857dad8ab0f8ef07ccba52ca/ARVO-42519555/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_a8656c2dc58d.cpg",
   "testcase_size": 3806
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "json_cquote--json_preR13_header_write_private--json_header_write"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    1322,
    1382
   ],
   "func_params": {
    "names": [
     "dest",
     "src",
     "len"
    ],
    "types": [
     "char*restrict",
     "char*restrict",
     "int"
    ]
   },
   "guards": [
    {
     "code": "c == '\"'",
     "line": 1338
    },
    {
     "code": "dest+1 < endp",
     "line": 1338
    },
    {
     "code": "c == '\\\\'",
     "line": 1343
    },
    {
     "code": "dest+2 < endp",
     "line": 1343
    },
    {
     "code": "dest+5 < endp",
     "line": 1345
    },
    {
     "code": "s[0] == 'U'",
     "line": 1345
    },
    {
     "code": "s[1] == '+'",
     "line": 1345
    },
    {
     "code": "c == '\\n'",
     "line": 1358
    },
    {
     "code": "dest+1 < endp",
     "line": 1358
    },
    {
     "code": "c == '\\r'",
     "line": 1363
    },
    {
     "code": "dest+1 < endp",
     "line": 1363
    },
    {
     "code": "c < 0x1f",
     "line": 1368
    },
    {
     "code": "dest+5 < endp",
     "line": 1368
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42519555",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "json_cquote"
  }
 },
 {
  "osv_id": "ARVO-42520151",
  "project": "wolfssl",
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
    "fn": "cryptofuzz::util::malloc(unsigned long)",
    "file": "/src/cryptofuzz-openssl-api/util.cpp",
    "line": 551
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
    "dir": "WRITE",
    "width": 16,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/b15bc3d2368dc2f990cda0c235711498cc758996/ARVO-42520151/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_b15bc3d2368d.cpg",
   "testcase_size": 160
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
   "dedup_token": "__asan_memcpy--wc_AesCbcEncrypt--evpCipherBlock"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": null
  }
 },
 {
  "osv_id": "ARVO-42520165",
  "project": "wolfssl",
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
    "fn": "cryptofuzz::util::malloc(unsigned long)",
    "file": "/src/cryptofuzz-openssl-api/util.cpp",
    "line": 551
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
    "dir": "WRITE",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/b15bc3d2368dc2f990cda0c235711498cc758996/ARVO-42520165/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_b15bc3d2368d.cpg",
   "testcase_size": 144
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
   "dedup_token": "wc_AesFeedbackEncrypt--wc_AesOfbEncrypt--evpCipherBlock"
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