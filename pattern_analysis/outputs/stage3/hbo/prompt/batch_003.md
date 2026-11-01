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
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "init_unpack",
    "line": 1834
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
   "control_structures": "WHILE:2378,IF:2379,BREAK:2386,IF:2389,BREAK:2396,IF:2400,IF:2418,CONTINUE:2425,ELSE:2426,IF:2426,IF:2432,IF:2439",
   "fn": "do_uncompress_block",
   "guard_count": 5,
   "guards": "num < 256 | num >= 262 | num == 256",
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
   "code": "rar->cstate.window_buf[write_idx & cmask] = (uint8_t) nu | rar->cstate.window_buf[write_idx & cmask] | rar->cstate.window_buf | rar->cstate",
   "site": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "do_uncompress_block",
    "line": 2424
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 2370,
    "size": null,
    "type": "rar5*"
   },
   "kind": "pointer",
   "name": "rar",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_d5f35a90a4cb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/d5f35a90a4cb1eeb918213bff9d78e8b0471dc0a/ARVO-42471116/report.log",
   "testcase_size": 109
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471116",
  "project": "libarchive",
  "sites": [
   {
    "code": "rar->cstate.window_buf[write_idx & cmask] = (uint8_t) nu | rar->cstate.window_buf[write_idx & cmask] | rar->cstate.window_buf | rar->cstate",
    "fn": "do_uncompress_block",
    "kind": "unknown",
    "line": 2424,
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
   "entity_type": "rar5*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/harfbuzz/src/./hb-vector.hh",
    "fn": "hb_vector_t<char, 8u>::alloc(unsigned int)",
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
   "control_structures": "FOR:650,WHILE:653,IF:657,BREAK:658,IF:660,CONTINUE:661,WHILE:664,IF:667,CONTINUE:668,WHILE:695",
   "fn": "reorder_marks_arabic",
   "guard_count": 5,
   "guards": "cc <= 230 | info_cc(info[i]) < cc | info_cc(info[i]) > cc",
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
   "code": "cc = 220 | cc <= 230 | cc += 10",
   "site": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "fn": "BEInt<unsigned short, 2>::set(unsigned short)",
    "line": 650
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 650,
    "size": null,
    "type": "unsigned int"
   },
   "kind": "struct",
   "name": "cc",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_fda994e1d45c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/fda994e1d45c4d34601af7272f37ea257f92a3d8/ARVO-42471192/report.log",
   "testcase_size": 880
  },
  "input_reachability": [
   "buffer",
   "start",
   "end"
  ],
  "osv_id": "ARVO-42471192",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "cc = 220 | cc <= 230 | cc += 10",
    "fn": "BEInt<unsigned short, 2>::set(unsigned short)",
    "kind": "unknown",
    "line": 650,
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
   "entity_type": "unsigned int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libfuzzer/afl/afl_driver.cpp",
    "fn": "main",
    "line": 339
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
   "fn": "parse_odp_key_mask_attr",
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
    "file": "/src/openvswitch/lib/odp-util.c",
    "fn": "parse_odp_key_mask_attr",
    "line": 5451
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_b47e7e2bac7f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/b47e7e2bac7f21f8c81aaeb1068598a6064c348b/ARVO-42471280/report.log",
   "testcase_size": 19
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471280",
  "project": "openvswitch",
  "sites": [
   {
    "code": null,
    "fn": "parse_odp_key_mask_attr",
    "kind": "unknown",
    "line": 5451,
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
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "line": 557
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
   "fn": "parse_mode",
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
    "file": "/src/libgit2/src/tree.c",
    "fn": "parse_mode",
    "line": 367
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_7615794c1256.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471287/report.log",
   "testcase_size": 1
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471287",
  "project": "libgit2",
  "sites": [
   {
    "code": null,
    "fn": "parse_mode",
    "kind": "unknown",
    "line": 367,
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
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "merge_block",
    "line": 2666
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
   "fn": "read_bits_16",
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
   "code": "bits |= (int) p[rar->bits.in_addr + 2] | (int) p[rar->bits.in_addr + 2] | p[rar->bits.in_addr + 2] | rar->bits.in_addr + 2",
   "site": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "fn": "read_bits_16",
    "line": 953
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libarchive/libarchive/archive_read_support_format_rar5.c",
    "line": 951,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "bits",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libarchive_d5f35a90a4cb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libarchive/address/d5f35a90a4cb1eeb918213bff9d78e8b0471dc0a/ARVO-42471319/report.log",
   "testcase_size": 304
  },
  "input_reachability": [
   "rar",
   "p"
  ],
  "osv_id": "ARVO-42471319",
  "project": "libarchive",
  "sites": [
   {
    "code": "bits |= (int) p[rar->bits.in_addr + 2] | (int) p[rar->bits.in_addr + 2] | p[rar->bits.in_addr + 2] | rar->bits.in_addr + 2",
    "fn": "read_bits_16",
    "kind": "unknown",
    "line": 953,
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
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:645,IF:648,GOTO:648,WHILE:650,IF:652,IF:657,GOTO:657,IF:659,GOTO:659,IF:669,GOTO:669",
   "fn": "hb_blob_create_from_file",
   "guard_count": 2,
   "guards": "data == nullptr | new_data == nullptr",
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
   "code": "data = new_data",
   "site": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "line": 660
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 644,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "data",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2c68f34bddbe.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/2c68f34bddbe506d0b22948562f2f59b9a5b6050/ARVO-42471374/report.log",
   "testcase_size": 36
  },
  "input_reachability": [
   "file_name"
  ],
  "osv_id": "ARVO-42471374",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "malloc (allocated)",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "kind": "malloc",
    "line": 644,
    "origin": "cpg"
   },
   {
    "code": "realloc (data, allocated)",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "kind": "realloc",
    "line": 658,
    "origin": "cpg"
   },
   {
    "code": "data = new_data",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "kind": "unknown",
    "line": 660,
    "origin": "report:crash"
   },
   {
    "code": "free (data)",
    "fn": "BEInt<unsigned char, 1>::operator unsigned char() const",
    "kind": "free",
    "line": 680,
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
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/src/openvswitch/lib/util.c",
    "fn": "xrealloc",
    "line": 134
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
   "fn": "ofpbuf_insert",
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
    "width": 64
   },
   "code": null,
   "site": {
    "file": "/src/openvswitch/lib/ofpbuf.c",
    "fn": "ofpbuf_insert",
    "line": 473
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_aa1a0f1aaf6a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/aa1a0f1aaf6a772327b712d0507735af5b8c791d/ARVO-42471383/report.log",
   "testcase_size": 32
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471383",
  "project": "openvswitch",
  "sites": [
   {
    "code": null,
    "fn": "ofpbuf_insert",
    "kind": "unknown",
    "line": 473,
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
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_allocate",
    "line": 257
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
   "control_structures": "IF:206,IF:208,IF:213",
   "fn": "_get_kerx",
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
    "width": 94
   },
   "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "line": 214
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "line": 204,
    "size": null,
    "type": "hb_blob_t**"
   },
   "kind": "pointer",
   "name": "blob",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_b605db2f65e6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/b605db2f65e62ad6727a61481f78015933dbf207/ARVO-42471394/report.log",
   "testcase_size": 1816
  },
  "input_reachability": [
   "face",
   "blob"
  ],
  "osv_id": "ARVO-42471394",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "kind": "unknown",
    "line": 214,
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
   "entity_type": "hb_blob_t**",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "line": 557
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
   "control_structures": "IF:206,IF:208,IF:213",
   "fn": "_get_kerx",
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
    "width": 5
   },
   "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "line": 214
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-post-table.hh",
    "line": 204,
    "size": null,
    "type": "hb_blob_t**"
   },
   "kind": "pointer",
   "name": "blob",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_b605db2f65e6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/b605db2f65e62ad6727a61481f78015933dbf207/ARVO-42471424/report.log",
   "testcase_size": 16731
  },
  "input_reachability": [
   "face",
   "blob"
  ],
  "osv_id": "ARVO-42471424",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "*blob = hb_ot_face_data (face)->kerx.get_blob () | *blob | hb_ot_face_data (face)->kerx.get_blob () | ((hb_ot_face_data_t *)face->shaper_data.ot.get_relaxed()",
    "fn": "OT::post::accelerator_t::cmp_gids(void const*, void const*, void*)",
    "kind": "unknown",
    "line": 214,
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
   "entity_type": "hb_blob_t**",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/openthread/tests/fuzz/radio_receive_done.cpp",
    "fn": "LLVMFuzzerTestOneInput",
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
   "control_structures": "IF:1570,IF:1577,ELSE:1583",
   "fn": "otPlatRadioAddSrcMatchExtEntry",
   "guard_count": 1,
   "guards": "idx == CC1352_SRC_MATCH_NONE",
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
   "code": "sSrcMatchExtData.srcMatchEn[idx / 32] |= (1 << (idx % 32 | sSrcMatchExtData.srcMatchEn[idx / 32] | sSrcMatchExtData.srcMatchEn | idx / 32",
   "site": {
    "file": "/src/openthread/src/core/thread/mesh_forwarder.cpp",
    "fn": "ot::MeshForwarder::GetFramePriority(unsigned char*, unsigned char, ot::Mac::Address const&, ot::Mac::Address const&, unsigned char&)",
    "line": 1586
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "sSrcMatchExtData",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_08747cf7a7b5.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openthread/address/08747cf7a7b5d14e301d174f8d095f18b68e17aa/ARVO-42471519/report.log",
   "testcase_size": 13
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471519",
  "project": "openthread",
  "sites": [
   {
    "code": "sSrcMatchExtData.srcMatchEn[idx / 32] |= (1 << (idx % 32 | sSrcMatchExtData.srcMatchEn[idx / 32] | sSrcMatchExtData.srcMatchEn | idx / 32",
    "fn": "ot::MeshForwarder::GetFramePriority(unsigned char*, unsigned char, ot::Mac::Address const&, ot::Mac::Address const&, unsigned char&)",
    "kind": "unknown",
    "line": 1586,
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
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "line": 558
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
   "control_structures": "IF:736",
   "fn": "parse_uint",
   "guard_count": 1,
   "guards": "p == pend",
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
   "code": "*p = buf",
   "site": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "line": 728
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 728,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "p",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2087f5a2a743.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/2087f5a2a743380b36399ba8a2b4ff9e93890fcf/ARVO-42471829/report.log",
   "testcase_size": 648
  },
  "input_reachability": [
   "end"
  ],
  "osv_id": "ARVO-42471829",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "*p = buf",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "unknown",
    "line": 728,
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
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libfuzzer/FuzzerLoop.cpp",
    "fn": "fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
    "line": 558
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
   "control_structures": "IF:193,IF:200,IF:222,IF:231,FOR:245,IF:246",
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
    "width": 62017
   },
   "code": "{HB_TAG ('v','h','a','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TE | HB_TAG ('v','h','a','l') | (hb_tag_t)((((uint32_t)('v') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('v') & 0xFF) << 24) | (((uint32_t)('h') & 0",
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-cff2-table.hh",
    "fn": "CFF::CFF2VariationStore::serialize(hb_serialize_context_t*, CFF::CFF2VariationStore const*)",
    "line": 127
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
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_2087f5a2a743.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/2087f5a2a743380b36399ba8a2b4ff9e93890fcf/ARVO-42471892/report.log",
   "testcase_size": 383
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471892",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "{HB_TAG ('v','h','a','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TE | HB_TAG ('v','h','a','l') | (hb_tag_t)((((uint32_t)('v') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('v') & 0xFF) << 24) | (((uint32_t)('h') & 0",
    "fn": "CFF::CFF2VariationStore::serialize(hb_serialize_context_t*, CFF::CFF2VariationStore const*)",
    "kind": "unknown",
    "line": 127,
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
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/src/openvswitch/lib/util.c",
    "fn": "xrealloc",
    "line": 134
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
   "fn": "learn_check",
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
    "file": "/src/openvswitch/lib/learn.c",
    "fn": "learn_check",
    "line": 51
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_aa1a0f1aaf6a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/aa1a0f1aaf6a772327b712d0507735af5b8c791d/ARVO-42472056/report.log",
   "testcase_size": 148
  },
  "input_reachability": [],
  "osv_id": "ARVO-42472056",
  "project": "openvswitch",
  "sites": [
   {
    "code": null,
    "fn": "learn_check",
    "kind": "unknown",
    "line": 51,
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
   "alloc",
   "call_chain"
  ],
  "context": {
   "control_structures": "WHILE:453,IF:455,IF:476,GOTO:477,IF:478,GOTO:479,IF:491,GOTO:492,SWITCH:494,BREAK:501,IF:506,BREAK:511",
   "fn": "_hb_buffer_deserialize_glyphs_json",
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
   "code": "unlikely (!buffer->successful) | !buffer->successful | buffer->successful | !buffer->successful",
   "site": {
    "file": "/src/harfbuzz/src/hb-aat-layout-kerx-table.hh",
    "fn": "AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::driver_context_t::transition(AAT::StateTableDriver<AAT::ExtendedTypes, AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData>*, AAT::Entry<AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData> const*)",
    "line": 557
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-aat-layout-kerx-table.hh",
    "line": 442,
    "size": null,
    "type": "hb_buffer_t*"
   },
   "kind": "pointer",
   "name": "buffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_574d888c8a40.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/574d888c8a409295a952361a39c8e83a52a0fc3d/ARVO-42472801/report.log",
   "testcase_size": 407
  },
  "input_reachability": [
   "buffer"
  ],
  "osv_id": "ARVO-42472801",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "unlikely (!buffer->successful) | !buffer->successful | buffer->successful | !buffer->successful",
    "fn": "AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::driver_context_t::transition(AAT::StateTableDriver<AAT::ExtendedTypes, AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData>*, AAT::Entry<AAT::KerxSubTableFormat4<AAT::KerxSubTableHeader>::EntryData> const*)",
    "kind": "unknown",
    "line": 557,
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
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/radare2/libr/util/buf.c",
    "fn": "r_buf_set_bytes",
    "line": 535
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
   "fn": "r_read_le32",
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
    "file": "/src/radare2/libr/include/r_endian.h",
    "fn": "r_read_le32",
    "line": 176
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
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_ea833632f1eb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/ea833632f1eb47e2dba4c5fa174d1880acec3f93/ARVO-42472970/report.log",
   "testcase_size": 17410
  },
  "input_reachability": [],
  "osv_id": "ARVO-42472970",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "r_read_le32",
    "kind": "unknown",
    "line": 176,
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