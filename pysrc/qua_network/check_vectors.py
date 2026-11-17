# SPDX-License-Identifier: Apache-2.0
"""Recompute the conformance vectors and compare them with the stored values.

The stored values in vectors/ were produced independently of this package
(during the design discussion, or extracted from a third-party source), so
agreement is evidence about both.
"""

import json
from pathlib import Path

import click

from qua_network import decimal_number, icon, identifier, name_format, object_pdu, pdu, position, station_info, symbol, usx
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


def check_decimal_number(v):
    if v.get("invalid") == "text":
        try:
            decimal_number.from_text(v["text"])
        except decimal_number.DecimalError:
            return None
        return "the parser accepts the text"
    data = bytes.fromhex(v["bytes"])
    if "invalid" in v:
        try:
            decimal_number.decode(data, v.get("infinity", True))
        except decimal_number.DecimalError as e:
            return None if e.case == v["invalid"] else f"decoder gives case {e.case}"
        return "decoder accepts it"
    want = v["text"] if v["text"] in (decimal_number.INF, decimal_number.NEG_INF) else (v["m"], v["e"])
    try:
        if decimal_number.decode(data) != want:
            return f"decode gives {decimal_number.decode(data)}"
        if decimal_number.encode(want) != data:
            return f"encode gives {decimal_number.encode(want).hex().upper()}"
        if decimal_number.to_text(want) != v["text"]:
            return f"the text form is {decimal_number.to_text(want)}"
        if decimal_number.from_text(v["text"]) != want:
            return f"the parser gives {decimal_number.from_text(v['text'])}"
    except decimal_number.DecimalError as e:
        return f"rejected: {e}"
    return None


def check_text_compression(v):
    data = bytes.fromhex(v["compressed"])
    try:
        got = usx.decode(data, v["length"])
    except usx.Malformed as e:
        if "invalid" not in v:
            return f"decoder rejects it: {e}"
        return None if e.case == v["invalid"] else f"decoder gives case {e.case}"
    if "invalid" in v:
        return "decoder accepts it"
    if len(got) != v["length"]:
        return "the length is not the length of the text"
    return None if got == v["text"].encode("utf-8") else f"decode gives {got!r}"


def check_pdu(v):
    data = bytes.fromhex(v["bytes"])
    try:
        got = pdu.parse(data)
    except pdu.PduError as e:
        if "invalid" not in v:
            return f"parser rejects it: {e}"
        return None if e.reason == v["invalid"] else f"parser gives the reason {e.reason}"
    if "invalid" in v:
        return "parser accepts it"
    got["source"] = identifier.decode(got["source"])
    got["entries"] = [f"{e:06X}" for e in got["entries"]]
    for key in ("tlv", "padding"):
        got[key] = got[key].hex().upper()
    for key, want in v.items():
        if key not in ("bytes", "note") and got[key] != want:
            return f"{key} is {got[key]}"
    return None


def check_pdu_unit(v):
    pdus, rest = pdu.split(bytes.fromhex(v["unit"]))
    got = [p.hex().upper() for p in pdus]
    if got != v["pdus"]:
        return f"the receiver reads {len(got)} PDUs: {got}"
    return None if rest.hex().upper() == v["rest"] else f"the rest is {rest.hex().upper()}"


def check_pdu_relay(v):
    received = bytes.fromhex(v["received"])
    try:
        got = pdu.relay(received, identifier.encode(v["relay"]), v.get("not_radio", False))
    except pdu.NotSentOn as e:
        if v["sent"] is not None:
            return f"relay does not send it on: {e}"
        return None if e.reason == v["reason"] else f"relay gives the reason {e.reason}"
    if v["sent"] is None:
        return "relay sends it on"
    return None if got == bytes.fromhex(v["sent"]) else f"relay sends {got.hex().upper()}"


def check_position(v):
    area = bytes.fromhex(v["tlv"])
    try:
        got = position.decode(area)
    except position.PositionError as e:
        if "invalid" not in v:
            return f"decoder rejects it: {e}"
        return None if e.field == v["invalid"] else f"decoder gives the field {e.field}"
    if "invalid" in v:
        return "decoder accepts it"
    if position.encode(got) != area:
        return f"encode gives {position.encode(got).hex().upper()}"
    for key in ("altitude", "uncertainty", "speed"):
        if key in got:
            got[key] = decimal_number.to_text(got[key])
    if "time" in got:
        got["time"] = str(got["time"])
    if "object" in got:
        got["object"] = identifier.decode(got["object"])
    if "other" in got:
        got["other"] = [[tag, value.hex().upper()] for tag, value in got["other"]]
    want = {key: value for key, value in v.items() if key not in ("tlv", "note")}
    return None if got == want else f"decode gives {got}"


