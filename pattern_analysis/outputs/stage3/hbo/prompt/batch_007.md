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
    "file": "/src/lwan/src/lib/lwan-array.c",
    "fn": "lwan_array_append_heap",
    "line": 80
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
   "control_structures": "FOR:1004,IF:1005,FOR:1006,IF:1007,IF:1012,BREAK:1014,IF:1018,ELSE:1027,IF:1027,FOR:1030,IF:1031,IF:1036",
   "fn": "post_process_template",
   "guard_count": 5,
   "guards": "chunk < ((typeof)(&parser->chunks)->base.base + (&parser->chunks)->bas | chunk->action == ACTION_LAST | chunk->action == ACTION_LAST",
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
   "code": "chunk->action == ACTION_LAST | chunk->action",
   "site": {
    "file": "/src/lwan/src/lib/lwan-template.c",
    "fn": "post_process_template",
    "line": 1007
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-template.c",
    "line": 1002,
    "size": null,
    "type": "chunk*"
   },
   "kind": "pointer",
   "name": "chunk",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_f905fa80d71d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lwan/address/f905fa80d71d6a0f6d773938f39e3f9d7558d537/ARVO-42479930/report.log",
   "testcase_size": 26
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479930",
  "project": "lwan",
  "sites": [
   {
    "code": "chunk->action == ACTION_LAST | chunk->action",
    "fn": "post_process_template",
    "kind": "unknown",
    "line": 1007,
    "origin": "report:crash"
   },
   {
    "code": "malloc(sizeof(*cd))",
    "fn": "post_process_template",
    "kind": "malloc",
    "line": 1017,
    "origin": "cpg"
   },
   {
    "code": "malloc(sizeof(*cd))",
    "fn": "post_process_template",
    "kind": "malloc",
    "line": 1050,
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
   "entity_type": "chunk*",
   "is_signed": null,
   "ptr_origin": "assignment"
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "WHILE:453,IF:459,BREAK:461,ELSE:464,IF:465,FOR:468,ELSE:470,IF:470,ELSE:483,IF:507,IF:549,WHILE:560",
   "fn": "ih264d_decode_slice_thread",
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
   "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
   "site": {
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "fn": "ih264d_decode_slice_thread",
    "line": 510
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 438,
    "size": null,
    "type": "dec_struct_t*"
   },
   "kind": "pointer",
   "name": "ps_dec",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_25e615b9cbd4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/25e615b9cbd4ed41f9586dd82f947e72b0101f8b/ARVO-42479939/report.log",
   "testcase_size": 44
  },
  "input_reachability": [
   "ps_dec"
  ],
  "osv_id": "ARVO-42479939",
  "project": "libavc",
  "sites": [
   {
    "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
    "fn": "ih264d_decode_slice_thread",
    "kind": "unknown",
    "line": 510,
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
   "entity_type": "dec_struct_t*",
   "is_signed": null,
   "ptr_origin": "param"
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "WHILE:453,IF:459,BREAK:461,ELSE:464,IF:465,FOR:468,ELSE:470,IF:470,ELSE:483,IF:507,IF:549,WHILE:560",
   "fn": "ih264d_decode_slice_thread",
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
   "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
   "site": {
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "fn": "ih264d_decode_slice_thread",
    "line": 510
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_thread_parse_decode.c",
    "line": 438,
    "size": null,
    "type": "dec_struct_t*"
   },
   "kind": "pointer",
   "name": "ps_dec",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_25e615b9cbd4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/25e615b9cbd4ed41f9586dd82f947e72b0101f8b/ARVO-42480014/report.log",
   "testcase_size": 54
  },
  "input_reachability": [
   "ps_dec"
  ],
  "osv_id": "ARVO-42480014",
  "project": "libavc",
  "sites": [
   {
    "code": "(void *) ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_s | ps_dec->ps_decode_cur_slice->pv_tu_coeff_data_start | ps_dec->ps_decode_cur_slice",
    "fn": "ih264d_decode_slice_thread",
    "kind": "unknown",
    "line": 510,
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
   "entity_type": "dec_struct_t*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_allocate",
    "line": 253
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
   "fn": "bytes_to_hexstr_punct",
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
    "file": "/src/wireshark/epan/to_str.c",
    "fn": "bytes_to_hexstr_punct",
    "line": 168
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_7519c077d0d2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wireshark/address/7519c077d0d27c5e8c87c6df1ab19c3d172df45a/ARVO-42480062/report.log",
   "testcase_size": 279
  },
  "input_reachability": [],
  "osv_id": "ARVO-42480062",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "bytes_to_hexstr_punct",
    "kind": "unknown",
    "line": 168,
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
    "line": 253
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
   "control_structures": "IF:37,ELSE:47,IF:47,ELSE:55",
   "fn": "ndpi_check_amazon_video",
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
   "code": "packet->payload[1] == 0xED | packet->payload[1] | packet->payload",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/amazon_video.c",
    "fn": "ndpi_check_amazon_video",
    "line": 39
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/amazon_video.c",
    "line": 33,
    "size": null,
    "type": "ndpi_packet_struct*"
   },
   "kind": "pointer",
   "name": "packet",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_ead0325debc9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/ead0325debc96b2d134a625b4fac184a979ccc5a/ARVO-42480096/report.log",
   "testcase_size": 81
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42480096",
  "project": "ndpi",
  "sites": [
   {
    "code": "packet->payload[1] == 0xED | packet->payload[1] | packet->payload",
    "fn": "ndpi_check_amazon_video",
    "kind": "unknown",
    "line": 39,
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
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_allocate",
    "line": 253
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
   "control_structures": "IF:213,IF:215,IF:238,IF:242,ELSE:246,IF:257,IF:261,IF:268,IF:274,ELSE:277,IF:281,IF:295",
   "fn": "getTLScertificate",
   "guard_count": 6,
   "guards": "offset >= (packet->payload_packet_len+4) | j<len | offset < total_len",
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
   "code": "strncpy(buffer, (char*)&packet->payload[offset+extension | (char*)&packet->payload[offset+extension_offset+5] | &packet->payload[offset+extension_offset+5] | packet->payload[offset+extension_offset+5]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "fn": "getTLScertificate",
    "line": 584
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 203,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "buffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_d0e7e6955293.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/d0e7e6955293b656e1a1d7b01aebc1b5beefe711/ARVO-42480282/report.log",
   "testcase_size": 111
  },
  "input_reachability": [
   "flow",
   "buffer",
   "buffer_len"
  ],
  "osv_id": "ARVO-42480282",
  "project": "ndpi",
  "sites": [
   {
    "code": "strncpy(buffer, (char*)&packet->payload[offset+extension | (char*)&packet->payload[offset+extension_offset+5] | &packet->payload[offset+extension_offset+5] | packet->payload[offset+extension_offset+5]",
    "fn": "getTLScertificate",
    "kind": "unknown",
    "line": 584,
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
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_allocate",
    "line": 253
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
   "control_structures": "IF:113,IF:114,ELSE:121,IF:121,IF:122,IF:127,ELSE:136,IF:146,ELSE:147,IF:147,ELSE:148,IF:148",
   "fn": "ndpi_search_memcached",
   "guard_count": 26,
   "guards": "(sizeof (\"set \") - 1) > length | (sizeof (\"add \") - 1) > length | (sizeof (\"replace \") - 1) > length",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 13
   },
   "code": "! MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | (sizeof (\"CLIENT_ERROR \") - 1) > length || memcmp(offset | (sizeof (\"CLIENT_ERROR \") - 1) > length",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/memcached.c",
    "fn": "ndpi_search_memcached",
    "line": 162
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/memcached.c",
    "line": 108,
    "size": null,
    "type": "u_int16_t"
   },
   "kind": "struct",
   "name": "length",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_d37b69ce9c9c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/d37b69ce9c9caa979de7c511e33cb7d1cf5fbc91/ARVO-42480344/report.log",
   "testcase_size": 44
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42480344",
  "project": "ndpi",
  "sites": [
   {
    "code": "! MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | MEMCACHED_MATCH(MCDR_CLIENT_ERROR) | (sizeof (\"CLIENT_ERROR \") - 1) > length || memcmp(offset | (sizeof (\"CLIENT_ERROR \") - 1) > length",
    "fn": "ndpi_search_memcached",
    "kind": "unknown",
    "line": 162,
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
   "entity_type": "u_int16_t",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_allocate",
    "line": 253
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
   "control_structures": "IF:149,IF:153,IF:158,ELSE:160,IF:160,IF:163,ELSE:167,IF:170,GOTO:173,IF:178,IF:182,IF:192",
   "fn": "ndpi_int_check_stun",
   "guard_count": 2,
   "guards": "len == 4 | len == 4",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 2
   },
   "code": "len = ntohs(*((u_int16_t*)&payload[offset+2])) | ntohs(*((u_int16_t*)&payload[offset+2])) | *((u_int16_t*)&payload[offset+2]) | (u_int16_t*)&payload[offset+2]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "fn": "ndpi_int_check_stun",
    "line": 319
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "line": 319,
    "size": null,
    "type": "u_int16_t"
   },
   "kind": "struct",
   "name": "len",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_2c2bb11c9b70.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/2c2bb11c9b704c5b13e9b45d93a16fbad6304cb0/ARVO-42480353/report.log",
   "testcase_size": 51
  },
  "input_reachability": [
   "payload"
  ],
  "osv_id": "ARVO-42480353",
  "project": "ndpi",
  "sites": [
   {
    "code": "len = ntohs(*((u_int16_t*)&payload[offset+2])) | ntohs(*((u_int16_t*)&payload[offset+2])) | *((u_int16_t*)&payload[offset+2]) | (u_int16_t*)&payload[offset+2]",
    "fn": "ndpi_int_check_stun",
    "kind": "unknown",
    "line": 319,
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
   "entity_type": "u_int16_t",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
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
   "control_structures": "IF:155,IF:157,IF:163,IF:171,IF:200,IF:202,IF:204,IF:207,IF:211,IF:216,IF:218,IF:223",
   "fn": "pixReadMemBmp",
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
    "width": 196
   },
   "code": "memcpy(cmapBuf, cdata + BMP_FHBYTES + ihbytes,",
   "site": {
    "file": "/src/leptonica/src/bmpio.c",
    "fn": "pixReadMemBmp",
    "line": 250
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/leptonica/src/bmpio.c",
    "line": 136,
    "size": null,
    "type": "l_uint8*"
   },
   "kind": "pointer",
   "name": "cmapBuf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_95405007f7eb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/95405007f7ebf7df69f13475b3259179cdc4ec12/ARVO-42480786/report.log",
   "testcase_size": 65
  },
  "input_reachability": [
   "cdata"
  ],
  "osv_id": "ARVO-42480786",
  "project": "leptonica",
  "sites": [
   {
    "code": "calloc(cmapEntries, sizeof (RGBA_QUAD))",
    "fn": "pixReadMemBmp",
    "kind": "calloc",
    "line": 244,
    "origin": "cpg"
   },
   {
    "code": "memcpy(cmapBuf, cdata + BMP_FHBYTES + ihbytes,",
    "fn": "pixReadMemBmp",
    "kind": "unknown",
    "line": 250,
    "origin": "report:crash"
   },
   {
    "code": "free(cmapBuf)",
    "fn": "pixReadMemBmp",
    "kind": "free",
    "line": 257,
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
   "entity_type": "l_uint8*",
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
   "fn": "substitute",
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
    "width": 12
   },
   "code": "apply (proxy, plan, font, buffer)",
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "fn": "OT::VarRegionList::serialize(hb_serialize_context_t*, OT::VarRegionList const*, hb_bimap_t const&)",
    "line": 1910
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "line": 1909,
    "size": null,
    "type": "GSUBProxy"
   },
   "kind": "struct",
   "name": "proxy",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_9e48c6e9ef3f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/9e48c6e9ef3f6d398c7140933a2cd90980f0ed5b/ARVO-42481044/report.log",
   "testcase_size": 6452
  },
  "input_reachability": [
   "this",
   "plan",
   "font",
   "buffer"
  ],
  "osv_id": "ARVO-42481044",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "apply (proxy, plan, font, buffer)",
    "fn": "OT::VarRegionList::serialize(hb_serialize_context_t*, OT::VarRegionList const*, hb_bimap_t const&)",
    "kind": "unknown",
    "line": 1910,
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
   "entity_type": "GSUBProxy",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 80
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
   "control_structures": "IF:1411,SWITCH:1428,IF:1430,ELSE:1433,BREAK:1436,BREAK:1443,BREAK:1451,IF:1459,ELSE:1461,IF:1461,IF:1464,IF:1467",
   "fn": "ndpi_workflow_process_packet",
   "guard_count": 2,
   "guards": "check <= 1500 | check >= 1536",
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
   "code": "check = ntohs(ethernet->h_proto) | ntohs(ethernet->h_proto) | ethernet->h_proto",
   "site": {
    "file": "/src/ndpi/example/reader_util.c",
    "fn": "ndpi_workflow_process_packet",
    "line": 1457
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1394,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "check",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481193/report.log",
   "testcase_size": 40
  },
  "input_reachability": [
   "header",
   "packet"
  ],
  "osv_id": "ARVO-42481193",
  "project": "ndpi",
  "sites": [
   {
    "code": "check = ntohs(ethernet->h_proto) | ntohs(ethernet->h_proto) | ethernet->h_proto",
    "fn": "ndpi_workflow_process_packet",
    "kind": "unknown",
    "line": 1457,
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
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 80
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
   "control_structures": "IF:919",
   "fn": "get_ndpi_flow_info6",
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
   "code": "iph.saddr = iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->i | iph.saddr | iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->ip6_src.u6_ad | iph6->ip6_src.u6_addr.u6_addr32[2]",
   "site": {
    "file": "/src/ndpi/example/reader_util.c",
    "fn": "get_ndpi_flow_info6",
    "line": 915
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 911,
    "size": null,
    "type": "ndpi_iphdr"
   },
   "kind": "struct",
   "name": "iph",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481196/report.log",
   "testcase_size": 62
  },
  "input_reachability": [
   "iph6"
  ],
  "osv_id": "ARVO-42481196",
  "project": "ndpi",
  "sites": [
   {
    "code": "iph.saddr = iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->i | iph.saddr | iph6->ip6_src.u6_addr.u6_addr32[2] + iph6->ip6_src.u6_ad | iph6->ip6_src.u6_addr.u6_addr32[2]",
    "fn": "get_ndpi_flow_info6",
    "kind": "unknown",
    "line": 915,
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
   "entity_type": "ndpi_iphdr",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 80
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
   "control_structures": "IF:662,IF:663,IF:666,ELSE:672,IF:679,ELSE:681,IF:681,ELSE:683,IF:683,ELSE:685,IF:685,ELSE:687",
   "fn": "get_ndpi_flow_info",
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
   "code": "*sport = ntohs((*tcph)->source), *dport = ntohs((*tcph)- | *sport = ntohs((*tcph)->source) | *sport | ntohs((*tcph)->source)",
   "site": {
    "file": "/src/ndpi/example/reader_util.c",
    "fn": "get_ndpi_flow_info",
    "line": 703
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 644,
    "size": null,
    "type": "u_int16_t*"
   },
   "kind": "pointer",
   "name": "sport",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481216/report.log",
   "testcase_size": 86
  },
  "input_reachability": [
   "iph",
   "iph6",
   "tcph",
   "sport",
   "dport"
  ],
  "osv_id": "ARVO-42481216",
  "project": "ndpi",
  "sites": [
   {
    "code": "*sport = ntohs((*tcph)->source), *dport = ntohs((*tcph)- | *sport = ntohs((*tcph)->source) | *sport | ntohs((*tcph)->source)",
    "fn": "get_ndpi_flow_info",
    "kind": "unknown",
    "line": 703,
    "origin": "report:crash"
   },
   {
    "code": "malloc(sizeof(struct ndpi_flow_info))",
    "fn": "get_ndpi_flow_info",
    "kind": "malloc",
    "line": 770,
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
   "entity_type": "u_int16_t*",
   "is_signed": null,
   "ptr_origin": "param"
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
   "control_structures": "IF:1411,SWITCH:1428,IF:1430,ELSE:1433,BREAK:1436,BREAK:1443,BREAK:1451,IF:1459,ELSE:1461,IF:1461,IF:1464,IF:1467",
   "fn": "ndpi_workflow_process_packet",
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
   "code": "fc = wifi->fc | wifi->fc",
   "site": {
    "file": "/src/ndpi/example/reader_util.c",
    "fn": "ndpi_workflow_process_packet",
    "line": 1497
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1390,
    "size": null,
    "type": "u_int16_t"
   },
   "kind": "struct",
   "name": "fc",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_98d9f524f9ff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/98d9f524f9ff7746d0345939fe543020f8057212/ARVO-42481277/report.log",
   "testcase_size": 286
  },
  "input_reachability": [
   "header",
   "packet"
  ],
  "osv_id": "ARVO-42481277",
  "project": "ndpi",
  "sites": [
   {
    "code": "fc = wifi->fc | wifi->fc",
    "fn": "ndpi_workflow_process_packet",
    "kind": "unknown",
    "line": 1497,
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
   "entity_type": "u_int16_t",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
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
   "fn": "<clinit>",
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
   "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
   "site": {
    "file": "/src/harfbuzz/src/hb-array.hh",
    "fn": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "line": 220
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_c828d7bf76dd.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/c828d7bf76dd039be1775edff1d798dbcc10708b/ARVO-42481371/report.log",
   "testcase_size": 100109
  },
  "input_reachability": [],
  "osv_id": "ARVO-42481371",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
    "fn": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "kind": "unknown",
    "line": 220,
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