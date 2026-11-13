# SPDX-License-Identifier: Apache-2.0
"""Messages, acknowledgements, bulletins, announcements, NWS bulletins, NTS
lines and the obsolete bulletin without an identifier:
docs/legacy/08-message.md."""

import re

from qua_network.legacy.fields import (
    SP,
    bad_text_bytes,
    noarchive_in,
    noarchive_outside,
)
from qua_network.legacy.model import UNREAD, Scan

TELEMETRY = "07-telemetry"
QUERY = "09-other"

_ALNUM = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
_NAME = _ALNUM | {0x2D}
_DIGITS = frozenset(b"0123456789")
_UPPER = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_SV = ("syntax", "value")
_TEXT_MAX = 67

# Section 4: the keyword and a msg.ack.num, nothing else.
_ACK = re.compile(rb"(?:ack|rej)(?:[A-Za-z0-9]{1,5}|[A-Za-z0-9]{2}\}(?:[A-Za-z0-9]{2})?)")
_TLM_KW = (b"PARM.", b"UNIT.", b"EQNS.", b"BITS.")
# 09 section 4.1, reading (a) of amb.qry.dir: mark, type, optional SP,
# optional heard station, optional trailing SP; no '{' can match.
_QUERY = re.compile(rb"\?(?:APRS[DHMOPST]|PING\?) ?(?:[A-Za-z0-9-]{1,9})? *")
_NWS_WORDS = (b"ADVIS", b"WARN", b"WATCH")
# Reading (c) of amb.nws.addressee.
_NWS_OTHER = (b"NWS_", b"SKY", b"CWA", b"BOM")
# Section 8: the type byte and the number of fields it allows.
_NTS = {ord("#"): (8, 8), ord("A"): (1, 4), ord("P"): (1, 1), ord("S"): (1, 1), ord("R"): (4, 4)}
_NTS.update({c: (1, 1) for c in b"123456"})


def _pending(scan, what):
    """A part that another file's reader decides; the packet has no verdict."""
    if what not in scan.unread:
        scan.unread.append(what)


def read(scan, start, end, depth):
    """A ':' field; start is the identifier byte, whose token is emitted."""
    texts = []
    _read(scan, start, end, depth, texts, True)
    noarchive_outside(scan, start, end, texts)


def _read(scan, s, end, depth, texts, by_addressee):
    """Read the field line[s:end]. by_addressee=False reads it as a message
    by section 2.1 from case 3 on, whatever the addressee, for the other
    readings of amb.msg.order, amb.bln.forms and amb.nws.addressee.
    Returns the kind decided, or None when the field ends before the text."""
    line = scan.line
    a0 = s + 1
    if by_addressee and line.startswith(b"BLN", a0, end):
        kind = "bln"
        ok = _bln_addr(scan, s, end, depth)
    elif by_addressee and line.startswith(b"NWS-", a0, end):
        kind = "nws"
        ok = _nws_addr(scan, s, end, depth)
    else:
        kind = None
        ok = _msg_addr(scan, s, end, depth)
    if not ok:
        if kind:
            scan.retag(s, depth, kind + ".dti")
        return None
    sep = s + 10
    if sep >= end:
        scan.find("msg.sep", "syntax", sep)
        if kind:
            scan.retag(s, depth, kind + ".dti")
        return None
    scan.tok("msg.sep", sep, sep + 1, depth)
    if line[sep] != 0x3A:
        # Section 2: no earlier ':' is looked for; the text still starts at 11.
        scan.find("msg.sep", "syntax", sep)
    t0 = sep + 1

    if kind == "bln":
        _bulletin(scan, s, t0, end, depth, texts)
        return kind
    if kind == "nws":
        _nws(scan, s, t0, end, depth, texts)
        return kind
    kind = _text_kind(line, t0, end)
    if kind == "ack":
        scan.tok("msg.ack.kw" if line[t0] == 0x61 else "msg.rej.kw", t0, t0 + 3, depth)
        scan.tok("msg.ack.num", t0 + 3, end, depth)
    elif kind == "qry":
        # 09 section 4.1 reads the text from offset 11.
        scan.retag(s, depth, "qry.dir.dti")
        scan.residue(t0, end, depth, UNREAD)
        _pending(scan, QUERY)
        # Section 2.1, case 5: the text is message text for the length limit.
        if end - t0 > _TEXT_MAX:
            scan.find("msg.text", "value", t0 + _TEXT_MAX)
    else:
        _message(scan, s, t0, end, depth, texts, kind)
    if by_addressee and kind != "tlm" and line.startswith(_NWS_OTHER, a0, end):
        # amb.nws.addressee, reading (c): an NWS bulletin, which accepts any
        # text bytes and has no length limit or message identifier.
        if not _reported(scan, a0, end):
            scan.find("msg.addr", "ambiguous", a0)
    return kind


