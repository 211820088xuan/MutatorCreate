# Mutator Generation V2 设计与实施计划

> **路径映射（2026-11-02 整理后）**
> 本文是设计规格的快照，文中路径为整理前布局。对应关系：
> `pattern_analysis/pipeline/` → `pipeline/`；`pattern_analysis/artifacts/` → `artifacts/`；
> `pattern_analysis/outputs/` → `outputs/`；`mutator_custom/stage5/<OSV>/` → `projects/<OSV>/`。
> 下面的路径已按新布局替换。

---

> 本文是给服务器开发 agent 使用的设计规格和实施计划。它描述当前 mutator 生成质量不足的根因、V2 的架构、数据契约、修改范围、逐步开发任务、验收门禁，以及从单项目扩展到全项目的路线。第一版只针对 `ARVO-42494732 / libredwg / heap-use-after-free` 建立可重复闭环。

## 0. 文档结论

当前项目的 stage1 到 stage4 已经形成了可用的数据基础，但 stage5 仍然是“通用特征 + 故障函数上下文直接交给 LLM，让 LLM 写完整 mutator”。这条路径缺少一个重要中间层：它没有把 fuzz target 的输入、调用的 API、解析字段、候选漏洞、stage4 特征和具体变异动作建立成可验证的关系。因此生成结果容易出现以下问题：

- LLM 选择了与当前项目无关的 stage4 特征。
- 静态审计中的“候选”被当成了“已确认漏洞”。
- 变异动作没有证据说明它如何影响目标条件。
- 解析格式被破坏，输入在到达目标代码前就被拒绝。
- 多个机制混在一个 mutator 中，实验无法归因。
- crash 文件数量增加被误判为发现了更多漏洞。

V2 的核心设计是：

~~~text
固定项目版本和 fuzz target
        ↓
target_surface.json
        ↓
candidate_findings.json
        ↓
feature_bindings.json
        ↓
mutation_plan.json
        ↓
受约束的 mutator.json / mutator.c
        ↓
证据、编译、回放、路径和 fuzz 门禁
~~~

确定性程序分析负责事实、调用面、源码行、字段 locator 和不确定性；LLM 只负责在已提供证据上解释机制匹配，并把已经冻结的 mutation plan 翻译成 C 代码。没有可靠输入字段映射时，plan 必须是 `blocked`，流程必须停止，而不是生成一个无法解释的随机变异器。

---

## 1. 当前项目的事实基础

### 1.1 已有数据和代码

当前项目已经不是空白原型，已有以下可复用资产：

- `reproduce_crash/`：OSS-Fuzz/ARVO 崩溃复现记录、报告、testcase 和交付索引。
- `cpg_files/`：Joern CPG 文件，可用于函数、调用、数据流和 AST 查询。
- `artifacts/facts/`：由崩溃报告、CPG 和深度字段合成的 facts。
- `artifacts/interpretation/`：由 facts 派生的确定性解释。
- `outputs/stage3/`：按崩溃类型归纳的 pattern。
- `outputs/stage4/`：项目无关的机制特征。
- `pipeline/s5_fetch_source.py`：抓取固定版本源码、harness 和故障函数上下文。
- `pipeline/s5a_scan_target.py`：从 fuzz target 调用面生成风险函数 worklist。
- `pipeline/s5b_audit_agent.py`：让 agent 对风险函数做静态候选审计。
- `pipeline/s5c_mech_hypotheses.py`：用确定性规则寻找循环内释放后使用等形态。
- `pipeline/s5_generate_mutator.py`：当前直接生成 C mutator 的旧实现。
- `projects/ARVO-42494732/`：libredwg 单项目已有源码、CPG dump、审计报告、旧 mutator、门禁和 fuzz 实验。

### 1.2 当前 stage5 的真实数据流

现有流程可以概括为：

1. `s5_fetch_source.py` 从崩溃记录中取出项目、commit、故障文件、故障函数，复制 fuzz target，并抓取部分被调函数。
2. `s5a_scan_target.py` 读取 CPG，沿 `LLVMFuzzerTestOneInput` 的调用边展开，按 `free`、`alloc`、`mem`、`index` 等风险标签构建 worklist。
3. `s5b_audit_agent.py` 把 worklist 的函数块交给 LLM，要求逐函数给出 `candidate`、`clean` 或 `skipped`，并校验 candidate 的源码证据。
4. `s5c_mech_hypotheses.py` 用规则扫描释放包装函数、循环和释放后的解引用，生成 `hypothesis`。
5. `s5_generate_mutator.py` 只读取 stage4 feature 和 `source_context.json`，直接请求 LLM 输出完整 `mutator.c`。

问题在第 4 步到第 5 步之间：`vuln_report.json` 和 `mech_hypotheses.json` 没有成为生成器的正式输入；即使它们存在，也没有一个中间产物判断候选是否与 fuzz target 输入相关、是否与 stage4 特征匹配、是否具备可操作的字段定位。因此生成器仍然让 LLM 自己完成漏洞选择、输入格式推断和代码实现。

### 1.3 现有 libredwg 实验说明了什么

现有 `ARVO-42494732` 实验已经暴露出架构问题：

- 旧 mutator 把 5 个 UAF 特征混在一起。
- 只有针对当前 libredwg 已知 `in_dxf.c` UAF 的策略有直接项目证据，其他策略来自不同机制或不同项目。
- custom 组覆盖边低于 default，约为 default 的 95.9%。
- custom 组的目标 UAF 单位执行触发率提高，但两组仍然主要触发同一个已知崩溃点，没有证明发现了新的唯一漏洞。
- 多个 crash 文件不等于多个漏洞，必须按 ASan 崩溃点去重。

正确解释是：当前特征到项目机制的绑定不够精确，而不是“stage4 特征一定无效”。必须先对每个候选项目做单特征、单机制的落地，再做组合实验。

### 1.4 根因

质量问题由四个结构性缺口共同造成：

