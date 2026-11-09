#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct { size_t start; size_t end; size_t next; } Line;

static const uint8_t S_SECTION[] = {'S','E','C','T','I','O','N'};
static const uint8_t S_OBJECTS[] = {'O','B','J','E','C','T','S'};
static const uint8_t S_ENDSEC[] = {'E','N','D','S','E','C'};
static const uint8_t S_EOF[] = {'E','O','F'};
static const uint8_t ALPHA[] = {'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','0','1','2','3','4','5','6','7','8','9','_','-'};

static unsigned rng_next(unsigned *s) {
    unsigned x = *s; if (x == 0) x = 0x12345678u;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5; *s = x; return x;
}

static int next_line(const uint8_t *Data, size_t Size, size_t *pos, Line *ln) {
    if (*pos >= Size) return 0;
    size_t s = *pos, e = s;
    while (e < Size && Data[e] != 13 && Data[e] != 10) e++;
    size_t n = e;
    if (n < Size) {
        if (Data[n] == 13) { if (n + 1 < Size && Data[n + 1] == 10) n += 2; else n += 1; }
        else n += 1;
    }
    ln->start = s; ln->end = e; ln->next = n; *pos = n; return 1;
}

static int parse_group_code(const uint8_t *Data, size_t start, size_t end, int *out) {
    size_t i = start;
    while (i < end && (Data[i] == 32 || Data[i] == 9)) i++;
    int val = 0, nd = 0;
    while (i < end && Data[i] >= 48 && Data[i] <= 57 && nd < 3) { val = val * 10 + (int)(Data[i] - 48); i++; nd++; }
    if (nd == 0) return 0;
    if (i < end && Data[i] >= 48 && Data[i] <= 57) return 0;
    while (i < end) { if (Data[i] != 32 && Data[i] != 9) return 0; i++; }
    *out = val; return 1;
}

static int line_equals_trim(const uint8_t *Data, size_t start, size_t end, const uint8_t *s, size_t n) {
    size_t a = start, b = end;
    while (a < b && (Data[a] == 32 || Data[a] == 9)) a++;
    while (b > a && (Data[b - 1] == 32 || Data[b - 1] == 9)) b--;
    return (b - a == n) && (memcmp(Data + a, s, n) == 0);
}

static int is_dxf(const uint8_t *Data, size_t Size) {
    if (Size >= 2 && Data[0] == 65 && Data[1] == 67) return 0;
    if (Size >= 1 && Data[0] == 123) return 0;
    return 1;
}

static int find_section(const uint8_t *Data, size_t Size, const uint8_t *name, size_t nameLen, size_t *contentStart, size_t *contentEnd, size_t *endsecStart) {
    size_t scan = 0;
    while (scan < Size) {
        Line codeLn; size_t p = scan;
        if (!next_line(Data, Size, &p, &codeLn)) break;
        int code;
        if (!parse_group_code(Data, codeLn.start, codeLn.end, &code)) { scan = p; continue; }
        size_t vp = p; Line valLn;
        if (!next_line(Data, Size, &vp, &valLn)) break;
        if (code == 0 && line_equals_trim(Data, valLn.start, valLn.end, S_SECTION, sizeof(S_SECTION))) {
            size_t p2 = vp; Line c2;
            if (!next_line(Data, Size, &p2, &c2)) { scan = vp; continue; }
            int code2;
            if (parse_group_code(Data, c2.start, c2.end, &code2)) {
                size_t vp2 = p2; Line v2;
                if (next_line(Data, Size, &vp2, &v2)) {
                    if (code2 == 2 && line_equals_trim(Data, v2.start, v2.end, name, nameLen)) {
                        size_t q = vp2;
                        while (q < Size) {
                            Line c3; size_t qp = q;
                            if (!next_line(Data, Size, &qp, &c3)) break;
                            int code3;
                            if (!parse_group_code(Data, c3.start, c3.end, &code3)) { q = qp; continue; }
                            size_t qv = qp; Line v3;
                            if (!next_line(Data, Size, &qv, &v3)) break;
                            if (code3 == 0 && line_equals_trim(Data, v3.start, v3.end, S_ENDSEC, sizeof(S_ENDSEC))) {
                                *contentStart = vp2; *contentEnd = c3.start; *endsecStart = c3.start; return 1;
                            }
                            q = qv;
                        }
                        return 0;
                    }
                }
            }
        }
        scan = vp;
    }
    return 0;
}

static size_t count_code0_records(const uint8_t *Data, size_t Size, size_t start, size_t end) {
    size_t count = 0, q = start;
    while (q < end) {
        Line c; size_t p = q;
        if (!next_line(Data, Size, &p, &c)) break;
        if (c.start >= end) break;
        int code;
        if (!parse_group_code(Data, c.start, c.end, &code)) { q = p; continue; }
        size_t vp = p; Line v;
        if (!next_line(Data, Size, &vp, &v)) break;
        if (v.start >= end) break;
        if (code == 0) count++;
        q = vp;
    }
    return count;
}

