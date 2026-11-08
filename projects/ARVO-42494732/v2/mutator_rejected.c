#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct { uint32_t s; } Rng;

static const char SECTION_STR[] = {'S','E','C','T','I','O','N',0};
static const char OBJECTS_STR[] = {'O','B','J','E','C','T','S',0};
static const char ENDSEC_STR[] = {'E','N','D','S','E','C',0};
static const char EOF_STR[] = {'E','O','F',0};

static uint32_t rng_next(Rng *r) {
  uint32_t x = r->s;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  r->s = x;
  return x;
}

static void rng_init(Rng *r, unsigned seed, unsigned salt) {
  uint32_t s = (uint32_t)seed ^ (salt * 0x9e3779b9u);
  if (s == 0) s = 0x12345678u;
  r->s = s;
}

static size_t rng_range(Rng *r, size_t n) {
  if (n == 0) return 0;
  return (size_t)(rng_next(r) % n);
}

static int is_dxf_scope(const uint8_t *Data, size_t Size) {
  if (Size >= 2 && Data[0] == 0xAC) return 0;
  if (Size >= 1 && Data[0] == '{') return 0;
  return 1;
}

static int next_line(const uint8_t *Data, size_t Size, size_t pos, size_t *line_end, size_t *next_pos) {
  if (pos >= Size) { *line_end = Size; *next_pos = Size; return 0; }
  size_t i = pos;
  while (i < Size && Data[i] != 10 && Data[i] != 13) i++;
  *line_end = i;
  if (i < Size && Data[i] == 13) {
    i++;
    if (i < Size && Data[i] == 10) i++;
  } else if (i < Size && Data[i] == 10) {
    i++;
  }
  *next_pos = i;
  return 1;
}

static int parse_group_code(const uint8_t *Data, size_t start, size_t end, int *out) {
  size_t i = start;
  while (i < end && (Data[i] == ' ' || Data[i] == 9)) i++;
  if (i >= end) return 0;
  int val = 0; int any = 0;
  while (i < end && Data[i] >= '0' && Data[i] <= '9') {
    any = 1; val = val * 10 + (Data[i] - '0'); i++;
  }
  if (!any) return 0;
  while (i < end && (Data[i] == ' ' || Data[i] == 9)) i++;
  if (i != end) return 0;
  *out = val;
  return 1;
}

static int equals_trim(const uint8_t *Data, size_t start, size_t end, const char *s) {
  size_t i = start;
  while (i < end && (Data[i] == ' ' || Data[i] == 9)) i++;
  size_t e = end;
  while (e > i && (Data[e-1] == ' ' || Data[e-1] == 9)) e--;
  size_t j = 0;
  while (s[j]) {
    if (i + j >= e || Data[i + j] != (uint8_t)s[j]) return 0;
    j++;
  }
  return i + j == e;
}

static int get_record(const uint8_t *Data, size_t Size, size_t pos, int *code, size_t *val_start, size_t *val_end, size_t *next_pos) {
  size_t code_end, code_next;
  if (!next_line(Data, Size, pos, &code_end, &code_next)) return 0;
  int c;
  if (!parse_group_code(Data, pos, code_end, &c)) {
    *next_pos = code_next;
    return 0;
  }
  if (code_next >= Size) {
    *code = c;
    *val_start = code_next;
    *val_end = code_next;
    *next_pos = code_next;
    return 1;
  }
  size_t val_line_end, val_next;
  next_line(Data, Size, code_next, &val_line_end, &val_next);
  *code = c;
  *val_start = code_next;
  *val_end = val_line_end;
  *next_pos = val_next;
  return 1;
}

