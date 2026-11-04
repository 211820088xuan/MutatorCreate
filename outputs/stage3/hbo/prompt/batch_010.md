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
  "osv_id": "ARVO-42484477",
  "project": "file",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "eb",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/file/src/softmagic.c",
    "line": 1917,
    "size": null,
    "type": "unsigned char*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "file_ascmagic_with_encoding",
    "file": "/src/file/src/ascmagic.c",
    "line": 146
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1917,
    "fn": "file_strncmp",
    "code": "*eb = b + (ws ? strlen(s2) : len) | b + (ws ? strlen(s2) : len) | ws ? strlen(s2) : len | strlen(s2)",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "file_strncmp",
    "file": "/src/file/src/softmagic.c",
    "line": 1917
   },
   "code": "*eb = b + (ws ? strlen(s2) : len) | b + (ws ? strlen(s2) : len) | ws ? strlen(s2) : len | strlen(s2)",
   "access": {
    "dir": "READ",
    "width": 13,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "file_strncmp",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "b >= eb | b < eb | b < eb",
   "guard_count": 3,
   "control_structures": "IF:1925,WHILE:1926,IF:1927,BREAK:1928,ELSE:1930,WHILE:1931,IF:1932,BREAK:1934,IF:1936,IF:1938,BREAK:1939,ELSE:1941"
  },
  "call_chain": [],
  "types": {
   "entity_type": "unsigned char*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "s2",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/file/address/2b66ae67281848c411000005936bbbbf5acb459e/ARVO-42484477/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/file_2b66ae672818.cpg",
   "testcase_size": 2
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "strlen--file_strncmp--magiccheck"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*eb = b + (ws ? strlen(s2) : len)",
     "line": 1917
    }
   ],
   "entity_decl": {
    "line": 1917,
    "type": "unsigned char*"
   },
   "entity_name_cpg": "eb",
   "func_lines": [
    1904,
    1972
   ],
   "func_params": {
    "names": [
     "s1",
     "s2",
     "len",
     "flags"
    ],
    "types": [
     "char*",
     "char*",
     "size_t",
     "uint32_t"
    ]
   },
   "guards": [
    {
     "code": "0L == flags",
     "line": 1925
    },
    {
     "code": "len-- > 0",
     "line": 1926
    },
    {
     "code": "(v = *b++ - *a++) != '\\0'",
     "line": 1927
    },
    {
     "code": "len-- > 0",
     "line": 1931
    },
    {
     "code": "(v = tolower(*b++) - *a++) != '\\0'",
     "line": 1938
    },
    {
     "code": "(v = toupper(*b++) - *a++) != '\\0'",
     "line": 1943
    },
    {
     "code": "b < eb",
     "line": 1951
    },
    {
     "code": "b < eb",
     "line": 1962
    },
    {
     "code": "(v = *b++ - *a++) != '\\0'",
     "line": 1966
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "*eb = b + (ws ? strlen(s2) : len)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "b + (ws ? strlen(s2) : len)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "ws ? strlen(s2) : len",
     "name": "<operator>.conditional",
     "nargs": 3
    },
    {
     "code": "strlen(s2)",
     "name": "strlen",
     "nargs": 1
    }
   ],
   "line_ids": [
    "eb",
    "b",
    "ws",
    "s2",
    "len"
   ],
   "osv_id": "ARVO-42484477",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "file_strncmp"
  }
 },
 {
  "osv_id": "ARVO-42484593",
  "project": "perfetto",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "invoking_method_reply_",
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "std::__1::__libcpp_allocate(unsigned long, unsigned long)",
    "file": "/usr/local/bin/../include/c++/v1/new",
    "line": 253
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 263,
    "fn": "perfetto::trace_processor::ClockTracker::ConvertSlowpath(unsigned long, long, unsigned long)",
    "code": "invoking_method_reply_ = false",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "perfetto::trace_processor::ClockTracker::ConvertSlowpath(unsigned long, long, unsigned long)",
    "file": "/src/perfetto/src/trace_processor/importers/common/clock_tracker.cc",
    "line": 263
   },
   "code": "invoking_method_reply_ = false",
   "access": {
    "dir": "READ",
    "width": 8,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "OnInvokeMethodReply",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:247,IF:250,FOR:252,IF:253,BREAK:255,IF:267"
  },
  "call_chain": [],
  "types": {
   "entity_type": null,
   "cast_present": null,
   "is_signed": null
  },
  "input_reachability": [],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/perfetto/address/3755aca72039c54e42fded4b16a1f2ac2c48fbf5/ARVO-42484593/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/perfetto_3755aca72039.cpg",
   "testcase_size": 362
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
   "dedup_token": "perfetto::trace_processor::ClockTracker::ConvertSlowpath(unsigned long, long, unsigned long)--perfetto::trace_processor::ClockTracker::Convert(unsigned long, lo"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "invoking_method_reply_ = true",
     "line": 260
    },
    {
     "code": "invoking_method_reply_ = false",
     "line": 263
    }
   ],
   "entity_name_cpg": "invoking_method_reply_",
   "func_lines": [
    244,
    269
   ],
   "func_params": {
    "names": [
     "req",
     "reply"
    ],
    "types": [
     "QueuedRequest",
     "Frame.InvokeMethodReply&"
    ]
   },
   "guards": [
    {
     "code": "req.method_name == method.name",
     "line": 253
    }
   ],
   "line_call_count": 1,
   "line_calls": [
    {
     "code": "invoking_method_reply_ = false",
     "name": "<operator>.assignment",
     "nargs": 2
    }
   ],
   "line_ids": [
    "invoking_method_reply_"
   ],
   "osv_id": "ARVO-42484593",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "perfetto::trace_processor::ClockTracker::ConvertSlowpath(unsigned long, long, unsigned long)"
  }
 },
 {
  "osv_id": "ARVO-42484867",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 4783,
    "size": null,
    "type": "ndpi_packet_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "4",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 4804,
    "fn": "ndpi_parse_packet_line_info",
    "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a) | get_u_int16_t(packet->payload, a+2) | packet->payload | a+2",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_parse_packet_line_info",
    "file": "/src/ndpi/src/lib/ndpi_main.c",
    "line": 4804
   },
   "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a) | get_u_int16_t(packet->payload, a+2) | packet->payload | a+2",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_parse_packet_line_info",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "a < packet->payload_packet_len",
   "guard_count": 1,
   "control_structures": "IF:4785,IF:4788,FOR:4797,IF:4798,IF:4801,IF:4804,IF:4811,IF:4821,IF:4830,IF:4839,IF:4845,IF:4849"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_packet_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/cd765c08d6f1038ea5efd7a7cc556ca89bdec9e4/ARVO-42484867/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_cd765c08d6f1.cpg",
   "testcase_size": 186
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
   "dedup_token": "ndpi_parse_packet_line_info--ndpi_int_search_bittorrent_tcp_zero--check_ndpi_tcp_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "*packet = &flow->packet",
     "line": 4783
    },
    {
     "code": "packet->packet_lines_parsed_complete = 1",
     "line": 4791
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr = packet->payload",
     "line": 4794
    },
    {
     "code": "packet->line[packet->parsed_lines].len = 0",
     "line": 4795
    },
    {
     "code": "packet->line[packet->parsed_lines].len =",
     "line": 4817
    },
    {
     "code": "packet->http_response.ptr = &packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.1 \")]",
     "line": 4825
    },
    {
     "code": "packet->http_response.len = packet->line[0].len - NDPI_STATICSTRING_LEN(\"HTTP/1.1 \")",
     "line": 4826
    },
    {
     "code": "packet->server_line.ptr =",
     "line": 4850
    },
    {
     "code": "packet->server_line.len =",
     "line": 4852
    },
    {
     "code": "packet->server_line.ptr = &packet->line[packet->parsed_lines].ptr[NDPI_STATICSTRING_LEN(\"Server:\")]",
     "line": 4855
    },
    {
     "code": "packet->server_line.len = packet->line[packet->parsed_lines].len - NDPI_STATICSTRING_LEN(\"Server:\")",
     "line": 4856
    },
    {
     "code": "packet->host_line.ptr = &packet->line[packet->parsed_lines].ptr[6]",
     "line": 4865
    },
    {
     "code": "packet->host_line.len = packet->line[packet->parsed_lines].len - 6",
     "line": 4866
    },
    {
     "code": "packet->host_line.ptr = &packet->line[packet->parsed_lines].ptr[5]",
     "line": 4868
    },
    {
     "code": "packet->host_line.len = packet->line[packet->parsed_lines].len - 5",
     "line": 4869
    },
    {
     "code": "packet->forwarded_line.ptr = &packet->line[packet->parsed_lines].ptr[17]",
     "line": 4878
    },
    {
     "code": "packet->forwarded_line.len = packet->line[packet->parsed_lines].len - 17",
     "line": 4879
    },
    {
     "code": "packet->forwarded_line.ptr = &packet->line[packet->parsed_lines].ptr[16]",
     "line": 4881
    },
    {
     "code": "packet->forwarded_line.len = packet->line[packet->parsed_lines].len - 16",
     "line": 4882
    },
    {
     "code": "packet->content_line.ptr = &packet->line[packet->parsed_lines].ptr[14]",
     "line": 4890
    },
    {
     "code": "packet->content_line.len = packet->line[packet->parsed_lines].len - 14",
     "line": 4891
    },
    {
     "code": "packet->content_line.ptr = &packet->line[packet->parsed_lines].ptr[13]",
     "line": 4901
    },
    {
     "code": "packet->content_line.len = packet->line[packet->parsed_lines].len - 13",
     "line": 4902
    },
    {
     "code": "packet->content_line.len = c - (char *) packet->content_line.ptr",
     "line": 4915
    },
    {
     "code": "packet->accept_line.ptr = &packet->line[packet->parsed_lines].ptr[8]",
     "line": 4922
    },
    {
     "code": "packet->accept_line.len = packet->line[packet->parsed_lines].len - 8",
     "line": 4923
    },
    {
     "code": "packet->referer_line.ptr = &packet->line[packet->parsed_lines].ptr[9]",
     "line": 4929
    },
    {
     "code": "packet->referer_line.len = packet->line[packet->parsed_lines].len - 9",
     "line": 4930
    },
    {
     "code": "packet->user_agent_line.ptr = &packet->line[packet->parsed_lines].ptr[12]",
     "line": 4937
    },
    {
     "code": "packet->user_agent_line.len = packet->line[packet->parsed_lines].len - 12",
     "line": 4938
    },
    {
     "code": "packet->http_encoding.ptr = &packet->line[packet->parsed_lines].ptr[18]",
     "line": 4944
    },
    {
     "code": "packet->http_encoding.len = packet->line[packet->parsed_lines].len - 18",
     "line": 4945
    },
    {
     "code": "packet->http_transfer_encoding.ptr = &packet->line[packet->parsed_lines].ptr[19]",
     "line": 4951
    },
    {
     "code": "packet->http_transfer_encoding.len = packet->line[packet->parsed_lines].len - 19",
     "line": 4952
    },
    {
     "code": "packet->http_contentlen.ptr = &packet->line[packet->parsed_lines].ptr[16]",
     "line": 4959
    },
    {
     "code": "packet->http_contentlen.len = packet->line[packet->parsed_lines].len - 16",
     "line": 4960
    },
    {
     "code": "packet->http_cookie.ptr = &packet->line[packet->parsed_lines].ptr[8]",
     "line": 4966
    },
    {
     "code": "packet->http_cookie.len = packet->line[packet->parsed_lines].len - 8",
     "line": 4967
    },
    {
     "code": "packet->http_origin.ptr = &packet->line[packet->parsed_lines].ptr[8]",
     "line": 4973
    },
    {
     "code": "packet->http_origin.len = packet->line[packet->parsed_lines].len - 8",
     "line": 4974
    },
    {
     "code": "packet->http_x_session_type.ptr = &packet->line[packet->parsed_lines].ptr[16]",
     "line": 4980
    },
    {
     "code": "packet->http_x_session_type.len = packet->line[packet->parsed_lines].len - 16",
     "line": 4981
    },
    {
     "code": "packet->empty_line_position = a",
     "line": 5016
    },
    {
     "code": "packet->empty_line_position_set = 1",
     "line": 5017
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr = &packet->payload[a + 2]",
     "line": 5024
    },
    {
     "code": "packet->line[packet->parsed_lines].len = 0",
     "line": 5025
    },
    {
     "code": "packet->line[packet->parsed_lines].len =",
     "line": 5032
    }
   ],
   "entity_decl": {
    "line": 4783,
    "type": "ndpi_packet_struct*"
   },
   "entity_name_cpg": "packet",
   "func_lines": [
    4781,
    5037
   ],
   "func_params": {
    "names": [
     "ndpi_str",
     "flow"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*"
    ]
   },
   "guards": [
    {
     "code": "packet->payload_packet_len < 3",
     "line": 4785
    },
    {
     "code": "packet->payload == NULL",
     "line": 4785
    },
    {
     "code": "packet->packet_lines_parsed_complete != 0",
     "line": 4788
    },
    {
     "code": "a < packet->payload_packet_len",
     "line": 4797
    },
    {
     "code": "packet->parsed_lines < NDPI_MAX_PARSE_LINES_PER_PACKET",
     "line": 4797
    },
    {
     "code": "get_u_int16_t(packet->payload, a) == ntohs(0x0d0a)",
     "line": 4801
    },
    {
     "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a)",
     "line": 4804
    },
    {
     "code": "diff > 0",
     "line": 4811
    },
    {
     "code": "packet->parsed_lines == 0",
     "line": 4821
    },
    {
     "code": "strncasecmp((const char *) packet->line[0].ptr, \"HTTP/1.\", NDPI_STATICSTRING_LEN(\"HTTP/1.\")) == 0",
     "line": 4822
    },
    {
     "code": "packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.X \")] > '0'",
     "line": 4823
    },
    {
     "code": "packet->line[0].ptr[NDPI_STATICSTRING_LEN(\"HTTP/1.X \")] < '6'",
     "line": 4824
    },
    {
     "code": "flow->http.response_status_code < 100",
     "line": 4839
    },
    {
     "code": "flow->http.response_status_code > 509",
     "line": 4839
    },
    {
     "code": "packet->line[packet->parsed_lines].len > NDPI_STATICSTRING_LEN(\"Server:\") + 1",
     "line": 4845
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr,",
     "line": 4846
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[NDPI_STATICSTRING_LEN(\"Server:\")] == ' '",
     "line": 4849
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 6",
     "line": 4861
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Host:\", 5) == 0",
     "line": 4862
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[5] == ' '",
     "line": 4864
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 17",
     "line": 4874
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"X-Forwarded-For:\", 16) == 0",
     "line": 4875
    },
    {
     "code": "packet->line[packet->parsed_lines].ptr[16] == ' '",
     "line": 4877
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 14",
     "line": 4887
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Type: \", 14) == 0",
     "line": 4888
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-type: \", 14) == 0",
     "line": 4889
    },
    {
     "code": "packet->content_line.len > 0",
     "line": 4893
    },
    {
     "code": "packet->content_line.ptr[0] == ' '",
     "line": 4893
    },
    {
     "code": "packet->content_line.len == 0",
     "line": 4899
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 13",
     "line": 4899
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-type:\", 13) == 0",
     "line": 4900
    },
    {
     "code": "packet->content_line.len > 0",
     "line": 4906
    },
    {
     "code": "separator[i] != '\\0'",
     "line": 4911
    },
    {
     "code": "c != NULL",
     "line": 4914
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4920
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept: \", 8) == 0",
     "line": 4921
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 9",
     "line": 4927
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Referer: \", 9) == 0",
     "line": 4928
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 12",
     "line": 4934
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"User-Agent: \", 12) == 0",
     "line": 4935
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"User-agent: \", 12) == 0",
     "line": 4936
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 18",
     "line": 4942
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Encoding: \", 18) == 0",
     "line": 4943
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 19",
     "line": 4949
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Transfer-Encoding: \", 19) == 0",
     "line": 4950
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 16",
     "line": 4956
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Content-Length: \", 16) == 0",
     "line": 4957
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"content-length: \", 16) == 0",
     "line": 4958
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4964
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Cookie: \", 8) == 0",
     "line": 4965
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4971
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Origin: \", 8) == 0",
     "line": 4972
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 16",
     "line": 4978
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"X-Session-Type: \", 16) == 0",
     "line": 4979
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 6",
     "line": 4990
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Date: \", 6) == 0",
     "line": 4991
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Vary: \", 6) == 0",
     "line": 4992
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"ETag: \", 6) == 0",
     "line": 4993
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 8",
     "line": 4994
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Pragma: \", 8) == 0",
     "line": 4995
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 9",
     "line": 4996
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Expires: \", 9) == 0",
     "line": 4997
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 12",
     "line": 4998
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Set-Cookie: \", 12) == 0",
     "line": 4999
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Keep-Alive: \", 12) == 0",
     "line": 5000
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Connection: \", 12) == 0",
     "line": 5001
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 15",
     "line": 5002
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Last-Modified: \", 15) == 0",
     "line": 5003
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Ranges: \", 15) == 0",
     "line": 5004
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 17",
     "line": 5005
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Language: \", 17) == 0",
     "line": 5006
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr, \"Accept-Encoding: \", 17) == 0",
     "line": 5007
    },
    {
     "code": "packet->line[packet->parsed_lines].len > 27",
     "line": 5008
    },
    {
     "code": "strncasecmp((const char *) packet->line[packet->parsed_lines].ptr,",
     "line": 5009
    },
    {
     "code": "packet->line[packet->parsed_lines].len == 0",
     "line": 5015
    }
   ],
   "line_call_count": 5,
   "line_calls": [
    {
     "code": "get_u_int16_t(packet->payload, a+2) == ntohs(0x0d0a)",
     "name": "<operator>.equals",
     "nargs": 2
    },
    {
     "code": "get_u_int16_t(packet->payload, a+2)",
     "name": "get_u_int16_t",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "a+2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "ntohs(0x0d0a)",
     "name": "ntohs",
     "nargs": 1
    }
   ],
   "line_ids": [
    "packet",
    "a"
   ],
   "osv_id": "ARVO-42484867",
   "sites": [
    {
     "args": "4",
     "callee": "<operator>.alloc",
     "code": "buf[4]",
     "line": 4831
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_parse_packet_line_info"
  }
 },
 {
  "osv_id": "ARVO-42484909",
  "project": "leptonica",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "val",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/ccbord.c",
    "line": 1083,
    "size": null,
    "type": "l_int32"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pixCreateNoInit",
    "file": "/src/leptonica/src/pix1.c",
    "line": 345
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 1092,
    "fn": "findNextBorderPixel",
    "code": "val = GET_DATA_BIT(line, npx) | GET_DATA_BIT(line, npx) | (*((const l_uint32 *)(line) + ((npx) >> 5)) >> (31 - ((n | *((const l_uint32 *)(line) + ((npx) >> 5)) >> (31 - ((np",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "findNextBorderPixel",
    "file": "/src/leptonica/src/ccbord.c",
    "line": 1092
   },
   "code": "val = GET_DATA_BIT(line, npx) | GET_DATA_BIT(line, npx) | (*((const l_uint32 *)(line) + ((npx) >> 5)) >> (31 - ((n | *((const l_uint32 *)(line) + ((npx) >> 5)) >> (31 - ((np",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "findNextBorderPixel",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "FOR:1087,IF:1093"
  },
  "call_chain": [],
  "types": {
   "entity_type": "l_int32",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "data",
   "wpl",
   "px",
   "py",
   "pnpx",
   "pnpy"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/56315e1081efde6e14b88840d53876816fb2a7ca/ARVO-42484909/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_56315e1081ef.cpg",
   "testcase_size": 548
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
   "dedup_token": "findNextBorderPixel--pixGetHoleBorder--pixGetCCBorders"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "val = GET_DATA_BIT(line, npx)",
     "line": 1092
    }
   ],
   "entity_decl": {
    "line": 1083,
    "type": "l_int32"
   },
   "entity_name_cpg": "val",
   "func_lines": [
    1072,
    1102
   ],
   "func_params": {
    "names": [
     "w",
     "h",
     "data",
     "wpl",
     "px",
     "py",
     "pqpos",
     "pnpx",
     "pnpy"
    ],
    "types": [
     "l_int32",
     "l_int32",
     "l_uint32*",
     "l_int32",
     "l_int32",
     "l_int32",
     "l_int32*",
     "l_int32*",
     "l_int32*"
    ]
   },
   "guards": [
    {
     "code": "i < 8",
     "line": 1087
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "val = GET_DATA_BIT(line, npx)",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "GET_DATA_BIT(line, npx)",
     "name": "GET_DATA_BIT",
     "nargs": 2
    },
    {
     "code": "(*((const l_uint32 *)(line) + ((npx) >> 5)) >> (31 - ((npx) & 31))) & 1",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "*((const l_uint32 *)(line) + ((npx) >> 5)) >> (31 - ((npx) & 31))",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "*((const l_uint32 *)(line) + ((npx) >> 5))",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(const l_uint32 *)(line) + ((npx) >> 5)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(const l_uint32 *)(line)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(npx) >> 5",
     "name": "<operator>.arithmeticShiftRight",
     "nargs": 2
    },
    {
     "code": "31 - ((npx) & 31)",
     "name": "<operator>.subtraction",
     "nargs": 2
    },
    {
     "code": "(npx) & 31",
     "name": "<operator>.and",
     "nargs": 2
    }
   ],
   "line_ids": [
    "val",
    "line",
    "npx"
   ],
   "osv_id": "ARVO-42484909",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "findNextBorderPixel"
  }
 },
 {
  "osv_id": "ARVO-42485153",
  "project": "leptonica",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "ppixel",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/leptonica/src/tiffio.c",
    "line": 482,
    "size": null,
    "type": "l_uint32*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "pixReadFromTiffStream",
    "file": "/src/leptonica/src/tiffio.c",
    "line": 594
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": false,
   "size_expr_cpg": "",
   "size_expr_cpg_callee": "LEPT_CALLOC"
  },
  "sites": [
   {
    "code": "calloc(tiffbpl + 1, sizeof (l_uint8))",
    "fn": "pixReadFromTiffStream",
    "kind": "calloc",
    "line": 576,
    "origin": "cpg",
    "args": "tiffbpl + 1 ;; sizeof (l_uint8)"
   },
   {
    "code": "calloc(tiffbpl + 1, sizeof (l_uint8))",
    "fn": "pixReadFromTiffStream",
    "kind": "calloc",
    "line": 594,
    "origin": "cpg",
    "args": "tiffbpl + 1 ;; sizeof (l_uint8)"
   },
   {
    "kind": "unknown",
    "line": 606,
    "fn": "pixReadFromTiffStream",
    "code": "SET_DATA_BYTE(ppixel, COLOR_RED, rowptr[k]) | rowptr[k] | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_ | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_",
    "origin": "report:crash"
   },
   {
    "code": "calloc((size_t)w * h, sizeof (l_uint32))",
    "fn": "pixReadFromTiffStream",
    "kind": "calloc",
    "line": 615,
    "origin": "cpg",
    "args": "(size_t)w * h ;; sizeof (l_uint32)"
   }
  ],
  "crash": {
   "site": {
    "fn": "pixReadFromTiffStream",
    "file": "/src/leptonica/src/tiffio.c",
    "line": 606
   },
   "code": "SET_DATA_BYTE(ppixel, COLOR_RED, rowptr[k]) | rowptr[k] | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_ | *(l_uint8 *)((l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "pixReadFromTiffStream",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0,
   "control_structures": "IF:488,IF:499,IF:509,IF:522,IF:530,IF:534,IF:538,ELSE:540,IF:540,ELSE:542,IF:542,ELSE:545"
  },
  "call_chain": [],
  "types": {
   "entity_type": "l_uint32*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "tif"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/leptonica/address/26425b91ea850552d11af0ead0557eb0a328785f/ARVO-42485153/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/leptonica_26425b91ea85.cpg",
   "testcase_size": 4093
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
   "dedup_token": "pixReadFromTiffStream--pixReadMemTiff--pixReadMem"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "ppixel = pixdata + i * wpl",
     "line": 603
    },
    {
     "code": "ppixel = line",
     "line": 633
    }
   ],
   "entity_decl": {
    "line": 482,
    "type": "l_uint32*"
   },
   "entity_name_cpg": "ppixel",
   "func_lines": [
    472,
    725
   ],
   "func_params": {
    "names": [
     "tif"
    ],
    "types": [
     "TIFF*"
    ]
   },
   "guards": [
    {
     "code": "sample_fmt != SAMPLEFORMAT_UINT",
     "line": 499
    },
    {
     "code": "tiffcomp == COMPRESSION_OJPEG",
     "line": 522
    },
    {
     "code": "bps != 1",
     "line": 530
    },
    {
     "code": "bps != 2",
     "line": 530
    },
    {
     "code": "bps != 4",
     "line": 530
    },
    {
     "code": "bps != 8",
     "line": 530
    },
    {
     "code": "bps != 16",
     "line": 530
    },
    {
     "code": "spp == 2",
     "line": 534
    },
    {
     "code": "bps != 8",
     "line": 534
    },
    {
     "code": "spp == 1",
     "line": 538
    },
    {
     "code": "spp == 2",
     "line": 540
    },
    {
     "code": "spp == 3",
     "line": 542
    },
    {
     "code": "spp == 4",
     "line": 542
    },
    {
     "code": "w > MaxTiffWidth",
     "line": 549
    },
    {
     "code": "h > MaxTiffHeight",
     "line": 553
    },
    {
     "code": "packedbpl == 2 * tiffbpl",
     "line": 559
    },
    {
     "code": "tiffbpl != packedbpl",
     "line": 562
    },
    {
     "code": "2 * tiffbpl != packedbpl",
     "line": 562
    },
    {
     "code": "(pix = pixCreate(w, h, d)) == NULL",
     "line": 568
    },
    {
     "code": "spp == 1",
     "line": 575
    },
    {
     "code": "i < h",
     "line": 577
    },
    {
     "code": "TIFFReadScanline(tif, linebuf, i, 0) < 0",
     "line": 578
    },
    {
     "code": "spp == 2",
     "line": 591
    },
    {
     "code": "bps == 8",
     "line": 591
    },
    {
     "code": "i < h",
     "line": 596
    },
    {
     "code": "TIFFReadScanline(tif, linebuf, i, 0) < 0",
     "line": 597
    },
    {
     "code": "j < w",
     "line": 604
    },
    {
     "code": "(tiffdata = (l_uint32 *)LEPT_CALLOC((size_t)w * h,",
     "line": 615
    },
    {
     "code": "spp == 4",
     "line": 630
    },
    {
     "code": "i < h",
     "line": 632
    },
    {
     "code": "j < w",
     "line": 633
    },
    {
     "code": "spp == 3",
     "line": 639
    },
    {
     "code": "getTiffStreamResolution(tif, &xres, &yres) == 0",
     "line": 651
    },
    {
     "code": "bps > 8",
     "line": 665
    },
    {
     "code": "(cmap = pixcmapCreate(bps)) == NULL",
     "line": 669
    },
    {
     "code": "i < ncolors",
     "line": 674
    },
    {
     "code": "bps == 1",
     "line": 683
    },
    {
     "code": "tiffcomp == COMPRESSION_CCITTFAX3",
     "line": 692
    },
    {
     "code": "tiffcomp == COMPRESSION_CCITTFAX4",
     "line": 693
    },
    {
     "code": "tiffcomp == COMPRESSION_CCITTRLE",
     "line": 694
    },
    {
     "code": "tiffcomp == COMPRESSION_CCITTRLEW",
     "line": 695
    },
    {
     "code": "d == 1",
     "line": 701
    },
    {
     "code": "photometry == PHOTOMETRIC_MINISBLACK",
     "line": 701
    },
    {
     "code": "d == 8",
     "line": 702
    },
    {
     "code": "photometry == PHOTOMETRIC_MINISWHITE",
     "line": 702
    }
   ],
   "line_call_count": 10,
   "line_calls": [
    {
     "code": "SET_DATA_BYTE(ppixel, COLOR_RED, rowptr[k])",
     "name": "SET_DATA_BYTE",
     "nargs": 3
    },
    {
     "code": "rowptr[k]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "*(l_uint8 *)((l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_RED)) ^ 3) = (rowptr[k])",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "*(l_uint8 *)((l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_RED)) ^ 3)",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "(l_uint8 *)((l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_RED)) ^ 3)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_RED)) ^ 3",
     "name": "<operator>.xor",
     "nargs": 2
    },
    {
     "code": "(l_uintptr_t)((l_uint8 *)(ppixel) + (COLOR_RED))",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "(l_uint8 *)(ppixel) + (COLOR_RED)",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "(l_uint8 *)(ppixel)",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "rowptr[k]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    }
   ],
   "line_ids": [
    "ppixel",
    "COLOR_RED",
    "rowptr",
    "k"
   ],
   "osv_id": "ARVO-42485153",
   "sites": [
    {
     "args": "",
     "callee": "LEPT_CALLOC",
     "code": "LEPT_CALLOC(tiffbpl + 1, sizeof(l_uint8))",
     "line": 576
    },
    {
     "args": "tiffbpl + 1 ;; sizeof (l_uint8)",
     "callee": "calloc",
     "code": "calloc(tiffbpl + 1, sizeof (l_uint8))",
     "line": 576
    },
    {
     "args": "linebuf",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(linebuf)",
     "line": 579
    },
    {
     "args": "linebuf",
     "callee": "free",
     "code": "free(linebuf)",
     "line": 579
    },
    {
     "args": "linebuf",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(linebuf)",
     "line": 590
    },
    {
     "args": "linebuf",
     "callee": "free",
     "code": "free(linebuf)",
     "line": 590
    },
    {
     "args": "",
     "callee": "LEPT_CALLOC",
     "code": "LEPT_CALLOC(tiffbpl + 1, sizeof(l_uint8))",
     "line": 594
    },
    {
     "args": "tiffbpl + 1 ;; sizeof (l_uint8)",
     "callee": "calloc",
     "code": "calloc(tiffbpl + 1, sizeof (l_uint8))",
     "line": 594
    },
    {
     "args": "linebuf",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(linebuf)",
     "line": 598
    },
    {
     "args": "linebuf",
     "callee": "free",
     "code": "free(linebuf)",
     "line": 598
    },
    {
     "args": "linebuf",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(linebuf)",
     "line": 613
    },
    {
     "args": "linebuf",
     "callee": "free",
     "code": "free(linebuf)",
     "line": 613
    },
    {
     "args": null,
     "callee": "LEPT_CALLOC",
     "code": "LEPT_CALLOC((size_t)w * h,",
     "line": 615
    },
    {
     "args": "(size_t)w * h ;; sizeof (l_uint32)",
     "callee": "calloc",
     "code": "calloc((size_t)w * h, sizeof (l_uint32))",
     "line": 615
    },
    {
     "args": "tiffdata",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(tiffdata)",
     "line": 623
    },
    {
     "args": "tiffdata",
     "callee": "free",
     "code": "free(tiffdata)",
     "line": 623
    },
    {
     "args": "tiffdata",
     "callee": "LEPT_FREE",
     "code": "LEPT_FREE(tiffdata)",
     "line": 648
    },
    {
     "args": "tiffdata",
     "callee": "free",
     "code": "free(tiffdata)",
     "line": 648
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "pixReadFromTiffStream"
  }
 },
 {
  "osv_id": "ARVO-42485350",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "packet_len",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/iax.c",
    "line": 44,
    "size": null,
    "type": "u_int16_t"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2082f)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 70,
    "fn": "ndpi_search_setup_iax",
    "code": "packet_len = packet_len + 2 + packet->payload[packet_len | packet_len + 2 + packet->payload[packet_len + 1] | packet_len + 2 | packet->payload[packet_len + 1]",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "ndpi_search_setup_iax",
    "file": "/src/ndpi/src/lib/protocols/iax.c",
    "line": 70
   },
   "code": "packet_len = packet_len + 2 + packet->payload[packet_len | packet_len + 2 + packet->payload[packet_len + 1] | packet_len + 2 | packet->payload[packet_len + 1]",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "ndpi_search_setup_iax",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "packet_len == packet->payload_packet_len | packet_len > packet->payload_packet_len",
   "guard_count": 2,
   "control_structures": "IF:46,IF:63,FOR:69,IF:71,IF:76,BREAK:77"
  },
  "call_chain": [],
  "types": {
   "entity_type": "u_int16_t",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "flow"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/9dfd0d0071845779487b4e2e14c3599e18a74a8c/ARVO-42485350/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_9dfd0d007184.cpg",
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
   "dedup_token": "ndpi_search_setup_iax--ndpi_search_iax--check_ndpi_udp_flow_func"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "packet_len = 12",
     "line": 68
    },
    {
     "code": "packet_len = packet_len + 2 + packet->payload[packet_len + 1]",
     "line": 70
    }
   ],
   "entity_decl": {
    "line": 44,
    "type": "u_int16_t"
   },
   "entity_name_cpg": "packet_len",
   "func_lines": [
    40,
    85
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*"
    ]
   },
   "guards": [
    {
     "code": "packet->udp->source == htons(4569)",
     "line": 47
    },
    {
     "code": "packet->udp->dest == htons(4569)",
     "line": 47
    },
    {
     "code": "(packet->payload[0] & 0x80) != 0",
     "line": 53
    },
    {
     "code": "packet->payload[8] == 0",
     "line": 55
    },
    {
     "code": "packet->payload[9] == 0",
     "line": 57
    },
    {
     "code": "packet->payload[9] == 0x01",
     "line": 57
    },
    {
     "code": "packet->payload[10] == 0x06",
     "line": 59
    },
    {
     "code": "packet->payload_packet_len == 12",
     "line": 63
    },
    {
     "code": "i < NDPI_IAX_MAX_INFORMATION_ELEMENTS",
     "line": 69
    },
    {
     "code": "packet_len == packet->payload_packet_len",
     "line": 71
    },
    {
     "code": "packet_len > packet->payload_packet_len",
     "line": 76
    }
   ],
   "line_call_count": 6,
   "line_calls": [
    {
     "code": "packet_len = packet_len + 2 + packet->payload[packet_len + 1]",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "packet_len + 2 + packet->payload[packet_len + 1]",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "packet_len + 2",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "packet->payload[packet_len + 1]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "packet->payload",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "packet_len + 1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "packet_len",
    "packet"
   ],
   "osv_id": "ARVO-42485350",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "ndpi_search_setup_iax"
  }
 },
 {
  "osv_id": "ARVO-42486467",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "r",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/c-blosc2/internal-complibs/miniz-2.0.8/miniz.c",
    "line": 2339,
    "size": null,
    "type": "tinfl_decompressor*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib32/libc.so.6+0x18646)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "31",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 2374,
    "fn": "tinfl_decompress",
    "code": "TINFL_GET_BYTE(1, r->m_zhdr0) | r->m_zhdr0 | pIn_buf_cur >= pIn_buf_end | status = (decomp_flags & TINFL_FLAG_HAS_MORE_INPUT) ? TI",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "tinfl_decompress",
    "file": "/src/c-blosc2/internal-complibs/miniz-2.0.8/miniz.c",
    "line": 2374
   },
   "code": "TINFL_GET_BYTE(1, r->m_zhdr0) | r->m_zhdr0 | pIn_buf_cur >= pIn_buf_end | status = (decomp_flags & TINFL_FLAG_HAS_MORE_INPUT) ? TI",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "tinfl_decompress",
   "in_loop": true,
   "loop_type": null,
   "loop_range": null,
   "guards": "pIn_buf_cur >= pIn_buf_end | pIn_buf_cur >= pIn_buf_end | pIn_buf_cur >= pIn_buf_end",
   "guard_count": 25,
   "control_structures": "IF:2356,SWITCH:2368,IF:2372,DO:2374,WHILE:2374,DO:2374,GOTO:2374,DO:2375,WHILE:2375,DO:2375,GOTO:2375,IF:2377"
  },
  "call_chain": [],
  "types": {
   "entity_type": "tinfl_decompressor*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "r",
   "pIn_buf_next",
   "pIn_buf_size",
   "decomp_flags"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/8de8821d78ac0f018e14804dece7dc00be70c05f/ARVO-42486467/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_8de8821d78ac.cpg",
   "testcase_size": 40
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
   "dedup_token": "tinfl_decompress--mz_inflate--mz_uncompress"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "r->m_zhdr0 = r->m_zhdr1 = 0",
     "line": 2370
    },
    {
     "code": "r->m_zhdr1 = 0",
     "line": 2370
    },
    {
     "code": "r->m_z_adler32 = r->m_check_adler32 = 1",
     "line": 2371
    },
    {
     "code": "r->m_check_adler32 = 1",
     "line": 2371
    },
    {
     "code": "r->m_state = 1",
     "line": 2374
    },
    {
     "code": "r->m_zhdr0 = *pIn_buf_cur++",
     "line": 2374
    },
    {
     "code": "r->m_state = 2",
     "line": 2375
    },
    {
     "code": "r->m_zhdr1 = *pIn_buf_cur++",
     "line": 2375
    },
    {
     "code": "r->m_state = 36",
     "line": 2381
    },
    {
     "code": "r->m_state = 3",
     "line": 2387
    },
    {
     "code": "r->m_final = bit_buf & ((1 << (3)) - 1)",
     "line": 2387
    },
    {
     "code": "r->m_type = r->m_final >> 1",
     "line": 2388
    },
    {
     "code": "r->m_state = 5",
     "line": 2391
    },
    {
     "code": "r->m_state = 6",
     "line": 2395
    },
    {
     "code": "r->m_raw_header[counter] = bit_buf & ((1 << (8)) - 1)",
     "line": 2395
    },
    {
     "code": "r->m_state = 7",
     "line": 2397
    },
    {
     "code": "r->m_raw_header[counter] = *pIn_buf_cur++",
     "line": 2397
    },
    {
     "code": "r->m_state = 39",
     "line": 2401
    },
    {
     "code": "r->m_state = 51",
     "line": 2405
    },
    {
     "code": "r->m_state = 52",
     "line": 2408
    },
    {
     "code": "r->m_state = 9",
     "line": 2418
    },
    {
     "code": "r->m_state = 38",
     "line": 2422
    },
    {
     "code": "r->m_state = 10",
     "line": 2433
    },
    {
     "code": "r->m_table_sizes[0] = 288",
     "line": 2441
    },
    {
     "code": "r->m_table_sizes[1] = 32",
     "line": 2442
    },
    {
     "code": "r->m_state = 11",
     "line": 2457
    },
    {
     "code": "r->m_table_sizes[counter] = bit_buf & ((1 << (\"\\05\\05\\04\"[counter])) - 1)",
     "line": 2457
    },
    {
     "code": "r->m_state = 14",
     "line": 2464
    },
    {
     "code": "r->m_tables[2].m_code_size[s_length_dezigzag[counter]] = (mz_uint8)s",
     "line": 2465
    },
    {
     "code": "r->m_table_sizes[2] = 19",
     "line": 2467
    },
    {
     "code": "r->m_state = 35",
     "line": 2489
    },
    {
     "code": "r->m_state = 16",
     "line": 2536
    },
    {
     "code": "r->m_len_codes[counter++] = (mz_uint8)dist",
     "line": 2539
    },
    {
     "code": "r->m_state = 17",
     "line": 2544
    },
    {
     "code": "r->m_state = 18",
     "line": 2547
    },
    {
     "code": "r->m_state = 21",
     "line": 2554
    },
    {
     "code": "r->m_state = 23",
     "line": 2567
    },
    {
     "code": "r->m_state = 24",
     "line": 2572
    },
    {
     "code": "r->m_state = 25",
     "line": 2651
    },
    {
     "code": "r->m_state = 26",
     "line": 2655
    },
    {
     "code": "r->m_state = 27",
     "line": 2661
    },
    {
     "code": "r->m_state = 37",
     "line": 2668
    },
    {
     "code": "r->m_state = 53",
     "line": 2679
    },
    {
     "code": "r->m_state = 32",
     "line": 2730
    },
    {
     "code": "r->m_state = 41",
     "line": 2745
    },
    {
     "code": "r->m_state = 42",
     "line": 2747
    },
    {
     "code": "r->m_z_adler32 = (r->m_z_adler32 << 8) ",
     "line": 2748
    },
    {
     "code": "r->m_state = 34",
     "line": 2751
    },
    {
     "code": "r->m_num_bits = num_bits",
     "line": 2767
    },
    {
     "code": "r->m_bit_buf = bit_buf & (tinfl_bit_buf_t)((((mz_uint64)1) << num_bits) - (mz_uint64)1)",
     "line": 2768
    },
    {
     "code": "r->m_dist = dist",
     "line": 2769
    },
    {
     "code": "r->m_counter = counter",
     "line": 2770
    },
    {
     "code": "r->m_num_extra = num_extra",
     "line": 2771
    },
    {
     "code": "r->m_dist_from_out_buf_start = dist_from_out_buf_start",
     "line": 2772
    },
    {
     "code": "r->m_check_adler32 = (s2 << 16) + s1",
     "line": 2800
    }
   ],
   "entity_decl": {
    "line": 2339,
    "type": "tinfl_decompressor*"
   },
   "entity_name_cpg": "r",
   "func_lines": [
    2339,
    2805
   ],
   "func_params": {
    "names": [
     "r",
     "pIn_buf_next",
     "pIn_buf_size",
     "pOut_buf_start",
     "pOut_buf_next",
     "pOut_buf_size",
     "decomp_flags"
    ],
    "types": [
     "tinfl_decompressor*",
     "mz_uint8*",
     "size_t*",
     "mz_uint8*",
     "mz_uint8*",
     "size_t*",
     "mz_uint32"
    ]
   },
   "guards": [
    {
     "code": "pOut_buf_next < pOut_buf_start",
     "line": 2356
    },
    {
     "code": "(r->m_zhdr0 * 256 + r->m_zhdr1) % 31 != 0",
     "line": 2376
    },
    {
     "code": "(r->m_zhdr0 & 15) != 8",
     "line": 2376
    },
    {
     "code": "(1U << (8U + (r->m_zhdr0 >> 4))) > 32768U",
     "line": 2378
    },
    {
     "code": "(out_buf_size_mask + 1) < (size_t)(1U << (8U + (r->m_zhdr0 >> 4)))",
     "line": 2378
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2387
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2387
    },
    {
     "code": "r->m_type == 0",
     "line": 2389
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2391
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2391
    },
    {
     "code": "counter < 4",
     "line": 2392
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2395
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2395
    },
    {
     "code": "(counter = (r->m_raw_header[0] ",
     "line": 2399
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2405
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2405
    },
    {
     "code": "(((((size_t)(pOut_buf_end - pOut_buf_cur)) < ((size_t)(pIn_buf_end - pIn_buf_cur))) ? ((size_t)(pOut_buf_end - pOut_buf_cur)) : ((size_t)(pIn_buf_end",
     "line": 2424
    },
    {
     "code": "((size_t)(pOut_buf_end - pOut_buf_cur)) < ((size_t)(pIn_buf_end - pIn_buf_cur))",
     "line": 2424
    },
    {
     "code": "((size_t)(pOut_buf_end - pOut_buf_cur)) < ((size_t)(pIn_buf_end - pIn_buf_cur))",
     "line": 2424
    },
    {
     "code": "r->m_type == 3",
     "line": 2431
    },
    {
     "code": "r->m_type == 1",
     "line": 2437
    },
    {
     "code": "counter < 3",
     "line": 2455
    },
    {
     "code": "num_bits < (mz_uint)(\"\\05\\05\\04\"[counter])",
     "line": 2457
    },
    {
     "code": "num_bits < (mz_uint)(\"\\05\\05\\04\"[counter])",
     "line": 2457
    },
    {
     "code": "counter < r->m_table_sizes[2]",
     "line": 2461
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2464
    },
    {
     "code": "num_bits < (mz_uint)(3)",
     "line": 2464
    },
    {
     "code": "i < r->m_table_sizes[r->m_type]",
     "line": 2478
    },
    {
     "code": "65536 != total",
     "line": 2487
    },
    {
     "code": "used_syms > 1",
     "line": 2487
    },
    {
     "code": "sym_index < r->m_table_sizes[r->m_type]",
     "line": 2491
    },
    {
     "code": "l > 0",
     "line": 2497
    },
    {
     "code": "rev_code < TINFL_FAST_LOOKUP_SIZE",
     "line": 2502
    },
    {
     "code": "0 == (tree_cur = pTable->m_look_up[rev_code & (TINFL_FAST_LOOKUP_SIZE - 1)])",
     "line": 2509
    },
    {
     "code": "j > (TINFL_FAST_LOOKUP_BITS + 1)",
     "line": 2516
    },
    {
     "code": "r->m_type == 2",
     "line": 2531
    },
    {
     "code": "counter < (r->m_table_sizes[0] + r->m_table_sizes[1])",
     "line": 2533
    },
    {
     "code": "num_bits < 15",
     "line": 2536
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 2",
     "line": 2536
    },
    {
     "code": "num_bits > TINFL_FAST_LOOKUP_BITS",
     "line": 2536
    },
    {
     "code": "temp < 0",
     "line": 2536
    },
    {
     "code": "num_bits < 15",
     "line": 2536
    },
    {
     "code": "temp < 0",
     "line": 2536
    },
    {
     "code": "dist < 16",
     "line": 2537
    },
    {
     "code": "dist == 16",
     "line": 2542
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2547
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2547
    },
    {
     "code": "dist == 16",
     "line": 2549
    },
    {
     "code": "(r->m_table_sizes[0] + r->m_table_sizes[1]) != counter",
     "line": 2552
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 4",
     "line": 2565
    },
    {
     "code": "(pOut_buf_end - pOut_buf_cur) < 2",
     "line": 2565
    },
    {
     "code": "num_bits < 15",
     "line": 2567
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 2",
     "line": 2567
    },
    {
     "code": "num_bits > TINFL_FAST_LOOKUP_BITS",
     "line": 2567
    },
    {
     "code": "temp < 0",
     "line": 2567
    },
    {
     "code": "num_bits < 15",
     "line": 2567
    },
    {
     "code": "temp < 0",
     "line": 2567
    },
    {
     "code": "num_bits < 15",
     "line": 2588
    },
    {
     "code": "sym2 < 0",
     "line": 2603
    },
    {
     "code": "num_bits < 15",
     "line": 2612
    },
    {
     "code": "sym2 < 0",
     "line": 2627
    },
    {
     "code": "(counter &= 511) == 256",
     "line": 2643
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2651
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2651
    },
    {
     "code": "num_bits < 15",
     "line": 2655
    },
    {
     "code": "(pIn_buf_end - pIn_buf_cur) < 2",
     "line": 2655
    },
    {
     "code": "num_bits > TINFL_FAST_LOOKUP_BITS",
     "line": 2655
    },
    {
     "code": "temp < 0",
     "line": 2655
    },
    {
     "code": "num_bits < 15",
     "line": 2655
    },
    {
     "code": "temp < 0",
     "line": 2655
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2661
    },
    {
     "code": "num_bits < (mz_uint)(num_extra)",
     "line": 2661
    },
    {
     "code": "dist > dist_from_out_buf_start",
     "line": 2666
    },
    {
     "code": "(MZ_MAX(pOut_buf_cur, pSrc) + counter) > pOut_buf_end",
     "line": 2673
    },
    {
     "code": "(pOut_buf_cur) > (pSrc)",
     "line": 2673
    },
    {
     "code": "counter>2",
     "line": 2708
    },
    {
     "code": "counter > 0",
     "line": 2717
    },
    {
     "code": "counter > 1",
     "line": 2720
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2730
    },
    {
     "code": "num_bits < (mz_uint)(num_bits & 7)",
     "line": 2730
    },
    {
     "code": "pIn_buf_cur > pIn_buf_next",
     "line": 2731
    },
    {
     "code": "counter < 4",
     "line": 2741
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2745
    },
    {
     "code": "num_bits < (mz_uint)(8)",
     "line": 2745
    },
    {
     "code": "status != TINFL_STATUS_NEEDS_MORE_INPUT",
     "line": 2759
    },
    {
     "code": "status != TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS",
     "line": 2759
    },
    {
     "code": "pIn_buf_cur > pIn_buf_next",
     "line": 2761
    },
    {
     "code": "i + 7 < block_len",
     "line": 2783
    },
    {
     "code": "i < block_len",
     "line": 2794
    },
    {
     "code": "status == TINFL_STATUS_DONE",
     "line": 2801
    },
    {
     "code": "r->m_check_adler32 != r->m_z_adler32",
     "line": 2801
    }
   ],
   "line_call_count": 12,
   "line_calls": [
    {
     "code": "TINFL_GET_BYTE(1, r->m_zhdr0)",
     "name": "TINFL_GET_BYTE",
     "nargs": 2
    },
    {
     "code": "r->m_zhdr0",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "pIn_buf_cur >= pIn_buf_end",
     "name": "<operator>.greaterEqualsThan",
     "nargs": 2
    },
    {
     "code": "status = (decomp_flags & TINFL_FLAG_HAS_MORE_INPUT) ? TINFL_STATUS_NEEDS_MORE_INPUT : TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(decomp_flags & TINFL_FLAG_HAS_MORE_INPUT) ? TINFL_STATUS_NEEDS_MORE_INPUT : TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS",
     "name": "<operator>.conditional",
     "nargs": 3
    },
    {
     "code": "decomp_flags & TINFL_FLAG_HAS_MORE_INPUT",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "r->m_state = 1",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "r->m_state",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "r->m_zhdr0 = *pIn_buf_cur++",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "r->m_zhdr0",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "*pIn_buf_cur++",
     "name": "<operator>.indirection",
     "nargs": 1
    },
    {
     "code": "pIn_buf_cur++",
     "name": "<operator>.postIncrement",
     "nargs": 1
    }
   ],
   "line_ids": [
    "r",
    "pIn_buf_cur",
    "pIn_buf_end",
    "status",
    "decomp_flags",
    "TINFL_FLAG_HAS_MORE_INPUT",
    "TINFL_STATUS_NEEDS_MORE_INPUT",
    "TINFL_STATUS_FAILED_CANNOT_MAKE_PROGRESS"
   ],
   "osv_id": "ARVO-42486467",
   "sites": [
    {
     "args": "31",
     "callee": "<operator>.alloc",
     "code": "s_length_base[31] = { 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258, 0, 0 }",
     "line": 2341
    },
    {
     "args": "31",
     "callee": "<operator>.alloc",
     "code": "s_length_extra[31] = { 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0, 0, 0 }",
     "line": 2342
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "s_dist_base[32] = { 1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16",
     "line": 2343
    },
    {
     "args": "32",
     "callee": "<operator>.alloc",
     "code": "s_dist_extra[32] = { 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13 }",
     "line": 2344
    },
    {
     "args": "19",
     "callee": "<operator>.alloc",
     "code": "s_length_dezigzag[19] = { 16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15 }",
     "line": 2345
    },
    {
     "args": "3",
     "callee": "<operator>.alloc",
     "code": "s_min_table_sizes[3] = { 257, 1, 4 }",
     "line": 2346
    },
    {
     "args": "17",
     "callee": "<operator>.alloc",
     "code": "next_code[17]",
     "line": 2473
    },
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "total_syms[16]",
     "line": 2473
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "tinfl_decompress"
  }
 },
 {
  "osv_id": "ARVO-42486640",
  "project": "libheif",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "out_a",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": null,
    "line": 483,
    "type": "Pixel*",
    "size": null
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "heif::HeifPixelImage::add_plane(heif_channel, int, int, int)",
    "file": "/src/libheif/libheif/heif_image.cc",
    "line": 168
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 541,
    "fn": "Op_RGB_to_YCbCr<unsigned char>::convert_colorspace(std::__1::shared_ptr<heif::HeifPixelImage const> const&, heif::ColorState, heif::ColorConversionOptions)",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "Op_RGB_to_YCbCr<unsigned char>::convert_colorspace(std::__1::shared_ptr<heif::HeifPixelImage const> const&, heif::ColorState, heif::ColorConversionOptions)",
    "file": "/src/libheif/libheif/heif_colorconversion.cc",
    "line": 541
   },
   "code": "memcpy(&out_a[y*out_a_stride], &in_a[y*in_a_stride], width*2)",
   "access": {
    "dir": "READ",
    "width": 128,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "Op_RGB_to_YCbCr<unsigned char>::convert_colorspace(std::__1::shared_ptr<heif::HeifPixelImage const> const&, heif::ColorState, heif::ColorConversionOptions)",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/libheif/address/5258e9a093b86e827583d110300e9d7db150b9fa/ARVO-42486640/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/libheif_5258e9a093b8.cpg",
   "testcase_size": 817
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
   "shadow_byte": "07",
   "shadow_legend_size": 21,
   "dedup_token": "__asan_memcpy--Op_RGB_to_YCbCr<unsigned char>::convert_colorspace(std::__1::shared_ptr<heif::HeifPixelImage const> const&, heif::ColorState, heif::ColorConversi"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "out_a = (Pixel*)outimg->get_plane(heif_channel_Alpha, &out_a_stride)",
     "line": 495
    },
    {
     "code": "out_a = nullptr",
     "line": 499
    }
   ],
   "entity_decl": {
    "line": 483,
    "type": "Pixel*"
   },
   "entity_name_cpg": "out_a",
   "func_lines": [
    440,
    546
   ],
   "func_params": {
    "names": [
     "input",
     "target_state",
     "options"
    ],
    "types": [
     "std.shared_ptr<HeifPixelImage>&",
     "ColorState",
     "ColorConversionOptions"
    ]
   },
   "guards": [
    {
     "code": "(bpp!=8) != hdr",
     "line": 455
    },
    {
     "code": "bpp!=8",
     "line": 455
    },
    {
     "code": "input->get_bits_per_pixel(heif_channel_Alpha) != bpp",
     "line": 461
    },
    {
     "code": "y<height",
     "line": 518
    },
    {
     "code": "x<width",
     "line": 519
    },
    {
     "code": "y<height",
     "line": 528
    },
    {
     "code": "x<width",
     "line": 529
    },
    {
     "code": "y<height",
     "line": 540
    }
   ],
   "line_call_count": 8,
   "line_calls": [
    {
     "code": "memcpy(&out_a[y*out_a_stride], &in_a[y*in_a_stride], width*2)",
     "name": "memcpy",
     "nargs": 3
    },
    {
     "code": "&out_a[y*out_a_stride]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "out_a[y*out_a_stride]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "y*out_a_stride",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "&in_a[y*in_a_stride]",
     "name": "<operator>.addressOf",
     "nargs": 1
    },
    {
     "code": "in_a[y*in_a_stride]",
     "name": "<operator>.indirectIndexAccess",
     "nargs": 2
    },
    {
     "code": "y*in_a_stride",
     "name": "<operator>.multiplication",
     "nargs": 2
    },
    {
     "code": "width*2",
     "name": "<operator>.multiplication",
     "nargs": 2
    }
   ],
   "line_ids": [
    "out_a",
    "y",
    "out_a_stride",
    "in_a",
    "in_a_stride",
    "width"
   ],
   "osv_id": "ARVO-42486640",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "Op_RGB_to_YCbCr<unsigned char>::convert_colorspace(std::__1::shared_ptr<heif::HeifPixelImage const> const&, heif::ColorState, heif::ColorConversionOptions)"
  }
 },
 {
  "osv_id": "ARVO-42487174",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "hex",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-itacns.c",
    "line": 383,
    "size": null,
    "type": "char[16]"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "sc_der_copy",
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 2050
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "16",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 389,
    "fn": "hextoint",
    "code": "strncpy(hex, src, len+1) | len+1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hextoint",
    "file": "/src/opensc/src/libopensc/pkcs15-itacns.c",
    "line": 389
   },
   "code": "strncpy(hex, src, len+1) | len+1",
   "access": {
    "dir": "READ",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "hextoint",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "len >= sizeof(hex)",
   "guard_count": 1,
   "control_structures": "IF:387,IF:392"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[16]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "src",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/b02da8348be97d4b24081783f6af46757373bc3e/ARVO-42487174/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_b02da8348be9.cpg",
   "testcase_size": 157
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
   "shadow_byte": "01",
   "shadow_legend_size": 21,
   "dedup_token": "strncpy--hextoint--get_name_from_EF_DatiPersonali"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "hex[16]",
     "line": 383
    },
    {
     "code": "hex[len] = '\\0'",
     "line": 390
    }
   ],
   "entity_decl": {
    "line": 383,
    "type": "char[16]"
   },
   "entity_name_cpg": "hex",
   "func_lines": [
    381,
    395
   ],
   "func_params": {
    "names": [
     "src",
     "len"
    ],
    "types": [
     "char*",
     "unsigned int"
    ]
   },
   "guards": [
    {
     "code": "end != (char*)&hex[len]",
     "line": 392
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "strncpy(hex, src, len+1)",
     "name": "strncpy",
     "nargs": 3
    },
    {
     "code": "len+1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "hex",
    "src",
    "len"
   ],
   "osv_id": "ARVO-42487174",
   "sites": [
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "hex[16]",
     "line": 383
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "hextoint"
  }
 },
 {
  "osv_id": "ARVO-42487241",
  "project": "htslib",
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
    "fn": "ks_resize",
    "file": "/src/htslib/./htslib/kstring.h",
    "line": 150
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 136,
    "fn": "le_to_u32",
    "code": "",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "le_to_u32",
    "file": "/src/htslib/htslib/hts_endian.h",
    "line": 136
   },
   "code": "",
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "le_to_u32",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/htslib/address/34ba6c726925efceaa2cc995d7d4b0409907f331/ARVO-42487241/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/htslib_34ba6c726925.cpg",
   "testcase_size": 95
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
   "shadow_byte": "04",
   "shadow_legend_size": 21,
   "dedup_token": "le_to_u32--le_to_i32--bcf_dec_typed_int1_safe"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    134,
    143
   ],
   "func_params": {
    "names": [
     "buf"
    ],
    "types": [
     "uint8_t*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42487241",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "le_to_u32"
  }
 },
 {
  "osv_id": "ARVO-42487431",
  "project": "c-blosc2",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": null,
   "kind": "pointer",
   "storage": "heap",
   "decl": null
  },
  "alloc": {
   "api": "calloc",
   "site": {
    "fn": "util_Calloc (/out/decompress_fuzzer+0x4daf68)",
    "file": null,
    "line": null
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [],
  "crash": {
   "site": {
    "fn": "sw32_",
    "file": "/src/c-blosc2/blosc/blosc-private.h",
    "line": null
   },
   "code": null,
   "access": {
    "dir": "READ",
    "width": 4,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "sw32_",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/address/ed6acfff013ef727226d56b262c67b925730669e/ARVO-42487431/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/c-blosc2_ed6acfff013e.cpg",
   "testcase_size": 42
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
   "shadow_legend_size": 0,
   "dedup_token": "sw32_--blosc_d--serial_blosc"
  },
  "deep": {
   "entity_assignments": [],
   "func_lines": [
    39,
    59
   ],
   "func_params": {
    "names": [
     "pa"
    ],
    "types": [
     "void*"
    ]
   },
   "guards": [],
   "line_call_count": 0,
   "line_calls": [],
   "line_ids": [],
   "osv_id": "ARVO-42487431",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "sw32_"
  }
 },
 {
  "osv_id": "ARVO-42487504",
  "project": "openexr",
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
    "fn": "Imf_2_5::Array<Imf_2_5::Rgba>::Array(long)",
    "file": "/src/openexr/OpenEXR/IlmImf/ImfArray.h",
    "line": 86
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 746,
    "fn": "setBits",
    "code": null,
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "setBits",
    "file": "/src/openexr/IlmBase/Half/half.h",
    "line": 746
   },
   "code": null,
   "access": {
    "dir": "WRITE",
    "width": 2,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "setBits",
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
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openexr/address/ed560b8a932c78d5e8e5990ce36fe7808b35d9f0/ARVO-42487504/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openexr_ed560b8a932c.cpg",
   "testcase_size": 411
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
   "dedup_token": "setBits--read<Imf_2_5::CharPtrIO, const char *>--Imf_2_5::copyIntoFrameBuffer(char const*&, char*, char*, unsigned long, bool, double, Imf_2_5::Compressor::Form"
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
   "osv_id": "ARVO-42487504",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "setBits"
  }
 },
 {
  "osv_id": "ARVO-42487587",
  "project": "ndpi",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "flow",
   "kind": "pointer",
   "storage": "heap",
   "decl": {
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 279,
    "size": null,
    "type": "ndpi_flow_struct*"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "__libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x2083f)",
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
    "line": 350,
    "fn": "http_process_user_agent",
    "code": "strncpy(flow->http.user_agent, (char*)ua_ptr, ua_ptr_len | flow->http.user_agent | flow->http | (char*)ua_ptr",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "http_process_user_agent",
    "file": "/src/ndpi/src/lib/protocols/http.c",
    "line": 350
   },
   "code": "strncpy(flow->http.user_agent, (char*)ua_ptr, ua_ptr_len | flow->http.user_agent | flow->http | (char*)ua_ptr",
   "access": {
    "dir": "READ",
    "width": 956,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "http_process_user_agent",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "ua_ptr_len > 7 | ua_ptr_len > 14",
   "guard_count": 2,
   "control_structures": "IF:287,IF:294,IF:297,IF:302,IF:305,IF:306,IF:312,IF:314,IF:318,IF:320,IF:323,IF:325"
  },
  "call_chain": [],
  "types": {
   "entity_type": "ndpi_flow_struct*",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "param"
  },
  "input_reachability": [
   "ndpi_struct",
   "flow",
   "ua_ptr",
   "ua_ptr_len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/ndpi/address/6a7139bb24c4835604641262a07becee637a9e53/ARVO-42487587/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/ndpi_6a7139bb24c4.cpg",
   "testcase_size": 1280
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
   "dedup_token": "strncpy--http_process_user_agent--process_chlo"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "flow->http.user_agent = ndpi_malloc(len)",
     "line": 348
    },
    {
     "code": "flow->http.user_agent[ua_ptr_len] = '\\0'",
     "line": 351
    }
   ],
   "entity_decl": {
    "line": 279,
    "type": "ndpi_flow_struct*"
   },
   "entity_name_cpg": "flow",
   "func_lines": [
    278,
    360
   ],
   "func_params": {
    "names": [
     "ndpi_struct",
     "flow",
     "ua_ptr",
     "ua_ptr_len"
    ],
    "types": [
     "ndpi_detection_module_struct*",
     "ndpi_flow_struct*",
     "u_int8_t*",
     "u_int16_t"
    ]
   },
   "guards": [
    {
     "code": "ua_ptr_len > 7",
     "line": 287
    },
    {
     "code": "strncmp(ua, \"Mozilla\", 7) == 0",
     "line": 294
    },
    {
     "code": "strcmp(token, \"X11\") == 0",
     "line": 306
    },
    {
     "code": "strcmp(token, \"compatible\") == 0",
     "line": 307
    },
    {
     "code": "strcmp(token, \"Linux\") == 0",
     "line": 308
    },
    {
     "code": "strcmp(token, \"Macintosh\") == 0",
     "line": 309
    },
    {
     "code": "token[0] == ' '",
     "line": 312
    },
    {
     "code": "strcmp(token, \"U\") == 0",
     "line": 315
    },
    {
     "code": "strncmp(token, \"MSIE\", 4) == 0",
     "line": 316
    },
    {
     "code": "token[0] == ' '",
     "line": 318
    },
    {
     "code": "strncmp(token, \"Update\", 6)  == 0",
     "line": 320
    },
    {
     "code": "token[0] == ' '",
     "line": 323
    },
    {
     "code": "strncmp(token, \"AOL\", 3)  == 0",
     "line": 325
    },
    {
     "code": "token[0] == ' '",
     "line": 328
    },
    {
     "code": "ua_ptr_len > 14",
     "line": 338
    },
    {
     "code": "memcmp(ua, \"netflix-ios-app\", 15) == 0",
     "line": 338
    },
    {
     "code": "flow->http.user_agent == NULL",
     "line": 345
    }
   ],
   "line_call_count": 4,
   "line_calls": [
    {
     "code": "strncpy(flow->http.user_agent, (char*)ua_ptr, ua_ptr_len)",
     "name": "strncpy",
     "nargs": 3
    },
    {
     "code": "flow->http.user_agent",
     "name": "<operator>.fieldAccess",
     "nargs": 2
    },
    {
     "code": "flow->http",
     "name": "<operator>.indirectFieldAccess",
     "nargs": 2
    },
    {
     "code": "(char*)ua_ptr",
     "name": "<operator>.cast",
     "nargs": 2
    }
   ],
   "line_ids": [
    "flow",
    "ua_ptr",
    "ua_ptr_len"
   ],
   "osv_id": "ARVO-42487587",
   "sites": [
    {
     "args": "256",
     "callee": "<operator>.alloc",
     "code": "ua[256]",
     "line": 288
    },
    {
     "args": "len",
     "callee": "ndpi_malloc",
     "code": "ndpi_malloc(len)",
     "line": 348
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "http_process_user_agent"
  }
 },
 {
  "osv_id": "ARVO-42487631",
  "project": "opensc",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "hex",
   "kind": "array",
   "storage": "heap",
   "decl": {
    "file": "/src/opensc/src/libopensc/pkcs15-itacns.c",
    "line": 383,
    "size": null,
    "type": "char[16]"
   }
  },
  "alloc": {
   "api": "unknown:interceptor_skipped",
   "site": {
    "fn": "sc_der_copy",
    "file": "/src/opensc/src/libopensc/asn1.c",
    "line": 2050
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true,
   "size_expr_cpg": "16",
   "size_expr_cpg_callee": "<operator>.alloc"
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 389,
    "fn": "hextoint",
    "code": "strncpy(hex, src, len+1) | len+1",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "hextoint",
    "file": "/src/opensc/src/libopensc/pkcs15-itacns.c",
    "line": 389
   },
   "code": "strncpy(hex, src, len+1) | len+1",
   "access": {
    "dir": "READ",
    "width": 7,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "hextoint",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": "len >= sizeof(hex)",
   "guard_count": 1,
   "control_structures": "IF:387,IF:392"
  },
  "call_chain": [],
  "types": {
   "entity_type": "char[16]",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "src",
   "len"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/opensc/address/797414be05220fa371972606d7a6c2e94dd6d8db/ARVO-42487631/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/opensc_797414be0522.cpg",
   "testcase_size": 132
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
   "shadow_byte": "06",
   "shadow_legend_size": 21,
   "dedup_token": "strncpy--hextoint--get_name_from_EF_DatiPersonali"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "hex[16]",
     "line": 383
    },
    {
     "code": "hex[len] = '\\0'",
     "line": 390
    }
   ],
   "entity_decl": {
    "line": 383,
    "type": "char[16]"
   },
   "entity_name_cpg": "hex",
   "func_lines": [
    381,
    395
   ],
   "func_params": {
    "names": [
     "src",
     "len"
    ],
    "types": [
     "char*",
     "unsigned int"
    ]
   },
   "guards": [
    {
     "code": "end != (char*)&hex[len]",
     "line": 392
    }
   ],
   "line_call_count": 2,
   "line_calls": [
    {
     "code": "strncpy(hex, src, len+1)",
     "name": "strncpy",
     "nargs": 3
    },
    {
     "code": "len+1",
     "name": "<operator>.addition",
     "nargs": 2
    }
   ],
   "line_ids": [
    "hex",
    "src",
    "len"
   ],
   "osv_id": "ARVO-42487631",
   "sites": [
    {
     "args": "16",
     "callee": "<operator>.alloc",
     "code": "hex[16]",
     "line": 383
    }
   ]
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "hextoint"
  }
 },
 {
  "osv_id": "ARVO-42487672",
  "project": "openh264",
  "crash_type": "heap-buffer-overflow",
  "entity": {
   "name": "p0_r",
   "kind": "struct",
   "storage": "heap",
   "decl": {
    "file": "/src/openh264/codec/decoder/core/src/error_concealment.cpp",
    "line": 329,
    "size": null,
    "type": "v8i16"
   }
  },
  "alloc": {
   "api": "malloc",
   "site": {
    "fn": "WelsCommon::WelsMalloc(unsigned int, char const*, unsigned int)",
    "file": "/src/openh264/codec/common/src/memory_align.cpp",
    "line": 72
   },
   "size_expr": null,
   "size_bytes": null,
   "cross_function": true
  },
  "sites": [
   {
    "kind": "unknown",
    "line": 450,
    "fn": "WelsDec::NeedErrorCon(WelsDec::TagWelsDecoderContext*)",
    "code": "p0_r = (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags)) | (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags)) | t1 & (v8i16)flags | (v8i16)flags",
    "origin": "report:crash"
   }
  ],
  "crash": {
   "site": {
    "fn": "WelsDec::NeedErrorCon(WelsDec::TagWelsDecoderContext*)",
    "file": "/src/openh264/codec/decoder/core/src/error_concealment.cpp",
    "line": 450
   },
   "code": "p0_r = (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags)) | (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags)) | t1 & (v8i16)flags | (v8i16)flags",
   "access": {
    "dir": "READ",
    "width": 1,
    "region_bytes": null
   }
  },
  "context": {
   "fn": "DeblockLumaLt4H_msa",
   "in_loop": false,
   "loop_type": null,
   "loop_range": null,
   "guards": null,
   "guard_count": 0
  },
  "call_chain": [],
  "types": {
   "entity_type": "v8i16",
   "cast_present": null,
   "is_signed": null,
   "ptr_origin": "unknown"
  },
  "input_reachability": [
   "iStride",
   "iAlpha",
   "iBeta",
   "pTc"
  ],
  "evidence": {
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-buffer-overflow/openh264/address/effb3931c7c67f34b167fe6e0a93253bf075f78c/ARVO-42487672/report.log",
   "cpg": "/root/gyx/mutator_create/cpg_files/openh264_effb3931c7c6.cpg",
   "testcase_size": 91
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
   "dedup_token": "WelsDec::NeedErrorCon(WelsDec::TagWelsDecoderContext*)--WelsDec::CheckAndFinishLastPic(WelsDec::TagWelsDecoderContext*, unsigned char**, TagBufferInfo*)--WelsDe"
  },
  "deep": {
   "entity_assignments": [
    {
     "code": "(p0_r) = *((v8i16 *)((((pPix + 8 * iStride - 3))) + (iStride)))",
     "line": 350
    },
    {
     "code": "p0_r = (v8i16)__msa_ilvr_b((v16i8)zero, (v16i8)p0)",
     "line": 372
    },
    {
     "code": "p0_r = (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags))",
     "line": 450
    }
   ],
   "entity_decl": {
    "line": 329,
    "type": "v8i16"
   },
   "entity_name_cpg": "p0_r",
   "func_lines": [
    325,
    476
   ],
   "func_params": {
    "names": [
     "pPix",
     "iStride",
     "iAlpha",
     "iBeta",
     "pTc"
    ],
    "types": [
     "uint8_t*",
     "int32_t",
     "int32_t",
     "int32_t",
     "int8_t*"
    ]
   },
   "guards": [],
   "line_call_count": 7,
   "line_calls": [
    {
     "code": "p0_r = (t1 & (v8i16)flags) + (t3 & (v8i16)(~flags))",
     "name": "<operator>.assignment",
     "nargs": 2
    },
    {
     "code": "(t1 & (v8i16)flags) + (t3 & (v8i16)(~flags))",
     "name": "<operator>.addition",
     "nargs": 2
    },
    {
     "code": "t1 & (v8i16)flags",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(v8i16)flags",
     "name": "<operator>.cast",
     "nargs": 2
    },
    {
     "code": "t3 & (v8i16)(~flags)",
     "name": "<operator>.and",
     "nargs": 2
    },
    {
     "code": "(v8i16)(~flags)",
     "name": "<operator>.pointerCall",
     "nargs": 1
    },
    {
     "code": "~flags",
     "name": "<operator>.not",
     "nargs": 1
    }
   ],
   "line_ids": [
    "p0_r",
    "t1",
    "flags",
    "t3",
    "v8i16"
   ],
   "osv_id": "ARVO-42487672",
   "sites": []
  },
  "measured_dims": {
   "reassigned_between": null,
   "cross_frame_count": null,
   "cross_frame_exact": false,
   "free_cross_function": null,
   "free_fn": null,
   "use_fn": "WelsDec::NeedErrorCon(WelsDec::TagWelsDecoderContext*)"
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
        "free_cross_function": "true | false | unknown",
        "cross_frame_count": "number | unknown"
      },
      "dimension_distributions": {"维度名": {"取值": "样本数"}},
      "evidence": ["string"],
      "confidence": "high | medium | low"
    }
  ],
  "unclassified": [{"sample_id": "string", "reason": "string", "missing_fields": ["string"]}],
  "batch_observations": "string"
}

直接输出 JSON，不要任何解释文字。