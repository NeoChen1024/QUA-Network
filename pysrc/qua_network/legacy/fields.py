# SPDX-License-Identifier: Apache-2.0
"""Fields shared by several formats: docs/legacy/02-fields.md.

Every function takes absolute offsets into the line of the Scan. A field
function emits its tokens and findings and returns where the field ends;
callers (the format readers) decide what follows.
"""

import re

from qua_network.legacy.telemetry import b91_block

SP = 0x20
DIGITS = frozenset(b"0123456789")
UPPER = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWER = frozenset(b"abcdefghijklmnopqrstuvwxyz")


def is_b91(c):
    """b91.digit: '!' to '{' (amb.b91.set)."""
    return 0x21 <= c <= 0x7B


def _digits(b):
    return len(b) > 0 and all(c in DIGITS for c in b)


def missing(scan, rule, p, end):
    """True, with a syntax finding at p, when a required field starts at end."""
    if p >= end:
        scan.find(rule, "syntax", p)
        return True
    return False


# --- Timestamps (02 section 2) ------------------------------------------

_TIME_IND = {0x7A: "time.dhm", 0x2F: "time.dhm", 0x68: "time.hms"}  # z / h


def timestamp7(scan, s, end, depth):
    """A seven-byte timestamp, DHM or HMS by the byte at offset 6.

    Returns (end of the token, True when all seven bytes were present)."""
    line = scan.line
    e = min(s + 7, end)
    ind = line[s + 6] if s + 6 < end else None
    rule = _TIME_IND.get(ind, "time.dhm")
    scan.tok(rule, s, e, depth)
    b = line[s:e]
    bad = next((i for i in range(min(6, len(b))) if b[i] not in DIGITS), None)
    if bad is None and e < s + 7:
        bad = e - s
    elif bad is None and ind not in _TIME_IND:
        bad = 6
    if bad is not None:
        # One syntax finding per fixed field, at the first byte that fails.
        scan.find(rule, "syntax", s + bad)
    if ind == 0x2F:
        scan.find("time.dhm", "discouraged", s + 6)
    # Value ranges, on each part whose two digits are present.
    ranges = ((0, 23), (0, 59), (0, 59)) if rule == "time.hms" else ((1, 31), (0, 23), (0, 59))
    for i, (lo, hi) in enumerate(ranges):
        part = b[2 * i : 2 * i + 2]
        if len(part) == 2 and _digits(part) and not lo <= int(part) <= hi:
            scan.find(rule, "value", s + 2 * i)
    return e, e == s + 7


def timestamp8(scan, s, end, depth):
    """time.mdhm: eight digits, month, day, hour and minute.

    Returns (end of the token, True when all eight bytes were present)."""
    line = scan.line
    e = min(s + 8, end)
    scan.tok("time.mdhm", s, e, depth)
    b = line[s:e]
    bad = next((i for i, c in enumerate(b) if c not in DIGITS), None)
    if bad is None and e < s + 8:
        bad = e - s
    if bad is not None:
        scan.find("time.mdhm", "syntax", s + bad)
    for i, (lo, hi) in enumerate(((1, 12), (1, 31), (0, 23), (0, 59))):
        part = b[2 * i : 2 * i + 2]
        if len(part) == 2 and _digits(part) and not lo <= int(part) <= hi:
            scan.find("time.mdhm", "value", s + 2 * i)
    return e, e == s + 8


# --- Latitude and longitude (02 section 3) ------------------------------

_LAT_AMB = (6, 5, 3, 2)
_LON_AMB = (7, 6, 4, 3)
_LAT_SHAPE = (DIGITS, DIGITS, None, None, frozenset(b"."), None, None, frozenset(b"NS"))
_LON_SHAPE = (DIGITS, DIGITS, DIGITS, None, None, frozenset(b"."), None, None, frozenset(b"EW"))
_DIGIT_SP = DIGITS | {SP}


