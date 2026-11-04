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
  "osv_id": "OSV-2023-430",
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
    "code": "NULL == (ret_value = HDstrdup(s)) | ret_value = HDstrdup(s) | HDstrdup(s) | strdup(s)",
    "origin": "report:crash",
    "args": "s"
   },
   {
    "code": "strdup(s)",
    "fn": "H5MM_xstrdup",
    "kind": "strdup",
    "line": 172,
    "origin": "cpg",
    "args": "s"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5MM_xstrdup",
    "file": "/src/hdf5/src/H5MM.c",
    "line": 172
   },
   "code": "NULL == (ret_value = HDstrdup(s)) | ret_value = HDstrdup(s) | HDstrdup(s) | strdup(s)",
   "access": {
    "dir": "READ",
    "width": 5,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5MM_xstrdup",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "NULL == (ret_value = HDstrdup(s))",
   "guard_count": 1,
   "control_structures": "IF:169,IF:171,IF:172,GOTO:173"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "s"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-430.log",
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
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "loc_size": 263,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "___interceptor_strdup--H5MM_xstrdup--H5G__ent_to_link",
   "overshoot_ratio": 0.0
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
   "osv_id": "OSV-2023-430",
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
  "osv_id": "OSV-2023-471",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "udata",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "H5C__flush_single_entry",
    "file": "/src/hdf5/src/H5Centry.c",
    "line": 537
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1437,
    "fn": "H5FS__sinfo_serialize_node_cb",
    "code": "UINT64ENCODE_VAR(*udata->image, fspace_node->sect_size,  | *udata->image | udata->image | fspace_node->sect_size",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5FS__sinfo_serialize_node_cb",
    "file": "/src/hdf5/src/H5FScache.c",
    "line": 1437
   },
   "code": "UINT64ENCODE_VAR(*udata->image, fspace_node->sect_size,  | *udata->image | udata->image | fspace_node->sect_size",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5FS__sinfo_serialize_node_cb",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "_i < udata->sect_cnt_size | _i < udata->sinfo->sect_len_size",
   "guard_count": 2
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "_item",
   "_udata"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-471.log",
   "cpg": null,
   "testcase_size": 1808
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
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "loc_size": 53,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "H5FS__sinfo_serialize_node_cb--H5SL_iterate--H5FS__cache_sinfo_serialize",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5FS__sinfo_serialize_node_cb"
  }
 },
 {
  "osv_id": "OSV-2023-508",
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
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::replace(unsigned long, unsigned long, char const*, unsigned long) (/out/affdicfuzzer+0x35b241)",
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
    "line": 1612,
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "code": "(st[i] & 0xc0) == 0x80 | st[i] & 0xc0 | st[i] | i++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 1612
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
   "guard_count": 16
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-508.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_1be974933b09.cpg",
   "testcase_size": 8209
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
   "loc_size": 464,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hent",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "st[i] = '\\0'",
     "line": 1664
    },
    {
     "code": "st[i] = ch",
     "line": 1761
    },
    {
     "code": "st[i] = ch",
     "line": 1863
    },
    {
     "code": "st[i + rv->blen] = '\\0'",
     "line": 2120
    },
    {
     "code": "st[ + i + rv->blen] = r",
     "line": 2124
    },
    {
     "code": "st[i + rv->blen] = r",
     "line": 2138
    },
    {
     "code": "st[i] = ch",
     "line": 2177
    }
   ],
   "entity_decl": {
    "line": 1581,
    "type": "std.string"
   },
   "entity_name_cpg": "st",
   "func_lines": [
    1569,
    2184
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
     "line": 1595
    },
    {
     "code": "timelimit != 0",
     "line": 1601
    },
    {
     "code": "clock() > timelimit + TIMELIMIT",
     "line": 1601
    },
    {
     "code": "i < cmax",
     "line": 1609
    },
    {
     "code": "(st[i] & 0xc0) == 0x80",
     "line": 1612
    },
    {
     "code": "timelimit == 0",
     "line": 1629
    },
    {
     "code": "scpd > 0",
     "line": 1632
    },
    {
     "code": "i > word.size()",
     "line": 1635
    },
    {
     "code": "word.compare(i, checkcpdtable[scpd - 1].pattern3.size(), checkcpdtable[scpd - 1].pattern3) != 0",
     "line": 1636
    },
    {
     "code": "scpd > checkcpdtable.size()",
     "line": 1640
    },
    {
     "code": "i > st.size()",
     "line": 1660
    },
    {
     "code": "scpd != 0",
     "line": 1701
    },
    {
     "code": "checkcpdtable[scpd - 1].cond != FLAG_NULL",
     "line": 1701
    },
    {
     "code": "wordnum == 0",
     "line": 1732
    },
    {
     "code": "wordnum > 0",
     "line": 1743
    },
    {
     "code": "wordnum == 0",
     "line": 1786
    },
    {
     "code": "oldwordnum == 0",
     "line": 1813
    },
    {
     "code": "oldwordnum > 0",
     "line": 1815
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1819
    },
    {
     "code": "scpd == 0",
     "line": 1829
    },
    {
     "code": "checkcpdtable[scpd - 1].cond == FLAG_NULL",
     "line": 1829
    },
    {
     "code": "scpd == 0",
     "line": 1831
    },
    {
     "code": "i < word.size()",
     "line": 1832
    },
    {
     "code": "word[i - 1] == word[i]",
     "line": 1833
    },
    {
     "code": "i > 1",
     "line": 1834
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1834
    },
    {
     "code": "word[i - 1] == word[i + 1]",
     "line": 1835
    },
    {
     "code": "scpd == 0",
     "line": 1837
    },
    {
     "code": "i < word.size()",
     "line": 1837
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1840
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1851
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 1856
    },
    {
     "code": "i > 2",
     "line": 1872
    },
    {
     "code": "word[i - 1] == word[i - 2]",
     "line": 1872
    },
    {
     "code": "scpd != 0",
     "line": 1887
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 != FLAG_NULL",
     "line": 1887
    },
    {
     "code": "langnum == LANG_hu",
     "line": 1907
    },
    {
     "code": "cpdwordmax == -1",
     "line": 1936
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 1936
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 1937
    },
    {
     "code": "scpd != 0",
     "line": 1942
    },
    {
     "code": "i < word.size()",
     "line": 1943
    },
    {
     "code": "rv != rv_first",
     "line": 1944
    },
    {
     "code": "scpd == 0",
     "line": 1947
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1947
    },
    {
     "code": "i < word.size()",
     "line": 1963
    },
    {
     "code": "i < word.size()",
     "line": 1970
    },
    {
     "code": "i < word.size()",
     "line": 1975
    },
    {
     "code": "scpd == 0",
     "line": 1984
    },
    {
     "code": "checkcpdtable[scpd - 1].cond2 == FLAG_NULL",
     "line": 1984
    },
    {
     "code": "scpd == 0",
     "line": 1989
    },
    {
     "code": "langnum == LANG_hu",
     "line": 2022
    },
    {
     "code": "i < word.size()",
     "line": 2023
    },
    {
     "code": "get_syllable(pfx->getKey()) > 1",
     "line": 2040
    },
    {
     "code": "cpdwordmax == -1",
     "line": 2075
    },
    {
     "code": "wordnum + 1 < cpdwordmax",
     "line": 2075
    },
    {
     "code": "cpdmaxsyllable != 0",
     "line": 2076
    },
    {
     "code": "rv != rv_first",
     "line": 2077
    },
    {
     "code": "wordnum + 2 < maxwordnum",
     "line": 2091
    },
    {
     "code": "i < word.size()",
     "line": 2096
    },
    {
     "code": "scpd == 0",
     "line": 2097
    },
    {
     "code": "scpd != 0",
     "line": 2099
    },
    {
     "code": "i < word.size()",
     "line": 2118
    },
    {
     "code": "word.compare(i, rv->blen, rv->word, rv->blen) == 0",
     "line": 2118
    },
    {
     "code": "strncmp(rv2->word, st.c_str(), i + rv->blen) == 0",
     "line": 2134
    },
    {
     "code": "soldi != 0",
     "line": 2153
    },
    {
     "code": "soldi != 0",
     "line": 2169
    },
    {
     "code": "oldwordnum == 0",
     "line": 2179
    },
    {
     "code": "onlycpdrule++ < 1",
     "line": 2180
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
   "osv_id": "OSV-2023-508",
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
  "osv_id": "OSV-2023-673",
  "project": "pcre2",
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
    "line": 5795,
    "fn": "match",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "match",
    "file": "/src/pcre2/src/pcre2_match.c",
    "line": 5795
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "match",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-673.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/pcre2_b0b3fc4c4bc4.cpg",
   "testcase_size": 10
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
   "loc_size": 10,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "match--pcre2_match_8--LLVMFuzzerTestOneInput",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    588,
    6390
   ],
   "func_params": {
    "names": [
     "start_eptr",
     "start_ecode",
     "top_bracket",
     "frame_size",
     "match_data",
     "mb"
    ],
    "types": [
     "PCRE2_SPTR",
     "PCRE2_SPTR",
     "uint16_t",
     "PCRE2_SIZE",
     "pcre2_match_data*",
     "match_block*"
    ]
   },
   "guards": [
    {
     "code": "match_data->heapframes_size == PCRE2_SIZE_MAX - 1",
     "line": 674
    },
    {
     "code": "new == NULL",
     "line": 695
    },
    {
     "code": "group_frame_type != 0",
     "line": 762
    },
    {
     "code": "GF_IDMASK(group_frame_type) == GF_RECURSE",
     "line": 765
    },
    {
     "code": "Fcurrent_recurse == RECURSE_UNSET",
     "line": 799
    },
    {
     "code": "offset == PCRE2_UNSET",
     "line": 805
    },
    {
     "code": "N->group_frame_type == (GF_CAPTURE ",
     "line": 808
    },
    {
     "code": "Feptr > mb->last_used_ptr",
     "line": 827
    },
    {
     "code": "Fcurrent_recurse != RECURSE_UNSET",
     "line": 838
    },
    {
     "code": "offset == PCRE2_UNSET",
     "line": 843
    },
    {
     "code": "GF_IDMASK(N->group_frame_type) == GF_RECURSE",
     "line": 846
    },
    {
     "code": "Feptr == Fstart_match",
     "line": 868
    },
    {
     "code": "(mb->moptions & PCRE2_NOTEMPTY) != 0",
     "line": 869
    },
    {
     "code": "(mb->moptions & PCRE2_NOTEMPTY_ATSTART) != 0",
     "line": 870
    },
    {
     "code": "Fstart_match == mb->start_subject + mb->start_offset",
     "line": 871
    },
    {
     "code": "Feptr < mb->end_subject",
     "line": 878
    },
    {
     "code": "((mb->moptions ",
     "line": 879
    },
    {
     "code": "Fop == OP_END",
     "line": 881
    },
    {
     "code": "Feptr > mb->last_used_ptr",
     "line": 895
    },
    {
     "code": "top_bracket + 1 > match_data->oveccount",
     "line": 902
    },
    {
     "code": "mb->nltype != 0",
     "line": 914
    },
    {
     "code": "(F->eptr) < mb->end_subject",
     "line": 914
    },
    {
     "code": "UCHAR21TEST(F->eptr) == mb->nl[0]",
     "line": 914
    },
    {
     "code": "mb->nllen == 1",
     "line": 914
    },
    {
     "code": "UCHAR21TEST(F->eptr + 1) == mb->nl[1]",
     "line": 914
    },
    {
     "code": "mb->partial != 0",
     "line": 915
    },
    {
     "code": "Feptr == mb->end_subject - 1",
     "line": 916
    },
    {
     "code": "NLBLOCK->nltype == NLTYPE_FIXED",
     "line": 917
    },
    {
     "code": "NLBLOCK->nllen == 2",
     "line": 918
    },
    {
     "code": "UCHAR21TEST(Feptr) == NLBLOCK->nl[0]",
     "line": 919
    },
    {
     "code": "mb->partial > 1",
     "line": 922
    },
    {
     "code": "mb->partial != 0",
     "line": 931
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 931
    },
    {
     "code": "mb->partial > 1",
     "line": 931
    },
    {
     "code": "mb->partial != 0",
     "line": 950
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 950
    },
    {
     "code": "mb->partial > 1",
     "line": 950
    },
    {
     "code": "mb->end_subject - Feptr < 1",
     "line": 983
    },
    {
     "code": "mb->partial != 0",
     "line": 985
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 985
    },
    {
     "code": "mb->partial > 1",
     "line": 985
    },
    {
     "code": "Fecode[1] != *Feptr++",
     "line": 988
    },
    {
     "code": "mb->partial != 0",
     "line": 1003
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1003
    },
    {
     "code": "mb->partial > 1",
     "line": 1003
    },
    {
     "code": "TABLE_GET(Fecode[1], mb->lcc, Fecode[1])",
     "line": 1065
    },
    {
     "code": "mb->partial != 0",
     "line": 1080
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1080
    },
    {
     "code": "mb->partial > 1",
     "line": 1080
    },
    {
     "code": "ch == fc",
     "line": 1136
    },
    {
     "code": "Fop == OP_NOTI",
     "line": 1136
    },
    {
     "code": "TABLE_GET(ch, mb->fcc, ch) == fc",
     "line": 1136
    },
    {
     "code": "Fop < OP_STARI",
     "line": 1220
    },
    {
     "code": "mb->partial != 0",
     "line": 1373
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1373
    },
    {
     "code": "mb->partial > 1",
     "line": 1373
    },
    {
     "code": "Lc != cc",
     "line": 1377
    },
    {
     "code": "Loc != cc",
     "line": 1377
    },
    {
     "code": "Lmin == Lmax",
     "line": 1380
    },
    {
     "code": "reptype == REPTYPE_MIN",
     "line": 1382
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1388
    },
    {
     "code": "mb->partial != 0",
     "line": 1392
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1392
    },
    {
     "code": "mb->partial > 1",
     "line": 1392
    },
    {
     "code": "Lc != cc",
     "line": 1396
    },
    {
     "code": "Loc != cc",
     "line": 1396
    },
    {
     "code": "i < Lmax",
     "line": 1405
    },
    {
     "code": "mb->partial != 0",
     "line": 1410
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1410
    },
    {
     "code": "mb->partial > 1",
     "line": 1410
    },
    {
     "code": "Lc != cc",
     "line": 1414
    },
    {
     "code": "Loc != cc",
     "line": 1414
    },
    {
     "code": "reptype != REPTYPE_POS",
     "line": 1417
    },
    {
     "code": "Feptr == Lstart_eptr",
     "line": 1419
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1422
    },
    {
     "code": "mb->partial != 0",
     "line": 1435
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1435
    },
    {
     "code": "mb->partial > 1",
     "line": 1435
    },
    {
     "code": "Lc != UCHAR21INCTEST(Feptr)",
     "line": 1438
    },
    {
     "code": "Lmin == Lmax",
     "line": 1441
    },
    {
     "code": "reptype == REPTYPE_MIN",
     "line": 1443
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1448
    },
    {
     "code": "mb->partial != 0",
     "line": 1452
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1452
    },
    {
     "code": "mb->partial > 1",
     "line": 1452
    },
    {
     "code": "Lc != UCHAR21INCTEST(Feptr)",
     "line": 1455
    },
    {
     "code": "i < Lmax",
     "line": 1462
    },
    {
     "code": "mb->partial != 0",
     "line": 1466
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1466
    },
    {
     "code": "mb->partial > 1",
     "line": 1466
    },
    {
     "code": "Lc != UCHAR21TEST(Feptr)",
     "line": 1470
    },
    {
     "code": "reptype != REPTYPE_POS",
     "line": 1474
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1479
    },
    {
     "code": "mb->partial != 0",
     "line": 1626
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1626
    },
    {
     "code": "mb->partial > 1",
     "line": 1626
    },
    {
     "code": "Lc == *Feptr",
     "line": 1629
    },
    {
     "code": "Loc == *Feptr",
     "line": 1629
    },
    {
     "code": "Lmin == Lmax",
     "line": 1634
    },
    {
     "code": "reptype == REPTYPE_MIN",
     "line": 1636
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1664
    },
    {
     "code": "mb->partial != 0",
     "line": 1668
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1668
    },
    {
     "code": "mb->partial > 1",
     "line": 1668
    },
    {
     "code": "Lc == *Feptr",
     "line": 1671
    },
    {
     "code": "Loc == *Feptr",
     "line": 1671
    },
    {
     "code": "i < Lmax",
     "line": 1719
    },
    {
     "code": "mb->partial != 0",
     "line": 1723
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1723
    },
    {
     "code": "mb->partial > 1",
     "line": 1723
    },
    {
     "code": "Lc == *Feptr",
     "line": 1726
    },
    {
     "code": "Loc == *Feptr",
     "line": 1726
    },
    {
     "code": "reptype != REPTYPE_POS",
     "line": 1729
    },
    {
     "code": "Feptr == Lstart_eptr",
     "line": 1731
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1733
    },
    {
     "code": "mb->partial != 0",
     "line": 1767
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1767
    },
    {
     "code": "mb->partial > 1",
     "line": 1767
    },
    {
     "code": "Lc == *Feptr++",
     "line": 1770
    },
    {
     "code": "Lmin == Lmax",
     "line": 1774
    },
    {
     "code": "reptype == REPTYPE_MIN",
     "line": 1776
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1803
    },
    {
     "code": "mb->partial != 0",
     "line": 1807
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1807
    },
    {
     "code": "mb->partial > 1",
     "line": 1807
    },
    {
     "code": "Lc == *Feptr++",
     "line": 1810
    },
    {
     "code": "i < Lmax",
     "line": 1856
    },
    {
     "code": "mb->partial != 0",
     "line": 1860
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1860
    },
    {
     "code": "mb->partial > 1",
     "line": 1860
    },
    {
     "code": "Lc == *Feptr",
     "line": 1863
    },
    {
     "code": "reptype != REPTYPE_POS",
     "line": 1866
    },
    {
     "code": "Feptr == Lstart_eptr",
     "line": 1868
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 1870
    },
    {
     "code": "Lmax == 0",
     "line": 1930
    },
    {
     "code": "mb->partial != 0",
     "line": 1969
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 1969
    },
    {
     "code": "mb->partial > 1",
     "line": 1969
    },
    {
     "code": "fc > 255",
     "line": 1974
    },
    {
     "code": "Fop == OP_CLASS",
     "line": 1976
    },
    {
     "code": "(Lbyte_map[fc/8] & (1u << (fc&7))) == 0",
     "line": 1980
    },
    {
     "code": "Lmin == Lmax",
     "line": 1986
    },
    {
     "code": "reptype == REPTYPE_MIN",
     "line": 1991
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 2022
    },
    {
     "code": "mb->partial != 0",
     "line": 2026
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2026
    },
    {
     "code": "mb->partial > 1",
     "line": 2026
    },
    {
     "code": "fc > 255",
     "line": 2031
    },
    {
     "code": "Fop == OP_CLASS",
     "line": 2033
    },
    {
     "code": "(Lbyte_map[fc/8] & (1u << (fc&7))) == 0",
     "line": 2037
    },
    {
     "code": "i < Lmax",
     "line": 2088
    },
    {
     "code": "mb->partial != 0",
     "line": 2092
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2092
    },
    {
     "code": "mb->partial > 1",
     "line": 2092
    },
    {
     "code": "fc > 255",
     "line": 2097
    },
    {
     "code": "Fop == OP_CLASS",
     "line": 2099
    },
    {
     "code": "(Lbyte_map[fc/8] & (1u << (fc&7))) == 0",
     "line": 2103
    },
    {
     "code": "reptype == REPTYPE_POS",
     "line": 2107
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 2112
    },
    {
     "code": "mb->partial != 0",
     "line": 2274
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2274
    },
    {
     "code": "mb->partial > 1",
     "line": 2274
    },
    {
     "code": "(mb->ctypes[fc] & ctype_digit) != 0",
     "line": 2278
    },
    {
     "code": "mb->partial != 0",
     "line": 2286
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2286
    },
    {
     "code": "mb->partial > 1",
     "line": 2286
    },
    {
     "code": "(mb->ctypes[fc] & ctype_digit) == 0",
     "line": 2290
    },
    {
     "code": "mb->partial != 0",
     "line": 2298
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2298
    },
    {
     "code": "mb->partial > 1",
     "line": 2298
    },
    {
     "code": "(mb->ctypes[fc] & ctype_space) != 0",
     "line": 2302
    },
    {
     "code": "mb->partial != 0",
     "line": 2310
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2310
    },
    {
     "code": "mb->partial > 1",
     "line": 2310
    },
    {
     "code": "(mb->ctypes[fc] & ctype_space) == 0",
     "line": 2314
    },
    {
     "code": "mb->partial != 0",
     "line": 2322
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2322
    },
    {
     "code": "mb->partial > 1",
     "line": 2322
    },
    {
     "code": "(mb->ctypes[fc] & ctype_word) != 0",
     "line": 2326
    },
    {
     "code": "mb->partial != 0",
     "line": 2334
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2334
    },
    {
     "code": "mb->partial > 1",
     "line": 2334
    },
    {
     "code": "(mb->ctypes[fc] & ctype_word) == 0",
     "line": 2338
    },
    {
     "code": "mb->partial != 0",
     "line": 2346
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2346
    },
    {
     "code": "mb->partial > 1",
     "line": 2346
    },
    {
     "code": "mb->partial != 0",
     "line": 2357
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2357
    },
    {
     "code": "mb->partial > 1",
     "line": 2357
    },
    {
     "code": "UCHAR21TEST(Feptr) == CHAR_LF",
     "line": 2359
    },
    {
     "code": "mb->bsr_convention == PCRE2_BSR_ANYCRLF",
     "line": 2372
    },
    {
     "code": "mb->partial != 0",
     "line": 2381
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2381
    },
    {
     "code": "mb->partial > 1",
     "line": 2381
    },
    {
     "code": "mb->partial != 0",
     "line": 2396
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2396
    },
    {
     "code": "mb->partial > 1",
     "line": 2396
    },
    {
     "code": "mb->partial != 0",
     "line": 2411
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2411
    },
    {
     "code": "mb->partial > 1",
     "line": 2411
    },
    {
     "code": "mb->partial != 0",
     "line": 2426
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 2426
    },
    {
     "code": "mb->partial > 1",
     "line": 2426
    },
    {
     "code": "*Fecode == OP_TYPEMINUPTO",
     "line": 2614
    },
    {
     "code": "Lmin > 0",
     "line": 2677
    },
    {
     "code": "mb->partial != 0",
     "line": 3209
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3209
    },
    {
     "code": "mb->partial > 1",
     "line": 3209
    },
    {
     "code": "mb->nltype != 0",
     "line": 3212
    },
    {
     "code": "(F->eptr) < mb->end_subject",
     "line": 3212
    },
    {
     "code": "UCHAR21TEST(F->eptr) == mb->nl[0]",
     "line": 3212
    },
    {
     "code": "mb->nllen == 1",
     "line": 3212
    },
    {
     "code": "UCHAR21TEST(F->eptr + 1) == mb->nl[1]",
     "line": 3212
    },
    {
     "code": "mb->partial != 0",
     "line": 3213
    },
    {
     "code": "NLBLOCK->nltype == NLTYPE_FIXED",
     "line": 3215
    },
    {
     "code": "NLBLOCK->nllen == 2",
     "line": 3216
    },
    {
     "code": "*Feptr == NLBLOCK->nl[0]",
     "line": 3217
    },
    {
     "code": "mb->partial > 1",
     "line": 3220
    },
    {
     "code": "Feptr > mb->end_subject - Lmin",
     "line": 3227
    },
    {
     "code": "mb->partial != 0",
     "line": 3229
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3229
    },
    {
     "code": "mb->partial > 1",
     "line": 3229
    },
    {
     "code": "mb->partial != 0",
     "line": 3253
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3253
    },
    {
     "code": "mb->partial > 1",
     "line": 3253
    },
    {
     "code": "Feptr < mb->end_subject",
     "line": 3261
    },
    {
     "code": "*Feptr == CHAR_LF",
     "line": 3261
    },
    {
     "code": "mb->bsr_convention == PCRE2_BSR_ANYCRLF",
     "line": 3274
    },
    {
     "code": "mb->partial != 0",
     "line": 3285
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3285
    },
    {
     "code": "mb->partial > 1",
     "line": 3285
    },
    {
     "code": "mb->partial != 0",
     "line": 3305
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3305
    },
    {
     "code": "mb->partial > 1",
     "line": 3305
    },
    {
     "code": "mb->partial != 0",
     "line": 3325
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3325
    },
    {
     "code": "mb->partial > 1",
     "line": 3325
    },
    {
     "code": "mb->partial != 0",
     "line": 3345
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3345
    },
    {
     "code": "mb->partial > 1",
     "line": 3345
    },
    {
     "code": "mb->partial != 0",
     "line": 3365
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3365
    },
    {
     "code": "mb->partial > 1",
     "line": 3365
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_digit) != 0",
     "line": 3368
    },
    {
     "code": "mb->partial != 0",
     "line": 3379
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3379
    },
    {
     "code": "mb->partial > 1",
     "line": 3379
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_digit) == 0",
     "line": 3382
    },
    {
     "code": "mb->partial != 0",
     "line": 3393
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3393
    },
    {
     "code": "mb->partial > 1",
     "line": 3393
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_space) != 0",
     "line": 3396
    },
    {
     "code": "mb->partial != 0",
     "line": 3407
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3407
    },
    {
     "code": "mb->partial > 1",
     "line": 3407
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_space) == 0",
     "line": 3410
    },
    {
     "code": "mb->partial != 0",
     "line": 3421
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3421
    },
    {
     "code": "mb->partial > 1",
     "line": 3421
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_word) != 0",
     "line": 3424
    },
    {
     "code": "mb->partial != 0",
     "line": 3435
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3435
    },
    {
     "code": "mb->partial > 1",
     "line": 3435
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_word) == 0",
     "line": 3438
    },
    {
     "code": "Lmin == Lmax",
     "line": 3451
    },
    {
     "code": "reptype == REPTYPE_MIN",
     "line": 3458
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 3903
    },
    {
     "code": "mb->partial != 0",
     "line": 3907
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 3907
    },
    {
     "code": "mb->partial > 1",
     "line": 3907
    },
    {
     "code": "Lctype == OP_ANY",
     "line": 3910
    },
    {
     "code": "mb->nltype != 0",
     "line": 3910
    },
    {
     "code": "(F->eptr) < mb->end_subject",
     "line": 3910
    },
    {
     "code": "UCHAR21TEST(F->eptr) == mb->nl[0]",
     "line": 3910
    },
    {
     "code": "mb->nllen == 1",
     "line": 3910
    },
    {
     "code": "UCHAR21TEST(F->eptr + 1) == mb->nl[1]",
     "line": 3910
    },
    {
     "code": "mb->partial != 0",
     "line": 3916
    },
    {
     "code": "NLBLOCK->nltype == NLTYPE_FIXED",
     "line": 3918
    },
    {
     "code": "NLBLOCK->nllen == 2",
     "line": 3919
    },
    {
     "code": "fc == NLBLOCK->nl[0]",
     "line": 3920
    },
    {
     "code": "mb->partial > 1",
     "line": 3923
    },
    {
     "code": "Feptr < mb->end_subject",
     "line": 3937
    },
    {
     "code": "*Feptr == CHAR_LF",
     "line": 3937
    },
    {
     "code": "mb->bsr_convention == PCRE2_BSR_ANYCRLF",
     "line": 3950
    },
    {
     "code": "(mb->ctypes[fc] & ctype_digit) != 0",
     "line": 4005
    },
    {
     "code": "(mb->ctypes[fc] & ctype_digit) == 0",
     "line": 4010
    },
    {
     "code": "(mb->ctypes[fc] & ctype_space) != 0",
     "line": 4015
    },
    {
     "code": "(mb->ctypes[fc] & ctype_space) == 0",
     "line": 4020
    },
    {
     "code": "(mb->ctypes[fc] & ctype_word) != 0",
     "line": 4025
    },
    {
     "code": "(mb->ctypes[fc] & ctype_word) == 0",
     "line": 4030
    },
    {
     "code": "i < Lmax",
     "line": 4651
    },
    {
     "code": "mb->partial != 0",
     "line": 4655
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4655
    },
    {
     "code": "mb->partial > 1",
     "line": 4655
    },
    {
     "code": "mb->nltype != 0",
     "line": 4658
    },
    {
     "code": "(F->eptr) < mb->end_subject",
     "line": 4658
    },
    {
     "code": "UCHAR21TEST(F->eptr) == mb->nl[0]",
     "line": 4658
    },
    {
     "code": "mb->nllen == 1",
     "line": 4658
    },
    {
     "code": "UCHAR21TEST(F->eptr + 1) == mb->nl[1]",
     "line": 4658
    },
    {
     "code": "mb->partial != 0",
     "line": 4659
    },
    {
     "code": "NLBLOCK->nltype == NLTYPE_FIXED",
     "line": 4661
    },
    {
     "code": "NLBLOCK->nllen == 2",
     "line": 4662
    },
    {
     "code": "*Feptr == NLBLOCK->nl[0]",
     "line": 4663
    },
    {
     "code": "mb->partial > 1",
     "line": 4666
    },
    {
     "code": "fc > (uint32_t)(mb->end_subject - Feptr)",
     "line": 4675
    },
    {
     "code": "mb->partial != 0",
     "line": 4678
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4678
    },
    {
     "code": "mb->partial > 1",
     "line": 4678
    },
    {
     "code": "i < Lmax",
     "line": 4684
    },
    {
     "code": "mb->partial != 0",
     "line": 4688
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4688
    },
    {
     "code": "mb->partial > 1",
     "line": 4688
    },
    {
     "code": "fc == CHAR_CR",
     "line": 4692
    },
    {
     "code": "*Feptr == CHAR_LF",
     "line": 4695
    },
    {
     "code": "fc != CHAR_LF",
     "line": 4699
    },
    {
     "code": "mb->bsr_convention == PCRE2_BSR_ANYCRLF",
     "line": 4699
    },
    {
     "code": "fc != CHAR_VT",
     "line": 4700
    },
    {
     "code": "fc != CHAR_FF",
     "line": 4700
    },
    {
     "code": "fc != CHAR_NEL",
     "line": 4700
    },
    {
     "code": "fc != 0x2028",
     "line": 4702
    },
    {
     "code": "fc != 0x2029",
     "line": 4702
    },
    {
     "code": "i < Lmax",
     "line": 4711
    },
    {
     "code": "mb->partial != 0",
     "line": 4715
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4715
    },
    {
     "code": "mb->partial > 1",
     "line": 4715
    },
    {
     "code": "i < Lmax",
     "line": 4732
    },
    {
     "code": "mb->partial != 0",
     "line": 4736
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4736
    },
    {
     "code": "mb->partial > 1",
     "line": 4736
    },
    {
     "code": "i < Lmax",
     "line": 4753
    },
    {
     "code": "mb->partial != 0",
     "line": 4757
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4757
    },
    {
     "code": "mb->partial > 1",
     "line": 4757
    },
    {
     "code": "i < Lmax",
     "line": 4774
    },
    {
     "code": "mb->partial != 0",
     "line": 4778
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4778
    },
    {
     "code": "mb->partial > 1",
     "line": 4778
    },
    {
     "code": "i < Lmax",
     "line": 4795
    },
    {
     "code": "mb->partial != 0",
     "line": 4799
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4799
    },
    {
     "code": "mb->partial > 1",
     "line": 4799
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_digit) != 0",
     "line": 4802
    },
    {
     "code": "i < Lmax",
     "line": 4809
    },
    {
     "code": "mb->partial != 0",
     "line": 4813
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4813
    },
    {
     "code": "mb->partial > 1",
     "line": 4813
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_digit) == 0",
     "line": 4816
    },
    {
     "code": "i < Lmax",
     "line": 4823
    },
    {
     "code": "mb->partial != 0",
     "line": 4827
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4827
    },
    {
     "code": "mb->partial > 1",
     "line": 4827
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_space) != 0",
     "line": 4830
    },
    {
     "code": "i < Lmax",
     "line": 4837
    },
    {
     "code": "mb->partial != 0",
     "line": 4841
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4841
    },
    {
     "code": "mb->partial > 1",
     "line": 4841
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_space) == 0",
     "line": 4844
    },
    {
     "code": "i < Lmax",
     "line": 4851
    },
    {
     "code": "mb->partial != 0",
     "line": 4855
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4855
    },
    {
     "code": "mb->partial > 1",
     "line": 4855
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_word) != 0",
     "line": 4858
    },
    {
     "code": "i < Lmax",
     "line": 4865
    },
    {
     "code": "mb->partial != 0",
     "line": 4869
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4869
    },
    {
     "code": "mb->partial > 1",
     "line": 4869
    },
    {
     "code": "(mb->ctypes[*Feptr] & ctype_word) == 0",
     "line": 4872
    },
    {
     "code": "reptype == REPTYPE_POS",
     "line": 4882
    },
    {
     "code": "Feptr == Lstart_eptr",
     "line": 4886
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 4888
    },
    {
     "code": "Lctype == OP_ANYNL",
     "line": 4890
    },
    {
     "code": "Feptr > Lstart_eptr",
     "line": 4890
    },
    {
     "code": "*Feptr == CHAR_LF",
     "line": 4890
    },
    {
     "code": "Feptr[-1] == CHAR_CR",
     "line": 4891
    },
    {
     "code": "Fop == OP_DNREFI",
     "line": 4920
    },
    {
     "code": "count-- > 0",
     "line": 4926
    },
    {
     "code": "Loffset < Foffset_top",
     "line": 4929
    },
    {
     "code": "Fovector[Loffset] != PCRE2_UNSET",
     "line": 4929
    },
    {
     "code": "Fop == OP_REFI",
     "line": 4937
    },
    {
     "code": "Lmax == 0",
     "line": 4965
    },
    {
     "code": "rrc != 0",
     "line": 4972
    },
    {
     "code": "rrc > 0",
     "line": 4974
    },
    {
     "code": "mb->partial != 0",
     "line": 4975
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 4975
    },
    {
     "code": "mb->partial > 1",
     "line": 4975
    },
    {
     "code": "Loffset < Foffset_top",
     "line": 4990
    },
    {
     "code": "Fovector[Loffset] != PCRE2_UNSET",
     "line": 4990
    },
    {
     "code": "Fovector[Loffset] == Fovector[Loffset + 1]",
     "line": 4992
    },
    {
     "code": "Lmin == 0",
     "line": 4996
    },
    {
     "code": "(mb->poptions & PCRE2_MATCH_UNSET_BACKREF) != 0",
     "line": 4996
    },
    {
     "code": "rrc != 0",
     "line": 5006
    },
    {
     "code": "rrc > 0",
     "line": 5008
    },
    {
     "code": "mb->partial != 0",
     "line": 5009
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 5009
    },
    {
     "code": "mb->partial > 1",
     "line": 5009
    },
    {
     "code": "Lmin == Lmax",
     "line": 5017
    },
    {
     "code": "reptype == REPTYPE_MIN",
     "line": 5021
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5027
    },
    {
     "code": "rrc != 0",
     "line": 5030
    },
    {
     "code": "rrc > 0",
     "line": 5032
    },
    {
     "code": "mb->partial != 0",
     "line": 5033
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 5033
    },
    {
     "code": "mb->partial > 1",
     "line": 5033
    },
    {
     "code": "i < Lmax",
     "line": 5050
    },
    {
     "code": "rrc != 0",
     "line": 5054
    },
    {
     "code": "rrc > 0",
     "line": 5059
    },
    {
     "code": "mb->partial != 0",
     "line": 5059
    },
    {
     "code": "mb->end_subject > mb->start_used_ptr",
     "line": 5060
    },
    {
     "code": "mb->partial > 1",
     "line": 5063
    },
    {
     "code": "slength != Flength",
     "line": 5068
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5083
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5097
    },
    {
     "code": "Feptr == Lstart",
     "line": 5098
    },
    {
     "code": "i < Lmax",
     "line": 5101
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5151
    },
    {
     "code": "*Lnext_ecode == OP_ALT",
     "line": 5152
    },
    {
     "code": "*Lnext_ecode == OP_ALT",
     "line": 5158
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5160
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5168
    },
    {
     "code": "*Fecode == OP_CBRAPOS",
     "line": 5187
    },
    {
     "code": "*Fecode == OP_SCBRAPOS",
     "line": 5187
    },
    {
     "code": "rrc == MATCH_KETRPOS",
     "line": 5216
    },
    {
     "code": "Feptr == Lstart_eptr",
     "line": 5219
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5221
    },
    {
     "code": "rrc == MATCH_THEN",
     "line": 5231
    },
    {
     "code": "mb->verb_ecode_ptr < next_ecode",
     "line": 5234
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5235
    },
    {
     "code": "*next_ecode == OP_ALT",
     "line": 5235
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5239
    },
    {
     "code": "*Fecode != OP_ALT",
     "line": 5241
    },
    {
     "code": "Frdepth == 0",
     "line": 5274
    },
    {
     "code": "*Lnext_branch != OP_ALT",
     "line": 5283
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5289
    },
    {
     "code": "rrc == MATCH_THEN",
     "line": 5325
    },
    {
     "code": "mb->verb_ecode_ptr < next_ecode",
     "line": 5328
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5329
    },
    {
     "code": "*next_ecode == OP_ALT",
     "line": 5329
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5332
    },
    {
     "code": "*Fecode != OP_ALT",
     "line": 5334
    },
    {
     "code": "bracode == mb->start_code",
     "line": 5351
    },
    {
     "code": "Fcurrent_recurse != RECURSE_UNSET",
     "line": 5357
    },
    {
     "code": "offset != PCRE2_UNSET",
     "line": 5360
    },
    {
     "code": "N->group_frame_type == (GF_RECURSE ",
     "line": 5364
    },
    {
     "code": "Feptr == P->eptr",
     "line": 5366
    },
    {
     "code": "mb->verb_current_recurse == (Lframe_type ^ GF_RECURSE)",
     "line": 5397
    },
    {
     "code": "rrc == MATCH_THEN",
     "line": 5399
    },
    {
     "code": "mb->verb_ecode_ptr < next_ecode",
     "line": 5399
    },
    {
     "code": "*Lstart_branch == OP_ALT",
     "line": 5400
    },
    {
     "code": "*next_ecode == OP_ALT",
     "line": 5400
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5408
    },
    {
     "code": "*Lstart_branch != OP_ALT",
     "line": 5410
    },
    {
     "code": "rrc == MATCH_ACCEPT",
     "line": 5435
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5444
    },
    {
     "code": "rrc != MATCH_THEN",
     "line": 5444
    },
    {
     "code": "*Fecode != OP_ALT",
     "line": 5446
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5449
    },
    {
     "code": "*Fecode != OP_ALT",
     "line": 5479
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5485
    },
    {
     "code": "rrc > 0",
     "line": 5512
    },
    {
     "code": "rrc < 0",
     "line": 5513
    },
    {
     "code": "Fecode[Flength] != OP_ALT",
     "line": 5535
    },
    {
     "code": "*Fecode == OP_CALLOUT",
     "line": 5542
    },
    {
     "code": "*Fecode == OP_CALLOUT_STR",
     "line": 5542
    },
    {
     "code": "rrc > 0",
     "line": 5545
    },
    {
     "code": "rrc < 0",
     "line": 5546
    },
    {
     "code": "Fcurrent_recurse != RECURSE_UNSET",
     "line": 5561
    },
    {
     "code": "number == RREF_ANY",
     "line": 5564
    },
    {
     "code": "number == Fcurrent_recurse",
     "line": 5564
    },
    {
     "code": "Fcurrent_recurse != RECURSE_UNSET",
     "line": 5569
    },
    {
     "code": "count-- > 0",
     "line": 5573
    },
    {
     "code": "number == Fcurrent_recurse",
     "line": 5576
    },
    {
     "code": "offset < Foffset_top",
     "line": 5585
    },
    {
     "code": "Fovector[offset] != PCRE2_UNSET",
     "line": 5585
    },
    {
     "code": "count-- > 0",
     "line": 5592
    },
    {
     "code": "offset < Foffset_top",
     "line": 5595
    },
    {
     "code": "Fovector[offset] != PCRE2_UNSET",
     "line": 5595
    },
    {
     "code": "*Fecode == OP_ASSERT",
     "line": 5617
    },
    {
     "code": "*Fecode == OP_ASSERTBACK",
     "line": 5617
    },
    {
     "code": "*Lstart_branch == OP_ALT",
     "line": 5647
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5670
    },
    {
     "code": "Fop == OP_SCOND",
     "line": 5687
    },
    {
     "code": "(ptrdiff_t)number > Feptr - mb->start_subject",
     "line": 5726
    },
    {
     "code": "Feptr < mb->start_used_ptr",
     "line": 5732
    },
    {
     "code": "Lmin > available",
     "line": 5780
    },
    {
     "code": "Lmax > available",
     "line": 5781
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5791
    },
    {
     "code": "*Fecode == OP_ALT",
     "line": 5810
    },
    {
     "code": "branch_end == NULL",
     "line": 5826
    },
    {
     "code": "branch_start + GET(branch_start, 1) != branch_end",
     "line": 5828
    },
    {
     "code": "*bracode != OP_BRA",
     "line": 5836
    },
    {
     "code": "*bracode != OP_COND",
     "line": 5836
    },
    {
     "code": "GF_IDMASK(N->group_frame_type) == GF_CONDASSERT",
     "line": 5854
    },
    {
     "code": "branch_start[1 + LINK_SIZE] == OP_VREVERSE",
     "line": 5880
    },
    {
     "code": "Feptr != P->eptr",
     "line": 5880
    },
    {
     "code": "Feptr > mb->last_used_ptr",
     "line": 5885
    },
    {
     "code": "branch_start[1 + LINK_SIZE] == OP_VREVERSE",
     "line": 5894
    },
    {
     "code": "Feptr != P->eptr",
     "line": 5894
    },
    {
     "code": "Feptr > mb->last_used_ptr",
     "line": 5899
    },
    {
     "code": "(P->ecode)[y] != OP_ALT",
     "line": 5913
    },
    {
     "code": "branch_start[1 + LINK_SIZE] == OP_VREVERSE",
     "line": 5923
    },
    {
     "code": "Feptr != P->eptr",
     "line": 5923
    },
    {
     "code": "Fcurrent_recurse == number",
     "line": 5951
    },
    {
     "code": "*Fecode == OP_KETRPOS",
     "line": 5978
    },
    {
     "code": "Fop != OP_KET",
     "line": 5993
    },
    {
     "code": "P == NULL",
     "line": 5993
    },
    {
     "code": "Feptr != P->eptr",
     "line": 5993
    },
    {
     "code": "Fop == OP_KETRMIN",
     "line": 5995
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 5998
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6006
    },
    {
     "code": "Feptr != mb->start_subject",
     "line": 6020
    },
    {
     "code": "(mb->moptions & PCRE2_NOTBOL) != 0",
     "line": 6020
    },
    {
     "code": "Feptr != mb->start_subject",
     "line": 6026
    },
    {
     "code": "(mb->moptions & PCRE2_NOTEOL) != 0",
     "line": 6034
    },
    {
     "code": "(mb->poptions & PCRE2_DOLLAR_ENDONLY) == 0",
     "line": 6035
    },
    {
     "code": "Feptr < mb->end_subject",
     "line": 6041
    },
    {
     "code": "mb->partial != 0",
     "line": 6042
    },
    {
     "code": "mb->partial > 1",
     "line": 6045
    },
    {
     "code": "Feptr < mb->end_subject",
     "line": 6054
    },
    {
     "code": "mb->nltype != 0",
     "line": 6055
    },
    {
     "code": "(F->eptr) < mb->end_subject",
     "line": 6055
    },
    {
     "code": "UCHAR21TEST(F->eptr) == mb->nl[0]",
     "line": 6055
    },
    {
     "code": "mb->nllen == 1",
     "line": 6055
    },
    {
     "code": "UCHAR21TEST(F->eptr + 1) == mb->nl[1]",
     "line": 6055
    },
    {
     "code": "Feptr != mb->end_subject - mb->nllen",
     "line": 6055
    },
    {
     "code": "mb->partial != 0",
     "line": 6057
    },
    {
     "code": "NLBLOCK->nltype == NLTYPE_FIXED",
     "line": 6059
    },
    {
     "code": "NLBLOCK->nllen == 2",
     "line": 6060
    },
    {
     "code": "UCHAR21TEST(Feptr) == NLBLOCK->nl[0]",
     "line": 6061
    },
    {
     "code": "mb->partial > 1",
     "line": 6064
    },
    {
     "code": "mb->partial != 0",
     "line": 6071
    },
    {
     "code": "mb->partial > 1",
     "line": 6074
    },
    {
     "code": "(mb->moptions & PCRE2_NOTBOL) != 0",
     "line": 6087
    },
    {
     "code": "Feptr == mb->start_subject",
     "line": 6087
    },
    {
     "code": "Feptr != mb->start_subject",
     "line": 6089
    },
    {
     "code": "Feptr == mb->end_subject",
     "line": 6090
    },
    {
     "code": "(mb->poptions & PCRE2_ALT_CIRCUMFLEX) == 0",
     "line": 6091
    },
    {
     "code": "mb->nltype != 0",
     "line": 6092
    },
    {
     "code": "(F->eptr) > mb->start_subject",
     "line": 6092
    },
    {
     "code": "UCHAR21TEST(F->eptr - mb->nllen) == mb->nl[0]",
     "line": 6092
    },
    {
     "code": "mb->nllen == 1",
     "line": 6092
    },
    {
     "code": "UCHAR21TEST(F->eptr - mb->nllen + 1) == mb->nl[1]",
     "line": 6092
    },
    {
     "code": "Feptr < mb->end_subject",
     "line": 6101
    },
    {
     "code": "mb->nltype != 0",
     "line": 6103
    },
    {
     "code": "(F->eptr) < mb->end_subject",
     "line": 6103
    },
    {
     "code": "UCHAR21TEST(F->eptr) == mb->nl[0]",
     "line": 6103
    },
    {
     "code": "mb->nllen == 1",
     "line": 6103
    },
    {
     "code": "UCHAR21TEST(F->eptr + 1) == mb->nl[1]",
     "line": 6103
    },
    {
     "code": "mb->partial != 0",
     "line": 6105
    },
    {
     "code": "NLBLOCK->nltype == NLTYPE_FIXED",
     "line": 6107
    },
    {
     "code": "NLBLOCK->nllen == 2",
     "line": 6108
    },
    {
     "code": "UCHAR21TEST(Feptr) == NLBLOCK->nl[0]",
     "line": 6109
    },
    {
     "code": "mb->partial > 1",
     "line": 6112
    },
    {
     "code": "(mb->moptions & PCRE2_NOTEOL) != 0",
     "line": 6119
    },
    {
     "code": "mb->partial != 0",
     "line": 6120
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 6120
    },
    {
     "code": "mb->partial > 1",
     "line": 6120
    },
    {
     "code": "Feptr != mb->start_subject + mb->start_offset",
     "line": 6130
    },
    {
     "code": "Feptr == mb->check_subject",
     "line": 6155
    },
    {
     "code": "lastptr < mb->start_used_ptr",
     "line": 6167
    },
    {
     "code": "(mb->ctypes[fc] & ctype_word) != 0",
     "line": 6179
    },
    {
     "code": "mb->partial != 0",
     "line": 6186
    },
    {
     "code": "F->eptr > mb->start_used_ptr",
     "line": 6186
    },
    {
     "code": "mb->partial > 1",
     "line": 6186
    },
    {
     "code": "nextptr > mb->last_used_ptr",
     "line": 6201
    },
    {
     "code": "(mb->ctypes[fc] & ctype_word) != 0",
     "line": 6213
    },
    {
     "code": "*Fecode++ == OP_WORD_BOUNDARY",
     "line": 6218
    },
    {
     "code": "Fop == OP_UCP_WORD_BOUNDARY",
     "line": 6218
    },
    {
     "code": "cur_is_word == prev_is_word",
     "line": 6219
    },
    {
     "code": "cur_is_word != prev_is_word",
     "line": 6219
    },
    {
     "code": "rrc == MATCH_SKIP_ARG",
     "line": 6239
    },
    {
     "code": "PRIV(strcmp)(Fecode + 2, mb->verb_skip_ptr) == 0",
     "line": 6240
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6256
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6263
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6269
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6276
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6282
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6303
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6319
    },
    {
     "code": "rrc != MATCH_NOMATCH",
     "line": 6327
    },
    {
     "code": "Feptr > mb->last_used_ptr",
     "line": 6358
    },
    {
     "code": "Frdepth == 0",
     "line": 6359
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "OSV-2023-673",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "match"
  }
 },
 {
  "osv_id": "OSV-2023-674",
  "project": "pcre2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "gi",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 9240,
    "type": "uint32_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pcre2_compile_8",
    "file": "/src/pcre2/src/pcre2_compile.c",
    "line": 10404
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 9278,
    "fn": "get_grouplength",
    "code": "gi[1] = groupminlength | gi[1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "get_grouplength",
    "file": "/src/pcre2/src/pcre2_compile.c",
    "line": 9278
   },
   "code": "gi[1] = groupminlength | gi[1]",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "get_grouplength",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "branchminlength < groupminlength",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "pptrptr",
   "group",
   "recurses",
   "cb"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-674.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/pcre2_5f77d022733a.cpg",
   "testcase_size": 261
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
   "loc_size": 1028,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "get_grouplength--get_branchlength--get_grouplength",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*gi = cb->groupinfo + 2 * group",
     "line": 9240
    },
    {
     "code": "gi[1] = groupminlength",
     "line": 9278
    }
   ],
   "entity_decl": {
    "line": 9240,
    "type": "uint32_t*"
   },
   "entity_name_cpg": "gi",
   "func_lines": [
    9236,
    9287
   ],
   "func_params": {
    "names": [
     "pptrptr",
     "minptr",
     "isinline",
     "errcodeptr",
     "lcptr",
     "group",
     "recurses",
     "cb"
    ],
    "types": [
     "uint32_t**",
     "int*",
     "BOOL",
     "int*",
     "int*",
     "int",
     "parsed_recurse_check*",
     "compile_block*"
    ]
   },
   "guards": [
    {
     "code": "group > 0",
     "line": 9250
    },
    {
     "code": "(cb->external_flags & PCRE2_DUPCAPUSED) == 0",
     "line": 9250
    },
    {
     "code": "(groupinfo & GI_NOT_FIXED_LENGTH) != 0",
     "line": 9253
    },
    {
     "code": "(groupinfo & GI_SET_FIXED_LENGTH) != 0",
     "line": 9254
    },
    {
     "code": "branchlength < 0",
     "line": 9268
    },
    {
     "code": "branchlength > grouplength",
     "line": 9269
    },
    {
     "code": "branchminlength < groupminlength",
     "line": 9270
    },
    {
     "code": "**pptrptr == META_KET",
     "line": 9271
    },
    {
     "code": "group > 0",
     "line": 9275
    },
    {
     "code": "group > 0",
     "line": 9285
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "gi[1] = groupminlength",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "gi[1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "gi",
    "groupminlength"
   ],
   "osv_id": "OSV-2023-674",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "get_grouplength"
  }
 },
 {
  "osv_id": "OSV-2023-68",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i4_luma_nnz",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2031,
    "fn": "isvcd_residual_samp_mb_dyadic",
    "code": "i4_luma_nnz = (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_lu | (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask) >> i4 | ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask | ps_inter_lyr_mb_prms->u2_luma_nnz",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "isvcd_residual_samp_mb_dyadic",
    "file": "/src/libavc/decoder/svc/isvcd_residual_resamp.c",
    "line": 2031
   },
   "code": "i4_luma_nnz = (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_lu | (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask) >> i4 | ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask | ps_inter_lyr_mb_prms->u2_luma_nnz",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "isvcd_residual_samp_mb_dyadic",
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
   "ps_ref_mb_mode"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-68.log",
   "cpg": null,
   "testcase_size": 160
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
   "loc_size": 192,
   "loc_offset": 18,
   "loc_kind": "region",
   "dedup_token": "isvcd_residual_samp_mb_dyadic--isvcd_process_residual_resample_mb--isvcd_process_inter_mb_rsd_pred_target_lyr",
   "overshoot_ratio": 0.09375
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "isvcd_residual_samp_mb_dyadic"
  }
 },
 {
  "osv_id": "OSV-2023-722",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "image",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/hdf5/src/H5Ocache.c",
    "line": 764,
    "size": null,
    "type": "void*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 231
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 786,
    "fn": "H5O__cache_chk_serialize",
    "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5O__cache_chk_serialize",
    "file": "/src/hdf5/src/H5Ocache.c",
    "line": 786
   },
   "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
   "access": {
    "dir": "READ",
    "width": 32,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5O__cache_chk_serialize",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "chk_proxy->oh->chunk[chk_proxy->chunkno].size == len",
   "guard_count": 1,
   "control_structures": "IF:769,IF:779,DO:780,DO:780,DO:780,DO:780,GOTO:780"
  },
  "call_chain": [],
  "types": {
   "entity_type": "void*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "image",
   "len",
   "_thing"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-722.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_875fb3e70a0d.cpg",
   "testcase_size": 1808
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
   "loc_size": 8,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "__asan_memcpy--H5O__cache_chk_serialize--H5C__generate_image",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 764,
    "type": "void*"
   },
   "entity_name_cpg": "image",
   "func_lines": [
    763,
    790
   ],
   "func_params": {
    "names": [
     "f",
     "image",
     "len",
     "_thing"
    ],
    "types": [
     "H5F_t*",
     "void*",
     "size_t",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "'_' == __func__[2]",
     "line": 769
    },
    {
     "code": "'_' == __func__[3]",
     "line": 769
    },
    {
     "code": "'_' == __func__[3]",
     "line": 769
    },
    {
     "code": "'_' == __func__[4]",
     "line": 769
    },
    {
     "code": "'_' == __func__[4]",
     "line": 769
    },
    {
     "code": "'_' == __func__[5]",
     "line": 769
    },
    {
     "code": "chk_proxy->cache_info.type == H5AC_OHDR_CHK",
     "line": 774
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno].size == len",
     "line": 776
    },
    {
     "code": "H5O__chunk_serialize(f, chk_proxy->oh, chk_proxy->chunkno) < 0",
     "line": 779
    }
   ],
   "line_call_count": 12,
   "line_calls": [
    {
     "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunkno].image, len)",
     "name": "H5MM_memcpy",
     "nargs": 3
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno].image",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->chunkno",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunkno].image, len)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno].image",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk[chk_proxy->chunkno]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh->chunk",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->oh",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "chk_proxy->chunkno",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "image",
    "chk_proxy",
    "len"
   ],
   "osv_id": "OSV-2023-722",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5O__cache_chk_serialize"
  }
 },
 {
  "osv_id": "OSV-2023-75",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i1_ref_mb_mode",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "iv_aligned_malloc(void*, int, int)",
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "line": 85
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2622,
    "fn": "isvcd_interlyr_motion_mode_pred_dyadic",
    "code": "i1_ref_mb_mode = ps_inter_lyr_mb_prms->i1_mb_mode | ps_inter_lyr_mb_prms->i1_mb_mode",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "isvcd_interlyr_motion_mode_pred_dyadic",
    "file": "/src/libavc/decoder/svc/isvcd_mode_mv_resamp.c",
    "line": 2622
   },
   "code": "i1_ref_mb_mode = ps_inter_lyr_mb_prms->i1_mb_mode | ps_inter_lyr_mb_prms->i1_mb_mode",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "isvcd_interlyr_motion_mode_pred_dyadic",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "i1_ref_mb_mode > SVC_INTER_MB",
   "guard_count": 1
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-75.log",
   "cpg": null,
   "testcase_size": 201
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
   "loc_size": 192,
   "loc_offset": 52,
   "loc_kind": "region",
   "dedup_token": "isvcd_interlyr_motion_mode_pred_dyadic--isvcd_interlyr_motion_mode_pred--isvcd_mv_pred_ref_tfr_nby2_epmb",
   "overshoot_ratio": 0.270833
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "isvcd_interlyr_motion_mode_pred_dyadic"
  }
 },
 {
  "osv_id": "OSV-2023-754",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "chk_udata",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 231
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 178,
    "fn": "H5O__chunk_protect",
    "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5O__chunk_protect",
    "file": "/src/hdf5/src/H5Ochunk.c",
    "line": 178
   },
   "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5O__chunk_protect",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "idx < oh->nchunks | 0 == idx | chk_proxy->oh == oh",
   "guard_count": 5
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "f",
   "oh",
   "idx"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-754.log",
   "cpg": null,
   "testcase_size": 1808
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
   "loc_size": 168,
   "loc_offset": 8,
   "loc_kind": "region",
   "dedup_token": "H5O__chunk_protect--H5O__chunk_delete--H5O__cont_delete",
   "overshoot_ratio": 0.047619
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5O__chunk_protect"
  }
 },
 {
  "osv_id": "OSV-2023-76",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "type_id",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/hdf5/src/H5SM.c",
    "line": 1568,
    "size": null,
    "type": "unsigned"
   }
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
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1578,
    "fn": "H5SM_delete",
    "code": "type_id = sh_mesg->msg_type_id | sh_mesg->msg_type_id",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5SM_delete",
    "file": "/src/hdf5/src/H5SM.c",
    "line": 1578
   },
   "code": "type_id = sh_mesg->msg_type_id | sh_mesg->msg_type_id",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5SM_delete",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:1571,IF:1584,GOTO:1586,IF:1589,GOTO:1590,IF:1596,GOTO:1598,IF:1601,GOTO:1602,IF:1609,IF:1610,GOTO:1612"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "sh_mesg"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-76.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "testcase_size": 1028
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
   "loc_size": 16,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "H5SM_delete--H5O__msg_write_real--H5O_msg_write",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "type_id = sh_mesg->msg_type_id",
     "line": 1578
    }
   ],
   "entity_decl": {
    "line": 1568,
    "type": "unsigned"
   },
   "entity_name_cpg": "type_id",
   "func_lines": [
    1558,
    1632
   ],
   "func_params": {
    "names": [
     "f",
     "open_oh",
     "sh_mesg"
    ],
    "types": [
     "H5F_t*",
     "H5O_t*",
     "H5O_shared_t*"
    ]
   },
   "guards": [
    {
     "code": "'_' != ((const char *)__func__)[2]",
     "line": 1571
    },
    {
     "code": "'_' != ((const char *)__func__)[3]",
     "line": 1571
    },
    {
     "code": "'_' == ((const char *)__func__)[4]",
     "line": 1571
    },
    {
     "code": "((H5F_get_sohm_addr(f))) != UINT64_MAX",
     "line": 1574
    },
    {
     "code": "NULL == (table = (H5SM_master_table_t *)H5AC_protect(f, H5AC_SOHM_TABLE, H5F_SOHM_ADDR(f),",
     "line": 1584
    },
    {
     "code": "(index_num = H5SM__get_index(table, type_id)) < 0",
     "line": 1589
    },
    {
     "code": "H5SM__delete_from_index(f, open_oh, &(table->indexes[index_num]), sh_mesg, &cache_flags, &mesg_size,",
     "line": 1596
    },
    {
     "code": "H5AC_unprotect(f, H5AC_SOHM_TABLE, H5F_SOHM_ADDR(f), table, cache_flags) < 0",
     "line": 1601
    },
    {
     "code": "NULL ==",
     "line": 1610
    },
    {
     "code": "H5O_msg_delete(f, open_oh, type_id, native_mesg) < 0",
     "line": 1614
    },
    {
     "code": "H5AC_unprotect(f, H5AC_SOHM_TABLE, H5F_SOHM_ADDR(f), table, cache_flags) < 0",
     "line": 1620
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "type_id = sh_mesg->msg_type_id",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "sh_mesg->msg_type_id",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "type_id",
    "sh_mesg"
   ],
   "osv_id": "OSV-2023-76",
   "sites": [
    {
     "args": "type_id ;; native_mesg",
     "callee": "H5O_msg_free",
     "code": "H5O_msg_free(type_id, native_mesg)",
     "line": 1625
    },
    {
     "args": "mesg_buf",
     "callee": "H5MM_xfree",
     "code": "H5MM_xfree(mesg_buf)",
     "line": 1629
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5SM_delete"
  }
 },
 {
  "osv_id": "OSV-2023-77",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "H5C__load_cache_image",
    "file": "/src/hdf5/src/H5Cimage.c",
    "line": 645
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1338,
    "fn": "H5C__decode_cache_image_header",
    "code": "HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | memcmp(p, \"MDCI\", (size_t)4) | (size_t)4",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5C__decode_cache_image_header",
    "file": "/src/hdf5/src/H5Cimage.c",
    "line": 1338
   },
   "code": "HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | memcmp(p, \"MDCI\", (size_t)4) | (size_t)4",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5C__decode_cache_image_header",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-77.log",
   "cpg": null,
   "testcase_size": 2565
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "loc_size": 1,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--___interceptor_memcmp--H5C__decode_ca",
   "overshoot_ratio": 0.0
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5C__decode_cache_image_header"
  }
 },
 {
  "osv_id": "OSV-2023-79",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "vers",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/hdf5/src/H5Ofsinfo.c",
    "line": 99,
    "size": null,
    "type": "unsigned"
   }
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
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "H5FL_CALLOC"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 119,
    "fn": "H5O__fsinfo_decode",
    "code": "vers = *p++ | *p++ | p++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5O__fsinfo_decode",
    "file": "/src/hdf5/src/H5Ofsinfo.c",
    "line": 119
   },
   "code": "vers = *p++ | *p++ | p++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5O__fsinfo_decode",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "vers == H5O_FSINFO_VERSION_0 | vers >= 1",
   "guard_count": 2,
   "control_structures": "IF:103,IF:110,GOTO:111,FOR:113,IF:117,GOTO:118,IF:121,IF:132,GOTO:133,FOR:135,SWITCH:138,IF:143"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "assignment"
  },
  "input_reachability": [
   "p"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-79.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_8562645b8a0b.cpg",
   "testcase_size": 1808
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
   "shadow_byte": "03",
   "shadow_legend_size": 21,
   "loc_size": 75,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "H5O__fsinfo_decode--H5O__msg_iterate_real--H5O__msg_remove_real",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "vers = *p++",
     "line": 119
    }
   ],
   "entity_decl": {
    "line": 99,
    "type": "unsigned"
   },
   "entity_name_cpg": "vers",
   "func_lines": [
    93,
    209
   ],
   "func_params": {
    "names": [
     "f",
     "open_oh",
     "mesg_flags",
     "ioflags",
     "p_size",
     "p"
    ],
    "types": [
     "H5F_t*",
     "H5O_t*",
     "unsigned",
     "unsigned*",
     "size_t",
     "uint8_t*"
    ]
   },
   "guards": [
    {
     "code": "'_' == __func__[2]",
     "line": 103
    },
    {
     "code": "'_' == __func__[3]",
     "line": 103
    },
    {
     "code": "'_' == __func__[3]",
     "line": 103
    },
    {
     "code": "'_' == __func__[4]",
     "line": 103
    },
    {
     "code": "'_' == __func__[4]",
     "line": 103
    },
    {
     "code": "'_' == __func__[5]",
     "line": 103
    },
    {
     "code": "NULL == (fsinfo = H5FL_CALLOC(H5O_fsinfo_t))",
     "line": 110
    },
    {
     "code": "ptype < H5F_MEM_PAGE_NTYPES",
     "line": 113
    },
    {
     "code": "p + 1 - 1 > p_end",
     "line": 117
    },
    {
     "code": "vers == H5O_FSINFO_VERSION_0",
     "line": 121
    },
    {
     "code": "p + 1 + H5F_SIZEOF_SIZE(f) - 1 > p_end",
     "line": 132
    },
    {
     "code": "_i < (H5F_sizeof_size(f))",
     "line": 135
    },
    {
     "code": "HADDR_UNDEF == (fsinfo->eoa_pre_fsm_fsalloc = H5F_get_eoa(f, H5FD_MEM_DEFAULT))",
     "line": 143
    },
    {
     "code": "type < H5FD_MEM_NTYPES",
     "line": 145
    },
    {
     "code": "p + H5_SIZEOF_HADDR_T > p_end",
     "line": 146
    },
    {
     "code": "p + 1 + 1 + 2 * H5F_SIZEOF_SIZE(f) + 2 + H5F_SIZEOF_ADDR(f) - 1 > p_end",
     "line": 180
    },
    {
     "code": "_i < (H5F_sizeof_size(f))",
     "line": 184
    },
    {
     "code": "_i < (H5F_sizeof_size(f))",
     "line": 186
    },
    {
     "code": "ptype < H5F_MEM_PAGE_NTYPES",
     "line": 193
    },
    {
     "code": "p + H5F_SIZEOF_SIZE(f) - 1 > p_end",
     "line": 194
    },
    {
     "code": "ret_value == NULL",
     "line": 205
    },
    {
     "code": "fsinfo != NULL",
     "line": 205
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "vers = *p++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*p++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "p++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "vers",
    "p"
   ],
   "osv_id": "OSV-2023-79",
   "sites": [
    {
     "args": "",
     "callee": "H5FL_CALLOC",
     "code": "H5FL_CALLOC(H5O_fsinfo_t)",
     "line": 110
    },
    {
     "args": "&(H5_H5O_fsinfo_t_reg_free_list)",
     "callee": "H5FL_reg_calloc",
     "code": "H5FL_reg_calloc(&(H5_H5O_fsinfo_t_reg_free_list))",
     "line": 110
    },
    {
     "args": "",
     "callee": "H5F_FREE_SPACE_PERSIST_DEF",
     "code": "H5F_FREE_SPACE_PERSIST_DEF",
     "line": 126
    },
    {
     "args": "",
     "callee": "H5F_FREE_SPACE_THRESHOLD_DEF",
     "code": "H5F_FREE_SPACE_THRESHOLD_DEF",
     "line": 127
    },
    {
     "args": "fsinfo",
     "callee": "H5FL_FREE",
     "code": "H5FL_FREE(H5O_fsinfo_t, fsinfo)",
     "line": 206
    },
    {
     "args": "&(H5_H5O_fsinfo_t_reg_free_list) ;; fsinfo",
     "callee": "H5FL_reg_free",
     "code": "H5FL_reg_free(&(H5_H5O_fsinfo_t_reg_free_list), fsinfo)",
     "line": 206
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5O__fsinfo_decode"
  }
 },
 {
  "osv_id": "OSV-2023-806",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "accum",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 231
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 885,
    "fn": "H5F__accum_free",
    "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5F__accum_free",
    "file": "/src/hdf5/src/H5Faccum.c",
    "line": 885
   },
   "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
   "access": {
    "dir": "READ",
    "width": 361,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5F__accum_free",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "overlap_size < accum->dirty_off | overlap_size < (accum->dirty_off + accum->dirty_len)",
   "guard_count": 2
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "f_sh",
   "addr",
   "size"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-806.log",
   "cpg": null,
   "testcase_size": 1808
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
   "loc_size": 520,
   "loc_offset": 41,
   "loc_kind": "region",
   "dedup_token": "__asan_memmove--H5F__accum_free--H5MF_xfree",
   "overshoot_ratio": 0.078846
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5F__accum_free"
  }
 },
 {
  "osv_id": "OSV-2023-89",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/hdf5/src/H5Omtime.c",
    "line": 225,
    "size": null,
    "type": "uint8_t*"
   }
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
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 238,
    "fn": "H5O__mtime_new_encode",
    "code": "*p++ = H5O_MTIME_VERSION | *p++ | p++ | H5O_MTIME_VERSION",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5O__mtime_new_encode",
    "file": "/src/hdf5/src/H5Omtime.c",
    "line": 238
   },
   "code": "*p++ = H5O_MTIME_VERSION | *p++ | p++ | H5O_MTIME_VERSION",
   "access": {
    "dir": "WRITE",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5O__mtime_new_encode",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:230"
  },
  "call_chain": [],
  "types": {
   "entity_type": "uint8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "p"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-89.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "testcase_size": 2208
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
   "loc_size": 56,
   "loc_offset": 0,
   "loc_kind": "region",
   "dedup_token": "H5O__mtime_new_encode--H5O_msg_flush--H5O__chunk_serialize",
   "overshoot_ratio": 0.0
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 225,
    "type": "uint8_t*"
   },
   "entity_name_cpg": "p",
   "func_lines": [
    224,
    249
   ],
   "func_params": {
    "names": [
     "f",
     "disable_shared",
     "p",
     "_mesg"
    ],
    "types": [
     "H5F_t*",
     "hbool_t",
     "uint8_t*",
     "void*"
    ]
   },
   "guards": [
    {
     "code": "'_' == __func__[2]",
     "line": 230
    },
    {
     "code": "'_' == __func__[3]",
     "line": 230
    },
    {
     "code": "'_' == __func__[3]",
     "line": 230
    },
    {
     "code": "'_' == __func__[4]",
     "line": 230
    },
    {
     "code": "'_' == __func__[4]",
     "line": 230
    },
    {
     "code": "'_' == __func__[5]",
     "line": 230
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "*p++ = H5O_MTIME_VERSION",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*p++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "p++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "H5O_MTIME_VERSION",
     "name": "H5O_MTIME_VERSION",
     "nargs": 0
    }
   ],
   "line_ids": [
    "p"
   ],
   "osv_id": "OSV-2023-89",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5O__mtime_new_encode"
  }
 },
 {
  "osv_id": "OSV-2023-97",
  "project": "libavc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "i1_slice_id",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 2116,
    "fn": "isvcd_reflayer_construction_dyadic",
    "code": "i1_slice_id = ps_inter_lyr_mb_prms->i1_slice_id | ps_inter_lyr_mb_prms->i1_slice_id",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "isvcd_reflayer_construction_dyadic",
    "file": "/src/libavc/decoder/svc/isvcd_intra_resamp.c",
    "line": 2116
   },
   "code": "i1_slice_id = ps_inter_lyr_mb_prms->i1_slice_id | ps_inter_lyr_mb_prms->i1_slice_id",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "isvcd_reflayer_construction_dyadic",
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
   "ps_ref_mb_mode_map",
   "u2_mb_x",
   "u2_mb_y"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-97.log",
   "cpg": null,
   "testcase_size": 1041
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
   "dedup_token": "isvcd_reflayer_construction_dyadic--isvcd_intra_resamp_mb_dyadic--isvcd_process_ibl_mb"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "isvcd_reflayer_construction_dyadic"
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