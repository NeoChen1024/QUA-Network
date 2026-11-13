# SPDX-License-Identifier: Apache-2.0
"""Mic-E: docs/legacy/04-mic-e.md.

The reader takes the information field from its identifier byte, whose
token frame.py has already emitted, and the destination callsign through
the dest.mice token of the same packet's header.
"""

import re

from qua_network.legacy.fields import (
    DIGITS,
    SP,
    SYM_TABLE,
    bad_text_bytes,
    dao_candidates,
    emit_ext,
    is_b91,
    lat,
    lon,
    noarchive_in,
    noarchive_outside,
    step3,
    sym_code,
    sym_table,
)
from qua_network.legacy.model import Scan
from qua_network.legacy.other import frequency
from qua_network.legacy.telemetry import b91_block
from qua_network.legacy.weather import carriers as weather_carriers

_BAD = ("syntax", "value")

# --- Destination address (04 section 3) ---------------------------------

_STANDARD = frozenset(b"PQRSTUVWXYZ")
_CUSTOM = frozenset(b"ABCDEFGHIJK")
_ZERO_FLAG = DIGITS | frozenset(b"L")
_SET_ABC = _ZERO_FLAG | _CUSTOM | _STANDARD
_SET_NSW = _ZERO_FLAG | _STANDARD
_BLANK = frozenset(b"KLZ")
_DEST_RULES = ("mice.dest.a", "mice.dest.b", "mice.dest.c", "mice.dest.ns", "mice.dest.lonoff", "mice.dest.we")


def _dest_digit(c):
    """The latitude digit of a destination byte of the table, or None for a blank."""
    if c in _BLANK:
        return None
    if c in DIGITS:
        return c - 0x30
    return c - (0x41 if c in _CUSTOM else 0x50)


def _dest_token(scan, start):
    """The dest.mice token of the header that belongs to the field at start.

    The header of a packet is tokenized just before its information field,
    so the search goes back no further than the separator of an earlier
    packet (the outer one of a third-party payload)."""
    for t in reversed(scan.tokens):
        if t.rule == "dest.mice":
            return t
        if t.rule in ("line.sep", "tp.sep") and t.start != start - 1:
            return None
    return None


def destination(scan, start):
    line = scan.line
    t = _dest_token(scan, start)
    if t is None:
        # 01-frame reports a destination it could not take as an address.
        return
    ds, de, d = t.start, t.end, t.depth + 1
    n = min(6, de - ds)
    digit = [None] * 6
    blank = [False] * 6
    flags = []  # (offset, "s" or "c") of the one bits in bytes 1 to 3
    for i in range(n):
        p = ds + i
        c = line[p]
        rule = _DEST_RULES[i]
        scan.tok(rule, p, p + 1, d)
        if c not in (_SET_ABC if i < 3 else _SET_NSW):
            scan.find(rule, "syntax", p)
            continue
        v = _dest_digit(c)
        if v is None:
            blank[i] = True
            if i < 2:
                scan.find(rule, "syntax", p)
        else:
            digit[i] = v
        if i < 3 and c not in _ZERO_FLAG:
            flags.append((p, "s" if c in _STANDARD else "c"))
    if de - ds < 6:
        scan.find("mice.dest", "syntax", de)
    elif de - ds > 6:
        # Only an address that APRS-IS alone can carry is longer.
        scan.residue(ds + 6, de, d, "mice.dest")
        scan.find("mice.dest", "syntax", ds + 6)

    # Checks on the six bytes together. Blanks run from byte 6 leftwards;
    # those in bytes 1 and 2 are reported by their own rule above.
    for i in range(2, 6):
        if blank[i] and any(v is not None for v in digit[i + 1 :]):
            scan.find("mice.dest", "syntax", ds + i)
    if digit[0] is not None and digit[1] is not None:
        deg = 10 * digit[0] + digit[1]
        if deg > 90:
            scan.find("mice.dest", "value", ds)
        if deg == 90 and any(v for v in digit[2:]):
            scan.find("mice.dest", "value", ds + 2)
    if digit[2] is not None and digit[2] > 5:
        scan.find("mice.dest", "value", ds + 2)
    kinds = {k for _, k in flags}
    if len(kinds) > 1:
        first = flags[0][1]
        scan.find("mice.dest", "value", next(p for p, k in flags if k != first))

    _dest_ssid(scan, t)


def _dest_ssid(scan, t):
    """mice.dest.ssid: a non-zero SSID is a generic path code (obsolete).
    The token stays 01-frame's dest.ssid."""
    i = scan.tokens.index(t)
    if i + 1 >= len(scan.tokens):
        return
    s = scan.tokens[i + 1]
    if s.rule != "dest.ssid" or s.start != t.end or s.depth != t.depth:
        return
    v = scan.line[s.start + 1 : s.end]
    # "-0", a leading zero and values above 15 are addr.ssid's findings.
    if v.isdigit() and not v.startswith(b"0") and int(v) <= 15:
        scan.find("mice.dest.ssid", "obsolete", s.start)