def _coord(scan, s, end, depth, rule, shape, order, deg_n, deg_max, lat_level):
    """Shared body of lat and lon. Returns (end, complete, level)."""
    line = scan.line
    n = len(shape)
    e = min(s + n, end)
    scan.tok(rule, s, e, depth)
    b = line[s:e]
    bad = None
    for i, c in enumerate(b):
        allowed = shape[i] or _DIGIT_SP
        if c not in allowed:
            bad = i
            break
    if bad is None and e < s + n:
        bad = e - s
    if bad is not None:
        scan.find(rule, "syntax", s + bad)
    # Value ranges, on digits that are present (amb.lat.range).
    if _digits(b[:deg_n]):
        deg = int(b[:deg_n])
        if deg > deg_max:
            scan.find(rule, "value", s)
        if len(b) > deg_n and 0x36 <= b[deg_n] <= 0x39:
            scan.find(rule, "value", s + deg_n)
        mins = [b[i] for i in (deg_n, deg_n + 1, deg_n + 3, deg_n + 4) if i < len(b)]
        if deg == deg_max and any(c in DIGITS and c != 0x30 for c in mins):
            scan.find(rule, "value", s + deg_n)
    if e < s + n:
        return e, False, 0
    # The level is the number of SP from the start of the order; a SP after
    # an offset of the order that holds a digit breaks the order.
    level = 0
    while level < 4 and b[order[level]] == SP:
        level += 1
    amb_rule = rule + ".amb"
    digit_seen = False
    for off in order:
        if b[off] in DIGITS:
            digit_seen = True
        elif b[off] == SP and digit_seen:
            scan.find(amb_rule, "syntax", s + off)
    if lat_level is not None and level > lat_level:
        scan.find(amb_rule, "syntax", s + order[lat_level])
    return e, True, level


def lat(scan, s, end, depth):
    return _coord(scan, s, end, depth, "lat", _LAT_SHAPE, _LAT_AMB, 2, 90, None)


def lon(scan, s, end, depth, lat_level):
    return _coord(scan, s, end, depth, "lon", _LON_SHAPE, _LON_AMB, 3, 180, lat_level)


# --- Symbol (02 section 4) ----------------------------------------------

