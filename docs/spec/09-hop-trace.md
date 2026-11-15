# Hop trace

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.9](../rfc/qua-network-rfc-0.md#59-hop-trace) |
| Vectors | [`vectors/hop-hash.json`](../../vectors/hop-hash.json), [`vectors/pdu-relay.json`](../../vectors/pdu-relay.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the trailer of a PDU: the control byte, the entries,
what a source writes and what a relay does.

It does not specify these:

- The place of the trailer in a PDU, the header and the checksum
  ([08-pdu](08-pdu.md)).
- The station identifier ([01-station-identifier](01-station-identifier.md)).
- The MTU (RFC 6.1) and deduplication (RFC 6.2).
- Gateway provenance (RFC 8.3).
- The text form of the trace (RFC 5.4).

## 2. Terms

| Term | Meaning |
|---|---|
| Relay | A station that sends on a PDU that it received and that it is not the source of. |
| Entry | The 3 bytes that one relay adds to the trailer. |
| Hop limit | The field of the header ([08-pdu](08-pdu.md) section 4.2). |
| Hops remaining | The field of the control byte. |
| Hops taken | The hop limit minus the hops remaining. |
| Entry count | The field of the control byte: the number of entries in the trailer. |
| Truncated trace | A trailer with fewer entries than the hops taken. |

## 3. Layout

**[agreed]** Every PDU has a trailer. The trailer has a fixed layout and
is not a TLV:

| Part | Bytes |
|---|---|
| Control byte | 1 |
| Entries, in the order of the hops | 3 for each entry |

**[agreed]** The oldest entry is first. A relay adds its entry after the
last one.

**[agreed]** The checksum covers the trailer ([08-pdu](08-pdu.md)
section 8).

**[agreed]** No entry is reserved in advance. A PDU that no relay has
sent on has a trailer of 1 byte.

## 4. Control byte

**[agreed]** The bits of the control byte, from the most significant
bit:

| Bits | Content |
|---|---|
| 1 | Not Radio: set if the PDU has crossed a path that is not radio |
| 1 | Reserved |
| 3 | Entry count |
| 3 | Hops remaining |

**[agreed]** The entry count is always the number of entries in the
trailer. This is also true for a truncated trace.

**[proposed]** A relay copies the reserved bit. A receiver ignores it.

**[proposed]** A PDU is invalid if one of these is true:

- The hops remaining are more than the hop limit.
- The entry count is more than the hops taken.

## 5. Entry

**[agreed]** An entry is a hash of 24 bits of the identifier of the
relay. A station computes it as follows:

1. Take the 8 bytes of the identifier, as they are in a PDU
   ([01-station-identifier](01-station-identifier.md) section 7).
2. Compute the CRC-32C of these bytes, with the parameters of
   [08-pdu](08-pdu.md) section 8.
3. Take the 24 least significant bits of the result.

**[agreed]** In the trailer, the entry is 3 bytes in little-endian order.

**[agreed]** A relay also sends its full identifier periodically, in its
own beacons. The specification does not fix the interval. The operator
of the relay chooses it.

**[agreed]** A receiver resolves an entry against the stations that it
has heard. It shows an entry that it cannot resolve as the hash.

## 6. Source

**[agreed]** The source writes the control byte.

**[proposed]** The source writes the hops remaining equal to its hop
limit. It writes 0 in every other bit of the control byte.

**[agreed]** The specification does not make a source leave room for
entries. The PDU as sent, with its trailer of 1 byte, fits the PDU limit
of RFC 6.1.

## 7. Relay

**[proposed]** A relay sends a PDU on only if all of these are true:

- The checksum is good.
- The trailer is valid (section 4).
- The hops remaining are 1 or more.
- The hash of the relay is not one of the entries.

**[proposed]** To send a PDU on, a relay does these steps:

1. It subtracts 1 from the hops remaining.
2. It adds its entry after the last entry, if section 7.1 permits it.
3. It writes the number of entries in the entry count.
4. It computes the checksum again.

**[agreed]** A relay adds one entry. Section 7.1 gives the one
exception. **[proposed]** A relay changes nothing before the trailer.

### 7.1 A trailer that does not fit

**[agreed]** A trailer can have fewer entries than the hops taken. If a
trailer does not fit, the oldest entries are dropped. The trailer keeps
the most recent hops.

**[agreed]** If the PDU with the new entry is larger than the PDU limit
of RFC 6.1, the relay keeps only the newest entries that fit. The entry
of the relay is the newest. The relay drops the other entries, the oldest
first.

**[agreed]** If no entry fits, the trailer has only the control byte.
The relay does not add its entry. It still sends the PDU on, and it still
subtracts 1 from the hops remaining.

**[proposed]** A relay drops only as many entries as are necessary. A
relay MUST NOT drop an entry for a different reason.

### 7.2 A path that is not radio

**[agreed]** A station sets the bit Not Radio when it transmits on radio
a PDU that it received over a path that is not radio.

**[proposed]** This station is then a relay, and it adds its entry. No
station clears the bit.

**[agreed]** A gateway that carries a PDU from radio to the Internet
does not change the PDU. What the gateway knows about the reception
belongs to gateway provenance (RFC 8.3).

## 8. Test vectors

| Identifier | Bytes in a PDU | Entry | Bytes in the trailer |
|---|---|---|---|
| `N0CALL` | `3D EB EB 5B 0E 00 00 00` | `0x8ACFF6` | `F6 CF 8A` |
| `N0CALL-7` | `45 EB EB 5B 0E 00 00 00` | `0xC76C33` | `33 6C C7` |
| `N0CALL-15` | `21 00 19 49 13 02 00 80` | `0xD6B6EE` | `EE B6 D6` |
| `BV5AB-33` | `F5 3A 1E B0 07 00 00 80` | `0xF89C9C` | `9C 9C F8` |
| `PJ4/KA1ABC` | `A5 64 89 F4 F1 77 C5 01` | `0xE05390` | `90 53 E0` |
| `YW18FIFA/MM-A` | `66 74 1F D1 E2 F5 9F 58` | `0x65DF98` | `98 DF 65` |

This table is a copy of `vectors/hop-hash.json`, which is authoritative.
`qua-make-vectors` computes the values with `vectors_pdu.py`, which
imports no other module of the package. Its
CRC-32C uses a table and gives the check value of [08-pdu](08-pdu.md)
section 8. `qua-check-vectors` computes the values again with the
bit-by-bit CRC-32C of the package.

`vectors/pdu-relay.json` has the vectors for a relay. Each vector has
these keys:

| Key | Value |
|---|---|
| `received` | The bytes that the relay received |
| `relay` | The text form of the identifier of the relay |
| `limit` | The PDU limit in bytes. Its value is open (RFC 6.1), so each vector states one. |
| `not_radio` | If true, the relay got the PDU over a path that is not radio, and it transmits on radio (section 7.2) |
| `sent` | The bytes that the relay sends, or `null` if it does not send the PDU on |
| `reason` | Why the relay does not send the PDU on: `invalid`, `no hop remains` or `own entry` (section 7) |

The rules of section 7 are **[proposed]** in part. A vector changes if
its rule changes. `vectors_pdu.py` computes these vectors too
([08-pdu](08-pdu.md) section 10). `qua-check-vectors`
checks them against `pdu.py`. `vectors/pdu.json` has PDUs with a trailer,
and PDUs whose trailer is not valid.

## 9. Open items

- **[open]** The use of the reserved bit of the control byte.
- **[open]** What a relay does with a PDU that is larger than the PDU
  limit with no entry.
