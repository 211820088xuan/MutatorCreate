#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

typedef struct {
  size_t start;
  size_t content_end;
  size_t next;
  size_t eol_len;
  int has_eol;
} Line;

static int ascii_space(uint8_t c) {
  return c == 32 || c == 9 || c == 13 || c == 10 || c == 11 || c == 12;
}

static int get_line(const uint8_t *Data, size_t Size, size_t pos, Line *ln) {
  if (pos >= Size) return 0;
  size_t i = pos;
  while (i < Size && Data[i] != 10 && Data[i] != 13) i++;
  ln->start = pos;
  ln->content_end = i;
  if (i < Size) {
    if (Data[i] == 13) {
      if (i + 1 < Size && Data[i + 1] == 10) {
        ln->eol_len = 2;
        ln->next = i + 2;
      } else {
        ln->eol_len = 1;
        ln->next = i + 1;
      }
    } else {
      ln->eol_len = 1;
      ln->next = i + 1;
    }
    ln->has_eol = 1;
  } else {
    ln->eol_len = 0;
    ln->next = Size;
    ln->has_eol = 0;
  }
  return 1;
}

static int parse_group_code(const uint8_t *Data, const Line *ln) {
  size_t i = ln->start;
  size_t end = ln->content_end;
  while (i < end && ascii_space(Data[i])) i++;
  if (i >= end) return -1;
  if (Data[i] < 48 || Data[i] > 57) return -1;
  long val = 0;
  int nd = 0;
  while (i < end && Data[i] >= 48 && Data[i] <= 57) {
    val = val * 10 + (Data[i] - 48);
    if (val > 1000000L) return -1;
    i++;
    nd++;
  }
  if (nd == 0) return -1;
  while (i < end && ascii_space(Data[i])) i++;
  if (i != end) return -1;
  return (int)val;
}

static int value_equals_ci(const uint8_t *Data, const Line *ln, const char *s) {
  size_t a = ln->start;
  size_t b = ln->content_end;
  while (a < b && ascii_space(Data[a])) a++;
  while (b > a && ascii_space(Data[b - 1])) b--;
  size_t len = b - a;
  size_t slen = strlen(s);
  if (len != slen) return 0;
  for (size_t i = 0; i < len; i++) {
    uint8_t ca = Data[a + i];
    uint8_t cb = (uint8_t)s[i];
    if (ca >= 65 && ca <= 90) ca = (uint8_t)(ca - 65 + 97);
    if (cb >= 65 && cb <= 90) cb = (uint8_t)(cb - 65 + 97);
    if (ca != cb) return 0;
  }
  return 1;
}

static int name_equals_ci(const uint8_t *name, size_t len, const char *s) {
  size_t slen = strlen(s);
  if (len != slen) return 0;
  for (size_t i = 0; i < len; i++) {
    uint8_t ca = name[i];
    uint8_t cb = (uint8_t)s[i];
    if (ca >= 65 && ca <= 90) ca = (uint8_t)(ca - 65 + 97);
    if (cb >= 65 && cb <= 90) cb = (uint8_t)(cb - 65 + 97);
    if (ca != cb) return 0;
  }
  return 1;
}

static int name_is_reserved(const uint8_t *name, size_t len) {
  return name_equals_ci(name, len, "ENDSEC") ||
         name_equals_ci(name, len, "EOF") ||
         name_equals_ci(name, len, "SECTION") ||
         name_equals_ci(name, len, "OBJECTS");
}

static uint64_t rng_next(uint64_t *s) {
  uint64_t x = *s;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  *s = x;
  return x;
}

static uint64_t init_rng(unsigned int seed) {
  uint64_t s = (uint64_t)seed + 0x9e3779b97f4a7c15ULL;
  if (s == 0) s = 0x123456789abcdef0ULL;
  return s;
}

static size_t gen_random_name(uint64_t *rng, uint8_t *out, size_t cap, const uint8_t *orig, size_t orig_len) {
  static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  const size_t alpha_len = sizeof(alphabet) - 1;
  if (cap == 0) return 0;
  if (cap > 64) cap = 64;
  size_t max_len = cap;
  if (max_len == 0) return 0;
  uint8_t tmp[64];
  size_t len = 0;
  for (int attempt = 0; attempt < 8; attempt++) {
    len = 1 + (size_t)(rng_next(rng) % max_len);
    for (size_t i = 0; i < len; i++) {
      tmp[i] = (uint8_t)alphabet[rng_next(rng) % alpha_len];
    }
    int bad = 0;
    if (name_is_reserved(tmp, len)) bad = 1;
    if (!bad && orig != NULL && len == orig_len && memcmp(tmp, orig, len) == 0) bad = 1;
    if (!bad) {
      memcpy(out, tmp, len);
      return len;
    }
  }
  if (len == 0) {
    len = 1;
    tmp[0] = 65;
  }
  for (size_t i = 0; i < alpha_len; i++) {
    tmp[0] = (uint8_t)alphabet[i];
    int bad = 0;
    if (name_is_reserved(tmp, len)) bad = 1;
    if (!bad && orig != NULL && len == orig_len && memcmp(tmp, orig, len) == 0) bad = 1;
    if (!bad) {
      memcpy(out, tmp, len);
      return len;
    }
  }
  len = 1;
  out[0] = 65;
  if (orig != NULL && orig_len == 1 && orig[0] == 65) out[0] = 66;
  return len;
}