1. **生成器没有漏洞报告输入。** 生成器没有读 `vuln_report.json` 或 `mech_hypotheses.json`。
2. **没有 feature binding。** 代码没有明确说明“这个项目里的哪一个候选机制对应 stage4 的哪一个特征”。
3. **没有输入字段映射门禁。** source context 有故障函数和部分被调函数，但不一定能证明输入字节如何影响目标条件。
4. **没有声明式 mutation plan。** 变异字段、格式不变量、边界关系、预期路径和源码证据没有先被冻结，直接混在 LLM 输出的 C 代码中。

### 1.5 设计判断

以下判断必须贯穿实现：

- “源码中存在一次 free 调用”是事实。
- “该 free 后的变量在后续路径中再次解引用”是机制候选。
- “输入中的某个字段能让程序到达这个路径”是输入可达性结论。
- “修改这个字段会提高触发概率”是变异计划假设。
- “生成的 C 能正确执行该计划”是代码实现结果。

这五类信息不能用一段自然语言混在一起。每一层都要有独立 JSON 产物和校验状态。

---

## 2. 目标、非目标和成功标准

### 2.1 第一版目标

第一版只针对一个项目和一个已知崩溃建立闭环：

~~~text
ARVO-42494732
  → 固定 commit 的 libredwg 源码和 llvmfuzz harness
  → target_surface.json
  → candidate_findings.json
  → feature_bindings.json
  → mutation_plan.json
  → mutator.json / mutator.c
  → verification.json
  → 单特征 default/custom 对照实验
~~~

第一版需要回答：

1. fuzz target 的输入经过哪些入口和 API 进入目标函数？
2. 漏洞报告中的候选是否能与 fuzz 输入建立证据链？
3. 哪个 stage4 特征与候选漏洞机制匹配？
4. 哪些字段和不变量可以可靠地交给 mutator？
5. mutator 是否保持解析接受率，并提高目标路径或目标崩溃的单位执行触发率？

### 2.2 非目标

第一版不做以下工作：

- 不重构 stage1 复现、stage2 facts 或 stage3 pattern 聚类。
- 不一次性支持所有项目和所有输入格式。
- 不把所有静态候选都验证成真实漏洞。
- 不以覆盖率单项提升作为唯一成功标准。
- 不把旧 `mutator.c`、旧 `fuzz_exp` 或旧实验报告覆盖掉。
- 不在输入字段未知时使用任意字节插入作为兜底。
- 不让 LLM 自己决定计划外的字段、偏移、边界或控制流假设。

### 2.3 单项目完成标准

当以下条件全部满足时，第一版才算完成：

- 固定 commit、CPG、harness 和源码引用可以重现。
- `target_surface.json` 明确记录已知路径和 unknown。
- `candidate_findings.json` 能区分 LLM candidate、机械 hypothesis、facts 和 interpretation 来源。
- `feature_bindings.json` 只选择一个主特征，不把五个 UAF 特征自动混合。
- `mutation_plan.json` 明确输入格式、字段 locator、保持的不变量、变异关系、边界和证据引用。
- 没有完整字段映射时，plan 输出 `blocked`，且生成器拒绝生成 C。
- ready plan 生成的 C 通过编译、源码证据和行为门禁。
- 已知崩溃输入仍可回放。
- 实验至少报告 parser acceptance、目标路径触达、目标崩溃率、唯一崩溃点、覆盖边和 execs。

---

## 3. V2 总体架构

### 3.1 分层流程

~~~text
5.0 输入冻结
    固定 OSV/ARVO、项目、commit、源码树、harness、CPG、stage4 feature

5.1 Target Surface
    harness 入口、直接 API、CPG 可达面、parser、输入表达式、条件、sink、unknown

5.2 Candidate Findings
    audit candidate + mechanical hypothesis + facts/interpretation
    证据核对、去重、调用面关系、已知故障关系、输入可达性

5.3 Feature Binding
    机制族硬过滤、前置条件核对、字段目标核对、LLM 解释、选择/拒绝/阻塞

5.4 Mutation Plan
    输入格式、字段 locator、格式不变量、变异操作、边界、预期路径、证据 refs

5.5 Mutator Generation
    仅消费 ready plan，生成 mutator.json 和 mutator.c

5.6 Verification
    schema、源码证据、编译、已知崩溃回放、解析接受率、目标条件/路径

5.7 Experiment
    default、single_feature，之后才允许 mixed_features
~~~

### 3.2 为什么必须引入中间层

如果直接让 LLM 从完整源码生成 C，模型需要同时解决代码阅读、调用图恢复、漏洞判断、输入格式解析、字段定位、特征匹配和 C 实现。任何一个环节出错，最终只会表现为“mutator 不好”，而无法知道是事实错、路径错、字段错还是代码错。

中间层把职责拆开：

- `target_surface` 负责输入和可达代码面。
- `candidate_findings` 负责候选漏洞及证据。
- `feature_bindings` 负责项目候选和通用特征之间的关系。
- `mutation_plan` 负责可执行的变异策略。
- `mutator.c` 只负责实现已批准的计划。

这样可以对每一层单独测试、回放和替换模型，也能在字段映射不完整时安全停止。

### 3.3 LLM 的边界

LLM 只允许出现两次：

1. 读取候选摘要、feature 和相关证据，填写机制匹配的解释、满足条件和缺失条件。
2. 读取 ready mutation plan，生成符合 contract 的 C 代码。

LLM 不得：

- 修改 hard checks。
- 把 `unknown` 改写成 `complete`。
- 从完整源码中自行发明字段偏移。
- 添加计划中不存在的 mutation action。
- 将 `unverified` 写成 `verified`。

---

## 4. 产物与数据契约

### 4.1 V2 工作目录

第一版所有新增结果必须写到：

~~~text
projects/ARVO-42494732/v2/
~~~

旧 stage5 目录、旧 `mutator.c`、旧 fuzz 实验和旧报告不可覆盖。

推荐目录：

~~~text
v2/
├── manifest.json
├── target_surface.json
├── candidate_findings.json
├── feature_bindings.json
├── mutation_plan.json
├── mutator.json
├── mutator.c
├── verification.json
├── verification.log
├── source_refs/
└── experiment/
~~~