# --- Information field (04 section 4) -----------------------------------

_FIXED = ("mice.lon.deg", "mice.lon.min", "mice.lon.hun", "mice.sp", "mice.dc", "mice.se")


def fixed(scan, start, end, depth):
    """Offsets 1 to 8. Each part is a one-byte token at the level of the
    identifier; a field cut short keeps the parts present."""
    line = scan.line
    for k, rule in enumerate(_FIXED):
        p = start + 1 + k
        if p >= end:
            break
        c = line[p]
        scan.tok(rule, p, p + 1, depth)
        if not 0x1C <= c <= 0x7F:
            scan.find(rule, "syntax", p)
        elif rule == "mice.lon.deg" and c <= 0x25:
            scan.find(rule, "value", p)
        elif rule == "mice.lon.min" and (c <= 0x25 or c >= 0x62):
            scan.find(rule, "value", p)
        elif rule == "mice.dc" and (c - 0x1C) % 10 >= 8:
            scan.find(rule, "value", p)
    if start + 6 < end:
        dc, se = line[start + 5], line[start + 6]
        if 0x1C <= dc <= 0x7F and (dc - 0x1C) % 10 < 8 and 0x1C <= se <= 0x7F:
            if 100 * ((dc - 0x1C) % 10 % 4) + se - 0x1C > 360:
                scan.find("mice.dc", "value", start + 5)
    if start + 7 < end:
        sym_code(scan, start + 7, depth, "mice.sym.code")
    if start + 8 < end:
        scan.tok("mice.sym.table", start + 8, start + 9, depth)
        if line[start + 8] not in SYM_TABLE:
            scan.find("mice.sym.table", "syntax", start + 8)
    if end < start + 9:
        scan.find("mice.fixed", "syntax", end)


# --- Status text (04 section 5) -----------------------------------------

_KENWOOD = frozenset(b">]")
_OTHER = frozenset(b"`'")
_KENWOOD_SUFFIX = frozenset(b"=^&")
_SUFFIX_EXAMPLES = frozenset((b"_(", b"_0", b"_3", b"|3", b"|4"))  # p. 73/55
_HEX = frozenset(b"0123456789ABCDEFabcdef")
# A fifth or sixth byte outside A-X, in either case, is no subsquare letter
# (amb.grid.range); only the 4-byte locator is then tried.
# '/G' closes the locator as ']' closes that of a beacon, so letters out of
# range before it are a locator with a syntax finding (README section 3).
_GRID = re.compile(rb"[A-Za-z]{2}[0-9]{2}(?:[A-Za-z]{2})?/G")
_AR = frozenset(b"ABCDEFGHIJKLMNOPQR")
_AX = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWX")
_ALT_RUN = re.compile(rb"[!-{]{3}\}")
_MARKED = re.compile(rb"(?=PHG|RNG|DFS)")
_POSITION = re.compile(rb"(?=[0-9]{2}[0-9 ]{2}\.[0-9 ]{2}[NS].[0-9]{3}[0-9 ]{2}\.[0-9 ]{2}[EW].)", re.S)


def status(scan, start, end, depth):
    """The status text from offset 9; returns its free-text spans."""
    line = scan.line
    s = start + 9
    if s >= end:
        return []
    scan.tok("mice.status", s, end, depth)
    d = depth + 1
    c = line[s]
    prefix = None
    p = s
    if c == 0x1D:
        te = min(s + 6, end)
        scan.tok("mice.tlm", s, te, d)
        scan.find("mice.tlm", "obsolete", s)
        if te < s + 6:
            scan.find("mice.tlm", "syntax", te)
        elif te < end:
            scan.find("mice.tlm", "unstated", te)
        p = te
    elif c in _KENWOOD or c in _OTHER:
        scan.tok("mice.type.prefix", s, s + 1, d)
        prefix = c
        p = s + 1
    texts = _after_prefix(scan, p, end, d, prefix)
    if prefix in _OTHER:
        _byte9(scan, s, end, d, prefix)
    return texts


