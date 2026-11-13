# SPDX-License-Identifier: Apache-2.0
"""Status reports, station capabilities, general and directed queries,
user-defined data, invalid or test data, and the frequency specification
found at the start of a comment or of status text: docs/legacy/09-other.md.

frame.py has emitted the identifier token before read() is called. The
frequency reader (section 7) is called by the readers of 03, 04 and 05
through fields.comment() and the Mic-E free text; the directed query
(section 4.1) by the reader of 08.
"""

import re

from qua_network.legacy.fields import (
    DIGITS,
    LOWER,
    SP,
    SYM_TABLE,
    UPPER,
    bad_text_bytes,
    noarchive_in,
    noarchive_outside,
    sym_code,
    sym_table,
    timestamp7,
)
from qua_network.legacy.model import Scan

_SV = ("syntax", "value")


def _reported(scan, lo, hi):
    """Whether the reading already gives a syntax or value finding on
    line[lo:hi] (README section 3, precedence)."""
    return any(f.kind in _SV and lo <= f.offset < hi for f in scan.findings)


def read(scan, start, end, depth):
    """Dispatch a 09-other field by its identifier byte."""
    c = scan.line[start]
    texts = []
    if c == 0x3E:
        _status(scan, start, end, depth, texts)
    elif c == 0x3C:
        _capabilities(scan, start, end, depth)
    elif c == 0x3F:
        _query(scan, start, end, depth)
    elif c == 0x7B:
        _user(scan, start, end, depth)
    else:
        if start + 1 < end:
            scan.tok("inv.data", start + 1, end, depth)
    noarchive_outside(scan, start, end, texts)


# --- Status reports (09 section 2) --------------------------------------

_LETTERS = UPPER | LOWER
_AR_ANY = frozenset(b"ABCDEFGHIJKLMNOPQRabcdefghijklmnopqr")
_AR = frozenset(b"ABCDEFGHIJKLMNOPQR")
_AX = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWX")
_AX_ANY = _AX | frozenset(b"abcdefghijklmnopqrstuvwx")
_HEADING = DIGITS | UPPER


def _status(scan, start, end, depth, texts):
    line = scan.line
    p = start + 1
    limit, grid = 62, False
    if end - p >= 7 and all(c in DIGITS for c in line[p : p + 6]) and line[p + 6] == 0x7A:
        # stat.time: DHM zulu only.
        timestamp7(scan, p, end, depth)
        p, limit = p + 7, 55
    else:
        n = _grid_len(line, p, end)
        if n:
            _grid(scan, p, n, depth)
            p, limit, grid = p + n + 2, 54, True
    if p < end:
        _stat_text(scan, p, end, depth, limit, grid)
        texts.append((p, end))
    if p == start + 1:
        _time_other(scan, start, end, depth)


def _grid_len(line, p, end):
    """The length of the locator of a stat.grid at p (6, then 4), or 0.

    A locator letter is recognised in either case. Letters outside A-R in
    the first pair, or A-X in the subsquare, are not a locator: the bytes
    are status text (README section 3, amb.stat.grid)."""
    for n in (6, 4):
        q = p + n
        if q + 2 > end:
            continue
        b = line[p:q]
        if not (b[0] in _AR_ANY and b[1] in _AR_ANY and b[2] in DIGITS and b[3] in DIGITS):
            return 0
        if n == 6 and not (b[4] in _AX_ANY and b[5] in _AX_ANY):
            continue
        if line[q] not in SYM_TABLE or not 0x21 <= line[q + 1] <= 0x7E:
            continue
        if q + 2 < end and line[q + 2] != SP:
            continue
        return n
    return 0


def _grid(scan, p, n, depth):
    line = scan.line
    scan.tok("stat.grid", p, p + n + 2, depth)
    d = depth + 1
    scan.tok("grid.loc", p, p + n, d)
    ranges = (_AR, _AR, DIGITS, DIGITS, _AX, _AX)
    bad = next((p + i for i in range(n) if line[p + i] not in ranges[i]), None)
    if bad is not None:
        # Lower case (amb.grid.case), on the most specific rule that holds
        # the letter (README section 3, Placing a finding).
        scan.find("grid.loc", "syntax", bad)
    sym_table(scan, p + n, d)
    sym_code(scan, p + n + 1, d)


