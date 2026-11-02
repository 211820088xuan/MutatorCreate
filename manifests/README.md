# ARVO 复现状态清单

由 `tools/build_arvo_manifest.py` 生成，数据源：`arvo/data/arvo.db`（6,138 条崩溃 / 311 个项目）与本地复现台账 `pattern_analysis/artifacts/reproduced_crashes.jsonl`（1,154 条）。

## 总览

| 口径 | 数量 |
|---|---|
| ARVO 崩溃总数 | **6138** |
| ARVO 项目数 | 311 |
| **已复现** | **915**（54 个项目） |
| 　├ 有故障位置（fault_fn + fault_line） | 873 |
| 　└ 无故障位置 | 42 |
| **未复现** | **5223** |
| 　├ 未尝试（无复现日志） | 5223 |
| 　└ 尝试失败 | 0 |
| ARVO 之外（OSS-Fuzz）已复现 | 239 |
| ARVO 之外尝试失败 | 31 |

## 已复现的项目（按数量）

| 项目 | 已复现 | 该项目 ARVO 总数 | 复现率 |
|---|---:|---:|---:|
| ndpi | 80 | 179 | 44.7% |
| opensc | 63 | 127 | 49.6% |
| harfbuzz | 56 | 151 | 37.1% |
| mruby | 46 | 98 | 46.9% |
| c-blosc2 | 39 | 92 | 42.4% |
| fluent-bit | 36 | 64 | 56.2% |
| libredwg | 36 | 83 | 43.4% |
| libxml2 | 34 | 118 | 28.8% |
| openthread | 29 | 64 | 45.3% |
| wireshark | 24 | 102 | 23.5% |
| libavc | 24 | 61 | 39.3% |
| radare2 | 22 | 30 | 73.3% |
| openh264 | 22 | 49 | 44.9% |
| matio | 22 | 87 | 25.3% |
| serenity | 20 | 96 | 20.8% |
| libvips | 18 | 47 | 38.3% |
| lcms | 17 | 45 | 37.8% |
| htslib | 16 | 27 | 59.3% |
| assimp | 16 | 74 | 21.6% |
| lwan | 15 | 20 | 75.0% |
| open62541 | 15 | 63 | 23.8% |
| net-snmp | 14 | 29 | 48.3% |
| icu | 14 | 20 | 70.0% |
| leptonica | 14 | 33 | 42.4% |
| file | 13 | 27 | 48.1% |
| perfetto | 13 | 16 | 81.2% |
| kamailio | 13 | 16 | 81.2% |
| ntopng | 13 | 25 | 52.0% |
| libarchive | 12 | 31 | 38.7% |
| wolfssl | 12 | 72 | 16.7% |
| kimageformats | 12 | 44 | 27.3% |
| libjxl | 12 | 41 | 29.3% |
| gpac | 10 | 89 | 11.2% |
| espeak-ng | 9 | 16 | 56.2% |
| hdf5 | 9 | 24 | 37.5% |
| openvswitch | 8 | 26 | 30.8% |
| wasm3 | 7 | 41 | 17.1% |
| libgit2 | 6 | 11 | 54.5% |
| readstat | 6 | 10 | 60.0% |
| curl | 6 | 39 | 15.4% |
| igraph | 6 | 8 | 75.0% |
| selinux | 6 | 42 | 14.3% |
| zstd | 5 | 13 | 38.5% |
| libspng | 5 | 7 | 71.4% |
| libhevc | 5 | 24 | 20.8% |
| arrow | 5 | 46 | 10.9% |
| openexr | 5 | 16 | 31.2% |
| exiv2 | 5 | 10 | 50.0% |
| mongoose | 5 | 9 | 55.6% |
| jq | 5 | 10 | 50.0% |
| opencv | 4 | 18 | 22.2% |
| flac | 4 | 15 | 26.7% |
| libheif | 1 | 24 | 4.2% |
| mupdf | 1 | 93 | 1.1% |

## 未复现最多的项目

| 项目 | 未复现 | 该项目 ARVO 总数 |
|---|---:|---:|
| imagemagick | 459 | 459 |
| ffmpeg | 400 | 400 |
| gdal | 253 | 253 |
| ghostpdl | 177 | 177 |
| binutils-gdb | 165 | 165 |
| skia | 163 | 163 |
| php-src | 108 | 108 |
| ndpi | 99 | 179 |
| harfbuzz | 95 | 151 |
| mupdf | 92 | 93 |
| libxml2 | 84 | 118 |
| gpac | 79 | 89 |
| wireshark | 78 | 102 |
| graphicsmagick | 77 | 77 |
| serenity | 76 | 96 |

## 已复现崩溃的类型分布

| crash family | 已复现 |
|---|---:|
| heap-buffer-overflow | 483 |
| use-after-free | 113 |
| stack-buffer-overflow | 97 |
| unknown-read | 66 |
| global-buffer-overflow | 41 |
| segv | 33 |
| unknown-write | 24 |
| double-free | 16 |
| negative-size-param | 11 |
| stack-use-after-return | 6 |
| invalid-free | 6 |
| memcpy-param-overlap | 5 |
| use-after-poison | 4 |
| stack-use-after-scope | 3 |
| container-overflow | 3 |
| bad-free | 1 |
| unknown | 1 |
| stack-buffer-underflow | 1 |
| null-dereference | 1 |

## 字段说明（`arvo_manifest.jsonl` / `.csv`）

| 字段 | 含义 |
|---|---|
| `osv_id` | `ARVO-<localId>`，与台账/CPG/facts 的目录名一致 |
| `local_id` | ARVO 的 OSS-Fuzz issue id |
| `project / repo_addr / fix_commit` | 项目、仓库地址、修复提交 |
| `fuzz_target / fuzz_engine / sanitizer` | harness 名、生成引擎、sanitizer |
| `crash_type / crash_family` | 原始崩溃类型 + 归一化后的族 |
| `severity / report_url` | 严重级别、OSS-Fuzz issue 链接 |
| `status` | `reproduced` / `not_reproduced` |
| `reason` | 未复现原因：目前只可能是 `not_attempted` |
| `attempted` | 是否存在复现尝试日志 |
| `has_fault_location` | 是否拿到 `fault_fn` + `fault_line` |
| `fault_file / fault_fn / fault_line` | 故障位置（仅复现行有） |
| `pin_commit` | 复现时锁定的项目提交 |
| `testcase_size` | 复现用 crash 输入大小 |
| `has_facts / has_interpretation / has_deep` | 下游产物是否已生成 |
| `cpg_count` | 该项目在 `cpg_files/` 里的 CPG 图数量（项目维度，非崩溃维度） |

## 必须说清的三点

1. **ARVO 库里的 `reproduced` / `verified` / `patch_located` 是常量列**（全 1 / 全 0 / 全 1），没有区分度，**不能**用来解释“为什么没复现”。
2. **ARVO 里没有“尝试过但失败”的记录**：31 次失败尝试全部来自 OSS-Fuzz（`OSV-*`），已单独放在 `outside_manifest.jsonl`。
3. 未复现的 5,223 条全部是 **`not_attempted`**——没有复现日志，不是“试了没成功”。这批是后续扩展的主要来源。
