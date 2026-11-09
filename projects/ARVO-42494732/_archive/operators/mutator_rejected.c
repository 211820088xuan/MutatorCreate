#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct { size_t start; size_t content_end; size_t next; size_t eol_len; } DLine;

static unsigned rng_next(unsigned *s) { unsigned x = *s; if (x == 0) x = 0x6d2b79f5u; x ^= x << 13; x ^= x >> 17; x ^= x << 5; *s = x; return x; }

static int dl_next(const uint8_t *d, size_t n, size_t pos, DLine *ln) {
    if (pos >= n) return 0;
    ln->start = pos;
    size_t p = pos;
    while (p < n && d[p] != 13 && d[p] != 10) p++;
    ln->content_end = p;
    if (p < n) {
        if (d[p] == 13 && p + 1 < n && d[p + 1] == 10) { ln->eol_len = 2; ln->next = p + 2; }
        else { ln->eol_len = 1; ln->next = p + 1; }
    } else { ln->eol_len = 0; ln->next = p; }
    return 1;
}

static int line_eq(const uint8_t *d, size_t a, size_t b, const char *s) {
    while (a < b && (d[a] == ' ' || d[a] == 9)) a++;
    while (b > a && (d[b - 1] == ' ' || d[b - 1] == 9)) b--;
    size_t n = strlen(s);
    if (b - a != n) return 0;
    return memcmp(d + a, s, n) == 0;
}

static int parse_code(const uint8_t *d, const DLine *ln, int *out) {
    size_t p = ln->start, e = ln->content_end;
    while (p < e && (d[p] == ' ' || d[p] == 9)) p++;
    if (p >= e) return 0;
    int sign = 1;
    if (d[p] == '+' || d[p] == '-') { if (d[p] == '-') sign = -1; p++; }
    if (p >= e || d[p] < '0' || d[p] > '9') return 0;
    int v = 0, digits = 0;
    while (p < e && d[p] >= '0' && d[p] <= '9') { if (digits < 3) v = v * 10 + (d[p] - '0'); digits++; p++; }
    if (digits < 1 || digits > 3) return 0;
    while (p < e && (d[p] == ' ' || d[p] == 9)) p++;
    if (p != e) return 0;
    *out = sign * v;
    return 1;
}

static int is_code0(const uint8_t *d, const DLine *ln) { int c; return parse_code(d, ln, &c) && c == 0; }

static int looks_like_dxf(const uint8_t *d, size_t n) {
    int has_section = 0, has_eof = 0;
    size_t pos = 0; DLine ln;
    while (dl_next(d, n, pos, &ln)) {
        if (line_eq(d, ln.start, ln.content_end, "SECTION")) has_section = 1;
        if (line_eq(d, ln.start, ln.content_end, "EOF")) has_eof = 1;
        if (ln.next <= pos) break;
        pos = ln.next;
        if (pos >= n) break;
    }
    return has_section && has_eof;
}

static int find_section(const uint8_t *d, size_t n, const char *anchor, size_t *sec_start, size_t *sec_end) {
    size_t pos = 0; DLine ln; int found = 0; size_t after = 0;
    while (dl_next(d, n, pos, &ln)) {
        if (!found && line_eq(d, ln.start, ln.content_end, anchor)) { found = 1; after = ln.next; }
        else if (found && line_eq(d, ln.start, ln.content_end, "ENDSEC")) { *sec_start = after; *sec_end = ln.start; return 1; }
        if (ln.next <= pos) break;
        pos = ln.next;
        if (pos >= n) break;
    }
    if (found) { *sec_start = after; *sec_end = n; return 1; }
    return 0;
}

static int count_candidates(const uint8_t *d, size_t n, size_t start, size_t end) {
    size_t pos = start; DLine ln; int count = 0;
    while (pos < end && dl_next(d, n, pos, &ln)) {
        if (ln.start >= end) break;
        if (is_code0(d, &ln)) {
            DLine vl;
            if (dl_next(d, n, ln.next, &vl) && vl.start < end && !line_eq(d, vl.start, vl.content_end, "ENDSEC")) count++;
        }
        if (ln.next <= pos) break;
        pos = ln.next;
        if (pos >= n) break;
    }
    return count;
}

static int find_kth_candidate(const uint8_t *d, size_t n, size_t start, size_t end, unsigned k, DLine *out_vl) {
    size_t pos = start; DLine ln; unsigned idx = 0;
    while (pos < end && dl_next(d, n, pos, &ln)) {
        if (ln.start >= end) break;
        if (is_code0(d, &ln)) {
            DLine vl;
            if (dl_next(d, n, ln.next, &vl) && vl.start < end && !line_eq(d, vl.start, vl.content_end, "ENDSEC")) {
                if (idx == k) { *out_vl = vl; return 1; }
                idx++;
            }
        }
        if (ln.next <= pos) break;
        pos = ln.next;
        if (pos >= n) break;
    }
    return 0;
}

