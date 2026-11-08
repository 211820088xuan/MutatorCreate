/* R37 多策略算子（由 tools/r37_assemble.py 机械生成，不要手改）
 *
 * 模式 B：并列拼接。每个策略保留完整函数体，符号加了 sNNN_ 前缀。
 * 分流只用 Seed，不读 Data —— 否则等价性验证做不了。
 *
 * 策略清单：
 *   001. OBJECTS 段  (mutator_single_OBJECTS.c, 16 个 local 符号, 前缀 s001_)
 *   002. ENTITIES 段  (mutator_single_ENTITIES_r36_63b23547.c, 12 个 local 符号, 前缀 s002_)
 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

/* ───── 策略 1: OBJECTS 段 (原文件 mutator_single_OBJECTS.c) ───── */
#define DXF_CR 13
#define DXF_LF 10
#define DXF_TAB 9

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct {
    size_t code_start;
    size_t code_end;
    size_t val_start;
    size_t val_end;
    size_t next_pos;
    int code;
} DxfRec;

static void s001_get_line(const uint8_t *data, size_t size, size_t pos, size_t *content_end, size_t *next_pos) {
    size_t i = pos;
    while (i < size && data[i] != DXF_CR && data[i] != DXF_LF) i++;
    *content_end = i;
    if (i < size) {
        if (data[i] == DXF_CR) {
            if (i + 1 < size && data[i + 1] == DXF_LF) *next_pos = i + 2;
            else *next_pos = i + 1;
        } else {
            *next_pos = i + 1;
        }
    } else {
        *next_pos = size;
    }
}

static int s001_parse_group_code(const uint8_t *data, size_t start, size_t end) {
    size_t i = start;
    while (i < end && (data[i] == ' ' || data[i] == DXF_TAB)) i++;
    if (i >= end) return -1;
    int val = 0;
    int digits = 0;
    while (i < end && data[i] >= '0' && data[i] <= '9') {
        if (digits >= 3) return -1;
        val = val * 10 + (int)(data[i] - '0');
        digits++;
        i++;
    }
    if (digits == 0) return -1;
    while (i < end && (data[i] == ' ' || data[i] == DXF_TAB)) i++;
    if (i != end) return -1;
    return val;
}

static int s001_next_dxf_record(const uint8_t *data, size_t size, size_t pos, DxfRec *r) {
    while (pos < size) {
        size_t ce, np;
        s001_get_line(data, size, pos, &ce, &np);
        int code = s001_parse_group_code(data, pos, ce);
        if (code < 0) {
            pos = np;
            continue;
        }
        size_t ve = np, vnp = np;
        if (np < size) {
            s001_get_line(data, size, np, &ve, &vnp);
        } else {
            ve = np;
            vnp = np;
        }
        r->code_start = pos;
        r->code_end = ce;
        r->val_start = np;
        r->val_end = ve;
        r->next_pos = vnp;
        r->code = code;
        return 1;
    }
    return 0;
}

static int s001_value_equals_trim(const uint8_t *data, size_t start, size_t end, const char *s) {
    while (start < end && (data[start] == ' ' || data[start] == DXF_TAB)) start++;
    while (end > start && (data[end - 1] == ' ' || data[end - 1] == DXF_TAB)) end--;
    size_t n = strlen(s);
    if (end - start != n) return 0;
    for (size_t i = 0; i < n; i++) {
        if (data[start + i] != (uint8_t)s[i]) return 0;
    }
    return 1;
}

static uint32_t s001_rng_init(uint32_t seed) {
    uint32_t s = seed + 0x9e3779b9u;
    s ^= 0xA5A5A5A5u;
    if (s == 0) s = 1;
    return s;
}

static uint32_t s001_rng_next(uint32_t *s) {
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x;
    return x;
}

static size_t s001_make_random_name(uint32_t seed, const uint8_t *orig, size_t orig_len, uint8_t *out, size_t cap) {
    static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    const size_t alpha_len = sizeof(alphabet) - 1;
    if (cap == 0) return 0;
    if (cap > 64) cap = 64;
    uint32_t s = s001_rng_init(seed ^ 0x51ED270Bu);
    size_t len = 1 + (s001_rng_next(&s) % cap);
    if (len > cap) len = cap;
    for (size_t i = 0; i < len; i++) {
        out[i] = (uint8_t)alphabet[s001_rng_next(&s) % alpha_len];
    }
    if (len == orig_len && orig != NULL) {
        int same = 1;
        for (size_t i = 0; i < len; i++) {
            if (out[i] != orig[i]) { same = 0; break; }
        }
        if (same) {
            size_t idx = 0;
            while (idx < alpha_len && (uint8_t)alphabet[idx] != out[0]) idx++;
            out[0] = (uint8_t)alphabet[(idx + 1) % alpha_len];
        }
    }
    return len;
}

