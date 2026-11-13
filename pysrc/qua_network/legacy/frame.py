# SPDX-License-Identifier: Apache-2.0
"""The TNC2 line, addresses, destination classes, the data type identifier
and third-party payloads: docs/legacy/01-frame.md."""

import re

from qua_network.legacy.message import obsolete as obsolete_bulletin
from qua_network.legacy.message import obsolete_accepts as obsolete_bulletin_accepts
from qua_network.legacy.model import UNREAD
from qua_network.legacy.objects import obsolete as obsolete_object
from qua_network.legacy.objects import obsolete_accepts as obsolete_object_accepts
from qua_network.legacy.position import nmea_accepts
from qua_network.tnc2 import header_spans

OBSOLETE_FORMS = "obsolete object or bulletin (05, 08)"

# --- Addresses (01 section 3) -------------------------------------------

_AX25 = re.compile(rb"([A-Z0-9]{1,6})(?:-([1-9]|1[0-5]))?\Z")
# A callsign whose suffix addr.ssid reports: '-0', '-0d' (syntax) or a
# two-digit value above 15 (value). Such an address is not addr.is.
_SSID_ZERO = re.compile(rb"[A-Z0-9]{1,6}-0[0-9]?\Z")
_SSID_HIGH = re.compile(rb"[A-Z0-9]{1,6}-(?:1[6-9]|[2-9][0-9])\Z")
_IS_ADDR = re.compile(rb"[\x21-\x29\x2b\x2d-\x39\x3b-\x3d\x3f-\x7e]{1,9}\Z")  # not > , : *
_CALL = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

AX25, IS_ONLY, BAD = 0, 1, 2


def first_bad(a, allowed, limit):
    """Offset in a of the first byte at fault for a name of 1 to limit bytes
    from allowed: the first byte outside allowed, the first byte past the
    limit, or 0 when a is empty (README section 3, Placing a finding)."""
    for i, c in enumerate(a[: limit + 1]):
        if i == limit or c not in allowed:
            return i
    return 0


_IS_SET = frozenset(range(0x21, 0x7F)) - frozenset(b">,:*")


def ax25_bad(a):
    """Offset in a of the first byte that does not fit the AX.25 text form,
    for an address that _AX25 rejects (len(a) when a byte is missing)."""
    i = 0
    while i < len(a) and i < 6 and a[i] in _CALL:
        i += 1
    if i == 0 or i == len(a) or a[i] != 0x2D:
        return i
    j = i + 1
    if j == len(a) or a[j] not in b"123456789":
        return j
    if j + 1 == len(a):
        return len(a)
    if a[j] != 0x31 or a[j + 1] not in b"012345":
        return j + 1
    return j + 2


def address(scan, start, end, depth, call_rule="addr.call", ssid_rule="addr.ssid"):
    """Tokenize one address at [start, end) one level below its own token.

    Returns (form, call_end) where form is AX25, IS_ONLY or BAD and call_end
    is where the callsign part ends (end for an addr.is address).
    """
    a = scan.line[start:end]
    m = _AX25.match(a)
    if m:
        ce = start + m.end(1)
        scan.tok(call_rule, start, ce, depth)
        if ce < end:
            scan.tok(ssid_rule, ce, end, depth)
        return AX25, ce
    if _SSID_ZERO.match(a) or _SSID_HIGH.match(a):
        dash = start + a.index(b"-")
        scan.tok(call_rule, start, dash, depth)
        scan.tok(ssid_rule, dash, end, depth)
        scan.find("addr.ssid", "syntax" if a[dash - start + 1] == 0x30 else "value", dash)
        return AX25, dash
    if _IS_ADDR.match(a):
        scan.tok("addr.is", start, end, depth)
        scan.find("addr.is", "is-only", start)
        return IS_ONLY, end
    scan.residue(start, end, depth, "addr.is")
    scan.find("addr.is", "syntax", start + first_bad(a, _IS_SET, 9))
    return BAD, end


# --- Destination classes (01 section 5) ---------------------------------

_MICE_DTI = frozenset(b"\x1c\x1d'`")
_TOCALL = re.compile(rb"AP[A-Z0-9]{1,4}\Z")
_SYMNN = re.compile(rb"GPS[CE]([0-9]{2})\Z")
_SYM = re.compile(rb"(?:GPS|SPC|SYM)(..)([0-9A-Z]?)\Z", re.S)
_GENERIC = re.compile(
    rb"(?:ALL|AP|CQ|DF|DGPS|DRILL|DX|GPS|ID|JAVA|MAIL|MICE|QST|QTH|RTCM|SKY|SPACE|SPC|SYM|TEL|TEST|TLM|WX)[A-Z0-9]*\Z"
)
_GRID = re.compile(rb"[A-R]{2}[0-9]{2}[A-X]{2}\Z")


