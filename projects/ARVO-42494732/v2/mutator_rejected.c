#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct {
    size_t start;
    size_t content_end;
    size_t eol_start;
    size_t next;
} Line;

typedef struct {
    int found;
    size_t content_start;
    size_t endsec_start;
} SectionInfo;

static int next_line(const uint8_t *Data, size_t Size, size_t pos, Line *out) {
    if (pos >= Size) return 0;
    size_t i = pos;
    while (i < Size && Data[i] != '\n' && Data[i] != '\r') i++;
    out->start = pos;
    out->content_end = i;
    out->eol_start = i;
    if (i < Size) {
        if (Data[i] == '\r') {
            if (i + 1 < Size && Data[i + 1] == '\n') out->next = i + 2;
            else out->next = i + 1;
        } else {
            out->next = i + 1;
        }
    } else {
        out->next = Size;
    }
    return 1;
}

static int is_space_tab(uint8_t c) {
    return c == ' ' || c == '\t';
}

static int parse_group_code(const uint8_t *Data, const Line *line, int *code_out) {
    size_t i = line->start;
    while (i < line->content_end && is_space_tab(Data[i])) i++;
    if (i >= line->content_end) return 0;
    if (Data[i] < '0' || Data[i] > '9') return 0;
    int value = 0;
    int digits = 0;
    while (i < line->content_end && Data[i] >= '0' && Data[i] <= '9') {
        value = value * 10 + (int)(Data[i] - '0');
        i++;
        digits++;
        if (digits > 3 || value > 999) return 0;
    }
    while (i < line->content_end) {
        if (!is_space_tab(Data[i])) return 0;
        i++;
    }
    if (digits == 0) return 0;
    *code_out = value;
    return 1;
}

static int line_equals(const uint8_t *Data, const Line *line, const char *s) {
    size_t len = strlen(s);
    if (line->content_end < line->start) return 0;
    if (line->content_end - line->start != len) return 0;
    return memcmp(Data + line->start, s, len) == 0;
}

static void find_object_section(const uint8_t *Data, size_t Size, SectionInfo *info) {
    info->found = 0;
    info->content_start = 0;
    info->endsec_start = Size;
    size_t pos = 0;
    while (pos < Size) {
        Line l1;
        if (!next_line(Data, Size, pos, &l1)) break;
        int code1;
        if (!parse_group_code(Data, &l1, &code1)) {
            pos = l1.next;
            continue;
        }
        Line l2;
        if (!next_line(Data, Size, l1.next, &l2)) break;
        if (code1 == 0 && line_equals(Data, &l2, "SECTION")) {
            size_t p2 = l2.next;
            Line l3;
            if (next_line(Data, Size, p2, &l3)) {
                int code2;
                if (parse_group_code(Data, &l3, &code2)) {
                    Line l4;
                    if (next_line(Data, Size, l3.next, &l4)) {
                        if (code2 == 2 && line_equals(Data, &l4, "OBJECTS")) {
                            info->found = 1;
                            info->content_start = l4.next;
                            size_t p = info->content_start;
                            while (p < Size) {
                                Line c1;
                                if (!next_line(Data, Size, p, &c1)) break;
                                int cc;
                                if (!parse_group_code(Data, &c1, &cc)) {
                                    p = c1.next;
                                    continue;
                                }
                                Line c2;
                                if (!next_line(Data, Size, c1.next, &c2)) break;
                                if (cc == 0 && line_equals(Data, &c2, "ENDSEC")) {
                                    info->endsec_start = c1.start;
                                    return;
                                }
                                p = c2.next;
                            }
                            info->endsec_start = Size;
                            return;
                        }
                    }
                }
            }
        }
        pos = l2.next;
    }
}

static size_t count_code0_records(const uint8_t *Data, size_t Size, size_t start, size_t end) {
    size_t count = 0;
    size_t pos = start;
    while (pos < end && pos < Size) {
        Line l1;
        if (!next_line(Data, Size, pos, &l1)) break;
        if (l1.start >= end) break;
        int code;
        if (!parse_group_code(Data, &l1, &code)) {
            pos = l1.next;
            continue;
        }
        Line l2;
        if (!next_line(Data, Size, l1.next, &l2)) break;
        if (code == 0) count++;
        pos = l2.next;
    }
    return count;
}

static int get_kth_code0_value_line(const uint8_t *Data, size_t Size, size_t start, size_t end, size_t k, Line *out) {
    size_t idx = 0;
    size_t pos = start;
    while (pos < end && pos < Size) {
        Line l1;
        if (!next_line(Data, Size, pos, &l1)) break;
        if (l1.start >= end) break;
        int code;
        if (!parse_group_code(Data, &l1, &code)) {
            pos = l1.next;
            continue;
        }
        Line l2;
        if (!next_line(Data, Size, l1.next, &l2)) break;
        if (code == 0) {
            if (idx == k) {
                *out = l2;
                return 1;
            }
            idx++;
        }
        pos = l2.next;
    }
    return 0;
}

static size_t find_eof_record_start(const uint8_t *Data, size_t Size) {
    size_t pos = 0;
    while (pos < Size) {
        Line l1;
        if (!next_line(Data, Size, pos, &l1)) break;
        int code;
        if (!parse_group_code(Data, &l1, &code)) {
            pos = l1.next;
            continue;
        }
        Line l2;
        if (!next_line(Data, Size, l1.next, &l2)) break;
        if (code == 0 && line_equals(Data, &l2, "EOF")) return l1.start;
        pos = l2.next;
    }
    return (size_t)-1;
}