def _after_prefix(scan, p, end, d, prefix):
    """Altitude, suffix, locator, extension and free text, in that order of
    reading. Without a prefix there is no suffix."""
    line = scan.line
    # The altitude stands first (amb.mice.alt); '}' fixes its extent.
    alt = p + 4 <= end and line[p + 3] == 0x7D
    if alt:
        scan.tok("mice.alt", p, p + 4, d)
        bad = next((i for i in range(p, p + 3) if not is_b91(line[i])), None)
        if bad is not None:
            scan.find("mice.alt", "syntax", bad)
        p += 4

    # The suffix is taken from the raw last bytes before the rest is read
    # (amb.mice.suffix, amb.mice.pipe).
    te = end
    if prefix in _KENWOOD:
        if end > p and line[end - 1] in _KENWOOD_SUFFIX:
            te = end - 1
    elif prefix in _OTHER:
        if end == p:
            scan.find("mice.type.suffix", "unstated", end)
        elif end == p + 1:
            te = p
            scan.find("mice.type.suffix", "syntax", p)
        else:
            te = end - 2
            if line[te:end] not in _SUFFIX_EXAMPLES:
                scan.find("mice.type.suffix", "unstated", te)

    # The locator, after the prefix and any altitude (amb.mice.grid).
    m = _GRID.match(line, p, te)
    if m:
        ge = m.end()
        n = ge - 2 - p
        # Upper case and the Maidenhead ranges (amb.grid.range, amb.grid.case).
        ranges = (_AR, _AR, DIGITS, DIGITS, _AX, _AX)
        bad = next((p + i for i in range(n) if line[p + i] not in ranges[i]), None)
        if ge < te and line[ge] == SP:
            # The SP after /G is the locator's whatever follows it.
            ge += 1
        elif bad is None and not _tail_ok(line, ge, te):
            bad = ge
        scan.tok("mice.grid", p, ge, d)
        if bad is not None:
            scan.find("mice.grid", "syntax", bad)
        p = ge
    elif _grid_other_symbol(line, p, te):
        # The finding is on the rule this reading gives the bytes, the free
        # text (README section 3, Placing a finding).
        scan.find("cmt.text", "ambiguous", p)

    # One data extension at the start of the free text (amb.mice.extension);
    # a course and speed is not one of the Mic-E forms.
    x = step3(line, p, te) if p < te else None
    if x is not None and x.rule != "ext.csespd":
        emit_ext(scan, x, d)
        if x.h_alpha:
            # amb.ext.phg: reading (b) takes the bytes as text, and the
            # status text has no length limit to fail on.
            scan.find(x.rule, "ambiguous", x.start)
        p += x.n

    texts = []
    if p < te:
        _free_text(scan, p, te, d, alt)
        texts.append((p, te))
    if te < end:
        scan.tok("mice.type.suffix", te, end, d)
    return texts


def _tail_ok(line, q, te):
    """What section 5 allows after the text: nothing, or a base-91 block
    and DAO, or a DAO, up to the suffix."""
    if q >= te:
        return True
    daos = dao_candidates(line, q, te)
    if any(i == q and i + 5 == te for i, _ in daos):
        return True
    blk = b91_block(Scan(line), q, te, 0, daos)
    return blk is not None and blk[0] == q


def _grid_other_symbol(line, p, te):
    """Reading (c) of amb.mice.grid: an upper-case locator in range followed
    by a symbol other than /G, then SP or what may end the status text."""
    for n in (6, 4):
        if p + n + 2 > te:
            continue
        loc = line[p : p + n]
        if not (loc[0] in _AR and loc[1] in _AR and loc[2] in DIGITS and loc[3] in DIGITS):
            continue
        if n == 6 and not (loc[4] in _AX and loc[5] in _AX):
            continue
        table, code = line[p + n], line[p + n + 1]
        if table not in SYM_TABLE or not 0x21 <= code <= 0x7E or (table, code) == (0x2F, 0x47):
            continue
        q = p + n + 2
        if q < te and line[q] == SP or _tail_ok(line, q, te):
            return True
    return False


def _cmt_altitudes(scan, s, e, d):
    """cmt.alt and cmt.alt.neg as 02 section 8.2 finds them in a comment."""
    line = scan.line
    occ = []
    i = line.find(b"/A=", s, e)
    while i >= 0:
        j, nxt = i + 3, i + 9
        tail_ok = nxt <= e and (nxt == e or line[nxt] not in DIGITS)
        if tail_ok and all(c in DIGITS for c in line[j:nxt]):
            occ.append(("cmt.alt", i))
        elif tail_ok and line[j] == 0x2D and all(c in DIGITS for c in line[j + 1 : nxt]):
            occ.append(("cmt.alt.neg", i))
        else:
            scan.find("cmt.alt", "syntax", i)
        i = line.find(b"/A=", i + 1, e)
    for rule, i in occ:
        scan.tok(rule, i, i + 9, d)
        if len(occ) > 1:
            scan.find(rule, "ambiguous", i)
    return [(rule, i, i + 9) for rule, i in occ]


