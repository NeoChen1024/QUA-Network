# Station identifier

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.8](../rfc/qua-network-rfc-0.md#58-callsign-encoding) |
| Vectors | [`vectors/identifier.json`](../../vectors/identifier.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

A station identifier is a callsign together with an optional SSID, encoded
as one 64-bit unsigned value. It is used wherever a station is named: the
source of a PDU, a message addressee, the input of a hop trace entry.

## 2. Layout

```
MSB                                                        LSB
 63  62                                                    0
+---+------------------------------------------------------+
| F | 12 digits, base 37, 63 bits                          |
+---+------------------------------------------------------+

F = 0:  | callsign, 11 digits               | SSID, 1 digit  |
F = 1:  | callsign, 10 digits          | SSID, 2 digits      |
```

- **[agreed]** Bits 62 to 0 hold a number below 37^12, read as 12 base-37
  digits with the first digit most significant.
- **[agreed]** The SSID occupies the last digit or the last two digits. Bit
  63, F, says which: 0 for one digit, 1 for two. The callsign occupies the
  remaining 11 or 10 digits.

37^12 is 6,582,952,005,840,035,281, which is below 2^63.

## 3. Digit table

**[agreed]** One table is used for every digit.

| Digit | In the callsign | In the SSID |
|---|---|---|
| 0 | padding when leading, `/` otherwise | no character |
| 1 to 10 | `0` to `9` | `0` to `9` |
| 11 to 36 | `A` to `Z` | `A` to `Z` |

## 4. Encoding

Let `d(x)` be the digit of character `x` from the table.

1. **Callsign.** The callsign is 1 to 11 characters from `0` to `9`, `A` to
   `Z` and `/`, and does not begin with `/`. Its value `C` is the callsign
   read as a base-37 number, first character most significant. Leading
   digits that the callsign does not fill are 0.
2. **No SSID.** F = 0 and the value is `C * 37`.
3. **One-character SSID** `s`. F = 0 and the value is `C * 37 + d(s)`.
4. **Two-character SSID** `s1 s2`. The callsign is at most 10 characters.
   F = 1 and the low 63 bits are `C * 37^2 + d(s1) * 37 + d(s2)`.

Decoding reverses these steps. In the callsign part, leading zero digits
are padding and every other zero digit is `/`.

## 5. Validity

A decoder MUST reject a value that breaks any of these rules, and an encoder
MUST NOT produce one. With them, every valid value has exactly one text form
and every valid text form has exactly one value.

- **[agreed]** The callsign part is not all zeros. The all-zero identifier
  is reserved.
- **[proposed]** The low 63 bits are below 37^12.
- **[proposed]** With F = 1, neither SSID digit is 0. A one-character SSID
  is always encoded with F = 0.
- **[proposed]** The one-character SSID `0` is invalid. A two-character
  SSID is an opaque string: `07` and `7` are different identifiers.

**[agreed]** The encoding does not judge whether a string is a real
callsign. A callsign ending in `/`, or one too short to have been issued, is
representable. Callsign validity is a separate matter.

## 6. Text form

**[agreed]** The callsign, then, if there is an SSID, a dash and the SSID:
`N0CALL`, `N0CALL-7`, `N0CALL-15`. Letters are upper case.

## 7. Byte order

**[open]** The byte order of the identifier inside a PDU, to be fixed with
the header layout. Where the identifier is the input of a hash, it is the
8 bytes in big-endian order (RFC 5.9).

## 8. Mapping to an AX.25 address

This applies to gateways to legacy APRS and to the optional AX.25
encapsulation.

- An identifier maps to an AX.25 address only if its callsign is at most six
  characters without `/` and its SSID is absent or is the decimal string
  `1` to `15`.
- AX.25 SSID 0 maps to an identifier with no SSID.
- Any other identifier has no AX.25 address. **[open]** What the optional
  AX.25 encapsulation carries in that case (RFC 7.2).

## 9. Test vectors

| Text form | F | Value (hex, 64 bits) |
|---|---|---|
| `N0CALL` | 0 | `0x0000000E5BEBEB3D` |
| `N0CALL-7` | 0 | `0x0000000E5BEBEB45` |
| `N0CALL-G` | 0 | `0x0000000E5BEBEB4E` |
| `N0CALL-15` | 1 | `0x8000021349190021` |
| `BV5AB-33` | 1 | `0x80000007B01E3AF5` |
| `PJ4/KA1ABC` | 0 | `0x01C577F1F48964A5` |
| `PJ4/KA1ABC-15` | 1 | `0xC18A55F857DB8C29` |
| `YW18FIFA/MM` | 0 | `0x589FF5E2D11F745B` |
| `YW18FIFA/MM-A` | 0 | `0x589FF5E2D11F7466` |

This table is a copy of `vectors/identifier.json`, which is authoritative.
Each value was checked by decoding it back to its text form, and
`qua-check-vectors` recomputes them.

## 10. Open items

- Use of the unused values: the all-zero identifier, and 37^12 up to 2^63
  in the low 63 bits.
- Whether the SSID positions use base 36, with a table that lacks the
  excluded symbol, so that the two SSID rules of section 5 become
  structural. The cost is a mixed radix.
- The byte order of section 7.
- The AX.25 encapsulation case of section 8.
- Vectors for values that a decoder must reject.
