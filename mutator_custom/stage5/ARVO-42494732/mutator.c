/* ===========================================================================
 * mutator.c -- libFuzzer custom mutator (C11, single file, libc only)
 *
 * 目标漏洞 : ARVO-42494732 / libredwg / src/in_dxf.c:12267
 *            dxf_objects_read() 内的 heap-use-after-free
 * 接口契约 : design/MUTATOR_CONTRACT.md            (v1，逐条遵守)
 * 落地设计 : design/landing_plan.json              (uaf-llm01 .. uaf-llm05)
 *
 * 崩溃回路（source/in_dxf.c，行号均指该文件）:
 *   12264  pair = dxf_read_pair (dat);
 *   12267  while (pair != NULL && pair->code == 0 && pair->value.s)   <- UAF 读取点
 *   12272  if (is_dwg_object (name)) { ... }
 *   12280  else {
 *   12282    DXF_RETURN_ENDSEC (0);   // 3 个条件都不满足 -> 不返回
 *   12284    dxf_free_pair (pair);    // 只释放，不重新赋值
 *   12285  }
 *          -> 控制流回到 12267，再次读 pair->code / pair->value.s（已释放）
 *
 * 因此 5 个策略共同要造的形状是：OBJECTS 段内出现一个
 *   code == 0 && value.s != NULL && value != "ENDSEC" && 其后仍有字节
 * 的 pair，且它的 value 不是 is_dwg_object() 认得的对象名。
 *
 * ---------------------------------------------------------------------------
 * group code 依据（全部来自 source/in_dxf.c，不猜测；本文件"凭空合成"的只有 0 和 5，
 * 330 / 102 只会在 strat_3 原样复制真实实体字节时随之出现，从不编造）：
 *
 *   0   —— 实体/段分隔标记，value 是字符串。
 *          in_dxf.c:535  pair->code = (short)dxf_read_rs (dat);
 *          in_dxf.c:12267 while (... pair->code == 0 && pair->value.s)
 *          in_dxf.c:12282 DXF_RETURN_ENDSEC 用 strEQc (value, "ENDSEC") 判段尾
 *          in_dxf.c:12305 dxf_unknownsection_read 同样用 code 0 判实体/段尾
 *
 *   5   —— 对象的 handle，值是十六进制字符串。
 *          in_dxf.c:578-584  handle / objectid 类 code 走
 *                            dxf_read_string + sscanf (buf, "%X", &value.u)
 *          in_dxf.c:9076-9095 OBJECTS/对象读取路径的 case 5：
 *                            obj->handle.value = pair->value.u;
 *                            dwg_add_handle (&obj->handle, 0, value.u, obj);
 *                            （不调用 dwg_add_handleref，更不经过 array_push）
 *          注：6283-6292 的 case 5 属于 new_table_control()（函数起于 6192），
 *              不是 OBJECTS 路径，引用时容易张冠李戴。
 *
 *   330 —— owner / reactor 句柄（软指针），值同样是十六进制字符串。
 *          in_dxf.c:9451-9495 case 330: 写 ownerhandle；in_reactors 时
 *                            realloc reactors[] 再追加（容器增长点）
 *          in_dxf.c:6305      符号表路径的 case 330: ownerhandle
 *
 *   102 —— 控制字符串（"{ACAD_REACTORS" / "{ACAD_XDICTIONARY" / "}"）。
 *          in_dxf.c:9391-9405 case 102: 用这几个字面量开/关 in_reactors 等状态
 *
 * ---------------------------------------------------------------------------
 * DXF 真实文本形态（已用 Constraints.dxf / sample_2013.dxf 核对，契约 §8 的
 * "0 / OBJECTS" 只是简写，真实文件是 "0 / SECTION" + "2 / OBJECTS"）：
 *
 *     "  0\r\nSECTION\r\n  2\r\nOBJECTS\r\n  0\r\nDICTIONARY\r\n  5\r\nC\r\n..."
 *
 * 三个必须处理的细节，本文件的行解析全部按此实现：
 *   1) group code 行右对齐、带前导空格（"  0" / " 10" / "  2"），必须跳过前导空白；
 *   2) 行尾是 CRLF（也有纯 LF 的种子），比对 value 前必须剥掉行尾 '\r'；
 *   3) value 也可能带前导空白，比对时两端 trim。
 * 因此绝不用裸 memmem("ENDSEC")：真实文件里它的前一行是 "  0"，不是 "0"。
 *
 * 随机数：只用 Seed 派生的本地 xorshift32（契约 §5），不碰 rand()/random()。
 * 环境变量：全部用 static 缓存，只读一次（契约 §4）。
 * ===========================================================================*/

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

/* 契约 §7（v2 修订）：单次变异插入量 <= 256 字节。
   为什么从 64 放宽：对齐 pair 解析实测 8 个真实种子，OBJECTS 段内最小的
   完整对象块是 83 字节（83/105/115/...），64 字节上限让"整块复制"的 strat_3
   在所有真实种子上 100% 不适用；256 仍 < 输入(12~38KB) 的 2%，变异依旧是局部的。 */
#define MAX_INSERT 256u

/* ===================== 随机数（契约 §5） ===================== */

static uint32_t
rng_next (uint32_t *s)
{
  uint32_t x = *s ? *s : 0x9e3779b9u;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  *s = x;
  return x;
}

/* ===================== 环境变量（契约 §4，static 缓存） ===================== */

