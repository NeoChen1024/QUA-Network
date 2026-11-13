# SPDX-License-Identifier: Apache-2.0
"""Object and item reports, area objects, signposts and the obsolete object
without an identifier: docs/legacy/05-object-item.md."""

import re

from qua_network.legacy.fields import (
    CMP_TABLE,
    DIGITS,
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

_STORM = re.compile(rb"/(?:TS|HC|TD)")
_ITEM_END = re.compile(rb"[!_]")
# freq.objname (09 section 7): the two shapes of a 9-byte frequency name.
_FREQ_NAME = re.compile(rb"[0-9]{3}\.(?:[0-9]{3}..|[0-9]{2}...)\Z", re.S)
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
    freq_name = _FREQ_NAME.match(line[p : p + 9]) is not None
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
    freq_name = t - p == 9 and _FREQ_NAME.match(line[p:t]) is not None
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
                # Storm data (06 section 8), then the comment; it does not follow the
                # slot's extension, so no course and speed is looked for at its start.
                p = weather_storm(scan, slot - 11, p, end, depth)
                return comment(scan, p, end, depth, 36, kind + ".cmt", b91_kind="unstated", start_cse=False, freq_name=freq_name)
            # Bearing and NRQ are not read here; bytes of their shape that a
            # reading of amb.ext.brgnrq would take are comment text.
            brg = brgnrq_shape(line, p, end)
            df_sym = table == 0x2F and code == 0x5C
            if brg is not None and brg <= 360 and (x.rule == "ext.csespd" or df_sym):
                scan.find("cmt.text", "ambiguous", p)

    has_ext = x is not None or p > slot
    limit = 36 if has_ext else 43
    extra = _braces(scan, p, end, depth, table, code, line_area)
    cmt = comment(scan, p, end, depth, limit, kind + ".cmt", b91_kind="unstated", extra=extra, freq_name=freq_name)
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
    cmt = comment(scan, e, end, depth, 43, kind + ".cmt", b91_kind="unstated", extra=extra, start_cse=not area, freq_name=freq_name)
    if code == 0x5F and e < end:
        weather_carriers(scan, e, end, depth, block=q)  # amb.wx.carriers, as above
    return cmt


# --- Corridor width and signpost (05 sections 4 and 5) ------------------


def _braces(scan, s, end, depth, table, code, line_area):
    """Tokenize the corridor or signpost braces of the comment line[s:end];
    returns their spans for the overlap rule of 02 section 8.2."""
    line = scan.line
    d = depth + 1
    if line_area:
        m = _CORRIDOR.match(line, s, end)
        if m:
            scan.tok("area.corridor", s, m.end(), d)
            return [("area.corridor", s, m.end())]
        # amb.area.braces: reading (b) would take a later one, which this
        # reading leaves as comment text.
        m = _CORRIDOR.search(line, s, end)
        if m:
            scan.find("cmt.text", "ambiguous", m.start())
        return []
    if table == 0x5C and code == 0x6D:
        m = _SIGNPOST.search(line, s, end)
        if m:
            scan.tok("obj.signpost", m.start(), m.end(), d)
            if m.start() != s:
                # amb.area.braces: reading (a) would leave them as text.
                scan.find("obj.signpost", "ambiguous", m.start())
            return [("obj.signpost", m.start(), m.end())]
    return []


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