def _sym_pairs():
    """The xy pairs of dest.sym, from the pattern in 01 section 5."""
    primary, alternate = set(), set()

    def run(first_p, first_a, seconds):
        for s in seconds:
            primary.add(bytes((first_p, s)))
            alternate.add(bytes((first_a, s)))

    run(ord("B"), ord("O"), range(ord("B"), ord("P") + 1))
    run(ord("P"), ord("A"), range(ord("0"), ord("9") + 1))
    run(ord("M"), ord("N"), range(ord("R"), ord("X") + 1))
    run(ord("P"), ord("A"), range(ord("A"), ord("Z") + 1))
    run(ord("H"), ord("D"), range(ord("S"), ord("X") + 1))
    run(ord("L"), ord("S"), range(ord("A"), ord("Z") + 1))
    run(ord("J"), ord("Q"), range(ord("1"), ord("4") + 1))
    return frozenset(primary), frozenset(alternate)


_SYM_PRIMARY, _SYM_ALTERNATE = _sym_pairs()


def dest_class(scan, call, start, dti):
    """Classify the destination callsign part; returns the class rule ID."""
    if dti in _MICE_DTI:
        return "dest.mice"
    if call == b"APRS":
        scan.find("dest.aprs", "obsolete", start)
        cls = "dest.aprs"
    elif _TOCALL.match(call):
        cls = "dest.tocall"
    elif m := _SYMNN.match(call):
        if not 1 <= int(m.group(1)) <= 94:
            scan.find("dest.symnn", "value", start + 4)
        cls = "dest.symnn"
    elif (m := _SYM.match(call)) and (m.group(1) in _SYM_PRIMARY or m.group(1) in _SYM_ALTERNATE):
        if m.group(2) and m.group(1) in _SYM_PRIMARY:
            scan.find("dest.sym", "value", start + 5)
        cls = "dest.sym"
    elif _GENERIC.match(call) and len(call) <= 6 or call == b"BEACON":
        cls = "dest.generic"
    elif _GRID.match(call):
        scan.find("dest.grid", "obsolete", start)
        cls = "dest.grid"
    else:
        cls = "dest.altnet"
    # A locator shape that another class takes, or whose letters are out of
    # range, is not a locator and gives no finding (README section 3).
    return cls


# --- The header (01 sections 2 to 4) ------------------------------------

_Q = re.compile(rb"qA[A-Za-z]\Z")
_OBSOLETE_ALIAS = frozenset((b"RELAY", b"TRACE", b"WIDE"))
_NOGATE = frozenset((b"NOGATE", b"RFONLY"))


def _strip_star(line, s, e):
    if e > s and line[e - 1] == 0x2A:
        return e - 1, True
    return e, False


def _syntax_since(scan, n):
    """Whether a syntax finding was given after the first n findings: a field
    gives at most one, at its first failing byte (README section 3, Placing a
    finding), so a '*' after an address that already failed adds none."""
    return any(f.kind == "syntax" for f in scan.findings[n:])


def header(scan, end, dti, depth=0):
    """Tokenize the address header line[0:end]; end is the index of ':'."""
    line = scan.line
    spans = header_spans(line[:end])
    if spans is None:
        scan.residue(0, end, depth, "line.gt")
        scan.find("line.gt", "syntax", 0)
        return
    (ss, se), (ds, de), entries = spans

    # Source. A field whose extent its delimiter fixes keeps its token when
    # its bytes are wrong; a trailing '*', which no rule reads there, is a
    # residue one level below (README section 3, Output).
    ae, star = _strip_star(line, ss, se)
    scan.tok("addr.src", ss, se, depth)
    n = len(scan.findings)
    if ae == ss:
        scan.find("addr.src", "syntax", ss)
    else:
        address(scan, ss, ae, depth + 1, ssid_rule="src.ssid")
    if star:
        scan.residue(ae, se, depth + 1, "addr.src")
        if not _syntax_since(scan, n):
            scan.find("addr.src", "syntax", ae)
    scan.tok("line.gt", se, se + 1, depth)

    # Destination.
    ae, star = _strip_star(line, ds, de)
    scan.tok("addr.dest", ds, de, depth)
    n = len(scan.findings)
    if ae == ds:
        scan.find("addr.dest", "syntax", ds)
    else:
        _dest(scan, ds, ae, depth + 1, dti)
    if star:
        scan.residue(ae, de, depth + 1, "addr.dest")
        if not _syntax_since(scan, n):
            scan.find("addr.dest", "syntax", ae)

    _path(scan, entries, depth)