typedef struct
{
  int off;            /* LIBREDWG_MUTATOR_OFF=1 -> 100% default          */
  int force;          /* LIBREDWG_FORCE_STRATEGY=k -> k，-1 表示未设置    */
  unsigned pct;       /* LIBREDWG_CUSTOM_PCT，默认 40（default 占 60%）   */
  const char *trace;  /* LIBREDWG_TRACE_FILE，NULL 表示不记录             */
} MutCfg;

static long
env_num (const char *name, long dflt, long lo, long hi)
{
  const char *v = getenv (name);
  char *end = NULL;
  long x;
  if (!v || !*v)
    return dflt;
  x = strtol (v, &end, 10);
  if (end == v)
    return dflt;
  if (x < lo)
    x = lo;
  if (x > hi)
    x = hi;
  return x;
}

static const MutCfg *
cfg_get (void)
{
  static MutCfg c;
  static int init = 0;
  if (!init)
    {
      const char *v;
      init = 1;
      c.off = (int)env_num ("LIBREDWG_MUTATOR_OFF", 0, 0, 1);
      c.pct = (unsigned)env_num ("LIBREDWG_CUSTOM_PCT", 40, 0, 100);
      c.force = -1;
      v = getenv ("LIBREDWG_FORCE_STRATEGY");
      if (v && *v)
        {
          char *end = NULL;
          long x = strtol (v, &end, 10);
          if (end != v && x >= 0 && x <= 4)
            c.force = (int)x;
        }
      v = getenv ("LIBREDWG_TRACE_FILE");
      c.trace = (v && *v) ? v : NULL;
    }
  return &c;
}

/* trace 标记：D / S<k> / F<k>（契约 §4）。每次调用追加一行。 */
static void
trace_tag (const MutCfg *c, char tag, int k)
{
  FILE *f;
  if (!c->trace)
    return;
  f = fopen (c->trace, "a");
  if (!f)
    return;
  if (k < 0)
    {
      fputc ('D', f);
      fputc ('\n', f);
    }
  else
    {
      fprintf (f, "%c%d\n", tag, k);
    }
  fclose (f);
}

/* ===================== 行解析（CRLF / 前导空格） ===================== */

/* 取出从 pos 开始的一行：[*ls, *le) 不含行尾 \r\n，*lnext 为下一行起点。
   返回 0 表示 pos 已到缓冲区末尾。不假定输入以 '\0' 结尾。 */
static int
line_next (const uint8_t *d, size_t n, size_t pos, size_t *ls, size_t *le,
           size_t *lnext)
{
  size_t i;
  if (pos >= n)
    return 0;
  i = pos;
  while (i < n && d[i] != '\n')
    i++;
  *ls = pos;
  *le = (i > pos && d[i - 1] == '\r') ? i - 1 : i; /* 剥掉 CRLF 的 '\r' */
  *lnext = (i < n) ? i + 1 : n;
  return 1;
}

/* 该行是否为 group code 行：跳过前导空格/制表符后，1..5 位十进制数字，其余为空。
   返回 >=0 的 code；不是 group code 行返回 -1。 */
static int
code_of_line (const uint8_t *d, size_t ls, size_t le)
{
  size_t i = ls, digits = 0;
  int v = 0;
  while (i < le && (d[i] == ' ' || d[i] == '\t'))
    i++;
  while (i < le && d[i] >= '0' && d[i] <= '9')
    {
      if (digits < 5)
        v = v * 10 + (int)(d[i] - '0');
      digits++;
      i++;
    }
  if (digits == 0 || digits > 5)
    return -1;
  while (i < le && (d[i] == ' ' || d[i] == '\t'))
    i++; /* 容忍行尾空白 */
  if (i != le)
    return -1;
  return v;
}

/* value 行与字面量比较；两端 trim 空格/制表符（行尾 '\r' 已由 line_next 剥掉）。 */
static int
line_is_value (const uint8_t *d, size_t ls, size_t le, const char *lit)
{
  size_t a = ls, b = le, m = strlen (lit);
  while (a < b && (d[a] == ' ' || d[a] == '\t'))
    a++;
  while (b > a && (d[b - 1] == ' ' || d[b - 1] == '\t'))
    b--;
  if (b - a != m)
    return 0;
  return m == 0 ? 1 : memcmp (d + a, lit, m) == 0;
}

/* memmem 风格查找：输入不是 '\0' 结尾，所以用 memchr + memcmp。 */
static const uint8_t *
mem_find (const uint8_t *hay, size_t hn, const char *needle)
{
  size_t nn = strlen (needle);
  const uint8_t *p = hay;
  size_t left = hn;
  if (nn == 0 || hn < nn)
    return NULL;
  while (left >= nn)
    {
      const uint8_t *q
          = (const uint8_t *)memchr (p, (unsigned char)needle[0], left - nn + 1);
      if (!q)
        return NULL;
      if (memcmp (q, needle, nn) == 0)
        return q;
      left -= (size_t)(q - p) + 1;
      p = q + 1;
    }
  return NULL;
}

/* 行尾风格：整份文件跟随真实种子的 CRLF / LF，避免在 CRLF 文件里混入裸 LF。 */
static size_t
eol_of (const uint8_t *d, size_t n, const char **eol)
{
  size_t i = 0;
  while (i < n && d[i] != '\n')
    i++;
  if (i > 0 && i < n && d[i - 1] == '\r')
    {
      *eol = "\r\n";
      return 2;
    }
  *eol = "\n";
  return 1;
}

