# SPDX-License-Identifier: Apache-2.0
"""Telemetry reports, base-91 comment telemetry and the text of the
telemetry definition messages: docs/legacy/07-telemetry.md."""

import re

_DIGITS = frozenset(b"0123456789")
_BITS = frozenset(b"01")

# --- Base-91 comment telemetry (07 section 3) ---------------------------

# A run between two bars. The bars delimit the block (p. 88/68), so its digits
# are those of b91.digit other than '|'. The lookahead finds runs that share
# a bar.
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
    b91_span; daos are the DAO candidates outside it. A block followed by a
    DAO candidate while others stand elsewhere is a block only under the
    reading that keeps that candidate (amb.tlm.b91.order). Returns (start,
    end) of the block or None."""
    if span is None:
        span = b91_span(scan.line, s, e, daos)
    if span is None:
        return None
    bs, be = span
    scan.tok("tlm.b91", bs, be, depth)
    if be < e and len(daos) > 1:
        scan.find("tlm.b91", "ambiguous", bs)
    d = depth + 1
    for k in range((be - bs - 2) // 2):
        rule = "tlm.b91.seq" if k == 0 else "tlm.b91.bits" if k == 6 else "tlm.b91.analog"
        p = bs + 1 + 2 * k
        scan.tok(rule, p, p + 2, d)
    return span


# --- Numbers (tlm.analog, tlm.eqns.coef) --------------------------------


def _number_bad(line, p, q):
    """Where line[p:q] stops being a relaxed number (amb.tlm.value): an
    optional '-', then digits with at most one '.', at least one digit.
    Returns None when it is one, else the offset of the first byte that
    fails, q when a byte is missing at the end."""
    i = p + 1 if p < q and line[p] == 0x2D else p
    j = i
    while j < q and line[j] in _DIGITS:
        j += 1
    if j < q and line[j] == 0x2E:
        k = j + 1
        while k < q and line[k] in _DIGITS:
            k += 1
        if k < q:
            return k
        return None if k > j + 1 or j > i else q
    if j == i or j < q:
        return j
    return None


# --- Telemetry report (07 section 2) ------------------------------------


def read(scan, start, end, depth):
    """A 'T' field; start is the identifier byte, whose token is emitted."""
    line = scan.line
    p = start + 1
    if line.startswith(b"#MIC", p, end):
        # err.tlm.seq: MIC with or without its ','.
        q = p + 4
        if q < end and line[q] == 0x2C:
            q += 1
        scan.tok("tlm.seq", p, q, depth)
        p = q
    else:
        p = _seq(scan, p, end, depth)
    if p is None:
        return

    for _ in range(5):
        if p >= end:
            # The report ends early: one finding, at the first missing field.
            scan.find("tlm.analog", "syntax", p)
            return
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
                return
        # The relaxed number gives no finding: the text describes it
        # (amb.tlm.value).
        p = c + 1

    if p >= end:
        scan.find("tlm.digital", "syntax", p)
        return
    e = min(p + 8, end)
    scan.tok("tlm.digital", p, e, depth)
    bad = next((i for i in range(p, e) if line[i] not in _BITS), e if e < p + 8 else None)
    if bad is not None:
        scan.find("tlm.digital", "syntax", bad)
    p += 8
    if p < end:
        # A ',' or SP here is the first byte of the comment (p. 34/20).
        _comment(scan, p, end, depth)


def _seq(scan, p, end, depth):
    """tlm.seq as '#', three bytes other than ',', and ',', when it does not
    start with '#MIC'. Returns where the analog values start, or None when
    the field ends inside the sequence."""
    line = scan.line
    if p >= end:
        scan.find("tlm.seq", "syntax", p)
        return None
    c = line.find(b",", p, end)
    if line[p] != 0x23:
        bad = p
    else:
        # The first byte where the fixed width fails: a ',' or the end among
        # the three, or no ',' after them.
        bad = next((i for i in range(p + 1, p + 4) if i >= end or line[i] == 0x2C), None)
        if bad is None and (p + 4 >= end or line[p + 4] != 0x2C):
            bad = min(p + 4, end)
    if c < 0:
        if line[p] == 0x23 and end - p <= 4:
            # A sequence cut short by the end of the field.
            scan.tok("tlm.seq", p, end, depth)
        else:
            # Nothing delimits the sequence from what follows.
            scan.residue(p, end, depth, "tlm.seq")
        scan.find("tlm.seq", "syntax", bad)
        return None
    scan.tok("tlm.seq", p, c + 1, depth)
    if bad is not None:
        scan.find("tlm.seq", "syntax", bad)
    elif not line[p + 1 : p + 4].isdigit():
        # amb.tlm.seq: a value outside the typical forms.
        scan.find("tlm.seq", "unstated", p + 1)
    return c + 1


def _comment(scan, p, end, depth):
    """tlm.cmt, read as cmt.text with no length limit (07 section 2). The
    report has no position, so no DAO, data extension, base-91 block or
    frequency is looked for."""
    from qua_network.legacy.fields import comment

    comment(scan, p, end, depth, float("inf"), "tlm.cmt", b91=False, freq=False, dao=False)


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
# The message text limit of 08-message.
_TEXT_MAX = 67


def _bad_text(line, p, q):
    """The first byte of line[p:q] that is not a message text byte (08), or
    None. Its syntax finding is on the field of section 4 that holds it, the
    most specific rule, and not on msg.text."""
    # fields imports this module for b91_block, so it is imported here.
    from qua_network.legacy.fields import bad_text_bytes

    bad = bad_text_bytes(line[p:q])
    return p + bad[0] if bad else None


def definition(scan, t0, te, depth):
    """The text line[t0:te] of a definition message, inside msg.text; depth
    is one level below msg.text."""
    line = scan.line
    kw = bytes(line[t0 : t0 + 5])
    if kw == b"BITS.":
        _bits(scan, t0, te, depth)
        return
    rule, item, most = _LISTS[kw]
    scan.tok(rule, t0, te, depth)
    p = t0 + 5
    if p >= te:
        # amb.tlm.meta: a list that stops before its first field.
        return
    d = depth + 1
    k, a = 0, p
    within = True
    while True:
        c = line.find(b",", a + (k > 0), te)
        b = te if c < 0 else c
        body = a + (k > 0)
        if b > a:
            scan.tok(item, a, b, d)
        if k == most:
            # One finding for the list, at the comma of the first extra field.
            scan.find(item, "syntax", a)
            within = False
            k, a = k + 1, c
            if c < 0:
                break
            continue
        bad = _bad_text(line, body, b)
        if bad is not None:
            scan.find(item, "syntax", bad)
            within = False
        if k < most:
            if kw == b"EQNS.":
                if bad is None and _number_bad(line, body, b) is not None:
                    # amb.tlm.eqns: the notation of a coefficient is not stated.
                    scan.find(item, "unstated", body)
            elif k == 0 and b == body:
                # A1 has 1 to 7 bytes; an empty A1 before a ',' is shorter.
                scan.find(item, "value", body)
                within = False
            elif b - body > _NAME_MAX[k]:
                scan.find(item, "value", body + _NAME_MAX[k])
                within = False
        if c < 0:
            break
        k, a = k + 1, c
    if within and kw != b"EQNS." and te - t0 > _TEXT_MAX:
        # err.tlm.parmlen: the field counts allow one byte more than the
        # message text limit, and bytes within them conform.
        scan.withdraw("value", {t0 + _TEXT_MAX})


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
    if q < te and line[q] == 0x2C:
        # amb.tlm.bitsep: the example's ',' as a separator, the more specific
        # reading; it belongs to no field.
        q += 1
    if q >= te:
        return
    scan.tok("tlm.bits.title", q, te, d)
    bad = _bad_text(line, q, te)
    if bad is not None:
        scan.find("tlm.bits.title", "syntax", bad)
    if te - q > _TITLE_MAX:
        scan.find("tlm.bits.title", "value", q + _TITLE_MAX)
