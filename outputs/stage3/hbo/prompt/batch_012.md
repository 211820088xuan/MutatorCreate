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
  "osv_id": "ARVO-42488087",
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
    "fn": "wolfCrypt_custom_malloc",
    "file": "/src/wolf-ssl-ssh-fuzzers/oss-fuzz/projects/wolf-ssl-ssh/fuzzers/include/fuzzers/shared.h",
    "line": 180
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/881657782478cef4a1527847bb2c4cd427bd6c99/ARVO-42488087/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_881657782478.cpg",
   "testcase_size": 432
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
   "dedup_token": "fp_to_unsigned_bin_at_pos--fp_to_unsigned_bin--mp_to_unsigned_bin"
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
  "osv_id": "ARVO-42488088",
  "project": "openh264",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pCurDqLayer",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/decode_slice.cpp",
    "line": 2538,
    "size": null,
    "type": "PDqLayer"
   }
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
   "cross_function": true,
   "size_expr_cpg": "LIST_A ;; 2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2574,
    "fn": "WelsDec::WelsDecodeMbCavlcBSlice(WelsDec::TagWelsDecoderContext*, WelsDec::TagNalUnit*, unsigned int&)",
    "code": "memset (pCurDqLayer->pDec->pRefIndex[LIST_0][iMbXy], 0,  | pCurDqLayer->pDec->pRefIndex[LIST_0][iMbXy] | pCurDqLayer->pDec->pRefIndex[LIST_0] | pCurDqLayer->pDec->pRefIndex",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::WelsDecodeMbCavlcBSlice(WelsDec::TagWelsDecoderContext*, WelsDec::TagNalUnit*, unsigned int&)",
    "file": "/src/openh264/codec/decoder/core/src/decode_slice.cpp",
    "line": 2574
   },
   "code": "memset (pCurDqLayer->pDec->pRefIndex[LIST_0][iMbXy], 0,  | pCurDqLayer->pDec->pRefIndex[LIST_0][iMbXy] | pCurDqLayer->pDec->pRefIndex[LIST_0] | pCurDqLayer->pDec->pRefIndex",
   "access": {
    "dir": "WRITE",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "WelsDecodeMbCavlcBSlice",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:2554,DO:2555,IF:2555,IF:2557,IF:2561,IF:2587,IF:2591,ELSE:2594,IF:2597,IF:2607,FOR:2610,ELSE:2617"
  },
  "call_chain": [],
  "types": {
   "entity_type": "PDqLayer",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "pCtx"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openh264/address/992c1c147175126c3fe7ab78216aa0395f9e6c71/ARVO-42488088/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_992c1c147175.cpg",
   "testcase_size": 4364
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
   "dedup_token": "__asan_memset--WelsDec::WelsDecodeMbCavlcBSlice(WelsDec::TagWelsDecoderContext*, WelsDec::TagNalUnit*, unsigned int&)--WelsDec::WelsDecodeSlice(WelsDec::TagWels"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pCurDqLayer = pCtx->pCurDqLayer",
     "line": 2538
    },
    {
     "code": "pCurDqLayer->pNoSubMbPartSizeLessThan8x8Flag[iMbXy] = true",
     "line": 2551
    },
    {
     "code": "pCurDqLayer->pTransformSize8x8Flag[iMbXy] = false",
     "line": 2552
    },
    {
     "code": "pCurDqLayer->pDec->pMbType[iMbXy] = MB_TYPE_SKIP ",
     "line": 2565
    },
    {
     "code": "pCurDqLayer->pInterPredictionDoneFlag[iMbXy] = 0",
     "line": 2573
    },
    {
     "code": "pCurDqLayer->pLumaQp[iMbXy] = pSlice->iLastMbQp",
     "line": 2609
    },
    {
     "code": "pCurDqLayer->pChromaQp[iMbXy][i] = g_kuiChromaQpTable[WELS_CLIP3 (pCurDqLayer->pLumaQp[iMbXy] +",
     "line": 2611
    },
    {
     "code": "pCurDqLayer->pCbp[iMbXy] = 0",
     "line": 2616
    }
   ],
   "entity_decl": {
    "line": 2538,
    "type": "PDqLayer"
   },
   "entity_name_cpg": "pCurDqLayer",
   "func_lines": [
    2537,
    2649
   ],
   "func_params": {
    "names": [
     "pCtx",
     "pNalCur",
     "uiEosFlag"
    ],
    "types": [
     "PWelsDecoderContext",
     "PNalUnit",
     "uint32_t&"
    ]
   },
   "guards": [
    {
     "code": "-1 == pSlice->iMbSkipRun",
     "line": 2554
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 2555
    },
    {
     "code": "-1 == pSlice->iMbSkipRun",
     "line": 2557
    },
    {
     "code": "GetThreadCount (pCtx) > 1",
     "line": 2576
    },
    {
     "code": "ret != ERR_NONE",
     "line": 2591
    },
    {
     "code": "ret != ERR_NONE",
     "line": 2597
    },
    {
     "code": "pNalCur->sNalHeaderExt.uiQualityId == 0",
     "line": 2608
    },
    {
     "code": "pNalCur->sNalHeaderExt.uiDependencyId == 0",
     "line": 2608
    },
    {
     "code": "i < 2",
     "line": 2610
    },
    {
     "code": "(pCurDqLayer->pLumaQp[iMbXy] + pSliceHeader->pPps->iChromaQpIndexOffset[i]) < (0)",
     "line": 2611
    },
    {
     "code": "(pCurDqLayer->pLumaQp[iMbXy] + pSliceHeader->pPps->iChromaQpIndexOffset[i]) > (51)",
     "line": 2611
    },
    {
     "code": "pSlice->sSliceHeaderExt.bAdaptiveBaseModeFlag == 1",
     "line": 2618
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 2619
    },
    {
     "code": "iUsedBits == (pBs->iBits - 1)",
     "line": 2638
    },
    {
     "code": "iUsedBits > (pBs->iBits -",
     "line": 2641
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "memset (pCurDqLayer->pDec->pRefIndex[LIST_0][iMbXy], 0, sizeof (int8_t) * 16)",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "pCurDqLayer->pDec->pRefIndex[LIST_0][iMbXy]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pCurDqLayer->pDec->pRefIndex[LIST_0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pCurDqLayer->pDec->pRefIndex",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "pCurDqLayer->pDec",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "sizeof (int8_t) * 16",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "sizeof (int8_t)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "pCurDqLayer",
    "LIST_0",
    "iMbXy",
    "int8_t"
   ],
   "osv_id": "ARVO-42488088",
   "sites": [
    {
     "args": "LIST_A ;; 2",
     "callee": "<operator>.alloc",
     "code": "iMv[LIST_A][2] = { { 0, 0 }, { 0, 0 } }",
     "line": 2562
    },
    {
     "args": "LIST_A",
     "callee": "<operator>.alloc",
     "code": "ref[LIST_A] = { 0 }",
     "line": 2563
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WelsDec::WelsDecodeMbCavlcBSlice(WelsDec::TagWelsDecoderContext*, WelsDec::TagNalUnit*, unsigned int&)"
  }
 },
 {
  "osv_id": "ARVO-42488097",
  "project": "openh264",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p0_e",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/decode_slice.cpp",
    "line": 627,
    "size": null,
    "type": "v8i16"
   }
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
    "line": 683,
    "fn": "WelsDec::WelsDecodeMbCabacISliceBaseMode0(WelsDec::TagWelsDecoderContext*, unsigned int&)",
    "code": "MSA_PCKEV_B2(v8i16, p0_e, p0_e, q0_e, q0_e, t0, t1) | t0 = (v8i16)__msa_pckev_b((v16i8)p0_e, (v16i8)p0_e) | (v8i16)__msa_pckev_b((v16i8)p0_e, (v16i8)p0_e) | __msa_pckev_b((v16i8)p0_e, (v16i8)p0_e)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::WelsDecodeMbCabacISliceBaseMode0(WelsDec::TagWelsDecoderContext*, unsigned int&)",
    "file": "/src/openh264/codec/decoder/core/src/decode_slice.cpp",
    "line": 683
   },
   "code": "MSA_PCKEV_B2(v8i16, p0_e, p0_e, q0_e, q0_e, t0, t1) | t0 = (v8i16)__msa_pckev_b((v16i8)p0_e, (v16i8)p0_e) | (v8i16)__msa_pckev_b((v16i8)p0_e, (v16i8)p0_e) | __msa_pckev_b((v16i8)p0_e, (v16i8)p0_e)",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "DeblockChromaLt4V_msa",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "v8i16",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "iStride",
   "pTc"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openh264/address/effb3931c7c67f34b167fe6e0a93253bf075f78c/ARVO-42488097/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_effb3931c7c6.cpg",
   "testcase_size": 1632
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
   "dedup_token": "WelsDec::WelsDecodeMbCabacISliceBaseMode0(WelsDec::TagWelsDecoderContext*, unsigned int&)--WelsDec::WelsDecodeMbCabacISlice(WelsDec::TagWelsDecoderContext*, Wel"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "p0_e = (v8i16)__msa_ilvr_b((v16i8)zero, (v16i8)p0)",
     "line": 661
    },
    {
     "code": "p0_e = (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags))",
     "line": 675
    },
    {
     "code": "p0_e = (v8i16)__msa_ilvr_b((v16i8)zero, (v16i8)p0)",
     "line": 704
    },
    {
     "code": "p0_e = (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags))",
     "line": 718
    }
   ],
   "entity_decl": {
    "line": 627,
    "type": "v8i16"
   },
   "entity_name_cpg": "p0_e",
   "func_lines": [
    624,
    734
   ],
   "func_params": {
    "names": [
     "pPixCb",
     "pPixCr",
     "iStride",
     "iAlpha",
     "iBeta",
     "pTc"
    ],
    "types": [
     "uint8_t*",
     "uint8_t*",
     "int32_t",
     "int32_t",
     "int32_t",
     "int8_t*"
    ]
   },
   "guards": [],
   "line_call_count": 11,
   "line_calls": [
    {
     "code": "MSA_PCKEV_B2(v8i16, p0_e, p0_e, q0_e, q0_e, t0, t1)",
     "name": "MSA_PCKEV_B2",
     "nargs": 7
    },
    {
     "code": "t0 = (v8i16)__msa_pckev_b((v16i8)p0_e, (v16i8)p0_e)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(v8i16)__msa_pckev_b((v16i8)p0_e, (v16i8)p0_e)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "__msa_pckev_b((v16i8)p0_e, (v16i8)p0_e)",
     "name": "__msa_pckev_b",
     "nargs": 2
    },
    {
     "code": "(v16i8)p0_e",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(v16i8)p0_e",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "t1 = (v8i16)__msa_pckev_b((v16i8)q0_e, (v16i8)q0_e)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(v8i16)__msa_pckev_b((v16i8)q0_e, (v16i8)q0_e)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "__msa_pckev_b((v16i8)q0_e, (v16i8)q0_e)",
     "name": "__msa_pckev_b",
     "nargs": 2
    },
    {
     "code": "(v16i8)q0_e",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(v16i8)q0_e",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p0_e",
    "q0_e",
    "t0",
    "t1"
   ],
   "osv_id": "ARVO-42488097",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WelsDec::WelsDecodeMbCabacISliceBaseMode0(WelsDec::TagWelsDecoderContext*, unsigned int&)"
  }
 },
 {
  "osv_id": "ARVO-42488098",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_utils.c",
    "line": 574,
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
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 577,
    "fn": "encoded_to_buf",
    "code": "*p++ = in[i] | *p++ | p++ | in[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "encoded_to_buf",
    "file": "/src/fluent-bit/src/flb_utils.c",
    "line": 577
   },
   "code": "*p++ = in[i] | *p++ | p++ | in[i]",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "encoded_to_buf",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < len",
   "guard_count": 1,
   "control_structures": "FOR:576"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "out",
   "in",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/32588477159f5df8eda835c2d23edc4fce34f4b7/ARVO-42488098/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_32588477159f.cpg",
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "encoded_to_buf--flb_utils_write_str--msgpack2json"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*p = out",
     "line": 574
    }
   ],
   "entity_decl": {
    "line": 574,
    "type": "char*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    571,
    579
   ],
   "func_params": {
    "names": [
     "out",
     "in",
     "len"
    ],
    "types": [
     "char*",
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "i < len",
     "line": 576
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "*p++ = in[i]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*p++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "p++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "in[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p",
    "in",
    "i"
   ],
   "osv_id": "ARVO-42488098",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "encoded_to_buf"
  }
 },
 {
  "osv_id": "ARVO-42488121",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "total",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_log.c",
    "line": 330,
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
    "line": 406,
    "fn": "flb_log_print",
    "code": "total = vsnprintf(msg.msg + len,",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_log_print",
    "file": "/src/fluent-bit/src/flb_log.c",
    "line": 406
   },
   "code": "total = vsnprintf(msg.msg + len,",
   "access": {
    "dir": "READ",
    "width": 53,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_log_print",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "total < 0",
   "guard_count": 1,
   "control_structures": "SWITCH:343,BREAK:347,BREAK:351,BREAK:355,BREAK:359,BREAK:363,BREAK:367,BREAK:371,IF:375,IF:384,IF:409,IF:423"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "fmt"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9643eebeba6bddd31978783cbbfb1686c93d8e24/ARVO-42488121/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9643eebeba6b.cpg",
   "testcase_size": 100
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
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--flb_log_print--flb_parser_typecast"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "total = vsnprintf(msg.msg + len,",
     "line": 406
    },
    {
     "code": "total = strlen(msg.msg + len) + len",
     "line": 414
    }
   ],
   "entity_decl": {
    "line": 330,
    "type": "int"
   },
   "entity_name_cpg": "total",
   "func_lines": [
    327,
    432
   ],
   "func_params": {
    "names": [
     "type",
     "file",
     "line",
     "fmt"
    ],
    "types": [
     "int",
     "char*",
     "int",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "current == NULL",
     "line": 384
    },
    {
     "code": "total < 0",
     "line": 409
    },
    {
     "code": "n == -1",
     "line": 425
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "total = vsnprintf(msg.msg + len,",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "vsnprintf(msg.msg + len,",
     "name": "vsnprintf",
     "nargs": null
    },
    {
     "code": "msg.msg + len",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "msg.msg",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "total",
    "msg",
    "len"
   ],
   "osv_id": "ARVO-42488121",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_log_print"
  }
 },
 {
  "osv_id": "ARVO-42488123",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_strptime.c",
    "line": 669,
    "size": null,
    "type": "unsigned char**"
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
    "line": 674,
    "fn": "_conv_num",
    "code": "**buf < '0' || **buf > '9' | **buf < '0' | **buf | *buf",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_conv_num",
    "file": "/src/fluent-bit/src/flb_strptime.c",
    "line": 674
   },
   "code": "**buf < '0' || **buf > '9' | **buf < '0' | **buf | *buf",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_conv_num",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:674,DO:678,IF:684"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9643eebeba6bddd31978783cbbfb1686c93d8e24/ARVO-42488123/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9643eebeba6b.cpg",
   "testcase_size": 100
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
   "dedup_token": "_conv_num--_flb_strptime--flb_strptime"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 669,
    "type": "unsigned char**"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    668,
    689
   ],
   "func_params": {
    "names": [
     "buf",
     "dest",
     "llim",
     "ulim"
    ],
    "types": [
     "unsigned char**",
     "int*",
     "int",
     "int"
    ]
   },
   "guards": [
    {
     "code": "**buf < '0'",
     "line": 674
    },
    {
     "code": "**buf > '9'",
     "line": 674
    },
    {
     "code": "result < llim",
     "line": 684
    },
    {
     "code": "result > ulim",
     "line": 684
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "**buf < '0' ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "**buf < '0'",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "**buf",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*buf",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "**buf > '9'",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "**buf",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*buf",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "buf"
   ],
   "osv_id": "ARVO-42488123",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_conv_num"
  }
 },
 {
  "osv_id": "ARVO-42488124",
  "project": "openh264",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pSpsBs",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "line": 1178,
    "size": null,
    "type": "SSpsBsInfo*"
   }
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
   "cross_function": true,
   "size_expr_cpg": "6",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1180,
    "fn": "WelsDec::Update8x8RefIdx(WelsDec::TagDqLayer*&, short const&, int const&, signed char const&)",
    "code": "pSpsBs->pSpsBsBuf [0] = pSpsBs->pSpsBsBuf [1] = pSpsBs-> | pSpsBs->pSpsBsBuf [0] | pSpsBs->pSpsBsBuf | pSpsBs->pSpsBsBuf [1] = pSpsBs->pSpsBsBuf [2] = 0x00",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::Update8x8RefIdx(WelsDec::TagDqLayer*&, short const&, int const&, signed char const&)",
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "line": 1180
   },
   "code": "pSpsBs->pSpsBsBuf [0] = pSpsBs->pSpsBsBuf [1] = pSpsBs-> | pSpsBs->pSpsBsBuf [0] | pSpsBs->pSpsBsBuf | pSpsBs->pSpsBsBuf [1] = pSpsBs->pSpsBsBuf [2] = 0x00",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ParseSps",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:927,IF:927,IF:929,DO:935,IF:935,DO:937,IF:937,DO:939,IF:939,DO:941,IF:941,DO:943"
  },
  "call_chain": [],
  "types": {
   "entity_type": "SSpsBsInfo*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "pBsAux"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openh264/address/effb3931c7c67f34b167fe6e0a93253bf075f78c/ARVO-42488124/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_effb3931c7c6.cpg",
   "testcase_size": 1176
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
   "dedup_token": "WelsDec::Update8x8RefIdx(WelsDec::TagDqLayer*&, short const&, int const&, signed char const&)--WelsDec::ParseInterBMotionInfoCabac(WelsDec::TagWelsDecoderContex"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* pSpsBs = &pCtx->sSpsBsInfo [iSpsId]",
     "line": 1162
    },
    {
     "code": "pSpsBs->iSpsId = iSpsId",
     "line": 1163
    },
    {
     "code": "pSpsBs->uiSpsBsLen = (uint16_t) iActualLen",
     "line": 1168
    },
    {
     "code": "pSpsBs->pSpsBsBuf[0] = 0x0",
     "line": 1172
    },
    {
     "code": "* pSpsBs = &pCtx->sSubsetSpsBsInfo [iSpsId]",
     "line": 1178
    },
    {
     "code": "pSpsBs->iSpsId = iSpsId",
     "line": 1179
    },
    {
     "code": "pSpsBs->pSpsBsBuf [0] = pSpsBs->pSpsBsBuf [1] = pSpsBs->pSpsBsBuf [2] = 0x00",
     "line": 1180
    },
    {
     "code": "pSpsBs->pSpsBsBuf [1] = pSpsBs->pSpsBsBuf [2] = 0x00",
     "line": 1180
    },
    {
     "code": "pSpsBs->pSpsBsBuf [2] = 0x00",
     "line": 1180
    },
    {
     "code": "pSpsBs->pSpsBsBuf [3] = 0x01",
     "line": 1181
    },
    {
     "code": "pSpsBs->pSpsBsBuf [4] = 0x67",
     "line": 1182
    },
    {
     "code": "pSpsBs->uiSpsBsLen = (uint16_t) (sSubsetSpsBs.pCurBuf - sSubsetSpsBs.pStartBuf + 5)",
     "line": 1237
    }
   ],
   "entity_decl": {
    "line": 1162,
    "type": "SSpsBsInfo*"
   },
   "entity_name_cpg": "pSpsBs",
   "func_lines": [
    911,
    1310
   ],
   "func_params": {
    "names": [
     "pCtx",
     "pBsAux",
     "pPicWidth",
     "pPicHeight",
     "pSrcNal",
     "kSrcNalLen"
    ],
    "types": [
     "PWelsDecoderContext",
     "PBitStringAux",
     "int32_t*",
     "int32_t*",
     "uint8_t*",
     "int32_t"
    ]
   },
   "guards": [
    {
     "code": "(pNalHead->eNalUnitType) == NAL_UNIT_SUBSET_SPS",
     "line": 925
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 927
    },
    {
     "code": "uiProfileIdc != PRO_BASELINE",
     "line": 929
    },
    {
     "code": "uiProfileIdc != PRO_MAIN",
     "line": 929
    },
    {
     "code": "uiProfileIdc != PRO_SCALABLE_BASELINE",
     "line": 929
    },
    {
     "code": "uiProfileIdc != PRO_SCALABLE_HIGH",
     "line": 930
    },
    {
     "code": "uiProfileIdc != PRO_EXTENDED",
     "line": 931
    },
    {
     "code": "uiProfileIdc != PRO_HIGH",
     "line": 931
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 935
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 937
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 939
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 941
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 943
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 945
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 947
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 948
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 950
    },
    {
     "code": "NULL == pSLevelLimits",
     "line": 962
    },
    {
     "code": "PRO_SCALABLE_BASELINE == uiProfileIdc",
     "line": 974
    },
    {
     "code": "PRO_SCALABLE_HIGH == uiProfileIdc",
     "line": 974
    },
    {
     "code": "PRO_HIGH == uiProfileIdc",
     "line": 975
    },
    {
     "code": "PRO_HIGH10 == uiProfileIdc",
     "line": 975
    },
    {
     "code": "PRO_HIGH422 == uiProfileIdc",
     "line": 976
    },
    {
     "code": "PRO_HIGH444 == uiProfileIdc",
     "line": 976
    },
    {
     "code": "PRO_CAVLC444 == uiProfileIdc",
     "line": 977
    },
    {
     "code": "44 == uiProfileIdc",
     "line": 977
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 979
    },
    {
     "code": "pSps->uiChromaFormatIdc > 1",
     "line": 986
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 993
    },
    {
     "code": "uiCode != 0",
     "line": 994
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1000
    },
    {
     "code": "uiCode != 0",
     "line": 1001
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1007
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1009
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1013
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1017
    },
    {
     "code": "uiCode > 12",
     "line": 1018
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1021
    },
    {
     "code": "0 == pSps->uiPocType",
     "line": 1024
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1025
    },
    {
     "code": "uiCode > 12",
     "line": 1027
    },
    {
     "code": "1 == pSps->uiPocType",
     "line": 1031
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1033
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1035
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1037
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1039
    },
    {
     "code": "uiCode > 255",
     "line": 1040
    },
    {
     "code": "i < pSps->iNumRefFramesInPocCycle",
     "line": 1044
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1045
    },
    {
     "code": "pSps->uiPocType > 2",
     "line": 1049
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1054
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1056
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1058
    },
    {
     "code": "pSps->iMbWidth > MAX_MB_SIZE",
     "line": 1060
    },
    {
     "code": "pSps->iMbWidth == 0",
     "line": 1060
    },
    {
     "code": "((uint64_t)pSps->iMbWidth * (uint64_t)pSps->iMbWidth) > (uint64_t) (8 * pSLevelLimits->uiMaxFS)",
     "line": 1064
    },
    {
     "code": "((uint64_t)pSps->iMbWidth * (uint64_t)pSps->iMbWidth) > (uint64_t) (8 * pSMaxLevelLimits->uiMaxFS)",
     "line": 1065
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1072
    },
    {
     "code": "pSps->iMbHeight > MAX_MB_SIZE",
     "line": 1074
    },
    {
     "code": "pSps->iMbHeight == 0",
     "line": 1074
    },
    {
     "code": "((uint64_t)pSps->iMbHeight * (uint64_t)pSps->iMbHeight) > (uint64_t) (8 * pSLevelLimits->uiMaxFS)",
     "line": 1078
    },
    {
     "code": "((uint64_t)pSps->iMbHeight * (uint64_t)pSps->iMbHeight) > (uint64_t) (8 * pSMaxLevelLimits->uiMaxFS)",
     "line": 1079
    },
    {
     "code": "uiTmp64 > (uint64_t)pSLevelLimits->uiMaxFS",
     "line": 1087
    },
    {
     "code": "uiTmp64 > (uint64_t)pSMaxLevelLimits->uiMaxFS",
     "line": 1088
    },
    {
     "code": "pSps->iNumRefFrames > 16",
     "line": 1096
    },
    {
     "code": "uiMaxDpbFrames > SPS_MAX_NUM_REF_FRAMES_MAX",
     "line": 1101
    },
    {
     "code": "(uint32_t)pSps->iNumRefFrames > uiMaxDpbFrames",
     "line": 1103
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1106
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1113
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1115
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1118
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1120
    },
    {
     "code": "(pSps->sFrameCrop.iLeftOffset + pSps->sFrameCrop.iRightOffset) > ((int32_t)pSps->iMbWidth * 16 / 2)",
     "line": 1122
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1126
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1128
    },
    {
     "code": "(pSps->sFrameCrop.iTopOffset + pSps->sFrameCrop.iBottomOffset) > ((int32_t)pSps->iMbHeight * 16 / 2)",
     "line": 1130
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1140
    },
    {
     "code": "iRetVui == GENERATE_ERROR_NO (ERR_LEVEL_PARAM_SETS, ERR_INFO_UNSUPPORTED_VUI_HRD)",
     "line": 1144
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1150
    },
    {
     "code": "pSrcNal[kSrcNalLen - iTrailingZeroByte - 1] == 0x0",
     "line": 1165
    },
    {
     "code": "pSrcNal[0] == 0x0",
     "line": 1171
    },
    {
     "code": "pSrcNal[1] == 0x0",
     "line": 1171
    },
    {
     "code": "pSrcNal[2] == 0x1",
     "line": 1171
    },
    {
     "code": "NULL == pBsBuf",
     "line": 1190
    },
    {
     "code": "pSps->uiPocType == 0",
     "line": 1206
    },
    {
     "code": "pSps->uiPocType == 1",
     "line": 1208
    },
    {
     "code": "i < pSps->iNumRefFramesInPocCycle",
     "line": 1213
    },
    {
     "code": "PRO_SCALABLE_BASELINE == uiProfileIdc",
     "line": 1244
    },
    {
     "code": "PRO_SCALABLE_HIGH == uiProfileIdc",
     "line": 1244
    },
    {
     "code": "(iRet = DecodeSpsSvcExt (pCtx, pSubsetSps, pBs)) != ERR_NONE",
     "line": 1245
    },
    {
     "code": "uiRetTmp != ERR_NONE",
     "line": 1249
    },
    {
     "code": "PRO_SCALABLE_BASELINE == uiProfileIdc",
     "line": 1256
    },
    {
     "code": "PRO_SCALABLE_HIGH == uiProfileIdc",
     "line": 1256
    },
    {
     "code": "memcmp (&pCtx->sSpsPpsCtx.sSubsetSpsBuffer[iSpsId], pSubsetSps, sizeof (SSubsetSps)) != 0",
     "line": 1270
    },
    {
     "code": "pCtx->pAccessUnitList->uiAvailUnitsNum > 0",
     "line": 1271
    },
    {
     "code": "pCtx->pSps != NULL",
     "line": 1276
    },
    {
     "code": "pCtx->pSps->iSpsId == pSubsetSps->sSps.iSpsId",
     "line": 1276
    },
    {
     "code": "memcmp (&pCtx->sSpsPpsCtx.sSpsBuffer[iSpsId], pSps, sizeof (SSps)) != 0",
     "line": 1284
    },
    {
     "code": "pCtx->pAccessUnitList->uiAvailUnitsNum > 0",
     "line": 1285
    },
    {
     "code": "pCtx->pSps != NULL",
     "line": 1290
    },
    {
     "code": "pCtx->pSps->iSpsId == pSps->iSpsId",
     "line": 1290
    }
   ],
   "line_call_count": 9,
   "line_calls": [
    {
     "code": "pSpsBs->pSpsBsBuf [0] = pSpsBs->pSpsBsBuf [1] = pSpsBs->pSpsBsBuf [2] = 0x00",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf [0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf [1] = pSpsBs->pSpsBsBuf [2] = 0x00",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf [1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf [2] = 0x00",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf [2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pSpsBs->pSpsBsBuf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pSpsBs"
   ],
   "osv_id": "ARVO-42488124",
   "sites": [
    {
     "args": "6",
     "callee": "<operator>.alloc",
     "code": "bConstraintSetFlags[6] = { false }",
     "line": 924
    },
    {
     "args": null,
     "callee": "WelsMallocz",
     "code": "pMa->WelsMallocz (SPS_PPS_BS_SIZE + 4,",
     "line": 1188
    },
    {
     "args": "pMa ;; pBsBuf ;; \"pBsBuf for parse only usage\"",
     "callee": "WelsFree",
     "code": "pMa->WelsFree (pBsBuf, \"pBsBuf for parse only usage\")",
     "line": 1239
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WelsDec::Update8x8RefIdx(WelsDec::TagDqLayer*&, short const&, int const&, signed char const&)"
  }
 },
 {
  "osv_id": "ARVO-42488251",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dest_",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": 64,
    "size": null,
    "type": "uint8_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/c-blosc2/tests/fuzz/fuzz_compress.c",
    "line": 37
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 71,
    "fn": "_sw32",
    "code": "dest_[2] = pa[2] | dest_[2] | pa[2]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_sw32",
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": 71
   },
   "code": "dest_[2] = pa[2] | dest_[2] | pa[2]",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_sw32",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:68,ELSE:74"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dest",
   "a"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/d9a951facac6e95b1a99a7f8ae569c9cff2fd4d4/ARVO-42488251/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_d9a951facac6.cpg",
   "testcase_size": 4125
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
   "dedup_token": "_sw32--blosc_c--serial_blosc"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* dest_ = (uint8_t*)dest",
     "line": 64
    },
    {
     "code": "dest_[0] = pa[0]",
     "line": 69
    },
    {
     "code": "dest_[1] = pa[1]",
     "line": 70
    },
    {
     "code": "dest_[2] = pa[2]",
     "line": 71
    },
    {
     "code": "dest_[3] = pa[3]",
     "line": 72
    },
    {
     "code": "dest_[0] = pa[3]",
     "line": 75
    },
    {
     "code": "dest_[1] = pa[2]",
     "line": 76
    },
    {
     "code": "dest_[2] = pa[1]",
     "line": 77
    },
    {
     "code": "dest_[3] = pa[0]",
     "line": 78
    }
   ],
   "entity_decl": {
    "line": 64,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "dest_",
   "func_lines": [
    63,
    80
   ],
   "func_params": {
    "names": [
     "dest",
     "a"
    ],
    "types": [
     "void*",
     "int32_t"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "dest_[2] = pa[2]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "dest_[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pa[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dest_",
    "pa"
   ],
   "osv_id": "ARVO-42488251",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_sw32"
  }
 },
 {
  "osv_id": "ARVO-42488418",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "time",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_utils.c",
    "line": 468,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/fluent-bit/tests/internal/fuzzers/utils_fuzzer.c",
    "line": 19
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 477,
    "fn": "flb_utils_time_to_seconds",
    "code": "time[len - 1] == 'D' || time[len - 1] == 'd' | time[len - 1] == 'D' | time[len - 1] | len - 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_utils_time_to_seconds",
    "file": "/src/fluent-bit/src/flb_utils.c",
    "line": 477
   },
   "code": "time[len - 1] == 'D' || time[len - 1] == 'd' | time[len - 1] == 'D' | time[len - 1] | len - 1",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_utils_time_to_seconds",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:477,IF:480,ELSE:483,IF:483"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "time"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/e06fb6a86979e138882c538aef3fd48060d4d294/ARVO-42488418/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_e06fb6a86979.cpg",
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
   "dedup_token": "flb_utils_time_to_seconds--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 468,
    "type": "char*"
   },
   "entity_name_cpg": "time",
   "func_lines": [
    468,
    488
   ],
   "func_params": {
    "names": [
     "time"
    ],
    "types": [
     "char*"
    ]
   },
   "guards": [
    {
     "code": "time[len - 1] == 'D'",
     "line": 477
    },
    {
     "code": "time[len - 1] == 'd'",
     "line": 477
    },
    {
     "code": "time[len - 1] == 'H'",
     "line": 480
    },
    {
     "code": "time[len - 1] == 'h'",
     "line": 480
    },
    {
     "code": "time[len - 1] == 'M'",
     "line": 483
    },
    {
     "code": "time[len - 1] == 'm'",
     "line": 483
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "time[len - 1] == 'D' ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "time[len - 1] == 'D'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "time[len - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "len - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "time[len - 1] == 'd'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "time[len - 1]",
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
    "time",
    "len"
   ],
   "osv_id": "ARVO-42488418",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_utils_time_to_seconds"
  }
 },
 {
  "osv_id": "ARVO-42488563",
  "project": "openh264",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "const_2_h",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/decode_slice.cpp",
    "line": 490,
    "size": null,
    "type": "v8i16"
   }
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
    "line": 490,
    "fn": "WelsDec::ParseIntra4x4Mode(WelsDec::TagWelsDecoderContext*, WelsDec::TagNeighborAvail*, signed char*, WelsCommon::TagBitStringAux*, WelsDec::TagDqLayer*)",
    "code": "const_2_h = __msa_ldi_h(2) | __msa_ldi_h(2)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::ParseIntra4x4Mode(WelsDec::TagWelsDecoderContext*, WelsDec::TagNeighborAvail*, signed char*, WelsCommon::TagBitStringAux*, WelsDec::TagDqLayer*)",
    "file": "/src/openh264/codec/decoder/core/src/decode_slice.cpp",
    "line": 490
   },
   "code": "const_2_h = __msa_ldi_h(2) | __msa_ldi_h(2)",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "DeblockLumaEq4H_msa",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "v8i16",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openh264/address/effb3931c7c67f34b167fe6e0a93253bf075f78c/ARVO-42488563/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_effb3931c7c6.cpg",
   "testcase_size": 76
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
   "dedup_token": "WelsDec::ParseIntra4x4Mode(WelsDec::TagWelsDecoderContext*, WelsDec::TagNeighborAvail*, signed char*, WelsCommon::TagBitStringAux*, WelsDec::TagDqLayer*)--WelsD"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "const_2_h = __msa_ldi_h(2)",
     "line": 490
    }
   ],
   "entity_decl": {
    "line": 490,
    "type": "v8i16"
   },
   "entity_name_cpg": "const_2_h",
   "func_lines": [
    478,
    622
   ],
   "func_params": {
    "names": [
     "pPix",
     "iStride",
     "iAlpha",
     "iBeta"
    ],
    "types": [
     "uint8_t*",
     "int32_t",
     "int32_t",
     "int32_t"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "const_2_h = __msa_ldi_h(2)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "__msa_ldi_h(2)",
     "name": "__msa_ldi_h",
     "nargs": 1
    }
   ],
   "line_ids": [
    "const_2_h"
   ],
   "osv_id": "ARVO-42488563",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WelsDec::ParseIntra4x4Mode(WelsDec::TagWelsDecoderContext*, WelsDec::TagNeighborAvail*, signed char*, WelsCommon::TagBitStringAux*, WelsDec::TagDqLayer*)"
  }
 },
 {
  "osv_id": "ARVO-42489163",
  "project": "fluent-bit",
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
    "fn": "flb_malloc",
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "line": 62
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1150,
    "fn": "tdefl_compress_lz_codes",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tdefl_compress_lz_codes",
    "file": "/src/fluent-bit/lib/miniz/miniz.c",
    "line": 1150
   },
   "code": "",
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tdefl_compress_lz_codes",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/72b62d2270edda9a0281ff8a6c3903d99e1892c9/ARVO-42489163/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_72b62d2270ed.cpg",
   "testcase_size": 138656
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
   "dedup_token": "tdefl_compress_lz_codes--tdefl_compress_block--tdefl_flush_block"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    1175,
    1220
   ],
   "func_params": {
    "names": [
     "d"
    ],
    "types": [
     "tdefl_compressor*"
    ]
   },
   "guards": [
    {
     "code": "pLZ_codes < d->m_pLZ_code_buf",
     "line": 1181
    },
    {
     "code": "flags == 1",
     "line": 1183
    },
    {
     "code": "d->m_pOutput_buf < d->m_pOutput_buf_end",
     "line": 1192
    },
    {
     "code": "d->m_pOutput_buf < d->m_pOutput_buf_end",
     "line": 1193
    },
    {
     "code": "match_dist < 512",
     "line": 1195
    },
    {
     "code": "d->m_pOutput_buf < d->m_pOutput_buf_end",
     "line": 1206
    },
    {
     "code": "d->m_pOutput_buf < d->m_pOutput_buf_end",
     "line": 1207
    },
    {
     "code": "d->m_pOutput_buf < d->m_pOutput_buf_end",
     "line": 1213
    },
    {
     "code": "d->m_pOutput_buf < d->m_pOutput_buf_end",
     "line": 1217
    },
    {
     "code": "d->m_pOutput_buf < d->m_pOutput_buf_end",
     "line": 1219
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42489163",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tdefl_compress_lz_codes"
  }
 },
 {
  "osv_id": "ARVO-42489279",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pb",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_gzip.c",
    "line": 74,
    "size": null,
    "type": "uint8_t*"
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
   "size_expr_cpg": "out_size",
   "size_expr_cpg_callee": "flb_malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 163,
    "fn": "flb_gzip_compress",
    "code": "*pb++ = (crc >> 24) & 0xFF | *pb++ | pb++ | (crc >> 24) & 0xFF",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_gzip_compress",
    "file": "/src/fluent-bit/src/flb_gzip.c",
    "line": 163
   },
   "code": "*pb++ = (crc >> 24) & 0xFF | *pb++ | pb++ | (crc >> 24) & 0xFF",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_gzip_compress",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:99,WHILE:131,IF:135,IF:140,BREAK:141,ELSE:143,IF:143,IF:149"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "in_data",
   "in_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/7c265e23bd2c7592ac9987ea92daa426ce48263a/ARVO-42489279/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_7c265e23bd2c.cpg",
   "testcase_size": 31870
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
   "dedup_token": "flb_gzip_compress--LLVMFuzzerTestOneInput--main"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pb = (uint8_t *) out_buf + FLB_GZIP_HEADER_OFFSET",
     "line": 128
    },
    {
     "code": "pb = (uint8_t *) out_buf + footer_start",
     "line": 157
    }
   ],
   "entity_decl": {
    "line": 74,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "pb",
   "func_lines": [
    68,
    174
   ],
   "func_params": {
    "names": [
     "in_data",
     "in_len",
     "out_data",
     "out_len"
    ],
    "types": [
     "void*",
     "size_t",
     "void**",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "strm.avail_in == 0",
     "line": 135
    },
    {
     "code": "status == Z_STREAM_END",
     "line": 140
    },
    {
     "code": "status != Z_OK",
     "line": 143
    },
    {
     "code": "deflateEnd(&strm) != Z_OK",
     "line": 149
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "*pb++ = (crc >> 24) & 0xFF",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*pb++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "pb++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "(crc >> 24) & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "crc >> 24",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pb",
    "crc"
   ],
   "osv_id": "ARVO-42489279",
   "sites": [
    {
     "args": "out_size",
     "callee": "flb_malloc",
     "code": "flb_malloc(out_size)",
     "line": 97
    },
    {
     "args": "out_buf",
     "callee": "flb_free",
     "code": "flb_free(out_buf)",
     "line": 150
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_gzip_compress"
  }
 },
 {
  "osv_id": "ARVO-42489424",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "tmp",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_parser_json.c",
    "line": 43,
    "size": null,
    "type": "char[255]"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "init_chunk_list",
    "file": "/src/fluent-bit/lib/msgpack-3.2.0/src/zone.c",
    "line": 21
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "255",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 164,
    "fn": "flb_parser_json_do",
    "code": "memcpy(tmp, v->via.str.ptr, len) | v->via.str.ptr | v->via.str | v->via",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_parser_json_do",
    "file": "/src/fluent-bit/src/flb_parser_json.c",
    "line": 164
   },
   "code": "memcpy(tmp, v->via.str.ptr, len) | v->via.str.ptr | v->via.str | v->via",
   "access": {
    "dir": "READ",
    "width": 254,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_parser_json_do",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "len > sizeof(tmp) - 1",
   "guard_count": 1,
   "control_structures": "IF:61,IF:67,IF:69,ELSE:75,IF:76,IF:88,IF:92,IF:105,IF:110,IF:115,ELSE:118,FOR:126"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[255]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9643eebeba6bddd31978783cbbfb1686c93d8e24/ARVO-42489424/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9643eebeba6b.cpg",
   "testcase_size": 690
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
   "dedup_token": "__asan_memcpy--flb_parser_json_do--flb_parser_do"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "tmp[255]",
     "line": 43
    },
    {
     "code": "tmp[len] = '\\0'",
     "line": 165
    }
   ],
   "entity_decl": {
    "line": 43,
    "type": "char[255]"
   },
   "entity_name_cpg": "tmp",
   "func_lines": [
    29,
    204
   ],
   "func_params": {
    "names": [
     "parser",
     "in_buf",
     "in_size",
     "out_buf",
     "out_size",
     "out_time"
    ],
    "types": [
     "flb_parser*",
     "char*",
     "size_t",
     "void**",
     "size_t*",
     "flb_time*"
    ]
   },
   "guards": [
    {
     "code": "ret != 0",
     "line": 61
    },
    {
     "code": "msgpack_unpack_next(&result, mp_buf, mp_size, &off) == MSGPACK_UNPACK_SUCCESS",
     "line": 67
    },
    {
     "code": "map.type != MSGPACK_OBJECT_MAP",
     "line": 69
    },
    {
     "code": "mp_size > 0",
     "line": 76
    },
    {
     "code": "ret == 0",
     "line": 92
    },
    {
     "code": "mp_buf != tmp_out_buf",
     "line": 105
    },
    {
     "code": "i < map_size",
     "line": 126
    },
    {
     "code": "k->via.str.size != slen",
     "line": 130
    },
    {
     "code": "strncmp(k->via.str.ptr, time_key, k->via.str.size) == 0",
     "line": 134
    },
    {
     "code": "parser->time_keep == FLB_FALSE",
     "line": 136
    },
    {
     "code": "ret == -1",
     "line": 159
    },
    {
     "code": "len > sizeof(tmp) - 1",
     "line": 161
    },
    {
     "code": "parser->time_keep == FLB_FALSE",
     "line": 178
    },
    {
     "code": "i < map_size",
     "line": 185
    },
    {
     "code": "i == skip",
     "line": 186
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(tmp, v->via.str.ptr, len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "v->via.str.ptr",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "v->via.str",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "v->via",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "tmp",
    "v",
    "len"
   ],
   "osv_id": "ARVO-42489424",
   "sites": [
    {
     "args": "255",
     "callee": "<operator>.alloc",
     "code": "tmp[255]",
     "line": 43
    },
    {
     "args": "mp_buf",
     "callee": "flb_free",
     "code": "flb_free(mp_buf)",
     "line": 70
    },
    {
     "args": "mp_buf",
     "callee": "flb_free",
     "code": "flb_free(mp_buf)",
     "line": 77
    },
    {
     "args": "mp_buf",
     "callee": "flb_free",
     "code": "flb_free(mp_buf)",
     "line": 106
    },
    {
     "args": "tmp_out_buf",
     "callee": "flb_free",
     "code": "flb_free(tmp_out_buf)",
     "line": 194
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_parser_json_do"
  }
 },
 {
  "osv_id": "ARVO-42489565",
  "project": "matio",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "readcount",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/matio/src/mat73.c",
    "line": 320,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Mat_H5ReadDatasetInfo",
    "file": "/src/matio/src/mat73.c",
    "line": 663
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "matvar->nbytes",
   "size_expr_cpg_callee": "ComplexMalloc"
  },
  "sites": [
   {
    "code": "malloc(matvar->nbytes)",
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "malloc",
    "line": 337,
    "origin": "cpg",
    "args": "matvar->nbytes"
   },
   {
    "code": "malloc(matvar->nbytes)",
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "malloc",
    "line": 357,
    "origin": "cpg",
    "args": "matvar->nbytes"
   },
   {
    "code": "malloc(matvar->data_size)",
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "malloc",
    "line": 374,
    "origin": "cpg",
    "args": "matvar->data_size"
   },
   {
    "code": "malloc(readcount)",
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "malloc",
    "line": 393,
    "origin": "cpg",
    "args": "readcount"
   },
   {
    "code": "malloc(readcount)",
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "malloc",
    "line": 452,
    "origin": "cpg",
    "args": "readcount"
   },
   {
    "code": "malloc(readcount)",
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "malloc",
    "line": 460,
    "origin": "cpg",
    "args": "readcount"
   },
   {
    "code": "malloc(sparse->ndata*Mat_SizeOf(data_type))",
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "malloc",
    "line": 640,
    "origin": "cpg",
    "args": "sparse->ndata*Mat_SizeOf(data_type)"
   },
   {
    "kind": "unknown",
    "line": 664,
    "fn": "Mat_H5ReadDatasetInfo",
    "code": "readcount = ReadInt32Data(mat, (mat_int32_t*)sparse->dat | ReadInt32Data(mat, (mat_int32_t*)sparse->data,",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_H5ReadDatasetInfo",
    "file": "/src/matio/src/mat73.c",
    "line": 664
   },
   "code": "readcount = ReadInt32Data(mat, (mat_int32_t*)sparse->dat | ReadInt32Data(mat, (mat_int32_t*)sparse->data,",
   "access": {
    "dir": "WRITE",
    "width": 400,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_VarRead4",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "readcount != nelems | readcount != nelems | readcount != nelems",
   "guard_count": 45,
   "control_structures": "IF:301,SWITCH:308,IF:312,IF:317,IF:319,IF:325,ELSE:327,ELSE:332,ELSE:336,IF:338,IF:340,ELSE:346"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "mat",
   "matvar"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/6540087e697ca2b8950bada3d4ca653951b467dc/ARVO-42489565/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_6540087e697c.cpg",
   "testcase_size": 37480
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
   "dedup_token": "memcpy--memcpy--H5D__scatter_mem"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "readcount = ReadDoubleData(mat, (double*)complex_data->Re, matvar->data_type, nelems)",
     "line": 321
    },
    {
     "code": "readcount = ReadDoubleData(mat, (double*)complex_data->Im, matvar->data_type, nelems)",
     "line": 323
    },
    {
     "code": "readcount = ReadDoubleData(mat, (double*)matvar->data, matvar->data_type, nelems)",
     "line": 339
    },
    {
     "code": "readcount = ReadUInt8Data(mat, (mat_uint8_t*)matvar->data, matvar->data_type, nelems)",
     "line": 359
    },
    {
     "code": "readcount = ReadInt32Data(mat, sparse->ir, data_type, sparse->nir)",
     "line": 395
    },
    {
     "code": "readcount = ReadDoubleData(mat, &tmp, data_type, 1)",
     "line": 410
    },
    {
     "code": "readcount = ReadDoubleData(mat, &tmp, data_type, 1)",
     "line": 429
    },
    {
     "code": "readcount = ReadInt32Data(mat, jc, data_type, sparse->nir)",
     "line": 464
    },
    {
     "code": "readcount = ReadDoubleData(mat, &tmp, data_type, 1)",
     "line": 496
    },
    {
     "code": "readcount = ReadDoubleData(mat, (double*)complex_data->Re,",
     "line": 514
    },
    {
     "code": "readcount = ReadDoubleData(mat, &tmp, data_type, 1)",
     "line": 517
    },
    {
     "code": "readcount = ReadDoubleData(mat, (double*)complex_data->Im,",
     "line": 519
    },
    {
     "code": "readcount = ReadDoubleData(mat, &tmp, data_type, 1)",
     "line": 522
    },
    {
     "code": "readcount = ReadSingleData(mat, (float*)complex_data->Re,",
     "line": 528
    },
    {
     "code": "readcount = ReadSingleData(mat, &tmp2, data_type, 1)",
     "line": 531
    },
    {
     "code": "readcount = ReadSingleData(mat, (float*)complex_data->Im,",
     "line": 533
    },
    {
     "code": "readcount = ReadSingleData(mat, &tmp2, data_type, 1)",
     "line": 536
    },
    {
     "code": "readcount = ReadInt32Data(mat, (mat_int32_t*)complex_data->Re,",
     "line": 543
    },
    {
     "code": "readcount = ReadInt32Data(mat, &tmp2, data_type, 1)",
     "line": 546
    },
    {
     "code": "readcount = ReadInt32Data(mat, (mat_int32_t*)complex_data->Im,",
     "line": 548
    },
    {
     "code": "readcount = ReadInt32Data(mat, &tmp2, data_type, 1)",
     "line": 551
    },
    {
     "code": "readcount = ReadInt16Data(mat, (mat_int16_t*)complex_data->Re,",
     "line": 558
    },
    {
     "code": "readcount = ReadInt16Data(mat, &tmp2, data_type, 1)",
     "line": 561
    },
    {
     "code": "readcount = ReadInt16Data(mat, (mat_int16_t*)complex_data->Im,",
     "line": 563
    },
    {
     "code": "readcount = ReadInt16Data(mat, &tmp2, data_type, 1)",
     "line": 566
    },
    {
     "code": "readcount = ReadUInt16Data(mat, (mat_uint16_t*)complex_data->Re,",
     "line": 573
    },
    {
     "code": "readcount = ReadUInt16Data(mat, &tmp2, data_type, 1)",
     "line": 576
    },
    {
     "code": "readcount = ReadUInt16Data(mat, (mat_uint16_t*)complex_data->Im,",
     "line": 578
    },
    {
     "code": "readcount = ReadUInt16Data(mat, &tmp2, data_type, 1)",
     "line": 581
    },
    {
     "code": "readcount = ReadUInt8Data(mat, (mat_uint8_t*)complex_data->Re,",
     "line": 588
    },
    {
     "code": "readcount = ReadUInt8Data(mat, &tmp2, data_type, 1)",
     "line": 591
    },
    {
     "code": "readcount = ReadUInt8Data(mat, (mat_uint8_t*)complex_data->Im,",
     "line": 593
    },
    {
     "code": "readcount = ReadUInt8Data(mat, &tmp2, data_type, 1)",
     "line": 596
    },
    {
     "code": "readcount = ReadDoubleData(mat, (double*)sparse->data,",
     "line": 645
    },
    {
     "code": "readcount = ReadDoubleData(mat, &tmp, data_type, 1)",
     "line": 648
    },
    {
     "code": "readcount = ReadSingleData(mat, (float*)sparse->data,",
     "line": 654
    },
    {
     "code": "readcount = ReadSingleData(mat, &tmp2, data_type, 1)",
     "line": 657
    },
    {
     "code": "readcount = ReadInt32Data(mat, (mat_int32_t*)sparse->data,",
     "line": 664
    },
    {
     "code": "readcount = ReadInt32Data(mat, &tmp2, data_type, 1)",
     "line": 667
    },
    {
     "code": "readcount = ReadInt16Data(mat, (mat_int16_t*)sparse->data,",
     "line": 674
    },
    {
     "code": "readcount = ReadInt16Data(mat, &tmp2, data_type, 1)",
     "line": 677
    },
    {
     "code": "readcount = ReadUInt16Data(mat, (mat_uint16_t*)sparse->data,",
     "line": 684
    },
    {
     "code": "readcount = ReadUInt16Data(mat, &tmp2, data_type, 1)",
     "line": 687
    },
    {
     "code": "readcount = ReadUInt8Data(mat, (mat_uint8_t*)sparse->data,",
     "line": 694
    },
    {
     "code": "readcount = ReadUInt8Data(mat, &tmp2, data_type, 1)",
     "line": 697
    }
   ],
   "entity_decl": {
    "line": 359,
    "type": "size_t"
   },
   "entity_name_cpg": "readcount",
   "func_lines": [
    294,
    746
   ],
   "func_params": {
    "names": [
     "mat",
     "matvar"
    ],
    "types": [
     "mat_t*",
     "matvar_t*"
    ]
   },
   "guards": [
    {
     "code": "NULL != complex_data",
     "line": 319
    },
    {
     "code": "readcount != nelems",
     "line": 322
    },
    {
     "code": "readcount != nelems",
     "line": 324
    },
    {
     "code": "0 == err",
     "line": 325
    },
    {
     "code": "NULL != matvar->data",
     "line": 338
    },
    {
     "code": "readcount != nelems",
     "line": 340
    },
    {
     "code": "NULL != matvar->data",
     "line": 358
    },
    {
     "code": "readcount != nelems",
     "line": 360
    },
    {
     "code": "NULL != matvar->data",
     "line": 375
    },
    {
     "code": "matvar->dims[1] == 4",
     "line": 384
    },
    {
     "code": "sparse->ir != NULL",
     "line": 394
    },
    {
     "code": "readcount != sparse->nir",
     "line": 396
    },
    {
     "code": "i < sparse->nir",
     "line": 402
    },
    {
     "code": "readcount != 1",
     "line": 411
    },
    {
     "code": "tmp > INT_MAX-1",
     "line": 411
    },
    {
     "code": "tmp < 0",
     "line": 411
    },
    {
     "code": "fpos == -1L",
     "line": 421
    },
    {
     "code": "readcount != 1",
     "line": 430
    },
    {
     "code": "tmp > INT_MAX-1",
     "line": 430
    },
    {
     "code": "tmp < 0",
     "line": 430
    },
    {
     "code": "matvar->dims[1] > INT_MAX-1",
     "line": 439
    },
    {
     "code": "sparse->jc != NULL",
     "line": 453
    },
    {
     "code": "jc != NULL",
     "line": 461
    },
    {
     "code": "readcount != sparse->nir",
     "line": 465
    },
    {
     "code": "i < sparse->njc-1",
     "line": 473
    },
    {
     "code": "j < sparse->nir",
     "line": 474
    },
    {
     "code": "readcount != 1",
     "line": 497
    },
    {
     "code": "NULL != complex_data",
     "line": 509
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 516
    },
    {
     "code": "readcount != 1",
     "line": 518
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 521
    },
    {
     "code": "readcount != 1",
     "line": 523
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 530
    },
    {
     "code": "readcount != 1",
     "line": 532
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 535
    },
    {
     "code": "readcount != 1",
     "line": 537
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 545
    },
    {
     "code": "readcount != 1",
     "line": 547
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 550
    },
    {
     "code": "readcount != 1",
     "line": 552
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 560
    },
    {
     "code": "readcount != 1",
     "line": 562
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 565
    },
    {
     "code": "readcount != 1",
     "line": 567
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 575
    },
    {
     "code": "readcount != 1",
     "line": 577
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 580
    },
    {
     "code": "readcount != 1",
     "line": 582
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 590
    },
    {
     "code": "readcount != 1",
     "line": 592
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 595
    },
    {
     "code": "readcount != 1",
     "line": 597
    },
    {
     "code": "sparse->data != NULL",
     "line": 641
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 647
    },
    {
     "code": "readcount != 1",
     "line": 649
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 656
    },
    {
     "code": "readcount != 1",
     "line": 658
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 666
    },
    {
     "code": "readcount != 1",
     "line": 668
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 676
    },
    {
     "code": "readcount != 1",
     "line": 678
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 686
    },
    {
     "code": "readcount != 1",
     "line": 688
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 696
    },
    {
     "code": "readcount != 1",
     "line": 698
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "readcount = ReadInt32Data(mat, (mat_int32_t*)sparse->data,",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "ReadInt32Data(mat, (mat_int32_t*)sparse->data,",
     "name": "ReadInt32Data",
     "nargs": null
    },
    {
     "code": "(mat_int32_t*)sparse->data",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "sparse->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "readcount",
    "mat",
    "sparse"
   ],
   "osv_id": "ARVO-42489565",
   "sites": [
    {
     "args": "matvar->nbytes",
     "callee": "ComplexMalloc",
     "code": "ComplexMalloc(matvar->nbytes)",
     "line": 318
    },
    {
     "args": "complex_data",
     "callee": "ComplexFree",
     "code": "ComplexFree(complex_data)",
     "line": 328
    },
    {
     "args": "matvar->nbytes",
     "callee": "malloc",
     "code": "malloc(matvar->nbytes)",
     "line": 337
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 341
    },
    {
     "args": "matvar->nbytes",
     "callee": "malloc",
     "code": "malloc(matvar->nbytes)",
     "line": 357
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 361
    },
    {
     "args": "matvar->data_size",
     "callee": "malloc",
     "code": "malloc(matvar->data_size)",
     "line": 374
    },
    {
     "args": "readcount",
     "callee": "malloc",
     "code": "malloc(readcount)",
     "line": 393
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 397
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 398
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 405
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 412
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 413
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 422
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 423
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 431
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 432
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 440
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 441
    },
    {
     "args": "readcount",
     "callee": "malloc",
     "code": "malloc(readcount)",
     "line": 452
    },
    {
     "args": "readcount",
     "callee": "malloc",
     "code": "malloc(readcount)",
     "line": 460
    },
    {
     "args": "jc",
     "callee": "free",
     "code": "free(jc)",
     "line": 466
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 467
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 468
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 469
    },
    {
     "args": "jc",
     "callee": "free",
     "code": "free(jc)",
     "line": 478
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 482
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 483
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 484
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 490
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 491
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 498
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 499
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 500
    },
    {
     "args": "sparse->ndata*Mat_SizeOf(data_type)",
     "callee": "ComplexMalloc",
     "code": "ComplexMalloc(sparse->ndata*Mat_SizeOf(data_type))",
     "line": 508
    },
    {
     "args": "complex_data",
     "callee": "ComplexFree",
     "code": "ComplexFree(complex_data)",
     "line": 601
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 602
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 603
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 604
    },
    {
     "args": "complex_data",
     "callee": "ComplexFree",
     "code": "ComplexFree(complex_data)",
     "line": 623
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 624
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 625
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 626
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 632
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 633
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 634
    },
    {
     "args": "sparse->ndata*Mat_SizeOf(data_type)",
     "callee": "malloc",
     "code": "malloc(sparse->ndata*Mat_SizeOf(data_type))",
     "line": 640
    },
    {
     "args": "sparse->data",
     "callee": "free",
     "code": "free(sparse->data)",
     "line": 702
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 703
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 704
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 705
    },
    {
     "args": "sparse->data",
     "callee": "free",
     "code": "free(sparse->data)",
     "line": 718
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 719
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 720
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 721
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 726
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 727
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 728
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_H5ReadDatasetInfo"
  }
 },
 {
  "osv_id": "ARVO-42489779",
  "project": "c-blosc2",
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
    "line": 237
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "Lizard_decompress_LIZv1",
    "file": "/src/c-blosc2/internal-complibs/lizard-1.0/lizard_decompress_liz.h",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Lizard_decompress_LIZv1",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/474ebf151be847186e6bc2c1381a8f7d4beff4dd/ARVO-42489779/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_474ebf151be8.cpg",
   "testcase_size": 78
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
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "Lizard_decompress_LIZv1--Lizard_decompress_generic--Lizard_decompress_safe"
  },
  "deep": {
   "entity_assignments": [],
   "guards": [],
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42489779",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Lizard_decompress_LIZv1"
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