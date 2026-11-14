# SPDX-License-Identifier: Apache-2.0
"""Mic-E: docs/legacy/04-mic-e.md.

The reader takes the information field from its identifier byte, whose
token frame.py has already emitted, and the destination callsign through
the dest.mice token of the same packet's header.
"""

import re

from qua_network.deviceid import pinned_register
from qua_network.legacy.fields import (
    DIGITS,
    SP,
    SYM_TABLE,
    altitudes,
    comment_fault,
    dao_candidates,
    emit_ext,
    is_b91,
    item_overlaps,
    noarchive_in,
    step3,
    sym_code,
    text_spans,
)
from qua_network.legacy.model import Scan
from qua_network.legacy.other import frequency
from qua_network.legacy.telemetry import b91_block, b91_span

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
        # Such an address is not in the AX.25 form either (01 amb.addr.form).
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
        # amb.mice.dest: the document calls the comment type "unknown".
        first = flags[0][1]
        scan.find("mice.dest", "unstated", next(p for p, k in flags if k != first))
    # mice.dest.ssid gives no finding of its own (01 err.dest.ssid); the
    # token stays 01-frame's dest.ssid.


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

# amb.mice.suffix: the device suffixes are those of the aprs-deviceid
# register at the commit the repository pins, read from the submodule.


def _load_suffixes(reg):
    """(prefix, suffix) pairs of the 'micelegacy' list, and (prefix or None,
    suffix) of the 'mice' list, as bytes; None stands for any 0x60 or 0x27
    prefix. Entries without a suffix name no suffix."""

    def enc(v):
        return None if v is None else str(v).encode("latin-1")

    legacy = frozenset((enc(e["prefix"]), enc(e["suffix"])) for e in reg["micelegacy"] if e.get("suffix") is not None)
    other = frozenset((enc(e.get("prefix")), enc(e["suffix"])) for e in reg["mice"] if e.get("suffix") is not None)
    return legacy, other


_KENWOOD_PAIRS, _OTHER_SUFFIXES = _load_suffixes(pinned_register())
_HEX = frozenset(b"0123456789ABCDEFabcdef")
# A fifth or sixth byte outside A-X, in either case, is no subsquare letter
# (amb.grid.range); only the 4-byte locator is then tried. '/G' closes the
# locator, so letters out of range before it are a locator with a syntax
# finding.
_GRID = re.compile(rb"[A-Za-z]{2}[0-9]{2}(?:[A-Za-z]{2})?/G")
_AR = frozenset(b"ABCDEFGHIJKLMNOPQR")
_AX = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWX")
_GRID_RANGES = (_AR, _AR, DIGITS, DIGITS, _AX, _AX)
_ALT_RUN = re.compile(rb"[!-|]{3}\}")
# Where a form of step 3 of 02 section 7.1 can start.
_EXT_AT = re.compile(rb"(?=PHG|RNG|DFS|(?:[0-9]{3}|\.{3}| {3})/(?:[0-9]{3}|\.{3}| {3}))")


def status(scan, start, end, depth):
    """The status text from offset 9."""
    line = scan.line
    s = start + 9
    if s >= end:
        return
    scan.tok("mice.status", s, end, depth)
    d = depth + 1
    c = line[s]
    if c == 0x1D:
        te = min(s + 6, end)
        _telemetry(scan, s, te, end, d)
        if te < s + 6:
            scan.find("mice.tlm", "syntax", te)
        return
    if c in _OTHER:
        n = 4 if c == 0x60 else 10
        if end - s > n and all(b in _HEX for b in line[s + 1 : s + 1 + n]):
            # err.mice.status, amb.mice.byte9: the flag and its hexadecimal
            # channels are the more specific of the two readings.
            _telemetry(scan, s, s + 1 + n, end, d)
            if _prefix_accepts(line, s, end, d, c):
                scan.find("mice.tlm", "ambiguous", s)
            return
    if c in _KENWOOD or c in _OTHER:
        scan.tok("mice.type.prefix", s, s + 1, d)
        _after_prefix(scan, s + 1, end, d, c)
    else:
        _after_prefix(scan, s, end, d, None)


def _telemetry(scan, s, te, end, d):
    """mice.tlm over line[s:te]. The document names nothing after it, so the
    bytes that follow stay in mice.status with no deeper token."""
    scan.tok("mice.tlm", s, te, d)
    scan.find("mice.tlm", "obsolete", s)
    if te < end:
        scan.find("mice.tlm", "unstated", te)


def _prefix_accepts(line, s, end, d, prefix):
    """Whether the status text read with a device prefix at s gives no syntax
    or value finding (amb.mice.byte9)."""
    scratch = Scan(line)
    _after_prefix(scratch, s + 1, end, d, prefix)
    return not any(f.kind in _BAD for f in scratch.findings)


def _after_prefix(scan, p, end, d, prefix):
    """Altitude, suffix, locator, extension and free text, in that order of
    reading. Without a prefix there is no suffix."""
    line = scan.line
    # An altitude first after the type byte; '}' fixes its extent.
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
        # Only a listed (prefix, last byte) pair; any other last byte is text.
        if end > p and (bytes((prefix,)), line[end - 1 : end]) in _KENWOOD_PAIRS:
            te = end - 1
    elif prefix in _OTHER:
        te = _other_suffix(scan, line, p, end, prefix)

    ge = _grid(scan, p, te, te, d)
    grid = ge is not None
    if grid:
        p = ge

    x = step3(line, p, te) if p < te else None
    if x is not None:
        emit_ext(scan, x, d)
        p += x.n

    if p < te:
        _free_text(scan, p, te, d, alt, grid, x is not None)
    if te < end:
        scan.tok("mice.type.suffix", te, end, d)


