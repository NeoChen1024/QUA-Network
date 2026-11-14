# SPDX-License-Identifier: Apache-2.0
"""Position, DF, locator and NMEA reports: docs/legacy/03-position.md."""

from qua_network.legacy.fields import (
    CMP_TABLE,
    DIGITS,
    LOWER,
    UPPER,
    altitudes,
    area_bad,
    brgnrq_after,
    brgnrq_shape,
    cmp_block,
    comment,
    comment_fault,
    emit_area,
    emit_ext,
    item_overlaps,
    lat,
    lon,
    missing,
    noarchive_in,
    step3,
    sym_code,
    sym_table,
    timestamp7,
)
from qua_network.legacy.model import Scan
from qua_network.legacy.weather import complete as weather_complete
from qua_network.legacy.weather import storm as weather_storm


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
    if line[start] in b"/@":
        if missing(scan, "pos.time", p, end):
            return
        # Always the 7 bytes the layout fixes: time.mdhm is not looked for here.
        p, ok = timestamp7(scan, p, end, depth)
        if not ok:
            return
    if missing(scan, "pos.form", p, end):
        return
    c = line[p]
    if c in DIGITS:
        _uncompressed(scan, start, p, end, depth)
    elif c in CMP_TABLE:
        _compressed(scan, start, p, end, depth)
    else:
        scan.find("pos.form", "syntax", p)
        scan.residue(p, end, depth, "pos.form")


def _uncompressed(scan, start, p, end, depth):
    line = scan.line
    p, ok, level = lat(scan, p, end, depth)
    if not ok or missing(scan, "sym.table", p, end):
        return
    sym_table(scan, p, depth)
    table = line[p]
    p, ok, _ = lon(scan, p + 1, end, depth, level)
    if not ok or missing(scan, "sym.code", p, end):
        return
    sym_code(scan, p, depth)
    code = line[p]
    p += 1
    if code == 0x5F and p < end:
        _to_weather(scan, start, p, end, depth)
        return

    # The extension slot (02 section 7.1).
    if _area_symbol(table, code) and area_bad(line, p, end) is None:
        # amb.pos.ext: p. 45/27 lets the area descriptor follow position data.
        emit_area(scan, p, end, depth)
        scan.find("ext.area", "ambiguous", p)
        comment(scan, p + 7, end, depth, 36, "pos.cmt")
        return
    x = step3(line, p, end)
    if x is None:
        comment(scan, p, end, depth, 43, "pos.cmt")
        return
    emit_ext(scan, x, depth)
    p += x.n
    limit, limit_rule = 36, "pos.cmt"
    if code == 0x40 and x.rule == "ext.csespd":
        # Storm data (06 section 8) under any table byte, overlays included
        # (p. 125/101); storm() leaves bytes that are not storm data alone.
        q = weather_storm(scan, p, end, depth)
        if q > p:
            comment(scan, q, end, depth, limit, limit_rule)
            return

    # Bearing and NRQ (02 section 7.4, 03 section 3).
    df_sym = table == 0x2F and code == 0x5C
    if df_sym:
        brg = brgnrq_shape(line, p, end)
        if brg is not None and (x.rule == "ext.csespd" or brg <= 360):
            scan.tok("ext.brgnrq", p, p + 8, depth)
            if x.rule != "ext.csespd":
                # err.df.ext: one side of the document reads these bytes as
                # bearing and NRQ, the other as comment text.
                scan.find("ext.brgnrq", "ambiguous", p)
            elif brg > 360:
                scan.find("ext.brgnrq", "value", p + 1)
            p += 8
            limit, limit_rule = 28, "df.cmt"
    elif x.rule == "ext.csespd":
        # amb.df.detect: p. 45/27 sets no symbol.
        q = brgnrq_after(scan, p, end, depth)
        if q > p:
            p, limit = q, 28

    comment(scan, p, end, depth, limit, limit_rule)


def _area_symbol(table, code):
    """The area object symbol \\l (05 section 4)."""
    return table == 0x5C and code == 0x6C