/* ===================== pair 遍历（按行对齐） ===================== */

typedef struct
{
  int code;
  size_t code_start; /* group code 行起点 */
  size_t val_start;  /* value 行起点 */
  size_t val_end;    /* value 行终点（不含 \r\n） */
  size_t val_next;   /* 下一行起点 = 下一个 pair 的起点 */
} Pair;

typedef struct
{
  const uint8_t *d;
  size_t n;
  size_t pos;
  size_t to;
} PairIter;

/* 按 (code 行, value 行) 交替前进。遇到不是合法 group code 的行就跳一行重新同步，
   这样 value 里恰好是 "0" / "330" 的数字不会被误当成 group code 行。 */
static int
pair_iter_next (PairIter *it, Pair *out)
{
  while (it->pos < it->to)
    {
      size_t ls, le, ln, vs, ve, vn;
      int c;
      if (!line_next (it->d, it->n, it->pos, &ls, &le, &ln))
        return 0;
      it->pos = ln;
      c = code_of_line (it->d, ls, le);
      if (c < 0)
        continue; /* 重新同步：本行不是 group code，丢掉 */
      if (!line_next (it->d, it->n, ln, &vs, &ve, &vn))
        return 0; /* 有 code 行但没有 value 行（截断） */
      it->pos = vn;
      out->code = c;
      out->code_start = ls;
      out->val_start = vs;
      out->val_end = ve;
      out->val_next = vn;
      return 1;
    }
  return 0;
}

/* 在 [from, to) 里找 code/val 匹配的 pair。code < 0 表示不限 code，
   val == NULL 表示不限 value；last != 0 取最后一个匹配。 */
static int
pair_find (const uint8_t *d, size_t n, size_t from, size_t to, int code,
           const char *val, int last, Pair *out)
{
  PairIter it;
  Pair p;
  int found = 0;
  it.d = d;
  it.n = n;
  it.pos = from;
  it.to = to;
  while (pair_iter_next (&it, &p))
    {
      if ((code < 0 || p.code == code)
          && (val == NULL || line_is_value (d, p.val_start, p.val_end, val)))
        {
          *out = p;
          found = 1;
          if (!last)
            break;
        }
    }
  return found;
}

/* 在 OBJECTS 段体里找实体起点：code 0 且 value 不是 ENDSEC / EOF / SECTION。
   last != 0 取最后一个（strat_4 用）。 */
static int
entity_find (const uint8_t *d, size_t n, size_t from, size_t to, int last,
             Pair *out)
{
  PairIter it;
  Pair p;
  int found = 0;
  it.d = d;
  it.n = n;
  it.pos = from;
  it.to = to;
  while (pair_iter_next (&it, &p))
    {
      if (p.code != 0)
        continue;
      if (line_is_value (d, p.val_start, p.val_end, "ENDSEC"))
        continue;
      if (line_is_value (d, p.val_start, p.val_end, "EOF"))
        continue;
      if (line_is_value (d, p.val_start, p.val_end, "SECTION"))
        continue;
      *out = p;
      found = 1;
      if (!last)
        break;
    }
  return found;
}

/* ===================== 插入缓冲区 ===================== */

typedef struct
{
  uint8_t buf[MAX_INSERT];
  size_t len;
} Ins;

static size_t
pair_len (const char *code, const char *val, size_t eollen)
{
  return strlen (code) + eollen + strlen (val) + eollen;
}

/* 追加一个完整的 "code + eol + value + eol" pair；超出 256 字节预算返回 0。 */
static int
ins_pair (Ins *b, const char *code, const char *val, const char *eol,
          size_t eollen)
{
  size_t cl = strlen (code), vl = strlen (val);
  size_t need = cl + eollen + vl + eollen;
  if (b->len + need > MAX_INSERT)
    return 0;
  memcpy (b->buf + b->len, code, cl);
  b->len += cl;
  memcpy (b->buf + b->len, eol, eollen);
  b->len += eollen;
  if (vl)
    {
      memcpy (b->buf + b->len, val, vl);
      b->len += vl;
    }
  memcpy (b->buf + b->len, eol, eollen);
  b->len += eollen;
  return 1;
}

static int
ins_raw (Ins *b, const char *s)
{
  size_t l = strlen (s);
  if (b->len + l > MAX_INSERT)
    return 0;
  memcpy (b->buf + b->len, s, l);
  b->len += l;
  return 1;
}

/* 在 pos 处插入 b：只插入，不删除任何已有字节。
   容量不够（Size + ins > MaxSize）时返回 0，且不修改 Data。 */
static size_t
do_insert (uint8_t *d, size_t n, size_t max, size_t pos, const Ins *b)
{
  if (b->len == 0 || pos > n || n + b->len > max)
    return 0;
  memmove (d + pos + b->len, d + pos, n - pos);
  memcpy (d + pos, b->buf, b->len);
  return n + b->len;
}

/* ===================== 小工具 ===================== */

static void
hex8 (char *out, uint32_t v)
{
  static const char *H = "0123456789ABCDEF";
  int i;
  for (i = 7; i >= 0; i--)
    {
      out[i] = H[v & 0xFu];
      v >>= 4;
    }
  out[8] = '\0';
}

