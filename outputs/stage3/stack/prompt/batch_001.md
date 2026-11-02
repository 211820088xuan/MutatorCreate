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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "se_read_conf",
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
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/net-snmp/snmplib/snmp_enum.c",
    "fn": "se_read_conf",
    "line": 153
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
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-396958482/report.log",
   "testcase_size": 151
  },
  "input_reachability": [],
  "osv_id": "ARVO-396958482",
  "project": "net-snmp",
  "sites": [
   {
    "code": null,
    "fn": "se_read_conf",
    "kind": "unknown",
    "line": 153,
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
   "fn": "<clinit>",
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
    "width": 256
   },
   "code": "OT_MESHCOP_TLV_VENDOR_STACK_VERSION_TLV = 37",
   "site": {
    "file": "/src/openthread/src/cli/cli_utils.cpp",
    "fn": "ot::Cli::OutputImplementer::OutputV(char const*, __va_list_tag*)",
    "line": 290
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "OT_MESHCOP_TLV_VENDOR_STACK_VERSION_TLV",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_98b88dc8f7a3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/98b88dc8f7a3a9f7300248093752455260d605df/ARVO-411460530/report.log",
   "testcase_size": 266
  },
  "input_reachability": [],
  "osv_id": "ARVO-411460530",
  "project": "openthread",
  "sites": [
   {
    "code": "OT_MESHCOP_TLV_VENDOR_STACK_VERSION_TLV = 37",
    "fn": "ot::Cli::OutputImplementer::OutputV(char const*, __va_list_tag*)",
    "kind": "unknown",
    "line": 290,
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
   "fn": "nullable_memcpy",
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
    "width": 252
   },
   "code": null,
   "site": {
    "file": "/src/openvswitch/lib/util.h",
    "fn": "nullable_memcpy",
    "line": 173
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_bc9bbc4ea264.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openvswitch/address/bc9bbc4ea2645e5bbb3c02d986f26fdc83283d72/ARVO-42470954/report.log",
   "testcase_size": 523
  },
  "input_reachability": [],
  "osv_id": "ARVO-42470954",
  "project": "openvswitch",
  "sites": [
   {
    "code": null,
    "fn": "nullable_memcpy",
    "kind": "unknown",
    "line": 173,
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
   "fn": "cdma2k_message_ACTIVE_SET_RECORD_FIELDS",
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
    "width": 2
   },
   "code": null,
   "site": {
    "file": "/src/wireshark/epan/dissectors/packet-cdma2k.c",
    "fn": "cdma2k_message_ACTIVE_SET_RECORD_FIELDS",
    "line": 3861
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_85f822b04442.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/85f822b04442bdaaf5f39632412db3afbf842921/ARVO-42471803/report.log",
   "testcase_size": 522
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471803",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "cdma2k_message_ACTIVE_SET_RECORD_FIELDS",
    "kind": "unknown",
    "line": 3861,
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
   "control_structures": "IF:192,IF:199,IF:228,IF:237,FOR:251,IF:252",
   "fn": "<global>",
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
    "width": 4
   },
   "code": "{HB_TAG ('s','s','0','4'), HB_AAT_LAYOUT_FEATURE_TYPE_ST | HB_TAG ('s','s','0','4') | (hb_tag_t)((((uint32_t)('s') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('s') & 0xFF) << 24) | (((uint32_t)('s') & 0",
   "site": {
    "file": "/src/harfbuzz/src/hb-array.hh",
    "fn": "hb_array_t<char const>::cmp(hb_array_t<char const> const&) const",
    "line": 100
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "uint32_t",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_49334f9b509f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/harfbuzz/address/49334f9b509fc15e8baa93d49b86886ca933de04/ARVO-42472107/report.log",
   "testcase_size": 32
  },
  "input_reachability": [],
  "osv_id": "ARVO-42472107",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "{HB_TAG ('s','s','0','4'), HB_AAT_LAYOUT_FEATURE_TYPE_ST | HB_TAG ('s','s','0','4') | (hb_tag_t)((((uint32_t)('s') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('s') & 0xFF) << 24) | (((uint32_t)('s') & 0",
    "fn": "hb_array_t<char const>::cmp(hb_array_t<char const> const&) const",
    "kind": "unknown",
    "line": 100,
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
   "control_structures": "FOR:2001,IF:2004,IF:2012,IF:2014,IF:2019,ELSE:2023,FOR:2027,ELSE:2031,IF:2040,FOR:2046,IF:2050,IF:2056",
   "fn": "parse_tables",
   "guard_count": 1,
   "guards": "w < HUFF_BC",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 7
   },
   "code": "bit_length[w++] = 0 | bit_length[w++] | w++",
   "site": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "parse_tables",
    "line": 2028
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 1992,
    "size": null,
    "type": "uint8_t[20]"
   },
   "kind": "array",
   "name": "bit_length",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_d5f35a90a4cb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/libarchive/address/d5f35a90a4cb1eeb918213bff9d78e8b0471dc0a/ARVO-42472727/report.log",
   "testcase_size": 524
  },
  "input_reachability": [
   "p"
  ],
  "osv_id": "ARVO-42472727",
  "project": "libarchive",
  "sites": [
   {
    "code": "bit_length[w++] = 0 | bit_length[w++] | w++",
    "fn": "parse_tables",
    "kind": "unknown",
    "line": 2028,
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
   "entity_type": "uint8_t[20]",
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
   "control_structures": "DO:336,IF:336,GOTO:336,IF:346,IF:351,ELSE:356",
   "fn": "otPlatRadioTransmit",
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
    "width": 32
   },
   "code": "csmaConfig = RAIL_CSMA_CONFIG_802_15_4_2003_2p4_GHz_OQPS",
   "site": {
    "file": "/src/openthread/src/core/thread/network_data_tlvs.hpp",
    "fn": "ot::NetworkData::PrefixTlv::Init(unsigned char, unsigned char, unsigned char const*)",
    "line": 332
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/thread/network_data_tlvs.hpp",
    "line": 332,
    "size": null,
    "type": "RAIL_CsmaConfig_t"
   },
   "kind": "struct",
   "name": "csmaConfig",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_0f4bae97e968.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/0f4bae97e968fbcfd997a921b29f3a81910b01eb/ARVO-42472863/report.log",
   "testcase_size": 71
  },
  "input_reachability": [],
  "osv_id": "ARVO-42472863",
  "project": "openthread",
  "sites": [
   {
    "code": "csmaConfig = RAIL_CSMA_CONFIG_802_15_4_2003_2p4_GHz_OQPS",
    "fn": "ot::NetworkData::PrefixTlv::Init(unsigned char, unsigned char, unsigned char const*)",
    "kind": "unknown",
    "line": 332,
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
   "entity_type": "RAIL_CsmaConfig_t",
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
   "control_structures": "IF:1644,FOR:1648,ELSE:1655",
   "fn": "otPlatRadioClearSrcMatchShortEntries",
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
    "width": 253
   },
   "code": "OT_UNUSED_VARIABLE(aInstance)",
   "site": {
    "file": "/src/openthread/src/cli/cli.cpp",
    "fn": "ot::Cli::Interpreter::ProcessService(int, char**)",
    "line": 1642
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/cli/cli.cpp",
    "line": 1640,
    "size": null,
    "type": "otInstance*"
   },
   "kind": "pointer",
   "name": "aInstance",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_26c5d0ecb8fe.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/26c5d0ecb8fe198d379326a34d8489cb5eb2bcd1/ARVO-42472923/report.log",
   "testcase_size": 270
  },
  "input_reachability": [
   "aInstance"
  ],
  "osv_id": "ARVO-42472923",
  "project": "openthread",
  "sites": [
   {
    "code": "OT_UNUSED_VARIABLE(aInstance)",
    "fn": "ot::Cli::Interpreter::ProcessService(int, char**)",
    "kind": "unknown",
    "line": 1642,
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
   "entity_type": "otInstance*",
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
   "control_structures": "IF:921,ELSE:928",
   "fn": "otPlatRadioEnableSrcMatch",
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
    "width": 1
   },
   "code": "OT_UNUSED_VARIABLE(aInstance)",
   "site": {
    "file": "/src/openthread/src/core/thread/network_data.cpp",
    "fn": "ot::NetworkData::NetworkData::PrefixMatch(unsigned char const*, unsigned char const*, unsigned char)",
    "line": 917
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/thread/network_data.cpp",
    "line": 915,
    "size": null,
    "type": "otInstance*"
   },
   "kind": "pointer",
   "name": "aInstance",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_203bce7ae79a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/203bce7ae79ac63652c27aa26b3d480cd9c19cc0/ARVO-42473688/report.log",
   "testcase_size": 68
  },
  "input_reachability": [
   "aInstance"
  ],
  "osv_id": "ARVO-42473688",
  "project": "openthread",
  "sites": [
   {
    "code": "OT_UNUSED_VARIABLE(aInstance)",
    "fn": "ot::NetworkData::NetworkData::PrefixMatch(unsigned char const*, unsigned char const*, unsigned char)",
    "kind": "unknown",
    "line": 917,
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
   "entity_type": "otInstance*",
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
   "fn": "otPlatLog",
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
    "width": 25
   },
   "code": "va_start(ap, aFormat)",
   "site": {
    "file": "/src/openthread/src/core/thread/network_data.cpp",
    "fn": "ot::NetworkData::NetworkData::GetNextOnMeshPrefix(unsigned int*, unsigned short, otBorderRouterConfig*)",
    "line": 138
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/thread/network_data.cpp",
    "line": 137,
    "size": null,
    "type": "va_list"
   },
   "kind": "struct",
   "name": "ap",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_203bce7ae79a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/203bce7ae79ac63652c27aa26b3d480cd9c19cc0/ARVO-42473689/report.log",
   "testcase_size": 68
  },
  "input_reachability": [
   "aFormat"
  ],
  "osv_id": "ARVO-42473689",
  "project": "openthread",
  "sites": [
   {
    "code": "va_start(ap, aFormat)",
    "fn": "ot::NetworkData::NetworkData::GetNextOnMeshPrefix(unsigned int*, unsigned short, otBorderRouterConfig*)",
    "kind": "unknown",
    "line": 138,
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
   "entity_type": "va_list",
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
   "fn": "GetMask",
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
    "width": 4
   },
   "code": "Reverse32(HostSwap32(mMask)) | HostSwap32(mMask) | this->mMask",
   "site": {
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "fn": "ot::MeshCoP::ChannelMaskEntry::GetMask() const",
    "line": 1518
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "line": 1518,
    "size": null,
    "type": "ot.MeshCoP.ChannelMaskEntry"
   },
   "kind": "struct",
   "name": "this",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_6453c9f033f2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/6453c9f033f2e1ec1c95948f61b93496a1be1bda/ARVO-42474005/report.log",
   "testcase_size": 160
  },
  "input_reachability": [
   "this"
  ],
  "osv_id": "ARVO-42474005",
  "project": "openthread",
  "sites": [
   {
    "code": "Reverse32(HostSwap32(mMask)) | HostSwap32(mMask) | this->mMask",
    "fn": "ot::MeshCoP::ChannelMaskEntry::GetMask() const",
    "kind": "unknown",
    "line": 1518,
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
   "entity_type": "ot.MeshCoP.ChannelMaskEntry",
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
   "control_structures": "IF:1343,IF:1345,IF:1349,IF:1350,IF:1353,IF:1355,ELSE:1358,IF:1361,IF:1366,IF:1367,IF:1370,IF:1372",
   "fn": "parse_file_extra_owner",
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
    "width": 1
   },
   "code": "namebuf[name_len] = 0 | namebuf[name_len]",
   "site": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "parse_file_extra_owner",
    "line": 1377
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 1340,
    "size": null,
    "type": "char[256]"
   },
   "kind": "array",
   "name": "namebuf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_64e68f2034e6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/libarchive/address/64e68f2034e6c5c6fd20d6b274b67fbdb88c3804/ARVO-42474797/report.log",
   "testcase_size": 357
  },
  "input_reachability": [
   "a"
  ],
  "osv_id": "ARVO-42474797",
  "project": "libarchive",
  "sites": [
   {
    "code": "namebuf[name_len] = 0 | namebuf[name_len]",
    "fn": "parse_file_extra_owner",
    "kind": "unknown",
    "line": 1377,
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
   "entity_type": "char[256]",
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
   "control_structures": "SWITCH:264,IF:269,BREAK:273,IF:277,ELSE:290,BREAK:293,BREAK:309,BREAK:313,BREAK:316,IF:322",
   "fn": "otLwfDispatch",
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
    "width": 1
   },
   "code": "LogFuncExitNT(DRIVER_IOCTL, Status)",
   "site": {
    "file": "/src/openthread/src/core/net/ip6_address.cpp",
    "fn": "ot::Ip6::Address::FromString(char const*)",
    "line": 333
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "DRIVER_IOCTL",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_21ad4f5da3ae.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/21ad4f5da3ae085cd08997c52bd3fd053501a125/ARVO-42475341/report.log",
   "testcase_size": 26
  },
  "input_reachability": [
   "Irp"
  ],
  "osv_id": "ARVO-42475341",
  "project": "openthread",
  "sites": [
   {
    "code": "LogFuncExitNT(DRIVER_IOCTL, Status)",
    "fn": "ot::Ip6::Address::FromString(char const*)",
    "kind": "unknown",
    "line": 333,
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
   "fn": "otPlatSettingsAdd",
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
    "width": 9
   },
   "code": "FilterWriteSetting(",
   "site": {
    "file": "/src/openthread/src/core/net/ip6_headers.hpp",
    "fn": "ot::Ip6::OptionPadN::Init(unsigned char)",
    "line": 500
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_b7b085c9f97e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/b7b085c9f97ee2d9f16415249ccdcc9f28663fb8/ARVO-42475377/report.log",
   "testcase_size": 86
  },
  "input_reachability": [
   "otCtx",
   "aKey",
   "aValue",
   "aValueLength"
  ],
  "osv_id": "ARVO-42475377",
  "project": "openthread",
  "sites": [
   {
    "code": "FilterWriteSetting(",
    "fn": "ot::Ip6::OptionPadN::Init(unsigned char)",
    "kind": "unknown",
    "line": 500,
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
   "fn": "<clinit>",
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
    "width": 15
   },
   "code": "EXT_ADDRESS   = 0",
   "site": {
    "file": "/src/openthread/src/core/meshcop/dataset_manager_ftd.cpp",
    "fn": "ot::MeshCoP::DatasetManager::HandleSet(ot::Coap::Message&, ot::Ip6::MessageInfo const&)",
    "line": 152
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "EXT_ADDRESS",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_b694b00951ee.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/b694b00951eeeb4986387de1179d55dd38643a87/ARVO-42475955/report.log",
   "testcase_size": 89
  },
  "input_reachability": [],
  "osv_id": "ARVO-42475955",
  "project": "openthread",
  "sites": [
   {
    "code": "EXT_ADDRESS   = 0",
    "fn": "ot::MeshCoP::DatasetManager::HandleSet(ot::Coap::Message&, ot::Ip6::MessageInfo const&)",
    "kind": "unknown",
    "line": 152,
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