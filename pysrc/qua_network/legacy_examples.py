# SPDX-License-Identifier: Apache-2.0
"""Check the example packets of APRS12c against the legacy reading.

"extract" collects candidate examples from the Markdown working copy that
qua-spec-extract makes of APRS12c (work/refs/text/APRS12c.md): runs of
Courier text, joined across highlight marks, with the visible-space sign
read as a space, and the lines of fenced blocks. A candidate is kept when it
starts with a data type identifier byte or a TNC2 header. Each gets an ID:
the PDF page and the first 8 hex digits of the BLAKE3 digest of its bytes.
The candidates are written to a JSON Lines file under work/, because the
document's terms do not allow copying its text into the project.

"check" tokenizes every candidate and compares the verdict with the
expectation list, a JSON file that holds, per ID, the verdict the reading
gives and why, but not the bytes. Candidates that the list does not name,
and entries of the list that no candidate matches, are reported too.
"""

import json
import os
import re

import click
from blake3 import blake3

from qua_network.legacy.tokenizer import show_bytes, tokenize

_PAGE = re.compile(r"<!-- page (\d+)(?:, printed (\S+))? -->")
_SPAN = re.compile(r"`([^`]*)`")
_DTI = set("!\"#$%'()*+,./:;<=>?@T[\\]_`{}")
_TNC2 = re.compile(rb"[A-Za-z0-9-]{1,9}>[^:\s]+:")
_HEADER = b"N0CALL>APRS:"
_PACKET_KINDS = ("packet", "text-layer")


def _runs(piece):
    """Concatenations of code spans separated only by highlight marks."""
    out, cur, last = [], [], None
    for m in _SPAN.finditer(piece):
        gap = piece[last : m.start()] if last is not None else None
        if cur and gap is not None and gap.strip("=") != "":
            out.append("".join(cur))
            cur = []
        cur.append(m.group(1))
        last = m.end()
    if cur:
        out.append("".join(cur))
    return out


def _candidates(path):
    page, printed = None, None
    fenced = False
    with open(path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if m := _PAGE.match(line):
                page, printed = int(m.group(1)), m.group(2)
                continue
            if line.startswith("```"):
                fenced = not fenced
                continue
            texts = [line.strip()] if fenced else [r for p in re.split(r"<br>|\|", line) for r in _runs(p)]
            for t in texts:
                t = t.replace("˽", " ").rstrip()
                if len(t) < 2:
                    continue
                b = t.encode("utf-8")
                if t[0] in _DTI or _TNC2.match(b):
                    yield {"page": page, "printed": printed, "md_line": n, "text": t, "partial": "…" in t}


def _id(c):
    return f"p{c['page']}-{blake3(c['text'].encode('utf-8')).hexdigest()[:8]}"


@click.group(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
def cli():
    pass


@cli.command(help="Collect candidate examples into a JSON Lines file under work/.")
@click.option("--text", default="work/refs/text/APRS12c.md", show_default=True, type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output", default="work/legacy/examples/APRS12c.jsonl", show_default=True, type=click.Path(dir_okay=False))
def extract(text, output):
    seen = set()
    rows = []
    for c in _candidates(text):
        c["id"] = _id(c)
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        rows.append(c)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    tmp = output + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for c in rows:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    os.replace(tmp, output)
    click.echo(f"{len(rows)} candidates ({sum(c['partial'] for c in rows)} partial) from {text} written to {output}")


def _line(c):
    b = c["text"].encode("utf-8")
    return b if _TNC2.match(b) else _HEADER + b


@cli.command(help="Tokenize the candidates and compare with the expectation list.")
@click.option("--examples", default="work/legacy/examples/APRS12c.jsonl", show_default=True, type=click.Path(exists=True))
@click.option("--expect", "expect_path", type=click.Path(exists=True, dir_okay=False), help="Expectation list (JSON).")
@click.option("-v", "--verbose", is_flag=True, help="Show tokens and findings of every candidate.")
def check(examples, expect_path, verbose):
    with open(examples, encoding="utf-8") as fh:
        cands = [json.loads(x) for x in fh]
    expect = {}
    if expect_path:
        with open(expect_path, encoding="utf-8") as fh:
            expect = {e["id"]: e for e in json.load(fh)["examples"]}
    counts = dict.fromkeys(("agree", "verdict", "findings", "pending", "not-a-packet", "unlisted"), 0)
    for c in cands:
        line = _line(c)
        info = line.find(b":") + 1
        scan = tokenize(line)
        verdict = scan.verdict()
        # Findings in the information field, offsets from its byte 0; the
        # header that check adds is left out.
        got_f = sorted(f"{f.kind} {f.rule} @{f.offset - info}" for f in scan.findings if f.offset >= info)
        e = expect.get(c["id"])
        want = e.get("verdict") if e else None
        if e is None:
            mark, key = "?", "unlisted"
        elif e["kind"] not in _PACKET_KINDS:
            mark, key = ".", "not-a-packet"
        elif verdict is None:
            mark, key = "~", "pending"
        elif want != verdict:
            mark, key = "!", "verdict"
        elif sorted(e["findings"]) != got_f:
            mark, key = "f", "findings"
        else:
            mark, key = "=", "agree"
        counts[key] += 1
        got = verdict or "unread: " + ", ".join(scan.unread)
        click.echo(
            f"{mark} {c['id']:16s} p. {c['page']}/{c['printed']}  got {got:20s} want {want or '-':18s} {show_bytes(line[info:])[:70]}"
        )
        if verbose or mark in "!f":
            want_f = sorted(e["findings"]) if e and mark in "!f" else []
            for x in got_f:
                click.echo(f"      {' ' if x in want_f else '+'} {x}")
            for x in want_f:
                if x not in got_f:
                    click.echo(f"      - {x}")
    missing = sorted(set(expect) - {c["id"] for c in cands})
    for i in missing:
        click.echo(f"- {i}: listed, but no candidate has this ID")
    summary = " ".join(f"{k}={v}" for k, v in counts.items())
    click.echo(f"\ncandidates={len(cands)} {summary} listed-but-missing={len(missing)}")
    click.echo("marks: = agree, ! verdict differs, f findings differ (+ only got, - only expected), ~ format not read yet")


if __name__ == "__main__":
    cli()
