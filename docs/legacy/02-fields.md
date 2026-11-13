# Fields shared by several formats

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`; `UAP` from the same submodule. Conventions, the tokenizer model and the decoder commits are in [README.md](README.md). |

## 1. Scope

This file reads the fields that more than one format uses: timestamps,
uncompressed latitude and longitude with position ambiguity, the symbol
table and code, base-91 digits, the 13-byte compressed position block,
the 7-byte data extensions and the comment with the items found inside
it. It defines the rule IDs with the prefixes `time`, `lat`, `lon`, `sym`,
`b91`, `cmp`, `ext` and `cmt`.

Where a field sits in a packet, and whether a format requires it, is
stated by the format files ([03](03-position.md) to [09](09-other.md)).
The Required column below says whether a part is required inside the
field it belongs to, or names the file that decides.

Conventions used throughout this file:

- A field of fixed length is one token of that length whether or not
  its bytes match. A mismatch is one `syntax` finding at the first byte
  that fails, on the most specific rule at fault, usually the field's
  own ID. A field cut short covers the bytes present, with the finding
  where the first missing byte was expected. Reading continues at the
  next field wherever its start can be told
  ([README section 3](README.md#3-tokenizer-model), Output and Placing a
  finding). An earlier draft left it to the format file whether parsing
  continues after such a field.
- A `value` finding is reported at the first byte of the part whose
  value is out of range (README section 3, Placing a finding).
- Parts of a field (the digits of a latitude, the bytes of an extension)
  are described by byte offset from the start of the field, counting
  from 0. They are not separate tokens unless a row says so.
- Decoder statements in section 9 come from reading the source at the
  commits listed in [README section 4](README.md#4-decoders-consulted).
  None was built or run. A line number points at the start of the
  function or the statement read.

## 2. Timestamps

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="time.dhm"></a>`time.dhm` | Day, hour, minute | Six digits: day of month, hour, minute, two digits each. Then `'z'` (UTC) or `'/'` (local time of the sender); `'/'` gives `discouraged`. | Format file | Fixed, 7 bytes | p. 38/22 |
| <a id="time.hms"></a>`time.hms` | Hour, minute, second | Six digits: hour, minute, second, two digits each. Then `'h'`. Always UTC. | Format file | Fixed, 7 bytes | p. 38/22 |
| <a id="time.mdhm"></a>`time.mdhm` | Month, day, hour, minute | Eight digits: month, day of month, hour, minute, two digits each. UTC. No indicator byte. | Positionless weather reports only ([06](06-weather.md)) | Fixed, 8 bytes | p. 38/22 |

Where a format admits either seven-byte form (its diagram
says "DHM / HMS", p. 50/32), the tokenizer takes seven bytes and lets the
byte at offset 6 choose: `'z'` or `'/'` gives `time.dhm`, `'h'` gives
`time.hms`. This applies the rule for forms that can stand at one place
([README section 3](README.md#3-tokenizer-model)): the indicator byte
selects the form, and the place has no selector rule of its own.
**[agreed]** Any other byte at offset 6, including `'Z'` and `'H'`,
selects no form, and `time.dhm` is the form taken by default: a
`time.dhm` token with a `syntax` finding at offset 6, as decided by the
author. The indicator bytes are the narrowest set the text supports
([README section 3](README.md#3-tokenizer-model), Kinds by situation).
A non-digit in offsets 0 to 5
is a `syntax` finding on the chosen ID. See
[amb.time.indicator](#amb.time.indicator).

When both hold, the one finding is at the first byte that fails, as for
any fixed field (section 1;
[README section 3](README.md#3-tokenizer-model), Placing a finding).

Value ranges. Outside them the finding is `value`, since a range that
the document states or that the unit implies counts as stated
([README section 3](README.md#3-tokenizer-model), Kinds by situation).

| Part | Range | Basis |
|---|---|---|
| Day of month | `01`–`31` | Stated, p. 38/22 |
| Month | `01`–`12` | Stated, p. 38/22 |
| Hour | `00`–`23` | Follows from the 24-hour clock, p. 38/22 |
| Minute, second | `00`–`59` | Implied by the unit (README section 3, Kinds by situation); an earlier draft called it a reading |

Each part is checked when its two digits are present, whatever the
other parts hold: a `syntax` finding elsewhere in the field is an
independent defect and does not suppress it
([README section 3](README.md#3-tokenizer-model), Precedence).

The tokenizer does not check a day against the length of its month: no
form carries a year, and DHM carries no month.

A format that admits only some forms (a status report allows only
`time.dhm` with `'z'`, p. 38/22) states that in its own file.

APRS12c recommends that future implementations transmit only the zulu
form "on the air" (p. 38/22). An earlier draft paraphrased this as a
recommendation that new senders use only UTC, which dropped the limit
to the air. **[agreed]** The local-time form `'/'` is not marked
obsolete; it gives a `discouraged` finding on `time.dhm` at offset 6.
The finding is given whatever the q-construct in the path shows, as
[05-object-item section 2](05-object-item.md#2-object-report) decides
for every discouragement limited to RF or to the air.

## 3. Latitude and longitude

### 3.1 Fields

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="lat"></a>`lat` | Latitude | 8 bytes. Offsets 0–1: degrees, digits. 2–3: whole minutes, digits. 4: `'.'`. 5–6: hundredths of a minute, digits. 7: `'N'` or `'S'`. Offsets 2, 3, 5 and 6 can hold `SP` under [`lat.amb`](#lat.amb). | Format file | Fixed, 8 bytes | p. 39/23 |
| <a id="lon"></a>`lon` | Longitude | 9 bytes. Offsets 0–2: degrees, digits. 3–4: whole minutes, digits. 5: `'.'`. 6–7: hundredths of a minute, digits. 8: `'E'` or `'W'`. Offsets 3, 4, 6 and 7 can hold `SP` under [`lon.amb`](#lon.amb). | Format file | Fixed, 9 bytes | p. 39/23, p. 40/24 |

The hemisphere letters are upper case (p. 39/23). A lower-case
letter, or any other byte, is a `syntax` finding at that offset.

Value ranges (see [amb.lat.range](#amb.lat.range)). The degree ranges
are stated; the others are implied by the unit, minutes up to 59 and a
latitude up to 90 and a longitude up to 180 as a whole, and count as
stated ([README section 3](README.md#3-tokenizer-model), Kinds by
situation):

| Part | No finding | `value` finding |
|---|---|---|
| Latitude degrees | `00`–`90` (stated, p. 39/23) | `91`–`99` |
| Longitude degrees | `000`–`180` (stated, p. 40/24) | `181`–`999` |
| Tens of minutes (offset 2 of `lat`, 3 of `lon`) | `'0'`–`'5'` (implied) | `'6'`–`'9'` |
| Minutes and hundredths when the degrees are `90` (`lat`) or `180` (`lon`) | all `'0'` or `SP` (implied) | any other digit |

They are checked only on digits that are present, also when another
byte of the field gives `syntax` or the field is cut short: those are
independent defects
([README section 3](README.md#3-tokenizer-model), Precedence).

### 3.2 Position ambiguity

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="lat.amb"></a>`lat.amb` | Ambiguity level | No token of its own; a check on `lat`. Offsets 6, 5, 3, 2 of `lat`, in that order, are blanked with `SP` from the first onwards; the number blanked is the level, 0 to 4. A `SP` at one of these offsets while an earlier one in that order holds a digit is a `syntax` finding, at that `SP`. A `SP` anywhere else in `lat` is a `syntax` finding on `lat`. | No | — | p. 40/24, p. 41/25 |
| <a id="lon.amb"></a>`lon.amb` | Longitude blanks | No token of its own; a check on `lon`. Offsets 7, 6, 4, 3 of `lon` follow the same order rule as `lat.amb`. Blanking is allowed but not needed: the latitude's level applies to both. A longitude with more blanks than the latitude's level is a `syntax` finding. | No | — | p. 40/24 |

**[proposed]** The level of a field is the number of `SP` counted from
the first offset of its order up to the first offset that is not `SP`.
The longitude's level is compared with the latitude's; when it is
higher, the byte at fault is the first longitude offset, in its order,
beyond the latitude's level. A latitude whose blanks break the order
still has the level so defined.

`lat` and `lon` each give at most one `syntax` finding, at the first
byte of the field that fails its layout, the order of `lat.amb` or
`lon.amb`, or the longitude's level. It is on `lat.amb` or `lon.amb`
when that byte is a `SP` that breaks the order or exceeds the level, and
on `lat` or `lon` otherwise
([README section 3](README.md#3-tokenizer-model), Placing a finding).
An earlier draft gave every `SP` that breaks the order its own `syntax`
finding.

The levels correspond to a tenth of a minute, one minute, ten minutes and
one degree (p. 40/24, p. 41/25). The contiguity rule and the longitude
rule are the narrowest reading the text supports
([README section 3](README.md#3-tokenizer-model), Kinds by situation);
see [amb.lat.ambiguity](#amb.lat.ambiguity). The degree digits are never
blanked: the text names only the minute digits as the ones replaced,
and its four examples blank only those (p. 40/24).

The document describes the area that an ambiguous position covers in two
incompatible ways (p. 40/24 to p. 41/25). That is a matter for the
decoding layer and does not affect the tokens.

### 3.3 Null position

The position that a station without a fix sends is latitude `0000.00N`,
longitude `00000.00W`, with symbol table `'\'` and code `'.'` (p. 42/26).
**[proposed]** It produces the ordinary `lat`, `sym.table`, `lon` and
`sym.code` tokens and no finding. Recognising it is left to the decoding
layer; see [amb.lat.null](#amb.lat.null).

## 4. Symbol table and code

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="sym.table"></a>`sym.table` | Symbol table identifier, uncompressed position | 1 byte: `'/'` (primary table), `'\'` (alternate table), `'0'`–`'9'` or `'A'`–`'Z'` (alternate table with that character as overlay). | Format file | Fixed, 1 byte | p. 40/24, p. 125/101 |
| <a id="sym.code"></a>`sym.code` | Symbol code | 1 byte, `0x21`–`0x7E`: the codes listed in both tables of Appendix 2 run from `'!'` to `'~'`. | Format file | Fixed, 1 byte | p. 40/24, p. 139/115 to p. 141/117 |

In the uncompressed position the table identifier sits between `lat` and
`lon`, and the code directly after `lon` (p. 40/24). Lower-case
`'a'`–`'j'` are table identifiers only in the compressed block
([`cmp.table`](#cmp.table)); in `sym.table` they are a `syntax` finding
(p. 125/101). Any byte outside the set is a `syntax` finding.

An overlay selects the alternate table and puts the character on the
symbol (p. 125/101, p. 126/102). Only symbols marked as overlay-capable
in Appendix 2 take one, although the end of that appendix says that
every alternate symbol may now take one (p. 141/117). **[agreed]** The
tokenizer does not check the mark: any overlay on an alternate-table
symbol gives no finding. See [amb.sym.overlay](#amb.sym.overlay).

A packet is meant to carry one symbol; when the information field, the
destination address and the source SSID each carry one, the information
field wins (p. 127/103). That comparison spans the header and is not a
check on these fields. The tokenizer reports nothing for it; the
precedence is applied by the decoding layer, as
[amb.src.ssid](01-frame.md#amb.src.ssid) states.

Symbols carried in the destination address or the source SSID are read
in [01-frame.md](01-frame.md); the Mic-E symbol bytes in
[04-mic-e.md](04-mic-e.md).

## 5. Base-91 digits

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="b91.digit"></a>`b91.digit` | Base-91 digit | 1 byte, `0x21`–`0x7B` (`'!'` to `'{'`). Its value is the byte minus 33, 0 to 90. A number of k digits is read most significant digit first. | — | Fixed, 1 byte | p. 34/20, p. 55/37 |

The set ends at `'{'`, the narrowest of the sets the text states
([README section 3](README.md#3-tokenizer-model), Kinds by situation);
see [amb.b91.set](#amb.b91.set) and [err.b91.range](#err.b91.range). `b91.digit` is a rule, not a token: the
fields that use it (the compressed block here, the lower-case
[`cmt.dao`](#cmt.dao) form, the Mic-E altitude in
[04-mic-e.md](04-mic-e.md), [`tlm.b91`](07-telemetry.md#tlm.b91)) report
a byte outside the set as a `syntax` finding on their own ID.

## 6. Compressed position block

### 6.1 Telling the two position forms apart

Where a format admits either position form, the first
byte decides. A digit starts an uncompressed position: `lat`,
`sym.table`, `lon`, `sym.code`, 19 bytes. A byte in the set of
[`cmp.table`](#cmp.table) starts a compressed block. Any other byte is a
`syntax` finding at that byte, and neither form can be delimited.
The finding is on the selector rule of the format file,
such as [`pos.form`](03-position.md#pos.form); an earlier draft named
`cmp.block`. This applies the rule for forms that can stand at one
place ([README section 3](README.md#3-tokenizer-model)): the first byte
selects the form, and when none matches, one `syntax` finding goes on
the selector rule of the place. Source: p. 55/37, p. 125/101. See
[amb.cmp.detect](#amb.cmp.detect).

### 6.2 Fields

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmp.block"></a>`cmp.block` | Compressed position | Table identifier (1), latitude (4), longitude (4), symbol code (1), cs (2), T (1). It takes the place of the uncompressed position and of the data extension that would follow it. Its parts are tokens one level deeper. | Format file | Fixed, 13 bytes | p. 55/37, p. 59/41 |
| <a id="cmp.table"></a>`cmp.table` | Symbol table identifier, compressed | 1 byte: `'/'`, `'\'`, `'A'`–`'Z'`, or `'a'`–`'j'` standing for overlay digits 0–9. Never a digit. | Yes | Fixed, 1 byte | p. 55/37, p. 125/101, p. 126/102 |
| <a id="cmp.lat"></a>`cmp.lat` | Latitude | 4 base-91 digits. Their value is 380926 × (90 − latitude in degrees, north positive). | Yes | Fixed, 4 bytes | p. 55/37, p. 56/38 |
| <a id="cmp.lon"></a>`cmp.lon` | Longitude | 4 base-91 digits. Their value is 190463 × (180 + longitude in degrees, east positive). | Yes | Fixed, 4 bytes | p. 55/37, p. 56/38 |
| <a id="cmp.code"></a>`cmp.code` | Symbol code | As [`sym.code`](#sym.code). Not subject to the base-91 rule. | Yes | Fixed, 1 byte | p. 55/37 |
| <a id="cmp.cs"></a>`cmp.cs` | Course and speed, range, altitude or wind | 2 bytes, `c` then `s`, read as in 6.3. The token carries the ID of the reading chosen. | Yes | Fixed, 2 bytes | p. 56/38 to p. 58/40 |
| <a id="cmp.t"></a>`cmp.t` | Compression type | 1 byte, read as in 6.4. | Yes | Fixed, 1 byte | p. 57/39, p. 58/40 |

A block cut short by the end of the field is a `cmp.block` token over
the bytes present. Each part with a byte present is a token over the
bytes it has and is checked as in a whole block; a part with no byte
present has no token. The part cut short, or else the first part
missing, gives a `syntax` finding where its first missing byte was
expected, unless a byte of it that is present already fails
([README section 3](README.md#3-tokenizer-model), Output and Placing a
finding). An earlier draft gave such a block no part tokens and its one
finding on `cmp.block`.

**[proposed]** Since the step of 6.3 depends on `T`, the `cs` part of a
block without `T` is a `cmp.cs` token, or `cmp.cs.none` when `c` is
`SP`. Its `c` fails only when no step could take it (neither `SP` nor
`'!'`–`'{'`), and its `s` is checked as a base-91 digit, or as a filler
after a `c` of `SP`.

Range of `cmp.lat` and `cmp.lon`. Latitude 90 S and
longitude 180 E both give 68566680 (380926 × 180 = 190463 × 360 =
68566680). Four base-91 digits reach 91⁴ − 1 = 68574960. A value from
68566681 to 68574960 is a `value` finding on the field: the range of a
latitude and a longitude is implied by the unit and counts as stated
([README section 3](README.md#3-tokenizer-model), Kinds by situation).
See [amb.cmp.range](#amb.cmp.range).

### 6.3 Reading the cs bytes

The tokenizer applies the first step whose condition holds
([README section 3](README.md#3-tokenizer-model), Forms that can stand
at one place). See [amb.cmp.cs](#amb.cmp.cs) for the order of the
steps.

| Step | Condition | Token ID | Further bytes | Source |
|---|---|---|---|---|
| 1 | `c` is `SP` | <a id="cmp.cs.none"></a>`cmp.cs.none` | `s` and `T` are fillers: a base-91 digit or `SP`, else `syntax` ([amb.cmp.filler](#amb.cmp.filler)) | p. 56/38, p. 57/39, p. 59/41 |
| 2 | `T` is a base-91 digit and bits 4–3 of `T` − 33 are `1 0` (GGA source) | <a id="cmp.cs.alt"></a>`cmp.cs.alt` | `c` and `s` base-91 digits; together the exponent 91·c + s | p. 58/40 |
| 3 | The report is a weather report ([06](06-weather.md)) and `c` is in `'!'`–`'z'` | <a id="cmp.cs.wind"></a>`cmp.cs.wind` | `s` a base-91 digit; encoded as step 4 | p. 86/66 |
| 4 | `c` is in `'!'`–`'z'` (values 0–89) | <a id="cmp.cs.crs"></a>`cmp.cs.crs` | `s` a base-91 digit | p. 56/38, p. 57/39, p. 153/129 |
| 5 | `c` is `'{'` (value 90) | <a id="cmp.cs.rng"></a>`cmp.cs.rng` | `s` a base-91 digit | p. 57/39 |
| 6 | Otherwise | `cmp.cs` | `syntax` finding at `c` | — |

**[agreed]** Step 2, the GGA bits of `T`, is tested before the range of
`c`. When step 2 applies and `c` is also in `'!'`–`'z'`, the course and
speed range of step 4, the token is `cmp.cs.alt` with an `ambiguous`
finding at `c`, since a reading that lets the range of `c` decide
alone, without consulting `T`, would take the bytes as course and
speed.

The same holds when `c` is `'{'`, the range value of step 5:
the token is `cmp.cs.alt`, with an `ambiguous` finding at `c`, since
that reading would take the bytes as a range
([README section 3](README.md#3-tokenizer-model), applied in
[amb.cmp.cs](#amb.cmp.cs)). The `cs` token gives at most one `syntax`
finding, at the first of `c` and `s` that fails (README section 3,
Placing a finding). A `syntax` finding at `s` or the `value` finding of
6.4 at `T` does not suppress either `ambiguous` finding: both readings
give it, of the same kind at the same offset, so it does not count
against the other reading (README section 3, Which findings are the
other reading's own).

### 6.4 The T byte

When `c` is not `SP`, `T` is a base-91 digit; otherwise a `syntax`
finding. Its value `T` − 33 holds the fix state (bit 5), the NMEA source
(bits 4–3) and the origin of the compression (bits 2–0); bits 7–6 are
unused and zero (p. 57/39). A `T` from `'a'` to `'{'`, whose value has
bit 6 set, is a `value` finding, as a value outside that stated range
([README section 3](README.md#3-tokenizer-model), Kinds by situation).
See [amb.cmp.t](#amb.cmp.t).
The origin codes marked "tbd" give no finding.

When `c` is `SP`, `T` carries no meaning (p. 57/39) and is a filler as in
step 1 of 6.3.

### 6.5 What follows the block

**[proposed]** No data extension follows a compressed block. The bytes
after `T` are what the format puts there, usually a comment
([`cmt.text`](#cmt.text)). When the bytes directly after `T` match an
extension form that 7.1 would try at a slot of the same report, with no
`syntax` or `value` finding of that form, they get an `ambiguous`
finding at their first byte and stay comment text; see
[amb.ext.compressed](#amb.ext.compressed). An earlier draft gave the
finding for any form of 7.2; a form that 7.1 would not try there, or
one that fails, is not an extension under any reading, so it does not
make the bytes ambiguous
([README section 3](README.md#3-tokenizer-model)).

That finding is on the rule this reading gives the first byte of the
run, as in [amb.ext.count](#amb.ext.count)
([README section 3](README.md#3-tokenizer-model), Placing a finding).

## 7. Data extensions

### 7.1 The extension slot

- The slot is the bytes directly after the symbol code of
  an uncompressed position, in the formats whose files provide one. When
  they match one of the forms in 7.2, they are read as that extension.
  When they match none, the slot is empty and the comment starts there.
  Being an extension, or not, gives no finding of its own. This applies
  the rule for forms that can stand at one place
  ([README section 3](README.md#3-tokenizer-model)): the extension, the
  more specific form, is tried before the comment text that also covers
  its bytes, and the overlap that every extension carries gives no
  finding. See [amb.ext.slot](#amb.ext.slot). The slot bytes on which the readings
  of another entry divide differently get the `ambiguous` findings that
  entry gives: the literal-letter case and the descriptor-only case
  below, [amb.ext.csespd](#amb.ext.csespd) and
  [amb.ext.phg](#amb.ext.phg)
  ([README section 3](README.md#3-tokenizer-model)). An earlier draft
  also listed [amb.pos.ext](03-position.md#amb.pos.ext), which no
  longer gives a finding.
- Each `ambiguous` finding of this section and of 7.3 is on the rule
  this reading gives the first byte of the bytes in question: the
  extension's own rule where this reading reads them as an extension,
  and [`cmt.text`](#cmt.text) where it reads them as comment text
  ([README section 3](README.md#3-tokenizer-model), Placing a finding).
- The forms are tried in this order, and the first match is taken: a
  form that the symbol or the kind of report selects first, then the
  longer form before the one that covers its start
  ([README section 3](README.md#3-tokenizer-model), Forms that can
  stand at one place):
  1. **[agreed]** In an object or item report whose symbol is table
     `'\'` with code `'l'`: [`ext.area`](#ext.area), and nothing else.
     Bytes that do not fit it give `syntax`, as
     [05-object-item.md](05-object-item.md#amb.area.symbol) decides. In a
     position report the descriptor is never read
     ([amb.pos.ext](03-position.md#amb.pos.ext)), and the slot is tried
     as in step 3.
  2. **[proposed]** When [06-weather.md](06-weather.md) reads the
     report as a weather report: [`ext.dirspd`](#ext.dirspd), and
     nothing else.
  3. Otherwise [`ext.csespd`](#ext.csespd), [`ext.phgr`](#ext.phgr),
     [`ext.phg`](#ext.phg), [`ext.rng`](#ext.rng), [`ext.dfs`](#ext.dfs).
     PHGR comes before PHG because it is the longer match.
- **[proposed]** A slot holds one extension. Bytes after it that match
  another extension are comment text, with an `ambiguous` finding where
  [amb.ext.count](#amb.ext.count) gives one. Exceptions are
  [`ext.brgnrq`](#ext.brgnrq) (7.4) and storm data, which
  [06-weather.md](06-weather.md) reads.
- **[agreed]** Seven slot bytes with a literal `'T'` at offset 0, `'/'`
  at offset 3 and `'C'` at offset 4, the spelling of the descriptor's
  name, and digits at offsets 1, 2, 5 and 6, get an `ambiguous` finding
  at the first byte of the slot, in any report, because a reading that
  takes those letters as literal would read them as `ext.area`. The
  bytes stay what this reading makes them. In an object or item report
  with symbol `\l` they fail step 1 and give its `syntax` finding,
  which alone is given
  ([README section 3](README.md#3-tokenizer-model), Precedence). See
  [amb.ext.area](#amb.ext.area).
- In an object or item report whose symbol is not `\l` and which is
  not read as a weather report, seven slot bytes after an uncompressed
  position that fit only `ext.area`, with a colour of `'1'` and
  `'0'`–`'5'` (10 to 15), so that they are no course and speed or other
  form of step 3, are comment text with an `ambiguous` finding at their
  first byte, under the condition of
  [amb.area.symbol](05-object-item.md#amb.area.symbol): a reading in
  which the bytes decide would take them as a descriptor
  ([README section 3](README.md#3-tokenizer-model)).
- **[proposed]** There is no slot after a compressed block (6.5).

### 7.2 Fields

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="ext.csespd"></a>`ext.csespd` | Course and speed | Course (3 bytes), `'/'`, speed (3 bytes). Each 3-byte part is three digits, `'...'`, or three `SP`. | Format file | Fixed, 7 bytes | p. 45/27; parts: [amb.ext.csespd](#amb.ext.csespd) |
| <a id="ext.dirspd"></a>`ext.dirspd` | Wind direction and speed | Same layout as `ext.csespd`. | Weather reports ([06](06-weather.md)) | Fixed, 7 bytes | p. 45/27, p. 85/65 |
| <a id="ext.phg"></a>`ext.phg` | Power, height, gain, directivity | `'PHG'`, then power code `p` (digit), height code `h` (`0x30`–`0x7E`), gain code `g` (digit), directivity code `d` (digit). | Format file | Fixed, 7 bytes | p. 46/28; `h`: [amb.ext.phg](#amb.ext.phg) |
| <a id="ext.phgr"></a>`ext.phgr` | PHG with beacon rate | As `ext.phg`, then a rate byte `r` (`'0'`–`'9'`, or `'A'`–`'Z'` for 10 and up), then `'/'`. | Format file | Fixed, 9 bytes | p. 46/28; UAP 3.2; [amb.ext.phg](#amb.ext.phg) |
| <a id="ext.rng"></a>`ext.rng` | Pre-calculated range | `'RNG'`, then four digits: range in miles, zero-padded. | Format file | Fixed, 7 bytes | p. 47/29 |
| <a id="ext.dfs"></a>`ext.dfs` | Omni DF signal strength | `'DFS'`, then strength `s` (digit), then `h`, `g`, `d` as in `ext.phg`. | Format file | Fixed, 7 bytes | p. 47/29, p. 48/30; `h`: [amb.ext.phg](#amb.ext.phg) |
| <a id="ext.area"></a>`ext.area` | Area object descriptor | Type `T` (digit), latitude offset `yy` (2 digits), colour (2 bytes: `'/'` and a digit for colours 0–9, or `'1'` and `'0'`–`'5'` for 10–15), longitude offset `xx` (2 digits). The letters of the name `Tyy/Cxx` are placeholders, not literals. | Only with symbol `\l`; [05](05-object-item.md) decides | Fixed, 7 bytes | p. 49/31, p. 78/60; [amb.ext.area](#amb.ext.area) |
| <a id="ext.brgnrq"></a>`ext.brgnrq` | DF bearing and number, range, quality | `'/'`, bearing (3 digits), `'/'`, then `N`, `R`, `Q`, one digit each. | DF reports ([03](03-position.md)) | Fixed, 8 bytes | p. 45/27, p. 48/30, p. 49/31, p. 52/34, p. 53/35 |

Upper case is significant: `'phg'`, `'rng'` and `'dfs'` match nothing and
are comment text (UAP 5.9).

### 7.3 Values

Outside these the finding is `value`, for a range that the document
states or the unit implies, or a code outside a table
([README section 3](README.md#3-tokenizer-model), Kinds by situation):

| ID | Part | No finding | `value` finding | Basis |
|---|---|---|---|---|
| `ext.csespd` | Course | `000`–`360`, `'...'`, three `SP` | `361`–`999` | p. 45/27 gives 001–360 and 000 for unknown |
| `ext.csespd` | Speed | Any | — | No range stated |
| `ext.dirspd` | Direction | As course | `361`–`999` | p. 45/27 |
| `ext.phg`, `ext.phgr`, `ext.dfs` | `d` | `'0'`–`'8'` | `'9'` | The code table on p. 46/28 stops at 8 |
| `ext.brgnrq` | Bearing | `000`–`360` | `361`–`999` | Implied by the unit; an earlier draft called it a reading |

**[proposed]** A course and speed whose two parts are of different kinds
(digits in one, dots or spaces in the other, as in `088/...`) is read as
`ext.csespd` with an `unstated` finding. **[proposed]** Digits, dots and
spaces are three kinds, so `.../   ` mixes kinds too.

Such a course and speed also gets an `ambiguous` finding at its first
byte, since a reading that takes only the listed forms would read the
seven bytes as comment text, unless the course gives the `value`
finding above; then there is no `ambiguous` finding, and the `unstated`
one, on an independent defect, stays. A seven-byte slot with `'/'` at
offset 3 and only digits, dots and spaces, in which one part mixes
kinds, is comment text, with an `ambiguous` finding at its first byte
unless its course part is three digits above 360
([README section 3](README.md#3-tokenizer-model), applied in
[amb.ext.csespd](#amb.ext.csespd)).

An `ext.phg`, `ext.phgr` or `ext.dfs` whose `h` is not a digit gets an
`ambiguous` finding at its first byte, under the condition of
[amb.ext.phg](#amb.ext.phg), unless its `d` gives the `value` finding
above (README section 3, Precedence).

### 7.4 Bearing and NRQ

**[agreed]** `ext.brgnrq` is read only directly after an `ext.csespd`
of a report whose symbol is table `'/'` with code `'\'`. With that
symbol, 8 bytes of its shape directly after any other extension are
comment text with an `ambiguous` finding at their first byte.

That finding is given when their bearing is at most 360; with a larger
bearing the reading that would take them as bearing and NRQ gives
`value` and does not count. Under any other symbol the 8 bytes are
comment text; when they directly follow an `ext.csespd` and fit
`ext.brgnrq` with a bearing of at most 360, the finding is `ambiguous`
at their first byte
([README section 3](README.md#3-tokenizer-model), applied in
[amb.ext.brgnrq](#amb.ext.brgnrq)). Whether a DF report requires the
field is stated in [03-position.md](03-position.md#3-df-reports).

## 8. Comment

### 8.1 Comment field

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmt.text"></a>`cmt.text` | Comment | Free text from the end of the last data field or extension to the end of the information field. No separator before it. Bytes: printable ASCII `0x20`–`0x7E`, and well-formed UTF-8 sequences. An empty comment produces no token. | No | End of the information field ([01](01-frame.md)) | p. 34/20 |

- **[proposed]** A byte outside the set, including `0x0D` or `0x0A`
  anywhere in the comment and a byte that does not form well-formed
  UTF-8, is a `syntax` finding. See [amb.cmt.bytes](#amb.cmt.bytes).
- The comment gives one such finding, at the first byte outside the
  set, and the token still runs to the end of the information field
  ([README section 3](README.md#3-tokenizer-model), Output and Placing
  a finding). An earlier draft gave a finding at every byte outside the
  set.
- The length limit of a comment is given by the format file, in bytes
  (the diagrams count bytes, p. 50/32). The bytes counted are those of
  the `cmt.text` token, items found inside it included, less those of
  its `cmt.dao` tokens (next item). A longer comment is a `value`
  finding at the first byte past the limit (README section 3, Length
  limits and Kinds by situation). See [amb.cmt.length](#amb.cmt.length).
- **[proposed]** p. 35/21 is the page that exempts the DAO: it lets the
  option extend beyond a "viewable" limit of 57 bytes, since legacy
  systems do not use those bytes. That limit is not one of the comment
  limits of the diagrams, so reading it as an exemption from them is a
  reading.

### 8.2 Items found inside a comment

- Each item is looked for only in the fields that its own chapter of
  APRS12c names for it, listed below; bytes of its shape in any other
  field are text, with no finding
  ([README section 3](README.md#3-tokenizer-model), Where comment items
  are looked for). An earlier draft searched every item below over the
  whole `cmt.text` token of any format, and let a format name further
  free-text fields to be searched the same way.
- **[proposed]** Within those fields each item is searched for
  independently of the others, and each occurrence it takes is a token
  one level deeper than the field.
- **[proposed]** When occurrences of two items overlap, both are
  recorded, each with an `ambiguous` finding.
- An item that the document lets stand anywhere in its field, as it
  does the altitude, the DAO and `'!x!'`, is recorded at every
  occurrence, and two or more occurrences in one field give an
  `ambiguous` finding on each. An item that the document places at a
  fixed spot is read there only, and once; later bytes of its shape
  are text, with an `ambiguous` finding where the reading that takes
  them as the item accepts the whole field
  ([README section 3](README.md#3-tokenizer-model), Fixed spots and
  repeats). An earlier draft gave the repetition rule as a proposal of
  this section, for every item.

Where each item is looked for:

| Item | Fields | Place in the field | Source |
|---|---|---|---|
| [`cmt.alt`](#cmt.alt), [`cmt.alt.neg`](#cmt.alt.neg) | The comment of a position report ([`pos.cmt`](03-position.md#pos.cmt), [`pos.cmpcmt`](03-position.md#pos.cmpcmt), [`df.cmt`](03-position.md#df.cmt)), the Mic-E free text ([04-mic-e section 5](04-mic-e.md#5-status-text)), [`obj.cmt`](05-object-item.md#obj.cmt), [`item.cmt`](05-object-item.md#item.cmt), [`tlm.cmt`](07-telemetry.md#tlm.cmt). | Anywhere | p. 43/27 |
| [`cmt.dao`](#cmt.dao) | The position comments of the row above: all of them but `tlm.cmt`. | Anywhere | p. 35/21; p. 76/58, p. 80/62 |
| [`cmt.noarchive`](#cmt.noarchive) | Every free-text field, the information field searched ([amb.cmt.noarchive](#amb.cmt.noarchive)). | Anywhere | p. 110/86 |
| [`tlm.b91`](07-telemetry.md#tlm.b91) | `pos.cmt`, `pos.cmpcmt`, `df.cmt` and the Mic-E free text ([07-telemetry section 3](07-telemetry.md#3-base-91-comment-telemetry)). | After the free text | p. 88/68 |
| Data extensions ([7.1](#71-the-extension-slot)) | The slot after an uncompressed position; the start of the Mic-E free text ([amb.mice.extension](04-mic-e.md#amb.mice.extension)). | Fixed | p. 45/27 |
| Frequencies (`freq.*`) | As [09-other section 7](09-other.md#7-frequency-specification) lists. | Start | p. 113/89 |
| [`area.corridor`](05-object-item.md#area.corridor), [`obj.signpost`](05-object-item.md#obj.signpost) | `obj.cmt` and `item.cmt` of the symbols of [05-object-item sections 4 and 5](05-object-item.md#4-area-objects). | Start | p. 80/62 |

The altitude and the DAO are read in the comment of an object or item
report because p. 76/58 lets that comment carry the data of the comment
section of chapter 5, and p. 80/62 calls these reports object position
reports: **[agreed]** an object or item comment counts as a position
comment. **[agreed]** A telemetry report has no position, so a DAO
shape in `tlm.cmt` is text, with no finding; the altitude is still read
there, since p. 43/27 places it in the comment without naming a
format. The extension-shaped runs that
[amb.ext.count](#amb.ext.count) reports are looked for as that entry
states. Weather and storm data are read by
[06-weather.md](06-weather.md), and the parts of a Mic-E status text by
[04-mic-e.md](04-mic-e.md). Whether the comment of a Maidenhead beacon,
[`grid.cmt`](03-position.md#grid.cmt), holds the altitude or the DAO
is open ([03-position section 9](03-position.md#9-open-items)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cmt.alt"></a>`cmt.alt` | Altitude | `'/A='`, then six digits: feet. The byte after them is not a digit. | No | Fixed, 9 bytes | p. 43/27; UAP 3.4 |
| <a id="cmt.alt.neg"></a>`cmt.alt.neg` | Negative altitude | `'/A=-'`, then five digits. The byte after them is not a digit. | No | Fixed, 9 bytes | p. 43/27; UAP 3.4 |
| <a id="cmt.dao"></a>`cmt.dao` | Datum and added precision | `'!'`, datum byte `D`, latitude byte `A`, longitude byte `O`, `'!'`, in one of the forms of 8.3. | No | Fixed, 5 bytes | p. 35/21 to p. 37/23; UAP 3.5 |
| <a id="cmt.noarchive"></a>`cmt.noarchive` | No-archive marker | `'!x!'`, with a literal lower-case `'x'`. | No | Fixed, 3 bytes | p. 110/86, p. 155/131; UAP 3.7 |

**[proposed]** `cmt.alt`: both IDs count as the same item for the
repetition rule. The negative form is described in APRS12c as outside
the official standard (p. 43/27); its own ID marks it, and it gets no
finding. See [amb.cmt.alt](#amb.cmt.alt).

`'/A='` declares the altitude
([README section 3](README.md#3-tokenizer-model), Classes that a
keyword declares), so a `'/A='` that does not start either form, and a
form followed by a further digit, give a `syntax` finding on `cmt.alt`
at the `'/'`. **[proposed]** The bytes of such a run stay comment
text, with no `cmt.alt` token. An earlier draft carried the `syntax`
finding as part of the proposal of the paragraph above, and listed in
section 11 whether `'/A='` is a keyword or the altitude a form
recognised by its shape alone, which would have left such a run as
text with no finding; the author decided that it is a keyword.

`cmt.dao`: every candidate is recorded; more than one gives an
`ambiguous` finding on each, at the candidate's first `'!'`, under the
conditions of [amb.cmt.dao](#amb.cmt.dao)
([README section 3](README.md#3-tokenizer-model), Fixed spots and
repeats). A single candidate gives no finding, wherever it stands in
the comment. An earlier draft carried this paragraph as a proposal of
its own. An
earlier draft also gave `ambiguous` to a single candidate followed by
further bytes of the comment; that rested on taking a DAO only at the
end of the comment, which contradicts p. 35/21 and was dropped
([amb.cmt.dao](#amb.cmt.dao)). The order of a DAO and a base-91
telemetry block is checked by [`tlm.b91`](07-telemetry.md#tlm.b91).

**[agreed]** `'!x!'` is searched for in the whole information field. A
match that lies inside a free-text field (comments and the text fields
that format files name) is a `cmt.noarchive` token. Any other match is
no token and gets an `ambiguous` finding on `cmt.noarchive` at its
first `'!'`. See [amb.cmt.noarchive](#amb.cmt.noarchive).

### 8.3 DAO forms

The case of the datum letter selects the precision: upper case adds one
decimal digit to each coordinate, lower case adds a base-91 digit, and
two `SP` add nothing (p. 35/21, p. 36/22). Digits `'0'`–`'9'` name local
datums (p. 36/22).

**[proposed]** A five-byte run `'!'` `D` `A` `O` `'!'` is a `cmt.dao`
candidate when it fits a row of this table. See
[amb.cmt.dao](#amb.cmt.dao).

| `D` | `A` and `O` | Result |
|---|---|---|
| `'A'`–`'Z'` | Both digits | `cmt.dao` |
| `'a'`–`'z'` | Both base-91 digits | `cmt.dao` |
| Letter or digit | Both `SP` | `cmt.dao` |
| `'0'`–`'9'` | Both base-91 digits | `cmt.dao`, `unstated` finding |
| Other base-91 digit | Both `SP` | `cmt.dao`, `unstated` finding |
| Anything else | | Not a candidate; comment text |

A run with one `SP` and one precision byte is outside every form of
p. 35/21 to p. 36/22, which makes `A` and `O` base-91 digits or both
`SP`. It is not a candidate: in the comment it is text, with no finding
([README section 3](README.md#3-tokenizer-model), Kinds by situation).
An earlier draft made it a candidate with an `unstated` finding when
the other byte fitted the datum's mode.

## 9. Ambiguities

<a id="amb.time.indicator"></a>
### amb.time.indicator

**Open.** APRS12c gives the three forms, the indicator bytes and the
ranges of day and month (p. 38/22). For hour, minute and second it says
only that the clock is 24-hour. It does not say what a receiver does
with another indicator byte or an out-of-range value.

**Readings.** (a) Exact indicator bytes; out-of-range parts are errors.
(b) Indicator bytes in either case. (c) Any seventh byte; the timestamp
is dropped when it cannot be decoded.

**Reading taken.** (a). P. 38/22 shows the indicator bytes in lower
case and gives no allowance for another case, so `'Z'` and `'H'` are
not the indicator of any form
([README section 3](README.md#3-tokenizer-model), Letter case). The
timestamp's place is fixed, so these bytes are not text either: no form
matches, and `time.dhm` is the form taken by default, with a `syntax`
finding at offset 6 (section 2; README section 3, Forms that can stand
at one place). Any other byte at offset 6 is read the same way. Reading
(b) is not taken because it folds the case where the document gives no
allowance (Letter case); (c) is wider still, and the narrowest reading
the text supports is taken (Kinds by situation). Out-of-range parts are
a `value` finding (section 2). The minute and second ranges are implied
by the unit and count as stated (Kinds by situation). An earlier draft
gave (a) as the narrowest of the three readings only, without the
Letter case rule.

**In the bytes.** Visible, since (b) or (c) would accept the bytes. The
`syntax` or `value` finding of the reading alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).
Where (a) gives no finding, (b) and (c) read the seven bytes the same
way, so there is no `ambiguous` finding (README section 3).

| Decoder | Reads | Where |
|---|---|---|
| FAP | Six digits and `z`, `h` or `/`; checks day 1–31, hour, minute and second. A bad stamp becomes 0 with a warning; the seven bytes are skipped either way and the position is parsed. | `_parse_timestamp`, FAP.pm:627, 631, 644, 677; `parseaprs`, FAP.pm:2607–2611 |
| Dire Wolf | Six digits and `z`, `/` or `h`; no range check. | `get_timestamp`, src/decode_aprs.c:3961, 3981 |
| aprslib | Six digits and any seventh byte; `h`, `z` and `/` are decoded, other bytes and impossible dates give 0. In a status report only `z` is consumed. | `parse_timestamp`, aprslib/parsing/common.py:77, 80, 87, 101, 105 |
| Xastir | Six digits and `z`, `Z`, `/`, `h` or `H`; eight digits for MDHM; no range check. | `extract_time`, src/db.c:8071, 8089, 8111 |
| aprs-parser-rs | `z` or `Z`, `h` or `H`, `/`; with `/` the six bytes before it are not checked. | `Timestamp::try_from`, src/components/timestamp.rs:80, 85, 97 |
| pdn-aprs | Exact `z`, `/`, `h`; a separate range check. | `Timestamp::parse` and `is_valid`, src/timestamp.rs:25, 53 |

**Corpus question.** Which bytes occur at offset 6 of seven-byte
timestamps, and how many timestamps have a part outside the ranges of
section 2?

<a id="amb.lat.range"></a>
### amb.lat.range

**Open.** The degree ranges are stated (p. 39/23, p. 40/24); the minute
range and a degree value of 90 or 180 with non-zero minutes are not. The
hemisphere letters are stated as upper case, but no receiver action is
given for others.

**Readings.** (a) Minutes up to 59; 90 and 180 only with zero minutes;
upper case only. (b) Minutes up to 99. (c) Lower-case hemisphere
accepted.

**Reading taken.** (a), as in 3.1, the narrowest of the three, with
the ranges that the unit implies counted as stated
([README section 3](README.md#3-tokenizer-model), Kinds by situation):
range departures are `value` findings, case departures `syntax`
findings.

**In the bytes.** Visible, and reported as those `value` and `syntax`
findings, which alone are given
([README section 3](README.md#3-tokenizer-model), Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP | Tens of minutes `0`–`7` or space; lower-case hemisphere accepted; rejects latitude degrees above 89 and longitude degrees above 179, so 90 and 180 are rejected. | `_normalpos_to_decimal`, FAP.pm:1514, 1541 |
| Dire Wolf | Tens of minutes `0`–`5` or space; lower-case hemisphere accepted with a warning; longitude hundreds digit `0` or `1`; no other degree bound in the functions read. | `get_latitude_8`, src/decode_aprs.c:3651, 3712; `get_longitude_9`, :3784 |
| aprslib | Lower-case hemisphere accepted; rejects latitude degrees above 89 and longitude above 179; the minute check is commented out. | `parse_normal`, aprslib/parsing/position.py:140, 176–190 |
| Xastir | Hemisphere compared after upper-casing; no range check in the function. | `extract_position`, src/db.c:6953 |
| aprsc | Lower case accepted; degrees above 89 or 179 and minutes above 59 rejected. | `parse_aprs_uncompressed`, src/parse_aprs.c:811, 857–871 |
| aprs-parser-rs | Upper case only; latitude beyond 90 rejected. | `Latitude::parse_uncompressed`, src/components/lonlat.rs:136, 141; `Latitude::new`, :85 |
| pdn-aprs | Minutes of 60 or more and latitude beyond 90 or longitude beyond 180 rejected; lower case a defect tolerated by option. | `uncompressed`, src/position.rs:52, 85, 91, 98, 132, 137 |

**Corpus question.** How many uncompressed positions have minutes of 60
or more, degrees above the range, degrees at 90 or 180 with non-zero
minutes, or a hemisphere byte other than the four upper-case letters?

<a id="amb.lat.ambiguity"></a>
### amb.lat.ambiguity

**Open.** Blanking is described for the minute digits of the latitude
and shown by four latitude examples, each blanking from the right
(p. 40/24). Not stated: blanks that are not contiguous, blanks in degree
digits (the text names only the minute digits), longitude blanks that
differ from the latitude's.

**Readings.** (a) Latitude blanks contiguous from the right; longitude
blanks contiguous and not beyond the latitude's level. (b) Latitude level
only; longitude blanks ignored. (c) Blanks anywhere, read as zero.

**Reading taken.** (a), as in 3.2, the narrowest of the three
([README section 3](README.md#3-tokenizer-model), Kinds by situation).
A departure is a `syntax` finding.

**In the bytes.** Visible, and reported as that `syntax` finding, which
alone is given ([README section 3](README.md#3-tokenizer-model),
Precedence). A longitude with fewer blanks than the latitude's level is
allowed: p. 40/24 states that blanks in the longitude are allowed but
not needed, and its own example has none. It matches every reading
listed and gives no finding. Requiring the longitude to have as many
blanks as the latitude is not a reading of the document, since it
contradicts that statement; it is decoder behaviour (aprslib, in the
table below), which gives no finding (README section 3). An earlier
draft listed it as reading (b) and left open whether it made such a
longitude visible.

| Decoder | Reads | Where |
|---|---|---|
| FAP | Latitude blanks contiguous from the right, else error. Longitude blanks rejected at level 0; at levels 1–3 a blank among the kept longitude digits is rejected; blanked positions are not checked. | `_normalpos_to_decimal`, FAP.pm:1550, 1561, 1567–1597 |
| Dire Wolf | A blank accepted at each minute position independently and read as zero. | `get_latitude_8`, src/decode_aprs.c:3608, 3651–3705 |
| aprslib | Blanks anywhere in the minutes; the count in latitude and longitude has to be equal. | `parse_normal`, aprslib/parsing/position.py:140, 159–162 |
| Xastir | Level from the leftmost blank among the latitude minute digits; the digits after it, and the longitude digits the level covers, are overwritten. Longitude blanks are accepted at any minute digit and not compared with the latitude. | `extract_position`, src/db.c:6960–6970, 6979–7004 |
| aprsc | Each blank, in latitude or longitude, replaced on its own by a fixed digit; no pattern or level check. | `parse_aprs_uncompressed`, src/parse_aprs.c:835–843 |
| aprs-parser-rs | Once a blank is seen, the rest of the latitude has to be blank; the units digit of the degrees can be blanked too (a fifth level). Longitude digits covered by the level are overwritten, whatever they hold. | `Latitude::parse_uncompressed`, src/components/lonlat.rs:147–162; `Precision::from_num_digits`, :50; `Longitude::parse_uncompressed`, :298 |
| pdn-aprs | Latitude blanks contiguous from the right. A longitude blank is accepted only at a digit the latitude's level covers; contiguity within the longitude is not checked. | `uncompressed`, src/position.rs:62–71, 118–122 |

**Corpus question.** What is the joint distribution of blank patterns in
latitude and longitude, and how many are not contiguous, blank a degree
digit, or blank more in the longitude than in the latitude?

<a id="amb.lat.null"></a>
### amb.lat.null

**Open.** The null position is given with symbol `\.` (p. 42/26). Not
stated: zero coordinates with another symbol or with `'S'` or `'E'`, and
how to tell the null position from a station really at 0° 0′.

**Readings.** (a) The exact 19 bytes are the null position. (b) Any zero
latitude and longitude is null. (c) The tokenizer does not distinguish.

**Reading taken.** **[proposed]** (c): no token or finding of its own;
recognition belongs to the decoding layer.

**In the bytes.** Decided silently. Readings (a) and (b) would
classify all-zero coordinates as the null position, but every such
position carries the question, and the bytes of one packet cannot tell
a null position from a station at 0° 0′
([README section 3](README.md#3-tokenizer-model), on an ambiguity that
every instance of a form carries). No finding.

| Decoder | Reads | Where |
|---|---|---|
| FAP, Dire Wolf, aprslib | No special case found in the position functions read. | Functions cited in [amb.lat.range](#amb.lat.range) |
| aprsc | Rejects a position at 0/0 whatever its symbol, and a few points near the poles and on the equator at 90° of longitude. | `pbuf_fill_pos`, src/parse_aprs.c:75 |

**Corpus question.** With which symbols and hemisphere letters do
all-zero positions occur?

<a id="amb.sym.overlay"></a>
### amb.sym.overlay

**Open.** Overlays are allowed only on alternate-table symbols marked as
overlay-capable in Appendix 2 (p. 124/100, p. 126/102, p. 139/115). The
mark set has changed since (p. 154/130 lists an "overlayable symbols
subset"), and the end of Appendix 2 says that since 2007 every
alternate symbol may take an overlay (p. 141/117), which leaves the
marks of the same appendix without force. No receiver action is stated.

**Readings.** (a) No check. (b) A `value` finding when the symbol is not
marked. (c) A `syntax` finding.

**Reading taken.** **[agreed]** (a): overlay capability by the
Appendix 2 marks is not checked, because p. 141/117 lets every
alternate symbol take an overlay since 2007. The same holds for the
overlay of a [`dest.sym`](01-frame.md#dest.sym) destination.

**In the bytes.** Decided by the reading, with no finding: no
`ambiguous`, `value` or `syntax` finding is given for any overlay on an
alternate-table symbol. The marks that (b) and (c) test are the ones
p. 141/117 sets aside, and the tokenizer does not carry them, so it
does not look for the cases where the readings would differ. Readings
(b) and (c) would themselves report a finding on such a symbol, so
under the test of [README section 3](README.md#3-tokenizer-model) they
would not make the bytes ambiguous either.

| Decoder | Reads | Where |
|---|---|---|
| FAP | Checks the table byte set only; symbol code `'!'`–`'{'` or `'}'`. | `_normalpos_to_decimal`, FAP.pm:1514, 1534; `_compressed_to_decimal`, :1893 |
| Dire Wolf | Compressed table byte set checked; an invalid one is replaced by `'/'`. | `decode_compressed_position`, src/decode_aprs.c:3546 |
| aprslib | Table byte set by regex; symbol code `'!'`–`'~'` uncompressed, `'!'`–`'{'` or `'}'` compressed. | `parse_normal`, aprslib/parsing/position.py:140; `parse_compressed`, :89 |
| pdn-aprs | Table byte set by form; symbol code `'!'`–`'~'`. | `symbol`, src/position.rs:262 |

None of the functions read checks overlay capability.

**Corpus question.** Which table and code pairs occur with an overlay
byte, and how many of the codes are not overlay-capable in Appendix 2?

<a id="amb.cmp.detect"></a>
### amb.cmp.detect

**Open.** A compressed block is recognised by a table identifier where a
digit would be (p. 55/37). A first byte that is neither is not
addressed.

**Readings.** (a) Digit, table set, or error. (b) Digit, else compressed.

**Reading taken.** (a), as in 6.1, by the rule for forms that can
stand at one place: the first byte selects the form, and a byte that
selects none gives one `syntax` finding on the selector rule
([README section 3](README.md#3-tokenizer-model)). Reading (b) would
make the compressed form a default that takes any byte, which is also
wider than the table set the text states (Kinds by situation).

**In the bytes.** Visible, and reported as the `syntax` finding of 6.1,
which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP | Digit: uncompressed; `'/'`, `'\'`, `'A'`–`'Z'` or `'a'`–`'j'`: compressed; `'!'`: Ultimeter weather; else error. | `parseaprs`, FAP.pm:2616, 2631, 2648, 2653 |
| Dire Wolf | Digit: uncompressed; else compressed, with the table checked inside. | `aprs_ll_pos`, src/decode_aprs.c:926; `decode_compressed_position`, :3546 |
| aprslib | Tries the compressed pattern first (table set at the start), then uncompressed. | `parse_position`, aprslib/parsing/position.py:47–59 |
| Xastir | Tries uncompressed first, then compressed with the table set checked. | src/db.c:9530–9533; `extract_comp_position`, :7164 |
| aprs-parser-rs | Digit: uncompressed; else compressed, table unchecked. | `Position::decode`, src/components/position.rs:75 |
| pdn-aprs | As reading (a). | `decode`, src/position.rs:37 |

**Corpus question.** Which first bytes occur where a position starts, as
digit, table set, or other?

<a id="amb.cmp.cs"></a>
### amb.cmp.cs

**Open.** The rules for `c` are given first, by range, and the GGA rule
from `T` after (p. 56/38 to p. 58/40); the order is not stated. The
altitude example has `c` = `'S'`, inside the course range (p. 58/40,
p. 59/41). The weather diagrams put wind in `cs` (p. 86/66).

**Readings.** (a) `c` = `SP`, then the GGA bits, then the range of `c`.
(b) The document's literal order: the range of `c` decides alone,
course and speed for `'!'`–`'z'` and range for `'{'`, and the `T` byte
is not consulted for `cs`; `T` is still the compression type byte of
6.4. (c) GGA first, before the `SP` test.

An earlier draft described (b) as the range of `c` first, with the GGA
bits tested only inside the course range. That is Xastir's behaviour
(table below), not a reading of the text, which gives the GGA rule
without limiting it to part of the range.

**Reading taken.** **[agreed]** (a), as in 6.3: `T` is tested before
the range of `c`. `c` = `SP` comes first because `T` has no meaning then
(p. 57/39). The weather step comes before the course step: the report
being a weather report selects it, and a form that a marker selects is
tried first ([README section 3](README.md#3-tokenizer-model), Forms
that can stand at one place).

**In the bytes.** Visible: (a) and (b) differ when the GGA bits of `T`
are set and `c` lies in the course and speed range `'!'`–`'z'`, which
the bytes show. Those blocks get `cmp.cs.alt` with an `ambiguous`
finding at `c` (6.3). They also differ when the GGA bits are set and
`c` is `'{'`: (a) reads altitude and (b) a range. Those blocks also get
`cmp.cs.alt` with an `ambiguous` finding at `c`. With `c` = `SP` and
the GGA bits set, (c) would read altitude from a `c` that is not a
base-91 digit, so it fails there and gives no finding. In both visible
cases (b) gives no finding of its own that (a) does not give: both need
`s` to be a base-91 digit and read `T` by the same rule (6.4). A
`syntax` finding at `s` or a `value` finding at `T` is one that both
readings give, of the same kind at the same offset, so it does not
count against (b), and the `ambiguous` finding at `c` is given beside
it (README section 3, Which findings are the other reading's own). In a
weather report, (b) would take a `c` in `'!'`–`'z'` as wind (step 3)
rather than course and speed; the finding is the same.

| Decoder | Reads | Where |
|---|---|---|
| FAP | `c` or `s` = `SP`: unused; then GGA; then `c` 0–89; then 90. | `_compressed_to_decimal`, FAP.pm:1951–1972 |
| Dire Wolf | `c` = `SP`; GGA; `'{'`; `'!'`–`'z'`. | `decode_compressed_position`, src/decode_aprs.c:3565–3580 |
| aprslib | As FAP. | `parse_compressed`, aprslib/parsing/position.py:117–125 |
| Xastir | `c` = `SP`; then `c` below 90, inside which GGA gives altitude; `c` = 90 range. | `extract_comp_position`, src/db.c:7291–7357 |
| aprs-parser-rs | `c` = `SP`; GGA; 0–89; 90; else error. | src/components/position.rs:116; `AprsCompressedCs::parse`, src/compressed_cs.rs:17 |
| pdn-aprs | `c` = `SP`; GGA; `'{'`; weather symbol; course. | `compressed`, src/position.rs:189; `decode`, src/comment.rs:51–63 |
| javAPRSlib | `'_'` symbol: nothing; GGA: nothing; otherwise takes `c` from block offset 11, which is the `s` byte. | `parseCompressedExtension`, DataExtension.java:137, 149, 154 |

**Corpus question.** How many blocks have GGA bits set, split by `c` as
`SP`, `'!'`–`'z'` or `'{'`?

<a id="amb.cmp.filler"></a>
### amb.cmp.filler

**Open.** With `c` = `SP`, `s` and `T` are fillers (p. 56/38, p. 59/41),
while p. 55/37 makes every byte except table and code base-91.

**Readings.** (a) Base-91 digit or `SP`. (b) Any byte.

**Reading taken.** (a), the narrower byte set
([README section 3](README.md#3-tokenizer-model), Kinds by situation).
Other bytes are a `syntax` finding.

**In the bytes.** Visible, and reported as that `syntax` finding, which
alone is given ([README section 3](README.md#3-tokenizer-model),
Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP | All three of `c`, `s`, `T` in `0x20`–`0x7B`. | `_compressed_to_decimal`, FAP.pm:1893 |
| aprslib | All three in `0x20`–`0x7C`. | `parse_compressed`, aprslib/parsing/position.py:89 |
| Dire Wolf | Not checked when `c` is `SP`. | `decode_compressed_position`, src/decode_aprs.c:3565 |
| Xastir | Not checked when `c` is `SP`. | `extract_comp_position`, src/db.c:7198 |
| aprs-parser-rs, pdn-aprs | Not checked when `c` is `SP`. | src/components/position.rs:115–116; src/position.rs:188 |

**Corpus question.** Which bytes occur as `s` and `T` when `c` is `SP`?

<a id="amb.cmp.t"></a>
### amb.cmp.t

**Open.** Bits 7–6 of `T` − 33 are unused and zero (p. 57/39); the
action when they are not is not stated.

**Readings.** (a) Out of range. (b) Ignore the high bits.

**Reading taken.** (a), the narrower of the two
([README section 3](README.md#3-tokenizer-model), Kinds by situation):
a `value` finding.

**In the bytes.** Visible, and reported as that `value` finding, which
alone is given ([README section 3](README.md#3-tokenizer-model),
Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP | Tests bits 5 and 4–3 only. | `_compressed_to_decimal`, FAP.pm:1938, 1953 |
| Dire Wolf | Tests bits 4–3 only. | `decode_compressed_position`, src/decode_aprs.c:3568 |
| aprslib | Tests bits 5 and 4–3 only. | `parse_compressed`, aprslib/parsing/position.py:115, 119 |
| Xastir | Masks the value to six bits. | `extract_comp_position`, src/db.c:7254 |
| pdn-aprs | An error unless tolerated as a defect. | `compressed`, src/position.rs:200 |

**Corpus question.** How often is `T` in `'a'`–`'{'` while `c` is not
`SP`?

<a id="amb.cmp.range"></a>
### amb.cmp.range

**Open.** Four base-91 digits can encode values beyond 90° S and 180° E
(6.2). No action is stated.

**Readings.** (a) Out of range. (b) Accept the decoded value.

**Reading taken.** (a): a `value` finding, since base-91 coordinates
are held to the latitude and longitude ranges that the unit implies
([README section 3](README.md#3-tokenizer-model), Kinds by situation).

**In the bytes.** Visible, and reported as that `value` finding, which
alone is given ([README section 3](README.md#3-tokenizer-model),
Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP | No range check after decoding. | `_compressed_to_decimal`, FAP.pm:1921 |
| Dire Wolf | No range check. | `decode_compressed_position`, src/decode_aprs.c:3522, 3535 |
| aprslib | No range check. | `parse_compressed`, aprslib/parsing/position.py:104 |
| Xastir | No range check. | `extract_comp_position`, src/db.c:7261 |
| aprsc | Rejects positions outside ±90, ±180. | `pbuf_fill_pos`, src/parse_aprs.c:75 |
| aprs-parser-rs | Rejects them. | `Latitude::new`, src/components/lonlat.rs:85 |
| pdn-aprs | Rejects them. | `compressed`, src/position.rs:181 |

**Corpus question.** How many compressed blocks decode beyond the range?

<a id="amb.b91.set"></a>
### amb.b91.set

**Open.** Three statements of the digit set disagree; see
[err.b91.range](#err.b91.range).

**Readings.** (a) `'!'`–`'{'`, 91 digits. (b) Up to `'|'`. (c) Up to
`'}'`.

**Reading taken.** (a), the narrowest of the three
([README section 3](README.md#3-tokenizer-model), Kinds by situation):
it is also the set the compressed chapter states (p. 55/37) and the
only one with 91 members. The glossary gives the same set (p. 145/121).

**In the bytes.** Visible, since (b) or (c) would accept `'|'` or `'}'`.
Reported as the `syntax` finding of the field that uses the digit, which
alone is given ([README section 3](README.md#3-tokenizer-model),
Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP | `0x21`–`0x7B` in the compressed block. | `_compressed_to_decimal`, FAP.pm:1893 |
| Dire Wolf | `'!'` to `'{'`. | src/decode_aprs.c:95–97 |
| aprslib | Converter rejects `0x7C` and above; the compressed pattern lets `'|'` through to it. | `to_decimal`, aprslib/base91.py:34, 42; aprslib/parsing/position.py:89 |
| Xastir | Values 0–90 in the latitude and longitude; a `SP` there is read as 0. | `extract_comp_position`, src/db.c:7212–7252 |
| aprs-parser-rs | No upper bound. | `digit_from_ascii`, src/base91.rs:51 |
| pdn-aprs | `'!'` to `'{'`. | `is_digit`, src/base91.rs:3 |

**Corpus question.** Do `'|'` or `'}'` occur in compressed latitude or
longitude, or in lower-case DAO bytes?

<a id="amb.ext.slot"></a>
### amb.ext.slot

**Open.** Nothing marks whether the bytes after the symbol code are an
extension or the start of the comment (p. 31/17, p. 34/20).

**Readings.** (a) Matching bytes are the extension. (b) Never an
extension unless the format says so.

**Reading taken.** (a) (7.1), by the rule for forms that can stand at
one place: the extension, the more specific form, is tried before the
comment text that covers its bytes
([README section 3](README.md#3-tokenizer-model)).

**In the bytes.** Inherent
([README section 3](README.md#3-tokenizer-model)): every extension that
the reading accepts at the slot could also be the start of a comment,
and the bytes of one packet cannot narrow it. A finding here would mark
every extension. Decided by the reading, with no finding. Slot bytes on
which the readings of another entry divide differently, whether this
reading takes them as an extension or not, are visible cases, reported
by [amb.ext.csespd](#amb.ext.csespd), [amb.ext.phg](#amb.ext.phg),
[amb.ext.area](#amb.ext.area) and, in an object or item report,
[amb.area.symbol](05-object-item.md#amb.area.symbol).
[amb.pos.ext](03-position.md#amb.pos.ext) no longer gives a finding.

| Decoder | Reads | Where |
|---|---|---|
| FAP | Matching bytes at the start are the extension. | `_comments_to_decimal`, FAP.pm:1148 |
| Dire Wolf | Same. | `data_extension_comment`, src/decode_aprs.c:4138 |
| aprslib | Same. | `parse_data_extentions`, aprslib/parsing/common.py:135 |
| Xastir | Same for course and speed, BRG/NRQ and DFS; PHG and RNG are searched anywhere (see [amb.ext.count](#amb.ext.count)). | `process_data_extension`, src/db.c:8147 |
| aprs-parser-rs | Same for objects and items; a position's comment is kept undecoded. | src/object.rs:85, src/item.rs:73; src/position.rs:49 |
| pdn-aprs | Same. | `extension_at_start`, src/comment.rs:338 |

**Corpus question.** How many comments that begin with an
extension-shaped run read as text rather than as data?

<a id="amb.ext.count"></a>
### amb.ext.count

**Open.** The document speaks of one 7-byte field (p. 45/27) without
saying that a second one cannot follow, or that an extension later in
the comment does not count. UAP says one, directly after the symbol
(UAP 3.1, 3.2, 5.15).

**Readings.** (a) One, at the slot. (b) A chain. (c) Extensions found
anywhere in the comment. **[proposed]** Reading (c) takes only the
forms that begin with a three-letter marker, `PHG` (with PHGR), `RNG`
and `DFS`. A course and speed has no marker: away from the slot, seven
bytes of its shape are as likely to be part of other text, such as a
pair of frequencies or a date, and no decoder read searches for one
there (Xastir, the one that searches the rest of the packet, looks for
`RNG` and `PHG` only; table below). An earlier draft let (c) take every
form of step 3, which gave the finding to any `ddd/ddd` in a comment.

**Reading taken.** **[proposed]** (a). Most read decoders agree.

**In the bytes.** **[proposed]** Visible, under the test of
[README section 3](README.md#3-tokenizer-model). A run in the comment
that fits a form of step 3 of 7.1 with no `syntax` or `value` finding
of that form is comment text here, and an extension under reading (b)
when it directly follows the slot's extension, or under reading (c)
anywhere when it begins with a marker. **[proposed]** A course and
speed run therefore gets the finding only at the start of the comment:
directly after the slot's extension, or directly after a compressed
block (6.5). Either reading leaves the rest of the comment as it is, so it
accepts what this reading accepts. Such a run gets an `ambiguous`
finding at its first byte. This is the same kind of run that
[amb.ext.compressed](#amb.ext.compressed) reports after a compressed
block. **[proposed]** The search covers the comment
of every report that carries a position, including a compressed one,
since reading (c) takes a run with a marker anywhere in such a comment.
**[agreed]** It does not cover the comment of a report without a
position, such as a telemetry report: no reading gives such a report a
data extension, so no rule makes a run there one.
**[proposed]** A run that overlaps another
token found in the comment (8.2), or whose bytes carry the finding of
7.4, still gets this finding: findings from different rules on one
byte are not merged ([README section 3](README.md#3-tokenizer-model)).
An earlier draft gave no further finding in those two cases. An
earlier draft also treated the question as not visible, on the grounds
that such a run cannot be told from text; that is the case the finding
marks.

The finding is on the rule this reading gives the first byte of the
run: `cmt.text`, or the item found in the comment (8.2) that the byte
lies in. A run that already carries the `ambiguous` finding of 6.5 does
not get it a second time: both entries give the same finding, of the
same rule, kind and offset, which is given once
([README section 3](README.md#3-tokenizer-model), Placing a finding).
An earlier draft reported the run under the rule of the extension form
it fits, the rule of the other reading.

| Decoder | Reads | Where |
|---|---|---|
| FAP | One, at the start. | `_comments_to_decimal`, FAP.pm:1149–1187 |
| Dire Wolf | One, then BRG/NRQ after a course and speed. | `data_extension_comment`, src/decode_aprs.c:4138, 4175 |
| aprslib | One, then BRG/NRQ after a course and speed. | `parse_data_extentions`, aprslib/parsing/common.py:135–204 |
| Xastir | RNG, else PHG, searched anywhere in the rest of the packet. DFS only at the start and only with a `'/'` after it; then a course and speed and BRG/NRQ. | `extract_powergain_range`, src/db.c:7566–7570; `extract_omnidf`, :7643; `process_data_extension`, :8241–8285 |
| pdn-aprs | One at the start; a later PHG, RNG or DFS only behind an option. | `extension_at_start`, src/comment.rs:338; `late_extension`, :305 |

**Corpus question.** How often does an extension-shaped run follow a
first extension directly, or appear later in the comment?

<a id="amb.ext.compressed"></a>
### amb.ext.compressed

**Open.** The compressed block replaces the uncompressed position
together with the extension that would follow it (p. 55/37); the
compressed form does not carry PHG (p. 54/36); the diagrams go from `T`
to the comment (p. 59/41). The extension chapter says an extension can
follow position data without excluding the compressed form (p. 45/27).

**Readings.** (a) No slot; the bytes are comment. (b) A slot as after an
uncompressed position.

**Reading taken.** (a), following the diagrams over the general
extension chapter ([README section 3](README.md#3-tokenizer-model),
Pages that disagree).

**In the bytes.** Visible. Under (a) the bytes after `T` are comment
text, so a comment whose first bytes fit an extension is a case that
the bytes of the packet show, not one that every compressed report
carries; and the decoders split on it (table below), reading those
bytes as an extension or as text. Reading (b) takes them as an
extension, and accepts them, when they fit a form that 7.1 would try at
a slot of the same report and give no `syntax` or `value` finding of
that form (README section 3). Those bytes get an `ambiguous` finding at
their first byte, the byte after `T` (6.5). Bytes that fit only another form
of 7.2, or that would give such a finding, get none: (b) would not read
them as an extension, or would fail on them. This differs from
[amb.ext.slot](#amb.ext.slot), where the bytes in question are an
extension that the reading accepts, and a finding would mark every
extension.

| Decoder | Reads | Where |
|---|---|---|
| FAP | Reads an extension after the block. | `parseaprs`, FAP.pm:2642 |
| aprslib | Reads an extension after the block. | `parse_position`, aprslib/parsing/position.py:76 |
| Xastir | Reads an extension after either form. | src/db.c:9553 |
| Dire Wolf | Comment only, no extension. | `aprs_ll_pos`, src/decode_aprs.c:917, 986; `aprs_ll_pos_time`, :1096 |
| pdn-aprs | No extension after a compressed block. | `decode`, src/comment.rs:150 |
| javAPRSlib | Takes course, speed or range from `cs` only. | `PositionField`, PositionField.java:114 |

**Corpus question.** How often do the bytes after a compressed block
match an extension form?

<a id="amb.ext.csespd"></a>
### amb.ext.csespd

**Open.** The document lists three all-unknown forms (p. 45/27). Not
stated: a known course with an unknown speed, mixed bytes within one
part, and courses above 360. Course 000 means unknown in general and a
fixed station in a DF report (p. 45/27, p. 52/34).

**Readings.** (a) Each part three digits, three dots or three spaces,
independently. (b) Any mix of digits, dots and spaces per byte. (c) Only
the three listed forms.

**Reading taken.** **[proposed]** (a). Parts of different kinds give an
`unstated` finding; course or direction above 360 a `value` finding. A
seven-byte run with `'/'` at offset 3 and only digits, dots and spaces
that fails (a) is comment text with an `ambiguous` finding, because
reading (b) would take it. The meaning of 000 is left to decoding.

**In the bytes.** Visible. A run that only reading (b) accepts gets the
`ambiguous` finding above; parts of different kinds an `unstated`
finding; a course above 360 a `value` finding, which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).
By the test of README section 3, at the slot:

- A run with `'/'` at offset 3 and only digits, dots and spaces, in
  which a part mixes kinds, fails (a) and is comment text. (b) takes it
  as course and speed and accepts the report, since the comment limits
  with and without an extension are seven bytes apart (p. 50/32),
  unless its course part is three digits above 360, where (b) would
  give `value`. Where (b) accepts, the run gets `ambiguous` at its
  first byte; otherwise no finding.
- Parts of different kinds are read by (a) and (b) as course and speed
  with the `unstated` finding. (c) reads the seven bytes as the start of
  the comment, and accepts the report, since the comment limits with
  and without an extension are seven bytes apart (p. 50/32). They get
  `ambiguous` at their first byte beside the `unstated` finding, unless
  the course gives `value`, which then alone is given.
- Parts of one kind each are read alike by all three readings.

| Decoder | Reads | Where |
|---|---|---|
| FAP | Digit, `'.'` or `SP` per byte; a course outside 1–360 is set to 0. | `_comments_to_decimal`, FAP.pm:1149–1161 |
| Dire Wolf | Any bytes with `'/'` at offset 3. | `data_extension_comment`, src/decode_aprs.c:4162 |
| aprslib | Digit, `'.'` or `SP` per byte; a course outside 1–360 is set to 0. | `parse_data_extentions`, aprslib/parsing/common.py:141, 146 |
| Xastir | Digit, space or dot per byte. | `extract_speed_course`, src/db.c:7390 |
| pdn-aprs | As reading (a); a course above 360 dropped as a defect. | `is_course_speed`, src/comment.rs:326; `extension_at_start`, :350 |
| javAPRSlib | `'/'` at offset 3 and a symbol other than `'_'`. | `parseUncompressedExtension`, DataExtension.java:78 |
| aprs-parser-rs | `'/'` at offset 3. | `Extension::decode`, src/components/extensions.rs:254 |

**Corpus question.** How many seven-byte runs after the symbol have
`'/'` at offset 3 with mixed digits, dots and spaces, and how many
courses are above 360?

<a id="amb.ext.phg"></a>
### amb.ext.phg

**Open.** The height code is any byte from `'0'` upward with no bound
(p. 46/28); directivity code `'9'` has no meaning in the table; the rate
byte of PHGR runs from `'A'` upward with no bound (p. 46/28). PHG
followed by a comment that starts with a digit or letter and `'/'` is
byte for byte a PHGR. The DFS table has the same height row, ending at
`'9'`, and no sentence that extends it (p. 48/30).

**Readings.** (a) `h` up to `'~'`, in PHG and DFS alike; `d` = `'9'` out
of range; PHGR when the two bytes after `phgd` fit. (b) All four codes
digits only; PHGR not recognised.

**Reading taken.** (a), as in 7.2 and 7.3, for PHG and PHGR: the
narrowest listed reading that the text supports, since (b) contradicts
p. 46/28, which lets the height code run past `'9'` and adds PHGR
([README section 3](README.md#3-tokenizer-model), Kinds by situation).
**[proposed]** The same `h` up to `'~'` in DFS (see the open item in
section 11). **[proposed]** `r` is `'0'`–`'9'` or `'A'`–`'Z'`.

**In the bytes.** PHG against PHGR is inherent
([README section 3](README.md#3-tokenizer-model)): every PHGR is also a
PHG followed by a comment of that shape, and the bytes of one packet
cannot narrow it. It is decided by the reading (PHGR first), with no
finding. A `d` of `'9'` is visible and is reported as the `value`
finding of 7.3, which alone is given (Precedence). An `h` that is not a
digit is visible: (b) does not take the bytes as an extension and reads
them as the start of the comment. It accepts the report when the
comment, with those bytes added, stays within the limit the format
gives without an extension; for `ext.phg` and `ext.dfs` that holds
whenever (a) accepts, the limits being seven bytes apart (p. 50/32),
while the nine bytes of an `ext.phgr` can pass it. When this reading's
comment is itself over its limit, (b) is over its own as well. After an
`ext.phg` or `ext.dfs` the two length findings fall on the same byte,
so (b)'s is shared and does not count, and the condition holds. After
an `ext.phgr`, (b)'s first byte past its limit lies two counted bytes
before this reading's, so that finding is (b)'s own and the condition
fails (README section 3, Which findings are the other reading's own).
An earlier draft counted the length finding as shared after an
`ext.phgr` too.
Where (b) accepts, the extension gets `ambiguous` at its first byte,
unless its `d` gives the `value` finding, which then alone is given.

| Decoder | Reads | Where |
|---|---|---|
| FAP | `p`, `g`, `d` digits, `h` `0x30`–`0x7E`; PHGR rate a digit or `'A'`–`'Z'`, then `'/'`. | `_comments_to_decimal`, FAP.pm:1172, 1177 |
| Dire Wolf | Codes unchecked; directivity used for `'0'`–`'8'`; PHGR not read. | `data_extension_comment`, src/decode_aprs.c:4187 |
| aprslib | As FAP; `d` = `'9'` marked invalid; the rate read as a hexadecimal digit. | `parse_data_extentions`, aprslib/parsing/common.py:166, 180, 196 |
| Xastir | Four digits; a `'/'` directly after them is consumed unless an `'A'` follows it; no rate, so the rate byte of a PHGR stays in the comment. | `extract_powergain_range`, src/db.c:7556, 7580 |
| aprs-parser-rs | `h` from `'0'` to `'L'`; `d` 0–9; the same for DFS. | `Extension::decode`, src/components/extensions.rs:156, 184, 192, 206 |
| pdn-aprs | `h` `'0'`–`'~'`; rate `'1'`–`'9'`, `'A'`–`'Z'`. | `is_phg_codes`, src/comment.rs:416; `beacon_rate`, :449 |
| javAPRSlib | Four digits. | `parseUncompressedExtension`, DataExtension.java:66 |

**Corpus question.** Which bytes occur as `h` and `d`, and after `PHGphgd`
how often is the next pair a rate byte and `'/'`?

<a id="amb.ext.brgnrq"></a>
### amb.ext.brgnrq

**Open.** The extension chapter puts BRG/NRQ after a course and speed
(p. 45/27, p. 48/30). The DF diagrams put it after any of the four
extensions (p. 52/34, p. 53/35) and say it means something only with
the DF symbol `/\` (p. 52/34). The bearing range is not stated.

**Readings.** (a) After any extension with the DF symbol. (b) After a
course and speed with the DF symbol. (c) After a course and speed, any
symbol.

**Reading taken.** **[agreed]** (b), following the text of the
extension chapter (p. 45/27, p. 48/30) and every DF example, as
[03-position.md](03-position.md#amb.df.ext) does; the DF diagrams that
(a) follows are an erratum there
([err.df.ext](03-position.md#err.df.ext)). An earlier draft of this
entry took (a); it was changed to agree with 03. A bearing above 360
is a `value` finding, the range being implied by the unit
([README section 3](README.md#3-tokenizer-model), Kinds by situation).

**In the bytes.** Visible: an `ambiguous` finding where (a) or (c) would
read the bytes differently (7.4). By the test of
[README section 3](README.md#3-tokenizer-model) that is two cases, both
picked out by the bytes, with the finding at the first byte of the 8:

- With the DF symbol, after an extension other than `ext.csespd`: (a)
  reads the 8 bytes as bearing and NRQ, and accepts them when their
  bearing is at most 360. With a larger bearing (a) would give `value`
  and does not count; there is no finding.
- Under another symbol, after an `ext.csespd`: (c) reads them as
  bearing and NRQ, and accepts them when they fit `ext.brgnrq` with a
  bearing of at most 360. With a larger bearing (c) would give `value`
  and does not count; there is no finding.

With the DF symbol after an `ext.csespd` the three readings agree, and
under another symbol after any other extension none of them reads
bearing and NRQ. In both visible cases only findings that the other
reading itself would produce count against it. Besides the bearing,
the one it could add is a comment over its limit, and that does not
arise: its 28 bytes are met exactly when this reading's comment, 8
bytes longer, meets 36
([03-position.md](03-position.md#amb.df.ext)), and the two length
findings then fall on the same byte, so that one is shared (README
section 3, Which findings are the other reading's own).

| Decoder | Reads | Where |
|---|---|---|
| FAP | Does not parse BRG/NRQ. | `_comments_to_decimal`, FAP.pm:1141 |
| Dire Wolf | After a course and speed when offsets 7 and 11 are `'/'`, any symbol. | `data_extension_comment`, src/decode_aprs.c:4175 |
| aprslib | After a course and speed, any symbol. | `parse_data_extentions`, aprslib/parsing/common.py:152 |
| Xastir | After a course and speed, after PHG or RNG, after DFS, or alone; any symbol; first byte unchecked. | `extract_bearing_NRQ`, src/db.c:7460; `process_data_extension`, :8182, 8199, 8225, 8273 |
| pdn-aprs | After a course and speed with the DF symbol. | `extension_at_start`, src/comment.rs:359 |

**Corpus question.** With the DF symbol, which extensions precede an
8-byte `/ddd/ddd` run; under other symbols, how often does one follow a
course and speed?

<a id="amb.ext.area"></a>
### amb.ext.area

**Open.** The descriptor follows the `\l` symbol directly (p. 78/60);
its name `Tyy/Cxx` (p. 45/27, p. 49/31) reads as if `'T'`, `'/'` and
`'C'` were literal, but the examples show digits (p. 80/62). The byte
set of `yy` and `xx` is implied by the examples. A `\l` report whose
slot holds a course and speed is not addressed.

**Readings.** (a) By symbol, digits as in 7.2, other extensions tried
when it fails. (b) By the literal letters, any symbol. (c) By symbol,
no fallback.

**Reading taken.** **[agreed]** (c), in object and item reports only.
[05-object-item.md](05-object-item.md#amb.area.symbol), which owns area
objects, gives a `\l` slot that does not fit the descriptor `syntax` and
tries no other extension, and
[03-position.md](03-position.md#amb.pos.ext) never reads the descriptor
after a position report. An earlier draft of this entry took (a), with
other extensions tried when the descriptor fails; it was changed to
agree with those two files.

**In the bytes.** **[agreed]** Visible where the slot is spelled with a
literal `'T'` at offset 0, `'/'` at offset 3 and `'C'` at offset 4, and
holds digits at offsets 1, 2, 5 and 6, which only reading (b) takes as
a descriptor: those seven bytes get an `ambiguous` finding at their
first byte, in any report (7.1). In an object or item report with
symbol `\l` the same bytes fail the descriptor, and there that `syntax`
finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence). Other
slots are decided by the symbol bytes, with no finding of this entry.

One case is visible under the readings of
[amb.area.symbol](05-object-item.md#amb.area.symbol) instead: in an
object or item report without the `\l` symbol, a slot that fits only
`ext.area`, with a colour from 10 to 15 and so no course and speed,
gets the `ambiguous` finding that 05 gives (7.1). In a `\l` object or
item, every descriptor that the reading accepts has digits where (b)
wants the letters, so (b) would read every one as comment text; every
descriptor carries that, and the bytes of one packet cannot narrow it,
so it gives no finding. A `\l` slot that fails the descriptor gives
the `syntax` finding of 05, which alone is given, although (a) might
read another extension there
([README section 3](README.md#3-tokenizer-model), on an ambiguity that
every instance of a form carries, and Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP | Does not parse area descriptors. | `_comments_to_decimal`, FAP.pm:1141 |
| Dire Wolf | Literal `'T'` at 0, `'/'` at 3, `'C'` at 4, any symbol; not decoded. | `data_extension_comment`, src/decode_aprs.c:4149 |
| aprslib | Does not parse area descriptors. | `parse_data_extentions`, aprslib/parsing/common.py:135 |
| Xastir | By `\l` symbol; type digit; colour `'/'` and a digit or `'1'` and `'0'`–`'5'`, while any other byte at offset 3 leaves the default colour; offsets two digits; no fallback. | `process_data_extension`, src/db.c:8155; `extract_area`, :7909, 7924–7979 |
| aprs-parser-rs | Literal `'T'` at offset 0, any symbol. | `Extension::decode`, src/components/extensions.rs:246 |
| pdn-aprs | By `\l` symbol, as reading (a). | `extension_at_start`, src/comment.rs:341; `area`, :528 |

**Corpus question.** Among `\l` reports, how many slots fail the
descriptor rule, and which extension do they match instead?

<a id="amb.cmt.bytes"></a>
### amb.cmt.bytes

**Open.** The free text is printable ASCII or UTF-8, with no CR or LF at
the end (p. 34/20). Control bytes elsewhere, DEL and byte sequences that
are not UTF-8 (UAP 5.16, 5.25) are not addressed.

**Readings.** (a) The stated set; anything else is an error. (b) The
comment is opaque bytes.

**Reading taken.** **[proposed]** (a), as in 8.1. The severity is
listed in section 11. The comment is not one of the fields of
[README section 3](README.md#3-tokenizer-model) where APRS12c only
recommends printable ASCII: p. 34/20 admits UTF-8, so well-formed UTF-8
gives no finding by the rule of 8.1 itself, and the rule for bytes
outside 7-bit ASCII in those fields does not apply here.

**In the bytes.** Visible, and reported as the comment's one `syntax`
finding, at the first byte outside the set (8.1), which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence and
Placing a finding).

| Decoder | Reads | Where |
|---|---|---|
| FAP | Deletes bytes outside `0x20`–`0x7E` and `0x80`–`0xFE` and trims spaces; no rejection. | `_cleanup_comment`, FAP.pm:739 |
| Dire Wolf | Drops one trailing LF and CR from the shown comment; prints other control bytes in hex; warns about a lone `0xB0` or `0xF8`. | `decode_aprs_print`, src/decode_aprs.c:808–870 |
| aprslib | Decodes the packet as UTF-8, else a detected encoding, else Latin-1; no rejection. | `_unicode_packet`, aprslib/parsing/\_\_init\_\_.py:67 |
| Xastir | No byte check in the comment paths read. | `process_data_extension`, src/db.c:8147; `process_info_field`, :8345 |
| pdn-aprs | Text that is not UTF-8 is read as Latin-1 when tolerated, else an error. | `decode`, src/text.rs:10 |

**Corpus question.** How many comments hold control bytes, DEL, a
trailing CR or LF, or bytes that are not well-formed UTF-8?

<a id="amb.cmt.length"></a>
### amb.cmt.length

**Open.** Each diagram gives a comment limit: 43 bytes, 36 after an
extension, 28 in a DF report (p. 50/32 to p. 53/35), 40 after a
compressed block (p. 59/41), 36 or 43 in objects and items (p. 76/58,
p. 77/59). The information field holds up to 256 bytes, and the editor
questions the limit (p. 50/32, p. 76/58). A DAO can exceed a "viewable"
limit given as 57 bytes (p. 35/21). No receiver action is stated.

**Readings.** (a) Over the limit is out of range. (b) The limit is
advice only.

**Reading taken.** **[proposed]** (a): a `value` finding.

Which bytes count is not part of this question. Items found in the
comment, telemetry included, count; DAO bytes do not, under the
reading of p. 35/21 that 8.1 proposes
([README section 3](README.md#3-tokenizer-model), Length limits).

**In the bytes.** Visible, since (b) would accept the comment. Reported
as that `value` finding, which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).

| Decoder | Reads | Where |
|---|---|---|
| FAP, Dire Wolf, aprslib, Xastir | No length check in the comment paths read. | FAP.pm:1141; src/decode_aprs.c:4138; aprslib/parsing/common.py:117; src/db.c:8147 |

**Corpus question.** What is the distribution of comment lengths per
format, and what share exceeds each limit?

<a id="amb.cmt.alt"></a>
### amb.cmt.alt

**Open.** The altitude can be anywhere in the comment and has exactly
six digits (p. 43/27). Not stated: more than one occurrence, a run of
more digits, and whether the negative form, described as outside the
standard, counts.

**Readings.** (a) Every occurrence recorded, several are ambiguous. (b)
The first wins. (c) The last wins.

**Reading taken.** (a), which
[README section 3](README.md#3-tokenizer-model) (Fixed spots and
repeats) gives for an item that may stand anywhere in its field, as
p. 43/27 lets the altitude; an earlier draft took (a) as a proposal of
its own. All read decoders take the first, so a decoding layer
that needs one value takes the first. More digits than the form
allows give a `syntax` finding, although every read decoder accepts
the first six: `'/A='` declares the altitude, so the fault is reported
inside it ([README section 3](README.md#3-tokenizer-model), Classes
that a keyword declares). An earlier draft carried this sentence as a
proposal.

**In the bytes.** Visible. Repeated altitudes get `ambiguous` findings
(8.2); a malformed one gets the `syntax` finding above, which alone is
given for it ([README section 3](README.md#3-tokenizer-model),
Precedence). With two or more well-formed occurrences, of `cmt.alt` or
`cmt.alt.neg`, (b) and (c) each read all but one as comment text,
which accepts them, so each occurrence gets `ambiguous` at its `'/'`. A
single well-formed occurrence is read alike by all three readings and
gets no finding. A malformed run is not an occurrence and does not
count towards the repetition (README section 3).

| Decoder | Reads | Where |
|---|---|---|
| FAP | First; six digits or `'-'` and five; no right boundary. | `_comments_to_decimal`, FAP.pm:1192 |
| Dire Wolf | First; a digit or `'-'`, then five digits. | `process_comment`, src/decode_aprs.c:4481, 4844 |
| aprslib | First; as FAP. | `parse_comment_altitude`, aprslib/parsing/common.py:208 |
| Xastir | First; a digit or `'-'`, then five digits. | `extract_altitude`, src/db.c:7504 |
| pdn-aprs | First; six digits or `'-'` and five. | `find_altitude`, src/comment.rs:578 |

**Corpus question.** How many comments hold more than one altitude, the
negative form, `'/A='` followed by fewer than six digits, or more than
six?

<a id="amb.cmt.dao"></a>
### amb.cmt.dao

**Open.** A DAO can sit anywhere in a position comment and is best put
at its end (p. 35/21). Not stated: what a digit datum or another datum
byte does to the precision bytes (p. 36/22 says only that further
datum values remain, and counts 28 of them where the base-91 set less
letters and digits leaves 29), mixed `SP` and digit, and how a reader
tells a DAO from text of the same shape.

**Readings.** (a) Every candidate recorded. (b) The last. (c) The first.

An earlier draft listed (d), a DAO only at the end of the comment.
P. 35/21 lets the field stand anywhere in the position comment and
only recommends the end, so (d) contradicts the text: it is decoder
behaviour, not a reading
([README section 3](README.md#3-tokenizer-model)). None of the decoders
in the table below limits the DAO to the end of the comment.

**Reading taken.** (a), which
[README section 3](README.md#3-tokenizer-model) (Fixed spots and
repeats) gives for an item that p. 35/21 lets stand anywhere in the
position comment; an earlier draft took (a) as a proposal of its own.
**[proposed]** The candidates are those of the forms of 8.3.

**In the bytes.** Visible: several candidates give `ambiguous` findings,
and the forms that 8.3 marks give `unstated` findings. Whether a single
candidate is a DAO or text of the same shape is inherent
([README section 3](README.md#3-tokenizer-model)): every DAO carries the
question, and the bytes of one packet cannot narrow it. It is taken
silently. By the test of README section 3:

- With several candidates, (b) and (c) each read all but one of them
  as text. Each candidate gets `ambiguous` at its first `'!'` when one
  of those readings that reads it as text accepts the report: the
  comment, with the bytes of the candidates that reading takes as text
  now counted (8.1), stays within its limit. When this reading's
  comment is itself over the limit, that reading is over its limit
  too. Its length finding is shared, and does not count, only when it
  falls on the same byte as this reading's, which holds when no
  candidate it counts lies before that byte; otherwise the finding is
  its own and it does not accept
  ([README section 3](README.md#3-tokenizer-model), Which findings are
  the other reading's own). An earlier draft counted the length finding
  as shared wherever both readings gave one.
- A single candidate is read alike by all three readings, wherever it
  stands in the comment, and gives no finding; the question left is
  the inherent one above.

| Decoder | Reads | Where |
|---|---|---|
| FAP | Last run of `'!'`, a byte `0x21`–`0x7B`, two bytes `0x20`–`0x7B`, `'!'`; kept if upper case with two digits, lower case with two base-91 digits, or any datum with two spaces. | `_comments_to_decimal`, FAP.pm:1202; `_dao_parse`, :1983 |
| Dire Wolf | First run of an upper-case datum with digits or spaces, a lower-case datum with base-91 digits or spaces, or a private `'T'` form; spaces per byte. | `process_comment`, src/decode_aprs.c:4475, 4732 |
| aprslib | Last run with any datum `0x21`–`0x7B`; offsets applied for `'W'` and `'w'` only. | `parse_dao`, aprslib/parsing/common.py:218, 226 |
| Xastir | First valid run; letter datum only; both digits or both spaces, both base-91 or both spaces; uncompressed positions only. | `decode_dao`, src/db.c:6830; `extract_position`, :7025 |
| pdn-aprs | Last run outside a telemetry block; datum-only with letter or digit; mixed forms rejected. | `find_dao`, src/comment.rs:622 |

**Corpus question.** Where in the comment do DAO candidates fall, which
datum bytes occur, and how many comments hold more than one?

<a id="amb.cmt.noarchive"></a>
### amb.cmt.noarchive

**Open.** Any packet containing the string is not to be archived
(p. 110/86); the release history names positions, status and messages
(p. 155/131); UAP names comment and message text (UAP 3.7). Whether the
header or other fields count is not stated.

**Readings.** (a) Free-text fields only. (b) The whole information field.
(c) The whole line.

**Reading taken.** **[agreed]** (a) for the token, with the search of
(b): `'!x!'` is looked for in the whole information field, a match
inside a free-text field is the `cmt.noarchive` token, and a match
anywhere else in the information field gives `ambiguous` (8.2). In
base-91 fields the bytes `'!'` and `'x'` are digits, so a run there can
be part of the coordinates rather than a marker. An earlier draft
searched free-text fields only and gave no finding elsewhere.

**In the bytes.** Visible under the test of
[README section 3](README.md#3-tokenizer-model): (b) takes a match
outside free text as the marker, and since the marker only flags the
packet and leaves the bytes to the field they lie in, (b) accepts the
packet wherever this reading does. **[proposed]** The finding at the
first `'!'` is not given where the reading already reports the bytes:
when one of the three bytes carries a `syntax` or `value` finding, or
the match lies in a residue, including the field of a format not read
yet ([README section 3](README.md#3-tokenizer-model), Precedence). An
earlier draft gave it with no further condition. A match in the address header is outside the
search; see section 11.

| Decoder | Reads | Where |
|---|---|---|
| FAP, Dire Wolf, aprslib, Xastir, aprsc, javAPRSlib, ebarkie/aprs, aprs-parser-rs, pdn-aprs | The string does not occur in the sources read. | Search of FAP.pm, src/, aprslib/, src/main/java/, `*.go` |

**Corpus question.** Where in the line does `'!x!'` occur: header,
free text, or other fields?

## 10. Errata

<a id="err.b91.range"></a>
### err.b91.range

The base-91 digits are given as codes 33 to 124, `'!'` to `'|'`, on
p. 34/20, which is 92 values. The DAO section says `'}'` has the value
90 (p. 36/22), which would make 93. The compressed chapter gives `'!'` to
`'{'` (p. 55/37), the only one of the three with 91 values; the
glossary (p. 145/121) and the telemetry maximum 8280 = 91 × 91 − 1
(p. 89/69) agree with it. The reading follows p. 55/37.

Origin: a merge. The 92-value range is already in APRS 1.0.1 (PDF p. 30,
printed 20), beside the 91-value set of its own compressed chapter (PDF
p. 47, printed 37). The `'}'` statement belongs to the precision and
datum option of the APRS 1.2 addendum, which 1.0.1 does not have, and
was placed next to the 1.0.1 text. 12b already has all three (PDF p. 36,
38 and 57).

<a id="err.b91.users"></a>
### err.b91.users

p. 34/20 says that two formats use base-91, the compressed position and
the Mic-E altitude. The DAO option (p. 35/21 to p. 37/23) and comment
telemetry (p. 88/68) use it too, and p. 88/68 lists all four. The
reading follows p. 88/68. No effect on the tokens.

Origin: a merge. The sentence is APRS 1.0.1 text (PDF p. 30, printed 20)
and was true there; the DAO option and comment telemetry came with the
APRS 1.2 addendum, which the release history lists (p. 157/133), and the
sentence was not updated. 12b already has it (PDF p. 36, printed 20).
The same defect was also entered as
[err.tlm.b91count](07-telemetry.md#err.tlm.b91count), which now points
here.

<a id="err.cmp.overlayexample"></a>
### err.cmp.overlayexample

The compressed overlay example on p. 125/101 has 12 bytes after the data
type identifier (rendered page checked); a block needs 13. It is the
base example of p. 58/40 with the first latitude digit missing. The
example on p. 126/102, with `'d'` as table, is complete. The reading
follows the layout of p. 55/37.

Origin: already in APRS 1.0.1 (PDF p. 101, printed 91, rendered page
checked), where the `'5'` is missing as well. 12b has the same text (PDF
p. 130, printed 104; text layer checked).

<a id="err.cmt.daoexample"></a>
### err.cmt.daoexample

On p. 37/23 the example `!w:\!` decodes `':'` to 27. `':'` is `0x3A`, 58,
so its base-91 value is 25. The value of `'\'`, 59, is right. The reading
follows the rule of p. 36/22. On the same page the `!wAb!` example is
said to add two digits but ends with three (`352`) once scaled; that
concerns decoding only.

Origin: within an addendum. The DAO option is not in APRS 1.0.1; it
came with the APRS 1.2 addendum, and 12b already has the same values
(PDF p. 39, printed 23). That the addendum's own text has them was not
checked here.

<a id="err.ext.phgheight"></a>
### err.ext.phgheight

On p. 46/28 height code `';'` is 20480 feet, given as about 36.2 km. It
is about 6.2 km. The tokenizer does not compute heights; recorded for
the decoding layer.

Origin: introduced by the 12c compilation. APRS 1.0.1 (PDF p. 38) and
12b (PDF p. 48, printed 28) give the height as about 3.9 miles, which is
right. The 12c release history lists metric units added to the PHG
table (p. 157/133).

<a id="err.ext.phgrange"></a>
### err.ext.phgrange

On p. 47/29 the range formula and its worked example print a dash where
a square root belongs, twice in each; read literally they do not give
the stated 7.9 miles (rendered page checked). The tokenizer does not
compute ranges; recorded for the decoding layer.

Origin: introduced by the 12b/12c compilation. APRS 1.0.1 prints the
root signs (PDF p. 39, printed 29, rendered page checked); 12b already
prints dashes (PDF p. 49, printed 29, rendered page checked).

<a id="err.ext.length"></a>
### err.ext.length

The generic layout and the extension chapter make every extension seven
bytes (p. 31/17, p. 45/27); PHGR is nine (p. 46/28), and the document
notes that it breaks the rule. The reading follows p. 46/28.

Origin: a merge. The seven-byte rule is APRS 1.0.1 text (PDF p. 27 and
p. 37). PHGR came from the APRS 1.2 addendum ("Probes (PHGR)" in the
release history, p. 157/133) and was inserted without changing the
rule. 12b already has it (PDF p. 48, printed 28).

<a id="err.ext.areagap"></a>
### err.ext.areagap

A duplicate of [err.area.gap](05-object-item.md#err.area.gap), which
records the spaces printed around the `'l'` symbol code of the area
descriptor (p. 78/60, p. 80/62) and their origin. The reading is the one
stated there and in [`ext.area`](#ext.area): no byte between the symbol
code and the descriptor.

<a id="err.sym.chapter"></a>
### err.sym.chapter

A duplicate of [err.dest.chapref](01-frame.md#err.dest.chapref), which
records the references to "Chapter 20" for symbols (p. 27/17, p. 29/19,
p. 40/24, p. 85/65) and their origin. Citations in this directory use
the page.

## 11. Open items

- The severity of comment bytes outside the stated set
  ([amb.cmt.bytes](#amb.cmt.bytes)): `syntax` as read now, or a weaker
  kind if the corpus shows Latin-1 text is common.
- Whether a DAO candidate inside a [`tlm.b91`](07-telemetry.md#tlm.b91)
  block is still a candidate. Under 8.2 it is, with an `ambiguous`
  finding on both.
- **[open]** A block followed by one of several DAO candidates: under
  reading (c) of [amb.cmt.dao](#amb.cmt.dao) that candidate is text, so
  the run is not a block
  ([amb.tlm.b91.order](07-telemetry.md#amb.tlm.b91.order)). Whether the
  block then gets an `ambiguous` finding is not decided; the tokenizer
  gives none.
- **[open]** The height code of [`ext.dfs`](#ext.dfs). Its table on
  p. 48/30 ends at `'9'` and no sentence there extends it, while the
  same page says that the DFS format replaces the power code of PHG
  with the signal strength. Reading (a) of [amb.ext.phg](#amb.ext.phg)
  takes `h` up to `'~'` in PHG and DFS alike. A reading that keeps the
  DFS height code to digits is not listed; it would be the narrower one
  under [README section 3](README.md#3-tokenizer-model) (Kinds by
  situation), if the text supports it. Whether to list and take it is
  not decided.
- Whether a separate finding kind for forms that APRS12c describes as
  outside its standard, such as [`cmt.alt.neg`](#cmt.alt.neg), is
  wanted instead of a separate ID.
- Whether `'!x!'` in the address header, which an address only
  APRS-IS can carry may hold ([`addr.is`](01-frame.md#addr.is)), is
  searched for and gives a finding
  ([amb.cmt.noarchive](#amb.cmt.noarchive)). The search covers the
  information field only.
- Whether reading (b) of [amb.ext.csespd](#amb.ext.csespd), any mix of
  digits, dots and spaces per byte, is a reading of the document's text
  or a wider form that README section 3 leaves to the deviation
  recognisers. In the second case the slot is a place where a form is
  recognised by its shape alone, and the `ambiguous` finding that (b)
  gives to such a run goes.
- An earlier list held as open whether a `'/A='` that starts neither
  altitude form, or one followed by a further digit
  ([amb.cmt.alt](#amb.cmt.alt)), keeps its `syntax` finding, which
  turned on whether `'/A='` is a keyword. The author decided that it
  is, and README section 3 (Classes that a keyword declares) now names
  it; the finding stays ([`cmt.alt`](#cmt.alt)).
- Each ambiguity above ends in a corpus question. None has been run.
