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
  "osv_id": "OSV-2021-973",
  "project": "c-blosc2",
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
    "fn": "malloc",
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "line": 67
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2192,
    "fn": "initialize_context_decompression",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "initialize_context_decompression",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 2192
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "initialize_context_decompression",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-973.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_886d4c9b7833.cpg",
   "testcase_size": 271
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
   "loc_size": 271,
   "loc_offset": 31,
   "loc_kind": "region",
   "dedup_token": "initialize_context_decompression--blosc_run_decompression_with_context--blosc2_decompress_ctx",
   "overshoot_ratio": 0.114391
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    2116,
    2209
   ],
   "func_params": {
    "names": [
     "context",
     "header",
     "src",
     "srcsize",
     "dest",
     "destsize"
    ],
    "types": [
     "blosc2_context*",
     "blosc_header*",
     "void*",
     "int32_t",
     "void*",
     "int32_t"
    ]
   },
   "guards": [
    {
     "code": "rc < 0",
     "line": 2129
    },
    {
     "code": "context->sourcesize > (int32_t)context->destsize",
     "line": 2134
    },
    {
     "code": "context->block_maskout != NULL",
     "line": 2138
    },
    {
     "code": "context->block_maskout_nitems != context->nblocks",
     "line": 2138
    },
    {
     "code": "context->special_type > BLOSC2_SPECIAL_LASTID",
     "line": 2146
    },
    {
     "code": "header->cbytes != header->nbytes + context->header_overhead",
     "line": 2153
    },
    {
     "code": "header->nbytes == 0",
     "line": 2158
    },
    {
     "code": "header->cbytes == context->header_overhead",
     "line": 2158
    },
    {
     "code": "srcsize < bstarts_end",
     "line": 2171
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "OSV-2021-973",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "initialize_context_decompression"
  }
 },
 {
  "osv_id": "OSV-2021-997",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "internalBuffer",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 134,
    "fn": "ZSTD_initDDict_internal",
    "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ZSTD_initDDict_internal",
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/decompress/zstd_ddict.c",
    "line": 134
   },
   "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
   "access": {
    "dir": "READ",
    "width": 61951,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ZSTD_initDDict_internal",
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
   "ddict",
   "dict",
   "dictSize"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-997.log",
   "cpg": null,
   "testcase_size": 24087
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "loc_size": 24087,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--ZSTD_initDDict_internal--ZSTD_createDDict_advanced",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ZSTD_initDDict_internal"
  }
 },
 {
  "osv_id": "OSV-2022-1004",
  "project": "hunspell",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1355,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>& std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::__assign_no_alias<true>(char const*, unsigned int) (/out/affdicfuzzer+0x3353bf)",
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
    "line": 1356,
    "fn": "AffixMgr::cpdcase_check(char const*, int)",
    "code": "p = word + pos - 1 | word + pos - 1 | word + pos | (*p & 0xc0) == 0x80",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AffixMgr::cpdcase_check(char const*, int)",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 1356
   },
   "code": "p = word + pos - 1 | word + pos - 1 | word + pos | (*p & 0xc0) == 0x80",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cpdcase_check",
   "in_loop": true,
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
   "word",
   "pos"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1004.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_52021df98d3b.cpg",
   "testcase_size": 1235
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "loc_size": 40,
   "loc_offset": 1,
   "loc_kind": "region",
   "dedup_token": "AffixMgr::cpdcase_check(char const*, int)--AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&,",
   "overshoot_ratio": 0.025
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "p = word + pos - 1",
     "line": 1356
    }
   ],
   "entity_decl": {
    "line": 1355,
    "type": "char*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    1353,
    1374
   ],
   "func_params": {
    "names": [
     "this",
     "word",
     "pos"
    ],
    "types": [
     "AffixMgr",
     "char*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "(*p & 0xc0) == 0x80",
     "line": 1356
    },
    {
     "code": "pair_u.size() > 1",
     "line": 1361
    },
    {
     "code": "unicodetoupper(a, langnum) == a",
     "line": 1363
    },
    {
     "code": "unicodetoupper(b, langnum) == b",
     "line": 1364
    },
    {
     "code": "a != '-'",
     "line": 1365
    },
    {
     "code": "b != '-'",
     "line": 1365
    },
    {
     "code": "a != '-'",
     "line": 1370
    },
    {
     "code": "b != '-'",
     "line": 1370
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "p = word + pos - 1",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "word + pos - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "word + pos",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(*p & 0xc0) == 0x80",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*p & 0xc0",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "*p",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "p--",
     "name": "<operator>.postDecrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "p",
    "word",
    "pos"
   ],
   "osv_id": "OSV-2022-1004",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AffixMgr::cpdcase_check(char const*, int)"
  }
 },
 {
  "osv_id": "OSV-2022-1028",
  "project": "hunspell",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1627,
    "type": "int",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate<char>",
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "line": 43
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1882,
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "code": "i > 2 && word[i - 1] == word[i - 2] | i > 2 | word[i - 1] == word[i - 2] | word[i - 1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 1882
   },
   "code": "i > 2 && word[i - 1] == word[i - 2] | i > 2 | word[i - 1] == word[i - 2] | word[i - 1]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "compound_check",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < cmax | i >= cmax | i > st.size()",
   "guard_count": 8
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "this",
   "word",
   "wordnum",
   "numsyllable",
   "maxwordnum",
   "wnum",
   "rwords",
   "hu_mov_rule",
   "is_sug",
   "info"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1028.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_96a0c2e82ad9.cpg",
   "testcase_size": 10971
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "loc_size": 56,
   "loc_offset": 9,
   "loc_kind": "region",
   "dedup_token": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hent",
   "overshoot_ratio": 0.160714
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "i = cmin",
     "line": 1627
    },
    {
     "code": "i = soldi",
     "line": 2161
    },
    {
     "code": "i = soldi",
     "line": 2177
    }
   ],
   "entity_decl": {
    "line": 1627,
    "type": "int"
   },
   "entity_name_cpg": "i",
   "func_lines": [
    1578,
    2188
   ],
   "func_params": {
    "names": [
     "this",
     "word",
     "wordnum",
     "numsyllable",
     "maxwordnum",
     "wnum",
     "words",
     "rwords",
     "hu_mov_rule",
     "is_sug",
     "info"
    ],
    "types": [
     "AffixMgr",
     "std.string&",
     "short",
     "short",
     "short",
     "short",
     "hentry**",
     "hentry**",
     "char",
     "char",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "wordnum == 0",
     "line": 1613
    },
    {
     "code": "timelimit != 0",
     "line": 1619
    },
    {
     "code": "clock() > timelimit + TIMELIMIT",
     "line": 1619
    },
    {
     "code": "i < cmax",
     "line": 1627
    },
    {
     "code": "(st[i] & 0xc0) == 0x80",
     "line": 1630
    },
    {
     "code": "timelimit == 0",
     "line": 1647
    },
    {
     "code": "scpd > 0",
     "line": 1650
    },
    {
     "code": "word.compare(i, checkcpdtable[scpd - 1].pattern3.size(), checkcpdtable[scpd - 1].pattern3) != 0",
     "line": 1653
    },
    {
     "code": "scpd > checkcpdtable.size()",
     "line": 1657
    },
    {
     "code": "i > st.size()",
     "line": 1677
    },
    {
     "code": "scpd != 0",
     "line": 1711
    },
    {
     "code": "checkcpdtable[scpd - 1].cond != FLAG_NULL",
     "line": 1711
    },
    {
     "code": "wordnum == 0",
     "line": 1742
    },
    {
     "code": "wordnum > 0",
     "line": 1753
    },
    {
     "code": "wordnum == 0",
     "line": 1796
    },
    {
     "code": "oldwordnum == 0",
     "line": 1823
    },
    {
     "code": "oldwordnum > 0",
     "line": 1825
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1829
    },
    {
     "code": "scpd == 0",
     "line": 1839
    },
    {
     "code": "checkcpdtable[scpd - 1].cond == FLAG_NULL",
     "line": 1839
    },
    {
     "code": "scpd == 0",
     "line": 1841
    },
    {
     "code": "word[i - 1] == word[i]",
     "line": 1843
    },
    {
     "code": "i > 1",
     "line": 1844
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1844
    },
    {
     "code": "word[i - 1] == word[i + 1]",
     "line": 1845
    },
    {
     "code": "scpd == 0",
     "line": 1847
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1850
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1861
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 1866
    },
    {
     "code": "i > 2",
     "line": 1882
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1882
    },
    {
     "code": "scpd != 0",
     "line": 1897
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 != FLAG_NULL",
     "line": 1897
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1917
    },
    {
     "code": "cpdwordmax == -1",
     "line": 1946
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 1946
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 1947
    },
    {
     "code": "scpd != 0",
     "line": 1952
    },
    {
     "code": "rv != rv_first",
     "line": 1954
    },
    {
     "code": "scpd == 0",
     "line": 1957
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1957
    },
    {
     "code": "i < word.size()",
     "line": 1973
    },
    {
     "code": "i < word.size()",
     "line": 1980
    },
    {
     "code": "i < word.size()",
     "line": 1985
    },
    {
     "code": "scpd == 0",
     "line": 1994
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1994
    },
    {
     "code": "scpd == 0",
     "line": 1999
    },
    {
     "code": "langnum == LANG_hu",
     "line": 2032
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 2048
    },
    {
     "code": "cpdwordmax == -1",
     "line": 2083
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 2083
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 2084
    },
    {
     "code": "rv != rv_first",
     "line": 2085
    },
    {
     "code": "wordnum + 2 < maxwordnum",
     "line": 2098
    },
    {
     "code": "scpd == 0",
     "line": 2104
    },
    {
     "code": "scpd != 0",
     "line": 2106
    },
    {
     "code": "word.compare(i, rv->blen, rv->word, rv->blen) == 0",
     "line": 2125
    },
    {
     "code": "strncmp(rv2->word, st.c_str(), i + rv->blen) == 0",
     "line": 2141
    },
    {
     "code": "soldi != 0",
     "line": 2160
    },
    {
     "code": "soldi != 0",
     "line": 2176
    },
    {
     "code": "oldwordnum == 0",
     "line": 2183
    },
    {
     "code": "onlycpdrule++ < 1",
     "line": 2184
    }
   ],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "i > 2 && word[i - 1] == word[i - 2]",
     "name": "<operator>.logicalAnd",
     "nargs": 2
    },
    {
     "code": "i > 2",
     "name": "<operator>.greaterThan",
     "nargs": 2
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "word[i - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "word[i - 2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "i - 2",
     "name": "<operator>.subtraction",
     "nargs": 2
    }
   ],
   "line_ids": [
    "i",
    "word"
   ],
   "osv_id": "OSV-2022-1028",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)"
  }
 },
 {
  "osv_id": "OSV-2022-1042",
  "project": "hunspell",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "numsyllable",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1580,
    "type": "short",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate<char>",
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "line": 43
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2035,
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "code": "numsyllable += get_syllable(word.substr(i)) | get_syllable(word.substr(i)) | word.substr(i)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 2035
   },
   "code": "numsyllable += get_syllable(word.substr(i)) | get_syllable(word.substr(i)) | word.substr(i)",
   "access": {
    "dir": "READ",
    "width": 10,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "compound_check",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < cmax | i >= cmax | i > word.size()",
   "guard_count": 11
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "this",
   "word",
   "wordnum",
   "numsyllable",
   "maxwordnum",
   "wnum",
   "rwords",
   "hu_mov_rule",
   "is_sug",
   "info"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1042.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_3f0f43060c96.cpg",
   "testcase_size": 3577
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 32,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "strlen--__constexpr_strlen<char>--length",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "numsyllable = oldnumsyllable2",
     "line": 1968
    },
    {
     "code": "numsyllable = oldnumsyllable2",
     "line": 2095
    },
    {
     "code": "numsyllable = oldnumsyllable",
     "line": 2175
    }
   ],
   "entity_decl": {
    "line": 1580,
    "type": "short"
   },
   "entity_name_cpg": "numsyllable",
   "func_lines": [
    1578,
    2189
   ],
   "func_params": {
    "names": [
     "this",
     "word",
     "wordnum",
     "numsyllable",
     "maxwordnum",
     "wnum",
     "words",
     "rwords",
     "hu_mov_rule",
     "is_sug",
     "info"
    ],
    "types": [
     "AffixMgr",
     "std.string&",
     "short",
     "short",
     "short",
     "short",
     "hentry**",
     "hentry**",
     "char",
     "char",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "wordnum == 0",
     "line": 1613
    },
    {
     "code": "timelimit != 0",
     "line": 1619
    },
    {
     "code": "clock() > timelimit + TIMELIMIT",
     "line": 1619
    },
    {
     "code": "i < cmax",
     "line": 1627
    },
    {
     "code": "(st[i] & 0xc0) == 0x80",
     "line": 1630
    },
    {
     "code": "timelimit == 0",
     "line": 1647
    },
    {
     "code": "scpd > 0",
     "line": 1650
    },
    {
     "code": "i > word.size()",
     "line": 1653
    },
    {
     "code": "word.compare(i, checkcpdtable[scpd - 1].pattern3.size(), checkcpdtable[scpd - 1].pattern3) != 0",
     "line": 1654
    },
    {
     "code": "scpd > checkcpdtable.size()",
     "line": 1658
    },
    {
     "code": "i > st.size()",
     "line": 1678
    },
    {
     "code": "scpd != 0",
     "line": 1712
    },
    {
     "code": "checkcpdtable[scpd - 1].cond != FLAG_NULL",
     "line": 1712
    },
    {
     "code": "wordnum == 0",
     "line": 1743
    },
    {
     "code": "wordnum > 0",
     "line": 1754
    },
    {
     "code": "wordnum == 0",
     "line": 1797
    },
    {
     "code": "oldwordnum == 0",
     "line": 1824
    },
    {
     "code": "oldwordnum > 0",
     "line": 1826
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1830
    },
    {
     "code": "scpd == 0",
     "line": 1840
    },
    {
     "code": "checkcpdtable[scpd - 1].cond == FLAG_NULL",
     "line": 1840
    },
    {
     "code": "scpd == 0",
     "line": 1842
    },
    {
     "code": "word[i - 1] == word[i]",
     "line": 1844
    },
    {
     "code": "i > 1",
     "line": 1845
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1845
    },
    {
     "code": "word[i - 1] == word[i + 1]",
     "line": 1846
    },
    {
     "code": "scpd == 0",
     "line": 1848
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1851
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1862
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 1867
    },
    {
     "code": "i > 2",
     "line": 1883
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1883
    },
    {
     "code": "scpd != 0",
     "line": 1898
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 != FLAG_NULL",
     "line": 1898
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1918
    },
    {
     "code": "cpdwordmax == -1",
     "line": 1947
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 1947
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 1948
    },
    {
     "code": "scpd != 0",
     "line": 1953
    },
    {
     "code": "rv != rv_first",
     "line": 1955
    },
    {
     "code": "scpd == 0",
     "line": 1958
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1958
    },
    {
     "code": "i < word.size()",
     "line": 1974
    },
    {
     "code": "i < word.size()",
     "line": 1981
    },
    {
     "code": "i < word.size()",
     "line": 1986
    },
    {
     "code": "scpd == 0",
     "line": 1995
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1995
    },
    {
     "code": "scpd == 0",
     "line": 2000
    },
    {
     "code": "langnum == LANG_hu",
     "line": 2033
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 2049
    },
    {
     "code": "cpdwordmax == -1",
     "line": 2084
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 2084
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 2085
    },
    {
     "code": "rv != rv_first",
     "line": 2086
    },
    {
     "code": "wordnum + 2 < maxwordnum",
     "line": 2099
    },
    {
     "code": "scpd == 0",
     "line": 2105
    },
    {
     "code": "scpd != 0",
     "line": 2107
    },
    {
     "code": "word.compare(i, rv->blen, rv->word, rv->blen) == 0",
     "line": 2126
    },
    {
     "code": "strncmp(rv2->word, st.c_str(), i + rv->blen) == 0",
     "line": 2142
    },
    {
     "code": "soldi != 0",
     "line": 2161
    },
    {
     "code": "soldi != 0",
     "line": 2177
    },
    {
     "code": "oldwordnum == 0",
     "line": 2184
    },
    {
     "code": "onlycpdrule++ < 1",
     "line": 2185
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "numsyllable += get_syllable(word.substr(i))",
     "name": "<operator>.assignmentPlus",
     "nargs": 2
    },
    {
     "code": "get_syllable(word.substr(i))",
     "name": "get_syllable",
     "nargs": 1
    },
    {
     "code": "word.substr(i)",
     "name": "substr",
     "nargs": 2
    }
   ],
   "line_ids": [
    "numsyllable",
    "word",
    "i"
   ],
   "osv_id": "OSV-2022-1042",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)"
  }
 },
 {
  "osv_id": "OSV-2022-1054",
  "project": "hunspell",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "s1",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1069,
    "type": "char*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libcpp_allocate<char>",
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "line": 43
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1070,
    "fn": "isSubset",
    "code": "((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') && (*s2  | ((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') | (*s1 == *s2) || (*s1 == '.') | *s1 == *s2",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "isSubset",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 1070
   },
   "code": "((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') && (*s2  | ((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') | (*s1 == *s2) || (*s1 == '.') | *s1 == *s2",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "isSubset",
   "in_loop": true,
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
   "s1",
   "s2"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1054.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_5f57c6c24719.cpg",
   "testcase_size": 2729
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "loc_size": 48,
   "loc_offset": 6,
   "loc_kind": "region",
   "dedup_token": "isSubset--AffixMgr::cpdpat_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, hentry*, hentry*, char)--Affi",
   "overshoot_ratio": 0.125
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1069,
    "type": "char*"
   },
   "entity_name_cpg": "s1",
   "func_lines": [
    1069,
    1075
   ],
   "func_params": {
    "names": [
     "this",
     "s1",
     "s2"
    ],
    "types": [
     "AffixMgr",
     "char*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "*s1 == *s2",
     "line": 1070
    },
    {
     "code": "*s1 == '.'",
     "line": 1070
    },
    {
     "code": "*s1 != '\\0'",
     "line": 1070
    },
    {
     "code": "*s2 != '\\0'",
     "line": 1070
    },
    {
     "code": "*s1 == '\\0'",
     "line": 1074
    }
   ],
   "line_call_count": 12,
   "line_calls": [
    {
     "code": "((*s1 == *s2) ",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "((*s1 == *s2) ",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "(*s1 == *s2) ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "*s1 == *s2",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*s1",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*s2",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*s1 == '.'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "*s1",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*s1 != '\\0'",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "*s1",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "*s2 != '\\0'",
     "name": "<operator>.notEquals",
     "nargs": 2
    },
    {
     "code": "*s2",
     "name": "<operator>.indirection",
     "nargs": 1
    }
   ],
   "line_ids": [
    "s1",
    "s2"
   ],
   "osv_id": "OSV-2022-1054",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "isSubset"
  }
 },
 {
  "osv_id": "OSV-2022-1061",
  "project": "hunspell",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "st",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1581,
    "type": "std.string",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::replace(unsigned long, unsigned long, char const*, unsigned long) (/out/affdicfuzzer+0x358cf1)",
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
    "line": 1611,
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "code": "(st[i] & 0xc0) == 0x80 | st[i] & 0xc0 | st[i] | i++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 1611
   },
   "code": "(st[i] & 0xc0) == 0x80 | st[i] & 0xc0 | st[i] | i++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "compound_check",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < cmax | i >= cmax | i > word.size()",
   "guard_count": 12
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "this",
   "word",
   "wordnum",
   "numsyllable",
   "maxwordnum",
   "wnum",
   "rwords",
   "hu_mov_rule",
   "is_sug",
   "info"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1061.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_631800650ab3.cpg",
   "testcase_size": 2908
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 96,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hent",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "st[i] = '\\0'",
     "line": 1663
    },
    {
     "code": "st[i] = ch",
     "line": 1753
    },
    {
     "code": "st[i] = ch",
     "line": 1855
    },
    {
     "code": "st[i + rv->blen] = '\\0'",
     "line": 2111
    },
    {
     "code": "st[ + i + rv->blen] = r",
     "line": 2115
    },
    {
     "code": "st[i + rv->blen] = r",
     "line": 2129
    },
    {
     "code": "st[i] = ch",
     "line": 2165
    }
   ],
   "entity_decl": {
    "line": 1581,
    "type": "std.string"
   },
   "entity_name_cpg": "st",
   "func_lines": [
    1569,
    2172
   ],
   "func_params": {
    "names": [
     "this",
     "word",
     "wordnum",
     "numsyllable",
     "maxwordnum",
     "wnum",
     "words",
     "rwords",
     "hu_mov_rule",
     "is_sug",
     "info"
    ],
    "types": [
     "AffixMgr",
     "std.string&",
     "short",
     "short",
     "short",
     "short",
     "hentry**",
     "hentry**",
     "char",
     "char",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "wordnum == 0",
     "line": 1594
    },
    {
     "code": "timelimit != 0",
     "line": 1600
    },
    {
     "code": "clock() > timelimit + TIMELIMIT",
     "line": 1600
    },
    {
     "code": "i < cmax",
     "line": 1608
    },
    {
     "code": "(st[i] & 0xc0) == 0x80",
     "line": 1611
    },
    {
     "code": "timelimit == 0",
     "line": 1628
    },
    {
     "code": "scpd > 0",
     "line": 1631
    },
    {
     "code": "i > word.size()",
     "line": 1634
    },
    {
     "code": "word.compare(i, checkcpdtable[scpd - 1].pattern3.size(), checkcpdtable[scpd - 1].pattern3) != 0",
     "line": 1635
    },
    {
     "code": "scpd > checkcpdtable.size()",
     "line": 1639
    },
    {
     "code": "i > st.size()",
     "line": 1659
    },
    {
     "code": "scpd != 0",
     "line": 1693
    },
    {
     "code": "checkcpdtable[scpd - 1].cond != FLAG_NULL",
     "line": 1693
    },
    {
     "code": "wordnum == 0",
     "line": 1724
    },
    {
     "code": "wordnum > 0",
     "line": 1735
    },
    {
     "code": "wordnum == 0",
     "line": 1778
    },
    {
     "code": "oldwordnum == 0",
     "line": 1805
    },
    {
     "code": "oldwordnum > 0",
     "line": 1807
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1811
    },
    {
     "code": "scpd == 0",
     "line": 1821
    },
    {
     "code": "checkcpdtable[scpd - 1].cond == FLAG_NULL",
     "line": 1821
    },
    {
     "code": "scpd == 0",
     "line": 1823
    },
    {
     "code": "word[i - 1] == word[i]",
     "line": 1825
    },
    {
     "code": "i > 1",
     "line": 1826
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1826
    },
    {
     "code": "word[i - 1] == word[i + 1]",
     "line": 1827
    },
    {
     "code": "scpd == 0",
     "line": 1829
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1832
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1843
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 1848
    },
    {
     "code": "i > 2",
     "line": 1864
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1864
    },
    {
     "code": "scpd != 0",
     "line": 1879
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 != FLAG_NULL",
     "line": 1879
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1899
    },
    {
     "code": "cpdwordmax == -1",
     "line": 1928
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 1928
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 1929
    },
    {
     "code": "scpd != 0",
     "line": 1934
    },
    {
     "code": "i < word.size()",
     "line": 1935
    },
    {
     "code": "rv != rv_first",
     "line": 1936
    },
    {
     "code": "scpd == 0",
     "line": 1939
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1939
    },
    {
     "code": "i < word.size()",
     "line": 1955
    },
    {
     "code": "i < word.size()",
     "line": 1962
    },
    {
     "code": "i < word.size()",
     "line": 1967
    },
    {
     "code": "scpd == 0",
     "line": 1976
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1976
    },
    {
     "code": "scpd == 0",
     "line": 1981
    },
    {
     "code": "langnum == LANG_hu",
     "line": 2014
    },
    {
     "code": "i < word.size()",
     "line": 2015
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 2032
    },
    {
     "code": "cpdwordmax == -1",
     "line": 2067
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 2067
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 2068
    },
    {
     "code": "rv != rv_first",
     "line": 2069
    },
    {
     "code": "wordnum + 2 < maxwordnum",
     "line": 2082
    },
    {
     "code": "scpd == 0",
     "line": 2088
    },
    {
     "code": "scpd != 0",
     "line": 2090
    },
    {
     "code": "word.compare(i, rv->blen, rv->word, rv->blen) == 0",
     "line": 2109
    },
    {
     "code": "strncmp(rv2->word, st.c_str(), i + rv->blen) == 0",
     "line": 2125
    },
    {
     "code": "soldi != 0",
     "line": 2144
    },
    {
     "code": "soldi != 0",
     "line": 2160
    },
    {
     "code": "oldwordnum == 0",
     "line": 2167
    },
    {
     "code": "onlycpdrule++ < 1",
     "line": 2168
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "(st[i] & 0xc0) == 0x80",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "st[i] & 0xc0",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "st[i]",
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
    "st",
    "i"
   ],
   "osv_id": "OSV-2022-1061",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)"
  }
 },
 {
  "osv_id": "OSV-2022-1180",
  "project": "libredwg",
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
    "fn": "dwg_setup_LAYOUT",
    "file": "/src/libredwg/src/./dwg.spec",
    "line": 5069
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 50,
    "fn": "json_common_entity_data",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "json_common_entity_data",
    "file": "/src/libredwg/src/common_entity_handle_data.spec",
    "line": 50
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_common_entity_data",
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/4cf4cbdd28158f9a858f76525ab155fb1daf10fa/OSV-2022-1180",
   "cpg": null,
   "testcase_size": 16316
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
   "loc_size": 88,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "json_common_entity_data--dwg_json_LOAD--dwg_json_object",
   "overshoot_ratio": 0.090909
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "json_common_entity_data"
  }
 },
 {
  "osv_id": "OSV-2022-1211",
  "project": "libredwg",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 3280,
    "fn": "bit_calc_CRC",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_calc_CRC",
    "file": "/src/libredwg/src/bits.c",
    "line": 3280
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_calc_CRC",
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/97fd500ac19eb64c1218c41ef7582fcd41f98895/OSV-2022-1211",
   "cpg": null,
   "testcase_size": 1025
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
   "loc_size": 1025,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "bit_calc_CRC--decode_preR13--dwg_decode",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_calc_CRC"
  }
 },
 {
  "osv_id": "OSV-2022-1252",
  "project": "libredwg",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 198,
    "fn": "bit_read_BB",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_read_BB",
    "file": "/src/libredwg/src/bits.c",
    "line": 198
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_read_BB",
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/f5eb830532f3a34821132c85f019593a9f51fa3c/OSV-2022-1252",
   "cpg": null,
   "testcase_size": 205
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "loc_size": 205,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "bit_read_BB--bit_read_BD--dwg_decode_header_variables",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_read_BB"
  }
 },
 {
  "osv_id": "OSV-2022-126",
  "project": "md4c",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "next_closer",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/md4c/src/md4c.c",
    "line": 3442,
    "size": null,
    "type": "MD_MARK*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "md_push_mark",
    "file": "/src/md4c/src/md4c.c",
    "line": 2532
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 3481,
    "fn": "md_resolve_links",
    "code": "next_closer->ch == ']' | next_closer->ch",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "md_resolve_links",
    "file": "/src/md4c/src/md4c.c",
    "line": 3481
   },
   "code": "next_closer->ch == ']' | next_closer->ch",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "md_resolve_links",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "next_closer != NULL",
   "guard_count": 1,
   "control_structures": "WHILE:3436,IF:3448,ELSE:3451,IF:3463,CONTINUE:3468,IF:3474,WHILE:3495,IF:3497,BREAK:3499,IF:3501,BREAK:3502,IF:3507"
  },
  "call_chain": [],
  "types": {
   "entity_type": "MD_MARK*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "ctx",
   "lines"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-126.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/md4c_62b60979f6a2.cpg",
   "testcase_size": 43679
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
   "loc_size": 248840,
   "loc_offset": 4,
   "loc_kind": "region",
   "dedup_token": "md_resolve_links--md_analyze_inlines--md_process_normal_block_contents",
   "overshoot_ratio": 1.6e-05
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "next_closer = &ctx->marks[next_opener->next]",
     "line": 3450
    },
    {
     "code": "next_closer = NULL",
     "line": 3453
    }
   ],
   "entity_decl": {
    "line": 3442,
    "type": "MD_MARK*"
   },
   "entity_name_cpg": "next_closer",
   "func_lines": [
    3427,
    3688
   ],
   "func_params": {
    "names": [
     "ctx",
     "lines",
     "n_lines"
    ],
    "types": [
     "MD_CTX*",
     "MD_LINE*",
     "int"
    ]
   },
   "guards": [
    {
     "code": "opener->beg < last_link_beg",
     "line": 3463
    },
    {
     "code": "closer->end < last_link_end",
     "line": 3463
    },
    {
     "code": "opener->beg < last_img_beg",
     "line": 3464
    },
    {
     "code": "closer->end < last_img_end",
     "line": 3464
    },
    {
     "code": "opener->beg < last_link_end",
     "line": 3465
    },
    {
     "code": "opener->ch == '['",
     "line": 3465
    },
    {
     "code": "opener->end - opener->beg == 1",
     "line": 3475
    },
    {
     "code": "next_opener != NULL",
     "line": 3476
    },
    {
     "code": "next_opener->ch == '['",
     "line": 3477
    },
    {
     "code": "next_opener->beg == opener->beg - 1",
     "line": 3478
    },
    {
     "code": "next_opener->end - next_opener->beg == 1",
     "line": 3479
    },
    {
     "code": "next_closer != NULL",
     "line": 3480
    },
    {
     "code": "next_closer->ch == ']'",
     "line": 3481
    },
    {
     "code": "next_closer->beg == closer->beg + 1",
     "line": 3482
    },
    {
     "code": "next_closer->end - next_closer->beg == 1",
     "line": 3483
    },
    {
     "code": "delim_index < closer_index",
     "line": 3495
    },
    {
     "code": "m->ch == '",
     "line": 3497
    },
    {
     "code": "m->ch != 'D'",
     "line": 3501
    },
    {
     "code": "m->beg - opener->end > 100",
     "line": 3501
    },
    {
     "code": "delim != NULL",
     "line": 3506
    },
    {
     "code": "dest_end - dest_beg == 0",
     "line": 3507
    },
    {
     "code": "dest_end - dest_beg > 100",
     "line": 3507
    },
    {
     "code": "off < dest_end",
     "line": 3513
    },
    {
     "code": "(((ctx->text[(off)]))) == ('\\r')",
     "line": 3514
    },
    {
     "code": "(((ctx->text[(off)]))) == ('\\n')",
     "line": 3514
    },
    {
     "code": "delim != NULL",
     "line": 3522
    },
    {
     "code": "delim->end < closer->beg",
     "line": 3523
    },
    {
     "code": "delim != NULL",
     "line": 3547
    },
    {
     "code": "next_opener != NULL",
     "line": 3555
    },
    {
     "code": "next_opener->beg == closer->end",
     "line": 3555
    },
    {
     "code": "next_closer->beg > closer->end + 1",
     "line": 3556
    },
    {
     "code": "is_link < 0",
     "line": 3566
    },
    {
     "code": "closer->end < ctx->size",
     "line": 3578
    },
    {
     "code": "CH(closer->end) == _T('(')",
     "line": 3578
    },
    {
     "code": "is_link < 0",
     "line": 3583
    },
    {
     "code": "i < ctx->n_marks",
     "line": 3591
    },
    {
     "code": "(mark->flags & (MD_MARK_OPENER ",
     "line": 3596
    },
    {
     "code": "is_link < 0",
     "line": 3622
    },
    {
     "code": "opener->ch == '['",
     "line": 3645
    },
    {
     "code": "first_nested->ch == _T('D')",
     "line": 3663
    },
    {
     "code": "first_nested < closer",
     "line": 3663
    },
    {
     "code": "first_nested->ch == _T('D')",
     "line": 3667
    },
    {
     "code": "last_nested > opener",
     "line": 3667
    },
    {
     "code": "first_nested->beg == opener->end",
     "line": 3671
    },
    {
     "code": "(first_nested->ch) != '\\0'",
     "line": 3672
    },
    {
     "code": "strchr((\"@:.\"), (first_nested->ch)) != NULL",
     "line": 3672
    },
    {
     "code": "first_nested->next == (last_nested - ctx->marks)",
     "line": 3673
    },
    {
     "code": "last_nested->end == closer->beg",
     "line": 3674
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "next_closer->ch == ']'",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "next_closer->ch",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "next_closer"
   ],
   "osv_id": "OSV-2022-126",
   "sites": [
    {
     "args": "attr.title",
     "callee": "free",
     "code": "free(attr.title)",
     "line": 3600
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "md_resolve_links"
  }
 },
 {
  "osv_id": "OSV-2022-1260",
  "project": "hunspell",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "a",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 1359,
    "type": "short unsigned",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>& std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::__assign_no_alias<true>(char const*, unsigned long) (/out/affdicfuzzer+0x3599e6)",
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
    "line": 1366,
    "fn": "AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)",
    "code": "a = word[pos - 1] | word[pos - 1] | pos - 1 | b = word[pos]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 1366
   },
   "code": "a = word[pos - 1] | word[pos - 1] | pos - 1 | b = word[pos]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cpdcase_check",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "unicodetoupper(a, langnum) == a | unicodetoupper(b, langnum) == b | a != '-'",
   "guard_count": 6
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "word",
   "pos"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1260.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_379716df74b5.cpg",
   "testcase_size": 16367
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "loc_size": 104,
   "loc_offset": 24,
   "loc_kind": "region",
   "dedup_token": "AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)--AffixMgr::compound_check(std::__1::ba",
   "overshoot_ratio": 0.230769
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "a = pair_u.size() > 1 ? (unsigned short)pair_u[1] : 0",
     "line": 1359
    },
    {
     "code": "a = word[pos - 1]",
     "line": 1366
    }
   ],
   "entity_decl": {
    "line": 1359,
    "type": "short unsigned"
   },
   "entity_name_cpg": "a",
   "func_lines": [
    1350,
    1371
   ],
   "func_params": {
    "names": [
     "this",
     "word",
     "pos"
    ],
    "types": [
     "AffixMgr",
     "std.string&",
     "int"
    ]
   },
   "guards": [
    {
     "code": "p > wordp",
     "line": 1354
    },
    {
     "code": "(*p & 0xc0) == 0x80",
     "line": 1354
    },
    {
     "code": "pair_u.size() > 1",
     "line": 1359
    },
    {
     "code": "unicodetoupper(a, langnum) == a",
     "line": 1361
    },
    {
     "code": "unicodetoupper(b, langnum) == b",
     "line": 1362
    },
    {
     "code": "a != '-'",
     "line": 1363
    },
    {
     "code": "b != '-'",
     "line": 1363
    },
    {
     "code": "a != '-'",
     "line": 1367
    },
    {
     "code": "b != '-'",
     "line": 1367
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "a = word[pos - 1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "word[pos - 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "pos - 1",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "b = word[pos]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "word[pos]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "a",
    "word",
    "pos",
    "b"
   ],
   "osv_id": "OSV-2022-1260",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)"
  }
 },
 {
  "osv_id": "OSV-2022-33",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "op",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 438,
    "type": "uint8_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "my_malloc",
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "line": 173
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 462,
    "fn": "ndlz8_decompress",
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndlz8_decompress",
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "line": 462
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "access": {
    "dir": "WRITE",
    "width": 201851904,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndlz8_decompress",
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
   "input",
   "output"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-33.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
   "testcase_size": 73
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "loc_size": 804,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memset--ndlz8_decompress--blosc_d",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "* op = (uint8_t*)output",
     "line": 438
    }
   ],
   "entity_decl": {
    "line": 438,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "op",
   "func_lines": [
    429,
    575
   ],
   "func_params": {
    "names": [
     "input",
     "input_len",
     "output",
     "output_len",
     "meta",
     "dparams"
    ],
    "types": [
     "uint8_t*",
     "int32_t",
     "uint8_t*",
     "int32_t",
     "uint8_t",
     "blosc2_dparams*"
    ]
   },
   "guards": [
    {
     "code": "input_len < 8",
     "line": 444
    },
    {
     "code": "ndim != 2",
     "line": 451
    },
    {
     "code": "i < 2",
     "line": 465
    },
    {
     "code": "ii[0] < i_stop[0]",
     "line": 476
    },
    {
     "code": "ii[1] < i_stop[1]",
     "line": 477
    },
    {
     "code": "ip > ip_limit",
     "line": 478
    },
    {
     "code": "ii[0] == i_stop[0] - 1",
     "line": 484
    },
    {
     "code": "blockshape[0] % cell_shape == 0",
     "line": 485
    },
    {
     "code": "ii[1] == i_stop[1] - 1",
     "line": 489
    },
    {
     "code": "blockshape[1] % cell_shape == 0",
     "line": 490
    },
    {
     "code": "token == 0",
     "line": 496
    },
    {
     "code": "token == (uint8_t)((1U << 7U) ",
     "line": 499
    },
    {
     "code": "token == (uint8_t)(1U << 6U)",
     "line": 503
    },
    {
     "code": "match_type == 21",
     "line": 507
    },
    {
     "code": "l < 3",
     "line": 512
    },
    {
     "code": "l < cell_shape",
     "line": 516
    },
    {
     "code": "l < row",
     "line": 517
    },
    {
     "code": "l > row + 2",
     "line": 517
    },
    {
     "code": "match_type == 17",
     "line": 522
    },
    {
     "code": "l < 2",
     "line": 527
    },
    {
     "code": "l < cell_shape",
     "line": 531
    },
    {
     "code": "l < row",
     "line": 532
    },
    {
     "code": "l > row + 1",
     "line": 532
    },
    {
     "code": "i < (uint32_t) cell_shape",
     "line": 545
    },
    {
     "code": "i < padding[0]",
     "line": 546
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 552
    },
    {
     "code": "ind != (blockshape[0] * blockshape[1])",
     "line": 565
    },
    {
     "code": "ind > (uint32_t) output_len",
     "line": 569
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "memset(op, 0, blockshape[0] * blockshape[1])",
     "name": "memset",
     "nargs": 3
    },
    {
     "code": "blockshape[0] * blockshape[1]",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "blockshape[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "blockshape[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "op",
    "blockshape"
   ],
   "osv_id": "OSV-2022-33",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "blockshape[2]",
     "line": 440
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "eshape[2]",
     "line": 441
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "i_stop[2]",
     "line": 464
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "ii[2]",
     "line": 471
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "padding[2]",
     "line": 472
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 474
    },
    {
     "args": "cell_size",
     "callee": "malloc",
     "code": "malloc(cell_size)",
     "line": 475
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 480
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 481
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 539
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 540
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 554
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 555
    },
    {
     "args": "cell_aux",
     "callee": "free",
     "code": "free(cell_aux)",
     "line": 562
    },
    {
     "args": "local_buffer",
     "callee": "free",
     "code": "free(local_buffer)",
     "line": 563
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndlz8_decompress"
  }
 },
 {
  "osv_id": "OSV-2022-34",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "dest",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 321,
    "type": "void*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "8",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 469,
    "fn": "LZ4_wildCopy32",
    "code": "vst1_lane_u8(dest + k + j * size * elem_size / (8 * elem | dest + k + j * size * elem_size / (8 * elem_size) + 8 *  | dest + k + j * size * elem_size / (8 * elem_size) | dest + k",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "LZ4_wildCopy32",
    "file": "/src/c-blosc2/internal-complibs/lz4-1.9.3/lz4.c",
    "line": 469
   },
   "code": "vst1_lane_u8(dest + k + j * size * elem_size / (8 * elem | dest + k + j * size * elem_size / (8 * elem_size) + 8 *  | dest + k + j * size * elem_size / (8 * elem_size) | dest + k",
   "access": {
    "dir": "READ",
    "width": 16,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bitshuffle16_neon",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "j < 8",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "src",
   "dest",
   "size",
   "elem_size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-34.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5a50726608d0.cpg",
   "testcase_size": 270
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "loc_size": 270,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--LZ4_wildCopy32--LZ4_decompress_generic",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 321,
    "type": "void*"
   },
   "entity_name_cpg": "dest",
   "func_lines": [
    320,
    479
   ],
   "func_params": {
    "names": [
     "src",
     "dest",
     "size",
     "elem_size"
    ],
    "types": [
     "void*",
     "void*",
     "size_t",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "i < size * elem_size",
     "line": 332
    },
    {
     "code": "j < 8",
     "line": 360
    }
   ],
   "line_call_count": 14,
   "line_calls": [
    {
     "code": "vst1_lane_u8(dest + k + j * size * elem_size / (8 * elem_size) + 8 * size * elem_size / 16, r0[4].val[0], 0)",
     "name": "vst1_lane_u8",
     "nargs": 3
    },
    {
     "code": "dest + k + j * size * elem_size / (8 * elem_size) + 8 * size * elem_size / 16",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "dest + k + j * size * elem_size / (8 * elem_size)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "dest + k",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "j * size * elem_size / (8 * elem_size)",
     "name": "<operator>.division",
     "nargs": 2
    },
    {
     "code": "j * size * elem_size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "j * size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "8 * elem_size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "8 * size * elem_size / 16",
     "name": "<operator>.division",
     "nargs": 2
    },
    {
     "code": "8 * size * elem_size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "8 * size",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "r0[4].val[0]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "r0[4].val",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "r0[4]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "dest",
    "k",
    "j",
    "size",
    "elem_size",
    "r0"
   ],
   "osv_id": "OSV-2022-34",
   "sites": [
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "r0[8]",
     "line": 324
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "r1[8]",
     "line": 325
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "r2[8]",
     "line": 326
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "xr[8] = {0, 1, 2, 3, 4, 5, 6, 7}",
     "line": 328
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "LZ4_wildCopy32"
  }
 },
 {
  "osv_id": "OSV-2022-42",
  "project": "md4c",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "str",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
    "line": 817,
    "fn": "md_decode_utf8__",
    "code": "!IS_UTF8_LEAD1(str[0]) | IS_UTF8_LEAD1(str[0]) | str[0] | (unsigned char)(str[0]) <= 0x7f",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "md_decode_utf8__",
    "file": "/src/md4c/src/md4c.c",
    "line": 817
   },
   "code": "!IS_UTF8_LEAD1(str[0]) | IS_UTF8_LEAD1(str[0]) | str[0] | (unsigned char)(str[0]) <= 0x7f",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "md_decode_utf8__",
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
   "str"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-42.log",
   "cpg": null,
   "testcase_size": 42
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
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "loc_size": 42,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "md_decode_utf8__--md_decode_unicode--md_link_label_hash",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "md_decode_utf8__"
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