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
  "osv_id": "ARVO-42491698",
  "project": "matio",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "data_type",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 385,
    "type": "matio_types",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "Mat_H5ReadDatasetInfo",
    "file": "/src/matio/src/mat73.c",
    "line": 673
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "matvar->nbytes",
   "size_expr_cpg_callee": "ComplexMalloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 674,
    "fn": "Mat_H5ReadDatasetInfo",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_H5ReadDatasetInfo",
    "file": "/src/matio/src/mat73.c",
    "line": 674
   },
   "code": "sparse->ndata",
   "access": {
    "dir": "WRITE",
    "width": 400,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_H5ReadDatasetInfo",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/92e9a90b02cb3af869d86de1a1428b4bd9e6e7a5/ARVO-42491698/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_92e9a90b02cb.cpg",
   "testcase_size": 27460
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
   "dedup_token": "__asan_memcpy--H5MM_memcpy--H5D__scatter_mem"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "data_type = MAT_T_DOUBLE",
     "line": 385
    },
    {
     "code": "data_type = matvar->data_type",
     "line": 524
    }
   ],
   "entity_decl": {
    "line": 385,
    "type": "matio_types"
   },
   "entity_name_cpg": "data_type",
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
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "sparse->ndata",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "data_type",
    "sparse"
   ],
   "osv_id": "ARVO-42491698",
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
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_H5ReadDatasetInfo"
  }
 },
 {
  "osv_id": "ARVO-42491774",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 2404,
    "fn": "blosc_getitem",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "blosc_getitem",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 2404
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "blosc_getitem",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/474ebf151be847186e6bc2c1381a8f7d4beff4dd/ARVO-42491774/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_474ebf151be8.cpg",
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
   "alloc",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "blosc_getitem--get_coffset--frame_get_lazychunk"
  },
  "deep": {
   "osv_id": "ARVO-42491774"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "blosc_getitem"
  }
 },
 {
  "osv_id": "ARVO-42491954",
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
    "file": "/src/hdf5-1.12.0/src/H5MM.c",
    "line": 292
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
    "line": 583,
    "fn": "Mat_Open",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_Open",
    "file": "/src/matio/src/mat.c",
    "line": 583
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/1ce8f2d1845ecdde19a35605cabdbb884776d52d/ARVO-42491954/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_1ce8f2d1845e.cpg",
   "testcase_size": 5609
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
   "dedup_token": "H5F_addr_decode_len--H5F_addr_decode--H5G_ent_decode"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    433,
    615
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
     "line": 441
    },
    {
     "code": "(mode & 0x01) == MAT_ACC_RDWR",
     "line": 453
    },
    {
     "code": "NULL == mat",
     "line": 473
    },
    {
     "code": "NULL == mat->header",
     "line": 481
    },
    {
     "code": "NULL == mat->subsys_offset",
     "line": 488
    },
    {
     "code": "128 == bytesread",
     "line": 510
    },
    {
     "code": "tmp == 0x4d49",
     "line": 513
    },
    {
     "code": "tmp == 0x494d",
     "line": 515
    },
    {
     "code": "mat->version == 0x0100",
     "line": 521
    },
    {
     "code": "mat->version == 0x0200",
     "line": 521
    },
    {
     "code": "-1 != mat->byteswap",
     "line": 522
    },
    {
     "code": "mat->bof == -1L",
     "line": 524
    },
    {
     "code": "0 == mat->version",
     "line": 538
    },
    {
     "code": "NULL == var",
     "line": 559
    },
    {
     "code": "bytesread != 0",
     "line": 560
    },
    {
     "code": "NULL == mat",
     "line": 571
    },
    {
     "code": "mat->version == 0x0200",
     "line": 577
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42491954",
   "sites": [
    {
     "args": "sizeof(*mat)",
     "callee": "malloc",
     "code": "malloc(sizeof(*mat))",
     "line": 472
    },
    {
     "args": "128 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(128,sizeof(char))",
     "line": 480
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 482
    },
    {
     "args": "8 ;; sizeof(char)",
     "callee": "calloc",
     "code": "calloc(8,sizeof(char))",
     "line": 487
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 489
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 490
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 525
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 526
    },
    {
     "args": "mat",
     "callee": "free",
     "code": "free(mat)",
     "line": 527
    },
    {
     "args": "mat->header",
     "callee": "free",
     "code": "free(mat->header)",
     "line": 542
    },
    {
     "args": "mat->subsys_offset",
     "callee": "free",
     "code": "free(mat->subsys_offset)",
     "line": 543
    },
    {
     "args": "var",
     "callee": "Mat_VarFree",
     "code": "Mat_VarFree(var)",
     "line": 566
    },
    {
     "args": "matname",
     "callee": "strdup",
     "code": "strdup(matname)",
     "line": 574
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
  "osv_id": "ARVO-42491972",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "N",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "line": 931,
    "size": null,
    "type": "unsigned int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "cram_read_block",
    "file": "/src/htslib/cram/cram_io.c",
    "line": 1445
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 931,
    "fn": "arith_uncompress_to",
    "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
    "origin": "report:crash"
   },
   {
    "code": "malloc(ulen)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 936,
    "origin": "cpg",
    "args": "ulen"
   },
   {
    "code": "malloc(ulen)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 969,
    "origin": "cpg",
    "args": "ulen"
   },
   {
    "code": "free(outN)",
    "fn": "arith_uncompress_to",
    "kind": "free",
    "line": 978,
    "origin": "cpg",
    "args": "outN"
   },
   {
    "code": "free(outN)",
    "fn": "arith_uncompress_to",
    "kind": "free",
    "line": 984,
    "origin": "cpg",
    "args": "outN"
   },
   {
    "code": "free(outN)",
    "fn": "arith_uncompress_to",
    "kind": "free",
    "line": 992,
    "origin": "cpg",
    "args": "outN"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 1028,
    "origin": "cpg",
    "args": "*out_size"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 1051,
    "origin": "cpg",
    "args": "*out_size"
   }
  ],
  "crash": {
   "site": {
    "fn": "arith_uncompress_to",
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "line": 931
   },
   "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "arith_uncompress_to",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < N | c_meta_len > in_size | i < N",
   "guard_count": 4,
   "control_structures": "IF:921,IF:924,IF:933,IF:934,IF:936,IF:941,FOR:946,IF:951,IF:960,IF:970,FOR:974,IF:976"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "in",
   "in_size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42491972/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 138
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
  "free_related": {
   "free_sites_in_func": [
    978,
    984,
    992
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "arith_uncompress_to--cram_uncompress_block--cram_read_SAM_hdr"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "N = in[c_meta_len++]",
     "line": 931
    }
   ],
   "entity_decl": {
    "line": 931,
    "type": "unsigned int"
   },
   "entity_name_cpg": "N",
   "func_lines": [
    915,
    1157
   ],
   "func_params": {
    "names": [
     "in",
     "in_size",
     "out",
     "out_size"
    ],
    "types": [
     "unsigned char*",
     "unsigned int",
     "unsigned char*",
     "unsigned int*"
    ]
   },
   "guards": [
    {
     "code": "in_size == 0",
     "line": 921
    },
    {
     "code": "ulen != *out_size",
     "line": 941
    },
    {
     "code": "i < N",
     "line": 946
    },
    {
     "code": "(ulen % N) > i",
     "line": 947
    },
    {
     "code": "c_meta_len > in_size",
     "line": 951
    },
    {
     "code": "clenN[i] > in_size",
     "line": 951
    },
    {
     "code": "clenN[i] < 1",
     "line": 951
    },
    {
     "code": "c_meta_len + clen_tot > in_size",
     "line": 960
    },
    {
     "code": "i < N",
     "line": 974
    },
    {
     "code": "in_size < c_meta_len",
     "line": 976
    },
    {
     "code": "olen != ulenN[i]",
     "line": 982
    },
    {
     "code": "*out_size < osz",
     "line": 1031
    },
    {
     "code": "c_meta_size == 0",
     "line": 1069
    },
    {
     "code": "osz > tmp1_size",
     "line": 1082
    },
    {
     "code": "tmp1_size > in_size",
     "line": 1098
    },
    {
     "code": "tmp1_size > *out_size",
     "line": 1100
    },
    {
     "code": "order == 1",
     "line": 1115
    },
    {
     "code": "order == 1",
     "line": 1122
    },
    {
     "code": "npacked_sym == 1",
     "line": 1136
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "N = in[c_meta_len++]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "in[c_meta_len++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "c_meta_len++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "N",
    "in",
    "c_meta_len"
   ],
   "osv_id": "ARVO-42491972",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "clenN[256]",
     "line": 932
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "ulenN[256]",
     "line": 932
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "idxN[256]",
     "line": 932
    },
    {
     "args": "ulen",
     "callee": "malloc",
     "code": "malloc(ulen)",
     "line": 936
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 942
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 952
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 961
    },
    {
     "args": "ulen",
     "callee": "malloc",
     "code": "malloc(ulen)",
     "line": 969
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 971
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 977
    },
    {
     "args": "outN",
     "callee": "free",
     "code": "free(outN)",
     "line": 978
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 983
    },
    {
     "args": "outN",
     "callee": "free",
     "code": "free(outN)",
     "line": 984
    },
    {
     "args": "outN",
     "callee": "free",
     "code": "free(outN)",
     "line": 992
    },
    {
     "args": "*out_size",
     "callee": "malloc",
     "code": "malloc(*out_size)",
     "line": 1028
    },
    {
     "args": "*out_size",
     "callee": "malloc",
     "code": "malloc(*out_size)",
     "line": 1051
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "map[16] = {0}",
     "line": 1064
    },
    {
     "args": "tmp",
     "callee": "free",
     "code": "free(tmp)",
     "line": 1148
    },
    {
     "args": "tmp_free",
     "callee": "free",
     "code": "free(tmp_free)",
     "line": 1154
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1155
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "arith_uncompress_to",
   "use_fn": "arith_uncompress_to"
  }
 },
 {
  "osv_id": "ARVO-42491975",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "N",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/rANS_static4x16pr.c",
    "line": 1536,
    "size": null,
    "type": "unsigned int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "cram_read_block",
    "file": "/src/htslib/cram/cram_io.c",
    "line": 1445
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1536,
    "fn": "rans_uncompress_to_4x16",
    "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
    "origin": "report:crash"
   },
   {
    "code": "malloc(ulen)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1541,
    "origin": "cpg",
    "args": "ulen"
   },
   {
    "code": "malloc(ulen)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1574,
    "origin": "cpg",
    "args": "ulen"
   },
   {
    "code": "free(outN)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "free",
    "line": 1583,
    "origin": "cpg",
    "args": "outN"
   },
   {
    "code": "free(outN)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "free",
    "line": 1589,
    "origin": "cpg",
    "args": "outN"
   },
   {
    "code": "free(outN)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "free",
    "line": 1597,
    "origin": "cpg",
    "args": "outN"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1628,
    "origin": "cpg",
    "args": "*out_size"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1666,
    "origin": "cpg",
    "args": "*out_size"
   }
  ],
  "crash": {
   "site": {
    "fn": "rans_uncompress_to_4x16",
    "file": "/src/htslib/htscodecs/htscodecs/rANS_static4x16pr.c",
    "line": 1536
   },
   "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rans_uncompress_to_4x16",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < N | c_meta_len > in_size | i < N",
   "guard_count": 4,
   "control_structures": "IF:1526,IF:1529,IF:1538,IF:1539,IF:1541,IF:1546,FOR:1551,IF:1556,IF:1565,IF:1575,FOR:1579,IF:1581"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "in",
   "in_size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42491975/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 207
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
  "free_related": {
   "free_sites_in_func": [
    1583,
    1589,
    1597
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "rans_uncompress_to_4x16--rans_uncompress_4x16--cram_uncompress_block"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "N = in[c_meta_len++]",
     "line": 1536
    }
   ],
   "entity_decl": {
    "line": 1536,
    "type": "unsigned int"
   },
   "entity_name_cpg": "N",
   "func_lines": [
    1521,
    1801
   ],
   "func_params": {
    "names": [
     "in",
     "in_size",
     "out",
     "out_size"
    ],
    "types": [
     "unsigned char*",
     "unsigned int",
     "unsigned char*",
     "unsigned int*"
    ]
   },
   "guards": [
    {
     "code": "in_size == 0",
     "line": 1526
    },
    {
     "code": "ulen != *out_size",
     "line": 1546
    },
    {
     "code": "i < N",
     "line": 1551
    },
    {
     "code": "(ulen % N) > i",
     "line": 1552
    },
    {
     "code": "c_meta_len > in_size",
     "line": 1556
    },
    {
     "code": "clenN[i] > in_size",
     "line": 1556
    },
    {
     "code": "clenN[i] < 1",
     "line": 1556
    },
    {
     "code": "c_meta_len + clen_tot > in_size",
     "line": 1565
    },
    {
     "code": "i < N",
     "line": 1579
    },
    {
     "code": "in_size < c_meta_len",
     "line": 1581
    },
    {
     "code": "olen != ulenN[i]",
     "line": 1587
    },
    {
     "code": "*out_size < osz",
     "line": 1631
    },
    {
     "code": "c_meta_size == 0",
     "line": 1696
    },
    {
     "code": "osz > tmp1_size",
     "line": 1709
    },
    {
     "code": "rle_len > tmp1_size",
     "line": 1721
    },
    {
     "code": "u_meta_size/2 > (in_end-meta)",
     "line": 1725
    },
    {
     "code": "c_meta_size+sz > in_size",
     "line": 1734
    },
    {
     "code": "tmp1_size > in_size",
     "line": 1747
    },
    {
     "code": "tmp1_size > *out_size",
     "line": 1749
    },
    {
     "code": "u_meta_size < 1+rle_nsyms",
     "line": 1769
    },
    {
     "code": "npacked_sym == 1",
     "line": 1781
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "N = in[c_meta_len++]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "in[c_meta_len++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "c_meta_len++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "N",
    "in",
    "c_meta_len"
   ],
   "osv_id": "ARVO-42491975",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "clenN[256]",
     "line": 1537
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "ulenN[256]",
     "line": 1537
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "idxN[256]",
     "line": 1537
    },
    {
     "args": "ulen",
     "callee": "malloc",
     "code": "malloc(ulen)",
     "line": 1541
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1547
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1557
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1566
    },
    {
     "args": "ulen",
     "callee": "malloc",
     "code": "malloc(ulen)",
     "line": 1574
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1576
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1582
    },
    {
     "args": "outN",
     "callee": "free",
     "code": "free(outN)",
     "line": 1583
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1588
    },
    {
     "args": "outN",
     "callee": "free",
     "code": "free(outN)",
     "line": 1589
    },
    {
     "args": "outN",
     "callee": "free",
     "code": "free(outN)",
     "line": 1597
    },
    {
     "args": "*out_size",
     "callee": "malloc",
     "code": "malloc(*out_size)",
     "line": 1628
    },
    {
     "args": "*out_size",
     "callee": "malloc",
     "code": "malloc(*out_size)",
     "line": 1666
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "map[16] = {0}",
     "line": 1691
    },
    {
     "args": "meta_free",
     "callee": "free",
     "code": "free(meta_free)",
     "line": 1776
    },
    {
     "args": "tmp",
     "callee": "free",
     "code": "free(tmp)",
     "line": 1791
    },
    {
     "args": "meta_free",
     "callee": "free",
     "code": "free(meta_free)",
     "line": 1797
    },
    {
     "args": "out_free",
     "callee": "free",
     "code": "free(out_free)",
     "line": 1798
    },
    {
     "args": "tmp_free",
     "callee": "free",
     "code": "free(tmp_free)",
     "line": 1799
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "rans_uncompress_to_4x16",
   "use_fn": "rans_uncompress_to_4x16"
  }
 },
 {
  "osv_id": "ARVO-42491999",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
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
    "region_bytes": null
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/aebf2b9858368681e497f136501ab33cc1014aed/ARVO-42491999/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_aebf2b985836.cpg",
   "testcase_size": 89
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "sw32_--blosc_d--_blosc_getitem"
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
    59
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
   "osv_id": "ARVO-42491999",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sw32_"
  }
 },
 {
  "osv_id": "ARVO-42492002",
  "project": "leptonica",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dptr",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/fmorphgenlow.1.c",
    "line": 5757,
    "size": null,
    "type": "l_uint32*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "pixdata_malloc",
    "file": "/src/leptonica/src/pix1.c",
    "line": 247
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 5767,
    "fn": "fdilate_1_56",
    "code": "*dptr = ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) < | *dptr | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) | | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) |",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "fdilate_1_56",
    "file": "/src/leptonica/src/fmorphgenlow.1.c",
    "line": 5767
   },
   "code": "*dptr = ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) < | *dptr | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) | | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) |",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "fdilate_1_56",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:5763,FOR:5766"
  },
  "call_chain": [],
  "types": {
   "entity_type": "l_uint32*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "datad",
   "h",
   "wpld",
   "datas",
   "wpls"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/0665ff28f9e9df91565ee09438a30d47232ad2eb/ARVO-42492002/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_0665ff28f9e9.cpg",
   "testcase_size": 540
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
   "dedup_token": "fdilate_1_56--fmorphopgen_low_1--pixFMorphopGen_1"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "dptr = datad + i * wpld",
     "line": 5765
    }
   ],
   "entity_decl": {
    "line": 5757,
    "type": "l_uint32*"
   },
   "entity_name_cpg": "dptr",
   "func_lines": [
    5747,
    5774
   ],
   "func_params": {
    "names": [
     "datad",
     "w",
     "h",
     "wpld",
     "datas",
     "wpls"
    ],
    "types": [
     "l_uint32*",
     "l_int32",
     "l_int32",
     "l_int32",
     "l_uint32*",
     "l_int32"
    ]
   },
   "guards": [
    {
     "code": "i < h",
     "line": 5763
    },
    {
     "code": "j < pwpls",
     "line": 5766
    }
   ],
   "line_call_count": 14,
   "line_calls": [
    {
     "code": "*dptr = ((*(sptr + wpls2) >> 2) ",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "*dptr",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "((*(sptr + wpls2) >> 2) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "((*(sptr + wpls2) >> 2) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "((*(sptr + wpls2) >> 2) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "((*(sptr + wpls2) >> 2) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "(*(sptr + wpls2) >> 2) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "*(sptr + wpls2) >> 2",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "*(sptr + wpls2)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "sptr + wpls2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "*(sptr + wpls2 - 1) << 30",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "*(sptr + wpls2 - 1)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "sptr + wpls2 - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "sptr + wpls2",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dptr",
    "sptr",
    "wpls2"
   ],
   "osv_id": "ARVO-42492002",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "fdilate_1_56"
  }
 },
 {
  "osv_id": "ARVO-42492011",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/cram/cram_codecs.c",
    "line": 1387,
    "size": null,
    "type": "cram_codec*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "cram_xpack_decode_init",
    "file": "/src/htslib/cram/cram_codecs.c",
    "line": 1391
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "sizeof(*c)",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "code": "malloc(sizeof(*c))",
    "fn": "cram_xpack_decode_init",
    "kind": "malloc",
    "line": 1391,
    "origin": "cpg",
    "args": "sizeof(*c)"
   },
   {
    "kind": "unknown",
    "line": 1415,
    "fn": "cram_xpack_decode_init",
    "code": "c->u.xpack.rmap[i] = v | c->u.xpack.rmap[i] | c->u.xpack.rmap | c->u.xpack",
    "origin": "report:crash"
   },
   {
    "code": "free(c)",
    "fn": "cram_xpack_decode_init",
    "kind": "free",
    "line": 1432,
    "origin": "cpg",
    "args": "c"
   }
  ],
  "crash": {
   "site": {
    "fn": "cram_xpack_decode_init",
    "file": "/src/htslib/cram/cram_codecs.c",
    "line": 1415
   },
   "code": "c->u.xpack.rmap[i] = v | c->u.xpack.rmap[i] | c->u.xpack.rmap | c->u.xpack",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cram_xpack_decode_init",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < c->u.xpack.nval | v >= 256",
   "guard_count": 2,
   "control_structures": "IF:1391,IF:1395,ELSE:1397,IF:1397,ELSE:1399,IF:1399,ELSE:1401,FOR:1412,IF:1414,IF:1420,GOTO:1421,IF:1424"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cram_codec*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "data",
   "size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492011/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 91
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
   "dedup_token": "cram_xpack_decode_init--cram_decoder_init--cram_decode_compression_header"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = malloc(sizeof(*c))",
     "line": 1391
    },
    {
     "code": "c->codec  = E_XPACK",
     "line": 1394
    },
    {
     "code": "c->decode = cram_xpack_decode_long",
     "line": 1396
    },
    {
     "code": "c->decode = cram_xpack_decode_int",
     "line": 1398
    },
    {
     "code": "c->decode = cram_xpack_decode_char",
     "line": 1400
    },
    {
     "code": "c->free = cram_xpack_decode_free",
     "line": 1405
    },
    {
     "code": "c->size = cram_xpack_decode_size",
     "line": 1406
    },
    {
     "code": "c->get_block = cram_xpack_get_block",
     "line": 1407
    },
    {
     "code": "c->u.xpack.nbits = vv->varint_get32(&cp, endp, NULL)",
     "line": 1409
    },
    {
     "code": "c->u.xpack.nval  = vv->varint_get32(&cp, endp, NULL)",
     "line": 1410
    },
    {
     "code": "c->u.xpack.rmap[i] = v",
     "line": 1415
    },
    {
     "code": "c->u.xpack.sub_codec = cram_decoder_init(hdr, encoding, cp, sub_size,",
     "line": 1422
    }
   ],
   "entity_decl": {
    "line": 1387,
    "type": "cram_codec*"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    1382,
    1437
   ],
   "func_params": {
    "names": [
     "hdr",
     "data",
     "size",
     "codec",
     "option",
     "version",
     "vv"
    ],
    "types": [
     "cram_block_compression_hdr*",
     "char*",
     "int",
     "cram_encoding",
     "cram_external_type",
     "int",
     "varint_vec*"
    ]
   },
   "guards": [
    {
     "code": "option == E_LONG",
     "line": 1395
    },
    {
     "code": "option == E_INT",
     "line": 1397
    },
    {
     "code": "option == E_BYTE_ARRAY",
     "line": 1399
    },
    {
     "code": "option == E_BYTE",
     "line": 1399
    },
    {
     "code": "i < c->u.xpack.nval",
     "line": 1412
    },
    {
     "code": "sub_size < 0",
     "line": 1420
    },
    {
     "code": "endp - cp < sub_size",
     "line": 1420
    },
    {
     "code": "c->u.xpack.sub_codec == NULL",
     "line": 1424
    },
    {
     "code": "cp - data != size",
     "line": 1428
    },
    {
     "code": "c->u.xpack.nbits < 0",
     "line": 1429
    },
    {
     "code": "c->u.xpack.nbits > 8 * sizeof(int64_t)",
     "line": 1429
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "c->u.xpack.rmap[i] = v",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "c->u.xpack.rmap[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "c->u.xpack.rmap",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "c->u.xpack",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "c->u",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c",
    "i",
    "v"
   ],
   "osv_id": "ARVO-42492011",
   "sites": [
    {
     "args": "sizeof(*c)",
     "callee": "malloc",
     "code": "malloc(sizeof(*c))",
     "line": 1391
    },
    {
     "args": "c",
     "callee": "free",
     "code": "free(c)",
     "line": 1432
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "cram_xpack_decode_init",
   "use_fn": "cram_xpack_decode_init"
  }
 },
 {
  "osv_id": "ARVO-42492022",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "up",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/cram/cram_io.c",
    "line": 669,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "cram_read_block",
    "file": "/src/htslib/cram/cram_io.c",
    "line": 1433
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 734,
    "fn": "safe_ltf8_get",
    "code": "(uint64_t)up[5]<<24 | (uint64_t)up[5] | up[5]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "safe_ltf8_get",
    "file": "/src/htslib/cram/cram_io.c",
    "line": 734
   },
   "code": "(uint64_t)up[5]<<24 | (uint64_t)up[5] | up[5]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "safe_ltf8_get",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:671,IF:673,IF:677,ELSE:680,IF:680,ELSE:684,IF:684,ELSE:689,IF:689,ELSE:695,IF:695,ELSE:702"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492022/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 90
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
   "dedup_token": "safe_ltf8_get--cram_varint_decode_init--cram_decoder_init"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*up = (unsigned char *)*cp",
     "line": 669
    }
   ],
   "entity_decl": {
    "line": 669,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "up",
   "func_lines": [
    668,
    739
   ],
   "func_params": {
    "names": [
     "cp",
     "endp",
     "err"
    ],
    "types": [
     "char**",
     "char*",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "endp - *cp < 9",
     "line": 671
    },
    {
     "code": "endp - *cp < ltf8_bytes[up[0]]",
     "line": 672
    },
    {
     "code": "up[0] < 0x80",
     "line": 677
    },
    {
     "code": "up[0] < 0xc0",
     "line": 680
    },
    {
     "code": "up[0] < 0xe0",
     "line": 684
    },
    {
     "code": "up[0] < 0xf0",
     "line": 689
    },
    {
     "code": "up[0] < 0xf8",
     "line": 695
    },
    {
     "code": "up[0] < 0xfc",
     "line": 702
    },
    {
     "code": "up[0] < 0xfe",
     "line": 710
    },
    {
     "code": "up[0] < 0xff",
     "line": 719
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "(uint64_t)up[5]<<24",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint64_t)up[5]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "up[5]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "up"
   ],
   "osv_id": "ARVO-42492022",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "safe_ltf8_get"
  }
 },
 {
  "osv_id": "ARVO-42492042",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "b",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/cram/cram_io.c",
    "line": 1024,
    "size": null,
    "type": "cram_block*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "uncompress_block_fqz2f",
    "file": "/src/htslib/htscodecs/htscodecs/fqzcomp_qual.c",
    "line": 1338
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1030,
    "fn": "int32_get_blk",
    "code": "((uint32_t) b->data[b->byte+1]) <<  8 | (uint32_t) b->data[b->byte+1] | b->data[b->byte+1] | b->data",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "int32_get_blk",
    "file": "/src/htslib/cram/cram_io.c",
    "line": 1030
   },
   "code": "((uint32_t) b->data[b->byte+1]) <<  8 | (uint32_t) b->data[b->byte+1] | b->data[b->byte+1] | b->data",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "int32_get_blk",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1025"
  },
  "call_chain": [],
  "types": {
   "entity_type": "cram_block*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "b"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492042/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 128
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "int32_get_blk--cram_read_SAM_hdr--cram_dopen"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1024,
    "type": "cram_block*"
   },
   "entity_name_cpg": "b",
   "func_lines": [
    1024,
    1037
   ],
   "func_params": {
    "names": [
     "b",
     "val"
    ],
    "types": [
     "cram_block*",
     "int32_t*"
    ]
   },
   "guards": [
    {
     "code": "b->uncomp_size - BLOCK_SIZE(b) < 4",
     "line": 1025
    },
    {
     "code": "v < 0x80000000U",
     "line": 1034
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "((uint32_t) b->data[b->byte+1]) <<  8",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "(uint32_t) b->data[b->byte+1]",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "b->data[b->byte+1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "b->data",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "b->byte+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "b->byte",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "b"
   ],
   "osv_id": "ARVO-42492042",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "int32_get_blk"
  }
 },
 {
  "osv_id": "ARVO-42492101",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "up",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/cram/cram_io.c",
    "line": 640,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "uncompress_block_fqz2f",
    "file": "/src/htslib/htscodecs/htscodecs/fqzcomp_qual.c",
    "line": 1338
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 653,
    "fn": "safe_itf8_get",
    "code": "((up[0] <<8) |  up[1])                           & 0x3ff | (up[0] <<8) |  up[1] | up[0] <<8 | up[0]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "safe_itf8_get",
    "file": "/src/htslib/cram/cram_io.c",
    "line": 653
   },
   "code": "((up[0] <<8) |  up[1])                           & 0x3ff | (up[0] <<8) |  up[1] | up[0] <<8 | up[0]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "safe_itf8_get",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:642,IF:644,IF:648,ELSE:651,IF:651,ELSE:654,IF:654,ELSE:657,IF:657,ELSE:661"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492101/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 58
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "safe_itf8_get--cram_decode_compression_header--cram_first_slice"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*up = (unsigned char *)*cp",
     "line": 640
    }
   ],
   "entity_decl": {
    "line": 640,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "up",
   "func_lines": [
    639,
    666
   ],
   "func_params": {
    "names": [
     "cp",
     "endp",
     "err"
    ],
    "types": [
     "char**",
     "char*",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "endp - *cp < 5",
     "line": 642
    },
    {
     "code": "endp - *cp < itf8_bytes[up[0]>>4]",
     "line": 643
    },
    {
     "code": "up[0] < 0x80",
     "line": 648
    },
    {
     "code": "up[0] < 0xc0",
     "line": 651
    },
    {
     "code": "up[0] < 0xe0",
     "line": 654
    },
    {
     "code": "up[0] < 0xf0",
     "line": 657
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "((up[0] <<8) ",
     "name": "<operator>.and",
     "nargs": null
    },
    {
     "code": "(up[0] <<8) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "up[0] <<8",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "up[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "up[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "up"
   ],
   "osv_id": "ARVO-42492101",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "safe_itf8_get"
  }
 },
 {
  "osv_id": "ARVO-42492173",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "usermeta",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1047,
    "size": null,
    "type": "uint8_t**"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1",
   "size_expr_cpg_callee": "malloc"
  },
  "sites": [
   {
    "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
    "fn": "frame_get_usermeta",
    "kind": "malloc",
    "line": 1078,
    "origin": "cpg",
    "args": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1"
   },
   {
    "code": "malloc(usermeta_len)",
    "fn": "frame_get_usermeta",
    "kind": "malloc",
    "line": 1106,
    "origin": "cpg",
    "args": "usermeta_len"
   },
   {
    "kind": "unknown",
    "line": 1108,
    "fn": "frame_get_usermeta",
    "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
    "origin": "report:crash"
   },
   {
    "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
    "fn": "frame_get_usermeta",
    "kind": "malloc",
    "line": 1113,
    "origin": "cpg",
    "args": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1"
   }
  ],
  "crash": {
   "site": {
    "fn": "frame_get_usermeta",
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1108
   },
   "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
   "access": {
    "dir": "READ",
    "width": 538976288,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "frame_get_usermeta",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "trailer_offset < 0 | usermeta_len < 0 | usermeta_len == 0",
   "guard_count": 3,
   "control_structures": "IF:1056,DO:1057,IF:1057,BREAK:1057,IF:1061,DO:1062,IF:1062,BREAK:1062,IF:1065,DO:1066,IF:1066,BREAK:1066"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t**",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "frame",
   "usermeta"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/aebf2b9858368681e497f136501ab33cc1014aed/ARVO-42492173/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_aebf2b985836.cpg",
   "testcase_size": 89
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--frame_get_usermeta--blosc2_frame_to_schunk"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1047,
    "type": "uint8_t**"
   },
   "entity_name_cpg": "usermeta",
   "func_lines": [
    1047,
    1132
   ],
   "func_params": {
    "names": [
     "frame",
     "usermeta"
    ],
    "types": [
     "blosc2_frame*",
     "uint8_t**"
    ]
   },
   "guards": [
    {
     "code": "ret < 0",
     "line": 1056
    },
    {
     "code": "nbytes > 0",
     "line": 1060
    },
    {
     "code": "trailer_offset < 0",
     "line": 1061
    },
    {
     "code": "trailer_offset + FRAME_TRAILER_USERMETA_LEN_OFFSET > frame_len",
     "line": 1065
    },
    {
     "code": "frame->sdata != NULL",
     "line": 1072
    },
    {
     "code": "rbytes != sizeof(int32_t)",
     "line": 1089
    },
    {
     "code": "usermeta_len < 0",
     "line": 1097
    },
    {
     "code": "usermeta_len == 0",
     "line": 1101
    },
    {
     "code": "frame->sdata != NULL",
     "line": 1107
    },
    {
     "code": "rbytes != (size_t)usermeta_len",
     "line": 1124
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_OFFSET, usermeta_len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "*usermeta",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_OFFSET",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "frame->sdata + trailer_offset",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "frame->sdata",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "FRAME_TRAILER_USERMETA_OFFSET",
     "name": "FRAME_TRAILER_USERMETA_OFFSET",
     "nargs": 0
    }
   ],
   "line_ids": [
    "usermeta",
    "frame",
    "trailer_offset",
    "usermeta_len"
   ],
   "osv_id": "ARVO-42492173",
   "sites": [
    {
     "args": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
     "line": 1078
    },
    {
     "args": "eframe_name",
     "callee": "free",
     "code": "free(eframe_name)",
     "line": 1081
    },
    {
     "args": "usermeta_len",
     "callee": "malloc",
     "code": "malloc(usermeta_len)",
     "line": 1106
    },
    {
     "args": "strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1",
     "callee": "malloc",
     "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
     "line": 1113
    },
    {
     "args": "eframe_name",
     "callee": "free",
     "code": "free(eframe_name)",
     "line": 1116
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "frame_get_usermeta"
  }
 },
 {
  "osv_id": "ARVO-42492301",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "out",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "line": 873,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "arith_uncompress_to",
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "line": 969
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 905,
    "fn": "unstripe",
    "code": "out[j++] = outN[idxN[k]++] | out[j++] | j++ | outN[idxN[k]++]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "unstripe",
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "line": 905
   },
   "code": "out[j++] = outN[idxN[k]++] | out[j++] | j++ | outN[idxN[k]++]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "unstripe",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j < ulen-4 | k < 4 | j < ulen",
   "guard_count": 12,
   "control_structures": "SWITCH:878,WHILE:880,FOR:881,WHILE:884,FOR:885,BREAK:888,WHILE:891,FOR:892,WHILE:895,FOR:896,BREAK:899,WHILE:903"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "out",
   "outN",
   "ulen",
   "N",
   "idxN"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492301/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 267
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "unstripe--arith_uncompress_to--arith_decode"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "out[j++] = outN[idxN[k]++]",
     "line": 882
    },
    {
     "code": "out[j++] = outN[idxN[k]++]",
     "line": 886
    },
    {
     "code": "out[j++] = outN[idxN[k]++]",
     "line": 893
    },
    {
     "code": "out[j++] = outN[idxN[k]++]",
     "line": 897
    },
    {
     "code": "out[j++] = outN[idxN[k]++]",
     "line": 905
    },
    {
     "code": "out[j++] = outN[idxN[k]++]",
     "line": 909
    }
   ],
   "entity_decl": {
    "line": 873,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "out",
   "func_lines": [
    873,
    913
   ],
   "func_params": {
    "names": [
     "out",
     "outN",
     "ulen",
     "N",
     "idxN"
    ],
    "types": [
     "unsigned char*",
     "unsigned char*",
     "unsigned int",
     "unsigned int",
     "unsigned int[256]"
    ]
   },
   "guards": [
    {
     "code": "j < ulen-4",
     "line": 880
    },
    {
     "code": "k < 4",
     "line": 881
    },
    {
     "code": "j < ulen",
     "line": 884
    },
    {
     "code": "j < ulen",
     "line": 885
    },
    {
     "code": "j < ulen-4",
     "line": 891
    },
    {
     "code": "k < 2",
     "line": 892
    },
    {
     "code": "j < ulen",
     "line": 895
    },
    {
     "code": "j < ulen",
     "line": 896
    },
    {
     "code": "j < ulen-N",
     "line": 903
    },
    {
     "code": "k < N",
     "line": 904
    },
    {
     "code": "j < ulen",
     "line": 907
    },
    {
     "code": "j < ulen",
     "line": 908
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "out[j++] = outN[idxN[k]++]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "out[j++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "j++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "outN[idxN[k]++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "idxN[k]++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "idxN[k]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out",
    "j",
    "outN",
    "idxN",
    "k"
   ],
   "osv_id": "ARVO-42492301",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "unstripe"
  }
 },
 {
  "osv_id": "ARVO-42492330",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dobj",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "line": 842,
    "size": null,
    "type": "sc_pkcs15_object"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "sc_oberthur_read_file",
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "line": 264
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "0x100",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 898,
    "fn": "sc_pkcs15emu_oberthur_add_data",
    "code": "memcpy(dobj.label, label, label_len) | dobj.label",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sc_pkcs15emu_oberthur_add_data",
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "line": 898
   },
   "code": "memcpy(dobj.label, label, label_len) | dobj.label",
   "access": {
    "dir": "READ",
    "width": 254,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sc_pkcs15emu_oberthur_add_data",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "label_len > sizeof(dobj.label) - 1",
   "guard_count": 1,
   "control_structures": "DO:849,DO:857,IF:857,IF:859,DO:860,IF:860,IF:865,DO:866,IF:866,IF:869,IF:874,DO:875"
  },
  "call_chain": [],
  "types": {
   "entity_type": "sc_pkcs15_object",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/978c912c7089fa4573add7140170feb9fcbe7f87/ARVO-42492330/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_978c912c7089.cpg",
   "testcase_size": 2328
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
   "dedup_token": "__asan_memcpy--sc_pkcs15emu_oberthur_add_data--sc_oberthur_parse_privateinfo"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "dobj.auth_id.len = sizeof(PinDomainID) > sizeof(dobj.auth_id.value)",
     "line": 907
    }
   ],
   "entity_decl": {
    "line": 842,
    "type": "sc_pkcs15_object"
   },
   "entity_name_cpg": "dobj",
   "func_lines": [
    836,
    917
   ],
   "func_params": {
    "names": [
     "p15card",
     "file_id",
     "size",
     "private"
    ],
    "types": [
     "sc_pkcs15_card*",
     "unsigned int",
     "unsigned int",
     "int"
    ]
   },
   "guards": [
    {
     "code": "_ret < 0",
     "line": 857
    },
    {
     "code": "info_len < 2",
     "line": 859
    },
    {
     "code": "_ret < 0",
     "line": 860
    },
    {
     "code": "offs > info_len",
     "line": 865
    },
    {
     "code": "_ret < 0",
     "line": 866
    },
    {
     "code": "label_len > sizeof(dobj.label) - 1",
     "line": 869
    },
    {
     "code": "offs > info_len",
     "line": 874
    },
    {
     "code": "_ret < 0",
     "line": 875
    },
    {
     "code": "app_len > sizeof(dinfo.app_label) - 1",
     "line": 878
    },
    {
     "code": "offs > info_len",
     "line": 883
    },
    {
     "code": "_ret < 0",
     "line": 884
    },
    {
     "code": "*oid != 0x06",
     "line": 888
    },
    {
     "code": "*(oid + 1) != oid_len - 2",
     "line": 888
    },
    {
     "code": "_ret < 0",
     "line": 889
    },
    {
     "code": "sizeof(PinDomainID) > sizeof(dobj.auth_id.value)",
     "line": 907
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memcpy(dobj.label, label, label_len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "dobj.label",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dobj",
    "label",
    "label_len"
   ],
   "osv_id": "ARVO-42492330",
   "sites": [
    {
     "args": "0x100",
     "callee": "<operator>.alloc",
     "code": "ch_tmp[0x100]",
     "line": 846
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sc_pkcs15emu_oberthur_add_data"
  }
 },
 {
  "osv_id": "ARVO-42492643",
  "project": "htslib",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "outp",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/rle.c",
    "line": 160,
    "size": null,
    "type": "uint8_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "rans_uncompress_to_4x16",
    "file": "/src/htslib/htscodecs/htscodecs/rANS_static4x16pr.c",
    "line": 1628
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 174,
    "fn": "rle_decode",
    "code": "memset(outp, b, rlen+1) | rlen+1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "rle_decode",
    "file": "/src/htslib/htscodecs/htscodecs/rle.c",
    "line": 174
   },
   "code": "memset(outp, b, rlen+1) | rlen+1",
   "access": {
    "dir": "WRITE",
    "width": 111,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "rle_decode",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "outp >= out_end",
   "guard_count": 1,
   "control_structures": "FOR:155,WHILE:161,IF:162,GOTO:163,IF:166,ELSE:168,IF:171,IF:172,GOTO:173,ELSE:176"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "out"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492643/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "testcase_size": 383
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
   "dedup_token": "__asan_memset--rle_decode--rans_uncompress_to_4x16"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*outp = out",
     "line": 160
    }
   ],
   "entity_decl": {
    "line": 160,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "outp",
   "func_lines": [
    142,
    188
   ],
   "func_params": {
    "names": [
     "lit",
     "lit_len",
     "run",
     "run_len",
     "rle_syms",
     "rle_nsyms",
     "out",
     "out_len"
    ],
    "types": [
     "uint8_t*",
     "uint64_t",
     "uint8_t*",
     "uint64_t",
     "uint8_t*",
     "int",
     "uint8_t*",
     "uint64_t*"
    ]
   },
   "guards": [
    {
     "code": "j < rle_nsyms",
     "line": 155
    },
    {
     "code": "lit < lit_end",
     "line": 161
    },
    {
     "code": "outp + rlen > out_end",
     "line": 172
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "memset(outp, b, rlen+1)",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "rlen+1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "outp",
    "b",
    "rlen"
   ],
   "osv_id": "ARVO-42492643",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "saved[256] = {0}",
     "line": 154
    },
    {
     "args": "out",
     "callee": "free",
     "code": "free(out)",
     "line": 186
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "rle_decode"
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