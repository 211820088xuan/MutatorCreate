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
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/c-blosc2/blosc/schunk.c",
    "fn": "blosc2_schunk_append_buffer",
    "line": 1024
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
   "control_structures": "IF:127,ELSE:130",
   "fn": "_sw32",
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
   "code": "*(int32_t *)dest_ = a | *(int32_t *)dest_ | (int32_t *)dest_",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "fn": "_sw32",
    "line": 128
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": 123,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "dest_",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_69f841768ac2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/69f841768ac2c98f6d0ac4c15ab162055871e95b/ARVO-42514900/report.log",
   "testcase_size": 2
  },
  "input_reachability": [
   "dest",
   "a"
  ],
  "osv_id": "ARVO-42514900",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "*(int32_t *)dest_ = a | *(int32_t *)dest_ | (int32_t *)dest_",
    "fn": "_sw32",
    "kind": "unknown",
    "line": 128,
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "Exiv2::MemIo::read(unsigned char*, unsigned long)",
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
    "width": 24
   },
   "code": null,
   "site": {
    "file": "/src/exiv2/src/basicio.cpp",
    "fn": "Exiv2::MemIo::read(unsigned char*, unsigned long)",
    "line": 822
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
   "cpg": "/root/gyx/mutator_create/cpg_files/exiv2_e4adf388aaac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/exiv2/address/e4adf388aaaccccaf08fc0fc38419a5b0117b299/ARVO-42515419/report.log",
   "testcase_size": 80
  },
  "input_reachability": [],
  "osv_id": "ARVO-42515419",
  "project": "exiv2",
  "sites": [
   {
    "code": null,
    "fn": "Exiv2::MemIo::read(unsigned char*, unsigned long)",
    "kind": "unknown",
    "line": 822,
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
    "file": "/src/libjxl/lib/jxl/base/cache_aligned.cc",
    "fn": "jxl::CacheAligned::Allocate(unsigned long, unsigned long)",
    "line": 87
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
   "control_structures": "IF:169,IF:173,IF:180,IF:185,IF:192",
   "fn": "LoadFile",
   "guard_count": 2,
   "guards": "size >= LONG_MAX | size < 0",
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
   "code": "out->resize(size)",
   "site": {
    "file": "/src/libjxl/lib/jxl/render_pipeline/stage_blending.cc",
    "fn": "jxl::N_AVX3::BlendingStage::ProcessPaddingRow(std::__1::vector<std::__1::vector<float*, std::__1::allocator<float*> >, std::__1::allocator<std::__1::vector<float*, std::__1::allocator<float*> > > > const&, unsigned long, unsigned long, unsigned long) const",
    "line": 190
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libjxl/lib/jxl/render_pipeline/stage_blending.cc",
    "line": 167,
    "size": null,
    "type": "std.vector<uint8_t>*"
   },
   "kind": "pointer",
   "name": "out",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_ca8e276aacf6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/ca8e276aacf63a752346a6a44ba673b0af993237/ARVO-42515434/report.log",
   "testcase_size": 52
  },
  "input_reachability": [
   "filename",
   "out"
  ],
  "osv_id": "ARVO-42515434",
  "project": "libjxl",
  "sites": [
   {
    "code": "out->resize(size)",
    "fn": "jxl::N_AVX3::BlendingStage::ProcessPaddingRow(std::__1::vector<std::__1::vector<float*, std::__1::allocator<float*> >, std::__1::allocator<std::__1::vector<float*, std::__1::allocator<float*> > > > const&, unsigned long, unsigned long, unsigned long) const",
    "kind": "unknown",
    "line": 190,
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
   "entity_type": "std.vector<uint8_t>*",
   "is_signed": null,
   "ptr_origin": "param"
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
    "width": 3324313568
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/6b40381b5b09a9bda0ee0634b398fd2f46616744/ARVO-42515518/report.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "ARVO-42515518",
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
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "g_malloc (/out/fuzzshark_ip_proto-udp+0x2c50da8)",
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
   "fn": "get_utf_8_string",
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
    "file": "/src/wireshark/epan/charsets.c",
    "fn": "get_utf_8_string",
    "line": 118
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_2dfbed7a5fe4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wireshark/address/2dfbed7a5fe42dd37d025b3298391a8114e71039/ARVO-42515629/report.log",
   "testcase_size": 15
  },
  "input_reachability": [],
  "osv_id": "ARVO-42515629",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "get_utf_8_string",
    "kind": "unknown",
    "line": 118,
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
    "fn": "__getdelim (/lib/x86_64-linux-gnu/libc.so.6+0x83543) (BuildId: 0323ab4806bee6f846d9ad4bccfc29afdca49a58)",
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
   "control_structures": "IF:253",
   "fn": "file_magwarn",
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
    "width": 109
   },
   "code": "(void) vfprintf(stderr, f, va) | vfprintf(stderr, f, va)",
   "site": {
    "file": "/src/file/src/print.c",
    "fn": "file_magwarn",
    "line": 258
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "stderr",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/file_5f957469b734.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/5f957469b734366c8d4cbd050609ba4cc3a5c47c/ARVO-42516199/report.log",
   "testcase_size": 13
  },
  "input_reachability": [
   "ms",
   "f"
  ],
  "osv_id": "ARVO-42516199",
  "project": "file",
  "sites": [
   {
    "code": "(void) vfprintf(stderr, f, va) | vfprintf(stderr, f, va)",
    "fn": "file_magwarn",
    "kind": "unknown",
    "line": 258,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 0323ab4806bee6f846d9ad4bccfc29afdca49a58)",
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
   "control_structures": "IF:556,IF:560,GOTO:562,IF:569,GOTO:570,FOR:574",
   "fn": "file_ms_alloc",
   "guard_count": 2,
   "guards": "(ms = CAST(struct magic_set *, calloc(CAST(size_t, 1u),",
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
   "code": "ms->o.buf = ms->o.pbuf = NULL | ms->o.buf | ms->o | ms->o.pbuf = NULL",
   "site": {
    "file": "/src/file/src/compress.c",
    "fn": "uncompressgzipped",
    "line": 565
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/file/src/compress.c",
    "line": 553,
    "size": null,
    "type": "magic_set*"
   },
   "kind": "pointer",
   "name": "ms",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/file_5f957469b734.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/5f957469b734366c8d4cbd050609ba4cc3a5c47c/ARVO-42516204/report.log",
   "testcase_size": 2
  },
  "input_reachability": [],
  "osv_id": "ARVO-42516204",
  "project": "file",
  "sites": [
   {
    "code": "calloc(((size_t)(1u)), sizeof (magic_set))",
    "fn": "uncompressgzipped",
    "kind": "calloc",
    "line": 556,
    "origin": "cpg"
   },
   {
    "code": "ms->o.buf = ms->o.pbuf = NULL | ms->o.buf | ms->o | ms->o.pbuf = NULL",
    "fn": "uncompressgzipped",
    "kind": "unknown",
    "line": 565,
    "origin": "report:crash"
   },
   {
    "code": "malloc(len)",
    "fn": "uncompressgzipped",
    "kind": "malloc",
    "line": 569,
    "origin": "cpg"
   },
   {
    "code": "free(ms)",
    "fn": "uncompressgzipped",
    "kind": "free",
    "line": 592,
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
   "entity_type": "magic_set*",
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "Exiv2::MemIo::read(unsigned char*, unsigned long)",
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
    "width": 112
   },
   "code": null,
   "site": {
    "file": "/src/exiv2/src/basicio.cpp",
    "fn": "Exiv2::MemIo::read(unsigned char*, unsigned long)",
    "line": 822
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
   "cpg": "/root/gyx/mutator_create/cpg_files/exiv2_e4adf388aaac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/exiv2/address/e4adf388aaaccccaf08fc0fc38419a5b0117b299/ARVO-42516314/report.log",
   "testcase_size": 159
  },
  "input_reachability": [],
  "osv_id": "ARVO-42516314",
  "project": "exiv2",
  "sites": [
   {
    "code": null,
    "fn": "Exiv2::MemIo::read(unsigned char*, unsigned long)",
    "kind": "unknown",
    "line": 822,
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
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "fn": "flb_malloc",
    "line": 79
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
   "fn": "onig_vsnprintf_with_pattern",
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
    "file": "/src/fluent-bit/lib/onigmo/regerror.c",
    "fn": "onig_vsnprintf_with_pattern",
    "line": 350
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
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_6016eb575e93.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/6016eb575e9309965f793ab69ec50604cf47e962/ARVO-42516566/report.log",
   "testcase_size": 71
  },
  "input_reachability": [],
  "osv_id": "ARVO-42516566",
  "project": "fluent-bit",
  "sites": [
   {
    "code": null,
    "fn": "onig_vsnprintf_with_pattern",
    "kind": "unknown",
    "line": 350,
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
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 102
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
   "control_structures": "IF:353,IF:359,IF:364,IF:366,IF:368,IF:369,ELSE:372,IF:372,ELSE:374,FOR:378,IF:379,IF:381",
   "fn": "ndpi_search_irc_tcp",
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
    "width": 9
   },
   "code": "snprintf(buf, sizeof(buf), \"%s\", &user[5]) | sizeof(buf) | &user[5] | user[5]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/irc.c",
    "fn": "ndpi_search_irc_tcp",
    "line": 411
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/irc.c",
    "line": 409,
    "size": null,
    "type": "char[32]"
   },
   "kind": "array",
   "name": "buf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_fba926d6a441.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/fba926d6a441396baf65e7ff29cfbf76eff4d8df/ARVO-42516833/report.log",
   "testcase_size": 97
  },
  "input_reachability": [
   "ndpi_struct"
  ],
  "osv_id": "ARVO-42516833",
  "project": "ndpi",
  "sites": [
   {
    "code": "snprintf(buf, sizeof(buf), \"%s\", &user[5]) | sizeof(buf) | &user[5] | user[5]",
    "fn": "ndpi_search_irc_tcp",
    "kind": "unknown",
    "line": 411,
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
   "entity_type": "char[32]",
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
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "onigenc_unicode_mbc_case_fold",
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
    "file": "/src/fluent-bit/lib/onigmo/enc/unicode.c",
    "fn": "onigenc_unicode_mbc_case_fold",
    "line": 312
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
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_6016eb575e93.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/6016eb575e9309965f793ab69ec50604cf47e962/ARVO-42517007/report.log",
   "testcase_size": 3704
  },
  "input_reachability": [],
  "osv_id": "ARVO-42517007",
  "project": "fluent-bit",
  "sites": [
   {
    "code": null,
    "fn": "onigenc_unicode_mbc_case_fold",
    "kind": "unknown",
    "line": 312,
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
   "control_structures": "IF:353,IF:359,IF:364,IF:366,IF:368,IF:369,ELSE:372,IF:372,ELSE:374,FOR:378,IF:379,IF:381",
   "fn": "ndpi_search_irc_tcp",
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
    "width": 15
   },
   "code": "snprintf(buf, sizeof(buf), \"%s\", &user[5]) | sizeof(buf) | &user[5] | user[5]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/irc.c",
    "fn": "ndpi_search_irc_tcp",
    "line": 411
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/irc.c",
    "line": 409,
    "size": null,
    "type": "char[32]"
   },
   "kind": "array",
   "name": "buf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_fba926d6a441.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/fba926d6a441396baf65e7ff29cfbf76eff4d8df/ARVO-42517122/report.log",
   "testcase_size": 64
  },
  "input_reachability": [
   "ndpi_struct"
  ],
  "osv_id": "ARVO-42517122",
  "project": "ndpi",
  "sites": [
   {
    "code": "snprintf(buf, sizeof(buf), \"%s\", &user[5]) | sizeof(buf) | &user[5] | user[5]",
    "fn": "ndpi_search_irc_tcp",
    "kind": "unknown",
    "line": 411,
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
   "entity_type": "char[32]",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/net-snmp/testing/fuzzing/ada_fuzz_header.h",
    "fn": "af_get_null_terminated",
    "line": 67
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
   "control_structures": "IF:1221",
   "fn": "asn_build_header",
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
    "width": 1
   },
   "code": "*data++ = type | *data++ | data++",
   "site": {
    "file": "/src/net-snmp/snmplib/asn1.c",
    "fn": "asn_build_header",
    "line": 1229
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/net-snmp/snmplib/asn1.c",
    "line": 1216,
    "size": null,
    "type": "u_char*"
   },
   "kind": "pointer",
   "name": "data",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_763e9cd5c005.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/763e9cd5c005c95729c89085a854f159e88da32c/ARVO-42517155/report.log",
   "testcase_size": 112
  },
  "input_reachability": [
   "data",
   "type",
   "length"
  ],
  "osv_id": "ARVO-42517155",
  "project": "net-snmp",
  "sites": [
   {
    "code": "*data++ = type | *data++ | data++",
    "fn": "asn_build_header",
    "kind": "unknown",
    "line": 1229,
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
   "entity_type": "u_char*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "g_malloc (/out/fuzzshark_ip+0x2c975c8)",
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
   "fn": "_strbuf_vsnprintf",
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
    "width": 241
   },
   "code": null,
   "site": {
    "file": "/src/wireshark/wsutil/wmem/wmem_strbuf.c",
    "fn": "_strbuf_vsnprintf",
    "line": 173
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_f1ddda51d434.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wireshark/address/f1ddda51d434c37da7cb9c091c537455891c9222/ARVO-42517523/report.log",
   "testcase_size": 715
  },
  "input_reachability": [],
  "osv_id": "ARVO-42517523",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "_strbuf_vsnprintf",
    "kind": "unknown",
    "line": 173,
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
    "file": null,
    "fn": "g_malloc (/out/fuzzshark_ip+0x2c975c8)",
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
   "fn": "expert_set_info_vformat",
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
    "width": 241
   },
   "code": null,
   "site": {
    "file": "/src/wireshark/epan/expert.c",
    "fn": "expert_set_info_vformat",
    "line": 568
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_f1ddda51d434.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wireshark/address/f1ddda51d434c37da7cb9c091c537455891c9222/ARVO-42517543/report.log",
   "testcase_size": 100
  },
  "input_reachability": [],
  "osv_id": "ARVO-42517543",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "expert_set_info_vformat",
    "kind": "unknown",
    "line": 568,
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