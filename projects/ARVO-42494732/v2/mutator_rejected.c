#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

static int is_dxf_format(const uint8_t *d, size_t n) {
  if (n >= 2 && d[0] == 'A' && d[1] == 'C') return 0; /* DWG */
  if (n >= 1 && d[0] == '{') return 0; /* JSON */
  return 1; /* DXF */
}

typedef struct {
  size_t start;
  size_t end;
  size_t next;
} DxfLine;

typedef struct {
  DxfLine code_line;
  DxfLine value_line;
  size_t next;
  int code;
  int valid;
} DxfRecord;

static int is_digit_byte(uint8_t c) { return c >= '0' && c <= '9'; }
static int is_space_byte(uint8_t c) { return c == ' ' || c == '\t'; }

static int dxf_next_line(const uint8_t *d, size_t n, size_t pos, DxfLine *ln) {
  if (pos >= n) return 0;
  size_t p = pos;
  size_t s = p;
  while (p < n && d[p] != '\r' && d[p] != '\n') p++;
  ln->start = s;
  ln->end = p;
  if (p < n) {
    if (d[p] == '\r') {
      p++;
      if (p < n && d[p] == '\n') p++;
    } else if (d[p] == '\n') {
      p++;
    }
  }
  ln->next = p;
  return 1;
}

static int dxf_line_code(const uint8_t *d, const DxfLine *ln, int *code) {
  size_t i = ln->start;
  while (i < ln->end && is_space_byte(d[i])) i++;
  if (i >= ln->end || !is_digit_byte(d[i])) return 0;
  int v = 0;
  int nd = 0;
  while (i < ln->end && is_digit_byte(d[i]) && nd < 5) {
    v = v * 10 + (int)(d[i] - '0');
    i++;
    nd++;
  }
  if (nd == 0) return 0;
  while (i < ln->end && is_space_byte(d[i])) i++;
  if (i != ln->end) return 0;
  *code = v;
  return 1;
}

static int dxf_line_equals(const uint8_t *d, const DxfLine *ln, const char *s) {
  size_t i = ln->start;
  size_t e = ln->end;
  while (i < e && is_space_byte(d[i])) i++;
  while (e > i && is_space_byte(d[e - 1])) e--;
  size_t len = e - i;
  size_t slen = strlen(s);
  if (len != slen) return 0;
  return memcmp(d + i, s, len) == 0;
}

static int dxf_next_record(const uint8_t *d, size_t n, size_t pos, DxfRecord *r) {
  DxfLine cl, vl;
  if (!dxf_next_line(d, n, pos, &cl)) return 0;
  int code;
  if (!dxf_line_code(d, &cl, &code)) return 0;
  if (!dxf_next_line(d, n, cl.next, &vl)) return 0;
  r->code_line = cl;
  r->value_line = vl;
  r->next = vl.next;
  r->code = code;
  r->valid = 1;
  return 1;
}

static unsigned dxf_rand(unsigned *state) {
  unsigned x = *state;
  if (x == 0) x = 0x9e3779b9u;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  *state = x;
  return x;
}

static size_t dxf_gen_name(uint8_t out[64], unsigned *state,
                           const uint8_t *orig, size_t orig_len) {
  static const char alpha[] =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  const size_t alen = sizeof(alpha) - 1;
  size_t len = 1 + (size_t)(dxf_rand(state) % 64);
  size_t i;
  for (i = 0; i < len; i++) {
    out[i] = (uint8_t)alpha[dxf_rand(state) % alen];
  }
  size_t os = 0, oe = orig_len;
  while (os < oe && is_space_byte(orig[os])) os++;
  while (oe > os && is_space_byte(orig[oe - 1])) oe--;
  size_t olen = oe - os;
  if (len == olen && olen > 0 && memcmp(out, orig + os, len) == 0) {
    out[len - 1] = (out[len - 1] == (uint8_t)'A') ? (uint8_t)'B' : (uint8_t)'A';
  }
  return len;
}

static int dxf_find_section(const uint8_t *d, size_t n, const char *anchor,
                            size_t *body_start, size_t *body_end) {
  size_t pos = 0;
  DxfRecord rec, rec2, r3;
  while (dxf_next_record(d, n, pos, &rec)) {
    if (rec.code == 0 && dxf_line_equals(d, &rec.value_line, "SECTION")) {
      if (dxf_next_record(d, n, rec.next, &rec2)) {
        if (rec2.code == 2 && dxf_line_equals(d, &rec2.value_line, anchor)) {
          size_t bstart = rec2.next;
          size_t p = bstart;
          while (p < n && dxf_next_record(d, n, p, &r3)) {
            if (r3.code == 0 && dxf_line_equals(d, &r3.value_line, "ENDSEC")) {
              *body_start = bstart;
              *body_end = r3.code_line.start;
              return 1;
            }
            if (r3.next <= p) break;
            p = r3.next;
          }
          *body_start = bstart;
          *body_end = n;
          return 1;
        }
      }
    }
    if (rec.next <= pos) break;
    pos = rec.next;
  }
  return 0;
}

static int dxf_select_code0(const uint8_t *d, size_t n, size_t body_start,
                            size_t body_end, unsigned *state,
                            size_t *value_start, size_t *value_end) {
  size_t count = 0;
  size_t pos = body_start;
  DxfRecord r;
  while (pos < body_end && dxf_next_record(d, n, pos, &r)) {
    if (r.code_line.start >= body_end) break;
    if (r.code == 0) count++;
    if (r.next <= pos) break;
    pos = r.next;
  }
  if (count == 0) return 0;
  size_t k = (size_t)(dxf_rand(state) % count);
  size_t idx = 0;
  pos = body_start;
  while (pos < body_end && dxf_next_record(d, n, pos, &r)) {
    if (r.code_line.start >= body_end) break;
    if (r.code == 0) {
      if (idx == k) {
        *value_start = r.value_line.start;
        *value_end = r.value_line.end;
        return 1;
      }
      idx++;
    }
    if (r.next <= pos) break;
    pos = r.next;
  }
  return 0;
}

