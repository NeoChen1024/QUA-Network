# Object

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.11](../rfc/qua-network-rfc-0.md#511-pdu-types) |
| Vectors | [`vectors/object.json`](../../vectors/object.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies what an object is, how a PDU refers to an object,
and the schema of the Object type.

It does not specify these:

- The format of an identifier
  ([01-station-identifier](01-station-identifier.md)).
- The TLV container ([03-tlv](03-tlv.md)).
- The free text and its two forms ([13-strings](13-strings.md)
  section 5), and the compressed string
  ([04-text-compression](04-text-compression.md)).
- The form of a time ([06-numbers-units](06-numbers-units.md)).
- Which types can have the object identifier. The schema of each type
  states it.

## 2. Terms

| Term | Meaning |
|---|---|
| Object | A thing that a station describes and that is not the station: a repeater, an event, a storm. |
| Owner | The station that sends the PDUs for an object. It is the source of each of them. |
| Object identifier | The identifier that the owner gives to an object. |
| Object PDU | A PDU of the Object type. |
| Content PDU | A PDU of a different type that has an object identifier. |

## 3. Objects

**[agreed]** An object identifier has the format of a station identifier
([01-station-identifier](01-station-identifier.md)). In a TLV it has the
8 bytes of section 7 of that file. A value that section 5 of that file
rejects is invalid.

**[agreed]** An object identifier belongs to its owner. Two stations can
each have an object with one identifier. These are two objects. A
receiver knows an object by the pair of the source and the object
identifier.

**[agreed]** The source of a PDU for an object is the owner. The object
identifier is not the source of a PDU.

**[agreed]** The object identifier has the tag 0 in each type that can
have it. It is then the first TLV of the TLV area.

**[agreed]** If a PDU has an object identifier, its content describes
that object. If it has none, its content describes the source.

**[agreed]** No PDU declares the start of an object. The first PDU for
an object that a receiver gets makes the object at that receiver. This
PDU is a content PDU or an Object PDU. An Object PDU with the End TLV
(section 4.4) does not make an object.

**[agreed]** The object has no description until an Object PDU gives
one.

## 4. Fields of the Object type

Each field is the value of one TLV.

### 4.1 Object identifier

**[agreed]** The field is the object identifier (section 3).

### 4.2 Description

**[agreed]** The field is a free text that describes the object, for
example `Typhoon Champi`. It is a free text
([13-strings](13-strings.md) section 5).

**[agreed]** The field has two tags, one for each form of the free text
([13-strings](13-strings.md) section 5.2):

- With the passthrough tag, the value is the text.
- With the compressed tag, the value is a length byte and a compressed
  string ([04-text-compression](04-text-compression.md) section 2).

**[agreed]** The text has 1 byte or more. A source that has no
description omits the TLV.

### 4.3 End time

**[agreed]** The field is a time
([06-numbers-units](06-numbers-units.md) section 4). The
owner states that the object no longer exists after this time.

**[agreed]** The field is a suggestion to a receiver. A receiver can
remove the object before this time, for example if its store of PDUs is
full.

### 4.4 End

**[agreed]** The field has no value: the TLV has a length of 0. With
this TLV, the owner states that the object no longer exists.

## 5. Object type

**[agreed]** The type byte of an Object PDU is 2
([08-pdu](08-pdu.md) section 4.3).

**[agreed]** An Object PDU has the object identifier:

| Tag | Field | Section | Bytes | In one PDU |
|---|---|---|---|---|
| 0 | Object identifier | 4.1 | 8 | 1 |

**[agreed]** An Object PDU can also hold these TLVs:

| Tag | Field | Section | Bytes | In one PDU |
|---|---|---|---|---|
| 1 | Description, passthrough | 4.2 | 1 or more | 0 or 1 |
| 2 | Description, compressed | 4.2 | 2 or more | 0 or 1 |
| 3 | End time | 4.3 | 8 | 0 or 1 |
| 4 | End | 4.4 | 0 | 0 or 1 |

**[agreed]** A PDU MUST NOT have both tags of the description
([13-strings](13-strings.md) section 5.2).

**[agreed]** An Object PDU without the End TLV states that the object
exists. The owner can send it again at an interval.

**[agreed]** A receiver that gets an Object PDU with the End TLV
removes the object. It removes the Object PDU and each content PDU that
it keeps for the object. The other TLVs of such a PDU have no effect.

**[agreed]** An Object PDU is invalid in each of these cases:

- It has no object identifier.
- The length of a TLV of the tables is not a length that its table
  gives.
- The value of a TLV is invalid by the section of its field. For a
  compressed description,
  [04-text-compression](04-text-compression.md) section 7 also applies.
- A tag of the tables occurs a second time.
- It has both tags of the description.

A TLV with a tag that the tables do not give is not invalid. A decoder
skips it ([03-tlv](03-tlv.md) section 4).

An Object PDU has 28 bytes at least: 14 for the header, 9 for the TLV of
the object identifier, 1 for the control byte and 4 for the checksum.

### 5.1 The end and the order of PDUs

[08-pdu](08-pdu.md) section 4.6 states when a PDU is older or newer than
a kept PDU, and the time `T`.

**[proposed]** A receiver that gets an Object PDU with the End TLV keeps
the sequence number of that PDU for the time `T`. For the comparison,
that PDU is the kept PDU of the object.

**[proposed]** In that time, a PDU for the object that is older than the
kept PDU does not make the object. A PDU that is newer makes the object
again: the owner uses the identifier again.

**[proposed]** An Object PDU with the End TLV does not remove a content
PDU that is newer than it.

### 5.2 Repetition and the life of an object

**[proposed]** An owner SHOULD send the Object PDU with the End TLV more
than one time, with a longer interval each time. Each is a new PDU with
a new sequence number.

**[proposed]** An owner that sends an Object PDU again at an interval
can give a later end time each time. If the owner stops, the object ends
at the last end time that it gave.

**[proposed]** A receiver removes an object with no end time after a
time of its own choice. A receiver that does not know the UTC time does
the same for each object.

## 6. Example

The station has the object `TYPHOON` with the description
`Typhoon Champi`. The TLV area of its Object PDU has 25 bytes:

| Bytes | TLV |
|---|---|
| `08` `53 B9 7F 6D AC 02 00 00` | Tag 0, 8 bytes. The identifier `TYPHOON`. |
| `1D 01` `54 79 70 68 6F 6F 6E 20 43 68 61 6D 70 69` | Tag 1, 14 bytes. The text. The length has an extension byte. |

The station later states the end of the object. The TLV area has 10
bytes:

| Bytes | TLV |
|---|---|
| `08` `53 B9 7F 6D AC 02 00 00` | Tag 0, 8 bytes. |
| `40` | Tag 4, no value. |

This example is a copy of vectors of section 7. The file is
authoritative.

## 7. Test vectors

`vectors/object.json` has the test vectors. Each vector is the TLV area
of an Object PDU. It is one of two kinds:

| Kind | Keys | A conformant implementation |
|---|---|---|
| A valid area | `tlv` and the keys of the fields | Decodes `tlv` to the fields. If the description is not compressed, it encodes the fields to `tlv`. |
| An invalid area | `tlv`, `invalid` | Finds that the area or the field of `invalid` is invalid. |

A valid area has a key only for a field that it has:

| Key | Content |
|---|---|
| `tlv` | The bytes of the TLV area |
| `object` | The text form of the object identifier ([01-station-identifier](01-station-identifier.md) section 6) |
| `description` | The text |
| `compressed` | `true` if the description has the compressed tag |
| `end_time` | The count of the time, as a string of decimal digits |
| `end` | `true` if the area has the End TLV |
| `other` | Each TLV with a tag that section 5 does not give, in the order of the area: the tag, and the bytes of the value |

The values of `invalid`:

| `invalid` | Cause |
|---|---|
| `object`, `description`, `end_time`, `end` | The TLV of this field is invalid, or the object identifier is absent (section 5). |
| `tlv area` | The area breaks [03-tlv](03-tlv.md) section 4. |

Each invalid area has one cause only.

The vectors have these limits:

- A vector does not state what a receiver does with an invalid field.
  That is open (section 8).
- This file does not pin an encoder of the compressed form. A vector
  with a compressed description is for a decoder only.
- Some vectors follow **[proposed]** rules of [03-tlv](03-tlv.md). They
  change if the rule changes.

`qua-make-vectors` computes the vectors with `vectors_object.py`. This
module packs the integers with the `struct` module of Python. It writes
the first byte and the extension byte of each TLV itself. It takes the
computation of an object identifier from `vectors_position.py`, and each
compressed string from `vectors/text-compression.json`.
`qua-check-vectors` checks the vectors against `object_pdu.py`. That
module reads the area with `tlv.py`, the object identifier with
`identifier.py` and the compressed string with `usx.py`. The two paths
do not import each other.

## 8. Open items

- **[open]** What a receiver does with an Object PDU that is invalid.
  The question applies to every type (RFC section 14, question 27).
- **[open]** How often an owner sends the Object PDU again. How many
  times it sends the Object PDU with the End TLV, and at which
  intervals (section 5.2).
- **[open]** A recommended time after which a receiver removes an
  object that has no End TLV and no end time (section 5.2).
- **[open]** The values of the time `T` and of the window `W`
  ([08-pdu](08-pdu.md) section 11).
- **[open]** Test vectors for section 5.1.
- **[open]** A limit for the length of the description.
- **[open]** A field that states the kind of an object, from a standard
  list (RFC 5.11). The symbol of an object does not state its kind.
  [12-station-information](12-station-information.md) proposes the kind
  field of a station for this use. Its list has only kinds of movement.
- **[open]** What a receiver does with a description that is not valid
  UTF-8 ([13-strings](13-strings.md) section 6).
