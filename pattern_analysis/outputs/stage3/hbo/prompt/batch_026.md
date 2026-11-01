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
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/src/hdf5/src/H5MM.c",
    "fn": "H5MM_realloc",
    "line": 144
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
   "fn": "H5F_addr_decode_len",
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
    "file": "/src/hdf5/src/H5Fint.c",
    "fn": "H5F_addr_decode_len",
    "line": 2859
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
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_720e04e196aa.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/720e04e196aac60b8914830b0297fdf291cb7f00/ARVO-42520210/report.log",
   "testcase_size": 149
  },
  "input_reachability": [],
  "osv_id": "ARVO-42520210",
  "project": "hdf5",
  "sites": [
   {
    "code": null,
    "fn": "H5F_addr_decode_len",
    "kind": "unknown",
    "line": 2859,
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
    "line": 117
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
   "control_structures": "IF:460,IF:461,GOTO:462,IF:464,IF:467,IF:476,IF:477,ELSE:479,IF:479,IF:484,IF:496,IF:497",
   "fn": "ndpi_search_bittorrent",
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
    "width": 22
   },
   "code": "(strncmp((const char*)packet->payload, bt_search, strlen | strncmp((const char*)packet->payload, bt_search, strlen( | strncmp((const char*)packet->payload, bt_search, strlen( | (const char*)packet->payload",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/bittorrent.c",
    "fn": "ndpi_search_bittorrent",
    "line": 498
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/bittorrent.c",
    "line": 454,
    "size": null,
    "type": "ndpi_packet_struct*"
   },
   "kind": "pointer",
   "name": "packet",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_de24206adccf.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/de24206adccf2347addc05d6d62b3bf743fef411/ARVO-42520214/report.log",
   "testcase_size": 101
  },
  "input_reachability": [
   "ndpi_struct"
  ],
  "osv_id": "ARVO-42520214",
  "project": "ndpi",
  "sites": [
   {
    "code": "(strncmp((const char*)packet->payload, bt_search, strlen | strncmp((const char*)packet->payload, bt_search, strlen( | strncmp((const char*)packet->payload, bt_search, strlen( | (const char*)packet->payload",
    "fn": "ndpi_search_bittorrent",
    "kind": "unknown",
    "line": 498,
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
   "entity_type": "ndpi_packet_struct*",
   "is_signed": null,
   "ptr_origin": "unknown"
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
   "fn": "test_backend",
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
   "code": "benchmark::kMillisecond",
   "site": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "line": 142
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "benchmark",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_bf2e81754911.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/bf2e8175491126f7b7f471fb9739e84c623c8d2d/ARVO-42520290/report.log",
   "testcase_size": 1154
  },
  "input_reachability": [
   "backend",
   "backend_name",
   "test_input"
  ],
  "osv_id": "ARVO-42520290",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "benchmark::kMillisecond",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "unknown",
    "line": 142,
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
    "file": "/src/readstat/src/readstat_malloc.c",
    "fn": "readstat_realloc",
    "line": 33
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
   "fn": "sas_read2",
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
    "file": "/src/readstat/src/sas/readstat_sas.c",
    "fn": "sas_read2",
    "line": 152
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
   "cpg": "/root/gyx/mutator_create/cpg_files/readstat_b8e708d14d5e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/readstat/address/b8e708d14d5e11abca74822a701ec5e51b61ce14/ARVO-42520314/report.log",
   "testcase_size": 3584
  },
  "input_reachability": [],
  "osv_id": "ARVO-42520314",
  "project": "readstat",
  "sites": [
   {
    "code": null,
    "fn": "sas_read2",
    "kind": "unknown",
    "line": 152,
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
    "fn": "iv_aligned_malloc(void*, int, int)",
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
   "control_structures": "IF:4658,IF:4706,IF:4717,IF:4723,IF:4729,IF:4734,IF:4741,ELSE:4746,IF:4746,IF:4755,IF:4757,FOR:4791",
   "fn": "isvcd_populate_res_prms",
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
   "code": "ps_tmp_prms->i1_mb_mode = (WORD8) 0xFF | ps_tmp_prms->i1_mb_mode | (WORD8) 0xFF",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_intra_resamp.c",
    "fn": "isvcd_populate_res_prms",
    "line": 4811
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/svc/isvcd_intra_resamp.c",
    "line": 4769,
    "size": null,
    "type": "inter_lyr_mb_prms_t*"
   },
   "kind": "pointer",
   "name": "ps_tmp_prms",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_b2a61a152a5e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/b2a61a152a5e83b3419212e8d15a10d4488e51d9/ARVO-42520945/report.log",
   "testcase_size": 9554
  },
  "input_reachability": [
   "pv_svc_dec"
  ],
  "osv_id": "ARVO-42520945",
  "project": "libavc",
  "sites": [
   {
    "code": "ps_tmp_prms->i1_mb_mode = (WORD8) 0xFF | ps_tmp_prms->i1_mb_mode | (WORD8) 0xFF",
    "fn": "isvcd_populate_res_prms",
    "kind": "unknown",
    "line": 4811,
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
   "entity_type": "inter_lyr_mb_prms_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/buf.c",
    "fn": "xmlBufCreate",
    "line": 138
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
   "control_structures": "FOR:12069,IF:12077",
   "fn": "test_xmlClearNodeInfoSeq",
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
   "code": "test_ret++",
   "site": {
    "file": "/src/libxml2/parser.c",
    "fn": "xmlParseTryOrFinish",
    "line": 12080
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/parser.c",
    "line": 12063,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "test_ret",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_0e193f0d61f6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libxml2/address/0e193f0d61f6d6f29c31ac5f801975e810df7a04/ARVO-42521059/report.log",
   "testcase_size": 1591
  },
  "input_reachability": [],
  "osv_id": "ARVO-42521059",
  "project": "libxml2",
  "sites": [
   {
    "code": "test_ret++",
    "fn": "xmlParseTryOrFinish",
    "kind": "unknown",
    "line": 12080,
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
   "api": "calloc",
   "cross_function": true,
   "site": {
    "file": "/src/libgit2/src/util/allocators/stdalloc.c",
    "fn": "stdalloc__calloc",
    "line": 42
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
   "fn": "set_data",
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
    "width": 65487
   },
   "code": null,
   "site": {
    "file": "/src/libgit2/src/libgit2/transports/smart_pkt.c",
    "fn": "set_data",
    "line": 234
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_cefe6c456230.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/cefe6c4562304c9e23948b8e745c16e24921707f/ARVO-42521123/report.log",
   "testcase_size": 65536
  },
  "input_reachability": [],
  "osv_id": "ARVO-42521123",
  "project": "libgit2",
  "sites": [
   {
    "code": null,
    "fn": "set_data",
    "kind": "unknown",
    "line": 234,
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
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "H5O__fsinfo_decode",
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
    "file": "/src/hdf5/src/H5Ofsinfo.c",
    "fn": "H5O__fsinfo_decode",
    "line": 119
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
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42521166/report.log",
   "testcase_size": 1808
  },
  "input_reachability": [],
  "osv_id": "ARVO-42521166",
  "project": "hdf5",
  "sites": [
   {
    "code": null,
    "fn": "H5O__fsinfo_decode",
    "kind": "unknown",
    "line": 119,
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
   "control_structures": "IF:2074,IF:2100,ELSE:2119,IF:2184,IF:2190,IF:2223,IF:2233,FOR:2243,FOR:2258,IF:2265,IF:2275,FOR:2284",
   "fn": "isvcd_reflayer_construction_dyadic",
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
   "code": "i1_slice_id = ps_inter_lyr_mb_prms->i1_slice_id | ps_inter_lyr_mb_prms->i1_slice_id",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_intra_resamp.c",
    "fn": "isvcd_reflayer_construction_dyadic",
    "line": 2116
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/svc/isvcd_intra_resamp.c",
    "line": 2051,
    "size": null,
    "type": "WORD8"
   },
   "kind": "struct",
   "name": "i1_slice_id",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_b2a61a152a5e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/b2a61a152a5e83b3419212e8d15a10d4488e51d9/ARVO-42521316/report.log",
   "testcase_size": 1041
  },
  "input_reachability": [
   "ps_ref_mb_mode_map",
   "u2_mb_x",
   "u2_mb_y"
  ],
  "osv_id": "ARVO-42521316",
  "project": "libavc",
  "sites": [
   {
    "code": "i1_slice_id = ps_inter_lyr_mb_prms->i1_slice_id | ps_inter_lyr_mb_prms->i1_slice_id",
    "fn": "isvcd_reflayer_construction_dyadic",
    "kind": "unknown",
    "line": 2116,
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
   "entity_type": "WORD8",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/tests/fuzzing/../../../src/pkcs15init/pkcs15-lib.c",
    "fn": "sc_pkcs15init_update_file",
    "line": 4162
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
   "fn": "sc_hsm_write_ef",
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
    "width": 1224
   },
   "code": null,
   "site": {
    "file": "/src/opensc/src/libopensc/card-sc-hsm.c",
    "fn": "sc_hsm_write_ef",
    "line": 878
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
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_aadd82bb071e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/aadd82bb071e574fc57263a103e3bf06ebbd8de7/ARVO-42521319/report.log",
   "testcase_size": 21565
  },
  "input_reachability": [],
  "osv_id": "ARVO-42521319",
  "project": "opensc",
  "sites": [
   {
    "code": null,
    "fn": "sc_hsm_write_ef",
    "kind": "unknown",
    "line": 878,
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
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "H5FS__sect_link_size",
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
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/hdf5/src/H5FSsection.c",
    "fn": "H5FS__sect_link_size",
    "line": 973
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
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42521342/report.log",
   "testcase_size": 1808
  },
  "input_reachability": [],
  "osv_id": "ARVO-42521342",
  "project": "hdf5",
  "sites": [
   {
    "code": null,
    "fn": "H5FS__sect_link_size",
    "kind": "unknown",
    "line": 973,
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
    "fn": "iv_aligned_malloc(void*, int, int)",
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
   "control_structures": "FOR:572,IF:581,IF:584,BREAK:586,CONTINUE:590,IF:598,IF:603,IF:613",
   "fn": "isvcd_nal_byte_swap_emulation",
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
   "code": "*pu4_out_stream = (UWORD32) temp_out_stream | *pu4_out_stream | (UWORD32) temp_out_stream",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_nal.c",
    "fn": "isvcd_nal_byte_swap_emulation",
    "line": 617
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/svc/isvcd_nal.c",
    "line": 561,
    "size": null,
    "type": "UWORD32*"
   },
   "kind": "pointer",
   "name": "pu4_out_stream",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_4900778d4c9f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/4900778d4c9f01faa81f6f26327b57ae3b60e3c2/ARVO-42521509/report.log",
   "testcase_size": 1017591
  },
  "input_reachability": [
   "pu4_out_stream",
   "pu4_out_len",
   "pv_emulation_ctxt"
  ],
  "osv_id": "ARVO-42521509",
  "project": "libavc",
  "sites": [
   {
    "code": "*pu4_out_stream = (UWORD32) temp_out_stream | *pu4_out_stream | (UWORD32) temp_out_stream",
    "fn": "isvcd_nal_byte_swap_emulation",
    "kind": "unknown",
    "line": 617,
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
   "entity_type": "UWORD32*",
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
   "size_bytes": null,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:89,SWITCH:95,BREAK:99,BREAK:105,SWITCH:108,FOR:119,FOR:124,BREAK:133,FOR:140,FOR:143,BREAK:151,FOR:156",
   "fn": "BM_Font",
   "guard_count": 1,
   "guards": "g < num_glyphs",
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
   "code": "glyphs[g] = g | glyphs[g]",
   "site": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "line": 141
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "line": 137,
    "size": null,
    "type": "hb_codepoint_t*"
   },
   "kind": "pointer",
   "name": "glyphs",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_918193ebf908.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/918193ebf908d35c88bb71d02dfc14bc41ffc31d/ARVO-42521648/report.log",
   "testcase_size": 366
  },
  "free_related": {
   "free_sites_in_func": [
    130,
    150
   ],
   "reassign_between": true,
   "reassign_sites": [
    {
     "lhs": "glyphs",
     "line": 137,
     "rhs": "(hb_codepoint_t *) calloc (num_glyphs, sizeof (hb_codepoint_t))"
    }
   ],
   "remalloc_between": true
  },
  "input_reachability": [
   "test_input"
  ],
  "osv_id": "ARVO-42521648",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "calloc",
    "line": 115,
    "origin": "cpg"
   },
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "calloc",
    "line": 116,
    "origin": "cpg"
   },
   {
    "code": "free (glyphs)",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "free",
    "line": 130,
    "origin": "cpg"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "calloc",
    "line": 137,
    "origin": "cpg"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "calloc",
    "line": 138,
    "origin": "cpg"
   },
   {
    "code": "glyphs[g] = g | glyphs[g]",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "unknown",
    "line": 141,
    "origin": "report:crash"
   },
   {
    "code": "free (glyphs)",
    "fn": "BEInt<unsigned int, 3>::operator unsigned int() const",
    "kind": "free",
    "line": 150,
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
   "entity_type": "hb_codepoint_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/curl/lib/memdebug.c",
    "fn": "curl_dbg_malloc",
    "line": 146
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
   "fn": "rtsp_rtp_readwrite",
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
    "file": "/src/curl/lib/rtsp.c",
    "fn": "rtsp_rtp_readwrite",
    "line": 683
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
   "cpg": "/root/gyx/mutator_create/cpg_files/curl_f7a3fae4cb2a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/curl/address/f7a3fae4cb2af0f3b917eb6ccacb372a67ce8781/ARVO-42522403/report.log",
   "testcase_size": 875
  },
  "input_reachability": [],
  "osv_id": "ARVO-42522403",
  "project": "curl",
  "sites": [
   {
    "code": null,
    "fn": "rtsp_rtp_readwrite",
    "kind": "unknown",
    "line": 683,
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
    "file": "/src/ndpi/src/lib/ndpi_memory.c",
    "fn": "ndpi_malloc",
    "line": 60
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
   "control_structures": "FOR:378,IF:383,IF:386,BREAK:386,ELSE:391,IF:391,IF:394,BREAK:394,ELSE:399,IF:399,IF:402,BREAK:402",
   "fn": "processCertificateElements",
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
   "code": "flow->protos.tls_quic.server_names[flow->protos.tls_quic | flow->protos.tls_quic.server_names[flow->protos.tls_quic | flow->protos.tls_quic.server_names | flow->protos.tls_quic",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "fn": "processCertificateElements",
    "line": 682
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 364,
    "size": null,
    "type": "ndpi_flow_struct*"
   },
   "kind": "pointer",
   "name": "flow",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_2a3ade397b25.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/2a3ade397b250c5f13470c7be137ea763d216294/ARVO-42522544/report.log",
   "testcase_size": 65466
  },
  "input_reachability": [
   "ndpi_struct",
   "flow",
   "p_offset",
   "certificate_len"
  ],
  "osv_id": "ARVO-42522544",
  "project": "ndpi",
  "sites": [
   {
    "code": "flow->protos.tls_quic.server_names[flow->protos.tls_quic | flow->protos.tls_quic.server_names[flow->protos.tls_quic | flow->protos.tls_quic.server_names | flow->protos.tls_quic",
    "fn": "processCertificateElements",
    "kind": "unknown",
    "line": 682,
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
   "entity_type": "ndpi_flow_struct*",
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