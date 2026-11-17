# Numbers and units

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.3](../rfc/qua-network-rfc-0.md#53-numeric-and-text-rules) |
| Vectors | None. |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the form of a number, the types of a number, the
unit of each quantity and the form of a time.

It does not specify these:

- The formats of the decimal number
  ([05-decimal-number](05-decimal-number.md)).
- The string formats and the free text ([13-strings](13-strings.md)).
- The tag and the definition of each field (RFC 5.11).
- How the specification chooses a unit (RFC 5.3).

## 2. Numbers

**[agreed]** No field holds a binary floating-point number.

**[agreed]** A quantity is an integer with a fixed scale, or it is a
decimal number. The definition of a field states which of the two.

**[agreed]** An integer of more than one byte is in little-endian order:
its least significant byte comes first. This applies to every such
integer of a PDU.

**[agreed]** The rule is for the bytes of a PDU only. A text, a screen
and this specification show a number in the usual way, with its most
significant digit first. The number `0x1234` is the bytes `34 12`.

This rule is about the order of bytes. A bit string is a different
thing: the compressed forms of the icon and of a text fill each byte from
its most significant bit ([02-icon](02-icon.md),
[04-text-compression](04-text-compression.md)).

**[agreed]** A position is in WGS84. No other datum is used.

### 2.1 Integer types

**[agreed]** The specification has these integer types. The definition
of a field names the type of each integer.

| Type | Bytes | Sign | Smallest value | Largest value |
|---|---|---|---|---|
| `uint8` | 1 | Unsigned | 0 | 255 |
| `uint16` | 2 | Unsigned | 0 | 65535 |
| `uint32` | 4 | Unsigned | 0 | 2^32 − 1 |
| `uint64` | 8 | Unsigned | 0 | 2^64 − 1 |
| `int32` | 4 | Signed | −2^31 | 2^31 − 1 |
| `int64` | 8 | Signed | −2^63 | 2^63 − 1 |

**[agreed]** These rules apply to each type:

1. A signed type is in two's complement.
2. A type of more than one byte is in little-endian order (section 2).
3. Each value of the type is valid, unless the definition of the field
   gives a range.
4. An integer has no code for an absent value. A source that has no
   value omits the TLV.

The name of a type is the name of the C language with no `_t`.

### 2.2 Angle

**[agreed]** An angle is a `uint16`. The unit is 1 degree. The value is
from 0 to 359. A larger value is invalid.

**[agreed]** An angle is a direction in the horizontal plane. It is
counted clockwise from true north. North is 0, and east is 90.

### 2.3 All number types

Each number of a TLV has one of these types:

| Type | Bytes | Specified in |
|---|---|---|
| An integer type | 1, 2, 4 or 8 | Section 2.1 |
| Angle | 2 | Section 2.2 |
| Time | 8 | Section 4 |
| Decimal number | 2, 3 or 4 | [05-decimal-number](05-decimal-number.md) |

Some fields give an integer type a scale, a range or a list of codes.
The definition of the field states it. These are the fields so far:

| Field | Type | Specified in |
|---|---|---|
| Latitude, longitude | `int32`, in units of 10^−7 degree | [10-position](10-position.md) section 3.1 |
| Kind of a station | `uint8`, a code | [12-station-information](12-station-information.md) section 3.1 |
| Classic form of a symbol | `uint16`, from 0 to 3571 | [14-symbol](14-symbol.md) section 4 |
| Code point of a symbol | `uint32`, a Unicode code point | [14-symbol](14-symbol.md) section 5 |
| Station identifier, object identifier | `uint64`, with the layout of that file | [01-station-identifier](01-station-identifier.md) section 2 |
| Name | `uint64`, 12 digits in base 37 | [13-strings](13-strings.md) section 4 |

The integers of the header and of the trailer of a PDU are not fields of
a TLV. [08-pdu](08-pdu.md) and [09-hop-trace](09-hop-trace.md) specify
them.

## 3. Units

**[agreed]** One quantity has one unit. This file fixes the unit. A
sender cannot choose a different unit. No field holds a prefix.

**[agreed]** A quantity in this rule is one kind of use. It is not one
physical dimension. Altitude, range and rain depth are lengths, and they
are three quantities.

**[agreed]** The quantities that have a unit so far:

| Quantity | Unit | Type |
|---|---|---|
| Latitude, longitude | Degree | `int32`, in units of 10^−7 degree |
| Altitude | Metre | Decimal number |
| Speed | Kilometre per hour | Decimal number |
| Wind speed | Kilometre per hour | Decimal number |
| Temperature | Degree Celsius | Not decided |
| Pressure | Hectopascal | Not decided |
| Horizontal uncertainty | Metre | Decimal number |
| Course | Degree | Angle |
| Transmitter power | Watt | Decimal number |
| Antenna height | Metre | Decimal number |
| Antenna gain | Decibel relative to an isotropic antenna (dBi) | Decimal number |
| Antenna direction | Degree | Angle |
| Range | Kilometre | Decimal number |

Wind speed is a speed. It has the unit and the type of speed.

The definition of a field gives the type and the scale of an integer.
[10-position](10-position.md) has the fields of a position.
[12-station-information](12-station-information.md) has the fields of a
station and its antenna.

## 4. Time

**[agreed]** A time is an integer count from a fixed epoch in UTC.

**[agreed]** The epoch is 1970-01-01, 00:00:00 UTC. The count is in
seconds, as the time of a Unix system is.

**[agreed]** The specification has no rule for a leap second. A source
writes the count that its time source gives.

**[agreed]** A time has no part of a second.

**[agreed]** A time is an `int64` (section 2.1). It has 8 bytes.

**[agreed]** A count below 0 is a time before the epoch. Each value of
the integer is a valid time.

## 5. Precision

**[proposed]** Precision or uncertainty is an explicit field. A value
does not show it with blanked digits.

## 6. Text

The rules of this section moved to [13-strings](13-strings.md) section
5.1. The section keeps its number.

## 7. Telemetry

**[agreed]** A telemetry value describes itself, or it refers to a
registered schema. A value MUST NOT depend on a separate definition
packet that the receiver has heard.

## 8. Open items

- **[open]** The form of temperature and of pressure.
- **[open]** The other quantities and their units (RFC section 15,
  step 16). The list of section 3 grows with the tag tables.
- **[open]** The questions on telemetry values and on units are in the
  RFC (section 14, question 24).
