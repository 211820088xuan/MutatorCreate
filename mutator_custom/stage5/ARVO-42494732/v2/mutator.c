#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

static int next_line_bounds(const uint8_t *d, size_t n, size_t pos,
                            size_t *cs, size_t *ce, size_t *nx)
{
    if (pos >= n) return 0;
    size_t i = pos;
    while (i < n && d[i] != '\r' && d[i] != '\n') i++;
    *cs = pos;
    *ce = i;
    if (i < n) {
        if (d[i] == '\r') {
            if (i + 1 < n && d[i + 1] == '\n') *nx = i + 2;
            else *nx = i + 1;
        } else {
            *nx = i + 1;
        }
    } else {
        *nx = n;
    }
    return 1;
}

static void trim_span(const uint8_t *d, size_t *s, size_t *e)
{
    while (*s < *e && (d[*s] == ' ' || d[*s] == '\t')) (*s)++;
    while (*e > *s && (d[*e - 1] == ' ' || d[*e - 1] == '\t')) (*e)--;
}

static int line_equals_trimmed(const uint8_t *d, size_t s, size_t e, const char *lit)
{
    size_t ts = s, te = e;
    trim_span(d, &ts, &te);
    size_t n = strlen(lit);
    return te - ts == n && memcmp(d + ts, lit, n) == 0;
}

static int find_objects_zero_value(uint8_t *Data, size_t Size, size_t *vstart, size_t *vend)
{
    size_t pos = 0;
    size_t cs, ce, nx;
    int in_objects = 0;

    while (next_line_bounds(Data, Size, pos, &cs, &ce, &nx)) {
        if (!in_objects) {
            if (line_equals_trimmed(Data, cs, ce, "OBJECTS")) {
                in_objects = 1;
            }
            pos = nx;
            continue;
        }

        if (line_equals_trimmed(Data, cs, ce, "ENDSEC")) return 0;

        size_t ts = cs, te = ce;
        trim_span(Data, &ts, &te);
        if (te > ts && te - ts <= 3) {
            int all_digits = 1;
            for (size_t j = ts; j < te; j++) {
                if (Data[j] < '0' || Data[j] > '9') { all_digits = 0; break; }
            }
            if (all_digits && te - ts == 1 && Data[ts] == '0') {
                size_t p2 = nx;
                size_t cs2, ce2, nx2;
                if (!next_line_bounds(Data, Size, p2, &cs2, &ce2, &nx2)) return 0;
                if (line_equals_trimmed(Data, cs2, ce2, "ENDSEC")) return 0;
                *vstart = cs2;
                *vend = ce2;
                return 1;
            }
        }
        pos = nx;
    }
    return 0;
}

static size_t mutate_a001_value_line(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed)
{
    size_t vs, ve;
    if (!find_objects_zero_value(Data, Size, &vs, &ve)) return Size;
    if (ve < vs || ve > Size) return Size;

    static const char *candidates[3] = {
        "FUZZ_OBJECT",
        "AAAAAAAA",
        "\x7f\x7f\x7f"
    };
    const char *rep = candidates[Seed % 3u];
    size_t rlen = strlen(rep);
    size_t oldlen = ve - vs;

    if (rlen > oldlen) {
        size_t extra = rlen - oldlen;
        if (Size + extra > MaxSize) return Size;
    }

    if (rlen != oldlen) {
        memmove(Data + vs + rlen, Data + ve, Size - ve);
    }
    memcpy(Data + vs, rep, rlen);
    return Size - oldlen + rlen;
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed)
{
    unsigned r = Seed % 1000u;
    if (r < 500u) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    switch ((r - 500u) / 500u) {
        case 0:
            return mutate_a001_value_line(Data, Size, MaxSize, Seed);
        default:
            return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
}