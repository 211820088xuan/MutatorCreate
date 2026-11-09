#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct {
    size_t start;
    size_t end;
    size_t next;
    size_t eol_len;
    int ok;
} Line;

static Line next_line(const uint8_t *Data, size_t Size, size_t pos) {
    Line L;
    L.start = pos; L.end = pos; L.next = pos; L.eol_len = 0; L.ok = 0;
    if (pos >= Size) return L;
    size_t i = pos;
    while (i < Size && Data[i] != '\r' && Data[i] != '\n') i++;
    L.start = pos;
    L.end = i;
    if (i < Size) {
        if (Data[i] == '\r') {
            if (i + 1 < Size && Data[i + 1] == '\n') {
                L.next = i + 2; L.eol_len = 2;
            } else {
                L.next = i + 1; L.eol_len = 1;
            }
        } else {
            L.next = i + 1; L.eol_len = 1;
        }
    } else {
        L.next = Size; L.eol_len = 0;
    }
    L.ok = 1;
    return L;
}

static int line_eq(const uint8_t *Data, size_t start, size_t end, const char *s) {
    size_t n = strlen(s);
    if (end < start || end - start != n) return 0;
    for (size_t i = 0; i < n; i++) {
        if (Data[start + i] != (uint8_t)s[i]) return 0;
    }
    return 1;
}

static int parse_code_line(const uint8_t *Data, size_t start, size_t end, int *out) {
    size_t i = start;
    while (i < end && (Data[i] == ' ' || Data[i] == '\t')) i++;
    if (i >= end) return 0;
    int v = 0, digits = 0;
    while (i < end && Data[i] >= '0' && Data[i] <= '9') {
        v = v * 10 + (int)(Data[i] - '0');
        digits++;
        i++;
    }
    if (digits == 0 || digits > 3) return 0;
    while (i < end && (Data[i] == ' ' || Data[i] == '\t')) i++;
    if (i != end) return 0;
    *out = v;
    return 1;
}

static int get_pair(const uint8_t *Data, size_t Size, size_t pos,
                    int *code, size_t *val_start, size_t *val_end,
                    size_t *after_val, size_t *code_start,
                    size_t *code_end, size_t *after_code) {
    Line c = next_line(Data, Size, pos);
    if (!c.ok) return 0;
    Line v = next_line(Data, Size, c.next);
    if (!v.ok) return 0;
    int cd;
    if (!parse_code_line(Data, c.start, c.end, &cd)) return 0;
    *code = cd;
    *val_start = v.start;
    *val_end = v.end;
    *after_val = v.next;
    *code_start = c.start;
    *code_end = c.end;
    *after_code = c.next;
    return 1;
}

static int find_section(const uint8_t *Data, size_t Size, const char *name,
                        size_t *body_start, size_t *body_end,
                        size_t *section_start) {
    size_t pos = 0;
    while (pos < Size) {
        int code;
        size_t vs, ve, av, cs, ce, ac;
        if (!get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
            Line l = next_line(Data, Size, pos);
            if (!l.ok || l.next <= pos) break;
            pos = l.next;
            continue;
        }
        if (code == 0 && line_eq(Data, vs, ve, "SECTION")) {
            size_t pos2 = av;
            int c2;
            size_t vs2, ve2, av2, cs2, ce2, ac2;
            if (get_pair(Data, Size, pos2, &c2, &vs2, &ve2, &av2, &cs2, &ce2, &ac2) &&
                c2 == 2 && line_eq(Data, vs2, ve2, name)) {
                *body_start = av2;
                *section_start = cs;
                size_t p = av2;
                while (p < Size) {
                    int c3;
                    size_t vs3, ve3, av3, cs3, ce3, ac3;
                    if (!get_pair(Data, Size, p, &c3, &vs3, &ve3, &av3, &cs3, &ce3, &ac3)) {
                        Line l = next_line(Data, Size, p);
                        if (!l.ok || l.next <= p) break;
                        p = l.next;
                        continue;
                    }
                    if (c3 == 0 && line_eq(Data, vs3, ve3, "ENDSEC")) {
                        *body_end = cs3;
                        return 1;
                    }
                    p = av3;
                }
                *body_end = Size;
                return 1;
            }
        }
        pos = av;
    }
    return 0;
}

static int is_dxf_input(const uint8_t *Data, size_t Size) {
    size_t pos = 0;
    while (pos < Size) {
        int code;
        size_t vs, ve, av, cs, ce, ac;
        if (!get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
            Line l = next_line(Data, Size, pos);
            if (!l.ok || l.next <= pos) break;
            pos = l.next;
            continue;
        }
        if (code == 0 && (line_eq(Data, vs, ve, "SECTION") ||
                          line_eq(Data, vs, ve, "EOF") ||
                          line_eq(Data, vs, ve, "ENDSEC"))) return 1;
        if (code == 2 && line_eq(Data, vs, ve, "ENTITIES")) return 1;
        pos = av;
    }
    return 0;
}

static uint64_t rng_next(uint64_t *s) {
    uint64_t x = *s;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *s = x;
    return x * 2685821657736338717ULL;
}

