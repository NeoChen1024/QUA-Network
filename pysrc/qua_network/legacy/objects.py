# SPDX-License-Identifier: Apache-2.0
"""Object and item reports, area objects, signposts and the obsolete object
without an identifier: docs/legacy/05-object-item.md."""

import re

from qua_network.legacy.fields import (
    CMP_TABLE,
    DIGITS,
    SYM_TABLE,
    area_bad,
    area_high,
    area_literal,
    brgnrq_shape,
    cmp_block,
    comment,
    csespd_mixed,
    emit_ext,
    lat,
    lon,
    missing,
    noarchive_outside,
    step3,
    sym_code,
    sym_table,
    timestamp7,
)
from qua_network.legacy.model import Scan
from qua_network.legacy.weather import carriers as weather_carriers
from qua_network.legacy.weather import complete as weather_complete
from qua_network.legacy.weather import storm as weather_storm
from qua_network.legacy.weather import storm_overlay as weather_storm_overlay

_STORM = re.compile(rb"/(?:TS|HC|TD)")
_ITEM_END = re.compile(rb"[!_]")
# freq.objname (09 section 7): the four 9-byte forms of p. 116/92, tested on
# the name without its padding. The identifying bytes are letters or digits;
# any byte 0x21-0x7E may stand in place of '-' (amb.freq.objname).
_FREQ_NAME = re.compile(rb"[0-9]{3}\.(?:[0-9]{3}[\x21-\x7e][0-9A-Za-z]|[0-9]{2}[\x21-\x7e][0-9A-Za-z]{2})")
# An overlay character as table byte, by position form (02 sections 4 and 6).
_UNC_OVERLAY = SYM_TABLE - frozenset(b"/\\")
_CMP_OVERLAY = CMP_TABLE - frozenset(b"/\\")
_BAD = ("syntax", "value")
_CORRIDOR = re.compile(rb"\{[0-9]+\}")
# A signpost: 1 to 3 bytes 0x20-0x7E other than '{' and '}', in braces.
_SIGNPOST = re.compile(rb"\{[\x20-\x7a\x7c\x7e]{1,3}\}")
_AREA_PARTS = (("area.type", 0, 1), ("area.lat", 1, 3), ("area.color", 3, 5), ("area.lon", 5, 7))


def read(scan, start, end, depth):
    """Dispatch a 05-object-item field by its identifier byte."""
    texts = []
    if scan.line[start] == 0x3B:
        _object(scan, start, start + 1, end, depth, texts)
    else:
        _item(scan, start, end, depth, texts)
    noarchive_outside(scan, start, end, texts)


# --- Object report (05 section 2) ---------------------------------------


def _object(scan, dti, p, end, depth, texts):
    """An object whose name starts at p; dti is the offset of the identifier
    byte, or None for the obsolete form of section 6."""
    line = scan.line
    e = min(p + 9, end)
    if e > p:
        scan.tok("obj.name", p, e, depth)
    bad = next((i for i in range(p, e) if not 0x20 <= line[i] <= 0x7E), None)
    if bad is None and e < p + 9:
        bad = e
    elif bad is None and line[p:e] == b" " * 9:
        # amb.obj.name: no name is left once the padding is removed.
        bad = p
    if bad is not None:
        scan.find("obj.name", "syntax", bad)
    if e < p + 9 or missing(scan, "obj.state", e, end):
        return
    scan.tok("obj.state", e, e + 1, depth)
    if line[e] not in b"*_":
        scan.find("obj.state", "syntax", e)

    # amb.obj.time: required. Six digits mark a timestamp, which no position
    # starts with; anything else is a missing timestamp.
    t = e + 1
    head = line[t : min(t + 6, end)]
    if head and all(c in DIGITS for c in head):
        q, ok = timestamp7(scan, t, end, depth)
        if not ok:
            return
    else:
        # A missing timestamp uses no byte; the position is read from where it
        # was expected (README section 3, Output).
        scan.find("obj.time", "syntax", t)
        if t >= end:
            return
        q = t
    if missing(scan, "obj.pos", q, end):
        return
    # obj.name: trailing SP are padding and not part of the name.
    freq_name = _FREQ_NAME.fullmatch(line[p : p + 9].rstrip(b" ")) is not None
    _body(scan, dti, q, end, depth, "obj", freq_name, texts)


# --- Item report (05 section 3) -----------------------------------------


