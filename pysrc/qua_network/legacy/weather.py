# SPDX-License-Identifier: Apache-2.0
"""Weather reports of every form and storm data: docs/legacy/06-weather.md.

read() takes the fields that 01-frame dispatches to 06 (raw and positionless
reports). The position and object readers hand over the bytes after a '_'
position block (complete()) and storm data after an '@' symbol (storm()).
"""

from qua_network.legacy.fields import DIGITS, comment, missing, timestamp8

_FILL = frozenset(b". ")

# Software codes (section 7): the listed codes and 'w' (err.wx.software-case).
# The list names software and is open: another byte is unstated.
_SOFTWARE = frozenset(b"dMPSWXw")
# The 1-byte unit codes of the unit list (err.wx.unit-length).
_UNIT1 = frozenset(b"OKBY")
# The weather comment has no stated length limit (section 7).
_NO_LIMIT = float("inf")

# Elements of section 6.1 with a stated width, by letter, as read outside the
# leading places: an 's' there is snowfall (amb.wx.order). '#' has no stated
# width, so it never completes an element and ends the data (amb.wx.rawrain).
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
}
# The leading elements of a positionless report, at fixed places (6.2).
_LEADING = ((ord("c"), "wx.wdir"), (ord("s"), "wx.wspd"), (ord("g"), "wx.gust"), (ord("t"), "wx.temp"))


# --- Values (06 section 6.1) --------------------------------------------


def _fill_bad(b):
    """First byte of b that is neither '.' nor SP (amb.wx.unknown)."""
    return next((i for i, c in enumerate(b) if c not in _FILL), len(b))


def _num_bad(b, signed):
    """First byte of b that leaves the number: digits with at most one '.'
    (amb.wx.width), after a '-' where signed. len(b) when every byte fits."""
    i = 1 if signed and b[:1] == b"-" else 0
    dot = False
    for j in range(i, len(b)):
        c = b[j]
        if c == 0x2E and not dot:
            dot = True
        elif c not in DIGITS:
            return j
    return len(b)


def _first_bad(b, rule):
    """Offset in the value b of the first byte at which every form of a value
    has failed: the unknown fill and the number. len(b) when the bytes fit,
    which for a value cut short is where its next byte was expected."""
    return max(_fill_bad(b), _num_bad(b, rule == "wx.temp"))


def _fits(b, rule):
    """Whether the whole value b is the unknown fill or a number."""
    if b.isdigit() or _fill_bad(b) == len(b):
        return True
    return _num_bad(b, rule == "wx.temp") == len(b) and any(c in DIGITS for c in b)


def _fixed(line, v, end, rule, width):
    """Length of the value at v under the fixed width of 6.1, or None."""
    if v + width > end:
        return None
    return width if _fits(line[v : v + width], rule) else None


def _value_findings(scan, rule, s, b):
    """The ranges of 6.1, at the first byte of the value."""
    if rule == "wx.wdir":
        bad = b.isdigit() and int(b) > 360
    elif rule == "wx.temp":
        bad = b == b"-00"
    else:
        return
    if bad:
        scan.find(rule, "value", s + 1)


# --- Weather data elements (06 section 6) -------------------------------


def _element(scan, p, depth, rule, n, seen):
    """seen holds each rule read in this report."""
    e = p + 1 + n
    scan.tok(rule, p, e, depth)
    _value_findings(scan, rule, p, scan.line[p + 1 : e])
    if rule in seen:
        # 6.2: a field already read in this report.
        scan.find(rule, "unstated", p)
    seen.add(rule)
    return e


def _elements(scan, p, end, depth, seen):
    """Elements from p up to the first byte that starts none (6.2)."""
    line = scan.line
    while p < end:
        el = _ELEMENTS.get(line[p])
        if el is None:
            break
        rule, width = el
        if rule == "wx.hum" and line[p + 1 : p + 4] == b"100" and p + 4 <= end:
            # Section 10, amb.wx.hum100: the field has three digits. The
            # other reading is `h10` and text from the last digit.
            p = _element(scan, p, depth, rule, 3, seen)
            scan.find(rule, "ambiguous", p - 1)
            continue
        n = _fixed(line, p + 1, end, rule, width)
        if n is None:
            break
        p = _element(scan, p, depth, rule, n, seen)
    return p


def _leading_wind(scan, p, end, depth, seen):
    """amb.wx.leading: a complete report with no wind can start its data
    with a c field and, directly after it, an s field that is the wind
    speed. Returns the offset after them."""
    line = scan.line
    if p < end and line[p] == 0x63 and _fixed(line, p + 1, end, "wx.wdir", 3):
        p = _element(scan, p, depth, "wx.wdir", 3, seen)
        if p < end and line[p] == 0x73 and _fixed(line, p + 1, end, "wx.wspd", 3):
            p = _element(scan, p, depth, "wx.wspd", 3, seen)
    return p


def _data(scan, p, end, depth, positionless, wind=True):
    """Weather data from p, then what follows it; positionless selects the
    leading elements of a positionless report (6.2). wind tells a complete
    report whether its wind field has read c and s."""
    line = scan.line
    seen = set()
    if positionless:
        for letter, rule in _LEADING:
            if p >= end or line[p] != letter:
                # A place without its letter is a missing element: the finding
                # is where it was expected, no byte is used, and the next place
                # is the same byte.
                scan.missing(rule, p)
                continue
            e = min(p + 4, end)
            seen.add(rule)
            scan.tok(rule, p, e, depth)
            b = line[p + 1 : e]
            if e < p + 4 or not _fits(b, rule):
                # The letter fixes a 4-byte field: it keeps its token, with one
                # finding at the first byte that fails.
                scan.find(rule, "syntax", p + 1 + _first_bad(b, rule))
                if e < p + 4:
                    return
            else:
                _value_findings(scan, rule, p, b)
            p = e
    elif wind:
        seen.update(("wx.wdir", "wx.wspd"))
    else:
        p = _leading_wind(scan, p, end, depth, seen)
    q = _elements(scan, p, end, depth, seen)
    _after(scan, q, end, depth)


