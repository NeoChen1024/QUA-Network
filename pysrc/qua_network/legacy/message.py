# SPDX-License-Identifier: Apache-2.0
"""Messages, acknowledgements, bulletins, announcements, NWS bulletins, NTS
lines and the obsolete bulletin without an identifier:
docs/legacy/08-message.md."""

import re

from qua_network.legacy.fields import SP, bad_text_bytes, noarchive_in
from qua_network.legacy.other import directed
from qua_network.legacy.telemetry import KEYWORDS as _TLM_KW
from qua_network.legacy.telemetry import definition as tlm_definition

_ALNUM = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
_NAME = _ALNUM | {0x2D}
_DIGITS = frozenset(b"0123456789")
_UPPER = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_SV = ("syntax", "value")
_TEXT_MAX = 67
_NUM_MAX = 5
_NWS_WORDS = frozenset((b"ADVIS", b"WARN", b"WATCH"))

# Section 4: the keyword and a msg.ack.num, nothing else; the number is
# letters or digits, with at most one '}' after its first byte, and its
# length is checked apart (at most 5).
_ACK = re.compile(rb"(?:ack|rej)[A-Za-z0-9]+(?:\}[A-Za-z0-9]*)?")
# 09 section 4.1 and amb.qry.dir: mark, a type of five upper-case letters or
# PING?, optional SP, optional heard station, optional trailing SP; no '{'
# can match.
_QUERY = re.compile(rb"\?(?:[A-Z]{5}|PING\?) ?(?:[A-Za-z0-9-]{1,9})? *")
# Section 8: the type byte and the number of fields it allows.
_NTS = {ord("#"): (8, 8), ord("A"): (1, 4), ord("P"): (1, 1), ord("S"): (1, 1), ord("R"): (4, 4)}
_NTS.update({c: (1, 1) for c in b"123456"})


def read(scan, s, end, depth):
    """A ':' field; s is the identifier byte, whose token is emitted. The
    kind is decided by section 2.1."""
    line = scan.line
    a0 = s + 1
    kind = None
    if line.startswith(b"BLN", a0, end):
        # amb.bln.forms: BLN announces a bulletin addressee.
        kind = "bln"
    elif line.startswith(b"NWS-", a0, end):
        kind = "nws"
    if kind == "bln":
        ok = _bln_addr(scan, s, end, depth)
    elif kind == "nws":
        ok = _nws_addr(scan, s, end, depth)
    else:
        ok = _msg_addr(scan, s, end, depth)
    if kind:
        scan.retag(s, depth, kind + ".dti")
    if not ok:
        return
    sep = s + 10
    if sep >= end:
        scan.find("msg.sep", "syntax", sep)
        return
    scan.tok("msg.sep", sep, sep + 1, depth)
    if line[sep] != 0x3A:
        # No earlier ':' is looked for; the text still starts at offset 11.
        scan.find("msg.sep", "syntax", sep)
    t0 = sep + 1

    if kind == "bln":
        _bln_text(scan, t0, end, depth)
        return
    if kind == "nws":
        _nws(scan, t0, end, depth)
        return
    kind = _text_kind(line, t0, end)
    if kind == "ack":
        scan.tok("msg.ack.kw" if line[t0] == 0x61 else "msg.rej.kw", t0, t0 + 3, depth)
        scan.tok("msg.ack.num", t0 + 3, end, depth)
        close = line.find(b"}", t0 + 3, end)
        if close >= 0 and _replyack_odd(close - t0 - 3, end - close - 1):
            scan.find("msg.ack.num", "unstated", t0 + 3)
    elif kind == "qry":
        # 09 section 4.1 reads the text from offset 11.
        scan.retag(s, depth, "qry.dir.dti")
        directed(scan, t0, end, depth)
        # Section 2.1, case 5: the text is message text for the length limit.
        over = _over(line, t0, end)
        if over is not None:
            scan.find("msg.text", "value", over)
    else:
        _message(scan, s, t0, end, depth, kind)


def _text_kind(line, t0, end):
    """Cases 3 to 6 of section 2.1."""
    if end - t0 <= 3 + _NUM_MAX and _ACK.fullmatch(line, t0, end):
        return "ack"
    if line.startswith(_TLM_KW, t0, end):
        return "tlm"
    if _QUERY.fullmatch(line, t0, end):
        return "qry"
    return "msg"


def _over(line, p, e):
    """Offset of the 68th character of line[p:e], counted as UTF-8 characters
    (amb.msg.text), or None when there are at most 67."""
    if e - p <= _TEXT_MAX:
        return None
    n = 0
    for i in range(p, e):
        if not 0x80 <= line[i] <= 0xBF:
            n += 1
            if n > _TEXT_MAX:
                return i
    return None


def _replyack_odd(mm, aa):
    """Whether reply-ack parts of these lengths are of a size p. 95/73 does
    not give (amb.msg.replyack): MM other than 2, AA other than 0 or 2."""
    return mm != 2 or aa not in (0, 2)


