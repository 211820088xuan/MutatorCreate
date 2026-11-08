#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

static const char *ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
#define ALPHABET_LEN 64

static int next_line(const uint8_t *Data, size_t Size, size_t pos,
                     size_t *line_start, size_t *line_len,
                     size_t *next_pos, size_t *eol_len) {
  if (pos >= Size) return 0;
  size_t i = pos;
  while (i < Size && Data[i] != '\r' && Data[i] != '\n') i++;
  *line_start = pos;
  *line_len = i - pos;
  size_t eol = 0;
  if (i < Size) {
    if (Data[i] == '\r') {
      if (i + 1 < Size && Data[i + 1] == '\n') eol = 2;
      else eol = 1;
    } else {
      eol = 1;
    }
  }
  *eol_len = eol;
  *next_pos = i + eol;
  return 1;
}

static int line_equals_trim(const uint8_t *p, size_t len, const char *s) {
  size_t a = 0, b = len;
  while (a < b && (p[a] == ' ' || p[a] == '\t')) a++;
  while (b > a && (p[b - 1] == ' ' || p[b - 1] == '\t')) b--;
  size_t slen = strlen(s);
  if (b - a != slen) return 0;
  for (size_t i = 0; i < slen; i++) {
    if (p[a + i] != (uint8_t)s[i]) return 0;
  }
  return 1;
}

static int parse_group_code(const uint8_t *p, size_t len, int *code) {
  size_t i = 0;
  while (i < len && (p[i] == ' ' || p[i] == '\t')) i++;
  if (i >= len) return 0;
  int sign = 1;
  if (p[i] == '+') {
    i++;
  } else if (p[i] == '-') {
    sign = -1;
    i++;
  }
  if (i >= len || p[i] < '0' || p[i] > '9') return 0;
  int val = 0;
  int digits = 0;
  while (i < len && p[i] >= '0' && p[i] <= '9') {
    if (digits < 9) val = val * 10 + (int)(p[i] - '0');
    digits++;
    i++;
  }
  while (i < len && (p[i] == ' ' || p[i] == '\t')) i++;
  if (i != len || digits == 0) return 0;
  *code = sign * val;
  return 1;
}

typedef struct {
  size_t code_start;
  size_t code_len;
  size_t code_eol;
  size_t value_start;
  size_t value_len;
  size_t value_eol;
  size_t next_pos;
  int code;
} DxfPair;

static int next_pair(const uint8_t *Data, size_t Size, size_t pos, DxfPair *pair) {
  size_t cs, cl, cn, ce;
  if (!next_line(Data, Size, pos, &cs, &cl, &cn, &ce)) return 0;
  pair->code_start = cs;
  pair->code_len = cl;
  pair->code_eol = ce;
  if (cn >= Size) return 0;
  size_t vs, vl, vn, ve;
  if (!next_line(Data, Size, cn, &vs, &vl, &vn, &ve)) return 0;
  pair->value_start = vs;
  pair->value_len = vl;
  pair->value_eol = ve;
  pair->next_pos = vn;
  if (!parse_group_code(Data + cs, cl, &pair->code)) return 0;
  return 1;
}

static int find_objects_section(const uint8_t *Data, size_t Size, size_t *content_start) {
  size_t pos = 0;
  DxfPair pair;
  while (pos < Size) {
    if (next_pair(Data, Size, pos, &pair)) {
      if (pair.code == 2 && line_equals_trim(Data + pair.value_start, pair.value_len, "OBJECTS")) {
        *content_start = pair.next_pos;
        return 1;
      }
      pos = pair.next_pos;
    } else {
      size_t ls, ll, np, eol;
      if (!next_line(Data, Size, pos, &ls, &ll, &np, &eol)) break;
      pos = np;
    }
  }
  pos = 0;
  while (pos < Size) {
    size_t ls, ll, np, eol;
    if (!next_line(Data, Size, pos, &ls, &ll, &np, &eol)) break;
    if (line_equals_trim(Data + ls, ll, "OBJECTS")) {
      *content_start = np;
      return 1;
    }
    pos = np;
  }
  return 0;
}

