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
heap-use-after-free

## 该类型的机制背景
UAF 的必要条件链：
- N1 对象是堆分配
- N2 存在 free(p) 调用
- N3 p 在 free 之后被解引用（执行顺序）
- N4 free 与解引用之间 p 未被重新赋值
- N5 free 与解引用之间 p 未重新 malloc
- N6 free 的实参是 p 本身（非 p+off）
- N7 解引用对象与 free 对象是同一对象（含别名）
- N8 free 与解引用在同一可达路径上
- N9 p 解引用时未被置空
- N10 解引用发生在 free 生效后（非同一语句）

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 53
   },
   "size_bytes": 602112,
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
   "fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 602112,
    "width": 16
   },
   "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)(pu1_src)) | _mm_loadu_si128((__m128i *)(pu1_src)) | (__m128i *)(pu1_src)",
   "site": {
    "file": "/src/libavc/common/x86/ih264_inter_pred_filters_ssse3.c",
    "fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3",
    "line": 3683
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "src_r0_16x8b",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2020-370.log",
   "testcase_size": 122
  },
  "input_reachability": [],
  "osv_id": "OSV-2020-370",
  "project": "libavc",
  "sites": [
   {
    "code": null,
    "fn": "ih264d_free_dynamic_bufs",
    "kind": "free",
    "line": 2265,
    "origin": "report:freed_by"
   },
   {
    "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)(pu1_src)) | _mm_loadu_si128((__m128i *)(pu1_src)) | (__m128i *)(pu1_src)",
    "fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3",
    "kind": "unknown",
    "line": 3683,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/tr_languages.c",
    "fn": "NewTranslator",
    "line": 242
   },
   "size_bytes": 14864,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:703,IF:706,IF:708,IF:714,IF:716,IF:718,IF:721,IF:724,IF:738,IF:744,IF:751,IF:756",
   "fn": "TranslateLetter",
   "guard_count": 1,
   "guards": "translator != tr",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 14864,
    "width": 4
   },
   "code": "ph_buf[len+1] = tr->phoneme_tab_ix | ph_buf[len+1] | len+1 | tr->phoneme_tab_ix",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "fn": "TranslateLetter",
    "line": 839
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "line": 690,
    "size": null,
    "type": "char[80]"
   },
   "kind": "array",
   "name": "ph_buf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_1f76c4b8bd32.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1141.log",
   "testcase_size": 20
  },
  "input_reachability": [
   "tr",
   "current_alphabet"
  ],
  "osv_id": "OSV-2021-1141",
  "project": "espeak-ng",
  "sites": [
   {
    "code": null,
    "fn": "DeleteTranslator",
    "kind": "free",
    "line": 218,
    "origin": "report:freed_by"
   },
   {
    "code": "ph_buf[len+1] = tr->phoneme_tab_ix | ph_buf[len+1] | len+1 | tr->phoneme_tab_ix",
    "fn": "TranslateLetter",
    "kind": "unknown",
    "line": 839,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char[80]",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/tr_languages.c",
    "fn": "NewTranslator",
    "line": 242
   },
   "size_bytes": 14864,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2235,IF:2238,FOR:2241,IF:2244,BREAK:2245,IF:2249,FOR:2253,IF:2256,ELSE:2259,IF:2266,WHILE:2269,IF:2271",
   "fn": "TranslateRules",
   "guard_count": 4,
   "guards": "c == 0 | c != 0 | c != 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 14864,
    "width": 1
   },
   "code": "n = tr->groups2_count[c] | tr->groups2_count[c] | tr->groups2_count",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "fn": "TranslateRules",
    "line": 2274
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "line": 2221,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "n",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_1f76c4b8bd32.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-1157.log",
   "testcase_size": 10
  },
  "input_reachability": [
   "tr",
   "p_start",
   "end_phonemes"
  ],
  "osv_id": "OSV-2021-1157",
  "project": "espeak-ng",
  "sites": [
   {
    "code": null,
    "fn": "DeleteTranslator",
    "kind": "free",
    "line": 218,
    "origin": "report:freed_by"
   },
   {
    "code": "n = tr->groups2_count[c] | tr->groups2_count[c] | tr->groups2_count",
    "fn": "TranslateRules",
    "kind": "unknown",
    "line": 2274,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/common/zstd_common.c",
    "fn": "ZSTD_malloc",
    "line": 60
   },
   "size_bytes": 26720,
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
   "fn": "ZSTD_freeDDict",
   "guard_count": 1,
   "guards": "ddict==NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 26720,
    "width": 24
   },
   "code": "cMem = ddict->cMem | ddict->cMem",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/decompress/zstd_ddict.c",
    "fn": "ZSTD_freeDDict",
    "line": 215
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "cMem",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_0e8bdfce66ba.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-213.log",
   "testcase_size": 36366
  },
  "input_reachability": [
   "ddict"
  ],
  "osv_id": "OSV-2021-213",
  "project": "c-blosc2",
  "sites": [
   {
    "code": null,
    "fn": "ZSTD_free",
    "kind": "free",
    "line": 81,
    "origin": "report:freed_by"
   },
   {
    "code": "cMem = ddict->cMem | ddict->cMem",
    "fn": "ZSTD_freeDDict",
    "kind": "unknown",
    "line": 215,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "frame_to_schunk",
    "line": 1285
   },
   "size_bytes": 148,
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
   "fn": "frame_get_lazychunk",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 148,
    "width": 4
   },
   "code": "free(csize_idx)",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "frame_get_lazychunk",
    "line": 1761
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "csize_idx",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_60b79c4c05ae.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-371.log",
   "testcase_size": 158
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-371",
  "project": "c-blosc2",
  "sites": [
   {
    "code": null,
    "fn": "blosc2_schunk_free",
    "kind": "free",
    "line": 427,
    "origin": "report:freed_by"
   },
   {
    "code": "free(csize_idx)",
    "fn": "frame_get_lazychunk",
    "kind": "free",
    "line": 1761,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp",
    "fn": "malloc",
    "line": 67
   },
   "size_bytes": 148,
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
   "fn": "frame_get_lazychunk",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 148,
    "width": 4
   },
   "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | *chunk + BLOSC2_CHUNK_CBYTES | *chunk",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "frame_get_lazychunk",
    "line": 2021
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "lazychunk_cbytes",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_969fb4cbb617.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-422.log",
   "testcase_size": 148
  },
  "input_reachability": [
   "frame",
   "chunk"
  ],
  "osv_id": "OSV-2021-422",
  "project": "c-blosc2",
  "sites": [
   {
    "code": null,
    "fn": "free",
    "kind": "free",
    "line": 51,
    "origin": "report:freed_by"
   },
   {
    "code": "lazychunk_cbytes = sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | sw32_(*chunk + BLOSC2_CHUNK_CBYTES) | *chunk + BLOSC2_CHUNK_CBYTES | *chunk",
    "fn": "frame_get_lazychunk",
    "kind": "unknown",
    "line": 2021,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/common/zstd_common.c",
    "fn": "ZSTD_customMalloc",
    "line": 60
   },
   "size_bytes": 27352,
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
   "fn": "ZSTD_freeDDict",
   "guard_count": 1,
   "guards": "ddict==NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 27352,
    "width": 24
   },
   "code": "cMem = ddict->cMem | ddict->cMem",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.9/decompress/zstd_ddict.c",
    "fn": "ZSTD_freeDDict",
    "line": 215
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "cMem",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_f84af976e1d8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-526.log",
   "testcase_size": 186
  },
  "input_reachability": [
   "ddict"
  ],
  "osv_id": "OSV-2021-526",
  "project": "c-blosc2",
  "sites": [
   {
    "code": null,
    "fn": "ZSTD_customFree",
    "kind": "free",
    "line": 81,
    "origin": "report:freed_by"
   },
   {
    "code": "cMem = ddict->cMem | ddict->cMem",
    "fn": "ZSTD_freeDDict",
    "kind": "unknown",
    "line": 215,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "calloc",
   "cross_function": true,
   "site": {
    "file": "/src/libredwg/src/in_dxf.c",
    "fn": "xcalloc",
    "line": 216
   },
   "size_bytes": 16,
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
   "fn": "dxf_objects_read",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 16,
    "width": 2
   },
   "code": null,
   "site": {
    "file": "/src/libredwg/src/in_dxf.c",
    "fn": "dxf_objects_read",
    "line": 12267
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "artifacts/by_crash_type/heap-use-after-free/libredwg/address/23a5dd6de69ea81f79948e620306248c51b5f034/OSV-2021-543",
   "testcase_size": 256
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-543",
  "project": "libredwg",
  "sites": [
   {
    "code": null,
    "fn": "dxf_free_pair",
    "kind": "free",
    "line": 515,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "dxf_objects_read",
    "kind": "unknown",
    "line": 12267,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/common/zstd_common.c",
    "fn": "ZSTD_customMalloc",
    "line": 60
   },
   "size_bytes": 27324,
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
   "fn": "ZSTD_freeDDict",
   "guard_count": 1,
   "guards": "ddict==NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 27324,
    "width": 4
   },
   "code": "cMem = ddict->cMem | ddict->cMem",
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.5.2/decompress/zstd_ddict.c",
    "fn": "ZSTD_freeDDict",
    "line": 215
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "cMem",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_886d4c9b7833.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-652.log",
   "testcase_size": 24087
  },
  "input_reachability": [
   "ddict"
  ],
  "osv_id": "OSV-2021-652",
  "project": "c-blosc2",
  "sites": [
   {
    "code": null,
    "fn": "ZSTD_customFree",
    "kind": "free",
    "line": 81,
    "origin": "report:freed_by"
   },
   {
    "code": "cMem = ddict->cMem | ddict->cMem",
    "fn": "ZSTD_freeDDict",
    "kind": "unknown",
    "line": 215,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/tr_languages.c",
    "fn": "NewTranslator",
    "line": 242
   },
   "size_bytes": 14864,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2617,IF:2622,ELSE:2627,IF:2632,IF:2633,WHILE:2641,IF:2644,CONTINUE:2647,IF:2659,ELSE:2662,WHILE:2668,IF:2672",
   "fn": "LookupDict2",
   "guard_count": 1,
   "guards": "tr != translator",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 14864,
    "width": 4
   },
   "code": "tr->transpose_min > 0 | tr->transpose_min",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "fn": "LookupDict2",
    "line": 2622
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "line": 2593,
    "size": null,
    "type": "Translator*"
   },
   "kind": "pointer",
   "name": "tr",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_1f76c4b8bd32.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2021-765.log",
   "testcase_size": 2
  },
  "input_reachability": [
   "tr"
  ],
  "osv_id": "OSV-2021-765",
  "project": "espeak-ng",
  "sites": [
   {
    "code": null,
    "fn": "DeleteTranslator",
    "kind": "free",
    "line": 218,
    "origin": "report:freed_by"
   },
   {
    "code": "tr->transpose_min > 0 | tr->transpose_min",
    "fn": "LookupDict2",
    "kind": "unknown",
    "line": 2622,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
  },
  "types": {
   "cast_present": null,
   "entity_type": "Translator*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "calloc",
   "cross_function": true,
   "site": {
    "file": "/src/libredwg/src/in_dxf.c",
    "fn": "xcalloc",
    "line": 227
   },
   "size_bytes": 16,
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
   "fn": "dwg_free_TABLEGEOMETRY_private",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 16,
    "width": 8
   },
   "code": null,
   "site": {
    "file": "/src/libredwg/src/dwg.spec",
    "fn": "dwg_free_TABLEGEOMETRY_private",
    "line": 6411
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "artifacts/by_crash_type/heap-use-after-free/libredwg/address/d0accfd39bb1acc70ed0fbfcbf33e466d389c087/OSV-2021-771",
   "testcase_size": 4096
  },
  "input_reachability": [],
  "osv_id": "OSV-2021-771",
  "project": "libredwg",
  "sites": [
   {
    "code": null,
    "fn": "dxf_free_pair",
    "kind": "free",
    "line": 557,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "dwg_free_TABLEGEOMETRY_private",
    "kind": "unknown",
    "line": 6411,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
   "size_bytes": 24,
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
    "region_bytes": 24,
    "width": 1
   },
   "code": "((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') && (*s2  | ((*s1 == *s2) || (*s1 == '.')) && (*s1 != '\\0') | (*s1 == *s2) || (*s1 == '.') | *s1 == *s2",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "isSubset",
    "line": 1070
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "s1",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_07564b7d879c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-1246.log",
   "testcase_size": 7362
  },
  "input_reachability": [
   "s1",
   "s2"
  ],
  "osv_id": "OSV-2022-1246",
  "project": "hunspell",
  "sites": [
   {
    "code": null,
    "fn": "__libcpp_deallocate<char>",
    "kind": "free",
    "line": 63,
    "origin": "report:freed_by"
   },
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
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::parse_file(char const*, char const*)",
    "line": 275
   },
   "size_bytes": 65936,
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
   "fn": "prefix_check",
   "guard_count": 0,
   "guards": null,
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 65936,
    "width": 2
   },
   "code": "TESTAFF(pe->getCont(), onlyincompound, pe->getContLen()) | pe->getCont() | pe->getContLen() | std::binary_search(pe->getCont(), pe->getCont() + pe->ge",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::prefix_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, int, char, unsigned short)",
    "line": 1098
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "pe",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_1f1d23ca0683.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2022-889.log",
   "testcase_size": 66357
  },
  "input_reachability": [
   "this",
   "word",
   "len",
   "needflag"
  ],
  "osv_id": "OSV-2022-889",
  "project": "hunspell",
  "sites": [
   {
    "code": null,
    "fn": "finishFileMgr",
    "kind": "free",
    "line": 257,
    "origin": "report:freed_by"
   },
   {
    "code": "TESTAFF(pe->getCont(), onlyincompound, pe->getContLen()) | pe->getCont() | pe->getContLen() | std::binary_search(pe->getCont(), pe->getCont() + pe->ge",
    "fn": "AffixMgr::prefix_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, int, int, char, unsigned short)",
    "kind": "unknown",
    "line": 1098,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
    "fn": "HashMgr::load_config(char const*, char const*)",
    "line": 950
   },
   "size_bytes": 65936,
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
   "fn": "free_flag",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 65936,
    "width": 2
   },
   "code": "astr && (aliasf.empty() || TESTAFF(astr, ONLYUPCASEFLAG, | aliasf.empty() || TESTAFF(astr, ONLYUPCASEFLAG, alen) | aliasf.empty() | this->aliasf",
   "site": {
    "file": "/src/hunspell/src/hunspell/hashmgr.cxx",
    "fn": "free_flag",
    "line": 110
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "astr",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_a9b7270c1c28.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-156.log",
   "testcase_size": 66307
  },
  "input_reachability": [
   "this",
   "astr",
   "alen"
  ],
  "osv_id": "OSV-2023-156",
  "project": "hunspell",
  "sites": [
   {
    "code": null,
    "fn": "HashMgr::load_config(char const*, char const*)",
    "kind": "free",
    "line": null,
    "origin": "report:freed_by"
   },
   {
    "code": "astr && (aliasf.empty() || TESTAFF(astr, ONLYUPCASEFLAG, | aliasf.empty() || TESTAFF(astr, ONLYUPCASEFLAG, alen) | aliasf.empty() | this->aliasf",
    "fn": "free_flag",
    "kind": "unknown",
    "line": 110,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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
   "size_bytes": 1204224,
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
   "fn": "ih264_inter_pred_luma_vert_ssse3",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 1204224,
    "width": 16
   },
   "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)pu1_src) | _mm_loadu_si128((__m128i *)pu1_src) | (__m128i *)pu1_src",
   "site": {
    "file": "/src/libavc/common/x86/ih264_inter_pred_filters_ssse3.c",
    "fn": "ih264_inter_pred_luma_vert_ssse3",
    "line": 650
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "src_r0_16x8b",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-342.log",
   "testcase_size": 18797
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-342",
  "project": "libavc",
  "sites": [
   {
    "code": "src_r0_16x8b = _mm_loadu_si128((__m128i *)pu1_src) | _mm_loadu_si128((__m128i *)pu1_src) | (__m128i *)pu1_src",
    "fn": "ih264_inter_pred_luma_vert_ssse3",
    "kind": "unknown",
    "line": 650,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "ih264d_free_dynamic_bufs",
    "kind": "free",
    "line": 2337,
    "origin": "report:freed_by"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "heap-use-after-free",
   "report_fault_kind": "heap-use-after-free",
   "used": "heap-use-after-free"
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