def _item(scan, start, end, depth, texts):
    line = scan.line
    scan.find("item.dti", "discouraged", start)
    p = start + 1
    m = _ITEM_END.search(line, p, end)
    if m is None:
        # No '!' or '_': where the name ends cannot be told (amb.item.name).
        scan.residue(p, end, depth, "item.name")
        scan.find("item.name", "syntax", end)
        return
    t = m.start()
    if t == p:
        scan.find("item.name", "syntax", p)
    else:
        scan.tok("item.name", p, t, depth)
        bad = next((i for i in range(p, t) if not 0x20 <= line[i] <= 0x7E), None)
        if bad is not None:
            scan.find("item.name", "syntax", bad)
        if t - p < 3:
            # At the place where the missing byte was expected (README section 3).
            scan.find("item.name", "value", t)
        elif t - p > 9:
            scan.find("item.name", "value", p + 9)
    scan.tok("item.state", t, t + 1, depth)
    q = t + 1
    if missing(scan, "item.pos", q, end):
        return
    freq_name = _FREQ_NAME.fullmatch(line[p:t]) is not None
    _body(scan, start, q, end, depth, "item", freq_name, texts)


# --- Position, extension slot and comment (05 sections 2 to 5, 7) -------


def _body(scan, dti, q, end, depth, kind, freq_name, texts):
    """The position at q and what follows it; kind is "obj" or "item"."""
    c = scan.line[q]
    if c in DIGITS:
        cmt = _uncompressed(scan, dti, q, end, depth, kind, freq_name)
    elif c in CMP_TABLE:
        cmt = _compressed(scan, dti, q, end, depth, kind, freq_name)
    else:
        # 02 section 6.1: neither form can be delimited.
        scan.find(kind + ".pos", "syntax", q)
        scan.residue(q, end, depth, kind + ".pos")
        cmt = None
    if cmt is not None:
        texts.append((cmt.start, cmt.end))


def _to_weather(scan, dti, p, end, depth, block=None):
    """05 section 7: the bytes after the position block are 06's (wx.obj)."""
    if dti is not None:
        scan.retag(dti, depth, "wx.obj")
    weather_complete(scan, p, end, depth, block, obj_cmt=block is not None)


def _uncompressed(scan, dti, p, end, depth, kind, freq_name):
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
        if kind == "obj":
            _to_weather(scan, dti, p, end, depth)
            return None

    slot = p
    x = None
    line_area = False
    storm_at = None
    if table == 0x5C and code == 0x6C:
        # Step 1 of 02 section 7.1: the area descriptor and nothing else
        # (amb.area.symbol). A report that ends at the symbol has none.
        if p < end:
            e = min(p + 7, end)
            scan.tok("ext.area", p, e, depth)
            bad = area_bad(line, p, end)
            if bad is not None:
                scan.find("ext.area", "syntax", bad)
            for rule, a, b in _AREA_PARTS:
                if p + b <= end:
                    scan.tok(rule, p + a, p + b, depth + 1)
            line_area = line[p] in b"16"
            p = e
    else:
        # Step 3, with the visible cases of 7.1. Each of these runs is comment
        # text here, so its finding is on cmt.text, the rule this reading gives
        # the bytes (02 section 7.1; README section 3, Placing a finding).
        x = step3(line, p, end)
        if area_literal(line, p, end):
            scan.find("cmt.text", "ambiguous", p)  # amb.ext.area
        if area_high(line, p, end):
            scan.find("cmt.text", "ambiguous", p)  # amb.area.symbol
        if x is None:
            m = csespd_mixed(line, p, end)
            if m is not None:
                scan.find("cmt.text", "ambiguous", m)  # amb.ext.csespd
        else:
            emit_ext(scan, x, depth)
            p += x.n
            if code == 0x40 and x.rule == "ext.csespd" and _STORM.match(line, p, end):
                if table in b"/\\":
                    # Storm data (06 section 8), then the comment; it does not
                    # follow the slot's extension, so no course and speed is
                    # looked for at its start.
                    p = weather_storm(scan, p, end, depth)
                    return comment(scan, p, end, depth, 36, kind + ".cmt", b91=False, start_cse=False, freq_name=freq_name)
                if table in _UNC_OVERLAY:
                    storm_at = p  # an overlaid '@': no storm report here
            # Bearing and NRQ are not read here; bytes of their shape that a
            # reading of amb.ext.brgnrq would take are comment text.
            brg = brgnrq_shape(line, p, end)
            df_sym = table == 0x2F and code == 0x5C
            if brg is not None and brg <= 360 and (x.rule == "ext.csespd" or df_sym):
                scan.find("cmt.text", "ambiguous", p)

    has_ext = x is not None or p > slot
    limit = 36 if has_ext else 43
    extra = _braces(scan, p, end, depth, table, code, line_area)
    cmt = comment(scan, p, end, depth, limit, kind + ".cmt", b91=False, extra=extra, freq_name=freq_name)
    if table in _UNC_OVERLAY:
        _overlay(scan, slot, p, end, code, "cmt.text" if x is None else x.rule)
    if storm_at is not None:
        weather_storm_overlay(
            scan,
            storm_at,
            end,
            lambda scratch, q: comment(scratch, q, end, depth, 36, kind + ".cmt", b91=False, start_cse=False, freq_name=freq_name),
        )
    if x is not None and x.h_alpha:
        # amb.ext.phg: reading (b) takes the extension as comment text, within
        # the limit without an extension (43). A length finding that both
        # readings give does not count against (b).
        rest = cmt.counted if cmt else 0
        if x.rule != "ext.phgr" or x.n + rest <= 43:
            scan.find(x.rule, "ambiguous", slot)
    if code == 0x5F and slot < end:
        # amb.wx.carriers: an item that reading (a) would read as weather.
        weather_carriers(scan, slot, end, depth)
    return cmt


