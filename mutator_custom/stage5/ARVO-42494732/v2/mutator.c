#include <stddef.h>
#include <stdint.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

#define CR 13
#define LF 10
#define TAB 9
#define ALPHABET_LEN 64

static const uint8_t ALPHABET[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";

typedef struct {
    const uint8_t *ptr;
    size_t len;
    size_t content_off;
    size_t eol_off;
    size_t eol_len;
    size_t next_off;
} DxfLine;

static int read_line(const uint8_t *data, size_t size, size_t *pos, DxfLine *ln) {
    size_t start, i, eol_len;
    if (*pos >= size) return 0;
    start = *pos;
    i = start;
    while (i < size && data[i] != LF && data[i] != CR) i++;
    ln->ptr = data + start;
    ln->len = i - start;
    ln->content_off = start;
    ln->eol_off = i;
    eol_len = 0;
    if (i < size) {
        if (data[i] == CR) {
            if (i + 1 < size && data[i + 1] == LF) eol_len = 2;
            else eol_len = 1;
        } else if (data[i] == LF) {
            eol_len = 1;
        }
    }
    ln->eol_len = eol_len;
    ln->next_off = i + eol_len;
    *pos = ln->next_off;
    return 1;
}

static size_t trim_left(const uint8_t *p, size_t len) {
    size_t i = 0;
    while (i < len && (p[i] == ' ' || p[i] == TAB)) i++;
    return i;
}

static size_t trim_right_len(const uint8_t *p, size_t len) {
    while (len > 0 && (p[len - 1] == ' ' || p[len - 1] == TAB)) len--;
    return len;
}

static int line_eq(const DxfLine *ln, const char *s) {
    size_t start = trim_left(ln->ptr, ln->len);
    size_t n = trim_right_len(ln->ptr + start, ln->len - start);
    size_t slen = strlen(s);
    if (n != slen) return 0;
    return memcmp(ln->ptr + start, s, slen) == 0;
}

static int parse_code_line(const DxfLine *ln, int *code) {
    size_t start = trim_left(ln->ptr, ln->len);
    size_t len = ln->len - start;
    size_t end = trim_right_len(ln->ptr + start, len);
    size_t i = 0;
    int val = 0;
    if (end == 0) return 0;
    while (i < end && ln->ptr[start + i] >= '0' && ln->ptr[start + i] <= '9') {
        if (i >= 3) return 0;
        val = val * 10 + (ln->ptr[start + i] - '0');
        i++;
    }
    if (i == 0 || i != end) return 0;
    *code = val;
    return 1;
}

typedef struct {
    int found;
    size_t section_start;
    size_t section_end;
} SectionInfo;

static int find_objects_section(const uint8_t *data, size_t size, SectionInfo *out) {
    size_t pos = 0;
    DxfLine code_ln, val_ln;
    int code;
    out->found = 0;
    out->section_start = 0;
    out->section_end = size;
    while (pos < size) {
        if (!read_line(data, size, &pos, &code_ln)) break;
        if (code_ln.len == 0) continue;
        if (!parse_code_line(&code_ln, &code)) continue;
        if (pos >= size) break;
        if (!read_line(data, size, &pos, &val_ln)) break;
        if (code == 2 && line_eq(&val_ln, "OBJECTS")) {
            out->found = 1;
            out->section_start = pos;
            break;
        }
    }
    if (!out->found) return 0;
    pos = out->section_start;
    while (pos < size) {
        if (!read_line(data, size, &pos, &code_ln)) break;
        if (code_ln.len == 0) continue;
        if (!parse_code_line(&code_ln, &code)) continue;
        if (pos >= size) {
            out->section_end = size;
            break;
        }
        if (!read_line(data, size, &pos, &val_ln)) {
            out->section_end = size;
            break;
        }
        if (code == 0 && line_eq(&val_ln, "ENDSEC")) {
            out->section_end = code_ln.content_off;
            break;
        }
        if (code == 0 && line_eq(&val_ln, "EOF")) {
            out->section_end = code_ln.content_off;
            break;
        }
    }
    return 1;
}

static uint32_t rng_next(uint32_t *s) {
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x;
    return x;
}

static size_t gen_random_name(uint32_t *state, uint8_t *out, const uint8_t *orig, size_t orig_len) {
    size_t len = 1 + (rng_next(state) % 64u);
    size_t i;
    for (i = 0; i < len; i++) {
        out[i] = ALPHABET[rng_next(state) % ALPHABET_LEN];
    }
    if (orig != NULL && orig_len == len && memcmp(out, orig, len) == 0) {
        size_t idx = 0;
        while (idx < ALPHABET_LEN && ALPHABET[idx] == out[0]) idx++;
        if (idx >= ALPHABET_LEN) idx = 0;
        out[0] = ALPHABET[idx];
        if (memcmp(out, orig, len) == 0) {
            out[0] = (out[0] == 'A') ? 'B' : 'A';
        }
    }
    return len;
}

static size_t replace_random_code0_value(uint8_t *Data, size_t Size, size_t MaxSize, const SectionInfo *sec, uint32_t *state) {
    size_t pos, count = 0, idx = 0, chosen;
    DxfLine code_ln, val_ln;
    int code;
    pos = sec->section_start;
    while (pos < sec->section_end) {
        if (!read_line(Data, Size, &pos, &code_ln)) break;
        if (code_ln.len == 0) continue;
        if (!parse_code_line(&code_ln, &code)) continue;
        if (pos >= sec->section_end) break;
        if (!read_line(Data, Size, &pos, &val_ln)) break;
        if (code == 0) {
            if (line_eq(&val_ln, "ENDSEC") || line_eq(&val_ln, "EOF")) break;
            count++;
        }
    }
    if (count == 0) return Size;
    chosen = rng_next(state) % count;
    pos = sec->section_start;
    while (pos < sec->section_end) {
        if (!read_line(Data, Size, &pos, &code_ln)) break;
        if (code_ln.len == 0) continue;
        if (!parse_code_line(&code_ln, &code)) continue;
        if (pos >= sec->section_end) break;
        if (!read_line(Data, Size, &pos, &val_ln)) break;
        if (code == 0) {
            if (line_eq(&val_ln, "ENDSEC") || line_eq(&val_ln, "EOF")) break;
            if (idx == chosen) {
                uint8_t newname[64];
                size_t old_len = val_ln.len;
                size_t new_len = gen_random_name(state, newname, val_ln.ptr, old_len);
                size_t val_off = val_ln.content_off;
                if (new_len > old_len) {
                    size_t delta = new_len - old_len;
                    if (Size + delta > MaxSize) return Size;
                    memmove(Data + val_off + new_len, Data + val_off + old_len, Size - (val_off + old_len));
                    memcpy(Data + val_off, newname, new_len);
                    return Size + delta;
                } else {
                    size_t delta = old_len - new_len;
                    memmove(Data + val_off + new_len, Data + val_off + old_len, Size - (val_off + old_len));
                    memcpy(Data + val_off, newname, new_len);
                    return Size - delta;
                }
            }
            idx++;
        }
    }
    return Size;
}

static size_t find_eof_insert_off(const uint8_t *data, size_t size, int *found) {
    size_t pos = 0;
    DxfLine code_ln, val_ln;
    int code;
    *found = 0;
    while (pos < size) {
        if (!read_line(data, size, &pos, &code_ln)) break;
        if (code_ln.len == 0) continue;
        if (!parse_code_line(&code_ln, &code)) continue;
        if (pos >= size) break;
        if (!read_line(data, size, &pos, &val_ln)) break;
        if (code == 0 && line_eq(&val_ln, "EOF")) {
            *found = 1;
            return code_ln.content_off;
        }
    }
    return size;
}

static size_t insert_section_before_eof(uint8_t *Data, size_t Size, size_t MaxSize, uint32_t *state) {
    static const uint8_t p1[] = { '0', CR, LF, 'S', 'E', 'C', 'T', 'I', 'O', 'N', CR, LF };
    static const uint8_t p2[] = { '2', CR, LF, 'O', 'B', 'J', 'E', 'C', 'T', 'S', CR, LF };
    static const uint8_t p3[] = { '0', CR, LF };
    static const uint8_t p4[] = { CR, LF, '0', CR, LF, 'E', 'N', 'D', 'S', 'E', 'C', CR, LF };
    uint8_t block[256];
    uint8_t name[64];
    size_t name_len, blen = 0, ins, need, prefix_extra = 0;
    int eof_found;
    name_len = gen_random_name(state, name, NULL, 0);
    memcpy(block + blen, p1, sizeof(p1)); blen += sizeof(p1);
    memcpy(block + blen, p2, sizeof(p2)); blen += sizeof(p2);
    memcpy(block + blen, p3, sizeof(p3)); blen += sizeof(p3);
    memcpy(block + blen, name, name_len); blen += name_len;
    memcpy(block + blen, p4, sizeof(p4)); blen += sizeof(p4);
    ins = find_eof_insert_off(Data, Size, &eof_found);
    if (!eof_found && Size > 0) {
        uint8_t last = Data[Size - 1];
        if (last != LF && last != CR) prefix_extra = 2;
    }
    need = prefix_extra + blen;
    if (Size + need > MaxSize) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    memmove(Data + ins + need, Data + ins, Size - ins);
    {
        size_t out = ins;
        if (prefix_extra) {
            Data[out++] = CR;
            Data[out++] = LF;
        }
        memcpy(Data + out, block, blen);
    }
    return Size + need;
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, uint32_t Seed) {
    uint32_t state = Seed ^ 0x9e3779b9u;
    SectionInfo sec;
    if (state == 0) state = 0x12345678u;
    if (!find_objects_section(Data, Size, &sec)) {
        return insert_section_before_eof(Data, Size, MaxSize, &state);
    }
    return replace_random_code0_value(Data, Size, MaxSize, &sec, &state);
}

static int is_dxf_format(const uint8_t *Data, size_t Size) {
    if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') return 0;
    if (Size >= 1 && Data[0] == '{') return 0;
    return 1;
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
    unsigned r;
    if (!is_dxf_format(Data, Size)) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    r = Seed % 1000u;
    if (r < 500u) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    return mutate_a001(Data, Size, MaxSize, (uint32_t)Seed);
}