static int find_eof_record(const uint8_t *Data, size_t Size, size_t *eof_pos) {
  size_t pos = 0;
  DxfPair pair;
  while (pos < Size) {
    if (next_pair(Data, Size, pos, &pair)) {
      if (pair.code == 0 && line_equals_trim(Data + pair.value_start, pair.value_len, "EOF")) {
        *eof_pos = pair.code_start;
        return 1;
      }
      pos = pair.next_pos;
    } else {
      size_t ls, ll, np, eol;
      if (!next_line(Data, Size, pos, &ls, &ll, &np, &eol)) break;
      pos = np;
    }
  }
  return 0;
}

static int is_special_name(const uint8_t *Data, size_t start, size_t len) {
  return line_equals_trim(Data + start, len, "ENDSEC") ||
         line_equals_trim(Data + start, len, "SECTION") ||
         line_equals_trim(Data + start, len, "EOF");
}

static unsigned long count_candidates(const uint8_t *Data, size_t Size, size_t content_start) {
  unsigned long count = 0;
  size_t pos = content_start;
  while (pos < Size) {
    DxfPair pair;
    if (next_pair(Data, Size, pos, &pair)) {
      if (pair.code == 0) {
        if (line_equals_trim(Data + pair.value_start, pair.value_len, "ENDSEC")) break;
        if (!is_special_name(Data, pair.value_start, pair.value_len)) count++;
      }
      pos = pair.next_pos;
    } else {
      size_t ls, ll, np, eol;
      if (!next_line(Data, Size, pos, &ls, &ll, &np, &eol)) break;
      pos = np;
    }
  }
  return count;
}

static int find_candidate(const uint8_t *Data, size_t Size, size_t content_start,
                          unsigned long k, size_t *value_start,
                          size_t *value_len, size_t *value_eol) {
  unsigned long idx = 0;
  size_t pos = content_start;
  while (pos < Size) {
    DxfPair pair;
    if (next_pair(Data, Size, pos, &pair)) {
      if (pair.code == 0) {
        if (line_equals_trim(Data + pair.value_start, pair.value_len, "ENDSEC")) break;
        if (!is_special_name(Data, pair.value_start, pair.value_len)) {
          if (idx == k) {
            *value_start = pair.value_start;
            *value_len = pair.value_len;
            *value_eol = pair.value_eol;
            return 1;
          }
          idx++;
        }
      }
      pos = pair.next_pos;
    } else {
      size_t ls, ll, np, eol;
      if (!next_line(Data, Size, pos, &ls, &ll, &np, &eol)) break;
      pos = np;
    }
  }
  return 0;
}

static uint32_t rng_next(uint32_t *s) {
  *s ^= *s << 13;
  *s ^= *s >> 17;
  *s ^= *s << 5;
  return *s;
}

static size_t make_random_name(uint8_t *buf, size_t max_len, unsigned Seed,
                               const uint8_t *orig, size_t orig_len) {
  uint32_t s = (uint32_t)Seed;
  if (s == 0) s = 0x9e3779b9u;
  s ^= s >> 16;
  s *= 0x7feb352du;
  s ^= s >> 15;
  s *= 0x846ca68bu;
  s ^= s >> 16;
  size_t len = 1 + (rng_next(&s) % 64u);
  if (len > max_len) len = max_len;
  if (len < 1) len = 1;
  for (size_t i = 0; i < len; i++) {
    uint32_t v = rng_next(&s);
    buf[i] = (uint8_t)ALPHABET[v % ALPHABET_LEN];
  }
  if (len == orig_len && len > 0 && memcmp(buf, orig, len) == 0) {
    char c = (char)buf[0];
    for (size_t i = 0; i < ALPHABET_LEN; i++) {
      if (ALPHABET[i] != c) {
        buf[0] = (uint8_t)ALPHABET[i];
        break;
      }
    }
  }
  return len;
}

