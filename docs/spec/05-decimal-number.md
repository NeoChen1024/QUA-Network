# Decimal number

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.3](../rfc/qua-network-rfc-0.md#decimal-number) |
| Vectors | None yet. |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the decimal number: its value, its formats in bytes,
the encodings that are invalid, and its text form.

It does not specify these:

- Which fields are decimal numbers (RFC 5.3).
- The unit of a field (RFC 5.3).
- Which fields allow an infinity.

## 2. Value

**[agreed]** A decimal number has a significand `m` and an exponent `e`.
Both are integers. The value is `m` × 10^`e`.

**[agreed]** The definition of a field states whether the field is a
decimal number.

## 3. Formats

**[agreed]** A decimal number has one of three formats. There is no
format of 1 byte.

| Bytes | Bits of `e` | Range of `e` | Bits of `m` | Range of `m` |
|---|---|---|---|---|
| 2 | 4 | −8 to 7 | 12 | −2048 to 2047 |
| 3 | 4 | −8 to 7 | 20 | −524288 to 524287 |
| 4 | 8 | −128 to 127 | 24 | −8388608 to 8388607 |

**[agreed]** These rules apply to each format:

1. `e` comes before `m`. `e` has the most significant bits of the first
   byte.
2. The bytes are in big-endian order.
3. `e` and `m` are two's-complement integers.

**[agreed]** The length of the TLV gives the format. A TLV therefore
holds one decimal number at most, and the number is the last field of the
TLV.

In the formats of 2 and 3 bytes, the first hexadecimal digit is `e`. The
bytes `F0 FD` have `e` = −1 and `m` = 253. The value is 25.3.

## 4. One encoding for one value

**[agreed]** Zero has one encoding: the 2 bytes `00 00`, with `m` 0 and
`e` 0.

**[agreed]** For every other finite value, `m` MUST NOT be a multiple of
10.

**[agreed]** A sender MUST use the shortest format that holds `m` and
`e`.

With these rules, `m` and `e` are unique for a value, and one value has
one encoding.

## 5. Infinity

**[agreed]** The format has two special values: positive infinity and
negative infinity. They are in the 2-byte format only.

**[agreed]** The encodings:

| Value | Bytes | `m` | `e` |
|---|---|---|---|
| Positive infinity | `70 00` | 0 | 7 |
| Negative infinity | `80 00` | 0 | −8 |

**[agreed]** These rules apply:

- Positive infinity states that the value is greater than every value
  that the sender can give.
- Negative infinity states that the value is less than every such value.
- An infinity is not an error code.
- The definition of a field states whether the field allows an infinity.
- The format has no "not a number".
- A sender that has no value omits the TLV.
- The other 13 encodings of 2 bytes with `m` 0 are invalid. This file
  does not reserve them for a later use.

## 6. Invalid encodings

**[agreed]** A decoder MUST reject a decimal number in each of these
cases:

1. The number does not have 2, 3 or 4 bytes.
2. `m` is a multiple of 10 and is not 0.
3. `m` is 0, and the bytes are not `00 00`, `70 00` or `80 00`.
4. A shorter format holds `m` and `e`.
5. The number is an infinity, and the field does not allow it.

## 7. Text form

**[agreed]** The text form of a finite value follows from `e`:

- If `e` is from −8 to 7, the text is the plain decimal value. It has no
  exponent notation: `25.3`, `-12.7`, `0.12`, `85000`.
- If `e` is outside −8 to 7, the text is `m`, the letter `e` and the
  exponent, each as an integer: `3e9`, `-15e-12`. Such a value has no
  plain form.

**[agreed]** These rules apply to the plain form:

- It has no `+` sign.
- Its integer part is `0`, or starts with a digit from 1 to 9.
- Its fraction has 8 digits at most and does not end in `0`.
- The text `-0` is invalid.

**[agreed]** The text form of positive infinity is `inf`. The text form
of negative infinity is `-inf`.

**[agreed]** A parser MUST reject a text that breaks these rules, or
whose value has no encoding.

One value has one text form. The conversion to text moves the decimal
point and needs no rounding.

## 8. Examples

A script that is not part of this repository computed the bytes. The
examples are not test vectors.

| Value | `m` | `e` | Bytes | Text |
|---|---|---|---|---|
| 0 | 0 | 0 | `00 00` | `0` |
| 9 | 9 | 0 | `00 09` | `9` |
| 100 | 1 | 2 | `20 01` | `100` |
| 25.3 | 253 | −1 | `F0 FD` | `25.3` |
| −12.7 | −127 | −1 | `FF 81` | `-12.7` |
| 853.4 | 8534 | −1 | `F0 21 56` | `853.4` |
| 1013.2 | 10132 | −1 | `F0 27 94` | `1013.2` |
| 10668.25 | 1066825 | −2 | `FE 10 47 49` | `10668.25` |
| 3 × 10^9 | 3 | 9 | `09 00 00 03` | `3e9` |
| −15 × 10^−12 | −15 | −12 | `F4 FF FF F1` | `-15e-12` |
| Positive infinity | 0 | 7 | `70 00` | `inf` |
| Negative infinity | 0 | −8 | `80 00` | `-inf` |

Invalid encodings:

| Bytes | Case of section 6 |
|---|---|
| `00` | 1 |
| `10 0A` | 2: `m` is 10 |
| `10 00` | 3 |
| `00 00 09` | 4: the 2-byte format holds `m` 9 and `e` 0 |
| `00 00 00 09` | 4 |

## 9. Open items

- **[open]** Test vectors, with encodings that a decoder rejects (RFC
  section 15, step 15).
- **[open]** The questions on the use of the decimal number are in the
  RFC (section 14, question 24).