static int
hexval (uint8_t c)
{
  if (c >= '0' && c <= '9')
    return (int)(c - '0');
  if (c >= 'a' && c <= 'f')
    return (int)(c - 'a') + 10;
  if (c >= 'A' && c <= 'F')
    return (int)(c - 'A') + 10;
  return -1;
}

/* 把 value 行解析成十六进制 handle：成功返回 1，并给出数值与位数（1..8）。
   handle 值在 in_dxf.c:578-584 就是用 sscanf ("%X") 解析的，所以只接受十六进制。 */
static int
hex_parse_text (const uint8_t *d, size_t ls, size_t le, uint32_t *val,
                size_t *digits_out)
{
  size_t a = ls, b = le, i;
  uint64_t v = 0;
  while (a < b && (d[a] == ' ' || d[a] == '\t'))
    a++;
  while (b > a && (d[b - 1] == ' ' || d[b - 1] == '\t'))
    b--;
  if (b - a == 0 || b - a > 8)
    return 0;
  for (i = a; i < b; i++)
    {
      int hv = hexval (d[i]);
      if (hv < 0)
        return 0;
      v = (v << 4) | (uint64_t)hv;
    }
  *val = (uint32_t)v;
  *digits_out = b - a;
  return 1;
}

/* 把 value 行当十六进制 handle，加上 off 后按"原位数"大写写回 out。
   位数会变长（溢出）或值非法时返回 0，调用者保持原值。 */
static int
hex_offset_text (const uint8_t *d, size_t ls, size_t le, uint32_t off,
                 char *out, size_t outcap)
{
  size_t digits, i;
  uint32_t v32 = 0;
  uint64_t v;
  if (!hex_parse_text (d, ls, le, &v32, &digits) || outcap < 10)
    return 0;
  v = (uint64_t)v32 + (uint64_t)off;
  if (v > 0xFFFFFFFFu)
    return 0;
  {
    uint64_t t = v;
    size_t need = 1;
    while (t > 0xFu)
      {
        t >>= 4;
        need++;
      }
    if (need > digits)
      return 0; /* 保持句柄宽度，避免改变 pair 长度 */
  }
  for (i = 0; i < digits; i++)
    {
      out[digits - 1 - i] = "0123456789ABCDEF"[v & 0xFu];
      v >>= 4;
    }
  out[digits] = '\0';
  return 1;
}

/* 找某个段的段体起点：第一个 value == name 的 pair 之后。
   真实文件里它是 code 2 的 value（0/SECTION + 2/<NAME>），不是 code 0，
   所以这里不限制 code；契约 §8 的 "0 / OBJECTS" 写法也能命中。 */
static int
named_section_body (const uint8_t *d, size_t n, const char *name, Pair *sec,
                    size_t *body)
{
  if (!pair_find (d, n, 0, n, -1, name, 0, sec))
    return 0;
  *body = sec->val_next;
  return 1;
}

/* OBJECTS 段体起点（调用 named_section_body，语义与旧版一致） */
static int
objects_body (const uint8_t *d, size_t n, Pair *sec, size_t *body)
{
  return named_section_body (d, n, "OBJECTS", sec, body);
}

/* 段体结束位置：body 之后第一个 code 0 的 pair（即 0/ENDSEC）的行首。
   找不到则返回 n。*have 表示是否真的找到了 ENDSEC。 */
static size_t
section_limit (const uint8_t *d, size_t n, size_t body, Pair *end, int *have)
{
  if (pair_find (d, n, body, n, 0, "ENDSEC", 0, end))
    {
      if (have)
        *have = 1;
      return end->code_start;
    }
  if (have)
    *have = 0;
  return n;
}

/* ===========================================================================
 * strat_0 -- feature_id: uaf-llm01
 *            同函数内释放后继续解引用（本漏洞唯一有已知崩溃证据的策略）
 *
 * mutation_op（landing_plan.json）:
 *   定位首个 "OBJECTS"，从它往后找第一个 "0 / ENDSEC" pair，在该 pair 的
 *   group-code 行之前插入 "0 / FUZZ_OBJ"；找不到 OBJECTS/ENDSEC 时退化为
 *   "最后一个 ENDSEC 之前"，再找不到则追加 "0 / FUZZ_OBJ" + 悬挂的 "0"。
 *
 * 引用 in_dxf.c:
 *   12267  释放后重读 pair->code（UAF 现场）
 *   12272  is_dwg_object("FUZZ_OBJ") 为假
 *   12282  DXF_RETURN_ENDSEC: code 0 / value 非空 / 不是 ENDSEC / 仍有字节 ->
 *          三个条件都不满足，不返回
 *   12284  dxf_free_pair(pair) 后没有重新赋值（dxf_free_pair 在 506-517 行，
 *          516 行 "pair = NULL" 只置空形参，对调用者无效）
 * =========================================================================== */
