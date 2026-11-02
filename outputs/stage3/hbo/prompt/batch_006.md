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
    "file": "/src/libhevc/fuzzer/hevc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 53
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
   "fn": "ihevcd_parse_slice_data",
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
    "file": "/src/libhevc/decoder/ihevcd_parse_slice.c",
    "fn": "ihevcd_parse_slice_data",
    "line": 3151
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_cdd7c97c2704.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/cdd7c97c270408c330fcffd7d280e68b3678efe4/ARVO-42477544/report.log",
   "testcase_size": 113
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477544",
  "project": "libhevc",
  "sites": [
   {
    "code": null,
    "fn": "ihevcd_parse_slice_data",
    "kind": "unknown",
    "line": 3151,
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
    "file": "/src/libhevc/decoder/ihevcd_api.c",
    "fn": "ihevcd_allocate_dynamic_bufs",
    "line": 1682
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
   "fn": "ihevcd_sao_shift_ctb",
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
    "file": "/src/libhevc/decoder/ihevcd_sao.c",
    "fn": "ihevcd_sao_shift_ctb",
    "line": 3318
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_cdd7c97c2704.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/cdd7c97c270408c330fcffd7d280e68b3678efe4/ARVO-42477558/report.log",
   "testcase_size": 251
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477558",
  "project": "libhevc",
  "sites": [
   {
    "code": null,
    "fn": "ihevcd_sao_shift_ctb",
    "kind": "unknown",
    "line": 3318,
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
    "file": "/src/libspng/tests/spng_read_fuzzer.cc",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 65
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
   "fn": "spng_decode_image",
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
    "file": "/src/libspng/spng.c",
    "fn": "spng_decode_image",
    "line": 2068
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libspng_d48a9fa212ce.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libspng/address/d48a9fa212cee4c05c51178b9c7813cd1299dcb3/ARVO-42477573/report.log",
   "testcase_size": 51
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477573",
  "project": "libspng",
  "sites": [
   {
    "code": null,
    "fn": "spng_decode_image",
    "kind": "unknown",
    "line": 2068,
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
    "file": "/src/libhevc/decoder/ihevcd_api.c",
    "fn": "ihevcd_allocate_dynamic_bufs",
    "line": 1830
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
   "fn": "ihevcd_ctb_boundary_strength_islice",
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
    "file": "/src/libhevc/decoder/ihevcd_boundary_strength.c",
    "fn": "ihevcd_ctb_boundary_strength_islice",
    "line": 452
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_cdd7c97c2704.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/cdd7c97c270408c330fcffd7d280e68b3678efe4/ARVO-42477586/report.log",
   "testcase_size": 473
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477586",
  "project": "libhevc",
  "sites": [
   {
    "code": null,
    "fn": "ihevcd_ctb_boundary_strength_islice",
    "kind": "unknown",
    "line": 452,
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "ihevcd_mv_pred",
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
    "file": "/src/libhevc/decoder/ihevcd_mv_pred.c",
    "fn": "ihevcd_mv_pred",
    "line": 442
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libhevc_a469393436a3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libhevc/address/a469393436a31721cc47533e6479ace24e81f6a4/ARVO-42477643/report.log",
   "testcase_size": 960
  },
  "input_reachability": [],
  "osv_id": "ARVO-42477643",
  "project": "libhevc",
  "sites": [
   {
    "code": null,
    "fn": "ihevcd_mv_pred",
    "kind": "unknown",
    "line": 442,
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
    "file": "/src/htslib/sam.c",
    "fn": "sam_realloc_bam_data",
    "line": 386
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
   "control_structures": "IF:3855",
   "fn": "hts_log",
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
    "width": 65
   },
   "code": "vfprintf(stderr, format, argptr)",
   "site": {
    "file": "/src/htslib/hts.c",
    "fn": "hts_log",
    "line": 3861
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
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_dd6f0b72c925.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/dd6f0b72c92591252bb77818663629cc1a129949/ARVO-42479042/report.log",
   "testcase_size": 165
  },
  "input_reachability": [
   "context",
   "format"
  ],
  "osv_id": "ARVO-42479042",
  "project": "htslib",
  "sites": [
   {
    "code": "vfprintf(stderr, format, argptr)",
    "fn": "hts_log",
    "kind": "unknown",
    "line": 3861,
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
    "file": "/src/radare2/libr/../libr/bin/p/../format/mach0/mach0.c",
    "fn": "walk_exports",
    "line": 1940
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
   "fn": "walk_exports",
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
    "file": "/src/radare2/libr/bin/format/mach0/mach0.c",
    "fn": "walk_exports",
    "line": 2017
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
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_c0779bd604b2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/c0779bd604b251fc97befebfdc870527b3947379/ARVO-42479230/report.log",
   "testcase_size": 65843
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479230",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "walk_exports",
    "kind": "unknown",
    "line": 2017,
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
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "fn": "ndpi_base64_decode",
    "line": 811
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
   "control_structures": "IF:72,FOR:81,IF:83,IF:84,ELSE:86,IF:86,ELSE:88,IF:88,ELSE:90,IF:90,ELSE:92,IF:92",
   "fn": "ndpi_search_mail_smtp_tcp",
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
   "code": "snprintf(flow->protos.ftp_imap_pop_smtp.password,",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/mail_smtp.c",
    "fn": "ndpi_search_mail_smtp_tcp",
    "line": 177
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/mail_smtp.c",
    "line": 67,
    "size": null,
    "type": "ndpi_flow_struct*"
   },
   "kind": "pointer",
   "name": "flow",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479685/report.log",
   "testcase_size": 99
  },
  "input_reachability": [
   "ndpi_struct",
   "flow"
  ],
  "osv_id": "ARVO-42479685",
  "project": "ndpi",
  "sites": [
   {
    "code": "snprintf(flow->protos.ftp_imap_pop_smtp.password,",
    "fn": "ndpi_search_mail_smtp_tcp",
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
   "entity_type": "ndpi_flow_struct*",
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
   "control_structures": "IF:752,IF:762,ELSE:765,IF:765,IF:768,IF:771,IF:795,ELSE:811,IF:820,IF:825,IF:828,IF:829",
   "fn": "getSSCertificateFingerprint",
   "guard_count": 2,
   "guards": "len < 10 | len > 4096",
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
   "code": "len = ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.t | ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_rec | *(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_of | (u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_off",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "fn": "getSSCertificateFingerprint",
    "line": 875
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tls.c",
    "line": 875,
    "size": null,
    "type": "u_int16_t"
   },
   "kind": "struct",
   "name": "len",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479687/report.log",
   "testcase_size": 110
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42479687",
  "project": "ndpi",
  "sites": [
   {
    "code": "len = ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.t | ntohs(*(u_int16_t*)&packet->payload[flow->l4.tcp.tls_rec | *(u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_of | (u_int16_t*)&packet->payload[flow->l4.tcp.tls_record_off",
    "fn": "getSSCertificateFingerprint",
    "kind": "unknown",
    "line": 875,
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
   "control_structures": "IF:149,IF:153,IF:158,ELSE:160,IF:160,IF:163,ELSE:167,IF:170,GOTO:173,IF:178,IF:182,IF:192",
   "fn": "ndpi_int_check_stun",
   "guard_count": 1,
   "guards": "j<i",
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
   "code": "flow->host_server_name[j] = payload[k++] | flow->host_server_name[j] | flow->host_server_name | payload[k++]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "fn": "ndpi_int_check_stun",
    "line": 354
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/stun.c",
    "line": 141,
    "size": null,
    "type": "ndpi_flow_struct*"
   },
   "kind": "pointer",
   "name": "flow",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479691/report.log",
   "testcase_size": 58
  },
  "input_reachability": [
   "flow",
   "payload"
  ],
  "osv_id": "ARVO-42479691",
  "project": "ndpi",
  "sites": [
   {
    "code": "flow->host_server_name[j] = payload[k++] | flow->host_server_name[j] | flow->host_server_name | payload[k++]",
    "fn": "ndpi_int_check_stun",
    "kind": "unknown",
    "line": 354,
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
   "control_structures": "IF:187,IF:191,FOR:194,ELSE:199",
   "fn": "SHA1Update",
   "guard_count": 1,
   "guards": "(context->count[0] += len << 3) < j",
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
   "code": "memcpy(&context->buffer[j], data, (i = 64-j)) | &context->buffer[j] | context->buffer[j] | context->buffer",
   "site": {
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "fn": "SHA1Update",
    "line": 192
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "line": 181,
    "size": null,
    "type": "SHA1_CTX*"
   },
   "kind": "pointer",
   "name": "context",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479695/report.log",
   "testcase_size": 84
  },
  "input_reachability": [
   "context",
   "data",
   "len"
  ],
  "osv_id": "ARVO-42479695",
  "project": "ndpi",
  "sites": [
   {
    "code": "memcpy(&context->buffer[j], data, (i = 64-j)) | &context->buffer[j] | context->buffer[j] | context->buffer",
    "fn": "SHA1Update",
    "kind": "unknown",
    "line": 192,
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
   "entity_type": "SHA1_CTX*",
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
   "fn": "SHA1Transform",
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
   "code": "memcpy(block, buffer, 64)",
   "site": {
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "fn": "SHA1Transform",
    "line": 115
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/third_party/src/ndpi_sha1.c",
    "line": 114,
    "size": null,
    "type": "CHAR64LONG16[1]"
   },
   "kind": "array",
   "name": "block",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e695dd6eade7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e695dd6eade754b2d50bdf297ca8bdc4105f93ff/ARVO-42479697/report.log",
   "testcase_size": 184
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479697",
  "project": "ndpi",
  "sites": [
   {
    "code": "memcpy(block, buffer, 64)",
    "fn": "SHA1Transform",
    "kind": "unknown",
    "line": 115,
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
   "entity_type": "CHAR64LONG16[1]",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_file_set_sec_attr",
    "line": 678
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
   "control_structures": "WHILE:790,IF:792,BREAK:793,IF:797,IF:802,IF:803,IF:804,IF:805,IF:806,IF:809,IF:811,BREAK:812",
   "fn": "parse_sec_attr_44",
   "guard_count": 3,
   "guards": "iACLen > len | iACLen > (1+iParmLen+iKeyLen) | iACLen > 0",
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
   "code": "iACLen   = buf[iOffset] & 0x0F | buf[iOffset] & 0x0F | buf[iOffset]",
   "site": {
    "file": "/src/opensc/src/libopensc/card-setcos.c",
    "fn": "parse_sec_attr_44",
    "line": 791
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-setcos.c",
    "line": 791,
    "size": null,
    "type": "size_t"
   },
   "kind": "struct",
   "name": "iACLen",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_8fea658fe9b5.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/8fea658fe9b5bdf51de7e321a1a549056ba4b150/ARVO-42479758/report.log",
   "testcase_size": 74
  },
  "input_reachability": [
   "buf",
   "len"
  ],
  "osv_id": "ARVO-42479758",
  "project": "opensc",
  "sites": [
   {
    "code": "iACLen   = buf[iOffset] & 0x0F | buf[iOffset] & 0x0F | buf[iOffset]",
    "fn": "parse_sec_attr_44",
    "kind": "unknown",
    "line": 791,
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
   "entity_type": "size_t",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/build/hdf5-3JSo9x/hdf5-1.8.16+docs/debian/build/src/../../../src/H5FL.c",
    "fn": "H5FL_malloc",
    "line": 199
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
   "fn": "Mat_VarReadNextInfoIterate",
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
    "width": 7680
   },
   "code": null,
   "site": {
    "file": "/src/matio/src/mat73.c",
    "fn": "Mat_VarReadNextInfoIterate",
    "line": 2788
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
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_6540087e697c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/6540087e697ca2b8950bada3d4ca653951b467dc/ARVO-42479773/report.log",
   "testcase_size": 71808
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479773",
  "project": "matio",
  "sites": [
   {
    "code": null,
    "fn": "Mat_VarReadNextInfoIterate",
    "kind": "unknown",
    "line": 2788,
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "git_buf_decode_base85",
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
    "file": "/src/libgit2/src/buffer.c",
    "fn": "git_buf_decode_base85",
    "line": 431
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
   "cpg": "/root/gyx/mutator_create/cpg_files/libgit2_b246bed5ab83.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/b246bed5ab83035d8aef95f1b7ff10dd746db7cb/ARVO-42479852/report.log",
   "testcase_size": 59
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479852",
  "project": "libgit2",
  "sites": [
   {
    "code": null,
    "fn": "git_buf_decode_base85",
    "kind": "unknown",
    "line": 431,
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