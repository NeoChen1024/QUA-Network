# SPDX-License-Identifier: Apache-2.0
"""Position, DF, locator and NMEA reports: docs/legacy/03-position.md."""

import re

from qua_network.legacy.fields import (
    CMP_TABLE,
    DIGITS,
    LOWER,
    UPPER,
    area_literal,
    brgnrq_shape,
    cmp_block,
    comment,
    csespd_mixed,
    emit_ext,
    lat,
    lon,
    missing,
    noarchive_in,
    noarchive_outside,
    step3,
    sym_code,
    sym_table,
    timestamp7,
)
from qua_network.legacy.model import Scan
from qua_network.legacy.weather import complete as weather_complete
from qua_network.legacy.weather import storm as weather_storm

_STORM = re.compile(rb"/(?:TS|HC|TD)")


def _to_weather(scan, start, p, end, depth, block=None):
    """pos.wx: the bytes after the position block are 06's (wx.pos)."""
    scan.retag(start, depth, "wx.pos")
    weather_complete(scan, p, end, depth, block)


def read(scan, start, end, depth):
    """Dispatch a 03-position field by its identifier byte."""
    c = scan.line[start]
    if c == 0x25:
        agrelo(scan, start, end, depth)
    elif c == 0x5B:
        grid(scan, start, end, depth)
    elif c == 0x24:
        nmea(scan, start, end, depth)
    else:
        position(scan, start, end, depth)


# --- Position and DF reports (03 sections 2 and 3) ----------------------


def position(scan, start, end, depth):
    line = scan.line
    p = start + 1
    texts = []
    if line[start] in b"/@":
        if missing(scan, "pos.time", p, end):
            return
        # Always the 7 bytes the layout fixes: time.mdhm is not recognised
        # here (README section 3, Obsolete and nested forms).
        p, ok = timestamp7(scan, p, end, depth)
        if not ok:
            return
    if missing(scan, "pos.form", p, end):
        return
    c = line[p]
    if c in DIGITS:
        cmt = _uncompressed(scan, start, p, end, depth)
    elif c in CMP_TABLE:
        cmt = _compressed(scan, start, p, end, depth)
    else:
        scan.find("pos.form", "syntax", p)
        scan.residue(p, end, depth, "pos.form")
        cmt = None
    if cmt is not None:
        texts.append((cmt.start, cmt.end))
    noarchive_outside(scan, start, end, texts)


def _uncompressed(scan, start, p, end, depth):
    line = scan.line
    p, ok, level = lat(scan, p, end, depth)
    if not ok or missing(scan, "sym.table", p, end):
        return None
    sym_table(scan, p, depth)
    table = line[p]
    p, ok, _ = lon(scan, p + 1, end, depth, level)
    if not ok or missing(scan, "sym.code", p, end):
        return None
    sym_code(scan, p, depth)
    code = line[p]
    p += 1
    if code == 0x5F and p < end:
        _to_weather(scan, start, p, end, depth)
        return None

    # The extension slot (02 section 7.1, step 3; amb.pos.ext).
    slot = p
    x = step3(line, p, end)
    # Runs that this reading takes as comment text carry their finding on
    # cmt.text (README section 3, Placing a finding).
    if area_literal(line, p, end):
        scan.find("cmt.text", "ambiguous", p)  # amb.ext.area
    if x is None:
        q = csespd_mixed(line, p, end)
        if q is not None:
            scan.find("cmt.text", "ambiguous", q)  # amb.ext.csespd
    else:
        emit_ext(scan, x, depth)
        p += x.n
        if code == 0x40 and x.rule == "ext.csespd" and _STORM.match(line, p, end):
            # Storm data (06 section 8), then the comment; it does not follow the
            # slot's extension, so no course and speed is looked for at its start.
            p = weather_storm(scan, slot - 11, p, end, depth)
            return comment(scan, p, end, depth, 36, "pos.cmt", start_cse=False)

    # Bearing and NRQ (02 section 7.4, 03 section 3).
    limit, limit_rule = (36, "pos.cmt") if x else (43, "pos.cmt")
    if x is not None:
        brg = brgnrq_shape(line, p, end)
        df_sym = table == 0x2F and code == 0x5C
        df_ext = x.rule == "ext.csespd"
        if brg is not None and df_sym and df_ext:
            scan.tok("ext.brgnrq", p, p + 8, depth)
            if brg > 360:
                scan.find("ext.brgnrq", "value", p + 1)
            p += 8
            limit, limit_rule = 28, "df.cmt"
        elif brg is not None and df_sym != df_ext and brg <= 360:
            scan.find("df.notdf", "ambiguous", p)

    cmt = comment(scan, p, end, depth, limit, limit_rule)
    if x is not None and x.h_alpha:
        # amb.ext.phg: reading (b) takes the extension as comment text, within
        # the limit without an extension (43).
        # After ext.phgr, (b)'s length finding falls on another byte than
        # this reading's, so it is (b)'s own (README section 3).
        rest = cmt.counted if cmt else 0
        if x.rule != "ext.phgr" or x.n + rest <= 43:
            scan.find(x.rule, "ambiguous", slot)
    return cmt


