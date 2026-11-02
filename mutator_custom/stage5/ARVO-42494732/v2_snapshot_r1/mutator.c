#include <stdint.h>
#include <stddef.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

static uint64_t pm003_rng_next(uint64_t *s) {
  uint64_t x = *s;
  x ^= x << 13;
  x ^= x >> 7;
  x ^= x << 17;
  if (x == 0) x = 1;
  *s = x;
  return x;
}

static int pm003_get_line(const uint8_t *Data, size_t Size, size_t pos,
                          size_t *start, size_t *end, size_t *next, size_t *eol_len) {
  if (pos >= Size) return 0;
  *start = pos;
  size_t i = pos;
  while (i < Size && Data[i] != 13 && Data[i] != 10) i++;
  *end = i;
  if (i >= Size) {
    *next = Size;
    if (eol_len) *eol_len = 0;
    return 1;
  }
  if (Data[i] == 13) {
    if (i + 1 < Size && Data[i + 1] == 10) {
      *next = i + 2;
      if (eol_len) *eol_len = 2;
    } else {
      *next = i + 1;
      if (eol_len) *eol_len = 1;
    }
  } else {
    *next = i + 1;
    if (eol_len) *eol_len = 1;
  }
  return 1;
}

static int pm003_parse_code(const uint8_t *p, size_t n, int *out) {
  size_t i = 0;
  while (i < n && (p[i] == 32 || p[i] == 9)) i++;
  size_t start = i;
  int v = 0;
  int digits = 0;
  while (i < n && p[i] >= 48 && p[i] <= 57 && digits < 3) {
    v = v * 10 + (int)(p[i] - 48);
    i++;
    digits++;
  }
  if (digits == 0) return 0;
  if (i == start) return 0;
  while (i < n && (p[i] == 32 || p[i] == 9)) i++;
  if (i != n) return 0;
  *out = v;
  return 1;
}

static int pm003_trim_eq(const uint8_t *p, size_t n, const char *s) {
  while (n > 0 && (p[0] == 32 || p[0] == 9)) {
    p++;
    n--;
  }
  while (n > 0 && (p[n - 1] == 32 || p[n - 1] == 9)) n--;
  size_t m = strlen(s);
  if (n != m) return 0;
  for (size_t i = 0; i < m; i++) {
    if (p[i] != (uint8_t)s[i]) return 0;
  }
  return 1;
}

static int pm003_find_objects_start(const uint8_t *Data, size_t Size, size_t *out_start) {
  size_t pos = 0;
  while (pos < Size) {
    size_t cs, ce, cn, ceol;
    if (!pm003_get_line(Data, Size, pos, &cs, &ce, &cn, &ceol)) break;
    int code = 0;
    if (pm003_parse_code(Data + cs, ce - cs, &code) && code == 2) {
      size_t vs, ve, vn, veol;
      if (pm003_get_line(Data, Size, cn, &vs, &ve, &vn, &veol)) {
        if (pm003_trim_eq(Data + vs, ve - vs, "OBJECTS")) {
          *out_start = vn;
          return 1;
        }
      }
    }
    pos = cn;
  }
  return 0;
}

static size_t pm003_scan_candidates(const uint8_t *Data, size_t Size, size_t start,
                                    long select_index,
                                    size_t *out_value_start, size_t *out_value_end) {
  size_t pos = start;
  size_t count = 0;
  while (pos < Size) {
    size_t cs, ce, cn, ceol;
    if (!pm003_get_line(Data, Size, pos, &cs, &ce, &cn, &ceol)) break;
    int code = 0;
    if (!pm003_parse_code(Data + cs, ce - cs, &code)) {
      pos = cn;
      continue;
    }
    size_t vs, ve, vn, veol;
    if (!pm003_get_line(Data, Size, cn, &vs, &ve, &vn, &veol)) break;
    if (code == 0) {
      if (pm003_trim_eq(Data + vs, ve - vs, "ENDSEC")) {
        break;
      }
      if (select_index >= 0 && (size_t)select_index == count) {
        if (out_value_start) *out_value_start = vs;
        if (out_value_end) *out_value_end = ve;
      }
      count++;
    }
    pos = vn;
  }
  return count;
}

static size_t pm003_mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  size_t section_start = 0;
  if (!pm003_find_objects_start(Data, Size, &section_start)) return Size;
  size_t total = pm003_scan_candidates(Data, Size, section_start, -1, NULL, NULL);
  if (total == 0) return Size;

  uint64_t rng = ((uint64_t)Seed * 0x9E3779B97F4A7C15ULL) ^ 0xD1B54A32D192ED03ULL;
  if (rng == 0) rng = 1;
  size_t pick = (size_t)(pm003_rng_next(&rng) % total);

  size_t value_start = 0, value_end = 0;
  size_t got = pm003_scan_candidates(Data, Size, section_start, (long)pick, &value_start, &value_end);
  if (got <= pick) return Size;
  size_t old_len = value_end - value_start;

  static const char alphabet[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-";
  const size_t alphabet_len = sizeof(alphabet) - 1;
  char new_value[64];

  size_t new_len = 0;
  int same = 1;
  for (int attempt = 0; attempt < 12; attempt++) {
    uint64_t r = pm003_rng_next(&rng);
    new_len = 1 + (size_t)(r % 64);
    for (size_t i = 0; i < new_len; i++) {
      new_value[i] = alphabet[pm003_rng_next(&rng) % alphabet_len];
    }
    same = 0;
    if (new_len == old_len) {
      same = 1;
      for (size_t i = 0; i < new_len; i++) {
        if ((uint8_t)new_value[i] != Data[value_start + i]) {
          same = 0;
          break;
        }
      }
    }
    if (!same) break;
  }
  if (same) {
    if (new_len == old_len && new_len > 0) {
      if (Data[value_start] == (uint8_t)'A') {
        new_value[0] = 'B';
      } else {
        new_value[0] = 'A';
      }
    }
  }

  if (new_len > old_len) {
    size_t delta = new_len - old_len;
    if (delta > MaxSize - Size) return Size;
    memmove(Data + value_end + delta, Data + value_end, Size - value_end);
    memcpy(Data + value_start, new_value, new_len);
    return Size + delta;
  } else if (new_len < old_len) {
    size_t shrink = old_len - new_len;
    memmove(Data + value_start + new_len, Data + value_end, Size - value_end);
    memcpy(Data + value_start, new_value, new_len);
    return Size - shrink;
  } else {
    memcpy(Data + value_start, new_value, new_len);
    return Size;
  }
}

size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
  if (Size >= 1 && Data[0] == (uint8_t)'{') {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  if (Size >= 2 && Data[0] == (uint8_t)'A' && Data[1] == (uint8_t)'C') {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }

  unsigned r = Seed % 1000;
  if (r < 500) {
    return LLVMFuzzerMutate(Data, Size, MaxSize);
  }
  return pm003_mutate_a001(Data, Size, MaxSize, Seed);
}
