# SPDX-License-Identifier: Apache-2.0
"""Extract reference PDFs to Markdown for reading and searching.

Written for the APRS documents of 3rdparty/aprsspec, which are Word
exports, and usable on other PDFs with a text layer. The output is a local
working copy: it goes under work/ and is never committed, because the
documents' terms do not allow copying their text into the project.

What the APRS documents say with typography is kept as Markdown:

\b
  - text in a Courier font (literal APRS data) becomes a `code span`, and
    two or more lines of it without highlights a fenced block that keeps
    their indentation;
  - text on a yellow highlight (literal characters in a format diagram)
    becomes ==marked==;
  - in a packet format diagram (a table with a "Bytes" row label) a
    grey-shaded cell gets "(optional)" appended, except in a title row;
  - a table cell in white text on black (a non-printing character) gets
    "(non-printing)" appended;
  - a raised character (an exponent) is written ^x or ^(xy).

Tables are rebuilt from their ruling lines; text left of a row, such as
"Bytes:", becomes an extra first column, and alternatives stacked in one
column of a diagram share one cell, separated by <br>. Bold lines in the left margin
become "##" headings, bold numbered lines and large bold lines become
headings by their numbering depth. Running headers and footers, recognised
as lines near the top or bottom edge that repeat on many pages, are
removed; each page starts with a comment giving its PDF page number and the
page number printed on it. Lines set one by one end in a hard line break.
Rotated text is given after the page's other text it stands beside, marked
"(rotated)".

Characters are kept as the text layer has them, except:

\b
  - in Courier text, U+2018 and U+2019 become ` and ', and U+2013 becomes
    -, because Word's typographic replacement altered the data there;
  - U+0002, drawn as '-' in the documents, becomes '-';
  - the symbol-font code points U+F020 (space), U+F0B7 (bullet), U+F0FC
    (check mark) and U+F04F (ballot x) become their Unicode characters.
    Other private-use characters are left and counted in the report;
  - outside code, the Markdown characters \\ ` * _ [ ] < are escaped with
    a backslash.

Images are written next to the Markdown file and linked where they stand,
inside a table cell if they sit in one. An image that occurs on three or
more pages (a logo) is left out.

Known limits: columns separated only by shading or white space, with no
rule (some Mic-E tables, tab-aligned lists), share one cell or one line;
hanging-indent lists may be split into paragraphs; links are not kept.

With --check, every page is compared with the output of poppler's
`pdftotext -layout` for the same page, an independent extraction: the
letters and digits of the page, headers and footers included, must be the
same multiset. Pages that differ are listed.
"""

import os
import re
import shutil
import statistics
import subprocess
from collections import Counter
from functools import partial
from pathlib import Path

import blake3
import click
import pdfplumber
import pypdfium2

from .parallel import jobs_option, map_files

# Fraction of the page height at the top and at the bottom searched for running headers and footers.
FURNITURE_BAND = 0.11
# A header or footer line, with digits removed, recurs on at least this share of the pages.
FURNITURE_SHARE = 0.2
# An image whose pixels recur on this many pages is decoration.
REPEATED_IMAGE_PAGES = 3
# A run of raised characters longer than this is not an exponent (a drop cap, a misaligned word).
MAX_RAISED = 3

GLOBAL_MAP = {chr(0x02): "-", chr(0xF020): " ", chr(0xF0B7): chr(0x2022), chr(0xF0FC): chr(0x2714), chr(0xF04F): chr(0x2717)}
COURIER_MAP = {chr(0x2018): "`", chr(0x2019): "'", chr(0x2013): "-"}
BULLETS = (chr(0x2022), chr(0x25AA))
MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]<^])")
PRIVATE_USE = re.compile(f"[{chr(0xE000)}-{chr(0xF8FF)}]")


