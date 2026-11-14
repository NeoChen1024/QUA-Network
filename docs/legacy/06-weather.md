# Weather reports and storm data

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. A reviewed exception is marked **[agreed]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers these formats and fields:

- raw weather station output (`!!`, `#`, `$ULTW`, `*`);
- the positionless report (`_`);
- complete reports in a position report or an Object (and in an Item,
  [amb.wx.carriers](#amb.wx.carriers));
- the weather data fields;
- the software and unit codes;
- the comment after the data;
- storm data.

The tokenizer reads the shared fields (timestamps, positions, symbols,
the compressed block, data extensions) as [02-fields.md](02-fields.md)
says. It reads NWS bulletins as [08-message.md](08-message.md) says. The
tokenizer does not look for weather in Mic-E or status reports, because
no page names these formats for weather (README rule 2).

Offsets count from the data type identifier, at offset 0.

## 2. Recognition

The token of byte 0 has the rule ID of the weather format
([01-frame.md](01-frame.md#7-data-type-identifier)).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.raw.ultlog.dti"></a>`wx.raw.ultlog.dti` | Ultimeter logging format | `'!'` followed by a second `'!'` ([amb.wx.rawdti](#amb.wx.rawdti)). | - | 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.raw.ultpkt.dti"></a>`wx.raw.ultpkt.dti` | Ultimeter packet format | `'$'` followed by `ULTW` ([amb.wx.rawdti](#amb.wx.rawdti)). | - | 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.raw.peet"></a>`wx.raw.peet` | Peet Bros format | `'#'` or `'*'`. | - | 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.pl"></a>`wx.pl` | Positionless report | `'_'`. | - | 1 byte | p. 31/17, p. 83/63 |
| <a id="wx.pos"></a>`wx.pos` | Weather with position | `'!'`, `'='`, `'/'` or `'@'`, then a position with the symbol code `'_'` under any table byte, overlays included (p. 125/101). At least one byte follows the position block ([amb.wx.symbol](#amb.wx.symbol)). | - | 1 byte | p. 82/62, p. 85/65, p. 86/66 |
| <a id="wx.obj"></a>`wx.obj` | Weather on an Object | `';'`, then an Object with the symbol code `'_'`, in either position format. At least one byte follows the position block ([err.wx.object-dti](#err.wx.object-dti)). | - | 1 byte | p. 55/37, p. 85/65, p. 86/66 |

<a id="amb.wx.status"></a>APRS12c marks the raw and positionless formats
as "not recommended" (p. 82/62, p. 83/63). Each of these formats gives
`discouraged` at offset 0, from the `dti` rules of 01. If a position
report or Object ends at its `'_'` symbol code, it is an ordinary report,
with no finding.

## 3. Raw weather reports

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.raw.ultlog"></a>`wx.raw.ultlog` | Ultimeter logging marker | `'!'` at offset 1. | For `wx.raw.ultlog.dti` | 1 byte | p. 82/62 |
| <a id="wx.raw.ultpkt"></a>`wx.raw.ultpkt` | Ultimeter packet marker | `ULTW` at offsets 1-4. | For `wx.raw.ultpkt.dti` | 4 bytes | p. 82/62 |
| <a id="wx.raw.data"></a>`wx.raw.data` | Station output | n bytes. APRS12c does not specify their content. The tokenizer checks no byte. If there are no bytes, the tokenizer gives `unstated` at the end of the field. | Yes | End of field | p. 82/62, p. 132/108 |

## 4. Positionless weather report

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pl`](#wx.pl) | DTI | `'_'`. | Yes | 1 byte | p. 83/63 |
| [`time.mdhm`](02-fields.md#time.mdhm) | Timestamp | 8 digits, MDHM. | Yes | 8 bytes | p. 83/63 |
| [`wx.wdir`](#wx.wdir) ... | Weather data | Section 6. `c`, `s`, `g` and `t` come first, in that order. | Yes | Section 6.2 | p. 83/63, p. 84/64 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7: 1 to 5 bytes after the data. | No | End of field | p. 83/63 |
| [`cmt.text`](02-fields.md#cmt.text) | Comment | Section 7: 6 bytes or more after the data. | No | End of field | p. 34/20 |

## 5. Complete weather reports

The tokenizer reads the position fields as for any report of the same
kind. In place of the `c` and `s` fields, the report contains the wind
(p. 85/65). The fields after the wind can be in any order. None of them
is required ([amb.wx.required](#amb.wx.required)).

### 5.1 Uncompressed position

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pos`](#wx.pos) | DTI | `'!'`, `'='` (no timestamp), `'/'`, `'@'` (timestamp). | Yes | 1 byte | p. 85/65, p. 86/66 |
| [`time.dhm`](02-fields.md#time.dhm), [`time.hms`](02-fields.md#time.hms) | Timestamp | 7 bytes, after `'/'` or `'@'` only. | With `'/'`, `'@'` | 7 bytes | p. 86/66 |
| [`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code) | Position | As in 02, with the symbol code `'_'`. | Yes | 19 bytes | p. 85/65 |
| [`ext.dirspd`](02-fields.md#ext.dirspd) | Wind | Direction, `'/'`, speed, 3 bytes each. The direction and the speed are each three digits, a number with one `'.'`, or unknown fill ([amb.wx.unknown](#amb.wx.unknown)). The direction and the speed can use different formats. A direction above 360 gives `value`. Bytes that do not match give `syntax` at the first byte that fails. | Yes | 7 bytes | p. 45/27, p. 84/64, p. 85/65 |
| [`wx.gust`](#wx.gust) ... | Weather data | Section 6. | No | Section 6.2 | p. 85/65 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7: 1 to 5 bytes after the data. | No | End of field | p. 85/65 |
| [`cmt.text`](02-fields.md#cmt.text) | Comment | Section 7: 6 bytes or more after the data. | No | End of field | p. 34/20 |

If the fourth of its seven bytes is `'/'`, the wind field is present.
It then keeps its 7-byte token, which the end of the information field
can cut short. The wind field gives one `syntax` finding at the first
byte that fails. If the fourth byte is not `'/'`, the wind field is
missing. The tokenizer then gives `syntax` at the byte after the symbol
code and reads the weather data from that byte. If the direction of the
wind field matches, the tokenizer counts `c` and `s` as read for this
report (section 6.2).

### 5.2 Compressed position

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pos`](#wx.pos) | DTI | `'!'`, `'='`, `'/'`, `'@'`. | Yes | 1 byte | p. 86/66 |
| [`time.dhm`](02-fields.md#time.dhm), [`time.hms`](02-fields.md#time.hms) | Timestamp | 7 bytes, after `'/'` or `'@'` only. | With `'/'`, `'@'` | 7 bytes | p. 86/66 |
| [`cmp.block`](02-fields.md#cmp.block) | Compressed block | As in 02, with the symbol code `'_'`. The `cs` bytes contain the wind ([amb.wx.cmpwind](#amb.wx.cmpwind)). | Yes | 13 bytes | p. 86/66 |
| [`wx.gust`](#wx.gust) ... | Weather data | Section 6, directly after the block. There is no 7-byte wind field. | No | Section 6.2 | p. 86/66 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7: 1 to 5 bytes after the data. | No | End of field | p. 86/66 |
| [`cmt.text`](02-fields.md#cmt.text) | Comment | Section 7: 6 bytes or more after the data. | No | End of field | p. 34/20 |

No field after the block is required. Bytes there that start no weather
field are the tail or the comment (6.2).

### 5.3 Object

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.obj`](#wx.obj) | DTI | `';'` ([err.wx.object-dti](#err.wx.object-dti)). | Yes | 1 byte | p. 86/66 |
| [`obj.name`](05-object-item.md#obj.name), [`obj.state`](05-object-item.md#obj.state), [`obj.time`](05-object-item.md#obj.time) | Object header | As in 05. | Yes | As in 05 | p. 86/66 |
| [`obj.pos`](05-object-item.md#obj.pos) | Position | Uncompressed as in 5.1, or compressed as in 5.2. A compressed position can be at any place where the lat/long format can be (p. 55/37). | Yes | As 5.1 or 5.2 | p. 55/37, p. 86/66 |
| [`ext.dirspd`](02-fields.md#ext.dirspd), [`wx.gust`](#wx.gust) ..., [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit), [`cmt.text`](02-fields.md#cmt.text) | Wind, data, tail, comment | As 5.1 or 5.2. | As 5.1 | As 5.1 | p. 34/20, p. 86/66 |

## 6. Weather data fields

### 6.1 Elements

Each weather field is one letter and a value of fixed width, with no
separator (p. 84/64). Each weather field is one token. A value is one of
these:

- digits;
- a number with one `'.'` among its digits
  ([amb.wx.width](#amb.wx.width));
- unknown fill: `'.'` and SP only ([amb.wx.unknown](#amb.wx.unknown)).

The tokenizer puts a `value` finding at the first byte of the value.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.wdir"></a>`wx.wdir` | Wind direction | `c`, 3 bytes, degrees. A value above 360 gives `value` (README rule 1). | Positionless, first | 4 bytes | p. 84/64 |
| <a id="wx.wspd"></a>`wx.wspd` | Wind speed | `s`, 3 bytes, mph. | Positionless, second | 4 bytes | p. 84/64 |
| <a id="wx.gust"></a>`wx.gust` | Gust | `g`, 3 bytes, mph. | Positionless, third | 4 bytes | p. 84/64 |
| <a id="wx.temp"></a>`wx.temp` | Temperature | `t`, 3 bytes, °F. Below zero: `'-'` and 2 digits, -01 to -99. Thus `-00` gives `value`. | Positionless, fourth | 4 bytes | p. 84/64 |
| <a id="wx.rain1h"></a>`wx.rain1h` | Rain, last hour | `r`, 3 bytes. | No | 4 bytes | p. 84/64 |
| <a id="wx.rain24h"></a>`wx.rain24h` | Rain, 24 hours | `p`, 3 bytes. | No | 4 bytes | p. 84/64 |
| <a id="wx.rainmid"></a>`wx.rainmid` | Rain since midnight | `P`, 3 bytes. | No | 4 bytes | p. 84/64 |
| <a id="wx.hum"></a>`wx.hum` | Humidity | `h`, 2 bytes, %. `00` is 100. | No | 3 bytes | p. 84/64 |
| <a id="wx.baro"></a>`wx.baro` | Pressure | `b`, 5 bytes, tenths of hPa. | No | 6 bytes | p. 84/64 |
| <a id="wx.lum"></a>`wx.lum` | Luminosity | `L`, 3 bytes, 000 to 999 W/m² ([amb.wx.lum](#amb.wx.lum)). | No | 4 bytes | p. 84/64 |
| <a id="wx.lumk"></a>`wx.lumk` | Luminosity, 1000 up | `l`, 3 bytes, 1000 more than the digits. | No | 4 bytes | p. 84/64 |
| <a id="wx.snow"></a>`wx.snow` | Snowfall, 24 hours | `s` outside the leading places, 3 bytes, inches ([amb.wx.order](#amb.wx.order)). | No | 4 bytes | p. 84/64 |
| <a id="wx.rawrain"></a>`wx.rawrain` | Raw rain counter | `#`. APRS12c specifies no width. Thus a `#` never completes a weather field, and it ends the data ([amb.wx.rawrain](#amb.wx.rawrain)). | No | - | p. 84/64 |

### 6.2 Order and end of the data

In a positionless report, `c`, `s`, `g` and `t` are at four leading
places, in that order. "The remaining" fields can follow in any order
(p. 84/64). If a leading place contains its letter, the field is present
and is 4 bytes wide. If its value does not match, the tokenizer gives
one `syntax` finding. This finding is at the first byte where neither the
number nor the fill matches.

If a leading place does not contain its letter, the field is missing:

- The tokenizer gives `syntax` where the field was expected.
- The missing field uses no byte.
- If several places are missing at one byte, only the first gives the
  finding.

A complete report has no leading places.

After the leading places, the tokenizer reads a weather field at any
place where a matching value of the full width follows its letter. If
the tokenizer has already read the same field in the report, the
repeated field keeps its token and gives `unstated` at its letter. The
`c` and `s` that the tokenizer counts as read for a wind field (section
5.1) are also read fields for this check. `wx.wspd` and `wx.snow` are
different fields ([amb.wx.order](#amb.wx.order)).

The data ends at the first byte that starts no such field. The tokenizer
gives no finding there. That byte can be one of these:

- a letter that is not in 6.1 ([amb.wx.letters](#amb.wx.letters));
- a `#` ([amb.wx.rawrain](#amb.wx.rawrain));
- a letter of 6.1 whose value does not match, for example the `h` of
  `home`;
- any other byte.

The bytes from that byte to the end are:

1. the tail of section 7, if they are 1 to 5 bytes
   ([amb.wx.tail](#amb.wx.tail));
2. if not, a comment, as section 7 says
   ([amb.wx.comment](#amb.wx.comment)).

## 7. Software and unit codes

After the data, the diagrams show a 1-byte software code and a 2-4 byte
unit code, with no separator. They show nothing after these codes
(p. 83/63, p. 85/65, p. 86/66). APRS12c specifies no byte set for either
code. A comment can be at this place instead
([amb.wx.comment](#amb.wx.comment)).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.sw"></a>`wx.sw` | Software code | 1 byte. The codes are `d`, `M`, `P`, `S`, `W`, `X`, and `w` ([err.wx.software-case](#err.wx.software-case)). The list is open, because it names software (README section 3.3). Another byte gives `unstated`. | No | 1 byte | p. 83/63 |
| <a id="wx.unit"></a>`wx.unit` | Unit code | Any code of 2-4 bytes (the list is open), or one of `O`, `K`, `B`, `Y` ([err.wx.unit-length](#err.wx.unit-length)). | No | End of field | p. 83/63 |
| [`cmt.text`](02-fields.md#cmt.text) | Comment | 6 bytes or more after the data. The tokenizer reads it as in 02 section 8.1, with no length limit. | No | End of field | p. 34/20 |

The tokenizer divides the tail as follows
([amb.wx.tail](#amb.wx.tail)):

- A tail of 1 byte is a unit code if it is `O`, `K`, `B` or `Y`. If not,
  it is a software code.
- A tail of 5 bytes is a software code and a 4-byte unit code.
- A tail of 2 to 4 bytes has two cases:
  - If its first byte is a listed software code and the rest is a unit
    code, the tail has both codes.
  - If not, the tail is one unit code.

Six bytes or more after the data are a comment. APRS12c permits a
comment after the data of any packet (p. 34/20,
[amb.wx.comment](#amb.wx.comment)). The tokenizer reads it as
[`cmt.text`](02-fields.md#cmt.text), with the byte set of 02 section
8.1. APRS12c specifies no length limit for it, so the tokenizer checks
none. Of the fields of 02 section 8.2, the tokenizer looks for `cmt.alt`
and `cmt.noarchive` in it, and for no other.

## 8. Storm data

A position report, an Object or an Item can contain storm data if its
symbol is `\@` or `/@` (p. 87/67). An overlay table byte selects the
alternate table. Thus `\@` with an overlay is also the storm symbol
(p. 125/101). Storm data is directly after the 7-byte
[`ext.csespd`](02-fields.md#ext.csespd) of an uncompressed report, at
the place where the comment would start (p. 33/19, p. 34/20). This
`ext.csespd` is the direction and speed of the storm.

A storm type at this place is a marker that starts storm data. The
tokenizer then reads the storm data field by field:

- If a field starts with its leading byte, it is a token of its width.
  The end of the information field can cut this token short. The
  tokenizer gives `syntax` at its first byte that fails.
- If a required field does not start with its leading byte, the
  tokenizer gives `syntax` where the field was expected.

If there is no storm type, the bytes are the comment
([amb.storm.placement](#amb.storm.placement)). The bytes after the storm
data are the comment of the format that contains them. This comment has
the limit that applies after a data extension.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="storm.type"></a>`storm.type` | Storm type | `'/'`, then `TS`, `HC` or `TD` (closed list). | Yes | 3 bytes | p. 87/67 |
| <a id="storm.wind"></a>`storm.wind` | Sustained wind | `'/'`, 3 digits, knots. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.gust"></a>`storm.gust` | Peak gust | `'^'`, 3 digits, knots. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.press"></a>`storm.press` | Central pressure | `'/'`, 4 digits, hPa. | Yes | 5 bytes | p. 87/67 |
| <a id="storm.rhurr"></a>`storm.rhurr` | Radius of hurricane winds | `'>'`, 3 digits, nautical miles. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.rts"></a>`storm.rts` | Radius of tropical storm winds | `'&'`, 3 digits, nautical miles. | Yes | 4 bytes | p. 87/67 |
| <a id="storm.rgale"></a>`storm.rgale` | Radius of 50-knot winds | `'%'`, 3 digits, nautical miles. | No | 4 bytes | p. 87/67 |

## 9. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.wx.rawdti"></a>`amb.wx.rawdti` | p. 31/17, p. 82/62 | `'!'` starts a position, and `'$'` starts an NMEA sentence. Each of them also starts an Ultimeter report. The diagram of that report is the identifier and n bytes of unspecified content. Only the examples show `!!` and `$ULTW`. | ambiguous | 7 | As the reviewed exception of [section 10](#10-reviewed-exceptions) says, only `!!` and `$ULTW` select raw weather. The tokenizer reads every other `'!'` or `'$'` field as 03 says. If a `$ULTW` field is also an NMEA sentence, 01's [amb.dti.shared](01-frame.md#amb.dti.shared) applies. |
| <a id="amb.wx.symbol"></a>`amb.wx.symbol` | p. 76/58, p. 82/62, p. 85/65 | The `'_'` symbol identifies a complete report. But the position and Object formats permit an extension and a comment after any symbol. | ambiguous | 1 | The `'_'` symbol is a marker that starts weather data. If there are bytes after the block, the report is a weather report. The tokenizer reads it as section 5 says. In an uncompressed report, a missing wind field gives `syntax` at the byte after the symbol code (5.1). This also applies if the bytes there are text. An interpretation of the bytes as a comment does not prevent the finding. A comment can follow the data ([amb.wx.comment](#amb.wx.comment)). |
| <a id="amb.wx.carriers"></a>`amb.wx.carriers` | p. 33/19, p. 75/57, p. 85/65, p. 87/67 | The weather pages name positions and Objects. APRS12c handles Items as Objects, except for listed differences (p. 75/57). | ambiguous | 1, 4 | On an Item, as on an Object, the `'_'` symbol is a marker that starts weather data. The tokenizer reads the bytes after the block as a complete report. The token of byte 0 keeps the rule ID `item.dti`. The tokenizer gives no `ambiguous`, because every such Item has the same ambiguity. |
| <a id="amb.wx.order"></a>`amb.wx.order` | p. 84/64 | APRS12c does not say if a weather field can repeat. Snowfall and wind speed use the same letter `s`. | unstated | 2 | The place of wind speed is the second leading place. Thus `s` at any other place is snowfall. A repeated field keeps its token and gives `unstated` at its letter. |
| <a id="amb.wx.required"></a>`amb.wx.required` | p. 84/64, p. 85/65, p. 86/66 | The note on minimum content names an MDHM timestamp, `c`, `s`, `g` and `t`. This list matches only the positionless format. One Object example has no `t`. | conflict | 3 | Positionless: a missing `c`, `s`, `g` or `t` gives `syntax`. Complete reports: `g` and `t` are optional. |
| <a id="amb.wx.unknown"></a>`amb.wx.unknown` | p. 84/64 | An unknown value is "a series of dots or spaces". This can mean all of one byte, or any mix. | ambiguous | 1 | Any mix of `'.'` and SP gives no finding. Fill mixed with digits gives `syntax`. |
| <a id="amb.wx.width"></a>`amb.wx.width` | p. 84/64 | The sentence that permits a decimal point follows the snowfall entry. It can apply to snowfall only or to every value. | ambiguous | 1 | Every value can contain one `'.'`. A value whose width is not the width of its field does not start a field. |
| <a id="amb.wx.rawrain"></a>`amb.wx.rawrain` | p. 84/64 | APRS12c specifies no width for the raw rain counter. | unstated | 3, 4 | A `#` never completes a weather field, because APRS12c does not specify its full format. The data ends at the `#`. The bytes from it are the tail or the comment, with no finding, as for [amb.wx.letters](#amb.wx.letters). |
| <a id="amb.wx.lum"></a>`amb.wx.lum` | p. 84/64 | APRS12c puts `L` "in place of one of the rain values". It does not say which rain value, or if that value is then absent. | ambiguous | 1 | `L` and `l` are ordinary weather fields. The tokenizer accepts all three rain fields together with them. |
| <a id="amb.wx.tail"></a>`amb.wx.tail` | p. 34/20, p. 83/63, p. 84/64 | The tail has no separator. Thus a tail of 2 to 4 bytes can be one unit code, or a software code and a unit code. Any bytes after the data can also be a comment. | ambiguous | 4 | 1 to 5 bytes after the data are the tail, not a comment, because the tail is the stricter format. If a tail of 2 to 4 bytes starts with a listed software code, both divisions give no finding. The tokenizer then uses the software code and unit code, because this division is the stricter format: the listed codes restrict its first byte. If the first byte is not a listed software code, the tail is one unit code. The tokenizer gives no finding, because every tail has the same two ambiguities. |
| <a id="amb.wx.comment"></a>`amb.wx.comment` | p. 34/20, p. 83/63, p. 85/65, p. 86/66 | The weather diagrams show only a software code and a unit code after the data. But APRS12c permits a comment directly after the data of any packet (p. 34/20). | conflict | 3, 4 | The tokenizer accepts both. Bytes after the data that are not a tail ([amb.wx.tail](#amb.wx.tail)) are a comment. The tokenizer reads it as section 7 says. |
| <a id="amb.wx.cmpwind"></a>`amb.wx.cmpwind` | p. 56/38, p. 57/39, p. 86/66 | The weather diagram makes `cs` the wind. But the compression type byte and the first `cs` byte can make `cs` an altitude, a range or nothing. | conflict | 3, 4 | The tokenizer accepts both sides. An altitude also restricts the type byte, so the altitude is the stricter format. `cs` keeps the token of 02. The tokenizer gives no finding, because every report with that type byte has the same ambiguity. The tokenizer counts `c` and `s` as read only for a `cmp.cs.wind` token. |
| <a id="amb.wx.letters"></a>`amb.wx.letters` | p. 84/64 | The other parameters "include" those listed. Thus other letters can occur, with no specified width. | unstated | 3, 4 | A letter that is not in 6.1 starts no complete weather field. The data ends at this letter. The bytes from it are the tail or the comment ([amb.wx.comment](#amb.wx.comment)), with no finding. |
| <a id="amb.storm.placement"></a>`amb.storm.placement` | p. 34/20, p. 87/67 | Storm data is optional in a storm report. APRS12c specifies no delimiter between the storm data and the comment. | ambiguous | 1, 4 | A storm type of the closed list is a marker that starts storm data. The tokenizer reads the bytes as storm data, as section 8 says, with `syntax` where they fail. An interpretation of the bytes as a comment does not prevent the finding. If there is no storm type, the bytes are comment text, with no finding. |
| <a id="err.wx.object-dti"></a>`err.wx.object-dti` | p. 86/66, p. 134/110 | The weather Object diagram of Appendix 1 has the identifier `'*'`. Chapter 12 and every other Object diagram have `';'`. | conflict | 3 | A typing error in the diagram (`'*'` for `';'`). It permits nothing. A weather Object starts with `';'`. Every `'*'` field is the Peet Bros format, as 01's [err.dti.star](01-frame.md#err.dti.star) says. |
| <a id="err.wx.object-time"></a>`err.wx.object-time` | p. 86/66 | The first weather Object example has no timestamp. The diagram specifies 7 bytes. | conflict | 3 | The tokenizer accepts both. 05 reads a position in place of the timestamp ([amb.obj.time](05-object-item.md#amb.obj.time)). |
| <a id="err.wx.object-baro"></a>`err.wx.object-baro` | p. 86/66 | The second weather Object example ends with `b0990`. This is four digits for a 5-digit pressure. | conflict | 3 | A typing error (one digit is missing). It permits nothing, and the tokenizer reads no 4-digit pressure. The bytes are a 5-byte tail: the software code `b`, which is not a listed code, with `unstated`, and the unit code `0990`. |
| <a id="err.wx.cmp-example"></a>`err.wx.cmp-example` | p. 86/66 | The compressed example without a timestamp has a `'>'` before `'_'`. This makes 14 bytes for the 13-byte block. | conflict | 3 | A typing error (one extra byte). It permits nothing, and the example gives `syntax`. |
| <a id="err.wx.unknown-example"></a>`err.wx.unknown-example` | p. 85/65 | The second example shows the pressure as `'.'`, SP and three `'.'`. | conflict | 3 | The tokenizer accepts it, because [amb.wx.unknown](#amb.wx.unknown) accepts any mix of the two bytes. |
| <a id="err.wx.software-case"></a>`err.wx.software-case` | p. 83/63 to p. 86/66 | The list contains `W` for WinAPRS. Every example shows `w`. | conflict | 3 | `W` and `w` are both listed codes. |
| <a id="err.wx.unit-length"></a>`err.wx.unit-length` | p. 83/63 | Unit codes have 2-4 bytes, but the unit list ends with `O`, `K`, `B` and `Y`. | conflict | 3, 5 | The tokenizer accepts both: a unit code has 2-4 bytes or is one of the four. These four are not software codes. APRS12c does not name the APRS 1.1 note that makes them software codes. |
| <a id="err.wx.wind-units"></a>`err.wx.wind-units` | p. 37/23, p. 45/27, p. 84/64, p. 85/65 | The speed of the wind field is in knots (p. 45/27). But the wind field replaces `s`, which is in mph. | conflict | 3 | The tokenizer accepts both. No token or finding depends on the unit. |

## 10. Reviewed exceptions

**[agreed]** Raw weather under `'!'` and `'$'` (p. 31/17, p. 82/62).
The diagram of the two Ultimeter formats contains the identifier and n
bytes of station output. It does not say what these bytes are. The
tokenizer reads these fields as follows:

- Only a field that starts with `!!` or `$ULTW`, as the examples show, is
  a raw Ultimeter report ([`wx.raw.ultlog.dti`](#wx.raw.ultlog.dti),
  [`wx.raw.ultpkt.dti`](#wx.raw.ultpkt.dti)).
- The tokenizer reads every other `'!'` field as a position and every
  other `'$'` field as an NMEA sentence ([03](03-position.md)).

As the author decided, the reason is that the n bytes of raw data cannot
be any content at all. If they could be any content, a `'!'` position
could never fail.

## 11. Open items

None.
