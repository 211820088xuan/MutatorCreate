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
global-buffer-overflow

## 该类型的机制背景
global-BOF 的必要条件链：
- N1 访问对象是全局数组/表
- N2 访问宽度
- N3 下标表达式及其来源
- N4 常量表 vs 可变全局缓冲区
- N5 下标是单字节还是多字节
- N6 表长是否是 2 的幂（256/512）
- N7 同一输入索引是否访问多个全局表

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "FOR:25,FOR:28,IF:41,IF:45,IF:47,ELSE:50,IF:54,IF:56,IF:58",
   "fn": "fuzzyeq",
   "guard_count": 1,
   "guards": "da > fuzz",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 15
   },
   "code": "da = iAbs(int(qAlpha(px2)) - int(qAlpha(px1))) | iAbs(int(qAlpha(px2)) - int(qAlpha(px1))) | int(qAlpha(px2)) - int(qAlpha(px1)) | int(qAlpha(px2))",
   "site": {
    "file": "/src/kimageformats/src/imageformats/ora.cpp",
    "fn": "OraHandler::read(QImage*)",
    "line": 37
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/kimageformats/src/imageformats/ora.cpp",
    "line": 37,
    "size": null,
    "type": "auto"
   },
   "kind": "struct",
   "name": "da",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_6f588c6fd3b4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/kimageformats/address/6f588c6fd3b4345e5d697b4a3b28e7ea70576ead/ARVO-408025086/report.log",
   "testcase_size": 46
  },
  "input_reachability": [
   "im1",
   "im2"
  ],
  "osv_id": "ARVO-408025086",
  "project": "kimageformats",
  "sites": [
   {
    "code": "da = iAbs(int(qAlpha(px2)) - int(qAlpha(px1))) | iAbs(int(qAlpha(px2)) - int(qAlpha(px1))) | int(qAlpha(px2)) - int(qAlpha(px1)) | int(qAlpha(px2))",
    "fn": "OraHandler::read(QImage*)",
    "kind": "unknown",
    "line": 37,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "auto",
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
   "control_structures": "IF:193,IF:200,IF:222,IF:231,FOR:245,IF:246",
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
    "width": 8
   },
   "code": "{HB_TAG ('c','l','i','g'), HB_AAT_LAYOUT_FEATURE_TYPE_LI | HB_TAG ('c','l','i','g') | (hb_tag_t)((((uint32_t)('c') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('c') & 0xFF) << 24) | (((uint32_t)('l') & 0",
   "site": {
    "file": "/src/harfbuzz/src/hb-cff2-interp-cs.hh",
    "fn": "CFF::BlendArg::set_blends(unsigned int, unsigned int, unsigned int, CFF::BlendArg const*)",
    "line": 61
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "uint32_t",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2087f5a2a743.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/harfbuzz/address/2087f5a2a743380b36399ba8a2b4ff9e93890fcf/ARVO-42471867/report.log",
   "testcase_size": 2880
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471867",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "{HB_TAG ('c','l','i','g'), HB_AAT_LAYOUT_FEATURE_TYPE_LI | HB_TAG ('c','l','i','g') | (hb_tag_t)((((uint32_t)('c') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('c') & 0xFF) << 24) | (((uint32_t)('l') & 0",
    "fn": "CFF::BlendArg::set_blends(unsigned int, unsigned int, unsigned int, CFF::BlendArg const*)",
    "kind": "unknown",
    "line": 61,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "control_structures": "IF:58,FOR:60",
   "fn": "<lambda>0",
   "guard_count": 1,
   "guards": "i < *size_of_arr",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "& descriptor = rail_descriptors[i] | rail_descriptors[i]",
   "site": {
    "file": "/src/perfetto/src/trace_processor/proto_trace_parser.cc",
    "fn": "perfetto::trace_processor::ParseSystraceTracePoint(perfetto::base::StringView, perfetto::trace_processor::SystraceTracePoint*)",
    "line": 62
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/perfetto/src/trace_processor/proto_trace_parser.cc",
    "line": 62,
    "size": null,
    "type": "RailDescriptor&"
   },
   "kind": "struct",
   "name": "descriptor",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_aa35f2e0e156.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/perfetto/address/aa35f2e0e156944fc3e7f4ba0bedc144fd78143e/ARVO-42473852/report.log",
   "testcase_size": 67
  },
  "input_reachability": [
   "r"
  ],
  "osv_id": "ARVO-42473852",
  "project": "perfetto",
  "sites": [
   {
    "code": "& descriptor = rail_descriptors[i] | rail_descriptors[i]",
    "fn": "perfetto::trace_processor::ParseSystraceTracePoint(perfetto::base::StringView, perfetto::trace_processor::SystraceTracePoint*)",
    "kind": "unknown",
    "line": 62,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "RailDescriptor&",
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
   "fn": "compcp",
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
    "file": "/src/wireshark/epan/dissectors/packet-noe.c",
    "fn": "compcp",
    "line": 1054
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_daf29e2bde25.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/wireshark/address/daf29e2bde25f931908f4b17ee5866f90f84b3ce/ARVO-42473920/report.log",
   "testcase_size": 92
  },
  "input_reachability": [],
  "osv_id": "ARVO-42473920",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "compcp",
    "kind": "unknown",
    "line": 1054,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "fn": "string_as_int32",
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
   "code": "memcpy(&i, s, sizeof(int32_t)) | &i | sizeof(int32_t)",
   "site": {
    "file": "/src/lwan/src/lib/lwan.h",
    "fn": "string_as_int32",
    "line": 139
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan.h",
    "line": 138,
    "size": null,
    "type": "int32_t"
   },
   "kind": "struct",
   "name": "i",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_5a47a0c2d988.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/5a47a0c2d988d3b3b1c8d3938b7a994f464469b5/ARVO-42474687/report.log",
   "testcase_size": 32765
  },
  "input_reachability": [
   "s"
  ],
  "osv_id": "ARVO-42474687",
  "project": "lwan",
  "sites": [
   {
    "code": "memcpy(&i, s, sizeof(int32_t)) | &i | sizeof(int32_t)",
    "fn": "string_as_int32",
    "kind": "unknown",
    "line": 139,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int32_t",
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
   "fn": "string_as_int32",
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
   "code": "memcpy(&i, s, sizeof(int32_t)) | &i | sizeof(int32_t)",
   "site": {
    "file": "/src/lwan/src/lib/lwan.h",
    "fn": "string_as_int32",
    "line": 139
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan.h",
    "line": 138,
    "size": null,
    "type": "int32_t"
   },
   "kind": "struct",
   "name": "i",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_5a47a0c2d988.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/5a47a0c2d988d3b3b1c8d3938b7a994f464469b5/ARVO-42474758/report.log",
   "testcase_size": 32759
  },
  "input_reachability": [
   "s"
  ],
  "osv_id": "ARVO-42474758",
  "project": "lwan",
  "sites": [
   {
    "code": "memcpy(&i, s, sizeof(int32_t)) | &i | sizeof(int32_t)",
    "fn": "string_as_int32",
    "kind": "unknown",
    "line": 139,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int32_t",
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
   "fn": "csnStreamDissector",
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
    "file": "/src/wireshark/epan/dissectors/packet-csn1.c",
    "fn": "csnStreamDissector",
    "line": 181
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_954548fdb951.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/wireshark/address/954548fdb951cbffbfa3c7cadb2c202919c0204c/ARVO-42474828/report.log",
   "testcase_size": 97
  },
  "input_reachability": [],
  "osv_id": "ARVO-42474828",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "csnStreamDissector",
    "kind": "unknown",
    "line": 181,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "control_structures": "IF:145,IF:149",
   "fn": "strsep_char",
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
    "width": 32759
   },
   "code": "ptr = strchr(strp, delim) | strchr(strp, delim)",
   "site": {
    "file": "/src/lwan/src/lib/lwan-request.c",
    "fn": "strsep_char",
    "line": 148
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-request.c",
    "line": 143,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "ptr",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_341dca6b2594.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/341dca6b2594eea98df73dcdb96bb80b6ccc9fb9/ARVO-42474994/report.log",
   "testcase_size": 32767
  },
  "input_reachability": [
   "strp",
   "delim"
  ],
  "osv_id": "ARVO-42474994",
  "project": "lwan",
  "sites": [
   {
    "code": "ptr = strchr(strp, delim) | strchr(strp, delim)",
    "fn": "strsep_char",
    "kind": "unknown",
    "line": 148,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
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
   "fn": "string_as_int16",
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
    "width": 2
   },
   "code": "memcpy(&i, s, sizeof(int16_t)) | &i | sizeof(int16_t)",
   "site": {
    "file": "/src/lwan/src/lib/lwan.h",
    "fn": "string_as_int16",
    "line": 146
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan.h",
    "line": 145,
    "size": null,
    "type": "int16_t"
   },
   "kind": "struct",
   "name": "i",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_341dca6b2594.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/341dca6b2594eea98df73dcdb96bb80b6ccc9fb9/ARVO-42474997/report.log",
   "testcase_size": 32768
  },
  "input_reachability": [
   "s"
  ],
  "osv_id": "ARVO-42474997",
  "project": "lwan",
  "sites": [
   {
    "code": "memcpy(&i, s, sizeof(int16_t)) | &i | sizeof(int16_t)",
    "fn": "string_as_int16",
    "kind": "unknown",
    "line": 146,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int16_t",
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
   "control_structures": "FOR:536,IF:540,BREAK:541,IF:543,IF:544,SWITCH:545,BREAK:550,IF:558,FOR:564,SWITCH:569,IF:571,CONTINUE:571",
   "fn": "parse_headers",
   "guard_count": 3,
   "guards": "next_chr == next_hdr | n_headers > N_HEADER_START | i < n_headers",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 8
   },
   "code": "header_start[n_headers++] = next_chr | header_start[n_headers++] | n_headers++",
   "site": {
    "file": "/src/lwan/src/lib/lwan-request.c",
    "fn": "parse_headers",
    "line": 553
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-request.c",
    "line": 532,
    "size": null,
    "type": "char**"
   },
   "kind": "pointer",
   "name": "header_start",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_ed0401f0889b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/ed0401f0889b6e91b41241093891e5716c24ac0b/ARVO-42475016/report.log",
   "testcase_size": 114
  },
  "input_reachability": [
   "helper",
   "buffer"
  ],
  "osv_id": "ARVO-42475016",
  "project": "lwan",
  "sites": [
   {
    "code": "header_start[n_headers++] = next_chr | header_start[n_headers++] | n_headers++",
    "fn": "parse_headers",
    "kind": "unknown",
    "line": 553,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char**",
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
   "control_structures": "WHILE:693",
   "fn": "ignore_leading_whitespace",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "lwan_char_isspace(*buffer) | *buffer",
   "site": {
    "file": "/src/lwan/src/lib/lwan-request.c",
    "fn": "ignore_leading_whitespace",
    "line": 693
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-request.c",
    "line": 691,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "buffer",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_341dca6b2594.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/341dca6b2594eea98df73dcdb96bb80b6ccc9fb9/ARVO-42475075/report.log",
   "testcase_size": 32773
  },
  "input_reachability": [
   "buffer"
  ],
  "osv_id": "ARVO-42475075",
  "project": "lwan",
  "sites": [
   {
    "code": "lwan_char_isspace(*buffer) | *buffer",
    "fn": "ignore_leading_whitespace",
    "kind": "unknown",
    "line": 693,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
   "is_signed": null,
   "ptr_origin": "param"
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
   "fn": "ihevcd_unpack_coeffs",
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
    "file": "/src/libhevc/decoder/ihevcd_iquant_itrans_recon_ctb.c",
    "fn": "ihevcd_unpack_coeffs",
    "line": 283
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_a469393436a3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libhevc/address/a469393436a31721cc47533e6479ace24e81f6a4/ARVO-42477679/report.log",
   "testcase_size": 28657
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477679",
  "project": "libhevc",
  "sites": [
   {
    "code": null,
    "fn": "ihevcd_unpack_coeffs",
    "kind": "unknown",
    "line": 283,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "control_structures": "IF:279",
   "fn": "backup",
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
   "code": "*lexer->pos == '\\n' | *lexer->pos | lexer->pos",
   "site": {
    "file": "/src/lwan/src/lib/lwan-config.c",
    "fn": "backup",
    "line": 279
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-config.c",
    "line": 275,
    "size": null,
    "type": "lexer*"
   },
   "kind": "pointer",
   "name": "lexer",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_f3aaf8f603b6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/f3aaf8f603b69f89343c06b33d234dd0a1ea8149/ARVO-42479369/report.log",
   "testcase_size": 33702
  },
  "input_reachability": [
   "lexer"
  ],
  "osv_id": "ARVO-42479369",
  "project": "lwan",
  "sites": [
   {
    "code": "*lexer->pos == '\\n' | *lexer->pos | lexer->pos",
    "fn": "backup",
    "kind": "unknown",
    "line": 279,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "lexer*",
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
   "control_structures": "DO:344,IF:345",
   "fn": "lex_multiline_string",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "!strncmp(lexer->pos, end, 3) | strncmp(lexer->pos, end, 3) | lexer->pos",
   "site": {
    "file": "/src/lwan/src/lib/lwan-config.c",
    "fn": "lex_multiline_string",
    "line": 345
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-config.c",
    "line": 338,
    "size": null,
    "type": "lexer*"
   },
   "kind": "pointer",
   "name": "lexer",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_f3aaf8f603b6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/f3aaf8f603b69f89343c06b33d234dd0a1ea8149/ARVO-42479378/report.log",
   "testcase_size": 70642
  },
  "input_reachability": [
   "lexer"
  ],
  "osv_id": "ARVO-42479378",
  "project": "lwan",
  "sites": [
   {
    "code": "!strncmp(lexer->pos, end, 3) | strncmp(lexer->pos, end, 3) | lexer->pos",
    "fn": "lex_multiline_string",
    "kind": "unknown",
    "line": 345,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "lexer*",
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
   "control_structures": "DO:344,IF:345",
   "fn": "lex_multiline_string",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 3
   },
   "code": "!strncmp(lexer->pos, end, 3) | strncmp(lexer->pos, end, 3) | lexer->pos",
   "site": {
    "file": "/src/lwan/src/lib/lwan-config.c",
    "fn": "lex_multiline_string",
    "line": 345
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-config.c",
    "line": 338,
    "size": null,
    "type": "lexer*"
   },
   "kind": "pointer",
   "name": "lexer",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_2e932a087234.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/2e932a0872344f54ec3732efa4523ac8eec4cb82/ARVO-42479497/report.log",
   "testcase_size": 32769
  },
  "input_reachability": [
   "lexer"
  ],
  "osv_id": "ARVO-42479497",
  "project": "lwan",
  "sites": [
   {
    "code": "!strncmp(lexer->pos, end, 3) | strncmp(lexer->pos, end, 3) | lexer->pos",
    "fn": "lex_multiline_string",
    "kind": "unknown",
    "line": 345,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "lexer*",
   "is_signed": null,
   "ptr_origin": "param"
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