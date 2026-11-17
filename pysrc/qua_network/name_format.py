# SPDX-License-Identifier: Apache-2.0
"""The name (docs/spec/13-strings.md section 4): a string of 12 characters
at most as one number in base 37, with the digit table of the callsign.

This follows the draft, including its [proposed] rules. This module is a
research aid for checking vectors, not a reference implementation.
"""

from qua_network.identifier import ALPHABET, BASE, LIMIT

LENGTH = 12


class NameFormatError(ValueError):
    """The text or the value is not a name."""


def encode(text):
    """The value of a name."""
    if not 1 <= len(text) <= LENGTH:
        raise NameFormatError("the name does not have 1 to 12 characters")
    if text[0] == "/":
        raise NameFormatError("the name begins with /")
    value = 0
    for c in text:
        digit = ALPHABET.find(c)
        if digit < 0:
            raise NameFormatError("the name has a character outside 0-9 A-Z /")
        value = value * BASE + digit
    return value


def decode(value):
    """The characters of the name with this value."""
    if value == 0:
        raise NameFormatError("the value is 0")
    if not 0 < value < LIMIT:
        raise NameFormatError("the value is 37^12 or more")
    text = ""
    while value:
        value, digit = divmod(value, BASE)
        text = ALPHABET[digit] + text
    return text
