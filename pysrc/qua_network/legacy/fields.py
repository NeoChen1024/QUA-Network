# SPDX-License-Identifier: Apache-2.0
"""Fields shared by several formats: docs/legacy/02-fields.md.

Every function takes absolute offsets into the line of the Scan. A field
function emits its tokens and findings and returns where the field ends;
callers (the format readers) decide what follows.
"""

import re

from qua_network.legacy.telemetry import b91_block, b91_span

SP = 0x20
DIGITS = frozenset(b"0123456789")
UPPER = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWER = frozenset(b"abcdefghijklmnopqrstuvwxyz")


def is_b91(c):
    """b91.digit: '!' to '|' (err.b91.range)."""
    return 0x21 <= c <= 0x7C


def _digits(b):
    # bytes.isdigit: one or more ASCII digits.
    return b.isdigit()


def missing(scan, rule, p, end):
    """True, with a syntax finding at p, when a required field starts at end
    (Scan.missing: only the first missing field at one byte gives it)."""
    if p >= end:
        scan.missing(rule, p)
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
    # Failing bytes as (offset, rule); the field gives one syntax finding, at
    # the first of them.
    bad = []
    for i, c in enumerate(b):
        allowed = shape[i] or _DIGIT_SP
        if c not in allowed:
            bad.append((i, rule))
            break
    if not bad and e < s + n:
        bad.append((e - s, rule))
    level = 0
    if len(b) > order[0]:
        # The order starts at the highest offset, so once it is present the
        # whole order is.
        if lat_level is None:
            # lat.amb: blanks from the right; a SP after an offset of the
            # order that holds a digit breaks it.
            while level < 4 and b[order[level]] == SP:
                level += 1
            digit_seen = False
            for off in order:
                if b[off] in DIGITS:
                    digit_seen = True
                elif b[off] == SP and digit_seen:
                    bad.append((off, "lat.amb"))
        else:
            # lon.amb: a SP that the latitude's level does not cover is a case
            # the document does not give (amb.lat.ambiguity).
            beyond = [off for off in order[lat_level:] if b[off] == SP]
            if beyond:
                scan.find("lon.amb", "unstated", s + min(beyond))
    if bad:
        off, r = min(bad)
        scan.find(r, "syntax", s + off)
    # Value ranges, on digits that are present.
    if _digits(b[:deg_n]):
        deg = int(b[:deg_n])
        if deg > deg_max:
            scan.find(rule, "value", s)
        if len(b) > deg_n and 0x36 <= b[deg_n] <= 0x39:
            scan.find(rule, "value", s + deg_n)
        mins = [b[i] for i in (deg_n, deg_n + 1, deg_n + 3, deg_n + 4) if i < len(b)]
        if deg == deg_max and any(c in DIGITS and c != 0x30 for c in mins):
            scan.find(rule, "value", s + deg_n)
    return e, e == s + n, level


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
        _cmp_short(scan, s, end, depth)
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
        # Step 1: s and T are ignored fillers, any byte (amb.cmp.filler).
        scan.tok("cmp.cs.none", cs, cs + 2, d)
        scan.tok("cmp.t", ts, ts + 1, d)
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
    if rule == "cmp.cs" or not is_b91(c):
        scan.find(rule, "syntax", cs)
    elif not is_b91(sb):
        scan.find(rule, "syntax", cs + 1)
    scan.tok("cmp.t", ts, ts + 1, d)
    if not is_b91(t):
        scan.find("cmp.t", "syntax", ts)
    elif tv & 0x40:
        scan.find("cmp.t", "value", ts)
    return s + 13


