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
  "osv_id": "ARVO-42480782",
  "project": "libxml2",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/libxml2/valid.c",
    "line": 1250,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1279,
    "fn": "xmlSnprintfElementContent",
    "code": "strcat(buf, (char *) content->name) | (char *) content->name | content->name",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlSnprintfElementContent",
    "file": "/src/libxml2/valid.c",
    "line": 1279
   },
   "code": "strcat(buf, (char *) content->name) | (char *) content->name | content->name",
   "access": {
    "dir": "WRITE",
    "width": 37,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlSnprintfElementContent",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "content == NULL",
   "guard_count": 1,
   "control_structures": "IF:1253,IF:1255,IF:1256,IF:1260,SWITCH:1261,BREAK:1264,IF:1266,IF:1267,IF:1274,IF:1278,BREAK:1280,IF:1282"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf",
   "content"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/libxml2/address/e905f08123e4a6e7731549e6f09dadff4cab65bd/ARVO-42480782/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_e905f08123e4.cpg",
   "testcase_size": 2889
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
   "loc_offset": 5128,
   "loc_kind": "stack_frame",
   "dedup_token": "__interceptor_strcat--xmlSnprintfElementContent--xmlSnprintfElementContent"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1250,
    "type": "char*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    1249,
    1337
   ],
   "func_params": {
    "names": [
     "buf",
     "size",
     "content",
     "englob"
    ],
    "types": [
     "char*",
     "int",
     "xmlElementContentPtr",
     "int"
    ]
   },
   "guards": [
    {
     "code": "content == NULL",
     "line": 1253
    },
    {
     "code": "size - len < 50",
     "line": 1255
    },
    {
     "code": "size - len > 4",
     "line": 1256
    },
    {
     "code": "buf[len - 1] != '.'",
     "line": 1256
    },
    {
     "code": "content->prefix != NULL",
     "line": 1266
    },
    {
     "code": "size - len < xmlStrlen(content->prefix) + 10",
     "line": 1267
    },
    {
     "code": "size - len < xmlStrlen(content->name) + 10",
     "line": 1274
    },
    {
     "code": "content->name != NULL",
     "line": 1278
    },
    {
     "code": "content->c1->type == XML_ELEMENT_CONTENT_OR",
     "line": 1282
    },
    {
     "code": "content->c1->type == XML_ELEMENT_CONTENT_SEQ",
     "line": 1283
    },
    {
     "code": "size - len < 50",
     "line": 1288
    },
    {
     "code": "size - len > 4",
     "line": 1289
    },
    {
     "code": "buf[len - 1] != '.'",
     "line": 1289
    },
    {
     "code": "content->c2->type == XML_ELEMENT_CONTENT_OR",
     "line": 1294
    },
    {
     "code": "content->c2->ocur != XML_ELEMENT_CONTENT_ONCE",
     "line": 1295
    },
    {
     "code": "content->c2->type != XML_ELEMENT_CONTENT_ELEMENT",
     "line": 1296
    },
    {
     "code": "content->c1->type == XML_ELEMENT_CONTENT_OR",
     "line": 1302
    },
    {
     "code": "content->c1->type == XML_ELEMENT_CONTENT_SEQ",
     "line": 1303
    },
    {
     "code": "size - len < 50",
     "line": 1308
    },
    {
     "code": "size - len > 4",
     "line": 1309
    },
    {
     "code": "buf[len - 1] != '.'",
     "line": 1309
    },
    {
     "code": "content->c2->type == XML_ELEMENT_CONTENT_SEQ",
     "line": 1314
    },
    {
     "code": "content->c2->ocur != XML_ELEMENT_CONTENT_ONCE",
     "line": 1315
    },
    {
     "code": "content->c2->type != XML_ELEMENT_CONTENT_ELEMENT",
     "line": 1316
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "strcat(buf, (char *) content->name)",
     "name": "strcat",
     "nargs": 2
    },
    {
     "code": "(char *) content->name",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "content->name",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buf",
    "content"
   ],
   "osv_id": "ARVO-42480782",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlSnprintfElementContent"
  }
 },
 {
  "osv_id": "ARVO-42480985",
  "project": "mruby",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "n",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/mruby/src/string.c",
    "line": 2498,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "size_expr_cpg": "DBL_DIG * 4 + 10",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2542,
    "fn": "mrb_str_len_to_dbl",
    "code": "*n++ = c | *n++ | n++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mrb_str_len_to_dbl",
    "file": "/src/mruby/src/string.c",
    "line": 2542
   },
   "code": "*n++ = c | *n++ | n++",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_str_len_to_dbl",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "c == '_' | n == buf",
   "guard_count": 2,
   "control_structures": "IF:2502,WHILE:2503,IF:2505,IF:2508,IF:2510,ELSE:2513,WHILE:2516,IF:2517,IF:2518,GOTO:2524,IF:2526,BREAK:2526"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/mruby/address/afad9391734998df4f76a6f7108278d2aa2599a0/ARVO-42480985/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_afad93917349.cpg",
   "testcase_size": 156
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
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_offset": 102,
   "loc_kind": "stack_frame",
   "dedup_token": "mrb_str_len_to_dbl--mrb_str_len_to_inum--mrb_str_to_i"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "n = buf",
     "line": 2530
    }
   ],
   "entity_decl": {
    "line": 2498,
    "type": "char*"
   },
   "entity_name_cpg": "n",
   "func_lines": [
    2491,
    2565
   ],
   "func_params": {
    "names": [
     "mrb",
     "s",
     "len",
     "badcheck"
    ],
    "types": [
     "mrb_state*",
     "char*",
     "size_t",
     "mrb_bool"
    ]
   },
   "guards": [
    {
     "code": "p<pend",
     "line": 2503
    },
    {
     "code": "pend - p > 2",
     "line": 2505
    },
    {
     "code": "p[0] == '0'",
     "line": 2505
    },
    {
     "code": "p[1] == 'x'",
     "line": 2505
    },
    {
     "code": "p[1] == 'X'",
     "line": 2505
    },
    {
     "code": "p < pend",
     "line": 2516
    },
    {
     "code": "p < pend",
     "line": 2518
    },
    {
     "code": "*p == '_'",
     "line": 2526
    },
    {
     "code": "p < pend",
     "line": 2531
    },
    {
     "code": "c == '_'",
     "line": 2533
    },
    {
     "code": "n == buf",
     "line": 2535
    },
    {
     "code": "p == pend",
     "line": 2535
    },
    {
     "code": "prev == '_'",
     "line": 2540
    },
    {
     "code": "p == end",
     "line": 2551
    },
    {
     "code": "p == end",
     "line": 2560
    },
    {
     "code": "end<pend",
     "line": 2561
    },
    {
     "code": "end<pend",
     "line": 2562
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "*n++ = c",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*n++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "n++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "n",
    "c"
   ],
   "osv_id": "ARVO-42480985",
   "sites": [
    {
     "args": "DBL_DIG * 4 + 10",
     "callee": "<operator>.alloc",
     "code": "buf[DBL_DIG * 4 + 10]",
     "line": 2494
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_str_len_to_dbl"
  }
 },
 {
  "osv_id": "ARVO-42481955",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "data",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/openthread/src/core/common/tlvs.hpp",
    "line": 268,
    "size": null,
    "type": "uint8_t*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 268,
    "fn": "ot::ExtendedTlv::GetLength() const",
    "code": "*data    = aData + written | aData + written",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::ExtendedTlv::GetLength() const",
    "file": "/src/openthread/src/core/common/tlvs.hpp",
    "line": 268
   },
   "code": "*data    = aData + written | aData + written",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "utilsFlashWrite",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "written < aSize",
   "guard_count": 1,
   "control_structures": "WHILE:265,IF:273,IF:286,IF:291,BREAK:293"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "aAddress",
   "aData",
   "aSize"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/1f2bed8e7d73daa057ebb24f785ff88b8315c922/ARVO-42481955/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_1f2bed8e7d73.cpg",
   "testcase_size": 844
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
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_offset": 286,
   "loc_kind": "stack_frame",
   "dedup_token": "ot::ExtendedTlv::GetLength() const--ot::Tlv::GetSize() const--ot::Tlv::GetNext()"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*data    = aData + written",
     "line": 268
    }
   ],
   "entity_decl": {
    "line": 268,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "data",
   "func_lines": [
    256,
    303
   ],
   "func_params": {
    "names": [
     "aAddress",
     "aData",
     "aSize"
    ],
    "types": [
     "uint32_t",
     "uint8_t*",
     "uint32_t"
    ]
   },
   "guards": [
    {
     "code": "written < aSize",
     "line": 265
    },
    {
     "code": "toWrite > MAX_WRITE_INCREMENT",
     "line": 273
    },
    {
     "code": "fsmRet != FAPI_STATUS_SUCCESS",
     "line": 291
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "*data    = aData + written",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "aData + written",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "data",
    "aData",
    "written"
   ],
   "osv_id": "ARVO-42481955",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::ExtendedTlv::GetLength() const"
  }
 },
 {
  "osv_id": "ARVO-42483000",
  "project": "wireshark",
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
    "line": 59,
    "fn": "tvb_get_ipv4_addr_with_prefix_len",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tvb_get_ipv4_addr_with_prefix_len",
    "file": "/src/wireshark/epan/addr_and_mask.c",
    "line": 59
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tvb_get_ipv4_addr_with_prefix_len",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/2bdff1df49282cf0959b841789095cd5813ea214/ARVO-42483000/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_2bdff1df4928.cpg",
   "testcase_size": 219
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_offset": 36,
   "loc_kind": "stack_frame",
   "dedup_token": "tvb_get_ipv4_addr_with_prefix_len--decode_path_prefix4--decode_prefix_MP"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tvb_get_ipv4_addr_with_prefix_len"
  }
 },
 {
  "osv_id": "ARVO-42483752",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "out",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-coolkey.c",
    "line": 1669,
    "size": null,
    "type": "u8*"
   }
  },
  "alloc": {
   "size_expr_cpg": "MAX_COMPUTE_BUF+2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1764,
    "fn": "coolkey_rsa_op",
    "code": "memcpy(out, buf+2, out_length) | buf+2",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "coolkey_rsa_op",
    "file": "/src/opensc/src/libopensc/card-coolkey.c",
    "line": 1764
   },
   "code": "memcpy(out, buf+2, out_length) | buf+2",
   "access": {
    "dir": "READ",
    "width": 36864,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "coolkey_rsa_op",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "(out_length) < (max_out_len) | (out_length) < (max_out_len)",
   "guard_count": 2,
   "control_structures": "DO:1683,IF:1700,GOTO:1702,IF:1708,IF:1721,GOTO:1722,IF:1727,GOTO:1728,IF:1733,IF:1742,GOTO:1743,IF:1745"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "out",
   "max_out_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/31169afb7252f58a2db2b365835f6166f9d4b6c9/ARVO-42483752/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_31169afb7252.cpg",
   "testcase_size": 1517
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_offset": 538,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--coolkey_rsa_op--coolkey_compute_crypt"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1669,
    "type": "u8*"
   },
   "entity_name_cpg": "out",
   "func_lines": [
    1667,
    1770
   ],
   "func_params": {
    "names": [
     "card",
     "data",
     "datalen",
     "out",
     "max_out_len"
    ],
    "types": [
     "sc_card_t*",
     "u8*",
     "size_t",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "priv->key_id > 0xff",
     "line": 1700
    },
    {
     "code": "crypt_in_len > MAX_COMPUTE_BUF",
     "line": 1708
    },
    {
     "code": "r < 0",
     "line": 1721
    },
    {
     "code": "r < 0",
     "line": 1727
    },
    {
     "code": "r < 0",
     "line": 1742
    },
    {
     "code": "datalen > MAX_COMPUTE_BUF",
     "line": 1745
    },
    {
     "code": "r < 0",
     "line": 1751
    },
    {
     "code": "(out_length) < (max_out_len)",
     "line": 1756
    },
    {
     "code": "(out_length) < (max_out_len)",
     "line": 1763
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(out, buf+2, out_length)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "buf+2",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out",
    "buf",
    "out_length"
   ],
   "osv_id": "ARVO-42483752",
   "sites": [
    {
     "args": "MAX_COMPUTE_BUF+2",
     "callee": "<operator>.alloc",
     "code": "buf[MAX_COMPUTE_BUF+2]",
     "line": 1680
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "len_buf[2]",
     "line": 1709
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "len_buf[2]",
     "line": 1746
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "coolkey_rsa_op"
  }
 },
 {
  "osv_id": "ARVO-42483880",
  "project": "mruby",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-sprintf/src/sprintf.c",
    "line": 1130,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1153,
    "fn": "fmt_setup",
    "code": "*buf++ = c | *buf++ | buf++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "fmt_setup",
    "file": "/src/mruby/mrbgems/mruby-sprintf/src/sprintf.c",
    "line": 1153
   },
   "code": "*buf++ = c | *buf++ | buf++",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "fmt_setup",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1136,IF:1137,IF:1138,IF:1139,IF:1140,IF:1142,IF:1147"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buf",
   "size",
   "c",
   "width",
   "prec"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/mruby/address/7add524041df0f2482e587ec1a3920c6f34624a4/ARVO-42483880/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_7add524041df.cpg",
   "testcase_size": 40
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
   "loc_offset": 257,
   "loc_kind": "stack_frame",
   "dedup_token": "fmt_setup--mrb_str_format--mrb_f_sprintf"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1130,
    "type": "char*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    1129,
    1155
   ],
   "func_params": {
    "names": [
     "buf",
     "size",
     "c",
     "flags",
     "width",
     "prec"
    ],
    "types": [
     "char*",
     "size_t",
     "int",
     "int",
     "mrb_int",
     "mrb_int"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "*buf++ = c",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*buf++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "buf++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "buf",
    "c"
   ],
   "osv_id": "ARVO-42483880",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "fmt_setup"
  }
 },
 {
  "osv_id": "ARVO-42484390",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "sbuf",
   "kind": "array",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-tcos.c",
    "line": 604,
    "size": null,
    "type": "u8[261]"
   }
  },
  "alloc": {
   "size_expr_cpg": "SC_MAX_APDU_BUFFER_SIZE",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 626,
    "fn": "tcos_decipher",
    "code": "memcpy(sbuf+1, crgram, crgram_len) | sbuf+1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tcos_decipher",
    "file": "/src/opensc/src/libopensc/card-tcos.c",
    "line": 626
   },
   "code": "memcpy(sbuf+1, crgram, crgram_len) | sbuf+1",
   "access": {
    "dir": "WRITE",
    "width": 52545,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tcos_decipher",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "crgram != NULL | crgram_len>255",
   "guard_count": 2,
   "control_structures": "DO:613,DO:629,IF:629,IF:631,IF:634,WHILE:635,DO:639,IF:639,ELSE:639,DO:641,IF:641,ELSE:641"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8[261]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "card",
   "crgram",
   "crgram_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/797414be05220fa371972606d7a6c2e94dd6d8db/ARVO-42484390/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_797414be0522.cpg",
   "testcase_size": 68675
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
   "loc_offset": 773,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--tcos_decipher--sc_decipher"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "sbuf[SC_MAX_APDU_BUFFER_SIZE]",
     "line": 604
    },
    {
     "code": "sbuf[0] = tcos3 ? 0x00 : ((data->pad_flags & SC_ALGORITHM_RSA_PAD_PKCS1) ? 0x81 : 0x02)",
     "line": 625
    }
   ],
   "entity_decl": {
    "line": 604,
    "type": "u8[261]"
   },
   "entity_name_cpg": "sbuf",
   "func_lines": [
    599,
    642
   ],
   "func_params": {
    "names": [
     "card",
     "crgram",
     "crgram_len",
     "out",
     "outlen"
    ],
    "types": [
     "sc_card_t*",
     "u8*",
     "size_t",
     "u8*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "card != NULL",
     "line": 608
    },
    {
     "code": "crgram != NULL",
     "line": 608
    },
    {
     "code": "out != NULL",
     "line": 608
    },
    {
     "code": "card->type==SC_CARD_TYPE_TCOS_V3",
     "line": 610
    },
    {
     "code": "crgram_len>255",
     "line": 618
    },
    {
     "code": "_ret < 0",
     "line": 629
    },
    {
     "code": "apdu.sw1==0x90",
     "line": 631
    },
    {
     "code": "apdu.sw2==0x00",
     "line": 631
    },
    {
     "code": "apdu.resplen>outlen",
     "line": 632
    },
    {
     "code": "apdu.resp[0]==0",
     "line": 634
    },
    {
     "code": "apdu.resp[1]==2",
     "line": 634
    },
    {
     "code": "offset<len",
     "line": 635
    },
    {
     "code": "apdu.resp[offset]!=0",
     "line": 635
    },
    {
     "code": "offset<len-1",
     "line": 636
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(sbuf+1, crgram, crgram_len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "sbuf+1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "sbuf",
    "crgram",
    "crgram_len"
   ],
   "osv_id": "ARVO-42484390",
   "sites": [
    {
     "args": "SC_MAX_APDU_BUFFER_SIZE",
     "callee": "<operator>.alloc",
     "code": "rbuf[SC_MAX_APDU_BUFFER_SIZE]",
     "line": 603
    },
    {
     "args": "SC_MAX_APDU_BUFFER_SIZE",
     "callee": "<operator>.alloc",
     "code": "sbuf[SC_MAX_APDU_BUFFER_SIZE]",
     "line": 604
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tcos_decipher"
  }
 },
 {
  "osv_id": "ARVO-42487756",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/apdu.c",
    "line": 423,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 475,
    "fn": "sc_get_response",
    "code": "memcpy(buf, resp, le)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_get_response",
    "file": "/src/opensc/src/libopensc/apdu.c",
    "line": 475
   },
   "code": "memcpy(buf, resp, le)",
   "access": {
    "dir": "WRITE",
    "width": 28,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_get_response",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "buflen < le",
   "guard_count": 1,
   "control_structures": "DO:426,IF:427,IF:435,DO:436,IF:436,DO:452,IF:460,DO:467,IF:467,IF:472,IF:480,BREAK:481"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "card",
   "apdu",
   "olen"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b02da8348be97d4b24081783f6af46757373bc3e/ARVO-42487756/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b02da8348be9.cpg",
   "testcase_size": 66395
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_offset": 65570,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--sc_get_response--sc_transmit"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf = apdu->resp + apdu->resplen",
     "line": 442
    }
   ],
   "entity_decl": {
    "line": 423,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    418,
    498
   ],
   "func_params": {
    "names": [
     "card",
     "apdu",
     "olen"
    ],
    "types": [
     "sc_card*",
     "sc_apdu*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "apdu->le == 0",
     "line": 427
    },
    {
     "code": "_ret < 0",
     "line": 436
    },
    {
     "code": "apdu->sw2 != 0",
     "line": 448
    },
    {
     "code": "rv < 0",
     "line": 460
    },
    {
     "code": "_ret < 0",
     "line": 467
    },
    {
     "code": "buflen < le",
     "line": 472
    },
    {
     "code": "buflen == 0",
     "line": 480
    },
    {
     "code": "rv != 0",
     "line": 484
    },
    {
     "code": "rv != 0",
     "line": 490
    },
    {
     "code": "minlen != 0",
     "line": 490
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(buf, resp, le)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "buf",
    "resp",
    "le"
   ],
   "osv_id": "ARVO-42487756",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "resp[256]",
     "line": 453
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_get_response"
  }
 },
 {
  "osv_id": "ARVO-42488023",
  "project": "fluent-bit",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "s",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/fluent-bit/src/flb_sds.c",
    "line": 118,
    "size": null,
    "type": "flb_sds_t"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 132,
    "fn": "flb_sds_cat",
    "code": "memcpy((char *) (s + flb_sds_len(s)), str, len) | (char *) (s + flb_sds_len(s)) | s + flb_sds_len(s) | flb_sds_len(s)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_sds_cat",
    "file": "/src/fluent-bit/src/flb_sds.c",
    "line": 132
   },
   "code": "memcpy((char *) (s + flb_sds_len(s)), str, len) | (char *) (s + flb_sds_len(s)) | s + flb_sds_len(s) | flb_sds_len(s)",
   "access": {
    "dir": "READ",
    "width": 313,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "flb_sds_cat",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "avail < len",
   "guard_count": 1,
   "control_structures": "IF:125,IF:127"
  },
  "call_chain": [],
  "types": {
   "entity_type": "flb_sds_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "s",
   "str",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/fluent-bit/address/6fe5d030bcee43556fb1c6054f55854c605a5b0c/ARVO-42488023/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_6fe5d030bcee.cpg",
   "testcase_size": 512
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
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 144,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--flb_sds_cat--flb_msgpack_gelf_value"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "s = tmp",
     "line": 130
    },
    {
     "code": "s[head->len] = '\\0'",
     "line": 136
    }
   ],
   "entity_decl": {
    "line": 118,
    "type": "flb_sds_t"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    118,
    139
   ],
   "func_params": {
    "names": [
     "s",
     "str",
     "len"
    ],
    "types": [
     "flb_sds_t",
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "avail < len",
     "line": 125
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy((char *) (s + flb_sds_len(s)), str, len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "(char *) (s + flb_sds_len(s))",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "s + flb_sds_len(s)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "flb_sds_len(s)",
     "name": "flb_sds_len",
     "nargs": 1
    }
   ],
   "line_ids": [
    "s",
    "str",
    "len"
   ],
   "osv_id": "ARVO-42488023",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "flb_sds_cat"
  }
 },
 {
  "osv_id": "ARVO-42489404",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "buf",
   "kind": "array",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-tcos.c",
    "line": 126,
    "size": null,
    "type": "unsigned char[256]"
   }
  },
  "alloc": {
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 142,
    "fn": "insert_key",
    "code": "buf[i]==0x83 && buf[i+1]==1 && buf[i+2]==key_reference | buf[i]==0x83 && buf[i+1]==1 | buf[i]==0x83 | buf[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "insert_key",
    "file": "/src/opensc/src/libopensc/pkcs15-tcos.c",
    "line": 142
   },
   "code": "buf[i]==0x83 && buf[i+1]==1 && buf[i+2]==key_reference | buf[i]==0x83 && buf[i+1]==1 | buf[i]==0x83 | buf[i]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "insert_key",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i<buf[1]+2 | buf[i+2]==key_reference | i<r",
   "guard_count": 3,
   "control_structures": "IF:125,IF:128,IF:130,WHILE:138,IF:140,CONTINUE:140,FOR:141,IF:142,IF:144,BREAK:144,IF:146,FOR:150"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char[256]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "key_reference"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/797414be05220fa371972606d7a6c2e94dd6d8db/ARVO-42489404/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_797414be0522.cpg",
   "testcase_size": 1218
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
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 3744,
   "loc_kind": "stack_frame",
   "dedup_token": "insert_key--detect_netkey--sc_pkcs15emu_tcos_init_ex"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "buf[256]",
     "line": 126
    }
   ],
   "entity_decl": {
    "line": 126,
    "type": "unsigned char[256]"
   },
   "entity_name_cpg": "buf",
   "func_lines": [
    94,
    177
   ],
   "func_params": {
    "names": [
     "p15card",
     "path",
     "id",
     "key_reference",
     "key_length",
     "auth_id",
     "label"
    ],
    "types": [
     "sc_pkcs15_card_t*",
     "char*",
     "unsigned char",
     "unsigned char",
     "int",
     "unsigned char",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "card->type==SC_CARD_TYPE_TCOS_V3",
     "line": 125
    },
    {
     "code": "sc_select_file(card, &prkey_info.path, NULL)!=SC_SUCCESS",
     "line": 130
    },
    {
     "code": "(r=sc_read_record(card, ++rec_no, buf, sizeof(buf), SC_RECORD_BY_REC_NR))>0",
     "line": 138
    },
    {
     "code": "buf[0]!=0xA0",
     "line": 140
    },
    {
     "code": "i<buf[1]+2",
     "line": 141
    },
    {
     "code": "buf[i]==0x83",
     "line": 142
    },
    {
     "code": "buf[i+1]==1",
     "line": 142
    },
    {
     "code": "buf[i+2]==key_reference",
     "line": 142
    },
    {
     "code": "i<r",
     "line": 150
    },
    {
     "code": "buf[i]==0xB6",
     "line": 151
    },
    {
     "code": "buf[i]==0xB8",
     "line": 152
    },
    {
     "code": "sc_select_file(card, &prkey_info.path, &f)!=SC_SUCCESS",
     "line": 155
    },
    {
     "code": "f->prop_attr_len < 2",
     "line": 156
    },
    {
     "code": "r!=SC_SUCCESS",
     "line": 171
    }
   ],
   "line_call_count": 11,
   "line_calls": [
    {
     "code": "buf[i]==0x83 && buf[i+1]==1 && buf[i+2]==key_reference",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "buf[i]==0x83 && buf[i+1]==1",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "buf[i]==0x83",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "buf[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "buf[i+1]==1",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "buf[i+1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "buf[i+2]==key_reference",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "buf[i+2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i+2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "++found",
     "name": "<operator>.preIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "buf",
    "i",
    "key_reference",
    "found"
   ],
   "osv_id": "ARVO-42489404",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "buf[256]",
     "line": 126
    },
    {
     "args": "f",
     "callee": "sc_file_free",
     "code": "sc_file_free(f)",
     "line": 164
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "insert_key"
  }
 },
 {
  "osv_id": "ARVO-42489610",
  "project": "wolfssl",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": null,
  "sites": [],
  "crash": {
   "site": {
    "fn": null,
    "file": null,
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": null,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wolfssl/address/2d79e3843686f498db28e3a406a87e389eb0749b/ARVO-42489610/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_2d79e3843686.cpg",
   "testcase_size": 4154
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
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 120,
   "loc_kind": "stack_frame",
   "dedup_token": "fp_read_unsigned_bin--mp_read_unsigned_bin--wc_RsaPublicKeyDecodeRaw"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": null
  }
 },
 {
  "osv_id": "ARVO-42490332",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "aPower",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "line": 1292,
    "size": null,
    "type": "int8_t*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1298,
    "fn": "ot::MeshCoP::ChannelMaskEntryBase::GetEntrySize() const",
    "code": "otEXPECT_ACTION(aPower != NULL, error = OT_ERROR_INVALID | aPower != NULL | error = OT_ERROR_INVALID_ARGS",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::MeshCoP::ChannelMaskEntryBase::GetEntrySize() const",
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "line": 1298
   },
   "code": "otEXPECT_ACTION(aPower != NULL, error = OT_ERROR_INVALID | aPower != NULL | error = OT_ERROR_INVALID_ARGS",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "otPlatRadioGetTransmitPower",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "aPower != NULL",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": "int8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "aPower"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/82eee1f8d32980279ba5b9b63f53609325d910fb/ARVO-42490332/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_82eee1f8d329.cpg",
   "testcase_size": 255
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_offset": 594,
   "loc_kind": "stack_frame",
   "dedup_token": "ot::MeshCoP::ChannelMaskEntryBase::GetEntrySize() const--ot::MeshCoP::ChannelMaskEntryBase::GetNext() const--ot::MeshCoP::ChannelMaskBaseTlv::IsValid() const"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1292,
    "type": "int8_t*"
   },
   "entity_name_cpg": "aPower",
   "func_lines": [
    1292,
    1303
   ],
   "func_params": {
    "names": [
     "aInstance",
     "aPower"
    ],
    "types": [
     "otInstance*",
     "int8_t*"
    ]
   },
   "guards": [
    {
     "code": "aPower != NULL",
     "line": 1298
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "otEXPECT_ACTION(aPower != NULL, error = OT_ERROR_INVALID_ARGS)",
     "name": "otEXPECT_ACTION",
     "nargs": 2
    },
    {
     "code": "aPower != NULL",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "error = OT_ERROR_INVALID_ARGS",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "aPower",
    "NULL",
    "error",
    "OT_ERROR_INVALID_ARGS"
   ],
   "osv_id": "ARVO-42490332",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::MeshCoP::ChannelMaskEntryBase::GetEntrySize() const"
  }
 },
 {
  "osv_id": "ARVO-42490739",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 92,
    "fn": "ot::IsValidUtf8String(char const*, unsigned long)",
    "code": "{-18, 0x06c9} | -18",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::IsValidUtf8String(char const*, unsigned long)",
    "file": "/src/openthread/src/core/common/string.cpp",
    "line": 92
   },
   "code": "{-18, 0x06c9} | -18",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "<global>",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/0d14e854398cd9eced31666e48e6ab656e574074/ARVO-42490739/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_0d14e854398c.cpg",
   "testcase_size": 51
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_offset": 300,
   "loc_kind": "stack_frame",
   "dedup_token": "ot::IsValidUtf8String(char const*, unsigned long)--ot::MeshCoP::NetworkNameTlv::IsValid() const--ot::MeshCoP::Tlv::IsValid(ot::MeshCoP::Tlv const&)"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    1,
    200
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "{-18, 0x06c9}",
     "name": "<operator>.arrayInitializer",
     "nargs": 2
    },
    {
     "code": "-18",
     "name": "<operator>.minus",
     "nargs": 1
    }
   ],
   "line_ids": [],
   "osv_id": "ARVO-42490739",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::IsValidUtf8String(char const*, unsigned long)"
  }
 },
 {
  "osv_id": "ARVO-42490832",
  "project": "perfetto",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 211,
    "fn": "perfetto::trace_processor::MemoryTrackerSnapshotParser::EmitRows(long, perfetto::trace_processor::GlobalNodeGraph&, perfetto::trace_processor::LevelOfDetail)",
    "code": "base::StringView()",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "perfetto::trace_processor::MemoryTrackerSnapshotParser::EmitRows(long, perfetto::trace_processor::GlobalNodeGraph&, perfetto::trace_processor::LevelOfDetail)",
    "file": "/src/perfetto/src/trace_processor/importers/proto/memory_tracker_snapshot_parser.cc",
    "line": 211
   },
   "code": "base::StringView()",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Lookup",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/perfetto/address/f37338cdaa2126eef2a11e1a6f0cb075888c20e6/ARVO-42490832/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_f37338cdaa21.cpg",
   "testcase_size": 140
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
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 80,
   "loc_kind": "stack_frame",
   "dedup_token": "perfetto::trace_processor::MemoryTrackerSnapshotParser::EmitRows(long, perfetto::trace_processor::GlobalNodeGraph&, perfetto::trace_processor::LevelOfDetail)--p"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    209,
    233
   ],
   "func_params": {
    "names": [
     "this",
     "id"
    ],
    "types": [
     "perfetto.KernelSymbolMap.TokenTable",
     "TokenId"
    ]
   },
   "guards": [
    {
     "code": "id == 0",
     "line": 210
    },
    {
     "code": "id > num_tokens_",
     "line": 212
    },
    {
     "code": "index_off < index_.size()",
     "line": 218
    },
    {
     "code": "begin == 0",
     "line": 221
    },
    {
     "code": "off < buf_size",
     "line": 223
    },
    {
     "code": "(buf_[off] & 0x80) == 0",
     "line": 225
    },
    {
     "code": "cur_id == id",
     "line": 227
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "base::StringView()",
     "name": "StringView",
     "nargs": 0
    }
   ],
   "line_ids": [],
   "osv_id": "ARVO-42490832",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "perfetto::trace_processor::MemoryTrackerSnapshotParser::EmitRows(long, perfetto::trace_processor::GlobalNodeGraph&, perfetto::trace_processor::LevelOfDetail)"
  }
 },
 {
  "osv_id": "ARVO-42491388",
  "project": "serenity",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "output",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/serenity/Libraries/LibJS/Heap/Heap.cpp",
    "line": 118,
    "size": null,
    "type": "StringBuilder"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 149,
    "fn": "JS::Heap::gather_conservative_roots(AK::HashTable<JS::Cell*, AK::Traits<JS::Cell*> >&)",
    "code": "output.append(out2)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "JS::Heap::gather_conservative_roots(AK::HashTable<JS::Cell*, AK::Traits<JS::Cell*> >&)",
    "file": "/src/serenity/Libraries/LibJS/Heap/Heap.cpp",
    "line": 149
   },
   "code": "output.append(out2)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "encode_base64",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:129"
  },
  "call_chain": [],
  "types": {
   "entity_type": "StringBuilder",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/serenity/address/370ce4243005fb123ae1a13177b486c377ce2d6d/ARVO-42491388/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_370ce4243005.cpg",
   "testcase_size": 4
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
   "loc_offset": 40,
   "loc_kind": "stack_frame",
   "dedup_token": "JS::Heap::gather_conservative_roots(AK::HashTable<JS::Cell*, AK::Traits<JS::Cell*> >&)--JS::Heap::gather_roots(AK::HashTable<JS::Cell*, AK::Traits<JS::Cell*> >&"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 118,
    "type": "StringBuilder"
   },
   "entity_name_cpg": "output",
   "func_lines": [
    115,
    154
   ],
   "func_params": {
    "names": [
     "input"
    ],
    "types": [
     "ReadonlyBytes"
    ]
   },
   "guards": [
    {
     "code": "i < input.size()",
     "line": 129
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "output.append(out2)",
     "name": "append",
     "nargs": 2
    }
   ],
   "line_ids": [
    "output",
    "out2"
   ],
   "osv_id": "ARVO-42491388",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "JS::Heap::gather_conservative_roots(AK::HashTable<JS::Cell*, AK::Traits<JS::Cell*> >&)"
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