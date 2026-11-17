# SPDX-License-Identifier: Apache-2.0
"""The two forms of a symbol (docs/spec/14-symbol.md): the classic form, one
number of 16 bits, and the Unicode form, one or two code points.

This follows the draft, including its [proposed] rules. This module is a
research aid for checking vectors, not a reference implementation.
"""

from qua_network.identifier import ALPHABET

CODES = 94  # the symbol codes of one table, ASCII 33 to 126
OVERLAYS = 37  # no overlay, then `0` to `9` and `A` to `Z`
LIMIT = CODES + CODES * OVERLAYS


class SymbolError(ValueError):
    """The text, the number, the bytes or the code point is not valid."""


def classic_number(chars):
    """The number of the two characters of a classic symbol: the table or
    the overlay, then the symbol code."""
    if len(chars) != 2:
        raise SymbolError("a classic symbol has two characters")
    table, code = chars[0], ord(chars[1]) - 33
    if not 0 <= code < CODES:
        raise SymbolError("the symbol code is outside ASCII 33 to 126")
    if table == "/":
        return code
    # in the digit table, the digit 0 is `/`: here it is the table `\\`, with no overlay
    overlay = 0 if table == "\\" else ALPHABET.find(table)
    if overlay <= 0 and table != "\\":
        raise SymbolError("the table character is not / \\ 0-9 A-Z")
    return CODES + code * OVERLAYS + overlay


def classic_chars(number):
    """The two characters of a classic symbol with this number."""
    if not 0 <= number < LIMIT:
        raise SymbolError("the number is 3572 or more")
    if number < CODES:
        return "/" + chr(number + 33)
    code, overlay = divmod(number - CODES, OVERLAYS)
    return (ALPHABET[overlay] if overlay else "\\") + chr(code + 33)


def classic_decode(value):
    """The number of the 2 bytes of the classic form."""
    if len(value) != 2:
        raise SymbolError("the classic form does not have 2 bytes")
    number = int.from_bytes(value, "little")
    classic_chars(number)
    return number


def classic_encode(number):
    classic_chars(number)
    return number.to_bytes(2, "little")


def _check(point):
    if point > 0x10FFFF:
        raise SymbolError("the code point is above U+10FFFF")
    if 0xD800 <= point <= 0xDFFF:
        raise SymbolError("the code point is a surrogate")
    if point < 0x20 or 0x7F <= point <= 0x9F:
        raise SymbolError("the code point is a control character")
    if 0xFE00 <= point <= 0xFE0F:
        raise SymbolError("the code point is a variation selector")


def unicode_decode(value):
    """The one or two code points of the bytes of the Unicode form."""
    if len(value) not in (4, 8):
        raise SymbolError("the Unicode form does not have 4 or 8 bytes")
    points = [int.from_bytes(value[i : i + 4], "little") for i in range(0, len(value), 4)]
    for point in points:
        _check(point)
    return points


def unicode_encode(points):
    if len(points) not in (1, 2):
        raise SymbolError("the Unicode form has one or two code points")
    for point in points:
        _check(point)
    return b"".join(point.to_bytes(4, "little") for point in points)
