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
   "control_structures": "IF:127,IF:143,IF:149,IF:170,IF:177,IF:180,IF:182,IF:183,IF:194,IF:201,IF:208,IF:215",
   "fn": "ndpi_search_oscar_tcp_connect",
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
   "code": "get_u_int32_t(packet->payload, 6) == htonl(FLAPVERSION) | get_u_int32_t(packet->payload, 6) | packet->payload | htonl(FLAPVERSION)",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/oscar.c",
    "fn": "ndpi_search_oscar_tcp_connect",
    "line": 145
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/oscar.c",
    "line": 112,
    "size": null,
    "type": "ndpi_packet_struct*"
   },
   "kind": "pointer",
   "name": "packet",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_e21fe5d594e4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/e21fe5d594e42cb7add0f86ad2b625a0693e8ba9/ARVO-42481695/report.log",
   "testcase_size": 52
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42481695",
  "project": "ndpi",
  "sites": [
   {
    "code": "get_u_int32_t(packet->payload, 6) == htonl(FLAPVERSION) | get_u_int32_t(packet->payload, 6) | packet->payload | htonl(FLAPVERSION)",
    "fn": "ndpi_search_oscar_tcp_connect",
    "kind": "unknown",
    "line": 145,
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
   "control_structures": "IF:1411,IF:1427,SWITCH:1431,IF:1433,ELSE:1436,BREAK:1439,BREAK:1446,BREAK:1454,IF:1462,ELSE:1464,IF:1464,IF:1467",
   "fn": "ndpi_workflow_process_packet",
   "guard_count": 2,
   "guards": "iph->version == IPVERSION | iph->version != IPVERSION",
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
   "code": "iph->version == IPVERSION | iph->version",
   "site": {
    "file": "/src/ndpi/example/reader_util.c",
    "fn": "ndpi_workflow_process_packet",
    "line": 1600
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1380,
    "size": null,
    "type": "ndpi_iphdr*"
   },
   "kind": "pointer",
   "name": "iph",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_931f51bd77b2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/931f51bd77b2b863cab010064d2a2d0b4f968f7e/ARVO-42481810/report.log",
   "testcase_size": 129
  },
  "input_reachability": [
   "header",
   "packet"
  ],
  "osv_id": "ARVO-42481810",
  "project": "ndpi",
  "sites": [
   {
    "code": "iph->version == IPVERSION | iph->version",
    "fn": "ndpi_workflow_process_packet",
    "kind": "unknown",
    "line": 1600,
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
   "entity_type": "ndpi_iphdr*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/htslib/cram/cram_io.c",
    "fn": "cram_read_block",
    "line": 951
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
   "fn": "hts_md5_update",
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
    "width": 36
   },
   "code": null,
   "site": {
    "file": "/src/htslib/md5.c",
    "fn": "hts_md5_update",
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
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_6b72368c97a2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/6b72368c97a234ceebdc89c8806199585d9706b3/ARVO-42481865/report.log",
   "testcase_size": 331
  },
  "input_reachability": [],
  "osv_id": "ARVO-42481865",
  "project": "htslib",
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
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "context": {
   "fn": "get16",
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
   "code": "v = *(u_int16_t*)&payload[*i] | *(u_int16_t*)&payload[*i] | (u_int16_t*)&payload[*i] | &payload[*i]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/dns.c",
    "fn": "get16",
    "line": 40
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/dns.c",
    "line": 40,
    "size": null,
    "type": "u_int16_t"
   },
   "kind": "struct",
   "name": "v",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_5c52c00ea4ad.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/5c52c00ea4ad8afaebd5259bc53215a1ab41569f/ARVO-42481886/report.log",
   "testcase_size": 46
  },
  "input_reachability": [
   "i",
   "payload"
  ],
  "osv_id": "ARVO-42481886",
  "project": "ndpi",
  "sites": [
   {
    "code": "v = *(u_int16_t*)&payload[*i] | *(u_int16_t*)&payload[*i] | (u_int16_t*)&payload[*i] | &payload[*i]",
    "fn": "get16",
    "kind": "unknown",
    "line": 40,
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
   "code": "iph.daddr = iph6->ip6_dst.u6_addr.u6_addr32[2] + iph6->i | iph.daddr | iph6->ip6_dst.u6_addr.u6_addr32[2] + iph6->ip6_dst.u6_ad | iph6->ip6_dst.u6_addr.u6_addr32[2]",
   "site": {
    "file": "/src/ndpi/example/reader_util.c",
    "fn": "get_ndpi_flow_info6",
    "line": 916
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
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_812505b56bb4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/812505b56bb4508bc42e1615d6425ad26444d3f8/ARVO-42481924/report.log",
   "testcase_size": 2210
  },
  "input_reachability": [
   "iph6"
  ],
  "osv_id": "ARVO-42481924",
  "project": "ndpi",
  "sites": [
   {
    "code": "iph.daddr = iph6->ip6_dst.u6_addr.u6_addr32[2] + iph6->i | iph.daddr | iph6->ip6_dst.u6_addr.u6_addr32[2] + iph6->ip6_dst.u6_ad | iph6->ip6_dst.u6_addr.u6_addr32[2]",
    "fn": "get_ndpi_flow_info6",
    "kind": "unknown",
    "line": 916,
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
   "control_structures": "IF:63,IF:66,IF:70,ELSE:73,IF:75",
   "fn": "ndpi_add_connection_as_bittorrent",
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
    "width": 20
   },
   "code": "memcpy(flow->protos.bittorrent.hash, bt_hash, 20) | flow->protos.bittorrent.hash | flow->protos.bittorrent | flow->protos",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/bittorrent.c",
    "fn": "ndpi_add_connection_as_bittorrent",
    "line": 75
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/bittorrent.c",
    "line": 64,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "bt_hash",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_5c52c00ea4ad.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/5c52c00ea4ad8afaebd5259bc53215a1ab41569f/ARVO-42481957/report.log",
   "testcase_size": 65
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42481957",
  "project": "ndpi",
  "sites": [
   {
    "code": "memcpy(flow->protos.bittorrent.hash, bt_hash, 20) | flow->protos.bittorrent.hash | flow->protos.bittorrent | flow->protos",
    "fn": "ndpi_add_connection_as_bittorrent",
    "kind": "unknown",
    "line": 75,
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
   "control_structures": "IF:46,WHILE:49,IF:50,BREAK:52,IF:59,FOR:67",
   "fn": "ndpi_netbios_name_interpret",
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
   "code": "in[0] < 'A' || in[0] > 'P' || in[1] < 'A' || in[1] > 'P' | in[0] < 'A' || in[0] > 'P' || in[1] < 'A' | in[0] < 'A' || in[0] > 'P' | in[0] < 'A'",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/netbios.c",
    "fn": "ndpi_netbios_name_interpret",
    "line": 50
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/netbios.c",
    "line": 38,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "in",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_5c52c00ea4ad.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/5c52c00ea4ad8afaebd5259bc53215a1ab41569f/ARVO-42482009/report.log",
   "testcase_size": 100
  },
  "input_reachability": [
   "in"
  ],
  "osv_id": "ARVO-42482009",
  "project": "ndpi",
  "sites": [
   {
    "code": "in[0] < 'A' || in[0] > 'P' || in[1] < 'A' || in[1] > 'P' | in[0] < 'A' || in[0] > 'P' || in[1] < 'A' | in[0] < 'A' || in[0] > 'P' | in[0] < 'A'",
    "fn": "ndpi_netbios_name_interpret",
    "kind": "unknown",
    "line": 50,
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
   "control_structures": "DO:68,IF:73,BREAK:74,IF:80",
   "fn": "check_ymsg",
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
   "code": "memcmp(yahoo->YMSG_str, \"YMSG\", 4) == 0 | memcmp(yahoo->YMSG_str, \"YMSG\", 4) | yahoo->YMSG_str",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/yahoo.c",
    "fn": "check_ymsg",
    "line": 78
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/yahoo.c",
    "line": 65,
    "size": null,
    "type": "ndpi_yahoo_header*"
   },
   "kind": "pointer",
   "name": "yahoo",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_5c52c00ea4ad.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/5c52c00ea4ad8afaebd5259bc53215a1ab41569f/ARVO-42482045/report.log",
   "testcase_size": 66
  },
  "input_reachability": [
   "payload",
   "payload_packet_len"
  ],
  "osv_id": "ARVO-42482045",
  "project": "ndpi",
  "sites": [
   {
    "code": "memcmp(yahoo->YMSG_str, \"YMSG\", 4) == 0 | memcmp(yahoo->YMSG_str, \"YMSG\", 4) | yahoo->YMSG_str",
    "fn": "check_ymsg",
    "kind": "unknown",
    "line": 78,
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
   "entity_type": "ndpi_yahoo_header*",
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
   "control_structures": "WHILE:453,IF:455,IF:476,GOTO:477,IF:478,GOTO:479,IF:491,GOTO:492,SWITCH:494,BREAK:501,IF:506,BREAK:511",
   "fn": "_hb_buffer_deserialize_glyphs_json",
   "guard_count": 4,
   "guards": "p < pe | p < pe | p == pe",
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
   "code": "!parse_int  (tok, p, &pos.y_offset ) | parse_int  (tok, p, &pos.y_offset ) | &pos.y_offset | pos.y_offset",
   "site": {
    "file": "/src/harfbuzz/src/hb.hh",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "line": 541
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb.hh",
    "line": 460,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "tok",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_5ad761b94372.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/5ad761b943721c3541d0ca0472f34f7d54b89b5b/ARVO-42482101/report.log",
   "testcase_size": 1413
  },
  "input_reachability": [
   "buffer",
   "buf",
   "buf_len",
   "font"
  ],
  "osv_id": "ARVO-42482101",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "!parse_int  (tok, p, &pos.y_offset ) | parse_int  (tok, p, &pos.y_offset ) | &pos.y_offset | pos.y_offset",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "unknown",
    "line": 541,
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
   "control_structures": "WHILE:453,IF:455,IF:476,GOTO:477,IF:478,GOTO:479,IF:491,GOTO:492,SWITCH:494,BREAK:501,IF:506,BREAK:511",
   "fn": "_hb_buffer_deserialize_glyphs_json",
   "guard_count": 4,
   "guards": "p < pe | p < pe | p == pe",
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
   "code": "!parse_int  (tok, p, &pos.y_offset ) | parse_int  (tok, p, &pos.y_offset ) | &pos.y_offset | pos.y_offset",
   "site": {
    "file": "/src/harfbuzz/src/hb.hh",
    "fn": "BEInt<short, 2>::operator short() const",
    "line": 541
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb.hh",
    "line": 460,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "tok",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_5ad761b94372.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/5ad761b943721c3541d0ca0472f34f7d54b89b5b/ARVO-42482121/report.log",
   "testcase_size": 4004
  },
  "input_reachability": [
   "buffer",
   "buf",
   "buf_len",
   "font"
  ],
  "osv_id": "ARVO-42482121",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "!parse_int  (tok, p, &pos.y_offset ) | parse_int  (tok, p, &pos.y_offset ) | &pos.y_offset | pos.y_offset",
    "fn": "BEInt<short, 2>::operator short() const",
    "kind": "unknown",
    "line": 541,
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
   "control_structures": "IF:103,GOTO:104,IF:118,IF:121,GOTO:122,ELSE:129,IF:134,IF:137,GOTO:138,ELSE:145,IF:150,IF:153",
   "fn": "concat_hash_string",
   "guard_count": 14,
   "guards": "offset >= packet->payload_packet_len | len >= packet->payload_packet_len-offset-1 | offset >= packet->payload_packet_len",
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
   "code": "len = ntohl(*(u_int32_t*)&packet->payload[offset]) | ntohl(*(u_int32_t*)&packet->payload[offset]) | *(u_int32_t*)&packet->payload[offset] | (u_int32_t*)&packet->payload[offset]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/ssh.c",
    "fn": "concat_hash_string",
    "line": 99
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/ssh.c",
    "line": 99,
    "size": null,
    "type": "u_int32_t"
   },
   "kind": "struct",
   "name": "len",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_812505b56bb4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/812505b56bb4508bc42e1615d6425ad26444d3f8/ARVO-42482491/report.log",
   "testcase_size": 855
  },
  "input_reachability": [
   "packet"
  ],
  "osv_id": "ARVO-42482491",
  "project": "ndpi",
  "sites": [
   {
    "code": "len = ntohl(*(u_int32_t*)&packet->payload[offset]) | ntohl(*(u_int32_t*)&packet->payload[offset]) | *(u_int32_t*)&packet->payload[offset] | (u_int32_t*)&packet->payload[offset]",
    "fn": "concat_hash_string",
    "kind": "unknown",
    "line": 99,
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
   "entity_type": "u_int32_t",
   "is_signed": null,
   "ptr_origin": "assignment"
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
   "control_structures": "IF:102,ELSE:105,IF:105,ELSE:108,IF:110,IF:112,WHILE:116,IF:117,BREAK:124,ELSE:126,ELSE:129,ELSE:130",
   "fn": "search_valid_dns",
   "guard_count": 2,
   "guards": "x < flow->packet.payload_packet_len | x < flow->packet.payload_packet_len",
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
   "code": "flow->packet.payload[x] != '\\0' | flow->packet.payload[x] | flow->packet.payload | flow->packet",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/dns.c",
    "fn": "search_valid_dns",
    "line": 144
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/dns.c",
    "line": 84,
    "size": null,
    "type": "ndpi_flow_struct*"
   },
   "kind": "pointer",
   "name": "flow",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_5c52c00ea4ad.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/5c52c00ea4ad8afaebd5259bc53215a1ab41569f/ARVO-42482498/report.log",
   "testcase_size": 41
  },
  "input_reachability": [
   "flow",
   "payload_offset"
  ],
  "osv_id": "ARVO-42482498",
  "project": "ndpi",
  "sites": [
   {
    "code": "flow->packet.payload[x] != '\\0' | flow->packet.payload[x] | flow->packet.payload | flow->packet",
    "fn": "search_valid_dns",
    "kind": "unknown",
    "line": 144,
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
   "control_structures": "IF:389,IF:394,IF:400,IF:401,ELSE:405,IF:405,IF:412,IF:421,IF:425,FOR:426,IF:427,IF:435",
   "fn": "ndpi_search_irc_tcp",
   "guard_count": 6,
   "guards": "i < packet->parsed_lines | i < packet->parsed_lines | j < packet->line[i].len - 8",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 7
   },
   "code": "memcmp(&packet->line[i].ptr[j], \"sslchat\", 7) == 0 | memcmp(&packet->line[i].ptr[j], \"sslchat\", 7) | &packet->line[i].ptr[j] | packet->line[i].ptr[j]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/irc.c",
    "fn": "ndpi_search_irc_tcp",
    "line": 680
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/irc.c",
    "line": 370,
    "size": null,
    "type": "ndpi_packet_struct*"
   },
   "kind": "pointer",
   "name": "packet",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_a845e997209b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/a845e997209b987ef85a2562697d4d0522cb0c66/ARVO-42482590/report.log",
   "testcase_size": 256
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42482590",
  "project": "ndpi",
  "sites": [
   {
    "code": "memcmp(&packet->line[i].ptr[j], \"sslchat\", 7) == 0 | memcmp(&packet->line[i].ptr[j], \"sslchat\", 7) | &packet->line[i].ptr[j] | packet->line[i].ptr[j]",
    "fn": "ndpi_search_irc_tcp",
    "kind": "unknown",
    "line": 680,
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
    "file": "/src/leptonica/src/pix1.c",
    "fn": "pixCreateNoInit",
    "line": 345
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
   "control_structures": "IF:488,IF:499,IF:509,IF:517,IF:521,IF:525,ELSE:527,IF:527,ELSE:529,IF:529,ELSE:532,IF:536",
   "fn": "pixReadFromTiffStream",
   "guard_count": 3,
   "guards": "j < w | j < w | j < w",
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
   "code": "SET_DATA_BYTE(line, j, rval) | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(line) + (j)) ^ 3) | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(line) + (j)) ^ 3) | (l_uint8 *)((l_uintptr_t)((l_uint8 *)(line) + (j)) ^ 3)",
   "site": {
    "file": "/src/leptonica/src/tiffio.c",
    "fn": "pixReadFromTiffStream",
    "line": 627
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/leptonica/src/tiffio.c",
    "line": 482,
    "size": null,
    "type": "l_uint32*"
   },
   "kind": "pointer",
   "name": "line",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_7274a4a0cd69.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/7274a4a0cd69d20f4e8eec524ef3482852cb340d/ARVO-42482689/report.log",
   "testcase_size": 7728
  },
  "free_related": {
   "free_sites_in_func": [
    569,
    580,
    588,
    603
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "input_reachability": [
   "tif"
  ],
  "osv_id": "ARVO-42482689",
  "project": "leptonica",
  "sites": [
   {
    "code": "calloc(tiffbpl + 1, sizeof (l_uint8))",
    "fn": "pixReadFromTiffStream",
    "kind": "calloc",
    "line": 566,
    "origin": "cpg"
   },
   {
    "code": "free(linebuf)",
    "fn": "pixReadFromTiffStream",
    "kind": "free",
    "line": 569,
    "origin": "cpg"
   },
   {
    "code": "free(linebuf)",
    "fn": "pixReadFromTiffStream",
    "kind": "free",
    "line": 580,
    "origin": "cpg"
   },
   {
    "code": "calloc(tiffbpl + 1, sizeof (l_uint8))",
    "fn": "pixReadFromTiffStream",
    "kind": "calloc",
    "line": 584,
    "origin": "cpg"
   },
   {
    "code": "free(linebuf)",
    "fn": "pixReadFromTiffStream",
    "kind": "free",
    "line": 588,
    "origin": "cpg"
   },
   {
    "code": "free(linebuf)",
    "fn": "pixReadFromTiffStream",
    "kind": "free",
    "line": 603,
    "origin": "cpg"
   },
   {
    "code": "calloc((size_t)w * h, sizeof (l_uint32))",
    "fn": "pixReadFromTiffStream",
    "kind": "calloc",
    "line": 605,
    "origin": "cpg"
   },
   {
    "code": "SET_DATA_BYTE(line, j, rval) | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(line) + (j)) ^ 3) | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(line) + (j)) ^ 3) | (l_uint8 *)((l_uintptr_t)((l_uint8 *)(line) + (j)) ^ 3)",
    "fn": "pixReadFromTiffStream",
    "kind": "unknown",
    "line": 627,
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
   "entity_type": "l_uint32*",
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
   "control_structures": "IF:93,IF:94",
   "fn": "ih264d_get_bits_h264",
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
   "code": "UWORD32 * | ps_bitstrm->pu4_buffer | UWORD32 | (ps_bitstrm->u4_ofst) >> 5",
   "site": {
    "file": "/src/libavc/decoder/ih264d_bitstrm.c",
    "fn": "ih264d_get_bits_h264",
    "line": 94
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_bitstrm.c",
    "line": 94,
    "size": null,
    "type": "std.function"
   },
   "kind": "struct",
   "name": "pu4_buf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_748aa1e4597a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/748aa1e4597a2b0e4c20d30867879780648e0f6a/ARVO-42482784/report.log",
   "testcase_size": 257513
  },
  "input_reachability": [
   "ps_bitstrm",
   "u4_num_bits"
  ],
  "osv_id": "ARVO-42482784",
  "project": "libavc",
  "sites": [
   {
    "code": "UWORD32 * | ps_bitstrm->pu4_buffer | UWORD32 | (ps_bitstrm->u4_ofst) >> 5",
    "fn": "ih264d_get_bits_h264",
    "kind": "unknown",
    "line": 94,
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
   "entity_type": "std.function",
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