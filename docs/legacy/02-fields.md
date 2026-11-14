# Fields shared by several formats

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers the fields that several formats use:

- timestamps;
- uncompressed latitude and longitude, with position ambiguity;
- the symbol;
- base-91 digits;
- the compressed position block;
- the data extensions;
- the comment and the fields found in it.

The rule prefixes are `time`, `lat`, `lon`, `sym`, `b91`, `cmp`, `ext`
and `cmt`. The format files ([03](03-position.md) to [09](09-other.md))
say where each field is and whether it is required.

A field of fixed length is one token of that length, also when its bytes
do not match. If a field is cut short, its token contains only the bytes
that are present. Offsets inside a field count from 0.

## 2. Timestamps

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="time.dhm"></a>`time.dhm` | Day, hour, minute | Six digits: day of month `01`–`31`, hour `00`–`23`, minute `00`–`59`. Then `'z'` (UTC) or `'/'` (local time). `'/'` gives `discouraged`: APRS12c recommends only zulu time on the air. | Format file | Fixed, 7 bytes | p. 38/22 |
| <a id="time.hms"></a>`time.hms` | Hour, minute, second | Six digits: hour `00`–`23`, minute and second `00`–`59`. Then `'h'`. UTC. | Format file | Fixed, 7 bytes | p. 38/22 |
| <a id="time.mdhm"></a>`time.mdhm` | Month, day, hour, minute | Eight digits: month `01`–`12`, day `01`–`31`, hour, minute. UTC, with no indicator. Only in positionless weather reports. | [06](06-weather.md) | Fixed, 8 bytes | p. 38/22 |

Some formats permit both timestamp formats of seven bytes ("DHM / HMS",
p. 50/32). In these formats, the byte at offset 6 selects the format:

- `'z'` or `'/'` gives `time.dhm`.
- `'h'` gives `time.hms`.
- Any other byte, `'Z'` and `'H'` included, gives a `time.dhm` token with
  `syntax` at offset 6.

A byte that is not a digit in offsets 0–5 gives `syntax`. A value outside
its range gives `value`. The ranges of the hour, the minute and the
second are those of the 24-hour clock (README rule 1). The tokenizer
checks each value when its two digits are present. It does not check a
day against the length of its month.

## 3. Latitude and longitude

### 3.1 Fields

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="lat"></a>`lat` | Latitude | Offsets 0–1: degrees `00`–`90`. Offsets 2–3: minutes. Offset 4: `'.'`. Offsets 5–6: hundredths. Offset 7: `'N'` or `'S'` (upper case). Minutes up to 59, and no minutes at 90 degrees. `SP` only under `lat.amb`. | Format file | Fixed, 8 bytes | p. 39/23 |
| <a id="lon"></a>`lon` | Longitude | Offsets 0–2: degrees `000`–`180`. Offsets 3–4: minutes. Offset 5: `'.'`. Offsets 6–7: hundredths. Offset 8: `'E'` or `'W'` (upper case). Minutes up to 59, and no minutes at 180 degrees. `SP` only under `lon.amb`. | Format file | Fixed, 9 bytes | p. 39/23, p. 40/24 |

A byte that does not match the format gives one `syntax` finding, at the
first such byte. These bytes give `value` (README rule 1):

- degrees above 90 or 180;
- a digit `'6'`–`'9'` in the tens of minutes;
- a minute digit that is not zero at 90 or 180 degrees.

The tokenizer checks these values on the digits that are present.