def _path(scan, entries, depth, inner=False):
    """Path entries: path.digi before the first q-construct, path.q, then path.is.

    In an inner header (inner=True) each entry is a tp.path token that
    includes its ',', and the entry is classified one level below it; a '*'
    there gives syntax (amb.tp.header).
    """
    line = scan.line
    q_seen = False
    n_digi = 0
    used_seen = False
    for es, ee in entries:
        star_at = -1
        if inner:
            scan.tok("tp.path", es - 1, ee, depth)
            d = depth + 1
            if ee == es:
                scan.find("tp.path", "syntax", es - 1)
            star_at = line.find(b"*", es, ee)
        else:
            scan.tok("path.sep", es - 1, es, depth)
            d = depth
            if ee == es:
                scan.find("path.sep", "syntax", es - 1)
        if ee == es:
            # An empty entry counts toward the limit of 8 (01 path.sep).
            if not q_seen:
                n_digi += 1
                if n_digi == 9:
                    scan.find("path.digi", "syntax", es - 1)
            continue
        entry = line[es:ee]
        if not q_seen and _Q.match(entry):
            q_seen = True
            scan.tok("path.q", es, ee, d)
            scan.find("path.q", "is-only", es)
            continue
        if q_seen:
            # In an inner header the entry ends at its first '*', as above.
            pe = star_at if star_at >= 0 else ee
            entry = line[es:pe]
            if pe > es:
                scan.tok("path.is", es, pe, d)
            bad = next((es + i for i, c in enumerate(entry) if not 0x21 <= c <= 0x7E), pe)
            if bad < pe:
                scan.find("path.is", "syntax", bad)
            elif pe > es:
                body = entry[:-1] if entry.endswith(b"*") else entry
                if entry.endswith(b"*"):
                    scan.find("path.is", "unstated", ee - 1)
                # The SSID text-form rules of addr.ssid are not applied here.
                if not _AX25.match(body):
                    scan.find("path.is", "is-only", es)
            if star_at >= 0:
                scan.residue(star_at, ee, d, "tp.path")
                if bad == pe:
                    scan.find("tp.path", "syntax", star_at)
            continue
        n_digi += 1
        n = len(scan.findings)
        if star_at >= 0:
            # In an inner header the '*' and what follows it are a residue
            # below the tp.path token, with one syntax finding at the '*'
            # unless the address before it already gave one.
            ae, star = star_at, True
            if ae > es:
                scan.tok("path.digi", es, ae, d)
        else:
            ae, star = _strip_star(line, es, ee)
            scan.tok("path.digi", es, ae, d)
        if n_digi == 9:
            scan.find("path.digi", "syntax", es - 1)
        if ae == es:
            if not inner:
                scan.find("path.digi", "syntax", es)
        else:
            # The callsign part of an alias or a gating block carries its class.
            call = line[es:ae].partition(b"-")[0]
            if call in _OBSOLETE_ALIAS:
                call_rule = "path.obsolete"
            elif call in _NOGATE:
                call_rule = "path.nogate"
            else:
                call_rule = "addr.call"
            form, _ = address(scan, es, ae, d + 1, call_rule=call_rule)
            if form == AX25 and call_rule == "path.obsolete":
                scan.find("path.obsolete", "obsolete", es)
        if star and not inner:
            scan.tok("path.used", ae, ee, d)
            if used_seen:
                scan.find("path.used", "syntax", ae)
            used_seen = True
        elif star:
            scan.residue(ae, ee, d, "tp.path")
            if not _syntax_since(scan, n):
                scan.find("tp.path", "syntax", ae)


def _dest(scan, ds, de, depth, dti):
    """Tokenize a destination address; its callsign part carries its class."""
    a = scan.line[ds:de]
    if _AX25.match(a) or _SSID_ZERO.match(a) or _SSID_HIGH.match(a):
        call, _, ssid = a.partition(b"-")
        cls = dest_class(scan, call, ds, dti)
        form, ce = address(scan, ds, de, depth, call_rule=cls, ssid_rule="dest.ssid")
        if ssid and _AX25.match(a) and dti not in _MICE_DTI:
            scan.find("dest.ssid", "obsolete", ce)
        return form, ce
    form, ce = address(scan, ds, de, depth, ssid_rule="dest.ssid")
    if form == IS_ONLY:
        # The class applies to the bytes as written ([agreed]: a lower-case
        # locator shape is not dest.grid and falls through to the next class).
        scan.tokens[-1] = scan.tokens[-1]._replace(rule=dest_class(scan, a, ds, dti))
    return form, ce