static int find_objects_section(const uint8_t *Data, size_t Size, size_t *content_start, size_t *sec_end) {
  size_t pos = 0;
  while (pos < Size) {
    int code; size_t vs, ve, next;
    if (!get_record(Data, Size, pos, &code, &vs, &ve, &next)) {
      size_t le, np;
      next_line(Data, Size, pos, &le, &np);
      if (np <= pos) break;
      pos = np;
      continue;
    }
    if (code == 0 && equals_trim(Data, vs, ve, SECTION_STR)) {
      size_t p = next;
      while (p < Size) {
        int c2; size_t vs2, ve2, next2;
        if (!get_record(Data, Size, p, &c2, &vs2, &ve2, &next2)) {
          size_t le, np;
          next_line(Data, Size, p, &le, &np);
          if (np <= p) break;
          p = np;
          continue;
        }
        if (c2 == 2 && equals_trim(Data, vs2, ve2, OBJECTS_STR)) {
          size_t q = next2;
          while (q < Size) {
            int c3; size_t vs3, ve3, next3;
            if (!get_record(Data, Size, q, &c3, &vs3, &ve3, &next3)) {
              size_t le, np;
              next_line(Data, Size, q, &le, &np);
              if (np <= q) break;
              q = np;
              continue;
            }
            if (c3 == 0 && equals_trim(Data, vs3, ve3, ENDSEC_STR)) {
              *content_start = next2;
              *sec_end = q;
              return 1;
            }
            if (next3 <= q) break;
            q = next3;
          }
          *content_start = next2;
          *sec_end = Size;
          return 1;
        }
        if (c2 == 0 && equals_trim(Data, vs2, ve2, ENDSEC_STR)) break;
        if (next2 <= p) break;
        p = next2;
      }
      pos = next;
      continue;
    }
    if (next <= pos) break;
    pos = next;
  }
  return 0;
}

static char alpha_char(unsigned v) {
  v = v % 64u;
  if (v < 26u) return (char)('A' + v);
  v -= 26u;
  if (v < 26u) return (char)('a' + v);
  v -= 26u;
  if (v < 10u) return (char)('0' + v);
  v -= 10u;
  if (v == 0u) return '_';
  return '-';
}

static size_t gen_name(char *out, size_t cap, Rng *rng, const uint8_t *old, size_t old_len) {
  if (cap == 0) return 0;
  size_t len = 1 + rng_range(rng, 64);
  if (len > cap) len = cap;
  size_t i;
  for (i = 0; i < len; i++) {
    out[i] = alpha_char((unsigned)rng_next(rng));
  }
  if (old != NULL && len == old_len && old_len > 0) {
    int same = 1;
    for (i = 0; i < len; i++) {
      if ((uint8_t)out[i] != old[i]) { same = 0; break; }
    }
    if (same) {
      out[len-1] = (out[len-1] == 'A') ? 'B' : 'A';
    }
  }
  return len;
}

static size_t replace_range(uint8_t *Data, size_t Size, size_t MaxSize, size_t start, size_t end, const char *newbuf, size_t newlen) {
  if (start > end || end > Size) return Size;
  size_t oldlen = end - start;
  if (newlen > oldlen) {
    size_t delta = newlen - oldlen;
    if (Size + delta > MaxSize) return Size;
    memmove(Data + end + delta, Data + end, Size - end);
  } else if (newlen < oldlen) {
    size_t delta = oldlen - newlen;
    memmove(Data + start + newlen, Data + end, Size - end);
  }
  memcpy(Data + start, newbuf, newlen);
  if (newlen > oldlen) return Size + (newlen - oldlen);
  if (newlen < oldlen) return Size - (oldlen - newlen);
  return Size;
}

static void append_str(uint8_t *dst, size_t *pos, const char *s) {
  while (*s) { dst[*pos] = (uint8_t)*s; (*pos)++; s++; }
}

static void append_crlf(uint8_t *dst, size_t *pos) {
  dst[*pos] = 13; (*pos)++;
  dst[*pos] = 10; (*pos)++;
}

