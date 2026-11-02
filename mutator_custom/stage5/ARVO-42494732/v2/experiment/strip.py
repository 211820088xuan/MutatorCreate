import sys, os
def strip_objects(raw):
    """删掉从 `  0 SECTION` 到 `  2 OBJECTS` 之后第一个 `  0 ENDSEC` 的整段。"""
    # 定位 `2\nOBJECTS`
    cands = [b"  2\r\nOBJECTS\r\n", b"  2\nOBJECTS\n", b"  2\r\nOBJECTS\n", b"  2\nOBJECTS\r\n"]
    oi = -1; pat = None
    for p in cands:
        i = raw.find(p)
        if i >= 0 and (oi < 0 or i < oi): oi, pat = i, p
    if oi < 0: return None, "找不到 '  2 OBJECTS'"
    # 往前找最近的 `  0 SECTION`
    sec = -1
    for p in (b"  0\r\nSECTION\r\n", b"  0\nSECTION\n", b"  0\r\nSECTION\n", b"  0\nSECTION\r\n"):
        j = raw.rfind(p, 0, oi)
        if j >= 0 and j > sec: sec = j
    if sec < 0: return None, "OBJECTS 之前找不到 '  0 SECTION'"
    # 往后找第一个 `  0 ENDSEC`
    end = -1; endl = 0
    for p in (b"  0\r\nENDSEC\r\n", b"  0\nENDSEC\n", b"  0\r\nENDSEC\n", b"  0\nENDSEC\r\n"):
        j = raw.find(p, oi)
        if j >= 0 and (end < 0 or j < end): end, endl = j, len(p)
    if end < 0: return None, "OBJECTS 之后找不到 '  0 ENDSEC'"
    return raw[:sec] + raw[end+endl:], f"删除 [{sec}, {end+endl}) 共 {end+endl-sec} 字节"
if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    raw = open(src, "rb").read()
    out, why = strip_objects(raw)
    if out is None:
        print(f"  {os.path.basename(src)}: FAIL {why}"); sys.exit(1)
    open(dst, "wb").write(out)
    print(f"  {os.path.basename(src)}: {len(raw)} -> {len(out)} 字节  ({why})")
    print(f"     OBJECTS 残留次数: {out.count(b'OBJECTS')}   SECTION: {out.count(b'SECTION')}   ENDSEC: {out.count(b'ENDSEC')}")
