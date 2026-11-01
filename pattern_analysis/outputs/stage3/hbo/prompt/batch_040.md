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
    "file": "/src/libavc/fuzzer/mvc_dec_fuzzer.cpp",
    "fn": "mvcd_aligned_malloc(void*, int, int)",
    "line": 61
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
   "fn": "ih264d_read_coeff4x4_cabac",
   "guard_count": 10,
   "guards": "u4_code_int_val_ofst >= u4_code_int_range | u4_code_int_range < ONE_RIGHT_SHIFTED_BY_8 | u4_code_int_val_ofst >= u4_code_int_range",
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
   "code": "u4_clz_m = CLZ(u4_code_int_range) | CLZ(u4_code_int_range) | UWORD32 * | UWORD32",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_cabac.c",
    "fn": "ih264d_read_coeff4x4_cabac",
    "line": 369
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "u4_clz_m",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-1124.log",
   "testcase_size": 1034896
  },
  "input_reachability": [
   "ps_bitstrm",
   "u4_ctxcat",
   "ps_ctxt_sig_coeff",
   "ps_dec",
   "ps_ctxt_coded"
  ],
  "osv_id": "OSV-2024-1124",
  "project": "libavc",
  "sites": [
   {
    "code": "u4_clz_m = CLZ(u4_code_int_range) | CLZ(u4_code_int_range) | UWORD32 * | UWORD32",
    "fn": "ih264d_read_coeff4x4_cabac",
    "kind": "unknown",
    "line": 369,
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
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "fn": "char* std::__1::__libcpp_allocate[abi:ne220000]<char>(std::__1::__element_count, unsigned long)",
    "line": 43
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
   "fn": "WebPDataCopy",
   "guard_count": 2,
   "guards": "src == NULL | dst == NULL",
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
   "code": "memcpy((void*)dst->bytes, src->bytes, src->size) | (void*)dst->bytes | dst->bytes | src->bytes",
   "site": {
    "file": "/src/libwebp/src/webp/mux_types.h",
    "fn": "WebPDataCopy",
    "line": 89
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-1356.log",
   "testcase_size": 58
  },
  "input_reachability": [
   "src",
   "dst"
  ],
  "osv_id": "OSV-2024-1356",
  "project": "libwebp",
  "sites": [
   {
    "code": "memcpy((void*)dst->bytes, src->bytes, src->size) | (void*)dst->bytes | dst->bytes | src->bytes",
    "fn": "WebPDataCopy",
    "kind": "unknown",
    "line": 89,
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
   "fn": "LLVMFuzzerTestOneInput",
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
    "width": 4
   },
   "code": "",
   "site": {
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 302
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-161.log",
   "testcase_size": 8
  },
  "input_reachability": [],
  "osv_id": "OSV-2024-161",
  "project": "pcre2",
  "sites": [
   {
    "code": "",
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "unknown",
    "line": 302,
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
   "cross_function": false,
   "site": {
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 302
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
   "fn": "LLVMFuzzerTestOneInput",
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
    "width": 4
   },
   "code": "",
   "site": {
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 363
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-173.log",
   "testcase_size": 24
  },
  "input_reachability": [],
  "osv_id": "OSV-2024-173",
  "project": "pcre2",
  "sites": [
   {
    "code": "",
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "unknown",
    "line": 363,
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
   "cross_function": false,
   "site": {
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 303
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
   "fn": "LLVMFuzzerTestOneInput",
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
    "width": 4
   },
   "code": "",
   "site": {
    "file": "/src/pcre2/src/pcre2_fuzzsupport.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 339
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-187.log",
   "testcase_size": 28
  },
  "input_reachability": [],
  "osv_id": "OSV-2024-187",
  "project": "pcre2",
  "sites": [
   {
    "code": "",
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "unknown",
    "line": 339,
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
    "file": "/src/hdf5/src/H5FL.c",
    "fn": "H5FL__malloc",
    "line": 211
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:147,IF:147,IF:155,IF:158,DO:159,DO:159,DO:159,DO:159,GOTO:159,IF:162,DO:163,DO:163",
   "fn": "H5O__chunk_protect",
   "guard_count": 5,
   "guards": "idx < oh->nchunks | 0 == idx | chk_proxy->oh == oh",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 8
   },
   "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
   "site": {
    "file": "/src/hdf5/src/H5Ochunk.c",
    "fn": "H5O__chunk_protect",
    "line": 178
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5Ochunk.c",
    "line": 171,
    "size": null,
    "type": "H5O_chk_cache_ud_t"
   },
   "kind": "struct",
   "name": "chk_udata",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_fe7ae303b171.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-370.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "f",
   "oh",
   "idx"
  ],
  "osv_id": "OSV-2024-370",
  "project": "hdf5",
  "sites": [
   {
    "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
    "fn": "H5O__chunk_protect",
    "kind": "unknown",
    "line": 178,
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
   "entity_type": "H5O_chk_cache_ud_t",
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
    "line": 211
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
   "fn": "H5F__accum_free",
   "guard_count": 2,
   "guards": "overlap_size < accum->dirty_off | overlap_size < (accum->dirty_off + accum->dirty_len)",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 361
   },
   "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
   "site": {
    "file": "/src/hdf5/src/H5Faccum.c",
    "fn": "H5F__accum_free",
    "line": 885
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "accum",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-381.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "f_sh",
   "addr",
   "size"
  ],
  "osv_id": "OSV-2024-381",
  "project": "hdf5",
  "sites": [
   {
    "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
    "fn": "H5F__accum_free",
    "kind": "unknown",
    "line": 885,
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
    "file": "/src/hdf5/src/H5FL.c",
    "fn": "H5FL__malloc",
    "line": 237
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2782,IF:2787,FOR:2788,ELSE:2794,FOR:2795",
   "fn": "H5F_addr_encode_len",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 1
   },
   "code": "*(*pp)++ = 0xff | *(*pp)++ | (*pp)++ | *pp",
   "site": {
    "file": "/src/hdf5/src/H5Fint.c",
    "fn": "H5F_addr_encode_len",
    "line": 2796
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5Fint.c",
    "line": 2777,
    "size": null,
    "type": "uint8_t**"
   },
   "kind": "pointer",
   "name": "pp",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-387.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "pp",
   "addr"
  ],
  "osv_id": "OSV-2024-387",
  "project": "hdf5",
  "sites": [
   {
    "code": "*(*pp)++ = 0xff | *(*pp)++ | (*pp)++ | *pp",
    "fn": "H5F_addr_encode_len",
    "kind": "unknown",
    "line": 2796,
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
   "entity_type": "uint8_t**",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/hdf5/src/H5FL.c",
    "fn": "H5FL__malloc",
    "line": 211
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:767,IF:767,IF:777,DO:778,DO:778,DO:778,DO:778,GOTO:778",
   "fn": "H5O__cache_chk_serialize",
   "guard_count": 1,
   "guards": "chk_proxy->oh->chunk[chk_proxy->chunkno].size == len",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 64
   },
   "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
   "site": {
    "file": "/src/hdf5/src/H5Ocache.c",
    "fn": "H5O__cache_chk_serialize",
    "line": 784
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5Ocache.c",
    "line": 762,
    "size": null,
    "type": "void*"
   },
   "kind": "pointer",
   "name": "image",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_ed082ac981a2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-390.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "image",
   "len",
   "_thing"
  ],
  "osv_id": "OSV-2024-390",
  "project": "hdf5",
  "sites": [
   {
    "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
    "fn": "H5O__cache_chk_serialize",
    "kind": "unknown",
    "line": 784,
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
    "file": "/src/libavc/fuzzer/mvc_dec_fuzzer.cpp",
    "fn": "mvcd_aligned_malloc(void*, int, int)",
    "line": 61
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
   "fn": "ih264d_read_coeff4x4_cabac",
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
    "width": 4
   },
   "code": "NEXTBITS(read_bits, u4_offset, pu4_buffer, CABAC_BITS_TO | UWORD32 * | UWORD32 | (u4_offset) >> 5",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_cabac.c",
    "fn": "ih264d_read_coeff4x4_cabac",
    "line": 412
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "read_bits",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-456.log",
   "testcase_size": 1048576
  },
  "input_reachability": [
   "ps_bitstrm",
   "u4_ctxcat",
   "ps_ctxt_sig_coeff",
   "ps_dec",
   "ps_ctxt_coded"
  ],
  "osv_id": "OSV-2024-456",
  "project": "libavc",
  "sites": [
   {
    "code": "NEXTBITS(read_bits, u4_offset, pu4_buffer, CABAC_BITS_TO | UWORD32 * | UWORD32 | (u4_offset) >> 5",
    "fn": "ih264d_read_coeff4x4_cabac",
    "kind": "unknown",
    "line": 412,
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
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc",
    "line": 85
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
   "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
   "guard_count": 1,
   "guards": "j < num_cols",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 48
   },
   "code": "memcpy(pu1_dst, pu1_src, num_cols)",
   "site": {
    "file": "/src/libavc/decoder/ih264d_format_conv.c",
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "line": 497
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "pu1_dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-637.log",
   "testcase_size": 6180
  },
  "input_reachability": [
   "pu1_y_src",
   "pu1_y_dst",
   "wd",
   "src_y_strd",
   "dst_y_strd"
  ],
  "osv_id": "OSV-2024-637",
  "project": "libavc",
  "sites": [
   {
    "code": "memcpy(pu1_dst, pu1_src, num_cols)",
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "kind": "unknown",
    "line": 497,
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
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc",
    "line": 85
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
   "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
   "guard_count": 1,
   "guards": "j < num_cols",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 32
   },
   "code": "memcpy(pu1_dst, pu1_src, num_cols)",
   "site": {
    "file": "/src/libavc/decoder/ih264d_format_conv.c",
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "line": 497
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "pu1_dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-638.log",
   "testcase_size": 966
  },
  "input_reachability": [
   "pu1_y_src",
   "pu1_y_dst",
   "wd",
   "src_y_strd",
   "dst_y_strd"
  ],
  "osv_id": "OSV-2024-638",
  "project": "libavc",
  "sites": [
   {
    "code": "memcpy(pu1_dst, pu1_src, num_cols)",
    "fn": "ih264d_fmt_conv_420sp_to_420sp_swap_uv",
    "kind": "unknown",
    "line": 497,
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
    "file": "/src/jq/src/jv_alloc.c",
    "fn": "jv_mem_alloc",
    "line": 141
   },
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:573,IF:578,ELSE:581,IF:581,ELSE:584,IF:584,IF:587,ELSE:592,IF:600,FOR:603,FOR:603,IF:604",
   "fn": "f_format",
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
    "width": 2
   },
   "code": "* fmt_s = jv_string_value(fmt) | jv_string_value(fmt)",
   "site": {
    "file": "/src/jq/src/jv.c",
    "fn": "jvp_literal_number_new",
    "line": 577
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/jq/src/jv.c",
    "line": 577,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "fmt_s",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/jq_6d8e9f98ae3c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-831.log",
   "testcase_size": 412
  },
  "input_reachability": [
   "fmt"
  ],
  "osv_id": "OSV-2024-831",
  "project": "jq",
  "sites": [
   {
    "code": "* fmt_s = jv_string_value(fmt) | jv_string_value(fmt)",
    "fn": "jvp_literal_number_new",
    "kind": "unknown",
    "line": 577,
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
   "entity_type": "char*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/jq/src/jv_alloc.c",
    "fn": "jv_mem_alloc",
    "line": 141
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
   "fn": "validate_relpath",
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
    "width": 2
   },
   "code": "strchr(s, '\\\\')",
   "site": {
    "file": "/src/jq/src/linker.c",
    "fn": "validate_relpath",
    "line": 96
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "s",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-919.log",
   "testcase_size": 24
  },
  "input_reachability": [],
  "osv_id": "OSV-2024-919",
  "project": "jq",
  "sites": [
   {
    "code": "strchr(s, '\\\\')",
    "fn": "validate_relpath",
    "kind": "unknown",
    "line": 96,
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
    "file": "/src/libwebp/src/dec/vp8l_dec.c",
    "fn": "AllocateInternalBuffers32b",
    "line": 1609
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
   "fn": "GIFReadFrame",
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
    "width": 32
   },
   "code": "ErrorGIFNotAvailable()",
   "site": {
    "file": "/src/libwebp/src/dsp/lossless_avx2.c",
    "fn": "AddGreenToBlueAndRed_AVX2",
    "line": 349
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2025-796.log",
   "testcase_size": 131
  },
  "input_reachability": [],
  "osv_id": "OSV-2025-796",
  "project": "libwebp",
  "sites": [
   {
    "code": "ErrorGIFNotAvailable()",
    "fn": "AddGreenToBlueAndRed_AVX2",
    "kind": "unknown",
    "line": 349,
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