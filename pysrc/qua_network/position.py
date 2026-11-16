# SPDX-License-Identifier: Apache-2.0
"""The TLV area of a Position PDU (docs/spec/10-position.md): the fields of
an area, and the area of a set of fields.

The fields are a dict. It has only the keys of the fields that the area
has:

- `latitude`, `longitude`: integers in units of 10^-7 degree;
- `altitude`, `uncertainty`, `speed`: decimal numbers as (m, e);
- `course`: an integer in degrees;
- `time`: an integer count of seconds;
- `object`: the value of the object identifier;
- `other`: the TLVs with a tag that the specification does not give, each
  as (tag, value).

This follows the draft, including its [proposed] rules. This module is a
research aid for checking vectors, not a reference implementation.
"""

from qua_network import decimal_number, identifier, tlv

OBJECT, COORDINATES, ALTITUDE, UNCERTAINTY, COURSE, SPEED, TIME = 0, 1, 2, 3, 4, 5, 6
NAMES = {
    COORDINATES: "coordinates",
    ALTITUDE: "altitude",
    UNCERTAINTY: "uncertainty",
    COURSE: "course",
    SPEED: "speed",
    TIME: "time",
    OBJECT: "object",
}
LATITUDE = 900000000
LONGITUDE = 1800000000


class PositionError(ValueError):
    """The area is not valid. field is the name of the field with the
    invalid TLV, or `tlv area` if the area breaks 03-tlv."""

    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


def _decimal(tag, value, negative):
    try:
        number = decimal_number.decode(value, infinity=False)
    except decimal_number.DecimalError as e:
        raise PositionError(NAMES[tag], str(e)) from None
    if not negative and number[0] < 0:
        raise PositionError(NAMES[tag], "the value is negative")
    return number


def decode(area):
    """The fields of the TLV area of a Position PDU."""
    try:
        tlvs = tlv.read(area)
    except tlv.TlvError as e:
        raise PositionError("tlv area", str(e)) from None
    out = {}
    seen = set()
    for tag, value in tlvs:
        name = NAMES.get(tag)
        if name is None:
            out.setdefault("other", []).append((tag, value))
            continue
        if tag in seen:
            raise PositionError(name, "the tag occurs a second time")
        seen.add(tag)
        if tag == COORDINATES:
            if len(value) != 8:
                raise PositionError(name, "the field does not have 8 bytes")
            lat = int.from_bytes(value[:4], "little", signed=True)
            lon = int.from_bytes(value[4:], "little", signed=True)
            if not -LATITUDE <= lat <= LATITUDE:
                raise PositionError(name, "the latitude is outside its range")
            if not -LONGITUDE <= lon < LONGITUDE:
                raise PositionError(name, "the longitude is outside its range")
            out["latitude"], out["longitude"] = lat, lon
        elif tag == COURSE:
            if len(value) != 2:
                raise PositionError(name, "the field does not have 2 bytes")
            out[name] = int.from_bytes(value, "little")
            if out[name] > 359:
                raise PositionError(name, "the course is above 359")
        elif tag == TIME:
            if len(value) != 8:
                raise PositionError(name, "the field does not have 8 bytes")
            out[name] = int.from_bytes(value, "little", signed=True)
        elif tag == OBJECT:
            if len(value) != 8:
                raise PositionError(name, "the field does not have 8 bytes")
            out[name] = int.from_bytes(value, "little")
            try:
                identifier.decode(out[name])
            except identifier.IdentifierError as e:
                raise PositionError(name, str(e)) from None
        else:
            if tag == UNCERTAINTY and COORDINATES not in seen:
                raise PositionError(name, "the PDU has no coordinates")
            out[name] = _decimal(tag, value, negative=tag == ALTITUDE)
    return out


def encode(fields):
    """The TLV area of the fields."""
    tlvs = list(fields.get("other", ()))
    if "latitude" in fields:
        value = fields["latitude"].to_bytes(4, "little", signed=True) + fields["longitude"].to_bytes(4, "little", signed=True)
        tlvs.append((COORDINATES, value))
    for tag in (ALTITUDE, UNCERTAINTY, SPEED):
        if NAMES[tag] in fields:
            tlvs.append((tag, decimal_number.encode(fields[NAMES[tag]])))
    if "course" in fields:
        tlvs.append((COURSE, fields["course"].to_bytes(2, "little")))
    if "time" in fields:
        tlvs.append((TIME, fields["time"].to_bytes(8, "little", signed=True)))
    if "object" in fields:
        tlvs.append((OBJECT, fields["object"].to_bytes(8, "little")))
    area = tlv.write(sorted(tlvs, key=lambda t: t[0]))
    decode(area)  # the fields are valid
    return area
