import os, subprocess, sys, tempfile
S5 = '/root/gyx/mutator_create/mutator_custom/stage5/ARVO-42494732'
code = open(f'{S5}/v2/mutator.c').read()
d = tempfile.mkdtemp(dir='/tmp')
open(f'{d}/gen.c', 'w').write(code)
open(f'{d}/one.c', 'w').write(open('/root/gyx/mutator_create/mutator_custom/stage5/ARVO-42494732/v2/experiment/one.c').read())
subprocess.run(['clang', '-O0', '-std=c11', '-w', f'{d}/one.c', '-o', f'{d}/one'], check=True)
seed = f'{S5}/seeds/sample_r14.dxf'
print("  策略      Seed  输出长度   是否崩溃")
for aid, sd in (("a001", 550), ("a002", 650), ("a003", 750), ("a004", 850), ("a005", 950)):
    out = subprocess.run([f'{d}/one', seed, str(sd)], capture_output=True).stdout
    p = f'/exp/v2/experiment/strat_{aid}.dxf'
    open(f'{S5}/v2/experiment/strat_{aid}.dxf', 'wb').write(out)
    r = subprocess.run(['docker', 'exec', 'libredwg-exp', 'sh', '-c',
                        f'ASAN_OPTIONS=detect_leaks=0 /exp/v2/experiment/llvmfuzz -runs=1 {p} 2>&1'],
                       capture_output=True, text=True)
    hit = [l for l in r.stdout.split('\n') if l.startswith('SUMMARY')]
    print(f"  {aid}      {sd}   {len(out):>8}   {hit[0][:80] if hit else '无崩溃'}")
