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
  "osv_id": "ARVO-42486724",
  "project": "open62541",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "size",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/plugins/ua_nodestore_hashmap.c",
    "line": 447,
    "size": null,
    "type": "UA_UInt32"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "UA_memoryManager_malloc",
    "file": "/src/open62541/tests/fuzz/custom_memory_manager.c",
    "line": 112
   },
   "size_expr": null,
   "size_bytes": 3104,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 58,
    "fn": "UA_ServerConfig_clean",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 447,
    "fn": "UA_NodeMap_delete",
    "code": "size = ns->size | ns->size",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "UA_NodeMap_delete",
    "file": "/src/open62541/plugins/ua_nodestore_hashmap.c",
    "line": 447
   },
   "code": "size = ns->size | ns->size",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 3104
   }
  },
  "context": {
   "fn": "UA_NodeMap_delete",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < size",
   "guard_count": 1,
   "control_structures": "FOR:449,IF:450,FOR:460"
  },
  "call_chain": [],
  "types": {
   "entity_type": "UA_UInt32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "context"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/ee275e79310280a71fad3b21f6d430c0c046091b/ARVO-42486724/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_ee275e793102.cpg",
   "testcase_size": 5
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
   "loc_size": 3104,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "UA_NodeMap_delete--UA_Server_new--LLVMFuzzerTestOneInput",
   "region_size": 3104
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "size = ns->size",
     "line": 447
    }
   ],
   "entity_decl": {
    "line": 447,
    "type": "UA_UInt32"
   },
   "entity_name_cpg": "size",
   "func_lines": [
    444,
    464
   ],
   "func_params": {
    "names": [
     "context"
    ],
    "types": [
     "void*"
    ]
   },
   "guards": [
    {
     "code": "i < size",
     "line": 449
    },
    {
     "code": "slots[i].entry > UA_NODEMAP_TOMBSTONE",
     "line": 450
    },
    {
     "code": "slots[i].entry->refCount == 0",
     "line": 452
    },
    {
     "code": "i < ns->referenceTypeCounter",
     "line": 460
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "size = ns->size",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ns->size",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "size",
    "ns"
   ],
   "osv_id": "ARVO-42486724",
   "sites": [
    {
     "args": "ns->slots",
     "callee": "UA_free",
     "code": "UA_free(ns->slots)",
     "line": 457
    },
    {
     "args": "ns",
     "callee": "UA_free",
     "code": "UA_free(ns)",
     "line": 463
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "UA_ServerConfig_clean",
   "use_fn": "UA_NodeMap_delete"
  }
 },
 {
  "osv_id": "ARVO-42486883",
  "project": "libxml2",
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
    "fn": "xmlNewDocPI",
    "file": "/src/libxml2/tree.c",
    "line": 2179
   },
   "size_expr": null,
   "size_bytes": 120,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 507,
    "fn": "xmlTextReaderFreeNode",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1484,
    "fn": "xmlTextReaderRead",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlTextReaderRead",
    "file": "/src/libxml2/xmlreader.c",
    "line": 1484
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 120
   }
  },
  "context": {
   "fn": "xmlTextReaderRead",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/00ed736eecf93aeab49089abb06e0e5fc0e7e091/ARVO-42486883/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_00ed736eecf9.cpg",
   "testcase_size": 102
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
   "loc_size": 120,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "xmlTextReaderRead--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
   "region_size": 120
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
   "osv_id": "ARVO-42486883",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xmlTextReaderFreeNode",
   "use_fn": "xmlTextReaderRead"
  }
 },
 {
  "osv_id": "ARVO-42487244",
  "project": "libxml2",
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
    "fn": "xmlNewNodeEatName",
    "file": "/src/libxml2/tree.c",
    "line": 2283
   },
   "size_expr": null,
   "size_bytes": 120,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 569,
    "fn": "xmlTextReaderFreeNode",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 3760,
    "fn": "xmlXPathNodeSetAdd",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlXPathNodeSetAdd",
    "file": "/src/libxml2/xpath.c",
    "line": 3760
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 120
   }
  },
  "context": {
   "fn": "xmlXPathNodeSetAdd",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/f0fd1b67fc883a24cdd039abb3d4fe4696104d72/ARVO-42487244/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_f0fd1b67fc88.cpg",
   "testcase_size": 93
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
   "loc_size": 120,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "xmlXPathNodeSetAdd--xmlXPathGetElementsByIds--xmlXPathIdFunction",
   "region_size": 120
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
     "p2"
    ],
    "types": [
     "ANY",
     "ANY"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42487244",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xmlTextReaderFreeNode",
   "use_fn": "xmlXPathNodeSetAdd"
  }
 },
 {
  "osv_id": "ARVO-42487785",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "node",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/tree.c",
    "line": 4192,
    "size": null,
    "type": "xmlNodePtr"
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "xmlNewText",
    "file": "/src/libxml2/tree.c",
    "line": 2447
   },
   "size_expr": null,
   "size_bytes": 120,
   "cross_function": true,
   "size_expr_cpg": "sizeof(xmlNode)",
   "size_expr_cpg_callee": "xmlMalloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 481,
    "fn": "xmlTextReaderFreeNodeList",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 4197,
    "fn": "xmlStaticCopyNode",
    "code": "node->type",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlStaticCopyNode",
    "file": "/src/libxml2/tree.c",
    "line": 4197
   },
   "code": "node->type",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 120
   }
  },
  "context": {
   "fn": "xmlStaticCopyNode",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "node == NULL",
   "guard_count": 1,
   "control_structures": "IF:4196,SWITCH:4197,BREAK:4208,IF:4235,IF:4244,ELSE:4246,IF:4246,ELSE:4248,IF:4248,ELSE:4250,IF:4250,IF:4251"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlNodePtr",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "node",
   "doc",
   "parent"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/f0fd1b67fc883a24cdd039abb3d4fe4696104d72/ARVO-42487785/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_f0fd1b67fc88.cpg",
   "testcase_size": 249
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
   "loc_size": 120,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "xmlStaticCopyNode--xmlCopyNode--xmlXIncludeLoadTxt",
   "region_size": 120
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 4192,
    "type": "xmlNodePtr"
   },
   "entity_name_cpg": "node",
   "func_lines": [
    4191,
    4342
   ],
   "func_params": {
    "names": [
     "node",
     "doc",
     "parent",
     "extended"
    ],
    "types": [
     "xmlNodePtr",
     "xmlDocPtr",
     "xmlNodePtr",
     "int"
    ]
   },
   "guards": [
    {
     "code": "node == NULL",
     "line": 4196
    },
    {
     "code": "ret == NULL",
     "line": 4235
    },
    {
     "code": "node->name == xmlStringText",
     "line": 4244
    },
    {
     "code": "node->name == xmlStringTextNoenc",
     "line": 4246
    },
    {
     "code": "node->name == xmlStringComment",
     "line": 4248
    },
    {
     "code": "node->name != NULL",
     "line": 4250
    },
    {
     "code": "doc != NULL",
     "line": 4251
    },
    {
     "code": "doc->dict != NULL",
     "line": 4251
    },
    {
     "code": "node->type != XML_ELEMENT_NODE",
     "line": 4256
    },
    {
     "code": "node->content != NULL",
     "line": 4257
    },
    {
     "code": "node->type != XML_ENTITY_REF_NODE",
     "line": 4258
    },
    {
     "code": "node->type != XML_XINCLUDE_END",
     "line": 4259
    },
    {
     "code": "node->type != XML_XINCLUDE_START",
     "line": 4260
    },
    {
     "code": "node->type == XML_ELEMENT_NODE",
     "line": 4263
    },
    {
     "code": "parent != NULL",
     "line": 4266
    },
    {
     "code": "tmp != ret",
     "line": 4279
    },
    {
     "code": "node->type == XML_ELEMENT_NODE",
     "line": 4285
    },
    {
     "code": "node->type == XML_XINCLUDE_START",
     "line": 4286
    },
    {
     "code": "node->nsDef != NULL",
     "line": 4286
    },
    {
     "code": "node->ns != NULL",
     "line": 4289
    },
    {
     "code": "ns == NULL",
     "line": 4293
    },
    {
     "code": "ns != NULL",
     "line": 4300
    },
    {
     "code": "root->parent != NULL",
     "line": 4303
    },
    {
     "code": "node->type == XML_ELEMENT_NODE",
     "line": 4315
    },
    {
     "code": "node->type == XML_XINCLUDE_START",
     "line": 4316
    },
    {
     "code": "node->properties != NULL",
     "line": 4316
    },
    {
     "code": "node->type == XML_ENTITY_REF_NODE",
     "line": 4318
    },
    {
     "code": "doc == NULL",
     "line": 4319
    },
    {
     "code": "node->doc != doc",
     "line": 4319
    },
    {
     "code": "node->children != NULL",
     "line": 4331
    },
    {
     "code": "extended != 2",
     "line": 4331
    },
    {
     "code": "(ret) != NULL",
     "line": 4333
    },
    {
     "code": "ulccur == NULL",
     "line": 4333
    },
    {
     "code": "ulccur->next != NULL",
     "line": 4333
    },
    {
     "code": "parent == NULL",
     "line": 4338
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "node->type",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "node"
   ],
   "osv_id": "ARVO-42487785",
   "sites": [
    {
     "args": "sizeof(xmlNode)",
     "callee": "xmlMalloc",
     "code": "xmlMalloc(sizeof(xmlNode))",
     "line": 4234
    },
    {
     "args": "node->name",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(node->name)",
     "line": 4254
    },
    {
     "args": "node->content",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(node->content)",
     "line": 4261
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xmlTextReaderFreeNodeList",
   "use_fn": "xmlStaticCopyNode"
  }
 },
 {
  "osv_id": "ARVO-42488049",
  "project": "leptonica",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "fpix",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/fpix1.c",
    "line": 518,
    "size": null,
    "type": "FPIX*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fpixCreate",
    "file": "/src/leptonica/src/fpix1.c",
    "line": 179
   },
   "size_expr": null,
   "size_bytes": 32,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 398,
    "fn": "fpixDestroy",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 526,
    "fn": "fpixChangeRefcount",
    "code": "fpix->refcount += delta | fpix->refcount",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "fpixChangeRefcount",
    "file": "/src/leptonica/src/fpix1.c",
    "line": 526
   },
   "code": "fpix->refcount += delta | fpix->refcount",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 32
   }
  },
  "context": {
   "fn": "fpixChangeRefcount",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:523"
  },
  "call_chain": [],
  "types": {
   "entity_type": "FPIX*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "fpix",
   "delta"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/leptonica/address/90ec70fd43222d66d4c8d2af93e8c4acc54192d4/ARVO-42488049/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_90ec70fd4322.cpg",
   "testcase_size": 48
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
   "loc_size": 32,
   "loc_offset": 12,
   "loc_kind": "region",
   "dedup_token": "fpixChangeRefcount--fpixDestroy--LLVMFuzzerTestOneInput",
   "region_size": 32
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 518,
    "type": "FPIX*"
   },
   "entity_name_cpg": "fpix",
   "func_lines": [
    517,
    528
   ],
   "func_params": {
    "names": [
     "fpix",
     "delta"
    ],
    "types": [
     "FPIX*",
     "l_int32"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "fpix->refcount += delta",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "fpix->refcount",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "fpix",
    "delta"
   ],
   "osv_id": "ARVO-42488049",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "fpixDestroy",
   "use_fn": "fpixChangeRefcount"
  }
 },
 {
  "osv_id": "ARVO-42488143",
  "project": "fluent-bit",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "head",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 736,
    "type": "mk_list*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "flb_malloc",
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "line": 62
   },
   "size_expr": null,
   "size_bytes": 16,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 122,
    "fn": "flb_free",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 743,
    "fn": "flb_parser_decoder_list_destroy",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "flb_parser_decoder_list_destroy",
    "file": "/src/fluent-bit/src/flb_parser_decoder.c",
    "line": 743
   },
   "code": "mk_list_foreach_safe(head, tmp, list)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 16
   }
  },
  "context": {
   "fn": "flb_parser_decoder_list_destroy",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/fluent-bit/address/1b262cebff01a2d54c7dab8ff5d3d8e340faed30/ARVO-42488143/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_1b262cebff01.cpg",
   "testcase_size": 100
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
   "loc_size": 16,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "flb_parser_decoder_list_destroy--LLVMFuzzerTestOneInput--fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
   "region_size": 16
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 736,
    "type": "mk_list*"
   },
   "entity_name_cpg": "head",
   "func_lines": [
    733,
    763
   ],
   "func_params": {
    "names": [
     "list"
    ],
    "types": [
     "mk_list*"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "mk_list_foreach_safe(head, tmp, list)",
     "name": "mk_list_foreach_safe",
     "nargs": 3
    }
   ],
   "line_ids": [
    "head",
    "tmp",
    "list"
   ],
   "osv_id": "ARVO-42488143",
   "sites": [
    {
     "args": "dec_rule",
     "callee": "flb_free",
     "code": "flb_free(dec_rule)",
     "line": 751
    },
    {
     "args": "dec",
     "callee": "flb_free",
     "code": "flb_free(dec)",
     "line": 757
    },
    {
     "args": "list",
     "callee": "flb_free",
     "code": "flb_free(list)",
     "line": 761
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "flb_free",
   "use_fn": "flb_parser_decoder_list_destroy"
  }
 },
 {
  "osv_id": "ARVO-42488833",
  "project": "leptonica",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "pix",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/pix1.c",
    "line": 1305,
    "size": null,
    "type": "PIX*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pixCreateHeader",
    "file": "/src/leptonica/src/pix1.c",
    "line": 541
   },
   "size_expr": null,
   "size_bytes": 64,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 653,
    "fn": "pixFree",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1313,
    "fn": "pixChangeRefcount",
    "code": "pix->refcount += delta | pix->refcount",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixChangeRefcount",
    "file": "/src/leptonica/src/pix1.c",
    "line": 1313
   },
   "code": "pix->refcount += delta | pix->refcount",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 64
   }
  },
  "context": {
   "fn": "pixChangeRefcount",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1310"
  },
  "call_chain": [],
  "types": {
   "entity_type": "PIX*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "pix",
   "delta"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/leptonica/address/8d7717457caf7960a8b6cbac762c69b5001039c2/ARVO-42488833/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_8d7717457caf.cpg",
   "testcase_size": 32
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
   "loc_offset": 20,
   "loc_kind": "region",
   "dedup_token": "pixChangeRefcount--pixFree--pixDestroy",
   "region_size": 64
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1305,
    "type": "PIX*"
   },
   "entity_name_cpg": "pix",
   "func_lines": [
    1304,
    1315
   ],
   "func_params": {
    "names": [
     "pix",
     "delta"
    ],
    "types": [
     "PIX*",
     "l_int32"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "pix->refcount += delta",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "pix->refcount",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pix",
    "delta"
   ],
   "osv_id": "ARVO-42488833",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "pixFree",
   "use_fn": "pixChangeRefcount"
  }
 },
 {
  "osv_id": "ARVO-42489816",
  "project": "openvswitch",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "encap",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 4323,
    "type": "ofpact_encap*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "xmalloc",
    "file": "/src/openvswitch/lib/util.c",
    "line": 123
   },
   "size_expr": null,
   "size_bytes": 64,
   "cross_function": true
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
    "line": 4352,
    "fn": "decode_NXAST_RAW_ENCAP",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "decode_NXAST_RAW_ENCAP",
    "file": "/src/openvswitch/lib/ofp-actions.c",
    "line": 4352
   },
   "code": "encap->n_props = n_props",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": 64
   }
  },
  "context": {
   "fn": "decode_NXAST_RAW_ENCAP",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openvswitch/address/418a7a84245f5fbe589dd1267463fc9ba27a1dd6/ARVO-42489816/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_418a7a84245f.cpg",
   "testcase_size": 72
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
   "loc_offset": 58,
   "loc_kind": "region",
   "dedup_token": "decode_NXAST_RAW_ENCAP--ofpacts_decode--ofpacts_pull_openflow_actions__",
   "region_size": 64
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "encap = ofpact_put_ENCAP(out)",
     "line": 4329
    },
    {
     "code": "encap->ofpact.raw = NXAST_RAW_ENCAP",
     "line": 4330
    },
    {
     "code": "encap->new_pkt_type = nae->new_pkt_type",
     "line": 4339
    },
    {
     "code": "encap->hdr_size = ntohs(nae->hdr_size)",
     "line": 4340
    },
    {
     "code": "encap->n_props = n_props",
     "line": 4352
    }
   ],
   "entity_decl": {
    "line": 4323,
    "type": "ofpact_encap*"
   },
   "entity_name_cpg": "encap",
   "func_lines": [
    4318,
    4357
   ],
   "func_params": {
    "names": [
     "nae",
     "ofp_version",
     "out"
    ],
    "types": [
     "nx_action_encap*",
     "ofp_version",
     "ofpbuf*"
    ]
   },
   "guards": [
    {
     "code": "props_len > 0",
     "line": 4345
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "encap->n_props = n_props",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "encap->n_props",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "encap",
    "n_props"
   ],
   "osv_id": "ARVO-42489816",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "xrealloc",
   "use_fn": "decode_NXAST_RAW_ENCAP"
  }
 },
 {
  "osv_id": "ARVO-42491511",
  "project": "igraph",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "v",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 461,
    "type": "igraph_vector_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "igraph_read_graph_gml",
    "file": "/src/igraph/src/io/gml.c",
    "line": 367
   },
   "size_expr": null,
   "size_bytes": 24,
   "cross_function": false,
   "size_expr_cpg": "3",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": null,
    "fn": "igraph_i_gml_destroy_attrs",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 462,
    "fn": "igraph_read_graph_gml",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "igraph_read_graph_gml",
    "file": "/src/igraph/src/io/gml.c",
    "line": 462
   },
   "code": "VECTOR(*v)[id] = igraph_i_gml_toreal(node, j)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 24
   }
  },
  "context": {
   "fn": "igraph_read_graph_gml",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/igraph/address/c83b6ecdc3fe18dd7fb0cdf0786f43462db2c7d8/ARVO-42491511/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/igraph_c83b6ecdc3fe.cpg",
   "testcase_size": 10214
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
   "loc_size": 24,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "igraph_read_graph_gml--LLVMFuzzerTestOneInput--main",
   "region_size": 24
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*v = (igraph_vector_t *)atrec->value",
     "line": 419
    },
    {
     "code": "*v = (igraph_strvector_t *)atrec->value",
     "line": 422
    },
    {
     "code": "*v = (igraph_vector_t *)atrec->value",
     "line": 461
    },
    {
     "code": "*v = (igraph_strvector_t *)atrec->value",
     "line": 464
    }
   ],
   "entity_decl": {
    "line": 461,
    "type": "igraph_vector_t*"
   },
   "entity_name_cpg": "v",
   "func_lines": [
    160,
    491
   ],
   "func_params": {
    "names": [
     "graph",
     "instream"
    ],
    "types": [
     "igraph_t*",
     "FILE*"
    ]
   },
   "guards": [
    {
     "code": "i != 0",
     "line": 189
    },
    {
     "code": "context.errmsg[0] != 0",
     "line": 190
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 197
    },
    {
     "code": "igraph_gml_tree_type(context.tree, i) == IGRAPH_I_GML_TREE_INTEGER",
     "line": 202
    },
    {
     "code": "igraph_gml_tree_get_integer(context.tree, i) != 1",
     "line": 203
    },
    {
     "code": "gidx == -1",
     "line": 211
    },
    {
     "code": "igraph_gml_tree_type(context.tree, gidx) !=",
     "line": 214
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 225
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 226
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 227
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 228
    },
    {
     "code": "igraph_gml_tree_type(gtree, i) == IGRAPH_I_GML_TREE_INTEGER",
     "line": 232
    },
    {
     "code": "igraph_gml_tree_get_integer(gtree, i) == 1",
     "line": 233
    },
    {
     "code": "i < igraph_gml_tree_length(gtree)",
     "line": 240
    },
    {
     "code": "igraph_gml_tree_type(gtree, i) != IGRAPH_I_GML_TREE_TREE",
     "line": 248
    },
    {
     "code": "j < igraph_gml_tree_length(node)",
     "line": 253
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 256
    },
    {
     "code": "trieid == triesize",
     "line": 257
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 264
    },
    {
     "code": "type == IGRAPH_I_GML_TREE_INTEGER",
     "line": 266
    },
    {
     "code": "type == IGRAPH_I_GML_TREE_REAL",
     "line": 266
    },
    {
     "code": "type1 == IGRAPH_ATTRIBUTE_NUMERIC",
     "line": 276
    },
    {
     "code": "type2 == IGRAPH_I_GML_TREE_STRING",
     "line": 276
    },
    {
     "code": "igraph_gml_tree_type(node, j) != IGRAPH_I_GML_TREE_INTEGER",
     "line": 283
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 288
    },
    {
     "code": "igraph_gml_tree_type(gtree, i) != IGRAPH_I_GML_TREE_TREE",
     "line": 299
    },
    {
     "code": "j < igraph_gml_tree_length(edge)",
     "line": 304
    },
    {
     "code": "igraph_gml_tree_type(edge, j) != IGRAPH_I_GML_TREE_INTEGER",
     "line": 308
    },
    {
     "code": "igraph_gml_tree_type(edge, j) != IGRAPH_I_GML_TREE_INTEGER",
     "line": 314
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 320
    },
    {
     "code": "trieid == triesize",
     "line": 321
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 328
    },
    {
     "code": "type == IGRAPH_I_GML_TREE_INTEGER",
     "line": 330
    },
    {
     "code": "type == IGRAPH_I_GML_TREE_REAL",
     "line": 330
    },
    {
     "code": "type1 == IGRAPH_ATTRIBUTE_NUMERIC",
     "line": 340
    },
    {
     "code": "type2 == IGRAPH_I_GML_TREE_STRING",
     "line": 340
    },
    {
     "code": "igraph_trie_size(&trie) != no_of_nodes",
     "line": 358
    },
    {
     "code": "i < igraph_vector_ptr_size(&vattrs)",
     "line": 363
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_NUMERIC",
     "line": 366
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 369
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_STRING",
     "line": 370
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 373
    },
    {
     "code": "i < igraph_vector_ptr_size(&eattrs)",
     "line": 379
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_NUMERIC",
     "line": 382
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 385
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_STRING",
     "line": 386
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 389
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 396
    },
    {
     "code": "(p = igraph_gml_tree_find(gtree, \"edge\", p + 1)) != -1",
     "line": 398
    },
    {
     "code": "j < igraph_gml_tree_length(edge)",
     "line": 404
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_NUMERIC",
     "line": 418
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_STRING",
     "line": 421
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 424
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 431
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 433
    },
    {
     "code": "igraph_trie_size(&trie) != no_of_nodes",
     "line": 434
    },
    {
     "code": "i < igraph_gml_tree_length(gtree)",
     "line": 442
    },
    {
     "code": "j < igraph_gml_tree_length(node)",
     "line": 453
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_NUMERIC",
     "line": 460
    },
    {
     "code": "type == IGRAPH_ATTRIBUTE_STRING",
     "line": 463
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 466
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 480
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 481
    },
    {
     "code": "igraph_i_ret != 0",
     "line": 483
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "VECTOR(*v)[id] = igraph_i_gml_toreal(node, j)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "VECTOR(*v)[id]",
     "name": "VECTOR",
     "nargs": 1
    },
    {
     "code": "*v",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "((*v).stor_begin)[id]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "(*v).stor_begin",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "*v",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "igraph_i_gml_toreal(node, j)",
     "name": "igraph_i_gml_toreal",
     "nargs": 2
    }
   ],
   "line_ids": [
    "v",
    "id",
    "node",
    "j"
   ],
   "osv_id": "ARVO-42491511",
   "sites": [
    {
     "args": "3",
     "callee": "<operator>.alloc",
     "code": "*attrs[3]",
     "line": 174
    },
    {
     "args": "100",
     "callee": "<operator>.alloc",
     "code": "cname[100]",
     "line": 242
    },
    {
     "args": "1 ;; igraph_attribute_record_t",
     "callee": "igraph_Calloc",
     "code": "igraph_Calloc(1, igraph_attribute_record_t)",
     "line": 259
    },
    {
     "args": "(size_t)(1) ;; sizeof (igraph_attribute_record_t)",
     "callee": "calloc",
     "code": "calloc((size_t)(1), sizeof (igraph_attribute_record_t))",
     "line": 259
    },
    {
     "args": "name",
     "callee": "strdup",
     "code": "strdup(name)",
     "line": 265
    },
    {
     "args": "1 ;; igraph_attribute_record_t",
     "callee": "igraph_Calloc",
     "code": "igraph_Calloc(1, igraph_attribute_record_t)",
     "line": 323
    },
    {
     "args": "(size_t)(1) ;; sizeof (igraph_attribute_record_t)",
     "callee": "calloc",
     "code": "calloc((size_t)(1), sizeof (igraph_attribute_record_t))",
     "line": 323
    },
    {
     "args": "name",
     "callee": "strdup",
     "code": "strdup(name)",
     "line": 329
    },
    {
     "args": "1 ;; igraph_vector_t",
     "callee": "igraph_Calloc",
     "code": "igraph_Calloc(1, igraph_vector_t)",
     "line": 367
    },
    {
     "args": "(size_t)(1) ;; sizeof (igraph_vector_t)",
     "callee": "calloc",
     "code": "calloc((size_t)(1), sizeof (igraph_vector_t))",
     "line": 367
    },
    {
     "args": "1 ;; igraph_strvector_t",
     "callee": "igraph_Calloc",
     "code": "igraph_Calloc(1, igraph_strvector_t)",
     "line": 371
    },
    {
     "args": "(size_t)(1) ;; sizeof (igraph_strvector_t)",
     "callee": "calloc",
     "code": "calloc((size_t)(1), sizeof (igraph_strvector_t))",
     "line": 371
    },
    {
     "args": "1 ;; igraph_vector_t",
     "callee": "igraph_Calloc",
     "code": "igraph_Calloc(1, igraph_vector_t)",
     "line": 383
    },
    {
     "args": "(size_t)(1) ;; sizeof (igraph_vector_t)",
     "callee": "calloc",
     "code": "calloc((size_t)(1), sizeof (igraph_vector_t))",
     "line": 383
    },
    {
     "args": "1 ;; igraph_strvector_t",
     "callee": "igraph_Calloc",
     "code": "igraph_Calloc(1, igraph_strvector_t)",
     "line": 387
    },
    {
     "args": "(size_t)(1) ;; sizeof (igraph_strvector_t)",
     "callee": "calloc",
     "code": "calloc((size_t)(1), sizeof (igraph_strvector_t))",
     "line": 387
    },
    {
     "args": "100",
     "callee": "<operator>.alloc",
     "code": "name[100]",
     "line": 401
    },
    {
     "args": "100",
     "callee": "<operator>.alloc",
     "code": "name[100]",
     "line": 444
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "igraph_i_gml_destroy_attrs",
   "use_fn": "igraph_read_graph_gml"
  }
 },
 {
  "osv_id": "ARVO-42491546",
  "project": "igraph",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "v",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 261,
    "type": "igraph_vector_ptr_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "igraph_i_gml_make_numeric",
    "file": "/src/igraph/src/io/gml-parser.y",
    "line": 192
   },
   "size_expr": null,
   "size_bytes": 88,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 189,
    "fn": "igraph_gml_tree_destroy",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 264,
    "fn": "igraph_vector_ptr_size",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "igraph_vector_ptr_size",
    "file": "/src/igraph/src/core/vector_ptr.c",
    "line": 264
   },
   "code": "v->end - v->stor_begin",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 88
   }
  },
  "context": {
   "fn": "igraph_vector_ptr_size",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/igraph/address/883bd139af3775d7f90f144c9038a6cb9a28f309/ARVO-42491546/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/igraph_883bd139af37.cpg",
   "testcase_size": 9
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
   "loc_size": 88,
   "loc_offset": 72,
   "loc_kind": "region",
   "dedup_token": "igraph_vector_ptr_size--igraph_gml_tree_destroy--igraph_i_gml_parsedata_destroy",
   "region_size": 88
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 261,
    "type": "igraph_vector_ptr_t*"
   },
   "entity_name_cpg": "v",
   "func_lines": [
    261,
    265
   ],
   "func_params": {
    "names": [
     "v"
    ],
    "types": [
     "igraph_vector_ptr_t*"
    ]
   },
   "guards": [
    {
     "code": "v != NULL",
     "line": 262
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "v->end - v->stor_begin",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "v->end",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "v->stor_begin",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "v"
   ],
   "osv_id": "ARVO-42491546",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "igraph_gml_tree_destroy",
   "use_fn": "igraph_vector_ptr_size"
  }
 },
 {
  "osv_id": "ARVO-42491876",
  "project": "c-blosc2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cMem",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/decompress/zstd_ddict.c",
    "line": 215,
    "size": null,
    "type": "ZSTD_customMem"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "ZSTD_malloc",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/common/zstd_common.c",
    "line": 60
   },
   "size_expr": null,
   "size_bytes": 26720,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 81,
    "fn": "ZSTD_free",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 215,
    "fn": "ZSTD_freeDDict",
    "code": "cMem = ddict->cMem | ddict->cMem",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_freeDDict",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/decompress/zstd_ddict.c",
    "line": 215
   },
   "code": "cMem = ddict->cMem | ddict->cMem",
   "access": {
    "dir": "READ",
    "width": 24,
    "region_bytes": 26720
   }
  },
  "context": {
   "fn": "ZSTD_freeDDict",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "ddict==NULL",
   "guard_count": 1,
   "control_structures": "IF:214"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ZSTD_customMem",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ddict"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/c-blosc2/address/0739de6c94ca57367192250cfad779cca1349088/ARVO-42491876/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_0739de6c94ca.cpg",
   "testcase_size": 36366
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
   "loc_size": 26720,
   "loc_offset": 26696,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ZSTD_freeDDict--blosc2_free_ctx",
   "region_size": 26720
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cMem = ddict->cMem",
     "line": 215
    }
   ],
   "entity_decl": {
    "line": 215,
    "type": "ZSTD_customMem"
   },
   "entity_name_cpg": "cMem",
   "func_lines": [
    212,
    220
   ],
   "func_params": {
    "names": [
     "ddict"
    ],
    "types": [
     "ZSTD_DDict*"
    ]
   },
   "guards": [
    {
     "code": "ddict==NULL",
     "line": 214
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "cMem = ddict->cMem",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ddict->cMem",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cMem",
    "ddict"
   ],
   "osv_id": "ARVO-42491876",
   "sites": [
    {
     "args": "ddict->dictBuffer ;; cMem",
     "callee": "ZSTD_free",
     "code": "ZSTD_free(ddict->dictBuffer, cMem)",
     "line": 216
    },
    {
     "args": "ddict ;; cMem",
     "callee": "ZSTD_free",
     "code": "ZSTD_free(ddict, cMem)",
     "line": 217
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "ZSTD_free",
   "use_fn": "ZSTD_freeDDict"
  }
 },
 {
  "osv_id": "ARVO-42493388",
  "project": "selinux",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1619,
    "type": "cil_classperms*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "cil_malloc",
    "file": "/src/selinux/libsepol/src/../cil/src/cil_mem.c",
    "line": 40
   },
   "size_expr": null,
   "size_bytes": 32,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 695,
    "fn": "cil_destroy_classperms",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1620,
    "fn": "__cil_verify_classperms",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "__cil_verify_classperms",
    "file": "/src/selinux/libsepol/cil/src/cil_verify.c",
    "line": 1620
   },
   "code": "((cil_tree_node *)(((cil_symtab_datum *)(cp->class))->nodes->head->data))->flavor",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 32
   }
  },
  "context": {
   "fn": "__cil_verify_classperms",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/selinux/address/0451adebdf153eee1f69914141311114a0130982/ARVO-42493388/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/selinux_0451adebdf15.cpg",
   "testcase_size": 125659
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
   "loc_size": 32,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "__cil_verify_classperms--__cil_verify_classpermission--__cil_pre_verify_helper",
   "region_size": 32
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*cp = curr->data",
     "line": 1619
    },
    {
     "code": "*cp = cp_set->set",
     "line": 1632
    }
   ],
   "entity_decl": {
    "line": 1619,
    "type": "cil_classperms*"
   },
   "entity_name_cpg": "cp",
   "func_lines": [
    1582,
    1644
   ],
   "func_params": {
    "names": [
     "classperms",
     "orig",
     "parent",
     "cur",
     "flavor",
     "steps",
     "limit"
    ],
    "types": [
     "cil_list*",
     "cil_symtab_datum*",
     "cil_symtab_datum*",
     "cil_symtab_datum*",
     "cil_flavor",
     "unsigned",
     "unsigned"
    ]
   },
   "guards": [
    {
     "code": "classperms == NULL",
     "line": 1592
    },
    {
     "code": "flavor == CIL_MAP_PERM",
     "line": 1593
    },
    {
     "code": "steps > 0",
     "line": 1601
    },
    {
     "code": "orig == cur",
     "line": 1601
    },
    {
     "code": "flavor == CIL_MAP_PERM",
     "line": 1602
    },
    {
     "code": "steps > limit",
     "line": 1610
    },
    {
     "code": "curr != NULL",
     "line": 1617
    },
    {
     "code": "curr->flavor == CIL_CLASSPERMS",
     "line": 1618
    },
    {
     "code": "FLAVOR(cp->class) != CIL_CLASS",
     "line": 1620
    },
    {
     "code": "i != NULL",
     "line": 1622
    },
    {
     "code": "rc != SEPOL_OK",
     "line": 1625
    },
    {
     "code": "rc != SEPOL_OK",
     "line": 1634
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "FLAVOR(cp->class) != CIL_CLASS",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "FLAVOR(cp->class)",
     "name": "FLAVOR",
     "nargs": 1
    },
    {
     "code": "cp->class",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "((cil_tree_node *)(((cil_symtab_datum *)(cp->class))->nodes->head->data))->flavor",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(cil_tree_node *)(((cil_symtab_datum *)(cp->class))->nodes->head->data)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "((cil_symtab_datum *)(cp->class))->nodes->head->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "((cil_symtab_datum *)(cp->class))->nodes->head",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "((cil_symtab_datum *)(cp->class))->nodes",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(cil_symtab_datum *)(cp->class)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "cp->class",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cp",
    "CIL_CLASS"
   ],
   "osv_id": "ARVO-42493388",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "cil_destroy_classperms",
   "use_fn": "__cil_verify_classperms"
  }
 },
 {
  "osv_id": "ARVO-42493450",
  "project": "c-blosc2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "idest",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": 40,
    "size": null,
    "type": "int32_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib32/libc.so.6+0x18646)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": 148,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": null,
    "fn": "__libc_start_main (/lib32/libc.so.6+0x18646)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 44,
    "fn": "sw32_",
    "code": "idest = *(int32_t *)pa | *(int32_t *)pa | (int32_t *)pa",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sw32_",
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": 44
   },
   "code": "idest = *(int32_t *)pa | *(int32_t *)pa | (int32_t *)pa",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 148
   }
  },
  "context": {
   "fn": "sw32_",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:43,ELSE:46"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int32_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "pa"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/c-blosc2/address/969fb4cbb617801876fb5ddefc73778935ff1a56/ARVO-42493450/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_969fb4cbb617.cpg",
   "testcase_size": 148
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
   "loc_size": 148,
   "loc_offset": 130,
   "loc_kind": "region",
   "dedup_token": "sw32_--frame_get_lazychunk--frame_decompress_chunk",
   "region_size": 148
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "idest = *(int32_t *)pa",
     "line": 44
    }
   ],
   "entity_decl": {
    "line": 40,
    "type": "int32_t"
   },
   "entity_name_cpg": "idest",
   "func_lines": [
    39,
    60
   ],
   "func_params": {
    "names": [
     "pa"
    ],
    "types": [
     "void*"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "idest = *(int32_t *)pa",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*(int32_t *)pa",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(int32_t *)pa",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "idest",
    "pa"
   ],
   "osv_id": "ARVO-42493450",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "__libc_start_main (/lib32/libc.so.6+0x18646)",
   "use_fn": "sw32_"
  }
 },
 {
  "osv_id": "ARVO-42494623",
  "project": "selinux",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 51,
    "type": "cil_classpermission*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "cil_malloc",
    "file": "/src/selinux/libsepol/src/../cil/src/cil_mem.c",
    "line": 40
   },
   "size_expr": null,
   "size_bytes": 40,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 57,
    "fn": "cil_reset_classpermission",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 836,
    "fn": "cil_destroy_classpermission",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "cil_reset_classpermission",
    "file": "/src/selinux/libsepol/cil/src/cil_reset_ast.c",
    "line": 57
   },
   "code": "cil_reset_classperms_list(cp->classperms)",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 40
   }
  },
  "context": {
   "fn": "cil_reset_classpermission",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/selinux/address/0451adebdf153eee1f69914141311114a0130982/ARVO-42494623/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/selinux_0451adebdf15.cpg",
   "testcase_size": 123
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
   "loc_size": 40,
   "loc_offset": 32,
   "loc_kind": "region",
   "dedup_token": "cil_reset_classpermission--cil_reset_classperms_set--cil_reset_classperms_list",
   "region_size": 40
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 51,
    "type": "cil_classpermission*"
   },
   "entity_name_cpg": "cp",
   "func_lines": [
    51,
    58
   ],
   "func_params": {
    "names": [
     "cp"
    ],
    "types": [
     "cil_classpermission*"
    ]
   },
   "guards": [
    {
     "code": "cp == NULL",
     "line": 53
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "cil_reset_classperms_list(cp->classperms)",
     "name": "cil_reset_classperms_list",
     "nargs": 1
    },
    {
     "code": "cp->classperms",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cp"
   ],
   "osv_id": "ARVO-42494623",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "cil_destroy_classpermission",
   "use_fn": "cil_reset_classpermission"
  }
 },
 {
  "osv_id": "ARVO-42494732",
  "project": "libredwg",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "pair",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/in_dxf.c",
    "line": 12264,
    "size": null,
    "type": "Dxf_Pair*"
   }
  },
  "alloc": {
   "api": "calloc",
   "site": {
    "fn": "xcalloc",
    "file": "/src/libredwg/src/in_dxf.c",
    "line": 216
   },
   "size_expr": null,
   "size_bytes": 16,
   "cross_function": true,
   "size_expr_cpg": "80",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 515,
    "fn": "dxf_free_pair",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 12267,
    "fn": "dxf_objects_read",
    "code": "pair != NULL && pair->code == 0 && pair->value.s | pair != NULL && pair->code == 0 | pair != NULL | pair->code == 0",
    "origin": "report:crash"
   },
   {
    "code": "strdup (pair->value.s)",
    "fn": "dxf_objects_read",
    "kind": "strdup",
    "line": 12274,
    "origin": "cpg",
    "args": "pair->value.s"
   }
  ],
  "crash": {
   "site": {
    "fn": "dxf_objects_read",
    "file": "/src/libredwg/src/in_dxf.c",
    "line": 12267
   },
   "code": "pair != NULL && pair->code == 0 && pair->value.s | pair != NULL && pair->code == 0 | pair != NULL | pair->code == 0",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": 16
   }
  },
  "context": {
   "fn": "dxf_objects_read",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "pair != NULL | pair != NULL | pair != NULL",
   "guard_count": 4,
   "control_structures": "WHILE:12265,WHILE:12267,IF:12272,IF:12277,ELSE:12281,IF:12282,IF:12283,IF:12283,IF:12289,IF:12289"
  },
  "call_chain": [],
  "types": {
   "entity_type": "Dxf_Pair*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dat"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libredwg/address/ff69eeda665843f1a73f42b6ba82dad46dfde07c/ARVO-42494732/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_ff69eeda6658.cpg",
   "testcase_size": 256
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
   "loc_size": 16,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "dxf_objects_read--dwg_read_dxf--LLVMFuzzerTestOneInput",
   "region_size": 16
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*pair = dxf_read_pair (dat)",
     "line": 12264
    },
    {
     "code": "pair = new_object (name, dxfname, dat, dwg, 0, NULL)",
     "line": 12276
    },
    {
     "code": "pair = dxf_read_pair (dat)",
     "line": 12288
    },
    {
     "code": "pair = NULL",
     "line": 12289
    }
   ],
   "entity_decl": {
    "line": 12264,
    "type": "Dxf_Pair*"
   },
   "entity_name_cpg": "pair",
   "func_lines": [
    12260,
    12293
   ],
   "func_params": {
    "names": [
     "dat",
     "dwg"
    ],
    "types": [
     "Bit_Chain*restrict",
     "Dwg_Data*restrict"
    ]
   },
   "guards": [
    {
     "code": "pair != NULL",
     "line": 12265
    },
    {
     "code": "pair != NULL",
     "line": 12267
    },
    {
     "code": "pair->code == 0",
     "line": 12267
    },
    {
     "code": "pair != NULL",
     "line": 12282
    },
    {
     "code": "pair->code == 0",
     "line": 12282
    },
    {
     "code": "pair->code == 0",
     "line": 12282
    },
    {
     "code": "pair == NULL",
     "line": 12289
    },
    {
     "code": "pair->code == 0",
     "line": 12289
    },
    {
     "code": "pair->code == 0",
     "line": 12289
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "pair != NULL && pair->code == 0 && pair->value.s",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "pair != NULL && pair->code == 0",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "pair != NULL",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "pair->code == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "pair->code",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "pair->value.s",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "pair->value",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pair",
    "NULL"
   ],
   "osv_id": "ARVO-42494732",
   "sites": [
    {
     "args": "80",
     "callee": "<operator>.alloc",
     "code": "name[80]",
     "line": 12263
    },
    {
     "args": "pair->value.s",
     "callee": "strdup",
     "code": "strdup (pair->value.s)",
     "line": 12274
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair (pair)",
     "line": 12275
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair(pair)",
     "line": 12282
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair (pair)",
     "line": 12284
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair (pair)",
     "line": 12287
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair(pair)",
     "line": 12289
    },
    {
     "args": "pair",
     "callee": "dxf_free_pair",
     "code": "dxf_free_pair (pair)",
     "line": 12291
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "dxf_free_pair",
   "use_fn": "dxf_objects_read"
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