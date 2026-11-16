# SPDX-License-Identifier: Apache-2.0
"""Distribution of the values of the records (docs/interop/01-record.md).

Every packet is decoded into a record. The tool counts, over all input
files and for each field of each body:

- for a quantity: the values by their resolution `res`, the values by a
  band of `v`, and the smallest and the largest `v`;
- for a code or a flag: the values by their content.

For the position body it also counts the records by the set of parts that
give a value: altitude, course, speed, a comment that is not empty, each
extension, and the other bodies of the record.

A band of `v` has the edges 1, 2 and 5 times a power of ten. The band
`[20, 50)` holds each `v` from 20 up to, but not including, 50. A marked
value of permissive mode counts as a value. A field with no value is not
counted here; `qua-legacy-decode --stats` counts those.

The tool prints counts only, and no content of a packet except the codes.
The input file range and the packet count are printed with the results.
One corpus file is one unit of work.
"""

import math
import os
from collections import Counter
from functools import partial

import click

from qua_network.interop.record import MODES, decode
from qua_network.legacy_decode import BODY_FIELDS, LOGGED_RES
from qua_network.parallel import jobs_option, map_files
from qua_network.tnc2 import log_files, read_records, split_record

try:
    import pypyjit
except ImportError:
    pass
else:
    # As qua-legacy-fields: bridges compiled sooner, set at import for the
    # pool workers.
    pypyjit.set_param("decay=0,trace_eagerness=50")

# The base resolution of an uncompressed position, 1/6000 degree, with a
# margin for the arithmetic of doubles.
FINE = 1 / 6000 * 0.999

# The codes of a field are counted up to this many different contents, so
# that a field with free content cannot fill the memory.
CODE_LIMIT = 4096


def _band(v):
    """The band of v as (sign, power of ten, index of the edge 1, 2 or 5).
    Zero is (0, 0, 0)."""
    if v == 0:
        return (0, 0, 0)
    a = abs(v)
    p = math.floor(math.log10(a))
    m = a / 10.0**p
    if m >= 10:  # log10 rounded down at a power of ten
        p, m = p + 1, m / 10
    elif m < 1:
        p, m = p - 1, m * 10
    return (1 if v > 0 else -1, p, 0 if m < 2 else 1 if m < 5 else 2)


def _band_text(band):
    sign, p, i = band
    if sign == 0:
        return "0"
    lo = (1, 2, 5)[i] * 10.0**p
    hi = (2, 5, 10)[i] * 10.0**p
    return f"[{lo:g}, {hi:g})" if sign > 0 else f"(-{hi:g}, -{lo:g}]"


class Dist:
    def __init__(self):
        self.packets = 0
        self.truncated = 0
        self.bodies = Counter()  # body name -> records
        self.res = Counter()  # (field, res) -> values
        self.bands = Counter()  # (field, band) -> values
        self.low = {}  # field -> smallest v
        self.high = {}  # field -> largest v
        self.codes = Counter()  # (field, content) -> values
        self.parts = Counter()  # parts of a position body -> records

    def _value(self, field, o):
        if "v" in o:
            v = o["v"]
            self.res[(field, float(f"{o['res']:.6g}"))] += 1
            self.bands[(field, _band(v))] += 1
            if field not in self.low or v < self.low[field]:
                self.low[field] = v
            if field not in self.high or v > self.high[field]:
                self.high[field] = v
        elif "code" in o or "flag" in o:
            key = (field, repr(o["code"]) if "code" in o else repr(o["flag"]))
            if key in self.codes or len(self.codes) < CODE_LIMIT:
                self.codes[key] += 1
            else:
                self.codes[(field, "(other)")] += 1
        if "ref" in o:
            self.codes[(field + " ref", repr(o["ref"]))] += 1

    def add(self, rec):
        self.packets += 1
        for use, fields in BODY_FIELDS.items():
            body = rec.get(use)
            if body is None:
                continue
            self.bodies[use] += 1
            for name in fields:
                o = body.get(name)
                if o is None:
                    continue
                for item in o if isinstance(o, list) else (o,):
                    self._value(f"{use}.{name}", item)
            for item in body.get("extensions", ()):
                for name, o in item["values"].items():
                    self._value(f"{use} {item['rule']} {name}", o)
        pos = rec.get("position")
        if pos is not None:
            self.parts[self._parts(rec, pos)] += 1

    @staticmethod
    def _parts(rec, pos):
        parts = set()
        lat = pos.get("lat")
        if lat is None or "v" not in lat:
            parts.add("no-latitude")
        elif lat["res"] < FINE:
            parts.add("fine")
        amb = pos.get("ambiguity")
        if amb is not None and amb.get("code"):
            parts.add("ambiguity")
        if any("v" in a for a in pos.get("altitude", ())):
            parts.add("altitude")
        for name in ("course", "speed"):
            o = pos.get(name)
            if o is not None and "v" in o:
                parts.add(name)
        cmt = pos.get("comment")
        if cmt is not None and cmt.get("bytes"):
            parts.add("comment")
        for item in pos.get("extensions", ()):
            if any("why" not in o for o in item["values"].values()):
                parts.add(item["rule"])
        for use in rec["uses"]:
            if use != "position":
                parts.add("+" + use)
        return " ".join(sorted(parts)) or "-"

    def merge(self, o):
        self.packets += o.packets
        self.truncated += o.truncated
        self.bodies.update(o.bodies)
        self.res.update(o.res)
        self.bands.update(o.bands)
        self.codes.update(o.codes)
        self.parts.update(o.parts)
        for field, v in o.low.items():
            if field not in self.low or v < self.low[field]:
                self.low[field] = v
        for field, v in o.high.items():
            if field not in self.high or v > self.high[field]:
                self.high[field] = v


