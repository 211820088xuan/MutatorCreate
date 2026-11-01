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
   "control_structures": "IF:588,IF:593,IF:598",
   "fn": "mk_string_copy_substr",
   "guard_count": 1,
   "guards": "pos_init > pos_end",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 30988
   },
   "code": "memcpy(buffer, string + pos_init, bytes) | string + pos_init",
   "site": {
    "file": "/src/fluent-bit/lib/monkey/mk_core/mk_string.c",
    "fn": "mk_string_copy_substr",
    "line": 603
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/lib/monkey/mk_core/mk_string.c",
    "line": 586,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "buffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_8f653c34c0dd.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/8f653c34c0dd46c39e2a5ebf9ff3fe9ec932fc4f/ARVO-42497985/report.log",
   "testcase_size": 13
  },
  "input_reachability": [
   "string",
   "pos_init",
   "pos_end"
  ],
  "osv_id": "ARVO-42497985",
  "project": "fluent-bit",
  "sites": [
   {
    "code": null,
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
    "kind": "free",
    "line": null,
    "origin": "report:freed_by"
   },
   {
    "code": "memcpy(buffer, string + pos_init, bytes) | string + pos_init",
    "fn": "mk_string_copy_substr",
    "kind": "unknown",
    "line": 603,
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
   "fn": "FSE_writeNCount_generic",
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
    "file": "/src/zstd/lib/compress/fse_compress.c",
    "fn": "FSE_writeNCount_generic",
    "line": 270
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
   "cpg": "/root/gyx/mutator_create/cpg_files/zstd_0a96d0006427.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/zstd/address/0a96d0006427e9275d0711b978495da919416ff4/ARVO-42497992/report.log",
   "testcase_size": 493072
  },
  "input_reachability": [],
  "osv_id": "ARVO-42497992",
  "project": "zstd",
  "sites": [
   {
    "code": null,
    "fn": "FSE_writeNCount_generic",
    "kind": "unknown",
    "line": 270,
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
   "control_structures": "IF:767,IF:767,IF:768,IF:769,DO:770,IF:770",
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
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/decompress/zstd_decompress.c",
    "fn": "ZSTD_copyRawBlock",
    "line": 772
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/decompress/zstd_decompress.c",
    "line": 763,
    "size": null,
    "type": "void*"
   },
   "kind": "pointer",
   "name": "dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_38b23d5ab3c6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/38b23d5ab3c67c5528faed5750611f34c3f18f3f/ARVO-42498356/report.log",
   "testcase_size": 11408
  },
  "input_reachability": [
   "dst",
   "dstCapacity",
   "src",
   "srcSize"
  ],
  "osv_id": "ARVO-42498356",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "ZSTD_memcpy(dst, src, srcSize) | memcpy((dst), (src), (srcSize))",
    "fn": "ZSTD_copyRawBlock",
    "kind": "unknown",
    "line": 772,
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
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:207,IF:214,IF:249,IF:258,FOR:272,IF:273",
   "fn": "<global>",
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
   "code": "{HB_TAG ('h','l','i','g'), HB_AAT_LAYOUT_FEATURE_TYPE_LI | HB_TAG ('h','l','i','g') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('l') & 0",
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-color-cpal-table.hh",
    "fn": "OT::CPALV1Tail::serialize(hb_serialize_context_t*, unsigned int, unsigned int, void const*, hb_map_t const*) const",
    "line": 113
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "uint32_t",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_cb5a6b5a27cf.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/cb5a6b5a27cfe616113bafe7f23ad33f1b0d0a1e/ARVO-42498506/report.log",
   "testcase_size": 2116
  },
  "input_reachability": [],
  "osv_id": "ARVO-42498506",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "{HB_TAG ('h','l','i','g'), HB_AAT_LAYOUT_FEATURE_TYPE_LI | HB_TAG ('h','l','i','g') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('l') & 0",
    "fn": "OT::CPALV1Tail::serialize(hb_serialize_context_t*, unsigned int, unsigned int, void const*, hb_map_t const*) const",
    "kind": "unknown",
    "line": 113,
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
    "file": "/src/mruby/src/state.c",
    "fn": "mrb_default_allocf",
    "line": 68
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
   "control_structures": "IF:1118,IF:1121,GOTO:1122,GOTO:1123,FOR:1129,SWITCH:1129,GOTO:1132,GOTO:1137,SWITCH:1141,BREAK:1144,GOTO:1156,GOTO:1159",
   "fn": "mrb_vm_exec",
   "guard_count": 3,
   "guards": "b < MRB_ENV_LEN(e) | b < MRB_ENV_LEN(e) | b == CALL_MAXARGS",
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
   "code": "pool[b].tt | pool[b]",
   "site": {
    "file": "/src/mruby/src/vm.c",
    "fn": "mrb_vm_exec",
    "line": 1141
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/mruby/src/vm.c",
    "line": 1093,
    "size": null,
    "type": "mrb_pool_value*"
   },
   "kind": "pointer",
   "name": "pool",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e60ddc431d24.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e60ddc431d242ede15e8f4d59a1a815fac532dc6/ARVO-42498551/report.log",
   "testcase_size": 56823
  },
  "input_reachability": [],
  "osv_id": "ARVO-42498551",
  "project": "mruby",
  "sites": [
   {
    "code": "pool[b].tt | pool[b]",
    "fn": "mrb_vm_exec",
    "kind": "unknown",
    "line": 1141,
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
   "entity_type": "mrb_pool_value*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/mruby/src/state.c",
    "fn": "mrb_default_allocf",
    "line": 68
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
   "control_structures": "IF:565,IF:569,IF:575",
   "fn": "dispatch",
   "guard_count": 2,
   "guards": "pos0 == JMPLINK_START | newpos == 0",
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
   "code": "newpos = (int16_t)PEEK_S(s->iseq+pos0) | (int16_t)PEEK_S(s->iseq+pos0) | PEEK_S(s->iseq+pos0) | s->iseq+pos0",
   "site": {
    "file": "/src/mruby/mrbgems/mruby-compiler/core/codegen.c",
    "fn": "dispatch",
    "line": 573
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-compiler/core/codegen.c",
    "line": 563,
    "size": null,
    "type": "int16_t"
   },
   "kind": "struct",
   "name": "newpos",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e60ddc431d24.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e60ddc431d242ede15e8f4d59a1a815fac532dc6/ARVO-42498567/report.log",
   "testcase_size": 26226
  },
  "input_reachability": [
   "s",
   "pos0"
  ],
  "osv_id": "ARVO-42498567",
  "project": "mruby",
  "sites": [
   {
    "code": "newpos = (int16_t)PEEK_S(s->iseq+pos0) | (int16_t)PEEK_S(s->iseq+pos0) | PEEK_S(s->iseq+pos0) | s->iseq+pos0",
    "fn": "dispatch",
    "kind": "unknown",
    "line": 573,
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
   "entity_type": "int16_t",
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
    "fn": "g_malloc (/out/fuzzshark_media_type-json+0x2c1d718)",
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
   "fn": "json_string_unescape",
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
    "file": "/src/wireshark/epan/dissectors/packet-json.c",
    "fn": "json_string_unescape",
    "line": 358
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_6dfa2cb0ae4f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wireshark/address/6dfa2cb0ae4f15d171da8cf77f2a6e11d35d0d86/ARVO-42498787/report.log",
   "testcase_size": 3
  },
  "input_reachability": [],
  "osv_id": "ARVO-42498787",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "json_string_unescape",
    "kind": "unknown",
    "line": 358,
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "vips_foreign_load_jxl_build",
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
    "width": 64
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jxlload.c",
    "fn": "vips_foreign_load_jxl_build",
    "line": 156
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42499353/report.log",
   "testcase_size": 2661
  },
  "input_reachability": [],
  "osv_id": "ARVO-42499353",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "vips_foreign_load_jxl_build",
    "kind": "unknown",
    "line": 156,
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
    "file": "/src/mruby/src/state.c",
    "fn": "mrb_default_allocf",
    "line": 68
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
   "control_structures": "IF:1118,IF:1121,GOTO:1122,GOTO:1123,FOR:1129,SWITCH:1129,GOTO:1132,GOTO:1137,SWITCH:1141,BREAK:1144,GOTO:1156,GOTO:1159",
   "fn": "mrb_vm_exec",
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
   "code": "CASE(OP_LOADL, BB) | pc++ | FETCH_BB() | mrb->c->ci->pc = pc",
   "site": {
    "file": "/src/mruby/src/vm.c",
    "fn": "mrb_vm_exec",
    "line": 1140
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "OP_LOADL",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_598c97ef7677.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/598c97ef76771f3b741657ee6807c58b0ca4f393/ARVO-42499386/report.log",
   "testcase_size": 9
  },
  "input_reachability": [],
  "osv_id": "ARVO-42499386",
  "project": "mruby",
  "sites": [
   {
    "code": "CASE(OP_LOADL, BB) | pc++ | FETCH_BB() | mrb->c->ci->pc = pc",
    "fn": "mrb_vm_exec",
    "kind": "unknown",
    "line": 1140,
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
    "line": 85
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
   "control_structures": "FOR:563,FOR:583,WHILE:603,IF:634,FOR:635,FOR:637,FOR:640",
   "fn": "ConvolveRow",
   "guard_count": 1,
   "guards": "dy <= kRadius",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 4
   },
   "code": "wy = weights.vert[std::abs(dy) * 4] | weights.vert[std::abs(dy) * 4] | weights.vert | std::abs(dy) * 4",
   "site": {
    "file": "/src/libjxl/third_party/highway/hwy/base.h",
    "fn": "CopyBytes<4, float, float>",
    "line": 638
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libjxl/third_party/highway/hwy/base.h",
    "line": 638,
    "size": null,
    "type": "float"
   },
   "kind": "struct",
   "name": "wy",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libjxl_08973db8ae2e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libjxl/address/08973db8ae2e4f19bf57afa85089e705c50a572b/ARVO-42499415/report.log",
   "testcase_size": 102
  },
  "input_reachability": [
   "row_m",
   "xsize",
   "stride",
   "weights",
   "row_out"
  ],
  "osv_id": "ARVO-42499415",
  "project": "libjxl",
  "sites": [
   {
    "code": "wy = weights.vert[std::abs(dy) * 4] | weights.vert[std::abs(dy) * 4] | weights.vert | std::abs(dy) * 4",
    "fn": "CopyBytes<4, float, float>",
    "kind": "unknown",
    "line": 638,
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
   "entity_type": "float",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libjxl/lib/jxl/base/cache_aligned.cc",
    "fn": "jxl::CacheAligned::Allocate(unsigned long, unsigned long)",
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "vips_foreign_load_jxl_build",
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
    "width": 64
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jxlload.c",
    "fn": "vips_foreign_load_jxl_build",
    "line": 156
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42499474/report.log",
   "testcase_size": 2036
  },
  "input_reachability": [],
  "osv_id": "ARVO-42499474",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "vips_foreign_load_jxl_build",
    "kind": "unknown",
    "line": 156,
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
   "control_structures": "IF:396,IF:401,IF:405,ELSE:409,IF:412,BREAK:413,IF:419",
   "fn": "flb_hash_get_by_id",
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
    "width": 593
   },
   "code": "strcmp(entry->key, key) == 0 | strcmp(entry->key, key) | entry->key",
   "site": {
    "file": "/src/fluent-bit/src/flb_hash.c",
    "fn": "flb_hash_get_by_id",
    "line": 412
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/src/flb_hash.c",
    "line": 393,
    "size": null,
    "type": "flb_hash_entry*"
   },
   "kind": "pointer",
   "name": "entry",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9da96a3b8885.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9da96a3b88859ae57134c6932cab65101114e3b4/ARVO-42499668/report.log",
   "testcase_size": 601
  },
  "input_reachability": [
   "key"
  ],
  "osv_id": "ARVO-42499668",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "strcmp(entry->key, key) == 0 | strcmp(entry->key, key) | entry->key",
    "fn": "flb_hash_get_by_id",
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
   "entity_type": "flb_hash_entry*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": false,
   "site": {
    "file": "/src/net-snmp/snmplib/read_config.c",
    "fn": "read_config",
    "line": 803
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
   "fn": "read_config",
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
    "file": "/src/net-snmp/snmplib/read_config.c",
    "fn": "read_config",
    "line": 823
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
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_7b39d280f81a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/7b39d280f81af4513382c3cf4ba09458ab57e6c6/ARVO-42499879/report.log",
   "testcase_size": 1
  },
  "input_reachability": [],
  "osv_id": "ARVO-42499879",
  "project": "net-snmp",
  "sites": [
   {
    "code": null,
    "fn": "read_config",
    "kind": "unknown",
    "line": 823,
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
    "file": "/src/hdf5-1.12.1/src/H5MM.c",
    "fn": "H5MM_malloc",
    "line": 313
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
   "fn": "Mat_Open",
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
   "code": "",
   "site": {
    "file": "/src/matio/src/mat.c",
    "fn": "Mat_Open",
    "line": 590
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
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_2945c0ded5ed.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/2945c0ded5ede79eae3cba3a5d12450ba2917fbc/ARVO-42500334/report.log",
   "testcase_size": 18198
  },
  "input_reachability": [],
  "osv_id": "ARVO-42500334",
  "project": "matio",
  "sites": [
   {
    "code": "",
    "fn": "Mat_Open",
    "kind": "unknown",
    "line": 590,
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
   "control_structures": "WHILE:195,IF:215,GOTO:216,IF:217,IF:218,ELSE:222,IF:226,IF:228,ELSE:231,ELSE:233,IF:240,SWITCH:242",
   "fn": "_hb_buffer_deserialize_text",
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
   "code": "unlikely (!buffer->ensure_glyphs ()) | !buffer->ensure_glyphs() | buffer->ensure_glyphs() | buffer->ensure_glyphs",
   "site": {
    "file": "/src/harfbuzz/src/hb-array.hh",
    "fn": "hb_array_t<OT::IntType<unsigned int, 4u> const> hb_array_t<OT::IntType<unsigned int, 4u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "line": 271
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-array.hh",
    "line": 184,
    "size": null,
    "type": "hb_buffer_t*"
   },
   "kind": "pointer",
   "name": "buffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_b235511ed88e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/b235511ed88e46d97d27a9176da1931f4a701b0d/ARVO-42500367/report.log",
   "testcase_size": 567
  },
  "input_reachability": [
   "buffer"
  ],
  "osv_id": "ARVO-42500367",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "unlikely (!buffer->ensure_glyphs ()) | !buffer->ensure_glyphs() | buffer->ensure_glyphs() | buffer->ensure_glyphs",
    "fn": "hb_array_t<OT::IntType<unsigned int, 4u> const> hb_array_t<OT::IntType<unsigned int, 4u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "kind": "unknown",
    "line": 271,
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
   "entity_type": "hb_buffer_t*",
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