### 4.2 manifest.json

记录输入冻结信息：

~~~json
{
  "schema_version": "stage5.manifest.v1",
  "osv_id": "ARVO-42494732",
  "project": "libredwg",
  "commit": "ff69eeda6658",
  "source_root": "/tmp/opencode/src_local/github.com_LibreDWG_libredwg",
  "harness": ["harness/llvmfuzz.c"],
  "cpg": "cpg_files/libredwg_ff69eeda6658.cpg",
  "inputs": {
    "source_context_sha256": "...",
    "worklist_sha256": "...",
    "vuln_report_sha256": "...",
    "mech_hypotheses_sha256": "...",
    "features_sha256": "..."
  },
  "old_experiment_is_baseline": true,
  "v2_status": "initialized"
}
~~~

manifest 的作用是防止 agent 误把另一个 commit 的源码、CPG 或旧实验当作当前输入，也防止开发过程中覆盖旧结果。

### 4.3 target_surface.json

职责：只描述 fuzz target 的输入攻击面和静态可达面，不负责证明漏洞。

~~~json
{
  "schema_version": "stage5.target_surface.v1",
  "target": {
    "osv_id": "ARVO-42494732",
    "project": "libredwg",
    "commit": "ff69eeda6658",
    "harness": "llvmfuzz",
    "entry_symbol": "LLVMFuzzerTestOneInput",
    "input_parameter": "data",
    "input_length_parameter": "size"
  },
  "call_surface": {
    "direct_calls": [],
    "reachable_functions": [],
    "reachable_files": [],
    "depth": 2,
    "source": "joern_cpg"
  },
  "parsers": [
    {
      "function": "dxf_read_pair",
      "file": "src/in_dxf.c",
      "role": "record_parser",
      "input_expressions": ["dat->chain", "dat->byte", "dat->size"],
      "evidence_lines": [
        [445, "int size = strlen ((char*)&dat->chain[dat->byte]) + 1;"]
      ],
      "confidence": "medium"
    }
  ],
  "fields": [
    {
      "field_id": "dxf.group_code.9",
      "format": "DXF",
      "anchor": "group code 9",
      "value_kind": "string",
      "locator": "record_sequence",
      "source_path": [],
      "controls": [],
      "confidence": "unknown"
    }
  ],
  "conditions": [],
  "sinks": [],
  "unknowns": [],
  "validation": {
    "fixed_commit": true,
    "source_files_present": true,
    "harness_present": true,
    "cpg_present": true,
    "field_mapping_complete": false
  }
}
~~~

关键规则：`fields[].confidence=unknown` 时，该字段不能成为 ready plan 的唯一控制对象。target surface 只能把名称相似当成候选，不能把“出现了 `data`”当成完整数据流证明。

### 4.4 candidate_findings.json

职责：合并 LLM 审计候选、机械规则假设、facts、interpretation 和已知崩溃关系。

~~~json
{
  "schema_version": "stage5.candidate_findings.v1",
  "target": {"osv_id": "ARVO-42494732", "commit": "ff69eeda6658"},
  "findings": [
    {
      "finding_id": "c001",
      "vuln_family": "heap-buffer-overflow",
      "original_types": ["heap-buffer-overflow"],
      "mechanism": "固定容量缓冲区在输入长度累加后可能越界写",
      "file": "src/in_dxf.c",
      "function": "add_LTYPE_dashes",
      "evidence_lines": [[2051, "o->strings_area = ..."]],
      "sources": ["vuln_report.c001"],
      "input_reachability": {
        "status": "partial",
        "field_ids": ["dxf.group_code.9"],
        "path_evidence": [],
        "missing": ["group code 9 到 add_LTYPE_dashes 的完整调用路径"]
      },
      "call_surface_relation": "reachable",
      "fault_relation": "unrelated",
      "status": "unverified",
      "confidence": "medium",
      "why_unverified": "未完成输入字段到候选函数的完整数据流，也未执行 ASAN 回放"
    }
  ],
  "rejected": [],
  "unknowns": []
}
~~~

`status` 允许：`verified`、`unverified`、`rejected`、`blocked`。第一版不要求每个 finding 都 verified，但进入主计划至少需要证据通过和完整输入可达性。

### 4.5 feature_bindings.json

职责：说明某个 stage4 feature 是否适合某个项目 finding。

~~~json
{
  "schema_version": "stage5.feature_bindings.v1",
  "target": "ARVO-42494732",
  "bindings": [
    {
      "binding_id": "b001",
      "feature_id": "uaf-llm01",
      "finding_ids": ["h003"],
      "hard_checks": {
        "same_vulnerability_family": true,
        "free_or_reclaim_evidence": true,
        "post_free_use_evidence": true,
        "input_reachability_complete": false,
        "fault_relation_available": true
      },
      "satisfied_preconditions": [],
      "missing_preconditions": ["输入记录到释放分支的可证明路径"],
      "evidence_refs": [],
      "llm_rationale": "只解释现有证据，不补造字段",
      "score": 0.0,
      "status": "blocked"
    }
  ],
  "selected_binding_id": null,
  "selection_reason": "字段映射尚未闭合"
}
~~~

LLM 不能修改 `hard_checks` 和 `status`。`score` 只用于排序，不能覆盖硬门禁。

### 4.6 mutation_plan.json

职责：冻结输入格式、字段、变异动作和保持不变量，成为 C 生成器的唯一业务输入。

~~~json
{
  "schema_version": "stage5.mutation_plan.v1",
  "plan_id": "plan-001",
  "target": {
    "osv_id": "ARVO-42494732",
    "project": "libredwg",
    "commit": "ff69eeda6658",
    "crash_type": "heap-use-after-free",
    "known_fault": {"file": "src/in_dxf.c", "line": 12267}
  },
  "feature_binding": {
    "feature_id": "uaf-llm01",
    "binding_id": "b001",
    "status": "blocked"
  },
  "input_contract": {
    "format": "DXF",
    "parser_entry": null,
    "accepted_seed_requirements": [],
    "preserve": ["header", "section ordering", "record terminators", "field type"]
  },
  "targets": [],
  "mutations": [],
  "expected_path": [],
  "limits": [],
  "status": "blocked",
  "blockers": ["no complete field-to-condition mapping"]
}
~~~

