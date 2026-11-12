# SPDX-License-Identifier: Apache-2.0
"""Size of the icon bitmap forms, measured on glyphs of BDF fonts.

Each glyph whose bounding box fits the 16 by 16 icon is centred in it and
its size is computed in the gap form of docs/spec/02-icon.md ("xor+gap")
and, for comparison, as alternating run lengths with and without the row
XOR ("xor+rle", "rle"). A glyph with no set pixel is skipped, and a bitmap
that occurs more than once in a file is counted once.

These are sizes only: this tool counts bits and does not produce an
encoding. A form is used when it is strictly shorter than the 32 bytes of
the plain bitmap, which is what the "used" and "with fallback" columns and
the histogram report.
"""

import os
import statistics
from collections import Counter

import click

SIZE = 16
RAW_BYTES = SIZE * SIZE // 8


def read_bdf(path):
    """Yield (codepoint, width, height, rows) for every glyph; rows are integers with the leftmost pixel in bit width-1."""
    codepoint = width = height = 0
    rows = None
    with open(path, "rb") as f:
        for line in f:
            word, _, rest = line.strip().partition(b" ")
            if word == b"ENCODING":
                codepoint = int(rest.split()[0])
            elif word == b"BBX":
                width, height = (int(x) for x in rest.split()[:2])
            elif word == b"BITMAP":
                rows = []
            elif word == b"ENDCHAR":
                if rows is not None and len(rows) == height:
                    yield codepoint, width, height, rows
                rows = None
            elif rows is not None and word:
                # A row is padded with zero bits on the right to a whole number of bytes.
                rows.append(int(word, 16) >> (len(word) * 4 - width))


def place(width, height, rows):
    """The 256 pixels of the icon, top row first, with the glyph centred. None if it does not fit."""
    if width > SIZE or height > SIZE:
        return None
    left = (SIZE - width) // 2
    top = (SIZE - height) // 2
    pixels = [0] * (SIZE * SIZE)
    for y, row in enumerate(rows):
        for x in range(width):
            pixels[(top + y) * SIZE + left + x] = (row >> (width - 1 - x)) & 1
    return pixels


def row_xor(pixels):
    """Every row XORed with the row above it; the top row is unchanged."""
    return pixels[:SIZE] + [a ^ b for a, b in zip(pixels[SIZE:], pixels[:-SIZE])]


def runs(bits):
    lengths = [1]
    for a, b in zip(bits, bits[1:]):
        if a == b:
            lengths[-1] += 1
        else:
            lengths.append(1)
    return lengths


def gamma_bits(n):
    """Length of the Elias gamma code of n >= 1."""
    return 2 * n.bit_length() - 1


def rle_bits(bits):
    """One bit for the first pixel, then every run length in Elias gamma."""
    return 1 + sum(gamma_bits(n) for n in runs(bits))


def gap_bits(bits):
    """The distance from each set bit to the next in Elias gamma, counting from before the first bit to after the last."""
    total = 0
    last = -1
    for pos in [i for i, bit in enumerate(bits) if bit] + [len(bits)]:
        total += gamma_bits(pos - last)
        last = pos
    return total


SPECIFIED = "xor+gap"
FORMS = {
    "rle": rle_bits,
    "xor+rle": lambda p: rle_bits(row_xor(p)),
    SPECIFIED: lambda p: gap_bits(row_xor(p)),
}
HISTOGRAM_WIDTH = 60


def parse_ranges(ctx, param, values):
    ranges = []
    for value in values:
        lo, _, hi = value.partition("-")
        try:
            ranges.append((int(lo, 16), int(hi or lo, 16)))
        except ValueError:
            raise click.BadParameter(f"{value!r} is not HEX or HEX-HEX")
    return ranges


def percentile(ordered, q):
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


@click.command()
@click.argument("bdf", nargs=-1, required=True, type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-c",
    "--codepoints",
    multiple=True,
    callback=parse_ranges,
    metavar="HEX[-HEX]",
    help="Only glyphs in this codepoint range. May be repeated.",
)
@click.option("-H", "--histogram", is_flag=True, help="Also draw the distribution of the icon bitmap size, 1 to 32 bytes.")
def cli(bdf, codepoints, histogram):
    """Measure the icon bitmap forms on the glyphs of BDF fonts."""
    if codepoints:
        click.echo("codepoints: " + ", ".join(f"{lo:04X}-{hi:04X}" for lo, hi in codepoints))
    for path in bdf:
        seen = set()
        total = too_large = blank = duplicate = 0
        for codepoint, width, height, rows in read_bdf(path):
            if codepoints and not any(lo <= codepoint <= hi for lo, hi in codepoints):
                continue
            total += 1
            pixels = place(width, height, rows)
            if pixels is None:
                too_large += 1
            elif not any(pixels):
                blank += 1
            elif tuple(pixels) in seen:
                duplicate += 1
            else:
                seen.add(tuple(pixels))
        click.echo(f"\n{os.path.basename(path)}: {total:,} glyphs, {len(seen):,} measured")
        click.echo(f"  skipped: {too_large:,} larger than {SIZE} by {SIZE}, {blank:,} blank, {duplicate:,} duplicate")
        if not seen:
            continue
        click.echo(f"  set pixels: mean {statistics.fmean(sum(p) for p in seen):.1f} of {SIZE * SIZE}")
        click.echo(f"  plain bitmap: {RAW_BYTES} bytes")
        click.echo(f"  {'form, bytes':<12}{'mean':>7}{'p10':>5}{'p50':>5}{'p90':>5}{'max':>5}{'used':>8}{'with fallback':>15}")
        for name, size in FORMS.items():
            sizes = sorted((size(list(p)) + 7) // 8 for p in seen)
            used = sum(1 for s in sizes if s < RAW_BYTES)
            fallback = statistics.fmean(min(s, RAW_BYTES) for s in sizes)
            click.echo(
                f"  {name:<12}{statistics.fmean(sizes):>7.1f}{percentile(sizes, 0.1):>5}{percentile(sizes, 0.5):>5}"
                f"{percentile(sizes, 0.9):>5}{sizes[-1]:>5}{used / len(sizes):>8.1%}{fallback:>15.1f}"
            )
        if histogram:
            draw_histogram(Counter(min((FORMS[SPECIFIED](list(p)) + 7) // 8, RAW_BYTES) for p in seen))


def draw_histogram(counts):
    """One row per size from 1 to 32 bytes; 32 is the plain form."""
    total = sum(counts.values())
    peak = max(counts.values())
    click.echo(f"  bitmap size as sent ({SPECIFIED}, or plain at {RAW_BYTES} bytes):")
    click.echo(f"  {'bytes':>5}{'glyphs':>8}{'share':>8}{'cumul.':>8}")
    cumulative = 0
    for size in range(1, RAW_BYTES + 1):
        n = counts[size]
        cumulative += n
        bar = "#" * round(HISTOGRAM_WIDTH * n / peak)
        if n and not bar:
            bar = "."
        click.echo(f"  {size:>5}{n:>8,}{n / total:>8.1%}{cumulative / total:>8.1%}  {bar}")
