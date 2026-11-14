# Fields shared by several formats

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, the general rules and the tokenizer model are in [README.md](README.md). |

## 1. Scope

The fields that several formats use: timestamps, uncompressed latitude
and longitude with position ambiguity, the symbol, base-91 digits, the
compressed position block, the data extensions and the comment with the
items found in it. Rule prefixes `time`, `lat`, `lon`, `sym`, `b91`,
`cmp`, `ext` and `cmt`. Where a field stands, and whether it is required,
is said by the format files ([03](03-position.md) to [09](09-other.md)).

A field of fixed length is one token of that length whether or not its
bytes fit; a field cut short covers the bytes present. Offsets inside a
field count from 0.

## 2. Timestamps

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="time.dhm"></a>`time.dhm` | Day, hour, minute | Six digits: day of month `01`–`31`, hour `00`–`23`, minute `00`–`59`; then `'z'` (UTC) or `'/'` (local time). `'/'` gives `discouraged`: zulu only is recommended on the air. | Format file | Fixed, 7 bytes | p. 38/22 |
| <a id="time.hms"></a>`time.hms` | Hour, minute, second | Six digits: hour `00`–`23`, minute and second `00`–`59`; then `'h'`. UTC. | Format file | Fixed, 7 bytes | p. 38/22 |
| <a id="time.mdhm"></a>`time.mdhm` | Month, day, hour, minute | Eight digits: month `01`–`12`, day `01`–`31`, hour, minute. UTC, no indicator. Only in positionless weather reports. | [06](06-weather.md) | Fixed, 8 bytes | p. 38/22 |

Where a format allows both seven-byte forms ("DHM / HMS", p. 50/32), the
byte at offset 6 picks the form: `'z'` or `'/'` gives `time.dhm`, `'h'`
gives `time.hms`. Any other byte there, `'Z'` and `'H'` included, gives a
`time.dhm` token with `syntax` at offset 6. A non-digit in offsets 0–5
gives `syntax`. A part outside its range gives `value`; the hour, minute
and second ranges are those of the 24-hour clock (README rule 1). Each
part is checked when its two digits are present. A day is not checked
against the length of its month.

## 3. Latitude and longitude

### 3.1 Fields

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="lat"></a>`lat` | Latitude | Offsets 0–1 degrees `00`–`90`, 2–3 minutes, 4 `'.'`, 5–6 hundredths, 7 `'N'` or `'S'` (upper case). Minutes up to 59, and none at 90 degrees. `SP` only under `lat.amb`. | Format file | Fixed, 8 bytes | p. 39/23 |
| <a id="lon"></a>`lon` | Longitude | Offsets 0–2 degrees `000`–`180`, 3–4 minutes, 5 `'.'`, 6–7 hundredths, 8 `'E'` or `'W'` (upper case). Minutes up to 59, and none at 180 degrees. `SP` only under `lon.amb`. | Format file | Fixed, 9 bytes | p. 39/23, p. 40/24 |

A byte outside the layout gives one `syntax` finding, at the first such
byte. Degrees above 90 or 180, a tens-of-minutes digit `'6'`–`'9'`, and
a non-zero minute digit at 90 or 180 degrees give `value` (README rule
1), checked on the digits present.

### 3.2 Position ambiguity

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="lat.amb"></a>`lat.amb` | Ambiguity level | A check on `lat`, no token. The minute and hundredths digits are replaced by `SP` progressively from the right: offsets 6, 5, 3, 2 in that order. The level, 0 to 4, is the number of `SP` counted from offset 6. A `SP` at one of these offsets after a digit earlier in that order gives `syntax`. | No | — | p. 40/24 |
| <a id="lon.amb"></a>`lon.amb` | Longitude blanks | A check on `lon`, no token. The latitude's level applies to the longitude, and blanks there are allowed but not needed. A `SP` at offsets 7, 6, 4, 3 that the level covers (the first *level* offsets of that order) gives no finding; one it does not cover gives `unstated` ([amb.lat.ambiguity](#amb.lat.ambiguity)). | No | — | p. 40/24 |

### 3.3 Null position

