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
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:271,FOR:277,IF:279,BREAK:280,IF:282,GOTO:283,IF:288,GOTO:289,IF:293",
   "fn": "sc_format_oid",
   "guard_count": 2,
   "guards": "oid == NULL | ii < SC_MAX_OBJECT_ID_OCTETS",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 17
   },
   "code": "oid->value[ii] = strtol(p, &q, 10) | oid->value[ii] | oid->value | strtol(p, &q, 10)",
   "site": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_format_oid",
    "line": 278
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 265,
    "size": null,
    "type": "sc_object_id*"
   },
   "kind": "pointer",
   "name": "oid",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509373/report.log",
   "testcase_size": 101
  },
  "input_reachability": [
   "oid",
   "in"
  ],
  "osv_id": "ARVO-42509373",
  "project": "opensc",
  "sites": [
   {
    "code": "oid->value[ii] = strtol(p, &q, 10) | oid->value[ii] | oid->value | strtol(p, &q, 10)",
    "fn": "sc_format_oid",
    "kind": "unknown",
    "line": 278,
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
   "entity_type": "sc_object_id*",
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
   "control_structures": "IF:908,ELSE:910,IF:919,DO:925,IF:925,DO:929,IF:929,ELSE:929",
   "fn": "sc_hsm_list_files",
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
    "width": 65538
   },
   "code": "memcpy(buf, recvbuf, buflen)",
   "site": {
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "fn": "sc_hsm_list_files",
    "line": 927
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "line": 901,
    "size": null,
    "type": "u8*"
   },
   "kind": "pointer",
   "name": "buf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b35993db095c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b35993db095c14be95fc0f40b96b44e2850b7990/ARVO-42510727/report.log",
   "testcase_size": 21
  },
  "input_reachability": [
   "buf",
   "buflen"
  ],
  "osv_id": "ARVO-42510727",
  "project": "opensc",
  "sites": [
   {
    "code": "memcpy(buf, recvbuf, buflen)",
    "fn": "sc_hsm_list_files",
    "kind": "unknown",
    "line": 927,
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
   "entity_type": "u8*",
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
   "call_chain"
  ],
  "context": {
   "fn": "dynapi_set_helper",
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
   "code": "",
   "site": {
    "file": "/src/libredwg/src/gen-dynapi.pl",
    "fn": "dynapi_set_helper",
    "line": 3093
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_d8911aa11479.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/libredwg/address/d8911aa11479953ca8ebda8367302767dcbc68f0/ARVO-42510993/report.log",
   "testcase_size": 36
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510993",
  "project": "libredwg",
  "sites": [
   {
    "code": "",
    "fn": "dynapi_set_helper",
    "kind": "unknown",
    "line": 3093,
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
   "control_structures": "DO:503,DO:516,IF:516,DO:518,IF:518,IF:520,WHILE:525,IF:529,IF:533,BREAK:535,IF:537,IF:542",
   "fn": "cardos_list_files",
   "guard_count": 2,
   "guards": "q == NULL | q != NULL",
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
   "code": "buf[fids++] = q[1] | buf[fids++] | fids++ | q[1]",
   "site": {
    "file": "/src/opensc/src/libopensc/card-cardos.c",
    "fn": "cardos_list_files",
    "line": 544
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-cardos.c",
    "line": 495,
    "size": null,
    "type": "u8*"
   },
   "kind": "pointer",
   "name": "buf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b35993db095c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b35993db095c14be95fc0f40b96b44e2850b7990/ARVO-42511654/report.log",
   "testcase_size": 375
  },
  "input_reachability": [
   "buf"
  ],
  "osv_id": "ARVO-42511654",
  "project": "opensc",
  "sites": [
   {
    "code": "buf[fids++] = q[1] | buf[fids++] | fids++ | q[1]",
    "fn": "cardos_list_files",
    "kind": "unknown",
    "line": 544,
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
   "entity_type": "u8*",
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
   "control_structures": "DO:1207,IF:1212,IF:1217,BREAK:1226",
   "fn": "tlsCheckUncommonALPN",
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
    "width": 116
   },
   "code": "strncpy(str, alpn_start, alpn_len)",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "fn": "tlsCheckUncommonALPN",
    "line": 1224
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1218,
    "size": null,
    "type": "char[64]"
   },
   "kind": "array",
   "name": "str",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_897f8314b29c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/897f8314b29cd7de9eeab9af15b3e189ae6724a1/ARVO-42511896/report.log",
   "testcase_size": 295
  },
  "input_reachability": [],
  "osv_id": "ARVO-42511896",
  "project": "ndpi",
  "sites": [
   {
    "code": "strncpy(str, alpn_start, alpn_len)",
    "fn": "tlsCheckUncommonALPN",
    "kind": "unknown",
    "line": 1224,
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
   "entity_type": "char[64]",
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
   "fn": "get_transaction",
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
    "file": "/src/wireshark/epan/dissectors/packet-atalk.c",
    "fn": "get_transaction",
    "line": 1015
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_3307397da14b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/3307397da14b543a289191c23af9a61fb32eeb46/ARVO-42514948/report.log",
   "testcase_size": 960
  },
  "input_reachability": [],
  "osv_id": "ARVO-42514948",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "get_transaction",
    "kind": "unknown",
    "line": 1015,
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
   "control_structures": "IF:1040,ELSE:1042,IF:1042,ELSE:1044,IF:1044,ELSE:1046,IF:1046,ELSE:1048,IF:1048,ELSE:1050,IF:1050,ELSE:1052",
   "fn": "sc_hsm_decode_ecdsa_signature",
   "guard_count": 2,
   "guards": "i<2 | taglen > fieldsizebytes",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 256
   },
   "code": "memcpy(out + fieldsizebytes*i + fieldsizebytes - taglen  | out + fieldsizebytes*i + fieldsizebytes - taglen | out + fieldsizebytes*i + fieldsizebytes | out + fieldsizebytes*i",
   "site": {
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "fn": "sc_hsm_decode_ecdsa_signature",
    "line": 1083
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "line": 1032,
    "size": null,
    "type": "u8*"
   },
   "kind": "pointer",
   "name": "out",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_4edb7ceffb6d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/4edb7ceffb6d704688be20a71c77d302dea0e82a/ARVO-42515176/report.log",
   "testcase_size": 41798
  },
  "input_reachability": [
   "data",
   "out",
   "outlen"
  ],
  "osv_id": "ARVO-42515176",
  "project": "opensc",
  "sites": [
   {
    "code": "memcpy(out + fieldsizebytes*i + fieldsizebytes - taglen  | out + fieldsizebytes*i + fieldsizebytes - taglen | out + fieldsizebytes*i + fieldsizebytes | out + fieldsizebytes*i",
    "fn": "sc_hsm_decode_ecdsa_signature",
    "kind": "unknown",
    "line": 1083,
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
   "entity_type": "u8*",
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
   "control_structures": "IF:645,IF:648,ELSE:651,IF:651,FOR:656,IF:659,IF:662,ELSE:667,IF:667",
   "fn": "ndpi_check_http_server",
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
    "width": 17
   },
   "code": "snprintf(msg, sizeof(msg), \"Obsolete nginx server %s\", b | sizeof(msg)",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "fn": "ndpi_check_http_server",
    "line": 670
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 668,
    "size": null,
    "type": "char[64]"
   },
   "kind": "array",
   "name": "msg",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_37c88b129f6f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/37c88b129f6f5a3475dc6364cc4a898df9ff37ab/ARVO-42516818/report.log",
   "testcase_size": 64
  },
  "input_reachability": [
   "server"
  ],
  "osv_id": "ARVO-42516818",
  "project": "ndpi",
  "sites": [
   {
    "code": "snprintf(msg, sizeof(msg), \"Obsolete nginx server %s\", b | sizeof(msg)",
    "fn": "ndpi_check_http_server",
    "kind": "unknown",
    "line": 670,
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
   "entity_type": "char[64]",
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
   "fn": "dissect_he_feedback_matrix",
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
    "width": 9
   },
   "code": null,
   "site": {
    "file": "/src/wireshark/epan/dissectors/packet-ieee80211.c",
    "fn": "dissect_he_feedback_matrix",
    "line": 15203
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_139e46898dfd.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/139e46898dfd4aeed90da6f0684f8e32475340c8/ARVO-42517300/report.log",
   "testcase_size": 131
  },
  "input_reachability": [],
  "osv_id": "ARVO-42517300",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "dissect_he_feedback_matrix",
    "kind": "unknown",
    "line": 15203,
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
   "control_structures": "IF:149,ELSE:150,IF:151,IF:152,IF:154,IF:159,ELSE:165,IF:165,IF:171,ELSE:172,IF:172,FOR:176",
   "fn": "_my_getopt_internal",
   "guard_count": 3,
   "guards": "my_optind >= argc | k+1<my_optind | my_optind > argc",
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
   "code": "(argv[my_optind][0] == '-') &&",
   "site": {
    "file": "/src/opensc/src/libopensc/card-authentic.c",
    "fn": "authentic_parse_size",
    "line": 160
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-authentic.c",
    "line": 142,
    "size": null,
    "type": "char[]*"
   },
   "kind": "pointer",
   "name": "argv",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b35993db095c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b35993db095c14be95fc0f40b96b44e2850b7990/ARVO-42517374/report.log",
   "testcase_size": 1248
  },
  "input_reachability": [
   "argc",
   "argv"
  ],
  "osv_id": "ARVO-42517374",
  "project": "opensc",
  "sites": [
   {
    "code": "(argv[my_optind][0] == '-') &&",
    "fn": "authentic_parse_size",
    "kind": "unknown",
    "line": 160,
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
   "entity_type": "char[]*",
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
   "control_structures": "IF:468,IF:473,IF:474,IF:479,IF:484,ELSE:487,IF:493,IF:499,IF:500,ELSE:502,SWITCH:519,BREAK:525",
   "fn": "write",
   "guard_count": 2,
   "guards": "x < tmpgrayimage.width() | x < tmpgrayimage.width()",
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
   "code": "x = 0 | x < tmpgrayimage.width() | tmpgrayimage.width() | x++",
   "site": {
    "file": "/src/kimageformats/src/imageformats/raw.cpp",
    "fn": "(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)",
    "line": 608
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/kimageformats/src/imageformats/raw.cpp",
    "line": 608,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "x",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_d881a7bbb156.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/kimageformats/address/d881a7bbb1562af383bbb6ca20340ad739fb0d13/ARVO-42517499/report.log",
   "testcase_size": 471
  },
  "input_reachability": [
   "image"
  ],
  "osv_id": "ARVO-42517499",
  "project": "kimageformats",
  "sites": [
   {
    "code": "x = 0 | x < tmpgrayimage.width() | tmpgrayimage.width() | x++",
    "fn": "(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)",
    "kind": "unknown",
    "line": 608,
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
   "entity_type": "int",
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
   "control_structures": "IF:453,IF:456,IF:460,FOR:461,FOR:466,IF:468",
   "fn": "sc_path_print",
   "guard_count": 5,
   "guards": "buf == NULL | path == NULL | buflen < path->len * 2 + path->aid.len * 2 + 3",
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
   "code": "snprintf(buf + strlen(buf), buflen - strlen(buf), \"%02x\" | buf + strlen(buf) | strlen(buf) | buflen - strlen(buf)",
   "site": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_path_print",
    "line": 467
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "line": 449,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "buf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42518213/report.log",
   "testcase_size": 4945
  },
  "input_reachability": [
   "buf",
   "buflen",
   "path"
  ],
  "osv_id": "ARVO-42518213",
  "project": "opensc",
  "sites": [
   {
    "code": "snprintf(buf + strlen(buf), buflen - strlen(buf), \"%02x\" | buf + strlen(buf) | strlen(buf) | buflen - strlen(buf)",
    "fn": "sc_path_print",
    "kind": "unknown",
    "line": 467,
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
   "entity_type": "char*",
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
   "control_structures": "FOR:133,DO:135,IF:135",
   "fn": "msc_zero_object",
   "guard_count": 1,
   "guards": "(dataLength - i) < (max_write_unit)",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 65526
   },
   "code": "memset(zeroBuffer, 0, max_write_unit)",
   "site": {
    "file": "/src/opensc/src/libopensc/muscle.c",
    "fn": "msc_zero_object",
    "line": 132
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/muscle.c",
    "line": 128,
    "size": null,
    "type": "u8[512]"
   },
   "kind": "array",
   "name": "zeroBuffer",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42518451/report.log",
   "testcase_size": 104
  },
  "input_reachability": [],
  "osv_id": "ARVO-42518451",
  "project": "opensc",
  "sites": [
   {
    "code": "memset(zeroBuffer, 0, max_write_unit)",
    "fn": "msc_zero_object",
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
   "entity_type": "u8[512]",
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
   "control_structures": "IF:661,IF:665,IF:667,IF:670,WHILE:677,IF:681,IF:682,CONTINUE:683,BREAK:684,IF:690,IF:698,IF:702",
   "fn": "sc_pkcs15init_rmdir",
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
   "code": "path.value[path.len-1] = buffer[2*nfids+1] | path.value[path.len-1] | path.value | path.len-1",
   "site": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "fn": "sc_pkcs15init_rmdir",
    "line": 679
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "line": 657,
    "size": null,
    "type": "sc_path"
   },
   "kind": "struct",
   "name": "path",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42518779/report.log",
   "testcase_size": 5386
  },
  "input_reachability": [
   "p15card",
   "df"
  ],
  "osv_id": "ARVO-42518779",
  "project": "opensc",
  "sites": [
   {
    "code": "path.value[path.len-1] = buffer[2*nfids+1] | path.value[path.len-1] | path.value | path.len-1",
    "fn": "sc_pkcs15init_rmdir",
    "kind": "unknown",
    "line": 679,
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
   "entity_type": "sc_path",
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
   "fn": "dump_stats",
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
    "file": "/src/flac/src/flac/analyze.c",
    "fn": "dump_stats",
    "line": 219
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
   "cpg": "/root/gyx/mutator_create/cpg_files/flac_9382c5375bb6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/flac/address/9382c5375bb66872cdedb0fd36e68e371fae8721/ARVO-42523836/report.log",
   "testcase_size": 126
  },
  "input_reachability": [],
  "osv_id": "ARVO-42523836",
  "project": "flac",
  "sites": [
   {
    "code": null,
    "fn": "dump_stats",
    "kind": "unknown",
    "line": 219,
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