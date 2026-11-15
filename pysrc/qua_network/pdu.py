# SPDX-License-Identifier: Apache-2.0
"""The parts of a PDU (docs/spec/08-pdu.md) and the hop trace
(docs/spec/09-hop-trace.md): parse a PDU, and send one on as a relay.

This follows the drafts, including their [proposed] rules. The TLV area is
bytes that this module does not read. The length of the authentication tag
is open, so a caller gives it. This module is a research aid for checking
vectors, not a reference implementation.
"""

from qua_network import identifier
from qua_network.crc import crc32c

HEADER = 14
CHECKSUM = 4
ENTRY = 3


class PduError(ValueError):
    """The bytes are not a valid PDU. reason is one of: `not a PDU`,
    `source length`, `short`, `size`, `checksum`, `trailer`."""

    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


class NotSentOn(ValueError):
    """A relay does not send the PDU on. reason is one of: `invalid`,
    `no hop remains`, `own entry`."""

    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


def parse(data, tag_length=None, limit=None):
    """The fields of the PDU at the start of data, as a dict. Bytes after
    the PDU are padding. limit, if given, is the PDU limit in bytes."""
    if not data or not data[0] & 1:
        raise PduError("not a PDU", "the least significant bit of the first byte is not 1")
    if len(data) < HEADER:
        raise PduError("short", "fewer bytes than a header")
    source_length = data[3]
    if source_length < HEADER:
        raise PduError("source length", "the source length is less than 14")
    authenticated = bool(data[1] & 0x04)
    if authenticated and tag_length is None:
        raise NotImplementedError("the length of the authentication tag is open")
    control_at = source_length + (tag_length if authenticated else 0)
    if len(data) <= control_at:
        raise PduError("short", "fewer bytes than the source part, the tag and the control byte")
    control = data[control_at]
    entry_count = (control >> 3) & 7
    length = control_at + 1 + ENTRY * entry_count + CHECKSUM
    if len(data) < length:
        raise PduError("short", "fewer bytes than the length of the PDU")
    if limit is not None and length > limit:
        raise PduError("size", "the PDU is larger than the PDU limit")
    if crc32c(data[: length - CHECKSUM]) != int.from_bytes(data[length - CHECKSUM : length], "little"):
        raise PduError("checksum", "the checksum is not the CRC-32C of the bytes before it")
    hop_limit = data[1] >> 5
    hops_remaining = control & 7
    if hops_remaining > hop_limit:
        raise PduError("trailer", "the hops remaining are more than the hop limit")
    if entry_count > hop_limit - hops_remaining:
        raise PduError("trailer", "the entry count is more than the hops taken")
    entries_at = control_at + 1
    return {
        "version": [data[0] >> 5, (data[0] >> 1) & 15],
        "hop_limit": hop_limit,
        "no_internet": bool(data[1] & 0x10),
        "translated": bool(data[1] & 0x08),
        "authenticated": authenticated,
        "reserved": data[1] & 3,
        "type": data[2],
        "source_length": source_length,
        "source": int.from_bytes(data[4:12], "little"),
        "sequence": int.from_bytes(data[12:14], "little"),
        "tlv": bytes(data[HEADER:source_length]),
        "tag": bytes(data[source_length:control_at]),
        "not_radio": bool(control & 0x80),
        "trailer_reserved": (control >> 6) & 1,
        "entry_count": entry_count,
        "hops_remaining": hops_remaining,
        "entries": [
            int.from_bytes(data[i : i + ENTRY], "little") for i in range(entries_at, entries_at + ENTRY * entry_count, ENTRY)
        ],
        "length": length,
        "padding": bytes(data[length:]),
    }


def relay(data, relay_identifier, limit, not_radio=False, tag_length=None):
    """The PDU that the relay sends on. limit is the PDU limit in bytes.
    not_radio is true if the relay got the PDU over a path that is not
    radio and transmits it on radio."""
    try:
        pdu = parse(data, tag_length, limit)
    except PduError as e:
        raise NotSentOn("invalid", str(e)) from None
    if pdu["hops_remaining"] < 1:
        raise NotSentOn("no hop remains", "the hops remaining are 0")
    own = identifier.hop_hash(relay_identifier)
    if own in pdu["entries"]:
        raise NotSentOn("own entry", "the hash of the relay is one of the entries")
    before = bytes(data[: pdu["source_length"] + len(pdu["tag"])])
    room = (limit - len(before) - 1 - CHECKSUM) // ENTRY
    # The newest entries that fit; the entry of the relay is the newest.
    entries = (pdu["entries"] + [own])[-room:] if room else []
    control = (data[len(before)] & 0xC0) | (0x80 if not_radio else 0) | (len(entries) << 3) | (pdu["hops_remaining"] - 1)
    out = before + bytes((control,)) + b"".join(e.to_bytes(ENTRY, "little") for e in entries)
    return out + crc32c(out).to_bytes(CHECKSUM, "little")
