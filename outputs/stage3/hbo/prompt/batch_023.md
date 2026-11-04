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
  "osv_id": "ARVO-42513630",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "y",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 742,
    "size": null,
    "type": "mpz_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 749,
    "fn": "mpz_get_int",
    "code": "digits(y) > 2 || y->p[1] > 1 | digits(y) > 2 | digits(y) | y->p[1] > 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mpz_get_int",
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 749
   },
   "code": "digits(y) > 2 || y->p[1] > 1 | digits(y) > 2 | digits(y) | y->p[1] > 1",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mpz_get_int",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:746,ELSE:749,IF:749,ELSE:752,IF:754"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mpz_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "y"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/a99d0036222ad4c3a300243113f7afff2618aff9/ARVO-42513630/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_a99d0036222a.cpg",
   "testcase_size": 32
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
   "dedup_token": "mpz_get_int--mrb_bint_cmp--cmpnum"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 742,
    "type": "mpz_t*"
   },
   "entity_name_cpg": "y",
   "func_lines": [
    741,
    758
   ],
   "func_params": {
    "names": [
     "y",
     "v"
    ],
    "types": [
     "mpz_t*",
     "mrb_int*"
    ]
   },
   "guards": [
    {
     "code": "y->sn == 0",
     "line": 746
    },
    {
     "code": "digits(y) > 2",
     "line": 749
    },
    {
     "code": "y->p[1] > 1",
     "line": 749
    },
    {
     "code": "MRB_INT_MAX < i",
     "line": 754
    },
    {
     "code": "i < MRB_INT_MIN",
     "line": 754
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "digits(y) > 2 ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "digits(y) > 2",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "digits(y)",
     "name": "digits",
     "nargs": 1
    },
    {
     "code": "y->p[1] > 1",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "y->p[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "y->p",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "y"
   ],
   "osv_id": "ARVO-42513630",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mpz_get_int"
  }
 },
 {
  "osv_id": "ARVO-42513731",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c1",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmsintrp.c",
    "line": 729,
    "size": null,
    "type": "cmsS15Fixed16Number"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 766,
    "fn": "TetrahedralInterp16",
    "code": "c1 = LutTable[X1] | LutTable[X1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "TetrahedralInterp16",
    "file": "/src/lcms/src/cmsintrp.c",
    "line": 766
   },
   "code": "c1 = LutTable[X1] | LutTable[X1]",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "TetrahedralInterp16",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:761,IF:762,FOR:765,ELSE:776,IF:776,FOR:779,ELSE:790,FOR:793,ELSE:805,IF:806,FOR:809,ELSE:820"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cmsS15Fixed16Number",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "Input",
   "p"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/a9796f61c682f5320ff572c888062ee34315b836/ARVO-42513731/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_a9796f61c682.cpg",
   "testcase_size": 304
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
   "dedup_token": "TetrahedralInterp16--cmsCreateExtendedTransform--cmsCreateMultiprofileTransformTHR"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c1 = LutTable[X1]",
     "line": 766
    },
    {
     "code": "c1 = LutTable[X1]",
     "line": 780
    },
    {
     "code": "c1 = LutTable[X1]",
     "line": 794
    },
    {
     "code": "c1 = LutTable[X1]",
     "line": 810
    },
    {
     "code": "c1 = LutTable[X1]",
     "line": 824
    },
    {
     "code": "c1 = LutTable[X1]",
     "line": 838
    }
   ],
   "entity_decl": {
    "line": 729,
    "type": "cmsS15Fixed16Number"
   },
   "entity_name_cpg": "c1",
   "func_lines": [
    720,
    850
   ],
   "func_params": {
    "names": [
     "Input",
     "Output",
     "p"
    ],
    "types": [
     "cmsUInt16Number[]",
     "cmsUInt16Number[]",
     "cmsInterpParams*"
    ]
   },
   "guards": [
    {
     "code": "Input[0] == 0xFFFFU",
     "line": 746
    },
    {
     "code": "Input[1] == 0xFFFFU",
     "line": 749
    },
    {
     "code": "Input[2] == 0xFFFFU",
     "line": 752
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "c1 = LutTable[X1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "LutTable[X1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c1",
    "LutTable",
    "X1"
   ],
   "osv_id": "ARVO-42513731",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "TetrahedralInterp16"
  }
 },
 {
  "osv_id": "ARVO-42513776",
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
    "fn": "Assimp::MD5Importer::LoadFileIntoMemory(Assimp::IOStream*)",
    "file": "/src/assimp/code/AssetLib/MD5/MD5Loader.cpp",
    "line": 195
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 436,
    "fn": "SkipSpacesAndLineEnd",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "SkipSpacesAndLineEnd",
    "file": "/src/assimp/code/AssetLib/MD5/MD5Parser.h",
    "line": 436
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "SkipSpacesAndLineEnd",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/71a87b653cd4b5671104fe49e2e38cf5dd4d8675/ARVO-42513776/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_71a87b653cd4.cpg",
   "testcase_size": 27
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
   "dedup_token": "SkipSpacesAndLineEnd--SkipSpacesAndLineEnd--Assimp::MD5::MD5Parser::ParseHeader()"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    369,
    382
   ],
   "func_params": {
    "names": [
     "this",
     "buffer"
    ],
    "types": [
     "Assimp.PLY.DOM",
     "std.vector<char>&"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42513776",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "SkipSpacesAndLineEnd"
  }
 },
 {
  "osv_id": "ARVO-42513779",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "qhat",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 433,
    "size": null,
    "type": "mp_limb2"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "mrb ;; &x ;; xx->sz+1",
   "size_expr_cpg_callee": "mpz_realloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 433,
    "fn": "udiv",
    "code": "qhat = (((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]) | (((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]) / z | ((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1] | (mp_limb2)x.p[j+yd] << DIG_SIZE",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "udiv",
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 433
   },
   "code": "qhat = (((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]) | (((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]) / z | ((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1] | (mp_limb2)x.p[j+yd] << DIG_SIZE",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "udiv",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i<yd | i<yd | j == 0",
   "guard_count": 3,
   "control_structures": "IF:408,ELSE:413,IF:413,IF:422,FOR:432,IF:435,FOR:436,FOR:444,FOR:446,IF:454,BREAK:454"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mp_limb2",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "mrb",
   "xx",
   "yy"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e04184185ab43b94980550e850d8813a415fa438/ARVO-42513779/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e04184185ab4.cpg",
   "testcase_size": 22
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
   "dedup_token": "udiv--mpz_mmod--mrb_bint_mod"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "qhat = (((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]) / z",
     "line": 433
    }
   ],
   "entity_decl": {
    "line": 433,
    "type": "mp_limb2"
   },
   "entity_name_cpg": "qhat",
   "func_lines": [
    403,
    461
   ],
   "func_params": {
    "names": [
     "mrb",
     "qq",
     "rr",
     "xx",
     "yy"
    ],
    "types": [
     "mrb_state*",
     "mpz_t*",
     "mpz_t*",
     "mpz_t*",
     "mpz_t*"
    ]
   },
   "guards": [
    {
     "code": "cmp == 0",
     "line": 408
    },
    {
     "code": "cmp < 0",
     "line": 413
    },
    {
     "code": "i<yd",
     "line": 436
    },
    {
     "code": "b!=0",
     "line": 444
    },
    {
     "code": "i<yd",
     "line": 446
    },
    {
     "code": "j == 0",
     "line": 454
    }
   ],
   "line_call_count": 15,
   "line_calls": [
    {
     "code": "qhat = (((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]) / z",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]) / z",
     "name": "<operator>.division",
     "nargs": 2
    },
    {
     "code": "((mp_limb2)x.p[j+yd] << DIG_SIZE) + x.p[j+yd-1]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(mp_limb2)x.p[j+yd] << DIG_SIZE",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(mp_limb2)x.p[j+yd]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "x.p[j+yd]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "x.p",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "j+yd",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "DIG_SIZE",
     "name": "DIG_SIZE",
     "nargs": 0
    },
    {
     "code": "sizeof (mp_limb) * 8",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "sizeof (mp_limb)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "x.p[j+yd-1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "x.p",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "j+yd-1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "j+yd",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "qhat",
    "x",
    "j",
    "yd",
    "mp_limb",
    "z"
   ],
   "osv_id": "ARVO-42513779",
   "sites": [
    {
     "args": "mrb ;; &x ;; xx->sz+1",
     "callee": "mpz_realloc",
     "code": "mpz_realloc(mrb,&x,xx->sz+1)",
     "line": 424
    },
    {
     "args": "mrb ;; &q ;; xd",
     "callee": "mpz_realloc",
     "code": "mpz_realloc(mrb,&q,xd)",
     "line": 430
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "udiv"
  }
 },
 {
  "osv_id": "ARVO-42513788",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "Len",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmstypes.c",
    "line": 1573,
    "size": null,
    "type": "cmsUInt32Number"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1591,
    "fn": "Type_MLU_Write",
    "code": "Len    =  mlu ->Entries[i].Len | mlu ->Entries[i].Len | mlu ->Entries[i] | mlu ->Entries",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Type_MLU_Write",
    "file": "/src/lcms/src/cmstypes.c",
    "line": 1591
   },
   "code": "Len    =  mlu ->Entries[i].Len | mlu ->Entries[i].Len | mlu ->Entries[i] | mlu ->Entries",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Type_MLU_Write",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < mlu ->UsedEntries",
   "guard_count": 1,
   "control_structures": "IF:1576,IF:1579,IF:1580,IF:1584,IF:1585,FOR:1589,IF:1597,IF:1598,IF:1599,IF:1600,IF:1603"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cmsUInt32Number",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "Ptr"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/6849af422fd296cb8ce160d376978ef5d79f9417/ARVO-42513788/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_6849af422fd2.cpg",
   "testcase_size": 1224
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
   "dedup_token": "Type_MLU_Write--SaveTags--cmsSaveProfileToIOhandler"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "Len    =  mlu ->Entries[i].Len",
     "line": 1591
    },
    {
     "code": "Len    = (Len * sizeof(cmsUInt16Number)) / sizeof(wchar_t)",
     "line": 1594
    }
   ],
   "entity_decl": {
    "line": 1573,
    "type": "cmsUInt32Number"
   },
   "entity_name_cpg": "Len",
   "func_lines": [
    1568,
    1609
   ],
   "func_params": {
    "names": [
     "self",
     "io",
     "Ptr",
     "nItems"
    ],
    "types": [
     "_cms_typehandler_struct*",
     "cmsIOHANDLER*",
     "void*",
     "cmsUInt32Number"
    ]
   },
   "guards": [
    {
     "code": "Ptr == NULL",
     "line": 1576
    },
    {
     "code": "i < mlu ->UsedEntries",
     "line": 1589
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "Len    =  mlu ->Entries[i].Len",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "mlu ->Entries[i].Len",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "mlu ->Entries[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "mlu ->Entries",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "Len",
    "mlu",
    "i"
   ],
   "osv_id": "ARVO-42513788",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Type_MLU_Write"
  }
 },
 {
  "osv_id": "ARVO-42513797",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "self",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmstypes.c",
    "line": 3495,
    "size": null,
    "type": "_cms_typehandler_struct*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3506,
    "fn": "WriteSeqID",
    "code": "!SaveDescription(self, io, Seq ->seq[n].Description) | SaveDescription(self, io, Seq ->seq[n].Description) | Seq ->seq[n].Description | Seq ->seq[n]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WriteSeqID",
    "file": "/src/lcms/src/cmstypes.c",
    "line": 3506
   },
   "code": "!SaveDescription(self, io, Seq ->seq[n].Description) | SaveDescription(self, io, Seq ->seq[n].Description) | Seq ->seq[n].Description | Seq ->seq[n]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "WriteSeqID",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:3503,IF:3506"
  },
  "call_chain": [],
  "types": {
   "entity_type": "_cms_typehandler_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "self",
   "io",
   "Cargo",
   "n"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/6849af422fd296cb8ce160d376978ef5d79f9417/ARVO-42513797/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_6849af422fd2.cpg",
   "testcase_size": 1032
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
   "dedup_token": "WriteSeqID--WritePositionTable--Type_ProfileSequenceId_Write"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 3495,
    "type": "_cms_typehandler_struct*"
   },
   "entity_name_cpg": "self",
   "func_lines": [
    3494,
    3511
   ],
   "func_params": {
    "names": [
     "self",
     "io",
     "Cargo",
     "n",
     "SizeOfTag"
    ],
    "types": [
     "_cms_typehandler_struct*",
     "cmsIOHANDLER*",
     "void*",
     "cmsUInt32Number",
     "cmsUInt32Number"
    ]
   },
   "guards": [],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "!SaveDescription(self, io, Seq ->seq[n].Description)",
     "name": "<operator>.logicalNot",
     "nargs": 1
    },
    {
     "code": "SaveDescription(self, io, Seq ->seq[n].Description)",
     "name": "SaveDescription",
     "nargs": 3
    },
    {
     "code": "Seq ->seq[n].Description",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "Seq ->seq[n]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "Seq ->seq",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "FALSE",
     "name": "FALSE",
     "nargs": 0
    }
   ],
   "line_ids": [
    "self",
    "io",
    "Seq",
    "n"
   ],
   "osv_id": "ARVO-42513797",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WriteSeqID"
  }
 },
 {
  "osv_id": "ARVO-42513819",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "val",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmstypes.c",
    "line": 2070,
    "size": null,
    "type": "cmsUInt16Number"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2081,
    "fn": "Write16bitTables",
    "code": "val = Tables->TheCurves[i]->Table16[j] | Tables->TheCurves[i]->Table16[j] | Tables->TheCurves[i]->Table16 | Tables->TheCurves[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Write16bitTables",
    "file": "/src/lcms/src/cmstypes.c",
    "line": 2081
   },
   "code": "val = Tables->TheCurves[i]->Table16[j] | Tables->TheCurves[i]->Table16[j] | Tables->TheCurves[i]->Table16 | Tables->TheCurves[i]",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Write16bitTables",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "Tables != NULL | i < Tables ->nCurves | j < nEntries",
   "guard_count": 3,
   "control_structures": "FOR:2077,FOR:2079,IF:2082"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cmsUInt16Number",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "Tables"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/6849af422fd296cb8ce160d376978ef5d79f9417/ARVO-42513819/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_6849af422fd2.cpg",
   "testcase_size": 796
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
   "dedup_token": "Write16bitTables--Type_LUT16_Write--SaveTags"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "val = Tables->TheCurves[i]->Table16[j]",
     "line": 2081
    }
   ],
   "entity_decl": {
    "line": 2070,
    "type": "cmsUInt16Number"
   },
   "entity_name_cpg": "val",
   "func_lines": [
    2065,
    2088
   ],
   "func_params": {
    "names": [
     "ContextID",
     "io",
     "Tables"
    ],
    "types": [
     "cmsContext",
     "cmsIOHANDLER*",
     "_cmsStageToneCurvesData*"
    ]
   },
   "guards": [
    {
     "code": "Tables != NULL",
     "line": 2073
    },
    {
     "code": "i < Tables ->nCurves",
     "line": 2077
    },
    {
     "code": "j < nEntries",
     "line": 2079
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "val = Tables->TheCurves[i]->Table16[j]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "Tables->TheCurves[i]->Table16[j]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "Tables->TheCurves[i]->Table16",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "Tables->TheCurves[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "Tables->TheCurves",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "val",
    "Tables",
    "i",
    "j"
   ],
   "osv_id": "ARVO-42513819",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Write16bitTables"
  }
 },
 {
  "osv_id": "ARVO-42513834",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "v",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmsnamed.c",
    "line": 336,
    "size": null,
    "type": "_cmsMLUentry*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 346,
    "fn": "_cmsMLUgetWide",
    "code": "v -> Language == LanguageCode | v -> Language",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_cmsMLUgetWide",
    "file": "/src/lcms/src/cmsnamed.c",
    "line": 346
   },
   "code": "v -> Language == LanguageCode | v -> Language",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_cmsMLUgetWide",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "v -> Language == LanguageCode",
   "guard_count": 1,
   "control_structures": "IF:338,IF:340,FOR:342,IF:346,IF:348,IF:350,IF:352,IF:353,IF:355,IF:363,IF:368,IF:369"
  },
  "call_chain": [],
  "types": {
   "entity_type": "_cmsMLUentry*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "mlu",
   "LanguageCode",
   "CountryCode"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/6849af422fd296cb8ce160d376978ef5d79f9417/ARVO-42513834/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_6849af422fd2.cpg",
   "testcase_size": 1224
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
   "dedup_token": "_cmsMLUgetWide--cmsMLUgetASCII--WriteCountAndString"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "v = mlu ->Entries + i",
     "line": 344
    },
    {
     "code": "v = mlu ->Entries + Best",
     "line": 366
    }
   ],
   "entity_decl": {
    "line": 336,
    "type": "_cmsMLUentry*"
   },
   "entity_name_cpg": "v",
   "func_lines": [
    328,
    374
   ],
   "func_params": {
    "names": [
     "mlu",
     "len",
     "LanguageCode",
     "CountryCode",
     "UsedLanguageCode",
     "UsedCountryCode"
    ],
    "types": [
     "cmsMLU*",
     "cmsUInt32Number*",
     "cmsUInt16Number",
     "cmsUInt16Number",
     "cmsUInt16Number*",
     "cmsUInt16Number*"
    ]
   },
   "guards": [
    {
     "code": "mlu == NULL",
     "line": 338
    },
    {
     "code": "i < mlu ->UsedEntries",
     "line": 342
    },
    {
     "code": "v -> Language == LanguageCode",
     "line": 346
    },
    {
     "code": "Best == -1",
     "line": 348
    },
    {
     "code": "v -> Country == CountryCode",
     "line": 350
    },
    {
     "code": "UsedLanguageCode != NULL",
     "line": 352
    },
    {
     "code": "UsedCountryCode  != NULL",
     "line": 353
    },
    {
     "code": "len != NULL",
     "line": 355
    },
    {
     "code": "Best == -1",
     "line": 363
    },
    {
     "code": "UsedLanguageCode != NULL",
     "line": 368
    },
    {
     "code": "UsedCountryCode  != NULL",
     "line": 369
    },
    {
     "code": "len != NULL",
     "line": 371
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "v -> Language == LanguageCode",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "v -> Language",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "v",
    "LanguageCode"
   ],
   "osv_id": "ARVO-42513834",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_cmsMLUgetWide"
  }
 },
 {
  "osv_id": "ARVO-42513868",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "xyz",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmsplugin.c",
    "line": 352,
    "size": null,
    "type": "cmsEncodedXYZNumber"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 359,
    "fn": "_cmsWriteXYZNumber",
    "code": "xyz.Z = (cmsS15Fixed16Number) _cmsAdjustEndianess32((cms | xyz.Z | (cmsS15Fixed16Number) _cmsAdjustEndianess32((cmsUInt32Nu | _cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fi",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_cmsWriteXYZNumber",
    "file": "/src/lcms/src/cmsplugin.c",
    "line": 359
   },
   "code": "xyz.Z = (cmsS15Fixed16Number) _cmsAdjustEndianess32((cms | xyz.Z | (cmsS15Fixed16Number) _cmsAdjustEndianess32((cmsUInt32Nu | _cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fi",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_cmsWriteXYZNumber",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "XYZ != NULL",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": "cmsEncodedXYZNumber",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "io",
   "XYZ"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/6849af422fd296cb8ce160d376978ef5d79f9417/ARVO-42513868/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_6849af422fd2.cpg",
   "testcase_size": 976
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
   "dedup_token": "_cmsWriteXYZNumber--Type_ViewingConditions_Write--SaveTags"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "xyz.X = (cmsS15Fixed16Number) _cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fixed16(XYZ->X))",
     "line": 357
    },
    {
     "code": "xyz.Y = (cmsS15Fixed16Number) _cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fixed16(XYZ->Y))",
     "line": 358
    },
    {
     "code": "xyz.Z = (cmsS15Fixed16Number) _cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fixed16(XYZ->Z))",
     "line": 359
    }
   ],
   "entity_decl": {
    "line": 352,
    "type": "cmsEncodedXYZNumber"
   },
   "entity_name_cpg": "xyz",
   "func_lines": [
    350,
    362
   ],
   "func_params": {
    "names": [
     "io",
     "XYZ"
    ],
    "types": [
     "cmsIOHANDLER*",
     "cmsCIEXYZ*"
    ]
   },
   "guards": [
    {
     "code": "io != NULL",
     "line": 354
    },
    {
     "code": "XYZ != NULL",
     "line": 355
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "xyz.Z = (cmsS15Fixed16Number) _cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fixed16(XYZ->Z))",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "xyz.Z",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "(cmsS15Fixed16Number) _cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fixed16(XYZ->Z))",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "_cmsAdjustEndianess32((cmsUInt32Number) _cmsDoubleTo15Fixed16(XYZ->Z))",
     "name": "_cmsAdjustEndianess32",
     "nargs": 1
    },
    {
     "code": "(cmsUInt32Number) _cmsDoubleTo15Fixed16(XYZ->Z)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "_cmsDoubleTo15Fixed16(XYZ->Z)",
     "name": "_cmsDoubleTo15Fixed16",
     "nargs": 1
    },
    {
     "code": "XYZ->Z",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "xyz",
    "XYZ"
   ],
   "osv_id": "ARVO-42513868",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_cmsWriteXYZNumber"
  }
 },
 {
  "osv_id": "ARVO-42513988",
  "project": "libredwg",
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
    "fn": "dynapi_set_helper",
    "file": "/src/libredwg/src/gen-dynapi.pl",
    "line": 3111
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "f->size ;; 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3112,
    "fn": "dynapi_set_helper",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dynapi_set_helper",
    "file": "/src/libredwg/src/gen-dynapi.pl",
    "line": 3112
   },
   "code": "",
   "access": {
    "dir": "WRITE",
    "width": 49,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dynapi_set_helper",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/fe03c5a89cbd441b6840335bd484cf08bc65c7c4/ARVO-42513988/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_fe03c5a89cbd.cpg",
   "testcase_size": 256
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
   "shadow_legend_size": 0,
   "dedup_token": "__interceptor_strcpy--strcpy--dynapi_set_helper"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    14262,
    14318
   ],
   "func_params": {
    "names": [
     "old",
     "f",
     "dwg_version",
     "value",
     "is_utf8"
    ],
    "types": [
     "void*restrict",
     "Dwg_DYNAPI_field*restrict",
     "Dwg_Version_Type",
     "void*restrict",
     "bool"
    ]
   },
   "guards": [
    {
     "code": "dwg_version < R_2007",
     "line": 14284
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42513988",
   "sites": [
    {
     "args": "f->size ;; 1",
     "callee": "calloc",
     "code": "calloc (f->size, 1)",
     "line": 14279
    },
    {
     "args": "strlen (*(char**)value)+1",
     "callee": "malloc",
     "code": "malloc (strlen (*(char**)value)+1)",
     "line": 14287
    },
    {
     "args": "2 * length",
     "callee": "malloc",
     "code": "malloc (2 * length)",
     "line": 14307
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dynapi_set_helper"
  }
 },
 {
  "osv_id": "ARVO-42514015",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/softether.c",
    "line": 266,
    "size": null,
    "type": "ndpi_flow_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)",
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
    "line": 301,
    "fn": "dissect_softether_ip_port",
    "code": "strncpy(flow->protos.softether.port, ip_port_separator + | flow->protos.softether.port | flow->protos.softether | flow->protos",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dissect_softether_ip_port",
    "file": "/src/ndpi/src/lib/protocols/softether.c",
    "line": 301
   },
   "code": "strncpy(flow->protos.softether.port, ip_port_separator + | flow->protos.softether.port | flow->protos.softether | flow->protos",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dissect_softether_ip_port",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "ip_port_separator == NULL",
   "guard_count": 1,
   "control_structures": "IF:272,IF:278,IF:286"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_flow_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "flow",
   "packet"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/ed4f106a0d6ba2d644e95354891b4b68f927c535/ARVO-42514015/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_ed4f106a0d6b.cpg",
   "testcase_size": 40
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
   "dedup_token": "__interceptor_strncpy--dissect_softether_ip_port--ndpi_search_softether"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->protos.softether.ip[ip_len] = '\\0'",
     "line": 296
    },
    {
     "code": "flow->protos.softether.port[port_len] = '\\0'",
     "line": 303
    }
   ],
   "entity_decl": {
    "line": 266,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    266,
    306
   ],
   "func_params": {
    "names": [
     "flow",
     "packet"
    ],
    "types": [
     "ndpi_flow_struct*",
     "ndpi_packet_struct*"
    ]
   },
   "guards": [
    {
     "code": "packet->payload_packet_len < NDPI_STATICSTRING_LEN(\"IP=\") +",
     "line": 272
    },
    {
     "code": "strncmp((char *)&packet->payload[0], \"IP=\", NDPI_STATICSTRING_LEN(\"IP=\")) != 0",
     "line": 278
    },
    {
     "code": "ip_port_separator == NULL",
     "line": 286
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "strncpy(flow->protos.softether.port, ip_port_separator + NDPI_STATICSTRING_LEN(\",PORT=\"),",
     "name": "strncpy",
     "nargs": null
    },
    {
     "code": "flow->protos.softether.port",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->protos.softether",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->protos",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ip_port_separator + NDPI_STATICSTRING_LEN(\",PORT=\")",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "NDPI_STATICSTRING_LEN(\",PORT=\")",
     "name": "NDPI_STATICSTRING_LEN",
     "nargs": 1
    }
   ],
   "line_ids": [
    "flow",
    "ip_port_separator"
   ],
   "osv_id": "ARVO-42514015",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dissect_softether_ip_port"
  }
 },
 {
  "osv_id": "ARVO-42514154",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "q",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 419,
    "size": null,
    "type": "mpz_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "mrb ;; &x ;; xx->sz+1",
   "size_expr_cpg_callee": "mpz_realloc"
  },
  "sites": [
   {
    "kind": "free",
    "line": 65,
    "fn": "mrb_default_allocf",
    "code": null,
    "origin": "report:freed_by"
   },
   {
    "kind": "unknown",
    "line": 453,
    "fn": "udiv",
    "code": "q.p[j] = qhat | q.p[j] | q.p",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "udiv",
    "file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
    "line": 453
   },
   "code": "q.p[j] = qhat | q.p[j] | q.p",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "udiv",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j == 0",
   "guard_count": 1,
   "control_structures": "IF:408,ELSE:413,IF:413,IF:422,FOR:432,IF:435,FOR:436,FOR:444,FOR:446,IF:454,BREAK:454"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mpz_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "mrb",
   "xx",
   "yy"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e04184185ab43b94980550e850d8813a415fa438/ARVO-42514154/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e04184185ab4.cpg",
   "testcase_size": 33854
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
   "dedup_token": "udiv--mpz_mdiv--mrb_bint_div"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "q.p[j] = qhat",
     "line": 453
    }
   ],
   "entity_decl": {
    "line": 419,
    "type": "mpz_t"
   },
   "entity_name_cpg": "q",
   "func_lines": [
    403,
    461
   ],
   "func_params": {
    "names": [
     "mrb",
     "qq",
     "rr",
     "xx",
     "yy"
    ],
    "types": [
     "mrb_state*",
     "mpz_t*",
     "mpz_t*",
     "mpz_t*",
     "mpz_t*"
    ]
   },
   "guards": [
    {
     "code": "cmp == 0",
     "line": 408
    },
    {
     "code": "cmp < 0",
     "line": 413
    },
    {
     "code": "i<yd",
     "line": 436
    },
    {
     "code": "b!=0",
     "line": 444
    },
    {
     "code": "i<yd",
     "line": 446
    },
    {
     "code": "j == 0",
     "line": 454
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "q.p[j] = qhat",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "q.p[j]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "q.p",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "q",
    "j",
    "qhat"
   ],
   "osv_id": "ARVO-42514154",
   "sites": [
    {
     "args": "mrb ;; &x ;; xx->sz+1",
     "callee": "mpz_realloc",
     "code": "mpz_realloc(mrb,&x,xx->sz+1)",
     "line": 424
    },
    {
     "args": "mrb ;; &q ;; xd",
     "callee": "mpz_realloc",
     "code": "mpz_realloc(mrb,&q,xd)",
     "line": 430
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 2,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "mrb_default_allocf",
   "use_fn": "udiv"
  }
 },
 {
  "osv_id": "ARVO-42514542",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/florensia.c",
    "line": 37,
    "size": null,
    "type": "ndpi_flow_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "LLVMFuzzerTestOneInput",
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "line": 103
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 93,
    "fn": "ndpi_search_florensia",
    "code": "flow->packet_counter < 10 && get_l16(packet->payload, 0) | flow->packet_counter < 10 | flow->packet_counter | get_l16(packet->payload, 0) == packet->payload_packet_le",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_florensia",
    "file": "/src/ndpi/src/lib/protocols/florensia.c",
    "line": 93
   },
   "code": "flow->packet_counter < 10 && get_l16(packet->payload, 0) | flow->packet_counter < 10 | flow->packet_counter | get_l16(packet->payload, 0) == packet->payload_packet_le",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_florensia",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:43,IF:44,IF:46,IF:55,IF:61,IF:67,IF:69,IF:79,IF:80,IF:86,IF:93,IF:100"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_flow_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ndpi_struct",
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/897f8314b29cd7de9eeab9af15b3e189ae6724a1/ARVO-42514542/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_897f8314b29c.cpg",
   "testcase_size": 164
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "ndpi_search_florensia--check_ndpi_detection_func--ndpi_check_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->florensia_stage = 1",
     "line": 52
    },
    {
     "code": "flow->florensia_stage = 1",
     "line": 58
    },
    {
     "code": "flow->florensia_stage = 1",
     "line": 64
    },
    {
     "code": "flow->florensia_stage = 1",
     "line": 75
    },
    {
     "code": "flow->florensia_stage = 1",
     "line": 104
    }
   ],
   "entity_decl": {
    "line": 37,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    37,
    116
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*"
    ]
   },
   "guards": [
    {
     "code": "packet->tcp != NULL",
     "line": 43
    },
    {
     "code": "packet->payload_packet_len == 5",
     "line": 44
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "line": 44
    },
    {
     "code": "packet->payload[2] == 0x65",
     "line": 45
    },
    {
     "code": "packet->payload[4] == 0xff",
     "line": 45
    },
    {
     "code": "flow->florensia_stage == 1",
     "line": 46
    },
    {
     "code": "packet->payload_packet_len > 8",
     "line": 55
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "line": 55
    },
    {
     "code": "get_u_int16_t(packet->payload, 2) == htons(0x0201)",
     "line": 56
    },
    {
     "code": "get_u_int32_t(packet->payload, 4) == htonl(0xFFFFFFFF)",
     "line": 56
    },
    {
     "code": "packet->payload_packet_len == 406",
     "line": 61
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "line": 61
    },
    {
     "code": "packet->payload[2] == 0x63",
     "line": 62
    },
    {
     "code": "packet->payload_packet_len == 12",
     "line": 67
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "line": 67
    },
    {
     "code": "get_u_int16_t(packet->payload, 2) == htons(0x0301)",
     "line": 68
    },
    {
     "code": "flow->florensia_stage == 1",
     "line": 69
    },
    {
     "code": "flow->florensia_stage == 1",
     "line": 79
    },
    {
     "code": "packet->payload_packet_len == 8",
     "line": 80
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "line": 80
    },
    {
     "code": "get_u_int16_t(packet->payload, 2) == htons(0x0302)",
     "line": 81
    },
    {
     "code": "get_u_int32_t(packet->payload, 4) == htonl(0xFFFFFFFF)",
     "line": 81
    },
    {
     "code": "packet->payload_packet_len == 24",
     "line": 86
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "line": 86
    },
    {
     "code": "get_u_int16_t(packet->payload, 2) == htons(0x0202)",
     "line": 87
    },
    {
     "code": "get_u_int32_t(packet->payload, packet->payload_packet_len - 4) == htonl(0xFFFFFFFF)",
     "line": 88
    },
    {
     "code": "flow->packet_counter < 10",
     "line": 93
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "line": 93
    },
    {
     "code": "packet->udp != NULL",
     "line": 100
    },
    {
     "code": "flow->florensia_stage == 0",
     "line": 101
    },
    {
     "code": "packet->payload_packet_len == 6",
     "line": 101
    },
    {
     "code": "get_u_int16_t(packet->payload, 0) == ntohs(0x0503)",
     "line": 102
    },
    {
     "code": "get_u_int32_t(packet->payload, 2) == htonl(0xFFFF0000)",
     "line": 102
    },
    {
     "code": "flow->florensia_stage == 1",
     "line": 107
    },
    {
     "code": "packet->payload_packet_len == 8",
     "line": 107
    },
    {
     "code": "get_u_int16_t(packet->payload, 0) == ntohs(0x0500)",
     "line": 108
    },
    {
     "code": "get_u_int16_t(packet->payload, 4) == htons(0x4191)",
     "line": 108
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "flow->packet_counter < 10 && get_l16(packet->payload, 0) == packet->payload_packet_len",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "flow->packet_counter < 10",
     "name": "<operator>.lessThan",
     "nargs": 2
    },
    {
     "code": "flow->packet_counter",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "get_l16(packet->payload, 0) == packet->payload_packet_len",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "get_l16(packet->payload, 0)",
     "name": "get_l16",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload_packet_len",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "flow",
    "packet"
   ],
   "osv_id": "ARVO-42514542",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_florensia"
  }
 },
 {
  "osv_id": "ARVO-42514547",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "r",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmsmtrx.c",
    "line": 114,
    "size": null,
    "type": "cmsMAT3*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 120,
    "fn": "_cmsMAT3per",
    "code": "_cmsVEC3init(&r-> v[1], ROWCOL(1,0), ROWCOL(1,1), ROWCOL | &r-> v[1] | r-> v[1] | r-> v",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_cmsMAT3per",
    "file": "/src/lcms/src/cmsmtrx.c",
    "line": 120
   },
   "code": "_cmsVEC3init(&r-> v[1], ROWCOL(1,0), ROWCOL(1,1), ROWCOL | &r-> v[1] | r-> v[1] | r-> v",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_cmsMAT3per",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "cmsMAT3*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "r",
   "a",
   "b"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/a9796f61c682f5320ff572c888062ee34315b836/ARVO-42514547/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_a9796f61c682.cpg",
   "testcase_size": 628
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
   "dedup_token": "_cmsMAT3per--OptimizeMatrixShaper--_cmsOptimizePipeline"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 114,
    "type": "cmsMAT3*"
   },
   "entity_name_cpg": "r",
   "func_lines": [
    114,
    124
   ],
   "func_params": {
    "names": [
     "r",
     "a",
     "b"
    ],
    "types": [
     "cmsMAT3*",
     "cmsMAT3*",
     "cmsMAT3*"
    ]
   },
   "guards": [],
   "line_call_count": 94,
   "line_calls": [
    {
     "code": "_cmsVEC3init(&r-> v[1], ROWCOL(1,0), ROWCOL(1,1), ROWCOL(1,2))",
     "name": "_cmsVEC3init",
     "nargs": 4
    },
    {
     "code": "&r-> v[1]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "r-> v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "r-> v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ROWCOL(1,0)",
     "name": "ROWCOL",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[0] + a->v[1].n[1] * b->v[1].n[0] + a->v[1].n[2] * b->v[2].n[0]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[0] + a->v[1].n[1] * b->v[1].n[0]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[0]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0].n[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[1] * b->v[1].n[0]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1].n[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[2] * b->v[2].n[0]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2].n[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ROWCOL(1,1)",
     "name": "ROWCOL",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[1] + a->v[1].n[1] * b->v[1].n[1] + a->v[1].n[2] * b->v[2].n[1]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[1] + a->v[1].n[1] * b->v[1].n[1]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[1]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0].n[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[1] * b->v[1].n[1]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1].n[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[2] * b->v[2].n[1]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2].n[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "ROWCOL(1,2)",
     "name": "ROWCOL",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[2] + a->v[1].n[1] * b->v[1].n[2] + a->v[1].n[2] * b->v[2].n[2]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[2] + a->v[1].n[1] * b->v[1].n[2]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0] * b->v[0].n[2]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0].n[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[1] * b->v[1].n[2]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1].n[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[2] * b->v[2].n[2]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "a->v[1].n[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "a->v[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "a->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2].n[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2].n",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "b->v[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->v",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "r",
    "a",
    "b"
   ],
   "osv_id": "ARVO-42514547",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_cmsMAT3per"
  }
 },
 {
  "osv_id": "ARVO-42514634",
  "project": "libredwg",
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
    "fn": "dynapi_set_helper",
    "file": "/src/libredwg/src/gen-dynapi.pl",
    "line": 3111
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "f->size ;; 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3112,
    "fn": "dynapi_set_helper",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "dynapi_set_helper",
    "file": "/src/libredwg/src/gen-dynapi.pl",
    "line": 3112
   },
   "code": "",
   "access": {
    "dir": "WRITE",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dynapi_set_helper",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/fe03c5a89cbd441b6840335bd484cf08bc65c7c4/ARVO-42514634/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_fe03c5a89cbd.cpg",
   "testcase_size": 35
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "__interceptor_strcpy--strcpy--dynapi_set_helper"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    14262,
    14318
   ],
   "func_params": {
    "names": [
     "old",
     "f",
     "dwg_version",
     "value",
     "is_utf8"
    ],
    "types": [
     "void*restrict",
     "Dwg_DYNAPI_field*restrict",
     "Dwg_Version_Type",
     "void*restrict",
     "bool"
    ]
   },
   "guards": [
    {
     "code": "dwg_version < R_2007",
     "line": 14284
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42514634",
   "sites": [
    {
     "args": "f->size ;; 1",
     "callee": "calloc",
     "code": "calloc (f->size, 1)",
     "line": 14279
    },
    {
     "args": "strlen (*(char**)value)+1",
     "callee": "malloc",
     "code": "malloc (strlen (*(char**)value)+1)",
     "line": 14287
    },
    {
     "args": "2 * length",
     "callee": "malloc",
     "code": "malloc (2 * length)",
     "line": 14307
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "dynapi_set_helper"
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