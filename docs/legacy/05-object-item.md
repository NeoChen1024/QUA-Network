# Objects and items

| | |
|---|---|
| Status | Draft. Not frozen. Catalogue rows that the general rules do not settle are marked **[open]**. |
| Reference | `APRS12c.pdf` chapter 11, p. 75/57 to p. 80/62, with p. 49/31 and the appendices, in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, reading rules and tokenizer model: [README](README.md). |

## 1. Scope

APRS12c chapter 11: object and item reports, area objects with their
descriptor and corridor, signposts, and the obsolete object without an
identifier. Timestamps, positions, symbols, data extensions and the
comment follow [02-fields.md](02-fields.md); weather and storm data on
objects follow [06-weather.md](06-weather.md); frequencies in names and
comments follow [09-other.md](09-other.md#7-frequency-specification).

Offsets count from the first byte of the information field, which holds
the data type identifier at offset 0.

## 2. Object report

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.dti"></a>`obj.dti` | Data type identifier | `';'` ([err.dti.star](01-frame.md#err.dti.star)). | Required | 1 byte | p. 31/17, p. 76/58 |
| <a id="obj.name"></a>`obj.name` | Object name | Offsets 1 to 9, each byte 0x20–0x7E; trailing SP are padding, not part of the name. A byte outside the set, or a field cut short, gives `syntax`. | Required | 9 bytes | p. 76/58 |
| <a id="obj.state"></a>`obj.state` | Live or killed | `'*'` live, `'_'` killed; any other byte gives `syntax`, and reading goes on at offset 11. | Required | 1 byte | p. 76/58 |
| <a id="obj.time"></a>`obj.time` | Timestamp | [`time.dhm`](02-fields.md#time.dhm) or [`time.hms`](02-fields.md#time.hms) at offsets 11 to 17 ([amb.obj.time](#amb.obj.time)). | See amb.obj.time | 7 bytes | p. 75/57, p. 76/58 |
| <a id="obj.pos"></a>`obj.pos` | Position | A digit starts an uncompressed position ([`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code)); a byte of [`cmp.table`](02-fields.md#cmp.table) a compressed block [`cmp.block`](02-fields.md#cmp.block), which gives `discouraged` here. Any other byte gives `syntax`, and the rest is a residue naming `obj.pos`. | Required | 19 or 13 bytes | p. 55/37, p. 76/58 |
| <a id="obj.ext"></a>`obj.ext` | Data extension | After an uncompressed position: [`ext.csespd`](02-fields.md#ext.csespd), [`ext.phg`](02-fields.md#ext.phg) or [`ext.phgr`](02-fields.md#ext.phgr), [`ext.rng`](02-fields.md#ext.rng), [`ext.dfs`](02-fields.md#ext.dfs), or the area descriptor (section 4). The diagram lists no bearing, but p. 45/27 lets bearing and NRQ follow any course and speed: after an `ext.csespd`, storm data (section 7), else [`ext.brgnrq`](02-fields.md#ext.brgnrq) as [02 section 7.4](02-fields.md#74-bearing-and-nrq) reads it, with `ambiguous`. | Optional | 7 bytes; 9 for `ext.phgr`; 8 more for `ext.brgnrq` | p. 33/19, p. 45/27, p. 76/58 |
| <a id="obj.cmt"></a>`obj.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text) with the altitude, DAO and `'!x!'` items of 02-fields, the braces of sections 4 and 5, and a frequency at its start; no base-91 telemetry (p. 88/68). At most 36 characters after an extension, 28 after bearing and NRQ, 43 without, and 43 after a compressed position (36 after an extension there); more gives `value` ([amb.obj.cmtlen](#amb.obj.cmtlen)). | Optional | End of field | p. 34/20, p. 76/58, p. 88/68 |

The compressed diagram has no extension, while p. 45/27 lets one follow
any position: after a compressed position the start of the comment is
read as [02 section 6.5](02-fields.md#65-what-follows-the-block) says
([amb.ext.compressed](02-fields.md#amb.ext.compressed)), with an
`ambiguous` finding on a form that fits; under the area symbol only the
descriptor is tried (section 4).

## 3. Item report

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="item.dti"></a>`item.dti` | Data type identifier | `')'`. The item format is not recommended: `discouraged`. | Required | 1 byte | p. 31/17, p. 77/59 |
| <a id="item.name"></a>`item.name` | Item name | From offset 1, 3 to 9 bytes 0x20–0x7E other than `'!'` and `'_'`, ended by the first of these. A name of 1 or 2 bytes gives `value` at its end, one of more than 9 `value` at its tenth byte, an empty name `syntax`; with no `'!'` or `'_'` at all, `syntax` at the end of the field and the rest is a residue naming `item.name`. | Required | The first `'!'` or `'_'` | p. 77/59 |
| <a id="item.state"></a>`item.state` | Live or killed | `'!'` live, `'_'` killed. | Required | 1 byte | p. 77/59 |
| <a id="item.pos"></a>`item.pos` | Position | As `obj.pos`, directly after `item.state`; a compressed block gives no `discouraged` of its own. | Required | 19 or 13 bytes | p. 77/59 |
| <a id="item.ext"></a>`item.ext` | Data extension | As `obj.ext`. | Optional | 7 or 9 bytes | p. 77/59 |
| <a id="item.cmt"></a>`item.cmt` | Comment | As `obj.cmt`. | Optional | End of field | p. 77/59 |

## 4. Area objects

An object or item whose symbol is `'\'` `'l'` is an area object, and the
seven bytes after the symbol code of an uncompressed position are the
descriptor [`ext.area`](02-fields.md#ext.area), with no other extension
tried ([amb.area.symbol](#amb.area.symbol)). After a compressed position
seven bytes that fit the descriptor are `ext.area` with `ambiguous` at
their first byte, and other bytes are comment text with no finding
([amb.ext.compressed](02-fields.md#amb.ext.compressed)). Its parts are
tokens one level below it.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="area.type"></a>`area.type` | Shape | `'0'`–`'9'` | Required | 1 byte | p. 78/60 |
| <a id="area.lat"></a>`area.lat` | Latitude offset | Two digits | Required | 2 bytes | p. 78/60 |
| <a id="area.color"></a>`area.color` | Colour | `'/'` and a digit, or `'1'` and `'0'`–`'5'` ([err.area.slash](#err.area.slash)) | Required | 2 bytes | p. 49/31, p. 78/60 |
| <a id="area.lon"></a>`area.lon` | Longitude offset | Two digits | Required | 2 bytes | p. 78/60 |
| <a id="area.corridor"></a>`area.corridor` | Corridor width | In the comment of an area whose type byte is `'1'` or `'6'`: `'{'`, one or more digits, `'}'`; the first such braces anywhere in the comment ([amb.area.braces](#amb.area.braces)). | Optional | The `'}'` | p. 80/62 |

A descriptor that does not fit gives one `syntax` finding on `ext.area`,
at its first failing byte, or at the end of the field when it is cut
short; its parts are tokens as far as they are present, and the comment
has the limit after an extension.

## 5. Signposts

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.signpost"></a>`obj.signpost` | Signpost text | In the comment of an object or item with symbol `'\'` `'m'`: `'{'`, 1 to 3 bytes 0x20–0x7E other than `'{'` and `'}'`, `'}'`; the first such braces anywhere in the comment ([amb.area.braces](#amb.area.braces)). | Optional | The `'}'` | p. 80/62 |

## 6. Obsolete object format

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.obsolete"></a>`obj.obsolete` | Object without identifier | The object layout of section 2 from offset 0, with no identifier byte: `obj.name` at offsets 0 to 8, `obj.state` at 9, then the timestamp, position, extension and comment. `obsolete` at offset 0. One token over the field, the object tokens one level deeper ([amb.obj.obsolete](#amb.obj.obsolete)). | Optional | End of field | p. 80/62 |

The form matches when the fields from the name to the position are
complete and give no `syntax` finding. It is taken when byte 0 selects
no format ([01 section 7](01-frame.md#7-data-type-identifier)), and when
byte 0 selects a format other than the item and the object that also
reads the field with no `syntax` or `value` finding, then with
`ambiguous` on `obj.obsolete` at offset 0. Where byte 0 is `)` or `;`,
the item or object format decides.

## 7. Weather and storm data on objects

An object whose symbol code is `'_'` and which has at least one byte
after its position is a weather report read by
[06-weather.md](06-weather.md#wx.obj): the identifier token carries
`wx.obj`, and `obj.ext` and `obj.cmt` do not apply. An item whose symbol
code is `'_'` and which has at least one byte after its position is read
the same way, and its identifier token keeps `item.dti`
([amb.wx.carriers](06-weather.md#amb.wx.carriers)). An object or
item with symbol code `'@'`, under any table byte, overlays included,
and a course and speed may carry storm data before its comment, as
[06 section 8](06-weather.md#8-storm-data) reads it.

## 8. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.obj.time"></a>`amb.obj.time` | p. 75/57, p. 76/58, p. 78/60, p. 80/62, p. 153/129 | The timestamp is optional on one page and always present on the next; the area template and the FLIGHTPTH example have none ([err.obj.time](#err.obj.time)). | conflict | 3, 4 | Six digits and `'z'`, `'h'` or `'/'` at offset 11 are `obj.time`. Otherwise, where a position read from offset 11 reaches its symbol code with no `syntax` finding, it is the position, with no finding. Otherwise the 7 bytes are a malformed `obj.time` with `syntax`, and the position is read from offset 18. |
| <a id="amb.obj.name"></a>`amb.obj.name` | p. 76/58 | A name of nine SP leaves no name once the padding is removed. | unstated | 2 | `unstated` on `obj.name` at offset 1. |
| <a id="amb.obj.cmtlen"></a>`amb.obj.cmtlen` | p. 34/20, p. 76/58, p. 77/59 | The limits are in "chars", and the comment may hold UTF-8 characters of several bytes. | ambiguous | 1 | Counted in characters, the reading that accepts more bytes: `value` only where the characters exceed the limit. The limit is applied by the comment reader of 02-fields. |
| <a id="amb.area.symbol"></a>`amb.area.symbol` | p. 76/58, p. 78/60 | The descriptor follows the `\l` symbol code at once, while the object diagram makes the extension optional and lists course and speed and others at the same slot. | ambiguous | 1 | The `\l` symbol announces the descriptor: the seven bytes are `ext.area`, judged as it, and bytes that do not fit give `syntax`; no other extension is tried, and reading the bytes as comment does not make them conform. A report that ends at the symbol code has no descriptor and no finding. Under another symbol no descriptor is looked for. |
| <a id="amb.area.overlay"></a>`amb.area.overlay` | p. 78/60, p. 80/62, p. 126/102, p. 141/117 | The area and signpost symbols are named `\l` and `\m`; only marked symbols take an overlay (p. 126/102), yet every alternate symbol may (p. 141/117). | ambiguous | 1 | **[open]** Default: the symbols are matched on their bytes; an overlay character with `'l'` or `'m'` is another symbol, with no descriptor, corridor or signpost and no finding. |
| <a id="amb.area.braces"></a>`amb.area.braces` | p. 80/62 | Corridor and signpost braces are "in the comment", with no spot; the corridor's digit count is not given. | ambiguous | 2 | The whole comment is the place: the first braces of the item's shape are the item, with no finding; later braces are text. Braces in other reports, or in an area of another type, are text. |
| <a id="amb.obj.obsolete"></a>`amb.obj.obsolete` | p. 80/62 | Objects without `';'` are obsolete and "should now be interpreted" as status reports; no layout is given. | ambiguous | 1, 4 | The object layout from offset 0, with `obsolete`; every instance carries the status-report reading, so no `ambiguous`. Where byte 0 is `)` or `;`, the item or object format decides, its layout constraining at least as many bytes. Where byte 0 is another assigned identifier whose format also accepts the field, `ambiguous` on `obj.obsolete` at offset 0 and the object layout, the more specific, is taken; where that format does not accept it, the identifier decides. |
| <a id="err.obj.time"></a>`err.obj.time` | p. 75/57, p. 76/58, p. 78/60, p. 80/62, p. 153/129 | Optional timestamp against "always has a timestamp"; the template and FLIGHTPTH example omit it. | conflict | 3 | Both accepted ([amb.obj.time](#amb.obj.time)). |
| <a id="err.area.slash"></a>`err.area.slash` | p. 49/31, p. 78/60, p. 80/62 | The template `Tyy/Cxx` shows a fixed `'/'`; the colour table and the example `8101310` put `'1'` there for colours 10 to 15. | conflict | 3 | Both accepted (`area.color`). |
| <a id="err.area.size"></a>`err.area.size` | p. 78/60 | Areas range from 60 feet to 100 miles, which the two-digit offsets do not match. | conflict | 3 | Any two digits; the size is not checked. |
| <a id="err.area.sender"></a>`err.area.sender` | p. 78/60, p. 80/62 | The sender and receiver formulas for the offsets are not inverses. | conflict | 3 | No offset is computed: no effect. |
| <a id="err.area.gap"></a>`err.area.gap` | p. 78/60, p. 80/62 | The template and the FLIGHTPTH example print spaces around the symbol, while the text puts the descriptor directly after it. | conflict | 3 | A slip of the typesetting: it allows nothing, and no byte stands between the symbol code and the descriptor. |

## 9. Reviewed exceptions

None.

## 10. Open items

- [amb.area.overlay](#amb.area.overlay): whether an overlaid `'l'` or
  `'m'` is the area or signpost symbol.
