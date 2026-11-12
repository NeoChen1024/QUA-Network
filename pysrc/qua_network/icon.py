# SPDX-License-Identifier: Apache-2.0
"""Icon colour values, as drafted in docs/spec/02-icon.md."""

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
