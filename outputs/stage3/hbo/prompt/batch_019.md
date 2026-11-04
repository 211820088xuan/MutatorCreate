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
  "osv_id": "ARVO-42502576",
  "project": "assimp",
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
   "size_bytes": 164,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 85,
    "fn": "Swap2",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Swap2",
    "file": "/src/assimp/include/assimp/ByteSwapper.h",
    "line": 85
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 164
   }
  },
  "context": {
   "fn": "Swap2",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/71a87b653cd4b5671104fe49e2e38cf5dd4d8675/ARVO-42502576/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_71a87b653cd4.cpg",
   "testcase_size": 163
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
   "loc_size": 164,
   "loc_offset": 163,
   "loc_kind": "region",
   "dedup_token": "swap<unsigned char>--Swap2--Assimp::BaseImporter::ConvertToUTF8(std::__1::vector<char, std::__1::allocator<char> >&)",
   "region_size": 164
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    -1,
    -1
   ],
   "func_params": {
    "names": [
     "p1"
    ],
    "types": [
     "ANY"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42502576",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Swap2"
  }
 },
 {
  "osv_id": "ARVO-42503233",
  "project": "mruby",
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
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 68
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "mrb_funcall_with_block",
    "file": "/src/mruby/src/vm.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_funcall_with_block",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/6b3b1012ca480f1e930c4ddeeaebed55e5df4144/ARVO-42503233/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_6b3b1012ca48.cpg",
   "testcase_size": 6
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
   "dedup_token": "mrb_funcall_with_block--mrb_funcall_argv--mrb_funcall_id"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    435,
    536
   ],
   "func_params": {
    "names": [
     "mrb",
     "self",
     "mid",
     "argc",
     "argv",
     "blk"
    ],
    "types": [
     "mrb_state*",
     "mrb_value",
     "mrb_sym",
     "mrb_int",
     "mrb_value*",
     "mrb_value"
    ]
   },
   "guards": [
    {
     "code": "nth_ci < (mrb->c->ci - mrb->c->cibase)",
     "line": 451
    },
    {
     "code": "ci - mrb->c->cibase > MRB_CALL_LEVEL_MAX",
     "line": 470
    },
    {
     "code": "argv < mrb->c->stend",
     "line": 473
    },
    {
     "code": "argc < 0",
     "line": 476
    },
    {
     "code": "argc < 15",
     "line": 514
    },
    {
     "code": "argc > 0",
     "line": 515
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42503233",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_funcall_with_block"
  }
 },
 {
  "osv_id": "ARVO-42503239",
  "project": "mruby",
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
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 68
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "mrb_funcall_with_block",
    "file": "/src/mruby/src/vm.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_funcall_with_block",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/6b3b1012ca480f1e930c4ddeeaebed55e5df4144/ARVO-42503239/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_6b3b1012ca48.cpg",
   "testcase_size": 23805
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
   "dedup_token": "mrb_funcall_with_block--mrb_instance_new--mrb_funcall_with_block"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    435,
    536
   ],
   "func_params": {
    "names": [
     "mrb",
     "self",
     "mid",
     "argc",
     "argv",
     "blk"
    ],
    "types": [
     "mrb_state*",
     "mrb_value",
     "mrb_sym",
     "mrb_int",
     "mrb_value*",
     "mrb_value"
    ]
   },
   "guards": [
    {
     "code": "nth_ci < (mrb->c->ci - mrb->c->cibase)",
     "line": 451
    },
    {
     "code": "ci - mrb->c->cibase > MRB_CALL_LEVEL_MAX",
     "line": 470
    },
    {
     "code": "argv < mrb->c->stend",
     "line": 473
    },
    {
     "code": "argc < 0",
     "line": 476
    },
    {
     "code": "argc < 15",
     "line": 514
    },
    {
     "code": "argc > 0",
     "line": 515
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42503239",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_funcall_with_block"
  }
 },
 {
  "osv_id": "ARVO-42503489",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "id",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1211,
    "size": null,
    "type": "u_int16_t*"
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
   "size_expr_cpg": "JA3_STR_LEN",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1216,
    "fn": "processClientServerHello",
    "code": "(*id == 0) || (packet->payload[cipher_offset+i] != packe | *id == 0 | *id | packet->payload[cipher_offset+i] != packet->payload[ciph",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "processClientServerHello",
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1216
   },
   "code": "(*id == 0) || (packet->payload[cipher_offset+i] != packe | *id == 0 | *id | packet->payload[cipher_offset+i] != packet->payload[ciph",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "processClientServerHello",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i<extension_len | i<ja3.num_cipher | i > 0",
   "guard_count": 19,
   "control_structures": "IF:1047,IF:1053,IF:1058,IF:1067,IF:1070,IF:1081,ELSE:1083,IF:1084,IF:1088,IF:1092,IF:1103,ELSE:1106"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow",
   "quic_version"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/1a37595de02761497845503a390e24fc1cf11a4f/ARVO-42503489/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_1a37595de027.cpg",
   "testcase_size": 122
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
   "dedup_token": "processClientServerHello--processTLSBlock--ndpi_search_tls_udp"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*id = (u_int16_t*)&packet->payload[cipher_offset+i]",
     "line": 1211
    }
   ],
   "entity_decl": {
    "line": 1211,
    "type": "u_int16_t*"
   },
   "entity_name_cpg": "id",
   "func_lines": [
    1022,
    1729
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
     "line": 1035
    },
    {
     "code": "total_len > packet->payload_packet_len",
     "line": 1047
    },
    {
     "code": "packet->payload[1] != 0x0",
     "line": 1047
    },
    {
     "code": "total_len > 4",
     "line": 1053
    },
    {
     "code": "base_offset < total_len",
     "line": 1058
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.ssl_version < 0x0302",
     "line": 1067
    },
    {
     "code": "handshake_type == 0x02",
     "line": 1070
    },
    {
     "code": "tls_version < 0x7F15",
     "line": 1084
    },
    {
     "code": "(offset+3) > packet->payload_packet_len",
     "line": 1088
    },
    {
     "code": "(flow->protos.tls_quic_stun.tls_quic.server_unsafe_cipher = ndpi_is_safe_ssl_cipher(ja3.cipher[0])) == 1",
     "line": 1092
    },
    {
     "code": "(offset + 1) < packet->payload_packet_len",
     "line": 1103
    },
    {
     "code": "i<extension_len",
     "line": 1113
    },
    {
     "code": "(offset+4) > packet->payload_packet_len",
     "line": 1116
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 1121
    },
    {
     "code": "extension_id == 43",
     "line": 1129
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 1146
    },
    {
     "code": "i > 0",
     "line": 1147
    },
    {
     "code": "rc > 0",
     "line": 1153
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1153
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 1157
    },
    {
     "code": "i > 0",
     "line": 1158
    },
    {
     "code": "i<16",
     "line": 1175
    },
    {
     "code": "handshake_type == 0x01",
     "line": 1184
    },
    {
     "code": "(session_id_len+base_offset+3) > packet->payload_packet_len",
     "line": 1188
    },
    {
     "code": "(session_id_len+base_offset+cookie_len+4) > packet->payload_packet_len",
     "line": 1199
    },
    {
     "code": "i<cipher_len",
     "line": 1210
    },
    {
     "code": "*id == 0",
     "line": 1216
    },
    {
     "code": "packet->payload[cipher_offset+i] != packet->payload[cipher_offset+i+1]",
     "line": 1216
    },
    {
     "code": "ja3.num_cipher < MAX_NUM_JA3",
     "line": 1222
    },
    {
     "code": "offset < total_len",
     "line": 1243
    },
    {
     "code": "offset < total_len",
     "line": 1258
    },
    {
     "code": "extension_offset < extensions_len",
     "line": 1272
    },
    {
     "code": "extension_id == 0",
     "line": 1285
    },
    {
     "code": "packet->payload[extn_off] != packet->payload[extn_off+1]",
     "line": 1285
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 1288
    },
    {
     "code": "extension_id == 0",
     "line": 1298
    },
    {
     "code": "extension_id == 10",
     "line": 1356
    },
    {
     "code": "i<extension_len-2",
     "line": 1364
    },
    {
     "code": "s_group == 0",
     "line": 1370
    },
    {
     "code": "packet->payload[s_offset+i] != packet->payload[s_offset+i+1]",
     "line": 1370
    },
    {
     "code": "ja3.num_elliptic_curve < MAX_NUM_JA3",
     "line": 1372
    },
    {
     "code": "extension_id == 11",
     "line": 1390
    },
    {
     "code": "i<extension_len-1",
     "line": 1397
    },
    {
     "code": "ja3.num_elliptic_curve_point_format < MAX_NUM_JA3",
     "line": 1404
    },
    {
     "code": "extension_id == 16",
     "line": 1419
    },
    {
     "code": "s_offset < tot_alpn_len",
     "line": 1431
    },
    {
     "code": "s_offset < total_len",
     "line": 1431
    },
    {
     "code": "(alpn_str_len+alpn_len+1) < (sizeof(alpn_str)-1)",
     "line": 1439
    },
    {
     "code": "alpn_str_len > 0",
     "line": 1440
    },
    {
     "code": "alpn_i<alpn_len",
     "line": 1445
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.alpn == NULL",
     "line": 1460
    },
    {
     "code": "extension_id == 43",
     "line": 1462
    },
    {
     "code": "version_len == (extension_len-1)",
     "line": 1472
    },
    {
     "code": "j+1<version_len",
     "line": 1478
    },
    {
     "code": "(version_str_len+8) < sizeof(version_str)",
     "line": 1487
    },
    {
     "code": "version_str_len > 0",
     "line": 1490
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.tls_supported_versions == NULL",
     "line": 1498
    },
    {
     "code": "extension_id == 65486",
     "line": 1501
    },
    {
     "code": "(e_offset+4) < packet->payload_packet_len",
     "line": 1518
    },
    {
     "code": "(e_offset+4) < packet->payload_packet_len",
     "line": 1522
    },
    {
     "code": "e_offset+e_sni_len < packet->payload_packet_len",
     "line": 1527
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.encrypted_sni.esni == NULL",
     "line": 1532
    },
    {
     "code": "i<(e_offset+e_sni_len)",
     "line": 1538
    },
    {
     "code": "extension_id == 65445",
     "line": 1552
    },
    {
     "code": "extension_id == 57",
     "line": 1553
    },
    {
     "code": "s_offset < final_offset",
     "line": 1570
    },
    {
     "code": "s_offset+param_len > final_offset",
     "line": 1594
    },
    {
     "code": "param_type==0x3129",
     "line": 1597
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 1622
    },
    {
     "code": "i > 0",
     "line": 1624
    },
    {
     "code": "rc > 0",
     "line": 1625
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1625
    },
    {
     "code": "rc > 0",
     "line": 1629
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1629
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 1633
    },
    {
     "code": "i > 0",
     "line": 1635
    },
    {
     "code": "rc > 0",
     "line": 1636
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1636
    },
    {
     "code": "rc > 0",
     "line": 1640
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1640
    },
    {
     "code": "i<ja3.num_elliptic_curve",
     "line": 1644
    },
    {
     "code": "i > 0",
     "line": 1646
    },
    {
     "code": "rc > 0",
     "line": 1647
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1647
    },
    {
     "code": "rc > 0",
     "line": 1651
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1651
    },
    {
     "code": "i<ja3.num_elliptic_curve_point_format",
     "line": 1653
    },
    {
     "code": "i > 0",
     "line": 1655
    },
    {
     "code": "rc > 0",
     "line": 1656
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1656
    },
    {
     "code": "i<16",
     "line": 1667
    },
    {
     "code": "rc > 0",
     "line": 1671
    },
    {
     "code": "ndpi_struct->malicious_ja3_automa.ac_automa != NULL",
     "line": 1678
    },
    {
     "code": "rc1 > 0",
     "line": 1682
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.alpn == NULL",
     "line": 1689
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.client_requested_server_name[0] != '\\0'",
     "line": 1696
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.client_requested_server_name[0] == 0",
     "line": 1701
    },
    {
     "code": "flow->protos.tls_quic_stun.tls_quic.encrypted_sni.esni == NULL",
     "line": 1703
    },
    {
     "code": "offset == total_len",
     "line": 1716
    }
   ],
   "line_call_count": 11,
   "line_calls": [
    {
     "code": "(*id == 0) ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "*id == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*id",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "packet->payload[cipher_offset+i] != packet->payload[cipher_offset+i+1]",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "packet->payload[cipher_offset+i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "cipher_offset+i",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "packet->payload[cipher_offset+i+1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "cipher_offset+i+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "cipher_offset+i",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "id",
    "packet",
    "cipher_offset",
    "i"
   ],
   "osv_id": "ARVO-42503489",
   "sites": [
    {
     "args": "JA3_STR_LEN",
     "callee": "<operator>.alloc",
     "code": "ja3_str[JA3_STR_LEN]",
     "line": 1028
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "md5_hash[16]",
     "line": 1030
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "buffer[64] = { '\\0' }",
     "line": 1034
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "alpn_str[256]",
     "line": 1422
    },
    {
     "args": "alpn_str",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(alpn_str)",
     "line": 1461
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "version_str[256]",
     "line": 1465
    },
    {
     "args": "version_str",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(version_str)",
     "line": 1499
    },
    {
     "args": "e_sni_len*2+1",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(e_sni_len*2+1)",
     "line": 1533
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
  "osv_id": "ARVO-42503750",
  "project": "libjxl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "info",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libjxl/lib/jxl/box_content_decoder.cc",
    "line": 38,
    "size": null,
    "type": "JxlBasicInfo"
   }
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
   "cross_function": true,
   "size_expr_cpg": "data ;; remaining + chunk_size",
   "size_expr_cpg_callee": "realloc"
  },
  "sites": [
   {
    "code": "realloc(data, remaining + chunk_size)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "realloc",
    "line": 61,
    "origin": "cpg",
    "args": "data ;; remaining + chunk_size"
   },
   {
    "kind": "unknown",
    "line": 87,
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "code": "info.exponent_bits_per_sample",
    "origin": "report:crash"
   },
   {
    "code": "malloc(extra.name_length + 1)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "malloc",
    "line": 148,
    "origin": "cpg",
    "args": "extra.name_length + 1"
   },
   {
    "code": "malloc(profile_size)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "malloc",
    "line": 242,
    "origin": "cpg",
    "args": "profile_size"
   },
   {
    "code": "malloc(frame_header.name_length + 1)",
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "kind": "malloc",
    "line": 263,
    "origin": "cpg",
    "args": "frame_header.name_length + 1"
   }
  ],
  "crash": {
   "site": {
    "fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)",
    "file": "/src/libjxl/lib/jxl/box_content_decoder.cc",
    "line": 87
   },
   "code": "info.exponent_bits_per_sample",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "PrintBasicInfo",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:23,IF:30,FOR:42,IF:48,BREAK:50,ELSE:51,IF:51,IF:56,IF:64,BREAK:66,ELSE:70,IF:70"
  },
  "call_chain": [],
  "types": {
   "entity_type": "JxlBasicInfo",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "file"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/f0b9147ee57805c4ab45abdf8d72e2da9c5a951c/ARVO-42503750/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_f0b9147ee578.cpg",
   "testcase_size": 105
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
   "dedup_token": "__asan_memcpy--jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)--JxlDecoderProcessInput"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 38,
    "type": "JxlBasicInfo"
   },
   "entity_name_cpg": "info",
   "func_lines": [
    16,
    301
   ],
   "func_params": {
    "names": [
     "file"
    ],
    "types": [
     "FILE*"
    ]
   },
   "guards": [
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderSubscribeEvents(",
     "line": 30
    },
    {
     "code": "status == JXL_DEC_ERROR",
     "line": 48
    },
    {
     "code": "status == JXL_DEC_NEED_MORE_INPUT",
     "line": 51
    },
    {
     "code": "remaining != 0",
     "line": 56
    },
    {
     "code": "read_size == 0",
     "line": 64
    },
    {
     "code": "status == JXL_DEC_SUCCESS",
     "line": 70
    },
    {
     "code": "status == JXL_DEC_BASIC_INFO",
     "line": 73
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderGetBasicInfo(dec, &info)",
     "line": 74
    },
    {
     "code": "info.intensity_target != 255.f",
     "line": 88
    },
    {
     "code": "info.min_nits != 0.f",
     "line": 88
    },
    {
     "code": "info.relative_to_max_display != 0",
     "line": 89
    },
    {
     "code": "info.relative_to_max_display != 0.f",
     "line": 90
    },
    {
     "code": "info.orientation > 0",
     "line": 113
    },
    {
     "code": "info.orientation < 9",
     "line": 113
    },
    {
     "code": "i < info.num_extra_channels",
     "line": 126
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderGetExtraChannelInfo(dec, i, &extra)",
     "line": 128
    },
    {
     "code": "extra.type < 7",
     "line": 134
    },
    {
     "code": "extra.type == JXL_CHANNEL_OPTIONAL",
     "line": 135
    },
    {
     "code": "extra.exponent_bits_per_sample > 0",
     "line": 139
    },
    {
     "code": "extra.dim_shift > 0",
     "line": 143
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderGetExtraChannelName(",
     "line": 149
    },
    {
     "code": "extra.type == JXL_CHANNEL_ALPHA",
     "line": 158
    },
    {
     "code": "extra.type == JXL_CHANNEL_SPOT_COLOR",
     "line": 162
    },
    {
     "code": "extra.type == JXL_CHANNEL_CFA",
     "line": 167
    },
    {
     "code": "status == JXL_DEC_COLOR_ENCODING",
     "line": 170
    },
    {
     "code": "JXL_DEC_SUCCESS ==",
     "line": 175
    },
    {
     "code": "color_encoding.white_point == JXL_WHITE_POINT_CUSTOM",
     "line": 195
    },
    {
     "code": "color_encoding.color_space == JXL_COLOR_SPACE_RGB",
     "line": 199
    },
    {
     "code": "color_encoding.color_space == JXL_COLOR_SPACE_UNKNOWN",
     "line": 200
    },
    {
     "code": "color_encoding.primaries == JXL_PRIMARIES_CUSTOM",
     "line": 203
    },
    {
     "code": "color_encoding.transfer_function == JXL_TRANSFER_FUNCTION_GAMMA",
     "line": 215
    },
    {
     "code": "JXL_DEC_SUCCESS !=",
     "line": 230
    },
    {
     "code": "profile_size < 132",
     "line": 238
    },
    {
     "code": "JXL_DEC_SUCCESS !=",
     "line": 243
    },
    {
     "code": "status == JXL_DEC_FRAME",
     "line": 256
    },
    {
     "code": "JXL_DEC_SUCCESS != JxlDecoderGetFrameHeader(dec, &frame_header)",
     "line": 257
    },
    {
     "code": "JXL_DEC_SUCCESS !=",
     "line": 264
    },
    {
     "code": "status == JXL_DEC_BOX",
     "line": 284
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "info.exponent_bits_per_sample",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "info"
   ],
   "osv_id": "ARVO-42503750",
   "sites": [
    {
     "args": "data ;; remaining + chunk_size",
     "callee": "realloc",
     "code": "realloc(data, remaining + chunk_size)",
     "line": 61
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "* const orientation_string[8] = {",
     "line": 108
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "* const ec_type_names[7] = {\"Alpha\",       \"Depth\",",
     "line": 122
    },
    {
     "args": "extra.name_length + 1",
     "callee": "malloc",
     "code": "malloc(extra.name_length + 1)",
     "line": 148
    },
    {
     "args": "name",
     "callee": "free",
     "code": "free(name)",
     "line": 152
    },
    {
     "args": "name",
     "callee": "free",
     "code": "free(name)",
     "line": 155
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "* const cs_string[4] = {\"RGB color\", \"Grayscale\", \"XYB\",",
     "line": 180
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "* const wp_string[12] = {\"\", \"D65\", \"Custom\", \"\", \"\",  \"\",",
     "line": 182
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "* const pr_string[12] = {",
     "line": 184
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "* const tf_string[19] = {",
     "line": 186
    },
    {
     "args": null,
     "callee": "<operator>.alloc",
     "code": "* const ri_string[4] = {\"Perceptual\", \"Relative\",",
     "line": 189
    },
    {
     "args": "profile_size",
     "callee": "malloc",
     "code": "malloc(profile_size)",
     "line": 242
    },
    {
     "args": "profile",
     "callee": "free",
     "code": "free(profile)",
     "line": 248
    },
    {
     "args": "profile",
     "callee": "free",
     "code": "free(profile)",
     "line": 254
    },
    {
     "args": "frame_header.name_length + 1",
     "callee": "malloc",
     "code": "malloc(frame_header.name_length + 1)",
     "line": 263
    },
    {
     "args": "name",
     "callee": "free",
     "code": "free(name)",
     "line": 267
    },
    {
     "args": "name",
     "callee": "free",
     "code": "free(name)",
     "line": 270
    },
    {
     "args": "data",
     "callee": "free",
     "code": "free(data)",
     "line": 298
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "jxl::JxlBoxContentDecoder::Process(unsigned char const*, unsigned long, unsigned long, unsigned char**, unsigned long*)"
  }
 },
 {
  "osv_id": "ARVO-42503787",
  "project": "net-snmp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "data",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/net-snmp/snmplib/asn1.c",
    "line": 1006,
    "size": null,
    "type": "u_char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "agentx_parse",
    "file": "/src/net-snmp/agent/mibgroup/agentx/protocol.c",
    "line": 1646
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "1 + strlength",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1026,
    "fn": "asn_build_string",
    "code": "memmove(data, str, strlength)",
    "origin": "report:crash"
   },
   {
    "code": "malloc(1 + strlength)",
    "fn": "asn_build_string",
    "kind": "malloc",
    "line": 1032,
    "origin": "cpg",
    "args": "1 + strlength"
   }
  ],
  "crash": {
   "site": {
    "fn": "asn_build_string",
    "file": "/src/net-snmp/snmplib/asn1.c",
    "line": 1026
   },
   "code": "memmove(data, str, strlength)",
   "access": {
    "dir": "READ",
    "width": 32,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "asn_build_string",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "str == NULL",
   "guard_count": 1,
   "control_structures": "IF:1018,IF:1022,IF:1023,ELSE:1025,IF:1035,ELSE:1039,IF:1040,ELSE:1042,IF:1047"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "data",
   "str",
   "strlength"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/8babb2d078f83a4956c7cf70a013c80f78e6f71d/ARVO-42503787/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_8babb2d078f8.cpg",
   "testcase_size": 529
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
   "dedup_token": "__asan_memmove--asn_build_string--snmpv3_scopedPDU_header_build"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "data = asn_build_header(data, datalength, type, strlength)",
     "line": 1017
    }
   ],
   "entity_decl": {
    "line": 1006,
    "type": "u_char*"
   },
   "entity_name_cpg": "data",
   "func_lines": [
    1005,
    1052
   ],
   "func_params": {
    "names": [
     "data",
     "datalength",
     "type",
     "str",
     "strlength"
    ],
    "types": [
     "u_char*",
     "size_t*",
     "u_char",
     "u_char*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "str == NULL",
     "line": 1023
    },
    {
     "code": "buf != NULL",
     "line": 1033
    },
    {
     "code": "buf == NULL",
     "line": 1040
    },
    {
     "code": "buf != NULL",
     "line": 1047
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memmove(data, str, strlength)",
     "name": "memmove",
     "nargs": 3
    }
   ],
   "line_ids": [
    "data",
    "str",
    "strlength"
   ],
   "osv_id": "ARVO-42503787",
   "sites": [
    {
     "args": "1 + strlength",
     "callee": "malloc",
     "code": "malloc(1 + strlength)",
     "line": 1032
    },
    {
     "args": null,
     "callee": "sprint_realloc_asciistring",
     "code": "sprint_realloc_asciistring(&buf, &l, &ol, 1,",
     "line": 1035
    },
    {
     "args": "buf",
     "callee": "free",
     "code": "free(buf)",
     "line": 1048
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "asn_build_string"
  }
 },
 {
  "osv_id": "ARVO-42503790",
  "project": "net-snmp",
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
    "fn": "agentx_parse",
    "file": "/src/net-snmp/agent/mibgroup/agentx/protocol.c",
    "line": 1646
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3094,
    "fn": "asn_realloc_rbuild_string",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "asn_realloc_rbuild_string",
    "file": "/src/net-snmp/snmplib/asn1.c",
    "line": 3094
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1824,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "asn_realloc_rbuild_string",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/8babb2d078f83a4956c7cf70a013c80f78e6f71d/ARVO-42503790/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_8babb2d078f8.cpg",
   "testcase_size": 2068
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
   "dedup_token": "__asan_memcpy--asn_realloc_rbuild_string--snmpv3_scopedPDU_header_realloc_rbuild"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    -1,
    -1
   ],
   "func_params": {
    "names": [
     "p1",
     "p2",
     "p3",
     "p4",
     "p5",
     "p6",
     "p7"
    ],
    "types": [
     "ANY",
     "ANY",
     "ANY",
     "ANY",
     "ANY",
     "ANY",
     "ANY"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42503790",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "asn_realloc_rbuild_string"
  }
 },
 {
  "osv_id": "ARVO-42503809",
  "project": "libjxl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "next_out",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libjxl/third_party/brotli/c/dec/decode.c",
    "line": 1265,
    "size": null,
    "type": "uint8_t**"
   }
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
    "line": 1281,
    "fn": "WriteRingBuffer",
    "code": "memcpy(*next_out, start, num_written) | *next_out",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WriteRingBuffer",
    "file": "/src/libjxl/third_party/brotli/c/dec/decode.c",
    "line": 1281
   },
   "code": "memcpy(*next_out, start, num_written) | *next_out",
   "access": {
    "dir": "WRITE",
    "width": 135,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "WriteRingBuffer",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "num_written > to_write | num_written < to_write",
   "guard_count": 2,
   "control_structures": "IF:1271,IF:1274,IF:1277,ELSE:1279,IF:1280,IF:1289,IF:1292,IF:1293,ELSE:1295,IF:1300"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "s",
   "next_out"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/f0b9147ee57805c4ab45abdf8d72e2da9c5a951c/ARVO-42503809/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_f0b9147ee578.cpg",
   "testcase_size": 88
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
   "dedup_token": "__asan_memcpy--WriteRingBuffer--BrotliDecoderDecompressStream"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1265,
    "type": "uint8_t**"
   },
   "entity_name_cpg": "next_out",
   "func_lines": [
    1264,
    1307
   ],
   "func_params": {
    "names": [
     "s",
     "available_out",
     "next_out",
     "total_out",
     "force"
    ],
    "types": [
     "BrotliDecoderStateInternal*",
     "size_t*",
     "uint8_t**",
     "size_t*",
     "BROTLI_BOOL"
    ]
   },
   "guards": [
    {
     "code": "num_written > to_write",
     "line": 1271
    },
    {
     "code": "s->meta_block_remaining_len < 0",
     "line": 1274
    },
    {
     "code": "num_written < to_write",
     "line": 1292
    },
    {
     "code": "s->ringbuffer_size == (1 << s->window_bits)",
     "line": 1293
    },
    {
     "code": "s->ringbuffer_size == (1 << s->window_bits)",
     "line": 1300
    },
    {
     "code": "(size_t)s->pos != 0",
     "line": 1304
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(*next_out, start, num_written)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "*next_out",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "next_out",
    "start",
    "num_written"
   ],
   "osv_id": "ARVO-42503809",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WriteRingBuffer"
  }
 },
 {
  "osv_id": "ARVO-42503905",
  "project": "assimp",
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
    "fn": "_m3d_safestr",
    "file": "/src/assimp/code/AssetLib/M3D/m3d.h",
    "line": 2119
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2136,
    "fn": "_m3d_safestr",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_m3d_safestr",
    "file": "/src/assimp/code/AssetLib/M3D/m3d.h",
    "line": 2136
   },
   "code": "",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_m3d_safestr",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/0849f4e57395900ebd29531d679964e65e3904f6/ARVO-42503905/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_0849f4e57395.cpg",
   "testcase_size": 338
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
   "dedup_token": "_m3d_safestr--m3d_load--Assimp::M3DWrapper::M3DWrapper(Assimp::IOSystem*, std::__1::vector<unsigned char, std::__1::allocator<unsigned char> > const&)"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    545,
    545
   ],
   "func_params": {
    "names": [
     "in",
     "morelines"
    ],
    "types": [
     "char*",
     "int"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42503905",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_m3d_safestr"
  }
 },
 {
  "osv_id": "ARVO-42504256",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_dec",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "line": 1441,
    "size": null,
    "type": "dec_struct_t*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "line": 63
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1711,
    "fn": "ih264d_mark_err_slice_skip",
    "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_mark_err_slice_skip",
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "line": 1711
   },
   "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_mark_err_slice_skip",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1473,IF:1479,IF:1484,IF:1497,IF:1500,FOR:1505,IF:1507,IF:1509,BREAK:1512,IF:1518,IF:1524,IF:1534"
  },
  "call_chain": [],
  "types": {
   "entity_type": "dec_struct_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ps_dec"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42504256/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "testcase_size": 4489
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
   "dedup_token": "ih264d_mark_err_slice_skip--ih264d_video_decode--ih264d_api_function"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ps_dec->ps_dpb_cmds->u1_long_term_reference_flag = 0",
     "line": 1483
    },
    {
     "code": "ps_dec->ps_cur_slice->u2_frame_num = u2_frame_num",
     "line": 1487
    },
    {
     "code": "ps_dec->ps_cur_slice->u2_first_mb_in_slice = 0",
     "line": 1491
    },
    {
     "code": "ps_dec->pf_mvpred = ih264d_mvpred_nonmbaff",
     "line": 1493
    },
    {
     "code": "ps_dec->p_form_mb_part_info = ih264d_form_mb_part_info_bp",
     "line": 1494
    },
    {
     "code": "ps_dec->p_motion_compensate = ih264d_motion_compensate_bp",
     "line": 1495
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_slice_type = P_SLICE",
     "line": 1527
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_nal_ref_idc = 1",
     "line": 1528
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_nal_unit_type = 1",
     "line": 1529
    },
    {
     "code": "ps_dec->ps_ref_pic_buf_lx[0][0]->u1_pic_buf_id = 0",
     "line": 1540
    },
    {
     "code": "ps_dec->u4_output_present = 0",
     "line": 1542
    },
    {
     "code": "ps_dec->u4_fmt_conv_cur_row = ps_dec->s_disp_frame_info.u4_y_ht",
     "line": 1553
    },
    {
     "code": "ps_dec->u4_output_present = 1",
     "line": 1556
    },
    {
     "code": "ps_dec->u4_dec_thread_created = 1",
     "line": 1567
    },
    {
     "code": "ps_dec->u4_start_recon_deblk = 0",
     "line": 1574
    },
    {
     "code": "ps_dec->u4_bs_deblk_thread_created = 1",
     "line": 1578
    },
    {
     "code": "ps_dec->u4_num_mbs_cur_nmb = ps_dec->u4_num_mbs_cur_nmb - 1",
     "line": 1597
    },
    {
     "code": "ps_dec->u2_mby = ps_cur_mb_info->u2_mby",
     "line": 1619
    },
    {
     "code": "ps_dec->u2_mbx = ps_cur_mb_info->u2_mbx",
     "line": 1620
    },
    {
     "code": "ps_dec->u1_mb_ngbr_availablity =",
     "line": 1622
    },
    {
     "code": "ps_dec->pv_parse_tu_coeff_data = ps_dec->pv_prev_mb_parse_tu_coeff_data",
     "line": 1628
    },
    {
     "code": "ps_dec->ps_part = ps_dec->ps_parse_part_params",
     "line": 1637
    },
    {
     "code": "ps_dec->u1_mb_idx = 0",
     "line": 1659
    },
    {
     "code": "ps_dec->u4_num_mbs_cur_nmb = 0",
     "line": 1660
    },
    {
     "code": "ps_dec->u1_pic_decode_done = 1",
     "line": 1666
    },
    {
     "code": "ps_dec->i2_prev_slice_mbx = ps_dec->u2_mbx",
     "line": 1674
    },
    {
     "code": "ps_dec->i2_prev_slice_mby = ps_dec->u2_mby",
     "line": 1675
    },
    {
     "code": "ps_dec->ps_parse_cur_slice = ps_dec->ps_dec_slice_buf",
     "line": 1684
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (volatile void **)pu1_buf",
     "line": 1711
    },
    {
     "code": "ps_dec->ps_cur_slice->u2_first_mb_in_slice = ps_dec->u2_total_mbs_coded >> u1_mbaff",
     "line": 1714
    },
    {
     "code": "ps_dec->ps_cur_slice->i1_slice_alpha_c0_offset = 0",
     "line": 1715
    },
    {
     "code": "ps_dec->ps_cur_slice->i1_slice_beta_offset = 0",
     "line": 1716
    },
    {
     "code": "ps_dec->u2_prv_frame_num = ps_dec->ps_cur_slice->u2_frame_num",
     "line": 1719
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->u4_first_mb_in_slice = ps_dec->u2_total_mbs_coded >> u1_mbaff",
     "line": 1721
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->u2_log2Y_crwd =    ps_dec->ps_cur_slice->u2_log2Y_crwd",
     "line": 1722
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->pv_tu_coeff_data_start = ps_dec->pv_parse_tu_coeff_data",
     "line": 1727
    },
    {
     "code": "ps_dec->pv_proc_tu_coeff_data = ps_dec->pv_parse_tu_coeff_data",
     "line": 1731
    },
    {
     "code": "ps_dec->ps_cur_slice->u1_slice_type = P_SLICE",
     "line": 1740
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->slice_type = P_SLICE",
     "line": 1741
    },
    {
     "code": "ps_dec->pf_mvpred_ref_tfr_nby2mb = ih264d_mv_pred_ref_tfr_nby2_pmb",
     "line": 1742
    },
    {
     "code": "ps_dec->ps_part = ps_dec->ps_parse_part_params",
     "line": 1743
    },
    {
     "code": "ps_dec->u2_mbx =",
     "line": 1744
    },
    {
     "code": "ps_dec->u2_mby =",
     "line": 1746
    },
    {
     "code": "ps_dec->u1_slice_header_done = 2",
     "line": 1753
    },
    {
     "code": "ps_dec->u1_qp = ps_slice->u1_slice_qp",
     "line": 1754
    },
    {
     "code": "ps_dec->u4_num_mbs_cur_nmb = u1_num_mbs",
     "line": 1775
    },
    {
     "code": "ps_dec->u4_num_pmbair = (u1_num_mbs >> u1_mbaff)",
     "line": 1778
    },
    {
     "code": "ps_dec->i1_prev_mb_qp_delta = 0",
     "line": 1805
    },
    {
     "code": "ps_dec->u1_sub_mb_num = 0",
     "line": 1806
    },
    {
     "code": "ps_dec->ps_part = ps_dec->ps_parse_part_params",
     "line": 1860
    },
    {
     "code": "ps_dec->u1_mb_idx = u1_num_mbs",
     "line": 1877
    },
    {
     "code": "ps_dec->u4_num_mbs_cur_nmb = 0",
     "line": 1881
    },
    {
     "code": "ps_dec->ps_cur_slice->u4_mbs_in_slice = i2_cur_mb_addr",
     "line": 1882
    },
    {
     "code": "ps_dec->i2_prev_slice_mbx = ps_dec->u2_mbx",
     "line": 1895
    },
    {
     "code": "ps_dec->i2_prev_slice_mby = ps_dec->u2_mby",
     "line": 1896
    },
    {
     "code": "ps_dec->u1_pic_decode_done = 1",
     "line": 1901
    }
   ],
   "entity_decl": {
    "line": 1441,
    "type": "dec_struct_t*"
   },
   "entity_name_cpg": "ps_dec",
   "func_lines": [
    1441,
    1906
   ],
   "func_params": {
    "names": [
     "ps_dec",
     "num_mb_skip",
     "u1_is_idr_slice",
     "u2_frame_num",
     "ps_cur_poc",
     "prev_slice_err"
    ],
    "types": [
     "dec_struct_t*",
     "WORD32",
     "UWORD8",
     "UWORD16",
     "pocstruct_t*",
     "WORD32"
    ]
   },
   "guards": [
    {
     "code": "prev_slice_err == 1",
     "line": 1484
    },
    {
     "code": "ps_dec->ps_cur_pic != NULL",
     "line": 1497
    },
    {
     "code": "i < MAX_NUM_PIC_PARAMS",
     "line": 1505
    },
    {
     "code": "ps_dec->ps_pps[i].u1_is_valid == TRUE",
     "line": 1507
    },
    {
     "code": "ps_dec->ps_pps[i].ps_sps->u1_is_valid == TRUE",
     "line": 1509
    },
    {
     "code": "j == -1",
     "line": 1518
    },
    {
     "code": "ps_dec->u4_pic_buf_got == 0",
     "line": 1524
    },
    {
     "code": "ret != OK",
     "line": 1534
    },
    {
     "code": "0 != ps_dec->s_disp_op.u4_error_code",
     "line": 1551
    },
    {
     "code": "ps_dec->u1_separate_parse == 1",
     "line": 1559
    },
    {
     "code": "ps_dec->u4_dec_thread_created == 0",
     "line": 1561
    },
    {
     "code": "ps_dec->u4_num_cores == 3",
     "line": 1570
    },
    {
     "code": "ps_dec->u4_app_disable_deblk_frm == 0",
     "line": 1571
    },
    {
     "code": "ps_dec->u4_bs_deblk_thread_created == 0",
     "line": 1572
    },
    {
     "code": "ps_parse_cur_slice == ps_dec->ps_parse_cur_slice",
     "line": 1591
    },
    {
     "code": "ps_dec->u1_pr_sl_type == P_SLICE",
     "line": 1633
    },
    {
     "code": "ps_dec->u1_pr_sl_type == B_SLICE",
     "line": 1634
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->u4_first_mb_in_slice <",
     "line": 1671
    },
    {
     "code": "0 == ps_dec->i4_display_delay",
     "line": 1699
    },
    {
     "code": "i2_cur_mb_addr > ps_dec->ps_cur_sps->u2_max_mb_addr",
     "line": 1771
    },
    {
     "code": "ps_dec->u4_app_disable_deblk_frm == 0",
     "line": 1797
    },
    {
     "code": "u1_num_mbs == ps_dec->u1_recon_mb_grp",
     "line": 1849
    },
    {
     "code": "ps_dec->u4_first_slice_in_pic != 0",
     "line": 1889
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (volatile void **)pu1_buf",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ps_dec->ps_parse_cur_slice",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(volatile void **)pu1_buf",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ps_dec",
    "pu1_buf"
   ],
   "osv_id": "ARVO-42504256",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_mark_err_slice_skip"
  }
 },
 {
  "osv_id": "ARVO-42504546",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "size",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/internal-complibs/zlib-ng-2.0.2/inflate.c",
    "line": 317,
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
   "cross_function": true,
   "size_expr_cpg": "32",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 408,
    "fn": "inflate",
    "code": "size = 16 * KB | 16 * KB | KB",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "inflate",
    "file": "/src/c-blosc2/internal-complibs/zlib-ng-2.0.2/inflate.c",
    "line": 408
   },
   "code": "size = 16 * KB | 16 * KB | KB",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "main",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "size_ <= size | size_ <= size",
   "guard_count": 2,
   "control_structures": "IF:338,IF:345,IF:356,IF:358,IF:367,ELSE:370,IF:372,ELSE:375,IF:375,ELSE:379,IF:379,ELSE:382"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/c4c8c7cb7f22323cda796575f699ad4c953b6661/ARVO-42504546/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_c4c8c7cb7f22.cpg",
   "testcase_size": 246
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
   "dedup_token": "inflate--uncompress2--uncompress"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "size = 4 * MB",
     "line": 317
    },
    {
     "code": "size = 8 * MB",
     "line": 387
    },
    {
     "code": "size = 16 * MB",
     "line": 397
    },
    {
     "code": "size = 16 * KB",
     "line": 408
    },
    {
     "code": "size = (int)strtol(argv[5], NULL, 10)",
     "line": 425
    }
   ],
   "entity_decl": {
    "line": 317,
    "type": "int"
   },
   "entity_name_cpg": "size",
   "func_lines": [
    307,
    526
   ],
   "func_params": {
    "names": [
     "argc",
     "argv"
    ],
    "types": [
     "int",
     "char[]*"
    ]
   },
   "guards": [
    {
     "code": "argc < 2",
     "line": 338
    },
    {
     "code": "strcmp(compressor, \"blosclz\") != 0",
     "line": 345
    },
    {
     "code": "strcmp(compressor, \"lz4\") != 0",
     "line": 346
    },
    {
     "code": "strcmp(compressor, \"lz4hc\") != 0",
     "line": 347
    },
    {
     "code": "strcmp(compressor, \"snappy\") != 0",
     "line": 348
    },
    {
     "code": "strcmp(compressor, \"zlib\") != 0",
     "line": 349
    },
    {
     "code": "strcmp(compressor, \"zstd\") != 0",
     "line": 350
    },
    {
     "code": "strcmp(shuffle, \"shuffle\") != 0",
     "line": 358
    },
    {
     "code": "strcmp(shuffle, \"bitshuffle\") != 0",
     "line": 359
    },
    {
     "code": "strcmp(shuffle, \"noshuffle\") != 0",
     "line": 360
    },
    {
     "code": "argc < 4",
     "line": 367
    },
    {
     "code": "strcmp(bsuite, \"single\") == 0",
     "line": 372
    },
    {
     "code": "strcmp(bsuite, \"test\") == 0",
     "line": 375
    },
    {
     "code": "strcmp(bsuite, \"suite\") == 0",
     "line": 379
    },
    {
     "code": "strcmp(bsuite, \"hardsuite\") == 0",
     "line": 382
    },
    {
     "code": "strcmp(bsuite, \"extremesuite\") == 0",
     "line": 391
    },
    {
     "code": "strcmp(bsuite, \"debugsuite\") == 0",
     "line": 401
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "size = 16 * KB",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "16 * KB",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "KB",
     "name": "KB",
     "nargs": 0
    }
   ],
   "line_ids": [
    "size"
   ],
   "osv_id": "ARVO-42504546",
   "sites": [
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "compressor[32]",
     "line": 308
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "shuffle[32] = \"shuffle\"",
     "line": 309
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "bsuite[32]",
     "line": 310
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "usage[256]",
     "line": 329
    },
    {
     "args": "",
     "callee": "blosc_free_resources",
     "code": "blosc_free_resources()",
     "line": 523
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "inflate"
  }
 },
 {
  "osv_id": "ARVO-42505099",
  "project": "curl",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 133,
    "type": "unsigned char",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "curl_domalloc",
    "file": "/src/curl/lib/memdebug.c",
    "line": 175
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 135,
    "fn": "setcharset",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "setcharset",
    "file": "/src/curl/lib/curl_fnmatch.c",
    "line": 135
   },
   "code": "c = **p",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "setcharset",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/curl/address/e240a546a7ac2fa7956adb664b8c40c4dee4f82b/ARVO-42505099/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_e240a546a7ac.cpg",
   "testcase_size": 769
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "setcharset--loop--loop"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = **p",
     "line": 135
    },
    {
     "code": "c = *(++(*p))",
     "line": 188
    },
    {
     "code": "c = *(++(*p))",
     "line": 223
    },
    {
     "code": "c = *(++(*p))",
     "line": 239
    },
    {
     "code": "c = *(++(*p))",
     "line": 247
    }
   ],
   "entity_decl": {
    "line": 133,
    "type": "unsigned char"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    127,
    310
   ],
   "func_params": {
    "names": [
     "p",
     "charset"
    ],
    "types": [
     "unsigned char**",
     "unsigned char*"
    ]
   },
   "guards": [
    {
     "code": "c == ']'",
     "line": 145
    },
    {
     "code": "c == '['",
     "line": 153
    },
    {
     "code": "c2 == ':'",
     "line": 155
    },
    {
     "code": "c == '?'",
     "line": 169
    },
    {
     "code": "c == '*'",
     "line": 169
    },
    {
     "code": "c == '^'",
     "line": 174
    },
    {
     "code": "c == '!'",
     "line": 174
    },
    {
     "code": "c == '\\\\'",
     "line": 187
    },
    {
     "code": "c == '\\0'",
     "line": 199
    },
    {
     "code": "c == '-'",
     "line": 209
    },
    {
     "code": "c == '['",
     "line": 215
    },
    {
     "code": "c == '\\\\'",
     "line": 222
    },
    {
     "code": "c == ']'",
     "line": 231
    },
    {
     "code": "c == '\\\\'",
     "line": 238
    },
    {
     "code": "c == ']'",
     "line": 243
    },
    {
     "code": "c == '\\\\'",
     "line": 246
    },
    {
     "code": "c == '['",
     "line": 274
    },
    {
     "code": "c == ']'",
     "line": 279
    },
    {
     "code": "c == '\\0'",
     "line": 282
    },
    {
     "code": "c == ']'",
     "line": 297
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "c = **p",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "**p",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*p",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "c",
    "p"
   ],
   "osv_id": "ARVO-42505099",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "setcharset"
  }
 },
 {
  "osv_id": "ARVO-42505128",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 515,
    "size": null,
    "type": "uint8_t*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 169
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 540,
    "fn": "ndlz4_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz4_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 540
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 201851904,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz4_decompress",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:522,IF:529,FOR:543,FOR:553,FOR:554,IF:555,IF:559,ELSE:561,IF:564,ELSE:566,IF:570,ELSE:573"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42505128/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
   "testcase_size": 73
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
   "dedup_token": "__asan_memset--ndlz4_decompress--blosc_d"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* op = (uint8_t*)output",
     "line": 515
    }
   ],
   "entity_decl": {
    "line": 515,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "op",
   "func_lines": [
    510,
    694
   ],
   "func_params": {
    "names": [
     "input",
     "input_len",
     "output",
     "output_len",
     "meta",
     "dparams"
    ],
    "types": [
     "uint8_t*",
     "int32_t",
     "uint8_t*",
     "int32_t",
     "uint8_t",
     "blosc2_dparams*"
    ]
   },
   "guards": [
    {
     "code": "ndim != 2",
     "line": 529
    },
    {
     "code": "i < 2",
     "line": 543
    },
    {
     "code": "ii[0] < i_stop[0]",
     "line": 553
    },
    {
     "code": "ii[1] < i_stop[1]",
     "line": 554
    },
    {
     "code": "ip > ip_limit",
     "line": 555
    },
    {
     "code": "ii[0] == i_stop[0] - 1",
     "line": 559
    },
    {
     "code": "blockshape[0] % 4 == 0",
     "line": 560
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 564
    },
    {
     "code": "blockshape[1] % 4 == 0",
     "line": 565
    },
    {
     "code": "token == 0",
     "line": 570
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 573
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 577
    },
    {
     "code": "(token >> 3U) == 28",
     "line": 587
    },
    {
     "code": "(token >> 3U) < 30",
     "line": 593
    },
    {
     "code": "(token >> 3U) == 30",
     "line": 598
    },
    {
     "code": "l < 4",
     "line": 608
    },
    {
     "code": "l != i",
     "line": 609
    },
    {
     "code": "l != j",
     "line": 609
    },
    {
     "code": "l != k",
     "line": 609
    },
    {
     "code": "token == 128",
     "line": 622
    },
    {
     "code": "k < 4",
     "line": 631
    },
    {
     "code": "k != i",
     "line": 632
    },
    {
     "code": "k != j",
     "line": 632
    },
    {
     "code": "k < 4",
     "line": 649
    },
    {
     "code": "k != i",
     "line": 650
    },
    {
     "code": "k != j",
     "line": 650
    },
    {
     "code": "l == -1",
     "line": 651
    },
    {
     "code": "i < 4",
     "line": 669
    },
    {
     "code": "i < padding[0]",
     "line": 670
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 676
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 684
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 688
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memset(op, 0, blockshape[0] * blockshape[1])",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "blockshape[0] * blockshape[1]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "blockshape[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "blockshape[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "op",
    "blockshape"
   ],
   "osv_id": "ARVO-42505128",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "blockshape[2]",
     "line": 517
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "eshape[2]",
     "line": 518
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "local_buffer[16]",
     "line": 520
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 542
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 549
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 550
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "cell_aux[16]",
     "line": 552
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz4_decompress"
  }
 },
 {
  "osv_id": "ARVO-42505679",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 515,
    "size": null,
    "type": "uint8_t*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 169
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 540,
    "fn": "ndlz4_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz4_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 540
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 48423648,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz4_decompress",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:522,IF:529,FOR:543,FOR:553,FOR:554,IF:555,IF:559,ELSE:561,IF:564,ELSE:566,IF:570,ELSE:573"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42505679/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
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
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memset--ndlz4_decompress--blosc_d"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* op = (uint8_t*)output",
     "line": 515
    }
   ],
   "entity_decl": {
    "line": 515,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "op",
   "func_lines": [
    510,
    694
   ],
   "func_params": {
    "names": [
     "input",
     "input_len",
     "output",
     "output_len",
     "meta",
     "dparams"
    ],
    "types": [
     "uint8_t*",
     "int32_t",
     "uint8_t*",
     "int32_t",
     "uint8_t",
     "blosc2_dparams*"
    ]
   },
   "guards": [
    {
     "code": "ndim != 2",
     "line": 529
    },
    {
     "code": "i < 2",
     "line": 543
    },
    {
     "code": "ii[0] < i_stop[0]",
     "line": 553
    },
    {
     "code": "ii[1] < i_stop[1]",
     "line": 554
    },
    {
     "code": "ip > ip_limit",
     "line": 555
    },
    {
     "code": "ii[0] == i_stop[0] - 1",
     "line": 559
    },
    {
     "code": "blockshape[0] % 4 == 0",
     "line": 560
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 564
    },
    {
     "code": "blockshape[1] % 4 == 0",
     "line": 565
    },
    {
     "code": "token == 0",
     "line": 570
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 573
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 577
    },
    {
     "code": "(token >> 3U) == 28",
     "line": 587
    },
    {
     "code": "(token >> 3U) < 30",
     "line": 593
    },
    {
     "code": "(token >> 3U) == 30",
     "line": 598
    },
    {
     "code": "l < 4",
     "line": 608
    },
    {
     "code": "l != i",
     "line": 609
    },
    {
     "code": "l != j",
     "line": 609
    },
    {
     "code": "l != k",
     "line": 609
    },
    {
     "code": "token == 128",
     "line": 622
    },
    {
     "code": "k < 4",
     "line": 631
    },
    {
     "code": "k != i",
     "line": 632
    },
    {
     "code": "k != j",
     "line": 632
    },
    {
     "code": "k < 4",
     "line": 649
    },
    {
     "code": "k != i",
     "line": 650
    },
    {
     "code": "k != j",
     "line": 650
    },
    {
     "code": "l == -1",
     "line": 651
    },
    {
     "code": "i < 4",
     "line": 669
    },
    {
     "code": "i < padding[0]",
     "line": 670
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 676
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 684
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 688
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memset(op, 0, blockshape[0] * blockshape[1])",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "blockshape[0] * blockshape[1]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "blockshape[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "blockshape[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "op",
    "blockshape"
   ],
   "osv_id": "ARVO-42505679",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "blockshape[2]",
     "line": 517
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "eshape[2]",
     "line": 518
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "local_buffer[16]",
     "line": 520
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 542
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 549
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 550
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "cell_aux[16]",
     "line": 552
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz4_decompress"
  }
 },
 {
  "osv_id": "ARVO-42505797",
  "project": "kamailio",
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
    "line": 794,
    "fn": "find_sdp_line_delimiter",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "find_sdp_line_delimiter",
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "line": 794
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "find_sdp_line_delimiter",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42505797/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 37
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "strncmp--find_sdp_line_delimiter--parse_mixed_content"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "find_sdp_line_delimiter"
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