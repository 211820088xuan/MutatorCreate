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
   "control_structures": "IF:169,IF:171,IF:172,GOTO:173",
   "fn": "H5MM_xstrdup",
   "guard_count": 1,
   "guards": "NULL == (ret_value = HDstrdup(s))",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 5
   },
   "code": "NULL == (ret_value = HDstrdup(s)) | ret_value = HDstrdup(s) | HDstrdup(s) | strdup(s)",
   "site": {
    "file": "/src/hdf5/src/H5MM.c",
    "fn": "H5MM_xstrdup",
    "line": 172
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "NULL",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-430.log",
   "testcase_size": 1032
  },
  "input_reachability": [
   "s"
  ],
  "osv_id": "OSV-2023-430",
  "project": "hdf5",
  "sites": [
   {
    "code": "NULL == (ret_value = HDstrdup(s)) | ret_value = HDstrdup(s) | HDstrdup(s) | strdup(s)",
    "fn": "H5MM_xstrdup",
    "kind": "unknown",
    "line": 172,
    "origin": "report:crash"
   },
   {
    "code": "strdup(s)",
    "fn": "H5MM_xstrdup",
    "kind": "strdup",
    "line": 172,
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
   "entity_type": null,
   "is_signed": null
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/hdf5/src/H5Centry.c",
    "fn": "H5C__flush_single_entry",
    "line": 537
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
   "fn": "H5FS__sinfo_serialize_node_cb",
   "guard_count": 2,
   "guards": "_i < udata->sect_cnt_size | _i < udata->sinfo->sect_len_size",
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
   "code": "UINT64ENCODE_VAR(*udata->image, fspace_node->sect_size,  | *udata->image | udata->image | fspace_node->sect_size",
   "site": {
    "file": "/src/hdf5/src/H5FScache.c",
    "fn": "H5FS__sinfo_serialize_node_cb",
    "line": 1437
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "udata",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-471.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "_item",
   "_udata"
  ],
  "osv_id": "OSV-2023-471",
  "project": "hdf5",
  "sites": [
   {
    "code": "UINT64ENCODE_VAR(*udata->image, fspace_node->sect_size,  | *udata->image | udata->image | fspace_node->sect_size",
    "fn": "H5FS__sinfo_serialize_node_cb",
    "kind": "unknown",
    "line": 1437,
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
    "fn": "std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>>::replace(unsigned long, unsigned long, char const*, unsigned long) (/out/affdicfuzzer+0x35b241)",
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
   "guard_count": 16,
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
    "line": 1612
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
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_1be974933b09.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-508.log",
   "testcase_size": 8209
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
  "osv_id": "OSV-2023-508",
  "project": "hunspell",
  "sites": [
   {
    "code": "(st[i] & 0xc0) == 0x80 | st[i] & 0xc0 | st[i] | i++",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "kind": "unknown",
    "line": 1612,
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
   "fn": "match",
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
   "code": "",
   "site": {
    "file": "/src/pcre2/src/pcre2_match.c",
    "fn": "match",
    "line": 5795
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
   "cpg": "/root/gyx/mutator_create/cpg_files/pcre2_b0b3fc4c4bc4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-673.log",
   "testcase_size": 10
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-673",
  "project": "pcre2",
  "sites": [
   {
    "code": "",
    "fn": "match",
    "kind": "unknown",
    "line": 5795,
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
    "file": "/src/pcre2/src/pcre2_compile.c",
    "fn": "pcre2_compile_8",
    "line": 10404
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
   "fn": "get_grouplength",
   "guard_count": 1,
   "guards": "branchminlength < groupminlength",
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
   "code": "gi[1] = groupminlength | gi[1]",
   "site": {
    "file": "/src/pcre2/src/pcre2_compile.c",
    "fn": "get_grouplength",
    "line": 9278
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "gi",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/pcre2_5f77d022733a.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-674.log",
   "testcase_size": 261
  },
  "input_reachability": [
   "pptrptr",
   "group",
   "recurses",
   "cb"
  ],
  "osv_id": "OSV-2023-674",
  "project": "pcre2",
  "sites": [
   {
    "code": "gi[1] = groupminlength | gi[1]",
    "fn": "get_grouplength",
    "kind": "unknown",
    "line": 9278,
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
   "fn": "isvcd_residual_samp_mb_dyadic",
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
    "width": 2
   },
   "code": "i4_luma_nnz = (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_lu | (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask) >> i4 | ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask | ps_inter_lyr_mb_prms->u2_luma_nnz",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_residual_resamp.c",
    "fn": "isvcd_residual_samp_mb_dyadic",
    "line": 2031
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "i4_luma_nnz",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-68.log",
   "testcase_size": 160
  },
  "input_reachability": [
   "ps_ref_mb_mode"
  ],
  "osv_id": "OSV-2023-68",
  "project": "libavc",
  "sites": [
   {
    "code": "i4_luma_nnz = (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_lu | (ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask) >> i4 | ps_inter_lyr_mb_prms->u2_luma_nnz & u2_luma_mask | ps_inter_lyr_mb_prms->u2_luma_nnz",
    "fn": "isvcd_residual_samp_mb_dyadic",
    "kind": "unknown",
    "line": 2031,
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
   "control_structures": "IF:769,IF:779,DO:780,DO:780,DO:780,DO:780,GOTO:780",
   "fn": "H5O__cache_chk_serialize",
   "guard_count": 1,
   "guards": "chk_proxy->oh->chunk[chk_proxy->chunkno].size == len",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 32
   },
   "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
   "site": {
    "file": "/src/hdf5/src/H5Ocache.c",
    "fn": "H5O__cache_chk_serialize",
    "line": 786
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5Ocache.c",
    "line": 764,
    "size": null,
    "type": "void*"
   },
   "kind": "pointer",
   "name": "image",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_875fb3e70a0d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-722.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "image",
   "len",
   "_thing"
  ],
  "osv_id": "OSV-2023-722",
  "project": "hdf5",
  "sites": [
   {
    "code": "H5MM_memcpy(image, chk_proxy->oh->chunk[chk_proxy->chunk | chk_proxy->oh->chunk[chk_proxy->chunkno].image | chk_proxy->oh->chunk[chk_proxy->chunkno] | chk_proxy->oh->chunk",
    "fn": "H5O__cache_chk_serialize",
    "kind": "unknown",
    "line": 786,
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
   "entity_type": "void*",
   "is_signed": null,
   "ptr_origin": "param"
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
   "fn": "isvcd_interlyr_motion_mode_pred_dyadic",
   "guard_count": 1,
   "guards": "i1_ref_mb_mode > SVC_INTER_MB",
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
   "code": "i1_ref_mb_mode = ps_inter_lyr_mb_prms->i1_mb_mode | ps_inter_lyr_mb_prms->i1_mb_mode",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_mode_mv_resamp.c",
    "fn": "isvcd_interlyr_motion_mode_pred_dyadic",
    "line": 2622
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "i1_ref_mb_mode",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-75.log",
   "testcase_size": 201
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-75",
  "project": "libavc",
  "sites": [
   {
    "code": "i1_ref_mb_mode = ps_inter_lyr_mb_prms->i1_mb_mode | ps_inter_lyr_mb_prms->i1_mb_mode",
    "fn": "isvcd_interlyr_motion_mode_pred_dyadic",
    "kind": "unknown",
    "line": 2622,
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
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "H5O__chunk_protect",
   "guard_count": 5,
   "guards": "idx < oh->nchunks | 0 == idx | chk_proxy->oh == oh",
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
   "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
   "site": {
    "file": "/src/hdf5/src/H5Ochunk.c",
    "fn": "H5O__chunk_protect",
    "line": 178
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "chk_udata",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-754.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "f",
   "oh",
   "idx"
  ],
  "osv_id": "OSV-2023-754",
  "project": "hdf5",
  "sites": [
   {
    "code": "chk_udata.size    = oh->chunk[idx].size | chk_udata.size | oh->chunk[idx].size | oh->chunk[idx]",
    "fn": "H5O__chunk_protect",
    "kind": "unknown",
    "line": 178,
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1571,IF:1584,GOTO:1586,IF:1589,GOTO:1590,IF:1596,GOTO:1598,IF:1601,GOTO:1602,IF:1609,IF:1610,GOTO:1612",
   "fn": "H5SM_delete",
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
   "code": "type_id = sh_mesg->msg_type_id | sh_mesg->msg_type_id",
   "site": {
    "file": "/src/hdf5/src/H5SM.c",
    "fn": "H5SM_delete",
    "line": 1578
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5SM.c",
    "line": 1568,
    "size": null,
    "type": "unsigned"
   },
   "kind": "struct",
   "name": "type_id",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-76.log",
   "testcase_size": 1028
  },
  "input_reachability": [
   "sh_mesg"
  ],
  "osv_id": "OSV-2023-76",
  "project": "hdf5",
  "sites": [
   {
    "code": "type_id = sh_mesg->msg_type_id | sh_mesg->msg_type_id",
    "fn": "H5SM_delete",
    "kind": "unknown",
    "line": 1578,
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
   "entity_type": "unsigned",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/hdf5/src/H5Cimage.c",
    "fn": "H5C__load_cache_image",
    "line": 645
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
   "fn": "H5C__decode_cache_image_header",
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
   "code": "HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | memcmp(p, \"MDCI\", (size_t)4) | (size_t)4",
   "site": {
    "file": "/src/hdf5/src/H5Cimage.c",
    "fn": "H5C__decode_cache_image_header",
    "line": 1338
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
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-77.log",
   "testcase_size": 2565
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-77",
  "project": "hdf5",
  "sites": [
   {
    "code": "HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | HDmemcmp(p, H5C__MDCI_BLOCK_SIGNATURE, (size_t)H5C__MDCI | memcmp(p, \"MDCI\", (size_t)4) | (size_t)4",
    "fn": "H5C__decode_cache_image_header",
    "kind": "unknown",
    "line": 1338,
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:103,IF:110,GOTO:111,FOR:113,IF:117,GOTO:118,IF:121,IF:132,GOTO:133,FOR:135,SWITCH:138,IF:143",
   "fn": "H5O__fsinfo_decode",
   "guard_count": 2,
   "guards": "vers == H5O_FSINFO_VERSION_0 | vers >= 1",
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
   "code": "vers = *p++ | *p++ | p++",
   "site": {
    "file": "/src/hdf5/src/H5Ofsinfo.c",
    "fn": "H5O__fsinfo_decode",
    "line": 119
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5Ofsinfo.c",
    "line": 99,
    "size": null,
    "type": "unsigned"
   },
   "kind": "struct",
   "name": "vers",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_8562645b8a0b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-79.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "p"
  ],
  "osv_id": "OSV-2023-79",
  "project": "hdf5",
  "sites": [
   {
    "code": "vers = *p++ | *p++ | p++",
    "fn": "H5O__fsinfo_decode",
    "kind": "unknown",
    "line": 119,
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
   "entity_type": "unsigned",
   "is_signed": null,
   "ptr_origin": "assignment"
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
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "H5F__accum_free",
   "guard_count": 2,
   "guards": "overlap_size < accum->dirty_off | overlap_size < (accum->dirty_off + accum->dirty_len)",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 361
   },
   "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
   "site": {
    "file": "/src/hdf5/src/H5Faccum.c",
    "fn": "H5F__accum_free",
    "line": 885
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "accum",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-806.log",
   "testcase_size": 1808
  },
  "input_reachability": [
   "f_sh",
   "addr",
   "size"
  ],
  "osv_id": "OSV-2023-806",
  "project": "hdf5",
  "sites": [
   {
    "code": "memmove(accum->buf, accum->buf + overlap_size, new_accum | accum->buf | accum->buf + overlap_size | accum->buf",
    "fn": "H5F__accum_free",
    "kind": "unknown",
    "line": 885,
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
   "alloc.size_expr",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:230",
   "fn": "H5O__mtime_new_encode",
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
   "code": "*p++ = H5O_MTIME_VERSION | *p++ | p++ | H5O_MTIME_VERSION",
   "site": {
    "file": "/src/hdf5/src/H5Omtime.c",
    "fn": "H5O__mtime_new_encode",
    "line": 238
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/hdf5/src/H5Omtime.c",
    "line": 225,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "p",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-89.log",
   "testcase_size": 2208
  },
  "input_reachability": [
   "p"
  ],
  "osv_id": "OSV-2023-89",
  "project": "hdf5",
  "sites": [
   {
    "code": "*p++ = H5O_MTIME_VERSION | *p++ | p++ | H5O_MTIME_VERSION",
    "fn": "H5O__mtime_new_encode",
    "kind": "unknown",
    "line": 238,
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
   "entity_type": "uint8_t*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "isvcd_reflayer_construction_dyadic",
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
   "code": "i1_slice_id = ps_inter_lyr_mb_prms->i1_slice_id | ps_inter_lyr_mb_prms->i1_slice_id",
   "site": {
    "file": "/src/libavc/decoder/svc/isvcd_intra_resamp.c",
    "fn": "isvcd_reflayer_construction_dyadic",
    "line": 2116
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "i1_slice_id",
   "storage": "heap"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-97.log",
   "testcase_size": 1041
  },
  "input_reachability": [
   "ps_ref_mb_mode_map",
   "u2_mb_x",
   "u2_mb_y"
  ],
  "osv_id": "OSV-2023-97",
  "project": "libavc",
  "sites": [
   {
    "code": "i1_slice_id = ps_inter_lyr_mb_prms->i1_slice_id | ps_inter_lyr_mb_prms->i1_slice_id",
    "fn": "isvcd_reflayer_construction_dyadic",
    "kind": "unknown",
    "line": 2116,
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