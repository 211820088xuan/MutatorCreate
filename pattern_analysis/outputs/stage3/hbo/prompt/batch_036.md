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
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
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
   "fn": "initialize_context_decompression",
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
   "code": "",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "initialize_context_decompression",
    "line": 2192
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_886d4c9b7833.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-973.log",
   "testcase_size": 271
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-973",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "",
    "fn": "initialize_context_decompression",
    "kind": "unknown",
    "line": 2192,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
   "fn": "ZSTD_initDDict_internal",
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
    "width": 61951
   },
   "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/decompress/zstd_ddict.c",
    "fn": "ZSTD_initDDict_internal",
    "line": 134
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "internalBuffer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-997.log",
   "testcase_size": 24087
  },
  "input_reachability": [
   "ddict",
   "dict",
   "dictSize"
  ],
  "osv_id": "OSV-2021-997",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "ZSTD_memcpy(internalBuffer, dict, dictSize) | memcpy((internalBuffer), (dict), (dictSize))",
    "fn": "ZSTD_initDDict_internal",
    "kind": "unknown",
    "line": 134,
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
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>& std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::__assign_no_alias<true>(char const*, unsigned int) (/out/affdicfuzzer+0x3353bf)",
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
   "fn": "cpdcase_check",
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
   "code": "p = word + pos - 1 | word + pos - 1 | word + pos | (*p & 0xc0) == 0x80",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::cpdcase_check(char const*, int)",
    "line": 1356
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "p",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_52021df98d3b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1004.log",
   "testcase_size": 1235
  },
  "input_reachability": [
   "word",
   "pos"
  ],
  "osv_id": "OSV-2022-1004",
  "project": "hunspell",
  "sites": [
   {
    "code": "p = word + pos - 1 | word + pos - 1 | word + pos | (*p & 0xc0) == 0x80",
    "fn": "AffixMgr::cpdcase_check(char const*, int)",
    "kind": "unknown",
    "line": 1356,
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
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "fn": "__libcpp_allocate<char>",
    "line": 43
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
   "fn": "compound_check",
   "guard_count": 8,
   "guards": "i < cmax | i >= cmax | i > st.size()",
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
   "code": "i > 2 && word[i - 1] == word[i - 2] | i > 2 | word[i - 1] == word[i - 2] | word[i - 1]",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "line": 1882
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "i",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_96a0c2e82ad9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1028.log",
   "testcase_size": 10971
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
  "osv_id": "OSV-2022-1028",
  "project": "hunspell",
  "sites": [
   {
    "code": "i > 2 && word[i - 1] == word[i - 2] | i > 2 | word[i - 1] == word[i - 2] | word[i - 1]",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "kind": "unknown",
    "line": 1882,
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
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "fn": "__libcpp_allocate<char>",
    "line": 43
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
   "fn": "compound_check",
   "guard_count": 11,
   "guards": "i < cmax | i >= cmax | i > word.size()",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 10
   },
   "code": "numsyllable += get_syllable(word.substr(i)) | get_syllable(word.substr(i)) | word.substr(i)",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "line": 2035
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "numsyllable",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_3f0f43060c96.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1042.log",
   "testcase_size": 3577
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
  "osv_id": "OSV-2022-1042",
  "project": "hunspell",
  "sites": [
   {
    "code": "numsyllable += get_syllable(word.substr(i)) | get_syllable(word.substr(i)) | word.substr(i)",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "kind": "unknown",
    "line": 2035,
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
    "file": "/usr/local/bin/../include/c++/v1/__new/allocate.h",
    "fn": "__libcpp_allocate<char>",
    "line": 43
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
   "fn": "isSubset",
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
   "code": "((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') && (*s2  | ((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') | (*s1 == *s2) || (*s1 == '.') | *s1 == *s2",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "isSubset",
    "line": 1070
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "s1",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_5f57c6c24719.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1054.log",
   "testcase_size": 2729
  },
  "input_reachability": [
   "s1",
   "s2"
  ],
  "osv_id": "OSV-2022-1054",
  "project": "hunspell",
  "sites": [
   {
    "code": "((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') && (*s2  | ((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') | (*s1 == *s2) || (*s1 == '.') | *s1 == *s2",
    "fn": "isSubset",
    "kind": "unknown",
    "line": 1070,
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
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::replace(unsigned long, unsigned long, char const*, unsigned long) (/out/affdicfuzzer+0x358cf1)",
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
   "fn": "compound_check",
   "guard_count": 12,
   "guards": "i < cmax | i >= cmax | i > word.size()",
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
   "code": "(st[i] & 0xc0) == 0x80 | st[i] & 0xc0 | st[i] | i++",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "line": 1611
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "st",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_631800650ab3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1061.log",
   "testcase_size": 2908
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
  "osv_id": "OSV-2022-1061",
  "project": "hunspell",
  "sites": [
   {
    "code": "(st[i] & 0xc0) == 0x80 | st[i] & 0xc0 | st[i] | i++",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "kind": "unknown",
    "line": 1611,
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
    "file": "/src/libredwg/src/./dwg.spec",
    "fn": "dwg_setup_LAYOUT",
    "line": 5069
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
   "fn": "json_common_entity_data",
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
    "file": "/src/libredwg/src/common_entity_handle_data.spec",
    "fn": "json_common_entity_data",
    "line": 50
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/4cf4cbdd28158f9a858f76525ab155fb1daf10fa/OSV-2022-1180",
   "testcase_size": 16316
  },
  "input_reachability": [],
  "osv_id": "OSV-2022-1180",
  "project": "libredwg",
  "sites": [
   {
    "code": null,
    "fn": "json_common_entity_data",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
   "fn": "bit_calc_CRC",
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
    "file": "/src/libredwg/src/bits.c",
    "fn": "bit_calc_CRC",
    "line": 3280
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/97fd500ac19eb64c1218c41ef7582fcd41f98895/OSV-2022-1211",
   "testcase_size": 1025
  },
  "input_reachability": [],
  "osv_id": "OSV-2022-1211",
  "project": "libredwg",
  "sites": [
   {
    "code": null,
    "fn": "bit_calc_CRC",
    "kind": "unknown",
    "line": 3280,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
   "fn": "bit_read_BB",
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
    "file": "/src/libredwg/src/bits.c",
    "fn": "bit_read_BB",
    "line": 198
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
   "report": "artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/f5eb830532f3a34821132c85f019593a9f51fa3c/OSV-2022-1252",
   "testcase_size": 205
  },
  "input_reachability": [],
  "osv_id": "OSV-2022-1252",
  "project": "libredwg",
  "sites": [
   {
    "code": null,
    "fn": "bit_read_BB",
    "kind": "unknown",
    "line": 198,
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
    "file": "/src/md4c/src/md4c.c",
    "fn": "md_push_mark",
    "line": 2532
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
   "control_structures": "WHILE:3436,IF:3448,ELSE:3451,IF:3463,CONTINUE:3468,IF:3474,WHILE:3495,IF:3497,BREAK:3499,IF:3501,BREAK:3502,IF:3507",
   "fn": "md_resolve_links",
   "guard_count": 1,
   "guards": "next_closer != NULL",
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
   "code": "next_closer->ch == ']' | next_closer->ch",
   "site": {
    "file": "/src/md4c/src/md4c.c",
    "fn": "md_resolve_links",
    "line": 3481
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/md4c/src/md4c.c",
    "line": 3442,
    "size": null,
    "type": "MD_MARK*"
   },
   "kind": "pointer",
   "name": "next_closer",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/md4c_62b60979f6a2.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-126.log",
   "testcase_size": 43679
  },
  "input_reachability": [
   "ctx",
   "lines"
  ],
  "osv_id": "OSV-2022-126",
  "project": "md4c",
  "sites": [
   {
    "code": "next_closer->ch == ']' | next_closer->ch",
    "fn": "md_resolve_links",
    "kind": "unknown",
    "line": 3481,
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
   "entity_type": "MD_MARK*",
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
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>& std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::__assign_no_alias<true>(char const*, unsigned long) (/out/affdicfuzzer+0x3599e6)",
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
   "fn": "cpdcase_check",
   "guard_count": 6,
   "guards": "unicodetoupper(a, langnum) == a | unicodetoupper(b, langnum) == b | a != '-'",
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
   "code": "a = word[pos - 1] | word[pos - 1] | pos - 1 | b = word[pos]",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)",
    "line": 1366
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "a",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_379716df74b5.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1260.log",
   "testcase_size": 16367
  },
  "input_reachability": [
   "word",
   "pos"
  ],
  "osv_id": "OSV-2022-1260",
  "project": "hunspell",
  "sites": [
   {
    "code": "a = word[pos - 1] | word[pos - 1] | pos - 1 | b = word[pos]",
    "fn": "AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)",
    "kind": "unknown",
    "line": 1366,
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 173
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
   "fn": "ndlz8_decompress",
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
    "width": 201851904
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz8x8.c",
    "fn": "ndlz8_decompress",
    "line": 462
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "op",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_79b6995ab82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-33.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2022-33",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz8_decompress",
    "kind": "unknown",
    "line": 462,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
   "fn": "bitshuffle16_neon",
   "guard_count": 1,
   "guards": "j < 8",
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
   "code": "vst1_lane_u8(dest + k + j * size * elem_size / (8 * elem | dest + k + j * size * elem_size / (8 * elem_size) + 8 *  | dest + k + j * size * elem_size / (8 * elem_size) | dest + k",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/lz4-1.9.3/lz4.c",
    "fn": "LZ4_wildCopy32",
    "line": 469
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "dest",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5a50726608d0.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-34.log",
   "testcase_size": 270
  },
  "input_reachability": [
   "src",
   "dest",
   "size",
   "elem_size"
  ],
  "osv_id": "OSV-2022-34",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "vst1_lane_u8(dest + k + j * size * elem_size / (8 * elem | dest + k + j * size * elem_size / (8 * elem_size) + 8 *  | dest + k + j * size * elem_size / (8 * elem_size) | dest + k",
    "fn": "LZ4_wildCopy32",
    "kind": "unknown",
    "line": 469,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2a28a) (BuildId: 328820b908de8ea1ef79afa8995e302e819163d7)",
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
   "fn": "md_decode_utf8__",
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
   "code": "!IS_UTF8_LEAD1(str[0]) | IS_UTF8_LEAD1(str[0]) | str[0] | (unsigned char)(str[0]) <= 0x7f",
   "site": {
    "file": "/src/md4c/src/md4c.c",
    "fn": "md_decode_utf8__",
    "line": 817
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "str",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-42.log",
   "testcase_size": 42
  },
  "input_reachability": [
   "str"
  ],
  "osv_id": "OSV-2022-42",
  "project": "md4c",
  "sites": [
   {
    "code": "!IS_UTF8_LEAD1(str[0]) | IS_UTF8_LEAD1(str[0]) | str[0] | (unsigned char)(str[0]) <= 0x7f",
    "fn": "md_decode_utf8__",
    "kind": "unknown",
    "line": 817,
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