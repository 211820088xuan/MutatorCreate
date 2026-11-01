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
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
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
   "fn": "handle_runlen",
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
   "code": "all_zeros = src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZER | src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZERO_RUNLEN <<  | src[BLOSC2_CHUNK_BLOSC2_FLAGS] | BLOSC2_ZERO_RUNLEN << 4",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "handle_runlen",
    "line": 2237
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "all_zeros",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_acd71b1e12cb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-271.log",
   "testcase_size": 16
  },
  "input_reachability": [
   "src"
  ],
  "osv_id": "OSV-2021-271",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "all_zeros = src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZER | src[BLOSC2_CHUNK_BLOSC2_FLAGS] & (BLOSC2_ZERO_RUNLEN <<  | src[BLOSC2_CHUNK_BLOSC2_FLAGS] | BLOSC2_ZERO_RUNLEN << 4",
    "fn": "handle_runlen",
    "kind": "unknown",
    "line": 2237,
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
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
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
   "fn": "get_vlmeta_from_trailer",
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
   "code": "idxp[0] != 0xde | idxp[0]",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "get_vlmeta_from_trailer",
    "line": 1334
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "idxp",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_d5622cd1a624.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-382.log",
   "testcase_size": 98
  },
  "input_reachability": [
   "trailer"
  ],
  "osv_id": "OSV-2021-382",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "idxp[0] != 0xde | idxp[0]",
    "fn": "get_vlmeta_from_trailer",
    "kind": "unknown",
    "line": 1334,
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
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
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
   "fn": "frame_get_lazychunk",
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
   "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | *chunk + BLOSC2_CHUNK_CBYTES | *chunk",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "frame_get_lazychunk",
    "line": 1973
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "lazychunk_cbytes",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5eff30b8b3bc.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-428.log",
   "testcase_size": 187
  },
  "input_reachability": [
   "frame",
   "nchunk",
   "chunk"
  ],
  "osv_id": "OSV-2021-428",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | *chunk + BLOSC2_CHUNK_CBYTES | *chunk",
    "fn": "frame_get_lazychunk",
    "kind": "unknown",
    "line": 1973,
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
   "fn": "blosc_read_header",
   "guard_count": 2,
   "guards": "srcsize < BLOSC_MIN_HEADER_LENGTH | header->cbytes < BLOSC_MIN_HEADER_LENGTH",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 16
   },
   "code": "memcpy(header, src, BLOSC_MIN_HEADER_LENGTH)",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "blosc_read_header",
    "line": 677
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "header",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-464.log",
   "testcase_size": 184
  },
  "input_reachability": [
   "src",
   "srcsize",
   "header"
  ],
  "osv_id": "OSV-2021-464",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(header, src, BLOSC_MIN_HEADER_LENGTH)",
    "fn": "blosc_read_header",
    "kind": "unknown",
    "line": 677,
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
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
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
    "line": 1349
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-476.log",
   "testcase_size": 185
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
  "osv_id": "OSV-2021-476",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "cbytes = sw32_(src) | sw32_(src)",
    "fn": "blosc_d",
    "kind": "unknown",
    "line": 1349,
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
    "width": 222
   },
   "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.8/decompress/zstd_ddict.c",
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-481.log",
   "testcase_size": 165
  },
  "input_reachability": [
   "ddict",
   "dict",
   "dictSize"
  ],
  "osv_id": "OSV-2021-481",
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
   "fn": "initialize_context_decompression",
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "initialize_context_decompression",
    "line": 1806
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_54a7337f5e05.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-485.log",
   "testcase_size": 166
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-485",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "",
    "fn": "initialize_context_decompression",
    "kind": "unknown",
    "line": 1806,
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
    "line": 1398
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_f489cdbd0a25.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-496.log",
   "testcase_size": 186
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
  "osv_id": "OSV-2021-496",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "cbytes = sw32_(src) | sw32_(src)",
    "fn": "blosc_d",
    "kind": "unknown",
    "line": 1398,
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
   "fn": "get_vlmeta_from_trailer",
   "guard_count": 1,
   "guards": "content_len < 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 67
   },
   "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "get_vlmeta_from_trailer",
    "line": 1390
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "content",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_2112e1398b74.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-622.log",
   "testcase_size": 202
  },
  "input_reachability": [
   "trailer",
   "trailer_len"
  ],
  "osv_id": "OSV-2021-622",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "fn": "get_vlmeta_from_trailer",
    "kind": "unknown",
    "line": 1390,
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
    "width": 270541055
   },
   "code": "memcpy(_dest, src, bsize_)",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "blosc_d",
    "line": 1458
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "_dest",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_77b7dfd41f4b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-639.log",
   "testcase_size": 138
  },
  "input_reachability": [
   "thread_context",
   "bsize",
   "memcpyed",
   "src",
   "srcsize",
   "src_offset",
   "nblock",
   "dest",
   "dest_offset",
   "tmp"
  ],
  "osv_id": "OSV-2021-639",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(_dest, src, bsize_)",
    "fn": "blosc_d",
    "kind": "unknown",
    "line": 1458,
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
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
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
   "fn": "get_meta_from_header",
   "guard_count": 1,
   "guards": "content_len < 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 6
   },
   "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "get_meta_from_header",
    "line": 1310
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "content",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_4d2510757d79.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-640.log",
   "testcase_size": 173
  },
  "input_reachability": [
   "header",
   "header_len"
  ],
  "osv_id": "OSV-2021-640",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "fn": "get_meta_from_header",
    "kind": "unknown",
    "line": 1310,
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
    "file": "/src/espeak-ng/tests/ssml-fuzzer.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 49
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
   "control_structures": "SWITCH:541,IF:552,GOTO:552,IF:554,GOTO:554,IF:559,GOTO:559,IF:561,GOTO:561,IF:563,GOTO:563,IF:568",
   "fn": "string_decoder_getc_utf_8",
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
   "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "fn": "string_decoder_getc_utf_8",
    "line": 539
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539,
    "size": null,
    "type": "uint8_t"
   },
   "kind": "struct",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_d8ec91e809e9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-767.log",
   "testcase_size": 2
  },
  "input_reachability": [
   "decoder"
  ],
  "osv_id": "OSV-2021-767",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
    "fn": "string_decoder_getc_utf_8",
    "kind": "unknown",
    "line": 539,
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
   "entity_type": "uint8_t",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
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
   "fn": "_blosc_getitem",
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
    "width": 8
   },
   "code": "memcpy(_dest, _src, ntbytes)",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "_blosc_getitem",
    "line": 2833
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "_dest",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_886d4c9b7833.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-779.log",
   "testcase_size": 187
  },
  "input_reachability": [
   "context",
   "header",
   "src",
   "start",
   "nitems",
   "dest"
  ],
  "osv_id": "OSV-2021-779",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(_dest, _src, ntbytes)",
    "fn": "_blosc_getitem",
    "kind": "unknown",
    "line": 2833,
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
    "file": "/src/espeak-ng/tests/ssml-fuzzer.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 64
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
   "control_structures": "SWITCH:541,IF:552,GOTO:552,IF:554,GOTO:554,IF:559,GOTO:559,IF:561,GOTO:561,IF:563,GOTO:563,IF:568",
   "fn": "string_decoder_getc_utf_8",
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
   "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "fn": "string_decoder_getc_utf_8",
    "line": 539
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539,
    "size": null,
    "type": "uint8_t"
   },
   "kind": "struct",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_55e452cd9b40.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-787.log",
   "testcase_size": 2
  },
  "input_reachability": [
   "decoder"
  ],
  "osv_id": "OSV-2021-787",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
    "fn": "string_decoder_getc_utf_8",
    "kind": "unknown",
    "line": 539,
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
   "entity_type": "uint8_t",
   "is_signed": null,
   "ptr_origin": "unknown"
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
   "fn": "ZSTD_copyRawBlock",
   "guard_count": 3,
   "guards": "srcSize > dstCapacity | dst == NULL | srcSize == 0",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 37536
   },
   "code": "ZSTD_memcpy(dst, src, srcSize) | memcpy((dst), (src), (srcSize))",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/decompress/zstd_decompress.c",
    "fn": "ZSTD_copyRawBlock",
    "line": 828
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5a50726608d0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-897.log",
   "testcase_size": 11408
  },
  "input_reachability": [
   "dst",
   "dstCapacity",
   "src",
   "srcSize"
  ],
  "osv_id": "OSV-2021-897",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "ZSTD_memcpy(dst, src, srcSize) | memcpy((dst), (src), (srcSize))",
    "fn": "ZSTD_copyRawBlock",
    "kind": "unknown",
    "line": 828,
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