def check_object(v):
    area = bytes.fromhex(v["tlv"])
    try:
        got = object_pdu.decode(area)
    except object_pdu.ObjectError as e:
        if "invalid" not in v:
            return f"decoder rejects it: {e}"
        return None if e.field == v["invalid"] else f"decoder gives the field {e.field}"
    if "invalid" in v:
        return "decoder accepts it"
    if not got.get("compressed") and object_pdu.encode(got) != area:
        return f"encode gives {object_pdu.encode(got).hex().upper()}"
    got["object"] = identifier.decode(got["object"])
    if "description" in got:
        got["description"] = got["description"].decode("utf-8")
    if "end_time" in got:
        got["end_time"] = str(got["end_time"])
    if "other" in got:
        got["other"] = [[tag, value.hex().upper()] for tag, value in got["other"]]
    want = {key: value for key, value in v.items() if key not in ("tlv", "note")}
    return None if got == want else f"decode gives {got}"


def check_name(v):
    if v.get("invalid") == "text":
        try:
            name_format.encode(v["text"])
        except name_format.NameFormatError:
            return None
        return "encoder accepts it"
    value = int.from_bytes(bytes.fromhex(v["bytes"]), "little")
    try:
        text = name_format.decode(value)
    except name_format.NameFormatError as e:
        return None if "invalid" in v else f"decoder rejects it: {e}"
    if "invalid" in v:
        return "decoder accepts it"
    if text != v["text"]:
        return f"decode gives {text}"
    if value != int(v["value"], 16):
        return "bytes are not the value in little-endian order"
    got = name_format.encode(v["text"])
    return None if got == value else f"encode gives 0x{got:016X}"


def check_symbol(v):
    data = bytes.fromhex(v["bytes"])
    classic = v["form"] == "classic"
    try:
        got = symbol.classic_decode(data) if classic else symbol.unicode_decode(data)
    except symbol.SymbolError as e:
        return None if "invalid" in v else f"decoder rejects it: {e}"
    if "invalid" in v:
        return "decoder accepts it"
    if classic:
        if got != v["number"]:
            return f"decode gives {got}"
        if symbol.classic_chars(got) != v["chars"] or symbol.classic_number(v["chars"]) != got:
            return f"the characters of {got} are {symbol.classic_chars(got)}"
        back = symbol.classic_encode(got)
    else:
        if [f"{p:04X}" for p in got] != v["points"]:
            return f"decode gives {got}"
        back = symbol.unicode_encode(got)
    return None if back == data else f"encode gives {back.hex().upper()}"


def check_station_information(v):
    area = bytes.fromhex(v["tlv"])
    try:
        got = station_info.decode(area)
    except station_info.StationInfoError as e:
        if "invalid" not in v:
            return f"decoder rejects it: {e}"
        return None if e.field == v["invalid"] else f"decoder gives the field {e.field}"
    if "invalid" in v:
        return "decoder accepts it"
    if station_info.encode(got) != area:
        return f"encode gives {station_info.encode(got).hex().upper()}"
    for key in ("power", "height", "gain", "range"):
        if key in got:
            got[key] = decimal_number.to_text(got[key])
    if "symbol_unicode" in got:
        got["symbol_unicode"] = [f"{p:04X}" for p in got["symbol_unicode"]]
    if "object" in got:
        got["object"] = identifier.decode(got["object"])
    if "other" in got:
        got["other"] = [[tag, value.hex().upper()] for tag, value in got["other"]]
    want = {key: value for key, value in v.items() if key not in ("tlv", "note")}
    return None if got == want else f"decode gives {got}"


CHECKS = {
    "identifier.json": check_identifier,
    "hop-hash.json": check_hop_hash,
    "crc32c.json": check_crc32c,
    "decimal-number.json": check_decimal_number,
    "pdu.json": check_pdu,
    "pdu-unit.json": check_pdu_unit,
    "pdu-relay.json": check_pdu_relay,
    "position.json": check_position,
    "object.json": check_object,
    "name.json": check_name,
    "symbol.json": check_symbol,
    "station-information.json": check_station_information,
    "text-compression.json": check_text_compression,
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