def _cmp_short(scan, s, end, depth):
    """A block cut short by the end of its field (02 section 6.2): each part
    with a byte present is a token over the bytes it has, checked as in a
    whole block; the part where the first missing byte was expected gives
    the syntax finding there, unless a byte of it already failed. Without T
    the step of 6.3 is unknown, so c fails only where no step takes it."""
    line = scan.line
    scan.tok("cmp.block", s, end, depth)
    d = depth + 1
    c = line[s + 10] if s + 10 < end else None
    cs_rule = "cmp.cs.none" if c == SP else "cmp.cs"
    for rule, o, n in (("cmp.table", 0, 1), ("cmp.lat", 1, 4), ("cmp.lon", 5, 4), ("cmp.code", 9, 1), (cs_rule, 10, 2)):
        p, q = s + o, min(s + o + n, end)
        if p >= end:
            scan.find(rule, "syntax", p)
            return
        scan.tok(rule, p, q, d)
        bad = None
        for i in range(p, q):
            x = line[i]
            if rule == "cmp.table":
                ok = x in CMP_TABLE
            elif rule == "cmp.code":
                ok = 0x21 <= x <= 0x7E
            elif rule == "cmp.cs.none":
                ok = True
            else:
                ok = is_b91(x)
            if not ok:
                bad = i
                break
        if bad is None and q < s + o + n:
            bad = q
        if bad is not None:
            scan.find(rule, "syntax", bad)
        elif rule in ("cmp.lat", "cmp.lon") and _b91_value(scan, rule, p, 4) > _CMP_MAX:
            scan.find(rule, "value", p)
        if q < s + o + n:
            return
    # Only T is missing.
    scan.find("cmp.t", "syntax", end)


# --- Data extensions (02 section 7) -------------------------------------

_PART_KIND = {b"...": ".", b"   ": " "}


def _part(b):
    if _digits(b):
        return "d"
    return _PART_KIND.get(bytes(b))


class Ext:
    """A form of 02 section 7.2 that fits at an offset."""

    __slots__ = ("rule", "start", "n", "findings")

    def __init__(self, rule, start, n, findings):
        self.rule = rule
        self.start = start
        self.n = n
        self.findings = findings  # [(rule, kind, offset)]

    def clean(self):
        """No syntax or value finding of the form itself."""
        return not any(k in ("syntax", "value") for _, k, _ in self.findings)


def _csespd(line, p, end):
    rule = "ext.csespd"
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
        # amb.ext.csespd: a known value beside an unknown one is a combination
        # the document does not give, and a reading that takes only the listed
        # pairs reads the bytes as comment text.
        f.append((rule, "unstated", p))
        if not over:
            f.append((rule, "ambiguous", p))
    return Ext(rule, p, 7, f)


def _hgd(line, q):
    """PHG/DFS h, g, d at q; returns (fits, d_is_9)."""
    h, g, d = line[q], line[q + 1], line[q + 2]
    return 0x30 <= h <= 0x7E and g in DIGITS and d in DIGITS, d == 0x39


def _phg(line, p, end):
    if end - p < 7 or line[p : p + 3] != b"PHG" or line[p + 3] not in DIGITS:
        return None
    fits, d9 = _hgd(line, p + 4)
    if not fits:
        return None
    # PHGR: a rate byte '0'-'9', or 'A' (10) "and so on", then '/'.
    phgr = end - p >= 9 and (line[p + 7] in DIGITS or 0x41 <= line[p + 7] <= 0x7E) and line[p + 8] == 0x2F
    rule = "ext.phgr" if phgr else "ext.phg"
    f = [(rule, "value", p + 6)] if d9 else []
    return Ext(rule, p, 9 if phgr else 7, f)


def _rng(line, p, end):
    if end - p < 7 or line[p : p + 3] != b"RNG" or not _digits(line[p + 3 : p + 7]):
        return None
    return Ext("ext.rng", p, 7, [])


def _dfs(line, p, end):
    if end - p < 7 or line[p : p + 3] != b"DFS" or line[p + 3] not in DIGITS:
        return None
    fits, d9 = _hgd(line, p + 4)
    if not fits:
        return None
    return Ext("ext.dfs", p, 7, [("ext.dfs", "value", p + 6)] if d9 else [])


def step3(line, p, end):
    """The first form of step 3 of 02 section 7.1 that fits at p, or None.
    PHGR is tried with PHG, before it."""
    return _csespd(line, p, end) or _phg(line, p, end) or _rng(line, p, end) or _dfs(line, p, end)


# The parts of ext.area, as (rule, start, end) from its first byte (05).
AREA_PARTS = (("area.type", 0, 1), ("area.lat", 1, 3), ("area.color", 3, 5), ("area.lon", 5, 7))


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


def emit_area(scan, p, end, depth):
    """An ext.area token at p, cut short by end, with one syntax finding at
    its first byte that does not fit and its parts one level deeper as far
    as they are present (05 section 4). Returns its end."""
    e = min(p + 7, end)
    scan.tok("ext.area", p, e, depth)
    bad = area_bad(scan.line, p, end)
    if bad is not None:
        scan.find("ext.area", "syntax", bad)
    for rule, a, b in AREA_PARTS:
        if p + b <= end:
            scan.tok(rule, p + a, p + b, depth + 1)
    return e


