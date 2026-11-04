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
  "osv_id": "ARVO-42524167",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "DRIVER_DATA_PATH",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {
   "size_expr_cpg": "ARRAYSIZE(WaitEvents)",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 914,
    "fn": "ot::NetworkData::ServerTlv::GetServer16() const",
    "code": "LogError(DRIVER_DATA_PATH, \"otAppendMessage failed with",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::NetworkData::ServerTlv::GetServer16() const",
    "file": "/src/openthread/src/core/thread/network_data_tlvs.hpp",
    "line": 914
   },
   "code": "LogError(DRIVER_DATA_PATH, \"otAppendMessage failed with",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "otLwfEventWorkerThread",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "error != OT_ERROR_NONE | error != OT_ERROR_NONE",
   "guard_count": 2,
   "control_structures": "IF:737,IF:764,GOTO:767,IF:779,GOTO:782,FOR:801,IF:805,ELSE:815,IF:819,ELSE:833,IF:844,BREAK:847"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "Context"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/68a605f22e579ae45ab1d8221faa2d45e8668e05/ARVO-42524167/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_68a605f22e57.cpg",
   "testcase_size": 425
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
   "dedup_token": "ot::NetworkData::ServerTlv::GetServer16() const--ot::NetworkData::Leader::RlocLookup(unsigned short, bool&, bool&, unsigned char*, unsigned char)--ot::NetworkDa"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "DRIVER_DATA_PATH",
   "func_lines": [
    709,
    1114
   ],
   "func_params": {
    "names": [
     "Context"
    ],
    "types": [
     "PVOID"
    ]
   },
   "guards": [
    {
     "code": "MessageBuffer == NULL",
     "line": 737
    },
    {
     "code": "pFilter->otInstanceSize != 0",
     "line": 757
    },
    {
     "code": "pFilter == NULL",
     "line": 764
    },
    {
     "code": "pFilter->otCtx == NULL",
     "line": 779
    },
    {
     "code": "otCtxToFilter(pFilter->otCtx) == pFilter",
     "line": 786
    },
    {
     "code": "pFilter->NextAlarmTickCount.QuadPart == 0",
     "line": 805
    },
    {
     "code": "pFilter->NextAlarmTickCount.QuadPart > SystemTickCount.QuadPart",
     "line": 819
    },
    {
     "code": "status == STATUS_WAIT_0",
     "line": 844
    },
    {
     "code": "status == STATUS_TIMEOUT",
     "line": 858
    },
    {
     "code": "pFilter->EventTimerState == OT_EVENT_TIMER_FIRED",
     "line": 859
    },
    {
     "code": "status == STATUS_WAIT_0 + 3",
     "line": 859
    },
    {
     "code": "status == STATUS_WAIT_0 + 1",
     "line": 868
    },
    {
     "code": "Event == NULL",
     "line": 886
    },
    {
     "code": "CurrNbl != NULL",
     "line": 893
    },
    {
     "code": "CurrNb != NULL",
     "line": 896
    },
    {
     "code": "error != OT_ERROR_NONE",
     "line": 912
    },
    {
     "code": "error != OT_ERROR_NONE",
     "line": 931
    },
    {
     "code": "status == STATUS_WAIT_0 + 2",
     "line": 964
    },
    {
     "code": "Event == NULL",
     "line": 982
    },
    {
     "code": "Event->BufferLength > sizeof(uint16_t) + packetLength",
     "line": 992
    },
    {
     "code": "packetLength != 0",
     "line": 999
    },
    {
     "code": "status == STATUS_WAIT_0 + 3",
     "line": 1037
    },
    {
     "code": "status == STATUS_WAIT_0 + 4",
     "line": 1041
    },
    {
     "code": "status == STATUS_WAIT_0 + 5",
     "line": 1046
    },
    {
     "code": "status == STATUS_WAIT_0 + 6",
     "line": 1051
    },
    {
     "code": "status == STATUS_WAIT_0 + 7",
     "line": 1056
    },
    {
     "code": "Event == NULL",
     "line": 1074
    },
    {
     "code": "status == STATUS_WAIT_0 + 8",
     "line": 1083
    },
    {
     "code": "pFilter->otRadioState == OT_RADIO_STATE_TRANSMIT",
     "line": 1094
    },
    {
     "code": "pFilter->otInstanceBuffer != NULL",
     "line": 1104
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "LogError(DRIVER_DATA_PATH, \"otAppendMessage failed with %!otError!\", error)",
     "name": "LogError",
     "nargs": 3
    }
   ],
   "line_ids": [
    "DRIVER_DATA_PATH",
    "error"
   ],
   "osv_id": "ARVO-42524167",
   "sites": [
    {
     "args": "ARRAYSIZE(WaitEvents)",
     "callee": "<operator>.alloc",
     "code": "WaitBlocks[ARRAYSIZE(WaitEvents)] = { 0 }",
     "line": 732
    },
    {
     "args": "pFilter->FilterHandle ;; MessageBufferSize",
     "callee": "FILTER_ALLOC_MEM",
     "code": "FILTER_ALLOC_MEM(pFilter->FilterHandle, MessageBufferSize)",
     "line": 736
    },
    {
     "args": "pFilter->FilterHandle ;; MessageBufferSize ;; 'mFto' ;; LowPoolPriority",
     "callee": "NdisAllocateMemoryWithTagPriority",
     "code": "NdisAllocateMemoryWithTagPriority(pFilter->FilterHandle, MessageBufferSize, 'mFto', LowPoolPriority)",
     "line": 736
    },
    {
     "args": "pFilter->FilterHandle ;; (ULONG)pFilter->otInstanceSize",
     "callee": "FILTER_ALLOC_MEM",
     "code": "FILTER_ALLOC_MEM(pFilter->FilterHandle, (ULONG)pFilter->otInstanceSize)",
     "line": 763
    },
    {
     "args": "pFilter->FilterHandle ;; (ULONG)pFilter->otInstanceSize ;; 'mFto' ;; LowPoolPriority",
     "callee": "NdisAllocateMemoryWithTagPriority",
     "code": "NdisAllocateMemoryWithTagPriority(pFilter->FilterHandle, (ULONG)pFilter->otInstanceSize, 'mFto', LowPoolPriority)",
     "line": 763
    },
    {
     "args": "message",
     "callee": "otMessageFree",
     "code": "otMessageFree(message)",
     "line": 915
    },
    {
     "args": "Event ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(Event, 0, 0)",
     "line": 961
    },
    {
     "args": "Event ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(Event, 0, 0)",
     "line": 1034
    },
    {
     "args": "Event ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(Event, 0, 0)",
     "line": 1080
    },
    {
     "args": "pFilter->otInstanceBuffer ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(pFilter->otInstanceBuffer, 0, 0)",
     "line": 1106
    },
    {
     "args": "MessageBuffer",
     "callee": "FILTER_FREE_MEM",
     "code": "FILTER_FREE_MEM(MessageBuffer)",
     "line": 1111
    },
    {
     "args": "MessageBuffer ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(MessageBuffer, 0, 0)",
     "line": 1111
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::NetworkData::ServerTlv::GetServer16() const"
  }
 },
 {
  "osv_id": "ARVO-42524491",
  "project": "openexr",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "mem",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 88,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "size_expr_cpg": "128 + 1",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 102,
    "fn": "Classifier_read",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Classifier_read",
    "file": "/src/openexr/src/lib/OpenEXRCore/internal_dwa_classifier.h",
    "line": 102
   },
   "code": "memcpy (mem, suffix, len)",
   "access": {
    "dir": "READ",
    "width": 130,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Classifier_read",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openexr/address/7c40603eb2812148c6a99fbb6ee07533395fdadb/ARVO-42524491/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openexr_7c40603eb281.cpg",
   "testcase_size": 450
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_offset": 369,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--Classifier_read--DwaCompressor_readChannelRules"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "mem = internal_exr_alloc (len)",
     "line": 99
    }
   ],
   "entity_decl": {
    "line": 88,
    "type": "char*"
   },
   "entity_name_cpg": "mem",
   "func_lines": [
    75,
    135
   ],
   "func_params": {
    "names": [
     "out",
     "ptr",
     "size"
    ],
    "types": [
     "Classifier*",
     "uint8_t**",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "len < 128 + 1",
     "line": 90
    },
    {
     "code": "len > (*size - 3)",
     "line": 92
    },
    {
     "code": "curin[len] == '\\0'",
     "line": 93
    },
    {
     "code": "len == 128 + 1",
     "line": 97
    },
    {
     "code": "*size < len + 2 * sizeof (uint8_t)",
     "line": 107
    },
    {
     "code": "out->_cscIdx < -1",
     "line": 121
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy (mem, suffix, len)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "mem",
    "suffix",
    "len"
   ],
   "osv_id": "ARVO-42524491",
   "sites": [
    {
     "args": "128 + 1",
     "callee": "<operator>.alloc",
     "code": "suffix[128 + 1]",
     "line": 87
    },
    {
     "args": "len",
     "callee": "internal_exr_alloc",
     "code": "internal_exr_alloc (len)",
     "line": 99
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Classifier_read"
  }
 },
 {
  "osv_id": "ARVO-42526378",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "p15card",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "line": 530,
    "size": null,
    "type": "sc_pkcs15_card*"
   }
  },
  "alloc": {
   "size_expr_cpg": "C_ASN1_LAST_UPDATE_SIZE",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "code": "calloc(size, 1)",
    "fn": "sc_pkcs15_get_lastupdate",
    "kind": "calloc",
    "line": 552,
    "origin": "cpg",
    "args": "size ;; 1"
   },
   {
    "kind": "unknown",
    "line": 571,
    "fn": "sc_pkcs15_get_lastupdate",
    "code": "p15card->tokeninfo->last_update.gtime = strdup((char *)l | p15card->tokeninfo->last_update.gtime | p15card->tokeninfo->last_update | p15card->tokeninfo",
    "origin": "report:crash",
    "args": "(char *)last_update"
   },
   {
    "code": "strdup((char *)last_update)",
    "fn": "sc_pkcs15_get_lastupdate",
    "kind": "strdup",
    "line": 571,
    "origin": "cpg",
    "args": "(char *)last_update"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15_get_lastupdate",
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "line": 571
   },
   "code": "p15card->tokeninfo->last_update.gtime = strdup((char *)l | p15card->tokeninfo->last_update.gtime | p15card->tokeninfo->last_update | p15card->tokeninfo",
   "access": {
    "dir": "READ",
    "width": 64,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_pkcs15_get_lastupdate",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:540,GOTO:541,IF:543,IF:547,IF:553,IF:557,IF:568,IF:572"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_pkcs15_card*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "p15card"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/9628e06ad70def92aaa776217164fac57791d123/ARVO-42526378/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_9628e06ad70d.cpg",
   "testcase_size": 109145
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
   "shadow_legend_size": 0,
   "loc_offset": 256,
   "loc_kind": "stack_frame",
   "dedup_token": "__interceptor_strdup--sc_pkcs15_get_lastupdate--generate_cache_filename"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "p15card->tokeninfo->last_update.gtime = strdup((char *)last_update)",
     "line": 571
    }
   ],
   "entity_decl": {
    "line": 530,
    "type": "sc_pkcs15_card*"
   },
   "entity_name_cpg": "p15card",
   "func_lines": [
    529,
    577
   ],
   "func_params": {
    "names": [
     "p15card"
    ],
    "types": [
     "sc_pkcs15_card*"
    ]
   },
   "guards": [
    {
     "code": "r < 0",
     "line": 547
    },
    {
     "code": "r < 0",
     "line": 557
    },
    {
     "code": "r < 0",
     "line": 568
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "p15card->tokeninfo->last_update.gtime = strdup((char *)last_update)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "p15card->tokeninfo->last_update.gtime",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "p15card->tokeninfo->last_update",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "p15card->tokeninfo",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "strdup((char *)last_update)",
     "name": "strdup",
     "nargs": 1
    },
    {
     "code": "(char *)last_update",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p15card",
    "last_update"
   ],
   "osv_id": "ARVO-42526378",
   "sites": [
    {
     "args": "C_ASN1_LAST_UPDATE_SIZE",
     "callee": "<operator>.alloc",
     "code": "asn1_last_update[C_ASN1_LAST_UPDATE_SIZE]",
     "line": 534
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "last_update[32]",
     "line": 535
    },
    {
     "args": "size ;; 1",
     "callee": "calloc",
     "code": "calloc(size, 1)",
     "line": 552
    },
    {
     "args": "file",
     "callee": "sc_file_free",
     "code": "sc_file_free(file)",
     "line": 561
    },
    {
     "args": "content",
     "callee": "free",
     "code": "free(content)",
     "line": 567
    },
    {
     "args": "(char *)last_update",
     "callee": "strdup",
     "code": "strdup((char *)last_update)",
     "line": 571
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_pkcs15_get_lastupdate"
  }
 },
 {
  "osv_id": "ARVO-42527467",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "r",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/log.c",
    "line": 215,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 276,
    "fn": "sc_color_fprintf_va",
    "code": "r = vfprintf(stream, format, args) | vfprintf(stream, format, args)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_color_fprintf_va",
    "file": "/src/opensc/src/libopensc/log.c",
    "line": 276
   },
   "code": "r = vfprintf(stream, format, args) | vfprintf(stream, format, args)",
   "access": {
    "dir": "READ",
    "width": 41,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_color_fprintf_va",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:222,IF:225,DO:232,IF:232,DO:235,IF:235,DO:238,IF:238,DO:241,IF:241,DO:244,IF:244"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ctx",
   "stream",
   "format",
   "args"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/681c780fbafd48af53b491e562e6b2b435c06e10/ARVO-42527467/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_681c780fbafd.cpg",
   "testcase_size": 235
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_offset": 73,
   "loc_kind": "stack_frame",
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--sc_color_fprintf_va--sc_do_log_va"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "r = vfprintf(stream, format, args)",
     "line": 276
    }
   ],
   "entity_decl": {
    "line": 215,
    "type": "int"
   },
   "entity_name_cpg": "r",
   "func_lines": [
    213,
    287
   ],
   "func_params": {
    "names": [
     "colors",
     "ctx",
     "stream",
     "format",
     "args"
    ],
    "types": [
     "int",
     "sc_context*",
     "FILE*",
     "char*",
     "va_list"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "r = vfprintf(stream, format, args)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "vfprintf(stream, format, args)",
     "name": "vfprintf",
     "nargs": 3
    }
   ],
   "line_ids": [
    "r",
    "stream",
    "format",
    "args"
   ],
   "osv_id": "ARVO-42527467",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_color_fprintf_va"
  }
 },
 {
  "osv_id": "ARVO-42527518",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "argv",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 142,
    "size": null,
    "type": "char[]*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 220,
    "fn": "iasecc_crt_parse",
    "code": "argv[my_optind] + offset | argv[my_optind] | charind - offset",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "iasecc_crt_parse",
    "file": "/src/opensc/src/libopensc/iasecc-sdo.c",
    "line": 220
   },
   "code": "argv[my_optind] + offset | argv[my_optind] | charind - offset",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_my_getopt_internal",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "my_optind >= argc | k+1<my_optind | offset == 1",
   "guard_count": 4,
   "control_structures": "IF:149,ELSE:150,IF:151,IF:152,IF:154,IF:159,ELSE:165,IF:165,IF:171,ELSE:172,IF:172,FOR:176"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[]*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "argc",
   "argv"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42527518/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "testcase_size": 1944
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
   "loc_offset": 432,
   "loc_kind": "stack_frame",
   "dedup_token": "iasecc_crt_parse--iasecc_se_parse--iasecc_se_get_info"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "argv[k]=argv[k+1]",
     "line": 185
    },
    {
     "code": "argv[--my_optind]=tmp",
     "line": 186
    }
   ],
   "entity_decl": {
    "line": 142,
    "type": "char[]*"
   },
   "entity_name_cpg": "argv",
   "func_lines": [
    142,
    267
   ],
   "func_params": {
    "names": [
     "argc",
     "argv",
     "shortopts",
     "longopts",
     "longind",
     "long_only"
    ],
    "types": [
     "int",
     "char[]*",
     "char*",
     "option*",
     "int*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "(colon_mode = *shortopts) == ':'",
     "line": 151
    },
    {
     "code": "(mode = shortopts[shortoff]) == '+'",
     "line": 152
    },
    {
     "code": "mode == '-'",
     "line": 152
    },
    {
     "code": "colon_mode != ':'",
     "line": 154
    },
    {
     "code": "(colon_mode = shortopts[shortoff]) == ':'",
     "line": 154
    },
    {
     "code": "argv[my_optind][0] == '-'",
     "line": 160
    },
    {
     "code": "argv[my_optind][1] == '-'",
     "line": 161
    },
    {
     "code": "argv[my_optind][2] == '\\0'",
     "line": 162
    },
    {
     "code": "argv[my_optind][0] != '-'",
     "line": 165
    },
    {
     "code": "argv[my_optind][1] == '\\0'",
     "line": 166
    },
    {
     "code": "mode == '+'",
     "line": 171
    },
    {
     "code": "mode == '-'",
     "line": 172
    },
    {
     "code": "i<argc",
     "line": 176
    },
    {
     "code": "argv[i][0] == '-'",
     "line": 176
    },
    {
     "code": "argv[i][1] != '\\0'",
     "line": 177
    },
    {
     "code": "i > j",
     "line": 182
    },
    {
     "code": "k+1<my_optind",
     "line": 184
    },
    {
     "code": "argv[my_optind][1] != '-'",
     "line": 190
    },
    {
     "code": "(my_optopt = argv[my_optind][1]) != '-'",
     "line": 196
    },
    {
     "code": "shortopts[ind] == ':'",
     "line": 201
    },
    {
     "code": "c == 'W'",
     "line": 202
    },
    {
     "code": "shortopts[ind] == ';'",
     "line": 202
    },
    {
     "code": "shortopts[++ind] == ':'",
     "line": 203
    },
    {
     "code": "my_optopt == c",
     "line": 205
    },
    {
     "code": "argv[my_optind][1] != '-'",
     "line": 208
    },
    {
     "code": "argv[my_optind][charind] != '\\0'",
     "line": 210
    },
    {
     "code": "argv[my_optind][charind] != '='",
     "line": 211
    },
    {
     "code": "strlen(longopts[ind].name) == (size_t) (charind - offset)",
     "line": 214
    },
    {
     "code": "strncmp(longopts[ind].name,",
     "line": 215
    },
    {
     "code": "strncmp(longopts[ind].name,",
     "line": 219
    },
    {
     "code": "hits == 1",
     "line": 222
    },
    {
     "code": "argv[my_optind][charind] == '='",
     "line": 225
    },
    {
     "code": "longopts[found].has_arg == 0",
     "line": 226
    },
    {
     "code": "longopts[found].has_arg == 1",
     "line": 236
    },
    {
     "code": "colon_mode == ':'",
     "line": 238
    },
    {
     "code": "offset == 1",
     "line": 251
    },
    {
     "code": "my_optind > argc",
     "line": 265
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "argv[my_optind] + offset",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "argv[my_optind]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "charind - offset",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "argv",
    "my_optind",
    "offset",
    "charind"
   ],
   "osv_id": "ARVO-42527518",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "iasecc_crt_parse"
  }
 },
 {
  "osv_id": "ARVO-42527828",
  "project": "kimageformats",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "dataRead",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/kimageformats/src/imageformats/xcf.cpp",
    "line": 2060,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 2060,
    "fn": "XCFImageFormat::loadLevel(QDataStream&, XCFImageFormat::Layer&, int, XCFImageFormat::GimpPrecision)",
    "code": "dataRead = xcf_io.readRawData(reinterpret_cast<char *>(l | xcf_io.readRawData(reinterpret_cast<char *>(layer.tile), | reinterpret_cast<char *>(layer.tile) | layer.tile",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "XCFImageFormat::loadLevel(QDataStream&, XCFImageFormat::Layer&, int, XCFImageFormat::GimpPrecision)",
    "file": "/src/kimageformats/src/imageformats/xcf.cpp",
    "line": 2060
   },
   "code": "dataRead = xcf_io.readRawData(reinterpret_cast<char *>(l | xcf_io.readRawData(reinterpret_cast<char *>(layer.tile), | reinterpret_cast<char *>(layer.tile) | layer.tile",
   "access": {
    "dir": "WRITE",
    "width": 61440,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "loadLevel",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "data_size > int(blockSize) | dataRead < data_size | data_size >= unsigned(buffer.size())",
   "guard_count": 4,
   "control_structures": "IF:1979,IF:1984,FOR:1987,FOR:1988,IF:1990,SWITCH:1999,BREAK:2015,BREAK:2017,IF:2023,FOR:2026,FOR:2027,IF:2028"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "xcf_io",
   "layer",
   "bpp",
   "precision"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/kimageformats/address/b2b677b8a5e4c3cf34790eb990218217bf867c18/ARVO-42527828/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_b2b677b8a5e4.cpg",
   "testcase_size": 524271
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
   "loc_offset": 49616,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--QBuffer::readData(char*, long long)--QIODevicePrivate::read(char*, long long, bool)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "dataRead = xcf_io.readRawData(reinterpret_cast<char *>(layer.tile), data_size)",
     "line": 2060
    }
   ],
   "entity_decl": {
    "line": 2060,
    "type": "int"
   },
   "entity_name_cpg": "dataRead",
   "func_lines": [
    1971,
    2164
   ],
   "func_params": {
    "names": [
     "this",
     "xcf_io",
     "layer",
     "bpp",
     "precision"
    ],
    "types": [
     "XCFImageFormat",
     "QDataStream&",
     "Layer&",
     "qint32",
     "GimpPrecision"
    ]
   },
   "guards": [
    {
     "code": "offset < 0",
     "line": 1979
    },
    {
     "code": "offset == 0",
     "line": 1984
    },
    {
     "code": "j < layer.nrows",
     "line": 1987
    },
    {
     "code": "i < layer.ncols",
     "line": 1988
    },
    {
     "code": "layer.type == GRAYA_GIMAGE",
     "line": 1990
    },
    {
     "code": "layer.type == INDEXEDA_GIMAGE",
     "line": 1990
    },
    {
     "code": "bpp == 2",
     "line": 2024
    },
    {
     "code": "j < layer.nrows",
     "line": 2026
    },
    {
     "code": "i < layer.ncols",
     "line": 2027
    },
    {
     "code": "offset == 0",
     "line": 2028
    },
    {
     "code": "offset2 < 0",
     "line": 2036
    },
    {
     "code": "offset2 == 0",
     "line": 2042
    },
    {
     "code": "xcf_io.version() > 11",
     "line": 2051
    },
    {
     "code": "data_size > int(blockSize)",
     "line": 2056
    },
    {
     "code": "dataRead < data_size",
     "line": 2061
    },
    {
     "code": "data_size > sizeof(layer.tile)",
     "line": 2077
    },
    {
     "code": "blockSize > sizeof(layer.tile)",
     "line": 2081
    },
    {
     "code": "bytesParsed > buffer.size()",
     "line": 2098
    },
    {
     "code": "offset < len",
     "line": 2108
    },
    {
     "code": "qToBigEndian<quint16>(qFromBigEndian(source[offset]) / 65537)",
     "line": 2109
    },
    {
     "code": "qToBigEndian<quint16",
     "line": 2109
    },
    {
     "code": "offset < len",
     "line": 2134
    },
    {
     "code": "offset < 0",
     "line": 2156
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "dataRead = xcf_io.readRawData(reinterpret_cast<char *>(layer.tile), data_size)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "xcf_io.readRawData(reinterpret_cast<char *>(layer.tile), data_size)",
     "name": "readRawData",
     "nargs": 3
    },
    {
     "code": "reinterpret_cast<char *>(layer.tile)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "layer.tile",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dataRead",
    "xcf_io",
    "layer",
    "data_size"
   ],
   "osv_id": "ARVO-42527828",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "XCFImageFormat::loadLevel(QDataStream&, XCFImageFormat::Layer&, int, XCFImageFormat::GimpPrecision)"
  }
 },
 {
  "osv_id": "ARVO-42528131",
  "project": "icu",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "attrBuf",
   "kind": "array",
   "storage": "stack",
   "decl": {
    "file": "/src/icu/icu4c/source/common/uloc_tag.cpp",
    "line": 1266,
    "size": null,
    "type": "char[100]"
   }
  },
  "alloc": {
   "size_expr_cpg": "ULOC_KEYWORD_AND_VALUES_CAPACITY",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1336,
    "fn": "_appendKeywordsToLanguageTag",
    "code": "attrBuf[attrBufLength] = 0 | attrBuf[attrBufLength]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_appendKeywordsToLanguageTag",
    "file": "/src/icu/icu4c/source/common/uloc_tag.cpp",
    "line": 1336
   },
   "code": "attrBuf[attrBufLength] = 0 | attrBuf[attrBufLength]",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_appendKeywordsToLanguageTag",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "attrBufLength > 0",
   "guard_count": 1,
   "control_structures": "IF:1274,IF:1277,WHILE:1291,IF:1293,BREAK:1294,IF:1304,IF:1305,BREAK:1307,IF:1309,BREAK:1311,CONTINUE:1315,IF:1322"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[100]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/icu/address/c294c3272c9cb18e35e5827cf37f9f5c6e1c8b58/ARVO-42528131/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_c294c3272c9c.cpg",
   "testcase_size": 112
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_offset": 596,
   "loc_kind": "stack_frame",
   "dedup_token": "_appendKeywordsToLanguageTag--ulocimp_toLanguageTag_74--icu_74::Locale::toLanguageTag(icu_74::ByteSink&, UErrorCode&) const"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "attrBuf[ULOC_KEYWORD_AND_VALUES_CAPACITY] = { 0 }",
     "line": 1266
    },
    {
     "code": "attrBuf[ULOC_KEYWORD_AND_VALUES_CAPACITY] = { 0 }",
     "line": 1266
    },
    {
     "code": "attrBuf[attrBufLength++] = buf[i]",
     "line": 1329
    },
    {
     "code": "attrBuf[attrBufLength] = 0",
     "line": 1336
    }
   ],
   "entity_decl": {
    "line": 1266,
    "type": "char[100]"
   },
   "entity_name_cpg": "attrBuf",
   "func_lines": [
    1264,
    1504
   ],
   "func_params": {
    "names": [
     "localeID",
     "sink",
     "strict",
     "hadPosix",
     "status"
    ],
    "types": [
     "char*",
     "icu.ByteSink&",
     "UBool",
     "UBool",
     "UErrorCode*"
    ]
   },
   "guards": [
    {
     "code": "key == nullptr",
     "line": 1293
    },
    {
     "code": "tmpStatus == U_MEMORY_ALLOCATION_ERROR",
     "line": 1305
    },
    {
     "code": "keylen > 1",
     "line": 1319
    },
    {
     "code": "uprv_strcmp(key, LOCALE_ATTRIBUTE_KEY) == 0",
     "line": 1322
    },
    {
     "code": "len > 0",
     "line": 1323
    },
    {
     "code": "i < len",
     "line": 1327
    },
    {
     "code": "buf[i] != '-'",
     "line": 1328
    },
    {
     "code": "attrBufLength > 0",
     "line": 1335
    },
    {
     "code": "attr == nullptr",
     "line": 1344
    },
    {
     "code": "attrValue == nullptr",
     "line": 1350
    },
    {
     "code": "bcpKey == nullptr",
     "line": 1372
    },
    {
     "code": "bcpValue == nullptr",
     "line": 1382
    },
    {
     "code": "bcpValue == buf.data()",
     "line": 1389
    },
    {
     "code": "extBuf == nullptr",
     "line": 1398
    },
    {
     "code": "*key == PRIVATEUSE",
     "line": 1411
    },
    {
     "code": "extBuf == nullptr",
     "line": 1431
    },
    {
     "code": "ext == nullptr",
     "line": 1444
    },
    {
     "code": "ext == nullptr",
     "line": 1463
    },
    {
     "code": "firstExt != nullptr",
     "line": 1475
    },
    {
     "code": "firstAttr != nullptr",
     "line": 1475
    },
    {
     "code": "uprv_strlen(ext->key) > 1",
     "line": 1478
    },
    {
     "code": "uprv_strcmp(ext->key, LOCALE_ATTRIBUTE_KEY) == 0",
     "line": 1485
    },
    {
     "code": "uprv_strcmp(ext->value, \"true\") != 0",
     "line": 1495
    },
    {
     "code": "uprv_strcmp(ext->value, \"yes\") != 0",
     "line": 1496
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "attrBuf[attrBufLength] = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "attrBuf[attrBufLength]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "attrBuf",
    "attrBufLength"
   ],
   "osv_id": "ARVO-42528131",
   "sites": [
    {
     "args": "ULOC_KEYWORD_AND_VALUES_CAPACITY",
     "callee": "<operator>.alloc",
     "code": "attrBuf[ULOC_KEYWORD_AND_VALUES_CAPACITY] = { 0 }",
     "line": 1266
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_appendKeywordsToLanguageTag"
  }
 },
 {
  "osv_id": "ARVO-42528972",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "argv",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-entersafe.c",
    "line": 46,
    "size": null,
    "type": "char[]*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 123,
    "fn": "entersafe_reverse_buffer",
    "code": "argv[--my_optind]=tmp | argv[--my_optind] | --my_optind",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "entersafe_reverse_buffer",
    "file": "/src/opensc/src/libopensc/card-entersafe.c",
    "line": 123
   },
   "code": "argv[--my_optind]=tmp | argv[--my_optind] | --my_optind",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "my_getopt",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "my_optind >= argc | k+1<my_optind | my_optind > argc",
   "guard_count": 3,
   "control_structures": "IF:53,ELSE:54,IF:55,IF:56,IF:58,IF:63,FOR:65,IF:65,IF:67,IF:68,ELSE:71,IF:71"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[]*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "argc",
   "argv"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b17d4a4dfb02ac6f0476b280588bca022d989e0b/ARVO-42528972/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b17d4a4dfb02.cpg",
   "testcase_size": 369
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
   "loc_offset": 543,
   "loc_kind": "stack_frame",
   "dedup_token": "entersafe_reverse_buffer--entersafe_gen_key--entersafe_card_ctl_2048"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "argv[k]=argv[k+1]",
     "line": 122
    },
    {
     "code": "argv[--my_optind]=tmp",
     "line": 123
    }
   ],
   "entity_decl": {
    "line": 46,
    "type": "char[]*"
   },
   "entity_name_cpg": "argv",
   "func_lines": [
    46,
    135
   ],
   "func_params": {
    "names": [
     "argc",
     "argv",
     "opts"
    ],
    "types": [
     "int",
     "char[]*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "(colon_mode = *opts) == ':'",
     "line": 55
    },
    {
     "code": "(mode = opts[off]) == '+'",
     "line": 56
    },
    {
     "code": "mode == '-'",
     "line": 56
    },
    {
     "code": "colon_mode != ':'",
     "line": 58
    },
    {
     "code": "(colon_mode = opts[off]) == ':'",
     "line": 58
    },
    {
     "code": "my_optopt == *s",
     "line": 65
    },
    {
     "code": "*(++s) == ':'",
     "line": 67
    },
    {
     "code": "my_optopt == 'W'",
     "line": 67
    },
    {
     "code": "*s == ';'",
     "line": 67
    },
    {
     "code": "*(++s) != ':'",
     "line": 71
    },
    {
     "code": "colon_mode == ':'",
     "line": 77
    },
    {
     "code": "argv[my_optind][++charind] == '\\0'",
     "line": 90
    },
    {
     "code": "argv[my_optind][0] == '-'",
     "line": 100
    },
    {
     "code": "argv[my_optind][1] == '-'",
     "line": 101
    },
    {
     "code": "argv[my_optind][2] == '\\0'",
     "line": 102
    },
    {
     "code": "argv[my_optind][0] != '-'",
     "line": 105
    },
    {
     "code": "argv[my_optind][1] == '\\0'",
     "line": 106
    },
    {
     "code": "mode == '+'",
     "line": 110
    },
    {
     "code": "mode == '-'",
     "line": 111
    },
    {
     "code": "i<argc",
     "line": 116
    },
    {
     "code": "argv[i][0] == '-'",
     "line": 116
    },
    {
     "code": "argv[i][1] != '\\0'",
     "line": 117
    },
    {
     "code": "i > j",
     "line": 120
    },
    {
     "code": "k+1<my_optind",
     "line": 122
    },
    {
     "code": "i == argc",
     "line": 127
    },
    {
     "code": "my_optind > argc",
     "line": 133
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "argv[--my_optind]=tmp",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "argv[--my_optind]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "--my_optind",
     "name": "<operator>.preDecrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "argv",
    "my_optind",
    "tmp"
   ],
   "osv_id": "ARVO-42528972",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "entersafe_reverse_buffer"
  }
 },
 {
  "osv_id": "ARVO-42529684",
  "project": "ndpi",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 2771,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "size_expr_cpg": "4",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2771,
    "fn": "ndpi_add_host_ip_subprotocol",
    "code": "c = sscanf(value, \"%3u.%3u.%3u.%3u%s\", &d[0], &d[1], &d[ | sscanf(value, \"%3u.%3u.%3u.%3u%s\", &d[0], &d[1], &d[2],  | &d[0] | d[0]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_add_host_ip_subprotocol",
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 2771
   },
   "code": "c = sscanf(value, \"%3u.%3u.%3u.%3u%s\", &d[0], &d[1], &d[ | sscanf(value, \"%3u.%3u.%3u.%3u%s\", &d[0], &d[1], &d[2],  | &d[0] | d[0]",
   "access": {
    "dir": "WRITE",
    "width": 17,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_add_host_ip_subprotocol",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "c != 4",
   "guard_count": 1,
   "control_structures": "IF:2715,IF:2718,IF:2724,IF:2728,IF:2733,IF:2734,ELSE:2736,IF:2737,IF:2741,ELSE:2744,IF:2751,ELSE:2753"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "value"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/8769a2282b89883ccad97ddfe8dfaefefeb51865/ARVO-42529684/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_8769a2282b89.cpg",
   "testcase_size": 56
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
   "shadow_legend_size": 0,
   "loc_offset": 256,
   "loc_kind": "stack_frame",
   "dedup_token": "scanf_common(void*, int, bool, char const*, __va_list_tag*)--__interceptor___isoc99_vsscanf--__interceptor___isoc99_sscanf"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = sscanf(value, \"%3u.%3u.%3u.%3u%s\", &d[0], &d[1], &d[2], &d[3], tail)",
     "line": 2771
    }
   ],
   "entity_decl": {
    "line": 2771,
    "type": "int"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    2701,
    2838
   ],
   "func_params": {
    "names": [
     "ndpi_str",
     "value",
     "protocol_id",
     "is_ipv6"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "char*",
     "u_int16_t",
     "u_int8_t"
    ]
   },
   "guards": [
    {
     "code": "value[0] == '['",
     "line": 2718
    },
    {
     "code": "(double_column = strrchr(ptr, ':')) != NULL",
     "line": 2728
    },
    {
     "code": "c != 4",
     "line": 2773
    },
    {
     "code": "(h = gethostbyname2(value, AF_INET)) != NULL",
     "line": 2776
    },
    {
     "code": "inet_pton(AF_INET, value, &pin) != 1",
     "line": 2783
    },
    {
     "code": "strchr(value, ':') == NULL",
     "line": 2789
    },
    {
     "code": "(h = gethostbyname2(value, AF_INET6)) != NULL",
     "line": 2792
    },
    {
     "code": "inet_pton(AF_INET6, value, &pin6) != 1",
     "line": 2799
    },
    {
     "code": "node != NULL",
     "line": 2806
    },
    {
     "code": "i<UV16_MAX_USER_VALUES",
     "line": 2810
    },
    {
     "code": "node->value.u.uv16[i].user_value == 0",
     "line": 2811
    },
    {
     "code": "item != NULL",
     "line": 2824
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "c = sscanf(value, \"%3u.%3u.%3u.%3u%s\", &d[0], &d[1], &d[2], &d[3], tail)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "sscanf(value, \"%3u.%3u.%3u.%3u%s\", &d[0], &d[1], &d[2], &d[3], tail)",
     "name": "sscanf",
     "nargs": 7
    },
    {
     "code": "&d[0]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "d[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "&d[1]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "d[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "&d[2]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "d[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "&d[3]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "d[3]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c",
    "value",
    "d",
    "tail"
   ],
   "osv_id": "ARVO-42529684",
   "sites": [
    {
     "args": "4",
     "callee": "<operator>.alloc",
     "code": "d[4]",
     "line": 2769
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "tail[16] = { '\\0' }",
     "line": 2770
    },
    {
     "args": "sizeof(struct patricia_uv16_list)",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(sizeof(struct patricia_uv16_list))",
     "line": 2822
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_add_host_ip_subprotocol"
  }
 },
 {
  "osv_id": "ARVO-42529876",
  "project": "libredwg",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "pair",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 1031,
    "type": "Dxf_Pair*",
    "size": null
   }
  },
  "alloc": {
   "size_expr_cpg": "80",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1122,
    "fn": "dxf_header_read",
    "code": "char []",
    "origin": "report:crash",
    "args": "1024"
   }
  ],
  "crash": {
   "site": {
    "fn": "dxf_header_read",
    "file": "/src/libredwg/src/in_dxf.c",
    "line": 1122
   },
   "code": "bit_utf8_to_TV(dest, (unsigned char *)pair->value.s, 1024, strlen(pair->value.s), 0, dat->codepage)",
   "access": {
    "dir": "READ",
    "width": 1025,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dxf_header_read",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/libredwg/address/56b087fa0bdb5c5587f2e68f864a7240255f4d82/ARVO-42529876/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_56b087fa0bdb.cpg",
   "testcase_size": 8684
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
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 3472,
   "loc_kind": "stack_frame",
   "dedup_token": "strdup--dxf_header_read--dwg_read_dxf"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pair = dxf_read_pair (dat)",
     "line": 1040
    },
    {
     "code": "pair = dxf_read_pair (dat)",
     "line": 1050
    },
    {
     "code": "pair = dxf_read_pair (dat)",
     "line": 1053
    },
    {
     "code": "pair = dxf_read_pair (dat)",
     "line": 1264
    },
    {
     "code": "pair = dxf_read_pair (dat)",
     "line": 1267
    }
   ],
   "entity_decl": {
    "line": 1031,
    "type": "Dxf_Pair*"
   },
   "entity_name_cpg": "pair",
   "func_lines": [
    1022,
    1297
   ],
   "func_params": {
    "names": [
     "dat",
     "dwg"
    ],
    "types": [
     "Bit_Chain*restrict",
     "Dwg_Data*restrict"
    ]
   },
   "guards": [
    {
     "code": "pair != NULL",
     "line": 1041
    },
    {
     "code": "pair->code == 9",
     "line": 1041
    },
    {
     "code": "pair != NULL",
     "line": 1057
    },
    {
     "code": "pair->code == 0",
     "line": 1057
    },
    {
     "code": "pair->code == 0",
     "line": 1057
    },
    {
     "code": "pair->code == 280",
     "line": 1059
    },
    {
     "code": "pair->code == 1",
     "line": 1062
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1063
    },
    {
     "code": "dat->from_version == R_INVALID",
     "line": 1075
    },
    {
     "code": "dwg->object[0].fixedtype == DWG_TYPE_BLOCK_HEADER",
     "line": 1081
    },
    {
     "code": "field[0] == '$'",
     "line": 1097
    },
    {
     "code": "pair->code == 40",
     "line": 1102
    },
    {
     "code": "pair->code == 1",
     "line": 1120
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1120
    },
    {
     "code": "pair->code == 1",
     "line": 1121
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1121
    },
    {
     "code": "pair->code == 1",
     "line": 1122
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1122
    },
    {
     "code": "pair->code == 1",
     "line": 1123
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1123
    },
    {
     "code": "pair->code == 1",
     "line": 1124
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1124
    },
    {
     "code": "pair->code == 1",
     "line": 1125
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1125
    },
    {
     "code": "pair->code == 1",
     "line": 1126
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1128
    },
    {
     "code": "pair->code == 1",
     "line": 1144
    },
    {
     "code": "pair->value.s != NULL",
     "line": 1145
    },
    {
     "code": "dwg->summaryinfo.num_props > 0",
     "line": 1146
    },
    {
     "code": "strcmp((field), (\"$XCLIPFRAME\")) != 0",
     "line": 1158
    },
    {
     "code": "strcmp((field), (\"$OSMODE\")) != 0",
     "line": 1159
    },
    {
     "code": "strcmp((field), (\"$TIMEZONE\")) != 0",
     "line": 1159
    },
    {
     "code": "pair->type == DWG_VT_POINT3D",
     "line": 1167
    },
    {
     "code": "i == 0",
     "line": 1172
    },
    {
     "code": "i == 1",
     "line": 1174
    },
    {
     "code": "i == 2",
     "line": 1176
    },
    {
     "code": "i > 2",
     "line": 1178
    },
    {
     "code": "pair->type == DWG_VT_STRING",
     "line": 1192
    },
    {
     "code": "pair->type == DWG_VT_REAL",
     "line": 1232
    },
    {
     "code": "pair->type == DWG_VT_STRING",
     "line": 1244
    },
    {
     "code": "pair != NULL",
     "line": 1271
    },
    {
     "code": "pair->code == 0",
     "line": 1271
    },
    {
     "code": "pair->code == 0",
     "line": 1271
    },
    {
     "code": "pair->code != 9",
     "line": 1272
    }
   ],
   "line_call_count": 30,
   "line_calls": [
    {
     "code": "SUMMARY_T (SUBJECT)",
     "name": "SUMMARY_T",
     "nargs": 0
    },
    {
     "code": "pair->code == 1 && !strcmp((field), \"$SUBJECT\") && pair->value.s != NULL",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "pair->code == 1 && !strcmp((field), \"$SUBJECT\")",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "pair->code == 1",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "pair->code",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "!strcmp((field), \"$SUBJECT\")",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "strcmp((field), \"$SUBJECT\")",
     "name": "strcmp",
     "nargs": 2
    },
    {
     "code": "pair->value.s != NULL",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "pair->value.s",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "pair->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "char []",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "char []",
     "name": "<operator>.alloc",
     "nargs": 1
    },
    {
     "code": "loglevel >= 3",
     "name": "<operator>.greaterEqualsThan",
     "nargs": 2
    },
    {
     "code": "fprintf(stderr, \"SUMMARY.%s = %s [T16 1]\\n\", &field[1], pair->value.s)",
     "name": "fprintf",
     "nargs": 4
    },
    {
     "code": "&field[1]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "field[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pair->value.s",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "pair->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "bit_utf8_to_TV(dest, (unsigned char *)pair->value.s, 1024, strlen(pair->value.s), 0, dat->codepage)",
     "name": "bit_utf8_to_TV",
     "nargs": 6
    },
    {
     "code": "(unsigned char *)pair->value.s",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "pair->value.s",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "pair->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "strlen(pair->value.s)",
     "name": "strlen",
     "nargs": 1
    },
    {
     "code": "pair->value.s",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "pair->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dat->codepage",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "dwg->summaryinfo.SUBJECT = strdup(dest)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "dwg->summaryinfo.SUBJECT",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "dwg->summaryinfo",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "strdup(dest)",
     "name": "strdup",
     "nargs": 1
    }
   ],
   "line_ids": [
    "pair",
    "field",
    "NULL",
    "dest",
    "loglevel",
    "stderr",
    "dat",
    "dwg"
   ],
   "osv_id": "ARVO-42529876",
   "sites": [
    {
     "args": "80",
     "callee": "<operator>.alloc",
     "code": "field[80]",
     "line": 1043
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair (pair)",
     "line": 1049
    },
    {
     "args": "o->name",
     "callee": "free",
     "code": "free (o->name)",
     "line": 1085
    },
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "char []",
     "line": 1120
    },
    {
     "args": "dest",
     "callee": "strdup",
     "code": "strdup(dest)",
     "line": 1120
    },
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "char []",
     "line": 1121
    },
    {
     "args": "dest",
     "callee": "strdup",
     "code": "strdup(dest)",
     "line": 1121
    },
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "char []",
     "line": 1122
    },
    {
     "args": "dest",
     "callee": "strdup",
     "code": "strdup(dest)",
     "line": 1122
    },
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "char []",
     "line": 1123
    },
    {
     "args": "dest",
     "callee": "strdup",
     "code": "strdup(dest)",
     "line": 1123
    },
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "char []",
     "line": 1124
    },
    {
     "args": "dest",
     "callee": "strdup",
     "code": "strdup(dest)",
     "line": 1124
    },
    {
     "args": "1024",
     "callee": "<operator>.alloc",
     "code": "char []",
     "line": 1125
    },
    {
     "args": "dest",
     "callee": "strdup",
     "code": "strdup(dest)",
     "line": 1125
    },
    {
     "args": null,
     "callee": "realloc",
     "code": "realloc (",
     "line": 1134
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair (pair)",
     "line": 1263
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair (pair)",
     "line": 1295
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dxf_header_read"
  }
 },
 {
  "osv_id": "ARVO-42530547",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 1647,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "SC_ASN1_ALLOC"
  },
  "sites": [
   {
    "code": "malloc(objlen-1)",
    "fn": "asn1_decode_entry",
    "kind": "malloc",
    "line": 1543,
    "origin": "cpg",
    "args": "objlen-1"
   },
   {
    "code": "malloc(objlen)",
    "fn": "asn1_decode_entry",
    "kind": "malloc",
    "line": 1579,
    "origin": "cpg",
    "args": "objlen"
   },
   {
    "kind": "unknown",
    "line": 1588,
    "fn": "asn1_decode_entry",
    "code": "c = objlen > *len ? *len : objlen | objlen > *len ? *len : objlen | objlen > *len | *len",
    "origin": "report:crash"
   },
   {
    "code": "malloc(objlen)",
    "fn": "asn1_decode_entry",
    "kind": "malloc",
    "line": 1601,
    "origin": "cpg",
    "args": "objlen"
   },
   {
    "code": "malloc(objlen+1)",
    "fn": "asn1_decode_entry",
    "kind": "malloc",
    "line": 1626,
    "origin": "cpg",
    "args": "objlen+1"
   }
  ],
  "crash": {
   "site": {
    "fn": "asn1_decode_entry",
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 1588
   },
   "code": "c = objlen > *len ? *len : objlen | objlen > *len ? *len : objlen | objlen > *len | *len",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "asn1_decode_entry",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "objlen > 16 | objlen > 16 | objlen != 1",
   "guard_count": 15,
   "control_structures": "SWITCH:1504,IF:1506,BREAK:1509,BREAK:1511,IF:1513,IF:1514,ELSE:1520,BREAK:1522,IF:1525,BREAK:1530,IF:1533,IF:1536"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "entry",
   "objlen"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/dfeeac68f9cc3b26fe434ef7cfe046905a54b1d5/ARVO-42530547/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_dfeeac68f9cc.cpg",
   "testcase_size": 775
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_offset": 176,
   "loc_kind": "stack_frame",
   "dedup_token": "asn1_decode_entry--asn1_decode--_sc_asn1_decode"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = *len = objlen",
     "line": 1585
    },
    {
     "code": "c = objlen > *len ? *len : objlen",
     "line": 1588
    },
    {
     "code": "c = *len = objlen",
     "line": 1607
    },
    {
     "code": "c = objlen > *len ? *len : objlen",
     "line": 1610
    },
    {
     "code": "c = objlen > sizeof(id->value) ? sizeof(id->value) : objlen",
     "line": 1647
    }
   ],
   "entity_decl": {
    "line": 1565,
    "type": "size_t"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    1488,
    1680
   ],
   "func_params": {
    "names": [
     "ctx",
     "entry",
     "obj",
     "objlen",
     "depth"
    ],
    "types": [
     "sc_context_t*",
     "sc_asn1_entry*",
     "u8*",
     "size_t",
     "int"
    ]
   },
   "guards": [
    {
     "code": "objlen > 16",
     "line": 1501
    },
    {
     "code": "objlen > 16",
     "line": 1502
    },
    {
     "code": "parm != NULL",
     "line": 1506
    },
    {
     "code": "parm != NULL",
     "line": 1513
    },
    {
     "code": "objlen != 1",
     "line": 1514
    },
    {
     "code": "parm != NULL",
     "line": 1525
    },
    {
     "code": "parm != NULL",
     "line": 1533
    },
    {
     "code": "entry->type == SC_ASN1_BIT_STRING",
     "line": 1534
    },
    {
     "code": "len != NULL",
     "line": 1535
    },
    {
     "code": "objlen < 1",
     "line": 1536
    },
    {
     "code": "objlen > 1",
     "line": 1542
    },
    {
     "code": "*buf == NULL",
     "line": 1544
    },
    {
     "code": "parm != NULL",
     "line": 1560
    },
    {
     "code": "parm != NULL",
     "line": 1564
    },
    {
     "code": "len != NULL",
     "line": 1566
    },
    {
     "code": "objlen > 1",
     "line": 1570
    },
    {
     "code": "obj[0] == 0x00",
     "line": 1570
    },
    {
     "code": "objlen > 0",
     "line": 1578
    },
    {
     "code": "*buf == NULL",
     "line": 1580
    },
    {
     "code": "objlen > *len",
     "line": 1588
    },
    {
     "code": "parm != NULL",
     "line": 1595
    },
    {
     "code": "len != NULL",
     "line": 1597
    },
    {
     "code": "objlen > 0",
     "line": 1600
    },
    {
     "code": "*buf == NULL",
     "line": 1602
    },
    {
     "code": "objlen > *len",
     "line": 1610
    },
    {
     "code": "parm != NULL",
     "line": 1617
    },
    {
     "code": "parm != NULL",
     "line": 1622
    },
    {
     "code": "len != NULL",
     "line": 1623
    },
    {
     "code": "*buf == NULL",
     "line": 1627
    },
    {
     "code": "entry->parm != NULL",
     "line": 1641
    },
    {
     "code": "entry->parm != NULL",
     "line": 1645
    },
    {
     "code": "objlen > sizeof(id->value)",
     "line": 1647
    },
    {
     "code": "entry->parm != NULL",
     "line": 1654
    },
    {
     "code": "entry->parm != NULL",
     "line": 1658
    },
    {
     "code": "entry->parm != NULL",
     "line": 1662
    },
    {
     "code": "entry->parm != NULL",
     "line": 1666
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "c = objlen > *len ? *len : objlen",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "objlen > *len ? *len : objlen",
     "name": "<operator>.conditional",
     "nargs": 3
    },
    {
     "code": "objlen > *len",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "*len",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*len",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "c",
    "objlen",
    "len"
   ],
   "osv_id": "ARVO-42530547",
   "sites": [
    {
     "args": "",
     "callee": "SC_ASN1_ALLOC",
     "code": "SC_ASN1_ALLOC",
     "line": 1540
    },
    {
     "args": "objlen-1",
     "callee": "malloc",
     "code": "malloc(objlen-1)",
     "line": 1543
    },
    {
     "args": "",
     "callee": "SC_ASN1_ALLOC",
     "code": "SC_ASN1_ALLOC",
     "line": 1576
    },
    {
     "args": "objlen",
     "callee": "malloc",
     "code": "malloc(objlen)",
     "line": 1579
    },
    {
     "args": "",
     "callee": "SC_ASN1_ALLOC",
     "code": "SC_ASN1_ALLOC",
     "line": 1598
    },
    {
     "args": "objlen",
     "callee": "malloc",
     "code": "malloc(objlen)",
     "line": 1601
    },
    {
     "args": "",
     "callee": "SC_ASN1_ALLOC",
     "code": "SC_ASN1_ALLOC",
     "line": 1624
    },
    {
     "args": "objlen+1",
     "callee": "malloc",
     "code": "malloc(objlen+1)",
     "line": 1626
    },
    {
     "args": "",
     "callee": "SC_ASN1_ALLOC",
     "code": "SC_ASN1_ALLOC",
     "line": 1635
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "asn1_decode_entry"
  }
 },
 {
  "osv_id": "ARVO-42530554",
  "project": "radare2",
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
    "line": 82,
    "fn": "io_memory_read",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "io_memory_read",
    "file": "/src/radare2/libr/io/io_memory.c",
    "line": 82
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 11,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "io_memory_read",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/radare2/address/76a19989d109ff6f2106f1f63f87a0a9f2636820/ARVO-42530554/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_76a19989d109.cpg",
   "testcase_size": 69293
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
   "loc_offset": 104,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memset--io_memory_read--r_io_plugin_read"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "io_memory_read"
  }
 },
 {
  "osv_id": "ARVO-42530823",
  "project": "jq",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "s",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 3369,
    "type": "uint16_t*",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 3375,
    "fn": "decNumberCopy",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "decNumberCopy",
    "file": "/src/jq/src/decNumber/decNumber.c",
    "line": 3375
   },
   "code": "s=src->lsu+1",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "decNumberCopy",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/jq/address/bfb7fd570f521ef832fe1c3bca0e05abd398284c/ARVO-42530823/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/jq_bfb7fd570f52.cpg",
   "testcase_size": 19
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_offset": 44,
   "loc_kind": "stack_frame",
   "dedup_token": "decNumberCopy--decNaNs--decCompareOp"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "s=src->lsu+1",
     "line": 3375
    }
   ],
   "entity_decl": {
    "line": 3369,
    "type": "uint16_t*"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    3352,
    3378
   ],
   "func_params": {
    "names": [
     "dest",
     "src"
    ],
    "types": [
     "decNumber*",
     "decNumber*"
    ]
   },
   "guards": [
    {
     "code": "dest==src",
     "line": 3358
    },
    {
     "code": "src->digits>DECDPUN",
     "line": 3368
    },
    {
     "code": "s<smsup",
     "line": 3375
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "s=src->lsu+1",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "src->lsu+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "src->lsu",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "s<smsup",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "s++, d++",
     "name": "<operator>.expressionList",
     "nargs": 2
    },
    {
     "code": "s++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "d++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "*d=*s",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*d",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*s",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "s",
    "src",
    "smsup",
    "d"
   ],
   "osv_id": "ARVO-42530823",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "decNumberCopy"
  }
 },
 {
  "osv_id": "ARVO-42531617",
  "project": "icu",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "fu",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/icu/icu4c/source/i18n/tznames_impl.cpp",
    "line": 1296,
    "size": null,
    "type": "UText"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1297,
    "fn": "icu_75::mergeTimeZoneKey(icu_75::UnicodeString const&, char*)",
    "code": "utext_openUnicodeString(&fu, &inString, &status) | utext_openUnicodeString_75(&fu, &inString, &status) | &fu | &inString",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "icu_75::mergeTimeZoneKey(icu_75::UnicodeString const&, char*)",
    "file": "/src/icu/icu4c/source/i18n/tznames_impl.cpp",
    "line": 1297
   },
   "code": "utext_openUnicodeString(&fu, &inString, &status) | utext_openUnicodeString_75(&fu, &inString, &status) | &fu | &inString",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "divideUpDictionaryRange",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1140,IF:1141,IF:1153,ELSE:1163,IF:1169,IF:1173,WHILE:1176,WHILE:1181,IF:1189,IF:1193,FOR:1199,FOR:1203"
  },
  "call_chain": [],
  "types": {
   "entity_type": "UText",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "this",
   "inText",
   "rangeStart",
   "rangeEnd",
   "status"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/icu/address/4ba5d9191bc20e33773ee1ff0b7a96b2b2de8359/ARVO-42531617/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_4ba5d9191bc2.cpg",
   "testcase_size": 262
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_offset": 737,
   "loc_kind": "stack_frame",
   "dedup_token": "icu_75::mergeTimeZoneKey(icu_75::UnicodeString const&, char*)--icu_75::TZDBTimeZoneNames::getMetaZoneNames(icu_75::UnicodeString const&, UErrorCode&)--icu_75::T"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "fu = UTEXT_INITIALIZER",
     "line": 1296
    }
   ],
   "entity_decl": {
    "line": 1296,
    "type": "UText"
   },
   "entity_name_cpg": "fu",
   "func_lines": [
    1133,
    1472
   ],
   "func_params": {
    "names": [
     "this",
     "inText",
     "rangeStart",
     "rangeEnd",
     "foundBreaks",
     "isPhraseBreaking",
     "status"
    ],
    "types": [
     "icu_75.CjkBreakEngine",
     "UText*",
     "int32_t",
     "int32_t",
     "UVector32&",
     "UBool",
     "UErrorCode&"
    ]
   },
   "guards": [
    {
     "code": "limit > utext_nativeLength(inText)",
     "line": 1169
    },
    {
     "code": "utext_getNativeIndex(inText) < limit",
     "line": 1176
    },
    {
     "code": "inputMap->size() < inString.length()",
     "line": 1181
    },
    {
     "code": "srcI < inString.length()",
     "line": 1199
    },
    {
     "code": "srcI == inString.length()",
     "line": 1206
    },
    {
     "code": "normalizedMap->size() < normalizedInput.length()",
     "line": 1221
    },
    {
     "code": "numCodePts != inString.length()",
     "line": 1238
    },
    {
     "code": "cuIdx == inString.length()",
     "line": 1260
    },
    {
     "code": "i < numCodePts",
     "line": 1306
    },
    {
     "code": "(uint32_t)bestSnlp.elementAti(i) == kuint32max",
     "line": 1307
    },
    {
     "code": "count == 0",
     "line": 1323
    },
    {
     "code": "lengths.elementAti(0) != 1",
     "line": 1323
    },
    {
     "code": "j < count",
     "line": 1329
    },
    {
     "code": "newSnlp < (uint32_t)bestSnlp.elementAti(ln_j_i)",
     "line": 1332
    },
    {
     "code": "j < inString.length()",
     "line": 1349
    },
    {
     "code": "katakanaRunLength < kMaxKatakanaGroupLength",
     "line": 1349
    },
    {
     "code": "katakanaRunLength < kMaxKatakanaGroupLength",
     "line": 1354
    },
    {
     "code": "newSnlp < (uint32_t)bestSnlp.elementAti(i+katakanaRunLength)",
     "line": 1356
    },
    {
     "code": "(uint32_t)bestSnlp.elementAti(numCodePts) == kuint32max",
     "line": 1374
    },
    {
     "code": "i > 0",
     "line": 1386
    },
    {
     "code": "i > 0",
     "line": 1403
    },
    {
     "code": "foundBreaks.size() == 0",
     "line": 1412
    },
    {
     "code": "foundBreaks.peeki() < rangeStart",
     "line": 1412
    },
    {
     "code": "utextPos > prevUTextPos",
     "line": 1428
    },
    {
     "code": "utextPos != rangeStart",
     "line": 1434
    },
    {
     "code": "utextPos > 0",
     "line": 1435
    },
    {
     "code": "foundBreaks.peeki() == rangeEnd",
     "line": 1452
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "utext_openUnicodeString(&fu, &inString, &status)",
     "name": "utext_openUnicodeString",
     "nargs": 0
    },
    {
     "code": "utext_openUnicodeString_75(&fu, &inString, &status)",
     "name": "utext_openUnicodeString_75",
     "nargs": 3
    },
    {
     "code": "&fu",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "&inString",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "&status",
     "name": "<operator>.addressOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "fu",
    "inString",
    "status"
   ],
   "osv_id": "ARVO-42531617",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "icu_75::mergeTimeZoneKey(icu_75::UnicodeString const&, char*)"
  }
 },
 {
  "osv_id": "ARVO-42531783",
  "project": "icu",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "error",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/icu/icu4c/source/common/uloc.cpp",
    "line": 1479,
    "size": null,
    "type": "UErrorCode&"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1482,
    "fn": "_canonicalize(char const*, icu_75::ByteSink&, unsigned int, UErrorCode*)",
    "code": "U_SUCCESS(error)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_canonicalize(char const*, icu_75::ByteSink&, unsigned int, UErrorCode*)",
    "file": "/src/icu/icu4c/source/common/uloc.cpp",
    "line": 1482
   },
   "code": "U_SUCCESS(error)",
   "access": {
    "dir": "READ",
    "width": 1025,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "loadJapaneseExtensions",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1482,WHILE:1484"
  },
  "call_chain": [],
  "types": {
   "entity_type": "UErrorCode&",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "error"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/icu/address/3f054adaf3ca34d55338e56773088bd589600583/ARVO-42531783/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_3f054adaf3ca.cpg",
   "testcase_size": 1081
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
   "shadow_legend_size": 0,
   "loc_offset": 4608,
   "loc_kind": "stack_frame",
   "dedup_token": "StrstrCheck(void*, char*, char const*, char const*)--strstr--_canonicalize(char const*, icu_75::ByteSink&, unsigned int, UErrorCode*)"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1479,
    "type": "UErrorCode&"
   },
   "entity_name_cpg": "error",
   "func_lines": [
    1479,
    1488
   ],
   "func_params": {
    "names": [
     "this",
     "error"
    ],
    "types": [
     "icu_75.CjkBreakEngine",
     "UErrorCode&"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "U_SUCCESS(error)",
     "name": "U_SUCCESS",
     "nargs": 1
    }
   ],
   "line_ids": [
    "error"
   ],
   "osv_id": "ARVO-42531783",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_canonicalize(char const*, icu_75::ByteSink&, unsigned int, UErrorCode*)"
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