SYM_TABLE = frozenset(b"/\\0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def sym_table(scan, s, depth):
    scan.tok("sym.table", s, s + 1, depth)
    if scan.line[s] not in SYM_TABLE:
        scan.find("sym.table", "syntax", s)


def sym_code(scan, s, depth, rule="sym.code"):
    scan.tok(rule, s, s + 1, depth)
    if not 0x21 <= scan.line[s] <= 0x7E:
        scan.find(rule, "syntax", s)


# --- Compressed position block (02 section 6) ---------------------------

CMP_TABLE = frozenset(b"/\\ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij")
_CMP_MAX = 68566680  # 380926 * 180 = 190463 * 360


def _b91_value(scan, rule, s, n):
    """Check n base-91 digits; returns their value, or None after a syntax finding."""
    v = 0
    for i in range(n):
        c = scan.line[s + i]
        if not is_b91(c):
            scan.find(rule, "syntax", s + i)
            return None
        v = v * 91 + c - 33
    return v


def cmp_block(scan, s, end, depth, wx):
    """The 13-byte compressed block; wx says whether the report is weather.

    Returns the end of the block, or None when the field ends inside it."""
    line = scan.line
    if end < s + 13:
        scan.tok("cmp.block", s, end, depth)
        bad = end
        for i in range(s, end):
            o, c = i - s, line[i]
            ok = c in CMP_TABLE if o == 0 else 0x21 <= c <= 0x7E if o == 9 else is_b91(c) if o < 9 else True
            if not ok:
                bad = i
                break
        scan.find("cmp.block", "syntax", bad)
        return None
    scan.tok("cmp.block", s, s + 13, depth)
    d = depth + 1
    scan.tok("cmp.table", s, s + 1, d)
    if line[s] not in CMP_TABLE:
        scan.find("cmp.table", "syntax", s)
    for rule, o in (("cmp.lat", 1), ("cmp.lon", 5)):
        scan.tok(rule, s + o, s + o + 4, d)
        v = _b91_value(scan, rule, s + o, 4)
        if v is not None and v > _CMP_MAX:
            scan.find(rule, "value", s + o)
    sym_code(scan, s + 9, d, "cmp.code")
    c, sb, t = line[s + 10], line[s + 11], line[s + 12]
    cs, ts = s + 10, s + 12
    tv = t - 33
    if c == SP:
        # Step 1: s and T are fillers (amb.cmp.filler).
        scan.tok("cmp.cs.none", cs, cs + 2, d)
        if not (is_b91(sb) or sb == SP):
            scan.find("cmp.cs.none", "syntax", cs + 1)
        scan.tok("cmp.t", ts, ts + 1, d)
        if not (is_b91(t) or t == SP):
            scan.find("cmp.t", "syntax", ts)
        return s + 13
    if is_b91(t) and (tv >> 3) & 3 == 2:
        rule = "cmp.cs.alt"
    elif wx and 0x21 <= c <= 0x7A:
        rule = "cmp.cs.wind"
    elif 0x21 <= c <= 0x7A:
        rule = "cmp.cs.crs"
    elif c == 0x7B:
        rule = "cmp.cs.rng"
    else:
        rule = "cmp.cs"
    scan.tok(rule, cs, cs + 2, d)
    if rule == "cmp.cs":
        scan.find("cmp.cs", "syntax", cs)
    else:
        if rule == "cmp.cs.alt" and not is_b91(c):
            scan.find(rule, "syntax", cs)
        elif rule == "cmp.cs.alt":
            # amb.cmp.cs: a reading by the range of c alone would take
            # course and speed, or range.
            scan.find(rule, "ambiguous", cs)
        if is_b91(c) and not is_b91(sb):
            scan.find(rule, "syntax", cs + 1)
    scan.tok("cmp.t", ts, ts + 1, d)
    if not is_b91(t):
        scan.find("cmp.t", "syntax", ts)
    elif tv & 0x40:
        scan.find("cmp.t", "value", ts)
    return s + 13


# --- Data extensions (02 section 7) -------------------------------------

_PART_KIND = {b"...": ".", b"   ": " "}
_DDS = DIGITS | frozenset(b". ")


def _part(b):
    if _digits(b):
        return "d"
    return _PART_KIND.get(bytes(b))


class Ext:
    """A form of 02 section 7.2 that fits at an offset."""

    __slots__ = ("rule", "start", "n", "findings", "h_alpha")

    def __init__(self, rule, start, n, findings, h_alpha=False):
        self.rule = rule
        self.start = start
        self.n = n
        self.findings = findings  # [(rule, kind, offset)]
        self.h_alpha = h_alpha  # amb.ext.phg: h is not a digit

    def clean(self):
        """No syntax or value finding of the form itself."""
        return not any(k in ("syntax", "value") for _, k, _ in self.findings)


def _csespd(line, p, end, rule="ext.csespd"):
    if end - p < 7 or line[p + 3] != 0x2F:
        return None
    kc, ks = _part(line[p : p + 3]), _part(line[p + 4 : p + 7])
    if kc is None or ks is None:
        return None
    f = []
    over = kc == "d" and int(line[p : p + 3]) > 360
    if over:
        f.append((rule, "value", p))
    if kc != ks:
        f.append((rule, "unstated", p))
        if not over:
            # amb.ext.csespd: reading (c) takes only the listed forms.
            f.append((rule, "ambiguous", p))
    return Ext(rule, p, 7, f)


def dirspd(line, p, end):
    """ext.dirspd at p: the layout and findings of ext.csespd (7.2, 7.3)."""
    return _csespd(line, p, end, "ext.dirspd")


def csespd_mixed(line, p, end):
    """amb.ext.csespd: seven bytes with '/' at offset 3 and only digits, dots and
    spaces that reading (a) rejects. Returns the offset of the ambiguous finding
    (p) when reading (b) would accept them, else None."""
    if end - p < 7 or line[p + 3] != 0x2F:
        return None
    c, s = line[p : p + 3], line[p + 4 : p + 7]
    if not all(x in _DDS for x in c + s):
        return None
    if _part(c) is not None and _part(s) is not None:
        return None
    if _digits(c) and int(c) > 360:
        return None
    return p


def _hgd(line, q):
    """PHG/DFS h, g, d at q; returns (fits, d_is_9, h_alpha)."""
    h, g, d = line[q], line[q + 1], line[q + 2]
    fits = 0x30 <= h <= 0x7E and g in DIGITS and d in DIGITS
    return fits, d == 0x39, h not in DIGITS


def _phg(line, p, end):
    if end - p < 7 or line[p : p + 3] != b"PHG" or line[p + 3] not in DIGITS:
        return None
    fits, d9, ha = _hgd(line, p + 4)
    if not fits:
        return None
    phgr = end - p >= 9 and (line[p + 7] in DIGITS or line[p + 7] in UPPER) and line[p + 8] == 0x2F
    rule = "ext.phgr" if phgr else "ext.phg"
    f = [(rule, "value", p + 6)] if d9 else []
    return Ext(rule, p, 9 if phgr else 7, f, ha and not d9)


def _rng(line, p, end):
    if end - p < 7 or line[p : p + 3] != b"RNG" or not _digits(line[p + 3 : p + 7]):
        return None
    return Ext("ext.rng", p, 7, [])


def _dfs(line, p, end):
    if end - p < 7 or line[p : p + 3] != b"DFS" or line[p + 3] not in DIGITS:
        return None
    fits, d9, ha = _hgd(line, p + 4)
    if not fits:
        return None
    return Ext("ext.dfs", p, 7, [("ext.dfs", "value", p + 6)] if d9 else [], ha and not d9)


def step3(line, p, end):
    """The first form of step 3 of 02 section 7.1 that fits at p, or None.
    PHGR is tried with PHG, before it."""
    return _csespd(line, p, end) or _phg(line, p, end) or _rng(line, p, end) or _dfs(line, p, end)


_AREA_LITERAL = re.compile(rb"T[0-9]{2}/C[0-9]{2}")


def area_literal(line, p, end):
    """amb.ext.area: the descriptor's name spelled with literal letters."""
    return end - p >= 7 and _AREA_LITERAL.match(line, p) is not None


def area_bad(line, p, end):
    """ext.area at p: None when the seven bytes fit the descriptor, else the
    offset of the first byte that does not fit (end when the field is cut
    short there)."""
    for i in range(7):
        if p + i >= end:
            return end
        c = line[p + i]
        if i == 3:
            ok = c in b"/1"
        elif i == 4:
            ok = c in DIGITS if line[p + 3] == 0x2F else 0x30 <= c <= 0x35
        else:
            ok = c in DIGITS
        if not ok:
            return p + i
    return None


def area_high(line, p, end):
    """Seven bytes at p that fit ext.area with a colour of 10 to 15, which no
    form of step 3 of 7.1 takes (amb.area.symbol)."""
    return end - p >= 7 and line[p + 3] == 0x31 and area_bad(line, p, end) is None


_BRG = re.compile(rb"/([0-9]{3})/[0-9]{3}")


def brgnrq_shape(line, p, end):
    """The bearing of an 8-byte ext.brgnrq shape at p, or None."""
    m = _BRG.match(line, p, end)
    return int(m.group(1)) if m else None


def emit_ext(scan, x, depth):
    scan.tok(x.rule, x.start, x.start + x.n, depth)
    for f in x.findings:
        scan.find(*f)


# --- Comment (02 section 8) ---------------------------------------------

# Overlapping matches of every step-3 form, and of the comment items.
_STEP3_AT = re.compile(rb"(?=[0-9. ]{3}/[0-9. ]{3}|PHG|RNG|DFS)")


def bad_text_bytes(b):
    """Offsets in b of bytes outside printable ASCII and well-formed UTF-8."""
    try:
        b.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        return [i for i, c in enumerate(b) if c < 0x20 or c == 0x7F]
    out = []
    i, n = 0, len(b)
    while i < n:
        c = b[i]
        if c < 0x80:
            if c < 0x20 or c == 0x7F:
                out.append(i)
            i += 1
            continue
        if 0xC2 <= c <= 0xDF:
            k, lo, hi = 1, 0x80, 0xBF
        elif c == 0xE0:
            k, lo, hi = 2, 0xA0, 0xBF
        elif 0xE1 <= c <= 0xEC or 0xEE <= c <= 0xEF:
            k, lo, hi = 2, 0x80, 0xBF
        elif c == 0xED:
            k, lo, hi = 2, 0x80, 0x9F
        elif c == 0xF0:
            k, lo, hi = 3, 0x90, 0xBF
        elif 0xF1 <= c <= 0xF3:
            k, lo, hi = 3, 0x80, 0xBF
        elif c == 0xF4:
            k, lo, hi = 3, 0x80, 0x8F
        else:
            out.append(i)
            i += 1
            continue
        ok = i + k < n and lo <= b[i + 1] <= hi and all(0x80 <= b[i + j] <= 0xBF for j in range(2, k + 1))
        if ok:
            i += k + 1
        else:
            out.append(i)
            i += 1
    return out


def dao_kind(line, i):
    """The result of the table of 02 section 8.3 for '!' D A O '!' at i:
    None (not a candidate), "" (cmt.dao) or "unstated"."""
    d, a, o = line[i + 1], line[i + 2], line[i + 3]
    letter = d in UPPER or d in LOWER
    digit = d in DIGITS
    if d in UPPER and a in DIGITS and o in DIGITS:
        return ""
    if d in LOWER and is_b91(a) and is_b91(o):
        return ""
    if (letter or digit) and a == SP and o == SP:
        return ""
    if digit and is_b91(a) and is_b91(o):
        return "unstated"
    if letter or digit:
        fit = (lambda x: x in DIGITS) if d in UPPER else is_b91
        if (a == SP) != (o == SP) and fit(o if a == SP else a):
            return "unstated"
        return None
    if is_b91(d) and a == SP and o == SP:
        return "unstated"
    return None


def dao_candidates(line, s, e):
    out = []
    i = line.find(b"!", s, e)
    while 0 <= i and i + 5 <= e:
        if line[i + 4] == 0x21:
            k = dao_kind(line, i)
            if k is not None:
                out.append((i, k))
        i = line.find(b"!", i + 1, e)
    return out


def _altitudes(scan, s, e, d):
    """cmt.alt and cmt.alt.neg; returns the spans of the occurrences."""
    line = scan.line
    occ = []
    i = line.find(b"/A=", s, e)
    while i >= 0:
        j = i + 3
        nxt = i + 9
        if _digits(line[j:nxt]) and nxt <= e and (nxt == e or line[nxt] not in DIGITS):
            occ.append(("cmt.alt", i))
        elif line[j : j + 1] == b"-" and _digits(line[j + 1 : nxt]) and nxt <= e and (nxt == e or line[nxt] not in DIGITS):
            occ.append(("cmt.alt.neg", i))
        else:
            scan.find("cmt.alt", "syntax", i)
        i = line.find(b"/A=", i + 1, e)
    for rule, i in occ:
        scan.tok(rule, i, i + 9, d)
        if len(occ) > 1:
            scan.find(rule, "ambiguous", i)
    return [(rule, i, i + 9) for rule, i in occ]


class Comment:
    """What comment() found: its extent, the bytes it counts and its DAOs."""

    __slots__ = ("start", "end", "counted", "daos")

    def __init__(self, start, end, counted, daos):
        self.start, self.end, self.counted, self.daos = start, end, counted, daos


def comment(
    scan,
    s,
    end,
    depth,
    limit,
    limit_rule,
    b91=True,
    freq=True,
    b91_kind=None,
    extra=(),
    start_cse=True,
    freq_name=False,
    ext_search=True,
):
    """cmt.text from s to end with the items of 02 section 8.2.

    limit and limit_rule are the format's length limit and the rule that
    reports it; b91 searches base-91 telemetry (07), freq looks for a
    frequency at the start (09 section 7), and freq_name says that the
    comment belongs to an object or item named as a frequency, whose items
    are left-justified (09 freq.obj). b91_kind, when given, is the kind
    of finding a telemetry block gets in this format (07 section 3). extra
    holds (rule, start, end) of items the format itself found in the comment
    and has tokenized, for the overlap rule of 8.2. start_cse=False leaves out
    the course and speed at the comment start, for a report in which 7.1
    would not try that form at a slot. Returns a Comment, or None when the
    comment is empty."""
    if s >= end:
        return None
    line = scan.line
    scan.tok("cmt.text", s, end, depth)
    for i in bad_text_bytes(line[s:end]):
        scan.find("cmt.text", "syntax", s + i)
    d = depth + 1
    items = _altitudes(scan, s, end, d)

    # DAO candidates (8.3); the bytes of all of them are not counted.
    daos = dao_candidates(line, s, end)
    dao_bytes = set()
    for i, k in daos:
        scan.tok("cmt.dao", i, i + 5, d)
        if k:
            scan.find("cmt.dao", k, i)
        dao_bytes.update(range(i, i + 5))
        items.append(("cmt.dao", i, i + 5))
    counted = (end - s) - len(dao_bytes)
    if len(daos) > 1 and ((end - s) - 5 <= limit or counted > limit):
        # amb.cmt.dao: reading (b) or (c) takes the others as counted text; a
        # length finding that this reading gives too does not count.
        for i, _ in daos:
            scan.find("cmt.dao", "ambiguous", i)

    if b91:
        blk = b91_block(scan, s, end, d, daos)
        if blk:
            items.append(("tlm.b91",) + blk)
            if b91_kind:
                scan.find("tlm.b91", b91_kind, blk[0])

    items.extend(noarchive_in(scan, s, end, d))
    items.extend(extra)

    # Occurrences of two different items that overlap (8.2).
    if len(items) > 1:
        items.sort(key=lambda t: t[1])
        for a in range(len(items)):
            ra, sa, ea = items[a]
            for b in range(a + 1, len(items)):
                rb, sb, eb = items[b]
                if sb >= ea:
                    break
                if _item(ra) != _item(rb):
                    scan.find(ra, "ambiguous", sa)
                    scan.find(rb, "ambiguous", sb)

    # amb.ext.count / amb.ext.compressed: a step-3 form that fits cleanly.
    # A course and speed, which has no marker, counts only at the comment
    # start; the forms with a three-letter marker count anywhere.
    for m in _STEP3_AT.finditer(line, s, end) if ext_search else ():
        x = step3(line, m.start(), end)
        if x is not None and x.clean() and (x.rule != "ext.csespd" or (x.start == s and start_cse)):
            scan.find(x.rule, "ambiguous", x.start)

    if counted > limit:
        n = 0
        for i in range(s, end):
            if i not in dao_bytes:
                n += 1
                if n > limit:
                    scan.find(limit_rule, "value", i)
                    break

    if freq:
        # 09 section 7, after every syntax or value finding of the comment,
        # which its ambiguous findings defer to. other.py builds on this
        # module, so it is imported here.
        from qua_network.legacy.other import frequency

        frequency(scan, s, end, d, freq_name)
    return Comment(s, end, counted, daos)


def _item(rule):
    return "cmt.alt" if rule.startswith("cmt.alt") else rule


def noarchive_in(scan, s, e, d):
    """cmt.noarchive tokens in the free-text field line[s:e]; returns their spans."""
    line = scan.line
    nx = []
    i = line.find(b"!x!", s, e)
    while i >= 0 and i + 3 <= e:
        nx.append(i)
        i = line.find(b"!x!", i + 1, e)
    for i in nx:
        scan.tok("cmt.noarchive", i, i + 3, d)
        if len(nx) > 1:
            scan.find("cmt.noarchive", "ambiguous", i)
    return [("cmt.noarchive", i, i + 3) for i in nx]


def noarchive_outside(scan, start, end, texts):
    """'!x!' in the information field outside the free-text spans (amb.cmt.noarchive).

    No finding where the reading already reports the bytes: inside a residue
    (which an unread format's field also is) or on a syntax or value finding."""
    line = scan.line
    i = line.find(b"!x!", start, end)
    if i < 0:
        return
    residues = [(t.start, t.end) for t in scan.tokens if t.rule == "residue"]
    reported = {f.offset for f in scan.findings if f.kind in ("syntax", "value")}
    while i >= 0:
        inside = any(ts <= i and i + 3 <= te for ts, te in texts) or any(rs <= i < re_ for rs, re_ in residues)
        if not inside and not reported.intersection(range(i, i + 3)):
            scan.find("cmt.noarchive", "ambiguous", i)
        i = line.find(b"!x!", i + 1, end)