_BRG = re.compile(rb"/([0-9]{3})/[0-9]{3}")


def brgnrq_shape(line, p, end):
    """The bearing of an 8-byte ext.brgnrq shape at p, or None."""
    m = _BRG.match(line, p, end)
    return int(m.group(1)) if m else None


def brgnrq_after(scan, p, end, depth):
    """Bearing and NRQ directly after an ext.csespd outside a DF report, as
    7.4 reads them: bytes of the shape with a bearing of at most 360 are an
    ext.brgnrq token with an ambiguous finding at its first byte. Returns
    where the comment starts."""
    brg = brgnrq_shape(scan.line, p, end)
    if brg is None or brg > 360:
        return p
    scan.tok("ext.brgnrq", p, p + 8, depth)
    scan.find("ext.brgnrq", "ambiguous", p)
    return p + 8


def emit_ext(scan, x, depth):
    scan.tok(x.rule, x.start, x.start + x.n, depth)
    for f in x.findings:
        scan.find(*f)


# --- Comment (02 section 8) ---------------------------------------------


def comment_fault(b):
    """The offset in b of the first byte that breaks the comment's byte set
    (02 section 8.1), or None: a byte that is not part of well-formed UTF-8,
    or the first of the CR and LF bytes that end b. Control bytes elsewhere
    are UTF-8 characters (amb.cmt.bytes)."""
    try:
        b.decode("utf-8")
        bad = None
    except UnicodeDecodeError as e:
        bad = e.start
    i = len(b)
    while i and b[i - 1] in (0x0A, 0x0D):
        i -= 1
    if i < len(b) and (bad is None or i < bad):
        bad = i
    return bad


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
    if letter:
        # Upper case with a non-digit, or one SP beside a precision byte, is
        # no form of p. 36/22: text.
        return None
    if is_b91(d) and (a == SP and o == SP or is_b91(a) and is_b91(o)):
        # A datum whose precision mode, or whose meaning, is not given.
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


def altitudes(scan, s, e, d, skip=None):
    """cmt.alt and cmt.alt.neg in line[s:e]; returns the spans of the
    well-formed occurrences, as (rule, start, end).

    A '/A=' run that stops fitting its form keeps a token up to its last
    fitting byte, with its syntax finding at the first byte that does not
    fit; it is not an occurrence for the repetition rule
    (amb.cmt.alt.malformed). A '/A=' inside skip, the (start, end) of a
    base-91 telemetry block, is the block's (07 section 3)."""
    line = scan.line
    occ = []
    i = line.find(b"/A=", s, e)
    while i >= 0:
        if skip is not None and skip[0] <= i < skip[1]:
            i = line.find(b"/A=", i + 1, e)
            continue
        j = i + 3
        neg = j < e and line[j] == 0x2D
        rule = "cmt.alt.neg" if neg else "cmt.alt"
        k = j + 1 if neg else j
        q = k
        while q < k + (5 if neg else 6) and q < e and line[q] in DIGITS:
            q += 1
        scan.tok(rule, i, q, d)
        if q == i + 9:
            # The width is fixed: a digit after it is text (amb.cmt.alt.width).
            occ.append((rule, i))
        else:
            scan.find(rule, "syntax", q)
        i = line.find(b"/A=", i + 1, e)
    if len(occ) > 1:
        for rule, i in occ:
            scan.find(rule, "ambiguous", i)
    return [(rule, i, i + 9) for rule, i in occ]


def text_spans(s, e, block):
    """line[s:e] less the span block, as a list of (start, end)."""
    if block is None:
        return [(s, e)]
    return [(a, b) for a, b in ((s, block[0]), (block[1], e)) if a < b]


def past_chars(line, s, end, limit, skip=()):
    """The offset of the first character of line[s:end] past limit counted
    characters, or None. Each byte that is not a UTF-8 continuation byte
    starts a character (amb.cmt.length); the bytes of the spans in skip,
    sorted by start, are not counted."""
    if end - s <= limit:
        # A character has at least one byte.
        return None
    n = 0
    spans = iter(skip)
    nxt = next(spans, None)
    i = s
    while i < end:
        if nxt is not None and i >= nxt[0]:
            i = max(i, nxt[1])
            nxt = next(spans, None)
            continue
        if not 0x80 <= line[i] <= 0xBF:
            if n == limit:
                return i
            n += 1
        i += 1
    return None


