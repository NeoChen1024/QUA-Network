# Mic-E

| | |
|---|---|
| Status | Draft. Not frozen. |
| Reference | `APRS12c.pdf` chapter 10, p. 60/42 to p. 74/56, in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, reading rules and tokenizer model: [README](README.md). |

## 1. Scope

APRS12c chapter 10: the six bytes and the SSID of the destination address,
the eight bytes after the data type identifier, and the status text. The
destination address as a TNC2 field belongs to [01-frame.md](01-frame.md);
data extensions and comment items to [02-fields.md](02-fields.md); base-91
comment telemetry to [07-telemetry.md](07-telemetry.md); frequencies to
[09-other.md](09-other.md#7-frequency-specification).

Offsets count from the first byte of the information field, offset 0.
Destination bytes are numbered 1 to 6.

## 2. Recognition

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.dti"></a>`mice.dti` | Data type identifier | 0x60 or 0x27. 0x1C and 0x1D are the Rev 0 beta forms: `obsolete`. | Required | 1 byte | p. 31/17, p. 64/46 |
| <a id="mice.fixed"></a>`mice.fixed` | Fixed part | Offsets 1 to 8 (section 4). A field shorter than 9 bytes gives `syntax` where the first missing byte was expected. | Required | 8 bytes | p. 64/46, p. 65/47 |

The identifier alone makes the packet Mic-E (p. 31/17); a destination
that does not fit section 3 gives its findings on the destination rules.
`mice.fixed` has no token: its parts are one-byte tokens at the level of
`mice.dti`. The symbol code comes before the table identifier (p. 64/46).

## 3. Destination address

Each of the six bytes holds a latitude digit or a blank, and a flag
(p. 61/43, p. 62/44): `'0'`–`'9'` digit, flag 0 (South, +0, East in bytes
4 to 6); `'A'`–`'J'` digit, custom 1 (bytes 1 to 3 only); `'K'` blank,
custom 1 (bytes 1 to 3 only); `'L'` blank, flag 0; `'P'`–`'Y'` digit,
standard 1 (North, +100, West); `'Z'` blank, standard 1.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.dest"></a>`mice.dest` | Destination callsign | Exactly 6 bytes, each from the set of its position. Other than 6 bytes: `syntax` (at the seventh byte when longer, the bytes past the sixth a residue). The parts are tokens one level deeper. | Required | 6 bytes | p. 61/43, p. 62/44 |
| <a id="mice.dest.a"></a>`mice.dest.a` | Byte 1: latitude tens of degrees, bit A | `'0'`–`'9'`, `'A'`–`'L'`, `'P'`–`'Z'`; a blank (`'K'`, `'L'`, `'Z'`) gives `syntax` | Required | 1 byte | p. 40/24, p. 62/44 |
| <a id="mice.dest.b"></a>`mice.dest.b` | Byte 2: latitude degrees, bit B | As byte 1 | Required | 1 byte | p. 40/24, p. 62/44 |
| <a id="mice.dest.c"></a>`mice.dest.c` | Byte 3: tens of minutes, bit C | `'0'`–`'9'`, `'A'`–`'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.ns"></a>`mice.dest.ns` | Byte 4: minutes, North or South | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.lonoff"></a>`mice.dest.lonoff` | Byte 5: tenths of minutes, longitude offset | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44, p. 65/47 |
| <a id="mice.dest.we"></a>`mice.dest.we` | Byte 6: hundredths of minutes, East or West | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.ssid"></a>`mice.dest.ssid` | Destination SSID | 0: the path is in the digipeater field. 1 to 15: a generic path code (p. 64/46), which p. 27/17 calls obsolete; both are accepted, with no finding ([err.dest.ssid](01-frame.md#err.dest.ssid)). `-01` to `-09` are read as 01-frame says ([amb.addr.form](01-frame.md#amb.addr.form)). The token stays `dest.ssid` of 01-frame. | Optional | per [01-frame.md](01-frame.md) | p. 27/17, p. 64/46 |

A byte outside the set of its position, lower case included, gives
`syntax` on the part. On `mice.dest`: a blank followed by a digit gives
`syntax` at the blank (blanks replace digits from byte 6 leftwards, as in
[`lat.amb`](02-fields.md#lat.amb), p. 40/24); degrees over 90, tens of
minutes over 5, or minutes other than zero with 90 degrees give `value`;
a mixture of standard and custom bits gives `unstated`
([amb.mice.dest](#amb.mice.dest)). A fault of the address that no rule
of this section reports stays with `addr.dest` of 01-frame.

## 4. Information field

Offsets 1 to 6 are offset by 28 (p. 64/46). A byte outside 0x1C–0x7F
gives `syntax`; a byte inside it outside the values the encoding tables
use gives `value` (p. 66/48 and p. 67/49 give the valid ranges).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.lon.deg"></a>`mice.lon.deg` | Longitude degrees, d+28 | 0x26–0x7F; 0x1C–0x25 give `value` | Required | 1 byte | p. 65/47, p. 66/48 |
| <a id="mice.lon.min"></a>`mice.lon.min` | Longitude minutes, m+28 | 0x26–0x61; 0x1C–0x25 and 0x62–0x7F give `value` | Required | 1 byte | p. 66/48, p. 67/49 |
| <a id="mice.lon.hun"></a>`mice.lon.hun` | Hundredths of minutes, h+28 | 0x1C–0x7F | Required | 1 byte | p. 67/49 |
| <a id="mice.sp"></a>`mice.sp` | Speed, hundreds and tens of knots, SP+28 | 0x1C–0x7F; two equally valid codings below 200 knots | Required | 1 byte | p. 67/49, p. 68/50 |
| <a id="mice.dc"></a>`mice.dc` | Speed units and course hundreds, DC+28 | 0x1C–0x7D; with n = byte − 0x1C, n mod 10 of 8 or 9 gives `value`. Two equally valid codings. A course (from `mice.dc` and `mice.se`) over 360 gives `value` here. | Required | 1 byte | p. 67/49, p. 69/51, p. 70/52 |
| <a id="mice.se"></a>`mice.se` | Course tens and units, SE+28 | 0x1C–0x7F | Required | 1 byte | p. 70/52 |
| <a id="mice.sym.code"></a>`mice.sym.code` | Symbol code | As [`sym.code`](02-fields.md#sym.code) | Required | 1 byte | p. 64/46 |
| <a id="mice.sym.table"></a>`mice.sym.table` | Symbol table identifier | As [`sym.table`](02-fields.md#sym.table) of an uncompressed position: `'a'`–`'j'` are for compressed positions only and give `syntax` | Required | 1 byte | p. 64/46, p. 125/101 |

## 5. Status text

From offset 9 to the end of the information field: either the obsolete
telemetry or the status text (p. 60/42, p. 64/46). The status text holds,
all optional: a device prefix, an altitude, a locator, a data extension,
free text, base-91 telemetry, a DAO and a device suffix (p. 72/54 to
p. 74/56, p. 88/68).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.status"></a>`mice.status` | Status text | Offset 9 to the end; no length limit. Free text is [`cmt.text`](02-fields.md#cmt.text). The parts below are tokens one level deeper. | Optional | End of field | p. 72/54 |
| <a id="mice.tlm"></a>`mice.tlm` | Obsolete telemetry | 0x1D and 5 bytes of any value, or 0x60 and 4, or 0x27 and 10, hexadecimal digits. `obsolete`. A 0x1D block cut short gives `syntax` at the end. | Optional | 6, 5 or 11 bytes | p. 72/54 |
| <a id="mice.type.prefix"></a>`mice.type.prefix` | Device prefix | One byte at offset 9: `'>'`, `']'`, 0x60 or 0x27 | Optional | 1 byte | p. 73/55 |
| <a id="mice.alt"></a>`mice.alt` | Altitude | Three [`b91.digit`](02-fields.md#b91.digit) bytes and `'}'`. Advised first after the prefix: elsewhere `discouraged`. At the first spot, a `'}'` three bytes on fixes the token, and a byte that is not a base-91 digit gives `syntax`. | Optional | The `'}'` | p. 74/56 |
| <a id="mice.grid"></a>`mice.grid` | Maidenhead locator | [`grid.loc`](03-position.md#grid.loc), 4 or 6 bytes, then `'/'` `'G'`; then SP when plain text follows, which belongs to the token. Letters are sent in upper case: lower case, or a letter outside its Maidenhead range, gives `syntax`; so does text after `/G` without the SP. | Optional | The `'G'`, or the SP after it | p. 42/26, p. 73/55, p. 152/128 |
| <a id="mice.type.suffix"></a>`mice.type.suffix` | Device suffix | The raw last byte after a Kenwood prefix when the pair is in the `micelegacy` list of `3rdparty/aprs-deviceid/tocalls.yaml` at commit `c50d026`; the raw last two bytes after 0x60 or 0x27, checked against the `mice` list there: an unlisted suffix gives `unstated`. | Optional | End of field | p. 73/55, p. 88/68 |

The parts are read in this order: the telemetry or prefix at offset 9;
an altitude directly after it; the suffix from the end; a locator, then
a data extension ([`ext.csespd`](02-fields.md#ext.csespd),
[`ext.phg`](02-fields.md#ext.phg), [`ext.phgr`](02-fields.md#ext.phgr),
[`ext.rng`](02-fields.md#ext.rng), [`ext.dfs`](02-fields.md#ext.dfs)), at
the start of what is left; the free text up to the suffix. In the free
text the comment items ([`cmt.alt`](02-fields.md#cmt.alt),
[`cmt.dao`](02-fields.md#cmt.dao),
[`cmt.noarchive`](02-fields.md#cmt.noarchive)), base-91 telemetry
[`tlm.b91`](07-telemetry.md#tlm.b91) before the suffix (p. 88/68), a frequency at its start
([09 section 7](09-other.md#7-frequency-specification)), and, where none
stood at the start, the first locator, altitude and data extension are
tokens one level below `cmt.text`
([amb.mice.grid](#amb.mice.grid), [amb.mice.alt](#amb.mice.alt),
[amb.mice.extension](#amb.mice.extension)). After `mice.tlm` nothing is
looked for ([amb.mice.tlm](#amb.mice.tlm)).

## 6. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.mice.dest"></a>`amb.mice.dest` | p. 63/45 | Bits A to C mixing standard and custom ones give a comment type the page calls "unknown", with no meaning. | unstated | 2 | `unstated` on `mice.dest` at the first of bytes 1 to 3 whose bit is of the other kind. |
| <a id="amb.mice.byte9"></a>`amb.mice.byte9` | p. 72/54, p. 73/55, p. 157/133 | 0x60 and 0x27 at offset 9 are telemetry flags on one page and device prefixes on the next ([err.mice.status](#err.mice.status)). | ambiguous | 3, 4 | A flag followed by 4 (0x60) or 10 (0x27) hexadecimal digits is `mice.tlm`, the more specific form, with `obsolete`, and `ambiguous` on `mice.tlm` at offset 9 where the prefix reading gives no `syntax` or `value`; otherwise the byte is `mice.type.prefix`. |
| <a id="amb.mice.tlm"></a>`amb.mice.tlm` | p. 60/42, p. 64/46, p. 72/54 | Telemetry and status text are alternatives; nothing is said of bytes after the telemetry. | unstated | 2 | `unstated` on `mice.tlm` at the first byte after the block; the bytes stay in `mice.status` and nothing is looked for in them. |
| <a id="amb.mice.suffix"></a>`amb.mice.suffix` | p. 73/55, p. 88/68 | Whether a suffix must follow a 0x60 or 0x27 prefix; a Kenwood suffix byte can also end text; a trailing CR or SP. | ambiguous | 1, 4, 5 | The raw last bytes, nothing stripped. With fewer than two bytes after the prefix, or two that would cut a UTF-8 character of a text that is well formed as a whole, there is no suffix: `unstated` on `mice.type.suffix` at the end. A listed Kenwood pair is the suffix, with no finding, as every instance carries that ambiguity. |
| <a id="amb.mice.pipe"></a>`amb.mice.pipe` | p. 73/55, p. 88/68 | A Byonics suffix starts with `'|'`, the telemetry delimiter. | ambiguous | 1 | The suffix stands at the end and the telemetry before it (p. 88/68), so the suffix is taken first. No finding. |
| <a id="amb.mice.alt"></a>`amb.mice.alt` | p. 74/56, p. 154/130 | The status text "can contain" the altitude, which "should be" first after the type byte. | ambiguous | 1, 2 | The status text is the place. With none at the start, the first match in the free text is `mice.alt` with `discouraged`; later matches are text. |
| <a id="amb.mice.grid"></a>`amb.mice.grid` | p. 42/26, p. 73/55, p. 152/128 | Only six-character locators followed by `/G` are shown; length, case, other symbols and place are not stated. | ambiguous | 1, 2, 5 | The status text is the place: the first 4- or 6-byte locator followed by `/G`. Lower case gives `syntax` (sent in upper case, p. 152/128). A locator followed by another symbol is text, with no finding. |
| <a id="amb.mice.extension"></a>`amb.mice.extension` | p. 33/19, p. 34/20, p. 72/54, p. 157/133 | The status text may hold "any normal Position comment field"; whether at the spot a position report gives it or anywhere. A "standard APRS-formatted position" is allowed with no shape or place. | ambiguous | 2, 4, 1 | The status text is the place, so no `ambiguous`: a form of step 3, course and speed included, at the start of the free text, a token beside `cmt.text`; with none there, the first later run, one level below it. At the start, and later for the forms its keyword announces (`PHG`, `RNG`, `DFS`), the run is judged as that form, with its findings; a later course and speed, marked by its shape only, is taken only where it gives no `syntax` or `value` finding. Later runs are text. The embedded position is not looked for. |
| <a id="amb.mice.transport"></a>`amb.mice.transport` | p. 74/56 | A conversion for networks that do not keep binary data is required but not given. | unstated | 2 | Bytes from APRS-IS are read raw; no escape form is recognised. No finding. |
| <a id="err.mice.example"></a>`err.mice.example` | p. 70/52, p. 71/53 | The worked example subtracts 80 and 4 where the steps subtract 800 and 400. | conflict | 3 | No speed or course is computed: no effect. |
| <a id="err.mice.sptable"></a>`err.mice.sptable` | p. 68/50, p. 70/52 | The SP table labels 0x3A and 0x3B as 300–310 and 310–320 knots. | conflict | 3 | No effect on bytes. |
| <a id="err.mice.setable"></a>`err.mice.setable` | p. 70/52 | The SE table carries the headings of the minutes table. | conflict | 3 | No effect on bytes. |
| <a id="err.mice.status"></a>`err.mice.status` | p. 72/54, p. 73/55, p. 157/133 | The status text must not start with 0x60 or 0x27, yet these are the prefixes of other makers' devices. | conflict | 3 | Both accepted; where they divide bytes differently, [amb.mice.byte9](#amb.mice.byte9). |
| <a id="err.mice.binary"></a>`err.mice.binary` | p. 64/46, p. 72/54 | The field "never" uses full 8-bit values, yet the 0x1D telemetry carries five. | conflict | 3 | Any byte in the five channels of a 0x1D `mice.tlm`; 0x1C–0x7F at offsets 1 to 6. |

## 7. Reviewed exceptions

None.

## 8. Open items

- How decoders differ on the rows above is for differential testing
  (RFC Appendix E).
