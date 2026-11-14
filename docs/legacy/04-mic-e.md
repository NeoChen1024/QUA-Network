# Mic-E

| | |
|---|---|
| Status | Draft. Not frozen. |
| Reference | `APRS12c.pdf` chapter 10, p. 60/42 to p. 74/56, in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers APRS12c chapter 10:

- the six bytes and the SSID of the destination address;
- the eight bytes after the data type identifier;
- the status text.

Other files cover related fields:

- [01-frame.md](01-frame.md): the destination address as a TNC2 field;
- [02-fields.md](02-fields.md): data extensions and the fields found in
  comments;
- [07-telemetry.md](07-telemetry.md): base-91 comment telemetry;
- [09-other.md](09-other.md#7-frequency-specification): frequencies.

Offsets count from the first byte of the information field, which is
offset 0. The bytes of the destination are numbered 1 to 6.

## 2. Recognition

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.dti"></a>`mice.dti` | Data type identifier | 0x60 or 0x27. 0x1C and 0x1D are the Rev 0 beta formats: `obsolete`. | Required | 1 byte | p. 31/17, p. 64/46 |
| <a id="mice.fixed"></a>`mice.fixed` | Fixed part | Offsets 1 to 8 (section 4). An information field shorter than 9 bytes gives `syntax` where the first missing byte was expected. | Required | 8 bytes | p. 64/46, p. 65/47 |

The identifier alone makes the packet Mic-E (p. 31/17). If the
destination does not match section 3, it gives its findings on the
destination rules. `mice.fixed` has no token. The fields in it are
one-byte tokens at the level of `mice.dti`. The symbol code comes before
the table identifier (p. 64/46).

## 3. Destination address

Each of the six bytes contains a latitude digit or a blank, and a flag
(p. 61/43, p. 62/44):

- `'0'`–`'9'`: a digit, flag 0 (South, +0, East in bytes 4 to 6).
- `'A'`–`'J'`: a digit, custom 1 (bytes 1 to 3 only).
- `'K'`: a blank, custom 1 (bytes 1 to 3 only).
- `'L'`: a blank, flag 0.
- `'P'`–`'Y'`: a digit, standard 1 (North, +100, West).
- `'Z'`: a blank, standard 1.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.dest"></a>`mice.dest` | Destination callsign | Exactly 6 bytes, each from the set of its place. A length other than 6 bytes gives `syntax`. If the callsign is longer, the finding is at the seventh byte, and the bytes past the sixth are residue. The fields in it are tokens one level below `mice.dest`. | Required | 6 bytes | p. 61/43, p. 62/44 |
| <a id="mice.dest.a"></a>`mice.dest.a` | Byte 1: latitude tens of degrees, bit A | `'0'`–`'9'`, `'A'`–`'L'`, `'P'`–`'Z'`. A blank (`'K'`, `'L'`, `'Z'`) gives `syntax`. | Required | 1 byte | p. 40/24, p. 62/44 |
| <a id="mice.dest.b"></a>`mice.dest.b` | Byte 2: latitude degrees, bit B | As byte 1 | Required | 1 byte | p. 40/24, p. 62/44 |
| <a id="mice.dest.c"></a>`mice.dest.c` | Byte 3: tens of minutes, bit C | `'0'`–`'9'`, `'A'`–`'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.ns"></a>`mice.dest.ns` | Byte 4: minutes, North or South | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.lonoff"></a>`mice.dest.lonoff` | Byte 5: tenths of minutes, longitude offset | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44, p. 65/47 |
| <a id="mice.dest.we"></a>`mice.dest.we` | Byte 6: hundredths of minutes, East or West | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.ssid"></a>`mice.dest.ssid` | Destination SSID | 0: the path is in the digipeater field. 1 to 15: a generic path code (p. 64/46). APRS12c also calls this code obsolete (p. 27/17). The tokenizer accepts both values, with no finding ([err.dest.ssid](01-frame.md#err.dest.ssid)). The tokenizer reads `-01` to `-09` as 01-frame says ([amb.addr.form](01-frame.md#amb.addr.form)). The token stays `dest.ssid` of 01-frame. | Optional | per [01-frame.md](01-frame.md) | p. 27/17, p. 64/46 |

A byte outside the set of its place gives `syntax` on its field. This
includes lower case. These findings are on `mice.dest`:

- A blank followed by a digit gives `syntax` at the blank. Blanks replace
  digits from byte 6 to the left, as in [`lat.amb`](02-fields.md#lat.amb)
  (p. 40/24).
- Degrees over 90, tens of minutes over 5, or minutes other than zero
  with 90 degrees give `value`.
- A mix of standard and custom bits gives `unstated`
  ([amb.mice.dest](#amb.mice.dest)).

If no rule of this section reports a fault of the address, the fault
stays with `addr.dest` of 01-frame.

## 4. Information field

The bytes at offsets 1 to 6 have an offset of 28 (p. 64/46). A byte
outside 0x1C–0x7F gives `syntax`. A byte inside this range but outside
the values that the encoding tables use gives `value`. APRS12c specifies
the valid ranges (p. 66/48, p. 67/49).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.lon.deg"></a>`mice.lon.deg` | Longitude degrees, d+28 | 0x26–0x7F. 0x1C–0x25 give `value`. | Required | 1 byte | p. 65/47, p. 66/48 |
| <a id="mice.lon.min"></a>`mice.lon.min` | Longitude minutes, m+28 | 0x26–0x61. 0x1C–0x25 and 0x62–0x7F give `value`. | Required | 1 byte | p. 66/48, p. 67/49 |
| <a id="mice.lon.hun"></a>`mice.lon.hun` | Hundredths of minutes, h+28 | 0x1C–0x7F | Required | 1 byte | p. 67/49 |
| <a id="mice.sp"></a>`mice.sp` | Speed, hundreds and tens of knots, SP+28 | 0x1C–0x7F. Below 200 knots, two codings are equally valid. | Required | 1 byte | p. 67/49, p. 68/50 |
| <a id="mice.dc"></a>`mice.dc` | Speed units and course hundreds, DC+28 | 0x1C–0x7D. With n = byte − 0x1C, an n mod 10 of 8 or 9 gives `value`. Two codings are equally valid. A course (from `mice.dc` and `mice.se`) over 360 gives `value` here. | Required | 1 byte | p. 67/49, p. 69/51, p. 70/52 |
| <a id="mice.se"></a>`mice.se` | Course tens and units, SE+28 | 0x1C–0x7F | Required | 1 byte | p. 70/52 |
| <a id="mice.sym.code"></a>`mice.sym.code` | Symbol code | As [`sym.code`](02-fields.md#sym.code) | Required | 1 byte | p. 64/46 |
| <a id="mice.sym.table"></a>`mice.sym.table` | Symbol table identifier | As [`sym.table`](02-fields.md#sym.table) of an uncompressed position: `'a'`–`'j'` are for compressed positions only and give `syntax` | Required | 1 byte | p. 64/46, p. 125/101 |

## 5. Status text

From offset 9 to the end of the information field, the bytes are the
obsolete telemetry or the status text (p. 60/42, p. 64/46). The status
text can contain these fields, all optional (p. 72/54 to p. 74/56,
p. 88/68):

- a device prefix;
- an altitude;
- a locator;
- a data extension;
- text;
- base-91 telemetry;
- a DAO;
- a device suffix.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.status"></a>`mice.status` | Status text | Offset 9 to the end, with no length limit. The text in it is [`cmt.text`](02-fields.md#cmt.text). The fields below are tokens one level below `mice.status`. | Optional | End of field | p. 72/54 |
| <a id="mice.tlm"></a>`mice.tlm` | Obsolete telemetry | 0x1D and 5 bytes of any value, or 0x60 and 4 hexadecimal digits, or 0x27 and 10 hexadecimal digits. `obsolete`. If a 0x1D block is cut short, it gives `syntax` at the end. | Optional | 6, 5 or 11 bytes | p. 72/54 |
| <a id="mice.type.prefix"></a>`mice.type.prefix` | Device prefix | One byte at offset 9: `'>'`, `']'`, 0x60 or 0x27 | Optional | 1 byte | p. 73/55 |
| <a id="mice.alt"></a>`mice.alt` | Altitude | Three [`b91.digit`](02-fields.md#b91.digit) bytes and `'}'`. APRS12c advises the altitude first after the prefix. In other places, the altitude gives `discouraged`. At the first place, a `'}'` three bytes later makes the four bytes a token. Then a byte that is not a base-91 digit gives `syntax`. | Optional | The `'}'` | p. 74/56 |
| <a id="mice.grid"></a>`mice.grid` | Maidenhead locator | [`grid.loc`](03-position.md#grid.loc), 4 or 6 bytes, then `'/'` `'G'`. If text follows, a SP follows the `'G'`, and the SP belongs to the token. The sender sends the letters in upper case. Lower case, or a letter outside its Maidenhead range, gives `syntax`. Text after `/G` without the SP also gives `syntax`. | Optional | The `'G'`, or the SP after it | p. 42/26, p. 73/55, p. 152/128 |
| <a id="mice.type.suffix"></a>`mice.type.suffix` | Device suffix | After a Kenwood prefix: the raw last byte, if the pair is in the `micelegacy` list of `3rdparty/aprs-deviceid/tocalls.yaml` at commit `c50d026`. After 0x60 or 0x27: the raw last two bytes, checked against the `mice` list of the same file. A suffix that is not in the list gives `unstated`. | Optional | End of field | p. 73/55, p. 88/68 |

The tokenizer reads the fields in this order:

1. the telemetry or the prefix at offset 9;
2. an altitude directly after it;
3. the suffix, from the end;
4. a locator, then a data extension
   ([`ext.csespd`](02-fields.md#ext.csespd),
   [`ext.phg`](02-fields.md#ext.phg), [`ext.phgr`](02-fields.md#ext.phgr),
   [`ext.rng`](02-fields.md#ext.rng), [`ext.dfs`](02-fields.md#ext.dfs)),
   at the start of the remaining bytes;
5. the text, up to the suffix.

In the text, these fields are tokens one level below `cmt.text`:

- the comment fields [`cmt.alt`](02-fields.md#cmt.alt),
  [`cmt.dao`](02-fields.md#cmt.dao) and
  [`cmt.noarchive`](02-fields.md#cmt.noarchive);
- base-91 telemetry [`tlm.b91`](07-telemetry.md#tlm.b91) before the
  suffix (p. 88/68);
- a frequency at the start of the text
  ([09 section 7](09-other.md#7-frequency-specification));
- the first locator, the first altitude and the first data extension.
  Each of these is a token only if there is none of its kind at the
  start ([amb.mice.grid](#amb.mice.grid), [amb.mice.alt](#amb.mice.alt),
  [amb.mice.extension](#amb.mice.extension)).

After `mice.tlm`, the tokenizer looks for nothing
([amb.mice.tlm](#amb.mice.tlm)).

## 6. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.mice.dest"></a>`amb.mice.dest` | p. 63/45 | If bits A to C mix standard and custom bits, they give a comment type that the page calls "unknown". This type has no meaning. | unstated | 2 | `unstated` on `mice.dest`, at the first of bytes 1 to 3 whose bit is of the other kind. |
| <a id="amb.mice.byte9"></a>`amb.mice.byte9` | p. 72/54, p. 73/55, p. 157/133 | 0x60 and 0x27 at offset 9 are telemetry flags on one page and device prefixes on the next page ([err.mice.status](#err.mice.status)). | ambiguous | 3, 4 | A flag followed by 4 (0x60) or 10 (0x27) hexadecimal digits is `mice.tlm`, the stricter format, with `obsolete`. If the prefix interpretation gives no `syntax` or `value`, `mice.tlm` also gives `ambiguous` at offset 9. In all other cases, the byte is `mice.type.prefix`. |
| <a id="amb.mice.tlm"></a>`amb.mice.tlm` | p. 60/42, p. 64/46, p. 72/54 | Telemetry and status text are alternatives. APRS12c says nothing about bytes after the telemetry. | unstated | 2 | `unstated` on `mice.tlm` at the first byte after the block. The bytes stay in `mice.status`, and the tokenizer looks for nothing in them. |
| <a id="amb.mice.suffix"></a>`amb.mice.suffix` | p. 73/55, p. 88/68 | Whether a 0x60 or 0x27 prefix requires a suffix. The byte of a Kenwood suffix can also be the last byte of text. A CR or SP at the end. | ambiguous | 1, 4, 5 | The raw last bytes, with nothing removed. There is no suffix if fewer than two bytes follow the prefix. There is also no suffix if the two bytes would cut a UTF-8 character of a text that is well formed as a whole. In both cases, `mice.type.suffix` gives `unstated` at the end. A Kenwood pair in the list is the suffix, with no finding, because every packet with such a suffix has the same ambiguity. |
| <a id="amb.mice.pipe"></a>`amb.mice.pipe` | p. 73/55, p. 88/68 | A Byonics suffix starts with `'|'`, the telemetry delimiter. | ambiguous | 1 | The suffix is at the end, and the telemetry is before it (p. 88/68). Thus the tokenizer reads the suffix first. No finding. |
| <a id="amb.mice.alt"></a>`amb.mice.alt` | p. 74/56, p. 154/130 | The status text "can contain" the altitude, which "should be" first after the type byte. | ambiguous | 1, 2 | The status text is the place. If no altitude is at the start, the first match in the text is `mice.alt` with `discouraged`. Later matches are text. |
| <a id="amb.mice.grid"></a>`amb.mice.grid` | p. 42/26, p. 73/55, p. 152/128 | APRS12c shows only locators of six characters followed by `/G`. It does not specify the length, the case, other symbols or the place. | ambiguous | 1, 2, 5 | The status text is the place: the first locator of 4 or 6 bytes followed by `/G`. Lower case gives `syntax` (the sender sends the letters in upper case, p. 152/128). A locator followed by another symbol is text, with no finding. |
| <a id="amb.mice.extension"></a>`amb.mice.extension` | p. 33/19, p. 34/20, p. 72/54, p. 157/133 | The status text can contain "any normal Position comment field". APRS12c does not say whether this field is at the place where a position report has it, or anywhere. It permits a "standard APRS-formatted position", but specifies no format and no place for it. | ambiguous | 2, 4, 1 | The status text is the place, so there is no `ambiguous`. The tokenizer reads a data extension as the list below the table says. |
| <a id="amb.mice.transport"></a>`amb.mice.transport` | p. 74/56 | APRS12c requires a conversion for networks that do not keep binary data, but does not specify it. | unstated | 2 | The tokenizer reads bytes from APRS-IS raw. It recognises no escape format. No finding. |
| <a id="err.mice.example"></a>`err.mice.example` | p. 70/52, p. 71/53 | The worked example subtracts 80 and 4. The steps subtract 800 and 400. | conflict | 3 | The tokenizer computes no speed or course: no effect. |
| <a id="err.mice.sptable"></a>`err.mice.sptable` | p. 68/50, p. 70/52 | The SP table labels 0x3A and 0x3B as 300–310 and 310–320 knots. | conflict | 3 | No effect on bytes. |
| <a id="err.mice.setable"></a>`err.mice.setable` | p. 70/52 | The SE table has the headings of the minutes table. | conflict | 3 | No effect on bytes. |
| <a id="err.mice.status"></a>`err.mice.status` | p. 72/54, p. 73/55, p. 157/133 | APRS12c does not permit a status text that starts with 0x60 or 0x27. But these bytes are the prefixes of devices of other makers. | conflict | 3 | The tokenizer accepts both sides. Where they divide bytes differently, see [amb.mice.byte9](#amb.mice.byte9). |
| <a id="err.mice.binary"></a>`err.mice.binary` | p. 64/46, p. 72/54 | The field "never" uses full 8-bit values. But the 0x1D telemetry contains five. | conflict | 3 | Any byte in the five channels of a 0x1D `mice.tlm`. 0x1C–0x7F at offsets 1 to 6. |

For [amb.mice.extension](#amb.mice.extension), the tokenizer reads a data
extension in the status text as follows:

- At the start of the text, a format of step 3, course and speed
  included, is a token at the same level as `cmt.text`. The tokenizer
  reads the run as that format, with its findings.
- If there is none there, the tokenizer uses the first later run, one
  level below `cmt.text`.
- Later in the text, the tokenizer reads a run of a format with a keyword
  (`PHG`, `RNG`, `DFS`) as that format, with its findings.
- A later course and speed has no keyword, only its format. The tokenizer
  uses it only if it gives no `syntax` or `value` finding.
- Runs after the first run are text.
- The tokenizer does not look for the embedded position.

## 7. Reviewed exceptions

None.

## 8. Open items

- Differential testing finds how decoders differ on the rows above (RFC
  Appendix E).
