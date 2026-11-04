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
  "osv_id": "ARVO-42497985",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/lib/monkey/mk_core/mk_string.c",
    "line": 586,
    "size": null,
    "type": "char*"
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
   "size_expr_cpg": "size",
   "size_expr_cpg_callee": "mk_mem_alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 603,
    "fn": "mk_string_copy_substr",
    "code": "memcpy(buffer, string + pos_init, bytes) | string + pos_init",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mk_string_copy_substr",
    "file": "/src/fluent-bit/lib/monkey/mk_core/mk_string.c",
    "line": 603
   },
   "code": "memcpy(buffer, string + pos_init, bytes) | string + pos_init",
   "access": {
    "dir": "READ",
    "width": 30988,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mk_string_copy_substr",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "pos_init > pos_end",
   "guard_count": 1,
   "control_structures": "IF:588,IF:593,IF:598"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "string",
   "pos_init",
   "pos_end"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/8f653c34c0dd46c39e2a5ebf9ff3fe9ec932fc4f/ARVO-42497985/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_8f653c34c0dd.cpg",
   "testcase_size": 13
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
   "dedup_token": "__asan_memcpy--mk_string_copy_substr--mk_rconf_meta_add"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*buffer = 0",
     "line": 586
    },
    {
     "code": "buffer = mk_mem_alloc(size)",
     "line": 596
    },
    {
     "code": "buffer[bytes] = '\\0'",
     "line": 604
    }
   ],
   "entity_decl": {
    "line": 586,
    "type": "char*"
   },
   "entity_name_cpg": "buffer",
   "func_lines": [
    583,
    607
   ],
   "func_params": {
    "names": [
     "string",
     "pos_init",
     "pos_end"
    ],
    "types": [
     "char*",
     "int",
     "int"
    ]
   },
   "guards": [
    {
     "code": "pos_init > pos_end",
     "line": 588
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(buffer, string + pos_init, bytes)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "string + pos_init",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buffer",
    "string",
    "pos_init",
    "bytes"
   ],
   "osv_id": "ARVO-42497985",
   "sites": [
    {
     "args": "size",
     "callee": "mk_mem_alloc",
     "code": "mk_mem_alloc(size)",
     "line": 596
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
   "use_fn": "mk_string_copy_substr"
  }
 },
 {
  "osv_id": "ARVO-42497992",
  "project": "zstd",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "out",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 202,
    "type": "BYTE*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "FUZZ_malloc",
    "file": "/src/zstd/tests/fuzz/fuzz_helpers.c",
    "line": 19
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 270,
    "fn": "FSE_writeNCount_generic",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "FSE_writeNCount_generic",
    "file": "/src/zstd/lib/compress/fse_compress.c",
    "line": 270
   },
   "code": "out[0] = (BYTE)bitStream",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "FSE_writeNCount_generic",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/zstd/address/0a96d0006427e9275d0711b978495da919416ff4/ARVO-42497992/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/zstd_0a96d0006427.cpg",
   "testcase_size": 493072
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
   "dedup_token": "FSE_writeNCount_generic--FSE_writeNCount--HUF_compressWeights"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* out = ostart",
     "line": 202
    },
    {
     "code": "out[0] = (BYTE) bitStream",
     "line": 233
    },
    {
     "code": "out[1] = (BYTE)(bitStream>>8)",
     "line": 234
    },
    {
     "code": "out[0] = (BYTE)bitStream",
     "line": 248
    },
    {
     "code": "out[1] = (BYTE)(bitStream>>8)",
     "line": 249
    },
    {
     "code": "out[0] = (BYTE)bitStream",
     "line": 270
    },
    {
     "code": "out[1] = (BYTE)(bitStream>>8)",
     "line": 271
    },
    {
     "code": "out[0] = (BYTE)bitStream",
     "line": 284
    },
    {
     "code": "out[1] = (BYTE)(bitStream>>8)",
     "line": 285
    }
   ],
   "entity_decl": {
    "line": 202,
    "type": "BYTE*"
   },
   "entity_name_cpg": "out",
   "func_lines": [
    196,
    289
   ],
   "func_params": {
    "names": [
     "header",
     "headerBufferSize",
     "normalizedCounter",
     "maxSymbolValue",
     "tableLog",
     "writeIsSafe"
    ],
    "types": [
     "void*",
     "size_t",
     "short*",
     "unsigned",
     "unsigned",
     "unsigned"
    ]
   },
   "guards": [
    {
     "code": "symbol < alphabetSize",
     "line": 223
    },
    {
     "code": "remaining>1",
     "line": 223
    },
    {
     "code": "symbol < alphabetSize",
     "line": 226
    },
    {
     "code": "symbol == alphabetSize",
     "line": 227
    },
    {
     "code": "out > oend-2",
     "line": 231
    },
    {
     "code": "bitCount>16",
     "line": 245
    },
    {
     "code": "out > oend - 2",
     "line": 246
    },
    {
     "code": "count < 0",
     "line": 256
    },
    {
     "code": "count<max",
     "line": 262
    },
    {
     "code": "count==1",
     "line": 263
    },
    {
     "code": "remaining<1",
     "line": 264
    },
    {
     "code": "remaining<threshold",
     "line": 265
    },
    {
     "code": "bitCount>16",
     "line": 267
    },
    {
     "code": "out > oend - 2",
     "line": 268
    },
    {
     "code": "remaining != 1",
     "line": 277
    },
    {
     "code": "out > oend - 2",
     "line": 282
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "out[0] = (BYTE)bitStream",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "out[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "(BYTE)bitStream",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out",
    "bitStream"
   ],
   "osv_id": "ARVO-42497992",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "FSE_writeNCount_generic"
  }
 },
 {
  "osv_id": "ARVO-42498356",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/decompress/zstd_decompress.c",
    "line": 763,
    "size": null,
    "type": "void*"
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
    "line": 772,
    "fn": "ZSTD_copyRawBlock",
    "code": "ZSTD_memcpy(dst, src, srcSize) | memcpy((dst), (src), (srcSize))",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_copyRawBlock",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/decompress/zstd_decompress.c",
    "line": 772
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
   "guard_count": 3,
   "control_structures": "IF:767,IF:767,IF:768,IF:769,DO:770,IF:770"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "dst",
   "dstCapacity",
   "src",
   "srcSize"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/38b23d5ab3c67c5528faed5750611f34c3f18f3f/ARVO-42498356/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_38b23d5ab3c6.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--ZSTD_copyRawBlock--ZSTD_decompressFrame"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 763,
    "type": "void*"
   },
   "entity_name_cpg": "dst",
   "func_lines": [
    763,
    774
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
     "line": 767
    },
    {
     "code": "dst == NULL",
     "line": 768
    },
    {
     "code": "srcSize == 0",
     "line": 769
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
   "osv_id": "ARVO-42498356",
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
 },
 {
  "osv_id": "ARVO-42498506",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "uint32_t",
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
    "line": 113,
    "fn": "OT::CPALV1Tail::serialize(hb_serialize_context_t*, unsigned int, unsigned int, void const*, hb_map_t const*) const",
    "code": "{HB_TAG ('h','l','i','g'), HB_AAT_LAYOUT_FEATURE_TYPE_LI | HB_TAG ('h','l','i','g') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('l') & 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "OT::CPALV1Tail::serialize(hb_serialize_context_t*, unsigned int, unsigned int, void const*, hb_map_t const*) const",
    "file": "/src/harfbuzz/src/hb-ot-color-cpal-table.hh",
    "line": 113
   },
   "code": "{HB_TAG ('h','l','i','g'), HB_AAT_LAYOUT_FEATURE_TYPE_LI | HB_TAG ('h','l','i','g') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('l') & 0",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<global>",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:207,IF:214,IF:249,IF:258,FOR:272,IF:273"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/cb5a6b5a27cfe616113bafe7f23ad33f1b0d0a1e/ARVO-42498506/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_cb5a6b5a27cf.cpg",
   "testcase_size": 2116
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
   "dedup_token": "OT::CPALV1Tail::serialize(hb_serialize_context_t*, unsigned int, unsigned int, void const*, hb_map_t const*) const--OT::CPAL::subset(hb_subset_context_t*) const"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "uint32_t",
   "func_lines": [
    1,
    424
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [
    {
     "code": "i < count",
     "line": 272
    },
    {
     "code": "info[i].codepoint == AAT::DELETED_GLYPH",
     "line": 273
    },
    {
     "code": "info->codepoint == AAT::DELETED_GLYPH",
     "line": 280
    }
   ],
   "line_call_count": 17,
   "line_calls": [
    {
     "code": "{HB_TAG ('h','l','i','g'), HB_AAT_LAYOUT_FEATURE_TYPE_LIGATURES,               HB_AAT_LAYOUT_FEATURE_SELECTOR_HISTORICAL_LIGATURES_ON,        HB_AAT_LAYOUT_FEATURE_SELECTOR_HISTORICAL_LIGATURES_OFF}",
     "name": "<operator>.arrayInitializer",
     "nargs": 4
    },
    {
     "code": "HB_TAG ('h','l','i','g')",
     "name": "HB_TAG",
     "nargs": 4
    },
    {
     "code": "(hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.cast",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "((uint32_t)('h') & 0xFF) << 24",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('h') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('h')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "((uint32_t)('l') & 0xFF) << 16",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('l') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('l')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "((uint32_t)('i') & 0xFF) << 8",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('i') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('i')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('g') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('g')",
     "name": "<operator>()",
     "nargs": 2
    }
   ],
   "line_ids": [
    "uint32_t",
    "HB_AAT_LAYOUT_FEATURE_TYPE_LIGATURES",
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_HISTORICAL_LIGATURES_ON",
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_HISTORICAL_LIGATURES_OFF"
   ],
   "osv_id": "ARVO-42498506",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "OT::CPALV1Tail::serialize(hb_serialize_context_t*, unsigned int, unsigned int, void const*, hb_map_t const*) const"
  }
 },
 {
  "osv_id": "ARVO-42498551",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pool",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/vm.c",
    "line": 1093,
    "size": null,
    "type": "mrb_pool_value*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 68
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1141,
    "fn": "mrb_vm_exec",
    "code": "pool[b].tt | pool[b]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mrb_vm_exec",
    "file": "/src/mruby/src/vm.c",
    "line": 1141
   },
   "code": "pool[b].tt | pool[b]",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_vm_exec",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "b < MRB_ENV_LEN(e) | b < MRB_ENV_LEN(e) | b == CALL_MAXARGS",
   "guard_count": 3,
   "control_structures": "IF:1118,IF:1121,GOTO:1122,GOTO:1123,FOR:1129,SWITCH:1129,GOTO:1132,GOTO:1137,SWITCH:1141,BREAK:1144,GOTO:1156,GOTO:1159"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mrb_pool_value*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e60ddc431d242ede15e8f4d59a1a815fac532dc6/ARVO-42498551/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e60ddc431d24.cpg",
   "testcase_size": 56823
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
   "dedup_token": "mrb_vm_exec--mrb_vm_run--mrb_top_run"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*pool = irep->pool",
     "line": 1093
    },
    {
     "code": "pool = irep->pool",
     "line": 1553
    },
    {
     "code": "pool = irep->pool",
     "line": 1566
    },
    {
     "code": "pool = irep->pool",
     "line": 1598
    },
    {
     "code": "pool = irep->pool",
     "line": 1612
    },
    {
     "code": "pool = irep->pool",
     "line": 1731
    },
    {
     "code": "pool = irep->pool",
     "line": 1747
    },
    {
     "code": "pool = irep->pool",
     "line": 2063
    },
    {
     "code": "pool = irep->pool",
     "line": 2277
    },
    {
     "code": "pool = irep->pool",
     "line": 2808
    }
   ],
   "entity_decl": {
    "line": 1093,
    "type": "mrb_pool_value*"
   },
   "entity_name_cpg": "pool",
   "func_lines": [
    1089,
    2949
   ],
   "func_params": {
    "names": [
     "mrb",
     "proc",
     "pc"
    ],
    "types": [
     "mrb_state*",
     "RProc*",
     "mrb_code*"
    ]
   },
   "guards": [
    {
     "code": "mrb->exc->tt == MRB_TT_BREAK",
     "line": 1121
    },
    {
     "code": "b < MRB_ENV_LEN(e)",
     "line": 1307
    },
    {
     "code": "b < MRB_ENV_LEN(e)",
     "line": 1322
    },
    {
     "code": "a < irep->ilen",
     "line": 1363
    },
    {
     "code": "a < mrb_irep_catch_handler_unpack(ch->begin)",
     "line": 1369
    },
    {
     "code": "mrb->exc == NULL",
     "line": 1384
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1454
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1461
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1471
    },
    {
     "code": "argc < 0",
     "line": 1472
    },
    {
     "code": "bidx < irep->nregs",
     "line": 1478
    },
    {
     "code": "mid != missing",
     "line": 1499
    },
    {
     "code": "argc > 0",
     "line": 1527
    },
    {
     "code": "argc == -1",
     "line": 1527
    },
    {
     "code": "RARRAY_LEN(regs[1]) != 0",
     "line": 1527
    },
    {
     "code": "MRB_PROC_ENV(p) == mrb_vm_ci_env(&ci[-1])",
     "line": 1540
    },
    {
     "code": "ci->acc == CI_ACC_RESUMED",
     "line": 1545
    },
    {
     "code": "argc < 0",
     "line": 1568
    },
    {
     "code": "irep->nregs < 3",
     "line": 1568
    },
    {
     "code": "ci->argc < 0",
     "line": 1615
    },
    {
     "code": "irep->nregs > 3",
     "line": 1616
    },
    {
     "code": "ci->argc+2 < irep->nregs",
     "line": 1620
    },
    {
     "code": "b == CALL_MAXARGS",
     "line": 1632
    },
    {
     "code": "argc < 0",
     "line": 1633
    },
    {
     "code": "p->e.env->mid != mid",
     "line": 1642
    },
    {
     "code": "bidx < irep->nregs",
     "line": 1645
    },
    {
     "code": "mid == 0",
     "line": 1647
    },
    {
     "code": "target_class->tt == MRB_TT_MODULE",
     "line": 1655
    },
    {
     "code": "target_class->tt != MRB_TT_ICLASS",
     "line": 1657
    },
    {
     "code": "mid != missing",
     "line": 1688
    },
    {
     "code": "ci->acc == CI_ACC_RESUMED",
     "line": 1723
    },
    {
     "code": "argc < 0",
     "line": 1749
    },
    {
     "code": "irep->nregs < 3",
     "line": 1749
    },
    {
     "code": "mrb->c->ci->mid == 0",
     "line": 1763
    },
    {
     "code": "mrb_vm_ci_target_class(mrb->c->ci) == NULL",
     "line": 1763
    },
    {
     "code": "lv == 0",
     "line": 1771
    },
    {
     "code": "r == 0",
     "line": 1779
    },
    {
     "code": "m1 > 0",
     "line": 1795
    },
    {
     "code": "len > 0",
     "line": 1798
    },
    {
     "code": "m2 > 0",
     "line": 1801
    },
    {
     "code": "MRB_ASPEC_KEY(a) > 0",
     "line": 1819
    },
    {
     "code": "argc < 0",
     "line": 1828
    },
    {
     "code": "argc < 0",
     "line": 1833
    },
    {
     "code": "argc < m1 + m2",
     "line": 1842
    },
    {
     "code": "r == 0",
     "line": 1842
    },
    {
     "code": "argc > len + kd",
     "line": 1842
    },
    {
     "code": "len > 1",
     "line": 1848
    },
    {
     "code": "argc == 1",
     "line": 1848
    },
    {
     "code": "argc == m1+m2",
     "line": 1856
    },
    {
     "code": "argc > 0",
     "line": 1861
    },
    {
     "code": "MRB_ASPEC_KEY(a) > 0",
     "line": 1874
    },
    {
     "code": "argc-kargs < len",
     "line": 1881
    },
    {
     "code": "argc < m1+m2",
     "line": 1883
    },
    {
     "code": "m1 < argc",
     "line": 1884
    },
    {
     "code": "argv0 != argv",
     "line": 1890
    },
    {
     "code": "argc < m1",
     "line": 1893
    },
    {
     "code": "mlen < m2",
     "line": 1900
    },
    {
     "code": "o > 0",
     "line": 1908
    },
    {
     "code": "argc-kargs > m1+m2",
     "line": 1908
    },
    {
     "code": "argv0 != argv",
     "line": 1913
    },
    {
     "code": "argc-m2 > m1",
     "line": 1926
    },
    {
     "code": "argv0 == argv",
     "line": 1930
    },
    {
     "code": "irep->nlocals-blk_pos-1 > 0",
     "line": 1941
    },
    {
     "code": "ci->argc < 0",
     "line": 2004
    },
    {
     "code": "ci > mrb->c->cibase",
     "line": 2014
    },
    {
     "code": "MRB_PROC_ENV(p) == mrb_vm_ci_env(&ci[-1])",
     "line": 2014
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2023
    },
    {
     "code": "ch == NULL",
     "line": 2025
    },
    {
     "code": "(ch = catch_handler_find(mrb, ci, pc, MRB_CATCH_FILTER_ALL)) == NULL",
     "line": 2028
    },
    {
     "code": "ci[1].acc == CI_ACC_SKIP",
     "line": 2030
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2035
    },
    {
     "code": "ch == NULL",
     "line": 2037
    },
    {
     "code": "mrb->c == mrb->root_c",
     "line": 2039
    },
    {
     "code": "ch == NULL",
     "line": 2056
    },
    {
     "code": "e->cxt != mrb->c",
     "line": 2087
    },
    {
     "code": "ci->proc != dst",
     "line": 2093
    },
    {
     "code": "ci->acc < 0",
     "line": 2094
    },
    {
     "code": "ci->proc != dst",
     "line": 2105
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2124
    },
    {
     "code": "c->prev->ci == c->prev->cibase",
     "line": 2132
    },
    {
     "code": "e->cxt != mrb->c",
     "line": 2183
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2195
    },
    {
     "code": "ci->acc < 0",
     "line": 2202
    },
    {
     "code": "mrb->c->cibase < ci",
     "line": 2227
    },
    {
     "code": "ci[-1].proc != proc->upper",
     "line": 2227
    },
    {
     "code": "ci[-1].acc == CI_ACC_SKIP",
     "line": 2228
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2248
    },
    {
     "code": "ci == mrb->c->ci",
     "line": 2257
    },
    {
     "code": "mrb->exc == NULL",
     "line": 2258
    },
    {
     "code": "acc == CI_ACC_SKIP",
     "line": 2268
    },
    {
     "code": "acc == CI_ACC_DIRECT",
     "line": 2268
    },
    {
     "code": "lv == 0",
     "line": 2294
    },
    {
     "code": "e->mid == 0",
     "line": 2297
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) == mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) == mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) == mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) == mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) < mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) < mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) < mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) < mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) > mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) > mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) > mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) > mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "c == 0",
     "line": 2594
    },
    {
     "code": "len > pre + post",
     "line": 2625
    },
    {
     "code": "idx+pre<len",
     "line": 2635
    },
    {
     "code": "idx < post",
     "line": 2638
    },
    {
     "code": "i<lim",
     "line": 2679
    },
    {
     "code": "i<lim",
     "line": 2693
    },
    {
     "code": "c == OP_L_METHOD",
     "line": 2722
    },
    {
     "code": "(pool[a].tt&IREP_TT_NFLAG)==0",
     "line": 2877
    },
    {
     "code": "mrb->exc->tt == MRB_TT_EXCEPTION",
     "line": 2930
    },
    {
     "code": "ci > mrb->c->cibase",
     "line": 2941
    },
    {
     "code": "ci->acc == CI_ACC_DIRECT",
     "line": 2941
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "pool[b].tt",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "pool[b]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pool",
    "b"
   ],
   "osv_id": "ARVO-42498551",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_vm_exec"
  }
 },
 {
  "osv_id": "ARVO-42498567",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "newpos",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-compiler/core/codegen.c",
    "line": 563,
    "size": null,
    "type": "int16_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 68
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 573,
    "fn": "dispatch",
    "code": "newpos = (int16_t)PEEK_S(s->iseq+pos0) | (int16_t)PEEK_S(s->iseq+pos0) | PEEK_S(s->iseq+pos0) | s->iseq+pos0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dispatch",
    "file": "/src/mruby/mrbgems/mruby-compiler/core/codegen.c",
    "line": 573
   },
   "code": "newpos = (int16_t)PEEK_S(s->iseq+pos0) | (int16_t)PEEK_S(s->iseq+pos0) | PEEK_S(s->iseq+pos0) | s->iseq+pos0",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dispatch",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "pos0 == JMPLINK_START | newpos == 0",
   "guard_count": 2,
   "control_structures": "IF:565,IF:569,IF:575"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int16_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "s",
   "pos0"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e60ddc431d242ede15e8f4d59a1a815fac532dc6/ARVO-42498567/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e60ddc431d24.cpg",
   "testcase_size": 26226
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
   "dedup_token": "dispatch--dispatch_linked--codegen"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "newpos = (int16_t)PEEK_S(s->iseq+pos0)",
     "line": 573
    }
   ],
   "entity_decl": {
    "line": 563,
    "type": "int16_t"
   },
   "entity_name_cpg": "newpos",
   "func_lines": [
    558,
    577
   ],
   "func_params": {
    "names": [
     "s",
     "pos0"
    ],
    "types": [
     "codegen_scope*",
     "uint32_t"
    ]
   },
   "guards": [
    {
     "code": "pos0 == JMPLINK_START",
     "line": 565
    },
    {
     "code": "offset > INT16_MAX",
     "line": 569
    },
    {
     "code": "newpos == 0",
     "line": 575
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "newpos = (int16_t)PEEK_S(s->iseq+pos0)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(int16_t)PEEK_S(s->iseq+pos0)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "PEEK_S(s->iseq+pos0)",
     "name": "PEEK_S",
     "nargs": 1
    },
    {
     "code": "s->iseq+pos0",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "s->iseq",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "newpos",
    "s",
    "pos0"
   ],
   "osv_id": "ARVO-42498567",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dispatch"
  }
 },
 {
  "osv_id": "ARVO-42498787",
  "project": "wireshark",
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
    "fn": "g_malloc (/out/fuzzshark_media_type-json+0x2c1d718)",
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
    "line": 358,
    "fn": "json_string_unescape",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "json_string_unescape",
    "file": "/src/wireshark/epan/dissectors/packet-json.c",
    "line": 358
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_string_unescape",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wireshark/address/6dfa2cb0ae4f15d171da8cf77f2a6e11d35d0d86/ARVO-42498787/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_6dfa2cb0ae4f.cpg",
   "testcase_size": 3
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
   "dedup_token": "json_string_unescape--after_value--execute_callbacks"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "json_string_unescape"
  }
 },
 {
  "osv_id": "ARVO-42499353",
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
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 156,
    "fn": "vips_foreign_load_jxl_build",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vips_foreign_load_jxl_build",
    "file": "/src/libvips/libvips/foreign/jxlload.c",
    "line": 156
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vips_foreign_load_jxl_build",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42499353/report.log",
   "cpg": null,
   "testcase_size": 2661
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
   "dedup_token": "Load<int>--jxl::N_AVX3::RgbFromSingle(unsigned long, int const*, float, jxl::Image3<float>*, unsigned long, unsigned long, jxl::Rect&)--jxl::ThreadPool::Sequent"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vips_foreign_load_jxl_build"
  }
 },
 {
  "osv_id": "ARVO-42499386",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "OP_LOADL",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 68
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1140,
    "fn": "mrb_vm_exec",
    "code": "CASE(OP_LOADL, BB) | pc++ | FETCH_BB() | mrb->c->ci->pc = pc",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mrb_vm_exec",
    "file": "/src/mruby/src/vm.c",
    "line": 1140
   },
   "code": "CASE(OP_LOADL, BB) | pc++ | FETCH_BB() | mrb->c->ci->pc = pc",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_vm_exec",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1118,IF:1121,GOTO:1122,GOTO:1123,FOR:1129,SWITCH:1129,GOTO:1132,GOTO:1137,SWITCH:1141,BREAK:1144,GOTO:1156,GOTO:1159"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/598c97ef76771f3b741657ee6807c58b0ca4f393/ARVO-42499386/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_598c97ef7677.cpg",
   "testcase_size": 9
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "mrb_vm_exec--mrb_vm_run--mrb_top_run"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "OP_LOADL",
   "func_lines": [
    1089,
    2950
   ],
   "func_params": {
    "names": [
     "mrb",
     "proc",
     "pc"
    ],
    "types": [
     "mrb_state*",
     "RProc*",
     "mrb_code*"
    ]
   },
   "guards": [
    {
     "code": "mrb->exc->tt == MRB_TT_BREAK",
     "line": 1121
    },
    {
     "code": "b < MRB_ENV_LEN(e)",
     "line": 1307
    },
    {
     "code": "b < MRB_ENV_LEN(e)",
     "line": 1322
    },
    {
     "code": "a < irep->ilen",
     "line": 1363
    },
    {
     "code": "a < mrb_irep_catch_handler_unpack(ch->begin)",
     "line": 1369
    },
    {
     "code": "mrb->exc == NULL",
     "line": 1384
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1454
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1461
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1471
    },
    {
     "code": "argc < 0",
     "line": 1472
    },
    {
     "code": "bidx < irep->nregs",
     "line": 1478
    },
    {
     "code": "mid != missing",
     "line": 1499
    },
    {
     "code": "argc > 0",
     "line": 1527
    },
    {
     "code": "argc == -1",
     "line": 1527
    },
    {
     "code": "RARRAY_LEN(regs[1]) != 0",
     "line": 1527
    },
    {
     "code": "MRB_PROC_ENV(p) == mrb_vm_ci_env(&ci[-1])",
     "line": 1540
    },
    {
     "code": "ci->acc == CI_ACC_RESUMED",
     "line": 1545
    },
    {
     "code": "argc < 0",
     "line": 1568
    },
    {
     "code": "irep->nregs < 3",
     "line": 1568
    },
    {
     "code": "ci->argc < 0",
     "line": 1615
    },
    {
     "code": "irep->nregs > 3",
     "line": 1616
    },
    {
     "code": "ci->argc+2 < irep->nregs",
     "line": 1620
    },
    {
     "code": "b == CALL_MAXARGS",
     "line": 1632
    },
    {
     "code": "argc < 0",
     "line": 1633
    },
    {
     "code": "p->e.env->mid != mid",
     "line": 1642
    },
    {
     "code": "bidx < irep->nregs",
     "line": 1645
    },
    {
     "code": "mid == 0",
     "line": 1647
    },
    {
     "code": "target_class->tt == MRB_TT_MODULE",
     "line": 1655
    },
    {
     "code": "target_class->tt != MRB_TT_ICLASS",
     "line": 1657
    },
    {
     "code": "mid != missing",
     "line": 1688
    },
    {
     "code": "ci->acc == CI_ACC_RESUMED",
     "line": 1723
    },
    {
     "code": "argc < 0",
     "line": 1749
    },
    {
     "code": "irep->nregs < 3",
     "line": 1749
    },
    {
     "code": "mrb->c->ci->mid == 0",
     "line": 1763
    },
    {
     "code": "mrb_vm_ci_target_class(mrb->c->ci) == NULL",
     "line": 1763
    },
    {
     "code": "lv == 0",
     "line": 1771
    },
    {
     "code": "r == 0",
     "line": 1779
    },
    {
     "code": "m1 > 0",
     "line": 1795
    },
    {
     "code": "len > 0",
     "line": 1798
    },
    {
     "code": "m2 > 0",
     "line": 1801
    },
    {
     "code": "MRB_ASPEC_KEY(a) > 0",
     "line": 1819
    },
    {
     "code": "argc < 0",
     "line": 1828
    },
    {
     "code": "argc < 0",
     "line": 1833
    },
    {
     "code": "argc < m1 + m2",
     "line": 1842
    },
    {
     "code": "r == 0",
     "line": 1842
    },
    {
     "code": "argc > len + kd",
     "line": 1842
    },
    {
     "code": "len > 1",
     "line": 1848
    },
    {
     "code": "argc == 1",
     "line": 1848
    },
    {
     "code": "argc == m1+m2",
     "line": 1856
    },
    {
     "code": "argc > 0",
     "line": 1861
    },
    {
     "code": "MRB_ASPEC_KEY(a) > 0",
     "line": 1874
    },
    {
     "code": "argc-kargs < len",
     "line": 1881
    },
    {
     "code": "argc < m1+m2",
     "line": 1883
    },
    {
     "code": "m1 < argc",
     "line": 1884
    },
    {
     "code": "argv0 != argv",
     "line": 1890
    },
    {
     "code": "argc < m1",
     "line": 1893
    },
    {
     "code": "mlen < m2",
     "line": 1900
    },
    {
     "code": "o > 0",
     "line": 1908
    },
    {
     "code": "argc-kargs > m1+m2",
     "line": 1908
    },
    {
     "code": "argv0 != argv",
     "line": 1913
    },
    {
     "code": "argc-m2 > m1",
     "line": 1926
    },
    {
     "code": "argv0 == argv",
     "line": 1930
    },
    {
     "code": "irep->nlocals-blk_pos-1 > 0",
     "line": 1941
    },
    {
     "code": "ci->argc < 0",
     "line": 2004
    },
    {
     "code": "ci > mrb->c->cibase",
     "line": 2014
    },
    {
     "code": "MRB_PROC_ENV(p) == mrb_vm_ci_env(&ci[-1])",
     "line": 2014
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2023
    },
    {
     "code": "ch == NULL",
     "line": 2025
    },
    {
     "code": "(ch = catch_handler_find(mrb, ci, pc, MRB_CATCH_FILTER_ALL)) == NULL",
     "line": 2028
    },
    {
     "code": "ci[1].acc == CI_ACC_SKIP",
     "line": 2030
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2035
    },
    {
     "code": "ch == NULL",
     "line": 2037
    },
    {
     "code": "mrb->c == mrb->root_c",
     "line": 2039
    },
    {
     "code": "ch == NULL",
     "line": 2056
    },
    {
     "code": "e->cxt != mrb->c",
     "line": 2087
    },
    {
     "code": "ci->proc != dst",
     "line": 2093
    },
    {
     "code": "ci->acc < 0",
     "line": 2094
    },
    {
     "code": "ci->proc != dst",
     "line": 2105
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2124
    },
    {
     "code": "c->prev->ci == c->prev->cibase",
     "line": 2132
    },
    {
     "code": "e->cxt != mrb->c",
     "line": 2183
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2195
    },
    {
     "code": "ci->acc < 0",
     "line": 2202
    },
    {
     "code": "mrb->c->cibase < ci",
     "line": 2227
    },
    {
     "code": "ci[-1].proc != proc->upper",
     "line": 2227
    },
    {
     "code": "ci[-1].acc == CI_ACC_SKIP",
     "line": 2228
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2248
    },
    {
     "code": "ci == mrb->c->ci",
     "line": 2257
    },
    {
     "code": "mrb->exc == NULL",
     "line": 2258
    },
    {
     "code": "acc == CI_ACC_SKIP",
     "line": 2268
    },
    {
     "code": "acc == CI_ACC_DIRECT",
     "line": 2268
    },
    {
     "code": "lv == 0",
     "line": 2294
    },
    {
     "code": "e->mid == 0",
     "line": 2297
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) == mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) == mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) == mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) == mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) < mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) < mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) < mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) < mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) > mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) > mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) > mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) > mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "c == 0",
     "line": 2594
    },
    {
     "code": "len > pre + post",
     "line": 2625
    },
    {
     "code": "idx+pre<len",
     "line": 2635
    },
    {
     "code": "idx < post",
     "line": 2638
    },
    {
     "code": "i<lim",
     "line": 2679
    },
    {
     "code": "i<lim",
     "line": 2693
    },
    {
     "code": "c == OP_L_METHOD",
     "line": 2722
    },
    {
     "code": "(pool[a].tt&IREP_TT_NFLAG)==0",
     "line": 2878
    },
    {
     "code": "mrb->exc->tt == MRB_TT_EXCEPTION",
     "line": 2931
    },
    {
     "code": "ci > mrb->c->cibase",
     "line": 2942
    },
    {
     "code": "ci->acc == CI_ACC_DIRECT",
     "line": 2942
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "CASE(OP_LOADL, BB)",
     "name": "CASE",
     "nargs": 0
    },
    {
     "code": "pc++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "FETCH_BB()",
     "name": "FETCH_BB",
     "nargs": 0
    },
    {
     "code": "mrb->c->ci->pc = pc",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "mrb->c->ci->pc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "mrb->c->ci",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "mrb->c",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "OP_LOADL",
    "pc",
    "mrb"
   ],
   "osv_id": "ARVO-42499386",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_vm_exec"
  }
 },
 {
  "osv_id": "ARVO-42499415",
  "project": "libjxl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "wy",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libjxl/third_party/highway/hwy/base.h",
    "line": 638,
    "size": null,
    "type": "float"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "jxl::CacheAligned::Allocate(unsigned long, unsigned long)",
    "file": "/src/libjxl/lib/jxl/base/cache_aligned.cc",
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 638,
    "fn": "CopyBytes<4, float, float>",
    "code": "wy = weights.vert[std::abs(dy) * 4] | weights.vert[std::abs(dy) * 4] | weights.vert | std::abs(dy) * 4",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "CopyBytes<4, float, float>",
    "file": "/src/libjxl/third_party/highway/hwy/base.h",
    "line": 638
   },
   "code": "wy = weights.vert[std::abs(dy) * 4] | weights.vert[std::abs(dy) * 4] | weights.vert | std::abs(dy) * 4",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ConvolveRow",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "dy <= kRadius",
   "guard_count": 1,
   "control_structures": "FOR:563,FOR:583,WHILE:603,IF:634,FOR:635,FOR:637,FOR:640"
  },
  "call_chain": [],
  "types": {
   "entity_type": "float",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "row_m",
   "xsize",
   "stride",
   "weights",
   "row_out"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/08973db8ae2e4f19bf57afa85089e705c50a572b/ARVO-42499415/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_08973db8ae2e.cpg",
   "testcase_size": 102
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
   "dedup_token": "CopyBytes<4, float, float>--Store<float>--jxl::N_SCALAR::SingleFromSingle(unsigned long, int const*, float, jxl::Image3<float>*, unsigned long, unsigned long, j"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "wy = weights.vert[std::abs(dy) * 4]",
     "line": 638
    }
   ],
   "entity_decl": {
    "line": 638,
    "type": "float"
   },
   "entity_name_cpg": "wy",
   "func_lines": [
    531,
    649
   ],
   "func_params": {
    "names": [
     "this",
     "row_m",
     "xsize",
     "stride",
     "wrap_row",
     "weights",
     "row_out"
    ],
    "types": [
     "jxl.HWY_NAMESPACE.strategy.Separable7",
     "float*const",
     "size_t",
     "int64_t",
     "WrapRow&",
     "WeightsSeparable7&",
     "float*const"
    ]
   },
   "guards": [
    {
     "code": "x < kRadius",
     "line": 563
    },
    {
     "code": "x < xsize",
     "line": 603
    },
    {
     "code": "kSizeModN != 0",
     "line": 634
    },
    {
     "code": "x < xsize",
     "line": 635
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "wy = weights.vert[std::abs(dy) * 4]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "weights.vert[std::abs(dy) * 4]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "weights.vert",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "std::abs(dy) * 4",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "std::abs(dy)",
     "name": "abs",
     "nargs": 1
    }
   ],
   "line_ids": [
    "wy",
    "weights",
    "dy"
   ],
   "osv_id": "ARVO-42499415",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "CopyBytes<4, float, float>"
  }
 },
 {
  "osv_id": "ARVO-42499474",
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
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 156,
    "fn": "vips_foreign_load_jxl_build",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vips_foreign_load_jxl_build",
    "file": "/src/libvips/libvips/foreign/jxlload.c",
    "line": 156
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vips_foreign_load_jxl_build",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42499474/report.log",
   "cpg": null,
   "testcase_size": 2036
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
   "dedup_token": "Load<int>--jxl::N_AVX3::SingleFromSingle(unsigned long, int const*, float, jxl::Image3<float>*, unsigned long, unsigned long, jxl::Rect&)--jxl::ThreadPool::Sequ"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vips_foreign_load_jxl_build"
  }
 },
 {
  "osv_id": "ARVO-42499668",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "entry",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_hash.c",
    "line": 393,
    "size": null,
    "type": "flb_hash_entry*"
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
    "line": 412,
    "fn": "flb_hash_get_by_id",
    "code": "strcmp(entry->key, key) == 0 | strcmp(entry->key, key) | entry->key",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_hash_get_by_id",
    "file": "/src/fluent-bit/src/flb_hash.c",
    "line": 412
   },
   "code": "strcmp(entry->key, key) == 0 | strcmp(entry->key, key) | entry->key",
   "access": {
    "dir": "READ",
    "width": 593,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_hash_get_by_id",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:396,IF:401,IF:405,ELSE:409,IF:412,BREAK:413,IF:419"
  },
  "call_chain": [],
  "types": {
   "entity_type": "flb_hash_entry*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "key"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9da96a3b88859ae57134c6932cab65101114e3b4/ARVO-42499668/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9da96a3b8885.cpg",
   "testcase_size": 601
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
   "dedup_token": "strcmp--flb_hash_get_by_id--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*entry = NULL",
     "line": 393
    },
    {
     "code": "entry = NULL",
     "line": 415
    }
   ],
   "entity_decl": {
    "line": 393,
    "type": "flb_hash_entry*"
   },
   "entity_name_cpg": "entry",
   "func_lines": [
    388,
    427
   ],
   "func_params": {
    "names": [
     "ht",
     "id",
     "key",
     "out_buf",
     "out_size"
    ],
    "types": [
     "flb_hash*",
     "int",
     "char*",
     "char**",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "table->count == 0",
     "line": 401
    },
    {
     "code": "table->count == 1",
     "line": 405
    },
    {
     "code": "strcmp(entry->key, key) == 0",
     "line": 412
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "strcmp(entry->key, key) == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "strcmp(entry->key, key)",
     "name": "strcmp",
     "nargs": 2
    },
    {
     "code": "entry->key",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "entry",
    "key"
   ],
   "osv_id": "ARVO-42499668",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_hash_get_by_id"
  }
 },
 {
  "osv_id": "ARVO-42499879",
  "project": "net-snmp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "line",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 746,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "read_config",
    "file": "/src/net-snmp/snmplib/read_config.c",
    "line": 803
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "line ;; linesize + 256",
   "size_expr_cpg_callee": "realloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 823,
    "fn": "read_config",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_config",
    "file": "/src/net-snmp/snmplib/read_config.c",
    "line": 823
   },
   "code": "line[linelen - 1] == '\\n'",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "read_config",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/7b39d280f81af4513382c3cf4ba09458ab57e6c6/ARVO-42499879/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_7b39d280f81a.cpg",
   "testcase_size": 1
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
   "dedup_token": "read_config--LLVMFuzzerTestOneInput--ExecuteFilesOnyByOne"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*line = NULL",
     "line": 746
    },
    {
     "code": "line = tmp",
     "line": 805
    },
    {
     "code": "line[linelen] = '\\0'",
     "line": 815
    },
    {
     "code": "line[linelen - 1] = '\\0'",
     "line": 824
    }
   ],
   "entity_decl": {
    "line": 746,
    "type": "char*"
   },
   "entity_name_cpg": "line",
   "func_lines": [
    735,
    970
   ],
   "func_params": {
    "names": [
     "filename",
     "line_handler",
     "when"
    ],
    "types": [
     "char*",
     "config_line*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "depth == 0",
     "line": 750
    },
    {
     "code": "(ifile = fopen(filename, \"r\")) == NULL",
     "line": 753
    },
    {
     "code": "files > CONFIG_MAX_FILES",
     "line": 773
    },
    {
     "code": "depth > CONFIG_MAX_RECURSE_DEPTH",
     "line": 780
    },
    {
     "code": "fgets(line + linelen, linesize - linelen, ifile) == NULL",
     "line": 814
    },
    {
     "code": "line[linelen - 1] == '\\n'",
     "line": 823
    },
    {
     "code": "token[0] == '['",
     "line": 839
    },
    {
     "code": "token[strlen(token) - 1] != ']'",
     "line": 840
    },
    {
     "code": "lptr == NULL",
     "line": 847
    },
    {
     "code": "cptr == NULL",
     "line": 856
    },
    {
     "code": "token[0] == 'i'",
     "line": 868
    },
    {
     "code": "strncasecmp(token,\"include\", 7 )==0",
     "line": 868
    },
    {
     "code": "strcasecmp( token, \"include\" )==0",
     "line": 869
    },
    {
     "code": "when != PREMIB_CONFIG",
     "line": 870
    },
    {
     "code": "strcasecmp( token, \"includedir\" )==0",
     "line": 876
    },
    {
     "code": "cptr == NULL",
     "line": 882
    },
    {
     "code": "when != PREMIB_CONFIG",
     "line": 883
    },
    {
     "code": "(d=opendir(cptr)) == NULL",
     "line": 887
    },
    {
     "code": "when != PREMIB_CONFIG",
     "line": 888
    },
    {
     "code": "(entry = readdir( d )) != NULL",
     "line": 892
    },
    {
     "code": "entry->d_name[0] != '.'",
     "line": 893
    },
    {
     "code": "len > 5",
     "line": 895
    },
    {
     "code": "strcmp(&(entry->d_name[len-5]),\".conf\") == 0",
     "line": 895
    },
    {
     "code": "strcasecmp( token, \"includefile\" )==0",
     "line": 904
    },
    {
     "code": "cptr == NULL",
     "line": 907
    },
    {
     "code": "when != PREMIB_CONFIG",
     "line": 908
    },
    {
     "code": "cptr[0] == '/'",
     "line": 912
    },
    {
     "code": "read_config(fname, line_handler, when) !=",
     "line": 923
    },
    {
     "code": "when != PREMIB_CONFIG",
     "line": 924
    },
    {
     "code": "strcasecmp( token, \"includesearch\" )==0",
     "line": 928
    },
    {
     "code": "cptr == NULL",
     "line": 932
    },
    {
     "code": "when != PREMIB_CONFIG",
     "line": 933
    },
    {
     "code": "len > 5",
     "line": 941
    },
    {
     "code": "strcmp(&cptr[len-5],\".conf\") == 0",
     "line": 941
    },
    {
     "code": "len > 5",
     "line": 944
    },
    {
     "code": "cptr[len-5] == 0",
     "line": 944
    },
    {
     "code": "ret != SNMPERR_SUCCESS",
     "line": 946
    },
    {
     "code": "when != PREMIB_CONFIG",
     "line": 946
    },
    {
     "code": "cptr == NULL",
     "line": 955
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "line[linelen - 1] == '\\n'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "line[linelen - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "linelen - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "line",
    "linelen"
   ],
   "osv_id": "ARVO-42499879",
   "sites": [
    {
     "args": "line ;; linesize + 256",
     "callee": "realloc",
     "code": "realloc(line, linesize + 256)",
     "line": 803
    },
    {
     "args": "line",
     "callee": "free",
     "code": "free(line)",
     "line": 809
    },
    {
     "args": "STRINGMAX",
     "callee": "<operator>.alloc",
     "code": "token[STRINGMAX]",
     "line": 836
    },
    {
     "args": "SNMP_MAXPATH",
     "callee": "<operator>.alloc",
     "code": "fname[SNMP_MAXPATH]",
     "line": 879
    },
    {
     "args": "SNMP_MAXPATH",
     "callee": "<operator>.alloc",
     "code": "fname[SNMP_MAXPATH]",
     "line": 905
    },
    {
     "args": "line",
     "callee": "free",
     "code": "free(line)",
     "line": 964
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "read_config"
  }
 },
 {
  "osv_id": "ARVO-42500334",
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
    "fn": "H5MM_malloc",
    "file": "/src/hdf5-1.12.1/src/H5MM.c",
    "line": 313
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
    "line": 590,
    "fn": "Mat_Open",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_Open",
    "file": "/src/matio/src/mat.c",
    "line": 590
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_Open",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/2945c0ded5ede79eae3cba3a5d12450ba2917fbc/ARVO-42500334/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_2945c0ded5ed.cpg",
   "testcase_size": 18198
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
   "dedup_token": "H5O__cont_decode--H5O__chunk_deserialize--H5O__cache_deserialize"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    442,
    630
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
     "line": 450
    },
    {
     "code": "(mode & 0x01) == MAT_ACC_RDWR",
     "line": 462
    },
    {
     "code": "NULL == mat",
     "line": 482
    },
    {
     "code": "NULL == mat->header",
     "line": 490
    },
    {
     "code": "NULL == mat->subsys_offset",
     "line": 497
    },
    {
     "code": "128 == bytesread",
     "line": 519
    },
    {
     "code": "tmp == 0x4d49",
     "line": 522
    },
    {
     "code": "tmp == 0x494d",
     "line": 524
    },
    {
     "code": "mat->version == 0x0100",
     "line": 530
    },
    {
     "code": "mat->version == 0x0200",
     "line": 530
    },
    {
     "code": "-1 != mat->byteswap",
     "line": 530
    },
    {
     "code": "mat->bof == -1L",
     "line": 532
    },
    {
     "code": "0 == mat->version",
     "line": 546
    },
    {
     "code": "NULL == var",
     "line": 567
    },
    {
     "code": "bytesread != 0",
     "line": 567
    },
    {
     "code": "NULL == mat",
     "line": 578
    },
    {
     "code": "mat->version == 0x0200",
     "line": 584
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42500334",
   "sites": [
    {
     "args": "sizeof(*mat)",
     "callee": "malloc",
     "code": "malloc(sizeof(*mat))",
     "line": 481
    },
    {
     "args": "128 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(128, sizeof(char))",
     "line": 489
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 491
    },
    {
     "args": "8 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(8, sizeof(char))",
     "line": 496
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 498
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 499
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 533
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 534
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 535
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 550
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 551
    },
    {
     "args": "var",
     "callee": "Mat_VarFree",
     "code": "Mat_VarFree(var)",
     "line": 573
    },
    {
     "args": "matname",
     "callee": "strdup",
     "code": "strdup(matname)",
     "line": 581
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_Open"
  }
 },
 {
  "osv_id": "ARVO-42500367",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-array.hh",
    "line": 184,
    "size": null,
    "type": "hb_buffer_t*"
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
    "line": 271,
    "fn": "hb_array_t<OT::IntType<unsigned int, 4u> const> hb_array_t<OT::IntType<unsigned int, 4u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "code": "unlikely (!buffer->ensure_glyphs ()) | !buffer->ensure_glyphs() | buffer->ensure_glyphs() | buffer->ensure_glyphs",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hb_array_t<OT::IntType<unsigned int, 4u> const> hb_array_t<OT::IntType<unsigned int, 4u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "file": "/src/harfbuzz/src/hb-array.hh",
    "line": 271
   },
   "code": "unlikely (!buffer->ensure_glyphs ()) | !buffer->ensure_glyphs() | buffer->ensure_glyphs() | buffer->ensure_glyphs",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_hb_buffer_deserialize_text",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:195,IF:215,GOTO:216,IF:217,IF:218,ELSE:222,IF:226,IF:228,ELSE:231,ELSE:233,IF:240,SWITCH:242"
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_buffer_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buffer"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/b235511ed88e46d97d27a9176da1931f4a701b0d/ARVO-42500367/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_b235511ed88e.cpg",
   "testcase_size": 567
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
   "dedup_token": "hb_array_t<OT::IntType<unsigned int, 4u> const> hb_array_t<OT::IntType<unsigned int, 4u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const--OT"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 430
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 452
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 474
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 496
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 518
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 540
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 634
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 679
    },
    {
     "code": "buffer->pos[buffer->len - 1] = pos",
     "line": 730
    }
   ],
   "entity_decl": {
    "line": 184,
    "type": "hb_buffer_t*"
   },
   "entity_name_cpg": "buffer",
   "func_lines": [
    183,
    762
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
     "line": 195
    },
    {
     "code": "p == pe",
     "line": 215
    },
    {
     "code": "p != eof",
     "line": 215
    },
    {
     "code": "p == eof",
     "line": 217
    },
    {
     "code": "_deserialize_text_eof_trans[cs] > 0",
     "line": 218
    },
    {
     "code": "_deserialize_text_cond_actions[_trans] != 0",
     "line": 240
    },
    {
     "code": "p == eof",
     "line": 743
    },
    {
     "code": "cs != 0",
     "line": 748
    },
    {
     "code": "p == pe",
     "line": 761
    },
    {
     "code": "*(p-1) != ']'",
     "line": 761
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "unlikely (!buffer->ensure_glyphs ())",
     "name": "unlikely",
     "nargs": 1
    },
    {
     "code": "!buffer->ensure_glyphs()",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "buffer->ensure_glyphs()",
     "name": "<operator>.pointerCall",
     "nargs": 0
    },
    {
     "code": "buffer->ensure_glyphs",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "!buffer->ensure_glyphs()",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "buffer->ensure_glyphs()",
     "name": "<operator>.pointerCall",
     "nargs": 0
    },
    {
     "code": "buffer->ensure_glyphs",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buffer",
    "false"
   ],
   "osv_id": "ARVO-42500367",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "hb_array_t<OT::IntType<unsigned int, 4u> const> hb_array_t<OT::IntType<unsigned int, 4u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const"
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