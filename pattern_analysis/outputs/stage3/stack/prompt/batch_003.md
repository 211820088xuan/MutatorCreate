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
stack-buffer-overflow

## 该类型的机制背景
stack-BOF 的必要条件链：
- N1 对象是函数内栈数组
- N2 数组声明维度
- N3 访问宽度
- N4 是否 VLA（char buf[n]，n 来自输入）
- N5 数组所在栈帧
- N6 写入形式：memcpy 还是逐字节循环
- N7 栈增长方向 + 覆盖对象
- N8 是否经由 alloca / 变长分配

## 样本（共 15 条，完整 facts + interpretation）

[
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1253,IF:1255,IF:1256,IF:1260,SWITCH:1261,BREAK:1264,IF:1266,IF:1267,IF:1274,IF:1278,BREAK:1280,IF:1282",
   "fn": "xmlSnprintfElementContent",
   "guard_count": 1,
   "guards": "content == NULL",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 37
   },
   "code": "strcat(buf, (char *) content->name) | (char *) content->name | content->name",
   "site": {
    "file": "/src/libxml2/valid.c",
    "fn": "xmlSnprintfElementContent",
    "line": 1279
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/libxml2/valid.c",
    "line": 1250,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "buf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_e905f08123e4.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/libxml2/address/e905f08123e4a6e7731549e6f09dadff4cab65bd/ARVO-42480782/report.log",
   "testcase_size": 2889
  },
  "input_reachability": [
   "buf",
   "content"
  ],
  "osv_id": "ARVO-42480782",
  "project": "libxml2",
  "sites": [
   {
    "code": "strcat(buf, (char *) content->name) | (char *) content->name | content->name",
    "fn": "xmlSnprintfElementContent",
    "kind": "unknown",
    "line": 1279,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:2502,WHILE:2503,IF:2505,IF:2508,IF:2510,ELSE:2513,WHILE:2516,IF:2517,IF:2518,GOTO:2524,IF:2526,BREAK:2526",
   "fn": "mrb_str_len_to_dbl",
   "guard_count": 2,
   "guards": "c == '_' | n == buf",
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
   "code": "*n++ = c | *n++ | n++",
   "site": {
    "file": "/src/mruby/src/string.c",
    "fn": "mrb_str_len_to_dbl",
    "line": 2542
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/mruby/src/string.c",
    "line": 2498,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "n",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_afad93917349.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/mruby/address/afad9391734998df4f76a6f7108278d2aa2599a0/ARVO-42480985/report.log",
   "testcase_size": 156
  },
  "input_reachability": [],
  "osv_id": "ARVO-42480985",
  "project": "mruby",
  "sites": [
   {
    "code": "*n++ = c | *n++ | n++",
    "fn": "mrb_str_len_to_dbl",
    "kind": "unknown",
    "line": 2542,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "control_structures": "WHILE:265,IF:273,IF:286,IF:291,BREAK:293",
   "fn": "utilsFlashWrite",
   "guard_count": 1,
   "guards": "written < aSize",
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
   "code": "*data    = aData + written | aData + written",
   "site": {
    "file": "/src/openthread/src/core/common/tlvs.hpp",
    "fn": "ot::ExtendedTlv::GetLength() const",
    "line": 268
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/common/tlvs.hpp",
    "line": 268,
    "size": null,
    "type": "uint8_t*"
   },
   "kind": "pointer",
   "name": "data",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_1f2bed8e7d73.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/1f2bed8e7d73daa057ebb24f785ff88b8315c922/ARVO-42481955/report.log",
   "testcase_size": 844
  },
  "input_reachability": [
   "aAddress",
   "aData",
   "aSize"
  ],
  "osv_id": "ARVO-42481955",
  "project": "openthread",
  "sites": [
   {
    "code": "*data    = aData + written | aData + written",
    "fn": "ot::ExtendedTlv::GetLength() const",
    "kind": "unknown",
    "line": 268,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "uint8_t*",
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
   "fn": "tvb_get_ipv4_addr_with_prefix_len",
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
    "file": "/src/wireshark/epan/addr_and_mask.c",
    "fn": "tvb_get_ipv4_addr_with_prefix_len",
    "line": 59
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wireshark_2bdff1df4928.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wireshark/address/2bdff1df49282cf0959b841789095cd5813ea214/ARVO-42483000/report.log",
   "testcase_size": 219
  },
  "input_reachability": [],
  "osv_id": "ARVO-42483000",
  "project": "wireshark",
  "sites": [
   {
    "code": null,
    "fn": "tvb_get_ipv4_addr_with_prefix_len",
    "kind": "unknown",
    "line": 59,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "control_structures": "DO:1683,IF:1700,GOTO:1702,IF:1708,IF:1721,GOTO:1722,IF:1727,GOTO:1728,IF:1733,IF:1742,GOTO:1743,IF:1745",
   "fn": "coolkey_rsa_op",
   "guard_count": 2,
   "guards": "(out_length) < (max_out_len) | (out_length) < (max_out_len)",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 36864
   },
   "code": "memcpy(out, buf+2, out_length) | buf+2",
   "site": {
    "file": "/src/opensc/src/libopensc/card-coolkey.c",
    "fn": "coolkey_rsa_op",
    "line": 1764
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-coolkey.c",
    "line": 1669,
    "size": null,
    "type": "u8*"
   },
   "kind": "pointer",
   "name": "out",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_31169afb7252.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/31169afb7252f58a2db2b365835f6166f9d4b6c9/ARVO-42483752/report.log",
   "testcase_size": 1517
  },
  "input_reachability": [
   "out",
   "max_out_len"
  ],
  "osv_id": "ARVO-42483752",
  "project": "opensc",
  "sites": [
   {
    "code": "memcpy(out, buf+2, out_length) | buf+2",
    "fn": "coolkey_rsa_op",
    "kind": "unknown",
    "line": 1764,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "u8*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:1136,IF:1137,IF:1138,IF:1139,IF:1140,IF:1142,IF:1147",
   "fn": "fmt_setup",
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
   "code": "*buf++ = c | *buf++ | buf++",
   "site": {
    "file": "/src/mruby/mrbgems/mruby-sprintf/src/sprintf.c",
    "fn": "fmt_setup",
    "line": 1153
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-sprintf/src/sprintf.c",
    "line": 1130,
    "size": null,
    "type": "char*"
   },
   "kind": "pointer",
   "name": "buf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_7add524041df.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/mruby/address/7add524041df0f2482e587ec1a3920c6f34624a4/ARVO-42483880/report.log",
   "testcase_size": 40
  },
  "input_reachability": [
   "buf",
   "size",
   "c",
   "width",
   "prec"
  ],
  "osv_id": "ARVO-42483880",
  "project": "mruby",
  "sites": [
   {
    "code": "*buf++ = c | *buf++ | buf++",
    "fn": "fmt_setup",
    "kind": "unknown",
    "line": 1153,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "char*",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "DO:613,DO:629,IF:629,IF:631,IF:634,WHILE:635,DO:639,IF:639,ELSE:639,DO:641,IF:641,ELSE:641",
   "fn": "tcos_decipher",
   "guard_count": 2,
   "guards": "crgram != NULL | crgram_len>255",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 52545
   },
   "code": "memcpy(sbuf+1, crgram, crgram_len) | sbuf+1",
   "site": {
    "file": "/src/opensc/src/libopensc/card-tcos.c",
    "fn": "tcos_decipher",
    "line": 626
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/card-tcos.c",
    "line": 604,
    "size": null,
    "type": "u8[261]"
   },
   "kind": "array",
   "name": "sbuf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_797414be0522.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/797414be05220fa371972606d7a6c2e94dd6d8db/ARVO-42484390/report.log",
   "testcase_size": 68675
  },
  "input_reachability": [
   "card",
   "crgram",
   "crgram_len"
  ],
  "osv_id": "ARVO-42484390",
  "project": "opensc",
  "sites": [
   {
    "code": "memcpy(sbuf+1, crgram, crgram_len) | sbuf+1",
    "fn": "tcos_decipher",
    "kind": "unknown",
    "line": 626,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "u8[261]",
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
   "control_structures": "DO:426,IF:427,IF:435,DO:436,IF:436,DO:452,IF:460,DO:467,IF:467,IF:472,IF:480,BREAK:481",
   "fn": "sc_get_response",
   "guard_count": 1,
   "guards": "buflen < le",
   "in_loop": true,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "WRITE",
    "region_bytes": null,
    "width": 28
   },
   "code": "memcpy(buf, resp, le)",
   "site": {
    "file": "/src/opensc/src/libopensc/apdu.c",
    "fn": "sc_get_response",
    "line": 475
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/apdu.c",
    "line": 423,
    "size": null,
    "type": "unsigned char*"
   },
   "kind": "pointer",
   "name": "buf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b02da8348be9.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/b02da8348be97d4b24081783f6af46757373bc3e/ARVO-42487756/report.log",
   "testcase_size": 66395
  },
  "input_reachability": [
   "card",
   "apdu",
   "olen"
  ],
  "osv_id": "ARVO-42487756",
  "project": "opensc",
  "sites": [
   {
    "code": "memcpy(buf, resp, le)",
    "fn": "sc_get_response",
    "kind": "unknown",
    "line": 475,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "unsigned char*",
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
   "control_structures": "IF:125,IF:127",
   "fn": "flb_sds_cat",
   "guard_count": 1,
   "guards": "avail < len",
   "in_loop": false,
   "loop_range": null,
   "loop_type": null
  },
  "crash": {
   "access": {
    "dir": "READ",
    "region_bytes": null,
    "width": 313
   },
   "code": "memcpy((char *) (s + flb_sds_len(s)), str, len) | (char *) (s + flb_sds_len(s)) | s + flb_sds_len(s) | flb_sds_len(s)",
   "site": {
    "file": "/src/fluent-bit/src/flb_sds.c",
    "fn": "flb_sds_cat",
    "line": 132
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/fluent-bit/src/flb_sds.c",
    "line": 118,
    "size": null,
    "type": "flb_sds_t"
   },
   "kind": "struct",
   "name": "s",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/fluent-bit_6fe5d030bcee.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/fluent-bit/address/6fe5d030bcee43556fb1c6054f55854c605a5b0c/ARVO-42488023/report.log",
   "testcase_size": 512
  },
  "input_reachability": [
   "s",
   "str",
   "len"
  ],
  "osv_id": "ARVO-42488023",
  "project": "fluent-bit",
  "sites": [
   {
    "code": "memcpy((char *) (s + flb_sds_len(s)), str, len) | (char *) (s + flb_sds_len(s)) | s + flb_sds_len(s) | flb_sds_len(s)",
    "fn": "flb_sds_cat",
    "kind": "unknown",
    "line": 132,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "flb_sds_t",
   "is_signed": null,
   "ptr_origin": "param"
  }
 },
 {
  "alloc": null,
  "call_chain": [],
  "completeness": [
   "call_chain"
  ],
  "context": {
   "control_structures": "IF:125,IF:128,IF:130,WHILE:138,IF:140,CONTINUE:140,FOR:141,IF:142,IF:144,BREAK:144,IF:146,FOR:150",
   "fn": "insert_key",
   "guard_count": 3,
   "guards": "i<buf[1]+2 | buf[i+2]==key_reference | i<r",
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
   "code": "buf[i]==0x83 && buf[i+1]==1 && buf[i+2]==key_reference | buf[i]==0x83 && buf[i+1]==1 | buf[i]==0x83 | buf[i]",
   "site": {
    "file": "/src/opensc/src/libopensc/pkcs15-tcos.c",
    "fn": "insert_key",
    "line": 142
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-tcos.c",
    "line": 126,
    "size": null,
    "type": "unsigned char[256]"
   },
   "kind": "array",
   "name": "buf",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_797414be0522.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/opensc/address/797414be05220fa371972606d7a6c2e94dd6d8db/ARVO-42489404/report.log",
   "testcase_size": 1218
  },
  "input_reachability": [
   "key_reference"
  ],
  "osv_id": "ARVO-42489404",
  "project": "opensc",
  "sites": [
   {
    "code": "buf[i]==0x83 && buf[i+1]==1 && buf[i+2]==key_reference | buf[i]==0x83 && buf[i+1]==1 | buf[i]==0x83 | buf[i]",
    "fn": "insert_key",
    "kind": "unknown",
    "line": 142,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "unsigned char[256]",
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
    "width": 8
   },
   "code": null,
   "site": {
    "file": null,
    "fn": null,
    "line": null
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/wolfssl_2d79e3843686.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/wolfssl/address/2d79e3843686f498db28e3a406a87e389eb0749b/ARVO-42489610/report.log",
   "testcase_size": 4154
  },
  "input_reachability": [],
  "osv_id": "ARVO-42489610",
  "project": "wolfssl",
  "sites": [],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "fn": "otPlatRadioGetTransmitPower",
   "guard_count": 1,
   "guards": "aPower != NULL",
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
   "code": "otEXPECT_ACTION(aPower != NULL, error = OT_ERROR_INVALID | aPower != NULL | error = OT_ERROR_INVALID_ARGS",
   "site": {
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "fn": "ot::MeshCoP::ChannelMaskEntryBase::GetEntrySize() const",
    "line": 1298
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/openthread/src/core/meshcop/meshcop_tlvs.hpp",
    "line": 1292,
    "size": null,
    "type": "int8_t*"
   },
   "kind": "pointer",
   "name": "aPower",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_82eee1f8d329.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/82eee1f8d32980279ba5b9b63f53609325d910fb/ARVO-42490332/report.log",
   "testcase_size": 255
  },
  "input_reachability": [
   "aPower"
  ],
  "osv_id": "ARVO-42490332",
  "project": "openthread",
  "sites": [
   {
    "code": "otEXPECT_ACTION(aPower != NULL, error = OT_ERROR_INVALID | aPower != NULL | error = OT_ERROR_INVALID_ARGS",
    "fn": "ot::MeshCoP::ChannelMaskEntryBase::GetEntrySize() const",
    "kind": "unknown",
    "line": 1298,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "int8_t*",
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
    "region_bytes": null,
    "width": 1
   },
   "code": "{-18, 0x06c9} | -18",
   "site": {
    "file": "/src/openthread/src/core/common/string.cpp",
    "fn": "ot::IsValidUtf8String(char const*, unsigned long)",
    "line": 92
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/openthread_0d14e854398c.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/openthread/address/0d14e854398cd9eced31666e48e6ab656e574074/ARVO-42490739/report.log",
   "testcase_size": 51
  },
  "input_reachability": [],
  "osv_id": "ARVO-42490739",
  "project": "openthread",
  "sites": [
   {
    "code": "{-18, 0x06c9} | -18",
    "fn": "ot::IsValidUtf8String(char const*, unsigned long)",
    "kind": "unknown",
    "line": 92,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "fn": "Lookup",
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
   "code": "base::StringView()",
   "site": {
    "file": "/src/perfetto/src/trace_processor/importers/proto/memory_tracker_snapshot_parser.cc",
    "fn": "perfetto::trace_processor::MemoryTrackerSnapshotParser::EmitRows(long, perfetto::trace_processor::GlobalNodeGraph&, perfetto::trace_processor::LevelOfDetail)",
    "line": 211
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": null,
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_f37338cdaa21.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/perfetto/address/f37338cdaa2126eef2a11e1a6f0cb075888c20e6/ARVO-42490832/report.log",
   "testcase_size": 140
  },
  "input_reachability": [],
  "osv_id": "ARVO-42490832",
  "project": "perfetto",
  "sites": [
   {
    "code": "base::StringView()",
    "fn": "perfetto::trace_processor::MemoryTrackerSnapshotParser::EmitRows(long, perfetto::trace_processor::GlobalNodeGraph&, perfetto::trace_processor::LevelOfDetail)",
    "kind": "unknown",
    "line": 211,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
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
   "control_structures": "FOR:129",
   "fn": "encode_base64",
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
   "code": "output.append(out2)",
   "site": {
    "file": "/src/serenity/Libraries/LibJS/Heap/Heap.cpp",
    "fn": "JS::Heap::gather_conservative_roots(AK::HashTable<JS::Cell*, AK::Traits<JS::Cell*> >&)",
    "line": 149
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/serenity/Libraries/LibJS/Heap/Heap.cpp",
    "line": 118,
    "size": null,
    "type": "StringBuilder"
   },
   "kind": "struct",
   "name": "output",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/serenity_370ce4243005.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/stack-buffer-overflow/serenity/address/370ce4243005fb123ae1a13177b486c377ce2d6d/ARVO-42491388/report.log",
   "testcase_size": 4
  },
  "input_reachability": [],
  "osv_id": "ARVO-42491388",
  "project": "serenity",
  "sites": [
   {
    "code": "output.append(out2)",
    "fn": "JS::Heap::gather_conservative_roots(AK::HashTable<JS::Cell*, AK::Traits<JS::Cell*> >&)",
    "kind": "unknown",
    "line": 149,
    "origin": "report:crash"
   }
  ],
  "type_reconciliation": {
   "diverged": false,
   "ledger_crash_type": "stack-buffer-overflow",
   "report_fault_kind": "stack-buffer-overflow",
   "used": "stack-buffer-overflow"
  },
  "types": {
   "cast_present": null,
   "entity_type": "StringBuilder",
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