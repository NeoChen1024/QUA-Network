# SPDX-License-Identifier: Apache-2.0
"""Measure the free text of the corpus: how often a station sends the same
text again, and how small Unishox2 makes each text (RFC 5.7; section 15,
step 11).

Reads TNC2 lines from corpus files and decodes each packet in permissive
mode (docs/interop/01-record.md). The texts are the comment of a position,
the comment of an Object or Item, the status text, the message text and
the bulletin text.

Repetition: a text repeats if it is equal to the text before it of the
same kind from the same source. For an Object or Item, the name is part of
the key.

Compression: the tool compresses each text with every preset of Unishox2
and checks that the decompressed bytes are the input. The size of a text
under a preset is the rule of RFC 5.7: one length byte and the compressed
bytes if that is shorter than the text, and the text if not. A text that
is not valid UTF-8, or is longer than 255 bytes, is not compressed.

The tool compiles its shim and unishox2.c of 3rdparty/Unishox2 with `cc`
on first use, into work/usx.
"""

import ctypes
import os
import subprocess
from collections import Counter
from pathlib import Path

import click
from blake3 import blake3

from qua_network.interop.record import MODES, decode
from qua_network.legacy_decode import _expand, _records
from qua_network.parallel import jobs_option, map_files

ROOT = Path(__file__).resolve().parents[2]
SHIM = Path(__file__).resolve().parent / "usx_shim.c"
USX = ROOT / "3rdparty" / "Unishox2"
BUILD = ROOT / "work" / "usx"

KINDS = ("comment", "object comment", "status", "message", "bulletin")
REPEAT_KINDS = KINDS[:3]
MAX_TEXT = 255  # the largest value of a TLV (RFC 5.2)

# Script classes by code point, for the result by script of step 11.
_RANGES = (
    (0x0080, 0x024F, "latin"),
    (0x0370, 0x03FF, "greek"),
    (0x0400, 0x052F, "cyrillic"),
    (0x0590, 0x06FF, "hebrew or arabic"),
    (0x0E00, 0x0E7F, "thai"),
    (0x2E80, 0x9FFF, "cjk"),
    (0xAC00, 0xD7AF, "cjk"),
    (0xF900, 0xFAFF, "cjk"),
    (0xFF00, 0xFFEF, "cjk"),
    (0x20000, 0x3FFFF, "cjk"),
)


def script(b):
    """The script class of a text: `ascii`, the class with the most code
    points outside ASCII, `other`, or `not utf-8`."""
    if b.isascii():
        return "ascii"
    try:
        s = b.decode("utf-8")
    except UnicodeDecodeError:
        return "not utf-8"
    seen = Counter()
    for ch in s:
        c = ord(ch)
        if c < 0x80:
            continue
        for lo, hi, name in _RANGES:
            if lo <= c <= hi:
                seen[name] += 1
                break
        else:
            seen["other"] += 1
    return max(sorted(seen), key=lambda k: seen[k])


def _library():
    """Build the shim once for this version of the sources, and load it."""
    h = blake3()
    for src in (SHIM, USX / "unishox2.c", USX / "unishox2.h"):
        h.update(src.read_bytes())
    lib = BUILD / f"libqua_usx-{h.hexdigest()[:12]}.so"
    if not lib.exists():
        BUILD.mkdir(parents=True, exist_ok=True)
        part = lib.with_suffix(f".{os.getpid()}.tmp")
        cmd = ["cc", "-O2", "-shared", "-fPIC", "-DUNISHOX_API_WITH_OUTPUT_LEN=1", f"-I{USX}"]
        subprocess.run(cmd + [str(SHIM), str(USX / "unishox2.c"), "-o", str(part)], check=True)
        os.replace(part, lib)
    dll = ctypes.CDLL(str(lib))
    dll.qua_usx_name.restype = ctypes.c_char_p
    dll.qua_usx_all.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    dll.qua_usx_all.restype = None
    return dll


def presets():
    dll = _library()
    return [dll.qua_usx_name(i).decode("ascii") for i in range(dll.qua_usx_count())]


def _bytes(obj):
    """The bytes of a text value object, or None if it has no value."""
    if not obj or "bytes" not in obj:
        return None
    return obj["bytes"].encode("latin-1")


