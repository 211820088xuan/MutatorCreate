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
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 63
   },
   "size_bytes": null,
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
   "fn": "ih264d_fill_bs1_16x16mb_pslice",
   "guard_count": 2,
   "guards": "pv_cur_pic_addr0 != pv_nbr_pic_addr0 | pv_cur_pic_addr0 != pv_nbr_pic_addr0",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 4
   },
   "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
   "site": {
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "line": 222
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "pv_cur_pic_addr0",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1235.log",
   "testcase_size": 82
  },
  "input_reachability": [
   "ps_cur_mv_pred",
   "ppv_map_ref_idx_to_poc"
  ],
  "osv_id": "OSV-2021-1235",
  "project": "libavc",
  "sites": [
   {
    "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "kind": "unknown",
    "line": 222,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 63
   },
   "size_bytes": null,
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
   "fn": "ih264d_mark_err_slice_skip",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 4
   },
   "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "fn": "ih264d_mark_err_slice_skip",
    "line": 1711
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "ps_dec",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1559.log",
   "testcase_size": 4489
  },
  "input_reachability": [
   "ps_dec"
  ],
  "osv_id": "OSV-2021-1559",
  "project": "libavc",
  "sites": [
   {
    "code": "ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc = (vo | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice | (volatile void **)pu1_buf",
    "fn": "ih264d_mark_err_slice_skip",
    "kind": "unknown",
    "line": 1711,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "line": null
   },
   "size_bytes": null,
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
   "fn": "main",
   "guard_count": 3,
   "guards": "nthreads_ <= nthreads | nthreads_ <= nthreads | nthreads_ <= nthreads",
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
   "code": "nthreads = 1",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zlib-ng-2.0.6/inflate.c",
    "fn": "inflate",
    "line": 408
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "nthreads",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1589.log",
   "testcase_size": 246
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-1589",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "nthreads = 1",
    "fn": "inflate",
    "kind": "unknown",
    "line": 408,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 173
   },
   "size_bytes": null,
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
   "fn": "ndlz4_decompress",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 201851904
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 544
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1645.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2021-1645",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 544,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 173
   },
   "size_bytes": null,
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
   "fn": "ndlz4_decompress",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 48423648
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 544
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1663.log",
   "testcase_size": 36
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2021-1663",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 544,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 173
   },
   "size_bytes": null,
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
   "fn": "ndlz8_decompress",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 201851904
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "fn": "ndlz8_decompress",
    "line": 462
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1676.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2021-1676",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz8_decompress",
    "kind": "unknown",
    "line": 462,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 169
   },
   "size_bytes": null,
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
   "fn": "ndlz4_decompress",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 201851904
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 540
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1710.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2021-1710",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 540,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 173
   },
   "size_bytes": null,
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
   "fn": "ndlz8_decompress",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 67108864
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "fn": "ndlz8_decompress",
    "line": 462
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1712.log",
   "testcase_size": 40
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2021-1712",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz8_decompress",
    "kind": "unknown",
    "line": 462,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 173
   },
   "size_bytes": null,
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
   "fn": "ndlz4_decompress",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 201851904
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 544
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1755.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2021-1755",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 544,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "line": null
   },
   "size_bytes": null,
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
   "fn": "ZSTD_initDDict_internal",
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
    "width": 61951
   },
   "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/decompress/zstd_ddict.c",
    "fn": "ZSTD_initDDict_internal",
    "line": 134
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "internalBuffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_886d4c9b7833.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1791.log",
   "testcase_size": 24087
  },
  "input_reachability": [
   "ddict",
   "dict",
   "dictSize"
  ],
  "osv_id": "OSV-2021-1791",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
    "fn": "ZSTD_initDDict_internal",
    "kind": "unknown",
    "line": 134,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "blosc_getitem",
   "guard_count": 1,
   "guards": "version > BLOSC_VERSION_FORMAT",
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
   "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "blosc_getitem",
    "line": 2470
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "version",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_0e8bdfce66ba.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-207.log",
   "testcase_size": 89
  },
  "input_reachability": [
   "src"
  ],
  "osv_id": "OSV-2021-207",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
    "fn": "blosc_getitem",
    "kind": "unknown",
    "line": 2470,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "line": null
   },
   "size_bytes": null,
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
   "fn": "blosc_d",
   "guard_count": 6,
   "guards": "cbytes > 0 | srcsize < cbytes | cbytes == 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 4
   },
   "code": "cbytes = sw32_(src) | sw32_(src)",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "blosc_d",
    "line": 1116
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "cbytes",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_fdfeb753f3c1.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-221.log",
   "testcase_size": 89
  },
  "input_reachability": [
   "thread_context",
   "bsize",
   "src",
   "srcsize",
   "src_offset",
   "nblock",
   "dest",
   "dest_offset",
   "tmp"
  ],
  "osv_id": "OSV-2021-221",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "cbytes = sw32_(src) | sw32_(src)",
    "fn": "blosc_d",
    "kind": "unknown",
    "line": 1116,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "line": null
   },
   "size_bytes": null,
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
   "fn": "frame_get_usermeta",
   "guard_count": 3,
   "guards": "trailer_offset < 0 | usermeta_len < 0 | usermeta_len == 0",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 538976288
   },
   "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "frame_get_usermeta",
    "line": 1116
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "usermeta",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_c91ed64cc540.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-246.log",
   "testcase_size": 89
  },
  "input_reachability": [
   "frame",
   "usermeta"
  ],
  "osv_id": "OSV-2021-246",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
    "fn": "frame_get_usermeta",
    "kind": "unknown",
    "line": 1116,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "line": null
   },
   "size_bytes": null,
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
   "fn": "blosc_getitem",
   "guard_count": 1,
   "guards": "version > BLOSC_VERSION_FORMAT",
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
   "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "blosc_getitem",
    "line": 2632
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "version",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_b4bf11aee91b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-247.log",
   "testcase_size": 89
  },
  "input_reachability": [
   "src"
  ],
  "osv_id": "OSV-2021-247",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "version = _src[BLOSC2_CHUNK_VERSION] | _src[BLOSC2_CHUNK_VERSION]",
    "fn": "blosc_getitem",
    "kind": "unknown",
    "line": 2632,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "line": null
   },
   "size_bytes": null,
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
   "fn": "ZSTD_initDDict_internal",
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
    "width": 117791
   },
   "code": "memcpy(internalBuffer, dict, dictSize)",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/decompress/zstd_ddict.c",
    "fn": "ZSTD_initDDict_internal",
    "line": 134
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "internalBuffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_0e8bdfce66ba.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-27.log",
   "testcase_size": 27249
  },
  "input_reachability": [
   "ddict",
   "dict",
   "dictSize"
  ],
  "osv_id": "OSV-2021-27",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(internalBuffer, dict, dictSize)",
    "fn": "ZSTD_initDDict_internal",
    "kind": "unknown",
    "line": 134,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-buffer-overflow",
   "report_fault_kind": "heap-buffer-overflow",
   "used": "heap-buffer-overflow"
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