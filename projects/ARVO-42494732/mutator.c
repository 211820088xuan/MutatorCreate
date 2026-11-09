#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

static int is_space_byte(uint8_t c) {
  return c == ' ' || c == '\t' || c == '\v' || c == '\f';
}

static int next_line(const uint8_t *d, size_t size, size_t pos,
                     size_t *content_start, size_t *content_end,
                     size_t *next_pos) {
  size_t i;
  if (pos >= size) return 0;
  *content_start = pos;
  i = pos;
  while (i < size && d[i] != '\r' && d[i] != '\n') i++;
  *content_end = i;
  if (i < size) {
    if (d[i] == '\r') {
      if (i + 1 < size && d[i + 1] == '\n') *next_pos = i + 2;
      else *next_pos = i + 1;
    } else {
      *next_pos = i + 1;
    }
  } else {
    *next_pos = size;
  }
  return 1;
}

static void trim_range(const uint8_t *d, size_t *s, size_t *e) {
  while (*s < *e && is_space_byte(d[*s])) (*s)++;
  while (*e > *s && is_space_byte(d[*e - 1])) (*e)--;
}

static int parse_group_code(const uint8_t *d, size_t s, size_t e, int *out) {
  size_t i = s;
  int val = 0;
  int n = 0;
  while (i < e && (d[i] == ' ' || d[i] == '\t')) i++;
  while (i < e && d[i] >= '0' && d[i] <= '9') {
    if (n >= 6) return 0;
    val = val * 10 + (int)(d[i] - '0');
    n++;
    i++;
  }
  if (n == 0) return 0;
  while (i < e && (d[i] == ' ' || d[i] == '\t')) i++;
  if (i != e) return 0;
  *out = val;
  return 1;
}

static int get_record_at(const uint8_t *d, size_t size, size_t pos,
                         int *code, size_t *code_start, size_t *code_end,
                         size_t *code_next,
                         size_t *val_start, size_t *val_end,
                         size_t *val_next) {
  size_t cs, ce, cn, vs, ve, vn;
  int c;
  if (!next_line(d, size, pos, &cs, &ce, &cn)) return 0;
  if (!parse_group_code(d, cs, ce, &c)) return 0;
  if (!next_line(d, size, cn, &vs, &ve, &vn)) return 0;
  *code = c;
  if (code_start) *code_start = cs;
  if (code_end) *code_end = ce;
  if (code_next) *code_next = cn;
  if (val_start) *val_start = vs;
  if (val_end) *val_end = ve;
  if (val_next) *val_next = vn;
  return 1;
}

static int line_equals_trim(const uint8_t *d, size_t s, size_t e, const char *lit) {
  size_t a = s, b = e;
  size_t n = strlen(lit);
  trim_range(d, &a, &b);
  return (b - a == n) && (memcmp(d + a, lit, n) == 0);
}

static int find_section_anchor(const uint8_t *d, size_t size, const char *anchor,
                               size_t *after_anchor) {
  size_t pos = 0;
  while (pos < size) {
    int c;
    size_t cs, ce, cn, vs, ve, vn;
    if (!get_record_at(d, size, pos, &c, &cs, &ce, &cn, &vs, &ve, &vn)) {
      size_t s, e, n;
      if (!next_line(d, size, pos, &s, &e, &n)) break;
      pos = n;
      continue;
    }
    if (c == 2 && line_equals_trim(d, vs, ve, anchor)) {
      *after_anchor = vn;
      return 1;
    }
    pos = vn;
  }
  return 0;
}

static int count_code_zero_records(const uint8_t *d, size_t size, size_t start,
                                   size_t *count) {
  size_t pos = start;
  *count = 0;
  while (pos < size) {
    int c;
    size_t cs, ce, cn, vs, ve, vn;
    if (!get_record_at(d, size, pos, &c, &cs, &ce, &cn, &vs, &ve, &vn)) {
      size_t s, e, n;
      if (!next_line(d, size, pos, &s, &e, &n)) break;
      pos = n;
      continue;
    }
    if (c == 0 && (line_equals_trim(d, vs, ve, "ENDSEC") ||
                   line_equals_trim(d, vs, ve, "EOF"))) {
      break;
    }
    if (c == 0) (*count)++;
    pos = vn;
  }
  return 1;
}

static int find_kth_code_zero_record(const uint8_t *d, size_t size, size_t start,
                                     size_t k,
                                     size_t *val_start, size_t *val_end,
                                     size_t *val_next) {
  size_t pos = start;
  size_t idx = 0;
  while (pos < size) {
    int c;
    size_t cs, ce, cn, vs, ve, vn;
    if (!get_record_at(d, size, pos, &c, &cs, &ce, &cn, &vs, &ve, &vn)) {
      size_t s, e, n;
      if (!next_line(d, size, pos, &s, &e, &n)) break;
      pos = n;
      continue;
    }
    if (c == 0 && (line_equals_trim(d, vs, ve, "ENDSEC") ||
                   line_equals_trim(d, vs, ve, "EOF"))) {
      break;
    }
    if (c == 0) {
      if (idx == k) {
        *val_start = vs;
        *val_end = ve;
        *val_next = vn;
        return 1;
      }
      idx++;
    }
    pos = vn;
  }
  return 0;
}

