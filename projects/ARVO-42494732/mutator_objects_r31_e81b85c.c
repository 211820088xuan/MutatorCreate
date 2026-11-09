#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct {
  size_t start;
  size_t content_end;
  size_t next_start;
} Line;

static int get_line(const uint8_t *Data, size_t Size, size_t pos, Line *out) {
  if (pos >= Size) return 0;
  out->start = pos;
  size_t i = pos;
  while (i < Size) {
    if (Data[i] == '\n') {
      out->content_end = i;
      out->next_start = i + 1;
      return 1;
    } else if (Data[i] == '\r') {
      out->content_end = i;
      if (i + 1 < Size && Data[i + 1] == '\n') out->next_start = i + 2;
      else out->next_start = i + 1;
      return 1;
    }
    i++;
  }
  out->content_end = Size;
  out->next_start = Size;
  return 1;
}

static int parse_code_line(const uint8_t *Data, const Line *ln, unsigned *code) {
  size_t i = ln->start;
  while (i < ln->content_end && (Data[i] == ' ' || Data[i] == '\t')) i++;
  unsigned v = 0;
  int nd = 0;
  while (i < ln->content_end && Data[i] >= '0' && Data[i] <= '9') {
    if (nd >= 3) return 0;
    v = v * 10u + (unsigned)(Data[i] - '0');
    nd++;
    i++;
  }
  if (nd == 0) return 0;
  while (i < ln->content_end && (Data[i] == ' ' || Data[i] == '\t')) i++;
  if (i != ln->content_end) return 0;
  *code = v;
  return 1;
}

static void trim_bounds(const uint8_t *Data, const Line *ln, size_t *a, size_t *b) {
  size_t x = ln->start, y = ln->content_end;
  while (x < y && (Data[x] == ' ' || Data[x] == '\t')) x++;
  while (y > x && (Data[y - 1] == ' ' || Data[y - 1] == '\t')) y--;
  *a = x;
  *b = y;
}

static int line_value_is(const uint8_t *Data, const Line *ln, const char *s) {
  size_t a, b;
  trim_bounds(Data, ln, &a, &b);
  size_t n = strlen(s);
  return (b - a == n) && (memcmp(Data + a, s, n) == 0);
}

static int find_objects_section(const uint8_t *Data, size_t Size, size_t *sec_start, size_t *sec_end) {
  size_t pos = 0;
  while (pos < Size) {
    Line lc;
    if (!get_line(Data, Size, pos, &lc)) break;
    unsigned code;
    if (!parse_code_line(Data, &lc, &code)) { pos = lc.next_start; continue; }
    if (lc.next_start >= Size) break;
    Line lv;
    if (!get_line(Data, Size, lc.next_start, &lv)) break;
    if (code == 2 && line_value_is(Data, &lv, "OBJECTS")) {
      *sec_start = lv.next_start;
      size_t p = *sec_start;
      while (p < Size) {
        Line ec;
        if (!get_line(Data, Size, p, &ec)) break;
        unsigned ec_code;
        if (!parse_code_line(Data, &ec, &ec_code)) { p = ec.next_start; continue; }
        if (ec.next_start >= Size) { p = ec.next_start; continue; }
        Line ev;
        if (!get_line(Data, Size, ec.next_start, &ev)) break;
        if (ec_code == 0 && line_value_is(Data, &ev, "ENDSEC")) {
          *sec_end = ec.start;
          return 1;
        }
        p = ev.next_start;
      }
      *sec_end = Size;
      return 1;
    }
    pos = lv.next_start;
  }
  pos = 0;
  while (pos < Size) {
    Line l;
    if (!get_line(Data, Size, pos, &l)) break;
    if (line_value_is(Data, &l, "OBJECTS")) {
      *sec_start = l.next_start;
      size_t p = *sec_start;
      while (p < Size) {
        Line ec;
        if (!get_line(Data, Size, p, &ec)) break;
        unsigned ec_code;
        if (!parse_code_line(Data, &ec, &ec_code)) { p = ec.next_start; continue; }
        if (ec.next_start >= Size) { p = ec.next_start; continue; }
        Line ev;
        if (!get_line(Data, Size, ec.next_start, &ev)) break;
        if (ec_code == 0 && line_value_is(Data, &ev, "ENDSEC")) {
          *sec_end = ec.start;
          return 1;
        }
        p = ev.next_start;
      }
      *sec_end = Size;
      return 1;
    }
    pos = l.next_start;
  }
  return 0;
}

