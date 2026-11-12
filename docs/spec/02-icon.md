# Icon

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.6](../rfc/qua-network-rfc-0.md#56-symbols) |
| Vectors | [`vectors/icon-colour.json`](../../vectors/icon-colour.json) for the colour values. None yet for the bitmap. |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

An icon is a small picture that a station sends of itself. It is an optional
TLV that accompanies the station's symbol (RFC 5.6) and does not replace it.

**[proposed]** The icon is display only. Software MUST NOT derive behaviour
from it.

## 2. Content

- **[proposed]** A bitmap of 16 by 16 pixels, one bit per pixel.
- **[proposed]** Pixels are ordered by row from top to bottom and, within a
  row, from left to right. The leftmost pixel of a row is the most
  significant bit of its first byte. Uncompressed, the bitmap is 32 bytes.
- **[agreed]** Two colours of one byte each, foreground and background. A
  set bit is drawn in the foreground colour and a clear bit in the
  background colour.
- **[agreed]** A display with one colour ignores both colour bytes and draws
  set bits.

## 3. Colour values

**[agreed]** A colour byte takes its values from the part of the xterm
256-colour palette that has fixed values.

| Value | Meaning |
|---|---|
| 0 | As foreground: the device default. As background: transparent. |
| 1 to 15 | Invalid. |
| 16 to 231 | Colour cube. `value = 16 + 36 * r + 6 * g + b`, with `r`, `g`, `b` each from 0 to 5. |
| 232 to 255 | Grey ramp. All three channels are `8 + 10 * (value - 232)`, from 8 to 238. |

The channel value for a cube level is 0 for level 0 and `55 + 40 * level`
otherwise:

| Level | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Channel value | 0 | 95 | 135 | 175 | 215 | 255 |

A decoder MUST reject an icon with a colour byte from 1 to 15.

These are the default colours 16 to 255 of xterm. `vectors/icon-colour.json`
lists the RGB value of each of the 240 colours. It was extracted from
`256colres.h` of xterm patch 412 (2026-10-11), and the formulas above match
the generator `256colres.pl` in the same source. The values are fixed here:
a later change in xterm does not change this specification.

## 4. Relation to the symbol

- **[agreed]** A PDU that carries an icon also carries a symbol, in the
  classic or the Unicode form. The icon is bound to that symbol.
- **[agreed]** A receiver that does not support icons, or holds no icon for
  the station, shows the symbol.

## 5. Receiver state

A receiver that supports icons holds, for each station identifier, at most
one icon together with the symbol it is bound to.

- **[agreed]** An icon received from an identifier replaces the icon held
  for that identifier, and its symbol becomes the bound symbol.
- **[agreed]** A PDU from that identifier that carries no icon and whose
  symbol differs from the bound symbol drops the icon. The comparison is
  exact: a different form, or any different byte, is a different symbol.
  This is how a station withdraws its icon.
- **[proposed]** A PDU that carries no symbol leaves the icon as it is.
- **[agreed]** An icon has no lifetime of its own. It is kept until it is
  replaced or dropped as above, or until the receiver discards its record of
  the station, and is discarded with that record.

A receiver's storage for icons is therefore bounded by the number of
stations it tracks.

## 6. Sending

- **[proposed]** A sender SHOULD NOT include the icon in every beacon. It
  sends the icon every Nth beacon and only the symbol in between. **[open]**
  The value of N.
- **[proposed]** To change its symbol and keep its icon, a station sends the
  icon again with the new symbol.
- **[proposed]** To withdraw its icon, a station sends a different symbol
  without an icon.

## 7. Text form

**[proposed]** In canonical text the icon is written in hexadecimal.

## 8. Gateways and display services

**[proposed]** A gateway or a display service MAY decline to show icons. It
MUST NOT alter or remove the TLV when forwarding (RFC 6.2).

## 9. Open items

- Whether the bitmap is compressed, and by what method. If it is, the
  encoding is canonical in the manner of RFC 5.7: compressed if and only if
  strictly shorter, one exactly specified encoder, and a decoder that
  rejects any other encoding.
- The order of the fields inside the TLV, and its tag.
- The repeat interval N of section 6.
- Whether 16 by 16 is the only size.
- Test vectors for the bitmap and for icons that a decoder must reject.
