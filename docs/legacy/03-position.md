# Position, DF, locator and NMEA reports

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |

## 1. Scope

This file reads the information fields that [01-frame.md](01-frame.md#dti)
dispatches to position formats: position reports with and without
timestamp, in uncompressed and compressed form (identifiers `!`, `=`, `/`,
`@`), DF reports, the Agrelo DF format (`%`), the Maidenhead locator
beacon (`[`) and raw NMEA sentences (`$`).

The fields these formats share (timestamps, latitude and longitude, the
symbol, the compressed block, data extensions, items found inside a
comment) are read by [02-fields.md](02-fields.md); this file says where
they stand and when they apply. A position field whose symbol code is `_`
is handed to [06-weather.md](06-weather.md) after the position block when
any byte follows it (`pos.wx`, [amb.pos.wxsym](#amb.pos.wxsym)), and
storm data after a symbol code `@` is read there too
([06 section 8](06-weather.md#8-storm-data)). The forms
`!!` and `$ULTW` never reach this file
([amb.dti.shared](01-frame.md#amb.dti.shared)).

Conventions, finding kinds and verdicts are those of the
[README](README.md). Rule IDs in this file use the prefixes `pos`, `df`,
`grid` and `nmea`.

Each format here has its own identifier rule: `pos.dti` for position
and DF reports, `df.agrelo.dti`, `grid.dti` and `nmea.dti`. The token of
byte 0 carries that ID
([README section 3](README.md#3-tokenizer-model)); the dispatch and any
finding at that byte are given by the `dti` rules of
[01-frame.md](01-frame.md#dti). **[proposed]** A position report handed
to 06 by `pos.wx` is classified as a weather report, and its byte-0
token carries [`wx.pos`](06-weather.md#wx.pos) in place of `pos.dti`.

## 2. Position reports

The field is the identifier, a timestamp for two of the four
identifiers, a position block in one of two forms, then what follows the
symbol code.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.dti"></a>`pos.dti` | Identifier | `!` or `=` (no timestamp), `/` or `@` (timestamp). `=` and `@` mark a station that handles messages; the tokenizer records which. | yes | 1 byte | p. 31/17; p. 50/32 |
| <a id="pos.time"></a>`pos.time` | Timestamp | After `/` or `@` only: [`time.dhm`](02-fields.md#time.dhm) or [`time.hms`](02-fields.md#time.hms), 7 bytes. Missing, or in the [`time.mdhm`](02-fields.md#time.mdhm) form, gives `syntax`. **[proposed]** A missing timestamp gives the finding where it was expected, and nothing else. Eight digits are the `time.mdhm` form: an 8-byte `time.mdhm` token, the `syntax` finding at its first byte, and the position read after it. | for `/`, `@` | 7 bytes | p. 38/22; p. 50/32; p. 59/41 |
| <a id="pos.form"></a>`pos.form` | Form selector | Not a token. The next byte picks the form: a digit gives `pos.unc`; `/`, `\`, `A`–`Z` or `a`–`j` gives `pos.cmp`. Any other byte gives `syntax` and the rest of the field is `residue`. | yes | — | p. 50/32; p. 55/37; p. 125/101 ([amb.pos.form](#amb.pos.form)) |
| <a id="pos.unc"></a>`pos.unc` | Uncompressed position | Not a token; the sequence [`lat`](02-fields.md#lat) (8 bytes), [`sym.table`](02-fields.md#sym.table) (1), [`lon`](02-fields.md#lon) (9), [`sym.code`](02-fields.md#sym.code) (1). Position ambiguity is read by [`lat.amb`](02-fields.md#lat.amb) and [`lon.amb`](02-fields.md#lon.amb). | one of the two forms | 19 bytes | p. 39/23; p. 40/24; p. 50/32 |
| <a id="pos.cmp"></a>`pos.cmp` | Compressed position | [`cmp.block`](02-fields.md#cmp.block), 13 bytes. | one of the two forms | 13 bytes | p. 55/37; p. 59/41 |
| <a id="pos.wx"></a>`pos.wx` | Weather hand-off | When [`sym.code`](02-fields.md#sym.code) or [`cmp.code`](02-fields.md#cmp.code) is `_`, with any table or overlay, and at least one byte follows the position block, those bytes are tokenized by [06-weather.md](06-weather.md) as [`wx.pos`](06-weather.md#wx.pos) and none of the rules below apply. **[proposed]** The report is then a weather report: the token of byte 0 carries `wx.pos`, not `pos.dti` (section 1). A `_` report that ends at the position block is an ordinary position report with no finding ([amb.pos.wxsym](#amb.pos.wxsym)). | — | end of field | p. 51/33; p. 82/62; p. 85/65 |
| <a id="pos.null"></a>`pos.null` | Null position | Latitude `0000.00N`, longitude `00000.00W`. The tokenizer reports no finding, with any symbol; the null symbol `\.` is noted for the decoding layer. | — | — | p. 42/26 |

### 2.1 After an uncompressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.ext"></a>`pos.ext` | Data extension | The bytes directly after [`sym.code`](02-fields.md#sym.code), when they match one of [`ext.csespd`](02-fields.md#ext.csespd), [`ext.phg`](02-fields.md#ext.phg), [`ext.phgr`](02-fields.md#ext.phgr), [`ext.rng`](02-fields.md#ext.rng) or [`ext.dfs`](02-fields.md#ext.dfs). Bytes that match are the extension ([amb.pos.ext](#amb.pos.ext)). [`ext.dirspd`](02-fields.md#ext.dirspd) (weather only) and [`ext.area`](02-fields.md#ext.area) (area objects only) are not taken here, whatever the symbol: bytes of their layout that also fit `ext.csespd` are read as `ext.csespd`, and other `ext.area`-shaped bytes stay comment. **[proposed]** Being an extension gives no finding of its own, whatever byte follows it ([amb.pos.ext](#amb.pos.ext)). A slot spelled with a literal `T`, `/` and `C` at offsets 0, 3 and 4 and digits at offsets 1, 2, 5 and 6 gets the `ambiguous` finding of [amb.ext.area](02-fields.md#amb.ext.area); the other findings on slot bytes are those of [02-fields section 7](02-fields.md#7-data-extensions). | no | 7 bytes (9 for `ext.phgr`) | p. 33/19; p. 45/27; p. 46/28; p. 51/33 |
| <a id="pos.cmt"></a>`pos.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text): the rest of the field, or the bytes after the storm fields when [06-weather.md](06-weather.md#8-storm-data) reads storm data after a `pos.ext` with symbol code `@`. At most 43 bytes when there is no `pos.ext` and 36 when there is one; for a DF report see `df.cmt`. A longer comment gives `value` at the first byte past the limit ([amb.pos.cmtlen](#amb.pos.cmtlen)). | no | end of field | p. 50/32; p. 51/33 |

Inside `pos.cmt` and `pos.cmpcmt` the items of
[02-fields.md](02-fields.md#82-items-found-inside-a-comment) section 8.2
are searched for, together with base-91 telemetry
([`tlm.b91`](07-telemetry.md#tlm.b91)) and, at the start of the comment,
a frequency ([09-other.md](09-other.md#7-frequency-specification)).

### 2.2 After a compressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.cmpcmt"></a>`pos.cmpcmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), 0 to 40 bytes, with no data extension before it. Longer gives `value` at byte 41. When its first bytes match one of the extensions listed under `pos.ext` with no `syntax` or `value` finding of that extension, the tokenizer gives `ambiguous` at the comment start and keeps them as comment ([amb.pos.cmpext](#amb.pos.cmpext)). | no | end of field | p. 55/37; p. 59/41 |

## 3. DF reports

A DF report is a position report, with or without timestamp, in the
uncompressed form, whose symbol is the DF symbol and which carries
bearing and NRQ after course and speed.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="df.sym"></a>`df.sym` | DF symbol | Not a token. [`sym.table`](02-fields.md#sym.table) `/` with [`sym.code`](02-fields.md#sym.code) `\`. | yes | — | p. 52/34; p. 53/35 |
| <a id="df.ext"></a>`df.ext` | Course and speed | `pos.ext` in the form [`ext.csespd`](02-fields.md#ext.csespd) ([amb.df.ext](#amb.df.ext)). | yes | 7 bytes | p. 45/27; p. 48/30; p. 52/34 |
| <a id="df.brg"></a>`df.brg` | Bearing and NRQ | [`ext.brgnrq`](02-fields.md#ext.brgnrq), 8 bytes, directly after `df.ext`. | yes | 8 bytes | p. 48/30; p. 52/34; p. 53/35 |
| <a id="df.cmt"></a>`df.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), 0 to 28 bytes. Longer gives `value` at byte 29. | no | end of field | p. 52/34; p. 53/35 |
| <a id="df.notdf"></a>`df.notdf` | Bearing-shaped comment | The 8 bytes after a `pos.ext` match the shape of [`ext.brgnrq`](02-fields.md#ext.brgnrq), but `df.sym` or `df.ext` does not hold. The bytes stay `pos.cmt`. **[proposed]** When exactly one of the two holds and the bearing is at most 360, the tokenizer gives `ambiguous` at their first byte ([amb.df.detect](#amb.df.detect), [amb.df.ext](#amb.df.ext)). When neither holds, or the bearing is above 360, no finding: no reading listed would take the bytes as bearing and NRQ, or the one that would gives `value`. | — | — | p. 48/30; p. 52/34 |

A report with the DF symbol and no bearing is an ordinary position report;
the tokenizer reports nothing about it.

## 4. Agrelo DF format

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="df.agrelo.dti"></a>`df.agrelo.dti` | Identifier | `%`, 1 byte. | yes | 1 byte | p. 31/17; p. 138/114 |
| <a id="df.agrelo"></a>`df.agrelo` | Agrelo report | After `df.agrelo.dti`: the bearing as 3 digits, then `/`, then the quality as 1 digit: exactly 5 bytes, 6 with the identifier. Any other content gives `syntax`; bytes after the sixth byte of the field form `residue` ([amb.df.agrelo](#amb.df.agrelo)). | — | 5 bytes | p. 31/17; p. 138/114; p. 153/129 |

## 5. Maidenhead locator beacon

The `[` identifier is obsolete; the finding is given at the identifier
by [01-frame.md](01-frame.md#dti).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="grid.dti"></a>`grid.dti` | Identifier | `[`, 1 byte. | yes | 1 byte | p. 31/17; p. 42/26; p. 51/33 |
| <a id="grid.loc"></a>`grid.loc` | Locator | Two letters `A`–`R`, two digits, then optionally two letters `A`–`X`: 4 or 6 bytes. The letter ranges are those of the Maidenhead system, which APRS12c refers to but does not state ([amb.grid.range](#amb.grid.range)). The same letters in lower case are recognised; the format that holds the locator says what they give ([amb.grid.case](#amb.grid.case)). Used here, by [`stat.grid`](09-other.md#stat.grid) and by [`dest.grid`](01-frame.md#dest.grid). | yes | 4 or 6 bytes ([amb.grid.form](#amb.grid.form)) | p. 42/26; p. 51/33; p. 105/81; p. 106/82; p. 150/126 |
| <a id="grid.close"></a>`grid.close` | Closing bracket | `]`, 1 byte, directly after `grid.loc`. A `]` after six locator-shaped bytes makes all six the locator ([amb.grid.range](#amb.grid.range)). | no | 1 byte | p. 51/33 |
| <a id="grid.cmt"></a>`grid.cmt` | Comment | Any bytes to the end of the field. No limit beyond that of [`line.info`](01-frame.md#line.info). | no | end of field | p. 51/33 |

In a beacon, a locator with lower-case letters gives `unstated`: this
format states no case rule. **[proposed]** When the first four bytes
fail, the extent is still taken from what follows: six bytes when
bytes 5 and 6 are letters followed by `]` or in range, else four. The
first failing byte alone gives `syntax`. **[proposed]** A beacon gets `ambiguous` at
byte 5, the first byte after a 4-byte locator, when bytes 5 and 6 are
both letters and a reading listed would divide them differently from
this one: a 6-byte locator with no `]` after it
([amb.grid.form](#amb.grid.form)), and a
subsquare that holds a lower-case letter after an upper-case first pair
([amb.grid.case](#amb.grid.case)). One finding is given however many
of these hold. **[agreed]** Two letters of which one is outside `A`–`X`,
with no `]` after them, are comment text with no finding
([amb.grid.range](#amb.grid.range)); with a `]` they give `syntax`.
**[proposed]** With a `]` after the six bytes none of
these holds: every reading takes the six bytes as the locator
([amb.grid.range](#amb.grid.range)), and reading (a) of amb.grid.case,
which rejects the lower-case letters, then fails and does not count.
**[proposed]** `grid.cmt` is a free-text field for
[`cmt.noarchive`](02-fields.md#cmt.noarchive); the other items of
02 section 8.2 are not searched in it.

## 6. Raw NMEA

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nmea.dti"></a>`nmea.dti` | Identifier | `$`, 1 byte, when the field does not start `$ULTW`. P. 52/34 discourages sending raw NMEA but does not make it obsolete: **[agreed]** the field gives `discouraged` at this byte, by the dispatch table of [01-frame.md](01-frame.md#dti). | yes | 1 byte | p. 31/17; p. 52/34 |
| <a id="nmea.addr"></a>`nmea.addr` | Address field | 5 bytes, each `A`–`Z`: talker and sentence type. Anything else gives `syntax`. Any talker and type are accepted; the five recommended types (GGA, GLL, RMC, VTG, WPL) are noted, others give no finding ([amb.nmea.sentence](#amb.nmea.sentence)). | yes | `,` | p. 42/26; p. 52/34 |
| <a id="nmea.field"></a>`nmea.field` | Data field | `,` then zero or more bytes 0x20–0x7E other than `,`, `*` and `$`. One token per field; the content is not checked ([amb.nmea.sentence](#amb.nmea.sentence)). | yes, at least one | `,`, `*` or end of field | p. 42/26; p. 52/34 |
| <a id="nmea.cks"></a>`nmea.cks` | Checksum | `*` then two hex digits, `0`–`9` or `A`–`F`, as in three of the four examples. Their value is compared with the exclusive-or of every byte after `$` and before `*`; a mismatch gives `value` at the first hex digit. Hex digits `a`–`f` give `unstated`, and the value is still compared. A missing checksum gives no finding ([amb.nmea.checksum](#amb.nmea.checksum)). | no | 2 bytes after `*` | p. 52/34 |
| <a id="nmea.end"></a>`nmea.end` | Sentence terminator | CR, LF or both after the last field or the checksum. Gives `unstated`. **[proposed]** Any other bytes after the checksum are a residue that names `nmea.cks`, with `syntax` at the first of them. | no | end of field | — |
| <a id="nmea.len"></a>`nmea.len` | Sentence length | Not a token. The bytes after `$` up to `nmea.end` or the end of the field number 25 to 209; outside that range gives `value` at `nmea.dti`. | — | — | p. 52/34 |

## 7. Ambiguities

<a id="amb.pos.form"></a>
### amb.pos.form

**Open in the document.** The uncompressed diagrams start with a latitude
whose first byte is a digit (p. 50/32); the compressed diagrams start with
a symbol table identifier, `/`, `\`, `A`–`Z` or `a`–`j` (p. 55/37).
P. 55/37 says that a leading table identifier in place of a digit marks
the compressed form, and p. 125/101 that a compressed position never
starts with a digit. Nothing says what a first byte in neither set means.

**Readings.** (a) Select by the first byte; a byte in neither set is
malformed. (b) Try one form, then the other.

**Reading taken.** **[proposed]** (a). The sets do not overlap, so the
choice is never visible in the bytes: decided by the reading, no
`ambiguous` finding. **[proposed]** Where (a) selects a form, (b) can
read only that one. A first byte in neither set fails both forms under
(b) as well, and under (a) gives `syntax`, which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| FAP | A digit gives uncompressed, `/`, `\`, `A`–`Z`, `a`–`j` compressed, `!` Ultimeter; anything else is an error. | `parseaprs`, FAP.pm:2614–2654 |
| Dire Wolf | A digit gives uncompressed; any other byte is read as compressed. | `aprs_ll_pos`, decode_aprs.c:926, 972; `aprs_ll_pos_time`, decode_aprs.c:1032, 1059 |
| aprslib | Tries the compressed pattern first, then the uncompressed one. | `parse_position`, position.py:47–59; `parse_compressed`, position.py:89 |
| aprsc | Same byte sets as FAP. | `parse_aprs_body`, parse_aprs.c:1227–1236 |

**Corpus question.** In position fields, how many have a first position
byte in neither set, and which bytes are they?

<a id="amb.pos.ext"></a>
### amb.pos.ext

**Open in the document.** The extension is optional and has no
delimiter (p. 45/27, p. 51/33). Seven bytes after the symbol that happen
to read as an extension can be meant as comment text, and nothing in the
bytes tells them apart. The area descriptor is tied to area objects
(p. 49/31), and wind direction and speed to weather reports (p. 45/27),
but both share the layout of course and speed.

**Readings.** (a) Bytes that match an extension are the extension.

An earlier draft listed (b), an extension only when followed by the end
of the field or a separator. P. 34/20 puts no separator between the
data and the comment unless a format says otherwise, so (b)
contradicts the text: it is decoder behaviour, not a reading
([README section 3](README.md#3-tokenizer-model)), and the `ambiguous`
finding that the draft gave to an extension followed by a byte other
than `SP` or `/` was dropped with it. Of the decoders read, Xastir
takes DFS only with a `/` after it
([amb.ext.count](02-fields.md#amb.ext.count)); FAP and aprslib strip
one leading separator from the comment after an extension but do not
require one (table below).

**Reading taken.** **[proposed]** (a). **[agreed]** After a position
report the area descriptor is never read, whatever the symbol.

Whether bytes that match an extension are one is inherent
([README section 3](README.md#3-tokenizer-model)): every extension
carries the question, and the bytes of one packet cannot narrow it.
Decided by the reading, no finding, whatever byte follows the
extension. A slot spelled with the literal letters of the descriptor's
name, with digits in the other places, gets the `ambiguous` finding of
[amb.ext.area](02-fields.md#amb.ext.area).

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| FAP | One extension at the comment start: course and speed with digits, `.` or space, then PHGR, PHG, RNG; not DFS. Strips one leading `/` or space from what is left. | `_comments_to_decimal`, FAP.pm:1141–1211 |
| Dire Wolf | Area descriptor when bytes 0, 3, 4 are `T`, `/`, `C`, with any symbol; course and speed whenever byte 3 is `/`, without a digit check; PHG without the PHGR form; RNG; DFS. | `data_extension_comment`, decode_aprs.c:4138–4232 |
| aprslib | Course and speed with digits, space or `.`; PHG and PHGR; RNG; not DFS. Strips one leading `/` after the other comment items are taken out. | `parse_data_extentions`, common.py:135–204; `parse_comment`, common.py:129–130 |
| Xastir | Reads the area descriptor only for symbol `\l`; course and speed, PHG, RNG, DFS. | `process_data_extension`, db.c:8147, 8155 |
| pdn-aprs | Reads an extension only after an uncompressed position; the area descriptor only for `\l`. | comment.rs:150–154, 338–347; `is_area_symbol`, comment.rs:27 |

**Corpus question.** How many comments start with bytes that match an
extension and continue with a letter or digit rather than a space, `/` or
the end of the field?

<a id="amb.pos.cmpext"></a>
### amb.pos.cmpext

**Open in the document.** The compressed diagrams have no extension
column (p. 59/41), course, speed and range are carried in the compressed
block (p. 56/38), and the compressed format is said not to support PHG
(p. 54/36). The extension chapter says only that an extension can follow
position data (p. 45/27). Nothing says what a receiver does with an
extension-shaped comment start.

**Readings.** (a) Comment text. (b) An extension, as after an
uncompressed position.

**Reading taken.** **[proposed]** (a), with `ambiguous` at the comment
start when its bytes match an extension, since (b) is what several
decoders read. Visible in the bytes. **[proposed]** (b) accepts those
bytes when they match one of the extensions listed under `pos.ext` and
give no `syntax` or `value` finding of that extension
([02-fields section 7.3](02-fields.md#73-values)). Its comment is
then 7 or 9 bytes shorter, against a limit of 36 instead of 40, so the
length never makes (b) fail where (a) does not. The finding is given
under that condition, at the first byte after `T`; bytes that would
give such a finding get none
([README section 3](README.md#3-tokenizer-model)).

**Decoders (read).** FAP applies its extension parser after a compressed
position too (FAP.pm:2642, `_comments_to_decimal` at 1141). aprslib
does the same (`parse_comment`, common.py:117, called from
position.py:76). Dire Wolf goes to the comment parser directly, with no
extension (decode_aprs.c:986). pdn-aprs reads no extension after a
compressed position (comment.rs:150–154).

**Corpus question.** How many compressed positions have a comment that
starts with an extension, and which kind?

<a id="amb.pos.wxsym"></a>
### amb.pos.wxsym

**Open in the document.** A position with the weather symbol carries a
weather report in place of extension and comment (p. 51/33, p. 85/65);
p. 82/62 names `/_` and `\_` as the weather symbol. Nothing says how to
read a station that uses the symbol with an ordinary comment.

**Readings.** (a) Symbol code `_` always means a weather report. (b) Only
when the bytes after the symbol parse as weather.

**Reading taken.** **[agreed]** (a), when at least one byte follows the
position block. A `_` report that ends at the symbol is an ordinary
position report with no finding, as 06 section 2 states; otherwise, for
any table or overlay, the bytes after the position block are handed to
[06-weather.md](06-weather.md#amb.wx.symbol), which reports what fails
as weather. An earlier draft of this entry handed
the report that ends at the symbol to 06 as well, which then had no
bytes to read. Bytes that (b) would read as an ordinary comment get the
`syntax` finding of 06, which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence). No
`ambiguous` finding here. **[proposed]** Where 06 reads the bytes as
weather, (b) reads them as weather too; the two readings differ only
on bytes that fail as weather. A table byte other than `/` or `\`
gives no `ambiguous` finding either: with its reading (b) dropped,
[amb.wx.symbol](06-weather.md#amb.wx.symbol) is not visible. An earlier
draft said 06 gave one there.

**Decoders (read).** FAP sends the rest to the weather parser whenever
the symbol code is `_` (FAP.pm:2624–2628, 2641–2645). Dire Wolf does the
same, and a source comment there describes a station sending `_` with a
PHG extension and plain text (decode_aprs.c:930–961). aprslib reads an
extension and then weather for symbol `_` (position.py:62–73).

**Corpus question.** Among positions with symbol code `_`, how many have
no weather element after the symbol, and how many start with an
extension other than wind?

<a id="amb.pos.cmtlen"></a>
### amb.pos.cmtlen

**Open in the document.** The diagrams limit the comment to 43, 36, 28 or
40 bytes (p. 50/32 to p. 53/35, p. 59/41). An editorial note on p. 50/32,
new in 12c, asks where the 43 came from, points to the 256-byte field of
p. 22/12, and says longer comments are common. With the 9-byte
[`ext.phgr`](02-fields.md#ext.phgr) the diagrams give no figure.

**Readings.** (a) The limits apply. (b) Only the field limit applies.

**Reading taken.** **[proposed]** (a): a longer comment gives `value`,
as for every stated limit. After `ext.phgr` the limit stays 36.
Visible in the bytes, since (b) would accept the comment; the `value`
finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).

**Decoders (read).** None of the functions cited in this file applies
these limits: FAP takes the rest of the body (FAP.pm:2625, 2642); Dire
Wolf's overlay structure declares a 43- or 40-byte comment but the
comment is read to the end of the field (decode_aprs.c:908–918,
926–987); aprslib takes the rest (position.py:62–79).

**Corpus question.** Distribution of comment lengths per form, and the
share above each limit.

<a id="amb.df.ext"></a>
### amb.df.ext

**Open in the document.** The extension chapter says bearing and NRQ
follow the course and speed extension (p. 45/27, p. 48/30); the DF
section says only that they follow the data extension (p. 52/34). The DF
diagrams label their extension column with all four kinds (p. 52/34,
p. 53/35; see [err.df.ext](#err.df.ext)).

**Readings.** (a) Only after course and speed. (b) After any of the four.

**Reading taken.** **[agreed]** (a), as
[02-fields section 7.4](02-fields.md#74-bearing-and-nrq) also reads
`ext.brgnrq`. Bearing-shaped bytes after PHG, RNG or DFS with the DF
symbol stay comment and give `ambiguous` (`df.notdf`). Visible in the
bytes. **[proposed]** The finding is at the
first of the 8 bytes, after an `ext.phg`, `ext.phgr`, `ext.rng` or
`ext.dfs`, when their bearing is at most 360. (b) then reads them as
bearing and NRQ, with the rest as `df.cmt`; its limit of 28 bytes is
met exactly when the `pos.cmt` of (a), 8 bytes longer, meets 36, so
(b) accepts the report wherever (a) does. With a larger bearing (b)
would give `value`, does not count, and there is no finding
([README section 3](README.md#3-tokenizer-model)).

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| Dire Wolf | Skips bearing and NRQ only inside the course and speed branch, for any symbol. | `data_extension_comment`, decode_aprs.c:4162–4182 |
| aprslib | Reads bearing and NRQ after course and speed, for any symbol. | `parse_data_extentions`, common.py:150–162 |
| Xastir | Reads bearing and NRQ after course and speed, after PHG, after DFS, or alone, for any symbol; does not check the leading `/`. | `process_data_extension`, db.c:8182–8273; `extract_bearing_NRQ`, db.c:7460 |
| pdn-aprs | Only after course and speed, only with `/\`. | `extension_at_start`, comment.rs:359–370 |
| FAP | Does not read bearing and NRQ. | `_comments_to_decimal`, FAP.pm:1141 |

**Corpus question.** Among `/\` positions with an extension followed by
`/ddd/ddd`, how is the extension split between the four kinds?

<a id="amb.df.detect"></a>
### amb.df.detect

**Open in the document.** Bearing and NRQ are "only meaningful" with the
DF symbol (p. 52/34). That does not say whether the same 8 bytes after
course and speed with another symbol are bearing data or comment.

**Readings.** (a) Comment unless the symbol is `/\`. (b) Bearing data for
any symbol.

**Reading taken.** **[proposed]** (a), with `ambiguous` (`df.notdf`),
because Dire Wolf, aprslib and Xastir read (b). Visible in the bytes.
**[proposed]** The finding is at the first of the 8 bytes, when they
follow an `ext.csespd` under a symbol other than `/\` and their bearing
is at most 360: (b) then reads them as bearing and NRQ, which takes
them out of the comment, and accepts the report wherever (a) does.
With a larger bearing (b) would give `value`, does not count, and there
is no finding ([README section 3](README.md#3-tokenizer-model)).

**Decoders (read).** See the table of [amb.df.ext](#amb.df.ext).

**Corpus question.** How many non-DF positions have `/ddd/ddd` after
course and speed?

<a id="amb.df.agrelo"></a>
### amb.df.agrelo

**Open in the document.** The Agrelo format exists only as a diagram in
Appendix 1 (p. 138/114) and a line in the identifier table (p. 31/17).
No range is given for bearing or quality, nor whether anything follows.
The revision history records a change of the separator to `/`
(p. 153/129).

**Readings.** (a) Exactly the 6 bytes of the diagram. (b) The 6 bytes
and then free text. (c) Other separators, as older units sent.

**Reading taken.** **[proposed]** (a). No range check on the digits.
Departures are visible and give `syntax`, which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).
**[proposed]** A field that (a) accepts is read the same way by (b) and
(c), so it gives no `ambiguous` finding.

**Decoders (read).** Xastir recognises `%XXX/Q` and two longer variants,
only prints them, and keeps the field as status text (db.c:15283–15394).
pdn-aprs requires exactly 6 bytes and a bearing of at most 360 (`agrelo`,
other.rs:404–411). aprslib lists `%` as unsupported
(parsing/\_\_init\_\_.py:47–65). FAP lists direction finding as not
handled and has no `%` branch (FAP.pm:49; `parseaprs`, FAP.pm:2579–2768).
Dire Wolf has no `%` branch and reports it as unknown
(decode_aprs.c:178–183, 336–502).

**Corpus question.** How many `%` fields are there, and how many are
exactly `%ddd/d`?

<a id="amb.grid.form"></a>
### amb.grid.form

**Open in the document.** The beacon diagram gives a 4- or 6-byte
locator, an optional `]` and an optional comment, with no separator
(p. 51/33). `[IO91 SXtext` is clear, `[IO91SX` is not: the last two
bytes can be a subsquare or the start of the comment.

**Readings.** (a) Take 6 bytes when bytes 5 and 6 are in range. (b) Take
6 only when `]` follows.

**Reading taken.** **[proposed]** (a). When the 6-byte locator is not
followed by `]`, the tokenizer gives `ambiguous` at byte 5. Visible in
the bytes. **[proposed]** Byte 5 is the first subsquare letter. (b)
would end the locator after 4 bytes and read bytes 5 and 6 as the start
of `grid.cmt`, which accepts any bytes, so (b) accepts every such
beacon that (a) accepts. With a `]` after the locator both readings
agree.

**Decoders (read).** Xastir takes 6 bytes only when `]` follows, else 4
(`extract_position`, db.c:7061–7099). pdn-aprs requires the `]`
(`maidenhead_beacon`, other.rs:238–250). FAP, Dire Wolf and aprslib do
not decode `[` (no `[` branch in FAP's `parseaprs`, FAP.pm:2579–2768;
decode_aprs.c:336–502; parsing/\_\_init\_\_.py:61).

**Corpus question.** How many `[` fields lack `]`, and of those how many
have letters in bytes 5 and 6?

<a id="amb.grid.range"></a>
### amb.grid.range

**Open in the document.** APRS12c shows the locator only as two
letters, two digits and two optional letters, by diagram and example
(p. 42/26, p. 51/33, p. 106/82). It does not give the letter ranges and
refers to the IARU Region 1 manual for the Maidenhead system
(p. 150/126), which is not among the references.

**Readings.** (a) The Maidenhead ranges: `A`–`R` for the first pair,
`A`–`X` for the subsquare. (b) Any letter.

**Reading taken.** **[agreed]** (a): `A`–`R` for the first pair and
`A`–`X` for the subsquare. In the first pair of a beacon, whose locator
the `[` places, a letter outside `A`–`R`
gives `syntax`, which alone is given, although (b) would accept it
([README section 3](README.md#3-tokenizer-model), Precedence). A fifth
or sixth byte outside `A`–`X` means there is no subsquare: the locator
has 4 bytes and other bytes follow it, which
[amb.grid.form](#amb.grid.form) handles. In a destination the letter
range makes the address not [`dest.grid`](01-frame.md#dest.grid), with
no `syntax` finding. A lower-case locator in a destination that only
APRS-IS can carry is not `dest.grid` either; it falls to the next class
of [01-frame section 5](01-frame.md#5-destination-classes) without a
finding of its own.

**[agreed]** In a beacon, a `]` directly after six bytes that have the
shape of a 6-byte locator closes the locator: those six bytes are
`grid.loc`, and a fifth or sixth byte outside `A`–`X` gives `syntax` at
that byte. The sender evidently meant a subsquare, so the bytes are not
read as a 4-byte locator followed by a comment.

**[agreed]** Where nothing places or closes the locator, letters out of
range make the bytes something else, with no finding, by the rule for
forms recognised by shape alone
([README section 3](README.md#3-tokenizer-model)); reading (b) does not
make them ambiguous:

- In a beacon, bytes 5 and 6 that are both letters, one of them outside
  `A`–`X` in either case, and not followed by `]`, start `grid.cmt`
  after a 4-byte locator, with no finding. Followed by `]`, they give
  `syntax` as above.
- A destination of locator shape with a letter out of range is
  classified by the other classes of 01 section 5, with no finding.
- In a status report a first-pair letter out of range means there is no
  [`stat.grid`](09-other.md#stat.grid).

Earlier drafts gave the beacon and the destination an `ambiguous`
finding, at byte 5 and at the first byte of `addr.dest`, from
reading (b).

**Decoders (read).** Dire Wolf checks `A`–`R` and `A`–`X`, either case
(`get_maidenhead`, decode_aprs.c:4082–4102). Xastir checks `A`–`R` for
the first pair only (db.c:7064–7067). pdn-aprs checks `A`–`R` and
`A`–`X`, either case (`is_locator`, status.rs:72–80).

**Corpus question.** How many locators in `[` fields have a letter
outside these ranges?

<a id="amb.grid.case"></a>
### amb.grid.case

**Open in the document.** For a status locator, letters are sent in
upper case and accepted in either (p. 105/81). For the beacon and the
destination no case rule is given.

**Readings.** (a) Upper case only. (b) Either case. (c) The status rule
everywhere.

**Reading taken.** **[proposed]** Recognise either case. Lower case
gives `syntax` in a status report (a stated sending rule) and `unstated`
in a beacon. A destination in the AX.25 form cannot hold lower case,
and one that only APRS-IS can carry is not `dest.grid` when it does
([amb.grid.range](#amb.grid.range)).
Visible in the bytes and reported by those kinds; the `syntax` finding
of a status report alone is given
([README section 3](README.md#3-tokenizer-model), Precedence), and in a
beacon the `unstated` finding stands without an `ambiguous` one.
**[proposed]** That last holds where a lower-case letter is in the
first pair: (a) and (c) then fail, and (b) reads the bytes as the
reading does. A lower-case letter only in the subsquare is different:
(a) does not take bytes 5 and 6 as a subsquare, ends the locator after
4 bytes and reads them as the start of `grid.cmt`, which accepts them.
The beacon then also gets `ambiguous` at byte 5, beside the `unstated`
finding.

**Decoders (read).** Dire Wolf accepts either case in status locators
(`get_maidenhead`, decode_aprs.c:4082, called at 2447 and 2481). In the
beacon, Xastir accepts only upper case in the first pair and either case
in the subsquare, which it upper-cases (db.c:7061–7086).

**Corpus question.** How many locators in `[` fields and status reports
have lower-case letters, and in which pair?

<a id="amb.nmea.sentence"></a>
### amb.nmea.sentence

**Open in the document.** Raw NMEA data is recognised by reference to
NMEA 0183 version 2.0 (p. 42/26), which is not among the references. Five
sentence types are recommended; the examples all use the `GP` talker
(p. 52/34). Nothing says what other talkers or types mean, and the
sentence structure (a 5-letter address field, comma-separated fields,
the byte set, the checksum) is given only by the examples.

**Readings.** (a) Any 5-letter address field. (b) `GP` only. (c) The five
types only.

**Reading taken.** **[proposed]** (a), with the field structure and byte
set of `nmea.field` taken from the examples and the general form of an
NMEA 0183 sentence (recalled, not read). Decided by the reading; no
`ambiguous` finding for other talkers or types. **[proposed]** (b) and
(c) reject every other talker or type, so they fail there and do not
count; where they accept a sentence, they read it as (a) does
([README section 3](README.md#3-tokenizer-model)).

**Decoders (read).** FAP requires `$GP` and decodes RMC, GGA and GLL
(FAP.pm:2681, 938–1131). Dire Wolf decodes RMC and GGA with the `GP`
or `GN` talker (`aprs_raw_nmea`, decode_aprs.c:1136–1160). Xastir
decodes GGA, RMC and GLL with `GP` (db.c:15168–15194). pdn-aprs accepts
an address field of 5 upper-case letters or digits, or a proprietary one
starting `P`, and keeps bytes after the checksum as a comment (`nmea`,
other.rs:60–81; `nmea_sentence`, other.rs:95–114). aprslib does not
decode `$` (parsing/\_\_init\_\_.py:47–65).

**Corpus question.** Distribution of NMEA address fields.

<a id="amb.nmea.checksum"></a>
### amb.nmea.checksum

**Open in the document.** Three of the four examples carry a checksum;
the `GPGLL` example carries none (p. 52/34). The document does not say
whether a receiver verifies it, nor what a missing one means.

**Readings.** (a) Verify when present; mismatch gives `value`. (b) Do
not verify: the tokenizer checks bytes, not computed values. (c) Require
it.

**Reading taken.** **[agreed]** (a): the checksum is verified when it
is present, since a mismatch means the bytes are not what was sent
([README section 3](README.md#3-tokenizer-model)). It is the two hex
digits after `*`, compared with the exclusive-or of the bytes between
`$` and `*`, neither included. This rule is the NMEA 0183 checksum as
recalled, not read: the NMEA standard is not among the references. A
mismatch gives `value` at the first hex digit. A missing checksum gives
no finding, since one APRS12c example (`GPGLL`) has none.

**[proposed]** Hex digits `a`–`f`: APRS12c states no case, and the
examples use upper case. Every decoder read that verifies the checksum
accepts either case (below). Lower-case digits give `unstated`, as for
anything the document has no rule for, and the value is still
compared.

Not an ambiguity in the bytes: (b) and (c) are not taken, and a
mismatch is reported as the `value` finding, which alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).
**[proposed]** A missing checksum is read alike by (a) and (b), and (c)
fails on it, so it does not count. A matching checksum, in either case
of hex digit, is divided the same way by all three readings. No
`ambiguous` finding.

**Decoders (read).** FAP verifies a checksum when present, matching the
hex digits in either case, and rejects a mismatch; the sum runs over the
bytes after `$` up to the last `*` (`_nmea_to_decimal`, FAP.pm:899–915,
pattern at 901). Dire Wolf decodes only RMC and GGA
(decode_aprs.c:1143, 1153), and for those requires a checksum and
rejects a missing or wrong one; the sum runs from the byte after `$` to
the first `*`, and the digits are read by `strtoul` in base 16, which
accepts either case (`remove_checksum`, dwgpsnmea.c:381–411, compare at
402). pdn-aprs accepts a missing checksum, accepts hex digits in either
case, and rejects a wrong one (`nmea_sentence`, other.rs:102;
`nmea`, other.rs:71–74; `nmea_checksum`, other.rs:117). Xastir: no
checksum test was found in db.c.

**Corpus question.** How many NMEA fields have no checksum, and how many
have one that does not match?

## 8. Errata

Each entry ends with an "Origin" line: where the defect first appears.
APRS 1.0.1 pages are PDF pages of the 2000 edition; 12b pages are PDF
pages of `APRS12b.pdf` in the same submodule.

<a id="err.df.ext"></a>
### err.df.ext

The DF diagrams list all four extension kinds in the column before
bearing and NRQ (p. 52/34, p. 53/35); the text on p. 45/27 and p. 48/30
places bearing and NRQ after course and speed only, and every DF example
uses course and speed. The reading follows the text
([amb.df.ext](#amb.df.ext)).

Origin: already in APRS 1.0.1: the DF diagrams (1.0.1 PDF p. 44, p. 45,
and the Appendix 1 copy on p. 105) and the text (1.0.1 PDF p. 37,
p. 40). 12b carries both unchanged.

## 9. Open items

- The kind for lower-case hex digits in `nmea.cks`
  ([amb.nmea.checksum](#amb.nmea.checksum)): `unstated` as proposed, or
  none, given that every decoder read accepts them.
- Whether an NMEA field is split into finer tokens per sentence type. The
  reading stops at one token per comma field.
- Whether a DF report with bearing but no DF symbol is worth a
  deviation recogniser, given the decoders that read it.
- The Maidenhead letter ranges ([amb.grid.range](#amb.grid.range)) and
  the NMEA sentence structure ([amb.nmea.sentence](#amb.nmea.sentence))
  come from documents outside the references. If those are added, both
  are checked against them.
