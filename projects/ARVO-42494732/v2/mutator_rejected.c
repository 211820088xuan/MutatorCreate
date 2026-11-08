/* LLVMFuzzerCustomMutator for plan-003 / action a001
 * target: src/in_dxf.c dwg_read_dxf heap-use-after-free
 *   free: L12839 dxf_free_pair(pair)
 *   use : L12842 / L12707 pair->value.s
 * feature: uaf-llm01 (同函数直接释放后继续访问原堆对象)
 *
 * a001: target_part = value_line, operation = ensure_record_structure
 *   path 1 (段存在): 在 locator.section_anchor="OBJECTS" 段内按 random_k
 *                    选一条 code-0 记录，只替换它的值行；组码数字本身不动。
 *   path 2 (段不存在): 在 0/EOF 记录之前插入
 *                    0/SECTION, 2/OBJECTS, 0/<random_unrecognized_name>, 0/ENDSEC
 * 行切分兼容 \n, \r\n, \r。
 * 新名字由 Seed 派生的 PRNG 生成（长度 1..64，64 字符 alphabet），
 * 无任何固定候选值列表。
 */
#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

#define SECTION_ANCHOR "OBJECTS"
#define ALPHABET "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
#define ALPHABET_LEN 64
#define NAME_MAX_LEN 64
#define MAX_CANDS 1024

static uint64_t g_counter = 0;

/* ---------- 确定性 PRNG：seed 来自 (Seed, 输入内容 hash, 计数器) ---------- */
static uint64_t xorshift64(uint64_t *s) {
    uint64_t x = *s;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    *s = x;
    return x;
}

static uint64_t quick_hash(const uint8_t *d, size_t n) {
    uint64_t h = 1469598103934665603ULL ^ (uint64_t)n;
    size_t i;
    size_t pre = (n < 256u) ? n : 256u;
    for (i = 0; i < pre; i++) { h ^= (uint64_t)d[i]; h *= 1099511628211ULL; }
    if (n > 256u) {
        for (i = n - 256u; i < n; i++) { h ^= (uint64_t)d[i]; h *= 1099511628211ULL; }
    }
    return h;
}

/* ---------- 行工具：兼容 \r\n / \n / \r ---------- */
static size_t line_len(const uint8_t *p, size_t n, size_t *eol) {
    size_t i = 0;
    while (i < n && p[i] != '\n' && p[i] != '\r') i++;
    if (i >= n) { *eol = 0; return i; }
    if (p[i] == '\r') *eol = (i + 1 < n && p[i + 1] == '\n') ? 2u : 1u;
    else *eol = 1u;
    return i;
}

/* 组码行：可选前导空白 + 1..3 位数字 + 可选尾随空白 */
static int parse_group_code(const uint8_t *p, size_t len, int *out) {
    size_t s = 0, e = len, i;
    int ndig = 0;
    unsigned v = 0;
    while (s < e && (p[s] == ' ' || p[s] == '\t')) s++;
    i = s;
    while (i < e && p[i] >= '0' && p[i] <= '9') {
        if (ndig < 3) v = v * 10u + (unsigned)(p[i] - '0');
        ndig++; i++;
    }
    if (ndig < 1 || ndig > 3) return 0;
    while (i < e && (p[i] == ' ' || p[i] == '\t')) i++;
    if (i != e) return 0;
    *out = (int)v;
    return 1;
}

static int trimmed_eq(const uint8_t *p, size_t len, const char *lit) {
    size_t s = 0, e = len;
    size_t l = strlen(lit);
    while (s < e && (p[s] == ' ' || p[s] == '\t')) s++;
    while (e > s && (p[e - 1] == ' ' || p[e - 1] == '\t')) e--;
    if (e - s != l) return 0;
    return memcmp(p + s, lit, l) == 0;
}

/* ---------- 随机未识别名（绝不使用固定候选表） ---------- */
static int name_is_reserved(const char *s, size_t len) {
    static const char *r[4] = { "SECTION", "ENDSEC", "EOF", "OBJECTS" };
    size_t i;
    for (i = 0; i < 4; i++) {
        size_t l = strlen(r[i]);
        if (l == len && memcmp(s, r[i], l) == 0) return 1;
    }
    return 0;
}

static size_t gen_nonreserved_name(uint64_t *st, char *out) {
    size_t len = 0, tries;
    for (tries = 0; tries < 8; tries++) {
        size_t i;
        len = 1 + (size_t)(xorshift64(st) % (uint64_t)NAME_MAX_LEN);
        for (i = 0; i < len; i++)
            out[i] = ALPHABET[(size_t)(xorshift64(st) % (uint64_t)ALPHABET_LEN)];
        out[len] = '\0';
        if (!name_is_reserved(out, len)) return len;
    }
    out[0] = 'Z'; out[1] = '\0';
    return 1;
}

