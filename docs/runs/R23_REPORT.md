# R23 报告

日期：2026-11-07
两件事：**修守卫误杀** + **验证「agent 只回答一个判断题」可不可行**。

> 出发点（不重复论证）：R22 发现 gpac 一条 **R7 人工核实为真**的站点在加新守卫后消失（1→0）。
> "三个项目扫出 0 个"这个结论就是用这套守卫扫的 —— **守卫会误杀，这个 0 就不可信**。

---

## 步骤 1 · 定位是哪道守卫杀的

### 加了临时开关（`R23_OFF=break,ifelse,loopreassign`），逐道关掉跑 gpac

| 关掉哪道 | gpac 原语数 | 站点 |
|---|---:|---|
| （全开，现状） | 0 | — |
| **`break`**（守卫 9 里的 `break`） | **1** | **`gf_odf_vvc_cfg_read_bs:1400→1404 (same_path) var=ar`** ← **就是 R7 那条真站点** |
| `ifelse` | 0 | 不是它 |
| **`loopreassign`** | **2** | 另外 2 条（`gf_odf_vvc_cfg_del:1168→1167`、`1171→1164`，都是 `loop_back`） |
| 全关 | 3 | 上面 3 条 |

**→ 杀害 R7 那条真站点的是守卫 9 的 `break`。**

### 为什么那道守卫在这里判错了（读 pin 源码）

`gpac/src/odf/descriptors.c`（pin `319d44795db1`）：

```c
1393:            case GF_VVC_NALU_SEI_SUFFIX:
1394:                valid = GF_TRUE;
1395:                ar->nalus = gf_list_new();
1396:                gf_list_add(cfg->param_array, ar);
1397:                break;                                    ← 跳出 switch
1398:            default:
1399:                GF_LOG(..., ar->type);                    ← 先读了一次 ar->type
1400:                gf_free(ar);                              ← **释放 ar**
1401:                break;                                    ← **这里只是跳出 switch**
1402:            }
1403:
1404:            if (!valid || ((ar->type != GF_VVC_NALU_DEC_PARAM) && ...))   ← **仍然执行**
```

**`break` 在 `switch` 里只跳出 switch，`switch` 后面的代码（1404）照样执行。**

守卫 9 的判据是"`return`/`break`/`continue`/`goto` 之后不可达" ——
**它没区分 `break` 是跳出循环还是跳出 `switch`** ✗。这里是后者 → **误杀** ✓。

**这是一个真实的 UAF**：`ar` 在 `default` 分支被释放，`break` 之后 1404 行读 `ar->type` ✓。

---

## 步骤 2 · 收窄守卫

### 修法

```python
_m9 = re.search(r"\b(return|break|continue|goto|exit|abort|longjmp|_Exit)\b", s)
if _m9:
    _kw = _m9.group(1)
    if _kw == "break":
        _inner = _innermost_block(_blks, j)      # `break` 所在的最内层块
        if _inner is None or _inner["kind"] != "switch":
            break                                 # 在循环里/不在块里 → 后面不可达 ✓
        # 在 switch 里：只跳出 switch，**后面的代码仍然可达** → 不终止 ✓
    else:
        break
```

配套：`_blks = blocks(lines, lo, hi)` 改成**每个函数只算一次**（原来在守卫里反复算）。

### 两条验收

| 验收 | 结果 |
|---|---|
| **gpac 那条真站点回来了** | ✅ `gf_odf_vvc_cfg_read_bs:1400→1404 (same_path) var=ar` |
| **6 条已知假阳性仍被挡住** | ✅ 全部（`encode.c:1271` / `encode.c:1308` / `pix1.c:1665` / `pix4.c:2942` / `pix4.c:3053` / `in_json.c:4201`） |

**两全做到了** —— 这不是"调参"，是**修了一条判据的逻辑漏洞**（`break` 的两种语义被混为一谈）。

### 另外发现：`loopreassign` 那道也杀了 2 条

关掉它多出 2 条 `loop_back`（`gf_odf_vvc_cfg_del:1168→1167`、`1171→1164`）。
**它们是否真 UAF 本轮没核** —— 因为：
- 它们不在 R7 的核实记录里；
- `loopreassign` 是 R21 加的**正确性守卫**（`maze.c:459→403` 那个假阳性证明了它必要）；
- 本轮的口径是"修 R22 发现的那一条误杀"，不扩大范围。

**记进下一步建议：这 2 条要单独核。**

---

## 步骤 2b · 重扫三个候选

守卫改了，"三个项目扫出 0 个"这个结论要重新验证：

| 项目 | R22 站点数 | **R23 修守卫后** | 新增 | 核实为真 |
|---|---:|---:|---:|---:|
| **leptonica** `42488049` | 1 | **1** | 0 | 0（`pix4.c:3065→3064`，R21 已核为假） |
| **libxml2** `42533950` | 0 | **0** | 0 | — |
| **igraph** `42491511` | 0 | **0** | 0 | — |
| gpac `42518828`（非候选，靠锚点） | 0 | **1** | **+1** | **1**（R7 核过真） |

### 新增站点逐条核实

**唯一的"新增"是 gpac 那条 —— 它不是新站点，是被误杀后回来的，而且 R7 已核实为真。**

`verified_sites.json` 里 gpac 那条**本来就标着 `verdict: "true"`** ✓ —— 本轮**不需要新增台账条目**。

### libredwg 回归：✅ 全部不变

```
  站点: src/in_dxf.c 12284 → 12267  var=pair  kind=loop_back
  plan: ready 1 site 1 mut  total=1.0  weights=[0.5]
  mutator.c sha1: d7913b9e
  verify: pass
  pytest: 35 passed
```

### 三个候选仍是 0 个真站点

**→ R22 的结论"没有第二个落地项目"仍然成立**，而且这次是在**修好误杀之后**的守卫上得出的。

### gpac 能往下走吗

```
  findings: 从 feature_pipeline 派生（1 条）
  plan: BLOCKED —— "uaf-llm01: 段锚点未推出"
```

**和 leptonica 同一类**：gpac 是 **ISOM 二进制**格式，`ensure_record_structure`（DXF 专用）在它身上没有依据 ✓。

### ⏸ 停止点：等确认

| 你要的 | 结果 |
|---|---|
| 定位结果 | ✅ **守卫 9 的 `break`**（关掉它，R7 那条真站点就回来） |
| 为什么判错 | ✅ `break` 在 `switch` 里只跳出 switch，`switch` 后的代码仍可达；守卫 9 没区分两种语义 |
| 修法 | ✅ `break` 所在最内层块若是 `switch` → 不终止（附：块改成每函数算一次） |
| gpac 回来了吗 | ✅ `1400→1404 same_path var=ar` |
| 6 条假阳性还挡着吗 | ✅ 全部 |
| 重扫三个候选 | ✅ 1 / 0 / 0，**不变**；libredwg 回归全不变 |
| pytest | ✅ 35 passed |

**确认后进第二部分（agent 判定可行性验证）。**
