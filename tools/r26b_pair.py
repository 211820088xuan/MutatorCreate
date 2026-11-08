"""R26b：把单次调用的候选拆成释放点/使用点，程序配对。"""
import argparse, collections, glob, json, os, re, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,'tools'); sys.path.insert(0,'pipeline')
from r26_pairing import guard_block, func_of, load_funcs, _root
from s5_6_lib import blocks

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dir',required=True); ap.add_argument('--osv',default='ARVO-42494732')
    a=ap.parse_args()
    root=_root(a.osv); funcs=load_funcs(a.osv)
    rows=[]
    for fn in sorted(glob.glob(os.path.join(a.dir,'f_*.json'))):
        d=json.load(open(fn,encoding='utf-8'))
        for c in d.get('candidates') or []:
            if not c.get('verified'): continue
            rows.append(dict(file=d['file'],free_line=c['free_line'],use_line=c['use_line'],
                             object=(c.get('object') or '').strip(),run=d['run'],
                             self_confidence=c.get('confidence')))
    print(f"  核对通过 {len(rows)} 条")
    fp=collections.defaultdict(set); up=collections.defaultdict(set)
    for r in rows:
        f=r['file'].lstrip('./'); fp[(f,r['free_line'])].add(r['object']); up[(f,r['use_line'])].add(r['object'])
    def ov(field):
        seen=collections.defaultdict(set)
        for r in rows: seen[(r['file'].lstrip('./'),r[field])].add(r['run'])
        n=len(seen); b=sum(1 for v in seen.values() if len(v)>=2)
        return n,b
    nf,bf=ov('free_line'); nu,bu=ov('use_line')
    print(f"  释放点 {nf}，≥2 实例 {bf}（{100.0*bf/max(nf,1):.0f}%）")
    print(f"  使用点 {nu}，≥2 实例 {bu}（{100.0*bu/max(nu,1):.0f}%）")
    pairs=[]; rej=collections.Counter()
    for f in {k[0] for k in fp}:
        p=os.path.join(root,f)
        if not os.path.isfile(p): continue
        L=open(p,encoding='utf-8',errors='replace').read().split('\n')
        for (ff,fl),fo in fp.items():
            if ff!=f: continue
            for (uf,ul),uo in up.items():
                if uf!=f or ul==fl: continue
                same=fo&uo
                if not same: continue
                fn1=func_of(funcs,f,fl); fn2=func_of(funcs,f,ul)
                if not fn1 or not fn2 or fn1['name']!=fn2['name']:
                    rej['cross_function']+=1; continue
                lo,hi=fn1['lines'][0]-1, min(fn1['lines'][1],len(L))-1
                g=guard_block(L,blocks(L,lo,hi),fl-1,ul-1,sorted(same)[0])
                if g: rej[g]+=1; continue
                rf={x['run'] for x in rows if x['file'].lstrip('./')==f and x['free_line']==fl}
                ru={x['run'] for x in rows if x['file'].lstrip('./')==f and x['use_line']==ul}
                k=min(len(rf),len(ru))
                pairs.append(dict(file=f,free_line=fl,use_line=ul,object=sorted(same)[0],
                    confidence=('high' if k>=2 else ('medium' if k==1 else 'low')),source='program_paired'))
    seen=set(); uniq=[]
    for x in sorted(pairs,key=lambda z:(z['file'],z['free_line'],z['use_line'])):
        k=(x['file'],x['free_line'],x['use_line'],x['object'])
        if k in seen: continue
        seen.add(k); uniq.append(x)
    print(f"\n  配对后 {len(uniq)} 处，置信度:", dict(collections.Counter(x['confidence'] for x in uniq)))
    print(f"  过滤: {dict(rej)}")
    T=('src/in_dxf.c',12284,12267)
    hit=[x for x in uniq if (x['file'],x['free_line'],x['use_line'])==T]
    print(f"\n  ⭐ 标尺 {T[0]}:{T[1]}→{T[2]}: {'✅ ' + hit[0]['confidence'] if hit else '❌ 没出来'}")
    for field,val in (('free_line',12284),('use_line',12267)):
        runs=sorted({x['run'] for x in rows if x['file'].lstrip('./')=='src/in_dxf.c' and x[field]==val})
        print(f"    端点 {field}={val}: 实例 {runs or '无'}")
    json.dump(dict(dir=a.dir,pairs=uniq,rejected=dict(rej),free_overlap=[bf,nf],use_overlap=[bu,nu]),
              open(os.path.join(a.dir,'paired.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
if __name__=='__main__': main()
