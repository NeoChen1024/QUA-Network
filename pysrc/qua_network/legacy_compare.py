# SPDX-License-Identifier: Apache-2.0
"""Compare the records of the decoder with the results of other parsers
(docs/interop/09-comparison.md).

Reads TNC2 lines from corpus files. For each packet, the tool decodes a
record (docs/interop/01-record.md) and runs each other parser on the same
line, through its adapter program. The parsers are in submodules under
3rdparty/. The tool counts, for each parser:

- the packets that both decode, that only one decodes, and that neither
  decodes;
- for each compared field, the packets on which the two values agree or
  differ, and those on which only one side has a value.

With --samples, the tool also prints example lines for each count. These
lines are corpus lines: do not copy their callsigns into a document.
"""
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from functools import partial
from pathlib import Path

import click

from qua_network.interop.compare import OUTCOMES, RECORD_CLASSES, VIEWS, compare, record_view
from qua_network.interop.record import MODES
from qua_network.legacy_decode import _decode, _expand, _records
from qua_network.parallel import jobs_option, map_files

ADAPTERS = Path(__file__).resolve().parent / "interop" / "adapters"
THIRDPARTY = Path(__file__).resolve().parents[2] / "3rdparty"
# Parser name -> (submodule, command before the library directory).
PARSERS = {
    "pythonlib": ("aprs-python", [sys.executable, "-I", str(ADAPTERS / "pythonlib.py")]),
    "fap": ("perl-aprs-fap", ["perl", str(ADAPTERS / "fap.pl")]),
}


class Result:
    def __init__(self):
        self.packets = 0
        self.truncated = 0
        self.counts = Counter()  # (parser, path, outcome) -> packets
        self.samples = {}  # (parser, path, outcome) -> [(line, ours, theirs)]

    def merge(self, o, limit):
        self.packets += o.packets
        self.truncated += o.truncated
        self.counts.update(o.counts)
        for key, items in sorted(o.samples.items()):
            have = self.samples.setdefault(key, [])
            have.extend(items[: limit - len(have)])


def _show(value):
    return None if value is None else value[1]


def compare_file(path, mode, parsers, thirdparty, samples):
    res = Result()
    with tempfile.TemporaryDirectory() as tmp:
        # The adapters read the same lines, as hexadecimal digits.
        hexfile = os.path.join(tmp, "lines.hex")
        try:
            with open(hexfile, "wb") as f:
                for _, line in _records([path]):
                    f.write(line.hex().encode("ascii") + b"\n")
        except EOFError:
            res.truncated = 1
        procs = {}
        for name in parsers:
            sub, cmd = PARSERS[name]
            procs[name] = subprocess.Popen(
                cmd + [os.path.join(thirdparty, sub)], stdin=open(hexfile, "rb"), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
        try:
            for received, line in _records([path]):
                res.packets += 1
                rec = _decode(received, line, mode)
                ours = record_view(rec)
                for name in parsers:
                    raw = procs[name].stdout.readline()
                    if not raw:
                        raise click.ClickException(f"the adapter of {name} stopped at packet {res.packets} of {path}")
                    theirs, decoded = VIEWS[name](json.loads(raw))
                    cls = RECORD_CLASSES[(0 if rec["uses"] else 2) + (0 if decoded else 1)]
                    pairs = [("record", cls)] + (compare(ours, theirs) if rec["uses"] and decoded else [])
                    for field, outcome in pairs:
                        key = (name, field, outcome)
                        res.counts[key] += 1
                        if samples and len(res.samples.setdefault(key, [])) < samples:
                            res.samples[key].append((line.decode("latin-1"), _show(ours.get(field)), _show(theirs.get(field))))
        except EOFError:
            res.truncated = 1
        finally:
            for p in procs.values():
                p.stdout.close()
                p.kill()
                p.wait()
    return res


def _commit(thirdparty, sub):
    try:
        out = subprocess.run(["git", "-C", os.path.join(thirdparty, sub), "rev-parse", "HEAD"], capture_output=True, text=True)
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def _report(res, files, mode, parsers, thirdparty):
    echo = click.echo
    echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}  files={len(files)}  truncated={res.truncated}")
    echo(f"mode={mode}  packets={res.packets}")
    for name in parsers:
        echo(f"\n== parser {name}: 3rdparty/{PARSERS[name][0]} at {_commit(thirdparty, PARSERS[name][0])} ==")
        echo("  records: " + "  ".join(f"{c}={res.counts[(name, 'record', c)]}" for c in RECORD_CLASSES))
        echo(f"  {'field':28s}" + "".join(f"{o:>13s}" for o in OUTCOMES) + "   differ share")
        fields = sorted({f for (p, f, _) in res.counts if p == name and f != "record"})
        for field in fields:
            c = [res.counts[(name, field, o)] for o in OUTCOMES]
            both = c[0] + c[1]
            share = f"{c[1] / both * 100:8.3f}%" if both else "        -"
            echo(f"  {field:28s}" + "".join(f"{x:13d}" for x in c) + f"   {share}")
    if res.samples:
        echo("\n== samples: parser, field, outcome; line; ours; theirs ==")
        for (name, field, outcome), items in sorted(res.samples.items()):
            for line, ours, theirs in items:
                echo(f"  {name} {field} {outcome}\n    {line!r}\n    ours={ours!r}\n    theirs={theirs!r}")


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--mode", type=click.Choice(MODES), default="permissive", show_default=True, help="Mode of the decoder (01-record section 3)."
)
@click.option(
    "--parser", "parsers", multiple=True, type=click.Choice(sorted(PARSERS)), help="Parser to compare with. Default: all."
)
@click.option("--samples", type=click.IntRange(min=0), default=0, show_default=True, help="Example lines to print for each count.")
@click.option(
    "--thirdparty",
    type=click.Path(exists=True, file_okay=False),
    default=str(THIRDPARTY),
    show_default=True,
    help="Directory of the parser submodules.",
)
@jobs_option
def cli(paths, mode, parsers, samples, thirdparty, jobs):
    files = _expand(paths)
    if not files:
        raise click.ClickException("no corpus files found")
    parsers = tuple(parsers) or tuple(sorted(PARSERS))
    thirdparty = os.path.abspath(thirdparty)
    res = Result()
    func = partial(compare_file, mode=mode, parsers=parsers, thirdparty=thirdparty, samples=samples)
    for path, part in map_files(func, files, jobs):
        if part.truncated:
            click.echo(f"warning: {path} is truncated; using data read so far", err=True)
        res.merge(part, samples)
    _report(res, files, mode, parsers, thirdparty)


if __name__ == "__main__":
    cli()
