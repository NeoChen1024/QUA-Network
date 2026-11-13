# Status, capabilities, queries and other formats

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |

## 1. Scope

This file reads the information fields that
[01-frame.md](01-frame.md#dti) dispatches to the identifiers `>`
(status), `<` (station capabilities), `?` (general query), `{`
(user-defined) and `,` (invalid or test data), and the frequency
specification that chapter 18 places at the start of a comment or of
status text.

Directed queries are messages: [08-message.md](08-message.md) delimits
the addressee and the text and, when the text starts with `?`, hands it
to section 4.1 here. The Mic-E status text is read by
[04-mic-e.md](04-mic-e.md), which hands the start of its free text to
section 7 here. Object and item names are tokenized by
[05-object-item.md](05-object-item.md#obj.name); this file only says when
such a name is a frequency (`freq.objname`). Node naming conventions
(EchoLink, IRLP, WiRES, Winlink), net and meeting codes, the `111111z`
permanence timestamp, frequencies in messages (QSY) and DX cluster
spots are described by chapter 18 as conventions or proposals and are
not tokenized.

Conventions, finding kinds and verdicts are those of the
[README](README.md). Rule IDs in this file use the prefixes `stat`, `cap`,
`qry`, `udf`, `inv` and `freq`.

The token of the data type identifier byte carries the identifier rule
of its format ([README section 3](README.md#3-tokenizer-model)):
`stat.dti`, `cap.dti`, `qry.dti`, `udf.dti` or `inv.dti`, and
`qry.dir.dti` for a directed query.

## 2. Status reports

The field is `>`, then either a timestamp or a locator with symbol, or
neither, then text. A report with a locator has no timestamp.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="stat.dti"></a>`stat.dti` | Identifier | `>`, 1 byte. | yes | 1 byte | p. 31/17; p. 104/80 |
| <a id="stat.time"></a>`stat.time` | Timestamp | [`time.dhm`](02-fields.md#time.dhm) with the zulu suffix `z` only: 6 digits then `z`. Six digits followed by `/` or `h` are not a timestamp; they stay `stat.text`, with `ambiguous` at the first digit where the report read with that timestamp would give no `syntax` or `value` finding of its own ([amb.stat.time](#amb.stat.time)). | no | 7 bytes | p. 38/22; p. 104/80 |
| <a id="stat.grid"></a>`stat.grid` | Locator with symbol | Directly after `stat.dti`, never with `stat.time`: [`grid.loc`](03-position.md#grid.loc), then [`sym.table`](02-fields.md#sym.table), then [`sym.code`](02-fields.md#sym.code), then `SP` or the end of the field. The 6-byte locator is tried first, then the 4-byte one. The letter ranges are those of [amb.grid.range](03-position.md#amb.grid.range): **[agreed]** a first-pair letter outside `A`–`R`, in either case, means the bytes are no locator and are `stat.text`, with no finding; a fifth or sixth byte outside `A`–`X`, in either case, means the locator has no subsquare, and the 4-byte locator is tried. Lower-case locator letters, in the subsquare too, are recognised and give `syntax` ([amb.grid.case](03-position.md#amb.grid.case)). When a locator and symbol match but the next byte is not `SP`, the bytes are `stat.text`, with no finding ([amb.stat.grid](#amb.stat.grid)). | no | the byte before `SP` or end of field | p. 42/26; p. 105/81; p. 106/82 |
| <a id="stat.text"></a>`stat.text` | Status text | The rest of the field; its bytes are checked as [`cmt.text`](02-fields.md#cmt.text). At most 62 bytes with neither `stat.time` nor `stat.grid`, 55 after `stat.time`, 54 after `stat.grid` counting the leading `SP`. Longer gives `value` at the first byte past the limit, also when the text is valid UTF-8 and its character count is within the limit ([amb.stat.len](#amb.stat.len)). | no | end of field | p. 104/80; p. 106/82 |
| <a id="stat.beam"></a>`stat.beam` | Beam heading and power | The last 3 bytes of `stat.text` when they are `^`, then a heading byte (a digit or `A`–`Z`), then a power byte 0x31–0x4B (`1` to `9`, `:` to `@`, `A` to `K`). A depth + 1 token inside `stat.text`. Any other last 3 bytes are plain text. | no | end of field | p. 105/81 |
| <a id="stat.freq"></a>`stat.freq` | Frequency in status text | The rules of section 7 apply at the start of `stat.text`, after the leading `SP` when there is a `stat.grid`. | no | — | p. 111/87; p. 115/91 |

**[proposed]** Tokens. A `stat.time` is a
[`time.dhm`](02-fields.md#time.dhm) token, as a position timestamp is in
03. A `stat.grid` token covers the locator and the symbol, with
[`grid.loc`](03-position.md#grid.loc), [`sym.table`](02-fields.md#sym.table)
and [`sym.code`](02-fields.md#sym.code) one level deeper; a locator
letter that fails gives one `syntax` finding on `stat.grid`, at the first
such letter. The `ambiguous` finding of [amb.stat.time](#amb.stat.time)
is given on `stat.time`. `stat.text` is a free-text field for
[`cmt.noarchive`](02-fields.md#cmt.noarchive); the other items of
02 section 8.2 and [`tlm.b91`](07-telemetry.md#tlm.b91) are not looked
for in it. `stat.beam` and the tokens of section 7 lie one level below
`stat.text`. No other field of this file is named a free-text field:
`udf.data` holds data whose meaning its user defines, and `inv.data`
holds bytes sent as invalid or for a test. A `'!x!'` in either is
therefore a match outside free text, and gets the `ambiguous` finding
that the **[agreed]** search of
[02 section 8.2](02-fields.md#82-items-found-inside-a-comment) gives
there. The "No finding" of the `inv.data` row and the "no finding" for
bytes outside `SP` to `~` in `udf.data` concern the bytes of those
fields, which this file does not check; they do not exempt the fields
from that search, which covers the whole information field.
**[agreed]** Neither field counts as free text for this search.

## 3. Station capabilities

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cap.dti"></a>`cap.dti` | Identifier | `<`, 1 byte. | yes | 1 byte | p. 31/17; p. 101/77 |
| <a id="cap.item"></a>`cap.item` | Capability | `cap.token`, optionally followed by `=` and `cap.value`. One or more items, separated by `cap.sep`. An empty field or an empty item gives `syntax`. | yes, at least one | `,` or end of field | p. 101/77 |
| <a id="cap.sep"></a>`cap.sep` | Separator | `,`, 1 byte. | between items | 1 byte | p. 101/77 |
| <a id="cap.token"></a>`cap.token` | Token | 1 or more bytes 0x21–0x7E other than `,` and `=` ([amb.cap.form](#amb.cap.form)). | yes | `=`, `,` or end of field | p. 101/77 |
| <a id="cap.value"></a>`cap.value` | Value | 1 or more bytes 0x21–0x7E other than `,`. An `=` with nothing after it gives `syntax`. For the tokens `MSG_CNT` and `LOC_CNT` the value is a count, so digits; any other byte gives `syntax`, as a byte outside the set ([README section 3](README.md#3-tokenizer-model)). | no | `,` or end of field | p. 101/77 |
| <a id="cap.pad"></a>`cap.pad` | Padding | One or more `SP` before or after a token or value. A token of its own; gives `ambiguous` at its first byte where the field read with the spaces as padding would give no `syntax` or `value` finding of its own ([amb.cap.form](#amb.cap.form)). | no | the next byte that is not `SP` | — |

**[proposed]** Tokens. Each item is a `cap.item` token at the level of
`cap.sep`, with its `cap.pad`, `cap.token` and `cap.value` one level
deeper; the `=` has no token. A token runs from its first to its last
byte that is not `SP` before the first `=`, and a value likewise after
it, so a `SP` inside one is a byte outside its set and gives `syntax`
there. An item of `SP` only is empty and has no `cap.pad`: `syntax` on
`cap.item` at its first byte, or where it was expected when it has no
bytes. Only `SP` before `=` gives `syntax` on `cap.token` at the
item's first byte; nothing or only `SP` after it gives `syntax` on
`cap.value` at the byte after `=`. Reading (b) of
[amb.cap.form](#amb.cap.form) divides the bytes as this reading does, so
it has no finding of its own and every `cap.pad` gets its `ambiguous`
finding.

## 4. General queries

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="qry.dti"></a>`qry.dti` | Identifier | `?`, 1 byte. | yes | 1 byte | p. 31/17; p. 102/78 |
| <a id="qry.type"></a>`qry.type` | Query type | 1 or more bytes `A`–`Z`. `APRS`, `IGATE` and `WX` are the general types. A directed type (`APRSD`, `APRSH`, `APRSM`, `APRSO`, `APRSP`, `APRSS`, `APRST`, `PING`) gives `value`; any other upper-case type gives `unstated`. A lower-case letter gives `syntax` ([amb.qry.type](#amb.qry.type)). | yes | `qry.end` | p. 101/77; p. 102/78 |
| <a id="qry.end"></a>`qry.end` | Closing mark | `?`, 1 byte. Missing gives `syntax`. | yes | 1 byte | p. 102/78 |
| <a id="qry.fp"></a>`qry.fp` | Target footprint | `qry.lat`, `,`, `qry.lon`, `,`, `qry.radius`: all or none. A partial footprint gives `syntax`. Allowed with any general type ([amb.qry.fp](#amb.qry.fp)). | no | end of field | p. 102/78 |
| <a id="qry.lat"></a>`qry.lat` | Latitude | A sign byte, `SP` for north or `-` for south, then 1 or more digits, then optionally `.` and 1 or more digits. A missing sign byte or `+` gives `syntax`; a magnitude above 90 gives `value`. | in `qry.fp` | `,` | p. 102/78 |
| <a id="qry.lon"></a>`qry.lon` | Longitude | As `qry.lat`, with `SP` for east and `-` for west, and a limit of 180. | in `qry.fp` | `,` | p. 102/78 |
| <a id="qry.radius"></a>`qry.radius` | Radius | Exactly 4 digits, miles. Any other length gives `syntax`. | in `qry.fp` | 4 bytes | p. 102/78 |

Bytes after `qry.end` that are not a footprint, or after `qry.radius`,
give `syntax` and form `residue`.

**[proposed]** Tokens and findings. `qry.type` runs from offset 1 to the
first `?`; a byte that is not an upper-case letter gives one `syntax`
finding, at the first such byte, and an empty type gives it at offset 1.
With no `?` in the field, the type is the run of letters from offset 1,
possibly empty, `qry.end` gives `syntax` where the `?` was expected,
and the rest is residue; an empty type and the missing `?` then both
give their finding at offset 1. The bytes after `qry.end` are a
footprint when they start with a number of the `qry.lat` form, with or
without its sign byte; other bytes give `syntax` on `qry.fp` at their
first byte and are residue. A `qry.fp` token covers the parts present,
with `qry.lat`, `qry.lon` and `qry.radius` one level deeper.
`qry.lat` and `qry.lon` each run to the next `,`, or to the end of the
field when there is none, and keep their token when their bytes are
wrong: one `syntax` finding, at the first byte that fails, where a sign
that is missing or `+` fails at the first byte of the coordinate, and a
`value` finding when the number is well formed and over its limit.
`qry.radius` is a fixed 4-byte field and takes up to 4 bytes after the
second `,`: a byte that is not a digit, or a missing digit at the end of
the field, gives one `syntax` finding on `qry.radius` at the first such
byte. A part with no bytes at all, between two `,` or after the last
one, is missing, and a missing `,` is missing at the end of the field:
each gives `syntax` on `qry.fp` where it was expected. Bytes after the
4 bytes of the radius, a fifth digit as well as text, cannot be counted
against the fixed field; they give `syntax` on `qry.fp` at their first
byte and are residue. This is how the "any other length" of the
`qry.radius` row is reported for a radius that is too long.

### 4.1 Directed queries

A directed query is a message whose text is `?`, a query type and,
optionally, the callsign of a heard station (p. 103/79).
[08-message.md](08-message.md) tokenizes the addressee and the
separator and hands over the text from offset 11. A text that does not
match the rows below is not a directed query; 08 reads it as a message.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="qry.dir.dti"></a>`qry.dir.dti` | Identifier | `:` at offset 0 of a message whose text matches the rows below (the `dti` of this field). | yes | 1 byte | p. 31/17; p. 103/79 |
| <a id="qry.dir.mark"></a>`qry.dir.mark` | Query mark | `?` at offset 11. | yes | 1 byte | p. 103/79 |
| <a id="qry.dir.type"></a>`qry.dir.type` | Query type | Exactly 5 bytes, one of `APRSD`, `APRSH`, `APRSM`, `APRSO`, `APRSP`, `APRSS`, `APRST`, `PING?`. | yes | 5 bytes | p. 101/77; p. 103/79 |
| <a id="qry.dir.sep"></a>`qry.dir.sep` | Separator | One `SP` between `qry.dir.type` and `qry.dir.call`; may be absent ([amb.qry.dir](#amb.qry.dir)). | no | 1 byte | p. 103/79 |
| <a id="qry.dir.call"></a>`qry.dir.call` | Heard station | 1 to 9 letters, digits or `-`. Meaningful for `APRSH`; with another type it gives `unstated`. | no | `SP` or end of field | p. 101/77; p. 103/79 |
| <a id="qry.dir.pad"></a>`qry.dir.pad` | Padding | `SP` bytes after `qry.dir.call`, to the end of the field. No finding ([amb.qry.dir](#amb.qry.dir)). | no | end of field | p. 103/79 |

**[proposed]** With no `qry.dir.call`, every `SP` after `qry.dir.type`
is `qry.dir.pad`; `qry.dir.sep` is only a `SP` directly before a
`qry.dir.call`.

A directed query carries no message identifier (p. 101/77, p. 103/79):
a text with `{` does not match the rows above and is read as a message.
The responses to directed queries are ordinary packets and are not
recognised as responses; which of them carry a message identifier is
set out in [amb.qry.response](#amb.qry.response).

## 5. User-defined data

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="udf.dti"></a>`udf.dti` | Identifier | `{`, 1 byte. | yes | 1 byte | p. 31/17; p. 121/97 |
| <a id="udf.user"></a>`udf.user` | User ID | 1 byte. `{` marks experimental use. A byte outside 0x21–0x7E gives `unstated`. | yes | 1 byte | p. 121/97 |
| <a id="udf.type"></a>`udf.type` | Packet type | 1 byte. A byte outside 0x21–0x7E gives `unstated`. | yes | 1 byte | p. 121/97 |
| <a id="udf.data"></a>`udf.data` | Data | Any bytes. Printable 7-bit ASCII (`SP` to `~`) is strongly recommended, not required; bytes outside it give no finding. | no | end of field | p. 121/97 |

Bytes outside `SP` to `~` in `udf.data` are counted by the field
inventory as a statistic of its own, as
[README section 3](README.md#3-tokenizer-model) sets out for fields
where APRS12c only recommends printable ASCII. An earlier draft gave
`discouraged` at the first such byte; it was dropped when the README
gave such bytes no finding, since many senders put UTF-8 there and the
finding would bury the others.

A field shorter than 3 bytes gives `syntax`; **[proposed]** on the
first of `udf.user` and `udf.type` that is missing, at the end of the
field. The list of assigned user
IDs (p. 122/98) is not checked: the document says there is no mechanism
to reserve a code.

## 6. Invalid or test data

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="inv.dti"></a>`inv.dti` | Identifier | `,`, 1 byte. | yes | 1 byte | p. 31/17; p. 123/99 |
| <a id="inv.data"></a>`inv.data` | Data | Any bytes, possibly none. No finding. | no | end of field | p. 123/99 |

## 7. Frequency specification

A frequency specification is found inside a comment or status text and
gives depth + 1 tokens there. It is looked for:

- at the start of the [`cmt.text`](02-fields.md#cmt.text) of a position
  report ([`pos.cmt`](03-position.md#pos.cmt),
  [`pos.cmpcmt`](03-position.md#pos.cmpcmt)) and of an object or item
  report ([`obj.cmt`](05-object-item.md#obj.cmt),
  [`item.cmt`](05-object-item.md#item.cmt)), that is after any data
  extension;
- at the start of the free text of a Mic-E status text, after the
  prefix, altitude, locator and any data extension
  ([04-mic-e.md section 5](04-mic-e.md#5-status-text));
- at the start of status text (`stat.freq`).

**[proposed]** A DF report is a position report
([03-position.md section 3](03-position.md#3-df-reports)), so its
comment, [`df.cmt`](03-position.md#df.cmt), is the `cmt.text` of a
position report after its data extension and its bearing and NRQ, and
a frequency is looked for at its start as at the start of `pos.cmt`.

Nowhere else in a comment is it looked for. A weather report has no
comment ([amb.wx.comment](06-weather.md#amb.wx.comment)), so no
frequency is looked for in one.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="freq.lead"></a>`freq.lead` | Delimiter | One `/` or `SP` directly before `freq.mhz`, `freq.uw` or `freq.ghz` ([amb.freq.lead](#amb.freq.lead)). | no | 1 byte | p. 115/91 |
| <a id="freq.mhz"></a>`freq.mhz` | Frequency in MHz | 10 bytes: 3 digits, `.`, 3 digits, `MHz`; or 3 digits, `.`, 2 digits, `SP`, `MHz`. `MHz` in another case is recognised and gives `syntax` ([amb.freq.case](#amb.freq.case)). | — | 10 bytes | p. 113/89; p. 114/90 |
| <a id="freq.uw"></a>`freq.uw` | Frequency above 999 MHz | As `freq.mhz`, with the first digit replaced by a letter `A`–`O`. The letter stands for the leading digits of the frequency in MHz: `A` 12, `B` 23, `C` 24, `D` 34, `E` 56, `F` 57, `G` 58, `H` 101, `I` 102, `J` 103, `K` 104, `L` 105, `M` 240, `N` 241, `O` 242, placed before the two digits that follow. | — | 10 bytes | p. 119/95; p. 120/96 |
| <a id="freq.ghz"></a>`freq.ghz` | Frequency in GHz | 10 bytes: 3 bytes each a digit or a leading `SP`, at least one digit, then `.`, 3 digits, `GHz`. | — | 10 bytes | p. 119/95 |
| <a id="freq.rx"></a>`freq.rx` | Alternate receive frequency | `SP`, then 3 digits, `.`, 3 digits, `rx`. Only directly after a frequency. | no | 10 bytes | p. 114/90; p. 115/91 |
| <a id="freq.tone"></a>`freq.tone` | Tone | `SP` (none when left-justified, see `freq.obj`), then 4 bytes: `T`, `t`, `C`, `c` or `D` and 3 digits; or `Toff`, `1750`, `l750` (lower-case L). `d` and 3 digits, or `toff`, is recognised and gives `unstated`. | no | 4 bytes, then `SP` or end of text | p. 114/90; p. 116/92; p. 117/93 |
| <a id="freq.offset"></a>`freq.offset` | Transmit offset | `SP`, then `+` or `-`, then 3 digits in units of 10 kHz. `-000` means simplex. | no | 4 bytes, then `SP` or end of text | p. 114/90; p. 117/93 |
| <a id="freq.range"></a>`freq.range` | Range | `SP`, then `R` (all directions) or `N`, `S`, `E`, `W` (one direction), 2 digits, then `m` (miles) or `k` (kilometres). Up to one per letter. Three digits are recognised and give `unstated` ([amb.freq.items](#amb.freq.items)). | no | 4 bytes, then `SP` or end of text | p. 114/90; p. 115/91; p. 116/92 |
| <a id="freq.dstar"></a>`freq.dstar` | D-STAR marker | `D-STAR`, then either `SP` or `>` and an 8-byte access repeater name (a callsign padded with `SP` to 6 bytes, `SP`, one module letter). After a frequency and an optional `freq.offset`, or at the start of the text with no frequency. | no | 7 or 15 bytes | p. 116/92 |
| <a id="freq.obj"></a>`freq.obj` | Left-justified items | In an object or item whose name is `freq.objname`, `freq.tone`, `freq.offset` and `freq.range` are looked for at the start of the comment with no frequency and no leading `SP`; the first item has no `SP` before it. Elsewhere, items are looked for only after a frequency ([amb.freq.nofreq](#amb.freq.nofreq)). | no | — | p. 113/89; p. 114/90; p. 115/91; p. 116/92 |
| <a id="freq.objname"></a>`freq.objname` | Frequency name | A classification of the 9-byte object or item name: 3 digits, `.`, 3 digits and 2 more bytes; or 3 digits, `.`, 2 digits and 3 more bytes. The extra bytes are any bytes the name allows. No finding ([amb.freq.objname](#amb.freq.objname)). | — | — | p. 113/89; p. 116/92; p. 117/93 |

After a frequency the items are taken in the order `freq.rx`,
`freq.tone`, `freq.offset`, `freq.range`, each optional, each starting
with one `SP` and followed by `SP` or the end of the text; `freq.dstar`
can follow `freq.offset`. An item that matches out of this order stays
text and gives `ambiguous` at its leading `SP`, where reading the items
in any order would give no `syntax` or `value` finding of its own
([amb.freq.items](#amb.freq.items)). The text after the last item is
comment text.

**[proposed]** Tokens and findings. The tokens of this section lie one
level below the comment or text. An item token includes its leading
`SP`, so `freq.rx` is 10 bytes and a 2-digit `freq.range` 5; a
left-justified item has none. `freq.dstar` does not include the `SP`
before it; its 7-byte form ends with the `SP` after `D-STAR`, and
`D-STAR` followed by neither `SP` nor `>` is text. In the access
repeater name the callsign is 1 to 6 upper-case letters or digits,
padded with `SP` to 6 bytes, and the module is an upper-case letter;
other bytes leave `D-STAR>` and what follows as text. `freq.dstar`
stands directly after the frequency or after its `freq.offset`, with no
`freq.rx` or `freq.tone` before it (section 10), and no item is looked
for after it. A `freq.range` whose letter is already taken ends the
items and is not out of order. Only a tone or an offset can be out of
order: `freq.rx` stands only directly after a frequency, and
`freq.range` is last. The `ambiguous` findings of
[amb.freq.items](#amb.freq.items) and
[amb.freq.nofreq](#amb.freq.nofreq) are given on the rule of the item
that the other reading would take. The `unstated` findings of
`freq.tone` and `freq.range` are at the first byte of the item after its
`SP`, and the `syntax` finding of [amb.freq.case](#amb.freq.case) at the
first byte of `MHz` that differs. `freq.objname` and `freq.obj` give no
token: the name stays [`obj.name`](05-object-item.md#obj.name) or
[`item.name`](05-object-item.md#item.name).

## 8. Ambiguities

A finding "of its own" is one that the other reading gives and this
reading does not. A `syntax` or `value` finding that both readings give
elsewhere in the packet does not stop an `ambiguous` finding
([README section 3](README.md#3-tokenizer-model)). The same holds for
every condition of this kind in this file.

<a id="amb.stat.time"></a>
### amb.stat.time

**Open in the document.** A status timestamp is DHM zulu only
(p. 38/22, p. 104/80). Nothing says how to read seven bytes at the start
of the text that have the shape of a local-time DHM or HMS timestamp.

**Readings.** (a) Text. (b) A timestamp in a form the status format does
not allow.

**Reading taken.** **[proposed]** (a), with `ambiguous` at the first
digit when the bytes are 6 digits and `/` or `h`. Visible in the bytes,
hence the `ambiguous` finding.

**In the bytes.** **[agreed]** Reading (b) means accepting the seven
bytes as a timestamp, as the decoders that accept these forms do, and
the `ambiguous` finding stays. **[proposed]** Under the test of
[README section 3](README.md#3-tokenizer-model), reading (b) counts
only where it accepts the whole report. The finding is `ambiguous` at
offset 1, the first digit, and is given where the six digits are
values that [`time.dhm`](02-fields.md#time.dhm) (with `/`) or
[`time.hms`](02-fields.md#time.hms) (with `h`) accepts with no `syntax`
or `value` finding, and the text after the seventh byte, checked as
`stat.text` after a `stat.time`, gives no `syntax` or `value` finding
of its own. A finding that both readings give on that text, such as
one for a control byte, does not stop it. An earlier draft also gave
no `ambiguous` finding where this reading reported any `syntax` or
`value` finding on the status text; that was dropped with the README
rule that counts only the other reading's own findings.

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| FAP | Takes 6 digits and `z` only. | `_status_parse`, FAP.pm:1294, 1302 |
| Dire Wolf | Takes 6 digits and `z` only. | decode_aprs.c:2429–2435 |
| aprslib | Takes the `z` form only for status. | `parse_status`, misc.py:16–24; `parse_timestamp`, common.py:77, 87–88 |
| Xastir | Accepts `z`, `Z`, `/`, `h` and `H` in status. | `extract_time`, db.c:8111; called for status at db.c:9744 |
| aprs-parser-rs | Accepts any timestamp form. | `Status::decode`, status.rs:63 |
| pdn-aprs | Takes the `z` form only. | `decode`, status.rs:17 |

**Corpus question.** How many status fields start with 6 digits and `/`
or `h`?

<a id="amb.stat.grid"></a>
### amb.stat.grid

**Open in the document.** The locator, 4 or 6 bytes, follows `>`
directly, then a symbol, and status text, when there is any, must
start with `SP` (p. 105/81, p. 106/82). Letters are sent in upper case
and may be received in either (p. 105/81). A 4-byte locator whose
symbol table is an overlay letter begins like a 6-byte locator.

**Readings.** (a) Require `SP` or the end after the symbol; try 6 bytes
first. An earlier draft listed a second reading that takes any
locator-and-symbol prefix, with or without the `SP`. It was dropped
because the document requires the `SP` (p. 105/81); Dire Wolf and
pdn-aprs read it so (see Decoders;
[README section 3](README.md#3-tokenizer-model)).

**Reading taken.** **[proposed]** (a). When the locator and symbol
match but `SP` is missing, the bytes are status text, with no finding;
recognising such reports is left to a deviation recogniser. With the
`SP`-or-end rule the 6- and the 4-byte readings cannot both complete,
since the byte after a 4-byte reading's symbol would have to be both
`SP` (or the end) and the 6-byte reading's table byte; trying 6 first
therefore decides nothing in a packet that conforms, and needs no
finding.

**[proposed]** The Maidenhead rules of
[03-position.md](03-position.md#amb.grid.range) apply to the locator.
**[agreed]** A first-pair letter outside `A`–`R`, in either case, means
the bytes are no locator: they are `stat.text`, with no finding, by the
rule for forms recognised by shape alone
([README section 3](README.md#3-tokenizer-model)). A fifth or
sixth byte outside `A`–`X`, in either case, is not a subsquare letter,
so the 6-byte locator does not match and the 4-byte one is tried. A
lower-case
letter is recognised and gives `syntax`, in the first pair and in the
subsquare alike ([amb.grid.case](03-position.md#amb.grid.case)). In a
`[` beacon a lower-case subsquare after an upper-case first pair gives
`ambiguous` at byte 5, because a listed reading there ends the locator
after 4 bytes. In a status report such a reading would contradict
p. 105/81, which lets letters be received in lower case, so it is not
a listed reading here
([README section 3](README.md#3-tokenizer-model)) and that finding is
not given.

Status texts that name a DMR talkgroup, such as `TG4605` followed by
`SP`, have the shape of a 4-byte locator with an overlay symbol. An
earlier draft recognised a first-pair letter outside `A`–`R` and gave
them `syntax` on `stat.grid`; the author decided first to keep that
finding and then, generalising, to read such bytes as status text.

**In the bytes.** **[proposed]** No `ambiguous` finding. An earlier
draft gave one at offset 1 where a locator and symbol were not followed
by `SP`, under the second reading since dropped.

**Decoders (read).** Dire Wolf tries 6 then 4 characters, accepts either
case, checks the symbol table only with a warning and warns about a
missing space (`get_maidenhead`, decode_aprs.c:4082;
decode_aprs.c:2447–2510).
pdn-aprs tries 6 characters and, only when they are not a locator, 4;
it needs a valid symbol and tolerates a missing space (`decode` and
`grid`, status.rs:12–70; `is_locator`, status.rs:72). Xastir leaves
locator and beam decoding as a to-do (db.c:9745). FAP does not read a
locator in status (`_status_parse`, FAP.pm:1291–1294).

**Corpus question.** How many status texts start with a locator and a
symbol, and how many of those lack the `SP` after them?

<a id="amb.stat.len"></a>
### amb.stat.len

**Open in the document.** The limits of 62, 55 and 54 are given in
"characters", and the text can hold UTF-8 (p. 104/80). A character and a
byte differ for non-ASCII text.

**Readings.** (a) Bytes. (b) Characters of the UTF-8 text.

**Reading taken.** **[proposed]** Count bytes; text over the limit gives
`value`. When the text is valid UTF-8 whose character count is within
the limit, reading (b) would accept it; that `value` finding is still
the only one given
([README section 3](README.md#3-tokenizer-model), precedence). An
earlier draft gave `ambiguous` in place of `value` in that case; it was
dropped when the README made a `syntax` or `value` finding the only
finding for such bytes. **[proposed]** Text within the limit in bytes
is within it in characters too, so where (a) accepts the text (b)
accepts it the same way; no `ambiguous` finding.

**Decoders (read).** FAP strips CR, LF and trailing spaces and applies
no limit (`_status_parse`, FAP.pm:1297–1309). Dire Wolf and pdn-aprs
apply no limit in the functions cited under
[amb.stat.grid](#amb.stat.grid).

**Corpus question.** How many status texts exceed the limit in bytes but
not in characters?

<a id="amb.cap.form"></a>
### amb.cap.form

**Open in the document.** Capabilities are tokens or token-value pairs
separated by commas (p. 101/77). No byte set is given for either, nor
whether spaces can surround them. The appendix lists an IGate report
with spaces after the commas (p. 155/131; see
[err.cap.bracket](#err.cap.bracket)).

**Readings.** (a) Visible bytes only, spaces not allowed. (b) Spaces
around items are padding.

**Reading taken.** **[proposed]** (a) for the token and value; `SP`
around them is taken as `cap.pad` with `ambiguous`, since (b) would also
match: visible in the bytes.

**In the bytes.** **[proposed]** Under the test of
[README section 3](README.md#3-tokenizer-model), reading (b) counts
only where it accepts the whole field. Each `cap.pad` token gets an
`ambiguous` finding at its first byte where the field, read with every
`cap.pad` as padding, would give no `syntax` or `value` finding of its
own. A finding that both readings give elsewhere in the field, such as
one for an empty item or for a count that is not digits, does not stop
it. An earlier draft gave no `ambiguous` finding wherever this reading
gave a `syntax` or `value` finding on the field; that was dropped with
the README rule that counts only the other reading's own findings.

**Decoders (read).** FAP splits at `,` and trims spaces around tokens
and values (`_capabilities_parse`, FAP.pm:1315–1340). pdn-aprs trims
spaces and needs at least one item (`capabilities`, other.rs:343–360).
Dire Wolf copies the text without splitting it
(`aprs_station_capabilities`, decode_aprs.c:2329–2339). aprslib lists
`<` as unsupported (parsing/\_\_init\_\_.py:47–65). Xastir does not
decode `<` and keeps the field as the station's status text
(db.c:15257–15281, 15431–15433).

**Corpus question.** How many `<` fields contain `SP`, and where?

<a id="amb.qry.type"></a>
### amb.qry.type

**Open in the document.** Query types are upper case (p. 101/77) and an
unrecognised query is ignored (p. 102/78). The general form lists three
types; the table mixes general and directed types. Nothing says what a
directed type in the general form means.

**Readings.** (a) Any upper-case type, unknown ones ignored by the
receiver. (b) Only the three general types.

**Reading taken.** **[proposed]** The three general types give no
finding; a directed type gives `value`, as a value outside the set
stated for this form; another upper-case type gives `unstated`, since
the receiver rule (ignore it) is stated but the type is not. The
`value` finding for a directed type is the only one given, although (a)
would accept the bytes
([README section 3](README.md#3-tokenizer-model), precedence). Otherwise
the type token is the same under both readings, and only the finding
differs: no `ambiguous` finding.

**Decoders (read).** Dire Wolf requires the closing `?` and takes any
type before it (decode_aprs.c:2625–2635). pdn-aprs requires a type of
upper-case letters (`query`, other.rs:254–263). Xastir answers `APRS?`
and `IGATE?` in upper case; the same words in another case are
recognised as an illegal query and not answered (`process_query`,
db.c:12995, 13030–13093). aprslib lists `?` as unsupported
(parsing/\_\_init\_\_.py:47–65). FAP has no branch for `?` in its
dispatch (`parseaprs`, FAP.pm:2579–2760), and its documentation lists
capability queries as not handled (FAP.pm:51).

**Corpus question.** Distribution of query types in `?` fields, and how
many have lower case.

<a id="amb.qry.fp"></a>
### amb.qry.fp

**Open in the document.** The footprint is described for the `APRS`
type (p. 102/78), but the diagram shows it for the general form. The
number format of latitude and longitude is "floating point degrees",
with no stated digit counts.

**Readings.** (a) Footprint with any general type. (b) With `APRS` only.

**Reading taken.** **[proposed]** (a), with the number format of
`qry.lat`. Not visible as an alternative: decided by the reading, no
`ambiguous` finding. **[proposed]** Under the test of
[README section 3](README.md#3-tokenizer-model), (b) divides a
footprint after `APRS` the same way, and after another type it would
give `syntax`, so it does not count.

**Decoders (read).** Dire Wolf reads the footprint leniently with a
numeric conversion, checks the latitude and longitude ranges and
accepts a radius above 0 and up to 9999 (decode_aprs.c:2652–2689).
pdn-aprs accepts a leading `SP`, a `-` or no sign at all, and requires a
4-digit radius and the range limits (`footprint` and
`footprint_degrees`, other.rs:284–321). Xastir ignores the footprint and
answers every `APRS?` query (db.c:13011–13030).

**Corpus question.** How many `?` fields carry a footprint, with which
types, and how many lack the leading `SP` of a positive value?

<a id="amb.qry.dir"></a>
### amb.qry.dir

**Open in the document.** A directed query is a message text of `?` and
a query type, optionally followed by a heard station's callsign that
needs no padding; the diagram gives the type 5 bytes and the callsign 0
to 9, with no separator between them (p. 103/79). The `APRSH` example
puts a space before the callsign and its note pads it to 9 bytes
([err.qry.directed](#err.qry.directed)). Directed queries never carry a
message identifier (p. 103/79). What a `?` text with another type, or
with a `{`, is, is not said.

**Readings.** (a) Type of exactly the listed 5 bytes; an optional `SP`;
an optional callsign; optional trailing `SP`. (b) As the diagram: the
callsign directly after the type, no padding. (c) As the example: one
`SP`, and the callsign padded to 9 bytes. For a text that does not fit:
(d) a message; (e) a malformed query.

**Reading taken.** **[proposed]** (a) and (d). A `{` anywhere, an
unlisted type, or a callsign of other bytes makes the text a message,
with no finding. Not visible as an alternative where (a) matches: the
type has a fixed length, so (b) and (c) place the callsign at the same
bytes. Decided silently; no `ambiguous` finding. **[proposed]** Under
the test of [README section 3](README.md#3-tokenizer-model), (e) would
report a malformed query where (d) reads a message, so it does not
count; and every text that (b) or (c) accepts, (a) accepts too.

**Decoders (read).** Dire Wolf takes any message text starting with `?`
as a directed query but decodes nothing after it; its header comment
reads the type as exactly 5 bytes and the `APRSH` example with a space
(`aprs_message`, decode_aprs.c:1960–1965; `aprs_directed_station_query`,
decode_aprs.c:2742–2789). pdn-aprs takes the listed types in upper case,
then an optional `SP`, a callsign and trailing spaces; a `{` anywhere, a
listed type in another case, or a bad callsign makes it a message; it
also accepts an unlisted upper-case type (`directed_query`,
message.rs:335–370). Xastir compares the first 5 bytes with each type,
only for messages to itself without an identifier, and does not act on
`APRSH` (`process_directed_query`, db.c:12758, 12836–12840; called at
db.c:14230). FAP and aprslib do not single out directed queries: no `?`
test in `_message_parse` (FAP.pm:1352–1398) or `parse_message`
(message.py:21–134).

**Corpus question.** Message texts starting with `?`, by type; how many
have a `SP` before the callsign, trailing padding, or a `{`.

<a id="amb.qry.response"></a>
### amb.qry.response

**Open in the document.** Responses to queries are sent once and carry
no message identifier, so that nobody acknowledges them (p. 101/77). The
rule names no query type and no exception. Yet `APRSM` asks the queried
station for the messages it still holds for the querying station, and
the example answer is a message ending in `{003` (p. 103/79), with the
text and number of the numbered message example of chapter 14
(p. 93/71). That page says a message without an identifier is not
acknowledged and a numbered one is repeated until it is acknowledged,
cancelled or timed out, so a message still outstanding is one that
carries a number.

**Readings.** (a) The rule covers every response, and the `{003` of the
`APRSM` example is an error. (b) The rule is stated too broadly: it
covers the replies that the queried station composes, and the `APRSM`
answer is the outstanding messages themselves, each with its
identifier.

**Reading taken.** **[agreed]** (b). The rule that a response carries
no message identifier applies to the replies that the queried station
composes for the query: `APRSD`, `APRSH`, and `APRST` or `PING?`.
`APRSO`, `APRSP` and `APRSS` are answered with objects, positions and
status reports, which never carry a message identifier. The `APRSM`
answer is the outstanding messages themselves, each keeping its
identifier, so that the querying station can acknowledge them; each is
an ordinary message
([08-message.md section 5](08-message.md#5-group-and-special-addressees)).
Reading (a) would have outstanding messages re-sent in a form that
cannot be acknowledged. APRS 1.0.1 has the rule and the example as
12c has them (1.0.1 PDF 87, 89). The older APRSdos protocol notes,
`PROTOCOL.TXT` on aprs.org (read through the Wayback Machine, capture
20240120045957), state the same once-only, unnumbered rule for
responses, list messages beside the position, status and objects that
a queried station sends again, and describe the `APRSD` and `APRSH`
answers as a single message written for the reply. An earlier draft
held the question as one half of
[err.qry.directed](#err.qry.directed), an error in the example; it was
moved here when the example was found consistent with chapter 14.

**In the bytes.** **[agreed]** Nothing in a packet marks it as a
response: a reply is an ordinary message, object, position or status
report, read by its own rules. The tokenizer recognises no packet as a
response and gives no finding.

**Decoders (read).** Of the decoders read, only Xastir answers directed
queries. It handles them only when they are addressed to itself and
carry no identifier (db.c:14205–14230). It answers `APRSD` and `APRST`
or `PING?`, and a `VER` query of its own, with composed messages
(db.c:12775–12820, 12936–12941, 12964–12969), all sent once through
`transmit_message_data` without an identifier (messages.c:955–1022),
whereas its ordinary outgoing messages carry a sequence number
(messages.c:1378). It answers `APRSP` by scheduling its position
(db.c:12896) and leaves `APRSM`, `APRSH`, `APRSO` and `APRSS`
unanswered, marked as not implemented (db.c:12836, 12855–12859, 12874,
12912). Dire Wolf decodes a directed query and sends nothing
(decode_aprs.c:1960–1966, 2742–2794). No source read implements
`APRSM`, so deployed code does not show whether its answer is numbered.

**Corpus question.** Messages sent by a queried station to the querying
station shortly after a directed query, by query type, and how many of
them carry `{`.

<a id="amb.freq.lead"></a>
### amb.freq.lead

**Open in the document.** Chapter 18 shows the frequency at the start of
the comment, with an optional `/` or space after a data extension, or
none (p. 115/91), and then says some radios do not handle a leading
space and the matter is being clarified.

**Readings.** (a) One optional `/` or `SP` before the frequency. (b) No
delimiter.

**Reading taken.** **[proposed]** (a). Not visible as an alternative:
decided by the reading, no `ambiguous` finding. **[proposed]** Under
the tests of [README section 3](README.md#3-tokenizer-model): reading
(b) would leave a frequency after a `/` or `SP` as comment text, but
every frequency written with a delimiter carries that, and the bytes of
one packet cannot narrow it, so it is decided by the reading and gives
no finding. A frequency with no delimiter is read the same way by both.

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| Dire Wolf | Optional `/` or space, then a digit or `A`–`O`, two digits, `.`, two digits and a digit or space, then `MHz` in any case. | `process_comment`, decode_aprs.c:4391, 4435 |
| pdn-aprs | Skips one leading `/` or `SP`, then reads the frequency. | comment.rs:241–243; `frequency`, comment.rs:664 |
| ebarkie/aprs | The encoder writes `/` between an extension and the frequency. | `renderFreq`, position.go:98–104 |
| FAP, aprslib, Xastir | No frequency parsing found. | no `MHz` in FAP.pm, aprslib/parsing/, Xastir db.c |

**Corpus question.** How many frequency specifications follow `/`, `SP`
or nothing?

<a id="amb.freq.case"></a>
### amb.freq.case

**Open in the document.** `MHz` is to be sent in that mixed case and
accepted in any case (p. 114/90). UAP §3.3 says it is case-sensitive.

**Readings.** (a) Recognise any case; another case gives `syntax`, as a
departure from the sending rule. (b) Recognise any case with no
finding, since receivers are told to accept it. An earlier draft listed
a reading that takes `MHz` in the stated case only and leaves another
case as comment text, as UAP §3.3 has it. It was dropped because
p. 114/90 tells receivers to accept any case
([README section 3](README.md#3-tokenizer-model)); none of the decoders
read does so.

**Reading taken.** **[proposed]** (a), the kind that
[README section 3](README.md#3-tokenizer-model) gives a departure from
a sending rule that receivers are told to accept. That finding alone is
given, although (b) would accept the bytes (precedence). Both readings
divide the bytes the same way and differ only in the kind of finding;
no `ambiguous` finding.

**Decoders (read).** Dire Wolf accepts any case and warns
(decode_aprs.c:4435, 4577–4583). pdn-aprs accepts any case
(`frequency`, comment.rs:666).

**Corpus question.** Case distribution of `MHz` in frequency
specifications.

<a id="amb.freq.items"></a>
### amb.freq.items

**Open in the document.** Tone and offset are described as having a
fixed layout, with range and other text after them (p. 112/88); the
examples put tone, offset and range in that order (p. 114/90,
p. 115/91), but no order is stated and range is written with two digits
only.

**Readings.** (a) The order tone, offset, range. (b) Any order.

**Reading taken.** **[proposed]** (a). An item out of order stays text
with `ambiguous`: visible in the bytes. A 3-digit range is recognised
with `unstated`.

**In the bytes.** **[proposed]** Under the test of
[README section 3](README.md#3-tokenizer-model), reading (b) counts
only where it accepts the whole comment or status text. The first item
that (a) leaves as text because it is out of order gets an `ambiguous`
finding at its first byte, its leading `SP`, where reading (b), taking
that item and the items after it in any order, would give no `syntax`
or `value` finding of its own on the text. Where this reading already
gives a
`syntax` or `value` finding on those bytes, that finding alone is given
(precedence). The 3-digit range is a matter of the finding kind, not of
how the bytes divide.

**Decoders (read).** Dire Wolf reads tone, offset and range in any order
(decode_aprs.c:4611–4692). pdn-aprs reads them in the fixed order, each a
space and four bytes followed by a space or the end; it reads only the
`R` range, with 2 digits (`frequency`, comment.rs:693–735). The
ebarkie/aprs encoder writes the range with 3 digits and positive offsets
without `+` (`Render`, freq.go:20–60).

**Corpus question.** Order of the items after a frequency, and the
number of range digits.

<a id="amb.freq.nofreq"></a>
### amb.freq.nofreq

**Open in the document.** The 2012 clarification says that when the
first 10 bytes hold no frequency, tone and offset are left-justified
(p. 114/90, p. 115/91). It appears among object examples; whether it
applies to every comment is not said.

**Readings.** (a) Only in objects and items named as frequencies. (b) In
any comment.

**Reading taken.** **[proposed]** (a). In other comments, a start that
matches a tone item stays text and gives `ambiguous`: visible in the
bytes. The same holds for an offset or a range item, which `freq.obj`
also reads at the start; an earlier draft named only the tone.

**In the bytes.** **[proposed]** Under the test of
[README section 3](README.md#3-tokenizer-model), reading (b) counts
only where it accepts the whole comment or status text. Where section 7
looks for a frequency outside a `freq.objname` object or item and finds
none, a start that matches `freq.tone`, `freq.offset` or `freq.range`
as `freq.obj` reads them, with no leading `SP`, gets an `ambiguous`
finding at its first byte, the first byte of the comment or text. It is
given only where reading (b), taking the items there as `freq.obj`
does, would give no `syntax` or `value` finding of its own on the text.
Where this
reading already gives a `syntax` or `value` finding on those bytes,
that finding alone is given (precedence).

**Decoders (read).** Dire Wolf reads tone, offset and range at the
comment start whether or not a frequency is present, and takes a
frequency from the object name (decode_aprs.c:4588–4600, 4611–4692).
pdn-aprs reads items only after a frequency (comment.rs:664).

**Corpus question.** How many comments outside frequency-named objects
start with a tone item?

<a id="amb.freq.objname"></a>
### amb.freq.objname

**Open in the document.** Frequency object names have four forms of 9
bytes, with other separators allowed in place of `-` (p. 116/92,
p. 117/93). Nothing separates such a name from another name that starts
with digits and a point.

**Readings.** (a) Any name of the two shapes. (b) Only with the
listed separators.

**Reading taken.** **[proposed]** (a). Not visible in the bytes; no
finding. **[proposed]** Under the tests of
[README section 3](README.md#3-tokenizer-model): reading (b) would read
a name of these shapes with an unlisted byte in its last places as an
ordinary name, and its comment then without left-justified items, but
every name of that kind carries this, and the bytes of one packet
cannot narrow it, so it is decided by the reading and gives no finding.

**Decoders (read).** Dire Wolf converts a name with a numeric
conversion and checks the result against amateur bands
(decode_aprs.c:4588–4600). pdn-aprs: no object-name frequency found in
comment.rs.

**Corpus question.** Object and item names of the two shapes, and the
bytes in their last positions.

## 9. Errata

<a id="err.stat.grid"></a>
### err.stat.grid

The locator status diagram gives the text 1 to 54 bytes and leaves its
column unshaded (p. 106/82), and shaded columns are the optional ones
(p. 12/2). Yet two of its examples have no text, and the prose speaks of
status text only for a report that has some (p. 105/81). The reading
follows the prose: the text is optional, 0 to 54 bytes.

Origin: introduced by the 12b/12c compilation. In APRS 1.0.1 the status
text column of this diagram is shaded, so optional, and agrees with the
examples (1.0.1 PDF 92, rendered). 12b already shows it unshaded (12b
PDF 108, rendered).

<a id="err.cap.bracket"></a>
### err.cap.bracket

Appendix 7 lists, among the merged APRS 1.1 items, an IGate status
report written as a "left bracket" followed by `IGate, MSG_CNT=N,
LOC_CNT=N`, with spaces after the commas (p. 155/131). Chapter 15 uses
`<` and `IGATE,MSG_CNT=n,LOC_CNT=n` (p. 101/77). "Left bracket" may mean
`[` or may loosely name `<`; the case and the spaces differ either way.
The reading follows chapter 15. A `[` field of that shape fails
[`grid.loc`](03-position.md#grid.loc).

Origin: a merge of APRS 1.0.1 text with a later addendum. The chapter 15
form is 1.0.1 text (1.0.1 PDF 87); the Appendix 7 line quotes the APRS
1.1 addendum list, which is marked as merged although chapter 15 was not
changed. 12b has both (12b PDF 103, and its Appendix 7).

<a id="err.qry.response"></a>
### err.qry.response

The general query examples answer with `/3402.78N11714.02W-` (p. 102/78),
which has the timestamp identifier and no timestamp, and no symbol table
byte. The reading follows the position diagrams of
[03-position.md](03-position.md).

Origin: already in APRS 1.0.1 (1.0.1 PDF 88). 12b has it (12b PDF 104).

<a id="err.qry.directed"></a>
### err.qry.directed

In the directed query part of chapter 15 (section 4.1,
[amb.qry.dir](#amb.qry.dir)), the heard callsign needs no filler spaces
and the diagram has no separator before it (p. 103/79), but the `APRSH`
example puts a space before it and its note says it is padded to 9
bytes. The reading accepts both callsign forms (amb.qry.dir).

An earlier draft also listed here the `{003` of the `APRSM` example
response against the rule that responses carry no message identifier
(p. 101/77). That half was moved to
[amb.qry.response](#amb.qry.response), which finds the rule stated too
broadly rather than the example wrong.

Origin: already in APRS 1.0.1, which has the diagram and the `APRSH`
example with its note (1.0.1 PDF 89). 12b has them unchanged (12b
PDF 105).

<a id="err.freq.offset"></a>
### err.freq.offset

The offset is three digits in units of 10 kHz (p. 117/93), so its range
is 0 to 9.99 MHz; p. 114/90 gives the limit as 9.90 MHz. The reading
follows the digit count and checks no range.

Origin: within an addendum. Chapter 18 is the APRS 1.2 frequency
specification, listed in Appendix 7 among the merged APRS 1.2 items, and
has no counterpart in APRS 1.0.1. 12b has the same text (12b PDF 118).
The addendum's own text was not read for this file.

<a id="err.freq.netmtg"></a>
### err.freq.netmtg

The frequency object format writes `NETxxxxxx` and `MTGxxxx`; the
examples given for them are `Net Tu9PM` and `Mg3rdTu` (p. 116/92,
p. 117/93), whose first letters do not match the template. Neither is
tokenized.

Origin: within an addendum. The template and the examples come from the
same frequency object text of the APRS 1.2 frequency material, which is
not in APRS 1.0.1. 12b has them (12b PDF 120, 121).

## 10. Open items

- Whether the tokenizer checks a capability value for tokens other than
  `MSG_CNT` and `LOC_CNT`, if more tokens appear in the corpus.
- `freq.dstar` is placed after a frequency and offset; whether a tone
  can stand between them is not shown by the examples.
- Whether a directed query of an unlisted type (pdn-aprs accepts one)
  should be recognised with `unstated` instead of being read as a
  message ([amb.qry.dir](#amb.qry.dir)).
