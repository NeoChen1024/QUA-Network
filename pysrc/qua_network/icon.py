# SPDX-License-Identifier: Apache-2.0
"""Icon colour values and bitmap forms, as drafted in docs/spec/02-icon.md."""

CUBE_LEVELS = (0, 95, 135, 175, 215, 255)


class IconError(ValueError):
    pass


def colour_rgb(value):
    """(r, g, b) for a colour byte from 16 to 255. 0 has no fixed colour and 1 to 15 are invalid."""
    if not 16 <= value <= 255:
        raise IconError("colour value has no fixed RGB")
    if value >= 232:
        grey = 8 + 10 * (value - 232)
        return grey, grey, grey
    r, rest = divmod(value - 16, 36)
    g, b = divmod(rest, 6)
    return CUBE_LEVELS[r], CUBE_LEVELS[g], CUBE_LEVELS[b]


SIZE = 16
PIXELS = SIZE * SIZE
PLAIN_BYTES = PIXELS // 8


def _row_xor(rows):
    """Each row XORed with the row above it."""
    return [rows[0]] + [rows[y] ^ rows[y - 1] for y in range(1, SIZE)]


def _gap_form(plain):
    """The gap form of a 32-byte bitmap, whatever its length."""
    rows = _row_xor([int.from_bytes(plain[2 * y : 2 * y + 2], "big") for y in range(SIZE)])
    t = [(row >> (SIZE - 1 - x)) & 1 for row in rows for x in range(SIZE)]
    out = []
    last = -1
    # The position after the last pixel ends the list, as if a bit were set there.
    for pos in [i for i, bit in enumerate(t) if bit] + [PIXELS]:
        gap = pos - last
        last = pos
        # Elias gamma: one zero for each bit of the gap after the first, then the gap.
        width = gap.bit_length()
        out += [0] * (width - 1) + [(gap >> i) & 1 for i in reversed(range(width))]
    out += [0] * (-len(out) % 8)
    return bytes(sum(bit << (7 - i) for i, bit in enumerate(out[n : n + 8])) for n in range(0, len(out), 8))


def encode_bitmap(plain):
    """The bitmap field for 32 bytes of pixels: the gap form if it is shorter, the pixels themselves if not."""
    if len(plain) != PLAIN_BYTES:
        raise IconError("a bitmap is 32 bytes")
    packed = _gap_form(plain)
    return packed if len(packed) < PLAIN_BYTES else bytes(plain)


def decode_bitmap(field):
    """32 bytes of pixels from a bitmap field. Raises IconError for a field the specification tells a decoder to reject."""
    if len(field) == PLAIN_BYTES:
        # Accepted even where the gap form is shorter.
        return bytes(field)
    if not 1 <= len(field) < PLAIN_BYTES:
        raise IconError("bitmap field length")
    bits = [(byte >> (7 - i)) & 1 for byte in field for i in range(8)]
    pos = 0
    t = [0] * PIXELS
    at = -1
    while True:
        zeros = 0
        while pos < len(bits) and bits[pos] == 0:
            zeros += 1
            pos += 1
        if pos + zeros >= len(bits):
            raise IconError("field ends inside the gaps")
        gap = 0
        for bit in bits[pos : pos + zeros + 1]:
            gap = gap << 1 | bit
        pos += zeros + 1
        at += gap
        if at > PIXELS:
            raise IconError("gaps pass the end of the bitmap")
        if at == PIXELS:
            break
        t[at] = 1
    if len(bits) - pos >= 8 or any(bits[pos:]):
        raise IconError("bits after the last gap")
    rows = [sum(bit << (SIZE - 1 - x) for x, bit in enumerate(t[SIZE * y : SIZE * y + SIZE])) for y in range(SIZE)]
    for y in range(1, SIZE):
        rows[y] ^= rows[y - 1]
    return b"".join(row.to_bytes(2, "big") for row in rows)