def _text_kind(line, t0, end):
    """Cases 3 to 6 of section 2.1."""
    if _ACK.fullmatch(line, t0, end):
        return "ack"
    if line.startswith(_TLM_KW, t0, end):
        return "tlm"
    if _QUERY.fullmatch(line, t0, end):
        return "qry"
    return "msg"


def _reported(scan, lo, hi):
    """Whether the reading already gives a syntax or value finding on
    line[lo:hi] (README section 3, precedence)."""
    return any(f.kind in _SV and lo <= f.offset < hi for f in scan.findings)


def _as_message(scan, s, end, depth):
    """The other reading that takes the field as a message from case 3 on.
    Returns (kind, whether it gives a syntax or value finding of its own)."""
    other = Scan(scan.line)
    kind = _read(other, s, end, depth, [], False)
    mine = {(f.kind, f.offset) for f in scan.findings if f.kind in _SV}
    own = any((f.kind, f.offset) not in mine for f in other.findings if f.kind in _SV)
    return kind, own


def _other_reading(scan, s, end, depth, lo, hi, rule, at, kinds):
    """Give rule an ambiguous finding at `at` when the field read as a
    message from case 3 on is of one of kinds and gives no syntax or value
    finding of its own, unless this reading reports line[lo:hi] already.
    A definition message (case 4) has no reader yet, so whether it gives a
    finding of its own is open and the packet waits for 07."""
    if _reported(scan, lo, hi):
        return
    kind, own = _as_message(scan, s, end, depth)
    if own or kind not in kinds:
        return
    if kind == "tlm":
        _pending(scan, TELEMETRY)
        return
    # A text that matches a directed query gives no syntax or value finding
    # under 09 section 4.1, whose rows have none for it; the length limit of
    # msg.text, which _read applies, is the only one it can give.
    scan.find(rule, "ambiguous", at)


# --- Addressee (sections 2, 6 and 7) ------------------------------------


def _name(line, p, q, allowed):
    """A name from p to the first SP, then SP padding up to q.

    Returns (end of the name, offset of the first byte that fails, offset of
    the first byte outside allowed that gives unstated)."""
    n = p
    while n < q and line[n] != SP:
        n += 1
    bad = uns = None
    for i in range(p, n):
        c = line[i]
        if c in allowed:
            continue
        if 0x21 <= c <= 0x7E and c != 0x3A:
            if uns is None:
                uns = i
            continue
        bad = i
        break
    if bad is None:
        # A SP followed by a non-space: the first byte where the padding fails.
        bad = next((i for i in range(n, q) if line[i] != SP), None)
    return n, bad, uns


def _name_tokens(scan, p, n, q, depth, rule):
    if n > p:
        scan.tok(rule, p, n, depth)
    if q > n:
        scan.tok("msg.addr.pad", n, q, depth)


def _msg_addr(scan, s, end, depth):
    """msg.addr; returns True when all 9 bytes are present."""
    line = scan.line
    a0, q = s + 1, min(s + 10, end)
    if q > a0:
        scan.tok("msg.addr", a0, q, depth)
    n, bad, uns = _name(line, a0, q, _NAME)
    _name_tokens(scan, a0, n, q, depth + 1, "msg.addr.name")
    if uns is not None:
        scan.find("msg.addr.name", "unstated", uns)
    if n == a0 < q:
        # A SP where the name starts: the name is missing, whatever follows.
        bad = a0
    if bad is not None:
        scan.find("msg.addr.name", "syntax", bad)
    elif q < s + 10:
        scan.find("msg.addr", "syntax", q)
    return q == s + 10


def _bln_addr(scan, s, end, depth):
    """bln.addr (section 6, amb.bln.forms); returns True when complete."""
    line = scan.line
    a0, q = s + 1, min(s + 10, end)
    d = depth + 1
    scan.tok("bln.addr", a0, q, depth)
    scan.tok("bln.kw", a0, a0 + 3, d)
    p = a0 + 3
    bad = uns = None
    if p < q:
        c = line[p]
        if c in _DIGITS:
            scan.tok("bln.num", p, p + 1, d)
            n, bad, uns = _name(line, p + 1, q, _NAME)
            _name_tokens(scan, p + 1, n, q, d, "bln.group")
        elif c in _UPPER and all(b == SP for b in line[p + 1 : q]):
            scan.tok("bln.ann", p, p + 1, d)
            _name_tokens(scan, p + 1, p + 1, q, d, "bln.group")
        else:
            # None of the three forms: still a bulletin (section 6), the
            # bytes after BLN one bln.group.
            scan.find("bln.addr", "unstated", p)
            n, bad, uns = _name(line, p, q, _NAME)
            _name_tokens(scan, p, n, q, d, "bln.group")
    if uns is not None:
        scan.find("bln.group", "unstated", uns)
    if bad is not None:
        scan.find("bln.group", "syntax", bad)
    elif q < s + 10:
        scan.find("bln.addr", "syntax", q)
    return q == s + 10


