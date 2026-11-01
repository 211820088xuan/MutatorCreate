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
   "fn": "ndlz4_decompress",
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
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 544
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-51.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2022-51",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 544,
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
    "file": "/src/espeak-ng/tests/ssml-fuzzer.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 64
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
   "control_structures": "SWITCH:541,IF:552,GOTO:552,IF:554,GOTO:554,IF:559,GOTO:559,IF:561,GOTO:561,IF:563,GOTO:563,IF:568",
   "fn": "string_decoder_getc_utf_8",
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
   "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "fn": "string_decoder_getc_utf_8",
    "line": 539
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/encoding.c",
    "line": 539,
    "size": null,
    "type": "uint8_t"
   },
   "kind": "struct",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0fa9737a002c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-530.log",
   "testcase_size": 2
  },
  "input_reachability": [
   "decoder"
  ],
  "osv_id": "OSV-2022-530",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "c = *decoder->current++ | *decoder->current++ | decoder->current++ | decoder->current",
    "fn": "string_decoder_getc_utf_8",
    "kind": "unknown",
    "line": 539,
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
   "entity_type": "uint8_t",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "my_malloc",
    "line": 169
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
   "fn": "ndlz4_decompress",
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
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 540
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
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-55.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2022-55",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 540,
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
    "file": "/src/c-blosc2/blosc/schunk.c",
    "fn": "blosc2_schunk_append_buffer",
    "line": 1024
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
   "fn": "_sw32",
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
    "width": 4
   },
   "code": "*(int32_t *)dest_ = a | *(int32_t *)dest_ | (int32_t *)dest_",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "fn": "_sw32",
    "line": 128
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "dest_",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_3c630983297d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-750.log",
   "testcase_size": 2
  },
  "input_reachability": [
   "dest",
   "a"
  ],
  "osv_id": "OSV-2022-750",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "*(int32_t *)dest_ = a | *(int32_t *)dest_ | (int32_t *)dest_",
    "fn": "_sw32",
    "kind": "unknown",
    "line": 128,
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
    "file": "/src/c-blosc2/tests/fuzz/fuzz_compress_chunk.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 40
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
   "fn": "_sw32",
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
    "width": 4
   },
   "code": "memcpy(dest_, &a, sizeof(a)) | &a | sizeof(a)",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "fn": "_sw32",
    "line": 120
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "dest_",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-776.log",
   "testcase_size": 32
  },
  "input_reachability": [
   "dest",
   "a"
  ],
  "osv_id": "OSV-2022-776",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memcpy(dest_, &a, sizeof(a)) | &a | sizeof(a)",
    "fn": "_sw32",
    "kind": "unknown",
    "line": 120,
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
    "line": 186
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
   "fn": "ndlz4_decompress",
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
    "width": 3324313568
   },
   "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
   "site": {
    "file": "/src/c-blosc2/plugins/codecs/ndlz/ndlz4x4.c",
    "fn": "ndlz4_decompress",
    "line": 547
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_425e8a9a59d4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-847.log",
   "testcase_size": 73
  },
  "input_reachability": [
   "input",
   "output"
  ],
  "osv_id": "OSV-2022-847",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "memset(op, 0, blockshape[0] * blockshape[1]) | blockshape[0] * blockshape[1] | blockshape[0] | blockshape[1]",
    "fn": "ndlz4_decompress",
    "kind": "unknown",
    "line": 547,
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
    "fn": "__libcpp_allocate<w_char>",
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
   "fn": "parse_file",
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
   "code": "!parse_num(line, &maxcpdsugs, afflst) | parse_num(line, &maxcpdsugs, afflst) | &maxcpdsugs | this->maxcpdsugs",
   "site": {
    "file": "/src/hunspell/src/hunspell/suggestmgr.cxx",
    "fn": "SuggestMgr::badcharkey_utf(std::__1::vector<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, std::__1::allocator<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>>>&, w_char const*, int, int)",
    "line": 622
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "line",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_74b08bfb8b61.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-864.log",
   "testcase_size": 36
  },
  "input_reachability": [
   "this",
   "affpath",
   "key"
  ],
  "osv_id": "OSV-2022-864",
  "project": "hunspell",
  "sites": [
   {
    "code": "!parse_num(line, &maxcpdsugs, afflst) | parse_num(line, &maxcpdsugs, afflst) | &maxcpdsugs | this->maxcpdsugs",
    "fn": "SuggestMgr::badcharkey_utf(std::__1::vector<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>, std::__1::allocator<std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>>>&, w_char const*, int, int)",
    "kind": "unknown",
    "line": 622,
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
   "fn": "redundant_condition",
   "guard_count": 10,
   "guards": "i < stripl | j < condl | j < (condl - 1)",
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
   "code": "strip[i] == cond[j] | strip[i] | cond[j]",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::redundant_condition(char, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)",
    "line": 4827
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "strip",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_6b4c0259f24f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-868.log",
   "testcase_size": 89
  },
  "input_reachability": [
   "strip",
   "cond"
  ],
  "osv_id": "OSV-2022-868",
  "project": "hunspell",
  "sites": [
   {
    "code": "strip[i] == cond[j] | strip[i] | cond[j]",
    "fn": "AffixMgr::redundant_condition(char, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int)",
    "kind": "unknown",
    "line": 4827,
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
    "file": "/src/hunspell/src/hunspell/hashmgr.cxx",
    "fn": "HashMgr::add_word(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, unsigned short*, int, std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const*, bool, int)",
    "line": 229
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
   "fn": "add",
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
    "width": 7
   },
   "code": "result.append(word + strip.size()) | word + strip.size() | strip.size() | this->strip",
   "site": {
    "file": "/src/hunspell/src/hunspell/affentry.cxx",
    "fn": "PfxEntry::add(char const*, unsigned long)",
    "line": 105
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "result",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_6291cac8fb85.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-899.log",
   "testcase_size": 109
  },
  "input_reachability": [
   "this",
   "word",
   "len"
  ],
  "osv_id": "OSV-2022-899",
  "project": "hunspell",
  "sites": [
   {
    "code": "result.append(word + strip.size()) | word + strip.size() | strip.size() | this->strip",
    "fn": "PfxEntry::add(char const*, unsigned long)",
    "kind": "unknown",
    "line": 105,
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
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>& std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::__assign_no_alias<true>(char const*, unsigned int) (/out/affdicfuzzer+0x33581f)",
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
   "guard_count": 9,
   "guards": "i < cmax | i >= cmax | i > 1",
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
   "code": "r = st[i + rv->blen] | st[i + rv->blen] | i + rv->blen | rv->blen",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "line": 2126
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "r",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_7d1c7d46c7a7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-903.log",
   "testcase_size": 81
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
  "osv_id": "OSV-2022-903",
  "project": "hunspell",
  "sites": [
   {
    "code": "r = st[i + rv->blen] | st[i + rv->blen] | i + rv->blen | rv->blen",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "kind": "unknown",
    "line": 2126,
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
   "call_chain"
  ],
  "context": {
   "fn": "H5FS__sect_link_size",
   "guard_count": 6,
   "guards": "bin < sinfo->nbins | sinfo->bins[bin].bin_list == NULL | NULL == (sinfo->bins[bin].bin_list = H5SL_create(H5SL_TYPE_HSIZE, NULL",
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
   "code": "sinfo->bins[bin].bin_list == NULL | sinfo->bins[bin].bin_list | sinfo->bins[bin] | sinfo->bins",
   "site": {
    "file": "/src/hdf5/src/H5FSsection.c",
    "fn": "H5FS__sect_link_size",
    "line": 973
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "sinfo",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-104.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "sinfo"
  ],
  "osv_id": "OSV-2023-104",
  "project": "hdf5",
  "sites": [
   {
    "code": "sinfo->bins[bin].bin_list == NULL | sinfo->bins[bin].bin_list | sinfo->bins[bin] | sinfo->bins",
    "fn": "H5FS__sect_link_size",
    "kind": "unknown",
    "line": 973,
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
    "line": 231
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
   "control_structures": "IF:2970,FOR:2980,IF:2987,IF:2990,ELSE:2999,IF:2999,IF:3006",
   "fn": "H5F_addr_decode_len",
   "guard_count": 1,
   "guards": "c != 0xff",
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
   "code": "c = *(*pp)++ | *(*pp)++ | (*pp)++ | *pp",
   "site": {
    "file": "/src/hdf5/src/H5Fint.c",
    "fn": "H5F_addr_decode_len",
    "line": 2984
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5Fint.c",
    "line": 2981,
    "size": null,
    "type": "uint8_t"
   },
   "kind": "struct",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_875fb3e70a0d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-1091.log",
   "testcase_size": 6032
  },
  "input_reachability": [
   "addr_len",
   "pp",
   "addr_p"
  ],
  "osv_id": "OSV-2023-1091",
  "project": "hdf5",
  "sites": [
   {
    "code": "c = *(*pp)++ | *(*pp)++ | (*pp)++ | *pp",
    "fn": "H5F_addr_decode_len",
    "kind": "unknown",
    "line": 2984,
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
   "entity_type": "uint8_t",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 85
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
   "fn": "isvcd_nal_byte_swap_emulation",
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
    "width": 4
   },
   "code": "*pu4_out_stream = (UWORD32) temp_out_stream | *pu4_out_stream | (UWORD32) temp_out_stream",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_nal.c",
    "fn": "isvcd_nal_byte_swap_emulation",
    "line": 617
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "pu4_out_stream",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-117.log",
   "testcase_size": 1017591
  },
  "input_reachability": [
   "pu4_out_stream",
   "pu4_out_len",
   "pv_emulation_ctxt"
  ],
  "osv_id": "OSV-2023-117",
  "project": "libavc",
  "sites": [
   {
    "code": "*pu4_out_stream = (UWORD32) temp_out_stream | *pu4_out_stream | (UWORD32) temp_out_stream",
    "fn": "isvcd_nal_byte_swap_emulation",
    "kind": "unknown",
    "line": 617,
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
    "file": "/src/libavc/fuzzer/mvc_dec_fuzzer.cpp",
    "fn": "mvcd_aligned_malloc(void*, int, int)",
    "line": 61
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
   "fn": "ih264d_sev",
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
   "code": "UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5 | UWORD32",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_cavlc.c",
    "fn": "ih264d_sev",
    "line": 139
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "pu4_buf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-1180.log",
   "testcase_size": 368453
  },
  "input_reachability": [
   "pu4_bitstrm_buf"
  ],
  "osv_id": "OSV-2023-1180",
  "project": "libavc",
  "sites": [
   {
    "code": "UWORD32 * | UWORD32 | (u4_bitstream_offset) >> 5 | UWORD32",
    "fn": "ih264d_sev",
    "kind": "unknown",
    "line": 139,
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
    "file": "/src/libavc/fuzzer/svc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 85
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
   "fn": "isvcd_populate_res_prms",
   "guard_count": 0,
   "guards": null,
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
   "code": "ps_tmp_prms->i1_mb_mode = (WORD8) 0xFF | ps_tmp_prms->i1_mb_mode | (WORD8) 0xFF",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_intra_resamp.c",
    "fn": "isvcd_populate_res_prms",
    "line": 4802
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "ps_tmp_prms",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-1205.log",
   "testcase_size": 76
  },
  "input_reachability": [
   "pv_svc_dec"
  ],
  "osv_id": "OSV-2023-1205",
  "project": "libavc",
  "sites": [
   {
    "code": "ps_tmp_prms->i1_mb_mode = (WORD8) 0xFF | ps_tmp_prms->i1_mb_mode | (WORD8) 0xFF",
    "fn": "isvcd_populate_res_prms",
    "kind": "unknown",
    "line": 4802,
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