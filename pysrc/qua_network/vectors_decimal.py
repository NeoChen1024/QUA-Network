# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/decimal-number.json, for docs/spec/05-decimal-number.md.

This is the path independent of decimal_number.py, which qua-check-vectors
checks against the file. Neither imports the other. This module gets m and e
from a text with the decimal module, and it packs the bytes with struct;
decimal_number.py uses neither.
"""

import struct
from decimal import Decimal

VALID = """0 9 100 25.3 -12.7 853.4 1013.2 10668.25 3e9 -15e-12 inf -inf
    1 -1 0.12 85000 -0.5 2050
    2047 -2048 2048 -2049 524287 -524288 524288 -524289 8388607 -8388608
    0.00000001 10000000 1e8 1e-9 -1e8 20470000000 0.00002047 5.24287 83886.07
    8388607e127 -8388608e-128 8388607e-128 83886070000000 -0.08388608""".split()

# (bytes, the first case of section 6 that applies, the field allows an infinity)
INVALID = (
    [(b, 1, True) for b in ("", "00", "0100000000")]
    + [(b, 2, True) for b in ("0A10", "E80300", "0A000009", "F6FF")]
    + [(b, 3, True) for b in ("0010", "00F0", "000000", "00000000", "00000007", "000070")]
    + [(b, 4, True) for b in ("090000", "09000000", "FDFF0F", "00080000", "FDFFFFFF")]
    + [(b, 5, False) for b in ("0070", "0080")]
)

INVALID_TEXT = ["", "+1", "01", "00", "1.0", "0.0", "-0", "-0.0", ".5", "5.", "1e2", "0e9", "10e9", "3E9", "1e+9", "3e09"]
INVALID_TEXT += ["Inf", "+inf", "infinity", "nan", "0.123456789", "100000000", "8388608", "123456789", "8388608e9", "1e128"]
INVALID_TEXT += ["1e-129", "1 ", " 1", "1,5", "0x10", "1.5e9"]


def pair(text):
    """m and e of a text form."""
    if text == "inf":
        return 0, 7
    if text == "-inf":
        return 0, -8
    d = Decimal(text)
    if d == 0:
        return 0, 0
    sign, digits, exponent = d.normalize().as_tuple()
    m = int("".join(map(str, digits)))
    return (-m if sign else m), exponent


def pack(m, e):
    """The bytes of m and e in the shortest format."""
    if -8 <= e <= 7 and -2048 <= m <= 2047:
        return struct.pack("<H", ((e % 16) << 12) | (m % 4096))
    if -8 <= e <= 7 and -524288 <= m <= 524287:
        return struct.pack("<I", ((e % 16) << 20) | (m % (1 << 20)))[:3]
    if -128 <= e <= 127 and -8388608 <= m <= 8388607:
        return struct.pack("<I", ((e % 256) << 24) | (m % (1 << 24)))
    raise ValueError(f"no format holds {m}e{e}")


def vectors():
    out = []
    for text in VALID:
        m, e = pair(text)
        out.append({"text": text, "m": m, "e": e, "bytes": pack(m, e).hex().upper()})
    for data, case, infinity in INVALID:
        v = {"bytes": data, "invalid": case}
        if not infinity:
            v["infinity"] = False
        out.append(v)
    out.extend({"text": text, "invalid": "text"} for text in INVALID_TEXT)
    return out
