#!/usr/bin/env python3
"""逐策略独立覆盖率测量

对每个模式（default + 5 个强制策略），用同一份种子跑固定时长，
比较 "cov:"（覆盖边数）与执行次数。

用法（容器内）: python3 /exp/measure_strategy_cov.py [每次秒数]
"""
import os, re, shutil, subprocess, sys, tempfile, json

SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 45
BIN = '/exp/fuzz_exp/llvmfuzz'
SEEDS = '/exp/seeds'
BASE = '/tmp/covmeas'

os.makedirs(BASE, exist_ok=True)

def run(label, env_extra, secs):
    d = os.path.join(BASE, label)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, 'corpus'))
    for f in os.listdir(SEEDS):
        if f.endswith('.dxf'):
            shutil.copy(os.path.join(SEEDS, f), os.path.join(d, 'corpus', f))
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0', LSAN_OPTIONS='detect_leaks=0')
    env.update(env_extra)
    log = os.path.join(d, 'run.log')
    with open(log, 'w') as fh:
        subprocess.run([BIN, f'-max_total_time={secs}', '-fork=1', '-seed=1',
                        '-timeout=25', '-rss_limit_mb=2560', '-ignore_crashes=1',
                        '-ignore_ooms=1', '-ignore_timeouts=1', '-print_final_stats=1',
                        os.path.join(d, 'corpus')],
                       stdout=fh, stderr=subprocess.STDOUT, env=env)
    txt = open(log, errors='replace').read()
    cov = [int(x) for x in re.findall(r'cov: (\d+)', txt)]
    ft = [int(x) for x in re.findall(r'ft: (\d+)', txt)]
    ex = re.findall(r'stat::number_of_executed_units:\s*(\d+)', txt)
    cr = re.findall(r'stat::number_of_crashes:\s*(\d+)', txt)
    return {
        'label': label,
        'cov_max': max(cov) if cov else None,
        'ft_max': max(ft) if ft else None,
        'execs': int(ex[-1]) if ex else None,
        'crashes': int(cr[-1]) if cr else 0,
        'corpus_files': len(os.listdir(os.path.join(d, 'corpus'))),
    }

rows = []
print(f"每个模式跑 {SECS} 秒 ...\n", flush=True)

rows.append(run('default', {'LIBREDWG_MUTATOR_OFF': '1'}, SECS))
print(f"  default      cov={rows[-1]['cov_max']} ft={rows[-1]['ft_max']} execs={rows[-1]['execs']}", flush=True)

for k in range(5):
    rows.append(run(f'strat{k}', {'LIBREDWG_MUTATOR_OFF': '0',
                                   'LIBREDWG_FORCE_STRATEGY': str(k)}, SECS))
    r = rows[-1]
    print(f"  strat{k}       cov={r['cov_max']} ft={r['ft_max']} execs={r['execs']} "
          f"crashes={r['crashes']}", flush=True)

print("\n" + "=" * 72)
base = rows[0]['cov_max'] or 0
print(f"{'模式':<12}{'cov':>8}{'ft':>8}{'execs':>12}{'崩溃':>6}{'相对 default':>14}")
print("-" * 72)
for r in rows:
    d = f"{(r['cov_max'] or 0) / base * 100:6.1f}%" if base else "n/a"
    print(f"{r['label']:<12}{r['cov_max'] or 0:>8}{r['ft_max'] or 0:>8}"
          f"{r['execs'] or 0:>12}{r['crashes']:>6}{d:>14}")

json.dump(rows, open('/exp/fuzz_exp/strategy_cov.json', 'w'), indent=1)
print("\n已写出 /exp/fuzz_exp/strategy_cov.json")