static size_t replace_value_line(uint8_t *Data, size_t Size, size_t MaxSize,
                                 size_t value_start, size_t value_len,
                                 size_t value_eol, unsigned Seed) {
  uint8_t name[64];
  size_t name_len = make_random_name(name, sizeof(name), Seed,
                                     Data + value_start, value_len);
  size_t old_total = value_len + value_eol;
  if (value_start + old_total > Size) return Size;
  size_t overhead = Size - old_total;
  if (MaxSize < overhead + value_eol + 1) return Size;
  size_t max_new_len = MaxSize - overhead - value_eol;
  if (max_new_len > 64) max_new_len = 64;
  if (max_new_len < 1) return Size;
  if (name_len > max_new_len) name_len = max_new_len;
  if (name_len == value_len && name_len > 0 &&
      memcmp(name, Data + value_start, name_len) == 0) {
    char c = (char)name[0];
    for (size_t i = 0; i < ALPHABET_LEN; i++) {
      if (ALPHABET[i] != c) {
        name[0] = (uint8_t)ALPHABET[i];
        break;
      }
    }
  }
  uint8_t eol[2];
  for (size_t i = 0; i < value_eol; i++) {
    eol[i] = Data[value_start + value_len + i];
  }
  size_t new_total = name_len + value_eol;
  if (new_total > old_total) {
    size_t diff = new_total - old_total;
    if (Size + diff > MaxSize) return Size;
    memmove(Data + value_start + new_total,
            Data + value_start + old_total,
            Size - (value_start + old_total));
  } else if (new_total < old_total) {
    memmove(Data + value_start + new_total,
            Data + value_start + old_total,
            Size - (value_start + old_total));
  }
  memcpy(Data + value_start, name, name_len);
  for (size_t i = 0; i < value_eol; i++) {
    Data[value_start + name_len + i] = eol[i];
  }
  return Size - old_total + new_total;
}

static size_t construct_objects_section(uint8_t *Data, size_t Size,
                                        size_t MaxSize, unsigned Seed) {
  size_t eof_pos = 0;
  int has_eof = find_eof_record(Data, Size, &eof_pos);
  size_t insert_pos = has_eof ? eof_pos : Size;
  int need_prefix = 0;
  if (!has_eof && Size > 0) {
    uint8_t last = Data[Size - 1];
    if (last != '\n' && last != '\r') need_prefix = 1;
  }
  uint8_t name[64];
  size_t name_len = make_random_name(name, sizeof(name), Seed, NULL, 0);
  size_t fixed = 48u + (need_prefix ? 2u : 0u);
  if (Size > MaxSize) return Size;
  size_t available = MaxSize - Size;
  if (available <= fixed) return Size;
  size_t max_name = available - fixed;
  if (max_name > 64) max_name = 64;
  if (max_name < 1) return Size;
  if (name_len > max_name) name_len = max_name;
  uint8_t seq[128];
  size_t n = 0;
  if (need_prefix) {
    seq[n++] = '\r';
    seq[n++] = '\n';
  }
  const char *parts[] = {
    "  0\r\n",
    "SECTION\r\n",
    "  2\r\n",
    "OBJECTS\r\n",
    "  0\r\n"
  };
  for (size_t i = 0; i < sizeof(parts) / sizeof(parts[0]); i++) {
    const char *p = parts[i];
    while (*p) seq[n++] = (uint8_t)*p++;
  }
  memcpy(seq + n, name, name_len);
  n += name_len;
  seq[n++] = '\r';
  seq[n++] = '\n';
  const char *tail[] = {
    "  0\r\n",
    "ENDSEC\r\n"
  };
  for (size_t i = 0; i < sizeof(tail) / sizeof(tail[0]); i++) {
    const char *p = tail[i];
    while (*p) seq[n++] = (uint8_t)*p++;
  }
  if (n > MaxSize - Size) return Size;
  if (insert_pos > Size) insert_pos = Size;
  if (insert_pos < Size) {
    memmove(Data + insert_pos + n, Data + insert_pos, Size - insert_pos);
  }
  memcpy(Data + insert_pos, seq, n);
  return Size + n;
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  size_t content_start = 0;
  if (find_objects_section(Data, Size, &content_start)) {
    unsigned long count = count_candidates(Data, Size, content_start);
    if (count == 0) return Size;
    unsigned long k = (unsigned long)Seed % count;
    size_t vs = 0, vl = 0, ve = 0;
    if (find_candidate(Data, Size, content_start, k, &vs, &vl, &ve)) {
      return replace_value_line(Data, Size, MaxSize, vs, vl, ve, Seed);
    }
    return Size;
  }
  return construct_objects_section(Data, Size, MaxSize, Seed);
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  if (MaxSize == 0) return 0;
  int is_dwg = (Size >= 2 && Data[0] == 'A' && Data[1] == 'C');
  int is_json = (Size >= 1 && Data[0] == '{');
  if (is_dwg || is_json) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  unsigned r = Seed % 1000u;
  if (r < 500u) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  return mutate_a001(Data, Size, MaxSize, Seed);
}