def _stat_text(scan, s, end, depth, limit, grid):
    """stat.text from s, with the items found in it one level deeper."""
    line = scan.line
    scan.tok("stat.text", s, end, depth)
    # One syntax finding, at the first byte outside the set (README section
    # 3, Placing a finding).
    bad = bad_text_bytes(line[s:end])
    if bad:
        scan.find("stat.text", "syntax", s + bad[0])
    if end - s > limit:
        scan.find("stat.text", "value", s + limit)
    d = depth + 1
    noarchive_in(scan, s, end, d)
    if end - s >= 3 and line[end - 3] == 0x5E and line[end - 2] in _HEADING and 0x31 <= line[end - 1] <= 0x4B:
        scan.tok("stat.beam", end - 3, end, d)
    # stat.freq: after the SP that follows a locator.
    f0 = s + 1 if grid else s
    if f0 < end:
        frequency(scan, f0, end, d)


def _time_other(scan, start, end, depth):
    """amb.stat.time: six digits and '/' or 'h', which reading (b) takes as a
    timestamp. The finding is given where that timestamp has no syntax or
    value finding and the text after it, read as stat.text after a
    stat.time, gives none of its own. It goes on stat.text, the rule this
    reading gives the bytes (README section 3, Placing a finding)."""
    line = scan.line
    p = start + 1
    if end - p < 7 or line[p + 6] not in b"/h" or not all(c in DIGITS for c in line[p : p + 6]):
        return
    other = Scan(line)
    timestamp7(other, p, end, depth)
    if any(f.kind in _SV for f in other.findings):
        return
    if p + 7 < end:
        _stat_text(other, p + 7, end, depth, 55, False)
    mine = {(f.kind, f.offset) for f in scan.findings if f.kind in _SV}
    if any((f.kind, f.offset) not in mine for f in other.findings if f.kind in _SV):
        return
    scan.find("stat.text", "ambiguous", p)


# --- Station capabilities (09 section 3) --------------------------------

_COUNTS = (b"MSG_CNT", b"LOC_CNT")


def _capabilities(scan, start, end, depth):
    line = scan.line
    p = start + 1
    while True:
        q = line.find(b",", p, end)
        e = end if q < 0 else q
        _cap_item(scan, p, e, depth)
        if q < 0:
            return
        scan.tok("cap.sep", q, q + 1, depth)
        p = q + 1


def _cap_part(scan, s, e, d):
    """The SP padding around one token or value in line[s:e]; returns the
    span of what lies between, which is empty when there is none."""
    line = scan.line
    a = s
    while a < e and line[a] == SP:
        a += 1
    b = e
    while b > a and line[b - 1] == SP:
        b -= 1
    if a == b:
        return a, b
    # amb.cap.form: reading (b) takes the spaces as padding and divides the
    # bytes as this reading does, so it gives no finding of its own.
    for ps, pe in ((s, a), (b, e)):
        if pe > ps:
            scan.tok("cap.pad", ps, pe, d)
            scan.find("cap.pad", "ambiguous", ps)
    return a, b


def _visible_bad(line, a, b):
    return next((i for i in range(a, b) if not 0x21 <= line[i] <= 0x7E), None)


def _cap_item(scan, s, e, depth):
    line = scan.line
    if all(c == SP for c in line[s:e]):
        # An empty item, or one of spaces only, which holds no token.
        if e > s:
            scan.tok("cap.item", s, e, depth)
        scan.find("cap.item", "syntax", s)
        return
    scan.tok("cap.item", s, e, depth)
    d = depth + 1
    eq = line.find(b"=", s, e)
    te = e if eq < 0 else eq
    if all(c == SP for c in line[s:te]):
        scan.find("cap.token", "syntax", s)
        token = None
    else:
        a, b = _cap_part(scan, s, te, d)
        scan.tok("cap.token", a, b, d)
        bad = _visible_bad(line, a, b)
        if bad is not None:
            scan.find("cap.token", "syntax", bad)
        token = line[a:b]
    if eq < 0:
        return
    if all(c == SP for c in line[eq + 1 : e]):
        scan.find("cap.value", "syntax", eq + 1)
        return
    a, b = _cap_part(scan, eq + 1, e, d)
    scan.tok("cap.value", a, b, d)
    if token in _COUNTS:
        # A count's set is the digits, which lie inside the visible bytes.
        bad = next((i for i in range(a, b) if line[i] not in DIGITS), None)
    else:
        bad = _visible_bad(line, a, b)
    if bad is not None:
        scan.find("cap.value", "syntax", bad)