def _compressed(scan, start, p, end, depth):
    line = scan.line
    wx = end - p > 13 and line[p + 9] == 0x5F
    e = cmp_block(scan, p, end, depth, wx)
    if e is None:
        return
    if wx:
        _to_weather(scan, start, e, end, depth, p)
        return
    if _area_symbol(line[p], line[p + 9]) and area_bad(line, e, end) is None:
        # amb.ext.compressed with the area symbol: step 1 of 02 section 7.1.
        emit_area(scan, e, end, depth)
        scan.find("ext.area", "ambiguous", e)
        comment(scan, e + 7, end, depth, 36, "pos.cmpcmt")
        return
    # An extension at the comment start is read by comment() (amb.ext.compressed);
    # under the area symbol no form of step 3 is tried (02 section 6.5).
    comment(scan, e, end, depth, 40, "pos.cmpcmt", start_cse=not _area_symbol(line[p], line[p + 9]))


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
    # A bearing above 360 is checked whenever its digits are present.
    if e - s >= 3 and (bad is None or bad >= 3) and int(line[s : s + 3]) > 360:
        scan.find("df.agrelo", "value", s)
    if end > s + 5:
        # amb.df.agrelo: the diagram ends after the quality digit.
        scan.residue(s + 5, end, depth, "df.agrelo")
        if bad is None:
            scan.find("df.agrelo", "syntax", s + 5)


# --- Maidenhead locator beacon (03 section 5) ---------------------------

_AR = frozenset(b"ABCDEFGHIJKLMNOPQRabcdefghijklmnopqr")
_AX = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWX")
_AX_ANY = _AX | frozenset(b"abcdefghijklmnopqrstuvwx")
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
    # The subsquare (amb.grid.form, amb.grid.range, amb.grid.case). Followed
    # by ']', two letters close a 6-byte locator, and a letter that fails
    # gives syntax. Without ']', only two upper-case letters A-X are one;
    # other letters start the comment after a 4-byte locator.
    n = 4
    amb = False
    if end - s >= 6 and line[s + 4] in _LETTERS and line[s + 5] in _LETTERS:
        a, b = line[s + 4], line[s + 5]
        if end > s + 6 and line[s + 6] == 0x5D:
            n = 6
            if bad is None and not (a in _AX_ANY and b in _AX_ANY):
                bad = s + 4 if a not in _AX_ANY else s + 5
        elif a in _AX and b in _AX:
            n = 6
            amb = True
    e = min(s + n, end)
    # Lower case gives syntax, at the first lower-case letter when no byte
    # before it fails.
    letters = (s, s + 1, s + 4, s + 5) if n == 6 else (s, s + 1)
    lower = next((i for i in letters if i < e and line[i] in LOWER), None)
    if lower is not None and (bad is None or bad > lower):
        bad = lower
    if e > s:
        scan.tok("grid.loc", s, e, depth)
    if bad is not None:
        scan.find("grid.loc", "syntax", bad)
    if amb and bad is None:
        # A reading that ends the locator after 4 bytes also accepts the field.
        scan.find("grid.loc", "ambiguous", s + 4)
    p = e
    if p < end and line[p] == 0x5D:
        scan.tok("grid.close", p, p + 1, depth)
        p += 1
    if p < end:
        # A comment: the comment byte set, the altitude and '!x!' (03 section 5).
        scan.tok("grid.cmt", p, end, depth)
        f = comment_fault(line[p:end])
        if f is not None:
            scan.find("grid.cmt", "syntax", p + f)
        items = altitudes(scan, p, end, depth + 1)
        items += noarchive_in(scan, p, end, depth + 1)
        item_overlaps(scan, items)


# --- Raw NMEA (03 section 6) --------------------------------------------

_HEX = frozenset(b"0123456789ABCDEF")
_HEX_LOWER = frozenset(b"abcdef")


def nmea(scan, start, end, depth):
    line = scan.line
    s = start + 1
    # nmea.end: CR LF, the NMEA 0183 sentence terminator, closes the field.
    te = end - 2 if end - s >= 2 and line[end - 2 : end] == b"\r\n" else end
    # nmea.len: 25 to 209 bytes after '$', with or without the terminator.
    if not (25 <= end - s <= 209 or 25 <= te - s <= 209):
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
    cks_bad = False
    if p < te and line[p] == 0x2A:
        ce = min(p + 3, te)
        scan.tok("nmea.cks", p, ce, depth)
        h = line[p + 1 : ce]
        if len(h) < 2 or not all(c in _HEX or c in _HEX_LOWER for c in h):
            bad = next((p + 1 + i for i, c in enumerate(h) if c not in _HEX and c not in _HEX_LOWER), ce)
            scan.find("nmea.cks", "syntax", bad)
            cks_bad = True
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
        # amb.nmea.end: bytes after the checksum; a field gives at most one
        # syntax finding.
        scan.residue(p, te, depth, "nmea.cks")
        if not cks_bad:
            scan.find("nmea.cks", "syntax", p)
    if te < end:
        scan.tok("nmea.end", te, end, depth)


def nmea_accepts(line, start, end):
    """Whether the field line[start:end], read as raw NMEA, gives no syntax or
    value finding of its own (amb.dti.shared)."""
    scratch = Scan(line)
    nmea(scratch, start, end, 0)
    return not any(f.kind in ("syntax", "value") for f in scratch.findings)
