# SPDX-License-Identifier: Apache-2.0
"""The decimal number of docs/spec/05-decimal-number.md: its bytes and its
text form.

A finite value is the pair (m, e) with the value m * 10**e. The two
infinities are the constants INF and NEG_INF. This module is a research aid
for checking vectors, not a reference implementation.
"""

import re

INF, NEG_INF = "inf", "-inf"

# Section 3: (bytes, bits of e, bits of m), the shortest format first.
FORMATS = ((2, 4, 12), (3, 4, 20), (4, 8, 24))
PLAIN_E = range(-8, 8)  # section 7: the exponents that have a plain text form

_PLAIN = re.compile(r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]{1,8}))?")
_EXPONENT = re.compile(r"(-?[1-9][0-9]*)e(-?[1-9][0-9]*)")


class DecimalError(ValueError):
    """An invalid encoding or text. case is the case of section 6 for an
    encoding, and None for a text or a value."""

    def __init__(self, case, message):
        super().__init__(message)
        self.case = case


def _fits(m, e, e_bits, m_bits):
    return -(1 << (e_bits - 1)) <= e < (1 << (e_bits - 1)) and -(1 << (m_bits - 1)) <= m < (1 << (m_bits - 1))


def _signed(v, bits):
    return v - (1 << bits) if v >> (bits - 1) else v


def decode(data, infinity=True):
    """The value of the bytes. infinity states whether the field allows an
    infinity. The cases of section 6 are checked in their order."""
    for size, e_bits, m_bits in FORMATS:
        if size == len(data):
            break
    else:
        raise DecimalError(1, "not 2, 3 or 4 bytes")
    v = int.from_bytes(data, "little")
    e = _signed(v >> m_bits, e_bits)
    m = _signed(v & ((1 << m_bits) - 1), m_bits)
    if m != 0 and m % 10 == 0:
        raise DecimalError(2, "m is a multiple of 10")
    special = None
    if m == 0:
        special = {(2, 0): (0, 0), (2, 7): INF, (2, -8): NEG_INF}.get((size, e))
        if special is None:
            raise DecimalError(3, "m is 0")
    else:
        for shorter, e_bits, m_bits in FORMATS:
            if shorter < size and _fits(m, e, e_bits, m_bits):
                raise DecimalError(4, "a shorter format holds the value")
    if special in (INF, NEG_INF):
        if not infinity:
            raise DecimalError(5, "the field does not allow an infinity")
        return special
    return (m, e)


def encode(value):
    """The bytes of a value: the shortest format that holds it."""
    if value in (INF, NEG_INF):
        m, e = 0, 7 if value == INF else -8
    else:
        m, e = value
        if m == 0 and e != 0 or m != 0 and m % 10 == 0:
            raise DecimalError(None, "m and e are not the unique pair of the value")
    for size, e_bits, m_bits in FORMATS:
        if _fits(m, e, e_bits, m_bits):
            v = ((e & ((1 << e_bits) - 1)) << m_bits) | (m & ((1 << m_bits) - 1))
            return v.to_bytes(size, "little")
    raise DecimalError(None, "no format holds the value")


def to_text(value):
    """The text form of section 7."""
    if value in (INF, NEG_INF):
        return value
    m, e = value
    if e not in PLAIN_E:
        return f"{m}e{e}"
    if e >= 0:
        return str(m) + "0" * e if m else "0"
    digits = str(abs(m)).rjust(1 - e, "0")
    return ("-" if m < 0 else "") + digits[:e] + "." + digits[e:]


def from_text(text):
    """The value of a text form. Rejects a text that breaks the rules of
    section 7, or whose value has no encoding."""
    if text in (INF, NEG_INF):
        return text
    if match := _EXPONENT.fullmatch(text):
        m, e = int(match[1]), int(match[2])
        if e in PLAIN_E:
            raise DecimalError(None, "the value has a plain form")
        if m % 10 == 0:
            raise DecimalError(None, "m is a multiple of 10")
    elif match := _PLAIN.fullmatch(text):
        sign, whole, fraction = match[1], match[2], match[3] or ""
        if fraction.endswith("0"):
            raise DecimalError(None, "the fraction ends in 0")
        m, e = int(whole + fraction), -len(fraction)
        if m == 0:
            if sign or fraction:
                raise DecimalError(None, "zero has the one text form 0")
            return (0, 0)
        while m % 10 == 0:
            m, e = m // 10, e + 1
        if e not in PLAIN_E:
            raise DecimalError(None, "the value has no plain form")
        if sign:
            m = -m
    else:
        raise DecimalError(None, "not a text form")
    encode((m, e))
    return (m, e)
