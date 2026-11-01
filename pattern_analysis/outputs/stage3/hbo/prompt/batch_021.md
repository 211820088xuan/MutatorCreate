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
    "file": null,
    "fn": "g_malloc0 (/out/thumbnail_fuzzer+0x3bc8b50)",
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
   "fn": "vips_rect_intersectrect",
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
    "file": "/src/libvips/libvips/iofuncs/rect.c",
    "fn": "vips_rect_intersectrect",
    "line": 181
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42509256/report.log",
   "testcase_size": 79
  },
  "input_reachability": [],
  "osv_id": "ARVO-42509256",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "vips_rect_intersectrect",
    "kind": "unknown",
    "line": 181,
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
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_file_new",
    "line": 619
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
   "control_structures": "IF:1324,IF:1334,IF:1340,IF:1341,IF:1345",
   "fn": "do_fileid",
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
    "width": 2
   },
   "code": "memcpy(path->value + path->len, temp.value, 2) | path->value + path->len | path->value | path->len",
   "site": {
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "fn": "do_fileid",
    "line": 1351
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "line": 1322,
    "size": null,
    "type": "sc_path*"
   },
   "kind": "pointer",
   "name": "path",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509342/report.log",
   "testcase_size": 50863
  },
  "input_reachability": [],
  "osv_id": "ARVO-42509342",
  "project": "opensc",
  "sites": [
   {
    "code": "memcpy(path->value + path->len, temp.value, 2) | path->value + path->len | path->value | path->len",
    "fn": "do_fileid",
    "kind": "unknown",
    "line": 1351,
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
   "entity_type": "sc_path*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "alloc",
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1219,IF:1224,ELSE:1226,IF:1226,IF:1227,ELSE:1233,IF:1233,IF:1234,ELSE:1240,IF:1240,IF:1241,ELSE:1247",
   "fn": "new_file",
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
    "width": 8
   },
   "code": "profile->df[df_type] = file | profile->df[df_type] | profile->df",
   "site": {
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "fn": "new_file",
    "line": 1254
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/pkcs15init/profile.c",
    "line": 1214,
    "size": null,
    "type": "sc_profile_t*"
   },
   "kind": "pointer",
   "name": "profile",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509477/report.log",
   "testcase_size": 5989
  },
  "input_reachability": [
   "cur"
  ],
  "osv_id": "ARVO-42509477",
  "project": "opensc",
  "sites": [
   {
    "code": "profile->df[df_type] = file | profile->df[df_type] | profile->df",
    "fn": "new_file",
    "kind": "unknown",
    "line": 1254,
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
   "entity_type": "sc_profile_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_file_new",
    "line": 619
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
   "control_structures": "DO:314,WHILE:317,SWITCH:318,BREAK:323,BREAK:328,BREAK:333,BREAK:338,BREAK:342,BREAK:346,BREAK:350,IF:352,BREAK:353",
   "fn": "cosm_new_file",
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
   "code": "file->path.value[file->path.len - 1] = (num & 0xFF) | file->path.value[file->path.len - 1] | file->path.value | file->path",
   "site": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-epass2003.c",
    "fn": "cosm_new_file",
    "line": 379
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-epass2003.c",
    "line": 310,
    "size": null,
    "type": "sc_file*"
   },
   "kind": "pointer",
   "name": "file",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42509978/report.log",
   "testcase_size": 14971
  },
  "input_reachability": [
   "num"
  ],
  "osv_id": "ARVO-42509978",
  "project": "opensc",
  "sites": [
   {
    "code": "file->path.value[file->path.len - 1] = (num & 0xFF) | file->path.value[file->path.len - 1] | file->path.value | file->path",
    "fn": "cosm_new_file",
    "kind": "unknown",
    "line": 379,
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
   "entity_type": "sc_file*",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": {
   "api": "malloc",
   "cross_function": true,
   "site": {
    "file": "/src/fluent-bit/include/fluent-bit/flb_mem.h",
    "fn": "flb_malloc",
    "line": 56
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
   "fn": "onig_node_str_cat",
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
    "width": 3
   },
   "code": null,
   "site": {
    "file": "/src/fluent-bit/lib/onigmo/regparse.c",
    "fn": "onig_node_str_cat",
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
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_dbe29a1a77b5.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42510029/report.log",
   "testcase_size": 724
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510029",
  "project": "fluent-bit",
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
    "file": "/src/fluent-bit/lib/onigmo/regparse.c",
    "fn": "node_new",
    "line": 1125
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
   "control_structures": "DO:289,IF:289,DO:289,DO:289,IF:289,IF:289",
   "fn": "add_bytes",
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
   "code": "BBUF_ADD(reg, bytes, len) | int | ((reg)->used) + (int)((len)) | (reg)->used",
   "site": {
    "file": "/src/fluent-bit/lib/onigmo/regcomp.c",
    "fn": "add_bytes",
    "line": 289
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/lib/onigmo/regcomp.c",
    "line": 287,
    "size": null,
    "type": "regex_t*"
   },
   "kind": "pointer",
   "name": "reg",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_dbe29a1a77b5.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/fluent-bit/address/dbe29a1a77b544b9e1b39e9b32e151ac22c6874e/ARVO-42510070/report.log",
   "testcase_size": 1024
  },
  "input_reachability": [
   "reg",
   "bytes",
   "len"
  ],
  "osv_id": "ARVO-42510070",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "BBUF_ADD(reg, bytes, len) | int | ((reg)->used) + (int)((len)) | (reg)->used",
    "fn": "add_bytes",
    "kind": "unknown",
    "line": 289,
    "origin": "report:crash"
   },
   {
    "code": "realloc((((reg)))->p, (((reg)))->alloc)",
    "fn": "add_bytes",
    "kind": "realloc",
    "line": 289,
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
   "entity_type": "regex_t*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libjxl/lib/jxl/base/cache_aligned.cc",
    "fn": "jxl::CacheAligned::Allocate(unsigned long, unsigned long)",
    "line": 87
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
   "fn": "vips_foreign_load_jxl_process",
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
    "width": 64
   },
   "code": null,
   "site": {
    "file": "/src/libvips/libvips/foreign/jxlload.c",
    "fn": "vips_foreign_load_jxl_process",
    "line": 380
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libvips/address/unknown/ARVO-42510312/report.log",
   "testcase_size": 857
  },
  "input_reachability": [],
  "osv_id": "ARVO-42510312",
  "project": "libvips",
  "sites": [
   {
    "code": null,
    "fn": "vips_foreign_load_jxl_process",
    "kind": "unknown",
    "line": 380,
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
    "file": "/src/qtbase/src/gui/image/qimage.cpp",
    "fn": "QImageData::create(QSize const&, QImage::Format)",
    "line": 164
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
   "control_structures": "IF:546,IF:549,IF:552,IF:557",
   "fn": "capabilities",
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
    "width": 2
   },
   "code": "device->isReadable() && ANIHandler::canRead(device) | device->isReadable() | ANIHandler::canRead(device)",
   "site": {
    "file": "/src/kimageformats/src/imageformats/psd.cpp",
    "fn": "void (anonymous namespace)::planarToChunchy<unsigned short>(unsigned char*, char const*, int, int, int)",
    "line": 557
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/kimageformats/src/imageformats/psd.cpp",
    "line": 544,
    "size": null,
    "type": "QIODevice*"
   },
   "kind": "pointer",
   "name": "device",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_98f19c60aed4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/kimageformats/address/98f19c60aed45e81cad631825c212005889b459b/ARVO-42510459/report.log",
   "testcase_size": 52
  },
  "input_reachability": [
   "device"
  ],
  "osv_id": "ARVO-42510459",
  "project": "kimageformats",
  "sites": [
   {
    "code": "device->isReadable() && ANIHandler::canRead(device) | device->isReadable() | ANIHandler::canRead(device)",
    "fn": "void (anonymous namespace)::planarToChunchy<unsigned short>(unsigned char*, char const*, int, int, int)",
    "kind": "unknown",
    "line": 557,
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
   "entity_type": "QIODevice*",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x240b2)",
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
   "control_structures": "IF:1268,IF:1276,IF:1279,IF:1285,IF:1290,FOR:1296,IF:1298,IF:1301,IF:1311,IF:1323,IF:1326,IF:1332",
   "fn": "get_meta_from_header",
   "guard_count": 1,
   "guards": "content_len < 0",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 2147483647
   },
   "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
   "site": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "fn": "get_meta_from_header",
    "line": 1363
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/c-blosc2/blosc/frame.c",
    "line": 1362,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "content",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_5f5213c23cc8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/5f5213c23cc8608537b234e93ee5dae31a77aaff/ARVO-42510485/report.log",
   "testcase_size": 100
  },
  "input_reachability": [
   "header",
   "header_len"
  ],
  "osv_id": "ARVO-42510485",
  "project": "c-blosc2",
  "sites": [
   {
    "code": "calloc(sizeof(blosc2_metalayer), 1)",
    "fn": "get_meta_from_header",
    "kind": "calloc",
    "line": 1304,
    "origin": "cpg"
   },
   {
    "code": "malloc((size_t)nslen + 1)",
    "fn": "get_meta_from_header",
    "kind": "malloc",
    "line": 1314,
    "origin": "cpg"
   },
   {
    "code": "malloc((size_t)content_len)",
    "fn": "get_meta_from_header",
    "kind": "malloc",
    "line": 1362,
    "origin": "cpg"
   },
   {
    "code": "memcpy(content, content_marker + 1 + 4, (size_t)content_ | content_marker + 1 + 4 | content_marker + 1 | (size_t)content_len",
    "fn": "get_meta_from_header",
    "kind": "unknown",
    "line": 1363,
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
    "file": "/src/ndpi/fuzz/fuzz_ndpi_reader.c",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 85
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
   "control_structures": "IF:35,IF:36,IF:49,ELSE:64,IF:64,IF:65,IF:66,SWITCH:74,IF:77,WHILE:79,IF:80,BREAK:85",
   "fn": "ndpi_check_tinc",
   "guard_count": 1,
   "guards": "i < payload_len",
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
   "code": "(packet_payload[i] >= '0' && packet_payload[i] <= '9') | | packet_payload[i] >= '0' && packet_payload[i] <= '9' | packet_payload[i] >= '0' | packet_payload[i]",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/tinc.c",
    "fn": "ndpi_check_tinc",
    "line": 105
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/tinc.c",
    "line": 32,
    "size": null,
    "type": "u_int8_t*"
   },
   "kind": "pointer",
   "name": "packet_payload",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_a6029d250d9c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/a6029d250d9c5dd0d7346fe47de838c243c20cac/ARVO-42510527/report.log",
   "testcase_size": 230
  },
  "input_reachability": [
   "flow"
  ],
  "osv_id": "ARVO-42510527",
  "project": "ndpi",
  "sites": [
   {
    "code": "(packet_payload[i] >= '0' && packet_payload[i] <= '9') | | packet_payload[i] >= '0' && packet_payload[i] <= '9' | packet_payload[i] >= '0' | packet_payload[i]",
    "fn": "ndpi_check_tinc",
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
   "entity_type": "u_int8_t*",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x240b2)",
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
   "control_structures": "IF:14,WHILE:17,SWITCH:18,DO:20,DO:21,DO:22,DO:23,BREAK:24,IF:27,IF:33,BREAK:36,IF:42",
   "fn": "dump",
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
    "width": 8
   },
   "code": "printf(\"Error: %s\\n\", error)",
   "site": {
    "file": "/src/lwan/src/lib/lwan-h2-huffman.c",
    "fn": "read64be",
    "line": 43
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lwan/src/lib/lwan-h2-huffman.c",
    "line": 40,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "error",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_0e9355a0aac9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/lwan/address/0e9355a0aac992fe321abcc5b547602306fe4343/ARVO-42510536/report.log",
   "testcase_size": 6
  },
  "input_reachability": [
   "config"
  ],
  "osv_id": "ARVO-42510536",
  "project": "lwan",
  "sites": [
   {
    "code": "printf(\"Error: %s\\n\", error)",
    "fn": "read64be",
    "kind": "unknown",
    "line": 43,
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
   "api": "new",
   "cross_function": true,
   "site": {
    "file": "/src/opensc/src/libopensc/sc.c",
    "fn": "sc_file_new",
    "line": 619
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
   "control_structures": "DO:580,DO:593,IF:593,IF:595,ELSE:600,IF:600,ELSE:605,IF:608,DO:612,IF:612,DO:616,IF:616",
   "fn": "sc_pkcs15init_delete_by_path",
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
   "code": "path.value[0] = file_path->value[file_path->len - 2] | path.value[0] | path.value | file_path->value[file_path->len - 2]",
   "site": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "fn": "sc_pkcs15init_delete_by_path",
    "line": 628
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/pkcs15init/pkcs15-lib.c",
    "line": 576,
    "size": null,
    "type": "sc_path"
   },
   "kind": "struct",
   "name": "path",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_3d1acdf7d82e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/3d1acdf7d82eb2c532b525cc8d9229d6d0bdf72c/ARVO-42510699/report.log",
   "testcase_size": 130885
  },
  "input_reachability": [
   "p15card",
   "file_path"
  ],
  "osv_id": "ARVO-42510699",
  "project": "opensc",
  "sites": [
   {
    "code": "path.value[0] = file_path->value[file_path->len - 2] | path.value[0] | path.value | file_path->value[file_path->len - 2]",
    "fn": "sc_pkcs15init_delete_by_path",
    "kind": "unknown",
    "line": 628,
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
   "entity_type": "sc_path",
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
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x240b2)",
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
   "control_structures": "FOR:211",
   "fn": "strncpy_lower",
   "guard_count": 1,
   "guards": "i < dst_len",
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
   "code": "strncpy(dst, src, dst_len)",
   "site": {
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "fn": "strncpy_lower",
    "line": 208
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/kerberos.c",
    "line": 203,
    "size": null,
    "type": "char*const"
   },
   "kind": "struct",
   "name": "dst",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_06a0abb6fdf8.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/06a0abb6fdf8fb7a446ef5aafdf2c7d24608977f/ARVO-42510718/report.log",
   "testcase_size": 158
  },
  "input_reachability": [
   "dst",
   "dst_siz",
   "src",
   "src_siz"
  ],
  "osv_id": "ARVO-42510718",
  "project": "ndpi",
  "sites": [
   {
    "code": "strncpy(dst, src, dst_len)",
    "fn": "strncpy_lower",
    "kind": "unknown",
    "line": 208,
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
   "entity_type": "char*const",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libredwg/src/decode.c",
    "fn": "decode_preR13",
    "line": 728
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
   "control_structures": "IF:280,IF:284,IF:286,IF:286",
   "fn": "decode_preR13_section_hdr",
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
   "code": "tbl->size = bit_read_RS (dat) | tbl->size | bit_read_RS (dat)",
   "site": {
    "file": "/src/libredwg/src/decode.c",
    "fn": "decode_preR13_section_hdr",
    "line": 274
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/decode.c",
    "line": 273,
    "size": null,
    "type": "Dwg_Section*"
   },
   "kind": "pointer",
   "name": "tbl",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_fc96e7e65dd7.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/fc96e7e65dd763ed20eae58ead3f0a1f686bb51f/ARVO-42511065/report.log",
   "testcase_size": 58
  },
  "input_reachability": [
   "id",
   "dat"
  ],
  "osv_id": "ARVO-42511065",
  "project": "libredwg",
  "sites": [
   {
    "code": "tbl->size = bit_read_RS (dat) | tbl->size | bit_read_RS (dat)",
    "fn": "decode_preR13_section_hdr",
    "kind": "unknown",
    "line": 274,
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
   "entity_type": "Dwg_Section*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "cross_function": true,
   "site": {
    "file": "/src/libredwg/src/./dwg.spec",
    "fn": "dwg_setup_LAYOUT",
    "line": 4677
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
   "control_structures": "IF:9,IF:11,IF:11,ELSE:11,ELSE:11,IF:11,ELSE:11,IF:37,IF:37,ELSE:37,FOR:37,IF:37",
   "fn": "json_common_entity_data",
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
    "width": 8
   },
   "code": "_obj->next_entity | !(dat->opts & 0x20) | dat->opts & 0x20 | dat->opts",
   "site": {
    "file": "/src/libredwg/src/common_entity_handle_data.spec",
    "fn": "json_common_entity_data",
    "line": 73
   }
  },
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libredwg/src/common_entity_handle_data.spec",
    "line": 1114,
    "size": null,
    "type": "Dwg_Object_Entity*"
   },
   "kind": "pointer",
   "name": "_obj",
   "storage": "heap"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_a7c2bd168507.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/a7c2bd168507d426036003f26cad7e603c7a1045/ARVO-42511372/report.log",
   "testcase_size": 2048
  },
  "input_reachability": [
   "dat"
  ],
  "osv_id": "ARVO-42511372",
  "project": "libredwg",
  "sites": [
   {
    "code": "_obj->next_entity | !(dat->opts & 0x20) | dat->opts & 0x20 | dat->opts",
    "fn": "json_common_entity_data",
    "kind": "unknown",
    "line": 73,
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
   "entity_type": "Dwg_Object_Entity*",
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