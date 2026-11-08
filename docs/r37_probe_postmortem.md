# R37 · 插桩(④)事后分析

日期：2026-11-09
范围：R36 改动 ④ 第四轮。"60 slots 插入成功、编译通过、自检一个 `R36_` 标记都没打"。

## 一、先否掉一个错的诊断

R36 报告里我写的"最可疑"是：

> `_src0` 是 `cat -n` 的输出、用 `raw.split("\t",1)[-1]` 取内容 ——
> 如果某行本身含 tab，取到的是后半段，写回去就丢了前缀。

**这个诊断是错的。** `split("\t", 1)` 的 `maxsplit=1` 保证只切第一个 tab，
`[-1]` 拿到的是第一个 tab 之后的**全部**内容：

```python
'    13\tif (a)\tb = 1;'.split('\t', 1)[-1]   # → 'if (a)\tb = 1;'   前缀没丢
'  1234\t\t\tdeep'.split('\t', 1)[-1]          # → '\t\tdeep'         前缀没丢
```

## 二、两条命令的结果

```bash
docker exec libredwg-exp grep -c 'R36_' /src/libredwg/src/in_dxf.c
  → 0

docker exec libredwg-exp grep -c 'R36_' /src/libredwg_cov/src/in_dxf.c
  → 副本不存在

docker exec libredwg-exp 'for b in /tmp/r36probe/*; do strings $b | grep -c R36_; done'
  → llvmfuzz_probe_multi_a1c96e08149a:         0
  → llvmfuzz_probe_multi_a1c96e08149a_custom:  0
```

## 三、真因

| ① 源码 | ② 二进制 | 真因 |
|---:|---:|---|
| **0** | **0** | **`cp` 没落地，或落到了别的路径** |

`rebuild_probe` 里第一步是：

```python
_sh(f"rm -rf {COV_SRC} && cp -a /src/libredwg {COV_SRC} && cd {COV_SRC} && make clean >/dev/null 2>&1")
```

`_sh` **不检查返回码** —— `rm -rf` 执行了（所以副本没了），
`cp -a`（1.3 GB）失败或没跑完，**代码照样往下走**。

于是后面所有 `cp /exp/_out.c {path}` 都落进一个不存在的目录，
所有 `clang -fsyntax-only` 都失败、被记成 `syntax@...`（或干脆没报），
最后链接的仍是 `libredwg.a` 里**上一次**编出来的 `.o` —— 二进制里自然没有 `R36_`。

**而"60 slots"是 python 侧自己的计数**（`len(slots)`），不是编译器的确认。
这两个数在前四轮里一直被当成同一件事。

## 四、不修，按用户决定停止开发

④ 的性质已被重新定义：它要的是**"排序取 top-N"**，不是"证明每条站点是真的"。
排序用已有的证据链信号就够，插桩只是可选信号之一，不是前提。