每个 mutation action 必须有：`action_id`、`field_id`、`locator`、`operation`、`relation`、`bounds`、`preserve`、`expected_effect`、`basis_refs`。没有这些字段不能标记 `ready`。

### 4.7 mutator.json provenance

旧输出保留原字段，V2 增加：

~~~json
{
  "provenance": {
    "plan_file": "v2/mutation_plan.json",
    "binding_file": "v2/feature_bindings.json",
    "finding_file": "v2/candidate_findings.json",
    "source_commit": "ff69eeda6658"
  },
  "generation_gate": {
    "plan_status": "ready",
    "evidence_check": "pass",
    "compile_check": "pass",
    "replay_check": "pass"
  }
}
~~~

---

## 5. 文件边界和修改范围

### 5.1 新增文件

第一版不要直接重写旧 stage5，新增 V2 入口和小型模块：

- `pipeline/s5_target_surface.py`：目标面抽取，只做确定性分析。
- `pipeline/s5_candidate_findings.py`：候选合并、去重、证据和状态规范化。
- `pipeline/s5_feature_binding.py`：feature/finding 硬过滤和受限解释。
- `pipeline/s5_mutation_plan.py`：生成并校验声明式计划。
- `pipeline/s5_generate_mutator_v2.py`：只接受 ready plan，生成 JSON/C。
- `pipeline/s5_verify_mutator_v2.py`：统一执行验证门禁。
- `pattern_analysis/tests/test_stage5_v2.py`：契约、负例和纯函数测试。
- `pattern_analysis/tests/fixtures/stage5_v2/`：脱离 `/tmp` 的最小源码、harness、CPG 和 JSON fixture。

### 5.2 兼容性修改文件

- `s5_fetch_source.py`：保留旧字段，增加 `input_parameters`、`harness_calls`、`parser_candidates`、`source_commit_verified`。
- `s5a_scan_target.py`：增加入口、直接 API、调用深度、conditions 和 sinks 摘要；不改变旧 worklist 的读取方式。
- `s5b_audit_agent.py`：candidate 增加 `input_reachability`；无法连接输入的内容必须进入 `not_input_reachable`。
- `s5c_mech_hypotheses.py`：增加 `function_range`、`call_surface_relation` 和默认 `input_reachability=unknown`。
- `stage5_generate_mutator.md`：记录 V2 prompt contract，但实际生成由 V2 脚本负责。
- `projects/ARVO-42494732/`：只添加 `v2/` 和相关索引，不覆盖旧实验。

### 5.3 不应修改的内容

- 旧 `projects/ARVO-42494732/mutator.c`。
- 旧 `fuzz_exp/`、`fuzz_exp2/`、`RESULT.md`、`robust_stats.md`。
- `reproduce_crash/artifacts/`、`data/`、`crash_testcase/`、原始 CPG 文件。
- stage1–stage4 历史 JSONL，除非另建版本化输出并有回归测试。

---

## 6. 详细实施计划

执行 agent 必须按顺序完成。每项任务完成后保存修改文件、命令、退出码、输入输出哈希和失败原因。每项任务都应该有独立测试；不要把所有工作写成一个大脚本后一次性运行。

### Task 0：冻结基线并创建 V2 工作区

**Files:**

- Create: `projects/ARVO-42494732/v2/README.md`
- Create: `projects/ARVO-42494732/v2/manifest.json`
- Test: `pattern_analysis/tests/test_stage5_v2.py`

**Consumes:** `source_context.json`、`audit_worklist.json`、`vuln_report.json`、`mech_hypotheses.json`、stage4 UAF `features.json`。

**Produces:** 固定 commit、文件哈希、命令和空产物索引。

- [ ] 检查远端是否有正在运行的 agent、容器或 fuzz 进程，不重用旧实验目录。
- [ ] 记录项目、commit、源码根目录、harness、CPG 和所有输入 JSON 的 SHA-256。
- [ ] 建立 `v2/`，README 明确旧实验是 baseline。
- [ ] 写负例测试：plan 不存在或 `status=blocked` 时，生成器退出非零且不创建 `mutator.c`。
- [ ] 运行：`python3 -m pytest pattern_analysis/tests/test_stage5_v2.py::test_blocked_plan_cannot_generate_code -q`。

建议测试接口：

~~~python
def test_blocked_plan_cannot_generate_code(tmp_path):
    plan = {"schema_version": "stage5.mutation_plan.v1", "status": "blocked"}
    path = tmp_path / "mutation_plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    result = run_generator(path)
    assert result.returncode != 0
    assert not (tmp_path / "mutator.c").exists()
~~~

### Task 1：实现 target surface 抽取

**Files:**

- Create: `pipeline/s5_target_surface.py`
- Modify: `pipeline/s5_fetch_source.py`
- Modify: `pipeline/s5a_scan_target.py`
- Test: `pattern_analysis/tests/test_stage5_v2.py`

**Interface:**

~~~python
def build_target_surface(
    context: dict,
    worklist: dict,
    cpg_dump: dict,
    harness_sources: dict[str, str],
) -> dict:
    """Build stage5.target_surface.v1 without an LLM."""
~~~

实施步骤：

- [ ] 写 fixture：harness 的 `data` 传给 `parse_record`，但没有可证明的字段偏移；期望 `field_mapping_complete=false`，unknowns 有缺失路径。
- [ ] 运行测试确认失败，确保测试不是因为 fixture 错误失败。
- [ ] 从 `LLVMFuzzerTestOneInput` 识别输入参数和直接调用。
- [ ] 从 CPG 调用边计算 bounded reachable functions 和 files。
- [ ] 从源码识别 parser candidates、条件、循环、guard 和 memory sink。
- [ ] 每一个节点带 `file`、`line`、`code`、`source`、`confidence`。
- [ ] 无法确认的跨文件、宏展开或输入字段关系写入 `unknowns`。
- [ ] 加入 commit/CPG/harness/source 文件存在性校验。
- [ ] 正例验证 libredwg 的 harness → parser → `dxf_objects_read` 可达面。

