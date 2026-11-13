# SPDX-License-Identifier: Apache-2.0
"""Weather reports of every form and storm data: docs/legacy/06-weather.md.

read() takes the fields that 01-frame dispatches to 06 (raw and positionless
reports). The position and object readers hand over the bytes after a '_'
position block (complete()) and storm data after an '@' symbol (storm()); the
item and Mic-E readers ask carriers() for the ambiguous finding of
amb.wx.carriers.
"""

from qua_network.legacy.fields import (
    DIGITS,
    LOWER,
    UPPER,
    comment,
    dirspd,
    missing,
    noarchive_outside,
    timestamp8,
)
from qua_network.legacy.model import Scan

_BAD = ("syntax", "value")
_LETTERS = UPPER | LOWER
_TAIL_BYTES = _LETTERS | DIGITS | frozenset(b"-")

# Software codes (section 7): the listed ones, 'w' (err.wx.software-case) and
# the four of err.wx.unit-length.
_SOFTWARE = frozenset(b"dMPSWXwOKBY")
_UNITS = frozenset((b"Dvs", b"HKT", b"PIC", b"RSW", b"U-II", b"U2R", b"U2k", b"U2kr", b"U5", b"Upkm"))

# Elements of section 6.1 by letter, as read outside the leading places: an
# 's' there is snowfall (amb.wx.order).
_ELEMENTS = {
    ord("c"): ("wx.wdir", 3),
    ord("s"): ("wx.snow", 3),
    ord("g"): ("wx.gust", 3),
    ord("t"): ("wx.temp", 3),
    ord("r"): ("wx.rain1h", 3),
    ord("p"): ("wx.rain24h", 3),
    ord("P"): ("wx.rainmid", 3),
    ord("h"): ("wx.hum", 2),
    ord("b"): ("wx.baro", 5),
    ord("L"): ("wx.lum", 3),
    ord("l"): ("wx.lumk", 3),
    ord("#"): ("wx.rawrain", 3),
}
# The leading elements of a positionless report, at fixed places (6.2).
_LEADING = ((ord("c"), "wx.wdir"), (ord("s"), "wx.wspd"), (ord("g"), "wx.gust"), (ord("t"), "wx.temp"))


def _digits(b):
    return len(b) > 0 and all(c in DIGITS for c in b)


# --- Weather data elements (06 section 6) -------------------------------


def _fixed(line, v, end, rule, width):
    """Length of the value at v under the fixed widths of 6.1 (amb.wx.width
    (a) and (c), amb.wx.unknown (a)), or None."""
    if v + width > end:
        return None
    b = line[v : v + width]
    if _digits(b) or b == b"." * width or b == b" " * width:
        return width
    if rule == "wx.temp" and b[0] == 0x2D and _digits(b[1:]):
        return width
    if rule == "wx.snow" and b.count(b".") == 1 and all(c in DIGITS or c == 0x2E for c in b):
        return width
    return None


def _run(line, v, end, rule):
    """Length of the digit run at v (with a sign for temperature), or None."""
    q = v + 1 if rule == "wx.temp" and v < end and line[v] == 0x2D else v
    r = q
    while r < end and line[r] in DIGITS:
        r += 1
    return r - v if r > q else None


def _value_len(line, v, end, rule, width, runs):
    """Length of the value at v. runs selects reading (b) of amb.wx.width,
    which takes the whole digit run after the letter; a value it does not
    lengthen keeps the fixed width, so the readings agree where (a) holds."""
    n = _fixed(line, v, end, rule, width)
    if runs:
        m = _run(line, v, end, rule)
        if m is not None and (n is None or m > n):
            return m
    return n


