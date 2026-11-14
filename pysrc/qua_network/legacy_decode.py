# SPDX-License-Identifier: Apache-2.0
"""Decode legacy packets into records (docs/interop/01-record.md).

Reads TNC2 lines from corpus files (records with or without the logged
time) or from standard input, and writes one JSON object per line, one
record per line (01-record section 8). The logged time of a corpus record
is the received time, with the resolution 0.001 s (section 2). Only the
position slice has a body: position reports, DF reports and Mic-E.

With --stats no record is written. Instead the tool counts, over all input
files: packets, records with a position body, and for each field of the
position body, each extension value and report_time how many give a
value, a marked value (permissive mode) or no value, grouped by the items
of `mark` and `why`; and the count of each note. The input file range and
the packet count are printed with the results. One corpus file is one unit
of work, and -j applies to --stats only: records are written in input
order by one process.
"""

import os
import sys
from collections import Counter
from functools import partial

import click
from tqdm import tqdm

from qua_network.interop.record import MODES, decode
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

# 01-record section 2: the resolution of the logged decimal.
LOGGED_RES = 0.001


def _records(paths):
    """(received or None, line) for each input record."""
    if not paths:
        for raw in sys.stdin.buffer:
            yield _split(raw.rstrip(b"\r\n"))
        return
    for p in paths:
        for record in read_records(p):
            yield _split(record)


def _split(record):
    ts, line = split_record(record)
    return (float(ts) if ts is not None else None), line


def _decode(received, line, mode):
    return decode(line, received, LOGGED_RES if received is not None else None, mode)


def _json(value):
    """JSON text of plain data. Each double is written with the digits of
    repr, which give the same double back (01-record section 4.6)."""
    import json

    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


# --- Statistics ---------------------------------------------------------

BODY_FIELDS = ("lat", "lon", "ambiguity", "datum", "altitude", "course", "speed", "symbol", "messaging", "fix", "comment")


def _key(item):
    """A `why` or `mark` item without its offset."""
    return f"{item[0]} {item[1]}" if isinstance(item, list) else item


def _status(o):
    if "why" in o:
        return "no value", " + ".join(sorted({_key(i) for i in o["why"]})) or "-"
    if "mark" in o:
        return "marked", " + ".join(sorted({_key(i) for i in o["mark"]}))
    return "value", ""


class Stats:
    def __init__(self):
        self.packets = 0
        self.bodies = 0
        self.truncated = 0
        self.values = Counter()  # (field, status, detail) -> values
        self.notes = Counter()  # row -> notes

    def add(self, rec):
        self.packets += 1
        rt = rec.get("report_time")
        if rt is not None:
            self.values[("report_time",) + _status(rt)] += 1
        for row, _ in rec["notes"]:
            self.notes[row] += 1
        body = rec.get("position")
        if body is None:
            return
        self.bodies += 1
        for name in BODY_FIELDS:
            o = body.get(name)
            if o is None:
                continue
            for item in o if isinstance(o, list) else (o,):
                self.values[(name,) + _status(item)] += 1
        for item in body["extensions"]:
            for name, o in item["values"].items():
                self.values[(f"{item['rule']} {name}",) + _status(o)] += 1

    def merge(self, o):
        self.packets += o.packets
        self.bodies += o.bodies
        self.truncated += o.truncated
        self.values.update(o.values)
        self.notes.update(o.notes)


def stats_file(path, mode):
    st = Stats()
    try:
        for received, line in _records([path]):
            st.add(_decode(received, line, mode))
    except EOFError:
        st.truncated = 1
    return st


def _report(st, files, mode):
    echo = click.echo
    if files:
        echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}  files={len(files)}  truncated={st.truncated}")
    else:
        echo("input: standard input")
    echo(f"mode={mode}  packets={st.packets}  records with a position body={st.bodies}")
    echo("\n== values: field, status, count, share of position bodies (of packets for report_time); detail (mark or why items) ==")
    order = {s: i for i, s in enumerate(("value", "marked", "no value"))}
    for (field, status, detail), c in sorted(st.values.items(), key=lambda kv: (kv[0][0], order[kv[0][1]], -kv[1], kv[0][2])):
        n = (st.packets if field == "report_time" else st.bodies) or 1
        echo(f"  {field:28s} {status:9s} {c:10d}  {c / n * 100:7.3f}%  {detail}")
    echo("\n== notes: row, count ==")
    for row, c in sorted(st.notes.items(), key=lambda kv: (-kv[1], kv[0])):
        echo(f"  {row:24s} {c:10d}")


def _expand(paths):
    files = []
    for p in paths:
        files.extend(log_files(p) if os.path.isdir(p) else [p])
    return sorted(set(files), key=os.path.basename)


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--mode", type=click.Choice(MODES), default="strict", show_default=True, help="Strict or permissive mode (01-record section 3)."
)
@click.option("-n", "--limit", type=click.IntRange(min=1), help="Stop after this many records. Not with --stats.")
@click.option("--stats", is_flag=True, help="Print counts instead of records.")
@jobs_option
def cli(paths, mode, limit, stats, jobs):
    files = _expand(paths)
    if paths and not files:
        raise click.ClickException("no corpus files found")
    if stats:
        if limit:
            raise click.UsageError("--limit applies to record output only")
        st = Stats()
        if files:
            for path, part in map_files(partial(stats_file, mode=mode), files, jobs):
                if part.truncated:
                    click.echo(f"warning: {path} is truncated; using data read so far", err=True)
                st.merge(part)
        else:
            for received, line in _records([]):
                st.add(_decode(received, line, mode))
        _report(st, files, mode)
        return
    out = sys.stdout.buffer
    n = 0
    for path in tqdm(files, unit="file") if files else [None]:
        try:
            for received, line in _records([path] if path else []):
                if limit and n >= limit:
                    break
                out.write(_json(_decode(received, line, mode)).encode("utf-8") + b"\n")
                n += 1
        except EOFError:
            # As --stats: keep the records read so far and go on.
            tqdm.write(f"warning: {path} is truncated; using data read so far", file=sys.stderr)
        if limit and n >= limit:
            break
    out.flush()


if __name__ == "__main__":
    cli()
