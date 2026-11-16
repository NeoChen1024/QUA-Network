# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/position.json, for docs/spec/10-position.md.

This is the path independent of position.py and tlv.py, which
qua-check-vectors checks against the file. It imports neither. It packs the
integers with struct, takes the decimal numbers from vectors_decimal.py, and
writes the first byte of each TLV itself. It writes only a TLV with a delta
and a length of 12 at most, which has no extension byte. It has its own
computation of an identifier, for a text with no SSID or with an SSID of one
character.
"""

import struct
from datetime import datetime, timezone

from qua_network.vectors_decimal import pack, pair

INT64_MIN, INT64_MAX = -(1 << 63), (1 << 63) - 1


def area(*tlvs):
    """The TLV area of (tag, value) pairs. The tags do not decrease."""
    out = b""
    before = 0
    for tag, value in tlvs:
        if not 0 <= tag - before <= 12 or len(value) > 12:
            raise ValueError("the TLV needs an extension byte")
        out += bytes((((tag - before) << 4) | len(value),)) + value
        before = tag
    return out


def coordinates(lat, lon):
    return (1, struct.pack("<ii", lat, lon))


def decimal(tag, text):
    return (tag, pack(*pair(text)))


def course(degrees):
    return (4, struct.pack("<H", degrees))


def time(count):
    return (6, struct.pack("<q", count))


def obj(text):
    """The TLV of an object identifier: the callsign as a number in base
    37, then one digit for the SSID."""
    digits = "/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    name, _, ssid = text.partition("-")
    value = 0
    for c in name + (ssid or "/"):
        value = value * 37 + digits.index(c)
    return (0, struct.pack("<Q", value))


if obj("N0CALL-7")[1] != struct.pack("<Q", 0x0000000E5BEBEB45) or obj("PJ4/KA1ABC")[1] != struct.pack("<Q", 0x01C577F1F48964A5):
    raise AssertionError("the identifier is not the value of vectors/identifier.json")


def date(count):
    return datetime.fromtimestamp(count, timezone.utc).strftime("%Y-%m-%d, %H:%M:%S UTC")


def _valid():
    out = []

    def ok(note, other=(), **fields):
        tlvs = [(tag, bytes.fromhex(value)) for tag, value in other]
        if "latitude" in fields:
            tlvs.append(coordinates(fields["latitude"], fields["longitude"]))
        for tag, name in ((2, "altitude"), (3, "uncertainty"), (5, "speed")):
            if name in fields:
                tlvs.append(decimal(tag, fields[name]))
        if "course" in fields:
            tlvs.append(course(fields["course"]))
        if "time" in fields:
            tlvs.append(time(fields["time"]))
            fields["time"] = str(fields["time"])
        if "object" in fields:
            tlvs.append(obj(fields["object"]))
        tlvs.sort(key=lambda t: t[0])
        row = {"tlv": area(*tlvs).hex().upper()} | fields
        if other:
            row["other"] = [[tag, value] for tag, value in other]
        out.append(row | {"note": note})

    here = dict(latitude=242500000, longitude=1206700000)
    now = 1794787200
    ok("no TLV: the source states only that it has no coordinates")
    ok("the example of section 6", **here, altitude="152", course=90, speed="62")
    ok("coordinates only: the equator and the prime meridian", latitude=0, longitude=0)
    ok("a place south of the equator and west of the prime meridian", latitude=-338688000, longitude=-706693000)
    ok("the north pole, and the largest longitude", latitude=900000000, longitude=1799999999)
    ok("the south pole, and the meridian of 180 degrees", latitude=-900000000, longitude=-1800000000)
    ok("the smallest step from the equator and the prime meridian", latitude=1, longitude=-1)
    ok(f"each field; the time is {date(now)}", **here, altitude="152", uncertainty="15", course=90, speed="62", time=now)
    ok("an altitude below the mean sea level", **here, altitude="-28.5")
    ok("an altitude in the format of 3 bytes", **here, altitude="1234.5")
    ok("an altitude in the format of 4 bytes", **here, altitude="8848.86")
    ok("rounded coordinates with a horizontal uncertainty", latitude=242000000, longitude=1207000000, uncertainty="5000")
    ok("a horizontal uncertainty of 0", **here, uncertainty="0")
    ok("a horizontal uncertainty of 1 cm", **here, uncertainty="0.01")
    ok("a course and no speed; north is 0", **here, course=0)
    ok("the largest course", **here, course=359)
    ok("a speed and no course; the station does not move", **here, speed="0")
    ok("a speed with a fraction", **here, speed="5.4")
    ok("a large speed", **here, altitude="408000", course=51, speed="27600")
    ok(f"no coordinates: an altitude and a time, {date(now)}", altitude="152", time=now)
    ok("no coordinates: a course and a speed", course=270, speed="12")
    ok(f"the time 0 is {date(0)}", **here, time=0)
    ok(f"the time -1 is {date(-1)}", **here, time=-1)
    ok(f"the time 2^32 is {date(1 << 32)}", **here, time=1 << 32)
    ok("the smallest time", time=INT64_MIN)
    ok("the largest time", time=INT64_MAX)
    ok("a TLV with a tag that this file does not give, after the fields", **here, time=now, other=[(8, "AB")])
    ok("two such TLVs with one tag, and one with no value", **here, other=[(9, "01"), (9, "02"), (12, "")])
    ok("only a TLV with a tag that this file does not give", other=[(8, "0102030405060708")])
    ok("the position of an object", **here, object="RPT1-B")
    ok(
        f"each field for an object; the time is {date(now)}",
        **here,
        altitude="152",
        course=90,
        speed="62",
        time=now,
        object="TYPHOON",
    )
    ok("an object with no coordinates", object="TYPHOON")
    ok("an object with the identifier of a callsign", latitude=0, longitude=0, object="N0CALL-7")
    return out


def _invalid():
    out = []
    here = coordinates(242500000, 1206700000)

    def bad(note, field, *tlvs):
        out.append({"tlv": (tlvs[0] if isinstance(tlvs[0], bytes) else area(*tlvs)).hex().upper(), "invalid": field, "note": note})

    bad("the coordinates have 7 bytes", "coordinates", (1, here[1][:7]))
    bad("the coordinates have 9 bytes", "coordinates", (1, here[1] + b"\x00"))
    bad("the latitude is 90 degrees and one step", "coordinates", coordinates(900000001, 0))
    bad("the latitude is -90 degrees and one step", "coordinates", coordinates(-900000001, 0))
    bad("the longitude is 180 degrees", "coordinates", coordinates(0, 1800000000))
    bad("the longitude is -180 degrees and one step", "coordinates", coordinates(0, -1800000001))
    bad("the coordinates occur two times", "coordinates", here, here)
    bad("the altitude is the positive infinity", "altitude", here, decimal(2, "inf"))
    bad("the altitude is the negative infinity", "altitude", here, decimal(2, "-inf"))
    bad("the altitude has 1 byte", "altitude", here, (2, b"\x98"))
    bad("the altitude has 5 bytes", "altitude", here, (2, bytes(5)))
    bad("the altitude is 100 as 10 x 10^1, which is not a valid decimal number", "altitude", here, (2, bytes.fromhex("0A10")))
    bad("the horizontal uncertainty is negative", "uncertainty", here, decimal(3, "-15"))
    bad("the horizontal uncertainty is an infinity", "uncertainty", here, decimal(3, "inf"))
    bad("a horizontal uncertainty, and no coordinates", "uncertainty", decimal(3, "15"))
    bad("the horizontal uncertainty occurs two times", "uncertainty", here, decimal(3, "15"), decimal(3, "20"))
    bad("the course is 360", "course", here, course(360))
    bad("the course is 65535", "course", here, course(65535))
    bad("the course has 1 byte", "course", here, (4, b"\x5a"))
    bad("the course has 3 bytes", "course", here, (4, b"\x5a\x00\x00"))
    bad("the speed is negative", "speed", here, decimal(5, "-1"))
    bad("the speed is an infinity", "speed", here, decimal(5, "inf"))
    bad("the time has 4 bytes", "time", here, (6, struct.pack("<I", 1794787200)))
    bad("the time has 9 bytes", "time", here, (6, struct.pack("<q", 1794787200) + b"\x00"))
    bad("the time occurs two times", "time", time(1794787200), time(1794787201))
    bad("the object identifier has 7 bytes", "object", (0, obj("RPT1-B")[1][:7]), here)
    bad("the object identifier is the reserved value 0", "object", (0, bytes(8)), here)
    bad("the object identifier occurs two times", "object", obj("RPT1-B"), obj("TYPHOON"), here)
    whole = area(here)
    bad("the value of the coordinates is beyond the end of the area", "tlv area", whole[:-1])
    bad("the delta field of the first byte is 15", "tlv area", whole + b"\xf0")
    bad("the length field of the first byte is 14", "tlv area", whole + b"\x1e")
    return out


def vectors():
    return _valid() + _invalid()