static int is_candidate_value(const uint8_t *Data, const Line *vl) {
  if (value_equals_ci(Data, vl, "ENDSEC")) return 0;
  if (value_equals_ci(Data, vl, "EOF")) return 0;
  if (value_equals_ci(Data, vl, "SECTION")) return 0;
  return 1;
}

static int find_objects_section(const uint8_t *Data, size_t Size, size_t *out_start, size_t *out_end) {
  size_t pos = 0;
  while (pos < Size) {
    Line cl;
    if (!get_line(Data, Size, pos, &cl)) break;
    int code = parse_group_code(Data, &cl);
    if (code < 0) {
      if (cl.next <= pos) break;
      pos = cl.next;
      continue;
    }
    if (cl.next >= Size) break;
    Line vl;
    if (!get_line(Data, Size, cl.next, &vl)) break;
    if (code == 2 && value_equals_ci(Data, &vl, "OBJECTS")) {
      size_t sec_start = vl.next;
      size_t p = sec_start;
      size_t sec_end = Size;
      while (p < Size) {
        Line c2;
        if (!get_line(Data, Size, p, &c2)) break;
        int c = parse_group_code(Data, &c2);
        if (c < 0) {
          if (c2.next <= p) break;
          p = c2.next;
          continue;
        }
        if (c2.next >= Size) break;
        Line v2;
        if (!get_line(Data, Size, c2.next, &v2)) break;
        if (c == 0 && value_equals_ci(Data, &v2, "ENDSEC")) {
          sec_end = v2.start;
          break;
        }
        if (v2.next <= p) break;
        p = v2.next;
      }
      *out_start = sec_start;
      *out_end = sec_end;
      return 1;
    }
    if (vl.next <= pos) break;
    pos = vl.next;
  }
  return 0;
}

static int count_code0_candidates(const uint8_t *Data, size_t Size, size_t start, size_t end, size_t *out_count) {
  size_t pos = start;
  size_t cnt = 0;
  while (pos < Size && pos < end) {
    Line cl;
    if (!get_line(Data, Size, pos, &cl)) break;
    if (cl.start >= end) break;
    int code = parse_group_code(Data, &cl);
    if (code < 0) {
      if (cl.next <= pos) break;
      pos = cl.next;
      continue;
    }
    if (cl.next >= Size) break;
    Line vl;
    if (!get_line(Data, Size, cl.next, &vl)) break;
    if (vl.start >= end) break;
    if (code == 0 && is_candidate_value(Data, &vl)) cnt++;
    if (vl.next <= pos) break;
    pos = vl.next;
  }
  *out_count = cnt;
  return 1;
}

static int replace_kth_code0(uint8_t *Data, size_t Size, size_t MaxSize, uint64_t *rng, size_t start, size_t end, size_t k, size_t *out_size) {
  size_t pos = start;
  size_t idx = 0;
  while (pos < Size && pos < end) {
    Line cl;
    if (!get_line(Data, Size, pos, &cl)) break;
    if (cl.start >= end) break;
    int code = parse_group_code(Data, &cl);
    if (code < 0) {
      if (cl.next <= pos) break;
      pos = cl.next;
      continue;
    }
    if (cl.next >= Size) break;
    Line vl;
    if (!get_line(Data, Size, cl.next, &vl)) break;
    if (vl.start >= end) break;
    if (code == 0 && is_candidate_value(Data, &vl)) {
      if (idx == k) {
        size_t old_len = vl.content_end - vl.start;
        if (old_len > Size) return 0;
        size_t base_size = Size - old_len;
        if (base_size > MaxSize) return 0;
        size_t available = MaxSize - base_size;
        if (available == 0) return 0;
        size_t cap = available > 64 ? 64 : available;
        uint8_t name[64];
        size_t name_len = gen_random_name(rng, name, cap, Data + vl.start, old_len);
        if (name_len == 0) return 0;
        size_t new_size = base_size + name_len;
        if (new_size > MaxSize) return 0;
        memmove(Data + vl.start + name_len, Data + vl.content_end, Size - vl.content_end);
        memcpy(Data + vl.start, name, name_len);
        *out_size = new_size;
        return 1;
      }
      idx++;
    }
    if (vl.next <= pos) break;
    pos = vl.next;
  }
  return 0;
}