def _compressed(scan, dti, q, end, depth, kind, freq_name):
    line = scan.line
    wx = kind == "obj" and end - q > 13 and line[q + 9] == 0x5F
    if kind == "obj":
        scan.find("obj.pos", "discouraged", q)
    e = cmp_block(scan, q, end, depth, wx)
    if e is None:
        return None
    if wx:
        _to_weather(scan, dti, e, end, depth, q)
        return None
    table, code = line[q], line[q + 9]
    area = table == 0x5C and code == 0x6C
    if area and area_bad(line, e, end) is None:
        # 02 section 6.5: at a slot of this report 7.1 would try ext.area. The
        # bytes are comment text, so the finding is on cmt.text.
        scan.find("cmt.text", "ambiguous", e)
    extra = _braces(scan, e, end, depth, table, code, False)
    # amb.ext.compressed: 7.1 would try no course and speed in a \l report.
    cmt = comment(scan, e, end, depth, 43, kind + ".cmt", b91=False, extra=extra, start_cse=not area, freq_name=freq_name)
    if table in _CMP_OVERLAY:
        _overlay(scan, None, e, end, code, None)
    if code == 0x5F and e < end:
        weather_carriers(scan, e, end, depth, block=q)  # amb.wx.carriers, as above
    return cmt


# --- Corridor width and signpost (05 sections 4 and 5) ------------------


def _braces(scan, s, end, depth, table, code, line_area):
    """Tokenize the corridor or signpost braces of the comment line[s:end];
    returns their spans for the overlap rule of 02 section 8.2."""
    if line_area:
        return _braces_at_start(scan, s, end, depth, _CORRIDOR, "area.corridor")
    if table == 0x5C and code == 0x6D:
        return _braces_at_start(scan, s, end, depth, _SIGNPOST, "obj.signpost")
    return []


def _braces_at_start(scan, s, end, depth, pattern, rule):
    """Braces read at the start of the comment only, and once (README section
    3, Fixed spots and repeats). When the comment does not start with them,
    reading (b) of amb.area.braces would take the first later braces of their
    shape, which this reading leaves as comment text."""
    line = scan.line
    m = pattern.match(line, s, end)
    if m:
        scan.tok(rule, s, m.end(), depth + 1)
        return [(rule, s, m.end())]
    m = pattern.search(line, s, end)
    if m:
        scan.find("cmt.text", "ambiguous", m.start())
    return []


def _reported(scan, lo, hi):
    """Whether this reading gives a syntax or value finding on line[lo:hi]
    (README section 3, Precedence)."""
    return any(f.kind in _BAD and lo <= f.offset < hi for f in scan.findings)


def _overlay(scan, slot, s, end, code, slot_rule):
    """README section 3, Symbols that a format names: with an overlay
    character as table byte, 'l' and 'm' are not \\l and \\m. The wider
    reading, that the named '\\' accepts any overlay, would read an area
    descriptor at the slot of an uncompressed position (slot, whose bytes
    this reading gives slot_rule), or signpost braces at the comment start s
    (05 sections 4 and 5). Call it once the report is read."""
    line = scan.line
    if code == 0x6C and slot is not None and area_bad(line, slot, end) is None:
        # The two readings set the same comment limit over these bytes.
        if not _reported(scan, slot, slot + 7):
            scan.find(slot_rule, "ambiguous", slot)
    elif code == 0x6D:
        m = _SIGNPOST.match(line, s, end)
        if m and not _reported(scan, s, m.end()):
            scan.find("cmt.text", "ambiguous", s)


# --- Obsolete object without identifier (05 section 6) ------------------


def obsolete_accepts(line, start, end):
    """Whether line[start:end] is an object without its identifier: the
    fields from obj.name to the position are complete and give no syntax
    finding. What follows the position does not decide the match."""
    if end - start < 10 or line[start + 9] not in b"*_":
        return False
    scratch = Scan(line)
    _object(scratch, None, start, end, 1, [])
    pos_end = next(
        (t.end for t in scratch.tokens if t.rule == "sym.code" or (t.rule == "cmp.block" and t.end - t.start == 13)),
        None,
    )
    if pos_end is None:
        return False
    return not any(f.kind == "syntax" and f.offset < pos_end for f in scratch.findings)


def obsolete(scan, start, end, depth):
    """obj.obsolete: one token over the field, the object one level deeper."""
    scan.tok("obj.obsolete", start, end, depth)
    scan.find("obj.obsolete", "obsolete", start)
    texts = []
    _object(scan, None, start, end, depth + 1, texts)
    noarchive_outside(scan, start, end, texts)