static int dxf_find_eof_insert(const uint8_t *d, size_t n, size_t *pos_out) {
  size_t pos = 0;
  DxfRecord r;
  while (dxf_next_record(d, n, pos, &r)) {
    if (r.code == 0 && dxf_line_equals(d, &r.value_line, "EOF")) {
      *pos_out = r.code_line.start;
      return 1;
    }
    if (r.next <= pos) break;
    pos = r.next;
  }
  *pos_out = n;
  return 0;
}

static size_t dxf_replace_value(uint8_t *d, size_t n, size_t max_size,
                                size_t value_start, size_t value_end,
                                const uint8_t *name, size_t name_len) {
  size_t old_len = value_end - value_start;
  if (name_len > old_len) {
    size_t new_size = n - old_len + name_len;
    if (new_size > max_size) return (size_t)-1;
    memmove(d + value_start + name_len, d + value_end, n - value_end);
  } else if (name_len < old_len) {
    memmove(d + value_start + name_len, d + value_end, n - value_end);
  }
  memcpy(d + value_start, name, name_len);
  return n - old_len + name_len;
}

static size_t dxf_insert_block(uint8_t *d, size_t n, size_t max_size,
                               size_t pos, const uint8_t *block,
                               size_t block_len) {
  if (pos > n) pos = n;
  if (block_len > max_size || n > max_size - block_len) return (size_t)-1;
  memmove(d + pos + block_len, d + pos, n - pos);
  memcpy(d + pos, block, block_len);
  return n + block_len;
}

static size_t dxf_append_bytes(uint8_t *dst, size_t cap, size_t off,
                               const char *s) {
  size_t len = strlen(s);
  size_t i;
  if (off <= cap && len <= cap - off) {
    for (i = 0; i < len; i++) dst[off + i] = (uint8_t)s[i];
  }
  return off + len;
}

static int dxf_ensure_record_structure(uint8_t *Data, size_t Size,
                                       size_t MaxSize, unsigned Seed,
                                       unsigned salt,
                                       const char *section_anchor,
                                       size_t *out_size) {
  unsigned state = Seed ^ salt;
  size_t body_start = 0, body_end = 0;
  if (dxf_find_section(Data, Size, section_anchor, &body_start, &body_end)) {
    size_t vs = 0, ve = 0;
    if (!dxf_select_code0(Data, Size, body_start, body_end, &state, &vs, &ve)) {
      return 0;
    }
    uint8_t name[64];
    size_t name_len = dxf_gen_name(name, &state, Data + vs, ve - vs);
    size_t ns = dxf_replace_value(Data, Size, MaxSize, vs, ve, name, name_len);
    if (ns == (size_t)-1) return 0;
    *out_size = ns;
    return 1;
  } else {
    size_t insert_pos = Size;
    (void)dxf_find_eof_insert(Data, Size, &insert_pos);
    uint8_t name[64];
    size_t name_len = dxf_gen_name(name, &state, (const uint8_t *)"", 0);
    uint8_t block[512];
    size_t off = 0;
    off = dxf_append_bytes(block, sizeof(block), off, "0\r\nSECTION\r\n2\r\n");
    off = dxf_append_bytes(block, sizeof(block), off, section_anchor);
    off = dxf_append_bytes(block, sizeof(block), off, "\r\n0\r\n");
    if (off + name_len > sizeof(block)) return 0;
    memcpy(block + off, name, name_len);
    off += name_len;
    off = dxf_append_bytes(block, sizeof(block), off, "\r\n0\r\nENDSEC\r\n");
    if (off > sizeof(block)) return 0;
    size_t ns = dxf_insert_block(Data, Size, MaxSize, insert_pos, block, off);
    if (ns == (size_t)-1) return 0;
    *out_size = ns;
    return 1;
  }
}

static int mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize,
                       unsigned Seed, size_t *OutSize) {
  return dxf_ensure_record_structure(Data, Size, MaxSize, Seed,
                                     0x001u, "OBJECTS", OutSize);
}

static int mutate_a002(uint8_t *Data, size_t Size, size_t MaxSize,
                       unsigned Seed, size_t *OutSize) {
  return dxf_ensure_record_structure(Data, Size, MaxSize, Seed,
                                     0x002u, "OBJECTS", OutSize);
}

static int mutate_a003(uint8_t *Data, size_t Size, size_t MaxSize,
                       unsigned Seed, size_t *OutSize) {
  return dxf_ensure_record_structure(Data, Size, MaxSize, Seed,
                                     0x003u, "OBJECTS", OutSize);
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size,
                               size_t MaxSize, unsigned int Seed) {
  if (!is_dxf_format(Data, Size)) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  unsigned r = (unsigned)(Seed % 10000u);
  size_t out = Size;
  int ok = 0;
  if (r < 5000u) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  } else if (r < 6667u) {
    ok = mutate_a001(Data, Size, MaxSize, Seed, &out);
  } else if (r < 8334u) {
    ok = mutate_a002(Data, Size, MaxSize, Seed, &out);
  } else {
    ok = mutate_a003(Data, Size, MaxSize, Seed, &out);
  }
  if (!ok) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  return out;
}
