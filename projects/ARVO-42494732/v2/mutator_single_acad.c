#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

static uint64_t a001_rng_next(uint64_t *s) {
  uint64_t x = *s;
  if (x == 0) x = 0x9e3779b97f4a7c15ULL;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  *s = x;
  return x;
}

static int a001_is_ws(uint8_t c) {
  return c == ' ' || c == '\t' || c == '\v' || c == '\f';
}

static int a001_line_parse_code(const uint8_t *buf, size_t start, size_t end, int *out) {
  size_t p = start;
  int val = 0;
  int digits = 0;
  while (p < end && a001_is_ws(buf[p])) p++;
  while (p < end && buf[p] >= '0' && buf[p] <= '9') {
    val = val * 10 + (int)(buf[p] - '0');
    p++;
    digits++;
    if (digits > 5) return 0;
  }
  if (digits == 0) return 0;
  while (p < end && a001_is_ws(buf[p])) p++;
  if (p != end) return 0;
  *out = val;
  return 1;
}

static int a001_line_eq_trim(const uint8_t *buf, size_t start, size_t end, const char *s) {
  size_t n = strlen(s);
  while (start < end && a001_is_ws(buf[start])) start++;
  while (end > start && a001_is_ws(buf[end - 1])) end--;
  if (end - start != n) return 0;
  for (size_t i = 0; i < n; i++) {
    if (buf[start + i] != (uint8_t)s[i]) return 0;
  }
  return 1;
}

static int a001_next_line(const uint8_t *buf, size_t size, size_t pos,
                          size_t *line_start, size_t *line_end, size_t *next_pos) {
  if (pos >= size) return 0;
  size_t p = pos;
  while (p < size && buf[p] != '\r' && buf[p] != '\n') p++;
  *line_start = pos;
  *line_end = p;
  if (p < size) {
    if (buf[p] == '\r') {
      p++;
      if (p < size && buf[p] == '\n') p++;
    } else if (buf[p] == '\n') {
      p++;
    }
  }
  *next_pos = p;
  return 1;
}

static size_t a001_make_random_name(uint8_t *out, size_t max_len, uint64_t *rng,
                                    const uint8_t *orig, size_t orig_len) {
  static const char alphabet[] =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  const size_t alpha_len = sizeof(alphabet) - 1;
  if (max_len == 0) return 0;
  size_t lim = max_len;
  if (lim > 64) lim = 64;
  if (lim == 0) return 0;
  size_t n = 1 + (size_t)(a001_rng_next(rng) % lim);
  int attempts = 0;
  do {
    for (size_t i = 0; i < n; i++) {
      out[i] = (uint8_t)alphabet[a001_rng_next(rng) % alpha_len];
    }
    attempts++;
  } while (orig_len == n && memcmp(out, orig, n) == 0 && attempts < 8);
  if (orig_len == n && memcmp(out, orig, n) == 0) {
    uint8_t first = out[0];
    for (size_t i = 0; i < alpha_len; i++) {
      if ((uint8_t)alphabet[i] != first) {
        out[0] = (uint8_t)alphabet[i];
        break;
      }
    }
  }
  return n;
}

