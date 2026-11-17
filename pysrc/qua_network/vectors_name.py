# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/name.json, for docs/spec/13-strings.md section 4.

This is the path independent of name_format.py and identifier.py, which
qua-check-vectors checks against the file. It imports neither. It gets the
digit of a character from its code point, and it adds the digits with their
powers of 37. name_format.py takes the digit from the table of identifier.py and
multiplies step by step. This module packs the bytes with struct.
"""

import struct

VALID = """0 Z N0CALL EXAMPLE HT1 DEMO 1/2/3 A/B DEMO/ 24/ 00 0/ Z/Z 0123456789AB CDEFGHIJKLMN OPQRSTUVWXYZ
    AB/CD/EF/GHI Z/////////// ZZZZZZZZZZZ ZZZZZZZZZZZZ""".split()

INVALID_VALUE = (0, 37**12, 37**12 + 1, 1 << 63, (1 << 64) - 1)

INVALID_TEXT = ["", "/", "/A", "ABCDEFGHIJKLM", "demo", "Demo", "1.2.3", "HT-1", "A B", "A_B", " A", "A ", "É", "１"]


def digit(c):
    """The digit of a character: 0 for `/`, 1 to 10 for `0` to `9`, 11 to
    36 for `A` to `Z`."""
    n = ord(c)
    if c == "/":
        return 0
    if 0x30 <= n <= 0x39:
        return n - 0x30 + 1
    if 0x41 <= n <= 0x5A:
        return n - 0x41 + 11
    raise ValueError("not a character of a name")


def value(text):
    if not 1 <= len(text) <= 12 or text[0] == "/":
        raise ValueError("not a name")
    return sum(digit(c) * 37**place for place, c in enumerate(reversed(text)))


def name(text):
    """The 8 bytes of a name."""
    return struct.pack("<Q", value(text))


if value("0") != 1 or value("A/") != 11 * 37 or value("ZZZZZZZZZZZZ") != 37**12 - 1:
    raise AssertionError("the value of a name is wrong")


def vectors():
    out = [{"text": t, "value": f"0x{value(t):016X}", "bytes": name(t).hex().upper()} for t in VALID]
    out += [{"bytes": struct.pack("<Q", v).hex().upper(), "invalid": "value"} for v in INVALID_VALUE]
    for t in INVALID_TEXT:
        try:
            value(t)
        except ValueError:
            out.append({"text": t, "invalid": "text"})
        else:
            raise AssertionError(f"{t!r} is a name")
    return out
