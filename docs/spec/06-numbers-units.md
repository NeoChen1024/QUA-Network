# Numbers and units

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.3](../rfc/qua-network-rfc-0.md#53-numeric-and-text-rules) |
| Vectors | None. |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the form of a number, the unit of each quantity and
the form of a time.

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

## 3. Units

**[agreed]** One quantity has one unit. This file fixes the unit. A
sender cannot choose a different unit. No field holds a prefix.

**[agreed]** A quantity in this rule is one kind of use. It is not one
physical dimension. Altitude, range and rain depth are lengths, and they
are three quantities.

**[agreed]** The quantities that have a unit so far:

| Quantity | Unit | Form |
|---|---|---|
| Latitude, longitude | Degree | An integer with a fixed scale |
| Altitude | Metre | Decimal number |
| Speed | Kilometre per hour | Decimal number |
| Wind speed | Kilometre per hour | Decimal number |
| Temperature | Degree Celsius | Not decided |
| Pressure | Hectopascal | Not decided |
| Horizontal uncertainty | Metre | Decimal number |
| Course | Degree | An integer with a fixed scale |

Wind speed is a speed. It has the unit and the form of speed.

The definition of a field gives the scale and the size of an integer.
[10-position](10-position.md) has the fields of a position.

## 4. Time

**[agreed]** A time is an integer count from a fixed epoch in UTC.

**[agreed]** The epoch is 1970-01-01, 00:00:00 UTC. The count is in
seconds, as the time of a Unix system is.

**[agreed]** The specification has no rule for a leap second. A source
writes the count that its time source gives.

**[agreed]** A time has no part of a second.

**[agreed]** A time has 8 bytes: a signed integer of 64 bits in two's
complement, in little-endian order.

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
