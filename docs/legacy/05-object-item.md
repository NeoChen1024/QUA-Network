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
a frequency, by its shape alone and on the name without its padding,
and reads the frequency items in the comment
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
| <a id="obj.time"></a>`obj.time` | Timestamp | Offsets 11 to 17: [`time.dhm`](02-fields.md#time.dhm) or [`time.hms`](02-fields.md#time.hms). Required ([amb.obj.time](#amb.obj.time); README section 3, Pages that disagree). A missing or malformed timestamp is still these 7 bytes, as for [`pos.time`](03-position.md#pos.time): the entry names no presence test, so the field is always present (README section 3, When a fixed field is present). | Required | 7 bytes | p. 76/58, p. 153/129 |
| <a id="obj.pos"></a>`obj.pos` | Position | From offset 18 ([amb.obj.time](#amb.obj.time)). A digit there starts an uncompressed position: [`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code), 19 bytes. A byte in the set of [`cmp.table`](02-fields.md#cmp.table) starts a compressed block, [`cmp.block`](02-fields.md#cmp.block), 13 bytes. `obj.pos` is the selector rule of [02-fields section 6.1](02-fields.md#61-telling-the-two-position-forms-apart): any other byte there is a `syntax` finding on `obj.pos` at that byte, and the bytes from it to the end of the field, whose extent cannot be told, are a `residue` that names `obj.pos` ([README section 3](README.md#3-tokenizer-model), Output and Placing a finding). | Required | 19 or 13 bytes | p. 55/37, p. 76/58 |
| <a id="obj.ext"></a>`obj.ext` | Data extension | After an uncompressed position only: [`ext.csespd`](02-fields.md#ext.csespd), [`ext.phg`](02-fields.md#ext.phg) or [`ext.phgr`](02-fields.md#ext.phgr), [`ext.rng`](02-fields.md#ext.rng), [`ext.dfs`](02-fields.md#ext.dfs) or the area descriptor [`ext.area`](02-fields.md#ext.area) (section 4). | Optional | 7 bytes; 9 for `ext.phgr` | p. 76/58, p. 33/19 |
| <a id="obj.cmt"></a>`obj.cmt` | Comment | The rest, read as [`cmt.text`](02-fields.md#cmt.text) with the comment items of [02-fields.md](02-fields.md#82-items-found-inside-a-comment) section 8, the braces of sections 4 and 5 below, and a frequency at its start ([09-other.md](09-other.md#7-frequency-specification)). **[agreed]** The comment counts as a position comment (p. 76/58, p. 80/62), so the altitude and the DAO are read in it; base-91 telemetry is not, and a run of its shape is text, with no finding ([amb.tlm.b91.where](07-telemetry.md#amb.tlm.b91.where); an earlier draft recorded it with an `unstated` finding). At most 36 bytes after an extension, the 9-byte [`ext.phgr`](02-fields.md#ext.phgr) included, as in [amb.pos.cmtlen](03-position.md#amb.pos.cmtlen), and 43 without; 43 after a compressed position, from the object diagram ([err.obj.cmplen](#err.obj.cmplen); README section 3, Pages that disagree). A longer comment gives a `value` finding. | Optional | End of information field | p. 76/58, p. 132/108 |

The token of byte 0 carries `obj.dti`, so that the tokens show the
packet as an object report
([README section 3](README.md#3-tokenizer-model)). An object that is
classified as a weather report carries [`wx.obj`](06-weather.md#wx.obj)
there instead (section 7; README section 3, Output).

After a compressed position no data extension follows; the block's own
`cs` bytes, [`cmp.cs`](02-fields.md#cmp.cs), carry course and speed or
range (p. 76/58). Seven bytes there that look like an extension are
comment text.

**[proposed]** Bearing and NRQ,
[`ext.brgnrq`](02-fields.md#ext.brgnrq), are not read in object or item
reports: `obj.ext` does not list them,
[02-fields section 7.2](02-fields.md#72-fields) gives the field to DF
reports, and [03-position section 3](03-position.md#3-df-reports)
defines a DF report as a position report. Eight bytes of their shape
directly after the extension are comment text. The document does not
say this outright: 02 section 7.4 speaks of "a report" with the DF
symbol, without naming a format. A reading that follows those words
lets an object or item carry bearing and NRQ wherever one of the
readings of [amb.ext.brgnrq](02-fields.md#amb.ext.brgnrq) would put
them: with the DF symbol `/\` after an `ext.csespd` (all three of its
readings) or after another extension (its reading (a)), and under
another symbol after an `ext.csespd` (its reading (c)). In those cases,
when the bearing is at most 360, the 8 bytes get an `ambiguous` finding
at their first byte, on [`cmt.text`](02-fields.md#cmt.text), the rule
this reading gives them
([README section 3](README.md#3-tokenizer-model), Placing a finding; an
earlier draft put it on `ext.brgnrq`); with a larger bearing that
reading gives `value` and does not count. No comment limit is stated
for an object or item that carries bearing and NRQ, so no length
finding counts against that reading. Whether objects and items carry the field
is listed in section 10.

APRS 1.1 calls compressed objects not recommended for use on RF, and
the item format not recommended on RF (p. 76/58, p. 77/59). The
headings and diagram titles of the same pages call the compressed
object form and the item format "not recommended" without that limit
(p. 76/58, p. 77/59). **[agreed]** A compressed object gives a
`discouraged` finding at the first byte of `obj.pos`; every item report
gives one at `item.dti` (section 3). **[agreed]** These findings are
given whatever the q-construct in the path shows. A q-construct
records how an APRS-IS server saw the connection the packet came in
on, not the radio medium, and
[README section 3](README.md#3-tokenizer-model) does not check a rule
that depends on the connection. The same holds for the other
discouragements that APRS12c limits to RF or to the air: the
local-time timestamp, which p. 38/22 asks future implementations not to
transmit "on the air"
([02-fields section 2](02-fields.md#2-timestamps)), and raw weather,
which p. 82/62 and p. 85/65 ask senders to convert to the complete
format on RF ([06-weather section 2](06-weather.md#2-recognition)). An
earlier draft gave the findings everywhere as **[proposed]**, on the
ground that the TNC2 line does not show reliably whether the packet was
or will be sent on RF, and left open in section 10 whether a
q-construct should limit them to packets heard on RF.

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
| <a id="item.name"></a>`item.name` | Item name | From offset 1: bytes 0x20–0x7E other than `'!'` and `'_'`, 3 to 9 of them. A name of 1 or 2 bytes, or of more than 9, gives a `value` finding, and an empty name, a missing field, a `syntax` finding ([README section 3](README.md#3-tokenizer-model), Kinds by situation). No `'!'` or `'_'` at all gives a `syntax` finding ([amb.item.name](#amb.item.name); README section 3, Output). | Required | The first `'!'` or `'_'` | p. 77/59 |
| <a id="item.state"></a>`item.state` | Live or killed | `'!'` live, `'_'` killed. | Required | 1 byte | p. 77/59 |
| <a id="item.pos"></a>`item.pos` | Position | As `obj.pos`, directly after `item.state`. `item.pos` is the selector rule here and carries the `syntax` finding and the `residue`, as `obj.pos` does. | Required | 19 or 13 bytes | p. 77/59 |
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
| <a id="area.corridor"></a>`area.corridor` | Corridor width | In the comment of a type `'1'` or `'6'` area: `'{'`, one or more digits (miles either side of the line), `'}'`. **[agreed]** Only at the start of the comment, as for the signpost. When the comment does not start with one, the first braces of that shape later in the comment are comment text with an `ambiguous` finding on `cmt.text` at their `'{'` ([amb.area.braces](#amb.area.braces)). An earlier draft carried the place at the start of the comment as a proposal. | Optional | The `'}'` | p. 80/62 |

The tokenizer checks the digits and does not compute the offsets. The
scale is in [err.area.sender](#err.area.sender), and the stated size
range in [err.area.size](#err.area.size).

Details of the descriptor:

- The symbol is matched on its bytes: the table identifier
  ([`sym.table`](02-fields.md#sym.table) or
  [`cmp.table`](02-fields.md#cmp.table)) is the byte `'\'` itself and
  the code is `'l'`, since p. 78/60 names `\l`
  ([README section 3](README.md#3-tokenizer-model), Symbols that a
  format names). An overlay character in place of `'\'` makes a
  different symbol, and an overlaid `'l'` is read as any other symbol.
  The same holds for the signpost symbol `\m` (section 5). An earlier
  draft carried this as **[proposed]**, on the ground that nothing
  extends the area object to overlays as
  [06-weather section 2](06-weather.md#2-recognition) does for the
  weather symbol, and listed in section 10 whether an overlaid symbol
  should count.
- The wider reading of that rule, that a named `'\'` accepts any
  overlay, is visible in the bytes. In an object or item report with an
  uncompressed position whose table byte is an overlay character and
  whose code is `'l'`, seven bytes after the symbol code that fit
  [`ext.area`](02-fields.md#ext.area), with no `syntax` finding, get an
  `ambiguous` finding at their first byte, on the rule this reading
  gives them: the extension that
  [02-fields section 7.1](02-fields.md#71-the-extension-slot) reads
  there, or [`cmt.text`](02-fields.md#cmt.text)
  ([README section 3](README.md#3-tokenizer-model), Placing a finding).
  Where this reading gives those bytes a `syntax` or `value` finding,
  such as the course above 360 of a `710/310`
  [`ext.csespd`](02-fields.md#ext.csespd), that finding alone is given
  (Precedence). The two readings set the same comment limit over those
  bytes, 7 and 36 against 43. A report that ends at the symbol code has
  no descriptor under either reading, and after a compressed block both
  take the bytes as comment text, so neither gives a finding.
- **[proposed]** An object or item with the `\l` symbol that ends at
  the symbol code has no descriptor and no finding for one, as an
  object that ends at the `'_'` symbol is no weather report
  (section 7).
- Otherwise the `ext.area` token covers the seven bytes after the
  symbol code, or the bytes up to the end of the field when there are
  fewer, with one `syntax` finding on `ext.area` at the first byte that
  does not fit, at the end of the field when it is cut short. The
  parts are tokens as far as their bytes are present. The comment
  follows the seven bytes and has the limit after an extension
  ([README section 3](README.md#3-tokenizer-model), Output).
- **[proposed]** The corridor width is read when the first byte of the
  descriptor is `'1'` or `'6'`, whether or not a later part fits.
- After a compressed block there is no descriptor
  ([amb.ext.compressed](02-fields.md#amb.ext.compressed), reading (a);
  [02-fields section 7.1](02-fields.md#71-the-extension-slot)). Seven
  bytes directly after the block that fit `ext.area` get the
  `ambiguous` finding of
  [02-fields section 6.5](02-fields.md#65-what-follows-the-block) and
  of the In the bytes paragraph of amb.ext.compressed, since 7.1 would
  try that form at a slot of a `\l` report (step 1). A course and speed
  there gets no finding, since 7.1 would not try one.

## 5. Signposts

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.signpost"></a>`obj.signpost` | Signpost text | In the comment of an object or item with symbol `'\'` `'m'`: `'{'`, 1 to 3 bytes 0x20–0x7E other than `'{'` and `'}'`, `'}'`. **[agreed]** Only at the start of the comment. When the comment does not start with one, the first braces of that shape later in the comment are comment text with an `ambiguous` finding on `cmt.text` at their `'{'` ([amb.area.braces](#amb.area.braces)). An earlier draft took the first such braces anywhere in the comment, with an `ambiguous` finding on `obj.signpost` when they did not stand at its start. | Optional | The `'}'` | p. 80/62, p. 153/129 |

The signpost symbol is matched on its bytes, `\m` as p. 80/62 names
it, as section 4 states for `\l`
([README section 3](README.md#3-tokenizer-model), Symbols that a
format names). In an object or item report whose table byte is an
overlay character and whose code is `'m'`, a comment that starts with
braces of the signpost shape gets an `ambiguous` finding at their
`'{'`, on [`cmt.text`](02-fields.md#cmt.text), since the wider reading
of that rule would take them as `obj.signpost` (README section 3,
Placing a finding). Where this reading gives those bytes a `syntax` or
`value` finding, that finding alone is given (Precedence). Braces of
that shape later in the comment get no finding from this test: the
wider reading leaves them as text too (Fixed spots and repeats).

Corridor widths and signpost text are read in object and item reports
only, as chapter 11 describes them
([README section 3](README.md#3-tokenizer-model), Where comment items
are looked for); an earlier draft carried this as a proposal. The area
descriptor is limited in the same way by section 4.

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

**[proposed]** Match. A field matches `obj.obsolete` when the fields
from `obj.name` to the position are complete and give no `syntax`
finding; a `value` finding there, and any finding after the position,
do not prevent the match.

The `obsolete` finding is on `obj.obsolete` at offset 0, the first byte
of the form ([README section 3](README.md#3-tokenizer-model), Obsolete
and nested forms). An obsolete object with symbol code `'_'` is read as
in section 7, but there is no identifier byte to carry `wx.obj`
(README section 3, Output).

## 7. Weather and storm data on objects

An object whose symbol code is `'_'`, in either position form, carries a
weather report in place of the data extension and comment. When at least
one byte follows the position block, everything after it is read by
[06-weather.md](06-weather.md#53-object) as
[`wx.obj`](06-weather.md#wx.obj), and neither `obj.ext` nor `obj.cmt`
applies; an object that ends at the symbol code is an ordinary object.
An object read as weather is classified as a weather report: the token
of byte 0 carries `wx.obj` in place of `obj.dti`, as
[06-weather.md section 2](06-weather.md#2-recognition) and
[README section 3](README.md#3-tokenizer-model) (Output) state, and the
object header and position keep their own IDs. **[proposed]** Items
with symbol code `'_'` are not read as weather
([amb.wx.carriers](06-weather.md#amb.wx.carriers)). The Appendix 1
weather object diagram with `'*'` as identifier is an erratum
([err.wx.object-dti](06-weather.md#err.wx.object-dti)).

An object or item with the symbol `\@` or `/@` whose extension is
[`ext.csespd`](02-fields.md#ext.csespd) may carry storm data in place of
the comment; [06-weather.md](06-weather.md#8-storm-data) says when it is
read, and the bytes after the storm fields are `obj.cmt` or `item.cmt`.
The table byte is matched as p. 87/67 names it
([README section 3](README.md#3-tokenizer-model), Symbols that a
format names); an earlier draft named only the code `'@'`.

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
- **Reading taken.** (a), as the diagram has it
  ([README section 3](README.md#3-tokenizer-model), Pages that
  disagree); most decoders read agree. **[agreed]** The timestamp is
  the 7 bytes at offsets 11 to 17 that the layout fixes, whether they
  are malformed or the timestamp is missing, as for
  [`pos.time`](03-position.md#pos.time): a 7-byte token read by
  [`time.dhm`](02-fields.md#time.dhm) or
  [`time.hms`](02-fields.md#time.hms), chosen by offset 17 as
  [02 section 2](02-fields.md#2-timestamps) does, with one `syntax`
  finding at its first byte that fails, and the position is read from
  offset 18 ([README section 3](README.md#3-tokenizer-model), Output;
  Forms that can stand at one place). One cut short by the end of the
  field covers the bytes present, with the finding where its first
  missing byte was expected; a field that ends at offset 11 gives
  `syntax` on `obj.time` there. An earlier draft took the shape of the
  bytes as the test: six digits at offsets 11 to 16 were the
  timestamp, and any other bytes were a missing timestamp that used no
  byte, with the position read from offset 11. It was dropped because
  the format gives the timestamp no presence test: p. 76/58 draws the
  object with the 7 bytes always there and says that an object always
  has a timestamp, and nothing in those bytes marks them as present, as
  the `'/'` at offset 3 of the wind field of a complete weather report
  does ([06-weather section 5.1](06-weather.md#51-uncompressed-position)).
  Six digits are the timestamp's value, not a marker, so the test took
  a malformed timestamp for a missing one and lost the position after
  it, as after a corrupted `111111z`. The note first gave as the reason
  that the test contradicted the Output rule; it does not, since Output
  applies to a field once it is present and an entry may name the test
  that makes a fixed field present
  ([README section 3](README.md#3-tokenizer-model), When a fixed field
  is present). A draft before that stopped at a missing timestamp and
  made the bytes from offset 11 to the end of the field a `residue`
  that names `obj.time`, leaving the position to a deviation
  recogniser.
- **In the bytes.** Visible. Reading (b) would accept a report without
  a timestamp, but the `syntax` finding alone is given, with no
  `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence). Where
  offsets 11 to 17 hold a timestamp, reading (b) detects it too and the
  readings agree, since no position starts with six digits.
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
  with trailing spaces, and any printable byte may stand in it
  (p. 76/58). Not stated: an all-space name, and what to do when offset
  10 is not `'*'` or `'_'` because the sender did not pad the name.
- **Readings.** (a) Strict offsets; any 0x20–0x7E byte in the name. An
  earlier draft also listed (b): scan for the first `'*'` or `'_'` and
  take what precedes it as the name. That contradicts the fixed
  nine-byte name of p. 76/58, so by
  [README section 3](README.md#3-tokenizer-model) it is decoder
  behaviour (pdn-aprs, below), not a listed reading, and gives no
  finding.
- **Reading taken.** (a), the one listed reading
  ([README section 3](README.md#3-tokenizer-model)). Leading spaces and
  `'*'` or `'_'` inside the nine bytes are part of the name, with no
  finding. A byte other than `'*'` or `'_'` at offset 10 gives `syntax`
  on `obj.state`; recognising an unpadded name is left to a deviation
  recogniser. No other reading is listed, so the entry gives no
  `ambiguous` finding. An earlier draft gave one at a `'*'` or `'_'`
  inside the name where reading (b) would have parsed the rest of the
  report from there. A name of nine SP gives `syntax`,
  as no name is left once the padding is removed: it is an empty required field
  ([README section 3](README.md#3-tokenizer-model), Kinds by
  situation: an empty required field is a missing field). P. 76/58 and p. 77/59 state the
  byte set of object and item names as printable ASCII, where the
  comment, message and status text admit UTF-8 as well; the names are
  not a field where printable ASCII is only recommended, so the
  exemption of [README section 3](README.md#3-tokenizer-model) does not
  apply. A byte above 0x7E in a name gives `syntax` at that byte (README
  section 3, Kinds by situation: a byte outside the byte set that a
  rule states), and the nine-byte length counts bytes (README section 3,
  Length limits).
- **Placement.** The finding for nine SP is at offset 1, the first
  byte of the field at fault. After a `syntax` finding on `obj.state`
  the report is read on from offset 11, since the layout fixes where
  each field starts ([README section 3](README.md#3-tokenizer-model),
  Output and Placing a finding).
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

- **Open.** The name is 3 to 9 bytes ended by the first `'!'` or `'_'`,
  and neither byte may stand in it, since they end it (p. 77/59). Not
  stated: what to do with a shorter or longer name, or with no
  terminator.
- **Readings.** (a) The first `'!'` or `'_'` ends the name; a length
  outside 3 to 9 is an error. An earlier draft also listed (b), searching
  only the bytes where a 3 to 9 byte name can end, and (c), taking a
  `'!'` or `'_'` among the first three bytes as part of the name. Both
  keep a `'!'` or `'_'` inside the name, which p. 77/59 excludes, so by
  [README section 3](README.md#3-tokenizer-model) they are decoder
  behaviour (pdn-aprs and javAPRSlib, below), not listed readings, and
  give no finding.
- **Reading taken.** (a), with no terminator giving
  `syntax`. No other reading is listed, so there is no `ambiguous`
  finding. This applies agreed rules: a delimiter ends a field at its
  first occurrence when the field's content may not hold it
  ([README section 3](README.md#3-tokenizer-model), Forms that can
  stand at one place), and a field whose end is missing is placed as
  below (Output; Kinds by situation).
- **Placement.** Under (a), a name that is not empty and is outside 3
  to 9 bytes gives `value`, as a field outside its stated length, and
  an empty name is a missing field and gives `syntax`
  ([README section 3](README.md#3-tokenizer-model), Kinds by
  situation). A name of 1 or 2 bytes gives the `value` finding at
  its terminator, where the first missing byte was expected; a name of
  more than 9 bytes gives it at its tenth byte, the first past the
  limit; an empty name gives `syntax` at offset 1, where the terminator
  stands. With no terminator, where the name ends cannot be told: the
  bytes from offset 1 to the end of the field are a `residue` that
  names `item.name`, and the `syntax` finding is at the end of the
  field ([README section 3](README.md#3-tokenizer-model), Output and
  Placing a finding). An earlier draft put the finding for a name of 1
  or 2 bytes at its first byte, offset 1.
- **Decoders.** FAP: 3 to 9 bytes, then `'!'` or `'_'`
  (`_item_to_decimal`, `FAP.pm:1449`). Dire Wolf: the first `'!'` or
  `'_'` within nine bytes, no minimum (`aprs_item`,
  `decode_aprs.c:2273-2289`). aprslib: does not parse items
  (`__init__.py:53`). Xastir: the first `'!'` or `'_'` within nine bytes,
  then its object-name check of 1 to 9 printable bytes
  (`db.c:15575-15597`; `valid_object`, `objects.c:74-93`). aprsc: 3 to 9
  printable bytes (`parse_aprs_item`, `parse_aprs.c:958-985`). pdn-aprs:
  looks for the terminator from offset 4 on, so a `'!'` or `'_'` among
  the first three bytes stays in the name (`item`, `object.rs:74-89`).
  javAPRSlib: the first `'!'` if that gives 1 to 9 bytes, else the first
  `'_'`, in which case the name it takes is one byte too long and ends
  with the `'_'` (`ItemField.java:50-64`).
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
- **In the bytes.** One case remains visible under the test of README
  section 3. In an object or item report with another symbol, not read
  as weather (section 7), seven bytes after the symbol code of an
  uncompressed position may fit [`ext.area`](02-fields.md#ext.area)
  with a colour of `'1'` and `'0'`–`'5'`, and so fit no course and
  speed or other extension. This reading leaves them as comment text,
  and reading (b) would take them as a descriptor. They give an
  `ambiguous` finding at their first byte, on
  [`cmt.text`](02-fields.md#cmt.text), the rule this reading gives them
  ([README section 3](README.md#3-tokenizer-model), Placing a finding;
  an earlier draft put it on `ext.area`).
  Reading (b) reads every other byte of the report as this reading
  does, and the limits of `obj.cmt` allow the same total either way, 7
  and 36 bytes against 43, so a `syntax` or `value` finding elsewhere in
  the report is given by both and does not suppress the `ambiguous`
  finding. An earlier draft withheld it wherever the report had such a
  finding. [02-fields.md section 7.1](02-fields.md#71-the-extension-slot)
  gives the slot the same exception.
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
- **Reading taken.** **[agreed]** (c): corridor and signpost braces are
  read only within the scope of their symbols, and readings (a) and (b)
  differ only in where the braces stand within that scope. Braces in
  other reports are comment text with no finding.

  The scope is a line area, type `'1'` or `'6'`, for the corridor, and
  the `'\'` `'m'` symbol for the signpost, in object and item reports
  (section 5); braces in an area of another type are comment text as
  well (p. 80/62; reading (c)).

  **[proposed]** The corridor holds one or more digits.
  **[agreed]** Corridor and signpost: (a). The text says only "in the
  comment", and the examples of p. 80/62 put the braces at its start,
  which fixes the spot
  ([README section 3](README.md#3-tokenizer-model), Fixed spots and
  repeats, and Pages that disagree). An earlier draft took (a) for the
  corridor as a proposal, on the ground that only a line area carries
  one and its comment follows the descriptor, and took (b) for the
  signpost, the first well-formed braces anywhere, since the text says
  only "in the comment".
- **In the bytes.** Visible, under the test of
  [README section 3](README.md#3-tokenizer-model), in the same case for
  the corridor and the signpost (Fixed spots and repeats): when the
  comment does not start with braces of the item's shape, the first
  such braces later in it, which reading (b) would take as the item,
  are comment text with an `ambiguous` finding at their `'{'`, on
  `cmt.text`, the rule this reading gives them (README section 3,
  Placing a finding; an earlier draft put the corridor's on
  `area.corridor`). When the comment starts with such braces, (a) and
  (b) both take those, and later braces are text under both, with no
  finding; braces after the first later ones are text under both as
  well. The other reading reads every other byte as this reading does,
  so a `syntax` or `value` finding elsewhere in the report is given by
  both and does not suppress the `ambiguous` finding. An earlier draft
  gave `ambiguous` for every later corridor-shaped braces and for every
  second signpost candidate, neither of which meets the test, and a
  later one withheld the finding wherever the comment had a `syntax` or
  `value` finding. Under reading (b) for the signpost, a later draft
  gave the braces taken an `ambiguous` finding on `obj.signpost` when
  they did not stand at the start of the comment, from reading (a).
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
  q-construct in the path should limit them to packets heard on RF was
  listed here as open. Settled in section 2, which gives them whatever
  the q-construct shows. The item is kept here as a record.
- Whether object and item reports carry bearing and NRQ
  ([`ext.brgnrq`](02-fields.md#ext.brgnrq)), and with which rule ID and
  comment limit; the reading taken and its `ambiguous` finding are in
  section 2.
- Whether an overlay character on the alternate table, with code `'l'`
  or `'m'`, makes an area object or a signpost (section 4). If the
  author takes that as a listed reading, such reports become visible
  cases of it. Settled by the rule on symbols that a format names
  ([README section 3](README.md#3-tokenizer-model)): an overlay makes a
  different symbol, and the wider reading is listed, with the
  `ambiguous` finding of sections 4 and 5. The item is kept here as a
  record.
- ebarkie/aprs has no object or item decoder in the files read. The
  object and item handling of aprs-parser-rs was not read, apart from
  the area descriptor test cited in
  [amb.area.symbol](#amb.area.symbol).
