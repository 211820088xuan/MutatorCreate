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
   "api": "unknown:interceptor_skipped",
   "cross_function": false,
   "site": {
    "file": "/src/matio/src/mat73.c",
    "fn": "Mat_H5ReadDatasetInfo",
    "line": 673
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
   "fn": "Mat_H5ReadDatasetInfo",
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
    "width": 400
   },
   "code": null,
   "site": {
    "file": "/src/matio/src/mat73.c",
    "fn": "Mat_H5ReadDatasetInfo",
    "line": 674
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
   "cpg": "/root/gyx/mutator_create/cpg_files/matio_92e9a90b02cb.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/92e9a90b02cb3af869d86de1a1428b4bd9e6e7a5/ARVO-42491698/report.log",
   "testcase_size": 27460
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491698",
  "project": "matio",
  "sites": [
   {
    "code": null,
    "fn": "Mat_H5ReadDatasetInfo",
    "kind": "unknown",
    "line": 674,
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
   "fn": "blosc_getitem",
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
    "file": "/src/c-blosc2/blosc/blosc2.c",
    "fn": "blosc_getitem",
    "line": 2404
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/474ebf151be847186e6bc2c1381a8f7d4beff4dd/ARVO-42491774/report.log",
   "testcase_size": 89
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491774",
  "project": "c-blosc2",
  "sites": [
   {
    "code": null,
    "fn": "blosc_getitem",
    "kind": "unknown",
    "line": 2404,
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
   "fn": "Mat_Open",
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
    "file": "/src/matio/src/mat.c",
    "fn": "Mat_Open",
    "line": 583
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/matio/address/1ce8f2d1845ecdde19a35605cabdbb884776d52d/ARVO-42491954/report.log",
   "testcase_size": 5609
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491954",
  "project": "matio",
  "sites": [
   {
    "code": "",
    "fn": "Mat_Open",
    "kind": "unknown",
    "line": 583,
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
    "fn": "cram_read_block",
    "line": 1445
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
   "control_structures": "IF:921,IF:924,IF:933,IF:934,IF:936,IF:941,FOR:946,IF:951,IF:960,IF:970,FOR:974,IF:976",
   "fn": "arith_uncompress_to",
   "guard_count": 4,
   "guards": "i < N | c_meta_len > in_size | i < N",
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
   "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "fn": "arith_uncompress_to",
    "line": 931
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "line": 931,
    "size": null,
    "type": "unsigned int"
   },
   "kind": "struct",
   "name": "N",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42491972/report.log",
   "testcase_size": 138
  },
  "free_related": {
   "free_sites_in_func": [
    978,
    984,
    992
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "input_reachability": [
   "in",
   "in_size"
  ],
  "osv_id": "ARVO-42491972",
  "project": "htslib",
  "sites": [
   {
    "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
    "fn": "arith_uncompress_to",
    "kind": "unknown",
    "line": 931,
    "origin": "report:crash"
   },
   {
    "code": "malloc(ulen)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 936,
    "origin": "cpg"
   },
   {
    "code": "malloc(ulen)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 969,
    "origin": "cpg"
   },
   {
    "code": "free(outN)",
    "fn": "arith_uncompress_to",
    "kind": "free",
    "line": 978,
    "origin": "cpg"
   },
   {
    "code": "free(outN)",
    "fn": "arith_uncompress_to",
    "kind": "free",
    "line": 984,
    "origin": "cpg"
   },
   {
    "code": "free(outN)",
    "fn": "arith_uncompress_to",
    "kind": "free",
    "line": 992,
    "origin": "cpg"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 1028,
    "origin": "cpg"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "arith_uncompress_to",
    "kind": "malloc",
    "line": 1051,
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
   "entity_type": "unsigned int",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/htslib/cram/cram_io.c",
    "fn": "cram_read_block",
    "line": 1445
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
   "control_structures": "IF:1526,IF:1529,IF:1538,IF:1539,IF:1541,IF:1546,FOR:1551,IF:1556,IF:1565,IF:1575,FOR:1579,IF:1581",
   "fn": "rans_uncompress_to_4x16",
   "guard_count": 4,
   "guards": "i < N | c_meta_len > in_size | i < N",
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
   "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/rANS_static4x16pr.c",
    "fn": "rans_uncompress_to_4x16",
    "line": 1536
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/rANS_static4x16pr.c",
    "line": 1536,
    "size": null,
    "type": "unsigned int"
   },
   "kind": "struct",
   "name": "N",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42491975/report.log",
   "testcase_size": 207
  },
  "free_related": {
   "free_sites_in_func": [
    1583,
    1589,
    1597
   ],
   "reassign_between": false,
   "reassign_sites": [],
   "remalloc_between": false
  },
  "input_reachability": [
   "in",
   "in_size"
  ],
  "osv_id": "ARVO-42491975",
  "project": "htslib",
  "sites": [
   {
    "code": "N = in[c_meta_len++] | in[c_meta_len++] | c_meta_len++",
    "fn": "rans_uncompress_to_4x16",
    "kind": "unknown",
    "line": 1536,
    "origin": "report:crash"
   },
   {
    "code": "malloc(ulen)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1541,
    "origin": "cpg"
   },
   {
    "code": "malloc(ulen)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1574,
    "origin": "cpg"
   },
   {
    "code": "free(outN)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "free",
    "line": 1583,
    "origin": "cpg"
   },
   {
    "code": "free(outN)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "free",
    "line": 1589,
    "origin": "cpg"
   },
   {
    "code": "free(outN)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "free",
    "line": 1597,
    "origin": "cpg"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1628,
    "origin": "cpg"
   },
   {
    "code": "malloc(*out_size)",
    "fn": "rans_uncompress_to_4x16",
    "kind": "malloc",
    "line": 1666,
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
   "entity_type": "unsigned int",
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
   "control_structures": "IF:43,ELSE:46",
   "fn": "sw32_",
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
   "code": "idest = *(int32_t *)pa | *(int32_t *)pa | (int32_t *)pa",
   "site": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "fn": "sw32_",
    "line": 44
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": 40,
    "size": null,
    "type": "int32_t"
   },
   "kind": "struct",
   "name": "idest",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_aebf2b985836.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/aebf2b9858368681e497f136501ab33cc1014aed/ARVO-42491999/report.log",
   "testcase_size": 89
  },
  "input_reachability": [
   "pa"
  ],
  "osv_id": "ARVO-42491999",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "idest = *(int32_t *)pa | *(int32_t *)pa | (int32_t *)pa",
    "fn": "sw32_",
    "kind": "unknown",
    "line": 44,
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
   "entity_type": "int32_t",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/leptonica/src/pix1.c",
    "fn": "pixdata_malloc",
    "line": 247
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
   "control_structures": "FOR:5763,FOR:5766",
   "fn": "fdilate_1_56",
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
    "width": 4
   },
   "code": "*dptr = ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) < | *dptr | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) | | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) |",
   "site": {
    "file": "/src/leptonica/src/fmorphgenlow.1.c",
    "fn": "fdilate_1_56",
    "line": 5767
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/leptonica/src/fmorphgenlow.1.c",
    "line": 5757,
    "size": null,
    "type": "l_uint32*"
   },
   "kind": "pointer",
   "name": "dptr",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_0665ff28f9e9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/0665ff28f9e9df91565ee09438a30d47232ad2eb/ARVO-42492002/report.log",
   "testcase_size": 540
  },
  "input_reachability": [
   "datad",
   "h",
   "wpld",
   "datas",
   "wpls"
  ],
  "osv_id": "ARVO-42492002",
  "project": "leptonica",
  "sites": [
   {
    "code": "*dptr = ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) < | *dptr | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) | | ((*(sptr + wpls2) >> 2) | (*(sptr + wpls2 - 1) << 30)) |",
    "fn": "fdilate_1_56",
    "kind": "unknown",
    "line": 5767,
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
   "entity_type": "l_uint32*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": false,
   "site": {
    "file": "/src/htslib/cram/cram_codecs.c",
    "fn": "cram_xpack_decode_init",
    "line": 1391
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
   "control_structures": "IF:1391,IF:1395,ELSE:1397,IF:1397,ELSE:1399,IF:1399,ELSE:1401,FOR:1412,IF:1414,IF:1420,GOTO:1421,IF:1424",
   "fn": "cram_xpack_decode_init",
   "guard_count": 2,
   "guards": "i < c->u.xpack.nval | v >= 256",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 4
   },
   "code": "c->u.xpack.rmap[i] = v | c->u.xpack.rmap[i] | c->u.xpack.rmap | c->u.xpack",
   "site": {
    "file": "/src/htslib/cram/cram_codecs.c",
    "fn": "cram_xpack_decode_init",
    "line": 1415
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/cram/cram_codecs.c",
    "line": 1387,
    "size": null,
    "type": "cram_codec*"
   },
   "kind": "pointer",
   "name": "c",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492011/report.log",
   "testcase_size": 91
  },
  "input_reachability": [
   "data",
   "size"
  ],
  "osv_id": "ARVO-42492011",
  "project": "htslib",
  "sites": [
   {
    "code": "malloc(sizeof(*c))",
    "fn": "cram_xpack_decode_init",
    "kind": "malloc",
    "line": 1391,
    "origin": "cpg"
   },
   {
    "code": "c->u.xpack.rmap[i] = v | c->u.xpack.rmap[i] | c->u.xpack.rmap | c->u.xpack",
    "fn": "cram_xpack_decode_init",
    "kind": "unknown",
    "line": 1415,
    "origin": "report:crash"
   },
   {
    "code": "free(c)",
    "fn": "cram_xpack_decode_init",
    "kind": "free",
    "line": 1432,
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
   "entity_type": "cram_codec*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/htslib/cram/cram_io.c",
    "fn": "cram_read_block",
    "line": 1433
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
   "control_structures": "IF:671,IF:673,IF:677,ELSE:680,IF:680,ELSE:684,IF:684,ELSE:689,IF:689,ELSE:695,IF:695,ELSE:702",
   "fn": "safe_ltf8_get",
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
   "code": "(uint64_t)up[5]<<24 | (uint64_t)up[5] | up[5]",
   "site": {
    "file": "/src/htslib/cram/cram_io.c",
    "fn": "safe_ltf8_get",
    "line": 734
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/cram/cram_io.c",
    "line": 669,
    "size": null,
    "type": "unsigned char*"
   },
   "kind": "pointer",
   "name": "up",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492022/report.log",
   "testcase_size": 90
  },
  "input_reachability": [],
  "osv_id": "ARVO-42492022",
  "project": "htslib",
  "sites": [
   {
    "code": "(uint64_t)up[5]<<24 | (uint64_t)up[5] | up[5]",
    "fn": "safe_ltf8_get",
    "kind": "unknown",
    "line": 734,
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
   "entity_type": "unsigned char*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/fqzcomp_qual.c",
    "fn": "uncompress_block_fqz2f",
    "line": 1338
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
   "control_structures": "IF:1025",
   "fn": "int32_get_blk",
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
   "code": "((uint32_t) b->data[b->byte+1]) <<  8 | (uint32_t) b->data[b->byte+1] | b->data[b->byte+1] | b->data",
   "site": {
    "file": "/src/htslib/cram/cram_io.c",
    "fn": "int32_get_blk",
    "line": 1030
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/cram/cram_io.c",
    "line": 1024,
    "size": null,
    "type": "cram_block*"
   },
   "kind": "pointer",
   "name": "b",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492042/report.log",
   "testcase_size": 128
  },
  "input_reachability": [
   "b"
  ],
  "osv_id": "ARVO-42492042",
  "project": "htslib",
  "sites": [
   {
    "code": "((uint32_t) b->data[b->byte+1]) <<  8 | (uint32_t) b->data[b->byte+1] | b->data[b->byte+1] | b->data",
    "fn": "int32_get_blk",
    "kind": "unknown",
    "line": 1030,
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
   "entity_type": "cram_block*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/fqzcomp_qual.c",
    "fn": "uncompress_block_fqz2f",
    "line": 1338
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
   "control_structures": "IF:642,IF:644,IF:648,ELSE:651,IF:651,ELSE:654,IF:654,ELSE:657,IF:657,ELSE:661",
   "fn": "safe_itf8_get",
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
   "code": "((up[0] <<8) |  up[1])                           & 0x3ff | (up[0] <<8) |  up[1] | up[0] <<8 | up[0]",
   "site": {
    "file": "/src/htslib/cram/cram_io.c",
    "fn": "safe_itf8_get",
    "line": 653
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/cram/cram_io.c",
    "line": 640,
    "size": null,
    "type": "unsigned char*"
   },
   "kind": "pointer",
   "name": "up",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492101/report.log",
   "testcase_size": 58
  },
  "input_reachability": [],
  "osv_id": "ARVO-42492101",
  "project": "htslib",
  "sites": [
   {
    "code": "((up[0] <<8) |  up[1])                           & 0x3ff | (up[0] <<8) |  up[1] | up[0] <<8 | up[0]",
    "fn": "safe_itf8_get",
    "kind": "unknown",
    "line": 653,
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
   "entity_type": "unsigned char*",
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
   "control_structures": "IF:1056,DO:1057,IF:1057,BREAK:1057,IF:1061,DO:1062,IF:1062,BREAK:1062,IF:1065,DO:1066,IF:1066,BREAK:1066",
   "fn": "frame_get_usermeta",
   "guard_count": 3,
   "guards": "trailer_offset < 0 | usermeta_len < 0 | usermeta_len == 0",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 538976288
   },
   "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "frame_get_usermeta",
    "line": 1108
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1047,
    "size": null,
    "type": "uint8_t**"
   },
   "kind": "pointer",
   "name": "usermeta",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_aebf2b985836.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/aebf2b9858368681e497f136501ab33cc1014aed/ARVO-42492173/report.log",
   "testcase_size": 89
  },
  "input_reachability": [
   "frame",
   "usermeta"
  ],
  "osv_id": "ARVO-42492173",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
    "fn": "frame_get_usermeta",
    "kind": "malloc",
    "line": 1078,
    "origin": "cpg"
   },
   {
    "code": "malloc(usermeta_len)",
    "fn": "frame_get_usermeta",
    "kind": "malloc",
    "line": 1106,
    "origin": "cpg"
   },
   {
    "code": "memcpy(*usermeta, frame->sdata + trailer_offset + FRAME_ | *usermeta | frame->sdata + trailer_offset + FRAME_TRAILER_USERMETA_O | frame->sdata + trailer_offset",
    "fn": "frame_get_usermeta",
    "kind": "unknown",
    "line": 1108,
    "origin": "report:crash"
   },
   {
    "code": "malloc(strlen(frame->urlpath) + strlen(\"/chunks.b2frame\") + 1)",
    "fn": "frame_get_usermeta",
    "kind": "malloc",
    "line": 1113,
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
   "entity_type": "uint8_t**",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "fn": "arith_uncompress_to",
    "line": 969
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
   "control_structures": "SWITCH:878,WHILE:880,FOR:881,WHILE:884,FOR:885,BREAK:888,WHILE:891,FOR:892,WHILE:895,FOR:896,BREAK:899,WHILE:903",
   "fn": "unstripe",
   "guard_count": 12,
   "guards": "j < ulen-4 | k < 4 | j < ulen",
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
   "code": "out[j++] = outN[idxN[k]++] | out[j++] | j++ | outN[idxN[k]++]",
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "fn": "unstripe",
    "line": 905
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/arith_dynamic.c",
    "line": 873,
    "size": null,
    "type": "unsigned char*"
   },
   "kind": "pointer",
   "name": "out",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492301/report.log",
   "testcase_size": 267
  },
  "input_reachability": [
   "out",
   "outN",
   "ulen",
   "N",
   "idxN"
  ],
  "osv_id": "ARVO-42492301",
  "project": "htslib",
  "sites": [
   {
    "code": "out[j++] = outN[idxN[k]++] | out[j++] | j++ | outN[idxN[k]++]",
    "fn": "unstripe",
    "kind": "unknown",
    "line": 905,
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
   "entity_type": "unsigned char*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "fn": "sc_oberthur_read_file",
    "line": 264
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
   "control_structures": "DO:849,DO:857,IF:857,IF:859,DO:860,IF:860,IF:865,DO:866,IF:866,IF:869,IF:874,DO:875",
   "fn": "sc_pkcs15emu_oberthur_add_data",
   "guard_count": 1,
   "guards": "label_len > sizeof(dobj.label) - 1",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 254
   },
   "code": "memcpy(dobj.label, label, label_len) | dobj.label",
   "site": {
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "fn": "sc_pkcs15emu_oberthur_add_data",
    "line": 898
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-oberthur.c",
    "line": 842,
    "size": null,
    "type": "sc_pkcs15_object"
   },
   "kind": "struct",
   "name": "dobj",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_978c912c7089.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/978c912c7089fa4573add7140170feb9fcbe7f87/ARVO-42492330/report.log",
   "testcase_size": 2328
  },
  "input_reachability": [],
  "osv_id": "ARVO-42492330",
  "project": "opensc",
  "sites": [
   {
    "code": "memcpy(dobj.label, label, label_len) | dobj.label",
    "fn": "sc_pkcs15emu_oberthur_add_data",
    "kind": "unknown",
    "line": 898,
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
   "entity_type": "sc_pkcs15_object",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/rANS_static4x16pr.c",
    "fn": "rans_uncompress_to_4x16",
    "line": 1628
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
   "control_structures": "FOR:155,WHILE:161,IF:162,GOTO:163,IF:166,ELSE:168,IF:171,IF:172,GOTO:173,ELSE:176",
   "fn": "rle_decode",
   "guard_count": 1,
   "guards": "outp >= out_end",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 111
   },
   "code": "memset(outp, b, rlen+1) | rlen+1",
   "site": {
    "file": "/src/htslib/htscodecs/htscodecs/rle.c",
    "fn": "rle_decode",
    "line": 174
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/htslib/htscodecs/htscodecs/rle.c",
    "line": 160,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "outp",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_01830d77854b.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/01830d77854bf24d69959373d2570c640c1ff5d2/ARVO-42492643/report.log",
   "testcase_size": 383
  },
  "input_reachability": [
   "out"
  ],
  "osv_id": "ARVO-42492643",
  "project": "htslib",
  "sites": [
   {
    "code": "memset(outp, b, rlen+1) | rlen+1",
    "fn": "rle_decode",
    "kind": "unknown",
    "line": 174,
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