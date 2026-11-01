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
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:640",
   "fn": "rfCoreSendTransmitCmd",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 88
   },
   "code": ".startTrigger               =",
   "site": {
    "file": "/src/openthread/src/core/common/message.cpp",
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "line": 595
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "startTrigger",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_b694b00951ee.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/b694b00951eeeb4986387de1179d55dd38643a87/ARVO-42475962/report.log",
   "testcase_size": 41
  },
  "input_reachability": [],
  "osv_id": "ARVO-42475962",
  "project": "openthread",
  "sites": [
   {
    "code": ".startTrigger               =",
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "kind": "unknown",
    "line": 595,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "DO:3208,IF:3208,GOTO:3208,DO:3209,IF:3209,GOTO:3209,DO:3214,IF:3214,GOTO:3214,DO:3215,IF:3215,GOTO:3215",
   "fn": "HandleParentResponse",
   "guard_count": 1,
   "guards": "error != OT_ERROR_NONE",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 255
   },
   "code": "VerifyOrExit(response.IsValid() &&",
   "site": {
    "file": "/src/openthread/src/core/thread/mle.cpp",
    "fn": "ot::Mle::Mle::HandleParentResponse(ot::Message const&, ot::Ip6::MessageInfo const&, unsigned int)",
    "line": 3215
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/thread/mle.cpp",
    "line": 3192,
    "size": null,
    "type": "ResponseTlv"
   },
   "kind": "struct",
   "name": "response",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_b694b00951ee.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/b694b00951eeeb4986387de1179d55dd38643a87/ARVO-42475964/report.log",
   "testcase_size": 38
  },
  "input_reachability": [
   "aMessage"
  ],
  "osv_id": "ARVO-42475964",
  "project": "openthread",
  "sites": [
   {
    "code": "VerifyOrExit(response.IsValid() &&",
    "fn": "ot::Mle::Mle::HandleParentResponse(ot::Message const&, ot::Ip6::MessageInfo const&, unsigned int)",
    "kind": "unknown",
    "line": 3215,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "ResponseTlv",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "tvb_memcpy",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 27
   },
   "code": null,
   "site": {
    "file": "/src/wireshark/epan/tvbuff.c",
    "fn": "tvb_memcpy",
    "line": 859
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_81e2d2a668cc.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/81e2d2a668cc06e53168623af19718c03f68ab1d/ARVO-42476579/report.log",
   "testcase_size": 41
  },
  "input_reachability": [],
  "osv_id": "ARVO-42476579",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "tvb_memcpy",
    "kind": "unknown",
    "line": 859,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:670",
   "fn": "rfCoreSendTransmitCmd",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 8
   },
   "code": ".startTrigger               =",
   "site": {
    "file": "/src/openthread/src/core/thread/network_data_leader_ftd.cpp",
    "fn": "ot::NetworkData::Leader::IsStableUpdated(unsigned char*, unsigned char, unsigned char*, unsigned char)",
    "line": 638
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "startTrigger",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_f5ee3a5e65a8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/f5ee3a5e65a8c1bddae503e31a1aa51684931f00/ARVO-42476618/report.log",
   "testcase_size": 643
  },
  "input_reachability": [],
  "osv_id": "ARVO-42476618",
  "project": "openthread",
  "sites": [
   {
    "code": ".startTrigger               =",
    "fn": "ot::NetworkData::Leader::IsStableUpdated(unsigned char*, unsigned char, unsigned char*, unsigned char)",
    "kind": "unknown",
    "line": 638,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "ZSTD_decodeLiteralsBlock",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 131082
   },
   "code": null,
   "site": {
    "file": "/src/zstd/lib/legacy/zstd_v03.c",
    "fn": "ZSTD_decodeLiteralsBlock",
    "line": 2529
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/zstd_9ad7ea44ec96.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/zstd/address/9ad7ea44ec9644c618c2e82be5960d868e48745d/ARVO-42477145/report.log",
   "testcase_size": 131102
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477145",
  "project": "zstd",
  "sites": [
   {
    "code": null,
    "fn": "ZSTD_decodeLiteralsBlock",
    "kind": "unknown",
    "line": 2529,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "Mat_uint32Swap",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/matio/src/endian.c",
    "fn": "Mat_uint32Swap",
    "line": 132
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_6540087e697c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/matio/address/6540087e697ca2b8950bada3d4ca653951b467dc/ARVO-42477888/report.log",
   "testcase_size": 607
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477888",
  "project": "matio",
  "sites": [
   {
    "code": null,
    "fn": "Mat_uint32Swap",
    "kind": "unknown",
    "line": 132,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:328,IF:339,IF:349,IF:353,IF:357,IF:364",
   "fn": "applicationTick",
   "guard_count": 4,
   "guards": "message != NULL | error == OT_ERROR_NONE | error == OT_ERROR_NONE",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "error = otMessageAppend(message, payload, (uint16_t)strl | otMessageAppend(message, payload, (uint16_t)strlen(paylo | (uint16_t)strlen(payload) | strlen(payload)",
   "site": {
    "file": "/src/openthread/src/core/thread/network_data_leader_ftd.cpp",
    "fn": "ot::NetworkData::Leader::SendCommissioningGetResponse(ot::Coap::Message const&, ot::Ip6::MessageInfo const&, unsigned char const*, unsigned char)",
    "line": 351
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/thread/network_data_leader_ftd.cpp",
    "line": 322,
    "size": null,
    "type": "otError"
   },
   "kind": "struct",
   "name": "error",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_bb56fa906a09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/bb56fa906a09408acc3787ae54969270e43a2454/ARVO-42478091/report.log",
   "testcase_size": 33
  },
  "input_reachability": [],
  "osv_id": "ARVO-42478091",
  "project": "openthread",
  "sites": [
   {
    "code": "error = otMessageAppend(message, payload, (uint16_t)strl | otMessageAppend(message, payload, (uint16_t)strlen(paylo | (uint16_t)strlen(payload) | strlen(payload)",
    "fn": "ot::NetworkData::Leader::SendCommissioningGetResponse(ot::Coap::Message const&, ot::Ip6::MessageInfo const&, unsigned char const*, unsigned char)",
    "kind": "unknown",
    "line": 351,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "otError",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "DO:528,IF:528,GOTO:528,DO:529,IF:529,GOTO:529",
   "fn": "otPlatRadioDisable",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 147
   },
   "code": "error = OT_ERROR_NONE",
   "site": {
    "file": "/src/openthread/src/core/common/message.cpp",
    "fn": "ot::Message::Read(unsigned short, unsigned short, void*) const",
    "line": 526
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/common/message.cpp",
    "line": 526,
    "size": null,
    "type": "otError"
   },
   "kind": "struct",
   "name": "error",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_bb56fa906a09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/bb56fa906a09408acc3787ae54969270e43a2454/ARVO-42478129/report.log",
   "testcase_size": 1089
  },
  "input_reachability": [],
  "osv_id": "ARVO-42478129",
  "project": "openthread",
  "sites": [
   {
    "code": "error = OT_ERROR_NONE",
    "fn": "ot::Message::Read(unsigned short, unsigned short, void*) const",
    "kind": "unknown",
    "line": 526,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "otError",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:90,SWITCH:98,IF:101,BREAK:103,BREAK:106,IF:108,ELSE:111,BREAK:117,BREAK:121,IF:123,IF:126,ELSE:133",
   "fn": "sc_apdu2bytes",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 30
   },
   "code": "sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU  | _sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU",
   "site": {
    "file": "/src/opensc/src/tests/fuzzing/fuzz_pkcs15_reader.c",
    "fn": "fuzz_reader_transmit",
    "line": 129
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/tests/fuzzing/fuzz_pkcs15_reader.c",
    "line": 83,
    "size": null,
    "type": "sc_context_t*"
   },
   "kind": "pointer",
   "name": "ctx",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_61cd7fcdb2fd.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/61cd7fcdb2fdc9214b431abb631b202314dcc32f/ARVO-42479513/report.log",
   "testcase_size": 330
  },
  "input_reachability": [
   "ctx"
  ],
  "osv_id": "ARVO-42479513",
  "project": "opensc",
  "sites": [
   {
    "code": "sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU  | _sc_log(ctx, \"invalid Lc length for CASE 3 extended APDU",
    "fn": "fuzz_reader_transmit",
    "kind": "unknown",
    "line": 129,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "sc_context_t*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:48,IF:52,IF:58,IF:59,IF:62,ELSE:65,IF:67,IF:72,IF:79,IF:82,IF:85,IF:89",
   "fn": "ndpi_search_kerberos",
   "guard_count": 4,
   "guards": "realm_len > sizeof(realm_str)-1 | i<realm_len | realm_len > sizeof(realm_str)-1",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 1
   },
   "code": "realm_str[realm_len] = '\\0' | realm_str[realm_len]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "fn": "ndpi_search_kerberos",
    "line": 116
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 142,
    "size": null,
    "type": "char[24]"
   },
   "kind": "array",
   "name": "realm_str",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_803dc6ff779b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/803dc6ff779b44be1264380b800bb2904b9de692/ARVO-42480178/report.log",
   "testcase_size": 170
  },
  "input_reachability": [],
  "osv_id": "ARVO-42480178",
  "project": "ndpi",
  "sites": [
   {
    "code": "realm_str[realm_len] = '\\0' | realm_str[realm_len]",
    "fn": "ndpi_search_kerberos",
    "kind": "unknown",
    "line": 116,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char[24]",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:394,SWITCH:399,BREAK:403,BREAK:407,BREAK:411,BREAK:415,BREAK:419,IF:427",
   "fn": "sc_pkcs15emu_object_add",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 464
   },
   "code": "memcpy(obj->data, data, data_len) | obj->data",
   "site": {
    "file": "/src/opensc/src/libopensc/pkcs15-syn.c",
    "fn": "sc_pkcs15emu_object_add",
    "line": 431
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-syn.c",
    "line": 389,
    "size": null,
    "type": "sc_pkcs15_object_t*"
   },
   "kind": "pointer",
   "name": "obj",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_4c67bbf3838a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/4c67bbf3838aba9cf7e00697403d7b860bbae30b/ARVO-42480263/report.log",
   "testcase_size": 294
  },
  "free_related": {
   "free_sites_in_func": [
    422,
    428
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "input_reachability": [
   "p15card",
   "type",
   "in_obj",
   "data"
  ],
  "osv_id": "ARVO-42480263",
  "project": "opensc",
  "sites": [
   {
    "code": "calloc(1, sizeof(*obj))",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "calloc",
    "line": 393,
    "origin": "cpg"
   },
   {
    "code": "free(obj)",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "free",
    "line": 422,
    "origin": "cpg"
   },
   {
    "code": "calloc(1, data_len)",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "calloc",
    "line": 426,
    "origin": "cpg"
   },
   {
    "code": "free(obj)",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "free",
    "line": 428,
    "origin": "cpg"
   },
   {
    "code": "memcpy(obj->data, data, data_len) | obj->data",
    "fn": "sc_pkcs15emu_object_add",
    "kind": "unknown",
    "line": 431,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "sc_pkcs15_object_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:640",
   "fn": "rfCoreSendTransmitCmd",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 11
   },
   "code": ".triggerType            = TRIG_NOW",
   "site": {
    "file": "/src/openthread/src/core/common/message.cpp",
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "line": 569
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "triggerType",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_082c1c79f5a8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/082c1c79f5a84aeda8eee4f87d9f261089fb9e78/ARVO-42480359/report.log",
   "testcase_size": 56
  },
  "input_reachability": [],
  "osv_id": "ARVO-42480359",
  "project": "openthread",
  "sites": [
   {
    "code": ".triggerType            = TRIG_NOW",
    "fn": "ot::Message::Write(unsigned short, unsigned short, void const*)",
    "kind": "unknown",
    "line": 569,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1070,IF:1074,ELSE:1079,IF:1079,IF:1085,IF:1089,IF:1091,SWITCH:1094,IF:1097,ELSE:1104,BREAK:1110,BREAK:1116",
   "fn": "RFCCPE0IntHandler",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 17
   },
   "code": "sTxCmdChainDone = true",
   "site": {
    "file": "/src/openthread/src/core/meshcop/commissioner.cpp",
    "fn": "ot::MeshCoP::Commissioner::GeneratePskc(char const*, char const*, ot::Mac::ExtendedPanId const&, ot::Pskc&)",
    "line": 1121
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "sTxCmdChainDone",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_88df5fb4ac8b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/88df5fb4ac8bd177fcbb1323eb8494d8fe7b610c/ARVO-42480412/report.log",
   "testcase_size": 43
  },
  "input_reachability": [],
  "osv_id": "ARVO-42480412",
  "project": "openthread",
  "sites": [
   {
    "code": "sTxCmdChainDone = true",
    "fn": "ot::MeshCoP::Commissioner::GeneratePskc(char const*, char const*, ot::Mac::ExtendedPanId const&, ot::Pskc&)",
    "kind": "unknown",
    "line": 1121,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:213,IF:215,IF:238,IF:242,ELSE:246,IF:257,IF:261,IF:268,IF:274,ELSE:277,IF:281,IF:295",
   "fn": "getTLScertificate",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 2
   },
   "code": "ja3_str_len += snprintf(&ja3_str[ja3_str_len], sizeof(ja | snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_ | &ja3_str[ja3_str_len] | ja3_str[ja3_str_len]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "fn": "getTLScertificate",
    "line": 719
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 207,
    "size": null,
    "type": "u_int16_t"
   },
   "kind": "struct",
   "name": "ja3_str_len",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_bf5e9b7b0b83.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/bf5e9b7b0b83b93116786e7b982dbe4db3645ffa/ARVO-42480587/report.log",
   "testcase_size": 21569
  },
  "input_reachability": [],
  "osv_id": "ARVO-42480587",
  "project": "ndpi",
  "sites": [
   {
    "code": "ja3_str_len += snprintf(&ja3_str[ja3_str_len], sizeof(ja | snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_ | &ja3_str[ja3_str_len] | ja3_str[ja3_str_len]",
    "fn": "getTLScertificate",
    "kind": "unknown",
    "line": 719,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "u_int16_t",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:697,SWITCH:703,IF:705,BREAK:715,FOR:724,FOR:729,IF:730,BREAK:733,BREAK:736",
   "fn": "pgp_parse_algo_attr_blob",
   "guard_count": 2,
   "guards": "blob == NULL | j < (blob->len-1)",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 4
   },
   "code": "oid.value[j] = blob->data[j+1] | oid.value[j] | oid.value | blob->data[j+1]",
   "site": {
    "file": "/src/opensc/src/libopensc/card-openpgp.c",
    "fn": "pgp_parse_algo_attr_blob",
    "line": 725
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-openpgp.c",
    "line": 694,
    "size": null,
    "type": "sc_object_id"
   },
   "kind": "struct",
   "name": "oid",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_ee78b0b80514.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/ee78b0b80514460936c585c3ff5fc477338ae371/ARVO-42480591/report.log",
   "testcase_size": 368
  },
  "input_reachability": [
   "blob"
  ],
  "osv_id": "ARVO-42480591",
  "project": "opensc",
  "sites": [
   {
    "code": "oid.value[j] = blob->data[j+1] | oid.value[j] | oid.value | blob->data[j+1]",
    "fn": "pgp_parse_algo_attr_blob",
    "kind": "unknown",
    "line": 725,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "sc_object_id",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 }
]

## 任务
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、dimensions、evidence、confidence。
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