static size_t count_code0_records(const uint8_t *Data, size_t Size, size_t sec_start, size_t sec_end) {
  size_t p = sec_start;
  size_t count = 0;
  while (p < sec_end && p < Size) {
    Line lc;
    if (!get_line(Data, Size, p, &lc)) break;
    unsigned code;
    if (!parse_code_line(Data, &lc, &code)) { p = lc.next_start; continue; }
    if (lc.next_start >= Size) break;
    Line lv;
    if (!get_line(Data, Size, lc.next_start, &lv)) break;
    if (code == 0 && lc.start < sec_end && lv.start < sec_end) count++;
    p = lv.next_start;
  }
  return count;
}

static int find_kth_code0_value(const uint8_t *Data, size_t Size, size_t sec_start, size_t sec_end, size_t k, Line *code_line, Line *value_line) {
  size_t p = sec_start;
  size_t idx = 0;
  while (p < sec_end && p < Size) {
    Line lc;
    if (!get_line(Data, Size, p, &lc)) break;
    unsigned code;
    if (!parse_code_line(Data, &lc, &code)) { p = lc.next_start; continue; }
    if (lc.next_start >= Size) break;
    Line lv;
    if (!get_line(Data, Size, lc.next_start, &lv)) break;
    if (code == 0 && lc.start < sec_end && lv.start < sec_end) {
      if (idx == k) {
        *code_line = lc;
        *value_line = lv;
        return 1;
      }
      idx++;
    }
    p = lv.next_start;
  }
  return 0;
}

static int find_eof_insert_pos(const uint8_t *Data, size_t Size, size_t *pos_out) {
  size_t p = 0;
  while (p < Size) {
    Line lc;
    if (!get_line(Data, Size, p, &lc)) break;
    unsigned code;
    if (!parse_code_line(Data, &lc, &code)) { p = lc.next_start; continue; }
    if (lc.next_start >= Size) break;
    Line lv;
    if (!get_line(Data, Size, lc.next_start, &lv)) break;
    if (code == 0 && line_value_is(Data, &lv, "EOF")) {
      *pos_out = lc.start;
      return 1;
    }
    p = lv.next_start;
  }
  return 0;
}

static uint32_t rng_next(uint32_t *s) {
  *s = *s * 1664525u + 1013904223u;
  return *s;
}

static size_t generate_name(uint32_t *state, uint8_t *out, size_t max_len, const uint8_t *orig, size_t orig_len) {
  static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  size_t alpha_len = sizeof(alphabet) - 1;
  if (max_len == 0) return 0;
  size_t len = 1 + (size_t)(rng_next(state) % 64u);
  if (len > max_len) len = max_len;
  size_t i;
  for (i = 0; i < len; i++) {
    out[i] = (uint8_t)alphabet[rng_next(state) % (uint32_t)alpha_len];
  }
  if (len == orig_len && orig_len > 0 && memcmp(out, orig, len) == 0) {
    size_t idx = 0;
    while (idx < alpha_len && (uint8_t)alphabet[idx] != out[0]) idx++;
    if (idx < alpha_len) out[0] = (uint8_t)alphabet[(idx + 1) % alpha_len];
    else out[0] = (uint8_t)alphabet[0];
    if (len == orig_len && memcmp(out, orig, len) == 0) {
      if (len < max_len) {
        out[len++] = (uint8_t)alphabet[rng_next(state) % (uint32_t)alpha_len];
      } else if (len > 1) {
        len--;
      }
    }
  }
  return len;
}

