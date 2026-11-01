# libFuzzer 自定义变异算子使用情况调研

> 严谨约束：✅ 事实标 `file:line`；🅗 假设显式标注；ⓘ 外部/未知标注；无证据不下结论。
> 调研对象：本地 OSS-Fuzz 语料 334 项目（`/root/gyx/projects/` + `/root/gyx/driver_create/source_code/`）+ 崩溃数据集 `data/crash_dataset.jsonl`（3,790 条）。

---

## 1. 机制（✅ 官方文档）

libFuzzer 的变异默认走内置算子，输出 `MS:` 字段可见 `ChangeByte`/`ChangeBit`/`CrossOver`/`InsertByte`/`EraseBytes`/`CopyPart`/`ShuffleBytes` 等（`llvm.org/docs/LibFuzzer.html`）。用户可通过三个 hook 接管变异：

| Hook | 签名 | 作用 |
|---|---|---|
| `LLVMFuzzerCustomMutator` | `(Data, Size, MaxSize, Seed) -> size_t` | 完全替换变异逻辑；输出中显示为 `MS: ... Custom-` |
| `LLVMFuzzerCustomCrossOver` | `(Data1,Size1,Data2,Size2,Out,MaxOutSize,Seed) -> size_t` | 自定义两输入交叉 |
| `LLVMFuzzerMutate` | `(Data, Size, MaxSize) -> size_t` | **反向委托**：在 custom mutator 内回调 libFuzzer 内置变异，常用作 fallback |

**结构感知范式**（`github.com/google/fuzzing/blob/master/docs/structure-aware-fuzzing.md`）：custom mutator 做 parse → mutate(解析后表示) → serialize 回合法输入，使变异不破坏语法。两条实现路线：
- **手写** custom mutator（直接定义上述 hook）；
- **LPM 路线**：`DEFINE_PROTO_FUZZER` / `DEFINE_BINARY_PROTO_FUZZER`，变异器由 libprotobuf-mutator 内部提供，用户只写 proto schema + 一个消费 protobuf message 的 target。

ⓘ libFuzzer 已转入维护模式：原作者转向 Centipede，不再有重大新特性（`llvm.org/docs/LibFuzzer.html` "Status" 节）。

---

## 2. 采用率（✅ grep `/root/gyx/projects/`，334 项目）

| 类别 | 项目 | 数 | 占比 |
|---|---|---|---|
| 手写 `LLVMFuzzerCustomMutator` | fluent-bit, igraph, json, libxml2, ndpi, radare2, wamr | 7 | 2.1% |
| `LLVMFuzzerCustomCrossOver`（含仅 CrossOver） | igraph, json, qemu, radare2 | 4 | 1.2% |
| LPM/`DEFINE_PROTO_FUZZER` | ntopng | 1 | 0.3% |
| **任一形式 custom mutator** | (并集) | **8** | **2.4%** |
| 调用 `LLVMFuzzerMutate`（委托回内置） | fluent-bit, json, libxml2, radare2, wamr | 5 | 1.5% |

**结论（证据级）**：custom mutator 在 OSS-Fuzz 语料中**极为罕见**——96.4% 的项目完全依赖 libFuzzer 内置变异。即使采用者，多数也通过 `LLVMFuzzerMutate` 把部分工作回委托给内置算子。

---

## 3. 算子级 taxonomy（逐实现深读源码）

### 范式 A — 委托外部结构感知库：ndpi → pl7m

- ndpi 的 `LLVMFuzzerCustomMutator` 是 4 行薄封装，整体委托给 `pl7m_mutator`（`projects/ndpi/fuzz_ndpi_reader.c:44-47`，`#ifdef ENABLE_PCAP_L7_MUTATOR`）。
- pl7m 是 pcap L7 感知变异库，源码在本地 `driver_create/source_code/ndpi/src/lib/third_party/src/fuzz/pl7m.c`（1,564 行）。变异分两层（`pl7m.c:75-80` 注释 + 实现）：
  - **包级** `do_pkt_actions`（`pl7m.c:1262-1296`）：`rand()%4` → ① Drop（删包 `__del_pkt`）② Duplicate（复制 `__dup_pkt`+`__add_pkt`）③ Swap（相邻包交换 `__swap_pkt`）④ Swap direction（client↔server 方向翻转 `swap_direction`）。
  - **载荷级** `do_payload_actions`（`pl7m.c:1298-1304`）→ `update_do(p)`：对 TCP/UDP 头之后的 L5/7 载荷调用 `LLVMFuzzerMutate` 随机化（`pl7m.c:127` 声明）。
  - 序列化回**合法 pcap**：`__serialize_to_fd`（`pl7m.c:1306-1357`）写 24B 全局头 + 逐包 16B 头 + caplen，保证输出始终是合法 pcap 文件。