def comment(scan, s, end, depth, limit, limit_rule, b91=True, freq=True, dao=True, extra=(), start_cse=False):
    """cmt.text from s to end with the items of 02 section 8.2.

    Each item is looked for only in the fields that 02 section 8.2 lists, so
    the caller says which: b91 searches base-91 telemetry (07), freq looks
    for a frequency at the start (09 section 7), dao looks for DAO
    candidates. The altitude and '!x!' are always looked for. limit and
    limit_rule are the format's length limit, in characters, and the rule
    that reports it. extra holds (rule, start, end) of items the format
    itself found in the comment and has tokenized, for amb.cmt.overlap.
    With start_cse the comment directly follows a compressed block, and a
    form of step 3 of 7.1 at its start is that extension
    (amb.ext.compressed): its token comes first, at depth, and the comment
    after it may hold 36 characters. The bytes of a base-91 telemetry block
    belong to the block: no other item is looked for inside it (07 section
    3)."""
    line = scan.line
    if start_cse and s < end:
        x = step3(line, s, end)
        if x is not None and x.clean():
            emit_ext(scan, x, depth)
            scan.find(x.rule, "ambiguous", s)
            s += x.n
            limit = 36
    if s >= end:
        return
    scan.tok("cmt.text", s, end, depth)
    bad = comment_fault(line[s:end])
    if bad is not None:
        scan.find("cmt.text", "syntax", s + bad)
    d = depth + 1
    # The block is found first, with every DAO candidate, since one may
    # follow it; the other searches leave its bytes alone (07 section 3).
    daos = dao_candidates(line, s, end) if dao else []
    span = b91_span(line, s, end, daos) if b91 else None
    if span is not None:
        daos = [(i, k) for i, k in daos if not span[0] <= i < span[1]]
    items = altitudes(scan, s, end, d, span)

    for i, k in daos:
        scan.tok("cmt.dao", i, i + 5, d)
        if k:
            scan.find("cmt.dao", k, i)
        items.append(("cmt.dao", i, i + 5))
    if len(daos) > 1:
        # amb.cmt.dao: a reading that keeps one candidate reads the others as text.
        for i, _ in daos:
            scan.find("cmt.dao", "ambiguous", i)

    if span is not None:
        b91_block(scan, s, end, d, daos, span)
        items.append(("tlm.b91",) + span)

    noarchive_in(scan, s, end, d, span)
    items.extend(extra)
    item_overlaps(scan, items)

    # err.cmt.daolimit: the DAO may go beyond the limit, so its bytes are not counted.
    past = past_chars(line, s, end, limit, [(i, i + 5) for i, _ in daos])
    if past is not None:
        scan.find(limit_rule, "value", past)

    if freq:
        # 09 section 7, after every syntax or value finding of the comment,
        # which its ambiguous findings defer to. other.py builds on this
        # module, so it is imported here.
        from qua_network.legacy.other import frequency

        frequency(scan, s, end, d)


def _item(rule):
    return "cmt.alt" if rule.startswith("cmt.alt") else rule


def item_overlaps(scan, items):
    """Occurrences of two different items that overlap: an ambiguous finding
    on each (amb.cmt.overlap). '!x!' marks the packet and claims no bytes, so
    it takes no part. items holds (rule, start, end) and is sorted in
    place."""
    items.sort(key=lambda t: t[1])
    for a in range(len(items)):
        ra, sa, ea = items[a]
        if ra == "cmt.noarchive":
            continue
        for b in range(a + 1, len(items)):
            rb, sb, _ = items[b]
            if sb >= ea:
                break
            if rb != "cmt.noarchive" and _item(ra) != _item(rb):
                scan.find(ra, "ambiguous", sa)
                scan.find(rb, "ambiguous", sb)


def noarchive_in(scan, s, e, d, skip=None):
    """cmt.noarchive tokens in the free-text field line[s:e]; returns their
    spans. A match inside skip, the span of a base-91 telemetry block, lies
    outside free text (amb.cmt.noarchive)."""
    line = scan.line
    out = []
    i = line.find(b"!x!", s, e)
    while i >= 0:
        if skip is None or not skip[0] <= i < skip[1]:
            scan.tok("cmt.noarchive", i, i + 3, d)
            out.append(("cmt.noarchive", i, i + 3))
        i = line.find(b"!x!", i + 1, e)
    return out
