# Objects and items

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` chapter 11, p. 75/57 to p. 80/62, with p. 49/31 and Appendix 1, in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, tokenizer model and decoder commits: [README](README.md). |

## 1. Scope

This file reads APRS12c chapter 11: object reports, item reports, area
objects with their descriptor and corridor width, signposts, and the
obsolete object format without a data type identifier.

The data type identifiers `';'` and `')'` are classified by
[01-frame.md](01-frame.md). Timestamps, positions, symbols, data
extensions and the comment are read by the rules of
[02-fields.md](02-fields.md); this file says which of them follow which
and where. Weather data carried by objects, and storm data carried by
objects and items, are read in [06-weather.md](06-weather.md) (section
7). This file tokenizes object and item
names; [09-other.md](09-other.md#freq.objname) classifies a name that is
a frequency and reads the frequency items in the comment
([`freq.obj`](09-other.md#freq.obj)).

Offsets in this file count from the first byte of the information field,
which holds the data type identifier at offset 0.

## 2. Object report

An object report is the identifier `';'`, a fixed nine-byte name, a live
or killed byte, a timestamp, a position in either form, an optional data
extension after an uncompressed position, and a comment (p. 76/58,
p. 132/108).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.dti"></a>`obj.dti` | Data type identifier | `';'` at offset 0. | Required | 1 byte | p. 31/17, p. 76/58 |
| <a id="obj.name"></a>`obj.name` | Object name | Offsets 1 to 9, each byte 0x20–0x7E. Trailing SP are padding and not part of the name; case is significant. Nine SP give a `syntax` finding ([amb.obj.name](#amb.obj.name)). | Required | 9 bytes | p. 76/58 |
| <a id="obj.state"></a>`obj.state` | Live or killed | Offset 10: `'*'` live, `'_'` killed. Any other byte gives a `syntax` finding ([amb.obj.name](#amb.obj.name)). | Required | 1 byte | p. 76/58 |
| <a id="obj.time"></a>`obj.time` | Timestamp | Offsets 11 to 17: [`time.dhm`](02-fields.md#time.dhm) or [`time.hms`](02-fields.md#time.hms). **[proposed]** Required ([amb.obj.time](#amb.obj.time)). | Required | 7 bytes | p. 76/58, p. 153/129 |
| <a id="obj.pos"></a>`obj.pos` | Position | From offset 18. A digit there starts an uncompressed position: [`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code), 19 bytes. Otherwise a compressed block, [`cmp.block`](02-fields.md#cmp.block), 13 bytes. | Required | 19 or 13 bytes | p. 55/37, p. 76/58 |
| <a id="obj.ext"></a>`obj.ext` | Data extension | After an uncompressed position only: [`ext.csespd`](02-fields.md#ext.csespd), [`ext.phg`](02-fields.md#ext.phg) or [`ext.phgr`](02-fields.md#ext.phgr), [`ext.rng`](02-fields.md#ext.rng), [`ext.dfs`](02-fields.md#ext.dfs) or the area descriptor [`ext.area`](02-fields.md#ext.area) (section 4). | Optional | 7 bytes; 9 for `ext.phgr` | p. 76/58, p. 33/19 |
| <a id="obj.cmt"></a>`obj.cmt` | Comment | The rest, read as [`cmt.text`](02-fields.md#cmt.text) with the comment items of [02-fields.md](02-fields.md#82-items-found-inside-a-comment) section 8, the braces of sections 4 and 5 below, a frequency at its start ([09-other.md](09-other.md#7-frequency-specification)), and base-91 telemetry, which gives `unstated` here ([amb.tlm.b91.where](07-telemetry.md#amb.tlm.b91.where)). At most 36 bytes after an extension, the 9-byte [`ext.phgr`](02-fields.md#ext.phgr) included, as in [amb.pos.cmtlen](03-position.md#amb.pos.cmtlen), and 43 without; **[proposed]** 43 after a compressed position ([err.obj.cmplen](#err.obj.cmplen)). A longer comment gives a `value` finding. | Optional | End of information field | p. 76/58, p. 132/108 |

The token of byte 0 carries `obj.dti`, so that the tokens show the
packet as an object report
([README section 3](README.md#3-tokenizer-model)). **[proposed]** An
object that is classified as a weather report carries
[`wx.obj`](06-weather.md#wx.obj) there instead (section 7).

After a compressed position no data extension follows; the block's own
`cs` bytes, [`cmp.cs`](02-fields.md#cmp.cs), carry course and speed or
range (p. 76/58). Seven bytes there that look like an extension are
comment text.

APRS 1.1 calls compressed objects not recommended on RF, and the item
format not recommended on RF altogether (p. 76/58, p. 77/59).
**[agreed]** A compressed object gives a `discouraged` finding at the
first byte of `obj.pos`; every item report gives one at `item.dti`
(section 3). **[proposed]** The finding is given wherever the packet
was heard: the TNC2 line does not show reliably whether the packet was
or will be sent on RF.

Frequency objects mark a permanent object with the timestamp `111111z`
(p. 117/93), which is also an ordinary valid time. It gets no finding:
[09-other.md](09-other.md#1-scope) lists it among the chapter 18
conventions that are not tokenized.

## 3. Item report

An item report is the identifier `')'`, a name of three to nine bytes
ended by the live or killed byte, a position, an optional data extension
and a comment. It has no timestamp (p. 77/59, p. 132/108).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="item.dti"></a>`item.dti` | Data type identifier | `')'` at offset 0. Gives a `discouraged` finding (section 2). | Required | 1 byte | p. 31/17, p. 77/59 |
| <a id="item.name"></a>`item.name` | Item name | From offset 1: bytes 0x20–0x7E other than `'!'` and `'_'`, 3 to 9 of them. **[proposed]** A name of 1 or 2 bytes, or of more than 9, gives a `value` finding; an empty name, or no `'!'` or `'_'` at all, a `syntax` finding ([amb.item.name](#amb.item.name)). | Required | The first `'!'` or `'_'` | p. 77/59 |
| <a id="item.state"></a>`item.state` | Live or killed | `'!'` live, `'_'` killed. | Required | 1 byte | p. 77/59 |
| <a id="item.pos"></a>`item.pos` | Position | As `obj.pos`, directly after `item.state`. | Required | 19 or 13 bytes | p. 77/59 |
| <a id="item.ext"></a>`item.ext` | Data extension | As `obj.ext`. | Optional | 7 bytes | p. 77/59 |
| <a id="item.cmt"></a>`item.cmt` | Comment | As `obj.cmt`. | Optional | End of information field | p. 77/59, p. 132/108 |

The token of byte 0 carries `item.dti`, so that the tokens show the
packet as an item report.

## 4. Area objects

An object or item whose symbol is the alternate table `'\'` with code
`'l'` (0x6C) is an area object: a circle, line, ellipse, triangle or box
(p. 78/60). The code is printed as a script ℓ; the byte is the lower-case
letter. **[agreed]** In an object or item report with that symbol, the
seven bytes after the symbol code are the area descriptor, read as
[`ext.area`](02-fields.md#ext.area), and no other extension is tried;
if they do not fit the descriptor, the tokenizer reports `syntax` on it
([amb.area.symbol](#amb.area.symbol)). With any other symbol no
descriptor is read. Position reports never carry the descriptor
([amb.pos.ext](03-position.md#amb.pos.ext)).

The parts of the descriptor are tokens one level below
[`ext.area`](02-fields.md#ext.area):

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="area.type"></a>`area.type` | Shape | `'0'`–`'9'`. 0, 2, 3 and 4 are an open circle, ellipse, triangle and box, and 5, 7, 8 and 9 the same shapes filled; 1 and 6 are lines drawn down to the right and down to the left. | Required | 1 byte | p. 78/60 |
| <a id="area.lat"></a>`area.lat` | Latitude offset | Two digits. | Required | 2 bytes | p. 78/60 |
| <a id="area.color"></a>`area.color` | Colour | Two bytes giving the colour number 0 to 15 in decimal, with `'/'` in place of a leading zero: `'/'` and `'0'`–`'9'`, or `'1'` and `'0'`–`'5'`. | Required | 2 bytes | p. 49/31, p. 78/60 |
| <a id="area.lon"></a>`area.lon` | Longitude offset | Two digits. | Required | 2 bytes | p. 78/60 |
| <a id="area.corridor"></a>`area.corridor` | Corridor width | In the comment of a type `'1'` or `'6'` area: `'{'`, one or more digits (miles either side of the line), `'}'`. **[proposed]** Only at the start of the comment. When the comment does not start with one, the first braces of that shape later in the comment are comment text with an `ambiguous` finding at their `'{'` ([amb.area.braces](#amb.area.braces)). | Optional | The `'}'` | p. 80/62 |

The tokenizer checks the digits and does not compute the offsets. The
scale is in [err.area.sender](#err.area.sender), and the stated size
range in [err.area.size](#err.area.size).

## 5. Signposts

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.signpost"></a>`obj.signpost` | Signpost text | In the comment of an object or item with symbol `'\'` `'m'`: `'{'`, 1 to 3 bytes 0x20–0x7E other than `'{'` and `'}'`, `'}'`. **[proposed]** The first such braces anywhere in the comment. When they do not stand at the start of the comment they give an `ambiguous` finding at their `'{'`; later candidates are comment text with no finding ([amb.area.braces](#amb.area.braces)). | Optional | The `'}'` | p. 80/62, p. 153/129 |

**[proposed]** Corridor widths and signpost text are read in object and
item reports only, as chapter 11 describes them. The area descriptor is
limited in the same way by section 4.

## 6. Obsolete object format

Some stations sent objects without the `';'` identifier; the form is
obsolete and is to be taken as a status report (p. 80/62). No layout is
given.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.obsolete"></a>`obj.obsolete` | Object without identifier | **[agreed]** Only when byte 0 is not an assigned identifier, which [01-frame.md](01-frame.md#7-data-type-identifier) defines and from where it hands the field here: `obj.name` at offsets 0 to 8, `obj.state` at 9, then `obj.time`, `obj.pos`, `obj.ext` and `obj.cmt` as in section 2. Gives an `obsolete` finding ([amb.obj.obsolete](#amb.obj.obsolete)). | Optional | End of information field | p. 80/62 |

**[proposed]** Token structure. For an obsolete object there is no
identifier byte: the `obj.obsolete` token covers the whole field at
depth 0, and the object field tokens of
[05-object-item section 2](#2-object-report) lie one level deeper.
No `obj.dti` token is given, and byte 0 is the first byte of `obj.name`
at depth 1. [01-frame.md](01-frame.md#7-data-type-identifier) states
the same.

## 7. Weather and storm data on objects

An object whose symbol code is `'_'`, in either position form, carries a
weather report in place of the data extension and comment. When at least
one byte follows the position block, everything after it is read by
[06-weather.md](06-weather.md#53-object) as [`wx.obj`](06-weather.md#wx.obj),
and neither `obj.ext` nor `obj.cmt` applies; an object that ends at the
symbol code is an ordinary object. **[proposed]** An object read as
weather is classified as a weather report: the token of byte 0 carries
`wx.obj` in place of `obj.dti`, as
[06-weather.md section 2](06-weather.md#2-recognition) and
[README section 3](README.md#3-tokenizer-model) state, and the object
header and position keep their own IDs. Items with symbol code `'_'`
are not read as weather
([amb.wx.carriers](06-weather.md#amb.wx.carriers)). The Appendix 1
weather object diagram with `'*'` as identifier is an erratum
([err.wx.object-dti](06-weather.md#err.wx.object-dti)).

An object or item with symbol code `'@'` whose extension is
[`ext.csespd`](02-fields.md#ext.csespd) may carry storm data in place of
the comment; [06-weather.md](06-weather.md#8-storm-data) says when it is
read, and the bytes after the storm fields are `obj.cmt` or `item.cmt`.

## 8. Ambiguities

Decoder behaviour below was read in the source at the commits listed in
the [README](README.md#4-decoders-consulted), not run.

<a id="amb.obj.time"></a>
### amb.obj.time

- **Open.** p. 76/58 and the release notes on p. 151/127 and p. 153/129
  say an object always has a timestamp; p. 75/57 calls it optional, and
  the area
  template (p. 78/60) and the FLIGHTPTH example (p. 80/62) have none.
- **Readings.** (a) Required. (b) Optional, detected by its shape.
- **Reading taken.** **[proposed]** (a), as the diagram and most
  decoders read have it. A missing timestamp gives a `syntax` finding at
  offset 11 and parsing stops there; recognising the position at offset
  11 is left to a deviation recogniser. Visible in the bytes. Reading
  (b) would accept such a report, but the `syntax` finding alone is
  given, with no `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence).
- **Decoders.**

  | Decoder | Reads | Where |
  |---|---|---|
  | FAP | Required: six digits and `'z'`, `'h'` or `'/'`, or an error. | `_object_to_decimal`, `FAP.pm:1237` |
  | Dire Wolf | Fixed layout: offsets 11 to 17 are always the timestamp. | `aprs_object`, `decode_aprs.c:2169` |
  | aprslib | Optional: six digits and any seventh byte are taken as a timestamp when present. | `parse_timestamp`, `common.py:80`, called at `position.py:40` |
  | Xastir | Required; also accepts `'Z'` and `'H'`. | `db.c:9810`; `extract_time`, `db.c:8071-8131`, case test at `db.c:8111` |
  | aprsc | Offset 17 must be `'z'`, `'h'` or `'/'`. | `parse_aprs_object`, `parse_aprs.c:913` |
  | pdn-aprs | Missing timestamp tolerated as a defect. | `object`, `object.rs:42-58` |
  | javAPRSlib | Fixed offsets. | `ObjectField.java:65-73` |

- **Corpus question.** Object reports whose offsets 11 to 17 are not a
  timestamp but start a position; object reports with `111111z`.

<a id="amb.obj.name"></a>
### amb.obj.name

- **Open.** The name is fixed at nine bytes of printable ASCII, padded
  with trailing spaces (p. 76/58). Not stated: an all-space name, leading
  spaces, `'*'` or `'_'` inside the name, and what to do when offset 10
  is not `'*'` or `'_'` because the sender did not pad the name.
- **Readings.** (a) Strict offsets; any 0x20–0x7E byte in the name.
  (b) Scan for the first `'*'` or `'_'` and take what precedes it.
- **Reading taken.** **[proposed]** (a). Leading spaces and `'*'` or `'_'`
  inside the nine bytes are part of the name. A name of nine SP gives
  `syntax`, as no name is left once the padding is removed. A byte other
  than `'*'` or `'_'` at offset 10 gives `syntax` on `obj.state`;
  reading (b) is left to a deviation recogniser. Visible in the bytes,
  under the test of [README section 3](README.md#3-tokenizer-model):
  **[proposed]** a `'*'` or `'_'` inside the nine bytes gives an
  `ambiguous` finding at the first such byte only when reading (b) would
  parse the rest of the report from there: with the name ended at that
  byte, the bytes after it are an `obj.time`, an `obj.pos` and what may
  follow it, with no `syntax` or `value` finding. Otherwise reading (b)
  fails on the packet, and the byte is part of the name with no finding.
  An earlier draft gave the finding for every such byte. Where reading
  (b) would accept bytes that this reading reports as `syntax`, that
  finding alone is given, with no `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence). Leading
  spaces give no finding, since reading (b) keeps them too.
- **Decoders.** FAP: nine bytes 0x20–0x7E, then `'*'` or `'_'`
  (`FAP.pm:1237`). Dire Wolf: copies nine bytes, trims trailing spaces,
  notes a bad state byte and continues (`decode_aprs.c:2156-2167`).
  aprslib: nine bytes 0x20–0x7E, then `'*'` or `'_'` (`position.py:24`).
  Xastir: nine bytes, trailing spaces removed, printable and not empty
  (`db.c:15560-15571`; `valid_object`, `objects.c:74`). aprsc: state byte
  at offset 10, name 0x20–0x7E and not all spaces
  (`parse_aprs.c:906-933`). pdn-aprs: state byte at offset 10, otherwise
  the first `'*'` or `'_'` in offsets 1 to 9 as a tolerated defect; the
  name printable and not empty after trimming (`object.rs:14-36`).
- **Corpus question.** Object reports whose offset 10 is not `'*'` or
  `'_'`, and where the first such byte lies; names that are all spaces,
  start with a space, or hold bytes above 0x7E.

<a id="amb.item.name"></a>
### amb.item.name

- **Open.** The name is 3 to 9 bytes ended by the first `'!'` or `'_'`
  (p. 77/59). Not stated: what to do with a shorter or longer name, or
  with no terminator.
- **Readings.** (a) The first `'!'` or `'_'` ends the name; a length
  outside 3 to 9 is an error. (b) Search only the bytes where a 3 to 9
  byte name can end. (c) A `'!'` or `'_'` among the first three bytes is
  part of the name, since a name has at least three.
- **Reading taken.** **[proposed]** (a), with a length outside 3 to 9
  giving `value`, as a field outside its stated length; an empty name or
  no terminator gives `syntax`. Visible in the bytes. Reading (c) can
  differ only where the first `'!'` or `'_'` is among the first three
  bytes after the identifier, and there reading (a) already gives a
  `value` or `syntax` finding, which alone is given, with no `ambiguous`
  beside it ([README section 3](README.md#3-tokenizer-model),
  Precedence). The same holds where reading (b) would accept a name that
  reading (a) reports.
- **Decoders.** FAP: 3 to 9 bytes, then `'!'` or `'_'`
  (`_item_to_decimal`, `FAP.pm:1449`). Dire Wolf: the first `'!'` or
  `'_'` within nine bytes, no minimum (`aprs_item`,
  `decode_aprs.c:2273-2289`). aprslib: does not parse items
  (`__init__.py:53`). Xastir: the first `'!'` or `'_'` within nine bytes,
  then its object-name check of 1 to 9 printable bytes
  (`db.c:15575-15597`; `valid_object`, `objects.c:74-93`). aprsc: 3 to 9
  printable bytes (`parse_aprs_item`, `parse_aprs.c:958-985`). pdn-aprs:
  looks for the terminator from offset 4 on, so reading (c) (`item`,
  `object.rs:74-89`). javAPRSlib: the first `'!'` if that gives 1 to 9
  bytes, else the first `'_'`, in which case the name it takes is one
  byte too long and ends with the `'_'` (`ItemField.java:50-64`).
- **Corpus question.** Offsets of the first `'!'` or `'_'` in item
  reports; names of 1, 2 or more than 9 bytes.

<a id="amb.area.symbol"></a>
### amb.area.symbol

- **Open.** A descriptor whose colour starts with `'/'`, such as
  `710/310`, has the shape of course and speed (p. 45/27, p. 80/62). Only
  the `'\'` `'l'` symbol separates them, and the document does not say
  that the symbol decides, nor what follows from the symbol without a
  descriptor.
- **Readings.** (a) The symbol decides; with it, only a descriptor.
  (b) The bytes decide. (c) With the symbol, a descriptor first, else
  another extension.
- **Reading taken.** **[agreed]** (a), in object and item reports only:
  with the symbol, bytes that do not fit give `syntax` and no other
  extension is tried; without it, `710/310` is
  [`ext.csespd`](02-fields.md#ext.csespd), whose course 710 is out of
  range. Where reading (b) or (c) would accept bytes that this reading
  reports as `syntax` or `value`, that finding alone is given, with no
  `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence). Every
  course and speed extension also has the shape of a descriptor; that
  ambiguity is carried by every such extension, is decided by the
  symbol, and gives no finding.
- **Decoders.** FAP: lists area objects and signposts as not handled
  (`FAP.pm:45`). Dire Wolf: tests for a literal `'T'` as the first byte
  and `"/C"` as the fourth and fifth, which the example descriptors do
  not have; `710/310` is read as course and speed whatever the symbol
  (`data_extension_comment`, `decode_aprs.c:4148-4165`). aprslib: no area
  handling; its course and speed pattern takes `710/310`
  (`parse_data_extentions`, `common.py:139-146`). Xastir: with `'\'` `'l'`
  only, the descriptor before any other extension; type `'0'`–`'9'` and
  two-digit offsets, or the descriptor is dropped; colour `'/'` and a
  digit, or `'1'` and `'0'`–`'5'`, but any other byte at the fourth
  position is accepted and leaves the colour at its default
  (`db.c:8155-8159`; `extract_area`, `db.c:7909-7990`). aprs-parser-rs:
  a literal `'T'` as the first byte (`components/extensions.rs:246`).
  pdn-aprs: with
  the area symbol, the descriptor first, else the other extensions,
  reading (c) (`extension_at_start`, `comment.rs:338-346`; `area`,
  `comment.rs:528-555`).
- **Corpus question.** Among `'\'` `'l'` objects and items, extensions
  that do not fit the descriptor; among other symbols, course and speed
  extensions with a course above 360.

<a id="amb.area.braces"></a>
### amb.area.braces

- **Open.** The corridor width and the signpost text are both braces in
  the comment (p. 80/62). Their place in the comment, the corridor's digit
  count and the signpost's byte set are not stated; the examples put both
  at the start of the comment.
- **Readings.** (a) At the start of the comment only. (b) Anywhere.
  (c) Only with the line types or the signpost symbol.
- **Reading taken.** **[proposed]** (c) in all cases. Corridor: (a), one
  or more digits, since only a line area carries one and its comment
  follows the descriptor. Signpost: (b), the first well-formed braces,
  since the text says only "in the comment".
- **In the bytes.** **[proposed]** Visible, under the test of
  [README section 3](README.md#3-tokenizer-model), in one case each.
  Corridor: when a line area's comment does not start with a corridor,
  the first braces of corridor shape later in it, which reading (b)
  would take as the corridor, are comment text with an `ambiguous`
  finding at their `'{'`. When the comment starts with a corridor, (a)
  and (b) both take that one, and later braces are text under both, with
  no finding. Signpost: when the braces taken do not stand at the start
  of the comment, reading (a) would leave them as text, so they give an
  `ambiguous` finding at their `'{'`. A second candidate is text under
  every reading listed, so it gives no finding. An earlier draft gave
  `ambiguous` for every later corridor-shaped braces and for every
  second signpost candidate; neither case meets the test.
- **Decoders.** Xastir: corridor only for types 1 and 6 and only at the
  start of the comment, a decimal number (`db.c:7999-8030`); signpost
  only for `'\'` `'m'`, the first `'{'` with 1 to 3 bytes and `'}'`
  anywhere (`extract_signpost`, `db.c:7670-7720`, called at
  `db.c:8362-8366`). pdn-aprs: the first well-formed braces anywhere, 1 to
  3 bytes, printable for a signpost and digits for a corridor (`braces`,
  `comment.rs:269-296`). FAP lists them as not handled (`FAP.pm:45`); no
  brace handling was found in the Dire Wolf, aprslib or aprsc files read.
- **Corpus question.** Where braces stand in the comments of `'\'` `'l'`
  and `'\'` `'m'` objects and items; length and bytes of their content.

<a id="amb.obj.obsolete"></a>
### amb.obj.obsolete

- **Open.** Objects without `';'` are obsolete and are to be read as
  status reports (p. 80/62), but no layout is given and a status report
  has its own identifier `'>'`.
- **Readings.** (a) Not recognised; the packet is classified by its first
  byte. (b) The object layout shifted to offset 0, recognised only where
  byte 0 is not an assigned identifier. (c) Status text.
- **Reading taken.** **[agreed]** (b) with an `obsolete` finding, so
  that the form is counted rather than lost. It is tried before the
  field is given the `unknown-format` verdict. Where byte 0 is an
  assigned identifier, that identifier decides and this rule is not
  tried. Decided by the reading: readings (a) and (c) would class every
  field of this form differently, so the question is carried by every
  instance and gives no `ambiguous` finding
  ([README section 3](README.md#3-tokenizer-model)); the `obsolete`
  finding marks the form.
- **Decoders.** None read tries the object layout without `';'`. FAP and
  aprslib, with an unrecognised first byte, look for a `'!'` within the
  first 40 bytes and read a position from there (`FAP.pm:2737-2766`;
  `__init__.py:206-209`). Dire Wolf does nothing for an unknown first
  byte (`decode_aprs.c:499-501`).
- **Corpus question.** Information fields whose bytes 0 to 9 are nine
  name bytes and `'*'` or `'_'`, followed by a timestamp and a position.

## 9. Errata

<a id="err.obj.time"></a>
### err.obj.time

p. 75/57 calls the object timestamp optional; p. 76/58 and p. 153/129 say
an object always has one, and the template on p. 78/60 and the FLIGHTPTH
example on p. 80/62 omit it. The reading follows p. 76/58
([amb.obj.time](#amb.obj.time)).

Origin: already in APRS 1.0.1: the timestamp is optional on PDF p. 67
(printed 57) and always present on PDF p. 68 (printed 58), and the
template and the FLIGHTPTH example on PDF p. 70 and p. 71 have none.
12b has it.

<a id="err.obj.cmplen"></a>
### err.obj.cmplen

The compressed object and item diagrams give the comment as 43 bytes,
shaded as optional, with no lower bound (p. 76/58, p. 77/59,
p. 132/108). A compressed position report allows 0 to 40 (p. 59/41,
p. 131/107), and the uncompressed object diagram 0 to 43. The reading
takes 0 to 43 from the object diagrams.

Origin: already in APRS 1.0.1: 43 for compressed objects and items on
PDF p. 68, p. 69 and p. 107, and 0 to 40 for compressed position reports
on PDF p. 51 and p. 106. 12b has it.

<a id="err.area.slash"></a>
### err.area.slash

The descriptor is written `Tyy/Cxx` and its colour called the `/C`
parameter (p. 49/31, p. 78/60), suggesting a fixed `'/'` at byte 4. The
colour table gives `'1'` there for colours 10 to 15, as in the example
`8101310` (p. 80/62). The reading follows the colour table.

Origin: already in APRS 1.0.1: `Tyy/Cxx` and the `/C` parameter on PDF
p. 41 (printed 31) and p. 70, and the colour table and `8101310` on PDF
p. 70 and p. 71. 12b has it.

<a id="err.area.size"></a>
### err.area.size

Area objects are said to range from 60 feet to 100 miles (p. 78/60).
Neither follows from the two-digit offsets. Derived here, with the
receiver rule of [err.area.sender](#err.area.sender), an offset is `yy`
squared divided by 1500 degrees: `yy` = 1 gives 1/1500 degree, about
243 feet of latitude, and `yy` = 99 gives 9801/1500, about 6.5 degrees
or some 450 statute miles. The reading follows the encoding: any two
digits are accepted, and the stated range is not checked.

Origin: inherited from APRS 1.0.1, 1.0.1 PDF p. 70. It does not fit
that version's scale either: there the offset is `yy` squared in
hundredths of a degree, so `yy` = 1 gives 0.01 degree, about 3600 feet,
and `yy` = 99 about 98 degrees (derived here). 12b has the same
sentence (12b PDF p. 80).

<a id="err.area.sender"></a>
### err.area.sender

The sender rule makes `yy` the square root of the offset in degrees
divided by 1500; the receiver rule makes the offset `yy` squared
divided by 1500 (p. 78/60). The two are not inverses: the sender rule
would need the offset multiplied by 1500. The example, a 4-minute
offset giving `yy` = 10 (p. 80/62), fits the receiver rule. The
tokenizer checks only the digits; the reading follows the receiver rule
and the example for decoding.

Origin: introduced by the 12b/12c compilation, when the change of scale
from 100 to 1500 was merged. APRS 1.0.1 states a single rule in
hundredths of a degree that agrees with its own example (1.0.1 PDF
p. 70 and p. 71). 12b already has the two conflicting rules and the
4-minute example (12b PDF p. 80 and p. 82). The page p. 78/60 names
aprs.org/aprs11/areaobjects.txt as the source of the 1500 scale; that
file was not read here.

<a id="err.area.gap"></a>
### err.area.gap

The template on p. 78/60 and the FLIGHTPTH example on p. 80/62 print
spaces before and after the ℓ symbol, while the text says the descriptor
follows the symbol code at once and the two SEARCH examples on
p. 80/62 have no gap (rendered pages checked). A space before the symbol
would itself be the symbol code. The reading takes the spaces as
typesetting: no byte between the symbol code and the descriptor. The
same defect was also entered as
[err.ext.areagap](02-fields.md#err.ext.areagap), which now points here.

Origin: introduced by the 12b/12c compilation. APRS 1.0.1 prints the
template and the FLIGHTPTH example with no space around the symbol (PDF
p. 70 and p. 71, rendered at 110 dpi; the text layer of that PDF shows
spaces that the page does not). 12b already has the spaces (PDF p. 80
and p. 82, rendered).

## 10. Open items

- The corpus questions in section 8.
- The `discouraged` findings of section 2 apply on RF only, by the
  document's words, and are given for every packet. Whether a
  q-construct in the path should limit them to packets heard on RF is
  open.
- ebarkie/aprs has no object or item decoder in the files read. The
  object and item handling of aprs-parser-rs was not read, apart from
  the area descriptor test cited in
  [amb.area.symbol](#amb.area.symbol).