# --- Addressee (sections 2, 6 and 7) ------------------------------------


def _name(line, p, q, allowed):
    """A name from p to its last byte that is not SP, then SP padding up to q.

    Returns (end of the name, offset of the first byte of the name outside
    allowed, which gives unstated)."""
    n = q
    while n > p and line[n - 1] == SP:
        n -= 1
    uns = next((i for i in range(p, n) if line[i] not in allowed), None)
    return n, uns


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
    n, uns = _name(line, a0, q, _NAME)
    _name_tokens(scan, a0, n, q, depth + 1, "msg.addr.name")
    if uns is not None:
        scan.find("msg.addr.name", "unstated", uns)
    if n == a0 < q:
        # Only SP: the name is missing.
        scan.find("msg.addr.name", "syntax", a0)
    elif q < s + 10:
        scan.find("msg.addr", "syntax", q)
    return q == s + 10


def _bln_fits(line, p, q):
    """Whether the byte at p, after BLN, and the bytes to q fit one of the
    three addressees of p. 96/74 and p. 97/75: a digit, followed by 5 SP or a
    group name, or an upper-case letter followed by 5 SP."""
    c = line[p]
    if c in _DIGITS:
        return True
    return c in _UPPER and all(b == SP for b in line[p + 1 : q])


def _bln_addr(scan, s, end, depth):
    """bln.addr (section 6); returns True when complete."""
    line = scan.line
    a0, q = s + 1, min(s + 10, end)
    d = depth + 1
    scan.tok("bln.addr", a0, q, depth)
    scan.tok("bln.kw", a0, a0 + 3, d)
    p = a0 + 3
    uns = bad = None
    if p < q:
        c = line[p]
        if c in _DIGITS:
            scan.tok("bln.num", p, p + 1, d)
            n, uns = _name(line, p + 1, q, _NAME)
            _name_tokens(scan, p + 1, n, q, d, "bln.group")
        elif c in _UPPER:
            scan.tok("bln.ann", p, p + 1, d)
            # An announcement is padded with SP; a byte that is not SP is
            # where the last of the three forms fails (amb.bln.forms).
            bad = next((i for i in range(p + 1, q) if line[i] != SP), None)
            if bad is None:
                _name_tokens(scan, p + 1, p + 1, q, d, "bln.group")
        else:
            # amb.bln.forms: the byte fits none of the three forms.
            bad = p
    if uns is not None:
        scan.find("bln.group", "unstated", uns)
    if bad is not None:
        scan.find("bln.addr", "syntax", bad)
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
    n, _ = _name(line, p, q, _NAME)
    _name_tokens(scan, p, n, q, d, "nws.level")
    if n == p < q:
        scan.find("nws.level", "syntax", p)
    elif q < s + 10:
        scan.find("nws.addr", "syntax", q)
    elif line[p:n] not in _NWS_WORDS:
        # The words are an open list ("such as ... etc."), so another word,
        # whatever its bytes, gives unstated.
        scan.find("nws.level", "unstated", p)
    return q == s + 10


# --- Messages and NTS lines (sections 3 and 8) --------------------------


def _text_bytes(scan, rule, p, e):
    """One syntax finding for the field, at its first byte that is not a
    text byte."""
    bad = bad_text_bytes(scan.line[p:e])
    if bad:
        scan.find(rule, "syntax", p + bad[0])


def _message(scan, s, t0, end, depth, kind):
    """msg.text and the message identifier; kind is "msg" or "tlm"."""
    line = scan.line
    brace = line.find(b"{", t0, end)
    te = brace if brace >= 0 else end
    if te > t0:
        scan.tok("msg.text", t0, te, depth)
        over = _over(line, t0, te)
        if over is not None:
            scan.find("msg.text", "value", over)
    # A byte that is not a text byte gets its syntax finding on the most
    # specific rule that holds it: a field of 07 section 4 in case 4, an
    # nts.field in an NTS line, and otherwise msg.text.
    if kind == "tlm":
        # Case 4: 07 section 4 reads the text inside msg.text.
        scan.retag(s, depth, "tlm.def.dti")
        tlm_definition(scan, t0, te, depth + 1)
    else:
        if not _nts(scan, t0, te, depth) and te > t0:
            _text_bytes(scan, "msg.text", t0, te)
            noarchive_in(scan, t0, te, depth + 1)
    if brace >= 0:
        _msg_id(scan, brace, end, depth)