# --- Data type identifier (01 section 7) --------------------------------

# Byte value -> (identifier rule of the format, file that reads it, finding at dti).
# The identifier rule is provisional where 01 section 7 lets it depend on
# later bytes (weather symbol, ':' kind); the format readers refine it.
_DISPATCH = {}


def _set(chars, rule, where, finding=None):
    for c in chars:
        _DISPATCH[c] = (rule, where, finding)


_set(b"\x1c\x1d'`", "mice.dti", "04-mic-e")
_set(b"!=/@", "pos.dti", "03-position")
_set(b"#*", "wx.raw.peet", "06-weather", "discouraged")
_set(b"$", "nmea.dti", "03-position", "discouraged")
_set(b"%", "df.agrelo.dti", "03-position")
_set(b")", "item.dti", "05-object-item")
_set(b",", "inv.dti", "09-other")
_set(b":", "msg.dti", "08-message")
_set(b";", "obj.dti", "05-object-item")
_set(b"<", "cap.dti", "09-other")
_set(b">", "stat.dti", "09-other")
_set(b"?", "qry.dti", "09-other")
_set(b"T", "tlm.dti", "07-telemetry")
_set(b"[", "grid.dti", "03-position", "obsolete")
_set(b"_", "wx.pl", "06-weather", "discouraged")
_set(b"{", "udf.dti", "09-other")
_set(b"}", "tp.dti", "01-frame")

_DO_NOT_USE = frozenset(b"0123456789ABCDEFGHIJKLMNOPQRSUVWXYZabcdefghijklmnopqrstuvwxyz|~")


def dispatch(info):
    """(identifier rule, reading file, finding at dti) for an information field,
    or (None, None, kind) when the field is dti.unknown."""
    b = info[0]
    if b == 0x21 and info[1:2] == b"!":
        return "wx.raw.ultlog.dti", "06-weather", "discouraged"
    if b == 0x24 and info.startswith(b"$ULTW"):
        return "wx.raw.ultpkt.dti", "06-weather", "discouraged"
    if b in _DISPATCH:
        return _DISPATCH[b]
    return None, None, "syntax" if b in _DO_NOT_USE else "unstated"


# --- Information field and third-party payloads (01 sections 2, 7, 8) ---


def info_field(scan, start, end, depth, readers, tp_level=0):
    """Tokenize line[start:end] as an information field from its dti."""
    line = scan.line
    if end == start:
        scan.find("tp.info" if tp_level else "line.info", "syntax", start)
        return
    if end - start > 256 and depth == 0:
        scan.find("line.info", "value", start + 256)
    rule, where, finding = dispatch(line[start:end])
    if rule is None:
        # The obsolete object and bulletin without an identifier are tried
        # first, in that order (01 section 7). Without both readers the
        # field may still be one of them, so the packet gets no verdict; the
        # bulletin is tried only once the object reader has declined it.
        if "05-object-item" in readers and obsolete_object_accepts(line, start, end):
            obsolete_object(scan, start, end, depth)
            return
        if "05-object-item" in readers and "08-message" in readers and obsolete_bulletin_accepts(line, start, end):
            obsolete_bulletin(scan, start, end, depth)
            return
        scan.tok("dti.unknown", start, end, depth)
        scan.find("dti", finding, start)
        if "05-object-item" in readers and "08-message" in readers:
            scan.unknown_format = True
        else:
            scan.unread.append(OBSOLETE_FORMS)
        return
    if finding:
        scan.find("dti", finding, start)
    if rule == "wx.raw.ultpkt.dti" and nmea_accepts(line, start, end):
        # amb.dti.shared: the field is also a raw NMEA sentence.
        scan.find("wx.raw.ultpkt", "ambiguous", start + 1)
    if rule == "tp.dti":
        third_party(scan, start, end, depth, readers, tp_level)
        return
    scan.tok(rule, start, start + 1, depth)
    reader = readers.get(where)
    if reader is None:
        scan.residue(start + 1, end, depth, UNREAD)
        scan.unread.append(where)
        return
    reader(scan, start, end, depth)


