# SPDX-License-Identifier: Apache-2.0
"""The TLV area of docs/spec/03-tlv.md: read it into TLVs, and write TLVs
as an area.

This follows the draft, including its [proposed] rules. The meaning of
D = 14 is open, so this module rejects it. This module is a research aid
for checking vectors, not a reference implementation.
"""

SHORT = 13  # D or L from this value has an extension byte
LENGTH_EXTENSION = 242  # the largest extension byte of a length


class TlvError(ValueError):
    """The bytes are not a valid TLV area."""


def read(area):
    """The TLVs of the area, in their order, each as (tag, value)."""
    out = []
    tag, i = 0, 0
    while i < len(area):
        d, n = area[i] >> 4, area[i] & 15
        i += 1
        if d > SHORT:
            raise TlvError("D is 15" if d == 15 else "the meaning of D = 14 is open")
        if n > SHORT:
            raise TlvError("L is 14 or 15")
        if d == SHORT:
            if i >= len(area):
                raise TlvError("the extension byte of the delta is beyond the end of the area")
            d += area[i]
            i += 1
        if n == SHORT:
            if i >= len(area):
                raise TlvError("the extension byte of the length is beyond the end of the area")
            if area[i] > LENGTH_EXTENSION:
                raise TlvError("the extension byte of the length is above 242")
            n += area[i]
            i += 1
        if i + n > len(area):
            raise TlvError("the value extends beyond the end of the area")
        tag += d
        out.append((tag, bytes(area[i : i + n])))
        i += n
    return out


def write(tlvs):
    """The area of the TLVs, each (tag, value). The tags do not decrease."""
    out = bytearray()
    before = 0
    for tag, value in tlvs:
        d, n = tag - before, len(value)
        if not 0 <= d <= SHORT + 255:
            raise TlvError("the delta has no encoding")
        if n > SHORT + LENGTH_EXTENSION:
            raise TlvError("the value has more than 255 bytes")
        out.append((min(d, SHORT) << 4) | min(n, SHORT))
        if d >= SHORT:
            out.append(d - SHORT)
        if n >= SHORT:
            out.append(n - SHORT)
        out += value
        before = tag
    return bytes(out)
