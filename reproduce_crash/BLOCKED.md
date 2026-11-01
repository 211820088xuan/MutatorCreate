# BLOCKED —— worktree gate 未通过，② 拒绝构建

时间：2026-10-19T20:35:08

| 条件 | 结果 | 实测 |
|---|---|---|
| ①分支=repro-patches | ✅ | repro-patches |
| ②无未提交改动 | ❌ | M  projects/libredwg/Dockerfile |
| ③07522dc0e 在 HEAD 历史 | ✅ | 是 |
| ④无 dc-injected 残留 | ✅ | 0 |
| ⑤镜像 ndpi 无 dc 注入源 | ✅ | 0（或镜像不存在） |

范围：1 条 crash / 1 个项目

**处置**：不带污染构建。修好 gate 条件后重跑（DELIVERY §1.7 H）。
