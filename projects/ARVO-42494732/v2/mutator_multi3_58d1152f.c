#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <ctype.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct { size_t start, end, next; } Line;

static int next_line(const uint8_t *D, size_t S, size_t p, Line *o) {
  if (p >= S) return 0;
  size_t s = p;
  while (p < S && D[p] != '\n' && D[p] != '\r') p++;
  size_t e = p;
  if (p < S) {
    if (D[p] == '\r') { p++; if (p < S && D[p] == '\n') p++; }
    else if (D[p] == '\n') p++;
  }
  o->start = s; o->end = e; o->next = p;
  return 1;
}

static int parse_code(const uint8_t *D, size_t s, size_t e, int *c) {
  size_t i = s;
  while (i < e && (D[i] == ' ' || D[i] == '\t')) i++;
  if (i >= e) return 0;
  int neg = 0;
  if (D[i] == '-') { neg = 1; i++; }
  if (i >= e || !isdigit((unsigned char)D[i])) return 0;
  int v = 0;
  while (i < e && isdigit((unsigned char)D[i])) { v = v * 10 + (D[i] - '0'); i++; }
  while (i < e && (D[i] == ' ' || D[i] == '\t')) i++;
  if (i != e) return 0;
  *c = neg ? -v : v;
  return 1;
}

static int line_eq(const uint8_t *D, const Line *l, const char *s) {
  size_t i = l->start, j = l->end;
  while (i < j && (D[i] == ' ' || D[i] == '\t')) i++;
  while (j > i && (D[j-1] == ' ' || D[j-1] == '\t')) j--;
  size_t n = strlen(s);
  return (j - i == n) && (memcmp(D + i, s, n) == 0);
}

static int next_rec(const uint8_t *D, size_t S, size_t *p, Line *cl, Line *vl, int *c) {
  while (*p < S) {
    Line t;
    if (!next_line(D, S, *p, &t)) return 0;
    int cc;
    if (parse_code(D, t.start, t.end, &cc)) {
      Line vv;
      if (!next_line(D, S, t.next, &vv)) return 0;
      *cl = t; *vl = vv; *c = cc; *p = vv.next;
      return 1;
    }
    *p = t.next;
  }
  return 0;
}

static int find_sec(const uint8_t *D, size_t S, const char *anchor, size_t *ss, size_t *se, size_t *eof) {
  *ss = S; *se = S; *eof = S;
  size_t p = 0; Line cl, vl; int c; int found = 0;
  while (next_rec(D, S, &p, &cl, &vl, &c)) {
    if (c == 0 && line_eq(D, &vl, "EOF")) { if (*eof == S) *eof = cl.start; }
    if (!found) {
      if (c == 0 && line_eq(D, &vl, "SECTION")) {
        size_t save = p;
        Line c2, v2; int cc2;
        if (next_rec(D, S, &p, &c2, &v2, &cc2)) {
          if (cc2 == 2 && line_eq(D, &v2, anchor)) { found = 1; *ss = p; }
          else p = save;
        } else p = save;
      }
    } else {
      if (c == 0 && line_eq(D, &vl, "ENDSEC")) { *se = cl.start; break; }
    }
  }
  return found;
}

static size_t count_code0(const uint8_t *D, size_t S, size_t a, size_t b) {
  size_t p = a, n = 0; Line cl, vl; int c;
  while (p < b) {
    if (!next_rec(D, S, &p, &cl, &vl, &c)) break;
    if (cl.start >= b) break;
    if (c == 0) n++;
  }
  return n;
}

static int get_kth0(const uint8_t *D, size_t S, size_t a, size_t b, size_t k, Line *oc, Line *ov) {
  size_t p = a, n = 0; Line cl, vl; int c;
  while (p < b) {
    if (!next_rec(D, S, &p, &cl, &vl, &c)) break;
    if (cl.start >= b) break;
    if (c == 0) {
      if (n == k) { *oc = cl; *ov = vl; return 1; }
      n++;
    }
  }
  return 0;
}

static uint32_t rnd(uint32_t *s) {
  uint32_t x = *s;
  x ^= x << 13; x ^= x >> 17; x ^= x << 5;
  *s = x;
  return x;
}

