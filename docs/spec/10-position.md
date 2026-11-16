# Position

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.11](../rfc/qua-network-rfc-0.md#position-type) |
| Vectors | None yet. |

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
- The object name (RFC 5.11).
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

**[agreed]** A Position PDU also includes the object name (RFC 5.11).
Its tag and its form are open.

**[agreed]** A Position PDU can have no coordinates. With such a PDU, a
source states that its coordinates are not available.

**[agreed]** A receiver that gets such a PDU has no coordinates for
the source from then on. It does not keep the coordinates of an earlier
PDU (RFC 5.11).

**[agreed]** A PDU without coordinates MUST NOT have a horizontal
uncertainty. It can have each of the other TLVs.

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

The integers of this example were packed with the `struct` module of
Python. The first byte of each TLV was computed by hand from
[03-tlv](03-tlv.md) section 2.

## 7. Open items

- **[open]** What a receiver does with a Position PDU that has a field
  with an invalid length or value. The question applies to every type
  (RFC section 14, question 27).
- **[open]** The tag and the form of the object name.
- **[open]** Whether tag 0 can be used ([03-tlv](03-tlv.md) section 5).
  The tags of this file start at 1.
- **[open]** Test vectors.
