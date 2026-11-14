# Objects and Items

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. |
| Reference | `APRS12c.pdf` chapter 11, p. 75/57 to p. 80/62, with p. 49/31 and the appendices, in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers APRS12c chapter 11: Object and Item reports, area
objects with their descriptor and corridor, signposts, and the obsolete
Object without an identifier. The tokenizer reads the shared fields as
other files say:

- timestamps, positions, symbols, data extensions and the comment, as
  [02-fields.md](02-fields.md) says;
- weather and storm data on Objects, as [06-weather.md](06-weather.md)
  says;
- frequencies in names and comments, as
  [09-other.md](09-other.md#7-frequency-specification) says.

Offsets count from the first byte of the information field. That byte is
the data type identifier, at offset 0.

## 2. Object report

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.dti"></a>`obj.dti` | Data type identifier | `';'` ([err.dti.star](01-frame.md#err.dti.star)). | Required | 1 byte | p. 31/17, p. 76/58 |
| <a id="obj.name"></a>`obj.name` | Object name | Offsets 1 to 9. Each byte is 0x20–0x7E. Trailing SP bytes are padding and are not part of the name. A byte outside this set gives `syntax`. A field that is cut short also gives `syntax`. | Required | 9 bytes | p. 76/58 |
| <a id="obj.state"></a>`obj.state` | Live or killed | `'*'` is live. `'_'` is killed. Any other byte gives `syntax`. The tokenizer then continues at offset 11. | Required | 1 byte | p. 76/58 |
| <a id="obj.time"></a>`obj.time` | Timestamp | [`time.dhm`](02-fields.md#time.dhm) or [`time.hms`](02-fields.md#time.hms) at offsets 11 to 17 ([amb.obj.time](#amb.obj.time)). | See amb.obj.time | 7 bytes | p. 75/57, p. 76/58 |
| <a id="obj.pos"></a>`obj.pos` | Position | A digit starts an uncompressed position ([`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code)). A byte of [`cmp.table`](02-fields.md#cmp.table) starts a compressed block [`cmp.block`](02-fields.md#cmp.block). Here, a compressed block gives `discouraged`. Any other byte gives `syntax`. The rest of the bytes are then residue, and the `residue` token names `obj.pos`. | Required | 19 or 13 bytes | p. 55/37, p. 76/58 |
| <a id="obj.ext"></a>`obj.ext` | Data extension | After an uncompressed position: [`ext.csespd`](02-fields.md#ext.csespd), [`ext.phg`](02-fields.md#ext.phg) or [`ext.phgr`](02-fields.md#ext.phgr), [`ext.rng`](02-fields.md#ext.rng), [`ext.dfs`](02-fields.md#ext.dfs), or the area descriptor (section 4). The diagram contains no bearing. But APRS12c permits bearing and NRQ after any course and speed (p. 45/27). After an `ext.csespd`, the tokenizer reads storm data (section 7). If there is no storm data, it reads [`ext.brgnrq`](02-fields.md#ext.brgnrq) as [02 section 7.4](02-fields.md#74-bearing-and-nrq) says, with `ambiguous`. | Optional | 7 bytes; 9 for `ext.phgr`; 8 more for `ext.brgnrq` | p. 33/19, p. 45/27, p. 76/58 |
| <a id="obj.cmt"></a>`obj.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text). It can contain the altitude, DAO and `'!x!'` fields of 02-fields, the braces of sections 4 and 5, and a frequency at its start. It contains no base-91 telemetry (p. 88/68). The limit is 36 characters after an extension, 28 after bearing and NRQ, and 43 with no extension. After a compressed position, the limit is 43, or 36 after an extension. A longer comment gives `value` ([amb.obj.cmtlen](#amb.obj.cmtlen)). | Optional | End of field | p. 34/20, p. 76/58, p. 88/68 |

The diagram of the compressed format contains no extension. But
APRS12c permits an extension after any position (p. 45/27). After a
compressed position, the tokenizer reads the start of the comment as
[02 section 6.5](02-fields.md#65-what-follows-the-block) says
([amb.ext.compressed](02-fields.md#amb.ext.compressed)). If the bytes
there match a format of step 3 of 02 section 7.1 with no `syntax` or
`value` finding, the tokenizer gives `ambiguous`. Under the area symbol,
the tokenizer tries only the descriptor (section 4).

## 3. Item report

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="item.dti"></a>`item.dti` | Data type identifier | `')'`. APRS12c does not recommend the Item format, so this byte gives `discouraged`. | Required | 1 byte | p. 31/17, p. 77/59 |
| <a id="item.name"></a>`item.name` | Item name | From offset 1: 3 to 9 bytes 0x20–0x7E other than `'!'` and `'_'`. The first `'!'` or `'_'` ends the name. A name of 1 or 2 bytes gives `value` at its end. A name of more than 9 bytes gives `value` at its tenth byte. An empty name gives `syntax`. If the field contains no `'!'` or `'_'`, the tokenizer gives `syntax` at the end of the field. The rest of the bytes are then residue, and the `residue` token names `item.name`. | Required | The first `'!'` or `'_'` | p. 77/59 |
| <a id="item.state"></a>`item.state` | Live or killed | `'!'` is live. `'_'` is killed. | Required | 1 byte | p. 77/59 |
| <a id="item.pos"></a>`item.pos` | Position | As `obj.pos`, directly after `item.state`. Here, a compressed block gives no `discouraged` finding of its own. | Required | 19 or 13 bytes | p. 77/59 |
| <a id="item.ext"></a>`item.ext` | Data extension | As `obj.ext`. | Optional | 7 or 9 bytes | p. 77/59 |
| <a id="item.cmt"></a>`item.cmt` | Comment | As `obj.cmt`. | Optional | End of field | p. 77/59 |

## 4. Area objects

An Object or Item with the symbol `'\'` `'l'` is an area object. After
the symbol code of an uncompressed position, the seven bytes are the
descriptor [`ext.area`](02-fields.md#ext.area). The tokenizer tries no
other extension there ([amb.area.symbol](#amb.area.symbol)). After a
compressed position, the tokenizer reads the bytes as follows
([amb.ext.compressed](02-fields.md#amb.ext.compressed)):

- If seven bytes match the descriptor, they are `ext.area`, with
  `ambiguous` at their first byte.
- If not, the bytes are comment text, with no finding.

The fields of the descriptor are tokens one level below the `ext.area`
token.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="area.type"></a>`area.type` | Shape | `'0'`–`'9'` | Required | 1 byte | p. 78/60 |
| <a id="area.lat"></a>`area.lat` | Latitude offset | Two digits | Required | 2 bytes | p. 78/60 |
| <a id="area.color"></a>`area.color` | Colour | `'/'` and a digit, or `'1'` and `'0'`–`'5'` ([err.area.slash](#err.area.slash)) | Required | 2 bytes | p. 49/31, p. 78/60 |
| <a id="area.lon"></a>`area.lon` | Longitude offset | Two digits | Required | 2 bytes | p. 78/60 |
| <a id="area.corridor"></a>`area.corridor` | Corridor width | In the comment of an area object whose type byte is `'1'` or `'6'`: `'{'`, one or more digits, `'}'`. The tokenizer uses the first such braces at any place in the comment ([amb.area.braces](#amb.area.braces)). | Optional | The `'}'` | p. 80/62 |

If a descriptor does not match its format, the tokenizer gives one
`syntax` finding on `ext.area`. The finding is at the first byte that
fails. If the descriptor is cut short, the finding is at the end of the
field. The fields of the descriptor are tokens as far as they are
present. The comment then has the limit that applies after an extension.

## 5. Signposts

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.signpost"></a>`obj.signpost` | Signpost text | In the comment of an Object or Item with the symbol `'\'` `'m'`: `'{'`, 1 to 3 bytes 0x20–0x7E other than `'{'` and `'}'`, `'}'`. The tokenizer uses the first such braces at any place in the comment ([amb.area.braces](#amb.area.braces)). | Optional | The `'}'` | p. 80/62 |

## 6. Obsolete Object format

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="obj.obsolete"></a>`obj.obsolete` | Object without identifier | The Object format of section 2 from offset 0, with no identifier byte. `obj.name` is at offsets 0 to 8, and `obj.state` is at offset 9. The timestamp, position, extension and comment follow. The tokenizer gives `obsolete` at offset 0. One token covers the field. The Object tokens are one level below ([amb.obj.obsolete](#amb.obj.obsolete)). | Optional | End of field | p. 80/62 |

The obsolete format matches if the fields from the name to the position
are complete and give no `syntax` finding. The tokenizer uses the
obsolete format in these cases:

- Byte 0 selects no format ([01 section 7](01-frame.md#7-data-type-identifier)).
- Byte 0 selects a format other than the Item and Object formats, and
  that format also reads the field with no `syntax` or `value`. The
  tokenizer then gives `ambiguous` on `obj.obsolete` at offset 0.

If byte 0 is `)` or `;`, the Item or Object format decides.

## 7. Weather and storm data on Objects

If an Object has the symbol code `'_'` and at least one byte after its
position, it is a weather report. The tokenizer reads it as
[06-weather.md](06-weather.md#wx.obj) says:

- The token of byte 0 has the rule ID `wx.obj`.
- `obj.ext` and `obj.cmt` do not apply.
- The tokenizer reads a comment after the weather data as
  [06 section 7](06-weather.md#7-software-and-unit-codes) says.

If an Item has the symbol code `'_'` and at least one byte after its
position, the tokenizer reads it in the same way. The token of byte 0
keeps the rule ID `item.dti`
([amb.wx.carriers](06-weather.md#amb.wx.carriers)).

An Object or Item can contain storm data before its comment, as
[06 section 8](06-weather.md#8-storm-data) says. This applies if the
Object or Item has both of these:

- the symbol code `'@'` under any table byte, overlays included;
- a course and speed.

## 8. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.obj.time"></a>`amb.obj.time` | p. 75/57, p. 76/58, p. 78/60, p. 80/62, p. 153/129 | One page makes the timestamp optional. The next page says that it is always present. The area template and the FLIGHTPTH example contain no timestamp ([err.obj.time](#err.obj.time)). | conflict | 3, 4 | If six digits and `'z'`, `'h'` or `'/'` are at offset 11, they are `obj.time`. If not, the tokenizer reads a position from offset 11. If this position reaches its symbol code with no `syntax` finding, it is the position, with no finding. Otherwise, the 7 bytes are a malformed `obj.time` with `syntax`. The tokenizer then reads the position from offset 18. |
| <a id="amb.obj.name"></a>`amb.obj.name` | p. 76/58 | A name of nine SP bytes is empty when the padding is removed. | unstated | 2 | `unstated` on `obj.name` at offset 1. |
| <a id="amb.obj.cmtlen"></a>`amb.obj.cmtlen` | p. 34/20, p. 76/58, p. 77/59 | APRS12c specifies the limits in "chars". The comment can contain UTF-8 characters of several bytes. | ambiguous | 1 | The tokenizer counts characters, because this interpretation accepts more bytes. It gives `value` only if the characters are more than the limit. The comment reader of 02-fields applies the limit. |
| <a id="amb.area.symbol"></a>`amb.area.symbol` | p. 76/58, p. 78/60 | The descriptor follows the `\l` symbol code directly. But the Object diagram makes the extension optional and lists course and speed and other extensions at the same place. | ambiguous | 1 | The `\l` symbol is a marker that starts the descriptor. The tokenizer reads the seven bytes as `ext.area`. Bytes that do not match give `syntax`. The tokenizer tries no other extension. An interpretation of the bytes as a comment does not prevent the finding. A report that ends at the symbol code has no descriptor and no finding. Under another symbol, the tokenizer does not look for a descriptor. |
| <a id="amb.area.overlay"></a>`amb.area.overlay` | p. 78/60, p. 80/62, p. 126/102, p. 141/117 | APRS12c names the area and signpost symbols `\l` and `\m`. On p. 126/102, only marked symbols permit an overlay. On p. 141/117, every alternate symbol permits one. | ambiguous | none | Working choice: the tokenizer matches the symbols on their bytes. An overlay character with `'l'` or `'m'` is a different symbol. It has no descriptor, corridor or signpost, and it gives no finding. |
| <a id="amb.area.braces"></a>`amb.area.braces` | p. 80/62 | APRS12c puts corridor and signpost braces "in the comment", with no place in it. APRS12c does not specify the number of digits of the corridor. | ambiguous | 2 | The whole comment is the place. The first braces that match the format of the field are that field, with no finding. Later braces are text. Braces in other reports, or in an area object of another type, are text. |
| <a id="amb.obj.obsolete"></a>`amb.obj.obsolete` | p. 80/62 | Objects without `';'` are obsolete and "should now be interpreted" as status reports. APRS12c specifies no format for them. | ambiguous | 1, 4 | The tokenizer uses the Object format from offset 0, with `obsolete`. Every such field also has the status-report interpretation. Every packet of this format has the same ambiguity, so the tokenizer gives no `ambiguous` for it. If byte 0 is `)` or `;`, the Item or Object format decides, because its format is at least as strict. If byte 0 is another assigned identifier and its format also accepts the field, the tokenizer gives `ambiguous` on `obj.obsolete` at offset 0. It then uses the Object format, the stricter format. If that format does not accept the field, the identifier decides. |
| <a id="err.obj.time"></a>`err.obj.time` | p. 75/57, p. 76/58, p. 78/60, p. 80/62, p. 153/129 | One page makes the timestamp optional. Another page says that an Object "always has a timestamp". The template and the FLIGHTPTH example contain no timestamp. | conflict | 3 | The tokenizer accepts both ([amb.obj.time](#amb.obj.time)). |
| <a id="err.area.slash"></a>`err.area.slash` | p. 49/31, p. 78/60, p. 80/62 | The template `Tyy/Cxx` shows a fixed `'/'`. The colour table and the example `8101310` put `'1'` there for colours 10 to 15. | conflict | 3 | The tokenizer accepts both (`area.color`). |
| <a id="err.area.size"></a>`err.area.size` | p. 78/60 | APRS12c specifies area sizes from 60 feet to 100 miles. The two-digit offsets do not match this range. | conflict | 3 | The tokenizer accepts any two digits. It does not check the size. |
| <a id="err.area.sender"></a>`err.area.sender` | p. 78/60, p. 80/62 | The formulas for the offsets at the sender and at the receiver are not inverses of each other. | conflict | 3 | The tokenizer computes no offset, so this erratum has no effect. |
| <a id="err.area.gap"></a>`err.area.gap` | p. 78/60, p. 80/62 | The template and the FLIGHTPTH example show spaces around the symbol. The description in APRS12c puts the descriptor directly after the symbol. | conflict | 3 | A typing error. It permits nothing. No byte is between the symbol code and the descriptor. |

## 9. Reviewed exceptions

None.

## 10. Open items

None.
