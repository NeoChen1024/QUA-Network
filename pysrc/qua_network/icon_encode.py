# SPDX-License-Identifier: Apache-2.0
"""Encode 16 by 16 one-bit pictures as icon bitmap fields, and produce the bitmap vectors.

This is the independent path behind vectors/icon-bitmap.json. It is written
from the text of docs/spec/02-icon.md section 3 and works on strings of '0'
and '1'. It must not import icon.py, which works on integers and is the code
the vectors are used to check; the two share nothing.

Input files may be:

\b
  - PBM, plain (P1) or raw (P4);
  - text of 16 lines of 16 characters, '.', '0', '-' or space for a clear
    pixel and anything else for a set one;
  - 64 hexadecimal digits, the pixels in the plain form;
  - any image file Pillow can read. A pixel is set if it is darker than mid
    grey and not transparent.
"""

import json
import re
from pathlib import Path

import click
from PIL import Image

SIZE = 16
PIXELS = SIZE * SIZE


def gamma(n):
    """Elias gamma code of n >= 1 as a string of bits."""
    binary = format(n, "b")
    return "0" * (len(binary) - 1) + binary


def pad(bits):
    return bits + "0" * (-len(bits) % 8)


def to_hex(bits):
    return "".join(format(int(bits[i : i + 8], 2), "02X") for i in range(0, len(bits), 8))


def gaps(p):
    """Section 3.2 up to and including the gaps, without the padding."""
    t = p[:SIZE] + "".join("1" if p[i] != p[i - SIZE] else "0" for i in range(SIZE, PIXELS))
    # Split after every set bit: each piece but the last is some zeros before a one, so its length plus one is a gap.
    pieces = (t + "1").split("1")[:-1]
    return "".join(gamma(len(piece) + 1) for piece in pieces)


def field(p):
    """The bitmap field for 256 pixels, as hexadecimal: the gap form if it is shorter than the plain form."""
    packed = pad(gaps(p))
    return to_hex(packed) if len(packed) < PIXELS else to_hex(p)


def art(text):
    rows = text.split()
    assert len(rows) == SIZE and all(len(row) == SIZE for row in rows)
    return "".join(rows).replace(".", "0").replace("#", "1")


HOUSE = art(
    """
    ................
    .......##.......
    ......####......
    .....######.....
    ....########....
    ...##########...
    ..############..
    .##############.
    ...##########...
    ...##########...
    ...###..#####...
    ...###..#.#.#...
    ...###..#####...
    ...###..#####...
    ...##########...
    ................
    """
)

ANTENNA = art(
    """
    .......#........
    ..#....#....#...
    .#..#..#..#..#..
    .#.#...#...#.#..
    .#.#..###..#.#..
    .#.#...#...#.#..
    .#..#..#..#..#..
    ..#....#....#...
    .......#........
    ......###.......
    ......#.#.......
    .....##.##......
    .....#...#......
    ....##...##.....
    ....#.....#.....
    ...###...###....
    """
)

# Three of every four pixels set, shifted by one on each row: the row XOR leaves half the bits set.
DENSE = "".join(("1110" * 5)[y % 4 :][:SIZE] for y in range(SIZE))


def noise():
    """256 bits from x -> (25173x + 13849) mod 65536 starting at 1, taking the top bit of each new value."""
    bits = ""
    x = 1
    for _ in range(PIXELS):
        x = (25173 * x + 13849) % 65536
        bits += "1" if x & 32768 else "0"
    return bits


ENCODE = [
    ("empty", "0" * 256),
    ("every pixel set", "1" * 256),
    ("top left pixel only", "1" + "0" * 255),
    ("bottom right pixel only", "0" * 255 + "1"),
    ("horizontal stripes one pixel high; plain form, because the row XOR sets every bit", ("0" * 16 + "1" * 16) * 8),
    ("vertical stripes", "10" * 128),
    ("left half set", ("1" * 8 + "0" * 8) * 16),
    ("horizontal stripes two pixels high", ("0" * 32 + "1" * 32) * 4),
    ("frame one pixel wide", "1" * 16 + ("1" + "0" * 14 + "1") * 14 + "1" * 16),
    ("house", HOUSE),
    ("antenna", ANTENNA),
    ("checkerboard; plain form", ("10" * 8 + "01" * 8) * 8),
    ("every second pixel of every second row; plain form", ("10" * 8 + "0" * 16) * 8),
    ("dense irregular pattern; plain form", DENSE),
    ("noise; plain form", noise()),
]

# A sender does not produce these, and a decoder accepts them.
DECODE_ONLY = [
    ("plain form of the empty bitmap, whose gap form is 3 bytes", "0" * 256),
    ("plain form of the house, whose gap form is shorter", HOUSE),
]

