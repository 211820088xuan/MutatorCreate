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
heap-use-after-free

## 该类型的机制背景
UAF 的必要条件链：
- N1 对象是堆分配
- N2 存在 free(p) 调用
- N3 p 在 free 之后被解引用（执行顺序）
- N4 free 与解引用之间 p 未被重新赋值
- N5 free 与解引用之间 p 未重新 malloc
- N6 free 的实参是 p 本身（非 p+off）
- N7 解引用对象与 free 对象是同一对象（含别名）
- N8 free 与解引用在同一可达路径上
- N9 p 解引用时未被置空
- N10 解引用发生在 free 生效后（非同一语句）

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/open62541/src/ua_types_encoding_binary.c",
    "fn": "Array_decodeBinary",
    "line": 551
   },
   "size_bytes": 2,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1019,IF:1020,ELSE:1023,IF:1027,IF:1032,IF:1035,FOR:1043,IF:1048",
   "fn": "UA_Array_copy",
   "guard_count": 3,
   "guards": "size == 0 | src == NULL | i < size",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 2,
    "width": 2
   },
   "code": "memcpy(*dst, src, type->memSize * size) | *dst | type->memSize * size | type->memSize",
   "site": {
    "file": "/src/open62541/src/ua_types.c",
    "fn": "UA_Array_copy",
    "line": 1036
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 1018,
    "size": null,
    "type": "void**"
   },
   "kind": "pointer",
   "name": "dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_b916bd061121.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/b916bd061121852f7025f3610ae0074f8d597f7f/ARVO-42507154/report.log",
   "testcase_size": 21
  },
  "input_reachability": [
   "src",
   "size",
   "dst",
   "type"
  ],
  "osv_id": "ARVO-42507154",
  "project": "open62541",
  "sites": [
   {
    "code": null,
    "fn": "deleteMembers_noInit",
    "kind": "free",
    "line": 979,
    "origin": "report:freed_by"
   },
   {
    "code": "memcpy(*dst, src, type->memSize * size) | *dst | type->memSize * size | type->memSize",
    "fn": "UA_Array_copy",
    "kind": "unknown",
    "line": 1036,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "void**",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "fn": "hb_malloc_impl",
    "line": 45
   },
   "size_bytes": 704,
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
   "fn": "next",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 704,
    "width": 1
   },
   "code": "",
   "site": {
    "file": "/src/harfbuzz/src/hb-bit-set-invertible.hh",
    "fn": "next",
    "line": 242
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_bc899650c797.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/harfbuzz/address/bc899650c7976df7bc62ed55da5268f1d10b9a43/ARVO-42507972/report.log",
   "testcase_size": 1700
  },
  "input_reachability": [],
  "osv_id": "ARVO-42507972",
  "project": "harfbuzz",
  "sites": [
   {
    "code": null,
    "fn": "hb_free_impl",
    "kind": "free",
    "line": 60,
    "origin": "report:freed_by"
   },
   {
    "code": "",
    "fn": "next",
    "kind": "unknown",
    "line": 242,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "fn": "hb_malloc_impl",
    "line": 45
   },
   "size_bytes": 512,
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
   "fn": "as_array",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 512,
    "width": 4
   },
   "code": "",
   "site": {
    "file": "/src/harfbuzz/src/hb-vector.hh",
    "fn": "as_array",
    "line": 153
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_bc899650c797.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/harfbuzz/address/bc899650c7976df7bc62ed55da5268f1d10b9a43/ARVO-42508038/report.log",
   "testcase_size": 2288
  },
  "input_reachability": [],
  "osv_id": "ARVO-42508038",
  "project": "harfbuzz",
  "sites": [
   {
    "code": null,
    "fn": "hb_free_impl",
    "kind": "free",
    "line": 60,
    "origin": "report:freed_by"
   },
   {
    "code": "",
    "fn": "as_array",
    "kind": "unknown",
    "line": 153,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "fn": "hb_malloc_impl",
    "line": 45
   },
   "size_bytes": 704,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "FOR:216,IF:221,ELSE:224,DO:228,IF:232,IF:238,IF:242,ELSE:250",
   "fn": "_hb_buffer_serialize_unicode_json",
   "guard_count": 1,
   "guards": "buf_size > l",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 704,
    "width": 1
   },
   "code": "buf_size > l",
   "site": {
    "file": "/src/harfbuzz/src/hb-bit-set-invertible.hh",
    "fn": "hb_bit_set_invertible_t::next(unsigned int*) const",
    "line": 242
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-bit-set-invertible.hh",
    "line": 209,
    "size": null,
    "type": "unsigned int"
   },
   "kind": "struct",
   "name": "buf_size",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_bc899650c797.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/harfbuzz/address/bc899650c7976df7bc62ed55da5268f1d10b9a43/ARVO-42508045/report.log",
   "testcase_size": 526225
  },
  "input_reachability": [
   "buf",
   "buf_size"
  ],
  "osv_id": "ARVO-42508045",
  "project": "harfbuzz",
  "sites": [
   {
    "code": null,
    "fn": "hb_free_impl",
    "kind": "free",
    "line": 60,
    "origin": "report:freed_by"
   },
   {
    "code": "buf_size > l",
    "fn": "hb_bit_set_invertible_t::next(unsigned int*) const",
    "kind": "unknown",
    "line": 242,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "unsigned int",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/src/curl/lib/memdebug.c",
    "fn": "curl_dbg_realloc",
    "line": 260
   },
   "size_bytes": 76,
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
   "fn": "h2_session_send",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 76,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/curl/lib/http2.c",
    "fn": "h2_session_send",
    "line": 1612
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_5c55fe6df605.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/curl/address/5c55fe6df605b822bb637bdf0cf05b6812dcd732/ARVO-42508326/report.log",
   "testcase_size": 342
  },
  "input_reachability": [],
  "osv_id": "ARVO-42508326",
  "project": "curl",
  "sites": [
   {
    "code": null,
    "fn": "curl_dbg_free",
    "kind": "free",
    "line": 292,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "h2_session_send",
    "kind": "unknown",
    "line": 1612,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "line": 129
   },
   "size_bytes": 8200,
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
   "fn": "cb_stdout_flush",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 8200,
    "width": 24
   },
   "code": null,
   "site": {
    "file": "/src/fluent-bit/plugins/out_stdout/stdout.c",
    "fn": "cb_stdout_flush",
    "line": 179
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_8e310e6586ed.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/fluent-bit/address/8e310e6586ed66d1ac4e6880b2c89d2180b38916/ARVO-42509881/report.log",
   "testcase_size": 218
  },
  "input_reachability": [],
  "osv_id": "ARVO-42509881",
  "project": "fluent-bit",
  "sites": [
   {
    "code": null,
    "fn": "__interceptor_free",
    "kind": "free",
    "line": 111,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "cb_stdout_flush",
    "kind": "unknown",
    "line": 179,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libxml2/tree.c",
    "fn": "xmlStaticCopyNode",
    "line": 4247
   },
   "size_bytes": 120,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:3697,IF:3698,IF:3702,WHILE:3703,WHILE:3704,IF:3715,ELSE:3718,IF:3718,IF:3720,IF:3723,IF:3728,IF:3733",
   "fn": "xmlFreeNodeList",
   "guard_count": 8,
   "guards": "cur == NULL | cur->doc != NULL | cur->children != NULL",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 120,
    "width": 8
   },
   "code": "(cur->children != NULL) &&",
   "site": {
    "file": "/src/libxml2/tree.c",
    "fn": "xmlFreeNodeList",
    "line": 3704
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/tree.c",
    "line": 3691,
    "size": null,
    "type": "xmlNodePtr"
   },
   "kind": "struct",
   "name": "cur",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_f0ba4da18c17.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/f0ba4da18c17d3f1dd73007ce0888c978319e6f1/ARVO-42510333/report.log",
   "testcase_size": 233
  },
  "input_reachability": [
   "cur"
  ],
  "osv_id": "ARVO-42510333",
  "project": "libxml2",
  "sites": [
   {
    "code": "(cur->children != NULL) &&",
    "fn": "xmlFreeNodeList",
    "kind": "unknown",
    "line": 3704,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "xmlFreeNodeList",
    "kind": "free",
    "line": 3751,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "xmlNodePtr",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "fn": "alloc_small",
    "line": 312
   },
   "size_bytes": 16247,
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
   "fn": "read_jpeg_image",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 16247,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "fn": "read_jpeg_image",
    "line": 875
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510346/report.log",
   "testcase_size": 2048
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510346",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "read_jpeg_image",
    "kind": "unknown",
    "line": 875,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "free_pool",
    "kind": "free",
    "line": 1043,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "fn": "alloc_small",
    "line": 312
   },
   "size_bytes": 16343,
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
   "fn": "read_jpeg_image",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 16343,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "fn": "read_jpeg_image",
    "line": 875
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510349/report.log",
   "testcase_size": 161
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510349",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "read_jpeg_image",
    "kind": "unknown",
    "line": 875,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "free_pool",
    "kind": "free",
    "line": 1043,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "fn": "alloc_small",
    "line": 312
   },
   "size_bytes": 16343,
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
   "fn": "read_jpeg_image",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 16343,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "fn": "read_jpeg_image",
    "line": 875
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510355/report.log",
   "testcase_size": 1061
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510355",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "read_jpeg_image",
    "kind": "unknown",
    "line": 875,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "free_pool",
    "kind": "free",
    "line": 1043,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "fn": "alloc_small",
    "line": 312
   },
   "size_bytes": 16151,
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
   "fn": "read_jpeg_generate",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 16151,
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "fn": "read_jpeg_generate",
    "line": 833
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510367/report.log",
   "testcase_size": 495
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510367",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "read_jpeg_generate",
    "kind": "unknown",
    "line": 833,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "free_pool",
    "kind": "free",
    "line": 1043,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/libjpeg-turbo/jmemmgr.c",
    "fn": "alloc_large",
    "line": 385
   },
   "size_bytes": 65591,
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
   "fn": "read_jpeg_header",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 65591,
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jpeg2vips.c",
    "fn": "read_jpeg_header",
    "line": 500
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42510442/report.log",
   "testcase_size": 4
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510442",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "read_jpeg_header",
    "kind": "unknown",
    "line": 500,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "free_pool",
    "kind": "free",
    "line": 1030,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/mruby/src/state.c",
    "fn": "mrb_default_allocf",
    "line": 69
   },
   "size_bytes": 1024,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "fn": "stack_copy",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 1024,
    "width": 8
   },
   "code": "memcpy(dst, src, sizeof(mrb_value)*size) | sizeof(mrb_value)*size | sizeof(mrb_value)",
   "site": {
    "file": "/src/mruby/src/vm.c",
    "fn": "stack_copy",
    "line": 101
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/mruby/src/vm.c",
    "line": 99,
    "size": null,
    "type": "mrb_value*"
   },
   "kind": "pointer",
   "name": "dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_23ce122fc2b1.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/mruby/address/23ce122fc2b1d29ee7241813bbab1c7e150e23ae/ARVO-42511322/report.log",
   "testcase_size": 7270
  },
  "input_reachability": [
   "dst",
   "src",
   "size"
  ],
  "osv_id": "ARVO-42511322",
  "project": "mruby",
  "sites": [
   {
    "code": null,
    "fn": "mrb_default_allocf",
    "kind": "free",
    "line": 69,
    "origin": "report:freed_by"
   },
   {
    "code": "memcpy(dst, src, sizeof(mrb_value)*size) | sizeof(mrb_value)*size | sizeof(mrb_value)",
    "fn": "stack_copy",
    "kind": "unknown",
    "line": 101,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "mrb_value*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/open62541/src/ua_types.c",
    "fn": "UA_ByteString_allocBuffer",
    "line": 187
   },
   "size_bytes": 65535,
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
   "fn": "UInt32_encodeBinary",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 65535,
    "width": 4
   },
   "code": "",
   "site": {
    "file": "/src/open62541/src/ua_types_encoding_binary.c",
    "fn": "UInt32_encodeBinary",
    "line": 236
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_92b1758a64c8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/92b1758a64c8adf945dd8a2306cf2d139963fb95/ARVO-42511795/report.log",
   "testcase_size": 326
  },
  "input_reachability": [],
  "osv_id": "ARVO-42511795",
  "project": "open62541",
  "sites": [
   {
    "code": "",
    "fn": "UInt32_encodeBinary",
    "kind": "unknown",
    "line": 236,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "UA_Array_delete",
    "kind": "free",
    "line": 1064,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/lcms/src/cmserr.c",
    "fn": "_cmsMallocDefaultFn",
    "line": 97
   },
   "size_bytes": 88,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:576,IF:577",
   "fn": "cmsFreeNamedColorList",
   "guard_count": 1,
   "guards": "v == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 88,
    "width": 4
   },
   "code": "v ->List | _cmsFree(v ->ContextID, v ->List) | v ->ContextID | v ->List",
   "site": {
    "file": "/src/lcms/src/cmsnamed.c",
    "fn": "cmsFreeNamedColorList",
    "line": 577
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/lcms/src/cmsnamed.c",
    "line": 574,
    "size": null,
    "type": "cmsNAMEDCOLORLIST*"
   },
   "kind": "pointer",
   "name": "v",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_a9796f61c682.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/lcms/address/a9796f61c682f5320ff572c888062ee34315b836/ARVO-42513913/report.log",
   "testcase_size": 448
  },
  "input_reachability": [
   "v"
  ],
  "osv_id": "ARVO-42513913",
  "project": "lcms",
  "sites": [
   {
    "code": null,
    "fn": "_cmsFreeDefaultFn",
    "kind": "free",
    "line": 121,
    "origin": "report:freed_by"
   },
   {
    "code": "v ->List | _cmsFree(v ->ContextID, v ->List) | v ->ContextID | v ->List",
    "fn": "cmsFreeNamedColorList",
    "kind": "unknown",
    "line": 577,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "cmsNAMEDCOLORLIST*",
   "is_signed": null,
   "ptr_origin": "param"
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