A station without a position sends `0000.00N` and `00000.00W`, and the
symbol "should" be `\.` (p. 42/26). These are ordinary `lat`, `lon` and
symbol tokens with no finding ([amb.lat.null](#amb.lat.null)).

## 4. Symbol table and code

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="sym.table"></a>`sym.table` | Symbol table identifier, uncompressed | `'/'` (primary), `'\'` (alternate), `'0'`–`'9'` or `'A'`–`'Z'` (alternate with that overlay). `'a'`–`'j'` belong to the compressed form only. Other bytes give `syntax`. | Format file | Fixed, 1 byte | p. 40/24, p. 125/101 |
| <a id="sym.code"></a>`sym.code` | Symbol code | `'!'`–`'~'`, the codes of the tables of Appendix 2. Other bytes give `syntax`. | Format file | Fixed, 1 byte | p. 139/115 to p. 141/117 |

Overlay capability is not checked ([amb.sym.overlay](#amb.sym.overlay)).
Which of several symbols in one packet wins (p. 127/103) is not a check
on these fields. Symbols in the destination address are read in
[01](01-frame.md), the Mic-E symbol in [04](04-mic-e.md).

## 5. Base-91 digits

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="b91.digit"></a>`b91.digit` | Base-91 digit | One byte `'!'`–`'\|'` (`0x21`–`0x7C`), value byte − 33; a number is read most significant digit first ([err.b91.range](#err.b91.range)). A rule, not a token: a field that uses it gives `syntax` on its own ID for a byte outside the set. In a base-91 telemetry block `'\|'` is the delimiter ([07 section 3](07-telemetry.md#3-base-91-comment-telemetry)). | — | Fixed, 1 byte | p. 34/20, p. 55/37, p. 88/68 |

## 6. Compressed position block

### 6.1 Telling the two position forms apart

Where a format allows either position form, a digit starts an
uncompressed position (`lat`, `sym.table`, `lon`, `sym.code`), and a
byte of the `cmp.table` set starts a compressed block (p. 55/37,
p. 125/101). Any other byte gives `syntax` on the format's selector
rule, such as [`pos.form`](03-position.md#pos.form), and the rest of
the field is residue.

### 6.2 Fields

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmp.block"></a>`cmp.block` | Compressed position | Table (1), latitude (4), longitude (4), code (1), `cs` (2), `T` (1); the parts are tokens one level deeper. It stands in place of the uncompressed position and its extension. | Format file | Fixed, 13 bytes | p. 55/37, p. 59/41 |
| <a id="cmp.table"></a>`cmp.table` | Symbol table identifier, compressed | `'/'`, `'\'`, `'A'`–`'Z'`, or `'a'`–`'j'` for overlay digits 0–9. Never a digit. | Yes | Fixed, 1 byte | p. 55/37, p. 125/101 |
| <a id="cmp.lat"></a>`cmp.lat` | Latitude | 4 base-91 digits, 380926 × (90 − latitude). A value above 68566680 (beyond 90 S) gives `value`. | Yes | Fixed, 4 bytes | p. 56/38 |
| <a id="cmp.lon"></a>`cmp.lon` | Longitude | 4 base-91 digits, 190463 × (180 + longitude). A value above 68566680 (beyond 180 E) gives `value`. | Yes | Fixed, 4 bytes | p. 56/38 |
| <a id="cmp.code"></a>`cmp.code` | Symbol code | As [`sym.code`](#sym.code). | Yes | Fixed, 1 byte | p. 55/37 |
| <a id="cmp.cs"></a>`cmp.cs` | Course and speed, range, altitude or wind | `c` then `s`, read as in 6.3; the token carries the ID of the step taken. | Yes | Fixed, 2 bytes | p. 56/38 to p. 58/40 |
| <a id="cmp.t"></a>`cmp.t` | Compression type | Read as in 6.4. | Yes | Fixed, 1 byte | p. 57/39 |

A block cut short by the end of the field is a `cmp.block` token over
the bytes present, each part present a token over its bytes; the first
missing byte gives `syntax` where it was expected. Without `T` the step
of 6.3 is unknown, so `c` fails only when it is neither `SP` nor a
base-91 digit.

### 6.3 Reading the cs bytes

The first step whose condition holds is taken.

| Step | Condition | Token ID | Further bytes | Source |
|---|---|---|---|---|
| 1 | `c` is `SP` | <a id="cmp.cs.none"></a>`cmp.cs.none` | `s` and `T` are ignored fillers, any byte ([amb.cmp.filler](#amb.cmp.filler)) | p. 56/38, p. 59/41 |
| 2 | Bits 4–3 of `T` − 33 are `1 0` (GGA) | <a id="cmp.cs.alt"></a>`cmp.cs.alt` | `c` and `s` base-91 ([amb.cmp.cs](#amb.cmp.cs)) | p. 58/40 |
| 3 | A weather report ([06](06-weather.md)) and `c` in `'!'`–`'z'` | <a id="cmp.cs.wind"></a>`cmp.cs.wind` | `s` base-91 | p. 86/66 |
| 4 | `c` in `'!'`–`'z'` | <a id="cmp.cs.crs"></a>`cmp.cs.crs` | `s` base-91 | p. 56/38 |
| 5 | `c` is `'{'` | <a id="cmp.cs.rng"></a>`cmp.cs.rng` | `s` base-91 | p. 57/39 |
| 6 | Otherwise | `cmp.cs` | `syntax` at `c` | — |

The `cs` token gives at most one `syntax` finding, at the first of `c`
and `s` that fails.

### 6.4 The T byte

When `c` is not `SP`, `T` is a base-91 digit, else `syntax`. Bits 7–6 of
`T` − 33 are unused and 0, so a `T` from `'a'` to `'|'` gives `value`.
The origin codes marked "tbd" give no finding (p. 57/39).

### 6.5 What follows the block

What the format puts there, usually a comment. A run directly after `T`
that fits a form of step 3 of 7.1 with no `syntax` or `value` finding of
that form is that extension, with `ambiguous` at its first byte, and the
comment after it may hold 36 characters
([amb.ext.compressed](#amb.ext.compressed)). With the symbol `\l` the
form tried is step 1 instead: seven bytes that fit `ext.area` are that
descriptor, with `ambiguous` at its first byte, and no form of step 3 is
tried. Bearing and NRQ are not read there.

## 7. Data extensions

### 7.1 The extension slot

The slot is the bytes directly after the symbol code of an uncompressed
position, in the formats whose files provide one (p. 45/27). The forms
are tried in this order and the first that fits is taken:

1. Symbol `\l`: [`ext.area`](#ext.area). In a position report see
   [amb.pos.ext](03-position.md#amb.pos.ext); in an object or item,
   [05](05-object-item.md) says what the slot holds.
2. A weather report: [`ext.dirspd`](#ext.dirspd) only (06).
3. Otherwise [`ext.csespd`](#ext.csespd), [`ext.phgr`](#ext.phgr),
   [`ext.phg`](#ext.phg), [`ext.rng`](#ext.rng), [`ext.dfs`](#ext.dfs).

Bytes that fit no form are the start of the comment, with no finding
([amb.ext.slot](#amb.ext.slot)). A slot holds one extension; bytes after
it are comment text ([amb.ext.count](#amb.ext.count)), except bearing
and NRQ (7.4) and storm data (06). Upper case is significant: `phg`,
`rng`, `dfs` fit nothing.

### 7.2 Fields

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="ext.csespd"></a>`ext.csespd` | Course and speed | Course (3), `'/'`, speed (3). Each part three digits, `'...'` or three `SP` ([amb.ext.csespd](#amb.ext.csespd)). | Format file | Fixed, 7 bytes | p. 45/27 |
| <a id="ext.dirspd"></a>`ext.dirspd` | Wind direction and speed | As `ext.csespd`; each part also takes the forms of the weather element it replaces, as [06 section 5.1](06-weather.md#51-uncompressed-position) says. | [06](06-weather.md) | Fixed, 7 bytes | p. 45/27, p. 85/65 |
| <a id="ext.phg"></a>`ext.phg` | Power, height, gain, directivity | `'PHG'`, power digit, height code `'0'`–`'~'`, gain digit, directivity digit ([amb.ext.phg](#amb.ext.phg)). | Format file | Fixed, 7 bytes | p. 46/28 |
| <a id="ext.phgr"></a>`ext.phgr` | PHG with beacon rate | As `ext.phg`, then a rate byte (`'0'`–`'9'`, or `'A'` for 10 "and so on", up to `'~'`), then `'/'` ([err.ext.length](#err.ext.length)). | Format file | Fixed, 9 bytes | p. 46/28 |
| <a id="ext.rng"></a>`ext.rng` | Pre-calculated range | `'RNG'`, then four digits. | Format file | Fixed, 7 bytes | p. 47/29 |
| <a id="ext.dfs"></a>`ext.dfs` | Omni DF signal strength | `'DFS'`, strength digit, then height, gain and directivity as in `ext.phg`. | Format file | Fixed, 7 bytes | p. 47/29, p. 48/30 |
| <a id="ext.area"></a>`ext.area` | Area object descriptor | Type digit, `yy` two digits, colour (`'/'` and a digit, or `'1'` and `'0'`–`'5'`), `xx` two digits. The letters of `Tyy/Cxx` are placeholders ([amb.ext.area](#amb.ext.area)). Its parts are tokens of [05](05-object-item.md#area.type). | Symbol `\l` | Fixed, 7 bytes | p. 49/31, p. 78/60 |
| <a id="ext.brgnrq"></a>`ext.brgnrq` | DF bearing and NRQ | `'/'`, bearing (3 digits), `'/'`, then N, R, Q, one digit each. | 7.4 | Fixed, 8 bytes | p. 45/27, p. 48/30, p. 52/34 |

### 7.3 Values

| ID | Part | `value` finding | Source |
|---|---|---|---|
| `ext.csespd`, `ext.dirspd` | Course, direction | `361`–`999` | p. 45/27 |
| `ext.phg`, `ext.phgr`, `ext.dfs` | Directivity | `'9'`: no entry in the code table | p. 46/28, p. 48/30 |
| `ext.brgnrq` | Bearing | `361`–`999` (README rule 1) | p. 48/30 |

Speed has no stated range. A course and speed whose parts are of
different kinds, as `088/...`, gives `unstated` and `ambiguous` at its
first byte ([amb.ext.csespd](#amb.ext.csespd)); in `ext.dirspd` such
parts give no finding (06). A part that mixes kinds within itself, as
`8.8/036`, fits no form, and the bytes are comment text.

### 7.4 Bearing and NRQ

`ext.brgnrq` is read directly after the extension of an uncompressed
position report ([03 section 3](03-position.md#3-df-reports)), and after
the `ext.csespd` of an object or item, since p. 45/27 names no format
([05](05-object-item.md#obj.ext)). With the DF symbol `/\` after an
`ext.csespd` of a position report it is read with no finding. With the
DF symbol after another extension, or in any other case after an
`ext.csespd`, eight bytes of its shape with a bearing of at most 360 are
`ext.brgnrq` with `ambiguous` at their first byte
([amb.ext.brgnrq](#amb.ext.brgnrq)). Otherwise they are comment text.

## 8. Comment

### 8.1 Comment field

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmt.text"></a>`cmt.text` | Comment | Free text after the last data field or extension, no separator. Bytes: printable ASCII or any UTF-8 character, as well-formed UTF-8 ([amb.cmt.bytes](#amb.cmt.bytes)); no CR or LF at the end. One `syntax` finding, at the first byte that fails. An empty comment has no token. | No | End of the information field | p. 34/20 |

The length limit is the format's, in characters: each byte that is not
a UTF-8 continuation byte (`0x80`–`0xBF`) starts one. The bytes of
`cmt.dao` tokens are not counted ([err.cmt.daolimit](#err.cmt.daolimit));
the first counted character past the limit gives `value` on the rule the
format names ([amb.cmt.length](#amb.cmt.length)).

### 8.2 Items found inside a comment

Each item is looked for only in the fields listed here; elsewhere bytes
of its shape are text with no finding (README rule 2). Each occurrence is
a token one level deeper than the field. The bytes of a base-91
telemetry block ([`tlm.b91`](07-telemetry.md#tlm.b91)) belong to the
block, and no other item is looked for inside it. Two items whose
occurrences overlap: [amb.cmt.overlap](#amb.cmt.overlap).

| Item | Fields | Source |
|---|---|---|
| `cmt.alt`, `cmt.alt.neg` | Every comment: [`pos.cmt`](03-position.md#pos.cmt), [`pos.cmpcmt`](03-position.md#pos.cmpcmt), [`df.cmt`](03-position.md#df.cmt), the Mic-E free text, [`obj.cmt`](05-object-item.md#obj.cmt), [`item.cmt`](05-object-item.md#item.cmt), [`tlm.cmt`](07-telemetry.md#tlm.cmt), [`grid.cmt`](03-position.md#grid.cmt), the comment after weather data ([06 section 7](06-weather.md#7-software-and-unit-codes)). | p. 34/20, p. 43/27 |
| `cmt.dao` | The position comments of the row above, not `tlm.cmt`, `grid.cmt` or the comment after weather data; p. 76/58 names it for objects. | p. 35/21, p. 76/58 |
| `cmt.noarchive` | Every free-text field, and [`udf.data`](09-other.md#udf.data) and [`inv.data`](09-other.md#inv.data) ([amb.cmt.noarchive](#amb.cmt.noarchive)). | p. 110/86 |
| Data extensions | The slot (7.1); after a compressed block (6.5); the Mic-E status text, at the start of its free text or, with none there, the first later run ([04 amb.mice.extension](04-mic-e.md#amb.mice.extension)). | p. 45/27 |
| `tlm.b91`, `freq.*`, `area.corridor`, `obj.signpost` | As [07](07-telemetry.md), [09](09-other.md#7-frequency-specification) and [05](05-object-item.md) say. | — |

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmt.alt"></a>`cmt.alt` | Altitude | `'/A='`, then exactly six digits (feet), anywhere in the field. Several: [amb.cmt.alt](#amb.cmt.alt). A `'/A='` that starts neither form: [amb.cmt.alt.malformed](#amb.cmt.alt.malformed). | No | Fixed, 9 bytes | p. 43/27 |
| <a id="cmt.alt.neg"></a>`cmt.alt.neg` | Negative altitude | `'/A=-'`, then exactly five digits. The document says it is outside the official standard; no finding. Counts as the same item as `cmt.alt`. | No | Fixed, 9 bytes | p. 43/27 |
| <a id="cmt.dao"></a>`cmt.dao` | Datum and added precision | `'!'`, datum `D`, `A`, `O`, `'!'`, in a form of 8.3, anywhere in the field. | No | Fixed, 5 bytes | p. 35/21 to p. 36/22 |
| <a id="cmt.noarchive"></a>`cmt.noarchive` | No-archive marker | `'!x!'`, lower-case `'x'`. | No | Fixed, 3 bytes | p. 110/86 |

### 8.3 DAO forms

`D`, `A` and `O` are base-91 (p. 35/21). Upper case `D` adds a decimal
digit to each coordinate, lower case a base-91 digit, and `A` and `O`
both `SP` add nothing; digits are local datums, and further datum values
are left for later use (p. 36/22).

| `D` | `A` and `O` | Result |
|---|---|---|
| `'A'`–`'Z'` | Both digits | `cmt.dao` |
| `'a'`–`'z'` | Both base-91 | `cmt.dao` |
| Letter or digit | Both `SP` | `cmt.dao` |
| `'0'`–`'9'` | Both base-91 | `cmt.dao`, `unstated`: no precision mode is given |
| Other base-91 | Both base-91, or both `SP` | `cmt.dao`, `unstated`: the datum's meaning is not given |
| Anything else (an upper-case `D` with a non-digit, one `SP`) | | Text, no finding |

## 9. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.lat.ambiguity"></a>`amb.lat.ambiguity` | p. 40/24 | Blanking is described for the latitude; for the longitude only that blanks are allowed. Which longitude blanks, and more than the latitude's level, are not given. | unstated | 2 | Longitude `SP` the level covers: none. One it does not cover: `unstated` on `lon.amb`. |
| <a id="amb.lat.null"></a>`amb.lat.null` | p. 42/26 | The null position is also a real position at 0° N 0° W; other symbols than `\.` are not addressed. | ambiguous | 4 | Ordinary tokens, no finding: every all-zero position carries the question. |
| <a id="amb.sym.overlay"></a>`amb.sym.overlay` | p. 126/102, p. 141/117 | Overlays only on symbols marked in Appendix 2, against every alternate symbol since 2007. | conflict | 3 | Any overlay on an alternate-table symbol, no finding. |
| <a id="err.b91.range"></a><a id="amb.b91.set"></a>`err.b91.range` (also `amb.b91.set`) | p. 34/20, p. 36/22, p. 55/37 | The set is codes 33–124, to `'\|'` (p. 34/20), and `'!'`–`'{'` (p. 55/37); p. 36/22 names `'}'` with value 90. | conflict | 3 | The `'}'` sentence of p. 36/22 is a slip of the pen (the value 90 it states is that of `'{'`): it allows nothing. Base-91 is `'!'` to `'\|'` wherever it is used, and `'}'` gives `syntax`. |
| <a id="err.b91.users"></a>`err.b91.users` | p. 34/20, p. 88/68 | Two users of base-91 named, four on p. 88/68. | conflict | 3 | No effect on tokens. |
| <a id="amb.cmp.cs"></a>`amb.cmp.cs` | p. 56/38, p. 58/40, p. 59/41 | The range rule for `c` and the GGA rule for altitude both hold when `T` has GGA bits and `c` is `'!'`–`'{'`; no order. The altitude example has `c` in the course range. | conflict | 3, 4 | `cmp.cs.alt`, the more specific (it also fixes `T`), no finding: every `cmp.cs.alt` whose `c` is not `'\|'` carries it. |
| <a id="amb.cmp.filler"></a>`amb.cmp.filler` | p. 55/37, p. 56/38, p. 59/41 | All bytes but table and code are base-91 (p. 55/37); with `c` = `SP` the `csT` bytes are ignored, `s` and `T` fillers. | conflict | 3, 1 | `c` = `SP` conforms; `s` and `T` are then any byte, no finding. |
| <a id="err.cmp.overlayexample"></a>`err.cmp.overlayexample` | p. 55/37, p. 125/101 | The overlay example has a 12-byte block; the layout has 13. | conflict | 3 | A slip (a latitude digit missing): it allows nothing; the layout holds. |
| <a id="amb.ext.slot"></a>`amb.ext.slot` | p. 34/20, p. 45/27 | Nothing marks slot bytes as an extension or as the start of the comment. | ambiguous | 4, 1 | The extension, no finding: every extension carries it. The slot is the fixed place of the extension, so a run of an extension's shape there is judged as that extension, and its `value` finding, as for course 400, is given; reading the run as comment does not make it conform. |
| <a id="amb.ext.count"></a>`amb.ext.count` | p. 34/20, p. 45/27 | Whether a second extension, or one later in the comment, is read. | unstated | 2 | Only the slot is named: such runs are comment text, no finding. |
| <a id="amb.ext.compressed"></a>`amb.ext.compressed` | p. 45/27, p. 54/36, p. 55/37, p. 59/41, p. 76/58 | An extension may follow position data (p. 45/27); the block replaces the extension and the diagrams go from `T` to the comment. | conflict | 3, 4 | A run after `T` that fits a form of step 3 with no `syntax` or `value` finding, or under `\l` the area descriptor: that extension, `ambiguous` at its first byte, comment limit 36 after it. Else comment text. |
| <a id="amb.ext.csespd"></a>`amb.ext.csespd` | p. 45/27, p. 52/34 | Unknown values are listed only as whole pairs; a known course with an unknown speed is not given. | ambiguous | 2, 4 | `ext.csespd`, `unstated` and `ambiguous` at its first byte (the listed-pairs reading takes the bytes as comment). |
| <a id="amb.ext.phg"></a>`amb.ext.phg` | p. 46/28, p. 47/29, p. 48/30 | The height code is "0–9 and above"; the DFS table stops at `'9'` though DFS is PHG with power replaced; the rate runs from `'A'` "and so on"; directivity `'9'` has no entry. | ambiguous | 1 | Height `'0'`–`'~'` in PHG, PHGR and DFS and rate up to `'~'`, no finding. Directivity `'9'`: `value`. |
| <a id="err.ext.length"></a>`err.ext.length` | p. 31/17, p. 45/27, p. 46/28 | Extensions are always 7 bytes; PHGR has 9. | conflict | 3, 4 | `ext.phgr`, the more specific, no finding: every `ext.phgr` is also a PHG and a comment. |
| <a id="amb.ext.brgnrq"></a>`amb.ext.brgnrq` | p. 45/27, p. 48/30, p. 52/34, p. 53/35, p. 76/58 | Bearing and NRQ follow a course and speed (text, for any report) or any extension (DF diagrams, [err.df.ext](03-position.md#err.df.ext)); they are "only meaningful" with the DF symbol; the object diagram lists no bearing. | conflict | 3, 4 | As 7.4. A bearing above 360 outside a DF report with course and speed: comment text, no finding. |
| <a id="amb.ext.area"></a>`amb.ext.area` | p. 45/27, p. 49/31, p. 78/60, p. 80/62 | The name `Tyy/Cxx` reads as literal letters; `yy`, `xx` are digits only by example. | ambiguous | 1, 3 | Letters are placeholders: `T12/C34` is comment text, no finding. |
| <a id="err.ext.phgheight"></a>`err.ext.phgheight` | p. 46/28 | 20480 feet given as 36.2 km. | conflict | 3 | No effect on tokens. |
| <a id="err.ext.phgrange"></a>`err.ext.phgrange` | p. 47/29 | The range formula prints dashes for square roots. | conflict | 3 | No effect on tokens. |
| <a id="err.ext.areagap"></a>`err.ext.areagap` | p. 78/60, p. 80/62 | Spaces printed around `'l'` in the examples. | conflict | 3 | As [err.area.gap](05-object-item.md#err.area.gap). |
| <a id="err.sym.chapter"></a>`err.sym.chapter` | p. 27/17, p. 29/19, p. 40/24, p. 85/65 | "Chapter 20" for symbols; as [err.dest.chapref](01-frame.md#err.dest.chapref). | conflict | 3 | No effect on tokens. |
| <a id="amb.cmt.bytes"></a>`amb.cmt.bytes` | p. 34/20 | "Any printable ASCII or UTF-8 character": whether "printable" also bounds UTF-8. | ambiguous | 1 | Control bytes and DEL conform. Bytes outside well-formed UTF-8, and CR or LF at the end, give `syntax`. |
| <a id="amb.cmt.length"></a>`amb.cmt.length` | p. 34/20, p. 50/32, p. 76/58 | The editor questions the comment limits and states no other. The limits are in "chars", and the comment may hold UTF-8 characters of several bytes. | ambiguous | 1 | The limits hold: `value`. They count characters, the reading that accepts more bytes, so `value` only past the limit in characters. |
| <a id="err.cmt.daolimit"></a>`err.cmt.daolimit` | p. 35/21, p. 50/32 to p. 53/35, p. 59/41 | The DAO may go beyond a "viewable" 57-byte limit that no diagram gives. | conflict | 3 | A comment over its limit only by DAO bytes conforms: `cmt.dao` bytes are not counted. |
| <a id="amb.cmt.alt"></a>`amb.cmt.alt` | p. 43/27 | Several altitudes in one field. | ambiguous | 4 | Each a token, `ambiguous` on each. |
| <a id="amb.cmt.alt.malformed"></a>`amb.cmt.alt.malformed` | p. 43/27 | What `'/A='` not followed by exactly six digits (or `'-'` and five) is. | ambiguous | 1 | `'/A='` announces the altitude, so the run is judged as `cmt.alt`: a token up to the last fitting byte and `syntax` at the first byte that does not fit, past the field when it is cut short. |
| <a id="amb.cmt.dao"></a>`amb.cmt.dao` | p. 35/21, p. 36/22 | Several candidates; DAO or text of the same shape; the precision of digit and other datums. | ambiguous | 4, 2 | Several: `ambiguous` on each. One: no finding, every DAO carries it. Datums: 8.3. |
| <a id="err.cmt.daoexample"></a>`err.cmt.daoexample` | p. 36/22, p. 37/23 | `':'` decoded to 27; it is 25. | conflict | 3 | No effect on tokens. |
| <a id="amb.cmt.noarchive"></a>`amb.cmt.noarchive` | p. 110/86, p. 155/131 | "Any packet containing" `'!x!'`: in text only or anywhere. | ambiguous | 1; none | Anywhere, repeats included, no finding (rule 1). A `cmt.noarchive` token in free text. Working choice: a match outside free text has no token. |
| <a id="amb.cmt.overlap"></a>`amb.cmt.overlap` | p. 35/21, p. 43/27 | Two items that may stand anywhere can overlap. | ambiguous | 4; none | `ambiguous` on each (rule 4); `'!x!'` claims no bytes and takes no part. Working choice: both tokens are kept. |

## 10. Reviewed exceptions

None.

## 11. Open items

None.