static size_t
strat_0 (uint8_t *D, size_t n, size_t max, uint32_t *rng)
{
  const char *eol;
  size_t eollen = eol_of (D, n, &eol);
  Pair sec, end;
  size_t pos = 0;
  int have = 0, have_obj = 0;
  Ins b;

  (void)rng; /* 该策略位置确定，不需要随机 */

  if (objects_body (D, n, &sec, &pos))
    {
      Pair dummy;
      int h = 0;
      have_obj = 1;
      pos = section_limit (D, n, sec.val_next, &dummy, &h);
      have = h;
    }
  /* 只在"整份输入里根本没有 OBJECTS"时才退到最后一个 ENDSEC；
     若 OBJECTS 存在但段内没有 ENDSEC，最后一个 ENDSEC 可能属于前面的段
     （语义错误），此时走下面的"追加到文件尾"分支。 */
  if (!have && !have_obj
      && pair_find (D, n, 0, n, 0, "ENDSEC", 1, &end))
    {
      pos = end.code_start;
      have = 1;
    }

  b.len = 0;
  if (have)
    {
      if (!ins_pair (&b, "0", "FUZZ_OBJ", eol, eollen))
        return 0;
      return do_insert (D, n, max, pos, &b);
    }

  /* 兜底：整份输入里没有 ENDSEC pair -> 追加到末尾 */
  if (!ins_pair (&b, "0", "FUZZ_OBJ", eol, eollen))
    return 0;
  if (!ins_raw (&b, "0") || !ins_raw (&b, eol))
    return 0;
  return do_insert (D, n, max, n, &b);
}

/* ===========================================================================
 * strat_1 -- feature_id: uaf-llm02
 *            重分配或释放后旧缓冲指针仍被访问（压 array_push 扩容路径）
 *
 * mutation_op（landing_plan.json，已按源码核实修正段与插入内容）:
 *   段选择顺序：ENTITIES 段 -> OBJECTS 段 -> 放弃（返回 0）。
 *   在选中段里找第一个"实体"项（优先带 100/AcDbEntity 子类标记的，否则第一个
 *   非结构标记项），紧跟在它自己的 "0 / NAME" 行之后插入 N 条
 *   "8 / <随机 8 位大写十六进制>" 图层对，使 find_tablehandle() 失败而走
 *   array_push，把待解析句柄压进 obj_hdls。
 *
 *   为什么必须优先 ENTITIES：in_dxf.c:8771 的
 *   `int is_entity = is_dwg_entity (name) || strEQc (name, "DIMENSION");`
 *   是按**对象名**判定的；OBJECTS 段内的项是 DICTIONARY/XRECORD 等非实体，
 *   is_entity 为假，code 8 根本走不到 9147 的 array_push 分支。
 *
 *   为什么不是 code 5：in_dxf.c:9076-9095 的 case 5 只做 obj->handle.value 赋值 +
 *   dwg_add_handle，完全不碰 array_push；array_push 只有两个调用点——
 *   9147（code 8 图层名）和 11055（以字符串给出的 handle 型字段）。
 *
 * 引用 in_dxf.c:
 *   9143-9150  case 8: if (is_entity && pair->value.s) { handle = find_tablehandle
 *              (dwg, pair); if (!handle) obj_hdls = array_push (obj_hdls, "layer",
 *              pair->value.s, ...); }  —— 图层名解析失败才入队
 *   12680-12682 obj_hdls = new_array_hdls (16)：初始容量 16
 *   702-724    array_push：710 行 hdls->size += 16 后 realloc，数组搬家
 *   8771       is_entity = is_dwg_entity (name)：实体判定依据
 *
 *   N 取 16~19：landing_plan 写的是 16~48，v2 上限 256B 下一条 8/8hex 占 13B，
 *   19*13 = 247 <= 256；一次变异就能越过 new_array_hdls(16) 的初始容量，
 *   第 17 条起就会触发 710 行的 realloc 扩容分支。
 * =========================================================================== */

/* 结构标记：这些 value 是段/表分隔符，不是实体名 */
static int
is_structural_value (const uint8_t *d, size_t ls, size_t le)
{
  static const char *const k_mark[] = { "SECTION", "ENDSEC",  "EOF",
                                        "TABLE",   "ENDTAB",  "BLOCK",
                                        "ENDBLK",  "CLASSES", "ENDCLASS",
                                        "OBJECTS", "ENTITIES" };
  size_t i;
  for (i = 0; i < sizeof (k_mark) / sizeof (k_mark[0]); i++)
    if (line_is_value (d, ls, le, k_mark[i]))
      return 1;
  return 0;
}

/* 在段体里挑一个实体项：优先 100/AcDbEntity 子类标记，其次第一个非结构项。
   （纯文本无法调用 is_dwg_entity()，这两个信号是它的最接近近似。） */
static int
entity_pick (const uint8_t *d, size_t n, size_t body, size_t limit, Pair *out)
{
  PairIter it;
  Pair p, first;
  int have_first = 0;
  unsigned seen = 0;
  it.d = d;
  it.n = n;
  it.pos = body;
  it.to = limit;
  while (seen < 64 && pair_iter_next (&it, &p))
    {
      Pair q;
      size_t bend;
      if (p.code != 0)
        continue;
      if (is_structural_value (d, p.val_start, p.val_end))
        continue;
      seen++;
      bend = limit;
      if (pair_find (d, n, p.val_next, limit, 0, NULL, 0, &q))
        bend = q.code_start;
      if (!have_first)
        {
          first = p;
          have_first = 1;
        }
      if (pair_find (d, n, p.val_next, bend, 100, "AcDbEntity", 0, &q))
        {
          *out = p;
          return 1;
        }
    }
  if (have_first)
    {
      *out = first;
      return 1;
    }
  return 0;
}