static size_t make_name(uint8_t *out, size_t cap, unsigned Seed, unsigned salt, const uint8_t *old, size_t old_len) {
    static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    unsigned state = Seed ^ salt ^ 0x9e3779b9u;
    if (state == 0) state = 1;
    unsigned r = rng_next(&state);
    size_t len = 1 + (r % 64);
    if (len > cap) len = cap;
    size_t i;
    for (i = 0; i < len; i++) out[i] = (uint8_t)alphabet[rng_next(&state) % 64];
    if (old != 0 && old_len == len && memcmp(out, old, len) == 0) {
        size_t idx = 0;
        while (idx < 64 && alphabet[idx] != (char)out[0]) idx++;
        out[0] = (uint8_t)alphabet[(idx + 1) % 64];
    }
    return len;
}

static size_t replace_line_content(uint8_t *Data, size_t Size, size_t MaxSize, size_t start, size_t end, const uint8_t *name, size_t name_len) {
    if (end < start || end > Size) return (size_t)-1;
    size_t old_len = end - start;
    if (name_len > MaxSize || Size - old_len > MaxSize - name_len) return (size_t)-1;
    size_t new_size = Size - old_len + name_len;
    if (new_size > MaxSize) return (size_t)-1;
    memmove(Data + start + name_len, Data + end, Size - end);
    memcpy(Data + start, name, name_len);
    return new_size;
}

static void append_bytes(uint8_t *dst, size_t *pos, const void *src, size_t n) {
    memcpy(dst + *pos, src, n);
    *pos += n;
}

static void append_str(uint8_t *dst, size_t *pos, const char *s) {
    size_t n = strlen(s);
    append_bytes(dst, pos, s, n);
}

static size_t construct_objects_section(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed, unsigned salt) {
    static const uint8_t CRLF[2] = {13, 10};
    uint8_t name[64];
    uint8_t ins[512];
    size_t name_len = make_name(name, sizeof(name), Seed, salt, 0, 0);
    size_t ip = 0;
    append_str(ins, &ip, "  0"); append_bytes(ins, &ip, CRLF, 2);
    append_str(ins, &ip, "SECTION"); append_bytes(ins, &ip, CRLF, 2);
    append_str(ins, &ip, "  2"); append_bytes(ins, &ip, CRLF, 2);
    append_str(ins, &ip, "OBJECTS"); append_bytes(ins, &ip, CRLF, 2);
    append_str(ins, &ip, "  0"); append_bytes(ins, &ip, CRLF, 2);
    append_bytes(ins, &ip, name, name_len); append_bytes(ins, &ip, CRLF, 2);
    append_str(ins, &ip, "  0"); append_bytes(ins, &ip, CRLF, 2);
    append_str(ins, &ip, "ENDSEC"); append_bytes(ins, &ip, CRLF, 2);
    if (Size > MaxSize || ip > MaxSize - Size) return (size_t)-1;
    size_t insert = Size;
    size_t pos = 0; DLine ln;
    while (dl_next(Data, Size, pos, &ln)) {
        int c;
        if (parse_code(Data, &ln, &c) && c == 0) {
            DLine vl;
            if (dl_next(Data, Size, ln.next, &vl) && line_eq(Data, vl.start, vl.content_end, "EOF")) { insert = ln.start; break; }
        }
        if (ln.next <= pos) break;
        pos = ln.next;
        if (pos >= Size) break;
    }
    memmove(Data + insert + ip, Data + insert, Size - insert);
    memcpy(Data + insert, ins, ip);
    return Size + ip;
}

static size_t mutate_value_line_seed(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed, unsigned salt) {
    size_t sec_start = 0, sec_end = 0;
    if (!find_section(Data, Size, "OBJECTS", &sec_start, &sec_end)) return construct_objects_section(Data, Size, MaxSize, Seed, salt);
    int count = count_candidates(Data, Size, sec_start, sec_end);
    if (count <= 0) return (size_t)-1;
    unsigned state = Seed ^ salt ^ 0x9e3779b9u;
    if (state == 0) state = 1;
    unsigned k = rng_next(&state) % (unsigned)count;
    DLine vl;
    if (!find_kth_candidate(Data, Size, sec_start, sec_end, k, &vl)) return (size_t)-1;
    uint8_t name[64];
    size_t name_len = make_name(name, sizeof(name), Seed, salt, Data + vl.start, vl.content_end - vl.start);
    return replace_line_content(Data, Size, MaxSize, vl.start, vl.content_end, name, name_len);
}

static size_t strategy_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) { return mutate_value_line_seed(Data, Size, MaxSize, Seed, 0xA001u); }
static size_t strategy_a002(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) { return mutate_value_line_seed(Data, Size, MaxSize, Seed, 0xA002u); }
static size_t strategy_a003(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) { return mutate_value_line_seed(Data, Size, MaxSize, Seed, 0xA003u); }

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    if (!looks_like_dxf(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
    unsigned r = Seed % 1000u;
    if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);
    unsigned q = r - 500u;
    size_t out = (size_t)-1;
    if (q < 167u) out = strategy_a001(Data, Size, MaxSize, Seed);
    else if (q < 334u) out = strategy_a002(Data, Size, MaxSize, Seed);
    else out = strategy_a003(Data, Size, MaxSize, Seed);
    if (out == (size_t)-1) return LLVMFuzzerMutate(Data, Size, MaxSize);
    return out;
}
