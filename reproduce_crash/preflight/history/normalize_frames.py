#!/usr/bin/env python3
"""R2,R5,R6,R7 recompute (corrected口径). No docker/network, oss-fuzz read-only.
R2: normalize_frames() + recluster (before/after)
R5: language exact-match only (no substr fallback)
R6: HBO口径 1511 vs 1501
R7: M9 181 net usable after M2-miss + non-C/C++
Reproduce: python3 reproduce_crash/preflight/r2_r5_r6_r7_recompute.py
"""
import os, json, glob, re
from collections import Counter, defaultdict

MC="/root/gyx/mutator_create"; OF="/root/gyx/oss-fuzz"
rows=[json.loads(l) for l in open(os.path.join(MC,"data","crash_dataset.jsonl"))]
meta={}
for f in glob.glob(os.path.join(MC,"crash_testcase","**","*.json"),recursive=True):
    d=json.load(open(f)); meta[d["bug_id"]]=d
rec={}
for l in open(os.path.join(MC,"data","crash_state_recovered.jsonl")):
    d=json.loads(l); rec[d["osv_id"]]=d  # has frames, is_file_frame
of_dirs=set(os.listdir(os.path.join(OF,"projects")))

def san_of(r): m=meta.get(r["osv_id"],{}); return m.get("sanitizer") or r.get("sanitizer") or ""
def ft_of(r): m=meta.get(r["osv_id"],{}); return m.get("fuzz_target") or r.get("fuzz_target") or ""
def ct_of(r): return r.get("crash_type") or ""

# ---------- R2: normalize_frames ----------
INTERNAL_PREFIXES=("__asan_","__msan_","__ubsan_","__tsan_","__sanitizer_","__interceptor_",
                   "LLVMFuzzerTestOneInput","fuzzer::","FuzzedDataProvider","llvm_fuzzer",
                   "afl_","honggfuzz","__libc_","__pthread_","_IO_","gsyslog")
SUFFIX_RE=re.compile(r"\.(part|constprop|isra|cold|localalias|clone|llvm)\.\d+$")
LAMBDA_RE=re.compile(r"\$_\d+")
def normalize_one_frame(fr, is_file):
    if is_file: return None              # 剔除文件名帧 (审计A: 第3帧常为源文件)
    if not fr: return None
    f=str(fr).strip()
    if any(f.startswith(p) or p in f for p in INTERNAL_PREFIXES): return None  # 内部帧
    f=SUFFIX_RE.sub("",f)                # strip .part.NN/.constprop.NN/...
    f=re.sub(r"^auto\s+","",f)           # strip leading 'auto'
    f=LAMBDA_RE.sub("",f)                # strip $_N lambda 记号
    f=re.sub(r"::operator\(\)$","::operator",f)
    f=f.strip()
    return f if f else None
def normalize_frames(osv):
    d=rec.get(osv,{}); fr=d.get("frames") or []; iff=d.get("is_file_frame") or [False]*len(fr)
    out=[]
    for i,f in enumerate(fr):
        isf=iff[i] if i<len(iff) else False
        nf=normalize_one_frame(f,isf)
        if nf: out.append(nf)
    return tuple(out[:3])   # top-3 after normalization

print("="*70); print("R2: 归一化前后聚类对比"); print("="*70)
def cluster(keyfn):
    cl=defaultdict(list)
    for r in rows: cl[keyfn(r)].append(r["osv_id"])
    return cl
# original (raw top-3)
cl_raw=cluster(lambda r:(r["project"],ct_of(r),tuple((rec.get(r["osv_id"],{}).get("frames") or [])[:3])))
# normalized
cl_norm=cluster(lambda r:(r["project"],ct_of(r),normalize_frames(r["osv_id"])))
def stats(cl,label):
    sizes=[len(v) for v in cl.values()]
    single=sum(1 for s in sizes if s==1)
    print(f"  [{label}] 唯一簇={len(cl)} 单例={single}({single/len(cl)*100:.1f}%) 最大簇={max(sizes)} mean={sum(sizes)/len(sizes):.2f}")
    return len(cl),single/len(cl)*100,max(sizes)
print("全量:")
r_raw=stats(cl_raw,"原始帧"); r_norm=stats(cl_norm,"归一化帧")
# HBO subset
hbo=[r for r in rows if ct_of(r)=="Heap-buffer-overflow"]
cl_raw_h=defaultdict(list); cl_norm_h=defaultdict(list)
for r in hbo:
    cl_raw_h[(r["project"],tuple((rec.get(r["osv_id"],{}).get("frames") or [])[:3]))].append(r["osv_id"])
    cl_norm_h[(r["project"],normalize_frames(r["osv_id"]))].append(r["osv_id"])