static size_t
strat_1 (uint8_t *D, size_t n, size_t max, uint32_t *rng)
{
  const char *eol;
  size_t eollen = eol_of (D, n, &eol);
  Pair sec, end, ent;
  size_t body, limit, pos;
  int have = 0;
  Ins b;
  unsigned want, i;

  /* 1) 优先 ENTITIES：只有真实体才会走 9147 的 array_push 分支 */
  if (named_section_body (D, n, "ENTITIES", &sec, &body))
    {
      limit = section_limit (D, n, body, &end, NULL);
      have = entity_pick (D, n, body, limit, &ent);
    }
  /* 2) 退回 OBJECTS 段内首个实体项 */
  if (!have && objects_body (D, n, &sec, &body))
    {
      limit = section_limit (D, n, body, &end, NULL);
      have = entity_pick (D, n, body, limit, &ent);
    }
  if (!have)
    return 0; /* 两个段都没有实体项 -> 不适用，不硬插 */
  pos = ent.val_next;

  b.len = 0;
  want = 16u + (rng_next (rng) % 4u); /* 16..19 条 */
  for (i = 0; i < want; i++)
    {
      char layer[9];
      hex8 (layer, rng_next (rng) | 1u); /* 随机 8 位大写十六进制，必不在 LAYER 表 */
      if (!ins_pair (&b, "8", layer, eol, eollen))
        break;
    }
  if (b.len == 0)
    return 0;
  return do_insert (D, n, max, pos, &b);
}

/* ===========================================================================
 * strat_2 -- feature_id: uaf-llm03
 *            清理或析构先释放后仍读取旧指针（压提前终止 / 清理路径）
 *
 * mutation_op（landing_plan.json）:
 *   在 OBJECTS 段内随机 pair 边界插入一条"空 value"的 pair（code 0 + 空行），
 *   使 DXF_RETURN_ENDSEC / DXF_CHECK_EOF 的 value 判空分支被压到；
 *   再在段尾 0/ENDSEC 的 **group-code 行之前**插入一条 0/"0" pair（旧版插在
 *   ENDSEC 之后即 end.val_next，而 12282 遇 ENDSEC 就 return，那 6 字节永远
 *   读不到，等于 no-op）。
 *
 * 引用 in_dxf.c:
 *   436-503  dxf_read_string：空行 -> i == 0 -> malloc(1) 得到 ""（非 NULL）
 *   486-487  只有 dat->byte >= dat->size 或 i >= 4096 才提前 return（value.s 才留 NULL）
 *   758-765  DXF_RETURN_ENDSEC：code 0 且 !value.s 或 value == "ENDSEC" 才返回
 *   12267/12284  空 value 的对象名同样走进 else 分支的 free，随后回到 12267
 * =========================================================================== */
static size_t
strat_2 (uint8_t *D, size_t n, size_t max, uint32_t *rng)
{
  const char *eol;
  size_t eollen = eol_of (D, n, &eol);
  Pair sec, end;
  size_t body, limit, cand[16], nc = 0, pos, tail = 0;
  int have_end = 0;
  size_t nn;
  Ins a, b;

  if (!objects_body (D, n, &sec, &body))
    return 0;
  limit = section_limit (D, n, body, &end, &have_end);
  if (have_end)
    tail = end.code_start; /* ENDSEC 的 code 行之前：插在 val_next 会被直接跳过 */

  {
    size_t p = body, ls, le, ln;
    while (nc < 16 && p < limit && line_next (D, n, p, &ls, &le, &ln))
      {
        if (code_of_line (D, ls, le) == 0)
          cand[nc++] = ls;
        p = ln;
      }
  }
  pos = nc ? cand[rng_next (rng) % nc] : body;

  a.len = 0;
  b.len = 0;
  if (!ins_pair (&a, "0", "", eol, eollen))
    return 0;
  if (have_end && !ins_pair (&b, "0", "0", eol, eollen))
    return 0;
  if (n + a.len + b.len > max)
    b.len = 0; /* 预算不够就只做段内那一处 */
  if (n + a.len + b.len > max)
    return 0;

  nn = n;
  if (b.len)
    {
      nn = do_insert (D, nn, max, tail, &b); /* 先插靠后的位置 */
      if (nn == 0)
        return 0;
    }
  return do_insert (D, nn, max, pos, &a);
}

/* ===========================================================================
 * strat_3 -- feature_id: uaf-llm04
 *            跨函数释放后仍访问陈旧对象（同 handle 的重复对象声明）
 *
 * mutation_op（landing_plan.json）:
 *   在 OBJECTS 段内选一个**完整**实体块（"0 / NAME" 到下一个 code 0 之前），
 *   整块复制一份插在其后，handle 值原样保留 -> 两个对象声明同一个 handle。
 *   契约 §7 是 v2 修订后的 256 字节上限（原 64）。实测 8 个真实种子 OBJECTS 段内
 *   最小的完整对象块是 83 字节（83/105/115/...），64 字节上限会让本策略在所有
 *   真实种子上 100% 不适用，所以上限放宽到 256。
 *   实现上只挑 **长度 <= 256 的最短完整块**；找不到这样的块就返回 0。
 *   这里**不做前缀截断**——截断出来的对象不完整，与设计"整段复制"不符
 *   （旧版在 v.dxf 上会止于 3/ACAD_GROUP 这种半截块）。
 *
 * 引用 in_dxf.c:
 *   12267-12276  两个同 handle 的 code 0 pair 都进 new_object()
 *   12274-12276  strdup + dxf_free_pair + new_object（跨函数交出对象所有权）
 *   8760/8771    new_object()：is_entity = is_dwg_entity (name) || "DIMENSION"
 *   9076-9095    case 5 只写 obj->handle（dwg_add_handle），对象按 handle 索引
 * =========================================================================== */
