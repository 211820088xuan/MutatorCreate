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
  "osv_id": "ARVO-371068253",
  "project": "flac",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "current_link",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 128,
    "type": "FLAC__OggDecoderAspect_LinkDetails*",
    "size": null
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "safe_realloc_nofree_mul_2op_",
    "file": "/src/flac/src/libFLAC/../../include/share/alloc.h",
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "current_link->other_serial_numbers ;; 4+current_link->number_of_other_streams ;; sizeof(long)",
   "size_expr_cpg_callee": "safe_realloc_nofree_mul_2op_"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 130,
    "fn": "process_page_",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "process_page_",
    "file": "/src/flac/src/libFLAC/ogg_decoder_aspect.c",
    "line": 130
   },
   "code": "(current_link->number_of_other_streams) % 4 == 0",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "process_page_",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/flac/address/d367d6fe92839cce257eafaa0dc650cc5bd16151/ARVO-371068253/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/flac_d367d6fe9283.cpg",
   "testcase_size": 162876
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
   "loc_size": 4480,
   "loc_offset": 32,
   "loc_kind": "region",
   "dedup_token": "process_page_--FLAC__ogg_decoder_aspect_skip_link--seek_to_absolute_sample_ogg_",
   "overshoot_ratio": 0.007143
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* current_link = &aspect->linkdetails[aspect->current_linknumber_advance_read]",
     "line": 128
    },
    {
     "code": "current_link->other_serial_numbers = tmpptr",
     "line": 135
    },
    {
     "code": "current_link->other_serial_numbers[current_link->number_of_other_streams] = ogg_page_serialno(&aspect->working_page)",
     "line": 139
    }
   ],
   "entity_decl": {
    "line": 128,
    "type": "FLAC__OggDecoderAspect_LinkDetails*"
   },
   "entity_name_cpg": "current_link",
   "func_lines": [
    85,
    147
   ],
   "func_params": {
    "names": [
     "aspect",
     "tell_callback",
     "decoder",
     "client_data"
    ],
    "types": [
     "FLAC__OggDecoderAspect*",
     "FLAC__StreamDecoderTellCallback",
     "FLAC__StreamDecoder*",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "aspect->working_page.body_len > 1 + FLAC__OGG_MAPPING_MAGIC_LENGTH",
     "line": 92
    },
    {
     "code": "aspect->working_page.body[0] == FLAC__OGG_MAPPING_FIRST_HEADER_PACKET_TYPE",
     "line": 93
    },
    {
     "code": "tell_callback != 0",
     "line": 104
    },
    {
     "code": "tell_callback(decoder, &tell_offset, client_data) == FLAC__STREAM_DECODER_TELL_STATUS_OK",
     "line": 105
    },
    {
     "code": "ogg_stream_pagein(&aspect->stream_state, &aspect->working_page) == 0",
     "line": 118
    },
    {
     "code": "(current_link->number_of_other_streams) % 4 == 0",
     "line": 130
    },
    {
     "code": "NULL == (tmpptr = safe_realloc_nofree_mul_2op_(current_link->other_serial_numbers, 4+current_link->number_of_other_streams, sizeof(long)))",
     "line": 132
    },
    {
     "code": "aspect->number_of_links_allocated < aspect->current_linknumber_advance_read",
     "line": 136
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "(current_link->number_of_other_streams) % 4 == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "(current_link->number_of_other_streams) % 4",
     "name": "<operator>.modulo",
     "nargs": 2
    },
    {
     "code": "current_link->number_of_other_streams",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "current_link"
   ],
   "osv_id": "ARVO-371068253",
   "sites": [
    {
     "args": "current_link->other_serial_numbers ;; 4+current_link->number_of_other_streams ;; sizeof(long)",
     "callee": "safe_realloc_nofree_mul_2op_",
     "code": "safe_realloc_nofree_mul_2op_(current_link->other_serial_numbers, 4+current_link->number_of_other_streams, sizeof(long))",
     "line": 132
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "process_page_"
  }
 },
 {
  "osv_id": "ARVO-372515090",
  "project": "kamailio",
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
    "line": 387,
    "fn": "extract_sendrecv_mode",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "extract_sendrecv_mode",
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "line": 387
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 6,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "extract_sendrecv_mode",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-372515090/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 7257
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
   "dedup_token": "strncasecmp--extract_sendrecv_mode--parse_sdp_session"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "extract_sendrecv_mode"
  }
 },
 {
  "osv_id": "ARVO-372547397",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/cram/cram_encode.c",
    "line": 1825,
    "size": null,
    "type": "cram_container*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "refs2id",
    "file": "/src/htslib/cram/cram_io.c",
    "line": 2715
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "ntags*2 ;; sizeof(*s->aux_block)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2000,
    "fn": "cram_encode_container",
    "code": "c->ref_end > fd->refs->ref_id[c->ref_id]->LN_length | c->ref_end | fd->refs->ref_id[c->ref_id]->LN_length | fd->refs->ref_id[c->ref_id]",
    "origin": "report:crash"
   },
   {
    "code": "calloc(ntags*2, sizeof(*s->aux_block))",
    "fn": "cram_encode_container",
    "kind": "calloc",
    "line": 2077,
    "origin": "cpg",
    "args": "ntags*2 ;; sizeof(*s->aux_block)"
   },
   {
    "code": "malloc(sizeof(*spares))",
    "fn": "cram_encode_container",
    "kind": "malloc",
    "line": 2107,
    "origin": "cpg",
    "args": "sizeof(*spares)"
   },
   {
    "code": "malloc(c->num_landmarks * sizeof(*c->landmark))",
    "fn": "cram_encode_container",
    "kind": "malloc",
    "line": 2448,
    "origin": "cpg",
    "args": "c->num_landmarks * sizeof(*c->landmark)"
   },
   {
    "code": "free(c->ref)",
    "fn": "cram_encode_container",
    "kind": "free",
    "line": 2514,
    "origin": "cpg",
    "args": "c->ref"
   }
  ],
  "crash": {
   "site": {
    "fn": "cram_encode_container",
    "file": "/src/htslib/cram/cram_encode.c",
    "line": 2000
   },
   "code": "c->ref_end > fd->refs->ref_id[c->ref_id]->LN_length | c->ref_end | fd->refs->ref_id[c->ref_id]->LN_length | fd->refs->ref_id[c->ref_id]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cram_encode_container",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1833,GOTO:1834,IF:1836,GOTO:1837,IF:1845,ELSE:1849,IF:1849,IF:1866,IF:1867,GOTO:1868,IF:1871,IF:1873"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cram_container*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "fd",
   "c"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/ca920611fcd8be1180045589ac11bff2f04eafd8/ARVO-372547397/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_ca920611fcd8.cpg",
   "testcase_size": 1735
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
   "loc_size": 8,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "cram_encode_container--cram_flush_container--cram_flush_container_mt",
   "overshoot_ratio": 1.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c->no_ref = 0",
     "line": 1847
    },
    {
     "code": "c->embed_ref = 2",
     "line": 1848
    },
    {
     "code": "c->embed_ref = 0",
     "line": 1852
    },
    {
     "code": "c->embed_ref = fd->embed_ref = 0",
     "line": 1881
    },
    {
     "code": "c->no_ref = fd->no_ref = 1",
     "line": 1882
    },
    {
     "code": "c->embed_ref = fd->embed_ref = 2",
     "line": 1898
    },
    {
     "code": "c->ref_id = bam_ref(b)",
     "line": 1905
    },
    {
     "code": "c->ref_seq_id = c->ref_id",
     "line": 1906
    },
    {
     "code": "c->ref       = fd->refs->ref_id[c->ref_seq_id]->seq",
     "line": 1907
    },
    {
     "code": "c->ref_start = 1",
     "line": 1908
    },
    {
     "code": "c->ref_end   = fd->refs->ref_id[c->ref_seq_id]->length",
     "line": 1909
    },
    {
     "code": "c->ref_id = bam_ref(b)",
     "line": 1916
    },
    {
     "code": "c->ref = NULL",
     "line": 1917
    },
    {
     "code": "c->ref_free = 1",
     "line": 1923
    },
    {
     "code": "c->ref_seq_id = c->ref_id",
     "line": 1926
    },
    {
     "code": "c->ref_id = bam_ref(c->bams[0])",
     "line": 1928
    },
    {
     "code": "c->ref_seq_id = c->ref_id",
     "line": 1930
    },
    {
     "code": "c->no_ref = 1",
     "line": 1942
    },
    {
     "code": "c->embed_ref = fd->embed_ref = -2",
     "line": 1988
    },
    {
     "code": "c->no_ref = fd->no_ref = 1",
     "line": 1989
    },
    {
     "code": "c->ref_end = fd->refs->ref_id[c->ref_id]->LN_length",
     "line": 2001
    },
    {
     "code": "c->ref_seq_id = bam_ref(b)",
     "line": 2024
    },
    {
     "code": "c->ref       = fd->refs->ref_id[c->ref_seq_id]->seq",
     "line": 2027
    },
    {
     "code": "c->ref_start = 1",
     "line": 2028
    },
    {
     "code": "c->ref_end   = fd->refs->ref_id[c->ref_seq_id]->length",
     "line": 2029
    },
    {
     "code": "c->bams = NULL",
     "line": 2114
    },
    {
     "code": "c->ref_seq_id = -2",
     "line": 2126
    },
    {
     "code": "c->ref_seq_start = 0",
     "line": 2127
    },
    {
     "code": "c->ref_seq_span = 0",
     "line": 2128
    },
    {
     "code": "c->num_records = 0",
     "line": 2155
    },
    {
     "code": "c->num_blocks = 1",
     "line": 2156
    },
    {
     "code": "c->length = 0",
     "line": 2157
    },
    {
     "code": "c->num_landmarks = c->curr_slice",
     "line": 2447
    },
    {
     "code": "c->landmark = malloc(c->num_landmarks * sizeof(*c->landmark))",
     "line": 2448
    },
    {
     "code": "c->ref_seq_id    = c->slices[0]->hdr->ref_seq_id",
     "line": 2466
    },
    {
     "code": "c->ref_seq_start = 0",
     "line": 2470
    },
    {
     "code": "c->ref_seq_span  = 0",
     "line": 2471
    },
    {
     "code": "c->ref_seq_start = c->slices[0]->hdr->ref_seq_start",
     "line": 2473
    },
    {
     "code": "c->ref_seq_span  = c->slices[0]->hdr->ref_seq_span",
     "line": 2474
    },
    {
     "code": "c->landmark[i] = slice_offset",
     "line": 2480
    },
    {
     "code": "c->ref_seq_span = s->hdr->ref_seq_start + s->hdr->ref_seq_span",
     "line": 2484
    },
    {
     "code": "c->comp_hdr_block = c_hdr",
     "line": 2510
    },
    {
     "code": "c->ref = NULL",
     "line": 2515
    }
   ],
   "entity_decl": {
    "line": 1825,
    "type": "cram_container*"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    1825,
    2533
   ],
   "func_params": {
    "names": [
     "fd",
     "c"
    ],
    "types": [
     "cram_fd*",
     "cram_container*"
    ]
   },
   "guards": [
    {
     "code": "CRAM_MAJOR_VERS(fd->version) == 1",
     "line": 1836
    },
    {
     "code": "c->embed_ref == -2",
     "line": 1845
    },
    {
     "code": "c->embed_ref == -2",
     "line": 1849
    },
    {
     "code": "embed_ref == 0",
     "line": 1887
    },
    {
     "code": "validate_md5(fd, c->ref_seq_id) < 0",
     "line": 1902
    },
    {
     "code": "i < nref",
     "line": 1934
    },
    {
     "code": "validate_md5(fd, i) < 0",
     "line": 1937
    },
    {
     "code": "r1 < c->curr_c_rec",
     "line": 1949
    },
    {
     "code": "sn < c->curr_slice",
     "line": 1955
    },
    {
     "code": "lossy_read_names(fd, c, s, r1_start) != 0",
     "line": 1959
    },
    {
     "code": "embed_ref == 2",
     "line": 1969
    },
    {
     "code": "cram_generate_reference(c, s, r1) < 0",
     "line": 1970
    },
    {
     "code": "sn > 0",
     "line": 1979
    },
    {
     "code": "fd->no_ref_counter > 0",
     "line": 1996
    },
    {
     "code": "c->ref_end > fd->refs->ref_id[c->ref_id]->LN_length",
     "line": 2000
    },
    {
     "code": "r1 < c->curr_c_rec",
     "line": 2006
    },
    {
     "code": "r2 < s->hdr->num_records",
     "line": 2006
    },
    {
     "code": "bam_ref(b) != c->ref_seq_id",
     "line": 2012
    },
    {
     "code": "validate_md5(fd, bam_ref(b)) < 0",
     "line": 2021
    },
    {
     "code": "process_one_read(fd, c, s, cr, b, r2, &MD, embed_ref,",
     "line": 2033
    },
    {
     "code": "first_base > cr->apos",
     "line": 2039
    },
    {
     "code": "last_base < cr->aend",
     "line": 2042
    },
    {
     "code": "add_read_names(fd, c, s, r1_start) < 0",
     "line": 2053
    },
    {
     "code": "c->ref_id == -1",
     "line": 2060
    },
    {
     "code": "(0) > (last_base - first_base + 1)",
     "line": 2069
    },
    {
     "code": "k != kh_end(c->tags_used)",
     "line": 2084
    },
    {
     "code": "c->stats[DS_RI]->nvals > 1",
     "line": 2118
    },
    {
     "code": "i < c->curr_slice",
     "line": 2136
    },
    {
     "code": "CRAM_MAJOR_VERS(fd->version) != 1",
     "line": 2139
    },
    {
     "code": "c->multi_seq == 0",
     "line": 2140
    },
    {
     "code": "CRAM_MAJOR_VERS(fd->version) == 1",
     "line": 2316
    },
    {
     "code": "i < c->curr_slice",
     "line": 2421
    },
    {
     "code": "embed_ref>0",
     "line": 2425
    },
    {
     "code": "c->slices[i]->hdr->ref_seq_id != -1",
     "line": 2425
    },
    {
     "code": "cram_encode_slice(fd, c, h, c->slices[i], local_embed_ref) != 0",
     "line": 2426
    },
    {
     "code": "c_hdr->method == RAW",
     "line": 2457
    },
    {
     "code": "c->ref_seq_id == -1",
     "line": 2467
    },
    {
     "code": "i < c->curr_slice",
     "line": 2476
    },
    {
     "code": "s->hdr->ref_seq_start + s->hdr->ref_seq_span >",
     "line": 2482
    },
    {
     "code": "s->hdr_block->method == RAW",
     "line": 2488
    },
    {
     "code": "j < s->hdr->num_blocks",
     "line": 2497
    },
    {
     "code": "s->block[j]->method == RAW",
     "line": 2503
    },
    {
     "code": "i < fd->refs->nref",
     "line": 2523
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "c->ref_end > fd->refs->ref_id[c->ref_id]->LN_length",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "c->ref_end",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "fd->refs->ref_id[c->ref_id]->LN_length",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "fd->refs->ref_id[c->ref_id]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "fd->refs->ref_id",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "fd->refs",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "c->ref_id",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c",
    "fd"
   ],
   "osv_id": "ARVO-372547397",
   "sites": [
    {
     "args": "MD.s",
     "callee": "free",
     "code": "free(MD.s)",
     "line": 2018
    },
    {
     "args": "MD.s",
     "callee": "free",
     "code": "free(MD.s)",
     "line": 2035
    },
    {
     "args": "MD.s",
     "callee": "free",
     "code": "free(MD.s)",
     "line": 2046
    },
    {
     "args": "ntags*2 ;; sizeof(*s->aux_block)",
     "callee": "calloc",
     "code": "calloc(ntags*2, sizeof(*s->aux_block))",
     "line": 2077
    },
    {
     "args": "sizeof(*spares)",
     "callee": "malloc",
     "code": "malloc(sizeof(*spares))",
     "line": 2107
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "p[2] = {0, c->max_apos}",
     "line": 2193
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i2[2] = {0, DS_SC}",
     "line": 2372
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i2[2] = {0, DS_IN}",
     "line": 2400
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i2[2] = {0, DS_RN}",
     "line": 2412
    },
    {
     "args": "c->num_landmarks * sizeof(*c->landmark)",
     "callee": "malloc",
     "code": "malloc(c->num_landmarks * sizeof(*c->landmark))",
     "line": 2448
    },
    {
     "args": "c->ref",
     "callee": "free",
     "code": "free(c->ref)",
     "line": 2514
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "cram_encode_container",
   "use_fn": "cram_encode_container"
  }
 },
 {
  "osv_id": "ARVO-375237153",
  "project": "kamailio",
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
    "line": 216,
    "fn": "extract_fmtp",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "extract_fmtp",
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "line": 216
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 6,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "extract_fmtp",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-375237153/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 3185
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
   "dedup_token": "strncasecmp--extract_fmtp--parse_sdp_session"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "extract_fmtp"
  }
 },
 {
  "osv_id": "ARVO-376100377",
  "project": "kamailio",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x270b2)",
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
    "line": 384,
    "fn": "extract_ice_option",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "extract_ice_option",
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "line": 384
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "extract_ice_option",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/fe7d7c571b6c8d446cf66a1cf27d335d98f5f945/ARVO-376100377/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_fe7d7c571b6c.cpg",
   "testcase_size": 873
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
   "dedup_token": "extract_ice_option--parse_sdp_session--parse_sdp"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "extract_ice_option"
  }
 },
 {
  "osv_id": "ARVO-376515517",
  "project": "file",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/file/src/apprentice.c",
    "line": 2020,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__getdelim (/lib/x86_64-linux-gnu/libc.so.6+0x83543) (BuildId: 5792732f783158c66fb4f3756458ca24e46e827d)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "ALLOC_CHUNK"
  },
  "sites": [
   {
    "code": "realloc(me->mp, sizeof (*nm) * cnt)",
    "fn": "parse",
    "kind": "realloc",
    "line": 2061,
    "origin": "cpg",
    "args": "me->mp ;; sizeof (*nm) * cnt"
   },
   {
    "code": "malloc(len)",
    "fn": "parse",
    "kind": "malloc",
    "line": 2076,
    "origin": "cpg",
    "args": "len"
   },
   {
    "kind": "unknown",
    "line": 2400,
    "fn": "parse",
    "code": "i = 0 | (m->desc[i++] = *l++) != '\\0' && i < sizeof(m->desc) | (m->desc[i++] = *l++) != '\\0' | m->desc[i++] = *l++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse",
    "file": "/src/file/src/apprentice.c",
    "line": 2400
   },
   "code": "i = 0 | (m->desc[i++] = *l++) != '\\0' && i < sizeof(m->desc) | (m->desc[i++] = *l++) != '\\0' | m->desc[i++] = *l++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "l == t | l == t | i < sizeof(m->desc)",
   "guard_count": 4,
   "control_structures": "WHILE:2033,IF:2038,IF:2039,IF:2043,IF:2044,IF:2048,IF:2054,IF:2058,IF:2061,ELSE:2072,IF:2074,IF:2076"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ms",
   "me",
   "line",
   "lineno"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/93ddf99bc1d4e3dd526d5ae5367c3b4c4800354f/ARVO-376515517/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/file_93ddf99bc1d4.cpg",
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
   "dedup_token": "parse--load_1--apprentice_load"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "i = 0",
     "line": 2400
    }
   ],
   "entity_decl": {
    "line": 2020,
    "type": "size_t"
   },
   "entity_name_cpg": "i",
   "func_lines": [
    2013,
    2423
   ],
   "func_params": {
    "names": [
     "ms",
     "me",
     "line",
     "lineno",
     "action"
    ],
    "types": [
     "magic_set*",
     "magic_entry*",
     "char*",
     "size_t",
     "int"
    ]
   },
   "guards": [
    {
     "code": "*l == '>'",
     "line": 2033
    },
    {
     "code": "cont_level == 0",
     "line": 2038
    },
    {
     "code": "cont_level > last_cont_level",
     "line": 2038
    },
    {
     "code": "file_check_mem(ms, cont_level) == -1",
     "line": 2039
    },
    {
     "code": "cont_level != 0",
     "line": 2043
    },
    {
     "code": "me->mp == NULL",
     "line": 2044
    },
    {
     "code": "me->cont_count == 0",
     "line": 2048
    },
    {
     "code": "diff > 1",
     "line": 2054
    },
    {
     "code": "me->cont_count == me->max_count",
     "line": 2058
    },
    {
     "code": "(nm = CAST(struct magic *, realloc(me->mp,",
     "line": 2061
    },
    {
     "code": "me->mp != NULL",
     "line": 2074
    },
    {
     "code": "(m = CAST(struct magic *, malloc(len))) == NULL",
     "line": 2076
    },
    {
     "code": "*l == '&'",
     "line": 2089
    },
    {
     "code": "*l == '('",
     "line": 2093
    },
    {
     "code": "*l == '&'",
     "line": 2099
    },
    {
     "code": "m->cont_level == 0",
     "line": 2105
    },
    {
     "code": "*l == '-'",
     "line": 2112
    },
    {
     "code": "l == t",
     "line": 2117
    },
    {
     "code": "*l == '.'",
     "line": 2132
    },
    {
     "code": "*l == ','",
     "line": 2132
    },
    {
     "code": "*l == ','",
     "line": 2133
    },
    {
     "code": "*l == '~'",
     "line": 2195
    },
    {
     "code": "(op = get_op(*l)) != -1",
     "line": 2199
    },
    {
     "code": "*l == '('",
     "line": 2203
    },
    {
     "code": "*l == '-'",
     "line": 2207
    },
    {
     "code": "l == t",
     "line": 2209
    },
    {
     "code": "*l++ != ')'",
     "line": 2217
    },
    {
     "code": "*l++ != ')'",
     "line": 2218
    },
    {
     "code": "check_cond(ms, m->cond, cont_level) == -1",
     "line": 2229
    },
    {
     "code": "*l == 'u'",
     "line": 2238
    },
    {
     "code": "m->type == FILE_INVALID",
     "line": 2245
    },
    {
     "code": "m->type != FILE_INVALID",
     "line": 2253
    },
    {
     "code": "m->type == FILE_INVALID",
     "line": 2263
    },
    {
     "code": "*l == 'd'",
     "line": 2269
    },
    {
     "code": "*l == 's'",
     "line": 2271
    },
    {
     "code": "m->type == FILE_INVALID",
     "line": 2279
    },
    {
     "code": "m->type == FILE_INVALID",
     "line": 2284
    },
    {
     "code": "m->type == FILE_NAME",
     "line": 2290
    },
    {
     "code": "cont_level != 0",
     "line": 2290
    },
    {
     "code": "*l == '~'",
     "line": 2301
    },
    {
     "code": "(m->type) == 5",
     "line": 2302
    },
    {
     "code": "(m->type) == 13",
     "line": 2302
    },
    {
     "code": "(m->type) == 18",
     "line": 2302
    },
    {
     "code": "(m->type) == 19",
     "line": 2302
    },
    {
     "code": "(m->type) == 17",
     "line": 2302
    },
    {
     "code": "(m->type) == 20",
     "line": 2302
    },
    {
     "code": "(m->type) == 41",
     "line": 2302
    },
    {
     "code": "(m->type) == 45",
     "line": 2302
    },
    {
     "code": "(m->type) == 46",
     "line": 2302
    },
    {
     "code": "(m->type) == 59",
     "line": 2302
    },
    {
     "code": "m->type == FILE_PSTRING",
     "line": 2309
    },
    {
     "code": "(op = get_op(*l)) != -1",
     "line": 2310
    },
    {
     "code": "(m->type) == 5",
     "line": 2311
    },
    {
     "code": "(m->type) == 13",
     "line": 2311
    },
    {
     "code": "(m->type) == 18",
     "line": 2311
    },
    {
     "code": "(m->type) == 19",
     "line": 2311
    },
    {
     "code": "(m->type) == 17",
     "line": 2311
    },
    {
     "code": "(m->type) == 20",
     "line": 2311
    },
    {
     "code": "(m->type) == 41",
     "line": 2311
    },
    {
     "code": "(m->type) == 45",
     "line": 2311
    },
    {
     "code": "(m->type) == 46",
     "line": 2311
    },
    {
     "code": "(m->type) == 59",
     "line": 2311
    },
    {
     "code": "op != FILE_OPDIVIDE",
     "line": 2314
    },
    {
     "code": "m->type == FILE_INDIRECT",
     "line": 2322
    },
    {
     "code": "r == -1",
     "line": 2326
    },
    {
     "code": "*l == '='",
     "line": 2343
    },
    {
     "code": "*l == '='",
     "line": 2358
    },
    {
     "code": "*l == 'x'",
     "line": 2369
    },
    {
     "code": "m->reln != 'x'",
     "line": 2379
    },
    {
     "code": "l[0] == '\\b'",
     "line": 2392
    },
    {
     "code": "l[0] == '\\\\'",
     "line": 2395
    },
    {
     "code": "l[1] == 'b'",
     "line": 2395
    },
    {
     "code": "(m->desc[i++] = *l++) != '\\0'",
     "line": 2400
    },
    {
     "code": "i < sizeof(m->desc)",
     "line": 2400
    },
    {
     "code": "i == sizeof(m->desc)",
     "line": 2402
    },
    {
     "code": "check_format(ms, m) == -1",
     "line": 2413
    },
    {
     "code": "action == FILE_CHECK",
     "line": 2417
    }
   ],
   "line_call_count": 12,
   "line_calls": [
    {
     "code": "i = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(m->desc[i++] = *l++) != '\\0' && i < sizeof(m->desc)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "(m->desc[i++] = *l++) != '\\0'",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "m->desc[i++] = *l++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "m->desc[i++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "m->desc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "i++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "*l++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "l++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "i < sizeof(m->desc)",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "sizeof(m->desc)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "m->desc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "i",
    "m",
    "l"
   ],
   "osv_id": "ARVO-376515517",
   "sites": [
    {
     "args": "",
     "callee": "ALLOC_CHUNK",
     "code": "ALLOC_CHUNK",
     "line": 2060
    },
    {
     "args": "me->mp ;; sizeof (*nm) * cnt",
     "callee": "realloc",
     "code": "realloc(me->mp, sizeof (*nm) * cnt)",
     "line": 2061
    },
    {
     "args": "",
     "callee": "ALLOC_CHUNK",
     "code": "ALLOC_CHUNK",
     "line": 2073
    },
    {
     "args": "len",
     "callee": "malloc",
     "code": "malloc(len)",
     "line": 2076
    },
    {
     "args": "len",
     "callee": "malloc",
     "code": "malloc(len)",
     "line": 2076
    },
    {
     "args": "",
     "callee": "ALLOC_CHUNK",
     "code": "ALLOC_CHUNK",
     "line": 2081
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse"
  }
 },
 {
  "osv_id": "ARVO-379180960",
  "project": "ndpi",
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
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 146
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "ndpi_search_mikrotik",
    "file": "/src/ndpi/src/lib/protocols/mikrotik.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_mikrotik",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/3ce8d0e5087f6e3f2a3e1f65d39d78c228054a5d/ARVO-379180960/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_3ce8d0e5087f.cpg",
   "testcase_size": 259
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "loc_size": 219,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ndpi_search_mikrotik--check_ndpi_detection_func",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    29,
    107
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
     "code": "packet->iph->daddr== 0xFFFFFFFF",
     "line": 35
    },
    {
     "code": "ntohl(packet->iphv6->ip6_dst.u6_addr.u6_addr32[0]) == 0xFF020000",
     "line": 36
    },
    {
     "code": "ntohs(packet->udp->dest) == 5678",
     "line": 38
    },
    {
     "code": "packet->payload_packet_len < 8",
     "line": 42
    },
    {
     "code": "(offset+4) < packet->payload_packet_len",
     "line": 50
    },
    {
     "code": "(m_len+offset) < packet->payload_packet_len",
     "line": 56
    },
    {
     "code": "m_len == 6",
     "line": 59
    },
    {
     "code": "m_len == 4",
     "line": 71
    },
    {
     "code": "m_len == 16",
     "line": 83
    },
    {
     "code": "m_len == 4",
     "line": 91
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-379180960",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_mikrotik"
  }
 },
 {
  "osv_id": "ARVO-379418968",
  "project": "assimp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "out_mat",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/assimp/code/AssetLib/FBX/FBXExporter.cpp",
    "line": 2039,
    "size": null,
    "type": "aiMaterial*"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "__libcpp_operator_new<unsigned long>",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 245
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2053,
    "fn": "Assimp::FBXExporter::WriteObjects()",
    "code": "TrySetTextureProperties(out_mat, _textures, \"ReflectionF",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Assimp::FBXExporter::WriteObjects()",
    "file": "/src/assimp/code/AssetLib/FBX/FBXExporter.cpp",
    "line": 2053
   },
   "code": "TrySetTextureProperties(out_mat, _textures, \"ReflectionF",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "SetTextureProperties",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:2096,IF:2098,ELSE:2102,IF:2102,ELSE:2106"
  },
  "call_chain": [],
  "types": {
   "entity_type": "aiMaterial*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "out_mat",
   "_textures",
   "mesh"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/0c4d5909f8ca1931f3ca5c66ab5f0c37ea2efc2e/ARVO-379418968/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_0c4d5909f8ca.cpg",
   "testcase_size": 1400
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
   "dedup_token": "Assimp::FBXExporter::WriteObjects()--WriteAllNodes--Assimp::FBXExporter::ExportBinary(char const*, Assimp::IOSystem*)"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 2039,
    "type": "aiMaterial*"
   },
   "entity_name_cpg": "out_mat",
   "func_lines": [
    2039,
    2110
   ],
   "func_params": {
    "names": [
     "this",
     "out_mat",
     "_textures",
     "mesh"
    ],
    "types": [
     "Assimp.FBX.FBXConverter",
     "aiMaterial*",
     "TextureMap&",
     "MeshGeometry*const"
    ]
   },
   "guards": [
    {
     "code": "out_mat->Get(\"$raw.3dsMax",
     "line": 2096
    },
    {
     "code": "useGlossiness == 1",
     "line": 2098
    },
    {
     "code": "useGlossiness == 2",
     "line": 2102
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "TrySetTextureProperties(out_mat, _textures, \"ReflectionFactor\", aiTextureType_METALNESS, mesh)",
     "name": "TrySetTextureProperties",
     "nargs": 5
    }
   ],
   "line_ids": [
    "out_mat",
    "_textures",
    "aiTextureType_METALNESS",
    "mesh"
   ],
   "osv_id": "ARVO-379418968",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Assimp::FBXExporter::WriteObjects()"
  }
 },
 {
  "osv_id": "ARVO-386688710",
  "project": "opencv",
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
    "line": 271
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 661,
    "fn": "cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)",
    "file": "/src/opencv/modules/imgcodecs/src/grfmt_png.cpp",
    "line": 661
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opencv/address/8bc65a1d136c2ac4c31910ee271b5f3c9d14317e/ARVO-386688710/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opencv_8bc65a1d136c.cpg",
   "testcase_size": 12
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
   "loc_size": 8,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)--cv::PngDecoder::read_chunk(cv::Chunk&)",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)"
  }
 },
 {
  "osv_id": "ARVO-387317434",
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
    "fn": "g_malloc0 (/out/matrixsave_buffer_fuzzer+0xba9d60)",
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
    "line": 2100,
    "fn": "rtiff_decompress_jpeg_run",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "rtiff_decompress_jpeg_run",
    "file": "/src/libvips/libvips/foreign/tiff2vips.c",
    "line": 2100
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rtiff_decompress_jpeg_run",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-387317434/report.log",
   "cpg": null,
   "testcase_size": 378
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
   "loc_size": 524288,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "next_marker--read_markers--consume_markers",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "rtiff_decompress_jpeg_run"
  }
 },
 {
  "osv_id": "ARVO-390788198",
  "project": "opencv",
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
    "fn": "cv::fastMalloc(unsigned long)",
    "file": "/src/opencv/modules/core/src/alloc.cpp",
    "line": 137
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 654,
    "fn": "operator()",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "operator()",
    "file": "/src/opencv/modules/imgcodecs/src/grfmt_png.cpp",
    "line": 654
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 600,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "operator()",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opencv/address/ff18c9cc7904e878b10273265196e0238490e692/ARVO-390788198/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opencv_ff18c9cc7904.cpg",
   "testcase_size": 2928
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
   "loc_size": 90000,
   "loc_offset": 1448,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--operator()--__invoke<(lambda at /src/opencv/modules/imgcodecs/src/grfmt_png.cpp:647:44) &, const cv::Range &>",
   "overshoot_ratio": 0.016089
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "operator()"
  }
 },
 {
  "osv_id": "ARVO-391689728",
  "project": "kamailio",
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
    "line": 304,
    "fn": "extract_candidate",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "extract_candidate",
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "line": 304
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "extract_candidate",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-391689728/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 1297
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
   "dedup_token": "memchr--extract_candidate--parse_sdp_session"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "extract_candidate"
  }
 },
 {
  "osv_id": "ARVO-391975654",
  "project": "kamailio",
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
    "line": 475,
    "fn": "extract_mediaip",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "extract_mediaip",
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "line": 475
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "extract_mediaip",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-391975654/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 6978
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
   "dedup_token": "extract_mediaip--parse_sdp_session--parse_mixed_content"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "extract_mediaip"
  }
 },
 {
  "osv_id": "ARVO-396460413",
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
    "fn": "HeifPixelImage::ImagePlane::alloc(unsigned int, unsigned int, heif_channel_datatype, int, int, heif_security_limits const*)",
    "file": "/src/libheif/libheif/pixelimage.cc",
    "line": 279
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 383,
    "fn": "vips_foreign_save_heif_pack",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vips_foreign_save_heif_pack",
    "file": "/src/libvips/libvips/foreign/heifsave.c",
    "line": 383
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 248,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vips_foreign_save_heif_pack",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-396460413/report.log",
   "cpg": null,
   "testcase_size": 398
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
   "loc_size": 19215,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--vips_foreign_save_heif_pack--vips_foreign_save_heif_write_block",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vips_foreign_save_heif_pack"
  }
 },
 {
  "osv_id": "ARVO-397731139",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1287,
    "size": null,
    "type": "ndpi_flow_info*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "get_ndpi_flow_info",
    "file": "/src/ndpi/fuzz/../example/reader_util.c",
    "line": 929
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "128",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1379,
    "fn": "process_ndpi_collected_info",
    "code": "strncat(flow->info + length, flow->ndpi_flow->protos.slp | flow->info + length | flow->info | flow->ndpi_flow->protos.slp.url[i]",
    "origin": "report:crash"
   },
   {
    "code": "strdup(flow->ndpi_flow->protos.tls_quic.ja4_client_raw)",
    "fn": "process_ndpi_collected_info",
    "kind": "strdup",
    "line": 1548,
    "origin": "cpg",
    "args": "flow->ndpi_flow->protos.tls_quic.ja4_client_raw"
   },
   {
    "code": "strdup(flow->ndpi_flow->protos.tls_quic.issuerDN)",
    "fn": "process_ndpi_collected_info",
    "kind": "strdup",
    "line": 1564,
    "origin": "cpg",
    "args": "flow->ndpi_flow->protos.tls_quic.issuerDN"
   },
   {
    "code": "strdup(flow->ndpi_flow->protos.tls_quic.subjectDN)",
    "fn": "process_ndpi_collected_info",
    "kind": "strdup",
    "line": 1567,
    "origin": "cpg",
    "args": "flow->ndpi_flow->protos.tls_quic.subjectDN"
   }
  ],
  "crash": {
   "site": {
    "fn": "process_ndpi_collected_info",
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1379
   },
   "code": "strncat(flow->info + length, flow->ndpi_flow->protos.slp | flow->info + length | flow->info | flow->ndpi_flow->protos.slp.url[i]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "process_ndpi_collected_info",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < sizeof(flow->ndpi_flow->protos.bittorrent.hash) | i < flow->ndpi_flow->protos.slp.url_count | i < (size_t)flow->ndpi_flow->protos.slp.url_count - 1",
   "guard_count": 4,
   "control_structures": "IF:1291,IF:1297,IF:1309,IF:1316,IF:1317,IF:1320,ELSE:1322,IF:1322,IF:1327,IF:1331,FOR:1332,ELSE:1344"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_flow_info*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/9ee24d5bc110307b988554d83d1a88a6ad63490e/ARVO-397731139/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_9ee24d5bc110.cpg",
   "testcase_size": 94
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
   "loc_size": 1176,
   "loc_offset": 25,
   "loc_kind": "region",
   "dedup_token": "___interceptor_strncat--process_ndpi_collected_info--node_cleanup_walker",
   "overshoot_ratio": 0.021259
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->info_type = INFO_INVALID",
     "line": 1293
    },
    {
     "code": "flow->risk_str = ndpi_strdup(s)",
     "line": 1298
    },
    {
     "code": "flow->confidence = flow->ndpi_flow->confidence",
     "line": 1300
    },
    {
     "code": "flow->fpc = flow->ndpi_flow->fpc",
     "line": 1302
    },
    {
     "code": "flow->num_dissector_calls = flow->ndpi_flow->num_dissector_calls",
     "line": 1304
    },
    {
     "code": "flow->risk = flow->ndpi_flow->risk",
     "line": 1314
    },
    {
     "code": "flow->dhcp_fingerprint = ndpi_strdup(flow->ndpi_flow->protos.dhcp.fingerprint)",
     "line": 1318
    },
    {
     "code": "flow->dhcp_class_ident = ndpi_strdup(flow->ndpi_flow->protos.dhcp.class_ident)",
     "line": 1321
    },
    {
     "code": "flow->bittorent_hash = ndpi_malloc(avail)",
     "line": 1329
    },
    {
     "code": "flow->bittorent_hash[j] = '\\0'",
     "line": 1339
    },
    {
     "code": "flow->info_type = INFO_TIVOCONNECT",
     "line": 1345
    },
    {
     "code": "flow->info_type = INFO_SOFTETHER",
     "line": 1357
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1371
    },
    {
     "code": "flow->info[0] = 0",
     "line": 1372
    },
    {
     "code": "flow->info_type = INFO_NATPMP",
     "line": 1389
    },
    {
     "code": "flow->natpmp.result_code = flow->ndpi_flow->protos.natpmp.result_code",
     "line": 1390
    },
    {
     "code": "flow->natpmp.internal_port = flow->ndpi_flow->protos.natpmp.internal_port",
     "line": 1391
    },
    {
     "code": "flow->natpmp.external_port = flow->ndpi_flow->protos.natpmp.external_port",
     "line": 1392
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1400
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1408
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1411
    },
    {
     "code": "flow->dns.transaction_id = flow->ndpi_flow->protos.dns.transaction_id",
     "line": 1424
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1446
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1451
    },
    {
     "code": "flow->info_type = INFO_FTP_IMAP_POP_SMTP",
     "line": 1459
    },
    {
     "code": "flow->ftp_imap_pop_smtp.auth_failed =",
     "line": 1466
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1471
    },
    {
     "code": "flow->info_type = INFO_KERBEROS",
     "line": 1478
    },
    {
     "code": "flow->info_type = INFO_GENERIC",
     "line": 1490
    },
    {
     "code": "flow->info_type = INFO_SIP",
     "line": 1497
    },
    {
     "code": "flow->telnet.username = ndpi_strdup(flow->ndpi_flow->protos.telnet.username)",
     "line": 1510
    },
    {
     "code": "flow->telnet.password = ndpi_strdup(flow->ndpi_flow->protos.telnet.password)",
     "line": 1512
    },
    {
     "code": "flow->ssh_tls.ssl_version = flow->ndpi_flow->protos.tls_quic.ssl_version",
     "line": 1533
    },
    {
     "code": "flow->ssh_tls.quic_version = flow->ndpi_flow->protos.tls_quic.quic_version",
     "line": 1534
    },
    {
     "code": "flow->idle_timeout_sec = flow->ndpi_flow->protos.tls_quic.quic_idle_timeout_sec",
     "line": 1537
    },
    {
     "code": "flow->ssh_tls.server_names = ndpi_strdup(flow->ndpi_flow->protos.tls_quic.server_names)",
     "line": 1540
    },
    {
     "code": "flow->ssh_tls.notBefore = flow->ndpi_flow->protos.tls_quic.notBefore",
     "line": 1542
    },
    {
     "code": "flow->ssh_tls.notAfter = flow->ndpi_flow->protos.tls_quic.notAfter",
     "line": 1543
    },
    {
     "code": "flow->ssh_tls.ja4_client_raw = strdup(flow->ndpi_flow->protos.tls_quic.ja4_client_raw)",
     "line": 1548
    },
    {
     "code": "flow->ssh_tls.server_unsafe_cipher = flow->ndpi_flow->protos.tls_quic.server_unsafe_cipher",
     "line": 1552
    },
    {
     "code": "flow->ssh_tls.server_cipher = flow->ndpi_flow->protos.tls_quic.server_cipher",
     "line": 1553
    },
    {
     "code": "flow->ssh_tls.sha1_cert_fingerprint_set = 1",
     "line": 1558
    },
    {
     "code": "flow->ssh_tls.browser_heuristics = flow->ndpi_flow->protos.tls_quic.browser_heuristics",
     "line": 1561
    },
    {
     "code": "flow->ssh_tls.tls_issuerDN = strdup(flow->ndpi_flow->protos.tls_quic.issuerDN)",
     "line": 1564
    },
    {
     "code": "flow->ssh_tls.tls_subjectDN = strdup(flow->ndpi_flow->protos.tls_quic.subjectDN)",
     "line": 1567
    },
    {
     "code": "flow->ssh_tls.encrypted_ch.version = flow->ndpi_flow->protos.tls_quic.encrypted_ch.version",
     "line": 1569
    },
    {
     "code": "flow->ssh_tls.tls_supported_versions = ndpi_strdup(flow->ndpi_flow->protos.tls_quic.tls_supported_versions)",
     "line": 1572
    },
    {
     "code": "flow->ssh_tls.advertised_alpns = ndpi_strdup(flow->ndpi_flow->protos.tls_quic.advertised_alpns)",
     "line": 1577
    },
    {
     "code": "flow->ssh_tls.negotiated_alpn = ndpi_strdup(flow->ndpi_flow->protos.tls_quic.negotiated_alpn)",
     "line": 1582
    },
    {
     "code": "flow->tcp_fingerprint = ndpi_strdup(buf)",
     "line": 1618
    },
    {
     "code": "flow->http.response_status_code = flow->ndpi_flow->http.response_status_code",
     "line": 1630
    },
    {
     "code": "flow->rtp.payload_type = flow->ndpi_flow->protos.rtp.payload_type",
     "line": 1641
    },
    {
     "code": "flow->server_hostname = ndpi_strdup(c->hostname)",
     "line": 1661
    },
    {
     "code": "flow->flow_payload = flow->ndpi_flow->flow_payload",
     "line": 1690
    },
    {
     "code": "flow->flow_payload_len = flow->ndpi_flow->flow_payload_len",
     "line": 1690
    },
    {
     "code": "flow->ndpi_flow->flow_payload = NULL",
     "line": 1691
    }
   ],
   "entity_decl": {
    "line": 1287,
    "type": "ndpi_flow_info*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    1287,
    1701
   ],
   "func_params": {
    "names": [
     "workflow",
     "flow"
    ],
    "types": [
     "ndpi_workflow*",
     "ndpi_flow_info*"
    ]
   },
   "guards": [
    {
     "code": "s != NULL",
     "line": 1297
    },
    {
     "code": "flow->ndpi_flow->protos.dhcp.fingerprint[0] != '\\0'",
     "line": 1317
    },
    {
     "code": "flow->ndpi_flow->protos.dhcp.class_ident[0] != '\\0'",
     "line": 1320
    },
    {
     "code": "flow->ndpi_flow->protos.bittorrent.hash[0] != '\\0'",
     "line": 1327
    },
    {
     "code": "i < sizeof(flow->ndpi_flow->protos.bittorrent.hash)",
     "line": 1332
    },
    {
     "code": "flow->ndpi_flow->protos.slp.url_count > 0",
     "line": 1373
    },
    {
     "code": "i < flow->ndpi_flow->protos.slp.url_count",
     "line": 1376
    },
    {
     "code": "i < (size_t)flow->ndpi_flow->protos.slp.url_count - 1",
     "line": 1383
    },
    {
     "code": "flow->ndpi_flow->protos.discord.client_ip[0] != '\\0'",
     "line": 1399
    },
    {
     "code": "flow->ndpi_flow->protos.dns.is_rsp_addr_ipv6[0] == 0",
     "line": 1406
    },
    {
     "code": "flow->ndpi_flow->protos.dns.geolocation_iata_code[0] != '\\0'",
     "line": 1418
    },
    {
     "code": "flow->ndpi_flow->protos.dns.ptr_domain_name[0] != '\\0'",
     "line": 1421
    },
    {
     "code": "flow->ndpi_flow->protos.tftp.filename[0] != '\\0'",
     "line": 1472
    },
    {
     "code": "flow->ndpi_flow->protos.collectd.client_username[0] != '\\0'",
     "line": 1491
    },
    {
     "code": "flow->ndpi_flow->protos.sip.from_imsi[0] != '\\0'",
     "line": 1500
    },
    {
     "code": "flow->ndpi_flow->protos.sip.to_imsi[0] != '\\0'",
     "line": 1504
    },
    {
     "code": "flow->ndpi_flow->protos.telnet.username[0] != '\\0'",
     "line": 1509
    },
    {
     "code": "flow->ndpi_flow->protos.telnet.password[0] != '\\0'",
     "line": 1511
    },
    {
     "code": "flow->ndpi_flow->protos.tls_quic.server_names_len > 0",
     "line": 1539
    },
    {
     "code": "(flow->ssh_tls.tls_supported_versions = ndpi_strdup(flow->ndpi_flow->protos.tls_quic.tls_supported_versions)) != NULL",
     "line": 1572
    },
    {
     "code": "(flow->ssh_tls.advertised_alpns = ndpi_strdup(flow->ndpi_flow->protos.tls_quic.advertised_alpns)) != NULL",
     "line": 1577
    },
    {
     "code": "(flow->ssh_tls.negotiated_alpn = ndpi_strdup(flow->ndpi_flow->protos.tls_quic.negotiated_alpn)) != NULL",
     "line": 1582
    },
    {
     "code": "i<flow->ndpi_flow->l4.tcp.tls.num_tls_blocks",
     "line": 1590
    },
    {
     "code": "flow->ndpi_flow->http.url != NULL",
     "line": 1626
    },
    {
     "code": "flow->ip_version == 4",
     "line": 1653
    },
    {
     "code": "workflow->ndpi_serialization_format != ndpi_serialization_format_unknown",
     "line": 1665
    },
    {
     "code": "ndpi_flow2json(workflow->ndpi_struct, flow->ndpi_flow,",
     "line": 1666
    },
    {
     "code": "workflow->flow_callback != NULL",
     "line": 1693
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "strncat(flow->info + length, flow->ndpi_flow->protos.slp.url[i],",
     "name": "strncat",
     "nargs": null
    },
    {
     "code": "flow->info + length",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "flow->info",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->ndpi_flow->protos.slp.url[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "flow->ndpi_flow->protos.slp.url",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->ndpi_flow->protos.slp",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->ndpi_flow->protos",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->ndpi_flow",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "flow",
    "length",
    "i"
   ],
   "osv_id": "ARVO-397731139",
   "sites": [
    {
     "args": "128",
     "callee": "<operator>.alloc",
     "code": "out[128]",
     "line": 1289
    },
    {
     "args": "s",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(s)",
     "line": 1298
    },
    {
     "args": "flow->ndpi_flow->protos.dhcp.fingerprint",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.dhcp.fingerprint)",
     "line": 1318
    },
    {
     "args": "flow->ndpi_flow->protos.dhcp.class_ident",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.dhcp.class_ident)",
     "line": 1321
    },
    {
     "args": "avail",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(avail)",
     "line": 1329
    },
    {
     "args": "flow->ndpi_flow->protos.telnet.username",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.telnet.username)",
     "line": 1510
    },
    {
     "args": "flow->ndpi_flow->protos.telnet.password",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.telnet.password)",
     "line": 1512
    },
    {
     "args": "flow->ndpi_flow->protos.tls_quic.server_names",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.tls_quic.server_names)",
     "line": 1540
    },
    {
     "args": "flow->ndpi_flow->protos.tls_quic.ja4_client_raw",
     "callee": "strdup",
     "code": "strdup(flow->ndpi_flow->protos.tls_quic.ja4_client_raw)",
     "line": 1548
    },
    {
     "args": "flow->ndpi_flow->protos.tls_quic.issuerDN",
     "callee": "strdup",
     "code": "strdup(flow->ndpi_flow->protos.tls_quic.issuerDN)",
     "line": 1564
    },
    {
     "args": "flow->ndpi_flow->protos.tls_quic.subjectDN",
     "callee": "strdup",
     "code": "strdup(flow->ndpi_flow->protos.tls_quic.subjectDN)",
     "line": 1567
    },
    {
     "args": "flow->ndpi_flow->protos.tls_quic.tls_supported_versions",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.tls_quic.tls_supported_versions)",
     "line": 1572
    },
    {
     "args": "flow->ndpi_flow->protos.tls_quic.advertised_alpns",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.tls_quic.advertised_alpns)",
     "line": 1577
    },
    {
     "args": "flow->ndpi_flow->protos.tls_quic.negotiated_alpn",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(flow->ndpi_flow->protos.tls_quic.negotiated_alpn)",
     "line": 1582
    },
    {
     "args": "128",
     "callee": "<operator>.alloc",
     "code": "buf[128]",
     "line": 1614
    },
    {
     "args": "buf",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(buf)",
     "line": 1618
    },
    {
     "args": "c->hostname",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(c->hostname)",
     "line": 1661
    },
    {
     "args": "flow",
     "callee": "ndpi_free_flow_info_half",
     "code": "ndpi_free_flow_info_half(flow)",
     "line": 1699
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "process_ndpi_collected_info"
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