def _nws_addr(scan, s, end, depth):
    """nws.addr (section 7); returns True when complete."""
    line = scan.line
    a0, q = s + 1, min(s + 10, end)
    d = depth + 1
    scan.tok("nws.addr", a0, q, depth)
    scan.tok("nws.kw", a0, a0 + 4, d)
    p = a0 + 4
    n, bad, uns = _name(line, p, q, _ALNUM)
    _name_tokens(scan, p, n, q, d, "nws.level")
    if uns is not None:
        scan.find("nws.level", "unstated", uns)
    if n == p < q:
        bad = p
    if bad is not None:
        scan.find("nws.level", "syntax", bad)
    elif q < s + 10:
        scan.find("nws.addr", "syntax", q)
    return q == s + 10


# --- Messages and NTS lines (sections 3 and 8) --------------------------


def _text_bytes(scan, rule, p, e):
    for i in bad_text_bytes(scan.line[p:e]):
        scan.find(rule, "syntax", p + i)


def _message(scan, s, t0, end, depth, texts, kind):
    """msg.text and the message identifier; kind is "msg" or "tlm"."""
    line = scan.line
    brace = line.find(b"{", t0, end)
    te = brace if brace >= 0 else end
    if te > t0:
        scan.tok("msg.text", t0, te, depth)
        _text_bytes(scan, "msg.text", t0, te)
        if te - t0 > _TEXT_MAX:
            scan.find("msg.text", "value", t0 + _TEXT_MAX)
    if kind == "tlm":
        # Case 4: 07 section 4 reads the text inside msg.text.
        scan.retag(s, depth, "tlm.def.dti")
        scan.residue(t0, te, depth + 1, UNREAD)
        _pending(scan, TELEMETRY)
    else:
        if not _nts(scan, t0, te, depth, texts) and te > t0:
            texts.append((t0, te))
            noarchive_in(scan, t0, te, depth + 1)
        head = line[t0 : min(t0 + 5, te)]
        if head.upper() in _TLM_KW:
            # amb.tlm.keyword: whether the text read as a definition message
            # fits is for 07 to decide.
            _pending(scan, TELEMETRY)
        if te - t0 >= 3 and _ACK.fullmatch(line[t0 : t0 + 3].lower() + line[t0 + 3 : end]):
            # amb.msg.ack: reading (b) folds the case of the keyword.
            if not _reported(scan, t0, end):
                scan.find("msg.text", "ambiguous", t0)
    if brace >= 0:
        _msg_id(scan, brace, end, depth)


def _alnum_field(scan, rule, p, e, lengths):
    """Letters or digits from p to e, in one of the counts in lengths."""
    line = scan.line
    bad = next((i for i in range(p, e) if line[i] not in _ALNUM), None)
    run = (e if bad is None else bad) - p
    hi = max(lengths)
    if run > hi:
        scan.find(rule, "value", p + hi)
    elif bad is None and run not in lengths:
        scan.find(rule, "value", p)
    if bad is not None:
        scan.find(rule, "syntax", bad)


def _msg_id(scan, b, end, depth):
    """msg.id.open at b, then the plain or the reply-ack form (amb.msg.id,
    amb.msg.replyack)."""
    line = scan.line
    scan.tok("msg.id.open", b, b + 1, depth)
    p = b + 1
    close = line.find(b"}", p, end)
    if close < 0:
        if p == end:
            scan.find("msg.id", "syntax", end)
            return
        scan.tok("msg.id", p, end, depth)
        _alnum_field(scan, "msg.id", p, end, range(1, 6))
        return
    if close > p:
        scan.tok("msg.id.mm", p, close, depth)
    _alnum_field(scan, "msg.id.mm", p, close, (2,))
    scan.tok("msg.id.close", close, close + 1, depth)
    if end > close + 1:
        scan.tok("msg.id.aa", close + 1, end, depth)
    _alnum_field(scan, "msg.id.aa", close + 1, end, (0, 2))