static size_t mutate_objects_value(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed, unsigned salt) {
  if (!is_dxf_scope(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
  Rng rng;
  rng_init(&rng, Seed, salt);
  size_t content_start, sec_end;
  if (find_objects_section(Data, Size, &content_start, &sec_end)) {
    size_t pos = content_start;
    size_t count = 0;
    while (pos < sec_end) {
      int code; size_t vs, ve, next;
      if (!get_record(Data, Size, pos, &code, &vs, &ve, &next)) {
        size_t le, np;
        next_line(Data, Size, pos, &le, &np);
        if (np <= pos) break;
        pos = np;
        continue;
      }
      if (code == 0) count++;
      if (next <= pos) break;
      pos = next;
    }
    if (count == 0) return LLVMFuzzerMutate(Data, Size, MaxSize);
    size_t k = rng_range(&rng, count);
    pos = content_start;
    size_t idx = 0;
    size_t val_start = 0, val_end = 0;
    int found = 0;
    while (pos < sec_end) {
      int code; size_t vs, ve, next;
      if (!get_record(Data, Size, pos, &code, &vs, &ve, &next)) {
        size_t le, np;
        next_line(Data, Size, pos, &le, &np);
        if (np <= pos) break;
        pos = np;
        continue;
      }
      if (code == 0) {
        if (idx == k) { val_start = vs; val_end = ve; found = 1; break; }
        idx++;
      }
      if (next <= pos) break;
      pos = next;
    }
    if (!found) return LLVMFuzzerMutate(Data, Size, MaxSize);
    size_t old_len_full = val_end - val_start;
    char newname[64];
    size_t newlen = gen_name(newname, sizeof(newname), &rng, Data + val_start, old_len_full);
    return replace_range(Data, Size, MaxSize, val_start, val_end, newname, newlen);
  } else {
    size_t insert_pos = Size;
    size_t pos = 0;
    while (pos < Size) {
      int code; size_t vs, ve, next;
      if (!get_record(Data, Size, pos, &code, &vs, &ve, &next)) {
        size_t le, np;
        next_line(Data, Size, pos, &le, &np);
        if (np <= pos) break;
        pos = np;
        continue;
      }
      if (code == 0 && equals_trim(Data, vs, ve, EOF_STR)) {
        insert_pos = pos;
        break;
      }
      if (next <= pos) break;
      pos = next;
    }
    if (MaxSize < Size + 41) return LLVMFuzzerMutate(Data, Size, MaxSize);
    size_t maxL = MaxSize - Size - 40;
    if (maxL > 64) maxL = 64;
    if (maxL < 1) maxL = 1;
    size_t want = 1 + rng_range(&rng, 64);
    if (want > maxL) want = maxL;
    char newname[64];
    size_t newlen = gen_name(newname, want, &rng, NULL, 0);
    uint8_t ins[256];
    size_t ip = 0;
    ins[ip++] = '0'; append_crlf(ins, &ip);
    append_str(ins, &ip, SECTION_STR); append_crlf(ins, &ip);
    ins[ip++] = '2'; append_crlf(ins, &ip);
    append_str(ins, &ip, OBJECTS_STR); append_crlf(ins, &ip);
    ins[ip++] = '0'; append_crlf(ins, &ip);
    memcpy(ins + ip, newname, newlen); ip += newlen;
    append_crlf(ins, &ip);
    ins[ip++] = '0'; append_crlf(ins, &ip);
    append_str(ins, &ip, ENDSEC_STR); append_crlf(ins, &ip);
    if (Size + ip > MaxSize) return LLVMFuzzerMutate(Data, Size, MaxSize);
    memmove(Data + insert_pos + ip, Data + insert_pos, Size - insert_pos);
    memcpy(Data + insert_pos, ins, ip);
    return Size + ip;
  }
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  return mutate_objects_value(Data, Size, MaxSize, Seed, 0xA001u);
}
static size_t mutate_a002(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  return mutate_objects_value(Data, Size, MaxSize, Seed, 0xA002u);
}
static size_t mutate_a003(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  return mutate_objects_value(Data, Size, MaxSize, Seed, 0xA003u);
}
static size_t mutate_a004(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  return mutate_objects_value(Data, Size, MaxSize, Seed, 0xA004u);
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  if (!is_dxf_scope(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
  unsigned r = Seed % 1000u;
  if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);
  unsigned idx = (r - 500u) / 125u;
  switch (idx) {
    case 0: return mutate_a001(Data, Size, MaxSize, Seed);
    case 1: return mutate_a002(Data, Size, MaxSize, Seed);
    case 2: return mutate_a003(Data, Size, MaxSize, Seed);
    case 3: return mutate_a004(Data, Size, MaxSize, Seed);
    default: return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
}