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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 169
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
   "control_structures": "IF:445,IF:452,FOR:466,FOR:476,FOR:477,IF:478,IF:482,ELSE:484,IF:487,ELSE:489,IF:494,ELSE:497",
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
    "line": 463
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 438,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42505824/report.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42505824",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 443,
    "origin": "cpg"
   },
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz8_decompress",
    "kind": "unknown",
    "line": 463,
    "origin": "report:crash"
   },
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 475,
    "origin": "cpg"
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
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:445,IF:452,FOR:466,FOR:476,FOR:477,IF:478,IF:482,ELSE:484,IF:487,ELSE:489,IF:494,ELSE:497",
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
    "line": 463
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 438,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42506129/report.log",
   "testcase_size": 40
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42506129",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 443,
    "origin": "cpg"
   },
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz8_decompress",
    "kind": "unknown",
    "line": 463,
    "origin": "report:crash"
   },
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 475,
    "origin": "cpg"
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
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:522,IF:529,FOR:543,FOR:553,FOR:554,IF:555,IF:559,ELSE:561,IF:564,ELSE:566,IF:570,ELSE:573",
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
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "line": 515,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42506157/report.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42506157",
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
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_operator_new<unsigned long>",
    "line": 245
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
   "control_structures": "IF:208,IF:225,IF:233,IF:238,IF:242",
   "fn": "main",
   "guard_count": 3,
   "guards": "std::vector<uint8_t | std::vector<uint8_t> icc_profile | std::vector<uint8_t",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 1
   },
   "code": "std::vector<uint8_t> icc_profile | std::vector<uint8_t | std::vector",
   "site": {
    "file": "/src/libjxl/lib/jxl/dec_reconstruct.cc",
    "fn": "StoreRGBA<hwy::N_AVX3::Simd<unsigned char, 4>, hwy::N_AVX3::Vec128<unsigned char, 4> >",
    "line": 231
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "std",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_9767c3862c23.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/9767c3862c237c4c3e32a75fe191feb8b097fb1c/ARVO-42506464/report.log",
   "testcase_size": 41
  },
  "input_reachability": [],
  "osv_id": "ARVO-42506464",
  "project": "libjxl",
  "sites": [
   {
    "code": "std::vector<uint8_t> icc_profile | std::vector<uint8_t | std::vector",
    "fn": "StoreRGBA<hwy::N_AVX3::Simd<unsigned char, 4>, hwy::N_AVX3::Vec128<unsigned char, 4> >",
    "kind": "unknown",
    "line": 231,
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
    "file": "/src/assimp/code/Common/ZipArchiveIOSystem.cpp",
    "fn": "Assimp::IOSystem2Unzip::opendisk(void*, void*, unsigned int, int)",
    "line": 127
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
   "fn": "exportContentTypes",
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
   "code": "mContentOutput << std::endl | std::endl",
   "site": {
    "file": "/src/assimp/code/Common/ZipArchiveIOSystem.cpp",
    "fn": "Assimp::IOSystem2Unzip::opendisk(void*, void*, unsigned int, int)",
    "line": 131
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "mContentOutput",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_6a1f720f68f8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/6a1f720f68f8025dc987d2e7a42217d401ed3928/ARVO-42507104/report.log",
   "testcase_size": 2949
  },
  "input_reachability": [],
  "osv_id": "ARVO-42507104",
  "project": "assimp",
  "sites": [
   {
    "code": "mContentOutput << std::endl | std::endl",
    "fn": "Assimp::IOSystem2Unzip::opendisk(void*, void*, unsigned int, int)",
    "kind": "unknown",
    "line": 131,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
    "line": null
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
   "control_structures": "IF:415,IF:418,FOR:423,FOR:424,IF:426,FOR:427,FOR:458,CONTINUE:462,FOR:465,FOR:469,FOR:480,FOR:491",
   "fn": "bshuf_trans_byte_bitrow_altivec",
   "guard_count": 9,
   "guards": "k < 8 | k < 8 | k < 16",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 16
   },
   "code": "k = 0 | k < 16 | k += 8",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/lz4-1.9.3/lz4.c",
    "fn": "LZ4_wildCopy32",
    "line": 469
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/internal-complibs/lz4-1.9.3/lz4.c",
    "line": 480,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "k",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_c4c8c7cb7f22.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/c4c8c7cb7f22323cda796575f699ad4c953b6661/ARVO-42507214/report.log",
   "testcase_size": 270
  },
  "input_reachability": [],
  "osv_id": "ARVO-42507214",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "k = 0 | k < 16 | k += 8",
    "fn": "LZ4_wildCopy32",
    "kind": "unknown",
    "line": 469,
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 169
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
   "control_structures": "IF:445,IF:452,FOR:466,FOR:476,FOR:477,IF:478,IF:482,ELSE:484,IF:487,ELSE:489,IF:494,ELSE:497",
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
    "line": 463
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 438,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_6b40381b5b09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42507220/report.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42507220",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 443,
    "origin": "cpg"
   },
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz8_decompress",
    "kind": "unknown",
    "line": 463,
    "origin": "report:crash"
   },
   {
    "code": "malloc(cell_size)",
    "fn": "ndlz8_decompress",
    "kind": "malloc",
    "line": 475,
    "origin": "cpg"
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
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/leptonica/src/pix1.c",
    "fn": "pixdata_malloc",
    "line": 247
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
   "control_structures": "IF:3348,IF:3351,IF:3353,IF:3356,IF:3363,FOR:3364,FOR:3366,IF:3368,ELSE:3371,FOR:3373,IF:3374,CONTINUE:3374",
   "fn": "pixCountArbInRect",
   "guard_count": 4,
   "guards": "j < w | pixval == val | j < bw",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 1
   },
   "code": "pixval = GET_DATA_BYTE(line, bx + j) | GET_DATA_BYTE(line, bx + j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (bx | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (bx",
   "site": {
    "file": "/src/leptonica/src/pix3.c",
    "fn": "pixCountArbInRect",
    "line": 3378
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/leptonica/src/pix3.c",
    "line": 3343,
    "size": null,
    "type": "l_int32"
   },
   "kind": "struct",
   "name": "pixval",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_9562d40781af.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/9562d40781afffb0ae041681346ab5443e36528f/ARVO-42507762/report.log",
   "testcase_size": 16420
  },
  "input_reachability": [
   "pixs",
   "factor"
  ],
  "osv_id": "ARVO-42507762",
  "project": "leptonica",
  "sites": [
   {
    "code": "pixval = GET_DATA_BYTE(line, bx + j) | GET_DATA_BYTE(line, bx + j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (bx | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (bx",
    "fn": "pixCountArbInRect",
    "kind": "unknown",
    "line": 3378,
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
   "entity_type": "l_int32",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/zstd/tests/fuzz/fuzz_helpers.c",
    "fn": "FUZZ_malloc",
    "line": 19
   },
   "size_bytes": null,
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
   "fn": "generateRandomSequences",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 16
   },
   "code": null,
   "site": {
    "file": "/src/zstd/tests/fuzz/sequence_compression_api.c",
    "fn": "generateRandomSequences",
    "line": 217
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
   "cpg": "/root/gyx/mutator_create/cpg_files/zstd_7543085013db.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/zstd/address/7543085013db1a20a848d166e5931edc49e3cc2f/ARVO-42507889/report.log",
   "testcase_size": 1046506
  },
  "input_reachability": [],
  "osv_id": "ARVO-42507889",
  "project": "zstd",
  "sites": [
   {
    "code": null,
    "fn": "generateRandomSequences",
    "kind": "unknown",
    "line": 217,
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
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/fluent-bit/lib/onigmo/regparse.c",
    "fn": "node_new",
    "line": 1125
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
   "control_structures": "DO:289,IF:289,DO:289,DO:289,IF:289,IF:289",
   "fn": "add_bytes",
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
    "width": 3
   },
   "code": "BBUF_ADD(reg, bytes, len) | int | ((reg)->used) + (int)((len)) | (reg)->used",
   "site": {
    "file": "/src/fluent-bit/lib/onigmo/regcomp.c",
    "fn": "add_bytes",
    "line": 289
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/lib/onigmo/regcomp.c",
    "line": 287,
    "size": null,
    "type": "regex_t*"
   },
   "kind": "pointer",
   "name": "reg",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_dbe29a1a77b5.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42508173/report.log",
   "testcase_size": 703
  },
  "input_reachability": [
   "reg",
   "bytes",
   "len"
  ],
  "osv_id": "ARVO-42508173",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "BBUF_ADD(reg, bytes, len) | int | ((reg)->used) + (int)((len)) | (reg)->used",
    "fn": "add_bytes",
    "kind": "unknown",
    "line": 289,
    "origin": "report:crash"
   },
   {
    "code": "realloc((((reg)))->p, (((reg)))->alloc)",
    "fn": "add_bytes",
    "kind": "realloc",
    "line": 289,
    "origin": "cpg"
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
   "entity_type": "regex_t*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "fn": "flb_malloc",
    "line": 56
   },
   "size_bytes": null,
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
   "fn": "onig_node_str_cat",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/fluent-bit/lib/onigmo/regparse.c",
    "fn": "onig_node_str_cat",
    "line": null
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
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_dbe29a1a77b5.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42508187/report.log",
   "testcase_size": 575
  },
  "input_reachability": [],
  "osv_id": "ARVO-42508187",
  "project": "fluent-bit",
  "sites": [],
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x270b2)",
    "line": null
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
   "control_structures": "FOR:7111,IF:7112,ELSE:7114,IF:7114",
   "fn": "ndpi_strncasestr",
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
    "width": 1
   },
   "code": "str1[0] == '\\0' | str1[0]",
   "site": {
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "fn": "ndpi_strncasestr",
    "line": 7112
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 7106,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "str1",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_f5035521e8be.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/f5035521e8beadd228a304fd8707ba798bc850d2/ARVO-42508203/report.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "str1",
   "str2",
   "len"
  ],
  "osv_id": "ARVO-42508203",
  "project": "ndpi",
  "sites": [
   {
    "code": "str1[0] == '\\0' | str1[0]",
    "fn": "ndpi_strncasestr",
    "kind": "unknown",
    "line": 7112,
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
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "calloc",
   "cross_function": true,
   "site": {
    "file": "/src/libredwg/src/in_dxf.c",
    "fn": "xcalloc",
    "line": 216
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
   "fn": "dwg_free_HATCH_private",
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
   "code": "",
   "site": {
    "file": "/src/libredwg/src/dwg.spec",
    "fn": "dwg_free_HATCH_private",
    "line": 4225
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_7f525b96bb6d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/7f525b96bb6db2989a9d296cda5d76aeb46f71af/ARVO-42508287/report.log",
   "testcase_size": 256
  },
  "input_reachability": [],
  "osv_id": "ARVO-42508287",
  "project": "libredwg",
  "sites": [
   {
    "code": "",
    "fn": "dwg_free_HATCH_private",
    "kind": "unknown",
    "line": 4225,
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
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/open62541/src/ua_types.c",
    "fn": "UA_new",
    "line": 997
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
   "control_structures": "IF:1377,IF:1379,IF:1381,SWITCH:1384,IF:1392,IF:1402,IF:1404",
   "fn": "extensionObjectOrder",
   "guard_count": 3,
   "guards": "enc2 > UA_EXTENSIONOBJECT_DECODED | enc1 != enc2 | enc1 < enc2",
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
   "code": "enc2 = p2->encoding | p2->encoding",
   "site": {
    "file": "/src/open62541/src/ua_types.c",
    "fn": "extensionObjectOrder",
    "line": 1376
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 1376,
    "size": null,
    "type": "UA_ExtensionObjectEncoding"
   },
   "kind": "struct",
   "name": "enc2",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_4a12b64f3242.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/open62541/address/4a12b64f32427042605dbeafa6fded3583316244/ARVO-42508445/report.log",
   "testcase_size": 4155
  },
  "input_reachability": [
   "p2"
  ],
  "osv_id": "ARVO-42508445",
  "project": "open62541",
  "sites": [
   {
    "code": "enc2 = p2->encoding | p2->encoding",
    "fn": "extensionObjectOrder",
    "kind": "unknown",
    "line": 1376,
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
   "entity_type": "UA_ExtensionObjectEncoding",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/icu/icu4c/source/test/fuzzer/ucasemap_fuzzer.cpp",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 38
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
   "control_structures": "IF:454,IF:455,IF:458,ELSE:461,IF:466,ELSE:468,IF:468,ELSE:470,IF:476,IF:477,IF:480,ELSE:482",
   "fn": "maybeTitleDutchIJ",
   "guard_count": 6,
   "guards": "c2 == ACUTE_BYTE0 | index < segmentLimit | index == segmentLimit",
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
   "code": "c2 = src[index++] | src[index++] | index++",
   "site": {
    "file": "/src/icu/icu4c/source/common/ucasemap.cpp",
    "fn": "maybeTitleDutchIJ",
    "line": 451
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/icu/icu4c/source/common/ucasemap.cpp",
    "line": 450,
    "size": null,
    "type": "UChar32"
   },
   "kind": "struct",
   "name": "c2",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_66c83262804f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/icu/address/66c83262804f8752f4a87753f6a325e8f40febf5/ARVO-42508617/report.log",
   "testcase_size": 9
  },
  "input_reachability": [
   "src",
   "c",
   "start",
   "segmentLimit"
  ],
  "osv_id": "ARVO-42508617",
  "project": "icu",
  "sites": [
   {
    "code": "c2 = src[index++] | src[index++] | index++",
    "fn": "maybeTitleDutchIJ",
    "kind": "unknown",
    "line": 451,
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
   "entity_type": "UChar32",
   "is_signed": null,
   "ptr_origin": "unknown"
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