- 可选开关（`pl7m.c:52-73`）：`PL7M_USE_SIMPLEST_MUTATOR`（整包随机化）、`PL7M_DISABLE_PACKET_MUTATION`/`_PAYLOAD_MUTATION`、`PL7M_USE_64K_PACKETS`（触发 u16 溢出）、`PL7M_ENABLE_RANDOMIZE_PORTS`（随机 L4 端口但保流）。
- 算子清单：drop / duplicate / swap / swap-direction（包级）+ payload byte-mutation via LLVMFuzzerMutate（载荷级）+ 重算 pcap 封装。

### 范式 B — shell-out 外部 CLI + fallback 委托：wamr、fluent-bit

- **wamr**（`projects/wamr/wasm_mutator_fuzz.cc:60-129`，`#ifdef CUSTOM_MUTATOR`）：
  1. 若 `Size>10`：写 `Data`→`./cur.wasm`（`:72-79`）；
  2. `system("wasm-tools mutate cur.wasm --seed N -o modified.wasm [--preserve-semantics if Seed%2]")`（`:85-88`）——调用外部 Rust 工具做 wasm 结构感知变异；
  3. 读回 `modified.wasm` 覆盖 `Data`（`:96-119`）；
  4. **fallback**：若 `wasm-tools` 失败（非法 wasm），`return LLVMFuzzerMutate(Data,Size,MaxSize)` 委托内置（`:91-93`）。
  5. 若 `Size<=10`：清零返回（`:121-128`）。
- **fluent-bit**（`projects/fluent-bit/wasm_mutator_fuzz.cc:204-286`）：**与 wamr 逐行相同**（同为 Intel 版权 wasm 运行时家族，`wasm-tools mutate` + `--preserve-semantics` + `LLVMFuzzerMutate` fallback）。
- 算子清单：wasm 结构感知变异（ⓘ 实际算子在 `wasm-tools` Rust crate 内部，非本地源码，未能逐算子枚举；从命令行可知支持 `--preserve-semantics` 开关）+ 内置 fallback。
- ⓘ **局限**：`wasm-tools mutate` 的具体算子（section 操作/类型替换等）需读 wasm-tools crate 源码，超出本地语料范围，本报告标为外部未知。

### 范式 C — 手写 parse-mutate-serialize（无外部工具）

#### C1 chunk-descriptor 驱动：libxml2（11 targets 共享 helper）
- 每个 target 各自定义 `LLVMFuzzerCustomMutator`，但都调用共享 helper `xmlFuzzMutateChunks`（定义于 `driver_create/source_code/libxml2/fuzz/fuzz.c:551-602`）。
- 调用形态（以 `projects/libxml2/xml.c:250-262` 为例）：声明 chunk 描述表 `{{4, PROB/10}/*opts*/, {4, PROB/10}/*failurePos*/, {4, PROB/10}/*maxChunkSize*/, {0,0}/*flexible body*/}`，传 `LLVMFuzzerMutate` 作为 per-chunk mutator。
- helper 逻辑（`fuzz.c:561-601`）：按概率 `prob < descProb` 选中**一个** chunk → 对该 chunk 调 `mutator(data+off, chunkSize, maxChunkSize)`（即 `LLVMFuzzerMutate`）→ 缩小则零填充。
- 算子清单：按概率选 chunk + per-chunk 内置变异委托 + 零填充。结构感知体现在"知道输入由若干定长头字段 + 弹性 XML 正文构成"，逐次只变异一个 chunk。11 个 target 共享同一 helper，仅 chunk 表不同。

#### C2 token 级文本变异：radare2（C 类型声明字符串）
- `projects/radare2/fuzz_types_parser_custom.c:179-220`。`LLVMFuzzerCustomMutator` 先 50% 概率调 `LLVMFuzzerMutate`（`:185-187`），再 `rand()%8` 选一个算子（`:188-215`）：
  | case | 算子 | 实现 |
  |---|---|---|
  | 0 | replace_word | 找 `[a-zA-Z_]` 词，替换为随机 C 类型(int/char/short/long/float/double/void/unsigned/signed) `:28-54` |
  | 1 | insert_qualifier | 随机位置插入 const/volatile/static/extern/inline `:56-75` |
  | 2 | numbers | 每个数字字符替换为随机 0-9 `:77-87` |
  | 3 | brackets | 每个 `{}()[]` 替换为随机括号 `:89-101` |
  | 4 | semicolons | 1/3 概率删 `;`；1/5 概率在 `\n` 前插 `;` `:103-118` |
  | 5 | insert_fragment | 随机位置插入预定义 C 片段(typedef struct/enum/union/函数指针/bitfield/数组初始化) `:120-139` |
  | 6 | duplicate_statement | 复制一条语句(到 `;`/`}`/`{` 边界) `:141-177` |
  | 7 | replace_word + numbers | 组合 |
