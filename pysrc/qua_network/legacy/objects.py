# SPDX-License-Identifier: Apache-2.0
"""Object and item reports, area objects, signposts and the obsolete object
without an identifier: docs/legacy/05-object-item.md."""

import re

from qua_network.legacy.fields import (
    CMP_TABLE,
    DIGITS,
    area_bad,
    brgnrq_after,
    cmp_block,
    comment,
    emit_area,
    emit_ext,
    lat,
    lon,
    missing,
    step3,
    sym_code,
    sym_table,
    timestamp7,
)
from qua_network.legacy.model import Scan
from qua_network.legacy.weather import complete as weather_complete
from qua_network.legacy.weather import storm as weather_storm

_ITEM_END = re.compile(rb"[!_]")
_CORRIDOR = re.compile(rb"\{[0-9]+\}")
# A signpost: 1 to 3 bytes 0x20-0x7E other than '{' and '}', in braces.
_SIGNPOST = re.compile(rb"\{[\x20-\x7a\x7c\x7e]{1,3}\}")


def read(scan, start, end, depth):
    """Dispatch a 05-object-item field by its identifier byte."""
    if scan.line[start] == 0x3B:
        _object(scan, start, start + 1, end, depth)
    else:
        _item(scan, start, end, depth)


# --- Object report (05 section 2) ---------------------------------------


def _object(scan, dti, p, end, depth):
    """An object whose name starts at p; dti is the offset of the identifier
    byte, or None for the obsolete form of section 6."""
    line = scan.line
    e = min(p + 9, end)
    if e > p:
        scan.tok("obj.name", p, e, depth)
    bad = next((i for i in range(p, e) if not 0x20 <= line[i] <= 0x7E), None)
    if bad is None and e < p + 9:
        bad = e
    if bad is not None:
        scan.find("obj.name", "syntax", bad)
    elif line[p:e] == b" " * 9:
        # amb.obj.name: no name is left once the padding is removed.
        scan.find("obj.name", "unstated", p)
    if e < p + 9 or missing(scan, "obj.state", e, end):
        return
    scan.tok("obj.state", e, e + 1, depth)
    if line[e] not in b"*_":
        scan.find("obj.state", "syntax", e)

    # amb.obj.time: a timestamp by its shape, else a position read in its
    # place; bytes that are neither are the 7 bytes of a malformed timestamp.
    t = e + 1
    if missing(scan, "obj.time", t, end):
        return
    if _time_shape(line, t, end) or not _position_at(line, t, end):
        q, ok = timestamp7(scan, t, end, depth)
        if not ok:
            return
        if missing(scan, "obj.pos", q, end):
            return
    else:
        q = t
    _body(scan, dti, q, end, depth, "obj")


def _time_shape(line, t, end):
    return end - t >= 7 and line[t + 6] in b"zh/" and line[t : t + 6].isdigit()


def _position_at(line, t, end):
    """Whether a position at t runs to its symbol code with no syntax finding."""
    scratch = Scan(line)
    c = line[t]
    if c in DIGITS:
        p, ok, level = lat(scratch, t, end, 0)
        if not ok or p >= end:
            return False
        sym_table(scratch, p, 0)
        p, ok, _ = lon(scratch, p + 1, end, 0, level)
        if not ok or p >= end:
            return False
        sym_code(scratch, p, 0)
    elif c in CMP_TABLE:
        if cmp_block(scratch, t, end, 0, False) is None:
            return False
    else:
        return False
    return not any(f.kind == "syntax" for f in scratch.findings)


# --- Item report (05 section 3) -----------------------------------------


def _item(scan, start, end, depth):
    line = scan.line
    scan.find("item.dti", "discouraged", start)
    p = start + 1
    m = _ITEM_END.search(line, p, end)
    if m is None:
        # No '!' or '_': where the name ends cannot be told.
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
            # Where the missing byte was expected.
            scan.find("item.name", "value", t)
        elif t - p > 9:
            scan.find("item.name", "value", p + 9)
    scan.tok("item.state", t, t + 1, depth)
    q = t + 1
    if missing(scan, "item.pos", q, end):
        return
    _body(scan, start, q, end, depth, "item")


# --- Position, extension slot and comment (05 sections 2 to 5, 7) -------


