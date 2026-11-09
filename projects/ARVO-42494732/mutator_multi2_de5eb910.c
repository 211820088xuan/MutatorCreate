#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct {
  size_t start;
  size_t content_end;
  size_t end;
} DxfLine;

static int is_ws(uint8_t c) {
  return c == ' ' || c == '\t' || c == '\v' || c == '\f' || c == '\r' || c == '\n';
}

static int dxf_next_line(const uint8_t *d, size_t n, size_t *pos, DxfLine *out) {
  if (*pos >= n) return 0;
  size_t s = *pos;
  size_t e = s;
  while (e < n && d[e] != '\r' && d[e] != '\n') e++;
  size_t ce = e;
  size_t le = e;
  if (le < n) {
    if (d[le] == '\r') {
      le++;
      if (le < n && d[le] == '\n') le++;
    } else if (d[le] == '\n') {
      le++;
    }
  }
  out->start = s;
  out->content_end = ce;
  out->end = le;
  *pos = le;
  return 1;
}

static int line_trim_eq(const uint8_t *d, const DxfLine *ln, const char *s) {
  size_t i = ln->start;
  size_t j = ln->content_end;
  while (i < j && is_ws(d[i])) i++;
  while (j > i && is_ws(d[j - 1])) j--;
  size_t sl = strlen(s);
  return (j - i == sl) && (memcmp(d + i, s, sl) == 0);
}