不要把变量名相同当作数据流证明。`data`、`size`、`dat->chain` 等只能成为候选表达式，必须结合 CPG 或源码路径才能把 mapping 标成 complete。

### Task 2：统一候选漏洞报告

**Files:**

- Create: `pipeline/s5_candidate_findings.py`
- Modify: `pipeline/s5b_audit_agent.py`
- Modify: `pipeline/s5c_mech_hypotheses.py`
- Test: `pattern_analysis/tests/test_stage5_v2.py`

**Interface:**

~~~python
def normalize_findings(
    audit_report: dict,
    mech_report: dict,
    facts: dict | None,
    interpretation: dict | None,
    target_surface: dict,
    source_root: str,
) -> dict:
    """Normalize candidate findings and retain provenance."""
~~~

实施步骤：

- [ ] 写去重测试：LLM candidate 和 mechanical hypothesis 具有相同 family、file、function、free/use evidence 时合并为一个 finding，并保留两个 source。
- [ ] 写证据失败测试：行号越界或代码文本不是固定源码子串时，状态必须是 `rejected`。
- [ ] 统一 vulnerability family：lifetime、bounds、initialization、arithmetic-to-memory 等。
- [ ] 重新读取固定 commit 的源码核对所有 `evidence_lines`。
- [ ] 使用 `(family, file, function, normalized evidence lines)` 去重，不按自然语言 mechanism 去重。
- [ ] 计算 `call_surface_relation`：`direct`、`reachable`、`outside`、`unknown`。
- [ ] 计算 `fault_relation`：`same_site`、`same_function`、`same_file`、`same_family_only`、`unrelated`。
- [ ] 输入未连接时标为 `blocked` 或 `unverified`，不能成为 ready plan。
- [ ] 在 `s5b_audit_agent.py` candidate schema 加入 `input_reachability`。
- [ ] 在 `s5c_mech_hypotheses.py` 为机械假设增加函数范围、调用面关系和输入可达性 unknown 默认值。

机械规则只能证明代码形状，例如“释放后变量可能再次解引用”；它不能单独证明 fuzz 输入一定能走到该路径。

### Task 3：实现 feature binding

**Files:**

- Create: `pipeline/s5_feature_binding.py`
- Modify: `pattern_analysis/prompts/stage5_generate_mutator.md`
- Test: `pattern_analysis/tests/test_stage5_v2.py`

**Interface:**

~~~python
def bind_features(
    features: dict,
    findings: dict,
    target_surface: dict,
    llm=None,
) -> dict:
    """Return accepted/rejected/blocked feature bindings."""
~~~

硬过滤：

- [ ] 机制族一致，例如 heap-buffer-overflow 不能被 UAF feature 接受。
- [ ] UAF feature 必须有释放/回收和释放后使用 evidence。
- [ ] feature mutation target 必须能找到 target surface field。
- [ ] 目标函数、文件或调用面必须有交集，或显式标记为探索性 same_family_only。
- [ ] 检查相反证据：明确置空、重新赋值、提前 return 或已有保护条件。
- [ ] 没有完整 input reachability 时只能 `blocked`。

LLM 只接收候选摘要、feature JSON、相关 target surface 节点和证据行，只能填写：

- `satisfied_preconditions`
- `missing_preconditions`
- `rationale`

LLM 不得修改硬检查结果和 status。

选择规则：

1. hard checks 全部通过。
2. input reachability 为 complete。
3. evidence 全部通过。
4. fault relation 至少 same_function 或 same_file；探索性计划必须单独标记。
5. score 最高；同分时选 locator 更明确、证据更短更具体的 binding。

没有 accepted binding 时，`selected_binding_id=null`，不进入 mutator 生成。

### Task 4：生成 mutation plan

**Files:**

- Create: `pipeline/s5_mutation_plan.py`
- Test: `pattern_analysis/tests/test_stage5_v2.py`

**Interface:**

~~~python
def build_mutation_plan(
    binding: dict,
    feature: dict,
    target_surface: dict,
    findings: dict,
    seed_metadata: dict,
) -> dict:
    """Build mutation_plan.v1; status is ready only after validation."""
~~~

必须 blocked 的情况：

- 没有 selected binding。
- 输入格式未知。
- field 没有 locator。
- field 到目标 condition 没有 source path。
- mutation action 没有 basis refs。
- preserve invariant 没有实现策略。

第一版允许的 operation：

- 在已识别 record/field 上修改值，同时保持 record 结构。
- 复制已有合法 record，并同步需要同步的计数/终止条件。
- 对长度/数量做边界附近调整，同时同步格式要求的长度/校验字段。

第一版禁止：

- 未定位字段时在任意 offset 插入字节。
- 不知道格式边界时截断输入。
- 大范围随机替换 header、section 或 record terminator。
- 一个计划绑定多个无关机制。

每个 action 必须声明：

~~~json
{
  "action_id": "a001",
  "field_id": "dxf.group_code.9",
  "locator": {"kind": "record_sequence", "anchor": "..."},
  "operation": "replace_value",
  "relation": "increase_total_length_without_breaking_record",
  "bounds": {"min": 1, "max": 256, "boundary_values": [0, 1, 255, 256]},
  "preserve": ["record terminator", "field type"],
  "expected_effect": "increase loop iterations before target sink",
  "basis_refs": ["finding:c001:evidence_lines:0", "feature:uaf-llm01:mutation_target:0"]
}
~~~

### Task 5：实现受约束 mutator 生成

**Files:**

- Create: `pipeline/s5_generate_mutator_v2.py`
- Modify: `pattern_analysis/prompts/stage5_generate_mutator.md`
- Test: `pattern_analysis/tests/test_stage5_v2.py`

