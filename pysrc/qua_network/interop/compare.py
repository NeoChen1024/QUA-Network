# SPDX-License-Identifier: Apache-2.0
"""Comparison of a record with the result of another parser
(docs/interop/09-comparison.md).

A view is a dictionary from a path to a value. A number of a record is
("n", v, res). Every other value is ("e", value). The views of the other
parsers have the same paths; their numbers are ("n", v).
"""

WX_FIELDS = (
    "wind_direction",
    "wind_speed",
    "gust",
    "temperature",
    "rain_1h",
    "rain_24h",
    "rain_midnight",
    "snow_24h",
    "humidity",
    "pressure",
    "luminosity",
)
OUTCOMES = ("agree", "differ", "ours-only", "theirs-only")
RECORD_CLASSES = ("both", "ours-only", "theirs-only", "neither")


# --- Section 4: the view of a record --------------------------------------


def _num(view, path, o):
    if o is not None and "v" in o:
        view[path] = ("n", o["v"], o["res"])


def _eq(view, path, o, member):
    if o is not None and member in o:
        view[path] = ("e", o[member])


def record_view(rec):
    view = {}
    p = rec.get("position")
    if p is not None:
        for name in ("lat", "lon", "course", "speed"):
            _num(view, "position." + name, p.get(name))
        # The first altitude that has a value.
        _num(view, "position.altitude", next((a for a in p.get("altitude", ()) if "v" in a), None))
        _eq(view, "position.ambiguity", p.get("ambiguity"), "code")
        _eq(view, "position.symbol", p.get("symbol"), "chars")
        _eq(view, "position.messaging", p.get("messaging"), "flag")
        _eq(view, "position.comment", p.get("comment"), "bytes")
    o = rec.get("object")
    if o is not None:
        _eq(view, "object.name", o.get("name"), "bytes")
        _eq(view, "object.live", o.get("live"), "flag")
    w = rec.get("weather")
    if w is not None:
        for name in WX_FIELDS:
            _num(view, "weather." + name, w.get(name))
    m = rec.get("message")
    if m is not None:
        _eq(view, "message.kind", m.get("kind"), "code")
        for name in ("addressee", "text", "id"):
            _eq(view, "message." + name, m.get(name), "bytes")
    b = rec.get("bulletin")
    if b is not None:
        _eq(view, "bulletin.kind", b.get("kind"), "code")
        for name in ("id", "group", "text"):
            _eq(view, "bulletin." + name, b.get(name), "bytes")
    s = rec.get("status")
    if s is not None:
        _eq(view, "status.text", s.get("text"), "bytes")
    t = rec.get("telemetry")
    if t is not None:
        _eq(view, "telemetry.sequence", t.get("sequence"), "code")
        for i, a in enumerate(t.get("analog", ())):
            _num(view, f"telemetry.analog[{i}]", a)
        _eq(view, "telemetry.digital", t.get("digital"), "flags")
    c = rec.get("capabilities")
    if c is not None:
        view["capabilities.items"] = ("e", {i["bytes"]: i.get("value") for i in c["items"] if "bytes" in i})
    return view


# --- Section 5: the views of the other parsers ----------------------------


def _number(x):
    """A number of the other parser, or None if it is not one."""
    if isinstance(x, bool) or x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _put_n(view, path, x, factor=1):
    n = _number(x)
    if n is not None:
        view[path] = ("n", n * factor)


def _put_e(view, path, d, key, conv=None):
    if key in d and d[key] is not None:
        view[path] = ("e", conv(d[key]) if conv else d[key])


def _trim(x):
    """A byte string without the spaces at its start and at its end."""
    return x.strip(" ") if isinstance(x, str) else x


def _bits(s):
    return [c == "1" for c in s]


def _telemetry(view, t):
    if not isinstance(t, dict):
        return
    seq = _number(t.get("seq"))
    if seq is not None:
        view["telemetry.sequence"] = ("e", int(seq))
    for i, x in enumerate(t.get("vals") or ()):
        _put_n(view, f"telemetry.analog[{i}]", x)
    if isinstance(t.get("bits"), str):
        view["telemetry.digital"] = ("e", _bits(t["bits"]))


