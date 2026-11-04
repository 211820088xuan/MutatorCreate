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
  "osv_id": "ARVO-42477544",
  "project": "libhevc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_proc",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 3389,
    "type": "process_ctxt_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc(void*, int, int)",
    "file": "/src/libhevc/fuzzer/hevc_dec_fuzzer.cpp",
    "line": 53
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3151,
    "fn": "ihevcd_parse_slice_data",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ihevcd_parse_slice_data",
    "file": "/src/libhevc/decoder/ihevcd_parse_slice.c",
    "line": 3151
   },
   "code": "ps_proc->u4_ctb_top_left_pu_idx = ps_proc->pu4_pic_pu_idx_top[(ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE) + ctb_size / MIN_PU_SIZE - 1]",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ihevcd_parse_slice_data",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/cdd7c97c270408c330fcffd7d280e68b3678efe4/ARVO-42477544/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_cdd7c97c2704.cpg",
   "testcase_size": 113
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
   "dedup_token": "ihevcd_parse_slice_data--ihevcd_decode--ihevcd_cxa_api_function"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*ps_proc = &ps_codec->as_process[0]",
     "line": 2618
    },
    {
     "code": "ps_proc->i4_ctb_cnt = ps_tile->u2_wd",
     "line": 2627
    },
    {
     "code": "ps_proc->i4_ctb_x   = ps_codec->s_parse.i4_ctb_x",
     "line": 2628
    },
    {
     "code": "ps_proc->i4_ctb_y   = ps_codec->s_parse.i4_ctb_y",
     "line": 2629
    },
    {
     "code": "ps_proc->i4_cur_slice_idx = ps_codec->s_parse.i4_cur_slice_idx",
     "line": 2630
    },
    {
     "code": "ps_proc = &ps_codec->as_process[(ps_codec->i4_num_cores == 1) ? 1 : (ps_codec->i4_num_cores - 1)]",
     "line": 3060
    },
    {
     "code": "*ps_proc = &ps_codec->as_process[(ps_codec->i4_num_cores == 1) ? 1 : (ps_codec->i4_num_cores - 1)]",
     "line": 3104
    },
    {
     "code": "ps_proc->u4_ctb_top_left_pu_idx = ps_proc->pu4_pic_pu_idx_top[(ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE) + ctb_size / MIN_PU_SIZE - 1]",
     "line": 3151
    },
    {
     "code": "ps_proc->pu4_pic_pu_idx_left[i] = pu4_nbr_pu_idx[(ctb_size / MIN_PU_SIZE)",
     "line": 3156
    },
    {
     "code": "ps_proc->pu4_pic_pu_idx_top[(ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE) + i] =",
     "line": 3160
    },
    {
     "code": "ps_proc = &ps_codec->as_process[(ps_codec->i4_num_cores == 1) ? 1 : (ps_codec->i4_num_cores - 1)]",
     "line": 3206
    },
    {
     "code": "*ps_proc = &ps_codec->as_process[0]",
     "line": 3389
    },
    {
     "code": "ps_proc->i4_ctb_cnt = ps_proc->ps_tile->u2_wd",
     "line": 3391
    }
   ],
   "entity_decl": {
    "line": 3389,
    "type": "process_ctxt_t*"
   },
   "entity_name_cpg": "ps_proc",
   "func_lines": [
    2287,
    3504
   ],
   "func_params": {
    "names": [
     "ps_codec"
    ],
    "types": [
     "codec_t*"
    ]
   },
   "guards": [
    {
     "code": "0 != ps_codec->s_parse.i4_cur_slice_idx",
     "line": 2318
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2333
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2359
    },
    {
     "code": "1 == ps_slice_hdr->i1_dependent_slice_flag",
     "line": 2361
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_x",
     "line": 2364
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_y",
     "line": 2364
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_y",
     "line": 2379
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_x",
     "line": 2380
    },
    {
     "code": "ret != (IHEVCD_ERROR_T)IHEVCD_SUCCESS",
     "line": 2383
    },
    {
     "code": "ps_slice_hdr->i1_num_ref_idx_l1_active != 0",
     "line": 2396
    },
    {
     "code": "i < ps_slice_hdr->i1_num_ref_idx_l1_active",
     "line": 2398
    },
    {
     "code": "ps_slice_hdr->i1_num_ref_idx_l0_active != 0",
     "line": 2405
    },
    {
     "code": "i < ps_slice_hdr->i1_num_ref_idx_l0_active",
     "line": 2407
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_x",
     "line": 2416
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_y",
     "line": 2416
    },
    {
     "code": "i < ps_slice_hdr->i1_num_ref_idx_l0_active",
     "line": 2421
    },
    {
     "code": "ref_list_poc > cur_poc",
     "line": 2424
    },
    {
     "code": "ps_slice_hdr->i1_slice_type == BSLICE",
     "line": 2430
    },
    {
     "code": "i < ps_slice_hdr->i1_num_ref_idx_l1_active",
     "line": 2432
    },
    {
     "code": "ref_list_poc > cur_poc",
     "line": 2435
    },
    {
     "code": "ps_slice_hdr->i1_slice_type == ISLICE",
     "line": 2446
    },
    {
     "code": "ps_slice_hdr->i1_slice_type == PSLICE",
     "line": 2450
    },
    {
     "code": "(slice_qp) > (51)",
     "line": 2460
    },
    {
     "code": "(slice_qp) < (0)",
     "line": 2460
    },
    {
     "code": "0 == ps_slice_hdr->i1_dependent_slice_flag",
     "line": 2463
    },
    {
     "code": "1 == ps_slice_hdr->i1_dependent_slice_flag",
     "line": 2464
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_x",
     "line": 2464
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_y",
     "line": 2464
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2471
    },
    {
     "code": "1 == ps_slice_hdr->i1_dependent_slice_flag",
     "line": 2473
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_tile_x == 0",
     "line": 2473
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_tile_y == 0",
     "line": 2473
    },
    {
     "code": "0 == ps_pps->i1_entropy_coding_sync_enabled_flag",
     "line": 2475
    },
    {
     "code": "0 != ps_codec->s_parse.i4_ctb_x",
     "line": 2475
    },
    {
     "code": "0 == ps_pps->i1_entropy_coding_sync_enabled_flag",
     "line": 2481
    },
    {
     "code": "0 != ps_codec->s_parse.i4_ctb_x",
     "line": 2481
    },
    {
     "code": "ret != (IHEVCD_ERROR_T)IHEVCD_SUCCESS",
     "line": 2488
    },
    {
     "code": "1 == ps_codec->i4_num_cores",
     "line": 2504
    },
    {
     "code": "0 == cur_ctb_idx % RESET_TU_BUF_NCTB",
     "line": 2504
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_x",
     "line": 2522
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_y",
     "line": 2522
    },
    {
     "code": "ps_tile->u1_pos_x == 0",
     "line": 2523
    },
    {
     "code": "ps_tile->u1_pos_y == 0",
     "line": 2523
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_x",
     "line": 2524
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_y",
     "line": 2524
    },
    {
     "code": "(slice_qp) > (51)",
     "line": 2527
    },
    {
     "code": "(slice_qp) < (0)",
     "line": 2527
    },
    {
     "code": "slice_start_ctb_idx < tile_start_ctb_idx",
     "line": 2547
    },
    {
     "code": "((ps_slice_hdr->i2_ctb_x + ps_tile_prev->u2_wd) % ps_sps->i2_pic_wd_in_ctb) == ps_tile->u1_pos_x",
     "line": 2553
    },
    {
     "code": "ps_slice_hdr->i2_ctb_x > ps_tile->u1_pos_x",
     "line": 2558
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2577
    },
    {
     "code": "ret != (IHEVCD_ERROR_T)IHEVCD_SUCCESS",
     "line": 2584
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_x",
     "line": 2597
    },
    {
     "code": "1 < ps_codec->i4_num_cores",
     "line": 2600
    },
    {
     "code": "ret != (IHEVCD_ERROR_T)IHEVCD_SUCCESS",
     "line": 2613
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_x",
     "line": 2641
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2641
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_y",
     "line": 2646
    },
    {
     "code": "1 == ps_sps->i2_pic_wd_in_ctb",
     "line": 2648
    },
    {
     "code": "ret != (IHEVCD_ERROR_T)IHEVCD_SUCCESS",
     "line": 2661
    },
    {
     "code": "ret != (IHEVCD_ERROR_T)IHEVCD_SUCCESS",
     "line": 2677
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2689
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2719
    },
    {
     "code": "ret != (IHEVCD_ERROR_T)IHEVCD_SUCCESS",
     "line": 2736
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2767
    },
    {
     "code": "1 == ps_codec->s_parse.i4_ctb_x",
     "line": 2782
    },
    {
     "code": "(ps_codec->s_parse.i4_ctb_tile_x + 1) == (ps_tile->u2_wd)",
     "line": 2790
    },
    {
     "code": "(ps_codec->s_parse.i4_ctb_tile_y + 1) == ps_tile->u2_ht",
     "line": 2793
    },
    {
     "code": "0 == end_of_slice_flag",
     "line": 2796
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 2796
    },
    {
     "code": "ps_tile->u2_wd == (ps_codec->s_parse.i4_ctb_tile_x + 1)",
     "line": 2822
    },
    {
     "code": "ps_tile->u2_wd != ps_sps->i2_pic_wd_in_ctb",
     "line": 2822
    },
    {
     "code": "ps_tile->u2_ht == (ps_codec->s_parse.i4_ctb_tile_y + 1)",
     "line": 2825
    },
    {
     "code": "ps_tile->u2_wd + ps_tile->u1_pos_x == ps_sps->i2_pic_wd_in_ctb",
     "line": 2828
    },
    {
     "code": "ps_tile->u2_ht + ps_tile->u1_pos_y == ps_sps->i2_pic_ht_in_ctb",
     "line": 2828
    },
    {
     "code": "1 == ps_codec->i4_num_cores",
     "line": 2846
    },
    {
     "code": "0 == ctb_addr % RESET_TU_BUF_NCTB",
     "line": 2848
    },
    {
     "code": "ps_tile->u2_wd == (ps_codec->s_parse.i4_ctb_tile_x + 1)",
     "line": 2852
    },
    {
     "code": "ps_tile->u2_wd != ps_sps->i2_pic_wd_in_ctb",
     "line": 2852
    },
    {
     "code": "ps_tile->u2_ht == (ps_codec->s_parse.i4_ctb_tile_y + 1)",
     "line": 2855
    },
    {
     "code": "ps_tile->u2_wd + ps_tile->u1_pos_x == ps_sps->i2_pic_wd_in_ctb",
     "line": 2858
    },
    {
     "code": "ps_tile->u2_ht + ps_tile->u1_pos_y == ps_sps->i2_pic_ht_in_ctb",
     "line": 2858
    },
    {
     "code": "0 == ctb_addr % RESET_TU_BUF_NCTB",
     "line": 2860
    },
    {
     "code": "ps_tile->u2_wd == (ps_codec->s_parse.i4_ctb_tile_x + 1)",
     "line": 2876
    },
    {
     "code": "ps_tile->u2_wd != ps_sps->i2_pic_wd_in_ctb",
     "line": 2876
    },
    {
     "code": "ps_tile->u2_ht == (ps_codec->s_parse.i4_ctb_tile_y + 1)",
     "line": 2879
    },
    {
     "code": "ps_tile->u2_wd + ps_tile->u1_pos_x == ps_sps->i2_pic_wd_in_ctb",
     "line": 2882
    },
    {
     "code": "ps_tile->u2_ht + ps_tile->u1_pos_y == ps_sps->i2_pic_ht_in_ctb",
     "line": 2882
    },
    {
     "code": "0 != ps_codec->i4_disable_deblk_pic",
     "line": 2901
    },
    {
     "code": "1 == ps_slice_hdr->i1_slice_disable_deblocking_filter_flag",
     "line": 2902
    },
    {
     "code": "1 == ps_codec->i4_num_cores",
     "line": 2923
    },
    {
     "code": "i < i4_ctb_tu_cnt",
     "line": 2946
    },
    {
     "code": "0 == (start_pos_x & 1)",
     "line": 2959
    },
    {
     "code": "0 == (start_pos_y & 1)",
     "line": 2959
    },
    {
     "code": "row < start_pos_y + tu_size",
     "line": 2962
    },
    {
     "code": "col < start_pos_x + tu_size",
     "line": 2964
    },
    {
     "code": "slice_start_ctb_idx < tile_start_ctb_idx",
     "line": 2991
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_y",
     "line": 3001
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_y",
     "line": 3001
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_x",
     "line": 3008
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_x",
     "line": 3008
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_y",
     "line": 3012
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_y",
     "line": 3012
    },
    {
     "code": "(i2_wd_in_ctb - 1) != ps_codec->s_parse.i4_ctb_slice_x",
     "line": 3015
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_x > 0",
     "line": 3022
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_y",
     "line": 3024
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_tile_y",
     "line": 3024
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_x",
     "line": 3028
    },
    {
     "code": "(i2_wd_in_ctb - 1) != ps_codec->s_parse.i4_ctb_slice_x",
     "line": 3032
    },
    {
     "code": "1 == ps_codec->s_parse.i4_ctb_slice_y",
     "line": 3037
    },
    {
     "code": "0 == ps_codec->s_parse.i4_ctb_slice_x",
     "line": 3037
    },
    {
     "code": "(ps_sps->i2_pic_wd_in_ctb - 1) == ps_codec->s_parse.i4_ctb_x",
     "line": 3043
    },
    {
     "code": "(ps_tile->u2_wd - 1) == ps_codec->s_parse.i4_ctb_tile_x",
     "line": 3043
    },
    {
     "code": "PSLICE == ps_slice_hdr->i1_slice_type",
     "line": 3048
    },
    {
     "code": "BSLICE == ps_slice_hdr->i1_slice_type",
     "line": 3049
    },
    {
     "code": "ps_codec->i4_num_cores == 1",
     "line": 3060
    },
    {
     "code": "ps_codec->i4_num_cores == 1",
     "line": 3104
    },
    {
     "code": "pu_cnt < num_pu_per_ctb",
     "line": 3127
    },
    {
     "code": "row < pu_ht / MIN_PU_SIZE",
     "line": 3135
    },
    {
     "code": "col < pu_wd / MIN_PU_SIZE",
     "line": 3136
    },
    {
     "code": "(ctb_size) < (rows_remaining)",
     "line": 3147
    },
    {
     "code": "i < ctb_size / MIN_PU_SIZE",
     "line": 3152
    },
    {
     "code": "ctb_row < ctb_size_in_min_pu",
     "line": 3175
    },
    {
     "code": "ctb_col < ctb_size_in_min_pu",
     "line": 3177
    },
    {
     "code": "0 == ps_codec->i4_disable_deblk_pic",
     "line": 3194
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 3198
    },
    {
     "code": "ps_codec->i4_num_cores == 1",
     "line": 3206
    },
    {
     "code": "1 == ps_codec->i4_num_cores",
     "line": 3212
    },
    {
     "code": "ISLICE == ps_slice_hdr->i1_slice_type",
     "line": 3246
    },
    {
     "code": "0 != ps_slice_hdr->i1_slice_disable_deblocking_filter_flag",
     "line": 3257
    },
    {
     "code": "slice_start_ctb_idx < tile_start_ctb_idx",
     "line": 3303
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_slice_x == (ps_tile->u1_pos_x + ps_tile->u2_wd)",
     "line": 3305
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_slice_x == (ps_tile->u2_wd)",
     "line": 3313
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_slice_x == ps_tile->u2_wd",
     "line": 3321
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_tile_x == (ps_tile->u2_wd)",
     "line": 3330
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_tile_y == (ps_tile->u2_ht)",
     "line": 3339
    },
    {
     "code": "ps_tile->u2_ht + ps_tile->u1_pos_y  ==  ps_sps->i2_pic_ht_in_ctb",
     "line": 3346
    },
    {
     "code": "ps_tile->u2_wd + ps_tile->u1_pos_x  ==  ps_sps->i2_pic_wd_in_ctb",
     "line": 3346
    },
    {
     "code": "ps_codec->s_parse.i4_next_ctb_indx == next_slice_addr",
     "line": 3380
    },
    {
     "code": "1 == ps_codec->i4_num_cores",
     "line": 3387
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_tile_x == 0",
     "line": 3387
    },
    {
     "code": "(UWORD8 *)ps_codec->s_parse.s_bitstrm.pu1_buf_max + BITSTRM_OFF_THRS <",
     "line": 3398
    },
    {
     "code": "0 == ps_codec->i4_slice_error",
     "line": 3403
    },
    {
     "code": "0 == end_of_pic",
     "line": 3416
    },
    {
     "code": "1 == ps_codec->i4_num_cores",
     "line": 3427
    },
    {
     "code": "0 != (parse_slice_idx & (MAX_SLICE_HDR_CNT - 1))",
     "line": 3427
    },
    {
     "code": "ctb_indx != ps_sps->i4_pic_size_in_ctb",
     "line": 3438
    },
    {
     "code": "parse_status == proc_status",
     "line": 3443
    }
   ],
   "line_call_count": 13,
   "line_calls": [
    {
     "code": "ps_proc->u4_ctb_top_left_pu_idx = ps_proc->pu4_pic_pu_idx_top[(ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE) + ctb_size / MIN_PU_SIZE - 1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ps_proc->u4_ctb_top_left_pu_idx",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ps_proc->pu4_pic_pu_idx_top[(ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE) + ctb_size / MIN_PU_SIZE - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "ps_proc->pu4_pic_pu_idx_top",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE) + ctb_size / MIN_PU_SIZE - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "(ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE) + ctb_size / MIN_PU_SIZE",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_x * ctb_size / MIN_PU_SIZE",
     "name": "<operator>.division",
     "nargs": 2
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_x * ctb_size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "ps_codec->s_parse.i4_ctb_x",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ps_codec->s_parse",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "MIN_PU_SIZE",
     "name": "MIN_PU_SIZE",
     "nargs": 0
    },
    {
     "code": "ctb_size / MIN_PU_SIZE",
     "name": "<operator>.division",
     "nargs": 2
    },
    {
     "code": "MIN_PU_SIZE",
     "name": "MIN_PU_SIZE",
     "nargs": 0
    }
   ],
   "line_ids": [
    "ps_proc",
    "ps_codec",
    "ctb_size"
   ],
   "osv_id": "ARVO-42477544",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ihevcd_parse_slice_data"
  }
 },
 {
  "osv_id": "ARVO-42477558",
  "project": "libhevc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pu1_sao_src_top_left_chroma_bot_left",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 570,
    "type": "UWORD8*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "ihevcd_allocate_dynamic_bufs",
    "file": "/src/libhevc/decoder/ihevcd_api.c",
    "line": 1682
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "8",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3318,
    "fn": "ihevcd_sao_shift_ctb",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ihevcd_sao_shift_ctb",
    "file": "/src/libhevc/decoder/ihevcd_sao.c",
    "line": 3318
   },
   "code": "pu1_sao_src_top_left_chroma_bot_left[0] = pu1_src_chroma[(sao_ht_chroma)*src_strd + sao_wd_chroma - 2]",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ihevcd_sao_shift_ctb",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/cdd7c97c270408c330fcffd7d280e68b3678efe4/ARVO-42477558/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_cdd7c97c2704.cpg",
   "testcase_size": 251
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
   "dedup_token": "ihevcd_sao_shift_ctb--ihevcd_process--ihevcd_parse_slice_data"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pu1_sao_src_top_left_chroma_bot_left = ps_sao_ctxt->pu1_sao_src_top_left_chroma_bot_left + (2 * ps_sao_ctxt->i4_ctb_y)",
     "line": 607
    },
    {
     "code": "pu1_sao_src_top_left_chroma_bot_left[0] = pu1_src_chroma[(sao_ht_chroma)*src_strd + sao_wd_chroma - 2]",
     "line": 3318
    },
    {
     "code": "pu1_sao_src_top_left_chroma_bot_left[1] = pu1_src_chroma[(sao_ht_chroma)*src_strd + sao_wd_chroma - 1]",
     "line": 3319
    }
   ],
   "entity_decl": {
    "line": 570,
    "type": "UWORD8*"
   },
   "entity_name_cpg": "pu1_sao_src_top_left_chroma_bot_left",
   "func_lines": [
    526,
    3503
   ],
   "func_params": {
    "names": [
     "ps_sao_ctxt"
    ],
    "types": [
     "sao_ctxt_t*"
    ]
   },
   "guards": [
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 0",
     "line": 648
    },
    {
     "code": "i < (sao_blk_ht + (min_cu - 1)) >> log2_min_cu",
     "line": 655
    },
    {
     "code": "tmp_wd > 0",
     "line": 666
    },
    {
     "code": "((WORD32)(CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 670
    },
    {
     "code": "((WORD32)(CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 671
    },
    {
     "code": "row < min_cu",
     "line": 677
    },
    {
     "code": "col < MIN((WORD32)(CTZ(~u4_no_loop_filter_flag) << log2_min_cu), tmp_wd)",
     "line": 679
    },
    {
     "code": "((WORD32)(CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 679
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 684
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 685
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 0",
     "line": 727
    },
    {
     "code": "i < (sao_blk_ht + (min_cu - 1)) >> log2_min_cu",
     "line": 734
    },
    {
     "code": "tmp_wd > 0",
     "line": 745
    },
    {
     "code": "(((WORD32)CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 749
    },
    {
     "code": "(((WORD32)CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 750
    },
    {
     "code": "row < min_cu / 2",
     "line": 756
    },
    {
     "code": "col < MIN(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu), tmp_wd)",
     "line": 758
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 758
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 764
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 765
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 0",
     "line": 784
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y > 0",
     "line": 784
    },
    {
     "code": "0 == ps_sao->b3_y_type_idx",
     "line": 813
    },
    {
     "code": "row < sao_ht_luma",
     "line": 816
    },
    {
     "code": "1 == ps_sao->b3_y_type_idx",
     "line": 827
    },
    {
     "code": "i < 8",
     "line": 853
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_luma",
     "line": 884
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y > 1",
     "line": 884
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 1",
     "line": 884
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_luma",
     "line": 889
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_luma",
     "line": 917
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x == 1",
     "line": 919
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y == 1",
     "line": 928
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_x << log2_ctb_size) - sao_wd_luma",
     "line": 948
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_y << log2_ctb_size) - sao_ht_luma",
     "line": 957
    },
    {
     "code": "au4_idx_tl[5] > idx_tl",
     "line": 973
    },
    {
     "code": "i < 8",
     "line": 984
    },
    {
     "code": "au4_idx_tl[i] != idx_tl",
     "line": 987
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 1003
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 1003
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 1003
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 1003
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_luma",
     "line": 1017
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x == 1",
     "line": 1019
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y == 1",
     "line": 1028
    },
    {
     "code": "i < 8",
     "line": 1040
    },
    {
     "code": "au4_idx_tl[i] != idx_tl",
     "line": 1043
    },
    {
     "code": "i < 8",
     "line": 1055
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_x << log2_ctb_size) - sao_wd_luma",
     "line": 1066
    },
    {
     "code": "ps_sps->i2_pic_wd_in_ctb == ps_sao_ctxt->i4_ctb_x",
     "line": 1073
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_y << log2_ctb_size) - sao_ht_luma",
     "line": 1080
    },
    {
     "code": "ps_sps->i2_pic_ht_in_ctb == ps_sao_ctxt->i4_ctb_y",
     "line": 1086
    },
    {
     "code": "row < sao_ht_luma",
     "line": 1114
    },
    {
     "code": "0 == ps_sao->b3_cb_type_idx",
     "line": 1125
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 1127
    },
    {
     "code": "1 == ps_sao->b3_cb_type_idx",
     "line": 1139
    },
    {
     "code": "i < 8",
     "line": 1194
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_chroma",
     "line": 1205
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y > 1",
     "line": 1205
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 1",
     "line": 1205
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_chroma",
     "line": 1210
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_chroma",
     "line": 1237
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x == 1",
     "line": 1239
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y == 1",
     "line": 1248
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_x << log2_ctb_size) - sao_wd_chroma",
     "line": 1263
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_y << (log2_ctb_size - 1)) - sao_ht_chroma",
     "line": 1272
    },
    {
     "code": "i < 8",
     "line": 1291
    },
    {
     "code": "au4_idx_tl[i] != idx_tl",
     "line": 1294
    },
    {
     "code": "i < 8",
     "line": 1305
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 1313
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 1313
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 1313
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 1313
    },
    {
     "code": "0 == (1 << log2_ctb_size) - sao_wd_luma",
     "line": 1327
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x == 1",
     "line": 1329
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y == 1",
     "line": 1338
    },
    {
     "code": "i < 8",
     "line": 1350
    },
    {
     "code": "au4_idx_tl[i] != idx_tl",
     "line": 1353
    },
    {
     "code": "i < 8",
     "line": 1363
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_x << log2_ctb_size) - sao_wd_chroma",
     "line": 1374
    },
    {
     "code": "ps_sps->i2_pic_wd_in_ctb == ps_sao_ctxt->i4_ctb_x",
     "line": 1380
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_y << (log2_ctb_size - 1)) - sao_ht_chroma",
     "line": 1387
    },
    {
     "code": "ps_sps->i2_pic_ht_in_ctb == ps_sao_ctxt->i4_ctb_y",
     "line": 1393
    },
    {
     "code": "ctb_size == 16",
     "line": 1405
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y != ps_sps->i2_pic_ht_in_ctb - 1",
     "line": 1405
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 1446
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_y > 0",
     "line": 1464
    },
    {
     "code": "0 != sao_wd_luma",
     "line": 1503
    },
    {
     "code": "0 == ps_sao->b3_y_type_idx",
     "line": 1507
    },
    {
     "code": "row < sao_ht_luma",
     "line": 1510
    },
    {
     "code": "1 == ps_sao->b3_y_type_idx",
     "line": 1520
    },
    {
     "code": "i < 8",
     "line": 1550
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1595
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1612
    },
    {
     "code": "au4_idx_t[6] < idx_t",
     "line": 1632
    },
    {
     "code": "i < 8",
     "line": 1642
    },
    {
     "code": "au4_idx_t[i] != idx_t",
     "line": 1645
    },
    {
     "code": "i < 8",
     "line": 1656
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 1665
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 1665
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 1665
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 1665
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1671
    },
    {
     "code": "i < 8",
     "line": 1687
    },
    {
     "code": "au4_idx_t[i] != idx_t",
     "line": 1690
    },
    {
     "code": "i < 8",
     "line": 1700
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1712
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_y << log2_ctb_size) - sao_ht_luma",
     "line": 1726
    },
    {
     "code": "ps_sps->i2_pic_ht_in_ctb == ps_sao_ctxt->i4_ctb_y",
     "line": 1733
    },
    {
     "code": "row < sao_ht_luma",
     "line": 1760
    },
    {
     "code": "0 != sao_wd_chroma",
     "line": 1770
    },
    {
     "code": "0 == ps_sao->b3_cb_type_idx",
     "line": 1774
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 1777
    },
    {
     "code": "1 == ps_sao->b3_cb_type_idx",
     "line": 1789
    },
    {
     "code": "i < 8",
     "line": 1844
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1872
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1890
    },
    {
     "code": "idx_t > au4_idx_t[6]",
     "line": 1908
    },
    {
     "code": "i < 8",
     "line": 1917
    },
    {
     "code": "au4_idx_t[i] != idx_t",
     "line": 1920
    },
    {
     "code": "i < 8",
     "line": 1931
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 1939
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 1939
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 1939
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 1939
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1945
    },
    {
     "code": "i < 8",
     "line": 1961
    },
    {
     "code": "au4_idx_t[i] != idx_t",
     "line": 1964
    },
    {
     "code": "i < 8",
     "line": 1973
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 1984
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_y << (log2_ctb_size - 1)) - sao_ht_chroma",
     "line": 1998
    },
    {
     "code": "ps_sps->i2_pic_ht_in_ctb == ps_sao_ctxt->i4_ctb_y",
     "line": 2005
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 2054
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 0",
     "line": 2072
    },
    {
     "code": "0 != sao_ht_luma",
     "line": 2111
    },
    {
     "code": "0 == ps_sao->b3_y_type_idx",
     "line": 2115
    },
    {
     "code": "row < sao_ht_luma",
     "line": 2118
    },
    {
     "code": "1 == ps_sao->b3_y_type_idx",
     "line": 2129
    },
    {
     "code": "i < 8",
     "line": 2155
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2200
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2217
    },
    {
     "code": "idx_l < au4_idx_l[5]",
     "line": 2234
    },
    {
     "code": "i < 8",
     "line": 2243
    },
    {
     "code": "au4_idx_l[i] != idx_l",
     "line": 2246
    },
    {
     "code": "i < 8",
     "line": 2256
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 2265
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 2265
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 2265
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 2265
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2270
    },
    {
     "code": "i < 8",
     "line": 2287
    },
    {
     "code": "au4_idx_l[i] != idx_l",
     "line": 2290
    },
    {
     "code": "i < 8",
     "line": 2300
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_x << log2_ctb_size) - sao_wd_luma",
     "line": 2310
    },
    {
     "code": "ps_sps->i2_pic_wd_in_ctb == ps_sao_ctxt->i4_ctb_x",
     "line": 2316
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2323
    },
    {
     "code": "row < sao_ht_luma",
     "line": 2358
    },
    {
     "code": "0 != sao_ht_chroma",
     "line": 2369
    },
    {
     "code": "0 == ps_sao->b3_cb_type_idx",
     "line": 2373
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 2375
    },
    {
     "code": "1 == ps_sao->b3_cb_type_idx",
     "line": 2386
    },
    {
     "code": "i < 8",
     "line": 2442
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2470
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2487
    },
    {
     "code": "au4_idx_l[5] > idx_l",
     "line": 2499
    },
    {
     "code": "i < 8",
     "line": 2512
    },
    {
     "code": "au4_idx_l[i] != idx_l",
     "line": 2515
    },
    {
     "code": "i < 8",
     "line": 2525
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 2533
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 2533
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 2533
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 2533
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2538
    },
    {
     "code": "i < 8",
     "line": 2555
    },
    {
     "code": "au4_idx_l[i] != idx_l",
     "line": 2558
    },
    {
     "code": "i < 8",
     "line": 2567
    },
    {
     "code": "0 == (ps_sao_ctxt->i4_ctb_x << log2_ctb_size) - sao_wd_chroma",
     "line": 2577
    },
    {
     "code": "ps_sps->i2_pic_wd_in_ctb == ps_sao_ctxt->i4_ctb_x",
     "line": 2584
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2591
    },
    {
     "code": "ctb_size == 16",
     "line": 2612
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x != ps_sps->i2_pic_wd_in_ctb - 1",
     "line": 2612
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 2655
    },
    {
     "code": "0 != sao_wd_luma",
     "line": 2713
    },
    {
     "code": "0 != sao_ht_luma",
     "line": 2713
    },
    {
     "code": "0 == ps_sao->b3_y_type_idx",
     "line": 2717
    },
    {
     "code": "row < sao_ht_luma",
     "line": 2720
    },
    {
     "code": "1 == ps_sao->b3_y_type_idx",
     "line": 2732
    },
    {
     "code": "i < 8",
     "line": 2758
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 2803
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2814
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 2829
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2840
    },
    {
     "code": "au4_idx_c[6] < idx_c",
     "line": 2855
    },
    {
     "code": "i < 8",
     "line": 2864
    },
    {
     "code": "au4_idx_c[i] != idx_c",
     "line": 2867
    },
    {
     "code": "i < 8",
     "line": 2877
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 2886
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 2886
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 2886
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 2886
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 2891
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2902
    },
    {
     "code": "i < 8",
     "line": 2917
    },
    {
     "code": "au4_idx_c[i] != idx_c",
     "line": 2920
    },
    {
     "code": "i < 8",
     "line": 2930
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 2941
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 2955
    },
    {
     "code": "row < sao_ht_luma",
     "line": 2992
    },
    {
     "code": "0 != sao_wd_chroma",
     "line": 3004
    },
    {
     "code": "0 != sao_ht_chroma",
     "line": 3004
    },
    {
     "code": "0 == ps_sao->b3_cb_type_idx",
     "line": 3008
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 3010
    },
    {
     "code": "1 == ps_sao->b3_cb_type_idx",
     "line": 3024
    },
    {
     "code": "i < 8",
     "line": 3080
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 3107
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 3118
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 3133
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 3145
    },
    {
     "code": "idx_c > au4_idx_c[6]",
     "line": 3161
    },
    {
     "code": "i < 8",
     "line": 3170
    },
    {
     "code": "au4_idx_c[i] != idx_c",
     "line": 3173
    },
    {
     "code": "i < 8",
     "line": 3183
    },
    {
     "code": "ps_tile->u1_pos_x == ps_sao_ctxt->i4_ctb_x",
     "line": 3192
    },
    {
     "code": "ps_tile->u1_pos_y == ps_sao_ctxt->i4_ctb_y",
     "line": 3192
    },
    {
     "code": "0 == ps_tile->u1_pos_x",
     "line": 3192
    },
    {
     "code": "0 == ps_tile->u1_pos_y",
     "line": 3192
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 3197
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 3208
    },
    {
     "code": "i < 8",
     "line": 3223
    },
    {
     "code": "au4_idx_c[i] != idx_c",
     "line": 3226
    },
    {
     "code": "i < 8",
     "line": 3236
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_x",
     "line": 3247
    },
    {
     "code": "0 == ps_sao_ctxt->i4_ctb_y",
     "line": 3261
    },
    {
     "code": "row < sao_ht_chroma",
     "line": 3323
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 0",
     "line": 3372
    },
    {
     "code": "i < (sao_blk_ht + (min_cu - 1)) >> log2_min_cu",
     "line": 3379
    },
    {
     "code": "tmp_wd > 0",
     "line": 3389
    },
    {
     "code": "(((WORD32)CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3393
    },
    {
     "code": "(((WORD32)CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3394
    },
    {
     "code": "row < min_cu",
     "line": 3400
    },
    {
     "code": "col < MIN(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu), tmp_wd)",
     "line": 3402
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3402
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3407
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3408
    },
    {
     "code": "ps_sao_ctxt->i4_ctb_x > 0",
     "line": 3450
    },
    {
     "code": "i < (sao_blk_ht + (min_cu - 1)) >> log2_min_cu",
     "line": 3457
    },
    {
     "code": "tmp_wd > 0",
     "line": 3467
    },
    {
     "code": "(((WORD32)CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3471
    },
    {
     "code": "(((WORD32)CTZ(u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3472
    },
    {
     "code": "row < min_cu / 2",
     "line": 3478
    },
    {
     "code": "col < MIN(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu), tmp_wd)",
     "line": 3480
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3480
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3486
    },
    {
     "code": "(((WORD32)CTZ(~u4_no_loop_filter_flag) << log2_min_cu)) < (tmp_wd)",
     "line": 3487
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "pu1_sao_src_top_left_chroma_bot_left[0] = pu1_src_chroma[(sao_ht_chroma)*src_strd + sao_wd_chroma - 2]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "pu1_sao_src_top_left_chroma_bot_left[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pu1_src_chroma[(sao_ht_chroma)*src_strd + sao_wd_chroma - 2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "(sao_ht_chroma)*src_strd + sao_wd_chroma - 2",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "(sao_ht_chroma)*src_strd + sao_wd_chroma",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(sao_ht_chroma)*src_strd",
     "name": "<operator>.multiplication",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pu1_sao_src_top_left_chroma_bot_left",
    "pu1_src_chroma",
    "sao_ht_chroma",
    "src_strd",
    "sao_wd_chroma"
   ],
   "osv_id": "ARVO-42477558",
   "sites": [
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au1_avail_luma[8]",
     "line": 542
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au1_avail_chroma[8]",
     "line": 543
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au1_tile_slice_boundary[8]",
     "line": 544
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au4_ilf_across_tile_slice_enable[8]",
     "line": 545
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "au1_src_top_right[2]",
     "line": 551
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "au1_src_bot_left[2]",
     "line": 552
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "ai1_offset_y[8]",
     "line": 573
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "ai1_offset_cb[8]",
     "line": 574
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "ai1_offset_cr[8]",
     "line": 575
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au4_idx_tl[8]",
     "line": 793
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au4_idx_t[8]",
     "line": 1473
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au4_idx_l[8]",
     "line": 2081
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "au4_idx_c[8]",
     "line": 2681
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ihevcd_sao_shift_ctb"
  }
 },
 {
  "osv_id": "ARVO-42477573",
  "project": "libspng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "next_filter",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1819,
    "type": "uint8_t",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/libspng/tests/spng_read_fuzzer.cc",
    "line": 65
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "7",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2068,
    "fn": "spng_decode_image",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "spng_decode_image",
    "file": "/src/libspng/spng.c",
    "line": 2068
   },
   "code": "memcpy(&next_filter, scanline + scanline_width - 1, 1)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "spng_decode_image",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libspng/address/d48a9fa212cee4c05c51178b9c7813cd1299dcb3/ARVO-42477573/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_d48a9fa212ce.cpg",
   "testcase_size": 51
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
   "dedup_token": "spng_decode_image--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "next_filter = 0",
     "line": 1819
    }
   ],
   "entity_decl": {
    "line": 1819,
    "type": "uint8_t"
   },
   "entity_name_cpg": "next_filter",
   "func_lines": [
    1766,
    2328
   ],
   "func_params": {
    "names": [
     "ctx",
     "out",
     "out_size",
     "fmt",
     "flags"
    ],
    "types": [
     "spng_ctx*",
     "unsigned char*",
     "size_t",
     "int",
     "int"
    ]
   },
   "guards": [
    {
     "code": "ctx == NULL",
     "line": 1768
    },
    {
     "code": "out == NULL",
     "line": 1769
    },
    {
     "code": "out_size < out_size_required",
     "line": 1778
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_TRUECOLOR",
     "line": 1784
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_GRAYSCALE_ALPHA",
     "line": 1785
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_TRUECOLOR_ALPHA",
     "line": 1786
    },
    {
     "code": "ctx->ihdr.bit_depth < 8",
     "line": 1790
    },
    {
     "code": "inflateInit(&stream) != Z_OK",
     "line": 1798
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_INDEXED",
     "line": 1811
    },
    {
     "code": "fmt == SPNG_FMT_RGBA16",
     "line": 1836
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_TRUECOLOR_ALPHA",
     "line": 1842
    },
    {
     "code": "ctx->ihdr.bit_depth == depth_target",
     "line": 1843
    },
    {
     "code": "scanline == NULL",
     "line": 1868
    },
    {
     "code": "prev_scanline == NULL",
     "line": 1868
    },
    {
     "code": "row == NULL",
     "line": 1868
    },
    {
     "code": "fmt == SPNG_FMT_RGBA8",
     "line": 1883
    },
    {
     "code": "ctx->gamma_lut == NULL",
     "line": 1896
    },
    {
     "code": "FP_ZERO == fpclassify(exponent)",
     "line": 1907
    },
    {
     "code": "i < lut_entries",
     "line": 1915
    },
    {
     "code": "ctx->ihdr.color_type == 0",
     "line": 1934
    },
    {
     "code": "ctx->ihdr.color_type == 2",
     "line": 1939
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1939
    },
    {
     "code": "ctx->ihdr.color_type == 4",
     "line": 1946
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 1960
    },
    {
     "code": "fmt == SPNG_FMT_RGBA8",
     "line": 1960
    },
    {
     "code": "depth_target > 16",
     "line": 1972
    },
    {
     "code": "processing_depth > 16",
     "line": 1973
    },
    {
     "code": "sb.grayscale_bits > processing_depth",
     "line": 1974
    },
    {
     "code": "sb.alpha_bits > processing_depth",
     "line": 1975
    },
    {
     "code": "sb.red_bits > processing_depth",
     "line": 1976
    },
    {
     "code": "sb.green_bits > processing_depth",
     "line": 1977
    },
    {
     "code": "sb.blue_bits > processing_depth",
     "line": 1978
    },
    {
     "code": "sb.red_bits == sb.green_bits",
     "line": 1984
    },
    {
     "code": "sb.green_bits == sb.blue_bits",
     "line": 1985
    },
    {
     "code": "sb.blue_bits == sb.alpha_bits",
     "line": 1986
    },
    {
     "code": "sb.alpha_bits == processing_depth",
     "line": 1987
    },
    {
     "code": "processing_depth == depth_target",
     "line": 1988
    },
    {
     "code": "i < 256",
     "line": 1995
    },
    {
     "code": "i < ctx->trns.n_type3_entries",
     "line": 1997
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_TRUECOLOR",
     "line": 2021
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 2023
    },
    {
     "code": "pass < 7",
     "line": 2040
    },
    {
     "code": "sub[pass].width == 0",
     "line": 2043
    },
    {
     "code": "sub[pass].height == 0",
     "line": 2043
    },
    {
     "code": "scanline_idx < sub[pass].height",
     "line": 2058
    },
    {
     "code": "scanline_idx == (sub[pass].height - 1)",
     "line": 2061
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 2070
    },
    {
     "code": "k < width",
     "line": 2082
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_TRUECOLOR",
     "line": 2095
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 2097
    },
    {
     "code": "fmt == SPNG_FMT_RGBA8",
     "line": 2107
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_INDEXED",
     "line": 2120
    },
    {
     "code": "ctx->ihdr.bit_depth == 8",
     "line": 2124
    },
    {
     "code": "shift_amount > 8",
     "line": 2132
    },
    {
     "code": "fmt == SPNG_FMT_RGBA8",
     "line": 2139
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_TRUECOLOR_ALPHA",
     "line": 2163
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 2165
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_GRAYSCALE",
     "line": 2180
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 2182
    },
    {
     "code": "ctx->trns.gray == gray_16",
     "line": 2186
    },
    {
     "code": "shift_amount > 8",
     "line": 2197
    },
    {
     "code": "ctx->trns.gray == gray_8",
     "line": 2203
    },
    {
     "code": "ctx->ihdr.color_type == SPNG_COLOR_TYPE_GRAYSCALE_ALPHA",
     "line": 2209
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 2211
    },
    {
     "code": "fmt == SPNG_FMT_RGBA8",
     "line": 2232
    },
    {
     "code": "ctx->ihdr.bit_depth == 16",
     "line": 2234
    },
    {
     "code": "fmt == SPNG_FMT_RGBA16",
     "line": 2247
    },
    {
     "code": "ctx->ihdr.bit_depth != 16",
     "line": 2249
    },
    {
     "code": "k < width",
     "line": 2282
    },
    {
     "code": "scanline_idx != (sub[pass].height - 1)",
     "line": 2292
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(&next_filter, scanline + scanline_width - 1, 1)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&next_filter",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "scanline + scanline_width - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "scanline + scanline_width",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "next_filter",
    "scanline",
    "scanline_width"
   ],
   "osv_id": "ARVO-42477573",
   "sites": [
    {
     "args": "7",
     "callee": "<operator>.alloc",
     "code": "sub[7]",
     "line": 1849
    },
    {
     "args": "ctx ;; scanline_width",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, scanline_width)",
     "line": 1858
    },
    {
     "args": "ctx ;; scanline_width",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, scanline_width)",
     "line": 1859
    },
    {
     "args": "ctx ;; out_width",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, out_width)",
     "line": 1863
    },
    {
     "args": "ctx ;; lut_entries * sizeof(uint16_t)",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, lut_entries * sizeof(uint16_t))",
     "line": 1895
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "plte[256]",
     "line": 1990
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "trns_px[8]",
     "line": 2019
    },
    {
     "args": "7",
     "callee": "<operator>.alloc",
     "code": "adam7_x_start[7] = { 0, 4, 0, 2, 0, 1, 0 }",
     "line": 2277
    },
    {
     "args": "7",
     "callee": "<operator>.alloc",
     "code": "adam7_y_start[7] = { 0, 0, 4, 0, 2, 0, 1 }",
     "line": 2278
    },
    {
     "args": "7",
     "callee": "<operator>.alloc",
     "code": "adam7_x_delta[7] = { 8, 8, 4, 4, 2, 2, 1 }",
     "line": 2279
    },
    {
     "args": "7",
     "callee": "<operator>.alloc",
     "code": "adam7_y_delta[7] = { 8, 8, 8, 4, 4, 2, 2 }",
     "line": 2280
    },
    {
     "args": "ctx ;; row",
     "callee": "spng__free",
     "code": "spng__free(ctx, row)",
     "line": 2311
    },
    {
     "args": "ctx ;; scanline_buf",
     "callee": "spng__free",
     "code": "spng__free(ctx, scanline_buf)",
     "line": 2312
    },
    {
     "args": "ctx ;; prev_scanline_buf",
     "callee": "spng__free",
     "code": "spng__free(ctx, prev_scanline_buf)",
     "line": 2313
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "spng_decode_image"
  }
 },
 {
  "osv_id": "ARVO-42477586",
  "project": "libhevc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pu4_vert_bs",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 214,
    "type": "UWORD32*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "ihevcd_allocate_dynamic_bufs",
    "file": "/src/libhevc/decoder/ihevcd_api.c",
    "line": 1830
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 452,
    "fn": "ihevcd_ctb_boundary_strength_islice",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ihevcd_ctb_boundary_strength_islice",
    "file": "/src/libhevc/decoder/ihevcd_boundary_strength.c",
    "line": 452
   },
   "code": "memset(((UWORD8 *)pu4_vert_bs) + offset, 0, 1 << (log2_ctb_size - 4))",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ihevcd_ctb_boundary_strength_islice",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/cdd7c97c270408c330fcffd7d280e68b3678efe4/ARVO-42477586/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_cdd7c97c2704.cpg",
   "testcase_size": 473
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
   "dedup_token": "__asan_memset--ihevcd_ctb_boundary_strength_islice--ihevcd_parse_slice_data"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pu4_vert_bs = (UWORD32 *)((UWORD8 *)ps_bs_ctxt->pu4_pic_vert_bs +",
     "line": 247
    }
   ],
   "entity_decl": {
    "line": 214,
    "type": "UWORD32*"
   },
   "entity_name_cpg": "pu4_vert_bs",
   "func_lines": [
    209,
    457
   ],
   "func_params": {
    "names": [
     "ps_bs_ctxt"
    ],
    "types": [
     "bs_ctxt_t*"
    ]
   },
   "guards": [
    {
     "code": "0 != ps_bs_ctxt->i4_ctb_x",
     "line": 276
    },
    {
     "code": "0 != ps_bs_ctxt->i4_ctb_y",
     "line": 282
    },
    {
     "code": "i < i4_tu_cnt",
     "line": 293
    },
    {
     "code": "0 == (start_pos_x & 1)",
     "line": 313
    },
    {
     "code": "6 != log2_ctb_size",
     "line": 321
    },
    {
     "code": "0 == (start_pos_y & 1)",
     "line": 326
    },
    {
     "code": "6 != log2_ctb_size",
     "line": 334
    },
    {
     "code": "0 == u4_qp_const_in_ctb",
     "line": 340
    },
    {
     "code": "0 == (start_pos_x & 1)",
     "line": 342
    },
    {
     "code": "0 == (start_pos_y & 1)",
     "line": 342
    },
    {
     "code": "row < start_pos_y + tu_size",
     "line": 345
    },
    {
     "code": "col < start_pos_x + tu_size",
     "line": 347
    },
    {
     "code": "0 == i1_loop_filter_across_tiles_enabled_flag",
     "line": 363
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_tile_x",
     "line": 363
    },
    {
     "code": "0 == i1_loop_filter_across_slices_enabled_flag",
     "line": 364
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_slice_x",
     "line": 364
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_slice_y",
     "line": 364
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_x",
     "line": 365
    },
    {
     "code": "64 == ctb_size",
     "line": 367
    },
    {
     "code": "0 == i1_loop_filter_across_tiles_enabled_flag",
     "line": 373
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_tile_x",
     "line": 373
    },
    {
     "code": "64 == ctb_size",
     "line": 375
    },
    {
     "code": "ps_bs_ctxt->ps_slice_hdr->i1_dependent_slice_flag == 1",
     "line": 387
    },
    {
     "code": "slice_idx == left_slice_idx",
     "line": 387
    },
    {
     "code": "0 == i1_loop_filter_across_slices_enabled_flag",
     "line": 390
    },
    {
     "code": "slice_idx != left_slice_idx",
     "line": 391
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_slice_y",
     "line": 391
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_tile_x",
     "line": 392
    },
    {
     "code": "slice_idx != left_slice_idx",
     "line": 392
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_x",
     "line": 393
    },
    {
     "code": "64 == ctb_size",
     "line": 395
    },
    {
     "code": "0 == i1_loop_filter_across_tiles_enabled_flag",
     "line": 411
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_tile_y",
     "line": 411
    },
    {
     "code": "0 == i1_loop_filter_across_slices_enabled_flag",
     "line": 412
    },
    {
     "code": "slice_idx != top_slice_idx",
     "line": 412
    },
    {
     "code": "0 == ps_bs_ctxt->i4_ctb_y",
     "line": 413
    },
    {
     "code": "64 == ctb_size",
     "line": 415
    },
    {
     "code": "num_rows_remaining < (ctb_size >> 3)",
     "line": 426
    },
    {
     "code": "6 != log2_ctb_size",
     "line": 434
    },
    {
     "code": "num_cols_remaining < (ctb_size >> 3)",
     "line": 440
    },
    {
     "code": "6 != log2_ctb_size",
     "line": 449
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "memset(((UWORD8 *)pu4_vert_bs) + offset, 0, 1 << (log2_ctb_size - 4))",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "((UWORD8 *)pu4_vert_bs) + offset",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(UWORD8 *)pu4_vert_bs",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "1 << (log2_ctb_size - 4)",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "log2_ctb_size - 4",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pu4_vert_bs",
    "offset",
    "log2_ctb_size"
   ],
   "osv_id": "ARVO-42477586",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ihevcd_ctb_boundary_strength_islice"
  }
 },
 {
  "osv_id": "ARVO-42477643",
  "project": "libhevc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "lb_avail",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 360,
    "type": "WORD32",
    "size": null
   }
  },
  "alloc": {
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 442,
    "fn": "ihevcd_mv_pred",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ihevcd_mv_pred",
    "file": "/src/libhevc/decoder/ihevcd_mv_pred.c",
    "line": 442
   },
   "code": "lb_avail && (!ps_pic_pu[pu_idx_a0].b1_intra_flag)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ihevcd_mv_pred",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/a469393436a31721cc47533e6479ace24e81f6a4/ARVO-42477643/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_a469393436a3.cpg",
   "testcase_size": 960
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
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "ihevcd_mv_pred--ihevcd_get_mv_ctb--ihevcd_parse_slice_data"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 360,
    "type": "WORD32"
   },
   "entity_name_cpg": "lb_avail",
   "func_lines": [
    354,
    750
   ],
   "func_params": {
    "names": [
     "ps_mv_ctxt",
     "pu4_top_pu_idx",
     "pu4_left_pu_idx",
     "pu4_top_left_pu_idx",
     "left_nbr_4x4_strd",
     "ps_pu",
     "lb_avail",
     "l_avail",
     "tr_avail",
     "t_avail",
     "tl_avail",
     "ps_pred_mv"
    ],
    "types": [
     "mv_ctxt_t*",
     "UWORD32*",
     "UWORD32*",
     "UWORD32*",
     "WORD32",
     "pu_t*",
     "WORD32",
     "WORD32",
     "WORD32",
     "WORD32",
     "WORD32",
     "pu_mv_t*"
    ]
   },
   "guards": [
    {
     "code": "PSLICE == ps_slice_hdr->i1_slice_type",
     "line": 410
    },
    {
     "code": "nbr_avail[0] == 1",
     "line": 456
    },
    {
     "code": "0 == avail_a_flag[0]",
     "line": 466
    },
    {
     "code": "PRED_L0 != ps_pu->b2_pred_mode",
     "line": 472
    },
    {
     "code": "0 == avail_a_flag[1]",
     "line": 475
    },
    {
     "code": "PRED_L1 == ps_pu->b2_pred_mode",
     "line": 481
    },
    {
     "code": "PRED_L0 == ps_pu->b2_pred_mode",
     "line": 482
    },
    {
     "code": "max_l0_mvp_cand == num_l0_mvp_cand",
     "line": 487
    },
    {
     "code": "max_l1_mvp_cand == num_l1_mvp_cand",
     "line": 496
    },
    {
     "code": "PRED_L0 != ps_pu->b2_pred_mode",
     "line": 579
    },
    {
     "code": "0 == num_l0_mvp_cand",
     "line": 587
    },
    {
     "code": "as_mv_a[0].i2_mvx != as_mv_b[0].i2_mvx",
     "line": 588
    },
    {
     "code": "as_mv_a[0].i2_mvy != as_mv_b[0].i2_mvy",
     "line": 589
    },
    {
     "code": "max_l0_mvp_cand == num_l0_mvp_cand",
     "line": 592
    },
    {
     "code": "0 == num_l1_mvp_cand",
     "line": 601
    },
    {
     "code": "as_mv_a[1].i2_mvx != as_mv_b[1].i2_mvx",
     "line": 602
    },
    {
     "code": "as_mv_a[1].i2_mvy != as_mv_b[1].i2_mvy",
     "line": 603
    },
    {
     "code": "max_l1_mvp_cand == num_l1_mvp_cand",
     "line": 606
    },
    {
     "code": "is_scaled_flag_list == 0",
     "line": 616
    },
    {
     "code": "avail_b_flag[0] == 1",
     "line": 616
    },
    {
     "code": "is_scaled_flag_list == 0",
     "line": 621
    },
    {
     "code": "avail_b_flag[1] == 1",
     "line": 621
    },
    {
     "code": "0 == is_scaled_flag_list",
     "line": 627
    },
    {
     "code": "PRED_L0 != ps_pu->b2_pred_mode",
     "line": 633
    },
    {
     "code": "0 == num_l0_mvp_cand",
     "line": 640
    },
    {
     "code": "as_mv_a[0].i2_mvx != as_mv_b[0].i2_mvx",
     "line": 641
    },
    {
     "code": "as_mv_a[0].i2_mvy != as_mv_b[0].i2_mvy",
     "line": 642
    },
    {
     "code": "max_l0_mvp_cand == num_l0_mvp_cand",
     "line": 645
    },
    {
     "code": "0 == num_l1_mvp_cand",
     "line": 654
    },
    {
     "code": "as_mv_a[1].i2_mvx != as_mv_b[1].i2_mvx",
     "line": 655
    },
    {
     "code": "as_mv_a[1].i2_mvy != as_mv_b[1].i2_mvy",
     "line": 656
    },
    {
     "code": "max_l1_mvp_cand == num_l1_mvp_cand",
     "line": 659
    },
    {
     "code": "2 != num_l0_mvp_cand",
     "line": 672
    },
    {
     "code": "2 != num_l1_mvp_cand",
     "line": 672
    },
    {
     "code": "avail_col_l0 == 0",
     "line": 690
    },
    {
     "code": "avail_col_l1 == 0",
     "line": 690
    },
    {
     "code": "avail_col_l0 == 0",
     "line": 697
    },
    {
     "code": "avail_col_l1 == 0",
     "line": 701
    },
    {
     "code": "2 != num_l0_mvp_cand",
     "line": 713
    },
    {
     "code": "max_l0_mvp_cand == num_l0_mvp_cand",
     "line": 716
    },
    {
     "code": "2 != num_l1_mvp_cand",
     "line": 725
    },
    {
     "code": "max_l1_mvp_cand == num_l1_mvp_cand",
     "line": 728
    },
    {
     "code": "0 == l0_done_flag",
     "line": 739
    },
    {
     "code": "0 == l1_done_flag",
     "line": 744
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "lb_avail && (!ps_pic_pu[pu_idx_a0].b1_intra_flag)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "!ps_pic_pu[pu_idx_a0].b1_intra_flag",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "ps_pic_pu[pu_idx_a0].b1_intra_flag",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "ps_pic_pu[pu_idx_a0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "lb_avail",
    "ps_pic_pu",
    "pu_idx_a0"
   ],
   "osv_id": "ARVO-42477643",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "*ps_ref_pic_list[2]",
     "line": 368
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "avail_a_flag[2]",
     "line": 374
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "as_mv_a[2]",
     "line": 375
    },
    {
     "args": "3",
     "callee": "<operator>.alloc",
     "code": "nbr_avail[3]",
     "line": 381
    },
    {
     "args": "3",
     "callee": "<operator>.alloc",
     "code": "*aps_nbr_pu[3]",
     "line": 382
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "avail_b_flag[2]",
     "line": 510
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "as_mv_b[2]",
     "line": 511
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "as_mv_col[2]",
     "line": 674
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "avail_col_flag[2] = { 0 }",
     "line": 675
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ihevcd_mv_pred"
  }
 },
 {
  "osv_id": "ARVO-42479042",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "stderr",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "sam_realloc_bam_data",
    "file": "/src/htslib/sam.c",
    "line": 386
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3861,
    "fn": "hts_log",
    "code": "vfprintf(stderr, format, argptr)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hts_log",
    "file": "/src/htslib/hts.c",
    "line": 3861
   },
   "code": "vfprintf(stderr, format, argptr)",
   "access": {
    "dir": "READ",
    "width": 65,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "hts_log",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:3855"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "context",
   "format"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/dd6f0b72c92591252bb77818663629cc1a129949/ARVO-42479042/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_dd6f0b72c925.cpg",
   "testcase_size": 165
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
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--hts_log--bam_read1"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "stderr",
   "func_lines": [
    3852,
    3867
   ],
   "func_params": {
    "names": [
     "severity",
     "context",
     "format"
    ],
    "types": [
     "htsLogLevel",
     "char*",
     "char*"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "vfprintf(stderr, format, argptr)",
     "name": "vfprintf",
     "nargs": 3
    }
   ],
   "line_ids": [
    "stderr",
    "format",
    "argptr"
   ],
   "osv_id": "ARVO-42479042",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "hts_log"
  }
 },
 {
  "osv_id": "ARVO-42479230",
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
    "fn": "walk_exports",
    "file": "/src/radare2/libr/../libr/bin/p/../format/mach0/mach0.c",
    "line": 1940
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2017,
    "fn": "walk_exports",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "walk_exports",
    "file": "/src/radare2/libr/bin/format/mach0/mach0.c",
    "line": 2017
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "walk_exports",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/c0779bd604b251fc97befebfdc870527b3947379/ARVO-42479230/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_c0779bd604b2.cpg",
   "testcase_size": 65843
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
   "dedup_token": "strlen--walk_exports--get_symbols"
  },
  "deep": {
   "osv_id": "ARVO-42479230"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "walk_exports"
  }
 },
 {
  "osv_id": "ARVO-42479685",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/mail_smtp.c",
    "line": 67,
    "size": null,
    "type": "ndpi_flow_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "ndpi_base64_decode",
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "line": 811
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "48",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 177,
    "fn": "ndpi_search_mail_smtp_tcp",
    "code": "snprintf(flow->protos.ftp_imap_pop_smtp.password,",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_mail_smtp_tcp",
    "file": "/src/ndpi/src/lib/protocols/mail_smtp.c",
    "line": 177
   },
   "code": "snprintf(flow->protos.ftp_imap_pop_smtp.password,",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_mail_smtp_tcp",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:72,FOR:81,IF:83,IF:84,ELSE:86,IF:86,ELSE:88,IF:88,ELSE:90,IF:90,ELSE:92,IF:92"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_flow_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ndpi_struct",
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479685/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "testcase_size": 99
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
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--snprintf--ndpi_search_mail_smtp_tcp"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->protos.ftp_imap_pop_smtp.auth_found = 0",
     "line": 107
    },
    {
     "code": "flow->protos.ftp_imap_pop_smtp.auth_found = 0",
     "line": 114
    },
    {
     "code": "flow->protos.ftp_imap_pop_smtp.auth_found = 0",
     "line": 121
    },
    {
     "code": "flow->protos.ftp_imap_pop_smtp.auth_found = 1",
     "line": 132
    }
   ],
   "entity_decl": {
    "line": 67,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    66,
    263
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
     "code": "packet->payload_packet_len > 2",
     "line": 72
    },
    {
     "code": "packet->parsed_lines <  NDPI_MAX_PARSE_LINES_PER_PACKET",
     "line": 73
    },
    {
     "code": "ntohs(get_u_int16_t(packet->payload, packet->payload_packet_len - 2)) == 0x0d0a",
     "line": 74
    },
    {
     "code": "a < packet->parsed_lines",
     "line": 81
    },
    {
     "code": "memcmp(packet->line[a].ptr, \"220\", 3) == 0",
     "line": 84
    },
    {
     "code": "memcmp(packet->line[a].ptr, \"250\", 3) == 0",
     "line": 86
    },
    {
     "code": "memcmp(packet->line[a].ptr, \"235\", 3) == 0",
     "line": 88
    },
    {
     "code": "memcmp(packet->line[a].ptr, \"334\", 3) == 0",
     "line": 90
    },
    {
     "code": "memcmp(packet->line[a].ptr, \"354\", 3) == 0",
     "line": 92
    },
    {
     "code": "packet->line[a].ptr[0] == 'H'",
     "line": 99
    },
    {
     "code": "packet->line[a].ptr[0] == 'h'",
     "line": 99
    },
    {
     "code": "packet->line[a].ptr[1] == 'E'",
     "line": 100
    },
    {
     "code": "packet->line[a].ptr[1] == 'e'",
     "line": 100
    },
    {
     "code": "packet->line[a].ptr[0] == 'E'",
     "line": 101
    },
    {
     "code": "packet->line[a].ptr[0] == 'e'",
     "line": 101
    },
    {
     "code": "packet->line[a].ptr[1] == 'H'",
     "line": 102
    },
    {
     "code": "packet->line[a].ptr[1] == 'h'",
     "line": 102
    },
    {
     "code": "packet->line[a].ptr[2] == 'L'",
     "line": 103
    },
    {
     "code": "packet->line[a].ptr[2] == 'l'",
     "line": 103
    },
    {
     "code": "packet->line[a].ptr[3] == 'O'",
     "line": 104
    },
    {
     "code": "packet->line[a].ptr[3] == 'o'",
     "line": 104
    },
    {
     "code": "packet->line[a].ptr[4] == ' '",
     "line": 105
    },
    {
     "code": "packet->line[a].ptr[0] == 'M'",
     "line": 108
    },
    {
     "code": "packet->line[a].ptr[0] == 'm'",
     "line": 108
    },
    {
     "code": "packet->line[a].ptr[1] == 'A'",
     "line": 109
    },
    {
     "code": "packet->line[a].ptr[1] == 'a'",
     "line": 109
    },
    {
     "code": "packet->line[a].ptr[2] == 'I'",
     "line": 110
    },
    {
     "code": "packet->line[a].ptr[2] == 'i'",
     "line": 110
    },
    {
     "code": "packet->line[a].ptr[3] == 'L'",
     "line": 111
    },
    {
     "code": "packet->line[a].ptr[3] == 'l'",
     "line": 111
    },
    {
     "code": "packet->line[a].ptr[4] == ' '",
     "line": 112
    },
    {
     "code": "packet->line[a].ptr[0] == 'R'",
     "line": 115
    },
    {
     "code": "packet->line[a].ptr[0] == 'r'",
     "line": 115
    },
    {
     "code": "packet->line[a].ptr[1] == 'C'",
     "line": 116
    },
    {
     "code": "packet->line[a].ptr[1] == 'c'",
     "line": 116
    },
    {
     "code": "packet->line[a].ptr[2] == 'P'",
     "line": 117
    },
    {
     "code": "packet->line[a].ptr[2] == 'p'",
     "line": 117
    },
    {
     "code": "packet->line[a].ptr[3] == 'T'",
     "line": 118
    },
    {
     "code": "packet->line[a].ptr[3] == 't'",
     "line": 118
    },
    {
     "code": "packet->line[a].ptr[4] == ' '",
     "line": 119
    },
    {
     "code": "packet->line[a].ptr[0] == 'A'",
     "line": 122
    },
    {
     "code": "packet->line[a].ptr[0] == 'a'",
     "line": 122
    },
    {
     "code": "packet->line[a].ptr[1] == 'U'",
     "line": 123
    },
    {
     "code": "packet->line[a].ptr[1] == 'u'",
     "line": 123
    },
    {
     "code": "packet->line[a].ptr[2] == 'T'",
     "line": 124
    },
    {
     "code": "packet->line[a].ptr[2] == 't'",
     "line": 124
    },
    {
     "code": "packet->line[a].ptr[3] == 'H'",
     "line": 125
    },
    {
     "code": "packet->line[a].ptr[3] == 'h'",
     "line": 125
    },
    {
     "code": "packet->line[a].ptr[4] == ' '",
     "line": 126
    },
    {
     "code": "packet->line[a].ptr[3] != ' '",
     "line": 134
    },
    {
     "code": "flow->protos.ftp_imap_pop_smtp.username[0] == '\\0'",
     "line": 140
    },
    {
     "code": "flow->protos.ftp_imap_pop_smtp.password[0] == '\\0'",
     "line": 161
    },
    {
     "code": "packet->line[a].ptr[0] == 'S'",
     "line": 193
    },
    {
     "code": "packet->line[a].ptr[0] == 's'",
     "line": 193
    },
    {
     "code": "packet->line[a].ptr[1] == 'T'",
     "line": 194
    },
    {
     "code": "packet->line[a].ptr[1] == 't'",
     "line": 194
    },
    {
     "code": "packet->line[a].ptr[2] == 'A'",
     "line": 195
    },
    {
     "code": "packet->line[a].ptr[2] == 'a'",
     "line": 195
    },
    {
     "code": "packet->line[a].ptr[3] == 'R'",
     "line": 196
    },
    {
     "code": "packet->line[a].ptr[3] == 'r'",
     "line": 196
    },
    {
     "code": "packet->line[a].ptr[4] == 'T'",
     "line": 197
    },
    {
     "code": "packet->line[a].ptr[4] == 't'",
     "line": 197
    },
    {
     "code": "packet->line[a].ptr[5] == 'T'",
     "line": 198
    },
    {
     "code": "packet->line[a].ptr[5] == 't'",
     "line": 198
    },
    {
     "code": "packet->line[a].ptr[6] == 'L'",
     "line": 199
    },
    {
     "code": "packet->line[a].ptr[6] == 'l'",
     "line": 199
    },
    {
     "code": "packet->line[a].ptr[7] == 'S'",
     "line": 200
    },
    {
     "code": "packet->line[a].ptr[7] == 's'",
     "line": 200
    },
    {
     "code": "packet->line[a].ptr[0] == 'D'",
     "line": 206
    },
    {
     "code": "packet->line[a].ptr[0] == 'd'",
     "line": 206
    },
    {
     "code": "packet->line[a].ptr[1] == 'A'",
     "line": 207
    },
    {
     "code": "packet->line[a].ptr[1] == 'a'",
     "line": 207
    },
    {
     "code": "packet->line[a].ptr[2] == 'T'",
     "line": 208
    },
    {
     "code": "packet->line[a].ptr[2] == 't'",
     "line": 208
    },
    {
     "code": "packet->line[a].ptr[3] == 'A'",
     "line": 209
    },
    {
     "code": "packet->line[a].ptr[3] == 'a'",
     "line": 209
    },
    {
     "code": "packet->line[a].ptr[0] == 'N'",
     "line": 211
    },
    {
     "code": "packet->line[a].ptr[0] == 'n'",
     "line": 211
    },
    {
     "code": "packet->line[a].ptr[1] == 'O'",
     "line": 212
    },
    {
     "code": "packet->line[a].ptr[1] == 'o'",
     "line": 212
    },
    {
     "code": "packet->line[a].ptr[2] == 'O'",
     "line": 213
    },
    {
     "code": "packet->line[a].ptr[2] == 'o'",
     "line": 213
    },
    {
     "code": "packet->line[a].ptr[3] == 'P'",
     "line": 214
    },
    {
     "code": "packet->line[a].ptr[3] == 'p'",
     "line": 214
    },
    {
     "code": "packet->line[a].ptr[0] == 'R'",
     "line": 216
    },
    {
     "code": "packet->line[a].ptr[0] == 'r'",
     "line": 216
    },
    {
     "code": "packet->line[a].ptr[1] == 'S'",
     "line": 217
    },
    {
     "code": "packet->line[a].ptr[1] == 's'",
     "line": 217
    },
    {
     "code": "packet->line[a].ptr[2] == 'E'",
     "line": 218
    },
    {
     "code": "packet->line[a].ptr[2] == 'e'",
     "line": 218
    },
    {
     "code": "packet->line[a].ptr[3] == 'T'",
     "line": 219
    },
    {
     "code": "packet->line[a].ptr[3] == 't'",
     "line": 219
    },
    {
     "code": "flow->l4.tcp.smtp_command_bitmask != 0",
     "line": 226
    },
    {
     "code": "a < 16",
     "line": 227
    },
    {
     "code": "flow->packet_counter < 12",
     "line": 247
    },
    {
     "code": "ntohs(get_u_int16_t(packet->payload, packet->payload_packet_len - 2)) == 0x0d0a",
     "line": 255
    },
    {
     "code": "memcmp(packet->payload, \"220\", 3) == 0",
     "line": 256
    },
    {
     "code": "memcmp(packet->payload, \"EHLO\", 4) == 0",
     "line": 256
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "snprintf(flow->protos.ftp_imap_pop_smtp.password,",
     "name": "snprintf",
     "nargs": null
    },
    {
     "code": "flow->protos.ftp_imap_pop_smtp.password",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->protos.ftp_imap_pop_smtp",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->protos",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "flow"
   ],
   "osv_id": "ARVO-42479685",
   "sites": [
    {
     "args": "48",
     "callee": "<operator>.alloc",
     "code": "buf[48]",
     "line": 142
    },
    {
     "args": "out",
     "callee": "ndpi_free",
     "code": "ndpi_free(out)",
     "line": 159
    },
    {
     "args": "48",
     "callee": "<operator>.alloc",
     "code": "buf[48]",
     "line": 163
    },
    {
     "args": "out",
     "callee": "ndpi_free",
     "code": "ndpi_free(out)",
     "line": 179
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_mail_smtp_tcp"
  }
 },
 {
  "osv_id": "ARVO-42479687",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "len",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 875,
    "size": null,
    "type": "u_int16_t"
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
   "cross_function": true,
   "size_expr_cpg": "sizeof(SHA1_CTX)",
   "size_expr_cpg_callee": "ndpi_malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 875,
    "fn": "getSSCertificateFingerprint",
    "code": "len = ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.t | ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_rec | *(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_of | (u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_off",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "getSSCertificateFingerprint",
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 875
   },
   "code": "len = ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.t | ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_rec | *(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_of | (u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_off",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "getSSCertificateFingerprint",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "len < 10 | len > 4096",
   "guard_count": 2,
   "control_structures": "IF:752,IF:762,ELSE:765,IF:765,IF:768,IF:771,IF:795,ELSE:811,IF:820,IF:825,IF:828,IF:829"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479687/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "testcase_size": 110
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
   "dedup_token": "getSSCertificateFingerprint--tlsDetectProtocolFromCertificate--ndpi_search_tls_tcp_udp"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "len = ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_offset+3]) + 5",
     "line": 826
    },
    {
     "code": "len = ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_offset+7])",
     "line": 875
    }
   ],
   "entity_decl": {
    "line": 826,
    "type": "u_int"
   },
   "entity_name_cpg": "len",
   "func_lines": [
    747,
    904
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
     "code": "packet->packet_direction == 0",
     "line": 762
    },
    {
     "code": "packet->payload_packet_len == 0",
     "line": 763
    },
    {
     "code": "flow->l4.tcp.tls_fingerprint_len > 0",
     "line": 768
    },
    {
     "code": "avail > flow->l4.tcp.tls_fingerprint_len",
     "line": 771
    },
    {
     "code": "flow->l4.tcp.tls_fingerprint_len == 0",
     "line": 795
    },
    {
     "code": "packet->payload[flow->l4.tcp.tls_record_offset] == 0x15",
     "line": 825
    },
    {
     "code": "len < 10",
     "line": 828
    },
    {
     "code": "(flow->l4.tcp.tls_record_offset+len) < packet->payload_packet_len",
     "line": 829
    },
    {
     "code": "packet->payload[flow->l4.tcp.tls_record_offset] == 0x16",
     "line": 835
    },
    {
     "code": "packet->payload[flow->l4.tcp.tls_record_offset] != 0x16",
     "line": 841
    },
    {
     "code": "packet->payload[flow->l4.tcp.tls_record_offset+5] == 0xb",
     "line": 843
    },
    {
     "code": "packet->payload[flow->l4.tcp.tls_record_offset] == 0xb",
     "line": 844
    },
    {
     "code": "flow->l4.tcp.tls_srv_cert_fingerprint_ctx == NULL",
     "line": 850
    },
    {
     "code": "packet->payload_packet_len > flow->l4.tcp.tls_record_offset+7",
     "line": 873
    },
    {
     "code": "len > 4096",
     "line": 882
    },
    {
     "code": "flow->l4.tcp.tls_record_offset < packet->payload_packet_len",
     "line": 894
    }
   ],
   "line_call_count": 11,
   "line_calls": [
    {
     "code": "len = ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_offset+7])",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_offset+7])",
     "name": "ntohs",
     "nargs": 1
    },
    {
     "code": "*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_offset+7]",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_offset+7]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "&packet->payload[flow->l4.tcp.tls_record_offset+7]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "packet->payload[flow->l4.tcp.tls_record_offset+7]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->l4.tcp.tls_record_offset+7",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "flow->l4.tcp.tls_record_offset",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->l4.tcp",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->l4",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "len",
    "packet",
    "flow"
   ],
   "osv_id": "ARVO-42479687",
   "sites": [
    {
     "args": "sizeof(SHA1_CTX)",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(sizeof(SHA1_CTX))",
     "line": 851
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "getSSCertificateFingerprint"
  }
 },
 {
  "osv_id": "ARVO-42479691",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "line": 141,
    "size": null,
    "type": "ndpi_flow_struct*"
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
    "line": 354,
    "fn": "ndpi_int_check_stun",
    "code": "flow->host_server_name[j] = payload[k++] | flow->host_server_name[j] | flow->host_server_name | payload[k++]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_int_check_stun",
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "line": 354
   },
   "code": "flow->host_server_name[j] = payload[k++] | flow->host_server_name[j] | flow->host_server_name | payload[k++]",
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_int_check_stun",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j<i",
   "guard_count": 1,
   "control_structures": "IF:149,IF:153,IF:158,ELSE:160,IF:160,IF:163,ELSE:167,IF:170,GOTO:173,IF:178,IF:182,IF:192"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_flow_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "flow",
   "payload"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479691/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
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
   "dedup_token": "ndpi_int_check_stun--ndpi_search_stun--check_ndpi_udp_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_WHATSAPP_CALL",
     "line": 164
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_SIGNAL",
     "line": 204
    },
    {
     "code": "flow->guessed_host_protocol_id = proto",
     "line": 245
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_HANGOUT_DUO",
     "line": 262
    },
    {
     "code": "flow->guessed_protocol_id = NDPI_PROTOCOL_STUN",
     "line": 264
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_WHATSAPP_CALL",
     "line": 280
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_WHATSAPP_CALL",
     "line": 284
    },
    {
     "code": "flow->guessed_protocol_id = NDPI_PROTOCOL_STUN",
     "line": 299
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_ZOOM",
     "line": 331
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_WHATSAPP_CALL",
     "line": 339
    },
    {
     "code": "flow->host_server_name[j] = payload[k++]",
     "line": 354
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_HANGOUT_DUO",
     "line": 361
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_SIGNAL",
     "line": 364
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_MESSENGER",
     "line": 374
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_SKYPE_CALL",
     "line": 398
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_SKYPE_CALL",
     "line": 419
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_SKYPE_CALL",
     "line": 431
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_HANGOUT_DUO",
     "line": 437
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_WHATSAPP_CALL",
     "line": 453
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_WHATSAPP_CALL",
     "line": 459
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_MESSENGER",
     "line": 474
    },
    {
     "code": "flow->guessed_host_protocol_id = NDPI_PROTOCOL_HANGOUT_DUO",
     "line": 476
    }
   ],
   "entity_decl": {
    "line": 141,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    140,
    481
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow",
     "payload",
     "payload_length"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*",
     "u_int8_t*",
     "u_int16_t"
    ]
   },
   "guards": [
    {
     "code": "flow->packet.iph->daddr == 0xFFFFFFFF",
     "line": 153
    },
    {
     "code": "payload_length < sizeof(struct stun_packet_header)",
     "line": 160
    },
    {
     "code": "flow->protos.stun_ssl.stun.num_udp_pkts > 0",
     "line": 163
    },
    {
     "code": "strncmp((const char*)payload, (const char*)\"RSP/\", 4) == 0",
     "line": 170
    },
    {
     "code": "strncmp((const char*)&payload[7], (const char*)\" STUN_\", 6) == 0",
     "line": 171
    },
    {
     "code": "msg_type == 0",
     "line": 178
    },
    {
     "code": "(msg_type & 0x3EEF) > 0x000B",
     "line": 182
    },
    {
     "code": "msg_type != 0x0800",
     "line": 182
    },
    {
     "code": "payload[0] == 0x16",
     "line": 192
    },
    {
     "code": "payload_length == total_len",
     "line": 202
    },
    {
     "code": "msg_type == 0x01",
     "line": 258
    },
    {
     "code": "flow->guessed_host_protocol_id == NDPI_PROTOCOL_GOOGLE",
     "line": 261
    },
    {
     "code": "flow->guessed_host_protocol_id == NDPI_PROTOCOL_UNKNOWN",
     "line": 272
    },
    {
     "code": "payload[0] == 0x80",
     "line": 279
    },
    {
     "code": "payload_length < 512",
     "line": 279
    },
    {
     "code": "payload[0] == 0x90",
     "line": 282
    },
    {
     "code": "(msg_len+11) == payload_length",
     "line": 282
    },
    {
     "code": "payload[0] != 0x80",
     "line": 288
    },
    {
     "code": "(msg_len + 20) > payload_length",
     "line": 288
    },
    {
     "code": "payload_length == (msg_len+20)",
     "line": 304
    },
    {
     "code": "(offset+2) < payload_length",
     "line": 317
    },
    {
     "code": "flow->host_server_name[0] == '\\0'",
     "line": 347
    },
    {
     "code": "realm_len > sizeof(flow->host_server_name)",
     "line": 348
    },
    {
     "code": "j<i",
     "line": 353
    },
    {
     "code": "strstr((char*) flow->host_server_name, \"google.com\") != NULL",
     "line": 360
    },
    {
     "code": "strstr((char*) flow->host_server_name, \"whispersystems.org\") != NULL",
     "line": 363
    },
    {
     "code": "msg_type == 0x0001",
     "line": 372
    },
    {
     "code": "msg_len == 100",
     "line": 373
    },
    {
     "code": "msg_len == 104",
     "line": 373
    },
    {
     "code": "msg_len == 76",
     "line": 376
    },
    {
     "code": "len == 4",
     "line": 389
    },
    {
     "code": "(offset+7) < payload_length",
     "line": 390
    },
    {
     "code": "payload[offset+5] == 0x00",
     "line": 391
    },
    {
     "code": "payload[offset+6] == 0x00",
     "line": 392
    },
    {
     "code": "payload[offset+7] == 0x00",
     "line": 393
    },
    {
     "code": "len == 4",
     "line": 424
    },
    {
     "code": "(offset+7) < payload_length",
     "line": 424
    },
    {
     "code": "payload[offset+4] == 0x00",
     "line": 425
    },
    {
     "code": "payload[offset+5] == 0x00",
     "line": 425
    },
    {
     "code": "payload[offset+6] == 0x00",
     "line": 425
    },
    {
     "code": "payload[offset+7] == 0x02",
     "line": 426
    },
    {
     "code": "payload[offset+7] == 0x03",
     "line": 426
    },
    {
     "code": "msg_type == 0x0800",
     "line": 452
    },
    {
     "code": "flow->protos.stun_ssl.stun.num_udp_pkts > 0",
     "line": 458
    },
    {
     "code": "flow->protos.stun_ssl.stun.num_udp_pkts < MAX_NUM_STUN_PKTS",
     "line": 478
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "flow->host_server_name[j] = payload[k++]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "flow->host_server_name[j]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "flow->host_server_name",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "payload[k++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "k++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "flow",
    "j",
    "payload",
    "k"
   ],
   "osv_id": "ARVO-42479691",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_int_check_stun"
  }
 },
 {
  "osv_id": "ARVO-42479695",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "context",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "line": 181,
    "size": null,
    "type": "SHA1_CTX*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 253
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 192,
    "fn": "SHA1Update",
    "code": "memcpy(&context->buffer[j], data, (i = 64-j)) | &context->buffer[j] | context->buffer[j] | context->buffer",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "SHA1Update",
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "line": 192
   },
   "code": "memcpy(&context->buffer[j], data, (i = 64-j)) | &context->buffer[j] | context->buffer[j] | context->buffer",
   "access": {
    "dir": "READ",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "SHA1Update",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "(context->count[0] += len << 3) < j",
   "guard_count": 1,
   "control_structures": "IF:187,IF:191,FOR:194,ELSE:199"
  },
  "call_chain": [],
  "types": {
   "entity_type": "SHA1_CTX*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "context",
   "data",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479695/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "testcase_size": 84
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
   "dedup_token": "__asan_memcpy--SHA1Update--getSSCertificateFingerprint"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 181,
    "type": "SHA1_CTX*"
   },
   "entity_name_cpg": "context",
   "func_lines": [
    181,
    201
   ],
   "func_params": {
    "names": [
     "context",
     "data",
     "len"
    ],
    "types": [
     "SHA1_CTX*",
     "unsigned char*",
     "u_int32_t"
    ]
   },
   "guards": [
    {
     "code": "(context->count[0] += len << 3) < j",
     "line": 187
    },
    {
     "code": "(j + len) > 63",
     "line": 191
    },
    {
     "code": "i + 63 < len",
     "line": 194
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "memcpy(&context->buffer[j], data, (i = 64-j))",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&context->buffer[j]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "context->buffer[j]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "context->buffer",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "i = 64-j",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "64-j",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "context",
    "j",
    "data",
    "i"
   ],
   "osv_id": "ARVO-42479695",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "SHA1Update"
  }
 },
 {
  "osv_id": "ARVO-42479697",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "block",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "line": 114,
    "size": null,
    "type": "CHAR64LONG16[1]"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 253
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "1",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 115,
    "fn": "SHA1Transform",
    "code": "memcpy(block, buffer, 64)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "SHA1Transform",
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "line": 115
   },
   "code": "memcpy(block, buffer, 64)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "SHA1Transform",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "CHAR64LONG16[1]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479697/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "testcase_size": 184
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
   "dedup_token": "SHA1Transform--SHA1Update--getSSCertificateFingerprint"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "block[1]",
     "line": 114
    },
    {
     "code": "block->l[16 & 15] = (((block->l[(16 + 13) & 15] ^ block->l[(16 + 8) & 15] ^ block->l[(16 + 2) & 15] ^ block->l[16 & 15]) << (1)) ",
     "line": 135
    },
    {
     "code": "block->l[17 & 15] = (((block->l[(17 + 13) & 15] ^ block->l[(17 + 8) & 15] ^ block->l[(17 + 2) & 15] ^ block->l[17 & 15]) << (1)) ",
     "line": 135
    },
    {
     "code": "block->l[18 & 15] = (((block->l[(18 + 13) & 15] ^ block->l[(18 + 8) & 15] ^ block->l[(18 + 2) & 15] ^ block->l[18 & 15]) << (1)) ",
     "line": 135
    },
    {
     "code": "block->l[19 & 15] = (((block->l[(19 + 13) & 15] ^ block->l[(19 + 8) & 15] ^ block->l[(19 + 2) & 15] ^ block->l[19 & 15]) << (1)) ",
     "line": 135
    },
    {
     "code": "block->l[20 & 15] = (((block->l[(20 + 13) & 15] ^ block->l[(20 + 8) & 15] ^ block->l[(20 + 2) & 15] ^ block->l[20 & 15]) << (1)) ",
     "line": 136
    },
    {
     "code": "block->l[21 & 15] = (((block->l[(21 + 13) & 15] ^ block->l[(21 + 8) & 15] ^ block->l[(21 + 2) & 15] ^ block->l[21 & 15]) << (1)) ",
     "line": 136
    },
    {
     "code": "block->l[22 & 15] = (((block->l[(22 + 13) & 15] ^ block->l[(22 + 8) & 15] ^ block->l[(22 + 2) & 15] ^ block->l[22 & 15]) << (1)) ",
     "line": 136
    },
    {
     "code": "block->l[23 & 15] = (((block->l[(23 + 13) & 15] ^ block->l[(23 + 8) & 15] ^ block->l[(23 + 2) & 15] ^ block->l[23 & 15]) << (1)) ",
     "line": 136
    },
    {
     "code": "block->l[24 & 15] = (((block->l[(24 + 13) & 15] ^ block->l[(24 + 8) & 15] ^ block->l[(24 + 2) & 15] ^ block->l[24 & 15]) << (1)) ",
     "line": 137
    },
    {
     "code": "block->l[25 & 15] = (((block->l[(25 + 13) & 15] ^ block->l[(25 + 8) & 15] ^ block->l[(25 + 2) & 15] ^ block->l[25 & 15]) << (1)) ",
     "line": 137
    },
    {
     "code": "block->l[26 & 15] = (((block->l[(26 + 13) & 15] ^ block->l[(26 + 8) & 15] ^ block->l[(26 + 2) & 15] ^ block->l[26 & 15]) << (1)) ",
     "line": 137
    },
    {
     "code": "block->l[27 & 15] = (((block->l[(27 + 13) & 15] ^ block->l[(27 + 8) & 15] ^ block->l[(27 + 2) & 15] ^ block->l[27 & 15]) << (1)) ",
     "line": 137
    },
    {
     "code": "block->l[28 & 15] = (((block->l[(28 + 13) & 15] ^ block->l[(28 + 8) & 15] ^ block->l[(28 + 2) & 15] ^ block->l[28 & 15]) << (1)) ",
     "line": 138
    },
    {
     "code": "block->l[29 & 15] = (((block->l[(29 + 13) & 15] ^ block->l[(29 + 8) & 15] ^ block->l[(29 + 2) & 15] ^ block->l[29 & 15]) << (1)) ",
     "line": 138
    },
    {
     "code": "block->l[30 & 15] = (((block->l[(30 + 13) & 15] ^ block->l[(30 + 8) & 15] ^ block->l[(30 + 2) & 15] ^ block->l[30 & 15]) << (1)) ",
     "line": 138
    },
    {
     "code": "block->l[31 & 15] = (((block->l[(31 + 13) & 15] ^ block->l[(31 + 8) & 15] ^ block->l[(31 + 2) & 15] ^ block->l[31 & 15]) << (1)) ",
     "line": 138
    },
    {
     "code": "block->l[32 & 15] = (((block->l[(32 + 13) & 15] ^ block->l[(32 + 8) & 15] ^ block->l[(32 + 2) & 15] ^ block->l[32 & 15]) << (1)) ",
     "line": 139
    },
    {
     "code": "block->l[33 & 15] = (((block->l[(33 + 13) & 15] ^ block->l[(33 + 8) & 15] ^ block->l[(33 + 2) & 15] ^ block->l[33 & 15]) << (1)) ",
     "line": 139
    },
    {
     "code": "block->l[34 & 15] = (((block->l[(34 + 13) & 15] ^ block->l[(34 + 8) & 15] ^ block->l[(34 + 2) & 15] ^ block->l[34 & 15]) << (1)) ",
     "line": 139
    },
    {
     "code": "block->l[35 & 15] = (((block->l[(35 + 13) & 15] ^ block->l[(35 + 8) & 15] ^ block->l[(35 + 2) & 15] ^ block->l[35 & 15]) << (1)) ",
     "line": 139
    },
    {
     "code": "block->l[36 & 15] = (((block->l[(36 + 13) & 15] ^ block->l[(36 + 8) & 15] ^ block->l[(36 + 2) & 15] ^ block->l[36 & 15]) << (1)) ",
     "line": 140
    },
    {
     "code": "block->l[37 & 15] = (((block->l[(37 + 13) & 15] ^ block->l[(37 + 8) & 15] ^ block->l[(37 + 2) & 15] ^ block->l[37 & 15]) << (1)) ",
     "line": 140
    },
    {
     "code": "block->l[38 & 15] = (((block->l[(38 + 13) & 15] ^ block->l[(38 + 8) & 15] ^ block->l[(38 + 2) & 15] ^ block->l[38 & 15]) << (1)) ",
     "line": 140
    },
    {
     "code": "block->l[39 & 15] = (((block->l[(39 + 13) & 15] ^ block->l[(39 + 8) & 15] ^ block->l[(39 + 2) & 15] ^ block->l[39 & 15]) << (1)) ",
     "line": 140
    },
    {
     "code": "block->l[40 & 15] = (((block->l[(40 + 13) & 15] ^ block->l[(40 + 8) & 15] ^ block->l[(40 + 2) & 15] ^ block->l[40 & 15]) << (1)) ",
     "line": 141
    },
    {
     "code": "block->l[41 & 15] = (((block->l[(41 + 13) & 15] ^ block->l[(41 + 8) & 15] ^ block->l[(41 + 2) & 15] ^ block->l[41 & 15]) << (1)) ",
     "line": 141
    },
    {
     "code": "block->l[42 & 15] = (((block->l[(42 + 13) & 15] ^ block->l[(42 + 8) & 15] ^ block->l[(42 + 2) & 15] ^ block->l[42 & 15]) << (1)) ",
     "line": 141
    },
    {
     "code": "block->l[43 & 15] = (((block->l[(43 + 13) & 15] ^ block->l[(43 + 8) & 15] ^ block->l[(43 + 2) & 15] ^ block->l[43 & 15]) << (1)) ",
     "line": 141
    },
    {
     "code": "block->l[44 & 15] = (((block->l[(44 + 13) & 15] ^ block->l[(44 + 8) & 15] ^ block->l[(44 + 2) & 15] ^ block->l[44 & 15]) << (1)) ",
     "line": 142
    },
    {
     "code": "block->l[45 & 15] = (((block->l[(45 + 13) & 15] ^ block->l[(45 + 8) & 15] ^ block->l[(45 + 2) & 15] ^ block->l[45 & 15]) << (1)) ",
     "line": 142
    },
    {
     "code": "block->l[46 & 15] = (((block->l[(46 + 13) & 15] ^ block->l[(46 + 8) & 15] ^ block->l[(46 + 2) & 15] ^ block->l[46 & 15]) << (1)) ",
     "line": 142
    },
    {
     "code": "block->l[47 & 15] = (((block->l[(47 + 13) & 15] ^ block->l[(47 + 8) & 15] ^ block->l[(47 + 2) & 15] ^ block->l[47 & 15]) << (1)) ",
     "line": 142
    },
    {
     "code": "block->l[48 & 15] = (((block->l[(48 + 13) & 15] ^ block->l[(48 + 8) & 15] ^ block->l[(48 + 2) & 15] ^ block->l[48 & 15]) << (1)) ",
     "line": 143
    },
    {
     "code": "block->l[49 & 15] = (((block->l[(49 + 13) & 15] ^ block->l[(49 + 8) & 15] ^ block->l[(49 + 2) & 15] ^ block->l[49 & 15]) << (1)) ",
     "line": 143
    },
    {
     "code": "block->l[50 & 15] = (((block->l[(50 + 13) & 15] ^ block->l[(50 + 8) & 15] ^ block->l[(50 + 2) & 15] ^ block->l[50 & 15]) << (1)) ",
     "line": 143
    },
    {
     "code": "block->l[51 & 15] = (((block->l[(51 + 13) & 15] ^ block->l[(51 + 8) & 15] ^ block->l[(51 + 2) & 15] ^ block->l[51 & 15]) << (1)) ",
     "line": 143
    },
    {
     "code": "block->l[52 & 15] = (((block->l[(52 + 13) & 15] ^ block->l[(52 + 8) & 15] ^ block->l[(52 + 2) & 15] ^ block->l[52 & 15]) << (1)) ",
     "line": 144
    },
    {
     "code": "block->l[53 & 15] = (((block->l[(53 + 13) & 15] ^ block->l[(53 + 8) & 15] ^ block->l[(53 + 2) & 15] ^ block->l[53 & 15]) << (1)) ",
     "line": 144
    },
    {
     "code": "block->l[54 & 15] = (((block->l[(54 + 13) & 15] ^ block->l[(54 + 8) & 15] ^ block->l[(54 + 2) & 15] ^ block->l[54 & 15]) << (1)) ",
     "line": 144
    },
    {
     "code": "block->l[55 & 15] = (((block->l[(55 + 13) & 15] ^ block->l[(55 + 8) & 15] ^ block->l[(55 + 2) & 15] ^ block->l[55 & 15]) << (1)) ",
     "line": 144
    },
    {
     "code": "block->l[56 & 15] = (((block->l[(56 + 13) & 15] ^ block->l[(56 + 8) & 15] ^ block->l[(56 + 2) & 15] ^ block->l[56 & 15]) << (1)) ",
     "line": 145
    },
    {
     "code": "block->l[57 & 15] = (((block->l[(57 + 13) & 15] ^ block->l[(57 + 8) & 15] ^ block->l[(57 + 2) & 15] ^ block->l[57 & 15]) << (1)) ",
     "line": 145
    },
    {
     "code": "block->l[58 & 15] = (((block->l[(58 + 13) & 15] ^ block->l[(58 + 8) & 15] ^ block->l[(58 + 2) & 15] ^ block->l[58 & 15]) << (1)) ",
     "line": 145
    },
    {
     "code": "block->l[59 & 15] = (((block->l[(59 + 13) & 15] ^ block->l[(59 + 8) & 15] ^ block->l[(59 + 2) & 15] ^ block->l[59 & 15]) << (1)) ",
     "line": 145
    },
    {
     "code": "block->l[60 & 15] = (((block->l[(60 + 13) & 15] ^ block->l[(60 + 8) & 15] ^ block->l[(60 + 2) & 15] ^ block->l[60 & 15]) << (1)) ",
     "line": 146
    },
    {
     "code": "block->l[61 & 15] = (((block->l[(61 + 13) & 15] ^ block->l[(61 + 8) & 15] ^ block->l[(61 + 2) & 15] ^ block->l[61 & 15]) << (1)) ",
     "line": 146
    },
    {
     "code": "block->l[62 & 15] = (((block->l[(62 + 13) & 15] ^ block->l[(62 + 8) & 15] ^ block->l[(62 + 2) & 15] ^ block->l[62 & 15]) << (1)) ",
     "line": 146
    },
    {
     "code": "block->l[63 & 15] = (((block->l[(63 + 13) & 15] ^ block->l[(63 + 8) & 15] ^ block->l[(63 + 2) & 15] ^ block->l[63 & 15]) << (1)) ",
     "line": 146
    },
    {
     "code": "block->l[64 & 15] = (((block->l[(64 + 13) & 15] ^ block->l[(64 + 8) & 15] ^ block->l[(64 + 2) & 15] ^ block->l[64 & 15]) << (1)) ",
     "line": 147
    },
    {
     "code": "block->l[65 & 15] = (((block->l[(65 + 13) & 15] ^ block->l[(65 + 8) & 15] ^ block->l[(65 + 2) & 15] ^ block->l[65 & 15]) << (1)) ",
     "line": 147
    },
    {
     "code": "block->l[66 & 15] = (((block->l[(66 + 13) & 15] ^ block->l[(66 + 8) & 15] ^ block->l[(66 + 2) & 15] ^ block->l[66 & 15]) << (1)) ",
     "line": 147
    },
    {
     "code": "block->l[67 & 15] = (((block->l[(67 + 13) & 15] ^ block->l[(67 + 8) & 15] ^ block->l[(67 + 2) & 15] ^ block->l[67 & 15]) << (1)) ",
     "line": 147
    },
    {
     "code": "block->l[68 & 15] = (((block->l[(68 + 13) & 15] ^ block->l[(68 + 8) & 15] ^ block->l[(68 + 2) & 15] ^ block->l[68 & 15]) << (1)) ",
     "line": 148
    },
    {
     "code": "block->l[69 & 15] = (((block->l[(69 + 13) & 15] ^ block->l[(69 + 8) & 15] ^ block->l[(69 + 2) & 15] ^ block->l[69 & 15]) << (1)) ",
     "line": 148
    },
    {
     "code": "block->l[70 & 15] = (((block->l[(70 + 13) & 15] ^ block->l[(70 + 8) & 15] ^ block->l[(70 + 2) & 15] ^ block->l[70 & 15]) << (1)) ",
     "line": 148
    },
    {
     "code": "block->l[71 & 15] = (((block->l[(71 + 13) & 15] ^ block->l[(71 + 8) & 15] ^ block->l[(71 + 2) & 15] ^ block->l[71 & 15]) << (1)) ",
     "line": 148
    },
    {
     "code": "block->l[72 & 15] = (((block->l[(72 + 13) & 15] ^ block->l[(72 + 8) & 15] ^ block->l[(72 + 2) & 15] ^ block->l[72 & 15]) << (1)) ",
     "line": 149
    },
    {
     "code": "block->l[73 & 15] = (((block->l[(73 + 13) & 15] ^ block->l[(73 + 8) & 15] ^ block->l[(73 + 2) & 15] ^ block->l[73 & 15]) << (1)) ",
     "line": 149
    },
    {
     "code": "block->l[74 & 15] = (((block->l[(74 + 13) & 15] ^ block->l[(74 + 8) & 15] ^ block->l[(74 + 2) & 15] ^ block->l[74 & 15]) << (1)) ",
     "line": 149
    },
    {
     "code": "block->l[75 & 15] = (((block->l[(75 + 13) & 15] ^ block->l[(75 + 8) & 15] ^ block->l[(75 + 2) & 15] ^ block->l[75 & 15]) << (1)) ",
     "line": 149
    },
    {
     "code": "block->l[76 & 15] = (((block->l[(76 + 13) & 15] ^ block->l[(76 + 8) & 15] ^ block->l[(76 + 2) & 15] ^ block->l[76 & 15]) << (1)) ",
     "line": 150
    },
    {
     "code": "block->l[77 & 15] = (((block->l[(77 + 13) & 15] ^ block->l[(77 + 8) & 15] ^ block->l[(77 + 2) & 15] ^ block->l[77 & 15]) << (1)) ",
     "line": 150
    },
    {
     "code": "block->l[78 & 15] = (((block->l[(78 + 13) & 15] ^ block->l[(78 + 8) & 15] ^ block->l[(78 + 2) & 15] ^ block->l[78 & 15]) << (1)) ",
     "line": 150
    },
    {
     "code": "block->l[79 & 15] = (((block->l[(79 + 13) & 15] ^ block->l[(79 + 8) & 15] ^ block->l[(79 + 2) & 15] ^ block->l[79 & 15]) << (1)) ",
     "line": 150
    }
   ],
   "entity_decl": {
    "line": 114,
    "type": "CHAR64LONG16[1]"
   },
   "entity_name_cpg": "block",
   "func_lines": [
    106,
    162
   ],
   "func_params": {
    "names": [
     "state",
     "buffer"
    ],
    "types": [
     "u_int32_t[5]",
     "unsigned char[64]"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(block, buffer, 64)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "block",
    "buffer"
   ],
   "osv_id": "ARVO-42479697",
   "sites": [
    {
     "args": "1",
     "callee": "<operator>.alloc",
     "code": "block[1]",
     "line": 114
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "SHA1Transform"
  }
 },
 {
  "osv_id": "ARVO-42479758",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "iACLen",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-setcos.c",
    "line": 791,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "sc_file_set_sec_attr",
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 678
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": null,
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 791,
    "fn": "parse_sec_attr_44",
    "code": "iACLen   = buf[iOffset] & 0x0F | buf[iOffset] & 0x0F | buf[iOffset]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_sec_attr_44",
    "file": "/src/opensc/src/libopensc/card-setcos.c",
    "line": 791
   },
   "code": "iACLen   = buf[iOffset] & 0x0F | buf[iOffset] & 0x0F | buf[iOffset]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_sec_attr_44",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "iACLen > len | iACLen > (1+iParmLen+iKeyLen) | iACLen > 0",
   "guard_count": 3,
   "control_structures": "WHILE:790,IF:792,BREAK:793,IF:797,IF:802,IF:803,IF:804,IF:805,IF:806,IF:809,IF:811,BREAK:812"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "buf",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/8fea658fe9b5bdf51de7e321a1a549056ba4b150/ARVO-42479758/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_8fea658fe9b5.cpg",
   "testcase_size": 74
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
   "dedup_token": "parse_sec_attr_44--setcos_select_file--sc_select_file"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "iACLen   = buf[iOffset] & 0x0F",
     "line": 791
    }
   ],
   "entity_decl": {
    "line": 791,
    "type": "size_t"
   },
   "entity_name_cpg": "iACLen",
   "func_lines": [
    764,
    916
   ],
   "func_params": {
    "names": [
     "file",
     "buf",
     "len"
    ],
    "types": [
     "sc_file_t*",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "len > 1",
     "line": 790
    },
    {
     "code": "iACLen > len",
     "line": 792
    },
    {
     "code": "len < 1+(size_t)iACLen",
     "line": 811
    },
    {
     "code": "iACLen > (1+iParmLen+iKeyLen)",
     "line": 831
    },
    {
     "code": "len < 1+1+1+(size_t)iParmLen",
     "line": 832
    },
    {
     "code": "len < 1+2",
     "line": 839
    },
    {
     "code": "iACLen > 0",
     "line": 871
    },
    {
     "code": "len < 1 + (size_t)iACLen",
     "line": 875
    },
    {
     "code": "iPinCount > 0",
     "line": 897
    },
    {
     "code": "len < 1 + 2",
     "line": 898
    },
    {
     "code": "i < 8",
     "line": 906
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "iACLen   = buf[iOffset] & 0x0F",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "buf[iOffset] & 0x0F",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "buf[iOffset]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "iACLen",
    "buf",
    "iOffset"
   ],
   "osv_id": "ARVO-42479758",
   "sites": [
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "df_idx[8] = {\t /* byte 1 = OpenSC type of AC Bit0,  byte 2 = OpenSC type of AC Bit1 ...*/",
     "line": 767
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "ef_idx[8] = {",
     "line": 771
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "efi_idx[8] = { /* internal EF used for RSA keys */",
     "line": 775
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse_sec_attr_44"
  }
 },
 {
  "osv_id": "ARVO-42479773",
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
    "fn": "H5FL_malloc",
    "file": "/build/hdf5-3JSo9x/hdf5-1.8.16+docs/debian/build/src/../../../src/H5FL.c",
    "line": 199
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2788,
    "fn": "Mat_VarReadNextInfoIterate",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_VarReadNextInfoIterate",
    "file": "/src/matio/src/mat73.c",
    "line": 2788
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 7680,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_VarReadNextInfoIterate",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/6540087e697ca2b8950bada3d4ca653951b467dc/ARVO-42479773/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_6540087e697c.cpg",
   "testcase_size": 71808
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
   "dedup_token": "memcpy--memcpy--H5O_fill_new_decode"
  },
  "deep": {
   "entity_assignments": [],
   "guards": [],
   "line_calls": [],
   "line_ids": [],
   "method_missing": true,
   "osv_id": "ARVO-42479773",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_VarReadNextInfoIterate"
  }
 },
 {
  "osv_id": "ARVO-42479852",
  "project": "libgit2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ch",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 429,
    "type": "unsigned char",
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
   "cross_function": true,
   "size_expr_cpg": "&new_size ;; output_len ;; buf->size",
   "size_expr_cpg_callee": "GIT_ERROR_CHECK_ALLOC_ADD"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 431,
    "fn": "git_buf_decode_base85",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "git_buf_decode_base85",
    "file": "/src/libgit2/src/buffer.c",
    "line": 431
   },
   "code": "ch = *base85++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "git_buf_decode_base85",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/b246bed5ab83035d8aef95f1b7ff10dd746db7cb/ARVO-42479852/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_b246bed5ab83.cpg",
   "testcase_size": 59
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
   "dedup_token": "git_buf_decode_base85--parse_patch_binary_side--parse_patch_binary"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ch = *base85++",
     "line": 431
    },
    {
     "code": "ch = *base85++",
     "line": 438
    }
   ],
   "entity_decl": {
    "line": 429,
    "type": "unsigned char"
   },
   "entity_name_cpg": "ch",
   "func_lines": [
    408,
    468
   ],
   "func_params": {
    "names": [
     "buf",
     "base85",
     "base85_len",
     "output_len"
    ],
    "types": [
     "git_buf*",
     "char*",
     "size_t",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "output_len > base85_len * 4 / 5",
     "line": 417
    },
    {
     "code": "(buf)->ptr == git_buf__oom",
     "line": 424
    },
    {
     "code": "(new_size) > (buf)->asize",
     "line": 424
    },
    {
     "code": "git_buf_grow((buf), (new_size)) < 0",
     "line": 424
    },
    {
     "code": "--de < 0",
     "line": 433
    },
    {
     "code": "--de < 0",
     "line": 440
    },
    {
     "code": "0xffffffff / 85 < acc",
     "line": 444
    },
    {
     "code": "0xffffffff - de < (acc *= 85)",
     "line": 445
    },
    {
     "code": "output_len < 4",
     "line": 450
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "ch = *base85++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*base85++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "base85++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "ch",
    "base85"
   ],
   "osv_id": "ARVO-42479852",
   "sites": [
    {
     "args": "&new_size ;; output_len ;; buf->size",
     "callee": "GIT_ERROR_CHECK_ALLOC_ADD",
     "code": "GIT_ERROR_CHECK_ALLOC_ADD(&new_size, output_len, buf->size)",
     "line": 422
    },
    {
     "args": "&new_size ;; new_size ;; 1",
     "callee": "GIT_ERROR_CHECK_ALLOC_ADD",
     "code": "GIT_ERROR_CHECK_ALLOC_ADD(&new_size, new_size, 1)",
     "line": 423
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "git_buf_decode_base85"
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