- CrossOver（`:222-258`）：两输入各在 `;`/`\n` 处切分，前半来自 data1、后半来自 data2 拼接——语句边界感知的交叉。
- 算子清单：8 个 token/语法感知算子 + 语句边界交叉。

#### C3 元素级 + 边界浮点值生成：igraph（几何坐标 double 数组）
- `projects/igraph/spatial.cpp:31-94`，基于 `rigtorp.se/fuzzing-floating-point-code/`（注释 `:26-29`）。
- 随机浮点生成器 `rfp()`（`:38-67`）：80% 概率 `normal(0,10)`；20% 取边界值 {NaN, ±min, ±max, ±epsilon, ±inf, 0.0}。
- `rand()%4` 选算子（`:69-91`）：① Change element（随机下标赋 rfp）② Add element（尾部追加 rfp）③ Delete element（弹尾）④ Shuffle（`std::shuffle`）。
- CrossOver（`:97-108`）：逐 double 元素 50/50 从 data1/data2 取。
- 算子清单：4 个 double 数组算子 + 浮点边界值池。

#### C4 纯委托 demo：json（测试桩，非真实结构感知）
- `projects/json/CustomMutatorTest.cpp:30-37`：`LLVMFuzzerCustomMutator` 仅打印一次 "In LLVMFuzzerCustomMutator" 后 `return LLVMFuzzerMutate(Data,Size,MaxSize)`——**纯委托，无任何结构感知**。文件头注明 "Simple test for a custom mutator"，是 libFuzzer 自身的 hook 测试用例，非 json 库的真实变异策略。CustomCrossOver 同理（`CustomCrossOverTest.cpp`）。
- 算子清单：无自定义算子，等价于内置变异。归类为 C 仅因它"手写"了 hook，实质是 demo。

### 范式 D — LPM/protobuf：ntopng
- `projects/ntopng/fuzz_dissect_packet.cpp:144-177`，`#ifdef FUZZ_WITH_PROTOBUF`。
- `DEFINE_PROTO_FUZZER(const ntopng_fuzz::Pcap &message)`（`:150`）：消费 protobuf `Pcap` message（含 repeated `Record` 包，每包有 data/header/timestamp），逐包构造 `pcap_pkthdr` 后调 `iface->dissectPacket(...)`（`:153-175`）。
- 变异器由 **libprotobuf-mutator (LPM) 内部提供**——用户不写 `LLVMFuzzerCustomMutator`，LPM 按 proto schema 做字段级变异。
- ⓘ 实际算子在 LPM 库内部（`libprotobuf-mutator`），非本地源码；按文档为 proto 字段级 mutation + crossover。结构 = `proto/pcap.pb.h` 定义的 pcap schema。
- 不启用 `FUZZ_WITH_PROTOBUF` 时退化为普通 `LLVMFuzzerTestOneInput` + `pcap_fopen_offline`（`:179-218`），无 custom mutator。
- 算子清单：proto 字段级变异（LPM 内部，ⓘ 外部）。

### 范式 E — 仅 CrossOver、无 CustomMutator：qemu
- `projects/qemu/fuzz.c:130-141`：`LLVMFuzzerCustomCrossOver` 是**分发器**——`if (fuzz_target->crossover) return fuzz_target->crossover(...)`，委托给各注册 fuzz target 自带的 crossover 函数指针。无 `LLVMFuzzerCustomMutator`（变异完全用 libFuzzer 内置），仅在交叉环节按 target 定制。
- 算子清单：无统一算子；按 target 插件式 crossover。

---

## 4. 算子清单汇总表

