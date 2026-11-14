# TLV container

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.2](../rfc/qua-network-rfc-0.md#52-tlv-container) |
| Vectors | None yet. |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies how the fields of a PDU are laid out as a sequence of
TLVs: how a tag and a length are written, and in what order TLVs appear. It
does not assign tags or define the content of any TLV.

The TLV area follows the header (RFC 5.1). Its length follows from the
header. The hop trace (RFC 5.9) is not part of it.

## 2. A TLV

**[agreed]** A TLV is a whole number of bytes: a first byte, optional
extension bytes, and a value.

**[agreed]** The upper four bits of the first byte are the delta field `D`
and the lower four bits are the length field `L`. The tag is not written;
what is written is its difference from the tag of the TLV before.

**[proposed]** The delta, from `D`:

| `D` | Extension | Delta |
|---|---|---|
| 0 to 12 | None | `D` |
| 13 | One byte `e` | `13 + e`, from 13 to 268 |
| 14 | See section 5 | |
| 15 | | Invalid |

**[agreed]** The value of a TLV is 255 bytes at most.

**[proposed]** The length of the value in bytes, from `L`:

| `L` | Extension | Length |
|---|---|---|
| 0 to 12 | None | `L` |
| 13 | One byte `e` from 0 to 242 | `13 + e`, from 13 to 255 |
| 14, 15 | | Invalid |

**[agreed]** A length extension byte with a value above 242 is invalid.

**[proposed]** The extension byte of the delta, if any, comes directly
after the first byte. The extension byte of the length, if any, comes next.
The value follows.

Every delta and every length has exactly one encoding, because the ranges
of the two rows do not overlap.

## 3. Tags and order

**[proposed]** The tag of a TLV is the tag of the TLV before it plus its
delta. For the first TLV of the area, the tag before is 0.

**[agreed]** Tags therefore never decrease through the area. This is the
canonical order of RFC 5.2; a TLV area cannot express any other.

**[agreed]** A delta of 0 repeats the tag. A tag MAY appear more than once
where the definition of that TLV allows it.

**[proposed]** The order of TLVs with the same tag is part of the content.
A relay or a gateway MUST NOT change it.

## 4. Decoding

**[proposed]** A decoder reads TLVs from the start of the area until the
area is used up. It MUST reject the PDU if:

- `D` is 15, or `L` is 14 or 15;
- the extension byte of the length is above 242;
- an extension byte or a value extends beyond the end of the area.

**[agreed]** A decoder skips a TLV whose tag it does not know, and keeps it
unchanged, in place, when it relays or logs the PDU (RFC 5.2).

## 5. Open items

- The size of the tag space, and with it the meaning of `D` = 14: invalid,
  or two extension bytes for deltas from 269. It waits for a count of the
  tags the protocol needs.
- Whether tag 0 can be used.
- Whether some bits of a tag say what a receiver does with a TLV it does not
  know (ignore it, or not act on the PDU), in the manner of CoAP option
  numbers.
- The tag table.
- Test vectors, including areas a decoder must reject.
