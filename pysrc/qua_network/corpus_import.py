# SPDX-License-Identifier: Apache-2.0
"""Convert raw corpus files to Parquet, one output file per input file.

The conversion is lossless. Every input line becomes one row:

    time         timestamp[ms, UTC]  logged receive time; null if the line had none
    header       binary              the TNC2 line up to the first ':'
    payload      binary              everything after that ':'; null if there was none
    source       binary              source address
    destination  binary              destination address
    q            binary              q-construct
    n_digis      int16               addresses between destination and q-construct

The original line is header + b":" + payload, or header alone when payload
is null. The last four columns are derived from the header and are null
when it does not parse. Content columns are binary because packets are not
valid UTF-8.

Existing outputs are skipped, so a rerun only converts new files.
"""

import os
from functools import partial
from pathlib import Path

import click
import pyarrow as pa
import pyarrow.parquet as pq

from qua_network.parallel import jobs_option, map_files
from qua_network.tnc2 import (
    log_files,
    parse_header,
    read_records,
    split_payload,
    split_record,
    unix_ms,
)

SCHEMA = pa.schema(
    [
        ("time", pa.timestamp("ms", tz="UTC")),
        ("header", pa.binary()),
        ("payload", pa.binary()),
        ("source", pa.binary()),
        ("destination", pa.binary()),
        ("q", pa.binary()),
        ("n_digis", pa.int16()),
    ]
)
BATCH_ROWS = 65536
UNPARSED = (None, None, None, None)


def output_path(out_dir, src):
    name = os.path.basename(src).removesuffix(".gz").removesuffix(".log")
    return out_dir / f"{name}.parquet"


def convert(out_dir, src):
    """Write the Parquet file for src. Returns (rows, truncated)."""
    dst = output_path(out_dir, src)
    tmp = dst.with_name(dst.name + ".tmp")
    columns = [[] for _ in SCHEMA]
    times, headers, payloads, sources, destinations, qs, digis = columns
    rows = 0
    truncated = False

    def flush(writer):
        writer.write_batch(pa.record_batch([pa.array(c, type=f.type) for c, f in zip(columns, SCHEMA)], schema=SCHEMA))
        for c in columns:
            c.clear()

    try:
        with pq.ParquetWriter(tmp, SCHEMA, compression="zstd", compression_level=3) as writer:
            try:
                for record in read_records(src):
                    ts, line = split_record(record)
                    header, payload = split_payload(line)
                    source, destination, n_digis, q = (parse_header(header) if payload is not None else None) or UNPARSED
                    times.append(None if ts is None else unix_ms(ts))
                    headers.append(header)
                    payloads.append(payload)
                    sources.append(source)
                    destinations.append(destination)
                    qs.append(q)
                    digis.append(n_digis)
                    rows += 1
                    if len(times) >= BATCH_ROWS:
                        flush(writer)
            except EOFError:
                truncated = True
            if times:
                flush(writer)
        os.replace(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)
    return rows, truncated


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("log_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("out_dir", type=click.Path(file_okay=False, path_type=Path))
@click.option("--force", is_flag=True, help="Regenerate outputs that already exist.")
@jobs_option
def cli(log_dir, out_dir, force, jobs):
    files = log_files(log_dir)
    if not files:
        raise click.ClickException("no log files found")
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [fn for fn in files if force or not output_path(out_dir, fn).exists()]

    total = 0
    for fn, (rows, truncated) in map_files(partial(convert, out_dir), todo, jobs):
        if truncated:
            click.echo(f"warning: {fn} is truncated; converted the {rows} rows read", err=True)
        total += rows

    click.echo(f"input: {os.path.basename(files[0])} .. {os.path.basename(files[-1])}")
    click.echo(f"files={len(files)}  converted={len(todo)}  skipped={len(files) - len(todo)}  rows={total}")


if __name__ == "__main__":
    cli()
