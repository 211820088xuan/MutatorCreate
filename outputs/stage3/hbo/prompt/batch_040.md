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
  "osv_id": "OSV-2024-1124",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "u4_clz_m",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "mvcd_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/mvc_dec_fuzzer.cpp",
    "line": 61
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 369,
    "fn": "ih264d_read_coeff4x4_cabac",
    "code": "u4_clz_m = CLZ(u4_code_int_range) | CLZ(u4_code_int_range) | UWORD32 * | UWORD32",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_read_coeff4x4_cabac",
    "file": "/src/libavc/decoder/ih264d_parse_cabac.c",
    "line": 369
   },
   "code": "u4_clz_m = CLZ(u4_code_int_range) | CLZ(u4_code_int_range) | UWORD32 * | UWORD32",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_read_coeff4x4_cabac",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "u4_code_int_val_ofst >= u4_code_int_range | u4_code_int_range < ONE_RIGHT_SHIFTED_BY_8 | u4_code_int_val_ofst >= u4_code_int_range",
   "guard_count": 10
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "ps_bitstrm",
   "u4_ctxcat",
   "ps_ctxt_sig_coeff",
   "ps_dec",
   "ps_ctxt_coded"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-1124.log",
   "cpg": null,
   "testcase_size": 1034896
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
   "loc_size": 479351,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "ih264d_read_coeff4x4_cabac--ih264d_cabac_parse_8x8block--ih264d_parse_residual4x4_cabac",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_read_coeff4x4_cabac"
  }
 },
 {
  "osv_id": "OSV-2024-1356",
  "project": "libwebp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "char* std::__1::__libcpp_allocate[abi:ne220000]<char>(std::__1::__element_count, unsigned long)",
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "line": 43
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 89,
    "fn": "WebPDataCopy",
    "code": "memcpy((void*)dst->bytes, src->bytes, src->size) | (void*)dst->bytes | dst->bytes | src->bytes",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WebPDataCopy",
    "file": "/src/libwebp/src/webp/mux_types.h",
    "line": 89
   },
   "code": "memcpy((void*)dst->bytes, src->bytes, src->size) | (void*)dst->bytes | dst->bytes | src->bytes",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "WebPDataCopy",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "src == NULL | dst == NULL",
   "guard_count": 2
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "src",
   "dst"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-1356.log",
   "cpg": null,
   "testcase_size": 58
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
   "loc_size": 20,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--WebPDataCopy--ChunkAssignData",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WebPDataCopy"
  }
 },
 {
  "osv_id": "OSV-2024-161",
  "project": "pcre2",
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
    "line": 302,
    "fn": "LLVMFuzzerTestOneInput",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "line": 302
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "LLVMFuzzerTestOneInput",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-161.log",
   "cpg": null,
   "testcase_size": 8
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
   "loc_size": 8,
   "loc_offset": 4,
   "loc_kind": "region",
   "dedup_token": "LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)--fuzzer::RunOneTest(fuzzer::Fuzzer*, char const*, unsigned long)",
   "overshoot_ratio": 0.5
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "LLVMFuzzerTestOneInput"
  }
 },
 {
  "osv_id": "OSV-2024-173",
  "project": "pcre2",
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
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "line": 302
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 363,
    "fn": "LLVMFuzzerTestOneInput",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "line": 363
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "LLVMFuzzerTestOneInput",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-173.log",
   "cpg": null,
   "testcase_size": 24
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
   "loc_size": 16,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)--fuzzer::RunOneTest(fuzzer::Fuzzer*, char const*, unsigned long)",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "LLVMFuzzerTestOneInput"
  }
 },
 {
  "osv_id": "OSV-2024-187",
  "project": "pcre2",
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
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "line": 303
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 339,
    "fn": "LLVMFuzzerTestOneInput",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "line": 339
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "LLVMFuzzerTestOneInput",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-187.log",
   "cpg": null,
   "testcase_size": 28
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
   "loc_size": 20,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)--fuzzer::RunOneTest(fuzzer::Fuzzer*, char const*, unsigned long)",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "LLVMFuzzerTestOneInput"
  }
 },
 {
  "osv_id": "OSV-2024-370",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "chk_udata",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/hdf5/src/H5Ochunk.c",
    "line": 171,
    "size": null,
    "type": "H5O_chk_cache_ud_t"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 211
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "H5FL_CALLOC"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 178,
    "fn": "H5O__chunk_protect",
    "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5O__chunk_protect",
    "file": "/src/hdf5/src/H5Ochunk.c",
    "line": 178
   },
   "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5O__chunk_protect",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "idx < oh->nchunks | 0 == idx | chk_proxy->oh == oh",
   "guard_count": 5,
   "control_structures": "IF:147,IF:147,IF:155,IF:158,DO:159,DO:159,DO:159,DO:159,GOTO:159,IF:162,DO:163,DO:163"
  },
  "call_chain": [],
  "types": {
   "entity_type": "H5O_chk_cache_ud_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "f",
   "oh",
   "idx"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-370.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_fe7ae303b171.cpg",
   "testcase_size": 1808
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
   "loc_size": 168,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "H5O__chunk_protect--H5O__chunk_delete--H5O__cont_delete",
   "overshoot_ratio": 0.047619
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "chk_udata.oh      = oh",
     "line": 176
    },
    {
     "code": "chk_udata.chunkno = idx",
     "line": 177
    },
    {
     "code": "chk_udata.size    = oh->chunk[idx].size",
     "line": 178
    }
   ],
   "entity_decl": {
    "line": 171,
    "type": "H5O_chk_cache_ud_t"
   },
   "entity_name_cpg": "chk_udata",
   "func_lines": [
    141,
    200
   ],
   "func_params": {
    "names": [
     "f",
     "oh",
     "idx"
    ],
    "types": [
     "H5F_t*",
     "H5O_t*",
     "unsigned"
    ]
   },
   "guards": [
    {
     "code": "'_' == __func__[2]",
     "line": 147
    },
    {
     "code": "'_' == __func__[3]",
     "line": 147
    },
    {
     "code": "'_' == __func__[3]",
     "line": 147
    },
    {
     "code": "'_' == __func__[4]",
     "line": 147
    },
    {
     "code": "'_' == __func__[4]",
     "line": 147
    },
    {
     "code": "'_' == __func__[5]",
     "line": 147
    },
    {
     "code": "idx < oh->nchunks",
     "line": 152
    },
    {
     "code": "0 == idx",
     "line": 155
    },
    {
     "code": "NULL == (chk_proxy = H5FL_CALLOC(H5O_chunk_proxy_t))",
     "line": 158
    },
    {
     "code": "H5O__inc_rc(oh) < 0",
     "line": 162
    },
    {
     "code": "NULL == (chk_proxy = (H5O_chunk_proxy_t *)H5AC_protect(f, H5AC_OHDR_CHK, oh->chunk[idx].addr,",
     "line": 181
    },
    {
     "code": "chk_proxy->oh == oh",
     "line": 186
    },
    {
     "code": "chk_proxy->chunkno == idx",
     "line": 187
    },
    {
     "code": "0 == idx",
     "line": 196
    },
    {
     "code": "H5O__chunk_dest(chk_proxy) < 0",
     "line": 196
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "chk_udata.size    = oh->chunk[idx].size",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "chk_udata.size",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "oh->chunk[idx].size",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "oh->chunk[idx]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "oh->chunk",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "chk_udata",
    "oh",
    "idx"
   ],
   "osv_id": "OSV-2024-370",
   "sites": [
    {
     "args": "",
     "callee": "H5FL_CALLOC",
     "code": "H5FL_CALLOC(H5O_chunk_proxy_t)",
     "line": 158
    },
    {
     "args": "&(H5_H5O_chunk_proxy_t_reg_free_list)",
     "callee": "H5FL_reg_calloc",
     "code": "H5FL_reg_calloc(&(H5_H5O_chunk_proxy_t_reg_free_list))",
     "line": 158
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5O__chunk_protect"
  }
 },
 {
  "osv_id": "OSV-2024-381",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "accum",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 211
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 885,
    "fn": "H5F__accum_free",
    "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5F__accum_free",
    "file": "/src/hdf5/src/H5Faccum.c",
    "line": 885
   },
   "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
   "access": {
    "dir": "READ",
    "width": 361,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5F__accum_free",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "overlap_size < accum->dirty_off | overlap_size < (accum->dirty_off + accum->dirty_len)",
   "guard_count": 2
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "f_sh",
   "addr",
   "size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-381.log",
   "cpg": null,
   "testcase_size": 1808
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
   "loc_size": 520,
   "loc_offset": 41,
   "loc_kind": "region",
   "dedup_token": "__asan_memmove--H5F__accum_free--H5MF_xfree",
   "overshoot_ratio": 0.078846
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5F__accum_free"
  }
 },
 {
  "osv_id": "OSV-2024-387",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/hdf5/src/H5Fint.c",
    "line": 2777,
    "size": null,
    "type": "uint8_t**"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 237
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2796,
    "fn": "H5F_addr_encode_len",
    "code": "*(*pp)++ = 0xff | *(*pp)++ | (*pp)++ | *pp",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5F_addr_encode_len",
    "file": "/src/hdf5/src/H5Fint.c",
    "line": 2796
   },
   "code": "*(*pp)++ = 0xff | *(*pp)++ | (*pp)++ | *pp",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5F_addr_encode_len",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:2782,IF:2787,FOR:2788,ELSE:2794,FOR:2795"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "pp",
   "addr"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-387.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "testcase_size": 1808
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
   "loc_size": 312,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "H5F_addr_encode_len--H5F_addr_encode--H5O__fsinfo_encode",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 2777,
    "type": "uint8_t**"
   },
   "entity_name_cpg": "pp",
   "func_lines": [
    2776,
    2800
   ],
   "func_params": {
    "names": [
     "addr_len",
     "pp",
     "addr"
    ],
    "types": [
     "size_t",
     "uint8_t**",
     "haddr_t"
    ]
   },
   "guards": [
    {
     "code": "'_' != ((const char *)__func__)[2]",
     "line": 2782
    },
    {
     "code": "'_' != ((const char *)__func__)[3]",
     "line": 2782
    },
    {
     "code": "'_' == ((const char *)__func__)[4]",
     "line": 2782
    },
    {
     "code": "(addr) != UINT64_MAX",
     "line": 2787
    },
    {
     "code": "u < addr_len",
     "line": 2788
    },
    {
     "code": "0 == addr",
     "line": 2792
    },
    {
     "code": "u < addr_len",
     "line": 2795
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "*(*pp)++ = 0xff",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*(*pp)++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
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
   "osv_id": "OSV-2024-387",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5F_addr_encode_len"
  }
 },
 {
  "osv_id": "OSV-2024-390",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "image",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/hdf5/src/H5Ocache.c",
    "line": 762,
    "size": null,
    "type": "void*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 211
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 784,
    "fn": "H5O__cache_chk_serialize",
    "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5O__cache_chk_serialize",
    "file": "/src/hdf5/src/H5Ocache.c",
    "line": 784
   },
   "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
   "access": {
    "dir": "READ",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5O__cache_chk_serialize",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "chk_proxy->oh->chunk[chk_proxy->chunkno].size == len",
   "guard_count": 1,
   "control_structures": "IF:767,IF:767,IF:777,DO:778,DO:778,DO:778,DO:778,GOTO:778"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "image",
   "len",
   "_thing"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-390.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_ed082ac981a2.cpg",
   "testcase_size": 1808
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
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--H5O__cache_chk_serialize--H5C__generate_image",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 762,
    "type": "void*"
   },
   "entity_name_cpg": "image",
   "func_lines": [
    761,
    788
   ],
   "func_params": {
    "names": [
     "f",
     "image",
     "len",
     "_thing"
    ],
    "types": [
     "H5F_t*",
     "void*",
     "size_t",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "'_' == __func__[2]",
     "line": 767
    },
    {
     "code": "'_' == __func__[3]",
     "line": 767
    },
    {
     "code": "'_' == __func__[3]",
     "line": 767
    },
    {
     "code": "'_' == __func__[4]",
     "line": 767
    },
    {
     "code": "'_' == __func__[4]",
     "line": 767
    },
    {
     "code": "'_' == __func__[5]",
     "line": 767
    },
    {
     "code": "chk_proxy->cache_info.type == H5AC_OHDR_CHK",
     "line": 772
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno].size == len",
     "line": 774
    },
    {
     "code": "H5O__chunk_serialize(f, chk_proxy->oh, chk_proxy->chunkno) < 0",
     "line": 777
    }
   ],
   "line_call_count": 12,
   "line_calls": [
    {
     "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunkno].image, len)",
     "name": "H5MM_memcpy",
     "nargs": 3
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno].image",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->chunkno",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunkno].image, len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno].image",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->chunkno",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "image",
    "chk_proxy",
    "len"
   ],
   "osv_id": "OSV-2024-390",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5O__cache_chk_serialize"
  }
 },
 {
  "osv_id": "OSV-2024-456",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "read_bits",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "mvcd_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/mvc_dec_fuzzer.cpp",
    "line": 61
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 412,
    "fn": "ih264d_read_coeff4x4_cabac",
    "code": "NEXTBITS(read_bits, u4_offset, pu4_buffer, CABAC_BITS_TO | UWORD32 * | UWORD32 | (u4_offset) >> 5",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_read_coeff4x4_cabac",
    "file": "/src/libavc/decoder/ih264d_parse_cabac.c",
    "line": 412
   },
   "code": "NEXTBITS(read_bits, u4_offset, pu4_buffer, CABAC_BITS_TO | UWORD32 * | UWORD32 | (u4_offset) >> 5",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_read_coeff4x4_cabac",
   "in_loop": true,
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
   "ps_bitstrm",
   "u4_ctxcat",
   "ps_ctxt_sig_coeff",
   "ps_dec",
   "ps_ctxt_coded"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-456.log",
   "cpg": null,
   "testcase_size": 1048576
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
   "loc_size": 379625,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "ih264d_read_coeff4x4_cabac--ih264d_parse_residual4x4_cabac--ih264d_parse_imb_cabac",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_read_coeff4x4_cabac"
  }
 },
 {
  "osv_id": "OSV-2024-637",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pu1_dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc",
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 497,
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "code": "memcpy(pu1_dst, pu1_src, num_cols)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "file": "/src/libavc/decoder/ih264d_format_conv.c",
    "line": 497
   },
   "code": "memcpy(pu1_dst, pu1_src, num_cols)",
   "access": {
    "dir": "WRITE",
    "width": 48,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j < num_cols",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "pu1_y_src",
   "pu1_y_dst",
   "wd",
   "src_y_strd",
   "dst_y_strd"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-637.log",
   "cpg": null,
   "testcase_size": 6180
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
   "loc_size": 3072,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ih264d_fmt_conv_420sp_to_420sp_swap_uv--ih264d_format_convert",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv"
  }
 },
 {
  "osv_id": "OSV-2024-638",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pu1_dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc",
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 497,
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "code": "memcpy(pu1_dst, pu1_src, num_cols)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "file": "/src/libavc/decoder/ih264d_format_conv.c",
    "line": 497
   },
   "code": "memcpy(pu1_dst, pu1_src, num_cols)",
   "access": {
    "dir": "WRITE",
    "width": 32,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j < num_cols",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "pu1_y_src",
   "pu1_y_dst",
   "wd",
   "src_y_strd",
   "dst_y_strd"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-638.log",
   "cpg": null,
   "testcase_size": 966
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
   "loc_size": 1664,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ih264d_fmt_conv_420sp_to_420sp_swap_uv--ih264d_format_convert",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv"
  }
 },
 {
  "osv_id": "OSV-2024-831",
  "project": "jq",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "fmt_s",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/jq/src/jv.c",
    "line": 577,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "jv_mem_alloc",
    "file": "/src/jq/src/jv_alloc.c",
    "line": 141
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
    "line": 577,
    "fn": "jvp_literal_number_new",
    "code": "* fmt_s = jv_string_value(fmt) | jv_string_value(fmt)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "jvp_literal_number_new",
    "file": "/src/jq/src/jv.c",
    "line": 577
   },
   "code": "* fmt_s = jv_string_value(fmt) | jv_string_value(fmt)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "f_format",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:573,IF:578,ELSE:581,IF:581,ELSE:584,IF:584,IF:587,ELSE:592,IF:600,FOR:603,FOR:603,IF:604"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "fmt"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-831.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/jq_6d8e9f98ae3c.cpg",
   "testcase_size": 412
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
   "loc_size": 17,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "___interceptor_strlen--jvp_literal_number_new--jv_number_with_literal",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* fmt_s = jv_string_value(fmt)",
     "line": 577
    }
   ],
   "entity_decl": {
    "line": 577,
    "type": "char*"
   },
   "entity_name_cpg": "fmt_s",
   "func_lines": [
    572,
    802
   ],
   "func_params": {
    "names": [
     "jq",
     "input",
     "fmt"
    ],
    "types": [
     "jq_state*",
     "jv",
     "jv"
    ]
   },
   "guards": [
    {
     "code": "jv_get_kind(fmt) != JV_KIND_STRING",
     "line": 573
    },
    {
     "code": "jv_get_kind(input) != JV_KIND_ARRAY",
     "line": 600
    },
    {
     "code": "i < jv_len__",
     "line": 603
    },
    {
     "code": "jv_number_value(x) != jv_number_value(x)",
     "line": 615
    },
    {
     "code": "i<jv_string_length_bytes(jv_copy(input))",
     "line": 649
    },
    {
     "code": "ch < 128",
     "line": 651
    },
    {
     "code": "*s != '%'",
     "line": 668
    },
    {
     "code": "b == 0",
     "line": 675
    },
    {
     "code": "b < 4",
     "line": 675
    },
    {
     "code": "*(s++) != '%'",
     "line": 676
    },
    {
     "code": "i<2",
     "line": 680
    },
    {
     "code": "jv_get_kind(input) != JV_KIND_ARRAY",
     "line": 704
    },
    {
     "code": "i < jv_len__",
     "line": 707
    },
    {
     "code": "i<len",
     "line": 738
    },
    {
     "code": "j<3",
     "line": 741
    },
    {
     "code": "j < n",
     "line": 743
    },
    {
     "code": "j<4",
     "line": 746
    },
    {
     "code": "n < 3",
     "line": 749
    },
    {
     "code": "n < 2",
     "line": 750
    },
    {
     "code": "i<len",
     "line": 766
    },
    {
     "code": "data[i] != '='",
     "line": 766
    },
    {
     "code": "BASE64_DECODE_TABLE[data[i]] == BASE64_INVALID_ENTRY",
     "line": 767
    },
    {
     "code": "input_bytes_read == 4",
     "line": 776
    },
    {
     "code": "input_bytes_read == 3",
     "line": 784
    },
    {
     "code": "input_bytes_read == 2",
     "line": 787
    },
    {
     "code": "input_bytes_read == 1",
     "line": 789
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "* fmt_s = jv_string_value(fmt)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "jv_string_value(fmt)",
     "name": "jv_string_value",
     "nargs": 1
    }
   ],
   "line_ids": [
    "fmt_s",
    "fmt"
   ],
   "osv_id": "OSV-2024-831",
   "sites": [
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 574
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 579
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 582
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 599
    },
    {
     "args": "x",
     "callee": "jv_free",
     "code": "jv_free(x)",
     "line": 608
    },
    {
     "args": "x",
     "callee": "jv_free",
     "code": "jv_free(x)",
     "line": 617
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 629
    },
    {
     "args": "line",
     "callee": "jv_free",
     "code": "jv_free(line)",
     "line": 630
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 634
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 637
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 640
    },
    {
     "args": "128",
     "callee": "<operator>.alloc",
     "code": "unreserved[128] = {0}",
     "line": 643
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 658
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 661
    },
    {
     "args": "4",
     "callee": "<operator>.alloc",
     "code": "unicode[4] = {0}",
     "line": 671
    },
    {
     "args": "line",
     "callee": "jv_free",
     "code": "jv_free(line)",
     "line": 677
    },
    {
     "args": "line",
     "callee": "jv_free",
     "code": "jv_free(line)",
     "line": 687
    },
    {
     "args": "line",
     "callee": "jv_free",
     "code": "jv_free(line)",
     "line": 694
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 700
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 703
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 725
    },
    {
     "args": "line",
     "callee": "jv_free",
     "code": "jv_free(line)",
     "line": 726
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 730
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 733
    },
    {
     "args": "4",
     "callee": "<operator>.alloc",
     "code": "buf[4]",
     "line": 745
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 753
    },
    {
     "args": "fmt",
     "callee": "jv_free",
     "code": "jv_free(fmt)",
     "line": 756
    },
    {
     "args": "decoded_len ;; sizeof(char)",
     "callee": "jv_mem_calloc",
     "code": "jv_mem_calloc(decoded_len, sizeof(char))",
     "line": 761
    },
    {
     "args": "result",
     "callee": "free",
     "code": "free(result)",
     "line": 768
    },
    {
     "args": "result",
     "callee": "free",
     "code": "free(result)",
     "line": 790
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 795
    },
    {
     "args": "result",
     "callee": "free",
     "code": "free(result)",
     "line": 796
    },
    {
     "args": "input",
     "callee": "jv_free",
     "code": "jv_free(input)",
     "line": 799
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "jvp_literal_number_new"
  }
 },
 {
  "osv_id": "OSV-2024-919",
  "project": "jq",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "s",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "jv_mem_alloc",
    "file": "/src/jq/src/jv_alloc.c",
    "line": 141
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 96,
    "fn": "validate_relpath",
    "code": "strchr(s, '\\\\')",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "validate_relpath",
    "file": "/src/jq/src/linker.c",
    "line": 96
   },
   "code": "strchr(s, '\\\\')",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "validate_relpath",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-919.log",
   "cpg": null,
   "testcase_size": 24
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
   "loc_size": 17,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__interceptor_strchr--validate_relpath--load_module_meta",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "validate_relpath"
  }
 },
 {
  "osv_id": "OSV-2025-796",
  "project": "libwebp",
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
    "fn": "AllocateInternalBuffers32b",
    "file": "/src/libwebp/src/dec/vp8l_dec.c",
    "line": 1609
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 349,
    "fn": "AddGreenToBlueAndRed_AVX2",
    "code": "ErrorGIFNotAvailable()",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AddGreenToBlueAndRed_AVX2",
    "file": "/src/libwebp/src/dsp/lossless_avx2.c",
    "line": 349
   },
   "code": "ErrorGIFNotAvailable()",
   "access": {
    "dir": "WRITE",
    "width": 32,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "GIFReadFrame",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2025-796.log",
   "cpg": null,
   "testcase_size": 131
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
   "loc_size": 247680,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "AddGreenToBlueAndRed_AVX2--VP8LInverseTransform--ApplyInverseTransforms",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AddGreenToBlueAndRed_AVX2"
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