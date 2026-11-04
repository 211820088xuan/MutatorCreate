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
  "osv_id": "OSV-2021-1235",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pv_cur_pic_addr0",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "line": 63
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 222,
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "line": 222
   },
   "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_fill_bs1_16x16mb_pslice",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "pv_cur_pic_addr0 != pv_nbr_pic_addr0 | pv_cur_pic_addr0 != pv_nbr_pic_addr0",
   "guard_count": 2
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "ps_cur_mv_pred",
   "ppv_map_ref_idx_to_poc"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1235.log",
   "cpg": null,
   "testcase_size": 82
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
   "loc_size": 1152,
   "loc_offset": 4,
   "loc_kind": "region",
   "dedup_token": "ih264d_fill_bs1_16x16mb_pslice--ih264d_compute_bs_non_mbaff_thread--ih264d_recon_deblk_slice",
   "overshoot_ratio": 0.003472
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_fill_bs1_16x16mb_pslice"
  }
 },
 {
  "osv_id": "OSV-2021-1559",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_dec",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "line": 63
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1711,
    "fn": "ih264d_mark_err_slice_skip",
    "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_mark_err_slice_skip",
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "line": 1711
   },
   "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_mark_err_slice_skip",
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
  "input_reachability": [
   "ps_dec"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1559.log",
   "cpg": null,
   "testcase_size": 4489
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
   "loc_size": 3456,
   "loc_offset": 16,
   "loc_kind": "region",
   "dedup_token": "ih264d_mark_err_slice_skip--ih264d_video_decode--ih264d_api_function",
   "overshoot_ratio": 0.00463
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_mark_err_slice_skip"
  }
 },
 {
  "osv_id": "OSV-2021-1589",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "nthreads",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 408,
    "fn": "inflate",
    "code": "nthreads = 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "inflate",
    "file": "/src/c-blosc2/internal-complibs/zlib-ng-2.0.6/inflate.c",
    "line": 408
   },
   "code": "nthreads = 1",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "main",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "nthreads_ <= nthreads | nthreads_ <= nthreads | nthreads_ <= nthreads",
   "guard_count": 3
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1589.log",
   "cpg": null,
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_size": 246,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "inflate--uncompress2--uncompress",
   "overshoot_ratio": 0.0
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
  "osv_id": "OSV-2021-1645",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 519,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 173
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 544,
    "fn": "ndlz4_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz4_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 544
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 201851904,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz4_decompress",
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
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1645.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_size": 804,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--ndlz4_decompress--blosc_d",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* op = (uint8_t*)output",
     "line": 519
    }
   ],
   "entity_decl": {
    "line": 519,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "op",
   "func_lines": [
    512,
    698
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
     "line": 533
    },
    {
     "code": "i < 2",
     "line": 547
    },
    {
     "code": "ii[0] < i_stop[0]",
     "line": 557
    },
    {
     "code": "ii[1] < i_stop[1]",
     "line": 558
    },
    {
     "code": "ip > ip_limit",
     "line": 559
    },
    {
     "code": "ii[0] == i_stop[0] - 1",
     "line": 563
    },
    {
     "code": "blockshape[0] % 4 == 0",
     "line": 564
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 568
    },
    {
     "code": "blockshape[1] % 4 == 0",
     "line": 569
    },
    {
     "code": "token == 0",
     "line": 574
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 577
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 581
    },
    {
     "code": "(token >> 3U) == 28",
     "line": 591
    },
    {
     "code": "(token >> 3U) < 30",
     "line": 597
    },
    {
     "code": "(token >> 3U) == 30",
     "line": 602
    },
    {
     "code": "l < 4",
     "line": 612
    },
    {
     "code": "l != i",
     "line": 613
    },
    {
     "code": "l != j",
     "line": 613
    },
    {
     "code": "l != k",
     "line": 613
    },
    {
     "code": "token == 128",
     "line": 626
    },
    {
     "code": "k < 4",
     "line": 635
    },
    {
     "code": "k != i",
     "line": 636
    },
    {
     "code": "k != j",
     "line": 636
    },
    {
     "code": "k < 4",
     "line": 653
    },
    {
     "code": "k != i",
     "line": 654
    },
    {
     "code": "k != j",
     "line": 654
    },
    {
     "code": "l == -1",
     "line": 655
    },
    {
     "code": "i < 4",
     "line": 673
    },
    {
     "code": "i < padding[0]",
     "line": 674
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 680
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 688
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 692
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
   "osv_id": "OSV-2021-1645",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "blockshape[2]",
     "line": 521
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "eshape[2]",
     "line": 522
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "local_buffer[16]",
     "line": 524
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 546
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 553
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 554
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "cell_aux[16]",
     "line": 556
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz4_decompress"
  }
 },
 {
  "osv_id": "OSV-2021-1663",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 519,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 173
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 544,
    "fn": "ndlz4_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz4_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 544
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 48423648,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz4_decompress",
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
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1663.log",
   "cpg": null,
   "testcase_size": 36
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "loc_size": 656,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--ndlz4_decompress--blosc_d",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* op = (uint8_t*)output",
     "line": 519
    }
   ],
   "entity_decl": {
    "line": 519,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "op",
   "func_lines": [
    512,
    698
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
     "line": 533
    },
    {
     "code": "i < 2",
     "line": 547
    },
    {
     "code": "ii[0] < i_stop[0]",
     "line": 557
    },
    {
     "code": "ii[1] < i_stop[1]",
     "line": 558
    },
    {
     "code": "ip > ip_limit",
     "line": 559
    },
    {
     "code": "ii[0] == i_stop[0] - 1",
     "line": 563
    },
    {
     "code": "blockshape[0] % 4 == 0",
     "line": 564
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 568
    },
    {
     "code": "blockshape[1] % 4 == 0",
     "line": 569
    },
    {
     "code": "token == 0",
     "line": 574
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 577
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 581
    },
    {
     "code": "(token >> 3U) == 28",
     "line": 591
    },
    {
     "code": "(token >> 3U) < 30",
     "line": 597
    },
    {
     "code": "(token >> 3U) == 30",
     "line": 602
    },
    {
     "code": "l < 4",
     "line": 612
    },
    {
     "code": "l != i",
     "line": 613
    },
    {
     "code": "l != j",
     "line": 613
    },
    {
     "code": "l != k",
     "line": 613
    },
    {
     "code": "token == 128",
     "line": 626
    },
    {
     "code": "k < 4",
     "line": 635
    },
    {
     "code": "k != i",
     "line": 636
    },
    {
     "code": "k != j",
     "line": 636
    },
    {
     "code": "k < 4",
     "line": 653
    },
    {
     "code": "k != i",
     "line": 654
    },
    {
     "code": "k != j",
     "line": 654
    },
    {
     "code": "l == -1",
     "line": 655
    },
    {
     "code": "i < 4",
     "line": 673
    },
    {
     "code": "i < padding[0]",
     "line": 674
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 680
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 688
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 692
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
   "osv_id": "OSV-2021-1663",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "blockshape[2]",
     "line": 521
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "eshape[2]",
     "line": 522
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "local_buffer[16]",
     "line": 524
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 546
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 553
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 554
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "cell_aux[16]",
     "line": 556
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz4_decompress"
  }
 },
 {
  "osv_id": "OSV-2021-1676",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 438,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 173
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 462,
    "fn": "ndlz8_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz8_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 462
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 201851904,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz8_decompress",
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
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1676.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_size": 804,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--ndlz8_decompress--blosc_d",
   "overshoot_ratio": 0.0
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
    429,
    575
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
     "code": "input_len < 8",
     "line": 444
    },
    {
     "code": "ndim != 2",
     "line": 451
    },
    {
     "code": "i < 2",
     "line": 465
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
     "line": 484
    },
    {
     "code": "blockshape[0] % cell_shape == 0",
     "line": 485
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 489
    },
    {
     "code": "blockshape[1] % cell_shape == 0",
     "line": 490
    },
    {
     "code": "token == 0",
     "line": 496
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 499
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 503
    },
    {
     "code": "match_type == 21",
     "line": 507
    },
    {
     "code": "l < 3",
     "line": 512
    },
    {
     "code": "l < cell_shape",
     "line": 516
    },
    {
     "code": "l < row",
     "line": 517
    },
    {
     "code": "l > row + 2",
     "line": 517
    },
    {
     "code": "match_type == 17",
     "line": 522
    },
    {
     "code": "l < 2",
     "line": 527
    },
    {
     "code": "l < cell_shape",
     "line": 531
    },
    {
     "code": "l < row",
     "line": 532
    },
    {
     "code": "l > row + 1",
     "line": 532
    },
    {
     "code": "i < (uint32_t) cell_shape",
     "line": 545
    },
    {
     "code": "i < padding[0]",
     "line": 546
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 552
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 565
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 569
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
   "osv_id": "OSV-2021-1676",
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
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 464
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 471
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 472
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 474
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 475
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 480
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 481
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 539
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 540
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 554
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 555
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 562
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 563
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
  "osv_id": "OSV-2021-1710",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
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
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 540,
    "fn": "ndlz4_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz4_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 540
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 201851904,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz4_decompress",
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
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1710.log",
   "cpg": null,
   "testcase_size": 73
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
   "loc_size": 804,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--ndlz4_decompress--ndlz_decompress",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz4_decompress"
  }
 },
 {
  "osv_id": "OSV-2021-1712",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 438,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 173
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 462,
    "fn": "ndlz8_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz8_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 462
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 67108864,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz8_decompress",
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
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1712.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
   "testcase_size": 40
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 640,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--ndlz8_decompress--blosc_d",
   "overshoot_ratio": 0.0
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
    429,
    575
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
     "code": "input_len < 8",
     "line": 444
    },
    {
     "code": "ndim != 2",
     "line": 451
    },
    {
     "code": "i < 2",
     "line": 465
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
     "line": 484
    },
    {
     "code": "blockshape[0] % cell_shape == 0",
     "line": 485
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 489
    },
    {
     "code": "blockshape[1] % cell_shape == 0",
     "line": 490
    },
    {
     "code": "token == 0",
     "line": 496
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 499
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 503
    },
    {
     "code": "match_type == 21",
     "line": 507
    },
    {
     "code": "l < 3",
     "line": 512
    },
    {
     "code": "l < cell_shape",
     "line": 516
    },
    {
     "code": "l < row",
     "line": 517
    },
    {
     "code": "l > row + 2",
     "line": 517
    },
    {
     "code": "match_type == 17",
     "line": 522
    },
    {
     "code": "l < 2",
     "line": 527
    },
    {
     "code": "l < cell_shape",
     "line": 531
    },
    {
     "code": "l < row",
     "line": 532
    },
    {
     "code": "l > row + 1",
     "line": 532
    },
    {
     "code": "i < (uint32_t) cell_shape",
     "line": 545
    },
    {
     "code": "i < padding[0]",
     "line": 546
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 552
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 565
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 569
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
   "osv_id": "OSV-2021-1712",
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
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 464
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 471
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 472
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 474
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 475
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 480
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 481
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 539
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 540
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 554
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 555
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 562
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 563
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
  "osv_id": "OSV-2021-1755",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 519,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 173
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 544,
    "fn": "ndlz4_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz4_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 544
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 201851904,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz4_decompress",
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
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1755.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_size": 804,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--ndlz4_decompress--ndlz_decompress",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* op = (uint8_t*)output",
     "line": 519
    }
   ],
   "entity_decl": {
    "line": 519,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "op",
   "func_lines": [
    512,
    698
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
     "line": 533
    },
    {
     "code": "i < 2",
     "line": 547
    },
    {
     "code": "ii[0] < i_stop[0]",
     "line": 557
    },
    {
     "code": "ii[1] < i_stop[1]",
     "line": 558
    },
    {
     "code": "ip > ip_limit",
     "line": 559
    },
    {
     "code": "ii[0] == i_stop[0] - 1",
     "line": 563
    },
    {
     "code": "blockshape[0] % 4 == 0",
     "line": 564
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 568
    },
    {
     "code": "blockshape[1] % 4 == 0",
     "line": 569
    },
    {
     "code": "token == 0",
     "line": 574
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 577
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 581
    },
    {
     "code": "(token >> 3U) == 28",
     "line": 591
    },
    {
     "code": "(token >> 3U) < 30",
     "line": 597
    },
    {
     "code": "(token >> 3U) == 30",
     "line": 602
    },
    {
     "code": "l < 4",
     "line": 612
    },
    {
     "code": "l != i",
     "line": 613
    },
    {
     "code": "l != j",
     "line": 613
    },
    {
     "code": "l != k",
     "line": 613
    },
    {
     "code": "token == 128",
     "line": 626
    },
    {
     "code": "k < 4",
     "line": 635
    },
    {
     "code": "k != i",
     "line": 636
    },
    {
     "code": "k != j",
     "line": 636
    },
    {
     "code": "k < 4",
     "line": 653
    },
    {
     "code": "k != i",
     "line": 654
    },
    {
     "code": "k != j",
     "line": 654
    },
    {
     "code": "l == -1",
     "line": 655
    },
    {
     "code": "i < 4",
     "line": 673
    },
    {
     "code": "i < padding[0]",
     "line": 674
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 680
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 688
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 692
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
   "osv_id": "OSV-2021-1755",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "blockshape[2]",
     "line": 521
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "eshape[2]",
     "line": 522
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "local_buffer[16]",
     "line": 524
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 546
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 553
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 554
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "cell_aux[16]",
     "line": 556
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz4_decompress"
  }
 },
 {
  "osv_id": "OSV-2021-1791",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "internalBuffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 130,
    "type": "void*const",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "dictSize ;; ddict->cMem",
   "size_expr_cpg_callee": "ZSTD_customMalloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 134,
    "fn": "ZSTD_initDDict_internal",
    "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_initDDict_internal",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/decompress/zstd_ddict.c",
    "line": 134
   },
   "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
   "access": {
    "dir": "READ",
    "width": 61951,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ZSTD_initDDict_internal",
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
  "input_reachability": [
   "ddict",
   "dict",
   "dictSize"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1791.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_886d4c9b7833.cpg",
   "testcase_size": 24087
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "loc_size": 24087,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ZSTD_initDDict_internal--ZSTD_createDDict_advanced",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* const internalBuffer = ZSTD_customMalloc(dictSize, ddict->cMem)",
     "line": 130
    }
   ],
   "entity_decl": {
    "line": 130,
    "type": "void*const"
   },
   "entity_name_cpg": "internalBuffer",
   "func_lines": [
    120,
    143
   ],
   "func_params": {
    "names": [
     "ddict",
     "dict",
     "dictSize",
     "dictLoadMethod",
     "dictContentType"
    ],
    "types": [
     "ZSTD_DDict*",
     "void*",
     "size_t",
     "ZSTD_dictLoadMethod_e",
     "ZSTD_dictContentType_e"
    ]
   },
   "guards": [
    {
     "code": "dictLoadMethod == ZSTD_dlm_byRef",
     "line": 125
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "ZSTD_memcpy(internalBuffer, dict, dictSize)",
     "name": "ZSTD_memcpy",
     "nargs": 3
    },
    {
     "code": "memcpy((internalBuffer), (dict), (dictSize))",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "internalBuffer",
    "dict",
    "dictSize"
   ],
   "osv_id": "OSV-2021-1791",
   "sites": [
    {
     "args": "dictSize ;; ddict->cMem",
     "callee": "ZSTD_customMalloc",
     "code": "ZSTD_customMalloc(dictSize, ddict->cMem)",
     "line": 130
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ZSTD_initDDict_internal"
  }
 },
 {
  "osv_id": "OSV-2021-207",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "version",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2470,
    "type": "uint8_t",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 2470,
    "fn": "blosc_getitem",
    "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_getitem",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 2470
   },
   "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "blosc_getitem",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "version > BLOSC_VERSION_FORMAT",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "src"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-207.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_0e8bdfce66ba.cpg",
   "testcase_size": 89
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "blosc_getitem--get_coffset--frame_get_lazychunk"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "version = _src[BLOSC2_CHUNK_VERSION]",
     "line": 2470
    }
   ],
   "entity_decl": {
    "line": 2470,
    "type": "uint8_t"
   },
   "entity_name_cpg": "version",
   "func_lines": [
    2465,
    2503
   ],
   "func_params": {
    "names": [
     "src",
     "start",
     "nitems",
     "dest"
    ],
    "types": [
     "void*",
     "int",
     "int",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "version > BLOSC_VERSION_FORMAT",
     "line": 2471
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "version = _src[BLOSC2_CHUNK_VERSION]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "_src[BLOSC2_CHUNK_VERSION]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "version",
    "_src",
    "BLOSC2_CHUNK_VERSION"
   ],
   "osv_id": "OSV-2021-207",
   "sites": [
    {
     "args": "context.serial_context",
     "callee": "free_thread_context",
     "code": "free_thread_context(context.serial_context)",
     "line": 2501
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "blosc_getitem"
  }
 },
 {
  "osv_id": "OSV-2021-221",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "cbytes",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1000,
    "type": "int32_t",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "strlen(context->schunk->frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1116,
    "fn": "blosc_d",
    "code": "cbytes = sw32_(src) | sw32_(src)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_d",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 1116
   },
   "code": "cbytes = sw32_(src) | sw32_(src)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "blosc_d",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "cbytes > 0 | srcsize < cbytes | cbytes == 0",
   "guard_count": 6
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "thread_context",
   "bsize",
   "src",
   "srcsize",
   "src_offset",
   "nblock",
   "dest",
   "dest_offset",
   "tmp"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-221.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_fdfeb753f3c1.cpg",
   "testcase_size": 89
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_size": 89,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "blosc_d--_blosc_getitem--blosc_getitem",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cbytes = sw32_(src)",
     "line": 1116
    },
    {
     "code": "cbytes = 0",
     "line": 1156
    }
   ],
   "entity_decl": {
    "line": 1000,
    "type": "int32_t"
   },
   "entity_name_cpg": "cbytes",
   "func_lines": [
    987,
    1228
   ],
   "func_params": {
    "names": [
     "thread_context",
     "bsize",
     "leftoverblock",
     "src",
     "srcsize",
     "src_offset",
     "nblock",
     "dest",
     "dest_offset",
     "tmp",
     "tmp2"
    ],
    "types": [
     "thread_context*",
     "int32_t",
     "int32_t",
     "uint8_t*",
     "int32_t",
     "int32_t",
     "int32_t",
     "uint8_t*",
     "int32_t",
     "uint8_t*",
     "uint8_t*"
    ]
   },
   "guards": [
    {
     "code": "context->block_maskout != NULL",
     "line": 1007
    },
    {
     "code": "context->header_overhead == BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 1012
    },
    {
     "code": "context->schunk == NULL",
     "line": 1016
    },
    {
     "code": "context->schunk->frame == NULL",
     "line": 1020
    },
    {
     "code": "rbytes != block_csize",
     "line": 1058
    },
    {
     "code": "chunk_nbytes + context->header_overhead != chunk_cbytes",
     "line": 1069
    },
    {
     "code": "chunk_cbytes < context->header_overhead + (nblock * context->blocksize) + bsize_",
     "line": 1073
    },
    {
     "code": "next_filter(filters, BLOSC2_MAX_FILTERS, 'd') != BLOSC_DELTA",
     "line": 1092
    },
    {
     "code": "j < nstreams",
     "line": 1110
    },
    {
     "code": "srcsize < sizeof(int32_t)",
     "line": 1111
    },
    {
     "code": "cbytes > 0",
     "line": 1117
    },
    {
     "code": "srcsize < cbytes",
     "line": 1118
    },
    {
     "code": "cbytes == 0",
     "line": 1128
    },
    {
     "code": "cbytes < 0",
     "line": 1133
    },
    {
     "code": "srcsize < sizeof(uint8_t)",
     "line": 1137
    },
    {
     "code": "cbytes < -255",
     "line": 1149
    },
    {
     "code": "cbytes == neblock",
     "line": 1159
    },
    {
     "code": "compformat == BLOSC_BLOSCLZ_FORMAT",
     "line": 1164
    },
    {
     "code": "nbytes != neblock",
     "line": 1208
    },
    {
     "code": "errcode < 0",
     "line": 1222
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "cbytes = sw32_(src)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "sw32_(src)",
     "name": "sw32_",
     "nargs": 1
    }
   ],
   "line_ids": [
    "cbytes",
    "src"
   ],
   "osv_id": "OSV-2021-221",
   "sites": [
    {
     "args": "strlen(context->schunk->frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(context->schunk->frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1)",
     "line": 1044
    },
    {
     "args": "chunkpath",
     "callee": "free",
     "code": "free(chunkpath)",
     "line": 1047
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "blosc_d"
  }
 },
 {
  "osv_id": "OSV-2021-246",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "usermeta",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1055,
    "type": "uint8_t**",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1116,
    "fn": "frame_get_usermeta",
    "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "frame_get_usermeta",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1116
   },
   "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
   "access": {
    "dir": "READ",
    "width": 538976288,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "frame_get_usermeta",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "trailer_offset < 0 | usermeta_len < 0 | usermeta_len == 0",
   "guard_count": 3
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "frame",
   "usermeta"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-246.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_c91ed64cc540.cpg",
   "testcase_size": 89
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_size": 89,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--frame_get_usermeta--blosc2_frame_to_schunk",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1055,
    "type": "uint8_t**"
   },
   "entity_name_cpg": "usermeta",
   "func_lines": [
    1055,
    1140
   ],
   "func_params": {
    "names": [
     "frame",
     "usermeta"
    ],
    "types": [
     "blosc2_frame*",
     "uint8_t**"
    ]
   },
   "guards": [
    {
     "code": "ret < 0",
     "line": 1064
    },
    {
     "code": "nbytes > 0",
     "line": 1068
    },
    {
     "code": "trailer_offset < 0",
     "line": 1069
    },
    {
     "code": "trailer_offset + FRAME_TRAILER_USERMETA_LEN_OFFSET + (signed)sizeof(int32_t) > frame_len",
     "line": 1073
    },
    {
     "code": "frame->sdata != NULL",
     "line": 1080
    },
    {
     "code": "rbytes != sizeof(int32_t)",
     "line": 1097
    },
    {
     "code": "usermeta_len < 0",
     "line": 1105
    },
    {
     "code": "usermeta_len == 0",
     "line": 1109
    },
    {
     "code": "frame->sdata != NULL",
     "line": 1115
    },
    {
     "code": "rbytes != (size_t)usermeta_len",
     "line": 1132
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_OFFSET, usermeta_len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "*usermeta",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_OFFSET",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "frame->sdata + trailer_offset",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "frame->sdata",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "FRAME_TRAILER_USERMETA_OFFSET",
     "name": "FRAME_TRAILER_USERMETA_OFFSET",
     "nargs": 0
    }
   ],
   "line_ids": [
    "usermeta",
    "frame",
    "trailer_offset",
    "usermeta_len"
   ],
   "osv_id": "OSV-2021-246",
   "sites": [
    {
     "args": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
     "line": 1086
    },
    {
     "args": "eframe_name",
     "callee": "free",
     "code": "free(eframe_name)",
     "line": 1089
    },
    {
     "args": "usermeta_len",
     "callee": "malloc",
     "code": "malloc(usermeta_len)",
     "line": 1114
    },
    {
     "args": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
     "line": 1121
    },
    {
     "args": "eframe_name",
     "callee": "free",
     "code": "free(eframe_name)",
     "line": 1124
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "frame_get_usermeta"
  }
 },
 {
  "osv_id": "OSV-2021-247",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "version",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2632,
    "type": "uint8_t",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 2632,
    "fn": "blosc_getitem",
    "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_getitem",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 2632
   },
   "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "blosc_getitem",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "version > BLOSC_VERSION_FORMAT",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "src"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-247.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_b4bf11aee91b.cpg",
   "testcase_size": 89
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_size": 89,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "blosc_getitem--get_coffset--frame_get_lazychunk",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "version = _src[BLOSC2_CHUNK_VERSION]",
     "line": 2632
    }
   ],
   "entity_decl": {
    "line": 2632,
    "type": "uint8_t"
   },
   "entity_name_cpg": "version",
   "func_lines": [
    2627,
    2669
   ],
   "func_params": {
    "names": [
     "src",
     "start",
     "nitems",
     "dest"
    ],
    "types": [
     "void*",
     "int",
     "int",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "version > BLOSC_VERSION_FORMAT",
     "line": 2633
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "version = _src[BLOSC2_CHUNK_VERSION]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "_src[BLOSC2_CHUNK_VERSION]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "version",
    "_src",
    "BLOSC2_CHUNK_VERSION"
   ],
   "osv_id": "OSV-2021-247",
   "sites": [
    {
     "args": "context.serial_context",
     "callee": "free_thread_context",
     "code": "free_thread_context(context.serial_context)",
     "line": 2667
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "blosc_getitem"
  }
 },
 {
  "osv_id": "OSV-2021-27",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "internalBuffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 130,
    "type": "void*const",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "dictSize ;; ddict->cMem",
   "size_expr_cpg_callee": "ZSTD_malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 134,
    "fn": "ZSTD_initDDict_internal",
    "code": "memcpy(internalBuffer, dict, dictSize)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_initDDict_internal",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/decompress/zstd_ddict.c",
    "line": 134
   },
   "code": "memcpy(internalBuffer, dict, dictSize)",
   "access": {
    "dir": "READ",
    "width": 117791,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ZSTD_initDDict_internal",
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
  "input_reachability": [
   "ddict",
   "dict",
   "dictSize"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-27.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_0e8bdfce66ba.cpg",
   "testcase_size": 27249
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_size": 27249,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ZSTD_initDDict_internal--ZSTD_createDDict_advanced",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* const internalBuffer = ZSTD_malloc(dictSize, ddict->cMem)",
     "line": 130
    }
   ],
   "entity_decl": {
    "line": 130,
    "type": "void*const"
   },
   "entity_name_cpg": "internalBuffer",
   "func_lines": [
    120,
    143
   ],
   "func_params": {
    "names": [
     "ddict",
     "dict",
     "dictSize",
     "dictLoadMethod",
     "dictContentType"
    ],
    "types": [
     "ZSTD_DDict*",
     "void*",
     "size_t",
     "ZSTD_dictLoadMethod_e",
     "ZSTD_dictContentType_e"
    ]
   },
   "guards": [
    {
     "code": "dictLoadMethod == ZSTD_dlm_byRef",
     "line": 125
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(internalBuffer, dict, dictSize)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "internalBuffer",
    "dict",
    "dictSize"
   ],
   "osv_id": "OSV-2021-27",
   "sites": [
    {
     "args": "dictSize ;; ddict->cMem",
     "callee": "ZSTD_malloc",
     "code": "ZSTD_malloc(dictSize, ddict->cMem)",
     "line": 130
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ZSTD_initDDict_internal"
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