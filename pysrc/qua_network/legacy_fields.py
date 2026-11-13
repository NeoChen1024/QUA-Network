# SPDX-License-Identifier: Apache-2.0
"""Field inventory of the corpus under the legacy reading (docs/legacy/).

Every packet is tokenized; the inventory counts, per rule ID of the
reading: how many packets carry the token, how many tokens there are, the
distribution of their byte length, and how many of them hold bytes outside
7-bit ASCII (counted apart from the findings, docs/legacy/README.md
section 3). It also counts verdicts, the identifier rule carried by byte 0,
the findings by rule and kind, and the formats whose reader is not written
yet. Each finding keeps a few example lines: those with the smallest
BLAKE3 digest, so that the choice does not depend on the order in which
files are read.

The input is one or more corpus files, or directories of them. The input
file range and the packet count are printed with the results. With
-o/--output the full inventory is also written as JSON.
"""

import json
import os
from collections import Counter, defaultdict
from functools import partial

import click
from blake3 import blake3

from qua_network.legacy.tokenizer import show_bytes, tokenize
from qua_network.parallel import jobs_option, map_files
from qua_network.tnc2 import log_files, read_records, split_record

N_EXAMPLES = 5


class Inventory:
    def __init__(self):
        self.packets = 0
        self.truncated = 0
        self.uncovered = 0
        self.verdicts = Counter()
        self.identifiers = Counter()
        self.unread = Counter()
        self.present = Counter()  # rule -> packets carrying it
        self.tokens = Counter()  # rule -> tokens
        self.lengths = defaultdict(Counter)  # rule -> {length: tokens}
        self.non_ascii = Counter()  # rule -> tokens holding a byte >= 0x80
        self.findings = Counter()  # (rule, kind) -> findings
        self.examples = defaultdict(list)  # (rule, kind) -> [(digest, line)]

    def add(self, line):
        scan = tokenize(line)
        self.packets += 1
        verdict = scan.verdict()
        self.verdicts[verdict or "no verdict"] += 1
        for w in scan.unread:
            self.unread[w] += 1
        if not scan.check_cover():
            self.uncovered += 1
            self._example(("cover", "-"), line)
        seen = set()
        for t in scan.tokens:
            rule = t.rule if t.stop is None else f"residue@{t.stop}"
            self.tokens[rule] += 1
            n = t.end - t.start
            self.lengths[rule][n] += 1
            if rule not in seen:
                seen.add(rule)
                self.present[rule] += 1
            if n and max(line[t.start : t.end]) >= 0x80:
                self.non_ascii[rule] += 1
        # The byte-0 identifier token of the outer information field.
        sep = line.find(b":")
        ident = next((t.rule for t in scan.tokens if t.depth == 0 and t.start == sep + 1), None)
        if ident is not None:
            self.identifiers[ident] += 1
        for f in scan.findings:
            key = (f.rule, f.kind)
            self.findings[key] += 1
            self._example(key, line)

    def _example(self, key, line):
        ex = self.examples[key]
        d = blake3(line).digest(8)
        if len(ex) < N_EXAMPLES or d < ex[-1][0]:
            if (d, line) not in ex:
                ex.append((d, line))
                ex.sort()
                del ex[N_EXAMPLES:]

    def merge(self, o):
        self.packets += o.packets
        self.truncated += o.truncated
        self.uncovered += o.uncovered
        for a in ("verdicts", "identifiers", "unread", "present", "tokens", "non_ascii", "findings"):
            getattr(self, a).update(getattr(o, a))
        for rule, hist in o.lengths.items():
            self.lengths[rule].update(hist)
        for key, ex in o.examples.items():
            for d, line in ex:
                self._example_merge(key, d, line)

    def _example_merge(self, key, d, line):
        ex = self.examples[key]
        if (d, line) not in ex:
            ex.append((d, line))
            ex.sort()
            del ex[N_EXAMPLES:]


