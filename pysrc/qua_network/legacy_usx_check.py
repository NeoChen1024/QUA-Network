# SPDX-License-Identifier: Apache-2.0
"""Check the text compression of docs/spec/04-text-compression.md against
the Unishox2 library, on the free text of the corpus.

For each text of a record (valid UTF-8, 1 to 255 bytes) the tool does
these checks. A text counts once for each corpus file that has it.

Library output: usx.decode() gives the text for the output of the library
with the preset USX_PSET_DFLT, or it rejects the output because the
library used a part that the specification leaves out (a template,
hexadecimal digits, a UUID).

Encoder: if usx.decode() does not reject the output of the library, the
bytes of usx.encode() are equal to it. For every text, usx.decode() and
the decoder of the library both give the text for the bytes of
usx.encode().

Simple encoder: the same two decoders give the text for the bytes of
usx.encode(simple=True).

Size: the size of the texts under the rule of RFC 5.7, and the size if a
sender compresses every text.

Parts: which optional parts of the format the output of usx.encode() uses.

Mutations: the tool changes the output of usx.encode() (one bit, one byte
less, one byte more, the length byte one more or one less). If
usx.decode() gives a text for the changed input, the library must give
the same bytes at the start of its output. The changes are a function of
the text, so a run gives the same result each time.

The tool builds its shim and unishox2.c of 3rdparty/Unishox2 with `cc` on
first use, as qua-legacy-text does.
"""

import ctypes
import os
import random
import subprocess
from collections import Counter

import click
from blake3 import blake3

from qua_network import usx
from qua_network.interop.record import MODES, decode
from qua_network.legacy_decode import _expand, _records
from qua_network.legacy_text import MAX_TEXT, USX, _library, _pct, texts
from qua_network.parallel import jobs_option, map_files

BUF = 4096
MUTATIONS = ("one bit", "one byte less", "one byte more", "length + 1", "length - 1")
LEFT_OUT = ("a template", "hexadecimal digits", "a UUID")  # reasons of usx.Malformed


class Part:
    """The result of one corpus file."""

    def __init__(self):
        self.packets = 0
        self.truncated = 0
        self.n = Counter()


def _mutate(rng, kind, data, n):
    if kind == "one bit":
        i = rng.randrange(8 * len(data))
        out = bytearray(data)
        out[i >> 3] ^= 0x80 >> (i & 7)
        return bytes(out), n
    if kind == "one byte less":
        return data[:-1], n
    if kind == "one byte more":
        return data + bytes((rng.randrange(256),)), n
    return data, n + (1 if kind == "length + 1" else -1)


def check_file(path, mode, mutations):
    part = Part()
    n = part.n
    seen = Counter()
    try:
        for received, line in _records([path]):
            part.packets += 1
            rec = decode(line, received, 1 if received is not None else None, mode)
            for _kind, _key, b in texts(rec):
                seen[b] += 1
    except EOFError:
        part.truncated = 1
    dll = _library()
    for f in (dll.qua_usx_dflt_compress, dll.qua_usx_dflt_decompress):
        f.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        f.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(BUF)

    def library_decode(data):
        """(return value, the buffer) of the library decoder."""
        ctypes.memset(buf, 0, BUF)
        r = dll.qua_usx_dflt_decompress(data, len(data), buf, BUF)
        return r, buf.raw

    for b, count in seen.items():
        size = len(b)
        if size > MAX_TEXT:
            n["texts over 255 bytes"] += 1
            continue
        try:
            b.decode("utf-8")
        except UnicodeDecodeError:
            n["texts not utf-8"] += 1
            continue
        n["texts"] += 1
        n["texts by packet"] += count
        n["bytes by packet"] += count * size
        r = dll.qua_usx_dflt_compress(b, size, buf, BUF)
        if not 0 < r <= BUF:
            n["library encoder fails"] += 1
            continue
        ref = buf.raw[:r]
        n["size: library"] += count * min(size, r + 1)

        try:
            valid = usx.decode(ref, size) == b
            n["library output: decoder gives the text" if valid else "library output: decoder differs"] += 1
        except usx.Malformed as e:
            valid = False
            if str(e) in LEFT_OUT:
                n["library output: uses a part that is left out"] += 1
                n[("left out", str(e), "texts")] += 1
                n[("left out", str(e), "texts by packet")] += count
            else:
                n[f"library output: decoder rejects ({e})"] += 1

        mine = usx.encode(b)
        if valid:
            n["encoder: equal to the library" if mine == ref else "encoder: differs from the library"] += 1
        n["size: encoder"] += count * min(size, len(mine) + 1)
        n["size: encoder, every text compressed"] += count * (len(mine) + 1)
        if len(mine) + 1 < size:
            n["compressed form is shorter: texts by packet"] += count
        events = {}
        try:
            ok = usx.decode(mine, size, events) == b
        except usx.Malformed:
            ok = False
        n["encoder: decoder gives the text" if ok else "encoder: decoder differs"] += 1
        r, raw = library_decode(mine)
        n["encoder: library gives the text" if raw[: max(r, 0)] == b else "encoder: library differs"] += 1
        for name in events:
            n[("part", name, "texts")] += 1
            n[("part", name, "texts by packet")] += count
        if not events:
            n[("part", "none", "texts")] += 1
            n[("part", "none", "texts by packet")] += count

        simple = usx.encode(b, simple=True)
        n["size: simple encoder"] += count * min(size, len(simple) + 1)
        try:
            ok = usx.decode(simple, size) == b
        except usx.Malformed:
            ok = False
        n["simple encoder: decoder gives the text" if ok else "simple encoder: decoder differs"] += 1
        r, raw = library_decode(simple)
        n["simple encoder: library gives the text" if raw[: max(r, 0)] == b else "simple encoder: library differs"] += 1

        if mutations:
            rng = random.Random(int.from_bytes(blake3(b).digest(8), "big"))
            for _ in range(mutations):
                kind = rng.choice(MUTATIONS)
                data, length = _mutate(rng, kind, mine, size)
                n[("mutation", kind, "inputs")] += 1
                try:
                    got = usx.decode(data, length)
                except usx.Malformed as e:
                    n[("mutation", kind, "rejects")] += 1
                    n[("reject", str(e))] += 1
                    continue
                r, raw = library_decode(data)
                if r >= length and raw[:length] == got:
                    n[("mutation", kind, "accepts, library agrees")] += 1
                else:
                    n[("mutation", kind, "accepts, library differs")] += 1
    return part