# --- General queries (09 section 4) -------------------------------------

_GENERAL = frozenset((b"APRS", b"IGATE", b"WX"))
_DIRECTED = frozenset((b"APRSD", b"APRSH", b"APRSM", b"APRSO", b"APRSP", b"APRSS", b"APRST", b"PING"))
# The start of a footprint: a latitude number, with or without its sign.
_NUM = re.compile(rb"[ +-]?[0-9]+(?:\.[0-9]+)?")


def _query(scan, start, end, depth):
    line = scan.line
    p = start + 1
    q = line.find(b"?", p, end)
    if q < 0:
        # No closing mark: the type is the run of letters, possibly none,
        # and qry.end is missing where that run ends.
        q = p
        while q < end and line[q] in _LETTERS:
            q += 1
    if q > p:
        scan.tok("qry.type", p, q, depth)
        t = line[p:q]
        bad = next((p + i for i, c in enumerate(t) if c not in UPPER), None)
        if bad is not None:
            scan.find("qry.type", "syntax", bad)
        elif t in _DIRECTED:
            scan.find("qry.type", "value", p)
        elif t not in _GENERAL:
            scan.find("qry.type", "unstated", p)
    else:
        scan.find("qry.type", "syntax", p)
    if q >= end or line[q] != 0x3F:
        scan.find("qry.end", "syntax", q)
        # Reading goes on where the start of the footprint can be told
        # (README section 3, Output).
        if q < end and _NUM.match(line, q, end):
            _footprint(scan, q, end, depth)
        else:
            scan.residue(q, end, depth, "qry.end")
        return
    scan.tok("qry.end", q, q + 1, depth)
    if q + 1 < end:
        _footprint(scan, q + 1, end, depth)


def _coord(scan, rule, s, e, limit, d):
    """qry.lat or qry.lon over line[s:e], which its ',' delimits: one syntax
    finding at the first failing byte, a missing or '+' sign at s."""
    line = scan.line
    scan.tok(rule, s, e, d)
    n = s + 1 if line[s] in b" -+" else s
    bad = _decimal_bad(line, n, e)
    if n == s or line[s] == 0x2B:
        scan.find(rule, "syntax", s)
    elif bad is not None:
        scan.find(rule, "syntax", bad)
    if bad is None and float(line[n:e]) > limit:
        scan.find(rule, "value", s)


def _decimal_bad(line, n, e):
    """The first byte of line[n:e] that fails 1 or more digits, optionally
    '.' and 1 or more digits, or e where a digit is missing; None if none."""
    k = n
    while k < e and line[k] in DIGITS:
        k += 1
    if k == n or k == e or line[k] != 0x2E:
        return None if k == e and k > n else k
    j = k = k + 1
    while k < e and line[k] in DIGITS:
        k += 1
    return None if e == k > j else k


