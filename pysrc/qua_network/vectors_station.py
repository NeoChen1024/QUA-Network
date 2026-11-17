# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/station-information.json, for
docs/spec/12-station-information.md.

This is the path independent of station_info.py, name_format.py, symbol.py
and tlv.py, which qua-check-vectors checks against the file. It imports
none of them. It takes the names from vectors_name.py and the symbols from
vectors_symbol.py. It packs the integers with struct, and it takes the
decimal numbers and the object identifier from vectors_position.py. It
writes the first byte of each TLV itself, with the extension byte of a
delta from 13 to 268 and of a length from 13 to 255.
"""

import struct

from qua_network.vectors_name import name
from qua_network.vectors_position import decimal, obj
from qua_network.vectors_symbol import classic, classic_bytes, unicode_bytes

DECIMALS = ((4, "power"), (5, "height"), (6, "gain"), (8, "range"))


def area(*tlvs):
    """The TLV area of (tag, value) pairs. The tags do not decrease."""
    out = b""
    before = 0
    for tag, value in tlvs:
        delta, length = tag - before, len(value)
        if not 0 <= delta <= 268 or length > 255:
            raise ValueError("the TLV has no encoding")
        out += bytes(((min(delta, 13) << 4) | min(length, 13),))
        if delta >= 13:
            out += bytes((delta - 13,))
        if length >= 13:
            out += bytes((length - 13,))
        out += value
        before = tag
    return out


def kind(code):
    return (1, struct.pack("<B", code))


def names(tag, *texts):
    return (tag, b"".join(name(t) for t in texts))


def direction(degrees):
    return (7, struct.pack("<H", degrees))


def _valid():
    out = []

    def ok(note, other=(), **fields):
        tlvs = [(tag, bytes.fromhex(value)) for tag, value in other]
        if "kind" in fields:
            tlvs.append(kind(fields["kind"]))
        if "model" in fields:
            tlvs.append(names(2, *(fields[k] for k in ("make", "model") if k in fields)))
        if "software" in fields:
            tlvs.append(names(3, *(fields[k] for k in ("software", "version") if k in fields)))
        for tag, key in DECIMALS:
            if key in fields:
                tlvs.append(decimal(tag, fields[key]))
        if "direction" in fields:
            tlvs.append(direction(fields["direction"]))
        if "symbol_classic" in fields:
            tlvs.append((9, classic_bytes(fields["symbol_classic"])))
        if "symbol_unicode" in fields:
            tlvs.append((10, unicode_bytes(int(p, 16) for p in fields["symbol_unicode"])))
        if "object" in fields:
            tlvs.append(obj(fields["object"]))
        tlvs.sort(key=lambda t: t[0])
        row = {"tlv": area(*tlvs).hex().upper()} | fields
        if other:
            row["other"] = [[tag, value] for tag, value in other]
        out.append(row | {"note": note})

    device = dict(make="EXAMPLE", model="HT1")
    software = dict(software="DEMO", version="1/2/3")
    ok("no TLV")
    ok(
        "the example of section 5",
        kind=4,
        **device,
        **software,
        power="5",
        height="2.5",
        gain="-1.5",
        range="15",
    )
    for code, text in enumerate(("other", "fixed", "portable", "pedestrian", "land vehicle", "watercraft", "aircraft")):
        ok(f"the kind {code}, {text}", kind=code)
    ok("the kind 7, balloon", kind=7)
    ok("the kind 8, spacecraft", kind=8)
    ok("the kind 9 has no kind in the table: a receiver reads it as other", kind=9)
    ok("the kind 255 has no kind in the table: a receiver reads it as other", kind=255)
    ok("a device with a make and a model", **device)
    ok("a device with a model only", model="HT1")
    ok("software with a name and a version; the version is 1.2.3", **software)
    ok("software with a name only", software="DEMO")
    ok("a name of 1 character, the smallest value", model="0")
    ok("a name of 12 characters, the largest value", model="ZZZZZZZZZZZZ")
    ok("a name of 12 characters with /", make="AB/CD/EF/GHI", model="0123456789AB")
    ok("a name that ends with /", software="DEMO/", version="24/")
    ok("a name with the characters of a callsign: its value is not that of the station identifier", model="N0CALL")
    ok("a power of 0: the station does not transmit", power="0")
    ok("a power of 100 mW", power="0.1")
    ok("a power of 1500 W", power="1500")
    ok("an antenna height of 0", height="0")
    ok("an antenna height in the format of 3 bytes", height="123.45")
    ok("a gain of 0 dBi", gain="0")
    ok("a negative gain", gain="-3.5")
    ok("a gain and a direction to the north", gain="9.5", direction=0)
    ok("the largest direction", gain="14", direction=359)
    ok("a direction and no gain", direction=225)
    ok("a range of 0", range="0")
    ok("a range with a fraction", range="2.5")
    ok("a large range", range="3200")
    ok("each field", kind=1, **device, **software, power="25", height="12", gain="6", direction=90, range="40")
    ok("a TLV with a tag that this file does not give, after the fields", kind=1, range="40", other=[(200, "AB")])
    ok("two such TLVs with one tag, and one with no value", kind=3, other=[(201, "01"), (201, "02"), (204, "")])
    ok("only a TLV with a tag that this file does not give", other=[(200, "0102030405060708")])
    ok("the information of an object", object="RPT1-B", kind=1, power="50", height="30", gain="6", range="60")
    ok(
        "each field for an object",
        object="RPT1-B",
        kind=1,
        **device,
        **software,
        power="50",
        height="30",
        gain="6",
        direction=180,
        range="60",
    )
    car = classic("/>")
    ok("a symbol in the classic form: the characters /> of APRS, a car", symbol_classic=car)
    ok("the largest number of the classic form", symbol_classic=3571)
    ok("a symbol in the Unicode form with one code point: U+1F697", symbol_unicode=["1F697"])
    ok("a symbol in the Unicode form with two code points: a flag", symbol_unicode=["1F1F9", "1F1FC"])
    ok("a kind and a symbol: the two fields are independent", kind=5, symbol_classic=car)
    ok("each field, with a symbol in the classic form", kind=4, **device, **software, power="5", range="15", symbol_classic=car)
    ok(
        "each field, with a symbol in the Unicode form",
        kind=4,
        **device,
        **software,
        power="5",
        range="15",
        symbol_unicode=["1F697"],
    )
    return out


def _invalid():
    out = []
    limit = struct.pack("<Q", 37**12)

    def bad(note, field, *tlvs):
        out.append({"tlv": (tlvs[0] if isinstance(tlvs[0], bytes) else area(*tlvs)).hex().upper(), "invalid": field, "note": note})

    bad("the kind has no byte", "kind", (1, b""))
    bad("the kind has 2 bytes", "kind", (1, b"\x04\x00"))
    bad("the kind occurs two times", "kind", kind(4), kind(4))
    bad("the device has 7 bytes", "device", (2, name("HT1")[:7]))
    bad("the device has 12 bytes", "device", (2, name("EXAMPLE") + name("HT1")[:4]))
    bad("the device has 24 bytes", "device", names(2, "EXAMPLE", "HT1", "A"))
    bad("the model has the value 0", "device", (2, bytes(8)))
    bad("the make has the value 0", "device", (2, bytes(8) + name("HT1")))
    bad("the model after a make has the value 0", "device", (2, name("EXAMPLE") + bytes(8)))
    bad("the model has the value 37^12", "device", (2, limit))
    bad("the model has the value 2^64 - 1", "device", (2, b"\xff" * 8))
    bad("the device occurs two times", "device", names(2, "HT1"), names(2, "HT1"))
    bad("the software has 9 bytes", "software", (3, name("DEMO") + b"\x00"))
    bad("the name of the software has the value 0", "software", (3, bytes(8)))
    bad("the version has the value 0", "software", (3, name("DEMO") + bytes(8)))
    bad("the version has the value 37^12", "software", (3, name("DEMO") + limit))
    bad("the software occurs two times", "software", names(3, "DEMO"), names(3, "DEMO", "2"))
    bad("the power is negative", "power", decimal(4, "-5"))
    bad("the power is an infinity", "power", decimal(4, "inf"))
    bad("the power has 1 byte", "power", (4, b"\x05"))
    bad("the power is 100 as 10 x 10^1, which is not a valid decimal number", "power", (4, bytes.fromhex("0A10")))
    bad("the antenna height is negative", "height", decimal(5, "-2.5"))
    bad("the antenna height is an infinity", "height", decimal(5, "inf"))
    bad("the antenna height has 5 bytes", "height", (5, bytes(5)))
    bad("the gain is the positive infinity", "gain", decimal(6, "inf"))
    bad("the gain is the negative infinity", "gain", decimal(6, "-inf"))
    bad("the gain occurs two times", "gain", decimal(6, "6"), decimal(6, "9"))
    bad("the direction is 360", "direction", direction(360))
    bad("the direction is 65535", "direction", direction(65535))
    bad("the direction has 1 byte", "direction", (7, b"\x5a"))
    bad("the direction has 3 bytes", "direction", (7, b"\x5a\x00\x00"))
    bad("the range is negative", "range", decimal(8, "-15"))
    bad("the range is an infinity", "range", decimal(8, "inf"))
    bad("the object identifier has 7 bytes", "object", (0, obj("RPT1-B")[1][:7]), kind(1))
    bad("the object identifier is the reserved value 0", "object", (0, bytes(8)), kind(1))
    bad("the object identifier occurs two times", "object", obj("RPT1-B"), obj("TYPHOON"), kind(1))
    car, auto = (9, classic_bytes(classic("/>"))), (10, unicode_bytes((0x1F697,)))
    bad("the classic form has the number 3572", "symbol_classic", (9, classic_bytes(3572)))
    bad("the classic form has 1 byte", "symbol_classic", (9, b"\x0c"))
    bad("the classic form has 4 bytes", "symbol_classic", (9, b"\x0c\x00\x00\x00"))
    bad("the classic form occurs two times", "symbol_classic", car, car)
    bad("the Unicode form has 2 bytes", "symbol_unicode", (10, b"\x41\x00"))
    bad("the Unicode form has 12 bytes", "symbol_unicode", (10, unicode_bytes((0x41, 0x42, 0x43))))
    bad("the Unicode form has the variation selector U+FE0F", "symbol_unicode", (10, unicode_bytes((0x2600, 0xFE0F))))
    bad("the Unicode form has a surrogate", "symbol_unicode", (10, unicode_bytes((0xD83D,))))
    bad("the Unicode form occurs two times", "symbol_unicode", auto, auto)
    bad("the PDU has both forms of the symbol", "symbol", car, auto)
    whole = area(names(2, "EXAMPLE", "HT1"))
    bad("the value of the device is beyond the end of the area", "tlv area", whole[:-1])
    bad("the extension byte of the length is beyond the end of the area", "tlv area", whole[:1])
    bad("the delta field of the first byte is 15", "tlv area", whole + b"\xf0")
    bad("the length field of the first byte is 14", "tlv area", whole + b"\x1e")
    return out


def vectors():
    return _valid() + _invalid()