def pythonlib_view(r):
    """The view of a result of the parser `pythonlib`, and whether the
    parser decoded the packet."""
    if "error" in r or r.get("format") in ("beacon", "invalid"):
        return {}, False
    view = {}
    for path, key in (
        ("position.lat", "latitude"),
        ("position.lon", "longitude"),
        ("position.course", "course"),
        ("position.speed", "speed"),
        ("position.altitude", "altitude"),
    ):
        _put_n(view, path, r.get(key))
    _put_e(view, "position.ambiguity", r, "posambiguity")
    if "symbol" in r and "symbol_table" in r:
        view["position.symbol"] = ("e", r["symbol_table"] + r["symbol"])
    _put_e(view, "position.messaging", r, "messagecapable")
    if "latitude" in r:
        _put_e(view, "position.comment", r, "comment")
    _put_e(view, "object.name", r, "object_name")
    _put_e(view, "object.live", r, "alive")
    w = r.get("weather")
    if isinstance(w, dict):
        # The parser gives wind speed and gust in metres per second.
        for path, key, factor in (
            ("wind_direction", "wind_direction", 1),
            ("wind_speed", "wind_speed", 3.6),
            ("gust", "wind_gust", 3.6),
            ("temperature", "temperature", 1),
            ("rain_1h", "rain_1h", 1),
            ("rain_24h", "rain_24h", 1),
            ("rain_midnight", "rain_since_midnight", 1),
            ("snow_24h", "snow", 1),
            ("humidity", "humidity", 1),
            ("pressure", "pressure", 1),
            ("luminosity", "luminosity", 1),
        ):
            _put_n(view, "weather." + path, w.get(key), factor)
    fmt = r.get("format")
    if fmt == "message":
        view["message.kind"] = ("e", r["response"] if r.get("response") in ("ack", "rej") else "message")
        _put_e(view, "message.addressee", r, "addresse")
        _put_e(view, "message.text", r, "message_text")
        _put_e(view, "message.id", r, "msgNo")
    elif fmt in ("bulletin", "group-bulletin", "announcement"):
        view["bulletin.kind"] = ("e", "announcement" if fmt == "announcement" else "bulletin")
        _put_e(view, "bulletin.id", r, "aid" if fmt == "announcement" else "bid")
        _put_e(view, "bulletin.group", r, "identifier")
        _put_e(view, "bulletin.text", r, "message_text")
    elif fmt == "status":
        _put_e(view, "status.text", r, "status")
    _telemetry(view, r.get("telemetry"))
    return view, True


def fap_view(r):
    """The view of a result of the parser `fap`, and whether the parser
    decoded the packet."""
    if not r.get("ok"):
        return {}, False
    view = {}
    for path, key in (
        ("position.lat", "latitude"),
        ("position.lon", "longitude"),
        ("position.course", "course"),
        ("position.speed", "speed"),
        ("position.altitude", "altitude"),
    ):
        _put_n(view, path, r.get(key))
    _put_e(view, "position.ambiguity", r, "posambiguity")
    if "symbolcode" in r and "symboltable" in r:
        view["position.symbol"] = ("e", r["symboltable"] + r["symbolcode"])
    _put_e(view, "position.messaging", r, "messaging", bool)
    if "latitude" in r:
        _put_e(view, "position.comment", r, "comment")
    _put_e(view, "object.name", r, "objectname")
    _put_e(view, "object.name", r, "itemname")
    _put_e(view, "object.live", r, "alive", bool)
    w = r.get("wx")
    if isinstance(w, dict):
        # The parser gives wind speed and gust in metres per second.
        for path, key, factor in (
            ("wind_direction", "wind_direction", 1),
            ("wind_speed", "wind_speed", 3.6),
            ("gust", "wind_gust", 3.6),
            ("temperature", "temp", 1),
            ("rain_1h", "rain_1h", 1),
            ("rain_24h", "rain_24h", 1),
            ("rain_midnight", "rain_midnight", 1),
            ("snow_24h", "snow_24h", 1),
            ("humidity", "humidity", 1),
            ("pressure", "pressure", 1),
            ("luminosity", "luminosity", 1),
        ):
            _put_n(view, "weather." + path, w.get(key), factor)
    if r.get("type") == "message" and str(r.get("destination", "")).startswith("BLN"):
        # The parser has no bulletin. It gives a message to an addressee
        # that starts with BLN.
        _put_e(view, "bulletin.text", r, "message")
    elif r.get("type") == "message":
        # A message with a reply-ack has `message` and `messageack`.
        kind = "message" if "message" in r else "ack" if "messageack" in r else "rej" if "messagerej" in r else "message"
        view["message.kind"] = ("e", kind)
        _put_e(view, "message.addressee", r, "destination")
        _put_e(view, "message.text", r, "message")
        _put_e(view, "message.id", r, {"ack": "messageack", "rej": "messagerej"}.get(kind, "messageid"))
    _put_e(view, "status.text", r, "status")
    _telemetry(view, r.get("telemetry"))
    if isinstance(r.get("capabilities"), dict):
        view["capabilities.items"] = ("e", r["capabilities"])
    return view, True


VIEWS = {"pythonlib": pythonlib_view, "fap": fap_view}


# --- Section 6: comparison -------------------------------------------------


# A difference of exactly half of `res` does not agree. This margin keeps
# the rounding error of the doubles from changing that outcome.
HALF = 0.5 * (1 - 1e-9)


def _present(view):
    """The view without the texts that are empty after the trim."""
    return {path: v for path, v in view.items() if not (v[0] == "e" and isinstance(v[1], str) and not _trim(v[1]))}


def compare(ours, theirs):
    """(path, outcome) for each path of either view."""
    ours, theirs = _present(ours), _present(theirs)
    out = []
    for path in ours.keys() | theirs.keys():
        a, b = ours.get(path), theirs.get(path)
        if b is None:
            out.append((path, "ours-only"))
        elif a is None:
            out.append((path, "theirs-only"))
        elif a[0] == "n":
            n = b[1] if b[0] == "n" else _number(b[1])
            # Two numbers agree if they differ by less than half of `res`.
            out.append((path, "agree" if n is not None and abs(a[1] - n) < a[2] * HALF else "differ"))
        else:
            out.append((path, "agree" if _trim(a[1]) == _trim(b[1]) else "differ"))
    return out
