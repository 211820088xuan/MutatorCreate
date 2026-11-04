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
  "osv_id": "OSV-2021-271",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "all_zeros",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2237,
    "type": "bool",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2237,
    "fn": "handle_runlen",
    "code": "all_zeros = src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZER | src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZERO_RUNLEN <<  | src[BLOSC2_CHUNK_BLOSC2_FLAGS] | BLOSC2_ZERO_RUNLEN << 4",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "handle_runlen",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 2237
   },
   "code": "all_zeros = src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZER | src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZERO_RUNLEN <<  | src[BLOSC2_CHUNK_BLOSC2_FLAGS] | BLOSC2_ZERO_RUNLEN << 4",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "handle_runlen",
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
   "src"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-271.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_acd71b1e12cb.cpg",
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
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "loc_size": 16,
   "loc_offset": 1,
   "loc_kind": "region",
   "dedup_token": "handle_runlen--blosc_run_decompression_with_context--blosc2_decompress",
   "overshoot_ratio": 0.0625
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "all_zeros = src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZERO_RUNLEN << 4)",
     "line": 2237
    }
   ],
   "entity_decl": {
    "line": 2237,
    "type": "bool"
   },
   "entity_name_cpg": "all_zeros",
   "func_lines": [
    2223,
    2261
   ],
   "func_params": {
    "names": [
     "context",
     "src",
     "nbytes",
     "dest",
     "destsize"
    ],
    "types": [
     "blosc2_context*",
     "uint8_t*",
     "uint32_t",
     "uint8_t*",
     "int32_t"
    ]
   },
   "guards": [
    {
     "code": "typesize > BLOSC_MAX_TYPESIZE",
     "line": 2234
    },
    {
     "code": "cbytes_chunk != context->header_overhead + typesize",
     "line": 2239
    },
    {
     "code": "cbytes_chunk != context->header_overhead",
     "line": 2239
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "all_zeros = src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZERO_RUNLEN << 4)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZERO_RUNLEN << 4)",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "src[BLOSC2_CHUNK_BLOSC2_FLAGS]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "BLOSC2_ZERO_RUNLEN << 4",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    }
   ],
   "line_ids": [
    "all_zeros",
    "src",
    "BLOSC2_CHUNK_BLOSC2_FLAGS",
    "BLOSC2_ZERO_RUNLEN"
   ],
   "osv_id": "OSV-2021-271",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "handle_runlen"
  }
 },
 {
  "osv_id": "OSV-2021-382",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "idxp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1318,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(blosc2_metalayer) ;; 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1334,
    "fn": "get_vlmeta_from_trailer",
    "code": "idxp[0] != 0xde | idxp[0]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_vlmeta_from_trailer",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1334
   },
   "code": "idxp[0] != 0xde | idxp[0]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_vlmeta_from_trailer",
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
   "trailer"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-382.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_d5622cd1a624.cpg",
   "testcase_size": 98
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
   "loc_size": 98,
   "loc_offset": 6,
   "loc_kind": "region",
   "dedup_token": "get_vlmeta_from_trailer--frame_get_vlmetalayers--frame_to_schunk",
   "overshoot_ratio": 0.061224
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* idxp = trailer + trailer_pos",
     "line": 1318
    }
   ],
   "entity_decl": {
    "line": 1318,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "idxp",
   "func_lines": [
    1314,
    1422
   ],
   "func_params": {
    "names": [
     "frame",
     "schunk",
     "trailer",
     "trailer_len"
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
     "code": "trailer_len < trailer_pos",
     "line": 1322
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1331
    },
    {
     "code": "idxp[0] != 0xde",
     "line": 1334
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1341
    },
    {
     "code": "nmetalayers < 0",
     "line": 1346
    },
    {
     "code": "nmetalayers > BLOSC2_MAX_VLMETALAYERS",
     "line": 1346
    },
    {
     "code": "nmetalayer < nmetalayers",
     "line": 1352
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1354
    },
    {
     "code": "(*idxp & 0xe0u) != 0xa0u",
     "line": 1357
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1367
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1379
    },
    {
     "code": "(*idxp & 0xffu) != 0xd2u",
     "line": 1382
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1388
    },
    {
     "code": "offset < 0",
     "line": 1393
    },
    {
     "code": "*content_marker != 0xc6",
     "line": 1399
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1406
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1414
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "idxp[0] != 0xde",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "idxp[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "idxp"
   ],
   "osv_id": "OSV-2021-382",
   "sites": [
    {
     "args": "sizeof(blosc2_metalayer) ;; 1",
     "callee": "calloc",
     "code": "calloc(sizeof(blosc2_metalayer), 1)",
     "line": 1360
    },
    {
     "args": "(size_t)nslen + 1",
     "callee": "malloc",
     "code": "malloc((size_t)nslen + 1)",
     "line": 1370
    },
    {
     "args": "(size_t)content_len",
     "callee": "malloc",
     "code": "malloc((size_t)content_len)",
     "line": 1417
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "get_vlmeta_from_trailer"
  }
 },
 {
  "osv_id": "OSV-2021-428",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "lazychunk_cbytes",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1839,
    "type": "size_t",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "BLOSC_MIN_HEADER_LENGTH",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1973,
    "fn": "frame_get_lazychunk",
    "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | *chunk + BLOSC2_CHUNK_CBYTES | *chunk",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "frame_get_lazychunk",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1973
   },
   "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | *chunk + BLOSC2_CHUNK_CBYTES | *chunk",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "frame_get_lazychunk",
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
   "frame",
   "nchunk",
   "chunk"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-428.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5eff30b8b3bc.cpg",
   "testcase_size": 187
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
   "loc_size": 187,
   "loc_offset": 115,
   "loc_kind": "region",
   "dedup_token": "frame_get_lazychunk--frame_decompress_chunk--blosc2_schunk_decompress_chunk",
   "overshoot_ratio": 0.614973
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "lazychunk_cbytes = BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 1867
    },
    {
     "code": "lazychunk_cbytes = trailer_offset + trailer_len",
     "line": 1905
    },
    {
     "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES)",
     "line": 1973
    }
   ],
   "entity_decl": {
    "line": 1839,
    "type": "size_t"
   },
   "entity_name_cpg": "lazychunk_cbytes",
   "func_lines": [
    1830,
    1978
   ],
   "func_params": {
    "names": [
     "frame",
     "nchunk",
     "chunk",
     "needs_free"
    ],
    "types": [
     "blosc2_frame_s*",
     "int",
     "uint8_t**",
     "bool*"
    ]
   },
   "guards": [
    {
     "code": "ret < 0",
     "line": 1847
    },
    {
     "code": "ret < 0",
     "line": 1860
    },
    {
     "code": "offset < 0",
     "line": 1865
    },
    {
     "code": "rc < 0",
     "line": 1870
    },
    {
     "code": "frame->cframe == NULL",
     "line": 1876
    },
    {
     "code": "rbytes != BLOSC_MIN_HEADER_LENGTH",
     "line": 1893
    },
    {
     "code": "rbytes != trailer_offset",
     "line": 1917
    },
    {
     "code": "i < (int)nblocks",
     "line": 1941
    },
    {
     "code": "n < (int)nblocks",
     "line": 1951
    },
    {
     "code": "n < (int)nblocks - 1",
     "line": 1958
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "sw32_(*chunk + BLOSC2_CHUNK_CBYTES)",
     "name": "sw32_",
     "nargs": 1
    },
    {
     "code": "*chunk + BLOSC2_CHUNK_CBYTES",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "*chunk",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "lazychunk_cbytes",
    "chunk",
    "BLOSC2_CHUNK_CBYTES"
   ],
   "osv_id": "OSV-2021-428",
   "sites": [
    {
     "args": "BLOSC_MIN_HEADER_LENGTH",
     "callee": "<operator>.alloc",
     "code": "header[BLOSC_MIN_HEADER_LENGTH]",
     "line": 1882
    },
    {
     "args": "lazychunk_cbytes",
     "callee": "malloc",
     "code": "malloc(lazychunk_cbytes)",
     "line": 1906
    },
    {
     "args": "nblocks * sizeof(int32_t)",
     "callee": "malloc",
     "code": "malloc(nblocks * sizeof(int32_t))",
     "line": 1936
    },
    {
     "args": "nblocks * sizeof(struct csize_idx)",
     "callee": "malloc",
     "code": "malloc(nblocks * sizeof(struct csize_idx))",
     "line": 1950
    },
    {
     "args": "csize_idx",
     "callee": "free",
     "code": "free(csize_idx)",
     "line": 1964
    },
    {
     "args": "block_csizes",
     "callee": "free",
     "code": "free(block_csizes)",
     "line": 1969
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "frame_get_lazychunk"
  }
 },
 {
  "osv_id": "OSV-2021-464",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "header",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 668,
    "type": "blosc_header*",
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
    "line": 677,
    "fn": "blosc_read_header",
    "code": "memcpy(header, src, BLOSC_MIN_HEADER_LENGTH)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_read_header",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 677
   },
   "code": "memcpy(header, src, BLOSC_MIN_HEADER_LENGTH)",
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "blosc_read_header",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "srcsize < BLOSC_MIN_HEADER_LENGTH | header->cbytes < BLOSC_MIN_HEADER_LENGTH",
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
   "srcsize",
   "header"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-464.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
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
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "loc_size": 184,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--blosc_read_header--blosc2_cbuffer_sizes",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "header->nbytes = bswap32_(header->nbytes)",
     "line": 682
    },
    {
     "code": "header->blocksize = bswap32_(header->blocksize)",
     "line": 683
    },
    {
     "code": "header->cbytes = bswap32_(header->cbytes)",
     "line": 684
    },
    {
     "code": "header->filter_codes[5] = 0",
     "line": 734
    },
    {
     "code": "header->filter_meta[5] = 0",
     "line": 735
    }
   ],
   "entity_decl": {
    "line": 668,
    "type": "blosc_header*"
   },
   "entity_name_cpg": "header",
   "func_lines": [
    668,
    742
   ],
   "func_params": {
    "names": [
     "src",
     "srcsize",
     "extended_header",
     "header"
    ],
    "types": [
     "uint8_t*",
     "int32_t",
     "bool",
     "blosc_header*"
    ]
   },
   "guards": [
    {
     "code": "srcsize < BLOSC_MIN_HEADER_LENGTH",
     "line": 672
    },
    {
     "code": "header->version > BLOSC_VERSION_FORMAT",
     "line": 687
    },
    {
     "code": "header->cbytes < BLOSC_MIN_HEADER_LENGTH",
     "line": 691
    },
    {
     "code": "header->blocksize > header->nbytes",
     "line": 695
    },
    {
     "code": "header->typesize > BLOSC_MAX_TYPESIZE",
     "line": 699
    },
    {
     "code": "header->cbytes < BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 706
    },
    {
     "code": "srcsize < BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 710
    },
    {
     "code": "runlen_type != 0",
     "line": 719
    },
    {
     "code": "header->nbytes % header->typesize != 0",
     "line": 720
    },
    {
     "code": "runlen_type == BLOSC2_VALUE_RUNLEN",
     "line": 724
    },
    {
     "code": "header->cbytes < BLOSC_EXTENDED_HEADER_LENGTH + header->typesize",
     "line": 725
    },
    {
     "code": "header->version == BLOSC2_VERSION_FORMAT_ALPHA",
     "line": 733
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(header, src, BLOSC_MIN_HEADER_LENGTH)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "header",
    "src",
    "BLOSC_MIN_HEADER_LENGTH"
   ],
   "osv_id": "OSV-2021-464",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "blosc_read_header"
  }
 },
 {
  "osv_id": "OSV-2021-476",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "cbytes",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1217,
    "type": "int32_t",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1349,
    "fn": "blosc_d",
    "code": "cbytes = sw32_(src) | sw32_(src)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_d",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 1349
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-476.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
   "testcase_size": 185
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
   "loc_size": 185,
   "loc_offset": 85,
   "loc_kind": "region",
   "dedup_token": "blosc_d--serial_blosc--do_job",
   "overshoot_ratio": 0.459459
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cbytes = sw32_(src)",
     "line": 1349
    },
    {
     "code": "cbytes = 0",
     "line": 1390
    }
   ],
   "entity_decl": {
    "line": 1217,
    "type": "int32_t"
   },
   "entity_name_cpg": "cbytes",
   "func_lines": [
    1202,
    1455
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
     "code": "rc < 0",
     "line": 1226
    },
    {
     "code": "context->block_maskout != NULL",
     "line": 1230
    },
    {
     "code": "context->src == NULL",
     "line": 1237
    },
    {
     "code": "context->header_overhead == BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 1241
    },
    {
     "code": "context->schunk == NULL",
     "line": 1245
    },
    {
     "code": "context->schunk->frame == NULL",
     "line": 1249
    },
    {
     "code": "(int32_t)rbytes != block_csize",
     "line": 1284
    },
    {
     "code": "chunk_nbytes + context->header_overhead != chunk_cbytes",
     "line": 1295
    },
    {
     "code": "chunk_cbytes < context->header_overhead + (nblock * context->blocksize) + bsize_",
     "line": 1299
    },
    {
     "code": "next_filter(filters, BLOSC2_MAX_FILTERS, 'd') != BLOSC_DELTA",
     "line": 1321
    },
    {
     "code": "neblock == 0",
     "line": 1339
    },
    {
     "code": "j < nstreams",
     "line": 1343
    },
    {
     "code": "srcsize < (signed)sizeof(int32_t)",
     "line": 1344
    },
    {
     "code": "cbytes > 0",
     "line": 1350
    },
    {
     "code": "srcsize < cbytes",
     "line": 1351
    },
    {
     "code": "cbytes == 0",
     "line": 1361
    },
    {
     "code": "cbytes < 0",
     "line": 1366
    },
    {
     "code": "srcsize < (signed)sizeof(uint8_t)",
     "line": 1370
    },
    {
     "code": "cbytes < -255",
     "line": 1382
    },
    {
     "code": "cbytes == neblock",
     "line": 1392
    },
    {
     "code": "compformat == BLOSC_BLOSCLZ_FORMAT",
     "line": 1397
    },
    {
     "code": "nbytes != neblock",
     "line": 1435
    },
    {
     "code": "errcode < 0",
     "line": 1449
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
   "osv_id": "OSV-2021-476",
   "sites": [
    {
     "args": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1)",
     "line": 1269
    },
    {
     "args": "chunkpath",
     "callee": "free",
     "code": "free(chunkpath)",
     "line": 1272
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
  "osv_id": "OSV-2021-481",
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
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.8/decompress/zstd_ddict.c",
    "line": 134
   },
   "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
   "access": {
    "dir": "READ",
    "width": 222,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-481.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
   "testcase_size": 165
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "loc_size": 165,
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
   "osv_id": "OSV-2021-481",
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
  "osv_id": "OSV-2021-485",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1806,
    "fn": "initialize_context_decompression",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "initialize_context_decompression",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 1806
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "initialize_context_decompression",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-485.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
   "testcase_size": 166
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "initialize_context_decompression--blosc_run_decompression_with_context--blosc2_decompress_ctx"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    1748,
    1823
   ],
   "func_params": {
    "names": [
     "context",
     "header",
     "src",
     "srcsize",
     "dest",
     "destsize"
    ],
    "types": [
     "blosc2_context*",
     "blosc_header*",
     "void*",
     "int32_t",
     "void*",
     "int32_t"
    ]
   },
   "guards": [
    {
     "code": "rc < 0",
     "line": 1761
    },
    {
     "code": "context->sourcesize > (int32_t)context->destsize",
     "line": 1766
    },
    {
     "code": "context->block_maskout != NULL",
     "line": 1770
    },
    {
     "code": "context->block_maskout_nitems != context->nblocks",
     "line": 1770
    },
    {
     "code": "srcsize < bstarts_end",
     "line": 1785
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "OSV-2021-485",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "initialize_context_decompression"
  }
 },
 {
  "osv_id": "OSV-2021-496",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "cbytes",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1242,
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
   "size_expr_cpg": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1398,
    "fn": "blosc_d",
    "code": "cbytes = sw32_(src) | sw32_(src)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_d",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 1398
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-496.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_f489cdbd0a25.cpg",
   "testcase_size": 186
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
   "loc_size": 186,
   "loc_offset": 111,
   "loc_kind": "region",
   "dedup_token": "blosc_d--serial_blosc--do_job",
   "overshoot_ratio": 0.596774
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cbytes = sw32_(src)",
     "line": 1398
    },
    {
     "code": "cbytes = 0",
     "line": 1442
    }
   ],
   "entity_decl": {
    "line": 1242,
    "type": "int32_t"
   },
   "entity_name_cpg": "cbytes",
   "func_lines": [
    1227,
    1508
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
     "code": "rc < 0",
     "line": 1251
    },
    {
     "code": "context->block_maskout != NULL",
     "line": 1255
    },
    {
     "code": "context->src == NULL",
     "line": 1262
    },
    {
     "code": "context->header_overhead == BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 1266
    },
    {
     "code": "context->schunk == NULL",
     "line": 1270
    },
    {
     "code": "context->schunk->frame == NULL",
     "line": 1274
    },
    {
     "code": "chunkpath == NULL",
     "line": 1295
    },
    {
     "code": "(int32_t)rbytes != block_csize",
     "line": 1310
    },
    {
     "code": "chunk_nbytes + context->header_overhead != chunk_cbytes",
     "line": 1321
    },
    {
     "code": "chunk_cbytes < context->header_overhead + (nblock * context->blocksize) + bsize_",
     "line": 1325
    },
    {
     "code": "context->postfilter == NULL",
     "line": 1332
    },
    {
     "code": "context->postfilter(&postparams) != 0",
     "line": 1350
    },
    {
     "code": "next_filter(filters, BLOSC2_MAX_FILTERS, 'd') != BLOSC_DELTA",
     "line": 1369
    },
    {
     "code": "context->postfilter != NULL",
     "line": 1370
    },
    {
     "code": "neblock == 0",
     "line": 1388
    },
    {
     "code": "j < nstreams",
     "line": 1392
    },
    {
     "code": "srcsize < (signed)sizeof(int32_t)",
     "line": 1393
    },
    {
     "code": "cbytes > 0",
     "line": 1399
    },
    {
     "code": "srcsize < cbytes",
     "line": 1400
    },
    {
     "code": "cbytes == 0",
     "line": 1410
    },
    {
     "code": "cbytes < 0",
     "line": 1415
    },
    {
     "code": "srcsize < (signed)sizeof(uint8_t)",
     "line": 1419
    },
    {
     "code": "cbytes < -255",
     "line": 1431
    },
    {
     "code": "cbytes == neblock",
     "line": 1444
    },
    {
     "code": "compformat == BLOSC_BLOSCLZ_FORMAT",
     "line": 1449
    },
    {
     "code": "nbytes != neblock",
     "line": 1487
    },
    {
     "code": "context->postfilter != NULL",
     "line": 1498
    },
    {
     "code": "errcode < 0",
     "line": 1502
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
   "osv_id": "OSV-2021-496",
   "sites": [
    {
     "args": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1)",
     "line": 1294
    },
    {
     "args": "chunkpath",
     "callee": "free",
     "code": "free(chunkpath)",
     "line": 1298
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
  "osv_id": "OSV-2021-622",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "content",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1389,
    "type": "char*",
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
   "size_expr_cpg": "sizeof(blosc2_metalayer) ;; 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1390,
    "fn": "get_vlmeta_from_trailer",
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_vlmeta_from_trailer",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1390
   },
   "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
   "access": {
    "dir": "READ",
    "width": 67,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_vlmeta_from_trailer",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "content_len < 0",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "trailer",
   "trailer_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-622.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_2112e1398b74.cpg",
   "testcase_size": 202
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_size": 202,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--get_vlmeta_from_trailer--frame_get_vlmetalayers",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* content = malloc((size_t)content_len)",
     "line": 1389
    }
   ],
   "entity_decl": {
    "line": 1389,
    "type": "char*"
   },
   "entity_name_cpg": "content",
   "func_lines": [
    1283,
    1394
   ],
   "func_params": {
    "names": [
     "frame",
     "schunk",
     "trailer",
     "trailer_len"
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
     "code": "trailer_len < trailer_pos",
     "line": 1291
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1300
    },
    {
     "code": "idxp[0] != 0xde",
     "line": 1303
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1310
    },
    {
     "code": "nmetalayers < 0",
     "line": 1315
    },
    {
     "code": "nmetalayers > BLOSC2_MAX_VLMETALAYERS",
     "line": 1315
    },
    {
     "code": "nmetalayer < nmetalayers",
     "line": 1321
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1323
    },
    {
     "code": "(*idxp & 0xe0u) != 0xa0u",
     "line": 1326
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1336
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1348
    },
    {
     "code": "(*idxp & 0xffu) != 0xd2u",
     "line": 1351
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1357
    },
    {
     "code": "offset < 0",
     "line": 1362
    },
    {
     "code": "*content_marker != 0xc6",
     "line": 1368
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1375
    },
    {
     "code": "content_len < 0",
     "line": 1379
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1386
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
   "osv_id": "OSV-2021-622",
   "sites": [
    {
     "args": "sizeof(blosc2_metalayer) ;; 1",
     "callee": "calloc",
     "code": "calloc(sizeof(blosc2_metalayer), 1)",
     "line": 1329
    },
    {
     "args": "(size_t)nslen + 1",
     "callee": "malloc",
     "code": "malloc((size_t)nslen + 1)",
     "line": 1339
    },
    {
     "args": "(size_t)content_len",
     "callee": "malloc",
     "code": "malloc((size_t)content_len)",
     "line": 1389
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "get_vlmeta_from_trailer"
  }
 },
 {
  "osv_id": "OSV-2021-639",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "_dest",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1339,
    "type": "uint8_t*",
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
   "size_expr_cpg": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1458,
    "fn": "blosc_d",
    "code": "memcpy(_dest, src, bsize_)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_d",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 1458
   },
   "code": "memcpy(_dest, src, bsize_)",
   "access": {
    "dir": "READ",
    "width": 270541055,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "blosc_d",
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
   "thread_context",
   "bsize",
   "memcpyed",
   "src",
   "srcsize",
   "src_offset",
   "nblock",
   "dest",
   "dest_offset",
   "tmp"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-639.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_77b7dfd41f4b.cpg",
   "testcase_size": 138
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_size": 138,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--blosc_d--_blosc_getitem",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "_dest = dest + dest_offset",
     "line": 1429
    },
    {
     "code": "_dest = tmp",
     "line": 1432
    },
    {
     "code": "_dest = tmp",
     "line": 1497
    },
    {
     "code": "_dest = dest + dest_offset",
     "line": 1500
    }
   ],
   "entity_decl": {
    "line": 1339,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "_dest",
   "func_lines": [
    1322,
    1633
   ],
   "func_params": {
    "names": [
     "thread_context",
     "bsize",
     "leftoverblock",
     "memcpyed",
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
     "bool",
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
     "code": "rc < 0",
     "line": 1345
    },
    {
     "code": "context->block_maskout != NULL",
     "line": 1349
    },
    {
     "code": "context->src == NULL",
     "line": 1356
    },
    {
     "code": "context->header_overhead == BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 1361
    },
    {
     "code": "context->schunk == NULL",
     "line": 1365
    },
    {
     "code": "context->schunk->frame == NULL",
     "line": 1369
    },
    {
     "code": "chunkpath == NULL",
     "line": 1390
    },
    {
     "code": "(int32_t)rbytes != block_csize",
     "line": 1405
    },
    {
     "code": "chunk_nbytes + context->header_overhead != chunk_cbytes",
     "line": 1418
    },
    {
     "code": "chunk_cbytes < context->header_overhead + (nblock * context->blocksize) + bsize_",
     "line": 1421
    },
    {
     "code": "context->postfilter != NULL",
     "line": 1430
    },
    {
     "code": "rc < 0",
     "line": 1439
    },
    {
     "code": "rc < 0",
     "line": 1446
    },
    {
     "code": "context->postfilter != NULL",
     "line": 1460
    },
    {
     "code": "context->postfilter(&postparams) != 0",
     "line": 1475
    },
    {
     "code": "next_filter(filters, BLOSC2_MAX_FILTERS, 'd') != BLOSC_DELTA",
     "line": 1494
    },
    {
     "code": "context->postfilter != NULL",
     "line": 1495
    },
    {
     "code": "neblock == 0",
     "line": 1513
    },
    {
     "code": "j < nstreams",
     "line": 1517
    },
    {
     "code": "srcsize < (signed)sizeof(int32_t)",
     "line": 1518
    },
    {
     "code": "cbytes > 0",
     "line": 1524
    },
    {
     "code": "srcsize < cbytes",
     "line": 1525
    },
    {
     "code": "cbytes == 0",
     "line": 1535
    },
    {
     "code": "cbytes < 0",
     "line": 1540
    },
    {
     "code": "srcsize < (signed)sizeof(uint8_t)",
     "line": 1544
    },
    {
     "code": "cbytes < -255",
     "line": 1556
    },
    {
     "code": "cbytes == neblock",
     "line": 1569
    },
    {
     "code": "compformat == BLOSC_BLOSCLZ_FORMAT",
     "line": 1574
    },
    {
     "code": "nbytes != neblock",
     "line": 1612
    },
    {
     "code": "context->postfilter != NULL",
     "line": 1623
    },
    {
     "code": "errcode < 0",
     "line": 1627
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(_dest, src, bsize_)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "_dest",
    "src",
    "bsize_"
   ],
   "osv_id": "OSV-2021-639",
   "sites": [
    {
     "args": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1)",
     "line": 1389
    },
    {
     "args": "chunkpath",
     "callee": "free",
     "code": "free(chunkpath)",
     "line": 1393
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
  "osv_id": "OSV-2021-640",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "content",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1309,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(blosc2_metalayer) ;; 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1310,
    "fn": "get_meta_from_header",
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_meta_from_header",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1310
   },
   "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
   "access": {
    "dir": "READ",
    "width": 6,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_meta_from_header",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "content_len < 0",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "header",
   "header_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-640.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_4d2510757d79.cpg",
   "testcase_size": 173
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "loc_size": 173,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--get_meta_from_header--frame_get_metalayers",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* content = malloc((size_t)content_len)",
     "line": 1309
    }
   ],
   "entity_decl": {
    "line": 1309,
    "type": "char*"
   },
   "entity_name_cpg": "content",
   "func_lines": [
    1206,
    1315
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
     "line": 1213
    },
    {
     "code": "header_len < header_pos",
     "line": 1221
    },
    {
     "code": "metalayers_idx[0] != 0xde",
     "line": 1224
    },
    {
     "code": "header_len < header_pos",
     "line": 1230
    },
    {
     "code": "nmetalayers < 0",
     "line": 1235
    },
    {
     "code": "nmetalayers > BLOSC2_MAX_METALAYERS",
     "line": 1235
    },
    {
     "code": "nmetalayer < nmetalayers",
     "line": 1241
    },
    {
     "code": "header_len < header_pos",
     "line": 1243
    },
    {
     "code": "(*idxp & 0xe0u) != 0xa0u",
     "line": 1246
    },
    {
     "code": "header_len < header_pos",
     "line": 1256
    },
    {
     "code": "header_len < header_pos",
     "line": 1268
    },
    {
     "code": "(*idxp & 0xffu) != 0xd2u",
     "line": 1271
    },
    {
     "code": "header_len < header_pos",
     "line": 1277
    },
    {
     "code": "offset < 0",
     "line": 1282
    },
    {
     "code": "*content_marker != 0xc6",
     "line": 1288
    },
    {
     "code": "header_len < header_pos",
     "line": 1295
    },
    {
     "code": "content_len < 0",
     "line": 1299
    },
    {
     "code": "header_len < header_pos",
     "line": 1306
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
   "osv_id": "OSV-2021-640",
   "sites": [
    {
     "args": "sizeof(blosc2_metalayer) ;; 1",
     "callee": "calloc",
     "code": "calloc(sizeof(blosc2_metalayer), 1)",
     "line": 1249
    },
    {
     "args": "(size_t)nslen + 1",
     "callee": "malloc",
     "code": "malloc((size_t)nslen + 1)",
     "line": 1259
    },
    {
     "args": "(size_t)content_len",
     "callee": "malloc",
     "code": "malloc((size_t)content_len)",
     "line": 1309
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
  "osv_id": "OSV-2021-767",
  "project": "espeak-ng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539,
    "size": null,
    "type": "uint8_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/espeak-ng/tests/ssml-fuzzer.c",
    "line": 49
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 539,
    "fn": "string_decoder_getc_utf_8",
    "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "string_decoder_getc_utf_8",
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539
   },
   "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "string_decoder_getc_utf_8",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "SWITCH:541,IF:552,GOTO:552,IF:554,GOTO:554,IF:559,GOTO:559,IF:561,GOTO:561,IF:563,GOTO:563,IF:568"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "decoder"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-767.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_d8ec91e809e9.cpg",
   "testcase_size": 2
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
   "loc_size": 3,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "string_decoder_getc_utf_8--GetC--ReadClause",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = *decoder->current++",
     "line": 539
    },
    {
     "code": "c = *decoder->current++",
     "line": 554
    },
    {
     "code": "c = *decoder->current++",
     "line": 561
    },
    {
     "code": "c = *decoder->current++",
     "line": 563
    },
    {
     "code": "c = *decoder->current++",
     "line": 570
    },
    {
     "code": "c = *decoder->current++",
     "line": 572
    },
    {
     "code": "c = *decoder->current++",
     "line": 574
    }
   ],
   "entity_decl": {
    "line": 539,
    "type": "uint8_t"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    536,
    584
   ],
   "func_params": {
    "names": [
     "decoder"
    ],
    "types": [
     "espeak_ng_TEXT_DECODER*"
    ]
   },
   "guards": [
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 554
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 561
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 563
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 570
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 572
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 574
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "c = *decoder->current++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*decoder->current++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "decoder->current++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "decoder->current",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c",
    "decoder"
   ],
   "osv_id": "OSV-2021-767",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "string_decoder_getc_utf_8"
  }
 },
 {
  "osv_id": "OSV-2021-779",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "_dest",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2762,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "scontext->tmp_nbytes",
   "size_expr_cpg_callee": "my_malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2833,
    "fn": "_blosc_getitem",
    "code": "memcpy(_dest, _src, ntbytes)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_blosc_getitem",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 2833
   },
   "code": "memcpy(_dest, _src, ntbytes)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_blosc_getitem",
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
   "context",
   "header",
   "src",
   "start",
   "nitems",
   "dest"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-779.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_886d4c9b7833.cpg",
   "testcase_size": 187
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "loc_size": 187,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--_blosc_getitem--blosc2_getitem_ctx",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* _dest = (uint8_t*)(dest)",
     "line": 2762
    }
   ],
   "entity_decl": {
    "line": 2762,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "_dest",
   "func_lines": [
    2759,
    2923
   ],
   "func_params": {
    "names": [
     "context",
     "header",
     "src",
     "srcsize",
     "start",
     "nitems",
     "dest",
     "destsize"
    ],
    "types": [
     "blosc2_context*",
     "blosc_header*",
     "void*",
     "int32_t",
     "int",
     "int",
     "void*",
     "int32_t"
    ]
   },
   "guards": [
    {
     "code": "nitems == 0",
     "line": 2769
    },
    {
     "code": "nitems * header->typesize > destsize",
     "line": 2773
    },
    {
     "code": "start < 0",
     "line": 2781
    },
    {
     "code": "start * header->typesize > header->nbytes",
     "line": 2781
    },
    {
     "code": "stop < 0",
     "line": 2786
    },
    {
     "code": "stop * header->typesize > header->nbytes",
     "line": 2786
    },
    {
     "code": "(uint8_t *)(_src + srcsize) < (uint8_t *)(context->bstarts + context->nblocks)",
     "line": 2793
    },
    {
     "code": "context->header_overhead == BLOSC_EXTENDED_HEADER_LENGTH",
     "line": 2804
    },
    {
     "code": "rc < 0",
     "line": 2813
    },
    {
     "code": "rc < 0",
     "line": 2820
    },
    {
     "code": "header->blocksize > scontext->tmp_blocksize",
     "line": 2845
    },
    {
     "code": "(scontext->tmp) == NULL",
     "line": 2849
    },
    {
     "code": "j < context->nblocks",
     "line": 2856
    },
    {
     "code": "j == context->nblocks - 1",
     "line": 2859
    },
    {
     "code": "context->leftover > 0",
     "line": 2859
    },
    {
     "code": "startb < 0",
     "line": 2874
    },
    {
     "code": "stopb > header->blocksize",
     "line": 2877
    },
    {
     "code": "startb == 0",
     "line": 2892
    },
    {
     "code": "bsize == nitems * header->typesize",
     "line": 2892
    },
    {
     "code": "cbytes < 0",
     "line": 2902
    },
    {
     "code": "context->zfp_cell_nitems > 0",
     "line": 2906
    },
    {
     "code": "cbytes == bsize2",
     "line": 2907
    },
    {
     "code": "cbytes == context->blocksize",
     "line": 2909
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(_dest, _src, ntbytes)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "_dest",
    "_src",
    "ntbytes"
   ],
   "osv_id": "OSV-2021-779",
   "sites": [
    {
     "args": "scontext->tmp",
     "callee": "my_free",
     "code": "my_free(scontext->tmp)",
     "line": 2846
    },
    {
     "args": "scontext->tmp_nbytes",
     "callee": "my_malloc",
     "code": "my_malloc(scontext->tmp_nbytes)",
     "line": 2848
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_blosc_getitem"
  }
 },
 {
  "osv_id": "OSV-2021-787",
  "project": "espeak-ng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539,
    "size": null,
    "type": "uint8_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/espeak-ng/tests/ssml-fuzzer.c",
    "line": 64
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 539,
    "fn": "string_decoder_getc_utf_8",
    "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "string_decoder_getc_utf_8",
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539
   },
   "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "string_decoder_getc_utf_8",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "SWITCH:541,IF:552,GOTO:552,IF:554,GOTO:554,IF:559,GOTO:559,IF:561,GOTO:561,IF:563,GOTO:563,IF:568"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "decoder"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-787.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_55e452cd9b40.cpg",
   "testcase_size": 2
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
   "loc_size": 3,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "string_decoder_getc_utf_8--GetC--ReadClause",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = *decoder->current++",
     "line": 539
    },
    {
     "code": "c = *decoder->current++",
     "line": 554
    },
    {
     "code": "c = *decoder->current++",
     "line": 561
    },
    {
     "code": "c = *decoder->current++",
     "line": 563
    },
    {
     "code": "c = *decoder->current++",
     "line": 570
    },
    {
     "code": "c = *decoder->current++",
     "line": 572
    },
    {
     "code": "c = *decoder->current++",
     "line": 574
    }
   ],
   "entity_decl": {
    "line": 539,
    "type": "uint8_t"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    536,
    584
   ],
   "func_params": {
    "names": [
     "decoder"
    ],
    "types": [
     "espeak_ng_TEXT_DECODER*"
    ]
   },
   "guards": [
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 554
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 561
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 563
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 570
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 572
    },
    {
     "code": "((c = *decoder->current++) & LEADING_2_BITS) != UTF8_TAIL_BITS",
     "line": 574
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "c = *decoder->current++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*decoder->current++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "decoder->current++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "decoder->current",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c",
    "decoder"
   ],
   "osv_id": "OSV-2021-787",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "string_decoder_getc_utf_8"
  }
 },
 {
  "osv_id": "OSV-2021-897",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 819,
    "type": "void*",
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
    "line": 828,
    "fn": "ZSTD_copyRawBlock",
    "code": "ZSTD_memcpy(dst, src, srcSize) | memcpy((dst), (src), (srcSize))",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_copyRawBlock",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/decompress/zstd_decompress.c",
    "line": 828
   },
   "code": "ZSTD_memcpy(dst, src, srcSize) | memcpy((dst), (src), (srcSize))",
   "access": {
    "dir": "READ",
    "width": 37536,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ZSTD_copyRawBlock",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "srcSize > dstCapacity | dst == NULL | srcSize == 0",
   "guard_count": 3
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "dst",
   "dstCapacity",
   "src",
   "srcSize"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-897.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5a50726608d0.cpg",
   "testcase_size": 11408
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
   "loc_size": 11408,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ZSTD_copyRawBlock--ZSTD_decompressFrame",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 819,
    "type": "void*"
   },
   "entity_name_cpg": "dst",
   "func_lines": [
    819,
    830
   ],
   "func_params": {
    "names": [
     "dst",
     "dstCapacity",
     "src",
     "srcSize"
    ],
    "types": [
     "void*",
     "size_t",
     "void*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "srcSize > dstCapacity",
     "line": 823
    },
    {
     "code": "dst == NULL",
     "line": 824
    },
    {
     "code": "srcSize == 0",
     "line": 825
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "ZSTD_memcpy(dst, src, srcSize)",
     "name": "ZSTD_memcpy",
     "nargs": 3
    },
    {
     "code": "memcpy((dst), (src), (srcSize))",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "dst",
    "src",
    "srcSize"
   ],
   "osv_id": "OSV-2021-897",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ZSTD_copyRawBlock"
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