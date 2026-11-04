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
  "osv_id": "ARVO-42495340",
  "project": "assimp",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "writer",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Assimp::AMFImporter::ParseFile(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> > const&, Assimp::IOSystem*)",
    "file": "/src/assimp/code/AssetLib/AMF/AMFImporter.cpp",
    "line": 274
   },
   "size_expr": null,
   "size_bytes": 40,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 91,
    "fn": "Assimp::TXmlParser<pugi::xml_node>::clear()",
    "code": "writer.SetCurrentPos(chunk_start_pos + SIZE_OFFSET) | chunk_start_pos + SIZE_OFFSET",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 276,
    "fn": "Assimp::AMFImporter::ParseFile(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> > const&, Assimp::IOSystem*)",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "Assimp::TXmlParser<pugi::xml_node>::clear()",
    "file": "/src/assimp/include/assimp/XmlParser.h",
    "line": 91
   },
   "code": "writer.SetCurrentPos(chunk_start_pos + SIZE_OFFSET) | chunk_start_pos + SIZE_OFFSET",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 40
   }
  },
  "context": {
   "fn": "~ChunkWriter",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "head_pos > chunk_start_pos",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/assimp/address/91cb2947ace52bcd9d297171bd9b66f5203370b5/ARVO-42495340/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_91cb2947ace5.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 40,
   "loc_offset": 24,
   "loc_kind": "region",
   "dedup_token": "std::__1::vector<char, std::__1::allocator<char> >::size() const--std::__1::vector<char, std::__1::allocator<char> >::resize(unsigned long)--Assimp::TXmlParser<",
   "region_size": 40
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "writer",
   "func_lines": [
    85,
    94
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "Assimp.ChunkWriter"
    ]
   },
   "guards": [
    {
     "code": "head_pos > chunk_start_pos",
     "line": 88
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "writer.SetCurrentPos(chunk_start_pos + SIZE_OFFSET)",
     "name": "SetCurrentPos",
     "nargs": 2
    },
    {
     "code": "chunk_start_pos + SIZE_OFFSET",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "writer",
    "chunk_start_pos",
    "SIZE_OFFSET"
   ],
   "osv_id": "ARVO-42495340",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "Assimp::AMFImporter::ParseFile(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char> > const&, Assimp::IOSystem*)",
   "use_fn": "Assimp::TXmlParser<pugi::xml_node>::clear()"
  }
 },
 {
  "osv_id": "ARVO-42496387",
  "project": "wasm3",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "next",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 205,
    "type": "IM3Module",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "m3_ParseModule",
    "file": "/src/wasm3/source/m3_parse.c",
    "line": 581
   },
   "size_expr": null,
   "size_bytes": 160,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 205,
    "fn": "ForEachModule",
    "code": null,
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 219,
    "fn": "_FreeModule",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "ForEachModule",
    "file": "/src/wasm3/source/m3_env.c",
    "line": 205
   },
   "code": "next = module->next",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 160
   }
  },
  "context": {
   "fn": "ForEachModule",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/wasm3/address/4f0b769629fa8f2ba6e7baa9195ef9f1bf5dc310/ARVO-42496387/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wasm3_4f0b769629fa.cpg",
   "testcase_size": 101
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
   "loc_size": 160,
   "loc_offset": 152,
   "loc_kind": "region",
   "dedup_token": "ForEachModule--Runtime_Release--m3_FreeRuntime",
   "region_size": 160
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "next = module->next",
     "line": 205
    }
   ],
   "entity_decl": {
    "line": 205,
    "type": "IM3Module"
   },
   "entity_name_cpg": "next",
   "func_lines": [
    197,
    214
   ],
   "func_params": {
    "names": [
     "i_runtime",
     "i_visitor",
     "i_info"
    ],
    "types": [
     "IM3Runtime",
     "ModuleVisitor",
     "void*"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "next = module->next",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "module->next",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "next",
    "module"
   ],
   "osv_id": "ARVO-42496387",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "_FreeModule",
   "use_fn": "ForEachModule"
  }
 },
 {
  "osv_id": "ARVO-42496484",
  "project": "serenity",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "used_by_prefix",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/serenity/AK/Atomic.h",
    "line": 235,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "AK::Vector<Shell::Parser::HeredocInitiationRecord, 0ul>::try_ensure_capacity(unsigned long)",
    "file": "/src/serenity/Meta/Lagom/build/../../../AK/Vector.h",
    "line": 567
   },
   "size_expr": null,
   "size_bytes": 120,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 120,
    "fn": "AK::Vector<Shell::Parser::HeredocInitiationRecord, 0ul>::clear()",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 246,
    "fn": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::load(AK::MemoryOrder) const volatile",
    "code": "used_by_prefix += 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::load(AK::MemoryOrder) const volatile",
    "file": "/src/serenity/AK/Atomic.h",
    "line": 246
   },
   "code": "used_by_prefix += 1",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 120
   }
  },
  "context": {
   "fn": "put_u64",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:228,IF:236,ELSE:240,IF:241,IF:244,IF:245,ELSE:247,IF:247,ELSE:249,IF:249,IF:286,ELSE:292"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/serenity/address/81eab1a9d108beabe477bc052aa1b219f36812ed/ARVO-42496484/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_81eab1a9d108.cpg",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fd",
   "shadow_legend_size": 21,
   "loc_size": 120,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::load(AK::MemoryOrder) const volatile--AK::RefPtr<AK::StringImpl, AK::RefPtrTraits<AK::StringImpl> >::as_ptr() con",
   "region_size": 120
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "used_by_prefix = 0",
     "line": 235
    },
    {
     "code": "used_by_prefix = 0",
     "line": 239
    }
   ],
   "entity_decl": {
    "line": 235,
    "type": "size_t"
   },
   "entity_name_cpg": "used_by_prefix",
   "func_lines": [
    216,
    313
   ],
   "func_params": {
    "names": [
     "value",
     "base",
     "prefix",
     "upper_case",
     "zero_pad",
     "align",
     "min_width",
     "fill",
     "sign_mode",
     "is_negative"
    ],
    "types": [
     "u64",
     "u8",
     "bool",
     "bool",
     "bool",
     "Align",
     "size_t",
     "char",
     "SignMode",
     "bool"
    ]
   },
   "guards": [
    {
     "code": "align == Align::Default",
     "line": 228
    },
    {
     "code": "Array<u8",
     "line": 231
    },
    {
     "code": "128> buffer",
     "line": 231
    },
    {
     "code": "align == Align::Right",
     "line": 236
    },
    {
     "code": "sign_mode != SignMode::OnlyIfNeeded",
     "line": 241
    },
    {
     "code": "base == 8",
     "line": 245
    },
    {
     "code": "base == 16",
     "line": 247
    },
    {
     "code": "base == 2",
     "line": 249
    },
    {
     "code": "align == Align::Left",
     "line": 286
    },
    {
     "code": "align == Align::Center",
     "line": 292
    },
    {
     "code": "align == Align::Right",
     "line": 300
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "used_by_prefix += 1",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    }
   ],
   "line_ids": [
    "used_by_prefix"
   ],
   "osv_id": "ARVO-42496484",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": true,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "AK::Vector<Shell::Parser::HeredocInitiationRecord, 0ul>::clear()",
   "use_fn": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::load(AK::MemoryOrder) const volatile"
  }
 },
 {
  "osv_id": "ARVO-42497067",
  "project": "libredwg",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
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
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 513,
    "fn": "dxf_free_pair",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 6317,
    "fn": "dwg_free_TABLEGEOMETRY_private",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dwg_free_TABLEGEOMETRY_private",
    "file": "/src/libredwg/src/dwg.spec",
    "line": 6317
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 16
   }
  },
  "context": {
   "fn": "dwg_free_TABLEGEOMETRY_private",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libredwg/address/7f525b96bb6db2989a9d296cda5d76aeb46f71af/ARVO-42497067/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_7f525b96bb6d.cpg",
   "testcase_size": 4096
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
   "loc_size": 16,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "dwg_free_TABLEGEOMETRY_private--dwg_free_TABLEGEOMETRY--dwg_free_variable_no_class",
   "region_size": 16
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
     "p4"
    ],
    "types": [
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
   "osv_id": "ARVO-42497067",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 3,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "dxf_free_pair",
   "use_fn": "dwg_free_TABLEGEOMETRY_private"
  }
 },
 {
  "osv_id": "ARVO-42497161",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "cur",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/tree.c",
    "line": 3012,
    "size": null,
    "type": "xmlNodePtr"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "xmlStaticCopyNode",
    "file": "/src/libxml2/tree.c",
    "line": 4234
   },
   "size_expr": null,
   "size_bytes": 120,
   "cross_function": true,
   "size_expr_cpg": "elem->content",
   "size_expr_cpg_callee": "xmlStrdup"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3013,
    "fn": "xmlAddNextSibling",
    "code": "(cur == NULL) || (cur->type == XML_NAMESPACE_DECL) | cur == NULL | cur->type == XML_NAMESPACE_DECL | cur->type",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 3819,
    "fn": "xmlFreeNode",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlAddNextSibling",
    "file": "/src/libxml2/tree.c",
    "line": 3013
   },
   "code": "(cur == NULL) || (cur->type == XML_NAMESPACE_DECL) | cur == NULL | cur->type == XML_NAMESPACE_DECL | cur->type",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 120
   }
  },
  "context": {
   "fn": "xmlAddNextSibling",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "cur == NULL | cur->type == XML_NAMESPACE_DECL | elem == NULL",
   "guard_count": 9,
   "control_structures": "IF:3013,IF:3020,IF:3028,IF:3038,IF:3039,IF:3044,ELSE:3055,IF:3055,IF:3059,IF:3066,IF:3068"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlNodePtr",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "cur",
   "elem"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/9de7b94d4ffbd11814008a5aa529b4ca77564921/ARVO-42497161/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_9de7b94d4ffb.cpg",
   "testcase_size": 1205
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
   "dedup_token": "xmlAddNextSibling--xmlXIncludeCopyRange--xmlXIncludeCopyXPointer",
   "region_size": 120
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "cur->next = elem",
     "line": 3065
    }
   ],
   "entity_decl": {
    "line": 3012,
    "type": "xmlNodePtr"
   },
   "entity_name_cpg": "cur",
   "func_lines": [
    3011,
    3071
   ],
   "func_params": {
    "names": [
     "cur",
     "elem"
    ],
    "types": [
     "xmlNodePtr",
     "xmlNodePtr"
    ]
   },
   "guards": [
    {
     "code": "cur == NULL",
     "line": 3013
    },
    {
     "code": "cur->type == XML_NAMESPACE_DECL",
     "line": 3013
    },
    {
     "code": "elem == NULL",
     "line": 3020
    },
    {
     "code": "elem->type == XML_NAMESPACE_DECL",
     "line": 3020
    },
    {
     "code": "cur == elem",
     "line": 3028
    },
    {
     "code": "elem->type == XML_TEXT_NODE",
     "line": 3038
    },
    {
     "code": "cur->type == XML_TEXT_NODE",
     "line": 3039
    },
    {
     "code": "cur->next != NULL",
     "line": 3044
    },
    {
     "code": "cur->next->type == XML_TEXT_NODE",
     "line": 3044
    },
    {
     "code": "cur->name == cur->next->name",
     "line": 3045
    },
    {
     "code": "elem->type == XML_ATTRIBUTE_NODE",
     "line": 3055
    },
    {
     "code": "elem->doc != cur->doc",
     "line": 3059
    },
    {
     "code": "elem->next != NULL",
     "line": 3066
    },
    {
     "code": "elem->parent != NULL",
     "line": 3068
    },
    {
     "code": "elem->parent->last == cur",
     "line": 3068
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "(cur == NULL) ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "cur == NULL",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "cur->type == XML_NAMESPACE_DECL",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "cur->type",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "cur",
    "NULL",
    "XML_NAMESPACE_DECL"
   ],
   "osv_id": "ARVO-42497161",
   "sites": [
    {
     "args": "elem",
     "callee": "xmlFreeNode",
     "code": "xmlFreeNode(elem)",
     "line": 3041
    },
    {
     "args": "elem->content",
     "callee": "xmlStrdup",
     "code": "xmlStrdup(elem->content)",
     "line": 3048
    },
    {
     "args": "tmp",
     "callee": "xmlFree",
     "code": "xmlFree(tmp)",
     "line": 3051
    },
    {
     "args": "elem",
     "callee": "xmlFreeNode",
     "code": "xmlFreeNode(elem)",
     "line": 3052
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 1,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "xmlFreeNode",
   "use_fn": "xmlAddNextSibling"
  }
 },
 {
  "osv_id": "ARVO-42497297",
  "project": "serenity",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "si",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/serenity/AK/Atomic.h",
    "line": 226,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "JS::HeapBlock::create_with_cell_size(JS::Heap&, unsigned long)",
    "file": "/src/serenity/Userland/Libraries/LibJS/Heap/HeapBlock.cpp",
    "line": 22
   },
   "size_expr": null,
   "size_bytes": 16384,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 35,
    "fn": "JS::HeapBlock::operator delete(void*)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 226,
    "fn": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::fetch_or(unsigned long, AK::MemoryOrder) volatile",
    "code": "si = str.length() - end.length() | str.length() - end.length() | str.length() | end.length()",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::fetch_or(unsigned long, AK::MemoryOrder) volatile",
    "file": "/src/serenity/AK/Atomic.h",
    "line": 226
   },
   "code": "si = str.length() - end.length() | str.length() - end.length() | str.length() | end.length()",
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": 16384
   }
  },
  "context": {
   "fn": "ends_with",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:213,IF:215,IF:217,IF:220,FOR:227,IF:228"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "str",
   "end"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/serenity/address/3bc3a7a23a96bf8a8f7bb46481dbbb4255435187/ARVO-42497297/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_3bc3a7a23a96.cpg",
   "testcase_size": 6624
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
   "loc_size": 16384,
   "loc_offset": 15600,
   "loc_kind": "region",
   "dedup_token": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::fetch_or(unsigned long, AK::MemoryOrder) volatile--AK::RefPtrTraits<AK::StringImpl>::lock(AK::Atomic<unsigned lon",
   "region_size": 16384
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "si = str.length() - end.length()",
     "line": 226
    }
   ],
   "entity_decl": {
    "line": 226,
    "type": "size_t"
   },
   "entity_name_cpg": "si",
   "func_lines": [
    211,
    232
   ],
   "func_params": {
    "names": [
     "str",
     "end",
     "case_sensitivity"
    ],
    "types": [
     "StringView&",
     "StringView&",
     "CaseSensitivity"
    ]
   },
   "guards": [
    {
     "code": "end.length() > str.length()",
     "line": 217
    },
    {
     "code": "case_sensitivity == CaseSensitivity::CaseSensitive",
     "line": 220
    },
    {
     "code": "ei < end.length()",
     "line": 227
    },
    {
     "code": "to_lowercase(str_chars[si]) != to_lowercase(end_chars[ei])",
     "line": 228
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "si = str.length() - end.length()",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "str.length() - end.length()",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "str.length()",
     "name": "length",
     "nargs": 1
    },
    {
     "code": "end.length()",
     "name": "length",
     "nargs": 1
    }
   ],
   "line_ids": [
    "si",
    "str",
    "end"
   ],
   "osv_id": "ARVO-42497297",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "JS::HeapBlock::operator delete(void*)",
   "use_fn": "AK::Atomic<unsigned long, (AK::MemoryOrder)5>::fetch_or(unsigned long, AK::MemoryOrder) volatile"
  }
 },
 {
  "osv_id": "ARVO-42497715",
  "project": "fluent-bit",
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
    "fn": "mk_mem_alloc_z",
    "file": "/src/fluent-bit/lib/monkey/mk_core/../include/monkey/mk_core/mk_memory.h",
    "line": 70
   },
   "size_expr": null,
   "size_bytes": 72,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 102,
    "fn": "mk_mem_free",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "multiline_parser_conf_file",
    "file": "/src/fluent-bit/src/flb_parser.c",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 72
   }
  },
  "context": {
   "fn": "multiline_parser_conf_file",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/fluent-bit/address/03f3339594bdb472315823db78ca209b7ba319fb/ARVO-42497715/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_03f3339594bd.cpg",
   "testcase_size": 1
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
   "loc_size": 72,
   "loc_offset": 64,
   "loc_kind": "region",
   "dedup_token": "multiline_parser_conf_file--flb_parser_conf_file--LLVMFuzzerTestOneInput",
   "region_size": 72
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    595,
    702
   ],
   "func_params": {
    "names": [
     "cfg",
     "fconf",
     "config"
    ],
    "types": [
     "char*",
     "mk_rconf*",
     "flb_config*"
    ]
   },
   "guards": [
    {
     "code": "strcasecmp(section->name, \"MULTILINE_PARSER\") != 0",
     "line": 625
    },
    {
     "code": "type == -1",
     "line": 644
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42497715",
   "sites": [
    {
     "args": "fconf",
     "callee": "mk_rconf_free",
     "code": "mk_rconf_free(fconf)",
     "line": 691
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "mk_mem_free",
   "use_fn": "multiline_parser_conf_file"
  }
 },
 {
  "osv_id": "ARVO-42497729",
  "project": "serenity",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "in1",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/serenity/AK/StringImpl.cpp",
    "line": 75,
    "size": null,
    "type": "u8"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "AK::StringImpl::create_uninitialized(unsigned long, char*&)",
    "file": "/src/serenity/AK/StringImpl.cpp",
    "line": 47
   },
   "size_expr": null,
   "size_bytes": 90,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 34,
    "fn": "AK::StringImpl::operator delete(void*)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 75,
    "fn": "AK::StringImpl::create(char const*, unsigned long, AK::ShouldChomp)",
    "code": "in1 = get(i + 1) | get(i + 1) | i + 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AK::StringImpl::create(char const*, unsigned long, AK::ShouldChomp)",
    "file": "/src/serenity/AK/StringImpl.cpp",
    "line": 75
   },
   "code": "in1 = get(i + 1) | get(i + 1) | i + 1",
   "access": {
    "dir": "READ",
    "width": 65,
    "region_bytes": 90
   }
  },
  "context": {
   "fn": "decode_base64",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < input.length()",
   "guard_count": 1,
   "control_structures": "FOR:70,IF:84,IF:86"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "input"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/serenity/address/280785f0fa47d07edd7bfe386a1afd712691f5a0/ARVO-42497729/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_280785f0fa47.cpg",
   "testcase_size": 12337
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
   "loc_size": 90,
   "loc_offset": 22,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--AK::StringImpl::create(char const*, unsigned long, AK::ShouldChomp)--AK::String::String(AK::StringView const&)",
   "region_size": 90
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "in1 = get(i + 1)",
     "line": 75
    }
   ],
   "entity_decl": {
    "line": 75,
    "type": "u8"
   },
   "entity_name_cpg": "in1",
   "func_lines": [
    53,
    94
   ],
   "func_params": {
    "names": [
     "input"
    ],
    "types": [
     "StringView&"
    ]
   },
   "guards": [
    {
     "code": "Vector<u8> output",
     "line": 67
    },
    {
     "code": "Vector<u8",
     "line": 67
    },
    {
     "code": "i < input.length()",
     "line": 70
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "in1 = get(i + 1)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "get(i + 1)",
     "name": "<operator>()",
     "nargs": 1
    },
    {
     "code": "i + 1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "in1",
    "get",
    "i"
   ],
   "osv_id": "ARVO-42497729",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "AK::StringImpl::operator delete(void*)",
   "use_fn": "AK::StringImpl::create(char const*, unsigned long, AK::ShouldChomp)"
  }
 },
 {
  "osv_id": "ARVO-42498085",
  "project": "libjxl",
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
    "fn": "__libcpp_operator_new<unsigned long>",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 235
   },
   "size_expr": null,
   "size_bytes": 32,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 90,
    "fn": "VoidRow",
    "code": "",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 1687,
    "fn": "emplace_back<unsigned long, unsigned long>",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "VoidRow",
    "file": "/src/libjxl/lib/jxl/image.h",
    "line": 90
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 32
   }
  },
  "context": {
   "fn": "VoidRow",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libjxl/address/dbf8653bf9c654c42406dab4b55c024f0d879cd8/ARVO-42498085/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_dbf8653bf9c6.cpg",
   "testcase_size": 60
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
   "loc_size": 32,
   "loc_offset": 24,
   "loc_kind": "region",
   "dedup_token": "get--VoidRow--Row",
   "region_size": 32
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
   "osv_id": "ARVO-42498085",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "emplace_back<unsigned long, unsigned long>",
   "use_fn": "VoidRow"
  }
 },
 {
  "osv_id": "ARVO-42500437",
  "project": "espeak-ng",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "n",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 2184,
    "type": "int",
    "size": null
   }
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "NewTranslator",
    "file": "/src/espeak-ng/src/libespeak-ng/tr_languages.c",
    "line": 241
   },
   "size_expr": null,
   "size_bytes": 14864,
   "cross_function": true,
   "size_expr_cpg": "40",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 284,
    "fn": "DeleteTranslator",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 2237,
    "fn": "TranslateRules",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "TranslateRules",
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "line": 2237
   },
   "code": "n = tr->groups2_count[c]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": 14864
   }
  },
  "context": {
   "fn": "TranslateRules",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/espeak-ng/address/0a713d52bbf3e061823d1a7f35e5303e7320f27a/ARVO-42500437/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0a713d52bbf3.cpg",
   "testcase_size": 10
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
   "loc_size": 14864,
   "loc_offset": 14304,
   "loc_kind": "region",
   "dedup_token": "TranslateRules--TranslateWord3--TranslateWord",
   "region_size": 14864
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "n = tr->groups2_count[c]",
     "line": 2237
    },
    {
     "code": "n = utf8_in(&letter, p-1)-1",
     "line": 2300
    }
   ],
   "entity_decl": {
    "line": 2184,
    "type": "int"
   },
   "entity_name_cpg": "n",
   "func_lines": [
    2171,
    2423
   ],
   "func_params": {
    "names": [
     "tr",
     "p_start",
     "phonemes",
     "ph_size",
     "end_phonemes",
     "word_flags",
     "dict_flags"
    ],
    "types": [
     "Translator*",
     "char*",
     "char*",
     "int",
     "char*",
     "int",
     "unsigned int*"
    ]
   },
   "guards": [
    {
     "code": "tr->data_dictrules == NULL",
     "line": 2198
    },
    {
     "code": "dict_flags != NULL",
     "line": 2201
    },
    {
     "code": "ix < (N_WORD_BYTES-1)",
     "line": 2204
    },
    {
     "code": "c == 0",
     "line": 2207
    },
    {
     "code": "(word_flags & FLAG_NO_TRACE) == 0",
     "line": 2212
    },
    {
     "code": "(c = p_start[ix]) != ' '",
     "line": 2216
    },
    {
     "code": "c != 0",
     "line": 2216
    },
    {
     "code": "ix < (sizeof(wordbuf)-1)",
     "line": 2216
    },
    {
     "code": "end_phonemes != NULL",
     "line": 2229
    },
    {
     "code": "(c = *p) != ' '",
     "line": 2232
    },
    {
     "code": "c != 0",
     "line": 2232
    },
    {
     "code": "tr->langopts.tone_numbers == 0",
     "line": 2238
    },
    {
     "code": "ix < 128",
     "line": 2257
    },
    {
     "code": "tr->groups3[ix] != NULL",
     "line": 2258
    },
    {
     "code": "n > 0",
     "line": 2264
    },
    {
     "code": "g < (g1+n)",
     "line": 2270
    },
    {
     "code": "tr->groups2_name[g] == c12",
     "line": 2271
    },
    {
     "code": "match2.points > 0",
     "line": 2276
    },
    {
     "code": "tr->groups1[c] != NULL",
     "line": 2293
    },
    {
     "code": "match1.points == 0",
     "line": 2299
    },
    {
     "code": "(option_sayas & 0x10) == 0",
     "line": 2299
    },
    {
     "code": "tr->letter_bits_offset > 0",
     "line": 2302
    },
    {
     "code": "letter == 0xe000+'('",
     "line": 2311
    },
    {
     "code": "pre_pause < tr->langopts.param[LOPT_BRACKET_PAUSE_ANNOUNCED]",
     "line": 2312
    },
    {
     "code": "pre_pause < tr->langopts.param[LOPT_BRACKET_PAUSE]",
     "line": 2316
    },
    {
     "code": "letter < N_REMOVE_ACCENT",
     "line": 2321
    },
    {
     "code": "(ix = remove_accent[letter-0xc0]) != 0",
     "line": 2321
    },
    {
     "code": "p[-2] != ' '",
     "line": 2323
    },
    {
     "code": "p[n] != ' '",
     "line": 2323
    },
    {
     "code": "(p[0] = p[n]) != ' '",
     "line": 2327
    },
    {
     "code": "n-- > 0",
     "line": 2328
    },
    {
     "code": "lookupwchar(diereses_list, letter) > 0",
     "line": 2330
    },
    {
     "code": "(alphabet = AlphabetFromChar(letter)) != NULL",
     "line": 2344
    },
    {
     "code": "alphabet->offset != tr->letter_bits_offset",
     "line": 2344
    },
    {
     "code": "tr->langopts.alt_alphabet == alphabet->offset",
     "line": 2345
    },
    {
     "code": "match1.points == 0",
     "line": 2358
    },
    {
     "code": "any_alpha > 1",
     "line": 2362
    },
    {
     "code": "p[wc_bytes-1] > ' '",
     "line": 2362
    },
    {
     "code": "dict_flags != NULL",
     "line": 2365
    },
    {
     "code": "match1.phonemes == NULL",
     "line": 2382
    },
    {
     "code": "match1.points > 0",
     "line": 2385
    },
    {
     "code": "match1.phonemes[0] == phonSWITCH",
     "line": 2389
    },
    {
     "code": "(word_flags & FLAG_DONT_SWITCH_TRANSLATOR) == 0",
     "line": 2389
    },
    {
     "code": "(word_flags & FLAG_NO_TRACE) == 0",
     "line": 2395
    },
    {
     "code": "match1.end_type != 0",
     "line": 2400
    },
    {
     "code": "end_phonemes != NULL",
     "line": 2400
    },
    {
     "code": "(match1.end_type & 0x7f) == 0",
     "line": 2405
    },
    {
     "code": "match1.del_fwd != NULL",
     "line": 2414
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "n = tr->groups2_count[c]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "tr->groups2_count[c]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "tr->groups2_count",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "n",
    "tr",
    "c"
   ],
   "osv_id": "ARVO-42500437",
   "sites": [
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "ph_buf[40]",
     "line": 2194
    },
    {
     "args": "N_WORD_BYTES",
     "callee": "<operator>.alloc",
     "code": "word_copy[N_WORD_BYTES]",
     "line": 2195
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "str_pause[2] = { phonPAUSE_NOLINK, 0 }",
     "line": 2196
    },
    {
     "args": "120",
     "callee": "<operator>.alloc",
     "code": "wordbuf[120]",
     "line": 2213
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "string[8]",
     "line": 2240
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "buf[40]",
     "line": 2241
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "DeleteTranslator",
   "use_fn": "TranslateRules"
  }
 },
 {
  "osv_id": "ARVO-42502063",
  "project": "harfbuzz",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "hb_realloc_impl",
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "line": 51
   },
   "size_expr": null,
   "size_bytes": 608,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 56,
    "fn": "hb_free_impl",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 711,
    "fn": "hb_resolve_overflows(hb_vector_t<hb_serialize_context_t::object_t*> const&, hb_serialize_context_t*)",
    "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE\t\t= 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hb_resolve_overflows(hb_vector_t<hb_serialize_context_t::object_t*> const&, hb_serialize_context_t*)",
    "file": "/src/harfbuzz/src/hb-repacker.hh",
    "line": 711
   },
   "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE\t\t= 0",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 608
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/harfbuzz/address/2bd911b8b49ac9e7cb0708b7ff5861cc3705e915/ARVO-42502063/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2bd911b8b49a.cpg",
   "testcase_size": 60417
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
   "loc_size": 608,
   "loc_offset": 108,
   "loc_kind": "region",
   "dedup_token": "hb_resolve_overflows(hb_vector_t<hb_serialize_context_t::object_t*> const&, hb_serialize_context_t*)--_repack(unsigned int, hb_serialize_context_t const&)--bool",
   "region_size": 608
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE\t\t= 0",
     "line": 711
    }
   ],
   "entity_name_cpg": "HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE",
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
     "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE\t\t= 0",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE"
   ],
   "osv_id": "ARVO-42502063",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": false,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "hb_free_impl",
   "use_fn": "hb_resolve_overflows(hb_vector_t<hb_serialize_context_t::object_t*> const&, hb_serialize_context_t*)"
  }
 },
 {
  "osv_id": "ARVO-42504387",
  "project": "open62541",
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
    "fn": "UA_SessionManager_createSession",
    "file": "/src/open62541/src/server/ua_session_manager.c",
    "line": 129
   },
   "size_expr": null,
   "size_bytes": 312,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 180,
    "fn": "processDelayedCallbacks",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 372,
    "fn": "UA_Subscription_answerPublishRequestsNoSubscription",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "UA_Subscription_answerPublishRequestsNoSubscription",
    "file": "/src/open62541/src/server/ua_subscription.c",
    "line": 372
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 312
   }
  },
  "context": {
   "fn": "UA_Subscription_answerPublishRequestsNoSubscription",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/6610fcecc0a920346d391b41e8973e403ae3f731/ARVO-42504387/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_6610fcecc0a9.cpg",
   "testcase_size": 1015
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
   "loc_size": 312,
   "loc_offset": 288,
   "loc_kind": "region",
   "dedup_token": "UA_Subscription_answerPublishRequestsNoSubscription--processDelayedCallbacks--UA_Server_run_shutdown",
   "region_size": 312
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    136,
    136
   ],
   "func_params": {
    "names": [
     "server",
     "session"
    ],
    "types": [
     "UA_Server*",
     "UA_Session*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42504387",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "processDelayedCallbacks",
   "use_fn": "UA_Subscription_answerPublishRequestsNoSubscription"
  }
 },
 {
  "osv_id": "ARVO-42504673",
  "project": "perfetto",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "fd_",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "perfetto::base::AlignedAlloc(unsigned long, unsigned long)",
    "file": "/work/build/../../src/perfetto/src/base/utils.cc",
    "line": 255
   },
   "size_expr": null,
   "size_bytes": 327680,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "free",
    "line": 265,
    "fn": "perfetto::base::AlignedFree(void*)",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 361,
    "fn": "perfetto::trace_processor::SliceTracker::GetStackHash(std::__1::vector<perfetto::trace_processor::SliceTracker::SliceInfo, std::__1::allocator<perfetto::trace_processor::SliceTracker::SliceInfo> > const&)",
    "code": "bind(*fd_, addr.addr(), addr.size) | *fd_ | addr.addr() | addr.size",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "perfetto::trace_processor::SliceTracker::GetStackHash(std::__1::vector<perfetto::trace_processor::SliceTracker::SliceInfo, std::__1::allocator<perfetto::trace_processor::SliceTracker::SliceInfo> > const&)",
    "file": "/src/perfetto/src/trace_processor/importers/common/slice_tracker.cc",
    "line": 361
   },
   "code": "bind(*fd_, addr.addr(), addr.size) | *fd_ | addr.addr() | addr.size",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": 327680
   }
  },
  "context": {
   "fn": "Bind",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:356,IF:358,IF:361"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "socket_name"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/perfetto/address/03cb3fd2f9c1b7475bf3838ecdf014b786b791f3/ARVO-42504673/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_03cb3fd2f9c1.cpg",
   "testcase_size": 125820
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
   "loc_size": 327680,
   "loc_offset": 245728,
   "loc_kind": "region",
   "dedup_token": "size--perfetto::trace_processor::SliceTracker::GetStackHash(std::__1::vector<perfetto::trace_processor::SliceTracker::SliceInfo, std::__1::allocator<perfetto::t",
   "region_size": 327680
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "fd_",
   "func_lines": [
    355,
    367
   ],
   "func_params": {
    "names": [
     "this",
     "socket_name"
    ],
    "types": [
     "perfetto.base.UnixSocketRaw",
     "std.string&"
    ]
   },
   "guards": [
    {
     "code": "addr.size == 0",
     "line": 358
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "bind(*fd_, addr.addr(), addr.size)",
     "name": "bind",
     "nargs": 3
    },
    {
     "code": "*fd_",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "addr.addr()",
     "name": "addr",
     "nargs": 1
    },
    {
     "code": "addr.size",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "fd_",
    "addr"
   ],
   "osv_id": "ARVO-42504673",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "perfetto::base::AlignedFree(void*)",
   "use_fn": "perfetto::trace_processor::SliceTracker::GetStackHash(std::__1::vector<perfetto::trace_processor::SliceTracker::SliceInfo, std::__1::allocator<perfetto::trace_processor::SliceTracker::SliceInfo> > const&)"
  }
 },
 {
  "osv_id": "ARVO-42506644",
  "project": "open62541",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "dst",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 1018,
    "size": null,
    "type": "void**"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Array_decodeBinary",
    "file": "/src/open62541/src/ua_types_encoding_binary.c",
    "line": 551
   },
   "size_expr": null,
   "size_bytes": 258,
   "cross_function": true,
   "size_expr_cpg": "size ;; type->memSize",
   "size_expr_cpg_callee": "UA_calloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 979,
    "fn": "deleteMembers_noInit",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 1036,
    "fn": "UA_Array_copy",
    "code": "memcpy(*dst, src, type->memSize * size) | *dst | type->memSize * size | type->memSize",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "UA_Array_copy",
    "file": "/src/open62541/src/ua_types.c",
    "line": 1036
   },
   "code": "memcpy(*dst, src, type->memSize * size) | *dst | type->memSize * size | type->memSize",
   "access": {
    "dir": "READ",
    "width": 258,
    "region_bytes": 258
   }
  },
  "context": {
   "fn": "UA_Array_copy",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "size == 0 | src == NULL | i < size",
   "guard_count": 3,
   "control_structures": "IF:1019,IF:1020,ELSE:1023,IF:1027,IF:1032,IF:1035,FOR:1043,IF:1048"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "src",
   "size",
   "dst",
   "type"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/b916bd061121852f7025f3610ae0074f8d597f7f/ARVO-42506644/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_b916bd061121.cpg",
   "testcase_size": 302
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
   "loc_size": 258,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--UA_Array_copy--copy_noInit",
   "region_size": 258
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1018,
    "type": "void**"
   },
   "entity_name_cpg": "dst",
   "func_lines": [
    1016,
    1053
   ],
   "func_params": {
    "names": [
     "src",
     "size",
     "dst",
     "type"
    ],
    "types": [
     "void*",
     "size_t",
     "void**",
     "UA_DataType*"
    ]
   },
   "guards": [
    {
     "code": "size == 0",
     "line": 1019
    },
    {
     "code": "src == NULL",
     "line": 1020
    },
    {
     "code": "i < size",
     "line": 1043
    },
    {
     "code": "retval != UA_STATUSCODE_GOOD",
     "line": 1048
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(*dst, src, type->memSize * size)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "*dst",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "type->memSize * size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "type->memSize",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dst",
    "src",
    "type",
    "size"
   ],
   "osv_id": "ARVO-42506644",
   "sites": [
    {
     "args": "size ;; type->memSize",
     "callee": "UA_calloc",
     "code": "UA_calloc(size, type->memSize)",
     "line": 1031
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": true,
   "free_fn": "deleteMembers_noInit",
   "use_fn": "UA_Array_copy"
  }
 },
 {
  "osv_id": "ARVO-42507004",
  "project": "libarchive",
  "crash_type": "heap-use-after-free",
  "entity": {
   "name": "end",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar.c",
    "line": 3327,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "create_filter",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar.c",
    "line": 3302
   },
   "size_expr": null,
   "size_bytes": 88,
   "cross_function": true,
   "size_expr_cpg": "1 ;; sizeof(*filters->vm)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3334,
    "fn": "run_filters",
    "code": "end != start + filter->blocklength | start + filter->blocklength | filter->blocklength",
    "origin": "report:crash"
   },
   {
    "code": "calloc(1, sizeof(*filters->vm))",
    "fn": "run_filters",
    "kind": "calloc",
    "line": 3339,
    "origin": "cpg",
    "args": "1 ;; sizeof(*filters->vm)"
   },
   {
    "kind": "free",
    "line": 3430,
    "fn": "delete_filter",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "run_filters",
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar.c",
    "line": 3334
   },
   "code": "end != start + filter->blocklength | start + filter->blocklength | filter->blocklength",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": 88
   }
  },
  "context": {
   "fn": "run_filters",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "end != start + filter->blocklength | filters->stack->blockstartpos < end",
   "guard_count": 2,
   "control_structures": "IF:3334,IF:3337,IF:3340,IF:3345,IF:3347,WHILE:3356,IF:3359,IF:3369,IF:3371"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libarchive/address/7ef089ec204a279ef87ebd19fbedef42ec418d05/ARVO-42507004/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_7ef089ec204a.cpg",
   "testcase_size": 156
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
   "loc_size": 88,
   "loc_offset": 64,
   "loc_kind": "region",
   "dedup_token": "run_filters--read_data_compressed--archive_read_format_rar_read_data",
   "region_size": 88
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "end = start + filter->blocklength",
     "line": 3327
    },
    {
     "code": "end = (size_t)expand(a, end)",
     "line": 3333
    }
   ],
   "entity_decl": {
    "line": 3327,
    "type": "size_t"
   },
   "entity_name_cpg": "end",
   "func_lines": [
    3320,
    3381
   ],
   "func_params": {
    "names": [
     "a"
    ],
    "types": [
     "archive_read*"
    ]
   },
   "guards": [
    {
     "code": "end != start + filter->blocklength",
     "line": 3334
    },
    {
     "code": "ret != ARCHIVE_OK",
     "line": 3345
    },
    {
     "code": "(filter = filters->stack) != NULL",
     "line": 3356
    },
    {
     "code": "(int64_t)filter->blockstartpos == filters->filterstart",
     "line": 3356
    },
    {
     "code": "filter->blocklength == lastfilterlength",
     "line": 3356
    },
    {
     "code": "filters->stack->blockstartpos < end",
     "line": 3371
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "end != start + filter->blocklength",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "start + filter->blocklength",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "filter->blocklength",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "end",
    "start",
    "filter"
   ],
   "osv_id": "ARVO-42507004",
   "sites": [
    {
     "args": "1 ;; sizeof(*filters->vm)",
     "callee": "calloc",
     "code": "calloc(1, sizeof(*filters->vm))",
     "line": 3339
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": true,
   "free_fn": "delete_filter",
   "use_fn": "run_filters"
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