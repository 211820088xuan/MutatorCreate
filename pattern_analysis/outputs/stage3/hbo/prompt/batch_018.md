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
    "file": "/src/net-snmp/snmplib/tools.c",
    "fn": "snmp_realloc",
    "line": 182
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
   "fn": "snmp_add_var",
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
    "file": "/src/net-snmp/snmplib/snmp_api.c",
    "fn": "snmp_add_var",
    "line": 7604
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
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_05a463fd4ca6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/05a463fd4ca6ffa51698e00ddd6e30d0db1b5efd/ARVO-42500607/report.log",
   "testcase_size": 21
  },
  "input_reachability": [],
  "osv_id": "ARVO-42500607",
  "project": "net-snmp",
  "sites": [
   {
    "code": null,
    "fn": "snmp_add_var",
    "kind": "unknown",
    "line": 7604,
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
    "file": "/src/net-snmp/snmplib/tools.c",
    "fn": "snmp_realloc",
    "line": 182
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
   "control_structures": "IF:7286,IF:7289,IF:7292,SWITCH:7296,BREAK:7300,BREAK:7304,BREAK:7307,BREAK:7310,BREAK:7313,BREAK:7316,BREAK:7319,BREAK:7322",
   "fn": "snmp_add_var",
   "guard_count": 3,
   "guards": "ix >= (int) tint | ix >= (int)buf_len | buf != NULL",
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
   "code": "buf[ix] |= bit | buf[ix]",
   "site": {
    "file": "/src/net-snmp/snmplib/snmp_api.c",
    "fn": "snmp_add_var",
    "line": 7604
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/net-snmp/snmplib/snmp_api.c",
    "line": 7273,
    "size": null,
    "type": "u_char*"
   },
   "kind": "pointer",
   "name": "buf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/net-snmp_05a463fd4ca6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/net-snmp/address/05a463fd4ca6ffa51698e00ddd6e30d0db1b5efd/ARVO-42500699/report.log",
   "testcase_size": 21
  },
  "input_reachability": [
   "type"
  ],
  "osv_id": "ARVO-42500699",
  "project": "net-snmp",
  "sites": [
   {
    "code": "malloc(sizeof(oid) * MAX_OID_LEN)",
    "fn": "snmp_add_var",
    "kind": "malloc",
    "line": 7477,
    "origin": "cpg"
   },
   {
    "code": "malloc(256)",
    "fn": "snmp_add_var",
    "kind": "malloc",
    "line": 7549,
    "origin": "cpg"
   },
   {
    "code": "strdup(value)",
    "fn": "snmp_add_var",
    "kind": "strdup",
    "line": 7565,
    "origin": "cpg"
   },
   {
    "code": "buf[ix] |= bit | buf[ix]",
    "fn": "snmp_add_var",
    "kind": "unknown",
    "line": 7604,
    "origin": "report:crash"
   },
   {
    "code": "calloc(1, 4)",
    "fn": "snmp_add_var",
    "kind": "calloc",
    "line": 7648,
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
   "entity_type": "u_char*",
   "is_signed": null,
   "ptr_origin": "assignment"
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
    "line": 609
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/2945c0ded5ede79eae3cba3a5d12450ba2917fbc/ARVO-42501136/report.log",
   "testcase_size": 35337
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501136",
  "project": "matio",
  "sites": [
   {
    "code": "",
    "fn": "Mat_Open",
    "kind": "unknown",
    "line": 609,
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
   "fn": "trim_leading",
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
    "file": "/src/kamailio/src/core/trim.h",
    "fn": "trim_leading",
    "line": 59
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
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501143/report.log",
   "testcase_size": 17
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501143",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "trim_leading",
    "kind": "unknown",
    "line": 59,
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
   "fn": "parse_content_length",
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
    "file": "/src/kamailio/src/core/parser/parse_content.c",
    "fn": "parse_content_length",
    "line": 251
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
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501146/report.log",
   "testcase_size": 17
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501146",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "parse_content_length",
    "kind": "unknown",
    "line": 251,
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
   "fn": "parse_param_name",
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
    "file": "/src/kamailio/src/core/parser/parse_param.c",
    "fn": "parse_param_name",
    "line": 408
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
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501148/report.log",
   "testcase_size": 166
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501148",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "parse_param_name",
    "kind": "unknown",
    "line": 408,
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
   "fn": "q_memchr",
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
    "file": "/src/kamailio/src/core/ut.h",
    "fn": "q_memchr",
    "line": 422
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
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501162/report.log",
   "testcase_size": 147
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501162",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "q_memchr",
    "kind": "unknown",
    "line": 422,
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
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
   "fn": "parse_to_param",
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
    "file": "/src/kamailio/src/core/parser/parse_addr_spec.c",
    "fn": "parse_to_param",
    "line": 228
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
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501179/report.log",
   "testcase_size": 17
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501179",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "parse_to_param",
    "kind": "unknown",
    "line": 228,
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
   "guard_count": 7,
   "guards": "b < MRB_ENV_LEN(e) | b < MRB_ENV_LEN(e) | mid != missing",
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
   "code": "mid = syms[b] | syms[b]",
   "site": {
    "file": "/src/mruby/src/vm.c",
    "fn": "mrb_vm_exec",
    "line": 1468
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/mruby/src/vm.c",
    "line": 2820,
    "size": null,
    "type": "mrb_sym"
   },
   "kind": "struct",
   "name": "mid",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e60ddc431d24.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e60ddc431d242ede15e8f4d59a1a815fac532dc6/ARVO-42501369/report.log",
   "testcase_size": 210699
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501369",
  "project": "mruby",
  "sites": [
   {
    "code": "mid = syms[b] | syms[b]",
    "fn": "mrb_vm_exec",
    "kind": "unknown",
    "line": 1468,
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
   "entity_type": "mrb_sym",
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
   "control_structures": "IF:9,IF:10,WHILE:14,ELSE:18,IF:18,WHILE:19,ELSE:23",
   "fn": "value_move",
   "guard_count": 3,
   "guards": "s1 > s2 | s1 < s2 + n | s1 != s2",
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
   "code": "*s1++ = *s2++ | *s1++ | s1++ | *s2++",
   "site": {
    "file": "/src/mruby/src/value_array.h",
    "fn": "value_move",
    "line": 20
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/mruby/src/value_array.h",
    "line": 7,
    "size": null,
    "type": "mrb_value*"
   },
   "kind": "pointer",
   "name": "s1",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_a3fe04eda2b6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/a3fe04eda2b68b73486e5dbba2f7ebc6722f5e42/ARVO-42501420/report.log",
   "testcase_size": 11
  },
  "input_reachability": [
   "s1",
   "s2",
   "n"
  ],
  "osv_id": "ARVO-42501420",
  "project": "mruby",
  "sites": [
   {
    "code": "*s1++ = *s2++ | *s1++ | s1++ | *s2++",
    "fn": "value_move",
    "kind": "unknown",
    "line": 20,
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
    "file": null,
    "fn": "fuzzer::FuzzerDriver(int*, char***, int (*)(unsigned char const*, unsigned long)) (/out/fuzz_parse_msg+0x44a45e)",
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
   "fn": "parse_via_param",
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
    "file": "/src/kamailio/src/core/parser/parse_via.c",
    "fn": "parse_via_param",
    "line": 943
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
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_199f13a7dfac.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-42501431/report.log",
   "testcase_size": 154
  },
  "input_reachability": [],
  "osv_id": "ARVO-42501431",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "parse_via_param",
    "kind": "unknown",
    "line": 943,
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
   "control_structures": "FOR:228,IF:235,FOR:270,IF:277",
   "fn": "ih264d_fill_bs1_16x16mb_pslice",
   "guard_count": 2,
   "guards": "pv_cur_pic_addr0 != pv_nbr_pic_addr0 | pv_cur_pic_addr0 != pv_nbr_pic_addr0",
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
   "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
   "site": {
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "line": 222
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "line": 209,
    "size": null,
    "type": "void*"
   },
   "kind": "pointer",
   "name": "pv_cur_pic_addr0",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42501519/report.log",
   "testcase_size": 82
  },
  "input_reachability": [
   "ps_cur_mv_pred",
   "ppv_map_ref_idx_to_poc"
  ],
  "osv_id": "ARVO-42501519",
  "project": "libavc",
  "sites": [
   {
    "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "kind": "unknown",
    "line": 222,
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
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "calloc",
   "cross_function": true,
   "site": {
    "file": "/src/file/src/cdf.c",
    "fn": "cdf_calloc",
    "line": 121
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
   "control_structures": "IF:981,GOTO:983,IF:987,GOTO:988,IF:990,GOTO:992,IF:995,GOTO:996,IF:1001,GOTO:1002,IF:1004,GOTO:1005",
   "fn": "cdf_read_property_info",
   "guard_count": 8,
   "guards": "inp == NULL | i < sh.sh_properties | left < sizeof(uint32_t)",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 8425
   },
   "code": "DPRINTF((\"o=%\" SIZE_T_FORMAT \"u l=%d(%\"",
   "site": {
    "file": "/src/file/src/cdf.c",
    "fn": "cdf_read_property_info",
    "line": 1092
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/file/src/cdf.c",
    "line": 978,
    "size": null,
    "type": "size_t"
   },
   "kind": "struct",
   "name": "o4",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/file_a9c8d2a9493c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/a9c8d2a9493c4e0cd201db57801f3502e65c686c/ARVO-42502085/report.log",
   "testcase_size": 11264
  },
  "input_reachability": [
   "offs"
  ],
  "osv_id": "ARVO-42502085",
  "project": "file",
  "sites": [
   {
    "code": "DPRINTF((\"o=%\" SIZE_T_FORMAT \"u l=%d(%\"",
    "fn": "cdf_read_property_info",
    "kind": "unknown",
    "line": 1092,
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
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:207,IF:214,IF:249,IF:252,IF:260,IF:263,FOR:276,IF:277,IF:321",
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
   "code": "{HB_TAG ('h','n','g','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TR | HB_TAG ('h','n','g','l') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('n') & 0",
   "site": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "fn": "operator unsigned short",
    "line": 114
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
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_9247d24d7f41.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/9247d24d7f41f820d7ea79089b482410b927edc8/ARVO-42502435/report.log",
   "testcase_size": 919
  },
  "input_reachability": [],
  "osv_id": "ARVO-42502435",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "{HB_TAG ('h','n','g','l'), HB_AAT_LAYOUT_FEATURE_TYPE_TR | HB_TAG ('h','n','g','l') | (hb_tag_t)((((uint32_t)('h') & 0xFF) << 24) | (((uint32_ | (((uint32_t)('h') & 0xFF) << 24) | (((uint32_t)('n') & 0",
    "fn": "operator unsigned short",
    "kind": "unknown",
    "line": 114,
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
    "width": 4
   },
   "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON\t\t= 4",
   "site": {
    "file": "/src/harfbuzz/src/hb-serialize.hh",
    "fn": "embed<OT::MathValueRecord>",
    "line": 488
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_9247d24d7f41.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/9247d24d7f41f820d7ea79089b482410b927edc8/ARVO-42502450/report.log",
   "testcase_size": 982
  },
  "input_reachability": [],
  "osv_id": "ARVO-42502450",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_SLASHED_ZERO_ON\t\t= 4",
    "fn": "embed<OT::MathValueRecord>",
    "kind": "unknown",
    "line": 488,
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