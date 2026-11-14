# Weather reports and storm data

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that the general rules do not settle is marked **[open]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, general rules and tokenizer model: [README](README.md). |

## 1. Scope

Raw weather station output (`!!`, `#`, `$ULTW`, `*`), the positionless
report (`_`), complete reports carried by a position report or an object
(and an item, [amb.wx.carriers](#amb.wx.carriers)), the weather data
elements, the software and unit codes, and storm data. Shared fields
(timestamps, positions, symbols, the compressed block, data extensions)
are read by [02-fields.md](02-fields.md); NWS bulletins by
[08-message.md](08-message.md). No weather is looked for in Mic-E or
status reports, which no page names for it (README rule 2).

Offsets count from the data type identifier, offset 0.

## 2. Recognition

The token of the identifier byte carries the rule of the weather form
([01-frame.md](01-frame.md#7-data-type-identifier)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.raw.ultlog.dti"></a>`wx.raw.ultlog.dti` | Ultimeter logging form | `'!'` followed by a second `'!'` ([amb.wx.rawdti](#amb.wx.rawdti)). | - | 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.raw.ultpkt.dti"></a>`wx.raw.ultpkt.dti` | Ultimeter packet form | `'$'` followed by `ULTW` ([amb.wx.rawdti](#amb.wx.rawdti)). | - | 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.raw.peet"></a>`wx.raw.peet` | Peet Bros form | `'#'` or `'*'`. | - | 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.pl"></a>`wx.pl` | Positionless report | `'_'`. | - | 1 byte | p. 31/17, p. 83/63 |
| <a id="wx.pos"></a>`wx.pos` | Weather with position | `'!'`, `'='`, `'/'` or `'@'`, a position whose symbol code is `'_'` (any table byte, overlays included, p. 125/101), and at least one byte after the position block ([amb.wx.symbol](#amb.wx.symbol)). | - | 1 byte | p. 82/62, p. 85/65, p. 86/66 |
| <a id="wx.obj"></a>`wx.obj` | Weather on an object | `';'`, an object whose symbol code is `'_'`, in either position form, and at least one byte after the position block ([err.wx.object-dti](#err.wx.object-dti)). | - | 1 byte | p. 55/37, p. 85/65, p. 86/66 |

<a id="amb.wx.status"></a>The raw and positionless forms are marked "not
recommended" (p. 82/62, p. 83/63): each gives `discouraged` at offset 0
from the `dti` rules of 01. A position report or object that ends at its
`'_'` symbol code is a plain report, with no finding.

## 3. Raw weather reports

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.raw.ultlog"></a>`wx.raw.ultlog` | Ultimeter logging marker | `'!'` at offset 1. | For `wx.raw.ultlog.dti` | 1 byte | p. 82/62 |
| <a id="wx.raw.ultpkt"></a>`wx.raw.ultpkt` | Ultimeter packet marker | `ULTW` at offsets 1-4. | For `wx.raw.ultpkt.dti` | 4 bytes | p. 82/62 |
| <a id="wx.raw.data"></a>`wx.raw.data` | Station output | n bytes whose content APRS12c does not define; no byte is checked. None at all gives `unstated` at the end of the field. | Yes | End of field | p. 82/62, p. 132/108 |

## 4. Positionless weather report

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pl`](#wx.pl) | DTI | `'_'`. | Yes | 1 byte | p. 83/63 |
| [`time.mdhm`](02-fields.md#time.mdhm) | Timestamp | 8 digits, MDHM. | Yes | 8 bytes | p. 83/63 |
| [`wx.wdir`](#wx.wdir) ... | Weather data | Section 6; `c`, `s`, `g`, `t` lead, in that order. | Yes | Section 6.2 | p. 83/63, p. 84/64 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7. | No | End of field | p. 83/63 |

## 5. Complete weather reports

The position part is read as for any report of its kind. In place of
the `c` and `s` elements the report carries the wind (p. 85/65); every
element after it may come in any order, and none is required
([amb.wx.required](#amb.wx.required)).

### 5.1 Uncompressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pos`](#wx.pos) | DTI | `'!'`, `'='` (no timestamp), `'/'`, `'@'` (timestamp). | Yes | 1 byte | p. 85/65, p. 86/66 |
| [`time.dhm`](02-fields.md#time.dhm), [`time.hms`](02-fields.md#time.hms) | Timestamp | 7 bytes, after `'/'` or `'@'` only. | With `'/'`, `'@'` | 7 bytes | p. 86/66 |
| [`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code) | Position | As in 02; symbol code `'_'`. | Yes | 19 bytes | p. 85/65 |
| [`ext.dirspd`](02-fields.md#ext.dirspd) | Wind | Direction, `'/'`, speed, 3 bytes each. Each part is three digits, a number with one `'.'`, or unknown fill ([amb.wx.unknown](#amb.wx.unknown)), on its own. A direction above 360 gives `value`; other bytes give `syntax` at the first that fails. | Yes | 7 bytes | p. 45/27, p. 84/64, p. 85/65 |
| [`wx.gust`](#wx.gust) ... | Weather data | Section 6. | No | Section 6.2 | p. 85/65 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7. | No | End of field | p. 85/65 |

The wind field is present when the fourth of its seven bytes is `'/'`;
it then keeps its 7-byte token, cut short by the end of the field, with
one `syntax` finding at the first byte that fails. Otherwise it is
missing: `syntax` at the byte after the symbol code, and the weather data
is read from that byte. A wind field whose direction part fits has read
`c` and `s` (section 6.2).

### 5.2 Compressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pos`](#wx.pos) | DTI | `'!'`, `'='`, `'/'`, `'@'`. | Yes | 1 byte | p. 86/66 |
| [`time.dhm`](02-fields.md#time.dhm), [`time.hms`](02-fields.md#time.hms) | Timestamp | 7 bytes, after `'/'` or `'@'` only. | With `'/'`, `'@'` | 7 bytes | p. 86/66 |
| [`cmp.block`](02-fields.md#cmp.block) | Compressed block | As in 02, symbol code `'_'`; the `cs` bytes carry the wind ([amb.wx.cmpwind](#amb.wx.cmpwind)). | Yes | 13 bytes | p. 86/66 |
| [`wx.gust`](#wx.gust) ... | Weather data | Section 6, directly after the block; no 7-byte wind field. | No | Section 6.2 | p. 86/66 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7. | No | End of field | p. 86/66 |

### 5.3 Object

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.obj`](#wx.obj) | DTI | `';'` ([err.wx.object-dti](#err.wx.object-dti)). | Yes | 1 byte | p. 86/66 |
| [`obj.name`](05-object-item.md#obj.name), [`obj.state`](05-object-item.md#obj.state), [`obj.time`](05-object-item.md#obj.time) | Object header | As in 05. | Yes | As in 05 | p. 86/66 |
| [`obj.pos`](05-object-item.md#obj.pos) | Position | Uncompressed as 5.1, or compressed as 5.2, which may stand wherever the lat/long form does (p. 55/37). | Yes | As 5.1 or 5.2 | p. 55/37, p. 86/66 |
| [`ext.dirspd`](02-fields.md#ext.dirspd), [`wx.gust`](#wx.gust) ..., [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Wind, data, tail | As 5.1 or 5.2. | As 5.1 | As 5.1 | p. 86/66 |

## 6. Weather data elements

### 6.1 Elements

Each element is one letter and a value of fixed width, with no separator
(p. 84/64), and is one token. A value is digits, or a number with one
`'.'` among its digits ([amb.wx.width](#amb.wx.width)), or unknown fill:
`'.'` and SP only ([amb.wx.unknown](#amb.wx.unknown)). A `value` finding
is at the first byte of the value.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.wdir"></a>`wx.wdir` | Wind direction | `c`, 3 bytes, degrees; above 360 gives `value` (README rule 1). | Positionless, first | 4 bytes | p. 84/64 |
| <a id="wx.wspd"></a>`wx.wspd` | Wind speed | `s`, 3 bytes, mph. | Positionless, second | 4 bytes | p. 84/64 |
| <a id="wx.gust"></a>`wx.gust` | Gust | `g`, 3 bytes, mph. | Positionless, third | 4 bytes | p. 84/64 |
| <a id="wx.temp"></a>`wx.temp` | Temperature | `t`, 3 bytes, °F; below zero `'-'` and 2 digits, -01 to -99, so `-00` gives `value`. | Positionless, fourth | 4 bytes | p. 84/64 |
| <a id="wx.rain1h"></a>`wx.rain1h` | Rain, last hour | `r`, 3 bytes. | No | 4 bytes | p. 84/64 |
| <a id="wx.rain24h"></a>`wx.rain24h` | Rain, 24 hours | `p`, 3 bytes. | No | 4 bytes | p. 84/64 |
| <a id="wx.rainmid"></a>`wx.rainmid` | Rain since midnight | `P`, 3 bytes. | No | 4 bytes | p. 84/64 |
| <a id="wx.hum"></a>`wx.hum` | Humidity | `h`, 2 bytes, %; `00` is 100. | No | 3 bytes | p. 84/64 |
| <a id="wx.baro"></a>`wx.baro` | Pressure | `b`, 5 bytes, tenths of hPa. | No | 6 bytes | p. 84/64 |
| <a id="wx.lum"></a>`wx.lum` | Luminosity | `L`, 3 bytes, 000 to 999 W/m² ([amb.wx.lum](#amb.wx.lum)). | No | 4 bytes | p. 84/64 |
| <a id="wx.lumk"></a>`wx.lumk` | Luminosity, 1000 up | `l`, 3 bytes, 1000 more than the digits. | No | 4 bytes | p. 84/64 |
| <a id="wx.snow"></a>`wx.snow` | Snowfall, 24 hours | `s` outside the leading places, 3 bytes, inches ([amb.wx.order](#amb.wx.order)). | No | 4 bytes | p. 84/64 |
| <a id="wx.rawrain"></a>`wx.rawrain` | Raw rain counter | `#`; no width is stated ([amb.wx.rawrain](#amb.wx.rawrain)). | No | 1 byte | p. 84/64 |

### 6.2 Order and end of the data

In a positionless report `c`, `s`, `g` and `t` stand at four leading
places, in that order; "the remaining" may follow in any order
(p. 84/64). A leading place is present when it holds its letter; it is
then 4 bytes wide, and a value that does not fit gives one `syntax`
finding at the first byte at which neither the number nor the fill fits.
A place without its letter is a missing element: `syntax` where it was
expected, no byte used, and only the first of several missing places at
one byte gives it. A complete report has no leading places.

After that, an element is read wherever its letter is followed by a
value that fits its width. An element whose field this report has
already read keeps its token and gives `unstated` at its letter. A wind
field that has read `c` and `s` has read those fields; `wx.wspd` and
`wx.snow` are different fields ([amb.wx.order](#amb.wx.order)).

The data ends at the first byte that starts no such element. What
follows is, in this order:

1. the tail of section 7, when it is 1 to 5 bytes and either does not
   start with `#` or gives no finding as a tail;
2. `wx.rawrain` at a `#`, with `unstated`, and the rest a residue with no
   finding ([amb.wx.rawrain](#amb.wx.rawrain));
3. otherwise a residue named `wx.unit`, with `syntax` at its first byte
   ([amb.wx.comment](#amb.wx.comment), [amb.wx.letters](#amb.wx.letters)).

## 7. Software and unit codes

After the data a report may carry a 1-byte software code and a 2-4 byte
unit code, with no separator, and nothing after them (p. 83/63, p. 85/65,
p. 86/66). Neither byte set is stated.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.sw"></a>`wx.sw` | Software code | 1 byte. The codes `d`, `M`, `P`, `S`, `W`, `X`, and `w` ([err.wx.software-case](#err.wx.software-case)), an open list, as it names software (README section 3.3): another byte gives `unstated`. | No | 1 byte | p. 83/63 |
| <a id="wx.unit"></a>`wx.unit` | Unit code | 2-4 bytes, any code (the list is open), or one of `O`, `K`, `B`, `Y` ([err.wx.unit-length](#err.wx.unit-length)). | No | End of field | p. 83/63 |

A tail of 1 byte is a unit code when it is `O`, `K`, `B` or `Y`, and a
software code otherwise. A tail of 5 bytes is a software code and a
4-byte unit. A tail of 2 to 4 bytes is a software code and a unit when
its first byte is a listed software code and the rest is a unit code,
and one unit code otherwise ([amb.wx.tail](#amb.wx.tail)).

## 8. Storm data

Storm data may be carried by a position report, an object or an item
whose symbol is `\@` or `/@` (p. 87/67); an overlay table byte selects
the alternate table, so `\@` with an overlay is the storm symbol too
(p. 125/101). It stands directly after the 7-byte
[`ext.csespd`](02-fields.md#ext.csespd), the storm's direction and speed,
of an uncompressed report, where the comment would begin (p. 33/19,
p. 34/20). A storm type there announces storm data, which is then read
part by part: a part present by its leading byte is a token of its
width, cut short by the end of the field, with `syntax` at its first
byte that fails; a required part without its leading byte gives
`syntax` where it was expected. Without a storm type the bytes are the
comment ([amb.storm.placement](#amb.storm.placement)). Bytes after the
storm data are the comment of the carrying format, with its limit after
a data extension.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="storm.type"></a>`storm.type` | Storm type | `'/'`, then `TS`, `HC` or `TD` (closed list). | Yes | 3 bytes | p. 87/67 |
| <a id="storm.wind"></a>`storm.wind` | Sustained wind | `'/'`, 3 digits, knots. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.gust"></a>`storm.gust` | Peak gust | `'^'`, 3 digits, knots. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.press"></a>`storm.press` | Central pressure | `'/'`, 4 digits, hPa. | Yes | 5 bytes | p. 87/67 |
| <a id="storm.rhurr"></a>`storm.rhurr` | Radius of hurricane winds | `'>'`, 3 digits, nautical miles. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.rts"></a>`storm.rts` | Radius of tropical storm winds | `'&'`, 3 digits, nautical miles. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.rgale"></a>`storm.rgale` | Radius of 50-knot winds | `'%'`, 3 digits, nautical miles. | No | 4 bytes | p. 87/67 |

## 9. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.wx.rawdti"></a>`amb.wx.rawdti` | p. 31/17, p. 82/62 | `'!'` and `'$'` each start a position or NMEA sentence and an Ultimeter report, whose diagram is the identifier and n undefined bytes; only the examples show `!!` and `$ULTW`. | ambiguous | 4 | **[open]** By the rules every `'!'` or `'$'` field that fails as a position or NMEA sentence would be raw data and conform. Default: `!!` and `$ULTW` select raw weather, as in the examples, and other fields are read by 03; a `$ULTW` field that is also an NMEA sentence is 01's [amb.dti.shared](01-frame.md#amb.dti.shared). |
| <a id="amb.wx.symbol"></a>`amb.wx.symbol` | p. 76/58, p. 82/62, p. 85/65 | A complete report is identified by the `'_'` symbol, while the position and object formats let any symbol carry an extension and a comment. | ambiguous | 1 | The `'_'` symbol announces weather data: bytes after the block make the report weather, judged as weather data, with `syntax` where they are not; reading them as a plain comment does not make them conform. |
| <a id="amb.wx.carriers"></a>`amb.wx.carriers` | p. 33/19, p. 75/57, p. 85/65, p. 87/67 | The weather pages name positions and objects; items are handled as objects apart from listed differences (p. 75/57). | ambiguous | 1, 4 | The `'_'` symbol announces weather data on an item as on an object: bytes after the block are a complete report, judged as one, and the identifier token keeps `item.dti`. No `ambiguous`, as every such item carries the question. |
| <a id="amb.wx.order"></a>`amb.wx.order` | p. 84/64 | Whether an element may repeat; snowfall shares the letter `s` with wind speed. | unstated | 2 | Wind speed's place is the second leading place, so `s` elsewhere is snowfall. A repeat keeps its token and gives `unstated` at its letter. |
| <a id="amb.wx.required"></a>`amb.wx.required` | p. 84/64, p. 85/65, p. 86/66 | The minimum-content note names an MDHM timestamp, `c`, `s`, `g` and `t`, which fits only the positionless form; one object example has no `t`. | conflict | 3 | Positionless: a missing `c`, `s`, `g` or `t` gives `syntax`. Complete reports: `g` and `t` are optional. |
| <a id="amb.wx.unknown"></a>`amb.wx.unknown` | p. 84/64 | An unknown value is "a series of dots or spaces": all of one, or any mix. | ambiguous | 1 | Any mix of `'.'` and SP conforms; fill mixed with digits gives `syntax`. |
| <a id="amb.wx.width"></a>`amb.wx.width` | p. 84/64 | The sentence allowing a decimal point follows the snowfall entry and may cover snowfall or every value. | ambiguous | 1 | Every value may hold one `'.'`. A value of another width than its element's does not start an element. |
| <a id="amb.wx.rawrain"></a>`amb.wx.rawrain` | p. 84/64 | The raw rain counter has no width. | unstated | 2 | `#` is a 1-byte token with `unstated`; the rest of the field is residue, with no finding. |
| <a id="amb.wx.lum"></a>`amb.wx.lum` | p. 84/64 | `L` is put "in place of one of the rain values", not saying which, nor whether that value is then absent. | ambiguous | 1 | `L` and `l` are ordinary elements; all three rain elements beside them conform. |
| <a id="amb.wx.tail"></a>`amb.wx.tail` | p. 83/63, p. 84/64 | With no separator, a tail of 2 to 4 bytes can be one unit code or a software code and a unit. | ambiguous | 4 | Where the first byte is a listed software code, both splits give no finding, and the software code and unit is taken, whose first byte the listed codes constrain; otherwise one unit code. No finding, as every such tail carries the question. |
| <a id="amb.wx.comment"></a>`amb.wx.comment` | p. 34/20, p. 83/63, p. 85/65, p. 86/66 | No weather diagram has a comment, but p. 34/20 lets any packet carry one after its data. | ambiguous | 1 | The layout puts the tail of section 7 after the data, so the bytes there are judged as the tail; reading them as a comment does not make them conform. Bytes that are no tail or `#` are a residue with `syntax` (6.2); no comment item is looked for. |
| <a id="amb.wx.cmpwind"></a>`amb.wx.cmpwind` | p. 56/38, p. 57/39, p. 86/66 | The weather diagram makes `cs` the wind; the compression type byte and the first `cs` byte can make it an altitude, a range or nothing. | conflict | 3, 4 | Both sides conform. `cs` keeps the token of 02 (an altitude, which also constrains the type byte, is the more specific), with no finding, as every report with that type byte carries the question. Only a `cmp.cs.wind` token has read `c` and `s`. |
| <a id="amb.wx.letters"></a>`amb.wx.letters` | p. 84/64 | Other parameters "include" those listed, so other letters may occur, with no width. | unstated | 2 | **[open]** By rule 2 a letter outside 6.1 would be an element of the open list, with `unstated`, and the rest residue. Default: the letter ends the data, and the bytes from it are a tail or the residue of [amb.wx.comment](#amb.wx.comment). |
| <a id="amb.storm.placement"></a>`amb.storm.placement` | p. 34/20, p. 87/67 | Storm data is optional in a storm report and is not delimited from the comment. | ambiguous | 1, 4 | A storm type of the closed list announces storm data: the bytes are judged as storm data, as section 8 reads them, with `syntax` where they fail; reading them as comment does not make them conform. Without a storm type the bytes are comment text, no finding. |
| <a id="err.wx.object-dti"></a>`err.wx.object-dti` | p. 86/66, p. 134/110 | The Appendix 1 weather-object diagram has identifier `'*'`; chapter 12 and every other object diagram have `';'`. | conflict | 3 | A slip of the pen in the diagram (`'*'` for `';'`): it allows nothing. A weather object starts with `';'`, and every `'*'` field is the Peet Bros form, as 01's [err.dti.star](01-frame.md#err.dti.star) says. |
| <a id="err.wx.object-time"></a>`err.wx.object-time` | p. 86/66 | The first weather-object example has no timestamp; the diagram gives 7 bytes. | conflict | 3 | Both: 05 reads a position in place of the timestamp ([amb.obj.time](05-object-item.md#amb.obj.time)). |
| <a id="err.wx.object-baro"></a>`err.wx.object-baro` | p. 86/66 | The second weather-object example ends `b0990`, four digits for a 5-digit pressure. | conflict | 3 | A slip of the pen (one digit missing); it allows nothing: no 4-digit pressure is read. The bytes are a 5-byte tail: software code `b`, not a listed one, with `unstated`, and unit `0990`. |
| <a id="err.wx.cmp-example"></a>`err.wx.cmp-example` | p. 86/66 | The compressed example without timestamp has a `'>'` before `'_'`, 14 bytes for the 13-byte block. | conflict | 3 | A slip of the pen (one stray byte); it allows nothing, and the example gives `syntax`. |
| <a id="err.wx.unknown-example"></a>`err.wx.unknown-example` | p. 85/65 | The second example writes the pressure as `'.'`, SP and three `'.'`. | conflict | 3 | Accepted, as [amb.wx.unknown](#amb.wx.unknown) accepts any mix of the two. |
| <a id="err.wx.software-case"></a>`err.wx.software-case` | p. 83/63 to p. 86/66 | The list has `W` for WinAPRS; every example writes `w`. | conflict | 3 | `W` and `w` are both listed codes. |
| <a id="err.wx.unit-length"></a>`err.wx.unit-length` | p. 83/63 | Unit codes have 2-4 bytes, but the unit list ends with `O`, `K`, `B` and `Y`. | conflict | 3, 5 | Both: a unit code has 2-4 bytes or is one of the four. They are no software codes; the APRS 1.1 note that makes them so is not named by APRS12c. |
| <a id="err.wx.wind-units"></a>`err.wx.wind-units` | p. 37/23, p. 45/27, p. 84/64, p. 85/65 | The wind field's speed is in knots (p. 45/27), but it replaces `s`, in mph. | conflict | 3 | Both; no token or finding depends on the unit. |

## 10. Reviewed exceptions

None.

## 11. Open items

- [amb.wx.rawdti](#amb.wx.rawdti): which `'!'` and `'$'` fields are raw
  weather data, whose content is not stated.
- [amb.wx.letters](#amb.wx.letters): whether a letter outside 6.1 is an
  element of the open list, with the rest residue.