| 项目 | 范式 | 委托 LLVMFuzzerMutate? | 算子集 | 源 |
|---|---|---|---|---|
| ndpi | A 外部库 | 是(载荷级) | drop/duplicate/swap/swap-direction + payload 随机化 + pcap 重封装 | `pl7m.c:1262-1357` |
| wamr | B shell-out | 是(fallback) | wasm 结构感知(ⓘ外部 wasm-tools) + `--preserve-semantics` | `wasm_mutator_fuzz.cc:60-129` |
| fluent-bit | B shell-out | 是(fallback) | 同 wamr | `wasm_mutator_fuzz.cc:204-286` |
| libxml2 | C1 chunk表 | 是(per-chunk) | 按概率选 chunk + per-chunk 内置变异 + 零填充 | `fuzz.c:551-602`, `xml.c:250-262` |
| radare2 | C2 token级 | 是(50% pre) | replace_word/insert_qualifier/numbers/brackets/semicolons/insert_fragment/duplicate_statement/combo + 语句边界交叉 | `fuzz_types_parser_custom.c:179-258` |
| igraph | C3 元素级 | 否 | change/add/delete/shuffle + 浮点边界值池 + 逐元素交叉 | `spatial.cpp:31-108` |
| json | C4 demo | 是(纯委托) | 无自定义(等价内置) | `CustomMutatorTest.cpp:30-37` |
| ntopng | D LPM | 否(隐式) | proto 字段级变异(ⓘLPM 内部) | `fuzz_dissect_packet.cpp:150` |
| qemu | E 仅CrossOver | 否 | 无统一;target 插件式 crossover | `fuzz.c:130-141` |

---

## 5. 崩溃画像量化对比（✅ `data/crash_dataset.jsonl`）

9 个 custom-mutator 项目**全部**出现在 3,790 崩溃数据集中。

| 组 | 项目数 | 崩溃数 | 崩溃/项目 | Top-3 crash_type |
|---|---|---|---|---|
| custom-mutator 组 | 9 | 379 | **42.1** | Heap-buffer-overflow 196(52%) / Heap-use-after-free 62(16%) / Global-buffer-overflow 21 |
| 非 custom-mutator 组 | 325 | 3,411 | **10.5** | Heap-buffer-overflow 1,315(39%) / UNKNOWN 481(14%) / Use-of-uninitialized-value 401(12%) |
| custom 组(剔除 ndpi) | 8 | 237 | 29.6 | Heap-buffer-overflow 106 / Heap-use-after-free 56 / Global-buffer-overflow 21 |

🅗 **观察（假设级，非结论）**：custom-mutator 项目崩溃/项目比非 custom 组高约 **4.0×**（剔除 ndpi 仍 2.8×）。可能解释（均未证实）：
- (a) 结构感知变异能触达更深/更易错的代码路径，故产更多崩溃；
- (b) **混淆**：愿意投入写 custom mutator 的项目本就是复杂、高价值、产崩溃多的大项目（体量/年龄/驱动数未控制）；
- (c) custom-mutator 组中 wasm/xml/网络协议解析类占多数，本就是内存密集型。

ⓘ **不能下因果结论**：未控制项目代码体量、 fuzz 预算、驱动数、库龄。crash_type 分布差异（custom 组 HUF/Global 比例更高，非 custom 组 UNKNOWN/uninit 比例更高）亦可能反映 sanitizer/引擎配置差异而非变异策略效果。若要推进，需做体量归一化（如 crashes/loc、crashes/driver）。

---

## 6. 与"错误触发变异算子"方向的关联（材料级，不下结论）

- 本调研的唯一**确定结论**：custom mutator 采用率极低（2.4%），绝大多数 OSS-Fuzz 项目靠内置 6 类算子触发全部 3,790 崩溃。
- 采用者中真实"结构感知"者仅 6 个（ndpi/wamr/fluent-bit/libxml2/radare2/igraph，ntopng 的 LPM 路线另计），且实现路线**高度分化**（外部库 / shell-out CLI / chunk 表 / token 级 / 元素级 / proto）——无统一范式，每个项目重写一遍。
- radare2 的 8 算子、igraph 的 4 算子+边界值池、pl7m 的包级 4 算子是本地可读的**算子级范本**，可作为"变异算子该做什么"的具体参照材料。
- ⓘ 前述"错误触发变异算子"调研已被推翻；本报告不预设其结论，仅作为独立事实层供后续方向取用。

---

## 附：可复现命令

```bash
# 采用率
cd /root/gyx/projects && grep -rl "LLVMFuzzerCustomMutator" --include="*.c" --include="*.cc" --include="*.cpp" . | grep -v testFuzzer | xargs -I{} dirname {} | sort -u
grep -rl "DEFINE_PROTO_FUZZER" --include="*.cpp" . | xargs -I{} dirname {} | sort -u
# 崩溃画像
cd /root/gyx/mutator_create && python3 -c "..."  # 见本报告第 5 节脚本
```