def texts(rec):
    """Yield (kind, repetition key, bytes) for each text of a record."""
    pos = rec.get("position")
    if pos is not None:
        b = _bytes(pos.get("comment"))
        if b:
            name = _bytes((rec.get("object") or {}).get("name"))
            if "object" in rec["uses"]:
                yield "object comment", (rec["source"], name), b
            else:
                yield "comment", rec["source"], b
    for kind in ("status", "message", "bulletin"):
        body = rec.get(kind)
        if body is not None:
            b = _bytes(body.get("text"))
            if b:
                yield kind, rec["source"], b


class Part:
    """The result of one corpus file."""

    def __init__(self):
        self.packets = 0
        self.truncated = 0
        self.records = Counter()  # "position", "object": records that can hold a comment
        self.rep = Counter()  # (kind, what) -> count; what is texts, bytes, repeats, repeat bytes
        self.first = {}  # (kind, key) -> (digest, length) of the first text of the file
        self.last = {}  # (kind, key) -> digest of the last text of the file
        self.usx = Counter()  # (kind, script, what) -> count
        self.best = Counter()  # (kind, script, preset index) -> texts for which it is the shortest


def stats_file(path, mode):
    part = Part()
    seen = Counter()  # (kind, bytes) -> occurrences in this file
    first, last, rep = part.first, part.last, part.rep
    try:
        for received, line in _records([path]):
            part.packets += 1
            rec = decode(line, received, 1 if received is not None else None, mode)
            if rec.get("position") is not None:
                part.records["object" if "object" in rec["uses"] else "position"] += 1
            for kind, key, b in texts(rec):
                seen[(kind, b)] += 1
                rep[(kind, "texts")] += 1
                rep[(kind, "bytes")] += len(b)
                if kind in REPEAT_KINDS:
                    k = (kind, key)
                    d = blake3(b).digest(8)
                    if k not in first:
                        first[k] = (d, len(b))
                    elif last[k] == d:
                        rep[(kind, "repeats")] += 1
                        rep[(kind, "repeat bytes")] += len(b)
                    last[k] = d
    except EOFError:
        part.truncated = 1
    dll = _library()
    n = dll.qua_usx_count()
    lens = (ctypes.c_int * n)()
    usx, best = part.usx, part.best
    for (kind, b), count in seen.items():
        sc = script(b)
        usx[(kind, sc, "texts")] += count
        usx[(kind, sc, "distinct in a file")] += 1
        usx[(kind, sc, "bytes")] += count * len(b)
        if sc == "not utf-8":
            continue
        if len(b) > MAX_TEXT:
            usx[(kind, sc, "texts over 255 bytes")] += count
            usx[(kind, sc, "bytes over 255 bytes")] += count * len(b)
            continue
        usx[(kind, sc, "texts tried")] += count
        usx[(kind, sc, "bytes tried")] += count * len(b)
        dll.qua_usx_all(b, len(b), lens)
        low, low_i = len(b), None
        for i in range(n):
            c = lens[i]
            if c < 0:
                usx[(kind, sc, "failed", i)] += count
                size = len(b)
            else:
                # RFC 5.7: the length byte counts as part of the compressed form.
                size = min(len(b), c + 1)
            usx[(kind, sc, "size", i)] += count * size
            if size < len(b):
                usx[(kind, sc, "compressed", i)] += count
            if size < low:
                low, low_i = size, i
        usx[(kind, sc, "size with the best preset")] += count * low
        best[(kind, sc, low_i)] += count
    return part


def _merge_repeats(parts, total):
    """Add the repeats across file boundaries. parts are in file order."""
    last = {}
    for part in parts:
        for k, (d, length) in part.first.items():
            if last.get(k) == d:
                total[(k[0], "repeats")] += 1
                total[(k[0], "repeat bytes")] += length
            if k not in last:
                total[(k[0], "keys")] += 1
        last.update(part.last)


def _pct(a, b):
    return f"{a / b * 100:7.3f}%" if b else "       -"


