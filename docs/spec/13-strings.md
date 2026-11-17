# Strings

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.7](../rfc/qua-network-rfc-0.md#57-text-compression) for free text, and [section 5.11](../rfc/qua-network-rfc-0.md#station-information-type) for the name |
| Vectors | [`vectors/name.json`](../../vectors/name.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file lists each string format of the specification. It specifies
two of them: the name, and the free text with its two forms.

It does not specify these:

- The station identifier
  ([01-station-identifier](01-station-identifier.md)).
- The object identifier ([11-object](11-object.md) section 3).
- The bits of a compressed string
  ([04-text-compression](04-text-compression.md)).
- Which format a field has. The definition of the field states it.

## 2. Terms

| Term | Meaning |
|---|---|
| String format | A rule that gives the characters of a string, its length and its bytes. |
| Name | A string of 12 characters at most, in 8 bytes (section 4). |
| Free text | A string of UTF-8 with no fixed length (section 5). |
| Passthrough form | The free text as it is. |
| Compressed form | A length byte and the compressed string of the free text. |

## 3. String formats

**[proposed]** The specification has the string formats of this table. A
field that holds a string has one of them.

| Format | Characters | Length in characters | Bytes | Specified in |
|---|---|---|---|---|
| Station identifier | `0` to `9`, `A` to `Z`, `/`, and an SSID of `0` to `9` and `A` to `Z` | 1 to 11, and an SSID of 0 to 2 | 8 | [01-station-identifier](01-station-identifier.md) |
| Object identifier | Those of a station identifier | Those of a station identifier | 8 | [11-object](11-object.md) section 3 |
| Name | `0` to `9`, `A` to `Z`, `/` | 1 to 12 | 8 | Section 4 |
| Free text | Each character of UTF-8 | The TLV gives the limit | 255 at most | Section 5 |

A station identifier with an SSID of 2 characters has 10 characters at
most before the SSID.

The Unicode form of a symbol is not a string format. It is two code
points at most, each as an integer ([14-symbol](14-symbol.md) section
5).

## 4. Name

### 4.1 Format

**[agreed]** A name is a string of 1 to 12 characters. The characters
are `0` to `9`, `A` to `Z` and `/`. A name does not begin with `/`.

**[agreed]** The value of a name is the name read as a number in base
37. The first character is the most significant digit. The digit of each
character is that of the callsign in
[01-station-identifier](01-station-identifier.md) section 3.

**[agreed]** A name has no SSID and no bit `F`. Each of the 12 digits is
a character of the name. The value of a name is therefore not the value
of the station identifier with the same characters.

**[agreed]** A name is 8 bytes: its value as an unsigned integer of 64
bits in little-endian order
([06-numbers-units](06-numbers-units.md) section 2).

**[proposed]** A name is invalid in each of these cases:

- Its value is 0.
- Its value is 37^12 or more.

To decode a name, a decoder reads the value as 12 digits in base 37. The
leading digits that are 0 are padding. Each other digit that is 0 is
`/`.

### 4.2 Text form

**[agreed]** The text form of a name is its characters. Letters are
upper case.

One name has one value, and one valid value has one name.

### 4.3 Test vectors

`vectors/name.json` has the test vectors. Each vector is one of three
kinds:

| Kind | Keys | A conformant implementation |
|---|---|---|
| A name | `text`, `value`, `bytes` | Encodes `text` to `bytes`, and decodes `bytes` to `text`. `value` is the value as a hexadecimal number of 64 bits. |
| An invalid value | `bytes`, with `invalid` equal to `value` | Rejects `bytes`. |
| An invalid text | `text`, with `invalid` equal to `text` | Rejects `text`. |

`qua-make-vectors` computes the vectors with `vectors_name.py`. This
module gets the digit of a character from its code point. It adds the
digits with their powers of 37, and it packs the bytes with the `struct`
module. `qua-check-vectors` checks the vectors against `name_format.py`.
That module takes the digit from the table of `identifier.py` and
multiplies step by step. The two modules do not import each other.

The table below is a copy of some vectors. The file is authoritative.

| Text | Value (hex, 64 bits) | Bytes |
|---|---|---|
| `0` | `0x0000000000000001` | `01 00 00 00 00 00 00 00` |
| `N0CALL` | `0x0000000063596739` | `39 67 59 63 00 00 00 00` |
| `1/2/3` | `0x00000000003941F1` | `F1 41 39 00 00 00 00 00` |
| `DEMO/` | `0x00000000019C73BD` | `BD 73 9C 01 00 00 00 00` |
| `AB/CD/EF/GHI` | `0x1BF629CD26E4A78F` | `8F A7 E4 26 CD 29 F6 1B` |
| `ZZZZZZZZZZZZ` | `0x5B5B57F8A98A5DD0` | `D0 5D 8A A9 F8 57 5B 5B` |

## 5. Free text

### 5.1 Characters

**[agreed]** A free text is UTF-8.

**[agreed]** The format does not forbid a character in a free-text
field. A text can hold control characters and other special characters.
An implementation MUST be prepared for every character in such a field.

**[proposed]** This rule applies when the implementation shows the text,
writes it to a log or gives it to a different program.

### 5.2 Two forms and two tags

**[agreed]** A free-text field has one of two forms in a PDU:

| Form | Value of the TLV |
|---|---|
| Passthrough | The text |
| Compressed | A length byte, then the compressed string ([04-text-compression](04-text-compression.md) section 2) |

**[agreed]** The length byte gives the length of the text in bytes. A
passthrough form has no length byte.

**[agreed]** Each free-text field has two tags: one for the passthrough
form and one for the compressed form. The tag states the form. The
string has no marker.

**[agreed]** The two tags of one field are adjacent numbers.

**[agreed]** A PDU MUST NOT have both tags of one field.

**[agreed]** The uncompressed form of a PDU has the passthrough tag and
the text. The schema of a type gives the two tags of each free-text
field.

### 5.3 Choice of the form

**[agreed]** A sender SHOULD compress each free text as a trial. It
SHOULD send the compressed form only if that form is shorter than the
text. If not, it SHOULD send the passthrough form.

**[agreed]** The length byte counts as a part of the compressed form in
this comparison.

**[agreed]** A sender can always send the passthrough form.

**[agreed]** A decoder does not run an encoder. It does not reject a
field because the sender did not choose the shorter form.

### 5.4 Invalid string

[04-text-compression](04-text-compression.md) section 7 lists each
compressed string that is invalid. It also states what a decoder and a
receiver do with an invalid string.

## 6. Open items

- **[open]** A name has 12 characters at most. Is that sufficient for
  each field that has a name
  ([12-station-information](12-station-information.md))?
- **[open]** What a receiver does with a free text that is not valid
  UTF-8.
- **[open]** A limit for the length of a free text that is lower than
  the limit of the TLV.
