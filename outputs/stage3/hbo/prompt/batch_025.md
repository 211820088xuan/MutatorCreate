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
   "api": "calloc",
   "cross_function": true,
   "site": {
    "file": "/src/LibRaw/./libraw/libraw_alloc.h",
    "fn": "libraw_memmgr::calloc(unsigned long, unsigned long)",
    "line": 56
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
   "control_structures": "IF:468,IF:473,IF:474,IF:479,IF:484,ELSE:487,IF:493,IF:499,IF:500,ELSE:502,SWITCH:519,BREAK:525",
   "fn": "write",
   "guard_count": 2,
   "guards": "x < tmpgrayimage.width() | x < tmpgrayimage.width()",
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
   "code": "x = 0 | x < tmpgrayimage.width() | tmpgrayimage.width() | x++",
   "site": {
    "file": "/src/kimageformats/src/imageformats/raw.cpp",
    "fn": "(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)",
    "line": 608
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/kimageformats/src/imageformats/raw.cpp",
    "line": 608,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "x",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_d881a7bbb156.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kimageformats/address/d881a7bbb1562af383bbb6ca20340ad739fb0d13/ARVO-42517623/report.log",
   "testcase_size": 6471
  },
  "input_reachability": [
   "image"
  ],
  "osv_id": "ARVO-42517623",
  "project": "kimageformats",
  "sites": [
   {
    "code": "x = 0 | x < tmpgrayimage.width() | tmpgrayimage.width() | x++",
    "fn": "(anonymous namespace)::LoadRAW(QImageIOHandler*, QImage&)",
    "kind": "unknown",
    "line": 608,
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
    "width": 3959948288
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42517712/report.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42517712",
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
    "width": 8
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42517725/report.log",
   "testcase_size": 386
  },
  "input_reachability": [
   "reg",
   "bytes",
   "len"
  ],
  "osv_id": "ARVO-42517725",
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
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/mongoose/test/fuzz.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 70
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
   "fn": "rx_ip(mip_if*, pkt*)",
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
    "width": 2
   },
   "code": null,
   "site": {
    "file": "/src/mongoose/mip/mip.c",
    "fn": "rx_ip(mip_if*, pkt*)",
    "line": 720
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
   "cpg": "/root/gyx/mutator_create/cpg_files/mongoose_1f85fcc9b040.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mongoose/address/1f85fcc9b040635483b775fae4ae74a5c945e60a/ARVO-42517782/report.log",
   "testcase_size": 34
  },
  "input_reachability": [],
  "osv_id": "ARVO-42517782",
  "project": "mongoose",
  "sites": [
   {
    "code": null,
    "fn": "rx_ip(mip_if*, pkt*)",
    "kind": "unknown",
    "line": 720,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "mg_mqtt_parse",
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
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/mongoose/src/mqtt.c",
    "fn": "mg_mqtt_parse",
    "line": 177
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
   "cpg": "/root/gyx/mutator_create/cpg_files/mongoose_1f85fcc9b040.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mongoose/address/1f85fcc9b040635483b775fae4ae74a5c945e60a/ARVO-42517792/report.log",
   "testcase_size": 4
  },
  "input_reachability": [],
  "osv_id": "ARVO-42517792",
  "project": "mongoose",
  "sites": [
   {
    "code": null,
    "fn": "mg_mqtt_parse",
    "kind": "unknown",
    "line": 177,
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
    "file": "/src/libarchive/libarchive/archive_read.c",
    "fn": "archive_read_new",
    "line": 96
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
   "control_structures": "IF:805",
   "fn": "archive_read_format_capabilities",
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
   "code": "a && a->format && a->format->format_capabilties | a && a->format | a->format | a->format->format_capabilties",
   "site": {
    "file": "/src/libarchive/libarchive/archive_read.c",
    "fn": "archive_read_format_capabilities",
    "line": 805
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read.c",
    "line": 804,
    "size": null,
    "type": "archive_read*"
   },
   "kind": "pointer",
   "name": "a",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_fa4b613f2e25.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/fa4b613f2e2510bd036f2eeed2fece97cd18b079/ARVO-42518409/report.log",
   "testcase_size": 800
  },
  "input_reachability": [
   "_a"
  ],
  "osv_id": "ARVO-42518409",
  "project": "libarchive",
  "sites": [
   {
    "code": "a && a->format && a->format->format_capabilties | a && a->format | a->format | a->format->format_capabilties",
    "fn": "archive_read_format_capabilities",
    "kind": "unknown",
    "line": 805,
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
   "entity_type": "archive_read*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "fn": "hb_realloc_impl",
    "line": 55
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
   "fn": "check_glyph_property",
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
    "file": "/src/harfbuzz/src/hb-ot-layout-gsubgpos.hh",
    "fn": "check_glyph_property",
    "line": 778
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
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_3b43096ef336.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/3b43096ef336cf3ba149518c82541c0079ef0f92/ARVO-42518543/report.log",
   "testcase_size": 285
  },
  "input_reachability": [],
  "osv_id": "ARVO-42518543",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "",
    "fn": "check_glyph_property",
    "kind": "unknown",
    "line": 778,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
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
   "control_structures": "IF:153,IF:153,IF:153",
   "fn": "bit_read_B",
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
   "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
   "site": {
    "file": "/src/libredwg/src/bits.c",
    "fn": "bit_read_B",
    "line": 154
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 151,
    "size": null,
    "type": "unsigned char"
   },
   "kind": "struct",
   "name": "byte",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_45e5371477dc.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/45e5371477dc4a07809d97e109a62f3f84d8672e/ARVO-42519041/report.log",
   "testcase_size": 1014
  },
  "input_reachability": [
   "dat"
  ],
  "osv_id": "ARVO-42519041",
  "project": "libredwg",
  "sites": [
   {
    "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
    "fn": "bit_read_B",
    "kind": "unknown",
    "line": 154,
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
   "entity_type": "unsigned char",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
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
   "control_structures": "IF:185,IF:185,IF:185,IF:187,ELSE:190,IF:192",
   "fn": "bit_read_BB",
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
   "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
   "site": {
    "file": "/src/libredwg/src/bits.c",
    "fn": "bit_read_BB",
    "line": 186
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 183,
    "size": null,
    "type": "unsigned char"
   },
   "kind": "struct",
   "name": "byte",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_45e5371477dc.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/45e5371477dc4a07809d97e109a62f3f84d8672e/ARVO-42519042/report.log",
   "testcase_size": 205
  },
  "input_reachability": [
   "dat"
  ],
  "osv_id": "ARVO-42519042",
  "project": "libredwg",
  "sites": [
   {
    "code": "byte = dat->chain[dat->byte] | dat->chain[dat->byte] | dat->chain | dat->byte",
    "fn": "bit_read_BB",
    "kind": "unknown",
    "line": 186,
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
   "entity_type": "unsigned char",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": false,
   "site": {
    "file": "/src/assimp/code/AssetLib/Obj/ObjFileImporter.cpp",
    "fn": "Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)",
    "line": 421
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
   "control_structures": "FOR:418,IF:422,IF:425,FOR:439,IF:443,FOR:449,IF:455,FOR:457,IF:465,FOR:466,ELSE:473,IF:482",
   "fn": "AddNodeToGraph",
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
    "width": 12
   },
   "code": "aiMatrix4x4::RotationZ(AI_DEG_TO_RAD(-pcIn->aCameraRollK | AI_DEG_TO_RAD(-pcIn->aCameraRollKeys[0].mValue) | -pcIn->aCameraRollKeys[0].mValue | pcIn->aCameraRollKeys[0].mValue",
   "site": {
    "file": "/src/assimp/code/AssetLib/Obj/ObjFileImporter.cpp",
    "fn": "Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)",
    "line": 502
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/assimp/code/AssetLib/Obj/ObjFileImporter.cpp",
    "line": 411,
    "size": null,
    "type": "D3DS.Node*"
   },
   "kind": "pointer",
   "name": "pcIn",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_985a5b9667b2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/985a5b9667b25390a00e217ee2086882a101d74a/ARVO-42519068/report.log",
   "testcase_size": 563
  },
  "input_reachability": [
   "pcOut",
   "pcIn"
  ],
  "osv_id": "ARVO-42519068",
  "project": "assimp",
  "sites": [
   {
    "code": "aiMatrix4x4::RotationZ(AI_DEG_TO_RAD(-pcIn->aCameraRollK | AI_DEG_TO_RAD(-pcIn->aCameraRollKeys[0].mValue) | -pcIn->aCameraRollKeys[0].mValue | pcIn->aCameraRollKeys[0].mValue",
    "fn": "Assimp::ObjFileImporter::createVertexArray(Assimp::ObjFile::Model const*, Assimp::ObjFile::Object const*, unsigned int, aiMesh*, unsigned int)",
    "kind": "unknown",
    "line": 502,
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
   "entity_type": "D3DS.Node*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)",
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
   "control_structures": "IF:523,IF:527,IF:529,IF:531,IF:534,IF:536,IF:536,ELSE:542,IF:542,IF:542,IF:545,IF:547",
   "fn": "dwg_add_dat",
   "guard_count": 6,
   "guards": "p < end | ent.type != DWG_TYPE_MTEXT | ent.type != DWG_TYPE_MTEXT",
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
   "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = %d.%d.%X\", &s1[0], & | &s1[0] | s1[0] | &i1",
   "site": {
    "file": "/src/libredwg/src/dwg.spec",
    "fn": "dwg_decode_INSERT_private",
    "line": 699
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/dwg.spec",
    "line": 447,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "p",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_7a44f5e43b2a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/7a44f5e43b2a49bf244e24b796a657c9c78f31a1/ARVO-42519114/report.log",
   "testcase_size": 70
  },
  "free_related": {
   "free_sites_in_func": [
    809,
    820,
    831,
    867,
    879
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "input_reachability": [],
  "osv_id": "ARVO-42519114",
  "project": "libredwg",
  "sites": [
   {
    "code": "sscanf(p, \"mtext.%119[a-zA-Z0-9_] = %d.%d.%X\", &s1[0], & | &s1[0] | s1[0] | &i1",
    "fn": "dwg_decode_INSERT_private",
    "kind": "unknown",
    "line": 699,
    "origin": "report:crash"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 809,
    "origin": "cpg"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 820,
    "origin": "cpg"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 831,
    "origin": "cpg"
   },
   {
    "code": "free (fitpts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 867,
    "origin": "cpg"
   },
   {
    "code": "free (pts)",
    "fn": "dwg_decode_INSERT_private",
    "kind": "free",
    "line": 879,
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
    "file": "/src/assimp/code/AssetLib/MD5/MD5Loader.cpp",
    "fn": "Assimp::MD5Importer::LoadFileIntoMemory(Assimp::IOStream*)",
    "line": 182
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
   "control_structures": "IF:231,FOR:246,FOR:251",
   "fn": "WriteHierarchy",
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
   "code": "chunk(writer, Discreet3DS::CHUNK_TRACKOBJNAME) | Discreet3DS::CHUNK_TRACKOBJNAME",
   "site": {
    "file": "/src/assimp/code/AssetLib/MD5/MD5Parser.cpp",
    "fn": "Assimp::MD5::MD5MeshParser::MD5MeshParser(std::__1::vector<Assimp::MD5::Section, std::__1::allocator<Assimp::MD5::Section> >&)",
    "line": 259
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "writer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_1e2cff638308.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/1e2cff63830847118cd54992b554c6b069ae2e33/ARVO-42519344/report.log",
   "testcase_size": 20947
  },
  "input_reachability": [
   "seq",
   "sibling_level"
  ],
  "osv_id": "ARVO-42519344",
  "project": "assimp",
  "sites": [
   {
    "code": "chunk(writer, Discreet3DS::CHUNK_TRACKOBJNAME) | Discreet3DS::CHUNK_TRACKOBJNAME",
    "fn": "Assimp::MD5::MD5MeshParser::MD5MeshParser(std::__1::vector<Assimp::MD5::Section, std::__1::allocator<Assimp::MD5::Section> >&)",
    "kind": "unknown",
    "line": 259,
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
    "file": "/src/libredwg/src/./header_variables_r11.spec",
    "fn": "json_preR13_header_write_private",
    "line": 145
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
   "fn": "json_cquote",
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
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/libredwg/src/out_json.c",
    "fn": "json_cquote",
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_a8656c2dc58d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/a8656c2dc58d2deb857dad8ab0f8ef07ccba52ca/ARVO-42519555/report.log",
   "testcase_size": 3806
  },
  "input_reachability": [],
  "osv_id": "ARVO-42519555",
  "project": "libredwg",
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
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/cryptofuzz-openssl-api/util.cpp",
    "fn": "cryptofuzz::util::malloc(unsigned long)",
    "line": 551
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
   "fn": null,
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
    "file": null,
    "fn": null,
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_b15bc3d2368d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/b15bc3d2368dc2f990cda0c235711498cc758996/ARVO-42520151/report.log",
   "testcase_size": 160
  },
  "input_reachability": [],
  "osv_id": "ARVO-42520151",
  "project": "wolfssl",
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
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/cryptofuzz-openssl-api/util.cpp",
    "fn": "cryptofuzz::util::malloc(unsigned long)",
    "line": 551
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
   "fn": null,
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
    "width": 1
   },
   "code": null,
   "site": {
    "file": null,
    "fn": null,
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_b15bc3d2368d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/b15bc3d2368dc2f990cda0c235711498cc758996/ARVO-42520165/report.log",
   "testcase_size": 144
  },
  "input_reachability": [],
  "osv_id": "ARVO-42520165",
  "project": "wolfssl",
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