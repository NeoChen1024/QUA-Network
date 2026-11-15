# Values of the frequency specification

| | |
|---|---|
| Status | Draft. Not frozen. A paragraph, value rule or catalogue row of this file is **[proposed]** if it has no other label. An **[agreed]** item is a decision of the author. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of a frequency specification give values
([09 section 7](09-other.md#7-frequency-specification)). The tokens come
from [09](09-other.md). This file adds no token and changes no finding.
The rule prefix is `val`.

The tokens are in the text of a position comment, of the comment of an
Object or an Item, of a Mic-E status text and of a status report. The
value rules are the same in each place.

These parts are outside this file:

- a frequency in the name of an Object
  ([amb.freq.objname](09-other.md#amb.freq.objname)). The tokenizer makes
  no token for it;
- the net and meeting fields of a frequency Object
  ([err.freq.netmtg](09-other.md#err.freq.netmtg));
- a frequency in a message, and the frequency of the DX cluster format
  (p. 117/93, p. 120/96).

## 2. Conventions

The conventions of [10-values section 2](10-values.md#2-conventions) apply
to this file. These are the terms, the value tables, the findings that
concern a value, and the effects.

"The number of bytes `a` to `b`" is the decimal number of those digits.

The token of `freq.rx`, `freq.tone`, `freq.offset` or `freq.range`
includes its leading `SP`, if it has one. In this file, `b` is the bytes
of such a token without that `SP`. For every other token, `b` is all
bytes of the token. Offsets in `b` count from 0.

The bytes of these tokens are also bytes of the text that contains them.
The value rule of that text gives them unchanged.

## 3. Frequency

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.freq.mhz"></a>`val.freq.mhz` | Frequency | [`freq.mhz`](09-other.md#freq.mhz) | `M` is the number of bytes 0 to 2. If byte 6 is a digit, the count is 1000 · `M` plus the number of bytes 4 to 6, with step 1. If byte 6 is `SP`, the count is 1000 · `M` plus 10 times the number of bytes 4 to 5, with step 10. | Kilohertz, step 1 or 10, 0 to 999999 | p. 114/90 |
| <a id="val.freq.uw"></a>`val.freq.uw` | Frequency above 999 MHz | [`freq.uw`](09-other.md#freq.uw) | Byte 0 gives `h` (table below). `M` is 100 · `h` plus the number of bytes 1 to 2. The count follows from `M` as in `val.freq.mhz`. | Kilohertz, step 1 or 10 | p. 119/95, p. 120/96 |
| <a id="val.freq.ghz"></a>`val.freq.ghz` | Frequency in the GHz form | [`freq.ghz`](09-other.md#freq.ghz) | `G` is the number of bytes 0 to 2, where a leading `SP` counts as `0`. The count is 1000 · `G` plus the number of bytes 4 to 6. | Megahertz, step 1, 0 to 999999 | p. 119/95 |
| <a id="val.freq.rx"></a>`val.freq.rx` | Alternate receive frequency | [`freq.rx`](09-other.md#freq.rx) | The count is 1000 times the number of bytes 0 to 2, plus the number of bytes 4 to 6. | Kilohertz, step 1, 0 to 999999 | p. 114/90 |

The letter of `freq.uw` gives `h`, the frequency in hundreds of
megahertz. **[agreed]**

| Letter | A | B | C | D | E | F | G | H | I | J | K | L | M | N | O |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `h` | 12 | 23 | 24 | 34 | 56 | 57 | 58 | 101 | 102 | 103 | 104 | 105 | 240 | 241 | 242 |

APRS12c gives one example for each letter (p. 119/95, p. 120/96). Each
`h` above comes from its example (derived). For example, `A96.000MHz` is
1296 MHz, thus `h` of `A` is 12.

A packet has one frequency at most: the tokenizer looks for a frequency
at one place only. `freq.lead` has no value.

## 4. Tone, offset and range

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.freq.tone.kind"></a>`val.freq.tone.kind` | Kind of tone | [`freq.tone`](09-other.md#freq.tone) | Byte 0 `'T'` or `'t'` and three digits: `tone`. Byte 0 `'C'` or `'c'`: `ctcss`. Byte 0 `'D'` or `'d'`: `dcs`. `Toff` or `toff`: `off`. `1750` or `l750`: `burst`. | Code | p. 114/90, p. 117/93 |
| <a id="val.freq.tone"></a>`val.freq.tone` | Tone frequency | `freq.tone` | Kind `tone` or `ctcss`: `N` is the number of bytes 1 to 3. If the list below has a tone whose whole part is `N`, the value is that tone. If `N` is 0: [amb.val.tone0](#amb.val.tone0). If `N` / 10 is a tone of the list: [amb.val.tonetenths](#amb.val.tonetenths). If not, the value is `N` ([amb.val.tone](#amb.val.tone)), and outside 60 to 300: [amb.val.tonerange](#amb.val.tonerange). Kind `burst`: 1750. The kinds `dcs` and `off` give no tone frequency. | Hertz. Step 0.1 for a tone of the list, step 1 for every other value. | p. 114/90, p. 116/92, p. 117/93 |
| <a id="val.freq.dcs"></a>`val.freq.dcs` | DCS code | `freq.tone` | Kind `dcs` only: bytes 1 to 3. | Byte string of three digits | p. 114/90, p. 117/93 |
| <a id="val.freq.narrow"></a>`val.freq.narrow` | Narrow modulation | `freq.tone` | The flag is set if byte 0 is a lower-case letter. | Flag | p. 114/90, p. 117/93 |
| <a id="val.freq.offset"></a>`val.freq.offset` | Transmit offset | [`freq.offset`](09-other.md#freq.offset) | The number of bytes 1 to 3, negative if byte 0 is `'-'`. `+000` and `-000` both give 0. | 10 kHz, step 1, −990 to 990 | p. 114/90, p. 117/93 |
| <a id="val.freq.range"></a>`val.freq.range` | Range | [`freq.range`](09-other.md#freq.range) | Byte 0 gives the direction: `'R'` is every direction, and `'N'`, `'S'`, `'E'`, `'W'` are north, south, east and west. The number of bytes 1 to 2 is the range. Byte 3 gives the unit: `'m'` is miles, `'k'` is kilometres. | Miles or kilometres, step 1, 0 to 99 | p. 114/90, p. 116/92 |

**[agreed]** The tone frequency is a number in hertz. It has the tenths
of a hertz if the list below gives them. A station can use a tone that the
list does not have. Such a tone keeps the number of its three digits.

**[agreed]** The list has 51 tones, in hertz. It has 39 tones of the
standard:

67.0, 69.3, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4,
100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5,
141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2, 192.8,
203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3.

It also has 12 common tones that are not in the standard:

150.0, 159.8, 165.5, 171.3, 177.3, 183.5, 189.9, 196.6, 199.5, 206.5,
229.1, 254.1.

The whole parts of these 51 tones are all different. Thus three digits
select one tone at most.

The list comes from the article "Continuous Tone-Coded Squelch System" of
the English Wikipedia, read on 2026-11-15. The article gives the 39 tones
as the tones of the standard TIA-603-E, and the 12 tones as tones that
are not in it. The standard itself was not read. The article gives the
tone of 150.0 Hz as a tone of NATO radios.

**[agreed]** Three forms of the three digits have the effect `computable`:

- The digits `000`. The value is 0
  ([amb.val.tone0](#amb.val.tone0)).
- Digits that are a tone of the list in tenths of a hertz, for example
  `885` for 88.5 Hz. The value is that tone
  ([amb.val.tonetenths](#amb.val.tonetenths)).
- Another number that is not in the list, and that is below 60 or above
  300. The value is the number
  ([amb.val.tonerange](#amb.val.tonerange)).

A number from 60 to 300 that is not in the list is a value in both modes,
with step 1.

The list has 12 tones below 100 Hz. Only these have three digits in
tenths of a hertz. No such number is the whole part of a tone of the list,
because the highest whole part is 254.

**[agreed]** The kinds `tone` and `ctcss` are different:

- `tone`: a radio that uses the frequency sends the tone. Its squelch
  does not use the tone.
- `ctcss`: the radio sends the tone, and its squelch also uses the tone.

APRS12c calls the first a "PL tone" and the second a "CTCSS tone", and
states no difference (p. 114/90). The difference above is a decision of
the author.

A packet can have one `freq.range` token for each letter. Each token gives
one range.

An offset of 0 is a forced simplex operation (p. 114/90). This file gives
it as the number 0.

A mile is the statute mile
([amb.val.miles](10-values.md#amb.val.miles)).

## 5. D-STAR

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.freq.dstar"></a>`val.freq.dstar` | D-STAR marker, access repeater | [`freq.dstar`](09-other.md#freq.dstar) | The token sets the flag. In the form of 15 bytes: the repeater is bytes 7 to 12 without trailing `SP`, and the module is byte 14. | Flag. Repeater: byte string of 1 to 6 bytes. Module: byte string of one byte. | p. 116/92 |

## 6. Effect of findings

This table gives the effect of each finding that concerns a value of
sections 3 to 5. A token that has no row has only findings with the
effect `kept`.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `freq.mhz`, `freq.uw` | `syntax` (`MHz` in another case, [amb.freq.case](09-other.md#amb.freq.case)) | Frequency | **[agreed]** `kept` |
| `freq.offset` | `value` (above 990) | Transmit offset | **[agreed]** `computable`: the number of the digits |

**[agreed]** A receiver ignores the case of `MHz` (p. 114/90). Thus the
frequency keeps its value in both modes. The `syntax` finding of the
tokenizer stays.

## 7. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the decoder does |
|---|---|---|---|---|---|
| <a id="amb.val.tone"></a>`amb.val.tone` | p. 114/90, p. 116/92, p. 117/93 | A tone has three digits, and the sender drops the tenths. The examples give `T107` as 107.2 Hz and `C107` as 107.3 Hz. The packet does not have the tenths. | ambiguous | 1 | **[agreed]** If the list of section 4 has a tone whose whole part is the number of the three digits, the value is that tone, with step 0.1. If not, the value is the number of the digits, with step 1. The tone of the station is then from that number up to the next number. |
| <a id="amb.val.tone0"></a>`amb.val.tone0` | p. 114/90 | APRS12c gives `Toff` for a station with no tone. It does not say what the digits `000` mean. | unstated | 2 | **[agreed]** The tone has the effect `computable`, with the number 0. |
| <a id="amb.val.tonetenths"></a>`amb.val.tonetenths` | p. 116/92, p. 117/93 | The sender drops the tenths. Some packets have three digits that are a standard tone in tenths of a hertz, for example `T885`. As a number of hertz, such a value is not a tone below the voice band. | ambiguous | 2 | **[agreed]** If the number of the digits is not the whole part of a tone of the list, and a tenth of it is a tone of the list, the tone has the effect `computable`. Its value is that tone, with step 0.1. |
| <a id="amb.val.tonerange"></a>`amb.val.tonerange` | p. 114/90, p. 117/93 | APRS12c states no range for the three digits of a tone. | unstated | 2 | **[agreed]** A number that is not in the list is a value only from 60 to 300. Outside this range, the tone has the effect `computable`, with the number of the digits and step 1. The rows `amb.val.tone0` and `amb.val.tonetenths` apply first. |

## 8. Reviewed exceptions

None.

## 9. Open items

- The tone in tenths of a hertz is a candidate entry of the divergence
  catalogue (RFC Appendix E).
- Whether an upper-case first letter of `freq.tone` states wide
  modulation. This file gives no flag for it.
- A frequency in the name of an Object.
