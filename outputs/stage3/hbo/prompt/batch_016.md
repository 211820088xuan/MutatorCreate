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
  "osv_id": "ARVO-42494652",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "key_obj",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "line": 566,
    "size": null,
    "type": "sc_pkcs15_object"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "sc_oberthur_read_file",
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "line": 264
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "0x100",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 600,
    "fn": "sc_pkcs15emu_oberthur_add_pubkey",
    "code": "memcpy(key_obj.label, info_blob + offs + 2, len) | key_obj.label | info_blob + offs + 2 | info_blob + offs",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15emu_oberthur_add_pubkey",
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "line": 600
   },
   "code": "memcpy(key_obj.label, info_blob + offs + 2, len) | key_obj.label | info_blob + offs + 2 | info_blob + offs",
   "access": {
    "dir": "READ",
    "width": 254,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_pkcs15emu_oberthur_add_pubkey",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "offs > info_len | len > sizeof(key_obj.label) - 1 | offs > info_len",
   "guard_count": 4,
   "control_structures": "DO:573,DO:581,IF:581,IF:585,DO:586,IF:586,IF:589,IF:594,DO:595,IF:595,IF:597,IF:598"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_pkcs15_object",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/978c912c7089fa4573add7140170feb9fcbe7f87/ARVO-42494652/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_978c912c7089.cpg",
   "testcase_size": 802
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
   "dedup_token": "__asan_memcpy--sc_pkcs15emu_oberthur_add_pubkey--sc_oberthur_parse_publicinfo"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "key_obj.flags = SC_PKCS15_CO_FLAG_MODIFIABLE",
     "line": 590
    }
   ],
   "entity_decl": {
    "line": 566,
    "type": "sc_pkcs15_object"
   },
   "entity_name_cpg": "key_obj",
   "func_lines": [
    560,
    625
   ],
   "func_params": {
    "names": [
     "p15card",
     "file_id",
     "size"
    ],
    "types": [
     "sc_pkcs15_card*",
     "unsigned int",
     "unsigned int"
    ]
   },
   "guards": [
    {
     "code": "_ret < 0",
     "line": 581
    },
    {
     "code": "offs > info_len",
     "line": 585
    },
    {
     "code": "_ret < 0",
     "line": 586
    },
    {
     "code": "offs + 2 > info_len",
     "line": 594
    },
    {
     "code": "_ret < 0",
     "line": 595
    },
    {
     "code": "len > sizeof(key_obj.label) - 1",
     "line": 598
    },
    {
     "code": "offs > info_len",
     "line": 605
    },
    {
     "code": "_ret < 0",
     "line": 606
    },
    {
     "code": "len > sizeof(key_info.id.value)",
     "line": 608
    },
    {
     "code": "_ret < 0",
     "line": 609
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(key_obj.label, info_blob + offs + 2, len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "key_obj.label",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "info_blob + offs + 2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "info_blob + offs",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "key_obj",
    "info_blob",
    "offs",
    "len"
   ],
   "osv_id": "ARVO-42494652",
   "sites": [
    {
     "args": "0x100",
     "callee": "<operator>.alloc",
     "code": "ch_tmp[0x100]",
     "line": 567
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_pkcs15emu_oberthur_add_pubkey"
  }
 },
 {
  "osv_id": "ARVO-42495373",
  "project": "assimp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "head_pos",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/assimp/include/assimp/Hash.h",
    "line": 86,
    "size": null,
    "type": "std.size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Assimp::LWSImporter::InternReadFile(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> > const&, aiScene*, Assimp::IOSystem*)",
    "file": "/src/assimp/code/AssetLib/LWS/LWSLoader.cpp",
    "line": 884
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 88,
    "fn": "SuperFastHash(char const*, unsigned int, unsigned int)",
    "code": "ai_assert(head_pos > chunk_start_pos) | head_pos > chunk_start_pos",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "SuperFastHash(char const*, unsigned int, unsigned int)",
    "file": "/src/assimp/include/assimp/Hash.h",
    "line": 88
   },
   "code": "ai_assert(head_pos > chunk_start_pos) | head_pos > chunk_start_pos",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "~ChunkWriter",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "head_pos > chunk_start_pos",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": "std.size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/91cb2947ace52bcd9d297171bd9b66f5203370b5/ARVO-42495373/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_91cb2947ace5.cpg",
   "testcase_size": 4072
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
   "dedup_token": "SuperFastHash(char const*, unsigned int, unsigned int)--Assimp::SceneCombiner::AddNodePrefixesChecked(aiNode*, char const*, unsigned int, std::__1::vector<Assim"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "head_pos = writer.GetCurrentPos()",
     "line": 86
    }
   ],
   "entity_decl": {
    "line": 86,
    "type": "std.size_t"
   },
   "entity_name_cpg": "head_pos",
   "func_lines": [
    85,
    94
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "Assimp.ChunkWriter"
    ]
   },
   "guards": [
    {
     "code": "head_pos > chunk_start_pos",
     "line": 88
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "ai_assert(head_pos > chunk_start_pos)",
     "name": "ai_assert",
     "nargs": 1
    },
    {
     "code": "head_pos > chunk_start_pos",
     "name": "<operator>.greaterThan",
     "nargs": 2
    }
   ],
   "line_ids": [
    "head_pos",
    "chunk_start_pos"
   ],
   "osv_id": "ARVO-42495373",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "SuperFastHash(char const*, unsigned int, unsigned int)"
  }
 },
 {
  "osv_id": "ARVO-42495376",
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
    "fn": "g_malloc0 (/out/pngsave_buffer_fuzzer+0xff0c50)",
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
    "line": 824,
    "fn": "gif_internal_decode_frame",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "gif_internal_decode_frame",
    "file": "/src/libvips/libvips/foreign/libnsgif/libnsgif.c",
    "line": 824
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 16384,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "gif_internal_decode_frame",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42495376/report.log",
   "cpg": null,
   "testcase_size": 25
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
   "dedup_token": "__asan_memset--gif_internal_decode_frame--gif_decode_frame"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "gif_internal_decode_frame"
  }
 },
 {
  "osv_id": "ARVO-42495617",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "content",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1365,
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
   "size_expr_cpg": "sizeof(blosc2_metalayer) ;; 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc(sizeof(blosc2_metalayer), 1)",
    "fn": "get_vlmeta_from_trailer",
    "kind": "calloc",
    "line": 1305,
    "origin": "cpg",
    "args": "sizeof(blosc2_metalayer) ;; 1"
   },
   {
    "code": "malloc((size_t)nslen + 1)",
    "fn": "get_vlmeta_from_trailer",
    "kind": "malloc",
    "line": 1315,
    "origin": "cpg",
    "args": "(size_t)nslen + 1"
   },
   {
    "code": "malloc((size_t)content_len)",
    "fn": "get_vlmeta_from_trailer",
    "kind": "malloc",
    "line": 1365,
    "origin": "cpg",
    "args": "(size_t)content_len"
   },
   {
    "kind": "unknown",
    "line": 1366,
    "fn": "get_vlmeta_from_trailer",
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_vlmeta_from_trailer",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1366
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
   "guard_count": 1,
   "control_structures": "IF:1267,IF:1276,IF:1279,IF:1286,IF:1291,FOR:1297,IF:1299,IF:1302,IF:1312,IF:1324,IF:1327,IF:1333"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "trailer",
   "trailer_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/81c2fcd59368a9c57da77416066e731a7183a57d/ARVO-42495617/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_81c2fcd59368.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--get_vlmeta_from_trailer--frame_get_vlmetalayers"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* content = malloc((size_t)content_len)",
     "line": 1365
    }
   ],
   "entity_decl": {
    "line": 1365,
    "type": "char*"
   },
   "entity_name_cpg": "content",
   "func_lines": [
    1259,
    1370
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
     "line": 1267
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1276
    },
    {
     "code": "idxp[0] != 0xde",
     "line": 1279
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1286
    },
    {
     "code": "nmetalayers < 0",
     "line": 1291
    },
    {
     "code": "nmetalayers > BLOSC2_MAX_VLMETALAYERS",
     "line": 1291
    },
    {
     "code": "nmetalayer < nmetalayers",
     "line": 1297
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1299
    },
    {
     "code": "(*idxp & 0xe0u) != 0xa0u",
     "line": 1302
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1312
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1324
    },
    {
     "code": "(*idxp & 0xffu) != 0xd2u",
     "line": 1327
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1333
    },
    {
     "code": "offset < 0",
     "line": 1338
    },
    {
     "code": "*content_marker != 0xc6",
     "line": 1344
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1351
    },
    {
     "code": "content_len < 0",
     "line": 1355
    },
    {
     "code": "trailer_len < trailer_pos",
     "line": 1362
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
   "osv_id": "ARVO-42495617",
   "sites": [
    {
     "args": "sizeof(blosc2_metalayer) ;; 1",
     "callee": "calloc",
     "code": "calloc(sizeof(blosc2_metalayer), 1)",
     "line": 1305
    },
    {
     "args": "(size_t)nslen + 1",
     "callee": "malloc",
     "code": "malloc((size_t)nslen + 1)",
     "line": 1315
    },
    {
     "args": "(size_t)content_len",
     "callee": "malloc",
     "code": "malloc((size_t)content_len)",
     "line": 1365
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
  "osv_id": "ARVO-42495817",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "content",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1201,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib32/libc.so.6+0x18646)",
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
    "code": "calloc(sizeof(blosc2_metalayer), 1)",
    "fn": "get_meta_from_header",
    "kind": "calloc",
    "line": 1141,
    "origin": "cpg",
    "args": "sizeof(blosc2_metalayer) ;; 1"
   },
   {
    "code": "malloc((size_t)nslen + 1)",
    "fn": "get_meta_from_header",
    "kind": "malloc",
    "line": 1151,
    "origin": "cpg",
    "args": "(size_t)nslen + 1"
   },
   {
    "code": "malloc((size_t)content_len)",
    "fn": "get_meta_from_header",
    "kind": "malloc",
    "line": 1201,
    "origin": "cpg",
    "args": "(size_t)content_len"
   },
   {
    "kind": "unknown",
    "line": 1202,
    "fn": "get_meta_from_header",
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_meta_from_header",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1202
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
   "guard_count": 1,
   "control_structures": "IF:1105,IF:1113,IF:1116,IF:1122,IF:1127,FOR:1133,IF:1135,IF:1138,IF:1148,IF:1160,IF:1163,IF:1169"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "header",
   "header_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/81c2fcd59368a9c57da77416066e731a7183a57d/ARVO-42495817/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_81c2fcd59368.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--get_meta_from_header--frame_get_metalayers"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* content = malloc((size_t)content_len)",
     "line": 1201
    }
   ],
   "entity_decl": {
    "line": 1201,
    "type": "char*"
   },
   "entity_name_cpg": "content",
   "func_lines": [
    1098,
    1207
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
     "line": 1105
    },
    {
     "code": "header_len < header_pos",
     "line": 1113
    },
    {
     "code": "metalayers_idx[0] != 0xde",
     "line": 1116
    },
    {
     "code": "header_len < header_pos",
     "line": 1122
    },
    {
     "code": "nmetalayers < 0",
     "line": 1127
    },
    {
     "code": "nmetalayers > BLOSC2_MAX_METALAYERS",
     "line": 1127
    },
    {
     "code": "nmetalayer < nmetalayers",
     "line": 1133
    },
    {
     "code": "header_len < header_pos",
     "line": 1135
    },
    {
     "code": "(*idxp & 0xe0u) != 0xa0u",
     "line": 1138
    },
    {
     "code": "header_len < header_pos",
     "line": 1148
    },
    {
     "code": "header_len < header_pos",
     "line": 1160
    },
    {
     "code": "(*idxp & 0xffu) != 0xd2u",
     "line": 1163
    },
    {
     "code": "header_len < header_pos",
     "line": 1169
    },
    {
     "code": "offset < 0",
     "line": 1174
    },
    {
     "code": "*content_marker != 0xc6",
     "line": 1180
    },
    {
     "code": "header_len < header_pos",
     "line": 1187
    },
    {
     "code": "content_len < 0",
     "line": 1191
    },
    {
     "code": "header_len < header_pos",
     "line": 1198
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
   "osv_id": "ARVO-42495817",
   "sites": [
    {
     "args": "sizeof(blosc2_metalayer) ;; 1",
     "callee": "calloc",
     "code": "calloc(sizeof(blosc2_metalayer), 1)",
     "line": 1141
    },
    {
     "args": "(size_t)nslen + 1",
     "callee": "malloc",
     "code": "malloc((size_t)nslen + 1)",
     "line": 1151
    },
    {
     "args": "(size_t)content_len",
     "callee": "malloc",
     "code": "malloc((size_t)content_len)",
     "line": 1201
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
  "osv_id": "ARVO-42495831",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "_dest",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 1339,
    "size": null,
    "type": "uint8_t*"
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
   "size_expr_cpg": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "code": "malloc(strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1)",
    "fn": "blosc_d",
    "kind": "malloc",
    "line": 1389,
    "origin": "cpg",
    "args": "strlen(frame->urlpath) + 1 + 8 + strlen(\".chunk\") + 1"
   },
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
   "guard_count": 0,
   "control_structures": "IF:1345,IF:1349,IF:1356,IF:1363,IF:1365,DO:1366,IF:1366,BREAK:1366,IF:1369,DO:1370,IF:1370,BREAK:1370"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/38b23d5ab3c67c5528faed5750611f34c3f18f3f/ARVO-42495831/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_38b23d5ab3c6.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--blosc_d--_blosc_getitem"
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
   "osv_id": "ARVO-42495831",
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
  "osv_id": "ARVO-42495891",
  "project": "wasm3",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "_sp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1171,
    "type": "m3stack_t",
    "size": null
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "m3_NewRuntime",
    "file": "/src/wasm3/source/m3_env.c",
    "line": 180
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1175,
    "fn": "op_Const64",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "op_Const64",
    "file": "/src/wasm3/source/m3_exec.h",
    "line": 1175
   },
   "code": "*(u64 *)(_sp + *((i32 *)_pc++))",
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "op_Const64",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wasm3/address/7dd44291c7e6d60f6c358c83557e4e9c8b028e53/ARVO-42495891/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wasm3_7dd44291c7e6.cpg",
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
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "op_Const64--Call--EvaluateExpression"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1171,
    "type": "m3stack_t"
   },
   "entity_name_cpg": "_sp",
   "func_lines": [
    1171,
    1177
   ],
   "func_params": {
    "names": [
     "_pc",
     "_sp",
     "_mem",
     "_r0",
     "_fp0"
    ],
    "types": [
     "pc_t",
     "m3stack_t",
     "M3MemoryHeaderd_m3Op (Const64)",
     "m3reg_t",
     "f64"
    ]
   },
   "guards": [
    {
     "code": "M3_SIZEOF_PTR == 4",
     "line": 1174
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "slot (u64) = value",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "slot (u64)",
     "name": "slot",
     "nargs": 0
    },
    {
     "code": "*(u64 *)(_sp + *((i32 *)_pc++))",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(u64 *)(_sp + *((i32 *)_pc++))",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "_sp + *((i32 *)_pc++)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "*((i32 *)_pc++)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(i32 *)_pc++",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "_pc++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "_sp",
    "_pc",
    "value"
   ],
   "osv_id": "ARVO-42495891",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "op_Const64"
  }
 },
 {
  "osv_id": "ARVO-42496638",
  "project": "readstat",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "src_len",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 7,
    "type": "size_t",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "readstat_malloc",
    "file": "/src/readstat/src/readstat_malloc.c",
    "line": 12
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 10,
    "fn": "readstat_convert",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "readstat_convert",
    "file": "/src/readstat/src/readstat_convert.c",
    "line": 10
   },
   "code": "src_len && src[src_len-1] == ' '",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "readstat_convert",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/readstat/address/a8e6705453f0e610a698a4d98b3dfa3087cf4b28/ARVO-42496638/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/readstat_a8e6705453f0.cpg",
   "testcase_size": 1895
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
   "dedup_token": "readstat_convert--sav_process_row--sav_read_uncompressed_data"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 7,
    "type": "size_t"
   },
   "entity_name_cpg": "src_len",
   "func_lines": [
    7,
    36
   ],
   "func_params": {
    "names": [
     "dst",
     "dst_len",
     "src",
     "src_len",
     "converter"
    ],
    "types": [
     "char*",
     "size_t",
     "char*",
     "size_t",
     "iconv_t"
    ]
   },
   "guards": [
    {
     "code": "src[src_len-1] == ' '",
     "line": 10
    },
    {
     "code": "dst_len == 0",
     "line": 13
    },
    {
     "code": "status == (size_t)-1",
     "line": 19
    },
    {
     "code": "errno == E2BIG",
     "line": 20
    },
    {
     "code": "errno == EILSEQ",
     "line": 22
    },
    {
     "code": "errno != EINVAL",
     "line": 24
    },
    {
     "code": "src_len + 1 > dst_len",
     "line": 29
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "src_len && src[src_len-1] == ' '",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "src[src_len-1] == ' '",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "src[src_len-1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "src_len-1",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "src_len",
    "src"
   ],
   "osv_id": "ARVO-42496638",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "readstat_convert"
  }
 },
 {
  "osv_id": "ARVO-42496980",
  "project": "espeak-ng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 539,
    "type": "uint8_t",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/espeak-ng/tests/ssml-fuzzer.c",
    "line": 61
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
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "string_decoder_getc_utf_8",
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539
   },
   "code": "c = *decoder->current++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "string_decoder_getc_utf_8",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/espeak-ng/address/0a713d52bbf3e061823d1a7f35e5303e7320f27a/ARVO-42496980/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0a713d52bbf3.cpg",
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
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "dedup_token": "string_decoder_getc_utf_8--text_decoder_getc--GetC"
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
   "osv_id": "ARVO-42496980",
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
  "osv_id": "ARVO-42497205",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "alpn_str",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1553,
    "size": null,
    "type": "char[256]"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "ndpi_malloc",
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 98
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
    "line": 1180,
    "fn": "processClientServerHello",
    "code": "alpn_str[alpn_str_len+alpn_i] = packet->payload[s_offset | alpn_str[alpn_str_len+alpn_i] | alpn_str_len+alpn_i | packet->payload[s_offset+alpn_i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "processClientServerHello",
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1180
   },
   "code": "alpn_str[alpn_str_len+alpn_i] = packet->payload[s_offset | alpn_str[alpn_str_len+alpn_i] | alpn_str_len+alpn_i | packet->payload[s_offset+alpn_i]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "processClientServerHello",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "s_offset < tot_alpn_len | s_offset < total_len | alpn_str_len > 0",
   "guard_count": 11,
   "control_structures": "IF:1062,IF:1068,IF:1073,IF:1082,IF:1095,ELSE:1097,IF:1098,IF:1102,IF:1106,IF:1117,ELSE:1120,FOR:1127"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[256]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow",
   "quic_version"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/6333bb1702619d29e7f6ce2acf9091c0ccc436c9/ARVO-42497205/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_6333bb170261.cpg",
   "testcase_size": 3023
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
   "dedup_token": "processClientServerHello--processTLSBlock--ndpi_search_tls_tcp"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "alpn_str[256]",
     "line": 1156
    },
    {
     "code": "alpn_str[alpn_str_len] = ','",
     "line": 1175
    },
    {
     "code": "alpn_str[alpn_str_len+alpn_i] = packet->payload[s_offset+alpn_i]",
     "line": 1180
    },
    {
     "code": "alpn_str[alpn_str_len] = '\\0'",
     "line": 1189
    },
    {
     "code": "alpn_str[256]",
     "line": 1553
    },
    {
     "code": "alpn_str[alpn_str_len] = ','",
     "line": 1572
    },
    {
     "code": "alpn_str[alpn_str_len+alpn_i] = packet->payload[s_offset+alpn_i]",
     "line": 1577
    },
    {
     "code": "alpn_str[alpn_str_len] = '\\0'",
     "line": 1586
    }
   ],
   "entity_decl": {
    "line": 1156,
    "type": "char[256]"
   },
   "entity_name_cpg": "alpn_str",
   "func_lines": [
    1037,
    1886
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow",
     "quic_version"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*",
     "uint32_t"
    ]
   },
   "guards": [
    {
     "code": "quic_version != 0",
     "line": 1050
    },
    {
     "code": "total_len > packet->payload_packet_len",
     "line": 1062
    },
    {
     "code": "packet->payload[1] != 0x0",
     "line": 1062
    },
    {
     "code": "total_len > 4",
     "line": 1068
    },
    {
     "code": "base_offset < total_len",
     "line": 1073
    },
    {
     "code": "handshake_type == 0x02",
     "line": 1082
    },
    {
     "code": "tls_version < 0x7F15",
     "line": 1098
    },
    {
     "code": "(offset+3) > packet->payload_packet_len",
     "line": 1102
    },
    {
     "code": "(flow->protos.tls_quic_stun.tls_quic.server_unsafe_cipher = ndpi_is_safe_ssl_cipher(ja3.server.cipher[0])) == 1",
     "line": 1106
    },
    {
     "code": "(offset + 1) < packet->payload_packet_len",
     "line": 1117
    },
    {
     "code": "i<extension_len",
     "line": 1127
    },
    {
     "code": "(offset+4) > packet->payload_packet_len",
     "line": 1130
    },
    {
     "code": "ja3.server.num_tls_extension < MAX_NUM_JA3",
     "line": 1135
    },
    {
     "code": "extension_id == 43",
     "line": 1143
    },
    {
     "code": "extension_id == 16",
     "line": 1153
    },
    {
     "code": "s_offset < tot_alpn_len",
     "line": 1165
    },
    {
     "code": "s_offset < total_len",
     "line": 1165
    },
    {
     "code": "(alpn_str_len+alpn_len+1) < (sizeof(alpn_str)-1)",
     "line": 1173
    },
    {
     "code": "alpn_str_len > 0",
     "line": 1174
    },
    {
     "code": "alpn_i<alpn_len",
     "line": 1179
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.alpn == NULL",
     "line": 1194
    },
    {
     "code": "ja3.server.alpn[i] != '\\0'",
     "line": 1200
    },
    {
     "code": "ja3.server.alpn[i] == ','",
     "line": 1201
    },
    {
     "code": "extension_id == 11",
     "line": 1202
    },
    {
     "code": "i<extension_len-1",
     "line": 1209
    },
    {
     "code": "ja3.server.num_elliptic_curve_point_format < MAX_NUM_JA3",
     "line": 1216
    },
    {
     "code": "i<ja3.server.num_cipher",
     "line": 1238
    },
    {
     "code": "i > 0",
     "line": 1239
    },
    {
     "code": "rc > 0",
     "line": 1245
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1245
    },
    {
     "code": "i<ja3.server.num_tls_extension",
     "line": 1249
    },
    {
     "code": "i > 0",
     "line": 1250
    },
    {
     "code": "i<ja3.server.num_elliptic_curve_point_format",
     "line": 1256
    },
    {
     "code": "i > 0",
     "line": 1258
    },
    {
     "code": "rc > 0",
     "line": 1259
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1259
    },
    {
     "code": "ja3.server.alpn[0] != '\\0'",
     "line": 1262
    },
    {
     "code": "rc > 0",
     "line": 1264
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1264
    },
    {
     "code": "i<16",
     "line": 1280
    },
    {
     "code": "handshake_type == 0x01",
     "line": 1289
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.ssl_version < 0x0302",
     "line": 1294
    },
    {
     "code": "(session_id_len+base_offset+3) > packet->payload_packet_len",
     "line": 1297
    },
    {
     "code": "(session_id_len+base_offset+cookie_len+4) > packet->payload_packet_len",
     "line": 1308
    },
    {
     "code": "i<cipher_len",
     "line": 1319
    },
    {
     "code": "*id == 0",
     "line": 1325
    },
    {
     "code": "packet->payload[cipher_offset+i] != packet->payload[cipher_offset+i+1]",
     "line": 1325
    },
    {
     "code": "ja3.client.num_cipher < MAX_NUM_JA3",
     "line": 1331
    },
    {
     "code": "offset < total_len",
     "line": 1352
    },
    {
     "code": "offset < total_len",
     "line": 1367
    },
    {
     "code": "extension_offset < extensions_len",
     "line": 1381
    },
    {
     "code": "extension_id == 0",
     "line": 1394
    },
    {
     "code": "packet->payload[extn_off] != packet->payload[extn_off+1]",
     "line": 1394
    },
    {
     "code": "ja3.client.num_tls_extension < MAX_NUM_JA3",
     "line": 1397
    },
    {
     "code": "extension_id == 0",
     "line": 1407
    },
    {
     "code": "extension_id == 10",
     "line": 1465
    },
    {
     "code": "i<extension_len-2",
     "line": 1473
    },
    {
     "code": "s_group == 0",
     "line": 1479
    },
    {
     "code": "packet->payload[s_offset+i] != packet->payload[s_offset+i+1]",
     "line": 1479
    },
    {
     "code": "ja3.client.num_elliptic_curve < MAX_NUM_JA3",
     "line": 1481
    },
    {
     "code": "extension_id == 11",
     "line": 1499
    },
    {
     "code": "i<extension_len-1",
     "line": 1506
    },
    {
     "code": "ja3.client.num_elliptic_curve_point_format < MAX_NUM_JA3",
     "line": 1513
    },
    {
     "code": "extension_id == 13",
     "line": 1528
    },
    {
     "code": "i<tot_signature_algorithms_len",
     "line": 1539
    },
    {
     "code": "rc < 0",
     "line": 1542
    },
    {
     "code": "extension_id == 16",
     "line": 1550
    },
    {
     "code": "s_offset < tot_alpn_len",
     "line": 1562
    },
    {
     "code": "s_offset < total_len",
     "line": 1562
    },
    {
     "code": "(alpn_str_len+alpn_len+1) < (sizeof(alpn_str)-1)",
     "line": 1570
    },
    {
     "code": "alpn_str_len > 0",
     "line": 1571
    },
    {
     "code": "alpn_i<alpn_len",
     "line": 1576
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.alpn == NULL",
     "line": 1591
    },
    {
     "code": "ja3.client.alpn[i] != '\\0'",
     "line": 1597
    },
    {
     "code": "ja3.client.alpn[i] == ','",
     "line": 1598
    },
    {
     "code": "extension_id == 43",
     "line": 1600
    },
    {
     "code": "version_len == (extension_len-1)",
     "line": 1610
    },
    {
     "code": "j+1<version_len",
     "line": 1617
    },
    {
     "code": "(version_str_len+8) < sizeof(version_str)",
     "line": 1626
    },
    {
     "code": "version_str_len > 0",
     "line": 1629
    },
    {
     "code": "j > 0",
     "line": 1638
    },
    {
     "code": "rc > 0",
     "line": 1640
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.tls_supported_versions == NULL",
     "line": 1649
    },
    {
     "code": "extension_id == 65486",
     "line": 1652
    },
    {
     "code": "(e_offset+4) < packet->payload_packet_len",
     "line": 1669
    },
    {
     "code": "(e_offset+4) < packet->payload_packet_len",
     "line": 1673
    },
    {
     "code": "e_offset+e_sni_len < packet->payload_packet_len",
     "line": 1678
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.encrypted_sni.esni == NULL",
     "line": 1683
    },
    {
     "code": "i<(e_offset+e_sni_len)",
     "line": 1689
    },
    {
     "code": "extension_id == 65445",
     "line": 1703
    },
    {
     "code": "extension_id == 57",
     "line": 1704
    },
    {
     "code": "s_offset < final_offset",
     "line": 1721
    },
    {
     "code": "s_offset+param_len > final_offset",
     "line": 1745
    },
    {
     "code": "param_type==0x3129",
     "line": 1748
    },
    {
     "code": "i<ja3.client.num_cipher",
     "line": 1773
    },
    {
     "code": "i > 0",
     "line": 1775
    },
    {
     "code": "rc > 0",
     "line": 1776
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1776
    },
    {
     "code": "rc > 0",
     "line": 1780
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1780
    },
    {
     "code": "i<ja3.client.num_tls_extension",
     "line": 1784
    },
    {
     "code": "i > 0",
     "line": 1786
    },
    {
     "code": "rc > 0",
     "line": 1787
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1787
    },
    {
     "code": "rc > 0",
     "line": 1791
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1791
    },
    {
     "code": "i<ja3.client.num_elliptic_curve",
     "line": 1795
    },
    {
     "code": "i > 0",
     "line": 1797
    },
    {
     "code": "rc > 0",
     "line": 1798
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1798
    },
    {
     "code": "rc > 0",
     "line": 1802
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1802
    },
    {
     "code": "i<ja3.client.num_elliptic_curve_point_format",
     "line": 1804
    },
    {
     "code": "i > 0",
     "line": 1806
    },
    {
     "code": "rc > 0",
     "line": 1807
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1807
    },
    {
     "code": "rc > 0",
     "line": 1813
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1813
    },
    {
     "code": "i<16",
     "line": 1824
    },
    {
     "code": "rc > 0",
     "line": 1828
    },
    {
     "code": "ndpi_struct->malicious_ja3_automa.ac_automa != NULL",
     "line": 1835
    },
    {
     "code": "rc1 > 0",
     "line": 1839
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.alpn == NULL",
     "line": 1846
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.client_requested_server_name[0] != '\\0'",
     "line": 1853
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.client_requested_server_name[0] == 0",
     "line": 1858
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.encrypted_sni.esni == NULL",
     "line": 1860
    },
    {
     "code": "offset == total_len",
     "line": 1873
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "alpn_str[alpn_str_len+alpn_i] = packet->payload[s_offset+alpn_i]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "alpn_str[alpn_str_len+alpn_i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "alpn_str_len+alpn_i",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "packet->payload[s_offset+alpn_i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "s_offset+alpn_i",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "alpn_str",
    "alpn_str_len",
    "alpn_i",
    "packet",
    "s_offset"
   ],
   "osv_id": "ARVO-42497205",
   "sites": [
    {
     "args": "JA3_STR_LEN",
     "callee": "<operator>.alloc",
     "code": "ja3_str[JA3_STR_LEN]",
     "line": 1043
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "md5_hash[16]",
     "line": 1045
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "buffer[64] = { '\\0' }",
     "line": 1049
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "alpn_str[256]",
     "line": 1156
    },
    {
     "args": "alpn_str",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(alpn_str)",
     "line": 1195
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "alpn_str[256]",
     "line": 1553
    },
    {
     "args": "alpn_str",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(alpn_str)",
     "line": 1592
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "version_str[256]",
     "line": 1603
    },
    {
     "args": "version_str",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(version_str)",
     "line": 1650
    },
    {
     "args": "e_sni_len*2+1",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(e_sni_len*2+1)",
     "line": 1684
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "processClientServerHello"
  }
 },
 {
  "osv_id": "ARVO-42497224",
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
    "file": "/src/jpeg-xl/lib/jxl/base/cache_aligned.cc",
    "line": 94
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
    "file": "/src/libvips/libvips/foreign/jxl2vips.c",
    "line": 156
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 592,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42497224/report.log",
   "cpg": null,
   "testcase_size": 33
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
   "dedup_token": "__asan_memcpy--jxl::PerformAlphaWeightedAdd(float const*, float const*, float const*, float*, unsigned long, bool)--jxl::PerformBlending(float const* const*, fl"
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
  "osv_id": "ARVO-42497373",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "s",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/fmt_fp.c",
    "line": 87,
    "size": null,
    "type": "char*"
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
    "line": 200,
    "fn": "mrb_format_float",
    "code": "*s++ = '0' | *s++ | s++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mrb_format_float",
    "file": "/src/mruby/src/fmt_fp.c",
    "line": 200
   },
   "code": "*s++ = '0' | *s++ | s++",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_format_float",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:91,IF:95,IF:99,IF:102,IF:107,ELSE:110,IF:110,IF:117,GOTO:121,ELSE:122,IF:122,IF:132"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "buf",
   "buf_size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/b9bde0c918ac7122db85e1837b3c7dd901b1c40e/ARVO-42497373/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_b9bde0c918ac.cpg",
   "testcase_size": 12
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
   "dedup_token": "mrb_format_float--fmt_float--mrb_str_format"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*s = buf",
     "line": 87
    }
   ],
   "entity_decl": {
    "line": 87,
    "type": "char*"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    85,
    365
   ],
   "func_params": {
    "names": [
     "f",
     "buf",
     "buf_size",
     "fmt",
     "prec",
     "sign"
    ],
    "types": [
     "mrb_float",
     "char*",
     "size_t",
     "char",
     "int",
     "char"
    ]
   },
   "guards": [
    {
     "code": "prec < 0",
     "line": 132
    },
    {
     "code": "fmt == 'g'",
     "line": 138
    },
    {
     "code": "prec == 0",
     "line": 138
    },
    {
     "code": "f == 0.0",
     "line": 148
    },
    {
     "code": "fmt == 'e'",
     "line": 150
    },
    {
     "code": "fmt == 'f'",
     "line": 152
    },
    {
     "code": "f < 1.0",
     "line": 155
    },
    {
     "code": "*neg_pow > f",
     "line": 163
    },
    {
     "code": "f < 1.0",
     "line": 169
    },
    {
     "code": "e == 0",
     "line": 172
    },
    {
     "code": "fmt == 'f'",
     "line": 184
    },
    {
     "code": "fmt == 'g'",
     "line": 184
    },
    {
     "code": "prec + e + 1 > buf_remaining",
     "line": 189
    },
    {
     "code": "org_fmt == 'g'",
     "line": 193
    },
    {
     "code": "prec > (buf_remaining - 6)",
     "line": 210
    },
    {
     "code": "fmt == 'g'",
     "line": 212
    },
    {
     "code": "fmt == 'f'",
     "line": 230
    },
    {
     "code": "(e + prec + 2) > buf_remaining",
     "line": 233
    },
    {
     "code": "prec < 0",
     "line": 235
    },
    {
     "code": "fmt == 'e'",
     "line": 242
    },
    {
     "code": "prec > (buf_remaining - 6)",
     "line": 242
    },
    {
     "code": "fmt == 'g'",
     "line": 248
    },
    {
     "code": "e < prec",
     "line": 248
    },
    {
     "code": "fmt == 'f'",
     "line": 252
    },
    {
     "code": "prec < 0",
     "line": 259
    },
    {
     "code": "fmt == 'e'",
     "line": 275
    },
    {
     "code": "fmt == 'g'",
     "line": 277
    },
    {
     "code": "prec == 0",
     "line": 278
    },
    {
     "code": "i < num_digits",
     "line": 285
    },
    {
     "code": "dec == 0",
     "line": 288
    },
    {
     "code": "prec > 0",
     "line": 288
    },
    {
     "code": "*rs == '.'",
     "line": 300
    },
    {
     "code": "*rs < '0'",
     "line": 304
    },
    {
     "code": "*rs > '9'",
     "line": 304
    },
    {
     "code": "*rs < '9'",
     "line": 309
    },
    {
     "code": "rs == buf",
     "line": 314
    },
    {
     "code": "*rs == '0'",
     "line": 319
    },
    {
     "code": "rs[1] == '.'",
     "line": 321
    },
    {
     "code": "fmt != 'f'",
     "line": 321
    },
    {
     "code": "e_sign == '-'",
     "line": 326
    },
    {
     "code": "ss > rs",
     "line": 334
    },
    {
     "code": "f < 1.0",
     "line": 339
    },
    {
     "code": "fmt == 'f'",
     "line": 339
    },
    {
     "code": "org_fmt == 'g'",
     "line": 346
    },
    {
     "code": "prec > 0",
     "line": 346
    },
    {
     "code": "s[-1] == '0'",
     "line": 348
    },
    {
     "code": "s[-1] == '.'",
     "line": 351
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "*s++ = '0'",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*s++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "s++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "s"
   ],
   "osv_id": "ARVO-42497373",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_format_float"
  }
 },
 {
  "osv_id": "ARVO-42497607",
  "project": "serenity",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/serenity/AK/StringView.h",
    "line": 37,
    "size": null,
    "type": "size_t"
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
    "line": 37,
    "fn": "AK::StringView::StringView(char const*)",
    "code": "i = 0 | i < alphabet.size() | alphabet.size() | ++i",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AK::StringView::StringView(char const*)",
    "file": "/src/serenity/AK/StringView.h",
    "line": 37
   },
   "code": "i = 0 | i < alphabet.size() | alphabet.size() | ++i",
   "access": {
    "dir": "READ",
    "width": 3,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "make_lookup_table",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < alphabet.size()",
   "guard_count": 1,
   "control_structures": "FOR:37"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/33eb9a6ddcd6a9b1588ef3b437cc11d612324f5a/ARVO-42497607/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_33eb9a6ddcd6.cpg",
   "testcase_size": 3
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
   "dedup_token": "strlen--AK::StringView::StringView(char const*)--AK::Formatter<char const*, void>::format(AK::FormatBuilder&, char const*)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "i = 0",
     "line": 37
    }
   ],
   "entity_decl": {
    "line": 37,
    "type": "size_t"
   },
   "entity_name_cpg": "i",
   "func_lines": [
    33,
    41
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [
    {
     "code": "Array<u8",
     "line": 36
    },
    {
     "code": "256> table {}",
     "line": 36
    },
    {
     "code": "i < alphabet.size()",
     "line": 37
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
     "code": "i < alphabet.size()",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "alphabet.size()",
     "name": "size",
     "nargs": 1
    },
    {
     "code": "++i",
     "name": "<operator>.preIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "i",
    "alphabet"
   ],
   "osv_id": "ARVO-42497607",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AK::StringView::StringView(char const*)"
  }
 },
 {
  "osv_id": "ARVO-42497951",
  "project": "libjxl",
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
    "line": 199,
    "fn": "StoreLE32",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "StoreLE32",
    "file": "/src/libjxl/lib/jxl/base/byte_order.h",
    "line": 199
   },
   "code": "",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "StoreLE32",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/b45981e8365dec86ccfc16991d0573a521bf17db/ARVO-42497951/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_b45981e8365d.cpg",
   "testcase_size": 34
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
   "dedup_token": "StoreLE32--StoreLEFloat--StoreFloatRow<&jxl::(anonymous namespace)::StoreLEFloat>"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    196,
    207
   ],
   "func_params": {
    "names": [
     "native",
     "p"
    ],
    "types": [
     "uint32_t",
     "uint8_t*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42497951",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "StoreLE32"
  }
 },
 {
  "osv_id": "ARVO-42497965",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/lib/monkey/mk_core/mk_rconf.c",
    "line": 183,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mk_mem_alloc",
    "file": "/src/fluent-bit/lib/monkey/mk_core/../include/monkey/mk_core/mk_memory.h",
    "line": 53
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "PATH_MAX",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 235,
    "fn": "mk_rconf_read",
    "code": "buf[len - 1] == '\\n' | buf[len - 1] | len - 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mk_rconf_read",
    "file": "/src/fluent-bit/lib/monkey/mk_core/mk_rconf.c",
    "line": 235
   },
   "code": "buf[len - 1] == '\\n' | buf[len - 1] | len - 1",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mk_rconf_read",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "len > 9 | len > 3 | i < len",
   "guard_count": 5,
   "control_structures": "IF:195,IF:197,IF:199,IF:203,IF:212,IF:220,IF:227,WHILE:233,IF:235,IF:237,ELSE:241,IF:247"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "conf",
   "path"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/8f653c34c0dd46c39e2a5ebf9ff3fe9ec932fc4f/ARVO-42497965/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_8f653c34c0dd.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "mk_rconf_read--mk_rconf_open--flb_parser_conf_file"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf = mk_mem_alloc(MK_RCONF_KV_SIZE)",
     "line": 226
    },
    {
     "code": "buf[--len] = 0",
     "line": 236
    },
    {
     "code": "buf[--len] = 0",
     "line": 238
    }
   ],
   "entity_decl": {
    "line": 183,
    "type": "char*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    175,
    423
   ],
   "func_params": {
    "names": [
     "conf",
     "path"
    ],
    "types": [
     "mk_rconf*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "ret == -1",
     "line": 197
    },
    {
     "code": "errno == ENOENT",
     "line": 197
    },
    {
     "code": "path[0] == '/'",
     "line": 199
    },
    {
     "code": "ret == MK_TRUE",
     "line": 212
    },
    {
     "code": "(f = fopen(cfg_file, \"r\")) == NULL",
     "line": 220
    },
    {
     "code": "buf[len - 1] == '\\n'",
     "line": 235
    },
    {
     "code": "buf[len - 1] == '\\r'",
     "line": 237
    },
    {
     "code": "buf[0] == '#'",
     "line": 262
    },
    {
     "code": "len > 9",
     "line": 266
    },
    {
     "code": "strncasecmp(buf, \"@INCLUDE \", 9) == 0",
     "line": 266
    },
    {
     "code": "strchr(buf + 9, '*') != NULL",
     "line": 267
    },
    {
     "code": "ret == -1",
     "line": 273
    },
    {
     "code": "buf[0] == '@'",
     "line": 284
    },
    {
     "code": "len > 3",
     "line": 284
    },
    {
     "code": "ret == -1",
     "line": 286
    },
    {
     "code": "buf[0] == '['",
     "line": 298
    },
    {
     "code": "end > 0",
     "line": 301
    },
    {
     "code": "n_keys == 0",
     "line": 306
    },
    {
     "code": "i < len",
     "line": 328
    },
    {
     "code": "i == len",
     "line": 334
    },
    {
     "code": "strncmp(buf, indent, indent_len) != 0",
     "line": 340
    },
    {
     "code": "isblank(buf[indent_len]) != 0",
     "line": 341
    },
    {
     "code": "buf[indent_len] == '#'",
     "line": 348
    },
    {
     "code": "indent_len == len",
     "line": 348
    },
    {
     "code": "i < 0",
     "line": 357
    },
    {
     "code": "strlen(val) == 0",
     "line": 368
    },
    {
     "code": "n_keys == 0",
     "line": 385
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "buf[len - 1] == '\\n'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "buf[len - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "len - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "len"
   ],
   "osv_id": "ARVO-42497965",
   "sites": [
    {
     "args": "PATH_MAX",
     "callee": "<operator>.alloc",
     "code": "tmp[PATH_MAX]",
     "line": 184
    },
    {
     "args": "MK_RCONF_KV_SIZE",
     "callee": "mk_mem_alloc",
     "code": "mk_mem_alloc(MK_RCONF_KV_SIZE)",
     "line": 226
    },
    {
     "args": "buf",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(buf)",
     "line": 249
    },
    {
     "args": "indent",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(indent)",
     "line": 277
    },
    {
     "args": "buf",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(buf)",
     "line": 279
    },
    {
     "args": "indent",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(indent)",
     "line": 289
    },
    {
     "args": "buf",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(buf)",
     "line": 291
    },
    {
     "args": "section",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(section)",
     "line": 313
    },
    {
     "args": "buf",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(buf)",
     "line": 319
    },
    {
     "args": "key",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(key)",
     "line": 343
    },
    {
     "args": "val",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(val)",
     "line": 344
    },
    {
     "args": "key",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(key)",
     "line": 359
    },
    {
     "args": "val",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(val)",
     "line": 360
    },
    {
     "args": "key",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(key)",
     "line": 370
    },
    {
     "args": "val",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(val)",
     "line": 371
    },
    {
     "args": "key",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(key)",
     "line": 379
    },
    {
     "args": "val",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(val)",
     "line": 380
    },
    {
     "args": "indent",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(indent)",
     "line": 407
    },
    {
     "args": "buf",
     "callee": "mk_mem_free",
     "code": "mk_mem_free(buf)",
     "line": 409
    },
    {
     "args": "sizeof(struct mk_rconf_file)",
     "callee": "mk_mem_alloc",
     "code": "mk_mem_alloc(sizeof(struct mk_rconf_file))",
     "line": 412
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mk_rconf_read"
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