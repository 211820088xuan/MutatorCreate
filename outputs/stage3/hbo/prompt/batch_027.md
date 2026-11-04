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
  "osv_id": "ARVO-42522572",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "set",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "line": 112,
    "size": null,
    "type": "hb_set_t*"
   }
  },
  "alloc": {
   "size_expr_cpg": "pop ;; sizeof (hb_codepoint_t)",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 115,
    "origin": "cpg",
    "args": "pop ;; sizeof (hb_codepoint_t)"
   },
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 116,
    "origin": "cpg",
    "args": "pop ;; sizeof (hb_codepoint_t)"
   },
   {
    "kind": "unknown",
    "line": 120,
    "fn": "operator unsigned short",
    "code": "hb_set_next (set, &u) | &u",
    "origin": "report:crash"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 137,
    "origin": "cpg",
    "args": "num_glyphs ;; sizeof (hb_codepoint_t)"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "operator unsigned short",
    "kind": "calloc",
    "line": 138,
    "origin": "cpg",
    "args": "num_glyphs ;; sizeof (hb_codepoint_t)"
   }
  ],
  "crash": {
   "site": {
    "fn": "operator unsigned short",
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "line": 120
   },
   "code": "hb_set_next (set, &u) | &u",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "BM_Font",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:89,SWITCH:95,BREAK:99,BREAK:105,SWITCH:108,FOR:119,FOR:124,BREAK:133,FOR:140,FOR:143,BREAK:151,FOR:156"
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_set_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a975ec4842468e574484bdc310095fad780978fc/ARVO-42522572/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a975ec484246.cpg",
   "testcase_size": 2501
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "operator unsigned short--operator unsigned int--get_size"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*set = hb_set_create ()",
     "line": 112
    }
   ],
   "entity_decl": {
    "line": 112,
    "type": "hb_set_t*"
   },
   "entity_name_cpg": "set",
   "func_lines": [
    73,
    174
   ],
   "func_params": {
    "names": [
     "state",
     "is_var",
     "backend",
     "operation",
     "test_input"
    ],
    "types": [
     "benchmark.State&",
     "bool",
     "backend_t",
     "operation_t",
     "test_input_t&"
    ]
   },
   "guards": [
    {
     "code": "p == unicodes + pop",
     "line": 122
    },
    {
     "code": "g < num_glyphs",
     "line": 140
    },
    {
     "code": "gid < num_glyphs",
     "line": 157
    },
    {
     "code": "gid < num_glyphs",
     "line": 165
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "hb_set_next (set, &u)",
     "name": "hb_set_next",
     "nargs": 2
    },
    {
     "code": "&u",
     "name": "<operator>.addressOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "set",
    "u"
   ],
   "osv_id": "ARVO-42522572",
   "sites": [
    {
     "args": "pop ;; sizeof (hb_codepoint_t)",
     "callee": "calloc",
     "code": "calloc (pop, sizeof (hb_codepoint_t))",
     "line": 115
    },
    {
     "args": "pop ;; sizeof (hb_codepoint_t)",
     "callee": "calloc",
     "code": "calloc (pop, sizeof (hb_codepoint_t))",
     "line": 116
    },
    {
     "args": "glyphs",
     "callee": "free",
     "code": "free (glyphs)",
     "line": 130
    },
    {
     "args": "unicodes",
     "callee": "free",
     "code": "free (unicodes)",
     "line": 131
    },
    {
     "args": "num_glyphs ;; sizeof (hb_codepoint_t)",
     "callee": "calloc",
     "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
     "line": 137
    },
    {
     "args": "num_glyphs ;; sizeof (hb_codepoint_t)",
     "callee": "calloc",
     "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
     "line": 138
    },
    {
     "args": "advances",
     "callee": "free",
     "code": "free (advances)",
     "line": 149
    },
    {
     "args": "glyphs",
     "callee": "free",
     "code": "free (glyphs)",
     "line": 150
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "operator unsigned short"
  }
 },
 {
  "osv_id": "ARVO-42522665",
  "project": "serenity",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "m_inode_lock",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1011,
    "fn": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)",
    "file": "/src/serenity/Userland/Libraries/LibGfx/ICC/TagTypes.cpp",
    "line": 1011
   },
   "code": "locker(m_inode_lock)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/9a7b3c145fcc07302f5934037923b49e1a0bda32/ARVO-42522665/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_9a7b3c145fcc.cpg",
   "testcase_size": 512
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
   "dedup_token": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)--read_tag--operator()"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "m_inode_lock",
   "func_lines": [
    1009,
    1020
   ],
   "func_params": {
    "names": [],
    "types": []
   },
   "guards": [
    {
     "code": "m_raw_inode.i_links_count == max_link_count",
     "line": 1015
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "locker(m_inode_lock)",
     "name": "locker",
     "nargs": 1
    }
   ],
   "line_ids": [
    "m_inode_lock"
   ],
   "osv_id": "ARVO-42522665",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Gfx::ICC::TextDescriptionTagData::from_bytes(AK::Span<unsigned char const>, unsigned int, unsigned int)"
  }
 },
 {
  "osv_id": "ARVO-42522842",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "len",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 2846,
    "size": null,
    "type": "size_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "dxf_read_string",
    "file": "/src/libredwg/src/in_dxf.c",
    "line": 523
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2 ;; len + 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc (2, len + 1)",
    "fn": "bit_utf8_to_TU",
    "kind": "calloc",
    "line": 2856,
    "origin": "cpg",
    "args": "2 ;; len + 1"
   },
   {
    "kind": "unknown",
    "line": 2863,
    "fn": "bit_utf8_to_TU",
    "code": "len > 0 && (c = *str++) | len > 0 | c = *str++ | *str++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_utf8_to_TU",
    "file": "/src/libredwg/src/bits.c",
    "line": 2863
   },
   "code": "len > 0 && (c = *str++) | len > 0 | c = *str++ | *str++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_utf8_to_TU",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "len > 0xFFFE | len > 0 | c < 128",
   "guard_count": 12,
   "control_structures": "IF:2849,IF:2852,IF:2852,IF:2857,IF:2860,IF:2860,WHILE:2863,IF:2866,IF:2868,IF:2874,ELSE:2876,IF:2876"
  },
  "call_chain": [],
  "types": {
   "entity_type": "size_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "str"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/5363f2eaaa83a7692652a019e475e9259ce49422/ARVO-42522842/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_5363f2eaaa83.cpg",
   "testcase_size": 58479
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
   "dedup_token": "bit_utf8_to_TU--dynapi_set_helper--dwg_dynapi_entity_set_value"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "len = strlen (str)",
     "line": 2846
    },
    {
     "code": "len = UINT16_MAX - 1",
     "line": 2854
    }
   ],
   "entity_decl": {
    "line": 2846,
    "type": "size_t"
   },
   "entity_name_cpg": "len",
   "func_lines": [
    2841,
    2918
   ],
   "func_params": {
    "names": [
     "str",
     "cquoted"
    ],
    "types": [
     "char*restrict",
     "unsigned"
    ]
   },
   "guards": [
    {
     "code": "len > 0xFFFE",
     "line": 2849
    },
    {
     "code": "len > 0",
     "line": 2863
    },
    {
     "code": "c < 128",
     "line": 2866
    },
    {
     "code": "c == '\\\\'",
     "line": 2868
    },
    {
     "code": "len > 1",
     "line": 2868
    },
    {
     "code": "*str == '\"'",
     "line": 2870
    },
    {
     "code": "*str == '\\\\'",
     "line": 2870
    },
    {
     "code": "*str == 'r'",
     "line": 2870
    },
    {
     "code": "*str == 'n'",
     "line": 2871
    },
    {
     "code": "c == 'r'",
     "line": 2874
    },
    {
     "code": "c == 'n'",
     "line": 2876
    },
    {
     "code": "(c & 0xe0) == 0xc0",
     "line": 2885
    },
    {
     "code": "(c & 0xf0) == 0xe0",
     "line": 2893
    },
    {
     "code": "(unsigned char)str[1] < 0x80",
     "line": 2897
    },
    {
     "code": "(unsigned char)str[1] > 0xBF",
     "line": 2897
    },
    {
     "code": "(unsigned char)str[2] < 0x80",
     "line": 2898
    },
    {
     "code": "(unsigned char)str[2] > 0xBF",
     "line": 2899
    },
    {
     "code": "c == 0xe0",
     "line": 2903
    },
    {
     "code": "(unsigned char)str[1] < 0xa0",
     "line": 2903
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "len > 0 && (c = *str++)",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "len > 0",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "c = *str++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*str++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "str++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "len",
    "c",
    "str"
   ],
   "osv_id": "ARVO-42522842",
   "sites": [
    {
     "args": "2 ;; len + 1",
     "callee": "calloc",
     "code": "calloc (2, len + 1)",
     "line": 2856
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_utf8_to_TU"
  }
 },
 {
  "osv_id": "ARVO-42522843",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "wstr",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/bits.c",
    "line": 2844,
    "size": null,
    "type": "BITCODE_TU"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "bit_utf8_to_TU",
    "file": "/src/libredwg/src/bits.c",
    "line": 2856
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "2 ;; len + 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "code": "calloc (2, len + 1)",
    "fn": "bit_utf8_to_TU",
    "kind": "calloc",
    "line": 2856,
    "origin": "cpg",
    "args": "2 ;; len + 1"
   },
   {
    "kind": "unknown",
    "line": 2883,
    "fn": "bit_utf8_to_TU",
    "code": "wstr[i++] = c | wstr[i++] | i++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_utf8_to_TU",
    "file": "/src/libredwg/src/bits.c",
    "line": 2883
   },
   "code": "wstr[i++] = c | wstr[i++] | i++",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_utf8_to_TU",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "c < 128 | c == '\\\\' | c == 'r'",
   "guard_count": 5,
   "control_structures": "IF:2849,IF:2852,IF:2852,IF:2857,IF:2860,IF:2860,WHILE:2863,IF:2866,IF:2868,IF:2874,ELSE:2876,IF:2876"
  },
  "call_chain": [],
  "types": {
   "entity_type": "BITCODE_TU",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "str"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/5363f2eaaa83a7692652a019e475e9259ce49422/ARVO-42522843/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_5363f2eaaa83.cpg",
   "testcase_size": 27
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
   "dedup_token": "bit_utf8_to_TU--json_wstring--json_AppInfo"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "wstr = (BITCODE_TU)calloc (2, len + 1)",
     "line": 2856
    },
    {
     "code": "wstr[i++] = '\\r'",
     "line": 2875
    },
    {
     "code": "wstr[i++] = '\\n'",
     "line": 2877
    },
    {
     "code": "wstr[i++] = c",
     "line": 2880
    },
    {
     "code": "wstr[i++] = c",
     "line": 2883
    },
    {
     "code": "wstr[i++] = ((c & 0x1f) << 6) ",
     "line": 2889
    },
    {
     "code": "wstr[i++] = ((c & 0x0f) << 12) ",
     "line": 2908
    }
   ],
   "entity_decl": {
    "line": 2844,
    "type": "BITCODE_TU"
   },
   "entity_name_cpg": "wstr",
   "func_lines": [
    2841,
    2918
   ],
   "func_params": {
    "names": [
     "str",
     "cquoted"
    ],
    "types": [
     "char*restrict",
     "unsigned"
    ]
   },
   "guards": [
    {
     "code": "len > 0xFFFE",
     "line": 2849
    },
    {
     "code": "len > 0",
     "line": 2863
    },
    {
     "code": "c < 128",
     "line": 2866
    },
    {
     "code": "c == '\\\\'",
     "line": 2868
    },
    {
     "code": "len > 1",
     "line": 2868
    },
    {
     "code": "*str == '\"'",
     "line": 2870
    },
    {
     "code": "*str == '\\\\'",
     "line": 2870
    },
    {
     "code": "*str == 'r'",
     "line": 2870
    },
    {
     "code": "*str == 'n'",
     "line": 2871
    },
    {
     "code": "c == 'r'",
     "line": 2874
    },
    {
     "code": "c == 'n'",
     "line": 2876
    },
    {
     "code": "(c & 0xe0) == 0xc0",
     "line": 2885
    },
    {
     "code": "(c & 0xf0) == 0xe0",
     "line": 2893
    },
    {
     "code": "(unsigned char)str[1] < 0x80",
     "line": 2897
    },
    {
     "code": "(unsigned char)str[1] > 0xBF",
     "line": 2897
    },
    {
     "code": "(unsigned char)str[2] < 0x80",
     "line": 2898
    },
    {
     "code": "(unsigned char)str[2] > 0xBF",
     "line": 2899
    },
    {
     "code": "c == 0xe0",
     "line": 2903
    },
    {
     "code": "(unsigned char)str[1] < 0xa0",
     "line": 2903
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "wstr[i++] = c",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "wstr[i++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "wstr",
    "i",
    "c"
   ],
   "osv_id": "ARVO-42522843",
   "sites": [
    {
     "args": "2 ;; len + 1",
     "callee": "calloc",
     "code": "calloc (2, len + 1)",
     "line": 2856
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_utf8_to_TU"
  }
 },
 {
  "osv_id": "ARVO-42523342",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 195,
    "fn": "MEM_read64",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "MEM_read64",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/common/mem.h",
    "line": 195
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "MEM_read64",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/c4c8c7cb7f22323cda796575f699ad4c953b6661/ARVO-42523342/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_c4c8c7cb7f22.cpg",
   "testcase_size": 11408
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "MEM_read64--MEM_readLE64--MEM_readLEST"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    217,
    220
   ],
   "func_params": {
    "names": [
     "memPtr"
    ],
    "types": [
     "void*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42523342",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "MEM_read64"
  }
 },
 {
  "osv_id": "ARVO-42523382",
  "project": "harfbuzz",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "draw_funcs",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/harfbuzz/src/hb-open-type.hh",
    "line": 64,
    "size": null,
    "type": "hb_draw_funcs_t*"
   }
  },
  "alloc": {
   "api": "realloc",
   "site": {
    "fn": "hb_realloc_impl",
    "file": "/work/build/../../src/harfbuzz/src/failing-alloc.c",
    "line": 55
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 65,
    "fn": "operator=",
    "code": "hb_draw_funcs_set_move_to_func (draw_funcs, _hb_move_to,",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "operator=",
    "file": "/src/harfbuzz/src/hb-open-type.hh",
    "line": 65
   },
   "code": "hb_draw_funcs_set_move_to_func (draw_funcs, _hb_move_to,",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_draw_funcs_create",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "hb_draw_funcs_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/harfbuzz/address/a975ec4842468e574484bdc310095fad780978fc/ARVO-42523382/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_a975ec484246.cpg",
   "testcase_size": 15886
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
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "operator=--drop_hints--drop_hints"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*draw_funcs = hb_draw_funcs_create ()",
     "line": 64
    }
   ],
   "entity_decl": {
    "line": 64,
    "type": "hb_draw_funcs_t*"
   },
   "entity_name_cpg": "draw_funcs",
   "func_lines": [
    61,
    71
   ],
   "func_params": {
    "names": [],
    "types": [
     "void"
    ]
   },
   "guards": [],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "hb_draw_funcs_set_move_to_func (draw_funcs, _hb_move_to, nullptr, nullptr)",
     "name": "hb_draw_funcs_set_move_to_func",
     "nargs": 4
    }
   ],
   "line_ids": [
    "draw_funcs"
   ],
   "osv_id": "ARVO-42523382",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "operator="
  }
 },
 {
  "osv_id": "ARVO-42523472",
  "project": "libvips",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
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
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 268,
    "fn": "vips_foreign_load_heif_build",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "vips_foreign_load_heif_build",
    "file": "/src/libvips/libvips/foreign/heifload.c",
    "line": 268
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "vips_foreign_load_heif_build",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42523472/report.log",
   "cpg": null,
   "testcase_size": 10997
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
   "dedup_token": "RegionItem::parse(std::__1::vector<unsigned char, std::__1::allocator<unsigned char> > const&)--heif::HeifContext::interpret_heif_file()--heif::HeifContext::rea"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "vips_foreign_load_heif_build"
  }
 },
 {
  "osv_id": "ARVO-42524318",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "src",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/out_json.c",
    "line": 1378,
    "size": null,
    "type": "BITCODE_TF"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "decode_preR13_header_variables",
    "file": "/src/libredwg/src/./header_variables_r11.spec",
    "line": 159
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1403,
    "fn": "json_write_TF",
    "code": "src[j]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "json_write_TF",
    "file": "/src/libredwg/src/out_json.c",
    "line": 1403
   },
   "code": "src[j]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_write_TF",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j < len",
   "guard_count": 1,
   "control_structures": "FOR:1384,IF:1387,ELSE:1389,IF:1389,ELSE:1397,IF:1397,IF:1400,FOR:1402,IF:1403,BREAK:1406,IF:1409,ELSE:1412"
  },
  "call_chain": [],
  "types": {
   "entity_type": "BITCODE_TF",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "src",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/c8098abda7cd419dd034c5f30c22b679039baa95/ARVO-42524318/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_c8098abda7cd.cpg",
   "testcase_size": 6163
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
   "dedup_token": "json_write_TF--json_preR13_header_write_private--json_header_write"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1378,
    "type": "BITCODE_TF"
   },
   "entity_name_cpg": "src",
   "func_lines": [
    1377,
    1425
   ],
   "func_params": {
    "names": [
     "dat",
     "src",
     "len"
    ],
    "types": [
     "Bit_Chain*restrict",
     "BITCODE_TF",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "i < len",
     "line": 1384
    },
    {
     "code": "c == '\\r'",
     "line": 1387
    },
    {
     "code": "c == '\\n'",
     "line": 1387
    },
    {
     "code": "c == '\"'",
     "line": 1387
    },
    {
     "code": "c == '\\\\'",
     "line": 1389
    },
    {
     "code": "i + 6 < len",
     "line": 1389
    },
    {
     "code": "src[i] == 'U'",
     "line": 1389
    },
    {
     "code": "src[i + 1] == '+'",
     "line": 1389
    },
    {
     "code": "c == '\\0'",
     "line": 1397
    },
    {
     "code": "i == slen",
     "line": 1400
    },
    {
     "code": "j < len",
     "line": 1402
    },
    {
     "code": "c < 0x1f",
     "line": 1417
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "src[j]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "src",
    "j"
   ],
   "osv_id": "ARVO-42524318",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "json_write_TF"
  }
 },
 {
  "osv_id": "ARVO-42524653",
  "project": "ntopng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "tot",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ntopng/src/NetworkInterface.cpp",
    "line": 2414,
    "size": null,
    "type": "u_int64_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pcap_check_header",
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "line": 405
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "64",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2445,
    "fn": "NetworkInterface::dissectPacket(unsigned int, bool, unsigned char*, pcap_pkthdr const*, unsigned char const*, unsigned short*, Host**, Host**, Flow**)",
    "code": "getTotalNumAlertedOutgoingFlows()",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "NetworkInterface::dissectPacket(unsigned int, bool, unsigned char*, pcap_pkthdr const*, unsigned char const*, unsigned short*, Host**, Host**, Flow**)",
    "file": "/src/ntopng/src/NetworkInterface.cpp",
    "line": 2445
   },
   "code": "getTotalNumAlertedOutgoingFlows()",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "visit",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "tot > 0 | tot > 0 | tot > 0",
   "guard_count": 11,
   "control_structures": "IF:2416,ELSE:2419,IF:2422,SWITCH:2424,BREAK:2429,BREAK:2436,IF:2442,BREAK:2446,IF:2451,IF:2454,BREAK:2459,IF:2464"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int64_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42524653/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "testcase_size": 164
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
   "dedup_token": "NetworkInterface::dissectPacket(unsigned int, bool, unsigned char*, pcap_pkthdr const*, unsigned char const*, unsigned short*, Host**, Host**, Flow**)--LLVMFuzz"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "tot =",
     "line": 2439
    },
    {
     "code": "tot = dns->getRcvdNumRepliesOk() + dns->getSentNumQueries()",
     "line": 2452
    },
    {
     "code": "tot = getNumOutgoingFlows() + getNumIncomingFlows()",
     "line": 2465
    },
    {
     "code": "tot = getNumOutgoingFlows() + getNumIncomingFlows()",
     "line": 2478
    },
    {
     "code": "tot = getNumOutgoingFlows() + getNumIncomingFlows()",
     "line": 2491
    },
    {
     "code": "tot =",
     "line": 2507
    },
    {
     "code": "tot =",
     "line": 2525
    },
    {
     "code": "tot = getNumBytesSent() + getNumBytesRcvd()",
     "line": 2549
    },
    {
     "code": "tot = getScoreAsClient() + getScoreAsServer()",
     "line": 2557
    },
    {
     "code": "tot = num_blacklisted_flows.as_client + num_blacklisted_flows.as_server",
     "line": 2565
    },
    {
     "code": "tot = unidirectionalTCPUDPFlows.numIngressFlows +",
     "line": 2574
    }
   ],
   "entity_decl": {
    "line": 2414,
    "type": "u_int64_t"
   },
   "entity_name_cpg": "tot",
   "func_lines": [
    2412,
    2583
   ],
   "func_params": {
    "names": [
     "this",
     "v",
     "mode"
    ],
    "types": [
     "Host",
     "std.vector<ActiveHostWalkerInfo>*",
     "HostWalkMode"
    ]
   },
   "guards": [
    {
     "code": "get_vlan_id() == 0",
     "line": 2416
    },
    {
     "code": "label[0] == '\\0'",
     "line": 2422
    },
    {
     "code": "tot > 0",
     "line": 2442
    },
    {
     "code": "tot > 0",
     "line": 2454
    },
    {
     "code": "tot > 0",
     "line": 2467
    },
    {
     "code": "tot > 0",
     "line": 2480
    },
    {
     "code": "tot > 0",
     "line": 2493
    },
    {
     "code": "tot > 0",
     "line": 2510
    },
    {
     "code": "tot > 0",
     "line": 2528
    },
    {
     "code": "getNumAlertedFlows() > 0",
     "line": 2537
    },
    {
     "code": "tot > 0",
     "line": 2551
    },
    {
     "code": "tot > 0",
     "line": 2559
    },
    {
     "code": "tot > 0",
     "line": 2567
    },
    {
     "code": "tot > 0",
     "line": 2577
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "getTotalNumAlertedOutgoingFlows()",
     "name": "getTotalNumAlertedOutgoingFlows",
     "nargs": 0
    }
   ],
   "line_ids": [
    "tot"
   ],
   "osv_id": "ARVO-42524653",
   "sites": [
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "buf[64]",
     "line": 2413
    },
    {
     "args": "96",
     "callee": "<operator>.alloc",
     "code": "key[96]",
     "line": 2413
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "NetworkInterface::dissectPacket(unsigned int, bool, unsigned char*, pcap_pkthdr const*, unsigned char const*, unsigned short*, Host**, Host**, Flow**)"
  }
 },
 {
  "osv_id": "ARVO-42524654",
  "project": "ntopng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dst_ip",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "grow_buffer",
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "line": 426
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "32",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 100,
    "fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)",
    "code": "Utils::intoaV4(dst_ip, buf2ip, sizeof(buf2ip)) | sizeof(buf2ip)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)",
    "file": "/src/ntopng/src/ICMPinfo.cpp",
    "line": 100
   },
   "code": "Utils::intoaV4(dst_ip, buf2ip, sizeof(buf2ip)) | sizeof(buf2ip)",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "print",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "msg"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42524654/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "testcase_size": 78
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)--NetworkInterface::processPacket(unsigned int, bool, timeval const*, unsigned long, ndpi_ethhdr*, un"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "dst_ip",
   "func_lines": [
    93,
    102
   ],
   "func_params": {
    "names": [
     "msg"
    ],
    "types": [
     "char*"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "Utils::intoaV4(dst_ip, buf2ip, sizeof(buf2ip))",
     "name": "intoaV4",
     "nargs": 3
    },
    {
     "code": "sizeof(buf2ip)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "dst_ip",
    "buf2ip"
   ],
   "osv_id": "ARVO-42524654",
   "sites": [
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "buf1[32]",
     "line": 94
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "buf1ip[32]",
     "line": 94
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "buf2[32]",
     "line": 94
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "buf2ip[32]",
     "line": 94
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)"
  }
 },
 {
  "osv_id": "ARVO-42524709",
  "project": "openexr",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "res",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 100,
    "type": "libdeflate_result",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "internal_decode_alloc_buffer",
    "file": "/src/openexr/src/lib/OpenEXRCore/coding.c",
    "line": 261
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "libdeflate_alloc_decompressor"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 106,
    "fn": "exr_uncompress_buffer",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "exr_uncompress_buffer",
    "file": "/src/openexr/src/lib/OpenEXRCore/compression.c",
    "line": 106
   },
   "code": "res = libdeflate_zlib_decompress_ex (",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "exr_uncompress_buffer",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openexr/address/7c40603eb2812148c6a99fbb6ee07533395fdadb/ARVO-42524709/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openexr_7c40603eb281.cpg",
   "testcase_size": 197
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
   "dedup_token": "libdeflate_zlib_decompress_ex--exr_uncompress_buffer--DwaCompressor_uncompress"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "res = libdeflate_zlib_decompress_ex (",
     "line": 106
    }
   ],
   "entity_decl": {
    "line": 100,
    "type": "libdeflate_result"
   },
   "entity_name_cpg": "res",
   "func_lines": [
    92,
    126
   ],
   "func_params": {
    "names": [
     "in",
     "in_bytes",
     "out",
     "out_bytes_avail",
     "actual_out"
    ],
    "types": [
     "void*",
     "size_t",
     "void*",
     "size_t",
     "size_t*"
    ]
   },
   "guards": [
    {
     "code": "res == LIBDEFLATE_SUCCESS",
     "line": 117
    },
    {
     "code": "in_bytes == actual_in_bytes",
     "line": 119
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "res = libdeflate_zlib_decompress_ex (",
     "name": "<operator>.assignment",
     "nargs": null
    },
    {
     "code": "libdeflate_zlib_decompress_ex (",
     "name": "libdeflate_zlib_decompress_ex",
     "nargs": null
    }
   ],
   "line_ids": [
    "res"
   ],
   "osv_id": "ARVO-42524709",
   "sites": [
    {
     "args": "",
     "callee": "libdeflate_alloc_decompressor",
     "code": "libdeflate_alloc_decompressor ()",
     "line": 103
    },
    {
     "args": "decomp",
     "callee": "libdeflate_free_decompressor",
     "code": "libdeflate_free_decompressor (decomp)",
     "line": 115
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "exr_uncompress_buffer"
  }
 },
 {
  "osv_id": "ARVO-42524740",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "NULL",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 237
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "s",
   "size_expr_cpg_callee": "HDstrdup"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 172,
    "fn": "H5MM_xstrdup",
    "code": "HDstrdup(s)",
    "origin": "report:crash",
    "args": "s"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5MM_xstrdup",
    "file": "/src/hdf5/src/H5MM.c",
    "line": 172
   },
   "code": "NULL == (ret_value = HDstrdup(s))",
   "access": {
    "dir": "READ",
    "width": 5,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5MM_xstrdup",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42524740/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "testcase_size": 1032
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "strdup--H5MM_xstrdup--H5G__ent_to_link"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "NULL",
   "func_lines": [
    164,
    176
   ],
   "func_params": {
    "names": [
     "s"
    ],
    "types": [
     "char*"
    ]
   },
   "guards": [
    {
     "code": "'_' != ((const char *)__func__)[2]",
     "line": 169
    },
    {
     "code": "'_' != ((const char *)__func__)[3]",
     "line": 169
    },
    {
     "code": "'_' == ((const char *)__func__)[4]",
     "line": 169
    },
    {
     "code": "NULL == (ret_value = HDstrdup(s))",
     "line": 172
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "NULL == (ret_value = HDstrdup(s))",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "ret_value = HDstrdup(s)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "HDstrdup(s)",
     "name": "HDstrdup",
     "nargs": 1
    },
    {
     "code": "strdup(s)",
     "name": "strdup",
     "nargs": 1
    }
   ],
   "line_ids": [
    "NULL",
    "ret_value",
    "s"
   ],
   "osv_id": "ARVO-42524740",
   "sites": [
    {
     "args": "s",
     "callee": "HDstrdup",
     "code": "HDstrdup(s)",
     "line": 172
    },
    {
     "args": "s",
     "callee": "strdup",
     "code": "strdup(s)",
     "line": 172
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5MM_xstrdup"
  }
 },
 {
  "osv_id": "ARVO-42524849",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "buffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "line": 91,
    "size": null,
    "type": "char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 98,
    "fn": "ndpi_check_punycode_string",
    "code": "buffer[i+3] == '-' | buffer[i+3] | i+3",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_check_punycode_string",
    "file": "/src/ndpi/src/lib/ndpi_utils.c",
    "line": 98
   },
   "code": "buffer[i+3] == '-' | buffer[i+3] | i+3",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_check_punycode_string",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "WHILE:94,IF:95"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "buffer"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/998bedbbb731e369451298b891ffeb37245a7d96/ARVO-42524849/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_998bedbbb731.cpg",
   "testcase_size": 48
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
   "dedup_token": "ndpi_check_punycode_string--ndpi_match_host_subprotocol--ndpi_http_parse_subprotocol"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 91,
    "type": "char*"
   },
   "entity_name_cpg": "buffer",
   "func_lines": [
    91,
    105
   ],
   "func_params": {
    "names": [
     "buffer",
     "len"
    ],
    "types": [
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "i++ < len - 3",
     "line": 94
    },
    {
     "code": "buffer[i] == 'x'",
     "line": 95
    },
    {
     "code": "buffer[i+1] == 'n'",
     "line": 96
    },
    {
     "code": "buffer[i+2] == '-'",
     "line": 97
    },
    {
     "code": "buffer[i+3] == '-'",
     "line": 98
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "buffer[i+3] == '-'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "buffer[i+3]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i+3",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "buffer",
    "i"
   ],
   "osv_id": "ARVO-42524849",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_check_punycode_string"
  }
 },
 {
  "osv_id": "ARVO-42524929",
  "project": "serenity",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "m_data_ptr",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 183,
    "fn": "read_u8",
    "code": "*(m_data_ptr++) | m_data_ptr++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_u8",
    "file": "/src/serenity/Userland/Libraries/LibGfx/BMPLoader.cpp",
    "line": 183
   },
   "code": "*(m_data_ptr++) | m_data_ptr++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "read_u8",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/ed84a6f6ee4a620e936c53f91407cd04fe2b7106/ARVO-42524929/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_ed84a6f6ee4a.cpg",
   "testcase_size": 54
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "read_u8--read_u16--Gfx::InputStreamer::read_u32()"
  },
  "deep": {
   "entity_assignments": [],
   "entity_name_cpg": "m_data_ptr",
   "func_lines": [
    179,
    184
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "Gfx.InputStreamer"
    ]
   },
   "guards": [],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "*(m_data_ptr++)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "m_data_ptr++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "m_data_ptr"
   ],
   "osv_id": "ARVO-42524929",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "read_u8"
  }
 },
 {
  "osv_id": "ARVO-42524965",
  "project": "wolfssl",
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
    "fn": "wolfCrypt_custom_malloc",
    "file": "/src/wolf-ssl-ssh-fuzzers/oss-fuzz/projects/wolf-ssl-ssh/fuzzers/include/fuzzers/shared.h",
    "line": 189
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": null,
    "file": null,
    "line": null
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 9,
    "region_bytes": null
   }
  },
  "context": {
   "fn": null,
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/b2a6203ec01fcc5d55ab37b3d0e85ab160e962d4/ARVO-42524965/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_b2a6203ec01f.cpg",
   "testcase_size": 260
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
   "dedup_token": "__asan_memset--BundlePacket--SendChannelExit"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": null
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