**Interface:**

~~~python
def build_generation_prompt(
    plan: dict,
    source_snippets: dict,
    contract: dict,
) -> str:
    """Build a bounded prompt from a ready plan only."""
~~~

实现步骤：

- [ ] 先写测试：blocked plan 被拒绝；prompt 不包含未经筛选的全量候选；每个 bias 有 basis ref。
- [ ] 只允许 `plan.status=ready` 进入模型调用。
- [ ] prompt 只包含已选 feature、finding 摘要、locator、不变量、操作白名单、bounds、预期路径和 evidence refs。
- [ ] 明确禁止新增计划外字段、offset、strategy、随机替换和格式破坏动作。
- [ ] 解析失败、空代码、markdown 包裹、缺字段或计划外 action 必须失败。
- [ ] 生成后检查：C 代码中的策略和字段与 plan 一致；每个 bias 可回溯；有长度边界和原输入回退。
- [ ] 编译失败时保留失败日志，但不得把输出标为可实验。

生成器不应把完整 12,000 行 `in_dxf.c` 放进 prompt。只传 plan 需要的 source snippets 和证据行，避免模型重新做一遍未经约束的源码搜索。

### Task 6：统一验证门禁

**Files:**

- Create: `pipeline/s5_verify_mutator_v2.py`
- Modify: `projects/ARVO-42494732/stage5_verify.py`（只复用旧门禁，不破坏旧调用）
- Test: `pattern_analysis/tests/test_stage5_v2.py`

**Interface:**

~~~python
def verify_mutator_v2(
    manifest: dict,
    surface: dict,
    findings: dict,
    bindings: dict,
    plan: dict,
    mutator_path: str,
    runtime: dict,
) -> dict:
    """Return verification.json with pass/fail/blocked per gate."""
~~~

四层门禁：

**V1 schema gate**

- schema version 正确。
- commit、OSV、project、plan_id 一致。
- 必填字段存在。
- blocked 状态不能继续。

**V2 evidence gate**

- 每个源码文件存在。
- 行号合法。
- 代码片段是固定源码行的子串。
- 每个 mutation action 有 basis refs。
- 所有 refs 都能解析到 finding、feature 或 target surface。

**V3 code gate**

- C/C11 编译通过。
- `LLVMFuzzerCustomMutator` 接口正确。
- 输入长度和输出长度有边界。
- 失败时返回合法原输入/副本。
- 没有访问计划外字段。
- 单次新增字节和最大变异长度满足 contract。

**V4 behavior gate**

- 已知 crash input 能重放出原始崩溃。
- 至少一组 seed 可以被目标 parser 接受。
- 可以观测目标 parser、branch、free/use 或 sink。
- 解析失败率不超过实验阈值。
- 目标条件计数器能够报告触达变化。

验证输出必须区分 `pass`、`fail`、`not_applicable`、`blocked`，并记录每条命令、退出码、输入哈希和摘要。

### Task 7：运行单项目实验

**Files:**

- Create: `projects/ARVO-42494732/v2/experiment/README.md`
- Create: `projects/ARVO-42494732/v2/experiment/run_matrix.json`
- Create: `projects/ARVO-42494732/v2/experiment/summarize.py`

实验组：

1. `default`：libFuzzer 默认变异。
2. `single_feature`：只启用一个 accepted feature 的 mutator。
3. `mixed_features`：只有 single feature 完成后才允许运行，作为探索性对照。

固定：同一 binary、同一 seed corpus、同一 timeout/rss、同一资源、独立随机种子、至少 5 次重复。

必须报告：

- execs、exec/s。
- parser acceptance。
- target condition hits。
- target crash count 和每 100k execs 的触发率。
- unique crash site，而不是 crash 文件数。
- coverage edges、corpus size。
- timeout、OOM 和非目标崩溃。

结果解释规则：

- 目标崩溃率升高但 coverage 不升：说明更容易重放已知目标，不说明发现新漏洞。
- crash 文件数升高但 unique site 不升：说明同一个崩溃被重复触发。
- parser acceptance 降低：先检查格式保持和 locator，不要立即增加 mutator 权重。
- custom 只提高一个目标条件而没有路径变化：记录为局部触达改善，不宣称通用有效。

---

## 7. 为什么这个设计是正确的

### 7.1 它直接对应当前失败原因

当前生成质量低不是因为缺少一个更强的 prompt，而是因为事实到代码之间没有显式接口。四个新中间产物分别补上四个缺口：

- `target_surface`：输入从 harness 到 parser/目标函数的路径。
- `candidate_findings`：候选漏洞是什么，证据是什么，是否和调用面、已知故障相关。
- `feature_bindings`：哪个 stage4 机制适用于哪个项目候选，哪些条件缺失。
- `mutation_plan`：应该修改哪一类字段，保持哪些格式不变量，预期影响哪个条件。

这让 C 生成从开放式推理变成受约束实现。

### 7.2 为什么不能直接把漏洞报告塞进 prompt

漏洞报告可能同时包含：高置信候选、低置信候选、与当前崩溃无关的候选、只在源码形态上成立的候选、输入不可达候选。全部塞进 prompt 会让模型按“描述最完整”而不是按“证据最强”选择，也会把 `unverified` 变成自然语言中的确定事实。先规范化再绑定，可以把这些状态作为硬字段传递。

### 7.3 为什么一个 mutator 只绑定一个主特征

混合特征会稀释权重、破坏不同格式要求，并且无法归因。单特征实验能回答“该特征是否提高了该机制的触达”；随后再进行组合实验。如果组合变差，可以区分是组合冲突、权重问题还是单特征本身无效。

### 7.4 为什么需要声明式计划

C 代码是最难审查的输出。plan 能在编译前检查 locator、bounds、preserve invariants、expected path 和 evidence refs，也允许多个代码生成器实现同一个计划并比较结果。没有 plan，就无法知道失败来自字段映射、机制判断还是代码实现。

### 7.5 为什么 blocked 是正确结果

