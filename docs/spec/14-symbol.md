# Symbol

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.6](../rfc/qua-network-rfc-0.md#56-symbols) |
| Vectors | [`vectors/symbol.json`](../../vectors/symbol.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the two forms of a symbol: the classic form and the
Unicode form.

It does not specify these:

- The icon ([02-icon](02-icon.md)).
- The tag of each form. The schema of a type gives it
  ([12-station-information](12-station-information.md) section 4).
- What a gateway does with the symbol of a legacy packet (RFC 5.6).
- The text form of a symbol in the canonical text (RFC 5.4).

## 2. Terms

| Term | Meaning |
|---|---|
| Symbol | A small picture that stands for a station or an object on a display. |
| Classic form | A symbol of APRS, as one number (section 4). |
| Unicode form | One or two Unicode code points (section 5). |
| Symbol code | The second character of an APRS symbol, from ASCII 33 to 126. |
| Table character | The first character of an APRS symbol: `/`, `\`, or an overlay. |
| Overlay | A table character from `0` to `9` or from `A` to `Z`. It selects the alternate table and is drawn on the symbol. |

## 3. One symbol, two forms

**[agreed]** A symbol has one of two forms. Each form has its own tag.

**[agreed]** A PDU MUST NOT have both forms.

**[agreed]** The symbol is for display only, in both forms. Software
MUST NOT derive behaviour from it.

## 4. Classic form

**[agreed]** The field is a `uint16`
([06-numbers-units](06-numbers-units.md) section 2.1). It has 2 bytes.

**[agreed]** The number of a symbol, with `c` as the ASCII value of the
symbol code:

| Symbol | Number |
|---|---|
| Primary table (`/`) | `c − 33`, from 0 to 93 |
| Alternate table (`\` or an overlay), overlay digit `d` | `94 + (c − 33) × 37 + d`, from 94 to 3571 |

**[agreed]** The overlay digit `d`:

| Table character | `d` |
|---|---|
| `\` | 0 |
| `0` to `9` | 1 to 10 |
| `A` to `Z` | 11 to 36 |

The digits 1 to 36 are those of
[01-station-identifier](01-station-identifier.md) section 3.

**[agreed]** A number of 3572 or more is invalid.

Each valid number is one symbol, and each symbol has one number.

## 5. Unicode form

**[agreed]** The field has one or two Unicode code points. Each code
point is a `uint32` ([06-numbers-units](06-numbers-units.md) section
2.1).

**[agreed]** The field has 4 or 8 bytes. With 4 bytes, it has one code
point. With 8 bytes, it has two, in the order of the text.

**[agreed]** A code point is invalid in each of these cases:

1. It is above U+10FFFF.
2. It is a surrogate: U+D800 to U+DFFF.
3. It is a control character: U+0000 to U+001F, or U+007F to U+009F.
4. It is a variation selector: U+FE00 to U+FE0F.

**[agreed]** A receiver draws the symbol with the emoji presentation.
This is the presentation that the variation selector U+FE0F asks for.
The field does not hold that selector.

**[proposed]** The protocol does not interpret the code points. Two
different fields are two different symbols.

**[proposed]** A receiver that cannot draw the symbol draws the parts
that it can draw, or a placeholder.

Examples of two code points: an emoji with a skin-tone modifier, a flag
of two regional indicators, a keycap (a digit, then U+20E3), and a label
of two characters.

## 6. Test vectors

`vectors/symbol.json` has the test vectors. The key `form` of each
vector is `classic` or `unicode`. A vector is one of four kinds:

| Kind | Keys | A conformant implementation |
|---|---|---|
| A classic symbol | `chars`, `number`, `bytes` | Decodes `bytes` to `number`, and encodes `number` to `bytes`. `chars` is the two characters of the APRS symbol with this number. |
| An invalid classic form | `bytes`, `invalid` | Rejects `bytes`. `invalid` is `number` or `length`. |
| A Unicode symbol | `points`, `bytes` | Decodes `bytes` to the code points `points`, and encodes them to `bytes`. Each code point is a string of hexadecimal digits. |
| An invalid Unicode form | `bytes`, `invalid` | Rejects `bytes`. `invalid` is `code point` or `length`. |

`qua-make-vectors` computes the vectors with `vectors_symbol.py`. This
module gets the overlay digit from the code point of the table
character, and it packs the integers with the `struct` module of Python.
`qua-check-vectors` checks the vectors against `symbol.py`. That module
takes the overlay digit from the table of `identifier.py`. The two
modules do not import each other. For three symbols, the number was also
compared with the number that the record of `docs/interop/` gives.

The tables below are a copy of some vectors. The file is authoritative.

| APRS characters | Number | Bytes |
|---|---|---|
| `/!` | 0 | `00 00` |
| `/>` | 29 | `1D 00` |
| `L#` | 190 | `BE 00` |
| `0-` | 539 | `1B 02` |
| `\k` | 2832 | `10 0B` |
| `Z~` | 3571 | `F3 0D` |

| Code points | Bytes | Content |
|---|---|---|
| U+1F697 | `97 F6 01 00` | An automobile |
| U+2600 | `00 26 00 00` | A sun |
| U+1F1F9, U+1F1FC | `F9 F1 01 00` `FC F1 01 00` | A flag |
| U+0031, U+20E3 | `31 00 00 00` `E3 20 00 00` | A keycap |
| U+0057, U+0058 | `57 00 00 00` `58 00 00 00` | The label `WX` |

## 7. Open items

- **[open]** Where the emoji presentation applies in a symbol of two
  code points. In a keycap, Unicode puts U+FE0F between the digit and
  U+20E3. An emoji with a modifier has no U+FE0F.
- **[open]** The text form of each form for the canonical text (RFC
  5.4, RFC 5.6).
- **[open]** What a receiver does with a symbol that is invalid. The
  question applies to every field (RFC section 14, question 27).
