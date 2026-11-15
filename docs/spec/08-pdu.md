# PDU and header

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.1](../rfc/qua-network-rfc-0.md#51-header) |
| Vectors | [`vectors/pdu.json`](../../vectors/pdu.json), [`vectors/crc32c.json`](../../vectors/crc32c.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the parts of a PDU, the header, the length of a PDU,
padding and the checksum.

It does not specify these:

- The version numbers and the bits of the version byte
  ([07-versions](07-versions.md)).
- The station identifier ([01-station-identifier](01-station-identifier.md)).
- The TLV area ([03-tlv](03-tlv.md)).
- The types of a PDU (RFC 5.11).
- The content of the trailer, and what a relay does
  ([09-hop-trace](09-hop-trace.md)).
- The authentication tag (RFC section 10).
- Deduplication (RFC 6.2).

## 2. Terms

**[agreed]** The parts of a PDU have these names:

| Term | Meaning |
|---|---|
| PDU | The whole unit: the source part, the authentication tag if there is one, the trailer and the checksum. The PDU limit of RFC section 6 applies to it. |
| Source part | The header and the TLV area. |
| Source length | The length of the source part in bytes. It is a field of the header. |
| Trailer | The hop trace of [09-hop-trace](09-hop-trace.md): the control byte and the entries. |
| Padding | Bytes that a link gives after a PDU. Padding is not part of the PDU. |

## 3. Parts of a PDU

**[agreed]** A PDU has these parts, in this order:

| Part | Bytes | Present |
|---|---|---|
| Header | 14 | Always |
| TLV area | Source length minus 14 | Always. It can be empty. |
| Authentication tag | Fixed. **[open]** | If the flag Authenticated is set |
| Trailer | 1, and 3 for each entry | Always |
| Checksum | 4 | Always |

```
| header | TLVs | auth tag | control | entry, entry, ... | CRC-32C |
|< source part >|          |<------ trailer ------>|
```

**[agreed]** No application data is placed in the address fields of a
link layer.

## 4. Header

**[agreed]** The header is 14 bytes, in this layout:

| Offset | Bytes | Field |
|---|---|---|
| 0 | 1 | Version byte |
| 1 | 1 | Hop limit, 3 bits. Flags, 5 bits. |
| 2 | 1 | Type |
| 3 | 1 | Source length |
| 4 | 8 | Source identifier |
| 12 | 2 | Sequence number |

**[agreed]** The header has no other field. Every other field of a PDU
is a TLV.

### 4.1 Version byte

**[agreed]** The version byte is the first byte of the PDU. A receiver
reads it before every other field. [07-versions](07-versions.md) section
3 gives its bits.

**[agreed]** The least significant bit of the first byte of a PDU is 1.
The version byte gives this bit.

**[agreed]** If this bit is 0, the bytes are not a PDU. A receiver does
not read them as a PDU.

### 4.2 Hop limit and flags

**[agreed]** The bits of the second byte, from the most significant bit:

| Bits | Content |
|---|---|
| 3 | Hop limit, 0 to 7 |
| 1 | Flag No Internet |
| 1 | Flag Translated |
| 1 | Flag Authenticated |
| 2 | Reserved |

**[agreed]** The hop limit is the limit that the source chose. A relay
does not change it. The trailer gives the number of hops that remain
([09-hop-trace](09-hop-trace.md) section 4).

**[agreed]** The flags have these meanings:

| Flag | Meaning if the bit is 1 |
|---|---|
| No Internet | A gateway does not carry the PDU from radio to the Internet. |
| Translated | A gateway made the PDU from a legacy packet. |
| Authenticated | The PDU has an authentication tag (section 5). |

**[agreed]** A source writes 0 in a reserved bit. A receiver ignores a
reserved bit.

### 4.3 Type

**[agreed]** One PDU has one type. The type byte gives it (RFC 5.11).

### 4.4 Source length

**[agreed]** The source length counts the header and the TLV area. It
does not count the authentication tag, the trailer or the checksum.

**[agreed]** The TLV area ends where the source length ends.

**[agreed]** If the source length is less than 14, the PDU is invalid.

### 4.5 Source identifier

**[agreed]** The source identifier is the station identifier of the
source ([01-station-identifier](01-station-identifier.md)). It is 8 bytes
in little-endian order.

### 4.6 Sequence number

**[agreed]** The sequence number has 16 bits, in little-endian order.

**[agreed]** A station follows these rules:

1. Each time that the station starts, it starts at a random value.
2. It adds 1 for each PDU that it sends.
3. After 65535, the next number is 0.

**[agreed]** A sequence number can therefore occur again. A relay or a
receiver keeps a deduplication entry for a limited time only (RFC 6.2).

## 5. Authentication tag

**[agreed]** If the flag Authenticated is set, an authentication tag
follows the TLV area. If the flag is not set, the PDU has no tag.

**[agreed]** The algorithm of the tag is fixed, so the length of the tag
is fixed. **[open]** The algorithm and the length (RFC section 10).

**[agreed]** No field holds an algorithm identifier. A change of an
algorithm needs a new major version ([07-versions](07-versions.md)
section 5).

## 6. Changes in transit

**[agreed]** In transit, only the trailer changes, and the checksum with
it. A relay does not change the source part or the authentication tag.

## 7. Length of a PDU and padding

**[agreed]** The length of a PDU follows from its content. It is the sum
of these numbers:

- the source length;
- the length of the authentication tag, if the flag Authenticated is set;
- 1 for the control byte of the trailer;
- 3 for each entry of the trailer; the control byte gives the entry count
  ([09-hop-trace](09-hop-trace.md) section 4);
- 4 for the checksum.

**[agreed]** A receiver reads and checks only these bytes.

**[agreed]** A PDU that is larger than the PDU limit of RFC 6.1 is
invalid. A receiver or a relay drops it. Padding does not count for the
limit.

**[agreed]** A receiver ignores the bytes that a link gives after the
PDU. A link can therefore add padding after a PDU.

**[agreed]** If a link gives fewer bytes than the length of the PDU, the
PDU is invalid.

**[agreed]** The checksum does not cover padding. A relay does not send
the padding that it received.

## 8. Checksum

**[agreed]** Every PDU has one checksum. It is the last 4 bytes of the
PDU. An authenticated PDU has it too.

**[agreed]** The checksum is CRC-32C (Castagnoli), with these parameters:

| Parameter | Value |
|---|---|
| Polynomial | `0x1EDC6F41` (reflected: `0x82F63B78`) |
| Initial value | `0xFFFFFFFF` |
| Input and output | Reflected |
| Final XOR | `0xFFFFFFFF` |
| Check value for the ASCII string `123456789` | `0xE3069283` |

**[agreed]** The checksum covers every byte of the PDU before it: the
source part, the authentication tag if there is one, and the trailer.

**[agreed]** The checksum is in little-endian order.

**[agreed]** A relay changes the trailer, so it computes the checksum
again.

**[agreed]** A receiver computes the CRC-32C of the bytes before the
checksum. If the result is not the checksum, the PDU is invalid.

The CRC-32C of a whole PDU, with its checksum, is `0x48674BC7`. This
follows from the parameters and the byte order.

`vectors/crc32c.json` has the check value, and `qua-check-vectors`
computes it again.

## 9. Byte order

**[agreed]** Every integer of more than one byte in a PDU is in
little-endian order ([06-numbers-units-text](06-numbers-units-text.md)
section 2).

## 10. Test vectors

`vectors/pdu.json` has the test vectors. Each vector is one of two kinds:

| Kind | Keys | A conformant implementation |
|---|---|---|
| A valid PDU | `bytes`, and one key for each field | Reads each field from `bytes` with the value of its key. |
| Invalid bytes | `bytes`, `invalid` | Rejects `bytes`. `invalid` is the cause. |

The keys of a valid PDU:

| Key | Value |
|---|---|
| `version` | The major version and the minor version |
| `hop_limit`, `type`, `source_length`, `sequence` | The field, as a number |
| `no_internet`, `translated`, `authenticated` | The flag |
| `reserved` | The two reserved bits of the second byte, as a number |
| `source` | The text form of the source identifier |
| `tlv` | The bytes of the TLV area |
| `not_radio`, `trailer_reserved`, `entry_count`, `hops_remaining` | The fields of the control byte ([09-hop-trace](09-hop-trace.md) section 4) |
| `entries` | The entries, each as a number in 6 hexadecimal digits |
| `length` | The length of the PDU in bytes |
| `padding` | The bytes after the PDU |
| `limit` | In some vectors: the PDU limit in bytes. The value of the limit is open (RFC 6.1), so a vector that needs one states it. |

The values of `invalid`:

| `invalid` | Cause |
|---|---|
| `not a PDU` | The least significant bit of the first byte is 0, or there are no bytes (section 4.1). |
| `source length` | The source length is less than 14 (section 4.4). |
| `short` | The link gives fewer bytes than the length of the PDU (section 7). |
| `size` | The PDU is larger than `limit` (section 7). |
| `checksum` | The checksum is wrong (section 8). |
| `trailer` | The trailer is not valid ([09-hop-trace](09-hop-trace.md) section 4). |

Each set of invalid bytes has one cause only.

The vectors have these limits:

- No vector has the flag Authenticated, because the length of the tag is
  open.
- The type byte has no assigned values yet. The values in the vectors
  have no meaning.
- The TLV area follows the syntax of [03-tlv](03-tlv.md). Its tags have
  no meaning.
- Some vectors follow **[proposed]** rules. They change if the rule
  changes.

`qua-make-vectors` computes the vectors with `vectors_pdu.py`. This
module imports no other module of the package. It
packs the bytes with the `struct` module of Python and has its own
table-driven CRC-32C. It takes the identifiers from
`vectors/identifier.json` and the entries from `vectors/hop-hash.json`.
`qua-check-vectors` checks the vectors against `pdu.py`.

## 11. Open items

These are also in the RFC (section 14, question 25).

- **[open]** The use of the two reserved bits of the second byte.
- **[open]** The algorithm and the length of the authentication tag (RFC
  section 10).
- **[open]** The exact rule for the flag No Internet: which stations obey
  it, and whether it also applies to a trunk (RFC 8.2).
- **[open]** How long a relay or a receiver keeps a deduplication entry
  (RFC 6.2).
- **[open]** Test vectors for a PDU with an authentication tag.
- **[open]** What a receiver does with a version that it does not know
  ([07-versions](07-versions.md) section 6).