当前 source context 常常只能证明“函数里有某个条件或 free”，不能证明哪个输入字节控制它。如果在这种情况下仍生成一个“智能随机” mutator，只是把无依据的猜测包装成代码。`blocked` 能准确指出下一步需要补什么：CPG 数据流、parser adapter、动态字段追踪、编译期 instrumentation 或人工提供格式 schema。

---

## 8. 单项目的具体落地策略

### 8.1 libredwg 已知 UAF 的优先路径

当前已知崩溃点位于 `src/in_dxf.c:dxf_objects_read`。现有 source context 已经能看到类似：

~~~c
Dxf_Pair *pair = dxf_read_pair (dat);
while (pair != NULL) {
    while (pair != NULL && pair->code == 0 && pair->value.s) {
        if (is_dwg_object (name)) {
            dxf_free_pair (pair);
            pair = new_object (...);
        } else {
            DXF_RETURN_ENDSEC (0);
            dxf_free_pair (pair);
        }
    }
    dxf_free_pair (pair);
    pair = dxf_read_pair (dat);
}
~~~

这段源码可以证明释放和循环结构，但不能自动证明某个 DXF 字段一定让 `is_dwg_object` 进入某个分支。第一版应优先建立以下证据链：

1. `LLVMFuzzerTestOneInput(data,size)` 如何构造 `Bit_Chain`。
2. `Bit_Chain.chain` 和 `byte/size` 如何对应输入缓冲区。
3. `dxf_read_pair` 如何把 DXF record 转成 `Dxf_Pair`。
4. group code 0 的字符串如何进入 `name` 和 `is_dwg_object`。
5. `is_dwg_object(name)` 的合法对象集合如何影响释放分支。
6. 下一条 record 如何让控制流再次读 `pair`。

如果第 3–5 步无法从静态证据闭合，应先输出 blocked plan。可以开发 parser adapter 或动态 field tracing，但不能凭猜测写固定偏移。

### 8.2 对已有漏洞候选的排序

对 `ARVO-42494732` 的 `vuln_report.json`，排序建议如下：

1. 与已知故障同 family、同函数或同文件，并且有释放/使用证据的候选。
2. 与 fuzz target 调用面相交，且输入字段 mapping complete 的候选。
3. 有有效源码证据、无相反 guard 证据的候选。
4. 只有同 family、但不同文件或不同 parser 的候选，标为探索性。
5. 只有 LLM 自然语言、无源码行或输入关系的候选，拒绝或 blocked。

不要因为 `confidence=high` 就跳过输入可达性；审计模型的 high 只是它对源码候选的信心，不是 fuzz 输入一定可达。

---

## 9. 从单项目扩展到全项目

### 9.1 保持稳定的核心接口

全项目版本不应该为每个项目复制一条完全不同的流水线，而应让项目/格式适配器实现同一组接口：

~~~python
class TargetAdapter(Protocol):
    def discover_harness(self, source_root: str, commit: str) -> HarnessInfo: ...
    def extract_input_surface(self, context: dict, cpg: CpgView) -> TargetSurface: ...
    def locate_fields(self, surface: TargetSurface, seed: bytes) -> list[FieldLocation]: ...
    def preserve_invariants(self, surface: TargetSurface) -> list[Invariant]: ...
    def apply_mutation(self, data: bytes, action: MutationAction, seed: int) -> bytes: ...
    def observe_target(self, run: RunResult) -> TargetObservation: ...
~~~

通用核心只依赖：

- `TargetSurface`
- `Finding`
- `FeatureBinding`
- `MutationPlan`
- `VerificationResult`

不应在核心逻辑中写死 DXF、DWG、PNG、PDF 或某个项目的函数名。

### 9.2 输入格式适配器分层

建议按输入结构逐步增加适配器：

1. `raw_bytes`：只允许有明确字节锚点的动作。
2. `line_record`：适合 DXF、文本协议和配置文件，支持记录复制、字段替换和终止符保持。
3. `binary_record`：支持 endian、长度、校验和、偏移同步。
4. `ast_or_parser`：调用项目现有 parser 或轻量结构解析器，适合深层结构化输入。

每个适配器都必须在 locator 失败时返回原输入；不能把 unknown locator 当作 offset 0。

### 9.3 统一漏洞机制 ontology

不同项目的原始崩溃类型要保留，同时映射到有限机制族：

- `lifetime`：use-after-free、double-free、invalid-free。
- `bounds`：heap/stack/global buffer overflow、out-of-bounds read/write、container overflow。
- `initialization`：use-of-uninitialized-value。
- `arithmetic-to-memory`：整数溢出导致分配、长度或索引错误。
- `control/resource`：null dereference、状态脱钩等；只有有明确内存安全证据时进入主流程。

归一化不能覆盖原始 `vuln_type`、原始 report 和 evidence。

### 9.4 全项目批处理顺序

不要一开始对全量项目生成 mutator。推荐：

1. 只运行确定性的 target surface，统计 harness 识别、CPG 可用、parser 类型和 field mapping 完整率。
2. 选择已有 crash、source、CPG 和完整 mapping 的项目作为第一批。
3. 运行 candidate normalization，统计 finding family、证据通过率和输入可达率。
4. 按机制族执行 feature binding，得到 accepted、blocked、rejected 分布。
5. 只对 accepted binding 生成 mutation plan 和 mutator。
6. 每个项目/格式独立做 default/single-feature 实验。
7. 只有在多个项目上完成单特征验证后，才统计全项目共性或组合策略。

### 9.5 防止项目偏见

全项目结论必须按项目分层：

- 报告支持项目数，而不是只报 crash 样本数。
- 报告 mapping 完整率、accepted plan 数和 blocked 率。
- 对 custom/default 使用每 exec、每 accepted input、每单位时间的归一化指标。
- 统计 unique crash sites，而不是 crash artifact 文件数。
- 只在单项目出现的模式标记为 `project_specific`，不得进入全项目默认权重。
- 对 c-blosc2、libredwg 等样本量大的项目做 leave-one-project-out 检查，确认共性不是单项目贡献。

