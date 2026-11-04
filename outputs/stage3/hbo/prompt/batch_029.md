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
  "osv_id": "ARVO-42527353",
  "project": "ntopng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "payload",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ntopng/src/Flow.cpp",
    "line": 6160,
    "size": null,
    "type": "u_int8_t*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pcap_check_header",
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "line": 405
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "64",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 6166,
    "fn": "Flow::dissectNetBIOS(unsigned char*, unsigned short)",
    "code": "((payload[2] & 0x80) /* NetBIOS Response */ ||",
    "origin": "report:crash"
   },
   {
    "code": "strdup(name)",
    "fn": "Flow::dissectNetBIOS(unsigned char*, unsigned short)",
    "kind": "strdup",
    "line": 6196,
    "origin": "cpg",
    "args": "name"
   }
  ],
  "crash": {
   "site": {
    "fn": "Flow::dissectNetBIOS(unsigned char*, unsigned short)",
    "file": "/src/ntopng/src/Flow.cpp",
    "line": 6166
   },
   "code": "((payload[2] & 0x80) /* NetBIOS Response */ ||",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dissectNetBIOS",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:6164,IF:6166,IF:6172,WHILE:6176,IF:6182,ELSE:6186,IF:6196"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int8_t*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "payload",
   "payload_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42527353/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "testcase_size": 180
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_legend_size": 0,
   "dedup_token": "Flow::dissectNetBIOS(unsigned char*, unsigned short)--NetworkInterface::processPacket(unsigned int, bool, timeval const*, unsigned long, ndpi_ethhdr*, unsigned "
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 6160,
    "type": "u_int8_t*"
   },
   "entity_name_cpg": "payload",
   "func_lines": [
    6160,
    6198
   ],
   "func_params": {
    "names": [
     "this",
     "payload",
     "payload_len"
    ],
    "types": [
     "Flow",
     "u_int8_t*",
     "u_int16_t"
    ]
   },
   "guards": [
    {
     "code": "(payload[2] & 0x78) == 0x28",
     "line": 6167
    },
    {
     "code": "ndpi_netbios_name_interpret((u_char *)&payload[12], payload_len - 12,",
     "line": 6169
    },
    {
     "code": "name[0] == '*'",
     "line": 6172
    },
    {
     "code": "payload_len - 57 > (int)sizeof (name) - 1",
     "line": 6173
    },
    {
     "code": "i < limit",
     "line": 6176
    },
    {
     "code": "payload[57 + i] != 0x20",
     "line": 6176
    },
    {
     "code": "i < limit",
     "line": 6182
    },
    {
     "code": "payload[57 + i] != 0x00",
     "line": 6183
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "((payload[2] & 0x80) /* NetBIOS Response */ ",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "((payload[2] & 0x80) /* NetBIOS Response */ ",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "((payload[2] & 0x80) /* NetBIOS Response */ ",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "(payload[2] & 0x80) /* NetBIOS Response */ ",
     "name": "<operator>.logicalOr",
     "nargs": null
    },
    {
     "code": "payload[2] & 0x80",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "payload[2]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "payload"
   ],
   "osv_id": "ARVO-42527353",
   "sites": [
    {
     "args": "64",
     "callee": "<operator>.alloc",
     "code": "name[64]",
     "line": 6161
    },
    {
     "args": "name",
     "callee": "strdup",
     "code": "strdup(name)",
     "line": 6196
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Flow::dissectNetBIOS(unsigned char*, unsigned short)"
  }
 },
 {
  "osv_id": "ARVO-42527452",
  "project": "ntopng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "c",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ntopng/src/Flow.cpp",
    "line": 5516,
    "size": null,
    "type": "u_char"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "grow_buffer",
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "line": 426
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "41",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 5516,
    "fn": "Flow::setBittorrentHash(char*)",
    "code": "c = hash[i] & 0xFF | hash[i] & 0xFF | hash[i]",
    "origin": "report:crash"
   },
   {
    "code": "strdup(bittorrent_hash)",
    "fn": "Flow::setBittorrentHash(char*)",
    "kind": "strdup",
    "line": 5522,
    "origin": "cpg",
    "args": "bittorrent_hash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Flow::setBittorrentHash(char*)",
    "file": "/src/ntopng/src/Flow.cpp",
    "line": 5516
   },
   "code": "c = hash[i] & 0xFF | hash[i] & 0xFF | hash[i]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "setBittorrentHash",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < 20",
   "guard_count": 1,
   "control_structures": "FOR:5515,IF:5522"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_char",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "hash"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42527452/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "testcase_size": 256
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "Flow::setBittorrentHash(char*)--Flow::dissectBittorrent(char*, unsigned short)--NetworkInterface::processPacket(unsigned int, bool, timeval const*, unsigned lon"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "c = hash[i] & 0xFF",
     "line": 5516
    }
   ],
   "entity_decl": {
    "line": 5516,
    "type": "u_char"
   },
   "entity_name_cpg": "c",
   "func_lines": [
    5511,
    5523
   ],
   "func_params": {
    "names": [
     "this",
     "hash"
    ],
    "types": [
     "Flow",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "i < 20",
     "line": 5515
    },
    {
     "code": "n > 0",
     "line": 5522
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "c = hash[i] & 0xFF",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "hash[i] & 0xFF",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "hash[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "c",
    "hash",
    "i"
   ],
   "osv_id": "ARVO-42527452",
   "sites": [
    {
     "args": "41",
     "callee": "<operator>.alloc",
     "code": "bittorrent_hash[41]",
     "line": 5513
    },
    {
     "args": "bittorrent_hash",
     "callee": "strdup",
     "code": "strdup(bittorrent_hash)",
     "line": 5522
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Flow::setBittorrentHash(char*)"
  }
 },
 {
  "osv_id": "ARVO-42527526",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "chk_udata",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 178,
    "type": "H5O_chk_cache_ud_t",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 237
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "H5FL_CALLOC"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 185,
    "fn": "H5O__chunk_protect",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5O__chunk_protect",
    "file": "/src/hdf5/src/H5Ochunk.c",
    "line": 185
   },
   "code": "chk_udata.size    = oh->chunk[idx].size",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5O__chunk_protect",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42527526/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "testcase_size": 1808
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "H5O__chunk_protect--H5O__chunk_delete--H5O__cont_delete"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "chk_udata.oh      = oh",
     "line": 183
    },
    {
     "code": "chk_udata.chunkno = idx",
     "line": 184
    },
    {
     "code": "chk_udata.size    = oh->chunk[idx].size",
     "line": 185
    }
   ],
   "entity_decl": {
    "line": 178,
    "type": "H5O_chk_cache_ud_t"
   },
   "entity_name_cpg": "chk_udata",
   "func_lines": [
    148,
    207
   ],
   "func_params": {
    "names": [
     "f",
     "oh",
     "idx"
    ],
    "types": [
     "H5F_t*",
     "H5O_t*",
     "unsigned"
    ]
   },
   "guards": [
    {
     "code": "'_' == __func__[2]",
     "line": 154
    },
    {
     "code": "'_' == __func__[3]",
     "line": 154
    },
    {
     "code": "'_' == __func__[3]",
     "line": 154
    },
    {
     "code": "'_' == __func__[4]",
     "line": 154
    },
    {
     "code": "'_' == __func__[4]",
     "line": 154
    },
    {
     "code": "'_' == __func__[5]",
     "line": 154
    },
    {
     "code": "idx < oh->nchunks",
     "line": 159
    },
    {
     "code": "0 == idx",
     "line": 162
    },
    {
     "code": "NULL == (chk_proxy = H5FL_CALLOC(H5O_chunk_proxy_t))",
     "line": 165
    },
    {
     "code": "H5O__inc_rc(oh) < 0",
     "line": 169
    },
    {
     "code": "NULL == (chk_proxy = (H5O_chunk_proxy_t *)H5AC_protect(f, H5AC_OHDR_CHK, oh->chunk[idx].addr,",
     "line": 188
    },
    {
     "code": "chk_proxy->oh == oh",
     "line": 193
    },
    {
     "code": "chk_proxy->chunkno == idx",
     "line": 194
    },
    {
     "code": "0 == idx",
     "line": 203
    },
    {
     "code": "H5O__chunk_dest(chk_proxy) < 0",
     "line": 203
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "chk_udata.size    = oh->chunk[idx].size",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "chk_udata.size",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "oh->chunk[idx].size",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "oh->chunk[idx]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "oh->chunk",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "chk_udata",
    "oh",
    "idx"
   ],
   "osv_id": "ARVO-42527526",
   "sites": [
    {
     "args": "",
     "callee": "H5FL_CALLOC",
     "code": "H5FL_CALLOC(H5O_chunk_proxy_t)",
     "line": 165
    },
    {
     "args": "&(H5_H5O_chunk_proxy_t_reg_free_list)",
     "callee": "H5FL_reg_calloc",
     "code": "H5FL_reg_calloc(&(H5_H5O_chunk_proxy_t_reg_free_list))",
     "line": 165
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5O__chunk_protect"
  }
 },
 {
  "osv_id": "ARVO-42527562",
  "project": "ntopng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "this",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ntopng/src/ICMPinfo.cpp",
    "line": 67,
    "size": null,
    "type": "Redis"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "grow_buffer",
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "line": 426
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 118,
    "fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)",
    "code": "num_requests++ | this->num_requests",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)",
    "file": "/src/ntopng/src/ICMPinfo.cpp",
    "line": 118
   },
   "code": "num_requests++ | this->num_requests",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "reconnectRedis",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:74,IF:87,IF:90,GOTO:93,WHILE:97,IF:100,ELSE:105,BREAK:105,IF:108,IF:110,ELSE:115,IF:120"
  },
  "call_chain": [],
  "types": {
   "entity_type": "Redis",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "this"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42527562/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "testcase_size": 114
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)--NetworkInterface::processPacket(unsigned int, bool, timeval const*, unsigned long, ndpi_ethhdr*, un"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "operational = false",
     "line": 72
    },
    {
     "code": "redis = redisConnectWithTimeout(redis_host, redis_port, timeout)",
     "line": 85
    },
    {
     "code": "operational = true",
     "line": 135
    }
   ],
   "entity_decl": {
    "line": 67,
    "type": "Redis"
   },
   "entity_name_cpg": "this",
   "func_lines": [
    67,
    140
   ],
   "func_params": {
    "names": [
     "this"
    ],
    "types": [
     "Redis"
    ]
   },
   "guards": [
    {
     "code": "redis != NULL",
     "line": 74
    },
    {
     "code": "reply->type == REDIS_REPLY_ERROR",
     "line": 90
    },
    {
     "code": "num_attempts > 0",
     "line": 97
    },
    {
     "code": "reply->type == REDIS_REPLY_ERROR",
     "line": 100
    },
    {
     "code": "redis == NULL",
     "line": 108
    },
    {
     "code": "reply == NULL",
     "line": 108
    },
    {
     "code": "ntop->getTrace()->get_trace_level() == 0",
     "line": 110
    },
    {
     "code": "reply->type == REDIS_REPLY_ERROR",
     "line": 120
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "num_requests++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "this->num_requests",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "this"
   ],
   "osv_id": "ARVO-42527562",
   "sites": [
    {
     "args": "this->redis",
     "callee": "redisFree",
     "code": "redisFree(redis)",
     "line": 76
    },
    {
     "args": "reply",
     "callee": "freeReplyObject",
     "code": "freeReplyObject(reply)",
     "line": 116
    },
    {
     "args": "reply",
     "callee": "freeReplyObject",
     "code": "freeReplyObject(reply)",
     "line": 124
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ICMPinfo::dissectICMP(unsigned short, unsigned char const*)"
  }
 },
 {
  "osv_id": "ARVO-42527613",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "len",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_domain_classify.c",
    "line": 389,
    "size": null,
    "type": "u_int32_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082) (BuildId: 1878e6b475720c7c51969e69ab2d276fae6d1dee)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 394,
    "fn": "ndpi_domain_classify_contains",
    "code": "(len = strlen(domain)) == 0 | len = strlen(domain) | strlen(domain)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_domain_classify_contains",
    "file": "/src/ndpi/src/lib/ndpi_domain_classify.c",
    "line": 394
   },
   "code": "(len = strlen(domain)) == 0 | len = strlen(domain) | strlen(domain)",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_domain_classify_contains",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:393,IF:394,IF:395,IF:396,IF:399,IF:407,FOR:415,IF:416,IF:421"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int32_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "domain"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/3c7b2a714e34441b0c412f22e348f69bcfab6689/ARVO-42527613/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_3c7b2a714e34.cpg",
   "testcase_size": 45
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "strlen--ndpi_domain_classify_contains--ndpi_match_custom_category"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "len = strlen(domain)",
     "line": 394
    }
   ],
   "entity_decl": {
    "line": 389,
    "type": "u_int32_t"
   },
   "entity_name_cpg": "len",
   "func_lines": [
    387,
    435
   ],
   "func_params": {
    "names": [
     "_s",
     "domain"
    ],
    "types": [
     "ndpi_domain_classify*",
     "char*"
    ]
   },
   "guards": [
    {
     "code": "(len = strlen(domain)) == 0",
     "line": 394
    },
    {
     "code": "(dot = strrchr(domain, '.')) == NULL",
     "line": 395
    },
    {
     "code": "i<MAX_NUM_NDPI_DOMAIN_CLASSIFICATIONS",
     "line": 415
    },
    {
     "code": "s->class[i] != NULL",
     "line": 416
    }
   ],
   "line_call_count": 3,
   "line_calls": [
    {
     "code": "(len = strlen(domain)) == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "len = strlen(domain)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "strlen(domain)",
     "name": "strlen",
     "nargs": 1
    }
   ],
   "line_ids": [
    "len",
    "domain"
   ],
   "osv_id": "ARVO-42527613",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "buf[256]",
     "line": 417
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_domain_classify_contains"
  }
 },
 {
  "osv_id": "ARVO-42527635",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "bit_read_TV",
    "file": "/src/libredwg/src/bits.c",
    "line": 1707
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1186,
    "fn": "cquote",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "cquote",
    "file": "/src/libredwg/src/out_dxf.c",
    "line": 1186
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "cquote",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/f885ca9079816750f6f81fe6c0f7d15d53e8a9cb/ARVO-42527635/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_f885ca907981.cpg",
   "testcase_size": 1527
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "cquote--dxf_fixup_string--dxf_header_write"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    745,
    768
   ],
   "func_params": {
    "names": [
     "dest",
     "src"
    ],
    "types": [
     "char*restrict",
     "char*restrict"
    ]
   },
   "guards": [
    {
     "code": "c == '\"'",
     "line": 753
    },
    {
     "code": "c == '\\\\'",
     "line": 758
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42527635",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "cquote"
  }
 },
 {
  "osv_id": "ARVO-42527895",
  "project": "hdf5",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "accum",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 855,
    "type": "H5F_meta_accum_t*",
    "size": null
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "H5FL__malloc",
    "file": "/src/hdf5/src/H5FL.c",
    "line": 237
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 898,
    "fn": "H5F__accum_free",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "H5F__accum_free",
    "file": "/src/hdf5/src/H5Faccum.c",
    "line": 898
   },
   "code": "memmove((char *)(accum->buf), (const char *)(accum->buf + overlap_size), new_accum_size)",
   "access": {
    "dir": "READ",
    "width": 361,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "H5F__accum_free",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/hdf5/address/966454aac1231da7209ef81c11055d3312181f99/ARVO-42527895/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/hdf5_966454aac123.cpg",
   "testcase_size": 1808
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memmove--H5F__accum_free--H5MF_xfree"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "accum = &f_sh->accum",
     "line": 865
    },
    {
     "code": "accum->loc   = HADDR_UNDEF",
     "line": 885
    },
    {
     "code": "accum->size  = 0",
     "line": 886
    },
    {
     "code": "accum->dirty = FALSE",
     "line": 887
    },
    {
     "code": "accum->size = new_accum_size",
     "line": 902
    },
    {
     "code": "accum->dirty_len = (accum->dirty_off + accum->dirty_len) - overlap_size",
     "line": 912
    },
    {
     "code": "accum->dirty_off = 0",
     "line": 913
    },
    {
     "code": "accum->dirty = FALSE",
     "line": 917
    },
    {
     "code": "accum->dirty = FALSE",
     "line": 964
    },
    {
     "code": "accum->dirty = FALSE",
     "line": 987
    },
    {
     "code": "accum->dirty_len = (size_t)(addr - dirty_start)",
     "line": 991
    },
    {
     "code": "accum->size = accum->size - overlap_size",
     "line": 998
    }
   ],
   "entity_decl": {
    "line": 855,
    "type": "H5F_meta_accum_t*"
   },
   "entity_name_cpg": "accum",
   "func_lines": [
    852,
    1004
   ],
   "func_params": {
    "names": [
     "f_sh",
     "type",
     "addr",
     "size"
    ],
    "types": [
     "H5F_shared_t*",
     "H5FD_mem_t",
     "haddr_t",
     "hsize_t"
    ]
   },
   "guards": [
    {
     "code": "'_' == __func__[2]",
     "line": 859
    },
    {
     "code": "'_' == __func__[3]",
     "line": 859
    },
    {
     "code": "'_' == __func__[3]",
     "line": 859
    },
    {
     "code": "'_' == __func__[4]",
     "line": 859
    },
    {
     "code": "'_' == __func__[4]",
     "line": 859
    },
    {
     "code": "'_' == __func__[5]",
     "line": 859
    },
    {
     "code": "(accum->loc) != UINT64_MAX",
     "line": 871
    },
    {
     "code": "(addr) < (accum->loc)",
     "line": 872
    },
    {
     "code": "((addr) + (size)) > (accum->loc)",
     "line": 872
    },
    {
     "code": "(addr) < ((accum->loc) + (accum->size))",
     "line": 872
    },
    {
     "code": "H5FD_MEM_DRAW != type",
     "line": 877
    },
    {
     "code": "H5FD_MEM_GHEAP != type",
     "line": 878
    },
    {
     "code": "(addr) != UINT64_MAX",
     "line": 881
    },
    {
     "code": "(accum->loc) != UINT64_MAX",
     "line": 881
    },
    {
     "code": "(addr + size) != UINT64_MAX",
     "line": 883
    },
    {
     "code": "(accum->loc + accum->size) != UINT64_MAX",
     "line": 883
    },
    {
     "code": "overlap_size < accum->dirty_off",
     "line": 907
    },
    {
     "code": "overlap_size < (accum->dirty_off + accum->dirty_len)",
     "line": 911
    },
    {
     "code": "(addr) != UINT64_MAX",
     "line": 931
    },
    {
     "code": "(dirty_end) != UINT64_MAX",
     "line": 931
    },
    {
     "code": "(addr) < (dirty_end)",
     "line": 931
    },
    {
     "code": "(addr) != UINT64_MAX",
     "line": 938
    },
    {
     "code": "(dirty_start) != UINT64_MAX",
     "line": 938
    },
    {
     "code": "(addr) < (dirty_start)",
     "line": 938
    },
    {
     "code": "(tail_addr) != UINT64_MAX",
     "line": 940
    },
    {
     "code": "(dirty_start) != UINT64_MAX",
     "line": 940
    },
    {
     "code": "H5FD_write(file, H5FD_MEM_DEFAULT, dirty_start, accum->dirty_len,",
     "line": 942
    },
    {
     "code": "(tail_addr) != UINT64_MAX",
     "line": 948
    },
    {
     "code": "(dirty_end) != UINT64_MAX",
     "line": 948
    },
    {
     "code": "(tail_addr) < (dirty_end)",
     "line": 948
    },
    {
     "code": "write_size > 0",
     "line": 955
    },
    {
     "code": "H5FD_write(file, H5FD_MEM_DEFAULT, dirty_start + dirty_delta, write_size,",
     "line": 958
    },
    {
     "code": "(tail_addr) != UINT64_MAX",
     "line": 969
    },
    {
     "code": "(dirty_end) != UINT64_MAX",
     "line": 969
    },
    {
     "code": "(tail_addr) < (dirty_end)",
     "line": 969
    },
    {
     "code": "write_size > 0",
     "line": 976
    },
    {
     "code": "H5FD_write(file, H5FD_MEM_DEFAULT, dirty_start + dirty_delta, write_size,",
     "line": 979
    },
    {
     "code": "(addr) != UINT64_MAX",
     "line": 985
    },
    {
     "code": "(addr) == (dirty_start)",
     "line": 985
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "HDmemmove(accum->buf, accum->buf + overlap_size, new_accum_size)",
     "name": "HDmemmove",
     "nargs": 2
    },
    {
     "code": "accum->buf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "memmove((char *)(accum->buf), (const char *)(accum->buf + overlap_size), new_accum_size)",
     "name": "memmove",
     "nargs": 3
    },
    {
     "code": "(char *)(accum->buf)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "accum->buf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(const char *)(accum->buf + overlap_size)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "accum->buf + overlap_size",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "accum->buf",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "accum",
    "new_accum_size",
    "overlap_size"
   ],
   "osv_id": "ARVO-42527895",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "H5F__accum_free"
  }
 },
 {
  "osv_id": "ARVO-42528148",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "bit_TV_to_utf8",
    "file": "/src/libredwg/src/bits.c",
    "line": 2949
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "1 ;; destlen + 1",
   "size_expr_cpg_callee": "calloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2976,
    "fn": "bit_TV_to_utf8",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "bit_TV_to_utf8",
    "file": "/src/libredwg/src/bits.c",
    "line": 2976
   },
   "code": "",
   "access": {
    "dir": "WRITE",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "bit_TV_to_utf8",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/f8170bbc0835943027812dd7a1333747a2b840a8/ARVO-42528148/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_f8170bbc0835.cpg",
   "testcase_size": 1658
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "bit_TV_to_utf8--json_cquote--json_header_write_private"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    2922,
    3043
   ],
   "func_params": {
    "names": [
     "src",
     "codepage"
    ],
    "types": [
     "char*restrict",
     "BITCODE_RS"
    ]
   },
   "guards": [
    {
     "code": "codepage == CP_UTF8",
     "line": 2926
    },
    {
     "code": "i < destlen",
     "line": 2988
    },
    {
     "code": "c < 0x80",
     "line": 2997
    },
    {
     "code": "c < 0x80",
     "line": 3003
    },
    {
     "code": "c < 0x800",
     "line": 3006
    },
    {
     "code": "i + 1 > destlen",
     "line": 3008
    },
    {
     "code": "i + 2 > destlen",
     "line": 3019
    },
    {
     "code": "i + 1 > destlen",
     "line": 3038
    }
   ],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42528148",
   "sites": [
    {
     "args": "1 ;; destlen + 1",
     "callee": "calloc",
     "code": "calloc (1, destlen + 1)",
     "line": 2981
    },
    {
     "args": "str ;; i + 1 + 1",
     "callee": "realloc",
     "code": "realloc(str, i + 1 + 1)",
     "line": 3008
    },
    {
     "args": "str",
     "callee": "free",
     "code": "free(str)",
     "line": 3008
    },
    {
     "args": "str ;; i + 2 + 1",
     "callee": "realloc",
     "code": "realloc(str, i + 2 + 1)",
     "line": 3019
    },
    {
     "args": "str",
     "callee": "free",
     "code": "free(str)",
     "line": 3019
    },
    {
     "args": "str ;; i + 1 + 1",
     "callee": "realloc",
     "code": "realloc(str, i + 1 + 1)",
     "line": 3038
    },
    {
     "args": "str",
     "callee": "free",
     "code": "free(str)",
     "line": 3038
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "bit_TV_to_utf8"
  }
 },
 {
  "osv_id": "ARVO-42528225",
  "project": "icu",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "uprv_malloc_74",
    "file": "/src/icu/icu4c/source/common/cmemory.cpp",
    "line": 58
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 53,
    "fn": "getDayPeriodForHour",
    "code": "",
    "origin": "report:crash"
   },
   {
    "kind": "free",
    "line": 99,
    "fn": "uprv_free_74",
    "code": null,
    "origin": "report:freed_by"
   }
  ],
  "crash": {
   "site": {
    "fn": "getDayPeriodForHour",
    "file": "/src/icu/icu4c/source/i18n/dayperiodrules.h",
    "line": 53
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "getDayPeriodForHour",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/icu/address/d082de574ff13873123c55212ad20cf258ffb283/ARVO-42528225/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/icu_d082de574ff1.cpg",
   "testcase_size": 32
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "getDayPeriodForHour--icu_74::SimpleDateFormat::subFormat(icu_74::UnicodeString&, char16_t, int, UDisplayContext, int, char16_t, icu_74::FieldPositionHandler&, i"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    -1,
    -1
   ],
   "func_params": {
    "names": [
     "p1",
     "p2"
    ],
    "types": [
     "ANY",
     "ANY"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42528225",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": "uprv_free_74",
   "use_fn": "getDayPeriodForHour"
  }
 },
 {
  "osv_id": "ARVO-42528301",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "t",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-pack/src/pack.c",
    "line": 1208,
    "size": null,
    "type": "mrb_int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1220,
    "fn": "read_tmpl",
    "code": "t = tptr[tmpl->idx++] | tptr[tmpl->idx++] | tmpl->idx++ | tmpl->idx",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "read_tmpl",
    "file": "/src/mruby/mrbgems/mruby-pack/src/pack.c",
    "line": 1220
   },
   "code": "t = tptr[tmpl->idx++] | tptr[tmpl->idx++] | tmpl->idx++ | tmpl->idx",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "read_tmpl",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "SWITCH:1222,BREAK:1227,BREAK:1232,BREAK:1237,BREAK:1243,BREAK:1249,BREAK:1255,BREAK:1261,BREAK:1267,BREAK:1273,BREAK:1279,BREAK:1284"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mrb_int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "tmpl"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/1bc8ef903e138e9f3d6af4d3bdd9a09254a342e0/ARVO-42528301/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_1bc8ef903e13.cpg",
   "testcase_size": 37
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "05",
   "shadow_legend_size": 21,
   "dedup_token": "read_tmpl--mrb_pack_pack--mrb_vm_exec"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "t = tptr[tmpl->idx++]",
     "line": 1220
    },
    {
     "code": "t = 'S'",
     "line": 1302
    },
    {
     "code": "t = 'L'",
     "line": 1303
    },
    {
     "code": "t = 'Q'",
     "line": 1304
    },
    {
     "code": "t = 's'",
     "line": 1311
    },
    {
     "code": "t = 'l'",
     "line": 1312
    },
    {
     "code": "t = 'q'",
     "line": 1313
    },
    {
     "code": "t = 'L'",
     "line": 1320
    },
    {
     "code": "t = 'Q'",
     "line": 1321
    },
    {
     "code": "t = 'l'",
     "line": 1328
    },
    {
     "code": "t = 'q'",
     "line": 1329
    }
   ],
   "entity_decl": {
    "line": 1208,
    "type": "mrb_int"
   },
   "entity_name_cpg": "t",
   "func_lines": [
    1205,
    1493
   ],
   "func_params": {
    "names": [
     "mrb",
     "tmpl",
     "typep",
     "sizep",
     "countp",
     "flagsp"
    ],
    "types": [
     "mrb_state*",
     "tmpl*",
     "pack_type*",
     "int*",
     "int*",
     "unsigned int*"
    ]
   },
   "guards": [
    {
     "code": "++tmpl->idx < tlen",
     "line": 1428
    },
    {
     "code": "tptr[tmpl->idx] != '\\n'",
     "line": 1428
    },
    {
     "code": "tmpl->idx < tlen",
     "line": 1446
    },
    {
     "code": "INT_MAX < n",
     "line": 1451
    },
    {
     "code": "ch == '*'",
     "line": 1458
    },
    {
     "code": "type == PACK_TYPE_NONE",
     "line": 1459
    },
    {
     "code": "ch == '_'",
     "line": 1464
    },
    {
     "code": "ch == '!'",
     "line": 1464
    },
    {
     "code": "ch == '<'",
     "line": 1464
    },
    {
     "code": "ch == '>'",
     "line": 1464
    },
    {
     "code": "strchr(\"sSiIlLqQ\", (int)t) == NULL",
     "line": 1465
    },
    {
     "code": "ch == '_'",
     "line": 1468
    },
    {
     "code": "ch == '!'",
     "line": 1468
    },
    {
     "code": "ch == '<'",
     "line": 1471
    },
    {
     "code": "ch == '>'",
     "line": 1474
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "t = tptr[tmpl->idx++]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "tptr[tmpl->idx++]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "tmpl->idx++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    },
    {
     "code": "tmpl->idx",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "t",
    "tptr",
    "tmpl"
   ],
   "osv_id": "ARVO-42528301",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "read_tmpl"
  }
 },
 {
  "osv_id": "ARVO-42528658",
  "project": "mruby",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "bits",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/mruby/mrbgems/mruby-pack/src/pack.c",
    "line": 930,
    "size": null,
    "type": "int"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "mrb_default_allocf",
    "file": "/src/mruby/src/state.c",
    "line": 69
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 940,
    "fn": "unpack_bstr",
    "code": "bits = (unsigned char)*sptr++ | (unsigned char)*sptr++ | *sptr++ | sptr++",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "unpack_bstr",
    "file": "/src/mruby/mrbgems/mruby-pack/src/pack.c",
    "line": 940
   },
   "code": "bits = (unsigned char)*sptr++ | (unsigned char)*sptr++ | *sptr++ | sptr++",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "unpack_bstr",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "DO:920,IF:920,IF:924,FOR:932,IF:933,IF:934,ELSE:935,ELSE:938,IF:939,ELSE:940"
  },
  "call_chain": [],
  "types": {
   "entity_type": "int",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "mrb",
   "src",
   "ary",
   "count"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/mruby/address/5b2056efda14853ecf7107a76ee0feee451b4f34/ARVO-42528658/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/mruby_5b2056efda14.cpg",
   "testcase_size": 63
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "unpack_bstr--pack_unpack--mrb_pack_unpack"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "bits = 0",
     "line": 930
    },
    {
     "code": "bits = (unsigned char)*sptr++",
     "line": 935
    },
    {
     "code": "bits = (unsigned char)*sptr++",
     "line": 940
    }
   ],
   "entity_decl": {
    "line": 930,
    "type": "int"
   },
   "entity_name_cpg": "bits",
   "func_lines": [
    917,
    947
   ],
   "func_params": {
    "names": [
     "mrb",
     "src",
     "slen",
     "ary",
     "count",
     "flags"
    ],
    "types": [
     "mrb_state*",
     "void*",
     "int",
     "mrb_value",
     "int",
     "unsigned int"
    ]
   },
   "guards": [
    {
     "code": "count == -1",
     "line": 924
    },
    {
     "code": "i<count",
     "line": 932
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "bits = (unsigned char)*sptr++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(unsigned char)*sptr++",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "*sptr++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "sptr++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "bits",
    "sptr"
   ],
   "osv_id": "ARVO-42528658",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "unpack_bstr"
  }
 },
 {
  "osv_id": "ARVO-42528757",
  "project": "libxml2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "entry",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libxml2/dict.c",
    "line": 519,
    "size": null,
    "type": "xmlDictEntry*"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "xmlFuzzMalloc",
    "file": "/src/libxml2/fuzz/fuzz.c",
    "line": 84
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 541,
    "fn": "xmlDictFindEntry",
    "code": "(memcmp(entry->name, name, len) == 0) &&",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "xmlDictFindEntry",
    "file": "/src/libxml2/dict.c",
    "line": 541
   },
   "code": "(memcmp(entry->name, name, len) == 0) &&",
   "access": {
    "dir": "READ",
    "width": 8128207,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "xmlDictFindEntry",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:527,DO:535,IF:536,IF:537,IF:541,BREAK:544,ELSE:546,IF:547,BREAK:549,IF:557"
  },
  "call_chain": [],
  "types": {
   "entity_type": "xmlDictEntry*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dict",
   "prefix",
   "name",
   "len",
   "hashValue"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libxml2/address/06e2f3a46e488f285c010cfa738012f02ed98d10/ARVO-42528757/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libxml2_06e2f3a46e48.cpg",
   "testcase_size": 739009
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "MemcmpInterceptorCommon(void*, int (*)(void const*, void const*, unsigned long), void const*, void const*, unsigned long)--bcmp--xmlDictFindEntry"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "entry = &dict->table[pos]",
     "line": 525
    },
    {
     "code": "entry = dict->table",
     "line": 558
    }
   ],
   "entity_decl": {
    "line": 519,
    "type": "xmlDictEntry*"
   },
   "entity_name_cpg": "entry",
   "func_lines": [
    515,
    565
   ],
   "func_params": {
    "names": [
     "dict",
     "prefix",
     "name",
     "len",
     "hashValue",
     "pfound"
    ],
    "types": [
     "xmlDict*",
     "xmlChar*",
     "xmlChar*",
     "int",
     "unsigned",
     "int*"
    ]
   },
   "guards": [
    {
     "code": "entry->hashValue != 0",
     "line": 527
    },
    {
     "code": "entry->hashValue == hashValue",
     "line": 536
    },
    {
     "code": "prefix == NULL",
     "line": 537
    },
    {
     "code": "memcmp(entry->name, name, len) == 0",
     "line": 541
    },
    {
     "code": "entry->name[len] == 0",
     "line": 542
    },
    {
     "code": "(pos & mask) == 0",
     "line": 557
    },
    {
     "code": "entry->hashValue != 0",
     "line": 559
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "(memcmp(entry->name, name, len) == 0) &&",
     "name": "<operator>.logicalAnd",
     "nargs": null
    },
    {
     "code": "memcmp(entry->name, name, len) == 0",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "memcmp(entry->name, name, len)",
     "name": "memcmp",
     "nargs": 3
    },
    {
     "code": "entry->name",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "entry",
    "name",
    "len"
   ],
   "osv_id": "ARVO-42528757",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "xmlDictFindEntry"
  }
 },
 {
  "osv_id": "ARVO-42528919",
  "project": "libredwg",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "nums",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/libredwg/src/in_json.c",
    "line": 1258,
    "size": null,
    "type": "BITCODE_BS*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "json_HEADER",
    "file": "/src/libredwg/src/in_json.c",
    "line": 1258
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "80",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "code": "strdup (str)",
    "fn": "json_HEADER",
    "kind": "strdup",
    "line": 1229,
    "origin": "cpg",
    "args": "str"
   },
   {
    "code": "calloc (f->size, 1)",
    "fn": "json_HEADER",
    "kind": "calloc",
    "line": 1258,
    "origin": "cpg",
    "args": "f->size ;; 1"
   },
   {
    "kind": "unknown",
    "line": 1263,
    "fn": "json_HEADER",
    "code": "nums[k] = (BITCODE_BS)json_long (dat, tokens) | nums[k] | (BITCODE_BS)json_long (dat, tokens) | json_long (dat, tokens)",
    "origin": "report:crash"
   },
   {
    "code": "free (nums)",
    "fn": "json_HEADER",
    "kind": "free",
    "line": 1271,
    "origin": "cpg",
    "args": "nums"
   }
  ],
  "crash": {
   "site": {
    "fn": "json_HEADER",
    "file": "/src/libredwg/src/in_json.c",
    "line": 1263
   },
   "code": "nums[k] = (BITCODE_BS)json_long (dat, tokens) | nums[k] | (BITCODE_BS)json_long (dat, tokens) | json_long (dat, tokens)",
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "json_HEADER",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "k < size1",
   "guard_count": 1,
   "control_structures": "IF:1152,IF:1154,IF:1154,IF:1160,FOR:1163,IF:1169,IF:1169,IF:1169,IF:1172,IF:1174,FOR:1177,IF:1181"
  },
  "call_chain": [],
  "types": {
   "entity_type": "BITCODE_BS*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "dat",
   "tokens"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libredwg/address/c8cf03ce4c2315b146caf582ea061c0460193bcc/ARVO-42528919/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_c8cf03ce4c23.cpg",
   "testcase_size": 25
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "02",
   "shadow_legend_size": 21,
   "dedup_token": "json_HEADER--dwg_read_json--LLVMFuzzerTestOneInput"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*nums = (BITCODE_BS *)calloc (f->size, 1)",
     "line": 1258
    },
    {
     "code": "nums[k] = (BITCODE_BS)json_long (dat, tokens)",
     "line": 1263
    }
   ],
   "entity_decl": {
    "line": 1258,
    "type": "BITCODE_BS*"
   },
   "entity_name_cpg": "nums",
   "func_lines": [
    1141,
    1312
   ],
   "func_params": {
    "names": [
     "dat",
     "dwg",
     "tokens"
    ],
    "types": [
     "Bit_Chain*restrict",
     "Dwg_Data*restrict",
     "jsmntokens_t*restrict"
    ]
   },
   "guards": [
    {
     "code": "t->type != JSMN_OBJECT",
     "line": 1152
    },
    {
     "code": "i < size",
     "line": 1163
    },
    {
     "code": "tokens->index > (unsigned int)tokens->num_tokens",
     "line": 1169
    },
    {
     "code": "t->type == JSMN_ARRAY",
     "line": 1174
    },
    {
     "code": "index < MAX (t->size, 128)",
     "line": 1177
    },
    {
     "code": "(t->size) > (128)",
     "line": 1177
    },
    {
     "code": "tokens->index > (unsigned int)tokens->num_tokens",
     "line": 1184
    },
    {
     "code": "t->type == JSMN_PRIMITIVE",
     "line": 1193
    },
    {
     "code": "t->type == JSMN_PRIMITIVE",
     "line": 1200
    },
    {
     "code": "t->type == JSMN_PRIMITIVE",
     "line": 1211
    },
    {
     "code": "t->type == JSMN_STRING",
     "line": 1218
    },
    {
     "code": "dwg->header.version < R_13b1",
     "line": 1224
    },
    {
     "code": "strlen (str) > 15",
     "line": 1225
    },
    {
     "code": "t->type == JSMN_ARRAY",
     "line": 1236
    },
    {
     "code": "t->type == JSMN_ARRAY",
     "line": 1245
    },
    {
     "code": "t->type == JSMN_ARRAY",
     "line": 1254
    },
    {
     "code": "k < size1",
     "line": 1260
    },
    {
     "code": "tokens->index > (unsigned int)tokens->num_tokens",
     "line": 1262
    },
    {
     "code": "t->type == JSMN_ARRAY",
     "line": 1285
    },
    {
     "code": "t->type == JSMN_OBJECT",
     "line": 1293
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "nums[k] = (BITCODE_BS)json_long (dat, tokens)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "nums[k]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "(BITCODE_BS)json_long (dat, tokens)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "json_long (dat, tokens)",
     "name": "json_long",
     "nargs": 2
    }
   ],
   "line_ids": [
    "nums",
    "k",
    "dat",
    "tokens"
   ],
   "osv_id": "ARVO-42528919",
   "sites": [
    {
     "args": "80",
     "callee": "<operator>.alloc",
     "code": "key[80]",
     "line": 1165
    },
    {
     "args": "str",
     "callee": "strdup",
     "code": "strdup (str)",
     "line": 1229
    },
    {
     "args": "str",
     "callee": "free",
     "code": "free (str)",
     "line": 1234
    },
    {
     "args": "f->size ;; 1",
     "callee": "calloc",
     "code": "calloc (f->size, 1)",
     "line": 1258
    },
    {
     "args": "nums",
     "callee": "free",
     "code": "free (nums)",
     "line": 1271
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": 0,
   "cross_frame_exact": true,
   "free_cross_function": null,
   "free_fn": "json_HEADER",
   "use_fn": "json_HEADER"
  }
 },
 {
  "osv_id": "ARVO-42528923",
  "project": "ntopng",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "rsp",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ntopng/src/Flow.cpp",
    "line": 5935,
    "size": null,
    "type": "mdns_rsp_entry"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "grow_buffer",
    "file": "/src/libpcap-1.9.1/./sf-pcap.c",
    "line": 426
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "256",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 6004,
    "fn": "Flow::dissectMDNS(unsigned char*, unsigned short)",
    "code": "memcpy(&rsp, &payload[i], sizeof(rsp)) | &rsp | &payload[i] | payload[i]",
    "origin": "report:crash"
   },
   {
    "code": "strdup(name)",
    "fn": "Flow::dissectMDNS(unsigned char*, unsigned short)",
    "kind": "strdup",
    "line": 6054,
    "origin": "cpg",
    "args": "name"
   },
   {
    "code": "strdup(&txt_buf[3])",
    "fn": "Flow::dissectMDNS(unsigned char*, unsigned short)",
    "kind": "strdup",
    "line": 6097,
    "origin": "cpg",
    "args": "&txt_buf[3]"
   },
   {
    "code": "strdup(&txt_buf[5])",
    "fn": "Flow::dissectMDNS(unsigned char*, unsigned short)",
    "kind": "strdup",
    "line": 6100,
    "origin": "cpg",
    "args": "&txt_buf[5]"
   }
  ],
  "crash": {
   "site": {
    "fn": "Flow::dissectMDNS(unsigned char*, unsigned short)",
    "file": "/src/ntopng/src/Flow.cpp",
    "line": 6004
   },
   "code": "memcpy(&rsp, &payload[i], sizeof(rsp)) | &rsp | &payload[i] | payload[i]",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "dissectMDNS",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "i < payload_len | i < payload_len | offset > i",
   "guard_count": 5,
   "control_structures": "IF:5924,WHILE:5933,FOR:5943,IF:5944,BREAK:5946,ELSE:5947,IF:5947,IF:5948,ELSE:5949,IF:5949,BREAK:5955,ELSE:5956"
  },
  "call_chain": [],
  "types": {
   "entity_type": "mdns_rsp_entry",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "this",
   "payload",
   "payload_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ntopng/address/ab73418e29e000c54acb2a71d9f3bb57a779e792/ARVO-42528923/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ntopng_ab73418e29e0.cpg",
   "testcase_size": 146
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "alloc.size_expr",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "Flow::dissectMDNS(unsigned char*, unsigned short)--NetworkInterface::processPacket(unsigned int, bool, timeval const*, unsigned long, ndpi_ethhdr*, unsigned sho"
  },
  "deep": {
   "entity_assignments": [],
   "entity_decl": {
    "line": 5935,
    "type": "mdns_rsp_entry"
   },
   "entity_name_cpg": "rsp",
   "func_lines": [
    5914,
    6120
   ],
   "func_params": {
    "names": [
     "this",
     "payload",
     "payload_len"
    ],
    "types": [
     "Flow",
     "u_int8_t*",
     "u_int16_t"
    ]
   },
   "guards": [
    {
     "code": "(payload[2] & 0x80) != 0x80",
     "line": 5924
    },
    {
     "code": "payload_len < 12",
     "line": 5924
    },
    {
     "code": "answers > 0",
     "line": 5933
    },
    {
     "code": "i < payload_len",
     "line": 5933
    },
    {
     "code": "i < payload_len",
     "line": 5943
    },
    {
     "code": "j < (sizeof(_name) - 1)",
     "line": 5943
    },
    {
     "code": "payload[i] == 0x0",
     "line": 5944
    },
    {
     "code": "payload[i] < 32",
     "line": 5947
    },
    {
     "code": "j > 0",
     "line": 5948
    },
    {
     "code": "payload[i] == 0x22",
     "line": 5949
    },
    {
     "code": "payload[i] == 0xC0",
     "line": 5956
    },
    {
     "code": "offset > i",
     "line": 5966
    },
    {
     "code": "i > payload_len",
     "line": 5966
    },
    {
     "code": "num_loops > max_nested_loops",
     "line": 5967
    },
    {
     "code": "i < payload_len",
     "line": 5974
    },
    {
     "code": "payload[i] != 0",
     "line": 5974
    },
    {
     "code": "j < (sizeof(_name) - 1)",
     "line": 5975
    },
    {
     "code": "payload[i] == 0",
     "line": 5976
    },
    {
     "code": "payload[i] == 0xC0",
     "line": 5978
    },
    {
     "code": "payload[i] < 32",
     "line": 5981
    },
    {
     "code": "j > 0",
     "line": 5982
    },
    {
     "code": "i_save > 0",
     "line": 5988
    },
    {
     "code": "dtype != device_unknown",
     "line": 6033
    },
    {
     "code": "m->getDeviceType() == device_unknown",
     "line": 6036
    },
    {
     "code": "len > 6",
     "line": 6047
    },
    {
     "code": "strcmp(&name[len - 6], \".local\") == 0",
     "line": 6047
    },
    {
     "code": "c != name",
     "line": 6051
    },
    {
     "code": "rsp_type == 0x10",
     "line": 6056
    },
    {
     "code": "data_len > 0",
     "line": 6056
    },
    {
     "code": "off < data_len",
     "line": 6060
    },
    {
     "code": "txt_len < data_len",
     "line": 6063
    },
    {
     "code": "data_len - off > txt_len",
     "line": 6064
    },
    {
     "code": "txt_len > 0",
     "line": 6068
    },
    {
     "code": "strncmp(txt_buf, \"am=\", 3 /* Apple Model */) == 0",
     "line": 6080
    },
    {
     "code": "strncmp(txt_buf, \"model=\", 6) == 0",
     "line": 6082
    },
    {
     "code": "strncmp(txt_buf, \"md=\", 3) == 0",
     "line": 6084
    },
    {
     "code": "strncmp(txt_buf, \"nm=\", 3) == 0",
     "line": 6095
    },
    {
     "code": "strncmp(txt_buf, \"ssid=\", 5) == 0",
     "line": 6099
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "memcpy(&rsp, &payload[i], sizeof(rsp))",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&rsp",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "&payload[i]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "payload[i]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "sizeof(rsp)",
     "name": "<operator>.sizeOf",
     "nargs": 1
    }
   ],
   "line_ids": [
    "rsp",
    "payload",
    "i"
   ],
   "osv_id": "ARVO-42528923",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "_name[256]",
     "line": 5934
    },
    {
     "args": "name",
     "callee": "strdup",
     "code": "strdup(name)",
     "line": 6054
    },
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "txt_buf[256]",
     "line": 6057
    },
    {
     "args": "&txt_buf[3]",
     "callee": "strdup",
     "code": "strdup(&txt_buf[3])",
     "line": 6097
    },
    {
     "args": "&txt_buf[5]",
     "callee": "strdup",
     "code": "strdup(&txt_buf[5])",
     "line": 6100
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Flow::dissectMDNS(unsigned char*, unsigned short)"
  }
 },
 {
  "osv_id": "ARVO-42528938",
  "project": "radare2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "parse_segments",
    "file": "/src/radare2/libr/../libr/bin/p/../format/mach0/mach0.c",
    "line": 419
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 112,
    "fn": "r_str_ncpy",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "r_str_ncpy",
    "file": "/src/radare2/libr/include/r_util/r_str.h",
    "line": 112
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 161,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "r_str_ncpy",
   "in_loop": null,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": null
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/radare2/address/0c26502a21b8b51e5f7e366d9de08a16a3dfc764/ARVO-42528938/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/radare2_0c26502a21b8.cpg",
   "testcase_size": 984
  },
  "type_reconciliation": {
   "report_fault_kind": "heap-buffer-overflow",
   "ledger_crash_type": "heap-buffer-overflow",
   "used": "heap-buffer-overflow",
   "diverged": false
  },
  "completeness": [
   "entity.decl",
   "alloc.size_expr",
   "types.entity_type",
   "context.in_loop",
   "call_chain"
  ],
  "report_extra": {
   "shadow_byte": "fa",
   "shadow_legend_size": 21,
   "dedup_token": "strlen--r_str_ncpy--load_sections_64"
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "r_str_ncpy"
  }
 }
]

## 任务
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、dimensions、evidence、confidence。
   **样本里的 `measured_dims` 是 stage2 实测出来的值，不是让你猜的**：
   `reassigned_between` / `cross_frame_count` 直接照抄（`null` 才写 unknown），
   `cross_frame_exact=false` 表示跳数算不出精确值，此时 `cross_frame_count` 写 unknown。
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