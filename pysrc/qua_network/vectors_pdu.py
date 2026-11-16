# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/hop-hash.json, vectors/pdu.json,
vectors/pdu-unit.json and vectors/pdu-relay.json, for docs/spec/08-pdu.md and
docs/spec/09-hop-trace.md.

This is the path independent of pdu.py, crc.py and the hop hash of
identifier.py, which qua-check-vectors checks against the files. It imports
none of them. It packs bytes with struct and has a table-driven CRC-32C. The
identifier values come from vectors/identifier.json, and the caller gives
them.
"""

import struct

HEADER = 14
HOP_HASH_TEXTS = ("N0CALL", "N0CALL-7", "N0CALL-15", "BV5AB-33", "PJ4/KA1ABC", "YW18FIFA/MM-A")
TLV = bytes.fromhex("12AABB3101")  # two TLVs in the syntax of 03-tlv: tag 1 with 2 bytes, tag 4 with 1 byte


def tlv_area(n):
    """A TLV area of n bytes, from 15 to 257: one TLV with the tag 1."""
    return bytes((0x1D, n - 15)) + bytes(i % 251 for i in range(n - 2))


_TABLE = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ 0x82F63B78 if _c & 1 else _c >> 1
    _TABLE.append(_c)


def crc32c(data):
    c = 0xFFFFFFFF
    for b in data:
        c = _TABLE[(c ^ b) & 0xFF] ^ (c >> 8)
    return c ^ 0xFFFFFFFF


if crc32c(b"123456789") != 0xE3069283:
    raise AssertionError("the CRC-32C does not give the check value")


def hop_hash_vectors(ids):
    """ids is the text form and the value of each identifier."""
    out = []
    for text in HOP_HASH_TEXTS:
        wire = struct.pack("<Q", ids[text])
        h = crc32c(wire) & 0xFFFFFF
        row = {"text": text, "identifier": f"{ids[text]:016X}", "identifier_bytes": wire.hex().upper()}
        out.append(row | {"hash": f"{h:06X}", "hash_bytes": struct.pack("<I", h)[:3].hex().upper()})
    return out


class _Builder:
    def __init__(self, ids):
        self.ids = ids
        self.hash = {v["text"]: int(v["hash"], 16) for v in hop_hash_vectors(ids)}

    def source_part(self, src, seq, hop, tlv=b"", typ=0, major=0, minor=0, ni=0, tr=0, res=0, slen=None):
        version = (major << 5) | (minor << 1) | 1
        second = (hop << 5) | (ni << 4) | (tr << 3) | res
        length = HEADER + len(tlv) if slen is None else slen
        return bytes((version, second, typ, length)) + struct.pack("<QH", self.ids[src], seq) + tlv

    def trailer(self, remaining, entries=(), not_radio=0, res=0, count=None):
        n = len(entries) if count is None else count
        control = (not_radio << 7) | (res << 6) | (n << 3) | remaining
        return bytes((control,)) + b"".join(struct.pack("<I", self.hash[e])[:3] for e in entries)

    @staticmethod
    def close(body, big=False):
        return body + struct.pack(">I" if big else "<I", crc32c(body))

    def fields(
        self,
        src,
        seq,
        hop,
        tlv=b"",
        typ=0,
        major=0,
        minor=0,
        ni=0,
        tr=0,
        res=0,
        remaining=None,
        entries=(),
        not_radio=0,
        tres=0,
        padding=b"",
    ):
        remaining = hop if remaining is None else remaining
        sp = self.source_part(src, seq, hop, tlv, typ, major, minor, ni, tr, res)
        data = self.close(sp + self.trailer(remaining, entries, not_radio, tres))
        return {
            "bytes": (data + padding).hex().upper(),
            "version": [major, minor],
            "hop_limit": hop,
            "no_internet": bool(ni),
            "translated": bool(tr),
            "authenticated": False,
            "reserved": res,
            "type": typ,
            "source_length": len(sp),
            "source": src,
            "sequence": seq,
            "tlv": tlv.hex().upper(),
            "not_radio": bool(not_radio),
            "trailer_reserved": tres,
            "entry_count": len(entries),
            "hops_remaining": remaining,
            "entries": [f"{self.hash[e]:06X}" for e in entries],
            "length": len(data),
            "padding": padding.hex().upper(),
        }


def pdu_vectors(ids):
    b = _Builder(ids)
    out = []

    def ok(note, **kw):
        v = b.fields(**kw)
        v["note"] = note
        out.append(v)
        return bytes.fromhex(v["bytes"])

    def bad(note, data, reason):
        out.append({"bytes": data.hex().upper(), "invalid": reason, "note": note})

    common = dict(src="N0CALL-15", seq=0x1234, hop=3, tlv=TLV, typ=1)
    seven = ["N0CALL-7", "N0CALL-15", "BV5AB-33", "PJ4/KA1ABC", "YW18FIFA/MM-A", "N0CALL-7", "BV5AB-33"]
    p_min = ok("the smallest PDU: no TLV, hop limit 0", src="N0CALL", seq=0, hop=0)
    p_tlv = ok("a TLV area of 5 bytes; the sequence number 0x1234 is the bytes 34 12", **common)
    ok("the flag No Internet, and the last sequence number", src="BV5AB-33", seq=0xFFFF, hop=7, tlv=TLV, typ=2, ni=1)
    ok("the flag Translated; a receiver ignores the reserved bits", src="PJ4/KA1ABC", seq=1, hop=1, typ=3, tr=1, res=3)
    ok("version 1.0", src="N0CALL", seq=2, hop=2, major=1, minor=0)
    ok("version 7.15, the largest version byte", src="N0CALL", seq=2, hop=2, major=7, minor=15)
    ok("one relay sent the PDU on", **common, remaining=2, entries=["N0CALL-7"])
    ok("three relays", **common, remaining=0, entries=["N0CALL-7", "BV5AB-33", "PJ4/KA1ABC"])
    ok("a truncated trace: 3 hops taken, and 1 entry", **common, remaining=0, entries=["PJ4/KA1ABC"])
    ok("a truncated trace with no entry", **common, remaining=1, entries=[])
    ok("seven relays", src="N0CALL", seq=7, hop=7, remaining=0, entries=seven)
    note = "the bit Not Radio, and the reserved bit of the control byte"
    ok(note, src="N0CALL", seq=8, hop=2, remaining=1, entries=["N0CALL-7"], not_radio=1, tres=1)
    ok("3 bytes of padding after the PDU", **common, padding=bytes.fromhex("000000"))
    ok("1 byte of padding after a PDU with an entry", **common, remaining=2, entries=["N0CALL-7"], padding=b"\x00")
    big = dict(src="N0CALL-15", seq=0x1234, hop=3, typ=1)
    ok("a PDU of 255 bytes, the PDU limit: the source part has 250 bytes", **big, tlv=tlv_area(236))
    ok("padding does not count for the PDU limit", **big, tlv=tlv_area(236), padding=bytes.fromhex("000000"))
    ok(
        "a PDU of 255 bytes with 1 entry: the source part has 247 bytes",
        **big,
        tlv=tlv_area(233),
        remaining=2,
        entries=["N0CALL-7"],
    )

    sp = b.source_part("N0CALL-15", 0x1234, 3, TLV, 1)
    bad("no bytes", b"", "not a PDU")
    bad("the least significant bit of the first byte is 0", b.close(b"\x00" + p_min[1:15]), "not a PDU")
    bad("13 bytes: fewer than a header", p_min[:13], "short")
    bad("the PDU without its last byte", p_tlv[:-1], "short")
    bad("the source part alone", p_tlv[:19], "short")
    bad("the source length is 13", b.close(b.source_part("N0CALL", 0, 0, slen=13) + b.trailer(0)), "source length")
    bad("the source length is 0", b.close(b.source_part("N0CALL", 0, 0, slen=0) + b.trailer(0)), "source length")
    bad("the entry count is 2, and the PDU has 1 entry", b.close(sp + b.trailer(1, ["N0CALL-7"], count=2)), "short")
    flipped = bytearray(p_tlv)
    flipped[15] ^= 0x01
    bad("one bit of the TLV area is changed", bytes(flipped), "checksum")
    bad("the checksum is in big-endian order", b.close(sp + b.trailer(3), big=True), "checksum")
    flipped = bytearray(p_tlv)
    flipped[-1] ^= 0x80
    bad("one bit of the checksum is changed", bytes(flipped), "checksum")
    bad("the hops remaining are 4, and the hop limit is 3", b.close(sp + b.trailer(4)), "trailer")
    bad("the entry count is 2, and 1 hop is taken", b.close(sp + b.trailer(2, ["N0CALL-7", "BV5AB-33"])), "trailer")
    bad("the entry count is 1, and no hop is taken", b.close(sp + b.trailer(3, ["N0CALL-7"])), "trailer")
    bad(
        "a PDU of 256 bytes: the source part has 251 bytes",
        b.close(b.source_part("N0CALL-15", 0x1234, 3, tlv_area(237), 1) + b.trailer(3)),
        "size",
    )
    over = b.close(b.source_part("N0CALL-15", 0x1234, 3, tlv_area(236), 1) + b.trailer(2, ["N0CALL-7"]))
    bad("a PDU of 258 bytes: the source part has 250 bytes, and there is 1 entry", over, "size")
    return out


def unit_vectors(ids):
    """Link units of 08-pdu section 7.1: the PDUs that a receiver reads, and
    the bytes that it does not use."""
    b = _Builder(ids)
    out = []

    def pdu(src, seq, tlv=TLV, typ=1, hop=3, **kw):
        return b.close(b.source_part(src, seq, hop, tlv, typ) + b.trailer(kw.pop("remaining", hop), **kw))

    def unit(note, pdus, rest=b""):
        out.append(
            {
                "unit": (b"".join(pdus) + rest).hex().upper(),
                "pdus": [p.hex().upper() for p in pdus],
                "rest": rest.hex().upper(),
                "note": note,
            }
        )

    one = pdu("N0CALL-15", 0x1234)
    two = pdu("N0CALL-15", 0x1235, tlv=b"", typ=2)
    other = pdu("BV5AB-33", 7, remaining=2, entries=["N0CALL-7"])
    least = pdu("N0CALL", 0, tlv=b"", typ=0, hop=0)
    large = pdu("N0CALL-15", 0x1236, tlv=tlv_area(236))
    unit("one PDU", [one])
    unit("two PDUs of one source", [one, two])
    unit("three PDUs of two sources; one has an entry", [one, other, two])
    unit("twelve PDUs of 19 bytes", [least] * 12)
    unit("two PDUs and 3 bytes of padding", [one, two], bytes(3))
    unit("one PDU and 1 byte of padding", [one], bytes(1))
    unit("a unit of 274 bytes: the PDU limit applies to each PDU", [large, least])
    unit("padding, and then a PDU: the receiver stops at the padding", [one], bytes(1) + two)
    unit("a byte that is not 0 and has the least significant bit 0", [one], b"\x02" + two)
    flipped = bytearray(two)
    flipped[5] ^= 0x01
    unit("the second PDU has a wrong checksum: the receiver stops there", [one], bytes(flipped) + other)
    unit("the second PDU is not complete", [one], two[:-1])
    unit("a byte with the least significant bit 1 that starts no PDU", [one], b"\xa5\x5a\xff")
    too_large = b.close(b.source_part("N0CALL-15", 0x1237, 3, tlv_area(237), 1) + b.trailer(3))
    unit("the second PDU is larger than the PDU limit", [one], too_large + two)
    unit("the first PDU is invalid: the receiver reads no PDU", [], bytes(flipped) + one)
    unit("the first byte has the least significant bit 0", [], b"\x00" + one)
    unit("no bytes", [])
    return out


def relay_vectors(ids):
    b = _Builder(ids)
    out = []

    def rel(note, received, relay, sent, reason=None, not_radio=False):
        v = {"relay": relay, "received": received.hex().upper()}
        if not_radio:
            v["not_radio"] = True
        if sent is None:
            v["sent"] = None
            v["reason"] = reason
        else:
            v["sent"] = sent.hex().upper()
        v["note"] = note
        out.append(v)

    def sized(n):
        """A source part of n bytes."""
        return b.source_part("N0CALL-15", 0x1234, 3, tlv_area(n - HEADER), 1)

    sp = b.source_part("N0CALL-15", 0x1234, 3, TLV, 1)
    close, trailer = b.close, b.trailer
    r0 = close(sp + trailer(3))
    r1 = close(sp + trailer(2, ["N0CALL-7"]))
    r2 = close(sp + trailer(1, ["N0CALL-7", "BV5AB-33"]))
    r3 = close(sp + trailer(0, ["N0CALL-7", "BV5AB-33", "PJ4/KA1ABC"]))
    rel("the first relay adds its entry", r0, "N0CALL-7", r1)
    rel("the second relay", r1, "BV5AB-33", r2)
    rel("the third relay; no hop remains after it", r2, "PJ4/KA1ABC", r3)
    rel("a relay does not send the padding on", r0 + bytes.fromhex("000000"), "N0CALL-7", r1)
    for n, note in ((244, "a PDU of 255 bytes with 2 entries"), (242, "a PDU of 253 bytes with 2 entries")):
        received = close(sized(n) + trailer(1, ["N0CALL-7", "BV5AB-33"]))
        sent = close(sized(n) + trailer(0, ["BV5AB-33", "PJ4/KA1ABC"]))
        rel(note + ": the relay drops the oldest entry", received, "PJ4/KA1ABC", sent)
    received = close(sized(247) + trailer(1, ["BV5AB-33"]))
    rel(
        "a PDU of 255 bytes with 1 entry: only the entry of the relay stays",
        received,
        "PJ4/KA1ABC",
        close(sized(247) + trailer(0, ["PJ4/KA1ABC"])),
    )
    note = "a PDU of 255 bytes with no entry: the trailer has only the control byte"
    rel(note, close(sized(250) + trailer(3)), "N0CALL-7", close(sized(250) + trailer(2)))
    note = "a PDU of 253 bytes with no entry: 2 bytes are free, and an entry has 3"
    rel(note, close(sized(248) + trailer(3)), "N0CALL-7", close(sized(248) + trailer(2)))
    note = "the trace is already truncated; the relay adds its entry"
    rel(note, close(sp + trailer(1, ["BV5AB-33"])), "PJ4/KA1ABC", close(sp + trailer(0, ["BV5AB-33", "PJ4/KA1ABC"])))
    note = "the relay got the PDU over a path that is not radio: it sets the bit Not Radio"
    rel(note, r0, "N0CALL-7", close(sp + trailer(2, ["N0CALL-7"], not_radio=1)), not_radio=True)
    received = close(sp + trailer(2, ["N0CALL-7"], not_radio=1, res=1))
    sent = close(sp + trailer(1, ["N0CALL-7", "BV5AB-33"], not_radio=1, res=1))
    rel("the relay keeps the bit Not Radio and copies the reserved bit", received, "BV5AB-33", sent)
    rel("the hops remaining are 0", r3, "YW18FIFA/MM-A", None, "no hop remains")
    rel("the hop limit is 0", close(b.source_part("N0CALL", 0, 0) + trailer(0)), "N0CALL-7", None, "no hop remains")
    rel("the hash of the relay is one of the entries", r2, "N0CALL-7", None, "own entry")
    flipped = bytearray(r1)
    flipped[15] ^= 0x01
    rel("the checksum is not good", bytes(flipped), "BV5AB-33", None, "invalid")
    note = "the trailer is not valid: the hops remaining are more than the hop limit"
    rel(note, close(sp + trailer(4)), "N0CALL-7", None, "invalid")
    rel("a PDU of 256 bytes with no entry", close(sized(251) + trailer(3)), "N0CALL-7", None, "invalid")
    rel(
        "a PDU of 258 bytes with 2 entries", close(sized(247) + trailer(1, ["N0CALL-7", "BV5AB-33"])), "PJ4/KA1ABC", None, "invalid"
    )
    return out
