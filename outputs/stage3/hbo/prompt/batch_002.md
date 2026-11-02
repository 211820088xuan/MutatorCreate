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
   "cross_function": false,
   "site": {
    "file": "/src/net-snmp/snmplib/snmpv3.c",
    "fn": "setup_engineID",
    "line": 587
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
   "fn": "setup_engineID",
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
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/net-snmp/snmplib/snmpv3.c",
    "fn": "setup_engineID",
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
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-398053010/report.log",
   "testcase_size": 301
  },
  "input_reachability": [],
  "osv_id": "ARVO-398053010",
  "project": "net-snmp",
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
    "file": "/src/net-snmp/testing/fuzzing/snmp_parse_args_fuzzer.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 41
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
   "control_structures": "FOR:2366,SWITCH:2367,BREAK:2370,BREAK:2373,BREAK:2376,BREAK:2379,BREAK:2382,IF:2384,IF:2386,IF:2395,IF:2397",
   "fn": "snmp_in_options",
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
   "code": "cp = argv[optind++] | argv[optind++] | optind++",
   "site": {
    "file": "/src/net-snmp/snmplib/mib.c",
    "fn": "snmp_in_options",
    "line": 2396
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/net-snmp/snmplib/mib.c",
    "line": 2364,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "cp",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-398067543/report.log",
   "testcase_size": 151
  },
  "input_reachability": [
   "optarg",
   "argc",
   "argv"
  ],
  "osv_id": "ARVO-398067543",
  "project": "net-snmp",
  "sites": [
   {
    "code": "cp = argv[optind++] | argv[optind++] | optind++",
    "fn": "snmp_in_options",
    "kind": "unknown",
    "line": 2396,
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
    "file": "/src/net-snmp/snmplib/read_config.c",
    "fn": "read_config_read_octet_string_const",
    "line": 2051
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
   "fn": "usm_set_user_password",
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
    "width": 9
   },
   "code": null,
   "site": {
    "file": "/src/net-snmp/snmplib/snmpusm.c",
    "fn": "usm_set_user_password",
    "line": 4552
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
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_f720ed11acff.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/f720ed11acffa6425694ee3ac5144035aa094716/ARVO-399458050/report.log",
   "testcase_size": 1432
  },
  "input_reachability": [],
  "osv_id": "ARVO-399458050",
  "project": "net-snmp",
  "sites": [
   {
    "code": null,
    "fn": "usm_set_user_password",
    "kind": "unknown",
    "line": 4552,
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
    "file": "/src/readstat/src/spss/readstat_sav_parse.rl",
    "fn": "build_lookup_table",
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "sav_parse_long_variable_names_record",
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
    "file": "/src/readstat/src/spss/readstat_sav_parse.rl",
    "fn": "sav_parse_long_variable_names_record",
    "line": 121
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
   "cpg": "/root/gyx/mutator_create/cpg_files/readstat_24de678e9439.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/readstat/address/24de678e9439fff01b27c0bc8e8b745369888664/ARVO-420198855/report.log",
   "testcase_size": 237
  },
  "input_reachability": [],
  "osv_id": "ARVO-420198855",
  "project": "readstat",
  "sites": [
   {
    "code": null,
    "fn": "sav_parse_long_variable_names_record",
    "kind": "unknown",
    "line": 121,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 5792732f783158c66fb4f3756458ca24e46e827d)",
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
   "control_structures": "IF:941,IF:942,IF:945,FOR:950,IF:954,IF:958,IF:959,ELSE:962,ELSE:965,IF:965,IF:966,ELSE:969",
   "fn": "ndpi_check_http_server",
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
    "width": 11
   },
   "code": "snprintf(msg, sizeof(msg), \"Suspicious Agent [%s]\", serv | sizeof(msg)",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "fn": "ndpi_check_http_server",
    "line": 981
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 979,
    "size": null,
    "type": "char[64]"
   },
   "kind": "array",
   "name": "msg",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_a9433488cd09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/a9433488cd090a5da68179b52bb8c200d42649fa/ARVO-422832557/report.log",
   "testcase_size": 48
  },
  "input_reachability": [
   "server"
  ],
  "osv_id": "ARVO-422832557",
  "project": "ndpi",
  "sites": [
   {
    "code": "snprintf(msg, sizeof(msg), \"Suspicious Agent [%s]\", serv | sizeof(msg)",
    "fn": "ndpi_check_http_server",
    "kind": "unknown",
    "line": 981,
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
   "entity_type": "char[64]",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/harfbuzz/src/hb-blob.cc",
    "fn": "hb_blob_t::try_make_writable()",
    "line": 464
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
   "control_structures": "IF:757,FOR:763,ELSE:772,FOR:773,IF:776",
   "fn": "hb_ot_layout_collect_features",
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
   "code": "*scripts",
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-layout-gsub-table.hh",
    "fn": "OT::LigatureSubstFormat1::closure(OT::hb_closure_context_t*) const",
    "line": 778
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-layout-gsub-table.hh",
    "line": 752,
    "size": null,
    "type": "hb_tag_t*"
   },
   "kind": "pointer",
   "name": "scripts",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a26806801005.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a26806801005c28115ae9e48bdcf3bbbc1bcd767/ARVO-42470093/report.log",
   "testcase_size": 2648
  },
  "input_reachability": [
   "scripts"
  ],
  "osv_id": "ARVO-42470093",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "*scripts",
    "fn": "OT::LigatureSubstFormat1::closure(OT::hb_closure_context_t*) const",
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
   "entity_type": "hb_tag_t*",
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
    "line": 562
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
   "control_structures": "IF:952",
   "fn": "hb_buffer_set_direction",
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
   "code": "unlikely (hb_object_is_inert (buffer)) | hb_object_is_inert(buffer) | hb_object_is_inert(buffer)",
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "fn": "OT::Coverage::intersects(hb_set_t const*) const",
    "line": 952
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "line": 948,
    "size": null,
    "type": "hb_buffer_t*"
   },
   "kind": "pointer",
   "name": "buffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a26806801005.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a26806801005c28115ae9e48bdcf3bbbc1bcd767/ARVO-42470096/report.log",
   "testcase_size": 64
  },
  "input_reachability": [
   "buffer"
  ],
  "osv_id": "ARVO-42470096",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "unlikely (hb_object_is_inert (buffer)) | hb_object_is_inert(buffer) | hb_object_is_inert(buffer)",
    "fn": "OT::Coverage::intersects(hb_set_t const*) const",
    "kind": "unknown",
    "line": 952,
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
    "line": 341
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
   "fn": "r_bin_mdmp_get_mem_info",
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
    "file": "/src/radare2/libr/bin/format/mdmp/mdmp.c",
    "fn": "r_bin_mdmp_get_mem_info",
    "line": 33
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
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_eccc36f6b2df.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/eccc36f6b2df1d99bf0dcd09faccba8b3b892e0a/ARVO-42470250/report.log",
   "testcase_size": 1720
  },
  "input_reachability": [],
  "osv_id": "ARVO-42470250",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "r_bin_mdmp_get_mem_info",
    "kind": "unknown",
    "line": 33,
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
   "control_structures": "WHILE:654",
   "fn": "parse_space",
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
   "code": "(*pp)++ | *pp",
   "site": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "line": 655
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 652,
    "size": null,
    "type": "char**"
   },
   "kind": "pointer",
   "name": "pp",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_ca746f261e1e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/ca746f261e1e54cec2f9c8bc7a6f930491e19418/ARVO-42470379/report.log",
   "testcase_size": 256
  },
  "input_reachability": [
   "pp",
   "end"
  ],
  "osv_id": "ARVO-42470379",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "(*pp)++ | *pp",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "unknown",
    "line": 655,
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
   "entity_type": "char**",
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
    "line": 341
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
   "fn": "r_str_utf16_to_utf8",
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
    "file": "/src/radare2/libr/util/str.c",
    "fn": "r_str_utf16_to_utf8",
    "line": 2128
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
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_49b9ffcf9d21.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/49b9ffcf9d21745146407ee2701c25eb120a70e3/ARVO-42470538/report.log",
   "testcase_size": 527
  },
  "input_reachability": [],
  "osv_id": "ARVO-42470538",
  "project": "radare2",
  "sites": [
   {
    "code": null,
    "fn": "r_str_utf16_to_utf8",
    "kind": "unknown",
    "line": 2128,
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
   "fn": "format_generic_odp_key",
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
    "fn": "format_generic_odp_key",
    "line": 2527
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openvswitch_bc9bbc4ea264.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openvswitch/address/bc9bbc4ea2645e5bbb3c02d986f26fdc83283d72/ARVO-42470938/report.log",
   "testcase_size": 47
  },
  "input_reachability": [],
  "osv_id": "ARVO-42470938",
  "project": "openvswitch",
  "sites": [
   {
    "code": null,
    "fn": "format_generic_odp_key",
    "kind": "unknown",
    "line": 2527,
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:694",
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
    "width": 1
   },
   "code": "v = strtol (p, &pend, 0) | strtol (p, &pend, 0) | &pend",
   "site": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "fn": "BEInt<unsigned int, 4>::operator unsigned int() const",
    "line": 693
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-machinery.hh",
    "line": 688,
    "size": null,
    "type": "unsigned int"
   },
   "kind": "struct",
   "name": "v",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_4035158de46c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/4035158de46ce373b7521daf61c5b6df83312968/ARVO-42470972/report.log",
   "testcase_size": 28
  },
  "input_reachability": [
   "end"
  ],
  "osv_id": "ARVO-42470972",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "v = strtol (p, &pend, 0) | strtol (p, &pend, 0) | &pend",
    "fn": "BEInt<unsigned int, 4>::operator unsigned int() const",
    "kind": "unknown",
    "line": 693,
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
   "fn": "tag_parse",
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
    "file": "/src/libgit2/src/tag.c",
    "fn": "tag_parse",
    "line": 142
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471100/report.log",
   "testcase_size": 73
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471100",
  "project": "libgit2",
  "sites": [
   {
    "code": null,
    "fn": "tag_parse",
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
   "fn": "git_buf_vprintf",
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
    "width": 13
   },
   "code": null,
   "site": {
    "file": "/src/libgit2/src/buffer.c",
    "fn": "git_buf_vprintf",
    "line": 506
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471108/report.log",
   "testcase_size": 71
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471108",
  "project": "libgit2",
  "sites": [
   {
    "code": null,
    "fn": "git_buf_vprintf",
    "kind": "unknown",
    "line": 506,
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
   "fn": "prefixcmp",
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
    "file": "/src/libgit2/src/util.c",
    "fn": "prefixcmp",
    "line": 262
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libgit2/address/7615794c125698b50c48698782c6c602044b92a3/ARVO-42471111/report.log",
   "testcase_size": 63
  },
  "input_reachability": [],
  "osv_id": "ARVO-42471111",
  "project": "libgit2",
  "sites": [
   {
    "code": null,
    "fn": "prefixcmp",
    "kind": "unknown",
    "line": 262,
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