static int s001_find_objects_section(const uint8_t *data, size_t size,
                                size_t *section_start,
                                size_t *section_end_record_start) {
    size_t pos = 0;
    DxfRec r;
    while (s001_next_dxf_record(data, size, pos, &r)) {
        pos = r.next_pos;
        if (r.code == 2 && s001_value_equals_trim(data, r.val_start, r.val_end, "OBJECTS")) {
            size_t start = r.next_pos;
            size_t p = start;
            DxfRec q;
            while (s001_next_dxf_record(data, size, p, &q)) {
                p = q.next_pos;
                if (q.code == 0 && s001_value_equals_trim(data, q.val_start, q.val_end, "ENDSEC")) {
                    *section_start = start;
                    *section_end_record_start = q.code_start;
                    return 1;
                }
            }
            *section_start = start;
            *section_end_record_start = size;
            return 1;
        }
    }
    return 0;
}

static int s001_is_candidate_code0(const uint8_t *data, const DxfRec *r) {
    if (r->code != 0) return 0;
    if (s001_value_equals_trim(data, r->val_start, r->val_end, "ENDSEC")) return 0;
    if (s001_value_equals_trim(data, r->val_start, r->val_end, "SECTION")) return 0;
    if (s001_value_equals_trim(data, r->val_start, r->val_end, "EOF")) return 0;
    return 1;
}

static size_t s001_count_candidates(const uint8_t *data, size_t size, size_t start, size_t end) {
    size_t count = 0;
    size_t pos = start;
    DxfRec r;
    while (pos < end && s001_next_dxf_record(data, size, pos, &r)) {
        if (r.code_start >= end) break;
        pos = r.next_pos;
        if (s001_is_candidate_code0(data, &r)) count++;
    }
    return count;
}

static int s001_find_kth_candidate(const uint8_t *data, size_t size, size_t start, size_t end, size_t k, DxfRec *out) {
    size_t idx = 0;
    size_t pos = start;
    DxfRec r;
    while (pos < end && s001_next_dxf_record(data, size, pos, &r)) {
        if (r.code_start >= end) break;
        pos = r.next_pos;
        if (s001_is_candidate_code0(data, &r)) {
            if (idx == k) {
                *out = r;
                return 1;
            }
            idx++;
        }
    }
    return 0;
}

static int s001_find_eof_record_start(const uint8_t *data, size_t size, size_t *out) {
    size_t pos = 0;
    DxfRec r;
    while (s001_next_dxf_record(data, size, pos, &r)) {
        pos = r.next_pos;
        if (r.code == 0 && s001_value_equals_trim(data, r.val_start, r.val_end, "EOF")) {
            *out = r.code_start;
            return 1;
        }
    }
    return 0;
}

