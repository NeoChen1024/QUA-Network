# SPDX-License-Identifier: Apache-2.0
"""The record of one legacy packet: docs/interop/01-record.md.

The decoder runs the tokenizer, applies the value rules of the value files
of docs/legacy (values.py) and converts each value to its record unit
(section 4.3). It reads no byte outside the tokens that a value rule names
(section 2). The object body is that of docs/interop/02-object.md, and the
weather body that of docs/interop/03-weather.md. The telemetry body and
the telemetry definition body are those of docs/interop/04-telemetry.md.
The status body is that of docs/interop/05-status.md. The message body and
the bulletin body are those of docs/interop/06-message.md. The frequency
body is that of docs/interop/07-frequency.md. The capabilities body is that
of docs/interop/08-capabilities.md.
"""

import calendar
import datetime
from functools import lru_cache

from qua_network.interop.values import (
    CALM,
    COMPUTABLE,
    KEPT,
    MIC,
    NAMED_DATUMS,
    NONE,
    UNKNOWN,
    WDIR0,
    Q,
    b91,
    df_station,
    effect_cmp,
    effect_cmp_t,
    effect_cmt_alt,
    effect_coord,
    effect_csespd,
    effect_dao,
    effect_ext_value,
    effect_lat_level,
    effect_mice_alt,
    effect_mice_dc,
    effect_mice_dest,
    effect_mice_lon,
    effect_msg_number,
    effect_obj_name,
    effect_obj_state,
    effect_sym,
    effect_time,
    effect_time_mdhm,
    effect_tlm_analog,
    effect_tlm_coef,
    effect_tlm_seq,
    effect_tlm_station,
    effect_tlm_text,
    effect_wind,
    effect_wx,
    hemisphere,
    mice_lat_sign,
    mice_lon_sign,
    tlm_field,
    val_b91_bits,
    val_cmp_alt,
    val_cmp_crs,
    val_cmp_lat,
    val_cmp_lon,
    val_cmp_rng,
    val_cmp_spd,
    val_cmp_t,
    val_cmt_alt,
    val_cmt_alt_neg,
    val_dao_coord,
    val_dao_datum,
    val_ext_brgnrq,
    val_ext_csespd,
    val_ext_dfs,
    val_ext_phg,
    val_ext_phgr,
    val_ext_rng,
    val_freq,
    val_freq_dstar,
    val_freq_offset,
    val_freq_range,
    val_freq_rx,
    val_freq_tone,
    val_item_state,
    val_lat,
    val_lat_amb,
    val_lon,
    val_mice_alt,
    val_mice_crs,
    val_mice_dti,
    val_mice_lat,
    val_mice_lon,
    val_mice_msg,
    val_mice_msgcap,
    val_mice_spd,
    val_obj_name,
    val_obj_state,
    val_pos_dti,
    val_stat_beam,
    val_sym,
    val_time_dhm,
    val_time_hms,
    val_time_mdhm,
    val_tlm_bits,
    val_tlm_number,
    val_tlm_seq,
    val_wx,
    val_wx_wind,
)
from qua_network.legacy.tokenizer import tokenize
from qua_network.tnc2 import header_spans

RECORD_LAYOUT = 0
MODES = ("strict", "permissive")
# 01-record section 3.1: the repairs of permissive mode.
REPAIRS = ("repair.humidity-width", "repair.overlay-lowercase")

# --- Section 4.3: record units ------------------------------------------
#
# Each entry gives (v, res) from (n, w), or from the code k for a
# non-linear unit. int / int is the correctly rounded quotient, so a value
# is the double nearest to the exact result of its formula (section 4.6).


@lru_cache(maxsize=None)
def _knot_cmp(k):
    return (108**k - 100**k) * 1852 / (100**k * 1000), 8 * 108**k * 1852 / (100 ** (k + 1) * 1000)


@lru_cache(maxsize=None)
def _foot_cmp(k):
    return 1002**k * 3048 / (1000**k * 10000), 2 * 1002**k * 3048 / (1000 ** (k + 1) * 10000)


@lru_cache(maxsize=None)
def _mile_cmp(k):
    return 2 * 108**k * 1609344 / (100**k * 1000000), 16 * 108**k * 1609344 / (100 ** (k + 1) * 1000000)


def _same(v):
    return v, v


UNITS = {
    "deg/6000": lambda n, w: (n / 6000, w / 6000),
    "deg/60000": lambda n, w: (n / 60000, w / 60000),
    "deg/6000000": lambda n, w: (n / 6000000, w / 6000000),
    "deg/380926": lambda n, w: (n / 380926, w / 380926),
    "deg/190463": lambda n, w: (n / 190463, w / 190463),
    "deg": lambda n, w: (n, w),
    "dir45": lambda k, w: (45 * k, 45),
    "knot": lambda n, w: (n * 1852 / 1000, w * 1852 / 1000),
    "knot.cmp": lambda k, w: _knot_cmp(k),
    "foot": lambda n, w: (n * 3048 / 10000, w * 3048 / 10000),
    "foot.cmp": lambda k, w: _foot_cmp(k),
    "foot.phg": lambda k, w: _same(10 * 2**k * 3048 / 10000),
    "metre": lambda n, w: (n, w),
    "mile": lambda n, w: (n * 1609344 / 1000000, w * 1609344 / 1000000),
    "mile.cmp": lambda k, w: _mile_cmp(k),
    "mile.df": lambda k, w: _same(2**k * 1609344 / 1000000),
    "watt.phg": lambda k, w: (k * k, 2 * k + 1),
    "dBi": lambda n, w: (n, w),
    "dB": lambda n, w: (n, w),
    "S": lambda n, w: (n, w),
    "per-hour": lambda n, w: (n, w),
    # 03-weather section 3.1.
    "mph": lambda n, w: (n * 1609344 / 1000000, w * 1609344 / 1000000),
    "degF": lambda n, w: ((n - 32) * 5 / 9, w * 5 / 9),
    "inch/100": lambda n, w: (n * 254 / 1000, w * 254 / 1000),
    "inch": lambda n, w: (n * 254 / 10, w * 254 / 10),
    "percent": lambda n, w: (n, w),
    "hPa/10": lambda n, w: (n / 10, w / 10),
    "W/m2": lambda n, w: (n, w),
    # 04-telemetry section 3.1: a raw value has no record unit.
    "raw": lambda n, w: (n, w),
    # 05-status section 3.1.
    "watt.erp": lambda k, w: (10 * k * k, 10 * (2 * k + 1)),
    # 07-frequency section 3.1.
    "kHz": lambda n, w: (n / 1000, w / 1000),
    "MHz": lambda n, w: (n, w),
    "10kHz": lambda n, w: (n / 100, w / 100),
    "Hz": lambda n, w: (n, w),
    "km": lambda n, w: (n, w),
}


def number(x):
    """A number for JSON: an integral double within 2^53 is written without
    a fraction (section 4.6)."""
    if isinstance(x, float) and x.is_integer() and abs(x) < 2**53:
        return int(x)
    return x


def quantity(q):
    n, w = (q.n, q.w) if q.d == 1 else (q.n / q.d, q.w / q.d)
    v, res = UNITS[q.unit](n, w)
    return {"v": number(v), "res": number(res)}


def text(b):
    """A byte string (section 4.1): each byte the character with its number."""
    return b.decode("latin-1")


