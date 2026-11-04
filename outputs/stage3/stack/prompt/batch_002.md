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
stack-buffer-overflow

## 该类型的机制背景
stack-BOF 的必要条件链：
- N1 对象是函数内栈数组
- N2 数组声明维度
- N3 访问宽度
- N4 是否 VLA（char buf[n]，n 来自输入）
- N5 数组所在栈帧
- N6 写入形式：memcpy 还是逐字节循环
- N7 栈增长方向 + 覆盖对象
- N8 是否经由 alloca / 变长分配

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "osv_id": "ARVO-42475962",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "startTrigger",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 595,
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "code": ".startTrigger               =",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "file": "/src/openthread/src/core/common/message.cpp",
    "line": 595
   },
   "code": ".startTrigger               =",
   "access": {
    "dir": "READ",
    "width": 88,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rfCoreSendTransmitCmd",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:640"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/b694b00951eeeb4986387de1179d55dd38643a87/ARVO-42475962/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_b694b00951ee.cpg",
   "testcase_size": 41
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_offset": 106,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--ot::Message::Write(unsigned short, unsigned short, void const*)--ot::Message::Append(void const*, unsigned short)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": ".startTrigger               =",
     "line": 567
    },
    {
     "code": ".startTrigger               =",
     "line": 595
    },
    {
     "code": ".startTrigger               =",
     "line": 608
    }
   ],
   "entity_name_cpg": "startTrigger",
   "func_lines": [
    560,
    651
   ],
   "func_params": {
    "names": [
     "aPsdu",
     "aLen"
    ],
    "types": [
     "uint8_t*",
     "uint8_t"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": ".startTrigger               =",
     "name": "<operator>.assignment",
     "nargs": null
    }
   ],
   "line_ids": [
    "startTrigger"
   ],
   "osv_id": "ARVO-42475962",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::Message::Write(unsigned short, unsigned short, void const*)"
  }
 },
 {
  "osv_id": "ARVO-42475964",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "response",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/openthread/src/core/thread/mle.cpp",
    "line": 3192,
    "size": null,
    "type": "ResponseTlv"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 3215,
    "fn": "ot::Mle::Mle::HandleParentResponse(ot::Message const&, ot::Ip6::MessageInfo const&, unsigned int)",
    "code": "VerifyOrExit(response.IsValid() &&",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::Mle::Mle::HandleParentResponse(ot::Message const&, ot::Ip6::MessageInfo const&, unsigned int)",
    "file": "/src/openthread/src/core/thread/mle.cpp",
    "line": 3215
   },
   "code": "VerifyOrExit(response.IsValid() &&",
   "access": {
    "dir": "READ",
    "width": 255,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "HandleParentResponse",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "error != OT_ERROR_NONE",
   "guard_count": 1,
   "control_structures": "DO:3208,IF:3208,GOTO:3208,DO:3209,IF:3209,GOTO:3209,DO:3214,IF:3214,GOTO:3214,DO:3215,IF:3215,GOTO:3215"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ResponseTlv",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "aMessage"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/b694b00951eeeb4986387de1179d55dd38643a87/ARVO-42475964/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_b694b00951ee.cpg",
   "testcase_size": 38
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_offset": 42,
   "loc_kind": "stack_frame",
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--bcmp--ot::Mle::Mle::HandleParentRespo"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 3192,
    "type": "ResponseTlv"
   },
   "entity_name_cpg": "response",
   "func_lines": [
    3188,
    3385
   ],
   "func_params": {
    "names": [
     "this",
     "aMessage",
     "aMessageInfo",
     "aKeySequence"
    ],
    "types": [
     "ot.Mle.Mle",
     "Message&",
     "Ip6.MessageInfo&",
     "uint32_t"
    ]
   },
   "guards": [
    {
     "code": "(error = Tlv::GetTlv(aMessage, Tlv::kSourceAddress, sizeof (sourceAddress), sourceAddress)) != 0",
     "line": 3208
    },
    {
     "code": "(error = Tlv::GetTlv(aMessage, Tlv::kResponse, sizeof (response), response)) != 0",
     "line": 3214
    },
    {
     "code": "memcmp(response.GetResponse(), mParentRequest.mChallenge, response.GetLength()) == 0",
     "line": 3215
    },
    {
     "code": "mRole == OT_DEVICE_ROLE_CHILD",
     "line": 3221
    },
    {
     "code": "mParent.GetExtAddress() == extAddress",
     "line": 3221
    },
    {
     "code": "(error = Tlv::GetTlv(aMessage, Tlv::kLeaderData, sizeof (leaderData), leaderData)) != 0",
     "line": 3227
    },
    {
     "code": "(error = Tlv::GetTlv(aMessage, Tlv::kLinkMargin, sizeof (linkMarginTlv), linkMarginTlv)) != 0",
     "line": 3231
    },
    {
     "code": "linkMargin > linkMarginTlv.GetLinkMargin()",
     "line": 3236
    },
    {
     "code": "(error = Tlv::GetTlv(aMessage, Tlv::kConnectivity, sizeof (connectivity), connectivity)) != 0",
     "line": 3244
    },
    {
     "code": "mParentCandidate.GetState() == Neighbor::kStateParentResponse",
     "line": 3297
    },
    {
     "code": "compare != 0",
     "line": 3311
    },
    {
     "code": "(error = Tlv::GetTlv(aMessage, Tlv::kLinkFrameCounter, sizeof (linkFrameCounter), linkFrameCounter)) != 0",
     "line": 3315
    },
    {
     "code": "Tlv::GetTlv(aMessage, Tlv::kMleFrameCounter, sizeof(mleFrameCounter), mleFrameCounter) == OT_ERROR_NONE",
     "line": 3319
    },
    {
     "code": "(error = Tlv::GetTlv(aMessage, Tlv::kChallenge, sizeof (challenge), challenge)) != 0",
     "line": 3350
    },
    {
     "code": "error != OT_ERROR_NONE",
     "line": 3379
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "VerifyOrExit(response.IsValid() &&",
     "name": "VerifyOrExit",
     "nargs": null
    },
    {
     "code": "!(response.IsValid() && memcmp(response.GetResponse(), mParentRequest.mChallenge, response.GetLength()) == 0)",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "response.IsValid() && memcmp(response.GetResponse(), mParentRequest.mChallenge, response.GetLength()) == 0",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "response.IsValid()",
     "name": "IsValid",
     "nargs": 1
    },
    {
     "code": "memcmp(response.GetResponse(), mParentRequest.mChallenge, response.GetLength()) == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "memcmp(response.GetResponse(), mParentRequest.mChallenge, response.GetLength())",
     "name": "memcmp",
     "nargs": 3
    },
    {
     "code": "response.GetResponse()",
     "name": "GetResponse",
     "nargs": 1
    },
    {
     "code": "mParentRequest.mChallenge",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "response.GetLength()",
     "name": "GetLength",
     "nargs": 1
    },
    {
     "code": "error = OT_ERROR_PARSE",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "response",
    "mParentRequest",
    "error",
    "OT_ERROR_PARSE"
   ],
   "osv_id": "ARVO-42475964",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::Mle::Mle::HandleParentResponse(ot::Message const&, ot::Ip6::MessageInfo const&, unsigned int)"
  }
 },
 {
  "osv_id": "ARVO-42476579",
  "project": "wireshark",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 859,
    "fn": "tvb_memcpy",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tvb_memcpy",
    "file": "/src/wireshark/epan/tvbuff.c",
    "line": 859
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 27,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tvb_memcpy",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/81e2d2a668cc06e53168623af19718c03f68ab1d/ARVO-42476579/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_81e2d2a668cc.cpg",
   "testcase_size": 41
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "loc_offset": 1685,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--tvb_memcpy--quic_extract_header"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tvb_memcpy"
  }
 },
 {
  "osv_id": "ARVO-42476618",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "startTrigger",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 638,
    "fn": "ot::NetworkData::Leader::IsStableUpdated(unsigned char*, unsigned char, unsigned char*, unsigned char)",
    "code": ".startTrigger               =",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::NetworkData::Leader::IsStableUpdated(unsigned char*, unsigned char, unsigned char*, unsigned char)",
    "file": "/src/openthread/src/core/thread/network_data_leader_ftd.cpp",
    "line": 638
   },
   "code": ".startTrigger               =",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rfCoreSendTransmitCmd",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:670"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/f5ee3a5e65a8c1bddae503e31a1aa51684931f00/ARVO-42476618/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_f5ee3a5e65a8.cpg",
   "testcase_size": 643
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_offset": 289,
   "loc_kind": "stack_frame",
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--__interceptor_bcmp--ot::NetworkData::"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": ".startTrigger               =",
     "line": 597
    },
    {
     "code": ".startTrigger               =",
     "line": 625
    },
    {
     "code": ".startTrigger               =",
     "line": 638
    }
   ],
   "entity_name_cpg": "startTrigger",
   "func_lines": [
    590,
    681
   ],
   "func_params": {
    "names": [
     "aPsdu",
     "aLen"
    ],
    "types": [
     "uint8_t*",
     "uint8_t"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": ".startTrigger               =",
     "name": "<operator>.assignment",
     "nargs": null
    }
   ],
   "line_ids": [
    "startTrigger"
   ],
   "osv_id": "ARVO-42476618",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::NetworkData::Leader::IsStableUpdated(unsigned char*, unsigned char, unsigned char*, unsigned char)"
  }
 },
 {
  "osv_id": "ARVO-42477145",
  "project": "zstd",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 2529,
    "fn": "ZSTD_decodeLiteralsBlock",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_decodeLiteralsBlock",
    "file": "/src/zstd/lib/legacy/zstd_v03.c",
    "line": 2529
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 131082,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ZSTD_decodeLiteralsBlock",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/zstd/address/9ad7ea44ec9644c618c2e82be5960d868e48745d/ARVO-42477145/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/zstd_9ad7ea44ec96.cpg",
   "testcase_size": 131102
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 141416,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--ZSTD_decodeLiteralsBlock--ZSTD_decompressBlock"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    430,
    567
   ],
   "func_params": {
    "names": [
     "dctx",
     "src",
     "srcSize"
    ],
    "types": [
     "ZSTD_DCtx*",
     "void*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "srcSize < MIN_CBLOCK_SIZE",
     "line": 432
    },
    {
     "code": "dctx->litEntropy == 0",
     "line": 441
    },
    {
     "code": "srcSize < 5",
     "line": 445
    },
    {
     "code": "litSize > ZSTD_BLOCKSIZE_ABSOLUTEMAX",
     "line": 475
    },
    {
     "code": "litCSize + lhSize > srcSize",
     "line": 477
    },
    {
     "code": "litEncType == set_repeat",
     "line": 481
    },
    {
     "code": "litEncType == set_compressed",
     "line": 494
    },
    {
     "code": "lhSize + litSize + WILDCOPY_OVERLENGTH > srcSize",
     "line": 520
    },
    {
     "code": "litSize + lhSize > srcSize",
     "line": 521
    },
    {
     "code": "srcSize < 4",
     "line": 552
    },
    {
     "code": "litSize > ZSTD_BLOCKSIZE_ABSOLUTEMAX",
     "line": 556
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42477145",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ZSTD_decodeLiteralsBlock"
  }
 },
 {
  "osv_id": "ARVO-42477888",
  "project": "matio",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "tmp",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 130,
    "type": "union",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 132,
    "fn": "Mat_uint32Swap",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_uint32Swap",
    "file": "/src/matio/src/endian.c",
    "line": 132
   },
   "code": "tmp.i4 = *a",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_uint32Swap",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/matio/address/6540087e697ca2b8950bada3d4ca653951b467dc/ARVO-42477888/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_6540087e697c.cpg",
   "testcase_size": 607
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_offset": 128,
   "loc_kind": "stack_frame",
   "dedup_token": "Mat_uint32Swap--Mat_VarReadNextInfo5--Mat_GetDir"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "tmp.i4 = *a",
     "line": 132
    }
   ],
   "entity_decl": {
    "line": 130,
    "type": "union"
   },
   "entity_name_cpg": "tmp",
   "func_lines": [
    123,
    140
   ],
   "func_params": {
    "names": [
     "a"
    ],
    "types": [
     "mat_uint32_t*"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "tmp.i4 = *a",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "tmp.i4",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "*a",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "tmp",
    "a"
   ],
   "osv_id": "ARVO-42477888",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_uint32Swap"
  }
 },
 {
  "osv_id": "ARVO-42478091",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "error",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/openthread/src/core/thread/network_data_leader_ftd.cpp",
    "line": 322,
    "size": null,
    "type": "otError"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 351,
    "fn": "ot::NetworkData::Leader::SendCommissioningGetResponse(ot::Coap::Message const&, ot::Ip6::MessageInfo const&, unsigned char const*, unsigned char)",
    "code": "error = otMessageAppend(message, payload, (uint16_t)strl | otMessageAppend(message, payload, (uint16_t)strlen(paylo | (uint16_t)strlen(payload) | strlen(payload)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::NetworkData::Leader::SendCommissioningGetResponse(ot::Coap::Message const&, ot::Ip6::MessageInfo const&, unsigned char const*, unsigned char)",
    "file": "/src/openthread/src/core/thread/network_data_leader_ftd.cpp",
    "line": 351
   },
   "code": "error = otMessageAppend(message, payload, (uint16_t)strl | otMessageAppend(message, payload, (uint16_t)strlen(paylo | (uint16_t)strlen(payload) | strlen(payload)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "applicationTick",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "message != NULL | error == OT_ERROR_NONE | error == OT_ERROR_NONE",
   "guard_count": 4,
   "control_structures": "IF:328,IF:339,IF:349,IF:353,IF:357,IF:364"
  },
  "call_chain": [],
  "types": {
   "entity_type": "otError",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/bb56fa906a09408acc3787ae54969270e43a2454/ARVO-42478091/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_bb56fa906a09.cpg",
   "testcase_size": 33
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_offset": 302,
   "loc_kind": "stack_frame",
   "dedup_token": "ot::NetworkData::Leader::SendCommissioningGetResponse(ot::Coap::Message const&, ot::Ip6::MessageInfo const&, unsigned char const*, unsigned char)--ot::NetworkDa"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "error = 0",
     "line": 322
    },
    {
     "code": "error = otMessageAppend(message, payload, (uint16_t)strlen(payload))",
     "line": 351
    },
    {
     "code": "error = otUdpSend(&sMtdSocket, message, &messageInfo)",
     "line": 355
    }
   ],
   "entity_decl": {
    "line": 322,
    "type": "otError"
   },
   "entity_name_cpg": "error",
   "func_lines": [
    320,
    369
   ],
   "func_params": {
    "names": [],
    "types": [
     "void"
    ]
   },
   "guards": [
    {
     "code": "sRxOnIdleButtonPressed == true",
     "line": 328
    },
    {
     "code": "sButtonPressed == true",
     "line": 339
    },
    {
     "code": "message != NULL",
     "line": 349
    },
    {
     "code": "error == OT_ERROR_NONE",
     "line": 353
    },
    {
     "code": "error == OT_ERROR_NONE",
     "line": 357
    },
    {
     "code": "message != NULL",
     "line": 364
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "error = otMessageAppend(message, payload, (uint16_t)strlen(payload))",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "otMessageAppend(message, payload, (uint16_t)strlen(payload))",
     "name": "otMessageAppend",
     "nargs": 3
    },
    {
     "code": "(uint16_t)strlen(payload)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "strlen(payload)",
     "name": "strlen",
     "nargs": 1
    }
   ],
   "line_ids": [
    "error",
    "message",
    "payload"
   ],
   "osv_id": "ARVO-42478091",
   "sites": [
    {
     "args": "message",
     "callee": "otMessageFree",
     "code": "otMessageFree(message)",
     "line": 366
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::NetworkData::Leader::SendCommissioningGetResponse(ot::Coap::Message const&, ot::Ip6::MessageInfo const&, unsigned char const*, unsigned char)"
  }
 },
 {
  "osv_id": "ARVO-42478129",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "error",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/openthread/src/core/common/message.cpp",
    "line": 526,
    "size": null,
    "type": "otError"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 526,
    "fn": "ot::Message::Read(unsigned short, unsigned short, void*) const",
    "code": "error = OT_ERROR_NONE",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::Message::Read(unsigned short, unsigned short, void*) const",
    "file": "/src/openthread/src/core/common/message.cpp",
    "line": 526
   },
   "code": "error = OT_ERROR_NONE",
   "access": {
    "dir": "WRITE",
    "width": 147,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "otPlatRadioDisable",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:528,IF:528,GOTO:528,DO:529,IF:529,GOTO:529"
  },
  "call_chain": [],
  "types": {
   "entity_type": "otError",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/bb56fa906a09408acc3787ae54969270e43a2454/ARVO-42478129/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_bb56fa906a09.cpg",
   "testcase_size": 1089
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_offset": 302,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--ot::Message::Read(unsigned short, unsigned short, void*) const--ot::NetworkData::Leader::HandleCommissioningGet(ot::Coap::Message&, ot::Ip6::Mess"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "error = OT_ERROR_NONE",
     "line": 526
    },
    {
     "code": "error = OT_ERROR_INVALID_STATE",
     "line": 529
    }
   ],
   "entity_decl": {
    "line": 526,
    "type": "otError"
   },
   "entity_name_cpg": "error",
   "func_lines": [
    524,
    535
   ],
   "func_params": {
    "names": [
     "aInstance"
    ],
    "types": [
     "otInstance*"
    ]
   },
   "guards": [
    {
     "code": "sState == OT_RADIO_STATE_SLEEP",
     "line": 529
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "error = OT_ERROR_NONE",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "error",
    "OT_ERROR_NONE"
   ],
   "osv_id": "ARVO-42478129",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::Message::Read(unsigned short, unsigned short, void*) const"
  }
 },
 {
  "osv_id": "ARVO-42479513",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "ctx",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/tests/fuzzing/fuzz_pkcs15_reader.c",
    "line": 83,
    "size": null,
    "type": "sc_context_t*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 129,
    "fn": "fuzz_reader_transmit",
    "code": "sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU  | _sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "fuzz_reader_transmit",
    "file": "/src/opensc/src/tests/fuzzing/fuzz_pkcs15_reader.c",
    "line": 129
   },
   "code": "sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU  | _sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU",
   "access": {
    "dir": "WRITE",
    "width": 30,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_apdu2bytes",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:90,SWITCH:98,IF:101,BREAK:103,BREAK:106,IF:108,ELSE:111,BREAK:117,BREAK:121,IF:123,IF:126,ELSE:133"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_context_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ctx"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/61cd7fcdb2fdc9214b431abb631b202314dcc32f/ARVO-42479513/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_61cd7fcdb2fd.cpg",
   "testcase_size": 330
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 4159,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--fuzz_reader_transmit--sc_single_transmit"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 83,
    "type": "sc_context_t*"
   },
   "entity_name_cpg": "ctx",
   "func_lines": [
    83,
    172
   ],
   "func_params": {
    "names": [
     "ctx",
     "apdu",
     "proto",
     "out",
     "outlen"
    ],
    "types": [
     "sc_context_t*",
     "sc_apdu_t*",
     "unsigned int",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "out == NULL",
     "line": 90
    },
    {
     "code": "outlen < len",
     "line": 90
    },
    {
     "code": "proto == SC_PROTO_T0",
     "line": 101
    },
    {
     "code": "proto == SC_PROTO_T0",
     "line": 108
    },
    {
     "code": "proto == SC_PROTO_T0",
     "line": 123
    },
    {
     "code": "apdu->lc > 255",
     "line": 126
    },
    {
     "code": "proto != SC_PROTO_T0",
     "line": 146
    },
    {
     "code": "proto == SC_PROTO_T0",
     "line": 150
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU (need ENVELOPE)\")",
     "name": "sc_log",
     "nargs": 0
    },
    {
     "code": "_sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU (need ENVELOPE)\")",
     "name": "_sc_log",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ctx"
   ],
   "osv_id": "ARVO-42479513",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "fuzz_reader_transmit"
  }
 },
 {
  "osv_id": "ARVO-42480178",
  "project": "ndpi",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "realm_str",
   "kind": "array",
   "storage": "stack",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 142,
    "size": null,
    "type": "char[24]"
   }
  },
  "alloc": {
   "size_expr_cpg": "24",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 116,
    "fn": "ndpi_search_kerberos",
    "code": "realm_str[realm_len] = '\\0' | realm_str[realm_len]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_kerberos",
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 116
   },
   "code": "realm_str[realm_len] = '\\0' | realm_str[realm_len]",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_kerberos",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "realm_len > sizeof(realm_str)-1 | i<realm_len | realm_len > sizeof(realm_str)-1",
   "guard_count": 4,
   "control_structures": "IF:48,IF:52,IF:58,IF:59,IF:62,ELSE:65,IF:67,IF:72,IF:79,IF:82,IF:85,IF:89"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[24]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/803dc6ff779b44be1264380b800bb2904b9de692/ARVO-42480178/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_803dc6ff779b.cpg",
   "testcase_size": 170
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 120,
   "loc_kind": "stack_frame",
   "dedup_token": "ndpi_search_kerberos--check_ndpi_tcp_flow_func--ndpi_check_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "realm_str[24]",
     "line": 110
    },
    {
     "code": "realm_str[realm_len] = '\\0'",
     "line": 116
    },
    {
     "code": "realm_str[i] = tolower(realm_str[i])",
     "line": 117
    },
    {
     "code": "realm_str[24]",
     "line": 142
    },
    {
     "code": "realm_str[realm_len] = '\\0'",
     "line": 148
    },
    {
     "code": "realm_str[i] = tolower(realm_str[i])",
     "line": 149
    }
   ],
   "entity_decl": {
    "line": 110,
    "type": "char[24]"
   },
   "entity_name_cpg": "realm_str",
   "func_lines": [
    41,
    217
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
     "code": "kerberos_len < 1514",
     "line": 52
    },
    {
     "code": "packet->payload_packet_len > 128",
     "line": 59
    },
    {
     "code": "packet->payload[14] == 0x05",
     "line": 62
    },
    {
     "code": "packet->payload[koffset] == 0x0a",
     "line": 67
    },
    {
     "code": "packet->payload[koffset] == 0x0c",
     "line": 67
    },
    {
     "code": "packet->payload[koffset] == 0x0d",
     "line": 67
    },
    {
     "code": "packet->payload[koffset] == 0x0e",
     "line": 67
    },
    {
     "code": "packet->payload[koffset] == 0x0a",
     "line": 72
    },
    {
     "code": "body_offset < packet->payload_packet_len",
     "line": 79
    },
    {
     "code": "name_offset < packet->payload_packet_len",
     "line": 82
    },
    {
     "code": "(cname_len+name_offset) < packet->payload_packet_len",
     "line": 85
    },
    {
     "code": "cname_len > sizeof(cname_str)-1",
     "line": 89
    },
    {
     "code": "i<cname_len",
     "line": 94
    },
    {
     "code": "cname_str[cname_len-1] == '$'",
     "line": 101
    },
    {
     "code": "(realm_offset+realm_len) < packet->payload_packet_len",
     "line": 109
    },
    {
     "code": "realm_len > sizeof(realm_str)-1",
     "line": 112
    },
    {
     "code": "i<realm_len",
     "line": 117
    },
    {
     "code": "packet->payload[koffset] == 0x0c",
     "line": 127
    },
    {
     "code": "body_offset < packet->payload_packet_len",
     "line": 134
    },
    {
     "code": "name_offset < packet->payload_packet_len",
     "line": 137
    },
    {
     "code": "(realm_len+name_offset) < packet->payload_packet_len",
     "line": 140
    },
    {
     "code": "realm_len > sizeof(realm_str)-1",
     "line": 144
    },
    {
     "code": "i<realm_len",
     "line": 149
    },
    {
     "code": "packet->payload[koffset] == 0x0d",
     "line": 161
    },
    {
     "code": "cname_offset < packet->payload_packet_len",
     "line": 169
    },
    {
     "code": "(cname_offset+cname_offset) < packet->payload_packet_len",
     "line": 172
    },
    {
     "code": "cname_len > sizeof(cname_str)-1",
     "line": 176
    },
    {
     "code": "i<cname_len",
     "line": 181
    },
    {
     "code": "cname_str[cname_len-1] == '$'",
     "line": 187
    },
    {
     "code": "packet->payload_packet_len > 21",
     "line": 201
    },
    {
     "code": "packet->payload[16] == 0x05",
     "line": 202
    },
    {
     "code": "packet->payload[21] == 0x0a",
     "line": 203
    },
    {
     "code": "packet->payload[21] == 0x0c",
     "line": 204
    },
    {
     "code": "packet->payload[21] == 0x0d",
     "line": 204
    },
    {
     "code": "packet->payload[21] == 0x0e",
     "line": 204
    },
    {
     "code": "flow->protos.kerberos.domain[0] != '\\0'",
     "line": 211
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "realm_str[realm_len] = '\\0'",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "realm_str[realm_len]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "realm_str",
    "realm_len"
   ],
   "osv_id": "ARVO-42480178",
   "sites": [
    {
     "args": "24",
     "callee": "<operator>.alloc",
     "code": "cname_str[24]",
     "line": 87
    },
    {
     "args": "24",
     "callee": "<operator>.alloc",
     "code": "realm_str[24]",
     "line": 110
    },
    {
     "args": "24",
     "callee": "<operator>.alloc",
     "code": "realm_str[24]",
     "line": 142
    },
    {
     "args": "24",
     "callee": "<operator>.alloc",
     "code": "cname_str[24]",
     "line": 173
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_kerberos"
  }
 },
 {
  "osv_id": "ARVO-42480263",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "obj",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-syn.c",
    "line": 389,
    "size": null,
    "type": "sc_pkcs15_object_t*"
   }
  },
  "alloc": {
   "size_expr_cpg": "1 ;; sizeof(*obj)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc(1, sizeof(*obj))",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "calloc",
    "line": 393,
    "origin": "cpg",
    "args": "1 ;; sizeof(*obj)"
   },
   {
    "code": "free(obj)",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "free",
    "line": 422,
    "origin": "cpg",
    "args": "obj"
   },
   {
    "code": "calloc(1, data_len)",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "calloc",
    "line": 426,
    "origin": "cpg",
    "args": "1 ;; data_len"
   },
   {
    "code": "free(obj)",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "free",
    "line": 428,
    "origin": "cpg",
    "args": "obj"
   },
   {
    "kind": "unknown",
    "line": 431,
    "fn": "sc_pkcs15emu_object_add",
    "code": "memcpy(obj->data, data, data_len) | obj->data",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15emu_object_add",
    "file": "/src/opensc/src/libopensc/pkcs15-syn.c",
    "line": 431
   },
   "code": "memcpy(obj->data, data, data_len) | obj->data",
   "access": {
    "dir": "READ",
    "width": 464,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_pkcs15emu_object_add",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:394,SWITCH:399,BREAK:403,BREAK:407,BREAK:411,BREAK:415,BREAK:419,IF:427"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_pkcs15_object_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "p15card",
   "type",
   "in_obj",
   "data"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/4c67bbf3838aba9cf7e00697403d7b860bbae30b/ARVO-42480263/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_4c67bbf3838a.cpg",
   "testcase_size": 294
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "free_related": {
   "free_sites_in_func": [
    422,
    428
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 8152,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--sc_pkcs15emu_object_add--sc_pkcs15emu_coolkey_init"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "obj = calloc(1, sizeof(*obj))",
     "line": 393
    },
    {
     "code": "obj->type  = type",
     "line": 397
    },
    {
     "code": "obj->data = calloc(1, data_len)",
     "line": 426
    },
    {
     "code": "obj->df = sc_pkcs15emu_get_df(p15card, df_type)",
     "line": 433
    }
   ],
   "entity_decl": {
    "line": 389,
    "type": "sc_pkcs15_object_t*"
   },
   "entity_name_cpg": "obj",
   "func_lines": [
    386,
    437
   ],
   "func_params": {
    "names": [
     "p15card",
     "type",
     "in_obj",
     "data"
    ],
    "types": [
     "sc_pkcs15_card_t*",
     "unsigned int",
     "sc_pkcs15_object_t*",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "obj->data == NULL",
     "line": 427
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(obj->data, data, data_len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "obj->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "obj",
    "data",
    "data_len"
   ],
   "osv_id": "ARVO-42480263",
   "sites": [
    {
     "args": "1 ;; sizeof(*obj)",
     "callee": "calloc",
     "code": "calloc(1, sizeof(*obj))",
     "line": 393
    },
    {
     "args": "obj",
     "callee": "free",
     "code": "free(obj)",
     "line": 422
    },
    {
     "args": "1 ;; data_len",
     "callee": "calloc",
     "code": "calloc(1, data_len)",
     "line": 426
    },
    {
     "args": "obj",
     "callee": "free",
     "code": "free(obj)",
     "line": 428
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "sc_pkcs15emu_object_add",
   "use_fn": "sc_pkcs15emu_object_add"
  }
 },
 {
  "osv_id": "ARVO-42480359",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "triggerType",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 569,
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "code": ".triggerType            = TRIG_NOW",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "file": "/src/openthread/src/core/common/message.cpp",
    "line": 569
   },
   "code": ".triggerType            = TRIG_NOW",
   "access": {
    "dir": "READ",
    "width": 11,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rfCoreSendTransmitCmd",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:640"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/082c1c79f5a84aeda8eee4f87d9f261089fb9e78/ARVO-42480359/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_082c1c79f5a8.cpg",
   "testcase_size": 56
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_offset": 90,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--ot::Message::Write(unsigned short, unsigned short, void const*)--ot::Message::Append(void const*, unsigned short)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": ".triggerType            = TRIG_NOW",
     "line": 569
    },
    {
     "code": ".triggerType            = TRIG_NEVER",
     "line": 587
    },
    {
     "code": ".triggerType            = TRIG_NOW",
     "line": 597
    },
    {
     "code": ".triggerType            = TRIG_NOW",
     "line": 610
    },
    {
     "code": ".triggerType            = TRIG_REL_START",
     "line": 614
    }
   ],
   "entity_name_cpg": "triggerType",
   "func_lines": [
    560,
    651
   ],
   "func_params": {
    "names": [
     "aPsdu",
     "aLen"
    ],
    "types": [
     "uint8_t*",
     "uint8_t"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": ".triggerType            = TRIG_NOW",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "triggerType",
    "TRIG_NOW"
   ],
   "osv_id": "ARVO-42480359",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::Message::Write(unsigned short, unsigned short, void const*)"
  }
 },
 {
  "osv_id": "ARVO-42480412",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "sTxCmdChainDone",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1121,
    "fn": "ot::MeshCoP::Commissioner::GeneratePskc(char const*, char const*, ot::Mac::ExtendedPanId const&, ot::Pskc&)",
    "code": "sTxCmdChainDone = true",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::MeshCoP::Commissioner::GeneratePskc(char const*, char const*, ot::Mac::ExtendedPanId const&, ot::Pskc&)",
    "file": "/src/openthread/src/core/meshcop/commissioner.cpp",
    "line": 1121
   },
   "code": "sTxCmdChainDone = true",
   "access": {
    "dir": "WRITE",
    "width": 17,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "RFCCPE0IntHandler",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1070,IF:1074,ELSE:1079,IF:1079,IF:1085,IF:1089,IF:1091,SWITCH:1094,IF:1097,ELSE:1104,BREAK:1110,BREAK:1116"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/88df5fb4ac8bd177fcbb1323eb8494d8fe7b610c/ARVO-42480412/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_88df5fb4ac8b.cpg",
   "testcase_size": 43
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_offset": 62,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--ot::MeshCoP::Commissioner::GeneratePskc(char const*, char const*, ot::Mac::ExtendedPanId const&, ot::Pskc&)--ot::Ncp::NcpBase::HandlePropertySet_"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "sTxCmdChainDone = true",
     "line": 1107
    },
    {
     "code": "sTxCmdChainDone = true",
     "line": 1115
    },
    {
     "code": "sTxCmdChainDone = true",
     "line": 1121
    },
    {
     "code": "sTxCmdChainDone = true",
     "line": 1127
    },
    {
     "code": "sTxCmdChainDone = true",
     "line": 1161
    }
   ],
   "entity_name_cpg": "sTxCmdChainDone",
   "func_lines": [
    1068,
    1165
   ],
   "func_params": {
    "names": [],
    "types": [
     "void"
    ]
   },
   "guards": [
    {
     "code": "sState == cc1352_stateReceive",
     "line": 1074
    },
    {
     "code": "sReceiveCmd.status != ACTIVE",
     "line": 1074
    },
    {
     "code": "sReceiveCmd.status != IEEE_SUSPENDED",
     "line": 1074
    },
    {
     "code": "sState == cc1352_stateEdScan",
     "line": 1079
    },
    {
     "code": "sState == cc1352_stateTransmit",
     "line": 1089
    },
    {
     "code": "sTransmitRetryCount < IEEE802154_MAC_MAX_FRAMES_RETRIES",
     "line": 1097
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "sTxCmdChainDone = true",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "sTxCmdChainDone",
    "true"
   ],
   "osv_id": "ARVO-42480412",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::MeshCoP::Commissioner::GeneratePskc(char const*, char const*, ot::Mac::ExtendedPanId const&, ot::Pskc&)"
  }
 },
 {
  "osv_id": "ARVO-42480587",
  "project": "ndpi",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "ja3_str_len",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 207,
    "size": null,
    "type": "u_int16_t"
   }
  },
  "alloc": {
   "size_expr_cpg": "JA3_STR_LEN",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 719,
    "fn": "getTLScertificate",
    "code": "ja3_str_len += snprintf(&ja3_str[ja3_str_len], sizeof(ja | snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_ | &ja3_str[ja3_str_len] | ja3_str[ja3_str_len]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "getTLScertificate",
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 719
   },
   "code": "ja3_str_len += snprintf(&ja3_str[ja3_str_len], sizeof(ja | snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_ | &ja3_str[ja3_str_len] | ja3_str[ja3_str_len]",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "getTLScertificate",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:213,IF:215,IF:238,IF:242,ELSE:246,IF:257,IF:261,IF:268,IF:274,ELSE:277,IF:281,IF:295"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/bf5e9b7b0b83b93116786e7b982dbe4db3645ffa/ARVO-42480587/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_bf5e9b7b0b83.cpg",
   "testcase_size": 21569
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 2098,
   "loc_kind": "stack_frame",
   "dedup_token": "vsnprintf--snprintf--getTLScertificate"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ja3_str_len = snprintf(ja3_str, sizeof(ja3_str), \"%u,\", ja3.tls_handshake_version)",
     "line": 353
    },
    {
     "code": "ja3_str_len = snprintf(ja3_str, sizeof(ja3_str), \"%u,\", ja3.tls_handshake_version)",
     "line": 696
    }
   ],
   "entity_decl": {
    "line": 207,
    "type": "u_int16_t"
   },
   "entity_name_cpg": "ja3_str_len",
   "func_lines": [
    201,
    757
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
     "code": "(offset + 1) < packet->payload_packet_len",
     "line": 312
    },
    {
     "code": "i<extension_len",
     "line": 322
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 330
    },
    {
     "code": "extension_id == 43",
     "line": 338
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 355
    },
    {
     "code": "i > 0",
     "line": 356
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 365
    },
    {
     "code": "i > 0",
     "line": 366
    },
    {
     "code": "i<16",
     "line": 383
    },
    {
     "code": "i < packet->payload_packet_len-3",
     "line": 398
    },
    {
     "code": "packet->payload[i] == 0x04",
     "line": 399
    },
    {
     "code": "packet->payload[i+1] == 0x03",
     "line": 399
    },
    {
     "code": "packet->payload[i+2] == 0x0c",
     "line": 399
    },
    {
     "code": "packet->payload[i] == 0x04",
     "line": 400
    },
    {
     "code": "packet->payload[i+1] == 0x03",
     "line": 400
    },
    {
     "code": "packet->payload[i+2] == 0x13",
     "line": 400
    },
    {
     "code": "packet->payload[i] == 0x55",
     "line": 401
    },
    {
     "code": "packet->payload[i+1] == 0x04",
     "line": 401
    },
    {
     "code": "packet->payload[i+2] == 0x03",
     "line": 401
    },
    {
     "code": "packet->payload[i] == 0x55",
     "line": 404
    },
    {
     "code": "num_found != 2",
     "line": 407
    },
    {
     "code": "(server_len+i+3) < packet->payload_packet_len",
     "line": 410
    },
    {
     "code": "begin < server_len",
     "line": 414
    },
    {
     "code": "j<len",
     "line": 427
    },
    {
     "code": "buffer[j] == '.'",
     "line": 431
    },
    {
     "code": "subproto != NDPI_PROTOCOL_UNKNOWN",
     "line": 456
    },
    {
     "code": "handshake_protocol == 0x01",
     "line": 465
    },
    {
     "code": "i<cipher_len",
     "line": 501
    },
    {
     "code": "*id == 0",
     "line": 507
    },
    {
     "code": "packet->payload[cipher_offset+i] != packet->payload[cipher_offset+i+1]",
     "line": 507
    },
    {
     "code": "ja3.num_cipher < MAX_NUM_JA3",
     "line": 513
    },
    {
     "code": "offset < total_len",
     "line": 536
    },
    {
     "code": "offset < total_len",
     "line": 551
    },
    {
     "code": "extension_offset < extensions_len",
     "line": 565
    },
    {
     "code": "extension_id == 0",
     "line": 578
    },
    {
     "code": "packet->payload[extn_off] != packet->payload[extn_off+1]",
     "line": 578
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 581
    },
    {
     "code": "extension_id == 0",
     "line": 591
    },
    {
     "code": "(offset+extension_offset+5+len) < packet->payload_packet_len",
     "line": 597
    },
    {
     "code": "extension_id == 10",
     "line": 608
    },
    {
     "code": "i<extension_len-2",
     "line": 616
    },
    {
     "code": "s_group == 0",
     "line": 622
    },
    {
     "code": "packet->payload[s_offset+i] != packet->payload[s_offset+i+1]",
     "line": 622
    },
    {
     "code": "ja3.num_elliptic_curve < MAX_NUM_JA3",
     "line": 624
    },
    {
     "code": "extension_id == 11",
     "line": 642
    },
    {
     "code": "(s_offset+extension_len) < total_len",
     "line": 648
    },
    {
     "code": "i<extension_len-1",
     "line": 649
    },
    {
     "code": "ja3.num_elliptic_curve_point_format < MAX_NUM_JA3",
     "line": 656
    },
    {
     "code": "extension_id == 43",
     "line": 671
    },
    {
     "code": "version_len == (extension_len-1)",
     "line": 674
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 698
    },
    {
     "code": "i > 0",
     "line": 700
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 707
    },
    {
     "code": "i > 0",
     "line": 709
    },
    {
     "code": "i<ja3.num_elliptic_curve",
     "line": 715
    },
    {
     "code": "i > 0",
     "line": 717
    },
    {
     "code": "i<ja3.num_elliptic_curve_point_format",
     "line": 721
    },
    {
     "code": "i > 0",
     "line": 723
    },
    {
     "code": "i<16",
     "line": 733
    },
    {
     "code": "offset == total_len",
     "line": 745
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "ja3_str_len += snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \",\")",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \",\")",
     "name": "snprintf",
     "nargs": 3
    },
    {
     "code": "&ja3_str[ja3_str_len]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "ja3_str[ja3_str_len]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "sizeof(ja3_str)-ja3_str_len",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "sizeof(ja3_str)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "ja3_str_len",
    "ja3_str"
   ],
   "osv_id": "ARVO-42480587",
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
  "osv_id": "ARVO-42480591",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "oid",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-openpgp.c",
    "line": 694,
    "size": null,
    "type": "sc_object_id"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 725,
    "fn": "pgp_parse_algo_attr_blob",
    "code": "oid.value[j] = blob->data[j+1] | oid.value[j] | oid.value | blob->data[j+1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "pgp_parse_algo_attr_blob",
    "file": "/src/opensc/src/libopensc/card-openpgp.c",
    "line": 725
   },
   "code": "oid.value[j] = blob->data[j+1] | oid.value[j] | oid.value | blob->data[j+1]",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "pgp_parse_algo_attr_blob",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "blob == NULL | j < (blob->len-1)",
   "guard_count": 2,
   "control_structures": "IF:697,SWITCH:703,IF:705,BREAK:715,FOR:724,FOR:729,IF:730,BREAK:733,BREAK:736"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_object_id",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "blob"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/ee78b0b80514460936c585c3ff5fc477338ae371/ARVO-42480591/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_ee78b0b80514.cpg",
   "testcase_size": 368
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 96,
   "loc_kind": "stack_frame",
   "dedup_token": "pgp_parse_algo_attr_blob--pgp_get_card_features--pgp_init"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "oid.value[j] = blob->data[j+1]",
     "line": 725
    }
   ],
   "entity_decl": {
    "line": 694,
    "type": "sc_object_id"
   },
   "entity_name_cpg": "oid",
   "func_lines": [
    691,
    742
   ],
   "func_params": {
    "names": [
     "blob",
     "key_info"
    ],
    "types": [
     "pgp_blob_t*",
     "sc_cardctl_openpgp_keygen_info_t*"
    ]
   },
   "guards": [
    {
     "code": "blob == NULL",
     "line": 697
    },
    {
     "code": "blob->data == NULL",
     "line": 697
    },
    {
     "code": "blob->len == 0",
     "line": 697
    },
    {
     "code": "blob->id < 0x00c1",
     "line": 698
    },
    {
     "code": "blob->id > 0x00c3",
     "line": 698
    },
    {
     "code": "key_info == NULL",
     "line": 698
    },
    {
     "code": "blob->len < 5",
     "line": 705
    },
    {
     "code": "blob->len > 5",
     "line": 712
    },
    {
     "code": "j < (blob->len-1)",
     "line": 724
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "oid.value[j] = blob->data[j+1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "oid.value[j]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "oid.value",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "blob->data[j+1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "blob->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "j+1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "oid",
    "j",
    "blob"
   ],
   "osv_id": "ARVO-42480591",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "pgp_parse_algo_attr_blob"
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