def _body(scan, dti, q, end, depth, kind):
    """The position at q and what follows it; kind is "obj" or "item"."""
    c = scan.line[q]
    if c in DIGITS:
        _uncompressed(scan, dti, q, end, depth, kind)
    elif c in CMP_TABLE:
        _compressed(scan, dti, q, end, depth, kind)
    else:
        # 02 section 6.1: neither form can be delimited.
        scan.find(kind + ".pos", "syntax", q)
        scan.residue(q, end, depth, kind + ".pos")


def _weather(scan, dti, p, end, depth, kind, block=None):
    """Read the bytes from p as the weather data of 06; an object's
    identifier token carries wx.obj, an item's keeps item.dti."""
    if kind == "obj" and dti is not None:
        scan.retag(dti, depth, "wx.obj")
    weather_complete(scan, p, end, depth, block)


def _area_symbol(table, code):
    """The area object symbol \\l (section 4)."""
    return table == 0x5C and code == 0x6C


def _uncompressed(scan, dti, p, end, depth, kind):
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
        # 05 section 7: the '_' symbol announces weather data, on an object
        # (06 amb.wx.symbol) and on an item (06 amb.wx.carriers).
        _weather(scan, dti, p, end, depth, kind)
        return

    limit = 43
    line_area = False
    if _area_symbol(table, code):
        # Step 1 of 02 section 7.1: the area descriptor and nothing else
        # (amb.area.symbol). A report that ends at the symbol has none.
        if p < end:
            line_area = line[p] in b"16"
            p = emit_area(scan, p, end, depth)
            limit = 36
    else:
        x = step3(line, p, end)
        if x is not None:
            emit_ext(scan, x, depth)
            p += x.n
            limit = 36
            if x.rule == "ext.csespd":
                # Storm data under '@', any table byte (06 section 8), else
                # bearing and NRQ (02 section 7.4); the slot is the only
                # place of an extension (02 amb.ext.count).
                q = weather_storm(scan, p, end, depth) if code == 0x40 else p
                if q == p:
                    q = brgnrq_after(scan, p, end, depth)
                    if q > p:
                        limit = 28
                p = q
    extra = _braces(scan, p, end, depth, table, code, line_area)
    comment(scan, p, end, depth, limit, kind + ".cmt", b91=False, extra=extra)


def _compressed(scan, dti, q, end, depth, kind):
    line = scan.line
    table, code = line[q], line[q + 9] if q + 9 < end else None
    wx = code == 0x5F and end > q + 13
    if kind == "obj":
        scan.find("obj.pos", "discouraged", q)
    e = cmp_block(scan, q, end, depth, wx)
    if e is None:
        return
    if wx:
        _weather(scan, dti, e, end, depth, kind, q)
        return
    line_area = False
    if _area_symbol(table, code) and area_bad(line, e, end) is None:
        # 02 amb.ext.compressed with the area symbol: step 1 of 02 section 7.1.
        line_area = line[e] in b"16"
        emit_area(scan, e, end, depth)
        scan.find("ext.area", "ambiguous", e)
        e += 7
        start_cse, limit = False, 36
    else:
        # amb.area.symbol: no other extension is tried under the area symbol.
        start_cse, limit = not _area_symbol(table, code), 43
    extra = _braces(scan, e, end, depth, table, code, line_area)
    comment(scan, e, end, depth, limit, kind + ".cmt", b91=False, extra=extra, start_cse=start_cse)


# --- Corridor width and signpost (05 sections 4 and 5) ------------------


def _braces(scan, s, end, depth, table, code, line_area):
    """Tokenize the corridor or signpost braces of the comment line[s:end]:
    the first of their shape anywhere in it (amb.area.braces). Returns their
    spans for the overlap rule of 02 section 8.2."""
    if line_area:
        pattern, rule = _CORRIDOR, "area.corridor"
    elif table == 0x5C and code == 0x6D:
        pattern, rule = _SIGNPOST, "obj.signpost"
    else:
        return []
    m = pattern.search(scan.line, s, end)
    if m is None:
        return []
    scan.tok(rule, m.start(), m.end(), depth + 1)
    return [(rule, m.start(), m.end())]


# --- Obsolete object without identifier (05 section 6) ------------------


def obsolete_accepts(line, start, end):
    """Whether line[start:end] is an object without its identifier: the
    fields from obj.name to the position are complete and give no syntax
    finding. What follows the position does not decide the match."""
    if end - start < 10 or line[start + 9] not in b"*_":
        return False
    scratch = Scan(line)
    _object(scratch, None, start, end, 1)
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
    _object(scan, None, start, end, depth + 1)
