# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/object.json, for docs/spec/11-object.md.

This is the path independent of object_pdu.py, tlv.py and usx.py, which
qua-check-vectors checks against the file. It imports none of them. It packs
the integers with struct and writes the first byte and the extension byte of
each TLV itself. The computation of an object identifier is that of
vectors_position.py. The compressed strings come from
vectors/text-compression.json, and the caller gives them.
"""

import struct

from qua_network.vectors_position import INT64_MAX, INT64_MIN, date, obj

PASSTHROUGH, COMPRESSED, END_TIME, END = 1, 2, 3, 4
COMPRESSED_TEXTS = ("Monitoring 145.500 MHz FM", "testing testing testing", "Hello")


def area(*tlvs):
    """The TLV area of (tag, value) pairs. The tags do not decrease. A
    delta is 12 at most. A length from 13 has an extension byte."""
    out = b""
    before = 0
    for tag, value in tlvs:
        if not 0 <= tag - before <= 12 or len(value) > 255:
            raise ValueError("the TLV has no encoding here")
        n = len(value)
        out += bytes((((tag - before) << 4) | min(n, 13),)) + (bytes((n - 13,)) if n >= 13 else b"") + value
        before = tag
    return out


def end_time(count):
    return (END_TIME, struct.pack("<q", count))


def vectors(texts):
    """texts is the rows of vectors/text-compression.json."""
    packed = {row["text"]: bytes((row["length"],)) + bytes.fromhex(row["compressed"]) for row in texts if "text" in row}
    broken = next(row for row in texts if row.get("invalid") == 2 and row["length"] == 5)
    out = []

    def ok(note, name, description=None, compressed=False, time=None, end=False, other=()):
        tlvs = [obj(name)]
        row = {"object": name}
        if description is not None:
            row["description"] = description
            if compressed:
                row["compressed"] = True
                tlvs.append((COMPRESSED, packed[description]))
            else:
                tlvs.append((PASSTHROUGH, description.encode("utf-8")))
        if time is not None:
            row["end_time"] = str(time)
            tlvs.append(end_time(time))
        if end:
            row["end"] = True
            tlvs.append((END, b""))
        if other:
            row["other"] = [[tag, value] for tag, value in other]
            tlvs.extend((tag, bytes.fromhex(value)) for tag, value in other)
        tlvs.sort(key=lambda t: t[0])
        out.append({"tlv": area(*tlvs).hex().upper()} | row | {"note": note})

    def bad(note, field, *tlvs):
        data = tlvs[0] if isinstance(tlvs[0], bytes) else area(*tlvs)
        out.append({"tlv": data.hex().upper(), "invalid": field, "note": note})

    now = 1794787200
    later = now + 7 * 86400
    ok("the smallest Object PDU: the object exists", "TYPHOON")
    ok("the example of section 6: a description", "TYPHOON", "Typhoon Champi")
    ok("the example of section 6: the end of the object", "TYPHOON", end=True)
    ok("a description of 1 byte", "RPT1-B", "R")
    ok("a description of 12 bytes: the largest length with no extension byte", "RPT1-B", "Repeater 1 B")
    ok("a description of 13 bytes: the smallest length with an extension byte", "RPT1-B", "Repeater 1 B.")
    ok("a description with characters of 2, 3 and 4 bytes", "TYPHOON", "Tajfun é 颱風 🌀")
    ok("a description of 200 bytes", "TYPHOON", "0123456789" * 20)
    ok("a compressed description", "RPT1-B", COMPRESSED_TEXTS[0], compressed=True)
    ok("a compressed description with a repeat", "RPT1-B", COMPRESSED_TEXTS[1], compressed=True)
    ok("a compressed description that is not shorter than the text", "RPT1-B", COMPRESSED_TEXTS[2], compressed=True)
    ok(f"an end time, {date(later)}", "TYPHOON", time=later)
    ok(f"a description and an end time, {date(later)}", "TYPHOON", "Typhoon Champi", time=later)
    ok("the smallest end time", "TYPHOON", time=INT64_MIN)
    ok("the largest end time", "TYPHOON", time=INT64_MAX)
    ok("the end, with a description and an end time that have no effect", "TYPHOON", "Typhoon Champi", time=now, end=True)
    ok("an object with the identifier of a callsign", "N0CALL-7", "Net control")
    ok("a TLV with a tag that this file does not give", "TYPHOON", "Typhoon Champi", other=[(5, "AB"), (12, "")])

    typhoon = obj("TYPHOON")
    text = (PASSTHROUGH, b"Typhoon Champi")
    bad("no TLV: the object identifier is absent", "object", b"")
    bad("a description, and no object identifier", "object", text)
    bad("the object identifier has 7 bytes", "object", (0, typhoon[1][:7]))
    bad("the object identifier is the reserved value 0", "object", (0, bytes(8)))
    bad("the object identifier occurs two times", "object", typhoon, obj("RPT1-B"))
    bad("the description has no byte", "description", typhoon, (PASSTHROUGH, b""))
    bad("the description occurs two times", "description", typhoon, text, text)
    bad("the PDU has both tags of the description", "description", typhoon, text, (COMPRESSED, packed["Hello"]))
    bad("the compressed description has only the length byte", "description", typhoon, (COMPRESSED, b"\x05"))
    note = "the compressed string is invalid: its first bit is 0"
    bad(note, "description", typhoon, (COMPRESSED, bytes((broken["length"],)) + bytes.fromhex(broken["compressed"])))
    bad("the end time has 4 bytes", "end_time", typhoon, (END_TIME, struct.pack("<I", now)))
    bad("the end time occurs two times", "end_time", typhoon, end_time(now), end_time(later))
    bad("the End TLV has a value of 1 byte", "end", typhoon, (END, b"\x01"))
    bad("the End TLV occurs two times", "end", typhoon, (END, b""), (END, b""))
    whole = area(typhoon, text)
    bad("the value of the description is beyond the end of the area", "tlv area", whole[:-1])
    bad("the extension byte of the length is 243", "tlv area", area(typhoon) + b"\x1d\xf3" + bytes(64))
    return out