def _after(scan, q, end, depth):
    """The bytes after the weather data, line[q:end] (sections 6.2 and 7):
    1 to 5 bytes are the tail, the more specific reading (amb.wx.tail), and
    more are a comment (amb.wx.comment). The comment has no length limit, and
    only the altitude and '!x!' are looked for in it (section 7)."""
    if q >= end:
        return
    if end - q <= 5:
        _tail(scan, q, end, depth)
    else:
        comment(scan, q, end, depth, _NO_LIMIT, "cmt.text", b91=False, freq=False, dao=False)


# --- Software and unit codes (06 section 7) -----------------------------


def _sw(scan, q, depth):
    scan.tok("wx.sw", q, q + 1, depth)
    if scan.line[q] not in _SOFTWARE:
        scan.find("wx.sw", "unstated", q)


def _tail(scan, q, end, depth):
    """The tail line[q:end] of 1 to 5 bytes. Where it splits two ways, the
    software code and unit is the more specific reading (amb.wx.tail)."""
    line = scan.line
    n = end - q
    c = line[q]
    if n == 1:
        if c in _UNIT1:
            scan.tok("wx.unit", q, end, depth)
        else:
            _sw(scan, q, depth)
    elif n == 5 or (c in _SOFTWARE and (n > 2 or line[q + 1] in _UNIT1)):
        _sw(scan, q, depth)
        scan.tok("wx.unit", q + 1, end, depth)
    else:
        scan.tok("wx.unit", q, end, depth)


# --- Raw and positionless reports (06 sections 3 and 4) -----------------


def read(scan, start, end, depth):
    """A field that 01-frame dispatches to 06 by its identifier byte."""
    if scan.line[start] == 0x5F:
        _positionless(scan, start, end, depth)
    else:
        _raw(scan, start, end, depth)


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
        # The diagram gives the data n bytes and no case of none.
        scan.find("wx.raw.data", "unstated", end)


def _positionless(scan, start, end, depth):
    p = start + 1
    if missing(scan, "time.mdhm", p, end):
        return
    p, ok = timestamp8(scan, p, end, depth)
    if ok:
        _data(scan, p, end, depth, True)


# --- Complete weather reports (06 section 5) ----------------------------


def complete(scan, p, end, depth, block=None):
    """The bytes after the position block of a '_' report, from p.

    block is the offset of a compressed block, or None after an uncompressed
    position, where the wind field comes first."""
    line = scan.line
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


def _wind(scan, p, end, depth):
    """The wind field at p, present by its '/' (5.1): a 7-byte ext.dirspd
    token, cut short by end, with one syntax finding at the first byte that
    fails. Each part takes the forms of the weather item it replaces. Returns
    whether the field has read c and s: it has when its direction part fits."""
    line = scan.line
    e = min(p + 7, end)
    scan.tok("ext.dirspd", p, e, depth)
    matched = True
    for v in (p, p + 4):
        b = line[v : min(v + 3, e)]
        if len(b) < 3 or not _fits(b, None):
            scan.find("ext.dirspd", "syntax", v + _first_bad(b, None))
            matched = v != p
            break
    d = line[p : p + 3]
    if d.isdigit() and int(d) > 360:
        scan.find("ext.dirspd", "value", p)
    return matched


def _cmpwind(scan, block):
    """amb.wx.cmpwind: whether the cs bytes of the compressed block were read
    as the wind, and so have read c and s."""
    cs = block + 10
    return any(t.start == cs and t.rule == "cmp.cs.wind" for t in scan.tokens)


# --- Storm data (06 section 8) ------------------------------------------

_STORM_TYPES = (b"TS", b"HC", b"TD")
_STORM_FIELDS = (
    ("storm.wind", 0x2F, 3),
    ("storm.gust", 0x5E, 3),
    ("storm.press", 0x2F, 4),
    ("storm.rhurr", 0x3E, 3),
    ("storm.rts", 0x26, 3),
    ("storm.rgale", 0x25, 3),
)


def storm(scan, p, end, depth):
    """Storm data at p, directly after the ext.csespd of a report whose
    symbol is '@' under any table byte, overlays included (section 8).

    A storm type of the closed list announces storm data, and the bytes
    after it are read as its parts (amb.storm.placement): a part present by
    its leading byte keeps its fixed-width token, cut short by end, with
    syntax at its first byte that fails; a required part without its leading
    byte is missing, with syntax where it was expected. Without a storm type
    the bytes are the comment. Returns where the comment of the carrying
    format starts."""
    line = scan.line
    if p + 3 > end or line[p] != 0x2F or line[p + 1 : p + 3] not in _STORM_TYPES:
        return p
    scan.tok("storm.type", p, p + 3, depth)
    q = p + 3
    for rule, mark, n in _STORM_FIELDS:
        if q >= end or line[q] != mark:
            if rule != "storm.rgale":
                scan.missing(rule, q)
            continue
        e = min(q + 1 + n, end)
        scan.tok(rule, q, e, depth)
        bad = next((i for i in range(q + 1, e) if line[i] not in DIGITS), None)
        if bad is not None:
            scan.find(rule, "syntax", bad)
        elif e < q + 1 + n:
            # Cut short: the parts after it are missing at the same byte and
            # give no finding of their own.
            scan.missing(rule, e)
        q = e
    return q
