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
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 63
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
   "control_structures": "IF:1960,IF:1967,IF:1987,IF:1992,ELSE:1997,FOR:2009,IF:2019,FOR:2034,IF:2055,IF:2061,IF:2079,IF:2082",
   "fn": "ih264d_parse_pslice",
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
    "width": 268
   },
   "code": "memcpy((void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_i | (void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_p | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice",
   "site": {
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "fn": "ih264d_parse_pslice",
    "line": 2072
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_parse_pslice.c",
    "line": 1920,
    "size": null,
    "type": "dec_struct_t*"
   },
   "kind": "pointer",
   "name": "ps_dec",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42489821/report.log",
   "testcase_size": 60
  },
  "input_reachability": [
   "ps_dec"
  ],
  "osv_id": "ARVO-42489821",
  "project": "libavc",
  "sites": [
   {
    "code": "memcpy((void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_i | (void *)ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_p | ps_dec->ps_parse_cur_slice->ppv_map_ref_idx_to_poc | ps_dec->ps_parse_cur_slice",
    "fn": "ih264d_parse_pslice",
    "kind": "unknown",
    "line": 2072,
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
   "entity_type": "dec_struct_t*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/libavc/fuzzer/avc_dec_fuzzer.cpp",
    "fn": "iv_aligned_malloc(void*, int, int)",
    "line": 63
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
   "control_structures": "FOR:228,IF:235,FOR:270,IF:277",
   "fn": "ih264d_fill_bs1_16x16mb_pslice",
   "guard_count": 2,
   "guards": "pv_cur_pic_addr0 != pv_nbr_pic_addr0 | pv_cur_pic_addr0 != pv_nbr_pic_addr0",
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
   "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
   "site": {
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "line": 222
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libavc/decoder/ih264d_compute_bs.c",
    "line": 209,
    "size": null,
    "type": "void*"
   },
   "kind": "pointer",
   "name": "pv_cur_pic_addr0",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libavc_6efeedf0633e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libavc/address/6efeedf0633e1965a4d4e17d64f14215e9b6d48f/ARVO-42490025/report.log",
   "testcase_size": 55
  },
  "input_reachability": [
   "ps_cur_mv_pred",
   "ppv_map_ref_idx_to_poc"
  ],
  "osv_id": "ARVO-42490025",
  "project": "libavc",
  "sites": [
   {
    "code": "pv_cur_pic_addr0 = ppv_map_ref_idx_to_poc_l0[ps_cur_mv_p | ppv_map_ref_idx_to_poc_l0[ps_cur_mv_pred->i1_ref_frame[0 | ps_cur_mv_pred->i1_ref_frame[0] | ps_cur_mv_pred->i1_ref_frame",
    "fn": "ih264d_fill_bs1_16x16mb_pslice",
    "kind": "unknown",
    "line": 222,
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
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/usr/local/bin/../include/c++/v1/new",
    "fn": "__libcpp_operator_new<unsigned long>",
    "line": 235
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
   "fn": "consume_replacement_field",
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
   "code": "!consume_specific('{') | consume_specific('{')",
   "site": {
    "file": "/src/serenity/Libraries/LibGfx/BMPLoader.cpp",
    "fn": "Gfx::Streamer::read_u8()",
    "line": 219
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
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_65eef944ab35.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/65eef944ab35ca85be178615ffc32834d430f4e3/ARVO-42490150/report.log",
   "testcase_size": 230
  },
  "input_reachability": [],
  "osv_id": "ARVO-42490150",
  "project": "serenity",
  "sites": [
   {
    "code": "!consume_specific('{') | consume_specific('{')",
    "fn": "Gfx::Streamer::read_u8()",
    "kind": "unknown",
    "line": 219,
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
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
   "control_structures": "IF:226,IF:228,FOR:235,IF:236,IF:238,IF:246,ELSE:250,IF:250,SWITCH:252,BREAK:255,BREAK:258,BREAK:261",
   "fn": "flb_sds_cat_utf8",
   "guard_count": 3,
   "guards": "ret == 0 | state != FLB_UTF8_ACCEPT | cp > 0xFFFF",
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
   "code": "ret = flb_utf8_decode(&state, &cp, *p) | flb_utf8_decode(&state, &cp, *p) | &state | &cp",
   "site": {
    "file": "/src/fluent-bit/src/flb_sds.c",
    "fn": "flb_sds_cat_utf8",
    "line": 291
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/src/flb_sds.c",
    "line": 213,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "ret",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_6fe5d030bcee.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/6fe5d030bcee43556fb1c6054f55854c605a5b0c/ARVO-42490229/report.log",
   "testcase_size": 512
  },
  "input_reachability": [
   "str",
   "str_len"
  ],
  "osv_id": "ARVO-42490229",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "ret = flb_utf8_decode(&state, &cp, *p) | flb_utf8_decode(&state, &cp, *p) | &state | &cp",
    "fn": "flb_sds_cat_utf8",
    "kind": "unknown",
    "line": 291,
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
   "entity_type": "int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "realloc",
   "cross_function": true,
   "site": {
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "fn": "flb_realloc",
    "line": 91
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
   "control_structures": "IF:1098,IF:1103,IF:1106,IF:1132,IF:1137,IF:1141,WHILE:1152,IF:1154,IF:1161,IF:1175,IF:1176,BREAK:1177",
   "fn": "flb_http_do",
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
    "width": 1
   },
   "code": "c->header_buf[c->header_len++] = '\\r' | c->header_buf[c->header_len++] | c->header_buf | c->header_len++",
   "site": {
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "fn": "flb_http_do",
    "line": 1114
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "line": 1084,
    "size": null,
    "type": "flb_http_client*"
   },
   "kind": "pointer",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9da96a3b8885.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9da96a3b88859ae57134c6932cab65101114e3b4/ARVO-42490266/report.log",
   "testcase_size": 1898
  },
  "input_reachability": [
   "c"
  ],
  "osv_id": "ARVO-42490266",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "c->header_buf[c->header_len++] = '\\r' | c->header_buf[c->header_len++] | c->header_buf | c->header_len++",
    "fn": "flb_http_do",
    "kind": "unknown",
    "line": 1114,
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
   "entity_type": "flb_http_client*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "fn": "flb_malloc",
    "line": 62
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
   "control_structures": "IF:254,IF:260,IF:272,IF:288,IF:293,IF:306,IF:316,IF:320,IF:344,IF:352,GOTO:353",
   "fn": "process_chunked_data",
   "guard_count": 4,
   "guards": "val == LONG_MAX | val == LONG_MIN | val == 0",
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
   "code": "p[val -2] != '\\r' || p[val - 1] != '\\n' | p[val -2] != '\\r' | p[val -2] | val -2",
   "site": {
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "fn": "process_chunked_data",
    "line": 293
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/src/flb_http_client.c",
    "line": 248,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "p",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_9da96a3b8885.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/9da96a3b88859ae57134c6932cab65101114e3b4/ARVO-42490276/report.log",
   "testcase_size": 162
  },
  "input_reachability": [
   "c"
  ],
  "osv_id": "ARVO-42490276",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "p[val -2] != '\\r' || p[val - 1] != '\\n' | p[val -2] != '\\r' | p[val -2] | val -2",
    "fn": "process_chunked_data",
    "kind": "unknown",
    "line": 293,
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
   "entity_type": "char*",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
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
   "control_structures": "IF:2398,SWITCH:2410,IF:2414,DO:2416,WHILE:2416,DO:2416,GOTO:2416,DO:2417,WHILE:2417,DO:2417,GOTO:2417,IF:2419",
   "fn": "tinfl_decompress",
   "guard_count": 66,
   "guards": "pIn_buf_cur >= pIn_buf_end | pIn_buf_cur >= pIn_buf_end | num_bits < (mz_uint)(3)",
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
   "code": "TINFL_GET_BITS(3, r->m_final, 3) | r->m_final | num_bits < (mz_uint)(3) | (mz_uint)(3)",
   "site": {
    "file": "/src/fluent-bit/lib/miniz/miniz.c",
    "fn": "tinfl_decompress",
    "line": 2429
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/lib/miniz/miniz.c",
    "line": 2381,
    "size": null,
    "type": "tinfl_decompressor*"
   },
   "kind": "pointer",
   "name": "r",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_72b62d2270ed.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/72b62d2270edda9a0281ff8a6c3903d99e1892c9/ARVO-42490298/report.log",
   "testcase_size": 600
  },
  "input_reachability": [
   "r",
   "pIn_buf_next",
   "pIn_buf_size",
   "pOut_buf_start",
   "pOut_buf_next",
   "pOut_buf_size",
   "decomp_flags"
  ],
  "osv_id": "ARVO-42490298",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "TINFL_GET_BITS(3, r->m_final, 3) | r->m_final | num_bits < (mz_uint)(3) | (mz_uint)(3)",
    "fn": "tinfl_decompress",
    "kind": "unknown",
    "line": 2429,
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
   "entity_type": "tinfl_decompressor*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/cryptofuzz-sp-math-all/util.cpp",
    "fn": "cryptofuzz::util::malloc(unsigned long)",
    "line": 346
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
   "fn": null,
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
    "width": 1
   },
   "code": null,
   "site": {
    "file": null,
    "fn": null,
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_4280861af059.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/4280861af059e4781cbe8012613a7f4d1786f9e1/ARVO-42491082/report.log",
   "testcase_size": 540
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491082",
  "project": "wolfssl",
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
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "alloc",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": null,
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
    "file": null,
    "fn": null,
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
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_c482d160290c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/wolfssl/address/c482d160290c5cf314a3b10eba621dd37b6795a1/ARVO-42491208/report.log",
   "testcase_size": 127
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491208",
  "project": "wolfssl",
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
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/serenity/Meta/Lagom/build/../../../AK/ByteBuffer.h",
    "fn": "AK::ByteBufferImpl::ByteBufferImpl(void const*, unsigned long)",
    "line": 252
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
   "fn": "double_hash",
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
   "code": "key ^= (key >> 20) | key >> 20",
   "site": {
    "file": "/src/serenity/Libraries/LibTTF/Font.cpp",
    "fn": "TTF::be_u16(unsigned char const*)",
    "line": 48
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/serenity/Libraries/LibTTF/Font.cpp",
    "line": 42,
    "size": null,
    "type": "u32"
   },
   "kind": "struct",
   "name": "key",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_df5ea97c51e6.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/serenity/address/df5ea97c51e63f84ce30e8db9d8617b035e2ac38/ARVO-42491468/report.log",
   "testcase_size": 16
  },
  "input_reachability": [
   "key"
  ],
  "osv_id": "ARVO-42491468",
  "project": "serenity",
  "sites": [
   {
    "code": "key ^= (key >> 20) | key >> 20",
    "fn": "TTF::be_u16(unsigned char const*)",
    "kind": "unknown",
    "line": 48,
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
   "entity_type": "u32",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
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
   "fn": "ZSTD_initDDict_internal",
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
    "width": 117791
   },
   "code": null,
   "site": {
    "file": "/src/c-blosc2/internal-complibs/zstd-1.4.5/decompress/zstd_ddict.c",
    "fn": "ZSTD_initDDict_internal",
    "line": 134
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
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_474ebf151be8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/474ebf151be847186e6bc2c1381a8f7d4beff4dd/ARVO-42491502/report.log",
   "testcase_size": 27249
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491502",
  "project": "c-blosc2",
  "sites": [
   {
    "code": null,
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
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "line": 72
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
   "fn": "<clinit>",
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
    "width": 16
   },
   "code": "DECODER_OPTION_END_OF_STREAM = 1",
   "site": {
    "file": "/src/openh264/codec/decoder/core/src/mv_pred.cpp",
    "fn": "WelsDec::CopyRectBlock4Cols(void*, void*, int, int, int, int)",
    "line": 152
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "DECODER_OPTION_END_OF_STREAM",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_992c1c147175.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openh264/address/992c1c147175126c3fe7ab78216aa0395f9e6c71/ARVO-42491572/report.log",
   "testcase_size": 339
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491572",
  "project": "openh264",
  "sites": [
   {
    "code": "DECODER_OPTION_END_OF_STREAM = 1",
    "fn": "WelsDec::CopyRectBlock4Cols(void*, void*, int, int, int, int)",
    "kind": "unknown",
    "line": 152,
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
    "file": "/build/hdf5-3JSo9x/hdf5-1.8.16+docs/debian/build/src/../../../src/H5FL.c",
    "fn": "H5FL_malloc",
    "line": 199
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
   "fn": "Mat_LogInitFunc",
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
    "width": 129
   },
   "code": "silent  = 0",
   "site": {
    "file": "/src/matio/src/mat73.c",
    "fn": "Mat_H5ReadVarInfo",
    "line": 477
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "silent",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_a47b7cd3aca7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/a47b7cd3aca70e9a0bddf8146eb4ab0cbd19c2c3/ARVO-42491640/report.log",
   "testcase_size": 48243
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491640",
  "project": "matio",
  "sites": [
   {
    "code": "silent  = 0",
    "fn": "Mat_H5ReadVarInfo",
    "kind": "unknown",
    "line": 477,
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
    "file": "/src/hdf5-1.12.0/src/H5MM.c",
    "fn": "H5MM_malloc",
    "line": 292
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
   "fn": "Mat_H5ReadVarInfo",
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
    "file": "/src/matio/src/mat73.c",
    "fn": "Mat_H5ReadVarInfo",
    "line": 483
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
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_1ce8f2d1845e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/1ce8f2d1845ecdde19a35605cabdbb884776d52d/ARVO-42491649/report.log",
   "testcase_size": 71761
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491649",
  "project": "matio",
  "sites": [
   {
    "code": null,
    "fn": "Mat_H5ReadVarInfo",
    "kind": "unknown",
    "line": 483,
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
    "file": "/src/hdf5-1.12.0/src/H5MM.c",
    "fn": "H5MM_malloc",
    "line": 292
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
   "control_structures": "IF:366,IF:375,ELSE:377,IF:377,IF:385,IF:392,IF:396,IF:399,IF:401,IF:403,ELSE:409,IF:409",
   "fn": "getopt_internal",
   "guard_count": 1,
   "guards": "place != nargv[optind]",
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
   "code": "place = EMSG | EMSG",
   "site": {
    "file": "/src/matio/src/mat73.c",
    "fn": "Mat_H5ReadVarInfo",
    "line": 534
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": "pointer",
   "name": "place",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_1ce8f2d1845e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/1ce8f2d1845ecdde19a35605cabdbb884776d52d/ARVO-42491667/report.log",
   "testcase_size": 33657
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491667",
  "project": "matio",
  "sites": [
   {
    "code": "place = EMSG | EMSG",
    "fn": "Mat_H5ReadVarInfo",
    "kind": "unknown",
    "line": 534,
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