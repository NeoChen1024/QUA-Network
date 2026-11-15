# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/hop-hash.json, vectors/pdu.json and
vectors/pdu-relay.json, for docs/spec/08-pdu.md and docs/spec/09-hop-trace.md.

This is the path independent of pdu.py, crc.py and the hop hash of
identifier.py, which qua-check-vectors checks against the files. It imports
none of them. It packs bytes with struct and has a table-driven CRC-32C. The
identifier values come from vectors/identifier.json, and the caller gives
them.
"""

import struct

HEADER = 14
LIMIT = 240  # a PDU limit for the relay vectors; the value of the specification is open
HOP_HASH_TEXTS = ("N0CALL", "N0CALL-7", "N0CALL-15", "BV5AB-33", "PJ4/KA1ABC", "YW18FIFA/MM-A")
TLV = bytes.fromhex("12AABB3101")  # two TLVs in the syntax of 03-tlv: tag 1 with 2 bytes, tag 4 with 1 byte

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

    def ok(note, limit=None, **kw):
        v = b.fields(**kw)
        if limit is not None:
            v["limit"] = limit
        v["note"] = note
        out.append(v)
        return bytes.fromhex(v["bytes"])

    def bad(note, data, reason, limit=None):
        v = {"bytes": data.hex().upper(), "invalid": reason}
        if limit is not None:
            v["limit"] = limit
        out.append(v | {"note": note})

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
    ok("padding that is not 0", **common, remaining=2, entries=["N0CALL-7"], padding=bytes.fromhex("A55AFF"))
    ok("a PDU of 24 bytes with a PDU limit of 24", limit=24, **common)
    ok("padding does not count for the PDU limit", limit=24, **common, padding=bytes.fromhex("000000"))
    ok("a PDU of 27 bytes with a PDU limit of 27", limit=27, **common, remaining=2, entries=["N0CALL-7"])

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
    bad("a PDU of 24 bytes with a PDU limit of 23", p_tlv, "size", limit=23)
    bad("a PDU of 27 bytes, with 1 entry, and a PDU limit of 24", b.close(sp + b.trailer(2, ["N0CALL-7"])), "size", limit=24)
    return out


def relay_vectors(ids):
    b = _Builder(ids)
    out = []

    def rel(note, received, relay, limit, sent, reason=None, not_radio=False):
        v = {"relay": relay, "limit": limit, "received": received.hex().upper()}
        if not_radio:
            v["not_radio"] = True
        if sent is None:
            v["sent"] = None
            v["reason"] = reason
        else:
            v["sent"] = sent.hex().upper()
        v["note"] = note
        out.append(v)

    sp = b.source_part("N0CALL-15", 0x1234, 3, TLV, 1)
    close, trailer = b.close, b.trailer
    r0 = close(sp + trailer(3))
    r1 = close(sp + trailer(2, ["N0CALL-7"]))
    r2 = close(sp + trailer(1, ["N0CALL-7", "BV5AB-33"]))
    r3 = close(sp + trailer(0, ["N0CALL-7", "BV5AB-33", "PJ4/KA1ABC"]))
    two = close(sp + trailer(0, ["BV5AB-33", "PJ4/KA1ABC"]))
    base = len(sp) + 1 + 4  # the PDU with no entry
    rel("the first relay adds its entry", r0, "N0CALL-7", LIMIT, r1)
    rel("the second relay", r1, "BV5AB-33", LIMIT, r2)
    rel("the third relay; no hop remains after it", r2, "PJ4/KA1ABC", LIMIT, r3)
    rel("a relay does not send the padding on", r0 + bytes.fromhex("A55AFF"), "N0CALL-7", LIMIT, r1)
    rel("room for 2 entries: the relay drops the oldest entry", r2, "PJ4/KA1ABC", base + 6, two)
    rel("room for 2 entries and 2 bytes more: the same result", r2, "PJ4/KA1ABC", base + 8, two)
    one = close(sp + trailer(1, ["BV5AB-33"]))
    rel("room for 1 entry: only the entry of the relay stays", one, "PJ4/KA1ABC", base + 3, close(sp + trailer(0, ["PJ4/KA1ABC"])))
    rel("room for no entry: the trailer has only the control byte", r0, "N0CALL-7", base, close(sp + trailer(2)))
    rel("room for no entry, 2 bytes free", r0, "N0CALL-7", base + 2, close(sp + trailer(2)))
    note = "the trace is already truncated; the relay adds its entry"
    rel(note, close(sp + trailer(1, ["BV5AB-33"])), "PJ4/KA1ABC", LIMIT, two)
    note = "the relay got the PDU over a path that is not radio: it sets the bit Not Radio"
    rel(note, r0, "N0CALL-7", LIMIT, close(sp + trailer(2, ["N0CALL-7"], not_radio=1)), not_radio=True)
    received = close(sp + trailer(2, ["N0CALL-7"], not_radio=1, res=1))
    sent = close(sp + trailer(1, ["N0CALL-7", "BV5AB-33"], not_radio=1, res=1))
    rel("the relay keeps the bit Not Radio and copies the reserved bit", received, "BV5AB-33", LIMIT, sent)
    rel("the hops remaining are 0", r3, "YW18FIFA/MM-A", LIMIT, None, "no hop remains")
    rel("the hop limit is 0", close(b.source_part("N0CALL", 0, 0) + trailer(0)), "N0CALL-7", LIMIT, None, "no hop remains")
    rel("the hash of the relay is one of the entries", r2, "N0CALL-7", LIMIT, None, "own entry")
    flipped = bytearray(r1)
    flipped[15] ^= 0x01
    rel("the checksum is not good", bytes(flipped), "BV5AB-33", LIMIT, None, "invalid")
    note = "the trailer is not valid: the hops remaining are more than the hop limit"
    rel(note, close(sp + trailer(4)), "N0CALL-7", LIMIT, None, "invalid")
    rel("the PDU is larger than the PDU limit with no entry", r0, "N0CALL-7", base - 1, None, "invalid")
    rel("the PDU as received is larger than the PDU limit", r2, "PJ4/KA1ABC", base + 3, None, "invalid")
    return out