static size_t
strat_3 (uint8_t *D, size_t n, size_t max, uint32_t *rng)
{
  Pair sec, end, best;
  size_t body, limit, best_len = 0, best_end = 0;
  unsigned seen = 0;
  int have = 0;
  Ins b;

  (void)rng;

  if (!objects_body (D, n, &sec, &body))
    return 0;
  limit = section_limit (D, n, body, &end, NULL);

  best.code = 0;
  best.code_start = 0;
  best.val_start = 0;
  best.val_end = 0;
  best.val_next = 0;

  {
    PairIter it;
    Pair p;
    it.d = D;
    it.n = n;
    it.pos = body;
    it.to = limit;
    while (seen < 256 && pair_iter_next (&it, &p))
      {
        size_t bend, len;
        Pair q;
        if (p.code != 0)
          continue;
        if (is_structural_value (D, p.val_start, p.val_end))
          continue;
        seen++;
        bend = limit;
        if (pair_find (D, n, p.val_next, limit, 0, NULL, 0, &q))
          bend = q.code_start;
        if (bend <= p.code_start)
          continue;
        len = bend - p.code_start;
        if (len > MAX_INSERT)
          continue; /* 只整块复制：块太长就换下一块，绝不截断 */
        if (mem_find (D + p.code_start, len, "ENDSEC") != NULL)
          continue; /* ENDSEC 出现次数必须不变 */
        if (!have || len < best_len)
          {
            best = p;
            best_len = len;
            best_end = bend;
            have = 1;
          }
      }
  }
  if (!have || best_len == 0 || best_len > MAX_INSERT)
    return 0;

  memcpy (b.buf, D + best.code_start, best_len);
  b.len = best_len;
  return do_insert (D, n, max, best_end, &b);
}

/* ===========================================================================
 * strat_4 -- feature_id: uaf-llm05
 *            容器节点销毁后旧指针遍历访问（对象条数 / 容器增长）
 *
 * mutation_op（landing_plan.json）:
 *   复制 OBJECTS 段内的实体内容 K 份（K = 2..4），每份的 handle 值加一个偏移量，
 *   避免完全重复。这里取"最后一个实体"的 0/NAME(+5/HANDLE) 作为模板，合成 K 份
 *   插在该实体起点之前（与 strat_3 的"第一个实体块 + 原字节照抄"位置和内容都不同）。
 *   契约 §7（v2）上限 256 字节；K 仍受 landing_plan 的 2~4 约束，
 *   按"256 / 单份长度"反推后夹到 [2, 4]。
 *
 * 引用 in_dxf.c:
 *   12264-12289  dxf_objects_read 的实体循环，条数驱动 dwg->object[] / obj_hdls 增长
 *   8760/8771    new_object()：is_entity = is_dwg_entity (name) || "DIMENSION"
 *   738-746      free_array_hdls：遍历 items[] 逐个 free(field)/free(name) 再 free(hdls)
 *   578-584      handle 值按 %X 解析，加偏移后仍是合法十六进制串
 *   注：array_push 只在 9147（code 8 图层名）与 11055（字符串型 handle 字段）
 *       被调用，本策略复制对象不经过它，这里不再把它当作增长点。
 * =========================================================================== */