print(f"HBO 子集 ({len(hbo)} 条):")
hr=stats(cl_raw_h,"原始帧"); hn=stats(cl_norm_h,"归一化帧")
drop=r_raw[1]-r_norm[1]
print(f"\n单例率变化: 全量 {r_raw[1]:.1f}% -> {r_norm[1]:.1f}% (降 {drop:.1f}pp); HBO {hr[1]:.1f}% -> {hn[1]:.1f}% (降 {hr[1]-hn[1]:.1f}pp)")
print(f"簇数变化: 全量 {r_raw[0]} -> {r_norm[0]} (合并 {r_raw[0]-r_norm[0]} 簇); HBO {hr[0]} -> {hn[0]}")
# show a few merged clusters (norm cluster with >1 raw cluster)
print("\n归一化合并样例 (norm 簇含多 raw 帧形态):")
n=0
for k,ids in sorted(cl_norm.items(),key=lambda kv:-len(kv[1])):
    if len(ids)>1 and n<5:
        raw_variants=set(tuple((rec.get(i,{}).get("frames") or [])[:3]) for i in ids)
        if len(raw_variants)>1:
            print(f"  {k[0]}/{k[1]} norm={list(k[2])} <- {len(ids)}条/{len(raw_variants)}种原始帧"); n+=1

# ---------- R2-extra (item6): normalize_frames() 实际改动记录数 ----------
# 验证「单例率仅降 0.2pp」是否因为归一化几乎没生效（用户要求补的数）。
# 区分两类改动：①剔帧（文件帧/内部帧）——改变 top-3 但通常不合并同 bug 簇；
#            ②文本归一（.part/.constprop/.isra/$_N/auto/operator）——这才是合并
#            「同 bug 不同版本编译」重复簇的规则。若②只命中几十条，则「无需去重」证据偏弱。
print("\n[R2-extra item6] normalize_frames() 实际改动记录数:")
n_wf=0; n_key_changed=0; n_text_norm=0; n_removal_only=0
fire_file=0; fire_internal=0; fire_suffix=0; fire_lambda=0; fire_auto=0; fire_oper=0
for r in rows:
    osv=r["osv_id"]; d=rec.get(osv,{}); raw=d.get("frames") or []
    iff=d.get("is_file_frame") or [False]*len(raw)
    if not raw: continue
    n_wf+=1
    norm=normalize_frames(osv)
    if norm!=tuple(raw[:3]): n_key_changed+=1
    text_fired=False; removal_fired=False
    for i,f in enumerate(raw):
        fs=str(f).strip() if f else ""
        if not fs: continue
        isf=iff[i] if i<len(iff) else False
        if isf: fire_file+=1; removal_fired=True; continue
        if any(fs.startswith(p) or p in fs for p in INTERNAL_PREFIXES): fire_internal+=1; removal_fired=True; continue
        s2=SUFFIX_RE.sub("",fs)
        if s2!=fs: fire_suffix+=1; text_fired=True
        s3=re.sub(r"^auto\s+","",s2)
        if s3!=s2: fire_auto+=1; text_fired=True
        s4=LAMBDA_RE.sub("",s3)
        if s4!=s3: fire_lambda+=1; text_fired=True
        s5=re.sub(r"::operator\(\)$","::operator",s4).strip()
        if s5!=s4: fire_oper+=1; text_fired=True
    if text_fired: n_text_norm+=1
    if removal_fired and not text_fired: n_removal_only+=1
print(f"  有帧记录: {n_wf}")
print(f"  归一化后 top-3 ≠ 原始 top-3 的记录(键改变): {n_key_changed} ({n_key_changed/n_wf*100:.1f}%)")
print(f"    其中含文本归一(.part/.constprop/.isra/auto/$_N/operator): {n_text_norm} ({n_text_norm/n_wf*100:.1f}%)  <- 合并版本漂移重复簇的关键规则")
print(f"    仅剔帧(文件帧/内部帧)无文本归一: {n_removal_only} ({n_removal_only/n_wf*100:.1f}%)")
print(f"  逐帧规则触发计数(全帧非仅top-3): 文件帧={fire_file} 内部帧={fire_internal} 后缀strip={fire_suffix} auto={fire_auto} lambda={fire_lambda} operator={fire_oper}")
print(f"  => 判读: 若 n_text_norm 仅几十条, 则归一化对'合并同bug不同版本簇'几乎没生效, '单例率降0.2pp'不能单独作为'无需去重'的强证据(应表述为: 现有数据中版本漂移型重复极少, 故未观察到去重需求)。")

