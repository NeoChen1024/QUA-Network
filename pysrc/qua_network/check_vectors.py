# SPDX-License-Identifier: Apache-2.0
"""Recompute the conformance vectors and compare them with the stored values.

The stored values in vectors/ were produced independently of this package
(during the design discussion, or extracted from a third-party source), so
agreement is evidence about both.
"""

import json
from pathlib import Path

import click

from qua_network import icon, identifier
from qua_network.crc import crc32c


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
    if ident.to_bytes(8, "little").hex().upper() != v["identifier_bytes"]:
        return "identifier_bytes are not the identifier in little-endian order"
    got = identifier.hop_hash(ident)
    if got != int(v["hash"], 16):
        return f"hash is {got:06X}"
    if got.to_bytes(3, "little").hex().upper() != v["hash_bytes"]:
        return "hash_bytes are not the hash in little-endian order"
    return None


def check_crc32c(v):
    got = crc32c(v["ascii"].encode("ascii"))
    return None if got == int(v["crc"], 16) else f"crc is 0x{got:08X}"


def check_icon_colour(v):
    got = "%02X%02X%02X" % icon.colour_rgb(v["value"])
    return None if got == v["rgb"] else f"rgb is {got}"


def check_icon_bitmap(v):
    field = bytes.fromhex(v["field"])
    if "reject" in v:
        try:
            icon.decode_bitmap(field)
        except icon.IconError:
            return None
        return "decoder accepts it"
    pixels = bytes.fromhex(v["pixels"])
    got = icon.encode_bitmap(pixels)
    if v.get("decode_only"):
        if got == field:
            return "marked decode_only, but it is what the encoder gives"
    elif got != field:
        return f"encode gives {got.hex().upper()}"
    try:
        back = icon.decode_bitmap(field)
    except icon.IconError as e:
        return f"decoder rejects it: {e}"
    return None if back == pixels else f"decode gives {back.hex().upper()}"


CHECKS = {
    "identifier.json": check_identifier,
    "hop-hash.json": check_hop_hash,
    "crc32c.json": check_crc32c,
    "icon-colour.json": check_icon_colour,
    "icon-bitmap.json": check_icon_bitmap,
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