def _footprint(scan, p, end, depth):
    """qry.fp after qry.end: all or none (amb.qry.fp). The bytes are a
    footprint when they start with a latitude number; otherwise they give
    syntax and are residue. Latitude and longitude run to their ','; the
    radius is 4 bytes."""
    line = scan.line
    if _NUM.match(line, p, end) is None:
        scan.find("qry.fp", "syntax", p)
        scan.residue(p, end, depth, "qry.end")
        return
    d = depth + 1
    i = p
    for rule, limit in (("qry.lat", 90), ("qry.lon", 180)):
        c = line.find(b",", i, end)
        e = end if c < 0 else c
        if e > i:
            _coord(scan, rule, i, e, limit, d)
        else:
            # A part that is missing: syntax on qry.fp where it was expected.
            scan.find("qry.fp", "syntax", i)
        if c < 0:
            # The ',' after it is missing, at the end of the field.
            scan.find("qry.fp", "syntax", end)
            scan.tok("qry.fp", p, end, depth)
            return
        i = c + 1
    e = min(i + 4, end)
    if e == i:
        scan.find("qry.fp", "syntax", i)
    else:
        scan.tok("qry.radius", i, e, d)
        bad = next((j for j in range(i, e) if line[j] not in DIGITS), None)
        if bad is None and e - i < 4:
            bad = e
        if bad is not None:
            scan.find("qry.radius", "syntax", bad)
    scan.tok("qry.fp", p, e, depth)
    if e < end:
        # Bytes after the 4-byte radius, a fifth digit too: qry.fp would end
        # at the end of the field.
        scan.find("qry.fp", "syntax", e)
        scan.residue(e, end, depth, "qry.fp")


# --- Directed queries (09 section 4.1) ----------------------------------

_CALL = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-")


def directed(scan, t0, end, depth):
    """The text of a ':' packet from offset 11 (t0), which 08 has found to
    match the rows of section 4.1; tokens at the level of the addressee."""
    line = scan.line
    scan.tok("qry.dir.mark", t0, t0 + 1, depth)
    scan.tok("qry.dir.type", t0 + 1, t0 + 6, depth)
    p = t0 + 6
    if p + 1 < end and line[p] == SP and line[p + 1] in _CALL:
        scan.tok("qry.dir.sep", p, p + 1, depth)
        p += 1
    c = p
    while c < end and c - p < 9 and line[c] in _CALL:
        c += 1
    if c > p:
        scan.tok("qry.dir.call", p, c, depth)
        if line[t0 + 1 : t0 + 6] != b"APRSH":
            scan.find("qry.dir.call", "unstated", p)
    if c < end:
        # SP to the end of the field; with no heard station, every SP after
        # the type is padding.
        scan.tok("qry.dir.pad", c, end, depth)


# --- User-defined data and invalid or test data (09 sections 5, 6) -----


def _user(scan, start, end, depth):
    line = scan.line
    for rule, p in (("udf.user", start + 1), ("udf.type", start + 2)):
        if p >= end:
            # A field shorter than 3 bytes.
            scan.find(rule, "syntax", p)
            return
        scan.tok(rule, p, p + 1, depth)
        if not 0x21 <= line[p] <= 0x7E:
            scan.find(rule, "unstated", p)
    if start + 3 < end:
        scan.tok("udf.data", start + 3, end, depth)


# --- Frequency specification (09 section 7) -----------------------------

_FREQ = re.compile(rb"[0-9A-O][0-9]{2}\.(?:[0-9]{3}|[0-9]{2} )[Mm][Hh][Zz]")
_GHZ = re.compile(rb"(?:[0-9]{3}| [0-9]{2}|  [0-9])\.[0-9]{3}GHz")
# Items without their leading SP; each is followed by SP or the end of the
# text. Group 1, where present, marks a form that gives unstated. A range of
# three digits is no form the document defines, so it is text (README
# section 3, Kinds by situation).
_RX = re.compile(rb"[0-9]{3}\.[0-9]{3}rx(?= |\Z)")
_TONE = re.compile(rb"(?:[TtCcD][0-9]{3}|Toff|1750|l750|(d[0-9]{3}|toff))(?= |\Z)")
_OFFSET = re.compile(rb"[+-][0-9]{3}(?= |\Z)")
_RANGE = re.compile(rb"[RNSEW][0-9]{2}[mk](?= |\Z)")
_DSTAR = re.compile(rb"D-STAR(?: |>([A-Z0-9 ]{6}) [A-Z])")
_ITEMS = (("freq.tone", _TONE), ("freq.offset", _OFFSET), ("freq.range", _RANGE))


def _freq_at(line, p, e):
    """(rule, offset of a byte of MHz in another case or None) of a
    frequency at p, or None."""
    if _FREQ.match(line, p, e):
        rule = "freq.mhz" if line[p] in DIGITS else "freq.uw"
        u = p + 7
        return rule, next((u + i for i, c in enumerate(b"MHz") if line[u + i] != c), None)
    if _GHZ.match(line, p, e):
        return "freq.ghz", None
    return None