def colour(value):
    """A fill colour as a tuple of floats, or None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return (float(value),)
    try:
        return tuple(float(v) for v in value)
    except (TypeError, ValueError):
        return None


def is_yellow(c):
    return c is not None and len(c) == 3 and c[0] > 0.9 and c[1] > 0.9 and c[2] < 0.2


def is_grey(c):
    if c is None:
        return False
    if len(c) == 1:
        return 0.75 < c[0] < 0.95
    return len(c) == 3 and max(c) - min(c) < 0.02 and 0.75 < c[0] < 0.95


def is_dark(c):
    return c is not None and sum(c) / len(c) < 0.5


def is_ruling(obj):
    """Whether a page object may be a table rule.

    Highlights, shading (Word draws it in thin slices too) and white boxes
    have edges, but are not rules; a filled rectangle is a rule only if it
    is dark (a thin black rule, or a black cell whose edges bound its row).
    """
    if obj.get("object_type") != "rect" or not obj.get("fill"):
        return True
    return is_dark(colour(obj.get("non_stroking_color")))


def is_rotated(char):
    a, b = char["matrix"][:2]
    return abs(b) > abs(a)


def is_white(char):
    c = colour(char.get("non_stroking_color"))
    return c is not None and min(c) > 0.9 and (len(c) != 4 or max(c) < 0.1)


def inside(x, y, box, slack=0.5):
    x0, top, x1, bottom = box
    return x0 - slack <= x <= x1 + slack and top - slack <= y <= bottom + slack


def centre(obj):
    return (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2


def is_space(char):
    return char["text"].isspace() or char["text"] == chr(0xF020)


def is_courier(char):
    return "courier" in char["fontname"].lower()


def is_bold(char):
    return "bold" in char["fontname"].lower()


def mostly(chars, test, share=0.8):
    chars = [c for c in chars if not is_space(c)]
    return bool(chars) and sum(1 for c in chars if test(c)) >= share * len(chars)


# ---------------------------------------------------------------- lines and runs


def group_lines(chars):
    """Group characters into lines by vertical overlap; each line is a list sorted left to right."""
    lines = []
    for ch in sorted(chars, key=lambda c: (c["top"], c["x0"])):
        height = ch["bottom"] - ch["top"]
        for line in lines:
            overlap = min(line["bottom"], ch["bottom"]) - max(line["top"], ch["top"])
            if overlap >= 0.5 * min(height, line["bottom"] - line["top"]):
                line["chars"].append(ch)
                # Grow only by full-size characters, so a superscript does not pull the next line in.
                if height >= 0.8 * (line["bottom"] - line["top"]):
                    line["top"] = min(line["top"], ch["top"])
                    line["bottom"] = max(line["bottom"], ch["bottom"])
                break
        else:
            lines.append({"top": ch["top"], "bottom": ch["bottom"], "chars": [ch]})
    for line in lines:
        finish_line(line)
    lines.sort(key=lambda line: (line["top"], line["x0"]))
    return lines


def finish_line(line):
    line["chars"].sort(key=lambda c: c["x0"])
    ink = [c for c in line["chars"] if not is_space(c)] or line["chars"]
    line["x0"] = ink[0]["x0"]
    line["x1"] = max(c["x1"] for c in ink)
    line["size"] = statistics.median(c["size"] for c in ink)
    line["baseline"] = statistics.median(c["bottom"] for c in ink)
    return line


class Marks:
    """Per-page highlight and shading boxes, from filled rectangles and filled paths."""

    def __init__(self, page):
        self.yellow = []
        self.grey = []
        for r in list(page.rects) + list(page.curves):
            if not r.get("fill"):
                continue
            c = colour(r.get("non_stroking_color"))
            box = (r["x0"], r["top"], r["x1"], r["bottom"])
            if is_yellow(c):
                self.yellow.append(box)
            elif is_grey(c):
                self.grey.append(box)

    def highlighted(self, char):
        """At least half the character's width lies on a highlight at its height."""
        _, y = centre(char)
        width = max(char["x1"] - char["x0"], 0.1)
        for x0, top, x1, bottom in self.yellow:
            if top - 1 <= y <= bottom + 1 and min(x1, char["x1"]) - max(x0, char["x0"]) >= 0.5 * width:
                return True
        return False

    def shaded(self, box):
        x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        return any(inside(x, y, b, 0) for b in self.grey)


def char_text(char, courier):
    t = GLOBAL_MAP.get(char["text"], char["text"])
    if courier:
        t = COURIER_MAP.get(t, t)
    return t


