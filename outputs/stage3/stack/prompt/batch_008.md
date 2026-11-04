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
stack-buffer-overflow

## 该类型的机制背景
stack-BOF 的必要条件链：
- N1 对象是函数内栈数组
- N2 数组声明维度
- N3 访问宽度
- N4 是否 VLA（char buf[n]，n 来自输入）
- N5 数组所在栈帧
- N6 写入形式：memcpy 还是逐字节循环
- N7 栈增长方向 + 覆盖对象
- N8 是否经由 alloca / 变长分配

## 样本（共 5 条，完整 facts + interpretation）

[
 {
  "osv_id": "OSV-2023-1329",
  "project": "jq",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": null,
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 3375,
    "fn": "decNumberCopy",
    "code": "s=src->lsu+1 | src->lsu+1 | src->lsu | s<smsup",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "decNumberCopy",
    "file": "/src/jq/vendor/decNumber/decNumber.c",
    "line": 3375
   },
   "code": "s=src->lsu+1 | src->lsu+1 | src->lsu | s<smsup",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "decNumberCopy",
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
   "report": "artifacts/by_crash_type/stack-buffer-overflow/jq/address/64bd8ba3749fe473b0708f999e088dfa94d37a2c/OSV-2023-1329",
   "cpg": null,
   "testcase_size": 23
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 48,
   "loc_kind": "stack_frame",
   "dedup_token": "decNumberCopy--decNaNs--decCompareOp"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "decNumberCopy"
  }
 },
 {
  "osv_id": "OSV-2023-14",
  "project": "hunspell",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "word",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 1569,
    "type": "std.string&",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1825,
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "code": "word[i - 1] == word[i] | word[i - 1] | i - 1 | word[i]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "line": 1825
   },
   "code": "word[i - 1] == word[i] | word[i - 1] | i - 1 | word[i]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "compound_check",
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
  "input_reachability": [
   "this",
   "word",
   "wordnum"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-14.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_82b92126325d.cpg",
   "testcase_size": 14095
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f3",
   "shadow_legend_size": 21,
   "loc_offset": 56,
   "loc_kind": "stack_frame",
   "dedup_token": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hent"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 1569,
    "type": "std.string&"
   },
   "entity_name_cpg": "word",
   "func_lines": [
    1569,
    2176
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
     "code": "i < word.size()",
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
     "line": 2083
    },
    {
     "code": "i < word.size()",
     "line": 2088
    },
    {
     "code": "scpd == 0",
     "line": 2089
    },
    {
     "code": "scpd != 0",
     "line": 2091
    },
    {
     "code": "i < word.size()",
     "line": 2110
    },
    {
     "code": "word.compare(i, rv->blen, rv->word, rv->blen) == 0",
     "line": 2110
    },
    {
     "code": "strncmp(rv2->word, st.c_str(), i + rv->blen) == 0",
     "line": 2126
    },
    {
     "code": "soldi != 0",
     "line": 2145
    },
    {
     "code": "soldi != 0",
     "line": 2161
    },
    {
     "code": "oldwordnum == 0",
     "line": 2171
    },
    {
     "code": "onlycpdrule++ < 1",
     "line": 2172
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "word[i - 1] == word[i]",
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
     "code": "word[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "word",
    "i"
   ],
   "osv_id": "OSV-2023-14",
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
  "osv_id": "OSV-2023-984",
  "project": "espeak-ng",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "word_length",
   "kind": "struct",
   "storage": "stack",
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/translateword.c",
    "line": 163,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "size_expr_cpg": "2",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 231,
    "fn": "TranslateWord3",
    "code": "word_length = 0",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "TranslateWord3",
    "file": "/src/espeak-ng/src/libespeak-ng/translateword.c",
    "line": 231
   },
   "code": "word_length = 0",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "TranslateWord3",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "word_length == 1 | word_length == 1 | word_length == 1",
   "guard_count": 9,
   "control_structures": "IF:201,IF:219,IF:227,WHILE:232,IF:238,IF:244,IF:247,IF:251,IF:252,ELSE:254,IF:264,ELSE:267"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-984.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_c19350f961d3.cpg",
   "testcase_size": 1204
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 5536,
   "loc_kind": "stack_frame",
   "dedup_token": "TranslateWord3--TranslateWord--CombineFlag"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "word_length = 0",
     "line": 231
    }
   ],
   "entity_decl": {
    "line": 163,
    "type": "int"
   },
   "entity_name_cpg": "word_length",
   "func_lines": [
    158,
    775
   ],
   "func_params": {
    "names": [
     "tr",
     "word_start",
     "wtab",
     "wtab_remaining",
     "word_out",
     "any_stressed_words",
     "current_alphabet",
     "word_phonemes",
     "size_word_phonemes"
    ],
    "types": [
     "Translator*",
     "char*",
     "WORD_TAB*",
     "int",
     "char*",
     "bool*",
     "ALPHABET*",
     "char[]",
     "size_t"
    ]
   },
   "guards": [
    {
     "code": "wtab == NULL",
     "line": 201
    },
    {
     "code": "tr->data_dictlist == NULL",
     "line": 219
    },
    {
     "code": "*word1 == ' '",
     "line": 227
    },
    {
     "code": "*wordx != 0",
     "line": 232
    },
    {
     "code": "*wordx != ' '",
     "line": 232
    },
    {
     "code": "word_length == 1",
     "line": 244
    },
    {
     "code": "AlphabetFromChar(last_char) != AlphabetFromChar(c_temp)",
     "line": 247
    },
    {
     "code": "option_sayas == SAYAS_KEY",
     "line": 251
    },
    {
     "code": "word_length == 1",
     "line": 252
    },
    {
     "code": "wordx[1] == '.'",
     "line": 274
    },
    {
     "code": "word_out != NULL",
     "line": 278
    },
    {
     "code": "found == false",
     "line": 282
    },
    {
     "code": "ix < dictionary_skipwords",
     "line": 286
    },
    {
     "code": "*wordx == ' '",
     "line": 287
    },
    {
     "code": "word_length == 1",
     "line": 295
    },
    {
     "code": "dictionary_skipwords == 0",
     "line": 295
    },
    {
     "code": "phonemes[0] == phonSWITCH",
     "line": 306
    },
    {
     "code": "word_phonemes[0] == phonSWITCH",
     "line": 319
    },
    {
     "code": "(wflags & FLAG_UPPERS) != FLAG_FIRST_UPPER",
     "line": 331
    },
    {
     "code": "(found = TranslateRoman(tr, word1, phonemes, phonemes + sizeof(phonemes), wtab, wtab_remaining)) != 0",
     "line": 337
    },
    {
     "code": "word_length > 1",
     "line": 343
    },
    {
     "code": "word_length < 4",
     "line": 347
    },
    {
     "code": "tr->clause_lower_count > 3",
     "line": 347
    },
    {
     "code": "spell_word > 0",
     "line": 355
    },
    {
     "code": "SpeakIndividualLetters(tr, word1, phonemes, spell_word, current_alphabet, word_phonemes) == NULL",
     "line": 359
    },
    {
     "code": "word_length > 1",
     "line": 360
    },
    {
     "code": "found == false",
     "line": 370
    },
    {
     "code": "length < 3",
     "line": 382
    },
    {
     "code": "length > 0",
     "line": 382
    },
    {
     "code": "word_length > 1",
     "line": 382
    },
    {
     "code": "wordx[0] == '\\''",
     "line": 388
    },
    {
     "code": "posn > 0",
     "line": 391
    },
    {
     "code": "unpron_phonemes[0] == phonSWITCH",
     "line": 396
    },
    {
     "code": "strcmp(&unpron_phonemes[1], ESPEAKNG_DEFAULT_VOICE) == 0",
     "line": 399
    },
    {
     "code": "wordx[length] != ' '",
     "line": 405
    },
    {
     "code": "*wordx != ' '",
     "line": 410
    },
    {
     "code": "unpron_phonemes[0] != 0",
     "line": 411
    },
    {
     "code": "wordx[0] != '\\''",
     "line": 411
    },
    {
     "code": "phonemes[0] == phonSWITCH",
     "line": 419
    },
    {
     "code": "phonemes[0] == 0",
     "line": 425
    },
    {
     "code": "end_phonemes[0] == 0",
     "line": 425
    },
    {
     "code": "word_length == 1",
     "line": 430
    },
    {
     "code": "(wordx = SpeakIndividualLetters(tr, wordx, phonemes, spell_word, current_alphabet, word_phonemes)) == NULL",
     "line": 431
    },
    {
     "code": "loopcount < 50",
     "line": 442
    },
    {
     "code": "(end_type & SUFX_P) == 0",
     "line": 456
    },
    {
     "code": "(prefix_type & SUFX_B) == 0",
     "line": 479
    },
    {
     "code": "ix > 0",
     "line": 480
    },
    {
     "code": "(*wordx & 0xc0) == 0x80",
     "line": 482
    },
    {
     "code": "ix < n_chars",
     "line": 489
    },
    {
     "code": "ix == (n_chars-1)",
     "line": 492
    },
    {
     "code": "dictionary_flags[0] == 0",
     "line": 526
    },
    {
     "code": "found == false",
     "line": 531
    },
    {
     "code": "phonemes[0] == phonSWITCH",
     "line": 534
    },
    {
     "code": "end_type != 0",
     "line": 543
    },
    {
     "code": "prefix_phonemes[0] != 0",
     "line": 555
    },
    {
     "code": "phonemes[0] == phonSWITCH",
     "line": 560
    },
    {
     "code": "dictionary_flags[0] == 0",
     "line": 566
    },
    {
     "code": "found == false",
     "line": 573
    },
    {
     "code": "dictionary_flags2[0] != 0",
     "line": 573
    },
    {
     "code": "found == false",
     "line": 576
    },
    {
     "code": "phonemes[0] == phonSWITCH",
     "line": 578
    },
    {
     "code": "dictionary_flags[0] == 0",
     "line": 585
    },
    {
     "code": "found == false",
     "line": 590
    },
    {
     "code": "end_type != 0",
     "line": 606
    },
    {
     "code": "phonemes[0] == phonSWITCH",
     "line": 617
    },
    {
     "code": "(end_type1 & SUFX_T) == 0",
     "line": 629
    },
    {
     "code": "end_phonemes[0] != 0",
     "line": 647
    },
    {
     "code": "*p != 0",
     "line": 651
    },
    {
     "code": "*p == phonSTRESS_P",
     "line": 652
    },
    {
     "code": "*p == phonSTRESS_P2",
     "line": 652
    },
    {
     "code": "prefix_stress != 0",
     "line": 655
    },
    {
     "code": "*p != 0",
     "line": 663
    },
    {
     "code": "*p == phonSTRESS_P",
     "line": 664
    },
    {
     "code": "ix == 0",
     "line": 665
    },
    {
     "code": "end_phonemes[0] != 0",
     "line": 687
    },
    {
     "code": "dictionary_skipwords < wtab_remaining",
     "line": 709
    },
    {
     "code": "wordx[0] != 0",
     "line": 749
    },
    {
     "code": "tr->expect_verb > 0",
     "line": 750
    },
    {
     "code": "tr->expect_verb_s > 0",
     "line": 753
    },
    {
     "code": "tr->expect_noun > 0",
     "line": 756
    },
    {
     "code": "tr->expect_past > 0",
     "line": 759
    },
    {
     "code": "word_length == 1",
     "line": 763
    },
    {
     "code": "tr->translator_name == L('e', 'n')",
     "line": 763
    },
    {
     "code": "first_char != 'i'",
     "line": 763
    },
    {
     "code": "(dictionary_flags[0] & (FLAG_ALT_TRANS ",
     "line": 769
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "word_length = 0",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "word_length"
   ],
   "osv_id": "OSV-2023-984",
   "sites": [
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "dictionary_flags[2]",
     "line": 168
    },
    {
     "args": "2",
     "callee": "<operator>.alloc",
     "code": "dictionary_flags2[2]",
     "line": 169
    },
    {
     "args": "N_WORD_PHONEMES",
     "callee": "<operator>.alloc",
     "code": "phonemes[N_WORD_PHONEMES]",
     "line": 175
    },
    {
     "args": "N_WORD_PHONEMES",
     "callee": "<operator>.alloc",
     "code": "phonemes2[N_WORD_PHONEMES]",
     "line": 176
    },
    {
     "args": "N_WORD_PHONEMES",
     "callee": "<operator>.alloc",
     "code": "prefix_phonemes[N_WORD_PHONEMES]",
     "line": 177
    },
    {
     "args": "N_WORD_PHONEMES",
     "callee": "<operator>.alloc",
     "code": "unpron_phonemes[N_WORD_PHONEMES]",
     "line": 178
    },
    {
     "args": "N_WORD_PHONEMES",
     "callee": "<operator>.alloc",
     "code": "end_phonemes[N_WORD_PHONEMES]",
     "line": 179
    },
    {
     "args": "N_WORD_PHONEMES",
     "callee": "<operator>.alloc",
     "code": "end_phonemes2[N_WORD_PHONEMES]",
     "line": 180
    },
    {
     "args": "N_WORD_BYTES",
     "callee": "<operator>.alloc",
     "code": "word_copy[N_WORD_BYTES]",
     "line": 181
    },
    {
     "args": "N_WORD_BYTES",
     "callee": "<operator>.alloc",
     "code": "word_copy2[N_WORD_BYTES]",
     "line": 182
    },
    {
     "args": "0x3f + 2",
     "callee": "<operator>.alloc",
     "code": "prefix_chars[0x3f + 2]",
     "line": 184
    },
    {
     "args": "8",
     "callee": "<operator>.alloc",
     "code": "wtab_null[8]",
     "line": 199
    },
    {
     "args": "N_WORD_PHONEMES",
     "callee": "<operator>.alloc",
     "code": "end_phonemes2[N_WORD_PHONEMES]",
     "line": 447
    },
    {
     "args": "12",
     "callee": "<operator>.alloc",
     "code": "prefix_phonemes2[12]",
     "line": 506
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "TranslateWord3"
  }
 },
 {
  "osv_id": "OSV-2024-1261",
  "project": "pcre2",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "ptr",
   "kind": null,
   "storage": "stack",
   "decl": {
    "file": null,
    "line": 1465,
    "type": "PCRE2_SPTR",
    "size": null
   }
  },
  "alloc": {},
  "sites": [
   {
    "kind": "unknown",
    "line": 1638,
    "fn": "_pcre2_compile_class_not_nested_16",
    "code": "ptr = hptr + 1 | hptr + 1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "_pcre2_compile_class_not_nested_16",
    "file": "/src/pcre2/src/pcre2_compile_class.c",
    "line": 1638
   },
   "code": "ptr = hptr + 1 | hptr + 1",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "_pcre2_check_escape",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "ptr >= ptrend | ptr < ptrend | ptr >= ptrend",
   "guard_count": 25
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [
   "ptrptr",
   "ptrend"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-1261.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/pcre2_62b3ceca1787.cpg",
   "testcase_size": 50000
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 18270,
   "loc_kind": "stack_frame",
   "dedup_token": "__asan_memmove--_pcre2_compile_class_not_nested_16--compile_class_operand"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ptr = *ptrptr",
     "line": 1465
    },
    {
     "code": "ptr = p + 2",
     "line": 1532
    },
    {
     "code": "ptr = hptr",
     "line": 1621
    },
    {
     "code": "ptr = hptr + 1",
     "line": 1638
    },
    {
     "code": "ptr = p + 1",
     "line": 1738
    },
    {
     "code": "ptr = p + 1",
     "line": 1771
    },
    {
     "code": "ptr = oldptr",
     "line": 1883
    }
   ],
   "entity_decl": {
    "line": 1465,
    "type": "PCRE2_SPTR"
   },
   "entity_name_cpg": "ptr",
   "func_lines": [
    1457,
    2175
   ],
   "func_params": {
    "names": [
     "ptrptr",
     "ptrend",
     "chptr",
     "errorcodeptr",
     "options",
     "xoptions",
     "bracount",
     "isclass",
     "cb"
    ],
    "types": [
     "PCRE2_SPTR*",
     "PCRE2_SPTR",
     "uint32_t*",
     "int*",
     "uint32_t",
     "uint32_t",
     "uint32_t",
     "BOOL",
     "compile_block*"
    ]
   },
   "guards": [
    {
     "code": "(options & PCRE2_UTF) != 0",
     "line": 1462
    },
    {
     "code": "((options & PCRE2_ALT_BSUX) ",
     "line": 1464
    },
    {
     "code": "c < ESCAPES_FIRST",
     "line": 1485
    },
    {
     "code": "c > ESCAPES_LAST",
     "line": 1485
    },
    {
     "code": "(i = escapes[c - ESCAPES_FIRST]) != 0",
     "line": 1493
    },
    {
     "code": "i > 0",
     "line": 1495
    },
    {
     "code": "c == CHAR_CR",
     "line": 1498
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_ESCAPED_CR_IS_LF) != 0",
     "line": 1498
    },
    {
     "code": "cb != NULL",
     "line": 1504
    },
    {
     "code": "escape == ESC_P",
     "line": 1504
    },
    {
     "code": "escape == ESC_p",
     "line": 1504
    },
    {
     "code": "escape == ESC_X",
     "line": 1504
    },
    {
     "code": "escape == ESC_N",
     "line": 1512
    },
    {
     "code": "ptr < ptrend",
     "line": 1512
    },
    {
     "code": "*ptr == CHAR_LEFT_CURLY_BRACKET",
     "line": 1512
    },
    {
     "code": "p < ptrend",
     "line": 1518
    },
    {
     "code": "*p == CHAR_SPACE",
     "line": 1518
    },
    {
     "code": "*p == CHAR_HT",
     "line": 1518
    },
    {
     "code": "ptrend - p > 1",
     "line": 1527
    },
    {
     "code": "*p == CHAR_U",
     "line": 1527
    },
    {
     "code": "p[1] == CHAR_PLUS",
     "line": 1527
    },
    {
     "code": "cb == NULL",
     "line": 1543
    },
    {
     "code": "*errorcodeptr == 0",
     "line": 1554
    },
    {
     "code": "cb == NULL",
     "line": 1574
    },
    {
     "code": "c < CHAR_0",
     "line": 1576
    },
    {
     "code": "c > CHAR_9",
     "line": 1577
    },
    {
     "code": "c != CHAR_c",
     "line": 1577
    },
    {
     "code": "c != CHAR_o",
     "line": 1577
    },
    {
     "code": "c != CHAR_x",
     "line": 1577
    },
    {
     "code": "c != CHAR_g",
     "line": 1577
    },
    {
     "code": "*ptr == CHAR_LEFT_CURLY_BRACKET",
     "line": 1610
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_ALT_BSUX) != 0",
     "line": 1611
    },
    {
     "code": "hptr < ptrend",
     "line": 1616
    },
    {
     "code": "(xc = XDIGIT(*hptr)) != 0xff",
     "line": 1616
    },
    {
     "code": "(cc & 0xf0000000) != 0",
     "line": 1618
    },
    {
     "code": "hptr == ptr + 1",
     "line": 1628
    },
    {
     "code": "*hptr != CHAR_RIGHT_CURLY_BRACKET",
     "line": 1630
    },
    {
     "code": "ptrend - ptr < 4",
     "line": 1643
    },
    {
     "code": "(cc = XDIGIT(ptr[0])) == 0xff",
     "line": 1644
    },
    {
     "code": "(xc = XDIGIT(ptr[1])) == 0xff",
     "line": 1645
    },
    {
     "code": "(xc = XDIGIT(ptr[2])) == 0xff",
     "line": 1647
    },
    {
     "code": "(xc = XDIGIT(ptr[3])) == 0xff",
     "line": 1649
    },
    {
     "code": "c > 0x10ffffU",
     "line": 1656
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_ALLOW_SURROGATE_ESCAPES) == 0",
     "line": 1659
    },
    {
     "code": "c > MAX_NON_UTF_CHAR",
     "line": 1662
    },
    {
     "code": "cb == NULL",
     "line": 1709
    },
    {
     "code": "*ptr != CHAR_LESS_THAN_SIGN",
     "line": 1713
    },
    {
     "code": "*errorcodeptr == 0",
     "line": 1724
    },
    {
     "code": "*p != CHAR_GREATER_THAN_SIGN",
     "line": 1728
    },
    {
     "code": "*ptr == CHAR_LESS_THAN_SIGN",
     "line": 1743
    },
    {
     "code": "*ptr == CHAR_APOSTROPHE",
     "line": 1743
    },
    {
     "code": "*ptr == CHAR_LEFT_CURLY_BRACKET",
     "line": 1752
    },
    {
     "code": "p < ptrend",
     "line": 1756
    },
    {
     "code": "*p == CHAR_SPACE",
     "line": 1756
    },
    {
     "code": "*p == CHAR_HT",
     "line": 1756
    },
    {
     "code": "*errorcodeptr == 0",
     "line": 1760
    },
    {
     "code": "p < ptrend",
     "line": 1763
    },
    {
     "code": "*p == CHAR_SPACE",
     "line": 1763
    },
    {
     "code": "*p == CHAR_HT",
     "line": 1763
    },
    {
     "code": "*p != CHAR_RIGHT_CURLY_BRACKET",
     "line": 1765
    },
    {
     "code": "*errorcodeptr == 0",
     "line": 1781
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_PYTHON_OCTAL) != 0",
     "line": 1825
    },
    {
     "code": "ptr + 1 < ptrend",
     "line": 1828
    },
    {
     "code": "s < 10",
     "line": 1868
    },
    {
     "code": "(unsigned)s > MAX_GROUP_NUMBER",
     "line": 1874
    },
    {
     "code": "i++ < 2",
     "line": 1903
    },
    {
     "code": "ptr < ptrend",
     "line": 1903
    },
    {
     "code": "c > 0xff",
     "line": 1905
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_PYTHON_OCTAL) != 0",
     "line": 1907
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_NO_BS0) != 0",
     "line": 1916
    },
    {
     "code": "c == 0",
     "line": 1916
    },
    {
     "code": "i == 1",
     "line": 1916
    },
    {
     "code": "*ptr++ != CHAR_LEFT_CURLY_BRACKET",
     "line": 1925
    },
    {
     "code": "ptr < ptrend",
     "line": 1932
    },
    {
     "code": "*ptr == CHAR_SPACE",
     "line": 1932
    },
    {
     "code": "*ptr == CHAR_HT",
     "line": 1932
    },
    {
     "code": "*ptr == CHAR_RIGHT_CURLY_BRACKET",
     "line": 1933
    },
    {
     "code": "ptr < ptrend",
     "line": 1941
    },
    {
     "code": "c == 0",
     "line": 1944
    },
    {
     "code": "cc == CHAR_0",
     "line": 1944
    },
    {
     "code": "ptr < ptrend",
     "line": 1958
    },
    {
     "code": "*ptr == CHAR_SPACE",
     "line": 1958
    },
    {
     "code": "*ptr == CHAR_HT",
     "line": 1958
    },
    {
     "code": "ptr < ptrend",
     "line": 1962
    },
    {
     "code": "ptr < ptrend",
     "line": 1965
    },
    {
     "code": "*ptr++ == CHAR_RIGHT_CURLY_BRACKET",
     "line": 1965
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_ALLOW_SURROGATE_ESCAPES) == 0",
     "line": 1968
    },
    {
     "code": "ptrend - ptr < 2",
     "line": 1988
    },
    {
     "code": "(cc = XDIGIT(ptr[0])) == 0xff",
     "line": 1989
    },
    {
     "code": "(xc = XDIGIT(ptr[1])) == 0xff",
     "line": 1990
    },
    {
     "code": "ptr < ptrend",
     "line": 2004
    },
    {
     "code": "*ptr == CHAR_LEFT_CURLY_BRACKET",
     "line": 2004
    },
    {
     "code": "ptr < ptrend",
     "line": 2007
    },
    {
     "code": "*ptr == CHAR_SPACE",
     "line": 2007
    },
    {
     "code": "*ptr == CHAR_HT",
     "line": 2007
    },
    {
     "code": "*ptr == CHAR_RIGHT_CURLY_BRACKET",
     "line": 2012
    },
    {
     "code": "ptr < ptrend",
     "line": 2020
    },
    {
     "code": "(cc = XDIGIT(*ptr)) != 0xff",
     "line": 2020
    },
    {
     "code": "c == 0",
     "line": 2023
    },
    {
     "code": "cc == 0",
     "line": 2023
    },
    {
     "code": "c > 0x10ffffU",
     "line": 2028
    },
    {
     "code": "c > MAX_NON_UTF_CHAR",
     "line": 2028
    },
    {
     "code": "ptr < ptrend",
     "line": 2037
    },
    {
     "code": "*ptr == CHAR_SPACE",
     "line": 2037
    },
    {
     "code": "*ptr == CHAR_HT",
     "line": 2037
    },
    {
     "code": "ptr < ptrend",
     "line": 2043
    },
    {
     "code": "XDIGIT(*ptr) != 0xff",
     "line": 2043
    },
    {
     "code": "ptr < ptrend",
     "line": 2046
    },
    {
     "code": "*ptr++ == CHAR_RIGHT_CURLY_BRACKET",
     "line": 2046
    },
    {
     "code": "(xoptions & PCRE2_EXTRA_ALLOW_SURROGATE_ESCAPES) == 0",
     "line": 2049
    },
    {
     "code": "(cc = XDIGIT(*ptr)) == 0xff",
     "line": 2077
    },
    {
     "code": "(cc = XDIGIT(*ptr)) == 0xff",
     "line": 2095
    },
    {
     "code": "c < 32",
     "line": 2132
    },
    {
     "code": "c > 126",
     "line": 2132
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "ptr = hptr + 1",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "hptr + 1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ptr",
    "hptr"
   ],
   "osv_id": "OSV-2024-1261",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "_pcre2_compile_class_not_nested_16"
  }
 },
 {
  "osv_id": "OSV-2025-169",
  "project": "espeak-ng",
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "name": "tr",
   "kind": null,
   "storage": "stack",
   "decl": null
  },
  "alloc": null,
  "sites": [
   {
    "kind": "unknown",
    "line": 782,
    "fn": "TranslateRoman",
    "code": "((tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0 | (tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0] | tr->langopts.numbers & NUM_ROMAN_CAPITALS | tr->langopts.numbers",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "TranslateRoman",
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "line": 782
   },
   "code": "((tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0 | (tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0] | tr->langopts.numbers & NUM_ROMAN_CAPITALS | tr->langopts.numbers",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "TranslateRoman",
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
   "tr",
   "word",
   "wtab"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2025-169.log",
   "cpg": null,
   "testcase_size": 2018
  },
  "type_reconciliation": {
   "report_fault_kind": "stack-buffer-overflow",
   "ledger_crash_type": "stack-buffer-overflow",
   "used": "stack-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "f2",
   "shadow_legend_size": 21,
   "loc_offset": 303,
   "loc_kind": "stack_frame",
   "dedup_token": "TranslateRoman--TranslateWord3--TranslateWord"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "TranslateRoman"
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