def _first_bad(b, rule):
    """Offset in the value b of a leading element (6.2), or in a part of
    the wind field (5.1), of the first byte that fails. The first byte selects
    the form, '.' the dots and SP the spaces; any other selects none, and the
    digits (after the sign of a temperature) are the form taken by default
    (README section 3, Forms that can stand at one place). len(b) when the
    bytes present fit and the value is cut short."""
    if not b:
        return 0
    if b[0] in b". ":
        return next((i for i, c in enumerate(b) if c != b[0]), len(b))
    k = 1 if rule == "wx.temp" and b[0] == 0x2D else 0
    return next((i for i in range(k, len(b)) if b[i] not in DIGITS), len(b))


def _value_findings(scan, rule, s, b):
    """Findings on the value b of the element at s. A value finding is at the
    first byte of the value, the first byte at fault (README section 3)."""
    if rule == "wx.wdir" and _digits(b) and int(b) > 360:
        scan.find(rule, "value", s + 1)
    elif rule == "wx.temp" and b[:1] == b"-" and _digits(b[1:]) and int(b[1:]) == 0:
        scan.find(rule, "value", s + 1)
    elif rule == "wx.rawrain":
        # amb.wx.rawrain: the width is this reading's, not the document's.
        scan.find(rule, "unstated", s)


def _element(scan, p, end, depth, rule, n, seen):
    e = p + 1 + n
    scan.tok(rule, p, e, depth)
    _value_findings(scan, rule, p, scan.line[p + 1 : e])
    if rule in seen:
        # 6.2: a field already read in this report.
        scan.find(rule, "unstated", p)
    seen.add(rule)
    return e


def _elements(scan, p, end, depth, seen, runs=False, extra=False):
    """Elements from p up to the first byte that starts none (6.2).

    runs and extra select the other readings of amb.wx.width (b) and
    amb.wx.letters (b). Returns (end of the data, (rule, start) of the last
    element or None)."""
    line = scan.line
    last = None
    while p < end:
        c = line[p]
        el = _ELEMENTS.get(c)
        if el is not None:
            rule, width = el
            n = _value_len(line, p + 1, end, rule, width, runs)
        elif extra and c in _LETTERS:
            # An undefined letter and its digits as an extra element.
            rule, n = "wx.extra", _run(line, p + 1, end, None)
        else:
            break
        if n is None:
            break
        last = (rule, p)
        p = _element(scan, p, end, depth, rule, n, seen)
    return p, last


def _data(scan, p, end, depth, positionless, wind=True):
    """Weather data from p, then the tail; positionless selects the leading
    elements of a positionless report (6.2). wind tells a complete report
    whether its wind field matched and so has read c and s."""
    line = scan.line
    last = None
    if positionless:
        seen = set()
        for letter, rule in _LEADING:
            if p >= end or line[p] != letter:
                # A place without its letter is a missing element (6.2): the
                # finding is where it was expected, no byte is used, and the
                # next place is the same byte.
                scan.missing(rule, p)
                continue
            n = _fixed(line, p + 1, end, rule, 3)
            if n is None:
                # The letter fixes a 4-byte field: it keeps its token, with one
                # finding at the first byte that fails.
                e = min(p + 4, end)
                scan.tok(rule, p, e, depth)
                scan.find(rule, "syntax", p + 1 + _first_bad(line[p + 1 : e], rule))
                seen.add(rule)
                if e < p + 4:
                    return
                p = e
                continue
            last = (rule, p)
            p = _element(scan, p, end, depth, rule, n, seen)
    else:
        # No leading elements; a wind field that matched stands for c and s
        # (section 5), so a 'c' element repeats it (6.2).
        seen = {"wx.wdir", "wx.wspd"} if wind else set()
    q, more = _elements(scan, p, end, depth, seen)
    last = more or last
    first = _tail(scan, q, end, depth)
    if first is not None and first != "residue":
        _tail_ambiguities(scan, q, end, last, first)


# --- Software and unit codes (06 section 7) -----------------------------


def _sw(scan, q, depth):
    scan.tok("wx.sw", q, q + 1, depth)
    c = scan.line[q]
    if c not in _LETTERS:
        scan.find("wx.sw", "syntax", q)
    elif c not in _SOFTWARE:
        scan.find("wx.sw", "unstated", q)


