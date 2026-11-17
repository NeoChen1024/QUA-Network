# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/symbol.json, for docs/spec/14-symbol.md.

This is the path independent of symbol.py and identifier.py, which
qua-check-vectors checks against the file. It imports neither. It gets the
overlay digit from the code point of the table character, and it packs the
integers with struct. It takes the code points of a text from Python.
"""

import struct

CLASSIC = ["/!", "/>", "/-", "/_", "/~", "\\!", "\\k", "\\~", "0!", "0-", "9#", "A!", "L#", "Z~", "D&", "W_"]

INVALID_CLASSIC = [
    (3572, "the first number that is not valid"),
    (3573, "a larger number"),
    (65535, "the largest number of 16 bits"),
]

# (the characters, a note); a variation selector is never part of the field
UNICODE = [
    ("\U0001f697", "one emoji: U+1F697, automobile"),
    ("☀", "one code point of the basic plane: U+2600, sun; the receiver draws it with the emoji presentation"),
    ("✈", "U+2708, airplane"),
    ("\U0001f44b\U0001f3fd", "an emoji and a skin-tone modifier"),
    ("\U0001f1f9\U0001f1fc", "a flag: two regional indicators"),
    ("\U0001f1ef\U0001f1f5", "a flag: two regional indicators"),
    ("1⃣", "a keycap: a digit and U+20E3"),
    ("#⃣", "a keycap: # and U+20E3"),
    ("A", "one letter"),
    ("WX", "a label of two letters"),
    ("氣象", "a label of two CJK characters"),
    (" ", "U+0020, the smallest valid code point"),
    ("~", "U+007E, the code point before the control characters"),
    (" ", "U+00A0, the code point after the control characters"),
    ("퟿", "U+D7FF, the code point before the surrogates"),
    ("", "U+E000, the code point after the surrogates"),
    ("﷿", "U+FDFF, the code point before the variation selectors"),
    ("︐", "U+FE10, the code point after the variation selectors"),
    ("\U0010ffff", "U+10FFFF, the largest code point"),
    ("‍", "U+200D, the joiner, is valid: the protocol does not interpret a code point"),
    ("\U0001f697\U0001f697", "one code point two times"),
]

# (the code points, a note)
INVALID_UNICODE = [
    ((0x110000,), "above U+10FFFF"),
    ((0xFFFFFFFF,), "the largest number of 32 bits"),
    ((0xD800,), "the first surrogate"),
    ((0xDFFF,), "the last surrogate"),
    ((0x0000,), "the control character U+0000"),
    ((0x001F,), "the control character U+001F"),
    ((0x007F,), "the control character U+007F"),
    ((0x009F,), "the control character U+009F"),
    ((0xFE00,), "the first variation selector"),
    ((0xFE0E,), "the variation selector of the text presentation"),
    ((0xFE0F,), "the variation selector of the emoji presentation"),
    ((0x2600, 0xFE0F), "an emoji and the variation selector U+FE0F"),
    ((0x1F697, 0x0000), "the second code point is U+0000: a symbol of one code point has 4 bytes"),
    ((0xFE0F, 0x1F697), "the first code point is a variation selector"),
    ((0x1F697, 0x110000), "the second code point is above U+10FFFF"),
]

INVALID_LENGTH = ["", "97", "97F1", "97F101", "97F1010000", "97F1010097F101", "97F1010097F1010000", "97F1010097F1010097F10100"]


def classic(chars):
    """The number of a classic symbol."""
    table, code = chars[0], ord(chars[1]) - 33
    if table == "/":
        return code
    n = ord(table)
    if table == "\\":
        overlay = 0
    elif 0x30 <= n <= 0x39:
        overlay = n - 0x30 + 1
    else:
        overlay = n - 0x41 + 11
    return 94 + code * 37 + overlay


if (classic("/!"), classic("/~"), classic("\\!"), classic("0-"), classic("Z~")) != (0, 93, 94, 539, 3571):
    raise AssertionError("the number of a classic symbol is wrong")


def classic_bytes(number):
    return struct.pack("<H", number)


def unicode_bytes(points):
    return b"".join(struct.pack("<I", p) for p in points)


def points_of(text):
    """The code points of a text. A surrogate in the text is a mistake."""
    return [int.from_bytes(text.encode("utf-32-le", "surrogatepass")[i : i + 4], "little") for i in range(0, 4 * len(text), 4)]


def vectors():
    out = []
    for chars in CLASSIC:
        out.append(
            {"form": "classic", "chars": chars, "number": classic(chars), "bytes": classic_bytes(classic(chars)).hex().upper()}
        )
    for number, note in INVALID_CLASSIC:
        out.append({"form": "classic", "bytes": classic_bytes(number).hex().upper(), "invalid": "number", "note": note})
    for b in ("", "0C", "0C0000"):
        out.append({"form": "classic", "bytes": b, "invalid": "length", "note": f"{len(b) // 2} bytes"})
    for text, note in UNICODE:
        points = points_of(text)
        out.append(
            {"form": "unicode", "points": [f"{p:04X}" for p in points], "bytes": unicode_bytes(points).hex().upper(), "note": note}
        )
    for points, note in INVALID_UNICODE:
        out.append({"form": "unicode", "bytes": unicode_bytes(points).hex().upper(), "invalid": "code point", "note": note})
    for b in INVALID_LENGTH:
        out.append({"form": "unicode", "bytes": b, "invalid": "length", "note": f"{len(b) // 2} bytes"})
    return out
