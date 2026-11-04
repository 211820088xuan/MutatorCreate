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
  "osv_id": "ARVO-42479930",
  "project": "lwan",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "chunk",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lwan/src/lib/lwan-template.c",
    "line": 1002,
    "size": null,
    "type": "chunk*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "lwan_array_append_heap",
    "file": "/src/lwan/src/lib/lwan-array.c",
    "line": 80
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(*cd)",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1007,
    "fn": "post_process_template",
    "code": "chunk->action == ACTION_LAST | chunk->action",
    "origin": "report:crash"
   },
   {
    "code": "malloc(sizeof(*cd))",
    "fn": "post_process_template",
    "kind": "malloc",
    "line": 1017,
    "origin": "cpg",
    "args": "sizeof(*cd)"
   },
   {
    "code": "malloc(sizeof(*cd))",
    "fn": "post_process_template",
    "kind": "malloc",
    "line": 1050,
    "origin": "cpg",
    "args": "sizeof(*cd)"
   }
  ],
  "crash": {
   "site": {
    "fn": "post_process_template",
    "file": "/src/lwan/src/lib/lwan-template.c",
    "line": 1007
   },
   "code": "chunk->action == ACTION_LAST | chunk->action",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "post_process_template",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "chunk < ((typeof)(&parser->chunks)->base.base + (&parser->chunks)->bas | chunk->action == ACTION_LAST | chunk->action == ACTION_LAST",
   "guard_count": 5,
   "control_structures": "FOR:1004,IF:1005,FOR:1006,IF:1007,IF:1012,BREAK:1014,IF:1018,ELSE:1027,IF:1027,FOR:1030,IF:1031,IF:1036"
  },
  "call_chain": [],
  "types": {
   "entity_type": "chunk*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lwan/address/f905fa80d71d6a0f6d773938f39e3f9d7558d537/ARVO-42479930/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_f905fa80d71d.cpg",
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
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "post_process_template--parser_shutdown--parse_string"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "chunk = (&parser->chunks)->base.base",
     "line": 1004
    },
    {
     "code": "chunk = prev_chunk + 1",
     "line": 1026
    },
    {
     "code": "chunk->data =",
     "line": 1043
    },
    {
     "code": "chunk = prev_chunk + 1",
     "line": 1063
    },
    {
     "code": "chunk->action = ACTION_VARIABLE_STR_ESCAPE",
     "line": 1070
    },
    {
     "code": "chunk->action = ACTION_VARIABLE_STR",
     "line": 1072
    },
    {
     "code": "chunk->data = (void *)(uintptr_t)descriptor->offset",
     "line": 1073
    }
   ],
   "entity_decl": {
    "line": 1002,
    "type": "chunk*"
   },
   "entity_name_cpg": "chunk",
   "func_lines": [
    999,
    1089
   ],
   "func_params": {
    "names": [
     "parser"
    ],
    "types": [
     "parser*"
    ]
   },
   "guards": [
    {
     "code": "chunk < ((typeof)(&parser->chunks)->base.base + (&parser->chunks)->base.elements)",
     "line": 1004
    },
    {
     "code": "chunk->action == ACTION_IF_VARIABLE_NOT_EMPTY",
     "line": 1005
    },
    {
     "code": "chunk->action == ACTION_LAST",
     "line": 1007
    },
    {
     "code": "chunk->action == ACTION_END_IF_VARIABLE_NOT_EMPTY",
     "line": 1012
    },
    {
     "code": "chunk->data == prev_chunk->data",
     "line": 1013
    },
    {
     "code": "chunk->action == ACTION_START_ITER",
     "line": 1027
    },
    {
     "code": "chunk->action == ACTION_LAST",
     "line": 1031
    },
    {
     "code": "chunk->action == ACTION_END_ITER",
     "line": 1036
    },
    {
     "code": "prev_index == start_index",
     "line": 1041
    },
    {
     "code": "chunk->action == ACTION_LAST",
     "line": 1058
    },
    {
     "code": "chunk->action == ACTION_VARIABLE",
     "line": 1064
    },
    {
     "code": "descriptor->append_to_strbuf == lwan_append_str_to_strbuf",
     "line": 1068
    },
    {
     "code": "chunk->action == ACTION_LAST",
     "line": 1081
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "chunk->action == ACTION_LAST",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "chunk->action",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "chunk",
    "ACTION_LAST"
   ],
   "osv_id": "ARVO-42479930",
   "sites": [
    {
     "args": "sizeof(*cd)",
     "callee": "malloc",
     "code": "malloc(sizeof(*cd))",
     "line": 1017
    },
    {
     "args": "sizeof(*cd)",
     "callee": "malloc",
     "code": "malloc(sizeof(*cd))",
     "line": 1050
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "post_process_template"
  }
 },
 {
  "osv_id": "ARVO-42479939",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_dec",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 438,
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
    "line": 510,
    "fn": "ih264d_decode_slice_thread",
    "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_decode_slice_thread",
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 510
   },
   "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_decode_slice_thread",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:453,IF:459,BREAK:461,ELSE:464,IF:465,FOR:468,ELSE:470,IF:470,ELSE:483,IF:507,IF:549,WHILE:560"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/25e615b9cbd4ed41f9586dd82f947e72b0101f8b/ARVO-42479939/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_25e615b9cbd4.cpg",
   "testcase_size": 44
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
   "dedup_token": "ih264d_decode_slice_thread--ih264d_decode_picture_thread--start_thread"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ps_dec->u4_fmt_conv_num_rows =",
     "line": 473
    },
    {
     "code": "ps_dec->i2_dec_thread_mb_y = i16_mb_y",
     "line": 502
    },
    {
     "code": "ps_dec->cur_dec_mb_num = u2_first_mb_in_slice << u1_mbaff",
     "line": 505
    },
    {
     "code": "ps_dec->pv_proc_tu_coeff_data =",
     "line": 509
    },
    {
     "code": "ps_dec->p_mc_dec_thread = ih264d_motion_compensate_bp",
     "line": 539
    },
    {
     "code": "ps_dec->p_form_mb_part_info_thread = ih264d_form_mb_part_info_bp",
     "line": 540
    },
    {
     "code": "ps_dec->p_mc_dec_thread = ih264d_motion_compensate_mp",
     "line": 551
    },
    {
     "code": "ps_dec->p_form_mb_part_info_thread = ih264d_form_mb_part_info_mp",
     "line": 552
    },
    {
     "code": "ps_dec->u4_cur_slice_decode_done = 0",
     "line": 557
    }
   ],
   "entity_decl": {
    "line": 438,
    "type": "dec_struct_t*"
   },
   "entity_name_cpg": "ps_dec",
   "func_lines": [
    438,
    591
   ],
   "func_params": {
    "names": [
     "ps_dec"
    ],
    "types": [
     "dec_struct_t*"
    ]
   },
   "guards": [
    {
     "code": "nop_cnt > 0",
     "line": 465
    },
    {
     "code": "nop_i < 128",
     "line": 468
    },
    {
     "code": "2 == ps_dec->u4_num_cores",
     "line": 470
    },
    {
     "code": "ps_dec->u4_fmt_conv_cur_row < ps_dec->s_disp_frame_info.u4_y_ht",
     "line": 471
    },
    {
     "code": "16 < (ps_dec->s_disp_frame_info.u4_y_ht - ps_dec->u4_fmt_conv_cur_row)",
     "line": 474
    },
    {
     "code": "ps_dec->u4_num_cores == 2",
     "line": 507
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_field_pic_flag == 0",
     "line": 544
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_mbaff_frame_flag == 0",
     "line": 545
    },
    {
     "code": "ps_dec->ps_decode_cur_slice->slice_type != B_SLICE",
     "line": 546
    },
    {
     "code": "ps_dec->ps_cur_pps->u1_wted_pred_flag == 0",
     "line": 547
    },
    {
     "code": "uc_nofield_nombaff == 0",
     "line": 549
    },
    {
     "code": "ps_dec->u4_cur_slice_decode_done != 1",
     "line": 560
    },
    {
     "code": "ret != OK",
     "line": 587
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_decode_cur_slice",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ps_dec"
   ],
   "osv_id": "ARVO-42479939",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_decode_slice_thread"
  }
 },
 {
  "osv_id": "ARVO-42480014",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_dec",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 438,
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
    "line": 510,
    "fn": "ih264d_decode_slice_thread",
    "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_decode_slice_thread",
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 510
   },
   "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_decode_slice_thread",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:453,IF:459,BREAK:461,ELSE:464,IF:465,FOR:468,ELSE:470,IF:470,ELSE:483,IF:507,IF:549,WHILE:560"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/25e615b9cbd4ed41f9586dd82f947e72b0101f8b/ARVO-42480014/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_25e615b9cbd4.cpg",
   "testcase_size": 54
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
   "dedup_token": "ih264d_decode_slice_thread--ih264d_decode_picture_thread--__asan::AsanThread::ThreadStart(unsigned long long, __sanitizer::atomic_uintptr_t*)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ps_dec->u4_fmt_conv_num_rows =",
     "line": 473
    },
    {
     "code": "ps_dec->i2_dec_thread_mb_y = i16_mb_y",
     "line": 502
    },
    {
     "code": "ps_dec->cur_dec_mb_num = u2_first_mb_in_slice << u1_mbaff",
     "line": 505
    },
    {
     "code": "ps_dec->pv_proc_tu_coeff_data =",
     "line": 509
    },
    {
     "code": "ps_dec->p_mc_dec_thread = ih264d_motion_compensate_bp",
     "line": 539
    },
    {
     "code": "ps_dec->p_form_mb_part_info_thread = ih264d_form_mb_part_info_bp",
     "line": 540
    },
    {
     "code": "ps_dec->p_mc_dec_thread = ih264d_motion_compensate_mp",
     "line": 551
    },
    {
     "code": "ps_dec->p_form_mb_part_info_thread = ih264d_form_mb_part_info_mp",
     "line": 552
    },
    {
     "code": "ps_dec->u4_cur_slice_decode_done = 0",
     "line": 557
    }
   ],
   "entity_decl": {
    "line": 438,
    "type": "dec_struct_t*"
   },
   "entity_name_cpg": "ps_dec",
   "func_lines": [
    438,
    591
   ],
   "func_params": {
    "names": [
     "ps_dec"
    ],
    "types": [
     "dec_struct_t*"
    ]
   },
   "guards": [
    {
     "code": "nop_cnt > 0",
     "line": 465
    },
    {
     "code": "nop_i < 128",
     "line": 468
    },
    {
     "code": "2 == ps_dec->u4_num_cores",
     "line": 470
    },
    {
     "code": "ps_dec->u4_fmt_conv_cur_row < ps_dec->s_disp_frame_info.u4_y_ht",
     "line": 471
    },
    {
     "code": "16 < (ps_dec->s_disp_frame_info.u4_y_ht - ps_dec->u4_fmt_conv_cur_row)",
     "line": 474
    },
    {
     "code": "ps_dec->u4_num_cores == 2",
     "line": 507
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_field_pic_flag == 0",
     "line": 544
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_mbaff_frame_flag == 0",
     "line": 545
    },
    {
     "code": "ps_dec->ps_decode_cur_slice->slice_type != B_SLICE",
     "line": 546
    },
    {
     "code": "ps_dec->ps_cur_pps->u1_wted_pred_flag == 0",
     "line": 547
    },
    {
     "code": "uc_nofield_nombaff == 0",
     "line": 549
    },
    {
     "code": "ps_dec->u4_cur_slice_decode_done != 1",
     "line": 560
    },
    {
     "code": "ret != OK",
     "line": 587
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_decode_cur_slice",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ps_dec"
   ],
   "osv_id": "ARVO-42480014",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_decode_slice_thread"
  }
 },
 {
  "osv_id": "ARVO-42480062",
  "project": "wireshark",
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
    "line": 168,
    "fn": "bytes_to_hexstr_punct",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bytes_to_hexstr_punct",
    "file": "/src/wireshark/epan/to_str.c",
    "line": 168
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bytes_to_hexstr_punct",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wireshark/address/7519c077d0d27c5e8c87c6df1ab19c3d172df45a/ARVO-42480062/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_7519c077d0d2.cpg",
   "testcase_size": 279
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
   "dedup_token": "bytes_to_hexstr_punct--bytestring_to_str--dissect_1722_acf_lin"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bytes_to_hexstr_punct"
  }
 },
 {
  "osv_id": "ARVO-42480096",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/amazon_video.c",
    "line": 33,
    "size": null,
    "type": "ndpi_packet_struct*"
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
    "line": 39,
    "fn": "ndpi_check_amazon_video",
    "code": "packet->payload[1] == 0xED | packet->payload[1] | packet->payload",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_amazon_video",
    "file": "/src/ndpi/src/lib/protocols/amazon_video.c",
    "line": 39
   },
   "code": "packet->payload[1] == 0xED | packet->payload[1] | packet->payload",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_amazon_video",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:37,ELSE:47,IF:47,ELSE:55"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_packet_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/ead0325debc96b2d134a625b4fac184a979ccc5a/ARVO-42480096/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_ead0325debc9.cpg",
   "testcase_size": 81
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
   "dedup_token": "ndpi_check_amazon_video--ndpi_search_amazon_video--check_ndpi_tcp_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 33
    }
   ],
   "entity_decl": {
    "line": 33,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    30,
    58
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
     "code": "packet->tcp != NULL",
     "line": 37
    },
    {
     "code": "packet->payload[0] == 0xFE",
     "line": 38
    },
    {
     "code": "packet->payload[1] == 0xED",
     "line": 39
    },
    {
     "code": "packet->payload[2] == 0xFA",
     "line": 40
    },
    {
     "code": "packet->payload[3] == 0xCE",
     "line": 41
    },
    {
     "code": "packet->udp != NULL",
     "line": 47
    },
    {
     "code": "packet->payload[0] == 0xDE",
     "line": 48
    },
    {
     "code": "packet->payload[1] == 0xAD",
     "line": 49
    },
    {
     "code": "packet->payload[2] == 0xBE",
     "line": 50
    },
    {
     "code": "packet->payload[3] == 0xEF",
     "line": 51
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "packet->payload[1] == 0xED",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet"
   ],
   "osv_id": "ARVO-42480096",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_check_amazon_video"
  }
 },
 {
  "osv_id": "ARVO-42480282",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 203,
    "size": null,
    "type": "char*"
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
   "size_expr_cpg": "JA3_STR_LEN",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 584,
    "fn": "getTLScertificate",
    "code": "strncpy(buffer, (char*)&packet->payload[offset+extension | (char*)&packet->payload[offset+extension_offset+5] | &packet->payload[offset+extension_offset+5] | packet->payload[offset+extension_offset+5]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "getTLScertificate",
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 584
   },
   "code": "strncpy(buffer, (char*)&packet->payload[offset+extension | (char*)&packet->payload[offset+extension_offset+5] | &packet->payload[offset+extension_offset+5] | packet->payload[offset+extension_offset+5]",
   "access": {
    "dir": "READ",
    "width": 6,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "getTLScertificate",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "offset >= (packet->payload_packet_len+4) | j<len | offset < total_len",
   "guard_count": 6,
   "control_structures": "IF:213,IF:215,IF:238,IF:242,ELSE:246,IF:257,IF:261,IF:268,IF:274,ELSE:277,IF:281,IF:295"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "flow",
   "buffer",
   "buffer_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/d0e7e6955293b656e1a1d7b01aebc1b5beefe711/ARVO-42480282/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_d0e7e6955293.cpg",
   "testcase_size": 111
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
   "dedup_token": "strncpy--getTLScertificate--tlsDetectProtocolFromCertificate"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buffer[len] = '\\0'",
     "line": 412
    },
    {
     "code": "buffer[len] = '\\0'",
     "line": 585
    }
   ],
   "entity_decl": {
    "line": 203,
    "type": "char*"
   },
   "entity_name_cpg": "buffer",
   "func_lines": [
    201,
    742
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow",
     "buffer",
     "buffer_len"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*",
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "packet->payload[1] != 0xfe",
     "line": 215
    },
    {
     "code": "packet->payload[2] != 0xff",
     "line": 216
    },
    {
     "code": "packet->payload[2] != 0xfd",
     "line": 216
    },
    {
     "code": "packet->payload[0] == 0x16",
     "line": 238
    },
    {
     "code": "total_len > packet->payload_packet_len",
     "line": 257
    },
    {
     "code": "total_len > 4",
     "line": 261
    },
    {
     "code": "handshake_protocol == 0x02",
     "line": 268
    },
    {
     "code": "handshake_protocol == 0x0b",
     "line": 269
    },
    {
     "code": "handshake_protocol == 0x02",
     "line": 281
    },
    {
     "code": "tls_version < 0x7F15",
     "line": 298
    },
    {
     "code": "i<extension_len",
     "line": 318
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 326
    },
    {
     "code": "extension_id == 43",
     "line": 334
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 351
    },
    {
     "code": "i > 0",
     "line": 352
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 358
    },
    {
     "code": "i > 0",
     "line": 359
    },
    {
     "code": "i<16",
     "line": 373
    },
    {
     "code": "i < packet->payload_packet_len-3",
     "line": 386
    },
    {
     "code": "packet->payload[i] == 0x04",
     "line": 387
    },
    {
     "code": "packet->payload[i+1] == 0x03",
     "line": 387
    },
    {
     "code": "packet->payload[i+2] == 0x0c",
     "line": 387
    },
    {
     "code": "packet->payload[i] == 0x04",
     "line": 388
    },
    {
     "code": "packet->payload[i+1] == 0x03",
     "line": 388
    },
    {
     "code": "packet->payload[i+2] == 0x13",
     "line": 388
    },
    {
     "code": "packet->payload[i] == 0x55",
     "line": 389
    },
    {
     "code": "packet->payload[i+1] == 0x04",
     "line": 389
    },
    {
     "code": "packet->payload[i+2] == 0x03",
     "line": 389
    },
    {
     "code": "packet->payload[i] == 0x55",
     "line": 392
    },
    {
     "code": "num_found != 2",
     "line": 395
    },
    {
     "code": "(server_len+i+3) < packet->payload_packet_len",
     "line": 398
    },
    {
     "code": "begin < server_len",
     "line": 402
    },
    {
     "code": "j<len",
     "line": 415
    },
    {
     "code": "buffer[j] == '.'",
     "line": 419
    },
    {
     "code": "subproto != NDPI_PROTOCOL_UNKNOWN",
     "line": 444
    },
    {
     "code": "handshake_protocol == 0x01",
     "line": 453
    },
    {
     "code": "i<cipher_len",
     "line": 489
    },
    {
     "code": "*id == 0",
     "line": 495
    },
    {
     "code": "packet->payload[cipher_offset+i] != packet->payload[cipher_offset+i+1]",
     "line": 495
    },
    {
     "code": "ja3.num_cipher < MAX_NUM_JA3",
     "line": 501
    },
    {
     "code": "offset < total_len",
     "line": 524
    },
    {
     "code": "offset < total_len",
     "line": 539
    },
    {
     "code": "extension_offset < extensions_len",
     "line": 553
    },
    {
     "code": "extension_id == 0",
     "line": 566
    },
    {
     "code": "packet->payload[extn_off] != packet->payload[extn_off+1]",
     "line": 566
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 569
    },
    {
     "code": "extension_id == 0",
     "line": 579
    },
    {
     "code": "extension_id == 10",
     "line": 593
    },
    {
     "code": "i<extension_len-2",
     "line": 601
    },
    {
     "code": "s_group == 0",
     "line": 607
    },
    {
     "code": "packet->payload[s_offset+i] != packet->payload[s_offset+i+1]",
     "line": 607
    },
    {
     "code": "ja3.num_elliptic_curve < MAX_NUM_JA3",
     "line": 609
    },
    {
     "code": "extension_id == 11",
     "line": 627
    },
    {
     "code": "(s_offset+extension_len) < total_len",
     "line": 633
    },
    {
     "code": "i<extension_len-1",
     "line": 634
    },
    {
     "code": "ja3.num_elliptic_curve_point_format < MAX_NUM_JA3",
     "line": 641
    },
    {
     "code": "extension_id == 43",
     "line": 656
    },
    {
     "code": "version_len == (extension_len-1)",
     "line": 659
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 683
    },
    {
     "code": "i > 0",
     "line": 685
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 692
    },
    {
     "code": "i > 0",
     "line": 694
    },
    {
     "code": "i<ja3.num_elliptic_curve",
     "line": 700
    },
    {
     "code": "i > 0",
     "line": 702
    },
    {
     "code": "i<ja3.num_elliptic_curve_point_format",
     "line": 706
    },
    {
     "code": "i > 0",
     "line": 708
    },
    {
     "code": "i<16",
     "line": 718
    },
    {
     "code": "offset == total_len",
     "line": 730
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "strncpy(buffer, (char*)&packet->payload[offset+extension_offset+5], len)",
     "name": "strncpy",
     "nargs": 3
    },
    {
     "code": "(char*)&packet->payload[offset+extension_offset+5]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "&packet->payload[offset+extension_offset+5]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "packet->payload[offset+extension_offset+5]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "offset+extension_offset+5",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "offset+extension_offset",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buffer",
    "packet",
    "offset",
    "extension_offset",
    "len"
   ],
   "osv_id": "ARVO-42480282",
   "sites": [
    {
     "args": "JA3_STR_LEN",
     "callee": "<operator>.alloc",
     "code": "ja3_str[JA3_STR_LEN]",
     "line": 208
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "md5_hash[16]",
     "line": 210
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "getTLScertificate"
  }
 },
 {
  "osv_id": "ARVO-42480344",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "length",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/memcached.c",
    "line": 108,
    "size": null,
    "type": "u_int16_t"
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
    "line": 162,
    "fn": "ndpi_search_memcached",
    "code": "! MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | (sizeof (\"CLIENT_ERROR \") - 1) > length || memcmp(offset | (sizeof (\"CLIENT_ERROR \") - 1) > length",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_memcached",
    "file": "/src/ndpi/src/lib/protocols/memcached.c",
    "line": 162
   },
   "code": "! MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | (sizeof (\"CLIENT_ERROR \") - 1) > length || memcmp(offset | (sizeof (\"CLIENT_ERROR \") - 1) > length",
   "access": {
    "dir": "READ",
    "width": 13,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_memcached",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "(sizeof (\"set \") - 1) > length | (sizeof (\"add \") - 1) > length | (sizeof (\"replace \") - 1) > length",
   "guard_count": 26,
   "control_structures": "IF:113,IF:114,ELSE:121,IF:121,IF:122,IF:127,ELSE:136,IF:146,ELSE:147,IF:147,ELSE:148,IF:148"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/d37b69ce9c9caa979de7c511e33cb7d1cf5fbc91/ARVO-42480344/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_d37b69ce9c9c.cpg",
   "testcase_size": 44
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
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--bcmp--ndpi_search_memcached"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "length = packet->payload_packet_len",
     "line": 108
    }
   ],
   "entity_decl": {
    "line": 108,
    "type": "u_int16_t"
   },
   "entity_name_cpg": "length",
   "func_lines": [
    102,
    175
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
     "code": "packet->tcp != NULL",
     "line": 113
    },
    {
     "code": "packet->payload_packet_len < MEMCACHED_MIN_LEN",
     "line": 114
    },
    {
     "code": "packet->udp != NULL",
     "line": 121
    },
    {
     "code": "packet->payload_packet_len < MEMCACHED_MIN_UDP_LEN",
     "line": 122
    },
    {
     "code": "offset[4] == 0x00",
     "line": 127
    },
    {
     "code": "offset[5] == 0x00",
     "line": 127
    },
    {
     "code": "offset[6] != 0x00",
     "line": 128
    },
    {
     "code": "offset[7] != 0x00",
     "line": 128
    },
    {
     "code": "(sizeof (\"set \") - 1) > length",
     "line": 146
    },
    {
     "code": "(sizeof (\"add \") - 1) > length",
     "line": 147
    },
    {
     "code": "(sizeof (\"replace \") - 1) > length",
     "line": 148
    },
    {
     "code": "(sizeof (\"append \") - 1) > length",
     "line": 149
    },
    {
     "code": "(sizeof (\"prepend \") - 1) > length",
     "line": 150
    },
    {
     "code": "(sizeof (\"cas \") - 1) > length",
     "line": 151
    },
    {
     "code": "(sizeof (\"get \") - 1) > length",
     "line": 152
    },
    {
     "code": "(sizeof (\"gets \") - 1) > length",
     "line": 153
    },
    {
     "code": "(sizeof (\"delete \") - 1) > length",
     "line": 154
    },
    {
     "code": "(sizeof (\"incr \") - 1) > length",
     "line": 155
    },
    {
     "code": "(sizeof (\"decr \") - 1) > length",
     "line": 156
    },
    {
     "code": "(sizeof (\"touch \") - 1) > length",
     "line": 157
    },
    {
     "code": "(sizeof (\"gat \") - 1) > length",
     "line": 158
    },
    {
     "code": "(sizeof (\"gats \") - 1) > length",
     "line": 159
    },
    {
     "code": "(sizeof (\"stats\") - 1) > length",
     "line": 160
    },
    {
     "code": "(sizeof (\"ERROR\\r\\n\") - 1) > length",
     "line": 161
    },
    {
     "code": "(sizeof (\"CLIENT_ERROR \") - 1) > length",
     "line": 162
    },
    {
     "code": "(sizeof (\"SERVER_ERROR \") - 1) > length",
     "line": 163
    },
    {
     "code": "(sizeof (\"STORED\\r\\n\") - 1) > length",
     "line": 164
    },
    {
     "code": "(sizeof (\"NOT_STORED\\r\\n\") - 1) > length",
     "line": 165
    },
    {
     "code": "(sizeof (\"EXISTS\\r\\n\") - 1) > length",
     "line": 166
    },
    {
     "code": "(sizeof (\"NOT_FOUND\\r\\n\") - 1) > length",
     "line": 167
    },
    {
     "code": "(sizeof (\"END\\r\\n\") - 1) > length",
     "line": 168
    },
    {
     "code": "(sizeof (\"DELETED\\r\\n\") - 1) > length",
     "line": 169
    },
    {
     "code": "(sizeof (\"TOUCHED\\r\\n\") - 1) > length",
     "line": 170
    },
    {
     "code": "(sizeof (\"STAT \") - 1) > length",
     "line": 171
    }
   ],
   "line_call_count": 11,
   "line_calls": [
    {
     "code": "! MEMCACHED_MATCH(MCDR_CLIENT_ERROR)",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "MEMCACHED_MATCH(MCDR_CLIENT_ERROR)",
     "name": "MEMCACHED_MATCH",
     "nargs": 0
    },
    {
     "code": "(sizeof (\"CLIENT_ERROR \") - 1) > length ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "(sizeof (\"CLIENT_ERROR \") - 1) > length",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "sizeof (\"CLIENT_ERROR \") - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "sizeof (\"CLIENT_ERROR \")",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "memcmp(offset, \"CLIENT_ERROR \", (sizeof (\"CLIENT_ERROR \") - 1))",
     "name": "memcmp",
     "nargs": 3
    },
    {
     "code": "sizeof (\"CLIENT_ERROR \") - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "sizeof (\"CLIENT_ERROR \")",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "*matches += 1",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "*matches",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "length",
    "offset",
    "matches"
   ],
   "osv_id": "ARVO-42480344",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_memcached"
  }
 },
 {
  "osv_id": "ARVO-42480353",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "len",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "line": 319,
    "size": null,
    "type": "u_int16_t"
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
    "line": 319,
    "fn": "ndpi_int_check_stun",
    "code": "len = ntohs(*((u_int16_t*)&payload[offset+2])) | ntohs(*((u_int16_t*)&payload[offset+2])) | *((u_int16_t*)&payload[offset+2]) | (u_int16_t*)&payload[offset+2]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_int_check_stun",
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "line": 319
   },
   "code": "len = ntohs(*((u_int16_t*)&payload[offset+2])) | ntohs(*((u_int16_t*)&payload[offset+2])) | *((u_int16_t*)&payload[offset+2]) | (u_int16_t*)&payload[offset+2]",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_int_check_stun",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "len == 4 | len == 4",
   "guard_count": 2,
   "control_structures": "IF:149,IF:153,IF:158,ELSE:160,IF:160,IF:163,ELSE:167,IF:170,GOTO:173,IF:178,IF:182,IF:192"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "payload"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/2c2bb11c9b704c5b13e9b45d93a16fbad6304cb0/ARVO-42480353/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_2c2bb11c9b70.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "dedup_token": "ndpi_int_check_stun--ndpi_search_stun--check_ndpi_udp_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "len = ntohs(*((u_int16_t*)&payload[offset+2]))",
     "line": 319
    }
   ],
   "entity_decl": {
    "line": 319,
    "type": "u_int16_t"
   },
   "entity_name_cpg": "len",
   "func_lines": [
    140,
    485
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
     "code": "(k+i) < payload_length",
     "line": 354
    },
    {
     "code": "strstr((char*) flow->host_server_name, \"google.com\") != NULL",
     "line": 364
    },
    {
     "code": "strstr((char*) flow->host_server_name, \"whispersystems.org\") != NULL",
     "line": 367
    },
    {
     "code": "msg_type == 0x0001",
     "line": 376
    },
    {
     "code": "msg_len == 100",
     "line": 377
    },
    {
     "code": "msg_len == 104",
     "line": 377
    },
    {
     "code": "msg_len == 76",
     "line": 380
    },
    {
     "code": "len == 4",
     "line": 393
    },
    {
     "code": "(offset+7) < payload_length",
     "line": 394
    },
    {
     "code": "payload[offset+5] == 0x00",
     "line": 395
    },
    {
     "code": "payload[offset+6] == 0x00",
     "line": 396
    },
    {
     "code": "payload[offset+7] == 0x00",
     "line": 397
    },
    {
     "code": "len == 4",
     "line": 428
    },
    {
     "code": "(offset+7) < payload_length",
     "line": 428
    },
    {
     "code": "payload[offset+4] == 0x00",
     "line": 429
    },
    {
     "code": "payload[offset+5] == 0x00",
     "line": 429
    },
    {
     "code": "payload[offset+6] == 0x00",
     "line": 429
    },
    {
     "code": "payload[offset+7] == 0x02",
     "line": 430
    },
    {
     "code": "payload[offset+7] == 0x03",
     "line": 430
    },
    {
     "code": "msg_type == 0x0800",
     "line": 456
    },
    {
     "code": "flow->protos.stun_ssl.stun.num_udp_pkts > 0",
     "line": 462
    },
    {
     "code": "flow->protos.stun_ssl.stun.num_udp_pkts < MAX_NUM_STUN_PKTS",
     "line": 482
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "len = ntohs(*((u_int16_t*)&payload[offset+2]))",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ntohs(*((u_int16_t*)&payload[offset+2]))",
     "name": "ntohs",
     "nargs": 1
    },
    {
     "code": "*((u_int16_t*)&payload[offset+2])",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(u_int16_t*)&payload[offset+2]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "&payload[offset+2]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "payload[offset+2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "offset+2",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "len",
    "payload",
    "offset"
   ],
   "osv_id": "ARVO-42480353",
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
  "osv_id": "ARVO-42480786",
  "project": "leptonica",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "cmapBuf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/bmpio.c",
    "line": 136,
    "size": null,
    "type": "l_uint8*"
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
   "size_expr_cpg": "4",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "code": "calloc(cmapEntries, sizeof (RGBA_QUAD))",
    "fn": "pixReadMemBmp",
    "kind": "calloc",
    "line": 244,
    "origin": "cpg",
    "args": "cmapEntries"
   },
   {
    "kind": "unknown",
    "line": 250,
    "fn": "pixReadMemBmp",
    "code": "memcpy(cmapBuf, cdata + BMP_FHBYTES + ihbytes,",
    "origin": "report:crash"
   },
   {
    "code": "free(cmapBuf)",
    "fn": "pixReadMemBmp",
    "kind": "free",
    "line": 257,
    "origin": "cpg",
    "args": "cmapBuf"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixReadMemBmp",
    "file": "/src/leptonica/src/bmpio.c",
    "line": 250
   },
   "code": "memcpy(cmapBuf, cdata + BMP_FHBYTES + ihbytes,",
   "access": {
    "dir": "READ",
    "width": 196,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "pixReadMemBmp",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:155,IF:157,IF:163,IF:171,IF:200,IF:202,IF:204,IF:207,IF:211,IF:216,IF:218,IF:223"
  },
  "call_chain": [],
  "types": {
   "entity_type": "l_uint8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "cdata"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/95405007f7ebf7df69f13475b3259179cdc4ec12/ARVO-42480786/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_95405007f7eb.cpg",
   "testcase_size": 65
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
   "dedup_token": "__asan_memcpy--pixReadMemBmp--pixReadMem"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cmapBuf = NULL",
     "line": 242
    },
    {
     "code": "cmapBuf = (l_uint8 *)LEPT_CALLOC(cmapEntries, sizeof(RGBA_QUAD))",
     "line": 244
    }
   ],
   "entity_decl": {
    "line": 136,
    "type": "l_uint8*"
   },
   "entity_name_cpg": "cmapBuf",
   "func_lines": [
    131,
    370
   ],
   "func_params": {
    "names": [
     "cdata",
     "size"
    ],
    "types": [
     "l_uint8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "size < sizeof(BMP_FH) + sizeof(BMP_IH)",
     "line": 157
    },
    {
     "code": "bftype != BMP_ID",
     "line": 163
    },
    {
     "code": "compression != 0",
     "line": 171
    },
    {
     "code": "width < 1",
     "line": 200
    },
    {
     "code": "width > L_MAX_ALLOWED_WIDTH",
     "line": 202
    },
    {
     "code": "height == 0",
     "line": 204
    },
    {
     "code": "height < -L_MAX_ALLOWED_HEIGHT",
     "line": 204
    },
    {
     "code": "height > L_MAX_ALLOWED_HEIGHT",
     "line": 205
    },
    {
     "code": "xres < 0",
     "line": 207
    },
    {
     "code": "xres > L_MAX_ALLOWED_RES",
     "line": 207
    },
    {
     "code": "yres < 0",
     "line": 208
    },
    {
     "code": "yres > L_MAX_ALLOWED_RES",
     "line": 208
    },
    {
     "code": "height < 0",
     "line": 211
    },
    {
     "code": "npixels > L_MAX_ALLOWED_PIXELS",
     "line": 216
    },
    {
     "code": "depth != 1",
     "line": 218
    },
    {
     "code": "depth != 2",
     "line": 218
    },
    {
     "code": "depth != 4",
     "line": 218
    },
    {
     "code": "depth != 8",
     "line": 218
    },
    {
     "code": "depth != 16",
     "line": 219
    },
    {
     "code": "depth != 24",
     "line": 219
    },
    {
     "code": "depth != 32",
     "line": 219
    },
    {
     "code": "imagebytes != 0",
     "line": 223
    },
    {
     "code": "imagebytes != fdatabpl * height",
     "line": 223
    },
    {
     "code": "cmapEntries < 0",
     "line": 233
    },
    {
     "code": "cmapEntries == 1",
     "line": 233
    },
    {
     "code": "cmapEntries > L_MAX_ALLOWED_NUM_COLORS",
     "line": 235
    },
    {
     "code": "size != 1LL * offset + 1LL * fdatabpl * height",
     "line": 237
    },
    {
     "code": "cmapEntries > 0",
     "line": 243
    },
    {
     "code": "(cmapBuf = (l_uint8 *)LEPT_CALLOC(cmapEntries, sizeof(RGBA_QUAD)))",
     "line": 244
    },
    {
     "code": "depth == 24",
     "line": 255
    },
    {
     "code": "(pix = pixCreate(width, height, d)) == NULL",
     "line": 256
    },
    {
     "code": "cmapEntries > 0",
     "line": 268
    },
    {
     "code": "(d) < (8)",
     "line": 269
    },
    {
     "code": "(cmapEntries) < (256)",
     "line": 272
    },
    {
     "code": "i < cmap->n",
     "line": 273
    },
    {
     "code": "depth != 24",
     "line": 281
    },
    {
     "code": "i < height",
     "line": 283
    },
    {
     "code": "i < height",
     "line": 327
    },
    {
     "code": "j < width",
     "line": 328
    },
    {
     "code": "k < extrabytes",
     "line": 340
    },
    {
     "code": "depth == 1",
     "line": 363
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "memcpy(cmapBuf, cdata + BMP_FHBYTES + ihbytes,",
     "name": "memcpy",
     "nargs": null
    },
    {
     "code": "cdata + BMP_FHBYTES + ihbytes",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "cdata + BMP_FHBYTES",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "BMP_FHBYTES",
     "name": "BMP_FHBYTES",
     "nargs": 0
    },
    {
     "code": "sizeof (BMP_FH)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "cmapBuf",
    "cdata",
    "BMP_FH",
    "ihbytes"
   ],
   "osv_id": "ARVO-42480786",
   "sites": [
    {
     "args": "4",
     "callee": "<operator>.alloc",
     "code": "pel[4]",
     "line": 135
    },
    {
     "args": "cmapEntries",
     "callee": "LEPT_CALLOC",
     "code": "LEPT_CALLOC(cmapEntries, sizeof(RGBA_QUAD))",
     "line": 244
    },
    {
     "args": "cmapEntries ;; sizeof (RGBA_QUAD)",
     "callee": "calloc",
     "code": "calloc(cmapEntries, sizeof (RGBA_QUAD))",
     "line": 244
    },
    {
     "args": "cmapBuf",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(cmapBuf)",
     "line": 257
    },
    {
     "args": "cmapBuf",
     "callee": "free",
     "code": "free(cmapBuf)",
     "line": 257
    },
    {
     "args": "cmap->array",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(cmap->array)",
     "line": 270
    },
    {
     "args": "cmap->array",
     "callee": "free",
     "code": "free(cmap->array)",
     "line": 270
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "pixReadMemBmp",
   "use_fn": "pixReadMemBmp"
  }
 },
 {
  "osv_id": "ARVO-42481044",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "proxy",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "line": 1909,
    "size": null,
    "type": "GSUBProxy"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1910,
    "fn": "OT::VarRegionList::serialize(hb_serialize_context_t*, OT::VarRegionList const*, hb_bimap_t const&)",
    "code": "apply (proxy, plan, font, buffer)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OT::VarRegionList::serialize(hb_serialize_context_t*, OT::VarRegionList const*, hb_bimap_t const&)",
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "line": 1910
   },
   "code": "apply (proxy, plan, font, buffer)",
   "access": {
    "dir": "READ",
    "width": 12,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "substitute",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "GSUBProxy",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "this",
   "plan",
   "font",
   "buffer"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/9e48c6e9ef3f6d398c7140933a2cd90980f0ed5b/ARVO-42481044/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_9e48c6e9ef3f.cpg",
   "testcase_size": 6452
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
   "dedup_token": "__asan_memcpy--OT::VarRegionList::serialize(hb_serialize_context_t*, OT::VarRegionList const*, hb_bimap_t const&)--OT::VariationStore::serialize(hb_serialize_co"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1909,
    "type": "GSUBProxy"
   },
   "entity_name_cpg": "proxy",
   "func_lines": [
    1907,
    1911
   ],
   "func_params": {
    "names": [
     "this",
     "plan",
     "font",
     "buffer"
    ],
    "types": [
     "hb_ot_map_t",
     "hb_ot_shape_plan_t*",
     "hb_font_t*",
     "hb_buffer_t*"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "apply (proxy, plan, font, buffer)",
     "name": "apply",
     "nargs": 4
    }
   ],
   "line_ids": [
    "proxy",
    "plan",
    "font",
    "buffer"
   ],
   "osv_id": "ARVO-42481044",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OT::VarRegionList::serialize(hb_serialize_context_t*, OT::VarRegionList const*, hb_bimap_t const&)"
  }
 },
 {
  "osv_id": "ARVO-42481193",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "check",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1394,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 80
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1457,
    "fn": "ndpi_workflow_process_packet",
    "code": "check = ntohs(ethernet->h_proto) | ntohs(ethernet->h_proto) | ethernet->h_proto",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_workflow_process_packet",
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1457
   },
   "code": "check = ntohs(ethernet->h_proto) | ntohs(ethernet->h_proto) | ethernet->h_proto",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_workflow_process_packet",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "check <= 1500 | check >= 1536",
   "guard_count": 2,
   "control_structures": "IF:1411,SWITCH:1428,IF:1430,ELSE:1433,BREAK:1436,BREAK:1443,BREAK:1451,IF:1459,ELSE:1461,IF:1461,IF:1464,IF:1467"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "header",
   "packet"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481193/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "ndpi_workflow_process_packet--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "check = ntohs(ethernet->h_proto)",
     "line": 1457
    }
   ],
   "entity_decl": {
    "line": 1394,
    "type": "int"
   },
   "entity_name_cpg": "check",
   "func_lines": [
    1354,
    1740
   ],
   "func_params": {
    "names": [
     "workflow",
     "header",
     "packet"
    ],
    "types": [
     "ndpi_workflow*",
     "pcap_pkthdr*",
     "u_char*"
    ]
   },
   "guards": [
    {
     "code": "workflow->last_time > time",
     "line": 1411
    },
    {
     "code": "ntohl(*((u_int32_t*)&packet[eth_offset])) == 2",
     "line": 1430
    },
    {
     "code": "pyld_eth_len != 0",
     "line": 1464
    },
    {
     "code": "llc->dsap == SNAP",
     "line": 1467
    },
    {
     "code": "llc->ssap == SNAP",
     "line": 1467
    },
    {
     "code": "llc->dsap == BSTP",
     "line": 1472
    },
    {
     "code": "llc->ssap == BSTP",
     "line": 1472
    },
    {
     "code": "(radiotap->flags & BAD_FCS) == BAD_FCS",
     "line": 1490
    },
    {
     "code": "FCF_TYPE(fc) == WIFI_DATA",
     "line": 1500
    },
    {
     "code": "FCF_FROM_DS(fc) == 0x0",
     "line": 1501
    },
    {
     "code": "FCF_TO_DS(fc) == 0x0",
     "line": 1502
    },
    {
     "code": "llc->dsap == SNAP",
     "line": 1509
    },
    {
     "code": "type == 0x8100",
     "line": 1537
    },
    {
     "code": "ip_offset < (u_int16_t)header->caplen",
     "line": 1537
    },
    {
     "code": "type == ETH_P_IP",
     "line": 1581
    },
    {
     "code": "header->caplen < header->len",
     "line": 1585
    },
    {
     "code": "cap_warning_used == 0",
     "line": 1588
    },
    {
     "code": "iph->version == IPVERSION",
     "line": 1596
    },
    {
     "code": "iph->protocol == IPPROTO_IPV6",
     "line": 1600
    },
    {
     "code": "(frag_off & 0x1FFF) != 0",
     "line": 1605
    },
    {
     "code": "ipv4_frags_warning_used == 0",
     "line": 1609
    },
    {
     "code": "iph->version == 6",
     "line": 1618
    },
    {
     "code": "proto == IPPROTO_DSTOPTS",
     "line": 1623
    },
    {
     "code": "ipv4_warning_used == 0",
     "line": 1634
    },
    {
     "code": "proto == IPPROTO_UDP",
     "line": 1644
    },
    {
     "code": "sport == GTP_U_V1_PORT",
     "line": 1648
    },
    {
     "code": "dport == GTP_U_V1_PORT",
     "line": 1648
    },
    {
     "code": "((flags & 0xE0) >> 5) == 1",
     "line": 1656
    },
    {
     "code": "message_type == 0xFF",
     "line": 1657
    },
    {
     "code": "iph->version != IPVERSION",
     "line": 1666
    },
    {
     "code": "sport == TZSP_PORT",
     "line": 1671
    },
    {
     "code": "dport == TZSP_PORT",
     "line": 1671
    },
    {
     "code": "version == 1",
     "line": 1680
    },
    {
     "code": "ts_type == 0",
     "line": 1680
    },
    {
     "code": "encapsulates == 1",
     "line": 1680
    },
    {
     "code": "offset < header->caplen",
     "line": 1685
    },
    {
     "code": "sport == NDPI_CAPWAP_DATA_PORT",
     "line": 1711
    },
    {
     "code": "(offset+40) < header->caplen",
     "line": 1715
    },
    {
     "code": "packet[offset] == 0x02",
     "line": 1720
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "check = ntohs(ethernet->h_proto)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ntohs(ethernet->h_proto)",
     "name": "ntohs",
     "nargs": 1
    },
    {
     "code": "ethernet->h_proto",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "check",
    "ethernet"
   ],
   "osv_id": "ARVO-42481193",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_workflow_process_packet"
  }
 },
 {
  "osv_id": "ARVO-42481196",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "iph",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 911,
    "size": null,
    "type": "ndpi_iphdr"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 80
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 915,
    "fn": "get_ndpi_flow_info6",
    "code": "iph.saddr = iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->i | iph.saddr | iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->ip6_src.u6_ad | iph6->ip6_src.u6_addr.u6_addr32[2]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_ndpi_flow_info6",
    "file": "/src/ndpi/example/reader_util.c",
    "line": 915
   },
   "code": "iph.saddr = iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->i | iph.saddr | iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->ip6_src.u6_ad | iph6->ip6_src.u6_addr.u6_addr32[2]",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_ndpi_flow_info6",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:919"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_iphdr",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "iph6"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481196/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "testcase_size": 62
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
   "dedup_token": "get_ndpi_flow_info6--packet_processing--ndpi_workflow_process_packet"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "iph.version = IPVERSION",
     "line": 914
    },
    {
     "code": "iph.saddr = iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->ip6_src.u6_addr.u6_addr32[3]",
     "line": 915
    },
    {
     "code": "iph.daddr = iph6->ip6_dst.u6_addr.u6_addr32[2] + iph6->ip6_dst.u6_addr.u6_addr32[3]",
     "line": 916
    },
    {
     "code": "iph.protocol = iph6->ip6_hdr.ip6_un1_nxt",
     "line": 917
    },
    {
     "code": "iph.protocol = options[0]",
     "line": 922
    }
   ],
   "entity_decl": {
    "line": 911,
    "type": "ndpi_iphdr"
   },
   "entity_name_cpg": "iph",
   "func_lines": [
    896,
    932
   ],
   "func_params": {
    "names": [
     "workflow",
     "vlan_id",
     "tunnel_type",
     "iph6",
     "ip_offset",
     "tcph",
     "udph",
     "sport",
     "dport",
     "src",
     "dst",
     "proto",
     "payload",
     "payload_len",
     "src_to_dst_direction",
     "when"
    ],
    "types": [
     "ndpi_workflow*",
     "u_int16_t",
     "ndpi_packet_tunnel",
     "ndpi_ipv6hdr*",
     "u_int16_t",
     "ndpi_tcphdr**",
     "ndpi_udphdr**",
     "u_int16_t*",
     "u_int16_t*",
     "ndpi_id_struct**",
     "ndpi_id_struct**",
     "u_int8_t*",
     "u_int8_t**",
     "u_int16_t*",
     "u_int8_t*",
     "timeval"
    ]
   },
   "guards": [
    {
     "code": "iph.protocol == IPPROTO_DSTOPTS",
     "line": 919
    }
   ],
   "line_call_count": 11,
   "line_calls": [
    {
     "code": "iph.saddr = iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->ip6_src.u6_addr.u6_addr32[3]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "iph.saddr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->ip6_src.u6_addr.u6_addr32[3]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src.u6_addr.u6_addr32[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src.u6_addr.u6_addr32",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src.u6_addr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src.u6_addr.u6_addr32[3]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src.u6_addr.u6_addr32",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src.u6_addr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "iph6->ip6_src",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "iph",
    "iph6"
   ],
   "osv_id": "ARVO-42481196",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "get_ndpi_flow_info6"
  }
 },
 {
  "osv_id": "ARVO-42481216",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "sport",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 644,
    "size": null,
    "type": "u_int16_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 80
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(struct ndpi_flow_info)",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 703,
    "fn": "get_ndpi_flow_info",
    "code": "*sport = ntohs((*tcph)->source), *dport = ntohs((*tcph)- | *sport = ntohs((*tcph)->source) | *sport | ntohs((*tcph)->source)",
    "origin": "report:crash"
   },
   {
    "code": "malloc(sizeof(struct ndpi_flow_info))",
    "fn": "get_ndpi_flow_info",
    "kind": "malloc",
    "line": 770,
    "origin": "cpg",
    "args": "sizeof(struct ndpi_flow_info)"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_ndpi_flow_info",
    "file": "/src/ndpi/example/reader_util.c",
    "line": 703
   },
   "code": "*sport = ntohs((*tcph)->source), *dport = ntohs((*tcph)- | *sport = ntohs((*tcph)->source) | *sport | ntohs((*tcph)->source)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_ndpi_flow_info",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:662,IF:663,IF:666,ELSE:672,IF:679,ELSE:681,IF:681,ELSE:683,IF:683,ELSE:685,IF:685,ELSE:687"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "iph",
   "iph6",
   "tcph",
   "sport",
   "dport"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481216/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "testcase_size": 86
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
   "dedup_token": "get_ndpi_flow_info--get_ndpi_flow_info6--packet_processing"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 644,
    "type": "u_int16_t*"
   },
   "entity_name_cpg": "sport",
   "func_lines": [
    633,
    892
   ],
   "func_params": {
    "names": [
     "workflow",
     "version",
     "vlan_id",
     "tunnel_type",
     "iph",
     "iph6",
     "ip_offset",
     "ipsize",
     "l4_packet_len",
     "tcph",
     "udph",
     "sport",
     "dport",
     "src",
     "dst",
     "proto",
     "payload",
     "payload_len",
     "src_to_dst_direction",
     "when"
    ],
    "types": [
     "ndpi_workflow*",
     "u_int8_t",
     "u_int16_t",
     "ndpi_packet_tunnel",
     "ndpi_iphdr*",
     "ndpi_ipv6hdr*",
     "u_int16_t",
     "u_int16_t",
     "u_int16_t",
     "ndpi_tcphdr**",
     "ndpi_udphdr**",
     "u_int16_t*",
     "u_int16_t*",
     "ndpi_id_struct**",
     "ndpi_id_struct**",
     "u_int8_t*",
     "u_int8_t**",
     "u_int16_t*",
     "u_int8_t*",
     "timeval"
    ]
   },
   "guards": [
    {
     "code": "version == IPVERSION",
     "line": 662
    },
    {
     "code": "ipsize < 20",
     "line": 663
    },
    {
     "code": "(iph->ihl * 4) > ipsize",
     "line": 666
    },
    {
     "code": "ipsize < ntohs(iph->tot_len)",
     "line": 666
    },
    {
     "code": "l4_packet_len < 64",
     "line": 679
    },
    {
     "code": "l4_packet_len < 128",
     "line": 681
    },
    {
     "code": "l4_packet_len < 256",
     "line": 683
    },
    {
     "code": "l4_packet_len < 1024",
     "line": 685
    },
    {
     "code": "l4_packet_len < 1500",
     "line": 687
    },
    {
     "code": "l4_packet_len > workflow->stats.max_packet_len",
     "line": 692
    },
    {
     "code": "*proto == IPPROTO_TCP",
     "line": 697
    },
    {
     "code": "*proto == IPPROTO_UDP",
     "line": 708
    },
    {
     "code": "l4_packet_len > sizeof(struct ndpi_udphdr)",
     "line": 714
    },
    {
     "code": "*proto == IPPROTO_ICMP",
     "line": 716
    },
    {
     "code": "l4_packet_len > sizeof(struct ndpi_icmphdr)",
     "line": 718
    },
    {
     "code": "*proto == IPPROTO_ICMPV6",
     "line": 721
    },
    {
     "code": "l4_packet_len > sizeof(struct ndpi_icmp6hdr)",
     "line": 723
    },
    {
     "code": "ret == NULL",
     "line": 747
    },
    {
     "code": "ret == NULL",
     "line": 763
    },
    {
     "code": "workflow->stats.ndpi_flow_count == workflow->prefs.max_ndpi_flows",
     "line": 764
    },
    {
     "code": "newflow == NULL",
     "line": 772
    },
    {
     "code": "version == IPVERSION",
     "line": 792
    },
    {
     "code": "(newflow->ndpi_flow = ndpi_flow_malloc(SIZEOF_FLOW_STRUCT)) == NULL",
     "line": 802
    },
    {
     "code": "(newflow->src_id = ndpi_malloc(SIZEOF_ID_STRUCT)) == NULL",
     "line": 809
    },
    {
     "code": "(newflow->dst_id = ndpi_malloc(SIZEOF_ID_STRUCT)) == NULL",
     "line": 816
    },
    {
     "code": "newflow->entropy.src2dst_pkt_count == 0",
     "line": 829
    },
    {
     "code": "l4_data_len != 0XFEEDFACE",
     "line": 834
    },
    {
     "code": "l4_data_len != 0",
     "line": 834
    },
    {
     "code": "rflow->src_ip == iph->saddr",
     "line": 844
    },
    {
     "code": "rflow->dst_ip == iph->daddr",
     "line": 845
    },
    {
     "code": "rflow->src_port == htons(*sport)",
     "line": 846
    },
    {
     "code": "rflow->dst_port == htons(*dport)",
     "line": 847
    },
    {
     "code": "rflow->src_ip == iph->saddr",
     "line": 854
    },
    {
     "code": "rflow->dst_ip == iph->daddr",
     "line": 855
    },
    {
     "code": "rflow->src_port == htons(*sport)",
     "line": 856
    },
    {
     "code": "rflow->dst_port == htons(*dport)",
     "line": 857
    },
    {
     "code": "rflow->entropy.src2dst_pkt_count < max_num_packets_per_flow",
     "line": 864
    },
    {
     "code": "l4_data_len != 0XFEEDFACE",
     "line": 871
    },
    {
     "code": "l4_data_len != 0",
     "line": 871
    },
    {
     "code": "rflow->entropy.dst2src_pkt_count < max_num_packets_per_flow",
     "line": 875
    },
    {
     "code": "rflow->entropy.dst2src_pkt_count == 0",
     "line": 878
    },
    {
     "code": "l4_data_len != 0XFEEDFACE",
     "line": 885
    },
    {
     "code": "l4_data_len != 0",
     "line": 885
    }
   ],
   "line_call_count": 11,
   "line_calls": [
    {
     "code": "*sport = ntohs((*tcph)->source), *dport = ntohs((*tcph)->dest)",
     "name": "<operator>.expressionList",
     "nargs": 2
    },
    {
     "code": "*sport = ntohs((*tcph)->source)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*sport",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "ntohs((*tcph)->source)",
     "name": "ntohs",
     "nargs": 1
    },
    {
     "code": "(*tcph)->source",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "*tcph",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*dport = ntohs((*tcph)->dest)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*dport",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "ntohs((*tcph)->dest)",
     "name": "ntohs",
     "nargs": 1
    },
    {
     "code": "(*tcph)->dest",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "*tcph",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "sport",
    "tcph",
    "dport"
   ],
   "osv_id": "ARVO-42481216",
   "sites": [
    {
     "args": "sizeof(struct ndpi_flow_info)",
     "callee": "malloc",
     "code": "malloc(sizeof(struct ndpi_flow_info))",
     "line": 770
    },
    {
     "args": "DATA_ANALUYSIS_SLIDING_WINDOW",
     "callee": "ndpi_alloc_data_analysis",
     "code": "ndpi_alloc_data_analysis(DATA_ANALUYSIS_SLIDING_WINDOW)",
     "line": 786
    },
    {
     "args": "DATA_ANALUYSIS_SLIDING_WINDOW",
     "callee": "ndpi_alloc_data_analysis",
     "code": "ndpi_alloc_data_analysis(DATA_ANALUYSIS_SLIDING_WINDOW)",
     "line": 787
    },
    {
     "args": "DATA_ANALUYSIS_SLIDING_WINDOW",
     "callee": "ndpi_alloc_data_analysis",
     "code": "ndpi_alloc_data_analysis(DATA_ANALUYSIS_SLIDING_WINDOW)",
     "line": 788
    },
    {
     "args": "DATA_ANALUYSIS_SLIDING_WINDOW",
     "callee": "ndpi_alloc_data_analysis",
     "code": "ndpi_alloc_data_analysis(DATA_ANALUYSIS_SLIDING_WINDOW)",
     "line": 789
    },
    {
     "args": "DATA_ANALUYSIS_SLIDING_WINDOW",
     "callee": "ndpi_alloc_data_analysis",
     "code": "ndpi_alloc_data_analysis(DATA_ANALUYSIS_SLIDING_WINDOW)",
     "line": 790
    },
    {
     "args": "SIZEOF_FLOW_STRUCT",
     "callee": "ndpi_flow_malloc",
     "code": "ndpi_flow_malloc(SIZEOF_FLOW_STRUCT)",
     "line": 802
    },
    {
     "args": "newflow",
     "callee": "free",
     "code": "free(newflow)",
     "line": 804
    },
    {
     "args": "SIZEOF_ID_STRUCT",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(SIZEOF_ID_STRUCT)",
     "line": 809
    },
    {
     "args": "newflow",
     "callee": "free",
     "code": "free(newflow)",
     "line": 811
    },
    {
     "args": "SIZEOF_ID_STRUCT",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(SIZEOF_ID_STRUCT)",
     "line": 816
    },
    {
     "args": "newflow",
     "callee": "free",
     "code": "free(newflow)",
     "line": 818
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "get_ndpi_flow_info"
  }
 },
 {
  "osv_id": "ARVO-42481277",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "fc",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1390,
    "size": null,
    "type": "u_int16_t"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1497,
    "fn": "ndpi_workflow_process_packet",
    "code": "fc = wifi->fc | wifi->fc",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_workflow_process_packet",
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1497
   },
   "code": "fc = wifi->fc | wifi->fc",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_workflow_process_packet",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1411,SWITCH:1428,IF:1430,ELSE:1433,BREAK:1436,BREAK:1443,BREAK:1451,IF:1459,ELSE:1461,IF:1461,IF:1464,IF:1467"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "header",
   "packet"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481277/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "testcase_size": 286
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
   "shadow_legend_size": 0,
   "dedup_token": "ndpi_workflow_process_packet--LLVMFuzzerTestOneInput--ExecuteFilesOnyByOne"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "fc = wifi->fc",
     "line": 1497
    }
   ],
   "entity_decl": {
    "line": 1390,
    "type": "u_int16_t"
   },
   "entity_name_cpg": "fc",
   "func_lines": [
    1354,
    1740
   ],
   "func_params": {
    "names": [
     "workflow",
     "header",
     "packet"
    ],
    "types": [
     "ndpi_workflow*",
     "pcap_pkthdr*",
     "u_char*"
    ]
   },
   "guards": [
    {
     "code": "workflow->last_time > time",
     "line": 1411
    },
    {
     "code": "ntohl(*((u_int32_t*)&packet[eth_offset])) == 2",
     "line": 1430
    },
    {
     "code": "pyld_eth_len != 0",
     "line": 1464
    },
    {
     "code": "llc->dsap == SNAP",
     "line": 1467
    },
    {
     "code": "llc->ssap == SNAP",
     "line": 1467
    },
    {
     "code": "llc->dsap == BSTP",
     "line": 1472
    },
    {
     "code": "llc->ssap == BSTP",
     "line": 1472
    },
    {
     "code": "(radiotap->flags & BAD_FCS) == BAD_FCS",
     "line": 1490
    },
    {
     "code": "FCF_TYPE(fc) == WIFI_DATA",
     "line": 1500
    },
    {
     "code": "FCF_FROM_DS(fc) == 0x0",
     "line": 1501
    },
    {
     "code": "FCF_TO_DS(fc) == 0x0",
     "line": 1502
    },
    {
     "code": "llc->dsap == SNAP",
     "line": 1509
    },
    {
     "code": "type == 0x8100",
     "line": 1537
    },
    {
     "code": "ip_offset < (u_int16_t)header->caplen",
     "line": 1537
    },
    {
     "code": "type == ETH_P_IP",
     "line": 1581
    },
    {
     "code": "header->caplen < header->len",
     "line": 1585
    },
    {
     "code": "cap_warning_used == 0",
     "line": 1588
    },
    {
     "code": "iph->version == IPVERSION",
     "line": 1596
    },
    {
     "code": "iph->protocol == IPPROTO_IPV6",
     "line": 1600
    },
    {
     "code": "(frag_off & 0x1FFF) != 0",
     "line": 1605
    },
    {
     "code": "ipv4_frags_warning_used == 0",
     "line": 1609
    },
    {
     "code": "iph->version == 6",
     "line": 1618
    },
    {
     "code": "proto == IPPROTO_DSTOPTS",
     "line": 1623
    },
    {
     "code": "ipv4_warning_used == 0",
     "line": 1634
    },
    {
     "code": "proto == IPPROTO_UDP",
     "line": 1644
    },
    {
     "code": "sport == GTP_U_V1_PORT",
     "line": 1648
    },
    {
     "code": "dport == GTP_U_V1_PORT",
     "line": 1648
    },
    {
     "code": "((flags & 0xE0) >> 5) == 1",
     "line": 1656
    },
    {
     "code": "message_type == 0xFF",
     "line": 1657
    },
    {
     "code": "iph->version != IPVERSION",
     "line": 1666
    },
    {
     "code": "sport == TZSP_PORT",
     "line": 1671
    },
    {
     "code": "dport == TZSP_PORT",
     "line": 1671
    },
    {
     "code": "version == 1",
     "line": 1680
    },
    {
     "code": "ts_type == 0",
     "line": 1680
    },
    {
     "code": "encapsulates == 1",
     "line": 1680
    },
    {
     "code": "offset < header->caplen",
     "line": 1685
    },
    {
     "code": "sport == NDPI_CAPWAP_DATA_PORT",
     "line": 1711
    },
    {
     "code": "(offset+40) < header->caplen",
     "line": 1715
    },
    {
     "code": "packet[offset] == 0x02",
     "line": 1720
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "fc = wifi->fc",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "wifi->fc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "fc",
    "wifi"
   ],
   "osv_id": "ARVO-42481277",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_workflow_process_packet"
  }
 },
 {
  "osv_id": "ARVO-42481371",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
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
    "line": 220,
    "fn": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "file": "/src/harfbuzz/src/hb-array.hh",
    "line": 220
   },
   "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
   "access": {
    "dir": "READ",
    "width": 1,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/c828d7bf76dd039be1775edff1d798dbcc10708b/ARVO-42481371/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_c828d7bf76dd.cpg",
   "testcase_size": 100109
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const--"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
     "line": 220
    }
   ],
   "entity_name_cpg": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS",
   "func_lines": [
    97,
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
     "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS"
   ],
   "osv_id": "ARVO-42481371",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const"
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