def _tail(scan, q, end, depth):
    """The tail line[q:end]. Returns the rule of its first token, "residue"
    when it is not a tail (amb.wx.comment), or None when it is empty."""
    if q >= end:
        return None
    line = scan.line
    b = line[q:end]
    n = len(b)
    if n > 5 or any(c not in _TAIL_BYTES for c in b):
        scan.residue(q, end, depth, "wx.unit", fault=True)
        return "residue"
    if n == 1:
        _sw(scan, q, depth)
        return "wx.sw"
    split = n == 5
    two_ways = n in (3, 4) and b[0] in _LETTERS
    if two_ways:
        # amb.wx.tail: the tail splits two ways; the listed codes choose.
        if b[1:] in _UNITS:
            split = True
        elif b in _UNITS:
            split = False
        else:
            split = b[0] in _SOFTWARE
    first = "wx.sw" if split else "wx.unit"
    # Precedence: a syntax or value finding on the tail's bytes, a missing
    # field placed at its first byte included, is given alone. The finding is
    # on the rule of the first token (README section 3, Placing a finding).
    if two_ways and not any(f.kind in _BAD and q <= f.offset <= end for f in scan.findings):
        scan.find(first, "ambiguous", q)
    if split:
        _sw(scan, q, depth)
        scan.tok("wx.unit", q + 1, end, depth)
    else:
        scan.tok("wx.unit", q, end, depth)
    return first


def _alt_accepts(scan, s, end, runs=False, extra=False):
    """Whether the bytes from s, read as elements under another reading and
    then as a tail, give no syntax or value finding of their own."""
    scratch = Scan(scan.line)
    q, _ = _elements(scratch, s, end, 0, set(), runs, extra)
    _tail(scratch, q, end, 0)
    # A finding of the same kind at the same offset is shared; the rule ID is
    # not compared (README section 3).
    mine = {(f.kind, f.offset) for f in scan.findings}
    return not any(f.kind in _BAD and (f.kind, f.offset) not in mine for f in scratch.findings)


def _tail_ambiguities(scan, q, end, last, first):
    """amb.wx.width and amb.wx.letters: another reading would end the data
    at a different byte. The finding is at the first byte of the tail, on
    the rule of its first token, which this reading gives that byte."""
    line = scan.line
    if any(f.kind in _BAD and q <= f.offset <= end for f in scan.findings):
        return  # Precedence: the tail already has its finding.
    c = line[q]
    digit_next = q + 1 < end and line[q + 1] in DIGITS
    # A temperature that (b) reads with its sign: 't', '-' and a digit.
    signed = c == 0x74 and q + 2 < end and line[q + 1] == 0x2D and line[q + 2] in DIGITS
    if c in DIGITS:
        # (b) of amb.wx.width would lengthen a last value written in digits.
        if last is not None:
            _, s = last
            v = line[s + 1 : q]
            if (_digits(v) or v[:1] == b"-" and _digits(v[1:])) and _alt_accepts(scan, s, end, runs=True):
                scan.find(first, "ambiguous", q)
    elif c in _ELEMENTS and (digit_next or signed):
        # (b) of amb.wx.width would read a letter with fewer digits than its
        # width as that element.
        if _alt_accepts(scan, q, end, runs=True):
            scan.find(first, "ambiguous", q)
    elif c in _LETTERS and digit_next:
        # (b) of amb.wx.letters would read an undefined letter and its digits
        # as an extra element.
        if _alt_accepts(scan, q, end, extra=True):
            scan.find(first, "ambiguous", q)


# --- Raw and positionless reports (06 sections 3 and 4) -----------------


def read(scan, start, end, depth):
    """A field that 01-frame dispatches to 06 by its identifier byte."""
    if scan.line[start] == 0x5F:
        _positionless(scan, start, end, depth)
    else:
        _raw(scan, start, end, depth)
    noarchive_outside(scan, start, end, [])