def dist_file(path, mode):
    d = Dist()
    try:
        for record in read_records(path):
            ts, line = split_record(record)
            received = float(ts) if ts is not None else None
            d.add(decode(line, received, LOGGED_RES if received is not None else None, mode))
    except EOFError:
        d.truncated = 1
    return d


def _report(d, files, mode, top):
    echo = click.echo
    echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}  files={len(files)}  truncated={d.truncated}")
    bodies = "  ".join(f"{use}={d.bodies[use]}" for use in BODY_FIELDS)
    echo(f"mode={mode}  packets={d.packets}  records with a body: {bodies}")

    def total(counter, field):
        return sum(c for (f, _), c in counter.items() if f == field)

    echo("\n== quantities: field, values, smallest v, largest v ==")
    fields = sorted({f for f, _ in d.res})
    for field in fields:
        echo(f"  {field:40s} {total(d.res, field):10d}  {d.low[field]:.9g}  {d.high[field]:.9g}")

    echo(f"\n== resolution: field, res, 1/res, values, share of the values of the field (the {top} most frequent) ==")
    for field in fields:
        n = total(d.res, field)
        rows = sorted(((c, r) for (f, r), c in d.res.items() if f == field), key=lambda cr: (-cr[0], cr[1]))
        for c, r in rows[:top]:
            echo(f"  {field:40s} {r:<14.6g} {(1 / r if r else 0):<12.6g} {c:10d}  {c / n * 100:7.3f}%")
        if len(rows) > top:
            rest = sum(c for c, _ in rows[top:])
            echo(f"  {field:40s} {'(other)':14s} {len(rows) - top:<12d} {rest:10d}  {rest / n * 100:7.3f}%")

    echo("\n== bands of v: field, band, values, share of the values of the field ==")
    for field in fields:
        n = total(d.bands, field)
        for band, c in sorted(((b, c) for (f, b), c in d.bands.items() if f == field), key=lambda bc: _band_order(bc[0])):
            echo(f"  {field:40s} {_band_text(band):20s} {c:10d}  {c / n * 100:7.3f}%")

    echo(f"\n== codes and flags: field, content, values, share of the values of the field (the {top} most frequent) ==")
    for field in sorted({f for f, _ in d.codes}):
        n = total(d.codes, field)
        rows = sorted(((c, k) for (f, k), c in d.codes.items() if f == field), key=lambda ck: (-ck[0], ck[1]))
        for c, k in rows[:top]:
            echo(f"  {field:40s} {k:16s} {c:10d}  {c / n * 100:7.3f}%")
        if len(rows) > top:
            rest = sum(c for c, _ in rows[top:])
            echo(f"  {field:40s} (other, {len(rows) - top}) {rest:10d}  {rest / n * 100:7.3f}%")

    n = d.bodies["position"] or 1
    echo("\n== position bodies: parts with a value, records, share of the position bodies (the 60 most frequent) ==")
    rows = sorted(d.parts.items(), key=lambda kv: (-kv[1], kv[0]))
    for parts, c in rows[:60]:
        echo(f"  {c:10d}  {c / n * 100:7.3f}%  {parts}")
    if len(rows) > 60:
        rest = sum(c for _, c in rows[60:])
        echo(f"  {rest:10d}  {rest / n * 100:7.3f}%  (other, {len(rows) - 60} sets)")
    echo("\n== position bodies: part, records with the part, share of the position bodies ==")
    single = Counter()
    for parts, c in d.parts.items():
        for part in parts.split():
            single[part] += c
    for part, c in sorted(single.items(), key=lambda kv: (-kv[1], kv[0])):
        echo(f"  {part:24s} {c:10d}  {c / n * 100:7.3f}%")


def _band_order(band):
    sign, p, i = band
    return (sign, sign * (p * 3 + i))


def _expand(paths):
    files = []
    for p in paths:
        files.extend(log_files(p) if os.path.isdir(p) else [p])
    return sorted(set(files), key=os.path.basename)


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--mode", type=click.Choice(MODES), default="strict", show_default=True, help="Strict or permissive mode (01-record section 3)."
)
@click.option(
    "--top", type=click.IntRange(min=1), default=12, show_default=True, help="Rows for each field in the lists by frequency."
)
@jobs_option
def cli(paths, mode, top, jobs):
    files = _expand(paths)
    if not files:
        raise click.ClickException("no corpus files found")
    d = Dist()
    for path, part in map_files(partial(dist_file, mode=mode), files, jobs):
        if part.truncated:
            click.echo(f"warning: {path} is truncated; using data read so far", err=True)
        d.merge(part)
    _report(d, files, mode, top)


if __name__ == "__main__":
    cli()