# ---------- R5: language exact-match only ----------
print("\n"+"="*70); print("R5: language 分布 (exact-match only, 不用 substr 回落)"); print("="*70)
def read_lang(p):
    yp=os.path.join(OF,"projects",p,"project.yaml")
    if not os.path.exists(yp): return None
    for line in open(yp,encoding="utf-8",errors="replace"):
        m=re.match(r"\s*language\s*:\s*([^\s]+)",line)
        if m: return m.group(1)
    return None
lang_crash=Counter(); lang_proj={}
for r in rows:
    p=r["project"]
    if p in of_dirs:
        lg=read_lang(p) or "(yaml无language)"
    else:
        lg="unknown(name-miss)"   # 不应用未批准映射
    lang_crash[lg]+=1; lang_proj.setdefault(p,lg)
print("crash 级 language (exact-match):")
for l,n in lang_crash.most_common(): print(f"  {l}: {n}")
cpp=lang_crash.get("c",0)+lang_crash.get("c++",0)
noncpp=sum(n for l,n in lang_crash.items() if l not in("c","c++","unknown(name-miss)","(yaml无language)"))
unk=lang_crash.get("unknown(name-miss)",0)
nolang=lang_crash.get("(yaml无language)",0)
print(f"\nC/C++ 主线 scope: {cpp}")
print(f"非 C/C++ (jvm/rust/go/python/swift/ruby/javascript): {noncpp}")
print(f"unknown(name-miss, M2未命中): {unk}")
print(f"yaml无language字段(默认c++ per constants.DEFAULT_LANGUAGE): {nolang}")
print(f"\n[对比原 M3b] 原 jvm=218 (含 unrar26 误映 junrar)；修正后 jvm={lang_crash.get('jvm',0)}")
print(f"原非C/C++=274；修正后非C/C++={noncpp}；原 unmapped=11；修正后 unknown(name-miss)={unk}")

# ---------- R6: HBO口径 ----------
print("\n"+"="*70); print("R6: HBO口径 1511 vs 1501"); print("="*70)
all_hbo=[r for r in rows if ct_of(r)=="Heap-buffer-overflow"]
asan_hbo=[r for r in all_hbo if san_of(r)=="address (ASAN)"]
print(f"全部 HBO: {len(all_hbo)}")
print(f"ASAN ∩ HBO: {len(asan_hbo)}")
diff=[r for r in all_hbo if san_of(r)!="address (ASAN)"]
print(f"差集 (HBO 非 ASAN): {len(diff)}")
print(f"差集 sanitizer 分布: {dict(Counter(san_of(r) for r in diff))}")
print(f"差集样例: {[(r['osv_id'],r['project'],san_of(r)) for r in diff[:5]]}")
print("=> 统一口径: 后续引用 'HBO' 指全部 1511; 'ASAN∩HBO' 指 1501 (Phase0/2a 的 ASAN+HBO 子集)")

# ---------- R7: M9 181 net usable ----------
print("\n"+"="*70); print("R7: M9 181 条净可用 (减 M2未命中 + 非C/C++)"); print("="*70)
empty_ft=[r for r in rows if not ft_of(r)]
proj_targets=defaultdict(set)
for r in rows:
    ft=ft_of(r)
    if ft: proj_targets[r["project"]].add(ft)
inferable=[r for r in empty_ft if len(proj_targets.get(r["project"],set()))==1]
print(f"空 target: {len(empty_ft)}; 可推定(原M9): {len(inferable)}")
# subtract M2-missed (project not exact in of_dirs)
miss=[r for r in inferable if r["project"] not in of_dirs]
# subtract non-C/C++ (language exact-match)
noncpp_set={l for l in lang_crash if l not in("c","c++","unknown(name-miss)","(yaml无language)")}
noncpp_r=[r for r in inferable if r["project"] in of_dirs and (read_lang(r["project"]) in noncpp_set)]
net=[r for r in inferable if r["project"] in of_dirs and (read_lang(r["project"]) not in noncpp_set)]
print(f"  减 (a) M2未命中项目: {len(miss)} 条 ({dict(Counter(r['project'] for r in miss))})")
print(f"  减 (b) 非C/C++项目: {len(noncpp_r)} 条 ({dict(Counter(r['project'] for r in noncpp_r))})")
print(f"  净可用 (C/C++ 且 oss-fuzz 命中): {len(net)} 条")
print(f"  净可用 top 项目: {dict(Counter(r['project'] for r in net).most_common(8))}")
print(f"=> 决策#7 更新: 181 -> 净可用 {len(net)}; 不可复现空target = 535-{len(net)} = {535-len(net)} (含354原剩余+{len(miss)+len(noncpp_r)}被减)")
print("\n=== r2_r5_r6_r7_recompute.py done ===")