def third_party(scan, start, end, depth, readers, level):
    """A '}' field: inner TNC-2 header, then the original information field."""
    line = scan.line
    scan.tok("tp.dti", start, start + 1, depth)
    if level:
        scan.find("tp.dti", "unstated", start)
    sep = line.find(b":", start + 1, end)
    if sep < 0:
        scan.residue(start + 1, end, depth, "tp.sep")
        scan.find("tp.sep", "syntax", end)
        return
    h0 = start + 1
    if not _tp_aea(scan, h0, sep, depth):
        _tp_header(scan, h0, sep, depth)
    scan.tok("tp.sep", sep, sep + 1, depth)
    scan.tok("tp.info", sep + 1, end, depth)
    info_field(scan, sep + 1, end, depth + 1, readers, level + 1)


_TP_SRC_IS = re.compile(rb"[\x21-\x29\x2b-\x39\x3b-\x3d\x3f-\x7e]{1,9}\Z")  # not > : *
_TP_SRC_SET = frozenset(range(0x21, 0x7F)) - frozenset(b">:*")


def _inner_dti(scan, sep):
    return scan.line[sep + 1] if sep + 1 < len(scan.line) else -1


def _tp_aea(scan, h0, sep, depth):
    """An AEA-form inner header (amb.tp.aea): at least four non-empty addresses
    separated by '>', no ',', and one '*', at the end of the gateway, which is
    the second-to-last address; the last is the original destination."""
    line = scan.line
    hdr = line[h0:sep]
    pieces = hdr.split(b">")
    if b"," in hdr or len(pieces) < 4 or not all(pieces):
        return False
    if hdr.count(b"*") != 1 or not pieces[-2].endswith(b"*"):
        return False
    scan.tok("tp.aea", h0, sep, depth)
    scan.find("tp.aea", "obsolete", h0)
    pos = h0
    for i, p in enumerate(pieces):
        ps, pe = pos, pos + len(p)
        if i == len(pieces) - 1:
            _dest(scan, ps, pe, depth + 1, _inner_dti(scan, sep))
        else:
            address(scan, ps, pe - (i == len(pieces) - 2), depth + 1)
        pos = pe + 1
    return True


def _tp_header(scan, h0, sep, depth):
    line = scan.line
    spans = header_spans(line[h0:sep], h0)
    if spans is None:
        scan.residue(h0, sep, depth, "tp.gt")
        scan.find("tp.gt", "syntax", h0)
        return
    (ss, se), (ds, de), entries = spans
    scan.tok("tp.src", ss, se, depth)
    a = line[ss:se]
    if _AX25.match(a) or _SSID_ZERO.match(a) or _SSID_HIGH.match(a):
        address(scan, ss, se, depth + 1)
    elif _TP_SRC_IS.match(a):
        scan.find("tp.src", "is-only", ss)
    else:
        scan.find("tp.src", "syntax", ss + first_bad(a, _TP_SRC_SET, 9))
    scan.tok("tp.gt", se, se + 1, depth)
    ae, star = _strip_star(line, ds, de)
    scan.tok("tp.dest", ds, de, depth)
    n = len(scan.findings)
    if ae == ds:
        scan.find("tp.dest", "syntax", ds)
    else:
        _dest(scan, ds, ae, depth + 1, _inner_dti(scan, sep))
    if star:
        scan.residue(ae, de, depth + 1, "tp.dest")
        if not _syntax_since(scan, n):
            scan.find("tp.dest", "syntax", ae)
    if len(entries) < 2:
        # Network identifier and gateway are both required.
        for es, ee in entries:
            scan.tok("tp.net", es - 1, ee, depth)
        scan.find("tp.gate", "syntax", sep)
        return
    *path, (ns, ne), (gs, ge) = entries
    _path(scan, path, depth, inner=True)
    scan.tok("tp.net", ns - 1, ne, depth)
    star_at = line.find(b"*", ns, ne)
    if ne == ns:
        scan.find("tp.net", "syntax", ns)
    elif star_at >= 0:
        n = len(scan.findings)
        if star_at > ns:
            address(scan, ns, star_at, depth + 1)
        scan.residue(star_at, ne, depth + 1, "tp.net")
        if not _syntax_since(scan, n):
            scan.find("tp.net", "syntax", star_at)
    else:
        address(scan, ns, ne, depth + 1)
    # One syntax finding for the gateway, at its first byte at fault
    # (README section 3, Placing a finding).
    scan.tok("tp.gate", gs - 1, ge, depth)
    ae, star = _strip_star(line, gs, ge)
    g = line[gs:ae]
    if _AX25.match(g) or _SSID_ZERO.match(g) or _SSID_HIGH.match(g):
        n = len(scan.findings)
        address(scan, gs, ae, depth + 1)
        if not star and not _syntax_since(scan, n):
            scan.find("tp.gate", "syntax", ge)
    else:
        scan.find("tp.gate", "syntax", gs + ax25_bad(g))
