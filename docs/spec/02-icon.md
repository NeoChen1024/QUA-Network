# Icon

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.6](../rfc/qua-network-rfc-0.md#56-symbols) |
| Vectors | [`vectors/icon-bitmap.json`](../../vectors/icon-bitmap.json) for the bitmap forms, [`vectors/icon-colour.json`](../../vectors/icon-colour.json) for the colour values. |

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
followed by gap lengths. There is no other form.

**[agreed]** The length of the bitmap field tells the forms apart: 32
bytes is the plain form and 1 to 31 bytes is the gap form. A decoder MUST
reject any other length.

**[agreed]** A sender MUST use the gap form when it is shorter than 32
bytes, and the plain form otherwise.

### 3.1 Plain form

**[agreed]** The 256 pixels in the order of section 2, as 32 bytes.

**[agreed]** A decoder accepts a plain form whether or not its bitmap would
be shorter in the gap form.

### 3.2 Gap form

**[agreed]** The encoder works on 256 bits `t[0]` to `t[255]`, derived
from the pixels `p[0]` to `p[255]` in the order of section 2:

- `t[i] = p[i]` for `i` from 0 to 15 (the top row);
- `t[i] = p[i] XOR p[i - 16]` for `i` from 16 to 255.

Let `s[1]` to `s[k]` be the indices of the set bits of `t` in increasing
order, and let `s[0] = -1` and `s[k+1] = 256`. The gaps are the `k + 1`
differences `s[j] - s[j-1]` for `j` from 1 to `k + 1`. Each is at least 1
and they add up to 257.

The output is a bit string, written into bytes from the most significant
bit down:

1. Every gap, in order, each as an Elias gamma code.
2. Zero bits up to the next byte boundary. None if the string already ends
   on one.

The Elias gamma code of a gap `n` from 1 to 257 is the binary form of `n`
without leading zeros, preceded by one zero bit for each of its bits except
the first. The codes of 1, 2, 3, 4 and 257 are `1`, `010`, `011`, `00100`
and `00000000100000001`.

**[agreed]** A decoder starts with every bit of `t` clear and a position of
-1. It reads a gap and adds it to the position. If the position is then
less than 256 it sets that bit of `t` and reads the next gap; if it is 256
the gaps are complete. It MUST reject the bitmap if:

- the field ends before the position reaches 256;
- the position passes 256;
- a bit after the last gap is not zero;
- eight or more bits remain after the last gap.

It then recovers the pixels row by row from the top:
`p[i] = t[i] XOR p[i - 16]`.

The smallest bitmap in this form is the empty one, the three bytes
`00 80 80`.

### 3.3 Test vectors

`vectors/icon-bitmap.json` is authoritative. An entry with `pixels` gives 32
bytes of pixels in the plain order and the `field` a sender produces for
them; a decoder returns the same pixels for that field. An entry marked
`decode_only` gives a `field` that a sender does not produce and a decoder
accepts. An entry with `reject` gives a `field` that a decoder rejects.

| Bitmap | Field |
|---|---|
| Empty | `008080` |
| Every pixel set | `FFFF01E2` |
| Top left pixel only | `84007800` |
| Bottom right pixel only | `008040` |
| Left half set | `FF01F2` |
| Vertical stripes | `A492480790` |

| Rejected field | Reason |
|---|---|
| `0080` | Ends before the position reaches 256. |
| `804040` | Gaps of 1 and 257 pass position 256. |
| `008100` | A gap of 258 passes position 256. |
| `008081` | A bit after the last gap is set. |
| `00808000` | Eight bits remain after the last gap. |

The file also holds drawn icons and bitmaps that stay in the plain form.

The values are produced by `qua-icon-encode --vectors`. That encoder works
on strings of `0` and `1`, was written from the text of this section, and
shares no code with the encoder and decoder that `qua-check-vectors` runs
against the file, which work on integers. The first three bitmaps of the
table were also worked by hand.

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
- Test vectors for a whole icon TLV, including colour bytes a decoder must
  reject, once the field order is settled.