# Tokens that a value rule reads (the column "Tokens" of the value files,
# and cmp.cs of 10-values section 10). The identifier of an Object or an
# Item is read: `format` gives it. cmt.text is in the body.
READ = frozenset(
    (
        "pos.dti",
        "mice.dti",
        "obj.dti",
        "item.dti",
        "obj.name",
        "obj.state",
        "item.name",
        "item.state",
        "wx.pos",
        "wx.obj",
        "wx.pl",
        "time.mdhm",
        "ext.dirspd",
        "cmp.cs.wind",
        "wx.wdir",
        "wx.wspd",
        "wx.gust",
        "wx.temp",
        "wx.rain1h",
        "wx.rain24h",
        "wx.rainmid",
        "wx.hum",
        "wx.baro",
        "wx.lum",
        "wx.lumk",
        "wx.snow",
        "wx.sw",
        "wx.unit",
        "tlm.dti",
        "tlm.seq",
        "tlm.analog",
        "tlm.digital",
        "tlm.b91",
        "tlm.b91.seq",
        "tlm.b91.analog",
        "tlm.b91.bits",
        "tlm.def.dti",
        "msg.addr.name",
        "msg.addr.pad",
        "msg.sep",
        "tlm.parm",
        "tlm.parm.name",
        "tlm.unit",
        "tlm.unit.label",
        "tlm.eqns",
        "tlm.eqns.coef",
        "tlm.bits",
        "tlm.bits.sense",
        "tlm.bits.title",
        "stat.dti",
        "grid.loc",
        "stat.beam",
        "msg.dti",
        "msg.id.open",
        "msg.id",
        "msg.id.mm",
        "msg.id.close",
        "msg.id.aa",
        "msg.ack.kw",
        "msg.rej.kw",
        "msg.ack.num",
        "bln.dti",
        "nws.dti",
        "bln.kw",
        "bln.num",
        "bln.ann",
        "bln.group",
        "nws.kw",
        "nws.level",
        "nws.ref",
        "cap.dti",
        "cap.item",
        "cap.sep",
        "cap.token",
        "cap.value",
        "cap.pad",
        "freq.lead",
        "freq.mhz",
        "freq.uw",
        "freq.ghz",
        "freq.rx",
        "freq.tone",
        "freq.offset",
        "freq.range",
        "freq.dstar",
        "time.dhm",
        "time.hms",
        "lat",
        "lon",
        "sym.table",
        "sym.code",
        "cmp.table",
        "cmp.lat",
        "cmp.lon",
        "cmp.code",
        "cmp.cs",
        "cmp.cs.crs",
        "cmp.cs.rng",
        "cmp.cs.alt",
        "cmp.t",
        "mice.lon.deg",
        "mice.lon.min",
        "mice.lon.hun",
        "mice.sp",
        "mice.dc",
        "mice.se",
        "mice.sym.code",
        "mice.sym.table",
        "mice.alt",
        "mice.type.prefix",
        "ext.csespd",
        "ext.phg",
        "ext.phgr",
        "ext.rng",
        "ext.dfs",
        "ext.brgnrq",
        "cmt.alt",
        "cmt.alt.neg",
        "cmt.dao",
        "cmt.noarchive",
    )
)
EXT_RULES = ("ext.csespd", "ext.phg", "ext.phgr", "ext.rng", "ext.dfs", "ext.brgnrq")
ALT_RULES = ("cmt.alt", "cmt.alt.neg")
# 01-record section 7.1: the comment of the position body leaves out the
# bytes of these tokens.
COMMENT_OUT = ALT_RULES + ("cmt.dao", "tlm.b91")
TIME_RULES = ("time.dhm", "time.hms", "time.mdhm")
# Formats that have a position body, and those that also have an object body.
POSITION_FORMATS = ("pos.dti", "mice.dti", "obj.dti", "item.dti", "wx.pos", "wx.obj")
OBJECT_FORMATS = ("obj.dti", "item.dti", "wx.obj")
# Formats whose identifier is that of a position report (val.pos.dti), and
# Object formats, which can have a timestamp.
REPORT_FORMATS = ("pos.dti", "wx.pos")
OBJ_TIME_FORMATS = ("obj.dti", "wx.obj")
WEATHER_FORMATS = ("wx.pos", "wx.obj", "wx.pl")
# 03-weather section 3: field, token rules. The first two are also the wind.
WX_FIELDS = (
    ("wind_direction", ("wx.wdir",)),
    ("wind_speed", ("wx.wspd",)),
    ("gust", ("wx.gust",)),
    ("temperature", ("wx.temp",)),
    ("rain_1h", ("wx.rain1h",)),
    ("rain_24h", ("wx.rain24h",)),
    ("rain_midnight", ("wx.rainmid",)),
    ("snow_24h", ("wx.snow",)),
    ("humidity", ("wx.hum",)),
    ("pressure", ("wx.baro",)),
    ("luminosity", ("wx.lum", "wx.lumk")),
)
WX_ORDER = tuple(name for name, _ in WX_FIELDS) + ("software", "unit", "comment")
WX_NOTES = {"rain_midnight": "amb.val.midnight", "pressure": "amb.val.baroref"}
# The leading fields of a positionless report (06 section 6.2).
WX_LEADING = ("wx.wdir", "wx.wspd", "wx.gust", "wx.temp")
# 04-telemetry sections 3 and 4.
TLM_ORDER = ("sequence", "analog", "digital", "comment")
TLM_DEF_ORDER = ("station", "kind", "names", "units", "coefficients", "sense", "title")
# 05-status section 3.
STATUS_ORDER = ("locator", "symbol", "text", "beam_heading", "beam_power", "noarchive")
# 06-message sections 3 and 4.
MSG_ORDER = ("addressee", "kind", "text", "id", "reply_ack", "ack_id", "noarchive")
BLN_ORDER = ("kind", "id", "group", "level", "text", "reference", "noarchive")
# 08-capabilities section 3.
CAP_ORDER = ("items",)
# 07-frequency section 3.
FREQ_ORDER = (
    "frequency",
    "rx_frequency",
    "tone_kind",
    "tone",
    "dcs",
    "narrow",
    "offset",
    "range",
    "dstar",
    "dstar_repeater",
    "dstar_module",
)
MSG_ID_RULES = ("msg.id.open", "msg.id", "msg.id.mm", "msg.id.close", "msg.id.aa")
# Keyword token -> (kind, field of the body, item token, most fields).
TLM_LISTS = {
    "tlm.parm": ("parm", "names", "tlm.parm.name", 13),
    "tlm.unit": ("unit", "units", "tlm.unit.label", 13),
    "tlm.eqns": ("eqns", "coefficients", "tlm.eqns.coef", 15),
}
# Field order of 02-object section 3, then of section 7; notes follow it,
# then report_time.
FIELD_ORDER = (
    "object.name",
    "object.live",
    "position.lat",
    "position.lon",
    "position.ambiguity",
    "position.datum",
    "position.altitude",
    "position.course",
    "position.speed",
    "position.symbol",
    "position.messaging",
    "position.fix",
    "position.comment",
    "position.extensions",
)
FIELD_ORDER += tuple("weather." + name for name in WX_ORDER)
FIELD_ORDER += tuple("telemetry." + name for name in TLM_ORDER)
FIELD_ORDER += tuple("telemetry_definition." + name for name in TLM_DEF_ORDER)
FIELD_ORDER += tuple("status." + name for name in STATUS_ORDER)
FIELD_ORDER += tuple("message." + name for name in MSG_ORDER)
FIELD_ORDER += tuple("bulletin." + name for name in BLN_ORDER)
FIELD_ORDER += tuple("capabilities." + name for name in CAP_ORDER)
FIELD_ORDER += tuple("frequency." + name for name in FREQ_ORDER) + ("report_time",)
_DEST_CHILDREN = ("mice.dest.a", "mice.dest.b", "mice.dest.c", "mice.dest.ns", "mice.dest.lonoff", "mice.dest.we")
_DEST_RULES = frozenset(("dest.mice", "mice.dest") + _DEST_CHILDREN)
_LON_DEST_RULES = frozenset(("dest.mice", "mice.dest", "mice.dest.lonoff", "mice.dest.we"))


def _ref(t):
    return [t.rule, t.start, t.end]


class Pre:
    """A value before the mode applies: its payload (a Q or members), the
    findings that concern it with their effects, its provenance, and the
    reasons when the value rule gives no value."""

    __slots__ = ("payload", "judged", "frm", "reasons", "in_range", "notes", "extra")

    def __init__(self, payload, judged=(), frm=(), reasons=(), in_range=True, notes=(), extra=None):
        # extra: members that a value object has in addition to its kind.
        self.extra = extra
        self.payload = payload
        self.judged = list(judged)
        self.frm = list(frm)
        self.reasons = list(reasons)
        self.in_range = in_range
        self.notes = list(notes)