def _raw(scan, start, end, depth):
    c = scan.line[start]
    p = start + 1
    if c == 0x21:
        scan.tok("wx.raw.ultlog", p, p + 1, depth)
        p += 1
    elif c == 0x24:
        scan.tok("wx.raw.ultpkt", p, p + 4, depth)
        p += 4
    if p < end:
        scan.tok("wx.raw.data", p, end, depth)
    else:
        scan.find("wx.raw.data", "syntax", end)


def _positionless(scan, start, end, depth):
    p = start + 1
    if missing(scan, "time.mdhm", p, end):
        return
    p, ok = timestamp8(scan, p, end, depth)
    if ok:
        _data(scan, p, end, depth, True)


# --- Complete weather reports (06 section 5) ----------------------------


def complete(scan, p, end, depth, block=None, obj_cmt=False):
    """The bytes after the position block of a '_' report, from p.

    block is the offset of a compressed block, or None after an uncompressed
    position, where the wind field comes first. obj_cmt marks a compressed
    object, for amb.wx.carriers."""
    line = scan.line
    s = p
    if block is None:
        if p + 3 < end and line[p + 3] == 0x2F:
            wind = _wind(scan, p, end, depth)
            p = min(p + 7, end)
        else:
            # 5.1: without its '/' the wind field is missing; the data is read
            # from the same byte.
            scan.missing("ext.dirspd", p)
            wind = False
    else:
        wind = _cmpwind(scan, block)
    _data(scan, p, end, depth, False, wind)
    if obj_cmt:
        _object_comment(scan, s, end, depth)


def _wind(scan, p, end, depth):
    """The wind field at p, present by its '/' (5.1): a 7-byte ext.dirspd
    token, cut short by end, with one syntax finding at the first byte that
    fails. Returns whether it matches, and so has read c and s (6.2): it
    does when its direction part fits, whatever its speed part."""
    line = scan.line
    e = min(p + 7, end)
    scan.tok("ext.dirspd", p, e, depth)
    x = dirspd(line, p, end)
    if x is not None:
        for f in x.findings:
            # Each part takes the unknown forms of its weather item on its
            # own (5.1), so parts of different kinds give no finding; only
            # a direction above 360 does.
            if f[1] == "value":
                scan.find(*f)
        return True
    matched = True
    for v in (p, p + 4):
        b = line[v : min(v + 3, e)]
        i = _first_bad(b, None)
        if i < len(b) or len(b) < 3:
            scan.find("ext.dirspd", "syntax", v + i)
            matched = v != p
            break
    d = line[p : p + 3]
    if _digits(d) and int(d) > 360:
        # Independent of a fault in the speed (README section 3, Precedence).
        scan.find("ext.dirspd", "value", p)
    return matched


def _cmpwind(scan, block):
    """amb.wx.cmpwind: cs bytes that are not course and speed by 02. Returns
    whether the cs bytes match as the wind field (any kind but step 6)."""
    cs = block + 10
    rule = next((t.rule for t in scan.tokens if t.start == cs and t.rule.startswith("cmp.cs")), None)
    # Precedence: not where the cs or T bytes already have a syntax or value
    # finding.
    reported = any(f.kind in _BAD and cs <= f.offset < cs + 3 for f in scan.findings)
    if rule in ("cmp.cs.none", "cmp.cs.alt", "cmp.cs.rng") and not reported:
        scan.find("cmp.cs", "unstated", cs)
    return rule != "cmp.cs"


def _rule_at(scan, p, depth):
    """The rule of this reading's token at depth that holds the byte p."""
    return next((t.rule for t in scan.tokens if t.depth == depth and t.start <= p < t.end), None)


