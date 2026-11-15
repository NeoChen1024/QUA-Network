# Numbers, units and text

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.3](../rfc/qua-network-rfc-0.md#53-numeric-and-text-rules) |
| Vectors | None. |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the form of a number, the unit of each quantity, the
form of a time and the content of a string.

It does not specify these:

- The formats of the decimal number
  ([05-decimal-number](05-decimal-number.md)).
- The compressed form of a string
  ([04-text-compression](04-text-compression.md)).
- The tag and the definition of each field (RFC 5.11).
- How the specification chooses a unit (RFC 5.3).

## 2. Numbers

**[agreed]** No field holds a binary floating-point number.

**[agreed]** A quantity is an integer with a fixed scale, or it is a
decimal number. The definition of a field states which of the two.

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

Wind speed is a speed. It has the unit and the form of speed.

## 4. Time

**[agreed]** A time is an integer count from a fixed epoch in UTC.

## 5. Precision

**[proposed]** Precision or uncertainty is an explicit field. A value
does not show it with blanked digits.

## 6. Text

**[agreed]** A string is UTF-8.

**[agreed]** The format does not forbid a character in a free-text
field. A text can hold control characters and other special characters.
An implementation MUST be prepared for every character in such a field.

**[proposed]** This rule applies when the implementation shows the text,
writes it to a log or gives it to a different program.

## 7. Telemetry

**[agreed]** A telemetry value describes itself, or it refers to a
registered schema. A value MUST NOT depend on a separate definition
packet that the receiver has heard.

## 8. Open items

- **[open]** The scale and the size of latitude and longitude. RFC 5.3
  gives int32 in units of 1e-7 degree as an example.
- **[open]** The form of temperature and of pressure.
- **[open]** The epoch, the unit and the size of a time.
- **[open]** The other quantities and their units (RFC section 15,
  step 16). The list of section 3 grows with the tag tables.
- **[open]** What a receiver does with a string that is not valid UTF-8.
- **[open]** The questions on telemetry values and on units are in the
  RFC (section 14, question 24).
