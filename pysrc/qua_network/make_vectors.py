# SPDX-License-Identifier: Apache-2.0
"""Write the vector files that this package computes.

Each file comes from a module that is independent of the module that
qua-check-vectors checks against it: vectors_decimal.py, vectors_text.py,
vectors_pdu.py, vectors_position.py, vectors_object.py, vectors_name.py,
vectors_symbol.py and vectors_station.py. The text compression vectors need a C compiler and the
submodule 3rdparty/Unishox2.

An existing vector is a compatibility contract. A changed value in an
existing file is a format change, and the author decides it.
"""

import json
import os
from pathlib import Path

import click

NAMES = (
    "decimal-number",
    "text-compression",
    "hop-hash",
    "pdu",
    "pdu-unit",
    "pdu-relay",
    "position",
    "object",
    "name",
    "symbol",
    "station-information",
)


def _rows(name, vectors_dir):
    if name == "decimal-number":
        from qua_network import vectors_decimal

        return vectors_decimal.vectors()
    if name == "text-compression":
        from qua_network import vectors_text

        return vectors_text.vectors()
    if name == "position":
        from qua_network import vectors_position

        return vectors_position.vectors()
    if name == "name":
        from qua_network import vectors_name

        return vectors_name.vectors()
    if name == "symbol":
        from qua_network import vectors_symbol

        return vectors_symbol.vectors()
    if name == "station-information":
        from qua_network import vectors_station

        return vectors_station.vectors()
    if name == "object":
        from qua_network import vectors_object

        return vectors_object.vectors(json.loads((vectors_dir / "text-compression.json").read_text()))
    from qua_network import vectors_pdu

    ids = {v["text"]: int(v["value"], 16) for v in json.loads((vectors_dir / "identifier.json").read_text())}
    make = {
        "hop-hash": vectors_pdu.hop_hash_vectors,
        "pdu": vectors_pdu.pdu_vectors,
        "pdu-unit": vectors_pdu.unit_vectors,
        "pdu-relay": vectors_pdu.relay_vectors,
    }
    return make[name](ids)


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--vectors", "vectors_dir", type=click.Path(exists=True, file_okay=False, path_type=Path), default="vectors", show_default=True
)
@click.argument("name", nargs=-1, type=click.Choice(NAMES))
def cli(vectors_dir, name):
    """NAME is a file without `.json`. With no NAME, the tool writes each file."""
    for n in name or NAMES:
        text = "[\n" + ",\n".join("  " + json.dumps(row) for row in _rows(n, vectors_dir)) + "\n]\n"
        path = vectors_dir / f"{n}.json"
        changed = not path.exists() or path.read_text() != text
        if changed:
            part = path.with_suffix(f".{os.getpid()}.part")
            part.write_text(text)
            os.replace(part, path)
        click.echo(f"{path}: {'written' if changed else 'no change'}")


if __name__ == "__main__":
    cli()
