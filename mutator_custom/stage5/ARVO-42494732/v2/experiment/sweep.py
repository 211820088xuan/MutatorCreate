import json, os, subprocess, tempfile, sys
sys.path.insert(0, '/root/gyx/mutator_create/pattern_analysis/pipeline')
import s5_generate_mutator_v2 as G
S5 = '/root/gyx/mutator_create/mutator_custom/stage5/ARVO-42494732'
code = open(f'{S5}/v2/mutator.c').read()
d = tempfile.mkdtemp(dir='/tmp')
open(f'{d}/gen.c', 'w').write(code); open(f'{d}/drv.c', 'w').write(G.DRIVER)
subprocess.run(['clang', '-O0', '-std=c11', '-w', f'{d}/drv.c', '-o', f'{d}/drv'], check=True)
r = subprocess.run([f'{d}/drv', f'{S5}/seeds/sample_r14.dxf', '1000'],
                   capture_output=True, text=True, errors='replace')
print('  ', [x for x in r.stderr.split('\n') if x.startswith('UNCHANGED')][0])
recs = [x[4:] for x in r.stderr.split('\n') if x.startswith('REC ')][:10]
for i, rec in enumerate(recs):
    seg = [s for s in rec.split('|') if s.strip()][:4]
    print(f'   {i}: {seg}')