def line_pieces(line, marks):
    """The line as a list of pieces [text, courier, highlight, raised], with spaces for gaps.

    A space piece has courier None and is resolved from its neighbours in
    render_pieces; its highlight is its own for a space character, None for
    a gap.
    """
    chars = line["chars"]
    size = line["size"]
    ink = [i for i, c in enumerate(chars) if not is_space(c)]
    pieces = []
    prev = None
    for i, ch in enumerate(chars):
        if is_space(ch):
            # A stray space from another run that overlaps the glyphs beside it is not a space of this line.
            left = next((chars[j] for j in reversed(ink) if j < i), None)
            right = next((chars[j] for j in ink if j > i), None)
            if (left and ch["x0"] < left["x1"] - 0.3) or (right and ch["x1"] > right["x0"] + 0.3):
                continue
        courier = is_courier(ch)
        if prev is not None:
            gap = ch["x0"] - prev["x1"]
            if courier and is_courier(prev):
                # Courier advances 0.6 em; a glyph's box (such as that of U+02FD) may be narrower.
                n = int(gap / (0.6 * prev["size"]) + 0.4)
            elif gap > 1.2 * size:
                n = max(2, round(gap / (0.5 * size)))
            elif gap > 0.15 * size and not is_space(prev):
                # A justified line widens its spaces; a space character already stands for that gap.
                n = 1
            else:
                n = 0
            if n > 0:
                pieces.append([" " * n, None, None, False])
        text = char_text(ch, courier)
        if text.isspace():
            pieces.append([text, None, marks.highlighted(ch), False])
        else:
            raised = ch["bottom"] < line["baseline"] - 0.2 * size
            pieces.append([text, courier, marks.highlighted(ch), raised])
        prev = ch
    # Long raised runs are not exponents.
    i = 0
    while i < len(pieces):
        if pieces[i][3]:
            j = i
            while j < len(pieces) and pieces[j][3]:
                j += 1
            if j - i > MAX_RAISED:
                for k in range(i, j):
                    pieces[k][3] = False
            i = j
        else:
            i += 1
    return pieces


def render_pieces(pieces):
    """Markdown for a list of pieces. A space between two Courier characters belongs to the code span."""
    resolved = []
    for i, (text, courier, hl, raised) in enumerate(pieces):
        if courier is None:
            before = next((p for p in reversed(pieces[:i]) if p[1] is not None), None)
            after = next((p for p in pieces[i + 1 :] if p[1] is not None), None)
            code = before is not None and after is not None and before[1] and after[1]
            both_hl = before is not None and after is not None and before[2] and after[2]
            resolved.append((text, bool(code), bool(both_hl if hl is None else hl and both_hl), False))
        else:
            resolved.append((text, courier, hl, raised))
    out = []
    i = 0
    while i < len(resolved):
        key = resolved[i][1:]
        j = i
        while j < len(resolved) and resolved[j][1:] == key:
            j += 1
        out.append(decorate("".join(p[0] for p in resolved[i:j]), *key))
        i = j
    return "".join(out)


def decorate(text, courier, hl, raised):
    if not text.strip():
        return text
    if courier:
        fence = "``" if "`" in text else "`"
        pad = " " if text.startswith("`") or text.endswith("`") or (text.startswith(" ") and text.endswith(" ")) else ""
        lead, core, trail = "", f"{fence}{pad}{text}{pad}{fence}", ""
    else:
        core = text.strip(" ")
        lead = text[: len(text) - len(text.lstrip(" "))]
        trail = text[len(text.rstrip(" ")) :]
        core = escape_markdown(core)
    if raised:
        core = f"^{core}" if len(core) == 1 else f"^({core})"
    if hl:
        core = f"=={core}=="
    return lead + core + trail


def escape_markdown(text):
    return MARKDOWN_SPECIAL.sub(r"\\\1", text).replace("==", "\\=\\=")


def render_line(line, marks):
    return render_pieces(line_pieces(line, marks)).strip()


def plain_line(line):
    return "".join(GLOBAL_MAP.get(c["text"], c["text"]) for c in line["chars"]).strip()


# ---------------------------------------------------------------- document analysis


def furniture_key(text):
    return re.sub(r"\s+", " ", re.sub(r"\d", "", text)).strip()


def band_chars(page, chars):
    height = page.height
    return [c for c in chars if c["top"] < FURNITURE_BAND * height or c["bottom"] > (1 - FURNITURE_BAND) * height]


def position_key(line):
    """Where a header or footer line sits and how it is set; chapter headers change text but not this."""
    first = line["chars"][0]
    return (round(line["top"] / 3), first["fontname"], round(first["size"]))


def is_furniture(line, ctx):
    return furniture_key(plain_line(line)) in ctx["furniture"] or position_key(line) in ctx["furniture_positions"]


