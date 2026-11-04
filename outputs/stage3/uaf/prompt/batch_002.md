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
heap-use-after-free

## 该类型的机制背景
UAF 的必要条件链：
- N1 对象是堆分配
- N2 存在 free(p) 调用
- N3 p 在 free 之后被解引用（执行顺序）
- N4 free 与解引用之间 p 未被重新赋值
- N5 free 与解引用之间 p 未重新 malloc
- N6 free 的实参是 p 本身（非 p+off）
- N7 解引用对象与 free 对象是同一对象（含别名）
- N8 free 与解引用在同一可达路径上
- N9 p 解引用时未被置空
- N10 解引用发生在 free 生效后（非同一语句）

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "osv_id": "ARVO-42479533",
  "project": "libavc",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "src_r0_16x8b",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 3316,
    "type": "__m128i",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "ih264d_allocate_dynamic_bufs",
    "file": "/src/libavc/decoder/ih264d_utils.c",
    "line": 2101
   },
   "size_expr": null,
   "size_bytes": 602112,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 2252,
    "fn": "ih264d_free_dynamic_bufs",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 3683,
    "fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3",
    "file": "/src/libavc/common/x86/ih264_inter_pred_filters_ssse3.c",
    "line": 3683
   },
   "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)(pu1_src))",
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": 602112
   }
  },
  "context": {
   "fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libavc/address/ea14d495b1995ff09642edfb1b0b45a3d289b0af/ARVO-42479533/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_ea14d495b199.cpg",
   "testcase_size": 122
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 602112,
   "loc_offset": 79533,
   "loc_kind": "region",
   "dedup_token": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3--ih264d_motion_compensate_mp--ih264d_decode_recon_tfr_nmb",
   "region_size": 602112
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)pu1_src)",
     "line": 3330
    },
    {
     "code": "src_r0_16x8b = _mm_unpacklo_epi8(src_r0_16x8b, src_r0_sht_16x8b)",
     "line": 3336
    },
    {
     "code": "src_r0_16x8b = _mm_srli_si128(src_r0_16x8b, 4)",
     "line": 3343
    },
    {
     "code": "src_r0_16x8b = _mm_srli_si128(src_r0_16x8b, 4)",
     "line": 3350
    },
    {
     "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)(pu1_src))",
     "line": 3476
    },
    {
     "code": "src_r0_16x8b = _mm_srli_si128(src_r0_16x8b, 2)",
     "line": 3490
    },
    {
     "code": "src_r0_16x8b = _mm_srli_si128(src_r0_16x8b, 2)",
     "line": 3504
    },
    {
     "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)(pu1_src))",
     "line": 3683
    },
    {
     "code": "src_r0_16x8b = _mm_srli_si128(src_r0_16x8b, 2)",
     "line": 3697
    },
    {
     "code": "src_r0_16x8b = _mm_srli_si128(src_r0_16x8b, 2)",
     "line": 3711
    }
   ],
   "entity_decl": {
    "line": 3316,
    "type": "__m128i"
   },
   "entity_name_cpg": "src_r0_16x8b",
   "func_lines": [
    3288,
    3965
   ],
   "func_params": {
    "names": [],
    "types": [
     "UWORD8*",
     "UWORD8*",
     "WORD32",
     "WORD32",
     "WORD32",
     "WORD32",
     "UWORD8*",
     "WORD32"
    ]
   },
   "guards": [
    {
     "code": "wd == 4",
     "line": 3312
    },
    {
     "code": "ht_temp > 0",
     "line": 3367
    },
    {
     "code": "ht > 0",
     "line": 3452
    },
    {
     "code": "wd == 8",
     "line": 3455
    },
    {
     "code": "ht_temp > 0",
     "line": 3530
    },
    {
     "code": "ht > 0",
     "line": 3651
    },
    {
     "code": "ht_temp > 0",
     "line": 3737
    },
    {
     "code": "ht_temp > 0",
     "line": 3860
    },
    {
     "code": "ht > 0",
     "line": 3962
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)(pu1_src))",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "_mm_loadu_si128((__m128i *)(pu1_src))",
     "name": "_mm_loadu_si128",
     "nargs": 1
    },
    {
     "code": "(__m128i *)(pu1_src)",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "src_r0_16x8b",
    "pu1_src"
   ],
   "osv_id": "ARVO-42479533",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "ih264d_free_dynamic_bufs",
   "use_fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3"
  }
 },
 {
  "osv_id": "ARVO-42479702",
  "project": "openh264",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "LOW_COMPLEXITY",
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
   "size_bytes": 565775,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 113,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 505,
    "fn": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)",
    "file": "/src/openh264/codec/decoder/plus/src/welsDecoderExt.cpp",
    "line": 505
   },
   "code": "LOW_COMPLEXITY = 0",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": 565775
   }
  },
  "context": {
   "fn": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/0152b1ed1505da2ee6f32b9f6e0eff98a3e91800/ARVO-42479702/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_0152b1ed1505.cpg",
   "testcase_size": 22
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 565775,
   "loc_offset": 248825,
   "loc_kind": "region",
   "dedup_token": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned int)",
   "region_size": 565775
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "LOW_COMPLEXITY = 0",
     "line": 505
    }
   ],
   "entity_name_cpg": "LOW_COMPLEXITY",
   "func_lines": [
    504,
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
     "code": "LOW_COMPLEXITY = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "LOW_COMPLEXITY"
   ],
   "osv_id": "ARVO-42479702",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "WelsCommon::WelsFree(void*, char const*)",
   "use_fn": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)"
  }
 },
 {
  "osv_id": "ARVO-42481163",
  "project": "open62541",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "s",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 139,
    "size": null,
    "type": "UA_String*"
   }
  },
  "alloc": {
   "api": "calloc",
   "site": {
    "fn": "UA_memoryManager_calloc",
    "file": "/src/open62541/tests/fuzz/custom_memory_manager.c",
    "line": 142
   },
   "size_expr": null,
   "size_bytes": 32,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 140,
    "fn": "String_clear",
    "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 2994,
    "fn": "Variant_decodeJsonUnwrapExtensionObject",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "String_clear",
    "file": "/src/open62541/src/ua_types.c",
    "line": 140
   },
   "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 32
   }
  },
  "context": {
   "fn": "String_clear",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "UA_String*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "s"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/ac0d94217d06a229c9c671cfa0e37b497114848a/ARVO-42481163/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_ac0d94217d06.cpg",
   "testcase_size": 44
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 32,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "String_clear--LocalizedText_clear--UA_clear",
   "region_size": 32
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 139,
    "type": "UA_String*"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    138,
    141
   ],
   "func_params": {
    "names": [
     "s",
     "_"
    ],
    "types": [
     "UA_String*",
     "UA_DataType*"
    ]
   },
   "guards": [],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_BYTE])",
     "name": "UA_Array_delete",
     "nargs": 3
    },
    {
     "code": "s->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "s->length",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "&UA_TYPES[UA_TYPES_BYTE]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "UA_TYPES[UA_TYPES_BYTE]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "s",
    "UA_TYPES",
    "UA_TYPES_BYTE"
   ],
   "osv_id": "ARVO-42481163",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "Variant_decodeJsonUnwrapExtensionObject",
   "use_fn": "String_clear"
  }
 },
 {
  "osv_id": "ARVO-42481640",
  "project": "openh264",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
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
   "size_bytes": 539,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 113,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 426,
    "fn": "WelsDec::WelsReorderRefList(WelsDec::TagWelsDecoderContext*)",
    "code": "{{CTX_NA, CTX_NA}, {0, 58}, {1, 56}, {1, 63}} | {CTX_NA, CTX_NA} | CTX_NA | CTX_NA",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::WelsReorderRefList(WelsDec::TagWelsDecoderContext*)",
    "file": "/src/openh264/codec/decoder/core/src/manage_dec_ref.cpp",
    "line": 426
   },
   "code": "{{CTX_NA, CTX_NA}, {0, 58}, {1, 56}, {1, 63}} | {CTX_NA, CTX_NA} | CTX_NA | CTX_NA",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 539
   }
  },
  "context": {
   "fn": "<global>",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/4b41984f86d6e46f8e92af17a3515151aa282976/ARVO-42481640/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_4b41984f86d6.cpg",
   "testcase_size": 54
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 539,
   "loc_offset": 124,
   "loc_kind": "region",
   "dedup_token": "WelsDec::WelsReorderRefList(WelsDec::TagWelsDecoderContext*)--WelsDec::InitRefPicList(WelsDec::TagWelsDecoderContext*, unsigned char, int)--WelsDec::DecodeCurre",
   "region_size": 539
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    1,
    906
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "{{CTX_NA, CTX_NA}, {0, 58}, {1, 56}, {1, 63}}",
     "name": "<operator>.arrayInitializer",
     "nargs": 4
    },
    {
     "code": "{CTX_NA, CTX_NA}",
     "name": "<operator>.arrayInitializer",
     "nargs": 2
    },
    {
     "code": "CTX_NA",
     "name": "CTX_NA",
     "nargs": 0
    },
    {
     "code": "CTX_NA",
     "name": "CTX_NA",
     "nargs": 0
    },
    {
     "code": "{0, 58}",
     "name": "<operator>.arrayInitializer",
     "nargs": 2
    },
    {
     "code": "{1, 56}",
     "name": "<operator>.arrayInitializer",
     "nargs": 2
    },
    {
     "code": "{1, 63}",
     "name": "<operator>.arrayInitializer",
     "nargs": 2
    }
   ],
   "line_ids": [],
   "osv_id": "ARVO-42481640",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "WelsCommon::WelsFree(void*, char const*)",
   "use_fn": "WelsDec::WelsReorderRefList(WelsDec::TagWelsDecoderContext*)"
  }
 },
 {
  "osv_id": "ARVO-42482031",
  "project": "libvips",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "g_realloc (/out/jpegsave_file_fuzzer+0xe3ec97)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": 16,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 239,
    "fn": "vips_foreign_load_matrix_load",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 418,
    "fn": "vips_buf_vappendf",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vips_buf_vappendf",
    "file": "/src/libvips/libvips/iofuncs/buf.c",
    "line": 418
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": 16
   }
  },
  "context": {
   "fn": "vips_buf_vappendf",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42482031/report.log",
   "cpg": null,
   "testcase_size": 27
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 16,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--vips_buf_vappendf--vips_verror",
   "region_size": 16
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "vips_foreign_load_matrix_load",
   "use_fn": "vips_buf_vappendf"
  }
 },
 {
  "osv_id": "ARVO-42483214",
  "project": "perfetto",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "comment_till_eol",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/perfetto/src/trace_processor/importers/common/track_tracker.cc",
    "line": 474,
    "size": null,
    "type": "bool"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "file": "/work/build/../../src/perfetto/src/trace_processor/importers/common/track_tracker.cc",
    "line": 339
   },
   "size_expr": null,
   "size_bytes": 24,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "free",
    "line": 365,
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 485,
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "code": "comment_till_eol = false",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "file": "/src/perfetto/src/trace_processor/importers/common/track_tracker.cc",
    "line": 485
   },
   "code": "comment_till_eol = false",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 24
   }
  },
  "context": {
   "fn": "Parse",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:478,IF:481,IF:484,CONTINUE:486,IF:489,CONTINUE:490,SWITCH:492,IF:494,CONTINUE:495,IF:496,CONTINUE:498,IF:500"
  },
  "call_chain": [],
  "types": {
   "entity_type": "bool",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/perfetto/address/8a1fbea36994a227c79d36a3ce3a7be7a241fca0/ARVO-42483214/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_8a1fbea36994.cpg",
   "testcase_size": 113
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 24,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >::begin()--perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, pe",
   "region_size": 24
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "comment_till_eol = false",
     "line": 474
    },
    {
     "code": "comment_till_eol = false",
     "line": 485
    },
    {
     "code": "comment_till_eol = true",
     "line": 497
    },
    {
     "code": "comment_till_eol = true",
     "line": 530
    },
    {
     "code": "comment_till_eol = true",
     "line": 537
    },
    {
     "code": "comment_till_eol = c == '#'",
     "line": 606
    }
   ],
   "entity_decl": {
    "line": 474,
    "type": "bool"
   },
   "entity_name_cpg": "comment_till_eol",
   "func_lines": [
    467,
    624
   ],
   "func_params": {
    "names": [
     "input",
     "delegate"
    ],
    "types": [
     "std.string&",
     "ParserDelegate*"
    ]
   },
   "guards": [
    {
     "code": "i < input.size()",
     "line": 478
    },
    {
     "code": "i + 1 == input.size()",
     "line": 479
    },
    {
     "code": "c == '\\n'",
     "line": 481
    },
    {
     "code": "c == '#'",
     "line": 496
    },
    {
     "code": "c == '}'",
     "line": 500
    },
    {
     "code": "depth == 0",
     "line": 501
    },
    {
     "code": "c == ';'",
     "line": 510
    },
    {
     "code": "c == '#'",
     "line": 529
    },
    {
     "code": "c == '#'",
     "line": 536
    },
    {
     "code": "c == ':'",
     "line": 544
    },
    {
     "code": "c == '\"'",
     "line": 548
    },
    {
     "code": "c == '-'",
     "line": 552
    },
    {
     "code": "c == '{'",
     "line": 560
    },
    {
     "code": "c == ';'",
     "line": 570
    },
    {
     "code": "c == ';'",
     "line": 571
    },
    {
     "code": "c == ';'",
     "line": 574
    },
    {
     "code": "c == '\\\\'",
     "line": 584
    },
    {
     "code": "c == '\"'",
     "line": 586
    },
    {
     "code": "c == ';'",
     "line": 601
    },
    {
     "code": "c == '#'",
     "line": 601
    },
    {
     "code": "c == ';'",
     "line": 603
    },
    {
     "code": "c == '#'",
     "line": 603
    },
    {
     "code": "c == '#'",
     "line": 606
    },
    {
     "code": "c == ';'",
     "line": 607
    },
    {
     "code": "depth > 0",
     "line": 619
    },
    {
     "code": "state != kWaitingForKey",
     "line": 621
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "comment_till_eol = false",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "comment_till_eol"
   ],
   "osv_id": "ARVO-42483214",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": false,
   "free_fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
   "use_fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)"
  }
 },
 {
  "osv_id": "ARVO-42483440",
  "project": "leptonica",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cmap",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/colormap.c",
    "line": 280,
    "size": null,
    "type": "PIXCMAP*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pixcmapCreate",
    "file": "/src/leptonica/src/colormap.c",
    "line": 134
   },
   "size_expr": null,
   "size_bytes": 24,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 292,
    "fn": "pixcmapDestroy",
    "code": "LEPT_FREE(cmap->array) | cmap->array | free(cmap->array) | cmap->array",
    "origin": "report:crash",
    "args": "cmap->array"
   },
   {
    "kind": "free",
    "line": 293,
    "fn": "pixcmapDestroy",
    "code": "LEPT_FREE(cmap)",
    "origin": "report:freed_by",
    "args": "cmap"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixcmapDestroy",
    "file": "/src/leptonica/src/colormap.c",
    "line": 292
   },
   "code": "LEPT_FREE(cmap->array) | cmap->array | free(cmap->array) | cmap->array",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 24
   }
  },
  "context": {
   "fn": "pixcmapDestroy",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:284,IF:289"
  },
  "call_chain": [],
  "types": {
   "entity_type": "PIXCMAP*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/leptonica/address/695ff35cab05b6e7f80da48118a2b8fbe76d74e3/ARVO-42483440/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_695ff35cab05.cpg",
   "testcase_size": 44
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "free_related": {
   "free_sites_in_func": [
    292,
    293
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 24,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "pixcmapDestroy--LLVMFuzzerTestOneInput--ExecuteFilesOnyByOne",
   "region_size": 24
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cmap = *pcmap",
     "line": 289
    }
   ],
   "entity_decl": {
    "line": 280,
    "type": "PIXCMAP*"
   },
   "entity_name_cpg": "cmap",
   "func_lines": [
    277,
    295
   ],
   "func_params": {
    "names": [
     "pcmap"
    ],
    "types": [
     "PIXCMAP**"
    ]
   },
   "guards": [
    {
     "code": "pcmap == NULL",
     "line": 284
    },
    {
     "code": "(cmap = *pcmap) == NULL",
     "line": 289
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "LEPT_FREE(cmap->array)",
     "name": "LEPT_FREE",
     "nargs": 1
    },
    {
     "code": "cmap->array",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "free(cmap->array)",
     "name": "free",
     "nargs": 1
    },
    {
     "code": "cmap->array",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cmap"
   ],
   "osv_id": "ARVO-42483440",
   "sites": [
    {
     "args": "cmap->array",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(cmap->array)",
     "line": 292
    },
    {
     "args": "cmap->array",
     "callee": "free",
     "code": "free(cmap->array)",
     "line": 292
    },
    {
     "args": "cmap",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(cmap)",
     "line": 293
    },
    {
     "args": "cmap",
     "callee": "free",
     "code": "free(cmap)",
     "line": 293
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": false,
   "free_fn": "pixcmapDestroy",
   "use_fn": "pixcmapDestroy"
  }
 },
 {
  "osv_id": "ARVO-42484161",
  "project": "leptonica",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "val",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/readbarcode.c",
    "line": 777,
    "size": null,
    "type": "l_int32"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pixCreateNoInit",
    "file": "/src/leptonica/src/pix1.c",
    "line": 345
   },
   "size_expr": null,
   "size_bytes": 2432,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 634,
    "fn": "pixFree",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 805,
    "fn": "pixAverageRasterScans",
    "code": "val = GET_DATA_BYTE(line, j) | GET_DATA_BYTE(line, j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j) | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j))",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixAverageRasterScans",
    "file": "/src/leptonica/src/readbarcode.c",
    "line": 805
   },
   "code": "val = GET_DATA_BYTE(line, j) | GET_DATA_BYTE(line, j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j) | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j))",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 2432
   }
  },
  "context": {
   "fn": "pixAverageRasterScans",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j < w",
   "guard_count": 1,
   "control_structures": "IF:784,IF:788,ELSE:792,FOR:802,FOR:803"
  },
  "call_chain": [],
  "types": {
   "entity_type": "l_int32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "pixs",
   "nscans"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/leptonica/address/f6f7c9c4737e554b724ac8b5091698df67b570cb/ARVO-42484161/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_f6f7c9c4737e.cpg",
   "testcase_size": 412
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 2432,
   "loc_offset": 1879,
   "loc_kind": "region",
   "dedup_token": "pixAverageRasterScans--pixExtractBarcodeCrossings--pixExtractBarcodeWidths1",
   "region_size": 2432
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "val = GET_DATA_BYTE(line, j)",
     "line": 805
    }
   ],
   "entity_decl": {
    "line": 777,
    "type": "l_int32"
   },
   "entity_name_cpg": "val",
   "func_lines": [
    773,
    812
   ],
   "func_params": {
    "names": [
     "pixs",
     "nscans"
    ],
    "types": [
     "PIX*",
     "l_int32"
    ]
   },
   "guards": [
    {
     "code": "pixGetDepth(pixs) != 8",
     "line": 784
    },
    {
     "code": "j < w",
     "line": 802
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "val = GET_DATA_BYTE(line, j)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "GET_DATA_BYTE(line, j)",
     "name": "GET_DATA_BYTE",
     "nargs": 2
    },
    {
     "code": "*(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j)) ^ 3)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j)) ^ 3)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(l_uintptr_t)((const l_uint8 *)(line) + (j)) ^ 3",
     "name": "<operator>.xor",
     "nargs": 2
    },
    {
     "code": "(l_uintptr_t)((const l_uint8 *)(line) + (j))",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(const l_uint8 *)(line) + (j)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(const l_uint8 *)(line)",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "val",
    "line",
    "j"
   ],
   "osv_id": "ARVO-42484161",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "pixFree",
   "use_fn": "pixAverageRasterScans"
  }
 },
 {
  "osv_id": "ARVO-42484314",
  "project": "ndpi",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 99,
    "size": null,
    "type": "ndpi_packet_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 81
   },
   "size_expr": null,
   "size_bytes": 25421,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 84,
    "fn": "LLVMFuzzerTestOneInput",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 144,
    "fn": "ndpi_http_check_content",
    "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_http_check_content",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 144
   },
   "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 25421
   }
  },
  "context": {
   "fn": "ndpi_http_check_content",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "packet->content_disposition_line.len > attachment_len",
   "guard_count": 1,
   "control_structures": "IF:101,IF:104,IF:108,ELSE:111,IF:111,SWITCH:114,BREAK:115,BREAK:116,BREAK:117,IF:120,FOR:121,IF:122"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/ndpi/address/b6eef17e54999586b6aef8f545c87de4d3ec0ab3/ARVO-42484314/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_b6eef17e5499.cpg",
   "testcase_size": 51731
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 25421,
   "loc_offset": 6643,
   "loc_kind": "region",
   "dedup_token": "strncmp--ndpi_http_check_content--ndpi_int_http_add_connection",
   "region_size": 25421
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 99
    }
   ],
   "entity_decl": {
    "line": 99,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    97,
    172
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
     "code": "packet->content_line.len > 0",
     "line": 101
    },
    {
     "code": "packet->content_line.len > app_len",
     "line": 104
    },
    {
     "code": "ndpi_strncasestr(app, \"mpeg\", app_len_avail) != NULL",
     "line": 108
    },
    {
     "code": "app_len_avail > 1",
     "line": 111
    },
    {
     "code": "cmp_mimes[i] != NULL",
     "line": 121
    },
    {
     "code": "ndpi_strncasestr(app, cmp_mimes[i], app_len_avail) != NULL",
     "line": 122
    },
    {
     "code": "packet->content_disposition_line.len > 0",
     "line": 134
    },
    {
     "code": "packet->content_disposition_line.len > attachment_len",
     "line": 137
    },
    {
     "code": "filename_len > ATTACHMENT_LEN",
     "line": 140
    },
    {
     "code": "binary_file_ext[i] != NULL",
     "line": 143
    },
    {
     "code": "strncmp((const char*)&packet->content_disposition_line.ptr[attachment_len],",
     "line": 144
    },
    {
     "code": "strncasecmp((const char *)packet->content_line.ptr, \"audio\",",
     "line": 158
    },
    {
     "code": "strncasecmp((const char *)packet->content_line.ptr, \"video\",",
     "line": 164
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "strncmp((const char*)&packet->content_disposition_line.ptr[attachment_len],",
     "name": "<operator>.equals",
     "nargs": null
    },
    {
     "code": "strncmp((const char*)&packet->content_disposition_line.ptr[attachment_len],",
     "name": "strncmp",
     "nargs": null
    },
    {
     "code": "(const char*)&packet->content_disposition_line.ptr[attachment_len]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "&packet->content_disposition_line.ptr[attachment_len]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "packet->content_disposition_line.ptr[attachment_len]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->content_disposition_line.ptr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->content_disposition_line",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet",
    "attachment_len"
   ],
   "osv_id": "ARVO-42484314",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "LLVMFuzzerTestOneInput",
   "use_fn": "ndpi_http_check_content"
  }
 },
 {
  "osv_id": "ARVO-42484479",
  "project": "ndpi",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 99,
    "size": null,
    "type": "ndpi_packet_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 81
   },
   "size_expr": null,
   "size_bytes": 25443,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 84,
    "fn": "LLVMFuzzerTestOneInput",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 144,
    "fn": "ndpi_http_check_content",
    "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_http_check_content",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 144
   },
   "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 25443
   }
  },
  "context": {
   "fn": "ndpi_http_check_content",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "packet->content_disposition_line.len > attachment_len",
   "guard_count": 1,
   "control_structures": "IF:101,IF:104,IF:108,ELSE:111,IF:111,SWITCH:114,BREAK:115,BREAK:116,BREAK:117,IF:120,FOR:121,IF:122"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/ndpi/address/b6eef17e54999586b6aef8f545c87de4d3ec0ab3/ARVO-42484479/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_b6eef17e5499.cpg",
   "testcase_size": 52086
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 25443,
   "loc_offset": 18842,
   "loc_kind": "region",
   "dedup_token": "strncmp--ndpi_http_check_content--ndpi_int_http_add_connection",
   "region_size": 25443
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 99
    }
   ],
   "entity_decl": {
    "line": 99,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    97,
    172
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
     "code": "packet->content_line.len > 0",
     "line": 101
    },
    {
     "code": "packet->content_line.len > app_len",
     "line": 104
    },
    {
     "code": "ndpi_strncasestr(app, \"mpeg\", app_len_avail) != NULL",
     "line": 108
    },
    {
     "code": "app_len_avail > 1",
     "line": 111
    },
    {
     "code": "cmp_mimes[i] != NULL",
     "line": 121
    },
    {
     "code": "ndpi_strncasestr(app, cmp_mimes[i], app_len_avail) != NULL",
     "line": 122
    },
    {
     "code": "packet->content_disposition_line.len > 0",
     "line": 134
    },
    {
     "code": "packet->content_disposition_line.len > attachment_len",
     "line": 137
    },
    {
     "code": "filename_len > ATTACHMENT_LEN",
     "line": 140
    },
    {
     "code": "binary_file_ext[i] != NULL",
     "line": 143
    },
    {
     "code": "strncmp((const char*)&packet->content_disposition_line.ptr[attachment_len],",
     "line": 144
    },
    {
     "code": "strncasecmp((const char *)packet->content_line.ptr, \"audio\",",
     "line": 158
    },
    {
     "code": "strncasecmp((const char *)packet->content_line.ptr, \"video\",",
     "line": 164
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "strncmp((const char*)&packet->content_disposition_line.ptr[attachment_len],",
     "name": "<operator>.equals",
     "nargs": null
    },
    {
     "code": "strncmp((const char*)&packet->content_disposition_line.ptr[attachment_len],",
     "name": "strncmp",
     "nargs": null
    },
    {
     "code": "(const char*)&packet->content_disposition_line.ptr[attachment_len]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "&packet->content_disposition_line.ptr[attachment_len]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "packet->content_disposition_line.ptr[attachment_len]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->content_disposition_line.ptr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->content_disposition_line",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet",
    "attachment_len"
   ],
   "osv_id": "ARVO-42484479",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "LLVMFuzzerTestOneInput",
   "use_fn": "ndpi_http_check_content"
  }
 },
 {
  "osv_id": "ARVO-42484562",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "msg",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/error.c",
    "line": 460,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "strndup",
   "site": {
    "fn": "xmlStrndup",
    "file": "/src/libxml2/xmlstring.c",
    "line": 45
   },
   "size_expr": null,
   "size_bytes": 4,
   "cross_function": true,
   "size_expr_cpg": "150",
   "size_expr_cpg_callee": "xmlMalloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 311,
    "fn": "xmlTextReaderFreeProp",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 501,
    "fn": "__xmlRaiseError",
    "code": "XML_GET_VAR_STR(msg, str) | int | -1 | str = (char *)xmlMalloc(150)",
    "origin": "report:crash",
    "args": "150"
   }
  ],
  "crash": {
   "site": {
    "fn": "__xmlRaiseError",
    "file": "/src/libxml2/error.c",
    "line": 501
   },
   "code": "XML_GET_VAR_STR(msg, str) | int | -1 | str = (char *)xmlMalloc(150)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": 4
   }
  },
  "context": {
   "fn": "__xmlRaiseError",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "schannel == NULL | ctxt != NULL | ctxt->sax != NULL",
   "guard_count": 45,
   "control_structures": "IF:469,IF:471,IF:473,IF:477,IF:487,IF:492,IF:498,ELSE:500,IF:501,WHILE:501,IF:501,IF:501"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "schannel",
   "ctx",
   "nod",
   "file",
   "str1",
   "str2",
   "str3",
   "msg"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/00ed736eecf93aeab49089abb06e0e5fc0e7e091/ARVO-42484562/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_00ed736eecf9.cpg",
   "testcase_size": 523
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 4,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--__xmlRaiseError--xmlErrValidNode",
   "region_size": 4
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 460,
    "type": "char*"
   },
   "entity_name_cpg": "msg",
   "func_lines": [
    455,
    639
   ],
   "func_params": {
    "names": [
     "schannel",
     "channel",
     "data",
     "ctx",
     "nod",
     "domain",
     "code",
     "level",
     "file",
     "line",
     "str1",
     "str2",
     "str3",
     "int1",
     "col",
     "msg"
    ],
    "types": [
     "xmlStructuredErrorFunc",
     "xmlGenericErrorFunc",
     "void*",
     "void*",
     "void*",
     "int",
     "int",
     "xmlErrorLevel",
     "char*",
     "int",
     "char*",
     "char*",
     "char*",
     "int",
     "int",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "code == XML_ERR_OK",
     "line": 469
    },
    {
     "code": "xmlGetWarningsDefaultValue == 0",
     "line": 471
    },
    {
     "code": "level == XML_ERR_WARNING",
     "line": 471
    },
    {
     "code": "domain == XML_FROM_PARSER",
     "line": 473
    },
    {
     "code": "domain == XML_FROM_HTML",
     "line": 473
    },
    {
     "code": "domain == XML_FROM_DTD",
     "line": 474
    },
    {
     "code": "domain == XML_FROM_NAMESPACE",
     "line": 474
    },
    {
     "code": "domain == XML_FROM_IO",
     "line": 475
    },
    {
     "code": "domain == XML_FROM_VALID",
     "line": 475
    },
    {
     "code": "schannel == NULL",
     "line": 477
    },
    {
     "code": "ctxt != NULL",
     "line": 477
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 477
    },
    {
     "code": "ctxt->sax->initialized == XML_SAX2_MAGIC",
     "line": 478
    },
    {
     "code": "ctxt->sax->serror != NULL",
     "line": 479
    },
    {
     "code": "schannel == NULL",
     "line": 487
    },
    {
     "code": "schannel != NULL",
     "line": 492
    },
    {
     "code": "msg == NULL",
     "line": 498
    },
    {
     "code": "str != NULL",
     "line": 501
    },
    {
     "code": "size < 64000",
     "line": 501
    },
    {
     "code": "chars > -1",
     "line": 501
    },
    {
     "code": "chars < size",
     "line": 501
    },
    {
     "code": "prev_size == chars",
     "line": 501
    },
    {
     "code": "chars > -1",
     "line": 501
    },
    {
     "code": "(larger = (char *)xmlRealloc(str, size)) == NULL",
     "line": 501
    },
    {
     "code": "ctxt != NULL",
     "line": 507
    },
    {
     "code": "file == NULL",
     "line": 508
    },
    {
     "code": "input != NULL",
     "line": 510
    },
    {
     "code": "input->filename == NULL",
     "line": 510
    },
    {
     "code": "ctxt->inputNr > 1",
     "line": 511
    },
    {
     "code": "input != NULL",
     "line": 514
    },
    {
     "code": "node != NULL",
     "line": 521
    },
    {
     "code": "file == NULL",
     "line": 521
    },
    {
     "code": "node->doc != NULL",
     "line": 524
    },
    {
     "code": "node->doc->URL != NULL",
     "line": 524
    },
    {
     "code": "i < 10",
     "line": 529
    },
    {
     "code": "node != NULL",
     "line": 529
    },
    {
     "code": "node->type != XML_ELEMENT_NODE",
     "line": 529
    },
    {
     "code": "baseptr == NULL",
     "line": 532
    },
    {
     "code": "node != NULL",
     "line": 532
    },
    {
     "code": "node->doc != NULL",
     "line": 533
    },
    {
     "code": "node->doc->URL != NULL",
     "line": 533
    },
    {
     "code": "node != NULL",
     "line": 536
    },
    {
     "code": "node->type == XML_ELEMENT_NODE",
     "line": 536
    },
    {
     "code": "line == 0",
     "line": 538
    },
    {
     "code": "line == 65535",
     "line": 538
    },
    {
     "code": "file != NULL",
     "line": 550
    },
    {
     "code": "baseptr != NULL",
     "line": 552
    },
    {
     "code": "to->file == NULL",
     "line": 584
    },
    {
     "code": "node != NULL",
     "line": 584
    },
    {
     "code": "node->doc != NULL",
     "line": 584
    },
    {
     "code": "str1 != NULL",
     "line": 589
    },
    {
     "code": "str2 != NULL",
     "line": 591
    },
    {
     "code": "str3 != NULL",
     "line": 593
    },
    {
     "code": "to != &xmlLastError",
     "line": 600
    },
    {
     "code": "schannel != NULL",
     "line": 603
    },
    {
     "code": "ctxt != NULL",
     "line": 611
    },
    {
     "code": "channel == NULL",
     "line": 611
    },
    {
     "code": "xmlStructuredError == NULL",
     "line": 612
    },
    {
     "code": "ctxt->sax != NULL",
     "line": 612
    },
    {
     "code": "level == XML_ERR_WARNING",
     "line": 613
    },
    {
     "code": "channel == NULL",
     "line": 618
    },
    {
     "code": "ctxt != NULL",
     "line": 620
    },
    {
     "code": "channel == NULL",
     "line": 626
    },
    {
     "code": "channel == xmlParserError",
     "line": 629
    },
    {
     "code": "channel == xmlParserWarning",
     "line": 630
    },
    {
     "code": "channel == xmlParserValidityError",
     "line": 631
    },
    {
     "code": "channel == xmlParserValidityWarning",
     "line": 632
    },
    {
     "code": "(void(*)(void)) channel == (void(*)(void)) fprintf",
     "line": 634
    },
    {
     "code": "channel == xmlGenericErrorDefaultFunc",
     "line": 635
    }
   ],
   "line_call_count": 29,
   "line_calls": [
    {
     "code": "XML_GET_VAR_STR(msg, str)",
     "name": "XML_GET_VAR_STR",
     "nargs": 2
    },
    {
     "code": "int",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "-1",
     "name": "<operator>.minus",
     "nargs": 1
    },
    {
     "code": "str = (char *)xmlMalloc(150)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(char *)xmlMalloc(150)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "xmlMalloc(150)",
     "name": "xmlMalloc",
     "nargs": 1
    },
    {
     "code": "str != NULL",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "size = 150",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "size < 64000",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "va_start(ap, msg)",
     "name": "va_start",
     "nargs": 2
    },
    {
     "code": "chars = vsnprintf(str, size, msg, ap)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "vsnprintf(str, size, msg, ap)",
     "name": "vsnprintf",
     "nargs": 4
    },
    {
     "code": "va_end(ap)",
     "name": "va_end",
     "nargs": 1
    },
    {
     "code": "(chars > -1) && (chars < size)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "chars > -1",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "-1",
     "name": "<operator>.minus",
     "nargs": 1
    },
    {
     "code": "chars < size",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "prev_size == chars",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "prev_size = chars",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "chars > -1",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "-1",
     "name": "<operator>.minus",
     "nargs": 1
    },
    {
     "code": "size += chars + 1",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "chars + 1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "size += 100",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "(larger = (char *)xmlRealloc(str, size)) == NULL",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "larger = (char *)xmlRealloc(str, size)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(char *)xmlRealloc(str, size)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "xmlRealloc(str, size)",
     "name": "xmlRealloc",
     "nargs": 2
    },
    {
     "code": "str = larger",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "msg",
    "str",
    "prev_size",
    "NULL",
    "size",
    "ap",
    "chars",
    "larger"
   ],
   "osv_id": "ARVO-42484562",
   "sites": [
    {
     "args": "150",
     "callee": "xmlMalloc",
     "code": "xmlMalloc(150)",
     "line": 501
    },
    {
     "args": "str ;; size",
     "callee": "xmlRealloc",
     "code": "xmlRealloc(str, size)",
     "line": 501
    },
    {
     "args": "(const xmlChar *) file",
     "callee": "xmlStrdup",
     "code": "xmlStrdup((const xmlChar *) file)",
     "line": 551
    },
    {
     "args": "baseptr->doc->URL",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(baseptr->doc->URL)",
     "line": 583
    },
    {
     "args": "node->doc->URL",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(node->doc->URL)",
     "line": 585
    },
    {
     "args": "(const xmlChar *) str1",
     "callee": "xmlStrdup",
     "code": "xmlStrdup((const xmlChar *) str1)",
     "line": 590
    },
    {
     "args": "(const xmlChar *) str2",
     "callee": "xmlStrdup",
     "code": "xmlStrdup((const xmlChar *) str2)",
     "line": 592
    },
    {
     "args": "(const xmlChar *) str3",
     "callee": "xmlStrdup",
     "code": "xmlStrdup((const xmlChar *) str3)",
     "line": 594
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xmlTextReaderFreeProp",
   "use_fn": "__xmlRaiseError"
  }
 },
 {
  "osv_id": "ARVO-42485194",
  "project": "ndpi",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 178,
    "size": null,
    "type": "ndpi_flow_struct*"
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
   "size_bytes": 25443,
   "cross_function": true,
   "size_expr_cpg": "len",
   "size_expr_cpg_callee": "ndpi_malloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 83,
    "fn": "LLVMFuzzerTestOneInput",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 342,
    "fn": "check_content_type_and_change_protocol",
    "code": "strncpy((char*)flow->protos.http.nat_ip, (char*)packet-> | (char*)flow->protos.http.nat_ip | flow->protos.http.nat_ip | flow->protos.http",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "check_content_type_and_change_protocol",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 342
   },
   "code": "strncpy((char*)flow->protos.http.nat_ip, (char*)packet-> | (char*)flow->protos.http.nat_ip | flow->protos.http.nat_ip | flow->protos.http",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": 25443
   }
  },
  "context": {
   "fn": "check_content_type_and_change_protocol",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:183,IF:207,IF:213,IF:220,ELSE:222,SWITCH:223,BREAK:224,BREAK:225,BREAK:226,SWITCH:229,BREAK:230,BREAK:231"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_flow_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/ndpi/address/812505b56bb4508bc42e1615d6425ad26444d3f8/ARVO-42485194/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_812505b56bb4.cpg",
   "testcase_size": 51829
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 25443,
   "loc_offset": 8415,
   "loc_kind": "region",
   "dedup_token": "strncpy--check_content_type_and_change_protocol--ndpi_check_http_tcp",
   "region_size": 25443
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->http.url = ndpi_malloc(len)",
     "line": 212
    },
    {
     "code": "flow->http.url[len-1] = '\\0'",
     "line": 217
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_UNKNOWN",
     "line": 221
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_OPTIONS",
     "line": 224
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_GET",
     "line": 225
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_HEAD",
     "line": 226
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_PATCH",
     "line": 230
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_POST",
     "line": 231
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_PUT",
     "line": 232
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_DELETE",
     "line": 236
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_TRACE",
     "line": 237
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_CONNECT",
     "line": 238
    },
    {
     "code": "flow->http.method = NDPI_HTTP_METHOD_UNKNOWN",
     "line": 240
    },
    {
     "code": "flow->http.user_agent = ndpi_malloc(len)",
     "line": 313
    },
    {
     "code": "flow->http.user_agent[packet->user_agent_line.len] = '\\0'",
     "line": 317
    },
    {
     "code": "flow->host_server_name[len] = '\\0'",
     "line": 335
    },
    {
     "code": "flow->extra_packets_func = NULL",
     "line": 336
    },
    {
     "code": "flow->server_id = flow->dst",
     "line": 338
    },
    {
     "code": "flow->protos.http.nat_ip[len] = '\\0'",
     "line": 343
    },
    {
     "code": "flow->detected_protocol_stack[1] = flow->guessed_protocol_id",
     "line": 357
    },
    {
     "code": "flow->detected_protocol_stack[0] = flow->guessed_host_protocol_id",
     "line": 359
    },
    {
     "code": "flow->guessed_protocol_id = flow->detected_protocol_stack[1]",
     "line": 364
    },
    {
     "code": "flow->guessed_host_protocol_id = flow->detected_protocol_stack[0]",
     "line": 366
    },
    {
     "code": "flow->guessed_protocol_id = NDPI_PROTOCOL_HTTP",
     "line": 397
    },
    {
     "code": "flow->http.content_type = ndpi_malloc(len)",
     "line": 416
    },
    {
     "code": "flow->http.content_type[packet->content_line.len] = '\\0'",
     "line": 420
    }
   ],
   "entity_decl": {
    "line": 178,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    177,
    434
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
     "code": "flow->http.response_status_code != 0",
     "line": 183
    },
    {
     "code": "flow->http.url == NULL",
     "line": 207
    },
    {
     "code": "packet->http_url_name.len > 0",
     "line": 208
    },
    {
     "code": "packet->host_line.len > 0",
     "line": 209
    },
    {
     "code": "flow->packet.http_method.len < 3",
     "line": 220
    },
    {
     "code": "packet->user_agent_line.ptr != NULL",
     "line": 246
    },
    {
     "code": "packet->user_agent_line.len != 0",
     "line": 246
    },
    {
     "code": "packet->user_agent_line.len > 7",
     "line": 252
    },
    {
     "code": "strncmp(ua, \"Mozilla\", 7) == 0",
     "line": 259
    },
    {
     "code": "strcmp(token, \"X11\") == 0",
     "line": 271
    },
    {
     "code": "strcmp(token, \"compatible\") == 0",
     "line": 272
    },
    {
     "code": "strcmp(token, \"Linux\") == 0",
     "line": 273
    },
    {
     "code": "strcmp(token, \"Macintosh\") == 0",
     "line": 274
    },
    {
     "code": "token[0] == ' '",
     "line": 277
    },
    {
     "code": "strcmp(token, \"U\") == 0",
     "line": 280
    },
    {
     "code": "strncmp(token, \"MSIE\", 4) == 0",
     "line": 281
    },
    {
     "code": "token[0] == ' '",
     "line": 283
    },
    {
     "code": "strncmp(token, \"Update\", 6)  == 0",
     "line": 285
    },
    {
     "code": "token[0] == ' '",
     "line": 288
    },
    {
     "code": "strncmp(token, \"AOL\", 3)  == 0",
     "line": 290
    },
    {
     "code": "token[0] == ' '",
     "line": 293
    },
    {
     "code": "memcmp(ua, \"netflix-ios-app\", 15) == 0",
     "line": 303
    },
    {
     "code": "flow->http.user_agent == NULL",
     "line": 310
    },
    {
     "code": "packet->host_line.ptr != NULL",
     "line": 326
    },
    {
     "code": "flow->detected_protocol_stack[1] == NDPI_PROTOCOL_UNKNOWN",
     "line": 354
    },
    {
     "code": "ndpi_struct->proto_defaults[flow->guessed_protocol_id].can_have_a_subprotocol == 0",
     "line": 356
    },
    {
     "code": "flow->detected_protocol_stack[0] == NDPI_PROTOCOL_UNKNOWN",
     "line": 358
    },
    {
     "code": "flow->detected_protocol_stack[1] != flow->guessed_protocol_id",
     "line": 363
    },
    {
     "code": "flow->detected_protocol_stack[0] != flow->guessed_host_protocol_id",
     "line": 365
    },
    {
     "code": "flow->detected_protocol_stack[0] == NDPI_PROTOCOL_UNKNOWN",
     "line": 369
    },
    {
     "code": "packet->http_origin.len > 0",
     "line": 371
    },
    {
     "code": "flow->detected_protocol_stack[0] != NDPI_PROTOCOL_UNKNOWN",
     "line": 381
    },
    {
     "code": "packet->detected_protocol_stack[0] != NDPI_PROTOCOL_HTTP",
     "line": 382
    },
    {
     "code": "flow->guessed_protocol_id == NDPI_PROTOCOL_UNKNOWN",
     "line": 396
    },
    {
     "code": "packet->accept_line.ptr != NULL",
     "line": 400
    },
    {
     "code": "NDPI_COMPARE_PROTOCOL_TO_BITMASK(ndpi_struct->detection_bitmask,",
     "line": 403
    },
    {
     "code": "packet->content_line.ptr != NULL",
     "line": 409
    },
    {
     "code": "packet->content_line.len != 0",
     "line": 409
    },
    {
     "code": "flow->http.content_type == NULL",
     "line": 413
    },
    {
     "code": "packet->content_line.len > 0",
     "line": 413
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "strncpy((char*)flow->protos.http.nat_ip, (char*)packet->forwarded_line.ptr, len)",
     "name": "strncpy",
     "nargs": 3
    },
    {
     "code": "(char*)flow->protos.http.nat_ip",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "flow->protos.http.nat_ip",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->protos.http",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->protos",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(char*)packet->forwarded_line.ptr",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "packet->forwarded_line.ptr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->forwarded_line",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "flow",
    "packet",
    "len"
   ],
   "osv_id": "ARVO-42485194",
   "sites": [
    {
     "args": "len",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(len)",
     "line": 212
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "ua[256]",
     "line": 253
    },
    {
     "args": "len",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(len)",
     "line": 313
    },
    {
     "args": "len",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(len)",
     "line": 416
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "LLVMFuzzerTestOneInput",
   "use_fn": "check_content_type_and_change_protocol"
  }
 },
 {
  "osv_id": "ARVO-42485276",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cur",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/error.c",
    "line": 175,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "xmlBufCreate",
    "file": "/src/libxml2/buf.c",
    "line": 137
   },
   "size_expr": null,
   "size_bytes": 4096,
   "cross_function": true,
   "size_expr_cpg": "81",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 194,
    "fn": "xmlParserPrintFileContextInternal",
    "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 486,
    "fn": "xmlBufGrowInternal",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlParserPrintFileContextInternal",
    "file": "/src/libxml2/error.c",
    "line": 194
   },
   "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 4096
   }
  },
  "context": {
   "fn": "xmlParserPrintFileContextInternal",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "cur > base | cur > base",
   "guard_count": 2,
   "control_structures": "IF:180,WHILE:186,WHILE:191,IF:194,WHILE:201,WHILE:213,IF:214"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "input",
   "data"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/84bab955fe01c50e64382481de67259047d917a9/ARVO-42485276/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_84bab955fe01.cpg",
   "testcase_size": 2157
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 4096,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "xmlParserPrintFileContextInternal--xmlReportError--__xmlRaiseError",
   "region_size": 4096
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cur = input->cur",
     "line": 183
    }
   ],
   "entity_decl": {
    "line": 175,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "cur",
   "func_lines": [
    172,
    221
   ],
   "func_params": {
    "names": [
     "input",
     "channel",
     "data"
    ],
    "types": [
     "xmlParserInputPtr",
     "xmlGenericErrorFunc",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "input == NULL",
     "line": 180
    },
    {
     "code": "input->cur == NULL",
     "line": 180
    },
    {
     "code": "cur > base",
     "line": 186
    },
    {
     "code": "*(cur) == '\\n'",
     "line": 186
    },
    {
     "code": "*(cur) == '\\r'",
     "line": 186
    },
    {
     "code": "n++ < (sizeof(content)-1)",
     "line": 191
    },
    {
     "code": "cur > base",
     "line": 191
    },
    {
     "code": "*(cur) != '\\n'",
     "line": 192
    },
    {
     "code": "*(cur) != '\\r'",
     "line": 192
    },
    {
     "code": "*(cur) == '\\n'",
     "line": 194
    },
    {
     "code": "*(cur) == '\\r'",
     "line": 194
    },
    {
     "code": "*cur != 0",
     "line": 201
    },
    {
     "code": "*(cur) != '\\n'",
     "line": 201
    },
    {
     "code": "*(cur) != '\\r'",
     "line": 202
    },
    {
     "code": "n < sizeof(content)-1",
     "line": 202
    },
    {
     "code": "n<col",
     "line": 213
    },
    {
     "code": "n++ < sizeof(content)-2",
     "line": 213
    },
    {
     "code": "*ctnt != 0",
     "line": 213
    },
    {
     "code": "*(ctnt) != '\\t'",
     "line": 214
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "(*(cur) == '\\n') ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "*(cur) == '\\n'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*(cur)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*(cur) == '\\r'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*(cur)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "cur++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "cur"
   ],
   "osv_id": "ARVO-42485276",
   "sites": [
    {
     "args": "81",
     "callee": "<operator>.alloc",
     "code": "content[81]",
     "line": 177
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "xmlBufGrowInternal",
   "use_fn": "xmlParserPrintFileContextInternal"
  }
 },
 {
  "osv_id": "ARVO-42485599",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cur",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/error.c",
    "line": 175,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "xmlBufCreate",
    "file": "/src/libxml2/buf.c",
    "line": 137
   },
   "size_expr": null,
   "size_bytes": 4096,
   "cross_function": true,
   "size_expr_cpg": "81",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 194,
    "fn": "xmlParserPrintFileContextInternal",
    "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 486,
    "fn": "xmlBufGrowInternal",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlParserPrintFileContextInternal",
    "file": "/src/libxml2/error.c",
    "line": 194
   },
   "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 4096
   }
  },
  "context": {
   "fn": "xmlParserPrintFileContextInternal",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "cur > base | cur > base",
   "guard_count": 2,
   "control_structures": "IF:180,WHILE:186,WHILE:191,IF:194,WHILE:201,WHILE:213,IF:214"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "input",
   "data"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/84bab955fe01c50e64382481de67259047d917a9/ARVO-42485599/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_84bab955fe01.cpg",
   "testcase_size": 2060
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 4096,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "xmlParserPrintFileContextInternal--xmlReportError--__xmlRaiseError",
   "region_size": 4096
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cur = input->cur",
     "line": 183
    }
   ],
   "entity_decl": {
    "line": 175,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "cur",
   "func_lines": [
    172,
    221
   ],
   "func_params": {
    "names": [
     "input",
     "channel",
     "data"
    ],
    "types": [
     "xmlParserInputPtr",
     "xmlGenericErrorFunc",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "input == NULL",
     "line": 180
    },
    {
     "code": "input->cur == NULL",
     "line": 180
    },
    {
     "code": "cur > base",
     "line": 186
    },
    {
     "code": "*(cur) == '\\n'",
     "line": 186
    },
    {
     "code": "*(cur) == '\\r'",
     "line": 186
    },
    {
     "code": "n++ < (sizeof(content)-1)",
     "line": 191
    },
    {
     "code": "cur > base",
     "line": 191
    },
    {
     "code": "*(cur) != '\\n'",
     "line": 192
    },
    {
     "code": "*(cur) != '\\r'",
     "line": 192
    },
    {
     "code": "*(cur) == '\\n'",
     "line": 194
    },
    {
     "code": "*(cur) == '\\r'",
     "line": 194
    },
    {
     "code": "*cur != 0",
     "line": 201
    },
    {
     "code": "*(cur) != '\\n'",
     "line": 201
    },
    {
     "code": "*(cur) != '\\r'",
     "line": 202
    },
    {
     "code": "n < sizeof(content)-1",
     "line": 202
    },
    {
     "code": "n<col",
     "line": 213
    },
    {
     "code": "n++ < sizeof(content)-2",
     "line": 213
    },
    {
     "code": "*ctnt != 0",
     "line": 213
    },
    {
     "code": "*(ctnt) != '\\t'",
     "line": 214
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "(*(cur) == '\\n') ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "*(cur) == '\\n'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*(cur)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*(cur) == '\\r'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*(cur)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "cur++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "cur"
   ],
   "osv_id": "ARVO-42485599",
   "sites": [
    {
     "args": "81",
     "callee": "<operator>.alloc",
     "code": "content[81]",
     "line": 177
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "xmlBufGrowInternal",
   "use_fn": "xmlParserPrintFileContextInternal"
  }
 },
 {
  "osv_id": "ARVO-42486565",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "buf",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/xinclude.c",
    "line": 2216,
    "size": null,
    "type": "char[50]"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "xmlNewNodeEatName",
    "file": "/src/libxml2/tree.c",
    "line": 2283
   },
   "size_expr": null,
   "size_bytes": 120,
   "cross_function": true,
   "size_expr_cpg": "50",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2216,
    "fn": "xmlXIncludeIncludeNode",
    "code": "buf[50] | buf[50]",
    "origin": "report:crash",
    "args": "50"
   },
   {
    "kind": "free",
    "line": 3819,
    "fn": "xmlFreeNode",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlXIncludeIncludeNode",
    "file": "/src/libxml2/xinclude.c",
    "line": 2216
   },
   "code": "buf[50] | buf[50]",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 120
   }
  },
  "context": {
   "fn": "xmlCharEncFirstLineInput",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:2152,IF:2159,IF:2170,IF:2171,ELSE:2173,IF:2174,IF:2177,IF:2181,IF:2190,SWITCH:2193,BREAK:2200,BREAK:2207"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[50]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/9de7b94d4ffbd11814008a5aa529b4ca77564921/ARVO-42486565/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_9de7b94d4ffb.cpg",
   "testcase_size": 120
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 120,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "xmlXIncludeIncludeNode--xmlXIncludeDoProcess--xmlXIncludeLoadFallback",
   "region_size": 120
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf[50]",
     "line": 2216
    },
    {
     "code": "buf[49] = 0",
     "line": 2222
    }
   ],
   "entity_decl": {
    "line": 2216,
    "type": "char[50]"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    2141,
    2234
   ],
   "func_params": {
    "names": [
     "input",
     "len"
    ],
    "types": [
     "xmlParserInputBufferPtr",
     "int"
    ]
   },
   "guards": [
    {
     "code": "input == NULL",
     "line": 2152
    },
    {
     "code": "input->encoder == NULL",
     "line": 2152
    },
    {
     "code": "input->buffer == NULL",
     "line": 2153
    },
    {
     "code": "input->raw == NULL",
     "line": 2153
    },
    {
     "code": "toconv == 0",
     "line": 2159
    },
    {
     "code": "toconv > (unsigned int) len",
     "line": 2171
    },
    {
     "code": "toconv > 180",
     "line": 2174
    },
    {
     "code": "written > 360",
     "line": 2181
    },
    {
     "code": "ret == -1",
     "line": 2190
    },
    {
     "code": "ret == -3",
     "line": 2231
    },
    {
     "code": "ret == -1",
     "line": 2232
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "buf[50]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "buf[50]",
     "name": "<operator>.alloc",
     "nargs": 1
    }
   ],
   "line_ids": [
    "buf"
   ],
   "osv_id": "ARVO-42486565",
   "sites": [
    {
     "args": "50",
     "callee": "<operator>.alloc",
     "code": "buf[50]",
     "line": 2216
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xmlFreeNode",
   "use_fn": "xmlXIncludeIncludeNode"
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