def _compressed(scan, start, p, end, depth):
    line = scan.line
    wx = end - p > 13 and line[p + 9] == 0x5F
    e = cmp_block(scan, p, end, depth, wx)
    if e is None:
        return None
    if wx:
        _to_weather(scan, start, e, end, depth, p)
        return None
    # amb.pos.cmpext: a clean extension at the comment start is reported by
    # the search of comment(), at the same byte and rule.
    return comment(scan, e, end, depth, 40, "pos.cmpcmt")


# --- Agrelo DF (03 section 4) -------------------------------------------

_AGRELO = (DIGITS, DIGITS, DIGITS, frozenset(b"/"), DIGITS)


def agrelo(scan, start, end, depth):
    line = scan.line
    s = start + 1
    e = min(s + 5, end)
    if e > s:
        scan.tok("df.agrelo", s, e, depth)
    bad = next((i for i in range(e - s) if line[s + i] not in _AGRELO[i]), None)
    if bad is not None:
        scan.find("df.agrelo", "syntax", s + bad)
    elif e < s + 5:
        scan.find("df.agrelo", "syntax", e)
    # The range the unit implies: a bearing above 360 is a value finding at
    # its first digit, an independent defect beside any syntax finding.
    if e - s >= 3 and (bad is None or bad >= 3) and int(line[s : s + 3]) > 360:
        scan.find("df.agrelo", "value", s)
    if end > s + 5:
        scan.residue(s + 5, end, depth, "df.agrelo")
        if bad is None:
            scan.find("df.agrelo", "syntax", s + 5)
    noarchive_outside(scan, start, end, [])


# --- Maidenhead locator beacon (03 section 5) ---------------------------

_AR = frozenset(b"ABCDEFGHIJKLMNOPQRabcdefghijklmnopqr")
_AX = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXabcdefghijklmnopqrstuvwx")
_LETTERS = UPPER | LOWER


