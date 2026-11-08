#include <stdint.h>
#include <stddef.h>
#include <string.h>

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

static void get_line(const uint8_t *data, size_t size, size_t pos, size_t *content_end, size_t *next_pos) {
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

static int parse_group_code(const uint8_t *data, size_t start, size_t end) {
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

static int next_dxf_record(const uint8_t *data, size_t size, size_t pos, DxfRec *r) {
    while (pos < size) {
        size_t ce, np;
        get_line(data, size, pos, &ce, &np);
        int code = parse_group_code(data, pos, ce);
        if (code < 0) {
            pos = np;
            continue;
        }
        size_t ve = np, vnp = np;
        if (np < size) {
            get_line(data, size, np, &ve, &vnp);
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

static int value_equals_trim(const uint8_t *data, size_t start, size_t end, const char *s) {
    while (start < end && (data[start] == ' ' || data[start] == DXF_TAB)) start++;
    while (end > start && (data[end - 1] == ' ' || data[end - 1] == DXF_TAB)) end--;
    size_t n = strlen(s);
    if (end - start != n) return 0;
    for (size_t i = 0; i < n; i++) {
        if (data[start + i] != (uint8_t)s[i]) return 0;
    }
    return 1;
}

static uint32_t rng_init(uint32_t seed) {
    uint32_t s = seed + 0x9e3779b9u;
    s ^= 0xA5A5A5A5u;
    if (s == 0) s = 1;
    return s;
}

static uint32_t rng_next(uint32_t *s) {
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x;
    return x;
}

static size_t make_random_name(uint32_t seed, const uint8_t *orig, size_t orig_len, uint8_t *out, size_t cap) {
    static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    const size_t alpha_len = sizeof(alphabet) - 1;
    if (cap == 0) return 0;
    if (cap > 64) cap = 64;
    uint32_t s = rng_init(seed ^ 0x51ED270Bu);
    size_t len = 1 + (rng_next(&s) % cap);
    if (len > cap) len = cap;
    for (size_t i = 0; i < len; i++) {
        out[i] = (uint8_t)alphabet[rng_next(&s) % alpha_len];
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

static int find_objects_section(const uint8_t *data, size_t size,
                                size_t *section_start,
                                size_t *section_end_record_start) {
    size_t pos = 0;
    DxfRec r;
    while (next_dxf_record(data, size, pos, &r)) {
        pos = r.next_pos;
        if (r.code == 2 && value_equals_trim(data, r.val_start, r.val_end, "OBJECTS")) {
            size_t start = r.next_pos;
            size_t p = start;
            DxfRec q;
            while (next_dxf_record(data, size, p, &q)) {
                p = q.next_pos;
                if (q.code == 0 && value_equals_trim(data, q.val_start, q.val_end, "ENDSEC")) {
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

static int is_candidate_code0(const uint8_t *data, const DxfRec *r) {
    if (r->code != 0) return 0;
    if (value_equals_trim(data, r->val_start, r->val_end, "ENDSEC")) return 0;
    if (value_equals_trim(data, r->val_start, r->val_end, "SECTION")) return 0;
    if (value_equals_trim(data, r->val_start, r->val_end, "EOF")) return 0;
    return 1;
}

static size_t count_candidates(const uint8_t *data, size_t size, size_t start, size_t end) {
    size_t count = 0;
    size_t pos = start;
    DxfRec r;
    while (pos < end && next_dxf_record(data, size, pos, &r)) {
        if (r.code_start >= end) break;
        pos = r.next_pos;
        if (is_candidate_code0(data, &r)) count++;
    }
    return count;
}

static int find_kth_candidate(const uint8_t *data, size_t size, size_t start, size_t end, size_t k, DxfRec *out) {
    size_t idx = 0;
    size_t pos = start;
    DxfRec r;
    while (pos < end && next_dxf_record(data, size, pos, &r)) {
        if (r.code_start >= end) break;
        pos = r.next_pos;
        if (is_candidate_code0(data, &r)) {
            if (idx == k) {
                *out = r;
                return 1;
            }
            idx++;
        }
    }
    return 0;
}

static int find_eof_record_start(const uint8_t *data, size_t size, size_t *out) {
    size_t pos = 0;
    DxfRec r;
    while (next_dxf_record(data, size, pos, &r)) {
        pos = r.next_pos;
        if (r.code == 0 && value_equals_trim(data, r.val_start, r.val_end, "EOF")) {
            *out = r.code_start;
            return 1;
        }
    }
    return 0;
}

static size_t action_a001(uint8_t *data, size_t size, size_t max_size, unsigned int seed) {
    if (max_size < size) return size;
    size_t section_start = 0, section_end = 0;
    if (find_objects_section(data, size, &section_start, &section_end)) {
        size_t count = count_candidates(data, size, section_start, section_end);
        if (count == 0) return size;
        uint32_t sel_state = rng_init((uint32_t)seed ^ 0x1234567u);
        size_t k = (size_t)(rng_next(&sel_state) % count);
        DxfRec rec;
        if (!find_kth_candidate(data, size, section_start, section_end, k, &rec)) return size;
        size_t old_len = rec.val_end - rec.val_start;
        if (max_size < size - old_len + 1) return size;
        size_t cap = max_size - (size - old_len);
        uint8_t name[64];
        size_t new_len = make_random_name((uint32_t)seed, data + rec.val_start, old_len, name, cap);
        if (new_len == 0) return size;
        if (max_size < size - old_len + new_len) return size;
        if (new_len != old_len) {
            memmove(data + rec.val_start + new_len, data + rec.val_end, size - rec.val_end);
        }
        memcpy(data + rec.val_start, name, new_len);
        return size - old_len + new_len;
    }

    size_t insert_pos = size;
    int have_eof = find_eof_record_start(data, size, &insert_pos);
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
    size_t name_len = make_random_name((uint32_t)seed, NULL, 0, name, cap);
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

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
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
    return action_a001(Data, Size, MaxSize, Seed);
}