static size_t s001_action_a001(uint8_t *data, size_t size, size_t max_size, unsigned int seed) {
    if (max_size < size) return size;
    size_t section_start = 0, section_end = 0;
    if (s001_find_objects_section(data, size, &section_start, &section_end)) {
        size_t count = s001_count_candidates(data, size, section_start, section_end);
        if (count == 0) return size;
        uint32_t sel_state = s001_rng_init((uint32_t)seed ^ 0x1234567u);
        size_t k = (size_t)(s001_rng_next(&sel_state) % count);
        DxfRec rec;
        if (!s001_find_kth_candidate(data, size, section_start, section_end, k, &rec)) return size;
        size_t old_len = rec.val_end - rec.val_start;
        if (max_size < size - old_len + 1) return size;
        size_t cap = max_size - (size - old_len);
        uint8_t name[64];
        size_t new_len = s001_make_random_name((uint32_t)seed, data + rec.val_start, old_len, name, cap);
        if (new_len == 0) return size;
        if (max_size < size - old_len + new_len) return size;
        if (new_len != old_len) {
            memmove(data + rec.val_start + new_len, data + rec.val_end, size - rec.val_end);
        }
        memcpy(data + rec.val_start, name, new_len);
        return size - old_len + new_len;
    }

    size_t insert_pos = size;
    int have_eof = s001_find_eof_record_start(data, size, &insert_pos);
    size_t prefix_len = 0;
    if (!have_eof) {
        insert_pos = size;
        if (size > 0 && data[size - 1] != DXF_CR && data[size - 1] != DXF_LF) prefix_len = 2;
    }
    static const uint8_t pre[] = {
        '0', DXF_CR, DXF_LF,
        'S','E','C','T','I','O','N', DXF_CR, DXF_LF,
        '2', DXF_CR, DXF_LF,
        'O','B','J','E','C','T','S', DXF_CR, DXF_LF,
        '0', DXF_CR, DXF_LF
    };
    static const uint8_t post[] = {
        DXF_CR, DXF_LF,
        '0', DXF_CR, DXF_LF,
        'E','N','D','S','E','C', DXF_CR, DXF_LF
    };
    size_t fixed = prefix_len + sizeof(pre) + sizeof(post);
    if (fixed > max_size || size > max_size - fixed) return size;
    size_t cap = max_size - size - fixed;
    if (cap > 64) cap = 64;
    uint8_t name[64];
    size_t name_len = s001_make_random_name((uint32_t)seed, NULL, 0, name, cap);
    if (name_len == 0) return size;
    size_t insert_len = fixed + name_len;
    if (insert_len > max_size - size) return size;
    uint8_t tmp[256];
    size_t t = 0;
    if (prefix_len == 2) { tmp[t++] = DXF_CR; tmp[t++] = DXF_LF; }
    memcpy(tmp + t, pre, sizeof(pre)); t += sizeof(pre);
    memcpy(tmp + t, name, name_len); t += name_len;
    memcpy(tmp + t, post, sizeof(post)); t += sizeof(post);
    if (t != insert_len) return size;
    memmove(data + insert_pos + insert_len, data + insert_pos, size - insert_pos);
    memcpy(data + insert_pos, tmp, insert_len);
    return size + insert_len;
}

size_t s001_entry(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    if (Size > MaxSize) return 0;
    int is_dxf = 1;
    if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') is_dxf = 0;
    else if (Size >= 1 && Data[0] == '{') is_dxf = 0;
    if (!is_dxf) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    unsigned r = Seed % 1000u;
    if (r < 500u) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    return s001_action_a001(Data, Size, MaxSize, Seed);
}

/* ───── 策略 2: ENTITIES 段 (原文件 mutator_single_ENTITIES_r36_63b23547.c) ───── */
extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct {
    size_t start;
    size_t end;
    size_t next;
    size_t eol_len;
    int ok;
} Line;

