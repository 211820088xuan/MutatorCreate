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
heap-use-after-free

## 该类型的机制背景
UAF 的必要条件链：
- N1 对象是堆分配
- N2 存在 free(p) 调用
- N3 p 在 free 之后被解引用（执行顺序）
- N4 free 与解引用之间 p 未被重新赋值
- N5 free 与解引用之间 p 未重新 malloc
- N6 free 的实参是 p 本身（非 p+off）
- N7 解引用对象与 free 对象是同一对象（含别名）
- N8 free 与解引用在同一可达路径上
- N9 p 解引用时未被置空
- N10 解引用发生在 free 生效后（非同一语句）

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "osv_id": "ARVO-372547409",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cur",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/valid.c",
    "line": 5952,
    "size": null,
    "type": "xmlNsPtr"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "xmlFuzzMalloc",
    "file": "/src/libxml2/fuzz/fuzz.c",
    "line": 81
   },
   "size_expr": null,
   "size_bytes": 64,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 1625,
    "fn": "xmlFreeAttribute",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 5992,
    "fn": "xmlValidateOneElement",
    "code": "xmlStrEqual(cur->prefix, prefix) | cur->prefix",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlValidateOneElement",
    "file": "/src/libxml2/valid.c",
    "line": 5992
   },
   "code": "xmlStrEqual(cur->prefix, prefix) | cur->prefix",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 64
   }
  },
  "context": {
   "fn": "xmlSearchNsSafe",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "prefix != NULL | cur == NULL | cur != NULL",
   "guard_count": 6,
   "control_structures": "IF:5957,IF:5964,IF:5966,WHILE:5972,IF:5974,WHILE:5980,WHILE:5982,IF:5983,IF:5989,IF:5991,IF:6006,IF:6008"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlNsPtr",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "node",
   "prefix",
   "out"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/d4d1f3f33d6d4a5e31511281637a857944946e65/ARVO-372547409/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_d4d1f3f33d6d.cpg",
   "testcase_size": 26
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 64,
   "loc_offset": 44,
   "loc_kind": "region",
   "dedup_token": "xmlValidateOneElement--xmlValidateElement--LLVMFuzzerTestOneInput",
   "region_size": 64
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cur = xmlTreeEnsureXMLDecl(doc)",
     "line": 5965
    },
    {
     "code": "cur = node->nsDef",
     "line": 5981
    },
    {
     "code": "cur = cur->next",
     "line": 5987
    },
    {
     "code": "cur = node->ns",
     "line": 5990
    },
    {
     "code": "cur = xmlNewXmlNs()",
     "line": 6007
    },
    {
     "code": "cur->next = parent->nsDef",
     "line": 6010
    }
   ],
   "entity_decl": {
    "line": 5952,
    "type": "xmlNsPtr"
   },
   "entity_name_cpg": "cur",
   "func_lines": [
    5949,
    6016
   ],
   "func_params": {
    "names": [
     "node",
     "prefix",
     "out"
    ],
    "types": [
     "xmlNodePtr",
     "xmlChar*",
     "xmlNsPtr*"
    ]
   },
   "guards": [
    {
     "code": "out == NULL",
     "line": 5957
    },
    {
     "code": "node == NULL",
     "line": 5958
    },
    {
     "code": "node->type == XML_NAMESPACE_DECL",
     "line": 5958
    },
    {
     "code": "doc != NULL",
     "line": 5964
    },
    {
     "code": "prefix != NULL",
     "line": 5964
    },
    {
     "code": "prefix[0] == 'x'",
     "line": 5964
    },
    {
     "code": "prefix[1] == 'm'",
     "line": 5964
    },
    {
     "code": "prefix[2] == 'l'",
     "line": 5964
    },
    {
     "code": "prefix[3] == 0",
     "line": 5964
    },
    {
     "code": "cur == NULL",
     "line": 5966
    },
    {
     "code": "node->type != XML_ELEMENT_NODE",
     "line": 5972
    },
    {
     "code": "node == NULL",
     "line": 5974
    },
    {
     "code": "node != NULL",
     "line": 5980
    },
    {
     "code": "node->type == XML_ELEMENT_NODE",
     "line": 5980
    },
    {
     "code": "cur != NULL",
     "line": 5982
    },
    {
     "code": "orig != node",
     "line": 5989
    },
    {
     "code": "cur != NULL",
     "line": 5991
    },
    {
     "code": "doc == NULL",
     "line": 6006
    },
    {
     "code": "prefix != NULL",
     "line": 6006
    },
    {
     "code": "prefix[0] == 'x'",
     "line": 6006
    },
    {
     "code": "prefix[1] == 'm'",
     "line": 6006
    },
    {
     "code": "prefix[2] == 'l'",
     "line": 6006
    },
    {
     "code": "prefix[3] == 0",
     "line": 6006
    },
    {
     "code": "cur == NULL",
     "line": 6008
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "xmlStrEqual(cur->prefix, prefix)",
     "name": "xmlStrEqual",
     "nargs": 2
    },
    {
     "code": "cur->prefix",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cur",
    "prefix"
   ],
   "osv_id": "ARVO-372547409",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xmlFreeAttribute",
   "use_fn": "xmlValidateOneElement"
  }
 },
 {
  "osv_id": "ARVO-396777457",
  "project": "net-snmp",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 575,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "af_get_null_terminated",
    "file": "/src/net-snmp/testing/fuzzing/ada_fuzz_header.h",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": 76,
   "cross_function": true,
   "size_expr_cpg": "buf ;; buf_len",
   "size_expr_cpg_callee": "snmp_realloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 56,
    "fn": "af_gb_cleanup",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 581,
    "fn": "netsnmp_hex_to_binary",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "netsnmp_hex_to_binary",
    "file": "/src/net-snmp/snmplib/tools.c",
    "line": 581
   },
   "code": "(*cp == '0') && ((*(cp + 1) == 'x') ",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 76
   }
  },
  "context": {
   "fn": "netsnmp_hex_to_binary",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-396777457/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "testcase_size": 328
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 76,
   "loc_offset": 23,
   "loc_kind": "region",
   "dedup_token": "netsnmp_hex_to_binary--snmpv3_parse_arg--netsnmp_parse_args",
   "region_size": 76
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*cp = hex",
     "line": 575
    }
   ],
   "entity_decl": {
    "line": 575,
    "type": "char*"
   },
   "entity_name_cpg": "cp",
   "func_lines": [
    570,
    617
   ],
   "func_params": {
    "names": [
     "buf",
     "buf_len",
     "offset",
     "allow_realloc",
     "hex",
     "delim"
    ],
    "types": [
     "u_char**",
     "size_t*",
     "size_t*",
     "int",
     "char*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "buf == NULL",
     "line": 577
    },
    {
     "code": "buf_len == NULL",
     "line": 577
    },
    {
     "code": "offset == NULL",
     "line": 577
    },
    {
     "code": "hex == NULL",
     "line": 577
    },
    {
     "code": "*cp == '0'",
     "line": 581
    },
    {
     "code": "*(cp + 1) == 'x'",
     "line": 581
    },
    {
     "code": "*(cp + 1) == 'X'",
     "line": 581
    },
    {
     "code": "*cp != '\\0'",
     "line": 585
    },
    {
     "code": "NULL != delim",
     "line": 588
    },
    {
     "code": "NULL != strchr(delim, *cp)",
     "line": 588
    },
    {
     "code": "sscanf(cp, \"%2x\", &subid) == 0",
     "line": 594
    },
    {
     "code": "*++cp == '\\0'",
     "line": 607
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "(*cp == '0') && ((*(cp + 1) == 'x') ",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "*cp == '0'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*cp",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(*(cp + 1) == 'x') ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "*(cp + 1) == 'x'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*(cp + 1)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "cp + 1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "*(cp + 1) == 'X'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*(cp + 1)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "cp + 1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cp"
   ],
   "osv_id": "ARVO-396777457",
   "sites": [
    {
     "args": "buf ;; buf_len",
     "callee": "snmp_realloc",
     "code": "snmp_realloc(buf, buf_len)",
     "line": 602
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "af_gb_cleanup",
   "use_fn": "netsnmp_hex_to_binary"
  }
 },
 {
  "osv_id": "ARVO-42470878",
  "project": "openvswitch",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "actions",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2161,
    "type": "ofpbuf*",
    "size": null
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "xrealloc",
    "file": "/src/openvswitch/lib/util.c",
    "line": 134
   },
   "size_expr": null,
   "size_bytes": 64,
   "cross_function": true,
   "size_expr_cpg": "1024 / sizeof(struct nlattr)",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 134,
    "fn": "xrealloc",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 2246,
    "fn": "parse_odp_action",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "parse_odp_action",
    "file": "/src/openvswitch/lib/odp-util.c",
    "line": 2246
   },
   "code": "ofpbuf_put_zeros(actions, NLA_ALIGN(key->nla_len) -",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": 64
   }
  },
  "context": {
   "fn": "parse_odp_action",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openvswitch/address/bc9bbc4ea2645e5bbb3c02d986f26fdc83283d72/ARVO-42470878/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_bc9bbc4ea264.cpg",
   "testcase_size": 12
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 64,
   "loc_offset": 4,
   "loc_kind": "region",
   "dedup_token": "parse_odp_action--odp_actions_from_string--parse_actions",
   "region_size": 64
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 2161,
    "type": "ofpbuf*"
   },
   "entity_name_cpg": "actions",
   "func_lines": [
    2159,
    2403
   ],
   "func_params": {
    "names": [
     "s",
     "port_names",
     "actions"
    ],
    "types": [
     "char*",
     "simap*",
     "ofpbuf*"
    ]
   },
   "guards": [
    {
     "code": "retval < 0",
     "line": 2222
    },
    {
     "code": "s[retval + 4] != ')'",
     "line": 2226
    },
    {
     "code": "size == nl_attr_get_size(key)",
     "line": 2235
    },
    {
     "code": "sscanf(s, \"meter(%lli)%n\", &meter_id, &n) > 0",
     "line": 2294
    },
    {
     "code": "n > 0",
     "line": 2294
    },
    {
     "code": "retval < 0",
     "line": 2319
    },
    {
     "code": "s[n + 1] == ')'",
     "line": 2326
    },
    {
     "code": "retval < 0",
     "line": 2337
    },
    {
     "code": "retval < 0",
     "line": 2349
    },
    {
     "code": "n > 0",
     "line": 2395
    },
    {
     "code": "n < 0",
     "line": 2398
    }
   ],
   "line_call_count": 9,
   "line_calls": [
    {
     "code": "ofpbuf_put_zeros(actions, NLA_ALIGN(key->nla_len) -",
     "name": "ofpbuf_put_zeros",
     "nargs": null
    },
    {
     "code": "NLA_ALIGN(key->nla_len) -",
     "name": "<operator>.subtraction",
     "nargs": null
    },
    {
     "code": "NLA_ALIGN(key->nla_len)",
     "name": "NLA_ALIGN",
     "nargs": 1
    },
    {
     "code": "key->nla_len",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(((key->nla_len) + ((4) - 1)) / (4)) * (4)",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "((key->nla_len) + ((4) - 1)) / (4)",
     "name": "<operator>.division",
     "nargs": 2
    },
    {
     "code": "(key->nla_len) + ((4) - 1)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "key->nla_len",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(4) - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "actions",
    "key"
   ],
   "osv_id": "ARVO-42470878",
   "sites": [
    {
     "args": "1024 / sizeof(struct nlattr)",
     "callee": "<operator>.alloc",
     "code": "mask[1024 / sizeof(struct nlattr)]",
     "line": 2215
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xrealloc",
   "use_fn": "parse_odp_action"
  }
 },
 {
  "osv_id": "ARVO-42471500",
  "project": "radare2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "r_core_task_new",
    "file": "/src/radare2/libr/core/task.c",
    "line": 192
   },
   "size_expr": null,
   "size_bytes": 104,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 248,
    "fn": "r_core_task_decref",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 250,
    "fn": "r_core_task_decref",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "r_core_task_decref",
    "file": "/src/radare2/libr/core/task.c",
    "line": 250
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 104
   }
  },
  "context": {
   "fn": "r_core_task_decref",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/radare2/address/8f03b2a42fccf6fb7c3d78ca1adeea0bf9d78757/ARVO-42471500/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_8f03b2a42fcc.cpg",
   "testcase_size": 0
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 104,
   "loc_offset": 32,
   "loc_kind": "region",
   "dedup_token": "r_core_task_decref--r_list_delete--r_list_purge",
   "region_size": 104
  },
  "deep": {
   "osv_id": "ARVO-42471500"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": false,
   "free_fn": "r_core_task_decref",
   "use_fn": "r_core_task_decref"
  }
 },
 {
  "osv_id": "ARVO-42473818",
  "project": "openh264",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "uint32_t",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "line": 72
   },
   "size_expr": null,
   "size_bytes": 499,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 176,
    "fn": "WelsDec::ResetRefPicReferences(WelsDec::TagWelsDecoderContext* const&, WelsDec::SPicture* const&)",
    "code": "WELS_THREAD_ERROR_GENERAL | (uint32_t)(-1) | -1",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 234,
    "fn": "WelsDec::DecreasePicBuff(WelsDec::TagWelsDecoderContext*, WelsDec::TagPicBuff**, int, int, int, int)",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::ResetRefPicReferences(WelsDec::TagWelsDecoderContext* const&, WelsDec::SPicture* const&)",
    "file": "/src/openh264/codec/decoder/core/src/decoder.cpp",
    "line": 176
   },
   "code": "WELS_THREAD_ERROR_GENERAL | (uint32_t)(-1) | -1",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 499
   }
  },
  "context": {
   "fn": "Init",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:170,FOR:174,IF:175,IF:180"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/be82ccf42fc044ae1ea0792837a9415eaf535002/ARVO-42473818/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_be82ccf42fc0.cpg",
   "testcase_size": 70
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 499,
   "loc_offset": 216,
   "loc_kind": "region",
   "dedup_token": "WelsDec::ResetRefPicReferences(WelsDec::TagWelsDecoderContext* const&, WelsDec::SPicture* const&)--WelsDec::DecreasePicBuff(WelsDec::TagWelsDecoderContext*, Wel",
   "region_size": 499
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "uint32_t",
   "func_lines": [
    162,
    185
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "WelsCommon.CWelsThreadPool"
    ]
   },
   "guards": [
    {
     "code": "NULL == m_cWaitedTasks",
     "line": 170
    },
    {
     "code": "NULL == m_cIdleThreads",
     "line": 170
    },
    {
     "code": "NULL == m_cBusyThreads",
     "line": 170
    },
    {
     "code": "i < m_iMaxThreadNum",
     "line": 174
    },
    {
     "code": "WELS_THREAD_ERROR_OK != CreateIdleThread()",
     "line": 175
    },
    {
     "code": "WELS_THREAD_ERROR_OK != Start()",
     "line": 180
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "WELS_THREAD_ERROR_GENERAL",
     "name": "WELS_THREAD_ERROR_GENERAL",
     "nargs": 0
    },
    {
     "code": "(uint32_t)(-1)",
     "name": "<operator>()",
     "nargs": 2
    },
    {
     "code": "-1",
     "name": "<operator>.minus",
     "nargs": 1
    }
   ],
   "line_ids": [
    "uint32_t"
   ],
   "osv_id": "ARVO-42473818",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "WelsDec::DecreasePicBuff(WelsDec::TagWelsDecoderContext*, WelsDec::TagPicBuff**, int, int, int, int)",
   "use_fn": "WelsDec::ResetRefPicReferences(WelsDec::TagWelsDecoderContext* const&, WelsDec::SPicture* const&)"
  }
 },
 {
  "osv_id": "ARVO-42474100",
  "project": "radare2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "sdb_new",
    "file": "/src/radare2/shlr/sdb/src/sdb.c",
    "line": 56
   },
   "size_expr": null,
   "size_bytes": 11568,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 217,
    "fn": "sdb_free",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 223,
    "fn": "sdb_free",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "sdb_free",
    "file": "/src/radare2/shlr/sdb/src/sdb.c",
    "line": 217
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 11568
   }
  },
  "context": {
   "fn": "sdb_free",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/radare2/address/0c9ccb45de8a22700fe51bcda0d4baa99f09cfe9/ARVO-42474100/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_0c9ccb45de8a.cpg",
   "testcase_size": 4
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 11568,
   "loc_offset": 11424,
   "loc_kind": "region",
   "dedup_token": "sdb_free--ns_free--sdb_ns_free",
   "region_size": 11568
  },
  "deep": {
   "osv_id": "ARVO-42474100"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": false,
   "free_fn": "sdb_free",
   "use_fn": "sdb_free"
  }
 },
 {
  "osv_id": "ARVO-42474468",
  "project": "openh264",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "pSVCEncoder",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "line": 1113,
    "size": null,
    "type": "ISVCEncoder*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "line": 72
   },
   "size_expr": null,
   "size_bytes": 499,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 113,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1113,
    "fn": "WelsDec::MapColToList0(WelsDec::TagWelsDecoderContext*&, signed char const&, int const&)",
    "code": "* pSVCEncoder = NULL",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::MapColToList0(WelsDec::TagWelsDecoderContext*&, signed char const&, int const&)",
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "line": 1113
   },
   "code": "* pSVCEncoder = NULL",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 499
   }
  },
  "context": {
   "fn": "main",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1128,GOTO:1130,IF:1133,GOTO:1134,ELSE:1135,IF:1136,IF:1137,IF:1139,GOTO:1140,ELSE:1141,IF:1141,ELSE:1143"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ISVCEncoder*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/72974a4fcc65c595bacb3d2c12d418d680cb063d/ARVO-42474468/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_72974a4fcc65.cpg",
   "testcase_size": 80
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 499,
   "loc_offset": 112,
   "loc_kind": "region",
   "dedup_token": "WelsDec::MapColToList0(WelsDec::TagWelsDecoderContext*&, signed char const&, int const&)--WelsDec::PredBDirectTemporal(WelsDec::TagWelsDecoderContext*, short (*",
   "region_size": 499
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* pSVCEncoder = NULL",
     "line": 1113
    }
   ],
   "entity_decl": {
    "line": 1113,
    "type": "ISVCEncoder*"
   },
   "entity_name_cpg": "pSVCEncoder",
   "func_lines": [
    1110,
    1161
   ],
   "func_params": {
    "names": [
     "argc",
     "argv"
    ],
    "types": [
     "int",
     "char**"
    ]
   },
   "guards": [
    {
     "code": "argc < 2",
     "line": 1133
    },
    {
     "code": "argc > 2",
     "line": 1137
    },
    {
     "code": "iRet != 0",
     "line": 1139
    },
    {
     "code": "argc == 2",
     "line": 1141
    },
    {
     "code": "iRet > 0",
     "line": 1149
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "* pSVCEncoder = NULL",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pSVCEncoder",
    "NULL"
   ],
   "osv_id": "ARVO-42474468",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "WelsCommon::WelsFree(void*, char const*)",
   "use_fn": "WelsDec::MapColToList0(WelsDec::TagWelsDecoderContext*&, signed char const&, int const&)"
  }
 },
 {
  "osv_id": "ARVO-42474969",
  "project": "open62541",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "s",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 135,
    "size": null,
    "type": "UA_String*"
   }
  },
  "alloc": {
   "api": "calloc",
   "site": {
    "fn": "UA_memoryManager_calloc",
    "file": "/src/open62541/tests/fuzz/custom_memory_manager.c",
    "line": 142
   },
   "size_expr": null,
   "size_bytes": 144,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 136,
    "fn": "String_clear",
    "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 196,
    "fn": "deleteMembers_default",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "String_clear",
    "file": "/src/open62541/src/ua_types.c",
    "line": 136
   },
   "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 144
   }
  },
  "context": {
   "fn": "String_clear",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "UA_String*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "s"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/4e38d391dde9e5d74463f0a17de245f8917675ca/ARVO-42474969/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_4e38d391dde9.cpg",
   "testcase_size": 4
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 144,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "String_clear--clearStructure--UA_clear",
   "region_size": 144
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 135,
    "type": "UA_String*"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    134,
    137
   ],
   "func_params": {
    "names": [
     "s",
     "_"
    ],
    "types": [
     "UA_String*",
     "UA_DataType*"
    ]
   },
   "guards": [],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_BYTE])",
     "name": "UA_Array_delete",
     "nargs": 3
    },
    {
     "code": "s->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "s->length",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "&UA_TYPES[UA_TYPES_BYTE]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "UA_TYPES[UA_TYPES_BYTE]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "s",
    "UA_TYPES",
    "UA_TYPES_BYTE"
   ],
   "osv_id": "ARVO-42474969",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "deleteMembers_default",
   "use_fn": "String_clear"
  }
 },
 {
  "osv_id": "ARVO-42475763",
  "project": "radare2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "r_num_tail",
    "file": "/src/radare2/libr/util/unum.c",
    "line": 731
   },
   "size_expr": null,
   "size_bytes": 14,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 216,
    "fn": "cin_get",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 742,
    "fn": "r_num_tail",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "cin_get",
    "file": "/src/radare2/libr/util/calc.c",
    "line": 216
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 14
   }
  },
  "context": {
   "fn": "cin_get",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/radare2/address/ade7df45e8bd1c64e5d646d5aaf8943302205947/ARVO-42475763/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_ade7df45e8bd.cpg",
   "testcase_size": 3995
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 14,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "cin_get--get_token--prim",
   "region_size": 14
  },
  "deep": {
   "osv_id": "ARVO-42475763"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "r_num_tail",
   "use_fn": "cin_get"
  }
 },
 {
  "osv_id": "ARVO-42476708",
  "project": "libspng",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "keyword_nul",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1321,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "spng_set_png_stream",
    "file": "/src/libspng/build/../spng.c",
    "line": 2382
   },
   "size_expr": null,
   "size_bytes": 8192,
   "cross_function": true,
   "size_expr_cpg": "8",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 292,
    "fn": "read_data",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1321,
    "fn": "read_chunks_before_idat",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_chunks_before_idat",
    "file": "/src/libspng/spng.c",
    "line": 1321
   },
   "code": "*keyword_nul = memchr(data, '\\0', keyword_len)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": 8192
   }
  },
  "context": {
   "fn": "read_chunks_before_idat",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libspng/address/9fcecef4100bfa40b3b2b106790a97af70096ae0/ARVO-42476708/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_9fcecef4100b.cpg",
   "testcase_size": 8472
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 8192,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "memchr--read_chunks_before_idat--get_ancillary",
   "region_size": 8192
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*keyword_nul = memchr(data, '\\0', keyword_len)",
     "line": 1321
    }
   ],
   "entity_decl": {
    "line": 1321,
    "type": "char*"
   },
   "entity_name_cpg": "keyword_nul",
   "func_lines": [
    984,
    1471
   ],
   "func_params": {
    "names": [
     "ctx"
    ],
    "types": [
     "spng_ctx*"
    ]
   },
   "guards": [
    {
     "code": "ctx == NULL",
     "line": 986
    },
    {
     "code": "ctx->data == NULL",
     "line": 987
    },
    {
     "code": "chunk.length != 13",
     "line": 1009
    },
    {
     "code": "(chunk.type[1] & (1 << 5)) != 0",
     "line": 1055
    },
    {
     "code": "chunk.length == 0",
     "line": 1061
    },
    {
     "code": "chunk.length % 3 != 0",
     "line": 1062
    },
    {
     "code": "(chunk.length / 3) > 256",
     "line": 1063
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1065
    },
    {
     "code": "chunk.length / 3 > (1 << ctx->ihdr.bit_depth)",
     "line": 1067
    },
    {
     "code": "i < ctx->plte.n_entries",
     "line": 1073
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1090
    },
    {
     "code": "chunk.length != 32",
     "line": 1093
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1111
    },
    {
     "code": "chunk.length != 4",
     "line": 1114
    },
    {
     "code": "ctx->gama > png_u32max",
     "line": 1119
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1126
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1134
    },
    {
     "code": "ctx->ihdr.color_type == 0",
     "line": 1137
    },
    {
     "code": "chunk.length != 1",
     "line": 1139
    },
    {
     "code": "ctx->ihdr.color_type == 2",
     "line": 1143
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1143
    },
    {
     "code": "chunk.length != 3",
     "line": 1145
    },
    {
     "code": "ctx->ihdr.color_type == 4",
     "line": 1151
    },
    {
     "code": "chunk.length != 2",
     "line": 1153
    },
    {
     "code": "ctx->ihdr.color_type == 6",
     "line": 1158
    },
    {
     "code": "chunk.length != 4",
     "line": 1160
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1175
    },
    {
     "code": "chunk.length != 1",
     "line": 1178
    },
    {
     "code": "ctx->srgb_rendering_intent > 3",
     "line": 1182
    },
    {
     "code": "chunk.offset < ctx->plte_offset",
     "line": 1189
    },
    {
     "code": "ctx->ihdr.bit_depth < 16",
     "line": 1193
    },
    {
     "code": "ctx->ihdr.color_type == 0",
     "line": 1195
    },
    {
     "code": "ctx->ihdr.color_type == 4",
     "line": 1195
    },
    {
     "code": "chunk.length != 2",
     "line": 1197
    },
    {
     "code": "ctx->ihdr.color_type == 2",
     "line": 1201
    },
    {
     "code": "ctx->ihdr.color_type == 6",
     "line": 1201
    },
    {
     "code": "chunk.length != 6",
     "line": 1203
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1209
    },
    {
     "code": "chunk.length != 1",
     "line": 1211
    },
    {
     "code": "chunk.offset < ctx->plte_offset",
     "line": 1223
    },
    {
     "code": "ctx->ihdr.bit_depth < 16",
     "line": 1228
    },
    {
     "code": "ctx->ihdr.color_type == 0",
     "line": 1230
    },
    {
     "code": "chunk.length != 2",
     "line": 1232
    },
    {
     "code": "ctx->ihdr.color_type == 2",
     "line": 1236
    },
    {
     "code": "chunk.length != 6",
     "line": 1238
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1244
    },
    {
     "code": "chunk.length > ctx->plte.n_entries",
     "line": 1246
    },
    {
     "code": "k < chunk.length",
     "line": 1250
    },
    {
     "code": "chunk.offset < ctx->plte_offset",
     "line": 1264
    },
    {
     "code": "(chunk.length / 2) != (ctx->plte.n_entries)",
     "line": 1267
    },
    {
     "code": "k < (chunk.length / 2)",
     "line": 1270
    },
    {
     "code": "chunk.length != 9",
     "line": 1282
    },
    {
     "code": "ctx->splt_list == NULL",
     "line": 1304
    },
    {
     "code": "ctx->n_splt < 1",
     "line": 1309
    },
    {
     "code": "sizeof(struct spng_splt) > SIZE_MAX / ctx->n_splt",
     "line": 1310
    },
    {
     "code": "buf == NULL",
     "line": 1313
    },
    {
     "code": "chunk.length > 80",
     "line": 1320
    },
    {
     "code": "keyword_nul == NULL",
     "line": 1322
    },
    {
     "code": "(chunk.length - keyword_len - 1) ==  0",
     "line": 1330
    },
    {
     "code": "ctx->n_splt > 1",
     "line": 1334
    },
    {
     "code": "j < i",
     "line": 1337
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 16",
     "line": 1343
    },
    {
     "code": "(chunk.length - keyword_len - 2) % 10 != 0",
     "line": 1345
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 8",
     "line": 1348
    },
    {
     "code": "(chunk.length - keyword_len - 2) % 6 != 0",
     "line": 1350
    },
    {
     "code": "ctx->splt_list[i].n_entries == 0",
     "line": 1355
    },
    {
     "code": "sizeof(struct spng_splt_entry) > SIZE_MAX / ctx->splt_list[i].n_entries",
     "line": 1356
    },
    {
     "code": "ctx->splt_list[i].entries == NULL",
     "line": 1359
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 16",
     "line": 1364
    },
    {
     "code": "k < ctx->splt_list[i].n_entries",
     "line": 1366
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 8",
     "line": 1375
    },
    {
     "code": "k < ctx->splt_list[i].n_entries",
     "line": 1377
    },
    {
     "code": "chunk.length != 7",
     "line": 1399
    },
    {
     "code": "chunk.length != 9",
     "line": 1430
    },
    {
     "code": "exif.data == NULL",
     "line": 1452
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "*keyword_nul = memchr(data, '\\0', keyword_len)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "memchr(data, '\\0', keyword_len)",
     "name": "memchr",
     "nargs": 3
    }
   ],
   "line_ids": [
    "keyword_nul",
    "data",
    "keyword_len"
   ],
   "osv_id": "ARVO-42476708",
   "sites": [
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "signature[8] = { 137, 80, 78, 71, 13, 10, 26, 10 }",
     "line": 1003
    },
    {
     "args": "ctx ;; 1 ;; sizeof(struct spng_splt)",
     "callee": "spng__calloc",
     "code": "spng__calloc(ctx, 1, sizeof(struct spng_splt))",
     "line": 1303
    },
    {
     "args": "ctx ;; ctx->splt_list ;; ctx->n_splt * sizeof(struct spng_splt)",
     "callee": "spng__realloc",
     "code": "spng__realloc(ctx, ctx->splt_list, ctx->n_splt * sizeof(struct spng_splt))",
     "line": 1312
    },
    {
     "args": "ctx ;; sizeof(struct spng_splt_entry) * ctx->splt_list[i].n_entries",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, sizeof(struct spng_splt_entry) * ctx->splt_list[i].n_entries)",
     "line": 1358
    },
    {
     "args": "ctx ;; chunk.length",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, chunk.length)",
     "line": 1451
    },
    {
     "args": "ctx ;; exif.data",
     "callee": "spng__free",
     "code": "spng__free(ctx, exif.data)",
     "line": 1459
    },
    {
     "args": "ctx ;; exif.data",
     "callee": "spng__free",
     "code": "spng__free(ctx, exif.data)",
     "line": 1464
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "read_data",
   "use_fn": "read_chunks_before_idat"
  }
 },
 {
  "osv_id": "ARVO-42476741",
  "project": "libspng",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "exif",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1555,
    "type": "spng_exif",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "spng_set_png_stream",
    "file": "/src/libspng/build/../spng.c",
    "line": 2382
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "ctx ;; chunk.length",
   "size_expr_cpg_callee": "spng__malloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 292,
    "fn": "read_data",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1560,
    "fn": "read_chunks_after_idat",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_chunks_after_idat",
    "file": "/src/libspng/spng.c",
    "line": 1560
   },
   "code": "memcpy(exif.data, data, chunk.length)",
   "access": {
    "dir": "READ",
    "width": 8289,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "read_chunks_after_idat",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libspng/address/9fcecef4100bfa40b3b2b106790a97af70096ae0/ARVO-42476741/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_9fcecef4100b.cpg",
   "testcase_size": 8471
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "__asan_memcpy--read_chunks_after_idat--spng_decode_image"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "exif.data = spng__malloc(ctx, chunk.length)",
     "line": 1557
    },
    {
     "code": "exif.length = chunk.length",
     "line": 1561
    }
   ],
   "entity_decl": {
    "line": 1555,
    "type": "spng_exif"
   },
   "entity_name_cpg": "exif",
   "func_lines": [
    1473,
    1585
   ],
   "func_params": {
    "names": [
     "ctx"
    ],
    "types": [
     "spng_ctx*"
    ]
   },
   "guards": [
    {
     "code": "ctx == NULL",
     "line": 1475
    },
    {
     "code": "(chunk.type[1] & (1 << 5)) != 0",
     "line": 1501
    },
    {
     "code": "chunk.length != 7",
     "line": 1528
    },
    {
     "code": "exif.data == NULL",
     "line": 1558
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memcpy(exif.data, data, chunk.length)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "exif.data",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "chunk.length",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "exif",
    "data",
    "chunk"
   ],
   "osv_id": "ARVO-42476741",
   "sites": [
    {
     "args": "ctx ;; chunk.length",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, chunk.length)",
     "line": 1557
    },
    {
     "args": "ctx ;; exif.data",
     "callee": "spng__free",
     "code": "spng__free(ctx, exif.data)",
     "line": 1565
    },
    {
     "args": "ctx ;; exif.data",
     "callee": "spng__free",
     "code": "spng__free(ctx, exif.data)",
     "line": 1570
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "read_data",
   "use_fn": "read_chunks_after_idat"
  }
 },
 {
  "osv_id": "ARVO-42476946",
  "project": "libspng",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "exif",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1449,
    "type": "spng_exif",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "spng_set_png_stream",
    "file": "/src/libspng/build/../spng.c",
    "line": 2382
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "8",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 292,
    "fn": "read_data",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1454,
    "fn": "read_chunks_before_idat",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_chunks_before_idat",
    "file": "/src/libspng/spng.c",
    "line": 1454
   },
   "code": "memcpy(exif.data, data, chunk.length)",
   "access": {
    "dir": "READ",
    "width": 8224,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "read_chunks_before_idat",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libspng/address/9fcecef4100bfa40b3b2b106790a97af70096ae0/ARVO-42476946/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_9fcecef4100b.cpg",
   "testcase_size": 24604
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "__asan_memcpy--read_chunks_before_idat--get_ancillary"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "exif.data = spng__malloc(ctx, chunk.length)",
     "line": 1451
    },
    {
     "code": "exif.length = chunk.length",
     "line": 1455
    }
   ],
   "entity_decl": {
    "line": 1449,
    "type": "spng_exif"
   },
   "entity_name_cpg": "exif",
   "func_lines": [
    984,
    1471
   ],
   "func_params": {
    "names": [
     "ctx"
    ],
    "types": [
     "spng_ctx*"
    ]
   },
   "guards": [
    {
     "code": "ctx == NULL",
     "line": 986
    },
    {
     "code": "ctx->data == NULL",
     "line": 987
    },
    {
     "code": "chunk.length != 13",
     "line": 1009
    },
    {
     "code": "(chunk.type[1] & (1 << 5)) != 0",
     "line": 1055
    },
    {
     "code": "chunk.length == 0",
     "line": 1061
    },
    {
     "code": "chunk.length % 3 != 0",
     "line": 1062
    },
    {
     "code": "(chunk.length / 3) > 256",
     "line": 1063
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1065
    },
    {
     "code": "chunk.length / 3 > (1 << ctx->ihdr.bit_depth)",
     "line": 1067
    },
    {
     "code": "i < ctx->plte.n_entries",
     "line": 1073
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1090
    },
    {
     "code": "chunk.length != 32",
     "line": 1093
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1111
    },
    {
     "code": "chunk.length != 4",
     "line": 1114
    },
    {
     "code": "ctx->gama > png_u32max",
     "line": 1119
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1126
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1134
    },
    {
     "code": "ctx->ihdr.color_type == 0",
     "line": 1137
    },
    {
     "code": "chunk.length != 1",
     "line": 1139
    },
    {
     "code": "ctx->ihdr.color_type == 2",
     "line": 1143
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1143
    },
    {
     "code": "chunk.length != 3",
     "line": 1145
    },
    {
     "code": "ctx->ihdr.color_type == 4",
     "line": 1151
    },
    {
     "code": "chunk.length != 2",
     "line": 1153
    },
    {
     "code": "ctx->ihdr.color_type == 6",
     "line": 1158
    },
    {
     "code": "chunk.length != 4",
     "line": 1160
    },
    {
     "code": "chunk.offset > ctx->plte_offset",
     "line": 1175
    },
    {
     "code": "chunk.length != 1",
     "line": 1178
    },
    {
     "code": "ctx->srgb_rendering_intent > 3",
     "line": 1182
    },
    {
     "code": "chunk.offset < ctx->plte_offset",
     "line": 1189
    },
    {
     "code": "ctx->ihdr.bit_depth < 16",
     "line": 1193
    },
    {
     "code": "ctx->ihdr.color_type == 0",
     "line": 1195
    },
    {
     "code": "ctx->ihdr.color_type == 4",
     "line": 1195
    },
    {
     "code": "chunk.length != 2",
     "line": 1197
    },
    {
     "code": "ctx->ihdr.color_type == 2",
     "line": 1201
    },
    {
     "code": "ctx->ihdr.color_type == 6",
     "line": 1201
    },
    {
     "code": "chunk.length != 6",
     "line": 1203
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1209
    },
    {
     "code": "chunk.length != 1",
     "line": 1211
    },
    {
     "code": "chunk.offset < ctx->plte_offset",
     "line": 1223
    },
    {
     "code": "ctx->ihdr.bit_depth < 16",
     "line": 1228
    },
    {
     "code": "ctx->ihdr.color_type == 0",
     "line": 1230
    },
    {
     "code": "chunk.length != 2",
     "line": 1232
    },
    {
     "code": "ctx->ihdr.color_type == 2",
     "line": 1236
    },
    {
     "code": "chunk.length != 6",
     "line": 1238
    },
    {
     "code": "ctx->ihdr.color_type == 3",
     "line": 1244
    },
    {
     "code": "chunk.length > ctx->plte.n_entries",
     "line": 1246
    },
    {
     "code": "k < chunk.length",
     "line": 1250
    },
    {
     "code": "chunk.offset < ctx->plte_offset",
     "line": 1264
    },
    {
     "code": "(chunk.length / 2) != (ctx->plte.n_entries)",
     "line": 1267
    },
    {
     "code": "k < (chunk.length / 2)",
     "line": 1270
    },
    {
     "code": "chunk.length != 9",
     "line": 1282
    },
    {
     "code": "ctx->splt_list == NULL",
     "line": 1304
    },
    {
     "code": "ctx->n_splt < 1",
     "line": 1309
    },
    {
     "code": "sizeof(struct spng_splt) > SIZE_MAX / ctx->n_splt",
     "line": 1310
    },
    {
     "code": "buf == NULL",
     "line": 1313
    },
    {
     "code": "chunk.length > 80",
     "line": 1320
    },
    {
     "code": "keyword_nul == NULL",
     "line": 1322
    },
    {
     "code": "(chunk.length - keyword_len - 1) ==  0",
     "line": 1330
    },
    {
     "code": "ctx->n_splt > 1",
     "line": 1334
    },
    {
     "code": "j < i",
     "line": 1337
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 16",
     "line": 1343
    },
    {
     "code": "(chunk.length - keyword_len - 2) % 10 != 0",
     "line": 1345
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 8",
     "line": 1348
    },
    {
     "code": "(chunk.length - keyword_len - 2) % 6 != 0",
     "line": 1350
    },
    {
     "code": "ctx->splt_list[i].n_entries == 0",
     "line": 1355
    },
    {
     "code": "sizeof(struct spng_splt_entry) > SIZE_MAX / ctx->splt_list[i].n_entries",
     "line": 1356
    },
    {
     "code": "ctx->splt_list[i].entries == NULL",
     "line": 1359
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 16",
     "line": 1364
    },
    {
     "code": "k < ctx->splt_list[i].n_entries",
     "line": 1366
    },
    {
     "code": "ctx->splt_list[i].sample_depth == 8",
     "line": 1375
    },
    {
     "code": "k < ctx->splt_list[i].n_entries",
     "line": 1377
    },
    {
     "code": "chunk.length != 7",
     "line": 1399
    },
    {
     "code": "chunk.length != 9",
     "line": 1430
    },
    {
     "code": "exif.data == NULL",
     "line": 1452
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "memcpy(exif.data, data, chunk.length)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "exif.data",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "chunk.length",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "exif",
    "data",
    "chunk"
   ],
   "osv_id": "ARVO-42476946",
   "sites": [
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "signature[8] = { 137, 80, 78, 71, 13, 10, 26, 10 }",
     "line": 1003
    },
    {
     "args": "ctx ;; 1 ;; sizeof(struct spng_splt)",
     "callee": "spng__calloc",
     "code": "spng__calloc(ctx, 1, sizeof(struct spng_splt))",
     "line": 1303
    },
    {
     "args": "ctx ;; ctx->splt_list ;; ctx->n_splt * sizeof(struct spng_splt)",
     "callee": "spng__realloc",
     "code": "spng__realloc(ctx, ctx->splt_list, ctx->n_splt * sizeof(struct spng_splt))",
     "line": 1312
    },
    {
     "args": "ctx ;; sizeof(struct spng_splt_entry) * ctx->splt_list[i].n_entries",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, sizeof(struct spng_splt_entry) * ctx->splt_list[i].n_entries)",
     "line": 1358
    },
    {
     "args": "ctx ;; chunk.length",
     "callee": "spng__malloc",
     "code": "spng__malloc(ctx, chunk.length)",
     "line": 1451
    },
    {
     "args": "ctx ;; exif.data",
     "callee": "spng__free",
     "code": "spng__free(ctx, exif.data)",
     "line": 1459
    },
    {
     "args": "ctx ;; exif.data",
     "callee": "spng__free",
     "code": "spng__free(ctx, exif.data)",
     "line": 1464
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "read_data",
   "use_fn": "read_chunks_before_idat"
  }
 },
 {
  "osv_id": "ARVO-42477951",
  "project": "opensc",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "obj",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "line": 1878,
    "size": null,
    "type": "sc_pkcs15_object*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/opensc/src/tests/fuzzing/fuzz_pkcs15_decode.c",
    "line": 56
   },
   "size_expr": null,
   "size_bytes": 2776,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 58,
    "fn": "LLVMFuzzerTestOneInput",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1882,
    "fn": "sc_pkcs15_free_object",
    "code": "obj->type & SC_PKCS15_TYPE_CLASS_MASK | obj->type | SC_PKCS15_TYPE_CLASS_MASK",
    "origin": "report:crash"
   },
   {
    "code": "free(obj->data)",
    "fn": "sc_pkcs15_free_object",
    "kind": "free",
    "line": 1899,
    "origin": "cpg",
    "args": "obj->data"
   },
   {
    "code": "free(obj)",
    "fn": "sc_pkcs15_free_object",
    "kind": "free",
    "line": 1904,
    "origin": "cpg",
    "args": "obj"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15_free_object",
    "file": "/src/opensc/src/libopensc/pkcs15.c",
    "line": 1882
   },
   "code": "obj->type & SC_PKCS15_TYPE_CLASS_MASK | obj->type | SC_PKCS15_TYPE_CLASS_MASK",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 2776
   }
  },
  "context": {
   "fn": "sc_pkcs15_free_object",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1880,SWITCH:1882,BREAK:1885,BREAK:1888,BREAK:1891,BREAK:1894,BREAK:1897"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_pkcs15_object*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "obj"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/opensc/address/3b632e64a19235636ab0a93fc2a4b5a7caf078a3/ARVO-42477951/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3b632e64a192.cpg",
   "testcase_size": 36
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "free_related": {
   "free_sites_in_func": [
    58,
    1899,
    1904
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 2776,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "sc_pkcs15_free_object--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
   "region_size": 2776
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1878,
    "type": "sc_pkcs15_object*"
   },
   "entity_name_cpg": "obj",
   "func_lines": [
    1877,
    1905
   ],
   "func_params": {
    "names": [
     "obj"
    ],
    "types": [
     "sc_pkcs15_object*"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "obj->type & SC_PKCS15_TYPE_CLASS_MASK",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "obj->type",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "SC_PKCS15_TYPE_CLASS_MASK",
     "name": "SC_PKCS15_TYPE_CLASS_MASK",
     "nargs": 0
    }
   ],
   "line_ids": [
    "obj"
   ],
   "osv_id": "ARVO-42477951",
   "sites": [
    {
     "args": "(sc_pkcs15_prkey_info_t *)obj->data",
     "callee": "sc_pkcs15_free_prkey_info",
     "code": "sc_pkcs15_free_prkey_info((sc_pkcs15_prkey_info_t *)obj->data)",
     "line": 1884
    },
    {
     "args": "(sc_pkcs15_pubkey_info_t *)obj->data",
     "callee": "sc_pkcs15_free_pubkey_info",
     "code": "sc_pkcs15_free_pubkey_info((sc_pkcs15_pubkey_info_t *)obj->data)",
     "line": 1887
    },
    {
     "args": "(sc_pkcs15_cert_info_t *)obj->data",
     "callee": "sc_pkcs15_free_cert_info",
     "code": "sc_pkcs15_free_cert_info((sc_pkcs15_cert_info_t *)obj->data)",
     "line": 1890
    },
    {
     "args": "(sc_pkcs15_data_info_t *)obj->data",
     "callee": "sc_pkcs15_free_data_info",
     "code": "sc_pkcs15_free_data_info((sc_pkcs15_data_info_t *)obj->data)",
     "line": 1893
    },
    {
     "args": "(sc_pkcs15_auth_info_t *)obj->data",
     "callee": "sc_pkcs15_free_auth_info",
     "code": "sc_pkcs15_free_auth_info((sc_pkcs15_auth_info_t *)obj->data)",
     "line": 1896
    },
    {
     "args": "obj->data",
     "callee": "free",
     "code": "free(obj->data)",
     "line": 1899
    },
    {
     "args": "obj",
     "callee": "sc_pkcs15_free_object_content",
     "code": "sc_pkcs15_free_object_content(obj)",
     "line": 1902
    },
    {
     "args": "obj",
     "callee": "free",
     "code": "free(obj)",
     "line": 1904
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": false,
   "free_fn": "LLVMFuzzerTestOneInput",
   "use_fn": "sc_pkcs15_free_object"
  }
 },
 {
  "osv_id": "ARVO-42478101",
  "project": "wireshark",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "g_malloc (/out/fuzzshark_ip_proto-udp+0x276a7e8)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": 40,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 54,
    "fn": "wmem_simple_free",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 258,
    "fn": "wmem_strbuf_get_str",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "wmem_strbuf_get_str",
    "file": "/src/wireshark/epan/wmem/wmem_strbuf.c",
    "line": 258
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 40
   }
  },
  "context": {
   "fn": "wmem_strbuf_get_str",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/wireshark/address/828ff6ddb0a824de7f48af8b2018c3d4506a48ce/ARVO-42478101/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_828ff6ddb0a8.cpg",
   "testcase_size": 39
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
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
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 40,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "wmem_strbuf_get_str--dissect_rrc_PLMN_IdentityWithOptionalMCC_r6--dissect_per_sequence_of_helper",
   "region_size": 40
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "wmem_simple_free",
   "use_fn": "wmem_strbuf_get_str"
  }
 },
 {
  "osv_id": "ARVO-42479359",
  "project": "openh264",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "this",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/manage_dec_ref.cpp",
    "line": 76,
    "size": null,
    "type": "WelsCommon.CWelsThread"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "line": 72
   },
   "size_expr": null,
   "size_bytes": 515,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 89,
    "fn": "WelsDec::SetUnRef(WelsDec::SPicture*)",
    "code": "(LPWELS_THREAD_ROUTINE)TheThread",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 113,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::SetUnRef(WelsDec::SPicture*)",
    "file": "/src/openh264/codec/decoder/core/src/manage_dec_ref.cpp",
    "line": 89
   },
   "code": "(LPWELS_THREAD_ROUTINE)TheThread",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": 515
   }
  },
  "context": {
   "fn": "Start",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:78,IF:82,IF:91,WHILE:95"
  },
  "call_chain": [],
  "types": {
   "entity_type": "WelsCommon.CWelsThread",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "this"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/c185ac351eff0ae277bfe14a3b2ad52e9ed8ab81/ARVO-42479359/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_c185ac351eff.cpg",
   "testcase_size": 62
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-use-after-free",
   "ledger_crash_type": "heap-use-after-free",
   "used": "heap-use-after-free",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 515,
   "loc_offset": 119,
   "loc_kind": "region",
   "dedup_token": "WelsDec::SetUnRef(WelsDec::SPicture*)--WelsDec::WelsResetRefPic(WelsDec::TagWelsDecoderContext*)--WelsFreeDynamicMemory",
   "region_size": 515
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 76,
    "type": "WelsCommon.CWelsThread"
   },
   "entity_name_cpg": "this",
   "func_lines": [
    76,
    100
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "WelsCommon.CWelsThread"
    ]
   },
   "guards": [
    {
     "code": "NULL == m_hEvent",
     "line": 78
    },
    {
     "code": "WELS_THREAD_ERROR_OK != rc",
     "line": 91
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "(LPWELS_THREAD_ROUTINE)TheThread",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "this"
   ],
   "osv_id": "ARVO-42479359",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "WelsCommon::WelsFree(void*, char const*)",
   "use_fn": "WelsDec::SetUnRef(WelsDec::SPicture*)"
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
        "free_cross_function": "true | false | unknown",
        "cross_frame_count": "number | unknown"
      },
      "dimension_distributions": {"维度名": {"取值": "样本数"}},
      "evidence": ["string"],
      "confidence": "high | medium | low"
    }
  ],
  "unclassified": [{"sample_id": "string", "reason": "string", "missing_fields": ["string"]}],
  "batch_observations": "string"
}

直接输出 JSON，不要任何解释文字。