def _same_item(rule):
    return "cmt.alt" if rule.startswith("cmt.alt") else rule


def _free_text(scan, s, e, d, alt_at_start):
    """The free text between the parts, read as a position comment
    (04 section 5) with no length limit."""
    line = scan.line
    scan.tok("cmt.text", s, e, d)
    # One syntax finding, at the first byte outside the set (README section
    # 3, Placing a finding).
    bad = bad_text_bytes(line[s:e])
    if bad:
        scan.find("cmt.text", "syntax", s + bad[0])
    dd = d + 1
    items = _cmt_altitudes(scan, s, e, dd)
    daos = dao_candidates(line, s, e)
    for i, k in daos:
        scan.tok("cmt.dao", i, i + 5, dd)
        if k:
            scan.find("cmt.dao", k, i)
        items.append(("cmt.dao", i, i + 5))
    if len(daos) > 1:
        # amb.cmt.dao: with no limit, reading (b) or (c) always accepts.
        for i, _ in daos:
            scan.find("cmt.dao", "ambiguous", i)
    blk = b91_block(scan, s, e, dd, daos)
    if blk:
        items.append(("tlm.b91",) + blk)
    items.extend(noarchive_in(scan, s, e, dd))
    items.sort(key=lambda t: t[1])
    for a in range(len(items)):
        ra, sa, ea = items[a]
        for b in range(a + 1, len(items)):
            rb, sb, _ = items[b]
            if sb >= ea:
                break
            if _same_item(ra) != _same_item(rb):
                scan.find(ra, "ambiguous", sa)
                scan.find(rb, "ambiguous", sb)

    def in_text(i, j):
        return not any(i < ie and is_ < j for _, is_, ie in items)

    # amb.mice.extension: a later run of a marked extension, and a standard
    # position anywhere in the text. These findings and that of amb.mice.alt
    # are on cmt.text, the rule this reading gives the bytes.
    for m in _MARKED.finditer(line, s, e):
        x = step3(line, m.start(), e)
        if x is not None and x.clean() and in_text(x.start, x.start + x.n):
            scan.find("cmt.text", "ambiguous", x.start)
    for m in _POSITION.finditer(line, s, e):
        i = m.start()
        if i + 19 <= e and in_text(i, i + 19) and _position_fits(line, i):
            scan.find("cmt.text", "ambiguous", i)
    # amb.mice.alt: a later altitude, when none stands at the start.
    if not alt_at_start:
        for m in _ALT_RUN.finditer(line, s, e):
            if in_text(m.start(), m.end()):
                scan.find("cmt.text", "ambiguous", m.start())

    # 09 section 7 at the start of the free text, after its syntax findings.
    frequency(scan, s, e, dd)


def _position_fits(line, i):
    """An uncompressed position at i that gives no syntax or value finding."""
    scratch = Scan(line)
    _, ok, level = lat(scratch, i, i + 19, 0)
    if not ok:
        return False
    sym_table(scratch, i + 8, 0)
    _, ok, _ = lon(scratch, i + 9, i + 19, 0, level)
    if not ok:
        return False
    sym_code(scratch, i + 18, 0)
    return not any(f.kind in _BAD for f in scratch.findings)


def _byte9(scan, s, end, d, prefix):
    """amb.mice.byte9: reading (b) takes a 0x60 or 0x27 followed by 4 or 10
    hexadecimal digits as the obsolete telemetry, and the rest as status
    text with no prefix and no suffix."""
    line = scan.line
    n = 4 if prefix == 0x60 else 10
    h = s + 1
    if end - h < n or not all(c in _HEX for c in line[h : h + n]):
        return
    if any(f.kind in _BAD and h <= f.offset < h + n for f in scan.findings):
        return
    scratch = Scan(line)
    _after_prefix(scratch, h + n, end, d, None)
    # A finding of the same kind at the same offset is shared; the rule ID is
    # not compared (README section 3).
    mine = {(f.kind, f.offset) for f in scan.findings}
    if any(f.kind in _BAD and (f.kind, f.offset) not in mine for f in scratch.findings):
        return
    scan.find("mice.type.prefix", "ambiguous", s)


# --- The packet ---------------------------------------------------------


def read(scan, start, end, depth):
    line = scan.line
    if line[start] in (0x1C, 0x1D):
        scan.find("mice.dti", "obsolete", start)
    destination(scan, start)
    fixed(scan, start, end, depth)
    texts = status(scan, start, end, depth)
    if start + 9 < end and line[start + 7] == 0x5F:
        # amb.wx.carriers: reading (a) would read the status text as weather.
        weather_carriers(scan, start + 9, end, depth, wind=False)
    noarchive_outside(scan, start, end, texts)
