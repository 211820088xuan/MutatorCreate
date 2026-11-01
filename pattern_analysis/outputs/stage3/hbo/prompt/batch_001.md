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
    "file": "/src/flac/src/libFLAC/../../include/share/alloc.h",
    "fn": "safe_realloc_nofree_mul_2op_",
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
   "fn": "process_page_",
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
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/flac/src/libFLAC/ogg_decoder_aspect.c",
    "fn": "process_page_",
    "line": 130
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
   "cpg": "/root/gyx/mutator_create/cpg_files/flac_d367d6fe9283.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/flac/address/d367d6fe92839cce257eafaa0dc650cc5bd16151/ARVO-371068253/report.log",
   "testcase_size": 162876
  },
  "input_reachability": [],
  "osv_id": "ARVO-371068253",
  "project": "flac",
  "sites": [
   {
    "code": null,
    "fn": "process_page_",
    "kind": "unknown",
    "line": 130,
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
   "fn": "extract_sendrecv_mode",
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
    "width": 6
   },
   "code": null,
   "site": {
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "fn": "extract_sendrecv_mode",
    "line": 387
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-372515090/report.log",
   "testcase_size": 7257
  },
  "input_reachability": [],
  "osv_id": "ARVO-372515090",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "extract_sendrecv_mode",
    "kind": "unknown",
    "line": 387,
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
    "file": "/src/htslib/cram/cram_io.c",
    "fn": "refs2id",
    "line": 2715
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
   "control_structures": "IF:1833,GOTO:1834,IF:1836,GOTO:1837,IF:1845,ELSE:1849,IF:1849,IF:1866,IF:1867,GOTO:1868,IF:1871,IF:1873",
   "fn": "cram_encode_container",
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
    "width": 8
   },
   "code": "c->ref_end > fd->refs->ref_id[c->ref_id]->LN_length | c->ref_end | fd->refs->ref_id[c->ref_id]->LN_length | fd->refs->ref_id[c->ref_id]",
   "site": {
    "file": "/src/htslib/cram/cram_encode.c",
    "fn": "cram_encode_container",
    "line": 2000
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/cram/cram_encode.c",
    "line": 1825,
    "size": null,
    "type": "cram_container*"
   },
   "kind": "pointer",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_ca920611fcd8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/ca920611fcd8be1180045589ac11bff2f04eafd8/ARVO-372547397/report.log",
   "testcase_size": 1735
  },
  "input_reachability": [
   "fd",
   "c"
  ],
  "osv_id": "ARVO-372547397",
  "project": "htslib",
  "sites": [
   {
    "code": "c->ref_end > fd->refs->ref_id[c->ref_id]->LN_length | c->ref_end | fd->refs->ref_id[c->ref_id]->LN_length | fd->refs->ref_id[c->ref_id]",
    "fn": "cram_encode_container",
    "kind": "unknown",
    "line": 2000,
    "origin": "report:crash"
   },
   {
    "code": "calloc(ntags*2, sizeof(*s->aux_block))",
    "fn": "cram_encode_container",
    "kind": "calloc",
    "line": 2077,
    "origin": "cpg"
   },
   {
    "code": "malloc(sizeof(*spares))",
    "fn": "cram_encode_container",
    "kind": "malloc",
    "line": 2107,
    "origin": "cpg"
   },
   {
    "code": "malloc(c->num_landmarks * sizeof(*c->landmark))",
    "fn": "cram_encode_container",
    "kind": "malloc",
    "line": 2448,
    "origin": "cpg"
   },
   {
    "code": "free(c->ref)",
    "fn": "cram_encode_container",
    "kind": "free",
    "line": 2514,
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
   "entity_type": "cram_container*",
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
   "fn": "extract_fmtp",
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
    "width": 6
   },
   "code": null,
   "site": {
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "fn": "extract_fmtp",
    "line": 216
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-375237153/report.log",
   "testcase_size": 3185
  },
  "input_reachability": [],
  "osv_id": "ARVO-375237153",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "extract_fmtp",
    "kind": "unknown",
    "line": 216,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x270b2)",
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
   "fn": "extract_ice_option",
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
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "fn": "extract_ice_option",
    "line": 384
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
   "cpg": "/root/gyx/mutator_create/cpg_files/kamailio_fe7d7c571b6c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/fe7d7c571b6c8d446cf66a1cf27d335d98f5f945/ARVO-376100377/report.log",
   "testcase_size": 873
  },
  "input_reachability": [],
  "osv_id": "ARVO-376100377",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "extract_ice_option",
    "kind": "unknown",
    "line": 384,
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
    "fn": "__getdelim (/lib/x86_64-linux-gnu/libc.so.6+0x83543) (BuildId: 5792732f783158c66fb4f3756458ca24e46e827d)",
    "line": null
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
   "control_structures": "WHILE:2033,IF:2038,IF:2039,IF:2043,IF:2044,IF:2048,IF:2054,IF:2058,IF:2061,ELSE:2072,IF:2074,IF:2076",
   "fn": "parse",
   "guard_count": 4,
   "guards": "l == t | l == t | i < sizeof(m->desc)",
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
   "code": "i = 0 | (m->desc[i++] = *l++) != '\\0' && i < sizeof(m->desc) | (m->desc[i++] = *l++) != '\\0' | m->desc[i++] = *l++",
   "site": {
    "file": "/src/file/src/apprentice.c",
    "fn": "parse",
    "line": 2400
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/file/src/apprentice.c",
    "line": 2020,
    "size": null,
    "type": "size_t"
   },
   "kind": "struct",
   "name": "i",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/file_93ddf99bc1d4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/93ddf99bc1d4e3dd526d5ae5367c3b4c4800354f/ARVO-376515517/report.log",
   "testcase_size": 40
  },
  "input_reachability": [
   "ms",
   "me",
   "line",
   "lineno"
  ],
  "osv_id": "ARVO-376515517",
  "project": "file",
  "sites": [
   {
    "code": "realloc(me->mp, sizeof (*nm) * cnt)",
    "fn": "parse",
    "kind": "realloc",
    "line": 2061,
    "origin": "cpg"
   },
   {
    "code": "malloc(len)",
    "fn": "parse",
    "kind": "malloc",
    "line": 2076,
    "origin": "cpg"
   },
   {
    "code": "i = 0 | (m->desc[i++] = *l++) != '\\0' && i < sizeof(m->desc) | (m->desc[i++] = *l++) != '\\0' | m->desc[i++] = *l++",
    "fn": "parse",
    "kind": "unknown",
    "line": 2400,
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
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 146
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
   "fn": "ndpi_search_mikrotik",
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
    "width": 16
   },
   "code": null,
   "site": {
    "file": "/src/ndpi/src/lib/protocols/mikrotik.c",
    "fn": "ndpi_search_mikrotik",
    "line": null
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
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_3ce8d0e5087f.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/3ce8d0e5087f6e3f2a3e1f65d39d78c228054a5d/ARVO-379180960/report.log",
   "testcase_size": 259
  },
  "input_reachability": [],
  "osv_id": "ARVO-379180960",
  "project": "ndpi",
  "sites": [],
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
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_operator_new<unsigned long>",
    "line": 245
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
   "control_structures": "IF:2096,IF:2098,ELSE:2102,IF:2102,ELSE:2106",
   "fn": "SetTextureProperties",
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
   "code": "TrySetTextureProperties(out_mat, _textures, \"ReflectionF",
   "site": {
    "file": "/src/assimp/code/AssetLib/FBX/FBXExporter.cpp",
    "fn": "Assimp::FBXExporter::WriteObjects()",
    "line": 2053
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/assimp/code/AssetLib/FBX/FBXExporter.cpp",
    "line": 2039,
    "size": null,
    "type": "aiMaterial*"
   },
   "kind": "pointer",
   "name": "out_mat",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/assimp_0c4d5909f8ca.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/assimp/address/0c4d5909f8ca1931f3ca5c66ab5f0c37ea2efc2e/ARVO-379418968/report.log",
   "testcase_size": 1400
  },
  "input_reachability": [
   "out_mat",
   "_textures",
   "mesh"
  ],
  "osv_id": "ARVO-379418968",
  "project": "assimp",
  "sites": [
   {
    "code": "TrySetTextureProperties(out_mat, _textures, \"ReflectionF",
    "fn": "Assimp::FBXExporter::WriteObjects()",
    "kind": "unknown",
    "line": 2053,
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
   "entity_type": "aiMaterial*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_operator_new<unsigned long>",
    "line": 271
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
   "fn": "cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)",
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
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/opencv/modules/imgcodecs/src/grfmt_png.cpp",
    "fn": "cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)",
    "line": 661
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
   "cpg": "/root/gyx/mutator_create/cpg_files/opencv_8bc65a1d136c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opencv/address/8bc65a1d136c2ac4c31910ee271b5f3c9d14317e/ARVO-386688710/report.log",
   "testcase_size": 12
  },
  "input_reachability": [],
  "osv_id": "ARVO-386688710",
  "project": "opencv",
  "sites": [
   {
    "code": null,
    "fn": "cv::PngDecoder::read_from_io(void*, unsigned long, unsigned long)",
    "kind": "unknown",
    "line": 661,
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
    "file": null,
    "fn": "g_malloc0 (/out/matrixsave_buffer_fuzzer+0xba9d60)",
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
   "fn": "rtiff_decompress_jpeg_run",
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
    "file": "/src/libvips/libvips/foreign/tiff2vips.c",
    "fn": "rtiff_decompress_jpeg_run",
    "line": 2100
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-387317434/report.log",
   "testcase_size": 378
  },
  "input_reachability": [],
  "osv_id": "ARVO-387317434",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "rtiff_decompress_jpeg_run",
    "kind": "unknown",
    "line": 2100,
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
    "file": "/src/opencv/modules/core/src/alloc.cpp",
    "fn": "cv::fastMalloc(unsigned long)",
    "line": 137
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
   "fn": "operator()",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 600
   },
   "code": null,
   "site": {
    "file": "/src/opencv/modules/imgcodecs/src/grfmt_png.cpp",
    "fn": "operator()",
    "line": 654
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
   "cpg": "/root/gyx/mutator_create/cpg_files/opencv_ff18c9cc7904.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opencv/address/ff18c9cc7904e878b10273265196e0238490e692/ARVO-390788198/report.log",
   "testcase_size": 2928
  },
  "input_reachability": [],
  "osv_id": "ARVO-390788198",
  "project": "opencv",
  "sites": [
   {
    "code": null,
    "fn": "operator()",
    "kind": "unknown",
    "line": 654,
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
   "fn": "extract_candidate",
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
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "fn": "extract_candidate",
    "line": 304
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-391689728/report.log",
   "testcase_size": 1297
  },
  "input_reachability": [],
  "osv_id": "ARVO-391689728",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "extract_candidate",
    "kind": "unknown",
    "line": 304,
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
   "fn": "extract_mediaip",
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
    "file": "/src/kamailio/src/core/parser/sdp/sdp_helpr_funcs.c",
    "fn": "extract_mediaip",
    "line": 475
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kamailio/address/199f13a7dfac8cd817850c6a6afe5ba510835418/ARVO-391975654/report.log",
   "testcase_size": 6978
  },
  "input_reachability": [],
  "osv_id": "ARVO-391975654",
  "project": "kamailio",
  "sites": [
   {
    "code": null,
    "fn": "extract_mediaip",
    "kind": "unknown",
    "line": 475,
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
    "file": "/src/libheif/libheif/pixelimage.cc",
    "fn": "HeifPixelImage::ImagePlane::alloc(unsigned int, unsigned int, heif_channel_datatype, int, int, heif_security_limits const*)",
    "line": 279
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
   "fn": "vips_foreign_save_heif_pack",
   "guard_count": null,
   "guards": null,
   "in_loop": null,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 248
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/heifsave.c",
    "fn": "vips_foreign_save_heif_pack",
    "line": 383
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-396460413/report.log",
   "testcase_size": 398
  },
  "input_reachability": [],
  "osv_id": "ARVO-396460413",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "vips_foreign_save_heif_pack",
    "kind": "unknown",
    "line": 383,
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
    "file": "/src/ndpi/fuzz/../example/reader_util.c",
    "fn": "get_ndpi_flow_info",
    "line": 929
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
   "control_structures": "IF:1291,IF:1297,IF:1309,IF:1316,IF:1317,IF:1320,ELSE:1322,IF:1322,IF:1327,IF:1331,FOR:1332,ELSE:1344",
   "fn": "process_ndpi_collected_info",
   "guard_count": 4,
   "guards": "i < sizeof(flow->ndpi_flow->protos.bittorrent.hash) | i < flow->ndpi_flow->protos.slp.url_count | i < (size_t)flow->ndpi_flow->protos.slp.url_count - 1",
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
   "code": "strncat(flow->info + length, flow->ndpi_flow->protos.slp | flow->info + length | flow->info | flow->ndpi_flow->protos.slp.url[i]",
   "site": {
    "file": "/src/ndpi/example/reader_util.c",
    "fn": "process_ndpi_collected_info",
    "line": 1379
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/example/reader_util.c",
    "line": 1287,
    "size": null,
    "type": "ndpi_flow_info*"
   },
   "kind": "pointer",
   "name": "flow",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_9ee24d5bc110.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/9ee24d5bc110307b988554d83d1a88a6ad63490e/ARVO-397731139/report.log",
   "testcase_size": 94
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-397731139",
  "project": "ndpi",
  "sites": [
   {
    "code": "strncat(flow->info + length, flow->ndpi_flow->protos.slp | flow->info + length | flow->info | flow->ndpi_flow->protos.slp.url[i]",
    "fn": "process_ndpi_collected_info",
    "kind": "unknown",
    "line": 1379,
    "origin": "report:crash"
   },
   {
    "code": "strdup(flow->ndpi_flow->protos.tls_quic.ja4_client_raw)",
    "fn": "process_ndpi_collected_info",
    "kind": "strdup",
    "line": 1548,
    "origin": "cpg"
   },
   {
    "code": "strdup(flow->ndpi_flow->protos.tls_quic.issuerDN)",
    "fn": "process_ndpi_collected_info",
    "kind": "strdup",
    "line": 1564,
    "origin": "cpg"
   },
   {
    "code": "strdup(flow->ndpi_flow->protos.tls_quic.subjectDN)",
    "fn": "process_ndpi_collected_info",
    "kind": "strdup",
    "line": 1567,
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
   "entity_type": "ndpi_flow_info*",
   "is_signed": null,
   "ptr_origin": "param"
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