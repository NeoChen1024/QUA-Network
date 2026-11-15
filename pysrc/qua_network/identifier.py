# SPDX-License-Identifier: Apache-2.0
"""Station identifier encoding (docs/spec/01-station-identifier.md) and hop hash (docs/spec/09-hop-trace.md).

This follows the drafts, including their [proposed] rejection rules. It is a
research aid for checking vectors and measuring the corpus, not a reference
implementation.
"""

from qua_network.crc import crc32c

ALPHABET = "/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)
LIMIT = BASE**12
F_BIT = 1 << 63


class IdentifierError(ValueError):
    pass


def _digits(text, what):
    try:
        return [ALPHABET.index(c) for c in text]
    except ValueError:
        raise IdentifierError(f"{what} has a character outside 0-9 A-Z /") from None


def _number(digits):
    n = 0
    for d in digits:
        n = n * BASE + d
    return n


def encode(text):
    """Text form (CALLSIGN or CALLSIGN-SSID) to the 64-bit identifier."""
    callsign, dash, ssid = text.partition("-")
    if dash and not ssid:
        raise IdentifierError("empty SSID after dash")
    if not callsign:
        raise IdentifierError("empty callsign")
    if callsign[0] == "/":
        raise IdentifierError("callsign begins with /")
    if "/" in ssid:
        raise IdentifierError("SSID contains /")
    if len(ssid) > 2:
        raise IdentifierError("SSID longer than two characters")
    if ssid == "0":
        raise IdentifierError("one-character SSID 0 is not allowed")
    two = len(ssid) == 2
    if len(callsign) > (10 if two else 11):
        raise IdentifierError("callsign too long for this SSID length")
    call_n = _number(_digits(callsign, "callsign"))
    ssid_n = _number(_digits(ssid, "SSID"))
    if two:
        return F_BIT | (call_n * BASE**2 + ssid_n)
    return call_n * BASE + ssid_n


def decode(value):
    """64-bit identifier to its text form. Rejects every non-canonical value."""
    if not 0 <= value < 1 << 64:
        raise IdentifierError("not a 64-bit value")
    two = bool(value & F_BIT)
    low = value & (F_BIT - 1)
    if low >= LIMIT:
        raise IdentifierError("low 63 bits are 37^12 or above")
    call_n, ssid_n = divmod(low, BASE**2 if two else BASE)
    if call_n == 0:
        raise IdentifierError("callsign part is all zeros")
    callsign = ""
    while call_n:
        call_n, d = divmod(call_n, BASE)
        callsign = ALPHABET[d] + callsign
    if two:
        hi, lo = divmod(ssid_n, BASE)
        if hi == 0 or lo == 0:
            raise IdentifierError("two-character SSID contains a zero digit")
        return f"{callsign}-{ALPHABET[hi]}{ALPHABET[lo]}"
    if ssid_n == 0:
        return callsign
    if ssid_n == 1:
        raise IdentifierError("one-character SSID 0 is not allowed")
    return f"{callsign}-{ALPHABET[ssid_n]}"


def hop_hash(value):
    """24-bit hop trace entry, as a number: the 24 least significant bits of
    CRC-32C over the 8 bytes of the identifier in little-endian order. In a
    PDU it is 3 bytes in little-endian order."""
    return crc32c(value.to_bytes(8, "little")) & 0xFFFFFF
