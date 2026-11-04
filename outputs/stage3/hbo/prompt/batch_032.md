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
  "osv_id": "ARVO-42532420",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "eq",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/string.c",
    "line": 619,
    "size": null,
    "type": "uint32_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/allocf.c",
    "line": 28
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 619,
    "fn": "mrb_memsearch_ss",
    "code": "eq = (*s0 ^ first) | (*s1 ^ last) | (*s0 ^ first) | (*s1 ^ last) | *s0 ^ first | *s0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mrb_memsearch_ss",
    "file": "/src/mruby/src/string.c",
    "line": 619
   },
   "code": "eq = (*s0 ^ first) | (*s1 ^ last) | (*s0 ^ first) | (*s1 ^ last) | *s0 ^ first | *s0",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_memsearch_ss",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:602,IF:605,IF:606,FOR:618,WHILE:623,IF:624,IF:626"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint32_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "xs",
   "m",
   "ys",
   "n"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e859b430cc74ccc14ad3e97c4178c944dde55318/ARVO-42532420/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e859b430cc74.cpg",
   "testcase_size": 40
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "mrb_memsearch_ss--mrb_memsearch--mrb_str_split_m"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "eq = (*s0 ^ first) ",
     "line": 619
    }
   ],
   "entity_decl": {
    "line": 619,
    "type": "uint32_t"
   },
   "entity_name_cpg": "eq",
   "func_lines": [
    577,
    640
   ],
   "func_params": {
    "names": [
     "xs",
     "m",
     "ys",
     "n"
    ],
    "types": [
     "unsigned char*",
     "long",
     "unsigned char*",
     "long"
    ]
   },
   "guards": [
    {
     "code": "(p - ys) < m",
     "line": 605
    },
    {
     "code": "memcmp(p, xs, m) == 0",
     "line": 606
    },
    {
     "code": "i < n",
     "line": 618
    },
    {
     "code": "memcmp(substr, xs + 1, m - 2) == 0",
     "line": 626
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "eq = (*s0 ^ first) ",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "(*s0 ^ first) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "*s0 ^ first",
     "name": "<operator>.xor",
     "nargs": 2
    },
    {
     "code": "*s0",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*s1 ^ last",
     "name": "<operator>.xor",
     "nargs": 2
    },
    {
     "code": "*s1",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "eq",
    "s0",
    "first",
    "s1",
    "last"
   ],
   "osv_id": "ARVO-42532420",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_memsearch_ss"
  }
 },
 {
  "osv_id": "ARVO-42532659",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "eq",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/string.c",
    "line": 619,
    "size": null,
    "type": "uint32_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/allocf.c",
    "line": 28
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 619,
    "fn": "mrb_memsearch_ss",
    "code": "eq = (*s0 ^ first) | (*s1 ^ last) | (*s0 ^ first) | (*s1 ^ last) | *s0 ^ first | *s0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "mrb_memsearch_ss",
    "file": "/src/mruby/src/string.c",
    "line": 619
   },
   "code": "eq = (*s0 ^ first) | (*s1 ^ last) | (*s0 ^ first) | (*s1 ^ last) | *s0 ^ first | *s0",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "mrb_memsearch_ss",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:602,IF:605,IF:606,FOR:618,WHILE:623,IF:624,IF:626"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint32_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "xs",
   "m",
   "ys",
   "n"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/e859b430cc74ccc14ad3e97c4178c944dde55318/ARVO-42532659/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_e859b430cc74.cpg",
   "testcase_size": 41
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "mrb_memsearch_ss--mrb_memsearch--mrb_str_split_m"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "eq = (*s0 ^ first) ",
     "line": 619
    }
   ],
   "entity_decl": {
    "line": 619,
    "type": "uint32_t"
   },
   "entity_name_cpg": "eq",
   "func_lines": [
    577,
    640
   ],
   "func_params": {
    "names": [
     "xs",
     "m",
     "ys",
     "n"
    ],
    "types": [
     "unsigned char*",
     "long",
     "unsigned char*",
     "long"
    ]
   },
   "guards": [
    {
     "code": "(p - ys) < m",
     "line": 605
    },
    {
     "code": "memcmp(p, xs, m) == 0",
     "line": 606
    },
    {
     "code": "i < n",
     "line": 618
    },
    {
     "code": "memcmp(substr, xs + 1, m - 2) == 0",
     "line": 626
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "eq = (*s0 ^ first) ",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "(*s0 ^ first) ",
     "name": "<operator>.or",
     "nargs": null
    },
    {
     "code": "*s0 ^ first",
     "name": "<operator>.xor",
     "nargs": 2
    },
    {
     "code": "*s0",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*s1 ^ last",
     "name": "<operator>.xor",
     "nargs": 2
    },
    {
     "code": "*s1",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "eq",
    "s0",
    "first",
    "s1",
    "last"
   ],
   "osv_id": "ARVO-42532659",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "mrb_memsearch_ss"
  }
 },
 {
  "osv_id": "ARVO-42532796",
  "project": "jq",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "s",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 95,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "jv_mem_alloc",
    "file": "/src/jq/src/jv_alloc.c",
    "line": 141
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 96,
    "fn": "validate_relpath",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "validate_relpath",
    "file": "/src/jq/src/linker.c",
    "line": 96
   },
   "code": "strchr(s, '\\\\')",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "validate_relpath",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/jq/address/bfb7fd570f521ef832fe1c3bca0e05abd398284c/ARVO-42532796/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/jq_bfb7fd570f52.cpg",
   "testcase_size": 24
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "strchr--validate_relpath--load_module_meta"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*s = jv_string_value(name)",
     "line": 95
    }
   ],
   "entity_decl": {
    "line": 95,
    "type": "char*"
   },
   "entity_name_cpg": "s",
   "func_lines": [
    94,
    122
   ],
   "func_params": {
    "names": [
     "name"
    ],
    "types": [
     "jv"
    ]
   },
   "guards": [
    {
     "code": "i < jv_len__",
     "line": 102
    },
    {
     "code": "i > 0",
     "line": 110
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "strchr(s, '\\\\')",
     "name": "strchr",
     "nargs": 2
    }
   ],
   "line_ids": [
    "s"
   ],
   "osv_id": "ARVO-42532796",
   "sites": [
    {
     "args": "name",
     "callee": "jv_free",
     "code": "jv_free(name)",
     "line": 98
    },
    {
     "args": "x",
     "callee": "jv_free",
     "code": "jv_free(x)",
     "line": 104
    },
    {
     "args": "components",
     "callee": "jv_free",
     "code": "jv_free(components)",
     "line": 105
    },
    {
     "args": "name",
     "callee": "jv_free",
     "code": "jv_free(name)",
     "line": 107
    },
    {
     "args": "x",
     "callee": "jv_free",
     "code": "jv_free(x)",
     "line": 111
    },
    {
     "args": "components",
     "callee": "jv_free",
     "code": "jv_free(components)",
     "line": 112
    },
    {
     "args": "name",
     "callee": "jv_free",
     "code": "jv_free(name)",
     "line": 115
    },
    {
     "args": "x",
     "callee": "jv_free",
     "code": "jv_free(x)",
     "line": 118
    },
    {
     "args": "components",
     "callee": "jv_free",
     "code": "jv_free(components)",
     "line": 120
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "validate_relpath"
  }
 },
 {
  "osv_id": "ARVO-42532953",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/src/string.c",
    "line": 626,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/allocf.c",
    "line": 28
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 647,
    "fn": "memsearch_swar",
    "code": "memcmp(p+1, xs+1, m-1) == 0 | memcmp(p+1, xs+1, m-1) | p+1 | xs+1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "memsearch_swar",
    "file": "/src/mruby/src/string.c",
    "line": 647
   },
   "code": "memcmp(p+1, xs+1, m-1) == 0 | memcmp(p+1, xs+1, m-1) | p+1 | xs+1",
   "access": {
    "dir": "READ",
    "width": 3,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "memsearch_swar",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "p<e | p == NULL | len < m",
   "guard_count": 3,
   "control_structures": "FOR:613,FOR:623,IF:624,IF:627,IF:640,FOR:643,IF:646,BREAK:646,IF:647"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "xs",
   "m",
   "ys",
   "n"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/abcad36bae43f2c7cb8c2b1753dc94ab4cf25366/ARVO-42532953/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_abcad36bae43.cpg",
   "testcase_size": 52
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--bcmp--memsearch_swar"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* p = s0 + idx + 1",
     "line": 626
    },
    {
     "code": "*p = s0",
     "line": 641
    },
    {
     "code": "p = (const char*)memchr(p, *xs, len)",
     "line": 645
    }
   ],
   "entity_decl": {
    "line": 641,
    "type": "char*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    580,
    653
   ],
   "func_params": {
    "names": [
     "xs",
     "m",
     "ys",
     "n"
    ],
    "types": [
     "char*",
     "long",
     "char*",
     "long"
    ]
   },
   "guards": [
    {
     "code": "i < lim",
     "line": 613
    },
    {
     "code": "memcmp(p, xs + 1, m - 2) == 0",
     "line": 627
    },
    {
     "code": "i+m < n",
     "line": 640
    },
    {
     "code": "p<e",
     "line": 643
    },
    {
     "code": "p == NULL",
     "line": 646
    },
    {
     "code": "len < m",
     "line": 646
    },
    {
     "code": "memcmp(p+1, xs+1, m-1) == 0",
     "line": 647
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "memcmp(p+1, xs+1, m-1) == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "memcmp(p+1, xs+1, m-1)",
     "name": "memcmp",
     "nargs": 3
    },
    {
     "code": "p+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "xs+1",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "m-1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "(mrb_int)(p - ys)",
     "name": "<operator>.pointerCall",
     "nargs": 1
    },
    {
     "code": "p - ys",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "p",
    "xs",
    "m",
    "mrb_int",
    "ys"
   ],
   "osv_id": "ARVO-42532953",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "memsearch_swar"
  }
 },
 {
  "osv_id": "ARVO-42533083",
  "project": "readstat",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ctx",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 682,
    "type": "sav_ctx_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "readstat_malloc",
    "file": "/src/readstat/src/readstat_malloc.c",
    "line": 12
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 712,
    "fn": "sav_process_row",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "sav_process_row",
    "file": "/src/readstat/src/spss/readstat_sav_read.c",
    "line": 712
   },
   "code": "ctx->raw_string[raw_str_used++] = c",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sav_process_row",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/readstat/address/4d6c56413372f389fc29cecbe98e23a5c44a7296/ARVO-42533083/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/readstat_4d6c56413372.cpg",
   "testcase_size": 337
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "sav_process_row--sav_read_uncompressed_data--sav_read_data"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ctx->raw_string[raw_str_used++] = c",
     "line": 712
    }
   ],
   "entity_decl": {
    "line": 682,
    "type": "sav_ctx_t*"
   },
   "entity_name_cpg": "ctx",
   "func_lines": [
    682,
    764
   ],
   "func_params": {
    "names": [
     "buffer",
     "buffer_len",
     "ctx"
    ],
    "types": [
     "unsigned char*",
     "size_t",
     "sav_ctx_t*"
    ]
   },
   "guards": [
    {
     "code": "data_offset < buffer_len",
     "line": 697
    },
    {
     "code": "col < ctx->var_index",
     "line": 697
    },
    {
     "code": "var_index < ctx->var_index",
     "line": 697
    },
    {
     "code": "offset > 31",
     "line": 701
    },
    {
     "code": "var_info->type == READSTAT_TYPE_STRING",
     "line": 705
    },
    {
     "code": "i<8",
     "line": 710
    },
    {
     "code": "++offset == col_info->width",
     "line": 718
    },
    {
     "code": "++segment_offset < var_info->n_segments",
     "line": 719
    },
    {
     "code": "segment_offset == var_info->n_segments",
     "line": 725
    },
    {
     "code": "retval != READSTAT_OK",
     "line": 729
    },
    {
     "code": "ctx->handle.value(ctx->current_row, ctx->variables[var_info->index],",
     "line": 732
    },
    {
     "code": "var_info->type == READSTAT_TYPE_DOUBLE",
     "line": 742
    },
    {
     "code": "ctx->handle.value(ctx->current_row, ctx->variables[var_info->index],",
     "line": 750
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "ctx->raw_string[raw_str_used++] = c",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "ctx->raw_string[raw_str_used++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "ctx->raw_string",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "raw_str_used++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "ctx",
    "raw_str_used",
    "c"
   ],
   "osv_id": "ARVO-42533083",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sav_process_row"
  }
 },
 {
  "osv_id": "ARVO-42533286",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "read_bits",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_cabac.c",
    "line": 458,
    "size": null,
    "type": "UWORD32"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "mvcd_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/mvc_dec_fuzzer.cpp",
    "line": 61
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 412,
    "fn": "ih264d_read_coeff4x4_cabac",
    "code": "NEXTBITS(read_bits, u4_offset, pu4_buffer, CABAC_BITS_TO | UWORD32 * | UWORD32 | (u4_offset) >> 5",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ih264d_read_coeff4x4_cabac",
    "file": "/src/libavc/decoder/ih264d_parse_cabac.c",
    "line": 412
   },
   "code": "NEXTBITS(read_bits, u4_offset, pu4_buffer, CABAC_BITS_TO | UWORD32 * | UWORD32 | (u4_offset) >> 5",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ih264d_read_coeff4x4_cabac",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:116,IF:119,IF:122,IF:135,IF:145,IF:151,ELSE:156,DO:164,IF:194,IF:198,IF:203,IF:223"
  },
  "call_chain": [],
  "types": {
   "entity_type": "UWORD32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ps_bitstrm",
   "u4_ctxcat",
   "ps_ctxt_sig_coeff",
   "ps_dec",
   "ps_ctxt_coded"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/37beb9729249a1cde472545e2a19d80660e40edc/ARVO-42533286/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_37beb9729249.cpg",
   "testcase_size": 1048576
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "ih264d_read_coeff4x4_cabac--ih264d_cabac_parse_8x8block--ih264d_parse_residual4x4_cabac"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "read_bits = pu4_buf[u4_word_off++] << u4_bit_off",
     "line": 203
    },
    {
     "code": "read_bits = read_bits >> (32 - u4_clz)",
     "line": 203
    },
    {
     "code": "read_bits = pu4_buf[u4_word_off++] << u4_bit_off",
     "line": 412
    },
    {
     "code": "read_bits = read_bits >> (32 - 23)",
     "line": 412
    },
    {
     "code": "read_bits = pu4_buf[u4_word_off++] << u4_bit_off",
     "line": 462
    },
    {
     "code": "read_bits = read_bits >> (32 - 23)",
     "line": 462
    }
   ],
   "entity_decl": {
    "line": 201,
    "type": "UWORD32"
   },
   "entity_name_cpg": "read_bits",
   "func_lines": [
    64,
    568
   ],
   "func_params": {
    "names": [
     "ps_bitstrm",
     "u4_ctxcat",
     "ps_ctxt_sig_coeff",
     "ps_dec",
     "ps_ctxt_coded"
    ],
    "types": [
     "dec_bit_stream_t*",
     "UWORD32",
     "bin_ctxt_model_t*",
     "dec_struct_t*",
     "bin_ctxt_model_t*"
    ]
   },
   "guards": [
    {
     "code": "u4_code_int_range < ONE_RIGHT_SHIFTED_BY_8",
     "line": 119
    },
    {
     "code": "u4_ctxcat == CHROMA_AC_CTXCAT",
     "line": 145
    },
    {
     "code": "u4_ctxcat == LUMA_AC_CTXCAT",
     "line": 145
    },
    {
     "code": "u4_ctxcat == CHROMA_DC_CTXCAT",
     "line": 151
    },
    {
     "code": "u4_code_int_range < ONE_RIGHT_SHIFTED_BY_14",
     "line": 198
    },
    {
     "code": "uc_bin == 1",
     "line": 272
    },
    {
     "code": "i < uc_last_coeff_idx",
     "line": 280
    },
    {
     "code": "u4_code_int_range < ONE_RIGHT_SHIFTED_BY_9",
     "line": 366
    },
    {
     "code": "u4_value < UCOFF_LEVEL",
     "line": 385
    },
    {
     "code": "ui_prefix == UCOFF_LEVEL",
     "line": 391
    },
    {
     "code": "bits_to_flush < CABAC_BITS_TO_READ",
     "line": 441
    },
    {
     "code": "u4_value > 0",
     "line": 451
    },
    {
     "code": "u4_value > 10",
     "line": 456
    },
    {
     "code": "bits_to_flush < u1_max_bins",
     "line": 502
    },
    {
     "code": "i2_abs_lvl > 1",
     "line": 519
    },
    {
     "code": "u1_abs_level_equal1 < 4",
     "line": 526
    },
    {
     "code": "u1_abs_level_gt1 < 4",
     "line": 529
    },
    {
     "code": "num_sig_coeffs > 0",
     "line": 550
    }
   ],
   "line_call_count": 17,
   "line_calls": [
    {
     "code": "NEXTBITS(read_bits, u4_offset, pu4_buffer, CABAC_BITS_TO_READ)",
     "name": "NEXTBITS",
     "nargs": 3
    },
    {
     "code": "UWORD32 *",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "UWORD32",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(u4_offset) >> 5",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "UWORD32",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(u4_offset) & 0x1F",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "read_bits = pu4_buf[u4_word_off++] << u4_bit_off",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off++] << u4_bit_off",
     "name": "<operator>.shiftLeft",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "u4_word_off++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "read_bits ",
     "name": "<operators>.assignmentOr",
     "nargs": null
    },
    {
     "code": "pu4_buf[u4_word_off] >> (32 - u4_bit_off)",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "pu4_buf[u4_word_off]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "32 - u4_bit_off",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "read_bits = read_bits >> (32 - 23)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "read_bits >> (32 - 23)",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "32 - 23",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "read_bits",
    "u4_offset",
    "pu4_buffer",
    "pu4_buf",
    "u4_word_off",
    "u4_bit_off"
   ],
   "osv_id": "ARVO-42533286",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ih264d_read_coeff4x4_cabac"
  }
 },
 {
  "osv_id": "ARVO-42533348",
  "project": "gpac",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "gf_malloc",
    "file": "/src/gpac/src/utils/alloc.c",
    "line": 150
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 300,
    "fn": "gf_gz_decompress_payload_ex",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "gf_gz_decompress_payload_ex",
    "file": "/src/gpac/src/utils/base_encoding.c",
    "line": 300
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "gf_gz_decompress_payload_ex",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/gpac/address/f8a41b2aea6bf516a923ce7fe5fa69ff477e9f7a/ARVO-42533348/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/gpac_f8a41b2aea6b.cpg",
   "testcase_size": 2861
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "gf_gz_decompress_payload_ex--gf_isom_box_parse_ex--gf_isom_box_array_read"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "gf_gz_decompress_payload_ex"
  }
 },
 {
  "osv_id": "ARVO-42533590",
  "project": "gpac",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "gf_malloc",
    "file": "/src/gpac/src/utils/alloc.c",
    "line": 150
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2189,
    "fn": "gf_strmemstr",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "gf_strmemstr",
    "file": "/src/gpac/src/utils/error.c",
    "line": 2189
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 13,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "gf_strmemstr",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/gpac/address/d9da11ec2e3b5f223b303bdcd3f208c000958987/ARVO-42533590/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/gpac_d9da11ec2e3b.cpg",
   "testcase_size": 6119
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "memchr--gf_strmemstr--txtin_probe_data"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "gf_strmemstr"
  }
 },
 {
  "osv_id": "ARVO-42534463",
  "project": "lcms",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "t",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/lcms/src/cmscgats.c",
    "line": 1550,
    "size": null,
    "type": "TABLE*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "_cmsMallocDefaultFn",
    "file": "/src/lcms/src/cmserr.c",
    "line": 97
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "it8",
   "size_expr_cpg_callee": "AllocateDataFormat"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1561,
    "fn": "SetDataFormat",
    "code": "t->DataFormat[n] = AllocString(it8, label) | t->DataFormat[n] | t->DataFormat | AllocString(it8, label)",
    "origin": "report:crash",
    "args": "it8 ;; label"
   }
  ],
  "crash": {
   "site": {
    "fn": "SetDataFormat",
    "file": "/src/lcms/src/cmscgats.c",
    "line": 1561
   },
   "code": "t->DataFormat[n] = AllocString(it8, label) | t->DataFormat[n] | t->DataFormat | AllocString(it8, label)",
   "access": {
    "dir": "WRITE",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "SetDataFormat",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "n > t -> nSamples",
   "guard_count": 1,
   "control_structures": "IF:1552,IF:1555,IF:1560"
  },
  "call_chain": [],
  "types": {
   "entity_type": "TABLE*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "it8",
   "n",
   "label"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lcms/address/1c667a762c4272ec970a2dd6f945836c52f35720/ARVO-42534463/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_1c667a762c42.cpg",
   "testcase_size": 4244
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "SetDataFormat--DataFormatSection--ParseIT8"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* t = GetTable(it8)",
     "line": 1550
    },
    {
     "code": "t->DataFormat[n] = AllocString(it8, label)",
     "line": 1561
    }
   ],
   "entity_decl": {
    "line": 1550,
    "type": "TABLE*"
   },
   "entity_name_cpg": "t",
   "func_lines": [
    1547,
    1565
   ],
   "func_params": {
    "names": [
     "it8",
     "n",
     "label"
    ],
    "types": [
     "cmsIT8*",
     "int",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "n > t -> nSamples",
     "line": 1555
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "t->DataFormat[n] = AllocString(it8, label)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "t->DataFormat[n]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "t->DataFormat",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "AllocString(it8, label)",
     "name": "AllocString",
     "nargs": 2
    }
   ],
   "line_ids": [
    "t",
    "n",
    "it8",
    "label"
   ],
   "osv_id": "ARVO-42534463",
   "sites": [
    {
     "args": "it8",
     "callee": "AllocateDataFormat",
     "code": "AllocateDataFormat(it8)",
     "line": 1553
    },
    {
     "args": "it8 ;; label",
     "callee": "AllocString",
     "code": "AllocString(it8, label)",
     "line": 1561
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "SetDataFormat"
  }
 },
 {
  "osv_id": "ARVO-42534483",
  "project": "matio",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "out_data",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/matio/src/mat.c",
    "line": 1672,
    "size": null,
    "type": "mat_complex_split_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "ReadNextFunctionHandle",
    "file": "/src/matio/src/mat5.c",
    "line": 1890
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "Mat_VarCalloc"
  },
  "sites": [
   {
    "code": "malloc(len)",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1498,
    "origin": "cpg",
    "args": "len"
   },
   {
    "code": "malloc(in->rank * sizeof(*out->dims))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1503,
    "origin": "cpg",
    "args": "in->rank * sizeof(*out->dims)"
   },
   {
    "code": "calloc(in->internal->num_fields, sizeof(*in->internal->fieldnames))",
    "fn": "Mat_VarDuplicate",
    "kind": "calloc",
    "line": 1523,
    "origin": "cpg",
    "args": "in->internal->num_fields ;; sizeof(*in->internal->fieldnames)"
   },
   {
    "code": "strdup(in->internal->fieldnames[i])",
    "fn": "Mat_VarDuplicate",
    "kind": "strdup",
    "line": 1527,
    "origin": "cpg",
    "args": "in->internal->fieldnames[i]"
   },
   {
    "code": "malloc(in->nbytes)",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1610,
    "origin": "cpg",
    "args": "in->nbytes"
   },
   {
    "code": "malloc(in->nbytes)",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1620,
    "origin": "cpg",
    "args": "in->nbytes"
   },
   {
    "code": "malloc(sizeof(mat_sparse_t))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1630,
    "origin": "cpg",
    "args": "sizeof(mat_sparse_t)"
   },
   {
    "code": "malloc(in_sparse->nir * sizeof(*out_sparse->ir))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1636,
    "origin": "cpg",
    "args": "in_sparse->nir * sizeof(*out_sparse->ir)"
   },
   {
    "code": "malloc(in_sparse->njc * sizeof(*out_sparse->jc))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1640,
    "origin": "cpg",
    "args": "in_sparse->njc * sizeof(*out_sparse->jc)"
   },
   {
    "code": "malloc(sizeof(mat_complex_split_t))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1645,
    "origin": "cpg",
    "args": "sizeof(mat_complex_split_t)"
   },
   {
    "code": "malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1650,
    "origin": "cpg",
    "args": "in_sparse->ndata * Mat_SizeOf(in->data_type)"
   },
   {
    "code": "malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1654,
    "origin": "cpg",
    "args": "in_sparse->ndata * Mat_SizeOf(in->data_type)"
   },
   {
    "code": "malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1660,
    "origin": "cpg",
    "args": "in_sparse->ndata * Mat_SizeOf(in->data_type)"
   },
   {
    "code": "malloc(sizeof(mat_complex_split_t))",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1670,
    "origin": "cpg",
    "args": "sizeof(mat_complex_split_t)"
   },
   {
    "code": "malloc(out->nbytes)",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1674,
    "origin": "cpg",
    "args": "out->nbytes"
   },
   {
    "kind": "unknown",
    "line": 1676,
    "fn": "Mat_VarDuplicate",
    "code": "memcpy(out_data->Re, in_data->Re, out->nbytes) | out_data->Re | in_data->Re | out->nbytes",
    "origin": "report:crash"
   },
   {
    "code": "malloc(out->nbytes)",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1677,
    "origin": "cpg",
    "args": "out->nbytes"
   },
   {
    "code": "malloc(in->nbytes)",
    "fn": "Mat_VarDuplicate",
    "kind": "malloc",
    "line": 1682,
    "origin": "cpg",
    "args": "in->nbytes"
   }
  ],
  "crash": {
   "site": {
    "fn": "Mat_VarDuplicate",
    "file": "/src/matio/src/mat.c",
    "line": 1676
   },
   "code": "memcpy(out_data->Re, in_data->Re, out->nbytes) | out_data->Re | in_data->Re | out->nbytes",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Mat_VarDuplicate",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "out == NULL",
   "guard_count": 1,
   "control_structures": "IF:1482,IF:1496,IF:1499,IF:1504,IF:1507,IF:1521,IF:1524,FOR:1525,IF:1526,ELSE:1602,IF:1607,ELSE:1609"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mat_complex_split_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "in"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/36aa91bb702a9217ec05c866f932c78f1e0b2647/ARVO-42534483/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_36aa91bb702a.cpg",
   "testcase_size": 2126
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "Mat_VarDuplicate--MatioRead(char const*)--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*out_data = (mat_complex_split_t *)out_sparse->data",
     "line": 1647
    },
    {
     "code": "out_data->Re = malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
     "line": 1650
    },
    {
     "code": "out_data->Im = malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
     "line": 1654
    },
    {
     "code": "*out_data = (mat_complex_split_t *)out->data",
     "line": 1672
    },
    {
     "code": "out_data->Re = malloc(out->nbytes)",
     "line": 1674
    },
    {
     "code": "out_data->Im = malloc(out->nbytes)",
     "line": 1677
    }
   ],
   "entity_decl": {
    "line": 1647,
    "type": "mat_complex_split_t*"
   },
   "entity_name_cpg": "out_data",
   "func_lines": [
    1475,
    1689
   ],
   "func_params": {
    "names": [
     "in",
     "opt"
    ],
    "types": [
     "matvar_t*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "out == NULL",
     "line": 1482
    },
    {
     "code": "NULL != in->name",
     "line": 1496
    },
    {
     "code": "NULL != out->name",
     "line": 1499
    },
    {
     "code": "out->dims != NULL",
     "line": 1504
    },
    {
     "code": "NULL != in->internal",
     "line": 1507
    },
    {
     "code": "NULL != in->internal->fieldnames",
     "line": 1521
    },
    {
     "code": "in->internal->num_fields > 0",
     "line": 1521
    },
    {
     "code": "NULL != out->internal->fieldnames",
     "line": 1524
    },
    {
     "code": "i < in->internal->num_fields",
     "line": 1525
    },
    {
     "code": "NULL != in->internal->fieldnames[i]",
     "line": 1526
    },
    {
     "code": "in->data != NULL",
     "line": 1609
    },
    {
     "code": "in->class_type == MAT_C_STRUCT",
     "line": 1609
    },
    {
     "code": "out->data != NULL",
     "line": 1611
    },
    {
     "code": "in->data_size > 0",
     "line": 1611
    },
    {
     "code": "i < nfields",
     "line": 1615
    },
    {
     "code": "in->data != NULL",
     "line": 1619
    },
    {
     "code": "in->class_type == MAT_C_CELL",
     "line": 1619
    },
    {
     "code": "out->data != NULL",
     "line": 1621
    },
    {
     "code": "in->data_size > 0",
     "line": 1621
    },
    {
     "code": "i < nelems",
     "line": 1625
    },
    {
     "code": "in->data != NULL",
     "line": 1629
    },
    {
     "code": "in->class_type == MAT_C_SPARSE",
     "line": 1629
    },
    {
     "code": "out->data != NULL",
     "line": 1631
    },
    {
     "code": "out_sparse->ir != NULL",
     "line": 1637
    },
    {
     "code": "out_sparse->jc != NULL",
     "line": 1641
    },
    {
     "code": "NULL != in_sparse->data",
     "line": 1644
    },
    {
     "code": "out_sparse->data != NULL",
     "line": 1646
    },
    {
     "code": "NULL != out_data->Re",
     "line": 1651
    },
    {
     "code": "NULL != out_data->Im",
     "line": 1655
    },
    {
     "code": "in_sparse->data != NULL",
     "line": 1659
    },
    {
     "code": "NULL != out_sparse->data",
     "line": 1661
    },
    {
     "code": "in->data != NULL",
     "line": 1668
    },
    {
     "code": "out->data != NULL",
     "line": 1671
    },
    {
     "code": "NULL != out_data->Re",
     "line": 1675
    },
    {
     "code": "NULL != out_data->Im",
     "line": 1678
    },
    {
     "code": "out->data != NULL",
     "line": 1683
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memcpy(out_data->Re, in_data->Re, out->nbytes)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "out_data->Re",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "in_data->Re",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "out->nbytes",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out_data",
    "in_data",
    "out"
   ],
   "osv_id": "ARVO-42534483",
   "sites": [
    {
     "args": "",
     "callee": "Mat_VarCalloc",
     "code": "Mat_VarCalloc()",
     "line": 1481
    },
    {
     "args": "len",
     "callee": "malloc",
     "code": "malloc(len)",
     "line": 1498
    },
    {
     "args": "in->rank * sizeof(*out->dims)",
     "callee": "malloc",
     "code": "malloc(in->rank * sizeof(*out->dims))",
     "line": 1503
    },
    {
     "args": "in->internal->num_fields ;; sizeof(*in->internal->fieldnames)",
     "callee": "calloc",
     "code": "calloc(in->internal->num_fields, sizeof(*in->internal->fieldnames))",
     "line": 1523
    },
    {
     "args": "in->internal->fieldnames[i]",
     "callee": "strdup",
     "code": "strdup(in->internal->fieldnames[i])",
     "line": 1527
    },
    {
     "args": "out->internal",
     "callee": "free",
     "code": "free(out->internal)",
     "line": 1603
    },
    {
     "args": "in->nbytes",
     "callee": "malloc",
     "code": "malloc(in->nbytes)",
     "line": 1610
    },
    {
     "args": "in->nbytes",
     "callee": "malloc",
     "code": "malloc(in->nbytes)",
     "line": 1620
    },
    {
     "args": "sizeof(mat_sparse_t)",
     "callee": "malloc",
     "code": "malloc(sizeof(mat_sparse_t))",
     "line": 1630
    },
    {
     "args": "in_sparse->nir * sizeof(*out_sparse->ir)",
     "callee": "malloc",
     "code": "malloc(in_sparse->nir * sizeof(*out_sparse->ir))",
     "line": 1636
    },
    {
     "args": "in_sparse->njc * sizeof(*out_sparse->jc)",
     "callee": "malloc",
     "code": "malloc(in_sparse->njc * sizeof(*out_sparse->jc))",
     "line": 1640
    },
    {
     "args": "sizeof(mat_complex_split_t)",
     "callee": "malloc",
     "code": "malloc(sizeof(mat_complex_split_t))",
     "line": 1645
    },
    {
     "args": "in_sparse->ndata * Mat_SizeOf(in->data_type)",
     "callee": "malloc",
     "code": "malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
     "line": 1650
    },
    {
     "args": "in_sparse->ndata * Mat_SizeOf(in->data_type)",
     "callee": "malloc",
     "code": "malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
     "line": 1654
    },
    {
     "args": "in_sparse->ndata * Mat_SizeOf(in->data_type)",
     "callee": "malloc",
     "code": "malloc(in_sparse->ndata * Mat_SizeOf(in->data_type))",
     "line": 1660
    },
    {
     "args": "sizeof(mat_complex_split_t)",
     "callee": "malloc",
     "code": "malloc(sizeof(mat_complex_split_t))",
     "line": 1670
    },
    {
     "args": "out->nbytes",
     "callee": "malloc",
     "code": "malloc(out->nbytes)",
     "line": 1674
    },
    {
     "args": "out->nbytes",
     "callee": "malloc",
     "code": "malloc(out->nbytes)",
     "line": 1677
    },
    {
     "args": "in->nbytes",
     "callee": "malloc",
     "code": "malloc(in->nbytes)",
     "line": 1682
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Mat_VarDuplicate"
  }
 },
 {
  "osv_id": "ARVO-42534645",
  "project": "exiv2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "CmdId",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "new",
   "site": {
    "fn": "void* std::__1::__libcpp_operator_new<unsigned long>(unsigned long)",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 245
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "buf ;; nBytes",
   "size_expr_cpg_callee": "alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 57,
    "fn": "Exiv2::AsfVideo::GUIDTag::GUIDTag(unsigned char const*)",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Exiv2::AsfVideo::GUIDTag::GUIDTag(unsigned char const*)",
    "file": "/src/exiv2/src/asfvideo.cpp",
    "line": 57
   },
   "code": "{CmdId::invalid, \"invalidCmd\"}",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Exiv2::AsfVideo::GUIDTag::GUIDTag(unsigned char const*)",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/exiv2/address/93f5acbbff7dacc66cfa02a56957c5746a7c107c/ARVO-42534645/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/exiv2_93f5acbbff7d.cpg",
   "testcase_size": 96
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "memmove--std::__1::enable_if<(is_same<std::__1::remove_const<unsigned char const>::type, unsigned char>::value) && (is_trivially_copy_assignable<unsigned char>:"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "CmdId",
   "func_lines": [
    1,
    1515
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [
    {
     "code": "string == string_",
     "line": 50
    },
    {
     "code": "EXV_LOCALEDIR[0] == '/'",
     "line": 128
    },
    {
     "code": "filesCount > 1",
     "line": 156
    },
    {
     "code": "returnCode == EXIT_SUCCESS",
     "line": 177
    },
    {
     "code": "optArg.size() > 2",
     "line": 496
    },
    {
     "code": "optArg.back() == 'i'",
     "line": 496
    },
    {
     "code": "optArg[optArg.size() - 2] == '/'",
     "line": 496
    },
    {
     "code": "opt == 'r'",
     "line": 540
    },
    {
     "code": "rc > 0",
     "line": 765
    },
    {
     "code": "rc > 0",
     "line": 786
    },
    {
     "code": "rc > 0",
     "line": 807
    },
    {
     "code": "opt == 'c'",
     "line": 827
    },
    {
     "code": "opt == 'm'",
     "line": 829
    },
    {
     "code": "opt == 'M'",
     "line": 831
    },
    {
     "code": "argv == \"ad\"",
     "line": 847
    },
    {
     "code": "argv == \"adjust\"",
     "line": 847
    },
    {
     "code": "action_ != Action::none",
     "line": 848
    },
    {
     "code": "action_ != Action::adjust",
     "line": 848
    },
    {
     "code": "argv == \"pr\"",
     "line": 855
    },
    {
     "code": "argv == \"print\"",
     "line": 855
    },
    {
     "code": "action_ != Action::none",
     "line": 856
    },
    {
     "code": "action_ != Action::print",
     "line": 856
    },
    {
     "code": "argv == \"rm\"",
     "line": 863
    },
    {
     "code": "argv == \"delete\"",
     "line": 863
    },
    {
     "code": "action_ != Action::none",
     "line": 864
    },
    {
     "code": "action_ != Action::erase",
     "line": 864
    },
    {
     "code": "argv == \"ex\"",
     "line": 871
    },
    {
     "code": "argv == \"extract\"",
     "line": 871
    },
    {
     "code": "action_ != Action::none",
     "line": 872
    },
    {
     "code": "action_ != Action::extract",
     "line": 872
    },
    {
     "code": "action_ != Action::modify",
     "line": 872
    },
    {
     "code": "argv == \"in\"",
     "line": 879
    },
    {
     "code": "argv == \"insert\"",
     "line": 879
    },
    {
     "code": "action_ != Action::none",
     "line": 880
    },
    {
     "code": "action_ != Action::insert",
     "line": 880
    },
    {
     "code": "action_ != Action::modify",
     "line": 880
    },
    {
     "code": "argv == \"mv\"",
     "line": 887
    },
    {
     "code": "argv == \"rename\"",
     "line": 887
    },
    {
     "code": "action_ != Action::none",
     "line": 888
    },
    {
     "code": "action_ != Action::rename",
     "line": 888
    },
    {
     "code": "argv == \"mo\"",
     "line": 895
    },
    {
     "code": "argv == \"modify\"",
     "line": 895
    },
    {
     "code": "action_ != Action::none",
     "line": 896
    },
    {
     "code": "action_ != Action::modify",
     "line": 896
    },
    {
     "code": "argv == \"fi\"",
     "line": 903
    },
    {
     "code": "argv == \"fixiso\"",
     "line": 903
    },
    {
     "code": "action_ != Action::none",
     "line": 904
    },
    {
     "code": "action_ != Action::fixiso",
     "line": 904
    },
    {
     "code": "argv == \"fc\"",
     "line": 911
    },
    {
     "code": "argv == \"fixcom\"",
     "line": 911
    },
    {
     "code": "argv == \"fixcomment\"",
     "line": 911
    },
    {
     "code": "action_ != Action::none",
     "line": 912
    },
    {
     "code": "action_ != Action::fixcom",
     "line": 912
    },
    {
     "code": "action_ == Action::none",
     "line": 919
    },
    {
     "code": "n > 0",
     "line": 938
    },
    {
     "code": "i < argc",
     "line": 1020
    },
    {
     "code": "longs.find(arg) != longs.end()",
     "line": 1022
    },
    {
     "code": "action_ == Action::none",
     "line": 1034
    },
    {
     "code": "action_ == Action::adjust",
     "line": 1039
    },
    {
     "code": "action_ == Action::modify",
     "line": 1044
    },
    {
     "code": "rc == 0",
     "line": 1053
    },
    {
     "code": "rc == 0",
     "line": 1058
    },
    {
     "code": "rc == 0",
     "line": 1062
    },
    {
     "code": "action_ != Action::insert",
     "line": 1066
    },
    {
     "code": "action_ != Action::extract",
     "line": 1066
    },
    {
     "code": "action_ != Action::insert",
     "line": 1070
    },
    {
     "code": "action_ != Action::rename",
     "line": 1074
    },
    {
     "code": "action_ != Action::rename",
     "line": 1078
    },
    {
     "code": "i < argc",
     "line": 1085
    },
    {
     "code": "hh < 0",
     "line": 1114
    },
    {
     "code": "hh == 0",
     "line": 1119
    },
    {
     "code": "mm > 59",
     "line": 1125
    },
    {
     "code": "mm < 0",
     "line": 1127
    },
    {
     "code": "ss > 59",
     "line": 1134
    },
    {
     "code": "ss < 0",
     "line": 1136
    },
    {
     "code": "rc == 0",
     "line": 1154
    },
    {
     "code": "i < optArg.size()",
     "line": 1154
    },
    {
     "code": "i > 0",
     "line": 1185
    },
    {
     "code": "action == \"extract\"",
     "line": 1192
    },
    {
     "code": "i < optArg.size()",
     "line": 1213
    },
    {
     "code": "k < optArg.size()",
     "line": 1215
    },
    {
     "code": "k > i",
     "line": 1218
    },
    {
     "code": "optArg[i] != ','",
     "line": 1228
    },
    {
     "code": "ret == 0",
     "line": 1232
    },
    {
     "code": "filename == \"-\"",
     "line": 1249
    },
    {
     "code": "cmdStart == std::string::npos",
     "line": 1318
    },
    {
     "code": "line[cmdStart] == '#'",
     "line": 1318
    },
    {
     "code": "cmdEnd == std::string::npos",
     "line": 1325
    },
    {
     "code": "keyStart == std::string::npos",
     "line": 1325
    },
    {
     "code": "cmdId == CmdId::invalid",
     "line": 1338
    },
    {
     "code": "cmdId != CmdId::reg",
     "line": 1346
    },
    {
     "code": "metadataId == MetadataId::invalid",
     "line": 1353
    },
    {
     "code": "metadataId == MetadataId::invalid",
     "line": 1361
    },
    {
     "code": "metadataId == MetadataId::invalid",
     "line": 1369
    },
    {
     "code": "cmdId != CmdId::del",
     "line": 1377
    },
    {
     "code": "keyEnd != std::string::npos",
     "line": 1380
    },
    {
     "code": "typeStart != std::string::npos",
     "line": 1383
    },
    {
     "code": "valStart != std::string::npos",
     "line": 1387
    },
    {
     "code": "cmdId == CmdId::reg",
     "line": 1390
    },
    {
     "code": "keyEnd == std::string::npos",
     "line": 1390
    },
    {
     "code": "valStart == std::string::npos",
     "line": 1390
    },
    {
     "code": "cmdId != CmdId::reg",
     "line": 1395
    },
    {
     "code": "typeStart != std::string::npos",
     "line": 1395
    },
    {
     "code": "typeEnd != std::string::npos",
     "line": 1395
    },
    {
     "code": "tmpType != Exiv2::invalidTypeId",
     "line": 1398
    },
    {
     "code": "valStart == std::string::npos",
     "line": 1400
    },
    {
     "code": "valStart != std::string::npos",
     "line": 1409
    },
    {
     "code": "value.at(0) == '\"'",
     "line": 1412
    },
    {
     "code": "value.at(last) == '\"'",
     "line": 1412
    },
    {
     "code": "value.at(0) == '\\''",
     "line": 1412
    },
    {
     "code": "value.at(last) == '\\''",
     "line": 1412
    },
    {
     "code": "cmdId == CmdId::reg",
     "line": 1425
    },
    {
     "code": "i < input.length()",
     "line": 1446
    },
    {
     "code": "ch != '\\\\'",
     "line": 1448
    },
    {
     "code": "input.length() - 4 > i",
     "line": 1473
    },
    {
     "code": "j < 4",
     "line": 1475
    },
    {
     "code": "acc == 0xFFFFFFFF",
     "line": 1489
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "{CmdId::invalid, \"invalidCmd\"}",
     "name": "<operator>.arrayInitializer",
     "nargs": 2
    },
    {
     "code": "CmdId::invalid",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "CmdId"
   ],
   "osv_id": "ARVO-42534645",
   "sites": [
    {
     "args": "buf ;; nBytes",
     "callee": "alloc",
     "code": "buf.alloc(nBytes)",
     "line": 947
    },
    {
     "args": "buf ;; stdinBuf.size()",
     "callee": "alloc",
     "code": "buf.alloc(stdinBuf.size())",
     "line": 997
    },
    {
     "args": "longs.at(arg).c_str()",
     "callee": "strdup",
     "code": "::strdup(longs.at(arg).c_str())",
     "line": 1023
    },
    {
     "args": "Argv[i]",
     "callee": "strdup",
     "code": "::strdup(Argv[i])",
     "line": 1025
    },
    {
     "args": "argv[i]",
     "callee": "free",
     "code": "::free(argv[i])",
     "line": 1086
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Exiv2::AsfVideo::GUIDTag::GUIDTag(unsigned char const*)"
  }
 },
 {
  "osv_id": "ARVO-42536751",
  "project": "gpac",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "inspect_dump_pid",
    "file": "/src/gpac/src/filters/inspect.c",
    "line": 4442
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 7540,
    "fn": "gf_hevc_compute_ref_list",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "gf_hevc_compute_ref_list",
    "file": "/src/gpac/src/media_tools/av_parsers.c",
    "line": 7540
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "gf_hevc_compute_ref_list",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/gpac/address/df8121066cf8fb25cc70adf7ca8b35bda82fe216/ARVO-42536751/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/gpac_df8121066cf8.cpg",
   "testcase_size": 3828
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "loc_size": 529104,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "gf_hevc_compute_ref_list--gf_hevc_parse_nalu_bs--gf_inspect_dump_nalu_internal",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "gf_hevc_compute_ref_list"
  }
 },
 {
  "osv_id": "ARVO-42536963",
  "project": "libxml2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "name",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/HTMLparser.c",
    "line": 423,
    "size": null,
    "type": "xmlChar*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "xmlFuzzMalloc",
    "file": "/src/libxml2/fuzz/fuzz.c",
    "line": 94
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "150",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 423,
    "fn": "htmlCurrentChar",
    "code": "*name = NULL",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "htmlCurrentChar",
    "file": "/src/libxml2/HTMLparser.c",
    "line": 423
   },
   "code": "*name = NULL",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlFormatError",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "err == NULL | channel == NULL | node != NULL",
   "guard_count": 15,
   "control_structures": "IF:430,IF:441,IF:444,IF:450,IF:457,IF:459,IF:464,ELSE:466,IF:466,ELSE:468,IF:469,ELSE:471"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlChar*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libxml2/address/f48eefe3d0b5d82d46576f45a72b420568f5bc97/ARVO-42536963/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_f48eefe3d0b5.cpg",
   "testcase_size": 2580
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 4096,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "htmlCurrentChar--htmlParseCharDataInternal--htmlParseCharData",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*name = NULL",
     "line": 423
    },
    {
     "code": "name = node->name",
     "line": 452
    }
   ],
   "entity_decl": {
    "line": 423,
    "type": "xmlChar*"
   },
   "entity_name_cpg": "name",
   "func_lines": [
    415,
    618
   ],
   "func_params": {
    "names": [
     "err",
     "channel",
     "data"
    ],
    "types": [
     "xmlError*",
     "xmlGenericErrorFunc",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "err == NULL",
     "line": 430
    },
    {
     "code": "channel == NULL",
     "line": 430
    },
    {
     "code": "code == XML_ERR_OK",
     "line": 441
    },
    {
     "code": "domain == XML_FROM_PARSER",
     "line": 444
    },
    {
     "code": "domain == XML_FROM_HTML",
     "line": 444
    },
    {
     "code": "domain == XML_FROM_DTD",
     "line": 445
    },
    {
     "code": "domain == XML_FROM_NAMESPACE",
     "line": 445
    },
    {
     "code": "domain == XML_FROM_IO",
     "line": 446
    },
    {
     "code": "domain == XML_FROM_VALID",
     "line": 446
    },
    {
     "code": "node != NULL",
     "line": 450
    },
    {
     "code": "node->type == XML_ELEMENT_NODE",
     "line": 450
    },
    {
     "code": "domain != XML_FROM_SCHEMASV",
     "line": 451
    },
    {
     "code": "ctxt != NULL",
     "line": 457
    },
    {
     "code": "ctxt->input != NULL",
     "line": 457
    },
    {
     "code": "input->filename == NULL",
     "line": 459
    },
    {
     "code": "ctxt->inputNr > 1",
     "line": 460
    },
    {
     "code": "line != 0",
     "line": 466
    },
    {
     "code": "domain == XML_FROM_PARSER",
     "line": 466
    },
    {
     "code": "file != NULL",
     "line": 469
    },
    {
     "code": "line != 0",
     "line": 471
    },
    {
     "code": "domain == XML_FROM_PARSER",
     "line": 472
    },
    {
     "code": "domain == XML_FROM_SCHEMASV",
     "line": 472
    },
    {
     "code": "domain == XML_FROM_SCHEMASP",
     "line": 473
    },
    {
     "code": "domain == XML_FROM_DTD",
     "line": 473
    },
    {
     "code": "domain == XML_FROM_RELAXNGP",
     "line": 474
    },
    {
     "code": "domain == XML_FROM_RELAXNGV",
     "line": 474
    },
    {
     "code": "name != NULL",
     "line": 477
    },
    {
     "code": "message != NULL",
     "line": 568
    },
    {
     "code": "len > 0",
     "line": 571
    },
    {
     "code": "message[len - 1] != '\\n'",
     "line": 571
    },
    {
     "code": "ctxt != NULL",
     "line": 579
    },
    {
     "code": "input != NULL",
     "line": 580
    },
    {
     "code": "input->buf == NULL",
     "line": 581
    },
    {
     "code": "input->buf->encoder == NULL",
     "line": 581
    },
    {
     "code": "code == XML_ERR_INVALID_ENCODING",
     "line": 582
    },
    {
     "code": "input->cur < input->end",
     "line": 583
    },
    {
     "code": "i < 4",
     "line": 587
    },
    {
     "code": "cur != NULL",
     "line": 597
    },
    {
     "code": "line != 0",
     "line": 600
    },
    {
     "code": "domain == XML_FROM_PARSER",
     "line": 600
    },
    {
     "code": "domain == XML_FROM_XPATH",
     "line": 605
    },
    {
     "code": "err->str1 != NULL",
     "line": 605
    },
    {
     "code": "err->int1 < 100",
     "line": 606
    },
    {
     "code": "err->int1 < xmlStrlen((const xmlChar *)err->str1)",
     "line": 607
    },
    {
     "code": "i < err->int1",
     "line": 612
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "*name = NULL",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "name",
    "NULL"
   ],
   "osv_id": "ARVO-42536963",
   "sites": [
    {
     "args": "150",
     "callee": "<operator>.alloc",
     "code": "buf[150]",
     "line": 608
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "htmlCurrentChar"
  }
 },
 {
  "osv_id": "ARVO-42537014",
  "project": "gpac",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "gf_dynstrcat",
    "file": "/src/gpac/src/utils/error.c",
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 10383,
    "fn": "gf_dash_group_get_template",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "gf_dash_group_get_template",
    "file": "/src/gpac/src/media_tools/dash_client.c",
    "line": 10383
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "gf_dash_group_get_template",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/gpac/address/7323c74ff523fa2d5c4db793d5dfbc611ae505c4/ARVO-42537014/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/gpac_7323c74ff523.cpg",
   "testcase_size": 9
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_size": 1,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "gf_dash_group_get_template--gf_dash_resolve_url--gf_dash_download_init_segment",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "gf_dash_group_get_template"
  }
 },
 {
  "osv_id": "ARVO-42537249",
  "project": "kimageformats",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "mutableThis",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/kimageformats/src/imageformats/pcx.cpp",
    "line": 316,
    "size": null,
    "type": "auto*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "QImageData::create(QSize const&, QImage::Format)",
    "file": "/src/qtbase/src/gui/image/qimage.cpp",
    "line": 147
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 374,
    "fn": "readImage4v2(QImage&, QDataStream&, PCXHEADER const&)",
    "code": "mutableThis->m_size = QSize(aniHeader->iWidth, aniHeader | mutableThis->m_size | QSize(aniHeader->iWidth, aniHeader->iHeight) | aniHeader->iWidth",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "readImage4v2(QImage&, QDataStream&, PCXHEADER const&)",
    "file": "/src/kimageformats/src/imageformats/pcx.cpp",
    "line": 374
   },
   "code": "mutableThis->m_size = QSize(aniHeader->iWidth, aniHeader | mutableThis->m_size | QSize(aniHeader->iWidth, aniHeader->iHeight) | aniHeader->iWidth",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ensureScanned",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:308,IF:312,IF:326,IF:331,IF:336,WHILE:343,IF:345,IF:349,CONTINUE:350,IF:354,IF:359,IF:360"
  },
  "call_chain": [],
  "types": {
   "entity_type": "auto*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "this"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kimageformats/address/3590a43fc506afca40a20b09fb6e8007b6dcf5b8/ARVO-42537249/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_3590a43fc506.cpg",
   "testcase_size": 130
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_size": 4,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "readImage4v2(QImage&, QDataStream&, PCXHEADER const&)--PCXHandler::read(QImage*)--LLVMFuzzerTestOneInput",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*mutableThis = const_cast<ANIHandler *>(this)",
     "line": 316
    },
    {
     "code": "mutableThis->m_size = QSize(aniHeader->iWidth, aniHeader->iHeight)",
     "line": 374
    },
    {
     "code": "mutableThis->m_frameCount = aniHeader->nFrames",
     "line": 375
    },
    {
     "code": "mutableThis->m_imageCount = aniHeader->nSteps",
     "line": 376
    },
    {
     "code": "mutableThis->m_displayRate = aniHeader->iDispRate",
     "line": 377
    },
    {
     "code": "mutableThis->m_displayRates = list",
     "line": 394
    },
    {
     "code": "mutableThis->m_imageSequence = list",
     "line": 406
    },
    {
     "code": "mutableThis->m_name = stringValue",
     "line": 426
    },
    {
     "code": "mutableThis->m_artist = stringValue",
     "line": 428
    },
    {
     "code": "mutableThis->m_firstFrameOffset = device()->pos() - 4",
     "line": 445
    },
    {
     "code": "mutableThis->m_currentImageNumber = 0",
     "line": 446
    },
    {
     "code": "mutableThis->m_size = QSize(cursorDirEntry->bWidth, cursorDirEntry->bHeight)",
     "line": 459
    },
    {
     "code": "mutableThis->m_scanned = true",
     "line": 514
    }
   ],
   "entity_decl": {
    "line": 316,
    "type": "auto*"
   },
   "entity_name_cpg": "mutableThis",
   "func_lines": [
    306,
    516
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "ANIHandler"
    ]
   },
   "guards": [
    {
     "code": "riffIntro != \"RIFF\"",
     "line": 326
    },
    {
     "code": "riffSizeData.size() != sizeof(quint32_le)",
     "line": 331
    },
    {
     "code": "riffSize == 0",
     "line": 336
    },
    {
     "code": "device()->pos() < riffSize",
     "line": 343
    },
    {
     "code": "chunkId.length() != 4",
     "line": 345
    },
    {
     "code": "chunkId == \"ACON\"",
     "line": 349
    },
    {
     "code": "chunkSizeData.length() != sizeof(quint32_le)",
     "line": 354
    },
    {
     "code": "chunkId == \"anih\"",
     "line": 359
    },
    {
     "code": "chunkSize != sizeof(AniHeader)",
     "line": 360
    },
    {
     "code": "anihData.size() != sizeof(AniHeader)",
     "line": 366
    },
    {
     "code": "chunkId == \"rate\"",
     "line": 378
    },
    {
     "code": "chunkId == \"seq \"",
     "line": 378
    },
    {
     "code": "static_cast<quint32_le>(data.size()) != chunkSize",
     "line": 380
    },
    {
     "code": "data.size() % sizeof(quint32_le) != 0",
     "line": 380
    },
    {
     "code": "i < data.size()",
     "line": 387
    },
    {
     "code": "chunkId == \"rate\"",
     "line": 392
    },
    {
     "code": "chunkId == \"seq \"",
     "line": 395
    },
    {
     "code": "i < list.count()",
     "line": 398
    },
    {
     "code": "list.at(i) != i",
     "line": 399
    },
    {
     "code": "chunkId == \"INAM\"",
     "line": 411
    },
    {
     "code": "chunkId == \"IART\"",
     "line": 411
    },
    {
     "code": "static_cast<quint32_le>(value.size()) != chunkSize",
     "line": 414
    },
    {
     "code": "chunkSize % 2 != 0",
     "line": 419
    },
    {
     "code": "chunkId == \"INAM\"",
     "line": 425
    },
    {
     "code": "chunkId == \"IART\"",
     "line": 427
    },
    {
     "code": "chunkId == \"LIST\"",
     "line": 430
    },
    {
     "code": "listType == \"INFO\"",
     "line": 433
    },
    {
     "code": "listType == \"fram\"",
     "line": 435
    },
    {
     "code": "read < chunkSize",
     "line": 437
    },
    {
     "code": "chunkType != \"icon\"",
     "line": 440
    },
    {
     "code": "curHeaderData.length() == sizeof(CurHeader)",
     "line": 457
    },
    {
     "code": "cursorDirEntryData.length() == sizeof(CursorDirEntry)",
     "line": 457
    },
    {
     "code": "frameSizeData.size() != sizeof(quint32_le)",
     "line": 474
    },
    {
     "code": "m_frameOffsets.count() == m_frameCount",
     "line": 483
    },
    {
     "code": "m_imageCount != m_frameCount",
     "line": 494
    },
    {
     "code": "m_imageSequence.count() != m_imageCount",
     "line": 499
    },
    {
     "code": "m_displayRates.count() != m_imageCount",
     "line": 504
    },
    {
     "code": "m_frameOffsets.count() - 1 != m_frameCount",
     "line": 509
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "mutableThis->m_size = QSize(aniHeader->iWidth, aniHeader->iHeight)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "mutableThis->m_size",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "QSize(aniHeader->iWidth, aniHeader->iHeight)",
     "name": "QSize",
     "nargs": 2
    },
    {
     "code": "aniHeader->iWidth",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "aniHeader->iHeight",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "mutableThis",
    "aniHeader"
   ],
   "osv_id": "ARVO-42537249",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "readImage4v2(QImage&, QDataStream&, PCXHEADER const&)"
  }
 }
]

## 任务
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、dimensions、evidence、confidence。
   **样本里的 `measured_dims` 是 stage2 实测出来的值，不是让你猜的**：
   `reassigned_between` / `cross_frame_count` 直接照抄（`null` 才写 unknown），
   `cross_frame_exact=false` 表示跳数算不出精确值，此时 `cross_frame_count` 写 unknown。
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
        "free_cross_function": "true | false | unknown",
        "cross_frame_count": "number | unknown"
      },
      "dimension_distributions": {"维度名": {"取值": "样本数"}},
      "evidence": ["string"],
      "confidence": "high | medium | low"
    }
  ],
  "unclassified": [{"sample_id": "string", "reason": "string", "missing_fields": ["string"]}],
  "batch_observations": "string"
}

直接输出 JSON，不要任何解释文字。