REJECT = [
    ("empty field", ""),
    ("33 bytes", "00" * 33),
    ("field ends before the end of the bitmap: one byte", "00"),
    ("field ends before the end of the bitmap: empty bitmap cut to two bytes", "0080"),
    ("field ends before the end of the bitmap: house cut by one byte", to_hex(pad(gaps(HOUSE))[:-8])),
    ("gaps of 1 and 257 pass the end of the bitmap", to_hex(pad(gamma(1) + gamma(257)))),
    ("gap of 258", to_hex(pad(gamma(258)))),
    ("gap of 512", to_hex(pad(gamma(512)))),
    ("padding bit set", to_hex(pad(gaps("0" * 256))[:-1] + "1")),
    ("a whole byte after the padding", to_hex(pad(gaps("0" * 256))) + "00"),
]


def vectors():
    out = [{"name": name, "pixels": to_hex(p), "field": field(p)} for name, p in ENCODE]
    out += [{"name": name, "pixels": to_hex(p), "field": to_hex(p), "decode_only": True} for name, p in DECODE_ONLY]
    out += [{"name": name, "field": f, "reject": True} for name, f in REJECT]
    by_name = {v["name"]: v["field"] for v in out}
    # Worked by hand: gamma(257); sixteen gaps of 1 then gamma(241); gamma(1), gamma(16), gamma(240).
    assert by_name["empty"] == "008080"
    assert by_name["every pixel set"] == "FFFF01E2"
    assert by_name["top left pixel only"] == "84007800"
    return out


def read_pbm(data):
    """Pixels of a PBM file, or None if the data is not PBM. In PBM a 1 is black, which is a set pixel."""
    if data[:2] not in (b"P1", b"P4"):
        return None
    # Header: magic, width, height, separated by whitespace, with '#' comments to the end of the line.
    tokens = []
    pos = 2
    while len(tokens) < 2:
        match = re.compile(rb"\s*(?:#[^\n]*\n\s*)*(\d+)").match(data, pos)
        if not match:
            raise click.ClickException("malformed PBM header")
        tokens.append(int(match.group(1)))
        pos = match.end()
    if tokens != [SIZE, SIZE]:
        raise click.ClickException(f"picture is {tokens[0]} by {tokens[1]}, not {SIZE} by {SIZE}")
    if data[:2] == b"P1":
        bits = re.sub(rb"#[^\n]*", b"", data[pos:])
        bits = re.sub(rb"\s", b"", bits).decode("ascii", "replace")
    else:
        # One whitespace byte, then rows padded to whole bytes; 16 pixels need no padding.
        bits = "".join(format(byte, "08b") for byte in data[pos + 1 : pos + 1 + PIXELS // 8])
    if len(bits) != PIXELS or set(bits) - {"0", "1"}:
        raise click.ClickException("malformed PBM data")
    return bits


def read_text(data):
    """Pixels of a hexadecimal or drawn text file, or None if the data is neither."""
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        return None
    compact = "".join(text.split())
    if re.fullmatch(r"[0-9A-Fa-f]{64}", compact):
        return format(int(compact, 16), "0256b")
    rows = [line for line in text.splitlines() if line.strip()]
    if len(rows) != SIZE or any(len(row.rstrip("\r")) > SIZE for row in rows):
        return None
    return "".join("".join("0" if c in ".0- " else "1" for c in row.rstrip("\r").ljust(SIZE)) for row in rows)


def read_image(path):
    try:
        image = Image.open(path).convert("RGBA")
    except OSError as e:
        raise click.ClickException(f"{path}: {e}")
    if image.size != (SIZE, SIZE):
        raise click.ClickException(f"{path}: picture is {image.size[0]} by {image.size[1]}, not {SIZE} by {SIZE}")
    grey = image.convert("L").tobytes()
    alpha = image.getchannel("A").tobytes()
    return "".join("1" if a >= 128 and g < 128 else "0" for g, a in zip(grey, alpha))


def read_picture(path):
    data = Path(path).read_bytes()
    pixels = read_pbm(data)
    if pixels is None:
        pixels = read_text(data)
    if pixels is None:
        pixels = read_image(path)
    return pixels


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("picture", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option("--invert", is_flag=True, help="Swap set and clear pixels of every picture before encoding.")
@click.option("--draw", is_flag=True, help="Also draw each picture as text.")
@click.option("--vectors", "emit_vectors", is_flag=True, help="Write the contents of vectors/icon-bitmap.json to stdout.")
def cli(picture, invert, draw, emit_vectors):
    if emit_vectors:
        if picture:
            raise click.UsageError("--vectors takes no pictures")
        click.echo("[\n" + ",\n".join("  " + json.dumps(v) for v in vectors()) + "\n]")
        return
    if not picture:
        raise click.UsageError("give at least one picture, or --vectors")
    for path in picture:
        pixels = read_picture(path)
        if invert:
            pixels = pixels.translate(str.maketrans("01", "10"))
        encoded = field(pixels)
        form = "plain" if len(encoded) == PIXELS // 4 else "gap"
        click.echo(f"{path}: {len(encoded) // 2} bytes, {form} form (gap form alone: {len(pad(gaps(pixels))) // 8} bytes)")
        if draw:
            for y in range(SIZE):
                click.echo("  " + pixels[SIZE * y : SIZE * y + SIZE].translate(str.maketrans("01", ".#")))
        click.echo(f"  pixels {to_hex(pixels)}")
        click.echo(f"  field  {encoded}")


if __name__ == "__main__":
    cli()
