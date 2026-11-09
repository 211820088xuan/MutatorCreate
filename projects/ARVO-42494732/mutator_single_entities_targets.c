#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

static int next_line(const uint8_t *Data, size_t Size, size_t pos,
                     size_t *line_start, size_t *line_end, size_t *next_pos) {
    if (pos >= Size) return 0;
    *line_start = pos;
    size_t p = pos;
    while (p < Size && Data[p] != '\n' && Data[p] != '\r') p++;
    *line_end = p;
    if (p < Size) {
        if (Data[p] == '\r') {
            p++;
            if (p < Size && Data[p] == '\n') p++;
        } else {
            p++;
        }
    }
    *next_pos = p;
    return 1;
}

static int parse_group_code(const uint8_t *Data, size_t start, size_t end, int *code) {
    size_t p = start;
    while (p < end && (Data[p] == ' ' || Data[p] == '\t')) p++;
    if (p >= end) return 0;
    int val = 0;
    int nd = 0;
    while (p < end && Data[p] >= '0' && Data[p] <= '9' && nd < 3) {
        val = val * 10 + (Data[p] - '0');
        p++;
        nd++;
    }
    if (nd == 0) return 0;
    *code = val;
    return 1;
}

typedef struct {
    size_t code_start;
    size_t code_end;
    size_t code_next;
    size_t val_start;
    size_t val_end;
    size_t next;
    int code;
    int has_value;
} DxfRecord;

static int next_record(const uint8_t *Data, size_t Size, size_t *pos, DxfRecord *rec) {
    size_t cs, ce, cn;
    if (!next_line(Data, Size, *pos, &cs, &ce, &cn)) return 0;
    rec->code_start = cs;
    rec->code_end = ce;
    rec->code_next = cn;
    rec->code = -1;
    parse_group_code(Data, cs, ce, &rec->code);
    size_t vs, ve, vn;
    if (!next_line(Data, Size, cn, &vs, &ve, &vn)) {
        rec->val_start = rec->val_end = cn;
        rec->next = cn;
        rec->has_value = 0;
        *pos = cn;
        return 1;
    }
    rec->val_start = vs;
    rec->val_end = ve;
    rec->next = vn;
    rec->has_value = 1;
    *pos = vn;
    return 1;
}

static int value_equals(const uint8_t *Data, const DxfRecord *rec, const char *s) {
    if (!rec->has_value) return 0;
    size_t len = strlen(s);
    if (rec->val_end - rec->val_start != len) return 0;
    return memcmp(Data + rec->val_start, s, len) == 0;
}

static int find_objects_section(const uint8_t *Data, size_t Size,
                                size_t *section_start, size_t *section_end,
                                size_t *candidate_count) {
    size_t pos = 0;
    DxfRecord rec;
    int expecting_name = 0;
    int in_objects = 0;
    int found = 0;
    size_t start = 0, end = Size;
    size_t count = 0;
    while (next_record(Data, Size, &pos, &rec)) {
        if (rec.has_value && rec.code == 0 && value_equals(Data, &rec, "SECTION")) {
            expecting_name = 1;
            in_objects = 0;
            continue;
        }
        if (expecting_name) {
            if (rec.code == 2 && rec.has_value) {
                if (value_equals(Data, &rec, "OBJECTS")) {
                    in_objects = 1;
                    found = 1;
                    start = rec.next;
                } else {
                    in_objects = 0;
                }
                expecting_name = 0;
                continue;
            } else {
                expecting_name = 0;
            }
        }
        if (in_objects) {
            if (rec.code == 0 && rec.has_value && value_equals(Data, &rec, "ENDSEC")) {
                end = rec.code_start;
                break;
            }
            if (rec.code == 0 && rec.has_value && !value_equals(Data, &rec, "ENDSEC")) {
                count++;
            }
        }
    }
    if (!found) return 0;
    *section_start = start;
    *section_end = end;
    *candidate_count = count;
    return 1;
}

static uint64_t next_rand(uint64_t *state) {
    uint64_t x = *state;
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    x ^= x >> 31;
    *state = x + 0x9e3779b97f4a7c15ULL;
    return *state;
}