static int line_parse_code(const uint8_t *d, const DxfLine *ln, int *code) {
  size_t i = ln->start;
  size_t j = ln->content_end;
  while (i < j && is_ws(d[i])) i++;
  while (j > i && is_ws(d[j - 1])) j--;
  if (j <= i || j - i > 3) return 0;
  int v = 0;
  for (size_t k = i; k < j; k++) {
    if (d[k] < '0' || d[k] > '9') return 0;
    v = v * 10 + (int)(d[k] - '0');
  }
  *code = v;
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

static void make_random_name(unsigned Seed, uint32_t salt, const uint8_t *orig, size_t orig_len, char *out, size_t *out_len) {
  static const char alpha[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  const size_t alen = sizeof(alpha) - 1;
  uint32_t s = (uint32_t)Seed ^ salt ^ 0x9e3779b9u;
  if (s == 0) s = 0x1234567u;
  uint32_t r = rng_next(&s);
  size_t len = 1u + (size_t)(r % 64u);
  for (size_t i = 0; i < len; i++) {
    r = rng_next(&s);
    out[i] = alpha[r % alen];
  }
  if (orig && orig_len > 0 && len == orig_len) {
    int same = 1;
    for (size_t i = 0; i < len; i++) {
      if ((uint8_t)out[i] != orig[i]) { same = 0; break; }
    }
    if (same) {
      char c = out[0];
      for (size_t j = 0; j < alen; j++) {
        if (alpha[j] != c) { out[0] = alpha[j]; break; }
      }
    }
  }
  *out_len = len;
}

static int find_anchor(const uint8_t *d, size_t n, size_t *after_anchor) {
  size_t pos = 0;
  while (pos < n) {
    DxfLine ln;
    if (!dxf_next_line(d, n, &pos, &ln)) break;
    if (line_trim_eq(d, &ln, "OBJECTS")) {
      *after_anchor = ln.end;
      return 1;
    }
  }
  return 0;
}

static size_t find_section_end(const uint8_t *d, size_t n, size_t start) {
  size_t pos = start;
  while (pos < n) {
    DxfLine code_ln;
    if (!dxf_next_line(d, n, &pos, &code_ln)) break;
    DxfLine val_ln;
    size_t vpos = pos;
    if (!dxf_next_line(d, n, &vpos, &val_ln)) break;
    int code;
    if (line_parse_code(d, &code_ln, &code) && code == 0) {
      if (line_trim_eq(d, &val_ln, "ENDSEC") || line_trim_eq(d, &val_ln, "EOF")) {
        return code_ln.start;
      }
    }
    pos = val_ln.end;
  }
  return n;
}

static int select_value_line(const uint8_t *d, size_t n, size_t start, size_t end, uint32_t rnd, DxfLine *out_val) {
  if (end > n) end = n;
  size_t count = 0;
  size_t pos = start;
  while (pos < end) {
    DxfLine code_ln;
    if (!dxf_next_line(d, n, &pos, &code_ln)) break;
    if (code_ln.start >= end) break;
    DxfLine val_ln;
    size_t vpos = pos;
    if (!dxf_next_line(d, n, &vpos, &val_ln)) break;
    if (val_ln.start >= end) break;
    int code;
    if (line_parse_code(d, &code_ln, &code) && code == 0) {
      if (!line_trim_eq(d, &val_ln, "ENDSEC") && !line_trim_eq(d, &val_ln, "EOF")) {
        count++;
      }
    }
    pos = val_ln.end;
  }
  if (count == 0) return 0;
  size_t want = (size_t)rnd % count;
  size_t idx = 0;
  pos = start;
  while (pos < end) {
    DxfLine code_ln;
    if (!dxf_next_line(d, n, &pos, &code_ln)) break;
    if (code_ln.start >= end) break;
    DxfLine val_ln;
    size_t vpos = pos;
    if (!dxf_next_line(d, n, &vpos, &val_ln)) break;
    if (val_ln.start >= end) break;
    int code;
    if (line_parse_code(d, &code_ln, &code) && code == 0) {
      if (!line_trim_eq(d, &val_ln, "ENDSEC") && !line_trim_eq(d, &val_ln, "EOF")) {
        if (idx == want) { *out_val = val_ln; return 1; }
        idx++;
      }
    }
    pos = val_ln.end;
  }
  return 0;
}

static int find_eof_record(const uint8_t *d, size_t n, size_t *out_start) {
  size_t pos = 0;
  while (pos < n) {
    DxfLine code_ln;
    size_t p = pos;
    if (!dxf_next_line(d, n, &p, &code_ln)) break;
    int code;
    if (line_parse_code(d, &code_ln, &code) && code == 0) {
      DxfLine val_ln;
      size_t vpos = p;
      if (dxf_next_line(d, n, &vpos, &val_ln) && line_trim_eq(d, &val_ln, "EOF")) {
        *out_start = code_ln.start;
        return 1;
      }
    }
    pos = code_ln.end;
  }
  return 0;
}

static size_t replace_value_line(uint8_t *Data, size_t Size, size_t MaxSize, const DxfLine *val, const char *name, size_t name_len) {
  if (val->start > Size || val->content_end < val->start || val->content_end > Size) return Size;
  size_t old_len = val->content_end - val->start;
  size_t base = Size - old_len;
  if (base > MaxSize || name_len > MaxSize - base) return Size;
  size_t new_size = base + name_len;
  memmove(Data + val->start + name_len, Data + val->content_end, Size - val->content_end);
  memcpy(Data + val->start, name, name_len);
  return new_size;
}

static size_t construct_section(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed, uint32_t salt) {
  char name[65];
  size_t name_len = 0;
  make_random_name(Seed, salt, NULL, 0, name, &name_len);
  char ins[256];
  size_t ip = 0;
  size_t insert_pos = Size;
  int found = find_eof_record(Data, Size, &insert_pos);
  if (!found) {
    insert_pos = Size;
    if (Size > 0 && Data[Size - 1] != '\n' && Data[Size - 1] != '\r') {
      ins[ip++] = '\r';
      ins[ip++] = '\n';
    }
  }
  const char *p1 = "0\r\nSECTION\r\n2\r\nOBJECTS\r\n0\r\n";
  const char *p2 = "\r\n0\r\nENDSEC\r\n";
  size_t l1 = strlen(p1);
  size_t l2 = strlen(p2);
  if (ip + l1 + name_len + l2 > sizeof(ins)) return Size;
  memcpy(ins + ip, p1, l1); ip += l1;
  memcpy(ins + ip, name, name_len); ip += name_len;
  memcpy(ins + ip, p2, l2); ip += l2;
  if (ip > MaxSize || Size > MaxSize - ip) return Size;
  size_t new_size = Size + ip;
  memmove(Data + insert_pos + ip, Data + insert_pos, Size - insert_pos);
  memcpy(Data + insert_pos, ins, ip);
  return new_size;
}

static size_t ensure_record_structure_value_line(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed, uint32_t salt) {
  size_t anchor_end = 0;
  if (find_anchor(Data, Size, &anchor_end)) {
    size_t sec_end = find_section_end(Data, Size, anchor_end);
    uint32_t rs = (uint32_t)Seed ^ salt ^ 0x9e3779b9u;
    if (rs == 0) rs = 0x1234567u;
    uint32_t rk = rng_next(&rs);
    DxfLine val;
    if (select_value_line(Data, Size, anchor_end, sec_end, rk, &val)) {
      char name[65];
      size_t name_len = 0;
      const uint8_t *orig = Data + val.start;
      size_t orig_len = val.content_end - val.start;
      make_random_name(Seed, salt, orig, orig_len, name, &name_len);
      return replace_value_line(Data, Size, MaxSize, &val, name, name_len);
    }
    return Size;
  }
  return construct_section(Data, Size, MaxSize, Seed, salt);
}

static int is_dxf_input(const uint8_t *Data, size_t Size) {
  if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') return 0;
  if (Size >= 1 && Data[0] == '{') return 0;
  return 1;
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  if (!is_dxf_input(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
  return ensure_record_structure_value_line(Data, Size, MaxSize, Seed, 0x10001u);
}

static size_t mutate_a002(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  if (!is_dxf_input(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
  return ensure_record_structure_value_line(Data, Size, MaxSize, Seed, 0x20002u);
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  if (!is_dxf_input(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
  unsigned r = Seed % 1000u;
  if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);
  if (r < 750u) return mutate_a001(Data, Size, MaxSize, Seed);
  return mutate_a002(Data, Size, MaxSize, Seed);
}
