# SPDX-License-Identifier: Apache-2.0
"""Value rules of the value files of docs/legacy (10-values.md,
11-values-object.md, 12-values-weather.md, 13-values-telemetry.md,
14-values-status.md, 15-values-message.md and 16-values-frequency.md),
as integer arithmetic on
token bytes.

Each function named ``val_*`` is the value rule with the same ID (dots
become underscores). It takes the bytes of the tokens that the column
"Tokens" names and returns integer counts in the units of APRS12c, or
codes and flags. It does not judge findings: the ``effect_*`` functions
give the effect of section 10 for one finding, and record.py combines
them (10-values section 2.4).

A quantity is returned as ``Q(unit, n, w, d)``. For a linear unit ``n`` is
the count and ``w`` the step; for a non-linear unit ``n`` is the code ``k``
of the formula (01-record section 4.3). ``d`` is 10^f for a weather value
with f digits after its '.', and 1 for every other value: the count and
the step are at the scale 1/d of the unit (12-values-weather section 2.1).
The unit keys are those of record.UNITS.
"""

from typing import NamedTuple

SP = 0x20

# 10-values section 2.4, in increasing severity.
KEPT, COMPUTABLE, NONE = 0, 1, 2


class Q(NamedTuple):
    unit: str
    n: int
    w: int = 1
    d: int = 1


def _d(c):
    """d[i] of section 2.2; a blank or another non-digit counts as 0. Where
    the byte is not a blank, the tokenizer has given syntax, and the value
    has the effect none."""
    return c - 0x30 if 0x30 <= c <= 0x39 else 0


def _is_digit(c):
    return 0x30 <= c <= 0x39


def b91(b):
    """v(t) of section 2.2: base-91, most significant byte first."""
    v = 0
    for c in b:
        v = v * 91 + c - 33
    return v


# --- Section 3: identifier and timestamp --------------------------------


def val_pos_dti(c):
    """(timestamp flag, messaging flag)."""
    return c in b"/@", c in b"=@"


def val_mice_dti(c):
    """Fix age, or None for 0x27 (amb.val.micefix)."""
    if c in (0x60, 0x1C):
        return "current"
    if c == 0x1D:
        return "old"
    return None


def val_time_dhm(b):
    """(day, hour, minute, zone). 'z' and 'Z' (the computable case of
    section 10) give UTC, '/' local time."""
    zone = "local" if b[6] == 0x2F else "utc"
    return 10 * _d(b[0]) + _d(b[1]), 10 * _d(b[2]) + _d(b[3]), 10 * _d(b[4]) + _d(b[5]), zone


def val_time_hms(b):
    """(hour, minute, second), UTC."""
    return 10 * _d(b[0]) + _d(b[1]), 10 * _d(b[2]) + _d(b[3]), 10 * _d(b[4]) + _d(b[5])


# --- Section 4: uncompressed position -----------------------------------

LEVEL_STEP = (1, 10, 100, 1000, 6000)
_LAT_BLANKS = (6, 5, 3, 2)
_LON_BLANKS = (7, 6, 4, 3)


def val_lat_amb(b):
    """The level: SP at offsets 6, 5, 3, 2, counted in that order up to the
    first byte that is not SP."""
    level = 0
    while level < 4 and b[_LAT_BLANKS[level]] == SP:
        level += 1
    return level


def val_lat(b, level):
    """Q in 1/6000 degree; a blanked digit counts as 0, so n is the edge of
    the box nearest to the equator (amb.val.ambiguity)."""
    s = -1 if b[7] == 0x53 else 1
    n = 6000 * (10 * _d(b[0]) + _d(b[1])) + 100 * (10 * _d(b[2]) + _d(b[3])) + 10 * _d(b[5]) + _d(b[6])
    return Q("deg/6000", s * n, LEVEL_STEP[level])


def val_lon(b, level):
    """Q in 1/6000 degree. The level of lat covers the first `level` offsets
    of 7, 6, 4, 3; a covered byte counts as 0. A SP that the level does not
    cover counts as 0 too, and the step becomes that of the lowest level
    that covers every SP (section 10, lon.amb unstated)."""
    covered = set(_LON_BLANKS[:level])
    top = level
    for i, off in enumerate(_LON_BLANKS):
        if b[off] == SP:
            top = max(top, i + 1)
    dig = [0 if i in covered else _d(c) for i, c in enumerate(b)]
    s = -1 if b[8] == 0x57 else 1
    n = 6000 * (100 * dig[0] + 10 * dig[1] + dig[2]) + 100 * (10 * dig[3] + dig[4]) + 10 * dig[6] + dig[7]
    return Q("deg/6000", s * n, LEVEL_STEP[top])


