# Station information

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.11](../rfc/qua-network-rfc-0.md#station-information-type) |
| Vectors | [`vectors/station-information.json`](../../vectors/station-information.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the fields that describe a station and its radio
equipment, and the schema of the Station information type.

It does not specify these:

- The format of a name ([13-strings](13-strings.md) section 4).
- The TLV container ([03-tlv](03-tlv.md)).
- The decimal number ([05-decimal-number](05-decimal-number.md)).
- The unit of each quantity
  ([06-numbers-units](06-numbers-units.md)).
- The rules for an object ([11-object](11-object.md)).
- The status text and the frequency of a station. They belong to a
  different type, which has no schema so far (RFC 5.11).

## 2. Terms

| Term | Meaning |
|---|---|
| Kind | How a station moves, or what carries it. |
| Name | A string of 12 characters at most, in 8 bytes ([13-strings](13-strings.md) section 4). |
| Station information PDU | A PDU of the Station information type. |

## 3. Fields

Each field is the value of one TLV. [06-numbers-units](06-numbers-units.md)
section 3 gives the unit of each quantity.

### 3.1 Kind

**[agreed]** The field has 1 byte: an unsigned integer. It is a code for
the kind of the station.

**[agreed]** The kinds and their codes:

| Code | Kind | Meaning |
|---|---|---|
| 0 | Other | The table has no kind for the station. |
| 1 | Fixed | The station stays at one place. |
| 2 | Portable | The station is at a place for a limited time. It does not operate while it moves. |
| 3 | Pedestrian | A person on foot carries the station. |
| 4 | Land vehicle | The station is in or on a vehicle on land. |
| 5 | Watercraft | The station is on a ship or a boat. |
| 6 | Aircraft | The station is on an aircraft, with or without a crew. |
| 7 | Balloon | The station is on a balloon. |
| 8 | Spacecraft | The station is on a satellite or a different spacecraft. |

**[agreed]** A code that the table does not give is valid. A receiver
reads it as Other. A relay does not change the code.

**[agreed]** The kind does not state the function of a station. A relay,
a gateway and a weather station have no kind of their own.

**[agreed]** The kind is independent of the symbol. Software MUST NOT
derive the kind from the symbol, or the symbol from the kind.

### 3.2 Name

**[agreed]** A name is the string format of
[13-strings](13-strings.md) section 4. It has 8 bytes.

**[agreed]** A name is for display and for diagnosis only. Software MUST
NOT derive the behaviour or the abilities of a station from a name.

**[agreed]** The specification has no list of names. The manufacturer of
a device or the author of a program chooses each name.

### 3.3 Device

**[agreed]** The field has 8 or 16 bytes:

| Bytes | Content |
|---|---|
| 8 | The model of the device, as a name |
| 16 | The make of the device, then its model, each as a name |

### 3.4 Software

**[agreed]** The field has 8 or 16 bytes:

| Bytes | Content |
|---|---|
| 8 | The name of the software, as a name |
| 16 | The name of the software, then its version, each as a name |

**[agreed]** A version has `/` where its usual form has `.`. The version
1.2.3 is the name `1/2/3`.

### 3.5 Transmitter power

**[agreed]** The field is a decimal number. The unit is the watt.

**[proposed]** The value is the power at the output of the transmitter.
It is not the radiated power. The value is not negative, and an infinity
is invalid.

### 3.6 Antenna height

**[agreed]** The field is a decimal number. It is the height of the
antenna above the ground at the place of the antenna.

**[proposed]** The value is not negative, and an infinity is invalid.

### 3.7 Antenna gain

**[agreed]** The field is a decimal number. The unit is the decibel
relative to an isotropic antenna (dBi). The value can be negative.

**[proposed]** An infinity is invalid.

### 3.8 Antenna direction

**[agreed]** The field has 2 bytes: an unsigned integer of 16 bits in
little-endian order. The unit is 1 degree. The value is from 0 to 359. A
larger value is invalid.

**[agreed]** The value is the direction of the largest gain of the
antenna. It is counted clockwise from true north. North is 0.

**[agreed]** A source with an antenna that has no direction omits the
TLV.

### 3.9 Range

**[agreed]** The field is a decimal number. The unit is the kilometre.

**[proposed]** The value is the distance at which the source expects
that a station can receive it. The value is not negative, and an
infinity is invalid.

### 3.10 Object identifier

**[agreed]** The field is the object identifier
([11-object](11-object.md) section 3). It has 8 bytes. If a PDU has this
field, the content of the PDU describes that object and not the source.

## 4. Station information type

**[agreed]** The type byte of a Station information PDU is 3
([08-pdu](08-pdu.md) section 4.3).

**[agreed]** A Station information PDU can hold these TLVs:

| Tag | Field | Section | Bytes | In one PDU |
|---|---|---|---|---|
| 0 | Object identifier | 3.10 | 8 | 0 or 1 |
| 1 | Kind | 3.1 | 1 | 0 or 1 |
| 2 | Device | 3.3 | 8 or 16 | 0 or 1 |
| 3 | Software | 3.4 | 8 or 16 | 0 or 1 |
| 4 | Transmitter power | 3.5 | 2, 3 or 4 | 0 or 1 |
| 5 | Antenna height | 3.6 | 2, 3 or 4 | 0 or 1 |
| 6 | Antenna gain | 3.7 | 2, 3 or 4 | 0 or 1 |
| 7 | Antenna direction | 3.8 | 2 | 0 or 1 |
| 8 | Range | 3.9 | 2, 3 or 4 | 0 or 1 |

**[agreed]** Each TLV is optional. A source omits the TLV of a field for
which it has no value.

**[proposed]** A TLV of this table is invalid in each of these cases:

- Its length is not a length that the table gives.
- Its value is invalid by the section of its field. For a decimal
  number, [05-decimal-number](05-decimal-number.md) section 6 also
  applies.
- Its tag occurs a second time in the PDU.

A TLV with a tag that the table does not give is not invalid. A decoder
skips it ([03-tlv](03-tlv.md) section 4).

## 5. Example

A station is in a car. Its device has the make `EXAMPLE` and the model
`HT1`. Its software has the name `DEMO` and the version 1.2.3. The
transmitter gives 5 W. The antenna is 2.5 m above the ground, has a
gain of −1.5 dBi and has no direction. The range is 15 km. The TLV area
of its Station information PDU has 50 bytes:

| Bytes | TLV |
|---|---|
| `11` `04` | Tag 1, 1 byte. Kind 4, Land vehicle. |
| `1D 03` `8E A3 C4 83 09 00 00 00` `9A 64 00 00 00 00 00 00` | Tag 2, 16 bytes. Make `EXAMPLE`, model `HT1`. |
| `1D 03` `B9 25 0B 00 00 00 00 00` `F1 41 39 00 00 00 00 00` | Tag 3, 16 bytes. Software `DEMO`, version `1/2/3`. |
| `12` `05 00` | Tag 4, 2 bytes. Power 5. |
| `12` `19 F0` | Tag 5, 2 bytes. Height 2.5. |
| `12` `F1 FF` | Tag 6, 2 bytes. Gain −1.5. |
| `22` `0F 00` | Tag 8, 2 bytes. Range 15. |

This example is a copy of a vector of section 6. The file is
authoritative.

## 6. Test vectors

`vectors/station-information.json` has the test vectors. Each vector is
the TLV area of a Station information PDU. It is one of two kinds:

| Kind | Keys | A conformant implementation |
|---|---|---|
| A valid area | `tlv` and the keys of the fields | Decodes `tlv` to the fields. It encodes the fields to `tlv`. |
| An invalid area | `tlv`, `invalid` | Finds that the area or the field of `invalid` is invalid. |

A valid area has a key only for a field that it has:

| Key | Content |
|---|---|
| `tlv` | The bytes of the TLV area |
| `kind` | The code of the kind, as an integer |
| `make`, `model` | The names of the device (section 3.3) |
| `software`, `version` | The names of the software (section 3.4) |
| `power`, `height`, `gain`, `range` | The text form of the decimal number ([05-decimal-number](05-decimal-number.md) section 7) |
| `direction` | The integer of the antenna direction |
| `object` | The text form of the object identifier ([01-station-identifier](01-station-identifier.md) section 6) |
| `other` | Each TLV with a tag that section 4 does not give, in the order of the area: the tag, and the bytes of the value |

The values of `invalid`:

| `invalid` | Cause |
|---|---|
| `kind`, `device`, `software`, `power`, `height`, `gain`, `direction`, `range`, `object` | The TLV of this field is invalid (section 4). |
| `tlv area` | The area breaks [03-tlv](03-tlv.md) section 4. |

Each invalid area has one cause only.

The vectors have these limits:

- A vector does not state what a receiver does with an invalid field.
  That is open (section 7).
- Some vectors follow **[proposed]** rules of this file and of
  [03-tlv](03-tlv.md). They change if the rule changes.

`qua-make-vectors` computes the vectors with `vectors_station.py`. This
module packs the integers with the `struct` module of Python. It takes
the names from `vectors_name.py`, the decimal numbers from
`vectors_decimal.py` and the object identifier from
`vectors_position.py`. It writes the first byte and the extension byte
of each TLV itself. `qua-check-vectors` checks the vectors against
`station_info.py`. That module reads the area with `tlv.py`, the names
with `name_format.py`, the decimal numbers with `decimal_number.py` and
the object identifier with `identifier.py`. The two paths do not import
each other.

## 7. Open items

- **[open]** The fields of RFC 5.11 that have no TLV in this schema so
  far: the symbol, the comment and the messaging flag.
- **[open]** Fields for the abilities of a station, such as "relays" or
  "is a gateway". The kind and the names do not state them.
- **[open]** The text form of the kind for the canonical text of RFC
  5.4.
- **[open]** Does the kind of an object need more codes than the kind
  of a station? An event and a storm are examples
  ([11-object](11-object.md) section 8).
- **[open]** What a receiver does with a Station information PDU that
  has a field with an invalid length or value. The question applies to
  every type (RFC section 14, question 27).