static void fill_random_name(uint8_t *name, unsigned len, uint64_t *state) {
    static const char alpha[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    size_t alen = sizeof(alpha) - 1;
    for (unsigned i = 0; i < len; i++) {
        name[i] = (uint8_t)alpha[rng_next(state) % alen];
    }
}

static int ensure_differ(uint8_t *name, unsigned len, const uint8_t *oldv, size_t oldlen) {
    if (len != oldlen) return 1;
    if (memcmp(name, oldv, len) != 0) return 1;
    if (len == 0) return 0;
    static const char alpha[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    size_t alen = sizeof(alpha) - 1;
    size_t p = 0;
    for (size_t i = 0; i < alen; i++) {
        if (name[0] == (uint8_t)alpha[i]) { p = i; break; }
    }
    name[0] = (uint8_t)alpha[(p + 1) % alen];
    return memcmp(name, oldv, len) != 0;
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
    size_t body_start, body_end, section_start;
    if (find_section(Data, Size, "ENTITIES", &body_start, &body_end, &section_start)) {
        size_t count = 0;
        size_t pos = body_start;
        while (pos < body_end) {
            int code;
            size_t vs, ve, av, cs, ce, ac;
            if (!get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
                Line l = next_line(Data, Size, pos);
                if (!l.ok || l.next <= pos) break;
                pos = l.next;
                continue;
            }
            if (cs >= body_end) break;
            if (code == 0) count++;
            pos = av;
        }
        if (count == 0) return Size;

        uint64_t state = (uint64_t)Seed + 0x9e3779b97f4a7c15ULL;
        state ^= (uint64_t)Size * 0xbf58476d1ce4e5b9ULL;
        state ^= (uint64_t)body_start * 0x94d049bb133111ebULL;
        unsigned k = (unsigned)(rng_next(&state) % (uint64_t)count);

        size_t idx = 0;
        pos = body_start;
        while (pos < body_end) {
            int code;
            size_t vs, ve, av, cs, ce, ac;
            if (!get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
                Line l = next_line(Data, Size, pos);
                if (!l.ok || l.next <= pos) break;
                pos = l.next;
                continue;
            }
            if (cs >= body_end) break;
            if (code == 0) {
                if (idx == k) {
                    size_t oldlen = ve - vs;
                    unsigned newlen = 1 + (unsigned)(rng_next(&state) % 64);
                    if (Size - oldlen + newlen > MaxSize) {
                        if (MaxSize + oldlen < Size) return Size;
                        size_t maxlen = MaxSize - (Size - oldlen);
                        if (maxlen == 0) return Size;
                        if (newlen > maxlen) newlen = (unsigned)maxlen;
                    }
                    if (newlen < 1) return Size;
                    uint8_t name[64];
                    fill_random_name(name, newlen, &state);
                    if (!ensure_differ(name, newlen, Data + vs, oldlen)) return Size;
                    memmove(Data + vs + newlen, Data + ve, Size - ve);
                    memcpy(Data + vs, name, newlen);
                    return Size - oldlen + newlen;
                }
                idx++;
            }
            pos = av;
        }
        return Size;
    } else {
        uint64_t state = (uint64_t)Seed + 0x9e3779b97f4a7c15ULL;
        state ^= (uint64_t)Size * 0xbf58476d1ce4e5b9ULL;
        unsigned nameLen = 1 + (unsigned)(rng_next(&state) % 64);
        uint8_t name[64];
        fill_random_name(name, nameLen, &state);

        const char *prefix = "  0\r\nSECTION\r\n  2\r\nOBJECTS\r\n  0\r\n";
        const char *suffix = "\r\n  0\r\nENDSEC\r\n";
        size_t prefixLen = strlen(prefix);
        size_t suffixLen = strlen(suffix);

        size_t insertPos = Size;
        int foundEOF = 0;
        size_t pos = 0;
        while (pos < Size) {
            int code;
            size_t vs, ve, av, cs, ce, ac;
            if (!get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
                Line l = next_line(Data, Size, pos);
                if (!l.ok || l.next <= pos) break;
                pos = l.next;
                continue;
            }
            if (code == 0 && line_eq(Data, vs, ve, "EOF")) {
                insertPos = cs;
                foundEOF = 1;
                break;
            }
            pos = av;
        }

        int needLead = 0;
        if (!foundEOF && Size > 0 && Data[Size - 1] != '\r' && Data[Size - 1] != '\n') {
            needLead = 1;
        }

        size_t total = (needLead ? 2 : 0) + prefixLen + nameLen + suffixLen;
        if (Size + total > MaxSize) {
            size_t minTotal = (needLead ? 2 : 0) + prefixLen + 1 + suffixLen;
            if (Size + minTotal > MaxSize) return Size;
            size_t avail = MaxSize - Size - (minTotal - 1);
            if (avail < 1) return Size;
            if (nameLen > avail) nameLen = (unsigned)avail;
            total = (needLead ? 2 : 0) + prefixLen + nameLen + suffixLen;
        }

        uint8_t seq[512];
        size_t L = 0;
        if (needLead) {
            seq[L++] = '\r';
            seq[L++] = '\n';
        }
        memcpy(seq + L, prefix, prefixLen); L += prefixLen;
        memcpy(seq + L, name, nameLen); L += nameLen;
        memcpy(seq + L, suffix, suffixLen); L += suffixLen;
        if (L > sizeof(seq)) return Size;
        if (insertPos > Size) insertPos = Size;
        memmove(Data + insertPos + L, Data + insertPos, Size - insertPos);
        memcpy(Data + insertPos, seq, L);
        return Size + L;
    }
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    if (!is_dxf_input(Data, Size)) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    unsigned r = Seed % 1000;
    if (r < 500) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    } else {
        return mutate_a001(Data, Size, MaxSize, Seed);
    }
}