def analyse(pages):
    """Recurring header and footer keys and positions, the body column, and whether a side-heading column exists."""
    keys = Counter()
    positions = Counter()
    for page in pages:
        lines = group_lines(band_chars(page, page.chars))
        keys.update({furniture_key(plain_line(line)) for line in lines})
        positions.update({position_key(line) for line in lines})
    threshold = max(2, FURNITURE_SHARE * len(pages))
    furniture = {k for k, n in keys.items() if n >= threshold}
    # The first body line of a page often sits at the same height on many pages; never take the body font by position.
    fonts = Counter((c["fontname"], round(c["size"])) for p in pages for c in p.chars)
    body_font = fonts.most_common(1)[0][0] if fonts else None
    furniture_positions = {k for k, n in positions.items() if n >= threshold and (k[1], k[2]) != body_font}
    starts = Counter()
    ends = Counter()
    for page in pages:
        for line in group_lines(page.chars):
            if line["top"] < FURNITURE_BAND * page.height or line["bottom"] > (1 - FURNITURE_BAND) * page.height:
                continue
            starts[round(line["x0"])] += len(line["chars"])
            if len(line["chars"]) >= 40:
                ends[round(line["x1"])] += 1
    body_left = starts.most_common(1)[0][0] if starts else 0
    widths = sorted(ends.elements())
    body_right = widths[int(0.9 * (len(widths) - 1))] if widths else 0
    left_bold = sum(1 for p in pages for c in p.chars if c["x1"] < body_left - 10 and is_bold(c))
    sizes = Counter(round(c["size"], 1) for p in pages for c in p.chars if not is_space(c))
    return {
        "furniture": furniture,
        "furniture_positions": furniture_positions,
        "body_left": body_left,
        "body_right": body_right,
        "side_column": left_bold > 50 * max(1, len(pages) // 20),
        "body_size": sizes.most_common(1)[0][0] if sizes else 10,
    }


def image_objects(pdf_path):
    """Per page (0-based): list of (box in pdfplumber coordinates, digest, PIL image)."""
    doc = pypdfium2.PdfDocument(pdf_path)
    result = []
    for page in doc:
        height = page.get_height()
        items = []
        for obj in page.get_objects(filter=[pypdfium2.raw.FPDF_PAGEOBJ_IMAGE], max_depth=4):
            left, bottom, right, top = obj.get_bounds()
            try:
                # Rendering applies the soft mask, so a transparent background does not come out black.
                image = obj.get_bitmap(render=True).to_pil()
            except Exception:
                continue
            digest = blake3.blake3(image.tobytes() + repr(image.size).encode()).hexdigest()[:16]
            items.append(((left, height - top, right, height - bottom), digest, image))
        result.append(items)
    return result


# ---------------------------------------------------------------- tables


def cell_text(chars, marks):
    lines = [render_line(line, marks) for line in group_lines(chars)]
    return "<br>".join(text for text in lines if text)


def escape_cell(text):
    return text.replace("|", "\\|")


def table_markdown(rows):
    """Tables for a grid of cell strings: split at empty rows, without empty columns."""
    groups = [[]]
    for row in rows:
        if any(cell for cell in row):
            groups[-1].append(row)
        elif groups[-1]:
            groups.append([])
    out = []
    for group in groups:
        if not group:
            continue
        keep = [j for j in range(len(group[0])) if any(row[j] for row in group)]
        group = [[row[j] for j in keep] for row in group]
        if len(keep) == 1 and len(group) == 1:
            out.append("\n".join("> " + part for part in group[0][0].split("<br>")))
            continue
        lines = ["| " + " | ".join(group[0]) + " |", "|" + "---|" * len(keep)]
        lines += ["| " + " | ".join(row) + " |" for row in group[1:]]
        out.append("\n".join(lines))
    return "\n\n".join(out)


BYTE_COUNT = re.compile(r"[0-9n]+(\s*(-|\u2013|or|to)\s*[0-9n]+)*")


def is_count_row(texts):
    """Whether a row's cells are byte counts (1, n, 0-43, 4 or 6): the row a "Bytes:" label names."""
    values = [re.sub(r"[`=\\]|<br>", "", t).strip() for t in texts if t]
    return len(values) >= 2 and all(BYTE_COUNT.fullmatch(v) for v in values)


def build_table(table, chars, marks, label_lines, cell_images):
    """Markdown for one table, and the ids of the characters placed in it.

    label_lines are (y, text) for text left of the table. A "Bytes:" label
    goes to the nearest row of byte counts, any other label to the row whose
    band holds it. A table with a "Bytes" label is a packet format diagram;
    only there does grey shading mean an optional field, and not in a title
    row (one cell across the whole table). A cell in white text (on a black
    ground) holds a non-printing character.

    A row that exists only because some columns are split, the other columns
    spanning it from the row above (stacked alternatives such as the forms
    of a data extension), is merged into the row above with line breaks.
    """
    width = table.bbox[2] - table.bbox[0]
    columns = [col.bbox for col in table.columns]
    rows = []
    used = set()
    for row in table.rows:
        boxes = list(row.cells)
        present = [b for b in boxes if b is not None]
        title = len(present) == 1 and present[0][2] - present[0][0] >= 0.9 * width
        cells = []
        for b in boxes:
            if b is None:
                cells.append(None)
                continue
            inner = [ch for ch in chars if id(ch) not in used and inside(*centre(ch), b, 0)]
            used.update(id(ch) for ch in inner)
            text = cell_text(inner, marks)
            for link in cell_images.get(b, []):
                text = f"{text} {link}".strip()
            if text and mostly(inner, is_white):
                text += " (non-printing)"
            cells.append((escape_cell(text), bool(text) and not title and marks.shaded(b)))
        # Spanned from above: more columns are covered by cells of earlier rows than start in this one.
        from_above = sum(
            1 for b, col in zip(boxes, columns) if b is None and not any(p[0] <= col[0] + 1 and p[2] >= col[2] - 1 for p in present)
        )
        spanned = from_above > len(present)
        rows.append({"cells": cells, "bbox": row.bbox, "spanned": spanned, "label": ""})

    for y, text in label_lines:
        middle = [abs((r["bbox"][1] + r["bbox"][3]) / 2 - y) for r in rows]
        counts = [i for i, r in enumerate(rows) if is_count_row([c[0] for c in r["cells"] if c])]
        if text.lower().startswith("bytes") and counts:
            i = min(counts, key=lambda i: middle[i])
        else:
            holding = [i for i, r in enumerate(rows) if r["bbox"][1] - 1 <= y <= r["bbox"][3] + 1]
            if not holding:
                continue
            i = min(holding, key=lambda i: rows[i]["bbox"][3] - rows[i]["bbox"][1])
        rows[i]["label"] = (rows[i]["label"] + " " + text).strip()
    diagram = any(r["label"].lower().startswith("bytes") for r in rows)

    grid = []
    for r in rows:
        texts = [(c[0] + (" (optional)" if diagram and c[1] else "")) if c else "" for c in r["cells"]]
        if r["spanned"] and grid and not r["label"]:
            above = grid[-1]
            for j, t in enumerate(texts):
                if t:
                    above[j + 1] = f"{above[j + 1]}<br>{t}" if above[j + 1] else t
            continue
        grid.append([escape_cell(r["label"])] + texts)
    if not any(row[0] for row in grid):
        grid = [row[1:] for row in grid]
    width = max(len(r) for r in grid)
    grid = [r + [""] * (width - len(r)) for r in grid]
    return table_markdown(grid), used


def table_labels(table, chars, other_boxes, marks):
    """Lines of text left of the table's cells: the "Bytes:" of a format diagram.

    A label character lies in no cell of the table and in no other table,
    and left of every cell at its height. Returns ((y, text) per line, the
    characters).
    """
    cells = list(table.cells)
    picked = []
    for c in chars:
        x, y = centre(c)
        if not (table.bbox[1] <= y <= table.bbox[3]) or c["x0"] < table.bbox[0] - 150:
            continue
        if any(inside(x, y, b, 0) for b in cells) or any(inside(x, y, b, 0) for b in other_boxes):
            continue
        level = [b[0] for b in cells if b[1] <= y <= b[3]]
        if level and x < min(level):
            picked.append(c)
    lines = []
    for line in group_lines(picked):
        text = render_line(line, marks)
        if text:
            lines.append(((line["top"] + line["bottom"]) / 2, text))
    return lines, picked


# ---------------------------------------------------------------- running text


def printed_number(lines, height):
    """The page number among the header and footer lines."""
    top = [line for line in lines if line["top"] < height / 2]
    bottom = [line for line in lines if line["top"] >= height / 2]
    for line in top + bottom:
        text = plain_line(line)
        match = re.search(r"\bPage\s+(\d{1,4})\b", text)
        if match:
            return match.group(1)
        words = text.split()
        if not words or (line in bottom and len(words) > 3):
            continue
        for w in (words[0], words[-1]):
            if w.isdigit() and len(w) <= 4:
                return w
    return None


def heading_level(line, text, body_size):
    """1 to 4 for a heading line, else None: bold and short, numbered or clearly larger than the body."""
    if len(text) > 100 or not mostly(line["chars"], is_bold):
        return None
    number = re.match(r"^(\d+(?:\.\d+)*)\.?\s+\S", plain_line(line))
    if number and line["size"] >= body_size - 0.5:
        return min(4, number.group(1).count(".") + 1)
    if line["size"] >= 1.2 * body_size:
        return 1
    return None


def first_word_end(line):
    """x where the line's first word ends: at a space character or a gap of a third of an em."""
    chars = line["chars"]
    for i, ch in enumerate(chars):
        if is_space(ch):
            return ch["x0"]
        if i and ch["x0"] - chars[i - 1]["x1"] > 0.33 * line["size"]:
            return chars[i - 1]["x1"]
    return line["x1"]


class Block:
    def __init__(self, line, kind, text, margin):
        self.top = line["top"]
        self.x0 = line["x0"]
        self.kind = kind
        self.parts = [text]
        self.margin = margin
        self.lines = [line]

    @property
    def last(self):
        return self.lines[-1]


def paragraphs(lines, marks, body_size, body_right):
    """Join body lines into Markdown blocks. Returns (top, x0, text) tuples.

    A line that follows closely joins the block before. It continues the
    paragraph with a space (or with nothing after a hyphen) if its first
    word would not have fitted at the end of the line before, which then
    wrapped; otherwise it is set on a line of its own after a hard break. A
    line indented past the paragraph's margin starts a new paragraph, but the
    line after an indented first line may return to the margin. The right
    edge is the one that three in four long lines of the page stay within (a
    line of data may overrun the margin), or the document's.
    """
    long_lines = sorted(line["x1"] for line in lines if len(line["chars"]) >= 30)
    if long_lines:
        body_right = long_lines[int(0.75 * (len(long_lines) - 1))]
    blocks = []
    current = None
    for line in lines:
        text = render_line(line, marks)
        if not text:
            continue
        size = line["size"]
        level = heading_level(line, text, body_size)
        if level:
            blocks.append(Block(line, "heading", "#" * level + " " + text, line["x0"]))
            current = None
            continue
        code = mostly(line["chars"], is_courier, 0.9)
        bullet = text[0] in BULLETS and len(text) > 1 and text[1] in " \t"
        if bullet:
            ink = [c for c in line["chars"] if not is_space(c)]
            margin = ink[1]["x0"] if len(ink) > 1 else line["x0"]
            text = "- " + text[1:].strip()
        elif re.match(r"^(#|>|\+|-|\d+[.)]\s)", text):
            text = "\\" + text
            margin = line["x0"]
        else:
            margin = line["x0"]
        close = current is not None and line["top"] - current.last["bottom"] < 0.6 * size
        if close and code and current.kind == "code":
            current.parts.append(text)
            current.lines.append(line)
            continue
        if close and not code and not bullet and current.kind in ("para", "bullet"):
            prev = current.last
            word = first_word_end(line) - line["x0"]
            wrapped = prev["x1"] + 0.3 * size + word > body_right - 2 and word < 0.4 * (body_right - line["x0"])
            if len(current.lines) == 1 and current.kind == "para" and line["x0"] < current.margin - 2 and wrapped:
                current.margin = line["x0"]  # first-line indent
            indent = line["x0"] - current.margin
            if -2 <= indent <= 0.8 * size:
                if wrapped:
                    joiner = "" if current.parts[-1].endswith("-") else " "
                else:
                    joiner = "  \n"
                current.parts[-1] += joiner + text
                current.lines.append(line)
                continue
        current = Block(line, "code" if code else "bullet" if bullet else "para", text, margin)
        blocks.append(current)
    return [(b.top, b.x0, finish_block(b)) for b in blocks]


def finish_block(block):
    if block.kind != "code" or len(block.lines) == 1:
        return "  \n".join(block.parts)
    if any("==" in part for part in block.parts):
        return "  \n".join(block.parts)
    # Every character goes to the column of the Courier grid it stands on, whatever its own font.
    left = min(line["x0"] for line in block.lines)
    pitch = 0.6 * statistics.median(line["size"] for line in block.lines)
    body = []
    for line in block.lines:
        row = ""
        for ch in line["chars"]:
            if is_space(ch):
                continue
            column = max(len(row), int((ch["x0"] - left) / pitch + 0.4))
            row = row.ljust(column) + char_text(ch, is_courier(ch))
        body.append(row)
    fence = "````" if any("```" in b for b in body) else "```"
    return fence + "\n" + "\n".join(body) + "\n" + fence


def split_side_column(lines, body_left):
    """Separate side headings from body lines.

    Bold text wholly left of the body column is a side heading. A line that
    starts in the margin with bold text and continues, after a gap, with
    text that is not bold is split there (a side heading level with the
    first line of its paragraph). Anything else stays body text.
    """
    side, body = [], []
    edge = body_left - 4
    for line in lines:
        ink = [c for c in line["chars"] if not is_space(c)]
        if not ink:
            continue
        if line["x1"] < edge:
            (side if mostly(ink, is_bold) else body).append(line)
            continue
        if line["x0"] >= edge:
            body.append(line)
            continue
        cut = None
        for i in range(1, len(ink)):
            gap = ink[i]["x0"] - ink[i - 1]["x1"]
            if gap > 0.8 * line["size"] and ink[i - 1]["x1"] < edge and mostly(ink[:i], is_bold) and not is_bold(ink[i]):
                cut = ink[i]["x0"] - 0.1
                break
        if cut is None:
            body.append(line)
            continue
        side.append(finish_line({"top": line["top"], "bottom": line["bottom"], "chars": [c for c in ink if c["x0"] < cut]}))
        body.append(
            finish_line({"top": line["top"], "bottom": line["bottom"], "chars": [c for c in line["chars"] if c["x0"] >= cut]})
        )
    side.sort(key=lambda line: line["top"])
    body.sort(key=lambda line: (line["top"], line["x0"]))
    return side, body


def side_headings(lines, marks):
    """Join consecutive side-column lines into headings, placed just before the text level with them."""
    blocks = []
    for line in lines:
        text = render_line(line, marks)
        if not text:
            continue
        if blocks and line["top"] - blocks[-1][3] < 0.6 * line["size"]:
            blocks[-1][2] += " " + text
            blocks[-1][3] = line["bottom"]
        else:
            blocks.append([line["top"] - 0.5 * line["size"], line["x0"], text, line["bottom"]])
    return [(b[0], b[1], "## " + b[2]) for b in blocks]


def rotated_block(chars, marks):
    """Rotated characters, read column by column from left to right and upwards within a column."""
    columns = []
    for ch in sorted(chars, key=lambda c: c["x0"]):
        if columns and ch["x0"] - columns[-1][-1]["x0"] < 0.5 * ch["size"]:
            columns[-1].append(ch)
        else:
            columns.append([ch])
    text = " ".join("".join(char_text(c, is_courier(c)) for c in sorted(col, key=lambda c: -c["bottom"])) for col in columns)
    top = min(c["top"] for c in chars)
    x0 = min(c["x0"] for c in chars)
    return (top, x0, "(rotated) " + escape_markdown(" ".join(text.split())))


# ---------------------------------------------------------------- pages


def render_page(page, number, ctx, images, image_dir, image_prefix):
    marks = Marks(page)
    height = page.height
    tables = page.filter(is_ruling).find_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
    table_boxes = [t.bbox for t in tables]

    # Header and footer lines, but never a table row that reaches into the band.
    inner_boxes = [b for b in table_boxes if b[1] >= 0 and b[3] <= height]
    loose = [c for c in page.chars if not any(inside(*centre(c), b, 0) for b in inner_boxes)]
    band = [line for line in group_lines(band_chars(page, loose)) if is_furniture(line, ctx)]
    furniture_ids = {id(c) for line in band for c in line["chars"]}
    printed = printed_number(sorted(band, key=lambda line: line["top"]), height)
    furniture_text = " ".join(plain_line(line) for line in band)
    chars = [c for c in page.chars if id(c) not in furniture_ids]

    blocks = []
    rotated = [c for c in chars if is_rotated(c)]
    if rotated:
        blocks.append(rotated_block(rotated, marks))
        rotated_ids = {id(c) for c in rotated}
        chars = [c for c in chars if id(c) not in rotated_ids]

    image_links = []
    for k, (box, digest, image) in enumerate(images):
        if digest in ctx["repeated_images"]:
            continue
        name = f"p{number:03d}-{k + 1}.png"
        image.save(image_dir / name)
        image_links.append((box, f"![image]({image_prefix}/{name})"))

    in_table = set()
    placed_images = set()
    for t in tables:
        others = [b for b in table_boxes if b != t.bbox]
        labels, label_chars = table_labels(t, chars, others, marks)
        in_table.update(id(c) for c in label_chars)
        label_ids = {id(c) for c in label_chars}
        tchars = [c for c in chars if inside(*centre(c), t.bbox, 0) and id(c) not in label_ids]
        cell_images = {}
        for i, (box, link) in enumerate(image_links):
            x, y = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            for row in t.rows:
                for b in row.cells:
                    if b is not None and inside(x, y, b, 0):
                        cell_images.setdefault(b, []).append(link)
                        placed_images.add(i)
        text, used = build_table(t, tchars, marks, labels, cell_images)
        # Characters in the frame but in no cell stay in the running text, so nothing is lost.
        in_table.update(used)
        blocks.append((t.bbox[1], t.bbox[0], text))

    for i, (box, link) in enumerate(image_links):
        if i not in placed_images:
            blocks.append((box[1], box[0], link))

    flow = [c for c in chars if id(c) not in in_table]
    if ctx["side_column"]:
        side, body = split_side_column(group_lines(flow), ctx["body_left"])
        blocks += side_headings(side, marks)
    else:
        body = group_lines(flow)
    blocks += paragraphs(body, marks, ctx["body_size"], ctx["body_right"])
    blocks = [b for b in blocks if b[2].strip()]
    blocks.sort(key=lambda b: (b[0], b[1]))

    head = f"<!-- page {number}" + (f", printed {printed}" if printed else "") + " -->"
    text = head + "\n\n" + "\n\n".join(b[2] for b in blocks) + "\n"
    return text, furniture_text


# ---------------------------------------------------------------- check


ALNUM = re.compile(r"[A-Za-z0-9]")
ADDED = re.compile(r"<!--.*?-->|!\[image\]\([^)]*\)|\((optional|rotated|non-printing)\)|<br>")


def alnum(text):
    return Counter(ALNUM.findall(ADDED.sub(" ", text)))


def pdftotext_pages(pdf_path):
    out = subprocess.run(["pdftotext", "-layout", pdf_path, "-"], capture_output=True, check=True).stdout
    return out.decode("utf-8", "replace").split("\f")


def describe(diff):
    return " ".join(f"{k}{v:+d}" for k, v in sorted(diff.items()))


# ---------------------------------------------------------------- driver


def extract(pdf_path, out_dir, check):
    """Write <stem>.md and <stem>.images/ under out_dir. Returns a report dict."""
    pdf_path = str(pdf_path)
    stem = Path(pdf_path).stem
    out_dir = Path(out_dir)
    tmp_md = out_dir / f".{stem}.md.tmp"
    image_dir = out_dir / f".{stem}.images.tmp"
    shutil.rmtree(image_dir, ignore_errors=True)
    image_dir.mkdir(parents=True)

    report = {"pages": 0, "images": 0, "pua": Counter(), "check": []}
    images = image_objects(pdf_path)
    seen = Counter()
    for items in images:
        seen.update({digest for _, digest, _ in items})
    reference = pdftotext_pages(pdf_path) if check else None

    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.dedupe_chars() for p in pdf.pages]
        ctx = analyse(pages)
        ctx["repeated_images"] = {d for d, n in seen.items() if n >= REPEATED_IMAGE_PAGES}
        parts = []
        for i, page in enumerate(pages):
            text, furniture_text = render_page(page, i + 1, ctx, images[i], image_dir, f"{stem}.images")
            parts.append(text)
            report["pages"] += 1
            report["pua"].update(PRIVATE_USE.findall(text))
            if reference is not None and i < len(reference):
                diff = alnum(text + " " + furniture_text)
                diff.subtract(alnum(reference[i]))
                diff = {k: v for k, v in diff.items() if v}
                if diff:
                    report["check"].append((i + 1, describe(diff)))

    tmp_md.write_text("\n".join(parts), encoding="utf-8")
    final_images = out_dir / f"{stem}.images"
    report["images"] = len(list(image_dir.iterdir()))
    shutil.rmtree(final_images, ignore_errors=True)
    if report["images"]:
        os.replace(image_dir, final_images)
    else:
        image_dir.rmdir()
    os.replace(tmp_md, out_dir / f"{stem}.md")
    report["side_column"] = ctx["side_column"]
    report["body_left"] = ctx["body_left"]
    return report


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("pdf", nargs=-1, required=True, type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=False),
    default="work/refs/text",
    show_default=True,
    help="Directory for the Markdown files and their image directories.",
)
@click.option("--check", is_flag=True, help="Compare every page with pdftotext -layout and list the pages that differ.")
@jobs_option
def cli(pdf, output, check, jobs):
    if check and shutil.which("pdftotext") is None:
        raise click.ClickException("--check needs pdftotext (poppler-utils)")
    Path(output).mkdir(parents=True, exist_ok=True)
    for path, report in map_files(partial(extract, out_dir=output, check=check), list(pdf), jobs):
        name = Path(path).name
        layout = f"side headings left of x={report['body_left']}" if report["side_column"] else "single column"
        click.echo(f"{name}: {report['pages']} pages, {report['images']} images, {layout}")
        if report["pua"]:
            click.echo("  private-use characters left: " + " ".join(f"U+{ord(k):04X}x{v}" for k, v in report["pua"].most_common()))
        if check:
            bad = report["check"]
            click.echo(f"  check against pdftotext: {report['pages'] - len(bad)} of {report['pages']} pages agree")
            for number, diff in bad:
                click.echo(f"    page {number}: {diff}")


if __name__ == "__main__":
    cli()