def _other_suffix(scan, line, p, end, prefix):
    """Where the two-byte suffix after a 0x60 or 0x27 prefix starts, or end
    when there is none (amb.mice.suffix)."""
    te = end - 2
    if te < p or 0x80 <= line[te] <= 0xBF and _utf8(line, p, end):
        # Fewer than two bytes, or two that would cut a character of text
        # that is well formed as a whole: no suffix.
        scan.find("mice.type.suffix", "unstated", end)
        return end
    sfx = line[te:end]
    # The register is open: an unlisted suffix keeps its token.
    if (None, sfx) not in _OTHER_SUFFIXES and (bytes((prefix,)), sfx) not in _OTHER_SUFFIXES:
        scan.find("mice.type.suffix", "unstated", te)
    return te


def _utf8(line, s, e):
    try:
        line[s:e].decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _grid(scan, p, mend, te, d):
    """mice.grid at p, matched within line[p:mend]; returns its end, or None.
    te ends what may follow it: a SP is needed only before plain text."""
    line = scan.line
    m = _GRID.match(line, p, mend)
    if m is None:
        return None
    ge = m.end()
    n = ge - 2 - p
    # Upper case and the Maidenhead ranges (amb.grid.range, amb.grid.case).
    bad = next((p + i for i in range(n) if line[p + i] not in _GRID_RANGES[i]), None)
    if ge < te and line[ge] == SP:
        # The SP after /G is the locator's whatever follows it.
        ge += 1
    elif bad is None and not _tail_ok(line, ge, te):
        bad = ge
    scan.tok("mice.grid", p, ge, d)
    if bad is not None:
        scan.find("mice.grid", "syntax", bad)
    return ge


def _tail_ok(line, q, te):
    """What section 5 allows after the text: nothing, or a base-91 block
    and DAO, or a DAO, up to the suffix."""
    if q >= te:
        return True
    daos = dao_candidates(line, q, te)
    if any(i == q and i + 5 == te for i, _ in daos):
        return True
    blk = b91_span(line, q, te, daos)
    return blk is not None and blk[0] == q


def _free_text(scan, s, e, d, alt, grid, ext):
    """The free text between the parts, read as a position comment
    (04 section 5) with no length limit. alt, grid and ext say whether an
    altitude, a locator and an extension stood at the start."""
    line = scan.line
    scan.tok("cmt.text", s, e, d)
    bad = comment_fault(line[s:e])
    if bad is not None:
        scan.find("cmt.text", "syntax", s + bad)
    dd = d + 1
    # The block is found first, with every DAO candidate, since one may
    # follow it; the other searches leave its bytes alone (07 section 3).
    daos = dao_candidates(line, s, e)
    span = b91_span(line, s, e, daos)
    if span is not None:
        daos = [(i, k) for i, k in daos if not span[0] <= i < span[1]]
    items = altitudes(scan, s, e, dd, span)
    for i, k in daos:
        scan.tok("cmt.dao", i, i + 5, dd)
        if k:
            scan.find("cmt.dao", k, i)
        items.append(("cmt.dao", i, i + 5))
    if len(daos) > 1:
        # amb.cmt.dao: a reading that keeps one candidate reads the others as text.
        for i, _ in daos:
            scan.find("cmt.dao", "ambiguous", i)
    if span is not None:
        b91_block(scan, s, e, dd, daos, span)
        items.append(("tlm.b91",) + span)
    items.extend(noarchive_in(scan, s, e, dd, span))
    if not grid or not alt or not ext:
        # The block is no text for these searches (07 section 3).
        items.extend(_later(scan, text_spans(s, e, span), e, dd, grid, alt, ext))
    item_overlaps(scan, items)

    # 09 section 7 at the start of the free text, after its syntax findings.
    frequency(scan, s, e, dd)


def _later(scan, spans, e, dd, grid, alt, ext):
    """The first locator, altitude and extension in the free text when none
    stood at the start (amb.mice.grid, amb.mice.alt, amb.mice.extension):
    the whole text is their place, so the first run of each is that item,
    with no ambiguous finding. A course and speed, which only its shape
    marks, is taken only where it gives no syntax or value finding; the
    other forms are announced by their keyword. Returns their spans as
    items of the text."""
    line = scan.line
    out = []
    if not grid:
        for a, b in spans:
            m = _GRID.search(line, a, b)
            if m:
                ge = _grid(scan, m.start(), b, e, dd)
                out.append(("mice.grid", m.start(), ge))
                break
    if not alt:
        for a, b in spans:
            m = _ALT_RUN.search(line, a, b)
            if m:
                scan.tok("mice.alt", m.start(), m.end(), dd)
                scan.find("mice.alt", "discouraged", m.start())
                out.append(("mice.alt", m.start(), m.end()))
                break
    if not ext:
        for a, b in spans:
            x = next(
                (
                    x
                    for x in (step3(line, m.start(), b) for m in _EXT_AT.finditer(line, a, b))
                    if x and (x.rule != "ext.csespd" or x.clean())
                ),
                None,
            )
            if x is not None:
                emit_ext(scan, x, dd)
                out.append((x.rule, x.start, x.start + x.n))
                break
    return out


# --- The packet ---------------------------------------------------------


def read(scan, start, end, depth):
    line = scan.line
    if line[start] in (0x1C, 0x1D):
        scan.find("mice.dti", "obsolete", start)
    destination(scan, start)
    fixed(scan, start, end, depth)
    status(scan, start, end, depth)
