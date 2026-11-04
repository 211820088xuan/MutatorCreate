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
  "osv_id": "ARVO-42511465",
  "project": "opencv",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "aligned_alloc",
   "site": {
    "fn": "opj_aligned_alloc_n",
    "file": "/src/opencv/3rdparty/openjpeg/openjp2/opj_malloc.c",
    "line": 61
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1112,
    "fn": "opj_jp2_apply_pclr",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "opj_jp2_apply_pclr",
    "file": "/src/opencv/3rdparty/openjpeg/openjp2/jp2.c",
    "line": 1112
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "opj_jp2_apply_pclr",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opencv/address/f445b826d084188077a5e9d204c4c33d1589f380/ARVO-42511465/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opencv_f445b826d084.cpg",
   "testcase_size": 1218
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
   "dedup_token": "opj_jp2_apply_pclr--opj_jp2_decode--cv::Jpeg2KOpjDecoder::readData(cv::Mat&)"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "opj_jp2_apply_pclr"
  }
 },
 {
  "osv_id": "ARVO-42511520",
  "project": "assimp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/assimp/include/assimp/ParsingUtils.h",
    "line": 147,
    "size": null,
    "type": "unsigned int"
   }
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
    "line": 144,
    "fn": "SkipSpacesAndLineEnd<char>",
    "code": "i = 0 | i < node->mNumMeshes | node->mNumMeshes | ++i",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "SkipSpacesAndLineEnd<char>",
    "file": "/src/assimp/include/assimp/ParsingUtils.h",
    "line": 144
   },
   "code": "i = 0 | i < node->mNumMeshes | node->mNumMeshes | ++i",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "CollectMeshes",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < node->mNumMeshes | i < node->mNumChildren",
   "guard_count": 2,
   "control_structures": "FOR:144,FOR:147"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "node"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/71a87b653cd4b5671104fe49e2e38cf5dd4d8675/ARVO-42511520/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_71a87b653cd4.cpg",
   "testcase_size": 256
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
   "dedup_token": "SkipSpacesAndLineEnd<char>--SkipSpacesAndLineEnd<char>--Assimp::ASE::Parser::ParseLV1SoftSkinBlock()"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "i = 0",
     "line": 144
    },
    {
     "code": "i = 0",
     "line": 147
    }
   ],
   "entity_decl": {
    "line": 144,
    "type": "unsigned int"
   },
   "entity_name_cpg": "i",
   "func_lines": [
    143,
    150
   ],
   "func_params": {
    "names": [
     "node",
     "meshes"
    ],
    "types": [
     "aiNode*",
     "std.multimap<aiNode*",
     "unsignedint>&"
    ]
   },
   "guards": [
    {
     "code": "i < node->mNumMeshes",
     "line": 144
    },
    {
     "code": "i < node->mNumChildren",
     "line": 147
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "i = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "i < node->mNumMeshes",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "node->mNumMeshes",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "++i",
     "name": "<operator>.preIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "i",
    "node"
   ],
   "osv_id": "ARVO-42511520",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "SkipSpacesAndLineEnd<char>"
  }
 },
 {
  "osv_id": "ARVO-42511621",
  "project": "openexr",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "tmp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 248,
    "type": "uint32_t",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "internal_decode_alloc_buffer",
    "file": "/src/openexr/src/lib/OpenEXRCore/coding.c",
    "line": 276
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 249,
    "fn": "unaligned_load32",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "unaligned_load32",
    "file": "/src/openexr/src/lib/OpenEXRCore/internal_xdr.h",
    "line": 249
   },
   "code": "memcpy (&tmp, src, 4)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "unaligned_load32",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openexr/address/672c77d7c923402f549371e08b39ece4552cbb85/ARVO-42511621/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openexr_672c77d7c923.cpg",
   "testcase_size": 130
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "unaligned_load32--generic_unpack--exr_decoding_run"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 248,
    "type": "uint32_t"
   },
   "entity_name_cpg": "tmp",
   "func_lines": [
    245,
    251
   ],
   "func_params": {
    "names": [
     "src"
    ],
    "types": [
     "void*"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy (&tmp, src, 4)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&tmp",
     "name": "<operator>.addressOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "tmp",
    "src"
   ],
   "osv_id": "ARVO-42511621",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "unaligned_load32"
  }
 },
 {
  "osv_id": "ARVO-42511644",
  "project": "openexr",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "out",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 484,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "internal_decode_alloc_buffer",
    "file": "/src/openexr/src/lib/OpenEXRCore/coding.c",
    "line": 276
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "16",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 599,
    "fn": "uncompress_b44_impl",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "uncompress_b44_impl",
    "file": "/src/openexr/src/lib/OpenEXRCore/internal_b44.c",
    "line": 599
   },
   "code": "memcpy (out, tmp, bpl)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "uncompress_b44_impl",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openexr/address/672c77d7c923402f549371e08b39ece4552cbb85/ARVO-42511644/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openexr_672c77d7c923.cpg",
   "testcase_size": 201
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--uncompress_b44_impl--default_decompress_chunk"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*       out     = uncompressed_data",
     "line": 484
    }
   ],
   "entity_decl": {
    "line": 484,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "out",
   "func_lines": [
    475,
    608
   ],
   "func_params": {
    "names": [
     "decode",
     "compressed_data",
     "comp_buf_size",
     "uncompressed_data",
     "uncomp_buf_size"
    ],
    "types": [
     "exr_decode_pipeline_t*",
     "void*",
     "uint64_t",
     "void*",
     "uint64_t"
    ]
   },
   "guards": [
    {
     "code": "c < decode->channel_count",
     "line": 492
    },
    {
     "code": "nBytes == 0",
     "line": 500
    },
    {
     "code": "curc->data_type != EXR_PIXEL_HALF",
     "line": 502
    },
    {
     "code": "bIn + nBytes > comp_buf_size",
     "line": 504
    },
    {
     "code": "y < ny",
     "line": 512
    },
    {
     "code": "x < nx",
     "line": 519
    },
    {
     "code": "bIn + 3 > comp_buf_size",
     "line": 521
    },
    {
     "code": "bIn + 14 > comp_buf_size",
     "line": 532
    },
    {
     "code": "x + 3 < nx",
     "line": 542
    },
    {
     "code": "y + 3 < ny",
     "line": 544
    },
    {
     "code": "y + 1 < ny",
     "line": 554
    },
    {
     "code": "y + 2 < ny",
     "line": 555
    },
    {
     "code": "y < decode->chunk.height",
     "line": 568
    },
    {
     "code": "c < decode->channel_count",
     "line": 573
    },
    {
     "code": "nBytes == 0",
     "line": 582
    },
    {
     "code": "curc->y_samples > 1",
     "line": 585
    },
    {
     "code": "(cury % curc->y_samples) != 0",
     "line": 587
    },
    {
     "code": "bIn + bpl > uncomp_buf_size",
     "line": 597
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy (out, tmp, bpl)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "out",
    "tmp",
    "bpl"
   ],
   "osv_id": "ARVO-42511644",
   "sites": [
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "s[16]",
     "line": 490
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "uncompress_b44_impl"
  }
 },
 {
  "osv_id": "ARVO-42511664",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/sec.c",
    "line": 273,
    "size": null,
    "type": "u8*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "extract_word",
    "file": "/src/opensc/src/tests/fuzzing/fuzzer_tool.c",
    "line": 48
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 298,
    "fn": "sc_build_pin",
    "code": "memcpy(buf, pin->data, pin_len) | pin->data",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_build_pin",
    "file": "/src/opensc/src/libopensc/sec.c",
    "line": 298
   },
   "code": "memcpy(buf, pin->data, pin_len) | pin->data",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_build_pin",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "pin_len > pin->max_length | pin_len > 0 | pin_len > 12",
   "guard_count": 7,
   "control_structures": "IF:277,IF:280,WHILE:281,IF:283,FOR:285,IF:286,IF:295,IF:296,ELSE:300,IF:300,IF:301,FOR:303"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf",
   "buflen",
   "pin"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/c4371fac9e5b5a5505d9f9f2ca6f8cc7a5d61a24/ARVO-42511664/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_c4371fac9e5b.cpg",
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--sc_build_pin--iso7816_build_pin_apdu"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf[0] = 0x20 ",
     "line": 289
    }
   ],
   "entity_decl": {
    "line": 273,
    "type": "u8*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    273,
    339
   ],
   "func_params": {
    "names": [
     "buf",
     "buflen",
     "pin",
     "pad"
    ],
    "types": [
     "u8*",
     "size_t",
     "sc_pin_cmd_pin*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "pin_len > pin->max_length",
     "line": 277
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_GLP",
     "line": 280
    },
    {
     "code": "pin_len > 0",
     "line": 281
    },
    {
     "code": "pin->data[pin_len - 1] == 0xFF",
     "line": 281
    },
    {
     "code": "pin_len > 12",
     "line": 283
    },
    {
     "code": "i < pin_len",
     "line": 285
    },
    {
     "code": "pin->data[i] < '0'",
     "line": 286
    },
    {
     "code": "pin->data[i] > '9'",
     "line": 286
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_ASCII",
     "line": 295
    },
    {
     "code": "pin_len > buflen",
     "line": 296
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_BCD",
     "line": 300
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_GLP",
     "line": 300
    },
    {
     "code": "pin_len > 2 * buflen",
     "line": 301
    },
    {
     "code": "j < pin_len",
     "line": 303
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_GLP",
     "line": 320
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_GLP",
     "line": 322
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_BCD",
     "line": 324
    },
    {
     "code": "pin->encoding == SC_PIN_ENCODING_GLP",
     "line": 326
    },
    {
     "code": "pad_length > buflen",
     "line": 329
    },
    {
     "code": "i < pad_length",
     "line": 332
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(buf, pin->data, pin_len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "pin->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "pin",
    "pin_len"
   ],
   "osv_id": "ARVO-42511664",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_build_pin"
  }
 },
 {
  "osv_id": "ARVO-42511889",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "str",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 998,
    "size": null,
    "type": "char[64]"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 103
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "64",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 982,
    "fn": "ndpi_check_http_header",
    "code": "snprintf(str, sizeof(str), \"Found %s\", packet->line[i].p | sizeof(str) | packet->line[i].ptr | packet->line[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_http_header",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 982
   },
   "code": "snprintf(str, sizeof(str), \"Found %s\", packet->line[i].p | sizeof(str) | packet->line[i].ptr | packet->line[i]",
   "access": {
    "dir": "READ",
    "width": 12,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_http_header",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < packet->parsed_lines",
   "guard_count": 1,
   "control_structures": "FOR:974,SWITCH:977,IF:979,BREAK:986,IF:988,BREAK:995,IF:997,BREAK:1004,IF:1006,BREAK:1013,IF:1015,BREAK:1022"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[64]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ndpi_struct"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/897f8314b29cd7de9eeab9af15b3e189ae6724a1/ARVO-42511889/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_897f8314b29c.cpg",
   "testcase_size": 145
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
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--__interceptor_snprintf--ndpi_check_http_header"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "str[64]",
     "line": 980
    },
    {
     "code": "str[64]",
     "line": 989
    },
    {
     "code": "str[64]",
     "line": 998
    },
    {
     "code": "str[64]",
     "line": 1007
    },
    {
     "code": "str[64]",
     "line": 1016
    },
    {
     "code": "str[64]",
     "line": 1025
    },
    {
     "code": "str[64]",
     "line": 1034
    },
    {
     "code": "str[64]",
     "line": 1043
    },
    {
     "code": "str[64]",
     "line": 1052
    }
   ],
   "entity_decl": {
    "line": 980,
    "type": "char[64]"
   },
   "entity_name_cpg": "str",
   "func_lines": [
    969,
    1062
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
     "code": "i < packet->parsed_lines",
     "line": 974
    },
    {
     "code": "packet->line[i].ptr != NULL",
     "line": 975
    },
    {
     "code": "packet->line[i].len > 0",
     "line": 976
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "snprintf(str, sizeof(str), \"Found %s\", packet->line[i].ptr)",
     "name": "snprintf",
     "nargs": 4
    },
    {
     "code": "sizeof(str)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "packet->line[i].ptr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->line[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->line",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "str",
    "packet",
    "i"
   ],
   "osv_id": "ARVO-42511889",
   "sites": [
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 980
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 989
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 998
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1007
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1016
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1025
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1034
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1043
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1052
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_check_http_header"
  }
 },
 {
  "osv_id": "ARVO-42511900",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "str",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 998,
    "size": null,
    "type": "char[64]"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 103
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "64",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1018,
    "fn": "ndpi_check_http_header",
    "code": "snprintf(str, sizeof(str), \"Found %s\", packet->line[i].p | sizeof(str) | packet->line[i].ptr | packet->line[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_http_header",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 1018
   },
   "code": "snprintf(str, sizeof(str), \"Found %s\", packet->line[i].p | sizeof(str) | packet->line[i].ptr | packet->line[i]",
   "access": {
    "dir": "READ",
    "width": 11,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_http_header",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < packet->parsed_lines",
   "guard_count": 1,
   "control_structures": "FOR:974,SWITCH:977,IF:979,BREAK:986,IF:988,BREAK:995,IF:997,BREAK:1004,IF:1006,BREAK:1013,IF:1015,BREAK:1022"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[64]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ndpi_struct"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/897f8314b29cd7de9eeab9af15b3e189ae6724a1/ARVO-42511900/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_897f8314b29c.cpg",
   "testcase_size": 988
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
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--__interceptor_snprintf--ndpi_check_http_header"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "str[64]",
     "line": 980
    },
    {
     "code": "str[64]",
     "line": 989
    },
    {
     "code": "str[64]",
     "line": 998
    },
    {
     "code": "str[64]",
     "line": 1007
    },
    {
     "code": "str[64]",
     "line": 1016
    },
    {
     "code": "str[64]",
     "line": 1025
    },
    {
     "code": "str[64]",
     "line": 1034
    },
    {
     "code": "str[64]",
     "line": 1043
    },
    {
     "code": "str[64]",
     "line": 1052
    }
   ],
   "entity_decl": {
    "line": 980,
    "type": "char[64]"
   },
   "entity_name_cpg": "str",
   "func_lines": [
    969,
    1062
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
     "code": "i < packet->parsed_lines",
     "line": 974
    },
    {
     "code": "packet->line[i].ptr != NULL",
     "line": 975
    },
    {
     "code": "packet->line[i].len > 0",
     "line": 976
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "snprintf(str, sizeof(str), \"Found %s\", packet->line[i].ptr)",
     "name": "snprintf",
     "nargs": 4
    },
    {
     "code": "sizeof(str)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "packet->line[i].ptr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->line[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->line",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "str",
    "packet",
    "i"
   ],
   "osv_id": "ARVO-42511900",
   "sites": [
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 980
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 989
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 998
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1007
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1016
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1025
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1034
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1043
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "str[64]",
     "line": 1052
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_check_http_header"
  }
 },
 {
  "osv_id": "ARVO-42511938",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "path",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-myeid.c",
    "line": 532,
    "size": null,
    "type": "sc_path*"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "sc_pkcs15init_new_object",
    "file": "/src/opensc/src/tests/fuzzing/../../../src/pkcs15init/pkcs15-lib.c",
    "line": 3361
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 608,
    "fn": "myeid_create_key",
    "code": "memcpy(path->value, &file->path.value, file->path.len) | path->value | &file->path.value | file->path.value",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "myeid_create_key",
    "file": "/src/opensc/src/pkcs15init/pkcs15-myeid.c",
    "line": 608
   },
   "code": "memcpy(path->value, &file->path.value, file->path.len) | path->value | &file->path.value | file->path.value",
   "access": {
    "dir": "WRITE",
    "width": 190,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "myeid_create_key",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:542,SWITCH:544,BREAK:548,BREAK:552,IF:557,BREAK:559,IF:562,SWITCH:564,BREAK:567,BREAK:570,IF:572,BREAK:574"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_path*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "object"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42511938/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 172
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
   "dedup_token": "__asan_memcpy--myeid_create_key--sc_pkcs15init_store_secret_key"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "path = &prkey_info->path",
     "line": 587
    },
    {
     "code": "path = &skey_info->path",
     "line": 591
    }
   ],
   "entity_decl": {
    "line": 532,
    "type": "sc_path*"
   },
   "entity_name_cpg": "path",
   "func_lines": [
    524,
    668
   ],
   "func_params": {
    "names": [
     "profile",
     "p15card",
     "object"
    ],
    "types": [
     "sc_profile*",
     "sc_pkcs15_card*",
     "sc_pkcs15_object*"
    ]
   },
   "guards": [
    {
     "code": "(skey_info->access_flags & SC_PKCS15_PRKEY_ACCESS_EXTRACTABLE) == SC_PKCS15_PRKEY_ACCESS_EXTRACTABLE",
     "line": 557
    },
    {
     "code": "(skey_info->access_flags & SC_PKCS15_PRKEY_ACCESS_EXTRACTABLE) == SC_PKCS15_PRKEY_ACCESS_EXTRACTABLE",
     "line": 562
    },
    {
     "code": "object->type == SC_PKCS15_TYPE_SKEY_GENERIC",
     "line": 572
    },
    {
     "code": "_ret < 0",
     "line": 579
    },
    {
     "code": "(object->type & SC_PKCS15_TYPE_CLASS_MASK) == SC_PKCS15_TYPE_PRKEY",
     "line": 585
    },
    {
     "code": "_ret < 0",
     "line": 599
    },
    {
     "code": "_ret < 0",
     "line": 602
    },
    {
     "code": "r != SC_SUCCESS",
     "line": 617
    },
    {
     "code": "_ret < 0",
     "line": 619
    },
    {
     "code": "pin_object->type != SC_PKCS15_TYPE_AUTH_PIN",
     "line": 621
    },
    {
     "code": "_ret < 0",
     "line": 623
    },
    {
     "code": "pkcs15_auth_info == NULL",
     "line": 628
    },
    {
     "code": "pkcs15_auth_info->auth_type != SC_PKCS15_PIN_AUTH_TYPE_PIN",
     "line": 628
    },
    {
     "code": "_ret < 0",
     "line": 630
    },
    {
     "code": "pin_reference < MYEID_MAX_PINS",
     "line": 635
    },
    {
     "code": "_ret < 0",
     "line": 643
    },
    {
     "code": "object->user_consent != 0",
     "line": 648
    },
    {
     "code": "object->session_object != 0",
     "line": 654
    },
    {
     "code": "_ret < 0",
     "line": 660
    },
    {
     "code": "_ret < 0",
     "line": 665
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "memcpy(path->value, &file->path.value, file->path.len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "path->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "&file->path.value",
     "name": "<operator>.addressOf",
     "nargs": 1
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
     "code": "file->path.len",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "file->path",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "path",
    "file"
   ],
   "osv_id": "ARVO-42511938",
   "sites": [
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 618
    },
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 622
    },
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 629
    },
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 642
    },
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 664
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "myeid_create_key"
  }
 },
 {
  "osv_id": "ARVO-42512028",
  "project": "curl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "nread",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 116,
    "type": "int",
    "size": null
   }
  },
  "alloc": {
   "api": "calloc",
   "site": {
    "fn": "curl_docalloc",
    "file": "/src/curl/lib/memdebug.c",
    "line": 206
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "11",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 138,
    "fn": "Curl_fillreadbuffer",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Curl_fillreadbuffer",
    "file": "/src/curl/lib/transfer.c",
    "line": 138
   },
   "code": "nread = (int)data->state.fread_func(data->req.upload_fromhere, 1,",
   "access": {
    "dir": "WRITE",
    "width": 31075,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Curl_fillreadbuffer",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/curl/address/e240a546a7ac2fa7956adb664b8c40c4dee4f82b/ARVO-42512028/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_e240a546a7ac.cpg",
   "testcase_size": 31154
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
   "dedup_token": "__asan_memcpy--fuzz_read_callback(char*, unsigned long, unsigned long, void*)--Curl_fillreadbuffer"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "nread = (int)data->state.fread_func(data->req.upload_fromhere, 1,",
     "line": 138
    }
   ],
   "entity_decl": {
    "line": 116,
    "type": "int"
   },
   "entity_name_cpg": "nread",
   "func_lines": [
    112,
    262
   ],
   "func_params": {
    "names": [
     "conn",
     "bytes",
     "nreadp"
    ],
    "types": [
     "connectdata*",
     "int",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "nread == CURL_READFUNC_ABORT",
     "line": 141
    },
    {
     "code": "nread == CURL_READFUNC_PAUSE",
     "line": 146
    },
    {
     "code": "(size_t)nread > buffersize",
     "line": 167
    },
    {
     "code": "(nread - hexlen) == 0",
     "line": 241
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "nread = (int)data->state.fread_func(data->req.upload_fromhere, 1,",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "(int)data->state.fread_func(data->req.upload_fromhere, 1,",
     "name": "<operator>.cast",
     "nargs": null
    },
    {
     "code": "data->state.fread_func(data->req.upload_fromhere, 1,",
     "name": "<operator>.pointerCall",
     "nargs": null
    },
    {
     "code": "data->state.fread_func",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "data->state",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "data->req.upload_fromhere",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "data->req",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "nread",
    "data"
   ],
   "osv_id": "ARVO-42512028",
   "sites": [
    {
     "args": "11",
     "callee": "<operator>.alloc",
     "code": "hexbuffer[11]",
     "line": 190
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Curl_fillreadbuffer"
  }
 },
 {
  "osv_id": "ARVO-42512228",
  "project": "libjxl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "JXL_DEC_SUCCESS",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
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
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 86,
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "code": "JXL_DEC_SUCCESS != JxlDecoderGetColorAsICCProfile(",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "file": "/src/libjxl/lib/jxl/box_content_decoder.cc",
    "line": 86
   },
   "code": "JXL_DEC_SUCCESS != JxlDecoderGetColorAsICCProfile(",
   "access": {
    "dir": "READ",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "DecodeJpegXlOneShot",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "JXL_DEC_SUCCESS !=",
   "guard_count": 8,
   "control_structures": "IF:36,IF:44,FOR:57,IF:60,ELSE:63,IF:63,ELSE:66,IF:66,IF:67,ELSE:76,IF:76,IF:79"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "pixels",
   "icc_profile"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/b7076f1869914eee47b3eae107750f3a3ce43a76/ARVO-42512228/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_b7076f186991.cpg",
   "testcase_size": 61
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
   "dedup_token": "__asan_memcpy--jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)--HandleBoxes(JxlDecoderSt"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "JXL_DEC_SUCCESS",
   "func_lines": [
    29,
    128
   ],
   "func_params": {
    "names": [
     "jxl",
     "size",
     "pixels",
     "xsize",
     "ysize",
     "icc_profile"
    ],
    "types": [
     "uint8_t*",
     "size_t",
     "std.vector<float>*",
     "size_t*",
     "size_t*",
     "std.vector<uint8_t>*"
    ]
   },
   "guards": [
    {
     "code": "JXL_DEC_SUCCESS !=",
     "line": 36
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderSetParallelRunner(dec.get(),",
     "line": 44
    },
    {
     "code": "status == JXL_DEC_ERROR",
     "line": 60
    },
    {
     "code": "status == JXL_DEC_NEED_MORE_INPUT",
     "line": 63
    },
    {
     "code": "status == JXL_DEC_BASIC_INFO",
     "line": 66
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderGetBasicInfo(dec.get(), &info)",
     "line": 67
    },
    {
     "code": "status == JXL_DEC_COLOR_ENCODING",
     "line": 76
    },
    {
     "code": "JXL_DEC_SUCCESS !=",
     "line": 79
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderGetColorAsICCProfile(",
     "line": 86
    },
    {
     "code": "status == JXL_DEC_NEED_IMAGE_OUT_BUFFER",
     "line": 93
    },
    {
     "code": "JXL_DEC_SUCCESS !=",
     "line": 95
    },
    {
     "code": "buffer_size != *xsize * *ysize * 16",
     "line": 100
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderSetImageOutBuffer(dec.get(), &format,",
     "line": 109
    },
    {
     "code": "status == JXL_DEC_FULL_IMAGE",
     "line": 115
    },
    {
     "code": "status == JXL_DEC_SUCCESS",
     "line": 118
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderGetColorAsICCProfile(",
     "name": "<operator>.notEquals",
     "nargs": null
    },
    {
     "code": "JxlDecoderGetColorAsICCProfile(",
     "name": "JxlDecoderGetColorAsICCProfile",
     "nargs": null
    }
   ],
   "line_ids": [
    "JXL_DEC_SUCCESS"
   ],
   "osv_id": "ARVO-42512228",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)"
  }
 },
 {
  "osv_id": "ARVO-42512333",
  "project": "libjxl",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)",
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
    "fn": "LoadLE64",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "LoadLE64",
    "file": "/src/libjxl/lib/jxl/base/byte_order.h",
    "line": 113
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "LoadLE64",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/b7076f1869914eee47b3eae107750f3a3ce43a76/ARVO-42512333/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_b7076f186991.cpg",
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "LoadLE64--Refill--ReadBits"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    110,
    128
   ],
   "func_params": {
    "names": [
     "p"
    ],
    "types": [
     "uint8_t*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42512333",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "LoadLE64"
  }
 },
 {
  "osv_id": "ARVO-42513240",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "tmp_buf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "line": 2575,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "extract_word",
    "file": "/src/opensc/src/tests/fuzzing/fuzzer_tool.c",
    "line": 48
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "len",
   "size_expr_cpg_callee": "sc_mem_secure_alloc"
  },
  "sites": [
   {
    "code": "malloc(len)",
    "fn": "sc_pkcs15_allocate_object_content",
    "kind": "malloc",
    "line": 2593,
    "origin": "cpg",
    "args": "len"
   },
   {
    "kind": "unknown",
    "line": 2598,
    "fn": "sc_pkcs15_allocate_object_content",
    "code": "memcpy(tmp_buf, value, len)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15_allocate_object_content",
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "line": 2598
   },
   "code": "memcpy(tmp_buf, value, len)",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_pkcs15_allocate_object_content",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:2577,IF:2580,IF:2588,ELSE:2592,IF:2595"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "value",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/c4371fac9e5b5a5505d9f9f2ca6f8cc7a5d61a24/ARVO-42513240/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_c4371fac9e5b.cpg",
   "testcase_size": 477
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--sc_pkcs15_allocate_object_content--sc_pkcs15_pincache_add"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "tmp_buf = sc_mem_secure_alloc(len)",
     "line": 2591
    },
    {
     "code": "tmp_buf = malloc(len)",
     "line": 2593
    }
   ],
   "entity_decl": {
    "line": 2575,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "tmp_buf",
   "func_lines": [
    2571,
    2606
   ],
   "func_params": {
    "names": [
     "ctx",
     "obj",
     "value",
     "len"
    ],
    "types": [
     "sc_context*",
     "sc_pkcs15_object*",
     "unsigned char*",
     "size_t"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(tmp_buf, value, len)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "tmp_buf",
    "value",
    "len"
   ],
   "osv_id": "ARVO-42513240",
   "sites": [
    {
     "args": "obj",
     "callee": "sc_pkcs15_free_object_content",
     "code": "sc_pkcs15_free_object_content(obj)",
     "line": 2581
    },
    {
     "args": "len",
     "callee": "sc_mem_secure_alloc",
     "code": "sc_mem_secure_alloc(len)",
     "line": 2591
    },
    {
     "args": "len",
     "callee": "malloc",
     "code": "malloc(len)",
     "line": 2593
    },
    {
     "args": "obj",
     "callee": "sc_pkcs15_free_object_content",
     "code": "sc_pkcs15_free_object_content(obj)",
     "line": 2600
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_pkcs15_allocate_object_content"
  }
 },
 {
  "osv_id": "ARVO-42513357",
  "project": "mruby",
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
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "mrb ;; sz+2",
   "size_expr_cpg_callee": "mrb_malloc"
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "mpz_get_str",
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
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
   "fn": "mpz_get_str",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/872020bb3d85ba4066ec19cfcad375e51fdf024b/ARVO-42513357/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_872020bb3d85.cpg",
   "testcase_size": 27
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
   "dedup_token": "mpz_get_str--mrb_bint_to_s--int_to_s"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    685,
    724
   ],
   "func_params": {
    "names": [
     "mrb",
     "s",
     "sz",
     "base",
     "x"
    ],
    "types": [
     "mrb_state*",
     "char*",
     "mrb_int",
     "mrb_int",
     "mpz_t*"
    ]
   },
   "guards": [
    {
     "code": "x->sn < 0",
     "line": 702
    },
    {
     "code": "d < 10",
     "line": 710
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42513357",
   "sites": [
    {
     "args": "mrb ;; sz+2",
     "callee": "mrb_malloc",
     "code": "mrb_malloc(mrb, sz+2)",
     "line": 697
    },
    {
     "args": "mrb ;; t",
     "callee": "mrb_free",
     "code": "mrb_free(mrb,t)",
     "line": 721
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mpz_get_str"
  }
 },
 {
  "osv_id": "ARVO-42513590",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "y",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 742,
    "size": null,
    "type": "mpz_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 749,
    "fn": "mpz_get_int",
    "code": "digits(y) > 2 || y->p[1] > 1 | digits(y) > 2 | digits(y) | y->p[1] > 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mpz_get_int",
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 749
   },
   "code": "digits(y) > 2 || y->p[1] > 1 | digits(y) > 2 | digits(y) | y->p[1] > 1",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mpz_get_int",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:746,ELSE:749,IF:749,ELSE:752,IF:754"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mpz_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "y"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/a99d0036222ad4c3a300243113f7afff2618aff9/ARVO-42513590/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_a99d0036222a.cpg",
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
   "dedup_token": "mpz_get_int--bint_norm--mrb_bint_xor"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 742,
    "type": "mpz_t*"
   },
   "entity_name_cpg": "y",
   "func_lines": [
    741,
    758
   ],
   "func_params": {
    "names": [
     "y",
     "v"
    ],
    "types": [
     "mpz_t*",
     "mrb_int*"
    ]
   },
   "guards": [
    {
     "code": "y->sn == 0",
     "line": 746
    },
    {
     "code": "digits(y) > 2",
     "line": 749
    },
    {
     "code": "y->p[1] > 1",
     "line": 749
    },
    {
     "code": "MRB_INT_MAX < i",
     "line": 754
    },
    {
     "code": "i < MRB_INT_MIN",
     "line": 754
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "digits(y) > 2 ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "digits(y) > 2",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "digits(y)",
     "name": "digits",
     "nargs": 1
    },
    {
     "code": "y->p[1] > 1",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "y->p[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "y->p",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "y"
   ],
   "osv_id": "ARVO-42513590",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mpz_get_int"
  }
 },
 {
  "osv_id": "ARVO-42513620",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "y",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 742,
    "size": null,
    "type": "mpz_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 749,
    "fn": "mpz_get_int",
    "code": "digits(y) > 2 || y->p[1] > 1 | digits(y) > 2 | digits(y) | y->p[1] > 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mpz_get_int",
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 749
   },
   "code": "digits(y) > 2 || y->p[1] > 1 | digits(y) > 2 | digits(y) | y->p[1] > 1",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mpz_get_int",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:746,ELSE:749,IF:749,ELSE:752,IF:754"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mpz_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "y"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/a99d0036222ad4c3a300243113f7afff2618aff9/ARVO-42513620/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_a99d0036222a.cpg",
   "testcase_size": 389
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
   "dedup_token": "mpz_get_int--bint_norm--mrb_bint_add"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 742,
    "type": "mpz_t*"
   },
   "entity_name_cpg": "y",
   "func_lines": [
    741,
    758
   ],
   "func_params": {
    "names": [
     "y",
     "v"
    ],
    "types": [
     "mpz_t*",
     "mrb_int*"
    ]
   },
   "guards": [
    {
     "code": "y->sn == 0",
     "line": 746
    },
    {
     "code": "digits(y) > 2",
     "line": 749
    },
    {
     "code": "y->p[1] > 1",
     "line": 749
    },
    {
     "code": "MRB_INT_MAX < i",
     "line": 754
    },
    {
     "code": "i < MRB_INT_MIN",
     "line": 754
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "digits(y) > 2 ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "digits(y) > 2",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "digits(y)",
     "name": "digits",
     "nargs": 1
    },
    {
     "code": "y->p[1] > 1",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "y->p[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "y->p",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "y"
   ],
   "osv_id": "ARVO-42513620",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mpz_get_int"
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