def _nts(scan, t0, te, depth, texts):
    """NTS tokens inside msg.text line[t0:te]; returns True for an NTS line."""
    line = scan.line
    if te - t0 < 3 or line[t0] != 0x4E or line[t0 + 1] not in _NTS or line[t0 + 2] != 0x5C:
        return False
    d = depth + 1
    scan.tok("nts.prefix", t0, t0 + 3, d)
    p, count = t0 + 3, 0
    while True:
        q = line.find(b"\\", p, te)
        fe = q if q >= 0 else te
        if fe > p:
            # An empty field has no token and is not counted.
            count += 1
            scan.tok("nts.field", p, fe, d)
            texts.append((p, fe))
            noarchive_in(scan, p, fe, d + 1)
        if q < 0:
            break
        scan.tok("nts.sep", q, q + 1, d)
        p = q + 1
    lo, hi = _NTS[line[t0 + 1]]
    if not lo <= count <= hi:
        scan.find("nts.prefix", "syntax", t0)
    return True


# --- Bulletins and NWS bulletins (sections 6 and 7) ---------------------


def _ref(line, t0, end):
    """Start of a trailing '{' and 1 to 5 letters or digits, or None."""
    i = line.rfind(b"{", t0, end)
    if i >= 0 and 1 <= end - i - 1 <= 5 and all(c in _ALNUM for c in line[i + 1 : end]):
        return i
    return None


def _bulletin(scan, s, t0, end, depth, texts):
    line = scan.line
    scan.retag(s, depth, "bln.dti")
    ref = _ref(line, t0, end)
    te = end if ref is None else ref
    if te > t0:
        scan.tok("bln.text", t0, te, depth)
        _text_bytes(scan, "bln.text", t0, te)
        if te - t0 > _TEXT_MAX:
            scan.find("bln.text", "value", t0 + _TEXT_MAX)
        texts.append((t0, te))
        noarchive_in(scan, t0, te, depth + 1)
    if ref is not None:
        scan.tok("bln.ref", ref, end, depth)
        # amb.bln.ref: reading (b) takes it as text, within the limit.
        if end - t0 <= _TEXT_MAX:
            scan.find("bln.ref", "ambiguous", ref)
    p = s + 4
    if not (line[p] in _DIGITS or line[p] in _UPPER and all(b == SP for b in line[p + 1 : s + 10])):
        # amb.bln.forms: reading (c) takes the packet as a message.
        _other_reading(scan, s, end, depth, s + 1, s + 10, "bln.addr", p, ("ack", "tlm", "qry", "msg"))
    # amb.msg.order: reading (b) classifies the text first.
    _other_reading(scan, s, end, depth, t0, end, "bln.text", t0, ("ack", "tlm", "qry"))


def _nws(scan, s, t0, end, depth, texts):
    line = scan.line
    scan.retag(s, depth, "nws.dti")
    ref = _ref(line, t0, end)
    te = end if ref is None else ref
    if te > t0:
        scan.tok("nws.text", t0, te, depth)
        _text_bytes(scan, "nws.text", t0, te)
        texts.append((t0, te))
        noarchive_in(scan, t0, te, depth + 1)
    else:
        # Section 7: unlike msg.text and bln.text, nws.text may not be empty.
        scan.find("nws.text", "syntax", t0)
    if ref is not None:
        scan.tok("nws.ref", ref, end, depth)
        # amb.bln.ref: NWS text has no length limit, so reading (b) accepts
        # it, unless this reading already fails on the reference's bytes.
        if not _reported(scan, ref, end):
            scan.find("nws.ref", "ambiguous", ref)
    word = line[s + 5 : s + 10].rstrip(b" ")
    if word not in _NWS_WORDS:
        # amb.nws.addressee, reading (b): only the listed words.
        _other_reading(scan, s, end, depth, s + 1, s + 10, "nws.level", s + 5, ("ack", "tlm", "qry", "msg"))
    _other_reading(scan, s, end, depth, t0, end, "nws.text", t0, ("ack", "tlm", "qry"))


# --- Obsolete bulletin without an identifier (section 9) ----------------


def obsolete_accepts(line, start, end):
    """Whether line[start:end] starts with BLN and a digit or an upper-case
    letter (amb.bln.obsolete)."""
    return end - start >= 4 and line.startswith(b"BLN", start) and (line[start + 3] in _DIGITS or line[start + 3] in _UPPER)


def obsolete(scan, start, end, depth):
    """bln.obsolete: one token over the field, nothing inside it."""
    scan.tok("bln.obsolete", start, end, depth)
    scan.find("bln.obsolete", "obsolete", start)
    # Not a free-text field, so a '!x!' in it gives the ambiguous finding of
    # amb.cmt.noarchive.
    noarchive_outside(scan, start, end, [])