/* ---------- 格式分流：DXF 至少要有 0/SECTION 与 0/ENDSEC 记录对 ---------- */
static int looks_like_dxf(const uint8_t *d, size_t n) {
    size_t pos = 0;
    int expect_code = 1, code = -1;
    int saw_section = 0, saw_end = 0;
    if (n < 8) return 0;
    while (pos < n) {
        size_t eol = 0;
        size_t ll = line_len(d + pos, n - pos, &eol);
        size_t total = ll + eol;
        if (ll == 0 && eol == 0) break;
        if (expect_code) {
            int c;
            if (parse_group_code(d + pos, ll, &c)) { code = c; expect_code = 0; }
        } else {
            if (code == 0) {
                if (trimmed_eq(d + pos, ll, "SECTION")) saw_section = 1;
                else if (trimmed_eq(d + pos, ll, "ENDSEC")) saw_end = 1;
            }
            expect_code = 1;
        }
        if (saw_section && saw_end) return 1;
        pos += total;
    }
    return 0;
}

/* ---------- 定位 0/SECTION -> 2/OBJECTS，返回 OBJECTS 值行之后的位置 ---------- */
static int find_objects_section(const uint8_t *d, size_t n, size_t *body_start) {
    size_t pos = 0;
    int expect_code = 1, code = -1;
    int have_prev = 0, pcode = -1;
    size_t pval_off = 0, pval_len = 0;
    while (pos < n) {
        size_t eol = 0;
        size_t ll = line_len(d + pos, n - pos, &eol);
        size_t total = ll + eol;
        if (ll == 0 && eol == 0) break;
        if (expect_code) {
            int c;
            if (parse_group_code(d + pos, ll, &c)) { code = c; expect_code = 0; }
            else have_prev = 0;
        } else {
            if (have_prev && pcode == 0 && code == 2 &&
                trimmed_eq(d + pval_off, pval_len, "SECTION") &&
                trimmed_eq(d + pos, ll, SECTION_ANCHOR)) {
                size_t end = pos + ll + eol;
                if (end <= n) { *body_start = end; return 1; }
                return 0;
            }
            pcode = code; pval_off = pos; pval_len = ll; have_prev = 1;
            expect_code = 1;
        }
        pos += total;
    }
    return 0;
}

/* ---------- 收集段内 code-0 记录的值行（random_k 的候选集合） ---------- */
typedef struct { size_t off, len, eol; } cand_t;

static int collect_code0_records(const uint8_t *d, size_t n, size_t start,
                                 cand_t *out, int maxc) {
    size_t pos = start;
    int expect_code = 1, code = -1, count = 0;
    while (pos < n) {
        size_t eol = 0;
        size_t ll = line_len(d + pos, n - pos, &eol);
        size_t total = ll + eol;
        if (ll == 0 && eol == 0) break;
        if (expect_code) {
            int c;
            if (parse_group_code(d + pos, ll, &c)) { code = c; expect_code = 0; }
        } else {
            if (code == 0) {
                if (trimmed_eq(d + pos, ll, "ENDSEC") || trimmed_eq(d + pos, ll, "EOF"))
                    break;
                if (count < maxc) {
                    out[count].off = pos;
                    out[count].len = ll;
                    out[count].eol = eol;
                    count++;
                }
            }
            expect_code = 1;
        }
        pos += total;
    }
    return count;
}

/* ---------- path 1: 只替换值行，组码数字保持原样 ---------- */
static size_t replace_value_line(uint8_t *Data, size_t Size, size_t MaxSize,
                                 uint64_t *st, size_t voff, size_t vlen, size_t veol) {
    char name[NAME_MAX_LEN + 1];
    uint8_t eol_buf[2];
    size_t nlen, budget, suffix_off, suffix_len, newsize;

    if (voff > Size || vlen > Size - voff) return Size;
    if (veol > 2u) return Size;
    if (Size > MaxSize) return Size;
    if (Size < vlen) return Size;
    if (MaxSize < Size - vlen) return Size;
    budget = MaxSize - (Size - vlen);
    if (budget > NAME_MAX_LEN) budget = NAME_MAX_LEN;
    if (budget < 1) return Size;

    nlen = gen_nonreserved_name(st, name);
    if (nlen > budget) { nlen = budget; name[nlen] = '\0'; }

    /* must differ from original */
    if (nlen == vlen && (vlen == 0 || memcmp(Data + voff, name, nlen) == 0)) {
        name[0] = (name[0] == 'A') ? 'B' : 'A';
    }

    suffix_off = voff + vlen + veol;
    if (suffix_off > Size) return Size;
    suffix_len = Size - suffix_off;
    newsize = voff + nlen + veol + suffix_len;
    if (newsize > MaxSize) return Size;

    if (veol) memcpy(eol_buf, Data + voff + vlen, veol);
    memmove(Data + voff + nlen + veol, Data + suffix_off, suffix_len);
    memcpy(Data + voff, name, nlen);
    if (veol) memcpy(Data + voff + nlen, eol_buf, veol);
    return newsize;
}