static size_t
strat_4 (uint8_t *D, size_t n, size_t max, uint32_t *rng)
{
  const char *eol;
  size_t eollen = eol_of (D, n, &eol);
  Pair sec, ent, end, hp;
  size_t body, limit, block_end;
  char name[80];
  size_t namelen;
  int have_h = 0;
  size_t hstart = 0, hend = 0;
  size_t unit_noh, k, i;
  uint32_t base;
  Ins all, one;

  if (!objects_body (D, n, &sec, &body))
    return 0;
  limit = section_limit (D, n, body, &end, NULL);
  if (!entity_find (D, n, body, limit, 1, &ent))
    return 0;

  /* 实体名：value 行两端 trim */
  {
    size_t a = ent.val_start, e = ent.val_end;
    while (a < e && (D[a] == ' ' || D[a] == '\t'))
      a++;
    while (e > a && (D[e - 1] == ' ' || D[e - 1] == '\t'))
      e--;
    namelen = e - a;
    if (namelen == 0 || namelen >= sizeof (name))
      return 0;
    memcpy (name, D + a, namelen);
    name[namelen] = '\0';
    if (strstr (name, "ENDSEC") != NULL || strcmp (name, "SECTION") == 0
        || strcmp (name, "EOF") == 0)
      return 0;
  }

  block_end = limit;
  {
    Pair nxt;
    if (pair_find (D, n, ent.val_next, limit, 0, NULL, 0, &nxt))
      block_end = nxt.code_start;
  }

  /* ---- handle 偏移规划（P2-1）--------------------------------------------
     旧版从 0x100 起加偏移并强制保位宽：1~2 位 handle（如 v.dxf 的 "C"）永远
     放不下 -> have_h=0；而且 base + i*16 可能中途越界；K 还可能退化成 1。
     现在先算"位宽能容纳多少"，再定 K 与 base，全都放不下就整体放弃 handle。 */
  unit_noh = pair_len ("0", name, eollen);
  k = 0;
  base = 0;
  if (pair_find (D, n, ent.val_next, block_end, 5, NULL, 0, &hp))
    {
      uint32_t hv = 0;
      size_t hdigits = 0;
      if (hex_parse_text (D, hp.val_start, hp.val_end, &hv, &hdigits))
        {
          uint64_t maxv = (hdigits >= 8)
                              ? 0xFFFFFFFFull
                              : ((1ull << (4u * (unsigned)hdigits)) - 1ull);
          uint64_t max_off = (maxv > (uint64_t)hv) ? maxv - (uint64_t)hv : 0;
          char pad[10];
          size_t kh, j;
          for (j = 0; j < hdigits; j++)
            pad[j] = '0';
          pad[hdigits] = '\0';
          kh = MAX_INSERT / (unit_noh + pair_len ("5", pad, eollen));
          if (kh > 4)
            kh = 4;
          /* 至少 2 份，且每份 +1 的偏移都在原 handle 位宽内 */
          if (kh >= 2 && max_off >= 2)
            {
              k = (max_off < (uint64_t)kh) ? (size_t)max_off : kh;
              if (k >= 2)
                {
                  base = 1
                         + (uint32_t)(rng_next (rng)
                                      % (uint32_t)(max_off - (uint64_t)k + 1));
                  hstart = hp.val_start;
                  hend = hp.val_end;
                  have_h = 1;
                }
            }
        }
    }
  if (!have_h)
    {
      k = MAX_INSERT / unit_noh; /* 放不下带 handle 的副本就只复制 0/NAME */
      if (k > 4)
        k = 4;
      if (k < 2)
        return 0; /* K 退化成 1 就不插（旧版会插 1 份） */
    }

  all.len = 0;
  for (i = 0; i < k; i++)
    {
      one.len = 0;
      if (!ins_pair (&one, "0", name, eol, eollen))
        break;
      if (have_h)
        {
          char hx[16];
          if (!hex_offset_text (D, hstart, hend, base + (uint32_t)i, hx,
                                sizeof (hx)))
            break; /* 规划阶段已保证放得下，走到这里说明数据异常 */
          if (!ins_pair (&one, "5", hx, eol, eollen))
            break;
        }
      if (all.len + one.len > MAX_INSERT)
        break;
      memcpy (all.buf + all.len, one.buf, one.len);
      all.len += one.len;
    }
  if (all.len == 0 || i < 2)
    return 0;
  return do_insert (D, n, max, ent.code_start, &all);
}

/* ===================== 派发表 ===================== */

static size_t (*const k_strats[5]) (uint8_t *, size_t, size_t, uint32_t *)
    = { strat_0, strat_1, strat_2, strat_3, strat_4 };

/* ===================== 导出入口 ===================== */

size_t
LLVMFuzzerCustomMutator (uint8_t *Data, size_t Size, size_t MaxSize,
                         unsigned int Seed)
{
  const MutCfg *cfg = cfg_get ();
  uint32_t s = (uint32_t)Seed;
  size_t out;
  unsigned k;

  /* Seed 派生本地 xorshift32（契约 §5）；先混一次，打散相邻 Seed 的低位相关性 */
  if (s == 0)
    s = 0x9e3779b9u;
  (void)rng_next (&s);

  /* LIBREDWG_MUTATOR_OFF=1 -> 100% default */
  if (cfg->off)
    {
      trace_tag (cfg, 'D', -1);
      return LLVMFuzzerMutate (Data, Size, MaxSize);
    }
  /* 契约 §2：返回值必须 <= MaxSize。MaxSize < Size 是异常配置，
     此时既不能原样返回 Size（会 > MaxSize），也只能返回 0。 */
  if (MaxSize < Size)
    {
      trace_tag (cfg, 'D', -1);
      return Size <= MaxSize ? Size : 0;
    }

  /* 强制策略：只调用该策略，不回退 default（契约 §4） */
  if (cfg->force >= 0)
    {
      k = (unsigned)cfg->force;
      if (Size < 8)
        {
          trace_tag (cfg, 'F', (int)k);
          return Size;
        }
      out = k_strats[k](Data, Size, MaxSize, &s);
      if (out == 0 || out > MaxSize)
        {
          trace_tag (cfg, 'F', (int)k);
          return Size; /* 不适用 -> 输入不变 */
        }
      trace_tag (cfg, 'S', (int)k);
      return out;
    }

  /* 契约 §6：Size < 8 直接走 default */
  if (Size < 8)
    {
      trace_tag (cfg, 'D', -1);
      return LLVMFuzzerMutate (Data, Size, MaxSize);
    }

  /* 权重（契约 §3）：default 占 (100 - pct)%，5 个策略均分 pct%。
     pct == 40 时 thr == 60，k = (r - 60) * 5 / 40，与契约给出的式子逐字等价。 */
  {
    unsigned r = rng_next (&s) % 100u;
    unsigned pct = cfg->pct;
    unsigned thr = 100u - pct;
    if (pct == 0 || r < thr)
      {
        trace_tag (cfg, 'D', -1);
        return LLVMFuzzerMutate (Data, Size, MaxSize);
      }
    k = (r - thr) * 5u / pct;
    if (k > 4)
      k = 4;
  }

  out = k_strats[k](Data, Size, MaxSize, &s);
  if (out == 0 || out > MaxSize)
    {
      trace_tag (cfg, 'F', (int)k);
      return LLVMFuzzerMutate (Data, Size, MaxSize);
    }
  trace_tag (cfg, 'S', (int)k);
  return out;
}