### 3.2 Position ambiguity

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="lat.amb"></a>`lat.amb` | Ambiguity level | A check on `lat`, with no token. `SP` replaces the minute and hundredths digits progressively from the right: offsets 6, 5, 3, 2 in that order. The level, 0 to 4, is the number of `SP` counted from offset 6. If a `SP` is at one of these offsets and a digit is at an offset earlier in that order, the `SP` gives `syntax`. | No | — | p. 40/24 |
| <a id="lon.amb"></a>`lon.amb` | Longitude blanks | A check on `lon`, with no token. The level of the latitude applies to the longitude. APRS12c permits blanks in the longitude but does not require them. The offsets are 7, 6, 4, 3, in that order. The level covers the first *level* offsets of that order. A `SP` that the level covers gives no finding. A `SP` that the level does not cover gives `unstated` ([amb.lat.ambiguity](#amb.lat.ambiguity)). | No | — | p. 40/24 |

### 3.3 Null position

APRS12c specifies a null position for a station without a position:
`0000.00N` and `00000.00W`. With this position, the symbol "should" be
`\.` (p. 42/26). The tokenizer reads these bytes as ordinary `lat`, `lon`
and symbol tokens, with no finding ([amb.lat.null](#amb.lat.null)).

## 4. Symbol table and code

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="sym.table"></a>`sym.table` | Symbol table identifier, uncompressed | `'/'` (primary), `'\'` (alternate), `'0'`–`'9'` or `'A'`–`'Z'` (alternate with that overlay). `'a'`–`'j'` are for the compressed format only. Other bytes give `syntax`. | Format file | Fixed, 1 byte | p. 40/24, p. 125/101 |
| <a id="sym.code"></a>`sym.code` | Symbol code | `'!'`–`'~'`: the codes of the tables of Appendix 2. Other bytes give `syntax`. | Format file | Fixed, 1 byte | p. 139/115 to p. 141/117 |

The tokenizer does not check whether a symbol permits an overlay
([amb.sym.overlay](#amb.sym.overlay)). It also does not check which of
several symbols in one packet has priority (p. 127/103). [01](01-frame.md)
reads the symbols in the destination address. [04](04-mic-e.md) reads the
Mic-E symbol.

## 5. Base-91 digits

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="b91.digit"></a>`b91.digit` | Base-91 digit | One byte `'!'`–`'\|'` (`0x21`–`0x7C`). Value: byte − 33. A number has its most significant digit first ([err.b91.range](#err.b91.range)). This is a rule, not a token. If a field uses this rule, a byte outside the set gives `syntax` on the ID of that field. In a base-91 telemetry block, `'\|'` is the delimiter ([07 section 3](07-telemetry.md#3-base-91-comment-telemetry)). | — | Fixed, 1 byte | p. 34/20, p. 55/37, p. 88/68 |

## 6. Compressed position block

### 6.1 Uncompressed or compressed format

Some formats permit either position format. In these formats, the first
byte of the position selects the format (p. 55/37, p. 125/101):

- A digit starts an uncompressed position (`lat`, `sym.table`, `lon`,
  `sym.code`).
- A byte of the `cmp.table` set starts a compressed block.
- Any other byte gives `syntax` on the selector rule of the format, for
  example [`pos.form`](03-position.md#pos.form). The rest of the bytes are
  residue.

### 6.2 Fields

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmp.block"></a>`cmp.block` | Compressed position | Table (1), latitude (4), longitude (4), code (1), `cs` (2), `T` (1). These fields are tokens one level below the block. The block is in place of the uncompressed position and its extension. | Format file | Fixed, 13 bytes | p. 55/37, p. 59/41 |
| <a id="cmp.table"></a>`cmp.table` | Symbol table identifier, compressed | `'/'`, `'\'`, `'A'`–`'Z'`, or `'a'`–`'j'` for overlay digits 0–9. Never a digit. | Yes | Fixed, 1 byte | p. 55/37, p. 125/101 |
| <a id="cmp.lat"></a>`cmp.lat` | Latitude | 4 base-91 digits, 380926 × (90 − latitude). A value above 68566680 (beyond 90 S) gives `value`. | Yes | Fixed, 4 bytes | p. 56/38 |
| <a id="cmp.lon"></a>`cmp.lon` | Longitude | 4 base-91 digits, 190463 × (180 + longitude). A value above 68566680 (beyond 180 E) gives `value`. | Yes | Fixed, 4 bytes | p. 56/38 |
| <a id="cmp.code"></a>`cmp.code` | Symbol code | As [`sym.code`](#sym.code). | Yes | Fixed, 1 byte | p. 55/37 |
| <a id="cmp.cs"></a>`cmp.cs` | Course and speed, range, altitude or wind | `c` then `s`, read as in 6.3. The token ID is the ID of the step that applies. | Yes | Fixed, 2 bytes | p. 56/38 to p. 58/40 |
| <a id="cmp.t"></a>`cmp.t` | Compression type | Read as in 6.4. | Yes | Fixed, 1 byte | p. 57/39 |

If the end of the information field cuts a block short, the tokenizer
reads it as follows:

- The block is a `cmp.block` token over the bytes that are present.
- Each field that is present is a token over its bytes.
- The first missing byte gives `syntax` where it was expected.

If `T` is missing, the step of 6.3 is unknown. Then `c` fails only when
it is neither `SP` nor a base-91 digit.

### 6.3 Reading the cs bytes

The tokenizer uses the first step whose condition is true.

| Step | Condition | Token ID | Further bytes | Source |
|---|---|---|---|---|
| 1 | `c` is `SP` | <a id="cmp.cs.none"></a>`cmp.cs.none` | `s` and `T` are fillers: any byte, ignored ([amb.cmp.filler](#amb.cmp.filler)) | p. 56/38, p. 59/41 |
| 2 | Bits 4–3 of `T` − 33 are `1 0` (GGA) | <a id="cmp.cs.alt"></a>`cmp.cs.alt` | `c` and `s` are base-91 ([amb.cmp.cs](#amb.cmp.cs)) | p. 58/40 |
| 3 | The packet is a weather report ([06](06-weather.md)), and `c` is in `'!'`–`'z'` | <a id="cmp.cs.wind"></a>`cmp.cs.wind` | `s` is base-91 | p. 86/66 |
| 4 | `c` is in `'!'`–`'z'` | <a id="cmp.cs.crs"></a>`cmp.cs.crs` | `s` is base-91 | p. 56/38 |
| 5 | `c` is `'{'` | <a id="cmp.cs.rng"></a>`cmp.cs.rng` | `s` is base-91 | p. 57/39 |
| 6 | No other step applies | `cmp.cs` | `syntax` at `c` | — |

The `cs` token gives a maximum of one `syntax` finding. The finding is at
the first of `c` and `s` that fails.

### 6.4 The T byte

If `c` is not `SP`, `T` is a base-91 digit. If it is not a base-91 digit,
it gives `syntax`. APRS12c does not use bits 7–6 of `T` − 33, and they
are 0. Thus a `T` from `'a'` to `'|'` gives `value`. The origin codes
that APRS12c marks "tbd" give no finding (p. 57/39).

### 6.5 What follows the block

The format of the packet sets what follows the block. Usually it is a
comment.

A run of bytes directly after `T` can match a format of step 3 of 7.1. If
it matches with no `syntax` or `value` finding of that format, the
tokenizer reads it as that extension:

- The extension gives `ambiguous` at its first byte.
- The comment after the extension has a limit of 36 characters
  ([amb.ext.compressed](#amb.ext.compressed)).

If the symbol is `\l`, the tokenizer tries only step 1 instead, and no
format of step 3. Seven bytes that match `ext.area` are that descriptor,
with `ambiguous` at their first byte. The tokenizer does not read bearing
and NRQ after the block.

## 7. Data extensions

### 7.1 The extension slot

The slot is the bytes directly after the symbol code of an uncompressed
position (p. 45/27). Only the formats whose files provide a slot have
one. The tokenizer tries the formats in this order and uses the first
that matches:

1. Symbol `\l`: [`ext.area`](#ext.area). In a position report, see
   [amb.pos.ext](03-position.md#amb.pos.ext). In an Object or an Item,
   [05](05-object-item.md) says what the slot contains.
2. A weather report: [`ext.dirspd`](#ext.dirspd) only (06).
3. All other cases: [`ext.csespd`](#ext.csespd), [`ext.phgr`](#ext.phgr),
   [`ext.phg`](#ext.phg), [`ext.rng`](#ext.rng), [`ext.dfs`](#ext.dfs).

Bytes that match no format are the start of the comment, with no finding
([amb.ext.slot](#amb.ext.slot)). A slot contains one extension. The
bytes after it are comment text ([amb.ext.count](#amb.ext.count)). The
exceptions are bearing and NRQ (7.4) and storm data (06). Upper case is
significant: `phg`, `rng` and `dfs` match nothing.

### 7.2 Fields

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="ext.csespd"></a>`ext.csespd` | Course and speed | Course (3), `'/'`, speed (3). Each field is three digits, `'...'` or three `SP` ([amb.ext.csespd](#amb.ext.csespd)). | Format file | Fixed, 7 bytes | p. 45/27 |
| <a id="ext.dirspd"></a>`ext.dirspd` | Wind direction and speed | As `ext.csespd`. Each field also permits the formats of the weather field that it replaces, as [06 section 5.1](06-weather.md#51-uncompressed-position) says. | [06](06-weather.md) | Fixed, 7 bytes | p. 45/27, p. 85/65 |
| <a id="ext.phg"></a>`ext.phg` | Power, height, gain, directivity | `'PHG'`, power digit, height code `'0'`–`'~'`, gain digit, directivity digit ([amb.ext.phg](#amb.ext.phg)). | Format file | Fixed, 7 bytes | p. 46/28 |
| <a id="ext.phgr"></a>`ext.phgr` | PHG with beacon rate | As `ext.phg`, then a rate byte, then `'/'` ([err.ext.length](#err.ext.length)). The rate byte is `'0'`–`'9'`, or `'A'` for 10 "and so on", up to `'~'`. | Format file | Fixed, 9 bytes | p. 46/28 |
| <a id="ext.rng"></a>`ext.rng` | Pre-calculated range | `'RNG'`, then four digits. | Format file | Fixed, 7 bytes | p. 47/29 |
| <a id="ext.dfs"></a>`ext.dfs` | Omni DF signal strength | `'DFS'`, strength digit, then height, gain and directivity as in `ext.phg`. | Format file | Fixed, 7 bytes | p. 47/29, p. 48/30 |
| <a id="ext.area"></a>`ext.area` | Area object descriptor | Type digit, `yy` two digits, colour (`'/'` and a digit, or `'1'` and `'0'`–`'5'`), `xx` two digits. The letters of `Tyy/Cxx` are placeholders ([amb.ext.area](#amb.ext.area)). The fields inside it are tokens of [05](05-object-item.md#area.type). | Symbol `\l` | Fixed, 7 bytes | p. 49/31, p. 78/60 |
| <a id="ext.brgnrq"></a>`ext.brgnrq` | DF bearing and NRQ | `'/'`, bearing (3 digits), `'/'`, then N, R, Q, one digit each. | 7.4 | Fixed, 8 bytes | p. 45/27, p. 48/30, p. 52/34 |

### 7.3 Values

| ID | Field | `value` finding | Source |
|---|---|---|---|
| `ext.csespd`, `ext.dirspd` | Course, direction | `361`–`999` | p. 45/27 |
| `ext.phg`, `ext.phgr`, `ext.dfs` | Directivity | `'9'`: no entry in the code table | p. 46/28, p. 48/30 |
| `ext.brgnrq` | Bearing | `361`–`999` (README rule 1) | p. 48/30 |

APRS12c specifies no range for speed. The course and the speed can be of
different kinds, as in `088/...`. Then the extension gives `unstated` and
`ambiguous` at its first byte ([amb.ext.csespd](#amb.ext.csespd)). In
`ext.dirspd`, such fields give no finding (06). A field can mix kinds
within itself, as in `8.8/036`. Such a field matches no format, and the
bytes are comment text.

### 7.4 Bearing and NRQ

The tokenizer reads `ext.brgnrq` at two places:

- directly after the extension of an uncompressed position report
  ([03 section 3](03-position.md#3-df-reports));
- after the `ext.csespd` of an Object or an Item
  ([05](05-object-item.md#obj.ext)), because the description in APRS12c
  names no format (p. 45/27).

At these places, the table below gives the result for eight bytes of
the `ext.brgnrq` format. The tokenizer uses the first row that matches.

| Symbol | Extension before the bytes | Bearing | Result |
|---|---|---|---|
| DF symbol `/\` | `ext.csespd` of a position report | Any | `ext.brgnrq`, with no `ambiguous` |
| DF symbol | Another extension | 360 or less | `ext.brgnrq`, with `ambiguous` at its first byte ([amb.ext.brgnrq](#amb.ext.brgnrq)) |
| Any symbol | `ext.csespd` | 360 or less | `ext.brgnrq`, with `ambiguous` at its first byte |
| Any other case | | | Comment text |

## 8. Comment

### 8.1 Comment field

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmt.text"></a>`cmt.text` | Comment | Text after the last data field or extension, with no separator. Bytes: printable ASCII or any UTF-8 character, as well-formed UTF-8 ([amb.cmt.bytes](#amb.cmt.bytes)). No CR or LF at the end. One `syntax` finding, at the first byte that fails. An empty comment has no token. | No | End of the information field | p. 34/20 |

The length limit is the limit of the format, in characters. Each byte
that is not a UTF-8 continuation byte (`0x80`–`0xBF`) starts a character.
The tokenizer does not count the bytes of `cmt.dao` tokens
([err.cmt.daolimit](#err.cmt.daolimit)). The first counted character past
the limit gives `value` on the rule that the format names
([amb.cmt.length](#amb.cmt.length)).

### 8.2 Items found inside a comment

The tokenizer looks for each field of this section only in the fields
that the next table lists. In other places, bytes of its format are text,
with no finding (README rule 2). Each occurrence is a token one level
below the field that contains it. The bytes of a base-91 telemetry
block ([`tlm.b91`](07-telemetry.md#tlm.b91)) belong to the block. The
tokenizer looks for no other field inside the block. For two fields whose
occurrences overlap, see [amb.cmt.overlap](#amb.cmt.overlap).

| Field | Where the tokenizer looks for it | Source |
|---|---|---|
| `cmt.alt`, `cmt.alt.neg` | Every comment: [`pos.cmt`](03-position.md#pos.cmt), [`pos.cmpcmt`](03-position.md#pos.cmpcmt), [`df.cmt`](03-position.md#df.cmt), the `cmt.text` of the Mic-E status text, [`obj.cmt`](05-object-item.md#obj.cmt), [`item.cmt`](05-object-item.md#item.cmt), [`tlm.cmt`](07-telemetry.md#tlm.cmt), [`grid.cmt`](03-position.md#grid.cmt), the comment after weather data ([06 section 7](06-weather.md#7-software-and-unit-codes)). | p. 34/20, p. 43/27 |
| `cmt.dao` | The position comments of the row above. Not `tlm.cmt`, `grid.cmt` or the comment after weather data. APRS12c names the DAO for Objects (p. 76/58). | p. 35/21, p. 76/58 |
| `cmt.noarchive` | Every text field, and [`udf.data`](09-other.md#udf.data) and [`inv.data`](09-other.md#inv.data) ([amb.cmt.noarchive](#amb.cmt.noarchive)). | p. 110/86 |
| Data extensions | The slot (7.1). After a compressed block (6.5). In the Mic-E status text: at the start of its `cmt.text` or, if there is none there, the first later run ([04 amb.mice.extension](04-mic-e.md#amb.mice.extension)). | p. 45/27 |
| `tlm.b91`, `freq.*`, `area.corridor`, `obj.signpost` | As [07](07-telemetry.md), [09](09-other.md#7-frequency-specification) and [05](05-object-item.md) say. | — |

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmt.alt"></a>`cmt.alt` | Altitude | `'/A='`, then six digits (feet), anywhere in the field. The field has a fixed width: a byte after the sixth digit is text, also if it is a digit ([amb.cmt.alt.width](#amb.cmt.alt.width)). For several altitudes, see [amb.cmt.alt](#amb.cmt.alt). For a `'/A='` that starts neither format, see [amb.cmt.alt.malformed](#amb.cmt.alt.malformed). | No | Fixed, 9 bytes | p. 43/27 |
| <a id="cmt.alt.neg"></a>`cmt.alt.neg` | Negative altitude | `'/A=-'`, then five digits, with the same fixed width. APRS12c says that this format is outside the official standard. No finding. It counts as the same field as `cmt.alt`. | No | Fixed, 9 bytes | p. 43/27 |
| <a id="cmt.dao"></a>`cmt.dao` | Datum and added precision | `'!'`, datum `D`, `A`, `O`, `'!'`, in a format of 8.3, anywhere in the field. | No | Fixed, 5 bytes | p. 35/21 to p. 36/22 |
| <a id="cmt.noarchive"></a>`cmt.noarchive` | No-archive marker | `'!x!'`, with a lower-case `'x'`. | No | Fixed, 3 bytes | p. 110/86 |

### 8.3 DAO formats

`D`, `A` and `O` are base-91 (p. 35/21). APRS12c specifies these meanings
(p. 36/22):

- An upper-case `D` adds a decimal digit to each coordinate.
- A lower-case `D` adds a base-91 digit to each coordinate.
- If `A` and `O` are both `SP`, they add nothing.
- A digit as `D` is a local datum.
- APRS12c reserves other datum values for later use.

| `D` | `A` and `O` | Result |
|---|---|---|
| `'A'`–`'Z'` | Both digits | `cmt.dao` |
| `'a'`–`'z'` | Both base-91 | `cmt.dao` |
| Letter or digit | Both `SP` | `cmt.dao` |
| `'0'`–`'9'` | Both base-91 | `cmt.dao`, `unstated`: APRS12c specifies no precision mode |
| Other base-91 | Both base-91, or both `SP` | `cmt.dao`, `unstated`: APRS12c does not specify the meaning of the datum |
| Any other bytes (for example, an upper-case `D` with a byte that is not a digit, or one `SP`) | | Text, no finding |

## 9. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.lat.ambiguity"></a>`amb.lat.ambiguity` | p. 40/24 | APRS12c describes blanks for the latitude. For the longitude, it only permits blanks. It does not specify which longitude blanks, or more blanks than the level of the latitude. | unstated | 2 | A longitude `SP` that the level covers: no finding. A `SP` that the level does not cover: `unstated` on `lon.amb`. |
| <a id="amb.lat.null"></a>`amb.lat.null` | p. 42/26 | The null position is also a real position at 0° N 0° W. APRS12c does not address symbols other than `\.`. | ambiguous | 4 | Ordinary tokens, no finding: every position of all zeros has the same ambiguity. |
| <a id="amb.sym.overlay"></a>`amb.sym.overlay` | p. 126/102, p. 141/117 | One part of APRS12c permits overlays only on the symbols marked in Appendix 2. The other part permits them on every alternate symbol since 2007. | conflict | 3 | Any overlay on a symbol of the alternate table: no finding. |
| <a id="err.b91.range"></a><a id="amb.b91.set"></a>`err.b91.range` (also `amb.b91.set`) | p. 34/20, p. 36/22, p. 55/37 | APRS12c specifies the set as codes 33–124, up to `'\|'` (p. 34/20). Another page specifies `'!'`–`'{'` (p. 55/37). A third page names `'}'` with value 90 (p. 36/22). | conflict | 3 | The `'}'` sentence of p. 36/22 is a typing error: the value 90 in it is the value of `'{'`. This sentence permits nothing. Base-91 is `'!'` to `'\|'` in every field that uses it, and `'}'` gives `syntax`. |
| <a id="err.b91.users"></a>`err.b91.users` | p. 34/20, p. 88/68 | APRS12c names two users of base-91 on one page and four on another page (p. 88/68). | conflict | 3 | No effect on tokens. |
| <a id="amb.cmp.cs"></a>`amb.cmp.cs` | p. 56/38, p. 58/40, p. 59/41 | The range requirement for `c` and the GGA requirement for altitude both apply when `T` has GGA bits and `c` is `'!'`–`'{'`. APRS12c specifies no order. The altitude example has `c` in the course range. | conflict | 3, 4 | `cmp.cs.alt`, the stricter format (it also restricts `T`), with no finding: every `cmp.cs.alt` whose `c` is not `'\|'` has the same ambiguity. |
| <a id="amb.cmp.filler"></a>`amb.cmp.filler` | p. 55/37, p. 56/38, p. 59/41 | All bytes except the table and the code are base-91 (p. 55/37). If `c` is `SP`, a receiver ignores the `csT` bytes, and `s` and `T` are fillers. | conflict | 3, 1 | The tokenizer accepts `c` = `SP`. Then `s` and `T` can be any byte, with no finding. |
| <a id="err.cmp.overlayexample"></a>`err.cmp.overlayexample` | p. 55/37, p. 125/101 | The overlay example has a block of 12 bytes. The format has 13. | conflict | 3 | A typing error (a latitude digit is missing). It permits nothing, and the format applies. |
| <a id="amb.ext.slot"></a>`amb.ext.slot` | p. 34/20, p. 45/27 | Nothing marks the bytes of the slot as an extension or as the start of the comment. | ambiguous | 4, 1 | The extension, with no finding: every extension has the same ambiguity. The slot is the fixed place of the extension. Thus the tokenizer reads a run of the format of an extension there as that extension. It gives the `value` finding of the extension, for example for course 400. An interpretation of the bytes as a comment does not prevent the finding. |
| <a id="amb.ext.count"></a>`amb.ext.count` | p. 34/20, p. 45/27 | Whether a receiver reads a second extension, or an extension later in the comment. | unstated | 2 | APRS12c names only the slot. Such runs are comment text, with no finding. |
| <a id="amb.ext.compressed"></a>`amb.ext.compressed` | p. 45/27, p. 54/36, p. 55/37, p. 59/41, p. 76/58 | An extension can follow position data (p. 45/27). The block replaces the extension, and the diagrams go from `T` to the comment. | conflict | 3, 4 | A run after `T` is an extension if it matches a format of step 3 with no `syntax` or `value` finding. Under `\l`, the run is an extension if it is the area descriptor. The extension gives `ambiguous` at its first byte. The comment after it has a limit of 36. Other runs are comment text. |
| <a id="amb.ext.csespd"></a>`amb.ext.csespd` | p. 45/27, p. 52/34 | APRS12c lists unknown values only as complete pairs. It does not specify a known course with an unknown speed. | ambiguous | 2, 4 | `ext.csespd`, with `unstated` and `ambiguous` at its first byte. The interpretation with listed pairs reads the bytes as comment. |
| <a id="amb.ext.phg"></a>`amb.ext.phg` | p. 46/28, p. 47/29, p. 48/30 | The height code is "0–9 and above". The DFS table stops at `'9'`, but DFS is PHG with the power replaced. The rate starts at `'A'` "and so on". Directivity `'9'` has no entry. | ambiguous | 1 | Height `'0'`–`'~'` in PHG, PHGR and DFS, and rate up to `'~'`: no finding. Directivity `'9'`: `value`. |
| <a id="err.ext.length"></a>`err.ext.length` | p. 31/17, p. 45/27, p. 46/28 | Extensions are always 7 bytes. PHGR has 9. | conflict | 3, 4 | `ext.phgr`, the stricter format, with no finding: every `ext.phgr` is also a PHG and a comment. |
| <a id="amb.ext.brgnrq"></a>`amb.ext.brgnrq` | p. 45/27, p. 48/30, p. 52/34, p. 53/35, p. 76/58 | Bearing and NRQ follow a course and speed (the description in APRS12c, for any report) or any extension (the DF diagrams, [err.df.ext](03-position.md#err.df.ext)). They are "only meaningful" with the DF symbol. The Object diagram lists no bearing. | conflict | 3, 4 | As 7.4. A bearing above 360 outside a DF report with course and speed: comment text, no finding. |
| <a id="amb.ext.area"></a>`amb.ext.area` | p. 45/27, p. 49/31, p. 78/60, p. 80/62 | One interpretation reads the name `Tyy/Cxx` as literal letters. Only the examples show that `yy` and `xx` are digits. | ambiguous | 1, 3 | The letters are placeholders. `T12/C34` is comment text, with no finding. |
| <a id="err.ext.phgheight"></a>`err.ext.phgheight` | p. 46/28 | APRS12c writes 20480 feet as 36.2 km. | conflict | 3 | No effect on tokens. |
| <a id="err.ext.phgrange"></a>`err.ext.phgrange` | p. 47/29 | The range formula has dashes in place of square roots. | conflict | 3 | No effect on tokens. |
| <a id="err.ext.areagap"></a>`err.ext.areagap` | p. 78/60, p. 80/62 | The examples have spaces around `'l'`. | conflict | 3 | As [err.area.gap](05-object-item.md#err.area.gap). |
| <a id="err.sym.chapter"></a>`err.sym.chapter` | p. 27/17, p. 29/19, p. 40/24, p. 85/65 | "Chapter 20" for symbols, as in [err.dest.chapref](01-frame.md#err.dest.chapref). | conflict | 3 | No effect on tokens. |
| <a id="amb.cmt.bytes"></a>`amb.cmt.bytes` | p. 34/20 | "Any printable ASCII or UTF-8 character": whether "printable" also limits UTF-8. | ambiguous | 1 | Control bytes and DEL give no finding. Bytes that are not well-formed UTF-8, and CR or LF at the end, give `syntax`. |
| <a id="amb.cmt.length"></a>`amb.cmt.length` | p. 34/20, p. 50/32, p. 76/58 | The editor questions the comment limits and specifies no other limits. The limits are in "chars". The comment can contain UTF-8 characters of several bytes. | ambiguous | 1 | The limits apply: `value`. They count characters: this is the interpretation that accepts more bytes. Thus `value` only past the limit in characters. |
| <a id="err.cmt.daolimit"></a>`err.cmt.daolimit` | p. 35/21, p. 50/32 to p. 53/35, p. 59/41 | The DAO can go beyond a "viewable" limit of 57 bytes. No diagram specifies this limit. | conflict | 3 | A comment that is over its limit only because of DAO bytes gives no finding: the tokenizer does not count `cmt.dao` bytes. |
| <a id="amb.cmt.alt"></a>`amb.cmt.alt` | p. 43/27 | Several altitudes in one field. | ambiguous | 4 | Each altitude is a token, with `ambiguous` on each. |
| <a id="amb.cmt.alt.width"></a>`amb.cmt.alt.width` | p. 43/27 | The altitude has "exactly 6 digits". APRS12c does not say what a digit after the sixth digit is. | ambiguous | 1 | One interpretation accepts the bytes: the field has six digits, and the next byte is text. Thus a seventh digit gives no finding. Many senders write a digit directly after the altitude, for example a frequency. An earlier version of this reading gave `syntax` on a seventh digit. The author dropped it: that reading gave no altitude for these packets. |
| <a id="amb.cmt.alt.malformed"></a>`amb.cmt.alt.malformed` | p. 43/27 | What `'/A='` is when fewer than six digits (or `'-'` and fewer than five) follow it. | ambiguous | 1 | `'/A='` is a marker that starts the altitude. Thus the tokenizer reads the run as `cmt.alt`. The token goes up to the last byte that matches. The first byte that does not match gives `syntax`. If the field is cut short, that byte is past the end of the field. |
| <a id="amb.cmt.dao"></a>`amb.cmt.dao` | p. 35/21, p. 36/22 | Several candidates. A DAO, or text of the same format. The precision of digit datums and of other datums. | ambiguous | 4, 2 | Several candidates: `ambiguous` on each. One candidate: no finding, because every DAO has the same ambiguity. Datums: 8.3. |
| <a id="err.cmt.daoexample"></a>`err.cmt.daoexample` | p. 36/22, p. 37/23 | The example decodes `':'` to 27. The correct value is 25. | conflict | 3 | No effect on tokens. |
| <a id="amb.cmt.noarchive"></a>`amb.cmt.noarchive` | p. 110/86, p. 155/131 | "Any packet containing" `'!x!'`: in text only, or anywhere. | ambiguous | 1; none | Anywhere, repeats included, with no finding (rule 1). A `cmt.noarchive` token in text. Working choice: a match outside text has no token. |
| <a id="amb.cmt.overlap"></a>`amb.cmt.overlap` | p. 35/21, p. 43/27 | Two fields that can be anywhere can overlap. | ambiguous | 4; none | `ambiguous` on each (rule 4). `'!x!'` claims no bytes and is not part of this check. Working choice: the tokenizer keeps both tokens. |

## 10. Reviewed exceptions

None.

## 11. Open items

None.