### 9.6 全项目需要新增的基础设施

当单项目闭环稳定后，再引入：

- `adapters/`：按格式/项目的 TargetAdapter。
- `schemas/`：JSON schema 和版本迁移器。
- `batch_stage5.py`：按项目并行调度，但必须保存每个项目独立 manifest。
- `reports/stage5_matrix.jsonl`：跨项目成功率、blocked 原因、实验指标。
- `replay_registry.jsonl`：每个 mutator、binary、seed、crash 的可回放记录。
- 动态字段追踪工具：用于静态 CPG 不能闭合输入字段路径的项目。

---

## 10. 风险、失败处理和停止条件

### 10.1 源码和 CPG 不一致

症状：行号存在，但 CPG 来自另一个 commit。处理：manifest 记录 CPG commit，版本不一致直接 blocked。

### 10.2 宏、生成代码和 vendored code

症状：源码文本看起来有 free/use，但宏展开后控制流不同。处理：保存宏定义，必要时生成预处理源码或使用 compile database；不能确认就保留 unknown。

### 10.3 LLM 误判

症状：agent 将真实 UAF 判成 clean，或把无关释放判成 UAF。处理：机械规则负责候选发现，LLM 只能补充解释；候选必须有源码证据，主计划必须有输入映射。

### 10.4 输入字段定位缺失

症状：只能说“增大某字符串”，不能定位到 record、字段或偏移。处理：blocked；下一步补 parser adapter、CPG 数据流或动态字段追踪。

### 10.5 格式破坏

症状：custom acceptance 显著下降，目标条件反而更少。处理：先检查 locator、terminator、长度和 checksum invariant；不能直接提高权重。

### 10.6 旧会话冲突

症状：旧 agent、容器或 fuzz 实验仍在写目录。处理：V2 使用独立 `v2/experiment`，先检查进程和容器，不删除旧工作区。

### 10.7 三次失败后的架构判断

同一层连续三次失败时，不要继续改 prompt：

- 字段 locator 连续失败：需要 parser/动态追踪层。
- 编译连续失败：需要稳定 mutator contract 和桩编译测试。
- acceptance 连续下降：需要格式适配器，而不是更强随机策略。
- 目标率提高但路径和 unique site 不变：需要重新定义实验目标和观测点。

### 10.8 正确的安全失败

以下结果可以是正确交付：

- `target_surface.json` 完成，但 field mapping incomplete。
- `candidate_findings.json` 有候选，但没有 accepted binding。
- `mutation_plan.json` 为 blocked，并明确列出缺失 evidence。
- 没有生成 `mutator.c`。

这比生成一个无法复现、无法归因的随机 mutator 更有价值，因为它告诉后续 agent 应补哪一类证据。

---

## 11. 推荐提交顺序和执行规则

每个任务独立保存测试和产物，推荐 commit：

~~~text
feat(stage5): freeze v2 single-target baseline
feat(stage5): extract target surface
feat(stage5): normalize candidate findings
feat(stage5): bind features to findings
feat(stage5): build evidence-backed mutation plan
feat(stage5): generate mutator from ready plan
feat(stage5): add unified verification gate
exp(stage5): run single-feature libredwg comparison
~~~

执行顺序不可跳过：

~~~text
Task 0 baseline
  ↓
Task 1 target_surface
  ↓
Task 2 candidate_findings
  ↓
Task 3 feature_bindings
  ↓
Task 4 mutation_plan
  ↓
Task 5 mutator
  ↓
Task 6 verification
  ↓
Task 7 experiment
~~~

每项任务完成后必须记录：

- 修改文件列表。
- 运行命令、退出码和测试摘要。
- 输入/输出 JSON 的 schema version。
- 输入/输出 SHA-256。
- 当前状态：`pass`、`fail`、`blocked` 或 `not_applicable`。
- 若 blocked，缺失的具体证据和下一步建议。

---

## 12. 最终交付物清单

第一版实现完成后，项目中至少应有：

~~~text
docs/superpowers/plans/2026-11-01-mutator-generation-design-and-plan.md

projects/ARVO-42494732/v2/
├── README.md
├── manifest.json
├── target_surface.json
├── candidate_findings.json
├── feature_bindings.json
├── mutation_plan.json
├── mutator.json
├── mutator.c
├── verification.json
├── verification.log
└── experiment/

pipeline/
├── s5_target_surface.py
├── s5_candidate_findings.py
├── s5_feature_binding.py
├── s5_mutation_plan.py
├── s5_generate_mutator_v2.py
└── s5_verify_mutator_v2.py

pattern_analysis/tests/test_stage5_v2.py
~~~

若 `mutation_plan.json` 或 `verification.json` 最终是 blocked，只要 blocker 真实反映当前静态信息不足，仍然算阶段性成功。必须把 blocker 作为下一阶段增加动态字段追踪、parser adapter 或 CPG 数据流的依据，而不是绕过门禁生成代码。

---

## 13. 设计自检

### 13.1 覆盖性

- 现状、实验依据和根因：第 1 节。
- 目标和非目标：第 2 节。
- 总体架构和 LLM 边界：第 3 节。
- JSON 数据契约：第 4 节。
- 文件修改范围：第 5 节。
- 逐任务开发计划：第 6 节。
- 设计合理性：第 7、8 节。
- 全项目通用化：第 9 节。
- 风险和停止条件：第 10 节。
- agent 执行和交付：第 11、12 节。

### 13.2 无伪完成

文档不把“模型生成了 C 文件”定义为完成。只有证据、计划、编译、回放和实验口径都闭合，才允许把 mutator 标记为可实验。

### 13.3 类型一致性

数据流固定为：

~~~text
target_surface.v1
  → candidate_findings.v1
  → feature_bindings.v1
  → mutation_plan.v1
  → mutator.json + mutator.c
  → verification.json
~~~

任何下一层缺少上一层产物时必须退出并报告 blocker，不得从旧文件或模型上下文中隐式补齐。

