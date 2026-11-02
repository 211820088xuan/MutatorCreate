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

## 样本（共 5 条，完整 facts + interpretation）

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
   "fn": "decNumberCopy",
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
    "width": 2
   },
   "code": "s=src->lsu+1 | src->lsu+1 | src->lsu | s<smsup",
   "site": {
    "file": "/src/jq/vendor/decNumber/decNumber.c",
    "fn": "decNumberCopy",
    "line": 3375
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
   "cpg": null,
   "report": "artifacts/by_crash_type/stack-buffer-overflow/jq/address/64bd8ba3749fe473b0708f999e088dfa94d37a2c/OSV-2023-1329",
   "testcase_size": 23
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-1329",
  "project": "jq",
  "sites": [
   {
    "code": "s=src->lsu+1 | src->lsu+1 | src->lsu | s<smsup",
    "fn": "decNumberCopy",
    "kind": "unknown",
    "line": 3375,
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
   "context.in_loop",
   "call_chain"
  ],
  "context": {
   "fn": "compound_check",
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
   "code": "word[i - 1] == word[i] | word[i - 1] | i - 1 | word[i]",
   "site": {
    "file": "/src/hunspell/src/hunspell/affixmgr.cxx",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "line": 1825
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
   "cpg": "/root/gyx/mutator_create/cpg_files/hunspell_82b92126325d.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-14.log",
   "testcase_size": 14095
  },
  "input_reachability": [
   "this",
   "word",
   "wordnum"
  ],
  "osv_id": "OSV-2023-14",
  "project": "hunspell",
  "sites": [
   {
    "code": "word[i - 1] == word[i] | word[i - 1] | i - 1 | word[i]",
    "fn": "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<char>> const&, short, short, short, short, hentry**, hentry**, char, char, int*)",
    "kind": "unknown",
    "line": 1825,
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
   "control_structures": "IF:201,IF:219,IF:227,WHILE:232,IF:238,IF:244,IF:247,IF:251,IF:252,ELSE:254,IF:264,ELSE:267",
   "fn": "TranslateWord3",
   "guard_count": 9,
   "guards": "word_length == 1 | word_length == 1 | word_length == 1",
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
   "code": "word_length = 0",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/translateword.c",
    "fn": "TranslateWord3",
    "line": 231
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": {
    "file": "/src/espeak-ng/src/libespeak-ng/translateword.c",
    "line": 163,
    "size": null,
    "type": "int"
   },
   "kind": "struct",
   "name": "word_length",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/espeak-ng_c19350f961d3.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2023-984.log",
   "testcase_size": 1204
  },
  "input_reachability": [],
  "osv_id": "OSV-2023-984",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "word_length = 0",
    "fn": "TranslateWord3",
    "kind": "unknown",
    "line": 231,
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
   "entity_type": "int",
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
   "call_chain"
  ],
  "context": {
   "fn": "_pcre2_check_escape",
   "guard_count": 25,
   "guards": "ptr >= ptrend | ptr < ptrend | ptr >= ptrend",
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
   "code": "ptr = hptr + 1 | hptr + 1",
   "site": {
    "file": "/src/pcre2/src/pcre2_compile_class.c",
    "fn": "_pcre2_compile_class_not_nested_16",
    "line": 1638
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "ptr",
   "storage": "stack"
  },
  "evidence": {
   "cpg": "/root/gyx/mutator_create/cpg_files/pcre2_62b3ceca1787.cpg",
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2024-1261.log",
   "testcase_size": 50000
  },
  "input_reachability": [
   "ptrptr",
   "ptrend"
  ],
  "osv_id": "OSV-2024-1261",
  "project": "pcre2",
  "sites": [
   {
    "code": "ptr = hptr + 1 | hptr + 1",
    "fn": "_pcre2_compile_class_not_nested_16",
    "kind": "unknown",
    "line": 1638,
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
   "fn": "TranslateRoman",
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
   "code": "((tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0 | (tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0] | tr->langopts.numbers & NUM_ROMAN_CAPITALS | tr->langopts.numbers",
   "site": {
    "file": "/src/espeak-ng/src/libespeak-ng/numbers.c",
    "fn": "TranslateRoman",
    "line": 782
   }
  },
  "crash_type": "stack-buffer-overflow",
  "entity": {
   "decl": null,
   "kind": null,
   "name": "tr",
   "storage": "stack"
  },
  "evidence": {
   "cpg": null,
   "report": "/root/gyx/mutator_create/reproduce_crash/artifacts/logs/reproduce/OSV-2025-169.log",
   "testcase_size": 2018
  },
  "input_reachability": [
   "tr",
   "word",
   "wtab"
  ],
  "osv_id": "OSV-2025-169",
  "project": "espeak-ng",
  "sites": [
   {
    "code": "((tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0 | (tr->langopts.numbers & NUM_ROMAN_CAPITALS) && !(wtab[0] | tr->langopts.numbers & NUM_ROMAN_CAPITALS | tr->langopts.numbers",
    "fn": "TranslateRoman",
    "kind": "unknown",
    "line": 782,
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