static size_t find_eof_start(const uint8_t *Data, size_t Size) {
    size_t scan = 0;
    while (scan < Size) {
        Line c; size_t p = scan;
        if (!next_line(Data, Size, &p, &c)) break;
        int code;
        if (!parse_group_code(Data, c.start, c.end, &code)) { scan = p; continue; }
        size_t vp = p; Line v;
        if (!next_line(Data, Size, &vp, &v)) break;
        if (code == 0 && line_equals_trim(Data, v.start, v.end, S_EOF, sizeof(S_EOF))) return c.start;
        scan = vp;
    }
    return (size_t)-1;
}

static size_t gen_name(uint8_t *out, size_t maxLen, unsigned *st, const uint8_t *old, size_t oldLen) {
    size_t alen = sizeof(ALPHA);
    size_t len = 1 + (rng_next(st) % 64);
    if (len > maxLen) len = maxLen;
    if (len == 0) return 0;
    for (size_t i = 0; i < len; i++) out[i] = ALPHA[rng_next(st) % alen];
    if (old && len == oldLen && memcmp(out, old, len) == 0) {
        uint8_t oldc = oldLen ? old[0] : 0;
        for (size_t i = 0; i < alen; i++) { if (ALPHA[i] != oldc) { out[0] = ALPHA[i]; break; } }
    }
    return len;
}

static size_t construct_objects_section(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
    size_t eofStart = find_eof_start(Data, Size);
    if (eofStart == (size_t)-1) return Size;
    unsigned st = Seed ^ 0xa5a5a5a5u ^ (unsigned)Size; if (st == 0) st = 1;
    uint8_t name[64];
    size_t nameLen = gen_name(name, sizeof(name), &st, NULL, 0);
    static const uint8_t pre[] = {'0',13,10,'S','E','C','T','I','O','N',13,10,'2',13,10,'O','B','J','E','C','T','S',13,10,'0',13,10};
    static const uint8_t post[] = {13,10,'0',13,10,'E','N','D','S','E','C',13,10};
    size_t insLen = sizeof(pre) + nameLen + sizeof(post);
    if (Size + insLen > MaxSize) return Size;
    memmove(Data + eofStart + insLen, Data + eofStart, Size - eofStart);
    uint8_t *p = Data + eofStart;
    memcpy(p, pre, sizeof(pre)); p += sizeof(pre);
    memcpy(p, name, nameLen); p += nameLen;
    memcpy(p, post, sizeof(post));
    return Size + insLen;
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed, int *ok) {
    *ok = 0;
    size_t contentStart, contentEnd, endsecStart;
    if (find_section(Data, Size, S_OBJECTS, sizeof(S_OBJECTS), &contentStart, &contentEnd, &endsecStart)) {
        size_t count = count_code0_records(Data, Size, contentStart, contentEnd);
        if (count > 0) {
            unsigned st = Seed ^ 0x9e3779b9u ^ (unsigned)Size; if (st == 0) st = 1;
            size_t k = rng_next(&st) % count;
            size_t q = contentStart, idx = 0; int found = 0; Line foundVal;
            while (q < contentEnd) {
                Line c; size_t p = q;
                if (!next_line(Data, Size, &p, &c)) break;
                if (c.start >= contentEnd) break;
                int code;
                if (!parse_group_code(Data, c.start, c.end, &code)) { q = p; continue; }
                size_t vp = p; Line v;
                if (!next_line(Data, Size, &vp, &v)) break;
                if (v.start >= contentEnd) break;
                if (code == 0) {
                    if (idx == k) { foundVal = v; found = 1; break; }
                    idx++;
                }
                q = vp;
            }
            if (found) {
                uint8_t name[64];
                size_t oldLen = foundVal.end - foundVal.start;
                size_t nameLen = gen_name(name, sizeof(name), &st, Data + foundVal.start, oldLen);
                size_t leLen = foundVal.next - foundVal.end;
                uint8_t leBuf[2];
                if (leLen > sizeof(leBuf)) leLen = sizeof(leBuf);
                if (leLen) memcpy(leBuf, Data + foundVal.end, leLen);
                size_t oldLineLen = foundVal.next - foundVal.start;
                size_t newLineLen = nameLen + leLen;
                if (newLineLen > oldLineLen) {
                    size_t delta = newLineLen - oldLineLen;
                    if (Size + delta > MaxSize) return Size;
                }
                if (newLineLen != oldLineLen) {
                    memmove(Data + foundVal.start + newLineLen, Data + foundVal.next, Size - foundVal.next);
                    if (newLineLen > oldLineLen) Size += newLineLen - oldLineLen; else Size -= oldLineLen - newLineLen;
                }
                memcpy(Data + foundVal.start, name, nameLen);
                if (leLen) memcpy(Data + foundVal.start + nameLen, leBuf, leLen);
                *ok = 1; return Size;
            }
        }
        return Size;
    }
    size_t newSize = construct_objects_section(Data, Size, MaxSize, Seed);
    if (newSize != Size) { *ok = 1; return newSize; }
    return Size;
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    unsigned r = Seed % 1000u;
    if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);
    if (!is_dxf(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
    int ok = 0;
    size_t ns = mutate_a001(Data, Size, MaxSize, Seed, &ok);
    if (!ok) return LLVMFuzzerMutate(Data, Size, MaxSize);
    return ns;
}