static size_t strategy_a001_ensure_record_structure(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  uint32_t rng = (uint32_t)Seed ^ (uint32_t)(Size * 2654435761u) ^ 0x9e3779b9u;
  rng = rng * 1664525u + 1013904223u;
  size_t sec_start = 0, sec_end = 0;
  if (find_objects_section(Data, Size, &sec_start, &sec_end)) {
    size_t cnt = count_code0_records(Data, Size, sec_start, sec_end);
    if (cnt == 0) return Size;
    size_t k = (size_t)(rng_next(&rng) % (uint32_t)cnt);
    Line cl, vl;
    if (!find_kth_code0_value(Data, Size, sec_start, sec_end, k, &cl, &vl)) return Size;
    (void)cl;
    size_t a, b;
    trim_bounds(Data, &vl, &a, &b);
    size_t old_len = vl.content_end - vl.start;
    size_t avail = MaxSize - (Size - old_len);
    if (avail > 64) avail = 64;
    if (avail == 0) return Size;
    uint8_t name[64];
    size_t nlen = generate_name(&rng, name, avail, Data + a, b - a);
    if (nlen == 0) return Size;
    size_t new_size = Size - old_len + nlen;
    if (new_size > MaxSize) return Size;
    memmove(Data + vl.start + nlen, Data + vl.content_end, Size - vl.content_end);
    memcpy(Data + vl.start, name, nlen);
    return new_size;
  } else {
    size_t insert_pos = 0;
    int have_eof = find_eof_insert_pos(Data, Size, &insert_pos);
    if (!have_eof) insert_pos = Size;
    size_t prefix_len = 0;
    if (!have_eof && insert_pos == Size && Size > 0 && Data[Size - 1] != '\n' && Data[Size - 1] != '\r') {
      prefix_len = 2;
    }
    static const char p1[] = "0\r\nSECTION\r\n2\r\nOBJECTS\r\n0\r\n";
    static const char p3[] = "\r\n0\r\nENDSEC\r\n";
    size_t base_len = prefix_len + (sizeof(p1) - 1) + (sizeof(p3) - 1);
    if (MaxSize < Size + base_len + 1) return LLVMFuzzerMutate(Data, Size, MaxSize);
    size_t max_name = MaxSize - Size - base_len;
    if (max_name > 64) max_name = 64;
    if (max_name == 0) return LLVMFuzzerMutate(Data, Size, MaxSize);
    uint8_t name[64];
    size_t nlen = generate_name(&rng, name, max_name, NULL, 0);
    if (nlen == 0) return LLVMFuzzerMutate(Data, Size, MaxSize);
    size_t ins_len = base_len + nlen;
    if (Size + ins_len > MaxSize) return LLVMFuzzerMutate(Data, Size, MaxSize);
    uint8_t ins[256];
    size_t off = 0;
    if (prefix_len == 2) {
      ins[off++] = '\r';
      ins[off++] = '\n';
    }
    memcpy(ins + off, p1, sizeof(p1) - 1);
    off += sizeof(p1) - 1;
    memcpy(ins + off, name, nlen);
    off += nlen;
    memcpy(ins + off, p3, sizeof(p3) - 1);
    off += sizeof(p3) - 1;
    if (off != ins_len) return LLVMFuzzerMutate(Data, Size, MaxSize);
    memmove(Data + insert_pos + ins_len, Data + insert_pos, Size - insert_pos);
    memcpy(Data + insert_pos, ins, ins_len);
    return Size + ins_len;
  }
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') return LLVMFuzzerMutate(Data, Size, MaxSize);
  if (Size >= 1 && Data[0] == '{') return LLVMFuzzerMutate(Data, Size, MaxSize);
  unsigned r = Seed % 1000u;
  if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);
  return strategy_a001_ensure_record_structure(Data, Size, MaxSize, Seed);
}
