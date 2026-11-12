# SPDX-License-Identifier: Apache-2.0
"""Sending software and devices in the corpus, by destination callsign.

Reads the Parquet files written by qua-corpus-import and counts packets
by destination callsign (tocall), resolved against the aprs-deviceid
database. Counts are reported separately for RF-origin packets and for the
whole feed.

Mic-E packets are counted as their own row: their destination field holds
position, and the device is identified by other means that this tool does
not implement. A third-party packet ('}') is counted under the tocall of
the station that relayed it, not of the original sender.
"""

import csv
import glob
import os
from collections import Counter

import click
import pyarrow.compute as pc
import pyarrow.parquet as pq

from qua_network.deviceid import MIC_E_TYPES, DeviceIndex
from qua_network.parallel import jobs_option, map_files
from qua_network.tnc2 import RF_Q

MIC_E = "(Mic-E)"


def scan(path):
    """Return (rows, {(destination, q, data_type): packets}) for one Parquet file."""
    table = pq.read_table(path, columns=["destination", "q", "payload"])
    rows = table.num_rows
    table = table.filter(pc.is_valid(table["q"]))
    table = table.set_column(2, "dtype", pc.binary_slice(table["payload"], 0, 1))
    grouped = table.group_by(["destination", "q", "dtype"]).aggregate([([], "count_all")])
    keys = zip(grouped["destination"].to_pylist(), grouped["q"].to_pylist(), grouped["dtype"].to_pylist())
    return rows, dict(zip(keys, grouped["count_all"].to_pylist()))


def describe(entry):
    if entry is None:
        return "", "", ""
    return str(entry.get("vendor", "")), str(entry.get("model", "")), str(entry.get("class", ""))


def print_ranking(title, counts, total, top):
    """Ties are ordered by label so that output does not depend on worker completion order."""
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    click.echo(f"\n== {title} ==  n={total}")
    for label, n in ranked[:top]:
        click.echo(f"  {n:10d}  {n / total * 100:6.2f}%  {label}")
    rest = sum(n for _, n in ranked[top:])
    if rest:
        click.echo(f"  {rest:10d}  {rest / total * 100:6.2f}%  (all others, {len(ranked) - top} entries)")


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("parquet_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--deviceid",
    "deviceid_path",
    type=click.Path(exists=True, dir_okay=False),
    default="3rdparty/aprs-deviceid/tocalls.yaml",
    show_default=True,
    help="aprs-deviceid database.",
)
@click.option("--top", type=click.IntRange(min=1), default=40, show_default=True, help="Rows per ranking.")
@click.option("--csv", "csv_path", type=click.Path(dir_okay=False), help="Write the full per-tocall table here.")
@jobs_option
def cli(parquet_dir, deviceid_path, top, csv_path, jobs):
    files = sorted(glob.glob(os.path.join(parquet_dir, "aprsis-*.parquet")))
    if not files:
        raise click.ClickException("no Parquet files found")
    index = DeviceIndex.load(deviceid_path)

    rows = 0
    raw = Counter()
    for _, (n, part) in map_files(scan, files, jobs):
        rows += n
        raw.update(part)

    # (origin, tocall) -> packets, with Mic-E folded into one pseudo-tocall.
    by_tocall = Counter()
    for (destination, q, dtype), n in raw.items():
        origin = "RF" if q in RF_Q else "IS"
        tocall = MIC_E if dtype in MIC_E_TYPES else destination.decode("ascii", "replace").partition("-")[0]
        by_tocall[origin, tocall] += n

    parsed = sum(by_tocall.values())
    click.echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}")
    click.echo(f"files={len(files)}  rows={rows}  parsed={parsed}  distinct_tocalls={len({t for _, t in by_tocall})}")

    for origin, title in (("RF", "RF-origin"), (None, "Whole feed")):
        devices, unknown, classes = Counter(), Counter(), Counter()
        total = 0
        for (o, tocall), n in by_tocall.items():
            if origin and o != origin:
                continue
            total += n
            if tocall == MIC_E:
                devices[MIC_E] += n
                classes[MIC_E] += n
                continue
            entry = index.lookup(tocall)
            vendor, model, cls = describe(entry)
            if entry is None:
                devices["(not in database)"] += n
                unknown[tocall] += n
                classes["(not in database)"] += n
            else:
                devices[f"{vendor} {model}".strip() + f"  [{entry['tocall']}]"] += n
                classes[cls or "(no class)"] += n
        print_ranking(f"{title}: packets by device", devices, total, top)
        print_ranking(f"{title}: packets by device class", classes, total, top)
        print_ranking(f"{title}: destinations not in the database", unknown, total, top)

    if csv_path:
        with open(csv_path, "w", newline="") as fh:
            out = csv.writer(fh)
            out.writerow(["origin", "tocall", "pattern", "vendor", "model", "class", "packets"])
            for (origin, tocall), n in sorted(by_tocall.items(), key=lambda kv: (kv[0][0], -kv[1])):
                entry = None if tocall == MIC_E else index.lookup(tocall)
                out.writerow([origin, tocall, entry["tocall"] if entry else "", *describe(entry), n])
        click.echo(f"\ntable written to {csv_path}")


if __name__ == "__main__":
    cli()