def _library_commit():
    r = subprocess.run(["git", "-C", str(USX), "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def _report(parts, files, mode, mutations):
    echo = click.echo
    n = Counter()
    for p in parts:
        n.update(p.n)
    packets = sum(p.packets for p in parts)
    truncated = sum(p.truncated for p in parts)
    echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}  files={len(files)}  truncated={truncated}")
    echo(f"mode={mode}  packets={packets}  library commit={_library_commit()}  mutations for each text={mutations}")
    t = n["texts"]
    echo(f"texts checked={t}  (a text counts once for each file)  by packet={n['texts by packet']}")
    echo(f"not checked: over 255 bytes={n['texts over 255 bytes']}  not utf-8={n['texts not utf-8']}")

    echo("\n== checks: texts ==")
    echo(f"  {'library encoder fails':50s} {n['library encoder fails']:12d}")
    for k in sorted(k for k in n if isinstance(k, str) and ":" in k and not k.startswith(("size", "compressed"))):
        echo(f"  {k:50s} {n[k]:12d}")

    echo("\n== parts that are left out, in the output of the library: texts, share, by packet, share ==")
    for name in LEFT_OUT:
        a, b = n[("left out", name, "texts")], n[("left out", name, "texts by packet")]
        echo(f"  {name:18s} {a:12d} {_pct(a, t)} {b:12d} {_pct(b, n['texts by packet'])}")

    echo("\n== size by packet: bytes, share of the text bytes ==")
    total = n["bytes by packet"]
    echo(f"  {'text':38s} {total:14d}")
    for k in ("size: library", "size: encoder", "size: simple encoder", "size: encoder, every text compressed"):
        echo(f"  {k[6:]:38s} {n[k]:14d} {_pct(n[k], total)}")
    k = "compressed form is shorter: texts by packet"
    echo(f"  {k:38s} {n[k]:14d} {_pct(n[k], n['texts by packet'])}")

    echo("\n== optional parts in the output of the encoder: texts, share, by packet, share ==")
    names = sorted({k[1] for k in n if isinstance(k, tuple) and k[0] == "part"}, key=lambda x: -n[("part", x, "texts")])
    for name in names:
        a, b = n[("part", name, "texts")], n[("part", name, "texts by packet")]
        echo(f"  {name:18s} {a:12d} {_pct(a, t)} {b:12d} {_pct(b, n['texts by packet'])}")

    if mutations:
        echo("\n== mutations: kind, inputs, rejects, accepts and the library agrees, accepts and the library differs ==")
        for kind in MUTATIONS:
            g = lambda what: n[("mutation", kind, what)]  # noqa: E731
            echo(
                f"  {kind:16s} {g('inputs'):12d} {g('rejects'):12d} {g('accepts, library agrees'):12d} {g('accepts, library differs'):8d}"
            )
        echo("\n== mutations: reason of the reject ==")
        for k, v in sorted(((k[1], v) for k, v in n.items() if isinstance(k, tuple) and k[0] == "reject"), key=lambda kv: -kv[1]):
            echo(f"  {k:56s} {v:12d}")


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--mode", type=click.Choice(MODES), default="permissive", show_default=True, help="Mode of the decoder (01-record section 3)."
)
@click.option("--mutations", type=click.IntRange(0), default=4, show_default=True, help="Changed inputs for each text.")
@jobs_option
def cli(paths, mode, mutations, jobs):
    files = _expand(paths)
    if not files:
        raise click.ClickException("no corpus files found")
    _library()  # builds the library before the workers start
    done = {}
    for path, part in map_files(_Task(mode, mutations), files, jobs):
        if part.truncated:
            click.echo(f"warning: {path} is truncated; using data read so far", err=True)
        done[path] = part
    _report([done[f] for f in files], files, mode, mutations)


class _Task:
    """A picklable call of check_file."""

    def __init__(self, mode, mutations):
        self.mode = mode
        self.mutations = mutations

    def __call__(self, path):
        return check_file(path, self.mode, self.mutations)
