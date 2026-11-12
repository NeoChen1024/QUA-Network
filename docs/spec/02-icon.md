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

- **[agreed]** A bitmap of 16 by 16 pixels, one bit per pixel. This is the
  only size and depth of this TLV. A larger or a multi-colour icon is not
  defined; one added later would be a separate TLV.
- **[agreed]** Pixels are ordered by row from top to bottom and, within a
  row, from left to right. The leftmost pixel of a row is the most
  significant bit of its first byte. In the plain form (section 3) the
  bitmap is 32 bytes.
- **[agreed]** Two colours of one byte each, foreground and background. A
  set bit is drawn in the foreground colour and a clear bit in the
  background colour.
- **[agreed]** A display with one colour ignores both colour bytes and draws
  set bits.

## 3. Bitmap forms

**[agreed]** The bitmap is sent in one of two forms: plain, or row XOR
followed by run lengths. There is no other form.

**[agreed]** The length of the bitmap field tells the forms apart: 32
bytes is the plain form and 1 to 31 bytes is the run-length form. A decoder
MUST reject any other length.

**[agreed]** A sender MUST use the run-length form when it is shorter than
32 bytes, and the plain form otherwise.

### 3.1 Plain form

**[agreed]** The 256 pixels in the order of section 2, as 32 bytes.

### 3.2 Run-length form

**[agreed]** The encoder works on 256 bits `t[0]` to `t[255]`, derived
from the pixels `p[0]` to `p[255]` in the order of section 2:

- `t[i] = p[i]` for `i` from 0 to 15 (the top row);
- `t[i] = p[i] XOR p[i - 16]` for `i` from 16 to 255.

A run is a maximal sequence of consecutive equal bits of `t`. The output is
a bit string, written into bytes from the most significant bit down:

1. One bit: the value of `t[0]`.
2. The length of every run, in order, each as an Elias gamma code.
3. Zero bits up to the next byte boundary. None if the string already ends
   on one.

The Elias gamma code of a length `n` from 1 to 256 is the binary form of `n`
without leading zeros, preceded by one zero bit for each of its bits except
the first. The codes of 1, 2, 3, 4 and 256 are `1`, `010`, `011`, `00100`
and `00000000100000000`.

**[agreed]** A decoder reads the first bit and then reads run lengths
until they add up to 256. The runs alternate in value, starting with the
value of the first bit. It MUST reject the bitmap if:

- the field ends before the run lengths add up to 256;
- the run lengths add up to more than 256;
- a bit after the last run length is not zero;
- eight or more bits remain after the last run length.

It then recovers the pixels row by row from the top.

The smallest bitmap in this form is the empty one, the three bytes
`00 40 00`.

## 4. Colour values

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

Black is value 16 and white is value 231, both in the colour cube. The grey
ramp contains neither.

A decoder MUST reject an icon with a colour byte from 1 to 15.

These are the default colours 16 to 255 of xterm. `vectors/icon-colour.json`
lists the RGB value of each of the 240 colours. It was extracted from
`256colres.h` of xterm patch 412 (2026-10-11), and the formulas above match
the generator `256colres.pl` in the same source. The values are fixed here:
a later change in xterm does not change this specification.

## 5. Relation to the symbol

- **[agreed]** A PDU that carries an icon also carries a symbol, in the
  classic or the Unicode form. The icon is bound to that symbol.
- **[agreed]** A receiver that does not support icons, or holds no icon for
  the station, shows the symbol.

## 6. Receiver state

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

## 7. Sending

- **[proposed]** A sender SHOULD NOT include the icon in every beacon. It
  sends the icon every Nth beacon and only the symbol in between. **[open]**
  The value of N.
- **[proposed]** To change its symbol and keep its icon, a station sends the
  icon again with the new symbol.
- **[proposed]** To withdraw its icon, a station sends a different symbol
  without an icon.

## 8. Text form

**[proposed]** In canonical text the icon is written in hexadecimal.

## 9. Gateways and display services

**[proposed]** A gateway or a display service MAY decline to show icons. It
MUST NOT alter or remove the TLV when forwarding (RFC 6.2).

## 10. Open items

- The order of the fields inside the TLV, and its tag. Section 3 assumes
  that the length of the bitmap field follows from the length of the TLV.
- The repeat interval N of section 7.
- Test vectors for the bitmap and for icons that a decoder must reject.