def grid(scan, start, end, depth):
    line = scan.line
    s = start + 1
    # The first four bytes: two letters A-R (either case), two digits.
    e4 = min(s + 4, end)
    bad = None
    for i in range(e4 - s):
        c = line[s + i]
        ok = c in _AR if i < 2 else c in DIGITS
        if not ok:
            bad = s + i
            break
    if bad is None and e4 < s + 4:
        bad = e4
    # The subsquare (amb.grid.form, amb.grid.range).
    n = 4
    closed = in_range = False
    if end - s >= 6 and line[s + 4] in _LETTERS and line[s + 5] in _LETTERS:
        a, b = line[s + 4], line[s + 5]
        closed = end > s + 6 and line[s + 6] == 0x5D
        in_range = a in _AX and b in _AX
        if closed or in_range:
            n = 6
        if closed and not in_range and bad is None:
            bad = s + 4 if a not in _AX else s + 5
    e = min(s + n, end)
    # Without ']', reading (b) of amb.grid.form ends an in-range locator
    # after 4 bytes. Letters out of range and not closed by ']' are comment
    # text, with no finding (README section 3). With ']' every reading takes
    # six bytes. A lower-case subsquare is at fault under this reading, and
    # its syntax finding alone is given (Precedence); a fault in the first
    # four bytes, lower case among them, is at fault under both readings and
    # does not suppress the finding (Which findings are the other reading's
    # own).
    amb = not closed and in_range and not (line[s + 4] in LOWER or line[s + 5] in LOWER)
    # Lower case is recognised and gives syntax, at the first lower-case
    # letter when no byte before it fails (amb.grid.case; README section 3,
    # Letter case).
    letters = (s, s + 1, s + 4, s + 5) if n == 6 else (s, s + 1)
    lower = next((i for i in letters if i < e and line[i] in LOWER), None)
    if lower is not None and (bad is None or bad > lower):
        bad = lower
    if e > s:
        scan.tok("grid.loc", s, e, depth)
    if bad is not None:
        scan.find("grid.loc", "syntax", bad)
    if amb:
        scan.find("grid.loc", "ambiguous", s + 4)
    p = e
    if p < end and line[p] == 0x5D:
        scan.tok("grid.close", p, p + 1, depth)
        p += 1
    texts = []
    if p < end:
        scan.tok("grid.cmt", p, end, depth)
        noarchive_in(scan, p, end, depth + 1)
        texts.append((p, end))
    noarchive_outside(scan, start, end, texts)


# --- Raw NMEA (03 section 6) --------------------------------------------

_HEX = frozenset(b"0123456789ABCDEF")
_HEX_LOWER = frozenset(b"abcdef")
_END = re.compile(rb"(?:\r\n|\n\r|\r|\n)\Z")


def nmea(scan, start, end, depth):
    line = scan.line
    s = start + 1
    m = _END.search(line, s, end)
    te = m.start() if m else end
    n = te - s
    if not 25 <= n <= 209:
        scan.find("nmea.len", "value", start)
    # Address field: up to the first ',' or '*'.
    p = s
    while p < te and line[p] not in b",*":
        p += 1
    if p > s:
        scan.tok("nmea.addr", s, p, depth)
    bad = next((i for i in range(s, min(p, s + 5)) if line[i] not in UPPER), None)
    if bad is None and p != s + 5:
        bad = min(p, s + 5)
    if bad is not None:
        scan.find("nmea.addr", "syntax", bad)
    # Data fields.
    nf = 0
    while p < te and line[p] == 0x2C:
        q = p + 1
        while q < te and line[q] not in b",*":
            q += 1
        scan.tok("nmea.field", p, q, depth)
        for i in range(p + 1, q):
            c = line[i]
            if not 0x20 <= c <= 0x7E or c == 0x24:
                scan.find("nmea.field", "syntax", i)
                break
        nf += 1
        p = q
    if nf == 0:
        scan.find("nmea.field", "syntax", p)
    # Checksum.
    if p < te and line[p] == 0x2A:
        ce = min(p + 3, te)
        scan.tok("nmea.cks", p, ce, depth)
        h = line[p + 1 : ce]
        if len(h) < 2 or not all(c in _HEX or c in _HEX_LOWER for c in h):
            bad = next((p + 1 + i for i, c in enumerate(h) if c not in _HEX and c not in _HEX_LOWER), ce)
            scan.find("nmea.cks", "syntax", bad)
        else:
            if any(c in _HEX_LOWER for c in h):
                scan.find("nmea.cks", "unstated", p + 1)
            x = 0
            for c in line[s:p]:
                x ^= c
            if x != int(h, 16):
                scan.find("nmea.cks", "value", p + 1)
        p = ce
    if p < te:
        # Bytes after the checksum, or a '*' field, that no rule reads.
        scan.residue(p, te, depth, "nmea.cks")
        scan.find("nmea.cks", "syntax", p)
    if m:
        scan.tok("nmea.end", te, end, depth)
        scan.find("nmea.end", "unstated", te)
    noarchive_outside(scan, start, end, [])


def nmea_accepts(line, start, end):
    """Whether the field line[start:end], read as raw NMEA, gives no syntax or
    value finding of its own (amb.dti.shared)."""
    scratch = Scan(line)
    nmea(scratch, start, end, 0)
    return not any(f.kind in ("syntax", "value") for f in scratch.findings)
