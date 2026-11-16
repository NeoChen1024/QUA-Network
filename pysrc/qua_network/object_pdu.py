# SPDX-License-Identifier: Apache-2.0
"""The TLV area of an Object PDU (docs/spec/11-object.md): the fields of an
area, and the area of a set of fields.

The fields are a dict. It has only the keys of the fields that the area
has:

- `object`: the value of the object identifier;
- `description`: the text, as bytes;
- `compressed`: True, if the description has the compressed tag;
- `end_time`: an integer count of seconds;
- `end`: True, if the area has the End TLV;
- `other`: the TLVs with a tag that the specification does not give, each
  as (tag, value).

This follows the draft, including its [proposed] rules. This module is a
research aid for checking vectors, not a reference implementation.
"""

from qua_network import identifier, tlv, usx

OBJECT, PASSTHROUGH, COMPRESSED, END_TIME, END = 0, 1, 2, 3, 4
NAMES = {OBJECT: "object", PASSTHROUGH: "description", COMPRESSED: "description", END_TIME: "end_time", END: "end"}


class ObjectError(ValueError):
    """The area is not valid. field is the name of the field with the
    invalid TLV, or `tlv area` if the area breaks 03-tlv."""

    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


def decode(area):
    """The fields of the TLV area of an Object PDU."""
    try:
        tlvs = tlv.read(area)
    except tlv.TlvError as e:
        raise ObjectError("tlv area", str(e)) from None
    out = {}
    seen = set()
    for tag, value in tlvs:
        name = NAMES.get(tag)
        if name is None:
            out.setdefault("other", []).append((tag, value))
            continue
        if tag in seen:
            raise ObjectError(name, "the tag occurs a second time")
        seen.add(tag)
        if tag == OBJECT:
            if len(value) != 8:
                raise ObjectError(name, "the field does not have 8 bytes")
            out[name] = int.from_bytes(value, "little")
            try:
                identifier.decode(out[name])
            except identifier.IdentifierError as e:
                raise ObjectError(name, str(e)) from None
        elif tag in (PASSTHROUGH, COMPRESSED):
            if name in out:
                raise ObjectError(name, "the PDU has both tags of the description")
            if tag == PASSTHROUGH:
                if not value:
                    raise ObjectError(name, "the text has no byte")
                out[name] = value
            else:
                if len(value) < 2:
                    raise ObjectError(name, "the field has fewer than 2 bytes")
                try:
                    out[name] = usx.decode(value[1:], value[0])
                except usx.Malformed as e:
                    raise ObjectError(name, str(e)) from None
                out["compressed"] = True
        elif tag == END_TIME:
            if len(value) != 8:
                raise ObjectError(name, "the field does not have 8 bytes")
            out[name] = int.from_bytes(value, "little", signed=True)
        else:
            if value:
                raise ObjectError(name, "the End TLV has a value")
            out[name] = True
    if OBJECT not in seen:
        raise ObjectError("object", "the PDU has no object identifier")
    return out


def encode(fields):
    """The TLV area of the fields. The description gets the passthrough
    tag."""
    tlvs = list(fields.get("other", ()))
    tlvs.append((OBJECT, fields["object"].to_bytes(8, "little")))
    if "description" in fields:
        tlvs.append((PASSTHROUGH, fields["description"]))
    if "end_time" in fields:
        tlvs.append((END_TIME, fields["end_time"].to_bytes(8, "little", signed=True)))
    if fields.get("end"):
        tlvs.append((END, b""))
    area = tlv.write(sorted(tlvs, key=lambda t: t[0]))
    decode(area)  # the fields are valid
    return area