def hemisphere(b, letter_index, negative):
    """s of val.dao.lat and val.dao.lon: the sign of the hemisphere letter."""
    return -1 if b[letter_index] == negative else 1


# --- Section 5: symbol --------------------------------------------------


def val_sym(table, code, lower_overlay):
    """(classic number, overlay byte or None) of the table and code bytes.

    lower_overlay lets 'a'-'j' give the overlay '0'-'9': in cmp.table by
    val.sym, in sym.table and mice.sym.table only in permissive mode
    (01-record section 3). The classic number is that of RFC 5.6 and
    01-record section 7."""
    c = code - 33
    if table == 0x2F:
        return c, None
    if table == 0x5C:
        d, overlay = 0, None
    elif 0x30 <= table <= 0x39:
        d, overlay = table - 0x30 + 1, table
    elif 0x41 <= table <= 0x5A:
        d, overlay = table - 0x41 + 11, table
    elif lower_overlay and 0x61 <= table <= 0x6A:
        d, overlay = table - 0x61 + 1, table - 0x61 + 0x30
    else:
        return None, None
    return 94 + c * 37 + d, overlay


# --- Section 6: compressed position block -------------------------------

CMP_ORIGIN = 34283340  # 90 * 380926 = 180 * 190463 (section 6)
CMP_SOURCE = ("other", "GLL", "GGA", "RMC")


def val_cmp_lat(b):
    return Q("deg/380926", CMP_ORIGIN - b91(b))


def val_cmp_lon(b):
    return Q("deg/190463", b91(b) - CMP_ORIGIN)


def val_cmp_crs(b):
    return Q("deg", 4 * (b[0] - 33), 4)


def val_cmp_spd(b):
    return Q("knot.cmp", b[1] - 33)


def val_cmp_rng(b):
    return Q("mile.cmp", b[1] - 33)


def val_cmp_alt(b):
    return Q("foot.cmp", 91 * (b[0] - 33) + b[1] - 33)


