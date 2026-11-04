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
  "osv_id": "ARVO-42483004",
  "project": "ndpi",
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
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 81
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3672,
    "fn": "ndpi_handle_ipv6_extension_headers",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_handle_ipv6_extension_headers",
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 3672
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_handle_ipv6_extension_headers",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/287015ffdc33ff2c212563ffb866b38dee64e12b/ARVO-42483004/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_287015ffdc33.cpg",
   "testcase_size": 85
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
   "dedup_token": "ndpi_handle_ipv6_extension_headers--ndpi_workflow_process_packet--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    154,
    154
   ],
   "func_params": {
    "names": [
     "ndpi_str",
     "l4ptr",
     "l4len",
     "nxt_hdr"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "u_int8_t**",
     "u_int16_t*",
     "u_int8_t*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42483004",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_handle_ipv6_extension_headers"
  }
 },
 {
  "osv_id": "ARVO-42483072",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/oracle.c",
    "line": 36,
    "size": null,
    "type": "ndpi_packet_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 253
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 46,
    "fn": "ndpi_search_oracle",
    "code": "((packet->payload[0] == 0x07) && (packet->payload[1] ==  | (packet->payload[0] == 0x07) && (packet->payload[1] == 0 | (packet->payload[0] == 0x07) && (packet->payload[1] == 0 | packet->payload[0] == 0x07",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_oracle",
    "file": "/src/ndpi/src/lib/protocols/oracle.c",
    "line": 46
   },
   "code": "((packet->payload[0] == 0x07) && (packet->payload[1] ==  | (packet->payload[0] == 0x07) && (packet->payload[1] == 0 | (packet->payload[0] == 0x07) && (packet->payload[1] == 0 | packet->payload[0] == 0x07",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_oracle",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:41,IF:45,ELSE:53,IF:53,ELSE:59"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/a845e997209b987ef85a2562697d4d0522cb0c66/ARVO-42483072/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_a845e997209b.cpg",
   "testcase_size": 81
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
   "dedup_token": "ndpi_search_oracle--check_ndpi_tcp_flow_func--ndpi_detection_process_packet"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 36
    }
   ],
   "entity_decl": {
    "line": 36,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    34,
    62
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
     "code": "packet->tcp != NULL",
     "line": 41
    },
    {
     "code": "dport == 1521",
     "line": 45
    },
    {
     "code": "sport == 1521",
     "line": 45
    },
    {
     "code": "packet->payload[0] == 0x07",
     "line": 46
    },
    {
     "code": "packet->payload[1] == 0xff",
     "line": 46
    },
    {
     "code": "packet->payload[2] == 0x00",
     "line": 46
    },
    {
     "code": "packet->payload[0] == 0x00",
     "line": 47
    },
    {
     "code": "packet->payload[0] == 0x01",
     "line": 47
    },
    {
     "code": "packet->payload[1] != 0x00",
     "line": 48
    },
    {
     "code": "packet->payload[2] == 0x00",
     "line": 49
    },
    {
     "code": "packet->payload[3] == 0x00",
     "line": 50
    },
    {
     "code": "packet->payload_packet_len == 213",
     "line": 53
    },
    {
     "code": "packet->payload[0] == 0x00",
     "line": 53
    },
    {
     "code": "packet->payload[1] == 0xd5",
     "line": 54
    },
    {
     "code": "packet->payload[2] == 0x00",
     "line": 54
    },
    {
     "code": "packet->payload[3] == 0x00",
     "line": 55
    }
   ],
   "line_call_count": 12,
   "line_calls": [
    {
     "code": "((packet->payload[0] == 0x07) && (packet->payload[1] == 0xff) && (packet->payload[2] == 0x00))",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "(packet->payload[0] == 0x07) && (packet->payload[1] == 0xff) && (packet->payload[2] == 0x00)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "(packet->payload[0] == 0x07) && (packet->payload[1] == 0xff)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "packet->payload[0] == 0x07",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload[1] == 0xff",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload[2] == 0x00",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet"
   ],
   "osv_id": "ARVO-42483072",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_oracle"
  }
 },
 {
  "osv_id": "ARVO-42483133",
  "project": "radare2",
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
    "fn": "populate_relocs_record",
    "file": "/src/radare2/libr/../libr/bin/p/../format/elf/elf.c",
    "line": 2706
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2553,
    "fn": "read_reloc",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_reloc",
    "file": "/src/radare2/libr/bin/format/elf/elf.c",
    "line": 2553
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "read_reloc",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/2d3be881cb9c23e9ec01a148c8c09222a92ba2b3/ARVO-42483133/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_2d3be881cb9c.cpg",
   "testcase_size": 16390
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
   "dedup_token": "read_reloc--populate_relocs_record_from_dynamic--populate_relocs_record"
  },
  "deep": {
   "osv_id": "ARVO-42483133"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "read_reloc"
  }
 },
 {
  "osv_id": "ARVO-42483245",
  "project": "radare2",
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
    "fn": "populate_relocs_record",
    "file": "/src/radare2/libr/../libr/bin/p/../format/elf/elf.c",
    "line": 2699
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2703,
    "fn": "populate_relocs_record",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "populate_relocs_record",
    "file": "/src/radare2/libr/bin/format/elf/elf.c",
    "line": 2703
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "populate_relocs_record",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/b18529696c2f7d0571c58059e7c1c0957f5f4f65/ARVO-42483245/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_b18529696c2f.cpg",
   "testcase_size": 4113
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
   "dedup_token": "populate_relocs_record--Elf64_r_bin_elf_get_relocs--elf_init"
  },
  "deep": {
   "osv_id": "ARVO-42483245"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "populate_relocs_record"
  }
 },
 {
  "osv_id": "ARVO-42483264",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ident_byte",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "value_len + 1",
   "size_expr_cpg_callee": "flb_malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 142,
    "fn": "logfmt_parser",
    "code": "ident_byte[*c] && (c < end) | ident_byte[*c] | *c | c < end",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "logfmt_parser",
    "file": "/src/fluent-bit/src/flb_parser_logfmt.c",
    "line": 142
   },
   "code": "ident_byte[*c] && (c < end) | ident_byte[*c] | *c | c < end",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "logfmt_parser",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "c < end | c < end | c == end",
   "guard_count": 12,
   "control_structures": "IF:85,WHILE:89,WHILE:91,IF:94,BREAK:95,WHILE:99,IF:102,BREAK:103,IF:112,IF:114,IF:115,WHILE:119"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "in_buf",
   "in_size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/754c40a5aa372b08b7773fa3c39b2c6aabf667b6/ARVO-42483264/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_754c40a5aa37.cpg",
   "testcase_size": 3
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "dedup_token": "logfmt_parser--flb_parser_logfmt_do--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "ident_byte",
   "func_lines": [
    64,
    249
   ],
   "func_params": {
    "names": [
     "parser",
     "in_buf",
     "in_size",
     "tmp_pck",
     "time_key",
     "time_key_len",
     "time_lookup",
     "tmfrac",
     "map_size"
    ],
    "types": [
     "flb_parser*",
     "char*",
     "size_t",
     "msgpack_packer*",
     "char*",
     "size_t",
     "time_t*",
     "double*",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "*map_size == 0",
     "line": 85
    },
    {
     "code": "c < end",
     "line": 89
    },
    {
     "code": "c < end",
     "line": 91
    },
    {
     "code": "c == end",
     "line": 94
    },
    {
     "code": "c < end",
     "line": 99
    },
    {
     "code": "c == end",
     "line": 102
    },
    {
     "code": "*c == '='",
     "line": 112
    },
    {
     "code": "c < end",
     "line": 114
    },
    {
     "code": "*c == '\"'",
     "line": 115
    },
    {
     "code": "c < end",
     "line": 119
    },
    {
     "code": "*c != '\\\\'",
     "line": 120
    },
    {
     "code": "*c!= '\"'",
     "line": 120
    },
    {
     "code": "*c == '\\\\'",
     "line": 123
    },
    {
     "code": "c == end",
     "line": 126
    },
    {
     "code": "c < end",
     "line": 136
    },
    {
     "code": "*c == '\\\"'",
     "line": 136
    },
    {
     "code": "c < end",
     "line": 142
    },
    {
     "code": "key_len > 0",
     "line": 150
    },
    {
     "code": "key_len == time_key_len",
     "line": 153
    },
    {
     "code": "value_len > 0",
     "line": 154
    },
    {
     "code": "ret == -1",
     "line": 159
    },
    {
     "code": "time_found == FLB_FALSE",
     "line": 169
    },
    {
     "code": "parser->time_keep == FLB_TRUE",
     "line": 169
    },
    {
     "code": "parser->types_len != 0",
     "line": 171
    },
    {
     "code": "value_len == 0",
     "line": 181
    },
    {
     "code": "value_str == FLB_TRUE",
     "line": 182
    },
    {
     "code": "value_escape == FLB_TRUE",
     "line": 190
    },
    {
     "code": "out_str == NULL",
     "line": 195
    },
    {
     "code": "c == end",
     "line": 227
    },
    {
     "code": "*c == '\\r'",
     "line": 231
    },
    {
     "code": "c == end",
     "line": 233
    },
    {
     "code": "*c == '\\n'",
     "line": 236
    },
    {
     "code": "*c == '\\n'",
     "line": 241
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "ident_byte[*c] && (c < end)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "ident_byte[*c]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "*c",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "c < end",
     "name": "<operator>.lessThan",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ident_byte",
    "c",
    "end"
   ],
   "osv_id": "ARVO-42483264",
   "sites": [
    {
     "args": "value_len + 1",
     "callee": "flb_malloc",
     "code": "flb_malloc(value_len + 1)",
     "line": 194
    },
    {
     "args": "out_str",
     "callee": "flb_free",
     "code": "flb_free(out_str)",
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
   "use_fn": "logfmt_parser"
  }
 },
 {
  "osv_id": "ARVO-42483342",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "slen",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 6005,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 253
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 6016,
    "fn": "ndpi_strnstr",
    "code": "slen-- < 1 || (sc = *s++) == '\\0' | slen-- < 1 | slen-- | (sc = *s++) == '\\0'",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_strnstr",
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 6016
   },
   "code": "slen-- < 1 || (sc = *s++) == '\\0' | slen-- < 1 | slen-- | (sc = *s++) == '\\0'",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_strnstr",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "sc != c | len > slen",
   "guard_count": 2,
   "control_structures": "IF:6010,DO:6012,DO:6015,IF:6016,IF:6019"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "s",
   "find",
   "slen"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/4148c5e065d32128eea17c0e228e372ad72eef82/ARVO-42483342/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_4148c5e065d3.cpg",
   "testcase_size": 40
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
   "dedup_token": "ndpi_strnstr--ndpi_search_nats_tcp--check_ndpi_tcp_flow_func"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 6005,
    "type": "size_t"
   },
   "entity_name_cpg": "slen",
   "func_lines": [
    6005,
    6026
   ],
   "func_params": {
    "names": [
     "s",
     "find",
     "slen"
    ],
    "types": [
     "char*",
     "char*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "(c = *find++) != '\\0'",
     "line": 6010
    },
    {
     "code": "slen-- < 1",
     "line": 6016
    },
    {
     "code": "(sc = *s++) == '\\0'",
     "line": 6016
    },
    {
     "code": "sc != c",
     "line": 6018
    },
    {
     "code": "len > slen",
     "line": 6019
    },
    {
     "code": "strncmp(s, find, len) != 0",
     "line": 6021
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "slen-- < 1 ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "slen-- < 1",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "slen--",
     "name": "<operator>.postDecrement",
     "nargs": 1
    },
    {
     "code": "(sc = *s++) == '\\0'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "sc = *s++",
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
    "slen",
    "sc",
    "s"
   ],
   "osv_id": "ARVO-42483342",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_strnstr"
  }
 },
 {
  "osv_id": "ARVO-42483473",
  "project": "leptonica",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "val",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/colorquant1.c",
    "line": 3315,
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
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "LEPT_CALLOC"
  },
  "sites": [
   {
    "code": "calloc(256, sizeof (l_int32))",
    "fn": "pixFewColorsOctcubeQuantMixed",
    "kind": "calloc",
    "line": 3343,
    "origin": "cpg",
    "args": "256"
   },
   {
    "kind": "unknown",
    "line": 3383,
    "fn": "pixFewColorsOctcubeQuantMixed",
    "code": "val = GET_DATA_BYTE(linec, j) | GET_DATA_BYTE(linec, j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(linec) + (j | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(linec) + (j)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixFewColorsOctcubeQuantMixed",
    "file": "/src/leptonica/src/colorquant1.c",
    "line": 3383
   },
   "code": "val = GET_DATA_BYTE(linec, j) | GET_DATA_BYTE(linec, j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(linec) + (j | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(linec) + (j)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "pixFewColorsOctcubeQuantMixed",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j < w",
   "guard_count": 1,
   "control_structures": "IF:3323,IF:3325,IF:3326,IF:3328,IF:3329,IF:3330,IF:3331,IF:3332,IF:3335,FOR:3344,FOR:3346,IF:3350"
  },
  "call_chain": [],
  "types": {
   "entity_type": "l_int32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/695ff35cab05b6e7f80da48118a2b8fbe76d74e3/ARVO-42483473/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_695ff35cab05.cpg",
   "testcase_size": 36
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "pixFewColorsOctcubeQuantMixed--LLVMFuzzerTestOneInput--ExecuteFilesOnyByOne"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "val = GET_DATA_BYTE(linec, j)",
     "line": 3383
    }
   ],
   "entity_decl": {
    "line": 3315,
    "type": "l_int32"
   },
   "entity_name_cpg": "val",
   "func_lines": [
    3305,
    3401
   ],
   "func_params": {
    "names": [
     "pixs",
     "level",
     "darkthresh",
     "lightthresh",
     "diffthresh",
     "minfract",
     "maxspan"
    ],
    "types": [
     "PIX*",
     "l_int32",
     "l_int32",
     "l_int32",
     "l_int32",
     "l_float32",
     "l_int32"
    ]
   },
   "guards": [
    {
     "code": "pixGetDepth(pixs) != 32",
     "line": 3323
    },
    {
     "code": "level > 6",
     "line": 3326
    },
    {
     "code": "(pixc = pixFewColorsOctcubeQuant1(pixs, level)) == NULL",
     "line": 3335
    },
    {
     "code": "i < 256",
     "line": 3344
    },
    {
     "code": "i < ncolors",
     "line": 3346
    },
    {
     "code": "(rval) < (gval)",
     "line": 3348
    },
    {
     "code": "(minval) < (bval)",
     "line": 3349
    },
    {
     "code": "minval > lightthresh",
     "line": 3350
    },
    {
     "code": "(rval) > (gval)",
     "line": 3352
    },
    {
     "code": "(maxval) > (bval)",
     "line": 3353
    },
    {
     "code": "maxval < darkthresh",
     "line": 3354
    },
    {
     "code": "i < h",
     "line": 3378
    },
    {
     "code": "j < w",
     "line": 3382
    },
    {
     "code": "lut[val] == -1",
     "line": 3384
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "val = GET_DATA_BYTE(linec, j)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "GET_DATA_BYTE(linec, j)",
     "name": "GET_DATA_BYTE",
     "nargs": 2
    },
    {
     "code": "*(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(linec) + (j)) ^ 3)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(linec) + (j)) ^ 3)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(l_uintptr_t)((const l_uint8 *)(linec) + (j)) ^ 3",
     "name": "<operator>.xor",
     "nargs": 2
    },
    {
     "code": "(l_uintptr_t)((const l_uint8 *)(linec) + (j))",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(const l_uint8 *)(linec) + (j)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(const l_uint8 *)(linec)",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "val",
    "linec",
    "j"
   ],
   "osv_id": "ARVO-42483473",
   "sites": [
    {
     "args": "256",
     "callee": "LEPT_CALLOC",
     "code": "LEPT_CALLOC(256, sizeof(l_int32))",
     "line": 3343
    },
    {
     "args": "256 ;; sizeof (l_int32)",
     "callee": "calloc",
     "code": "calloc(256, sizeof (l_int32))",
     "line": 3343
    },
    {
     "args": "lut",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(lut)",
     "line": 3396
    },
    {
     "args": "lut",
     "callee": "free",
     "code": "free(lut)",
     "line": 3396
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "pixFewColorsOctcubeQuantMixed"
  }
 },
 {
  "osv_id": "ARVO-42483502",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 4781,
    "size": null,
    "type": "ndpi_flow_struct*"
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
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "4",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 4812,
    "fn": "ndpi_parse_packet_line_info",
    "code": "memcpy(&flow->initial_binary_bytes, &packet->payload[a1] | &flow->initial_binary_bytes | flow->initial_binary_bytes | &packet->payload[a1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_parse_packet_line_info",
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 4812
   },
   "code": "memcpy(&flow->initial_binary_bytes, &packet->payload[a1] | &flow->initial_binary_bytes | flow->initial_binary_bytes | &packet->payload[a1]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_parse_packet_line_info",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "diff > 0",
   "guard_count": 1,
   "control_structures": "IF:4785,IF:4788,FOR:4797,IF:4798,IF:4801,IF:4804,IF:4811,IF:4821,IF:4830,IF:4839,IF:4845,IF:4849"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/cd765c08d6f1038ea5efd7a7cc556ca89bdec9e4/ARVO-42483502/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_cd765c08d6f1.cpg",
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
   "dedup_token": "__asan_memcpy--ndpi_parse_packet_line_info--ndpi_check_steam_http"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->initial_binary_bytes_len = diff",
     "line": 4813
    },
    {
     "code": "flow->http.response_status_code = atoi(buf)",
     "line": 4837
    },
    {
     "code": "flow->http.response_status_code = 0",
     "line": 4840
    }
   ],
   "entity_decl": {
    "line": 4781,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    4781,
    5037
   ],
   "func_params": {
    "names": [
     "ndpi_str",
     "flow"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*"
    ]
   },
   "guards": [
    {
     "code": "packet->payload_packet_len < 3",
     "line": 4785
    },
    {
     "code": "packet->payload == NULL",
     "line": 4785
    },
    {
     "code": "packet->packet_lines_parsed_complete != 0",
     "line": 4788
    },
    {
     "code": "a < packet->payload_packet_len",
     "line": 4797
    },
    {
     "code": "packet->parsed_lines < NDPI_MAX_PARSE_LINES_PER_PACKET",
     "line": 4797
    },
    {
     "code": "get_u_int16_t(packet->payload, a) == ntohs(0x0d0a)",
     "line": 4801
    },
    {
     "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a)",
     "line": 4804
    },
    {
     "code": "diff > 0",
     "line": 4811
    },
    {
     "code": "packet->parsed_lines == 0",
     "line": 4821
    },
    {
     "code": "strncasecmp((const char *) packet->line[0].ptr, \"HTTP/1.\", NDPI_STATICSTRING_LEN(\"HTTP/1.\")) == 0",
     "line": 4822
    },
    {
     "code": "packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.X \")] > '0'",
     "line": 4823
    },
    {
     "code": "packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.X \")] < '6'",
     "line": 4824
    },
    {
     "code": "flow->http.response_status_code < 100",
     "line": 4839
    },
    {
     "code": "flow->http.response_status_code > 509",
     "line": 4839
    },
    {
     "code": "packet->line[packet->parsed_lines].len > NDPI_STATICSTRING_LEN(\"Server:\") + 1",
     "line": 4845
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr,",
     "line": 4846
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[NDPI_STATICSTRING_LEN(\"Server:\")] == ' '",
     "line": 4849
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 6",
     "line": 4861
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Host:\", 5) == 0",
     "line": 4862
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[5] == ' '",
     "line": 4864
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 17",
     "line": 4874
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"X-Forwarded-For:\", 16) == 0",
     "line": 4875
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[16] == ' '",
     "line": 4877
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 14",
     "line": 4887
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Type: \", 14) == 0",
     "line": 4888
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-type: \", 14) == 0",
     "line": 4889
    },
    {
     "code": "packet->content_line.len > 0",
     "line": 4893
    },
    {
     "code": "packet->content_line.ptr[0] == ' '",
     "line": 4893
    },
    {
     "code": "packet->content_line.len == 0",
     "line": 4899
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 13",
     "line": 4899
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-type:\", 13) == 0",
     "line": 4900
    },
    {
     "code": "packet->content_line.len > 0",
     "line": 4906
    },
    {
     "code": "separator[i] != '\\0'",
     "line": 4911
    },
    {
     "code": "c != NULL",
     "line": 4914
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4920
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept: \", 8) == 0",
     "line": 4921
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 9",
     "line": 4927
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Referer: \", 9) == 0",
     "line": 4928
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 12",
     "line": 4934
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"User-Agent: \", 12) == 0",
     "line": 4935
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"User-agent: \", 12) == 0",
     "line": 4936
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 18",
     "line": 4942
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Encoding: \", 18) == 0",
     "line": 4943
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 19",
     "line": 4949
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Transfer-Encoding: \", 19) == 0",
     "line": 4950
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 16",
     "line": 4956
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Length: \", 16) == 0",
     "line": 4957
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"content-length: \", 16) == 0",
     "line": 4958
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4964
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Cookie: \", 8) == 0",
     "line": 4965
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4971
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Origin: \", 8) == 0",
     "line": 4972
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 16",
     "line": 4978
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"X-Session-Type: \", 16) == 0",
     "line": 4979
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 6",
     "line": 4990
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Date: \", 6) == 0",
     "line": 4991
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Vary: \", 6) == 0",
     "line": 4992
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"ETag: \", 6) == 0",
     "line": 4993
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4994
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Pragma: \", 8) == 0",
     "line": 4995
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 9",
     "line": 4996
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Expires: \", 9) == 0",
     "line": 4997
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 12",
     "line": 4998
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Set-Cookie: \", 12) == 0",
     "line": 4999
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Keep-Alive: \", 12) == 0",
     "line": 5000
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Connection: \", 12) == 0",
     "line": 5001
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 15",
     "line": 5002
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Last-Modified: \", 15) == 0",
     "line": 5003
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Ranges: \", 15) == 0",
     "line": 5004
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 17",
     "line": 5005
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Language: \", 17) == 0",
     "line": 5006
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Encoding: \", 17) == 0",
     "line": 5007
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 27",
     "line": 5008
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr,",
     "line": 5009
    },
    {
     "code": "packet->line[packet->parsed_lines].len == 0",
     "line": 5015
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "memcpy(&flow->initial_binary_bytes, &packet->payload[a1], diff)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&flow->initial_binary_bytes",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "flow->initial_binary_bytes",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "&packet->payload[a1]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "packet->payload[a1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "flow",
    "packet",
    "a1",
    "diff"
   ],
   "osv_id": "ARVO-42483502",
   "sites": [
    {
     "args": "4",
     "callee": "<operator>.alloc",
     "code": "buf[4]",
     "line": 4831
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_parse_packet_line_info"
  }
 },
 {
  "osv_id": "ARVO-42483504",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 4783,
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
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "4",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 4804,
    "fn": "ndpi_parse_packet_line_info",
    "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a) | get_u_int16_t(packet->payload, a+2) | packet->payload | a+2",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_parse_packet_line_info",
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 4804
   },
   "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a) | get_u_int16_t(packet->payload, a+2) | packet->payload | a+2",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_parse_packet_line_info",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "a < packet->payload_packet_len",
   "guard_count": 1,
   "control_structures": "IF:4785,IF:4788,FOR:4797,IF:4798,IF:4801,IF:4804,IF:4811,IF:4821,IF:4830,IF:4839,IF:4845,IF:4849"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/cd765c08d6f1038ea5efd7a7cc556ca89bdec9e4/ARVO-42483504/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_cd765c08d6f1.cpg",
   "testcase_size": 141
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
   "dedup_token": "ndpi_parse_packet_line_info--ndpi_search_mail_smtp_tcp--check_ndpi_tcp_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 4783
    },
    {
     "code": "packet->packet_lines_parsed_complete = 1",
     "line": 4791
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr = packet->payload",
     "line": 4794
    },
    {
     "code": "packet->line[packet->parsed_lines].len = 0",
     "line": 4795
    },
    {
     "code": "packet->line[packet->parsed_lines].len =",
     "line": 4817
    },
    {
     "code": "packet->http_response.ptr = &packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.1 \")]",
     "line": 4825
    },
    {
     "code": "packet->http_response.len = packet->line[0].len - NDPI_STATICSTRING_LEN(\"HTTP/1.1 \")",
     "line": 4826
    },
    {
     "code": "packet->server_line.ptr =",
     "line": 4850
    },
    {
     "code": "packet->server_line.len =",
     "line": 4852
    },
    {
     "code": "packet->server_line.ptr = &packet->line[packet->parsed_lines].ptr[NDPI_STATICSTRING_LEN(\"Server:\")]",
     "line": 4855
    },
    {
     "code": "packet->server_line.len = packet->line[packet->parsed_lines].len - NDPI_STATICSTRING_LEN(\"Server:\")",
     "line": 4856
    },
    {
     "code": "packet->host_line.ptr = &packet->line[packet->parsed_lines].ptr[6]",
     "line": 4865
    },
    {
     "code": "packet->host_line.len = packet->line[packet->parsed_lines].len - 6",
     "line": 4866
    },
    {
     "code": "packet->host_line.ptr = &packet->line[packet->parsed_lines].ptr[5]",
     "line": 4868
    },
    {
     "code": "packet->host_line.len = packet->line[packet->parsed_lines].len - 5",
     "line": 4869
    },
    {
     "code": "packet->forwarded_line.ptr = &packet->line[packet->parsed_lines].ptr[17]",
     "line": 4878
    },
    {
     "code": "packet->forwarded_line.len = packet->line[packet->parsed_lines].len - 17",
     "line": 4879
    },
    {
     "code": "packet->forwarded_line.ptr = &packet->line[packet->parsed_lines].ptr[16]",
     "line": 4881
    },
    {
     "code": "packet->forwarded_line.len = packet->line[packet->parsed_lines].len - 16",
     "line": 4882
    },
    {
     "code": "packet->content_line.ptr = &packet->line[packet->parsed_lines].ptr[14]",
     "line": 4890
    },
    {
     "code": "packet->content_line.len = packet->line[packet->parsed_lines].len - 14",
     "line": 4891
    },
    {
     "code": "packet->content_line.ptr = &packet->line[packet->parsed_lines].ptr[13]",
     "line": 4901
    },
    {
     "code": "packet->content_line.len = packet->line[packet->parsed_lines].len - 13",
     "line": 4902
    },
    {
     "code": "packet->content_line.len = c - (char *) packet->content_line.ptr",
     "line": 4915
    },
    {
     "code": "packet->accept_line.ptr = &packet->line[packet->parsed_lines].ptr[8]",
     "line": 4922
    },
    {
     "code": "packet->accept_line.len = packet->line[packet->parsed_lines].len - 8",
     "line": 4923
    },
    {
     "code": "packet->referer_line.ptr = &packet->line[packet->parsed_lines].ptr[9]",
     "line": 4929
    },
    {
     "code": "packet->referer_line.len = packet->line[packet->parsed_lines].len - 9",
     "line": 4930
    },
    {
     "code": "packet->user_agent_line.ptr = &packet->line[packet->parsed_lines].ptr[12]",
     "line": 4937
    },
    {
     "code": "packet->user_agent_line.len = packet->line[packet->parsed_lines].len - 12",
     "line": 4938
    },
    {
     "code": "packet->http_encoding.ptr = &packet->line[packet->parsed_lines].ptr[18]",
     "line": 4944
    },
    {
     "code": "packet->http_encoding.len = packet->line[packet->parsed_lines].len - 18",
     "line": 4945
    },
    {
     "code": "packet->http_transfer_encoding.ptr = &packet->line[packet->parsed_lines].ptr[19]",
     "line": 4951
    },
    {
     "code": "packet->http_transfer_encoding.len = packet->line[packet->parsed_lines].len - 19",
     "line": 4952
    },
    {
     "code": "packet->http_contentlen.ptr = &packet->line[packet->parsed_lines].ptr[16]",
     "line": 4959
    },
    {
     "code": "packet->http_contentlen.len = packet->line[packet->parsed_lines].len - 16",
     "line": 4960
    },
    {
     "code": "packet->http_cookie.ptr = &packet->line[packet->parsed_lines].ptr[8]",
     "line": 4966
    },
    {
     "code": "packet->http_cookie.len = packet->line[packet->parsed_lines].len - 8",
     "line": 4967
    },
    {
     "code": "packet->http_origin.ptr = &packet->line[packet->parsed_lines].ptr[8]",
     "line": 4973
    },
    {
     "code": "packet->http_origin.len = packet->line[packet->parsed_lines].len - 8",
     "line": 4974
    },
    {
     "code": "packet->http_x_session_type.ptr = &packet->line[packet->parsed_lines].ptr[16]",
     "line": 4980
    },
    {
     "code": "packet->http_x_session_type.len = packet->line[packet->parsed_lines].len - 16",
     "line": 4981
    },
    {
     "code": "packet->empty_line_position = a",
     "line": 5016
    },
    {
     "code": "packet->empty_line_position_set = 1",
     "line": 5017
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr = &packet->payload[a + 2]",
     "line": 5024
    },
    {
     "code": "packet->line[packet->parsed_lines].len = 0",
     "line": 5025
    },
    {
     "code": "packet->line[packet->parsed_lines].len =",
     "line": 5032
    }
   ],
   "entity_decl": {
    "line": 4783,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    4781,
    5037
   ],
   "func_params": {
    "names": [
     "ndpi_str",
     "flow"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*"
    ]
   },
   "guards": [
    {
     "code": "packet->payload_packet_len < 3",
     "line": 4785
    },
    {
     "code": "packet->payload == NULL",
     "line": 4785
    },
    {
     "code": "packet->packet_lines_parsed_complete != 0",
     "line": 4788
    },
    {
     "code": "a < packet->payload_packet_len",
     "line": 4797
    },
    {
     "code": "packet->parsed_lines < NDPI_MAX_PARSE_LINES_PER_PACKET",
     "line": 4797
    },
    {
     "code": "get_u_int16_t(packet->payload, a) == ntohs(0x0d0a)",
     "line": 4801
    },
    {
     "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a)",
     "line": 4804
    },
    {
     "code": "diff > 0",
     "line": 4811
    },
    {
     "code": "packet->parsed_lines == 0",
     "line": 4821
    },
    {
     "code": "strncasecmp((const char *) packet->line[0].ptr, \"HTTP/1.\", NDPI_STATICSTRING_LEN(\"HTTP/1.\")) == 0",
     "line": 4822
    },
    {
     "code": "packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.X \")] > '0'",
     "line": 4823
    },
    {
     "code": "packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.X \")] < '6'",
     "line": 4824
    },
    {
     "code": "flow->http.response_status_code < 100",
     "line": 4839
    },
    {
     "code": "flow->http.response_status_code > 509",
     "line": 4839
    },
    {
     "code": "packet->line[packet->parsed_lines].len > NDPI_STATICSTRING_LEN(\"Server:\") + 1",
     "line": 4845
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr,",
     "line": 4846
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[NDPI_STATICSTRING_LEN(\"Server:\")] == ' '",
     "line": 4849
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 6",
     "line": 4861
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Host:\", 5) == 0",
     "line": 4862
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[5] == ' '",
     "line": 4864
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 17",
     "line": 4874
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"X-Forwarded-For:\", 16) == 0",
     "line": 4875
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[16] == ' '",
     "line": 4877
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 14",
     "line": 4887
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Type: \", 14) == 0",
     "line": 4888
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-type: \", 14) == 0",
     "line": 4889
    },
    {
     "code": "packet->content_line.len > 0",
     "line": 4893
    },
    {
     "code": "packet->content_line.ptr[0] == ' '",
     "line": 4893
    },
    {
     "code": "packet->content_line.len == 0",
     "line": 4899
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 13",
     "line": 4899
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-type:\", 13) == 0",
     "line": 4900
    },
    {
     "code": "packet->content_line.len > 0",
     "line": 4906
    },
    {
     "code": "separator[i] != '\\0'",
     "line": 4911
    },
    {
     "code": "c != NULL",
     "line": 4914
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4920
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept: \", 8) == 0",
     "line": 4921
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 9",
     "line": 4927
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Referer: \", 9) == 0",
     "line": 4928
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 12",
     "line": 4934
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"User-Agent: \", 12) == 0",
     "line": 4935
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"User-agent: \", 12) == 0",
     "line": 4936
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 18",
     "line": 4942
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Encoding: \", 18) == 0",
     "line": 4943
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 19",
     "line": 4949
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Transfer-Encoding: \", 19) == 0",
     "line": 4950
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 16",
     "line": 4956
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Length: \", 16) == 0",
     "line": 4957
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"content-length: \", 16) == 0",
     "line": 4958
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4964
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Cookie: \", 8) == 0",
     "line": 4965
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4971
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Origin: \", 8) == 0",
     "line": 4972
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 16",
     "line": 4978
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"X-Session-Type: \", 16) == 0",
     "line": 4979
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 6",
     "line": 4990
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Date: \", 6) == 0",
     "line": 4991
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Vary: \", 6) == 0",
     "line": 4992
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"ETag: \", 6) == 0",
     "line": 4993
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4994
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Pragma: \", 8) == 0",
     "line": 4995
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 9",
     "line": 4996
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Expires: \", 9) == 0",
     "line": 4997
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 12",
     "line": 4998
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Set-Cookie: \", 12) == 0",
     "line": 4999
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Keep-Alive: \", 12) == 0",
     "line": 5000
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Connection: \", 12) == 0",
     "line": 5001
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 15",
     "line": 5002
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Last-Modified: \", 15) == 0",
     "line": 5003
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Ranges: \", 15) == 0",
     "line": 5004
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 17",
     "line": 5005
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Language: \", 17) == 0",
     "line": 5006
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Encoding: \", 17) == 0",
     "line": 5007
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 27",
     "line": 5008
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr,",
     "line": 5009
    },
    {
     "code": "packet->line[packet->parsed_lines].len == 0",
     "line": 5015
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a)",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "get_u_int16_t(packet->payload, a+2)",
     "name": "get_u_int16_t",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a+2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "ntohs(0x0d0a)",
     "name": "ntohs",
     "nargs": 1
    }
   ],
   "line_ids": [
    "packet",
    "a"
   ],
   "osv_id": "ARVO-42483504",
   "sites": [
    {
     "args": "4",
     "callee": "<operator>.alloc",
     "code": "buf[4]",
     "line": 4831
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_parse_packet_line_info"
  }
 },
 {
  "osv_id": "ARVO-42483517",
  "project": "fluent-bit",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "str",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/fluent-bit/src/flb_unescape.c",
    "line": 70,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "9",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 96,
    "fn": "u8_read_escape_sequence",
    "code": "octal_digit(str[i]) && dno < 3 | octal_digit(str[i]) | str[i] | dno < 3",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "u8_read_escape_sequence",
    "file": "/src/fluent-bit/src/flb_unescape.c",
    "line": 96
   },
   "code": "octal_digit(str[i]) && dno < 3 | octal_digit(str[i]) | str[i] | dno < 3",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "u8_read_escape_sequence",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "dno < 3 | dno < 2 | dno > 0",
   "guard_count": 7,
   "control_structures": "IF:78,ELSE:80,IF:80,ELSE:82,IF:82,ELSE:84,IF:84,ELSE:86,IF:86,ELSE:88,IF:88,ELSE:90"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "str",
   "dest"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/754c40a5aa372b08b7773fa3c39b2c6aabf667b6/ARVO-42483517/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_754c40a5aa37.cpg",
   "testcase_size": 5
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
   "dedup_token": "u8_read_escape_sequence--flb_unescape_string_utf8--logfmt_parser"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 70,
    "type": "char*"
   },
   "entity_name_cpg": "str",
   "func_lines": [
    70,
    123
   ],
   "func_params": {
    "names": [
     "str",
     "dest"
    ],
    "types": [
     "char*",
     "uint32_t*"
    ]
   },
   "guards": [
    {
     "code": "str[0] == 'n'",
     "line": 78
    },
    {
     "code": "str[0] == 't'",
     "line": 80
    },
    {
     "code": "str[0] == 'r'",
     "line": 82
    },
    {
     "code": "str[0] == 'b'",
     "line": 84
    },
    {
     "code": "str[0] == 'f'",
     "line": 86
    },
    {
     "code": "str[0] == 'v'",
     "line": 88
    },
    {
     "code": "str[0] == 'a'",
     "line": 90
    },
    {
     "code": "dno < 3",
     "line": 96
    },
    {
     "code": "str[0] == 'x'",
     "line": 99
    },
    {
     "code": "dno < 2",
     "line": 100
    },
    {
     "code": "dno > 0",
     "line": 103
    },
    {
     "code": "str[0] == 'u'",
     "line": 106
    },
    {
     "code": "dno < 4",
     "line": 107
    },
    {
     "code": "dno > 0",
     "line": 110
    },
    {
     "code": "str[0] == 'U'",
     "line": 113
    },
    {
     "code": "dno < 8",
     "line": 114
    },
    {
     "code": "dno > 0",
     "line": 117
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "octal_digit(str[i]) && dno < 3",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "octal_digit(str[i])",
     "name": "octal_digit",
     "nargs": 1
    },
    {
     "code": "str[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "dno < 3",
     "name": "<operator>.lessThan",
     "nargs": 2
    }
   ],
   "line_ids": [
    "str",
    "i",
    "dno"
   ],
   "osv_id": "ARVO-42483517",
   "sites": [
    {
     "args": "9",
     "callee": "<operator>.alloc",
     "code": "digs[9]=\"\\0\\0\\0\\0\\0\\0\\0\\0\"",
     "line": 73
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "u8_read_escape_sequence"
  }
 },
 {
  "osv_id": "ARVO-42483588",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/openvpn.c",
    "line": 67,
    "size": null,
    "type": "ndpi_flow_struct*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 125,
    "fn": "ndpi_search_openvpn",
    "code": "memcmp(flow->ovpn_session_id, session_remote, 8) == 0 | memcmp(flow->ovpn_session_id, session_remote, 8) | flow->ovpn_session_id",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_openvpn",
    "file": "/src/ndpi/src/lib/protocols/openvpn.c",
    "line": 125
   },
   "code": "memcmp(flow->ovpn_session_id, session_remote, 8) == 0 | memcmp(flow->ovpn_session_id, session_remote, 8) | flow->ovpn_session_id",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_openvpn",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:76,IF:78,IF:83,IF:91,IF:106,IF:108,ELSE:116,IF:116,IF:121,IF:125,ELSE:129,ELSE:137"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42483588/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "testcase_size": 680
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--bcmp--ndpi_search_openvpn"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 67,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    66,
    147
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
     "code": "packet->tcp != NULL",
     "line": 78
    },
    {
     "code": "flow->num_processed_pkts == 1",
     "line": 92
    },
    {
     "code": "packet->payload_packet_len == 112",
     "line": 94
    },
    {
     "code": "opcode == 168",
     "line": 95
    },
    {
     "code": "opcode == 192",
     "line": 95
    },
    {
     "code": "packet->payload_packet_len == 80",
     "line": 97
    },
    {
     "code": "opcode == 184",
     "line": 98
    },
    {
     "code": "opcode == 88",
     "line": 98
    },
    {
     "code": "opcode == 160",
     "line": 98
    },
    {
     "code": "opcode == 168",
     "line": 98
    },
    {
     "code": "opcode == 200",
     "line": 98
    },
    {
     "code": "flow->ovpn_counter < P_HARD_RESET_CLIENT_MAX_COUNT",
     "line": 106
    },
    {
     "code": "opcode == P_CONTROL_HARD_RESET_CLIENT_V1",
     "line": 106
    },
    {
     "code": "opcode == P_CONTROL_HARD_RESET_CLIENT_V2",
     "line": 107
    },
    {
     "code": "check_pkid_and_detect_hmac_size(ovpn_payload) > 0",
     "line": 108
    },
    {
     "code": "opcode == P_CONTROL_HARD_RESET_SERVER_V1",
     "line": 117
    },
    {
     "code": "opcode == P_CONTROL_HARD_RESET_SERVER_V2",
     "line": 117
    },
    {
     "code": "hmac_size > 0",
     "line": 121
    },
    {
     "code": "memcmp(flow->ovpn_session_id, session_remote, 8) == 0",
     "line": 125
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memcmp(flow->ovpn_session_id, session_remote, 8) == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "memcmp(flow->ovpn_session_id, session_remote, 8)",
     "name": "memcmp",
     "nargs": 3
    },
    {
     "code": "flow->ovpn_session_id",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "flow",
    "session_remote"
   ],
   "osv_id": "ARVO-42483588",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_openvpn"
  }
 },
 {
  "osv_id": "ARVO-42483644",
  "project": "leptonica",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "val",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2592,
    "type": "l_int32",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pixReadMemBmp",
    "file": "/src/leptonica/src/bmpio.c",
    "line": 259
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2635,
    "fn": "pixGetRGBComponentCmap",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixGetRGBComponentCmap",
    "file": "/src/leptonica/src/pix2.c",
    "line": 2635
   },
   "code": "val = cta[index].red",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "pixGetRGBComponentCmap",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/a4caea083c23e22d01265d878a4a52e089bef370/ARVO-42483644/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_a4caea083c23.cpg",
   "testcase_size": 190
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
   "dedup_token": "pixGetRGBComponentCmap--pixGetRGBComponent--pixUnsharpMasking"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "val = cta[index].red",
     "line": 2635
    },
    {
     "code": "val = cta[index].green",
     "line": 2641
    },
    {
     "code": "val = cta[index].blue",
     "line": 2647
    }
   ],
   "entity_decl": {
    "line": 2592,
    "type": "l_int32"
   },
   "entity_name_cpg": "val",
   "func_lines": [
    2588,
    2655
   ],
   "func_params": {
    "names": [
     "pixs",
     "comp"
    ],
    "types": [
     "PIX*",
     "l_int32"
    ]
   },
   "guards": [
    {
     "code": "(cmap = pixGetColormap(pixs)) == NULL",
     "line": 2604
    },
    {
     "code": "comp == L_ALPHA_CHANNEL",
     "line": 2606
    },
    {
     "code": "comp != COLOR_RED",
     "line": 2608
    },
    {
     "code": "comp != COLOR_GREEN",
     "line": 2608
    },
    {
     "code": "comp != COLOR_BLUE",
     "line": 2608
    },
    {
     "code": "pixGetDepth(pixs) == 8",
     "line": 2612
    },
    {
     "code": "(pixd = pixCreateNoInit(w, h, 8)) == NULL",
     "line": 2618
    },
    {
     "code": "i < h",
     "line": 2629
    },
    {
     "code": "comp == COLOR_RED",
     "line": 2632
    },
    {
     "code": "j < w",
     "line": 2633
    },
    {
     "code": "comp == COLOR_GREEN",
     "line": 2638
    },
    {
     "code": "j < w",
     "line": 2639
    },
    {
     "code": "comp == COLOR_BLUE",
     "line": 2644
    },
    {
     "code": "j < w",
     "line": 2645
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "val = cta[index].red",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "cta[index].red",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "cta[index]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "val",
    "cta",
    "index"
   ],
   "osv_id": "ARVO-42483644",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "pixGetRGBComponentCmap"
  }
 },
 {
  "osv_id": "ARVO-42483697",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/h323.c",
    "line": 23,
    "size": null,
    "type": "ndpi_packet_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
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
    "line": 81,
    "fn": "ndpi_search_h323",
    "code": "packet->payload[0] == 0x16 && packet->payload[1] == 0x80 | packet->payload[0] == 0x16 && packet->payload[1] == 0x80 | packet->payload[0] == 0x16 && packet->payload[1] == 0x80 | packet->payload[0] == 0x16",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_h323",
    "file": "/src/ndpi/src/lib/protocols/h323.c",
    "line": 81
   },
   "code": "packet->payload[0] == 0x16 && packet->payload[1] == 0x80 | packet->payload[0] == 0x16 && packet->payload[1] == 0x80 | packet->payload[0] == 0x16 && packet->payload[1] == 0x80 | packet->payload[0] == 0x16",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_h323",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:28,IF:32,IF:38,IF:44,IF:46,IF:56,ELSE:60,ELSE:66,IF:66,IF:70,IF:79,IF:81"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/c8a176746568f145737935912421e03d342f925f/ARVO-42483697/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_c8a176746568.cpg",
   "testcase_size": 29
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
   "dedup_token": "ndpi_search_h323--check_ndpi_udp_flow_func--ndpi_detection_process_packet"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 23
    }
   ],
   "entity_decl": {
    "line": 23,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    21,
    101
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
     "code": "packet->tcp != NULL",
     "line": 28
    },
    {
     "code": "packet->payload[0] == 0x03",
     "line": 33
    },
    {
     "code": "packet->payload[1] == 0x00",
     "line": 34
    },
    {
     "code": "packet->payload_packet_len == len",
     "line": 38
    },
    {
     "code": "packet->payload[4] == (packet->payload_packet_len - sizeof(struct tpkt) - 1)",
     "line": 44
    },
    {
     "code": "packet->payload[5] == 0xE0",
     "line": 46
    },
    {
     "code": "packet->payload[5] == 0xD0",
     "line": 47
    },
    {
     "code": "packet->udp != NULL",
     "line": 66
    },
    {
     "code": "packet->payload[0] == 0x80",
     "line": 70
    },
    {
     "code": "packet->payload[1] == 0x08",
     "line": 70
    },
    {
     "code": "packet->payload[2] == 0xe7",
     "line": 71
    },
    {
     "code": "packet->payload[2] == 0x26",
     "line": 71
    },
    {
     "code": "packet->payload[4] == 0x00",
     "line": 72
    },
    {
     "code": "packet->payload[5] == 0x00",
     "line": 72
    },
    {
     "code": "sport == 1719",
     "line": 79
    },
    {
     "code": "dport == 1719",
     "line": 79
    },
    {
     "code": "packet->payload[0] == 0x16",
     "line": 81
    },
    {
     "code": "packet->payload[1] == 0x80",
     "line": 81
    },
    {
     "code": "packet->payload[4] == 0x06",
     "line": 81
    },
    {
     "code": "packet->payload[5] == 0x00",
     "line": 81
    }
   ],
   "line_call_count": 15,
   "line_calls": [
    {
     "code": "packet->payload[0] == 0x16 && packet->payload[1] == 0x80 && packet->payload[4] == 0x06 && packet->payload[5] == 0x00",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "packet->payload[0] == 0x16 && packet->payload[1] == 0x80 && packet->payload[4] == 0x06",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "packet->payload[0] == 0x16 && packet->payload[1] == 0x80",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "packet->payload[0] == 0x16",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload[1] == 0x80",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload[4] == 0x06",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[4]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload[5] == 0x00",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "packet->payload[5]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet"
   ],
   "osv_id": "ARVO-42483697",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_h323"
  }
 },
 {
  "osv_id": "ARVO-42483782",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 121,
    "size": null,
    "type": "u_int16_t"
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
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "kerberos_len+4",
   "size_expr_cpg_callee": "ndpi_malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 246,
    "fn": "ndpi_search_kerberos",
    "code": "i=0 | i<14 | i++ | packet->payload[realm_offset] != 0x1b",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_kerberos",
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 246
   },
   "code": "i=0 | i<14 | i++ | packet->payload[realm_offset] != 0x1b",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_kerberos",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i<16 | i<10 | i<4",
   "guard_count": 11,
   "control_structures": "IF:49,IF:60,IF:63,IF:67,ELSE:73,IF:85,IF:89,ELSE:94,IF:100,IF:106,IF:107,IF:108"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42483782/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "testcase_size": 237
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
   "dedup_token": "ndpi_search_kerberos--check_ndpi_udp_flow_func--ndpi_check_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "i=8",
     "line": 123
    },
    {
     "code": "i=3",
     "line": 156
    },
    {
     "code": "i=0",
     "line": 170
    },
    {
     "code": "i=0",
     "line": 179
    },
    {
     "code": "i=0",
     "line": 195
    },
    {
     "code": "i=0",
     "line": 224
    },
    {
     "code": "i=0",
     "line": 246
    },
    {
     "code": "i=0",
     "line": 264
    },
    {
     "code": "i=0",
     "line": 283
    },
    {
     "code": "i=0",
     "line": 305
    },
    {
     "code": "i=0",
     "line": 353
    }
   ],
   "entity_decl": {
    "line": 121,
    "type": "u_int16_t"
   },
   "entity_name_cpg": "i",
   "func_lines": [
    43,
    395
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
     "code": "sport != KERBEROS_PORT",
     "line": 49
    },
    {
     "code": "dport != KERBEROS_PORT",
     "line": 49
    },
    {
     "code": "flow->kerberos_buf.pktbuf != NULL",
     "line": 60
    },
    {
     "code": "flow->kerberos_buf.pktbuf_currlen == flow->kerberos_buf.pktbuf_maxlen",
     "line": 67
    },
    {
     "code": "kerberos_len < 12000",
     "line": 100
    },
    {
     "code": "kerberos_len > expected_len",
     "line": 106
    },
    {
     "code": "flow->kerberos_buf.pktbuf == NULL",
     "line": 108
    },
    {
     "code": "flow->kerberos_buf.pktbuf != NULL",
     "line": 111
    },
    {
     "code": "kerberos_len == expected_len",
     "line": 119
    },
    {
     "code": "packet->payload_packet_len > 128",
     "line": 120
    },
    {
     "code": "i<16",
     "line": 123
    },
    {
     "code": "packet->payload[base_offset+i] == 0x03",
     "line": 124
    },
    {
     "code": "packet->payload[base_offset+i+1] == 0x02",
     "line": 125
    },
    {
     "code": "packet->payload[base_offset+i+2] == 0x01",
     "line": 126
    },
    {
     "code": "packet->payload[base_offset+i+3] != 0x05",
     "line": 127
    },
    {
     "code": "packet->payload[koffset] == 0x0A",
     "line": 138
    },
    {
     "code": "packet->payload[koffset] == 0x0C",
     "line": 139
    },
    {
     "code": "packet->payload[koffset] == 0x0D",
     "line": 140
    },
    {
     "code": "packet->payload[koffset] == 0x0E",
     "line": 141
    },
    {
     "code": "msg_type != 0x0d",
     "line": 148
    },
    {
     "code": "packet->payload[koffset+1] == 0xA3",
     "line": 150
    },
    {
     "code": "packet->payload[koffset+3] == 0x30",
     "line": 151
    },
    {
     "code": "i<10",
     "line": 156
    },
    {
     "code": "packet->payload[koffset+i] == pad_len",
     "line": 156
    },
    {
     "code": "pad_len > 0",
     "line": 168
    },
    {
     "code": "i<4",
     "line": 170
    },
    {
     "code": "packet->payload[koffsetp] != 0x30",
     "line": 170
    },
    {
     "code": "i<10",
     "line": 179
    },
    {
     "code": "packet->payload[body_offset] != 0x05",
     "line": 179
    },
    {
     "code": "msg_type == 0x0A",
     "line": 185
    },
    {
     "code": "body_offset < packet->payload_packet_len",
     "line": 191
    },
    {
     "code": "i<20",
     "line": 195
    },
    {
     "code": "packet->payload[name_offset] != 0x1b",
     "line": 195
    },
    {
     "code": "name_offset < packet->payload_packet_len",
     "line": 201
    },
    {
     "code": "packet->payload[name_offset+1] < ' '",
     "line": 205
    },
    {
     "code": "packet->payload[name_offset+1] == 0x1b",
     "line": 208
    },
    {
     "code": "(cname_len+name_offset) < packet->payload_packet_len",
     "line": 213
    },
    {
     "code": "cname_len > sizeof(cname_str)-1",
     "line": 219
    },
    {
     "code": "i<cname_len",
     "line": 224
    },
    {
     "code": "strcmp(cname_str, \"host\") == 0",
     "line": 230
    },
    {
     "code": "strcmp(cname_str, \"ldap\") == 0",
     "line": 230
    },
    {
     "code": "packet->payload[name_offset+1+cname_len] == 0x1b",
     "line": 230
    },
    {
     "code": "cname_str[cname_len-1] == '$'",
     "line": 240
    },
    {
     "code": "i<14",
     "line": 246
    },
    {
     "code": "packet->payload[realm_offset] != 0x1b",
     "line": 246
    },
    {
     "code": "(realm_offset+realm_len) < packet->payload_packet_len",
     "line": 254
    },
    {
     "code": "realm_len > sizeof(realm_str)-1",
     "line": 257
    },
    {
     "code": "i<realm_len",
     "line": 264
    },
    {
     "code": "msg_type == 0x0c",
     "line": 274
    },
    {
     "code": "body_offset < packet->payload_packet_len",
     "line": 279
    },
    {
     "code": "i<14",
     "line": 283
    },
    {
     "code": "packet->payload[name_offset] != 0x1b",
     "line": 283
    },
    {
     "code": "name_offset < packet->payload_packet_len",
     "line": 289
    },
    {
     "code": "(realm_len+name_offset) < packet->payload_packet_len",
     "line": 295
    },
    {
     "code": "realm_len > sizeof(realm_str)-1",
     "line": 298
    },
    {
     "code": "i<realm_len",
     "line": 305
    },
    {
     "code": "flow->kerberos_buf.pktbuf != NULL",
     "line": 324
    },
    {
     "code": "msg_type == 0x0d",
     "line": 330
    },
    {
     "code": "cname_offset < packet->payload_packet_len",
     "line": 342
    },
    {
     "code": "(cname_offset+cname_offset) < packet->payload_packet_len",
     "line": 345
    },
    {
     "code": "cname_len > sizeof(cname_str)-1",
     "line": 348
    },
    {
     "code": "i<cname_len",
     "line": 353
    },
    {
     "code": "cname_str[cname_len-1] == '$'",
     "line": 360
    },
    {
     "code": "packet->payload_packet_len > 21",
     "line": 374
    },
    {
     "code": "packet->payload[16] == 0x05",
     "line": 375
    },
    {
     "code": "packet->payload[21] == 0x0a",
     "line": 376
    },
    {
     "code": "packet->payload[21] == 0x0c",
     "line": 377
    },
    {
     "code": "packet->payload[21] == 0x0d",
     "line": 377
    },
    {
     "code": "packet->payload[21] == 0x0e",
     "line": 377
    },
    {
     "code": "flow->protos.kerberos.domain[0] != '\\0'",
     "line": 389
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "i=0",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "i<14",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "i++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "packet->payload[realm_offset] != 0x1b",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "packet->payload[realm_offset]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "realm_offset++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "i",
    "packet",
    "realm_offset"
   ],
   "osv_id": "ARVO-42483782",
   "sites": [
    {
     "args": "kerberos_len+4",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(kerberos_len+4)",
     "line": 109
    },
    {
     "args": "48",
     "callee": "<operator>.alloc",
     "code": "cname_str[48]",
     "line": 215
    },
    {
     "args": "48",
     "callee": "<operator>.alloc",
     "code": "realm_str[48]",
     "line": 255
    },
    {
     "args": "48",
     "callee": "<operator>.alloc",
     "code": "realm_str[48]",
     "line": 296
    },
    {
     "args": "flow->kerberos_buf.pktbuf",
     "callee": "ndpi_free",
     "code": "ndpi_free(flow->kerberos_buf.pktbuf)",
     "line": 314
    },
    {
     "args": "flow->kerberos_buf.pktbuf",
     "callee": "free",
     "code": "free(flow->kerberos_buf.pktbuf)",
     "line": 325
    },
    {
     "args": "48",
     "callee": "<operator>.alloc",
     "code": "cname_str[48]",
     "line": 346
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
  "osv_id": "ARVO-42484330",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/spotify.c",
    "line": 41,
    "size": null,
    "type": "ndpi_packet_struct*"
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
    "line": 51,
    "fn": "ndpi_check_spotify",
    "code": "memcmp(packet->payload, \"SpotUdp\", 7) == 0 | memcmp(packet->payload, \"SpotUdp\", 7) | packet->payload",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_spotify",
    "file": "/src/ndpi/src/lib/protocols/spotify.c",
    "line": 51
   },
   "code": "memcmp(packet->payload, \"SpotUdp\", 7) == 0 | memcmp(packet->payload, \"SpotUdp\", 7) | packet->payload",
   "access": {
    "dir": "READ",
    "width": 7,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_spotify",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:45,IF:48,IF:50,IF:51,ELSE:58,IF:58,IF:60,IF:69,IF:99"
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/9dfd0d0071845779487b4e2e14c3599e18a74a8c/ARVO-42484330/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_9dfd0d007184.cpg",
   "testcase_size": 31
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--bcmp--ndpi_check_spotify"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 41
    }
   ],
   "entity_decl": {
    "line": 41,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    39,
    120
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
     "code": "packet->udp != NULL",
     "line": 45
    },
    {
     "code": "packet->udp->source == spotify_port",
     "line": 48
    },
    {
     "code": "packet->udp->dest == spotify_port",
     "line": 49
    },
    {
     "code": "payload_len > 2",
     "line": 50
    },
    {
     "code": "memcmp(packet->payload, \"SpotUdp\", 7) == 0",
     "line": 51
    },
    {
     "code": "packet->tcp != NULL",
     "line": 58
    },
    {
     "code": "packet->payload[0] == 0x00",
     "line": 60
    },
    {
     "code": "packet->payload[1] == 0x04",
     "line": 60
    },
    {
     "code": "packet->payload[2] == 0x00",
     "line": 61
    },
    {
     "code": "packet->payload[3] == 0x00",
     "line": 61
    },
    {
     "code": "packet->payload[6] == 0x52",
     "line": 62
    },
    {
     "code": "packet->payload[7] == 0x0e",
     "line": 62
    },
    {
     "code": "packet->payload[7] == 0x0f",
     "line": 62
    },
    {
     "code": "packet->payload[8] == 0x50",
     "line": 63
    },
    {
     "code": "src_addr_masked_22 == 0x4E1F0800",
     "line": 99
    },
    {
     "code": "dst_addr_masked_22 == 0x4E1F0800",
     "line": 100
    },
    {
     "code": "src_addr_masked_22 == 0xC1EBE800",
     "line": 102
    },
    {
     "code": "dst_addr_masked_22 == 0xC1EBE800",
     "line": 103
    },
    {
     "code": "src_addr_masked_22 == 0xC284C400",
     "line": 105
    },
    {
     "code": "dst_addr_masked_22 == 0xC284C400",
     "line": 106
    },
    {
     "code": "src_addr_masked_24 == 0xC284A200",
     "line": 108
    },
    {
     "code": "dst_addr_masked_24 == 0xC284A200",
     "line": 109
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memcmp(packet->payload, \"SpotUdp\", 7) == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "memcmp(packet->payload, \"SpotUdp\", 7)",
     "name": "memcmp",
     "nargs": 3
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet"
   ],
   "osv_id": "ARVO-42484330",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_check_spotify"
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