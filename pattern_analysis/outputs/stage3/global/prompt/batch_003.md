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
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "xmlParseQName",
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
    "file": "/src/libxml2/parser.c",
    "fn": "xmlParseQName",
    "line": null
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522277/report.log",
   "testcase_size": 241
  },
  "input_reachability": [],
  "osv_id": "ARVO-42522277",
  "project": "libxml2",
  "sites": [],
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
   "control_structures": "IF:2115,WHILE:2122,IF:2123,ELSE:2125,IF:2129,IF:2131,ELSE:2138,WHILE:2141,IF:2142,ELSE:2144,IF:2144,IF:2148",
   "fn": "xmlSkipBlankChars",
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
   "code": "IS_BLANK_CH(*cur) | *cur",
   "site": {
    "file": "/src/libxml2/parser.c",
    "fn": "xmlSkipBlankChars",
    "line": 2122
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 2117,
    "size": null,
    "type": "xmlChar*"
   },
   "kind": "pointer",
   "name": "cur",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522281/report.log",
   "testcase_size": 1799
  },
  "input_reachability": [],
  "osv_id": "ARVO-42522281",
  "project": "libxml2",
  "sites": [
   {
    "code": "IS_BLANK_CH(*cur) | *cur",
    "fn": "xmlSkipBlankChars",
    "kind": "unknown",
    "line": 2122,
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
   "entity_type": "xmlChar*",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:9948,WHILE:9949,IF:9956,ELSE:9964,IF:9964,ELSE:9971,IF:9971,ELSE:9980,IF:9980,IF:9981,IF:9982,BREAK:9983",
   "fn": "xmlParseContentInternal",
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
   "code": "(RAW != 0) &&",
   "site": {
    "file": "/src/libxml2/parser.c",
    "fn": "xmlParseContentInternal",
    "line": 9949
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 9945,
    "size": null,
    "type": "xmlParserCtxtPtr"
   },
   "kind": "struct",
   "name": "ctxt",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522285/report.log",
   "testcase_size": 228
  },
  "input_reachability": [
   "ctxt"
  ],
  "osv_id": "ARVO-42522285",
  "project": "libxml2",
  "sites": [
   {
    "code": "(RAW != 0) &&",
    "fn": "xmlParseContentInternal",
    "kind": "unknown",
    "line": 9949,
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
   "entity_type": "xmlParserCtxtPtr",
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
   "control_structures": "IF:436,IF:439,SWITCH:443,BREAK:462",
   "fn": "xmlDictComputeFastKey",
   "guard_count": 1,
   "guards": "name == NULL",
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
   "code": "value += *name | *name",
   "site": {
    "file": "/src/libxml2/dict.c",
    "fn": "xmlDictComputeFastKey",
    "line": 437
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/dict.c",
    "line": 434,
    "size": null,
    "type": "long unsigned"
   },
   "kind": "struct",
   "name": "value",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522315/report.log",
   "testcase_size": 111
  },
  "input_reachability": [
   "name",
   "namelen",
   "seed"
  ],
  "osv_id": "ARVO-42522315",
  "project": "libxml2",
  "sites": [
   {
    "code": "value += *name | *name",
    "fn": "xmlDictComputeFastKey",
    "kind": "unknown",
    "line": 437,
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
   "entity_type": "long unsigned",
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
   "control_structures": "IF:48,IF:50",
   "fn": "xmlStrndup",
   "guard_count": 3,
   "guards": "cur == NULL | len < 0 | ret == NULL",
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
   "code": "memcpy(ret, cur, len)",
   "site": {
    "file": "/src/libxml2/xmlstring.c",
    "fn": "xmlStrndup",
    "line": 53
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/xmlstring.c",
    "line": 46,
    "size": null,
    "type": "xmlChar*"
   },
   "kind": "pointer",
   "name": "ret",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_ca2bfecea9c2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/ca2bfecea9c23f8d2e11741fff7c6a5372c56bb8/ARVO-42522507/report.log",
   "testcase_size": 752
  },
  "input_reachability": [
   "cur",
   "len"
  ],
  "osv_id": "ARVO-42522507",
  "project": "libxml2",
  "sites": [
   {
    "code": "memcpy(ret, cur, len)",
    "fn": "xmlStrndup",
    "kind": "unknown",
    "line": 53,
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
   "entity_type": "xmlChar*",
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
   "control_structures": "IF:5354,DO:5356,IF:5356,IF:5359,IF:5361,DO:5362,IF:5362,IF:5363,IF:5368,IF:5370,IF:5378,IF:5383",
   "fn": "xmlParseEntityDecl",
   "guard_count": 1,
   "guards": "ctxt->userData==ctxt",
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
   "code": "SKIP(6) | ctxt->input->cur += (6), ctxt->input->col += (6) | ctxt->input->cur += (6) | ctxt->input->cur",
   "site": {
    "file": "/src/libxml2/parser.c",
    "fn": "xmlParseEntityDecl",
    "line": 5362
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 5346,
    "size": null,
    "type": "xmlParserCtxtPtr"
   },
   "kind": "struct",
   "name": "ctxt",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_9ef2a9abf357.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/9ef2a9abf357f747c2fb03841b7f479cc0dfd3ef/ARVO-42522518/report.log",
   "testcase_size": 639
  },
  "input_reachability": [
   "ctxt"
  ],
  "osv_id": "ARVO-42522518",
  "project": "libxml2",
  "sites": [
   {
    "code": "SKIP(6) | ctxt->input->cur += (6), ctxt->input->col += (6) | ctxt->input->cur += (6) | ctxt->input->cur",
    "fn": "xmlParseEntityDecl",
    "kind": "unknown",
    "line": 5362,
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
   "entity_type": "xmlParserCtxtPtr",
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
   "control_structures": "IF:3352,IF:3362,WHILE:3366,IF:3372,IF:3374,IF:3381",
   "fn": "xmlParseName",
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
   "code": "in++",
   "site": {
    "file": "/src/libxml2/HTMLparser.c",
    "fn": "htmlParsePI",
    "line": 3371
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/HTMLparser.c",
    "line": 3345,
    "size": null,
    "type": "xmlChar*"
   },
   "kind": "pointer",
   "name": "in",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_b167c7314497.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/b167c7314497b6cb0d9a587a31874ae0d273ffaa/ARVO-42522530/report.log",
   "testcase_size": 373
  },
  "input_reachability": [],
  "osv_id": "ARVO-42522530",
  "project": "libxml2",
  "sites": [
   {
    "code": "in++",
    "fn": "htmlParsePI",
    "kind": "unknown",
    "line": 3371,
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
   "entity_type": "xmlChar*",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2751,IF:2754,IF:2758,IF:2764,WHILE:2768,IF:2772,IF:2780,WHILE:2785,IF:2786,IF:2791,IF:2804,IF:2805",
   "fn": "xmlSplitQName",
   "guard_count": 1,
   "guards": "cur == NULL",
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
   "code": "cur[2] == 'l' | cur[2] | cur[3] == ':' | cur[3]",
   "site": {
    "file": "/src/libxml2/HTMLparser.c",
    "fn": "htmlParseHTMLAttribute",
    "line": 2759
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/HTMLparser.c",
    "line": 2748,
    "size": null,
    "type": "xmlChar*"
   },
   "kind": "pointer",
   "name": "cur",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_20f5c73457df.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/20f5c73457df065df21bf25aa081a0a4cd028046/ARVO-42525210/report.log",
   "testcase_size": 994
  },
  "input_reachability": [
   "name",
   "prefix"
  ],
  "osv_id": "ARVO-42525210",
  "project": "libxml2",
  "sites": [
   {
    "code": "cur[2] == 'l' | cur[2] | cur[3] == ':' | cur[3]",
    "fn": "htmlParseHTMLAttribute",
    "kind": "unknown",
    "line": 2759,
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
   "entity_type": "xmlChar*",
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
   "fn": "dissect_zcl_read_attr_struct",
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
    "file": "/src/wireshark/epan/dissectors/packet-zbee-zcl.c",
    "fn": "dissect_zcl_read_attr_struct",
    "line": 1748
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_855c445d14fe.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/wireshark/address/855c445d14feca90a1568a033f754f8e69313776/ARVO-42530289/report.log",
   "testcase_size": 952
  },
  "input_reachability": [],
  "osv_id": "ARVO-42530289",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "dissect_zcl_read_attr_struct",
    "kind": "unknown",
    "line": 1748,
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
   "control_structures": "DO:469,FOR:471,DO:472,DO:475",
   "fn": "xmlDictHashName",
   "guard_count": 1,
   "guards": "i < maxLen",
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
   "code": "i = 0 | i < maxLen && data[i] | i < maxLen | data[i]",
   "site": {
    "file": "/src/libxml2/dict.c",
    "fn": "xmlDictHashName",
    "line": 471
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/dict.c",
    "line": 467,
    "size": null,
    "type": "size_t"
   },
   "kind": "struct",
   "name": "i",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_4e23892cf04c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/4e23892cf04cdbe470b4e09c81cc1ed79c86fd10/ARVO-42531092/report.log",
   "testcase_size": 207
  },
  "input_reachability": [
   "seed",
   "data",
   "maxLen",
   "plen"
  ],
  "osv_id": "ARVO-42531092",
  "project": "libxml2",
  "sites": [
   {
    "code": "i = 0 | i < maxLen && data[i] | i < maxLen | data[i]",
    "fn": "xmlDictHashName",
    "kind": "unknown",
    "line": 471,
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
   "entity_type": "size_t",
   "is_signed": null,
   "ptr_origin": "assignment"
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
   "fn": "igraph_dl_yylex",
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
    "file": "/src/igraph/build/src/io/parsers/dl-lexer.c",
    "fn": "igraph_dl_yylex",
    "line": 3536
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
   "cpg": "/root/gyx/mutator_create/cpg_files/igraph_74b2e25f02b8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/igraph/address/74b2e25f02b82b583ee6c38c52e024337571f443/ARVO-42533290/report.log",
   "testcase_size": 2
  },
  "input_reachability": [],
  "osv_id": "ARVO-42533290",
  "project": "igraph",
  "sites": [
   {
    "code": null,
    "fn": "igraph_dl_yylex",
    "kind": "unknown",
    "line": 3536,
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
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "vte_write_debug",
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
   "code": "",
   "site": {
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "fn": "vte_write_debug",
    "line": 514
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
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2016-5.log",
   "testcase_size": 4874
  },
  "input_reachability": [],
  "osv_id": "OSV-2016-5",
  "project": "libtsm",
  "sites": [
   {
    "code": "",
    "fn": "vte_write_debug",
    "kind": "unknown",
    "line": 514,
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
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "vte_write_debug",
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
   "code": "",
   "site": {
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "fn": "vte_write_debug",
    "line": 514
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
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2017-121.log",
   "testcase_size": 2
  },
  "input_reachability": [],
  "osv_id": "OSV-2017-121",
  "project": "libtsm",
  "sites": [
   {
    "code": "",
    "fn": "vte_write_debug",
    "kind": "unknown",
    "line": 514,
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
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "vte_write_debug",
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
   "code": "",
   "site": {
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "fn": "vte_write_debug",
    "line": 514
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
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2017-157.log",
   "testcase_size": 2
  },
  "input_reachability": [],
  "osv_id": "OSV-2017-157",
  "project": "libtsm",
  "sites": [
   {
    "code": "",
    "fn": "vte_write_debug",
    "kind": "unknown",
    "line": 514,
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
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "vte_write_debug",
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
   "code": "",
   "site": {
    "file": "/src/libtsm/src/tsm/tsm-vte.c",
    "fn": "vte_write_debug",
    "line": 514
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
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2017-167.log",
   "testcase_size": 1920
  },
  "input_reachability": [],
  "osv_id": "OSV-2017-167",
  "project": "libtsm",
  "sites": [
   {
    "code": "",
    "fn": "vte_write_debug",
    "kind": "unknown",
    "line": 514,
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