def _object_comment(scan, s, end, depth):
    """amb.wx.carriers, compressed object: reading (c) takes the bytes after
    the block as obj.cmt (05 section 2, compressed: limit 43)."""
    if any(f.kind in _BAD and s <= f.offset <= end for f in scan.findings):
        return
    scratch = Scan(scan.line)
    comment(scratch, s, end, depth, 43, "obj.cmt", b91=False)
    rule = _rule_at(scan, s, depth)
    if rule is not None and not any(f.kind in _BAD for f in scratch.findings):
        scan.find(rule, "ambiguous", s)


def carriers(scan, p, end, depth, block=None, wind=True):
    """amb.wx.carriers for an item or a Mic-E report with symbol code '_':
    reading (a) reads the bytes from p as weather (sections 5 to 7; for
    Mic-E, wind=False, sections 6 and 7 only). Call it once the report's own
    reading of those bytes is complete: the finding is on the rule of its
    token at depth that holds p (README section 3, Placing a finding)."""
    if any(f.kind in _BAD and p <= f.offset <= end for f in scan.findings):
        return  # Precedence
    scratch = Scan(scan.line)
    if wind:
        complete(scratch, p, end, 0, block)
    else:
        _data(scratch, p, end, 0, False)
    rule = _rule_at(scan, p, depth)
    if rule is not None and not any(f.kind in _BAD for f in scratch.findings):
        scan.find(rule, "ambiguous", p)


# --- Storm data (06 section 8) ------------------------------------------

_STORM_FIELDS = (
    ("storm.wind", 0x2F, 3),
    ("storm.gust", 0x5E, 3),
    ("storm.press", 0x2F, 4),
    ("storm.rhurr", 0x3E, 3),
    ("storm.rts", 0x26, 3),
    ("storm.rgale", 0x25, 3),
)


def storm(scan, p, end, depth):
    """Storm data at p, where the caller found '/' and a storm type after the
    ext.csespd of a \\@ or /@ report (the table byte is matched, README
    section 3, Symbols that a format names). Returns where the comment of the
    carrying format starts."""
    line = scan.line
    scan.tok("storm.type", p, p + 3, depth)
    p += 3
    for rule, mark, n in _STORM_FIELDS:
        if p >= end or line[p] != mark:
            # No marker: a required field is missing, the storm data ends and
            # the bytes from p are the comment.
            if rule != "storm.rgale":
                scan.find(rule, "syntax", p)
            return p
        # The marker fixes a field of fixed width: it keeps its token, with
        # one syntax finding at the first byte that fails (README section 3).
        # Unknown fill is no form of these fields.
        e = min(p + 1 + n, end)
        scan.tok(rule, p, e, depth)
        b = line[p + 1 : e]
        bad = next((i for i, c in enumerate(b) if c not in DIGITS), None)
        if bad is None and e < p + 1 + n:
            bad = len(b)
        if bad is not None:
            scan.find(rule, "syntax", p + 1 + bad)
        if e < p + 1 + n:
            return e  # Cut short by the end of the field: reading stops.
        p = e
    return p


def storm_overlay(scan, p, end, read_comment):
    """Section 8: an overlaid '@' report whose bytes from p this reading took
    as the comment. The wider reading of README section 3 (Symbols that a
    format names) reads storm data there, then the comment through
    read_comment(scratch, start). Call it once this reading is complete: the
    finding is on cmt.text at the '/' of the storm type, given only where the
    wider reading has no syntax or value finding of its own and this reading
    none on the bytes from p, such as a comment over its limit (Precedence)."""
    if any(f.kind in _BAD and p <= f.offset <= end for f in scan.findings):
        return
    scratch = Scan(scan.line)
    q = storm(scratch, p, end, 0)
    read_comment(scratch, q)
    mine = {(f.kind, f.offset) for f in scan.findings}
    if any(f.kind in _BAD and (f.kind, f.offset) not in mine for f in scratch.findings):
        return
    scan.find("cmt.text", "ambiguous", p)
