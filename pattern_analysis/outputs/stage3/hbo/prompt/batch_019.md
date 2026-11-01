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
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_operator_new<unsigned long>",
    "line": 235
   },
   "size_bytes": 164,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "Swap2",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 164,
    "width": 1
   },
   "code": "",
   "site": {
    "file": "/src/assimp/include/assimp/ByteSwapper.h",
    "fn": "Swap2",
    "line": 85
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_71a87b653cd4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/71a87b653cd4b5671104fe49e2e38cf5dd4d8675/ARVO-42502576/report.log",
   "testcase_size": 163
  },
  "input_reachability": [],
  "osv_id": "ARVO-42502576",
  "project": "assimp",
  "sites": [
   {
    "code": "",
    "fn": "Swap2",
    "kind": "unknown",
    "line": 85,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/mruby/src/state.c",
    "fn": "mrb_default_allocf",
    "line": 68
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "mrb_funcall_with_block",
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
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/mruby/src/vm.c",
    "fn": "mrb_funcall_with_block",
    "line": null
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_6b3b1012ca48.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/6b3b1012ca480f1e930c4ddeeaebed55e5df4144/ARVO-42503233/report.log",
   "testcase_size": 6
  },
  "input_reachability": [],
  "osv_id": "ARVO-42503233",
  "project": "mruby",
  "sites": [],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/mruby/src/state.c",
    "fn": "mrb_default_allocf",
    "line": 68
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "mrb_funcall_with_block",
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
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/mruby/src/vm.c",
    "fn": "mrb_funcall_with_block",
    "line": null
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_6b3b1012ca48.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/6b3b1012ca480f1e930c4ddeeaebed55e5df4144/ARVO-42503239/report.log",
   "testcase_size": 23805
  },
  "input_reachability": [],
  "osv_id": "ARVO-42503239",
  "project": "mruby",
  "sites": [],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
    "line": null
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1047,IF:1053,IF:1058,IF:1067,IF:1070,IF:1081,ELSE:1083,IF:1084,IF:1088,IF:1092,IF:1103,ELSE:1106",
   "fn": "processClientServerHello",
   "guard_count": 19,
   "guards": "i<extension_len | i<ja3.num_cipher | i > 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 2
   },
   "code": "(*id == 0) || (packet->payload[cipher_offset+i] != packe | *id == 0 | *id | packet->payload[cipher_offset+i] != packet->payload[ciph",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "fn": "processClientServerHello",
    "line": 1216
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1211,
    "size": null,
    "type": "u_int16_t*"
   },
   "kind": "pointer",
   "name": "id",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_1a37595de027.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/1a37595de02761497845503a390e24fc1cf11a4f/ARVO-42503489/report.log",
   "testcase_size": 122
  },
  "input_reachability": [
   "flow",
   "quic_version"
  ],
  "osv_id": "ARVO-42503489",
  "project": "ndpi",
  "sites": [
   {
    "code": "(*id == 0) || (packet->payload[cipher_offset+i] != packe | *id == 0 | *id | packet->payload[cipher_offset+i] != packet->payload[ciph",
    "fn": "processClientServerHello",
    "kind": "unknown",
    "line": 1216,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "u_int16_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_operator_new<unsigned long>",
    "line": 235
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:23,IF:30,FOR:42,IF:48,BREAK:50,ELSE:51,IF:51,IF:56,IF:64,BREAK:66,ELSE:70,IF:70",
   "fn": "PrintBasicInfo",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 1
   },
   "code": "info.exponent_bits_per_sample",
   "site": {
    "file": "/src/libjxl/lib/jxl/box_content_decoder.cc",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "line": 87
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libjxl/lib/jxl/box_content_decoder.cc",
    "line": 38,
    "size": null,
    "type": "JxlBasicInfo"
   },
   "kind": "struct",
   "name": "info",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_f0b9147ee578.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/f0b9147ee57805c4ab45abdf8d72e2da9c5a951c/ARVO-42503750/report.log",
   "testcase_size": 105
  },
  "input_reachability": [
   "file"
  ],
  "osv_id": "ARVO-42503750",
  "project": "libjxl",
  "sites": [
   {
    "code": "realloc(data, remaining + chunk_size)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "realloc",
    "line": 61,
    "origin": "cpg"
   },
   {
    "code": "info.exponent_bits_per_sample",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "unknown",
    "line": 87,
    "origin": "report:crash"
   },
   {
    "code": "malloc(extra.name_length + 1)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "malloc",
    "line": 148,
    "origin": "cpg"
   },
   {
    "code": "malloc(profile_size)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "malloc",
    "line": 242,
    "origin": "cpg"
   },
   {
    "code": "malloc(frame_header.name_length + 1)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "malloc",
    "line": 263,
    "origin": "cpg"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "JxlBasicInfo",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/net-snmp/agent/mibgroup/agentx/protocol.c",
    "fn": "agentx_parse",
    "line": 1646
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1018,IF:1022,IF:1023,ELSE:1025,IF:1035,ELSE:1039,IF:1040,ELSE:1042,IF:1047",
   "fn": "asn_build_string",
   "guard_count": 1,
   "guards": "str == NULL",
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
   "code": "memmove(data, str, strlength)",
   "site": {
    "file": "/src/net-snmp/snmplib/asn1.c",
    "fn": "asn_build_string",
    "line": 1026
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/net-snmp/snmplib/asn1.c",
    "line": 1006,
    "size": null,
    "type": "u_char*"
   },
   "kind": "pointer",
   "name": "data",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_8babb2d078f8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/8babb2d078f83a4956c7cf70a013c80f78e6f71d/ARVO-42503787/report.log",
   "testcase_size": 529
  },
  "input_reachability": [
   "data",
   "str",
   "strlength"
  ],
  "osv_id": "ARVO-42503787",
  "project": "net-snmp",
  "sites": [
   {
    "code": "memmove(data, str, strlength)",
    "fn": "asn_build_string",
    "kind": "unknown",
    "line": 1026,
    "origin": "report:crash"
   },
   {
    "code": "malloc(1 + strlength)",
    "fn": "asn_build_string",
    "kind": "malloc",
    "line": 1032,
    "origin": "cpg"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "u_char*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/net-snmp/agent/mibgroup/agentx/protocol.c",
    "fn": "agentx_parse",
    "line": 1646
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "asn_realloc_rbuild_string",
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
    "width": 1824
   },
   "code": "",
   "site": {
    "file": "/src/net-snmp/snmplib/asn1.c",
    "fn": "asn_realloc_rbuild_string",
    "line": 3094
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_8babb2d078f8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/8babb2d078f83a4956c7cf70a013c80f78e6f71d/ARVO-42503790/report.log",
   "testcase_size": 2068
  },
  "input_reachability": [],
  "osv_id": "ARVO-42503790",
  "project": "net-snmp",
  "sites": [
   {
    "code": "",
    "fn": "asn_realloc_rbuild_string",
    "kind": "unknown",
    "line": 3094,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_operator_new<unsigned long>",
    "line": 235
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1271,IF:1274,IF:1277,ELSE:1279,IF:1280,IF:1289,IF:1292,IF:1293,ELSE:1295,IF:1300",
   "fn": "WriteRingBuffer",
   "guard_count": 2,
   "guards": "num_written > to_write | num_written < to_write",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 135
   },
   "code": "memcpy(*next_out, start, num_written) | *next_out",
   "site": {
    "file": "/src/libjxl/third_party/brotli/c/dec/decode.c",
    "fn": "WriteRingBuffer",
    "line": 1281
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libjxl/third_party/brotli/c/dec/decode.c",
    "line": 1265,
    "size": null,
    "type": "uint8_t**"
   },
   "kind": "pointer",
   "name": "next_out",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_f0b9147ee578.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/f0b9147ee57805c4ab45abdf8d72e2da9c5a951c/ARVO-42503809/report.log",
   "testcase_size": 88
  },
  "input_reachability": [
   "s",
   "next_out"
  ],
  "osv_id": "ARVO-42503809",
  "project": "libjxl",
  "sites": [
   {
    "code": "memcpy(*next_out, start, num_written) | *next_out",
    "fn": "WriteRingBuffer",
    "kind": "unknown",
    "line": 1281,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "uint8_t**",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": false,
   "site": {
    "file": "/src/assimp/code/AssetLib/M3D/m3d.h",
    "fn": "_m3d_safestr",
    "line": 2119
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "_m3d_safestr",
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
   "code": "",
   "site": {
    "file": "/src/assimp/code/AssetLib/M3D/m3d.h",
    "fn": "_m3d_safestr",
    "line": 2136
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_0849f4e57395.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/0849f4e57395900ebd29531d679964e65e3904f6/ARVO-42503905/report.log",
   "testcase_size": 338
  },
  "input_reachability": [],
  "osv_id": "ARVO-42503905",
  "project": "assimp",
  "sites": [
   {
    "code": "",
    "fn": "_m3d_safestr",
    "kind": "unknown",
    "line": 2136,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 63
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1473,IF:1479,IF:1484,IF:1497,IF:1500,FOR:1505,IF:1507,IF:1509,BREAK:1512,IF:1518,IF:1524,IF:1534",
   "fn": "ih264d_mark_err_slice_skip",
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
    "width": 4
   },
   "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "fn": "ih264d_mark_err_slice_skip",
    "line": 1711
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "line": 1441,
    "size": null,
    "type": "dec_struct_t*"
   },
   "kind": "pointer",
   "name": "ps_dec",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42504256/report.log",
   "testcase_size": 4489
  },
  "input_reachability": [
   "ps_dec"
  ],
  "osv_id": "ARVO-42504256",
  "project": "libavc",
  "sites": [
   {
    "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
    "fn": "ih264d_mark_err_slice_skip",
    "kind": "unknown",
    "line": 1711,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "dec_struct_t*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
    "line": null
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:338,IF:345,IF:356,IF:358,IF:367,ELSE:370,IF:372,ELSE:375,IF:375,ELSE:379,IF:379,ELSE:382",
   "fn": "main",
   "guard_count": 2,
   "guards": "size_ <= size | size_ <= size",
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
   "code": "size = 16 * KB | 16 * KB | KB",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zlib-ng-2.0.2/inflate.c",
    "fn": "inflate",
    "line": 408
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/internal-complibs/zlib-ng-2.0.2/inflate.c",
    "line": 317,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "size",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_c4c8c7cb7f22.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/c4c8c7cb7f22323cda796575f699ad4c953b6661/ARVO-42504546/report.log",
   "testcase_size": 246
  },
  "input_reachability": [],
  "osv_id": "ARVO-42504546",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "size = 16 * KB | 16 * KB | KB",
    "fn": "inflate",
    "kind": "unknown",
    "line": 408,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/curl/lib/memdebug.c",
    "fn": "curl_domalloc",
    "line": 175
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "setcharset",
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
    "file": "/src/curl/lib/curl_fnmatch.c",
    "fn": "setcharset",
    "line": 135
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_e240a546a7ac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/curl/address/e240a546a7ac2fa7956adb664b8c40c4dee4f82b/ARVO-42505099/report.log",
   "testcase_size": 769
  },
  "input_reachability": [],
  "osv_id": "ARVO-42505099",
  "project": "curl",
  "sites": [
   {
    "code": null,
    "fn": "setcharset",
    "kind": "unknown",
    "line": 135,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 169
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:522,IF:529,FOR:543,FOR:553,FOR:554,IF:555,IF:559,ELSE:561,IF:564,ELSE:566,IF:570,ELSE:573",
   "fn": "ndlz4_decompress",
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
    "width": 201851904
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 540
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 515,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42505128/report.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42505128",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 540,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 169
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:522,IF:529,FOR:543,FOR:553,FOR:554,IF:555,IF:559,ELSE:561,IF:564,ELSE:566,IF:570,ELSE:573",
   "fn": "ndlz4_decompress",
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
    "width": 48423648
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 540
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 515,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42505679/report.log",
   "testcase_size": 36
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42505679",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 540,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
    "line": null
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "find_sdp_line_delimiter",
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
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "fn": "find_sdp_line_delimiter",
    "line": 794
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42505797/report.log",
   "testcase_size": 37
  },
  "input_reachability": [],
  "osv_id": "ARVO-42505797",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "find_sdp_line_delimiter",
    "kind": "unknown",
    "line": 794,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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