static void gen_random_name(unsigned Seed, char *out, size_t max_len,
                            const uint8_t *orig, size_t orig_len,
                            size_t *out_len) {
    static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    uint64_t state = (uint64_t)Seed + 0x9e3779b97f4a7c15ULL;
    uint64_t r = next_rand(&state);
    size_t len = (size_t)(r % 64) + 1;
    if (len > max_len) len = max_len;
    if (len == 0) { *out_len = 0; return; }
    for (size_t i = 0; i < len; i++) {
        uint64_t v = next_rand(&state);
        out[i] = alphabet[(size_t)(v % 64)];
    }
    if (orig && orig_len > 0 && len == orig_len && memcmp(out, orig, len) == 0) {
        size_t k = 0;
        for (; k < 64; k++) {
            if (alphabet[k] == out[len - 1]) break;
        }
        out[len - 1] = alphabet[(k + 1) % 64];
    }
    *out_len = len;
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
    size_t section_start = 0, section_end = 0, count = 0;
    int has_section = find_objects_section(Data, Size, &section_start, &section_end, &count);

    if (has_section && count > 0) {
        size_t k = (size_t)Seed % count;
        size_t pos = section_start;
        DxfRecord rec;
        size_t seen = 0;
        while (pos < section_end && next_record(Data, Size, &pos, &rec)) {
            if (rec.code_start >= section_end) break;
            if (rec.code == 0 && rec.has_value && !value_equals(Data, &rec, "ENDSEC")) {
                if (seen == k) {
                    size_t old_len = rec.val_end - rec.val_start;
                    if (Size > MaxSize) return Size;
                    size_t tail = Size - old_len;
                    if (tail > MaxSize) return Size;
                    size_t max_new = MaxSize - tail;
                    if (max_new > 64) max_new = 64;
                    if (max_new < 1) return Size;
                    char name[64];
                    size_t new_len = 0;
                    gen_random_name(Seed, name, max_new, Data + rec.val_start, old_len, &new_len);
                    if (new_len == 0) return Size;
                    size_t new_size = Size - old_len + new_len;
                    if (new_size > MaxSize) return Size;
                    if (new_len != old_len) {
                        memmove(Data + rec.val_start + new_len,
                                Data + rec.val_end,
                                Size - rec.val_end);
                    }
                    memcpy(Data + rec.val_start, name, new_len);
                    return new_size;
                }
                seen++;
            }
        }
        return Size;
    }

    size_t pos = 0;
    DxfRecord rec;
    size_t insert_pos = Size;
    int found_eof = 0;
    while (next_record(Data, Size, &pos, &rec)) {
        if (rec.code == 0 && rec.has_value && value_equals(Data, &rec, "EOF")) {
            insert_pos = rec.code_start;
            found_eof = 1;
            break;
        }
    }

    int need_leading_newline = 0;
    if (!found_eof) {
        insert_pos = Size;
        if (Size > 0 && Data[Size - 1] != '\n' && Data[Size - 1] != '\r') {
            need_leading_newline = 1;
        }
    }

    const char *pre = "0\r\nSECTION\r\n2\r\nOBJECTS\r\n0\r\n";
    const char *post = "\r\n0\r\nENDSEC\r\n";
    size_t pre_len = strlen(pre);
    size_t post_len = strlen(post);
    size_t overhead = pre_len + post_len + (need_leading_newline ? 2 : 0);
    if (overhead > MaxSize) return Size;
    if (Size > MaxSize - overhead) return Size;
    size_t max_name = MaxSize - Size - overhead;
    if (max_name > 64) max_name = 64;
    if (max_name < 1) return Size;

    char name[64];
    size_t name_len = 0;
    gen_random_name(Seed, name, max_name, NULL, 0, &name_len);
    if (name_len == 0) return Size;

    size_t add_len = overhead + name_len;
    if (Size + add_len > MaxSize) return Size;
    memmove(Data + insert_pos + add_len, Data + insert_pos, Size - insert_pos);

    uint8_t *p = Data + insert_pos;
    if (need_leading_newline) {
        *p++ = '\r';
        *p++ = '\n';
    }
    memcpy(p, pre, pre_len);
    p += pre_len;
    memcpy(p, name, name_len);
    p += name_len;
    memcpy(p, post, post_len);
    p += post_len;

    return Size + add_len;
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
    if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    if (Size >= 1 && Data[0] == '{') {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    unsigned r = Seed % 1000;
    if (r < 500) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    return mutate_a001(Data, Size, MaxSize, Seed);
}