static size_t a001_mutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  if (MaxSize == 0) return 0;
  uint64_t rng = (uint64_t)Seed * 0x9e3779b97f4a7c15ULL + 0x123456789abcdefULL;
  if (rng == 0) rng = 1;

  size_t pos = 0;
  int expect_section_name = 0;
  int in_objects = 0;
  int section_exists = 0;
  size_t code0_count = 0;

  while (pos < Size) {
    size_t code_start, code_end, code_next;
    if (!a001_next_line(Data, Size, pos, &code_start, &code_end, &code_next)) break;
    int code;
    if (!a001_line_parse_code(Data, code_start, code_end, &code)) {
      pos = code_next;
      continue;
    }
    size_t val_start, val_end, val_next;
    if (!a001_next_line(Data, Size, code_next, &val_start, &val_end, &val_next)) break;

    if (expect_section_name) {
      if (code == 2 && a001_line_eq_trim(Data, val_start, val_end, "OBJECTS")) {
        in_objects = 1;
        section_exists = 1;
      }
      expect_section_name = 0;
    }

    if (code == 0) {
      if (a001_line_eq_trim(Data, val_start, val_end, "SECTION")) {
        expect_section_name = 1;
      } else if (a001_line_eq_trim(Data, val_start, val_end, "ENDSEC")) {
        if (in_objects) in_objects = 0;
      } else if (in_objects) {
        code0_count++;
      }
    }
    pos = val_next;
  }

  if (section_exists) {
    if (code0_count == 0) {
      return LLVMFuzzerMutate(Data, Size, MaxSize);
    }

    uint64_t pick = a001_rng_next(&rng);
    size_t k = (size_t)(pick % (uint64_t)code0_count);

    pos = 0;
    expect_section_name = 0;
    in_objects = 0;
    size_t idx = 0;
    int found = 0;
    size_t target_start = 0, target_end = 0;

    while (pos < Size) {
      size_t code_start, code_end, code_next;
      if (!a001_next_line(Data, Size, pos, &code_start, &code_end, &code_next)) break;
      int code;
      if (!a001_line_parse_code(Data, code_start, code_end, &code)) {
        pos = code_next;
        continue;
      }
      size_t val_start, val_end, val_next;
      if (!a001_next_line(Data, Size, code_next, &val_start, &val_end, &val_next)) break;

      if (expect_section_name) {
        if (code == 2 && a001_line_eq_trim(Data, val_start, val_end, "OBJECTS")) {
          in_objects = 1;
        }
        expect_section_name = 0;
      }

      if (code == 0) {
        if (a001_line_eq_trim(Data, val_start, val_end, "SECTION")) {
          expect_section_name = 1;
        } else if (a001_line_eq_trim(Data, val_start, val_end, "ENDSEC")) {
          if (in_objects) in_objects = 0;
        } else if (in_objects) {
          if (idx == k) {
            target_start = val_start;
            target_end = val_end;
            found = 1;
            break;
          }
          idx++;
        }
      }
      pos = val_next;
    }

    if (!found || target_end < target_start) {
      return Size;
    }

    size_t old_len = target_end - target_start;
    if (old_len > Size || target_start > Size - old_len) return Size;
    if (MaxSize < Size - old_len) return Size;
    size_t room = MaxSize - (Size - old_len);
    if (room == 0) return Size;
    if (room > 64) room = 64;

    uint8_t name[64];
    size_t new_len = a001_make_random_name(name, room, &rng, Data + target_start, old_len);
    if (new_len == 0) return Size;
    if (new_len > MaxSize - (Size - old_len)) return Size;

    if (new_len != old_len) {
      memmove(Data + target_start + new_len,
              Data + target_end,
              Size - target_end);
      Size = Size - old_len + new_len;
    }
    memcpy(Data + target_start, name, new_len);
    return Size;
  }

  /* Section absent: insert 0/SECTION, 2/OBJECTS, 0/<random>, 0/ENDSEC before 0/EOF. */
  static const char p1[] = "0\r\nSECTION\r\n2\r\nOBJECTS\r\n0\r\n";
  static const char p2[] = "\r\n0\r\nENDSEC\r\n";
  size_t p1len = sizeof(p1) - 1;
  size_t p2len = sizeof(p2) - 1;
  size_t spare = (MaxSize >= Size) ? (MaxSize - Size) : 0;
  if (spare < p1len + p2len + 1) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  size_t max_name_len = spare - p1len - p2len;
  if (max_name_len > 64) max_name_len = 64;

  uint8_t name[64];
  size_t name_len = a001_make_random_name(name, max_name_len, &rng, NULL, 0);
  if (name_len == 0) return LLVMFuzzerMutate(Data, Size, MaxSize);
  size_t ins_len = p1len + name_len + p2len;
  if (ins_len > MaxSize - Size) return LLVMFuzzerMutate(Data, Size, MaxSize);

  size_t ins_pos = Size;
  pos = 0;
  while (pos < Size) {
    size_t code_start, code_end, code_next;
    if (!a001_next_line(Data, Size, pos, &code_start, &code_end, &code_next)) break;
    int code;
    if (!a001_line_parse_code(Data, code_start, code_end, &code)) {
      pos = code_next;
      continue;
    }
    size_t val_start, val_end, val_next;
    if (!a001_next_line(Data, Size, code_next, &val_start, &val_end, &val_next)) break;
    if (code == 0 && a001_line_eq_trim(Data, val_start, val_end, "EOF")) {
      ins_pos = code_start;
      break;
    }
    pos = val_next;
  }

  memmove(Data + ins_pos + ins_len, Data + ins_pos, Size - ins_pos);
  memcpy(Data + ins_pos, p1, p1len);
  memcpy(Data + ins_pos + p1len, name, name_len);
  memcpy(Data + ins_pos + p1len + name_len, p2, p2len);
  return Size + ins_len;
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize,
                               unsigned int Seed) {
  if (MaxSize == 0) return 0;

  unsigned r = Seed % 1000u;
  if (r < 500u) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }

  int is_dxf = 1;
  if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C') is_dxf = 0;
  if (Size >= 1 && Data[0] == '{') is_dxf = 0;
  if (!is_dxf) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }

  return a001_mutator(Data, Size, MaxSize, Seed);
}
