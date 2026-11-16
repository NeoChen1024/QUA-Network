# Position

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.11](../rfc/qua-network-rfc-0.md#position-type) |
| Vectors | [`vectors/position.json`](../../vectors/position.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the fields that state where a station is and how it
moves, the two subgroups of these fields, and the schema of the Position
type.

It does not specify these:

- The TLV container ([03-tlv](03-tlv.md)).
- The decimal number ([05-decimal-number](05-decimal-number.md)).
- The unit of each quantity and the form of a time
  ([06-numbers-units-text](06-numbers-units-text.md)).
- The Object type and the rules for an object (RFC 5.11).
- The schema of every other type. A different type states its own tags
  for the fields of this file (RFC 5.11).

## 2. Terms

| Term | Meaning |
|---|---|
| Coordinates | The latitude and the longitude of one place. |
| Position subgroup | The fields of section 4.1. |
| Motion subgroup | The fields of section 4.2. |
| Position PDU | A PDU of the Position type. |

## 3. Fields

Each field is the value of one TLV. [06-numbers-units-text](06-numbers-units-text.md)
section 3 gives the unit of each quantity.

### 3.1 Coordinates

**[agreed]** The field has 8 bytes: the latitude, then the longitude.
Each is a signed integer of 32 bits in two's complement, in little-endian
order. The unit of each is 10^−7 degree.

**[agreed]** A latitude north of the equator is positive. A longitude
east of the prime meridian is positive.

**[agreed]** The latitude is from −900000000 to 900000000. The longitude
is from −1800000000 to 1799999999. A value outside these ranges is
invalid.

**[agreed]** The meridian of 180 degrees is written as −180 degrees. One
place then has one longitude.

### 3.2 Altitude

**[agreed]** The field is a decimal number. It is the height above the
mean sea level. A height below the mean sea level is negative.

**[agreed]** An infinity is invalid in this field.

### 3.3 Horizontal uncertainty

**[agreed]** The field is a decimal number. It states how far the
station can be from the coordinates. A source that does not send its
exact place rounds the coordinates and sends this field.

**[agreed]** The value is the radius of a circle around the
coordinates. The station is in that circle. The value is not negative,
and an infinity is invalid.

**[agreed]** The coordinates have no code for a missing digit. Only this
field states an uncertainty.

### 3.4 Course

**[agreed]** The field has 2 bytes: an unsigned integer of 16 bits in
little-endian order. The unit is 1 degree. The value is from 0 to 359. A
larger value is invalid.

**[agreed]** The course is the direction in which the station moves
over the ground. It is counted clockwise from true north. North is 0.

**[agreed]** The field has no code for a course that is not known. A
source that does not know its course omits the TLV.

### 3.5 Speed

**[agreed]** The field is a decimal number.

**[agreed]** The speed is the speed over the ground. The value is not
negative, and an infinity is invalid.

### 3.6 Time

**[agreed]** The field is a time
([06-numbers-units-text](06-numbers-units-text.md) section 4). It is the
time at which the content of the PDU was true. If the PDU has
coordinates, the station was at the coordinates at that time.

**[agreed]** The field has no code for a time that is not known. A
source that does not have a valid UTC time omits the TLV. A receiver
then takes the time at which it received the PDU.

### 3.7 Object identifier

**[agreed]** The field has 8 bytes: an identifier in the format of
[01-station-identifier](01-station-identifier.md), in the byte order of
its section 7. A value that its section 5 rejects is invalid.

**[agreed]** The field names an object that the source declared (RFC
5.11). If a PDU has this field, the content of the PDU describes that
object and not the source. Each rule of section 5 for the source then
applies to the object.

## 4. Subgroups

### 4.1 Position subgroup

**[agreed]** The position subgroup has these fields: the coordinates,
the altitude and the horizontal uncertainty.

### 4.2 Motion subgroup

**[agreed]** The motion subgroup has these fields: the course and the
speed. The two TLVs are independent: a PDU can have one and not the
other.

## 5. Position type

**[agreed]** The type byte of a Position PDU is 1
([08-pdu](08-pdu.md) section 4.3).

**[agreed]** A Position PDU can hold these TLVs:

| Tag | Field | Section | Bytes | In one PDU |
|---|---|---|---|---|
| 1 | Coordinates | 3.1 | 8 | 0 or 1 |
| 2 | Altitude | 3.2 | 2, 3 or 4 | 0 or 1 |
| 3 | Horizontal uncertainty | 3.3 | 2, 3 or 4 | 0 or 1 |
| 4 | Course | 3.4 | 2 | 0 or 1 |
| 5 | Speed | 3.5 | 2, 3 or 4 | 0 or 1 |
| 6 | Time | 3.6 | 8 | 0 or 1 |

**[agreed]** A Position PDU can also hold the object identifier. Its tag
is 0, so it is the first TLV of the area:

| Tag | Field | Section | Bytes | In one PDU |
|---|---|---|---|---|
| 0 | Object identifier | 3.7 | 8 | 0 or 1 |

**[agreed]** A Position PDU can have no coordinates. With such a PDU, a
source states that its coordinates are not available.

**[agreed]** A receiver that gets such a PDU has no coordinates for
the source from then on. It does not keep the coordinates of an earlier
PDU (RFC 5.11).

**[agreed]** A PDU without coordinates MUST NOT have a horizontal
uncertainty. It can have each of the other TLVs.

**[agreed]** A TLV of these tables is invalid in each of these cases:

- Its length is not a length that its table gives.
- Its value is invalid by the section of its field. For a decimal
  number, [05-decimal-number](05-decimal-number.md) section 6 also
  applies.
- Its tag occurs a second time in the PDU.

A TLV with a tag that the tables do not give is not invalid. A decoder
skips it ([03-tlv](03-tlv.md) section 4).

A Position PDU with coordinates has 28 bytes at least: 14 for the
header, 9 for the TLV of the coordinates, 1 for the control byte and 4
for the checksum. A Position PDU with no TLV has 19 bytes.

## 6. Example

A station is at 24.25 degrees north and 120.67 degrees east, at an
altitude of 152 m. It moves to the east at 62 km/h. The TLV area of its
Position PDU has 18 bytes:

| Bytes | TLV |
|---|---|
| `18` `A0 41 74 0E` `E0 C7 EC 47` | Tag 1, 8 bytes. Latitude 242500000, longitude 1206700000. |
| `12` `98 00` | Tag 2, 2 bytes. Altitude 152. |
| `22` `5A 00` | Tag 4, 2 bytes. Course 90. |
| `12` `3E 00` | Tag 5, 2 bytes. Speed 62. |

This example is a copy of a vector of section 7. The file is
authoritative.

## 7. Test vectors

`vectors/position.json` has the test vectors. Each vector is the TLV
area of a Position PDU. It is one of two kinds:

| Kind | Keys | A conformant implementation |
|---|---|---|
| A valid area | `tlv` and the keys of the fields | Decodes `tlv` to the fields. It encodes the fields to `tlv`. |
| An invalid area | `tlv`, `invalid` | Finds that the area or the field of `invalid` is invalid. |

A valid area has a key only for a field that it has:

| Key | Content |
|---|---|
| `tlv` | The bytes of the TLV area |
| `latitude`, `longitude` | The integers of the coordinates (section 3.1) |
| `altitude`, `uncertainty`, `speed` | The text form of the decimal number ([05-decimal-number](05-decimal-number.md) section 7) |
| `course` | The integer of the course |
| `time` | The count of the time, as a string of decimal digits |
| `object` | The text form of the object identifier ([01-station-identifier](01-station-identifier.md) section 6) |
| `other` | Each TLV with a tag that section 5 does not give, in the order of the area: the tag, and the bytes of the value |

The time is a string, because some JSON readers do not keep each digit
of an integer of 64 bits.

The values of `invalid`:

| `invalid` | Cause |
|---|---|
| `coordinates`, `altitude`, `uncertainty`, `course`, `speed`, `time`, `object` | The TLV of this field is invalid (section 5). |
| `tlv area` | The area breaks [03-tlv](03-tlv.md) section 4. |

Each invalid area has one cause only.

The vectors have these limits:

- A vector does not state what a receiver does with an invalid field.
  That is open (section 8).
- No vector has a TLV with an extension byte.
- Some vectors follow **[proposed]** rules of this file and of
  [03-tlv](03-tlv.md). They change if the rule changes.

`qua-make-vectors` computes the vectors with `vectors_position.py`. This
module packs the integers with the `struct` module of Python. It takes
the decimal numbers from `vectors_decimal.py`. It writes the first byte
of each TLV itself, and it has its own computation of an object
identifier. `qua-check-vectors` checks the vectors against
`position.py`. That module reads the area with `tlv.py`, the decimal
numbers with `decimal_number.py` and the object identifier with
`identifier.py`. The two paths do not import each other.

## 8. Open items

- **[open]** What a receiver does with a Position PDU that has a field
  with an invalid length or value. The question applies to every type
  (RFC section 14, question 27).
