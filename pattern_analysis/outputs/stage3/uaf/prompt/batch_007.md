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
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/flac/oss-fuzz/../src/metaflac/options.c",
    "fn": "append_new_operation",
    "line": 744
   },
   "size_bytes": 1200,
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
   "fn": "parse_options",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 1200,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/flac/src/metaflac/options.c",
    "fn": "parse_options",
    "line": 256
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/flac_6633d2f9bfdb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/flac/address/6633d2f9bfdba89e646d2169f5d8c1e9b168d972/ARVO-42526958/report.log",
   "testcase_size": 159
  },
  "input_reachability": [],
  "osv_id": "ARVO-42526958",
  "project": "flac",
  "sites": [
   {
    "code": null,
    "fn": "safe_realloc_",
    "kind": "free",
    "line": 207,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "parse_options",
    "kind": "unknown",
    "line": 256,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/igraph/build/src/io/parsers/pajek-lexer.c",
    "fn": "igraph_pajek_yyalloc",
    "line": 2736
   },
   "size_bytes": 16386,
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
   "fn": "dupl_str_len",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 16386,
    "width": 3
   },
   "code": null,
   "site": {
    "file": "/src/igraph/src/io/pajek-parser.y",
    "fn": "dupl_str_len",
    "line": 633
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/igraph_bfcfac20d6c4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/igraph/address/bfcfac20d6c465b860312f2c237b6f75a814c53e/ARVO-42529511/report.log",
   "testcase_size": 16625
  },
  "input_reachability": [],
  "osv_id": "ARVO-42529511",
  "project": "igraph",
  "sites": [
   {
    "code": null,
    "fn": "dupl_str_len",
    "kind": "unknown",
    "line": 633,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "igraph_pajek_yyrealloc",
    "kind": "free",
    "line": 2751,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/igraph/build/src/io/parsers/pajek-lexer.c",
    "fn": "igraph_pajek_yyalloc",
    "line": 2736
   },
   "size_bytes": 16386,
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
   "fn": "dupl_str_len",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 16386,
    "width": 11
   },
   "code": null,
   "site": {
    "file": "/src/igraph/src/io/pajek-parser.y",
    "fn": "dupl_str_len",
    "line": 633
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/igraph_bfcfac20d6c4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/igraph/address/bfcfac20d6c465b860312f2c237b6f75a814c53e/ARVO-42529532/report.log",
   "testcase_size": 16427
  },
  "input_reachability": [],
  "osv_id": "ARVO-42529532",
  "project": "igraph",
  "sites": [
   {
    "code": null,
    "fn": "dupl_str_len",
    "kind": "unknown",
    "line": 633,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "igraph_pajek_yyrealloc",
    "kind": "free",
    "line": 2751,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libredwg/src/decode.c",
    "fn": "dwg_add_object",
    "line": 4735
   },
   "size_bytes": 172032,
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
   "fn": "dxf_tables_read",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 172032,
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/libredwg/src/in_dxf.c",
    "fn": "dxf_tables_read",
    "line": 11738
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_a06d461bf19a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libredwg/address/a06d461bf19a9542204ad9761f2b38dc57c9d23d/ARVO-42530320/report.log",
   "testcase_size": 147107
  },
  "input_reachability": [],
  "osv_id": "ARVO-42530320",
  "project": "libredwg",
  "sites": [
   {
    "code": null,
    "fn": "dwg_add_object",
    "kind": "free",
    "line": 4746,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "dxf_tables_read",
    "kind": "unknown",
    "line": 11738,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_file_new",
    "line": 619
   },
   "size_bytes": 464,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:850,IF:853,IF:859,IF:865,FOR:866,ELSE:867,FOR:868,WHILE:875,FOR:876,FOR:878,IF:880,IF:892",
   "fn": "list_sort_quicksort",
   "guard_count": 11,
   "guards": "left != pivot | right != pivot | left != pivot",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 464,
    "width": 8
   },
   "code": "left != pivot && (l->attrs.comparator(left->data, pivot- | left != pivot | l->attrs.comparator(left->data, pivot->data) * -versus < | l->attrs.comparator(left->data, pivot->data) * -versus",
   "site": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-authentic.c",
    "fn": "authentic_emu_update_tokeninfo",
    "line": 876
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-authentic.c",
    "line": 842,
    "size": null,
    "type": "list_entry_s*"
   },
   "kind": "pointer",
   "name": "left",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_bfe896ae5d66.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/opensc/address/bfe896ae5d6604478d822a83030c165cac5bce9c/ARVO-42530963/report.log",
   "testcase_size": 1352
  },
  "input_reachability": [
   "l",
   "versus",
   "fel",
   "lel"
  ],
  "osv_id": "ARVO-42530963",
  "project": "opensc",
  "sites": [
   {
    "code": null,
    "fn": "sc_file_free",
    "kind": "free",
    "line": 643,
    "origin": "report:freed_by"
   },
   {
    "code": "left != pivot && (l->attrs.comparator(left->data, pivot- | left != pivot | l->attrs.comparator(left->data, pivot->data) * -versus < | l->attrs.comparator(left->data, pivot->data) * -versus",
    "fn": "authentic_emu_update_tokeninfo",
    "kind": "unknown",
    "line": 876,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "list_entry_s*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/fuzz/fuzz.c",
    "fn": "xmlFuzzMalloc",
    "line": 81
   },
   "size_bytes": 8193,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:427,IF:428,IF:430,IF:433,IF:438",
   "fn": "xmlSAX2ResolveEntity",
   "guard_count": 4,
   "guards": "ctx == NULL | ctxt->input != NULL | base == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 8193,
    "width": 1
   },
   "code": "ctx == NULL",
   "site": {
    "file": "/src/libxml2/HTMLparser.c",
    "fn": "htmlCurrentChar",
    "line": 427
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/HTMLparser.c",
    "line": 420,
    "size": null,
    "type": "void*"
   },
   "kind": "pointer",
   "name": "ctx",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_8e13133dbd2c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/8e13133dbd2c10e8a498235a62f9beceb19b87a1/ARVO-42531126/report.log",
   "testcase_size": 4243
  },
  "input_reachability": [
   "ctx"
  ],
  "osv_id": "ARVO-42531126",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlFuzzRealloc",
    "kind": "free",
    "line": 96,
    "origin": "report:freed_by"
   },
   {
    "code": "ctx == NULL",
    "fn": "htmlCurrentChar",
    "kind": "unknown",
    "line": 427,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "void*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/fuzz/fuzz.c",
    "fn": "xmlFuzzMalloc",
    "line": 81
   },
   "size_bytes": 48,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2738,IF:2739,IF:2742,IF:2745",
   "fn": "xmlRemoveID",
   "guard_count": 2,
   "guards": "attr == NULL | table == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 48,
    "width": 8
   },
   "code": "xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | attr->id->value | attr->id",
   "site": {
    "file": "/src/libxml2/valid.c",
    "fn": "xmlRemoveID",
    "line": 2745
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/valid.c",
    "line": 2736,
    "size": null,
    "type": "xmlIDTablePtr"
   },
   "kind": "struct",
   "name": "table",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_e45a4d711500.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/e45a4d711500298dfc7ee8f630acc18c71f14795/ARVO-42531532/report.log",
   "testcase_size": 5039
  },
  "input_reachability": [
   "doc",
   "attr"
  ],
  "osv_id": "ARVO-42531532",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlFreeID",
    "kind": "free",
    "line": 2503,
    "origin": "report:freed_by"
   },
   {
    "code": "xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | attr->id->value | attr->id",
    "fn": "xmlRemoveID",
    "kind": "unknown",
    "line": 2745,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "xmlIDTablePtr",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_file_add_acl_entry",
    "line": 545
   },
   "size_bytes": 16,
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
   "fn": "cac_parse_ACA_service",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 16,
    "width": 4
   },
   "code": "CAC_TAG_APPLET_FAMILY",
   "site": {
    "file": "/src/opensc/src/libopensc/card-iasecc.c",
    "fn": "iasecc_delete_file",
    "line": 1565
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_773fcc6bd0d0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/opensc/address/773fcc6bd0d047aa629dd297e87244ca3add5b16/ARVO-42531837/report.log",
   "testcase_size": 331
  },
  "input_reachability": [],
  "osv_id": "ARVO-42531837",
  "project": "opensc",
  "sites": [
   {
    "code": null,
    "fn": "sc_file_clear_acl_entries",
    "kind": "free",
    "line": 611,
    "origin": "report:freed_by"
   },
   {
    "code": "CAC_TAG_APPLET_FAMILY",
    "fn": "iasecc_delete_file",
    "kind": "unknown",
    "line": 1565,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libxml2/fuzz/fuzz.c",
    "fn": "xmlFuzzMalloc",
    "line": 81
   },
   "size_bytes": 120,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:5902,DO:5904,IF:5904,IF:5906,DO:5909,IF:5909,IF:5910,IF:5915,IF:5921,WHILE:5922,IF:5927,IF:5930",
   "fn": "xmlParseAttributeListDecl",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 120,
    "width": 8
   },
   "code": "xmlFatalErrMsg(ctxt, XML_ERR_SPACE_REQUIRED,",
   "site": {
    "file": "/src/libxml2/valid.c",
    "fn": "xmlValidatePopElement",
    "line": 5937
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/valid.c",
    "line": 5897,
    "size": null,
    "type": "xmlParserCtxtPtr"
   },
   "kind": "struct",
   "name": "ctxt",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_e45a4d711500.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/e45a4d711500298dfc7ee8f630acc18c71f14795/ARVO-42532360/report.log",
   "testcase_size": 180
  },
  "input_reachability": [
   "ctxt"
  ],
  "osv_id": "ARVO-42532360",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlTextReaderFreeNode",
    "kind": "free",
    "line": 421,
    "origin": "report:freed_by"
   },
   {
    "code": "xmlFatalErrMsg(ctxt, XML_ERR_SPACE_REQUIRED,",
    "fn": "xmlValidatePopElement",
    "kind": "unknown",
    "line": 5937,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "xmlParserCtxtPtr",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/fuzz/fuzz.c",
    "fn": "xmlFuzzMalloc",
    "line": 81
   },
   "size_bytes": 24,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2738,IF:2739,IF:2742,IF:2745",
   "fn": "xmlRemoveID",
   "guard_count": 2,
   "guards": "attr == NULL | table == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 24,
    "width": 4
   },
   "code": "xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | attr->id->value | attr->id",
   "site": {
    "file": "/src/libxml2/valid.c",
    "fn": "xmlRemoveID",
    "line": 2745
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/valid.c",
    "line": 2736,
    "size": null,
    "type": "xmlIDTablePtr"
   },
   "kind": "struct",
   "name": "table",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_e45a4d711500.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/e45a4d711500298dfc7ee8f630acc18c71f14795/ARVO-42532747/report.log",
   "testcase_size": 124
  },
  "input_reachability": [
   "doc",
   "attr"
  ],
  "osv_id": "ARVO-42532747",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlFreeID",
    "kind": "free",
    "line": 2503,
    "origin": "report:freed_by"
   },
   {
    "code": "xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | xmlHashRemoveEntry(table, attr->id->value, xmlFreeIDTabl | attr->id->value | attr->id",
    "fn": "xmlRemoveID",
    "kind": "unknown",
    "line": 2745,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "xmlIDTablePtr",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": false,
   "site": {
    "file": "/src/libredwg/src/in_json.c",
    "fn": "json_fixed_string",
    "line": 479
   },
   "size_bytes": 75,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:449,IF:449,IF:449,IF:451,GOTO:452,IF:453,IF:455,IF:455,IF:457,IF:457,IF:457,IF:462",
   "fn": "json_fixed_string",
   "guard_count": 1,
   "guards": "l > len",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 75,
    "width": 11
   },
   "code": "memcpy (str, &dat->chain[t->start], len) | &dat->chain[t->start] | dat->chain[t->start] | dat->chain",
   "site": {
    "file": "/src/libredwg/src/in_json.c",
    "fn": "json_fixed_string",
    "line": 490
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/in_json.c",
    "line": 447,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "str",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_6d082fd0b2c6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libredwg/address/6d082fd0b2c6c33914cbdc943370b9a0a5dd3ef0/ARVO-42533886/report.log",
   "testcase_size": 52
  },
  "input_reachability": [
   "dat",
   "len"
  ],
  "osv_id": "ARVO-42533886",
  "project": "libredwg",
  "sites": [
   {
    "code": "calloc (len + 1, 1)",
    "fn": "json_fixed_string",
    "kind": "calloc",
    "line": 447,
    "origin": "cpg"
   },
   {
    "code": null,
    "fn": "json_fixed_string",
    "kind": "free",
    "line": 476,
    "origin": "report:freed_by"
   },
   {
    "code": "realloc (str, dlen)",
    "fn": "json_fixed_string",
    "kind": "realloc",
    "line": 479,
    "origin": "cpg"
   },
   {
    "code": "memcpy (str, &dat->chain[t->start], len) | &dat->chain[t->start] | dat->chain[t->start] | dat->chain",
    "fn": "json_fixed_string",
    "kind": "unknown",
    "line": 490,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/fuzz/fuzz.c",
    "fn": "xmlFuzzMalloc",
    "line": 81
   },
   "size_bytes": 48,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:8446,IF:8454,IF:8459,IF:8467,FOR:8473,IF:8474,IF:8502,IF:8509,IF:8514,ELSE:8519,IF:8524,IF:8527",
   "fn": "xmlDOMWrapNSNormAcquireNormalizedNs",
   "guard_count": 19,
   "guards": "doc == NULL | ns == NULL | retNs == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 48,
    "width": 8
   },
   "code": "IS_STR_XML(ns->prefix) | ns->prefix | (ns->prefix != NULL) && (ns->prefix[0] == 'x') && (ns->p | (ns->prefix != NULL) && (ns->prefix[0] == 'x') && (ns->p",
   "site": {
    "file": "/src/libxml2/tree.c",
    "fn": "xmlDOMWrapNSNormAcquireNormalizedNs",
    "line": 8454
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/tree.c",
    "line": 8436,
    "size": null,
    "type": "xmlNsPtr"
   },
   "kind": "struct",
   "name": "ns",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_d4d1f3f33d6d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/d4d1f3f33d6d4a5e31511281637a857944946e65/ARVO-42533922/report.log",
   "testcase_size": 22
  },
  "input_reachability": [
   "doc",
   "ns",
   "retNs",
   "nsMap"
  ],
  "osv_id": "ARVO-42533922",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlFreeNs",
    "kind": "free",
    "line": 794,
    "origin": "report:freed_by"
   },
   {
    "code": "IS_STR_XML(ns->prefix) | ns->prefix | (ns->prefix != NULL) && (ns->prefix[0] == 'x') && (ns->p | (ns->prefix != NULL) && (ns->prefix[0] == 'x') && (ns->p",
    "fn": "xmlDOMWrapNSNormAcquireNormalizedNs",
    "kind": "unknown",
    "line": 8454,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "xmlNsPtr",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/fuzz/fuzz.c",
    "fn": "xmlFuzzMalloc",
    "line": 81
   },
   "size_bytes": 48,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:3918,IF:3919,IF:3921,ELSE:3923,IF:3923,ELSE:3925,IF:3925,ELSE:3927,IF:3927,ELSE:3930,IF:3931,IF:3934",
   "fn": "xmlCopyPropInternal",
   "guard_count": 13,
   "guards": "cur == NULL | target != NULL | target != NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 48,
    "width": 8
   },
   "code": "res = xmlSearchNsSafe(target, cur->ns->prefix, &ns) | xmlSearchNsSafe(target, cur->ns->prefix, &ns) | cur->ns->prefix | cur->ns",
   "site": {
    "file": "/src/libxml2/tree.c",
    "fn": "xmlCopyPropInternal",
    "line": 3938
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/tree.c",
    "line": 4012,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "res",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_d4d1f3f33d6d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/d4d1f3f33d6d4a5e31511281637a857944946e65/ARVO-42533950/report.log",
   "testcase_size": 21
  },
  "input_reachability": [
   "doc",
   "target",
   "cur"
  ],
  "osv_id": "ARVO-42533950",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlFreeNs",
    "kind": "free",
    "line": 794,
    "origin": "report:freed_by"
   },
   {
    "code": "res = xmlSearchNsSafe(target, cur->ns->prefix, &ns) | xmlSearchNsSafe(target, cur->ns->prefix, &ns) | cur->ns->prefix | cur->ns",
    "fn": "xmlCopyPropInternal",
    "kind": "unknown",
    "line": 3938,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/hdf5/src/H5FL.c",
    "fn": "H5FL__malloc",
    "line": 237
   },
   "size_bytes": 8,
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
   "fn": "H5FL__blk_gc_list",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 8,
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/hdf5/src/H5FL.c",
    "fn": "H5FL__blk_gc_list",
    "line": 1200
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42534222/report.log",
   "testcase_size": 1808
  },
  "input_reachability": [],
  "osv_id": "ARVO-42534222",
  "project": "hdf5",
  "sites": [
   {
    "code": null,
    "fn": "H5FL__blk_gc_list",
    "kind": "unknown",
    "line": 1200,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "H5FL__blk_gc_list",
    "kind": "free",
    "line": 1203,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libxml2/xmlmemory.c",
    "fn": "xmlMemMalloc",
    "line": 110
   },
   "size_bytes": 88,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1917,IF:1920,IF:1924",
   "fn": "xmlCharEncCloseFunc",
   "guard_count": 1,
   "guards": "handler == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 88,
    "width": 4
   },
   "code": "handler->flags & XML_HANDLER_STATIC | handler->flags | XML_HANDLER_STATIC",
   "site": {
    "file": "/src/libxml2/encoding.c",
    "fn": "xmlCharEncCloseFunc",
    "line": 1920
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/encoding.c",
    "line": 1916,
    "size": null,
    "type": "xmlCharEncodingHandler*"
   },
   "kind": "pointer",
   "name": "handler",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_36ea881b9d92.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/36ea881b9d92166568b1d107181a05f673fd4ab1/ARVO-42537493/report.log",
   "testcase_size": 24
  },
  "input_reachability": [
   "handler"
  ],
  "osv_id": "ARVO-42537493",
  "project": "libxml2",
  "sites": [
   {
    "code": "handler->flags & XML_HANDLER_STATIC | handler->flags | XML_HANDLER_STATIC",
    "fn": "xmlCharEncCloseFunc",
    "kind": "unknown",
    "line": 1920,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "xmlCharEncCloseFunc",
    "kind": "free",
    "line": 1928,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "xmlCharEncodingHandler*",
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