def scan_file(path):
    inv = Inventory()
    try:
        for record in read_records(path):
            inv.add(split_record(record)[1])
    except EOFError:
        inv.truncated = 1
    return inv


def _percentile(hist, p):
    n = sum(hist.values())
    acc = 0
    for v in sorted(hist):
        acc += hist[v]
        if acc >= p / 100 * n:
            return v
    return 0


def _report(inv, files):
    echo = click.echo
    echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}  files={len(files)}  truncated={inv.truncated}")
    echo(f"packets={inv.packets}  depth-0 cover failures={inv.uncovered}")
    n = inv.packets or 1

    echo("\n== verdicts ==")
    for v, c in inv.verdicts.most_common():
        echo(f"  {v:20s} {c:10d}  {c / n * 100:7.3f}%")
    if inv.unread:
        echo("\n== formats without a reader yet (packets) ==")
        for w, c in inv.unread.most_common():
            echo(f"  {w:20s} {c:10d}  {c / n * 100:7.3f}%")

    echo("\n== identifier rule at byte 0 of the information field ==")
    for r, c in inv.identifiers.most_common():
        echo(f"  {r:20s} {c:10d}  {c / n * 100:7.3f}%")

    echo("\n== tokens: rule, packets carrying it, tokens, length p50/p99/max, tokens with bytes >= 0x80 ==")
    for rule in sorted(inv.tokens):
        h = inv.lengths[rule]
        echo(
            f"  {rule:24s} {inv.present[rule]:10d} {inv.tokens[rule]:10d}"
            f"  {_percentile(h, 50):4d} {_percentile(h, 99):4d} {max(h):5d}  {inv.non_ascii[rule]:9d}"
        )

    echo("\n== findings: kind, rule, count, packets share; first example ==")
    for (rule, kind), c in sorted(inv.findings.items(), key=lambda kv: (kv[0][1], -kv[1])):
        ex = inv.examples[(rule, kind)]
        echo(f"  {kind:11s} {rule:20s} {c:10d}  {c / n * 100:7.3f}%  {show_bytes(ex[0][1])[:100] if ex else ''}")


def _to_json(inv, files):
    return {
        "input": {"first": os.path.basename(files[0]), "last": os.path.basename(files[-1]), "files": len(files)},
        "packets": inv.packets,
        "truncated_files": inv.truncated,
        "cover_failures": inv.uncovered,
        "verdicts": dict(inv.verdicts),
        "unread": dict(inv.unread),
        "identifiers": dict(inv.identifiers),
        "rules": {
            rule: {
                "packets": inv.present[rule],
                "tokens": inv.tokens[rule],
                "non_ascii_tokens": inv.non_ascii[rule],
                "lengths": {str(k): v for k, v in sorted(inv.lengths[rule].items())},
            }
            for rule in sorted(inv.tokens)
        },
        "findings": [
            {"rule": r, "kind": k, "count": c, "examples": [line.decode("latin-1") for _, line in inv.examples[(r, k)]]}
            for (r, k), c in sorted(inv.findings.items())
        ],
    }


def _expand(paths):
    files = []
    for p in paths:
        files.extend(log_files(p) if os.path.isdir(p) else [p])
    return sorted(set(files), key=os.path.basename)


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(dir_okay=False), help="Also write the full inventory as JSON here.")
@jobs_option
def cli(paths, output, jobs):
    files = _expand(paths)
    if not files:
        raise click.ClickException("no corpus files found")
    inv = Inventory()
    for path, part in map_files(partial(scan_file), files, jobs):
        if part.truncated:
            click.echo(f"warning: {path} is truncated; using data read so far", err=True)
        inv.merge(part)
    _report(inv, files)
    if output:
        tmp = output + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(_to_json(inv, files), fh, ensure_ascii=False, indent=1)
        os.replace(tmp, output)
        click.echo(f"\ninventory written to {output}")


if __name__ == "__main__":
    cli()
