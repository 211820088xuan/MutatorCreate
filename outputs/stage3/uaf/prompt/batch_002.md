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
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/decoder/ih264d_utils.c",
    "fn": "ih264d_allocate_dynamic_bufs",
    "line": 2101
   },
   "size_bytes": 602112,
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
   "fn": "ih264_inter_pred_luma_horz_hpel_vert_qpel_ssse3",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 602112,
    "width": 16
   },
   "code": null,
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
   "name": null,
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_ea14d495b199.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libavc/address/ea14d495b1995ff09642edfb1b0b45a3d289b0af/ARVO-42479533/report.log",
   "testcase_size": 122
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479533",
  "project": "libavc",
  "sites": [
   {
    "code": null,
    "fn": "ih264d_free_dynamic_bufs",
    "kind": "free",
    "line": 2252,
    "origin": "report:freed_by"
   },
   {
    "code": null,
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
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "line": 72
   },
   "size_bytes": 565775,
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
   "fn": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": 565775,
    "width": 1
   },
   "code": null,
   "site": {
    "file": "/src/openh264/codec/decoder/plus/src/welsDecoderExt.cpp",
    "fn": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)",
    "line": 505
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_0152b1ed1505.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/0152b1ed1505da2ee6f32b9f6e0eff98a3e91800/ARVO-42479702/report.log",
   "testcase_size": 22
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479702",
  "project": "openh264",
  "sites": [
   {
    "code": null,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "kind": "free",
    "line": 113,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "WelsDec::CWelsDecoder::SetOption(DECODER_OPTION, void*)",
    "kind": "unknown",
    "line": 505,
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
    "file": "/src/open62541/tests/fuzz/custom_memory_manager.c",
    "fn": "UA_memoryManager_calloc",
    "line": 142
   },
   "size_bytes": 32,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "fn": "String_clear",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 32,
    "width": 8
   },
   "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
   "site": {
    "file": "/src/open62541/src/ua_types.c",
    "fn": "String_clear",
    "line": 140
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/open62541/src/ua_types.c",
    "line": 139,
    "size": null,
    "type": "UA_String*"
   },
   "kind": "pointer",
   "name": "s",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/open62541_ac0d94217d06.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/open62541/address/ac0d94217d06a229c9c671cfa0e37b497114848a/ARVO-42481163/report.log",
   "testcase_size": 44
  },
  "input_reachability": [
   "s"
  ],
  "osv_id": "ARVO-42481163",
  "project": "open62541",
  "sites": [
   {
    "code": "UA_Array_delete(s->data, s->length, &UA_TYPES[UA_TYPES_B | s->data | s->length | &UA_TYPES[UA_TYPES_BYTE]",
    "fn": "String_clear",
    "kind": "unknown",
    "line": 140,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "Variant_decodeJsonUnwrapExtensionObject",
    "kind": "free",
    "line": 2994,
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
   "entity_type": "UA_String*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "line": 72
   },
   "size_bytes": 539,
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
    "region_bytes": 539,
    "width": 4
   },
   "code": "{{CTX_NA, CTX_NA}, {0, 58}, {1, 56}, {1, 63}} | {CTX_NA, CTX_NA} | CTX_NA | CTX_NA",
   "site": {
    "file": "/src/openh264/codec/decoder/core/src/manage_dec_ref.cpp",
    "fn": "WelsDec::WelsReorderRefList(WelsDec::TagWelsDecoderContext*)",
    "line": 426
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
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_4b41984f86d6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/openh264/address/4b41984f86d6e46f8e92af17a3515151aa282976/ARVO-42481640/report.log",
   "testcase_size": 54
  },
  "input_reachability": [],
  "osv_id": "ARVO-42481640",
  "project": "openh264",
  "sites": [
   {
    "code": null,
    "fn": "WelsCommon::WelsFree(void*, char const*)",
    "kind": "free",
    "line": 113,
    "origin": "report:freed_by"
   },
   {
    "code": "{{CTX_NA, CTX_NA}, {0, 58}, {1, 56}, {1, 63}} | {CTX_NA, CTX_NA} | CTX_NA | CTX_NA",
    "fn": "WelsDec::WelsReorderRefList(WelsDec::TagWelsDecoderContext*)",
    "kind": "unknown",
    "line": 426,
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
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": null,
    "fn": "g_realloc (/out/jpegsave_file_fuzzer+0xe3ec97)",
    "line": null
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
   "fn": "vips_buf_vappendf",
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
    "file": "/src/libvips/libvips/iofuncs/buf.c",
    "fn": "vips_buf_vappendf",
    "line": 418
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libvips/address/unknown/ARVO-42482031/report.log",
   "testcase_size": 27
  },
  "input_reachability": [],
  "osv_id": "ARVO-42482031",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "vips_foreign_load_matrix_load",
    "kind": "free",
    "line": 239,
    "origin": "report:freed_by"
   },
   {
    "code": null,
    "fn": "vips_buf_vappendf",
    "kind": "unknown",
    "line": 418,
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
   "cross_function": false,
   "site": {
    "file": "/work/build/../../src/perfetto/src/trace_processor/importers/common/track_tracker.cc",
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "line": 339
   },
   "size_bytes": 24,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "FOR:478,IF:481,IF:484,CONTINUE:486,IF:489,CONTINUE:490,SWITCH:492,IF:494,CONTINUE:495,IF:496,CONTINUE:498,IF:500",
   "fn": "Parse",
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
    "width": 8
   },
   "code": "comment_till_eol = false",
   "site": {
    "file": "/src/perfetto/src/trace_processor/importers/common/track_tracker.cc",
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "line": 485
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/perfetto/src/trace_processor/importers/common/track_tracker.cc",
    "line": 474,
    "size": null,
    "type": "bool"
   },
   "kind": "struct",
   "name": "comment_till_eol",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_8a1fbea36994.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/perfetto/address/8a1fbea36994a227c79d36a3ce3a7be7a241fca0/ARVO-42483214/report.log",
   "testcase_size": 113
  },
  "input_reachability": [],
  "osv_id": "ARVO-42483214",
  "project": "perfetto",
  "sites": [
   {
    "code": null,
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "kind": "free",
    "line": 365,
    "origin": "report:freed_by"
   },
   {
    "code": "comment_till_eol = false",
    "fn": "perfetto::trace_processor::TrackTracker::ResolveDescriptorTrack(unsigned long, perfetto::trace_processor::TrackTracker::DescriptorTrackReservation const&, std::__1::vector<unsigned long, std::__1::allocator<unsigned long> >*)",
    "kind": "unknown",
    "line": 485,
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
   "entity_type": "bool",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/leptonica/src/colormap.c",
    "fn": "pixcmapCreate",
    "line": 134
   },
   "size_bytes": 24,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:284,IF:289",
   "fn": "pixcmapDestroy",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 24,
    "width": 8
   },
   "code": "LEPT_FREE(cmap->array) | cmap->array | free(cmap->array) | cmap->array",
   "site": {
    "file": "/src/leptonica/src/colormap.c",
    "fn": "pixcmapDestroy",
    "line": 292
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/leptonica/src/colormap.c",
    "line": 280,
    "size": null,
    "type": "PIXCMAP*"
   },
   "kind": "pointer",
   "name": "cmap",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_695ff35cab05.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/leptonica/address/695ff35cab05b6e7f80da48118a2b8fbe76d74e3/ARVO-42483440/report.log",
   "testcase_size": 44
  },
  "free_related": {
   "free_sites_in_func": [
    292,
    293
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "input_reachability": [],
  "osv_id": "ARVO-42483440",
  "project": "leptonica",
  "sites": [
   {
    "code": "LEPT_FREE(cmap->array) | cmap->array | free(cmap->array) | cmap->array",
    "fn": "pixcmapDestroy",
    "kind": "free",
    "line": 292,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "pixcmapDestroy",
    "kind": "free",
    "line": 293,
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
   "entity_type": "PIXCMAP*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/leptonica/src/pix1.c",
    "fn": "pixCreateNoInit",
    "line": 345
   },
   "size_bytes": 2432,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:784,IF:788,ELSE:792,FOR:802,FOR:803",
   "fn": "pixAverageRasterScans",
   "guard_count": 1,
   "guards": "j < w",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 2432,
    "width": 1
   },
   "code": "val = GET_DATA_BYTE(line, j) | GET_DATA_BYTE(line, j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j) | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j))",
   "site": {
    "file": "/src/leptonica/src/readbarcode.c",
    "fn": "pixAverageRasterScans",
    "line": 805
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/leptonica/src/readbarcode.c",
    "line": 777,
    "size": null,
    "type": "l_int32"
   },
   "kind": "struct",
   "name": "val",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_f6f7c9c4737e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/leptonica/address/f6f7c9c4737e554b724ac8b5091698df67b570cb/ARVO-42484161/report.log",
   "testcase_size": 412
  },
  "input_reachability": [
   "pixs",
   "nscans"
  ],
  "osv_id": "ARVO-42484161",
  "project": "leptonica",
  "sites": [
   {
    "code": null,
    "fn": "pixFree",
    "kind": "free",
    "line": 634,
    "origin": "report:freed_by"
   },
   {
    "code": "val = GET_DATA_BYTE(line, j) | GET_DATA_BYTE(line, j) | *(l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j) | (l_uint8 *)((l_uintptr_t)((const l_uint8 *)(line) + (j))",
    "fn": "pixAverageRasterScans",
    "kind": "unknown",
    "line": 805,
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
   "entity_type": "l_int32",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 81
   },
   "size_bytes": 25421,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:101,IF:104,IF:108,ELSE:111,IF:111,SWITCH:114,BREAK:115,BREAK:116,BREAK:117,IF:120,FOR:121,IF:122",
   "fn": "ndpi_http_check_content",
   "guard_count": 1,
   "guards": "packet->content_disposition_line.len > attachment_len",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 25421,
    "width": 1
   },
   "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "fn": "ndpi_http_check_content",
    "line": 144
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 99,
    "size": null,
    "type": "ndpi_packet_struct*"
   },
   "kind": "pointer",
   "name": "packet",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_b6eef17e5499.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/ndpi/address/b6eef17e54999586b6aef8f545c87de4d3ec0ab3/ARVO-42484314/report.log",
   "testcase_size": 51731
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42484314",
  "project": "ndpi",
  "sites": [
   {
    "code": null,
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "free",
    "line": 84,
    "origin": "report:freed_by"
   },
   {
    "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
    "fn": "ndpi_http_check_content",
    "kind": "unknown",
    "line": 144,
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
   "entity_type": "ndpi_packet_struct*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 81
   },
   "size_bytes": 25443,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:101,IF:104,IF:108,ELSE:111,IF:111,SWITCH:114,BREAK:115,BREAK:116,BREAK:117,IF:120,FOR:121,IF:122",
   "fn": "ndpi_http_check_content",
   "guard_count": 1,
   "guards": "packet->content_disposition_line.len > attachment_len",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 25443,
    "width": 1
   },
   "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "fn": "ndpi_http_check_content",
    "line": 144
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 99,
    "size": null,
    "type": "ndpi_packet_struct*"
   },
   "kind": "pointer",
   "name": "packet",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_b6eef17e5499.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/ndpi/address/b6eef17e54999586b6aef8f545c87de4d3ec0ab3/ARVO-42484479/report.log",
   "testcase_size": 52086
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42484479",
  "project": "ndpi",
  "sites": [
   {
    "code": null,
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "free",
    "line": 84,
    "origin": "report:freed_by"
   },
   {
    "code": "strncmp((const char*)&packet->content_disposition_line.p | strncmp((const char*)&packet->content_disposition_line.p | (const char*)&packet->content_disposition_line.ptr[attac | &packet->content_disposition_line.ptr[attachment_len]",
    "fn": "ndpi_http_check_content",
    "kind": "unknown",
    "line": 144,
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
   "entity_type": "ndpi_packet_struct*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "strndup",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/xmlstring.c",
    "fn": "xmlStrndup",
    "line": 45
   },
   "size_bytes": 4,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:469,IF:471,IF:473,IF:477,IF:487,IF:492,IF:498,ELSE:500,IF:501,WHILE:501,IF:501,IF:501",
   "fn": "__xmlRaiseError",
   "guard_count": 45,
   "guards": "schannel == NULL | ctxt != NULL | ctxt->sax != NULL",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 4,
    "width": 2
   },
   "code": "XML_GET_VAR_STR(msg, str) | int | -1 | str = (char *)xmlMalloc(150)",
   "site": {
    "file": "/src/libxml2/error.c",
    "fn": "__xmlRaiseError",
    "line": 501
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/error.c",
    "line": 460,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "msg",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_00ed736eecf9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/00ed736eecf93aeab49089abb06e0e5fc0e7e091/ARVO-42484562/report.log",
   "testcase_size": 523
  },
  "input_reachability": [
   "schannel",
   "ctx",
   "nod",
   "file",
   "str1",
   "str2",
   "str3",
   "msg"
  ],
  "osv_id": "ARVO-42484562",
  "project": "libxml2",
  "sites": [
   {
    "code": null,
    "fn": "xmlTextReaderFreeProp",
    "kind": "free",
    "line": 311,
    "origin": "report:freed_by"
   },
   {
    "code": "XML_GET_VAR_STR(msg, str) | int | -1 | str = (char *)xmlMalloc(150)",
    "fn": "__xmlRaiseError",
    "kind": "unknown",
    "line": 501,
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
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 80
   },
   "size_bytes": 25443,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:183,IF:207,IF:213,IF:220,ELSE:222,SWITCH:223,BREAK:224,BREAK:225,BREAK:226,SWITCH:229,BREAK:230,BREAK:231",
   "fn": "check_content_type_and_change_protocol",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 25443,
    "width": 2
   },
   "code": "strncpy((char*)flow->protos.http.nat_ip, (char*)packet-> | (char*)flow->protos.http.nat_ip | flow->protos.http.nat_ip | flow->protos.http",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "fn": "check_content_type_and_change_protocol",
    "line": 342
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 178,
    "size": null,
    "type": "ndpi_flow_struct*"
   },
   "kind": "pointer",
   "name": "flow",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_812505b56bb4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/ndpi/address/812505b56bb4508bc42e1615d6425ad26444d3f8/ARVO-42485194/report.log",
   "testcase_size": 51829
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42485194",
  "project": "ndpi",
  "sites": [
   {
    "code": null,
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "free",
    "line": 83,
    "origin": "report:freed_by"
   },
   {
    "code": "strncpy((char*)flow->protos.http.nat_ip, (char*)packet-> | (char*)flow->protos.http.nat_ip | flow->protos.http.nat_ip | flow->protos.http",
    "fn": "check_content_type_and_change_protocol",
    "kind": "unknown",
    "line": 342,
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
   "entity_type": "ndpi_flow_struct*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/buf.c",
    "fn": "xmlBufCreate",
    "line": 137
   },
   "size_bytes": 4096,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:180,WHILE:186,WHILE:191,IF:194,WHILE:201,WHILE:213,IF:214",
   "fn": "xmlParserPrintFileContextInternal",
   "guard_count": 2,
   "guards": "cur > base | cur > base",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 4096,
    "width": 1
   },
   "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
   "site": {
    "file": "/src/libxml2/error.c",
    "fn": "xmlParserPrintFileContextInternal",
    "line": 194
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/error.c",
    "line": 175,
    "size": null,
    "type": "xmlChar*"
   },
   "kind": "pointer",
   "name": "cur",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_84bab955fe01.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/84bab955fe01c50e64382481de67259047d917a9/ARVO-42485276/report.log",
   "testcase_size": 2157
  },
  "input_reachability": [
   "input",
   "data"
  ],
  "osv_id": "ARVO-42485276",
  "project": "libxml2",
  "sites": [
   {
    "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
    "fn": "xmlParserPrintFileContextInternal",
    "kind": "unknown",
    "line": 194,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "xmlBufGrowInternal",
    "kind": "free",
    "line": 486,
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
   "entity_type": "xmlChar*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/buf.c",
    "fn": "xmlBufCreate",
    "line": 137
   },
   "size_bytes": 4096,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:180,WHILE:186,WHILE:191,IF:194,WHILE:201,WHILE:213,IF:214",
   "fn": "xmlParserPrintFileContextInternal",
   "guard_count": 2,
   "guards": "cur > base | cur > base",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 4096,
    "width": 1
   },
   "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
   "site": {
    "file": "/src/libxml2/error.c",
    "fn": "xmlParserPrintFileContextInternal",
    "line": 194
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/error.c",
    "line": 175,
    "size": null,
    "type": "xmlChar*"
   },
   "kind": "pointer",
   "name": "cur",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_84bab955fe01.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/84bab955fe01c50e64382481de67259047d917a9/ARVO-42485599/report.log",
   "testcase_size": 2060
  },
  "input_reachability": [
   "input",
   "data"
  ],
  "osv_id": "ARVO-42485599",
  "project": "libxml2",
  "sites": [
   {
    "code": "(*(cur) == '\\n') || (*(cur) == '\\r') | *(cur) == '\\n' | *(cur) | *(cur) == '\\r'",
    "fn": "xmlParserPrintFileContextInternal",
    "kind": "unknown",
    "line": 194,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "xmlBufGrowInternal",
    "kind": "free",
    "line": 486,
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
   "entity_type": "xmlChar*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/libxml2/tree.c",
    "fn": "xmlNewNodeEatName",
    "line": 2283
   },
   "size_bytes": 120,
   "size_expr": null
  },
  "call_chain": [],
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2152,IF:2159,IF:2170,IF:2171,ELSE:2173,IF:2174,IF:2177,IF:2181,IF:2190,SWITCH:2193,BREAK:2200,BREAK:2207",
   "fn": "xmlCharEncFirstLineInput",
   "guard_count": 0,
   "guards": null,
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": 120,
    "width": 4
   },
   "code": "buf[50] | buf[50]",
   "site": {
    "file": "/src/libxml2/xinclude.c",
    "fn": "xmlXIncludeIncludeNode",
    "line": 2216
   }
  },
  "crash_type": "heap-use-after-free",
  "entity": {
   "decl": {
    "file": "/src/libxml2/xinclude.c",
    "line": 2216,
    "size": null,
    "type": "char[50]"
   },
   "kind": "array",
   "name": "buf",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_9de7b94d4ffb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/libxml2/address/9de7b94d4ffbd11814008a5aa529b4ca77564921/ARVO-42486565/report.log",
   "testcase_size": 120
  },
  "input_reachability": [],
  "osv_id": "ARVO-42486565",
  "project": "libxml2",
  "sites": [
   {
    "code": "buf[50] | buf[50]",
    "fn": "xmlXIncludeIncludeNode",
    "kind": "unknown",
    "line": 2216,
    "origin": "report:crash"
   },
   {
    "code": null,
    "fn": "xmlFreeNode",
    "kind": "free",
    "line": 3819,
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
   "entity_type": "char[50]",
   "is_signed": null,
   "ptr_origin": "unknown"
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