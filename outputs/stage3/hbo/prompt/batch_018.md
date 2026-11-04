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
  "osv_id": "ARVO-42500607",
  "project": "net-snmp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 7273,
    "type": "u_char*",
    "size": null
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "snmp_realloc",
    "file": "/src/net-snmp/snmplib/tools.c",
    "line": 182
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(oid) * MAX_OID_LEN",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 7604,
    "fn": "snmp_add_var",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "snmp_add_var",
    "file": "/src/net-snmp/snmplib/snmp_api.c",
    "line": 7604
   },
   "code": "buf[ix] ",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "snmp_add_var",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/05a463fd4ca6ffa51698e00ddd6e30d0db1b5efd/ARVO-42500607/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_05a463fd4ca6.cpg",
   "testcase_size": 21
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
   "dedup_token": "snmp_add_var--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*buf = NULL",
     "line": 7273
    },
    {
     "code": "buf = (u_char *)malloc(sizeof(oid) * MAX_OID_LEN)",
     "line": 7477
    },
    {
     "code": "buf = (u_char *) malloc(256)",
     "line": 7549
    },
    {
     "code": "buf = (u_char *)calloc(1, 4)",
     "line": 7648
    }
   ],
   "entity_decl": {
    "line": 7273,
    "type": "u_char*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    7255,
    7733
   ],
   "func_params": {
    "names": [
     "pdu",
     "name",
     "name_length",
     "type",
     "value"
    ],
    "types": [
     "netsnmp_pdu*",
     "oid*",
     "size_t",
     "char",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "tp->type > TYPE_SIMPLE_LAST",
     "line": 7286
    },
    {
     "code": "type == '='",
     "line": 7292
    },
    {
     "code": "tp->type != TYPE_INTEGER",
     "line": 7336
    },
    {
     "code": "tp->type != TYPE_INTEGER32",
     "line": 7337
    },
    {
     "code": "strcmp(value, ep->label) == 0",
     "line": 7350
    },
    {
     "code": "tp->type != TYPE_GAUGE",
     "line": 7376
    },
    {
     "code": "tp->type != TYPE_UNSIGNED32",
     "line": 7376
    },
    {
     "code": "tp->type != TYPE_UINTEGER",
     "line": 7392
    },
    {
     "code": "tp->type != TYPE_COUNTER",
     "line": 7408
    },
    {
     "code": "tp->type != TYPE_COUNTER64",
     "line": 7424
    },
    {
     "code": "tp->type != TYPE_TIMETICKS",
     "line": 7439
    },
    {
     "code": "tp->type != TYPE_IPADDR",
     "line": 7455
    },
    {
     "code": "atmp != (in_addr_t) -1",
     "line": 7462
    },
    {
     "code": "tp->type != TYPE_OBJID",
     "line": 7471
    },
    {
     "code": "(buf = (u_char *)malloc(sizeof(oid) * MAX_OID_LEN)) == NULL",
     "line": 7477
    },
    {
     "code": "tp->type != TYPE_OCTETSTR",
     "line": 7494
    },
    {
     "code": "tp->type != TYPE_BITSTRING",
     "line": 7494
    },
    {
     "code": "'s' == type",
     "line": 7499
    },
    {
     "code": "type == 'd'",
     "line": 7509
    },
    {
     "code": "type == 'x'",
     "line": 7517
    },
    {
     "code": "type == 's'",
     "line": 7524
    },
    {
     "code": "tp->type != TYPE_BITSTRING",
     "line": 7542
    },
    {
     "code": "(buf = (u_char *) malloc(256)) == NULL",
     "line": 7549
    },
    {
     "code": "*ecp != 0",
     "line": 7574
    },
    {
     "code": "ep != NULL",
     "line": 7576
    },
    {
     "code": "strcmp(ep->label, cp) == 0",
     "line": 7577
    },
    {
     "code": "ep != NULL",
     "line": 7581
    },
    {
     "code": "buf != NULL",
     "line": 7649
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "buf[ix] ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "buf[ix]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "ix",
    "bit"
   ],
   "osv_id": "ARVO-42500607",
   "sites": [
    {
     "args": "sizeof(oid) * MAX_OID_LEN",
     "callee": "malloc",
     "code": "malloc(sizeof(oid) * MAX_OID_LEN)",
     "line": 7477
    },
    {
     "args": "hintptr",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(hintptr)",
     "line": 7504
    },
    {
     "args": "256",
     "callee": "malloc",
     "code": "malloc(256)",
     "line": 7549
    },
    {
     "args": "value",
     "callee": "strdup",
     "code": "strdup(value)",
     "line": 7565
    },
    {
     "args": "buf",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(buf)",
     "line": 7567
    },
    {
     "args": "buf",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(buf)",
     "line": 7587
    },
    {
     "args": "vp",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(vp)",
     "line": 7588
    },
    {
     "args": "&buf ;; &buf_len",
     "callee": "snmp_realloc",
     "code": "snmp_realloc(&buf, &buf_len)",
     "line": 7599
    },
    {
     "args": "vp",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(vp)",
     "line": 7607
    },
    {
     "args": "1 ;; 4",
     "callee": "calloc",
     "code": "calloc(1, 4)",
     "line": 7648
    },
    {
     "args": "buf",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(buf)",
     "line": 7656
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "error_msg[256]",
     "line": 7663
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "undef_msg[32]",
     "line": 7664
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "snmp_add_var"
  }
 },
 {
  "osv_id": "ARVO-42500699",
  "project": "net-snmp",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/net-snmp/snmplib/snmp_api.c",
    "line": 7273,
    "size": null,
    "type": "u_char*"
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "snmp_realloc",
    "file": "/src/net-snmp/snmplib/tools.c",
    "line": 182
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(oid) * MAX_OID_LEN",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "code": "malloc(sizeof(oid) * MAX_OID_LEN)",
    "fn": "snmp_add_var",
    "kind": "malloc",
    "line": 7477,
    "origin": "cpg",
    "args": "sizeof(oid) * MAX_OID_LEN"
   },
   {
    "code": "malloc(256)",
    "fn": "snmp_add_var",
    "kind": "malloc",
    "line": 7549,
    "origin": "cpg",
    "args": "256"
   },
   {
    "code": "strdup(value)",
    "fn": "snmp_add_var",
    "kind": "strdup",
    "line": 7565,
    "origin": "cpg",
    "args": "value"
   },
   {
    "kind": "unknown",
    "line": 7604,
    "fn": "snmp_add_var",
    "code": "buf[ix] |= bit | buf[ix]",
    "origin": "report:crash"
   },
   {
    "code": "calloc(1, 4)",
    "fn": "snmp_add_var",
    "kind": "calloc",
    "line": 7648,
    "origin": "cpg",
    "args": "1 ;; 4"
   }
  ],
  "crash": {
   "site": {
    "fn": "snmp_add_var",
    "file": "/src/net-snmp/snmplib/snmp_api.c",
    "line": 7604
   },
   "code": "buf[ix] |= bit | buf[ix]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "snmp_add_var",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "ix >= (int) tint | ix >= (int)buf_len | buf != NULL",
   "guard_count": 3,
   "control_structures": "IF:7286,IF:7289,IF:7292,SWITCH:7296,BREAK:7300,BREAK:7304,BREAK:7307,BREAK:7310,BREAK:7313,BREAK:7316,BREAK:7319,BREAK:7322"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "type"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/05a463fd4ca6ffa51698e00ddd6e30d0db1b5efd/ARVO-42500699/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_05a463fd4ca6.cpg",
   "testcase_size": 21
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
   "dedup_token": "snmp_add_var--LLVMFuzzerTestOneInput--ExecuteFilesOnyByOne"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*buf = NULL",
     "line": 7273
    },
    {
     "code": "buf = (u_char *)malloc(sizeof(oid) * MAX_OID_LEN)",
     "line": 7477
    },
    {
     "code": "buf = (u_char *) malloc(256)",
     "line": 7549
    },
    {
     "code": "buf = (u_char *)calloc(1, 4)",
     "line": 7648
    }
   ],
   "entity_decl": {
    "line": 7273,
    "type": "u_char*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    7255,
    7733
   ],
   "func_params": {
    "names": [
     "pdu",
     "name",
     "name_length",
     "type",
     "value"
    ],
    "types": [
     "netsnmp_pdu*",
     "oid*",
     "size_t",
     "char",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "tp->type > TYPE_SIMPLE_LAST",
     "line": 7286
    },
    {
     "code": "type == '='",
     "line": 7292
    },
    {
     "code": "tp->type != TYPE_INTEGER",
     "line": 7336
    },
    {
     "code": "tp->type != TYPE_INTEGER32",
     "line": 7337
    },
    {
     "code": "strcmp(value, ep->label) == 0",
     "line": 7350
    },
    {
     "code": "tp->type != TYPE_GAUGE",
     "line": 7376
    },
    {
     "code": "tp->type != TYPE_UNSIGNED32",
     "line": 7376
    },
    {
     "code": "tp->type != TYPE_UINTEGER",
     "line": 7392
    },
    {
     "code": "tp->type != TYPE_COUNTER",
     "line": 7408
    },
    {
     "code": "tp->type != TYPE_COUNTER64",
     "line": 7424
    },
    {
     "code": "tp->type != TYPE_TIMETICKS",
     "line": 7439
    },
    {
     "code": "tp->type != TYPE_IPADDR",
     "line": 7455
    },
    {
     "code": "atmp != (in_addr_t) -1",
     "line": 7462
    },
    {
     "code": "tp->type != TYPE_OBJID",
     "line": 7471
    },
    {
     "code": "(buf = (u_char *)malloc(sizeof(oid) * MAX_OID_LEN)) == NULL",
     "line": 7477
    },
    {
     "code": "tp->type != TYPE_OCTETSTR",
     "line": 7494
    },
    {
     "code": "tp->type != TYPE_BITSTRING",
     "line": 7494
    },
    {
     "code": "'s' == type",
     "line": 7499
    },
    {
     "code": "type == 'd'",
     "line": 7509
    },
    {
     "code": "type == 'x'",
     "line": 7517
    },
    {
     "code": "type == 's'",
     "line": 7524
    },
    {
     "code": "tp->type != TYPE_BITSTRING",
     "line": 7542
    },
    {
     "code": "(buf = (u_char *) malloc(256)) == NULL",
     "line": 7549
    },
    {
     "code": "*ecp != 0",
     "line": 7574
    },
    {
     "code": "ep != NULL",
     "line": 7576
    },
    {
     "code": "strcmp(ep->label, cp) == 0",
     "line": 7577
    },
    {
     "code": "ep != NULL",
     "line": 7581
    },
    {
     "code": "buf != NULL",
     "line": 7649
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "buf[ix] ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "buf[ix]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "ix",
    "bit"
   ],
   "osv_id": "ARVO-42500699",
   "sites": [
    {
     "args": "sizeof(oid) * MAX_OID_LEN",
     "callee": "malloc",
     "code": "malloc(sizeof(oid) * MAX_OID_LEN)",
     "line": 7477
    },
    {
     "args": "hintptr",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(hintptr)",
     "line": 7504
    },
    {
     "args": "256",
     "callee": "malloc",
     "code": "malloc(256)",
     "line": 7549
    },
    {
     "args": "value",
     "callee": "strdup",
     "code": "strdup(value)",
     "line": 7565
    },
    {
     "args": "buf",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(buf)",
     "line": 7567
    },
    {
     "args": "buf",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(buf)",
     "line": 7587
    },
    {
     "args": "vp",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(vp)",
     "line": 7588
    },
    {
     "args": "&buf ;; &buf_len",
     "callee": "snmp_realloc",
     "code": "snmp_realloc(&buf, &buf_len)",
     "line": 7599
    },
    {
     "args": "vp",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(vp)",
     "line": 7607
    },
    {
     "args": "1 ;; 4",
     "callee": "calloc",
     "code": "calloc(1, 4)",
     "line": 7648
    },
    {
     "args": "buf",
     "callee": "SNMP_FREE",
     "code": "SNMP_FREE(buf)",
     "line": 7656
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "error_msg[256]",
     "line": 7663
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "undef_msg[32]",
     "line": 7664
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "snmp_add_var"
  }
 },
 {
  "osv_id": "ARVO-42501136",
  "project": "matio",
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
    "fn": "H5MM_malloc",
    "file": "/src/hdf5-1.12.1/src/H5MM.c",
    "line": 313
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "sizeof(*mat)",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 609,
    "fn": "Mat_Open",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_Open",
    "file": "/src/matio/src/mat.c",
    "line": 609
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_Open",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/2945c0ded5ede79eae3cba3a5d12450ba2917fbc/ARVO-42501136/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_2945c0ded5ed.cpg",
   "testcase_size": 35337
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
   "dedup_token": "H5O__linfo_decode--H5O_msg_read_oh--H5O_msg_read"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    442,
    630
   ],
   "func_params": {
    "names": [
     "matname",
     "mode"
    ],
    "types": [
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "(mode & 0x01) == MAT_ACC_RDONLY",
     "line": 450
    },
    {
     "code": "(mode & 0x01) == MAT_ACC_RDWR",
     "line": 462
    },
    {
     "code": "NULL == mat",
     "line": 482
    },
    {
     "code": "NULL == mat->header",
     "line": 490
    },
    {
     "code": "NULL == mat->subsys_offset",
     "line": 497
    },
    {
     "code": "128 == bytesread",
     "line": 519
    },
    {
     "code": "tmp == 0x4d49",
     "line": 522
    },
    {
     "code": "tmp == 0x494d",
     "line": 524
    },
    {
     "code": "mat->version == 0x0100",
     "line": 530
    },
    {
     "code": "mat->version == 0x0200",
     "line": 530
    },
    {
     "code": "-1 != mat->byteswap",
     "line": 530
    },
    {
     "code": "mat->bof == -1L",
     "line": 532
    },
    {
     "code": "0 == mat->version",
     "line": 546
    },
    {
     "code": "NULL == var",
     "line": 567
    },
    {
     "code": "bytesread != 0",
     "line": 567
    },
    {
     "code": "NULL == mat",
     "line": 578
    },
    {
     "code": "mat->version == 0x0200",
     "line": 584
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42501136",
   "sites": [
    {
     "args": "sizeof(*mat)",
     "callee": "malloc",
     "code": "malloc(sizeof(*mat))",
     "line": 481
    },
    {
     "args": "128 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(128, sizeof(char))",
     "line": 489
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 491
    },
    {
     "args": "8 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(8, sizeof(char))",
     "line": 496
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 498
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 499
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 533
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 534
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 535
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 550
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 551
    },
    {
     "args": "var",
     "callee": "Mat_VarFree",
     "code": "Mat_VarFree(var)",
     "line": 573
    },
    {
     "args": "matname",
     "callee": "strdup",
     "code": "strdup(matname)",
     "line": 581
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_Open"
  }
 },
 {
  "osv_id": "ARVO-42501143",
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
    "line": 59,
    "fn": "trim_leading",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "trim_leading",
    "file": "/src/kamailio/src/core/trim.h",
    "line": 59
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "trim_leading",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501143/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 17
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "trim_leading--parse_contacts--contact_parser"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "trim_leading"
  }
 },
 {
  "osv_id": "ARVO-42501146",
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
    "line": 251,
    "fn": "parse_content_length",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_content_length",
    "file": "/src/kamailio/src/core/parser/parse_content.c",
    "line": 251
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_content_length",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501146/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 17
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "parse_content_length--get_hdr_field--parse_headers"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse_content_length"
  }
 },
 {
  "osv_id": "ARVO-42501148",
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
    "line": 408,
    "fn": "parse_param_name",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_param_name",
    "file": "/src/kamailio/src/core/parser/parse_param.c",
    "line": 408
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_param_name",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501148/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 166
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
   "dedup_token": "parse_param_name--parse_param2--parse_params2"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse_param_name"
  }
 },
 {
  "osv_id": "ARVO-42501162",
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
    "line": 422,
    "fn": "q_memchr",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "q_memchr",
    "file": "/src/kamailio/src/core/ut.h",
    "line": 422
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "q_memchr",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501162/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 147
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "dedup_token": "q_memchr--parse_quoted_param--parse_param_body"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "q_memchr"
  }
 },
 {
  "osv_id": "ARVO-42501179",
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
    "line": 228,
    "fn": "parse_to_param",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_to_param",
    "file": "/src/kamailio/src/core/parser/parse_addr_spec.c",
    "line": 228
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_to_param",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501179/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 17
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "parse_to_param--parse_addr_spec--parse_to"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse_to_param"
  }
 },
 {
  "osv_id": "ARVO-42501369",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "mid",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/vm.c",
    "line": 2820,
    "size": null,
    "type": "mrb_sym"
   }
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
  "sites": [
   {
    "kind": "unknown",
    "line": 1468,
    "fn": "mrb_vm_exec",
    "code": "mid = syms[b] | syms[b]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mrb_vm_exec",
    "file": "/src/mruby/src/vm.c",
    "line": 1468
   },
   "code": "mid = syms[b] | syms[b]",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_vm_exec",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "b < MRB_ENV_LEN(e) | b < MRB_ENV_LEN(e) | mid != missing",
   "guard_count": 7,
   "control_structures": "IF:1118,IF:1121,GOTO:1122,GOTO:1123,FOR:1129,SWITCH:1129,GOTO:1132,GOTO:1137,SWITCH:1141,BREAK:1144,GOTO:1156,GOTO:1159"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mrb_sym",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e60ddc431d242ede15e8f4d59a1a815fac532dc6/ARVO-42501369/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e60ddc431d24.cpg",
   "testcase_size": 210699
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
   "dedup_token": "mrb_vm_exec--mrb_vm_run--mrb_top_run"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "mid = syms[b]",
     "line": 1468
    },
    {
     "code": "mid = missing",
     "line": 1513
    },
    {
     "code": "mid = ci->mid",
     "line": 1639
    },
    {
     "code": "mid = p->e.env->mid",
     "line": 1643
    },
    {
     "code": "mid = missing",
     "line": 1702
    },
    {
     "code": "mid = MRB_OPSYM(add)",
     "line": 2370
    },
    {
     "code": "mid = MRB_OPSYM(sub)",
     "line": 2374
    },
    {
     "code": "mid = MRB_OPSYM(mul)",
     "line": 2378
    },
    {
     "code": "mid = MRB_OPSYM(div)",
     "line": 2412
    },
    {
     "code": "mid = MRB_OPSYM(add)",
     "line": 2458
    },
    {
     "code": "mid = MRB_OPSYM(sub)",
     "line": 2462
    },
    {
     "code": "mid = MRB_OPSYM(eq)",
     "line": 2523
    },
    {
     "code": "mid = MRB_OPSYM(lt)",
     "line": 2529
    },
    {
     "code": "mid = MRB_OPSYM(le)",
     "line": 2534
    },
    {
     "code": "mid = MRB_OPSYM(gt)",
     "line": 2539
    },
    {
     "code": "mid = MRB_OPSYM(ge)",
     "line": 2544
    },
    {
     "code": "mid = syms[b]",
     "line": 2820
    }
   ],
   "entity_decl": {
    "line": 1102,
    "type": "mrb_sym"
   },
   "entity_name_cpg": "mid",
   "func_lines": [
    1089,
    2949
   ],
   "func_params": {
    "names": [
     "mrb",
     "proc",
     "pc"
    ],
    "types": [
     "mrb_state*",
     "RProc*",
     "mrb_code*"
    ]
   },
   "guards": [
    {
     "code": "mrb->exc->tt == MRB_TT_BREAK",
     "line": 1121
    },
    {
     "code": "b < MRB_ENV_LEN(e)",
     "line": 1307
    },
    {
     "code": "b < MRB_ENV_LEN(e)",
     "line": 1322
    },
    {
     "code": "a < irep->ilen",
     "line": 1363
    },
    {
     "code": "a < mrb_irep_catch_handler_unpack(ch->begin)",
     "line": 1369
    },
    {
     "code": "mrb->exc == NULL",
     "line": 1384
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1454
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1461
    },
    {
     "code": "c == CALL_MAXARGS",
     "line": 1471
    },
    {
     "code": "argc < 0",
     "line": 1472
    },
    {
     "code": "bidx < irep->nregs",
     "line": 1478
    },
    {
     "code": "mid != missing",
     "line": 1499
    },
    {
     "code": "argc > 0",
     "line": 1527
    },
    {
     "code": "argc == -1",
     "line": 1527
    },
    {
     "code": "RARRAY_LEN(regs[1]) != 0",
     "line": 1527
    },
    {
     "code": "MRB_PROC_ENV(p) == mrb_vm_ci_env(&ci[-1])",
     "line": 1540
    },
    {
     "code": "ci->acc == CI_ACC_RESUMED",
     "line": 1545
    },
    {
     "code": "argc < 0",
     "line": 1568
    },
    {
     "code": "irep->nregs < 3",
     "line": 1568
    },
    {
     "code": "ci->argc < 0",
     "line": 1615
    },
    {
     "code": "irep->nregs > 3",
     "line": 1616
    },
    {
     "code": "ci->argc+2 < irep->nregs",
     "line": 1620
    },
    {
     "code": "b == CALL_MAXARGS",
     "line": 1632
    },
    {
     "code": "argc < 0",
     "line": 1633
    },
    {
     "code": "p->e.env->mid != mid",
     "line": 1642
    },
    {
     "code": "bidx < irep->nregs",
     "line": 1645
    },
    {
     "code": "mid == 0",
     "line": 1647
    },
    {
     "code": "target_class->tt == MRB_TT_MODULE",
     "line": 1655
    },
    {
     "code": "target_class->tt != MRB_TT_ICLASS",
     "line": 1657
    },
    {
     "code": "mid != missing",
     "line": 1688
    },
    {
     "code": "ci->acc == CI_ACC_RESUMED",
     "line": 1723
    },
    {
     "code": "argc < 0",
     "line": 1749
    },
    {
     "code": "irep->nregs < 3",
     "line": 1749
    },
    {
     "code": "mrb->c->ci->mid == 0",
     "line": 1763
    },
    {
     "code": "mrb_vm_ci_target_class(mrb->c->ci) == NULL",
     "line": 1763
    },
    {
     "code": "lv == 0",
     "line": 1771
    },
    {
     "code": "r == 0",
     "line": 1779
    },
    {
     "code": "m1 > 0",
     "line": 1795
    },
    {
     "code": "len > 0",
     "line": 1798
    },
    {
     "code": "m2 > 0",
     "line": 1801
    },
    {
     "code": "MRB_ASPEC_KEY(a) > 0",
     "line": 1819
    },
    {
     "code": "argc < 0",
     "line": 1828
    },
    {
     "code": "argc < 0",
     "line": 1833
    },
    {
     "code": "argc < m1 + m2",
     "line": 1842
    },
    {
     "code": "r == 0",
     "line": 1842
    },
    {
     "code": "argc > len + kd",
     "line": 1842
    },
    {
     "code": "len > 1",
     "line": 1848
    },
    {
     "code": "argc == 1",
     "line": 1848
    },
    {
     "code": "argc == m1+m2",
     "line": 1856
    },
    {
     "code": "argc > 0",
     "line": 1861
    },
    {
     "code": "MRB_ASPEC_KEY(a) > 0",
     "line": 1874
    },
    {
     "code": "argc-kargs < len",
     "line": 1881
    },
    {
     "code": "argc < m1+m2",
     "line": 1883
    },
    {
     "code": "m1 < argc",
     "line": 1884
    },
    {
     "code": "argv0 != argv",
     "line": 1890
    },
    {
     "code": "argc < m1",
     "line": 1893
    },
    {
     "code": "mlen < m2",
     "line": 1900
    },
    {
     "code": "o > 0",
     "line": 1908
    },
    {
     "code": "argc-kargs > m1+m2",
     "line": 1908
    },
    {
     "code": "argv0 != argv",
     "line": 1913
    },
    {
     "code": "argc-m2 > m1",
     "line": 1926
    },
    {
     "code": "argv0 == argv",
     "line": 1930
    },
    {
     "code": "irep->nlocals-blk_pos-1 > 0",
     "line": 1941
    },
    {
     "code": "ci->argc < 0",
     "line": 2004
    },
    {
     "code": "ci > mrb->c->cibase",
     "line": 2014
    },
    {
     "code": "MRB_PROC_ENV(p) == mrb_vm_ci_env(&ci[-1])",
     "line": 2014
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2023
    },
    {
     "code": "ch == NULL",
     "line": 2025
    },
    {
     "code": "(ch = catch_handler_find(mrb, ci, pc, MRB_CATCH_FILTER_ALL)) == NULL",
     "line": 2028
    },
    {
     "code": "ci[1].acc == CI_ACC_SKIP",
     "line": 2030
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2035
    },
    {
     "code": "ch == NULL",
     "line": 2037
    },
    {
     "code": "mrb->c == mrb->root_c",
     "line": 2039
    },
    {
     "code": "ch == NULL",
     "line": 2056
    },
    {
     "code": "e->cxt != mrb->c",
     "line": 2087
    },
    {
     "code": "ci->proc != dst",
     "line": 2093
    },
    {
     "code": "ci->acc < 0",
     "line": 2094
    },
    {
     "code": "ci->proc != dst",
     "line": 2105
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2124
    },
    {
     "code": "c->prev->ci == c->prev->cibase",
     "line": 2132
    },
    {
     "code": "e->cxt != mrb->c",
     "line": 2183
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2195
    },
    {
     "code": "ci->acc < 0",
     "line": 2202
    },
    {
     "code": "mrb->c->cibase < ci",
     "line": 2227
    },
    {
     "code": "ci[-1].proc != proc->upper",
     "line": 2227
    },
    {
     "code": "ci[-1].acc == CI_ACC_SKIP",
     "line": 2228
    },
    {
     "code": "ci == mrb->c->cibase",
     "line": 2248
    },
    {
     "code": "ci == mrb->c->ci",
     "line": 2257
    },
    {
     "code": "mrb->exc == NULL",
     "line": 2258
    },
    {
     "code": "acc == CI_ACC_SKIP",
     "line": 2268
    },
    {
     "code": "acc == CI_ACC_DIRECT",
     "line": 2268
    },
    {
     "code": "lv == 0",
     "line": 2294
    },
    {
     "code": "e->mid == 0",
     "line": 2297
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) == mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) == mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) == mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) == mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2523
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) < mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) < mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) < mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) < mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2529
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) > mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_fixnum((mrb->c->ci->stack)[a]) > mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) > mrb_fixnum((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "mrb_float((mrb->c->ci->stack)[a]) > mrb_float((mrb->c->ci->stack)[a + 1])",
     "line": 2539
    },
    {
     "code": "c == 0",
     "line": 2594
    },
    {
     "code": "len > pre + post",
     "line": 2625
    },
    {
     "code": "idx+pre<len",
     "line": 2635
    },
    {
     "code": "idx < post",
     "line": 2638
    },
    {
     "code": "i<lim",
     "line": 2679
    },
    {
     "code": "i<lim",
     "line": 2693
    },
    {
     "code": "c == OP_L_METHOD",
     "line": 2722
    },
    {
     "code": "(pool[a].tt&IREP_TT_NFLAG)==0",
     "line": 2877
    },
    {
     "code": "mrb->exc->tt == MRB_TT_EXCEPTION",
     "line": 2930
    },
    {
     "code": "ci > mrb->c->cibase",
     "line": 2941
    },
    {
     "code": "ci->acc == CI_ACC_DIRECT",
     "line": 2941
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "mid = syms[b]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "syms[b]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "mid",
    "syms",
    "b"
   ],
   "osv_id": "ARVO-42501369",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_vm_exec"
  }
 },
 {
  "osv_id": "ARVO-42501420",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "s1",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/value_array.h",
    "line": 7,
    "size": null,
    "type": "mrb_value*"
   }
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
  "sites": [
   {
    "kind": "unknown",
    "line": 20,
    "fn": "value_move",
    "code": "*s1++ = *s2++ | *s1++ | s1++ | *s2++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "value_move",
    "file": "/src/mruby/src/value_array.h",
    "line": 20
   },
   "code": "*s1++ = *s2++ | *s1++ | s1++ | *s2++",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "value_move",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "s1 > s2 | s1 < s2 + n | s1 != s2",
   "guard_count": 3,
   "control_structures": "IF:9,IF:10,WHILE:14,ELSE:18,IF:18,WHILE:19,ELSE:23"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mrb_value*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "s1",
   "s2",
   "n"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/a3fe04eda2b68b73486e5dbba2f7ebc6722f5e42/ARVO-42501420/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_a3fe04eda2b6.cpg",
   "testcase_size": 11
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
   "dedup_token": "value_move--mrb_ary_splice--mrb_ary_aset"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 7,
    "type": "mrb_value*"
   },
   "entity_name_cpg": "s1",
   "func_lines": [
    6,
    26
   ],
   "func_params": {
    "names": [
     "s1",
     "s2",
     "n"
    ],
    "types": [
     "mrb_value*",
     "mrb_value*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "n == 0",
     "line": 9
    },
    {
     "code": "s1 > s2",
     "line": 10
    },
    {
     "code": "s1 < s2 + n",
     "line": 10
    },
    {
     "code": "n-- > 0",
     "line": 14
    },
    {
     "code": "s1 != s2",
     "line": 18
    },
    {
     "code": "n-- > 0",
     "line": 19
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "*s1++ = *s2++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*s1++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "s1++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "*s2++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "s2++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "s1",
    "s2"
   ],
   "osv_id": "ARVO-42501420",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "value_move"
  }
 },
 {
  "osv_id": "ARVO-42501431",
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
    "line": 943,
    "fn": "parse_via_param",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_via_param",
    "file": "/src/kamailio/src/core/parser/parse_via.c",
    "line": 943
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "parse_via_param",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501431/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "testcase_size": 154
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "parse_via_param--parse_via--get_hdr_field"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "parse_via_param"
  }
 },
 {
  "osv_id": "ARVO-42501519",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "pv_cur_pic_addr0",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "line": 209,
    "size": null,
    "type": "void*"
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
    "line": 222,
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "line": 222
   },
   "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_fill_bs1_16x16mb_pslice",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "pv_cur_pic_addr0 != pv_nbr_pic_addr0 | pv_cur_pic_addr0 != pv_nbr_pic_addr0",
   "guard_count": 2,
   "control_structures": "FOR:228,IF:235,FOR:270,IF:277"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ps_cur_mv_pred",
   "ppv_map_ref_idx_to_poc"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42501519/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "testcase_size": 82
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
   "dedup_token": "ih264d_fill_bs1_16x16mb_pslice--ih264d_compute_bs_non_mbaff_thread--ih264d_recon_deblk_slice"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0]]",
     "line": 222
    }
   ],
   "entity_decl": {
    "line": 209,
    "type": "void*"
   },
   "entity_name_cpg": "pv_cur_pic_addr0",
   "func_lines": [
    198,
    312
   ],
   "func_params": {
    "names": [
     "ps_cur_mv_pred",
     "ps_top_mv_pred",
     "ppv_map_ref_idx_to_poc",
     "pu4_bs_table",
     "ps_leftmost_mv_pred",
     "ps_left_addr",
     "u4_pic_addrress",
     "i4_ver_mvlimit"
    ],
    "types": [
     "mv_pred_t*",
     "mv_pred_t*",
     "void**",
     "UWORD32*",
     "mv_pred_t*",
     "neighbouradd_t*",
     "void**",
     "WORD32"
    ]
   },
   "guards": [
    {
     "code": "i < 4",
     "line": 228
    },
    {
     "code": "((i2_p_mv0 - i2_q_mv0)) < 0",
     "line": 255
    },
    {
     "code": "((i2_p_mv1 - i2_q_mv1)) < 0",
     "line": 256
    },
    {
     "code": "pv_cur_pic_addr0 != pv_nbr_pic_addr0",
     "line": 258
    },
    {
     "code": "pv_cur_pic_addr1 != pv_nbr_pic_addr1",
     "line": 259
    },
    {
     "code": "i < 4",
     "line": 270
    },
    {
     "code": "((i2_p_mv0 - i2_q_mv0)) < 0",
     "line": 297
    },
    {
     "code": "((i2_p_mv1 - i2_q_mv1)) < 0",
     "line": 299
    },
    {
     "code": "pv_cur_pic_addr0 != pv_nbr_pic_addr0",
     "line": 302
    },
    {
     "code": "pv_cur_pic_addr1 != pv_nbr_pic_addr1",
     "line": 303
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0]]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0]]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "ps_cur_mv_pred->i1_ref_frame[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "ps_cur_mv_pred->i1_ref_frame",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pv_cur_pic_addr0",
    "ppv_map_ref_idx_to_poc_l0",
    "ps_cur_mv_pred"
   ],
   "osv_id": "ARVO-42501519",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_fill_bs1_16x16mb_pslice"
  }
 },
 {
  "osv_id": "ARVO-42502085",
  "project": "file",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "o4",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/file/src/cdf.c",
    "line": 978,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "calloc",
   "site": {
    "fn": "cdf_calloc",
    "file": "/src/file/src/cdf.c",
    "line": 121
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1092,
    "fn": "cdf_read_property_info",
    "code": "DPRINTF((\"o=%\" SIZE_T_FORMAT \"u l=%d(%\"",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "cdf_read_property_info",
    "file": "/src/file/src/cdf.c",
    "line": 1092
   },
   "code": "DPRINTF((\"o=%\" SIZE_T_FORMAT \"u l=%d(%\"",
   "access": {
    "dir": "READ",
    "width": 8425,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cdf_read_property_info",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "inp == NULL | i < sh.sh_properties | left < sizeof(uint32_t)",
   "guard_count": 8,
   "control_structures": "IF:981,GOTO:983,IF:987,GOTO:988,IF:990,GOTO:992,IF:995,GOTO:996,IF:1001,GOTO:1002,IF:1004,GOTO:1005"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "offs"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/a9c8d2a9493c4e0cd201db57801f3502e65c686c/ARVO-42502085/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/file_a9c8d2a9493c.cpg",
   "testcase_size": 11264
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
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--__interceptor_vprintf--printf"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "o4 = slen * sizeof(uint32_t)",
     "line": 1041
    },
    {
     "code": "o4 = slen * sizeof(uint32_t)",
     "line": 1101
    }
   ],
   "entity_decl": {
    "line": 978,
    "type": "size_t"
   },
   "entity_name_cpg": "o4",
   "func_lines": [
    971,
    1125
   ],
   "func_params": {
    "names": [
     "sst",
     "h",
     "offs",
     "info",
     "count",
     "maxcount"
    ],
    "types": [
     "cdf_stream_t*",
     "cdf_header_t*",
     "uint32_t",
     "cdf_property_info_t**",
     "size_t*",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "offs > UINT32_MAX / 4",
     "line": 981
    },
    {
     "code": "cdf_check_stream_offset(sst, h, shp, sizeof(*shp), __LINE__) == -1",
     "line": 987
    },
    {
     "code": "cdf_bo.u == ((uint32_t)(0x01020304))",
     "line": 989
    },
    {
     "code": "sh.sh_len > CDF_SHLEN_LIMIT",
     "line": 990
    },
    {
     "code": "cdf_check_stream_offset(sst, h, shp, sh.sh_len, __LINE__) == -1",
     "line": 995
    },
    {
     "code": "cdf_bo.u == ((uint32_t)(0x01020304))",
     "line": 998
    },
    {
     "code": "sh.sh_properties > CDF_PROP_LIMIT",
     "line": 1001
    },
    {
     "code": "inp == NULL",
     "line": 1004
    },
    {
     "code": "cdf_check_stream_offset(sst, h, e, 0, __LINE__) == -1",
     "line": 1010
    },
    {
     "code": "i < sh.sh_properties",
     "line": 1013
    },
    {
     "code": "(q = cdf_get_property_info_pos(sst, h, p, e, i)) == NULL",
     "line": 1014
    },
    {
     "code": "left < sizeof(uint32_t)",
     "line": 1018
    },
    {
     "code": "left < sizeof(uint32_t) * 2",
     "line": 1026
    },
    {
     "code": "nelements > CDF_ELEMENT_LIMIT",
     "line": 1031
    },
    {
     "code": "nelements == 0",
     "line": 1031
    },
    {
     "code": "nelements > 1",
     "line": 1068
    },
    {
     "code": "inp == NULL",
     "line": 1071
    },
    {
     "code": "j < nelements",
     "line": 1075
    },
    {
     "code": "i < sh.sh_properties",
     "line": 1075
    },
    {
     "code": "o4 + sizeof(uint32_t) > left",
     "line": 1080
    },
    {
     "code": "o4 + l > left",
     "line": 1085
    }
   ],
   "line_call_count": 15,
   "line_calls": [
    {
     "code": "DPRINTF((\"o=%\" SIZE_T_FORMAT \"u l=%d(%\"",
     "name": "DPRINTF",
     "nargs": null
    },
    {
     "code": "printf(\"o=%zu l=%d(%zu), t=%zu s=%s\\n\", o4, l, (((l) + (sizeof (l)) - 1) & ~((sizeof (l)) - 1)), left, inp[i].pi_val._pi_str.s_buf), fflush(stdout)",
     "name": "<operator>.expressionList",
     "nargs": 2
    },
    {
     "code": "printf(\"o=%zu l=%d(%zu), t=%zu s=%s\\n\", o4, l, (((l) + (sizeof (l)) - 1) & ~((sizeof (l)) - 1)), left, inp[i].pi_val._pi_str.s_buf)",
     "name": "printf",
     "nargs": 6
    },
    {
     "code": "((l) + (sizeof (l)) - 1) & ~((sizeof (l)) - 1)",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(l) + (sizeof (l)) - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "(l) + (sizeof (l))",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "sizeof (l)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "~((sizeof (l)) - 1)",
     "name": "<operator>.not",
     "nargs": 1
    },
    {
     "code": "(sizeof (l)) - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "sizeof (l)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "inp[i].pi_val._pi_str.s_buf",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "inp[i].pi_val._pi_str",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "inp[i].pi_val",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "inp[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "fflush(stdout)",
     "name": "fflush",
     "nargs": 1
    }
   ],
   "line_ids": [
    "o4",
    "l",
    "left",
    "inp",
    "i",
    "stdout"
   ],
   "osv_id": "ARVO-42502085",
   "sites": [
    {
     "args": "*info",
     "callee": "free",
     "code": "free(*info)",
     "line": 1119
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "cdf_read_property_info"
  }
 },
 {
  "osv_id": "ARVO-42502435",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "uint32_t",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 114,
    "fn": "operator unsigned short",
    "code": "{HB_TAG ('h','n','g','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TR | HB_TAG ('h','n','g','l') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('n') & 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "operator unsigned short",
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "line": 114
   },
   "code": "{HB_TAG ('h','n','g','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TR | HB_TAG ('h','n','g','l') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('n') & 0",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<global>",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:207,IF:214,IF:249,IF:252,IF:260,IF:263,FOR:276,IF:277,IF:321"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/9247d24d7f41f820d7ea79089b482410b927edc8/ARVO-42502435/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_9247d24d7f41.cpg",
   "testcase_size": 919
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "operator unsigned short--operator unsigned int--is_null"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "uint32_t",
   "func_lines": [
    1,
    430
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [
    {
     "code": "i < count",
     "line": 276
    },
    {
     "code": "info[i].codepoint == AAT::DELETED_GLYPH",
     "line": 277
    },
    {
     "code": "info->codepoint == AAT::DELETED_GLYPH",
     "line": 284
    }
   ],
   "line_call_count": 17,
   "line_calls": [
    {
     "code": "{HB_TAG ('h','n','g','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TRANSLITERATION,         HB_AAT_LAYOUT_FEATURE_SELECTOR_HANJA_TO_HANGUL,                HB_AAT_LAYOUT_FEATURE_SELECTOR_NO_TRANSLITERATION}",
     "name": "<operator>.arrayInitializer",
     "nargs": 4
    },
    {
     "code": "HB_TAG ('h','n','g','l')",
     "name": "HB_TAG",
     "nargs": 4
    },
    {
     "code": "(hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.cast",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(((uint32_t)('h') & 0xFF) << 24) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "((uint32_t)('h') & 0xFF) << 24",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('h') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('h')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "((uint32_t)('n') & 0xFF) << 16",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('n') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('n')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "((uint32_t)('g') & 0xFF) << 8",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('g') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('g')",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('l') & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(uint32_t)('l')",
     "name": "<operator>()",
     "nargs": 2
    }
   ],
   "line_ids": [
    "uint32_t",
    "HB_AAT_LAYOUT_FEATURE_TYPE_TRANSLITERATION",
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_HANJA_TO_HANGUL",
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_NO_TRANSLITERATION"
   ],
   "osv_id": "ARVO-42502435",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "operator unsigned short"
  }
 },
 {
  "osv_id": "ARVO-42502450",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 488,
    "fn": "embed<OT::MathValueRecord>",
    "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON\t\t= 4",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "embed<OT::MathValueRecord>",
    "file": "/src/harfbuzz/src/hb-serialize.hh",
    "line": 488
   },
   "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON\t\t= 4",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<clinit>",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/9247d24d7f41f820d7ea79089b482410b927edc8/ARVO-42502450/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_9247d24d7f41.cpg",
   "testcase_size": 982
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "embed<OT::MathValueRecord>--OT::MathValueRecord::copy(hb_serialize_context_t*, void const*) const--_copy<OT::MathValueRecord, const OT::MathGlyphAssembly *>"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON\t\t= 4",
     "line": 488
    }
   ],
   "entity_name_cpg": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON",
   "func_lines": [
    391,
    -1
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON\t\t= 4",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON"
   ],
   "osv_id": "ARVO-42502450",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "embed<OT::MathValueRecord>"
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