static Line s002_next_line(const uint8_t *Data, size_t Size, size_t pos) {
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

static int s002_line_eq(const uint8_t *Data, size_t start, size_t end, const char *s) {
    size_t n = strlen(s);
    if (end < start || end - start != n) return 0;
    for (size_t i = 0; i < n; i++) {
        if (Data[start + i] != (uint8_t)s[i]) return 0;
    }
    return 1;
}

static int s002_parse_code_line(const uint8_t *Data, size_t start, size_t end, int *out) {
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

static int s002_get_pair(const uint8_t *Data, size_t Size, size_t pos,
                    int *code, size_t *val_start, size_t *val_end,
                    size_t *after_val, size_t *code_start,
                    size_t *code_end, size_t *after_code) {
    Line c = s002_next_line(Data, Size, pos);
    if (!c.ok) return 0;
    Line v = s002_next_line(Data, Size, c.next);
    if (!v.ok) return 0;
    int cd;
    if (!s002_parse_code_line(Data, c.start, c.end, &cd)) return 0;
    *code = cd;
    *val_start = v.start;
    *val_end = v.end;
    *after_val = v.next;
    *code_start = c.start;
    *code_end = c.end;
    *after_code = c.next;
    return 1;
}

static int s002_find_section(const uint8_t *Data, size_t Size, const char *name,
                        size_t *body_start, size_t *body_end,
                        size_t *section_start) {
    size_t pos = 0;
    while (pos < Size) {
        int code;
        size_t vs, ve, av, cs, ce, ac;
        if (!s002_get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
            Line l = s002_next_line(Data, Size, pos);
            if (!l.ok || l.next <= pos) break;
            pos = l.next;
            continue;
        }
        if (code == 0 && s002_line_eq(Data, vs, ve, "SECTION")) {
            size_t pos2 = av;
            int c2;
            size_t vs2, ve2, av2, cs2, ce2, ac2;
            if (s002_get_pair(Data, Size, pos2, &c2, &vs2, &ve2, &av2, &cs2, &ce2, &ac2) &&
                c2 == 2 && s002_line_eq(Data, vs2, ve2, name)) {
                *body_start = av2;
                *section_start = cs;
                size_t p = av2;
                while (p < Size) {
                    int c3;
                    size_t vs3, ve3, av3, cs3, ce3, ac3;
                    if (!s002_get_pair(Data, Size, p, &c3, &vs3, &ve3, &av3, &cs3, &ce3, &ac3)) {
                        Line l = s002_next_line(Data, Size, p);
                        if (!l.ok || l.next <= p) break;
                        p = l.next;
                        continue;
                    }
                    if (c3 == 0 && s002_line_eq(Data, vs3, ve3, "ENDSEC")) {
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

static int s002_is_dxf_input(const uint8_t *Data, size_t Size) {
    size_t pos = 0;
    while (pos < Size) {
        int code;
        size_t vs, ve, av, cs, ce, ac;
        if (!s002_get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
            Line l = s002_next_line(Data, Size, pos);
            if (!l.ok || l.next <= pos) break;
            pos = l.next;
            continue;
        }
        if (code == 0 && (s002_line_eq(Data, vs, ve, "SECTION") ||
                          s002_line_eq(Data, vs, ve, "EOF") ||
                          s002_line_eq(Data, vs, ve, "ENDSEC"))) return 1;
        if (code == 2 && s002_line_eq(Data, vs, ve, "ENTITIES")) return 1;
        pos = av;
    }
    return 0;
}

static uint64_t s002_rng_next(uint64_t *s) {
    uint64_t x = *s;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *s = x;
    return x * 2685821657736338717ULL;
}

static void s002_fill_random_name(uint8_t *name, unsigned len, uint64_t *state) {
    static const char alpha[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    size_t alen = sizeof(alpha) - 1;
    for (unsigned i = 0; i < len; i++) {
        name[i] = (uint8_t)alpha[s002_rng_next(state) % alen];
    }
}

static int s002_ensure_differ(uint8_t *name, unsigned len, const uint8_t *oldv, size_t oldlen) {
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

static size_t s002_mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
    size_t body_start, body_end, section_start;
    if (s002_find_section(Data, Size, "ENTITIES", &body_start, &body_end, &section_start)) {
        size_t count = 0;
        size_t pos = body_start;
        while (pos < body_end) {
            int code;
            size_t vs, ve, av, cs, ce, ac;
            if (!s002_get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
                Line l = s002_next_line(Data, Size, pos);
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
        unsigned k = (unsigned)(s002_rng_next(&state) % (uint64_t)count);

        size_t idx = 0;
        pos = body_start;
        while (pos < body_end) {
            int code;
            size_t vs, ve, av, cs, ce, ac;
            if (!s002_get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
                Line l = s002_next_line(Data, Size, pos);
                if (!l.ok || l.next <= pos) break;
                pos = l.next;
                continue;
            }
            if (cs >= body_end) break;
            if (code == 0) {
                if (idx == k) {
                    size_t oldlen = ve - vs;
                    unsigned newlen = 1 + (unsigned)(s002_rng_next(&state) % 64);
                    if (Size - oldlen + newlen > MaxSize) {
                        if (MaxSize + oldlen < Size) return Size;
                        size_t maxlen = MaxSize - (Size - oldlen);
                        if (maxlen == 0) return Size;
                        if (newlen > maxlen) newlen = (unsigned)maxlen;
                    }
                    if (newlen < 1) return Size;
                    uint8_t name[64];
                    s002_fill_random_name(name, newlen, &state);
                    if (!s002_ensure_differ(name, newlen, Data + vs, oldlen)) return Size;
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
        unsigned nameLen = 1 + (unsigned)(s002_rng_next(&state) % 64);
        uint8_t name[64];
        s002_fill_random_name(name, nameLen, &state);

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
            if (!s002_get_pair(Data, Size, pos, &code, &vs, &ve, &av, &cs, &ce, &ac)) {
                Line l = s002_next_line(Data, Size, pos);
                if (!l.ok || l.next <= pos) break;
                pos = l.next;
                continue;
            }
            if (code == 0 && s002_line_eq(Data, vs, ve, "EOF")) {
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

size_t s002_entry(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    if (!s002_is_dxf_input(Data, Size)) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    unsigned r = Seed % 1000;
    if (r < 500) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    } else {
        return s002_mutate_a001(Data, Size, MaxSize, Seed);
    }
}


size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize,
                               unsigned int Seed)
{
  unsigned int r = Seed % 1000u;
  if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);   /* default 0.50 */
  if (r < 750u) return s001_entry(Data, Size, MaxSize, Seed);   /* 0.25 */
  return s002_entry(Data, Size, MaxSize, Seed);                   /* 0.25 */
}