static size_t gen_name(uint8_t *out, size_t cap, uint32_t *s) {
  static const char a[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  size_t an = sizeof(a) - 1;
  size_t n = 1 + (rnd(s) % 64);
  if (n > cap) n = cap;
  for (size_t i = 0; i < n; i++) out[i] = (uint8_t)a[rnd(s) % an];
  return n;
}

static size_t repl_val(uint8_t *D, size_t S, size_t M, size_t vs, size_t ve, const uint8_t *nv, size_t nl) {
  size_t ol = ve - vs;
  if (S - ol + nl > M) return S;
  memmove(D + vs + nl, D + ve, S - ve);
  memcpy(D + vs, nv, nl);
  return S - ol + nl;
}

static size_t ins_rec(uint8_t *D, size_t S, size_t M, size_t pos, const uint8_t *name, size_t nl) {
  uint8_t b[80]; size_t p = 0;
  b[p++] = '0'; b[p++] = '\r'; b[p++] = '\n';
  if (nl > sizeof(b) - 8) return S;
  memcpy(b + p, name, nl); p += nl;
  b[p++] = '\r'; b[p++] = '\n';
  size_t pre = 0;
  if (pos == S && S > 0 && D[S-1] != '\n' && D[S-1] != '\r') pre = 2;
  if (S + p + pre > M) return S;
  memmove(D + pos + p + pre, D + pos, S - pos);
  size_t q = pos;
  if (pre) { D[q++] = '\r'; D[q++] = '\n'; }
  memcpy(D + q, b, p);
  return S + p + pre;
}

static size_t cons_sec(uint8_t *D, size_t S, size_t M, size_t eof, const char *anchor, unsigned int Seed, unsigned int salt) {
  uint8_t name[64]; uint32_t st = Seed ^ salt; if (!st) st = 0x9e3779b9u;
  size_t nl = gen_name(name, sizeof(name), &st);
  uint8_t b[256]; size_t p = 0;
  const char *s1 = "0\r\nSECTION\r\n2\r\n"; size_t l1 = strlen(s1);
  if (p + l1 > sizeof(b)) return S; memcpy(b + p, s1, l1); p += l1;
  size_t al = strlen(anchor);
  if (p + al + 2 > sizeof(b)) return S; memcpy(b + p, anchor, al); p += al;
  b[p++] = '\r'; b[p++] = '\n';
  const char *s2 = "0\r\n"; size_t l2 = strlen(s2);
  if (p + l2 > sizeof(b)) return S; memcpy(b + p, s2, l2); p += l2;
  if (p + nl + 2 > sizeof(b)) return S; memcpy(b + p, name, nl); p += nl;
  b[p++] = '\r'; b[p++] = '\n';
  const char *s3 = "0\r\nENDSEC\r\n"; size_t l3 = strlen(s3);
  if (p + l3 > sizeof(b)) return S; memcpy(b + p, s3, l3); p += l3;
  size_t pos, pre = 0;
  if (eof < S) pos = eof;
  else { pos = S; if (S > 0 && D[S-1] != '\n' && D[S-1] != '\r') pre = 2; }
  if (S + p + pre > M) return S;
  memmove(D + pos + p + pre, D + pos, S - pos);
  size_t q = pos;
  if (pre) { D[q++] = '\r'; D[q++] = '\n'; }
  memcpy(D + q, b, p);
  return S + p + pre;
}

static size_t mut_sec(uint8_t *D, size_t S, size_t M, unsigned int Seed, const char *anchor, unsigned int salt) {
  size_t ss, se, eof;
  int found = find_sec(D, S, anchor, &ss, &se, &eof);
  uint32_t st = Seed ^ salt; if (!st) st = 0x9e3779b9u;
  if (!found) return cons_sec(D, S, M, eof, anchor, Seed, salt);
  size_t n = count_code0(D, S, ss, se);
  if (n == 0) {
    uint8_t name[64]; size_t nl = gen_name(name, sizeof(name), &st);
    return ins_rec(D, S, M, se, name, nl);
  }
  size_t k = rnd(&st) % n;
  Line cl, vl;
  if (!get_kth0(D, S, ss, se, k, &cl, &vl)) return S;
  uint8_t name[64]; size_t nl = gen_name(name, sizeof(name), &st);
  size_t ol = vl.end - vl.start;
  if (nl == ol && ol > 0 && memcmp(name, D + vl.start, nl) == 0) {
    static const char a[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
    size_t an = sizeof(a) - 1;
    for (size_t i = 0; i < an; i++) if (a[i] != (char)D[vl.start]) { name[0] = (uint8_t)a[i]; break; }
  }
  return repl_val(D, S, M, vl.start, vl.end, name, nl);
}

static size_t mut_a001(uint8_t *D, size_t S, size_t M, unsigned int Seed) { return mut_sec(D, S, M, Seed, "OBJECTS", 0xA001u); }
static size_t mut_a002(uint8_t *D, size_t S, size_t M, unsigned int Seed) { return mut_sec(D, S, M, Seed, "OBJECTS", 0xA002u); }
static size_t mut_a003(uint8_t *D, size_t S, size_t M, unsigned int Seed) { return mut_sec(D, S, M, Seed, "OBJECTS", 0xA003u); }

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') return LLVMFuzzerMutate(Data, Size, MaxSize);
  if (Size >= 1 && Data[0] == '{') return LLVMFuzzerMutate(Data, Size, MaxSize);
  unsigned r = Seed % 1000;
  if (r < 500) return LLVMFuzzerMutate(Data, Size, MaxSize);
  if (r < 667) return mut_a001(Data, Size, MaxSize, Seed);
  if (r < 834) return mut_a002(Data, Size, MaxSize, Seed);
  return mut_a003(Data, Size, MaxSize, Seed);
}
