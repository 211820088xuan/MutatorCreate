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
  "osv_id": "ARVO-42537622",
  "project": "gpac",
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
    "fn": "inspect_dump_pid",
    "file": "/src/gpac/src/filters/inspect.c",
    "line": 4442
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 7224,
    "fn": "hevc_ref_pic_lists_modification",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hevc_ref_pic_lists_modification",
    "file": "/src/gpac/src/media_tools/av_parsers.c",
    "line": 7224
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "hevc_ref_pic_lists_modification",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/gpac/address/df8121066cf8fb25cc70adf7ca8b35bda82fe216/ARVO-42537622/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/gpac_df8121066cf8.cpg",
   "testcase_size": 366
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
   "loc_size": 529104,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "hevc_ref_pic_lists_modification--hevc_parse_slice_segment--gf_hevc_parse_nalu_bs",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "hevc_ref_pic_lists_modification"
  }
 },
 {
  "osv_id": "ARVO-42539043",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c2",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmsintrp.c",
    "line": 601,
    "size": null,
    "type": "cmsFloat32Number"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMalloc",
    "file": "/src/lcms/src/cmserr.c",
    "line": 267
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 642,
    "fn": "TetrahedralInterpFloat",
    "code": "c2 = DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1) | DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1) | DENS(X1, Y1, Z1) | LutTable[(X1) + (Y1) + (Z1) + OutChan]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "TetrahedralInterpFloat",
    "file": "/src/lcms/src/cmsintrp.c",
    "line": 642
   },
   "code": "c2 = DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1) | DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1) | DENS(X1, Y1, Z1) | LutTable[(X1) + (Y1) + (Z1) + OutChan]",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "TetrahedralInterpFloat",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "OutChan < TotalOut",
   "guard_count": 1,
   "control_structures": "FOR:625,IF:631,ELSE:639,IF:639,ELSE:647,IF:647,ELSE:655,IF:655,ELSE:663,IF:663,ELSE:671,IF:671"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cmsFloat32Number",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "p"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/1272acb4b2e90088293874e9ab3c1d1e4f49f202/ARVO-42539043/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_1272acb4b2e9.cpg",
   "testcase_size": 735
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
   "loc_size": 96,
   "loc_offset": 12,
   "loc_kind": "region",
   "dedup_token": "TetrahedralInterpFloat--_LUTevalFloat--XFormSampler16",
   "overshoot_ratio": 0.125
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c2=0",
     "line": 601
    },
    {
     "code": "c2 = DENS(X1, Y1, Z0) - DENS(X1, Y0, Z0)",
     "line": 634
    },
    {
     "code": "c2 = DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1)",
     "line": 642
    },
    {
     "code": "c2 = DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1)",
     "line": 650
    },
    {
     "code": "c2 = DENS(X0, Y1, Z0) - c0",
     "line": 658
    },
    {
     "code": "c2 = DENS(X0, Y1, Z0) - c0",
     "line": 666
    },
    {
     "code": "c2 = DENS(X0, Y1, Z1) - DENS(X0, Y0, Z1)",
     "line": 674
    },
    {
     "code": "c2 = c3 = 0",
     "line": 679
    }
   ],
   "entity_decl": {
    "line": 601,
    "type": "cmsFloat32Number"
   },
   "entity_name_cpg": "c2",
   "func_lines": [
    591,
    685
   ],
   "func_params": {
    "names": [
     "Input",
     "Output",
     "p"
    ],
    "types": [
     "cmsFloat32Number[]",
     "cmsFloat32Number[]",
     "cmsInterpParams*"
    ]
   },
   "guards": [
    {
     "code": "OutChan < TotalOut",
     "line": 625
    }
   ],
   "line_call_count": 12,
   "line_calls": [
    {
     "code": "c2 = DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "DENS(X1, Y1, Z1) - DENS(X1, Y0, Z1)",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "DENS(X1, Y1, Z1)",
     "name": "DENS",
     "nargs": 3
    },
    {
     "code": "LutTable[(X1) + (Y1) + (Z1) + OutChan]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "(X1) + (Y1) + (Z1) + OutChan",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(X1) + (Y1) + (Z1)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(X1) + (Y1)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "DENS(X1, Y0, Z1)",
     "name": "DENS",
     "nargs": 3
    },
    {
     "code": "LutTable[(X1) + (Y0) + (Z1) + OutChan]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "(X1) + (Y0) + (Z1) + OutChan",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(X1) + (Y0) + (Z1)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(X1) + (Y0)",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c2",
    "X1",
    "Y1",
    "Z1",
    "LutTable",
    "OutChan",
    "Y0"
   ],
   "osv_id": "ARVO-42539043",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "TetrahedralInterpFloat"
  }
 },
 {
  "osv_id": "ARVO-42541581",
  "project": "file",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "uc",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/file/src/is_json.c",
    "line": 198,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 562
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 224,
    "fn": "json_parse_object",
    "code": "*uc++ | uc++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "json_parse_object",
    "file": "/src/file/src/is_json.c",
    "line": 224
   },
   "code": "*uc++ | uc++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_parse_object",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "uc < ue | uc == ue | uc == ue",
   "guard_count": 3,
   "control_structures": "WHILE:200,IF:202,GOTO:203,IF:204,GOTO:206,IF:209,GOTO:211,IF:214,GOTO:215,IF:216,GOTO:218,IF:220"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "ue"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/6382574724f99e4fd2e3b10580d83c9cb103ec5a/ARVO-42541581/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/file_6382574724f9.cpg",
   "testcase_size": 6
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
   "dedup_token": "json_parse_object--json_parse--file_is_json"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*uc = *ucp",
     "line": 198
    },
    {
     "code": "uc = json_skip_space(uc, ue)",
     "line": 201
    },
    {
     "code": "uc = json_skip_space(uc, ue)",
     "line": 213
    }
   ],
   "entity_decl": {
    "line": 198,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "uc",
   "func_lines": [
    194,
    241
   ],
   "func_params": {
    "names": [
     "ucp",
     "ue",
     "st",
     "lvl"
    ],
    "types": [
     "unsigned char**",
     "unsigned char*",
     "size_t*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "uc < ue",
     "line": 200
    },
    {
     "code": "uc == ue",
     "line": 202
    },
    {
     "code": "*uc++ != '\"'",
     "line": 204
    },
    {
     "code": "uc == ue",
     "line": 214
    },
    {
     "code": "*uc++ != ':'",
     "line": 216
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "*uc++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "uc++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "uc"
   ],
   "osv_id": "ARVO-42541581",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "json_parse_object"
  }
 },
 {
  "osv_id": "ARVO-42541665",
  "project": "file",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "uc",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/file/src/is_json.c",
    "line": 121,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "line": 562
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 130,
    "fn": "json_parse_string",
    "code": "*uc++ | uc++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "json_parse_string",
    "file": "/src/file/src/is_json.c",
    "line": 130
   },
   "code": "*uc++ | uc++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_parse_string",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "uc < ue",
   "guard_count": 1,
   "control_structures": "WHILE:125,SWITCH:126,GOTO:128,SWITCH:130,GOTO:132,CONTINUE:141,IF:143,GOTO:145,FOR:147,IF:148,GOTO:149,CONTINUE:150"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "ucp",
   "ue"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/6382574724f99e4fd2e3b10580d83c9cb103ec5a/ARVO-42541665/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/file_6382574724f9.cpg",
   "testcase_size": 3
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "dedup_token": "json_parse_string--json_parse--json_parse_array"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*uc = *ucp",
     "line": 121
    },
    {
     "code": "uc = ue",
     "line": 144
    }
   ],
   "entity_decl": {
    "line": 121,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "uc",
   "func_lines": [
    118,
    165
   ],
   "func_params": {
    "names": [
     "ucp",
     "ue"
    ],
    "types": [
     "unsigned char**",
     "unsigned char*"
    ]
   },
   "guards": [
    {
     "code": "uc < ue",
     "line": 125
    },
    {
     "code": "ue - uc < 4",
     "line": 143
    },
    {
     "code": "i < 4",
     "line": 147
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "*uc++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "uc++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "uc"
   ],
   "osv_id": "ARVO-42541665",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "json_parse_string"
  }
 },
 {
  "osv_id": "OSV-2020-1029",
  "project": "unicorn",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "as",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 1433,
    "fn": "iotlb_to_region_mips",
    "code": "as->dispatch->map.sections[index & ~TARGET_PAGE_MASK].mr | as->dispatch->map.sections[index & ~TARGET_PAGE_MASK] | as->dispatch->map.sections | as->dispatch->map",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "iotlb_to_region_mips",
    "file": "/src/unicorn/qemu/exec.c",
    "line": 1433
   },
   "code": "as->dispatch->map.sections[index & ~TARGET_PAGE_MASK].mr | as->dispatch->map.sections[index & ~TARGET_PAGE_MASK] | as->dispatch->map.sections | as->dispatch->map",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "iotlb_to_region",
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
  "input_reachability": [
   "as",
   "index"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-1029.log",
   "cpg": null,
   "testcase_size": 16
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
   "dedup_token": "iotlb_to_region_mips--get_page_addr_code_mips--tb_find_slow_mips"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "iotlb_to_region_mips"
  }
 },
 {
  "osv_id": "OSV-2020-1656",
  "project": "yara",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 50,
    "fn": "macho_is_32",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "macho_is_32",
    "file": "/src/yara/libyara/modules/macho/macho.c",
    "line": 50
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "macho_is_32",
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/yara/address/c6b3c4d1e0daa478e0592446cfd349a14acf9c81/OSV-2020-1656",
   "cpg": null,
   "testcase_size": 5377
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
   "loc_size": 5377,
   "loc_offset": 2,
   "loc_kind": "region",
   "dedup_token": "macho_is_32--macho_parse_file--macho_parse_fat_file",
   "overshoot_ratio": 0.000372
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "macho_is_32"
  }
 },
 {
  "osv_id": "OSV-2020-1698",
  "project": "yara",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 347,
    "fn": "macho_handle_segment",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "macho_handle_segment",
    "file": "/src/yara/libyara/modules/macho/macho.c",
    "line": 347
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 56,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "macho_handle_segment",
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/yara/address/c6b3c4d1e0daa478e0592446cfd349a14acf9c81/OSV-2020-1698",
   "cpg": null,
   "testcase_size": 59
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
   "loc_size": 59,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--macho_handle_segment--macho_parse_file",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "macho_handle_segment"
  }
 },
 {
  "osv_id": "OSV-2020-2087",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dest_",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 63,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/c-blosc2/tests/fuzz/fuzz_compress.c",
    "line": 37
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 68,
    "fn": "_sw32",
    "code": "*(int32_t *)dest_ = a | *(int32_t *)dest_ | (int32_t *)dest_",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_sw32",
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": 68
   },
   "code": "*(int32_t *)dest_ = a | *(int32_t *)dest_ | (int32_t *)dest_",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_sw32",
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
  "input_reachability": [
   "dest",
   "a"
  ],
  "evidence": {
   "report": "artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/3466fae4d72c9bd2afb5d62d18cf29beb5c499f2/OSV-2020-2087",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_3466fae4d72c.cpg",
   "testcase_size": 4125
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_size": 4126,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "_sw32--blosc_c--serial_blosc",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* dest_ = (uint8_t*)dest",
     "line": 63
    },
    {
     "code": "dest_[0] = pa[3]",
     "line": 76
    },
    {
     "code": "dest_[1] = pa[2]",
     "line": 77
    },
    {
     "code": "dest_[2] = pa[1]",
     "line": 78
    },
    {
     "code": "dest_[3] = pa[0]",
     "line": 79
    }
   ],
   "entity_decl": {
    "line": 63,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "dest_",
   "func_lines": [
    62,
    82
   ],
   "func_params": {
    "names": [
     "dest",
     "a"
    ],
    "types": [
     "void*",
     "int32_t"
    ]
   },
   "guards": [],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "*(int32_t *)dest_ = a",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*(int32_t *)dest_",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(int32_t *)dest_",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dest_",
    "a"
   ],
   "osv_id": "OSV-2020-2087",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_sw32"
  }
 },
 {
  "osv_id": "OSV-2020-2183",
  "project": "c-blosc2",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 70,
    "fn": "Lizard_decompress_LIZv1",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Lizard_decompress_LIZv1",
    "file": "/src/c-blosc2/internal-complibs/lizard-1.0/lizard_decompress_liz.h",
    "line": 70
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Lizard_decompress_LIZv1",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-2183.log",
   "cpg": null,
   "testcase_size": 78
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
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_size": 78,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "Lizard_decompress_LIZv1--Lizard_decompress_generic--Lizard_decompress_safe",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Lizard_decompress_LIZv1"
  }
 },
 {
  "osv_id": "OSV-2020-2238",
  "project": "yara",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 899,
    "fn": "dotnet_parse_tilde_2",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dotnet_parse_tilde_2",
    "file": "/src/yara/libyara/modules/dotnet/dotnet.c",
    "line": 899
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 47,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dotnet_parse_tilde_2",
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/yara/address/876ec3c1812ce21476f6af83a70551921b7e2506/OSV-2020-2238",
   "cpg": null,
   "testcase_size": 1772
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_size": 1772,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "___interceptor_strncpy--dotnet_parse_tilde_2--dotnet_parse_tilde",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dotnet_parse_tilde_2"
  }
 },
 {
  "osv_id": "OSV-2020-2251",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "version",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2174,
    "fn": "blosc_run_decompression_with_context",
    "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_run_decompression_with_context",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 2174
   },
   "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "blosc_run_decompression_with_context",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "version > BLOSC_VERSION_FORMAT",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "src"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-2251.log",
   "cpg": null,
   "testcase_size": 89
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
   "loc_size": 89,
   "loc_offset": 4,
   "loc_kind": "region",
   "dedup_token": "blosc_run_decompression_with_context--blosc2_decompress_ctx--frame_decompress_chunk",
   "overshoot_ratio": 0.044944
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "blosc_run_decompression_with_context"
  }
 },
 {
  "osv_id": "OSV-2020-2291",
  "project": "yara",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 876,
    "fn": "dotnet_parse_tilde_2",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dotnet_parse_tilde_2",
    "file": "/src/yara/libyara/modules/dotnet/dotnet.c",
    "line": 876
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dotnet_parse_tilde_2",
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/yara/address/e2d0ce5f132cf157e44acc904916c62c52bc3c91/OSV-2020-2291",
   "cpg": null,
   "testcase_size": 347
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
   "loc_size": 347,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "dotnet_parse_tilde_2--dotnet_parse_tilde--dotnet_parse_com",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dotnet_parse_tilde_2"
  }
 },
 {
  "osv_id": "OSV-2020-278",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_dec",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
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
    "line": 510,
    "fn": "ih264d_decode_slice_thread",
    "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_decode_slice_thread",
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 510
   },
   "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_decode_slice_thread",
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
  "input_reachability": [
   "ps_dec"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-278.log",
   "cpg": null,
   "testcase_size": 54
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
   "loc_size": 5184,
   "loc_offset": 12,
   "loc_kind": "region",
   "dedup_token": "ih264d_decode_slice_thread--ih264d_decode_picture_thread--asan_thread_start(void*)",
   "overshoot_ratio": 0.002315
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_decode_slice_thread"
  }
 },
 {
  "osv_id": "OSV-2020-546",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_dec",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
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
    "line": 510,
    "fn": "ih264d_decode_slice_thread",
    "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_decode_slice_thread",
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 510
   },
   "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_decode_slice_thread",
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
  "input_reachability": [
   "ps_dec"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-546.log",
   "cpg": null,
   "testcase_size": 44
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
   "loc_size": 5680,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "ih264d_decode_slice_thread--ih264d_decode_picture_thread--asan_thread_start(void*)",
   "overshoot_ratio": 0.001408
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_decode_slice_thread"
  }
 },
 {
  "osv_id": "OSV-2020-674",
  "project": "libhevc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ps_nbr_pu",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 532,
    "fn": "ihevcd_mv_merge",
    "code": "!ps_nbr_pu[NBR_A1]->b1_intra_flag | ps_nbr_pu[NBR_A1]->b1_intra_flag | ps_nbr_pu[NBR_A1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ihevcd_mv_merge",
    "file": "/src/libhevc/decoder/ihevcd_mv_merge.c",
    "line": 532
   },
   "code": "!ps_nbr_pu[NBR_A1]->b1_intra_flag | ps_nbr_pu[NBR_A1]->b1_intra_flag | ps_nbr_pu[NBR_A1]",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ihevcd_mv_merge",
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
  "input_reachability": [
   "ps_mv_ctxt",
   "ps_pu",
   "l_avail"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-674.log",
   "cpg": null,
   "testcase_size": 10491
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
   "dedup_token": "ihevcd_mv_merge--ihevcd_get_mv_ctb--ihevcd_parse_slice_data"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ihevcd_mv_merge"
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