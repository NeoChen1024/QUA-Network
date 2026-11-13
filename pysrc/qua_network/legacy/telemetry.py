# SPDX-License-Identifier: Apache-2.0
"""Telemetry reports, base-91 comment telemetry and the text of the
telemetry definition messages: docs/legacy/07-telemetry.md."""

import re

from qua_network.legacy.model import Scan

_DIGITS = frozenset(b"0123456789")
_BITS = frozenset(b"01")
_ALNUM = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
_SV = ("syntax", "value")

# --- Base-91 comment telemetry (07 section 3) ---------------------------

# A run between two bars; base-91 digits exclude '|', so runs are delimited
# by consecutive bars. The lookahead finds runs that share a bar.
_RUN = re.compile(rb"(?=\|([!-{]*)\|)")


def b91_span(line, s, e, daos):
    """(start, end) of the tlm.b91 block of the comment line[s:e], or None.

    daos are the cmt.dao candidates of the comment, as (offset, kind). A
    run is a block only when nothing follows it but an optional DAO
    candidate (amb.tlm.b91.order)."""
    dao_at = {i for i, _ in daos}
    for m in _RUN.finditer(line, s, e):
        n = len(m.group(1))
        if n % 2 or not 4 <= n <= 14:
            continue
        bs = m.start()
        be = bs + n + 2
        if be == e or (be + 5 == e and be in dao_at):
            return bs, be
    return None


