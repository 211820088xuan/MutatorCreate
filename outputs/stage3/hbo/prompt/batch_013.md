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
  "osv_id": "ARVO-42489821",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_dec",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "line": 1920,
    "size": null,
    "type": "dec_struct_t*"
   }
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
    "line": 2072,
    "fn": "ih264d_parse_pslice",
    "code": "memcpy((void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_i | (void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_p | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_parse_pslice",
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "line": 2072
   },
   "code": "memcpy((void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_i | (void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_p | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice",
   "access": {
    "dir": "WRITE",
    "width": 268,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_parse_pslice",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1960,IF:1967,IF:1987,IF:1992,ELSE:1997,FOR:2009,IF:2019,FOR:2034,IF:2055,IF:2061,IF:2079,IF:2082"
  },
  "call_chain": [],
  "types": {
   "entity_type": "dec_struct_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ps_dec"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42489821/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "testcase_size": 60
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
   "dedup_token": "__asan_memcpy--ih264d_parse_pslice--ih264d_parse_decode_slice"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ps_dec->s_default_mv_pred.u1_col_ref_pic_idx = (UWORD8)-1",
     "line": 1949
    },
    {
     "code": "ps_dec->s_default_mv_pred.u1_pic_type = (UWORD8)-1",
     "line": 1950
    },
    {
     "code": "ps_dec->u1_num_ref_idx_lx_active_prev =",
     "line": 1983
    },
    {
     "code": "ps_dec->ps_ref_pic_buf_lx[0] = ps_dec->ps_dpb_mgr->ps_mod_dpb[0]",
     "line": 1990
    },
    {
     "code": "ps_dec->ps_ref_pic_buf_lx[0] = ps_dec->ps_dpb_mgr->ps_mod_dpb[0]",
     "line": 1994
    },
    {
     "code": "ps_dec->ps_ref_pic_buf_lx[0] =",
     "line": 1997
    },
    {
     "code": "ps_dec->pu4_wt_ofsts = ps_dec->pu4_wts_ofsts_mat",
     "line": 2085
    },
    {
     "code": "ps_dec->ps_cur_slice->u2_log2Y_crwd = 0",
     "line": 2089
    },
    {
     "code": "ps_dec->pu4_wt_ofsts = ps_dec->pu4_wts_ofsts_mat",
     "line": 2090
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->u2_log2Y_crwd =",
     "line": 2093
    },
    {
     "code": "ps_dec->u4_bitoffset = i_temp",
     "line": 2111
    },
    {
     "code": "ps_dec->u1_slice_header_done = 2",
     "line": 2187
    },
    {
     "code": "ps_dec->pf_parse_inter_slice = ih264d_parse_inter_slice_data_cabac",
     "line": 2192
    },
    {
     "code": "ps_dec->pf_parse_inter_mb = ih264d_parse_pmb_cabac",
     "line": 2193
    },
    {
     "code": "ps_dec->pf_get_mb_info = ih264d_get_mb_info_cabac_mbaff",
     "line": 2197
    },
    {
     "code": "ps_dec->pf_get_mb_info = ih264d_get_mb_info_cabac_nonmbaff",
     "line": 2199
    },
    {
     "code": "ps_dec->pf_parse_inter_slice = ih264d_parse_inter_slice_data_cavlc",
     "line": 2204
    },
    {
     "code": "ps_dec->pf_parse_inter_mb = ih264d_parse_pmb_cavlc",
     "line": 2205
    },
    {
     "code": "ps_dec->pf_get_mb_info = ih264d_get_mb_info_cavlc_mbaff",
     "line": 2208
    },
    {
     "code": "ps_dec->pf_get_mb_info = ih264d_get_mb_info_cavlc_nonmbaff",
     "line": 2211
    },
    {
     "code": "ps_dec->u1_B = 0",
     "line": 2214
    },
    {
     "code": "ps_dec->pf_mvpred_ref_tfr_nby2mb = ih264d_mv_pred_ref_tfr_nby2_pmb",
     "line": 2215
    }
   ],
   "entity_decl": {
    "line": 1920,
    "type": "dec_struct_t*"
   },
   "entity_name_cpg": "ps_dec",
   "func_lines": [
    1920,
    2221
   ],
   "func_params": {
    "names": [
     "ps_dec",
     "u2_first_mb_in_slice"
    ],
    "types": [
     "dec_struct_t*",
     "UWORD16"
    ]
   },
   "guards": [
    {
     "code": "u8_ref_idx_l0 > u1_max_ref_idx",
     "line": 1967
    },
    {
     "code": "ret == -1",
     "line": 1992
    },
    {
     "code": "idx < ps_cur_slice->u1_num_ref_idx_lx_active[0]",
     "line": 2009
    },
    {
     "code": "idx < ps_cur_slice->u1_num_ref_idx_lx_active[0]",
     "line": 2034
    },
    {
     "code": "0 == ps_dec->i4_display_delay",
     "line": 2062
    },
    {
     "code": "ret != OK",
     "line": 2082
    },
    {
     "code": "u1_field_pic_flag == 0",
     "line": 2096
    },
    {
     "code": "ps_cur_slice->u1_nal_ref_idc != 0",
     "line": 2102
    },
    {
     "code": "i_temp < 0",
     "line": 2107
    },
    {
     "code": "ps_pps->u1_entropy_coding_mode == CABAC",
     "line": 2119
    },
    {
     "code": "u4_temp > MAX_CABAC_INIT_IDC",
     "line": 2123
    },
    {
     "code": "i8_temp < MIN_H264_QP",
     "line": 2134
    },
    {
     "code": "i8_temp > MAX_H264_QP",
     "line": 2134
    },
    {
     "code": "ps_pps->u1_deblocking_filter_parameters_present_flag == 1",
     "line": 2142
    },
    {
     "code": "u4_temp > SLICE_BOUNDARY_DBLK_DISABLED",
     "line": 2145
    },
    {
     "code": "u4_temp != 1",
     "line": 2152
    },
    {
     "code": "MIN_DBLK_FIL_OFF > i_temp",
     "line": 2156
    },
    {
     "code": "i_temp > MAX_DBLK_FIL_OFF",
     "line": 2156
    },
    {
     "code": "MIN_DBLK_FIL_OFF > i_temp",
     "line": 2166
    },
    {
     "code": "i_temp > MAX_DBLK_FIL_OFF",
     "line": 2166
    },
    {
     "code": "ret != OK",
     "line": 2217
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy((void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc,",
     "name": "memcpy",
     "nargs": null
    },
    {
     "code": "(void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_parse_cur_slice",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ps_dec"
   ],
   "osv_id": "ARVO-42489821",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_parse_pslice"
  }
 },
 {
  "osv_id": "ARVO-42490025",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pv_cur_pic_addr0",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "line": 209,
    "size": null,
    "type": "void*"
   }
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
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_fill_bs1_16x16mb_pslice",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "pv_cur_pic_addr0 != pv_nbr_pic_addr0 | pv_cur_pic_addr0 != pv_nbr_pic_addr0",
   "guard_count": 2,
   "control_structures": "FOR:228,IF:235,FOR:270,IF:277"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ps_cur_mv_pred",
   "ppv_map_ref_idx_to_poc"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42490025/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "testcase_size": 55
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
   "dedup_token": "ih264d_fill_bs1_16x16mb_pslice--ih264d_compute_bs_non_mbaff_thread--ih264d_recon_deblk_slice"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0]]",
     "line": 222
    }
   ],
   "entity_decl": {
    "line": 209,
    "type": "void*"
   },
   "entity_name_cpg": "pv_cur_pic_addr0",
   "func_lines": [
    198,
    312
   ],
   "func_params": {
    "names": [
     "ps_cur_mv_pred",
     "ps_top_mv_pred",
     "ppv_map_ref_idx_to_poc",
     "pu4_bs_table",
     "ps_leftmost_mv_pred",
     "ps_left_addr",
     "u4_pic_addrress",
     "i4_ver_mvlimit"
    ],
    "types": [
     "mv_pred_t*",
     "mv_pred_t*",
     "void**",
     "UWORD32*",
     "mv_pred_t*",
     "neighbouradd_t*",
     "void**",
     "WORD32"
    ]
   },
   "guards": [
    {
     "code": "i < 4",
     "line": 228
    },
    {
     "code": "((i2_p_mv0 - i2_q_mv0)) < 0",
     "line": 255
    },
    {
     "code": "((i2_p_mv1 - i2_q_mv1)) < 0",
     "line": 256
    },
    {
     "code": "pv_cur_pic_addr0 != pv_nbr_pic_addr0",
     "line": 258
    },
    {
     "code": "pv_cur_pic_addr1 != pv_nbr_pic_addr1",
     "line": 259
    },
    {
     "code": "i < 4",
     "line": 270
    },
    {
     "code": "((i2_p_mv0 - i2_q_mv0)) < 0",
     "line": 297
    },
    {
     "code": "((i2_p_mv1 - i2_q_mv1)) < 0",
     "line": 299
    },
    {
     "code": "pv_cur_pic_addr0 != pv_nbr_pic_addr0",
     "line": 302
    },
    {
     "code": "pv_cur_pic_addr1 != pv_nbr_pic_addr1",
     "line": 303
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0]]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0]]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "ps_cur_mv_pred->i1_ref_frame[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "ps_cur_mv_pred->i1_ref_frame",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pv_cur_pic_addr0",
    "ppv_map_ref_idx_to_poc_l0",
    "ps_cur_mv_pred"
   ],
   "osv_id": "ARVO-42490025",
   "sites": []
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
  "osv_id": "ARVO-42490150",
  "project": "serenity",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "__libcpp_operator_new<unsigned long>",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 235
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 219,
    "fn": "Gfx::Streamer::read_u8()",
    "code": "!consume_specific('{') | consume_specific('{')",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Gfx::Streamer::read_u8()",
    "file": "/src/serenity/Libraries/LibGfx/BMPLoader.cpp",
    "line": 219
   },
   "code": "!consume_specific('{') | consume_specific('{')",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "consume_replacement_field",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/65eef944ab35ca85be178615ffc32834d430f4e3/ARVO-42490150/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_65eef944ab35.cpg",
   "testcase_size": 230
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
   "dedup_token": "Gfx::Streamer::read_u8()--Gfx::uncompress_bmp_rle_data(Gfx::BMPLoadingContext&, AK::ByteBuffer&)::$_7::operator()() const--AK::Function<AK::Optional<unsigned in"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    217,
    229
   ],
   "func_params": {
    "names": [
     "index"
    ],
    "types": [
     "size_t&"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "!consume_specific('{')",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "consume_specific('{')",
     "name": "consume_specific",
     "nargs": 1
    }
   ],
   "line_ids": [],
   "osv_id": "ARVO-42490150",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Gfx::Streamer::read_u8()"
  }
 },
 {
  "osv_id": "ARVO-42490229",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ret",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_sds.c",
    "line": 213,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
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
    "line": 291,
    "fn": "flb_sds_cat_utf8",
    "code": "ret = flb_utf8_decode(&state, &cp, *p) | flb_utf8_decode(&state, &cp, *p) | &state | &cp",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_sds_cat_utf8",
    "file": "/src/fluent-bit/src/flb_sds.c",
    "line": 291
   },
   "code": "ret = flb_utf8_decode(&state, &cp, *p) | flb_utf8_decode(&state, &cp, *p) | &state | &cp",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_sds_cat_utf8",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "ret == 0 | state != FLB_UTF8_ACCEPT | cp > 0xFFFF",
   "guard_count": 3,
   "control_structures": "IF:226,IF:228,FOR:235,IF:236,IF:238,IF:246,ELSE:250,IF:250,SWITCH:252,BREAK:255,BREAK:258,BREAK:261"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "str",
   "str_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/6fe5d030bcee43556fb1c6054f55854c605a5b0c/ARVO-42490229/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_6fe5d030bcee.cpg",
   "testcase_size": 512
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
   "dedup_token": "flb_sds_cat_utf8--flb_msgpack_gelf_value--flb_msgpack_to_gelf"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ret = flb_utf8_decode(&state, &cp, *p)",
     "line": 291
    }
   ],
   "entity_decl": {
    "line": 213,
    "type": "int"
   },
   "entity_name_cpg": "ret",
   "func_lines": [
    208,
    329
   ],
   "func_params": {
    "names": [
     "sds",
     "str",
     "str_len"
    ],
    "types": [
     "flb_sds_t*",
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "tmp == NULL",
     "line": 228
    },
    {
     "code": "i < str_len",
     "line": 235
    },
    {
     "code": "flb_sds_avail(s) < 8",
     "line": 236
    },
    {
     "code": "tmp == NULL",
     "line": 238
    },
    {
     "code": "c == '\\\\'",
     "line": 246
    },
    {
     "code": "c == '\"'",
     "line": 246
    },
    {
     "code": "c < 32",
     "line": 277
    },
    {
     "code": "c == 0x7f",
     "line": 277
    },
    {
     "code": "b < hex_bytes",
     "line": 289
    },
    {
     "code": "ret == 0",
     "line": 292
    },
    {
     "code": "state != FLB_UTF8_ACCEPT",
     "line": 297
    },
    {
     "code": "cp > 0xFFFF",
     "line": 305
    },
    {
     "code": "c > 0",
     "line": 307
    },
    {
     "code": "c > 0",
     "line": 311
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "ret = flb_utf8_decode(&state, &cp, *p)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "flb_utf8_decode(&state, &cp, *p)",
     "name": "flb_utf8_decode",
     "nargs": 3
    },
    {
     "code": "&state",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "&cp",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "*p",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "ret",
    "state",
    "cp",
    "p"
   ],
   "osv_id": "ARVO-42490229",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_sds_cat_utf8"
  }
 },
 {
  "osv_id": "ARVO-42490266",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "line": 1084,
    "size": null,
    "type": "flb_http_client*"
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "flb_realloc",
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "line": 91
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "c->header_buf ;; new_size",
   "size_expr_cpg_callee": "flb_realloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1114,
    "fn": "flb_http_do",
    "code": "c->header_buf[c->header_len++] = '\\r' | c->header_buf[c->header_len++] | c->header_buf | c->header_len++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_http_do",
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "line": 1114
   },
   "code": "c->header_buf[c->header_len++] = '\\r' | c->header_buf[c->header_len++] | c->header_buf | c->header_len++",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_http_do",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1098,IF:1103,IF:1106,IF:1132,IF:1137,IF:1141,WHILE:1152,IF:1154,IF:1161,IF:1175,IF:1176,BREAK:1177"
  },
  "call_chain": [],
  "types": {
   "entity_type": "flb_http_client*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "c"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9da96a3b88859ae57134c6932cab65101114e3b4/ARVO-42490266/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9da96a3b8885.cpg",
   "testcase_size": 1898
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
   "dedup_token": "flb_http_do--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c->header_buf = tmp",
     "line": 1109
    },
    {
     "code": "c->header_len = new_size",
     "line": 1110
    },
    {
     "code": "c->header_buf[c->header_len++] = '\\r'",
     "line": 1114
    },
    {
     "code": "c->header_buf[c->header_len++] = '\\n'",
     "line": 1115
    },
    {
     "code": "c->resp.data_len = 0",
     "line": 1151
    },
    {
     "code": "c->resp.data[c->resp.data_len] = '\\0'",
     "line": 1184
    }
   ],
   "entity_decl": {
    "line": 1084,
    "type": "flb_http_client*"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    1084,
    1229
   ],
   "func_params": {
    "names": [
     "c",
     "bytes"
    ],
    "types": [
     "flb_http_client*",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "ret == -1",
     "line": 1098
    },
    {
     "code": "header_available(c, crlf) != 0",
     "line": 1103
    },
    {
     "code": "ret == -1",
     "line": 1132
    },
    {
     "code": "c->body_len > 0",
     "line": 1137
    },
    {
     "code": "ret == -1",
     "line": 1141
    },
    {
     "code": "ret == -1",
     "line": 1161
    },
    {
     "code": "ret == FLB_HTTP_ERROR",
     "line": 1187
    },
    {
     "code": "ret == FLB_HTTP_OK",
     "line": 1190
    },
    {
     "code": "ret == FLB_HTTP_MORE",
     "line": 1193
    },
    {
     "code": "ret == FLB_HTTP_OK",
     "line": 1206
    },
    {
     "code": "c->resp.connection_close == FLB_TRUE",
     "line": 1212
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "c->header_buf[c->header_len++] = '\\r'",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "c->header_buf[c->header_len++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "c->header_buf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "c->header_len++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "c->header_len",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c"
   ],
   "osv_id": "ARVO-42490266",
   "sites": [
    {
     "args": "c->header_buf ;; new_size",
     "callee": "flb_realloc",
     "code": "flb_realloc(c->header_buf, new_size)",
     "line": 1105
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_http_do"
  }
 },
 {
  "osv_id": "ARVO-42490276",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "line": 248,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "flb_malloc",
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "line": 62
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
    "line": 293,
    "fn": "process_chunked_data",
    "code": "p[val -2] != '\\r' || p[val - 1] != '\\n' | p[val -2] != '\\r' | p[val -2] | val -2",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "process_chunked_data",
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "line": 293
   },
   "code": "p[val -2] != '\\r' || p[val - 1] != '\\n' | p[val -2] != '\\r' | p[val -2] | val -2",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "process_chunked_data",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "val == LONG_MAX | val == LONG_MIN | val == 0",
   "guard_count": 4,
   "control_structures": "IF:254,IF:260,IF:272,IF:288,IF:293,IF:306,IF:316,IF:320,IF:344,IF:352,GOTO:353"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "c"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9da96a3b88859ae57134c6932cab65101114e3b4/ARVO-42490276/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9da96a3b8885.cpg",
   "testcase_size": 162
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
   "dedup_token": "process_chunked_data--process_data--fuzz_process_data"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "p = strstr(r->chunk_processed_end, \"\\r\\n\")",
     "line": 253
    }
   ],
   "entity_decl": {
    "line": 248,
    "type": "char*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    243,
    357
   ],
   "func_params": {
    "names": [
     "c"
    ],
    "types": [
     "flb_http_client*"
    ]
   },
   "guards": [
    {
     "code": "len > sizeof(tmp) - 1",
     "line": 260
    },
    {
     "code": "len == 0",
     "line": 260
    },
    {
     "code": "errno == ERANGE",
     "line": 272
    },
    {
     "code": "val == LONG_MAX",
     "line": 272
    },
    {
     "code": "val == LONG_MIN",
     "line": 272
    },
    {
     "code": "errno != 0",
     "line": 273
    },
    {
     "code": "val == 0",
     "line": 273
    },
    {
     "code": "len < val",
     "line": 288
    },
    {
     "code": "p[val -2] != '\\r'",
     "line": 293
    },
    {
     "code": "p[val - 1] != '\\n'",
     "line": 293
    },
    {
     "code": "val - 2 == 0",
     "line": 306
    },
    {
     "code": "len < 5",
     "line": 316
    },
    {
     "code": "r->chunk_processed_end[3] != '\\r'",
     "line": 320
    },
    {
     "code": "r->chunk_processed_end[4] != '\\n'",
     "line": 321
    },
    {
     "code": "val - 2 == 0",
     "line": 344
    },
    {
     "code": "len > 0",
     "line": 352
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "p[val -2] != '\\r' ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "p[val -2] != '\\r'",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "p[val -2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "val -2",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "p[val - 1] != '\\n'",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "p[val - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "val - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p",
    "val"
   ],
   "osv_id": "ARVO-42490276",
   "sites": [
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "tmp[32]",
     "line": 249
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "process_chunked_data"
  }
 },
 {
  "osv_id": "ARVO-42490298",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "r",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/lib/miniz/miniz.c",
    "line": 2381,
    "size": null,
    "type": "tinfl_decompressor*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "31",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2429,
    "fn": "tinfl_decompress",
    "code": "TINFL_GET_BITS(3, r->m_final, 3) | r->m_final | num_bits < (mz_uint)(3) | (mz_uint)(3)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tinfl_decompress",
    "file": "/src/fluent-bit/lib/miniz/miniz.c",
    "line": 2429
   },
   "code": "TINFL_GET_BITS(3, r->m_final, 3) | r->m_final | num_bits < (mz_uint)(3) | (mz_uint)(3)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tinfl_decompress",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "pIn_buf_cur >= pIn_buf_end | pIn_buf_cur >= pIn_buf_end | num_bits < (mz_uint)(3)",
   "guard_count": 66,
   "control_structures": "IF:2398,SWITCH:2410,IF:2414,DO:2416,WHILE:2416,DO:2416,GOTO:2416,DO:2417,WHILE:2417,DO:2417,GOTO:2417,IF:2419"
  },
  "call_chain": [],
  "types": {
   "entity_type": "tinfl_decompressor*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "r",
   "pIn_buf_next",
   "pIn_buf_size",
   "pOut_buf_start",
   "pOut_buf_next",
   "pOut_buf_size",
   "decomp_flags"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/72b62d2270edda9a0281ff8a6c3903d99e1892c9/ARVO-42490298/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_72b62d2270ed.cpg",
   "testcase_size": 600
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
   "dedup_token": "tinfl_decompress--mz_inflate--flb_gzip_uncompress"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "r->m_zhdr0 = r->m_zhdr1 = 0",
     "line": 2412
    },
    {
     "code": "r->m_zhdr1 = 0",
     "line": 2412
    },
    {
     "code": "r->m_z_adler32 = r->m_check_adler32 = 1",
     "line": 2413
    },
    {
     "code": "r->m_check_adler32 = 1",
     "line": 2413
    },
    {
     "code": "r->m_state = 1",
     "line": 2416
    },
    {
     "code": "r->m_zhdr0 = *pIn_buf_cur++",
     "line": 2416
    },
    {
     "code": "r->m_state = 2",
     "line": 2417
    },
    {
     "code": "r->m_zhdr1 = *pIn_buf_cur++",
     "line": 2417
    },
    {
     "code": "r->m_state = 36",
     "line": 2423
    },
    {
     "code": "r->m_state = 3",
     "line": 2429
    },
    {
     "code": "r->m_final = bit_buf & ((1 << (3)) - 1)",
     "line": 2429
    },
    {
     "code": "r->m_type = r->m_final >> 1",
     "line": 2430
    },
    {
     "code": "r->m_state = 5",
     "line": 2433
    },
    {
     "code": "r->m_state = 6",
     "line": 2437
    },
    {
     "code": "r->m_raw_header[counter] = bit_buf & ((1 << (8)) - 1)",
     "line": 2437
    },
    {
     "code": "r->m_state = 7",
     "line": 2439
    },
    {
     "code": "r->m_raw_header[counter] = *pIn_buf_cur++",
     "line": 2439
    },
    {
     "code": "r->m_state = 39",
     "line": 2443
    },
    {
     "code": "r->m_state = 51",
     "line": 2447
    },
    {
     "code": "r->m_state = 52",
     "line": 2450
    },
    {
     "code": "r->m_state = 9",
     "line": 2460
    },
    {
     "code": "r->m_state = 38",
     "line": 2464
    },
    {
     "code": "r->m_state = 10",
     "line": 2475
    },
    {
     "code": "r->m_table_sizes[0] = 288",
     "line": 2483
    },
    {
     "code": "r->m_table_sizes[1] = 32",
     "line": 2484
    },
    {
     "code": "r->m_state = 11",
     "line": 2499
    },
    {
     "code": "r->m_table_sizes[counter] = bit_buf & ((1 << (\"\\05\\05\\04\"[counter])) - 1)",
     "line": 2499
    },
    {
     "code": "r->m_state = 14",
     "line": 2506
    },
    {
     "code": "r->m_tables[2].m_code_size[s_length_dezigzag[counter]] = (mz_uint8)s",
     "line": 2507
    },
    {
     "code": "r->m_table_sizes[2] = 19",
     "line": 2509
    },
    {
     "code": "r->m_state = 35",
     "line": 2531
    },
    {
     "code": "r->m_state = 16",
     "line": 2578
    },
    {
     "code": "r->m_len_codes[counter++] = (mz_uint8)dist",
     "line": 2581
    },
    {
     "code": "r->m_state = 17",
     "line": 2586
    },
    {
     "code": "r->m_state = 18",
     "line": 2589
    },
    {
     "code": "r->m_state = 21",
     "line": 2596
    },
    {
     "code": "r->m_state = 23",
     "line": 2609
    },
    {
     "code": "r->m_state = 24",
     "line": 2614
    },
    {
     "code": "r->m_state = 25",
     "line": 2693
    },
    {
     "code": "r->m_state = 26",
     "line": 2697
    },
    {
     "code": "r->m_state = 27",
     "line": 2703
    },
    {
     "code": "r->m_state = 37",
     "line": 2710
    },
    {
     "code": "r->m_state = 53",
     "line": 2721
    },
    {
     "code": "r->m_state = 32",
     "line": 2776
    },
    {
     "code": "r->m_state = 41",
     "line": 2791
    },
    {
     "code": "r->m_state = 42",
     "line": 2793
    },
    {
     "code": "r->m_z_adler32 = (r->m_z_adler32 << 8) ",
     "line": 2794
    },
    {
     "code": "r->m_state = 34",
     "line": 2797
    },
    {
     "code": "r->m_num_bits = num_bits",
     "line": 2813
    },
    {
     "code": "r->m_bit_buf = bit_buf & (tinfl_bit_buf_t)((((mz_uint64)1) << num_bits) - (mz_uint64)1)",
     "line": 2814
    },
    {
     "code": "r->m_dist = dist",
     "line": 2815
    },
    {
     "code": "r->m_counter = counter",
     "line": 2816
    },
    {
     "code": "r->m_num_extra = num_extra",
     "line": 2817
    },
    {
     "code": "r->m_dist_from_out_buf_start = dist_from_out_buf_start",
     "line": 2818
    },
    {
     "code": "r->m_check_adler32 = (s2 << 16) + s1",
     "line": 2846
    }
   ],
   "entity_decl": {
    "line": 2381,
    "type": "tinfl_decompressor*"
   },
   "entity_name_cpg": "r",
   "func_lines": [
    2381,
    2851
   ],
   "func_params": {
    "names": [
     "r",
     "pIn_buf_next",
     "pIn_buf_size",
     "pOut_buf_start",
     "pOut_buf_next",
     "pOut_buf_size",
     "decomp_flags"
    ],
    "types": [
     "tinfl_decompressor*",
     "mz_uint8*",
     "size_t*",
     "mz_uint8*",
     "mz_uint8*",
     "size_t*",
     "mz_uint32"
    ]
   },
   "guards": [
    {
     "code": "pOut_buf_next < pOut_buf_start",
     "line": 2398
    },
    {
     "code": "(r->m_zhdr0 * 256 + r->m_zhdr1) % 31 != 0",
     "line": 2418
    },
    {
     "code": "(r->m_zhdr0 & 15) != 8",
     "line": 2418
    },
    {
     "code": "(1U << (8U + (r->m_zhdr0 >> 4))) > 32768U",
     "line": 2420
    },
    {
     "code": "(out_buf_size_mask + 1) < (size_t)(1U << (8U + (r->m_zhdr0 >> 4)))",
     "line": 2420
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2429
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2429
    },
    {
     "code": "r->m_type == 0",
     "line": 2431
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2433
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2433
    },
    {
     "code": "counter < 4",
     "line": 2434
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2437
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2437
    },
    {
     "code": "(counter = (r->m_raw_header[0] ",
     "line": 2441
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2447
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2447
    },
    {
     "code": "(((((size_t)(pOut_buf_end - pOut_buf_cur)) < ((size_t)(pIn_buf_end - pIn_buf_cur))) ? ((size_t)(pOut_buf_end - pOut_buf_cur)) : ((size_t)(pIn_buf_end",
     "line": 2466
    },
    {
     "code": "((size_t)(pOut_buf_end - pOut_buf_cur)) < ((size_t)(pIn_buf_end - pIn_buf_cur))",
     "line": 2466
    },
    {
     "code": "((size_t)(pOut_buf_end - pOut_buf_cur)) < ((size_t)(pIn_buf_end - pIn_buf_cur))",
     "line": 2466
    },
    {
     "code": "r->m_type == 3",
     "line": 2473
    },
    {
     "code": "r->m_type == 1",
     "line": 2479
    },
    {
     "code": "counter < 3",
     "line": 2497
    },
    {
     "code": "num_bits < (mz_uint)(\"\\05\\05\\04\"[counter])",
     "line": 2499
    },
    {
     "code": "num_bits < (mz_uint)(\"\\05\\05\\04\"[counter])",
     "line": 2499
    },
    {
     "code": "counter < r->m_table_sizes[2]",
     "line": 2503
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2506
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2506
    },
    {
     "code": "i < r->m_table_sizes[r->m_type]",
     "line": 2520
    },
    {
     "code": "65536 != total",
     "line": 2529
    },
    {
     "code": "used_syms > 1",
     "line": 2529
    },
    {
     "code": "sym_index < r->m_table_sizes[r->m_type]",
     "line": 2533
    },
    {
     "code": "l > 0",
     "line": 2539
    },
    {
     "code": "rev_code < TINFL_FAST_LOOKUP_SIZE",
     "line": 2544
    },
    {
     "code": "0 == (tree_cur = pTable->m_look_up[rev_code & (TINFL_FAST_LOOKUP_SIZE - 1)])",
     "line": 2551
    },
    {
     "code": "j > (TINFL_FAST_LOOKUP_BITS + 1)",
     "line": 2558
    },
    {
     "code": "r->m_type == 2",
     "line": 2573
    },
    {
     "code": "counter < (r->m_table_sizes[0] + r->m_table_sizes[1])",
     "line": 2575
    },
    {
     "code": "num_bits < 15",
     "line": 2578
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 2",
     "line": 2578
    },
    {
     "code": "num_bits > TINFL_FAST_LOOKUP_BITS",
     "line": 2578
    },
    {
     "code": "temp < 0",
     "line": 2578
    },
    {
     "code": "num_bits < 15",
     "line": 2578
    },
    {
     "code": "temp < 0",
     "line": 2578
    },
    {
     "code": "dist < 16",
     "line": 2579
    },
    {
     "code": "dist == 16",
     "line": 2584
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2589
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2589
    },
    {
     "code": "dist == 16",
     "line": 2591
    },
    {
     "code": "(r->m_table_sizes[0] + r->m_table_sizes[1]) != counter",
     "line": 2594
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 4",
     "line": 2607
    },
    {
     "code": "(pOut_buf_end - pOut_buf_cur) < 2",
     "line": 2607
    },
    {
     "code": "num_bits < 15",
     "line": 2609
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 2",
     "line": 2609
    },
    {
     "code": "num_bits > TINFL_FAST_LOOKUP_BITS",
     "line": 2609
    },
    {
     "code": "temp < 0",
     "line": 2609
    },
    {
     "code": "num_bits < 15",
     "line": 2609
    },
    {
     "code": "temp < 0",
     "line": 2609
    },
    {
     "code": "num_bits < 15",
     "line": 2630
    },
    {
     "code": "sym2 < 0",
     "line": 2645
    },
    {
     "code": "num_bits < 15",
     "line": 2654
    },
    {
     "code": "sym2 < 0",
     "line": 2669
    },
    {
     "code": "(counter &= 511) == 256",
     "line": 2685
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2693
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2693
    },
    {
     "code": "num_bits < 15",
     "line": 2697
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 2",
     "line": 2697
    },
    {
     "code": "num_bits > TINFL_FAST_LOOKUP_BITS",
     "line": 2697
    },
    {
     "code": "temp < 0",
     "line": 2697
    },
    {
     "code": "num_bits < 15",
     "line": 2697
    },
    {
     "code": "temp < 0",
     "line": 2697
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2703
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2703
    },
    {
     "code": "dist > dist_from_out_buf_start",
     "line": 2708
    },
    {
     "code": "(MZ_MAX(pOut_buf_cur, pSrc) + counter) > pOut_buf_end",
     "line": 2715
    },
    {
     "code": "(pOut_buf_cur) > (pSrc)",
     "line": 2715
    },
    {
     "code": "counter>2",
     "line": 2754
    },
    {
     "code": "counter > 0",
     "line": 2763
    },
    {
     "code": "counter > 1",
     "line": 2766
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2776
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2776
    },
    {
     "code": "pIn_buf_cur > pIn_buf_next",
     "line": 2777
    },
    {
     "code": "counter < 4",
     "line": 2787
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2791
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2791
    },
    {
     "code": "status != TINFL_STATUS_NEEDS_MORE_INPUT",
     "line": 2805
    },
    {
     "code": "status != TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS",
     "line": 2805
    },
    {
     "code": "pIn_buf_cur > pIn_buf_next",
     "line": 2807
    },
    {
     "code": "i + 7 < block_len",
     "line": 2829
    },
    {
     "code": "i < block_len",
     "line": 2840
    },
    {
     "code": "status == TINFL_STATUS_DONE",
     "line": 2847
    },
    {
     "code": "r->m_check_adler32 != r->m_z_adler32",
     "line": 2847
    }
   ],
   "line_call_count": 26,
   "line_calls": [
    {
     "code": "TINFL_GET_BITS(3, r->m_final, 3)",
     "name": "TINFL_GET_BITS",
     "nargs": 3
    },
    {
     "code": "r->m_final",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "(mz_uint)(3)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "pIn_buf_cur >= pIn_buf_end",
     "name": "<operator>.greaterEqualsThan",
     "nargs": 2
    },
    {
     "code": "status = (decomp_flags & TINFL_FLAG_HAS_MORE_INPUT) ? TINFL_STATUS_NEEDS_MORE_INPUT : TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(decomp_flags & TINFL_FLAG_HAS_MORE_INPUT) ? TINFL_STATUS_NEEDS_MORE_INPUT : TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS",
     "name": "<operator>.conditional",
     "nargs": 3
    },
    {
     "code": "decomp_flags & TINFL_FLAG_HAS_MORE_INPUT",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "r->m_state = 3",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "r->m_state",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "c = *pIn_buf_cur++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*pIn_buf_cur++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "pIn_buf_cur++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "bit_buf ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "((tinfl_bit_buf_t)c) << num_bits",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(tinfl_bit_buf_t)c",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "num_bits += 8",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "(mz_uint)(3)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "r->m_final = bit_buf & ((1 << (3)) - 1)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "r->m_final",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "bit_buf & ((1 << (3)) - 1)",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(1 << (3)) - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "1 << (3)",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "bit_buf >>= (3)",
     "name": "<operators>.assignmentArithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "num_bits -= (3)",
     "name": "<operator>.assignmentMinus",
     "nargs": 2
    }
   ],
   "line_ids": [
    "r",
    "num_bits",
    "pIn_buf_cur",
    "pIn_buf_end",
    "status",
    "decomp_flags",
    "TINFL_FLAG_HAS_MORE_INPUT",
    "TINFL_STATUS_NEEDS_MORE_INPUT",
    "TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS",
    "c",
    "bit_buf"
   ],
   "osv_id": "ARVO-42490298",
   "sites": [
    {
     "args": "31",
     "callee": "<operator>.alloc",
     "code": "s_length_base[31] = { 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258, 0, 0 }",
     "line": 2383
    },
    {
     "args": "31",
     "callee": "<operator>.alloc",
     "code": "s_length_extra[31] = { 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0, 0, 0 }",
     "line": 2384
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "s_dist_base[32] = { 1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16",
     "line": 2385
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "s_dist_extra[32] = { 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13 }",
     "line": 2386
    },
    {
     "args": "19",
     "callee": "<operator>.alloc",
     "code": "s_length_dezigzag[19] = { 16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15 }",
     "line": 2387
    },
    {
     "args": "3",
     "callee": "<operator>.alloc",
     "code": "s_min_table_sizes[3] = { 257, 1, 4 }",
     "line": 2388
    },
    {
     "args": "17",
     "callee": "<operator>.alloc",
     "code": "next_code[17]",
     "line": 2515
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "total_syms[16]",
     "line": 2515
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tinfl_decompress"
  }
 },
 {
  "osv_id": "ARVO-42491082",
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
    "file": "/src/cryptofuzz-sp-math-all/util.cpp",
    "line": 346
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/4280861af059e4781cbe8012613a7f4d1786f9e1/ARVO-42491082/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_4280861af059.cpg",
   "testcase_size": 540
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
   "dedup_token": "sp_tohex--cryptofuzz::module::wolfCrypt_bignum::Bignum::ToDecString()--cryptofuzz::module::wolfCrypt_bignum::Bignum::ToComponentBignum()"
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
  "osv_id": "ARVO-42491208",
  "project": "wolfssl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": null,
  "sites": [],
  "crash": {
   "site": {
    "fn": null,
    "file": null,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/c482d160290c5cf314a3b10eba621dd37b6795a1/ARVO-42491208/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_c482d160290c.cpg",
   "testcase_size": 127
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "ato16--TLSX_CSR_Parse--TLSX_Parse"
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
  "osv_id": "ARVO-42491468",
  "project": "serenity",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "key",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/serenity/Libraries/LibTTF/Font.cpp",
    "line": 42,
    "size": null,
    "type": "u32"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "AK::ByteBufferImpl::ByteBufferImpl(void const*, unsigned long)",
    "file": "/src/serenity/Meta/Lagom/build/../../../AK/ByteBuffer.h",
    "line": 252
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 48,
    "fn": "TTF::be_u16(unsigned char const*)",
    "code": "key ^= (key >> 20) | key >> 20",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "TTF::be_u16(unsigned char const*)",
    "file": "/src/serenity/Libraries/LibTTF/Font.cpp",
    "line": 48
   },
   "code": "key ^= (key >> 20) | key >> 20",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "double_hash",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "u32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "key"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/df5ea97c51e63f84ce30e8db9d8617b035e2ac38/ARVO-42491468/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_df5ea97c51e6.cpg",
   "testcase_size": 16
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
   "dedup_token": "TTF::be_u16(unsigned char const*)--TTF::Font::load_from_offset(AK::ByteBuffer&&, unsigned int)--TTF::Font::load_from_memory(AK::ByteBuffer&, unsigned int)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "key = ~key + (key >> 23)",
     "line": 44
    }
   ],
   "entity_decl": {
    "line": 42,
    "type": "u32"
   },
   "entity_name_cpg": "key",
   "func_lines": [
    42,
    50
   ],
   "func_params": {
    "names": [
     "key"
    ],
    "types": [
     "u32"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "key ^= (key >> 20)",
     "name": "<operators>.assignmentXor",
     "nargs": 2
    },
    {
     "code": "key >> 20",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    }
   ],
   "line_ids": [
    "key"
   ],
   "osv_id": "ARVO-42491468",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "TTF::be_u16(unsigned char const*)"
  }
 },
 {
  "osv_id": "ARVO-42491502",
  "project": "c-blosc2",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
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
    "line": 134,
    "fn": "ZSTD_initDDict_internal",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_initDDict_internal",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/decompress/zstd_ddict.c",
    "line": 134
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 117791,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ZSTD_initDDict_internal",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/474ebf151be847186e6bc2c1381a8f7d4beff4dd/ARVO-42491502/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_474ebf151be8.cpg",
   "testcase_size": 27249
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
   "dedup_token": "__asan_memcpy--ZSTD_initDDict_internal--ZSTD_createDDict_advanced"
  },
  "deep": {
   "osv_id": "ARVO-42491502"
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
  "osv_id": "ARVO-42491572",
  "project": "openh264",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "DECODER_OPTION_END_OF_STREAM",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "line": 72
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 152,
    "fn": "WelsDec::CopyRectBlock4Cols(void*, void*, int, int, int, int)",
    "code": "DECODER_OPTION_END_OF_STREAM = 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::CopyRectBlock4Cols(void*, void*, int, int, int, int)",
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "line": 152
   },
   "code": "DECODER_OPTION_END_OF_STREAM = 1",
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<clinit>",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openh264/address/992c1c147175126c3fe7ab78216aa0395f9e6c71/ARVO-42491572/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_992c1c147175.cpg",
   "testcase_size": 339
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
   "dedup_token": "__asan_memcpy--WelsDec::CopyRectBlock4Cols(void*, void*, int, int, int, int)--WelsDec::GetColocatedMb(WelsDec::TagWelsDecoderContext*, unsigned int&, unsigned i"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "DECODER_OPTION_END_OF_STREAM = 1",
     "line": 152
    }
   ],
   "entity_name_cpg": "DECODER_OPTION_END_OF_STREAM",
   "func_lines": [
    151,
    -1
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "DECODER_OPTION_END_OF_STREAM = 1",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "DECODER_OPTION_END_OF_STREAM"
   ],
   "osv_id": "ARVO-42491572",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WelsDec::CopyRectBlock4Cols(void*, void*, int, int, int, int)"
  }
 },
 {
  "osv_id": "ARVO-42491640",
  "project": "matio",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "silent",
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
    "line": 477,
    "fn": "Mat_H5ReadVarInfo",
    "code": "silent  = 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_H5ReadVarInfo",
    "file": "/src/matio/src/mat73.c",
    "line": 477
   },
   "code": "silent  = 0",
   "access": {
    "dir": "READ",
    "width": 129,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_LogInitFunc",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/a47b7cd3aca70e9a0bddf8146eb4ab0cbd19c2c3/ARVO-42491640/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_a47b7cd3aca7.cpg",
   "testcase_size": 48243
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
   "dedup_token": "strlen--H5MM_strdup--H5O_attr_decode"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "silent  = 0",
     "line": 477
    }
   ],
   "entity_name_cpg": "silent",
   "func_lines": [
    467,
    479
   ],
   "func_params": {
    "names": [
     "prog_name",
     "log_func"
    ],
    "types": [
     "char*",
     "void"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "silent  = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "silent"
   ],
   "osv_id": "ARVO-42491640",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_H5ReadVarInfo"
  }
 },
 {
  "osv_id": "ARVO-42491649",
  "project": "matio",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "fp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 436,
    "type": "FILE*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5MM_malloc",
    "file": "/src/hdf5-1.12.0/src/H5MM.c",
    "line": 292
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(*mat)",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 483,
    "fn": "Mat_H5ReadVarInfo",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_H5ReadVarInfo",
    "file": "/src/matio/src/mat73.c",
    "line": 483
   },
   "code": "fclose(fp)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_H5ReadVarInfo",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/1ce8f2d1845ecdde19a35605cabdbb884776d52d/ARVO-42491649/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_1ce8f2d1845e.cpg",
   "testcase_size": 71761
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
   "dedup_token": "__asan_memcpy--H5MM_memcpy--H5O_attr_decode"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*fp = NULL",
     "line": 436
    },
    {
     "code": "fp = fopen(matname, \"rb\")",
     "line": 449
    },
    {
     "code": "fp = fopen(matname, \"r+b\")",
     "line": 461
    }
   ],
   "entity_decl": {
    "line": 436,
    "type": "FILE*"
   },
   "entity_name_cpg": "fp",
   "func_lines": [
    433,
    615
   ],
   "func_params": {
    "names": [
     "matname",
     "mode"
    ],
    "types": [
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "(mode & 0x01) == MAT_ACC_RDONLY",
     "line": 441
    },
    {
     "code": "(mode & 0x01) == MAT_ACC_RDWR",
     "line": 453
    },
    {
     "code": "NULL == mat",
     "line": 473
    },
    {
     "code": "NULL == mat->header",
     "line": 481
    },
    {
     "code": "NULL == mat->subsys_offset",
     "line": 488
    },
    {
     "code": "128 == bytesread",
     "line": 510
    },
    {
     "code": "tmp == 0x4d49",
     "line": 513
    },
    {
     "code": "tmp == 0x494d",
     "line": 515
    },
    {
     "code": "mat->version == 0x0100",
     "line": 521
    },
    {
     "code": "mat->version == 0x0200",
     "line": 521
    },
    {
     "code": "-1 != mat->byteswap",
     "line": 522
    },
    {
     "code": "mat->bof == -1L",
     "line": 524
    },
    {
     "code": "0 == mat->version",
     "line": 538
    },
    {
     "code": "NULL == var",
     "line": 559
    },
    {
     "code": "bytesread != 0",
     "line": 560
    },
    {
     "code": "NULL == mat",
     "line": 571
    },
    {
     "code": "mat->version == 0x0200",
     "line": 577
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "fclose(fp)",
     "name": "fclose",
     "nargs": 1
    }
   ],
   "line_ids": [
    "fp"
   ],
   "osv_id": "ARVO-42491649",
   "sites": [
    {
     "args": "sizeof(*mat)",
     "callee": "malloc",
     "code": "malloc(sizeof(*mat))",
     "line": 472
    },
    {
     "args": "128 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(128,sizeof(char))",
     "line": 480
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 482
    },
    {
     "args": "8 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(8,sizeof(char))",
     "line": 487
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 489
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 490
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 525
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 526
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 527
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 542
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 543
    },
    {
     "args": "var",
     "callee": "Mat_VarFree",
     "code": "Mat_VarFree(var)",
     "line": 566
    },
    {
     "args": "matname",
     "callee": "strdup",
     "code": "strdup(matname)",
     "line": 574
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_H5ReadVarInfo"
  }
 },
 {
  "osv_id": "ARVO-42491667",
  "project": "matio",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "place",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5MM_malloc",
    "file": "/src/hdf5-1.12.0/src/H5MM.c",
    "line": 292
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 534,
    "fn": "Mat_H5ReadVarInfo",
    "code": "place = EMSG | EMSG",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_H5ReadVarInfo",
    "file": "/src/matio/src/mat73.c",
    "line": 534
   },
   "code": "place = EMSG | EMSG",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "getopt_internal",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "place != nargv[optind]",
   "guard_count": 1,
   "control_structures": "IF:366,IF:375,ELSE:377,IF:377,IF:385,IF:392,IF:396,IF:399,IF:401,IF:403,ELSE:409,IF:409"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/1ce8f2d1845ecdde19a35605cabdbb884776d52d/ARVO-42491667/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_1ce8f2d1845e.cpg",
   "testcase_size": 33657
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
   "dedup_token": "H5O__sdspace_decode--H5O_sdspace_shared_decode--H5O_attr_decode"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "place = EMSG",
     "line": 402
    },
    {
     "code": "place = nargv[optind]",
     "line": 419
    },
    {
     "code": "place = EMSG",
     "line": 425
    },
    {
     "code": "place = EMSG",
     "line": 463
    },
    {
     "code": "place = EMSG",
     "line": 501
    },
    {
     "code": "place = EMSG",
     "line": 534
    },
    {
     "code": "place = nargv[optind]",
     "line": 540
    },
    {
     "code": "place = EMSG",
     "line": 546
    },
    {
     "code": "place = EMSG",
     "line": 558
    },
    {
     "code": "place = EMSG",
     "line": 566
    }
   ],
   "entity_name_cpg": "place",
   "func_lines": [
    358,
    571
   ],
   "func_params": {
    "names": [
     "nargc",
     "nargv",
     "options",
     "long_options",
     "idx",
     "flags"
    ],
    "types": [
     "int",
     "char*const*",
     "char*",
     "option*",
     "int*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "options == NULL",
     "line": 366
    },
    {
     "code": "getenv(\"POSIXLY_CORRECT\") != NULL",
     "line": 373
    },
    {
     "code": "*options == '-'",
     "line": 375
    },
    {
     "code": "*options == '+'",
     "line": 377
    },
    {
     "code": "*options == '+'",
     "line": 385
    },
    {
     "code": "*options == '-'",
     "line": 385
    },
    {
     "code": "optind == 0",
     "line": 392
    },
    {
     "code": "nonopt_end != -1",
     "line": 403
    },
    {
     "code": "nonopt_start != -1",
     "line": 409
    },
    {
     "code": "*(place = nargv[optind]) != '-'",
     "line": 419
    },
    {
     "code": "place[1] == '\\0'",
     "line": 421
    },
    {
     "code": "nonopt_start == -1",
     "line": 442
    },
    {
     "code": "nonopt_end != -1",
     "line": 444
    },
    {
     "code": "nonopt_start != -1",
     "line": 455
    },
    {
     "code": "nonopt_end == -1",
     "line": 455
    },
    {
     "code": "place[1] != '\\0'",
     "line": 461
    },
    {
     "code": "*++place == '-'",
     "line": 461
    },
    {
     "code": "place[1] == '\\0'",
     "line": 461
    },
    {
     "code": "nonopt_end != -1",
     "line": 468
    },
    {
     "code": "long_options != NULL",
     "line": 484
    },
    {
     "code": "place != nargv[optind]",
     "line": 484
    },
    {
     "code": "*place == '-'",
     "line": 485
    },
    {
     "code": "*place == '-'",
     "line": 490
    },
    {
     "code": "*place != ':'",
     "line": 495
    },
    {
     "code": "strchr(options, *place) != NULL",
     "line": 495
    },
    {
     "code": "optchar != -1",
     "line": 500
    },
    {
     "code": "(optchar = (int)*place++) == (int)':'",
     "line": 506
    },
    {
     "code": "optchar == (int)'-'",
     "line": 507
    },
    {
     "code": "*place != '\\0'",
     "line": 507
    },
    {
     "code": "(oli = (char*)strchr(options, optchar)) == NULL",
     "line": 508
    },
    {
     "code": "optchar == (int)'-'",
     "line": 514
    },
    {
     "code": "*place == '\\0'",
     "line": 514
    },
    {
     "code": "*options != ':'",
     "line": 519
    },
    {
     "code": "long_options != NULL",
     "line": 529
    },
    {
     "code": "optchar == 'W'",
     "line": 529
    },
    {
     "code": "oli[1] == ';'",
     "line": 529
    },
    {
     "code": "*options != ':'",
     "line": 535
    },
    {
     "code": "*options == ':'",
     "line": 538
    },
    {
     "code": "*++oli != ':'",
     "line": 549
    },
    {
     "code": "oli[1] != ':'",
     "line": 556
    },
    {
     "code": "*options != ':'",
     "line": 559
    },
    {
     "code": "*options == ':'",
     "line": 562
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "place = EMSG",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "EMSG",
     "name": "EMSG",
     "nargs": 0
    }
   ],
   "line_ids": [
    "place"
   ],
   "osv_id": "ARVO-42491667",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_H5ReadVarInfo"
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