/* ---------- path 2: 段不存在 -> 在 0/EOF 之前插入完整结构 ---------- */
static size_t construct_objects_section(uint8_t *Data, size_t Size,
                                        size_t MaxSize, uint64_t *st) {
    static const char HEAD[] = "0\r\nSECTION\r\n2\r\nOBJECTS\r\n0\r\n";
    static const char TAIL[] = "\r\n0\r\nENDSEC\r\n";
    char name[NAME_MAX_LEN + 1];
    char frag[192];
    size_t head_len = sizeof(HEAD) - 1;
    size_t tail_len = sizeof(TAIL) - 1;
    size_t nlen, flen;
    size_t insert_off = Size;
    int found_eof = 0;
    int need_eol = 0;

    {
        size_t pos = 0;
        int expect_code = 1, code = -1;
        size_t code_start = 0;
        while (pos < Size) {
            size_t eol = 0;
            size_t ll = line_len(Data + pos, Size - pos, &eol);
            size_t total = ll + eol;
            if (ll == 0 && eol == 0) break;
            if (expect_code) {
                int c;
                if (parse_group_code(Data + pos, ll, &c)) {
                    code = c; code_start = pos; expect_code = 0;
                }
            } else {
                if (code == 0 && trimmed_eq(Data + pos, ll, "EOF")) {
                    insert_off = code_start; found_eof = 1; break;
                }
                expect_code = 1;
            }
            pos += total;
        }
    }

    if (!found_eof) {
        insert_off = Size;
        need_eol = (Size > 0) && (Data[Size - 1] != '\n') && (Data[Size - 1] != '\r');
    }

    nlen = gen_nonreserved_name(st, name);
    flen = head_len + nlen + tail_len;
    if (flen > sizeof(frag)) return Size;
    memcpy(frag, HEAD, head_len);
    memcpy(frag + head_len, name, nlen);
    memcpy(frag + head_len + nlen, TAIL, tail_len);

    {
        size_t extra = need_eol ? 2u : 0u;
        if (Size + extra + flen > MaxSize) {
            size_t avail = (MaxSize > Size + extra) ? (MaxSize - Size - extra) : 0u;
            size_t fixed = head_len + tail_len;
            if (avail <= fixed + 1u) return Size;
            nlen = avail - fixed;
            if (nlen > NAME_MAX_LEN) nlen = NAME_MAX_LEN;
            if (nlen < 1u) return Size;
            flen = fixed + nlen;
            memcpy(frag + head_len, name, nlen);
            memcpy(frag + head_len + nlen, TAIL, tail_len);
        }
        if (Size + extra + flen > MaxSize) return Size;

        if (need_eol) {
            Data[Size] = '\r';
            Data[Size + 1] = '\n';
            Size += 2;
            insert_off = Size;
        }
        memmove(Data + insert_off + flen, Data + insert_off, Size - insert_off);
        memcpy(Data + insert_off, frag, flen);
        return Size + flen;
    }
}

/* ---------- a001 特征策略 ---------- */
static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, uint64_t *st) {
    size_t body_start = 0;
    cand_t cands[MAX_CANDS];
    int nc;

    if (!looks_like_dxf(Data, Size))
        return LLVMFuzzerMutate(Data, Size, MaxSize);

    if (find_objects_section(Data, Size, &body_start)) {
        nc = collect_code0_records(Data, Size, body_start, cands, MAX_CANDS);
        if (nc > 0) {
            size_t k = (size_t)(xorshift64(st) % (uint64_t)nc);
            return replace_value_line(Data, Size, MaxSize, st,
                                      cands[k].off, cands[k].len, cands[k].eol);
        }
        /* 段存在但无可用 code-0 记录（极端截断）：回退 default，避免空转 */
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }

    return construct_objects_section(Data, Size, MaxSize, st);
}

/* ---------- 按权重分发的入口 ---------- */
size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize,
                               unsigned int Seed) {
    uint64_t st;
    unsigned r;

    if (Size > MaxSize) return Size;

    st = ((uint64_t)Seed) * 0x9E3779B97F4A7C15ULL
       ^ quick_hash(Data, Size)
       ^ ((++g_counter) * 0xD1B54A32D192ED03ULL);
    if (st == 0) st = 0xA5A5A5A5A5A5A5A5ULL;

    /* weighting: default=0.5 -> [0,500)；features_total=0.5 -> [500,1000)
     * 仅一个特征 a001，占 500/1000。 */
    r = (unsigned)(xorshift64(&st) % 1000u);

    if (r < 500u) {
        return LLVMFuzzerMutate(Data, Size, MaxSize);
    }
    return mutate_a001(Data, Size, MaxSize, &st);
}
