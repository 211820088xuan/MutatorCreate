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
global-buffer-overflow

## 该类型的机制背景
global-BOF 的必要条件链：
- N1 访问对象是全局数组/表
- N2 访问宽度
- N3 下标表达式及其来源
- N4 常量表 vs 可变全局缓冲区
- N5 下标是单字节还是多字节
- N6 表长是否是 2 的幂（256/512）
- N7 同一输入索引是否访问多个全局表

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "dissect_ber_choice",
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
    "file": "/src/wireshark/epan/dissectors/packet-ber.c",
    "fn": "dissect_ber_choice",
    "line": 2954
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_e0239089525e.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/wireshark/address/e0239089525e904e3f11206f6296addf138a9125/ARVO-42479779/report.log",
   "testcase_size": 106
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479779",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "dissect_ber_choice",
    "kind": "unknown",
    "line": 2954,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "types.entity_type",
   "call_chain"
  ],
  "context": {
   "fn": "LLVMFuzzerTestOneInput",
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
   "code": "",
   "site": {
    "file": "/src/lwan/src/bin/fuzz/template_fuzzer.cc",
    "fn": "LLVMFuzzerTestOneInput",
    "line": 63
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lwan_f905fa80d71d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lwan/address/f905fa80d71d6a0f6d773938f39e3f9d7558d537/ARVO-42479969/report.log",
   "testcase_size": 32768
  },
  "input_reachability": [],
  "osv_id": "ARVO-42479969",
  "project": "lwan",
  "sites": [
   {
    "code": "",
    "fn": "LLVMFuzzerTestOneInput",
    "kind": "unknown",
    "line": 63,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "wassp_match_strval",
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
    "file": "/src/wireshark/epan/dissectors/packet-wassp.c",
    "fn": "wassp_match_strval",
    "line": 4384
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_b7cb793fdf71.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/wireshark/address/b7cb793fdf71ae9eef132a50e7a3560db1dffbf0/ARVO-42481100/report.log",
   "testcase_size": 196
  },
  "input_reachability": [],
  "osv_id": "ARVO-42481100",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "wassp_match_strval",
    "kind": "unknown",
    "line": 4384,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
    "width": 1
   },
   "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
   "site": {
    "file": "/src/harfbuzz/src/hb-array.hh",
    "fn": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "line": 220
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_fd85818b5b85.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/harfbuzz/address/fd85818b5b85fb0ad2db71c60e94ca0689d38bca/ARVO-42481452/report.log",
   "testcase_size": 98811
  },
  "input_reachability": [],
  "osv_id": "ARVO-42481452",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "HB_AAT_LAYOUT_FEATURE_SELECTOR_PI_CHARACTERS\t\t\t= 2",
    "fn": "hb_array_t<OT::IntType<unsigned char, 1u> const> hb_array_t<OT::IntType<unsigned char, 1u> const>::copy<hb_serialize_context_t>(hb_serialize_context_t*) const",
    "kind": "unknown",
    "line": 220,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "call_chain"
  ],
  "context": {
   "control_structures": "WHILE:453,IF:455,IF:476,GOTO:477,IF:478,GOTO:479,IF:491,GOTO:492,SWITCH:494,BREAK:501,IF:506,BREAK:511",
   "fn": "_hb_buffer_deserialize_glyphs_json",
   "guard_count": 4,
   "guards": "p < pe | p < pe | p == pe",
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
   "code": "!parse_int  (tok, p, &pos.y_offset ) | parse_int  (tok, p, &pos.y_offset ) | &pos.y_offset | pos.y_offset",
   "site": {
    "file": "/src/harfbuzz/src/hb.hh",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "line": 541
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb.hh",
    "line": 460,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "tok",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_818f109bdec9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/harfbuzz/address/818f109bdec9659c05f9fd9a1de1db85ece65cbe/ARVO-42483059/report.log",
   "testcase_size": 87807
  },
  "input_reachability": [
   "buffer",
   "buf",
   "buf_len",
   "font"
  ],
  "osv_id": "ARVO-42483059",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "!parse_int  (tok, p, &pos.y_offset ) | parse_int  (tok, p, &pos.y_offset ) | &pos.y_offset | pos.y_offset",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "unknown",
    "line": 541,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "OT::VarData::get_scalars(int const*, unsigned int, OT::VarRegionList const&, float*, unsigned int) const",
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
    "width": 4
   },
   "code": null,
   "site": {
    "file": "/src/harfbuzz/src/hb-ot-layout-common.hh",
    "fn": "OT::VarData::get_scalars(int const*, unsigned int, OT::VarRegionList const&, float*, unsigned int) const",
    "line": 2302
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_48ad74599615.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/harfbuzz/address/48ad745996159337fb4733561e834a0ffbe3a1ae/ARVO-42486098/report.log",
   "testcase_size": 2707
  },
  "input_reachability": [],
  "osv_id": "ARVO-42486098",
  "project": "harfbuzz",
  "sites": [
   {
    "code": null,
    "fn": "OT::VarData::get_scalars(int const*, unsigned int, OT::VarRegionList const&, float*, unsigned int) const",
    "kind": "unknown",
    "line": 2302,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:378,IF:381",
   "fn": "<",
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
   "code": "!string.is_null() | string.is_null()",
   "site": {
    "file": "/src/serenity/Libraries/LibGfx/GIFLoader.cpp",
    "fn": "Gfx::decode_frame(Gfx::GIFLoadingContext&, unsigned long)",
    "line": 379
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/serenity/Libraries/LibGfx/GIFLoader.cpp",
    "line": 376,
    "size": null,
    "type": "String&"
   },
   "kind": "struct",
   "name": "string",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_3565d3c60c43.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/serenity/address/3565d3c60c43d29f35f309063de6b6a5dc70929a/ARVO-42490247/report.log",
   "testcase_size": 673
  },
  "input_reachability": [
   "string"
  ],
  "osv_id": "ARVO-42490247",
  "project": "serenity",
  "sites": [
   {
    "code": "!string.is_null() | string.is_null()",
    "fn": "Gfx::decode_frame(Gfx::GIFLoadingContext&, unsigned long)",
    "kind": "unknown",
    "line": 379,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "String&",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "entity.decl",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "IsLetterGroup",
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
    "file": "/src/espeak-ng/src/libespeak-ng/dictionary.c",
    "fn": "IsLetterGroup",
    "line": 714
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0a713d52bbf3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/espeak-ng/address/0a713d52bbf3e061823d1a7f35e5303e7320f27a/ARVO-42497197/report.log",
   "testcase_size": 1900
  },
  "input_reachability": [],
  "osv_id": "ARVO-42497197",
  "project": "espeak-ng",
  "sites": [
   {
    "code": null,
    "fn": "IsLetterGroup",
    "kind": "unknown",
    "line": 714,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "DoEmbedded2",
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
    "file": "/src/espeak-ng/src/libespeak-ng/setlengths.c",
    "fn": "DoEmbedded2",
    "line": 427
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0a713d52bbf3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/espeak-ng/address/0a713d52bbf3e061823d1a7f35e5303e7320f27a/ARVO-42497446/report.log",
   "testcase_size": 780
  },
  "input_reachability": [],
  "osv_id": "ARVO-42497446",
  "project": "espeak-ng",
  "sites": [
   {
    "code": null,
    "fn": "DoEmbedded2",
    "kind": "unknown",
    "line": 427,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "SubstitutePhonemes",
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
    "width": 2
   },
   "code": null,
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/phonemelist.c",
    "fn": "SubstitutePhonemes",
    "line": 75
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_0a713d52bbf3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/espeak-ng/address/0a713d52bbf3e061823d1a7f35e5303e7320f27a/ARVO-42497478/report.log",
   "testcase_size": 972
  },
  "input_reachability": [],
  "osv_id": "ARVO-42497478",
  "project": "espeak-ng",
  "sites": [
   {
    "code": null,
    "fn": "SubstitutePhonemes",
    "kind": "unknown",
    "line": 75,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
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
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:388",
   "fn": "StringAppend",
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
    "width": 102399999
   },
   "code": "memcpy(new_ptr, s->begin, s->len) | s->begin | s->len",
   "site": {
    "file": "/src/lcms/src/cmscgats.c",
    "fn": "StringAppend",
    "line": 394
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/lcms/src/cmscgats.c",
    "line": 390,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "new_ptr",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/lcms_1c667a762c42.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/lcms/address/1c667a762c4272ec970a2dd6f945836c52f35720/ARVO-42505785/report.log",
   "testcase_size": 10
  },
  "input_reachability": [
   "s",
   "c"
  ],
  "osv_id": "ARVO-42505785",
  "project": "lcms",
  "sites": [
   {
    "code": "memcpy(new_ptr, s->begin, s->len) | s->begin | s->len",
    "fn": "StringAppend",
    "kind": "unknown",
    "line": 394,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
   "is_signed": null,
   "ptr_origin": "assignment"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:362,IF:363,IF:370,TRY:375,IF:387,IF:388,ELSE:391,ELSE:395,IF:395,IF:396,ELSE:399,ELSE:403",
   "fn": "ensureDecoder",
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
   "code": "img = handle.decode_image(heif_colorspace_RGB, chroma) | handle.decode_image(heif_colorspace_RGB, chroma)",
   "site": {
    "file": "/src/kimageformats/src/imageformats/heif.cpp",
    "fn": "HEIFHandler::ensureDecoder()",
    "line": 413
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/kimageformats/src/imageformats/heif.cpp",
    "line": 413,
    "size": null,
    "type": "heif.Image"
   },
   "kind": "struct",
   "name": "img",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/kimageformats_43543f96bc45.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/kimageformats/address/43543f96bc45732a55aca2aa073d6d26ef57821c/ARVO-42515438/report.log",
   "testcase_size": 2849
  },
  "input_reachability": [],
  "osv_id": "ARVO-42515438",
  "project": "kimageformats",
  "sites": [
   {
    "code": "img = handle.decode_image(heif_colorspace_RGB, chroma) | handle.decode_image(heif_colorspace_RGB, chroma)",
    "fn": "HEIFHandler::ensureDecoder()",
    "kind": "unknown",
    "line": 413,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "heif.Image",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:89,SWITCH:95,BREAK:99,BREAK:105,SWITCH:108,FOR:119,FOR:124,BREAK:133,FOR:140,FOR:143,BREAK:151,FOR:156",
   "fn": "BM_Font",
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
   "code": "hb_set_next (set, &u) | &u",
   "site": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "line": 120
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/harfbuzz/src/hb-algs.hh",
    "line": 112,
    "size": null,
    "type": "hb_set_t*"
   },
   "kind": "pointer",
   "name": "set",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/harfbuzz_7327006d686c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/harfbuzz/address/7327006d686c149cefdc7ee6047d2b426ac1ac75/ARVO-42521970/report.log",
   "testcase_size": 133057
  },
  "input_reachability": [],
  "osv_id": "ARVO-42521970",
  "project": "harfbuzz",
  "sites": [
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "calloc",
    "line": 115,
    "origin": "cpg"
   },
   {
    "code": "calloc (pop, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "calloc",
    "line": 116,
    "origin": "cpg"
   },
   {
    "code": "hb_set_next (set, &u) | &u",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "unknown",
    "line": 120,
    "origin": "report:crash"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "calloc",
    "line": 137,
    "origin": "cpg"
   },
   {
    "code": "calloc (num_glyphs, sizeof (hb_codepoint_t))",
    "fn": "BEInt<unsigned short, 2>::operator unsigned short() const",
    "kind": "calloc",
    "line": 138,
    "origin": "cpg"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "hb_set_t*",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:370,IF:376,IF:397,IF:400,IF:421,IF:441,IF:446,WHILE:463,IF:468,ELSE:471,IF:472,ELSE:475",
   "fn": "xmlSAX2ExternalSubset",
   "guard_count": 2,
   "guards": "buffered > ULONG_MAX - consumed | consumed > ULONG_MAX - ctxt->sizeentities",
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
   "code": "consumed += buffered",
   "site": {
    "file": "/src/libxml2/HTMLparser.c",
    "fn": "htmlCurrentChar",
    "line": 471
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/HTMLparser.c",
    "line": 391,
    "size": null,
    "type": "long unsigned"
   },
   "kind": "struct",
   "name": "consumed",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_42322eba8200.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/42322eba820022eaebb9b6e7c083a8aadddea286/ARVO-42522151/report.log",
   "testcase_size": 2105
  },
  "input_reachability": [
   "ctx",
   "ExternalID",
   "SystemID"
  ],
  "osv_id": "ARVO-42522151",
  "project": "libxml2",
  "sites": [
   {
    "code": "consumed += buffered",
    "fn": "htmlCurrentChar",
    "kind": "unknown",
    "line": 471,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "long unsigned",
   "is_signed": null,
   "ptr_origin": "unknown"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:449,IF:453,IF:460,IF:464,IF:474,ELSE:477,IF:493,IF:494,GOTO:495,IF:496,IF:500,GOTO:501",
   "fn": "xmlNextChar",
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
   "code": "(cur[1] & 0xc0) != 0x80 | cur[1] & 0xc0 | cur[1]",
   "site": {
    "file": "/src/libxml2/parserInternals.c",
    "fn": "xmlNextChar",
    "line": 500
   }
  },
  "crash_type": "global-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/parserInternals.c",
    "line": 465,
    "size": null,
    "type": "unsigned char*"
   },
   "kind": "pointer",
   "name": "cur",
   "storage": "global"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_5f4ec41baee4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/global-buffer-overflow/libxml2/address/5f4ec41baee40819beefe0c52eaa06ec144938bd/ARVO-42522273/report.log",
   "testcase_size": 27
  },
  "input_reachability": [],
  "osv_id": "ARVO-42522273",
  "project": "libxml2",
  "sites": [
   {
    "code": "(cur[1] & 0xc0) != 0x80 | cur[1] & 0xc0 | cur[1]",
    "fn": "xmlNextChar",
    "kind": "unknown",
    "line": 500,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "global-buffer-overflow",
   "report_fault_kind": "global-buffer-overflow",
   "used": "global-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "unsigned char*",
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