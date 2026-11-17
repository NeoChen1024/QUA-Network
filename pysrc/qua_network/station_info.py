# SPDX-License-Identifier: Apache-2.0
"""The TLV area of a Station information PDU
(docs/spec/12-station-information.md): the fields of an area, and the area
of a set of fields.

The fields are a dict. It has only the keys of the fields that the area
has:

- `kind`: the code of the kind, an integer;
- `make`, `model`: the names of the device (name_format.py), as text;
- `software`, `version`: the names of the software, as text;
- `power`, `height`, `gain`, `range`: decimal numbers as (m, e);
- `direction`: an integer in degrees;
- `symbol_classic`: the number of the classic form of the symbol;
- `symbol_unicode`: the code points of the Unicode form of the symbol;
- `object`: the value of the object identifier;
- `other`: the TLVs with a tag that the specification does not give, each
  as (tag, value).

This follows the draft, including its [proposed] rules. This module is a
research aid for checking vectors, not a reference implementation.
"""

from qua_network import decimal_number, identifier, name_format, symbol, tlv

OBJECT, KIND, DEVICE, SOFTWARE, POWER, HEIGHT, GAIN, DIRECTION, RANGE, SYMBOL_CLASSIC, SYMBOL_UNICODE = range(11)
NAMES = {
    OBJECT: "object",
    KIND: "kind",
    DEVICE: "device",
    SOFTWARE: "software",
    POWER: "power",
    HEIGHT: "height",
    GAIN: "gain",
    DIRECTION: "direction",
    RANGE: "range",
    SYMBOL_CLASSIC: "symbol_classic",
    SYMBOL_UNICODE: "symbol_unicode",
}
KINDS = ("other", "fixed", "portable", "pedestrian", "land vehicle", "watercraft", "aircraft", "balloon", "spacecraft")


class StationInfoError(ValueError):
    """The area is not valid. field is the name of the field with the
    invalid TLV, or `tlv area` if the area breaks 03-tlv."""

    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


def kind_name(code):
    """The kind of a code. A code with no kind is `other` (section 3.1)."""
    return KINDS[code] if code < len(KINDS) else KINDS[0]


def _names(field, value, keys, alone):
    """The one or two names of a device or software field. With 8 bytes,
    the field has the name of the key alone only."""
    if len(value) not in (8, 16):
        raise StationInfoError(field, "the field does not have 8 or 16 bytes")
    out = {}
    for key, at in zip(keys if len(value) == 16 else (alone,), range(0, len(value), 8)):
        try:
            out[key] = name_format.decode(int.from_bytes(value[at : at + 8], "little"))
        except name_format.NameFormatError as e:
            raise StationInfoError(field, str(e)) from None
    return out


def decode(area):
    """The fields of the TLV area of a Station information PDU."""
    try:
        tlvs = tlv.read(area)
    except tlv.TlvError as e:
        raise StationInfoError("tlv area", str(e)) from None
    out = {}
    seen = set()
    for tag, value in tlvs:
        name = NAMES.get(tag)
        if name is None:
            out.setdefault("other", []).append((tag, value))
            continue
        if tag in seen:
            raise StationInfoError(name, "the tag occurs a second time")
        seen.add(tag)
        if tag == KIND:
            if len(value) != 1:
                raise StationInfoError(name, "the field does not have 1 byte")
            out[name] = value[0]
        elif tag == DEVICE:
            out |= _names(name, value, ("make", "model"), "model")
        elif tag == SOFTWARE:
            out |= _names(name, value, ("software", "version"), "software")
        elif tag == DIRECTION:
            if len(value) != 2:
                raise StationInfoError(name, "the field does not have 2 bytes")
            out[name] = int.from_bytes(value, "little")
            if out[name] > 359:
                raise StationInfoError(name, "the direction is above 359")
        elif tag in (SYMBOL_CLASSIC, SYMBOL_UNICODE):
            try:
                out[name] = symbol.classic_decode(value) if tag == SYMBOL_CLASSIC else symbol.unicode_decode(value)
            except symbol.SymbolError as e:
                raise StationInfoError(name, str(e)) from None
            if {SYMBOL_CLASSIC, SYMBOL_UNICODE} <= seen:
                raise StationInfoError("symbol", "the PDU has both forms of the symbol")
        elif tag == OBJECT:
            if len(value) != 8:
                raise StationInfoError(name, "the field does not have 8 bytes")
            out[name] = int.from_bytes(value, "little")
            try:
                identifier.decode(out[name])
            except identifier.IdentifierError as e:
                raise StationInfoError(name, str(e)) from None
        else:
            try:
                out[name] = decimal_number.decode(value, infinity=False)
            except decimal_number.DecimalError as e:
                raise StationInfoError(name, str(e)) from None
            if tag != GAIN and out[name][0] < 0:
                raise StationInfoError(name, "the value is negative")
    return out


def _pair(fields, keys, alone):
    """The value of a device or software field. alone is the key of the
    name that the field has with 8 bytes."""
    if not all(k in fields for k in keys):
        if alone not in fields:
            raise ValueError(f"the field cannot have a name without `{alone}`")
        keys = (alone,)
    return b"".join(name_format.encode(fields[k]).to_bytes(8, "little") for k in keys)


def encode(fields):
    """The TLV area of the fields."""
    tlvs = list(fields.get("other", ()))
    if "kind" in fields:
        tlvs.append((KIND, bytes((fields["kind"],))))
    if "make" in fields or "model" in fields:
        tlvs.append((DEVICE, _pair(fields, ("make", "model"), "model")))
    if "software" in fields or "version" in fields:
        tlvs.append((SOFTWARE, _pair(fields, ("software", "version"), "software")))
    for tag in (POWER, HEIGHT, GAIN, RANGE):
        if NAMES[tag] in fields:
            tlvs.append((tag, decimal_number.encode(fields[NAMES[tag]])))
    if "direction" in fields:
        tlvs.append((DIRECTION, fields["direction"].to_bytes(2, "little")))
    if "symbol_classic" in fields:
        tlvs.append((SYMBOL_CLASSIC, symbol.classic_encode(fields["symbol_classic"])))
    if "symbol_unicode" in fields:
        tlvs.append((SYMBOL_UNICODE, symbol.unicode_encode(fields["symbol_unicode"])))
    if "object" in fields:
        tlvs.append((OBJECT, fields["object"].to_bytes(8, "little")))
    area = tlv.write(sorted(tlvs, key=lambda t: t[0]))
    decode(area)  # the fields are valid
    return area