static int find_record_by_code_value(const uint8_t *d, size_t size, int want_code,
                                     const char *want_val, size_t *record_start) {
  size_t pos = 0;
  while (pos < size) {
    int c;
    size_t cs, ce, cn, vs, ve, vn;
    if (!get_record_at(d, size, pos, &c, &cs, &ce, &cn, &vs, &ve, &vn)) {
      size_t s, e, n;
      if (!next_line(d, size, pos, &s, &e, &n)) break;
      pos = n;
      continue;
    }
    if (c == want_code && line_equals_trim(d, vs, ve, want_val)) {
      *record_start = cs;
      return 1;
    }
    pos = vn;
  }
  return 0;
}

static uint32_t rng_next(uint32_t *state) {
  uint32_t x = *state;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  *state = x;
  return x;
}

static void generate_name(unsigned int seed, const uint8_t *orig,
                          size_t orig_len, char *out, size_t *out_len) {
  static const char alphabet[] =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  const size_t alen = sizeof(alphabet) - 1;
  uint32_t st = (uint32_t)seed * 0x9e3779b9u + 0x85ebca6bu;
  size_t len;
  size_t i;
  if (st == 0) st = 1;
  len = 1 + (rng_next(&st) % 64);
  for (i = 0; i < len; i++) {
    out[i] = alphabet[rng_next(&st) % alen];
  }
  if (orig && orig_len == len && memcmp(out, orig, len) == 0) {
    size_t idx = 0;
    for (idx = 0; idx < alen; idx++) {
      if (alphabet[idx] == out[0]) break;
    }
    out[0] = alphabet[(idx + 1 + (seed % (alen - 1))) % alen];
    if (orig_len == 1 && out[0] == (char)orig[0]) {
      out[0] = alphabet[(idx + 2) % alen];
    }
  }
  *out_len = len;
}

static size_t replace_value_line(uint8_t *d, size_t size, size_t max_size,
                                 size_t val_start, size_t val_end,
                                 unsigned int seed) {
  char name[64];
  size_t nlen = 0;
  size_t oldlen;
  size_t newsize;
  if (val_start > val_end || val_end > size) return size;
  oldlen = val_end - val_start;
  generate_name(seed, d + val_start, oldlen, name, &nlen);
  if (nlen > 64) return size;
  if (nlen > oldlen && size + (nlen - oldlen) > max_size) return size;
  newsize = size - oldlen + nlen;
  if (newsize > max_size) return size;
  memmove(d + val_start + nlen, d + val_end, size - val_end);
  memcpy(d + val_start, name, nlen);
  return newsize;
}

static size_t construct_objects_section(uint8_t *d, size_t size, size_t max_size,
                                        unsigned int seed) {
  static const char pre[] = "0\r\nSECTION\r\n2\r\nOBJECTS\r\n0\r\n";
  static const char post[] = "\r\n0\r\nENDSEC\r\n";
  char name[64];
  size_t nlen = 0;
  size_t ins_pos = size;
  size_t prelen = sizeof(pre) - 1;
  size_t postlen = sizeof(post) - 1;
  size_t ins_len;
  find_record_by_code_value(d, size, 0, "EOF", &ins_pos);
  generate_name(seed, NULL, 0, name, &nlen);
  if (nlen > 64) return size;
  ins_len = prelen + nlen + postlen;
  if (ins_pos > size) ins_pos = size;
  if (size + ins_len > max_size) return size;
  memmove(d + ins_pos + ins_len, d + ins_pos, size - ins_pos);
  memcpy(d + ins_pos, pre, prelen);
  memcpy(d + ins_pos + prelen, name, nlen);
  memcpy(d + ins_pos + prelen + nlen, post, postlen);
  return size + ins_len;
}

static size_t mutate_a001(uint8_t *d, size_t size, size_t max_size,
                          unsigned int seed) {
  size_t after_anchor = 0;
  size_t count = 0;
  size_t k;
  size_t val_start = 0, val_end = 0, val_next = 0;
  if (find_section_anchor(d, size, "OBJECTS", &after_anchor)) {
    if (count_code_zero_records(d, size, after_anchor, &count) && count > 0) {
      k = seed % count;
      if (find_kth_code_zero_record(d, size, after_anchor, k,
                                    &val_start, &val_end, &val_next)) {
        return replace_value_line(d, size, max_size, val_start, val_end, seed);
      }
    }
    return size;
  }
  return construct_objects_section(d, size, max_size, seed);
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize,
                               unsigned int Seed) {
  int is_dxf = 1;
  unsigned int r;
  if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') {
    is_dxf = 0;
  } else if (Size >= 1 && Data[0] == '{') {
    is_dxf = 0;
  }
  if (!is_dxf) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  r = Seed % 1000;
  if (r < 500) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  return mutate_a001(Data, Size, MaxSize, Seed);
}
