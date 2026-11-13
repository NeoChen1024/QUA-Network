# SPDX-License-Identifier: Apache-2.0
"""Show how the legacy tokenizer reads packets, token by token.

Reads TNC2 lines from corpus files (records with or without the logged
time) or from standard input, and prints for each line its tokens, nested
by depth, its findings and its verdict. Rule IDs are those of
docs/legacy/; a "residue" token names the rule at which reading stopped,
and "unread" means the format's reader is not written yet, so the packet
has no verdict.

With --json each line becomes one JSON object, with byte offsets into the
line and the bytes of each token as a latin-1 string.
"""

import json
import sys

import click

from qua_network.legacy.tokenizer import show_bytes, tokenize
from qua_network.tnc2 import read_records, split_record


def _lines(paths):
    if not paths:
        for raw in sys.stdin.buffer:
            yield raw.rstrip(b"\r\n")
        return
    for p in paths:
        for record in read_records(p):
            yield split_record(record)[1]


def _text(scan):
    line = scan.line
    out = [show_bytes(line)]
    for t in scan.sorted_tokens():
        stop = f"  (stopped at {t.stop})" if t.stop else ""
        out.append(f"  {'  ' * t.depth}{t.rule} [{t.start}:{t.end}] {show_bytes(line[t.start:t.end])}{stop}")
    for f in scan.findings:
        out.append(f"  ! {f.kind} {f.rule} @{f.offset}")
    verdict = scan.verdict()
    out.append(f"  = {verdict if verdict else 'no verdict (unread: ' + ', '.join(scan.unread) + ')'}")
    if not scan.check_cover():
        out.append("  ** depth-0 tokens do not cover the line **")
    return "\n".join(out)


def _json(scan):
    line = scan.line
    return json.dumps(
        {
            "line": line.decode("latin-1"),
            "tokens": [
                {"rule": t.rule, "start": t.start, "end": t.end, "depth": t.depth, "bytes": line[t.start : t.end].decode("latin-1")}
                | ({"stop": t.stop} if t.stop else {})
                for t in scan.sorted_tokens()
            ],
            "findings": [f._asdict() for f in scan.findings],
            "verdict": scan.verdict(),
            "unread": scan.unread,
        },
        ensure_ascii=False,
    )


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "as_json", is_flag=True, help="One JSON object per line.")
@click.option("-n", "--limit", type=click.IntRange(min=1), help="Stop after this many lines.")
def cli(paths, as_json, limit):
    for i, line in enumerate(_lines(paths)):
        if limit and i >= limit:
            break
        scan = tokenize(line)
        click.echo(_json(scan) if as_json else _text(scan))


if __name__ == "__main__":
    cli()