class Decoder:
    def __init__(self, line, received=None, received_res=None, mode="strict"):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if received is not None and received_res is None:
            raise ValueError("received_res is required with received")
        self.line = line
        self.received = received
        self.received_res = received_res
        self.mode = mode
        self.strict = mode == "strict"
        self.scan = tokenize(line, repairs=() if self.strict else REPAIRS)
        self.findings = self.scan.findings
        self.notes = []
        self.read = set()  # tokens that the body reads, beyond READ (cmt.text)
        self.weather = False  # the record has a weather body
        self.cmp_wind = None  # (direction, speed) of a compressed block in a weather report
        self.unread = set()  # tokens of READ that no value rule reads in this packet

    # --- Helpers ---------------------------------------------------------

    def toks(self, rule):
        return self.by_rule.get(rule, [])

    def tok(self, rule):
        ts = self.by_rule.get(rule)
        return ts[0] if ts else None

    def on(self, rules, t):
        """Findings with a rule of rules at an offset inside t or at its end
        (10-values section 2.3)."""
        return [f for f in self.findings if f.rule in rules and t.start <= f.offset <= t.end]

    def stop(self):
        """The syntax finding where the reader stopped: the last one in the
        information field. It is the `why` of a field whose token is
        missing (section 4.2)."""
        best = None
        for f in self.findings:
            if f.kind == "syntax" and self.info_start <= f.offset <= self.info_end and (best is None or f.offset >= best.offset):
                best = f
        return [best] if best else []

    def missing(self, frm=()):
        return Pre(None, [(f, NONE) for f in self.stop()], frm)

    def obj(self, pre, path=None, inner=False):
        """The value object of section 4.2 under the mode (section 3)."""
        worst = max((e for _, e in pre.judged), default=KEPT)
        if pre.payload is not None and worst == COMPUTABLE and not pre.in_range:
            # 10-values section 2.4: a computable number outside the range.
            worst = NONE
        bad = []
        for f, e in pre.judged:
            # f is a finding, or the ID of a catalogue row (section 4.2).
            item = f if isinstance(f, str) else list(f)
            if e != KEPT and item not in bad:
                bad.append(item)
        if pre.payload is None or worst == NONE or worst == COMPUTABLE and self.strict:
            o = {"why": pre.reasons + bad}
            if not inner:
                o["from"] = pre.frm
            return o
        o = quantity(pre.payload) if isinstance(pre.payload, Q) else dict(pre.payload)
        if pre.extra:
            o.update(pre.extra)
        if not inner:
            o["from"] = pre.frm
        if worst == COMPUTABLE:
            o["mark"] = bad
        if path is not None:
            for row in pre.notes:
                self.note(row, path)
        return o

    def note(self, row, path):
        key = path if path in FIELD_ORDER else path.split("[")[0]
        item = (FIELD_ORDER.index(key) if key in FIELD_ORDER else len(FIELD_ORDER), len(self.notes), [row, path])
        if all(n[2] != item[2] for n in self.notes):
            self.notes.append(item)

    # --- The record ------------------------------------------------------

    def run(self):
        scan, line = self.scan, self.line
        self._frame()
        out = {
            "record": RECORD_LAYOUT,
            "mode": self.mode,
            "line": text(line),
            "received": number(self.received) if self.received is not None else None,
            "source": self.source,
            "destination": self.destination,
            "path": self.path,
        }
        if self.outer is not None:
            out["outer"] = self.outer
        body = obj = wx = tlm = tdef = status = msg = bln = cap = freq = None
        if not scan.unknown_format:
            pre = wpre = tpre = None
            self.weather = self.format in WEATHER_FORMATS or self.format == "item.dti" and self._item_weather()
            if self.format in POSITION_FORMATS:
                pre = self._position()
                if self.format in OBJECT_FORMATS:
                    obj = self._object()
            if self.weather:
                wpre = self._weather(pre is not None)
            if self.format == "tlm.dti":
                tpre = self._telemetry()
            elif pre is not None and self.tok("tlm.b91") is not None:
                tpre = self._telemetry_b91()
            self._after_timestamp(pre, wpre, tpre)
            if pre is not None:
                body = self._body(pre)
            if wpre is not None:
                wx = {name: self.obj(wpre[name], "weather." + name) for name in WX_ORDER if name in wpre}
            if tpre is not None:
                tlm = self._lists(tpre, "telemetry", TLM_ORDER)
            if self.format == "tlm.def.dti":
                tdef = self._lists(self._definition(), "telemetry_definition", TLM_DEF_ORDER)
            if self.format == "stat.dti":
                status = self._lists(self._status(), "status", STATUS_ORDER)
            if self.format == "msg.dti":
                msg = self._lists(self._message(), "message", MSG_ORDER)
            if self.format in ("bln.dti", "nws.dti"):
                bln = self._lists(self._bulletin(), "bulletin", BLN_ORDER)
            if self.format == "cap.dti":
                cap = self._lists(self._capabilities(), "capabilities", CAP_ORDER)
            # 07-frequency section 2: only in a record with another body.
            fpre = self._frequency() if any(b is not None for b in (body, status)) else None
            if fpre:
                freq = self._lists(fpre, "frequency", FREQ_ORDER)
        bodies = (
            ("object", obj),
            ("position", body),
            ("weather", wx),
            ("telemetry", tlm),
            ("telemetry_definition", tdef),
            ("status", status),
            ("message", msg),
            ("bulletin", bln),
            ("capabilities", cap),
            ("frequency", freq),
        )
        has_body = any(b is not None for _, b in bodies)
        out["uses"] = [name for name, b in bodies if b is not None]
        out["format"] = self.format
        out["verdict"] = scan.verdict()
        out["findings"] = [list(f) for f in self.findings]
        rt = self._report_time(has_body)
        if rt is not None:
            out["report_time"] = rt
        for name, b in bodies:
            if b is not None:
                out[name] = b
        out["notes"] = [n[2] for n in sorted(self.notes, key=lambda n: (n[0], n[1]))]
        out["undecoded"] = self._undecoded(has_body)
        return out

    # --- Section 5: envelope ---------------------------------------------

    def _frame(self):
        """Find the information field that the record describes, and its
        header. A third-party packet is described by its innermost packet;
        `outer` is the header of the line."""
        line, tokens = self.line, self.scan.tokens
        sep = next((t for t in tokens if t.rule == "line.sep" and t.depth == 0), None)
        self.outer = None
        if sep is None:
            self.source = self.destination = None
            self.path = []
            self.info_start = self.info_end = len(line)
            self.info_depth = 0
            self.format = None
            self.header = (0, len(line))
            self._index()
            return
        self.source, self.destination, self.path = self._header(0, sep.start)
        start, depth, hdr = sep.end, 0, (0, sep.start)
        while True:
            ident = next((t for t in tokens if t.start == start and t.depth == depth), None)
            if ident is None or ident.rule != "tp.dti":
                break
            tsep = next((t for t in tokens if t.rule == "tp.sep" and t.depth == depth and t.start > start), None)
            if tsep is None:
                break
            if self.outer is None:
                self.outer = {"source": self.source, "destination": self.destination, "path": self.path}
            hdr = (ident.end, tsep.start)
            if any(t.rule == "tp.aea" and t.start == ident.end for t in tokens):
                self.source, self.destination, self.path = self._aea(*hdr)
            else:
                self.source, self.destination, self.path = self._header(*hdr)
            start, depth = tsep.end, depth + 1
        self.header = hdr
        self.info_start, self.info_end, self.info_depth = start, len(line), depth
        ident = next((t for t in tokens if t.start == start and t.depth == depth), None)
        self.format = ident.rule if ident is not None else None
        self._index()

    def _index(self):
        self.info = [t for t in self.scan.sorted_tokens() if t.start >= self.info_start and t.depth >= self.info_depth]
        self.by_rule = {}
        for t in self.info:
            self.by_rule.setdefault(t.rule, []).append(t)

    def _header(self, a, b):
        """source, destination and path of the header line[a:b]. Each path
        entry is the bytes between the separators, with its '*'."""
        spans = header_spans(self.line[a:b], a)
        if spans is None:
            return None, None, []
        (ss, se), (ds, de), entries = spans
        line = self.line
        return text(line[ss:se]), text(line[ds:de]), [text(line[s:e]) for s, e in entries]

    def _aea(self, a, b):
        """An AEA-form inner header (01-frame amb.tp.aea): addresses joined by
        '>'; the first is the source, the last the destination ([open] in
        01-record section 10)."""
        pieces = self.line[a:b].split(b">")
        return text(pieces[0]), text(pieces[-1]), [text(p) for p in pieces[1:-1]]

    # --- Section 5: undecoded --------------------------------------------

    def _undecoded(self, has_body):
        """The outermost tokens of the information field that nothing in the
        body reads. A token counts as read if a value rule reads it, if it
        is the comment of the body, or if a token inside it is read."""
        info = self.info
        parent = {}
        for i, t in enumerate(info):
            for j in range(i - 1, -1, -1):
                u = info[j]
                if u.depth == t.depth - 1 and u.start <= t.start and t.end <= u.end:
                    parent[i] = j
                    break
        read = [has_body and (t.rule in READ and t not in self.unread or t in self.read) for t in info]
        for i in sorted(parent, key=lambda i: -info[i].depth):
            if read[i]:
                read[parent[i]] = True
        return [_ref(t) for i, t in enumerate(info) if not read[i] and (i not in parent or read[parent[i]])]

    # --- Section 6: report time ------------------------------------------

    def _report_time(self, has_body):
        if not has_body and any(t.rule in TIME_RULES for t in self.info):
            # A timestamp of a format outside this slice, at any depth, has no
            # value rule: report_time is absent (section 6).
            return None
        time_tok = next((t for t in self.info if t.rule in TIME_RULES and t.depth == self.info_depth), None)
        if time_tok is None:
            if has_body and self.format in REPORT_FORMATS and val_pos_dti(self.line[self.info_start])[0]:
                # The timestamp is missing: the packet ends early.
                return self.obj(self.missing())
            if has_body and self.format == "wx.pl":
                # A positionless report always has its timestamp.
                return self.obj(self.missing())
            if has_body and self.format in OBJ_TIME_FORMATS and self.tok("lat") is None and self.tok("cmp.block") is None:
                # An Object that ends before its position: it is not known
                # whether it has a timestamp (02-object section 4).
                return self.obj(self.missing())
            if self.received is None:
                return None
            if has_body and self.format in OBJECT_FORMATS:
                self.note("amb.val.objtime", "report_time")
            return {"form": "received", "utc": number(self.received), "res": number(self.received_res), "from": []}
        b = self.line[time_tok.start : time_tok.end]
        frm = [_ref(time_tok)]
        if time_tok.rule == "time.mdhm":
            # 03-weather section 4.
            judged = [(f, effect_time_mdhm(f)) for f in self.on(("time.mdhm",), time_tok)]
            if len(b) < 8:
                return self.obj(Pre(None, judged or [(f, NONE) for f in self.stop()], frm))
            mo, d, h, m = val_time_mdhm(b)
            payload = {"form": "mdhm", "month": mo, "day": d, "hour": h, "minute": m, "zone": "utc"}
            utc = self._utc_mdhm(mo, d, h, m)
            notes = []
            if utc is not None:
                payload["utc"] = utc
                payload["res"] = 60
                notes.append("amb.val.mdhmyear")
            return self.obj(Pre(payload, judged, frm, notes=notes), "report_time")
        judged = [(f, effect_time(f, time_tok.start, b)) for f in self.on(("time.dhm", "time.hms"), time_tok)]
        if len(b) < 7:
            return self.obj(Pre(None, judged, frm))
        notes = []
        if time_tok.rule == "time.hms":
            h, m, s = val_time_hms(b)
            payload = {"form": "hms", "hour": h, "minute": m, "second": s, "zone": "utc"}
            utc = self._utc_hms(h, m, s)
            res = 1
        else:
            d, h, m, zone = val_time_dhm(b)
            payload = {"form": "dhm", "day": d, "hour": h, "minute": m, "zone": zone}
            utc = self._utc_dhm(d, h, m) if zone == "utc" else None
            res = 60
            if zone == "local":
                notes.append("amb.val.localtime")
        if utc is not None:
            payload["utc"] = utc
            payload["res"] = res
            notes.append("amb.val.timewindow")
        return self.obj(Pre(payload, judged, frm, notes=notes), "report_time")

    def _nearest(self, candidates):
        r = self.received
        best = None
        for c in sorted(candidates):
            if best is None or abs(c - r) < abs(best - r):
                best = c
        return best

    def _utc_dhm(self, d, h, m):
        """Section 6 step 1 and 3: the day and time in the month of the
        received time, the month before and the month after."""
        if self.received is None:
            return None
        now = datetime.datetime.fromtimestamp(int(self.received // 1), datetime.timezone.utc)
        out = []
        for k in (-1, 0, 1):
            y, mo = now.year, now.month + k
            if mo == 0:
                y, mo = y - 1, 12
            elif mo == 13:
                y, mo = y + 1, 1
            if d <= calendar.monthrange(y, mo)[1]:
                out.append(calendar.timegm((y, mo, d, h, m, 0)))
        return self._nearest(out)

    def _utc_mdhm(self, mo, d, h, m):
        """03-weather section 4: the date and time in the year of the
        received time, the year before and the year after."""
        if self.received is None or not 1 <= mo <= 12:
            return None
        year = datetime.datetime.fromtimestamp(int(self.received // 1), datetime.timezone.utc).year
        out = [calendar.timegm((y, mo, d, h, m, 0)) for y in (year - 1, year, year + 1) if 1 <= d <= calendar.monthrange(y, mo)[1]]
        return self._nearest(out) if out else None

    def _utc_hms(self, h, m, s):
        """Section 6 step 2 and 3: the time on the day of the received time,
        the day before and the day after."""
        if self.received is None:
            return None
        day = int(self.received // 86400) * 86400
        t = 3600 * h + 60 * m + s
        return self._nearest([day + k * 86400 + t for k in (-1, 0, 1)])

    # --- Section 7: position body ----------------------------------------

    def _position(self):
        if self.format == "mice.dti":
            pre = self._mice()
        elif self.tok("cmp.block") is not None:
            pre = self._compressed()
        elif self.tok("lat") is not None:
            pre = self._uncompressed()
        else:
            # pos.form: the packet ends, or the byte starts neither format.
            pre = {"lat": self.missing(), "lon": self.missing(), "symbol": self.missing()}
            self._messaging(pre)
        self._comment_fields(pre)
        return pre

    def _messaging(self, pre):
        """val.pos.dti: only a position report has the flag in its identifier."""
        if self.format in REPORT_FORMATS:
            dti = self.line[self.info_start]
            pre["messaging"] = Pre({"flag": val_pos_dti(dti)[1]}, (), [[self.format, self.info_start, self.info_start + 1]])

    # --- Object body (02-object section 3) -------------------------------

    def _object(self):
        line = self.line
        item = self.format == "item.dti"
        name_rule, state_rule = ("item.name", "item.state") if item else ("obj.name", "obj.state")
        body = {}
        t = self.tok(name_rule)
        fs = [f for f in self.findings if f.rule == name_rule and self.info_start <= f.offset <= self.info_end]
        if t is None:
            # No name token: the finding of the name is the reason.
            pre = Pre(None, [(f, NONE) for f in fs if f.kind == "syntax"] or [(f, NONE) for f in self.stop()])
        else:
            b = line[t.start : t.end]
            judged = [(f, effect_obj_name(f)) for f in self.on((name_rule,), t)]
            name = b if item else val_obj_name(b)
            notes = ["amb.obj.name"] if not item and not name else []
            pre = Pre({"bytes": text(name)}, judged, [_ref(t)], notes=notes)
        body["name"] = self.obj(pre, "object.name")
        t = self.tok(state_rule)
        if t is None:
            pre = self.missing()
        else:
            live = (val_item_state if item else val_obj_state)(line[t.start])
            judged = [(f, effect_obj_state(f)) for f in self.on((state_rule,), t)]
            pre = Pre({"flag": live} if live is not None else None, judged, [_ref(t)])
        body["live"] = self.obj(pre, "object.live")
        return body

    def _after_timestamp(self, pre, wpre, tpre=None):
        """10-values section 2.3 and 11-values-object section 4: a syntax
        finding on the timestamp concerns every value from a later token. If
        the six digits are in place and only the seventh byte is wrong, the
        effect is computable; if not, it is none. Only the messaging flag of
        the position body comes from a token before the timestamp."""
        ts = next((t for t in self.info if t.rule in TIME_RULES and t.depth == self.info_depth), None)
        digits = ts is not None and ts.end - ts.start == 7 and self.line[ts.start : ts.start + 6].isdigit()
        broken = [
            (f, COMPUTABLE if digits and f.offset == ts.start + 6 else NONE)
            for f in self.findings
            if f.kind == "syntax"
            and f.rule in ("time.dhm", "time.hms", "pos.time", "obj.time")
            and self.info_start <= f.offset <= self.info_end
        ]
        if not broken or self.format not in REPORT_FORMATS + OBJ_TIME_FORMATS:
            return
        targets = list(wpre.values()) if wpre is not None else []
        for p in (tpre or {}).values():
            targets += p if isinstance(p, list) else [p]
        for name, p in (pre or {}).items():
            if name == "messaging":
                continue
            if name == "altitude":
                targets += [a.pre for a in p]
            elif name == "extensions":
                targets += [v for _, _, values in p for v in values.values()]
            else:
                targets.append(p)
        for t in targets:
            t.judged.extend(broken)

    # --- Telemetry bodies (04-telemetry sections 3 and 4) -----------------

    def _lists(self, pre, use, order):
        """A body from its values before the mode; a list field gives one
        value object for each item."""
        body = {}
        for name in order:
            if name not in pre:
                continue
            p, path = pre[name], f"{use}.{name}"
            body[name] = [self.obj(x, path) for x in p] if isinstance(p, list) else self.obj(p, path)
        return body

    def _flags(self, t, rule, notes=()):
        """A field of eight bits from the token t of rule, or a missing one."""
        if t is None:
            fs = self._in_info(rule, "syntax")
            return Pre(None, [(f, NONE) for f in fs] or [(f, NONE) for f in self.stop()])
        judged = [(f, NONE if f.kind == "syntax" else KEPT) for f in self.on((rule,), t)]
        flags = val_tlm_bits(self.line[t.start : t.end])
        return Pre({"flags": flags} if flags is not None else None, judged, [_ref(t)], notes=notes)

    def _telemetry(self):
        """The telemetry body of a telemetry report, before the mode."""
        line, depth = self.line, self.info_depth
        w = {}
        t = self.tok("tlm.seq")
        if t is None:
            fs = self._in_info("tlm.seq", "syntax")
            w["sequence"] = Pre(None, [(f, NONE) for f in fs] or [(f, NONE) for f in self.stop()])
        else:
            b = line[t.start : t.end]
            judged = [(f, effect_tlm_seq(f, b)) for f in self.on(("tlm.seq",), t)]
            v = val_tlm_seq(b)
            payload = {"code": v} if isinstance(v, int) else None
            w["sequence"] = Pre(payload, judged, [_ref(t)], reasons=[MIC] if v == MIC else [])
        analog = []
        for t in [t for t in self.toks("tlm.analog") if t.depth == depth][:5]:
            b = line[t.start : t.end]
            # A finding at the end of a token that has its ',' is on the
            # next field (13-values-telemetry section 6).
            closed = b.endswith(b",")
            fs = [f for f in self.on(("tlm.analog",), t) if f.offset < t.end or not closed]
            judged = [(f, effect_tlm_analog(f)) for f in fs]
            analog.append(Pre(val_tlm_number(tlm_field(b)), judged, [_ref(t)]))
        w["analog"] = analog + [self.missing() for _ in range(5 - len(analog))]
        w["digital"] = self._flags(self.tok("tlm.digital"), "tlm.digital", ["amb.val.tlmbits"])
        c = self._comment_token()
        if c is not None:
            self.read.add(c)
            w["comment"] = Pre({"bytes": text(line[c.start : c.end])}, (), [_ref(c)])
        return w

    def _telemetry_b91(self):
        """The telemetry body of a base-91 block, before the mode."""
        line = self.line
        block = self.tok("tlm.b91")
        doubt = [(f, COMPUTABLE) for f in self.on(("tlm.b91",), block) if f.kind == "ambiguous"]
        w = {}
        t = self.tok("tlm.b91.seq")
        if t is not None:
            w["sequence"] = Pre({"code": b91(line[t.start : t.end])}, list(doubt), [_ref(t)])
        w["analog"] = [Pre(Q("raw", b91(line[t.start : t.end])), list(doubt), [_ref(t)]) for t in self.toks("tlm.b91.analog")]
        t = self.tok("tlm.b91.bits")
        if t is not None:
            w["digital"] = Pre({"flags": val_b91_bits(line[t.start : t.end])}, list(doubt), [_ref(t)])
        return w

    def _definition(self):
        """The telemetry definition body, before the mode."""
        line = self.line
        # msg.sep: the text still starts at its fixed place.
        sep = [(f, COMPUTABLE) for f in self._in_info("msg.sep", "syntax")]
        w = {"station": self._addressee(sep)}
        # No value rule of this body reads the message number.
        self.unread.update(t for r in MSG_ID_RULES for t in self.toks(r))
        lst = next((t for r in TLM_LISTS for t in self.toks(r)), None)
        if lst is not None:
            kind, field, item, most = TLM_LISTS[lst.rule]
            w["kind"] = Pre({"code": kind}, list(sep), [_ref(lst)])
            w[field] = self._list_items(lst, item, most, kind == "eqns", sep)
            return w
        bits = self.tok("tlm.bits")
        if bits is None:
            return w
        w["kind"] = Pre({"code": "bits"}, list(sep), [_ref(bits)])
        w["sense"] = self._flags(self.tok("tlm.bits.sense"), "tlm.bits.sense")
        w["sense"].judged += sep
        t = self.tok("tlm.bits.title")
        if t is not None:
            judged = [(f, effect_tlm_text(f)) for f in self.on(("tlm.bits.title",), t)] + sep
            w["title"] = Pre({"bytes": text(line[t.start : t.end])}, judged, [_ref(t)])
        return w

    def _list_items(self, lst, item, most, numbers, sep):
        """The fields of a PARM., UNIT. or EQNS. list: the bytes between its
        commas, up to `most` fields (13-values-telemetry section 5)."""
        line = self.line
        start = lst.start + 5
        toks = {t.start: t for t in self.toks(item)}
        fs = [f for f in self.findings if f.rule == item and lst.start <= f.offset <= lst.end]
        out = []
        a, k = start, 0
        while start < lst.end:
            body = a + (k > 0)
            c = line.find(b",", body, lst.end)
            b = lst.end if c < 0 else c
            # An empty A1 has no token; the token at its place is that of A2.
            t = toks.get(a) if k > 0 or b > a else None
            if k >= most:
                # An extra field: no value rule reads it.
                if t is not None:
                    self.unread.add(t)
            else:
                # A finding of a field is inside its bytes. For an empty
                # field it is at its place, and it is not the syntax finding
                # of an extra field, which is at a ','.
                mine = [f for f in fs if body <= f.offset < b or body == b == f.offset and f.kind != "syntax"]
                frm = [_ref(t if t is not None else lst)]
                if numbers:
                    judged = [(f, effect_tlm_coef(f)) for f in mine] + sep
                    out.append(Pre(val_tlm_number(line[body:b]), judged, frm))
                else:
                    # A value finding on an empty field is the empty A1.
                    judged = [(f, effect_tlm_text(f, b > body)) for f in mine] + sep
                    out.append(Pre({"bytes": text(line[body:b])}, judged, frm))
            if c < 0:
                break
            a, k = c, k + 1
        return out

    def _addressee(self, sep):
        """val.msg.addr and val.tlm.def.station: the name of the addressee."""
        t = self.tok("msg.addr.name")
        addr = self.tok("msg.addr")
        fs = [
            f
            for f in self.findings
            if f.rule in ("msg.addr", "msg.addr.name") and addr is not None and addr.start <= f.offset <= addr.end
        ]
        judged = [(f, effect_tlm_station(f)) for f in fs] + sep
        if t is None:
            return Pre(None, judged or [(f, NONE) for f in self.stop()])
        return Pre({"bytes": text(self.line[t.start : t.end])}, judged, [_ref(t)])

    # --- Message and bulletin bodies (06-message sections 3 and 4) ---------

    def _text(self, w, rule, sep):
        """The text of a message or a bulletin, and its no-archive flag."""
        t = self.tok(rule)
        if t is not None:
            self.read.add(t)
            w["text"] = Pre({"bytes": text(self.line[t.start : t.end])}, list(sep), [_ref(t)])
        t = self.tok("cmt.noarchive")
        if t is not None:
            w["noarchive"] = Pre({"flag": True}, list(sep), [_ref(t)])

    def _number(self, rule, sep, extra=(), a=0, cut=False):
        """A number from the token of rule, from its byte a; cut stops it
        before a '}'. None if the packet has no such token."""
        t = self.tok(rule)
        if t is None:
            return None
        b = self.line[t.start + a : t.end]
        if cut:
            b = b.split(b"}")[0]
        judged = [(f, effect_msg_number(f)) for f in self.on((rule,), t)] + list(extra) + sep
        return Pre({"bytes": text(b)}, judged, [_ref(t)])

    def _message(self):
        """The message body, before the mode."""
        sep = [(f, COMPUTABLE) for f in self._in_info("msg.sep", "syntax")]
        w = {"addressee": self._addressee(sep)}
        kw = self.tok("msg.ack.kw") or self.tok("msg.rej.kw")
        if kw is not None:
            w["kind"] = Pre({"code": kw.rule[4:7]}, list(sep), [_ref(kw)])
            num = self._number("msg.ack.num", sep, cut=True)
            w["id"] = num if num is not None else self.missing()
            return w
        w["kind"] = Pre({"code": "message"}, list(sep), [[self.format, self.info_start, self.info_start + 1]])
        # Without the separator, the start of the text is not certain.
        sep = [(f, NONE) for f, _ in sep]
        self._text(w, "msg.text", sep)
        if self.tok("msg.id.open") is None:
            return w
        close = self.tok("msg.id.close")
        # A number longer than 5 bytes: the finding is on the reply-ack
        # field that holds its sixth byte.
        long_ = [
            (f, COMPUTABLE)
            for f in self.findings
            if f.kind == "value"
            and f.rule in ("msg.id.mm", "msg.id.close", "msg.id.aa")
            and self.info_start <= f.offset <= self.info_end
        ]
        num = self._number("msg.id.mm" if close is not None else "msg.id", sep, long_)
        if num is None:
            fs = [f for r in ("msg.id", "msg.id.mm") for f in self._in_info(r, "syntax")]
            num = Pre(None, [(f, NONE) for f in fs] or [(f, NONE) for f in self.stop()])
        w["id"] = num
        if close is not None:
            w["reply_ack"] = Pre({"flag": True}, list(sep), [_ref(close)])
            aa = self._number("msg.id.aa", sep, long_)
            if aa is not None:
                w["ack_id"] = aa
        return w

    def _bulletin(self):
        """The bulletin body, before the mode."""
        sep = [(f, COMPUTABLE) for f in self._in_info("msg.sep", "syntax")]
        nws = self.format == "nws.dti"
        bad = [(f, NONE) for r in ("bln.addr", "nws.addr") for f in self._in_info(r, "syntax")]
        gone = Pre(None, bad or [(f, NONE) for f in self.stop()])
        w = {}
        if nws:
            w["kind"] = Pre({"code": "nws"}, list(sep), [[self.format, self.info_start, self.info_start + 1]])
            level = self._number("nws.level", sep)
            if level is not None:
                # The list of severity words is open: unstated is kept.
                level.judged = [(f, e if isinstance(f, str) or f.kind != "unstated" else KEPT) for f, e in level.judged]
            w["level"] = level if level is not None else gone
        else:
            t = self.tok("bln.num") or self.tok("bln.ann")
            if t is None:
                w["kind"] = w["id"] = gone
            else:
                kind = "bulletin" if t.rule == "bln.num" else "announcement"
                w["kind"] = Pre({"code": kind}, list(sep), [_ref(t)])
                w["id"] = Pre({"bytes": text(self.line[t.start : t.end])}, list(sep), [_ref(t)])
            group = self._number("bln.group", sep)
            if group is not None:
                w["group"] = group
        sep = [(f, NONE) for f, _ in sep]
        self._text(w, "nws.text" if nws else "bln.text", sep)
        ref = self._number("nws.ref", sep, a=1)
        if ref is not None:
            w["reference"] = ref
        return w

    # --- Capabilities body (08-capabilities section 3) ---------------------

    def _capabilities(self):
        """The capabilities body, before the mode: one item for each
        cap.item token."""
        line = self.line
        items = []
        for it in self.toks("cap.item"):
            inside = [t for t in self.info if t.depth == it.depth + 1 and it.start <= t.start and t.end <= it.end]
            name = next((t for t in inside if t.rule == "cap.token"), None)
            value = next((t for t in inside if t.rule == "cap.value"), None)
            judged = []
            for f in self.on(("cap.item", "cap.token", "cap.value"), it):
                # A count with a byte that is not a digit is still a byte string.
                judged.append((f, KEPT if f.rule == "cap.value" and value is not None else NONE))
            if name is None:
                items.append(Pre(None, judged or [(f, NONE) for f in self.stop()], [_ref(it)]))
                continue
            frm = [_ref(name)] + ([_ref(value)] if value is not None else [])
            extra = {"value": text(line[value.start : value.end])} if value is not None else None
            notes = ("amb.cap.form",) if any(t.rule == "cap.pad" for t in inside) else ()
            if any(e == NONE for _, e in judged):
                frm = [_ref(it)]
            items.append(Pre({"bytes": text(line[name.start : name.end])}, judged, frm, notes=notes, extra=extra))
        return {"items": items}

    # --- Frequency body (07-frequency section 3) ---------------------------

    def _frequency(self):
        """The frequency body, before the mode. It is empty if the text has
        no frequency specification."""
        line = self.line

        def item(t):
            # The token of an item includes its leading SP, if it has one.
            b = line[t.start : t.end]
            return b[1:] if b[:1] == b" " else b

        w = {}
        f = self.tok("freq.mhz") or self.tok("freq.uw") or self.tok("freq.ghz")
        if f is not None:
            # A receiver ignores the case of MHz: its syntax finding is kept.
            w["frequency"] = Pre(val_freq(f.rule, line[f.start : f.end]), (), [_ref(f)])
        nofreq = () if f is not None else ("amb.freq.nofreq",)
        t = self.tok("freq.rx")
        if t is not None:
            w["rx_frequency"] = Pre(val_freq_rx(item(t)), (), [_ref(t)])
        t = self.tok("freq.tone")
        if t is not None:
            kind, tone, dcs, narrow, row = val_freq_tone(item(t))
            w["tone_kind"] = Pre({"code": kind}, (), [_ref(t)], notes=nofreq)
            if tone is not None:
                doubt = [(row, COMPUTABLE)] if row else ()
                w["tone"] = Pre(tone, doubt, [_ref(t)], notes=() if kind == "burst" else ("amb.val.tone",))
            if dcs is not None:
                w["dcs"] = Pre({"bytes": text(dcs)}, (), [_ref(t)])
            if narrow:
                w["narrow"] = Pre({"flag": True}, (), [_ref(t)])
        t = self.tok("freq.offset")
        if t is not None:
            judged = [(x, COMPUTABLE) for x in self.on(("freq.offset",), t) if x.kind == "value"]
            w["offset"] = Pre(val_freq_offset(item(t)), judged, [_ref(t)], notes=nofreq)
        for t in self.toks("freq.range"):
            direction, q = val_freq_range(item(t))
            w.setdefault("range", []).append(Pre(q, (), [_ref(t)], notes=nofreq, extra={"dir": direction}))
        t = self.tok("freq.dstar")
        if t is not None:
            w["dstar"] = Pre({"flag": True}, (), [_ref(t)])
            rpt = val_freq_dstar(line[t.start : t.end])
            if rpt is not None:
                w["dstar_repeater"] = Pre({"bytes": text(rpt[0])}, (), [_ref(t)])
                w["dstar_module"] = Pre({"bytes": text(rpt[1])}, (), [_ref(t)])
        return w

    # --- Status body (05-status section 3) --------------------------------

    def _status(self):
        """The status body, before the mode."""
        line = self.line
        w = {}
        g = self.tok("grid.loc") if self.tok("stat.grid") is not None else None
        if g is not None:
            # A receiver can get the letters in lower case (p. 105/81): the
            # syntax finding of grid.loc is kept.
            w["locator"] = Pre({"bytes": text(line[g.start : g.end])}, (), [_ref(g)], notes=["amb.stat.grid"])
            w["symbol"] = self._symbol("sym.table", "sym.code")
        t = self.tok("stat.text")
        if t is not None:
            # After a locator, the SP that starts the text is a separator.
            s = t.start + (g is not None and line[t.start] == 0x20)
            self.read.add(t)
            w["text"] = Pre({"bytes": text(line[s : t.end])}, (), [_ref(t)])
        t = self.tok("stat.beam")
        if t is not None:
            heading, power = val_stat_beam(line[t.start : t.end])
            w["beam_heading"] = Pre(heading, (), [_ref(t)])
            w["beam_power"] = Pre(power, (), [_ref(t)])
        t = self.tok("cmt.noarchive")
        if t is not None:
            w["noarchive"] = Pre({"flag": True}, (), [_ref(t)])
        return w

    # --- Weather body (03-weather section 3) ------------------------------

    def _item_weather(self):
        """03-weather section 2: an Item whose symbol code is '_' and that
        has at least one byte after its position."""
        block = self.tok("cmp.block")
        sc = self.tok("cmp.code") if block is not None else self.tok("sym.code")
        if sc is None or self.line[sc.start] != 0x5F:
            return False
        return (block.end if block is not None else sc.end) < self.info_end

    def _in_info(self, rule, kind):
        return [f for f in self.findings if f.rule == rule and f.kind == kind and self.info_start <= f.offset <= self.info_end]

    def _weather(self, has_position):
        """The fields of the weather body before the mode applies."""
        line, depth = self.line, self.info_depth
        w = {}
        wind = self.tok("ext.dirspd")
        if wind is not None:
            b = line[wind.start : wind.end]
            fs = self.on(("ext.dirspd",), wind)
            frm = [_ref(wind)]
            calm = b == b"000/000"
            for name, speed, v in zip(("wind_direction", "wind_speed"), (False, True), val_wx_wind(b)):
                judged = [(f, effect_wind(f, wind.start, speed)) for f in fs]
                if calm and speed:
                    judged.append((CALM, COMPUTABLE))
                if isinstance(v, Q):
                    w[name] = Pre(v, judged, list(frm), notes=["err.wx.wind-units"] if speed else [])
                else:
                    w[name] = Pre(None, judged, list(frm), reasons=[v] if v else [])
        elif self.cmp_wind is not None:
            w["wind_direction"], w["wind_speed"] = self.cmp_wind
        elif self.format != "wx.pl" and self.tok("cmp.block") is None:
            # 06 section 5.1: the wind field of an uncompressed report is
            # missing.
            for name in ("wind_direction", "wind_speed"):
                fs = self._in_info("ext.dirspd", "syntax")
                w[name] = Pre(None, [(f, NONE) for f in fs] or [(f, NONE) for f in self.stop()])
        from_wind = wind is not None or self.cmp_wind is not None
        # 01-record section 3.1, repair.humidity-width: the repaired token
        # and each token after it have the mark of the repair.
        hum3 = [(rid, start) for rid, start, _ in self.scan.repaired if rid == "repair.humidity-width"]

        def repaired(t):
            return [(rid, COMPUTABLE) for rid, start in hum3 if t.start >= start]

        for name, rules in WX_FIELDS:
            toks = sorted((t for r in rules for t in self.toks(r) if t.depth == depth), key=lambda t: t.start)
            judged = [(f, effect_wx(f, t.rule)) for t in toks for f in self.on((t.rule,), t)]
            judged += [j for t in toks for j in repaired(t)]
            if name in w and from_wind:
                # 12-values-weather section 2.2: the wind field is the first
                # token; a later field is a repeated token.
                w[name].judged += judged
                w[name].frm += [_ref(t) for t in toks]
                continue
            if not toks:
                if self.format == "wx.pl" and rules[0] in WX_LEADING:
                    fs = self._in_info(rules[0], "syntax")
                    w[name] = Pre(None, [(f, NONE) for f in fs] or [(f, NONE) for f in self.stop()])
                continue
            first = toks[0]
            v = val_wx(first.rule, line[first.start + 1 : first.end])
            frm = [_ref(t) for t in toks]
            if isinstance(v, Q):
                notes = [WX_NOTES[name]] if name in WX_NOTES else []
                if name == "wind_direction" and v.n == 0:
                    notes.append(WDIR0)
                # val.wx.hum: only a repaired token of three digits gives a
                # number outside 1 to 100 (10-values section 2.4).
                w[name] = Pre(v, judged, frm, notes=notes, in_range=first.rule != "wx.hum" or 1 <= v.n <= 100)
            else:
                w[name] = Pre(None, judged, frm, reasons=[v] if v else [])
        t = self.tok("wx.sw")
        if t is not None:
            judged = [(f, effect_wx(f, "wx.sw")) for f in self.on(("wx.sw",), t)] + repaired(t)
            w["software"] = Pre({"code": text(line[t.start : t.end])}, judged, [_ref(t)], notes=["amb.wx.tail"])
        t = self.tok("wx.unit")
        if t is not None:
            w["unit"] = Pre({"bytes": text(line[t.start : t.end])}, repaired(t), [_ref(t)], notes=["amb.wx.tail"])
        if not has_position:
            # No position body: the comment is here, and no value rule reads
            # the altitude or the no-archive marker in it.
            c = self._comment_token()
            if c is not None:
                self.read.add(c)
                w["comment"] = Pre({"bytes": text(line[c.start : c.end])}, (), [_ref(c)])
            self.unread.update(t for r in ALT_RULES + ("cmt.noarchive",) for t in self.toks(r))
        return w

    def _body(self, pre):
        """Apply the DAO, then build the fields in the order of section 7."""
        body = {}
        for name in ("lat", "lon", "ambiguity", "datum"):
            if name in pre:
                body[name] = self.obj(pre[name], "position." + name)
        alts = []
        for p in pre.get("altitude", []):
            o = self.obj(p.pre, "position.altitude")
            if "why" not in o:
                o["ref"] = p.ref
                o["from"] = o.pop("from")
                if "mark" in o:
                    o["mark"] = o.pop("mark")
            alts.append(o)
        if len([o for o in alts if "why" not in o]) > 1:
            self.note("amb.val.altitudes", "position.altitude")
        if alts:
            body["altitude"] = alts
        for name in ("course", "speed", "symbol", "messaging", "fix", "comment"):
            if name in pre:
                body[name] = self.obj(pre[name], "position." + name)
        items = []
        for i, (rule, frm, values) in enumerate(sorted(pre.get("extensions", []), key=lambda x: x[1][0][1] if x[1] else -1)):
            vals = {}
            for name, p in values.items():
                vals[name] = self.obj(p, f"position.extensions[{i}].values.{name}", inner=True)
            items.append({"rule": rule, "from": frm, "values": vals})
        body["extensions"] = items
        return body

    # --- Uncompressed position (10-values sections 4, 5) -----------------

    def _uncompressed(self):
        line = self.line
        pre = {}
        lat_t, lon_t = self.tok("lat"), self.tok("lon")
        lat_b = line[lat_t.start : lat_t.end]
        lat_ok = len(lat_b) == 8
        lat_level_f = self.on(("lat", "lat.amb"), lat_t)
        level = val_lat_amb(lat_b) if lat_ok else 0

        if lat_ok:
            q = val_lat(lat_b, level)
            judged = [(f, effect_coord(f, lat_b, 2, 90)) for f in lat_level_f]
            pre["lat"] = Pre(q, judged, [_ref(lat_t)], in_range=abs(q.n) <= 540000)
            pre["ambiguity"] = Pre({"code": level}, [(f, effect_lat_level(f)) for f in lat_level_f], [_ref(lat_t)])
        else:
            pre["lat"] = Pre(None, [(f, NONE) for f in lat_level_f] or [(f, NONE) for f in self.stop()], [_ref(lat_t)])
            pre["ambiguity"] = Pre(None, pre["lat"].judged, [_ref(lat_t)])

        if lon_t is not None and lat_ok and lon_t.end - lon_t.start == 9:
            lon_b = line[lon_t.start : lon_t.end]
            q = val_lon(lon_b, level)
            judged = [(f, effect_coord(f, lon_b, 3, 180)) for f in self.on(("lon", "lon.amb"), lon_t)]
            judged += [(f, effect_lat_level(f)) for f in lat_level_f if f.rule == "lat.amb"]
            pre["lon"] = Pre(q, judged, [_ref(lon_t), _ref(lat_t)], in_range=abs(q.n) <= 1080000)
        else:
            frm = [_ref(lon_t)] if lon_t is not None else []
            judged = [(f, NONE) for f in self.on(("lon",), lon_t)] if lon_t is not None else []
            pre["lon"] = Pre(None, judged or [(f, NONE) for f in self.stop()], frm + [_ref(lat_t)])

        for name in ("lat", "lon"):
            p = pre[name]
            if p.payload is not None and p.payload.w > 1:
                p.notes.append("amb.val.ambiguity")
            if any(f.rule in ("lat", "lon") and f.kind == "value" and e == COMPUTABLE for f, e in p.judged):
                p.notes.append("amb.val.minutes")
        if pre["lat"].payload is not None and pre["lon"].payload is not None and pre["lat"].payload.n == pre["lon"].payload.n == 0:
            # The null position (10-values section 4).
            pre["lat"].notes.append("amb.lat.null")
            pre["lon"].notes.append("amb.lat.null")

        pre["symbol"] = self._symbol("sym.table", "sym.code")
        self._messaging(pre)
        pre["datum"], dao = self._dao(level, "unc")
        if dao is not None and lat_ok and lon_t is not None and lon_t.end - lon_t.start == 9:
            self._apply_dao(pre, dao, hemisphere(lat_b, 7, 0x53), hemisphere(line[lon_t.start : lon_t.end], 8, 0x57))

        # The slot: ext.csespd right after the symbol code gives course and speed.
        sc = self.tok("sym.code")
        slot = next(
            (t for t in self.toks("ext.csespd") if sc is not None and t.start == sc.end and t.depth == self.info_depth), None
        )
        pre["extensions"] = []
        if slot is not None:
            pre["course"], pre["speed"] = self._csespd(slot)
        self._ext_items(pre, skip=slot)
        return pre

    def _symbol(self, table_rule, code_rule):
        line = self.line
        st, sc = self.tok(table_rule), self.tok(code_rule)
        frm = [_ref(t) for t in (st, sc) if t is not None]
        if st is None or sc is None:
            return self.missing(frm)
        table, code = line[st.start], line[sc.start]
        # 01-record section 3.1, repair.overlay-lowercase: 'a'-'j' outside
        # the compressed format gives the overlay digit. The tokens do not
        # change; the syntax finding of the table byte has no effect.
        repair = not self.strict and table_rule != "cmp.table" and 0x61 <= table <= 0x6A
        judged = [(f, effect_sym(f)) for f in self.on((code_rule,), sc)]
        if repair:
            judged.append(("repair.overlay-lowercase", COMPUTABLE))
        else:
            judged += [(f, effect_sym(f)) for f in self.on((table_rule,), st)]
        classic, _ = val_sym(table, code, table_rule == "cmp.table" or repair)
        if classic is None or not 0x21 <= code <= 0x7E:
            return Pre(None, judged, frm)
        return Pre({"chars": text(bytes((table, code))), "classic": classic}, judged, frm)

    # --- Compressed position (10-values section 6) -----------------------

    def _compressed(self):
        line = self.line
        pre = {"extensions": []}
        for name, rule, fn in (("lat", "cmp.lat", val_cmp_lat), ("lon", "cmp.lon", val_cmp_lon)):
            t = self.tok(rule)
            if t is None or t.end - t.start < 4:
                frm = [_ref(t)] if t is not None else []
                judged = [(f, NONE) for f in self.on((rule,), t)] if t is not None else []
                pre[name] = Pre(None, judged or [(f, NONE) for f in self.stop()], frm)
            else:
                judged = [(f, effect_cmp(f)) for f in self.on((rule,), t)]
                pre[name] = Pre(fn(line[t.start : t.end]), judged, [_ref(t)])
        pre["symbol"] = self._symbol("cmp.table", "cmp.code")
        self._messaging(pre)

        cs_rules = ("cmp.cs.crs", "cmp.cs.wind", "cmp.cs.rng", "cmp.cs.alt", "cmp.cs", "cmp.cs.none")
        cs = next((t for r in cs_rules for t in self.toks(r)), None)
        tt = self.tok("cmp.t")
        if cs is None or cs.rule != "cmp.cs.none":
            t_judged = [(f, effect_cmp_t(f, True)) for f in self.on(("cmp.t",), tt)] if tt is not None else []
            cs_t_judged = [(f, effect_cmp_t(f, False)) for f in self.on(("cmp.t",), tt)] if tt is not None else []
            if tt is None:
                cs_t_judged = [(f, NONE) for f in self.stop()]
            if tt is not None:
                fix, source, origin = val_cmp_t(line[tt.start : tt.end])
                frm = [_ref(tt)]
                pre["fix"] = Pre({"code": fix}, t_judged, frm)
                pre["extensions"].append(
                    ("val.cmp.t", frm, {"source": Pre({"code": source}, t_judged), "origin": Pre({"code": origin}, t_judged)})
                )
            else:
                pre["fix"] = self.missing()
        elif tt is not None:
            # c = SP: T has no meaning and no value rule reads it (10-values
            # section 6; 01-record section 5).
            self.unread.add(tt)
        if cs is None:
            self._course_speed(pre, self.missing(), self.missing())
        elif cs.rule != "cmp.cs.none":
            b = line[cs.start : cs.end]
            judged = [(f, effect_cmp(f)) for f in self.on((cs.rule,), cs)] + cs_t_judged
            frm = [_ref(cs)]
            if cs.rule == "cmp.cs.crs":
                crs = val_cmp_crs(b)
                pre["course"] = Pre(crs, judged, frm, notes=["amb.val.course0"] if crs.n == 0 else [])
                pre["speed"] = Pre(val_cmp_spd(b), judged, frm)
            elif cs.rule == "cmp.cs.wind":
                # val.cmp.wind: the arithmetic of val.cmp.crs and val.cmp.spd.
                crs = val_cmp_crs(b)
                self.cmp_wind = (
                    Pre(crs, judged, frm, notes=[WDIR0] if crs.n == 0 else []),
                    Pre(val_cmp_spd(b), list(judged), list(frm), notes=["err.wx.wind-units"]),
                )
            elif cs.rule == "cmp.cs.rng":
                pre["extensions"].append(("val.cmp.rng", frm, {"range": Pre(val_cmp_rng(b), judged)}))
            elif cs.rule == "cmp.cs.alt":
                pre.setdefault("altitude", []).append(
                    _Alt(cs.start, Pre(val_cmp_alt(b), judged, frm, notes=["amb.val.altref"]), "unstated")
                )
            else:
                # The kind of cs is unknown (syntax): course and speed have no value.
                self._course_speed(pre, Pre(None, judged, frm), Pre(None, list(judged), list(frm)))
        pre["datum"], dao = self._dao(None, "cmp")
        if dao is not None:
            self._apply_dao(pre, dao, 1, 1)
        self._ext_items(pre)
        return pre

    def _course_speed(self, pre, a, b):
        """Course and speed with no value: in a weather report they are the
        wind (03-weather section 3)."""
        if self.weather:
            self.cmp_wind = (a, b)
        else:
            pre["course"], pre["speed"] = a, b

    # --- Mic-E (10-values section 7) -------------------------------------

    def _mice(self):
        line = self.line
        pre = {"extensions": []}
        hs, he = self.header
        dest_t = next((t for t in self.scan.tokens if t.rule == "dest.mice" and hs <= t.start < he), None)
        dest = line[dest_t.start : dest_t.end] if dest_t is not None else b""
        dest_f = self.on(_DEST_RULES, dest_t) if dest_t is not None else []
        dest_ok = len(dest) >= 6
        dref = [_ref(dest_t)] if dest_t is not None else []
        level = 0
        if dest_ok:
            q, level = val_mice_lat(dest)
            judged = [(f, effect_mice_dest(f, dest, "lat")) for f in dest_f]
            pre["lat"] = Pre(q, judged, dref, in_range=abs(q.n) <= 540000)
            # The level is a value of val.mice.lat and takes its effect.
            pre["ambiguity"] = Pre({"code": level}, judged, dref)
        else:
            judged = [(f, NONE) for f in dest_f] or [(f, NONE) for f in self.stop()]
            pre["lat"] = Pre(None, judged, dref)
            pre["ambiguity"] = Pre(None, judged, dref)

        deg, mins, hun = self.tok("mice.lon.deg"), self.tok("mice.lon.min"), self.tok("mice.lon.hun")
        lon_toks = [t for t in (deg, mins, hun) if t is not None]
        lon_f = [(f, effect_mice_lon(f)) for t in lon_toks for f in self.on((t.rule,), t)]
        # 10-values 2.3: val.mice.lon uses bytes 5 and 6 of the destination,
        # and bytes 1 to 4 only through the level; there only the blank-order
        # syntax on mice.dest concerns it.
        lon_dest_f = [
            f
            for f in dest_f
            if f.rule in _LON_DEST_RULES and f.offset >= dest_t.start + 4 or f.rule == "mice.dest" and f.kind == "syntax"
        ]
        lon_f += [(f, effect_mice_dest(f, dest, "lon")) for f in lon_dest_f]
        lon_frm = [_ref(t) for t in lon_toks] + dref
        if dest_ok and len(lon_toks) == 3:
            q = val_mice_lon(line[deg.start], line[mins.start], line[hun.start], dest, level)
            pre["lon"] = Pre(q, lon_f, lon_frm, in_range=abs(q.n) <= 1080000)
        else:
            pre["lon"] = Pre(None, lon_f + ([] if len(lon_toks) == 3 else [(f, NONE) for f in self.stop()]), lon_frm)
        for name in ("lat", "lon"):
            p = pre[name]
            if p.payload is not None and p.payload.w > 1:
                p.notes.append("amb.val.ambiguity")
        if any(f.kind == "value" and e == COMPUTABLE for f, e in pre["lat"].judged):
            pre["lat"].notes.append("amb.val.minutes")

        sp, dc, se = self.tok("mice.sp"), self.tok("mice.dc"), self.tok("mice.se")
        if sp is not None and dc is not None:
            b_dc = line[dc.start]
            judged = [(f, effect_mice_dc(f, b_dc, False)) for t in (sp, dc) for f in self.on((t.rule,), t)]
            pre["speed"] = Pre(val_mice_spd(line[sp.start], b_dc), judged, [_ref(sp), _ref(dc)])
        else:
            pre["speed"] = self.missing([_ref(t) for t in (sp, dc) if t is not None])
        if dc is not None and se is not None:
            b_dc = line[dc.start]
            judged = [(f, effect_mice_dc(f, b_dc, True)) for t in (dc, se) for f in self.on((t.rule,), t)]
            crs = val_mice_crs(b_dc, line[se.start])
            pre["course"] = Pre(crs, judged, [_ref(dc), _ref(se)], reasons=[] if crs else [UNKNOWN])
        else:
            pre["course"] = self.missing([_ref(t) for t in (dc, se) if t is not None])

        pre["symbol"] = self._symbol("mice.sym.table", "mice.sym.code")
        dti_t = self.tok(self.format)
        fix = val_mice_dti(line[self.info_start])
        pre["fix"] = Pre({"code": fix} if fix else None, (), [_ref(dti_t)], reasons=[] if fix else ["amb.val.micefix"])
        prefix = self.tok("mice.type.prefix")
        if prefix is not None:
            cap = val_mice_msgcap(line[prefix.start])
            pre["messaging"] = Pre(
                {"flag": cap} if cap is not None else None,
                (),
                [_ref(prefix)],
                reasons=[] if cap is not None else ["val.mice.msgcap"],
            )

        for t in self.toks("mice.alt"):
            b = line[t.start : t.end]
            judged = [(f, effect_mice_alt(f)) for f in self.on(("mice.alt",), t)]
            pre.setdefault("altitude", []).append(_Alt(t.start, Pre(val_mice_alt(b), judged, [_ref(t)]), "msl"))

        if dest_ok:
            abc = [t for t in self.scan.tokens if t.rule in _DEST_CHILDREN[:3] and dest_t.start <= t.start < dest_t.end]
            judged = [(f, effect_mice_dest(f, dest, "msg")) for t in abc for f in self.on(_DEST_RULES, t)]
            msg = val_mice_msg(dest)
            frm = [_ref(t) for t in abc]
            if msg is None:
                values = {"kind": Pre(None, judged), "index": Pre(None, judged)}
            else:
                values = {"kind": Pre({"code": msg[0]}, judged)}
                if msg[1] is not None:
                    values["index"] = Pre({"code": msg[1]}, judged)
            pre["extensions"].append(("val.mice.msg", frm, values))

        pre["datum"], dao = self._dao(level if dest_ok else None, "mice")
        if dao is not None and dest_ok:
            self._apply_dao(pre, dao, mice_lat_sign(dest), mice_lon_sign(dest))
        self._ext_items(pre)
        return pre

    # --- Data extensions (10-values section 8) ---------------------------

    def _csespd(self, t):
        b = self.line[t.start : t.end]
        fs = self.on(("ext.csespd",), t)
        course, speed = val_ext_csespd(b)
        frm = [_ref(t)]
        out = []
        for half, v in ((0, course), (1, speed)):
            judged = [(f, effect_csespd(f, b, half)) for f in fs]
            if isinstance(v, Q):
                ok = 1 <= v.n <= 360 if half == 0 else True
                out.append(Pre(v, judged, frm, in_range=ok))
            else:
                out.append(Pre(None, judged, frm, reasons=[v]))
        return out

    def _hgd(self, height, gain, directivity, judged_dir, judged):
        notes = ["amb.val.phgcodes"] if height.n > 0x3B - 0x30 else []
        if directivity is None:
            d = Pre(None, judged_dir)
        elif isinstance(directivity, Q):
            d = Pre(directivity, judged_dir)
        else:
            d = Pre({"code": directivity}, judged_dir)
        return Pre(height, judged, notes=notes), d

    def _ext_items(self, pre, skip=None):
        """Every data extension of the information field except the slot,
        and the no-archive marker, as items of `extensions`."""
        line = self.line
        items = pre["extensions"]
        for t in (t for r in EXT_RULES for t in self.toks(r)):
            if t is skip:
                continue
            b = line[t.start : t.end]
            fs = self.on((t.rule,), t)
            frm = [_ref(t)]
            if t.rule == "ext.csespd":
                c, s = self._csespd(t)
                items.append(("val.ext.csespd", frm, {"course": c, "speed": s}))
            elif t.rule in ("ext.phg", "ext.phgr"):
                power, height, gain, directivity = val_ext_phg(b)
                judged = [(f, effect_ext_value(f, False)) for f in fs]
                judged_dir = [(f, effect_ext_value(f, True)) for f in fs]
                h, d = self._hgd(height, gain, directivity, judged_dir, judged)
                values = {"power": Pre(power, judged), "height": h, "gain": Pre(gain, judged), "directivity": d}
                items.append(("val.ext.phg", frm, values))
                if t.rule == "ext.phgr":
                    rate = val_ext_phgr(b)
                    notes = ["amb.val.phgcodes"] if b[7] > 0x41 else []
                    items.append(("val.ext.phgr", frm, {"rate": Pre(rate, judged, notes=notes)}))
            elif t.rule == "ext.rng":
                judged = [(f, effect_ext_value(f, False)) for f in fs]
                items.append(("val.ext.rng", frm, {"range": Pre(val_ext_rng(b), judged)}))
            elif t.rule == "ext.dfs":
                strength, height, gain, directivity = val_ext_dfs(b)
                judged = [(f, effect_ext_value(f, False)) for f in fs]
                judged_dir = [(f, effect_ext_value(f, True)) for f in fs]
                h, d = self._hgd(height, gain, directivity, judged_dir, judged)
                values = {
                    "strength": Pre(strength, judged),
                    "height": h,
                    "gain": Pre(gain, judged, notes=["amb.val.dfsgain"]),
                    "directivity": d,
                }
                items.append(("val.ext.dfs", frm, values))
            elif t.rule == "ext.brgnrq":
                items.append(self._brgnrq(t, b, fs))
        for t in self.toks("cmt.noarchive"):
            items.append(("val.cmt.noarchive", [_ref(t)], {"noarchive": Pre({"flag": True})}))

    def _brgnrq(self, t, b, fs):
        line = self.line
        bearing, n, r, q = val_ext_brgnrq(b)
        judged_brg = [(f, effect_ext_value(f, True)) for f in fs]
        judged = [(f, effect_ext_value(f, False)) for f in fs]
        values = {"bearing": Pre(bearing, judged_brg, notes=["amb.val.bearing"])}
        if n is None:
            reason = ["val.ext.brgnrq"]
            values.update(hits=Pre(None, judged, reasons=reason), range=Pre(None, judged, reasons=reason))
            values["quality"] = Pre(None, judged, reasons=reason)
        else:
            values["hits"] = Pre({"code": n}, judged)
            values["range"] = Pre(r, judged)
            values["quality"] = Pre({"code": q}, judged)
        # The station: the DF symbol and an ext.csespd with a course before.
        frm = [_ref(t)]
        cse = next((c for c in self.toks("ext.csespd") if c.end <= t.start), None)
        st, sc = self.tok("sym.table"), self.tok("sym.code")
        if cse is not None:
            frm.append(_ref(cse))
        if st is not None and sc is not None:
            frm += [_ref(st), _ref(sc)]
        station = None
        if st is not None and sc is not None and line[st.start] == 0x2F and line[sc.start] == 0x5C and cse is not None:
            station = df_station(line[cse.start : cse.start + 3])
        values["station"] = Pre({"code": station}, ()) if station else Pre(None, (), reasons=["val.ext.brgnrq"])
        return ("val.ext.brgnrq", frm, values)

    # --- Fields in a comment (10-values section 9) -----------------------

    def _comment_fields(self, pre):
        line = self.line
        for t in (t for r in ALT_RULES for t in self.toks(r)):
            b = line[t.start : t.end]
            overlap = any(
                u.depth == t.depth
                and u is not t
                and u.rule not in ALT_RULES + ("cmt.noarchive",)
                and u.start < t.end
                and t.start < u.end
                for u in self.info
            )
            judged = [(f, effect_cmt_alt(f, overlap)) for f in self.on(ALT_RULES, t)]
            ok = len(b) == 9
            q = (val_cmt_alt(b) if t.rule == "cmt.alt" else val_cmt_alt_neg(b)) if ok else None
            pre.setdefault("altitude", []).append(_Alt(t.start, Pre(q, judged, [_ref(t)], notes=["amb.val.altref"]), "unstated"))
        if "altitude" in pre:
            pre["altitude"].sort(key=lambda a: a.start)
        c = self._comment_token()
        if c is not None:
            self.read.add(c)
            b = self._comment_bytes(c)
            if b:
                pre["comment"] = Pre({"bytes": text(b)}, (), [_ref(c)])

    def _comment_bytes(self, c):
        """The bytes of the comment token c without the tokens of
        COMMENT_OUT that are directly inside it, and without the `/` after
        a data extension (01-record section 7.1)."""
        line = self.line
        spans = sorted(
            (t.start, t.end)
            for t in self.info
            if t.rule in COMMENT_OUT and t.depth == c.depth + 1 and c.start <= t.start and t.end <= c.end
        )
        out = bytearray()
        pos = c.start
        for start, end in spans:
            if start > pos:
                out += line[pos:start]
            pos = max(pos, end)
        out += line[pos : c.end]
        # The `/` after a data extension is a separator, not text.
        after_ext = any(t.rule.startswith("ext.") and t.end == c.start and t.depth == c.depth for t in self.info)
        if after_ext and out[:1] == b"/":
            del out[:1]
        return bytes(out)

    def _comment_token(self):
        """cmt.text of the position comment, or the one inside mice.status."""
        status = self.tok("mice.status")
        for t in self.toks("cmt.text"):
            if t.depth == self.info_depth or status is not None and t.depth == status.depth + 1:
                return t
        return None

    def _dao(self, level, form):
        """(datum, the DAO to apply or None). form is "unc", "cmp" or "mice";
        level is the position ambiguity level (None for compressed)."""
        line = self.line
        daos = self.toks("cmt.dao")
        if not daos:
            return Pre({"code": "default"}, notes=["amb.val.datum"]), None
        if len(daos) > 1:
            judged = [(f, effect_dao(f, True)) for t in daos for f in self.on(("cmt.dao",), t)]
            return Pre(None, judged, [_ref(t) for t in daos]), None
        t = daos[0]
        b = line[t.start : t.end]
        fs = self.on(("cmt.dao",), t)
        datum_judged = [(f, effect_dao(f, True)) for f in fs]
        d = val_dao_datum(b)
        notes = [] if d[0] in NAMED_DATUMS or not (0x41 <= d[0] <= 0x5A or 0x61 <= d[0] <= 0x7A) else ["amb.val.datum"]
        datum = Pre({"code": text(d)}, datum_judged, [_ref(t)], notes=notes)
        coord_judged = [(f, effect_dao(f, False)) for f in fs]
        if any(e != KEPT for _, e in coord_judged) or b[2] == b[3] == 0x20:
            return datum, None
        if form == "cmp" or level:
            # amb.val.daobase: the datum and no added precision.
            return datum, ("daobase", t)
        return datum, ("apply", t)

    def _apply_dao(self, pre, dao, s_lat, s_lon):
        what, t = dao
        b = self.line[t.start : t.end]
        for name, i, s in (("lat", 2, s_lat), ("lon", 3, s_lon)):
            p = pre[name]
            if p.payload is None:
                continue
            if what == "daobase":
                p.notes.append("amb.val.daobase")
                continue
            q = val_dao_coord(b, i, p.payload.n, s)
            if q is None:
                continue
            if isinstance(q, str):
                p.notes.append(q)
                continue
            p.payload = q
            p.frm.append(_ref(t))


class _Alt:
    """An item of `altitude` before the mode applies: its token start (for
    order), its value and its reference surface."""

    __slots__ = ("start", "pre", "ref")

    def __init__(self, start, pre, ref):
        self.start = start
        self.pre = pre
        self.ref = ref


def decode(line, received=None, received_res=None, mode="strict"):
    """The record of one TNC2 line (bytes, no line terminator) as plain data
    for JSON (01-record section 8). received is the received time in
    seconds since the Unix epoch, and received_res its resolution."""
    return Decoder(line, received, received_res, mode).run()