def val_cmp_t(b):
    """(fix age, NMEA source, origin code)."""
    t = b[0] - 33
    return ("current" if (t // 32) % 2 else "old"), CMP_SOURCE[(t // 8) % 4], t % 8


# --- Section 7: Mic-E ---------------------------------------------------


def mice_dest_byte(c):
    """(digit or None for a blank, flag, kind) of one destination byte
    (04 section 3). kind is "s" for a standard 1, "c" for a custom 1, None
    for flag 0. A byte outside the table gives (None, 0, None); the
    tokenizer has given syntax for it."""
    if 0x30 <= c <= 0x39:
        return c - 0x30, 0, None
    if 0x41 <= c <= 0x4A:
        return c - 0x41, 1, "c"
    if c == 0x4B:
        return None, 1, "c"
    if c == 0x4C:
        return None, 0, None
    if 0x50 <= c <= 0x59:
        return c - 0x50, 1, "s"
    if c == 0x5A:
        return None, 1, "s"
    return None, 0, None


def val_mice_lat(dest):
    """(Q in 1/6000 degree, level) from the six destination bytes."""
    parts = [mice_dest_byte(c) for c in dest[:6]]
    dig = [p[0] or 0 for p in parts]
    level = 0
    while level < 4 and parts[5 - level][0] is None:
        level += 1
    s = 1 if parts[3][1] else -1
    n = 6000 * (10 * dig[0] + dig[1]) + 100 * (10 * dig[2] + dig[3]) + 10 * dig[4] + dig[5]
    return Q("deg/6000", s * n, LEVEL_STEP[level]), level


def mice_lat_sign(dest):
    return 1 if mice_dest_byte(dest[3])[1] else -1


def mice_lon_sign(dest):
    return -1 if mice_dest_byte(dest[5])[1] else 1


def val_mice_lon(deg, mins, hun, dest, level):
    """Q in 1/6000 degree, by steps 1 to 6 of section 7."""
    D = deg - 28
    if mice_dest_byte(dest[4])[1]:
        D += 100
    if 180 <= D <= 189:
        D -= 80
    elif 190 <= D <= 199:
        D -= 190
    M = mins - 28
    if M >= 60:
        M -= 60
    H = hun - 28
    if level >= 1:
        H -= H % 10
    if level >= 2:
        H = 0
    if level >= 3:
        M -= M % 10
    if level >= 4:
        M = 0
    return Q("deg/6000", mice_lon_sign(dest) * (6000 * D + 100 * M + H), LEVEL_STEP[level])


def val_mice_spd(sp, dc):
    S = 10 * (sp - 28) + (dc - 28) // 10
    if S >= 800:
        S -= 800
    return Q("knot", S)


def val_mice_crs(dc, se):
    """Q in degrees, or None for C = 0, an unknown course."""
    C = 100 * ((dc - 28) % 10) + se - 28
    if C >= 400:
        C -= 400
    return Q("deg", C) if C else None


def val_mice_msg(dest):
    """("emergency", None), ("standard", i), ("custom", i), or None for a mix
    of standard and custom (amb.mice.dest)."""
    parts = [mice_dest_byte(c) for c in dest[:3]]
    kinds = {p[2] for p in parts if p[1]}
    if not kinds:
        return "emergency", None
    if len(kinds) > 1:
        return None
    a, b, c = (p[1] for p in parts)
    return ("standard" if kinds == {"s"} else "custom"), 7 - (4 * a + 2 * b + c)


def val_mice_alt(b):
    return Q("metre", b91(b[:3]) - 10000)


def val_mice_msgcap(c):
    """Messaging flag, or None for '>' and ']'."""
    if c == 0x60:
        return True
    if c == 0x27:
        return False
    return None


# --- Section 8: data extensions -----------------------------------------

# Reason in `why` where a value rule itself gives no value for the bytes
# (01-record section 4.2).
UNKNOWN = "unknown"


def _half(b):
    """The kind of a half of ext.csespd: "d" for digits, else its first byte
    ('.' or SP)."""
    return "d" if all(_is_digit(c) for c in b) else b[0]


def val_ext_csespd(b):
    """(course, speed): each a Q, or a `why` reason when the rule gives no
    value. Course is the count before any range check."""
    kc, ks = _half(b[0:3]), _half(b[4:7])
    if b == b"000/000" or kc == ks != "d":
        return UNKNOWN, UNKNOWN
    course = Q("deg", int(b[0:3])) if kc == "d" else "val.ext.csespd"
    speed = Q("knot", int(b[4:7])) if ks == "d" else "val.ext.csespd"
    if kc == "d" and course.n == 0 and ks == "d":
        course = "amb.val.course0"
    return course, speed


def _hgd(b, i):
    """Height, gain and directivity at offsets i, i+1, i+2 of PHG or DFS."""
    d = _d(b[i + 2])
    directivity = "omni" if d == 0 else (Q("dir45", d) if d <= 8 else None)
    return Q("foot.phg", b[i] - 0x30), _d(b[i + 1]), directivity


def val_ext_phg(b):
    """(power, height, gain, directivity). Directivity is the code "omni",
    a Q, or None for '9'."""
    height, gain, directivity = _hgd(b, 4)
    return Q("watt.phg", _d(b[3])), height, Q("dBi", gain), directivity


def val_ext_phgr(b):
    c = b[7]
    return Q("per-hour", c - 0x30 if _is_digit(c) else c - 0x37)


def val_ext_rng(b):
    return Q("mile", int(b[3:7]))


def val_ext_dfs(b):
    """(strength, height, gain, directivity)."""
    height, gain, directivity = _hgd(b, 4)
    return Q("S", _d(b[3])), height, Q("dB", gain), directivity


def val_ext_brgnrq(b):
    """(bearing, N, R, Q). N, R and Q are None if N is 0."""
    bearing = Q("deg", int(b[1:4]))
    n = _d(b[5])
    if n == 0:
        return bearing, None, None, None
    return bearing, n, Q("mile.df", _d(b[6])), _d(b[7])


def df_station(course_bytes):
    """The station value of val.ext.brgnrq from the course of the ext.csespd
    before it: "fixed" for 000, "moving" for 001 to 360, else None."""
    if not all(_is_digit(c) for c in course_bytes):
        return None
    c = int(course_bytes)
    return "fixed" if c == 0 else "moving" if c <= 360 else None


# --- Section 9: fields in a comment -------------------------------------


def val_cmt_alt(b):
    return Q("foot", int(b[3:9]))


def val_cmt_alt_neg(b):
    return Q("foot", -int(b[4:9]))


NAMED_DATUMS = frozenset(b"WwNnOo")


def val_dao_datum(b):
    """The byte D, as one byte."""
    return b[1:2]


def val_dao_coord(b, i, base, s):
    """val.dao.lat (i = 2) or val.dao.lon (i = 3) on a base count in 1/6000
    degree. Returns a Q, None when the byte is SP (no added precision), or
    "amb.val.daorange" when a base-91 digit is above 90."""
    c = b[i]
    if c == SP:
        return None
    if 0x41 <= b[1] <= 0x5A:
        return Q("deg/60000", 10 * base + s * (c - 0x30))
    a = c - 33
    if a > 90:
        return "amb.val.daorange"
    return Q("deg/6000000", 1000 * base + s * 11 * a, 11)


# --- Section 10: effect of findings -------------------------------------
#
# Each function takes one finding that concerns the value (section 2.3)
# and the bytes of the token it is on, and returns the effect. A finding
# that no row names has the effect kept.


def effect_time(f, s, b):
    """time.dhm, time.hms: all values of the timestamp."""
    if f.kind == "syntax":
        if f.offset - s == 6 and len(b) == 7 and b[6] == 0x5A:
            return COMPUTABLE
        return NONE
    if f.kind == "value":
        return NONE
    return KEPT


def effect_coord(f, b, deg_n, deg_max):
    """lat or lon, on the coordinate of its own token. A `value` finding has
    one of two causes, found from the bytes, not from the offset of the
    finding (section 2.3)."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "value":
        deg = int(b[:deg_n]) if all(_is_digit(c) for c in b[:deg_n]) else -1
        mins = [b[i] for i in (deg_n, deg_n + 1, deg_n + 3, deg_n + 4) if i < len(b)]
        if deg > deg_max or deg == deg_max and any(_is_digit(c) and c != 0x30 for c in mins):
            return NONE
        return COMPUTABLE
    if f.rule == "lon.amb" and f.kind == "unstated":
        return COMPUTABLE
    return KEPT


def effect_lat_level(f):
    """lat and lat.amb on val.lat.amb, and lat on val.lon (the level). Only a
    syntax finding on lat.amb removes the level from val.lon; for
    val.lat.amb any syntax does ([proposed] rows of section 10)."""
    return NONE if f.kind == "syntax" else KEPT


def effect_sym(f, table_byte, table_rule):
    """sym.table, sym.code and the compressed and Mic-E forms. 'a'-'j' in
    sym.table or mice.sym.table is computable: permissive mode converts it
    (01-record section 3)."""
    if f.kind != "syntax":
        return KEPT
    if f.rule == table_rule and table_rule != "cmp.table" and 0x61 <= table_byte <= 0x6A:
        return COMPUTABLE
    return NONE


def effect_cmp(f):
    """cmp.lat, cmp.lon (syntax or value) and cmp.cs* (syntax): none."""
    return NONE if f.kind in ("syntax", "value") else KEPT


def effect_cmp_t(f, on_t):
    """cmp.t on val.cmp.t (on_t) or on the value of the cs token."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "value":
        return COMPUTABLE if on_t else KEPT
    return KEPT


def effect_mice_dest(f, dest, value):
    """dest.mice and its children; value is "lat", "lon" or "msg"."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "value":
        if value != "lat":
            return KEPT
        parts = [mice_dest_byte(c) for c in dest[:6]]
        if parts[0][0] is not None and parts[1][0] is not None:
            deg = 10 * parts[0][0] + parts[1][0]
            if deg > 90 or deg == 90 and any(p[0] for p in parts[2:]):
                return NONE
        return COMPUTABLE
    if f.kind == "unstated":
        return NONE if value == "msg" else KEPT
    return KEPT


def effect_mice_lon(f):
    """mice.lon.deg, mice.lon.min, mice.lon.hun on val.mice.lon."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "value":
        return COMPUTABLE
    return KEPT


def effect_mice_dc(f, dc, course):
    """mice.dc on val.mice.spd (course False) or val.mice.crs (course True);
    mice.sp and mice.se give none on syntax only."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "value" and f.rule == "mice.dc":
        if course:
            return NONE
        return COMPUTABLE if (dc - 28) % 10 >= 8 else KEPT
    return KEPT


def effect_mice_alt(f):
    """mice.alt on val.mice.alt. `ambiguous` on mice.alt is only the overlap
    of amb.cmt.overlap: computable, as for cmt.alt ([proposed] row of
    section 10)."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "ambiguous":
        return COMPUTABLE
    return KEPT


def effect_csespd(f, b, half):
    """ext.csespd on its course (half 0) or speed (half 1)."""
    if f.kind == "value":
        return NONE if half == 0 else KEPT
    if f.kind in ("unstated", "ambiguous") and _half(b[0:3]) != _half(b[4:7]):
        # amb.ext.csespd: the half with digits is computable; the other half
        # has no value under val.ext.csespd itself.
        return COMPUTABLE
    # Any other ambiguous: the narrowest interpretation (README section 3.1).
    return KEPT


def effect_ext_value(f, removes):
    """ext.phg, ext.phgr, ext.dfs (directivity '9') and ext.brgnrq (bearing
    above 360): a `value` finding removes the value it is about (removes is
    True for that value) and keeps the others."""
    if f.kind == "value":
        return NONE if removes else KEPT
    return KEPT


def effect_cmt_alt(f, overlap):
    """cmt.alt, cmt.alt.neg. An ambiguous finding is either several
    altitudes (kept) or an overlap with another token (computable); overlap
    says whether the bytes show the second cause."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "ambiguous":
        return COMPUTABLE if overlap else KEPT
    return KEPT


def effect_dao(f, datum):
    """cmt.dao on val.dao.datum (datum True) or val.dao.lat and val.dao.lon."""
    if f.kind == "ambiguous":
        return NONE
    if f.kind == "unstated":
        return KEPT if datum else NONE
    return KEPT


# --- 11-values-object section 3: name and state ---------------------------


def val_obj_name(b):
    """The 9 bytes without the SP bytes at the end."""
    return b.rstrip(b" ")


def val_obj_state(c):
    """True for live, False for killed, None for another byte."""
    return True if c == 0x2A else False if c == 0x5F else None


def val_item_state(c):
    return True if c == 0x21 else False if c == 0x5F else None


# --- 11-values-object section 6: effect of one finding --------------------


def effect_obj_name(f):
    """obj.name on val.obj.name, item.name on val.item.name."""
    if f.kind == "syntax":
        return NONE
    if f.kind in ("unstated", "value"):
        # Nine SP bytes; an Item name of fewer than 3 or more than 9 bytes.
        return COMPUTABLE
    return KEPT


def effect_obj_state(f):
    return NONE if f.kind == "syntax" else KEPT


# --- 12-values-weather sections 2 to 5 -------------------------------------

_FILL = frozenset(b". ")
WX_UNITS = {
    "wx.wdir": "deg",
    "wx.wspd": "mph",
    "wx.gust": "mph",
    "wx.temp": "degF",
    "wx.rain1h": "inch/100",
    "wx.rain24h": "inch/100",
    "wx.rainmid": "inch/100",
    "wx.hum": "percent",
    "wx.baro": "hPa/10",
    "wx.lum": "W/m2",
    "wx.lumk": "W/m2",
    "wx.snow": "inch",
}


def _is_fill(b):
    return bool(b) and all(c in _FILL for c in b)


def wx_number(b, signed=False):
    """Section 2.1: (n, d) of the digits of b, with at most one '.' and,
    where signed, a leading '-'. None if b is not such a number."""
    neg = signed and b[:1] == b"-"
    whole, _, frac = (b[1:] if neg else b).partition(b".")
    digits = whole + frac
    if not digits.isdigit():
        return None
    n = int(digits)
    return (-n if neg else n), 10 ** len(frac)


def val_wx(rule, b):
    """The value of one weather field from its value bytes b (without the
    letter): a Q, UNKNOWN for the unknown fill, or None where the bytes are
    no number (the tokenizer has then given syntax)."""
    if _is_fill(b):
        return UNKNOWN
    num = wx_number(b, rule == "wx.temp")
    if num is None:
        return None
    n, d = num
    if rule == "wx.hum" and b == b"00":
        n = 100
    elif rule == "wx.lumk":
        n += 1000 * d
    return Q(WX_UNITS[rule], n, 1, d)


WDIR0 = "amb.val.wdir0"
CALM = "amb.val.calm"


def val_wx_wind(b):
    """val.wx.wind: (direction, speed) of an ext.dirspd token. Each is a Q,
    UNKNOWN (fill), CALM (the direction of the pair 000/000), WDIR0
    (direction 0 with a speed), or None where the bytes are no number."""
    direction, speed = b[0:3], b[4:7]
    if direction == b"000" and speed == b"000":
        # 12-values-weather section 4: no direction; the speed is 0, with
        # the effect computable.
        return CALM, Q("knot", 0)
    out = []
    for part, unit in ((direction, "deg"), (speed, "knot")):
        if len(part) == 3 and _is_fill(part):
            out.append(UNKNOWN)
            continue
        num = wx_number(part) if len(part) == 3 else None
        out.append(Q(unit, num[0], 1, num[1]) if num is not None else None)
    if isinstance(out[0], Q) and out[0].n == 0:
        out[0] = WDIR0
    return out[0], out[1]


def val_time_mdhm(b):
    return 10 * _d(b[0]) + _d(b[1]), 10 * _d(b[2]) + _d(b[3]), 10 * _d(b[4]) + _d(b[5]), 10 * _d(b[6]) + _d(b[7])


# --- 12-values-weather section 6: effect of one finding --------------------


def effect_time_mdhm(f):
    return NONE if f.kind in ("syntax", "value") else KEPT


def effect_wind(f, s, speed):
    """ext.dirspd at offset s, on the direction or (speed True) the speed."""
    if f.kind == "syntax":
        return NONE if speed or f.offset - s < 4 else KEPT
    if f.kind == "value":
        return KEPT if speed else NONE
    return KEPT


def effect_wx(f, rule):
    """A weather field of 06 section 6.1, wx.sw or wx.unit."""
    if f.kind == "syntax":
        return NONE
    if f.kind == "value":
        return COMPUTABLE if rule == "wx.temp" else NONE
    if f.kind == "unstated":
        return KEPT if rule == "wx.sw" else COMPUTABLE
    if f.kind == "ambiguous" and rule == "wx.hum":
        # amb.wx.hum100: the bytes `100`.
        return COMPUTABLE
    return KEPT


# --- 13-values-telemetry sections 2 to 5 -----------------------------------

MIC = "val.tlm.seq"
_BITS = frozenset(b"01")


def tlm_field(b):
    """The bytes of a comma-delimited token without the ',' at its end."""
    return b[:-1] if b.endswith(b",") else b


def val_tlm_number(b):
    """Section 2.1: the raw value of a number, or None where b is none."""
    num = wx_number(b, True)
    return Q("raw", num[0], 1, num[1]) if num is not None else None


def _seq_digits(b):
    """The digits between '#' and ',' of a tlm.seq token, or None."""
    if b[:1] != b"#" or not b.endswith(b","):
        return None
    body = b[1:-1]
    return body if body.isdigit() and len(body) <= 9 else None


def val_tlm_seq(b):
    """val.tlm.seq: an integer, MIC for the sequence MIC, or None."""
    if b[:4] == b"#MIC":
        return MIC
    body = _seq_digits(b)
    return int(body) if body is not None else None


def val_tlm_bits(b):
    """val.tlm.digital and val.tlm.bits.sense: B1 first."""
    if len(b) != 8 or any(c not in _BITS for c in b):
        return None
    return [c == 0x31 for c in b]


def val_b91_bits(b):
    """val.tlm.b91.bits: bit i of the number is B(i + 1)."""
    n = b91(b)
    return [bool(n >> i & 1) for i in range(8)]


# --- 13-values-telemetry section 6: effect of one finding -------------------


def effect_tlm_seq(f, b):
    if f.kind == "syntax":
        return COMPUTABLE if _seq_digits(b) is not None else NONE
    return NONE if f.kind == "unstated" else KEPT


def effect_tlm_analog(f):
    return NONE if f.kind == "syntax" else KEPT


def effect_tlm_station(f):
    """An addressee name: its bytes are certain, so unstated is kept."""
    return NONE if f.kind == "syntax" else KEPT


def effect_tlm_text(f, long_kept=False):
    """A name, unit, label or title. A value finding is computable; on a
    name, unit or label that is too long it is kept (long_kept)."""
    if f.kind == "syntax":
        return NONE
    return COMPUTABLE if f.kind == "value" and not long_kept else KEPT


def effect_tlm_coef(f):
    return NONE if f.kind in ("syntax", "unstated") else KEPT


# --- 14-values-status section 3 --------------------------------------------


def val_stat_beam(b):
    """val.stat.beam: (heading, power) of the three bytes of stat.beam."""
    h = b[1] - 0x30 if _is_digit(b[1]) else b[1] - 0x37
    return Q("deg", 10 * h, 10), Q("watt.erp", b[2] - 0x30)


# --- 15-values-message section 6: effect of one finding ---------------------


def effect_msg_number(f):
    """A message number, a reply-ack field or a reference identifier."""
    if f.kind == "syntax":
        return NONE
    return COMPUTABLE if f.kind in ("value", "unstated") else KEPT


# --- 16-values-frequency ------------------------------------------------------

# val.freq.uw: the letter gives the frequency in hundreds of megahertz.
UW_HUNDREDS = dict(zip(b"ABCDEFGHIJKLMNO", (12, 23, 24, 34, 56, 57, 58, 101, 102, 103, 104, 105, 240, 241, 242)))
RANGE_DIRS = {0x52: "all", 0x4E: "north", 0x53: "south", 0x45: "east", 0x57: "west"}
TONE_KINDS = {0x54: "tone", 0x43: "ctcss", 0x44: "dcs"}
# val.freq.tone: the tones of the list of 16-values-frequency section 4, in
# tenths of a hertz, by their whole part.
_TONES = (670, 693, 719, 744, 770, 797, 825, 854, 885, 915, 948, 974, 1000, 1035, 1072, 1109, 1148, 1188, 1230, 1273)
_TONES += (1318, 1365, 1413, 1462, 1514, 1567, 1622, 1679, 1738, 1799, 1862, 1928, 2035, 2107, 2181, 2257, 2336, 2418, 2503)
# The 12 common tones that are not in the standard.
_TONES += (1500, 1598, 1655, 1713, 1773, 1835, 1899, 1966, 1995, 2065, 2291, 2541)
TONE_TENTHS = {t // 10: t for t in _TONES}
TONE0 = "amb.val.tone0"
TONE_IN_TENTHS = "amb.val.tonetenths"
TONE_RANGE = "amb.val.tonerange"


def val_freq(rule, b):
    """val.freq.mhz, val.freq.uw and val.freq.ghz."""
    if rule == "freq.ghz":
        return Q("MHz", 1000 * int(b[0:3].replace(b" ", b"0")) + int(b[4:7]))
    mhz = int(b[0:3]) if rule == "freq.mhz" else 100 * UW_HUNDREDS[b[0]] + int(b[1:3])
    if b[6] == 0x20:
        return Q("kHz", 1000 * mhz + 10 * int(b[4:6]), 10)
    return Q("kHz", 1000 * mhz + int(b[4:7]))


def val_freq_rx(b):
    return Q("kHz", 1000 * int(b[0:3]) + int(b[4:7]))


def val_freq_tone(b):
    """(kind, tone frequency or None, DCS code or None, narrow, the
    catalogue row that makes the tone computable or None)."""
    narrow = 0x61 <= b[0] <= 0x7A
    if b[1:] == b"off":
        return "off", None, None, narrow, None
    if b[1:] == b"750":
        return "burst", Q("Hz", 1750), None, narrow, None
    kind = TONE_KINDS[b[0] & 0xDF]
    if kind == "dcs":
        return kind, None, b[1:4], narrow, None
    n = int(b[1:4])
    if n in TONE_TENTHS:
        return kind, Q("Hz", TONE_TENTHS[n], 1, 10), None, narrow, None
    if n == 0:
        return kind, Q("Hz", 0), None, narrow, TONE0
    if n in _TONES:
        return kind, Q("Hz", n, 1, 10), None, narrow, TONE_IN_TENTHS
    # A number that is not in the list is a value only from 60 to 300.
    return kind, Q("Hz", n), None, narrow, None if 60 <= n <= 300 else TONE_RANGE


def val_freq_offset(b):
    n = int(b[1:4])
    return Q("10kHz", -n if b[0] == 0x2D else n)


def val_freq_range(b):
    """(direction, range)."""
    return RANGE_DIRS[b[0]], Q("mile" if b[3] == 0x6D else "km", int(b[1:3]))


def val_freq_dstar(b):
    """(repeater, module) of the form of 15 bytes, or None."""
    return (b[7:13].rstrip(b" "), b[14:15]) if len(b) == 15 else None
