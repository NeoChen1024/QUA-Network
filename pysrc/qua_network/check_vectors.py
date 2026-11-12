# SPDX-License-Identifier: Apache-2.0
"""Recompute the conformance vectors and compare them with the stored values.

The stored values in vectors/ were produced during the design discussion,
independently of this package, so agreement is evidence about both.
"""

import json
from pathlib import Path

import click

from qua_network import identifier


def crc32c(data):
    """CRC-32C (Castagnoli), bit by bit, with the parameters of RFC 5.1."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


def check_identifier(v):
    want = int(v["value"], 16)
    got = identifier.encode(v["text"])
    if got != want:
        return f"encode gives 0x{got:016X}"
    back = identifier.decode(want)
    if back != v["text"]:
        return f"decode gives {back}"
    return None


def check_hop_hash(v):
    ident = int(v["identifier"], 16)
    if identifier.encode(v["text"]) != ident:
        return "identifier does not match text"
    got = identifier.hop_hash(ident).hex().upper()
    return None if got == v["hash"] else f"hash is {got}"


def check_crc32c(v):
    got = crc32c(v["ascii"].encode("ascii"))
    return None if got == int(v["crc"], 16) else f"crc is 0x{got:08X}"


CHECKS = {
    "identifier.json": check_identifier,
    "hop-hash.json": check_hop_hash,
    "crc32c.json": check_crc32c,
}


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--vectors", "vectors_dir", type=click.Path(exists=True, file_okay=False, path_type=Path), default="vectors", show_default=True
)
def cli(vectors_dir):
    failed = 0
    seen = {p.name for p in vectors_dir.glob("*.json")}
    for name in sorted(seen - CHECKS.keys()):
        click.echo(f"{name}: no check defined")
        failed += 1
    for name, check in CHECKS.items():
        if name not in seen:
            click.echo(f"{name}: missing")
            failed += 1
            continue
        vectors = json.loads((vectors_dir / name).read_text())
        bad = 0
        for v in vectors:
            problem = check(v)
            if problem:
                click.echo(f"{name}: {json.dumps(v)}: {problem}")
                bad += 1
        click.echo(f"{name}: {len(vectors) - bad}/{len(vectors)} ok")
        failed += bad
    if failed:
        raise click.ClickException(f"{failed} problem(s)")


if __name__ == "__main__":
    cli()