def _msg_id(scan, b, end, depth):
    """msg.id.open at b, then the plain or the reply-ack form. The number is
    at most 5 bytes: value at the sixth of a run of letters, digits and the
    one '}', and syntax at the first other byte; the two are independent."""
    line = scan.line
    scan.tok("msg.id.open", b, b + 1, depth)
    p = b + 1
    if p == end:
        scan.find("msg.id", "syntax", end)
        return
    close = line.find(b"}", p, end)
    bad = next((i for i in range(p, end) if line[i] not in _ALNUM and i != close), None)
    over = p + _NUM_MAX if (end if bad is None else bad) - p > _NUM_MAX else None
    if close < 0:
        scan.tok("msg.id", p, end, depth)
        if over is not None:
            scan.find("msg.id", "value", over)
        if bad is not None:
            scan.find("msg.id", "syntax", bad)
        return
    if close > p:
        scan.tok("msg.id.mm", p, close, depth)
    scan.tok("msg.id.close", close, close + 1, depth)
    if end > close + 1:
        scan.tok("msg.id.aa", close + 1, end, depth)
    if close == p:
        scan.find("msg.id.mm", "syntax", close)
    if over is not None:
        scan.find("msg.id.mm" if over <= close else "msg.id.aa", "value", over)
    if bad is not None:
        scan.find("msg.id.mm" if bad < close else "msg.id.aa", "syntax", bad)
    if close > p and over is None and bad is None and _replyack_odd(close - p, end - close - 1):
        scan.find("msg.id.mm" if close - p != 2 else "msg.id.aa", "unstated", p if close - p != 2 else close + 1)


def _nts(scan, t0, te, depth):
    """NTS tokens inside msg.text line[t0:te]; returns True for an NTS line.
    The prefix announces the line (amb.nts.prefix): a separator before a
    field past the number its type allows gives syntax, and so does the end
    of the text before the fewest fields it allows."""
    line = scan.line
    if te - t0 < 3 or line[t0] != 0x4E or line[t0 + 1] not in _NTS or line[t0 + 2] != 0x5C:
        return False
    lo, hi = _NTS[line[t0 + 1]]
    d = depth + 1
    scan.tok("nts.prefix", t0, t0 + 3, d)
    p = t0 + 3
    n = 1
    while True:
        q = line.find(b"\\", p, te)
        fe = q if q >= 0 else te
        if fe > p:
            scan.tok("nts.field", p, fe, d)
            _text_bytes(scan, "nts.field", p, fe)
            noarchive_in(scan, p, fe, d + 1)
        elif n <= hi:
            # An empty field is a case p. 98/76 does not give.
            scan.find("nts.field", "unstated", p)
        if q < 0:
            break
        scan.tok("nts.sep", q, q + 1, d)
        if n == hi:
            scan.find("nts.sep", "syntax", q)
        p = q + 1
        n += 1
    if n < lo:
        scan.find("nts.field", "syntax", te)
    return True


# --- Bulletins and NWS bulletins (sections 6 and 7) ---------------------


def _ref(line, t0, end):
    """Start of a trailing '{' and 1 to 5 letters or digits, or None."""
    i = line.rfind(b"{", t0, end)
    if i >= 0 and 1 <= end - i - 1 <= 5 and all(c in _ALNUM for c in line[i + 1 : end]):
        return i
    return None


def _bln_text(scan, t0, end, depth):
    """bln.text: a trailing '{' and letters or digits are text too."""
    if end > t0:
        scan.tok("bln.text", t0, end, depth)
        _text_bytes(scan, "bln.text", t0, end)
        over = _over(scan.line, t0, end)
        if over is not None:
            scan.find("bln.text", "value", over)
        noarchive_in(scan, t0, end, depth + 1)


def _nws(scan, t0, end, depth):
    line = scan.line
    ref = _ref(line, t0, end)
    te = end if ref is None else ref
    if te > t0:
        scan.tok("nws.text", t0, te, depth)
        _text_bytes(scan, "nws.text", t0, te)
        noarchive_in(scan, t0, te, depth + 1)
    if ref is not None:
        scan.tok("nws.ref", ref, end, depth)
        # amb.bln.ref: the bytes are also NWS text, which has no length limit.
        if not any(f.kind in _SV and ref <= f.offset < end for f in scan.findings):
            scan.find("nws.ref", "ambiguous", ref)


# --- Obsolete bulletin without an identifier (section 9) ----------------


def obsolete_accepts(line, start, end):
    """Whether line[start:end] is a bulletin without its ':' identifier: one of
    the three bulletin addressees, then ':' (amb.bln.obsolete)."""
    return (
        end - start >= 10 and line.startswith(b"BLN", start) and line[start + 9] == 0x3A and _bln_fits(line, start + 3, start + 9)
    )


def obsolete(scan, start, end, depth):
    """bln.obsolete: one token over the field, read inside as a bulletin."""
    scan.tok("bln.obsolete", start, end, depth)
    scan.find("bln.obsolete", "obsolete", start)
    # The bulletin is read one level below, as if its ':' identifier stood
    # before start.
    _bln_addr(scan, start - 1, end, depth + 1)
    scan.tok("msg.sep", start + 9, start + 10, depth + 1)
    _bln_text(scan, start + 10, end, depth + 1)