static const uint8_t EOL_CRLF[2] = {13, 10};
static const uint8_t EOL_LF[1] = {10};
static const uint8_t EOL_CR[1] = {13};

static void detect_line_ending(const uint8_t *Data, size_t Size, const uint8_t **eol, size_t *eol_len) {
  for (size_t i = 0; i + 1 < Size; i++) {
    if (Data[i] == 13 && Data[i + 1] == 10) {
      *eol = EOL_CRLF;
      *eol_len = 2;
      return;
    }
  }
  for (size_t i = 0; i < Size; i++) {
    if (Data[i] == 10) {
      *eol = EOL_LF;
      *eol_len = 1;
      return;
    }
  }
  for (size_t i = 0; i < Size; i++) {
    if (Data[i] == 13) {
      *eol = EOL_CR;
      *eol_len = 1;
      return;
    }
  }
  *eol = EOL_CRLF;
  *eol_len = 2;
}

static int construct_objects_section(uint8_t *Data, size_t Size, size_t MaxSize, uint64_t *rng, size_t *out_size) {
  size_t insert_pos = Size;
  size_t pos = 0;
  while (pos < Size) {
    Line cl;
    if (!get_line(Data, Size, pos, &cl)) break;
    int code = parse_group_code(Data, &cl);
    if (code < 0) {
      if (cl.next <= pos) break;
      pos = cl.next;
      continue;
    }
    if (cl.next >= Size) break;
    Line vl;
    if (!get_line(Data, Size, cl.next, &vl)) break;
    if (code == 0 && value_equals_ci(Data, &vl, "EOF")) {
      insert_pos = cl.start;
      break;
    }
    if (vl.next <= pos) break;
    pos = vl.next;
  }

  uint8_t name[64];
  size_t name_len = gen_random_name(rng, name, 64, NULL, 0);
  if (name_len == 0) return 0;

  const uint8_t *eol = NULL;
  size_t eol_len = 0;
  detect_line_ending(Data, Size, &eol, &eol_len);

  size_t prefix = 0;
  if (insert_pos == Size && Size > 0 && Data[Size - 1] != 10 && Data[Size - 1] != 13) {
    prefix = eol_len;
  }

  size_t need = prefix;
  need += 1 + eol_len;
  need += 7 + eol_len;
  need += 1 + eol_len;
  need += 7 + eol_len;
  need += 1 + eol_len;
  need += name_len + eol_len;
  need += 1 + eol_len;
  need += 6 + eol_len;

  if (Size + need > MaxSize) return 0;

  memmove(Data + insert_pos + need, Data + insert_pos, Size - insert_pos);
  uint8_t *p = Data + insert_pos;

  if (prefix) {
    memcpy(p, eol, eol_len);
    p += eol_len;
  }

  *p++ = 48;
  memcpy(p, eol, eol_len);
  p += eol_len;
  memcpy(p, "SECTION", 7);
  p += 7;
  memcpy(p, eol, eol_len);
  p += eol_len;
  *p++ = 50;
  memcpy(p, eol, eol_len);
  p += eol_len;
  memcpy(p, "OBJECTS", 7);
  p += 7;
  memcpy(p, eol, eol_len);
  p += eol_len;
  *p++ = 48;
  memcpy(p, eol, eol_len);
  p += eol_len;
  memcpy(p, name, name_len);
  p += name_len;
  memcpy(p, eol, eol_len);
  p += eol_len;
  *p++ = 48;
  memcpy(p, eol, eol_len);
  p += eol_len;
  memcpy(p, "ENDSEC", 6);
  p += 6;
  memcpy(p, eol, eol_len);
  p += eol_len;

  *out_size = Size + need;
  return 1;
}

static size_t mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  uint64_t rng = init_rng(Seed);
  size_t sec_start = 0, sec_end = 0;
  if (find_objects_section(Data, Size, &sec_start, &sec_end)) {
    size_t count = 0;
    if (count_code0_candidates(Data, Size, sec_start, sec_end, &count) && count > 0) {
      size_t k = (size_t)(rng_next(&rng) % count);
      size_t new_size = Size;
      if (replace_kth_code0(Data, Size, MaxSize, &rng, sec_start, sec_end, k, &new_size)) {
        return new_size;
      }
    }
    return Size;
  } else {
    size_t new_size = Size;
    if (construct_objects_section(Data, Size, MaxSize, &rng, &new_size)) {
      return new_size;
    }
    return Size;
  }
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  if (Size >= 2 && Data[0] == 65 && Data[1] == 67) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  if (Size >= 1 && Data[0] == 123) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }

  unsigned r = Seed % 1000;
  if (r < 500) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  return mutate_a001(Data, Size, MaxSize, Seed);
}
