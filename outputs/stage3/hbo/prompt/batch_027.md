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
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:89,SWITCH:95,BREAK:99,BREAK:105,SWITCH:108,FOR:119,FOR:124,BREAK:133,FOR:140,FOR:143,BREAK:151,FOR:156",
   "fn": "BM_Font",
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
    "width": 2
   },
   "code": "hb_set_next (set, &u) | &u",
   "site": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "fn": "operator unsigned short",
    "line": 120
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "line": 112,
    "size": null,
    "type": "hb_set_t*"
   },
   "kind": "pointer",
   "name": "set",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a975ec484246.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a975ec4842468e574484bdc310095fad780978fc/ARVO-42522572/report.log",
   "testcase_size": 2501
  },
  "input_reachability": [],
  "osv_id": "ARVO-42522572",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 115,
    "origin": "cpg"
   },
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 116,
    "origin": "cpg"
   },
   {
    "code": "hb_set_next (set, &u) | &u",
    "fn": "operator unsigned short",
    "kind": "unknown",
    "line": 120,
    "origin": "report:crash"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 137,
    "origin": "cpg"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 138,
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
   "entity_type": "hb_set_t*",
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
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)",
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
    "file": "/src/serenity/Userland/Libraries/LibGfx/ICC/TagTypes.cpp",
    "fn": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)",
    "line": 1011
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
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_9a7b3c145fcc.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/9a7b3c145fcc07302f5934037923b49e1a0bda32/ARVO-42522665/report.log",
   "testcase_size": 512
  },
  "input_reachability": [],
  "osv_id": "ARVO-42522665",
  "project": "serenity",
  "sites": [
   {
    "code": null,
    "fn": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)",
    "kind": "unknown",
    "line": 1011,
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
    "file": "/src/libredwg/src/in_dxf.c",
    "fn": "dxf_read_string",
    "line": 523
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
   "control_structures": "IF:2849,IF:2852,IF:2852,IF:2857,IF:2860,IF:2860,WHILE:2863,IF:2866,IF:2868,IF:2874,ELSE:2876,IF:2876",
   "fn": "bit_utf8_to_TU",
   "guard_count": 12,
   "guards": "len > 0xFFFE | len > 0 | c < 128",
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
   "code": "len > 0 && (c = *str++) | len > 0 | c = *str++ | *str++",
   "site": {
    "file": "/src/libredwg/src/bits.c",
    "fn": "bit_utf8_to_TU",
    "line": 2863
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 2846,
    "size": null,
    "type": "size_t"
   },
   "kind": "struct",
   "name": "len",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_5363f2eaaa83.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/5363f2eaaa83a7692652a019e475e9259ce49422/ARVO-42522842/report.log",
   "testcase_size": 58479
  },
  "input_reachability": [
   "str"
  ],
  "osv_id": "ARVO-42522842",
  "project": "libredwg",
  "sites": [
   {
    "code": "calloc (2, len + 1)",
    "fn": "bit_utf8_to_TU",
    "kind": "calloc",
    "line": 2856,
    "origin": "cpg"
   },
   {
    "code": "len > 0 && (c = *str++) | len > 0 | c = *str++ | *str++",
    "fn": "bit_utf8_to_TU",
    "kind": "unknown",
    "line": 2863,
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
   "api": "unknown:interceptor_skipped",
   "cross_function": false,
   "site": {
    "file": "/src/libredwg/src/bits.c",
    "fn": "bit_utf8_to_TU",
    "line": 2856
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
   "control_structures": "IF:2849,IF:2852,IF:2852,IF:2857,IF:2860,IF:2860,WHILE:2863,IF:2866,IF:2868,IF:2874,ELSE:2876,IF:2876",
   "fn": "bit_utf8_to_TU",
   "guard_count": 5,
   "guards": "c < 128 | c == '\\\\' | c == 'r'",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 2
   },
   "code": "wstr[i++] = c | wstr[i++] | i++",
   "site": {
    "file": "/src/libredwg/src/bits.c",
    "fn": "bit_utf8_to_TU",
    "line": 2883
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 2844,
    "size": null,
    "type": "BITCODE_TU"
   },
   "kind": "struct",
   "name": "wstr",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_5363f2eaaa83.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/5363f2eaaa83a7692652a019e475e9259ce49422/ARVO-42522843/report.log",
   "testcase_size": 27
  },
  "input_reachability": [
   "str"
  ],
  "osv_id": "ARVO-42522843",
  "project": "libredwg",
  "sites": [
   {
    "code": "calloc (2, len + 1)",
    "fn": "bit_utf8_to_TU",
    "kind": "calloc",
    "line": 2856,
    "origin": "cpg"
   },
   {
    "code": "wstr[i++] = c | wstr[i++] | i++",
    "fn": "bit_utf8_to_TU",
    "kind": "unknown",
    "line": 2883,
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
   "entity_type": "BITCODE_TU",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "MEM_read64",
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
   "code": "",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/common/mem.h",
    "fn": "MEM_read64",
    "line": 195
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_c4c8c7cb7f22.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/c4c8c7cb7f22323cda796575f699ad4c953b6661/ARVO-42523342/report.log",
   "testcase_size": 11408
  },
  "input_reachability": [],
  "osv_id": "ARVO-42523342",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "",
    "fn": "MEM_read64",
    "kind": "unknown",
    "line": 195,
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
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "fn": "hb_realloc_impl",
    "line": 55
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
   "fn": "_draw_funcs_create",
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
    "width": 2
   },
   "code": "hb_draw_funcs_set_move_to_func (draw_funcs, _hb_move_to,",
   "site": {
    "file": "/src/harfbuzz/src/hb-open-type.hh",
    "fn": "operator=",
    "line": 65
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-open-type.hh",
    "line": 64,
    "size": null,
    "type": "hb_draw_funcs_t*"
   },
   "kind": "pointer",
   "name": "draw_funcs",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a975ec484246.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a975ec4842468e574484bdc310095fad780978fc/ARVO-42523382/report.log",
   "testcase_size": 15886
  },
  "input_reachability": [],
  "osv_id": "ARVO-42523382",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "hb_draw_funcs_set_move_to_func (draw_funcs, _hb_move_to,",
    "fn": "operator=",
    "kind": "unknown",
    "line": 65,
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
   "entity_type": "hb_draw_funcs_t*",
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
    "fn": "void* std::__1::__libcpp_operator_new<unsigned long>(unsigned long)",
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
   "fn": "vips_foreign_load_heif_build",
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
    "file": "/src/libvips/libvips/foreign/heifload.c",
    "fn": "vips_foreign_load_heif_build",
    "line": 268
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42523472/report.log",
   "testcase_size": 10997
  },
  "input_reachability": [],
  "osv_id": "ARVO-42523472",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "vips_foreign_load_heif_build",
    "kind": "unknown",
    "line": 268,
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
    "fn": "decode_preR13_header_variables",
    "line": 159
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
   "control_structures": "FOR:1384,IF:1387,ELSE:1389,IF:1389,ELSE:1397,IF:1397,IF:1400,FOR:1402,IF:1403,BREAK:1406,IF:1409,ELSE:1412",
   "fn": "json_write_TF",
   "guard_count": 1,
   "guards": "j < len",
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
   "code": "src[j]",
   "site": {
    "file": "/src/libredwg/src/out_json.c",
    "fn": "json_write_TF",
    "line": 1403
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/out_json.c",
    "line": 1378,
    "size": null,
    "type": "BITCODE_TF"
   },
   "kind": "struct",
   "name": "src",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_c8098abda7cd.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/c8098abda7cd419dd034c5f30c22b679039baa95/ARVO-42524318/report.log",
   "testcase_size": 6163
  },
  "input_reachability": [
   "src",
   "len"
  ],
  "osv_id": "ARVO-42524318",
  "project": "libredwg",
  "sites": [
   {
    "code": "src[j]",
    "fn": "json_write_TF",
    "kind": "unknown",
    "line": 1403,
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
   "entity_type": "BITCODE_TF",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "fn": "pcap_check_header",
    "line": 405
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
   "control_structures": "IF:2416,ELSE:2419,IF:2422,SWITCH:2424,BREAK:2429,BREAK:2436,IF:2442,BREAK:2446,IF:2451,IF:2454,BREAK:2459,IF:2464",
   "fn": "visit",
   "guard_count": 11,
   "guards": "tot > 0 | tot > 0 | tot > 0",
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
   "code": "getTotalNumAlertedOutgoingFlows()",
   "site": {
    "file": "/src/ntopng/src/NetworkInterface.cpp",
    "fn": "NetworkInterface::dissectPacket(unsigned int, bool, unsigned char*, pcap_pkthdr const*, unsigned char const*, unsigned short*, Host**, Host**, Flow**)",
    "line": 2445
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ntopng/src/NetworkInterface.cpp",
    "line": 2414,
    "size": null,
    "type": "u_int64_t"
   },
   "kind": "struct",
   "name": "tot",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42524653/report.log",
   "testcase_size": 164
  },
  "input_reachability": [],
  "osv_id": "ARVO-42524653",
  "project": "ntopng",
  "sites": [
   {
    "code": "getTotalNumAlertedOutgoingFlows()",
    "fn": "NetworkInterface::dissectPacket(unsigned int, bool, unsigned char*, pcap_pkthdr const*, unsigned char const*, unsigned short*, Host**, Host**, Flow**)",
    "kind": "unknown",
    "line": 2445,
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
   "entity_type": "u_int64_t",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "fn": "grow_buffer",
    "line": 426
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
   "fn": "print",
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
   "code": "Utils::intoaV4(dst_ip, buf2ip, sizeof(buf2ip)) | sizeof(buf2ip)",
   "site": {
    "file": "/src/ntopng/src/ICMPinfo.cpp",
    "fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)",
    "line": 100
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "dst_ip",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42524654/report.log",
   "testcase_size": 78
  },
  "input_reachability": [
   "msg"
  ],
  "osv_id": "ARVO-42524654",
  "project": "ntopng",
  "sites": [
   {
    "code": "Utils::intoaV4(dst_ip, buf2ip, sizeof(buf2ip)) | sizeof(buf2ip)",
    "fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)",
    "kind": "unknown",
    "line": 100,
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
    "file": "/src/openexr/src/lib/OpenEXRCore/coding.c",
    "fn": "internal_decode_alloc_buffer",
    "line": 261
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
   "fn": "exr_uncompress_buffer",
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
    "file": "/src/openexr/src/lib/OpenEXRCore/compression.c",
    "fn": "exr_uncompress_buffer",
    "line": 106
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openexr_7c40603eb281.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openexr/address/7c40603eb2812148c6a99fbb6ee07533395fdadb/ARVO-42524709/report.log",
   "testcase_size": 197
  },
  "input_reachability": [],
  "osv_id": "ARVO-42524709",
  "project": "openexr",
  "sites": [
   {
    "code": null,
    "fn": "exr_uncompress_buffer",
    "kind": "unknown",
    "line": 106,
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
   "fn": "H5MM_xstrdup",
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
    "width": 5
   },
   "code": null,
   "site": {
    "file": "/src/hdf5/src/H5MM.c",
    "fn": "H5MM_xstrdup",
    "line": 172
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42524740/report.log",
   "testcase_size": 1032
  },
  "input_reachability": [],
  "osv_id": "ARVO-42524740",
  "project": "hdf5",
  "sites": [
   {
    "code": null,
    "fn": "H5MM_xstrdup",
    "kind": "unknown",
    "line": 172,
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
   "control_structures": "WHILE:94,IF:95",
   "fn": "ndpi_check_punycode_string",
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
   "code": "buffer[i+3] == '-' | buffer[i+3] | i+3",
   "site": {
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "fn": "ndpi_check_punycode_string",
    "line": 98
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "line": 91,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "buffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_998bedbbb731.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/998bedbbb731e369451298b891ffeb37245a7d96/ARVO-42524849/report.log",
   "testcase_size": 48
  },
  "input_reachability": [
   "buffer"
  ],
  "osv_id": "ARVO-42524849",
  "project": "ndpi",
  "sites": [
   {
    "code": "buffer[i+3] == '-' | buffer[i+3] | i+3",
    "fn": "ndpi_check_punycode_string",
    "kind": "unknown",
    "line": 98,
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
   "call_chain"
  ],
  "context": {
   "fn": "read_u8",
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
   "code": "*(m_data_ptr++) | m_data_ptr++",
   "site": {
    "file": "/src/serenity/Userland/Libraries/LibGfx/BMPLoader.cpp",
    "fn": "read_u8",
    "line": 183
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "m_data_ptr",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_ed84a6f6ee4a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/ed84a6f6ee4a620e936c53f91407cd04fe2b7106/ARVO-42524929/report.log",
   "testcase_size": 54
  },
  "input_reachability": [],
  "osv_id": "ARVO-42524929",
  "project": "serenity",
  "sites": [
   {
    "code": "*(m_data_ptr++) | m_data_ptr++",
    "fn": "read_u8",
    "kind": "unknown",
    "line": 183,
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
    "file": "/src/wolf-ssl-ssh-fuzzers/oss-fuzz/projects/wolf-ssl-ssh/fuzzers/include/fuzzers/shared.h",
    "fn": "wolfCrypt_custom_malloc",
    "line": 189
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
    "width": 9
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_b2a6203ec01f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/b2a6203ec01fcc5d55ab37b3d0e85ab160e962d4/ARVO-42524965/report.log",
   "testcase_size": 260
  },
  "input_reachability": [],
  "osv_id": "ARVO-42524965",
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