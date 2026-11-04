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
  "osv_id": "ARVO-42492106",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 65,
    "size": null,
    "type": "u8*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 73,
    "fn": "sc_asn1_read_tag",
    "code": "*p == 0xff || *p == 0 | *p == 0xff | *p | *p == 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_asn1_read_tag",
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 73
   },
   "code": "*p == 0xff || *p == 0 | *p == 0xff | *p | *p == 0",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_asn1_read_tag",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:71,IF:73,IF:88,DO:92,IF:93,IF:106,IF:111,IF:114,FOR:116,IF:130"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/ee1c8073c2ecd0d7644d64ef3f2a2be4b5752c6e/ARVO-42492106/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_ee1c8073c2ec.cpg",
   "testcase_size": 517
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "loc_offset": 437,
   "loc_kind": "stack_frame",
   "dedup_token": "sc_asn1_read_tag--sc_asn1_find_tag--cardos_have_2048bit_package"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*p = *buf",
     "line": 65
    }
   ],
   "entity_decl": {
    "line": 65,
    "type": "u8*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    62,
    134
   ],
   "func_params": {
    "names": [
     "buf",
     "buflen",
     "cla_out",
     "tag_out",
     "taglen"
    ],
    "types": [
     "u8**",
     "size_t",
     "unsigned int*",
     "unsigned int*",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "left == 0",
     "line": 71
    },
    {
     "code": "*p == 0xff",
     "line": 73
    },
    {
     "code": "*p == 0",
     "line": 73
    },
    {
     "code": "tag == SC_ASN1_TAG_PRIMITIVE",
     "line": 88
    },
    {
     "code": "left == 0",
     "line": 93
    },
    {
     "code": "n == 0",
     "line": 93
    },
    {
     "code": "left == 0",
     "line": 106
    },
    {
     "code": "len > sizeof a",
     "line": 114
    },
    {
     "code": "len > left",
     "line": 114
    },
    {
     "code": "i < len",
     "line": 116
    },
    {
     "code": "len > left",
     "line": 130
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "*p == 0xff ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "*p == 0xff",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*p",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*p == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*p",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "p"
   ],
   "osv_id": "ARVO-42492106",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_asn1_read_tag"
  }
 },
 {
  "osv_id": "ARVO-42492295",
  "project": "matio",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "matvar",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/matio/src/mat73.c",
    "line": 300,
    "size": null,
    "type": "matvar_t*"
   }
  },
  "alloc": {
   "size_expr_cpg": "matvar->nbytes",
   "size_expr_cpg_callee": "ComplexMalloc"
  },
  "sites": [
   {
    "code": "malloc(matvar->nbytes)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "malloc",
    "line": 342,
    "origin": "cpg",
    "args": "matvar->nbytes"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 346,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "malloc(matvar->nbytes)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "malloc",
    "line": 362,
    "origin": "cpg",
    "args": "matvar->nbytes"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 366,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "calloc(1, matvar->data_size)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "calloc",
    "line": 379,
    "origin": "cpg",
    "args": "1 ;; matvar->data_size"
   },
   {
    "code": "malloc(readcount)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "malloc",
    "line": 401,
    "origin": "cpg",
    "args": "readcount"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 406,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 419,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 424,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 432,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 442,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 451,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 460,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "malloc(readcount)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "malloc",
    "line": 471,
    "origin": "cpg",
    "args": "readcount"
   },
   {
    "code": "malloc(readcount)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "malloc",
    "line": 479,
    "origin": "cpg",
    "args": "readcount"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 488,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 503,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 510,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 519,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "kind": "free",
    "line": 623,
    "fn": "Mat_H5ReadFieldNames",
    "code": "free(matvar->data) | matvar->data",
    "origin": "report:crash",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 645,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 653,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "malloc(sparse->ndata*Mat_SizeOf(data_type))",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "malloc",
    "line": 659,
    "origin": "cpg",
    "args": "sparse->ndata*Mat_SizeOf(data_type)"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 724,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 740,
    "origin": "cpg",
    "args": "matvar->data"
   },
   {
    "code": "free(matvar->data)",
    "fn": "Mat_H5ReadFieldNames",
    "kind": "free",
    "line": 747,
    "origin": "cpg",
    "args": "matvar->data"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_H5ReadFieldNames",
    "file": "/src/matio/src/mat73.c",
    "line": 623
   },
   "code": "free(matvar->data) | matvar->data",
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_VarRead4",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:306,SWITCH:313,IF:317,IF:322,IF:324,IF:330,ELSE:332,ELSE:337,ELSE:341,IF:343,IF:345,ELSE:351"
  },
  "call_chain": [],
  "types": {
   "entity_type": "matvar_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "matvar"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/matio/address/1ce8f2d1845ecdde19a35605cabdbb884776d52d/ARVO-42492295/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_1ce8f2d1845e.cpg",
   "testcase_size": 37240
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
  "free_related": {
   "free_sites_in_func": [
    346,
    366,
    406,
    419,
    424,
    432,
    442,
    451,
    460,
    488,
    503,
    510,
    519,
    623,
    645,
    653,
    724,
    740,
    747
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 40,
   "loc_kind": "stack_frame",
   "dedup_token": "H5S_extent_get_dims--H5S_get_simple_extent_dims--H5Sget_simple_extent_dims"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "matvar->data_size = sizeof(double)",
     "line": 315
    },
    {
     "code": "matvar->data = complex_data",
     "line": 331
    },
    {
     "code": "matvar->data = malloc(matvar->nbytes)",
     "line": 342
    },
    {
     "code": "matvar->data = NULL",
     "line": 347
    },
    {
     "code": "matvar->data_type = MAT_T_DOUBLE",
     "line": 357
    },
    {
     "code": "matvar->data_size = 1",
     "line": 360
    },
    {
     "code": "matvar->nbytes = nelems",
     "line": 361
    },
    {
     "code": "matvar->data = malloc(matvar->nbytes)",
     "line": 362
    },
    {
     "code": "matvar->data = NULL",
     "line": 367
    },
    {
     "code": "matvar->data_type = MAT_T_UINT8",
     "line": 375
    },
    {
     "code": "matvar->data_size = sizeof(mat_sparse_t)",
     "line": 378
    },
    {
     "code": "matvar->data      = calloc(1, matvar->data_size)",
     "line": 379
    },
    {
     "code": "matvar->isComplex = matvar->dims[1] == 4 ? 1 : 0",
     "line": 389
    },
    {
     "code": "matvar->data = NULL",
     "line": 407
    },
    {
     "code": "matvar->data = NULL",
     "line": 420
    },
    {
     "code": "matvar->data = NULL",
     "line": 425
    },
    {
     "code": "matvar->data = NULL",
     "line": 433
    },
    {
     "code": "matvar->dims[0] = (size_t)tmp",
     "line": 437
    },
    {
     "code": "matvar->data = NULL",
     "line": 443
    },
    {
     "code": "matvar->data = NULL",
     "line": 452
    },
    {
     "code": "matvar->dims[1] = (size_t)tmp",
     "line": 456
    },
    {
     "code": "matvar->data = NULL",
     "line": 461
    },
    {
     "code": "matvar->data = NULL",
     "line": 489
    },
    {
     "code": "matvar->data = NULL",
     "line": 504
    },
    {
     "code": "matvar->data = NULL",
     "line": 511
    },
    {
     "code": "matvar->data = NULL",
     "line": 520
    },
    {
     "code": "matvar->data = NULL",
     "line": 624
    },
    {
     "code": "matvar->data = NULL",
     "line": 646
    },
    {
     "code": "matvar->data = NULL",
     "line": 654
    },
    {
     "code": "matvar->data = NULL",
     "line": 725
    },
    {
     "code": "matvar->data = NULL",
     "line": 741
    },
    {
     "code": "matvar->data = NULL",
     "line": 748
    }
   ],
   "entity_decl": {
    "line": 300,
    "type": "matvar_t*"
   },
   "entity_name_cpg": "matvar",
   "func_lines": [
    299,
    765
   ],
   "func_params": {
    "names": [
     "mat",
     "matvar"
    ],
    "types": [
     "mat_t*",
     "matvar_t*"
    ]
   },
   "guards": [
    {
     "code": "NULL != complex_data",
     "line": 324
    },
    {
     "code": "readcount != nelems",
     "line": 327
    },
    {
     "code": "readcount != nelems",
     "line": 329
    },
    {
     "code": "0 == err",
     "line": 330
    },
    {
     "code": "NULL != matvar->data",
     "line": 343
    },
    {
     "code": "readcount != nelems",
     "line": 345
    },
    {
     "code": "NULL != matvar->data",
     "line": 363
    },
    {
     "code": "readcount != nelems",
     "line": 365
    },
    {
     "code": "NULL != matvar->data",
     "line": 380
    },
    {
     "code": "matvar->dims[1] == 4",
     "line": 389
    },
    {
     "code": "matvar->dims[0] < 2",
     "line": 390
    },
    {
     "code": "sparse->ir != NULL",
     "line": 402
    },
    {
     "code": "readcount != sparse->nir",
     "line": 404
    },
    {
     "code": "i < sparse->nir",
     "line": 410
    },
    {
     "code": "0 == sparse->ir[i]",
     "line": 411
    },
    {
     "code": "readcount != 1",
     "line": 430
    },
    {
     "code": "tmp > UINT_MAX - 1",
     "line": 430
    },
    {
     "code": "tmp < 0",
     "line": 430
    },
    {
     "code": "fpos == -1L",
     "line": 440
    },
    {
     "code": "readcount != 1",
     "line": 449
    },
    {
     "code": "tmp > UINT_MAX - 1",
     "line": 449
    },
    {
     "code": "tmp < 0",
     "line": 449
    },
    {
     "code": "matvar->dims[1] > UINT_MAX - 1",
     "line": 458
    },
    {
     "code": "sparse->jc != NULL",
     "line": 472
    },
    {
     "code": "jc != NULL",
     "line": 480
    },
    {
     "code": "readcount != sparse->nir",
     "line": 484
    },
    {
     "code": "i < sparse->njc - 1",
     "line": 492
    },
    {
     "code": "j < sparse->nir",
     "line": 493
    },
    {
     "code": "readcount != 1",
     "line": 516
    },
    {
     "code": "NULL != complex_data",
     "line": 528
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 535
    },
    {
     "code": "readcount != 1",
     "line": 537
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 540
    },
    {
     "code": "readcount != 1",
     "line": 542
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 549
    },
    {
     "code": "readcount != 1",
     "line": 551
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 554
    },
    {
     "code": "readcount != 1",
     "line": 556
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 564
    },
    {
     "code": "readcount != 1",
     "line": 566
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 569
    },
    {
     "code": "readcount != 1",
     "line": 571
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 579
    },
    {
     "code": "readcount != 1",
     "line": 581
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 584
    },
    {
     "code": "readcount != 1",
     "line": 586
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 594
    },
    {
     "code": "readcount != 1",
     "line": 596
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 599
    },
    {
     "code": "readcount != 1",
     "line": 601
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 609
    },
    {
     "code": "readcount != 1",
     "line": 611
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 614
    },
    {
     "code": "readcount != 1",
     "line": 616
    },
    {
     "code": "sparse->data != NULL",
     "line": 660
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 666
    },
    {
     "code": "readcount != 1",
     "line": 668
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 675
    },
    {
     "code": "readcount != 1",
     "line": 677
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 685
    },
    {
     "code": "readcount != 1",
     "line": 687
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 695
    },
    {
     "code": "readcount != 1",
     "line": 697
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 705
    },
    {
     "code": "readcount != 1",
     "line": 707
    },
    {
     "code": "readcount != sparse->ndata",
     "line": 715
    },
    {
     "code": "readcount != 1",
     "line": 717
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "free(matvar->data)",
     "name": "free",
     "nargs": 1
    },
    {
     "code": "matvar->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "matvar"
   ],
   "osv_id": "ARVO-42492295",
   "sites": [
    {
     "args": "matvar->nbytes",
     "callee": "ComplexMalloc",
     "code": "ComplexMalloc(matvar->nbytes)",
     "line": 323
    },
    {
     "args": "complex_data",
     "callee": "ComplexFree",
     "code": "ComplexFree(complex_data)",
     "line": 333
    },
    {
     "args": "matvar->nbytes",
     "callee": "malloc",
     "code": "malloc(matvar->nbytes)",
     "line": 342
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 346
    },
    {
     "args": "matvar->nbytes",
     "callee": "malloc",
     "code": "malloc(matvar->nbytes)",
     "line": 362
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 366
    },
    {
     "args": "1 ;; matvar->data_size",
     "callee": "calloc",
     "code": "calloc(1, matvar->data_size)",
     "line": 379
    },
    {
     "args": "readcount",
     "callee": "malloc",
     "code": "malloc(readcount)",
     "line": 401
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 405
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 406
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 418
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 419
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 424
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 431
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 432
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 441
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 442
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 450
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 451
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 459
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 460
    },
    {
     "args": "readcount",
     "callee": "malloc",
     "code": "malloc(readcount)",
     "line": 471
    },
    {
     "args": "readcount",
     "callee": "malloc",
     "code": "malloc(readcount)",
     "line": 479
    },
    {
     "args": "jc",
     "callee": "free",
     "code": "free(jc)",
     "line": 485
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 486
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 487
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 488
    },
    {
     "args": "jc",
     "callee": "free",
     "code": "free(jc)",
     "line": 497
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 501
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 502
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 503
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 509
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 510
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 517
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 518
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 519
    },
    {
     "args": "sparse->ndata*Mat_SizeOf(data_type)",
     "callee": "ComplexMalloc",
     "code": "ComplexMalloc(sparse->ndata*Mat_SizeOf(data_type))",
     "line": 527
    },
    {
     "args": "complex_data",
     "callee": "ComplexFree",
     "code": "ComplexFree(complex_data)",
     "line": 620
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 621
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 622
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 623
    },
    {
     "args": "complex_data",
     "callee": "ComplexFree",
     "code": "ComplexFree(complex_data)",
     "line": 642
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 643
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 644
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 645
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 651
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 652
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 653
    },
    {
     "args": "sparse->ndata*Mat_SizeOf(data_type)",
     "callee": "malloc",
     "code": "malloc(sparse->ndata*Mat_SizeOf(data_type))",
     "line": 659
    },
    {
     "args": "sparse->data",
     "callee": "free",
     "code": "free(sparse->data)",
     "line": 721
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 722
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 723
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 724
    },
    {
     "args": "sparse->data",
     "callee": "free",
     "code": "free(sparse->data)",
     "line": 737
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 738
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 739
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 740
    },
    {
     "args": "sparse->jc",
     "callee": "free",
     "code": "free(sparse->jc)",
     "line": 745
    },
    {
     "args": "sparse->ir",
     "callee": "free",
     "code": "free(sparse->ir)",
     "line": 746
    },
    {
     "args": "matvar->data",
     "callee": "free",
     "code": "free(matvar->data)",
     "line": 747
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "Mat_H5ReadFieldNames",
   "use_fn": "Mat_H5ReadFieldNames"
  }
 },
 {
  "osv_id": "ARVO-42492641",
  "project": "ndpi",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "rc",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 1009,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "size_expr_cpg": "JA3_STR_LEN",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 991,
    "fn": "processClientServerHello",
    "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3 | snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_ | &ja3_str[ja3_str_len] | ja3_str[ja3_str_len]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "processClientServerHello",
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 991
   },
   "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3 | snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_ | &ja3_str[ja3_str_len] | ja3_str[ja3_str_len]",
   "access": {
    "dir": "WRITE",
    "width": 6,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "processClientServerHello",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i<extension_len | i<ja3.num_cipher | i > 0",
   "guard_count": 33,
   "control_structures": "IF:880,IF:886,IF:891,IF:900,IF:903,IF:914,ELSE:916,IF:917,IF:921,IF:925,IF:936,ELSE:939"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/ndpi/address/32bd3d7a599a6dfcfadf6ed4ad684f904e50719c/ARVO-42492641/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_32bd3d7a599a.cpg",
   "testcase_size": 15176
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
   "loc_offset": 5427,
   "loc_kind": "stack_frame",
   "dedup_token": "vsnprintf--snprintf--processClientServerHello"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\", (i > 0) ? \"-\" : \"\", ja3.cipher[i])",
     "line": 980
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \",\")",
     "line": 985
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\", (i > 0) ? \"-\" : \"\", ja3.tls_extension[i])",
     "line": 991
    },
    {
     "code": "rc = snprintf(&flow->protos.stun_ssl.ssl.ja3_server[j],",
     "line": 1009
    },
    {
     "code": "rc = snprintf(&version_str[version_str_len],",
     "line": 1287
    },
    {
     "code": "rc = sprintf(&flow->protos.stun_ssl.ssl.encrypted_sni.esni[off], \"%02X\", packet->payload[i] & 0XFF)",
     "line": 1338
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\",",
     "line": 1367
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \",\")",
     "line": 1372
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\",",
     "line": 1378
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \",\")",
     "line": 1383
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\",",
     "line": 1389
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \",\")",
     "line": 1394
    },
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\",",
     "line": 1398
    },
    {
     "code": "rc = snprintf(&flow->protos.stun_ssl.ssl.ja3_client[j],",
     "line": 1412
    }
   ],
   "entity_decl": {
    "line": 904,
    "type": "int"
   },
   "entity_name_cpg": "rc",
   "func_lines": [
    857,
    1448
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
     "code": "total_len > packet->payload_packet_len",
     "line": 880
    },
    {
     "code": "packet->payload[1] != 0x0",
     "line": 880
    },
    {
     "code": "total_len > 4",
     "line": 886
    },
    {
     "code": "base_offset < total_len",
     "line": 891
    },
    {
     "code": "flow->protos.stun_ssl.ssl.ssl_version < 0x0302",
     "line": 900
    },
    {
     "code": "handshake_type == 0x02",
     "line": 903
    },
    {
     "code": "tls_version < 0x7F15",
     "line": 917
    },
    {
     "code": "(offset+3) > packet->payload_packet_len",
     "line": 921
    },
    {
     "code": "(flow->protos.stun_ssl.ssl.server_unsafe_cipher = ndpi_is_safe_ssl_cipher(ja3.cipher[0])) == 1",
     "line": 925
    },
    {
     "code": "(offset + 1) < packet->payload_packet_len",
     "line": 936
    },
    {
     "code": "i<extension_len",
     "line": 946
    },
    {
     "code": "(offset+4) > packet->payload_packet_len",
     "line": 949
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 954
    },
    {
     "code": "extension_id == 43",
     "line": 962
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 979
    },
    {
     "code": "i > 0",
     "line": 980
    },
    {
     "code": "rc > 0",
     "line": 986
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 986
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 990
    },
    {
     "code": "i > 0",
     "line": 991
    },
    {
     "code": "i<16",
     "line": 1008
    },
    {
     "code": "handshake_type == 0x01",
     "line": 1017
    },
    {
     "code": "(session_id_len+base_offset+3) > packet->payload_packet_len",
     "line": 1020
    },
    {
     "code": "i<cipher_len",
     "line": 1036
    },
    {
     "code": "*id == 0",
     "line": 1042
    },
    {
     "code": "packet->payload[cipher_offset+i] != packet->payload[cipher_offset+i+1]",
     "line": 1042
    },
    {
     "code": "ja3.num_cipher < MAX_NUM_JA3",
     "line": 1048
    },
    {
     "code": "offset < total_len",
     "line": 1069
    },
    {
     "code": "offset < total_len",
     "line": 1084
    },
    {
     "code": "extension_offset < extensions_len",
     "line": 1098
    },
    {
     "code": "extension_id == 0",
     "line": 1111
    },
    {
     "code": "packet->payload[extn_off] != packet->payload[extn_off+1]",
     "line": 1111
    },
    {
     "code": "ja3.num_tls_extension < MAX_NUM_JA3",
     "line": 1114
    },
    {
     "code": "extension_id == 0",
     "line": 1124
    },
    {
     "code": "extension_id == 10",
     "line": 1155
    },
    {
     "code": "i<extension_len-2",
     "line": 1163
    },
    {
     "code": "s_group == 0",
     "line": 1169
    },
    {
     "code": "packet->payload[s_offset+i] != packet->payload[s_offset+i+1]",
     "line": 1169
    },
    {
     "code": "ja3.num_elliptic_curve < MAX_NUM_JA3",
     "line": 1171
    },
    {
     "code": "extension_id == 11",
     "line": 1189
    },
    {
     "code": "i<extension_len-1",
     "line": 1196
    },
    {
     "code": "ja3.num_elliptic_curve_point_format < MAX_NUM_JA3",
     "line": 1203
    },
    {
     "code": "extension_id == 16",
     "line": 1218
    },
    {
     "code": "s_offset < tot_alpn_len",
     "line": 1230
    },
    {
     "code": "s_offset < total_len",
     "line": 1230
    },
    {
     "code": "(alpn_str_len+alpn_len+1) < (sizeof(alpn_str)-1)",
     "line": 1238
    },
    {
     "code": "alpn_str_len > 0",
     "line": 1239
    },
    {
     "code": "alpn_i<alpn_len",
     "line": 1244
    },
    {
     "code": "flow->protos.stun_ssl.ssl.alpn == NULL",
     "line": 1259
    },
    {
     "code": "extension_id == 43",
     "line": 1261
    },
    {
     "code": "version_len == (extension_len-1)",
     "line": 1271
    },
    {
     "code": "j+1<version_len",
     "line": 1277
    },
    {
     "code": "(version_str_len+8) < sizeof(version_str)",
     "line": 1286
    },
    {
     "code": "version_str_len > 0",
     "line": 1289
    },
    {
     "code": "flow->protos.stun_ssl.ssl.tls_supported_versions == NULL",
     "line": 1297
    },
    {
     "code": "extension_id == 65486",
     "line": 1300
    },
    {
     "code": "(e_offset+4) < packet->payload_packet_len",
     "line": 1317
    },
    {
     "code": "(e_offset+4) < packet->payload_packet_len",
     "line": 1321
    },
    {
     "code": "e_offset+e_sni_len < packet->payload_packet_len",
     "line": 1326
    },
    {
     "code": "flow->protos.stun_ssl.ssl.encrypted_sni.esni == NULL",
     "line": 1331
    },
    {
     "code": "i<(e_offset+e_sni_len)",
     "line": 1337
    },
    {
     "code": "i<ja3.num_cipher",
     "line": 1366
    },
    {
     "code": "i > 0",
     "line": 1368
    },
    {
     "code": "rc > 0",
     "line": 1369
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1369
    },
    {
     "code": "rc > 0",
     "line": 1373
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1373
    },
    {
     "code": "i<ja3.num_tls_extension",
     "line": 1377
    },
    {
     "code": "i > 0",
     "line": 1379
    },
    {
     "code": "rc > 0",
     "line": 1380
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1380
    },
    {
     "code": "rc > 0",
     "line": 1384
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1384
    },
    {
     "code": "i<ja3.num_elliptic_curve",
     "line": 1388
    },
    {
     "code": "i > 0",
     "line": 1390
    },
    {
     "code": "rc > 0",
     "line": 1391
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1391
    },
    {
     "code": "rc > 0",
     "line": 1395
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1395
    },
    {
     "code": "i<ja3.num_elliptic_curve_point_format",
     "line": 1397
    },
    {
     "code": "i > 0",
     "line": 1399
    },
    {
     "code": "rc > 0",
     "line": 1400
    },
    {
     "code": "ja3_str_len + rc < JA3_STR_LEN",
     "line": 1400
    },
    {
     "code": "i<16",
     "line": 1411
    },
    {
     "code": "rc > 0",
     "line": 1415
    },
    {
     "code": "flow->protos.stun_ssl.ssl.alpn == NULL",
     "line": 1424
    },
    {
     "code": "offset == total_len",
     "line": 1435
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "rc = snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\", (i > 0) ? \"-\" : \"\", ja3.tls_extension[i])",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "snprintf(&ja3_str[ja3_str_len], sizeof(ja3_str)-ja3_str_len, \"%s%u\", (i > 0) ? \"-\" : \"\", ja3.tls_extension[i])",
     "name": "snprintf",
     "nargs": 5
    },
    {
     "code": "&ja3_str[ja3_str_len]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "ja3_str[ja3_str_len]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "sizeof(ja3_str)-ja3_str_len",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "sizeof(ja3_str)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    },
    {
     "code": "(i > 0) ? \"-\" : \"\"",
     "name": "<operator>.conditional",
     "nargs": 3
    },
    {
     "code": "i > 0",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "ja3.tls_extension[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "ja3.tls_extension",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "rc",
    "ja3_str",
    "ja3_str_len",
    "i",
    "ja3"
   ],
   "osv_id": "ARVO-42492641",
   "sites": [
    {
     "args": "JA3_STR_LEN",
     "callee": "<operator>.alloc",
     "code": "ja3_str[JA3_STR_LEN]",
     "line": 863
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "md5_hash[16]",
     "line": 865
    },
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "buffer[64] = { '\\0' }",
     "line": 869
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "alpn_str[256]",
     "line": 1221
    },
    {
     "args": "alpn_str",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(alpn_str)",
     "line": 1260
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "version_str[256]",
     "line": 1264
    },
    {
     "args": "version_str",
     "callee": "ndpi_strdup",
     "code": "ndpi_strdup(version_str)",
     "line": 1298
    },
    {
     "args": "e_sni_len*2+1",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(e_sni_len*2+1)",
     "line": 1332
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "processClientServerHello"
  }
 },
 {
  "osv_id": "ARVO-42493128",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "sTransmitFrame",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 203,
    "fn": "ot::Coap::Message::AppendUintOption(unsigned short, unsigned int)",
    "code": "sTransmitFrame.mPsdu   = sTransmitPsdu | sTransmitFrame.mPsdu",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::Coap::Message::AppendUintOption(unsigned short, unsigned int)",
    "file": "/src/openthread/src/core/coap/coap_message.cpp",
    "line": 203
   },
   "code": "sTransmitFrame.mPsdu   = sTransmitPsdu | sTransmitFrame.mPsdu",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rfCoreInitBufs",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/2cd36266abaaf8b79ebb0441e6ed2ec3847cf3ca/ARVO-42493128/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_2cd36266abaa.cpg",
   "testcase_size": 21
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
   "loc_offset": 36,
   "loc_kind": "stack_frame",
   "dedup_token": "ot::Coap::Message::AppendUintOption(unsigned short, unsigned int)--ot::Coap::Message::AppendBlockOption(ot::Coap::Message::BlockType, unsigned int, bool, otCoap"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "sTransmitFrame.mPsdu   = sTransmitPsdu",
     "line": 203
    },
    {
     "code": "sTransmitFrame.mLength = 0",
     "line": 204
    }
   ],
   "entity_name_cpg": "sTransmitFrame",
   "func_lines": [
    175,
    205
   ],
   "func_params": {
    "names": [],
    "types": [
     "void"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "sTransmitFrame.mPsdu   = sTransmitPsdu",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "sTransmitFrame.mPsdu",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "sTransmitFrame",
    "sTransmitPsdu"
   ],
   "osv_id": "ARVO-42493128",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::Coap::Message::AppendUintOption(unsigned short, unsigned int)"
  }
 },
 {
  "osv_id": "ARVO-42496362",
  "project": "kimageformats",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "data",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/kimageformats/src/imageformats/xcf.cpp",
    "line": 1570,
    "size": null,
    "type": "uchar*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1669,
    "fn": "XCFImageFormat::loadTileRLE(QDataStream&, unsigned char*, int, int, int)",
    "code": "*data = val | *data",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "XCFImageFormat::loadTileRLE(QDataStream&, unsigned char*, int, int, int)",
    "file": "/src/kimageformats/src/imageformats/xcf.cpp",
    "line": 1669
   },
   "code": "*data = val | *data",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "loadTileRLE",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1576,IF:1584,IF:1590,IF:1594,FOR:1602,WHILE:1609,IF:1610,GOTO:1611,IF:1617,IF:1619,IF:1620,GOTO:1621"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uchar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "tile",
   "bpp"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/kimageformats/address/497b6b81bdf59afe1551b2ea38fcc45fe100057d/ARVO-42496362/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_497b6b81bdf5.cpg",
   "testcase_size": 29614
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
   "loc_offset": 16696,
   "loc_kind": "stack_frame",
   "dedup_token": "XCFImageFormat::loadTileRLE(QDataStream&, unsigned char*, int, int, int)--XCFImageFormat::loadLevel(QDataStream&, XCFImageFormat::Layer&, int)--XCFImageFormat::"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "data = tile + i",
     "line": 1604
    }
   ],
   "entity_decl": {
    "line": 1570,
    "type": "uchar*"
   },
   "entity_name_cpg": "data",
   "func_lines": [
    1567,
    1684
   ],
   "func_params": {
    "names": [
     "this",
     "xcf_io",
     "tile",
     "image_size",
     "data_length",
     "bpp"
    ],
    "types": [
     "XCFImageFormat",
     "QDataStream&",
     "uchar*",
     "int",
     "int",
     "qint32"
    ]
   },
   "guards": [
    {
     "code": "data_length < 0",
     "line": 1576
    },
    {
     "code": "data_length > int(TILE_WIDTH * TILE_HEIGHT * 4 * 1.5)",
     "line": 1576
    },
    {
     "code": "dataRead < data_length",
     "line": 1590
    },
    {
     "code": "i < bpp",
     "line": 1602
    },
    {
     "code": "size > 0",
     "line": 1609
    },
    {
     "code": "xcfdata > xcfdatalimit",
     "line": 1610
    },
    {
     "code": "length == 128",
     "line": 1619
    },
    {
     "code": "size < 0",
     "line": 1632
    },
    {
     "code": "&xcfdata[length - 1] > xcfdatalimit",
     "line": 1636
    },
    {
     "code": "length-- > 0",
     "line": 1640
    },
    {
     "code": "length == 128",
     "line": 1646
    },
    {
     "code": "size < 0",
     "line": 1658
    },
    {
     "code": "xcfdata > xcfdatalimit",
     "line": 1662
    },
    {
     "code": "length-- > 0",
     "line": 1668
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "*data = val",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*data",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "data",
    "val"
   ],
   "osv_id": "ARVO-42496362",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "XCFImageFormat::loadTileRLE(QDataStream&, unsigned char*, int, int, int)"
  }
 },
 {
  "osv_id": "ARVO-42496381",
  "project": "openthread",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "pFilter",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "line": 714,
    "size": null,
    "type": "PMS_FILTER"
   }
  },
  "alloc": {
   "size_expr_cpg": "ARRAYSIZE(WaitEvents)",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 779,
    "fn": "ot::MeshCoP::CommissionerSessionIdTlv::GetCommissionerSessionId() const",
    "code": "pFilter->otCtx == NULL | pFilter->otCtx",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ot::MeshCoP::CommissionerSessionIdTlv::GetCommissionerSessionId() const",
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "line": 779
   },
   "code": "pFilter->otCtx == NULL | pFilter->otCtx",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "otLwfEventWorkerThread",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "MessageBuffer == NULL | pFilter == NULL | pFilter->otCtx == NULL",
   "guard_count": 10,
   "control_structures": "IF:737,IF:764,GOTO:767,IF:779,GOTO:782,FOR:801,IF:805,ELSE:815,IF:819,ELSE:833,IF:844,BREAK:847"
  },
  "call_chain": [],
  "types": {
   "entity_type": "PMS_FILTER",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "Context"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/71d40a5c838d345248fbc130c74182dda99d85f1/ARVO-42496381/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_71d40a5c838d.cpg",
   "testcase_size": 424
  },
  "type_reconciliation": {
   "report_fault_kind": null,
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "loc_offset": 287,
   "loc_kind": "stack_frame",
   "dedup_token": "ot::MeshCoP::CommissionerSessionIdTlv::GetCommissionerSessionId() const--ot::NetworkData::Leader::HandleCommissioningSet(ot::Coap::Header&, ot::Message&, ot::Ip"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pFilter = (PMS_FILTER)Context",
     "line": 714
    },
    {
     "code": "pFilter->otInstanceSize = 0",
     "line": 755
    },
    {
     "code": "pFilter->otInstanceBuffer = (PUCHAR)FILTER_ALLOC_MEM(pFilter->FilterHandle, (ULONG)pFilter->otInstanceSize)",
     "line": 763
    },
    {
     "code": "pFilter->otCachedRole = OT_DEVICE_ROLE_DISABLED",
     "line": 776
    },
    {
     "code": "pFilter->otCtx = otInstanceInit(pFilter->otInstanceBuffer + sizeof(PMS_FILTER), &pFilter->otInstanceSize)",
     "line": 777
    },
    {
     "code": "pFilter->NextAlarmTickCount.QuadPart = 0",
     "line": 862
    },
    {
     "code": "pFilter->EventTimerState = OT_EVENT_TIMER_NOT_RUNNING",
     "line": 863
    },
    {
     "code": "pFilter->otReceiveFrame.mLength = (uint8_t)packetLength",
     "line": 994
    }
   ],
   "entity_decl": {
    "line": 714,
    "type": "PMS_FILTER"
   },
   "entity_name_cpg": "pFilter",
   "func_lines": [
    709,
    1114
   ],
   "func_params": {
    "names": [
     "Context"
    ],
    "types": [
     "PVOID"
    ]
   },
   "guards": [
    {
     "code": "MessageBuffer == NULL",
     "line": 737
    },
    {
     "code": "pFilter->otInstanceSize != 0",
     "line": 757
    },
    {
     "code": "pFilter == NULL",
     "line": 764
    },
    {
     "code": "pFilter->otCtx == NULL",
     "line": 779
    },
    {
     "code": "otCtxToFilter(pFilter->otCtx) == pFilter",
     "line": 786
    },
    {
     "code": "pFilter->NextAlarmTickCount.QuadPart == 0",
     "line": 805
    },
    {
     "code": "pFilter->NextAlarmTickCount.QuadPart > SystemTickCount.QuadPart",
     "line": 819
    },
    {
     "code": "status == STATUS_WAIT_0",
     "line": 844
    },
    {
     "code": "status == STATUS_TIMEOUT",
     "line": 858
    },
    {
     "code": "pFilter->EventTimerState == OT_EVENT_TIMER_FIRED",
     "line": 859
    },
    {
     "code": "status == STATUS_WAIT_0 + 3",
     "line": 859
    },
    {
     "code": "status == STATUS_WAIT_0 + 1",
     "line": 868
    },
    {
     "code": "Event == NULL",
     "line": 886
    },
    {
     "code": "CurrNbl != NULL",
     "line": 893
    },
    {
     "code": "CurrNb != NULL",
     "line": 896
    },
    {
     "code": "error != OT_ERROR_NONE",
     "line": 912
    },
    {
     "code": "error != OT_ERROR_NONE",
     "line": 931
    },
    {
     "code": "status == STATUS_WAIT_0 + 2",
     "line": 964
    },
    {
     "code": "Event == NULL",
     "line": 982
    },
    {
     "code": "Event->BufferLength > sizeof(uint16_t) + packetLength",
     "line": 992
    },
    {
     "code": "packetLength != 0",
     "line": 999
    },
    {
     "code": "status == STATUS_WAIT_0 + 3",
     "line": 1037
    },
    {
     "code": "status == STATUS_WAIT_0 + 4",
     "line": 1041
    },
    {
     "code": "status == STATUS_WAIT_0 + 5",
     "line": 1046
    },
    {
     "code": "status == STATUS_WAIT_0 + 6",
     "line": 1051
    },
    {
     "code": "status == STATUS_WAIT_0 + 7",
     "line": 1056
    },
    {
     "code": "Event == NULL",
     "line": 1074
    },
    {
     "code": "status == STATUS_WAIT_0 + 8",
     "line": 1083
    },
    {
     "code": "pFilter->otRadioState == OT_RADIO_STATE_TRANSMIT",
     "line": 1094
    },
    {
     "code": "pFilter->otInstanceBuffer != NULL",
     "line": 1104
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "pFilter->otCtx == NULL",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "pFilter->otCtx",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "pFilter",
    "NULL"
   ],
   "osv_id": "ARVO-42496381",
   "sites": [
    {
     "args": "ARRAYSIZE(WaitEvents)",
     "callee": "<operator>.alloc",
     "code": "WaitBlocks[ARRAYSIZE(WaitEvents)] = { 0 }",
     "line": 732
    },
    {
     "args": "pFilter->FilterHandle ;; MessageBufferSize",
     "callee": "FILTER_ALLOC_MEM",
     "code": "FILTER_ALLOC_MEM(pFilter->FilterHandle, MessageBufferSize)",
     "line": 736
    },
    {
     "args": "pFilter->FilterHandle ;; MessageBufferSize ;; 'mFto' ;; LowPoolPriority",
     "callee": "NdisAllocateMemoryWithTagPriority",
     "code": "NdisAllocateMemoryWithTagPriority(pFilter->FilterHandle, MessageBufferSize, 'mFto', LowPoolPriority)",
     "line": 736
    },
    {
     "args": "pFilter->FilterHandle ;; (ULONG)pFilter->otInstanceSize",
     "callee": "FILTER_ALLOC_MEM",
     "code": "FILTER_ALLOC_MEM(pFilter->FilterHandle, (ULONG)pFilter->otInstanceSize)",
     "line": 763
    },
    {
     "args": "pFilter->FilterHandle ;; (ULONG)pFilter->otInstanceSize ;; 'mFto' ;; LowPoolPriority",
     "callee": "NdisAllocateMemoryWithTagPriority",
     "code": "NdisAllocateMemoryWithTagPriority(pFilter->FilterHandle, (ULONG)pFilter->otInstanceSize, 'mFto', LowPoolPriority)",
     "line": 763
    },
    {
     "args": "message",
     "callee": "otMessageFree",
     "code": "otMessageFree(message)",
     "line": 915
    },
    {
     "args": "Event ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(Event, 0, 0)",
     "line": 961
    },
    {
     "args": "Event ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(Event, 0, 0)",
     "line": 1034
    },
    {
     "args": "Event ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(Event, 0, 0)",
     "line": 1080
    },
    {
     "args": "pFilter->otInstanceBuffer ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(pFilter->otInstanceBuffer, 0, 0)",
     "line": 1106
    },
    {
     "args": "MessageBuffer",
     "callee": "FILTER_FREE_MEM",
     "code": "FILTER_FREE_MEM(MessageBuffer)",
     "line": 1111
    },
    {
     "args": "MessageBuffer ;; 0 ;; 0",
     "callee": "NdisFreeMemory",
     "code": "NdisFreeMemory(MessageBuffer, 0, 0)",
     "line": 1111
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ot::MeshCoP::CommissionerSessionIdTlv::GetCommissionerSessionId() const"
  }
 },
 {
  "osv_id": "ARVO-42497018",
  "project": "espeak-ng",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "pn",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 2561,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "size_expr_cpg": "N_TR_SOURCE+4",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2649,
    "fn": "TranslateClause",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "TranslateClause",
    "file": "/src/espeak-ng/src/libespeak-ng/translate.c",
    "line": 2649
   },
   "code": "memcpy(pn, pw, 16)",
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "TranslateClause",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/espeak-ng/address/0a713d52bbf3e061823d1a7f35e5303e7320f27a/ARVO-42497018/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0a713d52bbf3.cpg",
   "testcase_size": 754
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 6432,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--TranslateClause--SpeakNextClause"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "pn = number_buf",
     "line": 2584
    },
    {
     "code": "pn = &number_buf[1]",
     "line": 2609
    },
    {
     "code": "pn[16] = 0",
     "line": 2650
    }
   ],
   "entity_decl": {
    "line": 2561,
    "type": "char*"
   },
   "entity_name_cpg": "pn",
   "func_lines": [
    1984,
    2742
   ],
   "func_params": {
    "names": [
     "tr",
     "tone_out",
     "voice_change"
    ],
    "types": [
     "Translator*",
     "int*",
     "char**"
    ]
   },
   "guards": [
    {
     "code": "tr == NULL",
     "line": 2031
    },
    {
     "code": "(clause_start_char = count_characters) < 0",
     "line": 2039
    },
    {
     "code": "ix < N_TR_SOURCE",
     "line": 2043
    },
    {
     "code": "tone_out != NULL",
     "line": 2047
    },
    {
     "code": "tone == 0",
     "line": 2048
    },
    {
     "code": "*p != 0",
     "line": 2062
    },
    {
     "code": "*p == 0",
     "line": 2066
    },
    {
     "code": "clause_pause < 0",
     "line": 2070
    },
    {
     "code": "skip_sentences > 0",
     "line": 2085
    },
    {
     "code": "skip_sentences == 0",
     "line": 2087
    },
    {
     "code": "charix[j] != 0",
     "line": 2123
    },
    {
     "code": "charix[j++] != -1",
     "line": 2125
    },
    {
     "code": "ix < (int)sizeof(sbuf) - 1",
     "line": 2130
    },
    {
     "code": "n_ph_list2 < N_PHONEME_LIST-4",
     "line": 2130
    },
    {
     "code": "prev_in_save != 0",
     "line": 2139
    },
    {
     "code": "source_index > 0",
     "line": 2142
    },
    {
     "code": "c == 0",
     "line": 2156
    },
    {
     "code": "c == CTRL_EMBEDDED",
     "line": 2161
    },
    {
     "code": "prev_in != ' '",
     "line": 2165
    },
    {
     "code": "option_sayas2 == SAYAS_KEY",
     "line": 2179
    },
    {
     "code": "c != ' '",
     "line": 2179
    },
    {
     "code": "prev_in == ' '",
     "line": 2180
    },
    {
     "code": "next_in == ' '",
     "line": 2180
    },
    {
     "code": "c == ']'",
     "line": 2189
    },
    {
     "code": "next_in == ']'",
     "line": 2189
    },
    {
     "code": "(option_sayas2 & 0xf0) == SAYAS_DIGITS",
     "line": 2194
    },
    {
     "code": "count_sayas_digits > (option_sayas2 & 0xf)",
     "line": 2197
    },
    {
     "code": "(option_sayas2 & 0x10) == 0",
     "line": 2210
    },
    {
     "code": "c == 0x92",
     "line": 2213
    },
    {
     "code": "c == 0xb4",
     "line": 2213
    },
    {
     "code": "c == 0x2019",
     "line": 2213
    },
    {
     "code": "c == 0x2032",
     "line": 2213
    },
    {
     "code": "c == 0x2018",
     "line": 2216
    },
    {
     "code": "c == '?'",
     "line": 2216
    },
    {
     "code": "c == CHAR_EMPHASIS",
     "line": 2221
    },
    {
     "code": "c == CHAR_COMMA_BREAK",
     "line": 2227
    },
    {
     "code": "c == 8",
     "line": 2233
    },
    {
     "code": "wcschr(tr->punct_within_word, c) == 0",
     "line": 2240
    },
    {
     "code": "c != '.'",
     "line": 2252
    },
    {
     "code": "c != ','",
     "line": 2252
    },
    {
     "code": "c != ' '",
     "line": 2252
    },
    {
     "code": "prev_in == ','",
     "line": 2257
    },
    {
     "code": "c == ','",
     "line": 2260
    },
    {
     "code": "c == '['",
     "line": 2267
    },
    {
     "code": "next_in == '\\002'",
     "line": 2268
    },
    {
     "code": "next_in == '['",
     "line": 2268
    },
    {
     "code": "c > 0x3040",
     "line": 2278
    },
    {
     "code": "prev_out > 0x3040",
     "line": 2278
    },
    {
     "code": "wcschr(tr->punct_within_word, prev_out) == 0",
     "line": 2279
    },
    {
     "code": "prev_out != ' '",
     "line": 2282
    },
    {
     "code": "wcschr(tr->punct_within_word, prev_out) == 0",
     "line": 2282
    },
    {
     "code": "prev_out == ' '",
     "line": 2293
    },
    {
     "code": "c != ' '",
     "line": 2302
    },
    {
     "code": "tr->letter_bits_offset > 0",
     "line": 2305
    },
    {
     "code": "c < 0x250",
     "line": 2306
    },
    {
     "code": "letter_count > 1",
     "line": 2307
    },
    {
     "code": "prev_out < 0x250",
     "line": 2307
    },
    {
     "code": "syllable_marked == false",
     "line": 2324
    },
    {
     "code": "UpperCaseInWord(tr, &sbuf[ix], c) == 0",
     "line": 2332
    },
    {
     "code": "c != ' '",
     "line": 2337
    },
    {
     "code": "tr->translator_name == L('n', 'l')",
     "line": 2341
    },
    {
     "code": "letter_count == 2",
     "line": 2341
    },
    {
     "code": "c == 'j'",
     "line": 2341
    },
    {
     "code": "prev_in == 'I'",
     "line": 2341
    },
    {
     "code": "letter_count > 2",
     "line": 2353
    },
    {
     "code": "tr->translator_name == L('e', 'n')",
     "line": 2355
    },
    {
     "code": "c == 's'",
     "line": 2355
    },
    {
     "code": "next_in == ' '",
     "line": 2355
    },
    {
     "code": "sbuf[ix-1] == '\\''",
     "line": 2359
    },
    {
     "code": "c == '-'",
     "line": 2366
    },
    {
     "code": "prev_out != ' '",
     "line": 2368
    },
    {
     "code": "word_count > 0",
     "line": 2375
    },
    {
     "code": "prev_in == ' '",
     "line": 2379
    },
    {
     "code": "next_in == ' '",
     "line": 2379
    },
    {
     "code": "next_in == '-'",
     "line": 2383
    },
    {
     "code": "prev_out == ' '",
     "line": 2388
    },
    {
     "code": "c == '.'",
     "line": 2393
    },
    {
     "code": "prev_out == '.'",
     "line": 2394
    },
    {
     "code": "word_count > 0",
     "line": 2398
    },
    {
     "code": "next_in == '-'",
     "line": 2402
    },
    {
     "code": "c == '\\''",
     "line": 2405
    },
    {
     "code": "prev_in == '.'",
     "line": 2406
    },
    {
     "code": "next_in == 's'",
     "line": 2406
    },
    {
     "code": "wcschr(tr->char_plus_apostrophe, prev_in) != 0",
     "line": 2413
    },
    {
     "code": "prev_out2 == ' '",
     "line": 2413
    },
    {
     "code": "next_in == ' '",
     "line": 2416
    },
    {
     "code": "prev_out == 's'",
     "line": 2419
    },
    {
     "code": "single_quoted == false",
     "line": 2419
    },
    {
     "code": "lookupwchar(breaks, c) != 0",
     "line": 2432
    },
    {
     "code": "prev_out != ' '",
     "line": 2436
    },
    {
     "code": "prev_out != tr->langopts.decimal_sep",
     "line": 2437
    },
    {
     "code": "decimal_sep_count == true",
     "line": 2437
    },
    {
     "code": "tr->langopts.decimal_sep == ','",
     "line": 2437
    },
    {
     "code": "prev_out == ' '",
     "line": 2442
    },
    {
     "code": "prev_out == ' '",
     "line": 2451
    },
    {
     "code": "cc == 0x09",
     "line": 2456
    },
    {
     "code": "cc == 0x0a",
     "line": 2456
    },
    {
     "code": "charix[k] != 0",
     "line": 2463
    },
    {
     "code": "charix[k] > 0",
     "line": 2464
    },
    {
     "code": "word_count < N_CLAUSE_WORDS-1",
     "line": 2476
    },
    {
     "code": "ix > words[word_count].start",
     "line": 2476
    },
    {
     "code": "embedded_count > 0",
     "line": 2477
    },
    {
     "code": "alpha_count == 0",
     "line": 2483
    },
    {
     "code": "pre_pause > 0",
     "line": 2489
    },
    {
     "code": "j > words[word_count].start",
     "line": 2491
    },
    {
     "code": "j < charix_top",
     "line": 2502
    },
    {
     "code": "charix[j] != 0",
     "line": 2506
    },
    {
     "code": "charix[j++] != -1",
     "line": 2508
    },
    {
     "code": "ix < (N_TR_SOURCE - 4)",
     "line": 2527
    },
    {
     "code": "pre_pause_add > pre_pause",
     "line": 2530
    },
    {
     "code": "word_count == 0",
     "line": 2535
    },
    {
     "code": "embedded_count > 0",
     "line": 2535
    },
    {
     "code": "word_count > 0",
     "line": 2546
    },
    {
     "code": "ix > 0",
     "line": 2548
    },
    {
     "code": "ix < word_count",
     "line": 2558
    },
    {
     "code": "skip_words > 0",
     "line": 2569
    },
    {
     "code": "skip_words == 0",
     "line": 2571
    },
    {
     "code": "tr->langopts.break_numbers != BREAK_THOUSANDS",
     "line": 2582
    },
    {
     "code": "pn < &number_buf[sizeof(number_buf)-20]",
     "line": 2585
    },
    {
     "code": "*pw == tr->langopts.thousands_sep",
     "line": 2588
    },
    {
     "code": "pw[1] == ' '",
     "line": 2588
    },
    {
     "code": "pw[3] != ' '",
     "line": 2589
    },
    {
     "code": "pw[4] != ' '",
     "line": 2589
    },
    {
     "code": "n_digits > 4",
     "line": 2606
    },
    {
     "code": "n_digits > tr->langopts.max_digits",
     "line": 2613
    },
    {
     "code": "word[0] == '0'",
     "line": 2613
    },
    {
     "code": "pn < &number_buf[sizeof(number_buf)-20]",
     "line": 2616
    },
    {
     "code": "c != tr->langopts.decimal_sep",
     "line": 2617
    },
    {
     "code": "nx > 0",
     "line": 2622
    },
    {
     "code": "tr->langopts.thousands_sep != ' '",
     "line": 2625
    },
    {
     "code": "(words[ix].flags & FLAG_INDIVIDUAL_DIGITS) == 0",
     "line": 2629
    },
    {
     "code": "pw < pn",
     "line": 2653
    },
    {
     "code": "*pw++ != ' '",
     "line": 2656
    },
    {
     "code": "pre_pause > words[ix+1].pre_pause",
     "line": 2665
    },
    {
     "code": "*pw != ' '",
     "line": 2672
    },
    {
     "code": "ix == word_count - 1 - dictionary_skipwords",
     "line": 2681
    },
    {
     "code": "tone_out != NULL",
     "line": 2684
    },
    {
     "code": "dictionary_skipwords > 0",
     "line": 2691
    },
    {
     "code": "embedded_read < embedded_ix",
     "line": 2698
    },
    {
     "code": "ix < 2",
     "line": 2703
    },
    {
     "code": "count_words == 0",
     "line": 2714
    },
    {
     "code": "word_count == 0",
     "line": 2716
    },
    {
     "code": "option_endpause == 0",
     "line": 2716
    },
    {
     "code": "voice_change != NULL",
     "line": 2735
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "memcpy(pn, pw, 16)",
     "name": "memcpy",
     "nargs": 3
    }
   ],
   "line_ids": [
    "pn",
    "pw"
   ],
   "osv_id": "ARVO-42497018",
   "sites": [
    {
     "args": "N_TR_SOURCE+4",
     "callee": "<operator>.alloc",
     "code": "charix[N_TR_SOURCE+4]",
     "line": 2021
    },
    {
     "args": "N_CLAUSE_WORDS",
     "callee": "<operator>.alloc",
     "code": "words[N_CLAUSE_WORDS]",
     "line": 2022
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "voice_change_name[40]",
     "line": 2023
    },
    {
     "args": "N_TR_SOURCE",
     "callee": "<operator>.alloc",
     "code": "sbuf[N_TR_SOURCE]",
     "line": 2026
    },
    {
     "args": "150",
     "callee": "<operator>.alloc",
     "code": "number_buf[150]",
     "line": 2564
    },
    {
     "args": "50",
     "callee": "<operator>.alloc",
     "code": "num_wtab[50]",
     "line": 2565
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "TranslateClause"
  }
 },
 {
  "osv_id": "ARVO-42497441",
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
    "dir": "WRITE",
    "width": 58,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wolfssl/address/41af3da0e3106c85b32429b13790fb34b2e77823/ARVO-42497441/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_41af3da0e310.cpg",
   "testcase_size": 116
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
   "loc_offset": 328,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--DecodeSingleResponse--DecodeResponseData"
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
  "osv_id": "ARVO-42499094",
  "project": "opensc",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "out",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/opensc/src/libopensc/card-piv.c",
    "line": 2390,
    "size": null,
    "type": "u8*"
   }
  },
  "alloc": {
   "size_expr_cpg": "128",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2444,
    "fn": "piv_compute_signature",
    "code": "memcpy(out + nLen*i + nLen - taglen , tag, taglen) | out + nLen*i + nLen - taglen | out + nLen*i + nLen | out + nLen*i",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "piv_compute_signature",
    "file": "/src/opensc/src/libopensc/card-piv.c",
    "line": 2444
   },
   "code": "memcpy(out + nLen*i + nLen - taglen , tag, taglen) | out + nLen*i + nLen - taglen | out + nLen*i + nLen | out + nLen*i",
   "access": {
    "dir": "WRITE",
    "width": 33,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "piv_compute_signature",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i<2 | taglen > nLen",
   "guard_count": 2,
   "control_structures": "DO:2402,IF:2412,IF:2414,GOTO:2419,IF:2424,GOTO:2425,FOR:2429,IF:2430,IF:2432,IF:2436,IF:2437,GOTO:2439"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u8*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "card",
   "out",
   "outlen"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/fc0df4e5d578e5926a59dbf3a34ce737424464ba/ARVO-42499094/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_fc0df4e5d578.cpg",
   "testcase_size": 1690
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
   "loc_offset": 223,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--piv_compute_signature--sc_compute_signature"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 2390,
    "type": "u8*"
   },
   "entity_name_cpg": "out",
   "func_lines": [
    2388,
    2461
   ],
   "func_params": {
    "names": [
     "card",
     "data",
     "datalen",
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
     "code": "priv->alg_id == 0x11",
     "line": 2412
    },
    {
     "code": "priv->alg_id == 0x14",
     "line": 2412
    },
    {
     "code": "outlen < 2*nLen",
     "line": 2414
    },
    {
     "code": "r < 0",
     "line": 2424
    },
    {
     "code": "i<2",
     "line": 2429
    },
    {
     "code": "taglen > nLen",
     "line": 2436
    },
    {
     "code": "*tag != 0x00",
     "line": 2437
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "memcpy(out + nLen*i + nLen - taglen , tag, taglen)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "out + nLen*i + nLen - taglen",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "out + nLen*i + nLen",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "out + nLen*i",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "nLen*i",
     "name": "<operator>.multiplication",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out",
    "nLen",
    "i",
    "taglen",
    "tag"
   ],
   "osv_id": "ARVO-42499094",
   "sites": [
    {
     "args": "128",
     "callee": "<operator>.alloc",
     "code": "rbuf[128]",
     "line": 2396
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "piv_compute_signature"
  }
 },
 {
  "osv_id": "ARVO-42499939",
  "project": "net-snmp",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "id",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/net-snmp/snmplib/parse.c",
    "line": 1866,
    "size": null,
    "type": "subid_s*"
   }
  },
  "alloc": {
   "size_expr_cpg": "MAXTOKEN",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "code": "strdup(token)",
    "fn": "getoid",
    "kind": "strdup",
    "line": 1885,
    "origin": "cpg",
    "args": "token"
   },
   {
    "kind": "free",
    "line": 1919,
    "fn": "getoid",
    "code": "free(id[i].label) | id[i].label | id[i]",
    "origin": "report:crash",
    "args": "id[i].label"
   }
  ],
  "crash": {
   "site": {
    "fn": "getoid",
    "file": "/src/net-snmp/snmplib/parse.c",
    "line": 1919
   },
   "code": "free(id[i].label) | id[i].label | id[i]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "getoid",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < count",
   "guard_count": 1,
   "control_structures": "IF:1870,FOR:1875,IF:1879,IF:1881,IF:1887,IF:1889,IF:1891,GOTO:1895,ELSE:1897,GOTO:1899,ELSE:1901,CONTINUE:1902"
  },
  "call_chain": [],
  "types": {
   "entity_type": "subid_s*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "id_arg",
   "length"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/net-snmp/address/1cb8393797913cad028124eb765560abe196fd43/ARVO-42499939/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_1cb839379791.cpg",
   "testcase_size": 1922
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
   "loc_offset": 552,
   "loc_kind": "stack_frame",
   "dedup_token": "getoid--parse_objectid--parse_asntype"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*id = id_arg",
     "line": 1866
    },
    {
     "code": "id->label = NULL",
     "line": 1876
    },
    {
     "code": "id->modid = current_module",
     "line": 1877
    },
    {
     "code": "id->subid = -1",
     "line": 1878
    },
    {
     "code": "id->label = strdup(token)",
     "line": 1885
    },
    {
     "code": "id->subid = strtoul(token, NULL, 10)",
     "line": 1890
    },
    {
     "code": "id->subid = strtoul(token, NULL, 10)",
     "line": 1908
    },
    {
     "code": "id[i].label = NULL",
     "line": 1920
    }
   ],
   "entity_decl": {
    "line": 1866,
    "type": "subid_s*"
   },
   "entity_name_cpg": "id",
   "func_lines": [
    1863,
    1924
   ],
   "func_params": {
    "names": [
     "fp",
     "id_arg",
     "length"
    ],
    "types": [
     "FILE*",
     "subid_s*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "(type = get_token(fp, token, MAXTOKEN)) != LEFTBRACKET",
     "line": 1870
    },
    {
     "code": "count < length",
     "line": 1875
    },
    {
     "code": "type == RIGHTBRACKET",
     "line": 1879
    },
    {
     "code": "type == LABEL",
     "line": 1881
    },
    {
     "code": "type == LEFTPAREN",
     "line": 1887
    },
    {
     "code": "type == NUMBER",
     "line": 1889
    },
    {
     "code": "(type =",
     "line": 1891
    },
    {
     "code": "type == NUMBER",
     "line": 1904
    },
    {
     "code": "i < count",
     "line": 1918
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "free(id[i].label)",
     "name": "free",
     "nargs": 1
    },
    {
     "code": "id[i].label",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "id[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "id",
    "i"
   ],
   "osv_id": "ARVO-42499939",
   "sites": [
    {
     "args": "MAXTOKEN",
     "callee": "<operator>.alloc",
     "code": "token[MAXTOKEN]",
     "line": 1868
    },
    {
     "args": "token",
     "callee": "strdup",
     "code": "strdup(token)",
     "line": 1885
    },
    {
     "args": "id[i].label",
     "callee": "free",
     "code": "free(id[i].label)",
     "line": 1919
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "getoid",
   "use_fn": "getoid"
  }
 },
 {
  "osv_id": "ARVO-42502055",
  "project": "assimp",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "face",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 376,
    "type": "aiFace&",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 376,
    "fn": "Assimp::ZipArchiveIOSystem::Implement::MapArchive()",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Assimp::ZipArchiveIOSystem::Implement::MapArchive()",
    "file": "/src/assimp/code/Common/ZipArchiveIOSystem.cpp",
    "line": 376
   },
   "code": "&face = meshOut->mFaces[q]",
   "access": {
    "dir": "READ",
    "width": 12288,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Assimp::ZipArchiveIOSystem::Implement::MapArchive()",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/assimp/address/71a87b653cd4b5671104fe49e2e38cf5dd4d8675/ARVO-42502055/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_71a87b653cd4.cpg",
   "testcase_size": 3850
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 288,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--copy--__init"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "&face = meshOut->mFaces[q]",
     "line": 376
    },
    {
     "code": "face.mIndices = new unsigned int[3]",
     "line": 378
    },
    {
     "code": "face.mNumIndices = 3",
     "line": 379
    },
    {
     "code": "face.mIndices[a] = base",
     "line": 389
    }
   ],
   "entity_decl": {
    "line": 376,
    "type": "aiFace&"
   },
   "entity_name_cpg": "face",
   "func_lines": [
    327,
    406
   ],
   "func_params": {
    "names": [
     "this",
     "pcOut"
    ],
    "types": [
     "Assimp.Discreet3DSImporter",
     "aiScene*"
    ]
   },
   "guards": [
    {
     "code": "i != mScene->mMeshes.end()",
     "line": 335
    },
    {
     "code": "a != (*i).mFaceMaterials.end()",
     "line": 342
    },
    {
     "code": "p < mScene->mMaterials.size()",
     "line": 346
    },
    {
     "code": "q < aiSplit[p].size()",
     "line": 374
    },
    {
     "code": "a < 3",
     "line": 381
    },
    {
     "code": "a < pcOut->mNumMeshes",
     "line": 398
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "&face = meshOut->mFaces[q]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "meshOut->mFaces[q]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "meshOut->mFaces",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "face",
    "meshOut",
    "q"
   ],
   "osv_id": "ARVO-42502055",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Assimp::ZipArchiveIOSystem::Implement::MapArchive()"
  }
 },
 {
  "osv_id": "ARVO-42504982",
  "project": "espeak-ng",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 694,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 714,
    "fn": "IsLetterGroup",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "IsLetterGroup",
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "line": 714
   },
   "code": "(*p == *w) && (*w != 0)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "IsLetterGroup",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/espeak-ng/address/0a713d52bbf3e061823d1a7f35e5303e7320f27a/ARVO-42504982/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0a713d52bbf3.cpg",
   "testcase_size": 6625
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 5629,
   "loc_kind": "stack_frame",
   "dedup_token": "IsLetterGroup--MatchRule--TranslateRules"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "p = tr->letterGroups[group]",
     "line": 698
    }
   ],
   "entity_decl": {
    "line": 694,
    "type": "char*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    672,
    730
   ],
   "func_params": {
    "names": [
     "tr",
     "word",
     "group",
     "pre"
    ],
    "types": [
     "Translator*",
     "char*",
     "int",
     "int"
    ]
   },
   "guards": [
    {
     "code": "p == NULL",
     "line": 699
    },
    {
     "code": "*p != RULE_GROUP_END",
     "line": 702
    },
    {
     "code": "*p == '~'",
     "line": 710
    },
    {
     "code": "*p == *w",
     "line": 714
    },
    {
     "code": "*w != 0",
     "line": 714
    },
    {
     "code": "*p == 0",
     "line": 718
    },
    {
     "code": "*p++ != 0",
     "line": 725
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "(*p == *w) && (*w != 0)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "*p == *w",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*p",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*w",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*w != 0",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "*w",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "p",
    "w"
   ],
   "osv_id": "ARVO-42504982",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "IsLetterGroup"
  }
 },
 {
  "osv_id": "ARVO-42507578",
  "project": "leptonica",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "tab",
   "kind": "pointer",
   "storage": "stack",
   "decl": {
    "file": "/src/leptonica/src/pix3.c",
    "line": 1944,
    "size": null,
    "type": "l_int32*"
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1970,
    "fn": "pixCountPixels",
    "code": "tab[(word >> 16) & 0xff] | (word >> 16) & 0xff | word >> 16",
    "origin": "report:crash"
   },
   {
    "code": "free(tab)",
    "fn": "pixCountPixels",
    "kind": "free",
    "line": 1986,
    "origin": "cpg",
    "args": "tab"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixCountPixels",
    "file": "/src/leptonica/src/pix3.c",
    "line": 1970
   },
   "code": "tab[(word >> 16) & 0xff] | (word >> 16) & 0xff | word >> 16",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "pixCountPixels",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1949,IF:1952,FOR:1964,FOR:1965,IF:1967,IF:1974,IF:1976,IF:1986"
  },
  "call_chain": [],
  "types": {
   "entity_type": "l_int32*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "pixs",
   "tab8"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/leptonica/address/9562d40781afffb0ae041681346ab5443e36528f/ARVO-42507578/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_9562d40781af.cpg",
   "testcase_size": 8220
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_offset": 276,
   "loc_kind": "stack_frame",
   "dedup_token": "pixCountPixels--pixCountPixelsInRect--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "tab = (tab8) ? tab8 : makePixelSumTab8()",
     "line": 1955
    }
   ],
   "entity_decl": {
    "line": 1944,
    "type": "l_int32*"
   },
   "entity_name_cpg": "tab",
   "func_lines": [
    1936,
    1988
   ],
   "func_params": {
    "names": [
     "pixs",
     "pcount",
     "tab8"
    ],
    "types": [
     "PIX*",
     "l_int32*",
     "l_int32*"
    ]
   },
   "guards": [
    {
     "code": "pixGetDepth(pixs) != 1",
     "line": 1952
    },
    {
     "code": "endbits == 0",
     "line": 1961
    },
    {
     "code": "i < h",
     "line": 1964
    },
    {
     "code": "j < fullwords",
     "line": 1965
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "tab[(word >> 16) & 0xff]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "(word >> 16) & 0xff",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "word >> 16",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    }
   ],
   "line_ids": [
    "tab",
    "word"
   ],
   "osv_id": "ARVO-42507578",
   "sites": [
    {
     "args": "tab",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(tab)",
     "line": 1986
    },
    {
     "args": "tab",
     "callee": "free",
     "code": "free(tab)",
     "line": 1986
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "pixCountPixels",
   "use_fn": "pixCountPixels"
  }
 },
 {
  "osv_id": "ARVO-42508338",
  "project": "espeak-ng",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "stderr",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": {
   "size_expr_cpg": "40",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 917,
    "fn": "LoadVoice",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "LoadVoice",
    "file": "/src/espeak-ng/src/libespeak-ng/voices.c",
    "line": 917
   },
   "code": "fprintf(stderr, \"Unknown phoneme table: '%s'\\n\", phonemes_name)",
   "access": {
    "dir": "READ",
    "width": 42,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "LoadVoice",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/espeak-ng/address/ac643ea5add300e036afbcc0d48e28d94edad5a9/ARVO-42508338/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_ac643ea5add3.cpg",
   "testcase_size": 405
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
   "loc_offset": 408,
   "loc_kind": "stack_frame",
   "dedup_token": "printf_common(void*, char const*, __va_list_tag*)--__interceptor_vfprintf--fprintf"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "stderr",
   "func_lines": [
    491,
    940
   ],
   "func_params": {
    "names": [
     "vname",
     "control"
    ],
    "types": [
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "voicename[0] == 0",
     "line": 540
    },
    {
     "code": "f_voice == NULL",
     "line": 559
    },
    {
     "code": "translator != NULL",
     "line": 567
    },
    {
     "code": "(p = strchr(voice_identifier, '+')) != NULL",
     "line": 586
    },
    {
     "code": "f_voice != NULL",
     "line": 593
    },
    {
     "code": "fgets_strip(buf, sizeof(buf), f_voice) != NULL",
     "line": 593
    },
    {
     "code": "*p != 0",
     "line": 595
    },
    {
     "code": "buf[0] == 0",
     "line": 598
    },
    {
     "code": "strcmp(language_name, \"variant\") == 0",
     "line": 616
    },
    {
     "code": "len < (sizeof(voice_languages)-langix-1)",
     "line": 621
    },
    {
     "code": "language_set == false",
     "line": 629
    },
    {
     "code": "tone_only == 0",
     "line": 643
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 667
    },
    {
     "code": "sscanf(p, \"%d %d\", &pitch1, &pitch2) == 2",
     "line": 676
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 684
    },
    {
     "code": "ix < stress_lengths_set",
     "line": 691
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 698
    },
    {
     "code": "ix < stress_amps_set",
     "line": 704
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 711
    },
    {
     "code": "ix < stress_add_set",
     "line": 717
    },
    {
     "code": "(option_tone_flags & 0xff) != 0",
     "line": 725
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 726
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 733
    },
    {
     "code": "ix < n",
     "line": 739
    },
    {
     "code": "strcmp(names[ix], \"NULL\") == 0",
     "line": 740
    },
    {
     "code": "(value = LookupTune(names[ix])) < 0",
     "line": 743
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 752
    },
    {
     "code": "*p != 0",
     "line": 756
    },
    {
     "code": "(n = atoi(p)) > 0",
     "line": 758
    },
    {
     "code": "n < 32",
     "line": 760
    },
    {
     "code": "key == V_DICTRULES",
     "line": 761
    },
    {
     "code": "key == V_NUMBERS",
     "line": 763
    },
    {
     "code": "key == V_STRESSOPT",
     "line": 765
    },
    {
     "code": "key == V_NUMBERS",
     "line": 768
    },
    {
     "code": "n < 64",
     "line": 768
    },
    {
     "code": "phonemes_set == false",
     "line": 780
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 788
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 794
    },
    {
     "code": "sscanf(p, \"%d\", &value) == 1",
     "line": 810
    },
    {
     "code": "sscanf(p, \"%d\", &value) == 1",
     "line": 814
    },
    {
     "code": "sscanf(p, \"%d\", &value) == 1",
     "line": 818
    },
    {
     "code": "value > 4",
     "line": 819
    },
    {
     "code": "sscanf(p, \"%d\", &value) == 1",
     "line": 834
    },
    {
     "code": "ix < 8",
     "line": 839
    },
    {
     "code": "status != ENS_OK",
     "line": 861
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 877
    },
    {
     "code": "sscanf(p, \"%d\", &value) == 1",
     "line": 880
    },
    {
     "code": "(key & 0xff00) == 0x100",
     "line": 890
    },
    {
     "code": "CheckTranslator(translator, keyword_tab, key) != 0",
     "line": 891
    },
    {
     "code": "f_voice != NULL",
     "line": 899
    },
    {
     "code": "translator == NULL",
     "line": 902
    },
    {
     "code": "(ix = SelectPhonemeTableName(phonemes_name)) < 0",
     "line": 916
    },
    {
     "code": "dictionary_name[0] == 0",
     "line": 926
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "fprintf(stderr, \"Unknown phoneme table: '%s'\\n\", phonemes_name)",
     "name": "fprintf",
     "nargs": 3
    }
   ],
   "line_ids": [
    "stderr",
    "phonemes_name"
   ],
   "osv_id": "ARVO-42508338",
   "sites": [
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "voicename[40]",
     "line": 513
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "language_name[40]",
     "line": 514
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "translator_name[40]",
     "line": 515
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "new_dictionary[40]",
     "line": 516
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "phonemes_name[40]",
     "line": 517
    },
    {
     "args": "sizeof(path_home)+30",
     "callee": "<operator>.alloc",
     "code": "buf[sizeof(path_home)+30]",
     "line": 519
    },
    {
     "args": "sizeof(path_home)+12",
     "callee": "<operator>.alloc",
     "code": "path_voices[sizeof(path_home)+12]",
     "line": 520
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "stress_add[8]",
     "line": 522
    },
    {
     "args": "8 ;; 40",
     "callee": "<operator>.alloc",
     "code": "names[8][40]",
     "line": 523
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "name1[40]",
     "line": 524
    },
    {
     "args": "80",
     "callee": "<operator>.alloc",
     "code": "name2[80]",
     "line": 525
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "voice_identifier[40]",
     "line": 530
    },
    {
     "args": "40",
     "callee": "<operator>.alloc",
     "code": "voice_name[40]",
     "line": 531
    },
    {
     "args": "100",
     "callee": "<operator>.alloc",
     "code": "voice_languages[100]",
     "line": 532
    },
    {
     "args": "80",
     "callee": "<operator>.alloc",
     "code": "vgender[80]",
     "line": 651
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "stress_lengths[8]",
     "line": 688
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "stress_amps[8]",
     "line": 702
    },
    {
     "args": "12",
     "callee": "<operator>.alloc",
     "code": "tone_data[12]",
     "line": 828
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "LoadVoice"
  }
 },
 {
  "osv_id": "ARVO-42509095",
  "project": "fluent-bit",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "sbuf",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 62,
    "type": "msgpack_sbuffer*",
    "size": null
   }
  },
  "alloc": {
   "size_expr_cpg": "sbuf->data ;; nsize",
   "size_expr_cpg_callee": "realloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 88,
    "fn": "msgpack_sbuffer_write",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "msgpack_sbuffer_write",
    "file": "/src/fluent-bit/lib/msgpack-c/include/msgpack/sbuffer.h",
    "line": 88
   },
   "code": "memcpy(sbuf->data + sbuf->size, buf, len)",
   "access": {
    "dir": "READ",
    "width": 37,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "msgpack_sbuffer_write",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/fluent-bit/address/a5661fee34a6f730033fcff32155f254c8d61262/ARVO-42509095/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_a5661fee34a6.cpg",
   "testcase_size": 9
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 96,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memcpy--msgpack_sbuffer_write--msgpack_pack_str_body"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* sbuf = (msgpack_sbuffer*)data",
     "line": 62
    },
    {
     "code": "sbuf->data = (char*)tmp",
     "line": 84
    },
    {
     "code": "sbuf->alloc = nsize",
     "line": 85
    }
   ],
   "entity_decl": {
    "line": 62,
    "type": "msgpack_sbuffer*"
   },
   "entity_name_cpg": "sbuf",
   "func_lines": [
    60,
    92
   ],
   "func_params": {
    "names": [
     "data",
     "buf",
     "len"
    ],
    "types": [
     "void*",
     "char*",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "len == 0",
     "line": 64
    },
    {
     "code": "sbuf->alloc - sbuf->size < len",
     "line": 67
    },
    {
     "code": "nsize < sbuf->size + len",
     "line": 72
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(sbuf->data + sbuf->size, buf, len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "sbuf->data + sbuf->size",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "sbuf->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "sbuf->size",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "sbuf",
    "buf",
    "len"
   ],
   "osv_id": "ARVO-42509095",
   "sites": [
    {
     "args": "sbuf->data ;; nsize",
     "callee": "realloc",
     "code": "realloc(sbuf->data, nsize)",
     "line": 81
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "msgpack_sbuffer_write"
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