static uint64_t rng_next(uint64_t *state) {
    *state += 0x9E3779B97F4A7C15ULL;
    uint64_t z = *state;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static size_t gen_random_name(uint64_t *state, uint8_t *out, size_t maxlen,
                              const uint8_t *orig, size_t orig_len) {
    static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    const size_t alen = sizeof(alphabet) - 1;
    if (maxlen == 0) return 0;
    size_t len = 1 + (size_t)(rng_next(state) % 64ULL);
    if (len > maxlen) len = maxlen;
    if (len > 64) len = 64;
    for (size_t i = 0; i < len; i++) {
        out[i] = (uint8_t)alphabet[(size_t)(rng_next(state) % (uint64_t)alen)];
    }
    if (orig != NULL && orig_len == len && memcmp(out, orig, len) == 0) {
        size_t idx = 0;
        while (idx < alen && (uint8_t)alphabet[idx] != out[0]) idx++;
        out[0] = (uint8_t)alphabet[(idx + 1) % alen];
    }
    return len;
}

static size_t replace_value_content(uint8_t *Data, size_t Size, size_t MaxSize,
                                    const Line *value_line,
                                    const uint8_t *name, size_t name_len) {
    if (value_line->start > Size || value_line->content_end > Size) return (size_t)-1;
    size_t old_len = value_line->content_end - value_line->start;
    if (name_len > old_len) {
        if (Size + (name_len - old_len) > MaxSize) return (size_t)-1;
    }
    size_t new_size = Size - old_len + name_len;
    if (new_size > MaxSize) return (size_t)-1;
    if (name_len != old_len) {
        memmove(Data + value_line->start + name_len,
                Data + value_line->content_end,
                Size - value_line->content_end);
    }
    memcpy(Data + value_line->start, name, name_len);
    return new_size;
}

static size_t ensure_record_structure(uint8_t *Data, size_t Size, size_t MaxSize,
                                      uint64_t seed, uint64_t salt) {
    uint64_t state = seed ^ salt ^ 0x9E3779B97F4A7C15ULL;
    SectionInfo sec;
    find_object_section(Data, Size, &sec);
    if (sec.found) {
        size_t end = sec.endsec_start;
        if (end > Size) end = Size;
        size_t count = count_code0_records(Data, Size, sec.content_start, end);
        if (count == 0) return Size;
        size_t k = (size_t)(rng_next(&state) % (uint64_t)count);
        Line value_line;
        if (!get_kth_code0_value_line(Data, Size, sec.content_start, end, k, &value_line)) {
            return Size;
        }
        uint8_t name[64];
        size_t name_len = gen_random_name(&state, name, sizeof(name),
                                          Data + value_line.start,
                                          value_line.content_end - value_line.start);
        size_t new_size = replace_value_content(Data, Size, MaxSize, &value_line, name, name_len);
        if (new_size == (size_t)-1) return Size;
        return new_size;
    } else {
        uint8_t name[64];
        size_t name_len = gen_random_name(&state, name, sizeof(name), NULL, 0);
        size_t eof = find_eof_record_start(Data, Size);
        size_t pos;
        int needs_sep = 0;
        if (eof != (size_t)-1) {
            pos = eof;
        } else {
            pos = Size;
            if (Size > 0 && Data[Size - 1] != '\n' && Data[Size - 1] != '\r') needs_sep = 1;
        }
        uint8_t block[256];
        size_t blen = 0;
        if (needs_sep) {
            block[blen++] = '\r';
            block[blen++] = '\n';
        }
        const char *prefix = "0\r\nSECTION\r\n2\r\nOBJECTS\r\n0\r\n";
        size_t plen = strlen(prefix);
        const char *suffix = "\r\n0\r\nENDSEC\r\n";
        size_t slen = strlen(suffix);
        if (blen + plen + name_len + slen > sizeof(block)) return Size;
        memcpy(block + blen, prefix, plen);
        blen += plen;
        memcpy(block + blen, name, name_len);
        blen += name_len;
        memcpy(block + blen, suffix, slen);
        blen += slen;
        if (pos > Size) return Size;
        if (Size + blen > MaxSize) return Size;
        memmove(Data + pos + blen, Data + pos, Size - pos);
        memcpy(Data + pos, block, blen);
        return Size + blen;
    }
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    return ensure_record_structure(Data, Size, MaxSize, (uint64_t)Seed, 0xA001ULL);
}

static size_t mutate_a002(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    return ensure_record_structure(Data, Size, MaxSize, (uint64_t)Seed, 0xA002ULL);
}

static size_t mutate_a003(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    return ensure_record_structure(Data, Size, MaxSize, (uint64_t)Seed, 0xA003ULL);
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    if (Size > MaxSize) return Size;
    if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    if (Size >= 1 && Data[0] == '{') {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    unsigned int r = Seed % 10000U;
    if (r < 5000U) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    if (r < 6667U) {
        return mutate_a001(Data, Size, MaxSize, Seed);
    }
    if (r < 8334U) {
        return mutate_a002(Data, Size, MaxSize, Seed);
    }
    return mutate_a003(Data, Size, MaxSize, Seed);
}