def _dstar(line, p, e):
    """The end of a freq.dstar at p, or None. The repeater name is a
    callsign of upper-case letters and digits padded with SP to 6 bytes."""
    m = _DSTAR.match(line, p, e)
    if m is None:
        return None
    call = m.group(1)
    if call is not None and (call[0] == SP or b" " in call.rstrip(b" ")):
        return None
    return m.end()


def _text_rule(scan, p, d):
    """The rule of the text token, one level above d, that holds offset p:
    the rule this reading gives bytes it leaves as text, on which an
    ambiguous finding goes (README section 3, Placing a finding)."""
    for t in reversed(scan.tokens):
        if t.depth == d - 1 and t.start <= p < t.end:
            return t.rule
    return None


def _item(scan, rule, rx, p, e, sp, d):
    """Tokenize the item of rule at p, with a leading SP when sp; returns
    its end, or None when it does not match."""
    line = scan.line
    q = p + 1 if sp else p
    if sp and not (p < e and line[p] == SP):
        return None
    m = rx.match(line, q, e)
    if m is None:
        return None
    scan.tok(rule, p, m.end(), d)
    if m.lastindex and m.group(1) is not None:
        scan.find(rule, "unstated", q)
    return m.end()


def frequency(scan, s, e, d, named=False):
    """Section 7 at the start of the text line[s:e]; its tokens are at depth d,
    one level below the text. named says that the text is the comment of an
    object or item whose name is freq.objname (freq.obj)."""
    line = scan.line
    f = _freq_at(line, s, e)
    fs = s
    if f is None and s < e and line[s] in b"/ ":
        f = _freq_at(line, s + 1, e)
        fs = s + 1
    if f is not None:
        if fs > s:
            scan.tok("freq.lead", s, fs, d)
        rule, bad = f
        scan.tok(rule, fs, fs + 10, d)
        if bad is not None:
            scan.find(rule, "syntax", bad)  # amb.freq.case
        _items(scan, fs + 10, e, d, True)
        return
    q = _dstar(line, s, e)
    if q is not None:
        scan.tok("freq.dstar", s, q, d)
        return
    if named:
        _items(scan, s, e, d, False)
        return
    # amb.freq.nofreq: reading (b) takes left-justified items in any comment.
    for rule, rx in _ITEMS:
        m = rx.match(line, s, e)
        if m:
            if not _reported(scan, s, m.end()):
                scan.find(_text_rule(scan, s, d), "ambiguous", s)
            return


def _items(scan, p, e, d, after_freq):
    """The items after a frequency, or left-justified (freq.obj) when not
    after_freq, in the order of section 7."""
    line = scan.line
    sp = after_freq  # the first left-justified item has no SP before it
    taken = set()
    order = (("freq.rx", _RX),) if after_freq else ()
    for rule, rx in order + _ITEMS[:2]:
        q = _item(scan, rule, rx, p, e, sp, d)
        if q is not None:
            taken.add(rule)
            p, sp = q, True
    if after_freq and not taken - {"freq.offset"} and p + 1 < e and line[p] == SP:
        # freq.dstar directly after the frequency or its offset.
        q = _dstar(line, p + 1, e)
        if q is not None:
            scan.tok("freq.dstar", p + 1, q, d)
            return
    letters = set()
    while True:
        q = p + 1 if sp else p
        if q < e and line[q] in letters:
            break
        r = _item(scan, "freq.range", _RANGE, p, e, sp, d)
        if r is None:
            break
        letters.add(line[q])
        p, sp = r, True
    # amb.freq.items: a tone or offset left as text because a later item
    # was taken; reading (b), which takes them in any order, gives no
    # finding of its own on them.
    for rule, rx in _ITEMS[:2]:
        if rule in taken:
            continue
        q = p + 1 if sp else p
        if sp and not (p < e and line[p] == SP):
            break
        m = rx.match(line, q, e)
        if m:
            if not _reported(scan, p, m.end()):
                scan.find(_text_rule(scan, p, d), "ambiguous", p)
            break
