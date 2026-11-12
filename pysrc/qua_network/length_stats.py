# SPDX-License-Identifier: Apache-2.0
"""Packet-length statistics over the corpus.

Reports the distribution of APRS payload length in bytes (the information
field after the first ':' following the TNC2 header), plus an estimated
on-air AX.25 frame size:

    ax25_len = 14 (src+dst) + 7 * n_digis + 2 (ctrl+PID) + payload + 2 (FCS)

Packets are split by origin using the q-construct (see tnc2.RF_Q). Only RF
packets are meaningful for an on-air size budget.

All statistics are kept as length histograms, so memory use is constant
regardless of corpus size.
"""

import os
from collections import Counter, defaultdict

import click

from qua_network.parallel import jobs_option, map_files
from qua_network.tnc2 import (
    RF_Q,
    log_files,
    parse_header,
    read_records,
    split_payload,
    split_record,
)

THRESHOLDS = (64, 96, 128, 160, 200, 255)

DATA_TYPE_NAMES = {
    b"!": "pos (no ts)",
    b"=": "pos (no ts, msg)",
    b"/": "pos (ts)",
    b"@": "pos (ts, msg)",
    b"`": "Mic-E",
    b"'": "Mic-E (old)",
    b":": "message",
    b";": "object",
    b")": "item",
    b"T": "telemetry",
    b"_": "weather",
    b">": "status",
    b"<": "capabilities",
    b"?": "query",
    b"$": "raw GPS",
    b"{": "user-defined",
    b"}": "third-party",
}


def hist_percentiles(hist, ps):
    """Exact percentiles from a {value: count} histogram."""
    n = sum(hist.values())
    out, acc = {}, 0
    it = iter(sorted(ps))
    cur = next(it)
    for v in sorted(hist):
        acc += hist[v]
        while acc >= cur / 100 * n:
            out[cur] = v
            cur = next(it, None)
            if cur is None:
                return out
    return out


def report(name, hist):
    n = sum(hist.values())
    if not n:
        return
    mean = sum(v * c for v, c in hist.items()) / n
    pct = hist_percentiles(hist, (50, 90, 95, 99, 99.9))
    click.echo(f"\n== {name} ==  n={n}  mean={mean:.1f}  max={max(hist)}")
    click.echo("  " + "  ".join(f"p{p}={v}" for p, v in pct.items()))
    for limit in THRESHOLDS:
        frac = sum(c for v, c in hist.items() if v <= limit) / n
        click.echo(f"  <= {limit:3d} B: {frac*100:7.3f}%")


def scan(fn):
    """Histograms for one corpus file."""
    payload_rf, payload_is, ax25_rf = Counter(), Counter(), Counter()
    by_type = {}
    digi_hist, q_hist = Counter(), Counter()
    total = bad = 0
    truncated = False
    try:
        for record in read_records(fn):
            total += 1
            header, payload = split_payload(split_record(record)[1])
            rec = parse_header(header) if payload is not None else None
            if rec is None:
                bad += 1
                continue
            _, _, n_digi, q = rec
            plen = len(payload)
            q_hist[q] += 1
            if q in RF_Q:
                payload_rf[plen] += 1
                ax25_rf[14 + 7 * n_digi + 2 + plen + 2] += 1
                by_type.setdefault(payload[:1], Counter())[plen] += 1
                digi_hist[n_digi] += 1
            else:
                payload_is[plen] += 1
    except EOFError:
        # The logger was killed mid-write: keep what decoded, skip the tail.
        truncated = True
    return payload_rf, payload_is, ax25_rf, by_type, digi_hist, q_hist, total, bad, truncated


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("log_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--csv", "csv_path", type=click.Path(dir_okay=False), help="Write the per-byte RF payload length histogram here.")
@jobs_option
def cli(log_dir, csv_path, jobs):
    files = log_files(log_dir)
    if not files:
        raise click.ClickException("no log files found")

    payload_rf, payload_is, ax25_rf = Counter(), Counter(), Counter()
    by_type = defaultdict(Counter)
    digi_hist, q_hist = Counter(), Counter()
    total = bad = truncated = 0

    for fn, part in map_files(scan, files, jobs):
        payload_rf.update(part[0])
        payload_is.update(part[1])
        ax25_rf.update(part[2])
        for dtype, hist in part[3].items():
            by_type[dtype].update(hist)
        digi_hist.update(part[4])
        q_hist.update(part[5])
        total += part[6]
        bad += part[7]
        if part[8]:
            truncated += 1
            click.echo(f"warning: {fn} is truncated; using data read so far", err=True)

    click.echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}")
    click.echo(f"files={len(files)}  truncated={truncated}  lines={total}  unparsable={bad} ({bad/total*100:.3f}%)")

    click.echo("\n== q-construct distribution ==")
    parsed = total - bad
    for q, c in sorted(q_hist.items(), key=lambda kv: (-kv[1], kv[0])):
        tag = "RF" if q in RF_Q else "IS"
        click.echo(f"  {q.decode('ascii', 'replace'):4s} [{tag}] {c:10d}  {c/parsed*100:6.2f}%")

    report("RF payload bytes", payload_rf)
    report("RF estimated AX.25 frame bytes (incl. header+FCS)", ax25_rf)
    report("IS-only payload bytes", payload_is)

    click.echo("\n== RF digi-path length (addresses after destination) ==")
    n_rf = sum(digi_hist.values())
    for k in sorted(digi_hist):
        click.echo(f"  {k} digis: {digi_hist[k]:10d}  {digi_hist[k]/n_rf*100:6.2f}%")

    click.echo("\n== RF payload bytes by data type ==")
    for dtype, hist in sorted(by_type.items(), key=lambda kv: (-sum(kv[1].values()), kv[0])):
        n = sum(hist.values())
        pct = hist_percentiles(hist, (50, 95, 99))
        name = DATA_TYPE_NAMES.get(dtype, repr(dtype))
        click.echo(
            f"  {name:18s} n={n:10d} ({n/n_rf*100:5.2f}%)  p50={pct[50]:3d}  p95={pct[95]:3d}  p99={pct[99]:3d}  max={max(hist):4d}"
        )

    if csv_path:
        with open(csv_path, "w") as fh:
            fh.write("payload_bytes,count\n")
            for k in sorted(payload_rf):
                fh.write(f"{k},{payload_rf[k]}\n")
        click.echo(f"\nhistogram written to {csv_path}")


if __name__ == "__main__":
    cli()
