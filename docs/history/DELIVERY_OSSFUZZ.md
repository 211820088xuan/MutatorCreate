> **历史文档（2026-11-02 归档）**
> 本文记录的是 **OSS-Fuzz/OSV 复现路径**的交付过程（从源码在 HEAD/钉版上构建再跑 testcase）。
> 该路径已从 `reproduce_crash/` 移除，stage1 现在只保留 ARVO 路径（`arvo_repro.py`）。
> 保留本文是为了给已产出的 1,154 条复现结果提供溯源；文中提到的脚本可从 commit `f31ba99e` 取回。

---

# Crash 复现流水线 —— 交付文档

> **唯一交付文档**（`mutator_create/reproduce_crash/DELIVERY.md`）。所有汇报内容直接写进本文，**不再产生新的交付文档**；历史全文底本冻结在 `archive/`（见 §7）。
> 科学严谨约束（`~/.config/opencode/skills/scientific-rigor/SKILL.md`）：✅ 实测（附 `file:line`/命令）｜🅗 假设（附可证伪判据）｜ⓘ 外部/不可得。**无证据不下结论，不用 🅗 推翻 ✅。**
> 状态：**设计定稿（R18）+ 前置验证完成（P0/P0-B/P0-C）+ 实现第一轮完成（W1：⓪① 两模块）**。下一步：② `build_orchestrator`。

## 怎么读这份文档

| 你要做什么 | 看哪几节 |
|---|---|
| **只想 3 分钟了解现状** | §0（一页结论：进度表 + 关键数字表） |
| **要写/改实现代码** | §1 设计规格（组件规格 1.3、schema 1.5、错误处理 1.7、验收 1.8）+ §4 已实现部分 |
| **要核某个数字怎么来的** | §2 实测结论（每行附来源）+ §6 复算命令 |
| **要看某轮的完整推理过程** | §7 变更历史 → `archive/` 对应底本（本文只留结论，不留论证过程） |

---

# 0. 一页结论

## 0.1 目标与交付物

- **目标**：从 3,790 条 OSS-Fuzz crash 构建**已验证可复现的研究数据集**——每条产出「二进制 + testcase + 可复现标注」三件套，作为后续实验（错误触发变异算子归纳）的输入底座。
- **验证标准 = Tiered**：每条记 `verification_tier ∈ {strict, medium, loose, none}` + `frame_match_score` + 重试次数 + 复现版本，**不做二分**，判断权留给下游。
- **下游最低接受 = `medium`**（crash_type 归一化一致）。`loose` 必须带标记入**隔离桶**（它允许 crash_type 不一致，混入会污染变异算子归纳）；`none` 不入下游；`strict` 用于「确证同一 bug」子任务。
- **最终交付物**：`repro_dataset.jsonl`（增量追加、跨轮持续生长）。
- **工作方式 = 增量循环**（不设终点）：每轮挑几个项目/几十条 crash 端到端跑一遍并追加，`state.json` 续跑。**不追求一次性全量复现。**

## 0.2 进度（每轮一行；完整推理见 §7 → archive）

| 轮次 | 做了什么 | 关键结论 | 状态 |
|---|---|---|---|
| 预飞 M1–M12 + 审计 A/B/C | 12 项测量 + 3 项专项审计（纯本地、零 docker） | 推翻 10 条原设计决策（C-inject→官方工具、钉 `fixed^`、scope 限 C/C++、运行参数用实测默认值…） | ✅ |
| 修正 R1–R15 | 复算 + 补测，消灭口径污染 | R5 language exact-match（主线 3,502）、R7 空 target 净 156、R12 独立 worktree、R13a `fixed^` 选择 0 歧义、R14 组合 448 | ✅ |
| R16 增量模式 | 全量扩面 → 增量循环 | 缓存键加 `commit` 分量（防**假复现**）、撤回 fixed 硬分流恢复 HEAD-first、删机时/预算估算 | ✅ |
| R17 | 评审 R16 落地 | 缓存**路径**也要含 commit（构建成功即归档）、`--max-builds`、首轮=**标定轮非验收轮**、`run_id/run_ts` append-only | ✅ |
| R18 | 收尾 | HEAD 缓存分量 = **构建时解析的上游 SHA**（非字面 `"HEAD"`，否则跨轮复用旧二进制）、归档归 ② 独有 | ✅ 设计定稿 |
| **P0** | 首次真实 docker 构建 + 复现（md4c/OSV-2022-126） | 两个硬阻塞解开（worktree 建树、代理 path (ii)）；**observed vs recovered off-by-one** → strict 判定改「recovered top-3 ⊆ observed 全栈有序子序列」；N1/N2 | ✅ |
| **P0-B** | 修 §1.3④ + 打通 `fixed^` 主路径（pcre2/OSV-2024-1261） | **项目首个 strict 级复现**；off-by-one 主因=版本差；N3（OSV `fixed` off-by-one）/N4（era-retry 弄脏 worktree）/N5（浅克隆 detect_repo 阻塞 73%） | ✅ |
| **P0-C** | 统一代理覆盖 + 三处文档修正 | **三个 docker 调用点全覆盖 → N5 关闭**（两失败样本复验 EXIT=0）；N3 改静态 check 主判据 + 有界 walk-back；可用率拆两个数 | ✅ 前置验证结束 |
| **W1** | off-by-one 抽样 + 固化补丁 + 写 ⓪① | **off-by-one 14.3% → 默认仍钉 `fixed^`**；§1.3① 帧↔文件判据被否证 → 复合证据分；**N6**（OSV 退化 range 53 条）；`repo_path` 逐 crash 可解析 **97.5%**；补丁入 `repro-patches` 分支；**回归 29/29** | ✅ |
| **W2** | Phase0 四遗留 + 写 **②③④⑤⑥** + **首轮真跑**（6 项目/129 crash/54 次构建/143 次执行） | **流水线打通并产出数据**：12 条复现（**3 strict + 7 medium + 2 loose**）、113 none；**端到端可构建率 90.7%**（HEAD 100% / 钉版 76.2%，首次测到）；三条已知答案 ② 产物与手工构建**逐字节一致 3/3**；era 缓存实测**省 49.5%**；负对照 **8/8**；**N7–N17 十一条新发现**；查出并修掉自己写的 **13 个 bug** | ✅ 本轮 |
| **W3** | 改路由 + 归档裁剪默认化 + 修 N12/N17/N16 + 两次单发实验 + 扩样本（4 run / 27 条 / 30 次构建） | **R16 的 HEAD-first 被实测推翻**（`T_head/T_pin≈0.87` 非 8×；has_fixed 的 HEAD 复现 0.8% < break-even 6.2%）→ 按 `commit_source` 分流；裁剪两次回收 **377+889MB**、一轮净增长转**负**；**N8「i386 结构性不可复现」被配对实验推翻**；镜像污染**可自愈**（74→0）但 harfbuzz 仍 0/7（N19）；`not_located` 10 条走完 → **8 条全在 depth1**；**W1 策略模型作废**（实测 A≈21<C=23<W3=28<B=33）；**N18–N21**；自查修 **13 个 bug**（2 个造成不可逆数据损失） | ✅ 本轮 |
| **W4** | 数据完整性防御 + 简化路由（策略 A）+ 构建前预检与早停 + 扩样本 | ⑤ **单调性校验** + 裁剪**双字段交叉校验**/dry-run 默认/审计日志（**自测 12/12 拦住**）；4 个被误删归档**重建 20/20 逐字节一致**；静态 check 降 **advisory**、② 一律走**策略 A**（`plan_pinned` 52→44 行、少一条顶层分路、② −11 行）；**预检** harfbuzz 6/6 + pcapplusplus 3/3 命中、0 误报；**早停**生产触发 1 次（省至多 27 次构建）；**N22** 按 `job_arch` 构建使 **3/3 从 medium/loose 升 strict**；负对照改 HEAD 为默认 **11/11**；累积 **10 strict + 9 medium + 3 loose**、可构建率 **85.1%**；**N22–N24**；自查修 5 个 bug | ✅ 本轮 |
| **W5** | 销两笔旧账（N12 / N16）+ 四道完整性护栏 + 扩样本 19 条 + 选镜像的离线筛选 | **N12**：离线回放（**0 次构建**，反事实完全可观测）→ 阈值 0.6 触发 7 次 / 省 10 次构建 / **tier 损失 0**，但只有 **3 条不同 crash** → **默认 OFF + shadow 常开**，预注册翻转判据 n≥10；**N16**：离线注入跑**真** `build_pinned` 重试分支 **8/8**（含负对照）→ 「重跑一次」那条待办**作废**；**N25** 日志同名覆盖销毁已引用证据（轮转修复，生产已拦到 1 次）；**N26** manifest 覆盖护栏（生产拦下 3790→5 行、退出 4）；**N27** 预检自身三个缺陷（误报×2 + 漏检×1，已知答案回归 11 真报 / 0 误报）；**N28** 第三方依赖 URL 已死 = 老 commit 主导失败模式（libspng **1/19=5%**）；**N29** 「查不了」必须与「查过没问题」分级（ndpi 一度被排第 1，实为 0/N 灾难）。**扩样本**：19 条 → **2 strict + 4 medium**，累积 **12+13+3**、复现 **28/151=18.5%**、`not_located` 11→**14**；筛选淘汰 4 个项目（省 4×2.2GB）→ 推荐 **libredwg**。**第二轮：92 条积压重跑**（W2 在 HEAD 上跑过、其实都有 `fixed_commit` → 跑的是**已修好的版本**）→ chunk1 **23/23**、chunk2 **19/23**，**累积复现 28 → 70 条（46.4%）**、**39 strict + 16 medium + 15 loose**；根因是**排序键与 W3 改后的路由错位**（92 条位于默认序第 196–2996 位、历轮 `--limit ≤30` → 三轮都碰不到）→ `--sort` 默认改 `fixed_first`；**N12 按预注册判据翻转默认**（n=11、损失 0 → `--stop-frac` 0→**0.6**，但 11 条全是 c-blosc2 → 跨项目未证，多项目轮次仍跑对照）；**N30** 新回收路径绕过保护集删掉 W4 已交付的 strict 证据（已修 + **5/5 sha256 逐字节恢复**）；逐条回收使 72 次构建下归档**基本不涨**。chunk3 **22/23**（hunspell 为主，**16 条 medium** → 档位画像与 c-blosc2 明显不同）、chunk4 **11/14**（9 条被 W4 早停按设计跳过）→ **四块合计 131 次构建 / 202min / 75 条新复现**；**累积复现 28 → 103 条 = 151 条里的 68.2%**，tier **44 strict + 36 medium + 23 loose + 48 none**；**N16 生产触发 2 次、2 次都成功**（升 ✅）；N12 翻转后首次生产触发在 **md4c**（但跨项目证据仍缺，hunspell 一个候选都没产生 → 如实标注为「没有可检验的样本」而非「验证过没反例」）；逐条回收使 **131 次构建下归档仅 1088→1140 MB**。**第三轮：三次新项目尝试全部失败**（libredwg 因 `make check-prep` 撑爆磁盘+30min/次构建**不可行**、opensc **0/3** 死于 `-Werror`、libspng 5%）→ **4 试 0 中**，而五个老项目全部 92–100% 且**池已榨干**；筛选升级 **v2**（新增构建体量维度 + 确立「先 3 条探针再整池」流程，opensc 探针 10.5min 拦住 4 小时白跑）；**N31/N32**（含「crash 年份」这个直觉被实测否证）。**第四轮：openh264 探针 0/3**（首试 `#include 'codec_def.h'` 在该 commit 不存在 + era Dockerfile 的 `libstdc++-5-dev` 已从 focal 下架）→ 暴露**两道结构性天花板 N33/N34**；顺带修掉分类器「era 段报错压过首试真因」的缺陷（N28③，两次误导过我）。**W5 新项目 5 试 0 中**，而五个老项目 92–100% 且池已榨干 → **规模化撞的是基础设施墙、不是采样墙**。**第五轮：硬骨头重试**（7 条 / 33 次构建 / `--max-depth 6`）→ **3 条翻成 strict**，累积复现 **103 → 106 条（69.3%）**、**strict 44 → 47**；**深度假设成立但只对残差成立**（全复现记录表 106 条里仅 **1 条**需 depth>3 → 全局抬深度不划算，改为「默认 3 + 只对残差深重试」，残差命中率 1/7）；**架构假设被否证**（2 条 i386 硬骨头在正确架构下走完 6 格仍全 none → 我当时的推断超出了 N22 的证据范围）。新增**交付面审计**（6 组不变量）+ **牙齿测试**（注入 4 类违规全被抓，并**抓到审计自身的漏检**）。**第六轮：N33 离线预测器**（era Dockerfile 的 apt 包 × 本地 base-builder 的 `apt-cache policy`）→ **已知答案校验 1 真阳 / 5 真阴 / 0 假阳 / 0 假阴**，把「赌一个 2.9GB 镜像」变成「先量一次（秒级）」；跑完 12 个候选后结论是 **N33 不是剩余候选的主要屏障**（只 openh264 中，且它已实测死）；另修 **N34 盲点②**（整行裸脚本路径）→ **libxml2 立刻从 ⓘ 翻成 ⛔**，省下一次镜像+探针。**第七轮：N34 盲点③ 检测器**（fuzzer 源码的 `#include` 是否在该 commit 存在）—— **已知答案对上真凶**（openh264@`58576925544e` 离线报缺 `codec_def.h`，与真实构建日志一致），但**适用边界窄**：8 个候选全部 `no_sources` → 0 个新增淘汰；按 N29 显示「不适用」而非 `0/1`。**第八轮：mupdf 探针**（复现 +0，但挖出两个真缺陷 + 撞上第三道天花板）—— **N35** 非 github 的 `repo_url` 让 walk-back「零构建」静默失败（**实测挡住 542 条 / 17.3% / 32 个项目**，含 ghostscript 197）→ 镜像映射修好、双方法互证 SHA 一致；**N36** 预检第 4 盲点（raw 端点看不见 submodule）**一次挡死 mupdf 37 条** → 已修且回归 11 真报全中 / 误报 0；**N37** 构建源换镜像**实测无效**（`--repo_path` 指向镜像内预烘焙的 shallow 克隆，`git remote update` 仍走 `git://`）；**N38** 第四类天花板：慢速上游 + shallow 预克隆 → 单格 `TIMEOUT 3600s`、3 格 **240.2min / 0 复现**，而修复被「不改 Dockerfile」+「infra md5 固定」两条硬约束挡住 → **判 mupdf 不可行**（成本外推 ≤111h）。附带修掉 **`--help` 一直是坏的**（argparse help 里 `%` 未转义）+ 清 1.8GB 孤儿临时目录 + 确立「杀构建后必须手工还原 worktree」规程。**第九轮**：只读查看器 `show_repro.py` **暴露 N39**（不剥 C++ 签名 → **17 条 hunspell medium 实为 strict**、tier 应为 **64/19**，并推翻 §4.44 一个结论；未修待定）+ **N40 已修**（`logs/reproduce/` 一直被覆盖、N25 只修了 build 侧；轮转移进 `repro_common` 单一权威实现）。**第十轮**：归档布局两问 —— 数据文件是**运行时依赖**（0.02%）；物理按类型重排不可行（**6/84 归档跨多类型**）→ 改**符号链接视图** `by_crash_type/`（11 类/106 条，经链接重放实测成功）；顺带修掉 **N41 删库地雷**（6 处改 `realpath`）。**第十一轮**：**`--purge-on-verify` 默认由开改关** —— 用户质疑「重放不是需要二进制吗」成立，我此前用「可 bit 级重建」偷换了「重放能力」；实测重建成本 **64 归档 / 1.7h / 2.8GB / 缺镜像 0**（付得起），而「非删不可」的 145GB 依据**只在跑满 3,093 条队列时成立**（新项目 6 试 0 中 → 跑不满）。新增 `rebuild_archives.py`（`--commit-override` 精确重建 + sha256 bit 级校验）；`by_crash_type/` 改 **commit 下挂 OSV 层** → 一条 crash = 一个自包含文件夹（`binary`/`testcase`/`report.log`/`INFO.txt`），实测经相对符号链接重放成功。**第十二轮：libavc 打通、新项目 7 试 1 中** —— 全量重建 **64 归档 / 498 文件 sha256 全一致**；**N42 Gitiles 解析器**解锁 googlesource 系 112 条（不需镜像）；离线筛 92 条 → **libaom 0/14 ⛔ 淘汰**、libavc 40/43 选中；探针 **3/3 / 5.6min** → 整池；**N43** 分类器漏形态 + `commit_not_found` 被误列进「版本确定性失败」→ **早停误伤 33 条**（同轮 10 条里 7 条成功即反证），修后**重跑 29/33 = 88%**。**复现 106→139、strict 47→63**、c-blosc2 占比 58%→44%、`T_strict` 首次有区分力（0→3）。另修 **N44**。**第十三轮：libhevc + libwebp 打通、项目数 7 → 9** —— libhevc **10/28**、libwebp **3/10**，**预检预测与实测双向印证**（libwebp 预测拦 2 → 实拦 2）。**⭐ MSAN flaky 重试首次拿到生产证据**：`retry_count>0` 从恒 0 变 **9 条**（全 memory），`attempts=[0,1]` 的 2 条是**重试救回的复现**、`[0,0,0]` 的仍如实记 none（未退化成造假工具）→ **销掉一笔挂了两轮的账**。**复现 139→152、strict 63→69、memory 10→17**、c-blosc2 占比 44%→**40%**；提炼出「**全量 https 克隆是新项目成功的必要条件**」（9 试 3 中）→ 可作离线硬前置。**第十四轮：用户一个结构问题拽出 4 个真缺陷（N45–N49）** —— ⑤ 连接键优先级反了 → 2 条复现记录表指向没崩的那格、重放 **exit=127**；libFuzzer **超时被当复现** → 虚高 1 条；`exit_code` 不可作判据（3 条 libwebp exit=0 却是真崩溃）；审计只查「是不是目录」故报 0 红线。**全部修在根因上**并**实测重放 exit=1 + ASan ABRT** 收尾；交付视图 `binary` 收窄成**单个 driver**、整棵树为 `out/`。**复现 152→151**、driver 在盘 **151/151**、151 条目断链 0。**本轮 4 个缺陷无一是自测或审计发现的**——全部源于用户看着交付物提问 → 交付视图是**最有效的评审界面**。**第十五轮：交付视图重做 + 首次全量重放验收** —— 用户第二次指出「一个 OSV 为什么有多个二进制」→ 改为只放**精确最小重放包**，**151/151 每条恰好 1 个 ELF**、硬链接额外 **0 字节**、128 条文件夹只有 5 个条目。**推翻我自己写进文档的结论**（「只给 driver 会重放失败」是 W2 个案的过度泛化；`ldd` 无 `libclang_rt.*.so`、14 组合真跑全崩）。**N47 破案**：libwebp target 是 shell 包装脚本、末行 `chmod -x` 吃掉退出码。**N51**：`replay.sh` 漏抄 `runtime_limits` → 2 条 **strict** 重放成 OOM，补参数后 2/2 稳定复现。**N52 首次全量重放验收 151/151 = 100%**（首轮 148 / 2 条第 3 次 / 1 条 i386 第 8 次、崩溃率 12%，且崩时给出的正是期望类型 → N15 形态的首个直接证据）。**本轮 7 个自身缺陷全部由真跑抓出。****第十六轮：N39 落地（strict 69 → 86）+ N53 红线** —— `strip_cpp_signature` **只挂 observed 侧**、11 例已知答案取自真实帧；**先干跑（升档 17 / 降档 0）再重跑 ④⑤ 落账** → **strict 占复现 45.7% → 57.0%**、medium 51 → 34；1 条不升是对的（R 首帧是模板类型名）。⚠ 明确口径：**这不等于 `T_strict=1.0` 被验证**（升档 17 条 subseq 全是 1.0，刻度样本仍 3 条）。**N53**：用户两次指出的「一个 OSV = 一个二进制」写成审计红线 + 牙齿测试 → **151/151 每条恰好 1 个 ELF**。**第十七轮：N54–N60 + unicorn（第 10 个项目）+ UBSAN 缺口破了** —— 解析器**回显假 SHA** 造出「假淘汰 + 假放行」两个假结论（修 4 处）；**又推翻我自己的一条规律**（`git://` 可达、`--depth 1` 由 infra 自己 unshallow → 真判据是实测吞吐，ghostpdl 29 KB/s ⛔）；分类器裸 `-Werror`/`unsupported`/`ninja-build` 命中**成功行/路径名/apt 行**（收紧 + 新增 `era_dep_drift`，复判历史 9 条**行为不变**）；带证据淘汰 radare2 / kimageformats / matio / ghostscript；**unicorn 探针 3/3**、N59 归一化修 2 处 → 2 条 loose→medium、N60 补审计盲区 2 条红线；⚠ **「bit 级可重建」加限定**（libavc 5/5 sha 不符，但重建件 7 次崩 6 次）。**复现 151→154、项目 9→10、UBSAN 0→1**；磁盘靠清 `build/`+悬空镜像回收 5.0G（现 4.1G，**紧**）。**第十八轮：磁盘分级保留策略（N61）** —— 先量字节去向再动手，发现 ① 交付是**硬链接**进归档，「删归档」对交付必需的 1.50G **不释放空间**；② **「按 tier 分级」被实测全面压制**：`tier=strict` 只回收 4.38G，**`reuse`（只保护服务 >1 条的归档）回收 7.09G 而只留 698M 有用的**（119 个被引用归档里 **100 个只服务 1 条**）。执行后**可用 3.0G→13G、归档 8.5G→2.2G**，自校验 + 审计全过，已接进 `run_repro.py --post-clean`（默认开、纯废物无条件清、动归档受阈值门控）。⚠ 量出 **unicorn 整池要 37GB 跑不起** → 改定向小批（UBSAN+MSAN 6 条）。**「期望 unknown」判据经用户裁定保持现状**（17 条结构性压在 loose，只记录不放宽）。**第十九轮：N62 水位线 → N63 误删在飞归档 → N64 磁盘写满事故** —— 一条「加安全机制却暴露两个更深的坑」的完整链条：水位线✅生效（触发 3 次、6.7G↔12G 震荡、产出 7 条复现）；轮中清理**删掉本轮在飞归档**（`needed_map` 只看复现记录表 → 在飞行被判孤儿）→ 4 条受害、15 个归档删了 14 个，修 `--protect-since`；修完**保护 7.29GB 本身把盘占满** → 可用掉到 **68KB（100%）**、进程僵死，修 `--disk-hard-floor-gb` 优雅停轮；恢复后 **2.0G→9.2G**、归档 13G→5.0G、交付 162 条全自包含、审计 0 红线。**第 19 套自测**（专抓 Python 静默生效缺陷：重复定义/重复常量/悬空异常名/**真跑 --help**）当场抓到 2 个 `--help` 崩溃 —— 我刚写的「100% 满」与 **W3 潜伏至今**的 `manifest_builder.py`「45.7% vs HEAD 6.7%」。**复现 156→162、unicorn 5→11、memory 18→20**。自测 **19 套 351 项全绿**；本轮 **56 个自查缺陷** | ✅ 本轮 |
| 下一步 | 补样本（挑**可构建**的项目） | ①`not_located` 补到 ≥30（现 **11**，还差 ~20）②**UBSAN 正样本**（换 libvips/hdf5/kimageformats，需新镜像 ~2.2GB）③MSAN flaky 重试路径 ④N12 的 `frac≥0.6` 即停（🅗，n=1 支持）⑤预检覆盖率仅 **56/249** 项目，其余 176 个 build.sh 提不出候选路径 | 待开工 |

## 0.3 关键数字速查

| 项 | 值 | 来源 |
|---|---|---|
| crash 总数 / C/C++ 主线 / 非 C/C++ / name-miss | 3,790 / **3,502** / 246 / 42 | ✅ R5 exact-match |
| C/C++ 项目数 / HEAD 构建组合 `(project,sanitizer)` | 271 / **448** | ✅ R14 |
| C/C++ sanitizer 分布 | ASAN 2,874 / MSAN 427 / UBSAN 176 / 空 25（空→按 ASAN 试跑） | ✅ R14/R16 |
| has_fixed / no_fixed | 3,550 / 240（no_fixed 中 **226 有 introduced**、14 都没有） | ✅ M4/R1 + **W1 修正** |
| 钉版回退链覆盖 | `fixed^` 3,550 → `introducing_commit` 226 → HEAD 14 | ✅ W1 |
| 空 fuzz_target / 可推定 / 不可复现 | 535 / **156**（181−25 unrar M2-未命中）/ **379**（= 27 无 target 项目 + 327 多 target + 25 unrar） | ✅ M9/R7 |
| 缺失 testcase | 35 | ✅ `_MANIFEST_missing.txt` |
| recovered 帧覆盖 / 恰 3 帧 | 3,770/3,790 / 94.4% | ✅ M10/审计A |
| `T_build`（~~n=1 的 5–10min~~ → **W2 实测分布**） | HEAD n=33 **中位 68s**（9–428s）；钉版 n=16 **中位 73s**（14–577s）。逐项目差 **47 倍**：md4c 9s / hunspell 53s / libtsm 68s / c-blosc2 75s / pcre2 274s / flatbuffers 428s → **`--max-builds N` 不能一律换算成 N×5–10min** | ✅ W2（49 次成功构建） |
| **era 缓存节省**（N4「省约一半」） | 同 commit 配对 **577.3s → 291.7s = −49.5%**；c-blosc2 **157s → 79s = −50%**；产物 sha256 **不变**；era commit 解析值 `a958ed8e` 与 P0-B 记录一致。⚠ 跨项目直接分组会得出**相反**结论（混淆变量） | ✅ W2 |
| **端到端可构建率**（P0-C 拒绝用 detect_repo 98% 冒充的那个数） | **49/54 = 90.7%**；HEAD **33/33 = 100%**、钉版 **16/21 = 76.2%**。⚠ 6 项目、选样非随机，**不可外推**到 249 项目；flatbuffers 钉版 **0/4**（A2 工具链漂移，era 自愈救不了） | ✅ W2 首测 |
| **首轮复现产出** | 129 条 crash / 125 跑 → **12 复现**（**3 strict + 7 medium + 2 loose**）+ 113 none + 4 未跑；HEAD yield **0/118**（fixed_parent·introducing 组）、libtsm head 组 **6/6**（但其 HEAD 冻结在 **2014-04-24**，早于报告年 → **不可外推**） | ✅ W2 |
| **observed 帧形态**（E4） | 137 帧：内部帧 **57.7%**、无符号模块帧 **0%**、`.part.NN`/`.constprop.NN` **0**、符号化失败 **0%** → **轻量归一化够用，`clusterfuzz` StackParser 不必装** | ✅ W2 |
| **负对照** | **8/8 通过**（c-blosc2：目标 bug 崩 + 同项目其他 3 条全 none + 随机 256B none + 别项目 testcase none；libtsm 同项目对照只 1 条，因该项目 7/7 全复现 → 判据在该项目**不可满足**，如实记） | ✅ W2 |
| **构建 bit 可确定性** | md4c@HEAD 连跑 3 次（含清空 `build/out`+`build/work` 冷建）sha256 全等；pcre2 在「era 未命中/命中」两路径 sha256 全等；三条已知答案与 P0 系列手工构建**逐字节一致 3/3** → `binary_sha256` 可作 `(project,san,commit)` 一致性校验 | ✅ W2 |
| `job_type` 架构（**N8**） | i386 **164**（可执行 3,136 中 **163** = 5.2%）/ x86_64(无标记) 3,606 / 空 20 → x86_64 构建下**结构性不可复现**先验 | ✅ W2 |
| `pinned_queue` 排序（Phase 0(b)） | 键 = **`(project, issue_id)`**；相邻同项目对 **432 → 2,844**（= 理论上限）；issue_id 对真实 commit 日期的**同年组内** Spearman **+0.733**（优于 osv_id +0.478、published +0.456）；era 邻接命中 **65.9%** vs 52.4%（真实日期上界 69.5%）；era 窗口实测中位 **32 天** | ✅ W2 |
| **off-by-one 率**（OSV `fixed` 不是真修复） | **6/42 = 14.3%**（Wilson 95% 6.7–27.8%；年后分层加权 11.8%） | ✅ W1 |
| `fixed` 精确率 / 静态法定位不到 / 托管不支持 | 59.5% / 26.2% / 12.5% | ✅ W1 |
| 须钉深度 depth1/2/3 | 25 / 3 / 3（**off-by-one 不止一格**） | ✅ W1 |
| OSV 退化 range `introduced==fixed`（**N6**） | 60 对 / 53 记录 / **53 crash（1.4%，C/C++ 36）** | ✅ W1 |
| `repo_path`：假设 (A) 成立率 / 逐 crash 可用率 | 89.7%（C/C++ 项目）/ **97.5%**（+candidates 运行期 = 99.0%） | ✅ W1 |
| detect_repo 可达率（**≠ 端到端可构建率**） | 修 N5 前 19%（49/257）→ 修后 ~98%（253/257 git-clone） | ✅ P0-B/P0-C |
| 主树脏项（driver_create 研究线，**不动**）/ worktree | **550** / `repro-patches` @ `07522dc0e`，69M | ✅ 审计B/W1 |
| manifest 全量产出 / 回归验证 | 3,790 条 × **47 字段** / **33s**（含 N6 复核 53 次网络；~~787s~~ 的 sleep bug 已修）；3 条已知答案 **29/29 字段全对**（其中 hunspell 4 个字段 W2 起标**争议不计分**，见 N9） | ✅ W1 + **W2 修正** |
| `repro_dataset.jsonl`（**交付物**） | ~~142 行 / 129 条 / 51 字段~~ → **152 行 / 131 条唯一 / 82 字段**，append-only 跨 7 个 `run_id`；归档区经两次裁剪 782MB → **278MB / 7 目录**（`_shared` 2 变体硬链接不动） | ✅ W2+**W3** |
| **累积 tier / 复现率** | **4 strict + 10 medium + 4 loose + 113 none**；复现 **18/131 = 13.7%**；按项目 = libtsm 7 + c-blosc2 11 | ✅ W3 |
| **累积端到端可构建率** | **69/81 = 85.2%**（HEAD **34/34=100%**、钉版 **35/47=74.5%**）；逐项目 c-blosc2 28/29、hunspell 11/11、md4c 12/12、pcre2 10/10、libtsm 3/3、flatbuffers 5/9、**harfbuzz 0/7**。⚠ 7 项目便利样本，**不可外推** | ✅ W3 |
| **路由 break-even**（W3 改路由的依据） | has_fixed 的 HEAD 复现 **1/119=0.8%**（上界 4.6%；排除 libtsm 冻结 HEAD 则 0/118、上界 3.2%）；`T_head/T_pin` 同项目中位 **0.87**；k=20.8（样本）/7.76（总体）→ break-even **6.2%/13.5%** > 4.6% → **跳过 Stage1** | ✅ W3 |
| **静态 check 的 located 率依项目** | 3 项目 199 条：located **138/158=87.3%**、depth **1×130/2×2/3×6**（94.2% 只需 depth1）；W1 的 41 项目分层抽样是 64.6% 与 25/3/3 → 🅗 **不可跨项目外推** | ✅ W3 |
| **`not_located` 桶真实 depth** | 走完三格 **10 条**（W2 1 条）→ **8 复现全在 depth1**、2 条三格全空；累积 11 条 = **1×9、无 depth2+** | ✅ W3（n 仍不足以定 A/C 优劣） |
| **归档裁剪** | 存量 **回收 377MB**（17→6 目录）；`w3-p5-cb` 轮末 **回收 889MB**（22→7）；该轮 14 次构建 +644MB → **净 −245MB** | ✅ W3 |
| **i386**（N8 复核） | 配对实验：c-blosc2@`861ba79f` 同 commit 两建 → i386 **崩**（4-byte、`_default`）/ x86_64 **崩**（8-byte、`_bmi2`），tier 同为 medium；另 2 条 i386 crash 在 x86_64 下复现 → **N8 推翻**。i386 可建上限 = **161/163（99%）**（97 个项目声明支持） | ✅ W3 |
| **镜像污染自愈** | harfbuzz `docker rmi` + worktree `build_image --no-pull`（2m17s）→ `/src` 注入源 **74→0**；gate 第⑤条改为**自动重建+复检** | ✅ W3 |
| **累积 tier / 复现率** | **10 strict + 9 medium + 3 loose + 110 none**；复现 **22/132 = 16.7%**；按项目 libtsm 7 + c-blosc2 15 | ✅ W4 |
| **累积可构建率** | **86/101 = 85.1%**（HEAD **35/35=100%**、钉版 **51/66=77.3%**）；15 次失败全来自 harfbuzz(0/7)+pcapplusplus(0/3)+flatbuffers(4/9 失败) | ✅ W4 |
| **按 sanitizer / job_arch 复现率** | `address` 20/127=**15.7%**、`memory` 2/3=**66.7%**、`undefined` **0/2**；`x86_64` 18/102=17.6% vs `i386` 4/30=**13.3%**（差异不显著 → 再证 N8 不成立） | ✅ W4 |
| **策略成本（三张表并列，见 §4.27）** | W1 模型「B 省 12.3%」= **0 次真实构建**、⛔作废；W3 实测 A≈21<C=23<W3实现28<B=33（n=13）；**W4 策略 A 首跑 located：10 条 / 7 次真实构建 / 9 strict**，advisory 与 best_depth 一致 7、A 更浅 1（n=10） | ✅ W3+W4 |
| **构建前预检（N19 两形态）** | harfbuzz **6/6** + pcapplusplus **3/3** 命中、已知能建的 6 条 **0 误报**；成本 0.0–22.6s/条 vs 白跑构建 90–320s；**覆盖率仅 56/249 项目**（176 个 no-op、17 个无 build.sh） | ✅ W4 |
| **按 `job_arch` 构建（N22）** | 配对 **n=3，3/3 从 medium/loose 升 strict**；其中 1 条 x86_64 下崩成**另一个 bug**（use-after-free）而 i386 下是**期望的** HBO + 帧逐字相同 | ✅ W4 |
| **归档重建 / bit 确定性** | 4 个被误删的 verified 归档重建 → **20/20 文件逐字节一致**（4 commit × 5 文件；3 次走 era 预 checkout 路径） | ✅ W4 |
| **数据完整性防御** | ⑤ 单调性校验 + 裁剪双字段交叉校验/dry-run 默认/审计；**自测 12/12 拦住**；生产 `prune_audit` 2 条（`M=0`）、`dataset_guard` 4 条（出自自测） | ✅ W4 |
| **负对照（W4 定稿判据）** | HEAD 为默认 + 版本感知补充：**11/11 通过 + 正对照 2/2**（W3 那条「失败」经查是窗口冲突下的**真阳性**，已重新归类、保留为正面结果） | ✅ W4 |
| **N12 离线回放（0 次构建）** | 5 run / 24 crash / 31 格；阈值 0.5–1.0 **结果完全相同**（5 触发 / 省 7 格 / **tier 损失 0**）；但只 **3 条不同 crash**（嵌套重复计数）、c-blosc2 占 20/24 → **默认 OFF**，还差 7 条才够翻转 | ✅ W5 |
| **N12 生产对照（同 crash、同缓存构建）** | A 轮默认：3 格、shadow 3 格全 True、`stop_reason=None`；B 轮 `--stop-frac 0.6`：**depth1 即停、省 2 次构建**、`stop_reason='frac'`、tier 同为 loose（**无损失**） | ✅ W5 |
| **N16 重试机制** | 离线注入跑真 `build_pinned`：**8/8**（网络失败→重试 1 次+`*_retry1.log`+成功则 `ok`；仍失败→只试 2 次；compile_error→不重试；`--no-retry-network`→不重试）+ **负对照**证明有牙。账目状态：机制 ✅ 已验证 / 生产触发 ⓘ 仍未观测 | ✅ W5 |
| **完整性护栏（3 道，全 TDD）** | 日志轮转（N25，7 项）+ manifest 覆盖护栏（N26，14 项，**生产拦下** 3790→5 行、退出 4）+ ⑤ 字段透传（11 项，TDD 抓到 `walkback_stop_reason` 丢失）；② 分类器自测**固化** 18 项（此前只是内联 heredoc → §6 的「可复算」是空的） | ✅ W5 |
| **自测总量** | **8 套全绿**：③4/4、④4/4、W4 防御 12/12、②轮转+N16 15、⑥停止判据 19、②分类器 18、⑤透传 11、①护栏 14；① 回归 **25 通过 / 0 不符 / 0 跳过 / 4 争议**（命令须带 flag，见 §6） | ✅ W5 |
| **扩样本第一轮（`w5-expand19b`）** | 19 条 / **21 次构建** / 41.6min → **2 strict + 4 medium + 13 none**（本轮复现率 **31.6%**）；累积 **12 strict + 13 medium + 3 loose + 123 none**、复现 **28/151 = 18.5%**；`not_located` 11→**14**（距 ≥30 差 16） | ✅ W5 |
| **MSAN 口径** | 本轮 6 条复现**全是 MSAN** → MSAN 累积 **8/14 = 57%** vs address 20/137 ≈ 15%。⚠ **选择效应非因果**（19 条池子里 11 条本就是 memory）；**flaky 重试仍未触发**（151 条 `retry_count>0` 为 **0**）→ 靠扩样本撞上概率低，需人工构造 | ✅ W5 |
| **可构建率（按项目，累积）** | hunspell 12/12、libtsm 3/3、c-blosc2 51/53=96%、md4c 12/13=92%、pcre2 14/16=88%、flatbuffers 5/15=33%、**libspng 1/19=5%**、harfbuzz 0/7、pcapplusplus 0/3 → **便利样本外推会显著高估**（N28） | ✅ W5 |
| **预检已知答案回归** | **真报 11/11**（harfbuzz 4/4 形态①、pcapplusplus 3/3 形态②、libspng 4/4 形态②）+ **误报 0**（6 个项目 23 个已成功 commit）+ 契约 2 项 | ✅ W5 |
| **选镜像的离线筛选** | 池 **2,801 条 / 239 项目**；⛔ 淘汰 **ndpi·fluent-bit·mruby·openexr**（错配 3/3）→ **省 4×2.2GB 镜像 + 数小时白跑**；✅ 有正证据 **libredwg(68)·radare2(56)·opensc(79)**；ⓘ 无证据 7 个（含 ghostscript 192，`git://` 判不了）→ **建议先建 libredwg** | ✅ W5 |
| **积压重跑（第二轮）** | 92 条「跑错版本」的积压 → chunk1 **23/23**、chunk2 **19/23**；**累积复现 28 → 70 条 = 151 条里的 46.4%**，tier **39 strict + 16 medium + 15 loose + 81 none**；72 次构建 / 104.5min | ✅ W5 |
| **两条路线的复现率（决定性对照）** | **HEAD 7/105 = 6.7%** vs **钉版 walk-back 21/46 = 45.7%**（**6.8×**）→ 那 104 条「建成功却没崩」里 92 条是**在已修好的版本上跑的**，不是复现失败 | ✅ W5 |
| **排序键与路由错位（根因）** | 92 条积压在默认序 `no_fixed_first` 里位于第 **196–2996** 位（中位 1650），历轮 `--limit ≤30` → **三轮都碰不到**；已改默认 `fixed_first`（TDD 断言默认值） | ✅ W5 |
| **N12 翻转默认** | 预注册判据「distinct-crash n≥10 且 tier 损失 0」**已满足**（n=**11**、触发 22、省 **32** 次构建、损失 **0**）→ `--stop-frac` 默认 **0→0.6**。⚠ 11 条**全是 c-blosc2** → 跨项目泛化未证；判据没写多样性要求，故**照预注册翻**（事后加条件＝移动球门），多项目轮次另跑 `--stop-frac 0` 对照 | ✅ W5 |
| **逐条回收（purge-on-verify）** | 每条证据落盘后立即删其钉版归档 → **72 次构建下归档 1088→1137 MB（基本不涨）**、磁盘持平 7.4–7.7G；行留住 sha256+配方并标 `binary_pruned`。**事故 N30**：绕过保护集删掉 2 条 W4 已交付 strict 证据 → 已修 + **5/5 sha256 逐字节恢复** | ✅ W5 |
| **积压重跑最终账（四块）** | 92 条积压 → 83 条进复现记录表、**75 条新复现**；**累积复现 28 → 103 = 151 条里的 68.2%**；tier **44 strict + 36 medium + 23 loose + 48 none**；131 次构建 / 202min；按项目 c-blosc2 60 · hunspell 24 · pcre2 9 · libtsm 7 · md4c 2 · libspng 1 | ✅ W5 |
| **N16 生产触发** | **2 次触发、2 次重试都成功**（`5a65e3d8322f` +80s→ok、`ac116b4bac72`→ok）；首试日志**完整保留**（`*_retry1.log` + N25 轮转）→ 与 W2 那次「证据被覆盖」形成对照。账目升 **✅** | ✅ W5 |
| **档位画像依项目而异** | hunspell 22 条复现里 **16 条 medium、仅 1 条 strict**；c-blosc2 以 strict 为主 → **strict 率不是全局常数**，跨项目外推必须分项目看 | ✅ W5 |
| **新项目命中率（决定规模化成本）** | W5 试了 **4 个新项目 → 0 个可用**：libspng **1/19=5%**、libtiff 无构建记录、libredwg **不可行**（30min+/次 + 磁盘爆）、opensc **0/3**；对照五个老项目 **92–100%** 且**未采样池已全为 0** | ✅ W5 |
| **筛选 v2 的结果** | 14 个池≥20 的未试项目里 **没有一个 ✅ 级候选**：⛔ 路径错配全中 4 个（ndpi/fluent-bit/mruby/openexr）、⚠ 外链多 3 个 + repo 偏大 3 个、ⓘ 证据不足只能探针 4 个（openh264 含 15 MSAN+2 UBSAN+13 i386、mupdf 含 30 MSAN） | ✅ W5 |
| **规模化余量** | 主线 3,136 条里 **2,984 条从未进复现记录表**（全需新镜像，池≥20 的项目 40 个）；真·剩余积压 **10 条已跑完 → 复现 0**（**积压彻底穷尽**）；磁盘 **9.0G**（同时只容 2–3 个镜像） | ✅ W5 |
| **两道结构性天花板（N33/N34）** | ① **era-retry 失效**：当期 Dockerfile 钉的包已从发行版下架（openh264 的 `libstdc++-5-dev`）→ 官方唯一兜底救不了，且 2020–2021 年的项目**普遍**如此；② **预检第三盲点**：fuzzer 源码的 C++ `#include` 缺头文件（`codec_def.h`），路径存在性检查看不到 → **预检通过是必要不充分条件，探针不可省** | ✅ W5 |
| **分类器修复（N28③）** | 改为**首试段优先**（以 `Retrying on earlier OSS-Fuzz commit` 切分）+ 新增形态③模式；openh264 那条由 `dockerfile_drift`/detail=`OpenPACE…`（错）→ **`buildscript_mismatch`**/detail 指向 `codec_def.h`（对）。早停计数行为不变（两类同属 `DETERMINISTIC_FAIL`）；分类器自测 18→**23 项** | ✅ W5 |
| **积压归零（含度量修正）** | 真·积压 **0** 条。旧口径误报 4 条 → 拆为 **1 条终止性 HEAD-only**（N6 退化 `introduced==fixed`，**按设计禁钉版**；且它是已采样集合里**唯一的 UBSAN 候选**）+ **3 条钉版已试过、每格构建全失败**（flatbuffers，`dockerfile_drift` = N33 第二个实证）。缺陷在度量侧（只看 `commit_source`，漏了「钉版试过但无 observation」与「N6 禁钉版」），**已修**；回核确认当初那 92 条**没算错**（重跑后 75 条立刻复现即为证） | ✅ W5 |
| **UBSAN 零正样本的确切原因** | 不再是「没找到」：已采样集合里唯一 UBSAN 候选 = **N6 退化 → 禁钉版**；openh264 池里那 2 条属 **0/3 不可构建**项目 → 要销账必须找到「UBSAN + 非退化 + 项目可构建」三者同时成立的对象，**前提是先建新镜像** | ✅ W5 |
| **交付面审计（复现记录表自洽性）** | 新护栏 `w5_audit_delivery.py` 审 6 组不变量（tier↔评分自洽、verified 行指纹/配方齐全、**verified 悬空=0**、`run_status`、溯源字段、外推警示）→ 真复现记录表 **0 条红线违反**（103 条 verified）；**牙齿测试注入 4 类违规全被抓、退出 1，真复现记录表仍绿** | ✅ W5 |
| **牙齿测试抓到的审计自身缺陷** | [3] 的 medium/loose 判据被我写成 `… and n_recovered_frames`，而该字段**复现记录表里常为 None**（⑤ 未透传 ④ 的它）→ 条件恒假、`recovered` 为空的行**从未被检查**。重读 ④ 分支后确认该前置**多余且有害** → 删掉。**对真复现记录表它永远是绿的，只有注入测试能暴露** | ✅ W5 |
| **最终交付面（W5 收尾）** | dataset **284 行 / 153 条唯一 / 21 个 run**；**复现 106/153 = 69.3%**；tier **47 strict + 36 medium + 23 loose + 47 none**；按项目 c-blosc2 61 · hunspell 24 · pcre2 10 · libtsm 7 · md4c 3 · libspng 1；按 sanitizer address 98 · **memory 8 · undefined 0**。审计 **0 条红线违反** | ✅ W5 |
| **命中深度分布（决定 `--max-depth`）** | 106 条复现行：**depth1 = 87、depth2 = 9、depth6 = 1、无深度 = 9** → **仅 0.9% 需要 depth>3** ⇒ 全局抬到 6 会让构建量最多翻倍而增益 ~1%，**不划算**；正解是「默认 3 + **只对残差**（3 格全 none 且构建都成功）做 depth 6 深重试」→ 残差命中率 **1/7 ≈ 14%**（高一个量级，因为残差本身是被筛过的可疑集合） | ✅ W5 |
| **架构假设被否证** | 2 条 i386 硬骨头（OSV-2021-766 / OSV-2022-886）在**正确架构**下走完 **6 格仍全 none** → 架构不匹配**不是**它们不复现的原因。⚠ 与 N22 不矛盾：N22 说的是「架构错配会让**已能复现**的 crash 掉档或撞上别的 bug」，**从不保证**「按对架构建就能复现」——我当时的推断**超出了 N22 的证据范围** | ✅ W5 |
| **N33 离线预测器（已知答案校验）** | era Dockerfile 的 apt 包 → 本地 base-builder 里**一次** `apt-cache policy`：**1 真阳**（openh264 判 ⛔，对上实测 0/3）/ **5 真阴** / **0 假阳 0 假阴**。成本 = 每项目 1–2 次 HTTP + 全部共用 1 次 docker run ⟷ 建镜像 2.3–2.9GB + 探针 10–30min | ✅ W5 |
| **N34 盲点②修复的实效** | `SCRIPT_RE` 加「整行就是裸脚本路径」形态（libxml2 的 build.sh 全文只有 `fuzz/oss-fuzz-build.sh` 一行）→ 重跑筛选后 **libxml2 从「ⓘ 证据不足」翻成「⛔ 路径错配 2/2」**，**一个正则修复省下一个 52 条池项目的镜像 + 探针**。回归：已知答案 **11 真报全中 / 24 个已成功 commit 误报 0** | ✅ W5 |
| **筛选终局** | 12 个池≥20 的未试项目：⛔ 路径错配 **5 个**（ndpi/fluent-bit/mruby/openexr/**libxml2**）、⚠ 外链多 3 个 + repo 偏大 3 个、ⓘ 只能探针 2 个（libavc/mupdf）、**✅ 级 0 个** → 结合新项目 **5 试 0 中**，扩规模已无离线可辨的高性价比目标 | ✅ W5 |
| **N34③ 检测器（已知答案校验）** | `precheck_includes()` 对 openh264 **实测失败的那个 commit** 离线报缺 `codec_def.h`/`codec_app_def.h`/`codec_api.h` —— 与真实日志 `fatal error: 'codec_def.h' file not found` 一致 → **不建镜像、不跑构建就复现了那次失败的真凶**。成本 20–24 次 HTTP/项目 → **只做筛选维度**（N24：不接进每次构建前） | ✅ W5 |
| **N35 爆炸半径（本轮最大产出）** | 可执行池 3,136 条里 **542 条（17.3%）/ 32 个项目**的 `repo_url` 非 github/gitlab → `resolve_commit_meta()` 返回 None → **walk-back 零构建静默失败**。此前「钉版 + 非 github」的组合 **100% 死在这一行**（已跑的 11 条非 github 全靠 `commit_source=head` 绕过）。修好后 mupdf 3 条各排出 3 格真 SHA | ✅ W5 |
| **新项目 6 试 0 中，归因已达 4 类天花板** | libspng 5%（N28 死外链）· libtiff 无构建 · libredwg 不可行（体量）· opensc 0/3（`-Werror`）· openh264 0/3（N33+N34③）· **mupdf 0/1（N38）**。其中 **N33/N34③/N28 已能离线判**，`-Werror` 与 **N38 离线判不了**（N38 最贵：要先建 3.11GB 镜像 + 烧 3,600s） | ✅ W5 |
| **适用边界（诚实记录）** | 8 个池≥30 的候选跑这一维**全部 `no_sources`** → 它们的 Dockerfile 不把 fuzzer 源码 `COPY` 进 `$SRC`（openh264 那种形态），故该维度**不适用**、**0 个新增淘汰**。筛选表显示「不适用」而非 `0/1`（N29：查不了 ≠ 查过干净），并把边界本身钉进自测 [F] 节 | ✅ W5 |
| **N39 影响面（tier 分布被低估）** | 按「剥 C++ 签名后重算」跑全部 106 条 verified：**17 条 hunspell 的 medium 应为 strict** → tier 应从 `47 strict / 36 medium` 变 **`64 strict / 19 medium`**；并**推翻** §4.44「hunspell 档位画像与 c-blosc2 明显不同」（那是归一化缺口的假象）。**重判级不需要任何构建**（observations 全在盘上、只重跑 ④⑤），且属**升档**、单调性护栏允许 | ⚠ 未修，待定 |
| **「没崩的日志」该不该删** | **不删**：30 个 `exit=0` 日志只占 **48 KB**（= 项目总占用 **0.0036%**），却是**分母的唯一证据**（19 条建成跑了不崩 + 9 条构建失败 + 2 条从未真跑）。另核实 `exit≠0` 的 106 个文件与复现记录表 `reproduced_any=True` **完全同一集合**（双向差集空）；但**不能只看退出码**（UBSAN 可 `exit=0` 却算崩，M11）—— 唯一那条 UBSAN（`OSV-2017-126`）已核为**判 none 正确**（无 `runtime error`、`binary_source=head_state_cache` = 跑在已修复的 HEAD 上） | ✅ W5 |
| **归档里的 `.aff`/`.dic`/`.options` 为什么必须在** | **不是垃圾，是二进制的运行时依赖**（占 **0.2MB / 1048.5MB = 0.02%**）：③ 重放 `cd /out` 后按相对名读它们。✅ **踩过的事**（W2 bug 修 A）：缺 `monster_test.bfbs` → flatbuffers `monster_fuzzer` 在 `LLVMFuzzerInitialize` 里 SIGILL → **被误记成「复现 10 条 loose」**。目录名确实不准（它是归档下来的 `/out`），但改名要连带处理复现记录表 156 行历史绝对路径 → 列 §5 待办 | ✅ W5 |
| **按 crash 类型的浏览视图（第十一轮改版）** | `artifacts/by_crash_type/<类型>/<项目>/<san>/<commit>[@arch]/**<OSV-ID>/**{binary,testcase,report.log,INFO.txt}` —— 按用户要求把 OSV 放到 commit **下面一层**，于是「**一条 crash = 一个自包含文件夹**」（三件套 + 判分依据 + 可复制重跑命令聚在一处）。**不物理重排归档**：6/84 个归档跨多种 crash_type，且复现记录表 `binary_dir` 是 append-only 历史路径。✅ 实测 106 条目 / 11 类，且**从 crash 自己的文件夹用相对符号链接重放成功**（libtsm `global-buffer-overflow READ 1 @ vte_write_debug`，与 INFO.txt 一致）。`show_repro.py --build-index / --tree` | ✅ W5 |
| **`purge-on-verify` 默认反转（策略变更）** | **默认由开改关**。用户质疑「重放不是需要二进制吗」成立：我此前用「✅ 可 bit 级重建（20/20、5/5）」代偿删除，但那是**用「信息没丢」偷换「能力没丢」**——对「反复重放」这个下游用法，重建代价是**每次都要付**的。✅ 复算重建成本：**64 个归档 / 72 条 crash / ≈1.7 小时 / ≈2.8GB / 缺镜像 0 个** → 完全付得起。而当初「非删不可」的依据（3,093 × 48MB ≈ **145GB** > 100G 磁盘）**只在跑满队列时成立**，而新项目 6 试 0 中、根本跑不满（实际规模 1.3GB / 磁盘 11G）。加上这条路径已出过 **N30** 与 **N41** 两次事故 → **默认关掉最危险的路径本身就是护栏** | ✅ W5 |
| **归档体积实测（重建成本的依据）** | 272 次成功构建的 `archived_bytes`：中位 **55MB**、均值 **48MB**、最大 143MB。单次构建耗时中位：c-blosc2 **80s** · hunspell **64s** · pcre2 **280s** · md4c **9s** | ✅ W5 |
| **libavc 打通：新项目 7 试 1 中** | 探针 **3/3 复现 / 5.6min** → 整池 43 条 → **33 条复现（16 strict + 8 medium + 9 loose）**；10 条 none = 3 预检⛔ + 6 建成没崩 + 1 compile_error。**复现总数 106 → 139**、strict **47 → 63**、libavc 跃居第二大项目 | ✅ W5 |
| **全量重建 + bit 可确定性的全量证据** | `rebuild_archives.py` 重建 **64 个归档**（c-blosc2 33 · hunspell 22 · pcre2 7 · md4c 2；x86_64 46 + i386 18），约 1h40m → **✅ 498 个文件 sha256 逐个一致、0 不符、0 仍缺**。**比此前证据强一个量级**（W4 只验 4 归档 20 文件、N30 只验 2 条 5 文件），且跨「原构建→删除→数小时后重建」的时间间隔。归档 1.2G→3.5G | ✅ W5 |
| **googlesource 系离线筛选（92 条）** | **libavc 40/43 (93%)** · libwebp 8/10 (80%) · libhevc 13/25 (52%) · **libaom 0/14 → ⛔ 淘汰（没花镜像钱）**。四项前置全过：N33（11 个 apt 包 0 不可安装）· N38（libavc 是全量 https github 克隆）· N34③（`no_sources` 不适用）· **N42 解析 92/92 成功**；另 ✅ libavc 的 seed corpus 外链 **HTTP 200 活着**（N28 无风险，libspng 就死在这） | ✅ W5 |
| **`T_strict` 第一次有区分力** | ④ 报告「复现 ∧ crash_type 一致 ∧ `score_subseq<1.0`」的样本 **0 → 3 条**（`OSV-2020-278`/`-370`/`-546`）。此前只能记「阈值 1.0 **未被证伪 ≠ 被验证**」，现在有真实刻度样本 → §2.2 那条局限可改写 | ✅ W5 |
| **项目集中度改善** | c-blosc2 占 verified 的比例 **58% → 44%** → 「复现率不能当全局估计」这个外推警示**严重性下降一档**（但仍成立）。verified 按 sanitizer 仍是 address 129 / memory 10 / **undefined 0** | ✅ W5 |
| **⚠ 抽样必须按 commit 去重** | 先抽 3 条快筛时 libavc 显示 **3/3 ⛔**，全量跑却是 **40/43 ✅** —— 那 3 条恰好是**同一个 commit** `ab5b036e757c`（manifest 前几条同源）。**3 条样本能给出与全量完全相反的结论** | ✅ W5 |
| **⚠ 已知答案本身必须先核实** | 测 `path_exists_at` 时我拿 `README.md`、`common/ih264_buf.c` 当「应该存在」，结果 6 个全 False，**差点误判成 N27① 同型的假阴性缺陷**；实际是该仓库根目录**根本没有 README.md**，且这是 **HEVC** 库不是 H264 → 用 `+/<sha>/?format=JSON` 取真实树再当基准 | ✅ W5 |
| **libhevc + libwebp 打通：项目数 7 → 9** | libhevc **10/28**（4 strict + 6 medium，10 次构建 / 6.8min）· libwebp **3/10**（2 strict + 1 medium，8 次构建 / 29.5min）。**预检预测被实测双向印证**：libhevc 预测放行 52% → 实拦 16；libwebp 预测拦 2 → 实拦 **2**。**复现 139 → 152、strict 63 → 69、memory 10 → 17** | ✅ W5 |
| **⭐ MSAN flaky 重试首次拿到生产证据** | `retry_count>0` 从**恒 0** 变为 **9 条**（全是 memory：libavc 2 · libhevc 3 · libwebp 4）。**且真的救回了复现**：`OSV-2023-1322` 与 `OSV-2020-1234` 的 `attempts=[0,1]`（第 1 次不崩、第 2 次崩）→ 单次尝试会记成 `none`。同时 `[0,0,0]` 的仍**如实记 none** → 重试没变成「重试到崩为止」的造假工具。→ §5「MSAN 重试从未触发、需人工构造」那条待办**可销** | ✅ W5 |
| **新项目的成败规律（可作硬前置）** | **9 试 3 中**。三个成功项目（libavc/libhevc/libwebp）的 Dockerfile 都是「**全量 https 克隆、无 `git://`、无 `--depth 1`**」；失败的要么外链死（N28）、要么 era 包下架（N33）、要么 `git://`+浅克隆（N38）→ 这条**已可离线判**，应进筛选表作硬前置 | ✅ W5 |
| **复现率 69.8% → 64.1% 不是退步** | 新进的 38 条里 **18 条被预检判为「该 commit 树上缺 build.sh 引用的文件」**（libhevc 16 + libwebp 2）→ **从未被构建**，属基础设施不可达而非复现方法失效。c-blosc2 占比同步降到 **40%**（W5 初 58%） | ✅ W5 |
| **用户一个结构问题拽出 4 个真缺陷（N45–N49）** | 「一个 OSV 为什么有这么多二进制」→ 查出 ⑤ 连接键优先级反了（2 条复现记录表指向**没崩的那格**、重放 exit=127）、libFuzzer **超时被当复现**（虚高 1 条）、`exit_code` 不可作判据（3 条 libwebp exit=0 却是真崩溃）、审计只查「是不是目录」故报 0 红线。**全部修在根因上**，并用**实测重放 exit=1 + ASan ABRT** 收尾 | ✅ W5 |
| **交付视图布局改对** | `binary` 从「整棵构建树（1～17 个可执行文件）」收窄成**单个 driver 文件**；整棵树保留为 `out/`（运行期 `.so`/`.dict` 依赖，只给 driver 会重放失败）；INFO.txt 顶部写明。**151 条目 · binary 单文件链接 151 · out 151 · 断链 0** | ✅ W5 |
| **复现 152 → 151（少的 1 条是超时假复现）** | 383 行 / 237 唯一 / 34 run；tier **strict 69** · medium 51 · **loose 31** · none 86；**driver 在盘 151/151**（此前只验过「目录在盘」）；审计 **0 红线**（含新增 3 条）；自测 **18 套 293 项 / 0 失败** | ✅ W5 |
| R13a `fixed` 选择规则（**W2 修正**） | ≥2 个 **fixed** 事件的记录 **540**（~~旧称「multi-event」~~；真 multi-event = ≥2 对 **639** / >2 事件 **630**，且**所有记录只有 1 个 range**）；歧义 **0** ✅；「无 intro 匹配→取最后 fixed」= **24**（540 内）/ **69**（全量），~~旧记 15~~（差值 9 = `introducing_commit=="0"` 哨兵被假匹配） | ✅ W2 复算 |

---

# 1. 设计规格（当前状态）

> 本节是**实现的唯一依据**：只写当前有效的规格，不写「原来怎样、第几轮改成怎样」（那在 `archive/`）。凡标 ✅ 的量化前提均为实测。

## 1.1 范围

**在范围**：C/C++ 主线 **3,502** 条（c++ 3,059 + c 443，271 项目）。首轮建议 ASAN + Heap-buffer-overflow + 有 testcase + 有 target 的 ~5–10 个稳定项目（**具体清单跑的时候定**），之后增量扩面。

**不在范围**：修 bug；一次性全量 3,790；driver_create 自身生成 driver 的复现（另一条线）；非 C/C++ 246 条（jvm 191 需 Jazzer 路径、rust 38/swift 8/python 7/ruby 2）+ unknown(name-miss) 42 条（M2 未命中，**不擅自映射**——R5 的教训：substr 回落把 unrar26 误映 junrar 污染了整个 language 口径）。

## 1.2 架构与数据流

```
crash_testcase/**/*.json ─┐
crash_dataset.jsonl ──────┼─→ ① manifest_builder ─→ artifacts/repro_manifest.jsonl + build_groups.json
crash_state_recovered ────┘      (+ _osv_cache: fixed/introduced/repo)
data/_osv_cache/*.json ───┘
                          │  [§1.7 H 四条件 worktree gate]
                          ▼
                   ② build_orchestrator     缓存键 (project, sanitizer, commit)
                      Stage1 HEAD  commit=<构建时解析的上游 source SHA>，共享：一次服务同项目同 san 全部 crash
                                 **[W3 路由] 只给 `commit_source=head` 组**；has_fixed 一律跳过 Stage1
                      Stage2 钉版  commit=<pin_commit>，per-commit 独占
                                 **[W3] ⑥ 逐格驱动 walk-back；停止判据 = tier 感知（N12）；
                                  任一格构建失败 → 继续下一格（N17，含 located 的回退格）
                          │  临时 $REPRO_OSS_FUZZ_DIR/build/out/<p>/（无 commit 分量、会被覆盖）
                          │  → 构建成功即归档 artifacts/binaries/<p>/<san>/<commit-SHA>/（binary_dir 指向此）
                          ▼
                   ③ repro_runner    base-runner 跑 二进制×testcase（-timeout=25 -rss_limit_mb=2560）
                          ▼          捕获 crash_type/符号化帧/信号；UBSAN 走 stderr 解析；ASAN 1×/MSAN·uninit ≤3× 重试
                   ④ verify_tiered   strict / medium / loose / none + frame_match_score（三量）
                          ▼
                   ⑤ annotate_dataset ─→ repro_dataset.jsonl（交付物，append-only + run_id/run_ts）
                   ⑥ run_repro        顶层编排（增量循环入口）    ⑦ recover_targets（可选增强）
```

**单轮内部顺序（[W3 改] 按 `commit_source` 分流，不再是无差别 HEAD-first）**：
* `commit_source = head`（OSV 既无 `fixed` 也无 `introduced`；全量 **65** 条 / 可执行 **42**）→ 走 Stage1(HEAD)，本来无别路可走；
* `commit_source ∈ {fixed_parent, fixed_ancestor, introducing}`（has_fixed）→ **跳过 Stage1、直接进钉版队列**，按 `pin_commit`→`introducing_commit` 回退链逐条 per-commit 构建；
* `--force-stage1` 可退回 W2 的无差别 HEAD-first（**仅供对照，非默认**）。

**[W3] 为什么改（✅ 实测复算；R16 的「单位成本差约 8×」是纯推测、从未测过）**

| 量 | 实测值 | 出处 |
|---|---|---|
| has_fixed 组在 HEAD 的复现率 | **1/119 = 0.8%**（Wilson 95% 上界 **4.6%**）。那 1 条是 libtsm OSV-2021-1373，而 libtsm 上游 HEAD 冻结在 **2014-04-24**、比报告年 2021 早 7 年 → HEAD 就是漏洞版，**不构成 has_fixed 组 HEAD 有用的证据**；排除它则 **0/118**、上界 **3.2%** | W2 Phase 3 |
| `T_head` / `T_pin` | 中位 **72s** / **79s**；同项目比值中位 **0.87**（n=4）→ **不是 8×，约 1×** | §4.9(e) |
| 共享比 k（每个 HEAD 构建服务几条 crash） | W2 样本 **20.8**（偏向大项目）；总体 **7.76**（可执行 3,136 / head_groups 404） | ✅ W3 复算 |
| break-even yield = `(T_head/k + t_run)/T_pin` | k=20.8 → **6.2%**；k=7.76 → **13.5%**；k=3.9 → 25.1% | ✅ W3 复算 |
| **结论** | 上界 **4.6% < 6.2% ≤ 13.5%** → **三种 k 口径下加 HEAD 层都是净亏** | ✅ W3 |

⚠ 口径：任务给的「33 次 HEAD 构建 → k=3.9」用的是 `build_records` 的**记录数**（含跨轮缓存命中 19 条）；唯一 `(project,san,commit)` HEAD 构建只有 **6** 个 → k=20.8。两种口径都算了，结论一致。
`fixed` 的用途不变：提供 `fixed^`；作**排序**先验（no_fixed 优先），**不用于排除**。

**钉版机制**：官方 `infra/build_specified_commit.py --project_name <p> --commit <SHA> --sanitizer <san> [--repo_url <url> --repo_path <path>]`。流程 `detect_main_repo`（给了 `--repo_url/--repo_path` 则**跳过**，见 1.3①）→ `copy_src_from_docker`（拷 /src 到 temp，**不注入主树**）→ `repo_manager.checkout_commit`（自动 `fetch_unshallow`、detached）→ `helper.build_fuzzers_impl`。构建失败时**自愈工具链漂移**：按上游 commit 日期 checkout 同期 oss-fuzz `projects/<p>` commit（`:243-268`）+ 替换 era base-builder digest（`:272`；**gcloud 实测不可用 → 此步跳过**，只剩 projects/ 侧自愈）。

## 1.3 组件规格（7 模块 + 1 共享底座）

**⓪ `repro_common.py`（共享底座，无 CLI）— ✅ W1 已实现**
- 4 数据源加载、路径常量、`normalize_frames()`（**AST 逐字提取** `preflight/history/r2_r5_r6_r7_recompute.py` 那份，不重写；以 R2-extra 10 项计数对账）、派生 helper（`osv_year`/`crash_type` 归一化/`language` R5 exact-match/`crash_cluster_id`/sanitizer+target 解析/testcase sha256+`input_magic`）、OSV 解析（R13a 规则、**N6** 检测）、`get_parent_local()`（经 `repo_manager.get_parent`）、`resolve_repo_path()`、静态 check（复合证据分）、schema 定义。
- 依赖：`oss-fuzz/projects/`（只读）、worktree `infra/repo_manager.py`。**不依赖 driver_create。**

**① `manifest_builder.py` — ✅ W1 已实现（W2–W5 增字段与护栏）**
> **[W5] 覆盖护栏（N26）**：`overwrite_guard()` 挂在唯一写盘点 `write_outputs()` —— **覆盖面缩水**或**交集行上任一强度字段由有值变空** → 拒写、退出码 **4**、点明字段；`--force-overwrite` 才写且记 `manifest_overwrite_audit.jsonl`。只在**交集**上比强度 → 子集运行不误报。
> **[W4] 路由职责摘除**：① 仍照算 `fixed_real`/`static_check_verdict`/`walkback_depth`/`fixed_misattributed` 并写进 manifest（对下游理解 crash 有价值），但**这些不再被 ② 用于选 pin** → 降为 **advisory**（§4.27）。
- 输出 `artifacts/repro_manifest.jsonl`（每 crash 一条，44 字段）+ `artifacts/build_groups.json`（`head_groups`：`(project,sanitizer)→[osv_id]`；`pinned_queue`：钉版**不入分组**，per-commit 独占）。
- CLI：`--projects --limit --crash-types --sanitizers --languages --sort --only-osv --out --build-groups --repo-map --static-check --static-check-limit --max-depth --keep-chain`。
- 派生：见 §1.5 schema。**静态 check**（W1）：`--static-check` 打开时用复合证据分定位真修复 → `fixed_real`/`pin_commit`/`walkback_depth`；默认关（离线可跑，全部记 `skipped`、`walkback_depth=null`，交 ② 构建期 walk-back）。
- `fixed` 仅用于**排序**（`--sort no_fixed_first` 默认），不排除任何 crash。

**② `build_orchestrator.py` — ✅ W2 已实现并实测；**W5 增：`rotate_existing_log()` 挂在 `run_cmd` 唯一写盘点（N25，永不覆盖上一次的日志）、预检三处修正（`sha=None`/`./` 前缀/`SCRIPT_RE` 容忍 flag，N27）、`_norm_cand()`**；**W4 增：`plan_pinned()` 一律走策略 A（删 located 分支与 `--no-pin-fallback`，52→44 行）、`precheck_buildscript()` 构建前静态预检（N19 两形态）、分类器加 `buildscript_mismatch` 并读整份日志、裁剪默认 dry-run + 双字段交叉校验 + `prune_audit.jsonl`**；W3 增：`--architecture`（进缓存键与归档路径）、`--min-free-gb`、`--prune-archive`、`network_fetch` 自动重试 1 次、`located` 路的 N17 回退格、gate 第⑤条自动重建自愈、N4 还原改 `git restore --staged` + `clean`**
- **前置 §1.7 H 四条件 worktree gate**（不过则 ABORT + 写 `BLOCKED.md`，不带污染构建）。
- **缓存键 `(project, sanitizer, commit)`**：先查 `state.json`/`build_records.jsonl`，命中复用、不命中才构建。
  - HEAD 路径 `commit` = **构建后在 builder 容器内 `git -C /src/<p> rev-parse HEAD` 解析的上游 SHA**（✅ P0：md4c = `61f5ce76…`）。**绝不用字面 `"HEAD"`**——`helper.py build_fuzzers` 在**构建时**才 clone 上游（✅ libxml2 `Dockerfile:32`、ndpi:19、radare2:20、file:21），第 1 轮 HEAD ≠ 第 20 轮 HEAD，字面量会让后续轮复用几个月前的二进制并标 `repro_version=head`（增量模式下必然发生）。
  - 🅗 SHA 拿不到（tarball 项目无 `.git`）→ **HEAD 缓存条目不跨轮复用**：强制每轮重建（或按 `oss_fuzz_commit`+日期加 TTL），`pinned_commit="UNKNOWN"` + `notes="head_commit_unresolved"`。绝不静默复用 stale-HEAD。
  - 钉版路径 `commit` = `pin_commit`（① 给）或 `get_parent_local(fixed, walkback_depth)`。**严禁用旧 `(project,sanitizer)` 键复用**：同项目两条 crash 的 `fixed^` 通常不同 → 第二条会复用第一条二进制 = **假复现**（两条就中招）。
- **构建成功即归档**（② 的专属职责，⑤ 不做——⑤ 时机太晚、临时 `build/out` 已被覆盖）：把 fuzz_target 二进制 + `.options`/`.dict`（**不含 seed_corpus.zip**）从临时 `build/out/<p>/` 拷到 `artifacts/binaries/<p>/<san>/<commit-SHA>/`，`binary_dir` 指向归档位、记 `binary_sha256`。归档失败 → `build_status=archive_failed`。若未实现即时归档，则**钉版构建与复现必须交错**（build A→run A→build B→run B），不得批量构建后批量复现。
  - **`llvm-symbolizer` 去重**（✅ P0-B：4 个新构建的 symbolizer sha256 完全相同）：它是 base-builder 提供的工具、非 per-commit 产物，仅 2 个内容变体（`13babd3b…`/6959432B、`db0240ff…`/7034272B）→ 按 sha256 内容寻址存一份到 `binaries/_shared/llvm-symbolizer-<sha8>` + 各 commit 目录**硬链接**。**单构建归档边际增量 ≈ 仅 fuzz_target 本身**（pcre2_fuzzer_16 ~10M / md4c fuzz-mdhtml 5.9M），symbolizer 首次后 0 增量。
- **假成功防护**：校验 `$REPRO_OSS_FUZZ_DIR/build/out/<p>/<fuzz_target>` 二进制**实际存在**，不轻信 build.sh 退出码（✅ 审计B：主树 `ndpi/build.sh:3 set +e` + `:87 exit 0` → 构建恒假成功）。
- **N4 era 缓存**：era-retry 解析出的 era oss-fuzz commit 由目标 commit 日期**确定性**决定（`:243-248 git log --before=<date> -n1 projects/<p>`）→ 按 `(project, 目标 commit 日期区间)` 缓存进 `state.json`，下次同项目钉版**直接 checkout 缓存的 era commit、跳过注定失败的首试**（✅ P0-B：pcre2 `fixed^` 含 era-retry 9m44s vs `fixed^^` 复用 era 残留 4m52s → 省约一半）。**worktree 还原照做**（每次钉版后 `git checkout HEAD -- projects/<p>`；✅ W1 实测该命令受 pathspec 限制只动 `projects/`、`infra/` 三补丁 md5 逐一不变，不需加例外）。
- **walk-back（仅对 ① 判 `not_located`/`undecidable` 者）**：依次钉 depth 1→2→3 构建+复现，首个 `reproduced_any=true` 停；记 `walkback_depth` + `repro_version`（depth1=`fixed_parent`、depth≥2=`fixed_ancestor`）；超 3 格 → `walkback_exhausted` + `tier=none` + notes（下游可区分「退够 3 格仍没复现」vs「这版本确实没 bug」）。① 判 `located` 者**直接钉 `pin_commit`、1 次构建**（✅ W1 实测省 12.3% 构建、成功率不变）。
- 输出 `build_records.jsonl`：`{key, commit, commit_source, stage, build_status, binary_dir, build_log, oss_fuzz_commit, base_builder_digest, pinned_commit}`。CLI：`--build-groups --stage {1,2,auto} --sanitizers --max-builds <n>`。
- 依赖：worktree `infra/helper.py build_fuzzers`、`infra/build_specified_commit.py`、`repro_common`、Docker。

**③ `repro_runner.py` — ✅ W2 已实现并实测**
- 每 testcase × 已构建二进制（**从归档位取，不从临时 build/out**），base-runner 跑，捕获 crash_type/符号化帧/退出信号；按 sanitizer 重试。
- **运行参数用 ✅ M11 实测的 OSS-Fuzz 默认值**（不自拍）：`-timeout=25 -rss_limit_mb=2560`（`base-runner/Dockerfile:80` FUZZER_ARGS）；`malloc_limit_mb` 不设（ⓘ libFuzzer 默认）；ASAN/MSAN/UBSAN_OPTIONS 用 `Dockerfile:77-79` 默认（含 `symbolize=1:dedup_token_length=3:strip_path_prefix=/workspace/`），记入 `runtime_limits`。
- **1:1 复刻 base-runner reproduce 命令行**（✅ R11）：env 设 `RUN_FUZZER_MODE=interactive`/`FUZZING_ENGINE=libfuzzer`/`SKIP_SEED_CORPUS=1`/`SANITIZER=<san>`/`TESTCASE=<path>`（`reproduce:21-32`）；执行 `bash -c "$OUT/<fuzz_target> -- $FUZZER_ARGS $TESTCASE < /dev/null"`（`run_fuzzer:198,214,227`；字面 `--` 须保留）；`SKIP_SEED_CORPUS=1` 故不 append corpus（`:200-202`）；有 `.options` 则 append CUSTOM_LIBFUZZER_OPTIONS（`:204-206`）、有 `.dict` 则 append `-dict=`（`:208-212`）；退出码=二进制退出码。**无 `-runs=1`**（libFuzzer 给单文件即跑一次）。
- **UBSAN 不 abort**（✅ M11：UBSAN_OPTIONS 无 `halt_on_error`，`Dockerfile:79`）→ exit 可能为 0，判定须**解析 stderr 的 `runtime error:` / `SUMMARY: UndefinedBehaviorSanitizer`**，记 `notes="ubsan_stderr_detected"`。ASAN/MSAN 仍可用 exit_code/signal（ASAN handle_abort/segv/sigill=1、MSAN exit_code=86）。
- 引擎异构不阻塞：非 libFuzzer 868 条（afl 581/honggfuzz 275/centipede 12），`reproduce:31` 强制 libfuzzer → 都走 libFuzzer 路径（🅗 testcase 是纯输入应等价，首轮抽查证实）。
- 🅗 直接 `docker run base-runner`（对帧捕获/重试/Tiered 更可控），`helper.py reproduce` 留作交叉校验。
- 输出 `observations.jsonl`：`{osv_id, observed_crash_type, observed_frames, exit_code, signal, retry_count, raw_log_path, reproduced_any, runtime_limits}`。CLI：`--manifest --build-records --out --retries-asan 1 --retries-msan 3 --timeout 25 --rss-limit-mb 2560`。

**④ `verify_tiered.py` — ✅ W2 已实现并实测**
- **Tiered 判定**：`strict` = **recovered top-3 按序出现在 observed 完整归一化栈中**（有序子序列，`score_subseq ≥ T_strict`）｜`medium` = 归一化 crash_type 一致｜`loose` = 任何 sanitizer 报告/崩溃信号｜`none` = 无 crash。
- **`frame_match_score` 三量**（设 R=recovered top-3 归一化后、O=observed 完整归一化栈）：① `score_pos = Σ[R[i]==O[i]]/|R|`（最严，跨版本脆弱）；② **`score_subseq`** = R 是否为 O 的有序子序列 → 1.0/0.0（**strict 用此**）；③ `score_set = |R∩O|/|R|`（最松）。`verifications.jsonl` 的 `frame_match_score` 记 `score_subseq`，`details` 内附**三量原值**（供日后重标定）。
- **帧归一化 6 步**（✅ P0 实测后定死）：
  1. **top-k 两侧不同处理**：**observed 侧不截断**（保留归一化后的完整项目帧栈供子序列定位）；**recovered 侧取 top-3**（= ClusterFuzz `dedup_token_length=3`；94.4% 恰 3 帧）。CLI `--recovered-topk 3`。*理由（✅ P0）：observed 截到 top-3 后若存在帧移位（md4c 顶部多一帧 `md_resolve_links`），`recovered[2]` 落在窗口外 → `score_subseq` 从 3/3 掉成 0/3、同一 bug 掉出 strict。*
  2. **文件帧剔除**：recovered 第 3 帧常是源文件名（`is_file_frame` 标记，审计A）→ 只比函数帧。
  3. **内部帧剔除**：`__asan_`/`__msan_`/`__interceptor_`/`LLVMFuzzerTestOneInput`/`fuzzer::` 等。
  4. **后缀归一**：strip `.part.NN`/`.constprop.NN`/`.isra.NN`、前导 `auto`、`$_N` lambda、`::operator()$`→`::operator`。
  5. **路径前缀**：observed 已被 `strip_path_prefix=/workspace/`（M11）。
  6. **<3 帧降级**：recovered 0 帧（20 条）→ strict 不可用，降 medium/loose；1–2 帧（192 条）按实际帧数比。
- **`T_strict = 1.0`**（子序列全中才 strict）。两个标定点：md4c/OSV-2022-126 @ `introducing 62b60979` = `score_pos 0.0 / subseq 1.0 / set 0.67`；pcre2/OSV-2024-1261 @ `fixed^^ 62b3ceca` = `1.0/1.0/1.0`（**项目首个 strict**）。⚠ **`T_strict=1.0` 目前无区分力**：两点 `score_subseq` 都是 1.0，取 0.5 还是 1.0 结果相同 → 它是**未被证伪、不是被验证**。要判断是否过严，需要一个「确实复现但帧对不齐（subseq<1.0）」的样本。**保持 1.0，每条存三量备回溯重标定。**
- **off-by-one 有两型，步骤 1 与步骤 3 各治一型、缺一不可**：①**拦截器帧假象**（pcre2 raw DEDUP_TOKEN 顶帧 `__asan_memmove`，剔内部帧后即对齐，`score_pos` 0→1.0）；②**真实项目帧移位**（md4c 顶部多一个**项目函数**，剔内部帧后仍 `score_pos=0`，须靠子序列规则保 strict）。
- **clusterfuzz StackParser 降 P1**：先用上述轻量归一化跑通，有真实 observed 帧后复评。🅗 ground-truth 帧是 2016–2026 **不同版本** ClusterFuzz 生产生成，用单一版本（2.5.9）StackParser 对齐本身有漂移风险，非无代价权威解；ⓘ 该包本地未安装。
- 输出 `verifications.jsonl`：`{osv_id, verification_tier, frame_match_score, crash_type_match, frames_aligned, details}`。CLI：`--observations --recovered --out --recovered-topk 3`。

**⑤ `annotate_dataset.py` — ✅ W2 已实现并实测；**W4 增：单调性校验（verified 不得被降级成无结论行，`--force` 才写且标 `tier_downgraded`）、`--only-observed` 默认开、`dataset_guard.jsonl` 审计**；W3 增 `commit_source_prior`/`walkback_best_*`/`run_status`**
- 合并四流 → `repro_dataset.jsonl`。**不归档二进制**（归档只在 ②）。
- **追加语义**：每条盖 `run_id`（本轮唯一）+ `run_ts` 后 **append-only**（不就地改、不删旧）；同 osv_id 跨轮/`--force` 重跑会有多条，**下游按 `osv_id` 分组取 `run_ts` 最新一条**（保留历史可审计，避免下游按 tier 重复计数）。
- CLI：`--manifest --build-records --observations --verifications --out --run-id <id>`。

**⑥ `run_repro.py` — ✅ W2 已实现并实测；**W4 增：`--match-job-arch`（默认开，按 crash 的 `job_arch` 构建 = N22）、`--stop-project-after`（默认 2，同项目连续同类确定性失败即早停）、预检拦截即放弃整条**；W3 增：按 `commit_source` 分流（`--force-stage1` 可退回）、walk-back 停止判据 **tier 感知**（调 ④ 的 `verify_one`，不另写判据）、逐格轨迹 `walkback_trace.jsonl`、`walkback_best_depth/_tier`、② rc=2（gate ABORT）→ 整轮停、轮末默认裁剪、`--min-free-gb`**
- 跑一轮增量端到端（①→⑤）并追加。幂等/可续跑：`state.json` 记已完成构建（`(project,sanitizer,commit)` 键 + `binary_dir` 归档位 + era commit 缓存）与已复现 osv_id，重跑跳过；`--force` = 追加新 `run_id` 记录。
- CLI：`--projects <list> --limit <n> [--max-builds <n>] [--stage1-only] [--crash-types] [--sanitizers] [--force]`。**`--limit` 界 crash 数、`--max-builds` 界单轮构建数**（HEAD+钉版合计，超限停 + 断点入 `state.json`；钉版 per-commit，`--limit 30` 且 HEAD 全没复现 = 30 次钉版 ≈ 15h，只看失败率的急停闸拦不住）；**`--stage1-only` 本轮只跑 HEAD**（首轮建议）。

**⑦ `recover_targets.py`（可选增强）— 待写**
- 379 条不可复现空 target，联网从 `report_url`/`testcase_url` 回捞 target 名（156 条已零成本推定）。🅗 成功率未知，纯增强。

## 1.4 目录布局

```
mutator_create/reproduce_crash/
├── repro_common.py ✅ / manifest_builder.py ✅ / build_orchestrator.py / repro_runner.py
├── verify_tiered.py / annotate_dataset.py / run_repro.py / recover_targets.py
├── DELIVERY.md（本文）  preflight/（测量脚本 + 逐条原值 JSON + **fixtures/** = ③ 解析器的 4 段真实 stderr 护栏）
├── build_orchestrator.py ✅ / repro_runner.py ✅ / verify_tiered.py ✅ / annotate_dataset.py ✅ / run_repro.py ✅
├── archive/（历史底本，含各轮报告全文快照）
├── repro_dataset.jsonl            # 交付物：增量追加，跨轮持续生长
└── artifacts/
    ├── repro_manifest.jsonl ✅ / build_groups.json ✅ / repo_path_map.json ✅ / static_check_cache.jsonl
    ├── build_records.jsonl / observations.jsonl / verifications.jsonl
    ├── state.json                 # 续跑：构建键 + binary_dir + era commit 缓存 + 已复现 osv_id
    ├── binaries/<p>/<san>/<commit-SHA>/               # 所有成功构建即归档（含 commit 分量防跨轮覆盖）
    │     ├── <每个 fuzz_target>                        # [W2/N11] **全部** target，不只本次请求的那个
    │     ├── <target>.options / .dict / **monster_test.bfbs 等运行期数据文件**   # 单文件 ≤32 MB
    │     └── llvm-symbolizer → 硬链接到 _shared/
    ├── binaries/_shared/llvm-symbolizer-<sha8>         # 内容寻址去重（✅ W2 实测两个变体 db0240ff/13babd3b）
    ├── runs/<run_id>/{manifest,build_groups,observations[_stage2],observations_all,verifications}.jsonl
    │                                                    # [W2] 每轮中间产物隔离 + run_meta.json；
    │                                                    # 全局共享的是 state/binaries/build_records/dataset
    └── logs/build/<p>_<san>_<commit>.log, logs/reproduce/<osv_id>[_rN].log, logs/negctl/*.log
                                                         # ✅ W2 留存：构建 21 + 复现 124 + 负对照 10 份
```
> **临时工作区 vs 归档位**：`$REPRO_OSS_FUZZ_DIR/build/out/<p>/` 无 commit 分量、会被同项目下次构建覆盖；`artifacts/binaries/<p>/<san>/<commit-SHA>/` 是归档位，`binary_dir` 指向它。③ 从**归档位**跑二进制 → 批量构建/跨轮续跑都安全。

## 1.5 `repro_dataset.jsonl` schema（▸ = 派生/新增字段）

| 字段 | 类型 | 来源 | 含义 |
|---|---|---|---|
| osv_id | str | crash_testcase.bug_id | 唯一 id |
| ▸ run_id / run_ts | str/int | ⑤ | 本轮 id + 时间戳；跨轮追加，下游按 osv_id 取 `run_ts` 最新 |
| ▸ osv_year | int | ①(osv_id) | crash 年份（**背景/分层用，非分流键**） |
| project / project_ossfuzz_dir | str | crash_dataset / 映射 | 项目名 / oss-fuzz 实际目录（未命中=null） |
| ▸ language | str | ①(project.yaml) | c/c++/jvm/rust/…（R5 **exact-match**，不做 substr 回落） |
| fuzz_target | str | crash_testcase | 二进制名（空→推定或 skip_reason） |
| ▸ target_inferred | bool | ①(M9/R7) | 空 target 由「project 唯一 target 且 oss-fuzz 命中且 C/C++」推定（**净 156 条 true**） |
| sanitizer / fuzzing_engine / job_type | str | crash_testcase | address/memory/undefined、引擎、job |
| ▸ sanitizer_inferred | bool | ①(R16) | 空 sanitizer 的 C/C++ crash 默认按 ASAN 试跑（**25 条 true**） |
| crash_type_expected / _full_expected | str | crash_dataset | 期望 crash 类型（归一/全） |
| ▸ crash_type_norm | str | ① | 归一化值（`Heap-buffer-overflow READ 1`→`heap-buffer-overflow`），供 ④ medium 比对；🅗 observed 侧形态仅 P0 测过一例 |
| ▸ crash_cluster_id | str | ①(M7+R2) | `(project, crash_type, 归一化 recovered top-3)` 哈希（**基于归一化帧**），下游归并 |
| introducing_commit | str | crash_testcase | 引入 bug 的上游 commit（99.5%） |
| ▸ fixed_commit / fixed_parent | str | ①(_osv_cache) | 修复 commit（93.7%，R13a 规则选）/ 其父=`fixed^`（② 用 `get_parent_local` 解析） |
| ▸ **fixed_real** | str? | ①(W1) | 静态 check 定位到的**真修复** commit（pcre2=037fb170、hunspell=d6836713）；未定位=null |
| ▸ **pin_commit** | str? | ①(W1) | **Stage2 实际要钉的 commit**（=`fixed_real` 之父；pcre2=62b3ceca）。② 直接用、不再自己算 |
| ▸ **static_check_verdict** | enum | ①(W1) | `located`(64.6%) / `not_located`(22.9%) / `undecidable`(12.5%，非 github/gitlab 托管) / `degenerate`(N6) / `skipped`(离线) / `no_fixed` |
| ▸ **walkback_depth** | int? | ①②(W1) | **静态预测/计划**要钉的格数（1=`fixed^`；2/3=`fixed^^`/`fixed^^^`；>3→`walkback_exhausted`+`tier=none`）。① `located` 时直接给值并 **clamp ≤ intro_depth**；否则 null 由 ② walk-back 填 |
| ▸ **walkback_depth_actual** | int? | ②③(**W2**) | **实际**在第几格复现（与上一行**分开存**，Phase 5(a) 要用真实分布检验 W1 的 B/C 之争）。`null` = 不是 walk-back 格（HEAD 复现、或钉 `introducing_commit`）；须与 `reproduced_any` 合读。✅ 实测：`1`×4、`2`×1、`null`×7 |
| ▸ **walkback_exhausted** | bool | ⑥(**W2**) | 三格全试完仍未复现（**区别于**「三格全构建失败」= `build_status=fail_both`） |
| ▸ **walkback_best_depth / _best_tier** | int?/enum | ⑥(**W3**) | **N12**：tier 感知 walk-back 走完后，**最佳 tier 那一格**的深度与 tier（`loose` 不停、继续下探，最后取最好的一格作结论）。✅ W3 实测 14 次下探中 **0 次**改善 tier → 🅗 建议加「`frac≥0.6` 即停」（§4.19） |
| ▸ **walkback_stop_reason** | enum? | ⑥(**W5**) | 本条 walk-back 是**怎么停的**：`tier`（达 medium+，W3 判据）/ `frac`（**N12** 新判据：帧已对齐 → 同一 bug 的不同表现，下探无收益）/ `null`（走完或构建失败）。**为什么必须进 dataset 而不只进 trace**：dataset 是交付物、trace 是中间产物；只有 trace 记 → 复现记录表上看不出哪些行是提前停的，而 N12 翻转默认值时要审计的正是这个。✅ W5 实测抓到该缺陷（⑤ 白名单漏字段 → TDD 修，自测 11 项） |
| ▸ **frac_stop_would_fire** | bool | ⑥(**W5**) | **shadow 字段，只在 `walkback_trace.jsonl` 的每格里**（不进 dataset）：该格「本来会因 frac 而停」与否，**与 `--stop-frac` 开关无关**、常开。这是 N12 翻转默认值的**唯一数据来源**——一旦真开 `--stop-frac`，更深格就不再被观测，测量通道即关闭，所以关闭状态下也必须留痕 |
| ▸ **binary_pruned** | bool? | ⑥/⑤(**W5**) | 该行 `binary_dir` 指向的归档**已被回收**（逐条回收或轮末裁剪）。**为什么必须有这个字段**：删了目录而记录还指着它 = **无声悬空指针**，消费者照路径去取会扑空且无从判断是「删了」还是「写错了」（N25/N26/N30 同族）。删归档**不丢信息**：`binary_sha256`（逐文件）+ 重建配方（`pinned_commit`/sanitizer/arch/era）都留着，而 W4/W5 已两次实测重建**逐字节一致**（20/20、5/5）。⑤ 还会在 `merge()` 里**按目录是否存在兜底标注**——✅ W5 实测复现记录表里有 **60 条**历史行悬空却无标记（W3 轮末裁剪删的，全是 `none` 档，按 §1.6 不在交付子集） |
| ▸ **walkback_depths_tried / _n_build_fail** | int | ⑥(**W3**) | 本条共试了几格 / 其中几格**构建失败**（**N17** 的量化：失败不丢 crash，逐格记） |
| ▸ **commit_source_prior** | enum | ⑤(**W3**) | **① 的先验**原值。`commit_source` 会被 ② 的实际值覆盖（§1.5「①先验→②实际」），W2 因此**丢了先验**（✅ 实测 109/129 条 dataset 与 manifest 不一致 → 跨轮分析必须回 join manifest）→ 两个都存 |
| ▸ **architecture** | enum | ②(**W3**) | 构建架构（默认 `x86_64`）。**进缓存键与归档路径**（`<commit>__i386`），否则两种架构产物互相覆盖 = 假复现（同 R16/R17 那类）。x86_64 时键与 W2 完全兼容 |
| ▸ **data_files / targets_absent_at_commit** | [str]/[str] | ②(**W2/W3**) | 归档里带的**运行期数据文件**（`.bfbs` 等，**N11**）／请求了但**该 commit 根本不产出**的 target（用于区分「归档缺件该重建」与「重建也拿不到」，避免无限重建） |
| ▸ **fixed_misattributed** | bool? | ①(W1) | OSV `fixed` 不是真修复 → true。**三态**：true/false/null（未定位、不可判定、退化 = null，**不猜 false**） |
| ▸ **osv_degenerate_range** | bool | ①(W1) | **N6**：`introduced == fixed` → vulnerable 窗口为空、钉版必然假 none → `pin_commit=null`、不进 Stage2、仅 HEAD |
| ▸ **degenerate_resolved** | bool | ①(**W2**) | **N6 不再一刀切**：退化 sha 经复合证据分复核**像修复** → 解禁钉版（`pin_commit=sha^`）。判据 `S≥2 ∧ ¬no_source ∧ ¬test_only ∧ ¬harness_like`(**N7**) `∧ frames_in_diff≠∅`。✅ 实测 53 条 → **解禁 2 条**（1 条可执行） |
| ▸ **issue_id** | int | ①(**W2**) | OSS-Fuzz Monorail issue 号（`report_url` 的 `?id=<n>`，✅ **3,790/3,790** 可解析）。两用：静态打分器的 `issue_id_in_msg`(+3) 信号；**`pinned_queue` 的项目内排序键**（= pin commit 日期的离线最优代理，同年组内 Spearman **+0.733**） |
| ▸ **job_arch** | enum | ①(**W2**) | **N8**：从 `job_type` 解析架构 = `x86_64`(3,606) / **`i386`(164)** / `aarch64` / null(20)。i386 在 x86_64 构建下**结构性不可复现** → 分层先验，**不 skip** |
| ▸ **repo_url** | str? | ①(_osv_cache) | OSV `ranges[].repo`（**99.6%**=3,776/3,790），供 `--repo_url` |
| ▸ **repo_path / _confidence / _candidates** | str?/enum/[str] | ①(映射表) | 容器内上游主仓库目录，供 `--repo_path`（`:425` 只取 basename 拼宿主 /src 副本）。`high` 91.1% / `medium` 6.5% / `candidates` 1.4%（运行期 `git cat-file -e` 定夺）/ `none` 1.0%（回退 `detect_main_repo`） |
| ▸ **expected_repro_version** | enum | ①(W1) | ① 对 `repro_version` 的先验（`fixed_parent`/`fixed_ancestor`/`introducing_commit`/`head`）；静态 check 未跑时仍记 `fixed_parent`（depth1 是设计默认），**不退化成 head** |
| testcase_path / _sha256 / _size | str/str/int | 磁盘/计算 | 位置 + 完整性 + 大小 |
| ▸ input_magic | str | ①(M8) | testcase 前 16 字节可打印表示 |
| ▸ testcase_is_minimized | null | M8 | ⓘ 本地无标记 → null（不可知） |
| recovered_frames / ▸ recovered_is_file_frame | [str]/[bool] | crash_state_recovered | ground-truth 符号化帧（top-3）+ 逐帧文件名标记 |
| report_url / testcase_url | str | crash_testcase | OSS-Fuzz 报告/下载（100% / 99.3%） |
| **repro_version** | enum | ②③ | `head` / `fixed_parent` / **`fixed_ancestor`**（depth≥2）/ `introducing_commit` / `none` |
| build_status / build_stage / binary_dir | enum/int/str | ② | `ok`/`fail_head`/**`fail_pinned`**/`fail_both`/`skipped`/`no_target`/`ok_but_no_target`/**`archive_failed`**；stage；**commit-specific 归档位** |
| ▸ **build_error_class** | enum | ②(**W2**) | 失败粗类，**顺序即优先级**：`network_fetch`(**N16**，该重试) / `commit_not_found` / `toolchain_drift`(A2) / `dead_external_url` / `dockerfile_drift` / `timeout` / `compile_error`(重试无用) / `no_target` / `archive_failed` / `unclassified`。⚠ 原把网络失败判成 `compile_error`（处置相反）→ 自测 8/8 |
| ▸ **build_error_detail / build_seconds** | str/float | ②(**W2**) | 首条真错误行（供按**根因**分组）/ 构建秒数（`T_build` 分布的原始数据） |
| ▸ **era_commit / era_cache_hit** | str/bool | ②(**W2**) | era-retry 解析出的 oss-fuzz commit（从日志 `Retrying on earlier OSS-Fuzz commit <sha>` 抓，✅ 与 P0-B 记录的 `a958ed8e` 一致）/ 本次是否**因缓存命中而预 checkout**（跳过注定失败的首试，✅ 实测省 49.5%） |
| ▸ commit_source | enum | ①先验→②实际 | `head`（commit 分量=解析的上游 SHA）/ `fixed_parent`（钉 `fixed^`）/ **`fixed_ancestor`**（钉 `fixed^^`/`fixed^^^`）/ `introducing`。与 `repro_version`/`pinned_commit` 一致（防假复现） |
| ▸ oss_fuzz_commit / pinned_commit / base_builder_digest | str | ② | 构建时 worktree HEAD（可溯源）/ 构建的上游 commit（HEAD 路径=解析的 SHA，解析不到=`UNKNOWN`+notes）/ era digest（gcloud 不可用→ⓘ） |
| observed_crash_type / observed_frames | str/[str] | ③ | 实测 crash 类型/符号化帧 |
| exit_code / signal / reproduced_any / retry_count | int/str/bool/int | ③ | 退出码/信号/是否任何崩溃/重试次数 |
| ▸ runtime_limits | str | ③(M11) | `timeout=25:rss_limit_mb=2560:symbolize=1:dedup_token_length=3` |
| **verification_tier** | enum | ④ | `strict`/`medium`/`loose`/`none`（下游最低 medium） |
| frame_match_score / crash_type_match | float/bool | ④ | `score_subseq`（**二值** 0/1）/ 类型一致；三量原值入 `details` |
| ▸ **score_pos / score_subseq / score_set** | float | ④(**W2**) | 三个分数**都落成顶层字段**（不再只藏 `details`）：位置化 / 有序子序列（strict 用此）/ 集合（对 observed **完整**栈） |
| ▸ **score_set_top3** | float | ④(**W2**) | 集合分对 **observed top-3** 的口径 = ✅ P0 报告记的「集合 2/3」，也是 §1.3④ 标定点「md4c set **0.67**」唯一能复现的口径（`score_set` 按 §1.3④ 表头用完整栈 → md4c 得 1.0）。**两个并存、不静默选边** |
| ▸ **score_subseq_frac** | float | ④(**W2**) | **N13**：`LCS(R,O)/|R|`（分数化子序列）。因为 `score_subseq` 二值 → `T_strict∈(0,1]` **结构上不可能有区分力**；旋钮移到这里（🅗 0.5–0.67） |
| ▸ **run_status** | enum | ⑤(**W2**) | `run` / **`not_run`**（在范围内但本轮没跑，如 testcase 磁盘缺失）→ 不让未跑的记录冒充 `tier=none` |
| ▸ **observed_crash_type_raw / _norm** | str | ③(**W2**) | sanitizer 报告的**逐字原文**（不解释）/ 经 ⓪ `normalize_crash_type()` 的归一值（④ medium 档比对此值）。ⓘ UBSAN 的形态无真实样本，只有合成 fixture 验过 |
| binary_sha256 | str? | ② | 归档二进制哈希（所有成功构建即归档时由 ② 算） |
| skip_reason | str? | ① | `unreproducible_no_target` / `missing_testcase` / `non_cpp_language` / `unmapped_project` / null。**语义 = 整条记录退出主线**（互斥、有优先级）；N6 退化**不入此枚举**（它只禁钉版、HEAD 仍可跑） |
| raw_log_path / notes | str | ③ | 完整 stderr 日志 / 备注（flaky、ubsan_stderr_detected、head_commit_unresolved、walkback_exhausted…） |

## 1.6 增量循环与续跑语义

- 单轮：`run_repro.py --projects <list> --limit <n> [--max-builds <n>] [--stage1-only] [--force]` → ①→⑤ → **追加**进 `repro_dataset.jsonl`。
- `state.json` 记：每 `(project,sanitizer,commit)` 的 `build_status` + `binary_dir`（归档位）+ era commit 缓存；每 osv_id 的 `repro_done`。重跑跳过已完成；`--force` 追加新 `run_id`（不删旧）。
- **钉版按 commit 区分**：同项目同 sanitizer 不同 `pin_commit` 各算一次构建、各归档各位；跨轮重跑 commit A 命中缓存 → 从 `binary_dir`=A 取 A 的二进制。
- 磁盘：worktree 独立 build/out + 轮间清理 + 归档（所有成功构建、仅二进制不含 seed_corpus + symbolizer 去重）控增长。✅ 实测量级：md4c 完整 `build/out/md4c` = 13M；归档 **≈46MB/次构建**（W2 782MB / 17 目录）。
- **[W3] 归档裁剪 = 默认执行**（原写成「可选」）：每轮 ⑤ 之后 ② `--prune-archive` 跑一次——
  * **保留** = 任何 `verification_tier ∈ {strict, medium, loose}` 的记录引用过的 `binary_dir`（**扫 dataset 全部行**、不只最新行，见 §3 N20）；
  * **裁掉** = 其余目录；`state.json` 对应缓存键一并删除 → 重跑时重建，**不会静默指向已删目录**；
  * `_shared/` 的 symbolizer **不动**（内容寻址 + 硬链接；硬链接文件不计入回收量）；
  * 依据：W2 的 129 条里 **113 条 `none`**，而 Hybrid 归档本就只交付 verified 子集；按队列外推 3,093 × 46MB ≈ **142GB** ≫ 磁盘。
  * ✅ W3 实测两次：存量 17 目录 → 裁 11、**回收 377MB**（633M→273M）；`w3-p5-cb` 轮末 22 目录 → 裁 15、**回收 889MB**。
- **[W4] 裁剪的安全化**：`--prune-archive` **默认 dry-run**（要真删须显式 `--prune-apply`；⑥ 轮末调用时传）；保护集之外再做一次**独立交叉校验**——用 verified 行的 `pinned_commit`(+project/sanitizer) 重算「哪些 commit 曾被引用」，与按 `binary_dir` 算的保护集**不一致即 `M>0` → 拒绝执行**（除非 `--prune-force`）。**用同一字段自查等于没查**，故必须换字段。每次裁剪（含 dry-run 与 REFUSED）写 `artifacts/prune_audit.jsonl`（含完整删除清单）。✅ 自测：构造 N20 事故形态 → `M=1` → **整轮拒绝**、连 `none` 的目录也不删。
- **[W4] ⑤ 的单调性校验**（写入侧防御，与裁剪侧配对）：曾达 verified 的 `osv_id` 不得被写成无结论行（`run_status≠run` 或 `tier=null`）→ **拒写 + 报错 + 记 `dataset_guard.jsonl`**；`--force` 才写并标 `tier_downgraded=true` + 原因；verified→另一个 verified 允许但留痕 `tier_changed_from`。**根因认知**：append-only 复现记录表里「最新一行 = 当前状态」，任何写入方的 bug 都能静默作废已交付结论——N20 只是这个根因的一个表现。
- **[W3] `--min-free-gb` 护栏**：② 每次构建前 + ⑥ 每条 crash 前查 `os.statvfs` 余量，低于阈值**停止本轮**（不是把盘写满）。取值理由见 §4.16。

## 1.7 错误处理（问题空间 A–H）

| 类 | 处置 |
|---|---|
| **A 版本/commit 漂移** | A1 bug 已在 HEAD 修复 → **[W3] 按 `commit_source` 分流**（`head` 组走 Stage1、has_fixed 直接钉版；旧「无差别 HEAD-first」已被实测推翻，见 §1.2）；A2 工具链漂移 → `build_specified_commit` era 自愈（`:234-278`；gcloud 不可用 → era digest 跳过、只剩 projects/ 侧，🅗 老 commit 失败率升高）；**A3 commit 缺失/误指** → 回退链 `fixed^`(3,550)→`introducing_commit`(226)→HEAD(14)，**且先过 ① 静态 check**（见 §2.4/§3 N3）；无 commit 者 `repro_version=none` + `notes="no_commit_to_pin"` |
| **B 构建** | B1 成功率 🅗 待首轮（yaml 声明支持 380/无字段 103/未声明 18 已测）；B2 sanitizer 支持（显式传 `--sanitizer`；`constants.py:21 DEFAULT_SANITIZER='address'`、`:38 SANITIZERS` 含 memory；MSAN 仅 9 条 yaml 未声明 memory = 🅗 风险）；B3 build 成功但 target 未产出 → **校验二进制实际存在**（防 `set +e`/`exit 0` 假成功）；B4 项目名映射（M2 命中 328/334，未命中 6 项目/42 crash → `unmapped_project`，**不擅自映射**）；`archive_failed`（构建成功但归档拷贝失败） |
| **C testcase** | C1 35 条磁盘缺失 → `missing_testcase`；C2 sha256 完整性；C3 engine None(535)=空 target(535) 同一批 → R7 净推定 156 |
| **D 执行/非确定性** | D1 flaky（MSAN/uninit 875 条）→ 重试 ASAN 1×/MSAN·uninit ≤3×，🅗 是否足够首轮再调；D2 ASLR → `run_fuzzer:21 sysctl vm.mmap_rnd_bits=28`，**不用地址匹配**；D3 timeout/OOM → 资源限额类仅 4 条（0.1%），非问题 |
| **E 验证** | E1 源 `crash_state` 几乎全空（3,789/3,790）→ 不用；E2 recovered 覆盖 3,770（20 无帧 → 降 medium/loose）；E3 成功标准 = Tiered；**E4 observed 帧**：✅ symbolize 生效、DEDUP_TOKEN 干净 top-3、内部帧 #11+、**0 个 `.part.NN`**；⚠ **归因注意**：off-by-one 主因判为**版本差**（pcre2 版本对齐+同等工具链漂移 → 项目帧**零偏移**；md4c 版本远 → 真实移位），但 **md4c/pcre2 是不同项目、帧稳定性本身依项目而异 → 两者不可比，该归因置信度降一档**；要彻底证需「同项目同版本不同 clang」对照 |
| **F 规模** | F1 增量限界（`--limit` 界 crash + `--max-builds` 界构建 + `state.json` 续跑）；F2 去重（缓存键含 commit + `binary_dir` 指归档位 + HEAD 分量用解析 SHA）；F3 优先级（增量循环，无 Phase 体系） |
| **G 环境** | **G1 代理**：宿主 clash `127.0.0.1:7890`（**仅绑 loopback** → 容器必须 `--network=host`）；gcr.io pull + apt **不需**代理，github **无代理被 reset**。✅ **三个 docker 调用点全覆盖**：① `docker build` → worktree `infra/common_utils.py:build_image_impl` 加 `--network=host`+代理 build-arg；② `docker run`（build_fuzzers/copy_src/reproduce）→ `infra/helper.py:660 docker_run` **统一注入** `--network=host`+代理 `-e` env；③ `detect_main_repo` 的 bespoke `docker run`（走 `utils.execute` 捕获 stdout、**不经 docker_run**，无法统一到同一点）→ 用 `build_specified_commit --repo_url/--repo_path` **旁路跳过**。G2 base-runner 版本（`Dockerfile:77-80` 默认值已知；era-digest 需 gcloud ⓘ）；G3 磁盘（ⓘ 待首轮，M12 外推已撤回） |
| **I 负对照（W4 定稿判据）** | **① 默认用 HEAD 二进制**做对照（HEAD 上绝大多数 bug 已修、窗口冲突概率最低、HEAD 构建**共享**故成本最低）：同项目其他 bug 的 testcase ≥3 条 + 随机 256B + 别项目 testcase 1 条 → 全期望 none。**② 版本感知作补充**：仍要在钉版二进制上做对照时，只挑「`[introduced, fixed)` 窗口**不含**被测 commit 日期」的其他 crash。**③ 正对照**：目标 bug 在自己那台二进制上仍须崩（否则「全 none」只说明二进制坏了）。✅ W4 实测 **11/11 通过 + 正对照 2/2**。<br>**为什么改（N21）**：原判据「用复现出来的那台钉版二进制跑同项目其他 bug」对老二进制**前提不成立**——老版本里同时活着别的 bug。✅ W3 实例：c-blosc2@`886d4c9b`(2022-06-09) 跑 OSV-2021-1791 的 testcase 真崩，而其窗口 `2021-02-18→2022-06-13` **含**该日 → 那是**真阳性**（流水线在正确版本上找到了正确的 bug），不是仪器故障。**该实例保留为正面结果，不当缺陷记。** || **H 共享 oss-fuzz 树隔离** | 见下 |

### H worktree 隔离与 gate（✅ W1 已固化）

**问题（✅ 审计B）**：主树 `/root/gyx/oss-fuzz` 被 driver_create 污染——`git status --porcelain` **550 脏项**（含 `M infra/helper.py`）、**38 个 dc-injected** build.sh/Dockerfile（13 项目全在 crash 数据集）；`ndpi/build.sh:3 set +e` + `:87 exit 0` → 构建恒假成功；`clear.sh` 不足以还原。
**方案**：**不清理主树**（driver_create 是在跑的研究线，其 `helper.py` 改动是有意的代理透传，还原=反向污染），改开**独立 worktree** `/root/gyx/oss-fuzz-repro`（`git worktree add -f … HEAD`，✅ P0 建树成功：detached `5c437ffb9`、7035 文件、1.1s、69M、.git 共享）。选 worktree 而非独立克隆：省磁盘、docker build 上下文用 worktree 的 `projects/<p>`、`build/out/` 天然隔离、检出官方 helper.py。

**gate = 四条件**（全部可机检，✅ W1 实测通过）：
```bash
# ①在 repro-patches 分支（不是 detached HEAD、不是 master）
[ "$(git -C $REPRO_OSS_FUZZ_DIR rev-parse --abbrev-ref HEAD)" = "repro-patches" ]
# ②无未提交改动（N4 era-retry 的 projects/ 脏项已还原）
[ -z "$(git -C $REPRO_OSS_FUZZ_DIR status --porcelain)" ]
# ③三补丁的 commit 在 HEAD 历史里
git -C $REPRO_OSS_FUZZ_DIR merge-base --is-ancestor 07522dc0e HEAD
# ④无 dc-injected 残留
! grep -rl dc-injected $REPRO_OSS_FUZZ_DIR/projects/
```
- **为何 ③ 不可省**：三补丁提交后 ② 又变回可满足，但一个「干净却在官方 HEAD」的树会**静默缺三个补丁** → 构建在拉取阶段全灭而 gate 看不出来。gate 必须**正向校验补丁存在**，不能只校验干净。
- **为何不用原「worktree 干净」单条件**：三补丁以未提交改动存在时 `status --porcelain` 恒非空 → gate 要么永远 ABORT、要么被放宽成永真（形同取消）。
- **附带收益**（✅ 实测）：补丁入 HEAD 后，误跑宽范围 `git checkout HEAD -- .` 也不再抹掉它们（此前任何此类操作都会让整条流水线失去基础）。
- **三补丁**（`repro-patches` @ `07522dc0e`，3 files +66/−3）：`infra/common_utils.py:274-287`（docker build 代理）、`infra/helper.py:660 docker_run`（docker run 统一代理，+17）、`infra/build_specified_commit.py:382-419 main()`（`--repo_url/--repo_path` 旁路 detect_main_repo，+34/−3）。
- **可溯源**：每次构建记 `oss_fuzz_commit`（worktree HEAD）入 build_records + schema。

## 1.8 测试与验收（**首轮 = 标定轮，不是验收轮**）

**首轮硬门槛（仅这三条是通过条件）**
1. 端到端跑通首轮子集（HEAD-only `--stage1-only`），**无未处理异常**。
2. `repro_dataset.jsonl` 产出、**schema 完整**（每条带 `run_id`/`run_ts`、`binary_dir` 指 commit-specific 归档位）。
3. **负对照 100% none** + **worktree gate 生效**（人为污染触发 ABORT + `BLOCKED.md`）。
   > **[W3 修正]** 「100% none」这个门槛对**钉版老二进制**不成立：老版本里可能同时活着别的 bug（**N21**，✅ 实测 c-blosc2@`886d4c9b` 撞 OSV-2021-1791，其漏洞窗口确含该 commit 日期 → 是**真阳性**不是仪器故障）。判据改为：**随机字节 + 跨项目 testcase 必须 100% none**；「同项目其他 bug」只在**其漏洞窗口不含被测 commit**时才要求 none。gate 生效已被 W3 实证一次（N18 抓到真脏 → ABORT）。

**首轮标定产出（非通过条件，供后续轮固定的基线/阈值/正对照）**
4. yield 基线（**含按 fixed 分组**，验证「has_fixed 组 HEAD 复现率低」🅗 排序先验）+ `T_strict` 标定后固定入 config + build-time 基线。
5. **≥3 条人工确认可复现 crash（`reproduced_any=true ∧ tier≥medium`）固化入 config，作后续轮回归正对照**——解「鸡生蛋」：首轮前一条已知可复现的都没有（那正是流水线要产出的），故**首轮只跑负对照**，正对照由首轮产出后固化。
6. 抽查 ≥5 个 strict-tier 复现确为同一 bug（observed 归一化帧 vs recovered 一致）。

**后续轮验收硬门槛**：config 固化的正对照 100% ≥medium + 负对照 100% none + UBSAN stderr 检测专项通过（exit 0 仍判 reproduced）。

**负对照判据（✅ P0-B 已升级）**：~~随机 256B~~（弱——随机字节喂 parser 不崩是意料之中）→ **同项目其他 bug 的结构化 testcase ≥3 条**（最可能产生 **loose 级假阳性**者，而 loose 假阳性正是会污染下游变异归纳的那类）+ **目标正对照仍 crash**。✅ 已实测：md4c OSV-2022-40/-42（**-42 与目标 126 同 crash_type HBO READ 1**）+ pcre2 OSV-2024-324/-2023-674/-2025-300，**5 条异 bug 结构化输入全 `none`、目标仍 crash → 零 loose 假阳性**。

**组件级测试（防假复现的三条关键回归）**
- **缓存键**：同 `(project,sanitizer)` 但 `fixed^` 不同的两条 crash → 必须产出**两条不同 `(project,sanitizer,commit)` 构建记录**（不复用）；若误用旧键则第二条复用第一条二进制 → **本测试必须失败**。
- **缓存路径**：轮1 构建 commit A（归档 A、`binary_dir`→A）；轮2 构建 commit B（覆盖临时 build/out、归档 B）；轮3 重跑 A 命中缓存 → 必须取到 **A 的二进制**（用 `binary_sha256` 区分）；若 `binary_dir` 指共享路径 → **必须失败**。
- **HEAD 漂移**：轮1 HEAD 解析上游 SHA=X；轮2 上游已移到 Y → 键 `(p,san,Y)`≠`(p,san,X)` → **必须重建、不得复用 X**；若 HEAD 分量用字面 `"HEAD"` → **必须失败**。
- 另：帧匹配单测（合成 observed/recovered 验 strict/medium/loose + score）、`build_orchestrator --dry-run` 计数、worktree gate 单测、钉版 SHA 解析 dry-run（`get_parent`/`fetch_unshallow`/`checkout_commit` 参数层）、manifest 完整性（sha256/映射/空 target/缺失 testcase）。

**科学严谨校验**：ground-truth 抽查 ~5 个 strict 复现（人工核验是否同一 bug）；交叉校验 direct-docker-run 的 Tiered 结果 vs `helper.py reproduce`（sanity runner 不漏 crash）。

---

# 2. 实测结论（每行附来源；复算命令见 §6）

## 2.1 数据源与规模

| 项 | 实测 | 来源 |
|---|---|---|
| 数据源实际路径 | `mutator_create/data/crash_dataset.jsonl`(3,790)、`data/crash_state_recovered.jsonl`(3,790，3,770 有帧)、`crash_testcase/<crash_type>/<target>/<osv>.json`(3,790)、`data/_osv_cache/*.json`(3,790) | ✅ Step1 |
| crash_testcase JSON 覆盖率 | `introducing_commit` 3,772(99.5%)、`report_url` 3,790(100%)、`testcase_url` 3,762(99.3%)、`crash_address` 2,954(78%)、`fuzzing_engine` 3,255(86%)、`platform` 3,770(99.5%)；**`crash_dataset.jsonl` 里这些字段全空** | ✅ 2.1 |
| 源 `crash_state` | **几乎全空（3,789/3,790）→ 不能做 ground truth**；唯一本地 ground truth = `crash_state_recovered.jsonl`（符号化函数名字符串，抽样 592/592 全 str、0 裸地址、0 `??`） | ✅ 2.4/审计A |
| recovered 帧形态 | 94.4% 恰 3 帧；仅 11 条含内部帧；`is_file_frame` 标记文件名帧（第 3 帧常为源文件）；20 条 0 帧、192 条 1–2 帧 | ✅ M10 |
| sanitizer（全量/ C/C++） | ASAN 3,122/MSAN 460/UBSAN 183/空 25 ｜ ASAN 2,874/MSAN 427/UBSAN 176/空 25 | ✅ 2.2/R14 |
| crash_type | HBO 1,511(39.9%)/UNKNOWN 503/Use-of-uninit 415/HUF 356/Stack-overflow 219/Security exception 166；**资源限额类仅 4 条(0.1%)** | ✅ M5 |
| engine | libFuzzer 2,387/afl 581/空 535/honggfuzz 275/centipede 12（非 libFuzzer 868=22.9%） | ✅ M6 |
| testcase 体积 | P50 394B / P90 37KB / P99 900KB / max 3.7MB；60% <1KB；magic 多样（PDF/HDF5/MATLAB/ELF/PNG/HEIC/XML）；**minimized ⓘ 不可知** | ✅ M8 |
| 项目存活 | 334 crash 项目 vs oss-fuzz 1,362 目录 → 命中 **328 项目/3,748 crash(98.9%)**；未命中 6 项目/42 crash（oniguruma 9、upb 2 疑已移除 ⓘ；unrar 26、libfmt 3、apache-commons 1、grpc 1 候选歧义） | ✅ M2 |
| 聚类 | `(project,crash_type,recovered top-3)` → 3,301 簇/单例 89.4%/最大簇 11；归一化后单例 89.1%（降 0.2pp）；HBO 1,511→1,279 簇 | ✅ M7/R2 |
| 构建/运行单元 | HEAD `(project,sanitizer)` = 448（C/C++）/518（全 scope）；运行 `(project,fuzz_target,sanitizer)` = 939；535 条空 target；334 项目中 199 用 1 种 sanitizer/90 用 2/41 用 3/4 用 4 | ✅ 2.3/R14 |

## 2.2 帧归一化与验证

| 项 | 实测 | 来源 |
|---|---|---|
| `normalize_frames()` 实效 | 3,770 条有帧中 **502 条(13.3%)** top-3 键改变，其中 **498 条仅剔帧**（文件帧 635 / 内部帧 22），**真正文本归一只 4 条(0.1%)、suffix-strip 0 帧**、auto 4、lambda 0、operator 0 | ✅ R2-extra |
| 诚实重述 | recovered 帧本就是 ClusterFuzz 生产归一化后的 dedup token（上游已 strip `.part.NN`）→ **recovered 侧无版本漂移噪声可归一**；会引入 `.part.NN` 噪声的是 **observed 侧**（原始 ASAN stderr）。故「单例率仅降 0.2pp」**不能单独作为「无需去重」的强证据**——只能说「现有数据未观察到版本漂移型重复」；轻量归一化的 suffix-strip 规则是为 observed 侧准备的 | ✅ R2-extra |
| observed 侧帧形态 | ✅ symbolize 生效、DEDUP_TOKEN 干净 top-3、内部帧 #11+、**0 个 `.part.NN`**；轻量归一化够用、clusterfuzz StackParser 仍 P1（n=1） | ✅ P0 |
| off-by-one 两型 | ①拦截器帧假象（`__asan_memmove` 顶帧，剔内部帧即对齐）；②真实项目帧移位（md4c 顶部多 `md_resolve_links`，须子序列规则） | ✅ P0/P0-B |
| 版本差 vs 工具链差 | pcre2 版本对齐 + 同等工具链漂移(2024→2026 clang) → **零真实移位**；md4c 版本远 → 真实移位 → 主因是**版本差**。⚠ 两例是不同项目、帧稳定性依项目而异 → **不可比，置信度降一档**；彻底证需「同项目同版本不同 clang」对照 | ✅ P0-B + W1 复核 |
| `T_strict=1.0` | 两标定点 `score_subseq` 都 1.0 → **无区分力**（未被证伪 ≠ 被验证）；保持 1.0、每条存三量备重标定 | ✅ P0/P0-B/P0-C |

## 2.3 构建、钉版与代理

| 项 | 实测 | 来源 |
|---|---|---|
| worktree 建树 | detached `5c437ffb9`、7035 文件、1.1s、**69M**（.git 共享）；三校验全过（porcelain 空/无 dc-injected/helper.py 官方）；主树仍 **550** | ✅ P0 |
| 代理需求 | gcr.io pull + apt **不需**代理；github clone **无代理被 reset**；clash **仅绑 loopback** → path (i)（只设 env）不够，**path (ii)（`--network=host` + 代理注入）必需且够用** | ✅ P0 |
| `T_build` | HEAD 同-commit 暖建 **10s**；HEAD 冷建 **~131s**（md4c）；**钉版 5–10min/次**（pcre2 `fixed^` 9m44s 含 era-retry、`fixed^^` 4m52s 首试即成）→ **`--max-builds N` ≈ N×5–10min**（暖建 10s 不可作钉版参照：钉版走 copy_src+checkout+全量重编译） | ✅ P0/P0-B |
| HEAD 上游 SHA 解析 | `docker run gcr.io/oss-fuzz/md4c git -C /src/md4c rev-parse HEAD` = `61f5ce76…`（`/src/md4c/.git` 在、Dockerfile 全量 clone）；`helper.py` **不捕获**（grep 仅 fuzzbench clone @`:1053/1548/1576`）→ 须额外一步；tarball 项目 fallback 仍 🅗 | ✅ P0 |
| 磁盘 | md4c 完整 `build/out/md4c` = **13M**（fuzz-mdhtml 5.9M + llvm-symbolizer 6.8M + seed 4K + dict 4K）；**symbolizer 跨构建 sha256 相同 → 内容寻址去重 + 硬链接，单构建边际增量 ≈ 仅二进制本身** | ✅ P0/P0-B |
| era 自愈 | projects/ 侧自愈**有效**（pcre2 HEAD build.sh 的 dict 路径×`fixed^` 布局不匹配 → era `a958ed8e` build.sh 成功），**即使无 gcloud era base-builder**；前提 era Dockerfile 的 apt 包在当前 ubuntu 仍在（**反例**：flatbuffers 因 `ninja`→`ninja-build` 改名而 era-retry 失败） | ✅ P0-B |
| 钉版主路径打通 | pcre2 全程走通：`get_parent`✅（`get_parent(6f36e8ab,1)=037fb170`、`,2)=62b3ceca`，host `rev-parse` 交叉一致）→ `detect_main_repo`（全量 clone 离线命中）→ `copy_src_from_docker` → `checkout_commit` → era-retry → `build_fuzzers_impl` → reproduce | ✅ P0-B |
| **detect_repo 可达率（两个数，前提不同勿混）** | ① **修 N5 前 = 全量 clone only ≈ 19%（49/257）**（浅克隆 73%/187 被阻塞、混合 7%/17、无 clone 2%/4；19%+73%=92%，余 8% = 混合+无 clone）；② **修 N5 后 ≈ 98%（253/257 git-clone 项目）**。⚠ 这是「**detect_repo 可达率**」**不是「端到端可构建率」**——后者仍受 era 死外链（libspng）/Dockerfile 漂移（lcms）/工具链漂移（flatbuffers）限制，🅗 待首轮多项目实测，**不可用 98% 冒充** | ✅ P0-B/P0-C |
| 三调用点代理覆盖复验 | hunspell（浅克隆，N5 样本）：修前 `detect_repo` fetch→`gnutls_handshake failed`→ValueError；修后旁路 → **EXIT=0，1m0.8s**。c-blosc2（build 期 CMake FetchContent）：修前挂起 15min 被 kill；修后 `docker_run` 代理 → **lz4/zlib-ng/zstd/zfp 全下载、EXIT=0，1m21.6s** | ✅ P0-C |
| **`repo_path` 假设审计** | `build_specified_commit.py:425` 只用 `os.path.basename(repo_path)` 拼宿主 /src 副本 → 隐含 (A) 仓库在 `/src/<project>`、(B) 是 /src 直接子目录。实测：**(A) 只对 89.7% 的 C/C++ 项目成立**（243/271；异名 22 个）；**(B) 破裂 1 个**（qt→`/src/qt/qt5`，11 条 crash）——**且这是上游工具自身的缺陷**（原版 `detect_main_repo` 返回 `/src/qt/qt5` 后同样被 basename 拼错），非旁路引入 | ✅ W1 |
| **逐 crash `repo_path` 解析率** | `high` 3,189(**91.1%**) + `medium` 227(6.5%) = **97.5% 可直接用**；`candidates` 50(1.4%) 运行期 `git cat-file -e` 定夺 → **99.0%**；`none` 36(1.0%) 回退 `detect_main_repo` | ✅ W1 |
| **为何必须逐 crash 解析、不能按项目猜** | 反例：binutils 同时 clone `binary-samples`(样本数据) 与 `sourceware binutils-gdb`，按「第一个 clone」猜会选错；xpdf 只 clone freetype（本体是 wget tarball）→ 会得 `/src/freetype`；mosquitto 会得依赖 `/src/libprotobuf-mutator`；pidgin `main_repo` 是 sourceforge **tarball**（/src 内无 git）；capstone 同 repo 两 branch（`capstonev5`/`capstonenext`）；open62541 两版本目录；openssl **6 个**版本目录；libjpeg-turbo dest 含未展开变量 `libjpeg-turbo.$branch`；freetype2 `main_repo` 竟是 `freetype2-testing`、**库本身没被 clone** | ✅ W1 |
| 扫描器自身三处修正（由反例发现） | ①`--recurse-submodules` 是**布尔** flag 却被当作取值选项 → 吃掉后面的 URL（arrow 被解析成 `url='$SRC/arrow'`；影响 18 个 Dockerfile）；②`${SRC}` 花括号写法漏替换（影响 **39** 个 Dockerfile，mosquitto 因此被误判 dynamic）；③**删除「仅一个 clone 就用它」的回退**——实测该回退会选到**依赖仓库**（xpdf→`/src/freetype`、mosquitto→`/src/libprotobuf-mutator`），**宁可返回 null 交运行期回退，不可给出错的 repo_path**。修后 high 置信 87.4%→**90.1%**、`dynamic_dest` 4→2、错映射→0 | ✅ W1 |

**附表 3 `repo_path` 项目级 kind 分布（扫描 328 个 crash 相关项目；机器可读版 = `artifacts/repo_path_map.json`）**

| kind | 全部 328 | C/C++ 271 |
|---|---|---|
| `exact_single` | 185 (56.4%) | 159 |
| `exact_multi` | 101 (30.8%) | 84 |
| `alias_main_repo` | 30 (9.1%) | 19 |
| `ambiguous_multi` | 7 (2.1%) | 5 |
| `alias_single` | 2 (0.6%) | 2 |
| `dynamic_dest` | 2 (0.6%) | 1 |
| `nested_or_outside_src` | 1 (0.3%) | 1 |

> `no_git_clone` = **0**（所有 crash 相关项目的 Dockerfile 都至少有一个 git clone；但 pidgin/xpdf 等**本体是 tarball**、clone 的是依赖 → 逐 crash 解析落 `none`，正是「不能用项目级 kind 代替逐 crash 解析」的原因）。

**异名映射表（假设 (A) 不成立者；机器可读版 = `artifacts/repo_path_map.json`，`repro_common.resolve_repo_path()` 消费）**

C/C++ 主线 22 个（★ = 逐 crash 解析实际会用到）：

| project | repo_path | project | repo_path |
|---|---|---|---|
| apache-httpd | `/src/httpd` | php | `/src/php-src` |
| capstone | `/src/capstonev5`（+`capstonenext` 候选） | python3-libraries | `/src/cpython` |
| firestore | `/src/firebase-ios-sdk` | qt | `/src/qt/qt5` ⚠**basename_unsafe** |
| freeradius | `/src/freeradius-server` | s2opc | `/src/S2OPC` |
| freerdp | `/src/FreeRDP` | sudoers | `/src/sudo` |
| freetype2 | `/src/freetype2-testing` ⚠**库本身未被 clone** | tesseract-ocr | `/src/tesseract` |
| gfwx | `/src/gfwx-fuzzers` | uwebsockets | `/src/uWebSockets` |
| ghostscript | `/src/ghostpdl` | wasmedge | `/src/WasmEdge` |
| libaom | `/src/aom` | xpdf | `/src/freetype` ⚠**是依赖、本体为 tarball** |
| libyal | `/src/libfplist`（51 个 dest） | llamacpp | `/src/llama.cpp` |
| mapserver | `/src/MapServer` | pcapplusplus | `/src/PcapPlusPlus` |

非主线 11 个：antlr4-java→`/src/antlr4`、apache-commons-{codec,configuration,jxpath,lang}→`/src/commons-*`、cras→`/src/adhd`、pillow→`/src/Pillow`、powsybl-java→`/src/powsybl-core`、tensorflow-py→`/src/tensorflow`、ujson→`/src/ultrajson`。

> ⚠ 三个标记者说明「**项目级 default 不可信、必须逐 crash 解析**」：`freetype2` 的 `main_repo` 与唯一 clone 都是 `freetype2-testing`（freetype2 库源码来自别处）；`xpdf` 只 clone 了依赖 freetype（本体 `wget` tarball）；`qt` 是嵌套 dest。这三者逐 crash 解析的实际结果是 `none`（回退 `detect_main_repo`）或 `basename_unsafe`，**不会**把上表的错值交给 ②。

## 2.4 OSV `fixed` 数据质量与钉版策略（W1 抽样）

**抽样**：总体 = C/C++ ∩ has_fixed = **3,301**（✅ 与 R14 一致）；分层随机 **48 条**（seed 20260909、同项目 ≤2、41 项目、11 年份全覆盖、**轮转非取前 N**）。diff 用 `github.com/<o>/<r>/commit/<sha>~N.patch`（N=0..3）+ GitLab `.patch`+`/api/v4 parent_ids` → **0 次 GitHub API**（无 token 仅剩 46/60，192 次会撞墙）、**0 次 clone**、0 次 docker。托管覆盖 84.7%（github 2,576 + gitlab 221）。

**可证伪判据（先定判据再测）**：🅗 H1「off-by-one 是系统性的 → 默认应改 `fixed^^`」vs 🅗 H2「2/2 是巧合 → 默认保持 `fixed^` + 静态 check + 有界 walk-back」。**判据：若 off-by-one ≥50% 则 H1 成立；若显著 <50% 且 95% 区间上界也 <50% 则 H2 成立。**  stakes：每猜错一格 = 一次 5–10min 白构建，在 3,301 条钉版规模上是**一半的构建成本**，故此默认值必须在写代码前测定。**结果：H1 被否证（上界 27.8% ≪ 50%）、H2 成立。**

**diff 端点实测（决定「不 clone、不用 API」这条路走得通）**：

| 端点 | 实测 | 用途 |
|---|---|---|
| `github.com/<o>/<r>/commit/<sha>.patch` | ✅ 200（pcre2 6f36e8ab，21,945 B） | mbox patch：`From <sha>`+Date+Subject/正文+全部 hunk |
| `github.com/…/<sha>~N.patch`（N=1,2,3） | ✅ 200（`~1` 返回父 `037fb170`） | **免 API 拿父/祖先** |
| `gitlab.com/<g>/<r>/-/commit/<sha>.patch` | ✅ 200（wireshark aa3bbe5a） | GitLab 四实例同法 |
| GitLab `<sha>~1.patch` | ❌ **302 → sign_in** | GitLab 不解析 `~N` |
| GitLab `/api/v4/projects/<enc>/repository/commits/<sha>` | ✅ 200 免认证，返回 `parent_ids` | GitLab 取父 |
| `api.github.com` | ⚠ 无 token，core 限额 60/h、**实测仅剩 46** | **完全避开**（48×4=192 次会撞墙） |

**附表 2 年份分布（等量分层，非按比例）**

| 年 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 抽样 n | 3 | 4 | 5 | 1 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| 总体 n | 7 | 47 | 186 | 1 | 994 | 658 | 527 | 432 | 253 | 153 | 43 |
| 总体占比 | 0.2% | 1.4% | 5.6% | 0.0% | **30.1%** | 19.9% | 16.0% | 13.1% | 7.7% | 4.6% | 1.3% |

⚠ 2020 占总体 30.1% 却只抽 5 条、2019 总体仅 1 条却抽满 → **未加权比例对总体有偏**，故另给年后分层加权值（11.8%）作敏感性对照；但每年 n=1–5、年别率区间极宽（2020 的 0/4 → 0–60%），**加权值并不比未加权值更可靠，只是偏差方向不同**——两个数都报，不挑好看的。

**附表 1 抽中清单（48 条实测结果；由 `preflight/history/offbyone_sample_results.json` 生成，重跑脚本可复现）**

| osv_id | project | 年 | 判定 | d_fix | 须钉 depth | S(C0/C1/C2/C3) | intro_depth | `fixed` 是 no_source |
|---|---|---|---|---|---|---|---|---|
| OSV-2026-21 | ndpi | 2026 | 命中 | 0 | 1 | 6/3/0/1 | – |  |
| OSV-2025-114 | net-snmp | 2025 | 命中 | 0 | 1 | 6/0/3/0 | – |  |
| OSV-2024-98 | upx | 2024 | **OBO** | 1 | 2 | 0/5/0/0 | – |  |
| OSV-2023-1320 | binutils | 2023 | 无法判定 | – | – | -/-/-/- | - |  |
| OSV-2022-709 | ndpi | 2022 | 命中 | 0 | 1 | 7/0/1/1 | – |  |
| OSV-2021-924 | dnsmasq | 2021 | 无法判定 | – | – | -/-/-/- | - |  |
| OSV-2020-881 | radare2 | 2020 | 未确认 | – | – | 0/0/0/0 | – |  |
| OSV-2019-1 | envoy | 2019 | 命中 | 0 | 1 | 2/1/0/1 | – |  |
| OSV-2018-219 | freetype2 | 2018 | 命中 | 0 | 1 | 3/3/-/- | – |  |
| OSV-2017-29 | open62541 | 2017 | 未确认 | – | – | 0/1/1/0 | – |  |
| OSV-2016-3 | file | 2016 | 未确认 | – | – | 0/0/0/0 | – |  |
| OSV-2026-119 | gpsd | 2026 | 未确认 | – | – | 1/0/1/0 | – |  |
| OSV-2025-827 | libjxl | 2025 | **OBO** | 2 | 3 | 1/1/3/0 | – | 是 |
| OSV-2024-322 | pistache | 2024 | 命中 | 0 | 1 | 4/2/0/1 | – |  |
| OSV-2023-221 | flac | 2023 | 命中 | 0 | 1 | 8/3/2/0 | – |  |
| OSV-2022-1111 | wireshark | 2022 | **OBO** | 2 | 3 | 1/1/2/1 | – |  |
| OSV-2021-1117 | clamav | 2021 | 命中 | 0 | 1 | 2/1/1/1 | – |  |
| OSV-2020-1677 | open62541 | 2020 | 命中 | 0 | 1 | 3/0/0/0 | – |  |
| OSV-2018-64 | harfbuzz | 2018 | 命中 | 0 | 1 | 4/2/0/0 | – |  |
| OSV-2017-8 | curl | 2017 | 命中 | 0 | 1 | 8/1/0/0 | – |  |
| OSV-2016-6 | file | 2016 | 未确认 | – | – | 2/1/0/0 | 0 |  |
| OSV-2026-195 | libical | 2026 | 命中 | 0 | 1 | 4/0/1/0 | – |  |
| OSV-2025-481 | glaze | 2025 | 未确认 | – | – | 0/1/1/1 | – |  |
| OSV-2024-20 | htslib | 2024 | 命中 | 0 | 1 | 6/3/1/3 | – |  |
| OSV-2023-1000 | libxml2 | 2023 | 命中 | 0 | 1 | 3/4/4/4 | – |  |
| OSV-2022-892 | cyclonedds | 2022 | 命中 | 0 | 1 | 4/1/0/2 | – |  |
| OSV-2021-1447 | frr | 2021 | 未确认 | – | – | 1/0/0/1 | – |  |
| OSV-2020-392 | gdal | 2020 | 命中 | 0 | 1 | 8/0/1/2 | – |  |
| OSV-2018-126 | harfbuzz | 2018 | 命中 | 0 | 1 | 2/1/3/4 | 2 |  |
| OSV-2017-53 | libpsl | 2017 | 命中 | 0 | 1 | 8/1/-/- | – |  |
| OSV-2016-4 | libtsm | 2016 | 无法判定 | – | – | -/-/-/- | - |  |
| OSV-2026-74 | assimp | 2026 | 命中 | 0 | 1 | 8/3/3/1 | – |  |
| OSV-2025-17 | opencv | 2025 | 命中 | 0 | 1 | 2/1/0/3 | – |  |
| OSV-2024-1209 | libxml2 | 2024 | 未确认 | – | – | 0/0/0/0 | – |  |
| OSV-2023-382 | wabt | 2023 | 命中 | 0 | 1 | 3/1/0/1 | – |  |
| OSV-2022-819 | libraw | 2022 | 未确认 | – | – | 1/1/1/1 | – |  |
| OSV-2021-1312 | simdjson | 2021 | **OBO** | 1 | 2 | 0/2/1/0 | 3 | 是 |
| OSV-2020-380 | openthread | 2020 | 命中 | 0 | 1 | 2/1/0/2 | – |  |
| OSV-2018-41 | botan | 2018 | 命中 | 0 | 1 | 8/2/0/1 | – |  |
| OSV-2017-161 | libtsm | 2017 | 无法判定 | – | – | -/-/-/- | - |  |
| OSV-2026-167 | gpsd | 2026 | **OBO** | 2 | 3 | 0/0/4/1 | – |  |
| OSV-2025-291 | poco | 2025 | **OBO** | 1 | 2 | 0/4/1/2 | – | 是 |
| OSV-2024-88 | php | 2024 | 未确认 | – | – | 0/0/0/0 | – | 是 |
| OSV-2023-285 | ghostscript | 2023 | 无法判定 | – | – | -/-/-/- | - |  |
| OSV-2022-267 | fluent-bit | 2022 | 未确认 | – | – | 1/1/0/0 | – |  |
| OSV-2021-1229 | flatbuffers | 2021 | 命中 | 0 | 1 | 3/4/0/1 | – |  |
| OSV-2020-769 | perfetto | 2020 | 无法判定 | – | – | -/-/-/- | - |  |
| OSV-2018-71 | openvswitch | 2018 | 命中 | 0 | 1 | 8/1/1/1 | – |  |

> `S` = 复合证据分逐深度值；`intro_depth` = introducing commit 在链内深度（`–` = 比 depth3 更深，39/48）；`d_fix` = 最小 d 使 `S≥2 且非 no_source 且 d<intro_depth`。逐条的 `msg`/`files`/`ev_*`/`chain` 原值都在 JSON 里（40 字段/条），本文只列判定所需列。

**判定 = 复合证据分 S(commit)**：`+3` 该 crash 自己的 OSS-Fuzz issue id 在 message ／ `+2` ≥1 帧函数名 whole-word 在 patch 体 ／ `+2` message 引用 OSS-Fuzz/ClusterFuzz ／ `+1` 通用修复意图 ／ `+1` 帧的 C++ 类名或「文件名 stem↔帧核心名」相关 ／ `+1` 类名 token↔改动路径（≥2 token）；**外加 `no_source` 硬否定**（改动全落在 docs/CI/打包/构建配置 → 不可能修掉内存安全 crash）。取 **`d_fix` = 最小 d 使 `S(C_d)≥2 且非 no_source 且 d<intro_depth`** → `fixed_real=C_{d_fix}`、`pin_commit=C_{d_fix+1}`、`walkback_depth=d_fix+1`。

| 结果 | 计数 | 占可判定 42 | Wilson 95% |
|---|---|---|---|
| 命中（`fixed` 精确 → depth 1） | 25 | **59.5%** | 44.5–73.0% |
| **off-by-one**（真修复在 C1/C2） | **6** | **14.3%** | **6.7–27.8%** |
| 未确认（0..3 深度定位不到） | 11 | 26.2% | 15.6–40.3% |
| 无法判定（非 github/gitlab 托管） | 6/48 | – | 12.5%（与总体 15.3% 一致，无选择偏差） |

- **仪器校验**：两个已知 off-by-one 正对照 **2/2 判对**，但各靠不同信号——pcre2 靠**帧信号**、hunspell 靠**message 信号**，**单信号各漏一个**。
- **→ §1.3① 原「帧↔文件比对」判据被否证**：hunspell 的 `fixed`(6291cac8「change short to int」) 与其父(d6836713「ofz#51277 fix…」) **改同一文件 `affentry.hxx`、都不含任一帧函数名**（帧是 C++ 类方法，diff 只改类内 `getContLen()` 返回类型）→ 帧比对会答「命中」，真值是 off-by-one。
- **`no_source` 是比帧比对更强、且不需要帧映射的判据**：**8.3%**（4/48）的 OSV `fixed` 是纯 docs/CI 提交（php `UPGRADING.INTERNALS`、poco `.github/workflows/codeql.yml`、simdjson `doc/*.md`、libjxl CI+`.cmake`）。对照：`test_only`（tests/fuzz 目录）4/48 = **中性**（可能就是 harness 修复，此时 `fixed^` 是旧 harness、crash 仍复现）。
- **须钉深度 depth1/2/3 = 25/3/3** → **off-by-one 不止一格**，walk-back ≤3 是**必要上限而非余量**（本轮 0 条需 depth4，但 11 条未定位者真实需求 ⓘ 未知 → 不可据此把上限降到 2）。
- **`d_fix<intro_depth` 约束由反例确立**：harfbuzz OSV-2018-126 的 depth2 = `ab1f30bd`「[kerx] **Implement** Format6」**正是 OSV 的 introducing commit**——引入 bug 的提交必然「含有帧函数」（它就是写这些函数的），会被 `frames_in_diff` 误命中。加约束后 harfbuzz 正确判为 hit。修正前后 off-by-one 7→6、hit 25→25（**只影响 1 条 → 结论不是靠调规则凑的**）。
- **机制旁证（🅗，不作判据）**：`fixed`↔`fixed^` 间隔中位数 hit **0.5h** / off-by-one **10.3h** / 未确认 **30.9h**。⚠ `.patch` 的 Date 是 **author date**，rebase 会致负值（hit 组 5/25 负值，最小 −14,313min），且 hunspell 间隔仅 **48 秒**却是 off-by-one → **gap 小不能推出 `fixed` 精确，不可作判据**。

> ### ⛔ 下面这张表已**作废**（W3）——不要再拿它做决策
> 三个方向同时失效（✅ W3 实测）：①「每次钉版 5–10min」是 n=1 外推，实测中位 **73s**、项目间差 **47 倍**；② 模型只数**构建次数**、完全没进**构建失败率**（实测钉版 **12/47 = 25.5%** 失败）；③「未定位者三格全败」是**仪器假设**，W3 实测 10 条 `not_located` 里 **8 条 depth1 就复现**、2 条三格全空。W3 的实测重算见 **§4.19**。
> **W4 再确认（第三次被实测否证）**：策略 A 首次跑 `located` 记录 —— 10 条只用 **7 次真实构建**、拿到 **9 strict**；反事实的策略 B 需 8 次构建，而且其中 OSV-2020-2251 的 advisory 指向 depth3、**A 在 depth1 就拿到 strict**（B 会指错格）。→ **② 现在一律走 A，静态 check 降为 advisory**（§4.27）。三张表并列见 §4.27。原表保留仅作历史记录：

**四策略构建成本（同 42 条可判定；成功率均 31/42=74%；每次钉版 5–10min）**

| 策略 | 构建次数 | 每 crash |
|---|---|---|
| A 现状：默认 depth1 + 构建期 walk-back `[1,2,3]` | 73 | 1.74 |
| **B 采纳：① 静态 check 直接选 depth（未定位者退化为 A）** | **64** | **1.52（−12.3%）** |
| C 一律默认 depth2 `[2,3]` | 56 | 1.33 |
| D 变体：B + 未定位者从 depth2 起 `[2,3,1]` | 64 | 1.52 |

- **B 与 A 成功率相同、少 9 次构建** → 静态 check 的价值就是省掉 off-by-one 白构建，不牺牲任何复现。
- **D == B** → 省构建来自 walk-back 的**上限**（试几格）而非**顺序**。
- **不采纳 C**（虽然表面最省）：其额外 8 次节省**全部**来自「在未定位者身上少试一格」，而模型把未定位者判为三格全败是**仪器假设非实测**（静态定位不到 ≠ 复现不出）；本轮无构建**无法测量**这个取舍 → 不用未测量的收益换确定的损失。且 C 对 52.1% 的 depth1 案例多钉一格（增加 N4 era 风险，同样无法测）、要安全仍需同样的 `intro_depth` clamp 机制。
- **introducing 安全边界**：48 条中 **39 条 introducing 比 depth3 更深**（vulnerable 窗口宽 → 钉深通常安全），但 2 条边界紧（file OSV-2016-6 `intro_depth=0` 即 N6 退化；harfbuzz `intro_depth=2`）→ **必须 clamp**，否则钉到 bug 引入之前 = 假 none。

**决定**：**Stage2 默认仍钉 `fixed^`（depth 1）**；① 的静态 check 输出**三态 + depth 选择器**（`located` 直接钉 `pin_commit`／`not_located` 与 `undecidable` 交 ② walk-back ≤3／`degenerate` 禁钉版）。**P0-B/P0-C 的 2/2 是小样本巧合**（95% 上界 27.8% ≪ 50%）——若当初按 2/2 改默认为 `fixed^^`，会让 59.5% 的多数派白白多钉一格。

**局限（不掩盖）**：① `S≥2` 阈值人为定，非实测标定——25 条 hit 里 **5 条只有 S=2（单一信号）**，阈值提到 3 则 hit→20、off-by-one→16.2%（**方向不变**，绝对值有 ±3pp 规则敏感度）；② `not_located` 是**混合桶**（10 条「C0 触及源码但与帧无关」+ 1 条 `no_source`），含**仪器假阴性**（真修复在 C0 但证据弱，如 harfbuzz 型）→ off-by-one 率被**低估**；③ 只覆盖 github/gitlab（84.7%），其余托管未实现抓取器（标 `undecidable`，**不是判为无 off-by-one**）；④ 等量分层非按比例分层（2020 占总体 30.1% 但只抽 5 条）→ 年后分层加权 11.8% 作敏感性对照，但每年 n=1–5、年别率区间极宽，**加权值并不比未加权值更可靠**；⑤ ⓘ 超大 commit 的 `.patch` 可能被 GitHub 截断（本轮 48×4 个 commit 全部 200 且有完整 diff 体，**未观察到截断，但未专门测**。

## 2.5 R13 规则与 repo 覆盖

| 项 | 实测 |
|---|---|
| **R13a `fixed` 选择规则**（**W2 Phase0(a) 复算修正**） | 规则：①`introducing_commit` 匹配某 `introduced` → 取配对 `fixed`；②无匹配 → 取最后一个；③多匹配 → 取最后 + 标 notes。**「0 歧义」✅ 成立**（`intro_match_multi`=0，两种解析器都是 0）。两处修正：**①「multi-event 540」是错标签**——540 实为「**≥2 个 fixed 事件**」的记录数；真 multi-event = ≥2 对 **639** / >2 事件 **630**，且**全部 3,790 条只有 1 个 range（3,776）或 0 个（14）**，multi-range 从未发生。**②「15 条走取最后 fixed」错**——真值 **24**（540 内口径）/ **69**（全量）；`15 = 24 − 9`，那 9 条的 `introducing_commit` 是 OSV 哨兵 `"0"` 且其 OSV 内也含 `introduced:"0"` → R1 脚本传原始值必然假匹配（与「no_fixed 细分 introduced-only=0」**同一个 bug 的第二个症状**）。⓪ 已加哨兵守卫（防御性，① 行为不变、回归 29/29）。`n_osv_pairs` 只记录不参与决策 → 流水线行为不受影响 |
| **R13b repo 覆盖** | OSV `ranges[].repo` 存在 **3,776/3,790(99.6%)**；有 fixed 且有 repo **3,550**；vs `project.yaml main_repo`：一致 3,456 / **不一致 229** / 部分一致 43 / yaml 无 main_repo 48 / osv 无 repo 14。ⓘ **229 不一致档仍未触发实测**（P0-B 的 pcre2 属一致档） |
| **R1 修正（W1）** | R1 脚本报「no_fixed 中 introduced-only=0 / neither=240」是**解析假象**——其 `osv_events()` 只在遇到 `fixed` 事件时才 append `(introduced,fixed)` 对，故无 fixed 的 range 里 `introduced` 永不可见。✅ 重算 = **OSV 有 introduced 226 / 两者都无 14**（反例 md4c OSV-2022-126 正是「只有 introduced、无 fixed」，P0 就在该 commit 上复现成功）→ 回退链第二档从「看似 0 覆盖」变成 **94% 覆盖** |

---

# 3. 新发现 N1–N34（设计未预料，均须记）

| # | 现象 | ✅ 证据 | 影响与处置 |
|---|---|---|---|
| **N1** | OSV `no_fixed` 不可靠 | P0 | 不能把「无 fixed」当作「HEAD 必可复现」；只作排序先验 |
| **N2** | 钉版构建覆盖 `build/out` | P0 | 归档位必须含 commit 分量（→ R17-1，已入 §1.3②） |
| **N3** | **OSV `fixed` off-by-one/误指** → `fixed^` 落在真修复上 → 复现 `none` | P0-B pcre2（OSV `fixed`=6f36e8ab 改 JIT，真修复=037fb170 改 `pcre2_compile_class.c`）；P0-C hunspell（`fixed`=6291cac8，真修复=其父 d6836713）；**W1 抽样 14.3%** | ① 静态 check（复合证据分）定位 `fixed_real`/`pin_commit`；② 有界 walk-back ≤3 兜底；schema 加 `fixed_real`/`pin_commit`/`walkback_depth`/`fixed_misattributed`/`repro_version=fixed_ancestor`。**废「无界加 `fixed^^`」**（无界/污染 `tier=none` 语义/schema 缺值） |
| **N4** | `build_specified_commit` era-retry（`:268 git checkout <era> projects/<p>`）**弄脏 worktree** | P0-B（staged 改 `projects/<p>/{Dockerfile,build.sh,project.yaml}`） | 每次钉版后 `git checkout HEAD -- projects/<p>` 还原（✅ W1 实测只动 projects/、infra/ md5 不变）+ **era commit 按 `(project, 日期区间)` 缓存进 `state.json`**，跳过注定失败首试（省约一半钉版时间） |
| **N5** | `detect_repo.py:147-148` 对**浅克隆**项目在 no-proxy `docker run` 内 `git fetch --unshallow` → 被 github 阻塞 | P0-B：**73%（187/257）候选项目钉版主路径不可达**；P0 的 md4c 走通纯因其 Dockerfile 是全量 clone（`.git/shallow` 不存在→跳过 fetch→离线命中） | **✅ P0-C 已关闭**：`helper.docker_run` 统一代理 + `--repo_url/--repo_path` 旁路 detect_main_repo；hunspell（浅克隆）复验 EXIT=0 |
| **N6** | **OSV 退化 range：`introduced == fixed`** | ✅ W1 全量：60 对 / 53 条记录 / **53 crash(1.4%，C/C++ 36)**；例 file OSV-2016-6 `introduced=fixed=8a667072`，freetype2 OSV-2021-553/-602 共用退化 sha `9927e6ec` | vulnerable 窗口为空 → `fixed^` = `introduced^` = **早于 bug 引入** → 钉版必然**假 none**（且会被误读成「这版本没 bug」）。① 零成本可检（比对两 sha）→ 标 `osv_degenerate_range=true`、`static_check_verdict=degenerate`、`pin_commit=null`、**不进 Stage2**（仅 HEAD）；`skip_reason` 保持 null（记录仍可跑 HEAD）。与 N1/N3 同族 = OSV `fixed` 数据质量第 3 类缺陷。**[W2 Phase0(c) 修正] 不再一刀切**：53 条逐个用复合证据分复核 → **解禁 2 条**（h3 OSV-2021-1472 可执行、file OSV-2016-6 被 `skip_reason` 挡），判据 `S≥2 ∧ ¬no_source ∧ ¬test_only ∧ ¬harness_like ∧ frames_in_diff≠∅`；ⓘ「不像 fix」≠「证实是 introducing」，其余 51 条维持禁钉版是**保守**处置 |
| **N7** | **「加/改 fuzzing harness」类 commit 会被复合证据打分器（⓪ `score_commit()`）判成 fix**（它天然满足两个强信号：消息提 OSS-Fuzz → `ofz_ref` +2；diff 动被测函数 → `frames_in_diff` +2） | ✅ W2：N6 的 53 条上 8 个「像 fix」里 **6 个假阳性(75%)**——systemd「make … "public" **and add a fuzzer for it**」×2、libyal「**Added property OSS-Fuzz target**」×2、freetype2「preparing **fuzzer corpora**」×2(`test_only`)。`HARNESS_RE` 命中 7/40、精确率 7/7、不误杀 file/h3 | ⓪ 加 `ev["harness_like"]`（**只记证据不改分** → W1 的 14.3% 不受影响）+ `resolve_degenerate()` 用它作取消资格条件。⚠ W1 的 off-by-one 抽样里该形态 **0/25**，故 14.3% 未见污染 |
| **N8** | **`job_type` 编码了架构；i386 崩溃在 x86_64 构建下结构性不可复现** | ✅ W2 全量：i386 **164**（可执行 3,136 中 **163** = 5.2%）；项目 top = c-blosc2 **24**/harfbuzz 15/openh264 13/libxml2 13。实证 hunspell OSV-2022-886（`libfuzzer_asan_**i386**_hunspell`）在 HEAD + 三格钉版共 **4 个版本全 none**，而 target 正常执行（`Executed /testcase in 10 ms`） | ⓪ `job_arch()` + manifest `job_arch` 字段。**不据此 skip**（很多内存错与架构无关），只作分层先验 + notes。ⓘ 本轮 `none` 里有多少由它造成**未分离** |
| **N9** | **`ofz_ref`(+2) 不校验是哪个 issue 号** → 修**别家** bug 的 commit 也拿 +2 | ✅ W2：hunspell OSV-2022-886 的 issue=**51242**，被归因的 `d6836713` 消息是「**ofz#51277** fix negative condition length」→ `issue_id_in_msg`(+3) 未命中、`ofz_ref`(+2) 命中。W1 48 条链上该形态 **0/25** | **① 回归基线里 hunspell 的 `fixed_real`/`fixed_misattributed` 不是「已知答案」**，而是 P0-C 单次负观测的推断 → 已在 `DISPUTED` 表标**争议、不计分**（照打印、不进 pass/fail）。⓪ 加 `ev["ofz_other_id"]`（只记不改分）。🅗 下轮把「提到别家 ofz# 号」做成**负**信号并重标定 W1 |
| **N10** | **worktree 隔离不覆盖 docker 镜像**：§1.7 H 四条件全过，镜像里仍躺着主树注入的源文件 | ✅ W2：`docker run … ls /src/*crfuzzer*` → **harfbuzz 74 / libspng 60 / libtiff 55**（8 天前从**污染主树**建），md4c/pcre2/hunspell/c-blosc2/flatbuffers = **0**。主树这些项目 Dockerfile 确有 `COPY *_cross_crfuzzer.c $SRC/`（**会烤进镜像层**） | gate 加**第五条**（镜像 `/src` 内 dc 注入源必须 0，否则 ABORT）；本轮据此**排除** harfbuzz(68 条可执行)/libtiff/libspng。ⓘ `build_fuzzers` 会从 worktree 重 `docker build`（缓存到分叉层）→ 🅗 重建可自愈，**未实测** |
| **N11** | **归档只拷二进制 + `.options`/`.dict` 不够：target 可能要运行期数据文件**，缺了就在 `LLVMFuzzerInitialize` 里 trap → **假复现** | ✅ W2：flatbuffers `monster_fuzzer` 因归档缺 `monster_test.bfbs`(14,520 B，就在 `build/out` 里) → `LoadBinarySchema`→`TestEq`→`TestFail`→**故意 SIGILL**（`test_init.h:23`），栈 `#4 LLVMFuzzerInitialize`。**10 条被误记成「复现+loose」**，一度把 HEAD yield 从 0% 抬到 9.1% | ② 归档改为「**全部 target + 全部非可执行数据文件**（排除 `_seed_corpus.zip`、单文件 ≤32MB）」；③ 加 **init 失败判据**（崩在 `LLVMFuzzerInitialize` 或无 `Running:` 行 → `target_init_failed`，**不计复现**）。修后 flatbuffers 12 条正常执行、0 init 失败 |
| **N12** | **walk-back 的停止判据「首个 `reproduced_any=true`」会停在无关 bug 上** | ✅ W2：OSV-2020-2251 期望 `Heap-buffer-overflow`(R=`blosc_run_decompression_with_context`/…)，depth1 实测 `Heap-use-after-free READ 32`(O=`MemcmpInterceptorCommon`/`memcmp`/`free`/…，**帧全不同**) → 判 `loose` 并停；而补跑的静态 check 说真修复在 depth2、应钉 depth3 | 停止判据应改 **tier 感知**（首个 crash_type 一致**或**帧对齐的格才停）。**W3 已实现 tier 感知**（达 medium+ 才停；14 次下探 **0 次**改善 tier）→ 由此提出 🅗「`frac≥0.6` 即停」。**W5 实现但默认 OFF**：判据抽成纯函数 `stop_decision()`、`--stop-frac` 默认 0、**shadow 字段常开**；离线回放（0 次构建）显示阈值 0.6 触发 5 次 / 省 7 格 / **tier 损失 0**，但只 **3 条不同 crash**（同一条在 depth1、depth2 各触发一次 = 嵌套重复计数）且 c-blosc2 占 20/24 → n 太小；**更关键：默认 ON 会摧毁测量通道**（一停就再也观察不到更深格）→ 省 23% 格构建 vs 永久失去定论能力，选后者。**预注册翻转判据：distinct-crash n≥10 且 tier 损失 0**（现 n=3，还差 7 条）。详见 §4.36 |
| **N13** | **`score_subseq` 是二值的 → `T_strict` 结构上不可能有区分力** | ✅ W2：定义即「R 是否 O 的有序子序列」→ 只取 {0,1}；实测 7 条 `subseq=0.0 ∧ ct_match=True` 的样本，阈值降到 0.5 **一条也不会变**（0.0<0.5） | ④ 并行记 **`score_subseq_frac = LCS(R,O)/|R|`**（那 7 条 = 0.333×4/0.667×3）；**不改** `score_subseq`（两标定点保持 1.0）→ 旋钮移到 frac。🅗 建议 0.5–0.67，n=7 不足定 |
| **N14** | **相邻祖先 commit 可能产出 bit 相同的二进制** → walk-back 的「格数」≠「版本多样性」，会白建 | ✅ W2：hunspell `1f1d23ca`（只改 `src/tools/hunspell.cxx`=CLI）与 `e46b020b`（只改 `po/el.po`=**希腊语翻译**）产出的 `affdicfuzzer` sha256 **完全相同** `543f013e…`；而 `d6836713`（改 `src/hunspell/affentry.hxx`）= `d0a126d3…` 不同 → 证明 checkout **确实生效** | 🅗 可优化：① 静态 check 已逐格拿到 `files`，若某格改动与 target 源码**无交集**即可跳过（省一次构建）。**未实现**、影响面未量化 |
| **N15** | **帧完全对齐但 crash_type 变了 → 被判最低档 `loose`**，与直觉相反 | ✅ W2：OSV-2020-2184 五个分数 **全 1.0**（R 与 O 逐字相同 `frame_get_usermeta`/`blosc2_frame_to_schunk`/`blosc2_schunk_open_sframe`），只因期望 `Heap-buffer-overflow`、实测 `Segv on unknown address` → `loose` | 🅗 几乎肯定是**同一 bug 的不同表现**（越界读落到未映射页→SEGV 而非 ASAN 拦截）。建议加规则「帧全对齐 ∧ 类型不一致 → 至少 `medium`」（n=1，属 🅗） |
| **N16** | **`build_specified_commit` 内的 `git remote update` 是网络依赖的易失败步骤**，且失败形态易被误判成编译错误 | ✅ W2：c-blosc2@`9ba29ef1` → `RPC failed; curl 56 GnuTLS recv error (-9)` → `fatal: early EOF` → `Could not fetch origin`；分类器判成 `compile_error`（日志尾含 `error:`） | 分类器加 **`network_fetch`** 置最高优先级、改读**整份日志**、加 `build_error_detail`（自测 8/8）。**处置相反**：网络失败该重试、编译错误重试无用 → 🅗 ② 应对 `network_fetch` 自动重试 1 次（未实现） ｜ **[W5 升级 ✅]** 生产触发 **2 次、2 次都成功**：`5a65e3d8322f`（backlog2，重试 +80s → `ok` 223s）与 `ac116b4bac72`（backlog3 → `ok` 62s），首试失败形态与 W2 完全一致（`git remote update` → `RPC failed; curl 56 GnuTLS recv error (-9)` → `early EOF` → `Could not fetch origin`）。**且这次首试日志完整保留**（重试另存 `*_retry1.log` + N25 轮转），与 W2 那次「证据被覆盖销毁」形成对照。状态从「机制 ✅ / 生产触发 ⓘ」升为 **「机制 ✅ + 生产 2/2 成功 ✅」** |
| **N17** | **策略 B 的「`located` → 1 次构建、无回退」会在该次构建失败时直接丢掉这条 crash** | ✅ W2：OSV-2020-2183 静态 check `located`、pin=`9ba29ef1`(depth1) → 该格**构建失败**（N16 网络）→ walk-back depth2 `71dd7e51` **构建成功并复现**（`walkback_depth_actual=2`、tier=`strict`）。按策略 B 这条 strict **不存在** | W1 的成本模型只数**构建次数**、没考虑**构建失败率**（本轮钉版 **5/21=23.8%** 失败）→ 🅗 策略 B 须加「构建失败 → 退回 walk-back 下一格」；按本轮失败率，6 条 located 里 1 条(17%)会白丢 |
| **N18** | **N4 的还原命令 `git checkout HEAD -- projects/<p>` 不够**：era-retry 的 `git checkout <era> projects/<p>`（`build_specified_commit.py:268`）会把「**era commit 里有、HEAD 里没有**」的文件**加进 index**（状态 `A`），而 `checkout HEAD -- <path>` 对 HEAD 中不存在的路径无从恢复 → 文件残留且**已 staged** | ✅ W3 实测：harfbuzz 的 era `e32b716754` 含 `hb-draw-fuzzer.options`/`hb-set-fuzzer.options`、HEAD 无 → 两文件以 `A` 残留 → **gate 条件② 判脏 → ② ABORT**。修法 `git restore --source=HEAD --staged --worktree` + `git clean -fdq` 实测还原后 `status --porcelain` = 空 | ⚠ **W1 当时只验了「不动 `infra/`」，没验「era 新增文件能否被还原」= 验证覆盖不全的典型**。② `restore_projects()` 已改；连带发现 ⑥ 会把 gate ABORT 当成「无钉版计划」继续跑（= 在污染树上继续构建，正是 gate 要防的）→ 已改为 rc=2 抛异常整轮停 |
| **N19** | **`ninja: error: unknown target '<path>'` = build.sh 与上游 commit 版本错配**（当前 `projects/<p>/build.sh` 要求一个该老 commit 里不存在的 target），且 **era 自愈救不了** | ✅ W3 实测：harfbuzz **6 次钉版全部**栽在 `unknown target 'test/fuzzing/hb-raster-fuzzer'`，日志里 era-retry **确实触发了**（`Retrying on earlier OSS-Fuzz commit 242b6ae6`）仍以同一错误失败 → era 侧的 build.sh 也要这个 target | 分类器新增 `buildscript_mismatch` 类（排在 `compile_error` 前）；同时把 `-Werror` 归入 `toolchain_drift`。⚠ 还发现**分类器读日志截断到末 400KB 会切掉首试的真错**（harfbuzz 日志 478,431 B，首试的 ninja 错在前、era-retry 的 `-Werror` 在后 → 被误判成 toolchain_drift）→ 改为读整份（8MB 上限）。自测 9/9 |
| **N20** | **归档裁剪的「保护集」若只按「同 osv_id 最新一行」算，一条坏行就能导致 verified 二进制被不可逆删除** | ✅ W3 实测事故：⑤ 的 scope bug（见 §4.17 bug #1）曾把 W2 的 OSV-2020-2183/-2184/-2251/-1663（**2 strict + 2 loose**）覆盖成 `not_run`/tier=null → 那一轮裁剪据此判「无人引用」→ **删掉 4 个 verified 归档目录**。记录本身仍有效（tier/score 是二进制还在时算的），但二进制要重建 | 保护集改为**扫 dataset 全部行**（append-only 的历史复现记录表里任何一行标了 verified 就说明该二进制曾产出过被交付的结论）→ 一律保护 |
| **N21** | **§1.7 的负对照判据对「钉版老二进制」前提不成立**：老版本里可能**同时活着别的 bug**，拿别条 crash 的 testcase 去跑会真崩 | ✅ W3 实测：用 c-blosc2@`886d4c9b`（commit 日期 **2022-06-09**）跑 OSV-2021-1791 的 testcase → `Heap-buffer-overflow READ 61951`；而 OSV-2021-1791 的窗口是 `introduced 2021-02-18` → `fixed 2022-06-13`，**2022-06-09 正落在窗口内** → 该 bug 在这个版本里本来就该崩 | **不是仪器坏，是对照设计错**：判据要加**版本感知**——只用「其漏洞窗口**不含**被测 commit」的其他 crash 作对照，或改用 HEAD 二进制。本轮其余 7 项对照（随机 256B ×2、别项目 testcase ×2、同项目其他 3 条）全 none ✅；这 1 条恰是**另一个 bug 的真阳性**，反证流水线能在正确版本上找到正确的 bug |
| **N22** | **架构不匹配不只是掉档，是会撞上「另一个 bug」并给出误导性结论** | ✅ W4 配对 n=3（同 commit、同 testcase、只换架构）：OSV-2020-2251@`8cb8eb2145` 在 **x86_64** 下崩成 `Heap-use-after-free READ 32`、帧 `MemcmpInterceptorCommon/memcmp/LooseMemeq/free/…` → 判 **loose**（看着像「复现了另一个 bug」）；同 commit 用 **i386**（= 该 crash `job_type` 的架构）建 → `Heap-buffer-overflow READ 1`（**正是期望类型**）、帧 `blosc_run_decompression_with_context/blosc2_decompress_ctx/frame_decompress_chunk` 与 ground truth **逐字相同** → **strict**。另 2 条（OSV-2021-1710 / OSV-2022-55）x86_64 把 `ndlz_decompress` **内联掉** → 少一帧 → medium，i386 保留 → **strict** | ⑥ 新增 `--match-job-arch`（**默认开**）：按 crash 自己的 `job_arch` 构建。是**替换不是新增**（i386 上报的 crash 本来也要建一次）→ 常规情况不多花构建。**未**因此把架构加成通用维度（① schema 不变），只复用 W3 已铺好的 ② 缓存键/归档路径分量。**这条把 N8 的故事彻底改写**：不是「i386 不可复现」，也不是「x86_64 够用」，而是「**架构错配会污染归因**」 |
| **N23** | **N19 有两种形态**，只查「ninja 目标缺失」会漏掉第二种 | ✅ W4：形态① harfbuzz `ninja: error: unknown target 'test/fuzzing/hb-raster-fuzzer'`（6/6）；形态② **pcapplusplus build.sh 第 22 行整行就是 `$SRC/PcapPlusPlus/Tests/Fuzzers/ossfuzz.sh`**（被执行的脚本在该 commit 不存在）→ `error: Tests/Fuzzers/ossfuzz.sh: No such file or directory`（3/3） | 预检加精确的 `SCRIPT_RE`（`$SRC/`、`bash`、`sh`、`source`、行首 `./` 之后的 `.sh/.py/.pl`）+ 分类器加该模式 → 自测 **10/10**。**⚠ 试过把候选放宽成「任何路径」：会把 `www.apache.org/licenses/LICENSE-2.0`、`$OUT/*.zip`、`.libs/libpcre2-8.a`、`bin/bash` 全抓进来 → 必然 404 → 误报会跳过本能成功的构建，比漏报更糟** → 回到窄口径 + 精确脚本模式（harfbuzz 6/6、pcapplusplus 3/3、已知能建的 6 条 **0 误报**） |
| **N24** | **预检自身可能比它省下的构建更贵** | ✅ W4 实测：`path_exists_at` 对**已有扩展名**的路径也把 15 个源码扩展名全试一遍 → harfbuzz 单条预检 **64.2s**；扩展候选集后验证脚本 **>15min 未返回** | 有扩展名只查 1 次、无扩展名（ninja target）只试 4 个最可能的 → **64.2s → 22.6s**；另加 `MAX_PRECHECK_PATHS=40` 成本护栏。对照：一次白跑的构建 90–320s → 预检仍划算，但**必须核算预检自己的成本**（「省时间的优化反而更慢」，与 W3 的 era 混淆变量同类教训） |
| **N25** | **构建日志按 `{project}_{san}_{commit[:12]}.log` 命名 + `open(…,"w")` 无条件截断 → 重跑同 commit 会静默覆盖上一次的失败日志**，而结论仍引用它 | ✅ W5 实证：为验 N16 去翻 W2 那条网络失败日志 → `GnuTLS/RPC failed` 在 `artifacts/logs/build/` **0 命中**；`c-blosc2_address_9ba29ef1584b.log` 现在是 2026-09-10 18:00 那次**成功**构建的内容，而 `build_records.jsonl` 里同 key 两条（`fail_pinned/compile_error` ts 1788940358 → `ok` ts 1789034514）**都指向同一个路径**，本文 §4.5 曾引它作 N16 证据 → **该引用已不可复算** | `rotate_existing_log()` 挂在 `run_cmd` 的**唯一写盘点**：写之前若同名文件存在 → 改名保留（UTC 时间戳后缀，同秒加序号），**永不销毁**；自测 7 项（含端到端跑两次 `run_cmd` → 第一次内容仍可在轮转文件里找到）。与 **N20**（归档侧误删）同根因：**派生产物被后来的运行覆盖，而结论仍引用它** |
| **N26** | **正典 manifest 也会被后一次运行静默削弱**：`--only-osv 3 条` 配**默认 `--out`** 会把全局 manifest **3,790 行覆盖成 3 行**；不带 `--static-check` 的全量重跑会把 `fixed_real` 刷成 0 | ✅ W5：`write_outputs()` 是唯一写盘点，此前无条件 `open(…,"w")`。**生产实证**：`--limit 5 --out artifacts/repro_manifest.jsonl` 被护栏拦下（退出 **4**、文件仍 3,790 行） | `overwrite_guard(old,new)` 纯函数：**覆盖面缩水**或**交集行上任一强度字段由有值变空**（`repo_path`/`fixed_real`/`static_check_verdict`（`skipped` 视为空）/`degenerate_resolved`）→ 拒写并点明字段；`--force-overwrite` 才写且记 `manifest_overwrite_audit.jsonl`。只在**交集**上比强度 → 子集运行/新增行不误报。自测 14 项（含负对照：完全相同 → 放行，证明不是恒拒） |
| **N27** | **预检自己会误报、也会漏检**——它是为「别白跑构建」加的，但三条路径让它反过来**制造**错误决策 | ✅ W5 三例：①`sha=None` → `_raw_url` 插值出 `raw/None/<path>` → 必然 404 → 被判**确定缺失**（`checked=0` 却报 `missing`），违反自身契约「无法判定时一律放行」；②候选保留 `./` 前缀 → 假 404 → 误报；③`SCRIPT_RE` 要求脚本路径紧跟解释器 → `bash -x ./ndpi/tests/ossfuzz.sh` **整条漏检** | 三处全 TDD 修（自测 15 项）+ **已知答案回归固化**（harfbuzz 4/4、pcapplusplus 3/3、libspng 4/4 = **11 条真报**；6 个项目 **23 个已成功 commit → 误报 0**）。③ 只放宽「破折号 flag」一种形态，**不**放宽成任意 token（W4 教训：宽口径 → 误报比漏报更糟）。**教训：护栏本身也要有已知答案回归**，否则「修一个误报、放跑一个真报」看不出来 |
| **N28** | **老 commit 构建失败的主导模式之一是「第三方依赖 URL 已死」，而预检在构造上预测不到它** | ✅ W5 实测 libspng 钉版 **1/19 = 5%**：`dead_external_url` **11 次**（日志 `Proxy request sent, awaiting response... 404 Not Found`，wget 的依赖包已死）+ `buildscript_mismatch` 6 次 + `toolchain_drift` 1 次。预检只查**仓库内路径**，外链死活它无从判断 | ① 可构建率外推**必须**把这一类算进去（此前 85.1% 的便利样本里没有它，因为那些项目都不下载外部依赖）；② 离线筛选把「build.sh/Dockerfile 里的**第三方**外链数」列为风险因子（区分指向项目自己的仓库 vs 第三方）；③ 顺带发现 `build_error_detail` 抓的是泛泛的 `ERROR:helper:Building fuzzers failed.` 而不是 404 那行 → **按根因分组会失真**（未修，记为待办） |
| **N29** | **「查不了」必须与「查过没问题」分级**，否则离线筛选会把**无证据**的项目排到第一 | ✅ W5 实例：修 N27③ 之前，`ndpi` 以「池 142 / 0 外链 / 错配 **0/3**」排推荐序**第 1**；而那个 `0/3` 的真实含义是 `no_candidate_paths`（**一条路径都没查**）。直接查其 build.sh 执行的 `tests/ossfuzz.sh` → **3/3 个 commit 全部缺失** = 0/N 灾难。发现靠的是**手工 `cat build.sh`**，不是筛选表 | 筛选表改**三级证据**输出（✅真查过 N 个路径 0 缺失 / ⓘ无证据并附原因 `no_candidate_paths`·`undecidable`·`no_sha` / ⛔全中出局），排序对「无证据」折半 → ndpi 从第 1 变**出局**，推荐改为 **libredwg**。**这与 W4 的「变量遮蔽让一整段验证静默跳过」、以及本轮 [A] 节 pcapplusplus 被静默跳过是同一个病**：缺证据与证据为负，必须在输出里长得不一样 |
| **N30** | **新加的回收路径绕过了老路径的保护集** → 删掉了**已交付**的证据 | ✅ W5 实测事故：`purge_archives`（复现完立即删）没查 dataset 保护集，而**钉到同一 commit 的 crash 共享同一个归档目录** → `purge_on_verify:OSV-2021-1676` 顺手删掉 **OSV-2021-1663 / OSV-2021-1712**（都是 `w4-stratA` 的 **strict** 行、W4 已交付）的归档，且那两行**没有任何标记** → 无声悬空指针。对照：`prune_archive`（W3 轮末裁剪）删掉的 verified 证据 = **0 条**，因为它**有**保护集 + `pinned_commit` 交叉校验 | `purge_archives` 加 `dataset_path` 保护集（已落盘 verified 行引用的目录一律保住）、⑥ **必传**；TDD 4 项含「不传就无保护」的对照。**证据已恢复**：重建后 **5/5 文件 sha256 与记录逐字节一致**（把 W4 的 bit 确定性从 4 个 commit 扩到 5 个）。**教训：给一个已有保护机制的系统加第二条删除路径时，保护集必须跟着走**——否则新路径就是绕过所有护栏的后门 |
| **N31** | **筛选只量「可构建性风险」、不量「构建成本」→ 会把不可行的项目排到第 1**；且**预检通过是必要不充分条件** | ✅ W5 两例：① **libredwg** 在 v1 筛选里排**第 1**（池 68、0 第三方外链、预检真查 3 路径 0 缺失 —— 全部正确），但 `build.sh:40` 的 `make check-prep -C test/unit-testing/ -j16` 要编 ~100 个 **ASAN 单测二进制**（fuzzer 一个都不需要）→ 链接期 `No space left on device`，且单次构建 **30min+** → 68 条 ≈ **40 小时**，**不可行**；② **opensc** 预检 ✅、外链仅 1、repo 只 25MB → 离线维度全判可行，实测 **0/3**（`-Werror` 工具链漂移） | 筛选升级 v2：新增**构建体量**维度（`build.sh` 是否编测试套件，用**精确**模式 `make check|check-prep|test`/`make -C *test`/`ctest`/`ninja test` —— v1 用 `/tests?/` 太松，会把 opensc 的 `$SRC/opensc/src/tests/fuzzing/`（fuzzer 源码本身）误判成测试套件）+ repo MB 作耗时代理（校准：hunspell 10MB=快 / libredwg 93MB=30min+ / radare2 204MB / php 640MB）。**并确立流程：任何新项目先跑 3 条探针（~10min）再决定整池** —— opensc 探针 10.5min 就拦住了 79 条 × 3min ≈ **4 小时**的白跑 |
| **N32** | **「crash 年份越新 → 老代码越兼容新工具链 → 越可构建」这个直觉被实测否证** | ✅ W5 反例成对：**libtsm** 池年份中位 **2017**、2023+ 仅 **9%** → 可构建率 **100%**（5/5）；**pcapplusplus** 中位 **2023**、2023+ 占 **53%** → **0/3**。libredwg（中位 2023、57%）同样 0/1 | 年份**不作预测因子**，v2 只当描述性信息打印。真正有区分力的是**项目自身的构建方式与外部依赖**（是否 wget 第三方包、是否编测试套件、是否 `-Werror` 洁净）。与 W1 策略模型、W3 的 N8、W4 的 N24 同类：**先验排序必须让位于实测**——这已是本项目第 **5** 次「模型输给实测」 |
| **N33** | **era-retry 有一道结构性天花板**：当当期 Dockerfile 钉死了后来被发行版**移除**的包名时，官方兜底必然失败，与项目本身无关 | ✅ W5 openh264 实证：首试用 HEAD Dockerfile（`libstdc++-9-dev`）镜像没问题、败在编译；era-retry 切到当期 Dockerfile（`libstdc++-5-dev`）→ `E: Package 'libstdc++-5-dev' has no installation candidate`（focal 已下架）→ **两段都死**。era-retry 是整套流水线对付「当前构建文件 vs 老 commit 错配」的**唯一官方兜底**（§1.5 的 era 学习也围绕它） | 影响面**不止 openh264**：未试池 2,984 条大多来自 2020–2021，那时 Dockerfile 普遍钉 `libstdc++-5/6/7-dev`、老 `python3.x`、已下架镜像源 → 同一道墙会反复出现；这也解释了 W5 的失败为何**集中**而非随机（harfbuzz 0/7 是 era 侧 build.sh 也要那个 target）。**可做未做**：把「era Dockerfile 是否引用已下架包」变成**离线可判**的筛选维度（读当期 Dockerfile 的 `apt-get install` 列表 × `apt-cache policy`）→ 建镜像**之前**就能否掉，省 2.9GB + 探针时间 ｜ **[W5 已实现离线预测器]** `preflight/screen/w5_predict_dockerfile_drift.py`：取 era Dockerfile（GitHub API `path`+`until`）→ 抽 `apt-get install` 包名（纯函数，自测 7 项）→ 在**本地 base-builder** 里跑**一次** `apt-cache policy` 批量查可安装性。**已知答案校验 1 真阳 / 5 真阴 / 0 假阳 / 0 假阴**（openh264 判 ⛔ 对上实测 0/3；c-blosc2·hunspell·pcre2 判 ✅ 对上 92–100%；flatbuffers·libspng 判 ✅ 也**正确**——它们死因不在此维）。成本 = 每项目 1–2 次 HTTP + **全部共用 1 次 docker run**，对比建镜像 2.3–2.9GB + 探针 10–30min。详见 §4.50 |
| **N34** | **预检的第三个盲点：C++ `#include`** —— fuzzer 源码由 Dockerfile `COPY` 进 `$SRC`（内容取自 HEAD），却要编译老 commit 的树 → include 的头文件可能不存在，而**路径存在性检查在构造上看不到** | ✅ W5 openh264：`/src/decoder_fuzzer.cpp:28:10: fatal error: 'codec_def.h' file not found`。三个盲点至此集齐（全在 W5 发现）：① `bash -x ./a/b.sh` 的 flag 间隔（N27③，**已修**）② libxml2 那种**全文只有一行裸脚本**的 build.sh（未修）③ **C++ `#include`**（本条） | ① 分类器已加形态③模式（`fatal error: '<X>' file not found` → `buildscript_mismatch`）+ **首试段优先**（以 `Retrying on earlier OSS-Fuzz commit` 切分，先分类首试段）→ openh264 从 `dockerfile_drift`+detail`OpenPACE…`（**错**）变成 `buildscript_mismatch`+detail 指向 `codec_def.h`（**对**）；自测 18→**23 项**，含「首试段无错、只有 era 段有错」的对照。② 影响面已核查：两类**同属** `DETERMINISTIC_FAIL` → **早停计数行为不变**。③ **结论：预检通过是必要不充分条件，探针不可省**；若要修盲点③，可抓 `$SRC/*.cpp` 的相对 `#include` 再查该 commit 树（成本同量级：raw 端点、0 API 0 clone） ｜ **[W5 盲点③已实现并校验]** `parse_fuzzer_includes()` + `include_candidates()` + `precheck_includes()`（TDD，自测 22 项）。**已知答案对上真凶**：openh264@`58576925544e` → 离线报缺 `codec_def.h`/`codec_app_def.h`/`codec_api.h`，而真实构建日志正是 `fatal error: 'codec_def.h' file not found`。**但适用边界比预想窄**：8 个候选**全部** `no_sources`（它们的 Dockerfile 不把 fuzzer 源码 COPY 进 `$SRC`，而是直接编仓库里的）→ **0 个新增淘汰**；筛选表按 N29 显示「不适用」而非 `0/1`。成本 20–24 次 HTTP/项目 → **只做筛选、不接进 ② 的每次构建前预检**（N24 教训） |
| **N35** | **非 github/gitlab 的 `repo_url` 让 walk-back「零构建」静默失败**：`resolve_commit_meta()` 走 `.patch` 端点、只认 github/gitlab，其余 `return None` → `plan_pinned()` 得 `(d, None, …)` → **walk-back 在建之前就中止**，表现为「0 次构建、0.0min」而非报错 | ✅ **实测爆炸半径：可执行池 3,136 条里 542 条（17.3%）/ 32 个项目**（ghostscript 197、matio 46、kimageformats 39、mupdf 37、libhevc 24…）。已跑的 153 条里 11 条非 github 之所以能跑，是因为 **8 条 libtsm 全是 `commit_source=head`**（从不需要 `fixed~d`）→ **此前「钉版 + 非 github」的组合 100% 死在这一行** | ✅ W5 修：`REPO_MIRRORS` + `mirror_for()`（strip/小写/**循环**剥 `.git` 与尾斜杠）接进 `resolve_commit_meta()` 与 `_raw_url()`。**安全性双证**：① git SHA 内容寻址、镜像无法伪造；② ✅ GitHub API 与**本地全量克隆**两种独立方法对 `7f82c015…~1` 都给 `813144d395bb`，逐字一致。自测 24 项（含前缀陷阱、同主机不同仓库不许误命中） |
| **N36** | **预检第 4 个盲点：raw 端点看不见 submodule 内部** → 对 `thirdparty/harfbuzz/src/hb-subset-cff1.cc` 必然 404 → 误判 `buildscript_mismatch` → **一次挡死 mupdf 全部 37 条** | ✅ 实测同一 commit `7f82c015`：`source/fitz/document.c` **200**、`include/mupdf/fitz.h` **200**、submodule 内那条 **404**；`.gitmodules` 列了 **10 个** submodule，而 `build.sh:19` 正 `sed -i` 它，容器 `git clone --recursive` → **该文件必然存在 = 纯误报** | ✅ W5 修：`submodule_paths()` 拉 `.gitmodules` 解析 `path=`（进程内缓存）→ 落在 submodule 前缀下者记 `undecidable` + `submodule_skipped` 留痕并**放行**（同 N27①/N29 口径）。前缀判据 `c == sm or c.startswith(sm + "/")` 防 `harfbuzz` 吞 `harfbuzz2`。**回归：11 真报仍全中、6 个可构建项目误报 0** |
| **N37** | 构建源也换镜像（`--repo_url`）——**实现正确但对 mupdf 实测无效** | ✅ 诊断到进程级：`build_specified_commit.py` 阻塞在子进程 `git remote update`，其 `cwd=/tmp/…/src/mupdf`、`origin=git://git.ghostscript.com/mupdf.git`（**不是镜像**）、`is-shallow=true`。该目录来自 `docker run … cp -r -p /src /out`，即**镜像内 Dockerfile step 4 预烘焙的克隆**；`--repo_path /src/mupdf` 指向它 → **我传的 `--repo_url` 不参与该仓库的 fetch** | ✅ W5 已实现并留痕 `repo_url_build`（成功/失败路径都记）。**保留**：对「RepoManager 需自行克隆」的项目仍有效，且映射表只有 mupdf 一项 → 不影响其它项目 |
| **N38** | **第四类结构性天花板：镜像内预烘焙的 shallow 克隆 + 慢速上游协议（`git://`）→ 钉版构建必然超时**，且**修复被两条硬约束正面挡住**（改 Dockerfile 违反「不改 Dockerfile/build.sh」；改 `infra/` 违反 md5 固定 `f5092d0a3f2a6909`） | ✅ 实测单价：`git://` 全量克隆 **>15min 未完**、GitHub 镜像 **51s / 211MB**；单格 **`# TIMEOUT after 3600s`**、3 格 **240.2min / 0 复现**。镜像 `/src` = 585MB / 13,351 文件（c-blosc2 61MB / 1,975）但**非主因**——临时目录 19min 内 663M→730M 后**停住**，进程阻塞在 `git remote update` 而非拷贝。**成本外推：37 条 × ≤3 格 × 3,600s = ≤111 小时且每格 0 信息量** → 判 mupdf 不可行（比 libredwg 30min/次更差） | ⚠ **离线判不了**（要先建 3.11GB 镜像 + 烧 3,600s 才知道）。可提取的**廉价前置信号**（未实现）：`repo_url` scheme 为 `git://` + Dockerfile 用 `--depth 1` 预克隆 → 高度可疑 |
| **N39** | **`normalize_one_frame` 不剥 C++ 参数签名 → C++ 项目的帧必然全失配**：R（`crash_state_recovered`）是**裸函数名**，O（ASAN stderr）带**完整 demangle 签名**；权威实现剥了 `.part.NN`/`auto`/`$_N`/`::operator()`，**唯独没剥 `(...)`** | ✅ 实测 `OSV-2022-1004`（hunspell，判 medium）三帧**函数名与顺序全对得上**、只差签名 → `score_subseq=0.0`。**106 条 verified 全部重算：17 条 medium 应为 strict，全是 hunspell** → tier 应从 47/36 变 **64 strict / 19 medium**。⚠ **并推翻 §4.44 的结论**「hunspell 档位画像与 c-blosc2 明显不同」—— 那是本缺口的假象 | ⚠ **未修，待定**。建议改 `repro_common.normalize_observed()`（O 侧），**不动**权威实现（避免污染 W1 的 R2 聚类结论）。代价：丢重载区分能力，但 **R 侧本来就没有签名**、该信息从来不存在。**成本≈0**：observations 全在盘上，只需重跑 ④⑤、无需任何构建；medium→strict 是**升档**，⑤ 单调性护栏本就允许 |
| **N40** | **`logs/reproduce/` 一直在被静默覆盖**：`run_once()` 用 `open(log_path,"w")` 无条件截断，而日志名只由 `<osv_id>[_rN]` 决定（`_r{i}` 只管**同轮内重试**、跨轮次不管）→ **N25 只修了 build 侧** | ✅ 实证：跑过多轮的 crash **113 条**（最多 6 行），盘上只剩 1 份日志的 **110 条**；`logs/build/` 有 **71** 个轮转文件、`logs/reproduce/` 有 **0** 个 | ✅ W5 已修：`rotate_existing_log` 移进 `repro_common` 作**单一权威实现**（② 改别名引用 → 不分叉），`run_once()` 写盘前先轮转。自测新增 **T1b 7 项**。⚠ **残留局限**：轮转保住字节，但旧复现记录表行的 `raw_log_path` 仍指原名（=最新那次内容）→ 彻底修法是**日志名带 run_id**，而 `run_id` 在 ③ 作用域不可用（只有 ⑥ 知道），列 §5 待办 |
| **N41** | **归档保护集用字符串（`normpath`）比对 → 路径一旦有别名就静默失配**：`prune_archive()` 与 `purge_archives()` 都是；后者正是 **N30 事故**的当事人。归档区改名或经符号链接访问 → 保护集为空 → **所有 verified 归档被判「无人引用」而删掉**。与 N20/N30 同形态、不同触发方式（不是绕过保护集，而是保护集失配） | ✅ 加符号链接视图前**主动排查**发现（不是事后事故）。已有安全网确实兜住：W4 Phase1a(ii) 那个**用 `pinned_commit` 独立重算**的交叉校验在 `M>0` 时**拒绝执行**；但那会让 `purge-on-verify` 一直误拒 | ✅ W5 已修：两侧共 **6 处**改 `os.path.realpath`。验证四件：①「复现记录表记符号链接、盘上是真实路径」**仍被保护**，且无关目录照样能删（非恒拒）；② dry-run `保留 24 / 将删 0 / M=0`；③ **建完视图后**再 dry-run 仍 `将删 0`；④ 18 套 **249 项**全绿、审计 0 红线 |
| **N42** | **Gitiles（googlesource）无法解析 `fixed~d`**：N35 的镜像映射只救了 mupdf 一个；可执行池里还有 **112 条**属 googlesource 系（android 58 · skia 18 · chromium 17 · aomedia 14 · boringssl 4 · code 1）→ `classify_repo` 判 `other` → `resolve_commit_meta` 返回 None → walk-back 零构建 | ✅ 但 **Gitiles 自带 JSON 端点且直接给 `parents`**（比 GitHub `.patch` 信息更全）→ **不需要任何镜像**。实现要点：剥 XSSI 前缀 `)]}'`；`parents` 是**字符串数组**（我一开始按对象数组解析直接 TypeError）；Gitiles **无 rev 语法** → `~d` 须逐级走 `parents[0]`；`author.time` 是 RFC2822。`_raw_url` 一并支持 `?format=TEXT` → **`path_exists_at`/`submodule_paths` 对 googlesource 也可判**（从 ⓘ 升为可预检） | ✅ W5 已实现 + 自测 **48 项**。**已知答案**：`libhevc 67e394c9…~1 = 130f5f1fc107`（与原始 JSON `parents[0]` 逐字一致）、`~2`/`~3` 亦对；该样例还是 **merge commit（2 parent）** → 取 `parents[0]` 与 git 语义一致。`path_exists_at` 对**核实过的真实树** **6/6** |
| **N43** | **分类器漏识别 `ValueError: Commit … does not exist in current branch`** → 落到 `compile_error`；**且 `commit_not_found` 被错误地列进 `DETERMINISTIC_FAIL`**（其成立条件是「哪一个 commit」，不是「同项目同 era 必然同样失败」）→ 连续 2 次就封整个项目 | ✅ 实测 libavc 整池：`⛔ [早停] 已连续 2 次 compile_error` → **早停跳过 33 条**，而**同一轮已试 10 条里 7 条复现成功**、github(29) 与 android.googlesource(14) **两种源都出过复现** = 直接反证 | ✅ W5 已修两处：① 补 `does not exist in current branch` 与 `ValueError: Commit <sha>` 两个形态；② 把 `commit_not_found` **移出** `DETERMINISTIC_FAIL`（与 `network_fetch` 同等）。自测 **+6 项含 3 个负对照**（真 `compile_error` 仍须归类正确且**仍计入**早停）。**重跑 33 条 → 29 复现（88%）、`早停跳过 0 条`** |
| **N44** | **错误串双重前缀 `httphttp403`**：`rc.http_get` 返回的 code **本身已带 `http`**（如 `http404`），而 `resolve_commit_meta`/`gitiles_commit` 又套一层 `f"http{code}"` | ✅ 不是假想：mupdf 探针时 GitHub 那条路就印过 `err=httphttp403`。危害是**诊断字符串误导**，且任何按 `http403` 匹配的下游都会失配 | ✅ W5 已修：新增 `_http_err(code)` 归一（已带前缀则不重复加），替换 3 处 |
| **N45** | 🔴 **⑤ 的连接键优先级反了** → `binary_dir`/`binary_sha256`/`pinned_commit` 三字段取自 `b_by_osv`（**后者覆盖前者 = 该 OSV 最后一次构建**），而 walk-back 对 loose「继续下探」→ 最后一格**不是崩的那格**。✅ 实测 2 条受害（`OSV-2020-1016` 复现记录表记 `dca55210` 而真相是 `b7d25a74`；`OSV-2023-48` 记 `bb0f31cb` 而真相是 `e14ee149`），归档里**没有自己的 driver** → 按 INFO.txt 重放得 `No such file or directory`、**exit=127**，直接违反 §0.3「verified = 可重放」。修：先按 observation 自己的 `binary_dir` 反查、查不到才退回 osv_id；再用修好的流水线重跑这 2 条（4 构建 / 5.1min），**实测重放 exit=1 + ASan ABRT** 收尾 | ✅ 已修 |
| **N46** | 🔴 **libFuzzer 超时被当成复现** → `classify()` 的 `evidence` 含 `engine_summary`+`dedup_token`，而 timeout 的 DEDUP_TOKEN 全是**引擎自身告警回调帧**（`__sanitizer_print_stack_trace--fuzzer::PrintStackTrace()--fuzzer::Fuzzer::AlarmCallback()`），无一个目标帧。✅ 实测 `OSV-2023-1206`（期望 `Heap-buffer-overflow WRITE`，实测 `timeout`、`score_subseq=0.0`、exit=70）被记成 **loose** → 复现数虚高 1。修三处：⑥ `classify` 加 `non_crash`（∈`NON_CRASH_DIAGNOSTICS` 且无 sanitizer 报告 → 不算崩）、④ `verify_one` 同判据放分级前（**重跑 ④⑤ 即纠正历史**）、⑤ 不得盲抄过期 `reproduced_any`。⚠ 集合不含空串、不排除 `deadly signal`。**复现 152 → 151** | ✅ 已修 |
| **N47** | ⓘ **`exit_code` 不可作判崩依据** → 3 条 libwebp（2 strict + 1 medium）复现记录表 `exit_code=0`，report 里却是真 `AddressSanitizer: heap-buffer-overflow`（`AddGreenToBlueAndRed_AVX2` / `WebPDataCopy`）。**⑥ 按报告内容判崩是正确设计**：若按退出码判，**libwebp 会是 0/10**。字段本身不可靠 → 审计作软性提示。🅗 exit=0 成因未查明（target 是 `advanced_api_fuzzer@AdvancedApi.AdvancedApiTest` 这种 gtest 形态，疑子进程崩、父进程正常退出）；未深挖，因判崩不依赖它 | ✅ 已记录 |
| **N48** | 🔴 **审计「有牙无齿」** → `w5_audit_delivery.py` 只查 `binary_dir` 是不是**目录**，于是 N45/N46 躺在里面却报「0 条红线违反」。补 `[4b]「可重放」的实质检验` 3 条红线：`binary_sha256` 必须含自己的 `fuzz_target`（**复现记录表自证**）· 盘上 `binary_dir/<fuzz_target>` 必须可执行 · `observed_crash_type` 不得 ∈ `NON_CRASH_DIAGNOSTICS`（从 `repro_common` 导入，**不复制一份**）。**补牙后立刻自证有效：先报 4 条红线，修完才归零** | ✅ 已修 |
| **N49** | 🟡 **交付视图把「整棵构建树」当 `binary` 暴露** → 一个 OSV 下面出现 **1～17 个可执行文件**（5 个的最多，43 个目录）。归档层按 `(project,san,commit)` 存整棵 `build/out/` 是**正确设计**（W2 教训：只存请求的 target → pcre2 8 条 `target_not_in_archive`），错在交付层直接暴露。改：`binary` = **单个 driver 文件**、`out/` = 整棵树（driver 动态链接 `libclang_rt.*.so`、要读 `.dict`/`.options`，**只给 driver 会重放失败**）、INFO.txt 顶部写明；driver 缺失写 `DRIVER_MISSING.txt`，**绝不留断链**。✅ 151 条目 binary 单文件链接 151 / out 151 / 断链 0 | ✅ 已修 |
| **⚠ 本轮 4 个缺陷无一是自测或审计发现的** | 全部源于**用户看着交付物问了一个结构问题**（「一个 OSV 为什么有这么多二进制」）。→ 交付视图不只是产物，**它是最有效的评审界面**；审计判据必须落在「消费者实际会做的动作」（能不能重放）而非「字段是否非空」。另：验证命令本身也要被验证 —— 我第一次实测重放时把 docker 输出接进 `grep \| head`，`head` 提前关管道 + `&&` 链冲掉 `PIPESTATUS` → 读到假的「退出码 0」，**不带管道直跑才是 1** | ✅ 教训 |
| **N50** | 🟡 **N49 没解决问题**：`binary` 收窄成单文件了，却仍留 `out/` 指向整棵构建树 → 打开 OSV 文件夹照样看到 **2～17 个可执行文件**（同一次构建的**兄弟 fuzz target**，与这条 crash 无关；151 条里 132 条含 1,497 个无用文件）。根因分层：归档层按 `(project,san,commit)` 存整棵 `build/out/` 是**对的**（W2 教训：pcre2 8 条 `target_not_in_archive`），**错在交付层直接暴露**。改为只放**精确最小重放包** → ✅ **151/151 每条恰好 1 个 ELF**；包内文件数 1→128 条、2→19、3→4；1555MB 走**硬链接 → 额外 0 字节** | ✅ 已修 |
| **⭐ 推翻我自己写进文档的一条结论** | N49 注释里写过「**只给 driver 会重放失败**（动态链接 `libclang_rt.*.so`、要读 `.dict`）」。本轮做实验：`ldd` → **0 个 not found、无 `libclang_rt.*.so`**（ASan/MSan **静态链入**）；符号化也不依赖归档里的 `llvm-symbolizer`；✅ **14 个项目×sanitizer 组合逐条真跑「只放 driver」全部崩**（hunspell 原归档 42 个文件 → 只放 1 个照样崩，含 i386、含 MSAN）。那条结论是**从 W2 flatbuffers 缺 `.bfbs` 的个案过度泛化**来的，写进文档后从未被检验，还**把 N49 的设计带偏了** | ✅ 已推翻 |
| **N47 悬案已破** | libwebp 的 `advanced_api_fuzzer@AdvancedApi.AdvancedApiTest` **不是 ELF，是 shell 包装脚本**，最后一行是 `chmod -x $this_dir/advanced_api_fuzzer` → **脚本退出码取的是 chmod 的 0**，子进程 ASan 崩了也返回 0。上一轮记为 🅗 未查明，本轮 ✅ 定性。推论：包装脚本引用的真 ELF 必须一起打包（否则 `not found`），且**判决必须按报告内容而非退出码** | ✅ 已定性 |
| **N51** | 🔴 **交付的 `replay.sh` 必须照抄复现记录表 `runtime_limits`** → 首版漏了 `-rss_limit_mb=2560 -timeout=25`，libFuzzer 用默认 2048MB 上限 → ✅ 实测 2 条 c-blosc2（`OSV-2021-464`/`OSV-2021-366`，复现记录表 **tier=strict**、`score_subseq=1.0`、类型完全对得上）在交付文件夹里重放变成 `SUMMARY: libFuzzer: out-of-memory`、容器 exit=71；补参数后**各 2/2 稳定复现**。**原则：交付的重放命令若与「产出那份 report 的那次实验」不是同一个实验，比不给命令更糟** | ✅ 已修 |
| **N52** | ⭐ **首次全量重放验收 151/151 = 100%** → 此前「二进制在盘」只验到「**目录存在**」（N45 就这样漏网），最多加验「driver 文件存在」，**从未真跑过**。本轮逐条执行各自 `replay.sh`（失败重试 3 轮）：**首轮即崩 148 条（98.0%）** · 重试后崩 2 条（`OSV-2023-48`/`OSV-2023-75`，都第 3 次）· 重度 flaky 1 条（`OSV-2023-948` i386，**第 8 次**才崩、**崩溃率 12%**）。结果固化为 `artifacts/replay_verification.json` 并**回写进每个 INFO.txt** | ✅ 已验收 |
| **`OSV-2023-948` 崩时给出的正是**期望**类型** | 复现记录表 tier=loose、期望 `Global-buffer-overflow` 而当次实测 `ABRT`；第 8 次崩时打出 `ERROR: AddressSanitizer: **global-buffer-overflow**`。→ 同一条 crash 可在 `ABRT` 与 `global-buffer-overflow` 之间摆动，**这是「loose 里混着同一 bug 的不同表现」（N15 形态）的第一个直接证据** | ✅ 实测 |
| **打包规则不能用「同前缀」** | ✅ 实测过度包含：`pcre2_fuzzer_1` 会匹配 `pcre2_fuzzer_16` → 产生 1 个 **21 文件**包、3 个**含 2 个 ELF** 的包。改为精确规则（target + 若为脚本则其引用的兄弟 + 同名 `.dict`/`.options`）→ **151/151 恰好 1 个 ELF** | ✅ 已修 |
| **本轮 7 个自身缺陷全部由「真跑一遍全量交付物」抓出** | 包装脚本 chmod 644→`exit=126` · `replay.sh` 漏 `runtime_limits`→2 条 strict 变 OOM · 验收判据用容器退出码→3 条 libwebp 被误判 · 同前缀打包过度包含 · 文档里「只给 driver 会失败」是错的 · `while read` 里 `docker run -i` 抢 stdin→只跑第 1 条 · 判崩 grep 漏 MSan 的 `WARNING:`→4 条真崩被误判。**无一由静态检查发现** | ✅ 教训 |
| **N39** | 🟡 **observed 带 C++ 参数签名、recovered 只有函数名** → 逐字比对必然不等。✅ 实测 **17 条 hunspell** 明明 `crash_type` 一致却拿 `score_subseq=0.0`，被压在 medium。修：新增 `rc.strip_cpp_signature()`，**只挂在 `normalize_observed`（O 侧）末尾**；⚠ **不塞进 `normalize_one_frame`**（那是 AST 逐字提取的权威实现、R/O 共用，改它等于改 ground truth 并与历史分叉）。11 例已知答案全取自复现记录表真实帧（含 `operator()` 的括号是函数名本身、`foo<int>::bar(int)` 的尖括号不受影响、C 帧不受影响）+ 端到端 `OSV-2022-1260`（`score_pos`/`score_subseq` 双双 0.0→1.0）。**先干跑量影响：升档 17、降档 0** → 重跑 ④⑤ 追加更正行，单调性守卫记 17 条升档、0 拒写。**strict 69 → 86**（占复现 45.7% → **57.0%**）、medium 51 → 34 | ✅ 已修 |
| **⚠ N39 不等于「`T_strict` 被验证了」** | 升档的 17 条 `score_subseq` 全是 **1.0**（不是 0<x<1）→ 「复现 ∧ crash_type 一致 ∧ `score_subseq<1.0`」的刻度样本**仍是 3 条**（§4.57.3）。N39 提高的是 strict 的**数量**，没有给 `T_strict=1.0` 这个**阈值本身**提供任何新证据。两件事必须分开说，否则「升档 17 条」会被误读成「阈值被验证」 | ✅ 口径 |
| **18 个候选里 1 条不升是对的** | `OSV-2022-899`：R 首帧是**模板类型名** `std::__1::basic_string<char,…`（原始 crash 崩在其内联处），本次重放该位置是 `strlen` → 子序列确实不成立（`score_pos=0.6667`）。N39 对其它帧生效（`PfxEntry::add(char const*, unsigned long)` → `PfxEntry::add` ✅）。**这条留在 medium 是判据正确工作的证据，不是漏改** | ✅ 实测 |
| **N53** | 🟡 **把「一个 OSV = 一个二进制」写成审计红线** → 这条性质是**用户两次指出**的（§4.58、§4.59），靠人眼看交付目录两次都没守住 → 改由测试守：审计新增 `[4c]`，扫全部条目断言 **ELF 个数 == 1** + 四件齐全 + 断链 0。**牙齿测试**：塞进第二个 ELF → `❌ [硬] 交付视图里有 1 个条目的 ELF 个数 ≠ 1：[('OSV-2016-5', 2)]`；清掉恢复 0 红线。现况 ✅ **151/151 每条恰好 1 个 ELF** | ✅ 已加 |
| **N54** | 🔴 **解析器把输入原样回显成「已解析的 SHA」**：`resolve_commit_meta` 末行 `{"sha": pc.get("sha") or sha, "error": None}` → 自建 GitLab 的 `.patch` 不认 `<sha>~d`，解析失败时**回显 `<sha>~3` 且 error=None**，把「没解析」伪装成「解析成功」。后果链：② 传假 SHA 给 infra → infra `checkout_commit` 末行 `get_current_commit() != commit`（完整 SHA vs 字面量 `…~3`）**必然**不等 → RuntimeError → 分类器落 `compile_error` → **N43 早停封掉整个项目**。✅ 实测 kimageformats 探针 0/3、2 条被跳过，且离线预检报「14/14 放行」→ **一个 bug 造出两个假结论**。爆炸半径已核：复现记录表里非纯 SHA 的 `pinned_commit` **只有 1 条**（tier=none）→ **已交付 verified 行无一被污染**。修：`SHA_RE` 校验，解析不出返回 `error=unresolved_sha:…`、`sha=None` | ✅ 已修 |
| **N55** | 🟡 **预检对垃圾输入返回 `ok=True`**（`reason='no_build_sh'`）→ 假放行。文档里「无法判定时一律放行」针对的是**查不到**，不是**给了垃圾**。修：非空但非纯 SHA → `ok=False, reason=bad_rev:…`（**输入非法 ≠ 无法判定**） | ✅ 已修 |
| **N56** | 🟡 `RuntimeError: Error checking out commit` 不被任何 pattern 认 → 落 `compile_error`（∈ DETERMINISTIC_FAIL）→ 计入**项目级**早停。修：并入 `commit_not_found`（同族：**逐 commit 成立、非项目级必然**）→ 自动排除在早停外 | ✅ 已修 |
| **N57** | ⭐ **自建 GitLab 无法解析 `~d`** → 新增 `gitlab_commit()`：`GET /api/v4/projects/<path>/repository/commits/<sha>` 取 **`parent_ids`** 逐级走 `parents[0]`（与 N42 Gitiles 同法，merge commit 亦正确）。✅ 实测 `invent.kde.org` `~0…~3` 全部解析出纯 SHA + 日期（`~2` 的标题正是 `xcf: Fix Stack-buffer-overflow WRITE …`）。离线自测用**桩掉 http_get**，含「API 返回错误体时不得伪造 sha」 | ✅ 已加 |
| **N58** | 🔴 **`toolchain_drift` 正则过宽 → 命中成功行/路径名/apt 行**：裸 `-Werror` 命中 autotools 的**成功探针** `checking if the -Werror option is usable... yes`（几乎所有 autotools 项目都打）；裸 `unsupported` 命中 Qt **目录名** `/usr/mkspecs/features/unsupported`；裸 `ninja-build` 命中 **apt 安装行**（pcapplusplus 就这么被误判）。收紧为 `error:.*-Werror`，并**新增 `era_dep_drift`**（镜像烘死的依赖 vs 要建的 era；镜像固定 → 项目级确定性 → 计入早停）。复判历史 9 条：kimageformats→era_dep_drift、libspng→dead_external_url、pcapplusplus→buildscript_mismatch、opensc→compile_error、libredwg 不变。**五类全在 DETERMINISTIC_FAIL → 早停行为完全一致**，改的只是记的原因对不对 | ✅ 已修 |
| **N59** | 🟡 **crash_type 归一化两处缺陷**（零构建成本）：① **十六进制地址被当成类型的一部分** —— ASan 那条路硬编码 `"Segv on unknown address"`（不含地址）所以没事，**MSan** 的 `MSAN_ERR_RE` 捕获到 `(` 之前把地址带进来了 → `segv-on-unknown-address-0x7f64aa200470` vs 期望 `segv-on-unknown-address` → 压在 loose；② **UBSan 具体检查名被压成泛化 `Undefined-behavior`** → UBSAN 条目**结构性地**拿不到 medium+，而报告里具体信息是有的（`runtime error: index 16 out of bounds for type 'TCGv_i32[16]'`）。修：①在**共享**归一化里剥 ` 0x…`（两侧对称）；②observed 侧加 `UBSAN_CHECK_MAP`（**只收已实测对上的形态**，未命中退回泛化 → 宁可不升档不靠猜）。✅ 已知答案 6/6 含 4 回归；**全复现记录表 expected 侧归一化 0 行变化**；重跑 ④⑤ → **2 条 loose→medium** | ✅ 已修 |
| **N60** | 🔴 **审计盲区：自己回收了就免检** → `OSV-2023-1322` 归档被回收、交付里只剩 `PRUNED.txt`，审计却报「0 条红线」。两个洞：① `build_index` 对已回收条目在写 `INFO.txt` **之前就 `continue`**，而 `[4c]` 靠**找 INFO.txt** 枚举条目 → PRUNED 条目**对审计完全不可见**；② `dang_ver` 带 `not binary_pruned` 豁免。修：PRUNED 也写 INFO.txt（首行 `⚠ 本条不可重放`）+ 新增 2 条红线（**交付条目数 == verified 行数**、verified 行不得「已回收且不在盘」） | ✅ 已修 |
| **⚠ 「bit 级可重建」的结论必须加限定** | 重建 `OSV-2023-1322` 归档后逐字节校验 **5/5 个可执行文件 sha256 全部不符**。而 §4.55 那次「498 文件全一致」的样本是 **c-blosc2/hunspell/pcre2/md4c**，**libavc 不在其列** → §0.3 的结论**只对已实测的这 4 个项目成立**。🅗 未查明原因（构建路径/时间戳嵌入，或原始记录本身来自 N45 修复前那次「`binary_dir` 与 `sha256` 张冠李戴」的落账）。⚠ **功能上没坏**：重建件实测 **7 次崩 6 次（86%）** → 仍可重放，只是**不能声称 bit 一致** | ⚠ 已加限定 |
| **⭐ 又推翻我自己写进文档的一条「规律」** | §4.57.4「硬前置 = 全量 https 克隆、无 `git://`、无 `--depth 1`」**逐条实测全错**：`git://` 在本环境**可达**（ghostpdl/dnsmasq `ls-remote` 退出 0）；`--depth 1` **不致命**（infra `checkout_commit` 第 218 行先调 `fetch_unshallow()`）。真判据是**实测 unshallow 吞吐**：perfetto 31s ✅ · kimageformats 7s ✅ · matio 5s ✅ · skia <240s ✅ · qemu >240s ⏱ · **ghostpdl 420s 仅 12MB ≈ 29 KB/s ⛔**。ghostscript 那 192 条大池的死因不是协议而是**速率**。这是**第二次**同类错误（上次是 §4.59.2「只给 driver 会重放失败」）→ **从少数样本归纳的「规律」写进文档后就成了后续决策的前提，而它从没被单独检验过** | ✅ 已推翻 |
| **⭐ UBSAN 长期 0 正样本的缺口已破** | 分层探针（刻意按 sanitizer 各取 1 条而非随机）→ `OSV-2020-1123`（unicorn/undefined）复现，配合 N59② 后 tier=**medium**。**unicorn 成为第 10 个项目**（探针 3/3、7 构建 / 42.3min） | ✅ 本轮 |
| **N61** | ⭐ **磁盘分级保留策略**（用户批准「自动回收 + tier 分级」）。先量字节去向：归档 8.5G = **交付必需 1.50G** + **兄弟 target 7.49G** + **孤儿目录 0.29G**。**关键**：交付视图是**硬链接**指进归档的 → 「删归档路径」对那 1.50G **根本不释放空间**（`st_nlink` 实测 `{1:1433, 2:124, …, 106:105}`）→ 策略应是**把归档瘦身到交付所需并集**，不是「删旧归档」。**且「按 tier 分级」被实测全面压制**：`tier=strict` 只回收 4.38G，而 **`reuse`（只保护服务 >1 条 verified 行的归档）回收 7.09G、只留 698M 真有用的** —— 因为 119 个被引用归档里 **100 个只服务 1 条**（兄弟文件 6.80G、复用价值≈0）。执行：可用 **3.0G → 13G**、归档 **8.5G → 2.2G**，事后自校验 + 审计全过 | ✅ 已实施 |
| **两类动作、两种门控** | **纯废物无条件清**（`build/{out,work}` 中间产物 ✅1.27G、悬空 docker 镜像 ✅250M）；**动归档才受阈值门控**（`--min-free-gb`，默认 3.0）。已接进流水线：`run_repro.py --post-clean`（**默认开**）/ `--post-clean-free-gb`（默认 6.0）→ 每轮汇总后自动执行。⚠ 只删**未被任何交付条目引用**的文件，交付必需的那份永远不动（libavc 重建非 bit 一致，§4.61.9） | ✅ 已接线 |
| **⚠ unicorn 整池跑不起，必须分批** | 单个 unicorn 归档 **104～124 MB**（`fuzz_emu_*` 单个二进制就 **108MB**，内嵌 QEMU），一次构建产出**全部**变体 → 探针 3 条就 **3.8 GB**。整池剩 30 条 × ~2.3 构建/条 × ~540MB ≈ **37 GB** ≫ 可用 13 GB，而 `--post-clean` 只在**轮末**触发 → 轮中必写满。故改**定向小批**（`--sanitizers undefined,memory --limit 6`），既控磁盘又正好补最缺的 sanitizer 覆盖 | ✅ 已改策略 |
| **「期望值 unknown」判据：保持现状（用户裁定）** | ✅ 实测 **17 条** verified 的 `crash_type_expected` 本身就是 `unknown`（ClusterFuzz 当年没分类）→ `crash_type_match` **永远为假** → 结构性拿不到 medium+，哪怕帧完全对齐（`OSV-2020-1016` 是 `score_subseq=1.0` 却停在 loose）。可放宽为「类型不可判 → 按帧单独定档」，但**用户裁定保持现状**（保守）→ 本轮只记录，并在 §5 item 58 标明这是**已知的 tier 下限折损**，读 tier 分布须带此前提 | ✅ 已裁定 |
| **N62** | 🟡 **轮中磁盘水位线**（`--post-clean` 只在轮末触发，unicorn 轮中就会写满）→ `run_repro.py` 每处理一条 crash 前查水位，低于 `--mid-clean-free-gb`（默认 5.0）即时调 `disk_policy.py`（**复用其全套安全检查，不另写删除逻辑**）。✅ 实测有效：`w5-unicorn-b2`（12 条/21 构建/96.9min）期间触发 **3 次**，可用空间在 **6.7G↔12G** 震荡未触底；该批产出 **7 条复现** | ✅ 已加 |
| **N63** | 🔴 **轮中清理删掉了本轮在飞的归档** → `needed_map()` 从**复现记录表 verified 行**算「交付必需」，而轮中清理时本轮那些**已构建、还没落账**的行不在复现记录表里 → 其归档被判成「孤儿目录」**整目录删掉**。✅ 实测：4 条刚复现的 crash（`OSV-2020-1409`/`-1945`/`-2180`/`-231`）归档被删 → ⑤ 只能标 `binary_pruned` → 审计 **3 条红线**；本轮 21 次构建涉及 15 个归档、**14 个已被删**。修：`--protect-since <epoch>` 读 `build_records.jsonl`，把 `ts >= 本轮起始` 的 `binary_dir` **整目录保护**（此时还不知最终用哪个 target，故连兄弟文件也不删；落账后下一轮自然精确瘦身） | ✅ 已修 |
| **N64** | 🔴 **磁盘写满事故**：修完 N63 重跑，可用空间 `4.3G → 2.1G → **96K** → **68K**（100% 满）`、进程僵死、连 shell 输出都写不出。原因：水位线触发了、N63 也保护住了在飞归档（`保护 6 个 / **7.29 GB**`），但**「保护 7.29G」与「继续构建」在 unicorn 这种单归档 100MB+ 的项目上直接冲突** —— 光靠水位线不够，保护集合本身就能占满盘。修：加**硬底线安全阀** `--disk-hard-floor-gb`（默认 **2.5**）→ 回收后仍低于底线就抛 RuntimeError **优雅停轮**（已完成记录已落盘，续跑减小 `--limit`）。恢复：清 build/ 1.27G + `disk_policy --force` **8.01G** → 可用 2.0G→**9.2G**、归档 13G→**5.0G**，交付 162 条全部自包含可重放、审计 0 红线 | ✅ 已修 |
| **N65** | 🔴 **构建前预检把 make 产物当成必需源文件** → `CAND_RE` 的第一个 alternative 是 `…(?:-|_)fuzzer(?:\.\w+)?`，`\.\w+` 允许**任意**扩展名。✅ 实测 htslib@`92ea05adb2`：`build.sh:23` 是 `make -j$(nproc) libhts.a bgzip htsfile tabix annot-tsv test/fuzz/hts_open_fuzzer.o` —— `.o` 是 make **目标**（第 35 行才拿去链接），同 commit 树里只有 `test/fuzz/hts_open_fuzzer.c`（`git ls-tree` 实测：`.o` 0 个、`.c` 1 个）。raw 端点对 `.o` 必然 404 → 判 `buildscript_mismatch` → **一次挡死 htslib 全部 25 条池**（含 19 条 heap-buffer-overflow，是当轮分析价值最高的候选）。与 **N36**（mupdf 的 submodule 误报）同族：该文件构建时必然存在、只是不在 git 树里。修：用**已有的 `SRC_EXTS` 白名单**过滤候选（不另造黑名单，`.dict`/`.options` 是签入的仍在白名单内）。✅ 修后 htslib `ok=True`（跳过 2 个产物路径），且**既有已知答案回归全过**：[A] 该报的 9 条缺路径仍全命中、[B] 11 个项目误报 0、[C] 契约通过 | ✅ 已修 |
| **N66** | 🔴 **归档跳过所有子目录** → `archive_build` 的 `if not os.path.isfile(fp): continue` 只收顶层文件。✅ 实测 espeak-ng：`projects/espeak-ng/build.sh:25` 是 `cp -r espeak-ng-data/ $OUT/`（1.4MB / 351 文件），归档里却只有 `ssml-fuzzer` + `llvm-symbolizer` **2 项** → 重放时 `Error processing file '/out/phontab': No such file or directory` → 目标初始化失败 `exit=77`。与 W2 修过的 flatbuffers `.bfbs` 缺失同族，但那次缺的是**顶层文件**、这次是**顶层目录**。修：递归归档子目录 + 新增 `ARCHIVE_DIR_MAX_BYTES=64MB` 每目录树预算（单文件仍沿用 32MB 上限）、仍排除 `*_seed_corpus.zip`。✅ 已知答案自测 5/5（含「子目录递归归档」「seed_corpus 仍排除」）；实测修后归档含 474–487 个数据文件 | ✅ 已修 |
| **N67** | 🔴 **`fuzz target exited` 被当成复现** → `NON_CRASH_DIAGNOSTICS` 只有 `{timeout, out-of-memory, oom, no-crash}`，漏了 N46 同族的第三种「非崩溃诊断」。✅ 实测受害 **4 条 espeak-ng** 被记成 `tier=loose`，而其 `report.log` 里**没有任何 sanitizer 段**，只有 `==7== ERROR: libFuzzer: fuzz target exited` + `DEDUP_TOKEN: __sanitizer_print_stack_trace--fuzzer::PrintStackTrace()--fuzzer::Fuzzer::ExitCallback()`。⚠ 且 N46 原有的「有 sanitizer 报告就不翻转」判据用的是**朴素子串** `"sanitizer" not in raw` —— 而上面那个 DEDUP_TOKEN 里就含 `__sanitizer_print_stack_trace`，**子串命中导致防线不触发**（自测当场抓到：新增用例 got tier=loose、want none）。修：① 加 `fuzz-target-exited`；② 改用 `RE_SAN_REPORT` 匹配真报告特征（`(?:ERROR|WARNING): (?:Address|Memory|Thread|Undefined)Sanitizer` / `SUMMARY: …Sanitizer` / `runtime error:`）。✅ N46 自测 9/10 → **10/10**，全套 20/20；重跑 ④⑤ 后 4 条自动降为 `none`（复现记录表 append-only，不手改） | ✅ 已修 |
| **N68** | 🟡 **预检对「多仓库 build.sh」误报** → `build.sh` 里 `cd $SRC/cryptofuzz` 之后的相对路径（wolfssl 第 53 行 `sed -i … modules/wolfcrypt/module.cpp`）属于**另一个仓库**，拿 wolfssl 仓库去查必然 404 → 判 `buildscript_mismatch` → **整个 wolfssl 23 条池被跳过**。✅ A/B 证明**与 N65 无关**：该项目只有 2 个候选、都是 `.c/.cpp`，`产物跳过=0`。与 N36（submodule 看不见）、N65（构建产物）同族 —— 都是「**查不到 ≠ 查过没有**」。修：追踪 `cd $SRC/<dir>` 上下文，外来仓库路径记 `undecidable` 并**放行**。✅ 已知答案回归全过：wolfssl 误报 1→**0**，且 [A] 段该报的（harfbuzz/pcapplusplus/libspng）仍全部命中 | ✅ 已修 |
| **N69** | 🔴 **交付副本不含运行期数据子目录** → `show_repro.py` 的交付拷贝按 `_replay_bundle` 逐个 `os.path.isfile` 处理，**目录被跳过**。N66 修好后归档里有 `espeak-ng-data/`，但交付条目仍缺 → **`tier=strict` 的行实际重放不出来**（✅ 实测受害者 `OSV-2021-1631`：`replay.sh` 返回 `❌ 未复现（容器退出码 77）`）。即「③ 在容器里跑的是**归档**（有数据）、交付重放跑的是**副本**（无数据）」→ 两者结论不一致，而审计只查目录存在性、**没查真重放**，所以 0 红线。修：交付拷贝时 `os.walk` 归档、把子目录内文件**硬链接**进副本（额外磁盘 0 字节）。✅ 修后 4 条 espeak-ng strict **全部重放成功**并给出真 ASAN 报告（如 `OSV-2021-1631` → `stack-buffer-overflow @ numbers.c:1785 in TranslateNumber_1`） | ✅ 已修 |
| **N70** | 🔴 **强杀 run_repro 会污染 worktree，并静默挡死后续所有构建** —— ② 的 era 适配会**改写** `projects/<p>/{Dockerfile,build.sh,project.yaml}` 并暂存（实测 w8new 轮为 OSV-2020-1080 把 curl 的 `FROM base-builder:ubuntu-24-04` 改回 `FROM base-builder`、加回 `MAINTAINER dvyukov@google.com`、去掉后来才有的 `REPLAY_ENABLED` 块），正常结束时还原；**`kill -9` 让还原没跑** → worktree 脏 → gate 条件②不通过 → 写 `BLOCKED.md` 并 ABORT。⚠ **危害被放大**：gate 是**每条 crash 每次构建**都查，于是下一轮（w8b4，目标是 wasm3/jq/wolfmqtt，**与 curl 毫无关系**）的 **252 次构建尝试全部 ABORT**，而失败形态极其安静：`build_status=None`、`实际构建 0 次`、`墙钟 5.8min`、**审计还报 0 红线**。处置：`git -C /root/gyx/oss-fuzz-repro checkout HEAD -- projects/curl/` 还原（✅ 实测恢复 0 项脏）。**教训**：① 长任务不能 `kill -9`，应先让它跑完或走优雅停止；② gate ABORT 应当**终止整轮**而不是逐格重试 252 次；③ 审计应增加一条红线：**`BLOCKED.md` 存在 或 worktree 脏 → 该轮结果不可信** | ✅ 已处置，②③待改 |
| **第 19 套自测：专抓「Python 不报错、只静默生效」的缺陷** | ① 重复顶层函数/类定义（**后定义者静默覆盖前者** —— 本轮 `free_gb` 事故：我在模块顶部新写一份，被第 132 行原有的**静默覆盖**，`except OSError` 容错根本没生效，直到 `free_gb('/nonexistent')` 抛 FileNotFoundError 才发现）② 重复模块级常量 ③ `except` 引用未定义异常名 ④ 已知答案（合成 `free_gb ×2` 必须检出）④b **真的 subprocess 跑每个脚本的 `--help`** | ✅ 已加 |
| **④b 当场抓到 2 个 `--help` 崩溃（argparse 会对 help 串做 `%` 格式化）** | ① **我自己刚写的**：`--disk-hard-floor-gb` 的 help 里「100% 满」→ `unsupported format character '?' (0x6ee1)`；② **W3 就存在、潜伏至今的**：`manifest_builder.py --sort` 的 help 里「复现率 **45.7% vs HEAD 6.7%**」→ `unsupported format character 'v' (0x76) at index 175`，**整个 `--help` 崩掉**，一直没暴露是因为**从来没人跑过它的 `--help`**。两处均改为 `%%`。⚠ 这类缺陷 `ast.parse` 查不出、`import` 也不报，**只有真渲染 help 才炸** → 所以 ④b 是直接跑（22 个脚本全覆盖），不是静态猜 | ✅ 已修 |
| **⚠ 又一次测量口径错误** | 查「今天的构建记录」时把阈值硬编码成 `2026-09-18 10:45`，而当天其实是 **09-17** → 查出 0 条，一度误判成「build_records 没写」。用 `date` 核对后才对上（21 条记录 / 15 个归档 / 14 个已删）。**与 §4.57.3「已知答案必须先核实」同族** | ✅ 教训 |

---

# 4. 已实现（W1 ⓪① + W2 ②③④⑤⑥）：模块、产物、对账、首轮结果

**W1 写 ⓪①；W2 写 ②③④⑤⑥ 并真跑首轮。⑦ `recover_targets.py`（可选增强）仍未写。**

## 4.1 模块

- **`repro_common.py`（⓪）**：见 §1.3⓪。`normalize_frames()` **不重写**——用 `ast` 从 `preflight/history/r2_r5_r6_r7_recompute.py` 逐字提取（含 `INTERNAL_PREFIXES`/`SUFFIX_RE`/`LAMBDA_RE`/两个函数），提取失败即 raise（**不静默回退到另一份实现**，防两处分叉）；并以 **R2-extra 的 10 项逐帧计数对账全等**（3770/502/498/4/635/22/0/4/0/0 ✅）证明是同一份实现。`PROJECT_NAME_MAP` **故意为空**（R5 教训：不擅自映射，name-miss 一律标 `unmapped_project`）。
- **`manifest_builder.py`（①）**：见 §1.3①。全量 **3,790 条 / 4.8s**（离线）；静态 check 需网络、可关（`--static-check` + `--static-check-limit` 限界，逐条 2–5 次 HTTP）。

## 4.2 产物与全量对账

`artifacts/repro_manifest.jsonl`（3,790 行 × 44 字段）+ `build_groups.json`（**404** head_groups + **3,093** pinned_queue）+ `repo_path_map.json`（328 项目、含逐项目 clone 清单）。

| 对账项 | manifest | 预飞实测 | |
|---|---|---|---|
| C/C++ 主线 | **3,502** | R14 3,502 | ✅ |
| 非 C/C++ / name-miss | 246 / 42 | R5 246 / 42 | ✅ |
| language 分布 | c++3,059/c443/jvm191/rust38/swift8/python7/ruby2 | R5 同 | ✅ |
| `target_inferred` | **156** | R7 净可用 156 | ✅ |
| `sanitizer_inferred` | **25** | R14/R16 空 sanitizer 25 | ✅ |
| 有 `fixed_commit` | **3,550** | R1 has_fixed 3,550 | ✅ |
| `osv_degenerate_range` | **53** | N6 53 | ✅ |
| 有 `repo_url` | **3,776** | R13b 3,776(99.6%) | ✅ |
| `repo_path` high+medium（主线） | **97.5%** | W1 报告 97.5% | ✅ |

**三处口径差已逐项测清（非丢数据）**：
1. `missing_testcase` 14 vs 文档 35 → skip_reason **互斥且有优先级**；非互斥口径下「testcase 磁盘缺失」= **35 ✅**（20 条被 `unreproducible_no_target` 占、1 条被 `unmapped_project` 占）。
2. `unreproducible_no_target` 352 vs 文档 379 → 非互斥口径下「最终无 fuzz_target」= **379 ✅**（25 条被 `unmapped_project` 占 = R7 减掉的 unrar 25、2 条被 `non_cpp_language` 占）。
3. `(project,sanitizer)` 组合 436 vs R14 的 448 → R14 用 `san_of()` **原始字符串**口径（`'address (ASAN)'` 与 `''` 算两组）；原始口径重算 = **448 ✅**，归一化后 25 条空 sanitizer 并入各自项目的 address 组（R16：它们**就是按 ASAN 构建**的）→ 436。`build_groups` 只收 actionable 记录 → **404**。

**skip_reason 分布**（互斥）：`null` 3,136(actionable) / `unreproducible_no_target` 352 / `non_cpp_language` 246 / `unmapped_project` 42 / `missing_testcase` 14。
**`commit_source` 先验**：`fixed_parent` 3,497 / `introducing` 226 / `head` 67（= 53 N6 退化 + 14 两者都无）。

## 4.3 回归验证（最有价值的一项：正确答案已知）

用 P0/P0-B/P0-C 手工跑通的 3 条验证 ① 的字段：**29/29 字段全对、0 不符**。

| crash | 关键字段（manifest 产出 = 当时手工确定值） |
|---|---|
| **md4c OSV-2022-126** | 无 `fixed` → `commit_source=introducing`、`pin=introducing_commit 62b60979…`、`repo_path=/src/md4c`、target `fuzz-mdhtml`（✅ P0 在该 commit 复现，`score_subseq=1.0`） |
| **pcre2 OSV-2024-1261** | `fixed=6f36e8ab…`、**`fixed_real=037fb170…`**、**`pin_commit=62b3ceca…`**、**`walkback_depth=2`**、**`fixed_misattributed=true`**、`commit_source=fixed_ancestor`、`repo_path=/src/pcre2`、target `pcre2_fuzzer_16`（✅ P0-B 在 `fixed^^` 得项目首个 strict） |
| **hunspell OSV-2022-886** | `fixed=6291cac8…`、**`fixed_real=d6836713…`**、`walkback_depth=2`、**`fixed_misattributed=true`**（**正是 §1.3① 旧帧判据会答错的那条**）、`repo_path=/src/hunspell`、target `affdicfuzzer`（✅ P0-C 钉 `fixed^` 复现 none，因其本身即真修复） |

**人工抽查 8 条**（覆盖各档：`fixed_misattributed`/N6 退化/target_inferred/candidates/unmapped/non_cpp/missing_testcase/alias/dynamic_dest），逐条对 Dockerfile grep、OSV json、project.yaml、testcase 磁盘存在性**独立复核**（用不同代码路径重算）→ 全部一致。抽查中还发现并修掉 ① 自身两个 bug：`repo_url` 只在「有 fixed 的 range」里找（3,550 应为 3,776）、`expected_repro_version` 在静态 check 关闭时错退化成 `head`；以及 `resolve_repo_path` 对无映射表条目的项目改为返回 `None`（**宁缺勿错**，不给 ② 一个看似可用却不可信的 path）。

## 4.4 本轮固化与约束

- worktree：`repro-patches` @ `07522dc0e`（3 files +66/−3），**干净**；主树仍 **550**（driver_create 研究线，未动）；未改任何 Dockerfile/build.sh；未跑构建/docker（除拉 diff）。
- **文档归属标记**：W1 的实测结论落在 §2.3/§2.4/§3/§4，来源列标 **`✅ W1`（19 处）**；规格变更落在 §1.3①②/§1.5/§1.7 H。精简前那版用的是 32 处内联 `[实现 W1]` 标记（逐处标注改了哪句），已随精简并入对应章节——**改动前后的逐处对照见 `archive/2026-09-09-DELIVERY-fulltext-snapshot.md`**（2,063 行全文快照，md5 与精简前一致）。

## 4.5 W2 概览：一句话结果与总量



**流水线打通并真跑起来了：6 个项目、129 条 crash、54 次真实构建尝试（49 成功 = 90.7%）、125 次复现执行 → 12 条复现（3 `strict` + 7 `medium` + 2 `loose`）、113 条 `none`、4 条未跑。** Phase 0–5 **全部完成，无卡点**；三条已知答案 crash 的 ② 产物与 P0/P0-B/P0-C 手工构建 **逐字节一致（3/3）**；era 缓存实测省 **49.5%**（与 P0-B 独立测得的 292s 吻合）；负对照 **8/8 通过**。

代价是**查出 13 个自己写的 bug**（§4.7）和 **11 条新发现 N7–N17**（§3），其中 3 条直接推翻或修正了此前几轮的结论（hunspell 的「已知答案」归因、R13a 的「15 条」、`T_strict` 的可调性）。

| 量 | 值 | 出处 |
|---|---|---|
| 交付模块 | ②`build_orchestrator.py` ③`repro_runner.py` ④`verify_tiered.py` ⑤`annotate_dataset.py` ⑥`run_repro.py` | `ls *.py` → 7 个（含 ⓪①） |
| `repro_dataset.jsonl` | **142 行 / 129 条唯一 crash / 51 字段**（append-only，3 个 run_id） | `wc -l repro_dataset.jsonl` |
| tier 分布（最新） | `strict` **3** ／ `medium` **7** ／ `loose` **2** ／ `none` **113** ／ 未跑 **4** | §4.8 表 A |
| 真实构建尝试 | **54** 次（`build_records.jsonl` 58 条，剔 4 条我方 bug 造成的伪记录） | §4.9(e) |
| **端到端可构建率** | **49/54 = 90.7%**（HEAD **33/33 = 100%**、钉版 **16/21 = 76.2%**） | §4.9(e)。**这是 P0-C 明确拒绝用 detect_repo 可达率 98% 冒充的那个数，本轮第一次测到** |
| 归档区 | 17 个 commit 目录、94 文件、**782 MB**；`_shared/` 两个 symbolizer 变体（`db0240ff`/`13babd3b`，硬链接生效） | `du -sh artifacts/binaries` |
| 日志留存 | 构建日志 **21** 份、复现日志 **124** 份（Phase 5(c) 的原始依据） | `artifacts/logs/` |
| 磁盘 | 剩 **13 G**（88% 已用）——本轮的硬约束，决定了选样 | `df -h /` |

---

---

## 4.6 W2 Phase 0：四项遗留的实测与改动



#### (a) `osv_events()` 解析假象的**横向**审计

W1 只查出「no_fixed 细分 introduced-only=0」这一处。本轮把 R1/R13a/R13b/R14 的**全部**已发布数字用三种解析器各算一遍：A = R1 原样（有 bug）、B = ⓪ 现行、C = 完整解析（introduced-only 也成对）。
脚本 `preflight/history/w2_phase0a_osv_audit.py`（结果落 `w2_phase0a_audit.json`）。

| # | 已发布数字 | A | B | C | 判定 |
|---|---|---|---|---|---|
| F1 | has_fixed 3,550 / no_fixed 240 | 3550/240 | 3550/240 | 3550/240 | ✅ **不受影响**（存在性判定，不依赖配对） |
| F2 | no_fixed 细分 introduced-only | **0** | 226 | 226 | ❌ W1 已查出；本轮确认 **B==C**，真值 226/14 |
| F3 | R13a「multi-event(>1 对) **540**」 | 540 | 540 | ≥2 fixed=540／≥2 对=**639**／>2 event=**630**／**≥2 range=0** | ⚠ **标签错**：540 实为「**≥2 个 fixed 事件**」的记录数，不是 multi-event。且**全部记录只有 1 个 range（3,776）或 0 个（14）** → multi-range 从未发生 |
| F4 | R13a「**0 歧义**」 | 0 | 0（`intro_match_multi`=0） | – | ✅ **成立** |
| F5 | R13a「**15** 条走取最后 fixed」 | 15 | **69**（全量）/ **24**（540 内） | – | ❌ **错**。真值 **24**（540 内口径）/ 69（全量）。`15 = 24 − 9`，差值正是 9 条 `introducing_commit=="0"` |
| F6 | repo URL 覆盖 **3,776** | 3776 | 3776 | 3776 | ✅ 三者一致；「同 range 配对」vs「最后一个有 repo 的 range」选出**不同 repo 的记录 = 0**（因为只有 1 个 range，W1 那个修在当前数据上无可观测差异——防御性正确，但不是 3,550→3,776 的原因） |
| F7 | N6 退化 **60 对 / 53 记录** | – | 53 | 60 对 | ✅ **不受影响**（逐 range 内比较，不依赖 pairs 累积） |
| F8 | R14 C/C++ has_fixed **3,301** | 3301 | 3301 | 3301 | ✅ |
| F9 | manifest vs 审计解析器 | – | **9 条不符** | – | ⚠ **假警报**：我传了原始 `"0"`，① 已归一（`manifest_builder.py:145`）→ ① 对、我的审计脚本错 |

**F5 的机制（逐字复刻 R1 脚本 88–109 行验证，非推断）**：R1 用 `ic=meta[...]["introducing_commit"]` **原始值**，而 OSV 用 `"0"` 表示「从最初即有漏洞」（**哨兵，不是 sha**）。全量 **9 条** crash 的 `introducing_commit == "0"` 且其 OSV 内也含 `introduced:"0"` 事件 → 传原始值必然假匹配 → 这 9 条从「无 intro 匹配→取最后 fixed」被错记成「规则① 匹配成功」。**同一个 bug 的第二个症状。**

**改了哪里**
1. ⓪ `osv_fixed_and_repo()`：`"0"`/`""` **永不参与规则① 匹配**（`repro_common.py` 内新增哨兵守卫 + 文档）。**防御性修复**——① 与 W1 抽样脚本本来就归一了，故行为不变（✅ 验证：审计的 9 条不符 → **0**；回归 **29/29 不变**），但未来的调用方（②、新脚本）不会再踩。
2. **已改**（DELIVERY §2 的 R13a 行）：R13a 的「540 multi-event」应改标签为「≥2 个 fixed 事件」，「15 条」应改 **24**（540 内）/ 69（全量）。
3. `n_osv_pairs` 只被记录、**不参与任何决策**（`repro_common.py` MANIFEST_FIELDS、`manifest_builder.py:151`）→ F3 的标签错**不影响流水线行为**，只影响文档表述。

#### (b) `pinned_queue` 排序

**先测量再选键**（脚本 `preflight/history/w2_phase0b_queue_order.py`，结果 `w2_phase0b_queue_order.json`）。

*era 窗口实测*（`git -C worktree log --format=%ct -- projects/<p>`，= 官方 `build_specified_commit.py:243-248` 的同一算法）：8 个 top 项目的 `projects/<p>` 变更中位间隔 **32 天**（范围 9–97；ghostscript 9.4d / opensc 97.3d）。→ era 窗口是**周级**，不是年级。

*离线日期代理选型*（pin commit 真实日期要联网，3,093 次请求不可接受）：取 84 条真实 fix author date（联网 + W1 已有 42 条）对三种代理做秩相关：

| 代理 | 全体 Spearman | **同年组内** Spearman | era 邻接命中（n=82 相邻同项目对） |
|---|---|---|---|
| P1 `osv_id` 字典序 | +0.974 | **+0.478** | 52.4% |
| P2 OSV `published` | +0.898 | +0.456 | 52.4% |
| **P3 OSS-Fuzz issue id**（`report_url` 的 `?id=<n>`，✅ **3,790/3,790** 可解析） | **+0.976** | **+0.733** | **65.9%** |
| 参照：真实日期排序（上界） | 1.0 | 1.0 | 69.5% |

⚠ 全体 0.974 几乎全来自**年份前缀**；era 邻接靠的是**组内**序 → 只有 P3 可用。P3 达到上界的 **95%**（65.9/69.5），比 P1 高 **13.5pp** ≫ 我预设的 5pp 判据 → **选 P3**。
`published` 的绝对偏移均值 **+244 天**（中位 +1.0，IQR −6.4…+476.3）→ 只能当序数用，不能当日期用。

**改了哪里**：① `write_outputs()` 的 `pinned_queue` 排序键 `osv_id` → **`(project, issue_id)`**；⓪ 新增 `issue_id_of()`；manifest 新增 `issue_id` 字段（45→46）。
**实测效果**：相邻同项目对 **432 → 2,844**（= 理论上限 `3,093−249`）；项目内 issue_id 单调违反 **0**；era 缓存因此才有命中机会（§4.9(e) 实测到 2 次命中 + 1 次跨 commit 命中）。
*不按 sanitizer 再分层*：实测那样会把日期序打断（旧口径 75.6% < 80.0%）。

#### (c) N6 的 53 条不要一刀切

脚本 `preflight/history/w2_phase0c_degenerate.py`（结果 `w2_phase0c_degenerate.json`）。**故意传 `introduced=None`**——若传退化 sha 自身，`intro_depth=0` 会使 `d_fix` 判据（`d<intro_depth`）永假、必然 `not_located`，等于把待检验的前提当输入（循环论证）。

| 判定 | 计数 |
|---|---|
| 🅗 H_fix（退化 sha 其实是修复）→ 像 fix | **8/53 = 15.1%** |
| 不像 fix：`not_located`（取到 patch 但 S<2 或 no_source） | 32 |
| 不像 fix：`undecidable`（非 github/gitlab 托管 11 + patch 404 2） | 13 |
| S(C0) 分布 | 0→20、1→12、2→6、3→2、None→13 |

**但逐条读消息后发现 8 个正例里 6 个是假阳性**：

| osv_id | project | S | 消息 | 判定 |
|---|---|---|---|---|
| OSV-2018-191 / -90 | systemd | 2 / 3 | 「networkd: make network_load_one **"public" and add a fuzzer for it**」 | ❌ 加 fuzzer 的 commit，不是修复 |
| OSV-2021-725 / -729 | libyal | 2 | 「**Added property OSS-Fuzz target**」 | ❌ 同上 |
| OSV-2021-553 / -602 | freetype2 | 2 | 「Include colrv1 in script preparing **fuzzer corpora**」（`test_only=True`；且 repo 是 `freetype2-testing`，W1 已标异名） | ❌ 只改语料脚本 |
| OSV-2021-1472 | h3 | 3 | 「Add error return codes to gridDisk functions (#505)」 | ✅ **可信**（帧函数 `h3NeighborRotations` 在 diff 里） |
| OSV-2016-6 | file | 2 | 「Use signed offsets to reduce false positives」 | ✅ 可信，但 `skip_reason=unreproducible_no_target` → 不可执行 |

→ **N7**：「加/改 fuzzing harness」类 commit 天然满足打分器的两个强信号（消息提 OSS-Fuzz → `ofz_ref` +2；diff 动被测函数 → `frames_in_diff` +2），在 N6 上造成 **6/8 = 75%** 假阳性。

**改了哪里**：⓪ 新增 `HARNESS_RE` + `ev["harness_like"]`（**只记证据、不改分** → W1 已标定的 off-by-one 14.3% 不受影响）+ `resolve_degenerate()`，放行需 ①`S≥2` ②`¬no_source` ③`¬test_only` ④`¬harness_like` ⑤`frames_in_diff≠∅` ⑥`pin` 可解析。① 新增 `degenerate_resolved` 字段 + `--no-degenerate-resolve`/`--degenerate-only`。
**实测**：53 条复核 → **解禁 2 条**（h3 OSV-2021-1472 可执行、file OSV-2016-6 被 skip_reason 挡），拒绝理由逐条可追（S=0×21 / S=1×11 / patch 不可得×13 / test_only×2 / **harness×4**）。正则精确率 **7/7**（命中全部 6 个假阳性 + 1 条 S=0 同族），**不误杀**两个必须放行的。`pinned_queue` 3,093 → **3,094**（h3 入队）。
ⓘ 诚实标注：「不像 fix」≠「证实是 introducing」——打分器只能证否 fix-like，不能证实 H_intro；那 45 条维持禁钉版是**保守**处置，不是被证明的处置。

#### (d) `walkback_depth_actual`

⓪ 新增 `RUNTIME_FIELDS`（31 项，②③④⑤ 追加到 dataset 的字段，顺序即落盘顺序），`walkback_depth_actual` 与静态 `walkback_depth` **分开存**，并在注释里写清语义：`walkback_depth` = ① 预测/② 计划要钉的格数；`walkback_depth_actual` = **实际**在第几格复现（须与 `reproduced_any` 合读）。⑤ 直接按此列表落盘、不自行发明。
**实测已产出真值**：`1`×4、`2`×1、`None`×7（HEAD/introducing 复现，非 walk-back 格）——见 §4.9(a)。

#### 附带修掉的性能 bug（不在任务清单里，但影响后续所有轮次）

① 主循环 `if args.static_check and args.sleep: time.sleep(...)` 对**每条记录**都睡，即使该条没发任何网络请求 → `--static-check` 的全量跑白等 3,790×0.2s = **758s**（实测 787s，其中静态 check 本身只占 17.4s）。改成「只在本条真发了请求时睡」→ 全量跑 **787s → 33s**（`user 4.7s`，说明之前全是 sleep）。

---

---

## 4.7 W2 模块实现：落地方式、偏离、13 个 bug、已知答案回归



#### 3.1 ② `build_orchestrator.py`（约 700 行）

核心逻辑：gate → 按 `(project,sanitizer)` 分组做 HEAD 构建 / 按 `pinned_queue` 顺序做钉版构建 → 每次成功立即归档 → 写 `build_records.jsonl` + `state.json`。

| 设计要求 | 如何落地 | 实测证据 |
|---|---|---|
| **缓存键三层**（R16/R17/R18） | `bkey()=f"{project}\|{san}\|{commit}"`；HEAD 的 commit 分量 = `resolve_head_sha()` 在**镜像内** `git -C <repo_path> rev-parse HEAD`（`repo_path` 优先，退化到 `/src/<project>`，再退化到「/src 下唯一 git 仓库」）；解析不到 → `pinned_commit="UNKNOWN"` + **不写 head_sha_cache**（不跨轮复用） | md4c → `61f5ce76647a…`（**与 P0 报告 :95 记录逐字一致**）、pcre2 → `aac57f978e38…`（**与 P0-B :78 一致**）、hunspell → `e184e22c51fe`、c-blosc2 → `c3059fa06452`、flatbuffers → `5761d6e67af8`、libtsm → `b73acb4c7169`。**6/6 解析成功，0 条 UNKNOWN** |
| **构建成功即归档**（② 专属） | `archive_build()`：`build/out/<p>/` → `artifacts/binaries/<p>/<san>/<commit>/`；`binary_dir` 指归档位；记 `binary_sha256`；归档失败 → `archive_failed` 且**不计入缓存**（`emit()` 只在 `build_status=="ok"` 时写 `st["builds"]`） | 17 个 commit 目录、782 MB。**R17-1 现场实证**：md4c 的 HEAD 二进制被随后的钉版构建 `rm -rf /out/*` 覆盖，而归档区 `61f5ce76…/` 与 `62b60979…/` **两个 commit 并存** |
| **symbolizer 内容寻址去重** | `dedup_symbolizer()`：sha256 → `_shared/llvm-symbolizer-<sha8>` + 各 commit 目录 `os.link()` 硬链接 | `_shared/` 恰好出现 **两个变体 `db0240ff` 与 `13babd3b`** = DELIVERY §1.3② 预言的「仅 2 个内容变体」；硬链接数 = 2（`stat -c %h`）；单构建边际增量 = 仅 target 本身 |
| **两条构建路径** | HEAD = `helper.py build_fuzzers --sanitizer <san> <p>`；钉版 = `build_specified_commit.py --project_name --commit --sanitizer [--repo_url --repo_path]`（P0-C 旁路，避开 N5） | 钉版日志逐条含 `detect_main_repo bypassed (N5): repo_url=… repo_path=…`（P0-C 的补丁在自动化下**照常生效**） |
| **N4 还原** | `restore_projects()`：`git checkout HEAD -- projects/<p>` + 清未跟踪文件，放在 `try/finally` 里（**无论成败都还原**），记 `worktree_restored` | 全部钉版记录 `worktree_restored=True`；跑完 worktree `git status --porcelain` = **空** |
| **N4 era 缓存** | `era_commit_for()` 用与官方**同一算法**（`git log --before=<date> -n1 projects/<p>`）自己算 era；`_learn_era()` 学习「HEAD 配置失败 / era 配置成功」；`era_suggestion()` **只在已观测到 `head_ok==0 且 era_ok>0` 时**才建议预 checkout（不预设「老 commit 一定要 era」）；era 日期取 `.patch` 的 author date（零 clone） | pcre2 首建 577.3s（era-retry 内建）→ 学到 `pcre2\|a958ed8e…`；**同 commit 重跑命中缓存 → 291.7s（省 49.5%）**；且**跨 commit 也命中**（`037fb170` 也落在 era `a958ed8e` → 291s）。解析出的 era commit `a958ed8e38ec…` **与 DELIVERY §2 记录的 `a958ed8e` 一致** |
| **walk-back + clamp** | `plan_pinned()`：① 判 `located` → 1 格直接钉；`not_located`/`undecidable`/`skipped` → depth 1..3 逐格解析 `fixed~d` 真实 SHA（`.patch` 端点，零 clone）；N6 未复核通过 → 不钉；无 fixed → 回退 `introducing_commit`（depth=None，**不占用 1..3 语义**） | 见 §4.9(a)：OSV-2020-2183 depth1 构建失败 → **depth2 成功并复现**（`walkback_depth_actual=2`） |
| **限界与护栏** | `--max-builds`（HEAD+钉版合计）、`--stop-after-failures`（连续失败急停）、`state.json` 续跑跳过、`--force` 重建、`--build-timeout` | Phase 4a 的 `--max-builds 8` 精确生效（8 次后停，3 条未尝试 → 记 `none` 而非假成功） |
| **worktree gate** | 四条件（分支 / 无未提交改动 / `07522dc0e` 在 HEAD 历史 / 无 dc-injected）**+ 第五条镜像污染检查** | ② 本轮被调用 **34 次**（stage1×13 / stage2×20 / auto×1，`state.json` 的 `runs`），每次非 dry-run 都过 gate，**34/34 全过**；第五条抓出 3 个污染镜像（→ N10） |
| **假成功防护** | 归档前校验目标二进制 `isfile ∧ X_OK ∧ size>0`，否则 `targets_missing` | c-blosc2 的 `compress_fuzzer` 在 HEAD **根本不产出**（`build/out` 只有 4 个 target）→ 如实记 `target_not_in_archive`，**没有**伪造成功 |

**与设计的偏离**（都在下面注明理由）：
1. `--stage auto` 需要 ③ 的 observations 才知道谁没复现 → ② 的 `auto` 要求 `--observations`，没给则退化成只做 Stage1 并告警（**不擅自把全部 crash 钉一遍**：钉版 per-commit 独占，单位成本约 8×）。
2. **walk-back 循环不在 ②、在 ⑥**（架构修正，见 §4.7 bug #9）：「首个 `reproduced_any=true` 即停」需要复现结果，而 ② 只懂构建 → ② 会在「构建成功」（甚至只是缓存命中）时就停。② 退化为「建这一格」，⑥ 用 `--commit-override <oid>=<sha>:<depth>` 逐格驱动。
3. era 日期用 `.patch` 的 **author date**，而官方 `build_specified_commit.py:239` 用 `git show --format=%ct` = **committer date** → 两者可能跨 `projects/<p>` 变更边界而不一致。故 era 预 checkout 是**优化而非前提**：预测错了官方 era-retry 仍兜底。ⓘ 本轮 4 次 era 命中未见预测偏差，但未专门测两口径差异。

#### 3.2 ③ `repro_runner.py`

一比一复刻 ✅ P0 验证过的形态（`docker run --rm -i -v <归档位>:/out -v <tc>:/testcase -e FUZZING_ENGINE=libfuzzer -e SANITIZER=<san> -e RUN_FUZZER_MODE=interactive -e SKIP_SEED_CORPUS=1 -e TESTCASE=/testcase base-runner:ubuntu-24-04 bash -c '<cmd>'`），并按 `run_fuzzer:204-212` 追加 `.options`（**由容器内 `parse_options.py` 解析**，不自己写 ini 解析器）与 `-dict=`，完整 `CMD_LINE` 回显进日志（`run_fuzzer:216 echo` 同法）。

* **运行参数用镜像 ENV 的实测默认值**：开工前核对活镜像 `docker run --rm base-runner env` → `OUT=/out`、`FUZZER_ARGS=-rss_limit_mb=2560 -timeout=25`（**M11 逐字命中**）；ASAN/MSAN/UBSAN_OPTIONS **不在命令行覆盖**，用镜像默认（含 `symbolize=1:dedup_token_length=3:strip_path_prefix=/workspace/`），记入 `runtime_limits`。
* **UBSAN 不 abort**：解析 stderr 的 `runtime error:` / `SUMMARY: UndefinedBehaviorSanitizer` → `ubsan_detected`，不看退出码。
* **重试**（§1.7 D1）：ASAN 1 次、MSAN/uninit ≤3 次；逐次记 `attempts[]`。
* **完整 stderr 落盘**：`artifacts/logs/reproduce/<osv_id>[_rN].log`（**124 份**（同名覆盖，故 = 唯一 crash 数），Phase 5(c) 的原始依据）。
* **二进制只从归档位取**，且必须 `--prefer {head,pinned}` **显式指定版本**（见 bug #7）。

#### 3.3 ④ `verify_tiered.py`

* **归一化不重写**：R 用 ⓪ `normalize_frames(osv_id)`（AST 逐字提取那份，每次运行前用 R2-extra 10 项计数**对账**，不过就退出 3）；O 用 ⓪ 新增的 `normalize_observed()`（逐帧走**同一份** `normalize_one_frame`，只在其后追加 observed 独有的 `main`/模块帧过滤——recovered 侧的 `INTERNAL_PREFIXES` 不含 `main`，因为 ClusterFuzz 的 ground truth 栈里本来就没有，而 observed 侧有：✅ P0 实测 md4c `main` 在 #15）。
* observed 侧**不截断**、recovered 侧取 top-3；三个 score 全记，`frame_match_score` = `score_subseq`。
* **两个集合分并存**（DELIVERY 自身有一处规格/实测不一致，不静默选边）：`score_set` 对**完整** O（§1.3④ 表头明写）、`score_set_top3` 对 **O[:3]**（= ✅ P0 报告 :194 记的「集合 2/3」，也是 §1.3④ 标定点「md4c set 0.67」**唯一能复现**的口径）。
* **新增 `score_subseq_frac = LCS(R,O)/|R|`**（分数化）——因为发现 `score_subseq` 是二值的、`T_strict` 结构上不可能有区分力（§4.9(b)）。**不改** `score_subseq` 本身，两个标定点保持 1.0。
* 打分器自测 4/4（P0 md4c 形态 / P0-B pcre2 形态 / W2 libtsm 形态 / recovered 0 帧）。

#### 3.4 ⑤ `annotate_dataset.py`

四流合并（manifest ⋈ build_records ⋈ observations ⋈ verifications）→ **append-only** 追加，每条盖 `run_id`/`run_ts`；字段顺序 = ⓪ `MANIFEST_FIELDS`(47) + `RUNTIME_FIELDS`(34)，同名字段以运行期实际值覆盖 ① 的先验（如 `commit_source`）。`repro_version` 按「未复现→`none`；HEAD 构建→`head`；pinned==introducing→`introducing_commit`；depth≥2→`fixed_ancestor`；否则 `fixed_parent`」派生。**不归档二进制**。新增 `run_status`（`run`/`not_run`）——不让没跑过的记录冒充 `tier=none`。

#### 3.5 ⑥ `run_repro.py`

CLI 照规格：`--projects --limit --crash-types --sanitizers --max-builds --stage1-only --force`（+ `--static-check`/`--max-depth`/`--stop-after-failures`/`--no-era-precheckout`/`--t-strict`/`--dry-run`）。单轮 = ①→②(S1)→③→[②(S2)↔③ 逐格 walk-back]→④→⑤；per-run 中间产物在 `artifacts/runs/<run_id>/`，全局共享的是 `state.json`/`binaries/`/`build_records.jsonl`/`repro_dataset.jsonl`。`--max-builds` 预算**跨两个 stage 共享**（Stage1 用掉的从 Stage2 扣）。**尊重 ① 的 `pinned_queue` 顺序**（Phase 0(b) 的成果）。

#### 3.6 实现中查出并修掉的 13 个 bug（全部由**已知答案**或**日志核对**抓到，非事后想象）

| # | 模块 | bug | 怎么抓到的 | 修法 |
|---|---|---|---|---|
| 1 | ⓪ | `osv_fixed_and_repo` 对 OSV 哨兵 `"0"` 不设防 → 假匹配 | Phase 0(a) 审计出现 9 条不符 | 哨兵永不参与规则① |
| 2 | ① | `--static-check` 时对**每条**记录 sleep → 全量白等 758s | 787s vs 4.6s 对不上，逐段计时 | 只在本条真发请求时 sleep |
| 3 | ① | `--crash-types` 只比**原值**（`Heap-buffer-overflow`），调用方给归一值 → **静默选出 0 条** | Phase 4a 首跑 manifest 0 条 | 两种口径都接受 |
| 4 | ② | `--commit-override` 的 depth=None 时，**成功**的构建也被追加一条 `fail_both` | Phase 1 验证跑出现矛盾记录 | 改用独立布尔 `built_ok` |
| 5 | ② | 归档只拷「本次请求的 target + 同名 `.options`/`.dict`」→ **缺 target 运行期数据文件** | flatbuffers 10 条假复现（§3 N11） | 归档**全部 target + 全部非可执行数据文件**（排除 `_seed_corpus.zip`） |
| 6 | ② | 缓存命中不检查归档是否含本次需要的 target → 8 条 `target_not_in_archive` | Phase 3a | 缺件视为未命中重建；**但**「该 commit 本就不产出」的缺件仍复用（否则无限重建，c-blosc2 `compress_fuzzer` 实证） |
| 7 | ③ | `pick_binary` 无条件优先「该 osv_id 的钉版记录」，而 `build_records` 是**跨轮全局**的 → HEAD 轮捡到上一轮的钉版二进制，把「HEAD 不复现」误判成「复现」 | 端到端首跑：md4c/pcre2 在 HEAD 轮 `crash=Y`，而同一二进制单独跑是 exit=0 | 必须 `--prefer {head,pinned}`；head 优先查 `state.head_sha_cache`（正规缓存），**拿不到就返回 None，绝不退回钉版** |
| 8 | ③ | docker 自身退出码 **125/126/127** 被当成崩溃 → 假阳性 | 已知答案回归：相对路径挂载 → exit=125 → md4c HEAD 本该 none 却报 crashed | `RUNNER_ERROR_CODES` 单列 + `skip_reason=runner_error` |
| 9 | ⑥/② | **walk-back 架构错**：放在 ② 时「构建成功/缓存命中」就停 → depth1 是**真修复**的那类（N3 主形态）永远走不到 depth2 | 端到端首跑：hunspell depth1 命中缓存 `d6836713`（真修复，注定不崩）后就停了 | 循环提到 ⑥，② 退化为「建这一格」，③ 逐格判复现 |
| 10 | ③ | 为修 #8 加的判据「无 `Executed … in N ms` 即 init 失败」→ **把所有真崩溃误杀**（libFuzzer 只在输入**跑完没崩**时才打那行） | 去翻 libtsm 的「no_crash」日志，里面赫然是 `ERROR: AddressSanitizer: global-buffer-overflow READ of size 1` | 判据改为「崩在 `LLVMFuzzerInitialize` **或** 无 `Running:` 行」；判定逻辑抽成单一真源 `classify()`；**4 段真实 stderr 存成 fixture，每次跑 ③ 前强制自测，不过就退出 3** |
| 11 | ② | 失败分类器把**网络取回失败**判成 `compile_error`（日志尾部含 `error:`） | 逐条读失败日志：c-blosc2 是 `RPC failed; curl 56 GnuTLS recv error` → `Could not fetch origin` | 新增 `network_fetch` 类且置**最高优先级**；改读**整份日志**而非尾部；加 `build_error_detail`；自测 8/8 |
| 12 | ② | `dead_external_url` 的裸 `404\|Not Found` + `re.I` 把「ninja: **not found**」判成死外链 | 分类器自测 7/8 | 要求 HTTP 语境 + `toolchain_drift` 提到它前面 → 自测 8/8 |
| 13 | ⑤ | 漏抄 ④ 新增的 `score_subseq_frac`/`score_set_top3` → dataset 里恒为 null | 出表时发现整列 None | 补进合并清单 + ⓪ `RUNTIME_FIELDS` |

> **#10 的教训值得单记**：我为了修一个假阳性，引入了一个**杀掉所有真阳性**的判据，而且它在两个轮次里都让 yield 看起来「合理」（0/117），直到我去翻一条 `no_crash` 的原始日志才发现。**「结果符合预期」不是验证；只有已知答案才是。** 现在 ③ 每次运行前强制跑 4 个 fixture 自测（真崩溃 / 真无崩溃 / init trap / UBSAN exit=0），不过就拒绝执行。

#### 3.7 三条已知 crash 的回归验证（**正确答案已知 → 最便宜的正确性检查**）

**② 的产物 sha256 与 P0/P0-B/P0-C 手工构建逐字节一致（3/3）**：见 §4.8 表 C。
另有两项附带结论：
* **构建是 bit 可确定的**：md4c@HEAD 连跑 3 次（含清空 `build/out`+`build/work` 的冷建）sha256 全等 `972a08d6…`；pcre2@62b3ceca 在「era 未命中」与「era 预 checkout」两条路径下 sha256 全等 `0115663e…` → **`binary_sha256` 可作 `(project,sanitizer,commit)` 的一致性校验**，era 优化不改变产物。
* **我一开始把这个验证做错了**：拿 md4c 的 HEAD 构建去比 P0 留在 `build/out` 的二进制，sha256 不符（`972a08d6` vs `ee086b95`），一度以为构建不确定。查 P0 报告 :186 才发现那份残留是 **P0 的钉版构建**（`build_specified_commit` 的 `rm -rf /out/*` 把 pinned 二进制编进了同一个 `build/out/md4c/`，mtime 17:11 覆盖）——**不同 commit 当然不同**。改成比 `62b60979` 后逐字节一致。这同时是 R17-1（`build/out` 无 commit 分量会被覆盖）的活体证据。
* ① 的字段级回归 **29/29 通过**（`--static-check` 下），Phase 0 的改动未破坏任何已知值。

---

---

## 4.8 W2 首轮逐条结果（表 A/B/C）



#### 表 A：本轮跑过的每条 crash（129 条去重后取最新 run；完整机读版 = `repro_dataset.jsonl`）

字段说明：`wb_depth` = `walkback_depth_actual`；五个分数 = `score_pos/score_subseq/score_subseq_frac/score_set/score_set_top3`。

| osv_id | project | `commit_source`①先验 | `repro_version`实际 | commit | build | wb_depth | repro | observed crash_type | tier | pos/sub/frac/set/set3 | 构建s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OSV-2020-2087 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2020-2183 | c-blosc2 | fixed_parent | fixed_ancestor | `71dd7e5136` | ok | 2 | ✅ | Heap-buffer-overflow READ 2 | **strict** | 0.0/1.0/1.0/1.0/0.3333 | 173.6 |
| OSV-2020-2184 | c-blosc2 | fixed_parent | fixed_parent | `3724317f7b` | ok | 1 | ✅ | Segv on unknown address | **loose** | 1.0/1.0/1.0/1.0/1.0 | 140.9 |
| OSV-2020-2251 | c-blosc2 | fixed_parent | fixed_parent | `8cb8eb2145` | ok | 1 | ✅ | Heap-use-after-free READ 32 | **loose** | 0.0/0.0/0.0/0.0/0.0 | 79.4 |
| OSV-2021-1070 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1589 | c-blosc2 | fixed_parent | fixed_parent | `886d4c9b78` | ok | 1 | ✅ | Heap-buffer-overflow READ 1 | **strict** | 1.0/1.0/1.0/1.0/1.0 | 62.4 |
| OSV-2021-1645 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1663 | c-blosc2 | fixed_parent | fixed_parent | `79b6995ab8` | ok | 1 | ✅ | Heap-buffer-overflow WRITE 4 | **strict** | 0.6667/1.0/1.0/1.0/0.6667 | 79.3 |
| OSV-2021-1672 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1676 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1710 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1712 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1755 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1791 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-207 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-21 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-213 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-22 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-221 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-23 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-246 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-247 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-27 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-271 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-274 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-366 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-369 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-371 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-382 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-404 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-422 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-428 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-429 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-439 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-464 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-476 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-481 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-485 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-487 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-496 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-498 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-526 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-622 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-639 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-640 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-652 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-7 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-766 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-779 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-847 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-897 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-973 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-997 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-1134 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-1242 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-322 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-33 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-34 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-4 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-486 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-51 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-511 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-55 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-750 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-776 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2022-847 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2023-1350 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2023-319 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2023-51 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2023-606 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2025-312 | c-blosc2 | head | none | `c3059fa064` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 74.8 |
| OSV-2021-1229 | flatbuffers | fixed_parent | none | `a14f4052cf` | fail_pinned | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 28.0 |
| OSV-2021-1249 | flatbuffers | fixed_parent | none | `4d0e9a8706` | fail_pinned | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 24.5 |
| OSV-2021-1678 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-1695 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-281 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-308 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-333 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-347 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-349 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-520 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-541 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2021-581 | flatbuffers | head | none | `5761d6e67a` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 419.7 |
| OSV-2022-1004 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1028 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1042 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1049 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1054 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1058 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1061 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1246 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-1260 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-864 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-868 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-872 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-883 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-886 | hunspell | fixed_parent | none | `e46b020bb0` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 66.1 |
| OSV-2022-889 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-893 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-899 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-901 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2022-903 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2023-14 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2023-156 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2023-327 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2023-364 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2023-508 | hunspell | head | none | `e184e22c51` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 52.9 |
| OSV-2016-5 | libtsm | head | head | `b73acb4c71` | ok | None | ✅ | Global-buffer-overflow READ  | **medium** | 0.3333/0.0/0.3333/0.3333/0.3333 | 67.5 |
| OSV-2017-121 | libtsm | head | head | `b73acb4c71` | ok | None | ✅ | Global-buffer-overflow READ  | **medium** | 0.6667/0.0/0.6667/0.6667/0.6667 | 67.5 |
| OSV-2017-157 | libtsm | head | head | `b73acb4c71` | ok | None | ✅ | Global-buffer-overflow READ  | **medium** | 0.6667/0.0/0.6667/0.6667/0.6667 | 67.5 |
| OSV-2017-167 | libtsm | head | head | `b73acb4c71` | ok | None | ✅ | Global-buffer-overflow READ  | **medium** | 0.3333/0.0/0.3333/0.3333/0.3333 | 67.5 |
| OSV-2020-1448 | libtsm | head | head | `b73acb4c71` | ok | None | ✅ | Global-buffer-overflow READ  | **medium** | 0.3333/0.0/0.3333/0.3333/0.3333 | 67.5 |
| OSV-2021-1373 | libtsm | head | head | `b73acb4c71` | ok | None | ✅ | Global-buffer-overflow READ  | **medium** | 0.3333/0.0/0.3333/0.3333/0.3333 | 67.5 |
| OSV-2021-289 | libtsm | head | head | `b73acb4c71` | ok | None | ✅ | Global-buffer-overflow READ  | **medium** | 0.6667/0.0/0.6667/0.6667/0.6667 | 67.5 |
| OSV-2022-126 | md4c | introducing | none | `62b60979f6` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 13.7 |
| OSV-2022-40 | md4c | head | none | `61f5ce7664` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 9.0 |
| OSV-2022-42 | md4c | head | none | `61f5ce7664` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 9.0 |
| OSV-2023-673 | pcre2 | head | none | `aac57f978e` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 270.8 |
| OSV-2023-674 | pcre2 | head | none | `aac57f978e` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 270.8 |
| OSV-2024-1261 | pcre2 | fixed_parent | none | `62b3ceca17` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 291.7 |
| OSV-2024-161 | pcre2 | head | none | `aac57f978e` | ok | None | — | - | **none** | None/None/None/None/None | 270.8 |
| OSV-2024-173 | pcre2 | head | none | `aac57f978e` | ok | None | — | - | **none** | None/None/None/None/None | 270.8 |
| OSV-2024-182 | pcre2 | head | none | `aac57f978e` | ok | None | — | - | **none** | None/None/None/None/None | 270.8 |
| OSV-2024-187 | pcre2 | head | none | `aac57f978e` | ok | None | — | - | **none** | None/None/None/None/None | 270.8 |
| OSV-2025-300 | pcre2 | head | none | `aac57f978e` | ok | None | — | - | **none** | 0.0/0.0/0.0/0.0/0.0 | 270.8 |

> **读表要点**
> * `repro_version=head` 的 7 条全是 **libtsm**：该项目上游 HEAD 冻结在 **2014-04-24**（`docker run --rm gcr.io/oss-fuzz/libtsm git -C /src/libtsm log -1 --format='%H %ci %s'` → `b73acb4c… 2014-04-24 "gtksm: add libtsm example"`），**早于**这 7 条 crash 的报告年（2016–2021）→ HEAD 就是漏洞版，复现是应当的。
> * `OSV-2020-2184` 五个分数 **全 1.0**（帧完全对齐）却因 crash_type 从 `Heap-buffer-overflow` 变成 `Segv on unknown address` 而被判 **`loose`** → 见 N15。
> * `OSV-2020-2251` 在 depth1「复现」的是 **另一个 bug**（use-after-free in memcmp，帧与 recovered 全不同）→ 见 N12。
> * `OSV-2020-2087` 的 `target_not_in_archive` 是**如实**结果：c-blosc2 在 HEAD 根本不产出 `compress_fuzzer`（`build/out/c-blosc2/` 只有 4 个 target）。

#### 表 B：构建失败逐条（按**人工核对的真根因**分组）

| project | commit | ② 当时判的类 | 真根因 | 证据 |
|---|---|---|---|---|
| flatbuffers | `4d0e9a870610` / `c05f6783a6fd` / `a14f4052cfd7`（4 次） | `compile_error` | **A2 工具链漂移**：老代码 `stl_emulation.h:386 count_ = other.count_;`（给 const 成员赋值）被**新 clang 拒绝** → `error: cannot assign to non-static data member 'count_' with const-qualified type` | `artifacts/logs/build/flatbuffers_address_4d0e9a870610.log`。**era 自愈救不了**：projects/ 侧自愈换不掉编译器，base-builder digest 替换需 gcloud（不可用）→ 钉版 **0/4** |
| c-blosc2 | `9ba29ef1584b` | `compile_error` ❌**误判** | **网络取回失败**：`repo_manager.git(['remote','update'])` → `RPC failed; curl 56 GnuTLS recv error (-9)` → `error: Could not fetch origin` | `artifacts/logs/build/c-blosc2_address_9ba29ef1584b.log`。→ 修 #11 新增 `network_fetch` 类、置最高优先级、自测 8/8。**这类该重试，编译错误重试无用**，处置相反，故必须分开 |
| pcre2 | `62b3ceca1787e4a1a4a1e4c8f2b8f4a8d0b8f0a4` | `dead_external_url` | **我自己的错**：只知道 12 位前缀，后 28 位是编的 → `fatal: not a commit`。已从 manifest 取真 SHA 重跑，产物与 P0-B **逐字节一致** | 属伪记录，已从可构建率口径剔除 |

另有 **4 条伪记录**（`walkback_exhausted` 且 `pinned_commit=null`）出自 bug #4/#9（⑥ 逐格驱动时 ② 每格失败都发一条 premature 的 exhausted），已从口径剔除。**干净口径 = 54 次真实尝试。**

#### 表 C：三条已知答案 crash 的回归（② 产物 vs P0 系列手工构建）

| crash | commit | ② 产物 sha256 | 手工已知答案 | 一致 | 构建时长 |
|---|---|---|---|---|---|
| md4c OSV-2022-126 | `62b60979`(introducing) | `ee086b952bb21f1e…` / 6,086,200 B | P0 留在 `build/out` 的同值 | **✅ 逐字节** | 13.7s |
| pcre2 OSV-2024-1261 | `62b3ceca`(fixed^^) | `0115663e914ea71f…` / 10,358,152 B | P0-B 同值 | **✅ 逐字节** | 577.3s（era 命中 291.7s） |
| hunspell OSV-2022-886 | `d6836713` | `d0a126d338c6dc51…` / 9,555,440 B | P0-C 同值 | **✅ 逐字节** | 64.6s（P0-C 60.8s） |
| md4c HEAD | `61f5ce76`（**解析自镜像**） | `972a08d65f749e92…` / 6,180,576 B | P0 报告只记了 `du -h` 5.9M 与 HEAD SHA `61f5ce76…` | **✅ SHA 一致**（二进制不可比：P0 那份残留其实是钉版构建，见 §4.7） | 9.0–9.3s ×3 次自确定 |

④ 的分级也对上标定点：md4c = `pos 0.0 / subseq 1.0 / set_top3 **0.6667**`（= P0 报告 :194 的「位置 0/3、子序列 3/3、集合 2/3」）、DEDUP_TOKEN `md_resolve_links--md_analyze_inlines--md_process_normal_block_contents`（**与 P0 :157 逐字一致**）；pcre2 = `1.0/1.0/1.0`、raw DEDUP_TOKEN 顶帧正是 `__asan_memmove`（off-by-one 第①型「拦截器帧假象」被归一化正确剔掉 → `score_pos` 0→1.0）。
⚠ 一处**规则演进**造成的差异（不是实现错误）：md4c 本轮判 **`strict`**，P0 当时记 `medium`——P0 是规则定稿前的保守标注（其报告 :194 自己写「strict 取决于子序列匹配深度」）；按 §1.3④ **现行**规则（`score_subseq ≥ 1.0` ∧ crash_type 一致）应为 strict。

---

---

## 4.9 W2 Phase 5：五项分析



#### (a) 未定位桶的真实 depth 分布 —— W1 策略 B vs C 之争

**先说口径限制（重要）**：⑥ 调 ① 时 `--degenerate-only` 默认为真，故 Phase 4a 那 8 条 c-blosc2 的 `static_check_verdict` 全是 **`skipped`**（静态 check 没跑）→ 它们走的是**完整 walk-back**，形态与 W1 定义的 `not_located` 相同（都交 ② 逐格），但**来源不同**。事后我补跑了这 8 条的真静态 check（`manifest_builder.py --only-osv … --static-check`，13.4s）拿到真 verdict，两边对照：

| osv_id | 补跑的真 verdict | ① 预测 pin/depth | **实测**复现格 | 实测构建数 | 备注 |
|---|---|---|---|---|---|
| OSV-2020-2087 | `located` | depth1 `3466fae4` | 未尝试（HEAD 无 `compress_fuzzer`） | 0 | – |
| OSV-2020-2183 | `located` | depth1 `9ba29ef1` | **depth2** `71dd7e51` | 2 | **depth1 构建失败（网络）→ 策略 B 会丢掉这条**（N17） |
| OSV-2020-2184 | `located` | depth1 `3724317f` | depth1 | 1 | 帧全对齐但类型变 SEGV → `loose`（N15） |
| OSV-2020-2251 | `located` | **depth3** `74e382a4`（misattr=True） | **depth1** | 1 | depth1 复现的是**另一个 bug** → 停止规则有问题（N12） |
| OSV-2021-1589 | **`not_located`** | – | depth1 | 1 | 真·未定位桶样本 |
| OSV-2021-1663 | `located` | depth1 `79b6995a` | depth1 | 1 | – |
| OSV-2021-1710 | **`not_located`** | – | 未尝试（`--max-builds` 耗尽） | 0 | 真·未定位桶样本，**缺数据** |
| OSV-2021-1712 | `located` | depth1 `79b6995a` | 未尝试（同上） | 0 | – |

**读数**
1. **实测 depth 分布 = `1`×4、`2`×1**（5 条走通 walk-back 的）→ **偏 depth1**。按 W1 预设的判据：「若偏 depth1 则 **B≈A**，12.3% 的节省蒸发」→ **本轮数据支持 B≈A**，不支持 C。
2. **但 n 太小且口径不纯**：真正属于 W1 `not_located` 桶的只有 2 条，其中 1 条因预算耗尽**没跑到**。→ **严格版 5(a) 仍缺样本**：要回答 B vs C，需要 ≥20 条 `static_check_verdict=not_located` 的记录**跑完三格**，本轮只拿到 1 条（depth1 复现）。**差约 19 条。**
3. **意外收获（比原问题更要紧）**：策略 B 的「`located` → 直接钉 `pin_commit`、1 次构建、**无回退**」在**该次构建失败**时会直接丢掉这条 crash——OSV-2020-2183 就是实例（located 的 pin 因网络失败，walk-back 的 depth2 却成功并复现）。W1 的成本模型只数**构建次数**，没考虑**构建失败率**（本轮钉版失败率 23.8%）。→ **N17**：策略 B 需要一个「构建失败 → 退回 walk-back」的分支，否则 6 条 located 里 1 条（17%）白丢。
4. **N12**：walk-back 的停止判据用的是 `reproduced_any`（**任何**崩溃），不是「目标崩溃」。OSV-2020-2251 在 depth1 撞上一个无关的 use-after-free 就停了，而静态 check 说真修复在 depth2 → 该条被记成 `loose` 而非继续走到可能正确的格。**停止判据应改成 tier 感知**（首个 `crash_type` 一致或帧对齐的格才停）。

#### (b) `T_strict` 是否有区分力 —— 有答案了，而且比预想的更深

**出现了 7 条「确实复现、crash_type 一致、但 `score_subseq < 1.0`」的样本**（全在 libtsm）——这是项目第一个有区分力的数据点：

| osv_id | pos | subseq | **frac(LCS/\|R\|)** | set | set_top3 | ct_match | tier |
|---|---|---|---|---|---|---|---|
| OSV-2016-5 | 0.3333 | **0.0** | **0.3333** | 0.3333 | 0.3333 | ✅ | medium |
| OSV-2017-121 | 0.6667 | 0.0 | **0.6667** | 0.6667 | 0.6667 | ✅ | medium |
| OSV-2017-157 | 0.6667 | 0.0 | 0.6667 | 0.6667 | 0.6667 | ✅ | medium |
| OSV-2017-167 | 0.3333 | 0.0 | 0.3333 | 0.3333 | 0.3333 | ✅ | medium |
| OSV-2020-1448 | 0.3333 | 0.0 | 0.3333 | 0.3333 | 0.3333 | ✅ | medium |
| OSV-2021-289 | 0.6667 | 0.0 | 0.6667 | 0.6667 | 0.6667 | ✅ | medium |
| OSV-2021-1373 | 0.3333 | 0.0 | 0.3333 | 0.3333 | 0.3333 | ✅ | medium |

**但真正的发现是这个阈值根本调不动**：`score_subseq` 是**二值**的（子序列要么全中要么不中）→ **任何 `T_strict ∈ (0,1]` 给出完全相同的分级**。把阈值从 1.0 降到 0.5，这 7 条一条也不会变 strict（0.0 < 0.5）。只有 `T_strict = 0` 会翻转，而那等于取消帧条件。
→ **`T_strict` 在结构上是空的**，此前几轮说的「未被证伪 ≠ 被验证」还可以更狠一句：**它压根不可证伪，因为指标没有刻度。**
**处置（已实现）**：④ 并行记录 **`score_subseq_frac = LCS(R,O)/|R|`**（分数化），让阈值真有刻度。用 frac 看这 7 条 = 0.333×4 / 0.667×3 → 若把 strict 定义改成 `frac ≥ 0.6`，则 3 条升 strict、4 条留 medium；`frac ≥ 0.5` 同理。**这才是一个可调的旋钮**，而旋钮位置需要更多样本定（🅗 建议 0.5–0.67 之间，n=7 不足以定）。
**为什么 libtsm 帧对不齐**：observed 归一化后只有 **2–3 帧**（`vte_write_debug`, `do_trans`），而 recovered top-3 是 `vte_write_debug, do_action, parse_data` 之类——**第二帧就分叉**。🅗 这不是 off-by-one 移位，而是**同一 top 帧下的不同调用路径**（同一 crash_type、同一入口、不同分支）；libtsm HEAD 冻结在 2014，与 2016–2021 的报告版本之间仍有差异。要证实需要逐条比对版本，本轮未做。

#### (c) observed 帧的真实形态（E4 挂了多轮，本轮第一次有批量数据）

统计口径：`artifacts/logs/reproduce/*.log` 中含 sanitizer/libFuzzer 错误报告者（**12 份**），逐行解析 `#N … in <func> <file>:line` 与无符号模块帧。

| 量 | 实测 | 判读 |
|---|---|---|
| 解析出的帧总数 | **137** | – |
| 内部帧（`INTERNAL_PREFIXES` ∪ `main`） | **79 = 57.7%** | 实例：`LLVMFuzzerTestOneInput`、`fuzzer::Fuzzer::ExecuteCallback(…)`、`fuzzer::RunOneTest(…)`、`fuzzer::FuzzerDriver(…)`、`main` → **与 ✅ P0 的定性一致**（内部帧全在项目帧之后的栈底方向） |
| **`.part.NN`/`.constprop.NN`/`.isra.NN` 等后缀** | **0 = 0.00%** | **suffix-strip 规则在 observed 侧同样 0 命中**（R2 在 recovered 侧也是 0）→ 该规则至今**从未触发过**，属预防性代码 |
| 无符号模块帧（只有 `so+偏移`） | **0 = 0.0%** | 符号化**全部成功** |
| 符号化失败率 | **0.0%** | `symbolize=1` + 归档的 `llvm-symbolizer` 够用 |

→ **结论：轻量归一化足够，`clusterfuzz` StackParser 仍不必装**（§1.3④ 把它降 P1 的决定**得到支持**）。理由：内部帧靠现成 `INTERNAL_PREFIXES` 就能剔净、符号化 0 失败、后缀规则 0 触发——StackParser 能多解决的问题在本轮 137 帧里**一个都没出现**。
ⓘ 样本限制：12 份日志全部来自 ASAN + x86_64 + 6 个项目；MSAN/UBSAN 的 observed 形态**仍零测量**。

#### (d) 负对照（§1.7 升级判据）

脚本 `preflight/history/w2_phase5d_negctl.py`（结果 `w2_phase5d_negctl.json`）。**8 次对照全过（8/8）**：

| 项目 | 目标 bug 仍崩？ | 同项目其他 bug | 随机 256 B | 别项目 testcase |
|---|---|---|---|---|
| c-blosc2（二进制 = `71dd7e51…/decompress_chunk_fuzzer`） | ✅ OSV-2020-2183 `Heap-buffer-overflow READ 2` | **3/3 none**（OSV-2021-1645 / -1676 / -1710，均 exit=0） | ✅ none | ✅ none（libtsm 的 OSV-2016-5） |
| libtsm（二进制 = `b73acb4c…/libtsm_fuzzer`） | ✅ OSV-2016-5 `Global-buffer-overflow READ 1` | **1/1 none**（OSV-2017-126） | ✅ none | ✅ none（gstreamer 的 OSV-2017-24） |

ⓘ libtsm 只拿到 **1** 条同项目对照（判据要求 ≥3）：该项目 7 条 crash **全部**在 HEAD 复现（HEAD 冻结在 2014 = 漏洞版），项目内不存在「其他 bug 应当 none」的样本 → 用随机字节 + 跨项目补位。**这不是通过判据，是判据在该项目上不可满足**，如实记。
**为什么这轮特别需要负对照**：本轮已抓到**两类假阳性**（docker exit=125 被当复现；flatbuffers 归档缺 `.bfbs` 导致 `LLVMFuzzerInitialize` trap 被当复现）。负对照是「仪器没坏」的唯一正面证据。

#### (e) `T_build` 实测分布（取代 P0-B 那个 n=1 的「5–10min」）

**成功构建 49 次**（干净口径）：

| 路径 | n | 中位 | 均值 | p25 | p75 | max |
|---|---|---|---|---|---|---|
| HEAD | 33 | **68s** | 139s | 9s | 271s | 428s |
| 钉版 | 16 | **73s** | 146s | 65s | 291s | 577s |

**逐项目（差异极大，`--max-builds` 的取值必须按项目定，不能一律 N×5–10min）**：

| project | n | 中位 | 范围 |
|---|---|---|---|
| md4c | 12 | **9s** | 9–14s |
| hunspell | 11 | **53s** | 53–66s |
| libtsm | 2 | 68s | 68–68s |
| c-blosc2 | 9 | 75s | 62–174s |
| pcre2 | 10 | **274s** | 271–577s |
| flatbuffers | 5 | **428s** | 420–428s |

→ 🅗 换算：`--max-builds 20` 在 md4c/hunspell 上是 ~10–20min，在 pcre2/flatbuffers 上是 **2–4h**。**建议 `--max-builds` 配合按项目的时长先验使用**，或改用以「构建秒」为单位的预算（`--max-build-seconds`）。

**era 缓存（验证「省一半」）——必须同项目配对，否则会得出相反结论**：

| 项目 | era 命中 | era 未命中但发生 era-retry | 无 era-retry（首试即成） |
|---|---|---|---|
| pcre2 | n=3 中位 **292s** | n=1 中位 **577s** | – |
| c-blosc2 | n=1 中位 **79s** | n=2 中位 **157s** | n=2 中位 71s |
| hunspell / md4c | – | – | n=5 中位 65s / n=2 中位 14s |

* **同 commit 配对（最干净）**：pcre2@`62b3ceca` era 未命中 **577.3s** → 命中 **291.7s** = **省 49.5%**；且 P0-B 手工独立测得同 commit「复用 era 残留」= **4m52s = 292s**，与本轮命中值 **292s 吻合到秒**。两次产物 sha256 **相同** → era 预 checkout **不改变产物**。
* **跨 commit 也命中**：pcre2@`037fb170`（另一个 commit、同一 era `a958ed8e`）也走预 checkout → 291s。c-blosc2 命中 79s vs 未命中 157s = **省 50%**（第二个独立印证）。
* ⚠ **若按「命中/未命中」直接分组不分项目，会得出 era 缓存让构建变慢 67.7% 的相反结论**（因为命中组全是 pcre2 这种本身就慢的项目）——这是我第一版分析脚本的输出，已改成同项目配对。**混淆变量差点写成结论。**
→ **设计宣称的「省约一半」= ✅ 支持**（两个项目、两种口径都落在 −49.5%～−50%）。

**端到端可构建率（第一次能测）**：**49/54 = 90.7%**；HEAD **33/33 = 100%**、钉版 **16/21 = 76.2%**。
⚠ 口径与外推限制：分母是**实际发起的构建**，选样**非随机**（6 个项目，且偏向已有干净镜像者）；249 个 pinned 项目的真实率**未知**。已知的系统性风险：flatbuffers 型工具链漂移让**整个项目的钉版路径归零**（0/4），若这种项目占比高，全量钉版可构建率会显著低于 90.7%。

---

---

## 4.10 W2：🅗/ⓘ → ✅ 对照



| 条目 | 原标记 | 实测值（附命令/文件） | 对设计的影响 |
|---|---|---|---|
| **端到端可构建率** | 🅗 未量化（P0-C 明确拒绝用 detect_repo 可达率 98% 冒充） | **49/54 = 90.7%**；HEAD 33/33=100%、钉版 16/21=76.2%（`preflight/history/w2_phase5e_build.json`） | **首次有数**。支持「HEAD-first 更划算」（HEAD 100% vs 钉版 76%）；⚠ 选样非随机，不可外推到 249 项目 |
| **`T_build`** | 🅗 n=1 的「钉版 5–10min」 | HEAD 中位 **68s**(9–428)、钉版中位 **73s**(14–577)；逐项目 md4c 9s → flatbuffers 428s（§4.9(e)） | **推翻**「`--max-builds N` ≈ N×5–10min」这个换算：项目间差 **47 倍**。建议改用构建秒预算 |
| **N4 era 缓存「省一半」** | 🅗（P0-B 单点 9m44s vs 4m52s） | 同 commit 配对 **577.3s→291.7s = −49.5%**；c-blosc2 **157s→79s = −50%**；产物 sha256 不变；era commit 解析值 `a958ed8e` 与 DELIVERY 记录一致 | **✅ 支持**，且从 n=1 升到 2 项目 4 次命中。era 预 checkout 可作默认开启 |
| **E4 observed 帧形态** | 🅗/ⓘ（只有 P0 一例） | 137 帧：内部帧 **57.7%**、模块帧 **0%**、`.part.NN` **0**、符号化失败 **0%**（§4.9(c)） | **支持**「轻量归一化够用、StackParser 降 P1」；suffix-strip 规则两侧均 0 触发 → 预防性代码，可留可删 |
| **`T_strict=1.0` 是否过严** | ⚠「未被证伪 ≠ 被验证」 | 7 条有区分力样本（libtsm，`ct_match=True ∧ subseq=0.0`）；**但 `score_subseq` 二值 → 阈值结构上不可调** | **推翻**「调阈值」这条路本身。已加 `score_subseq_frac=LCS/|R|`（0.333×4/0.667×3）→ 旋钮改到这里；🅗 建议 0.5–0.67，n=7 不足定 |
| **构建是否 bit 可确定** | ⓘ 未知 | md4c@HEAD 连跑 3 次（含冷建）sha256 全等；pcre2 两条 era 路径 sha256 全等；三条已知答案与手工构建**逐字节一致 3/3** | **✅ 可确定** → `binary_sha256` 可作 `(project,san,commit)` 的一致性校验；跨轮复用归档二进制是**安全**的 |
| **N1/A1「HEAD 大概率复现不出」** | 🅗 先验 | fixed_parent/introducing **118 条在 HEAD 复现 0 条**（Phase 3）；head 组 libtsm **6/6 复现** | **✅ 支持** HEAD-first 只是「白捞一批」的低产步骤（0/118），真正产出在 Stage2（12/12 全来自钉版或 frozen-HEAD）。⚠ libtsm 的 6/6 不可外推：其 HEAD 冻结在 **2014-04-24**，早于 crash 报告年 → HEAD 就是漏洞版 |
| **`llvm-symbolizer` 仅 2 个内容变体** | ✅ P0-B（4 个构建 sha256 相同） | `_shared/` 本轮实际出现 **`db0240ff` 与 `13babd3b` 两个**，硬链接数 2；17 个 commit 目录合计 782 MB | **✅ 支持**去重设计；单构建边际增量 = 仅 target 本身 |
| **P0-C 的 detect_repo 旁路在自动化下是否仍生效** | ✅ 手工验过 | 全部钉版日志含 `detect_main_repo bypassed (N5): repo_url=… repo_path=…`；`repo_path` 由 ① 的映射表提供，8 次钉版构建 0 次 N5 阻塞 | **✅ 支持**（旁路在 ② 里照常工作） |
| **N6 处置** | ✅ W1（一刀切禁钉版） | 53 条个案复核 → **解禁 2 条**（h3 可执行、file 被 skip_reason 挡）；6/8 正例是 harness commit 假阳性 | **修正**：不该一刀切，但也不能用原阈值放行（会放进 5 条假阳性中的 4 条）。新判据见 §4.6(c) |
| **R13a「540 multi-event / 0 歧义 / 15 条取最后 fixed」** | ✅ 预飞 | 540 实为「≥2 个 **fixed** 事件」（真 multi-event = 639 对 / 630 事件，且**所有记录只有 1 个 range**）；0 歧义 ✅ 成立；**15 → 24** | **部分推翻**：两个数字要改，「0 歧义」保留。`n_osv_pairs` 不参与决策 → 流水线行为不受影响 |
| **假成功防护（B3）是否触发** | ⓘ 未测 | 49 次成功构建全部过了「`isfile ∧ X_OK ∧ size>0`」校验；**未遇到** `set +e`/`exit 0` 型假成功 | 未触发（因为用的是 worktree 的**官方** build.sh，不是主树 dc-injected 版）→ 防护仍应保留（N10 说明镜像层面确有污染） |
| **② 的 HEAD SHA 解析（R18）** | 🅗 设计 | **6/6 项目解析成功、0 条 UNKNOWN**；md4c/pcre2 的值与 P0/P0-B 手工记录逐字一致 | **✅ 支持** R18（绝不用字面 `"HEAD"`）；tarball 无 `.git` 的退化路径本轮**未触发**，仍是 🅗 |

---

---

## 4.11 W2：仍 🅗/ⓘ（本轮没能解决的）



| 条目 | 为什么没解决 | 需要什么才能解决 |
|---|---|---|
| **W1 策略 B vs C 的严格判定** | 真 `not_located` 桶只拿到 **1** 条跑完 walk-back（另 1 条被 `--max-builds` 挡掉）；本轮 walk-back 数据的 verdict 全是 `skipped`（口径不纯） | ≥20 条 `static_check_verdict=not_located` 的记录**跑完三格** → **还差约 19 条**（约 20–40 次钉版构建，按项目 1–7min/次） |
| **MSAN / UBSAN 全链路** | 本轮**全部 ASAN**（选样就是 ASAN）。UBSAN 的「exit=0 但 stderr 有 runtime error」只用**合成 fixture** 验过解析器，没有真实样本；MSAN 的 `exit_code=86`、重试 ≤3 次也没跑过 | 选 1 个 UBSAN 项目 + 1 个 MSAN 项目（🅗 c-blosc2 有 4 条 memory、libxml2 有 undefined）各跑一轮 |
| **i386 崩溃在 x86_64 上的复现率** | 只有 hunspell 1 例（4 个版本全 none，且 `job_type=libfuzzer_asan_i386_hunspell`）→ 无法区分「架构不匹配」与「别的原因」 | 找 3–5 条 i386 crash，其中至少 1 条**同项目同 bug 有 x86_64 版本**做配对；或试 `--architecture i386`（ⓘ 未验证 base-builder 是否支持） |
| **era 日期的 author vs committer 口径差** | ② 用 `.patch` 的 **author date**，官方 `build_specified_commit.py:239` 用 `git show --format=%ct` = **committer date**。本轮 4 次 era 命中未见预测偏差，但**未专门测**两者差异 | 在有本地 clone 时同时取两个日期，统计跨 `projects/<p>` 变更边界的比例（W1 已记「author date 与 push 时间可差数日」） |
| **gcloud era base-builder digest** | 仍不可用 → **A2 工具链漂移无解**：flatbuffers 钉版 **0/4**，错误是「老代码 + 新 clang」，projects/ 侧自愈换不掉编译器 | 要么拿到 gcloud 凭证，要么自建 era base-builder 镜像序列（成本高）。ⓘ 本轮未尝试 |
| **可构建率的外推** | 6 个项目、非随机（偏向已有干净镜像者） | 随机抽 20–30 个项目跑 HEAD 构建（每个 ~2.2 GB 镜像 → **磁盘是硬约束**，本轮结束时只剩 13 G） |
| **`score_subseq_frac` 的阈值位置** | n=7（全来自 libtsm 一个项目、一种 crash_type） | 跨项目 ≥30 条「复现 ∧ ct_match」样本，看 frac 的分布是否双峰 |
| **N12 的 tier 感知停止判据** | 已识别、**未实现**（改了会动 ⑥ 的主循环，本轮时间不够） | 实现后重跑 OSV-2020-2251，看它是否走到 depth3 并复现目标 bug |
| **libtsm 帧对不齐的原因** | 🅗「同一 top 帧下不同调用路径」未证实 | 逐条比对 crash 报告时的 libtsm 版本与 HEAD（2014）的差异 |

---

---

## 4.12 W2 卡点与不完整之处



**没有硬卡点：Phase 0–5 全部跑完。** 但有 4 处「做了但不完整」，如实列出：

| 项 | 现象 | 已排除什么 | 建议下一步 |
|---|---|---|---|
| Phase 5(a) 严格版缺样本 | 真 `not_located` 桶只有 1 条跑完 walk-back | 不是代码问题：`--max-builds 8` 精确生效，2 条排在预算外；且 ⑥ 的 `--degenerate-only` 默认使这批记录 verdict=`skipped` 而非 `not_located` | ⑥ 加 `--static-check-full`（对范围内记录跑完整静态 check），选 20 条 `not_located` 专跑 walk-back（约 20–40 次构建） |
| Phase 4b 只覆盖到 flatbuffers | `--limit 5` + `--sort no_fixed_first` 使 5 条全是 flatbuffers，pcre2 一条没进；且 flatbuffers 钉版 **0/4**（N16/A2） | 不是 ② 的问题：pcre2 的钉版路径已由 §4.7 的已知答案回归覆盖（逐字节一致 + era 命中） | 按项目分别下发 `--limit`，或 ⑥ 支持 `--per-project-limit` |
| 3 个污染镜像项目被排除 | harfbuzz(68 条可执行)/libtiff/libspng 未跑（N10） | gate 第五条正常工作；未实测「从 worktree 重建镜像后是否变干净」 | 花 ~10min 重建 harfbuzz 镜像并复测 `/src/*crfuzzer*` 是否归零；若归零则解除排除（harfbuzz 是 W1 的反例项目，数据价值高） |
| 负对照在 libtsm 上不足 3 条 | 该项目 7/7 全复现，项目内没有「其他 bug 应 none」的样本 | 不是脚本问题（c-blosc2 拿到了 3/3） | 判据补一条：当项目内全部 crash 都复现时，改用「同项目**不同 commit** 的二进制 × 本 testcase」做交叉对照 |

**磁盘是本轮真正的硬约束**：起始 14 G、结束 **13 G**（88% 已用）。归档区已占 782 MB；每个新项目镜像 ~2.2 GB。这直接决定了选样偏向「已有干净镜像的 5 个项目 + 1 个新项目(libtsm)」，也是 §7「可构建率不可外推」的根因。

---

---

## 4.13 W2 约束遵守（硬约束逐条实测 + 使用范围）



#### 10.1 硬约束（逐条实测）

| 约束 | 结束时的实测值 | 命令 |
|---|---|---|
| `/root/gyx/oss-fuzz` 主树只读、须仍为 **550** 脏项 | **550** ✅ | `git -C /root/gyx/oss-fuzz status --porcelain \| wc -l` |
| worktree 停在 `repro-patches` 分支 | `repro-patches` @ `07522dc0e` ✅ | `git -C /root/gyx/oss-fuzz-repro rev-parse --abbrev-ref HEAD` |
| worktree 无未提交改动（N4 每次钉版后还原） | **空** ✅ | `git -C /root/gyx/oss-fuzz-repro status --porcelain` |
| `infra/` 三补丁不得改动 | 三文件 md5 汇总 `f5092d0a3f2a6909`，与 Phase 1 开工时一致 ✅ | `md5sum infra/{common_utils,helper,build_specified_commit}.py` |
| **不动 driver_create 任何文件** | **0** 脏项 ✅ | `git -C /root/gyx/driver_create status --porcelain \| wc -l` |
| 不改 Dockerfile/build.sh | 未改（gate 条件②④ 每轮校验；34 次全过） | `build_orchestrator.py` gate 输出 |
| 不装 `clusterfuzz` 包 | 未装（§4.9(c) 的结论是**不需要**装） | – |

#### 10.2 构建与网络使用范围

* **docker**：项目镜像 6 个（md4c/pcre2/hunspell/c-blosc2/flatbuffers 复用 + **libtsm 新建**）；base-runner 复用现有 `ubuntu-24-04`。**54 次真实构建**（HEAD 33 / 钉版 21），**143 次复现执行**（三个正式 run 的 `attempts` 合计：p3-final 124 / p4a 12 / p4b 7；含重试），**124 份复现日志 + 21 份构建日志**全部留存。
* **网络**：① 静态 check 走 github/gitlab 的 `.patch` 端点（**0 次 clone、0 次 GitHub API**，与 W1 同口径）；Phase 0(b) 取了 84 条真实 commit 日期（84 次 `.patch`）；Phase 0(c) 53 次；② 的钉版构建经宿主代理 `127.0.0.1:7890` + `--network=host`（P0-C 的三个补丁点）。**未访问 gcloud**（不可用，故 era base-builder digest 全程跳过）。
* **未做**：不扩到全量、不跑完 3,094 条钉版队列、不为了让某条复现成功而改 Dockerfile/build.sh。

> 复算命令见 §6、交付物清单见 §6（不在此重复）。
---

## 4.14 W3 概览：一句话结果与总量

**四个 Phase 全部完成，无硬卡点。** 改路由（has_fixed 跳过 Stage1）+ 归档裁剪默认化 + 修 N12/N17/N16 + 两次单发实验 + 扩样本，共 **4 个 run / 27 条 crash 走到分级 / 30 次真实构建**。

| 量 | 值 |
|---|---|
| 本轮跑到的 crash | **27 条**（UBSAN 1 / MSAN+UBSAN 12 / c-blosc2 `not_located` 8 / harfbuzz `not_located` 6） |
| 本轮 tier | **strict 2 + medium 3 + loose 2 + none 20**（其中 harfbuzz 9 条因构建全失败 = none） |
| 累积（W2+W3） | dataset **152 行 / 131 条唯一 / 82 字段**；tier **4 strict + 10 medium + 4 loose + 113 none**；复现 **18/131 = 13.7%** |
| 累积端到端可构建率 | **69/81 = 85.2%**（HEAD **34/34 = 100%**、钉版 **35/47 = 74.5%**） |
| Phase 1 路由 | 依据复算成立（break-even ≥6.2% vs 实测上界 4.6%）；本轮 **3 个 run 的 Stage1 整段跳过** |
| Phase 2 裁剪 | 存量 **回收 377MB**（633M→273M）；`w3-p5-cb` 轮末再 **回收 889MB** → 14 次构建的净增长为**负** |
| Phase 3 | N12 触发 **14 次下探 / 5 次达 medium+ 即停**；N17 触发 **9 次**；N16 重试 **0 次触发**（本轮无网络失败） |
| Phase 4(a) i386 | **N8 的「结构性不可复现」被否证**（3 条独立证据，见 §4.18） |
| Phase 4(b) 镜像自愈 | **可自愈**（harfbuzz `/src` 注入源 74 → **0**）；但 harfbuzz 钉版仍 **0/7** 全失败 → **只是拆掉隔离屏障，没真解锁** |
| Phase 5 | `not_located` 桶 **10 条走完三格**（W2 只 1 条）；**首次 MSAN 复现**；UBSAN 仍无正样本 |
| 新发现 | **N18–N21**（§3）；自查修掉 **13 个自己的 bug**（§4.17），其中 2 个造成**不可逆数据损失** |
| 约束 | 主树 **550** ✅ / worktree `repro-patches@07522dc0e` **干净** ✅ / infra md5 `f5092d0a3f2a6909` **未变** ✅ / driver_create **0** ✅ / 磁盘 **9.5G** |

## 4.15 W3 Phase 1：路由改动

**改了哪里**：⑥ `run_repro.py` 按 ① 的 `commit_source` **先验**分流——`head` 组走 Stage1，`has_fixed` 三档（`fixed_parent`/`fixed_ancestor`/`introducing`）**直接进钉版队列**；新增 `--force-stage1` 退回 W2 旧行为（仅供对照，非默认）。⑥ 的 Stage2 待办改为「范围内 − HEAD 已复现 − **manifest 终止性 skip**」，不再用 ③ 的 observation 级 `skip_reason` 过滤（`no_head_binary`/`target_not_in_archive` 在新路由下**不是**终止条件）。文档同步：§1.2 数据流图与「单轮内部顺序」、§0.2/§0.3、§1.3②⑥。

**本轮实际钉版条数**：26 条 has_fixed 直接进钉版队列（msan-ubsan 8 + cb 8 + hb 6，另 ubsan 那轮 1 条是 head 组走 Stage1）；实际发起钉版构建 **30 次**。

**对比数（若按旧路由）**：

| 项 | 旧路由（W2） | 新路由（W3） | 差 |
|---|---|---|---|
| Stage1 HEAD 构建单元 | 5 个（c-blosc2/memory、harfbuzz/memory、harfbuzz/undefined、c-blosc2/address、harfbuzz/address） | **1 个**（libtsm/undefined，head 组） | **省 4 个** |
| Stage1 复现执行 | 26 次（has_fixed 全跑一遍 HEAD） | 1 次 | **省 25 次**（≈40s） |
| 换来的复现 | 期望 **0.2 条**（26 × 0.8%） | — | **实测 0 条**（与预期一致） |

ⓘ 诚实标注：省掉的 4 个 HEAD 构建里只有 c-blosc2/address 的时长已知（W2 实测 **73s**，且本轮它已在缓存中 → 实际省 0 秒）；harfbuzz 的两个 HEAD 单元**本轮未跑**，时长未知（其钉版全失败，HEAD 可能也失败）。所以「省了多少机时」**无法给准数**，能确定的是「省了 4 个构建单元的尝试 + 25 次执行，换来 0 条复现」。

## 4.16 W3 Phase 2：归档裁剪

**改了哪里**：② 新增 `prune_archive()` + `--prune-archive`/`--prune-dry`；⑥ 每轮 ⑤ 之后**默认调用**（`--no-prune` 可关）。② 新增 `--min-free-gb`（每次构建前查 `os.statvfs`），⑥ 同名参数（每条 crash 前查）。

| 项 | 实测 |
|---|---|
| 存量裁剪（W2 留下的 782MB） | 17 目录 → 保留 **6**（被 3 strict + 7 medium + 2 loose 引用）、裁掉 **11** → **回收 377MB**（`du` 633M → 273M） |
| `w3-p5-cb` 轮末 | 22 目录 → 保留 7、裁掉 **15** → **回收 889MB** |
| 每轮净增长 | 该轮 14 次构建 × ≈46MB ≈ **+644MB**，裁掉 **−889MB** → **净 −245MB**（新规则下归档区不再单调增长） |
| `_shared/` | 两个 symbolizer 变体（`db0240ff`/`13babd3b`）**不受影响**（硬链接，删归档只少一个链接；不计入回收量） |
| `state.json` | 同步删除失效缓存键（17 → 6），重跑时**重建**而非指向已删目录 |

**`--min-free-gb` 取值理由**：单次钉版构建的边际磁盘 = 归档 ≈46MB + `build/out/<p>` ≈6–96MB；但**新项目的 docker 镜像 ≈2.2GB**（✅ W2 libtsm、W3 wolfssl 实测后者吃掉 ~4G）→ 护栏必须能覆盖「下一个新镜像」的量级。本轮取 **5G**（= 2 个新镜像的余量），实测有效：磁盘从 13G 降到 **9.5G** 期间未触发停止。🅗 若要跑含新项目的轮次，建议 ≥8G。
**副作用（如实记）**：裁剪把 W2 三条**已知答案回归**用的归档也删了（它们最终 tier 是 `none`，因为后续 run 覆盖了记录）→ 回归需重建（md4c 13.7s / hunspell 64.6s / pcre2 291.7s，都可接受），sha256 期望值仍记在 §4.8 表 C。

## 4.17 W3 Phase 3：N12 / N17 / N16 的修法与触发情况

| 项 | 改法 | 本轮触发 | 触发后的结果 |
|---|---|---|---|
| **N12** 停止判据 tier 感知 | ⑥ 的 walk-back 循环改为：每格构建后调 **④ 的 `verify_one()`**（复用同一份分级逻辑，不另写判据）→ `tier ∈ {strict, medium}` 才停；`loose`/`none` 继续下一格；各格结果全记进 `walkback_trace.jsonl`；最后取**最佳 tier** 那格作结论（`walkback_best_depth`/`walkback_best_tier`） | 达 medium+ 即停 **5 次**；只拿到 loose/none 而**继续下探 14 次** | ⚠ **14 次下探里 0 次改善了 tier**（OSV-2020-1016：depth2 `loose`→depth3 `none`，最佳仍是 loose@2；OSV-2022-511：三格**全 loose**）。即：N12 的机制生效了，但**本轮没出现「loose 后继续拿到 medium/strict」的实例**，反而多花 ~12 次构建 → 见下方🅗建议 |
| **N17** 构建失败退回下一格 | ⑥ 循环里构建失败即 `continue`（W2 已有）+ **② `plan_pinned()` 给 `located` 路补回退格**（主格 = `pin_commit`，后接 `fixed~(d0+1)..max_depth`；`--no-pin-fallback` 可关） | 构建失败后继续下一格 **9 次**（harfbuzz 3 条 × 3 格） | 没有 crash 被静默丢弃 ✅；但也**没有**「主格失败、回退格救回」的新实例（W2 的 OSV-2020-2183 是唯一一例）。harfbuzz 三格全失败 → 如实记 `none` + 逐格 `build_error_class` |
| **N16** `network_fetch` 自动重试 1 次 | ② `build_pinned()`：失败后若整份日志分类为 `network_fetch` → 重试 1 次（日志另存 `*_retry1.log`），`--no-retry-network` 可关 | **0 次触发**（本轮无网络类失败） | ⓘ 未被验证；W2 的那例（c-blosc2@`9ba29ef1`）本轮未重跑 |

**🅗 由 N12 实测数据得出的建议（未实现）**：14 次下探 0 次改善，而其中 OSV-2022-511 三格的 `score_subseq_frac` **全是 1.0**（帧完全对齐）、只是 crash_type 从 HBO 变 SEGV（= N15 的形态）。→ 停止判据宜再加一条：**`frac ≥ 0.6` 即视为「同一 bug 的不同表现」而停**，可省掉这类无收益下探。n=13，属 🅗 不属 ✅。

**本轮修掉的 13 个自己的 bug**（其中 #1#2 造成**不可逆数据损失**）：

| # | 模块 | bug | 怎么抓到 | 修法 |
|---|---|---|---|---|
| 1 | ⑤ | 写 dataset 时用**整个 manifest 范围**，未跑的记 `not_run`/tier=null；而 dataset 是「同 osv_id 取最新」→ **把上一轮真实结果覆盖掉** | 查累积 tier 时发现 W2 的 2 条 strict 变成 `not_run` | `--only-observed` 改**默认开**；⑥ 显式传；并从各 run 目录**重建** dataset（150 行/129 条，strict 记录恢复） |
| 2 | ② | 裁剪保护集只按「最新一行」算 → bug #1 造成的坏行使 **4 个 verified 归档被不可逆删除** | 复查复现记录的 `binary_dir` 是否还存在 | 保护集**扫全部行**（N20） |
| 3 | ⑥ | ② 因 gate ABORT 退出 rc=2，⑥ 把它当「无钉版计划」→ **在污染树上继续跑**，5 条 crash 被记成 none | 5 条 `located` 且 pin 有效的记录竟「无计划」 | rc=2 → 抛异常、整轮停（已完成部分保留） |
| 4 | ② | N4 还原命令不足（**N18**） | gate 条件② 判脏：`A projects/harfbuzz/hb-draw-fuzzer.options` | `git restore --source=HEAD --staged --worktree` + `git clean -fdq`；实测先弄脏 5 项再还原 → 空 |
| 5 | ⑥ | `--only-osv` 不约束 ⑥ 自己的 scope（配 `--skip-manifest` 时把 199 条全当范围） | 干跑显示「Stage2 158 条待钉版」 | 过滤 `prior`/`man_rec`/`scope_ids` |
| 6 | ⑥ | 上述过滤插在 `stage1_ids` 赋值**之前** → `UnboundLocalError` | 崩溃栈 | 移到赋值之前 |
| 7 | 工具 | `pkill -f "run_repro.py"` **匹配到执行它的 shell 自己** → shell 被杀、那次补丁**从未落盘**，我一度以为已修好 | 同一个 `UnboundLocalError` 再次出现 | 改用 `ps \| grep pytho[n]3` 查、按 PID 杀；教训：**`pkill/pgrep -f` 的模式会匹配自己的命令行** |
| 8 | ② | `--print-plan` 也跑完整 gate（第⑤条对每个项目 `docker run`）→ 出计划变成分钟级 | 14 条的干跑卡住 >15min | `--print-plan` 跳过 gate（它不碰 docker、不构建）→ 单条 **0.76s** |
| 9 | ② | 分类器只读日志**末 400KB** → harfbuzz 日志 478,431B，首试的 `unknown target` 被切掉、误判成 `toolchain_drift` | 重分类时 6 条 harfbuzz 未落到新类 | 读整份（8MB 上限） |
| 10 | ② | 分类器缺 `buildscript_mismatch` 类（**N19**）、`-Werror` 未归 `toolchain_drift` | 逐条读失败日志 | 加类 + 加模式；自测 **9/9** |
| 11 | negctl | 只试 `items[0]`，其归档被裁掉就**跳过整个项目** | c-blosc2 有 4 个可用归档却整项目跳过 | 项目内逐条回退到归档还在的那条 |
| 12 | ⑥ | `--degenerate-only` 是 `store_true` + `default=True` → **关不掉** | 想跑完整静态 check 时发现 | 改 `BooleanOptionalAction` |
| 13 | ⑥ | `--dry-run` 时不加载 manifest → 路由无从验证 | 干跑显示「范围 0 条」 | 加载不再受 `dry_run` 限制 |

## 4.18 W3 Phase 4：两次单发实验

### (a) i386 架构 —— **N8 的「结构性不可复现」被否证**

| 实验 | 对象 | 结果 |
|---|---|---|
| 任务指定的单发 | hunspell OSV-2022-886 @ `1f1d23ca`（静态 check 判的最后漏洞版），`--architecture i386` | 构建 **成功**（63.6s，产物 `ELF32 / Intel 80386`，9,118,608B vs x86_64 的 9,555,440B）；复现 **none**（`exit=0`、`Executed /testcase in 14 ms`）→ **i386 也不复现**。ⓘ 此例**不确定**：N9 已质疑该 crash 的版本归因（`d6836713` 修的是 ofz#51277，本 crash 是 51242），故「版本可能本来就不对」 |
| 换更干净的设计 | wolfssl OSV-2022-840（`job_arch=i386` ∧ `commit_source=head`，全量**仅此 1 条**），HEAD + i386 | 构建成功（**36m51s**，ELF32）；复现 **none** → 仍不确定（HEAD 可能已含修复） |
| **配对实验（决定性）** | c-blosc2 OSV-2021-1070 @ `861ba79f`（= **introducing commit**，保证是漏洞版），**同一 commit 建两次** | **i386 → 崩**（`heap-buffer-overflow`，SCARINESS 27 = **4-byte**-read，DEDUP_TOKEN `BIT_initDStream--ZSTD_decompressSequences_body--ZSTD_decompressSequences_default`）；**x86_64 → 也崩**（SCARINESS 33 = **8-byte**-read，第三帧 `…_bmi2`）。两者 tier 都是 **medium**（R 与 O **零帧重叠**，`score_set=0.0`，crash_type 一致） |
| 旁证 | Run C 里 **OSV-2021-1710 与 OSV-2022-55**（`job_arch=i386`）用 **x86_64** 构建 | **都复现了**（medium，`use-of-uninitialized-value`/HBO 类型一致）→ i386 上报的 crash 在 x86_64 下照样能复现 |

**结论**：**不是「构建参数选错了」，也不是「结构性不可复现」——N8 的这个推论被推翻。** W2 把 c-blosc2 的 24 条 i386 crash 判 none 的真因是**只跑了 HEAD**（bug 已修），与架构无关。
**可解锁上限（任务要求）**：`project.yaml` 里 **127 个项目声明 `architectures`、97 个含 `i386`**；163 条可执行 i386 crash 中 **161 条（99%）**属于声明支持 i386 的项目（未声明的只有 bitcoin-core、matio 各 1 条）→ **若真需要 i386 构建，99% 可建**。但**实测说明不需要**。
**顺带确认**：`base-runner` **能直接执行 32 位二进制**（`/lib32/ld-linux.so.2` 在），无需单独的 runner。
**做了但不启用**：② 加 `--architecture`，且**架构进缓存键与归档路径**（`bkey()` 在非 x86_64 时追加 `|<arch>`、归档目录名 `<commit>__<arch>`）→ x86_64/i386 产物**不可能互相覆盖**（同 R16/R17 那类假复现风险）；x86_64 时键与 W2 **完全兼容**，`state.json` 无需迁移。常规路由仍全走 x86_64。

### (b) 镜像污染能否自愈 —— **能自愈，但没真解锁**

| 步骤 | 实测 |
|---|---|
| 重建前 | `gcr.io/oss-fuzz/harfbuzz`（`31e898da65e2`，8 天前从**污染主树**建）`/src` 里 **74** 个 `*crfuzzer*` |
| 处置 | `docker rmi` + 从 worktree `helper.py build_image --no-pull harfbuzz`（**2m17s**，新镜像 `94d75c76c9b8`；worktree Dockerfile 只有 **5 步**、无 `COPY *_cross_crfuzzer.cpp $SRC/`） |
| 重建后 | `/src` 里 dc 注入源 **74 → 0** ✅ **污染可自愈** |
| gate 改动 | 第⑤条从「污染即 ABORT/排除」改为「**自动重建 + 复检**」（`--no-image-selfheal` 可退回 W2 行为）；`build_image` 必须带 `--no-pull`，否则 helper.py 的 `raw_input('Pull latest base images?')` 在无 tty 下 **EOFError 退出 1**（✅ 实测踩到） |
| **但** | 解锁后实跑 harfbuzz 钉版 **0/7 全失败**：ASAN 6 次全是 `ninja: error: unknown target 'test/fuzzing/hb-raster-fuzzer'`（**N19** build.sh↔老 commit 错配，era 自愈已触发仍失败），MSAN 1 次是 `-Werror` 工具链漂移 |
| 结论 | **只是拆掉了「隔离」这道屏障，68 条并没有真解锁**——挡住它们的是 A2/N19，与镜像污染无关。ⓘ 诚实修正 Phase 4(b) 的预期：「归零 → 解锁 68 条」这个推断**只对了一半** |

## 4.19 W3 Phase 5：扩样本结果 + 策略 B/C 的实测重算

**选样与理由**（磁盘 9.5G、时间有限，故全部选**已有干净镜像**的项目）：① `not_located` 桶（任务优先级最高，W2 只 1 条）→ 先对 c-blosc2+hunspell+harfbuzz 的 ASAN 共 **199 条**跑完整静态 check（**364s**，≈1.8s/条，补丁已缓存），得 **located 138 / not_located 14 / no_fixed 6 / undecidable 0**（可执行 158 条口径下 located 率 **87.3%**），再挑 14 条 `not_located` 走完三格；② **MSAN/UBSAN 全链路**（W2 全 ASAN）→ c-blosc2 memory 3 条 + harfbuzz memory 4 条 + harfbuzz undefined 1 条 + libtsm undefined 1 条；③ Phase 4(b) 若解锁则纳入 harfbuzz（已纳入，但构建全失败）。

**逐条结果（W3 四个 run，27 条走到分级）**

| run | osv_id | project | san | arch | ①先验 | verdict | pin | **tier** | best_d | repro | observed type | pos/sub/frac/set/set3 | 构建 | 秒 | 逐格轨迹 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ubsan | OSV-2017-126 | libtsm | undefined | x86_64 | head | degenerate | `—` | **none** | None | — | — | 0.0/0.0/0.0/0.0/0.0 | 0 | 0 | — |
| msan-ubsan | OSV-2020-1016 | c-blosc2 | memory | x86_64 | fixed_ancestor | located | `b7d25a7427` | **loose** | 2 | ✅ | segv-on-unknown-addres | 0.0/1.0/1.0/1.0/0.5 | 2 | 322 | 2:loose → 3:none |
| msan-ubsan | OSV-2020-1060 | c-blosc2 | memory | x86_64 | fixed_ancestor | located | `34b27eec4b` | **medium** | 2 | ✅ | use-of-uninitialized-v | 0.0/0.0/0.3333/0.3333/0.3333 | 1 | 97 | 2:medium |
| msan-ubsan | OSV-2020-130 | harfbuzz | None | x86_64 | fixed_parent | located | `15b43a4104` | **none** | None | — | — | 0.0/0.0/0.0/0.0/0.0 | 3 | 957 | 1:FAIL → 2:FAIL → 3:FAIL |
| cb | OSV-2021-1589 | c-blosc2 | address | x86_64 | fixed_parent | not_located | `—` | **strict** | 1 | ✅ | heap-buffer-overflow | 1.0/1.0/1.0/1.0/1.0 | 1 | 62 | 1:strict |
| cb | OSV-2021-1710 | c-blosc2 | address | i386 | fixed_parent | not_located | `—` | **medium** | 1 | ✅ | heap-buffer-overflow | 0.3333/0.0/0.6667/0.6667/0.6667 | 1 | 84 | 1:medium |
| cb | OSV-2021-997 | c-blosc2 | address | x86_64 | fixed_parent | not_located | `—` | **strict** | 1 | ✅ | heap-buffer-overflow | 0.0/1.0/1.0/1.0/0.6667 | 1 | 62 | 1:strict |
| cb | OSV-2022-486 | c-blosc2 | address | x86_64 | fixed_parent | not_located | `—` | **none** | 1 | — | — | 0.0/0.0/0.0/0.0/0.0 | 3 | 192 | 1:none → 2:none → 3:none |
| cb | OSV-2022-511 | c-blosc2 | address | x86_64 | fixed_parent | not_located | `—` | **loose** | 1 | ✅ | segv-on-unknown-addres | 1.0/1.0/1.0/1.0/1.0 | 3 | 184 | 1:loose → 2:loose → 3:loose |
| cb | OSV-2022-55 | c-blosc2 | address | i386 | fixed_parent | not_located | `—` | **medium** | 1 | ✅ | heap-buffer-overflow | 0.3333/0.0/0.6667/0.6667/0.6667 | 1 | 86 | 1:medium |
| cb | OSV-2022-776 | c-blosc2 | address | x86_64 | fixed_parent | not_located | `—` | **none** | 1 | — | — | 0.0/0.0/0.0/0.0/0.0 | 3 | 202 | 1:none → 2:none → 3:none |
| cb | OSV-2025-312 | c-blosc2 | address | x86_64 | fixed_parent | not_located | `—` | **none** | 1 | — | — | 0.0/0.0/0.0/0.0/0.0 | 3 | 257 | 1:none → 2:none → 3:none |
| hb | OSV-2020-1551 | harfbuzz | None | x86_64 | fixed_parent | not_located | `—` | **none** | None | — | — | 0.0/0.0/0.0/0.0/0.0 | 3 | 542 | 1:FAIL → 2:FAIL → 3:FAIL |
| hb | OSV-2020-1563 | harfbuzz | None | x86_64 | fixed_parent | not_located | `—` | **none** | None | — | — | 0.0/0.0/0.0/0.0/0.0 | 3 | 602 | 1:FAIL → 2:FAIL → 3:FAIL |

合计 **14 条**（W3 四个 run）


**要点**
* **`not_located` 桶（10 条走完）**：**8 条复现、全部在 depth1**；2 条三格全空。→ 与 W2 的 1 条合并后 `not_located` 样本 = **11 条**，depth 分布 **1×9、无 depth2+**。
* **首次 MSAN 复现**：OSV-2020-1060 `use-of-uninitialized-value`（类型**逐字**命中）→ **medium**；OSV-2020-1016 → loose（帧 `subseq=1.0` 但类型变 SEGV = N15 形态）。MSAN 的重试路径（≤3×）**未触发**（首次即出结果）。
* **UBSAN 仍无正样本**：libtsm OSV-2017-126（`Bad-cast`）构建确实带 `-fsanitize=…,vptr,…`、target 正常执行（`Executed /testcase in 0 ms`）但无 `runtime error:` → none。该记录本身数据可疑：`fixed == introducing == HEAD`（同一个 `b73acb4c`），且 recovered 帧是 `Bad-cast to const std::__1::__less<…> *_start`（**描述文本被塞进帧字段**）→ 是个坏的测试对象。harfbuzz 的 UBSAN 那条因构建失败未测。**③ 的 UBSAN 判定路径至今只有合成 fixture 验证过。**
* **2 条 i386 crash 在 x86_64 下复现**（OSV-2021-1710 / OSV-2022-55 → medium）→ 再次否证 N8。
* **located 率与 depth 分布高度依项目**：本轮 3 个项目 located **87.3%**、depth **1×130/2×2/3×6**（94.2% 只需 depth1）；W1 的 41 项目分层抽样是 located **64.6%**、depth **25/3/3**。→ 🅗 静态 check 的表现**不能跨项目外推**，两个数都对但总体不同。

**策略 B vs C 的实测重算（W1 模型已作废，见 §2.4）**

样本 = 13 条走完 tier 感知 walk-back 的 crash（located 3 / not_located 10），实际构建 **28 次**、拿到 medium+ **5 条**：

| 策略 | 定义 | 构建次数 | 相对 |
|---|---|---|---|
| A | 一律从 depth1 逐格到**首次复现**（N12 的旧判据） | ≈**21** | 最省，但会停在无关 bug 上 |
| C | W1：located 1 格 / not_located **2** 格 | **23** | – |
| **W3 实测** | tier 感知（到 medium+ 才停，最多 3 格）+ located 回退格 | **28** | 比 A 多 33%，换来**归因正确** |
| B | W1：located 1 格 / not_located **3** 格 | **33** | 最贵 |

* **B 比 C 多 10 次构建（+43%）**；W1 当年用**仪器假设**估的是「B 比 A 省 12.3%」——实测方向相反：**A 最省**。
* **C 会不会丢复现？** 本轮 `not_located` 里 `best_depth > 2` 的 = **0 条** → C 在这 10 条上**不丢任何东西**，还比 W3 实测省 5 次。
* **B 原版的风险**：located 里「主格构建失败、靠回退格救回」的本轮 **0 例**（W2 有 1 例：OSV-2020-2183）。
* **样本量与结论强度**：n=13（not_located 10）。**足以否证 W1 的模型**（三个前提全错），**不足以在 A/C/W3 之间定优劣**——差别是 21/23/28 次构建，而每种只在 10 条 not_located 上测过一次。要定论需 ≥30 条 not_located（还差约 20 条）。
* **🅗 建议（未实现）**：`not_located` 走 **depth1 → 若 `frac ≥ 0.6` 或 medium+ 即停，否则最多到 depth2**（= 介于 A 与 C 之间），按本轮数据可省 ~5 次构建且不丢复现。

## 4.20 W3 累积视角（W2 + W3，第一次有跨轮数据）

| 量 | W2 末 | **W3 末（累积）** |
|---|---|---|
| dataset | 142 行 / 129 条 / 51 字段 | **152 行 / 131 条 / 82 字段** |
| tier | 3 strict / 7 medium / 2 loose / 113 none | **4 strict / 10 medium / 4 loose / 113 none** |
| 复现 | 12/129 = 9.3% | **18/131 = 13.7%**（verified 18 条） |
| 按项目复现 | libtsm 7、c-blosc2 5 | libtsm 7、**c-blosc2 11** |
| `repro_version` | head 7 / fixed_parent 4 / fixed_ancestor 1 / none 113 | head 7 / **fixed_parent 8** / **fixed_ancestor 3** / none 113 |
| 真实构建尝试 | 54（成功 49 = 90.7%） | **81（成功 69 = 85.2%）** |
| — HEAD | 33/33 = 100% | **34/34 = 100%** |
| — 钉版 | 16/21 = 76.2% | **35/47 = 74.5%** |
| 逐项目可构建率 | — | c-blosc2 **28/29**、hunspell **11/11**、md4c **12/12**、pcre2 **10/10**、libtsm **3/3**、flatbuffers **5/9**、**harfbuzz 0/7** |
| 失败分类（新分类器重判 16 条） | compile_error 5 / walkback_exhausted 3 / dead_external_url 1 | **buildscript_mismatch 6**（harfbuzz，N19）/ **compile_error 4**（flatbuffers `stl_emulation.h` const 赋值）/ **toolchain_drift 2**（`-Werror`）/ **network_fetch 1** / unclassified 3（伪记录） |
| `T_build` | HEAD 中位 68s、钉版 73s | HEAD n=34 **中位 60s**（9–428）、钉版 n=35 **中位 73s**（14–577） |
| era 缓存（**同项目配对**） | pcre2 577→292s（−49.5%）、c-blosc2 157→79s（−50%） | c-blosc2 **92s vs 174s（−47%）**、pcre2 **291s vs 577s（−50%）**；另有 19+2 次「首试即成、不需 era」不参与此对比 |
| walk-back 复现深度 | 1×4、2×1 | **1×12、2×3**（含 `walkback_best_depth`） |
| 归档区 | 782MB / 17 目录 | **278MB / 7 目录**（裁剪生效） |
| 负对照 | 8/8 | 8 次 → **7 通过 + 1 可解释**（N21：那条是另一个 bug 在正确版本上的**真阳性**） |

⚠ **可外推性**：81 次构建集中在 **7 个项目**（全部是「已有干净镜像」的便利样本），钉版 74.5% 里 harfbuzz 一家贡献 7 次全失败。**不能外推**到 249 个 pinned 项目；要外推需随机抽 20–30 个项目，而磁盘（9.5G）与单项目镜像成本（~2.2GB）是硬约束。

## 4.21 W3：🅗/ⓘ → ✅

| 条目 | 原标记 | 实测值（附命令/文件） | 影响 |
|---|---|---|---|
| **N8「i386 结构性不可复现」** | ✅ W2（当作事实写进了 §3） | **配对实验**：c-blosc2@`861ba79f` 同一 commit 建两次 → i386 **崩**（4-byte-read、`_default`）、x86_64 **也崩**（8-byte-read、`_bmi2`），tier 都是 medium；另 2 条 i386 crash（OSV-2021-1710/-55）在 **x86_64** 下复现 | **推翻**。i386 不是障碍；W2 判 none 的真因是只跑 HEAD。`job_arch` 保留为**分层字段**，不再作「不可复现」先验 |
| **N10「镜像污染 → 排除项目」** | ✅ W2（🅗 重建可自愈、未实测） | `docker rmi` + worktree `build_image --no-pull`（2m17s）→ `/src` 注入源 **74 → 0** | **支持「可自愈」**，gate 第⑤条改为自动重建+复检。**但**「解锁 68 条」**只对一半**：harfbuzz 钉版仍 0/7（N19）→ 屏障换了个位置 |
| **R16「HEAD 共享、成本差 8×，HEAD-first 划算」** | ✅ 设计决策（纯推测） | `T_head/T_pin` 同项目中位 **0.87**（不是 8×）；has_fixed 的 HEAD 复现率 **0.8%**（上界 4.6%）< break-even **6.2%** | **推翻** → 路由改为按 `commit_source` 分流（§1.2） |
| **W1 策略 B 的成本模型** | ✅ W1（据此选了 B） | 三个前提全错：钉版中位 **73s** 非 5–10min；构建失败率 **25.5%** 未进模型；「未定位者三格全败」实测 **8/10 在 depth1 就复现** | **作废**（§2.4 已标）；实测重算见 §4.19：A≈21 < C=23 < W3=28 < B=33 |
| **`not_located` 桶的真实 depth** | ⓘ W1/W2 缺样本（差约 19 条） | 10 条走完三格：**8 复现全在 depth1**、2 条三格全空 → 累积 11 条，depth **1×9、无 2+** | **部分解决**：方向明确（depth1 足够），但 n=11 仍不足以在 A/C/W3 间定优劣（需 ≥30） |
| **MSAN 全链路** | ⓘ 零真实样本 | c-blosc2 MSAN 构建 3/3 成功（97–230s）；**首次 MSAN 复现**：OSV-2020-1060 `use-of-uninitialized-value` 类型逐字命中 → medium | **✅ 打通**。重试 ≤3× 路径**未触发**（首次即出结果）→ 仍 ⓘ |
| **UBSAN 全链路** | ⓘ 只有合成 fixture | libtsm UBSAN 构建带 `-fsanitize=…,vptr,…`、target 正常执行、无 `runtime error:` → none；harfbuzz UBSAN 构建失败 | **仍未解决**：判定路径**零正样本**（§4.22） |
| **era 缓存「省一半」** | ✅ W2（n=1 配对 + 1 项目） | 新增 c-blosc2 配对 **92s vs 174s = −47%**（n=3 vs 3）；pcre2 **−50%** 复现 | **支持**（2 项目、两种口径都 −47%～−50%） |
| **归档裁剪的可行性** | 🅗 设计（§1.6 写成「可选」） | 两次实测回收 **377MB + 889MB**；一轮 14 次构建的净增长 **−245MB** | **支持** → 改默认执行；同时暴露 **N20**（保护集口径） |
| **N4 还原是否充分** | ✅ W1（「实测只动 projects/、infra md5 不变」） | era commit 含 HEAD 没有的文件时，`checkout HEAD -- <path>` **删不掉且留 staged** → gate 判脏 | **修正**（**N18**）：W1 的验证只覆盖了一半情形 |
| **负对照判据** | ✅ 设计（§1.7） | 8 次里 1 次「失败」，查证是**另一个 bug 在被测版本里本来就活着**（窗口 2021-02-18→2022-06-13 含 2022-06-09） | **修正**（**N21**）：判据需**版本感知** |
| **`--print-plan`/gate 的开销** | ⓘ 未测 | gate 第⑤条对每项目 `docker run` ≈2–5s → 逐条 crash 出计划时 14 条卡 >15min；跳过后 **0.76s/条** | 已修（`--print-plan` 不跑 gate） |

## 4.22 W3：仍 🅗/ⓘ

| 条目 | 为什么没解决 | 需要什么 |
|---|---|---|
| **UBSAN 判定路径零正样本** | 两个候选都不行：libtsm 那条版本数据自相矛盾（`fixed==introducing==HEAD`）且 recovered 帧是描述文本；harfbuzz 那条构建失败 | 找一条 UBSAN crash，其 `fixed` 明确、项目可构建（🅗 c-blosc2/pcre2 的 undefined 记录，或 libxml2），钉到 `fixed^` 再跑 |
| **MSAN 重试路径（≤3×）未触发** | 首次执行即出结果，没遇到 flaky | 需要一条真 flaky 的 MSAN crash（W2 记录 MSAN/uninit 875 条，🅗 里面应有） |
| **A/C/W3 三种 walk-back 策略定优劣** | n=10 的 not_located，构建次数差 21/23/28 | ≥30 条 not_located 走完（还差约 20 条，≈40–60 次钉版构建） |
| **harfbuzz 68 条仍不可达** | N19：`build.sh` 要 `test/fuzzing/hb-raster-fuzzer`，老 commit 里没有；era 自愈已触发仍失败 | 🅗 需要「按 commit 日期选 build.sh」之外的手段（如允许 build.sh 的 target 列表容错），**但这属于改上游构建脚本**，本轮约束禁止 |
| **flatbuffers 钉版 0/4** | A2：老代码给 const 成员赋值，新 clang 拒绝；era 换不掉编译器 | gcloud era base-builder digest（不可用）或自建 era 镜像序列 |
| **可构建率外推** | 7 个项目的便利样本 | 随机抽 20–30 项目；受磁盘（9.5G）与镜像成本（~2.2GB/项目）限制 |
| **N16 重试未验证** | 本轮无 `network_fetch` 失败 | 重跑 W2 的 c-blosc2@`9ba29ef1`（已知会网络失败）即可验证 |
| **N12 的 🅗 改进（`frac≥0.6` 即停）** | 只有 n=13、0 次下探改善 tier | 更多 loose 样本；或直接按 §4.19 的建议实现后 A/B 对比 |
| **i386 是否对 tier 有影响** | 配对实验里两种架构的 tier 相同（都 medium），但**第三帧不同**（`_default` vs `_bmi2`）、访问宽度不同（4 vs 8 byte）→ 若 ground truth 含架构特有帧，x86_64 构建可能掉档 | 需要一条「recovered 帧含 i386 特有符号」的 crash；本轮那条 R 与 O 零重叠，看不出差别 |

## 4.23 W3 卡点

**没有硬卡点，四个 Phase 全部完成。** 三处「做了但不完整」：

| 项 | 现象 | 已排除 | 下一步 |
|---|---|---|---|
| Phase 5 的 not_located 只到 11 条 | 预算（`--max-builds 14`/`6`）与时间 | 不是代码问题；14 条里 harfbuzz 6 条因 N19 全失败、白占 18 次构建尝试 | 换 c-blosc2/hunspell/pcre2 的 not_located（构建可靠）补 20 条 |
| UBSAN 无正样本 | 两个候选一个数据矛盾、一个构建失败 | 构建侧确认 UBSAN 真的启用了（`-fsanitize=…,vptr,…`） | 见 §4.22 |
| harfbuzz 白跑 19.5min | 6 次构建全失败（每次 ~90–320s）才确认 N19 是系统性的 | 前 3 次失败后就该停（同项目同类错误）→ 🅗 ⑥ 应加「同项目连续 N 次同类构建失败即跳过该项目」 | 实现该早停（可省本轮 ~10min） |

**磁盘仍是硬约束**：起始 13G → 结束 **9.5G**（wolfssl i386 实验的镜像吃掉 ~4G，已 `docker rmi` 回收；归档区经两次裁剪从 782MB 降到 **278MB**）。

## 4.24 W3 约束遵守

| 约束 | 结束时实测 | 命令 |
|---|---|---|
| 主树 `/root/gyx/oss-fuzz` 只读、须 **550** | **550** ✅ | `git -C /root/gyx/oss-fuzz status --porcelain \| wc -l` |
| worktree 停 `repro-patches`、无未提交改动 | `repro-patches` @ `07522dc0e`、`status --porcelain` = **空** ✅ | 同上（worktree） |
| `infra/` 三补丁不得改动 | md5 汇总 **`f5092d0a3f2a6909`**，与 W2 结束时一致 ✅ | `md5sum infra/{common_utils,helper,build_specified_commit}.py` |
| 不动 driver_create | **0** 脏项 ✅ | `git -C /root/gyx/driver_create status --porcelain \| wc -l` |
| gate 五条件（含 N10 镜像检查） | 每次 ② 调用都跑；本轮触发**自动重建自愈 1 次**（harfbuzz，§4.18b）；抓到 **1 次真脏**（N18）→ ABORT | ② 的 gate 输出 + `BLOCKED.md`（已清） |
| 不改 Dockerfile/build.sh | 未改（N19 的修法是**分类 + 记录**，不是改上游脚本） | – |
| 不装 clusterfuzz | 未装 | – |
| docker / 网络使用 | 构建 **30 次**（另 i386 实验 4 次、镜像重建 1 次）、复现执行 **~40 次**、负对照 8 次；静态 check **199 条**（`.patch` 端点，**0 clone / 0 API**）；未访问 gcloud | 各 run 的 `artifacts/logs/` |
| 自测护栏 | ③ **4/4**、④ **4/4**、② 分类器 **9/9**、① 回归 **25 通过 / 0 不符 / 4 争议** | `repro_runner.py --selftest` 等 |
---

## 4.25 W4 概览：一句话结果与总量

**四个 Phase 全部完成，无硬卡点。** 数据完整性加了两道结构性防御（并**自测证明拦得住**）、4 个被误删的 verified 归档**逐字节重建还原**、静态 check 降为 advisory 且 ② 一律走策略 A（代码确实变短）、构建前静态预检 + 早停双双落地并在生产里触发、扩样本 **10 条**（策略 A 验证轮）+ 两个小实验。

| 量 | 值 |
|---|---|
| 本轮跑到分级的 crash | **11 条**（策略 A 验证轮 10 + pcapplusplus UBSAN 1）；另 4 次归档重建、3 次 i386 配对构建、11 次负对照执行 |
| 本轮 tier（策略 A 那 10 条） | **9 strict + 1 loose**，只用 **7 次真实构建**（12 次格尝试、5 次缓存命中） |
| **累积（W2+W3+W4）** | dataset **163 行 / 132 条唯一 / 82 字段**；tier **10 strict + 9 medium + 3 loose + 110 none**；复现 **22/132 = 16.7%** |
| 累积可构建率 | **86/101 = 85.1%**（HEAD **35/35=100%**、钉版 **51/66=77.3%**） |
| **strict 从 4 → 10** | 主因 = 策略 A（depth1 起）+ **按 `job_arch` 构建**（§4.30 (d)） |
| Phase 1 自测 | 两道防御 **12/12** 拦住（含构造的降级写入与会删 verified 的裁剪） |
| Phase 1b 重建 | 4 个归档 × 5 个文件 = **20/20 逐字节一致** |
| Phase 3 预检 | harfbuzz **6/6** 命中、pcapplusplus **3/3** 命中、已知能建的 6 个项目 **0 误报**；生产触发 **早停 1 次**（pcapplusplus，省 9 条 × 至多 3 格） |
| Phase 4(d) | i386 配对 **n=3**：`medium → strict`（3/3），其中 1 条 x86_64 下**崩成了另一个 bug** |
| Phase 4(e) | 负对照改 HEAD 为默认：**11/11 通过 + 正对照 2/2** |
| 新发现 | **N22–N24**（§3）；自查修 **5 个 bug**（§4.26/§4.28） |
| 约束 | 主树 **550** ✅ / worktree `repro-patches@07522dc0e` **干净** ✅ / infra md5 `f5092d0a3f2a6909` **未变** ✅ / driver_create **0** ✅ / 磁盘 **8.3G** |

## 4.26 W4 Phase 1：数据完整性

### (i) ⑤ 侧单调性校验

**根因判断**：N20 的修法（裁剪保护集扫全部行）治的是**裁剪侧**，根因在**写入侧**——`repro_dataset.jsonl` 是 append-only 复现记录表、下游按「同 `osv_id` 取 `run_ts` 最新一行」读，所以**最新一行就是当前状态**，任何写入方的 bug 都能静默作废一个已交付结论。

**实现**（`annotate_dataset.py`）：写入前用 `tier_history()` 扫全部历史行 → `{osv_id: 曾达到的 verified tier 集合}`；若该 id 曾 verified 而新行**无结论**（`run_status != "run"` 或 `verification_tier is None`）：
* 默认 **拒写 + ❌ 报错 + 记 `artifacts/dataset_guard.jsonl`**；
* `--force` 时才写，并标 **`tier_downgraded=true` + `tier_downgrade_reason`**；
* verified → **另一个** verified（真重跑得到的新结论）允许，但留痕 `tier_changed_from`。

**自测**（`preflight/selftest/w4_phase1a_selftest.py`，构造真实降级写入，对 dataset **副本**操作）：

| 断言 | 结果 |
|---|---|
| 默认无 `--force`：行数 152 → **152**（未写入） | ✅ |
| 日志含明确报错（`❌ 拒写 OSV-2016-5：历史行曾达 verified=['medium']，本行 tier=None run_status=not_run`） | ✅ |
| 该 osv_id 的当前状态仍是 `medium` | ✅ |
| `--force`：写入 1 行（152→153）且带 `tier_downgraded=true` + 原因 | ✅ |
| 两次都记进 `dataset_guard.jsonl` | ✅ |

### (ii) 裁剪 dry-run 默认 + 独立交叉校验 + 审计日志

* **默认 dry-run**：`--prune-archive` 不加 `--prune-apply` 只报告不删（删除不可逆，必须显式要求）；⑥ 轮末调用时显式传 `--prune-apply`。
* **独立交叉校验**（关键设计）：保护集是按 verified 行的 `binary_dir` 算的；这里**换一个字段** `pinned_commit`(+project/sanitizer) 再算一遍「哪些 commit 曾被 verified 记录用过」。**用同一字段自查等于没查**——两条路径不一致就说明保护逻辑有 bug（W3 N20 那种），此时 `M>0` → **拒绝执行**（除非 `--prune-force`），并打印冲突清单。
* **审计日志** `artifacts/prune_audit.jsonl`：每次裁剪（含 dry-run 与 REFUSED）都留一条（`action`/`n_pruned`/`M`/`freed_bytes`/**完整删除清单**/`protected_by_tier`）。
* 打印格式按要求：「将删 N 个目录，其中 **M 个在历史行里标过 verified**」。

**自测**（monkeypatch `BINARIES` 到 /tmp 的假归档树，**不碰真实数据**）：

| 断言 | 结果 |
|---|---|
| 构造「`binary_dir` 对不上但 `pinned_commit` 对得上」的 verified 行（= N20 事故形态）→ `M=1` → **拒绝执行** | ✅ |
| 拒绝是**整轮**拒绝：连 `none` 的目录也没删 | ✅ |
| 审计留痕 `action=REFUSED` | ✅ |
| `--prune-force` → 照删 3 个且审计 `action=pruned, M=1` | ✅ |
| 正常情形（`binary_dir` 对得上）→ `M=0`、保留 verified 1 个、删 none 1 个（目录级复核） | ✅ |
| 合计 | **12/12** |

生产实测：W4 两个 run 的轮末裁剪各写 1 条审计，`M=0`、`n_pruned=0/1`、`freed=0/51MB`。

### (iii) 4 个被删归档的重建 —— **20/20 逐字节一致**

W2 已证构建 bit 确定、且 `binary_sha256` 记着 → 重建可字节级还原。用 ② `--commit-override` 重建 4 个 commit（**6.9min**，其中 3 次 era 缓存命中）：

| osv_id | tier | commit | 校验 |
|---|---|---|---|
| OSV-2020-2183 | strict | `71dd7e513631` | 4 个 target + symbolizer **5/5 ✅** |
| OSV-2020-2184 | loose | `3724317f7bd6` | **5/5 ✅** |
| OSV-2020-2251 | loose | `8cb8eb21459b` | **5/5 ✅** |
| OSV-2021-1663 | strict | `79b6995ab82e` | **5/5 ✅**（symbolizer 是另一变体 `db0240ff`，也与记录一致） |

**合计 20/20 逐字节一致** → ① W2 的 bit 确定性结论在 **4 个 commit × 5 个文件**上再次成立（比 W2 的 3 个二进制强得多）；② 其中 3 次走 era 预 checkout 路径 → **era 优化不改变产物**再次确认；③ **已知答案回归的缺口已补齐**，不再留悬账。

### (iv) 本轮自查修掉的 5 个 bug

| # | 位置 | bug | 怎么抓到 | 修法 |
|---|---|---|---|---|
| 1 | ② `path_exists_at` | 对**已有扩展名**的路径也把 15 个 `SRC_EXTS` 全试一遍 → 预检成本爆炸（验证脚本 **>15min 未返回**） | 跑预检验证时卡死 | 有扩展名只查 1 次；无扩展名（ninja target）只试 4 个最可能扩展名 → harfbuzz 单条 **64.2s → 22.6s** |
| 2 | ② 预检候选正则 | 放宽成「任何路径」后把 `www.apache.org/licenses/LICENSE-2.0`、`$OUT/*.zip`、`.libs/libpcre2-8.a`、`bin/bash` 全抓进来 → 必然 404 → **误报会跳过本能成功的构建** | 在 4 个项目上打印候选集人工看 | 回到窄口径（fuzzer target + 源码扩展名）**另加**精确的「被调用的 `.sh/.py/.pl`」模式；并加 `MAX_PRECHECK_PATHS=40` 成本护栏 |
| 3 | ② 分类器 | 同一个 pcapplusplus 错误被分成 `toolchain_drift`(1) 与 `compile_error`(2) → **削弱早停的连续计数**（本该第 2 次触发，实际第 3 次） | 逐条读失败记录 | 新增形态② 的 `buildscript_mismatch` 模式（`error: \S+: No such file or directory`）→ 自测 **10/10** |
| 4 | `w4_phase4e_negctl.py` | 循环内 `target = m["fuzz_target"]` **遮蔽**了外层变量 → 版本感知段误判「钉版归档不可用」而**静默跳过** | 输出里 `[2]` 段的理由与上一轮不一致 | 改局部名 `tgt`；ⓘ 教训：「跳过」的原因必须能与「0 候选」区分开 |
| 5 | `w4_phase4e_negctl.py` | 对照限定「同一 fuzz_target」→ c-blosc2 复现那条的 target 是 `compress_fuzzer`、全项目仅 1 条用它 → **同项目对照 0 条可用** | 输出里 c-blosc2 只有随机+跨项目两项 | 放宽为「该 crash 自己的 target 在归档里存在即可」→ 同项目对照 3 条、总对照 5→**11** |

## 4.27 W4 Phase 2：静态 check 降 advisory，② 一律走策略 A

**改了哪里**
* ② `plan_pinned()`：**删掉 `located` 分支**（连同 `--no-pin-fallback` 开关，共 18 行）→ 一律 `fixed~1..max_depth` 逐格；`pin_commit` 只作为 **advisory** 出现在计划注释里（`advisory：① 静态 check 会钉 X=depthN，本轮不采用`）。
* ① **不变**：`fixed_real`/`static_check_verdict`/`walkback_depth`/`fixed_misattributed` 照常算、照常进 manifest（对下游理解 crash 有价值）。
* **不受影响**：N6 `degenerate` 未复核通过仍禁钉版；无 `fixed` 仍回退 `introducing_commit`；无 `repo_url` 仍 `undecidable`；`skip_reason` 各档照旧。
* N12 的 tier 感知停止、N17 的构建失败回退**保留**。

**代码行数（任务要求「应该变短」）**

| 对象 | W3 末 | Phase 2 后 | 变化 |
|---|---|---|---|
| `plan_pinned()` | 52 行、**2 条顶层分路**（located / 非 located）、10 个 `if` | **44 行、1 条顶层分路、7 个 `if`** | **−8 行、少一条分路** ✅ |
| `build_orchestrator.py` 整体 | 1,299 行 | **1,288 行** | **−11 行** ✅ |
| （对照）Phase 3 之后 | – | 1,481 行 | **+193 行 = 预检/早停/arch 三项新功能**，与 Phase 2 的简化无关 |

→ **简化那一步确实变短了**；总行数上升来自 Phase 3/4 的新能力，不是 Phase 2 的改法有问题。

**本轮实测的策略成本重算**（策略 A 第一次跑 `located` 记录 —— W3 只在 `not_located` 上跑过 A）

10 条 c-blosc2 ASAN HBO（8 `located` + 2 `not_located`），**12 次格尝试 / 7 次真实构建**（5 次缓存命中）→ **9 strict + 1 loose**：

| osv_id | verdict | ① advisory | **A 实际 best_depth** | 格数 | tier | frac |
|---|---|---|---|---|---|---|
| OSV-2020-2087 | located | 1 / `3466fae4d7` | **1** | 1 | strict | 1.0 |
| OSV-2020-2183 | located | 1 / `9ba29ef158` | **1** | 1 | strict | 1.0 |
| OSV-2020-2184 | located | 1 / `3724317f7b` | **3** | 3 | loose | 1.0（类型不一致=N15） |
| OSV-2020-2251 | located | **3** / `74e382a4c0` | **1** | 1 | **strict** | 1.0 |
| OSV-2021-1589 | not_located | — | **1** | 1 | strict | 1.0 |
| OSV-2021-1663 | located | 1 / `79b6995ab8` | **1** | 1 | strict | 1.0 |
| OSV-2021-1710 | not_located | — | **1** | 1 | strict | 1.0 |
| OSV-2021-1712 | located | 1 / `79b6995ab8` | **1** | 1 | strict | 1.0 |
| OSV-2021-1755 | located | 1 / `79b6995ab8` | **1** | 1 | strict | 1.0 |
| OSV-2021-1791 | located | 1 / `886d4c9b78` | **1** | 1 | strict | 1.0 |

* **advisory depth 与 A 的 best_depth：一致 7、A 更浅 1、A 更深 0**（那条更深的是 OSV-2020-2184，三格全 loose）。
* **反事实**：策略 B（located 直接钉 advisory）= 8 次构建；A 实测 **7 次真实构建**（12 次尝试里 5 次命中缓存）→ **A 不比 B 贵**，而且：
* **OSV-2020-2251 是决定性反例**：advisory 说 depth3，A 在 **depth1 就拿到 strict**；W3 用 x86_64 建 depth1 时它给的是**另一个 bug**（use-after-free in memcmp → loose），本轮按 `job_arch=i386` 建 → `Heap-buffer-overflow READ 1` + 帧与 ground truth **逐字相同** → strict（见 **N22**）。**advisory 指错格的代价是实打实的。**

**必须标注的前提（任务要求）**：n 小（`not_located` 累积仍只有 **11 条**走完三格：W3 的 10 + 本轮 2 条中 1 条与 W3 重复），且 **located 率跨项目不稳**（W3 的 3 项目 **87.3%** vs W1 的 41 项目分层抽样 **64.6%**）→ 本改动是「**按现有证据的默认选择**」，**不是终局结论**；`not_located` 补到 ≥30 条后复核（§5 待办）。

**W1 策略表 与 W3 四策略对比表 并列（各自样本量与适用范围）**

| 表 | 结论 | 样本 | 适用范围 | 现状 |
|---|---|---|---|---|
| **W1 四策略成本表**（§2.4） | B 最优（比 A 省 12.3%）、C 不采纳 | **0 次真实构建**（纯模型，42 条静态 check 结果 + 「未定位者三格全败」的**仪器假设**） | 无 —— 三个前提全被实测推翻 | **⛔ 已作废**（§2.4 顶部有红框） |
| **W3 四策略实测重算**（§4.19） | A≈21 < C=23 < W3 实现 28 < B=33 | 13 条走完 tier 感知 walk-back（located 3 / not_located 10），28 次构建 | c-blosc2 + harfbuzz，**单轮**；harfbuzz 9 次构建全失败会抬高 B/W3 的计数 | ✅ 有效，但 n=13 |
| **W4 策略 A 首轮**（本节） | A：10 条 / **7 次真实构建** / 9 strict + 1 loose；advisory 与 A 的 best_depth 一致 7、A 更浅 1 | 10 条 c-blosc2 ASAN HBO（8 located + 2 not_located） | **单项目单 sanitizer**；含缓存命中（5/12），换项目会不同 | ✅ 有效，n=10 |

**合并读数**：三张表方向一致 —— **A（depth1 起 + walk-back + tier 感知停止）在实测里既不更贵、也不更差，且避免了 advisory 指错格的损失**。→ 采用 A 为默认。

## 4.28 W4 Phase 3：构建前静态预检 + 早停

### 3a `buildscript_mismatch` 静态预检

**做法**：构建前读**将要使用的** `projects/<p>/build.sh`（worktree 版），展开 shell 花括号（`hb-{shape,raster,…}-fuzzer`），提取候选路径，用 **`raw` 端点**逐个查该 commit 的树里是否存在（**0 次 API、0 次 clone**，走 ⓪ 的宿主代理 + /tmp 磁盘缓存）；有缺失 → 标 `buildscript_mismatch` **跳过构建**。

**N19 有两种形态，只查 fuzzer target 会漏掉第二种**：

| 形态 | 实例 | 错误 | 预检怎么抓 |
|---|---|---|---|
| ① 构建目标缺失 | harfbuzz `ninja … test/fuzzing/hb-{shape,raster,vector,gpu,subset,repacker}-fuzzer` | `ninja: error: unknown target 'test/fuzzing/hb-raster-fuzzer'` | 窄口径正则抓 `*-fuzzer`/`*_fuzzer` 与源码扩展名路径 |
| ② **被调用的脚本缺失** | pcapplusplus build.sh 第 22 行整行就是 `$SRC/PcapPlusPlus/Tests/Fuzzers/ossfuzz.sh` | `error: Tests/Fuzzers/ossfuzz.sh: No such file or directory` | 另加精确的 `SCRIPT_RE`（`$SRC/`、`bash`、`sh`、`source`、行首 `./` 之后的 `.sh/.py/.pl` 路径），并剥掉 `$SRC/<repo basename>/` 前缀 |

**已知答案验证**（先验证再接进 ②，任务要求）：

| 组 | 结果 |
|---|---|
| harfbuzz 6 条（W3 已知 6/6 构建全失败于形态①） | **命中 6/6**（候选 = 6 个 fuzzer target，missing 含 `hb-raster-fuzzer`/`hb-gpu-fuzzer`/`hb-repacker-fuzzer`） |
| pcapplusplus 3 条（W4 已知 3/3 失败于形态②） | **命中 3/3**（候选 = `Tests/Fuzzers/ossfuzz.sh`，恰是缺的那个） |
| 已知能建的 6 条（c-blosc2 ×3、pcre2、hunspell、md4c） | **误报 0/6**（候选集为 **0** → 结构上不可能误报） |
| 成本 | harfbuzz **22.6s/条**（收窄扩展名前 64.2s）、pcapplusplus **0.8s/条**、无候选项目 **0.0s**；对比一次白跑的构建 **90–320s** |

**覆盖率（诚实标注）**：249 个 pinned 项目里 **56 个**的 build.sh 能提取到候选路径（预检有牙齿）、**176 个** no-op、**17 个**无 build.sh → 预检只能覆盖 ~22% 的项目；对其余项目**不拦也不误报**。
**误报防护原则**：宁可漏报不可误报（误报会跳过本能成功的构建，比 N19 的浪费更糟）——故①丢弃紧邻 shell 变量的匹配（✅ 实测 pcre2 的 `pcre2_fuzzer${bits}.dict` 曾被截断成不存在的路径 → 误报），②只认 ≥2 段路径，③无法判定（非 github/gitlab、网络错）一律放行，④候选 >40 个只查前 40（成本护栏）。

### 3b 早停

**规则**：同项目连续 **N=2** 次**同类版本确定性失败** → 跳过该项目本轮剩余队列（`--stop-project-after`）。
**N=2 的理由**：① 只数**版本确定性**失败类（`buildscript_mismatch`/`toolchain_drift`/`compile_error`/`dockerfile_drift`/`commit_not_found`）——这些由「上游 commit × 当前 build.sh/工具链」决定，同项目同 era 必然同样失败；**瞬态的 `network_fetch` 不计入**（且 ② 已按 N16 自动重试 1 次）。② 实测支持：harfbuzz **6/6** 同类失败、flatbuffers **4/4** 同类失败（W2+W3），**未出现过「前 2 次同类失败、第 3 次成功」**。③ 代价有界：早停只影响**本轮**该项目剩余队列（不写进 `state.json`，下轮可重试）；取 3 会多白跑一次（harfbuzz 单次 90–320s），取 1 则一次偶发失败就封项目、太激进。

**生产触发（W4 实测 1 次）**：pcapplusplus UBSAN 轮 —— 3 次构建全 `compile_error`（真因是形态②，当时分类器还没加该模式）→ 第 2 次同类失败即**封项目**，跳过剩余 **9 条**（每条至多 3 格 → **最多省 27 次构建**，实测该轮只用 3 次构建、9.4min 就收尾）。
**3a 与 3b 叠加的效果**：本轮预检在 harfbuzz/pcapplusplus 上共命中 **9 条**（6+3）；若两者都在位，pcapplusplus 那 3 次构建**一次都不会跑**（预检 0.8s/条 直接拦），早停只是兜没预料到的形态。

## 4.29 W4 Phase 4(a)(b)(c)：扩样本结果

**选样与理由**：磁盘 8.3G（新项目镜像 ~2.2GB）+ 时间有限 → ① 优先在**已验证可建**的 c-blosc2 上跑策略 A 验证轮（10 条，同时补 `located` 走 A 的新代码路径）；② 为 UBSAN/MSAN 选**一个新项目 pcapplusplus**（81 条可执行、含 **10 UBSAN + 23 MSAN**，一个项目同时覆盖 (b)(c)）；③ harfbuzz 的 6 条 `not_located` 已在 W3 试过、构建全失败，本轮由预检拦截不再白跑。

| 类别 | 结果 |
|---|---|
| **(a) `not_located` 累积** | 走完三格的 **11 条**（W3 10 + W4 2，其中 OSV-2021-1589 重复）→ **9 条在 depth1 复现**、2 条三格全空。**仍不足 30**，A/C 之争只能给方向不能定论（§4.33） |
| **(b) UBSAN 正样本** | **仍为 0**。pcapplusplus 3 次 UBSAN 钉版全失败（形态②）→ 早停；libtsm 的那条是坏测试对象（`fixed==introducing==HEAD`、recovered 帧是描述文本）。**③ 的 UBSAN 判定路径至今只有合成 fixture 验证过** |
| **(c) MSAN 全链路** | ✅ **W3 已打通**（c-blosc2 MSAN 构建 3/3 成功；OSV-2020-1060 `use-of-uninitialized-value` 类型逐字命中 → **medium**；OSV-2020-1016 → loose）。W4 未新增 MSAN 样本（pcapplusplus 被早停挡住）。**flaky 重试路径（≤3×）仍未触发** |
| 累积按 sanitizer 复现率 | `address` **20/127 = 15.7%**、`memory` **2/3 = 66.7%**、`undefined` **0/2 = 0%**（n 极小，不可外推） |
| 累积按 `job_arch` 复现率 | `x86_64` **18/102 = 17.6%**、`i386` **4/30 = 13.3%** → **差异不显著**（再次否证 N8 的「结构性不可复现」） |

**失败逐条（W4 新增，按根因分组）**

| project | san | 次数 | ② 当时记的类 | **人工核对的真根因** | 证据 |
|---|---|---|---|---|---|
| pcapplusplus | undefined | 3 | `toolchain_drift`(1) / `compile_error`(2) —— **同错不同类** | **N19 形态②**：build.sh 第 22 行执行 `$SRC/PcapPlusPlus/Tests/Fuzzers/ossfuzz.sh`，该文件在 3 个 pinned commit 里都不存在 | `artifacts/logs/build/pcapplusplus_undefined_*.log`；预检 3/3 命中 |
| （对照）harfbuzz | address/memory | 6+1 | `compile_error` | **N19 形态①** + `-Werror` 工具链漂移 | W3 §4.18(b) |

ⓘ 分类不一致（同一错误两个类）**削弱了早停的连续计数**：本该第 2 次触发，实际第 3 次 → 已修（新增形态② 模式，自测 10/10）。

## 4.30 W4 Phase 4(d)(e)：两个小实验

### (d) i386 精化 —— **结论：不是「可建上限」，而是「必须按原架构构建才能正确归因」**

**任务要求修正表述**：W3 报的「i386 可建上限 161/163（99%）」容易被读成「要加架构维度」；实测**不需要为了『能不能复现』加架构**（x86_64 也复现），但**需要为了『复现得对不对』按 `job_arch` 构建**。

**配对实验（同 commit、同 testcase、只换架构）**：

| osv_id | commit | x86_64 | **i386** | 差异机制 |
|---|---|---|---|---|
| OSV-2021-1710 | `f0fc8fb39b` | `pos 0.3333 / subseq 0.0 / frac 0.6667` → **medium** | **`1.0/1.0/1.0/1.0` → strict** | x86_64 把 `ndlz_decompress` **内联掉**了 → observed 少一帧；i386 保留 → 与 ground truth（来自 i386 job）逐字对齐 |
| OSV-2022-55 | `0112ed48a5` | 同上 → **medium** | **→ strict** | 同上 |
| **OSV-2020-2251** | `8cb8eb2145` | 崩成**另一个 bug**：`Heap-use-after-free READ 32`，帧 `MemcmpInterceptorCommon/memcmp/LooseMemeq/free/…` → **loose** | `Heap-buffer-overflow READ 1`（= 期望类型），帧 `blosc_run_decompression_with_context/blosc2_decompress_ctx/frame_decompress_chunk` **与 ground truth 逐字相同** → **strict** | **架构不匹配不只是掉档，是会撞上另一个 bug 并给出误导性结论** → **N22** |

**n=3，3/3 都从 medium/loose 升到 strict。** 产物已验证是 ELF32（`readelf -h` → `Class: ELF32 / Machine: Intel 80386`），归档目录带 `__i386` 后缀、缓存键含架构分量（W3 已铺好，x86_64 键与历史完全兼容）。
**实现**：⑥ `--match-job-arch`（**默认开**，`--no-match-job-arch` 可关）——按 crash 自己的 `job_arch` 构建。⚠ 这是**替换不是新增**：i386 上报的 crash 本来也要建一次，只是换成对的架构 → 常规情况**不多花构建**（仅当同项目同 commit 同时有 x86_64 与 i386 crash 时才多一次）。本轮生产触发 **3 次**，i386 构建中位 **106s**（n=3）。
**未做**（任务约束）：**没有**把架构加成 manifest 的通用维度、没有改 ① 的 schema —— 只在 ② 的缓存键/归档路径（W3 已有）与 ⑥ 的构建参数上生效。

### (e) N21 负对照改造 —— **HEAD 二进制为默认**

**新判据（已写进 §1.7 I）**：
1. **默认用 HEAD 二进制**做对照：HEAD 上绝大多数 bug 已修、窗口冲突概率最低、HEAD 构建**共享**（一次服务同项目同 sanitizer 全部 crash）→ 成本最低。跑：同项目其他 bug 的 testcase ≥3 条、随机 256B、别项目 testcase 1 条 → 全期望 none。
2. **版本感知作补充**：仍要在钉版二进制上做对照时，只挑「`[introduced, fixed)` 窗口**不含**被测 commit 日期」的其他 crash（日期取 `.patch` 的 author date，走磁盘缓存）。
3. **正对照**：目标 bug 在自己那台二进制上仍须崩。

**实测：期望 none 的对照 11 次 → 11/11 通过；正对照 2/2 仍崩**

| 项目 | 正对照 | HEAD：同项目其他 bug | HEAD：随机 256B | HEAD：别项目 | 版本感知（钉版） |
|---|---|---|---|---|---|
| c-blosc2（15 条复现） | ✅ OSV-2020-2087 `HBO WRITE 4` | **3/3 none**（OSV-2021-1645/-1676/-207） | ✅ none | ✅ none（libtsm 的 OSV-2016-5） | **3/3 none**（OSV-2020-1016 窗口[2020-06-24,06-25)、-1060 [06-24,06-27)、-775 [06-26,09-12)，均**不含**被测 commit 日期 2020-10-16） |
| libtsm（7 条复现） | ✅ OSV-2016-5 `GBO READ 1` | **1/1 none**（OSV-2017-126；该项目 7/7 全复现，同项目对照天然稀缺） | ✅ none | ✅ none（gstreamer 的 OSV-2017-24） | ⓘ 钉版 commit 日期取不到（libtsm 走 `introducing`，非 `fixed~d`）→ 跳过 |

**W3 那条「失败」的对照保留为正面结果**（不是缺陷）：c-blosc2@`886d4c9b`（2022-06-09）跑 OSV-2021-1791 的 testcase 真崩，而该 bug 窗口 `2021-02-18 → 2022-06-13` **含**该日 → **它证明流水线能在正确版本上找到正确的 bug**。新判据把这类情况从「对照失败」重新归类为「窗口冲突，不作对照」。

## 4.31 W4 累积视角（W2+W3+W4）

| 量 | W2 末 | W3 末 | **W4 末** |
|---|---|---|---|
| dataset | 142 行 / 129 条 / 51 字段 | 152 行 / 131 条 / 82 字段 | **163 行 / 132 条 / 82 字段**（9 个 run_id） |
| tier | 3 strict / 7 medium / 2 loose / 113 none | 4 / 10 / 4 / 113 | **10 strict / 9 medium / 3 loose / 110 none** |
| 复现 | 12/129 = 9.3% | 18/131 = 13.7% | **22/132 = 16.7%** |
| 按项目 | libtsm 7、c-blosc2 5 | libtsm 7、c-blosc2 11 | libtsm 7、**c-blosc2 15** |
| `repro_version` | head 7 / fp 4 / fa 1 / none 113 | head 7 / fp 8 / fa 3 / none 113 | head 7 / **fp 13** / fa 2 / none 110 |
| 复现深度（best/actual） | 1×4、2×1 | 1×12、2×3 | **1×13、2×2、null×7**（null = HEAD 或 introducing 复现，非 walk-back 格） |
| 真实构建尝试 / 成功 | 54 / 49 = 90.7% | 81 / 69 = 85.2% | **101 / 86 = 85.1%** |
| — HEAD | 33/33 = 100% | 34/34 = 100% | **35/35 = 100%** |
| — 钉版 | 16/21 = 76.2% | 35/47 = 74.5% | **51/66 = 77.3%** |
| 逐项目可构建率 | – | c-blosc2 28/29、harfbuzz 0/7、flatbuffers 5/9 | **c-blosc2 45/46**、md4c 12/12、hunspell 11/11、pcre2 10/10、libtsm 3/3、flatbuffers 5/9、**harfbuzz 0/7**、**pcapplusplus 0/3** |
| `T_build` | HEAD 中位 68s、钉版 73s | HEAD 60s、钉版 73s | HEAD n=35 **中位 68s**(9–428)、钉版 n=51 **中位 79s**(14–577)、**i386 n=3 中位 106s** |
| 归档区 | 782MB / 17 目录 | 278MB / 7 目录 | **989MB / 18 目录**（verified 增多 → 保留增多；裁剪仍每轮跑，`M=0`） |
| 负对照 | 8/8 | 7 通过 + 1 可解释（N21） | **11/11 + 正对照 2/2**（新判据） |

⚠ **外推限制（不变）**：101 次构建集中在 **8 个项目**，全是「已有干净镜像或已验证可建」的便利样本；钉版 77.3% 里 harfbuzz(0/7)、pcapplusplus(0/3)、flatbuffers(5/9) 三家贡献了全部 15 次失败 → **真实全量钉版可构建率很可能显著低于 77.3%**，因为「build.sh↔老 commit 错配」与「老代码×新 clang」这两类失败是**系统性**的，而本轮的项目样本恰好偏向能建的。

## 4.32 W4：🅗/ⓘ → ✅

| 条目 | 原标记 | 实测值（附命令/文件） | 影响 |
|---|---|---|---|
| **数据完整性有无结构性防御** | ⚠ W3 只治了裁剪侧（N20） | ⑤ 单调性校验 + 裁剪双字段交叉校验 + dry-run 默认 + 审计日志；**自测 12/12 拦住**（构造的降级写入、构造的会删 verified 的裁剪） | **✅ 建立**。`dataset_guard.jsonl` 4 条（2 refused + 2 forced，均出自自测）、`prune_audit.jsonl` 2 条（生产，M=0） |
| **4 个被误删的 verified 归档** | ⚠ W3 已知缺口 | 重建 4 commit × 5 文件 = **20/20 逐字节一致**（6.9min，3 次 era 命中） | **✅ 缺口补齐**；bit 确定性从 3 个二进制扩到 **20 个文件 / 4 个 commit** |
| **策略 A 在 `located` 记录上是否可行** | 🅗（W3 只在 not_located 上跑过 A） | 10 条（8 located）→ **7 次真实构建**、9 strict + 1 loose；advisory 与 best_depth 一致 7 / A 更浅 1 / 更深 0 | **✅ 支持 Phase 2 的改动**；且抓到 advisory 指错格的实例（OSV-2020-2251） |
| **W1 策略模型** | ⛔ W3 已作废 | W4 再测：B 反事实 8 次构建 vs A 实测 7 次 → **A 不更贵**，还多拿 1 条 strict | **作废确认**（第三次被实测否证） |
| **N19 能否构建前判定** | 🅗 W3（只归类，未预防） | 预检 harfbuzz **6/6**、pcapplusplus **3/3** 命中、已知能建的 6 条 **0 误报**；成本 0.0–22.6s/条 vs 白跑构建 90–320s | **✅ 可预防**。发现 N19 有**两种形态**（→ **N23**） |
| **早停能否省时间** | 🅗 W3 自列待办 | 生产触发 1 次（pcapplusplus）→ 3 次构建后封项目、跳过 9 条（最多省 27 次构建），该轮 9.4min 收尾 | **✅ 有效**；N=2 的理由见 §4.28 3b |
| **i386 是否影响 tier** | ⓘ W3（n=1，两架构 tier 相同） | **n=3，3/3 从 medium/loose 升 strict**；其中 1 条 x86_64 下崩成**另一个 bug** | **✅ 有显著影响** → ⑥ 默认按 `job_arch` 构建（**N22**）。**未**因此加通用架构维度 |
| **N21 的对照改造** | 🅗 W3（判据需版本感知） | 改用 HEAD 为默认后 **11/11 通过 + 正对照 2/2**；版本感知补充 3/3（窗口均不含被测 commit） | **✅ 落地**，§1.7 I 已更新 |
| **MSAN 全链路** | ✅ W3 打通 | 累积 `memory` 复现率 2/3 | 无变化；**flaky 重试路径仍未触发** |
| **UBSAN 正样本** | ⓘ 零真实样本 | pcapplusplus 3 次 UBSAN 钉版全失败（N19 形态②）→ 早停 | **仍未解决**（§4.33） |

## 4.33 W4：仍 🅗/ⓘ

| 条目 | 为什么没解决 | 需要什么 |
|---|---|---|
| **UBSAN 判定路径零正样本** | 两个候选都不行：pcapplusplus 构建失败（N19 形态②，预检现在能拦但拦掉就意味着没样本）；libtsm 那条数据自相矛盾（`fixed==introducing==HEAD`、recovered 帧是描述文本） | 找一条 UBSAN crash，其项目**可构建**且 `fixed` 明确（🅗 候选：libvips 7 条 / hdf5 7 条 / kimageformats 7 条 / draco 6 条 UBSAN，均需新镜像 ~2.2GB） |
| **A vs C 定论** | `not_located` 累积 **11 条**（目标 ≥30）；且 W4 的 10 条里只有 2 条是 not_located | 再补 ~20 条 not_located 走完三格 ≈ 40–60 次钉版构建；**必须挑可构建的项目**（harfbuzz/pcapplusplus/flatbuffers 都不行） |
| **MSAN flaky 重试（≤3×）** | 现有 3 条 MSAN 都首次即出结果 | 需要一条真 flaky 的 MSAN crash（🅗 MSAN/uninit 全量 875 条里应有） |
| **可构建率外推** | 8 个项目的便利样本；三类系统性失败（N19 两形态 + `-Werror` 工具链漂移）在样本里过表达或欠表达都可能 | 随机抽 20–30 个项目跑 HEAD+1 格钉版；受磁盘（**8.3G**）与镜像成本（~2.2GB/项目）限制 |
| **预检覆盖率只有 22%** | 176/249 项目的 build.sh 提取不到候选路径（多用变量、或 target 由 `make` 隐式规则产出） | 要么放宽候选（误报风险，已实测吃过亏），要么改用「构建一次后缓存该项目各 era 的失败形态」（🅗） |
| **N16 重试仍未验证** | W3、W4 都没遇到 `network_fetch` 失败 | 重跑 W2 的 c-blosc2@`9ba29ef1`（已知会网络失败）即可验证 |
| **N12 的 🅗 改进（`frac≥0.6` 即停）** | W4 只有 1 条走了 3 格且三格全 loose（OSV-2020-2184，`frac` 全 1.0）→ 支持该建议但 n=1 | 更多「loose 且 frac 高」的样本；或直接实现后 A/B 对比 |
| **版本感知对照在 libtsm 上不可用** | libtsm 走 `introducing` 路（无 `fixed~d`），且其 commit 日期取不到 | 给 `introducing_commit` 也解析日期（`.patch` 端点）；或接受该项目只用 HEAD 对照 |

## 4.34 W4 卡点

**没有硬卡点，四个 Phase 全部完成。** 三处「做了但不完整」：

| 项 | 现象 | 已排除 | 下一步 |
|---|---|---|---|
| UBSAN 仍零正样本 | 唯一新候选项目 pcapplusplus 构建全失败 | 不是 ③ 的判定问题（fixture 4/4 通过、构建确实带 `-fsanitize=…`）；是 **N19 形态②** 挡住了构建 | 换一个可构建的 UBSAN 项目（需新镜像） |
| `not_located` 只到 11 条 | 可构建项目里 not_located 已被挖尽（c-blosc2 8 条全跑过） | 不是预算问题（本轮 `--max-builds 12` 只用了 7） | 对 pcre2/md4c/libtsm/hunspell 跑完整静态 check 找新的 not_located；或纳入新项目 |
| 磁盘 8.3G | 归档 989MB（verified 变多→保留变多）+ 8 个项目镜像 | 裁剪每轮都在跑且 `M=0`；`--min-free-gb 4` 未触发 | 🅗 若要跑含新项目的轮次需 ≥8G；或把 `--min-free-gb` 提到 6 并清掉不再用的项目镜像（wolfssl 已清） |

## 4.35 W4 约束遵守

| 约束 | 结束时实测 | 命令 |
|---|---|---|
| 主树 `/root/gyx/oss-fuzz` 只读、须 **550** | **550** ✅ | `git -C /root/gyx/oss-fuzz status --porcelain \| wc -l` |
| worktree 停 `repro-patches`、无未提交改动 | `repro-patches` @ `07522dc0e`、`status --porcelain` = **空** ✅（N18 的 `git restore --staged` + `clean` 每次钉版后都跑） | 同上（worktree） |
| `infra/` 三补丁不得改动 | md5 汇总 **`f5092d0a3f2a6909`**，与 W2/W3 一致 ✅ | `md5sum infra/{common_utils,helper,build_specified_commit}.py` |
| 不动 driver_create | **0** 脏项 ✅ | `git -C /root/gyx/driver_create status --porcelain \| wc -l` |
| gate 五条件（含镜像自动重建+复检） | 每次 ② 调用都跑，全过；本轮**未**触发重建（harfbuzz 镜像 W3 已重建、pcapplusplus 是新建） | ② gate 输出 |
| 不改 Dockerfile/build.sh | 未改（N19 的处置是**构建前预检 + 分类 + 早停**，不是改上游脚本） | – |
| 不加架构维度（除非 4(d) 显著） | 4(d) 结果显著（3/3 升 strict）→ **只**在 ⑥ 加 `--match-job-arch`（默认开）+ 复用 W3 已有的 ② 缓存键/归档路径架构分量；**没有**动 ① 的 schema、没有把架构变成通用维度 | `run_repro.py --help` |
| 不装 clusterfuzz | 未装 | – |
| docker / 网络 | 构建 **~15 次**（4 次归档重建 + 7 次策略 A + 3 次 pcapplusplus + 1 次 c-blosc2 HEAD）、i386 配对构建 **3 次**、复现执行 **~30 次**、负对照 **13 次**；预检走 `raw` 端点（**0 API / 0 clone**，磁盘缓存）；未访问 gcloud | `artifacts/logs/`（build 52 / reproduce 128 / negctl 14 / negctl_head 13） |
| 自测护栏 | ③ **4/4**、④ **4/4**、② 分类器 **10/10**、Phase 1a 两道防御 **12/12**、① 回归 **25 通过 / 0 不符 / 4 争议** | 各 `--selftest` 与 `preflight/selftest/w4_phase1a_selftest.py` |
---

## 4.36 W5 Phase 1：N12 的离线回放与停止判据（默认 OFF + shadow 常开）

**为什么能离线定论（0 次构建）**：W3/W4 的 walk-back 跑的是「不达 medium 就继续下探」策略，
所以**更深格的结果都已经被观测到了** → 停止规则的反事实是**完全可观测**的（off-policy
evaluation）。数据在 `artifacts/runs/*/walkback_trace.jsonl`：5 个 run / 24 条 crash / 31 个构建成功的格。

| 阈值 | 触发 | 省构建 | **tier 损失** | 不同 crash |
|---|---|---|---|---|
| 0.5 / 0.6 / 0.7 / 0.8 / 1.0 | 5 | 7 | **0** | **3** |

* **五个阈值结果完全相同** → 扫描无信息量：`frac` 只取 `{0.0:10, 0.3333:1, 0.6667:2, 1.0:18}` 四个离散值，0.5–1.0 之间没有可分辨样本 → **沿用预注册的 0.6**（不是按数据挑的，避免在小样本上过拟合）。
* **计数口径纠正（W5）**：5 次触发只来自 **3 条不同 crash**（OSV-2020-1016 / OSV-2020-2184 / OSV-2022-511）—— 同一条在 depth1、depth2 各触发一次（**嵌套**）。**「触发次数」≠ 独立样本数**，决策只看 `distinct_crashes`。
* 项目集中度 `c-blosc2 20 / harfbuzz 3 / pcapplusplus 1` → 结论被单一项目主导的风险。

**决定：`--stop-frac` 默认 0（OFF）**，两条理由：① n=3、2/3 是 c-blosc2 → 太小；② **默认 ON 会摧毁测量通道** —— 一旦停了就再也观察不到更深格，W5 扩样本便永远无法给 N12 定论。代价 = 一轮多花 **7/31 ≈ 23%** 的格构建。**这是「省构建」与「保住定论能力」的取舍，选后者**（本项目已四次出现「模型输给实测」，不应为省一小时而关掉测量）。

**预注册翻转判据**：`distinct-crash n≥10 且 tier 损失 0` → 默认改 0.6（现 n=3，**还差 7 条**）。判据写在代码 help、回放脚本输出与本节，三处一致。

**实现**（TDD，自测 19 项）：判据抽成纯函数 `run_repro.stop_decision(tier, frac, reproduced, stop_frac, shadow_frac=0.6)` → `{stop, reason, would_fire}`；`TIER_RANK` 提到模块级（原先在循环内重复定义）；⑥ 的 CLI 抽成 `build_argparser()` → **默认值可在不跑 docker 的前提下被自测检查**。守卫：`frac` 为 None 或 `reproduced` 为假 → 一律不停（实测未复现格 `frac` 恒为 0.0，双保险）。`best` 取格逻辑不动（仍取已试格里最好的）→ **frac 停不可能让结论差于「已观测到的最好格」**。

**生产对照**（同一条 crash OSV-2020-2184、同一批缓存构建，两轮）：

| 轮次 | `--stop-frac` | 试了几格 | shadow | `stop_reason` | tier |
|---|---|---|---|---|---|
| `w5-shadow-A` | 0（默认） | **3** | 3 格全 True | `None` | loose |
| `w5-fracstop-B` | 0.6 | **1**（depth1 即停，**省 2 次构建**） | 1 格 True | **`frac`** | loose（**无损失**） |

**复算**：`python3 preflight/selftest/w5_phase1_replay_stopfrac.py`（→ `w5_phase1_replay_stopfrac.json`）。
脚本内置**交叉校验**：W3+W4 子集 @0.6 必须等于定稿时内联算出的冻结值（5/7/0/**3**），
漂移即红 → 本轮 ✅ 通过。

## 4.37 W5：N16 重试的离线注入验证（「重跑一次」销不掉这条账）

**为什么不能靠真实重跑**：`build_records.jsonl` 里同一个 key `c-blosc2|address|9ba29ef1…` 有**两条**记录 —— `fail_pinned/compile_error`(ts 1788940358) → **`ok`**(ts 1789034514)，即该 commit **现在能建成功**；而网络失败本身是瞬态的 → 重跑几乎必然首试即过 → **重试分支仍然不会被执行**。§5 里「重跑 c-blosc2@`9ba29ef1` 即可验证」这条待办**据此作废**。

**做法**：docker 边界就是 `run_cmd` → 替掉它（连同 `LOGS`/`restore_projects`/`archive_build`/`_learn_era` 共 5 处边界），跑**真的** `build_pinned()`，喂合成日志。测的是**真接线**，不是分类器。

| 用例 | 期望 | 结果 |
|---|---|---|
| `network_fetch` 首试失败 → 重试成功 | 调 2 次；第 2 次日志 `*_retry1.log`；记录 `build_status=ok`（不被首试污染） | ✅ |
| `network_fetch` 两次都失败 | 只试 2 次（**不无限重试**）、记 `fail_pinned` | ✅ |
| `compile_error` | **不重试**（1 次）、类别正确 | ✅ |
| `--no-retry-network` | 即使是网络失败也不重试（开关有效） | ✅ |
| **负对照**：分类器恒返回 `compile_error` | 重试**不再**触发（1 次）→ 证明「重试 2 次」确由分类结果驱动、测试有牙 | ✅ |

**账目状态改写**：从「**代码路径从未执行**」→「**机制已离线验证 ✅ / 生产触发仍未观测 ⓘ**」。这是能达到的最强结论：剩下的是运气（要正好遇到一次网络失败），不是工程。

## 4.38 W5：N25 —— 已引用的证据被静默销毁

**发现路径**：为验证 N16 去翻 W2 那条网络失败的日志 → `GnuTLS recv error` / `RPC failed` / `Could not fetch origin` 在 `artifacts/logs/build/` 里 **0 命中**。

**根因**：`run_cmd` 用 `open(log_path,"w")` 无条件截断，而日志名只由 `{project}_{san}_{commit[:12]}` 决定 → **重跑同一 commit 必然覆盖上一次的日志**。

**实证**：`c-blosc2_address_9ba29ef1584b.log`（37,204 B / 482 行）现在的内容是 **2026-09-10 18:00 那次成功构建**（尾部是把 fuzzer 拷进 `/out`），而 `build_records.jsonl` 里同 key 的两条记录（失败的那条与成功的那条）**都指向这一个路径**，且本文 §4.5 曾引它作 **N16** 的证据 → **该引用已不可复算**。

**修法**：`rotate_existing_log()` 挂在 `run_cmd` 的**唯一写盘点**上 → 写之前若同名文件存在则改名保留（`<name>.<UTC 时间戳>`，同一秒内多次再加序号，不互相覆盖），**永不销毁**；目标不存在时返回 None（不产生空文件）。自测 7 项，含端到端：同一 `log_path` 连跑两次 `run_cmd` → 当前日志是最新一次、**上一次的内容仍能在轮转文件里找到**。

**生产实证（本轮就抓到一次）**：`w5-shadow-A` 重建 c-blosc2@`af4860f071a1`（该 commit 2026-09-10 18:03 建过）→ 旧日志被轮转成 `c-blosc2_address_af4860f071a1.log.20260914T015239`（37,844 B）**保留下来**，当前路径写新一次（ts 2026-09-14 09:52:39）。**这就是销毁掉 N16 证据的同一个场景，如今不再发生。**

**归类**：与 **N20**（归档侧被误删）同根因 —— **派生产物被后来的运行覆盖，而结论仍引用它**。W4 修的是归档侧，W5 修的是日志侧；manifest 侧见 §4.39（N26）。

## 4.39 W5：N26 —— 覆盖护栏，以及我的一次误判与自纠

**footgun（两个形态）**：① `manifest_builder.py --only-osv 3 条` 配**默认 `--out`** 会把全局 manifest **3,790 行覆盖成 3 行**（`main()` 写的是过滤后的 records）；② 不带 `--static-check` 的全量重跑会把 `fixed_real` 刷成 0。

**修法**：`overwrite_guard(old_rows,new_rows)` 纯函数挂在**唯一写盘点** `write_outputs()`：**覆盖面缩水**，或**交集行**上任一强度字段（`repo_path`/`fixed_real`/`static_check_verdict`（`skipped`/`not_run` 视为空）/`degenerate_resolved`）**由有值变空** → 拒写、退出码 **4**、点明具体字段与例证；`--force-overwrite` 才写且记 `artifacts/manifest_overwrite_audit.jsonl`。**只在交集上比强度** → 子集运行/新增行不误报。自测 14 项（含负对照：完全相同 → 放行且无原因，证明不是恒拒）。

**生产验证**：`python3 manifest_builder.py --limit 5 --out artifacts/repro_manifest.jsonl` → ❌ 拒写「覆盖面缩水：老 3790 行 → 新 5 行（丢 3785 行）」、退出 **4**、文件仍 **3,790 行**。

**我的一次误判与自纠**（记下来，因为它本身就是缺陷证据）：
1. 我看到 ① 回归从 W4 的 **25 通过 / 0 不符 / 4 争议** 变成 **20 / 0 / 9 跳过 / 0**，判断「正典 manifest 被我削弱了」。
2. **核查后不成立**：全局 manifest 仍是 `repo_path 3648 / degenerate_resolved 53 / static_check_verdict 非 skipped 293`，而 §6 记载的正典命令本就**不带** `--static-check`（`fixed_real` 一直是 0；那 167 条在 `artifacts/runs/w3-p5-*/manifest.jsonl` 里，**未受影响**）。交付复现记录表 `repro_dataset.jsonl` 是 append-only，也未受影响。
3. **真因**：**回归结果依赖 flag，而 §6 没记 flag**。带 `--static-check --only-osv <3 条已知答案>` 复算 → **25 通过 / 0 不符 / 0 跳过 / 4 争议**，与 W4 一致。→ 已把 flag 补进 §6，否则这个数字永远看起来像回归。
4. **顺带修的两处**：① `load_repo_path_map` 的 docstring 与代码**相反**（说「缺失时回退 `/src/<project>` 并标 medium」，实际 `resolve_repo_path` 返回 `(None,"none",[])`，理由是「宁缺勿错」）—— 正是它把我引向「以为是 static-check 的锅」，已改正并写入踩坑记录；② `--repo-map` 指向**不存在**的路径会让**全部** `repo_path` 变 None（回归 3 不符）→ 对照实验必须**复制真缓存**再用，别指空路径。

**教训（与 N24 同型）**：我又一次先信了「数字变了 = 数据被毁了」的直觉，而没有先查**产生数字的命令**。护栏值得加（footgun 是真的），但**触发我加护栏的那次判断本身是错的** —— 两件事都记，不因为结论对了就掩盖推理错了。

## 4.40 W5 自查清单与约束遵守

**自测 inventory（8 套全绿，均可复算，见 §6）**

| 套 | 项数 | 覆盖 |
|---|---|---|
| ③ `repro_runner.py --selftest` | 4/4 | 执行与解析 |
| ④ `verify_tiered.py --selftest` | 4/4 | 分级三量 + `normalize_frames` 对账 |
| W4 完整性防御 `w4_phase1a_selftest.py` | 12/12 | ⑤ 单调性 + 裁剪交叉校验 |
| ② `w5_selftest_bo.py` | 15 | **日志轮转 7**（N25）+ **N16 重试接线 8**（含负对照） |
| ⑥ `w5_selftest_stopfrac.py` | 19 | 停止判据（tier 停 / frac 停 / 守卫 / shadow / CLI 默认值） |
| ② `w5_selftest_classifier.py` | 18 | **新固化**：13 类别 + 大日志不截断 + 倒序负对照 |
| ⑤ `w5_selftest_annotate.py` | 11 | `walkback_stop_reason` 透传 + 既有字段回归 + 负对照 |
| ① `w5_selftest_overwrite.py` | 14 | 覆盖护栏（覆盖面 / 字段强度 / 交集口径 / 负对照） |

① 已知答案回归：**25 通过 / 0 不符 / 0 跳过 / 4 争议**（命令含 flag，见 §6）。

**本轮 4 个自查缺陷**：① ⑤ 白名单漏 `walkback_stop_reason` → dataset 与 trace 分叉（TDD 抓到，2 项红 → 修 → 绿，并端到端复验 dataset 行确为 `'frac'`）；② `load_repo_path_map` docstring 与代码相反；③ §6 的 ① 回归命令未记 flag；④ ② 分类器自测从未固化成文件（§6 声称可复算，实际是内联 heredoc）。

**约束遵守**：主树 **550**（未变）｜worktree `repro-patches@07522dc0e` **干净**｜`infra/` md5 `f5092d0a3f2a6909`（未变）｜`driver_create` **0** 脏项｜未改任何 Dockerfile/build.sh｜未动 ① schema 的既有字段（只**新增** `walkback_stop_reason`）｜磁盘 **7.9G**｜本轮**未新建任何镜像**、**未跑全量 3,093 队列**。

**dataset**：166 行 / **12 个 run**。本轮新增 3 行均为**接线验证**（`w5-shadow-A`、`w5-fracstop-B`、`w5-fracstop-B-refix`），tier 均 `loose`、`run_status=run` → **未触发 ⑤ 单调性护栏**（无 verified 被降级）。

**交付形态**：本轮**无独立报告文件**，全部内容在本文 §4.36–§4.40；根目录 `.md` 仍只有 `DELIVERY.md`。


## 4.41 W5 扩样本第一轮：19 条本地镜像池（run `w5-expand19b`）

**范围选择的依据**（先量后选，不猜）：本地已有 10 个镜像；其中**已证可构建**的项目里未采样的主线 crash **只有 19 条**（libspng 11 / pcre2 3 / libtiff 2 / c-blosc2 1 / flatbuffers 1 / hunspell 1）。**这 19 条喂不饱两条预注册判据**（`not_located` 就算 18 条全是也只到 29 < 30；N12 shadow 按下探率 ~12.5% 估只能再攒 2–3 条）→ 本轮定位为「零镜像成本的确定收益 + 为下一步选镜像提供实测」，**不承诺销账**。

**结果**：21 次真实构建 / 41.6min 墙钟 → **2 strict + 4 medium + 13 none**，**本轮复现率 6/19 = 31.6%**（高于累积 16.7%）。

| 指标 | 本轮前 | 本轮后 |
|---|---|---|
| dataset | 166 行 / 132 唯一 / 12 run | **185 行 / 151 唯一 / 13 run** |
| tier（每条取最新） | 10 strict + 9 medium + 3 loose + 110 none | **12 strict + 13 medium + 3 loose + 123 none** |
| 复现 | 22/132 = 16.7% | **28/151 = 18.5%** |
| 复现按 sanitizer | address 20 / memory 2 | **address 20 / memory 8** |
| `not_located` | 11 | **14**（本轮 located 15 / not_located 3 / no_fixed 1）→ 距 ≥30 还差 16 |

**三个值得单记的实测**：

1. **本轮 6 条复现全部是 MSAN（`memory`）** → MSAN 累积 **8/14 = 57%** 复现，远高于 address 的 20/137 ≈ 15%。⚠ 但这是**选择效应**不是因果：19 条池子里 11 条本就是 memory（MSAN crash 在「本地已有镜像且可构建」的项目里占比偏高），不能据此说「MSAN 更容易复现」。
2. **libspng 钉版可构建率 1/19 = 5%**，根因两类：`dead_external_url` **11 次**（日志第 81 行 `Proxy request sent, awaiting response... 404 Not Found` = build.sh 里 wget 的第三方依赖包已死）+ `buildscript_mismatch` **6 次**（`tests/ossfuzz.sh` 不在老 commit 树里，**W4 预检在生产里全部拦下** → 预检在**全新项目**上的首次实战验证）。→ 见 **N28**。
3. **MSAN flaky 重试路径仍未触发**：151 条里 `retry_count>0` 的**为 0**。这条账（W4 待办③）**继续挂着**，且现在看清了：它需要「MSAN 复现非确定性」的样本，而本轮 8 条 MSAN 复现全是确定性的 → **靠扩样本撞上的概率低**，要销账得**人工构造 flaky 场景**（限流 / 改 `runtime_limits`），属另一类工作。

**N12 的 shadow 累积（回放口径，含本轮 trace）**：9 个 run / 47 条 crash / 43 个构建成功的格 → 阈值 0.6 触发 **7** 次、省 **10** 次构建、**tier 损失 0**、distinct-crash 仍是 **3**（本轮 19 条里 6 条达 medium+ 即停、13 条走完，**没有一条**出现「loose 且 frac≥0.6 且还有更深格」的形态）→ **距翻转判据 n≥10 还差 7 条**。`walkback_stop_reason` 本轮分布 = `tier` 6 / `null` 13 / **`frac` 0** → 默认 OFF 被正确遵守。

**轮末裁剪**（默认开、`--prune-apply`）：26 个归档目录 → 保留 23（被 verified 引用：strict 16 / medium 14 / loose 8）、删 3、回收 **213 MB**、`M=0`（W4 的交叉校验护栏通过）、保留 1126 MB。磁盘 7.9G → **7.4G**。

**可构建率（累积，按项目）**：hunspell 12/12=100%、libtsm 3/3=100%、c-blosc2 51/53=96%、md4c 12/13=92%、pcre2 14/16=88%、flatbuffers 5/15=33%、**libspng 1/19=5%**、harfbuzz 0/7、pcapplusplus 0/3。⚠ 这再次说明**便利样本外推会显著高估**：加入 libspng 后，「已证可构建项目」的集合里就出现了一个 5% 的。

## 4.42 W5：预检自身的三个缺陷 + 「下一个建哪个镜像」的离线筛选

**(a) 三个缺陷（全部 TDD 修完，自测 `w5_selftest_precheck_sha.py` 15 项）**

预检的契约写在它自己的 docstring 里：**「无法判定时一律放行」**（宁漏勿误，因为误报会跳过本能成功的构建）。✅ W5 实测发现**三条违反契约或漏检**的路径：

| # | 缺陷 | 实证 | 修法 |
|---|---|---|---|
| ① | `sha=None` 被判成**确定缺失** | `_raw_url` 直接插值 → `raw/None/<path>` → 必然 404 → `path_exists_at` 返回 **False** 而非 None。libredwg 在 `sha=None` 下报 `missing=['./autogen.sh','examples/llvmfuzz.c']` 而 `checked=0`（**一次都没真查**）。生产调用点传的是计划里的真 commit → 当前**潜伏**，但任何离线调用方都会中招 | `path_exists_at` 与 `precheck_buildscript` 双双在缺 `sha`/`repo_url` 时**发 HTTP 之前**短路返回「无法判定」；`reason='no_sha'`（与 `no_candidate_paths` 区分开） |
| ② | 候选保留 `./` 前缀 | `raw/<sha>/./autogen.sh` 这种 URL 不该用来判存在性 → 假 404 → **误报**（即使 sha 有效） | `_norm_cand()` 去 `./`；归一化后若变成单段名，会被既有「`/` not in t → 不查」规则挡掉 → 结果是**少查一个**（漏报），符合宁漏勿误 |
| ③ | `SCRIPT_RE` 对「解释器与脚本之间夹 flag」瞎 | ndpi/build.sh 第 24 行 `bash -x ./ndpi/tests/ossfuzz.sh` → 报 `no_candidate_paths`（**无证据**）。而直接查：`tests/ossfuzz.sh` 在抽样 **3 个 commit 上全部缺失** = pcapplusplus/libspng 同型的 0/N 灾难 | 只放宽「破折号开头的 flag」这一种形态（`\b(?:bash\|sh\|source)\s+(?:-\S+\s+)*`），**不**放宽成任意 token（W4 教训：宽口径会把 LICENSE URL / `$OUT/*.zip` / `.libs/*.a` 抓进来 → 必然 404 → 误报更糟） |

**(b) 已知答案回归固化**（`w5_precheck_known_answers.py`；W4 那次验证是内联 heredoc → §6 声称可复算而实际不可，与 ② 分类器自测同一个毛病）：
**真报不放跑** harfbuzz **4/4**（形态①）+ pcapplusplus **3/3**（形态②）+ libspng **4/4**（形态②，W5 新增）= **11 条**；**误报不新增** c-blosc2 / flatbuffers / hunspell / libtsm / md4c / pcre2 共 **23 个已成功 commit → 误报 0**；契约用例 2 项。**全绿**。

**(c) 我写这套测试时自己犯的三个错**（记下来，因为它们与被测缺陷同族）：

1. **测试期望错**：[A] 节起初把 `toolchain_drift` 也算作「预检该拦」→ libspng 报 3/4「放跑 1 条」。查根因：那条 `f47ed26affe9` 实测类是 **toolchain_drift**，而**路径存在性检查在构造上就预测不了工具链漂移** → 预检放行是对的，**错的是我的期望**。判据改成非循环的两条（类已是 `buildscript_mismatch`；或类是 `compile_error`/`toolchain_drift` **且日志里确有** `unknown target`/`No such file or directory`）。
2. **静默跳过**：改完判据后 pcapplusplus 变成「无记录，跳过」——因为判据只认形态①，而它是形态②。而我的防空过断言因为 harfbuzz+libspng 凑够 8 条**照样通过** → 补上形态② + 断言「**被跳过的项目必须为零**」。
3. **测试框架自己骗自己**：`patched()` 把传入的可调用又包了一层 lambda 并 `return exists` → 返回的是 **lambda 对象本身（恒真）** → 预检以为路径都存在，[B]/[C] 两节**空过**。是靠「[B] 实调 0 次 vs [C] checked=2」这个**内部不一致**才发现的。

**(d) 「下一个建哪个镜像」的离线筛选**（`w5_screen_next_projects.py`，**0 次 docker / 0 次构建**）

为什么需要：镜像 ~2.2GB/个、磁盘仅 7.4G → 最多再建 2–3 个，**赌错就是数小时白跑**。用 W4/W5 实测出的两个主导失败模式当预测因子：① build.sh/Dockerfile 里的**第三方**外链数（`dead_external_url` 风险，libspng 11/19）；② 在**真实钉版 commit** 上跑预检（`buildscript_mismatch` 风险，走 raw 端点、0 API 0 clone）。未采样 crash 没有 `fixed_parent`（那是静态 check 的产物）→ 退用 `fixed_commit`（与 walk-back 起点 `fixed~1` 只差一个 commit，作先验足够），**并在输出里记录用了哪个来源**。

池子：主线 + 有 `fixed_commit` + 未采样 = **2,801 条 / 239 个项目**。

| 结论 | 项目 |
|---|---|
| ⛔ **出局**（错配 3/3，harfbuzz 同型） | **ndpi**(池 142)、**fluent-bit**(73)、**mruby**(71)、**openexr**(44) → **省下 4×2.2GB 镜像 + 数小时注定失败的构建** |
| ✅ **有正证据**（真查过路径、0 缺失、0 第三方外链） | **libredwg**(68)、**radare2**(56)、**opensc**(79，1 条外链) |
| ⓘ **无证据**（查不了，附原因） | ghostscript(192，`git://` 非 github → undecidable)、openh264(64)、arrow(58)、matio(52)、libxml2(52)、php(50)、libavc(43) |

**→ 建议先建 `libredwg`（池 68、0 第三方外链、3 个路径实测都在），其次 `radare2`。**

**(e) 差点做出的错投**（这条比结论本身重要）：**修 bug③ 之前，ndpi 排在推荐序第 1**（池 142、0 外链、"错配 0/3"）——而那个 `0/3` 的真实含义是 `no_candidate_paths` = **一条路径都没查**，不是「查了没问题」。ndpi 的 build.sh 恰恰执行一个在**全部抽样 commit 上都缺失**的脚本。**发现靠的是手工 `cat ndpi/build.sh`，不是筛选表。** → 由此定出 **N29**：「查不了」必须与「查过没问题」分级显示。现在筛选表按三级证据输出（✅真查过 / ⓘ无证据附原因 / ⛔全中出局），排序对「无证据」折半 → ndpi 从第 1 变**出局**。

## 4.43 W5 第二轮：92 条积压重跑 —— "版本跑错了"的账，一次收掉 42 条

**(a) 积压是怎么被发现的**

用户问「151 条里为什么只有 28 条复现」→ 把 123 条未复现按根因分层，而不是笼统说"失败"：

| 类别 | 条数 |
|---|---|
| **构建成功、跑了、没崩** | **104** |
| 构建失败（`compile_error` 7 + `dead_external_url` 4） | 11 |
| 没有可用二进制（6 skipped + 2 无记录） | 8 |

那 104 条里 **98 条跑在 HEAD**，其中 **92 条本身是有 `fixed_commit` 的** → 也就是说**跑的是已经修好的版本**，不崩是应该的；97 条来自同一个 run `w2-p3-final`（W2 的第一批）。真正"在钉版上试过仍未崩"的只有 **6 条**。两条路线的复现率把这件事定量了：

| 路线 | 复现率 |
|---|---|
| HEAD | **7/105 = 6.7%** |
| 钉版 walk-back | **21/46 = 45.7%** |

**6.8 倍差距。** 所以那 92 条不是"复现失败"，是**积压**——从没在对的版本上试过。

**(b) 根因：排序键与路由规则错位（不是"忘了重跑"）**

`--sort` 默认 `no_fixed_first` 是 **W2 在 HEAD-first 路由下**定的（理由：无 fixed 的只能试 HEAD，先跑掉）。**W3 用实测把路由翻成 has_fixed→钉版**（45.7% vs 6.7%）之后，**排序键没跟着改** → 收益最高的那批被系统性排到队尾：

* ✅ 实测：92 条积压在默认序里位于第 **196–2996** 位（中位 **1650**），而历轮 `--limit` 最大才 30 左右 → **三轮都碰不到它们**。
* 修：① 与 ⑥ 的 `--sort` 默认改 **`fixed_first`**（TDD 断言默认值，防止被无意改回）。
* **教训**：改路由/判据规则时，必须同时检查**选样与排序键**——否则新规则永远作用不到旧队列，而复现记录表上看起来"每条都试过了"。

**(c) 结果（分块跑，每块 ≤23 条）**

| 轮次 | 条数 | 复现 | tier | 构建 | 墙钟 |
|---|---|---|---|---|---|
| `w5-backlog1`（c-blosc2 23） | 23 | **23/23 = 100%** | 14 strict + 1 medium + 8 loose | 40 | 56.1 min |
| `w5-backlog2`（c-blosc2 23） | 23 | **19/23 = 83%** | 13 strict + 2 medium + 4 loose + 4 none | 32 | 48.4 min |

**累积：复现 28 → 70 条（151 条里的 46.4%）；tier 39 strict + 16 medium + 15 loose + 81 none。**

* 两块合计 **42 条新增复现**，与"按 45.7% 估约 42 条"的预估**吻合**。
* `static_check_verdict` 全部 `located`；`walkback_best_depth` 全部 **1**（chunk2 23/23 在 depth1 就中）→ 再证策略 A 的"从 `fixed~1` 起"是对的。
* **i386**：chunk1 9 条（6 strict + 3 loose）、chunk2 7 条（4 strict + 1 medium + 1 loose + 1 none）→ **N22 的架构匹配在批量上有效**（21 条 i386 里 10 条 strict）。
* ⚠ **项目集中度恶化**：c-blosc2 占 **58/70**（积压里 72 条本就是 c-blosc2）→ 复现率的**绝对值**越来越像"c-blosc2 的复现率"，跨项目外推要更小心。
* 存储：逐条回收使归档在 **72 次构建**下基本不涨（1088 → 1137 MB），磁盘持平 7.4–7.7G。

**(d) 逐条回收（purge-on-verify）—— 以及它造成的事故**

* **必要性**（✅ 实测算出来的，不是拍的）：92 条一轮的归档峰值 ≈ 92×50MB ≈ **4.6GB**，而磁盘只有 7.7G → 沿用"轮末裁剪"会中途撞 `--min-free-gb` 护栏而**中止整轮**。
* **安全性依据**：W4 已实测归档重建**逐字节一致 20/20** → 删除是**可恢复**的；行留住 `binary_sha256` + 完整配方（`pinned_commit`/sanitizer/arch/era）并标 `binary_pruned=true`。HEAD/`_shared` 归档**永不删**（共享 + 负对照要用）。
* **事故（N30）**：`purge_archives` **没查 dataset 保护集**，而**钉到同一 commit 的 crash 共享同一个归档目录** → `purge_on_verify:OSV-2021-1676` 顺手删掉了 **OSV-2021-1663 / OSV-2021-1712**（都是 `w4-stratA` 的 **strict** 行、**W4 已交付**）的证据，而那两行**没有任何标记** → 无声悬空指针。`prune_archive` 本来有保护集 + `pinned_commit` 交叉校验，**我新加的这条路径把它整个绕过了**。
* **发现路径**（值得记）：不是设计时想到的，是核查"85 条悬空指针"时**按 tier 分层**，发现其中 2 条是 `strict` 且来自 W4 → 再去 `prune_audit.jsonl` 的 `why` 字段顺藤摸到是哪次 purge 删的。
* **修**：`purge_archives` 加 `dataset_path` 保护集（已落盘的 verified 行引用的目录一律保住），⑥ **必传**；TDD [F] 4 项，含"不传 dataset_path 就无保护"的对照（证明该参数真起作用）。
* **证据已恢复**：重建 `c-blosc2/address/79b6995a…` → **5/5 文件 sha256 与 dataset 记录逐字节一致**（顺带把 W4 的 bit 确定性从 4 个 commit 扩到 **5** 个）。
* **对照**：轮末 `prune` 删掉的 verified 证据 = **0 条** → 损伤确实只来自我新加的那条路径，不是老机制的问题。
* **另修**：还有 **60 条**历史 `none` 行的 `binary_dir` 也悬空（W3 轮末裁剪删的、从来没人标）→ ⑤ 在 `merge()` 里**按目录是否存在兜底标注**（TDD [D] 4 项）。60 条全是 `none` 档，按 §1.6 本就不在交付子集 → **无交付损失**，但"标记"是复现记录表的责任，不能靠消费者自己猜。

**(e) N12 按预注册判据翻转默认值**

* 判据（当初同时写在代码 help、回放脚本输出、§4.36 三处）：**distinct-crash n≥10 且 tier 损失 0**。
* 实测：n=**11**、触发 **22** 次、省 **32** 次构建、tier 损失 **0** → **满足**。
* → `--stop-frac` 默认由 `0` 改 **`0.6`**。TDD 顺序照做：**先改断言看它红**（`默认 = 0.0` ❌），**再改实现看它绿**。
* ⚠ **诚实标注**：那 11 条**全是 c-blosc2**（单项目 100%）→ **跨项目泛化未证**。判据当初只写了 n 与损失、**没写项目多样性**，所以按预注册**照翻不误**——事后加条件就是移动球门，那正是预注册要防的。同时把「**多项目轮次显式传 `--stop-frac 0` 作对照**」定为后续动作：`w5-backlog3`（hunspell 20 + c-blosc2 3）就是这么跑的，用来攒跨项目 shadow。

**(f) 本轮 3 个自查缺陷（全部 TDD 修完）**

1. **`purge_archives` 绕过保护集** → 删掉已交付的 strict 证据（N30）。已修 + 证据已重建校验。
2. **⑤ 不标历史悬空 `binary_dir`**（60 条）→ 加"按目录存在性兜底标注"。
3. **`select_purge_dirs` 用黑名单**（"非 head 即删"）→ `path` 字段缺失时会误删；改**白名单**（只删 `path=='pinned'`），fail-safe 偏向保留。自测 [A] 抓到。

## 4.44 W5 第二轮（续）：chunk3/4、N16 生产触发 2/2、N12 翻转后首次触发（在 md4c 上）

**(a) 四块合计**

| 轮次 | 范围 | 进复现记录表 | 复现 | tier | 构建 | 墙钟 |
|---|---|---|---|---|---|---|
| `w5-backlog1` | c-blosc2 23 | 23 | **23（100%）** | 14S + 1M + 8L | 40 | 56.1min |
| `w5-backlog2` | c-blosc2 23 | 23 | **19（83%）** | 13S + 2M + 4L + 4N | 32 | 48.4min |
| `w5-backlog3` | hunspell 20 + c-blosc2 3 | 23 | **22（96%）** | 1S + **16M** + 5L + 1N | 36 | 44.8min |
| `w5-backlog4` | hunspell 3 + pcre2 7 + md4c 2 + libtsm 1 + flatbuffers 10 | **14**（9 条被早停跳过） | **11（79%）** | 4S + 4M + 3L + 3N | 23 | 52.7min |
| **合计** | **92 条积压** | **83** | **75** | — | **131** | **202min** |

**累积：复现 28 → 103 条（151 条里的 68.2%）；tier 44 strict + 36 medium + 23 loose + 48 none。**

* **chunk4 只有 14 条进复现记录表**：flatbuffers 连续 2 次 `compile_error` → **W4 的早停按设计触发**，跳过该项目本轮剩余队列（省至多 8 次构建 × 90–320s）。**这不是丢数据**：被跳过的 9 条**没有被写成"试过没复现"**，下轮可重试（早停只影响本轮、不写 state）。
* **hunspell 的档位画像与 c-blosc2 明显不同**：22 条复现里 **16 条是 medium**（只 1 条 strict），而 c-blosc2 以 strict 为主 → **strict 率强烈依赖项目**（帧是否被内联、是否多一帧顶帧），累积的 strict/medium 比例**不能当全局常数**用。
* **逐条回收的实效**：chunk4 单轮删 **19 个归档 / 释放 897 MB**；四块合计 **131 次构建**，而归档总量 1088 → **1140 MB（基本不涨）**、磁盘始终 **7.4–7.7G**。若不逐条回收，131 次构建 ≈ 6.5GB 峰值 → **必然撞 `--min-free-gb` 而中止**。

**(b) N16 生产触发 2 次、2 次都成功 → 这条账从 ⓘ 升 ✅**

| 轮次 | commit | 首试失败形态 | 重试 | 最终 |
|---|---|---|---|---|
| backlog2 | `5a65e3d8322f` | `git remote update` → `RPC failed; curl 56 GnuTLS recv error (-9)` → `early EOF` → `Could not fetch origin` | ✅ 成功（+80s） | `ok`（223s） |
| backlog3 | `ac116b4bac72` | 同上（首试日志 **835/838/840 行仍在**） | ✅ 成功 | `ok`（62s） |

* **与 W2 那次事故的对照**：W2 的同型失败日志被后来的成功构建**覆盖销毁**（N25），导致 §4.5 的引用永久失效；**这次首试日志完整保留**（重试另存 `*_retry1.log`，且 N25 的轮转已生效）→ 证据链完整、可复算。
* **意义**：重试**直接换来 2 次构建成功**，否则这 2 条各会丢一格（甚至整条）。N16 状态从「机制已离线验证 / 生产触发未观测 ⓘ」升级为 **「机制 ✅ + 生产 2/2 成功 ✅」**。

**(c) N12 翻转后的首次生产触发 —— 在 md4c 上（不在 c-blosc2）**

`w5-backlog4` 里 **OSV-2022-40（md4c）** 在 depth1 拿到 `loose` + `frac=1.000` → 按新默认 `--stop-frac 0.6` **即停**，只试 1 格。这是翻转后**第一次生产触发**，且**发生在 c-blosc2 之外**。

⚠ **但这不构成跨项目泛化的证据，必须说清**：
* 回放显示 chunk3（hunspell 20 条）**一个 frac 停候选都没产生**（该轮 2 次触发都来自 c-blosc2 的 OSV-2022-847）；chunk4 只有 md4c 这 1 条。
* 累积口径：distinct-crash n 已从 3 → **17**、触发 **32** 次、省 **47** 次构建、tier 损失仍 **0**；**但项目分布仍高度偏斜**（回放口径 c-blosc2 76 / hunspell 21 / libspng 11 / 其余零星）。
* 关键在于：「frac 高但更深格能升档」的反例**在 hunspell 上根本没被采到** → 现状不是"验证过没有反例"，而是**"没有可检验的样本"**。这两件事在报告里必须分开写。
* **处置**：默认值**按预注册保持 0.6**（判据已满足；事后加多样性条件＝移动球门，那正是预注册要防的），但在 §5 记明「跨项目证据仍缺 → 在新项目（libredwg/radare2）轮次里用 `--stop-frac 0` 继续攒对照」。

**(d) 本轮**没有**销掉的账（如实记）**

* `not_located` 13 → **19**，距 ≥30 还差 **11**。但**积压里 92 条静态 check 全是 `located`** → **这条账靠积压销不掉**，必须去 2,801 条未采样池（= 需要新镜像）。
* **MSAN flaky 重试仍未触发**（151 条里 `retry_count>0` 为 **0**）→ 靠扩样本撞上概率低，需人工构造。
* **UBSAN 正样本仍为 0**（积压里只 1 条 `undefined`，且未复现）。
* **24 条历史 `none` 行的 `binary_dir` 仍悬空**：append-only 不重写旧行，⑤ 的兜底只对**新行**生效 → 已在 §1.4 记明「`none` 档的 `binary_dir` 是历史指针」。这 24 条**全部是 `none` 档**，按 §1.6 不在交付子集 → 无交付损失；verified 行的悬空指针为 **0**（曾有的 2 条已重建并 5/5 sha256 校验通过）。

## 4.45 W5 第三轮：三次新项目尝试全部失败，以及由此得到的筛选升级

**结论先说**：W5 一共试了 **4 个新项目**（libspng / libtiff / libredwg / opensc），**没有一个产出可用的池**：

| 项目 | 钉版可构建率 | 死因 | 代价 |
|---|---|---|---|
| libspng | **1/19 = 5%** | `dead_external_url` 11（build.sh wget 的第三方依赖已死，N28）+ `buildscript_mismatch` 6（N23 形态②） | 19 次构建 |
| libtiff | **0 条构建记录** | 2 条都是 MSAN，未走到钉版构建 | 低 |
| libredwg | **0/1 = 不可行** | `build.sh:40` 的 `make check-prep -C test/unit-testing/ -j16` 要编 ~100 个 **ASAN 单测二进制**（fuzzer 根本不需要）→ 链接期 `No space left on device`；且单次构建 **30min+** | 镜像 2.51GB + 30min，**已中止** |
| opensc | **0/3 = 0%** | `-Werror` 工具链漂移：`asn1.c:577: error: variable 'octets_left' is uninitialized [-Werror,-Wuninitialized]` → `make Error 1` | 镜像 2.3GB + 探针 10.5min |

对照**已知可用的老项目**：c-blosc2 **142/145 = 98%**、hunspell **48/48 = 100%**、libtsm **5/5 = 100%**、md4c **14/15 = 93%**、pcre2 **24/26 = 92%**（flatbuffers 18%、harfbuzz 0%、pcapplusplus 0%）。
→ **W5 试的每一个"新项目"都失败，而五个老项目全部 92–100%**。这五个老项目的未采样池现在**都已榨干（各 0 条）**。

**(a) libredwg 的事后剖析：筛选 v1 少了一整个维度**

v1 筛选（§4.42d）只量了**可构建性风险**（第三方外链 + 路径错配），**完全没量构建成本**（时间 / 磁盘峰值）。libredwg 在 v1 里排**第 1**（池 68、0 外链、预检真查 3 路径 0 缺失）——这些**全对**，但它：

* `build.sh` 末尾 `make check-prep -C test/unit-testing/ -j$(nproc)` → 编 ~100 个 ASAN 单测二进制，**fuzzer 一个都不需要**；`-j16` 并发 + 同期 docker 镜像重建 → **链接期磁盘打满**（日志 942–958 行连续 `final link failed: No space left on device`，死在 `CCLD mlinestyle/mtext/multileader` 这些单测上）。
* 单次构建 **30min+**（对比 c-blosc2 70–110s）→ 68 条 × ~1.2 次构建 ≈ **40 小时**，即使磁盘够也不可行。
* 处置：**中止该轮**（`kill` ⑥ + 杀容器）。核查无半截状态：dataset 仍 **268 行 / 151 唯一**，只多 1 条 `fail_pinned` 构建记录；⑤ 未跑 → 没有写入任何行。
* ⚠ 不能改 `build.sh` 绕过 `make check-prep`（任务约束：不改上游脚本）→ 该项目在**当前磁盘与时间预算下不可行**，不是"再试试"能解决的。

**(b) opensc 探针：探针纪律有效，排序无效**

* 3 条探针 / **10.5min** → **0/3 构建成功**（全 `toolchain_drift`，中位 172s）→ 早停在连续 2 次确定性失败后**封掉整个项目**，避免了 79 条 × ~3min ≈ **4 小时**的白跑。
* **这正是"先探针再整池"的价值**：opensc 的预检是 **✅ 通过**的（真查 3 路径 0 缺失），外链只 1 条（`git clone openpace`），repo 仅 25MB —— **v1/v2 的所有离线维度都判它可行**，而它 0/3。
* → **预检通过是必要不充分条件**；`-Werror` 这类工具链漂移**离线判不了**，只能靠探针。

**(c) N28③ 在实践中真的把我误导了（仍未修）**

opensc 那次失败，分类器给的 `build_error_detail` 是 **`configure: error: OpenPACE linkage required, but no OpenPACE was found`**，而**真正致命的是** `asn1.c:577 [-Werror,-Wuninitialized]` → `make Error 1`。若照着 detail 去查，我会去修"缺依赖 openpace"（方向完全错）。根因：`ERROR_LINE_RE` 抓**第一条**含 `error:` 的行，而 configure 阶段的非致命报错排在编译错误之前。→ 记为待办（§5），**按根因分组会失真**这一条现在有实证了。

**(d) 一个被实测否证的维度：crash 年份**

我一度想用「crash 越新 → 老代码与新工具链越兼容 → 越可构建」来排序，**数据直接否证**：

| 项目 | 池年份中位 | 2023+ 占比 | 实测可构建率 |
|---|---|---|---|
| libtsm | **2017** | 9% | **100%** |
| c-blosc2 | 2021 | 7% | **98%** |
| pcapplusplus | **2023** | **53%** | **0/3** |
| libredwg | 2023 | 57% | 0/1（不可行） |

→ 年份与可构建率**无单调关系**（真正起作用的是"项目自身的构建方式与依赖"）。v2 只把年份当**描述性信息**打印，**不作预测因子**。这与 W1 的策略模型、W3 的 N8、W4 的 N24 是同一类教训：**先验排序必须让位于实测**。

**(e) 筛选 v2（`preflight/screen/w5_screen_v2_buildcost.py`）：只用实测有区分力的维度**

四个维度，每个都对应一次真实失败：① 第三方外链（libspng/N28）② 仓库内路径是否存在（harfbuzz、pcapplusplus/N19·N23）③ **构建体量**（新增：`build.sh` 是否编测试套件 + repo MB 作耗时代理，校准点 hunspell 10MB=快 / libredwg 93MB=30min+ / radare2 204MB / php 640MB）④ 明确标注**离线判不了**的部分（`-Werror`）。

* v1 的另一个 bug 也修了：判"编测试套件"原用 `/tests?/` 太松 → opensc 的 `$SRC/opensc/src/tests/fuzzing/` 是 **fuzzer 源码本身**会被误判；v2 改用精确模式（`make check|check-prep|test`、`make -C *test`、`ctest`、`ninja test`）。
* **v2 的结果（14 个池 ≥20 的未试项目）：没有一个 ✅ 级候选**：
  * ⛔ **路径错配全中**：ndpi(142)、fluent-bit(73)、mruby(71)、openexr(44)
  * ⚠ **第三方外链多**：ghostscript(192，2 条)、arrow(58，2 条)、matio(52，2 条)
  * ⚠ **repo 偏大**（构建耗时风险）：radare2(56，204MB)、php(50，640MB)、serenity(39，237MB)
  * ⓘ **证据不足**（只能探针）：openh264(64，含 **15 MSAN + 2 UBSAN + 13 i386**)、libxml2(52)、libavc(43)、mupdf(37，含 **30 MSAN**)
* 其中 **libxml2 的 `build.sh` 全文只有一行 `fuzz/oss-fuzz-build.sh`**（无解释器、无 `$SRC/`、无 `./` 前缀）→ 这是 **N27③ 同族的第二个预检盲点**（`SCRIPT_RE` 要求有解释器或行首 `./`）→ 记为待办，未修。

**(f) 由此得到的规模化判断（重要，供决策）**

* 主线 3,136 条里 **2,984 条从未进过复现记录表**，全部需要新镜像；池 ≥20 的项目有 **40 个**。
* 但 W5 的实测命中率是 **4 试 0 中**（新项目的可构建率 0–5%），而 v2 筛选**给不出任何 ✅ 级候选**。
* 因此：**继续扩规模的边际成本已明显上升** —— 每个新项目 ≈ 2.3GB 镜像 + 一次探针（~10–30min），而命中率按现有证据约 **1/4 或更低**；且磁盘只剩 8.9G（同时只能容纳 2–3 个镜像）。
* 相对地，**已知可用的五个项目已全部榨干**，真·剩余积压只剩 **10 条**（flatbuffers 9 + libtsm 1）→ **已跑完：10 条 / 19 次构建 / 10.1min → 复现 0 条**（7 条走到分级、全 `none`）。**至此积压彻底穷尽**：W5 共处理 92 + 10 = **102 条**积压，新增复现 **75 条**（全部来自前 92 条；这最后 10 条按 flatbuffers 实测 18% 可构建率本就期望值很低）。副作用（有价值）：这 7 条从「HEAD 路线没崩」变成「**钉版路线也试过、仍没崩**」→ 真难啃的那一类从 33 条增至 ~40 条，复现记录表上不再有任何「版本没对上」的悬案。

## 4.46 W5 第四轮：openh264 探针 0/3，以及它暴露的**两道结构性天花板**

**探针设计**（按 N31 确立的纪律：先 3 条再决定整池）：从 64 条池里取 **address / undefined / memory 各 1 条**（`OSV-2020-1042` / `OSV-2020-1186` / `OSV-2020-1041`），一次同时试探三个未销账（UBSAN 零正样本、MSAN flaky、N22 跨项目架构）。

**结果**：**0/3 构建成功**（中位 64s），早停在连续 2 次确定性失败后封掉项目 → 全轮 ~10min 结束，只有 1 条 observation（`none`）。镜像 2.9GB 已删。

选它之前我手工读过 `build.sh`/`Dockerfile`，判断是**结构性有利**的（这个判断本身没错，错在没预料到下面两件事）：只编 `libopenh264.a` + 链接一个 fuzzer、fuzzer 源码由 Dockerfile `COPY` 进 `$SRC`（→ 仓库内**没有**可错配的 shell 路径，所以预检的 `no_candidate_paths` 是**良性**的，与 ndpi 那种"盲点藏了真灾难"不同）、**不编测试套件**（无 libredwg 式磁盘爆）、**无第三方 tarball**（无 libspng/N28 式死链）、`ARCH=$ARCHITECTURE` 尊重 i386、且有 MSAN 专用分支（`USE_ASM=No`）。

**(a) 两段式失败 —— 每一段各暴露一道天花板**

| 阶段 | 用的 Dockerfile | 失败点 | 含义 |
|---|---|---|---|
| 首试 | HEAD（`libstdc++-9-dev`） | `/src/decoder_fuzzer.cpp:28:10: fatal error: 'codec_def.h' file not found` | fuzzer 源码 include 的头文件**在该老 commit 不存在** → N19 同族，但形态是 **C++ `#include`** |
| era-retry | 当期（`libstdc++-5-dev`） | `E: Package 'libstdc++-5-dev' has no installation candidate` | 老 Dockerfile 钉的包**已从 focal 下架** → 官方兜底**结构性失效** |

**(b) N33：era-retry 有一道结构性天花板**

`build_specified_commit.py` 的 era-retry 是整套流水线对付"当前 build.sh/Dockerfile 与老 commit 不匹配"的**唯一官方兜底**（W2 起就依赖它，§1.5 的 era 学习也是围绕它）。但 openh264 证明：**当当期 Dockerfile 钉死了后来被发行版移除的包名时，era-retry 必然失败**，与项目本身无关、也无法通过重试/换 era 解决（除非改上游 Dockerfile —— 任务约束禁止）。

* 影响面：这不是 openh264 独有的。未试池里 **2,984 条**大多来自 2020–2021 年，那个年代的 Dockerfile 普遍钉 `libstdc++-5/6/7-dev`、老 `python3.x`、已下架的镜像源 → **同一道天花板会反复出现**。
* 这也解释了 W5 的命中率：harfbuzz 0/7（era 侧 build.sh 也要那个 target）、pcapplusplus 0/3、opensc 0/3、openh264 0/3 —— **失败集中在"era 兜底救不了"这一类**，而不是随机分布。
* 可做的（未做，记为待办）：把「era Dockerfile 是否引用已下架包」做成**离线可判**的筛选维度（读当期 Dockerfile 的 `apt-get install` 列表，与当前 `apt-cache policy` 对照）→ 能在建镜像**之前**就否掉这类项目，省下 2.9GB + 探针时间。

**(c) N34：预检的第三个盲点 —— C++ `#include`**

预检（W4 Phase3a）只检查 **build.sh 里的 shell 路径/target**是否存在于该 commit。openh264 的错配发生在 **fuzzer 源码的 `#include`** 上（`decoder_fuzzer.cpp` 由 Dockerfile `COPY` 进来、内容取自 HEAD，却要编译老 commit 的树）→ 路径存在性检查**在构造上看不到**。

三个盲点现已集齐（都在 W5 发现）：① `bash -x ./a/b.sh` 的 flag 间隔（N27③，已修）；② libxml2 那种**全文只有一行裸脚本**的 build.sh（未修）；③ **C++ `#include`**（本条，未修）。
→ 结论：**预检通过是必要不充分条件**，探针不可省。若要修 ③，可在预检里额外抓取 `$SRC/*.cpp` 的 `#include "..."`（相对 include）并在该 commit 树上查存在性 —— 成本与现在同量级（raw 端点、0 API 0 clone）。

**(d) 顺带修掉的分类器缺陷（N28③ 现在有实证了，已修）**

两次被同一个缺陷误导后修了它：
* **首试段优先**：以 `Retrying on earlier OSS-Fuzz commit` 切分，**先用首试段分类**，该段无命中才退回整份日志。此前 era 段的 `dockerfile_drift` 会**压过**首试真因。
* **新增形态③模式**：`fatal error: '<X>' file not found` → 归 `buildscript_mismatch`（GCC 的 `fatal error: X: No such file or directory` 早已被既有模式覆盖）。
* 效果：openh264 那条从 `dockerfile_drift` + detail=`OpenPACE…`（错）变成 **`buildscript_mismatch`** + detail=`/src/decoder_fuzzer.cpp:28:10: fatal error: 'codec_def.h' file not found`（对）。自测 18 → **23 项**（含"首试段无错、只有 era 段有错"的对照，确保新逻辑不会把可分类的变成 `unclassified`）。
* ⚠ 影响面已核查：`buildscript_mismatch` 与 `dockerfile_drift` **同属** `DETERMINISTIC_FAIL` → **早停的连续计数行为不变**；分类器自测与预检已知答案回归（11 真报 / 0 误报）全部重跑通过。

**(e) 我自己在测试里犯的第 5 个错（同类，记下来）**

新加的 `[A2]` 节断言 `detail` 含 `codec_def.h`，但我把用例下标**硬编码成 13** → 实际指到「空日志」那条 → `detail` 恒为 `None`，断言以**错误的理由**失败（看起来像生产 bug，其实是我的索引）。改为**按名字定位**（`next(i for i,(nm,…) if nm.startswith("W5 openh264"))`）。
→ 与本节 (d) 的教训同型：**断言必须先确认自己指向的是预期的那个样本**，否则红/绿都不说明问题。这是 W5 我自己测试里的第 5 个缺陷（前 4 个见 §4.42c）。

**(f) W5 新项目总账与规模化判断**

| 项目 | 结果 | 死因 | 属于哪道天花板 |
|---|---|---|---|
| libspng | **1/19 = 5%** | 第三方依赖 URL 已死 11 + `tests/ossfuzz.sh` 缺失 6 | N28 / N23② |
| libtiff | 无钉版构建记录 | 2 条都是 MSAN，未走到钉版 | — |
| libredwg | **不可行** | `make check-prep` 编 ~100 个 ASAN 单测 → 磁盘爆；30min+/次 → 68 条≈40h | N31（构建成本） |
| opensc | **0/3** | `-Werror,-Wuninitialized` 工具链漂移 | 离线判不了 |
| openh264 | **0/3** | 首试 `#include` 缺头文件 + era Dockerfile 包已下架 | **N34 + N33** |

**5 试 0 中**；对照五个老项目 **92–100%**，且它们的未采样池**已全为 0**。

→ **规模化现在撞的是基础设施墙，不是采样墙**：真·积压已穷尽（102 条处理完、75 条新复现），剩余 2,984 条全需新镜像，而 v2 筛选**给不出任何 ✅ 级候选**，且新发现的 N33 说明"老 crash + 老 Dockerfile"这一大类**官方兜底救不了**。继续扩的期望产出是「每个项目 2.3–2.9GB 镜像 + 一次探针，命中率按现有证据 ≤1/5」。

## 4.47 W5 收尾：积压确实归零，以及一个会误报的度量

我在终检里写了「积压彻底穷尽」，但同一份报告的另一行却显示 **真·积压 4 条** —— 自相矛盾，所以去查了这 4 条。**结论：积压确实归零，错的是度量口径**（而这个口径正是我前几轮用来算「92 条积压」的，必须核清它当时有没有也算错）。

**(a) 那 4 条各是什么**

| crash | 项目 | 真相 |
|---|---|---|
| OSV-2021-520 / -541 / -581 | flatbuffers | **钉版已试过**：final 轮里 18 次格构建**全部** `dockerfile_drift`、早停（阈值抬到 10 后）触发 → 每格都没二进制 → **不产生 observation** → ⑤ 不写新行 → 它的「最新行」仍是 W2 那条 HEAD 行 | 
| OSV-2017-126 | libtsm（**UBSAN**） | **N6 退化 range**：`introducing_commit == fixed_commit == b73acb4c7169`、`static_check_verdict=degenerate`、`degenerate_resolved=False` → **按设计禁止钉版**（钉了只会得到假 `none`）。HEAD 构建成功但没崩 → **终止性 HEAD-only**，不是待办 |

**(b) 度量缺陷（已修）**

原口径「最新行 `commit_source=='head'` 且有 `fixed_commit` 且未复现 ⇒ 积压」漏了两种情况：**① 钉版试过但每格构建都失败**（无 observation → 无新行 → 旧 HEAD 行仍是最新）；**② N6 退化 range**（设计上就不许钉版）。两者都会被当成「从没在对的版本上试过」。

修法（`preflight/selftest/w5_backlog_report.py`）：查 `build_records.jsonl` 里有没有 **`build_stage==2`** 的尝试记录，并把 `static_check_verdict=='degenerate'`（或 `osv_degenerate_range ∧ ¬degenerate_resolved`）单列为**终止性 HEAD-only**。修后输出三类：

```
旧口径会报 4 条「积压」，正确拆分：
  ▸ 终止性 HEAD-only（N6 退化，禁钉版）: 1  ['OSV-2017-126']
  ▸ 钉版已试过、每格构建都失败        : 3  ['OSV-2021-520','-541','-581']
  ▸ 真·积压（从没在钉版上试过）        : 0  []
```

**回头核验旧结论有没有被这个缺陷污染**：W5 那「92 条积压」是用**同一口径**算的，但它们当时**确实**从没走过钉版（`build_records` 里没有 stage=2 记录）—— 证据是这 92 条重跑后 **75 条立刻复现**（若早就试过钉版，不会有这个跃升）。所以**当时的 92 条是对的**，缺陷只在「跑完之后仍被算作积压」这一侧。

**(c) 顺带把两条账的状态定死**

* **UBSAN 正样本仍为 0，且现在有了确切原因**（不再是"没找到"）：已采样集合里**唯一的 UBSAN 候选**就是 OSV-2017-126，而它是 **N6 退化 range → 禁止钉版**；openh264 池里那 2 条 UBSAN 属于 **0/3 不可构建**的项目。→ 要销这条账，必须找到「**有 UBSAN crash + 非退化 range + 项目可构建**」三者同时成立的对象，而这需要先建新镜像。
* **flatbuffers 的 3 条也归入 N33**：它们的失败类是 `dockerfile_drift`（当期 Dockerfile 的包已下架），与 openh264 的 era 段死因同型 → N33 现在有**两个项目**的实证（openh264、flatbuffers），不再是一例。
* `not_located` 累积 **21 条**（final 轮的静态 check 又认出 2 条），距 ≥30 还差 **9**。

**(d) 状态定稿**

真·积压 **0**；已知可用的五个项目未采样池 **0**；未试池 **2,984 条**全需新镜像，而 v2 筛选**无 ✅ 级候选**、W5 新项目 **5 试 0 中**、N33 说明「老 crash + 老 Dockerfile」这一大类官方兜底救不了。**W5 的扩样本到此为止是收敛的，不是半途停下。**

## 4.48 W5 收尾：交付面审计（复现记录表自洽性护栏）+ 它抓到的一个真缺陷

**为什么补这一类护栏**：W5 下半程查出的缺陷 —— ⑤ 白名单漏 `walkback_stop_reason`、悬空 `binary_dir`、N30 删掉已交付证据、积压度量误报 —— **没有一个能被现有 13 套自测发现**。那些自测测的是「**模块行为**对不对」，而这些全是「**交付出去的复现记录表自不自洽**」。所以补一个直接审复现记录表的护栏：`preflight/selftest/w5_audit_delivery.py`。

**审计的不变量**（判据取自 ④ `verify_one()` 的**实际代码**，不是我的转述）：

| 组 | 检查 | 真复现记录表结果 |
|---|---|---|
| [1] append-only 基本性质 | 最新行唯一；`run_status` 全为 `run`；无 `tier_downgraded`（⑤ 单调性护栏未被 `--force` 绕过） | ✅ 153 条唯一 / 107 条有多行历史（正常） |
| [2] 交付子集规模 | `verified` 行数 **必须等于** `reproduced_any` 行数 | ✅ 103 = 103 |
| [3] tier ↔ 评分自洽 | `none ⇔ ¬reproduced`；`strict ⇒ crash_type 一致 ∧ score_subseq≥1.0`；`medium ⇒ crash_type 一致`；`loose ⇒ 不一致` | ✅ 153 条全自洽 |
| [4] 证据完整性 | verified 行必须有 `binary_sha256` + 重建配方；**verified 悬空指针 = 0（红线）**；已回收行必须留住 sha256 | ✅ 103/103 有指纹与配方；悬空 **0**；81 条已回收行全部留住 sha256 |
| [5] 溯源字段 | 8 个字段（osv_id/project/sanitizer/crash_type_expected/fuzz_target/testcase_path/run_id/tier）非空；且 `testcase_path` **实际存在** | ✅ 全非空、全存在 |
| [6] 外推警示（不算失败，但必须显式打印） | 项目集中度、sanitizer 覆盖 | ⚠ **c-blosc2 占 60/103 = 58%** → 复现率不能当全局估计；⚠ **UBSAN 覆盖 = 0** |

**结论：真复现记录表 0 条红线违反**；1 条软性提示（18 条 `none` 档悬空 `binary_dir`，属设计内：轮末 prune 在 ⑤ 之后跑，而 §1.6 本就只交付 verified 子集 → 已记 §5 item 27）。

**牙齿测试**（`preflight/selftest/w5_selftest_audit_teeth.py`）：一个**恒真**的审计也会报绿，所以往复现记录表**副本**（`--dataset` 指过去，绝不碰真数据）里注入 4 类违规，要求审计**必须变红**，同时真复现记录表**必须仍绿**（证明不是恒红）：

| 注入 | 目标行 | 审计是否抓到 |
|---|---|---|
| `strict` 却 `crash_type_match=False` | OSV-2020-2087 | ✅ |
| verified 却 `binary_sha256=None` | OSV-2016-5 | ✅ |
| verified 却 `binary_dir` 指向不存在路径且未标记 | OSV-2020-2184 | ✅ |
| `none` 却 `reproduced_any=True` | OSV-2021-1070 | ✅ |

→ **4/4 全抓、退出码 1；真复现记录表对照退出码 0。**

**牙齿测试抓到了审计自身的一个真缺陷**（这是它最大的价值）：

* 症状：注入 `medium + crash_type_match=False` 时审计**不报**。
* 根因：我把 [3] 的 medium/loose 判据写成了 `… and nrec`（`n_recovered_frames`），而**复现记录表里这个字段常为 `None`**（⑤ 没有透传 ④ 的该字段）→ 条件恒假 → **`recovered` 为空的那批行根本没被检查**。
* 修法：重读 ④ 的分支后确认 —— 无论 `R` 是否为空，`medium ⇒ crash_type_match`、`loose ⇒ ¬crash_type_match` **都成立**（R 为空时是 `medium if ct_match else loose`；R 非空时是 `strict / medium(ctm) / loose`）→ **那个 `nrec` 前置条件是多余且有害的**，删掉。
* 教训：**写不变量时要回去读判据的源码分支，不能凭"大概是这样"**；而"凭大概"写出来的多余条件，只有注入测试才能暴露 —— 对真复现记录表它永远是绿的。

**我自己的牙齿测试也犯了一个选样错**（同类，记下来）：第一版随便取前三条 verified 行注入，结果第一条是 `loose`，而「`loose` + `crash_type_match=False`」**本来就自洽**（④：loose ⇔ crash_type 不一致）→ 审计不报是**对的**，测试却据此判"审计无牙"。修法：**按 tier 选样**，确保每次注入都确实违反不变量。→ 这与 §4.46e 的教训同型：**断言必须先确认自己指向的是预期的那个样本**。

## 4.49 W5 第五轮：硬骨头重试 —— 一个设计参数被证伪，一个假设被否证

**动机**：积压归零、新项目 5 试 0 中之后，唯一不需新镜像的杠杆是那 40 条「钉版路线试过、仍没崩」的硬骨头。其中**镜像还在、项目可构建**的 13 条里，挑出信息量最高的 **7 条**做一轮重试，同时检验**两个设计假设**：

* **假设 A（架构）**：`OSV-2022-886`(hunspell) 与 `OSV-2021-766`(c-blosc2) 都是 **i386** job，而它们最后一次尝试在 **W4 的 `--match-job-arch` 之前** → 当时是按 x86_64 建的。W2 甚至据此写下「x86_64 下结构性不可复现」（= **N8**，后被 W3 配对实验推翻）。
* **假设 B（深度）**：9 条硬骨头当年走完 3 格、**构建全成功**（`build_fail=0`）却没崩 → `--max-depth 3` 这个上限（与 §5② 的「walk-back ≤3」对齐）是否太浅？

**做法**：`--max-depth 6` + `--match-job-arch`（默认开）+ `--stop-frac 0`（不提前停，让每格都被观测），7 条 / **33 次构建**。

**结果：7 条里 3 条翻成 strict** → 累积复现 **103 → 106 条（153 条里的 69.3%）**，**strict 44 → 47**。

| crash | 项目 | arch | 逐格结果 | 命中深度 | 靠哪个杠杆 |
|---|---|---|---|---|---|
| **OSV-2022-776** | c-blosc2 | x86_64 | d1–d5 全 `none`(frac 0.0) → **d6 `strict`(frac 1.0)** | **6** | **深度**：原 `--max-depth 3` **必然漏掉** |
| **OSV-2024-1261** | pcre2 | x86_64 | d1 `none` → **d2 `strict`** | 2 | 首次真正走完钉版 walk-back（W2 只浅试过） |
| **OSV-2022-126** | md4c | x86_64 | 单格 **`strict`** | — | 同上（W1 的已知答案 crash，此前复现记录表里是 none） |
| OSV-2021-766 | c-blosc2 | **i386** | 6 格全 `none` | — | **架构匹配也没救回来** |
| OSV-2022-886 | hunspell | **i386** | 6 格全 `none` | — | **架构匹配也没救回来** |
| OSV-2022-486 / OSV-2025-312 | c-blosc2 | x86_64 | 6 格全 `none` | — | — |

**(a) 假设 B 成立，但只对「残差」成立 → 不改全局默认**

全复现记录表 **106 条复现行**的命中深度分布：**depth1 = 87、depth2 = 9、depth6 = 1、无深度 = 9**。
→ **只有 1/106 ≈ 0.9% 需要 depth>3**。把 `--max-depth` 全局抬到 6 会让每条 crash 的构建量最多翻倍，换来 ~1% 的增益 → **不划算，默认保持 3**。

**正确的做法是本轮用的这个**：默认 3 跑规模，**只对残差**（3 格全 `none` 且构建都成功的那些）再做一轮 depth 6 的深重试。本轮就是这个策略，**命中率 1/7 ≈ 14%**（比全局抬深度的 ~1% 高一个量级，因为残差本身就是被筛过的可疑集合）。→ 已写进 §5 作为标准流程。

**(b) 假设 A 被否证（如实记）**

两条 i386 硬骨头在**正确架构**下走完 6 格仍全 `none` → **架构不匹配不是它们不复现的原因**。这与 N22 并不矛盾：N22 说的是「架构错配会让**已经能复现**的 crash 掉档或撞上别的 bug」（配对 n=3、3/3 升档），而**它从来不保证「按对架构建就能复现」**。我当时的推断（「W4 之前跑的 i386 crash 可能只是架构没对上」）**超出了 N22 的证据范围**，本轮把它证伪了。
→ 附带意义：W2 对 OSV-2022-886 写的那句「x86_64 下结构性不可复现」现在有了更完整的版本 —— **它在 x86_64 和 i386 下、6 个深度上都没复现**，所以「结构性不可复现」这个说法反而**更接近事实**，只是理由不是架构。

**(c) 顺手补掉 N34 的盲点② —— 而且它立刻产生了实效**

盲点②是「build.sh 整行就是一个裸脚本路径」的形态（无解释器、无 `$SRC/`、无 `./`）：✅ 实证 **libxml2/build.sh 去掉注释后只有一行** `fuzz/oss-fuzz-build.sh` → 原 `SCRIPT_RE` 三个 alternative 全不匹配 → 预检报 `no_candidate_paths`（**无证据**），于是 **52 条池**只能被判「ⓘ 只能探针」。而它在 **gitlab.gnome.org** 上、`path_exists_at` 本来就支持 gitlab → 属于「**查得了却没去查**」。

修法（TDD）：给 `SCRIPT_RE` 加 `^\s*` 这个 alternative。**为什么不会放宽成误报**：capture 要求 `[\w.+~-]+(?:/[\w.+~-]+)+\.(sh|py|pl)`，而 `cp tools/helper.sh $OUT/` 这类行**行首是 `cp`**、其后是空格 → 既进不了字符类也接不上 `/`，回溯也匹配不成（shell 里「整行以路径开头」本身就等于执行它）。自测新增 [E] 正例 + **[F] 负对照**（`cp`/`echo` 语境里的 `.sh`/`.py` **不得**被抽成候选）。

**回归**：预检已知答案 **11 条真报全中**（harfbuzz 4/4、pcapplusplus 3/3、libspng 4/4）、**6 个项目 24 个已成功 commit 误报 0** → 新 alternative 没有放宽成误报。

**立刻产生的实效**：重跑 v2 筛选后，**libxml2 从「ⓘ 证据不足」翻成「⛔ 路径错配全中 2/2」** —— `fuzz/oss-fuzz-build.sh` 在抽样的钉版 commit 上**不存在**。也就是说：**这一个正则修复，直接把一个 52 条池的项目按证据淘汰掉，省下了 2.3GB 镜像 + 一次探针**（否则会重演 openh264 的 0/3）。⛔ 名单因此从 4 个增至 **5 个**（ndpi / fluent-bit / mruby / openexr / **libxml2**），v2 仍**无 ✅ 级候选**。

**(d) 状态**

硬骨头 40 → **37 条**；其中镜像还在、项目可构建的 **10 条**（已含本轮试过 depth6 的 4 条）。审计重跑：新增 7 行后仍 **0 条红线违反**（verified 悬空 0、指纹/配方齐全、tier↔评分自洽）。
另把 openh264 补进筛选脚本的 `TRIED`/`TRIED_WHY`（**已证不可行的项目必须记进排除名单**，否则下一次筛选还会把它当候选推荐出来 —— 每个都是 2.3–2.9GB 镜像 + 一次探针的成本）。

## 4.50 W5 第六轮：N33 的离线预测器（把「赌一个镜像」变成「先量一次」）

**动机**：W5 新项目 **5 试 0 中**，其中 **2 个**（openh264、flatbuffers 的残余）死于 `dockerfile_drift`。这类失败**在建镜像之前就可判**，而每个镜像要 2.3–2.9GB + 一次 10–30min 探针 → 值得先把这一维变成离线可测。

**做法**（`preflight/screen/w5_predict_dockerfile_drift.py`，三步）：

1. 取该项目**当年**的 era Dockerfile：GitHub API `commits?path=projects/<p>/Dockerfile&until=<池里最老 crash 的年份>-12-31`（1 次调用）→ 再走 raw 取内容（1 次）。用"最老那条"是因为**越老越容易踩下架包**。
2. 抽出 `apt-get install` 的包名（**纯函数**，自测 7 项：同行多包、续行 `\`、`--no-install-recommends` 等 flag、`=版本` 钉定、`:i386` 架构后缀、空输入、以及"不把 `make install` 当 apt"）。
3. 在**本地已有的 base-builder 镜像**里跑**一次** `apt-cache policy` 批量查全部包的可安装性（只读缓存、不装东西、秒级）。

**成本对比**：每项目 1–2 次 HTTP + **全部项目共用 1 次 docker run** ⟷ 建镜像 2.3–2.9GB + 探针 10–30min。便宜两三个数量级。

**已知答案校验**（这是它有没有用的唯一标准 —— 6 个项目全部有实测结果）：

| 项目 | 实测钉版可构建率 | 预测（本维度） | 判对? |
|---|---|---|---|
| **openh264** | **0/3**（死于 `libstdc++-5-dev` 已下架） | **⛔ 预测 dockerfile_drift**（唯一不可安装的包正是它） | ✅ **真阳** |
| c-blosc2 | 142/145 = 98% | ✅ 5 个包全可安装 | ✅ 真阴 |
| hunspell | 48/48 = 100% | ✅ 4 个包全可安装 | ✅ 真阴 |
| pcre2 | 24/26 = 92% | ✅ 5 个包全可安装 | ✅ 真阴 |
| flatbuffers | 5/28（死于 `compile_error`） | ✅ 本维度无风险 | ✅ **正确**（死因不在此维） |
| libspng | 1/19（死于死外链 + 路径错配） | ✅ 本维度无风险 | ✅ **正确**（死因不在此维） |

→ **1 真阳 / 5 真阴 / 0 假阳 / 0 假阴**。注意 flatbuffers 与 libspng 判 ✅ 是**对的**：它们的死因本来就不是 `dockerfile_drift`，预测器只对自己那一维负责 —— **这正是"每个维度都要单独校验"的意义**。

**自测抓到我自己新代码里的一个真 bug**：`APT_RE` 原写成 `re.S` + `(.*?)(?:&&|\|\||;|$|\\)` → `.` 跨行、而 `$` 在非 MULTILINE 下只匹配串尾，于是一路吃到下一条 `RUN git clone …`，把 **`git`/`clone`/`1`/`https`/`openh264` 全当成了包名**。改为**按行捕获**再在行内切 `&&`/`||`/`;`。（若没这条自测，后面查可安装性时会去查一堆不存在的"包"，得出满屏假 ⛔。）

**跑完 12 个候选的结论**：**只有 openh264 被判 ⛔**（而它已经实测死了）。也就是说 —— **N33 不是剩余候选的主要屏障**；它们的风险都在别的维度上：路径错配 ⛔（ndpi / fluent-bit / mruby / openexr / **libxml2**）、第三方外链 ⚠（ghostscript 2 / arrow 2 / matio 2）、repo 体量 ⚠（radare2 204MB / php 640MB / serenity 237MB）。**v2 筛选仍然给不出 ✅ 级候选。**

**一个我怀疑过、但查证后推翻的判断**（记下来，因为它看起来太像 bug 了）：`libspng`/`c-blosc2`/`matio`/`opensc`/`arrow`/`pcapplusplus` 六个项目的 era sha **都是 `d561c49ae50b`** → 我怀疑 API 的 `path` 过滤没生效、取到了同一个文件。**查证结果：不是 bug** —— 该 commit 是 oss-fuzz 的一次**全仓批量改动**（message: `Update Dockerfiles (#4070)`，files 列表里同时有 `projects/arrow/Dockerfile`、`projects/aspell/Dockerfile`… 数百个），所以它**确实**是这些项目各自 Dockerfile 在该日期前的最后一次修改；而且 raw URL 含项目路径 → 六个项目抽出的**包列表各不相同**（openh264 是 `libstdc++-5-dev/nasm/subversion`、arrow 是 `bison/build-essential/cmake/…`、matio 是 `libhdf5-dev/…`），若真取错文件包列表必然相同。→ **判据：不同对象得到相同标识时，先查那个标识是不是本来就共享，再怀疑代码。**

## 4.51 W5 第七轮：N34 盲点③ 的检测器 —— 已知答案对上了，但适用边界比预想窄

**实现**（TDD，三层，前两层纯函数可离线测）：

| 函数 | 职责 |
|---|---|
| `parse_fuzzer_includes(project)` | 从 `projects/<p>/Dockerfile` 的 `COPY … $SRC/` 认出**被拷进容器的 fuzzer 源码** → 抽它们的 quoted `#include`（只取 `"…"`，尖括号是系统头、查不了也不该查）→ 从 `build.sh` 抽 `-I` 目录（归一化掉 `./`，含 `$` 的跳过）。**零网络**，自测直接读 worktree 里真实的 openh264 文件 |
| `include_candidates(inc, inc_dirs)` | 一个 include 要依次试的仓库相对路径：每个 `-I` 目录，**仓库根放最后**；`../` 逃逸 → 空（宁漏勿误） |
| `precheck_includes(...)` | 走 `path_exists_at` 实查；**无法判定一律放行**（与 N27① 同一契约）；`max_checks=24` 成本护栏 |

**已知答案校验（走网络，用 openh264 实测失败的那个 commit `58576925544e`）**：

```
[include 预检] openh264@58576925544e：6 个 include、3 个 -I 目录
  → 查 20 次、找到 3、**缺 3**、无法判定 0 → ['codec_def.h', 'codec_app_def.h', 'codec_api.h']
```

而当时真实的构建日志是 `fatal error: 'codec_def.h' file not found` → **预测器在没建镜像、没跑构建的情况下，离线复现了那次失败的真凶**（且多找出另外两个同样缺失的头文件；编译在第一个就停了，所以日志只报了一个）。

**为什么只做筛选维度、不接进 ② 的每次构建前预检**：6 个 include ×（3 个 `-I` + 根）= **20–24 次 HTTP**、约 10–25s/项目。作**一次性筛选**划算（对比建镜像 2.3–2.9GB + 探针 10–30min），但放进每次构建前就逼近 **N24** 的教训（预检自身比它省下的构建更贵）。→ **未接进生产路径**，这是有意的取舍。

**跑完候选集后发现的适用边界（比预想窄得多）**：把这一维加进 v2 筛选、对 8 个池≥30 的候选跑一遍，结果是 **8 个全部 `no_sources`/`no_includes`** —— 它们的 Dockerfile **不像 openh264 那样把 fuzzer 源码 `COPY` 进 `$SRC`**，而是直接编仓库里的 fuzzer，所以「HEAD 的 fuzzer 源码 vs 老 commit 的树」这个错配形态**对它们不成立**。

* 这不是缺陷，是**适用边界**；但如果筛选表把它显示成 `0/1`，就会被读成「查了、干净」——**正是 N29 那个陷阱**。所以：
  * 记录 `effective = n − len(why)`（真正有效的检查数），显示成 **`不适用`** 而不是 `0/1`；
  * 自测新增 **[F] 适用边界**节：对 libxml2/radare2/matio 断言 `reason ∈ {no_sources, no_includes, no_project_dir}` **且必须放行**（把边界本身钉进测试，免得日后有人以为它"漏检"）。
* **对候选名单的净影响：0 个新增淘汰** → v2 的结论不变：**无 ✅ 级候选**；⛔ 5 个（ndpi / fluent-bit / mruby / openexr / libxml2）、⚠ 6 个（外链多 3 + repo 偏大 3）、ⓘ 2 个（libavc / mupdf，仓库非 github/gitlab → `path_exists_at` 判不了）。

**一句话总结这一轮**：检测器本身是有效的（已知答案对上真凶），但**它只对一类项目有效**，而那类项目在当前候选里一个都没有 —— 所以它的价值是**封住一个已知失败模式**（下次再遇到 openh264 那种 `COPY fuzzer.cpp $SRC/` 的项目，建镜像之前就能否掉），而不是改变本轮的选择。

## 4.52 W5 第八轮：mupdf 探针 —— 挖出两个真缺陷（N35/N36），但最终撞上第三道结构性天花板（N38）

**这一轮的净结果**：复现 **+0**，但**修掉两个会静默少跑/多拦的真缺陷**，并把「新项目为什么建不起来」的归因从 2 类推进到 **4 类**。总花费 ≈ **6.5 小时墙钟 + 3.11GB 镜像**（已回收 2.3GB 临时垃圾）。

### 4.52.1 四次尝试，每次卡在不同的一层

| 次序 | run_id | 结果 | 卡在哪一层 |
|---|---|---|---|
| ① | `w5-mupdf-probe` | 3 条 / **0 次构建** / 0.0min | **N35**：`fixed~1` 解析不出 → walk-back 在建之前就中止 |
| ② | `w5-mupdf-probe2` | 3 条 / **0 次构建** / 0.3min | **N36**：预检误报 `buildscript_mismatch`（submodule 路径） |
| ③ | `w5-mupdf-p1b` | 1 条 / **3 次构建 / 240.2min / 0 复现** | **N38**：每格 `# TIMEOUT after 3600s` |
| ④ | `w5-mupdf-p1c`（带 N37 镜像源） | 卡住 57min，人工终止 | **N38 依旧**：N37 对这个项目**无效**（见下） |

### 4.52.2 N35：非 github/gitlab 的 `repo_url` 会让 walk-back「零构建」静默失败

`resolve_commit_meta()` 走 `.patch` 端点，**只认 github / gitlab**，其余 `return None` → `plan_pinned()` 得到 `(d, None, "fixed~d 解析失败")` → **walk-back 中止，一次构建都不发生**。

**✅ 实测爆炸半径**（这一条是本轮最有价值的产出）：

```
可执行池 3,136 条，按 repo_url 主机分：
  github.com                 2,427      git.ghostscript.com   242
  gitlab.com / gitlab.gnome    135      android.googlesource   58
  git.code.sf.net              46      invent.kde.org         42
  …（共 26 个主机）
→ **非 github/gitlab = 542 条（17.3%）/ 32 个项目**
   含池最大的 ghostscript 197、matio 46、kimageformats 39、mupdf 37、libhevc 24、dnsmasq 19…
```

而**已跑的 153 条里 11 条非 github**，它们之所以能跑是因为 **8 条 libtsm 全是 `commit_source=head`**（走 HEAD、从不需要 `fixed~d`）+ 3 条就是本轮 mupdf。**换言之：此前所有「钉版 + 非 github」的组合，100% 死在这一行 `return None` 上，而且表现为「静默 0 构建」而非报错。**

**修法**：`REPO_MIRRORS` 映射 + `mirror_for()`（归一化：strip/小写/循环剥 `.git` 与尾斜杠），接进 `resolve_commit_meta()` 与 `_raw_url()`（后者顺带让 `path_exists_at` 对镜像仓库也可判 → mupdf 从筛选里的 ⓘ「判不了」升为可判）。

**为什么用镜像是安全的**（两条独立理由）：
1. **git SHA 是内容寻址的** → 镜像无法伪造 SHA。✅ 双方法互证：GitHub API 给 `7f82c015…~1 = 813144d395bb`，**本地全量克隆镜像后 `git rev-parse` 也给 `813144d395bb`** —— 逐字一致。
2. 构建仍按 SHA 检出 → 若镜像给了错 SHA，构建会**当场失败**，不会静默产出错结果。

**效果**：`plan_pinned` 对 3 条探针各排出 3 格真 SHA（此前是 `(1, None)`）。自测 24 项（含**前缀陷阱**、大小写、多尾缀、同主机不同仓库不许误命中）。

### 4.52.3 N36：预检第 4 个盲点 —— raw 端点**看不见 submodule 内部**

预检报 `build.sh 引用但 commit 树里没有: ['thirdparty/harfbuzz/src/hb-subset-cff1.cc']` → 判 `buildscript_mismatch` → **一次挡死 mupdf 全部 37 条**。

**✅ 实测证明是纯误报**（同一 commit `7f82c015`）：

| 路径 | HTTP | 说明 |
|---|---|---|
| `source/fitz/document.c` | **200** | 普通文件，端点正常 |
| `include/mupdf/fitz.h` | **200** | 普通文件，端点正常 |
| `thirdparty/harfbuzz/src/hb-subset-cff1.cc` | **404** | ← 在 **submodule** 里 |

`.gitmodules` 明确列了 10 个 submodule（`thirdparty/harfbuzz` → `../thirdparty-harfbuzz.git`），而 `build.sh:19` 正是 `sed -i … ./thirdparty/harfbuzz/src/hb-subset-cff1.cc` —— 构建时容器 `git clone --recursive`，**该文件必然存在**。

**修法**：`submodule_paths(repo_url, sha)` 拉 `.gitmodules` 解析 `path=`（带进程内缓存），候选路径落在任一 submodule 前缀下 → 记 `undecidable` + `submodule_skipped` 留痕并**放行**（与 N27①/N29 同一口径：**查不了 ≠ 查过没有**）。前缀判据用 `c == sm or c.startswith(sm + "/")`，避免 `thirdparty/harfbuzz` 吞掉 `thirdparty/harfbuzz2/`（自测专门钉了这条）。

**回归**：已知答案 **11 真报仍全中**（harfbuzz 4/4、pcapplusplus 3/3、libspng 4/4）、6 个可构建项目**误报 0** → 没有把真阳性放跑。

### 4.52.4 N37 + N38：镜像源改了也没用 —— 因为 `--repo_path` 指向镜像内**预烘焙的 shallow 克隆**

N37 把构建的 `--repo_url` 也换成镜像（并记 `repo_url_build` 留痕）。**实测对 mupdf 无效**，诊断到进程级：

```
build_specified_commit.py  PID 1270098   wchan=do_poll   （ sleeping，57min ）
  └─ 子进程  git remote update            wchan=do_wait
       cwd = /tmp/tmpmatjz5j0/src/mupdf
       origin = git://git.ghostscript.com/mupdf.git     ← **不是镜像**
       is-shallow-repository = true,  HEAD = 89c1d183a
```

那个目录来自 `docker run … cp -r -p /src /out`，即**镜像里 Dockerfile step 4 `git clone --recursive --depth 1 git://git.ghostscript.com/mupdf.git` 预烘焙的克隆**。`--repo_path /src/mupdf` 指向它 → `build_specified_commit.py` 直接在这个已有仓库上 `git remote update`，**我传的 `--repo_url` 根本不参与该仓库的 fetch**。而它是 **shallow**，要检出 2018 年的 commit 还得先 unshallow —— 全走那个慢速 `git://` 服务器。

**✅ 实测单价对比**：

| 操作 | 耗时 |
|---|---|
| `git://git.ghostscript.com/mupdf.git` 全量克隆 | **>15min 未完**（超时终止） |
| `https://github.com/ArtifexSoftware/mupdf` 全量克隆 | **51s / 211MB** |
| 单个钉版格（p1b 实测） | **3,600s TIMEOUT** |
| 3 格合计 | **240.2min，0 复现** |

镜像里 `/src` = **585MB / 13,351 文件**（对照 c-blosc2 **61MB / 1,975**），但这**不是**主因 —— 临时目录 19min 内只从 663M 长到 730M 后就**停住**，进程阻塞在 `git remote update` 而非拷贝。

**为什么修不了（两条硬约束正面挡住）**：
* 改 `projects/mupdf/Dockerfile`（把 step 4 的 `git://` 换成 https 镜像、或去掉 `--depth 1`）→ **违反「不改 Dockerfile/build.sh」**；
* 改 `infra/build_specified_commit.py` / `repo_manager`（让它对已有仓库改写 origin、或做定向 fetch 而非 `remote update`）→ **违反 infra md5 固定 `f5092d0a3f2a6909`**。

**成本外推**：37 条 × 最多 3 格 × 3,600s = **最多 111 小时**，且每格都是超时（0 信息量）。→ **判定 mupdf 不可行**，比 libredwg（30min/次构建）更差。

### 4.52.5 一次操作事故 + 三个附带发现

* **⚠ 杀构建会污染 worktree**：我用 shell 超时杀掉了 p1b/p1c，而 era 预 checkout（`git checkout <era> -- projects/mupdf`）是**暂存**的（`git status` 第一列 `M`）→ `git checkout -- projects/` **修不回来**，必须 `git restore --source=HEAD --staged --worktree` + `git clean -fdq`。`restore_projects()` 本身是对的（**N18** 已修过这个坑），但它只在进程正常结束时跑。**护栏工作正常**：脏 worktree 被 §1.7 H 条件② 拦下、② ABORT。→ 规程：**杀构建后必须手工还原 worktree**。
* **`run_repro.py --help` 一直是坏的**：argparse 的 help 串里 `45.7%`/`6.7%`/`100%` 未转义 → `ValueError: unsupported format character`。已修为 `%%`（docstring 里那处**不能**改，它不参与 `%` 格式化）。附带发现：**我自己的检测器把已正确转义的 `0.8%%` 误报成非法** —— 扫描 `%` 时必须消费 `%%` 成对。
* **被杀的构建留下孤儿 `/tmp/tmp*`**：清出 **1.8GB**（单个 1.3GB）。→ 磁盘 6.1G 回到 8.5G。
* **`--min-free-gb` 默认 `0.0`** → 默认**没有**磁盘护栏；本轮全靠手工盯。

### 4.52.6 对复现记录表的影响（诚实记录，不改写历史）

复现记录表 284 → **292 行 / 153 → 156 唯一 / 25 run**；复现 **106/156 = 67.9%**（分母 +3、分子 +0）。

⚠ **其中 2 条 mupdf 行（OSV-2018-293 / OSV-2018-413）的 `buildscript_mismatch` 判定，现在已知是 N36 的误报** —— 它们是 N36 修复**之前**那一轮（`w5-mupdf-probe2`）留下的。按 append-only 原则**不改写历史行**，但必须标注：这 2 条的正确状态是「**预检误报，实际未尝试**」，不是「构建失败」。第 3 条（OSV-2018-255）是真跑过 3 格全 TIMEOUT。

→ 这也再次说明 **§4.52.2 那个积压度量缺陷**（`commit_source=="head"` 过滤）会漏算这类「路由到钉版但实际没跑成」的行。

### 4.52.7 新项目累计战绩与归因分类（更新）

**6 试 0 中**：libspng 5% · libtiff 无构建 · libredwg 不可行 · opensc 0/3 · openh264 0/3 · **mupdf 0/1（N38）**

| 归因类 | 项目 | 离线可判？ |
|---|---|---|
| N28 死外链 | libspng | ✅ `dead_external_url` |
| N33 era Dockerfile 包已下架 | openh264、flatbuffers(4) | ✅ `w5_predict_dockerfile_drift.py` |
| N34③ fuzzer 源码 `#include` 缺失 | openh264 | ✅ `precheck_includes()`（但适用面窄） |
| 工具链漂移 `-Werror` | opensc | ❌ 离线判不了 |
| 构建体量/磁盘 | libredwg | ⚠ 部分（N31 维度） |
| **N38 预烘焙 shallow 克隆 + 慢速上游协议** | **mupdf** | ❌ **离线判不了**（要建镜像 + 跑一格才知道） |

**N38 是新的第四类天花板**，而且**最贵**：它要求先建 3.11GB 镜像、再烧 3,600s 才能确认，**没有任何离线信号**。可提取的**廉价前置信号**（供下次筛选用，尚未实现）：`repo_url` 的 scheme 是 `git://`（而非 `https://`）+ Dockerfile 用 `--depth 1` 预克隆 → 高度可疑。

## 4.53 W5 第九轮：一个查看器暴露的两个缺陷 —— N39（C++ 签名让 17 条被错误降档）与 N40（reproduce 日志一直在被覆盖）

起因是「怎么看一条 crash 的复现」这个问题。为了回答它写了 `show_repro.py`（只读查看器，摊开复现记录表行 + 三件套 + ④ 的判分依据 + 可复制的重跑命令），**第一次拿它看 hunspell 的 medium 就发现判分不对**。

### 4.53.1 N39：`normalize_one_frame` 不剥 C++ 参数签名 → **17 条 medium 其实该是 strict**（未修，待定）

`OSV-2022-1004`（hunspell，判 medium）的逐帧对照：

```
[0] R: AffixMgr::cpdcase_check        O: AffixMgr::cpdcase_check(char const*, int)     ⚠ 仅函数名同
[1] R: AffixMgr::compound_check       O: AffixMgr::compound_check(std::__1::basic_string<…)  ⚠ 仅函数名同
[2] R: HunspellImpl::checkword        O: HunspellImpl::checkword(std::__1::basic_string<…)   ⚠ 仅函数名同
→ score_subseq = 0.0 → tier_why: 「crash_type 一致但帧不齐」→ medium
```

**函数名与顺序其实全对得上**。根因是两侧形态天生不同：

| | 来源 | 形态 |
|---|---|---|
| **R** | `crash_state_recovered.jsonl`（符号化后的函数名字符串） | **裸函数名** `AffixMgr::cpdcase_check` |
| **O** | ASAN/MSAN 的 stderr | **完整 demangle 签名** `AffixMgr::cpdcase_check(char const*, int)` |

而权威实现 `normalize_one_frame` 剥了 `.part.NN`/`.constprop.NN`、前导 `auto`、`$_N` lambda、`::operator()` → **唯独没剥 `(...)` 签名**。C 项目（c-blosc2 / pcre2 / libtsm / md4c / libspng）没有签名 → 不受影响；**C++ 项目每帧必失配**。

**✅ 实测影响面**（106 条 verified 全部按「剥签名后重算」跑一遍）：

```
维持 strict 47 · 维持 loose 23 · 维持 medium 15 · R 空 4
**medium → 应为 strict：17 条，全部是 hunspell**
```

→ tier 分布应从 `47 strict / 36 medium` 变成 **`64 strict / 19 medium`**。

**⚠ 它还推翻了本文已写下的一个结论**：§4.44 记「chunk3 以 hunspell 为主、16 条 medium → **档位画像与 c-blosc2 明显不同**」—— 那个「不同」是**这个归一化缺口的假象**，不是 hunspell 的真实性质。

**建议的修法**（尚未实施）：改在 **`repro_common.normalize_observed()`**（observed 侧本来就负责「main/模块帧过滤」），**不动**权威实现 `r2_r5_r6_r7_recompute.py` —— 签名只出现在 O 侧，剥 O 即可对齐，也不会污染 W1 时期 R2 聚类的结论。
**代价必须写清**：剥签名会**丢掉重载区分能力**（同名不同参视为同一帧）；但 R 侧本来就没有签名，这个信息**从来不存在**，故不是损失而是不可避免。
**成本几乎为零**：observations 全在盘上 → **只需重跑 ④⑤，不需要任何构建**；且 medium→strict 是**升档**，⑤ 的单调性护栏本来就允许（降级才需 `--force`）。

### 4.53.2 N40：`logs/reproduce/` 一直在被静默覆盖（N25 只修了一半）—— **已修**

回答「没崩的日志为什么不清理」时顺手核对，发现真正的问题**与直觉相反**：不是该删，而是**一直在丢**。

```python
repro_runner.py:253        with open(log_path, "w", ...)      # ← 无条件截断
build_orchestrator.py:225  def rotate_existing_log(...)       # ← N25 的修复，只用在 build 侧
```

**✅ 实证**：

| | 数量 |
|---|---|
| 复现记录表里跑过多轮的 crash | **113 条**（最多 6 行） |
| 其中盘上只剩 **1 份** reproduce 日志 | **110 条** ← 早先各轮的报告已被覆盖 |
| `logs/build/` 带轮转后缀的文件 | **71 个**（N25 在 build 侧确实生效） |
| `logs/reproduce/` 带轮转后缀的文件 | **0 个** |

文件名里的 `_r{i}` 后缀只处理**同一轮内的重试**（N16 flaky），**跨轮次不管**。所以「同一条 crash 在 W2 跑过、W5 又跑」时 W2 那份就没了 —— 与 N25 记录的事故同一类（派生产物被后来的运行覆盖，而结论仍引用它）。

**修法**：把 `rotate_existing_log` 移进 **`repro_common`** 作**单一权威实现**（`build_orchestrator` 改为别名引用 → 不会有两份实现分叉），`run_once()` 写盘前先轮转。自测新增 **T1b（7 项）**：别名同一性、替身跑两次 `run_once`、当前文件=最新一次、**产生 1 个轮转文件且上一次内容被保留**、`log_path` 语义不变（旧复现记录表行的 `raw_log_path` 仍指原名）。

**⚠ 残留局限（如实记）**：轮转**保住了字节**，但旧复现记录表行的 `raw_log_path` 仍指原名 → 现在指向的是**最新**那次的内容，旧内容要靠时间戳后缀去找。彻底修法是**日志名带 run_id**（`<osv>.<run_id>.log`），使每个引用永久精确 —— 但 `run_id` 在 ③ 的作用域里根本不可用（只有 ⑥ 知道），要给 ③ 加参数并由 ⑥ 透传，故列为待办（§5）。

### 4.53.3 顺带把「怎么看一条复现」变成一条命令

`show_repro.py`（只读，不重算不改写）：

```bash
python3 show_repro.py OSV-2020-2087 --cmd --check   # 摊开一条：版本/期望vs实测/判分/三件套/重跑命令
python3 show_repro.py --tier strict                 # 列某一档
python3 show_repro.py --project hunspell            # 列某项目
python3 show_repro.py --list                        # 列全部（带「报告/输入/二进制」在不在盘）
```

六段对应「怎么判断它真的复现了」：**【1】钉在哪个版本**（必须是 `fixed~d`，跑 HEAD = 白跑，就是当初 92 条积压的病因）· **【2】期望 vs 实测**（`crash_type` + `dedup_token` + `scariness`）· **【3】判分依据**（按**有序子序列**逐帧展示 R 在 O 中的命中位置，并标出「仅函数名同」的帧）· **【4】三件套路径与在盘状态** · **【5】`--check` 四项只读核对** · **【6】可复制的重跑命令**。

写它的时候自己先犯了一个错：【3】最初按**位置**比 `R[i]` vs `O[i]`，于是一条 `score_subseq=1.0` 的 strict 显示成三帧全 ❌ —— 因为判分是**子序列**匹配、不要求位置相同。已改为按真实算法走一遍游标。**教训：查看器必须复刻判分算法，否则它会制造出比它要解释的问题更多的 confusion。**

### 4.53.4 「没崩的日志该不该删」的量化答案

```
没崩的 30 个日志 =  48 KB
崩了的 106 个    = 691 KB
binaries/        = 1,295.6 MB      → 删那 30 个能省 **0.0036%**
```

而且它们是**分母的唯一证据**：19 条「建成、跑了、就是不崩」+ 9 条构建失败 + 2 条从未真跑。没有它们，`106/156` 这个比率就只剩断言、无法复核。**结论：不删。**（真正该做的是 N40 —— 别再丢了。）

另核实一处：`exit≠0` 的 106 个文件与复现记录表 `reproduced_any=True` 的集合**完全相同**（双向差集为空）。但**不能只靠退出码**：UBSAN 不 abort、可能 `exit=0` 却算崩（M11）；本数据集唯一那条 UBSAN 日志 `OSV-2017-126` 已核 → `exit 0`、无 `runtime error`、`ubsan_stderr_detected=False`、且 `binary_source=head_state_cache`（跑在已修复的 HEAD 上）→ **判 none 正确，不是漏判**。

## 4.54 W5 第十轮：归档布局的两个问题 —— 非二进制文件为什么必须在，以及按 crash 类型的浏览视图

### 4.54.1 `binaries/` 里的 `.aff`/`.dic`/`.options`/`.dict` **不是垃圾，是二进制的运行时依赖**

质疑合理（目录名叫 binaries 却装着数据文件），但**不能移走**。实测占比：

| | |
|---|---|
| 非可执行 / 带扩展名文件 | **0.2 MB / 1048.5 MB = 0.02%** |
| 按扩展名 | `.options` 27 · `.dict` 10 · `.aff` 10 · `.dic` 10 · `.good` 9 · `.wrong` 7 · `.zip` 1 · `.test` 1 |

③ 重放时是 `cd /out` 后按**相对名**读它们的：`.options` → 追加 `CUSTOM_LIBFUZZER_OPTIONS`；`.dict` → 追加 `-dict=`；hunspell 的 `affdicfuzzer` 初始化就要读 `.aff`/`.dic`/`.wrong`/`.good`。

**✅ 这不是推测，是踩过的事**（W2 bug 修 A）：原实现只归档「本次请求的 target + 同名 `.options`/`.dict`」，结果 flatbuffers 的 `monster_fuzzer` 在 `LLVMFuzzerInitialize → LoadBinarySchema` 里找不到 `monster_test.bfbs`（14,520 B，就在 build/out 里）→ 测试断言 helper **故意 trap（SIGILL）** → 被**误记成「复现 10 条 loose」**。所以归档规则改成「**全部 target + 全部非可执行数据文件**（只排除 `seed_corpus.zip`）」。

→ 结论：**这些文件必须与二进制同目录**，否则重放会假失败或假成功。目录名确实不准确（它是**归档下来的 `/out`**，不是「一堆二进制」）；改名要连带处理复现记录表 156 行的历史绝对路径（append-only 不能改，只能靠兼容符号链接），故先不动，只在此说明并列进 §5 待办。

### 4.54.2 为什么不能把物理布局改成 `<crash_type>/<project>/<commit>/`

**一份归档服务多条不同类型的 crash**：

```
84 个归档目录 服务 106 条 verified（平均 1.3 条/目录）
共用分布：1 条→74 个目录，2 条→5，3 条→3，6 条→1，7 条→1
**跨多种 crash_type 的归档：6/84**
  c-blosc2/address/886d4c9b…  ← 6 条，类型 [heap-buffer-overflow, memcpy-param-overlap]
  c-blosc2/address/0e8bdfce…  ← 3 条，类型 [heap-buffer-overflow, heap-use-after-free, segv-on-unknown-address]
  c-blosc2/address/b4bf11ae…  ← 2 条，类型 [heap-buffer-overflow, unknown]
  c-blosc2/address/886d4c9b…__i386 ← 3 条，类型 [heap-buffer-overflow, heap-use-after-free]
  md4c/address/a470fbf8…      ← 2 条，类型 [heap-buffer-overflow, unknown]
  hunspell/address/6291cac8…  ← 2 条，类型 [heap-buffer-overflow, heap-double-free]
```

物理按类型分就必须**复制**同一份产物；而归档键本来就是 `(project, sanitizer, commit, arch)`，且**复现记录表 `binary_dir` 是 append-only 的历史路径、不能改写** → 物理搬动会让 156 行全部悬空（正是 N20/N30 那类事故）。

**改用符号链接视图**（零字节、幂等可重建；同一份产物在多个类型下出现，恰好**如实反映共享关系**）：

```
artifacts/by_crash_type/<crash_type>/<project>/<sanitizer>/<commit>[@arch]__<OSV-ID>  → 真归档目录
```

`sanitizer` 必须留在路径里：同一 commit 的 ASAN 与 MSAN 产物**字节不同**。已回收的归档不留断链，而是放一个 `<name>.PRUNED.txt`（原路径 + 「sha256 与配方仍在复现记录表、可 bit 级重建」+ 报告与输入的位置）。

**✅ 实测**：**11 种 crash 类型 / 106 条**（34 个符号链接 + 72 个回收说明）；并且**通过符号链接路径直接重放成功** —— `global-buffer-overflow/libtsm/address/b73acb4c…__OSV-2016-5` 挂进容器跑出 `AddressSanitizer: global-buffer-overflow READ of size 1 @ vte_write_debug (tsm-vte.c:514)`，与复现记录表 `tier=medium` 一致。共享关系也如实可见：`0e8bdfce…` 同时出现在 `heap-buffer-overflow` 与 `heap-use-after-free` 下。

```bash
python3 show_repro.py --build-index     # 重建视图（幂等：先 rmtree 再建）
python3 show_repro.py --tree --limit 3  # 打印索引树
```

### 4.54.3 N41：顺手挖出的**删库地雷** —— 保护集用字符串比对，路径一旦有别名就静默失配

要加符号链接视图，就必须先确认「按字符串比对的保护集」不会被路径别名骗过。查出来两处都用 `os.path.normpath`：

| 函数 | 原实现 | 后果 |
|---|---|---|
| `prune_archive()` | `protected.add(normpath(binary_dir))` + `normpath(p) in protected` | 归档区一旦改名或经符号链接访问 → 保护集**静默失配** → **所有 verified 归档被判「无人引用」而删掉** |
| `purge_archives()` | 同上 | **更要命**：它就是 **N30 事故**（删掉 W4 已交付 strict 证据）的当事人 |

这是 N20/N30 的**同一形态、不同触发方式**：不是「绕过保护集」，而是「保护集因路径别名**静默失配**」。

**修法**：两侧共 **6 处**改 `os.path.realpath`。**已有的安全网确实兜住了**：`prune_archive` 里 W4 Phase1a(ii) 那个**用 `pinned_commit` 独立重算**的交叉校验会在 `M>0` 时**拒绝执行**而非删了再说 —— 但那样会让 `purge-on-verify` 一直误拒，所以仍必须修。

**✅ 验证四件**：① 构造「复现记录表记符号链接路径、盘上是真实路径」→ **仍被保护**，且**无关目录照样能删**（不是恒拒）；② 加固后 dry-run `保留 24 / 将删 0 / M=0`；③ **建完符号链接视图后**再 dry-run，仍 `将删 0`；④ 18 套自测 **249 项全绿**、审计 **0 条红线违反**。

## 4.55 W5 第十一轮：`purge-on-verify` 的默认反转 —— 「可重建」不等于「在场」

**触发**：用户直接质疑「重放不是需要二进制吗？你不应该把他们删了」。

**这个质疑是对的**，而且指出了我此前论证里的一个偷换：我一直用「✅ 可 bit 级重建（20/20、5/5 逐字节一致）」来代偿删除，但**「可重建」把「现场」换成了「要重搭一次现场」**。对下游用法（错误触发变异算子归纳 = **反复重放**）来说，这个代价不是一次性的、而是**每次都要付**。我此前只论证了「删了不会丢信息」，没论证「删了不影响使用」—— 两者不是一回事。

### 4.55.1 当初的理由还成立吗？——**只在跑满整个队列时成立，而队列跑不满**

| 当初的依据 | 现在的实测 |
|---|---|
| 「92 条一轮的归档峰值 ≈4.6GB 而磁盘仅 7.7G」 | 磁盘现有 **11G** 可用 |
| 「3,093 条钉版 × 48MB ≈ **145GB** > 100G 磁盘」 | ✅ 复算：272 次构建的归档体积中位 **55MB**、均值 **48MB**、最大 143MB → 145GB 这个数**没错**，但**前提是跑满 3,093 条** |
| —— | 而 **新项目 6 试 0 中**、五个老项目池已 100% 榨干 → **根本跑不满**。真实规模是 106 条 verified、归档 1.3GB |

**结论：「非删不可」的前提只在满队列下成立，而满队列在当前基础设施下不可达。** 既然实际规模只有 1.3GB、磁盘有 11G，删除换来的空间**远小于**它牺牲的可用性。

### 4.55.2 重建成本实测（这是决定性的数字）

```
需重建 **64 个归档**（服务 72 条 verified crash；按 (project,san,commit,arch) 去重）
  c-blosc2  33 个 × 中位  80s ≈ 44min
  hunspell  22 个 × 中位  64s ≈ 23min
  pcre2      7 个 × 中位 280s ≈ 33min
  md4c       2 个 × 中位   9s ≈  0min
→ 合计 **≈1.7 小时**、新增磁盘 **≈2.8GB**、**缺镜像的项目 0 个**（四个镜像全在）
```

**1.7 小时 + 2.8GB 就能把「可重建」变回「在场」** —— 这个代价完全付得起，所以不该让用户付「每次重放前先重建」的持续代价。

### 4.55.3 已做的三件事

1. **默认反转**：`--purge-on-verify` 的 `default` 由 `True` 改 **`False`**。help 里写清三条理由（重放必须有二进制 / 实测重建成本付得起 / 这条路径已出过 **N30** 与 **N41** 两次事故 —— **默认关掉最危险的那条路径本身就是护栏**）。跑满大队列且磁盘吃紧时再显式开启。
2. **`rebuild_archives.py`**（新工具）：从复现记录表挑出 verified 且归档不在盘上的行 → 按 `(project,san,commit,arch)` 去重 → 用 **`--commit-override <osv>=<commit>:<depth>` 强制钉到复现记录表记录的那个 commit**（**不能让 walk-back 自己找** —— 它可能在更浅的格就建成，那 restored 的就不是原来那份）→ 重建后把每个 target 的 sha256 与复现记录表 `binary_sha256` **逐个比对**（bit 级验证）。`--dry` 只报计划、`--verify-only` 只校验、`--project` 限定范围；自带 `--min-free-gb 4`（② 的默认是 0=不检查，这里显式给一个）。
3. **`by_crash_type/` 视图改版**（按用户要求把 OSV 放到 commit **下面一层**）：

```
by_crash_type/<crash_type>/<project>/<sanitizer>/<commit>[@arch]/<OSV-ID>/
    ├── binary      → 真归档目录（已回收则换成 PRUNED.txt，含重建命令）
    ├── testcase    → 输入文件
    ├── report.log  → 崩溃报告原文（**这才是「复现出来的 bug」**）
    └── INFO.txt    → tier / 期望vs实测 / pinned_commit / R与O帧 / tier_why / 可复制的重跑命令
```

改版动机不只是层级好看：**OSV 那一层正好能把三件套聚在一起**，于是「一条 crash = 一个自包含文件夹」。commit 层做成真目录也让你能一眼看出「这个 commit 覆盖了哪几条」（`886d4c9b…` 一个 commit 服务 6 条）。

**✅ 实测**：106 个条目 / 11 种类型；并且**从 crash 自己的文件夹里用相对符号链接直接重放成功**：

```bash
cd by_crash_type/global-buffer-overflow/libtsm/address/b73acb4c…/OSV-2016-5
docker run --rm -i -v $PWD/binary:/out -v $PWD/testcase:/testcase …
→ AddressSanitizer: global-buffer-overflow READ of size 1
  #0 vte_write_debug  /src/libtsm/src/tsm/tsm-vte.c:514:8      （与 INFO.txt 记录一致）
```

顺带修掉 INFO.txt 的一个显示瑕疵：跑在 HEAD 上的 crash（`walkback_depth_actual=None`）原先印成 `pinned_commit = … (= fixed~None)`，现改为 `(commit_source=head，非 walk-back 格)`。

### 4.55.4 这一轮的自查

**我在论证「删除可接受」时犯的是同一类错误两次**：N29 是「把『查不了』当成『查过没问题』」，这里是**把「可重建」当成「不影响使用」**——都是用「信息没丢」偷换「能力没丢」。判据应该是：**下游要做的那件事，现在还做不做得了**。重放要做，二进制不在就做不了，句号。

## 4.56 W5 第十二轮：libavc 打通 —— 新项目 **7 试 1 中**，复现 106 → **139**

**这是 W5 第一次有新项目跑通**，而且一次贡献 **33 条**（跃居第二大项目）。全过程：先把「删掉的二进制」全量补回并逐字节验证，再用新写的 Gitiles 解析器（N42）把 googlesource 系从「判不了」变成「可离线筛」，筛出 libavc，探针 3/3 通过后跑整池 —— 中途被一个分类器缺陷（N43）误伤 33 条，修掉后拿到 **88%**。

### 4.56.1 全量重建 + **首次在全量规模上验证 bit 可确定性**

`rebuild_archives.py` 跑完 64 个归档（c-blosc2 33 · hunspell 22 · pcre2 7 · md4c 2；x86_64 46 + i386 18），墙钟约 1h40m：

```
逐字节校验：✅ 一致 498 个文件 · ❌ 不符 0 · 归档仍缺 0 条
归档 1.2G → 3.5G；磁盘 11G → 8.3G
```

**这比此前的证据强一个量级**：W4 只验过 4 个归档 20 文件、N30 恢复只验过 2 条 5 文件，而这次是 **64 个归档 / 498 个文件 / 跨 4 个项目 × 2 种架构**，且跨越了「原构建 → 删除 → 数小时后重建」的时间间隔 → **✅ `binary_sha256` 确实可作 `(project,san,commit,arch)` 的一致性校验**（§0.3 那条结论现在有了全量证据）。

交付视图同步刷新：**139 个条目全部四件齐全**（`binary`/`testcase`/`report.log`/`INFO.txt`）、`PRUNED.txt` **0 个**、断链 **0 个**；复现记录表侧 `verified 139 条，二进制在盘 139，缺 0`。

### 4.56.2 N42：Gitiles 解析器 —— 不需要镜像就能解锁 googlesource 系

N35 的镜像映射只救了 mupdf 一个项目；但可执行池里还有 **112 条**属 googlesource 系（android 58 · skia 18 · chromium 17 · aomedia 14 · boringssl 4 · code 1）。**Gitiles 自带 JSON 端点、且直接给 `parents`**，比 GitHub 的 `.patch` 信息还全 → 不需要任何镜像映射。

实现要点（都有自测，48 项）：

| 点 | 说明 |
|---|---|
| XSSI 前缀 | 响应以 `)]}'` 开头 → 必须剥到第一个 `{` |
| `parents` 形状 | **字符串数组**（不是对象数组）—— 我第一次按对象数组解析直接 `TypeError` |
| `~d` 语义 | Gitiles **没有 rev 语法** → 逐级走 `parents[0]`，d 次请求（有磁盘缓存） |
| merge commit | ✅ 实测样例 `67e394c9…` 就是 merge（2 个 parent）→ git 的 `~1` = **第一个** parent，取 `parents[0]` 正确 |
| 日期格式 | `author.time` 是 RFC2822（`Mon Aug 19 21:11:00 2019 -0700`）→ `email.utils.parsedate_to_datetime` |
| `_raw_url` | 一并支持 `+/<sha>/<path>?format=TEXT` → **`path_exists_at`/`submodule_paths` 对 googlesource 也可判**，这些项目从筛选里的 ⓘ 升为可预检 |

**✅ 已知答案**：`libhevc 67e394c9…~1 = 130f5f1fc107`（与原始 JSON 的 `parents[0]` 逐字一致）、`~2 = 6490a452d6f8`(2019-08-14)、`~3 = c1d762a4bd48`(2019-07-10)；`path_exists_at` 对**核实过的真实树** 6/6。

**⚠ 一个自己的方法论错误，值得记**：第一次测 `path_exists_at` 时我拿 `README.md`、`common/ih264_buf.c` 当「应该存在」的已知答案，结果 6 个全 `False`，**差点误判成假阴性缺陷**（N27① 同型）。实际是**该仓库根目录根本没有 README.md**（真实条目是 `Android.bp / CMakeLists.txt / NOTICE / OWNERS / common / decoder / encoder / fuzzer / test`），而且这是 **HEVC** 库不是 H264。→ **已知答案本身必须先核实**（用 `+/<sha>/?format=JSON` 取真实树），否则「回归测试」会变成「制造假缺陷」。这条已钉进自测的 [H] 节留档。

顺带修一个老 bug：错误串是 **`httphttp403`** 这种双重前缀（`rc.http_get` 返回的 code 已带 `http`，`resolve_commit_meta` 又套一层 `f"http{code}"`）→ 新增 `_http_err()` 归一，替换 3 处。危害是**诊断字符串误导**、且任何按 `http403` 匹配的下游都会失配。

### 4.56.3 离线筛 92 条：**淘汰 libaom，选中 libavc**（没花一分镜像钱）

| 项目 | 池 | ✅放行 | ⛔拦下 | 预测可构建率 | 主要缺失路径 |
|---|---|---|---|---|---|
| **libavc** | 43 | **40** | 3 | **93%** | `fuzzer/ossfuzz.sh` |
| libwebp | 10 | 8 | 2 | 80% | `tests/fuzzer/oss-fuzz/build.sh` |
| libhevc | 25 | 13 | 12 | 52% | `fuzzer/ossfuzz.sh` |
| **libaom** | 14 | **0** | 14 | **0%** | `aom/examples/av1_dec_fuzzer.dict` → **⛔ 淘汰** |

四项前置检查全过：N33（apt 包 4 个项目共 11 个、**0 个不可安装**）· N38（libavc 的 Dockerfile 是 `git clone https://github.com/…`**全量、https、github** → 低风险）· N34③（`no_sources`，不适用）· **N42 Gitiles 解析 92/92 成功**。另 ✅ 实测 Dockerfile 里 `ADD` 的 seed corpus 外链 **HTTP 200 活着**（N28 无风险 —— libspng 就死在这）。

**⚠ 抽样教训（差点选错项目）**：我先抽 3 条快筛时，libavc 显示 **3/3 ⛔**，全量跑却是 **40/43 ✅** —— 因为那 3 条恰好是**同一个 commit** `ab5b036e757c`（manifest 前几条同源）。**抽样必须按 commit 去重**，否则 3 条样本能给出与全量完全相反的结论。

### 4.56.4 N43：分类器漏识别一个形态 → 早停**误伤 33 条**

探针 **3/3 复现、5.6min** 通过后跑整池，结果只跑了 10/43 就结束：

```
⛔ [早停] libavc 已连续 2 次 `compile_error` → 跳过该项目本轮剩余队列
[walk-back 统计] … 早停跳过 33 条（被封项目 ['libavc']）
```

但真实错误**根本不是编译失败**：

```
ValueError: Commit b7dc3513d68e23e88ab8bb347a17ec188137c96b does not exist in current branch
```

**两个缺陷叠在一起**：

1. **分类漏形态**：已有 `commit_not_found` 类，但其正则（`not a commit|invalid reference|Could not find commit|pathspec…`）**匹配不到** `does not exist in current branch` → 落到 `compile_error`。
2. **`commit_not_found` 被错误地列进「版本确定性失败」**：`DETERMINISTIC_FAIL` 的定义是「由**上游 commit × 当前 build.sh/工具链**决定，**同项目同 era 必然同样失败**」。而 `commit_not_found` 成立与否取决于**是哪一个 commit** —— ✅ 反证就在同一轮里：**已试 10 条中 7 条复现成功**，且 github（29 条）与 android.googlesource（14 条）**两种源都出过复现**。把「逐 commit 才成立」的失败当「项目级必然失败」→ 连续 2 次就封整个项目。

**修法**：① 给 `commit_not_found` 补 `does not exist in current branch` 与 `ValueError: Commit <sha>` 两个形态；② 把 `commit_not_found` **移出** `DETERMINISTIC_FAIL`（与 `network_fetch` 同等对待）。自测 +6 项，含 **3 个负对照**：真 `compile_error` 仍须归类正确且**仍计入**早停（否则早停被这次修正搞失效）、`buildscript_mismatch`/`dockerfile_drift`/`toolchain_drift` 仍在。

**重跑 33 条 → 29 条复现（88%）、40 次构建 / 53.3min、`早停跳过 0 条`、`预检拦截 0 次`**。

### 4.56.5 结果

```
复现记录表 338 行 / 199 唯一 / 28 run
**复现 139/199 = 69.8%**（上一轮 106/156 = 67.9%）
tier: **strict 63**（+16）· medium 44 · loose 32 · none 60
按项目: c-blosc2 61 · **libavc 33** · hunspell 24 · pcre2 10 · libtsm 7 · md4c 3 · libspng 1
按 sanitizer: address 129 · memory 10 · undefined 0
libavc 明细: 16 strict + 8 medium + 9 loose = 33 复现；10 none（3 预检⛔ + 6 建成没崩 + 1 compile_error）
             arch: x86_64 26 · i386 7
verified 139 条**二进制全部在盘**（缺 0）；审计 **0 条红线违反**
```

**两个附带收益**：

* **项目集中度改善**：c-blosc2 占比 **58% → 44%** → 「复现率不能当全局估计」这个外推警示的严重性下降了一档（但仍成立）。
* **`T_strict` 第一次有区分力**：④ 报告「复现 ∧ crash_type 一致 ∧ `score_subseq<1.0`」的样本从 **0 → 3 条**（`OSV-2020-278`/`-370`/`-546`）。此前只能记「阈值 1.0 **未被证伪 ≠ 被验证**」，现在有了真实刻度样本（§2.2 那条局限可以改写）。

**新项目累计战绩：7 试 1 中** —— libspng 5% · libtiff 无构建 · libredwg 不可行 · opensc 0/3 · openh264 0/3 · mupdf 0/1（N38）· **libavc 33/43 = 77% ✅**。

### 4.56.6 下一批候选（已离线筛过、按赔率排）

| 项目 | 池 | 预检放行 | 备注 |
|---|---|---|---|
| **libwebp** | 10 | **8 (80%)** | chromium.googlesource（N42 已通）；池小但赔率高 |
| **libhevc** | 25 | 13 (52%) | android.googlesource；与 libavc 同厂（ittiam）、同 `fuzzer/ossfuzz.sh` 形态 → **libavc 成功是它的强正面先验** |
| ghostscript | 197 | 未筛 | **池最大**，但 ⛔ N38 高风险（`git://` + `--depth 1`，与 mupdf 同型同主机）|
| libaom | 14 | **0** | ⛔ 已淘汰 |

## 4.57 W5 第十三轮：libhevc + libwebp —— 项目数 7 → **9**，并首次拿到 MSAN flaky 重试的**生产证据**

### 4.57.1 前置检查（都在建镜像之前做完，秒级）

| 检查 | libhevc | libwebp |
|---|---|---|
| N28 外链存活 | ✅ seed corpus **HTTP 200** | ✅ 2 个 clone 源 + seed corpus **全 200** |
| N38 克隆形态 | ✅ `git clone https://github.com/ittiam-systems/libhevc.git`（**全量、https、github**） | ✅ 2 × `git clone https://chromium.googlesource.com/…`（**全量、https**，无 `--depth 1`、无 `git://`） |
| N33 apt 包 | ✅ 2 个（wget/cmake），0 不可安装 | ✅ 7 个，0 不可安装 |
| N42 解析 | ✅ googlesource/github 均通 | ✅ chromium.googlesource |
| build.sh 形态 | `$SRC/libhevc/fuzzer/ossfuzz.sh`（**与 libavc 同厂同形态**） | `bash tests/fuzzer/oss-fuzz/build.sh` |

镜像：libhevc **2.27GB**、libwebp **2.26GB**（层共享 → 实占增量远小于此）。

### 4.57.2 结果

| 项目 | 池 | 复现 | tier | 构建 | 墙钟 | none 归因 |
|---|---|---|---|---|---|---|
| **libhevc** | 28 | **10** | 4 strict + 6 medium | 10 次 | 6.8min | **预检⛔ 16** + 建成没崩 2 |
| **libwebp** | 10 | **3** | 2 strict + 1 medium | 8 次 | 29.5min | 预检⛔ 2 + 建成没崩 5 |

* **预检的预测被实测印证**：libhevc 离线筛预测放行 13/25 (52%) → 实际 `预检拦截 16 次`（28 条里）；libwebp 预测拦 2 → 实际拦 **2**。**离线筛与生产一致**，这是 N34 系列仪器第一次在两个新项目上双向对上。
* **N43 修复稳定**：两轮 `早停跳过 0 条`、`被封项目 无`。
* libhevc 探针（3 条 / 2 复现 / 2.0min）先跑，通过后才跑整池 —— 沿用 §4.45 定的流程。

### 4.57.3 ⭐ 首次拿到 MSAN flaky 重试的**生产证据**（销掉一笔挂了两轮的账）

此前复现记录表里 `retry_count > 0` 恒为 **0 条** → `retries_for(memory)` 那条路径**从未在真实数据上跑过**，只能靠 N16 的离线注入验证（8/8），并如实记为「MSAN flaky 重试从未触发」。本轮：

```
retry_count > 0 的 **9 条**，sanitizer **全是 memory**（libavc 2 · libhevc 3 · libwebp 4）
retry_count 分布：1 → 2 条，2 → 7 条
```

**而且它真的救回了复现**——`attempts[]` 里出现「先不崩、后崩」：

| OSV | crash_type | attempts（exit_code 序列） | 结果 |
|---|---|---|---|
| `OSV-2023-1322` | unknown | **`[0, 1]`** | 第 1 次不崩、**第 2 次崩** → 单次尝试会记成 `none` |
| `OSV-2020-1234` | use-of-uninitialized-value | **`[0, 1]`** | 同上（这条正是 libhevc 探针里的 medium） |
| `OSV-2023-95` | use-of-uninitialized-value | `[0, 0, 0]` | 重试 2 次仍不崩 → **如实记 none**（没有靠重试凑出复现） |
| `OSV-2020-1008` | use-of-uninitialized-value | `[0, 0, 0]` | 同上 |

**意义**：① 重试**确有产出**（至少 2 条是它救回的）；② 重试**没有变成造假工具**（`[0,0,0]` 的仍记 none，说明判据是「任一次崩了才算」而非「重试到崩为止」）；③ 只在 MSAN 上触发，与 `retries_for()` 的设计一致（ASAN 确定性崩溃不浪费重跑）。→ §5 那条「MSAN flaky 重试从未触发，需人工构造」的待办**可以销掉**。

### 4.57.4 累积状态

```
复现记录表 379 行 / 237 唯一 / 31 run
**复现 152/237 = 64.1%**
tier: **strict 69** · medium 51 · loose 32 · none 85
按项目: c-blosc2 61 · libavc 33 · hunspell 24 · pcre2 10 · **libhevc 10** · libtsm 7 · md4c 3 · **libwebp 3** · libspng 1
按 sanitizer: address 135 · **memory 17**（上一轮 10）· undefined 0
verified 152 条**二进制全部在盘**（152/152）；by_crash_type 条目 152 个四件齐全、0 PRUNED、0 断链
c-blosc2 占比 **40%**（W5 初 58% → 上轮 44% → 本轮 40%）
审计 **0 条红线违反**；自测 **18 套 284 项 / 0 失败**
```

⚠ **复现率从 69.8% 降到 64.1% 不是退步**：新进来的 38 条里 **18 条被预检判为该 commit 树上缺 build.sh 引用的文件**（libhevc 16 + libwebp 2），它们**从未被构建**，属「基础设施不可达」而非「复现方法失效」。若只算**真拿到二进制并重放过**的：`152 / (237 − 18 − 其它未构建)`，口径见 §0.3。

**新项目累计：9 试 3 中** —— libspng 5% · libtiff 无构建 · libredwg 不可行 · opensc 0/3 · openh264 0/3 · mupdf 0/1（N38）· **libavc 33/43 ✅** · **libhevc 10/28 ✅** · **libwebp 3/10 ✅**。
**规律**：三个成功项目的 Dockerfile 都是「**全量 https 克隆、无 `git://`、无 `--depth 1`**」；失败的要么外链死（N28）、要么 era 包下架（N33）、要么 `git://` + 浅克隆（N38）。→ 这条**已可作为筛选的硬前置**（见 §5）。

### 4.57.5 磁盘

`purge` 默认关之后归档持续累积：本轮 4.2G → **5.2G**，磁盘 7.3G → **5.6G**。两个新镜像各 ~2.3G（层共享后实占更少）。再往下跑大池之前需要按 §5 第 44 条做**分级保留策略**，而不是回到「全删」。

## 4.58 W5 第十四轮：用户一句「一个 OSV 为什么有这么多二进制」拽出 4 个真缺陷（N45–N49）

**触发方式值得记下来**：这不是自测或审计发现的，是**用户看着交付目录问了一句结构问题**。
我原先回答「结构是对的，`binary` 是整棵构建树」，顺手去核 `INFO.txt` 里的字段，发现
`fuzz_target=svc_enc_fuzzer` 而目录里只有 `avc_dec_fuzzer` —— 由此拉出 4 个缺陷，其中 2 个
**直接违反 §0.3 的核心承诺「verified = 可重放」**，而当时审计报的是「0 条红线违反」。

### 4.58.1 N45（🔴 严重）⑤ 的连接键优先级反了 → 2 条复现记录表指向**没崩的那一格**

`annotate_dataset.merge()` 的 `binary_dir` / `binary_sha256` / `pinned_commit` **三个字段全部取自
`brec`（构建记录）**，而 `brec` 的选法是：

```python
b = b_by_osv.get(oid)                                  # ← 永远优先
if not b and o and o.get("binary_dir"):
    b = b_by_dir.get(o["binary_dir"])                  # ← 只有前者为空才反查
```

`_load_build_index` 里 `by_osv[d["osv_id"]] = d` 是**后者覆盖前者** → 拿到的是该 OSV
**最后一次**构建。而 walk-back 对 loose 档「继续下探」，最后一格往往**不是崩的那格**。
observation 里的 `binary_dir` 才是 ③ 从**真正重放并崩掉的那一格**抄来的 —— 它才是权威连接键。

✅ 实测受害 **2 条**（`build_records.jsonl` 里的正确记录一直都在）：

| OSV | 项目/san | 复现记录表记的（错） | 真相（崩的那格） | 错的归档里有什么 |
|---|---|---|---|---|
| `OSV-2020-1016` | c-blosc2/memory | `dca55210…` | **`b7d25a74…`**（SEGV，depth 2） | 只有 `llvm-symbolizer` |
| `OSV-2023-48` | libavc/address | `bb0f31cb…` | **`e14ee149…`**（ABRT，depth 1） | `avc_dec_fuzzer`（**别的 target**） |

后果是**实的**：按 `INFO.txt` 里给出的命令重放 →

```
bash: line 1: ./svc_enc_fuzzer: No such file or directory        退出码 127
```

**修法**（根因，不是改数据）：把优先级反过来 —— 先按 observation 自己的 `binary_dir` 反查，
查不到才退回 `osv_id`。然后用**修好的流水线重跑这 2 条**（`--only-osv`，run_id=`w5-fix-n45`，
4 次构建 / 5.1min），归档重建 + 重判 + 追加更正行一次到位：

```
OSV-2020-1016  pinned=b7d25a74 ✅  binary_sha256 含 decompress_fuzzer ✅  盘上可执行 ✅
OSV-2023-48    pinned=e14ee149 ✅  binary_sha256 含 svc_enc_fuzzer    ✅  盘上可执行 ✅
```

**并用实测重放收尾**（不是「目录里有文件」就算）：

```
退出码 1
SUMMARY: AddressSanitizer: ABRT (/lib/x86_64-linux-gnu/libc.so.6+0x9ec0c) in pthread_kill
DEDUP_TOKEN: pthread_kill--raise--abort
```

⚠ **我自己的测量也错过一次**：第一次验证时把 docker 输出接进 `grep | head`，`head` 提前关管道
+ `&&` 链把 `PIPESTATUS` 冲掉 → 读到「退出码 0」，差点误判成「重建后仍不崩」。
**不带管道直跑才是 1**。教训：验证命令本身也要被验证。

### 4.58.2 N46（🔴 严重）libFuzzer **超时**被当成复现 → 复现数虚高 1 条

⑥ 的 `classify()` 里 `evidence = crash_type or ubsan_detected or engine_summary or dedup_token`。
libFuzzer 打到 `-timeout=25` 上限时会打：

```
==7== ERROR: libFuzzer: timeout after 25 seconds
DEDUP_TOKEN: __sanitizer_print_stack_trace--fuzzer::PrintStackTrace()--fuzzer::Fuzzer::AlarmCallback()
SUMMARY: libFuzzer: timeout                     exit=70
```

那个 DEDUP_TOKEN **全是引擎自己的告警回调帧，没有任何目标代码帧** → `engine_summary`+`dedup_token`
双双命中 evidence → `crashed=True` → ④ 落到 else 分支给 **loose**（"崩了但 crash_type 不一致"）。

✅ 实测受害 1 条：`OSV-2023-1206`（libavc/address），期望 `Heap-buffer-overflow WRITE {*}`，
实测 `timeout`、`score_subseq=0.0`。**超时是资源上限，不是所报的那个漏洞。**

**修在两处（单一真源 + 防线）**：
* ⑥ `classify()`：新增 `non_crash` —— 实测类型 ∈ `rc.NON_CRASH_DIAGNOSTICS`
  (`timeout`/`out-of-memory`/`oom`/`no-crash`) **且没有任何 sanitizer 报告** → `crashed=False`。
  ⚠ 集合**不含空串**（空 `crash_type` 只代表解析器没认出来），也**不排除 `deadly signal`**（裸 SEGV 是真崩溃）。
* ④ `verify_one()`：同样的判断放在分级之前 → **重跑 ④⑤ 即可纠正历史数据**，不必手改 append-only 复现记录表。
* ⑤ `merge()`：④ 判了 `non_crash_diagnostic` 时**不得盲抄 observation 的过期 `reproduced_any`**
  （否则出现「tier=none 却 reproduced_any=True」的自相矛盾行 —— ✅ 本轮审计当场抓到 2 条红线）。

**已知答案用真实日志**：把 `OSV-2023-1206.log` 原样拷成 `preflight/fixtures/timeout_libavc.log`
（第 5 个 fixture），并加一条**合成反向对照**（真 ASan 报告 + 超时诊断并存 → 仍须 `crashed=True`），
证明防线不过度触发。④ 侧另加 4 条 `verify_one` 用例（timeout→none、OOM→none、
timeout+ASan→loose、普通崩溃→medium）。

⚠ 途中撞到一个坑：`verify_one` 的合成用例传假 `osv_id` 会在
`r2_r5_r6_r7_recompute.py:44` 抛 `NameError: rec`——因为 `normalize_frames` 是**闭包引用模块级
`rec`**，必须先 `rc.install_recovered(rc.load_recovered())` 注入。已照 main 的做法补上。

**结果**：`OSV-2023-1206` → `tier=none`，**复现 152 → 151**，loose 32 → 31，libavc 33 → 32。

### 4.58.3 N47（ⓘ 字段级）`exit_code` **不可作判崩依据**

3 条 libwebp（`OSV-2025-796`、`OSV-2025-797` = **strict**，`OSV-2024-1356` = medium）复现记录表
`exit_code=0`，但 report 里是货真价实的崩溃：

```
==10==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x7bd1234fef80
SUMMARY: AddressSanitizer: heap-buffer-overflow /src/libwebp/src/dsp/lossless_avx2.c:349:5 in AddGreenToBlueAndRed_AVX2
```

且 `OSV-2025-796` 的判分极干净：期望 `Heap-buffer-overflow WRITE {*}` vs 实测 `WRITE 32` → 一致；
`recovered=[AddGreenToBlueAndRed_AVX2, VP8LInverseTransform, ProcessRows]` 是 observed 的子序列
→ `score_subseq=1.0` → strict。

**结论**：⑥ **按报告内容判崩**是正确设计 —— 若按退出码判，**libwebp 会是 0/10**（3 条全丢）。
但 `exit_code` 这个字段本身不可靠，审计里作**软性**提示而非红线。
（🅗 未查明为何 exit=0：target 名是 `advanced_api_fuzzer@AdvancedApi.AdvancedApiTest` 这种
gtest 形态，疑为子进程崩溃而父进程正常退出；未继续深挖，因为判崩不依赖它。）

### 4.58.4 N48 审计「有牙无齿」→ 补 3 条红线

`w5_audit_delivery.py` 此前只查 `binary_dir` **是不是目录** → N45/N46 躺在里面却报「0 条红线」。
新增 `[4b]「可重放」的实质检验`：

| 红线 | 判据 | 修复前 | 修复后 |
|---|---|---|---|
| N45-a | `binary_sha256` 的键必须含自己的 `fuzz_target`（**复现记录表自证**，与目录在不在盘无关） | ❌ 2 条 | ✅ 0 |
| N45-b | 盘上 `binary_dir/<fuzz_target>` 必须是可执行文件（否则重放 exit=127） | ❌ 2 条 | ✅ 0 |
| N46 | verified 行的 `observed_crash_type` 不得 ∈ `NON_CRASH_DIAGNOSTICS` | ✅（已由 ④ 纠正） | ✅ 0 |
| N47 | `exit_code != 1` 的 verified 行 | — | ⓘ 软性 3 条 |

`NON_CRASH_DIAGNOSTICS` 从 `repro_common` 导入（**单一真源，不在审计里复制一份**）。
补牙后立刻自证有效：**先报出 4 条红线**（N45×2 + N46 残留×2），修完才归零。

### 4.58.5 N49 交付视图布局：`binary` 从「整棵树」收窄成「单个 driver」

**用户的疑问完全成立**：一个 OSV 就该对应一个二进制、一个 testcase、一份 report。而原先
`binary` 是**指向归档目录的符号链接**，于是「一个 OSV」下面出现 **1～17 个可执行文件**
（✅ 实测分布：5 个的最多，43 个目录）。

根因不在交付层：`archive_build` 按 `(project, san, commit)` 归档**整棵 `build/out/`**，那是
**归档层的正确设计**（W2 教训：只存请求的那个 target，会让同 commit 的另一条 crash 缓存命中却
找不到 target → pcre2 **8 条 `target_not_in_archive`**）。错在**交付视图直接把这个目录当
`binary` 暴露出去**。

改为：

```
by_crash_type/<crash_type>/<project>/<sanitizer>/<commit>[@arch]/<OSV-ID>/
    ├── binary      → **单个可执行文件** = out/<fuzz_target>（这条 crash 的 driver）
    ├── out         → 整棵构建树（driver 的运行期依赖：libclang_rt.*.so、.dict/.options）
    ├── testcase    → 输入文件
    ├── report.log  → 崩溃报告原文
    └── INFO.txt    → 顶部两行写明「可执行 driver = …」「out/ 里其它文件 = 依赖，不是多个复现结果」
```

**为什么 `out/` 必须保留**：driver 动态链接 `libclang_rt.*.so`、还要读同名 `.dict`/`.options`
→ **只给 driver 会重放失败**。driver 缺失时写 `DRIVER_MISSING.txt` 说明，**绝不留断链**。

✅ 重建后：151 条目，`binary` 单文件链接 **151**、`out` 链接 **151**、断链 **0**、
driver 缺失 **0**、已回收 **0**；抽样 `file` 验证 `binary` 确为
`ELF 64-bit LSB pie executable, x86-64 … not stripped`。

### 4.58.6 累积状态（本轮后）

```
复现记录表 383 行 / 237 唯一 / 34 run
**复现 151/237 = 63.7%**（N46 前 152 —— 少的 1 条是超时假复现）
tier: strict **69** · medium 51 · loose **31** · none 86
按项目: c-blosc2 61 · libavc **32** · hunspell 24 · pcre2 10 · libhevc 10 · libtsm 7 · md4c 3 · libwebp 3 · libspng 1
按 sanitizer: address 134 · memory 17 · undefined 0
**driver 在盘 151/151**（此前只验过「目录在盘」）；归档 122 个目录 / 4.7G；磁盘 5.5G
by_crash_type 151 条目 · binary 单文件链接 151 · out 151 · 断链 0
审计 **0 条红线**（含新增 3 条）；自测 **18 套 293 项 / 0 失败**
约束：主树 550 ✅ worktree dirty=0@07522dc0e ✅ infra md5 f5092d0a3f2a6909 未变 ✅ dc 0 ✅ Dockerfile/build.sh 改动 0 ✅ 根目录仅 DELIVERY.md ✅
```

**方法论收获**：本轮 4 个缺陷里，**没有一个**是被既有自测或审计发现的；全部源于
「用户看着交付物问了一个结构问题」。→ 交付视图不只是产物，**它是最有效的评审界面**；
审计的判据必须落在「消费者实际会做的动作」上（能不能重放），而不是「字段是否非空」。

## 4.59 W5 第十五轮：用户第二次指出「一个 OSV 为什么有多个二进制」→ 交付视图重做 + **首次全量重放验收**（N50–N52）

### 4.59.1 N49 没解决问题，用户是对的

N49 把 `binary` 从「目录链接」收窄成「单文件链接」，**却仍保留 `out/` 指向整棵构建树** → 打开 OSV 文件夹
照样看到 **2～17 个可执行文件**。用户第二次指出后实测确认：

```
by_crash_type/check-failed/libavc/memory/3cc9ff94d…/OSV-2023-1305/out/
    avc_dec_fuzzer  avc_enc_fuzzer  mvc_dec_fuzzer  svc_dec_fuzzer  svc_enc_fuzzer  llvm-symbolizer  avcdec_fuzzer.dict
```
这条 OSV 的 target 只是 `svc_dec_fuzzer`，其余 4 个是**同一次构建产出的兄弟 fuzz target**，与它无关。
✅ 实测每个归档目录的可执行文件个数：**2～17 个**（libwebp 最多 17；5 个的最常见，43 个目录）；
151 条里有 **132 条**的归档含「别的文件」，合计 **1,497 个**对该条 crash 毫无用处的文件。

**根因分层**：`archive_build` 按 `(project, san, commit)` 归档整棵 `build/out/` 是**归档层的正确设计**
（W2 教训：只存请求的那个 target → 同 commit 的另一条 crash 缓存命中却找不到 target → pcre2 **8 条
`target_not_in_archive`**）。**错在交付层直接把它暴露出去**。→ 归档层存全、交付层收窄，两层各司其职。

### 4.59.2 ⭐ 推翻我自己写进文档的一个结论

N49 的注释里我写过「**只给 driver 会重放失败**（driver 动态链接 `libclang_rt.*.so`、要读 `.dict`）」。
本轮**做实验去验它**，结论是**错的**：

* `ldd svc_dec_fuzzer` → **0 个 `not found`**，且**没有 `libclang_rt.*.so`** → ASan/MSan 运行时是
  **静态链进 driver** 的；
* 符号化也**不依赖**归档里的 `llvm-symbolizer`（只放 driver 时报告仍是完整 `file:line` 栈）；
* ✅ **14 个项目×sanitizer 组合逐条真跑「只放 driver（+自身 .dict）」→ 全部崩**，含 i386、含 MSAN。
  例：`hunspell/address` 原归档 **42 个文件** → 只放 1 个 → `AddressSanitizer` 报告照样出。

那条「只给 driver 会失败」是**从 W2 flatbuffers 缺 `monster_test.bfbs` 的个案过度泛化**来的，
写进文档后一直没被检验。**教训：写进交付文档的每一条「必须如此」都该有实验支撑，否则它会在
后续设计里被当成前提反复引用**（N49 就是被它带偏的）。

### 4.59.3 最小重放包的规则必须**精确**，不能用「同前缀」

先试的规则是「取所有以 target 名为前缀的文件」——✅ 实测**过度包含**：`pcre2_fuzzer_1` 会匹配到
`pcre2_fuzzer_16`，产生 **1 个 21 文件的包**和 **3 个含 2 个 ELF 的包**。

改为精确规则：**target 本身 + 若它不是 ELF 而是脚本包装器则解析它引用的兄弟文件 + 同名 `.dict`/`.options`**。

```
✅ 151 条实测：每包**恰好 1 个 ELF**（151/151）
   包内文件数：1 个 → 128 条 · 2 个 → 19 条 · 3 个 → 4 条
   合计 1555 MB；用**硬链接** → 交付视图额外占 **0 字节**
```

新布局（**一个 OSV 文件夹 = 一次复现**）：

```
by_crash_type/<crash_type>/<project>/<sanitizer>/<commit>[@arch]/<OSV-ID>/
    ├── <fuzz_target>        ← **唯一的 ELF**（硬链接到归档）
    ├── <fuzz_target>.dict   ← 仅 14 条有：运行期数据文件（**不是**二进制）
    ├── <包装脚本>            ← 仅 libwebp 3 条：入口脚本，它调上面那个 ELF
    ├── testcase             ← 输入（副本）
    ├── report.log           ← 崩溃报告（**冻结副本**，见 4.59.6）
    ├── replay.sh            ← 一条命令重放，**自己打判决**
    └── INFO.txt             ← 唯一可执行是谁 / tier / 期望vs实测 / 判分依据 / flaky 实测
```
128 条整个文件夹只有 **5 个条目**（1 个二进制 + testcase + report + replay.sh + INFO）。

### 4.59.4 N47 的悬案破了：libwebp 的 target 是**shell 包装脚本**

```sh
#!/bin/sh
this_dir=$(dirname "$0")
export TEST_DATA_DIRS=$this_dir/corpus
chmod +x $this_dir/advanced_api_fuzzer
$this_dir/advanced_api_fuzzer --fuzz=AdvancedApi.AdvancedApiTest -- $@
chmod -x $this_dir/advanced_api_fuzzer        ← **脚本退出码 = 最后一条命令 = chmod 成功 = 0**
```

真 ELF 是 `advanced_api_fuzzer`，`…@AdvancedApi.AdvancedApiTest` 只是 gtest 选择器包装。
子进程 ASan 崩了，**但脚本返回的是 `chmod` 的 0** → 这就是 §4.58.3 里 3 条 libwebp
`exit_code=0` 却有完整 ASan 报告的原因。**上一轮记为 🅗 未查明，本轮 ✅ 已定性。**
（同时说明：包装脚本引用的 ELF 必须一起打包，否则 `./advanced_api_fuzzer: not found`。）

### 4.59.5 N51 交付的 `replay.sh` 必须**照抄复现记录表的运行参数**

首版 `replay.sh` 只跑 `./<target> -- /testcase`，漏了 ⑥ 当时带的
`FUZZER_ARGS='-rss_limit_mb=2560 -timeout=25'` → libFuzzer 用默认 **2048MB** 上限。后果是实的：

```
OSV-2021-464（复现记录表 tier=strict、验证时 score_subseq=1.0、crash_type 完全对得上）
OSV-2021-366（同上，negative-size-param）
  → 在交付文件夹里重放变成 SUMMARY: libFuzzer: out-of-memory、容器 exit=71
```
补上参数后 **各 2/2 稳定复现**，且类型与复现记录表一致（`heap-buffer-overflow` / `negative-size-param`）。

**原则**：交付的重放命令如果与「产出那份 report 的那次实验」不是同一个实验，
**比不给命令更糟** —— 消费者会得出「这条复现不了」的错误结论。参数一律从复现记录表
`runtime_limits` 解析（✅ 151 条该字段完全一致），`.dict` 也按 ⑥ 的条件带上。

### 4.59.6 report.log 改为**冻结副本**，并挑对的那一份

`logs/reproduce/<OSV>.log` 是**单一可变路径**，后一次重放会覆盖它；而 walk-back 对 loose 档
「继续下探」→ 盘上最新那份往往来自**更深、没崩的那一格**（§5 item 50）。交付视图改为**存副本**，
并在 N40 的轮转副本里挑「`# binary_dir:` 与复现记录表一致 **且** `# exit: 1`」的那一份；
挑不到才退回 `raw_log_path` 并**在 INFO.txt 里如实标注**（本轮 4 条）。

### 4.59.7 ⭐ 首次**全量重放验收**：151/151

此前所有「二进制在盘」的核对都只验到「**目录存在**」（N45 就是这样漏网的），最多加验
「**driver 文件存在**」。**从未真跑过一遍**。本轮对 151 个条目逐个执行各自的 `replay.sh`
（失败者最多重试 3 轮，仍失败的单独加测）：

```
✅ 可重放 **151/151 = 100%**      总尝试 157+8 次
   首轮即崩        148 条（98.0%）
   重试后崩          2 条  OSV-2023-48、OSV-2023-75（都是第 3 次）
   重度 flaky        1 条  OSV-2023-948（i386，加测到**第 8 次**才崩，**崩溃率 12%**）
```

`OSV-2023-948` 值得单记：它复现记录表 tier=**loose**、期望 `Global-buffer-overflow` 而当次实测 `ABRT`。
第 8 次崩时打出的是 **`ERROR: AddressSanitizer: global-buffer-overflow`** —— **正是期望的类型**。
→ 同一条 crash 在不同次运行里可以表现为 `ABRT` 或 `global-buffer-overflow`；
**这也说明「loose = crash_type 不一致」里混着「同一 bug 的不同表现」**（N15 早就提过这个形态，
这是第一次拿到直接证据）。

**判决规则必须按报告内容、不能按容器退出码**（N47）：3 条 libwebp 的容器退出码恒为 0，
但报告里有完整 ASan 崩溃 → 按退出码判会把它们全算成「没复现」。

结果固化为机器可读产物 **`artifacts/replay_verification.json`**，并**回写进每个条目的 INFO.txt**
（`重放实测 = ⚠ flaky：第 3 次才崩 → 请多跑几次`），让消费者一眼知道要不要重试。

### 4.59.8 本轮自查抓到的自身缺陷

| # | 缺陷 | 怎么抓到的 |
|---|---|---|
| 1 | 包装脚本被 chmod 成 644 → libwebp 3 条 `exit=126` | 全量重放实测 |
| 2 | `replay.sh` 漏 `runtime_limits` → 2 条 strict 变 OOM | 全量重放实测 |
| 3 | 验收判据用「容器退出码==1」→ 3 条 libwebp 被误判失败 | 逐条看输出 |
| 4 | 「同前缀」打包规则过度包含 → 1 个 21 文件包、3 个双 ELF 包 | 打包前离线核算 |
| 5 | 文档里「只给 driver 会重放失败」是错的（过度泛化） | `ldd` + 14 组合真跑 |
| 6 | `while read` 循环里 `docker run -i` 抢 stdin → 只跑了第 1 条 | 输出条数不对 |
| 7 | 判崩 grep 漏 MSan 的 `WARNING:`（只写 `ERROR:`）→ 4 条真崩被判失败 | 逐条看输出 |

### 4.59.9 累积状态

```
复现记录表 383 行 / 237 唯一 / 34 run          复现 **151/237 = 63.7%**
tier: strict **69** · medium 51 · loose 31 · none 86
按项目: c-blosc2 61 · libavc 32 · hunspell 24 · pcre2 10 · libhevc 10 · libtsm 7 · md4c 3 · libwebp 3 · libspng 1
按 sanitizer: address 134 · memory 17 · undefined 0
交付视图 **151 条目 · 每条恰好 1 个 ELF · 全部实测可重放（148 首轮 / 2 需 3 次 / 1 需 8 次）**
硬链接 → 交付视图额外占 0 字节；归档 4.7G；磁盘 5.4G
审计 **0 条红线**（含 N48 新增 3 条）；自测 **18 套 293 项 / 0 失败**
```

**方法论收获**：本轮 7 个自身缺陷**全部**由「真跑一遍全量交付物」抓出，无一由静态检查发现。
§0.3 里「verified = 可重放」这句话，在跑完这 151 次重放之前，其实**还没有被验证过**。

## 4.60 W5 第十六轮：N39 落地（strict **69 → 86**）+ N53 把用户两次指出的性质写成红线

### 4.60.1 N39 修在哪：**只改 O 侧**，绝不动 AST 提取的权威实现

observed 侧的栈来自 ASan/MSan 的**符号化输出**（带完整参数类型），recovered 侧（R，ground truth）
来自 ClusterFuzz 的 `DEDUP_TOKEN` / crash state（**只有函数名**）→ 逐字比对必然不等：

```
R = ['AffixMgr::cpdcase_check', 'AffixMgr::compound_check', 'HunspellImpl::checkword']
O = ['AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::allocator<char>> const&, char const*) const', …]
    → score_subseq = 0.0 → 只能判 medium（crash_type 明明一致）
```

新增 `rc.strip_cpp_signature()`，**只挂在 `normalize_observed`（O 侧）末尾**。
⚠ **不能塞进 `normalize_one_frame`**：那是从 `preflight/history/r2_r5_r6_r7_recompute.py`
**AST 逐字提取**的权威实现、R/O 两侧共用；改它等于同时改 ground truth，并与历史结果分叉（N4 同族事故）。

⚠ **不引入假 strict**：R 侧本来就没有签名粒度，把 O 降到同一粒度是**对齐**而非放宽；
重载折叠（`f(int)`/`f(double)` 同为 `f`）是 R 侧 ground truth 固有的，不是本函数带来的。

边界都写了已知答案（**11 例全部取自复现记录表里的真实帧**）：

| 输入 | 输出 | 考点 |
|---|---|---|
| `AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::allocator<char>> const&, char const*) const` | `AffixMgr::cpdcase_check` | 模板实参 + 尾缀 `const` |
| `SfxEntry::test_condition(char const*, char const*)` | `SfxEntry::test_condition` | 多指针参数 |
| `ihevce_enc_frm_proc_slave_thrd` | 原样 | **C 帧不受影响** |
| `A::operator()` / `A::operator()(int)` | `A::operator` | **`operator()` 的括号是函数名本身**，不能当签名剥 |
| `foo<int>::bar(int)` | `foo<int>::bar` | **模板实参里的尖括号不受影响** |

外加一条端到端：复现记录表里真实的 `OSV-2022-1260`，剥签名后 `score_pos` 与 `score_subseq`
都从 **0.0 → 1.0**。④ 自测 **18/18 通过**。

### 4.60.2 先干跑量影响，再落账

```
═══ 干跑（不动复现记录表，只重算）═══
  strict → strict    69 条   ← 不变
  medium → medium    34 条   ← 不变
  loose  → loose     31 条   ← 不变
  medium → strict    17 条   ★ 全部是 hunspell
  升档 17 条；**降档 0 条**
```

落账方式与 N39/N46 一致：**重跑 ④⑤、追加更正行**（append-only，不改写历史）。
⑤ 的单调性守卫记录 **17 条 verified→verified 升档、0 条拒写**（留痕 `artifacts/dataset_guard.jsonl`）。

**18 个候选里 17 升 1 不升，那 1 条不升是对的**（`OSV-2022-899`）：

```
R = ['std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<ch', 'PfxEntry::add', 'AffixMgr::expand_rootword']
O = ['strlen', 'PfxEntry::add', 'AffixMgr::expand_rootword', 'SuggestMgr::ngsuggest', …]
score_pos=0.6667  score_subseq=0.0  crash_type_match=True  → medium
```
R 的首帧是**模板类型名**（原始 crash 崩在 `basic_string` 内联处），而本次重放该位置是 `strlen`
→ 子序列确实不成立。N39 对其它帧的剥离是生效的（`PfxEntry::add(char const*, unsigned long)` →
`PfxEntry::add` ✅）。**这条留在 medium 是判据正确工作的证据，不是漏改。**

### 4.60.3 N53 把「一个 OSV = 一个二进制」写成审计红线

这条性质是**用户两次指出**的（§4.58、§4.59）。既然靠人眼看交付目录两次都没守住，就该由测试守：

```
[4c] 交付视图 by_crash_type/：一个 OSV = 一次复现 = **一个**二进制
  ✅ [N53] 151 个条目**每条恰好 1 个 ELF**（分布 {1: 151}）
  ✅ [N53] 151 个条目四件齐全（testcase/report.log/replay.sh/INFO.txt）
  ✅ [N53] 断链 0
```

**牙齿测试**（红线必须能被触发，否则等于没有）：往一个条目里塞第二个 ELF →

```
❌ [硬] **[N53] 交付视图里有 1 个条目的 ELF 个数 ≠ 1**：[('OSV-2016-5', 2)]
```
清掉后恢复 0 红线。

### 4.60.4 累积状态

```
复现记录表 401 行 / 237 唯一 / 35 run          复现 **151/237 = 63.7%**
tier: **strict 86** · medium 34 · loose 31 · none 86
**strict 占复现 = 57.0%**（N39 前 45.7%）
按项目: c-blosc2 61 · libavc 32 · hunspell 24 · pcre2 10 · libhevc 10 · libtsm 7 · md4c 3 · libwebp 3 · libspng 1
按 sanitizer: address 134 · memory 17 · undefined 0
交付视图 151 条目 · **每条恰好 1 个 ELF** · 文件夹条目数 5/6/7（128/19/4 条）· 断链 0
全量重放验收 **151/151 = 100%**（首轮 148 · 2 条第 3 次 · 1 条 i386 第 8 次 / 崩溃率 12%）
审计 **0 条红线**（含 N48 的 3 条 + N53 的 3 条）；自测 **18 套 306 项 / 0 失败**
磁盘 5.3G · 归档 4.7G
```

⚠ **`T_strict` 仍无区分力**：升档的 17 条 `score_subseq` 全是 **1.0**（不是 0<x<1），
所以「复现 ∧ crash_type 一致 ∧ `score_subseq<1.0`」的刻度样本仍是 **3 条**（§4.57.3）。
**N39 提高了 strict 的数量，但没有给 `T_strict=1.0` 这个阈值本身提供任何新证据** —— 
这两件事必须分开说，否则容易把「升档 17 条」误读成「阈值被验证了」。

## 4.61 W5 第十七轮：一个静默回显 bug 造出两个假结论（N54–N57）+ 分类器过宽（N58）+ UBSAN 缺口破了（N59–N60）

### 4.61.1 又推翻我自己写进文档的一条「规律」

§4.57.4 我写过：新项目的硬前置是「**全量 https 克隆、无 `git://`、无 `--depth 1`**」（9 试 3 中归纳的）。
本轮**逐条实测，全部推翻**：

| 上游 | 协议 | depth1 | `git fetch --unshallow` | 结论 |
|---|---|---|---|---|
| perfetto (android.googlesource) | https | 6s / 32M | **31s** → 306M | ✅ |
| kimageformats (invent.kde.org) | https | 10s / 39M | **7s** → 46M | ✅ |
| matio / zlib / hdf5 (github) | https | 2s / 81s | **5s / 7s / 60s** | ✅ |
| skia (skia.googlesource) | https | 77M | **<240s** → 810M | ✅ |
| qemu (git.qemu.org) | https | 41M | 240s 未完成 → 226M | ⏱ 存疑 |
| **ghostpdl (git.ghostscript.com)** | **`git://`** | 33s / 72M | **420s → 仅 84M（≈29 KB/s）** | ⛔ |
| dnsmasq (thekelleys.org.uk) | **`git://`** | — | `git ls-remote` **退出 0** | 协议**可达** |

* **`git://` 在本环境是通的**（两个都 `ls-remote` 成功）→ 「无 `git://`」这条判据**不成立**；
* **`--depth 1` 也不致命**：infra 的 `checkout_commit()` **第 218 行先调 `fetch_unshallow()`**
  （`repo_manager.py:188-194`），浅克隆会自己补全 → 「必须全量克隆」**不成立**；
* 真正的判据是 **实测 unshallow 吞吐**。ghostscript 那 192 条大池的死因不是协议，是
  **29 KB/s**（完整历史按此速率要 10–20 小时）。`fetch_unshallow` 失败时**只 `logging.error` 不抛**
  → 随后 `commit_exists()` 判假 → 报 `ValueError: Commit … does not exist in current branch`
  （**正是 N43 处理的那个串**）。

⚠ 这是**第二次**发生同一类错误（上一次是 §4.59.2「只给 driver 会重放失败」）：
**从少数样本归纳出的「规律」被写进文档后，就成了后续决策的前提，而它从没被单独检验过。**

### 4.61.2 N54（🔴 严重）解析器**把输入原样回显**成「已解析的 SHA」

`resolve_commit_meta()` 末行是：

```python
return {"sha": pc.get("sha") or sha, "date": d, "error": None}     # ← 解析不出就回显输入
```

`invent.kde.org`（自建 GitLab）的 `/-/commit/<rev>.patch` **不接受 `<sha>~d`** → 解析不出 →
**回显 `<sha>~3` 且 `error=None`**，把「没解析」伪装成「解析成功」。后果是一条完整的错误链：

```
回显假 SHA → ② 以为拿到真 SHA、把 `<sha>~3` 传给 infra
          → infra `checkout_commit`：`git checkout -f <sha>~3` **成功**，
            但末行 `if self.get_current_commit() != commit`（**完整 SHA** vs **字面量 `…~3`**）必然不等
          → RuntimeError: Error checking out commit …~3
          → 分类器不认这个串 → 落 `compile_error` ∈ DETERMINISTIC_FAIL
          → 连续 2 次 → **N43 早停封掉整个项目**
```

✅ 实测受害：kimageformats 探针 **0/3**、另 2 条被跳过；且离线预检也拿假 SHA 报
「**kimageformats 14/14 放行**」——**一个 bug 造出两个假结论**（假淘汰 + 假放行）。

爆炸半径**已核**：复现记录表里 `pinned_commit` 非纯 SHA 的**只有 1 条**（`OSV-2020-2086`，tier=none）
→ **已交付的 verified 行无一被污染**。

修：`SHA_RE` 校验，解析不出就返回 `error=unresolved_sha:<输入>`、`sha=None`，**绝不回显**。

### 4.61.3 N55 / N56 / N57

| | 缺陷 | 修法 |
|---|---|---|
| **N55** | 预检对垃圾输入返回 `ok=True`（`reason='no_build_sh'`）→ 假放行。文档里「无法判定时一律放行」针对的是**查不到**，不是**给了垃圾** | 非空但非纯 SHA → `ok=False, reason=bad_rev:…`（**输入非法 ≠ 无法判定**） |
| **N56** | `RuntimeError: Error checking out commit` 不被任何 pattern 认 → 落 `compile_error` → 计入项目级早停 | 并入 `commit_not_found`（同族：**逐 commit 成立、非项目级必然**）→ 自动排除在 `DETERMINISTIC_FAIL` 外 |
| **N57** | 自建 GitLab 无法解析 `~d` | 新增 `gitlab_commit()`：`GET /api/v4/projects/<path>/repository/commits/<sha>` 取 **`parent_ids`**，逐级走 `parents[0]`（与 N42 Gitiles 完全同法，merge commit 亦正确）。✅ 实测 `invent.kde.org` `~0…~3` 全部解析出纯 SHA + 日期；`~2` 的标题正是 `xcf: Fix Stack-buffer-overflow WRITE …` |

四项都补了自测（N54/N57 用**桩掉 `http_get`** 的离线用例，含「API 返回错误体时不得伪造 sha」），
分类器自测 29 → **43 项**。

### 4.61.4 N58 `toolchain_drift` 的正则过宽 → 命中**成功行 / 路径名 / apt 行**

```
旧: r"ninja: not found|ninja-build|command not found|…|unsupported option|-Werror"
```
✅ 实测三个假阳性来源（都取自真实日志）：

| 命中的行 | 它其实是什么 |
|---|---|
| `checking if the -Werror option is usable... **yes**` | autotools 的**成功探针**（几乎所有 autotools 项目都打这行） |
| `-- Installing: /usr/mkspecs/features/**unsupported**/testserver.prf` | Qt 的**目录名** |
| `apt-get install -y **ninja-build** cmake` | **apt 安装行**（pcapplusplus 就是这么被误判的） |

收紧为 `error:.*-Werror`（要求出现在真错误行里），删掉裸 `ninja-build`。
另**新增一类 `era_dep_drift`**（镜像里烘死的依赖与要建的 era 不匹配；镜像固定 → 项目级确定性 → 计入早停）。

用新分类器复判历史 9 条 `toolchain_drift`（**按流水线口径**：`classify_build_failure` 优先用
era 重试**之前**的首试段，N28③）：

```
kimageformats ×3 → era_dep_drift        （真因：No Qt6 qtpaths executable found）
libspng       ×1 → dead_external_url    （与它当初被淘汰的原因一致）
pcapplusplus  ×1 → buildscript_mismatch （原先是被 apt 行里的 ninja-build 误判的）
opensc        ×3 → compile_error        （首试段真因 configure: error: OpenPACE linkage required）
libredwg      ×1 → toolchain_drift      （不变，真错误 command not found）
```
⚠ **五类全在 `DETERMINISTIC_FAIL` 里 → 早停行为完全一致**，改的只是**记的原因对不对**。
自测里因此断言「**行为不变**」而非断言某个标签（第一版我断言了标签，被真实日志证伪）。

### 4.61.5 两个项目带证据淘汰

* **radare2（池 54）**：预检 100%、0 外链，但 4 次构建全挂。真因不是「工具链漂移」这个泛标签，而是
  ```
  /out/r2-static/usr/include/libr/sdb/sdbht.h:15:9: error:
    cannot initialize return object of type 'char *' with an lvalue of type 'void *const'
  ```
  **C 头文件被当 C++ 编译**（`void*`→`char*` 隐式转换在 C 合法、C++ 不合法）→ 2018 年的头过不了今天的 clang。
* **kimageformats（池 28）**：真因是 `CMake Error at /usr/local/share/ECM/modules/ECMQueryQt.cmake:84:
  **No Qt6 qtpaths executable found**`。Dockerfile 是 `git clone --depth 1 -b **master**` 后跑上游的
  `prepare_build.sh` → 镜像里烘的是**当前（2026）的 ECM/Qt**，而我们要建 2021 年的 commit。
  **era-retry 救不了**：那个 prepare 脚本来自 master、**根本没被钉版**。
* **matio（池 52）**：离线预检 **0/14**（`fixed~1` 解析不出）→ 没花镜像钱就淘汰。
* **ghostscript（池 192）**：unshallow ≈29 KB/s → ⛔（见 4.61.1）。

### 4.61.6 ⭐ unicorn 打通：**第 10 个项目**，并**破了 UBSAN 长期 0 正样本**的缺口

repo 仅 21MB、0 第三方外链、`base-builder:ubuntu-24-04`。**分层探针**（刻意按 sanitizer 各取 1 条，
而不是随机 —— 就是为了撞 UBSAN）：

```
OSV-2020-1123  undefined  fuzz_emu_arm_thumb   index-out-of-bounds      → 复现
OSV-2020-1373  memory     fuzz_emu_arm_thumb   segv-on-unknown-address  → 复现
OSV-2020-1029  address    fuzz_emu_mips_32be   heap-buffer-overflow     → 复现 **strict**
探针 3/3；7 次构建 / 42.3min
```

### 4.61.7 N59 crash_type 归一化两处缺陷（零构建成本，2 条升档）

| | 缺陷 | 实测 | 修法 |
|---|---|---|---|
| ① | **十六进制地址被当成类型的一部分** | `OSV-2020-1373` 期望 `segv-on-unknown-address`，实测 `segv-on-unknown-address-**0x7f64aa200470**` → `crash_type_match=False` → 压在 loose。ASan 那条路是**硬编码** `"Segv on unknown address"`（不含地址）所以没这问题；**MSan** 的 `MSAN_ERR_RE` 捕获到 `(` 之前，把地址带进来了 | 在**共享**的 `normalize_crash_type` 里剥 ` 0x[0-9a-f]+` 及其后（两侧对称；地址是运行时值，不是类型） |
| ② | **UBSan 具体检查名被压成泛化** | `OSV-2020-1123` 期望 `Index-out-of-bounds`，实测一律 `Undefined-behavior` → UBSAN 条目**结构性地**拿不到 medium+。而报告原文里具体信息是有的：`runtime error: **index 16 out of bounds for type** 'TCGv_i32[16]'` | observed 侧加 `UBSAN_CHECK_MAP`（**只收已实测对上的形态**，未命中仍退回泛化值 → 宁可不升档，不可靠猜升档） |

✅ 已知答案 6/6（含 4 个回归：`READ 1` / `WRITE {*}` / 普通类型 / expected 侧原样）；
**全复现记录表 expected 侧归一化 0 行变化** → 改动安全。重跑 ④⑤ 后 **2 条 loose → medium**；
另 2 条仍 loose，因为它们期望值本身就是 `unknown`（ClusterFuzz 没分类）—— 那是**判据设计问题**
（全复现记录表 17 条属此类），**未擅自改**，见 §5 item 58。

### 4.61.8 N60 审计的盲区：自己回收了就免检

`OSV-2023-1322` 的归档被回收后，交付条目只剩一个 `PRUNED.txt`，而审计报「**0 条红线违反**」。两个洞：

1. `build_index` 对已回收条目在写 `INFO.txt` **之前就 `continue`**，而审计 `[4c]` 是靠**找 INFO.txt**
   枚举条目的 → **PRUNED 条目对审计完全不可见**；
2. `dang_ver` 带 `not binary_pruned` 豁免 → 等于「**自己回收了就免检**」。

修：PRUNED 条目也写 `INFO.txt`（首行就是 `⚠ 本条不可重放`）；新增两条红线 ——
**交付条目数必须 == verified 行数**、**verified 行不得处于「已回收且不在盘」态**（purge 默认已关，§4.55）。

### 4.61.9 ⚠ 必须给「bit 级可重建」的结论**加限定**

重建 `OSV-2023-1322` 的归档后逐字节校验：**5/5 个可执行文件 sha256 全部不符**。

```
❌ avc_dec_fuzzer  期望 e7f311fb5340… 实得 bf56168b0bdd…
❌ svc_dec_fuzzer  期望 11bc20933a7d… 实得 52e384acb57b…   （另 3 个同样不符）
```

而 §4.55 那次「**498 文件 sha256 全一致**」的样本是 **c-blosc2 / hunspell / pcre2 / md4c**，
**libavc 不在其列**。→ §0.3「可 bit 级重建」的结论**只对已实测的这 4 个项目成立**，
不能外推到 libavc。🅗 未查明原因（可能是构建路径/时间戳嵌入，或原始记录本身来自
N45 修复前那次「`binary_dir` 与 `sha256` 张冠李戴」的落账）。

⚠ 但**功能上没坏**：重建件实测 **7 次里崩 6 次（86%）**，`replay.sh` 判决命中 sanitizer 报告
→ 该条仍可重放，只是**不能声称 bit 一致**。已如实写入 `replay_verification.json`。

### 4.61.10 磁盘：回收了 5.0G，但仍然紧

```
清 oss-fuzz-repro/build/{out,work}（构建中间产物，归档早已拷走）  → +3.6G
清 4 个悬空 docker 镜像（era 重建后被取代的旧项目镜像）+ 停止的容器 → +1.4G
现况：归档 **8.5G** · 可用 **4.1G**
```
⚠ unicorn 探针期间磁盘一度掉到 **2.7G**（era 机制会为每个 era commit 建一个 ~2.4G 镜像，
旧 tag 变悬空）。**再跑大池之前必须先定分级保留策略**（§5 item 44/59），否则会写满。

### 4.61.11 累积状态

```
复现记录表 411 行 / 243 唯一 / 39 run          复现 **154/243 = 63.4%**
tier: **strict 87** · medium **36** · loose 31 · none 89
按项目（**10 个**）: c-blosc2 61 · libavc 32 · hunspell 24 · pcre2 10 · libhevc 10 · libtsm 7 ·
                    md4c 3 · libwebp 3 · **unicorn 3** · libspng 1
按 sanitizer: address 135 · memory 18 · **undefined 1**（← 长期为 0 的缺口**已破**）
交付视图 **154 条目 · 每条恰好 1 个 ELF · 全部实测可重放**（首轮 148 · flaky 3 条已在 INFO.txt 标注）
审计 **0 条红线**（含 N48 的 3 条 + N53 的 3 条 + N60 的 2 条）；自测 **18 套 324 项 / 0 失败**
约束：主树 550 ✅ worktree dirty=0@07522dc0e ✅ infra md5 未变 ✅ dc 0 ✅ Dockerfile/build.sh 改动 0 ✅ 根目录仅 DELIVERY.md ✅
```

**新项目累计：13 试 4 中** —— 新增淘汰 radare2（C 头当 C++ 编）· kimageformats（镜像烘当前 Qt/ECM vs 2021 commit）·
matio（解析不出 `fixed~1`）· ghostscript（unshallow 29 KB/s）；新增可用 **unicorn（3/3 探针）**。

## 4.62 W5 第十八轮：磁盘分级保留策略（N61）—— 先量清字节去向，发现「按 tier 分级」被「按复用价值分级」**全面压制**

### 4.62.1 用户批准的方向，与一个必须先纠正的直觉

用户选定「**自动回收 + tier 分级**」。但动手前先量归档的字节去向，发现一个反直觉的事实：

```
归档 8.5 GB 的构成：
  ① 交付必需（verified 行的最小重放包）   1.50 GB   147 文件
  ② 兄弟 target / 多余数据文件            7.49 GB   1,524 文件
  ③ 无任何 verified 行引用的整目录         0.29 GB   7 目录
```

**关键**：交付视图（`by_crash_type`）是用**硬链接**指进归档的（§4.59.3，为了「0 额外空间」）。
所以「删归档路径」对那 1.50 GB **根本不会释放空间** —— inode 引用计数 >1，数据还在。
✅ 实测 `st_nlink` 分布证实：`{1: 1433, 2: 124, 3: 12, …, 22: 21, 106: 105}`
（`nlink=106` 那 105 个是跨归档去重的 `llvm-symbolizer`）。

→ **策略不该是「删旧归档」，而是「把归档瘦身到交付所需的并集」**。这也说明
§4.55 把 purge 默认关掉是对的：交付依赖归档，删归档目录这个动作本身对交付无益、对空间也无益。

### 4.62.2 ⭐ 「按 tier 分级」被实测**全面压制**，改用「按复用价值分级」

用户要的是 tier 分级，但我把三种保护规则都量了一遍（**先测再选，不凭直觉**）：

| 保护规则 | 受保护的兄弟文件 | **可回收** |
|---|---|---|
| `tier=strict,medium,loose`（等于不瘦身） | 7.49 GB | 298 MB |
| `tier=strict,medium` | 6.63 GB | 1.15 GB |
| `tier=strict` | 3.39 GB | 4.38 GB |
| **`reuse`：只保护「服务 >1 条 verified 行」的归档** | **698 MB** | **7.09 GB** |
| `none`（全瘦身） | 0 | 7.78 GB |

**为什么 tier 分级不管用**：tier 与「这个归档会不会被复用」**不相关** —— 一条 strict 也常常
**独占**一个归档。✅ 实测：119 个被引用的归档里，**100 个只服务 1 条** verified 行
（它们的兄弟文件共 **6.80 GB**，复用价值≈0），只有 **19 个服务 >1 条**（覆盖 54 条，
兄弟文件 **698 MB**，才是真有复用价值的）。

→ `reuse` 用 **698 MB** 的代价换回 **7.09 GB**，比最好的 tier 方案（4.38 GB）多回收 62%，
且**保住的正是有用的那部分**。故 `reuse` 设为默认，`tier`/`none` 保留为开关。

### 4.62.3 两类动作、两种门控（不能一刀切）

```
纯废物 → **无条件**清（与磁盘水位无关）：
  --clean-build    oss-fuzz-repro/build/{out,work}   构建中间产物，归档早已拷走  ✅ 实测 1.27 GB
  --prune-images   悬空 docker 镜像（era 重建后被取代的旧项目镜像）+ 已停止容器  ✅ 实测 250 MB
动归档 → **只在低于阈值时**才动（有重建成本）：
  --prune-orphans  / --prune-siblings     受 --min-free-gb 门控（默认 3.0）
```

⚠ **代价与可逆性如实写明**：`--prune-siblings` 删的是「同一 commit 的**其它** fuzz target」。
若将来有新 crash 钉到同一 commit 却要另一个 target，② 会重建它（一次构建的成本）。
而 **libavc 的重建不是 bit 级一致**（§4.61.9：5/5 文件 sha256 不符）→ 重建件的 `binary_sha256`
会与复现记录表原值不同（功能可用，实测 7 次崩 6 次）。故本策略**只删未被任何交付条目引用的文件**，
交付必需的那份**永远不动**。

**事后强制自校验**（`--apply` 时跑，任一不符即退出码 3、不静默）：
交付条目数不变 · 每条仍**恰好 1 个 ELF** · 四件齐全 · 断链 0 · 审计 0 红线。

### 4.62.4 执行结果与接线

```
执行前 可用 3.0 GB（归档 8.5 GB）
  ✅ 清 build/out 1.16 GB + build/work 107 MB
  ✅ 删孤儿归档目录 7 个（298 MB）
  ✅ 删兄弟文件 1,392 个（6.80 GB）
  ✅ docker 悬空镜像 249.7 MB
执行后 可用 **13 GB**；归档 8.5 GB → **2.2 GB**
  ✅ 交付自校验：154 个条目、每条恰好 1 个 ELF、四件齐全、断链 0
  ✅ 审计 0 条红线
```

已接进流水线（用户批准的「每轮结束自动清」）：`run_repro.py` 新增
`--post-clean`（**默认开**）/ `--post-clean-free-gb`（默认 **6.0**）→ 每轮汇总后自动调
`disk_policy.py`，纯废物无条件清、归档瘦身低于 6 GB 才动。

### 4.62.5 顺带量出：unicorn 整池**跑不起**，必须分批

```
单个 unicorn 归档 = 104～124 MB（`fuzz_emu_*` 单个二进制就 **108 MB**，因为内嵌 QEMU）
一次构建会产出**全部** `fuzz_emu_*` 变体 → 探针 3 条就产生 **3.8 GB**
整池剩 30 条 × 实测 ~2.3 构建/条 × ~540 MB/构建 ≈ **37 GB** ≫ 可用 13 GB
```
→ **不能一次跑整池**（轮中就会写满；`--post-clean` 只在**轮末**触发）。
本轮改为**定向小批**：只取剩下的 UBSAN + MSAN（`--sanitizers undefined,memory --limit 6`，
池里剩 25 address / 4 memory / **1 undefined**）—— 既控磁盘，又正好补**最缺的 sanitizer 覆盖**
（UBSAN 目前仅 1 条、MSAN 18 条）。

### 4.62.6 「期望值 unknown」的判据：**保持现状**（用户裁定）

✅ 实测全复现记录表 **17 条** verified 的 `crash_type_expected` 本身就是 `unknown`
（ClusterFuzz 当年没分类）→ `crash_type_match` **永远为假** → 结构性地拿不到 medium/strict，
哪怕帧完全对齐（`OSV-2020-1016` 就是 `score_subseq=1.0` 却停在 loose）。

可选的放宽是「把期望 unknown 视作**类型不可判**、改按帧单独定档」（与「recovered 0 帧」同法）。
**用户裁定：保持现状**（保守：类型对不上就不给 medium+）。→ 本轮**只记录不改判据**，
并在 §5 item 58 写明这是**已知的 tier 下限折损**，读复现率/tier 分布时须带这个前提。

### 4.62.7 累积状态

```
复现记录表 411 行 / 243 唯一 / 39 run（+ 本轮 unicorn UBSAN/MSAN 定向批）
复现 **154/243 = 63.4%**；tier strict **87** · medium **36** · loose 31 · none 89
项目 **10 个**；sanitizer address 135 · memory 18 · **undefined 1**
交付 **154 条目 · 每条恰好 1 个 ELF · 全部实测可重放**；断链 0
审计 **0 红线**（8 条红线全带牙齿测试）；自测 18 套 **324 项** / 0 失败
磁盘：归档 8.5 GB → **2.2 GB**，可用 3.0 GB → **13 GB**
```

## 4.63 W5 第十九轮：轮中水位线（N62）→ 误删在飞归档（N63）→ **磁盘写满事故**（N64），以及两道新自测各抓到一个真 bug

本轮是「加一个安全机制、结果暴露出两个更深的坑」的完整链条，**每一步都有实测数字**。

### 4.63.1 N62 轮中水位线：确实需要，也确实生效

§5 item 63 提过：`--post-clean` 只在**轮末**触发，而 unicorn 这种项目轮中就会写满。
本轮先把它实现出来：`run_repro.py` 每处理一条 crash 前查一次水位，低于
`--mid-clean-free-gb`（默认 5.0）就即时调 `disk_policy.py`（**复用其全套安全检查，不另写删除逻辑**）。

✅ 实测有效：`w5-unicorn-b2`（12 条 / 21 次构建 / 96.9min）期间水位线**触发 3 次**，
可用空间在 **6.7 GB ↔ 12 GB** 之间震荡而没有触底；该批产出 **7 条复现**（1 strict + 6 loose）。

### 4.63.2 N63（🔴）轮中清理**删掉了本轮在飞的归档**

`disk_policy` 的 `needed_map()` 是从**复现记录表的 verified 行**算「哪些文件交付必需」的。
而轮中清理发生时，**本轮那些已构建、还没落账的行根本不在复现记录表里** → 它们的归档被判成
「无任何 verified 行引用的**孤儿目录**」→ **整目录删掉**。

✅ 实测事故（`w5-unicorn-b2`）：轮中触发 3 次清理，**4 条刚复现的 crash**
（`OSV-2020-1409`/`-1945`/`-2180`/`-231`）的归档被删，⑤ 落账时只能标 `binary_pruned=True`
→ 审计 **3 条红线**（`[N53] ELF 个数 ≠ 1` 4 个条目、`[N53] 缺件` 12 处、`[N60] 已回收且不在盘` 4 条）。

量化：本轮 21 次构建涉及 **15 个归档，其中 14 个已被删掉**。

**修**：`disk_policy.py` 新增 `--protect-since <epoch>` —— 读 `build_records.jsonl`，
把 `ts >= 本轮起始时刻` 的 `binary_dir` **整目录保护**（此时还不知道最终会用哪个 target，
故连兄弟文件也不删；等它落账成 verified 行后，**下一轮**清理自然按 `need` 精确瘦身）。
`run_repro.py` 的轮中清理必传该参数。

⚠ 接线时我自己先踩了一个坑：把 `t_start` 写成了 `a._t_start`（args 上并没有这个属性）。
更早还**在模块顶部新写了一份 `free_gb()`**，而文件里第 132 行本来就有一份 —— Python
**后定义者胜**，我那份带 `except OSError` 容错的被**静默覆盖**，直到拿
`free_gb('/nonexistent')` 去测、看它抛 `FileNotFoundError` 才发现。

### 4.63.3 N64（🔴）**磁盘写满事故**：保护机制本身把盘占住了

修完 N63 重跑那 4 条，结果**更糟**：

```
13:01 磁盘 4.3G   13:08 磁盘 2.1G（水位线已触发 2 次）
13:15 磁盘 **96K**  13:22 起 **68K**（= 100% 满）→ 进程僵死，连 shell 输出都写不出来
```

原因：水位线触发了、N63 也确实保护住了在飞归档（日志：`保护本轮在飞归档：6 个 / **7.29 GB**`），
**但「保护 7.29 GB」与「继续构建」在 unicorn 这种单归档 100 MB+ 的项目上是直接冲突的** ——
光靠水位线不够，保护集合本身就能把盘占满。

**修**：加**硬底线安全阀** `--disk-hard-floor-gb`（默认 **2.5**）—— 轮中回收**之后**仍低于底线，
就抛 `RuntimeError` 让本轮**优雅停止**（与 gate 中止同一处置：已完成的记录已落盘，
续跑减小 `--limit` 即可），而不是继续构建到写满。

**事故恢复**（按成本从低到高）：

```
① 杀进程 + 强删活动容器 + rm -rf build/{out,work}   → 回收 1.27 GB（68K → 1.2G）
② docker image/container prune                       → 0 B（已无可回收）
③ disk_policy --force --apply                        → 回收 **8.01 GB**（全是 unicorn：
                                                        孤儿目录 5 个 5.78G + 兄弟文件 2.23G）
   结果：可用 2.0 GB → **9.2 GB**；归档 13 GB → **5.0 GB**
   ✅ 交付索引重建 162 条全部自包含可重放、0 已回收、0 driver 缺失
   ✅ 交付自校验通过（162 条目、每条恰好 1 个 ELF、四件齐全、断链 0）
   ✅ 审计 **0 条红线**
```

⚠ 顺带纠正我自己的一次测量错误：查「今天的构建记录」时把阈值硬编码成 `2026-09-18 10:45`，
而当天其实是 **09-17** → 查出 0 条，一度误判成「build_records 没写」。
**用 `date` 核对后才对上**（21 条记录、15 个归档、14 个已删）。

### 4.63.4 两道新自测，各抓到一个真 bug

把本轮两类「Python 不报错、只静默生效」的缺陷固化成第 19 套自测
`preflight/selftest/w5_selftest_static_consistency.py`：

| 检查 | 抓什么 | 结果 |
|---|---|---|
| ① 重复的顶层函数/类定义 | **后定义者静默覆盖前者**（本轮 `free_gb` 事故） | ✅ 43 个文件 0 处 |
| ② 重复的模块级常量赋值 | 同名单调覆盖 | ✅ 0 处 |
| ③ `except` 引用未定义/未导入的异常名 | 拼错异常类 → 运行时才 NameError | ✅ 0 处 |
| ④ 已知答案 | 合成 `free_gb ×2` 必须被检出 | ✅ 检出 |
| ④b **真的去跑每个脚本的 `--help`** | argparse 会对 help 串做 `%` 格式化 | ⚠ **抓到 2 个** |

④b 当场抓到两个 `--help` 崩溃：

1. **我自己刚写的**：`--disk-hard-floor-gb` 的 help 里有「100% 满」→
   `ValueError: unsupported format character '?' (0x6ee1)` → 改成 `100%%`。
2. **W3 就存在、潜伏至今的**：`manifest_builder.py --sort` 的 help 里有
   「复现率 **45.7% vs HEAD 6.7%**」→ `unsupported format character 'v' (0x76) at index 175`
   → **整个 `--help` 崩掉**。它一直没暴露，是因为**从来没人跑过它的 `--help`**。
   → 已修为 `45.7%%` / `6.7%%`。

⚠ 这类缺陷 `ast.parse` 查不出、`import` 也不报，**只有真去渲染 help 才炸** →
所以 ④b 是**直接 subprocess 跑**，而不是静态猜（22 个脚本全部覆盖）。

### 4.63.5 累积状态

```
复现记录表 424 行 / 253 唯一 / 41 run          复现 **162/253 = 64.0%**
tier: strict **87** · medium **36** · loose **39** · none 91
按项目（**10 个**）: c-blosc2 61 · libavc 32 · hunspell 24 · **unicorn 11** · pcre2 10 ·
                    libhevc 10 · libtsm 7 · md4c 3 · libwebp 3 · libspng 1
按 sanitizer: address **141** · memory **20** · undefined 1
交付 **162 条目 · 每条恰好 1 个 ELF** · 断链 0 · 全部可重放
审计 **0 条红线**；自测 **19 套 351 项 / 0 失败**
磁盘：可用 **9.2 GB**（事故谷底 68 KB）· 归档 **5.0 GB**
```

**unicorn 的磁盘经济学（决定后续批次大小）**：单个 `fuzz_emu_*` 二进制 **108 MB**（内嵌 QEMU），
一次构建产出**全部**变体 → **~540 MB/构建**；每条 crash 实测 ~2.6 构建 → **~1.4 GB/条**。
池 33 条已做 11 条、剩 ~22 条 → 一次全跑要 **~31 GB**，**必须分批 ≤6 条**，
且依赖 N62 水位线 + N64 硬底线双闸。

## 4.64 W5 第二十轮（W8）：**年份≠可构建**（ntopng 反例）、**N71 预检 `$SRC/<repo>/` 前缀假阴性**、Docker 镜像/卷回收 **590 MB → 13 GB**

### 4.64.1 选目标规律：崩溃年份 vs 复现率（实测标定）

按 OSV 年份分组统计**已试目标**的复现率：

| 崩溃年份 | 复现率 | 说明 |
|---|---|---|
| ≤ 2020 | **37%** | 老 crash 的根因多是 `era_dep_drift`（取不到 era base 镜像） |
| ≥ 2022 | **76.7%** | |
| 2023 | **85.2%** | hdf5 / jq 池全是 OSV-2023-*，本轮高产的原因 |

→ 这条规律解释了 curl / wolfssl / libarchive 全灭（池全是 `OSV-2020-*`），
也指导了本轮改按年份挑目标。

### 4.64.2 ⚠ 但**年份新 ≠ 能构建**：ntopng 反例

ntopng 池 **20/20 = 100% 是 2022+**（18 条 2023），是年份维度上的最优候选。
实跑 8 个最新目标 → **0 复现**：

```
失败分类：era_dep_drift 1 · network_fetch 1 · **compile_error 5**
manifest 8 条 → observation 2 条 → 复现 0 条
```

`compile_error` 在「不改 build.sh」的约束下是**终局**（无法通过 era 自愈或 walk-back 绕过）。
→ **结论修正**：年份只是**必要条件之一**，还必须叠加「build.sh 能在当前依赖下编译通过」。
预筛应把 `compile_error` 史作为一票否决项，而不只看年份。

另：**arrow 池 58 条里只有 6 条（10%）是 2022+**（47 条是 2020）→ 按本轮标定应放弃。

### 4.64.3 N71（🔴）预检形态① **未剥 `$SRC/<repo>/` 前缀** → 假阴性挡死整个 icu 钉版池

**症状**：`w8ai2` 批 12 个目标里 6 条被判 `buildscript_mismatch`、**实际构建 0 次**：

```
[预检] icu@906093f31b44：候选 1 个路径，存在 0、缺失 1 → ['icu/icu4c/source/test/fuzzer/locale_util.cpp']
⛔ 预检判定 buildscript_mismatch：build.sh 引用但 commit 树里没有
```

**根因**：`CAND_RE` 的负向断言 `(?<![\w$~])` 让匹配**从 `$SRC/` 之后的第一段开始**，
于是把**仓库目录名也算进了路径**；而 git 树里没有这一层 → 必然 404。
形态②（`SCRIPT_RE`）**早就剥了**这个前缀，形态①（`CAND_RE`）**漏了**：

```python
# 形态②（原有，正确）           # 形态①（修复前，缺失）
t = _norm_cand(m.group(1))       t = _norm_cand(m.group(1))
if prefix and t.startswith(prefix + "/"):      # ← 这三行原来只在形态② 有
    t = t[len(prefix) + 1:]                    #
cands.add(t)                     cands.add(t)  # ← 直接入集，带着 icu/ 前缀
```

**证据（假阴性确认）**：GitHub contents API 查 `906093f31b44` 与 `7cec4a9308b0` 两棵树，
`icu4c/source/test/fuzzer/locale_util.cpp` **都存在** → 预检误判。

**为什么之前没暴露**：探测批里 icu 那条走的是 **Stage1(HEAD)**、不做预检，所以看着"能建"，
掩盖了 Stage2(钉版) 全被误杀的事实。**与 N36(submodule)、N65(构建产物)、N68(跨仓库 cd) 同族**：
都是「查不到 ≠ 查过没有」→ 应记 undecidable 并放行。

**修复**：形态① 补上同样的前缀剥离（`build_orchestrator.py:1315` 起）。

**验证**：

| 用例 | 修复前 | 修复后 |
|---|---|---|
| `icu@906093f31b44` + `repo_path=/src/icu` | ok=False，missing 1 | **ok=True，存在 1、缺失 0 → 放行** ✅ |
| `icu@7cec4a9308b0` + `repo_path=/src/icu` | ok=False，missing 1 | **ok=True，存在 1、缺失 0 → 放行** ✅ |
| **负对照** `repo_path=/src/noticu`（basename 不符） | — | **ok=False，仍报 missing** ✅（证明剥离由 `repo_path` 精确驱动，不是无条件砍第一段） |

固化进 `w5_precheck_known_answers.py` 新增 **[D]** 段（3 项，含负对照）。
**回归**：16 套自测按**退出码**判定 **16/16 通过、310 项**；审计 **0 红线**。

> ⚠ 判据教训：第一次用「输出里含『全部通过』」当通过判据，把 3 套**实际通过**的
> 自测误报成失败（它们的措辞是「两道防御全部按预期拦住」「审计有牙」）。
> **改用退出码后 16/16**。文本匹配做判据不可靠。

### 4.64.4 磁盘真凶是 Docker，不是归档：**590 MB → 13 GB**

N62/N63/N64 三道闸都在管 `artifacts/binaries`（8.6 GB，其中 3.09 GB 是「交付必需·永不删」、
4.04 GB 是「兄弟文件·受保护」）→ 分级保留算出**可回收 0 MB**，闸门再怎么调也放不出空间。
真正的占用在别处：

```
docker system df（回收前）
  Images          20 个   ACTIVE 2   16.26 GB   可回收 15.58 GB (95%)
  Local Volumes    7 个   ACTIVE 1    2.742 GB  可回收  2.74 GB (99%)
```

**回收前先验证重放依赖**（用户明确要求不得破坏重放）：

```
$ grep -hoE "gcr.io/oss-fuzz-base/[a-z-]+:[a-z0-9.-]+" $(find artifacts/by_crash_type -name replay.sh)
    221 gcr.io/oss-fuzz-base/base-runner:ubuntu-24-04      ← 221 条**全部**只用这一个 tag
```

→ **`docker image prune -a` 会连它一起删掉、废掉全部 221 条重放**。故改为**按名单精确删**：

* **删**：10 个项目镜像（assimp / icu / curl / wolfmqtt / ntopng / jq / hdf5 / espeak-ng / unicorn / `<none>`）
  \+ 4 个闲置 base 变体（base-builder-rust / base-builder:xenial / base-clang / base-runner-debug）
* **保留**：`base-runner:ubuntu-24-04`（重放必需）、`base-runner:latest`、`base-builder:latest`、
  `base-builder:ubuntu-24-04`、`base-image:latest`、`neo4j:5`（M9 的 Joern CPG 查询需要）
* 卷：`docker volume prune -f` 只删**无容器引用**的 6 个（含一个 1.7 G）；neo4j 那个有引用 → 自动跳过

**结果**：

```
磁盘      590 MB → 11 GB（镜像）→ 13 GB（卷）        释放 13.1 GB
Docker    Images 6 个 / 7.48 GB · Containers 1(neo4j, Up 5 days) · Volumes 1 / 1.68 MB
重放抽验  ✅ 剪枝后仍复现成功（退出码 1，ASan global-buffer-overflow 报告在）
worktree  ✅ 干净（gate 四条件全过，HEAD=07522dc0e）
```

> ⚠ 停机姿势：用 **SIGTERM** 而非 `kill -9`（N70 的教训是 `-9` 会污染 worktree）。
> 停止瞬间 `git status` 曾显示 `projects/assimp/{Dockerfile,build.sh,project.yaml}` 三个 `M`，
> 但 `git diff --cached` **为空** → 只是 index 的 stat 过期；`git update-index --refresh` 后
> **改动行数 0**，内容从未被改（约束「不改 Dockerfile/build.sh」未被破坏）。

### 4.64.5 本轮复现增量与累积状态

新增 **assimp**（第 14 个项目）：`OSV-2025-580` / `undefined` / `assimp_fuzzer` / tier=**loose**。

```
复现记录表 221 条复现 / **14 个项目**
tier: strict **126** · medium **45** · loose **50**
按项目: c-blosc2 61 · libavc 32 · **hdf5 29** · hunspell 24 · **espeak-ng 17** · **unicorn 15** ·
        pcre2 10 · libhevc 10 · **jq 8** · libtsm 7 · md4c 3 · libwebp 3 · libspng 1 · **assimp 1**
按 sanitizer: address **190** · memory **21** · undefined **10**
按崩溃类型（16 种）: heap-buffer-overflow 111 · unknown 34 · uninit-value 14 · heap-UAF 13 ·
        stack-buffer-overflow 13 · global-buffer-overflow 11 · segv 6 · negative-size-param 4 ·
        memcpy-param-overlap 3 · heap-double-free 3 · stack-use-after-return 2 ·
        index-out-of-bounds 2 · stack-buffer-underflow 2 · invalid-free 1 · check-failed 1 · null-deref 1
最大单项目占比 61/221 = **27.6%**（较上轮 37% 下降 → 样本偏斜缓解）
交付 **221 条目 · 每条恰好 1 个 ELF · 四件齐全 · 断链 0 · 全部可重放**
审计 **0 条红线**；自测 **16 套 310 项 / 退出码 0**
磁盘：可用 **13 GB**（谷底 590 MB）
```

> ⓘ UBSAN 覆盖已不是缺口：`undefined` 正样本 **10 条**（先前记录的「1 条」是过期信息）。

## 4.65 W5 第二十一轮：**N73 我误删交付依赖**（`artifacts/logs`）→ 221 条 report.log 全丢 → 重生成恢复；顺带挖出 **N74 replay.sh 判决与复现记录表自相矛盾**

### 4.65.1 🔴 N73：我把「交付依赖」当成「历史日志」删了

磁盘到 98%（剩 2.5G），我做了全盘遍历并把候选分成三档给用户判断。其中
`artifacts/logs`（269M）被我描述为「历史构建日志；DELIVERY.md 有引用作证据」，
用户据此批准删除。**这个描述是错的** —— 它是**交付的运行时依赖**：

```
show_repro.py:191   REPRO_LOGS = artifacts/logs/reproduce
show_repro.py:294   shutil.rmtree(INDEX_DIR)          ← build_index 是**整目录重建**
show_repro.py:399   rep, rep_note = _select_report(r) ← 从 REPRO_LOGS 里挑那份冻结副本
show_repro.py:401   shutil.copy2(rep, .../report.log)
```

`_select_report()` 的两条取报告路径（轮转副本 `REPRO_LOGS/<OSV>*`、复现记录表 `raw_log_path`）
**都指向被删目录** → 返回 `(None, "⚠ 盘上没有该 OSV 的任何 report")` → `report.log` 不再复制。
而 `build_index` 先 `rmtree` 再重建 → **221 条 report.log 一次性全部静默消失**。

**是审计抓到的，不是我**：`w5_audit_delivery.py` 的 **[N53] 交付条目缺件** 红线报
「221 处 `('OSV-2016-5','report.log')…`」。→ **红线机制按设计生效**（这是它第 6 次拦下真问题）。

**不可从磁盘恢复**（逐项排查过）：

| 恢复途径 | 结果 |
|---|---|
| 复现记录表 `raw_log_path` | 221 条 **0 个还存在** |
| `replay_verification.json` | 只有 2 KB / 12 个键，是**汇总**不是逐条报告 |
| `obs_verify.jsonl` / `ver_verify.jsonl` | 无报告字段（只有 tier/dedup_token/frame 匹配等） |
| 全盘 `grep -rl "ERROR: AddressSanitizer"` | 命中的全是**二进制里编译进去的字符串**，不是报告文本 |
| `/root/gyx/backup` | 无副本 |

### 4.65.2 恢复方式：重放重生成（`recover_report_logs.py`）

**为什么重生成是可信的、不是伪造证据**：交付目录里的 ELF 是 `artifacts/binaries/<…>` 的
**硬链接（同一 inode、同一字节）**，testcase 也是复现记录表那一份 → `replay.sh` 跑出来的报告与
当初 `_select_report()` 挑中的「binary_dir 一致且 exit==1」那份**同源**。
写回 `artifacts/logs/reproduce/<OSV>.log`，并补齐 `_select_report()` 要解析的
`# binary_dir:` / `# exit:` 头（→ 今后任何一次 `build_index()` 都能自然选回，不会再丢），
另加 **`# provenance: regenerated-by-replay`** 头标明来源，**不冒充**原始冻结副本。

**[N73②] 首版只跑一次 → 误判 5 条失败。** 历史 `replay_verification.json` 早就记录了 flaky：

```
needed_retry:   {'OSV-2023-48': 3, 'OSV-2023-75': 3}
heavily_flaky:  {'OSV-2023-948': {attempts_extra: 8, crash_rate: '1/8 = 12%'}}
notes: flaky 集中在 libavc 的 ABRT/global-buffer-overflow 类（svc_enc_fuzzer）与 MSAN 条目
```

加 `--retries` 后逐轮收敛：

| 轮次 | 重试上限 | 结果 |
|---|---|---|
| 1 | 1 次 | 216 / 221 成功，5 条失败 |
| 2 | 10 次 | 再恢复 3 条（含 **tier=strict 的 OSV-2023-68**） |
| 3 | 30 次 | 再恢复 1 条（OSV-2023-948，与 12% 崩溃率相符） |
| 4 | 修 N74 后 3 次 | 再恢复 1 条（OSV-2024-1044） |
| **合计** | | **221 / 221** ✅ 用时 < 3 分钟 |

### 4.65.3 ⭐ N74（意外收获）：`replay.sh` 的判决**与复现记录表自相矛盾**

第 4 条 `OSV-2024-1044`（hdf5 / **undefined** 构建 / tier=loose / `crash_type=unknown`）
30 次重试全"不崩"。看输出才发现**它其实崩了**：

```
==7== ERROR: libFuzzer: deadly signal        exit_code = 77（与复现记录表记录**完全一致**）
SUMMARY: libFuzzer: deadly signal
NOTE: libFuzzer has rudimentary signal handlers.
      Combine libFuzzer with AddressSanitizer or similar for better crash reports.
栈: H5_term_library → exit → FuzzerDriver
```

这是 **UBSan 构建（不带 ASan）** 的死信号崩溃 → libFuzzer 只能用简陋信号处理器报
`deadly signal`，**不产生 sanitizer 报告**。而 `repro_common.py:74-76` **早就明文规定**：

> `deadly signal`（如裸 SEGV）**不排除** —— 那是真崩溃，只是没有 sanitizer 报告。

④ `verify_tiered` 就是按这条判出 tier=loose 的。但 `show_repro.py:443-445` 生成的
`replay.sh` HIT 正则**只有** `ERROR: (Address｜Memory｜Thread)Sanitizer`、`WARNING: MemorySanitizer`、
`SUMMARY: UndefinedBehaviorSanitizer`、`runtime error:` 四种 → **不认 deadly signal** →
交付出去的 `replay.sh` 对这条报「❌ 未复现」，**与复现记录表 tier=loose 直接矛盾**。

**修复**：HIT 正则补 `ERROR: libFuzzer: deadly signal | SUMMARY: libFuzzer: deadly signal`
（`show_repro.py` N74 注释处），并同步 `recover_report_logs.py` 的判据。

**验证**：

```
$ bash .../OSV-2024-1044/replay.sh ; echo $?
[verdict] ✅ 复现成功（容器退出码 77）：==7== ERROR: libFuzzer: deadly signal
1                                    ← 与复现记录表 exit_code=77 / tier=loose 一致
```

→ **影响面**：所有「崩溃形态是死信号而非 sanitizer 报告」的条目，主要是
**UBSan-only 构建（10 条 undefined）** 与裸 SEGV。此前它们的 `replay.sh` 一律误报"未复现"。

### 4.65.4 恢复后的完整验证

```
report.log 覆盖      221 / 221 条**非空** ✅
交付索引重建         221 个条目 → **自包含可重放 221** / driver 缺失 0 / 断链 0 ✅
审计                 ✅ **0 条红线**（2 条软性提示，均可解释）
OSV-2024-1044        ✅ replay.sh 判「复现成功」，与复现记录表一致
worktree             ✅ 干净（0 改动，HEAD=07522dc0e，分支 repro-patches）
磁盘                 2.5G → **7.2G**
```

**顺带产出**：这一轮等于做了一次**全量 221 条重放验证**（此前最近一次是 156 条时期）。

### 4.65.5 教训（两条，都要固化）

1. **「与本项目无关」/「历史日志」不是删除依据。** 同一轮里我还差点建议删
   `driver_create`（16G）—— 实测发现 **PID 21658 的另一个 opencode 会话正以它为 cwd、
   已运行 8 天、git 有 24 个未提交改动**，`coverage-union`（PID 3788357，2 小时）同理。
   → 删除判断必须查：**谁在用它**（`/proc/*/cwd`、`lsof`）、**最近改动时间**、
   **有没有代码引用**，而不是看它属不属于当前任务。
2. **删之前先问「谁是它的消费者」。** `artifacts/logs` 的消费者是 `show_repro.py`，
   而 `build_index` 的 `rmtree` + 重建语义让"源没了"变成"交付静默缺件"。
   若审计没有 N53 红线，这 221 处缺件**不会有任何报错**。

### 4.65.6 磁盘遍历结果（供后续参考）

| 分类 | 明细 | 处置 |
|---|---|---|
| ⛔ **别的会话在用的活跃工作区** | `driver_create` 16G（opencode PID 21658，8 天，24 未提交）· `coverage-union` 1.4G（PID 3788357）· `oss-fuzz` 3.1G（主树 491 未提交）· `fuzzslice-repro` 191M（今天有 commit） | **不动** |
| ⛔ **torch 依赖链** | `torch` 1.1G 被 `driver_create/source_code/libjxl/tools/benchmark/metrics/iqa.py` 引用；`nvidia` 2.7G + `triton` 690M 是它的运行时依赖（删了 `import torch` 会失败） | **不动** |
| ⚠ **同名陷阱** | `dist-packages/triton` 690M 是 **OpenAI 的 GPU 编译器**，**不是** Quarkslab 的污点引擎 Triton | 保留（torch 依赖），但**别误认成污点工具** |
| ✅ 已删 | `binaries/icu` 1.5G（icu 复现记录表 6 行**全 tier=none**、0 交付条目）· `/tmp/opencode/{_pk,_pk2,piptest,dftest}` 126M（我的测试残留）· `/tmp/opencode/m9` 476M（CPG 缓存，可 13s/项目重建）· `artifacts/logs` 269M（**误删，已重生成**） | — |
| ✅ 已删（docker） | 10 个项目镜像 + 4 个闲置 base 变体 + 6 个无引用卷 | 释放 **13.1G**；重放抽验通过 |

> ⚠ **`base-runner:latest`（1.6G）当时判为「全 /root/gyx 代码引用 0 处」可删，但我保留了** ——
> 因为别的会话可能 ad hoc 用它，这个查不出来。221 条 replay.sh 全部用 `ubuntu-24-04` tag。

### 4.65.7 N72：`git remote update` 无超时 → 整轮流水线死锁

w8ai4 批（assimp+icu，12 目标）跑到第 6 格时**卡死 33 分钟**：

```
PID 3881340  git remote update    ELAPSED 1975s   %CPU 0.0
  wchan:    do_wait          ← 在等一个已经不存在的子进程
  网络连接: 0 个              ← 根本没在传输
  fd:       3 个（2 pipe）
  cwd:      /tmp/tmp3u0ft8es/src/icu
```

`infra/build_specified_commit.py` 调 `git remote update` 拉 icu（超大仓库）时传输子进程
消失，git 仍 `do_wait`，**且这一步没有 timeout** → 单条 crash 能把整轮挂死。
`network_fetch` 的失败分类**只在进程返回后才生效**，挂住就永远不返回。

**处置**：SIGTERM 停整轮（**不用 `-9`**，N70 的教训是 `-9` 会污染 worktree）。
停后 worktree 复检 **0 改动**。该批 5 格产出 **0 条复现**，失败全是
`toolchain_drift`（在 `DETERMINISTIC_FAIL` 里 = 项目级确定性失败，walk-back 往更老只会更糟）
与 `timeout` → 继续跑无收益。**复现工作按用户指示在此暂停。**

> ⚠ 另一个操作教训：用 `pgrep -f "git remote update"` 找残留进程时，**我自己的命令行里
> 含这个字符串 → 自匹配 → `kill -TERM` 打到了自己的 shell**。应使用括号技巧
> （`[g]it remote upd`）或直接取 PID。

## 4.66 W6 第二十二轮：**N75 `--sort fixed_first` 语义反转** —— 默认值实际表现为 `no_fixed_first`，配 `--limit` 时系统性挑中**最差**的一批（预期产出损失 ≈7×）

### 4.66.1 怎么发现的

W6 要为「LLM 指令级模式抽取」设计补数据（见
`mutator_create/docs/specs/2026-09-30-llm-insn-pattern-mutator-design.md` §6 Phase 0）：
实测源数据集 3,790 条 / **334 个程序**，而已复现的 221 条只覆盖 **14 个程序 = 4.2%**；
主组 67 条崩溃有 **51 个独立簇 / 58 个不同出错点**（独立率 76–87%）
→ **瓶颈不是样本量、也不是独立性，而是程序种类只有 6–7 个**。
故要写一个分组轮转的后台驱动去攻新程序。

启动前逐组做 dry-run 校验 manifest 产出，发现异常：

```
$ python3 manifest_builder.py --projects matio,lcms --languages c,c++ \
      --sort fixed_first --no-regression --limit 6 ...
  → 6 条，其中**有 fixed_commit 的 0 条**
$ 同上但不加 --limit
  → 87 条，其中**有 fixed_commit 的 79 条**
```

`--sort fixed_first` 号称把「有修复提交」的排前面（这类走钉版，复现率 **45.7%**
vs HEAD **6.7%**），结果截断后取到的 6 条**一条都没有**修复提交。

### 4.66.2 根因（`manifest_builder.py` 的 `sort_key`）

```python
has = 0 if fixed else 1          # 有 fixed → 0；升序排 → 有 fixed 在前（本就是 fixed_first）
if args.sort == "fixed_first":
    has = 1 - has                # ← 反转 → 有 fixed 变 1；升序 → **有 fixed 排到队尾**
...
sel.sort(key=sort_key)           # 升序，无 reverse
if args.limit:
    sel = sel[:args.limit]       # 截断无条件执行
```

**`has = 1 - has` 把已经正确的顺序又翻了回去。** 原注释
`# no_fixed 排前（HEAD-first）` 对 `has = 0 if fixed else 1` 的描述本身也是错的
（升序下 0 在前 = **有 fixed 在前**）。

决定性对照（✅ W6 实测，`--projects matio,lcms --languages c,c++ --limit 6`）：

| `--sort` 取值 | 前 6 条有 fixed_commit | commit_source | 预期产出 |
|---|---|---|---|
| `fixed_first`（**默认**，修复前） | **0/6** | introducing 5, head 1 | 0.4 条 |
| `no_fixed_first`（修复前） | **6/6** | fixed_parent 6 | 2.7 条 |
| `osv_id` | 6/6 | fixed_parent 6 | 2.7 条 |

全量 87 条中 79 条有修复者被排到**第 9–87 位**，前 8 位全是无修复的。

### 4.66.3 影响

* `fixed_first` 是 `manifest_builder.py` 与 `run_repro.py` 的**默认值** →
  凡用默认 `--sort` 且带 `--limit` 的轮次，都在**系统性挑中最差的一批**。
* 按 45.7% / 6.7% 折算，`--limit 6` 的预期产出从 **2.7 条掉到 0.4 条（≈7×）**。
* 这与 **W5 `--sort` help 文本里记载的现象完全吻合**：
  「✅ 实测 92 条积压位于默认序第 **196–2996** 位，历轮 `--limit ≤30` → 三轮都没碰到」。
  W5 声称已「根因修正：默认由 no_fixed_first 改为 fixed_first」，
  **但那次修正只是把默认值字符串改了、并加了 `has = 1 - has`，
  在升序排序下等于没修（甚至把原本正确的方向翻错）**。
  → **N75 是 W5 那次修正未真正生效的延续。**

### 4.66.4 修复与验证

**修复**（`manifest_builder.py` `sort_key`，最小改动）：

```python
has = 0 if fixed else 1                    # 有 fixed → 0 → 升序在前
if args.sort == "no_fixed_first":
    has = 1 - has                          # 反转 → 无 fixed 在前（HEAD-first）
```

即**把反转条件从 `fixed_first` 改成 `no_fixed_first`**，使两个取值都名副其实。
未动排序方向、未动 `--limit` 逻辑、未动 `only` 门控（`--only-osv` 时保持不排序，
是既有语义，本次不涉及）。

**新增自测** `preflight/selftest/w6_selftest_sort_direction.py`（TDD：先 RED 后 GREEN）：

| 断言 | 修复前 | 修复后 |
|---|---|---|
| [B] `fixed_first --limit 6` 前 6 条全有修复 | ❌ 0/6 | ✅ 6/6 |
| [C] `no_fixed_first --limit 6` 前 6 条全无修复 | ❌ 6/6 | ✅ 0/6 |
| [A] 样本区分力（有修复 79 / 无 8，两类都在） | ✅ | ✅ |
| [D] 两方向产出序列不同（证明 sort 生效） | ✅ | ✅ |
| [E] 负对照：sort 只改顺序不改**集合**（87=87） | ✅ | ✅ |
| [F] 负对照：`osv_id` 也产出 6 条（证明 [B] 非恒真） | ✅ | ✅ |

**回归验证**：

```
$ cd preflight/selftest && for x in *.py; do python3 $x; done
  ✅ 17 通过 / ❌ 0 失败（16 套原有 + 1 套新增）
$ python3 preflight/selftest/w5_audit_delivery.py
  ✅ 审计通过：0 条红线违反；2 条软性提示（均可解释）
$ bash artifacts/by_crash_type/heap-buffer-overflow/hdf5/.../OSV-2023-806/replay.sh ; echo $?
  [verdict] ✅ 复现成功（容器退出码 1）：==7==ERROR: AddressSanitizer: heap-b…   1
$ bash artifacts/by_crash_type/heap-buffer-overflow/c-blosc2/.../OSV-2021-897/replay.sh ; echo $?
  [verdict] ✅ 复现成功（容器退出码 1）：==7==ERROR: AddressSanitizer: heap-b…   1
```

`w5_selftest_purge.py:165/187` 只断言 `--sort` 的**默认值字符串**为 `"fixed_first"`，
不涉排序行为 → 与本修复不冲突，且修复后该默认值终于名副其实。

### 4.66.5 教训（三条，都要固化）

1. **「改了默认值」≠「修好了行为」。** W5 把 `--sort` 默认值从 `no_fixed_first`
   改成 `fixed_first`、并加了反转，help 文本也写了理由和实测数字，
   但**没有任何自测断言过排序的实际方向**。
   → 凡 help 文本里写「✅ 实测 X 提升 Y」的开关，都应有对应自测**锁住行为**，
   而不只是锁住默认值字符串。
2. **排序 + 截断的组合必须有专门测试。** `sort` 单独看是对的、`limit` 单独看也是对的，
   bug 只存在于两者组合处。既有自测覆盖了 purge/overwrite/stopfrac/queue_order，
   却**没有一套覆盖 sort 方向**。
3. **写后台驱动前的 dry-run 校验救了这一轮。** 若不逐组验 manifest 产出、
   只看「命令跑通、退出码 0」，这个 7× 的产出损失会静默持续数天，
   且事后从复现记录表上看不出异常（每条记录都"正常"，只是挑错了对象）。
   → 与 N73（误删交付依赖）同族：**静默错误必须靠前置校验拦，不能靠事后审计**。

**复算**：`python3 preflight/selftest/w6_selftest_sort_direction.py`



# 5. 开放问题与风险

**P0 级（一次性阻塞）——✅ 两项均已关闭**
1. **独立 worktree 建树**：✅ P0 通过（三校验全过、主树仍 550）。
2. **代理透传**：✅ P0 解 `docker build`（path (ii)，落点 `common_utils.build_image_impl`）→ ⚠ P0-B 发现只覆盖 build、漏 `docker run`（N5）→ ✅ P0-C 补齐三调用点、两失败样本复验通过。**真正关闭。**

**P1（首轮后复评/标定）——✅ W2 已处理两项**
3. ~~`clusterfuzz==2.5.9` StackParser 是否必要~~ → **✅ W2 关闭：不必装**。observed 侧 137 帧实测：内部帧 57.7%（现成 `INTERNAL_PREFIXES` 剔得净）、无符号模块帧 **0%**、`.part.NN`/`.constprop.NN` **0**（两侧都 0 触发）、符号化失败 **0%** → StackParser 能多解决的问题**一个都没出现**。
4. ~~`T_strict` 阈值~~ → **⚠ W2 部分关闭，但结论是「阈值本身没意义」**：找到 7 条有区分力样本（libtsm，`ct_match=True ∧ subseq=0.0`），同时发现 **N13**——`score_subseq` 二值 → `T_strict∈(0,1]` 给完全相同的分级，**它压根不可证伪**。已加 `score_subseq_frac=LCS/|R|` 作真旋钮。**仍开放**：frac 的阈值位置（n=7、单项目、单 crash_type，需跨项目 ≥30 条）。

**保留观察（跑到了再看）**
5. gcloud 不可用 → era base-builder digest 自愈失效，钉老 commit 失败率升高。**✅ W2 实证**：flatbuffers 钉版 **0/4**，根因是**A2 工具链漂移**（老代码 `stl_emulation.h:386` 给 const 成员赋值，新 clang 拒绝）→ **projects/ 侧 era 自愈换不掉编译器**，此类项目钉版路径**整条归零**。ⓘ 未量化这类项目占比。
6. ~~**端到端可构建率 🅗 未量化**~~ → **✅ W2 首测：49/54 = 90.7%**（HEAD **33/33=100%**、钉版 **16/21=76.2%**）。⚠ 6 项目、选样非随机（偏向已有干净镜像者）→ **不可外推**到 249 项目；要外推需随机抽 20–30 项目，**磁盘是硬约束**（本轮结束剩 13G，每个新镜像 ~2.2GB）。
7. R13b 的 **229 条 repo 不一致档仍未触发实测**（ⓘ 待专门样本）。
8. flaky 重试 ≤3× 是否足够（MSAN/uninit 875 条）。
9. AFL/honggfuzz crash 经 libFuzzer 路径复现的等价性（868 条，🅗 首轮抽查）。
10. HEAD 复现率按 `commit_source` 分组 → **✅ W2 实测**：`fixed_parent`/`introducing` **118 条在 HEAD 复现 0 条**；`head` 组 libtsm **6/6 复现**——但 ⚠ **不可外推**：libtsm 上游 HEAD 冻结在 **2014-04-24**，早于这 7 条的报告年（2016–2021），HEAD 就是漏洞版。活项目的 `head` 组仍**未测**。
11. **W1 遗留**：~~11 条 `not_located` 的真实 `need`~~ → **⚠ W2 只拿到 1 条**（另 1 条被 `--max-builds` 挡掉），**还差约 19 条**才能判 B/C；`S≥2` 阈值标定（**N7/N9 给出两个新证据，建议连同「别家 ofz# 号」负信号一起重标定**）；`repo_path` 的 `candidates`（50 条）运行期 `git cat-file -e` 解析——**W2 未实现**（② 直接用 ① 的 `repo_path`，8 次钉版构建 0 次因此失败，故未触发）；qt 型嵌套 repo（11 条）钉版路径不可用（上游工具缺陷）。
14. ~~**W2 新增待办**~~ → **W3 处理情况**：✅ **N12** 已改 tier 感知（触发 14 次下探，但 **0 次**改善 tier → 新增 🅗 建议「`frac≥0.6` 即停」）；✅ **N17** 已加回退格（触发 9 次，无 crash 被丢弃）；✅ **N16** 已实现重试（**0 次触发**，未验证）；⚠ **N10** 镜像可自愈（74→0）但 harfbuzz 仍 **0/7** 失败（真屏障是 **N19**）；⚠ **MSAN** 已打通并首次复现，**UBSAN 仍零正样本**；✅ **N8** 已被配对实验**推翻**（i386 不是障碍）；⬜ **N14/N15** 未实现。
15. ~~**W3 新增待办**~~ → **W4 处理情况**：✅ **早停**已实现并生产触发 1 次（pcapplusplus，省至多 27 次构建）；✅ **N21 负对照**已改 HEAD 为默认（11/11 通过）；✅ **N20** 已加两道结构性防御（自测 12/12）+ 4 个被删归档**重建 20/20 逐字节一致**；✅ **N19** 已加构建前预检（harfbuzz 6/6、pcapplusplus 3/3、0 误报）；⬜ **N12 的 `frac≥0.6` 即停**未实现（W4 新增 1 例支持：OSV-2020-2184 三格全 loose 且 `frac` 全 1.0）；⬜ **N14/N15** 未实现。
16. **W4 新增待办**：①`not_located` 累积 **11 条**，要到 ≥30 才能给 A/C 定论（还差 ~20 条 ≈40–60 次钉版构建，且**必须挑可构建的项目**——harfbuzz/pcapplusplus/flatbuffers 都不行）；②**UBSAN 正样本仍为 0**（候选项目要么构建失败、要么数据自相矛盾；🅗 换 libvips/hdf5/kimageformats/draco，各需新镜像 ~2.2GB）；③**MSAN flaky 重试（≤3×）仍未触发**；④**预检覆盖率只 56/249 项目**（176 个 build.sh 提不出候选路径 → no-op；放宽候选已实测会误报，不可取）；⑤**N16 重试仍未验证**（W3/W4 都没遇到 `network_fetch`；重跑 c-blosc2@`9ba29ef1` 即可验）；⑥`introducing` 路的 commit 日期取不到 → 版本感知对照在 libtsm 上不可用；⑦磁盘 **8.3G**、归档 989MB（verified 变多→保留变多），要跑含新项目的轮次需 ≥8G。
17. ~~**W3 新增待办**（原编号，已被上面两条吸收）~~：①`not_located` 补到 ≥30 条以在 A(≈21)/C(23)/W3(28) 三种 walk-back 策略间定优劣（现 n=10，还差 ~20 条 ≈40–60 次钉版构建）；②**UBSAN 正样本**（换对象：libtsm 那条 `fixed==introducing==HEAD` 且 recovered 帧是描述文本，是坏测试对象）；③**MSAN flaky 重试路径**（≤3×）仍未触发；④**「同项目连续 N 次同类构建失败即跳过该项目」早停**（本轮 harfbuzz 白跑 19.5min / 6 次构建才确认 N19 是系统性的）；⑤**N19** 的 build.sh↔commit 错配无解（era 自愈已触发仍失败），除非允许改上游构建脚本（约束禁止）；⑥**N21** 负对照判据加**版本感知**（只用「漏洞窗口不含被测 commit」的其他 crash 作对照）；⑦**N20** 已修，但被删的 4 个 W2 verified 归档需重建才能再做已知答案回归（md4c 13.7s / hunspell 64.6s / pcre2 291.7s）；⑧磁盘 **9.5G** 仍是扩样硬约束（新项目镜像 ~2.2GB/个）。

18. ~~**W4 待办 ④（N12）与 W3 待办（N16）**~~ → **W5 处理情况**：✅ **N12** 已实现（纯函数 `stop_decision()` + `--stop-frac` + shadow 常开），**默认 OFF** 并**预注册翻转判据**（distinct-crash n≥10 且 tier 损失 0；现 n=3，**还差 7 条**）；✅ **N16** 重试机制已**离线注入验证 8/8**（含负对照）→ 账目从「代码路径从未执行」改为「机制 ✅ / 生产触发 ⓘ」，**「重跑 c-blosc2@`9ba29ef1` 即可验证」这条待办作废**（该 commit 现在能建成功、网络失败又是瞬态 → 重跑销不掉账）；✅ 新增 **N25/N26** 两道覆盖护栏（日志轮转 + manifest 拒写更弱产物）。
19. **W5 新增待办**：① **N12 翻转判据差 7 条不同 crash** —— 扩样本时 shadow 自动攒，**不得提前把默认改成 0.6**（一改就再也观察不到更深格、测量通道关闭）；② `not_located` 现 **14**、距 ≥30 还差 **16** 条 → 需要**新项目**（本地镜像池已榨干：可用仅 19 条且已跑完）；③ **MSAN flaky 重试**靠扩样本撞不上（151 条 `retry_count>0` 为 0）→ 要销账须**人工构造** flaky 场景；④ `build_error_detail` 抓的是泛泛的 `Building fuzzers failed.` 而非真根因行（404 那行）→ **按根因分组会失真**（N28③，未修）；⑤ 覆盖护栏只加了 ①/日志两处，`build_groups.json`·`repo_path_map.json`·`state.json` 仍无护栏；⑥ 筛选表里 7 个项目「无证据」（`no_candidate_paths` 或 `git://` 判不了）→ 想扩池得先补这两类判定能力；⑦ N25 之前被覆盖的日志**无法追回**（§4.5 对 N16 那条日志的引用永久失效）。
20. ~~**W5 待办 ①（N12 差 7 条）与「not_located 补样本」的路径**~~ → **W5 第二轮处理情况**：✅ **N12 判据已满足并翻转默认**（n=11、损失 0）；✅ **92 条积压已重跑 46 条**（chunk1+2），累积复现 **28→70**；⬜ 积压**还剩 46 条**（chunk3 = hunspell 20 + c-blosc2 3 正在跑；chunk4 = hunspell 3 + pcre2 7 + md4c 2 + libtsm 1 + flatbuffers 10）；⬜ `not_located` 仍 **13**（积压里全是 `located` → **这条账靠积压销不掉**，得去 2,801 条未采样池，即需要新镜像）；⬜ **N12 的跨项目证据仍为 0**（11 条全 c-blosc2）→ chunk3 的 `--stop-frac 0` 对照就是为这个。
21. **W5 第二轮新增待办**：① **项目集中度恶化**：c-blosc2 占 **58/70** 复现 → 累积复现率 46.4% 越来越像"c-blosc2 的复现率"，**不能当全局估计**；要降集中度必须建新项目镜像（筛选已给出 libredwg/radare2/opensc）；② **共享归档的回收时机**：同一 commit 被多条 crash 共享时，先完成的那条会触发回收、后面那条只能重建（本轮已观察到 `purge_on_verify:X` 删掉 Y 引用的目录）→ 可改为"本轮回调结束后再删"，但要与磁盘峰值权衡；③ **N30 的第二道防线**：目前靠 `dataset_path` 保护集，但**本轮还没落盘的行**不在保护集里 → 同轮内共享归档仍可能被提前删（只是不再损伤已交付证据）；④ 60 条历史 `none` 行的悬空 `binary_dir` 已由 ⑤ 兜底标注**新行**，但**旧行不会被重写**（append-only）→ 需要一次显式对账或接受"`none` 档的 binary_dir 是历史指针"这一约定。
22. **W5 收尾状态（四块跑完后的账）**：✅ **92 条积压全部处理**（83 进复现记录表、9 条被早停跳过可下轮重试、75 条新复现）；✅ **N16 生产 2/2 成功**（账已销）；✅ **N12 按预注册判据翻转默认并已在生产触发**（md4c 1 次）；✅ **排序键根因已修**（`fixed_first`）；✅ **N30 证据已恢复并 5/5 sha256 校验**。⬜ **仍欠**：① `not_located` **19**（差 11；积压全 `located`，**只能靠新镜像去 2,801 条未采样池**）；② **N12 的跨项目证据仍缺**（hunspell 20 条产生 **0** 个候选 → 不是「验证过没反例」，是「没有可检验样本」；新项目轮次要用 `--stop-frac 0` 攒对照）；③ **MSAN flaky 重试**仍未触发（需人工构造）；④ **UBSAN 正样本仍为 0**；⑤ 24 条历史 `none` 行的悬空 `binary_dir`（旧行不重写；verified 行为 **0**）；⑥ **项目集中度**：c-blosc2 占 60/103 复现 → 68.2% 这个数**不能当全局复现率**。
23. ~~**下一步的唯一高性价比动作**：建 libredwg~~ → **W5 实测否决**：libredwg 单次构建 **30min+** 且 `make check-prep` 编 ~100 个 ASAN 单测撑爆磁盘（`No space left on device`）→ 68 条 ≈ **40 小时**，不可行；改选 opensc 后**探针 0/3**（`-Werror`）也被否决。**现状：v2 筛选给不出任何 ✅ 级候选**，四个 ⓘ 级（openh264 / libxml2 / libavc / mupdf）只能靠探针定夺。
24. **W5 第三轮新增待办**：① **`build_error_detail` 抓错行已有实证**（N28③）：opensc 的 detail 报 `OpenPACE linkage required`，真凶却是 `asn1.c:577 [-Werror,-Wuninitialized]` → 照 detail 查会**完全跑偏**；应改为抓**致命错误**（`make Error`/`ninja: build stopped` 之前最近的 `error:`）而非第一条；② **预检第二盲点**：libxml2 的 `build.sh` 全文只有一行裸脚本 `fuzz/oss-fuzz-build.sh`（无解释器/无 `$SRC/`/无 `./`）→ `SCRIPT_RE` 抓不到（N27③ 同族），未修；③ **规模化决策**：按 W5 实测命中率（新项目 4 试 0 中）与磁盘（8.9G，只容 2–3 镜像），继续扩规模是「每个项目 2.3GB + 一次探针、命中率 ≤1/4」的赌注 → 要么接受当前 **103 条 verified** 的交付面并做审计，要么明确按「探针优先、单项目单镜像」的节奏继续；④ 若继续，**优先 openh264**（64 条池，含 **15 MSAN + 2 UBSAN + 13 i386** → 一次能碰 MSAN flaky、UBSAN 零正样本、N22 跨项目三条账），其次 mupdf（37 条含 **30 MSAN**）。
25. ~~**W5 待办 24④：优先探针 openh264**~~ → **已执行，0/3 否决**（镜像 2.9GB 已删）。由此新增两条待办：① **N33 的离线判据**：把「当期 Dockerfile 的 `apt-get install` 列表 × `apt-cache policy` 是否可安装」做成筛选维度 → 能在**建镜像之前**否掉 openh264 这类项目（目前只能靠探针，每个 2.3–2.9GB + ~10min）；② **N34 盲点③的修法**：预检额外抓 `$SRC/*.cpp` 的相对 `#include "…"` 并在该 commit 树上查存在性（raw 端点、0 API 0 clone，成本与现有预检同量级）；③ 盲点②（libxml2 那种全文一行裸脚本的 build.sh）仍未修。
26. **W5 收尾的规模化判断（供决策，不含推测）**：真·积压已**归零**（正确口径核实：102 条处理完 → 75 条新复现；最后 10 条 0 复现；旧口径误报的 4 条已拆清 = 1 条 N6 禁钉版 + 3 条钉版全失败，见 §4.47）；已知可用的五个项目未采样池**全为 0**；未试池 **2,984 条**全需新镜像，而 v2 筛选**无 ✅ 级候选**、W5 新项目**5 试 0 中**、且 N33 表明「老 crash + 老 Dockerfile」这一大类官方兜底救不了。→ 继续扩规模是「每项目 2.3–2.9GB + 一次探针、命中率 ≤1/5」的赌注；**相对地，把现有 103 条 verified 的交付面做审计、或攻那 ~40 条「钉版也试过仍没崩」的硬骨头，边际收益更确定**。
27. **W5 收尾发现的残留缺陷（`binary_pruned` 标记不完整）**：⑥ 的阶段顺序是 **⑤ annotate → 轮末 prune**，所以 prune 删掉的归档必然留下一行「⑤ 写行时目录还在、之后才被删」的**未标记悬空指针**。✅ 实测 18 条，**全部是 `none` 档**（prune 只删未被 verified 引用的归档），而 §1.6 本就只交付 verified 子集 → **属设计内、无交付损失**；红线指标「**verified 行悬空 = 0**」当前为 **0**（曾有 2 条，已重建并 5/5 sha256 校验）。⑤ 的兜底（按目录存在性标注）只能救「写行时已删」的情况，救不了之后才被 prune 删的行。**根治的两条路（都未做）**：① 把 prune 提到 ⑤ 之前 —— 但保护集必须改成读**本轮的 verifications**（否则本轮 verified 归档会被删）；② 让 prune 回写标记 —— append-only 复现记录表下代价高（要为每条受影响 crash 追加一行）。当前处置：`w5_backlog_report.py` 把这两类**分开报**，不再把 `none` 档悬空当违约。
28. ~~**W5 待办：攻硬骨头**~~ → **已做一轮**（7 条 / `--max-depth 6`）：**3 条翻 strict**，硬骨头 40 → **37**；其中「镜像还在且项目可构建」的剩 **10 条**（4 条已试过 depth6 仍 none）。**由此确立标准流程**：`--max-depth` **默认保持 3**（全复现记录表仅 0.9% 需要更深，抬全局不划算），**只对残差做 depth 6 深重试**（本轮残差命中率 1/7 ≈ 14%）。若还要榨这 10 条，可试的杠杆只剩：① 更深的 depth（>6，收益递减）② 多次运行同一 testcase 探 flaky（③ 已有 `attempts`/`retries_for` 机制，但 153 条里 `retry_count>0` 仍为 **0**）③ 换 `--t-strict` 口径（会影响 strict/medium 划分，属改判据、需先预注册）。
29. ~~**W5 待办 25①：N33 的离线判据**~~ → **已实现并校验**（`w5_predict_dockerfile_drift.py`，1 真阳/5 真阴/0 假阳/0 假阴，见 §4.50）。**结论是它排不上用场**：跑完 12 个候选只有 openh264 命中（而它已实测死）→ **N33 不是剩余候选的主要屏障**，真正的屏障是路径错配（5 个 ⛔）与外链/体量（6 个 ⚠）。**仍缺的离线维度**：`-Werror` 洁净度（opensc 的死因）—— 这个**离线判不了**，只能靠探针。
30. **W5 第六轮后的剩余待办**：① ~~**N34 盲点③**未修~~ → **W5 第七轮已实现并校验**（`precheck_includes()`，openh264 已知答案对上真凶）；**但适用边界窄**：只对「Dockerfile 把 fuzzer 源码 COPY 进 `$SRC`」的项目有效，当前 8 个候选全部不适用 → 价值是**封住这个失败模式**（下次遇到同型项目，建镜像前就能否掉），不改变本轮选择；② `build_error_detail` 现在按**首试段**取了，但仍是「段内第一条 `error:`」，未做到「取致命错误」（`make Error`/`ninja: build stopped` 之前最近的那条）；③ 若还要扩规模，**只剩探针一条路**（离线维度已全部用完、无 ✅ 候选），按 W5 实测命中率 ≤1/5 计，每次尝试成本 2.3–2.9GB + 10–30min。
31. **[W5 第八轮新增] 积压度量仍有漏算**：`w5_backlog_report.py` 的候选过滤是 `commit_source == "head"`，于是「路由到钉版但实际一次构建都没发生」的行**不算积压** → 我先前报的「真·积压 0」**不成立**：✅ 实测至少 **2 条 libtiff**（`OSV-2020-1232`/`OSV-2020-1306`，`build_status=None`、`build_stage=None`、`pinned_commit=None`、libtiff 在 `build_records.jsonl` 里 **0 条记录**，却写着 `walkback_depths_tried=1`）+ **2 条 mupdf**（`OSV-2018-293`/`OSV-2018-413`，其 `buildscript_mismatch` 判定现已知是 **N36 误报**）。修法：判据改成「无 build record 且无 build_stage」即算未尝试。与 N29/N30 同一类错误 —— **把「路由到了」当成「试过了」**。
32. **[W5 第八轮新增] N38 的廉价前置信号未实现**：`repo_url` scheme 为 `git://`（非 `https://`）+ Dockerfile 用 `--depth 1` 预克隆 → 应进筛选表作⚠维度。当前只能靠「建镜像 + 烧一格 3,600s」才发现，是四类天花板里**最贵**的一类。
33. **[W5 第八轮新增] `--min-free-gb` 默认 `0.0` = 默认无磁盘护栏**：本轮磁盘一度掉到 5.6G 全靠手工盯。建议给一个非零默认（或在 ⑥ 里按镜像体积预估后自动设）。
34. **[W5 第八轮新增] 杀构建会污染 worktree**：era 预 checkout 是**暂存**的（`git status` 第一列 `M`），`git checkout -- projects/` **修不回来**，必须 `git restore --source=HEAD --staged --worktree` + `git clean -fdq`。`restore_projects()`（N18）本身正确，但只在进程正常结束时跑 → **规程：杀构建后必须手工还原**；可考虑在 ⑥ 启动时无条件先跑一次 `restore_projects`。
35. **[W5 第九轮 · N39 待决] 17 条 hunspell 的 tier 需重判**：在 `normalize_observed()` 里剥 C++ 参数签名 → 重跑 ④⑤（**零构建**）→ tier 变 `64 strict / 19 medium`；同时**改写 §4.44 里被推翻的那个结论**。**须先加自测已知答案**：`OSV-2022-1004` 必须升 strict，且**负对照**（帧真的不同的那条）必须仍留 medium，防止「剥签名」退化成一律放行。
36. **[W5 第九轮 · N40 残留] reproduce 日志名应带 `run_id`**：轮转只保住字节，旧复现记录表行的 `raw_log_path` 仍指原名（现在是最新那次的内容）→ 彻底修法是改成 `<osv>.<run_id>[_rN].log`，使每个引用**永久精确**。障碍：`run_id` 在 ③ 作用域不可用（只有 ⑥ 知道）→ 需给 ③ 加 `--run-id` 并由 ⑥ 透传。
37. **[W5 第九轮] 查看器必须复刻判分算法**：`show_repro.py` 的【3】最初按**位置**比 `R[i]` vs `O[i]`，于是一条 `score_subseq=1.0` 的 strict 显示成三帧全 ❌（判分其实是**有序子序列**、不要求同位置）→ 已改。**教训**：解释性工具若不复刻被解释的算法，会制造比它要解决的问题更多的误解。
38. **[W5 第十轮] `binaries/` 目录名不准确**：它实际是**归档下来的 `/out`**（二进制 + 其运行时数据文件）。改名需连带处理：复现记录表 156 行历史绝对路径（append-only 不能改，只能靠兼容符号链接）、DELIVERY 多处引用、`prune/purge` 的路径比对（**N41 已加固 → 现在改名是安全的**）。属**纯命名改善**，待定。
39. **[W5 第十轮] `by_crash_type/` 是派生物，需随复现记录表刷新**：幂等可重建、不进复现记录表、不参与审计。每跑完新一轮需 `python3 show_repro.py --build-index`；可考虑挂到 ⑥ 轮末（与 `--purge-on-verify` 同处），但**必须在 ⑤ 之后**（依赖最新 tier）。
40. **[W5 第十一轮] 重建完成后需刷新 `by_crash_type/` 视图**：它是派生物（幂等可重建），重建归档后 `PRUNED.txt` 应被真符号链接取代 → 跑 `python3 show_repro.py --build-index`。可考虑挂到 ⑥ 轮末（**必须在 ⑤ 之后**，依赖最新 tier）。
41. ~~**[W5 第十一轮] `rebuild_archives.py` 的 bit 级校验结果待记录**~~ → **第十二轮已完成**：**64 个归档 / 498 个文件 sha256 逐个一致、0 不符、0 仍缺**（跨 4 项目 × 2 架构、跨「删除→数小时后重建」的时间间隔）→ §0.3「bit 可确定性」结论**无需加限定条件**，反而拿到全量证据。
42. **[W5 第十二轮新增] 早停判据需要「项目级 vs 逐条级」的显式区分**：N43 暴露的是**概念错误**而不只是漏一个正则 —— `DETERMINISTIC_FAIL` 的语义是「同项目同 era 必然同样失败」，但 `commit_not_found` 取决于**是哪一个 commit**。建议给每个失败类标注**作用域**（`project` / `commit` / `transient`），只有 `project` 级才计入早停；并在自测里对**每个**类都断言其作用域。
43. **[W5 第十二轮新增] 下一批候选已离线筛好**：**libwebp**（池 10、放行 8 = 80%，chromium.googlesource，N42 已通）· **libhevc**（池 25、放行 13 = 52%，与 libavc **同厂（ittiam）同 `fuzzer/ossfuzz.sh` 形态** → libavc 成功是它的强正面先验）。**ghostscript 池最大（197）但 ⛔ N38 高风险**（`git://` + `--depth 1`，与 mupdf 同型同主机）→ 除非先解决 N38 否则不要碰。**libaom 已淘汰**（0/14）。
44. **[W5 第十二轮新增] 磁盘需要重新规划**：purge 默认关后归档持续累积（本轮 1.2G→4.2G、磁盘 11G→7.3G）。按 libavc 43 条 ≈ +1G 估算，再跑 libwebp+libhevc（35 条）≈ +0.8G → 仍安全；但若日后跑通 ghostscript 级别的大池，需要**分级保留策略**（例如只留 strict 的二进制、medium/loose 按需重建），而不是回到「全删」。
45. **[W5 第十三轮新增 · 可作硬前置] 「全量 https 克隆」是新项目成功的必要条件**：✅ 9 试 3 中，三个成功项目的 Dockerfile 都是全量 https 克隆、无 `git://`、无 `--depth 1`；失败的分别死于 N28（外链）/ N33（era 包下架）/ N38（`git://`+浅克隆）。→ 应把这条写进 `w5_screen_v2_buildcost.py` 作**第 6 维**（纯静态、零成本），并把 N38 的「廉价前置信号」（§5 第 32 条）一并实现。
46. **[W5 第十三轮新增] 复现率的口径需要显式区分「未构建」与「构建后没崩」**：本轮 64.1% 里有 18 条**从未被构建**（预检⛔）。建议 §0.3 同时给出两个数：**全口径**（分母 = 所有跑过的）与**方法口径**（分母 = 真拿到二进制并重放过的）—— 后者才反映复现方法本身的有效性。
47. ~~**[W5] MSAN flaky 重试从未触发，需人工构造**~~ → **第十三轮已销**：9 条生产触发（全 memory），其中 2 条 `attempts=[0,1]` 是**重试救回的复现**，另有 `[0,0,0]` 的如实记 none（未退化成造假工具）。
48. **[W5 第十四轮新增] 「可重放」必须用**实测重放**验收，不能用「目录存在」代替**：N45 的 2 条正是「目录在盘」但 driver 不在。建议给审计再加一条**抽样实跑**（每项目随机 1 条，`docker run` 真跑一遍、要求 exit=1 且报告含 sanitizer 错误），成本约 10 条 × 2s。
49. **[W5 第十四轮新增] `exit_code` 字段应改名或加注释**：3 条真崩溃记 0（N47）。建议改名为 `runner_exit_code` 并在 §1.5 字段表注明「**不可作判崩依据**，判崩看 `reproduced_any` + `observed_crash_type`」。🅗 exit=0 成因未查明。
50. **[W5 第十四轮新增] `report.log` 是按 OSV 单文件、后写覆盖**：虽有 N40 轮转副本（✅ 实测 `OSV-2023-1322_r2.log` 等留住了 MSAN flaky 的成功证据），但 `by_crash_type` 里的 `report.log` 链接指向的是**最新一份**，未必是判分那一份。建议改为链接`artifacts/runs/<run_id>/reports/<OSV>.log`（按 run 冻结），否则 loose 档「继续下探」的行会出现「tier 说崩了、report 显示没崩」的观感矛盾。
51. ~~**[W5 第十四轮] `report.log` 后写覆盖 → 交付里可能链到「没崩的那一份」**~~ → **第十五轮已修**：交付视图改为**冻结副本**，并在 N40 轮转副本里挑「`# binary_dir:` 与复现记录表一致**且** `# exit: 1`」的那一份；挑不到才退回 `raw_log_path` 并**在 INFO.txt 里如实标注**（本轮 4 条）。
52. **[W5 第十五轮新增] flaky 率需要进入交付口径**：✅ 实测 151 条里 3 条非首轮即崩（2 条第 3 次、1 条第 8 次 / 崩溃率 12%）。目前只在 INFO.txt 里标注，建议 §0.3 的复现率同时给出「**首轮复现率 148/237 = 62.4%**」与「**含重试 151/237 = 63.7%**」两个数，并说明重试上限（⑥ 的 `retries_for` 只对 MSAN 生效，ABRT 类 flaky 目前**不在**重试范围）。
53. **[W5 第十五轮新增] `replay_verification.json` 应纳入定期重跑**：本轮是**第一次**全量重放验收（25min / 151 条）。二进制在盘、镜像在盘的前提下它可重复；建议每新增一批复现就重跑一次，并把「首轮通过率」作为交付质量指标跟踪。
54. **[W5 第十五轮新增] 交付视图与归档层的一致性需要一个自动核对**：目前 `build_index` 每次全量重建（幂等），但没有自测断言「每条恰好 1 个 ELF」。建议加一条：重建后扫描全部条目，ELF 数 ≠ 1 即失败 —— 这正是用户两次指出的那个性质，**应该由测试守着，而不是靠人眼看**。
55. ~~**[W5] `normalize_one_frame` 不剥 C++ 参数签名 → 17 条 hunspell 应为 strict**~~ → **第十六轮已修（N39）**：`strip_cpp_signature` 只挂 O 侧，**strict 69 → 86**（占复现 57.0%）。⚠ 但 `T_strict` 阈值本身**仍未被验证**（升档的 17 条 subseq 全是 1.0，刻度样本仍 3 条）。
56. ~~**[W5 第十五轮] 建议加自测断言「每条恰好 1 个 ELF」**~~ → **第十六轮已加（N53）**，含牙齿测试（注入第二个 ELF 立即报红）。
57. **[W5 第十六轮新增] R 侧存在「模板类型名当帧名」的脏 ground truth**：`OSV-2022-899` 的 R[0] 是 `std::__1::basic_string<char, std::__1::char_traits<char>, std::__1::allocator<ch`（**被截断到 80 字符**、且是类型名不是函数名）。这类帧永远无法与任何 observed 栈对齐 → 该条**结构性地拿不到 strict**。建议统计全量 3,790 条里有多少 R 帧属此类，作为「strict 上限」的一个已知折损项。
58. **[W5 第十七轮新增 · 判据设计问题，未擅自改] 期望值是 `unknown` 时 `crash_type_match` 永远为假**：✅ 实测全复现记录表 **17 条** verified 的 `crash_type_expected` 就是 `unknown`（ClusterFuzz 当年没分类），它们**结构性地拿不到 medium/strict**（只能 loose），哪怕帧完全对齐（`OSV-2020-1016` 就是 `score_subseq=1.0` 却因期望 unknown 而停在 loose）。可选：把「期望 unknown」视作**类型不可判**，改按帧单独定档（与「recovered 0 帧」同法处理）。**这是放宽判据、会抬高 tier，必须由人决定**，故本轮只做记录。
59. **[W5 第十七轮新增 · 紧急度上升] 磁盘分级保留策略必须先定**：归档已 **8.5G**、可用 **4.1G**；unicorn 探针期间一度掉到 **2.7G**（era 机制为每个 era commit 建 ~2.4G 镜像、旧 tag 变悬空）。本轮靠清 `build/{out,work}`（+3.6G）与悬空镜像（+1.4G）撑过来，但这是**一次性**的。建议：① 每轮结束自动清 `build/`；② era 镜像用完即删；③ 归档按 tier 分级（strict/medium 常留、loose 可按需重建）。**不定这条就别再开大池。**
60. **[W5 第十七轮新增] `UBSAN_CHECK_MAP` 需要按实测逐条扩**：目前只有 1 条已验形态（`index N out of bounds for type` → `Index-out-of-bounds`）。unicorn 还有 1 条 UBSAN、arrow 有 7 条、skia 1 条 → 每撞到一个新形态就加一条（**必须有 expected 与 observed 真对上的样本**，不靠猜）。
61. **[W5 第十七轮新增] `rebuild_archives.py` 的 bit 一致性只对 4 个项目验过**：libavc 5/5 不符（N60 段）。建议对每个项目**首次重建时**都做一次逐字节校验，并把结果分项目记入 §0.3，而不是笼统写「可 bit 级重建」。
62. ~~**[W5 第十七轮] 磁盘分级保留策略必须先定**~~ → **第十八轮已实施（N61）**：`disk_policy.py`，默认 `reuse` 保护规则（实测比 tier 分级多回收 62%），纯废物无条件清、动归档受阈值门控，并已接进 `run_repro.py --post-clean`（默认开）。可用 3.0G → **13G**、归档 8.5G → **2.2G**。
63. **[W5 第十八轮新增] `--post-clean` 只在轮末触发 → 大归档项目仍需分批**：unicorn 单归档 104～124MB、整池 30 条估算要 **37GB** → 轮中必写满。建议给 ② 加**逐条构建后即时瘦身**（每条 crash 落账后就删该归档里非交付必需的兄弟文件），而不是等轮末；或给 `run_repro.py` 加 `--max-archive-gb` 水位线触发中途回收。
64. **[W5 第十八轮新增] `reuse` 保护规则的阈值（>1 条）值得复核**：目前 19 个归档因服务 >1 条而保住 698MB 兄弟文件。若后续项目多为「一 commit 一 crash」，这条规则会退化成全瘦身；建议每轮末把「受保护归档数 / 保住字节」打进 run_meta，便于观察它是否还划算。
65. ~~**[W5 第十八轮] 给 ② 加逐条构建后即时瘦身 / 水位线**~~ → **第十九轮已实施（N62）**：`--mid-clean-free-gb`（默认 5.0）+ 每条 crash 开跑前查水位。✅ 实测触发 3 次、磁盘 6.7G↔12G 震荡。
66. **[W5 第十九轮新增] N62+N64 双闸之下，unicorn 剩余池仍要**严格分批**：**单个 `fuzz_emu_*` 二进制 **108MB**（内嵌 QEMU）、一次构建产出全部变体 → **~540MB/构建**、每条 crash 实测 ~2.6 构建 → **~1.4GB/条**。池 33 条已做 11、剩 ~22 条 → 一次全跑要 **~31GB**。建议 `--limit ≤ 4`，或给 ② 加「**归档落盘后立即按 bundle 瘦身**」（而不是等水位线），从根上把 ~540MB/构建 降到 ~110MB/构建。
67. **[W5 第十九轮新增] `--protect-since` 的保护集合会随轮次变长而变大**：本轮保护了 7.29GB → 直接导致 N64 写满。建议改为「**只保护最近 K 条 crash 的归档**」（滑动窗口），或保护时**只保 bundle 不保兄弟文件**（需要在飞行的 target 已知，② 其实知道）。


**P2（主线外）**
12. 379 条不可复现空 target 联网回捞（⑦，156 已零成本推定）。
13. 非 C/C++ 246 + unknown 42 条复现路径（JVM 需 Jazzer；unknown 待 M2 映射批准，oniguruma/upb 疑已移出 ⓘ）。

**已删除（全量扩面假设产物，增量模式不需要）**：机时/串行天数估算、per-phase 预算、构建次数全量去重优化、磁盘全量外推（M12 已撤回：`build/out` 是 `clear.sh` 清理后残骸、0 executables）。

---

# 6. 交付物清单与复算命令

| # | 文件 | 内容 |
|---|---|---|
| 1 | **`DELIVERY.md`（本文件）** | 唯一交付文档：结论 + 设计规格 + 实测结论 + N1–N6 + 已实现对账 + 开放问题 + 复算命令 |
| 2 | `repro_common.py`（⓪） | 共享底座（4 数据源/路径/normalize_frames 逐字复用/派生 helper/R13a/N6/repo_path 解析/静态 check/schema） |
| 3 | `manifest_builder.py`（①） | 产出 manifest + build_groups；全量对账 + 3 条已知答案回归 |
| 4 | `artifacts/repro_manifest.jsonl` | 3,790 条 × 44 字段 |
| 5 | `artifacts/build_groups.json` | 404 head_groups + 3,093 pinned_queue（+ meta/args 可溯源） |
| 6 | `artifacts/repo_path_map.json` | 328 项目的 clone 清单 + 默认解析 + 假设 (A)(B) 统计 |
| 7 | `preflight/history/locate_sources.py` | Step1 数据源定位 |
| 8 | `preflight/history/m_crash_data.py` | M1/M5/M6/M7/M8/M9/M10 |
| 9 | `preflight/history/m_ossfuzz.py` | M2/M3/M12（M12 已撤回 R4） |
| 10 | `preflight/history/m4_fixed.py` | M4 fixed commit 可用率 |
| 11 | `preflight/history/r2_r5_r6_r7_recompute.py` | R2 归一化重聚类 + **R2-extra**（`normalize_frames` 的权威实现，⓪ 从此提取）/R5/R6/R7 |
| 12 | `preflight/history/r1_r13_r14_routing_scale.py` | R1/R13/R14（⚠ R1 的 no_fixed 细分有解析假象，见 §2.5） |
| 13 | `preflight/history/w1_offbyone_sampling.py` + `offbyone_sample_results.json` | W1 第一件：off-by-one 分层抽样（**需网络**）+ 48 条逐条信号原值 |
| 14 | `preflight/history/w1_repo_path_scan.py` | W1 第一件附带：Dockerfile clone 目标审计 + 映射表生成（纯本地） |
| 15 | `archive/`（7 份底本） | 历史全文，**不再维护、以本文为准**（见 §7） |
| 16 | **`repro_dataset.jsonl`** | ✅ **最终交付物**：142 行 / 129 条 crash / 51 字段，append-only 跨 3 个 `run_id` |
| 17 | `build_orchestrator.py`/`repro_runner.py`/`verify_tiered.py`/`annotate_dataset.py`/`run_repro.py` | ✅ W2 的 ②③④⑤⑥ |
| 18 | `artifacts/{state.json,build_records.jsonl,binaries/,logs/,runs/}` | ✅ W2 运行期产物（续跑缓存 / 构建复现记录表 / 归档二进制 / 全部 stderr / 每轮中间产物） |
| 19 | `preflight/w2_phase0{a,b,c}*.py` + `w2_phase5*.py` + `fixtures/` + 各 `.json` | ✅ W2 Phase0 三项审计、Phase5 五项分析、③ 解析器的 4 段真实 stderr 护栏 |
| 20 | `archive/2026-09-09-w2-report.md` | W2 主报告**原文快照**（该报告自身的 §1–§10 结构、md5 与并入前一致）。**内容已全量并入本文 §4.5–§4.13**，此份只作冻结底本、不再维护 |
| 21 | `artifacts/runs/<run_id>/walkback_trace.jsonl` | ✅ **W3** 逐格 walk-back 轨迹（每格 depth/commit/build 结果/tier/三个 score/构建秒/era 命中）= §4.19 策略重算的原始依据 |
| 22 | `preflight/history/w2_phase0a_audit.json`、`w2_phase0b_queue_order.json`、`w2_phase0c_degenerate.json`、`w2_phase5*.json` | ✅ W2/W3 各项分析的逐条原值（W3 的 Phase 1/3/4/5 数据在 `artifacts/runs/w3-*/` 与 `build_records.jsonl` 里，未另出 JSON） |
| 23 | **`artifacts/prune_audit.jsonl`** | ✅ **W4** 每次裁剪（含 dry-run 与 REFUSED）的审计：`action`/`n_pruned`/`M`/`freed_bytes`/**完整删除清单** |
| 24 | **`artifacts/dataset_guard.jsonl`** | ✅ **W4** ⑤ 单调性校验的审计：`refused` / `forced_downgrade` + 原因 |
| 25 | `preflight/selftest/w4_phase1a_selftest.py` | ✅ **W4** 两道数据完整性防御的自测（**12/12**；构造降级写入 + 构造会删 verified 的裁剪，均不碰真实数据） |
| 26 | `preflight/history/w4_phase4e_negctl.py` + `w4_phase4e_negctl.json` | ✅ **W4** 新判据负对照（HEAD 为默认 + 版本感知补充 + 正对照），**11/11** |
| 27 | `artifacts/runs/w4-*/walkback_trace.jsonl` | ✅ **W4** 策略 A 的逐格轨迹（advisory vs 实际 best_depth 的原始依据） |
| 28 | **`preflight/selftest/w5_phase1_replay_stopfrac.py`** + `w5_phase1_replay_stopfrac.json` | ✅ **W5** N12 的**离线回放**（0 次构建）：阈值扫描 + tier 损失 + **distinct-crash 口径** + 预注册翻转判据判定；内置**冻结值交叉校验**（W3+W4 子集 @0.6 必须 = 5/7/0/3，漂移即红） |
| 29 | `preflight/selftest/w5_selftest_bo.py` | ✅ **W5** ② 自测 15 项：**日志轮转 7**（N25，含端到端连跑两次 `run_cmd`）+ **N16 重试接线 8**（跑真 `build_pinned`，含分类器负对照） |
| 30 | `preflight/selftest/w5_selftest_stopfrac.py` | ✅ **W5** ⑥ 停止判据 19 项（tier 停 / frac 停 / None 与 reproduced 守卫 / shadow 常开 / CLI 默认值） |
| 31 | `preflight/selftest/w5_selftest_classifier.py` | ✅ **W5** ② 失败分类器 **18 项（新固化**——此前只是内联 heredoc，§6 声称的「可复算」是空的）：13 类别 + 大日志不截断（967,868 B）+ `FAIL_PATTERNS` 倒序负对照 |
| 32 | `preflight/selftest/w5_selftest_annotate.py` | ✅ **W5** ⑤ 字段透传 11 项（`walkback_stop_reason` + 既有 `walkback_*` 回归 + 负对照） |
| 33 | `preflight/selftest/w5_selftest_overwrite.py` | ✅ **W5** ① 覆盖护栏 14 项（覆盖面缩水 / 字段强度 / 只在交集上比 / 负对照） |
| 34 | `artifacts/manifest_overwrite_audit.jsonl` | ✅ **W5** N26 强制覆盖留痕（**本轮不存在该文件 = 从未发生过 `--force-overwrite`**；生产那次被拦下、退出 4、未写盘） |
| 35 | `artifacts/logs/build/*.log.<UTC 时间戳>` | ✅ **W5** N25 轮转保留的历史日志（**永不销毁**上一次的证据）。**本轮已有 1 件、且是生产实证**：`c-blosc2_address_af4860f071a1.log.20260914T015239`（37,844 B，原 ts 2026-09-10 18:03）—— `w5-shadow-A` 那轮重建了同一 commit，**旧日志被改名保留而不是被覆盖**。这正是销毁掉 N16 证据的那个场景，如今不再发生 |
| 36 | `artifacts/runs/w5-shadow-A/`、`artifacts/runs/w5-fracstop-B/` | ✅ **W5** N12 的**生产对照两轮**（同一条 crash、同一批缓存构建）：A 默认 → 3 格 / shadow 全 True / `stop_reason=None`；B `--stop-frac 0.6` → 1 格 / 省 2 次构建 / `stop_reason='frac'` |
| 37 | `preflight/selftest/w5_selftest_precheck_sha.py` | ✅ **W5** 预检**不得误报**的自测 15 项：`sha=None`/`repo_url=None` 必须「无法判定」且**零 HTTP**、候选不得带 `./`、`bash -x ./a/b.sh` 必须被抽到（N27③）、含负对照证明没被修成恒放行 |
| 38 | **`preflight/selftest/w5_precheck_known_answers.py`** | ✅ **W5** 预检的**已知答案回归**（把 W4 的内联验证固化）：真报 harfbuzz 4/4 + pcapplusplus 3/3 + libspng 4/4、误报 0（23 个已成功 commit）、契约 2 项；并断言「**被跳过的已知答案项目必须为零**」 |
| 39 | **`preflight/history/w5_screen_next_projects.py`** + `.json` | ✅ **W5** 「下一个建哪个镜像」的离线筛选（**0 docker / 0 构建**）：第三方外链数 + 真实钉版 commit 上的预检；输出**三级证据**（✅真查过 / ⓘ无证据附原因 / ⛔出局）并按证据加权排序 |
| 40 | `artifacts/runs/w5-expand19b/` | ✅ **W5** 扩样本第一轮的完整产物（manifest 19 / walkback_trace / observations / verifications），§4.41 全部数字的原始依据 |
| 41 | **`preflight/selftest/w5_backlog_report.py`** | ✅ **W5** 积压重跑的逐块核查 + 累积汇总：tier/版本/静态check/walkback 分布、**逐条回收的完整性契约**（`binary_pruned` 行必须留住 sha256+配方）、**无声悬空指针必须为 0**、两条预注册判据的进度 |
| 42 | `artifacts/runs/w5-backlog1..4/` | ✅ **W5** 92 条积压重跑的完整产物（chunk1 **23/23**、chunk2 **19/23**；chunk3/4 见 §4.43）——§4.43 全部数字的原始依据 |
| 43 | `preflight/selftest/w5_selftest_purge.py` | ✅ **W5** 逐条回收自测 **19 项**：只删钉版（白名单，`path` 缺失→不删）、HEAD/`_shared` 拒删、state 缓存键失效、审计、dry-run、**dataset 保护集（N30 事故的正解）**、⑤ `binary_pruned` 透传与兜底、CLI 默认值（`--sort fixed_first` / `--purge-on-verify` / `--stop-frac 0.6`） |
| 44 | **`preflight/screen/w5_screen_v2_buildcost.py`** + `.json` | ✅ **W5** 筛选 v2：只保留**实测有区分力**的维度（第三方外链 / 路径错配 / **构建体量**：测试套件精确模式 + repo MB），并显式标注**离线判不了**的部分（`-Werror`）→ 结论「无 ✅ 级候选」。含被否证维度（crash 年份）的记录 |
| 45 | `artifacts/runs/w5-opensc-probe/`、`w5-libredwgA/`、`w5-oh264-probe/`、`w5-backlog1..4/`、`w5-backlog-final/` | ✅ **W5** 全部轮次的完整产物，含 **3 次失败尝试**（libredwg 中止 / opensc 0/3 / openh264 0/3）——**负结果也是交付物**：§4.45–§4.46 的死因判断全部可从这里复算 |
| 46 | `preflight/selftest/w5_backlog_report.py` | ✅ **W5** 积压/回收契约/两条预注册判据的**统一核查脚本**（可重复跑）。**含 W5 修的度量缺陷**：旧口径只看 `commit_source` → 会把「钉版试过但每格构建失败（无 observation → 无新行）」和「N6 退化禁钉版」误报成积压；现按 `build_records` 的 `build_stage==2` + `static_check_verdict=='degenerate'` 三分类，输出**真·积压**（现 **0**） |
| 47 | **`preflight/selftest/w5_audit_delivery.py`** | ✅ **W5 交付面审计**：直接审复现记录表自洽性（6 组不变量，判据取自 ④ `verify_one()` 实际代码）。**为什么必须有**：W5 下半程查出的 4 个缺陷（⑤ 白名单漏字段、悬空 `binary_dir`、N30 删证据、积压度量误报）**没有一个能被现有 13 套自测发现**——那些测「模块行为」，这些是「复现记录表自不自洽」。`--dataset` 可指向副本供牙齿测试用 |
| 48 | **`preflight/selftest/w5_selftest_audit_teeth.py`** | ✅ **W5 审计的牙齿测试**：往复现记录表**副本**注入 4 类违规（strict∧¬crash_type / verified 缺 sha256 / verified 悬空未标 / none∧reproduced）→ 审计必须退出非 0，且**真复现记录表必须仍绿**（防恒红）。**它已经抓到过审计自身的漏检**（`n_recovered_frames` 恒 None 导致整段不检查） |
| 49 | `artifacts/runs/w5-hardretry/` | ✅ **W5** 硬骨头重试轮（7 条 / 33 次构建 / `--max-depth 6`）的完整产物：`walkback_trace.jsonl` 里能看到 OSV-2022-776 **d1–d5 全 none → d6 strict** 的逐格轨迹，是「默认 depth 3 会漏」这条结论的原始依据 |
| 50 | **`preflight/screen/w5_predict_dockerfile_drift.py`** + `.json` | ✅ **W5** N33 离线预测器：era Dockerfile（GitHub API `path`+`until`，取池里**最老** crash 的年份为上界）→ `extract_apt_packages()` 纯函数（自测 7 项：同行多包/续行/flag/`=版本`/`:i386`/空输入/不误抓 `make install`）→ **一次** `docker run … apt-cache policy` 批量查全部包。`--selftest` 跑纯函数部分；`--projects a,b` 可对已榨干池的项目做**已知答案校验** |
| 51 | `preflight/selftest/w5_selftest_include_precheck.py` | ✅ **W5** N34③ 检测器自测 **22 项**：解析层（真读 worktree 里 openh264 的 Dockerfile/源码/build.sh）、候选路径生成（`-I` 目录 + 仓库根、`../` 逃逸拒绝）、实查层（替身，零网络）、**负对照**（头文件在某个 `-I` 里找到 → 必须放行）、守卫（`sha=None`/全无法判定 → 放行）、**[F] 适用边界**（libxml2/radare2/matio 必须 `no_sources` 且放行） |
| 52 | `preflight/selftest/w5_selftest_mirror_submodule.py` | ✅ **W5** N35/N36 自测 **24 项**（**全离线**）：`mirror_for` 归一化（大小写/多尾缀/同主机不同仓库不许误命中/None 不抛）、submodule **前缀陷阱**（`harfbuzz` 不许吞 `harfbuzz2`）、`submodule_paths` 契约（404→空集、其它错→None、缓存命中）、集成（submodule 误报形态必须放行且记 `submodule_skipped` 留痕） |
| 53 | `show_repro.py` | ✅ **W5** **只读查看器**：一条命令摊开某条 crash 的复现（【1】钉的 commit【2】期望 vs 实测【3】按**有序子序列**逐帧展示 R 在 O 中的命中位置、并标出「仅函数名同」【4】三件套路径与在盘状态【5】`--check` 四项只读核对【6】可复制的 `docker run` 重跑命令）；`--tier`/`--project`/`--list` 浏览；**`--build-index`/`--tree`** 生成并打印「按 crash 类型」的符号链接视图（§4.54.2）。**它暴露了 N39** |
| 54 | `artifacts/by_crash_type/` | ✅ **W5** 按 crash 类型的**符号链接浏览视图**（派生物、幂等可重建）：`<类型>/<项目>/<san>/<commit>[@arch]__<OSV>` → 真归档；已回收的放 `.PRUNED.txt` 说明而非断链。实测 **11 类 / 106 条**（34 链接 + 72 说明），**经链接重放实测成功** |
| 55 | `rebuild_archives.py` | ✅ **W5** 重建被 `purge-on-verify` 回收的归档：从复现记录表挑 verified 且归档不在盘上的行 → 按 `(project,san,commit,arch)` 去重 → **`--commit-override` 强制钉到复现记录表记录的 commit**（不能让 walk-back 自己找，否则 restored 的不是原来那份）→ 重建后**逐个 target 比对 sha256**（bit 级验证）。`--dry` / `--verify-only` / `--project` / 自带 `--min-free-gb 4`。**✅ 实测：64 个归档 / 498 个文件全部一致、0 不符** |

```bash
cd /root/gyx/mutator_create/reproduce_crash

# ── 预飞测量（纯本地、不跑 docker、不联网、oss-fuzz 只读）──
python3 preflight/history/locate_sources.py                 # Step1 数据源定位
python3 preflight/history/m_crash_data.py                   # M1,M5,M6,M7,M8,M9,M10
python3 preflight/history/m_ossfuzz.py                      # M2,M3,M12
python3 preflight/history/m4_fixed.py                       # M4
python3 preflight/history/r2_r5_r6_r7_recompute.py          # R2(+R2-extra),R5,R6,R7
python3 preflight/history/r1_r13_r14_routing_scale.py       # R1,R13,R14
grep -n "DEFAULT_SANITIZER\|SANITIZERS" /root/gyx/oss-fuzz/infra/constants.py    # R10
grep -rn "ASAN_OPTIONS\|UBSAN_OPTIONS\|rss_limit_mb\|timeout=" \
  /root/gyx/oss-fuzz/infra/base-images/base-runner/                              # M11

# ── W1 第一件（off-byone 抽样需网络：github/gitlab .patch，0 次 API、0 次 clone）──
python3 preflight/history/w1_offbyone_sampling.py --controls-only                        # 仪器校验，须 2/2
python3 preflight/history/w1_offbyone_sampling.py --n 48 --seed 20260909 --max-depth 3   # 三档 + 四策略 + N6
python3 preflight/history/w1_repo_path_scan.py                                          # 假设 (A)(B) + 映射表

# ── W1 第二件（补丁固化；✅ 已执行）+ §1.7 H 四条件 gate ──
git -C /root/gyx/oss-fuzz-repro log --oneline -1                 # repro-patches @ 07522dc0e
git -C /root/gyx/oss-fuzz-repro show --stat HEAD                 # 3 files, +66/-3
git -C /root/gyx/oss-fuzz-repro rev-parse --abbrev-ref HEAD      # = repro-patches
git -C /root/gyx/oss-fuzz-repro status --porcelain               # = 空
git -C /root/gyx/oss-fuzz-repro merge-base --is-ancestor 07522dc0e HEAD && echo ok
grep -rl dc-injected /root/gyx/oss-fuzz-repro/projects/ || echo "no dc-injected"
git -C /root/gyx/oss-fuzz status --porcelain | wc -l             # 主树须仍为 550

# ── W1 第三件（⓪① 两模块）──
python3 repro_common.py                                           # ⓪ 自检 + normalize_frames 对账 R2-extra
python3 manifest_builder.py                                       # 全量 3,790（~5s）+ 对账 + 回归
# ⚠ [W5 §4.39] **回归数字依赖 flag**：不带 --static-check → 20 通过/0 不符/**9 跳过**；
#    带 --static-check 才是正典的 **25 通过 / 0 不符 / 0 跳过 / 4 争议**。
#    且**子集运行必须改 --out**，否则会被覆盖护栏拦下（退出 4）——那是护栏在正常工作：
python3 manifest_builder.py --static-check \
    --only-osv OSV-2022-126,OSV-2024-1261,OSV-2022-886 \
    --out /tmp/regress.jsonl --build-groups /tmp/regress_bg.json   # → 25/0/0/4（不动交付物）
python3 manifest_builder.py --limit 5 --out artifacts/repro_manifest.jsonl   # → ❌ 退出 4（护栏演示）
# ⚠ [W5] `--repo-map` 指向**不存在**的路径会让全部 repo_path 变 None（回归 3 不符）；
#    做对照实验要先 `cp artifacts/repo_path_map.json /tmp/…` 再指过去（见 §4.39 的误判记录）
python3 manifest_builder.py --languages c,c++ --limit 20           # R16 增量口径示例
python3 manifest_builder.py --only-osv OSV-2022-126,OSV-2024-1261,OSV-2022-886 \
    --static-check --static-check-limit 3                         # 回归须 29/29（需网络）

# ── W2 Phase 0（三项审计）──
python3 preflight/history/w2_phase0a_osv_audit.py                       # osv_events 横向审计（纯本地 ~40s）
python3 preflight/history/w2_phase0b_queue_order.py --n-per-project 12   # 排序键选型（需网络 84 次 .patch）
python3 preflight/history/w2_phase0c_degenerate.py                      # N6 53 条个案复核（需网络，走缓存）

# ── W2 ⓪①（含 N6 复核；33s，9 项对账 + 29/29 回归）──
python3 manifest_builder.py --static-check --degenerate-only --static-check-limit 60

# ── W2 ③④ 自测（不跑 docker；不过就退出 3）──
python3 repro_runner.py --selftest        # 4 段真实 stderr：真崩溃/真无崩溃/init trap/UBSAN exit=0
python3 verify_tiered.py --selftest       # 4 个打分器已知答案（含 P0/P0-B 两个标定点）

# ── W2 已知答案回归（② 产物须与 P0/P0-B/P0-C 手工构建逐字节一致）──
python3 manifest_builder.py --only-osv OSV-2022-126,OSV-2024-1261,OSV-2022-886 \
    --static-check --static-check-limit 5 --out /tmp/reg3.jsonl --build-groups /tmp/reg3.json
python3 build_orchestrator.py --manifest /tmp/reg3.jsonl --only-osv OSV-2022-126 --stage 1
python3 build_orchestrator.py --manifest /tmp/reg3.jsonl --only-osv OSV-2022-126 --stage 2 \
    --commit-override OSV-2022-126=62b60979f6a281b2b3cf883abc84299431fe2f76   # 须得 ee086b95…

# ── W2 ⑥ 一轮完整复现 ──
python3 run_repro.py --projects md4c,pcre2,hunspell,c-blosc2,flatbuffers,libtsm \
    --sanitizers address --stage1-only --run-id <id>                 # HEAD 轮
python3 run_repro.py --projects c-blosc2 --sanitizers address \
    --crash-types heap-buffer-overflow --limit 8 --max-builds 8 --run-id <id>   # 钉版轮（walk-back）

# ── W2 Phase 5 分析 ──
python3 preflight/history/w2_phase5_analysis.py            # (a) depth (b) T_strict (c) 帧形态 (e) T_build
python3 preflight/history/w2_phase5d_negctl.py --n-other 3 # (d) 负对照（跑 docker，8 次）

# ── W3 路由（has_fixed 跳过 Stage1；--force-stage1 退回 W2 旧路由做对照）──
python3 run_repro.py --projects c-blosc2 --sanitizers address --crash-types heap-buffer-overflow \
    --limit 8 --max-builds 14 --min-free-gb 5 --run-id <id>

# ── W3 归档裁剪（默认每轮末自动跑；也可单独跑）──
python3 build_orchestrator.py --prune-archive --prune-dry   # 先看会裁什么
python3 build_orchestrator.py --prune-archive               # 实裁 + 同步删 state 缓存键

# ── W3 完整静态 check（拿 located/not_located，Phase 5 的 not_located 桶要用）──
python3 manifest_builder.py --projects c-blosc2,hunspell,harfbuzz --sanitizers address \
    --static-check --static-check-limit 200 --out /tmp/sc.jsonl --build-groups /tmp/sc.json

# ── W3 i386 配对实验（同一 commit 建两次，比 sha256/ELF class/复现）──
python3 infra/build_specified_commit.py --project_name c-blosc2 --commit <sha> --sanitizer address \
    --architecture i386 --repo_url <url> --repo_path /src/c-blosc2      # → readelf -h 应为 ELF32

# ── W4 数据完整性防御自测（不碰真实数据；12/12 才算过）──
python3 preflight/selftest/w4_phase1a_selftest.py

# ── W4 裁剪：默认 dry-run，真删要显式 --prune-apply ──
python3 build_orchestrator.py --prune-archive                 # 只报告 + 写审计
python3 build_orchestrator.py --prune-archive --prune-apply   # 真删（M>0 会拒绝）
cat artifacts/prune_audit.jsonl artifacts/dataset_guard.jsonl

# ── W4 负对照（新判据：HEAD 为默认 + 版本感知补充 + 正对照）──
python3 preflight/history/w4_phase4e_negctl.py --n-other 3

# ── W4 策略 A + 按 job_arch 构建 + 早停（默认全开）──
python3 run_repro.py --projects c-blosc2 --sanitizers address --crash-types heap-buffer-overflow \
    --static-check --no-degenerate-only --limit 10 --max-builds 12 --min-free-gb 4 --run-id <id>
python3 run_repro.py ... --no-match-job-arch      # 对照：全走 x86_64（会掉 tier，见 N22）
python3 run_repro.py ... --stop-project-after 3   # 早停阈值对照

# ── W5 N12：离线回放（0 次构建）+ 五套自测 ──
python3 preflight/selftest/w5_selftest_precheck_sha.py      # ② 预检不得误报（15 项，零网络）
python3 preflight/selftest/w5_precheck_known_answers.py     # ② 预检已知答案回归（11 真报 / 0 误报，需网络）
python3 preflight/history/w5_screen_next_projects.py --top 14 --sample-commits 3   # 选镜像（0 docker）
# 扩样本一轮（本地镜像池；--stop-frac 保持默认 0 = 预注册不得提前开）
python3 run_repro.py --only-osv <19 个 id> --static-check --no-degenerate-only \
    --static-check-limit 60 --max-builds 40 --min-free-gb 5 --run-id <id>
# ⚠ 后台跑长轮次要用 setsid：`nohup … &` 挡不住工具超时对整个进程组的终止（W5 实测被杀过一次）
python3 preflight/selftest/w5_phase1_replay_stopfrac.py     # 阈值扫描 + tier 损失 + 冻结值交叉校验
python3 preflight/selftest/w5_selftest_stopfrac.py          # ⑥ 停止判据 19 项
python3 preflight/selftest/w5_selftest_bo.py                # ② 日志轮转 7 + N16 重试接线 8
python3 preflight/selftest/w5_selftest_classifier.py        # ② 分类器 18 项
python3 preflight/selftest/w5_selftest_annotate.py          # ⑤ 字段透传 11 项
python3 preflight/selftest/w5_selftest_overwrite.py         # ① 覆盖护栏 14 项
python3 preflight/selftest/w5_selftest_purge.py             # ② 逐条回收 19 项（含 N30 保护集）
python3 preflight/selftest/w5_backlog_report.py w5-backlog1 w5-backlog2   # 积压重跑核查 + 累积汇总
python3 preflight/selftest/w5_audit_delivery.py             # 交付面审计（真复现记录表，须 0 红线）
python3 preflight/selftest/w5_selftest_audit_teeth.py       # 审计的牙齿测试（注入 4 类违规，须变红）
python3 preflight/selftest/w5_backlog_report.py             # 积压正确分类 + 回收契约 + 两条判据进度
python3 preflight/screen/w5_predict_dockerfile_drift.py --selftest      # 纯函数 7 项（零网络/docker）
python3 preflight/screen/w5_predict_dockerfile_drift.py \
    --projects openh264,flatbuffers,libspng,c-blosc2,hunspell,pcre2   # 已知答案校验：须 1⛔+5✅
python3 preflight/screen/w5_predict_dockerfile_drift.py --min-pool 20   # 全部候选（1 次 docker run）
python3 preflight/selftest/w5_selftest_include_precheck.py  # N34③ 检测器 22 项（含适用边界）
python3 preflight/selftest/w5_selftest_mirror_submodule.py   # N35/N36 共 24 项（全离线）
# N35 爆炸半径复算（542 条 / 32 项目）：
python3 -c "import json,collections,urllib.parse as up;m=[json.loads(l) for l in open('artifacts/repro_manifest.jsonl')];e=[r for r in m if not r.get('skip_reason')];h=lambda u:(up.urlparse(u).netloc or '') if u else '';print('非 github/gitlab =',sum(1 for r in e if not h(r.get('repo_url')).startswith(('github','gitlab'))),'/',len(e))"
# N38 单价复算（git:// >15min vs 镜像 51s）：
time git clone https://github.com/ArtifexSoftware/mupdf /tmp/x && du -sh /tmp/x
python3 -c "import sys;sys.path.insert(0,'.');import build_orchestrator as B;print(B.precheck_includes('openh264','https://github.com/cisco/openh264.git','58576925544e',verbose=True))"   # 已知答案：须报缺 codec_def.h
# 积压重跑（钉版路线 = 未修复版本；--sort 默认已改 fixed_first）
python3 run_repro.py --only-osv <积压 id> --static-check --no-degenerate-only \
    --static-check-limit 100 --max-builds 60 --min-free-gb 4 --run-id <id>
python3 run_repro.py ... --stop-frac 0 --run-id <id>   # 多项目轮次：N12 跨项目对照
# 恢复被误删的归档并校验 bit 一致（N30 事故的善后姿势）
python3 build_orchestrator.py --manifest artifacts/runs/<run>/manifest.jsonl \
    --out artifacts/build_records.jsonl --state artifacts/state.json --stage 2 \
    --only-osv <OSV> --commit-override <OSV>=<pinned_commit> --architecture x86_64

# ── W5 N12 生产对照（同一条 crash、同一批缓存构建 → 只花 ③ 的秒级开销）──
python3 run_repro.py --projects c-blosc2 --only-osv OSV-2020-2184 --run-id <idA> \
    --no-prune --min-free-gb 4                       # 默认 --stop-frac 0 → 走完 3 格 + shadow
python3 run_repro.py --projects c-blosc2 --only-osv OSV-2020-2184 --run-id <idB> \
    --stop-frac 0.6 --no-prune --min-free-gb 4       # 开启 → depth1 即停、省 2 次构建
python3 -c "import json; [print(json.loads(l)['osv_id'], json.loads(l)['stop_reason'], [(c['depth'], c['tier'], c['frac_stop_would_fire']) for c in json.loads(l)['results']]) for l in open('artifacts/runs/<idB>/walkback_trace.jsonl')]"


# ── W3 镜像污染自愈（gate 第⑤条现在自动做；手工复现用）──
docker rmi gcr.io/oss-fuzz/harfbuzz:latest
python3 infra/helper.py build_image --no-pull harfbuzz     # 必须 --no-pull，否则 raw_input EOFError
docker run --rm --entrypoint bash gcr.io/oss-fuzz/harfbuzz -c 'ls /src/*crfuzzer* | wc -l'   # 应为 0
```

---

# 7. 变更历史与底本索引

**本文只留结论；每轮的完整论证过程（观测→假设→演绎→检验→评价）在对应底本里。**

| 轮次 | 日期 | 一句话 | 底本（`archive/`，不再维护） |
|---|---|---|---|
| 设计初版 + 预飞修订 | 2026-09-07 | M1–M12 + 审计 A/B/C 推翻 10 条原决策 | `2026-09-07-crash-reproduction-pipeline-design.md`（R17 快照）、`2026-09-07-preflight-measurements.md`（R17 快照） |
| R1–R15 | 2026-09-07 | 复算 + 补测，消灭口径污染 | 同上（第五步） |
| R16 | 2026-09-08 | 全量扩面 → 增量循环；缓存键加 commit | 同上（第六步） |
| R17 | 2026-09-08 | 缓存路径含 commit、`--max-builds`、首轮=标定轮、append-only | 同上（第七步） |
| R18 | 2026-09-08 | HEAD 分量用解析的上游 SHA；归档归 ② | 同上（第八步） |
| **P0** | 2026-09-08 | 首次真实构建+复现；off-by-one → strict 改子序列 | `2026-09-08-p0-environment-report.md` |
| **P0-B** | 2026-09-08 | `fixed^` 主路径打通；首个 strict；N3/N4/N5 | `2026-09-08-p0b-report.md` |
| **P0-C** | 2026-09-09 | 代理三调用点全覆盖 → N5 关闭；三处文档修正 | `2026-09-09-p0c-report.md` |
| **W1（精简前全文）** | 2026-09-09 | 精简重构前的 2,063 行全文快照（含设计/预飞 R18 全文 + 五份报告逐字全文 + W1 报告全文） | `2026-09-09-DELIVERY-fulltext-snapshot.md` |
| **W6** | 2026-09-30 | **N75 `--sort fixed_first` 语义反转**（默认值实际表现为 `no_fixed_first` → 配 `--limit` 系统性挑中最差一批，按 45.7%/6.7% 折算预期产出 **0.4→2.7 条 ≈7×**；W5 那次「根因修正」只改了默认值字符串+加反转，在升序下等于没修）+ 新增 `w6_selftest_sort_direction.py`（TDD 先 RED 后 GREEN，17 套自测全过、审计 0 红线、重放抽验通过）。同轮：`mutator_create/` 目录重构（建 `README.md` 含**依赖图与误删防范**、`docs/`、`tools/`；删 `pattern_analysis/workspace` 1012M 陈旧 CPG 等）、腾磁盘 5.1G→12G（`driver_create/source_code` 6.4G 经确认为**可再生克隆缓存**且 35 项全部 >30 天未动）、写出 LLM 指令级模式抽取设计规格。**无独立报告文件**：全部内容在本文 §4.66 与 `mutator_create/docs/specs/2026-09-30-llm-insn-pattern-mutator-design.md` | 本文 §4.66 |
| **W5** | 2026-09-14 | 销两笔旧账 + 四道护栏 + 扩样本 + 选镜像筛选：**N12** 离线回放（0 构建）→ 实现但**默认 OFF** + shadow 常开 + 预注册翻转判据；**N16** 离线注入验证 **8/8**（「重跑一次」待办**作废**）；**N25** 日志覆盖销毁证据 → 轮转（生产已拦到 1 次）；**N26** manifest 覆盖护栏（生产拦下 3790→5 行）；**N27** 预检自身三缺陷（误报×2 + 漏检×1）+ 已知答案回归固化；**N28** 第三方 URL 已死 = 老 commit 主导失败模式；**N29** 证据分级。扩样本 19 条 → 累积 **12 strict + 13 medium + 3 loose**、复现 **28/151**；筛选淘汰 4 项目、推荐 **libredwg**。**第二轮**：92 条「跑错版本」的积压重跑（chunk1 **23/23** + chunk2 **19/23**）→ **累积复现 28→70 条（46.4%）、39 strict**；根因 = **排序键与 W3 路由错位**（92 条位于默认序 196–2996 位、历轮 `--limit ≤30`）→ 默认改 `fixed_first`；**N12 按预注册判据翻转默认**（n=11、损失 0；11 条全 c-blosc2 → 跨项目未证，另跑对照）；**N30** 新回收路径绕过保护集、删掉 W4 已交付的 strict 证据（已修 + **5/5 sha256 逐字节恢复**）；逐条回收使 72 次构建下归档基本不涨。**12 个自查缺陷 + 一次误判自纠 + 一次差点错投 + 一次自己造成的证据损毁与恢复**，全过程留痕。**四块跑完**：92 条积压 → **75 条新复现**、累积 **103/151 = 68.2%**（44 strict）；**N16 生产 2/2 成功**（账已销）；N12 翻转后首次生产触发在 md4c，**但跨项目证据仍缺**（hunspell 产生 0 候选 → 如实记为「没有可检验的样本」）。**第三轮**：三次新项目尝试全部失败（libredwg 不可行 / opensc 0/3 / libspng 5%）→ **4 试 0 中**，筛选升级 **v2**（加构建体量维度、确立探针流程）、**N31/N32**（「crash 年份」直觉被否证，本项目第 5 次「模型输给实测」）。**第四轮**：openh264 探针 **0/3** → 暴露 **N33**（era-retry 对「当期 Dockerfile 包已下架」结构性失效）与 **N34**（预检第三盲点：C++ `#include`），并修掉分类器「era 段压过首试真因」的缺陷（N28③）。**W5 新项目 5 试 0 中** → 结论：规模化撞的是**基础设施墙**、不是采样墙；真·积压已穷尽。**收尾**：真·积压**归零**（并修掉一个会误报的度量口径，回核确认当初 92 条没算错）；**UBSAN 零正样本**现在有了确切原因（唯一候选是 N6 退化 → 禁钉版）。**收尾**：新增**交付面审计**（复现记录表自洽性 6 组不变量）+ **牙齿测试**（注入 4 类违规全被抓）→ 真复现记录表 **0 条红线违反**；牙齿测试**抓到审计自身的漏检**（`n_recovered_frames` 恒 None 使整段判据失效）。**第五轮**：硬骨头重试（`--max-depth 6`）→ **3 条翻 strict**、累积复现 **106/153 = 69.3%**、**strict 47**；确立「默认 depth 3 + 只对残差深重试」流程（全复现记录表仅 0.9% 需 depth>3）；**架构假设被否证**（2 条 i386 在正确架构下 6 格全 none）。**第六轮**：N33 **离线预测器**（已知答案 1 真阳/5 真阴/0 假阳/0 假阴）+ 修 N34 盲点② → **libxml2 从 ⓘ 翻 ⛔**（省下镜像+探针）；筛选终局：**无 ✅ 级候选**、⛔ 5 个、⚠ 6 个、ⓘ 2 个。**第七轮**：**N34③ 检测器**（fuzzer 源码 `#include` × 该 commit 的 `-I`/根）—— 已知答案对上真凶（openh264 离线报缺 `codec_def.h`），但 8 个候选全部 `no_sources` → 适用边界窄、0 新增淘汰，按 N29 显示「不适用」。**第八轮**：**mupdf 探针**（复现 +0）→ 挖出 **N35**（非 github 的 repo_url 让 walk-back 零构建静默失败，**实测挡住 542 条 / 17.3% / 32 项目**）与 **N36**（预检第 4 盲点：raw 端点看不见 submodule，**一次挡死 mupdf 37 条**），两者都已修并回归（11 真报全中 / 误报 0）；**N37** 构建源换镜像**实测无效**（`--repo_path` 指向镜像内预烘焙 shallow 克隆）；最终撞上 **N38**（慢速 `git://` + shallow 预克隆 → 单格 `TIMEOUT 3600s`、3 格 240.2min / 0 复现，修复被两条硬约束挡住）→ **判 mupdf 不可行**、**新项目 6 试 0 中**。附带修掉 `--help` 一直是坏的（argparse `%` 未转义）。**第九轮**：为回答「怎么看一条复现」写了只读查看器 `show_repro.py`，**它当场暴露 N39**（不剥 C++ 签名 → **17 条 hunspell medium 实为 strict**、tier 应为 64/19，并**推翻 §4.44 一个结论**；未修待定）；顺带查出 **N40**（`logs/reproduce/` 一直被静默覆盖，**N25 只修了 build 侧**：113 条多轮 crash 里 110 条只剩 1 份日志）→ 已修（轮转实现移进 `repro_common` 单一权威，自测 +7 项）。**第十轮**：归档布局两问 —— `.aff`/`.dic`/`.options` **是运行时依赖不是垃圾**（0.02%；W2 曾因缺 `.bfbs` 把 SIGILL **误记成 10 条 loose**）；物理按类型重排**不可行**（**6/84 归档跨多类型** + 复现记录表路径 append-only）→ 改**符号链接视图** `by_crash_type/`（11 类/106 条，**经链接重放实测成功**）；顺带挖出并修掉 **N41 删库地雷**（保护集字符串比对，6 处改 `realpath`）。**第十一轮**：用户质疑「重放不是需要二进制吗？你不应该把他们删了」→ **质疑成立**，我此前是用「信息没丢（可 bit 级重建）」偷换「能力没丢（重放要二进制在场）」。✅ 复算：重建 **64 个归档 / 72 条 / ≈1.7h / ≈2.8GB / 缺镜像 0 个** → 付得起；而「非删不可」的依据（3,093 × 48MB ≈ 145GB > 100G 磁盘）**只在跑满队列时成立**，而新项目 6 试 0 中、根本跑不满 → **`--purge-on-verify` 默认由开改关**，并新增 `rebuild_archives.py`（`--commit-override` 精确重建 + sha256 逐个 bit 级校验）。另按用户要求把 `by_crash_type/` 改成 **commit 下挂 OSV 层**，使「一条 crash = 一个自包含文件夹」（`binary`/`testcase`/`report.log`/`INFO.txt`），并**实测从该文件夹用相对符号链接重放成功**。**第十二轮：libavc 打通 —— 新项目 7 试 1 中**：① 全量重建 **64 个归档** → **✅ 498 个文件 sha256 逐个一致、0 不符**（bit 可确定性首次拿到全量证据）；② **N42 Gitiles 解析器**（剥 XSSI、`parents` 是字符串数组、`~d` 逐级走 `parents[0]`、`_raw_url` 走 `?format=TEXT`）→ **解锁 googlesource 系 112 条且不需要镜像**，自测 48 项 + 已知答案逐字对上；③ 离线筛 92 条 → **libaom 0/14 ⛔ 淘汰（没花镜像钱）**、**libavc 40/43 (93%) 选中**；④ 探针 **3/3 / 5.6min** → 整池；⑤ 中途 **N43**：分类器漏识别 `does not exist in current branch` → 误标 `compile_error` → **早停封项目、误伤 33 条**（而同轮已试 10 条里 7 条成功 = 直接反证），修两处后**重跑 33 条 → 29 复现（88%）**。**复现 106 → 139、strict 47 → 63**，c-blosc2 占比 58%→44%，`T_strict` **首次有区分力**（0→3 个刻度样本）。另修 **N44**（`httphttp403` 双重前缀）。**第十三轮：libhevc + libwebp 打通、项目数 7 → 9** —— 前置检查（N28 外链全 200 / N38 全量 https 克隆 / N33 apt 包 0 不可安装 / N42 解析通）后建镜像，libhevc **10/28**（4 strict + 6 medium、6.8min）、libwebp **3/10**（2 strict + 1 medium、29.5min）；**预检预测被实测双向印证**（libwebp 预测拦 2 → 实拦 2）。**⭐ 首次拿到 MSAN flaky 重试的生产证据**：`retry_count>0` 从恒 0 变 **9 条**（全 memory），其中 `attempts=[0,1]` 的 2 条是**重试救回的复现**，而 `[0,0,0]` 的仍如实记 none → 销掉一笔挂了两轮的账。**复现 139 → 152、strict 63 → 69、memory 10 → 17**；c-blosc2 占比降到 **40%**；并提炼出「**全量 https 克隆是新项目成功的必要条件**」（9 试 3 中，失败分别死于 N28/N33/N38）→ 可作离线硬前置。**第十四轮：用户一个结构问题拽出 4 个真缺陷（N45–N49）** —— 「一个 OSV 为什么有这么多二进制」查出：⑤ 连接键优先级反了（`b_by_osv` 取到**最后一次**构建，而 walk-back 对 loose 会继续下探）→ 2 条复现记录表指向**没崩的那格**、按 INFO.txt 重放得 **exit=127**；libFuzzer **超时被当复现**（DEDUP_TOKEN 全是引擎告警回调帧）→ 虚高 1 条；`exit_code` 不可作判据（3 条 libwebp exit=0 却是真 ASan 崩溃，**内容判崩救了它们，否则 libwebp 是 0/10**）；审计只查「是不是目录」故报 0 红线。**全部修在根因上**（⑥ classify + ④ verify_one + ⑤ merge + 审计 3 条红线 + 交付布局），用修好的流水线重跑那 2 条并**实测重放 exit=1 + ASan ABRT** 收尾；交付视图 `binary` 收窄成**单个 driver**、整棵树保留为 `out/`。**复现 152 → 151**（少的是超时假复现）、tier strict 69 / medium 51 / loose 31 / none 86、**driver 在盘 151/151**、151 条目断链 0。**第十五轮：交付视图重做 + 首次全量重放验收** —— 用户第二次指出「一个 OSV 为什么有多个二进制」，实测确认 N49 没解决（`out/` 仍暴露 2～17 个兄弟 target；151 条里 132 条含 1,497 个无用文件）。改为只放**精确最小重放包** → **151/151 每条恰好 1 个 ELF**（128 条整个文件夹只有 5 个条目），硬链接 → **额外 0 字节**。过程中**推翻了我自己写进文档的一条结论**（「只给 driver 会重放失败」——`ldd` 无 `libclang_rt.*.so`，ASan/MSan 静态链入；14 组合真跑全崩，那条是 W2 flatbuffers 个案的过度泛化，还把 N49 带偏了）。**N47 悬案破案**：libwebp 的 target 是 shell 包装脚本、最后一行 `chmod -x` → 退出码取 chmod 的 0。**N51**：`replay.sh` 必须照抄复现记录表 `runtime_limits`，漏了 `-rss_limit_mb=2560` 会让 2 条 **strict** 重放成 OOM。**N52 首次全量重放验收：151/151 = 100%**（首轮 148、2 条第 3 次、1 条 i386 第 8 次 / 崩溃率 12%；该条崩时给出的正是**期望**类型 `global-buffer-overflow`，是「loose 里混着同一 bug 不同表现」的第一个直接证据）。**本轮 7 个自身缺陷全部由「真跑一遍全量交付物」抓出，无一由静态检查发现。****第十六轮：N39 落地 + N53 红线** —— `strip_cpp_signature` **只挂 observed 侧**（不动 AST 提取的权威实现 `normalize_one_frame`，否则等于改 ground truth），11 例已知答案全取自复现记录表真实帧 + 端到端一例；**先干跑量影响（升档 17 / 降档 0）再落账**，重跑 ④⑤ 追加更正行 → **strict 69 → 86**（占复现 45.7% → **57.0%**）、medium 51 → 34。18 个候选里 1 条不升是**对的**（`OSV-2022-899` 的 R 首帧是模板类型名、本次该位置是 `strlen`）。⚠ 同时明确口径：**N39 提高的是 strict 的数量，没有验证 `T_strict=1.0` 这个阈值本身**（升档 17 条 subseq 全是 1.0，刻度样本仍 3 条）。**N53**：把用户两次指出的「一个 OSV = 一个二进制」写成审计红线并做牙齿测试 → ✅ **151/151 每条恰好 1 个 ELF**。**第十七轮：一个静默回显 bug 造出两个假结论（N54–N57）+ 分类器过宽（N58）+ UBSAN 缺口破了（N59–N60）** —— `resolve_commit_meta` 解析失败时**把输入原样回显**成已解析 SHA（`error=None`），于是 ② 把 `<sha>~3` 传给 infra、infra 的 `get_current_commit() != commit` 必然失败、分类器落 `compile_error`、**N43 早停封掉整个项目** → kimageformats 假淘汰 + 离线预检假放行。修 4 处（SHA 校验 / 预检拒垃圾 / 并入 commit_not_found / 新增 GitLab `parent_ids` 解析）。**又推翻我自己写进文档的一条规律**：§4.57.4「必须全量 https 克隆、无 `git://`、无 `--depth 1`」逐条实测全错（`git://` 可达；infra `checkout_commit` 自己会 `fetch_unshallow`）→ 真判据是**实测 unshallow 吞吐**（ghostpdl ≈29 KB/s ⛔ 才是 ghostscript 192 条大池的死因）。**N58** 分类器裸 `-Werror`/`unsupported`/`ninja-build` 会命中**成功探针行/Qt 路径名/apt 安装行**，收紧并新增 `era_dep_drift`（复判历史 9 条，**早停行为完全一致**，只是记对了原因）。**带证据淘汰** radare2（C 头被当 C++ 编）· kimageformats（镜像烘当前 Qt/ECM vs 2021 commit、era-retry 救不了因为 prepare 脚本来自 master）· matio（0/14）· ghostscript（29 KB/s）。**⭐ unicorn 打通 → 第 10 个项目**，分层探针 3/3，**UBSAN 长期 0 正样本的缺口破了**。**N59** 归一化两处缺陷（十六进制地址被当类型的一部分、UBSan 具体名被压成泛化）→ 2 条 loose→medium。**N60** 审计盲区（PRUNED 条目不写 INFO.txt 于是对审计不可见 + `binary_pruned` 豁免）→ 补 2 条红线。⚠ **给「bit 级可重建」加了限定**：libavc 重建 5/5 文件 sha256 不符（此前 498 文件全一致的是 c-blosc2/hunspell/pcre2/md4c），但重建件实测 7 次崩 6 次 → 功能没坏、只是不能声称 bit 一致。**第十八轮：磁盘分级保留策略（N61）** —— 用户批准「自动回收 + tier 分级」，但先量字节去向发现两件事：① 交付视图是**硬链接**指进归档的，「删归档路径」对交付必需的 1.50G **根本不释放空间** → 策略应是「瘦身到交付所需并集」而非「删旧归档」；② **「按 tier 分级」被实测全面压制** —— `tier=strict` 只回收 4.38G，而 **`reuse`（只保护服务 >1 条 verified 行的归档）回收 7.09G、只留 698M 真有用的**，因为 119 个被引用归档里 **100 个只服务 1 条**（兄弟文件 6.80G、复用价值≈0）。执行后**可用 3.0G → 13G、归档 8.5G → 2.2G**，事后自校验（154 条目每条恰好 1 个 ELF、断链 0）+ 审计 0 红线全过；已接进 `run_repro.py --post-clean`（默认开）。两类动作两种门控：纯废物（build/ 中间产物 1.27G、悬空镜像 250M）无条件清，动归档才受阈值门控。⚠ 顺带量出 **unicorn 整池跑不起**（单归档 104～124MB、整池估算 37GB，而 post-clean 只在轮末触发）→ 改**定向小批**（UBSAN+MSAN 6 条），既控磁盘又补最缺的 sanitizer 覆盖。**「期望值 unknown」判据经用户裁定保持现状**（17 条结构性拿不到 medium+，只记录不放宽）。**第十九轮：轮中水位线（N62）→ 误删在飞归档（N63）→ 磁盘写满事故（N64）** —— 一条完整的「加安全机制却暴露两个更深的坑」链条，每步都有实测数字。N62 水位线✅生效（触发 3 次、磁盘 6.7G↔12G 震荡、该批产出 7 条复现）；N63 轮中清理**删掉本轮在飞的归档**（`needed_map` 只看复现记录表、在飞的行还没落账 → 被判孤儿整目录删）→ 4 条刚复现的 crash 归档被删、审计 3 条红线、15 个归档里 14 个已删；修 `--protect-since`。N64 修完更糟：**保护 7.29GB 本身把盘占满** → 可用空间掉到 **68KB（100%）**、进程僵死；修 `--disk-hard-floor-gb` 硬底线优雅停轮；恢复后可用 2.0G→**9.2G**、归档 13G→**5.0G**、交付 162 条全部自包含、审计 0 红线。**第 19 套自测**（专抓 Python 静默生效的缺陷）当场抓到 2 个 `--help` 崩溃：我自己刚写的「100% 满」、以及 **W3 潜伏至今**的 `manifest_builder.py`「45.7% vs HEAD 6.7%」（从来没人跑过它的 --help）。**复现 156→162、unicorn 5→11**。**无独立报告文件**：全部内容在本文 §4.36–§4.63 | 本文 §4.36–§4.63（+ `artifacts/runs/w5-*/`、11 个 `preflight/w5_*` 脚本） |
| **W4** | 2026-09-10 | 数据完整性两道防御（自测 12/12）+ 4 归档重建 20/20 逐字节 + 静态 check 降 advisory·② 走策略 A（代码变短）+ 构建前预检与早停 + 扩样本 11 条 + i386/负对照两实验；N22–N24；5 个自查 bug。**无独立报告文件**：全部内容在本文 §4.25–§4.35 | 本文 §4.25–§4.35（+ `artifacts/runs/w4-*/`、`prune_audit.jsonl`、`dataset_guard.jsonl`） |
| **W3** | 2026-09-10 | 改路由（has_fixed 跳过 Stage1，R16 的 HEAD-first 被实测推翻）+ 归档裁剪默认化 + 修 N12/N17/N16 + i386/镜像两次单发实验 + 扩样本（27 条 / 30 次构建）；W1 策略模型作废；N18–N21；13 个自查 bug。**无独立报告文件**：全部内容在本文 §4.14–§4.24 | 本文 §4.14–§4.24（+ `artifacts/runs/w3-*/`） |
| **W2** | 2026-09-09 | Phase0 四遗留（`osv_events` 横向审计 / `pinned_queue` 排序 / N6 个案复核 / `walkback_depth_actual`）+ 写 **②③④⑤⑥** + **首轮真跑**：129 crash、54 次构建、**12 复现（3 strict）**、端到端可构建率 **90.7%**、era 省 **49.5%**、已知答案 **3/3 逐字节**、负对照 **8/8**、**N7–N17**、修掉自己 **13 个 bug** | `archive/2026-09-09-w2-report.md`（md5 `ca67ed45…`，**内容已全量并入本文 §4.5–§4.13**） |

> **W2 与「单一交付文档」约定**：本轮任务显式要求另出报告文件（该报告自身的 §1–§10 结构），故先写了 `2026-09-09-w2-report.md`；**随后按约定把其全量内容并入本文 §4.5–§4.13**（§8「N7–N17」因与本文 §3 重复而未重复并入，交叉引用已重定向），原文快照冻结为 `archive/2026-09-09-w2-report.md`。**根目录下只有本文一个交付文档**，与 W1 约定一致。
> 并入后做过**内容丢失核查**：报告 775 个 distinctive token（sha / osv_id / 带单位数字 / 反引号标识符 / N 编号 / 文件名）→ 本文覆盖 **751**，缺的 24 个逐项查过：4 个是正则跨表格单元格的假阳性、其余是「已在 §3/§6 以等价表述存在」（如 `4.3%`↔`5.2%` 是同数不同分母、日志份数与 fixtures 数已补进 §1.4）。**教训沿用上一轮：合并/精简后必须对着被合并的那份文件逐项核，不能只比新旧两版本文。**
>
> **W1 精简说明**：本轮把本文从 2,063 行压到当前长度——**删的是历史叙述与逐字全文重复**（每轮「原表述→为何改→改成什么」的层层叠加、以及 P0/P0-B/P0-C 与 archive 底本逐字重复的部分），**保留的是全部当前有效规格、全部实测数字、全部结论与其证据出处**。需要看某轮的完整推理 → 查上表底本。`archive/README.md` 有各底本的状态说明。
> **今后约定**：每轮汇报的内容**直接写进本文对应章节**（新实测 → §2、新发现 → §3、规格变更 → §1、进度 → §0.2），**不再新建交付文档**；`preflight/` 只放**脚本 + 逐条原值 JSON**（可复算的数据，不是文档）。

---

# 8. 约束遵守声明

- ✅ **每个数字附复算命令或 `file:line`**；🅗 显式标注并给可证伪判据；ⓘ 标不可得；不用估计填实测栏；不用 🅗 推翻 ✅；不用单侧测量给双侧定级（R3 教训）；不用「单例率降 0.2pp」单侧证据下「无需去重」双侧结论（R2-extra 重述证据边界）；**不用未测量的取舍换确定的数字**（W1 不采纳策略 C 的理由）。
- ✅ **主树 `/root/gyx/oss-fuzz` 只读**：每轮结束核对 `git status --porcelain | wc -l` = **550**（driver_create 研究线的工作状态，含其 `M infra/helper.py`，**不还原、不清理**）。
- ✅ **不动 driver_create**；worktree 改动只在 `repro-patches` 分支的 `infra/` 三文件（本轮已提交固化）。
- ✅ **测量脚本不跑 docker、不改 oss-fuzz**（W1 及之前）；需要网络的只有 diff 抓取（`.patch` 端点，**0 次 API、0 次 clone**）。
- ✅ **W2 起允许跑 docker / 联网**（本轮任务授权）：54 次真实构建 + 143 次复现执行 + 8 次负对照，全部经 worktree 与宿主代理；**未访问 gcloud**（不可用）；`infra/` 三补丁 md5 全程不变（`f5092d0a3f2a6909`）；结束时 worktree `git status --porcelain` = **空**、主树仍 **550**、driver_create **0** 脏项。
- ✅ **模块边界**：W1 写 ⓪①；**W2 写 ②③④⑤⑥**（⑦ `recover_targets.py` 仍未写）。
- ✅ **文档同步不分叉**（R17-3）：本文是**结论与规格**的唯一可编辑底本；W2 的逐条数据表与推理过程在 `2026-09-09-w2-report.md`（本轮任务显式要求单独出报告，见 §7 说明）；历史全文冻结在 `archive/`。
- ✅ **W5 的约束遵守**：主树 **550**（未变）、worktree `repro-patches@07522dc0e` **干净**、`infra/` md5 `f5092d0a3f2a6909`（未变）、`driver_create` **0** 脏项、磁盘 **8.9G**（本轮建过 libredwg 2.51GB / opensc 2.3GB 两个镜像，证不可行后**已删**，另建 openh264 2.9GB 探针 0/3 后亦**已删**，并清掉 libtiff/libspng/harfbuzz/pcapplusplus/dangling）；**未新建任何镜像**（选镜像改用离线筛选，把 2.2GB 的赌注换成证据）、**未跑全量 3,093 队列**、未改任何 Dockerfile/build.sh；① schema 只**新增** `walkback_stop_reason`；本轮 22 行 dataset（19 条扩样本 + 3 行接线验证）均 `run_status=run`、**未触发 ⑤ 单调性护栏**（无 verified 被降级）；轮末裁剪 `M=0` 通过。详见 §4.40/§4.41。
- ✅ **W5 新增的自查纪律**：① **「数字变了」不等于「数据被毁了」**——先查**产生数字的命令**（flag / 输入路径），再查数据；本轮我正好搞反了一次，全过程记在 §4.39；② **计数口径要防嵌套重复**（5 次触发 ≠ 5 个独立样本，实为 3 条 crash）；③ **省资源的优化不得以关闭测量通道为代价**（N12 默认 OFF 的真正理由）；④ **声称「可复算」的东西必须真落成文件**（② 分类器自测此前是内联 heredoc）；⑤ **护栏要挂在唯一写盘点上**（`run_cmd` / `write_outputs`），挂在调用方就会漏。
- ✅ **W4 的约束遵守**：主树 **550**、worktree `repro-patches@07522dc0e` **干净**、`infra/` md5 `f5092d0a3f2a6909` **未变**、driver_create **0** 脏项、gate 五条件每次都跑（本轮未触发镜像重建）、**未改任何 Dockerfile/build.sh**（N19 的处置是构建前预检+分类+早停，不是改上游脚本）、**未加通用架构维度**（只在 ⑥ 加 `--match-job-arch`、复用 W3 已有的 ② 缓存键/归档路径分量，① schema 不变）、磁盘 **8.3G**。详见 §4.35。
- ✅ **W4 新增的自查纪律**：① **防御要治根因**——N20 修在裁剪侧只是治标，根因是「append-only 复现记录表里最新一行 = 当前状态」，所以写入侧也要设闸；② **交叉校验必须换字段**，用同一字段自查等于没查；③ **删除类操作默认 dry-run**，真删要显式要求；④ **省时间的优化要核算自己的成本**（N24：预检一度比它省下的构建还慢）；⑤ **放宽判定条件前先量误报**（N23：预检候选一放宽就抓进 URL/生成物，误报比漏报更糟）；⑥ **「跳过」的原因必须能与「0 候选」区分**（否则变量遮蔽这类 bug 会静默吃掉一整段验证）。
- ✅ **W3 的约束遵守**：主树 **550**、worktree `repro-patches@07522dc0e` **干净**、`infra/` md5 `f5092d0a3f2a6909` **未变**、driver_create **0** 脏项、gate 五条件每次都跑（本轮触发自动重建自愈 1 次、抓到真脏 1 次 = N18）；磁盘 13G → **9.5G**（wolfssl i386 镜像 ~4G 已 `docker rmi` 回收，归档 782→278MB）。详见 §4.24。
- ✅ **W3 新增的自查纪律**：① **`pkill/pgrep -f` 的模式会匹配到自己的命令行**（W3 因此杀掉了正在打补丁的 shell，补丁从未落盘、我却以为修好了 → 同一个错重复出现才发现）；② 分类器/解析器读日志**不能截断**（末 400KB 会切掉首试的真错）；③ 任何「按最新一行算」的保护逻辑都要想清楚**坏行**的后果（N20 因此不可逆删了 4 个 verified 归档）；④ 负对照的前提本身也要验证（N21）。
- ✅ **已知答案优先**（W2 的教训）：本轮 13 个 bug 里 **11 个**是被「已知答案回归」或「去翻原始日志」抓到的，其中 2 个（docker exit=125 当复现、`Executed…in N ms` 判据误杀所有真崩溃）**会直接污染数据集**且当时看起来「结果合理」。故 ③④ 现在**每次运行前强制自测**（4 段真实 stderr fixture / 4 个打分器已知答案），不过就退出 3。「结果符合预期」不是验证，**只有已知答案才是**。


# 9. 目录索引（`artifacts/runs/` 与 `preflight/` 逐项说明）

> 本节回答「这两个目录里每个东西是什么、还有没有用」。**顶层只留仍在交付证据链上的轮次**；被后续轮次取代的早期尝试移进 `artifacts/runs/_archive/`（**不删**，因为里面还带着当时的 observations/verifications 原始结果）。

## 9.1 `artifacts/runs/` —— 每轮一个目录，存该轮的推导链

每个目录里的固定 7 件：`manifest.jsonl`（①输出）· `build_groups.json`（①分组）· `observations_all.jsonl`（③输出）· `observations_stage2.jsonl`（仅钉版部分）· `verifications.jsonl`（④输出）· `walkback_trace.jsonl`（每格试了什么/为何停）· `run_meta.json`（本轮参数与汇总）。`repro_dataset.jsonl` 就是由这些汇总而来。

### 顶层 27 个（仍在证据链上）

| run 目录 | 范围 | obs | 复现 | tier | 构建 | 墙钟 | 入复现记录表 | 体积 |
|---|---|---|---|---|---|---|---|---|
| `w2-p3-final` | md4c,pcre2,hunspell,c-blosc2,flatbuffers,libtsm/address | 125 | 7 | medium7 · none118 | 1 | 3min | 125 | 932K |
| `w2-p4a` | c-blosc2/address limit8 | 8 | 5 | loose2 · none3 · strict3 | 8 | 15min | 8 | 104K |
| `w2-p4b` | pcre2,flatbuffers/address limit5 | 5 | 0 | none5 | 4 | 2min | 5 | 47K |
| `w3-p5-cb` | — | 8 | 5 | loose1 · medium2 · none3 · strict2 | 14 | 18min | 8 | 642K |
| `w3-p5-hb` | — | 2 | 0 | none2 | 6 | 19min | 2 | 474K |
| `w3-p5-msan-ubsan` | c-blosc2,harfbuzz/memory,undefined | 3 | 2 | loose1 · medium1 · none1 | 4 | 13min | 3 | 70K |
| `w3-p5-ubsan` | libtsm/undefined | 1 | 0 | none1 | 1 | 0min | 1 | 9K |
| `w4-stratA` | c-blosc2/address limit10 | 10 | 10 | loose1 · strict9 | 7 | 15min | 10 | 244K |
| `w4-ubsan` | pcapplusplus/undefined | 1 | 0 | none1 | 3 | 9min | 1 | 28K |
| `w5-backlog-final` | — | 7 | 0 | none7 | 19 | 10min | 7 | 47K |
| `w5-backlog1` | — | 23 | 23 | loose8 · medium1 · strict14 | 40 | 56min | 23 | 646K |
| `w5-backlog2` | — | 23 | 19 | loose4 · medium2 · none4 · strict13 | 32 | 48min | 23 | 653K |
| `w5-backlog3` | — | 23 | 22 | loose5 · medium16 · none1 · strict1 | 36 | 45min | 23 | 1308K |
| `w5-backlog4` | — | 14 | 11 | loose3 · medium4 · none3 · strict4 | 23 | 53min | 14 | 466K |
| `w5-expand19` | — | — | — | — | — | 0min | 0 | 57K |
| `w5-expand19b` | — | 19 | 6 | medium4 · none13 · strict2 | 21 | 42min | 19 | 198K |
| `w5-fracstop-B` | c-blosc2 | 1 | 1 | loose1 | 0 | 0min | 1 | 20K |
| `w5-hardretry` | — | 7 | 3 | none4 · strict3 | 33 | 77min | 7 | 232K |
| `w5-libredwgA` | — | — | — | — | — | 0min | 0 | 55K |
| `w5-mupdf-p1` | mupdf | 1 | 0 | none1 | 0 | 0min | 1 | 6K |
| `w5-mupdf-p1b` | mupdf | 1 | 0 | none1 | 3 | 240min | 1 | 6K |
| `w5-mupdf-p1c` | — | — | — | — | — | 0min | 0 | 4K |
| `w5-mupdf-probe` | mupdf | 3 | 0 | none3 | 0 | 0min | 3 | 66K |
| `w5-mupdf-probe2` | mupdf | 3 | 0 | none3 | 0 | 0min | 3 | 15K |
| `w5-oh264-probe` | — | 1 | 0 | none1 | 3 | 4min | 1 | 12K |
| `w5-opensc-probe` | — | 1 | 0 | none1 | 3 | 10min | 1 | 11K |
| `w5-shadow-A` | c-blosc2 | 1 | 1 | loose1 | 1 | 2min | 1 | 34K |

> ⚠ **一个预先存在的溯源缺口**（本轮盘点时发现，**不是归档造成的**）：复现记录表里 `run_id=w5-fracstop-B-refix`
> 有 **1 行**，但 `artifacts/runs/` 下**从来没有过**这个目录 → 它的中间推导链（observations/verifications）不在盘上。
> 该行**仍有完整证据**：崩溃报告原文与 testcase 都在（审计「报告缺失 0 / testcase 缺失 0」），
> 缺的只是「复现记录表这一行是怎么从 ③④ 推出来的」那段可复核中间态。**155/156 的 run_id 都能找到目录。**

### `_archive/` 10 个（被后续轮次取代，**保留不删**）

| run 目录 | 为什么归档 |
|---|---|
| `w2-e2e-verify` | W2 首次端到端联通性验证（6 obs / 4 复现），已被 `w2-p3-final`（125 obs）取代 |
| `w2-e2e-verify2` | 同上的第二次（10 obs / 2 复现） |
| `w2-p3a` | W2 Phase3 首次尝试（118 obs / 10 复现），未入复现记录表；结论并入 `w2-p3-final` |
| `w2-p3a-fb` | flatbuffers 专项试跑（12 obs / 0 复现） |
| `w2-p3a2` | 同上的重跑（118 obs / 0 复现） |
| `w2-p3b` | W2 Phase3b 试跑（7 obs / 0 复现） |
| `w3-p5-nl` | `not_located` 采样实验，**只有 manifest + build_groups、0 observation** |
| `w3-p5-nl2` | 同上（第二次） |
| `w3-p5-nl3` | 同上（第三次） |
| `w5-mupdf-probe3` | mupdf 第三轮探针，**被 shell 超时杀掉**（见 §4.52.5 操作事故），只留下 manifest |

## 9.2 `preflight/` —— 按「活的 / 一次性历史」分三个子目录

**[W5 整理]** 原来 45 项平铺在一层、名字还都是 `w2_phase0c_degenerate.py` 这种，没法看。现按**是否还会被反复运行**分三类，顶层只剩 3 个目录 + `fixtures/`：

```
preflight/
├── selftest   18 项   ← 17 个 .py（实测 17 套全过）+ 1 个 .json，会反复跑
├── screen      4 项   ← 还在用于决策的筛选/预测仪器
├── history    24 项   ← 一次性测量脚本，结论已进本文
└── fixtures/   5 项   ← repro_runner.py --selftest 的输入样本（活的）
```

> **[W6 校正项数]** 原记 selftest 17 / screen 5 / history 25 / fixtures 4。
> W6 实测为 **18 / 4 / 24 / 5**：① selftest **+1** 是新增的
> `w6_selftest_sort_direction.py`（N75）；② screen **−1**、history **−1** 是因为
> W6 清理了各子目录下的 `__pycache__/`（原计数把它们也算进去了）；
> ③ fixtures 原记 4 实为 5（`ubsan_exit0.stderr` 等），属**文档旧有误记**，本次一并更正。
> **教训**：目录项数这类数字必须由脚本实测，不能手抄 —— 手抄会同时犯
> 「多算 `__pycache__`」和「少数 fixture」两个方向相反的错。

> ⚠ **移动打断过两处写死的路径，已修并加兜底**（自测立刻抓到，14 套一度全红）：
> ① `repro_common.py` 按「不重写、逐字复用」原则**从 `r2_r5_r6_r7_recompute.py` 用 AST 提取 `normalize_frames`**，路径写死在 `preflight/` 顶层 → 改为**在 `preflight/` 下递归查找**，且要求**恰好 1 个命中**（0 个=权威实现丢了；≥2 个=两份实现会分叉，违反设计原则）；
> ② `repro_runner.py` 的 `FIXTURES` 同样写死 → 同样改递归兜底。另修 `w5_backlog_report.py` 的 `ROOT` 少包一层 `dirname`。
> **教训**：`fixtures/` 一开始被我判成「无脚本引用的孤儿」——因为我只 grep 了 `preflight/*.py`，**漏了根目录的流水线文件**。跨目录引用必须全仓 grep。

### `selftest/` —— 18 套验证电池（本文 §6 的复算命令都指这里）

| 文件 | 项数 | 作用 |
|---|---|---|
| `w4_phase1a_selftest.py` | 15 | W4 Phase 1a：两道数据完整性防御的**自测**（任务明确要求「构造一次降级写入、构造一次会删 |
| `w5_audit_delivery.py` | 11 | W5：**交付面审计** —— 对 `repro_dataset.jsonl` 的 verified 子集做不变量检查。 |
| `w5_backlog_report.py` | 0 | W5 积压重跑的逐块核查 + 累积汇总（可重复跑）。 |
| `w5_phase1_replay_stopfrac.py` | 5 | W5 Phase 1：`frac≥阈值 即停`（N12 的 🅗 改进）的**离线回放** —— 0 次构建。 |
| `w5_precheck_known_answers.py` | 14 | W5：② 构建前预检的**已知答案回归**（把 W4 当时内联跑的验证固化成可复算 artifact）。 |
| `w5_selftest_annotate.py` | 17 | W5：⑤ `annotate_dataset.merge()` 的字段透传自测。 |
| `w5_selftest_audit_teeth.py` | 1 | W5：交付面审计的**牙齿测试** —— 往复现记录表**副本**里注入违规，审计必须抓出来。 |
| `w5_selftest_bo.py` | 18 | W5：② `build_orchestrator` 的两项自测 —— **不碰 docker、不碰真实数据**。 |
| `w5_selftest_classifier.py` | 23 | W5：② 失败分类器 + `_full_log` 的**固化自测**（此前只是内联 heredoc，§6 的「可复算」是空的）。 |
| `w5_selftest_include_precheck.py` | 21 | W5：**N34 盲点③**（C++ `#include` 的头文件在该 commit 不存在）的检测器自测。 |
| `w5_selftest_mirror_submodule.py` | 25 | [W5 N35/N36] 镜像映射 + submodule 守卫 的自测（**全离线**，纯函数 + 替身）。 |
| `w5_selftest_overwrite.py` | 14 | W5：① `manifest_builder` 的**覆盖护栏**自测（新发现 N26）。 |
| `w5_selftest_precheck_sha.py` | 19 | W5：② `precheck_buildscript` / `path_exists_at` 的**误报**自测（两个真 bug）。 |
| `w5_selftest_purge.py` | 24 | W5：**复现完立即删归档**（purge-on-verify）+ 排序默认值修正 的自测。 |
| `w5_selftest_stopfrac.py` | 19 | W5：⑥ walk-back **停止判据**的自测（N12 的 🅗 改进：`frac≥0.6` 即停）。 |
| `w6_selftest_sort_direction.py` | 10 | **[W6 N75]** ① `--sort` 的**方向**自测 —— `w5_selftest_purge.py` 只断言了默认值**字符串**是 `fixed_first`，本套断言其**实际排序行为**（配 `--limit` 时前 K 条是否真有 `fixed_commit`），含两个负对照（sort 不得改集合、`osv_id` 档证明断言非恒真）。真跑 `manifest_builder` 子进程，不用替身。 |

> 另有两套自测在流水线文件自身：`repro_runner.py --selftest`（4，用 `fixtures/`）、`verify_tiered.py --selftest`（4）。`screen/w5_predict_dockerfile_drift.py` 也带 `--selftest`（8）。**合计 18 套 / 242 项。**

### `screen/` —— 仍在用于决策的仪器

| 文件 | 落盘 | 作用 |
|---|---|---|
| `w5_predict_dockerfile_drift.py` | ✅ | W5：**N33 的离线预测器** —— 在建镜像**之前**判断「era Dockerfile 是否会因包已下架而构建失败」。 |
| `w5_screen_v2_buildcost.py` | ✅ | W5 v2：选下一个项目的离线筛选 —— 只用**实测证明有区分力**的维度。 |

### `history/` —— 一次性测量脚本（结论已进本文，保留只为可复算）

| 文件 | 落盘 | 当时测的是什么 |
|---|---|---|
| `locate_sources.py` | — | Step 1: locate data sources, confirm actual paths + counts. |
| `m4_fixed.py` | — | M4: fixed-commit availability in raw OSV cache (_osv_cache). |
| `m_crash_data.py` | — | M1,M5,M6,M7,M8,M9,M10: pure local crash-data measurements. |
| `m_ossfuzz.py` | — | M2,M3,M12: oss-fuzz read-only measurements. NO modification of oss-fuzz. |
| `r1_r13_r14_routing_scale.py` | — | R1,R13,R14: fixed-routing, fixed^ selection rules, repo coverage, revised scale. |
| `r2_r5_r6_r7_recompute.py` | — | R2,R5,R6,R7 recompute (corrected口径). No docker/network, oss-fuzz read-only. |
| `w1_offbyone_sampling.py` | — | [实现 W1] 第一件：OSV `fixed` off-by-one 抽样测量。 |
| `w1_repo_path_scan.py` | — | [实现 W1] 第一件附带项：`repo_path` 假设的静态审计（零成本、否则运行时炸）。 |
| `w2_phase0a_osv_audit.py` | — | W2 Phase 0(a)：`osv_events()` 解析假象的**横向**审计。 |
| `w2_phase0b_queue_order.py` | ✅ `w2_phase0b_queue_order.json` | W2 Phase 0(b)：`pinned_queue` 排序键的**实测选型**。 |
| `w2_phase0c_degenerate.py` | ✅ `w2_phase0c_degenerate.json` | W2 Phase 0(c)：N6 的 53 条退化 range **不要一刀切**——用 W1 现成打分器判退化 sha 像不像 fix。 |
| `w2_phase5_analysis.py` | ✅ `w2_phase5_analysis.json` | W2 Phase 5：把跑出来的数据用掉 —— (a)(b)(c)(e) 四项分析（(d) 负对照另见 |
| `w2_phase5d_negctl.py` | ✅ `w2_phase5d_negctl.json` | W2 Phase 5(d)：负对照（§1.7 升级后的判据）。 |
| `w4_phase4e_negctl.py` | ✅ `w4_phase4e_negctl.json` | W4 Phase 4(e)：负对照改造 —— **HEAD 二进制为默认**，版本感知作补充。 |
| `w5_screen_next_projects.py` | ✅ `w5_screen_next_projects.json` | W5：「下一个该建哪个项目镜像」的**离线筛选**（0 次 docker、0 次构建）。 |

> `w2_phase5e_build.json` 是**孤儿输出**（对应的 `.py` 已不在）；`w5_screen_next_projects.json` 是 v1 筛选的输出，已被 `screen/w5_screen_v2_buildcost.py` 取代，两者都留在 `history/` 作证据。