def _report(parts, files, mode, names):
    echo = click.echo
    packets = sum(p.packets for p in parts)
    truncated = sum(p.truncated for p in parts)
    records, rep, usx, best = Counter(), Counter(), Counter(), Counter()
    for p in parts:
        records.update(p.records)
        rep.update(p.rep)
        usx.update(p.usx)
        best.update(p.best)
    _merge_repeats(parts, rep)
    echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}  files={len(files)}  truncated={truncated}")
    echo(f"mode={mode}  packets={packets}")
    echo(f"records with a position: station={records['position']}  object={records['object']}")

    echo("\n== texts: kind, texts, bytes, mean bytes ==")
    for kind in KINDS:
        t, b = rep[(kind, "texts")], rep[(kind, "bytes")]
        echo(f"  {kind:16s} {t:12d} {b:14d} {b / t if t else 0:8.1f}")
    echo(f"  station positions with a comment: {_pct(rep[('comment', 'texts')], records['position'])}")
    echo(f"  object positions with a comment:  {_pct(rep[('object comment', 'texts')], records['object'])}")

    echo("\n== repetition: kind, keys, texts, repeats, share of texts, repeat bytes, share of bytes ==")
    for kind in REPEAT_KINDS:
        t, b = rep[(kind, "texts")], rep[(kind, "bytes")]
        r, rb = rep[(kind, "repeats")], rep[(kind, "repeat bytes")]
        echo(f"  {kind:16s} {rep[(kind, 'keys')]:9d} {t:12d} {r:12d} {_pct(r, t)} {rb:14d} {_pct(rb, b)}")

    echo("\n== scripts: kind, script, texts, bytes, texts tried, bytes tried, texts over 255 bytes ==")
    scripts = sorted({(k[0], k[1]) for k in usx}, key=lambda k: (KINDS.index(k[0]), -usx[(k[0], k[1], "texts")]))
    for kind, sc in scripts:
        g = lambda what: usx[(kind, sc, what)]  # noqa: E731
        echo(
            f"  {kind:16s} {sc:18s} {g('texts'):12d} {g('bytes'):14d} {g('texts tried'):12d} {g('bytes tried'):14d} {g('texts over 255 bytes'):8d}"
        )

    groups = [("all kinds", "all scripts", [k for k in scripts])]
    groups += [(kind, "all scripts", [k for k in scripts if k[0] == kind]) for kind in KINDS]
    for sc in sorted({k[1] for k in scripts if k[1] != "not utf-8"}):
        groups.append(("all kinds", sc, [k for k in scripts if k[1] == sc]))
    echo("\n== Unishox2: size of the tried texts under each preset (RFC 5.7 rule) ==")
    echo("   size: share of the bytes tried.  compressed: share of the texts tried that are shorter compressed.")
    for kind, sc, members in groups:
        tried = sum(usx[(k, s, "bytes tried")] for k, s in members)
        texts_tried = sum(usx[(k, s, "texts tried")] for k, s in members)
        if not tried:
            continue
        echo(f"\n  {kind}, {sc}: texts tried={texts_tried}  bytes tried={tried}")
        low = sum(usx[(k, s, "size with the best preset")] for k, s in members)
        echo(f"    {'best preset for each text':26s} {low:14d} {_pct(low, tried)}")
        rows = []
        for i, name in enumerate(names):
            size = sum(usx[(k, s, "size", i)] for k, s in members)
            comp = sum(usx[(k, s, "compressed", i)] for k, s in members)
            fail = sum(usx[(k, s, "failed", i)] for k, s in members)
            wins = sum(best[(k, s, i)] for k, s in members)
            rows.append((size, i, name, comp, fail, wins))
        echo(f"    {'preset':26s} {'size':>14s} {'share':>8s} {'compressed':>11s} {'shortest for':>13s} {'failed':>8s}")
        for size, i, name, comp, fail, wins in sorted(rows):
            echo(
                f"    {i:2d} {name:23s} {size:14d} {_pct(size, tried)} {_pct(comp, texts_tried):>11s} {_pct(wins, texts_tried):>13s} {fail:8d}"
            )
        none = sum(best[(k, s, None)] for k, s in members)
        echo(f"    {'no preset is shorter':26s} {'':14s} {'':8s} {'':11s} {_pct(none, texts_tried):>13s}")


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--mode", type=click.Choice(MODES), default="permissive", show_default=True, help="Mode of the decoder (01-record section 3)."
)
@jobs_option
def cli(paths, mode, jobs):
    files = _expand(paths)
    if not files:
        raise click.ClickException("no corpus files found")
    names = presets()  # builds the library before the workers start
    done = {}
    for path, part in map_files(_Task(mode), files, jobs):
        if part.truncated:
            click.echo(f"warning: {path} is truncated; using data read so far", err=True)
        done[path] = part
    _report([done[f] for f in files], files, mode, names)


class _Task:
    """A picklable call of stats_file."""

    def __init__(self, mode):
        self.mode = mode

    def __call__(self, path):
        return stats_file(path, self.mode)