def b91_block(scan, s, e, depth, daos, span=None):
    """Tokenize the tlm.b91 block of the comment line[s:e], if there is one.

    span is the block's extent when the caller has already found it with
    b91_span. Returns (start, end) of the block or None."""
    if span is None:
        span = b91_span(scan.line, s, e, daos)
    if span is None:
        return None
    bs, be = span
    scan.tok("tlm.b91", bs, be, depth)
    d = depth + 1
    for k in range((be - bs - 2) // 2):
        rule = "tlm.b91.seq" if k == 0 else "tlm.b91.bits" if k == 6 else "tlm.b91.analog"
        p = bs + 1 + 2 * k
        scan.tok(rule, p, p + 2, d)
    return span


# --- Numbers (tlm.analog, tlm.eqns.coef) --------------------------------


def _number_bad(line, p, q):
    """Where line[p:q] stops being a relaxed number (amb.tlm.value): an
    optional '-', then digits, digits '.' digits, or '.' digits. Returns
    None when it is one, else the offset of the first byte that fails, q
    when a byte is missing at the end."""
    i = p + 1 if p < q and line[p] == 0x2D else p
    j = i
    while j < q and line[j] in _DIGITS:
        j += 1
    if j < q and line[j] == 0x2E:
        k = j + 1
        while k < q and line[k] in _DIGITS:
            k += 1
        return k if k == j + 1 or k < q else None
    if j == i or j < q:
        return j
    return None


# --- Telemetry report (07 section 2) ------------------------------------


def read(scan, start, end, depth):
    """A 'T' field; start is the identifier byte, whose token is emitted."""
    # fields imports this module for b91_block, so it is imported here.
    from qua_network.legacy.fields import noarchive_outside

    texts = []
    n0 = len(scan.findings)
    mic_bare = _report(scan, start, end, depth, texts)
    if mic_bare:
        mine = {(f.kind, f.offset) for f in scan.findings[n0:] if f.kind in _SV}
        _seq_other(scan, start, end, depth, mine)
    noarchive_outside(scan, start, end, texts)


def _report(scan, start, end, depth, texts, alnum_seq=False):
    """The fields after the identifier. alnum_seq=True reads the sequence as
    reading (c) of amb.tlm.seq does: '#', letters or digits, ','. Returns
    True when the sequence is MIC with no ',' after it."""
    line = scan.line
    p = start + 1
    mic_bare = False
    if alnum_seq:
        p = _seq_alnum(scan, p, end)
    elif line.startswith(b"#MIC", p, end):
        q = p + 4
        if q < end and line[q] == 0x2C:
            q += 1
        else:
            mic_bare = True
        scan.tok("tlm.seq", p, q, depth)
        p = q
    else:
        p = _seq_digits(scan, p, end, depth)
    if p is None:
        return mic_bare

    for _ in range(5):
        if p >= end:
            # The report ends early: one finding, at the first missing field.
            scan.find("tlm.analog", "syntax", p)
            return mic_bare
        c = line.find(b",", p, end)
        q = end if c < 0 else c
        scan.tok("tlm.analog", p, end if c < 0 else c + 1, depth)
        strict = q - p == 3 and all(x in _DIGITS for x in line[p:q])
        bad = None if strict else _number_bad(line, p, q)
        if bad is None and c < 0:
            # A value up to the end of the field: its ',' is missing.
            bad = end
        if bad is not None:
            scan.find("tlm.analog", "syntax", bad)
            if c < 0:
                return mic_bare
        # The relaxed number gives no finding: the text describes it
        # (amb.tlm.value).
        p = c + 1

    if p >= end:
        scan.find("tlm.digital", "syntax", p)
        return mic_bare
    e = min(p + 8, end)
    scan.tok("tlm.digital", p, e, depth)
    bad = next((i for i in range(p, e) if line[i] not in _BITS), e if e < p + 8 else None)
    if bad is not None:
        scan.find("tlm.digital", "syntax", bad)
    p += 8
    if p < end:
        # A ',' or SP here is the first byte of the comment, with no finding:
        # no text of the document puts a separator there (amb.tlm.count;
        # README section 3, Separators and padding).
        _comment(scan, p, end, depth)
        texts.append((p, end))
    return mic_bare


def _seq_digits(scan, p, end, depth):
    """tlm.seq as '#', three digits and ',', when it does not start with
    '#MIC'. Returns where the analog values start, or None when the field
    ends inside the sequence."""
    line = scan.line
    if p >= end:
        scan.find("tlm.seq", "syntax", p)
        return None
    c = line.find(b",", p, end)
    run = 0
    q = p
    if line[p] != 0x23:
        bad = p
    else:
        q = p + 1
        while q < end and line[q] in _DIGITS:
            q += 1
        run = q - p - 1
        # The first byte that fits neither '#' and digits nor '#MIC': the
        # later of the two places where the forms stop matching.
        m = p + 1
        while m < end and m < p + 4 and line[m] == b"#MIC"[m - p]:
            m += 1
        bad = None if q == c and run else max(q, m)
    if c < 0:
        if q == end:
            # '#' and digits up to the end of the field: the ',' is missing.
            scan.tok("tlm.seq", p, end, depth)
        else:
            # Nothing delimits the sequence from what follows.
            scan.residue(p, end, depth, "tlm.seq")
        scan.find("tlm.seq", "syntax", bad)
        return None
    scan.tok("tlm.seq", p, c + 1, depth)
    # amb.tlm.seq: a digit run of another length gives value; the ',' fixes
    # the extent of the field. A short run gives it where the first missing
    # digit was expected (README section 3, Placing a finding).
    if run > 3:
        scan.find("tlm.seq", "value", p + 4)
    elif bad is None and run < 3:
        scan.find("tlm.seq", "value", p + 1 + run)
    if bad is not None:
        scan.find("tlm.seq", "syntax", bad)
    return c + 1


def _seq_alnum(scan, p, end):
    """The sequence under reading (c) of amb.tlm.seq: '#', letters or digits,
    ','. Only whether it fails is used."""
    line = scan.line
    c = line.find(b",", p, end)
    if c <= p + 1 or line[p] != 0x23 or any(x not in _ALNUM for x in line[p + 1 : c]):
        scan.find("tlm.seq", "syntax", p)
        return None
    return c + 1


def _seq_other(scan, start, end, depth, mine):
    """amb.tlm.seq: MIC with no ',' after it, which reading (c) runs on to the
    first ','. mine are the syntax and value findings this reading gives in
    the report, as (kind, offset). The finding is given when reading (c)
    gives no such finding of its own, and this reading gives none that
    reading (c) does not give (Precedence): the two readings then differ
    only in how they divide the bytes. A finding is shared when both give
    one of the same kind at the same offset, whatever its rule (README
    section 3). The finding goes on tlm.analog, the rule this reading gives
    offset 5, where the readings first divide the bytes."""
    other = Scan(scan.line)
    _report(other, start, end, depth, [], alnum_seq=True)
    theirs = {(f.kind, f.offset) for f in other.findings if f.kind in _SV}
    if theirs == mine:
        scan.find("tlm.analog", "ambiguous", start + 5)


def _comment(scan, p, end, depth):
    """tlm.cmt, read as cmt.text with no length limit (07 section 2). Of the
    items of 02 section 8.2 only the altitude and '!x!' are looked for: the
    report has no position, so neither a DAO nor the extension-shaped runs
    of 02 amb.ext.count are, and no chapter places a base-91 block or a
    frequency there."""
    from qua_network.legacy.fields import comment

    comment(scan, p, end, depth, float("inf"), "tlm.cmt", b91=False, freq=False, dao=False, ext_search=False)


# --- Telemetry definition messages (07 section 4) -----------------------

KEYWORDS = (b"PARM.", b"UNIT.", b"EQNS.", b"BITS.")
# Keyword -> (list rule, field rule, most fields).
_LISTS = {
    b"PARM.": ("tlm.parm", "tlm.parm.name", 13),
    b"UNIT.": ("tlm.unit", "tlm.unit.label", 13),
    b"EQNS.": ("tlm.eqns", "tlm.eqns.coef", 15),
}
# Longest name, unit or label of A1 to A5 and B1 to B8, the comma not counted.
_NAME_MAX = (7, 6, 5, 5, 4, 5, 4, 3, 3, 3, 2, 2, 2)
_TITLE_MAX = 23


def _bad_text(line, p, q):
    """The first byte of line[p:q] that is not a text byte of 08 section 1,
    or None. Such a byte gives its syntax finding on the field of section 4
    that holds it, the most specific rule, and none on msg.text (README
    section 3, Placing a finding)."""
    # fields imports this module for b91_block, so it is imported here.
    from qua_network.legacy.fields import bad_text_bytes

    bad = bad_text_bytes(line[p:q])
    return p + bad[0] if bad else None


def definition(scan, t0, te, depth, kw=None):
    """The text line[t0:te] of a definition message, inside msg.text; depth
    is one level below msg.text. kw is the keyword to read the text as, by
    default its first five bytes (amb.tlm.keyword reads another case as
    upper case)."""
    line = scan.line
    kw = kw or bytes(line[t0 : t0 + 5])
    if kw == b"BITS.":
        _bits(scan, t0, te, depth)
        return
    rule, item, most = _LISTS[kw]
    scan.tok(rule, t0, te, depth)
    p = t0 + 5
    if p >= te:
        # amb.tlm.meta: the earliest stopping point of the list is not stated.
        scan.find(rule, "unstated", p)
        return
    d = depth + 1
    k, a = 0, p
    while True:
        c = line.find(b",", a + (k > 0), te)
        b = te if c < 0 else c
        body = a + (k > 0)
        if b > a:
            scan.tok(item, a, b, d)
        if k == most:
            # One finding for the list, at the comma of the first extra field.
            scan.find(item, "syntax", a)
        elif k > most:
            # A field after the first extra one keeps its token and the byte
            # rule of the fields.
            bad = _bad_text(line, body, b)
            if bad is not None:
                scan.find(item, "syntax", bad)
        elif kw == b"EQNS.":
            # The relaxed number's bytes lie inside the text bytes.
            bad = _number_bad(line, body, b)
            if bad is not None:
                scan.find(item, "syntax", bad)
        else:
            bad = _bad_text(line, body, b)
            if bad is not None:
                scan.find(item, "syntax", bad)
            if k == 0 and b == body:
                # A1 holds at least one byte and a ',' follows here: an empty
                # required field is missing (README section 3, Kinds by
                # situation).
                scan.find(item, "syntax", body)
            elif b - body > _NAME_MAX[k]:
                scan.find(item, "value", body + _NAME_MAX[k])
        if c < 0:
            break
        k, a = k + 1, c
    if kw == b"EQNS." and k < most and (k + 1) % 3:
        # A list that stops inside a channel's three coefficients has too few
        # fields: the next coefficient was expected at the end.
        scan.find(item, "syntax", te)


def _bits(scan, t0, te, depth):
    line = scan.line
    scan.tok("tlm.bits", t0, te, depth)
    d = depth + 1
    p = t0 + 5
    if p >= te:
        scan.find("tlm.bits.sense", "syntax", p)
        return
    e = min(p + 8, te)
    scan.tok("tlm.bits.sense", p, e, d)
    bad = next((i for i in range(p, e) if line[i] not in _BITS), e if e < p + 8 else None)
    if bad is not None:
        scan.find("tlm.bits.sense", "syntax", bad)
    q = p + 8
    if q >= te:
        return
    scan.tok("tlm.bits.title", q, te, d)
    bad = _bad_text(line, q, te)
    if bad is not None:
        scan.find("tlm.bits.title", "syntax", bad)
    if te - q > _TITLE_MAX:
        scan.find("tlm.bits.title", "value", q + _TITLE_MAX)
    elif line[q] == 0x2C:
        # amb.tlm.bitsep: readings (b) and (c) take the ',' as a separator.
        scan.find("tlm.bits.title", "ambiguous", q)


def keyword_case(scan, t0, te, depth):
    """amb.tlm.keyword for message text line[t0:te] that starts with a
    keyword in another case: whether reading (b), which takes it as that
    definition message, gives no syntax or value finding of its own."""
    head = bytes(scan.line[t0 : t0 + 5])
    kw = head.upper()
    if te - t0 < 5 or kw not in KEYWORDS or head == kw:
        return False
    other = Scan(scan.line)
    definition(other, t0, te, depth, kw)
    # A finding of reading (b) is shared when this reading gives one of the
    # same kind at the same offset, whatever its rule (README section 3).
    mine = {(f.kind, f.offset) for f in scan.findings if f.kind in _SV}
    return all((f.kind, f.offset) in mine for f in other.findings if f.kind in _SV)
