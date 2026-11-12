# Weather reports and storm data

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, tokenizer model and decoder commits: [README](README.md). |

## 1. Scope

This file states how the tokenizer reads weather reports of every form
and storm data:

- raw weather station output (`!!`, `#`, `$ULTW`, `*`);
- the positionless weather report (`_`);
- complete weather reports carried by a position report, with or without
  a timestamp, uncompressed or compressed, and by an object;
- the weather data elements, the software code and the unit code;
- storm data in position, object and item reports.

Fields shared with other formats (timestamps, latitude and longitude,
symbol, the compressed block, the data extension) are tokenized by the
rules of [02-fields.md](02-fields.md) and are only referenced here.
[01-frame.md](01-frame.md#7-data-type-identifier) dispatches on the data
type identifier byte; the token of that byte carries the identifier rule
of the weather form, defined in section 2. National Weather Service
bulletins are messages and are read in [08-message.md](08-message.md).

Raw and positionless reports carry no symbol. APRS12c lets such a station
give one through a generic destination address, or mark a balloon with
source SSID 11, and asks it to send its position in a separate packet
(p. 85/65). Those are matters of the address fields
([01-frame.md](01-frame.md)) and of station behaviour; nothing in the
information field is tokenized for them here.

Byte offsets below count from the first byte of the information field
(the data type identifier is offset 0).

## 2. Recognition

**[proposed]** The tokenizer decides that a packet is a weather report
from the data type identifier and, for the position and object forms,
from the symbol code. Each row names a form that the rest of this file
then applies. Its ID is the identifier rule of that form: the token of
the data type identifier byte at offset 0 carries it, as
[README section 3](README.md#3-tokenizer-model) requires.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.raw.ultlog.dti"></a>`wx.raw.ultlog.dti` | Ultimeter logging form | DTI `'!'` followed at offset 1 by a second `'!'` ([`wx.raw.ultlog`](#wx.raw.ultlog)). Reading: [amb.wx.rawdti](#amb.wx.rawdti). | - | Fixed 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.raw.ultpkt.dti"></a>`wx.raw.ultpkt.dti` | Ultimeter packet form | DTI `'$'` followed by the 4 bytes `ULTW` at offsets 1-4 ([`wx.raw.ultpkt`](#wx.raw.ultpkt)). Reading: [amb.wx.rawdti](#amb.wx.rawdti). | - | Fixed 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.raw.peet"></a>`wx.raw.peet` | Peet Bros form | DTI `'#'` or `'*'`. No marker bytes follow the DTI. | - | Fixed 1 byte | p. 31/17, p. 82/62 |
| <a id="wx.pl"></a>`wx.pl` | Positionless report | DTI `'_'`. | - | Fixed 1 byte | p. 31/17, p. 83/63 |
| <a id="wx.pos"></a>`wx.pos` | Weather with position | DTI `'!'`, `'='`, `'/'` or `'@'`, a position whose [`sym.code`](02-fields.md#sym.code) or [`cmp.code`](02-fields.md#cmp.code) is `'_'`, and at least one byte after the position block. Handed over by [`pos.wx`](03-position.md#pos.wx). Reading: [amb.wx.symbol](#amb.wx.symbol). | - | Fixed 1 byte | p. 82/62, p. 85/65 to p. 86/66 |
| <a id="wx.obj"></a>`wx.obj` | Weather on an object | DTI `';'`, an object (see [05-object-item.md](05-object-item.md#7-weather-and-storm-data-on-objects)) whose symbol code is `'_'`, and at least one byte after the position block. Reading: [amb.wx.carriers](#amb.wx.carriers). | - | Fixed 1 byte | p. 85/65, p. 86/66 |

**[agreed]** The raw and positionless forms are marked "not
recommended" (p. 82/62, p. 83/63). Each gives a `discouraged` finding at
offset 0, from the `dti` rules of
[01-frame.md](01-frame.md#7-data-type-identifier). See
[amb.wx.status](#amb.wx.status).

**[proposed]** A `'_'` report whose symbol table byte is neither `'/'`
nor `'\'` gives an `ambiguous` finding against `wx.pos` or `wx.obj` at
that table byte, unless the bytes after the position block give a
`syntax` or `value` finding. See [amb.wx.symbol](#amb.wx.symbol).

**[proposed]** The weather rules are not applied to items, to Mic-E
reports or to any other format. Where such a report would read as
weather, it gets an `ambiguous` finding; see
[amb.wx.carriers](#amb.wx.carriers).
Storm data (section 8) is read in items as well.

**[agreed]** A position report whose information field ends at the
`'_'` symbol code does not match `wx.pos`. It is an ordinary position
report, read by [03-position.md](03-position.md#pos.wx) with no finding
([amb.pos.wxsym](03-position.md#amb.pos.wxsym)). **[proposed]** The same
holds for an object, which then does not match `wx.obj` and is read by
[05-object-item.md](05-object-item.md#7-weather-and-storm-data-on-objects).
Every other `'_'` report of those kinds is handed to this file at the
byte after the position block.

## 3. Raw weather reports

APRS12c names the weather stations that produce these forms and gives
one example of each, but it does not define their content (p. 82/62). The
tokenizer finds the boundaries only.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.raw.ultlog.dti`](#wx.raw.ultlog.dti), [`wx.raw.ultpkt.dti`](#wx.raw.ultpkt.dti), [`wx.raw.peet`](#wx.raw.peet) | DTI | `'!'`, `'$'`, or `'#'` and `'*'`, at offset 0. | Required | Fixed 1 byte | p. 82/62 |
| <a id="wx.raw.ultlog"></a>`wx.raw.ultlog` | Ultimeter logging marker | `'!'` at offset 1. | Required for `wx.raw.ultlog.dti` | Fixed 1 byte | p. 82/62 |
| <a id="wx.raw.ultpkt"></a>`wx.raw.ultpkt` | Ultimeter packet marker | `ULTW` at offsets 1-4. | Required for `wx.raw.ultpkt.dti` | Fixed 4 bytes | p. 82/62 |
| <a id="wx.raw.data"></a>`wx.raw.data` | Station output | All remaining bytes, content not defined by APRS12c. Starts at offset 2 (`!!`), 5 (`$ULTW`) or 1 (`#`, `*`). | Required, at least 1 byte | End of information field | p. 82/62, p. 132/108 |

**[proposed]** `wx.raw.data` is one token. The tokenizer checks no byte
set, length or structure in it and reports no finding on its content,
because APRS12c states none. An empty `wx.raw.data` gives a `syntax`
finding (the diagram gives it a length of `n` and every example has
content).

## 4. Positionless weather report

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pl`](#wx.pl) | DTI | `'_'` at offset 0. | Required | Fixed 1 byte | p. 83/63 |
| [`time.mdhm`](02-fields.md#time.mdhm) | Timestamp | 8 digits, month, day, hour, minute; offsets 1-8. | Required | Fixed 8 bytes | p. 38/22, p. 83/63 |
| [`wx.wdir`](#wx.wdir) ... | Weather data | Elements from offset 9, section 6. The first four are wind direction `c`, wind speed `s`, gust `g` and temperature `t`, in that order. | Required | First byte that does not start an element | p. 83/63, p. 84/64 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7. | Optional | End of information field | p. 83/63 |

## 5. Complete weather reports

A complete report is a position report or an object whose symbol code is
`'_'`. The position part is read as for any other report of its kind. In
place of the course and speed that would follow the symbol, the report
carries the wind. Wind direction `c` and wind speed `s` elements do not
occur in the weather data, because the wind field replaces them
(p. 85/65). The diagrams show gust and temperature next; in a complete
report they are optional ([amb.wx.required](#amb.wx.required)).

### 5.1 Uncompressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pos`](#wx.pos) | DTI | `'!'` or `'='` (no timestamp), `'/'` or `'@'` (timestamp). | Required | Fixed 1 byte | p. 85/65, p. 86/66 |
| [`time.dhm`](02-fields.md#time.dhm), [`time.hms`](02-fields.md#time.hms) | Timestamp | 7 bytes, only after `'/'` or `'@'`. | Required with `'/'`, `'@'`; absent otherwise | Fixed 7 bytes | p. 86/66 |
| [`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon) | Position | As in 02. | Required | Fixed 8 + 1 + 9 bytes | p. 85/65 |
| [`sym.code`](02-fields.md#sym.code) | Symbol code | `'_'`. | Required | Fixed 1 byte | p. 85/65 |
| [`ext.dirspd`](02-fields.md#ext.dirspd) | Wind | 3-byte direction, `'/'`, 3-byte speed, directly after the symbol code. Reading: [amb.wx.required](#amb.wx.required). | Required | Fixed 7 bytes | p. 45/27, p. 85/65 |
| [`wx.gust`](#wx.gust) ... | Weather data | Elements, section 6, in any order (section 6.2). | Optional | First byte that does not start an element | p. 85/65, p. 86/66 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7. | Optional | End of information field | p. 85/65 |

**[proposed]** If the 7 bytes after the symbol code do not match
[`ext.dirspd`](02-fields.md#ext.dirspd), the tokenizer reports `syntax`
against `ext.dirspd` at the first byte after the symbol code and reads
the weather data from that byte.

### 5.2 Compressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.pos`](#wx.pos) | DTI | `'!'`, `'='`, `'/'` or `'@'`. | Required | Fixed 1 byte | p. 86/66 |
| [`time.dhm`](02-fields.md#time.dhm), [`time.hms`](02-fields.md#time.hms) | Timestamp | 7 bytes, only after `'/'` or `'@'`. | As in 5.1 | Fixed 7 bytes | p. 86/66 |
| [`cmp.block`](02-fields.md#cmp.block) | Compressed block | 13 bytes: table, 4 bytes latitude, 4 bytes longitude, symbol code `'_'`, the 2 bytes [`cmp.cs`](02-fields.md#cmp.cs) carrying the wind, and [`cmp.t`](02-fields.md#cmp.t). Reading: [amb.wx.cmpwind](#amb.wx.cmpwind). | Required | Fixed 13 bytes | p. 86/66 |
| [`wx.gust`](#wx.gust) ... | Weather data | Elements, section 6, in any order (section 6.2), directly after the compression type byte. | Optional | First byte that does not start an element | p. 86/66 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7. | Optional | End of information field | p. 86/66 |

No 7-byte wind field follows the compressed block: the wind is in its
`cs` bytes (p. 86/66). Seven bytes of the shape of `ext.dirspd` after the
block are not a wind field here; they are read as weather data and fail
there, giving `syntax` (UAP 5.33 describes such a packet).

### 5.3 Object

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`wx.obj`](#wx.obj) | DTI | `';'`. | Required | Fixed 1 byte | p. 86/66 |
| [`obj.name`](05-object-item.md#obj.name), [`obj.state`](05-object-item.md#obj.state), [`obj.time`](05-object-item.md#obj.time) | Object header | As in [05-object-item.md](05-object-item.md#2-object-report). The weather diagram shows the live state `'*'` and a 7-byte timestamp. | Required | Fixed 9 + 1 + 7 bytes | p. 86/66 |
| [`obj.pos`](05-object-item.md#obj.pos) | Position and symbol | As 5.1 (uncompressed) or 5.2 (compressed); symbol code `'_'`. | Required | As 5.1 or 5.2 | p. 85/65, p. 86/66 |
| [`ext.dirspd`](02-fields.md#ext.dirspd) | Wind | Uncompressed only, as 5.1. | Required | Fixed 7 bytes | p. 86/66 |
| [`wx.gust`](#wx.gust) ... | Weather data | As 5.1 or 5.2. | Optional | First byte that does not start an element | p. 86/66 |
| [`wx.sw`](#wx.sw), [`wx.unit`](#wx.unit) | Tail | Section 7. | Optional | End of information field | p. 86/66 |

**[proposed]** An object with a compressed position and symbol code `'_'`
is read as 5.2 after the object header. APRS12c diagrams only the
uncompressed weather object (p. 86/66), but says a complete report may use
"any" position format and that an object may carry weather (p. 85/65).

## 6. Weather data elements

Weather data is a run of elements with no separator. Each element is one
letter followed by a value of fixed width (p. 84/64). Each element is one
depth-0 token covering the letter and its value.

### 6.1 Elements

"Unknown" in the table is the fill a sender uses when the value is not
known: the whole value written as `'.'` bytes, or the whole value written
as `SP` bytes (p. 84/64). Reading:
[amb.wx.unknown](#amb.wx.unknown).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.wdir"></a>`wx.wdir` | Wind direction | `'c'`, then 3 digits, degrees. A value above 360 gives `value` (range taken from [`ext.dirspd`](02-fields.md#ext.dirspd), which replaces it). Unknown allowed. | Positionless: required, first element. Absent in complete reports. | Fixed 4 bytes | p. 45/27, p. 84/64 |
| <a id="wx.wspd"></a>`wx.wspd` | Wind speed | `'s'`, then 3 digits, sustained one-minute speed. Unknown allowed. | Positionless: required, second element. Absent in complete reports. | Fixed 4 bytes | p. 84/64 |
| <a id="wx.gust"></a>`wx.gust` | Gust | `'g'`, then 3 digits, peak in the last five minutes. Unknown allowed. | Positionless: required, third element. Complete reports: optional. Reading: [amb.wx.required](#amb.wx.required). | Fixed 4 bytes | p. 84/64 |
| <a id="wx.temp"></a>`wx.temp` | Temperature | `'t'`, then 3 digits, or `'-'` and 2 digits for -01 to -99. `-00` gives `value`. Unknown allowed. | Positionless: required, fourth element. Complete reports: optional. | Fixed 4 bytes | p. 84/64 |
| <a id="wx.rain1h"></a>`wx.rain1h` | Rain, last hour | `'r'`, then 3 digits, hundredths of an inch. Unknown allowed. | Optional | Fixed 4 bytes | p. 84/64 |
| <a id="wx.rain24h"></a>`wx.rain24h` | Rain, last 24 hours | `'p'`, then 3 digits, hundredths of an inch. Unknown allowed. | Optional | Fixed 4 bytes | p. 84/64 |
| <a id="wx.rainmid"></a>`wx.rainmid` | Rain since midnight | `'P'`, then 3 digits, hundredths of an inch. Unknown allowed. | Optional | Fixed 4 bytes | p. 84/64 |
| <a id="wx.hum"></a>`wx.hum` | Humidity | `'h'`, then 2 digits, percent; `00` stands for 100. Unknown allowed. | Optional | Fixed 3 bytes | p. 84/64 |
| <a id="wx.baro"></a>`wx.baro` | Pressure | `'b'`, then 5 digits, tenths of a hectopascal. Unknown allowed. | Optional | Fixed 6 bytes | p. 84/64 |
| <a id="wx.lum"></a>`wx.lum` | Luminosity | `'L'`, then 3 digits, 000 to 999 W/m². Unknown allowed. | Optional. Reading: [amb.wx.rawrain](#amb.wx.rawrain). | Fixed 4 bytes | p. 84/64 |
| <a id="wx.lumk"></a>`wx.lumk` | Luminosity, 1000 and up | `'l'` (lower case), then 3 digits; the value is 1000 more than the digits. Unknown allowed. | Optional | Fixed 4 bytes | p. 84/64 |
| <a id="wx.snow"></a>`wx.snow` | Snowfall, last 24 hours | `'s'`, then 3 bytes: digits with at most one `'.'`, inches. Unknown allowed. Which `'s'` this is: [amb.wx.order](#amb.wx.order). Decimal point: [amb.wx.width](#amb.wx.width). | Optional | Fixed 4 bytes | p. 84/64 |
| <a id="wx.rawrain"></a>`wx.rawrain` | Raw rain counter | `'#'`, then 3 digits. Width not stated; the tokenizer reports `unstated` on every occurrence. Reading: [amb.wx.rawrain](#amb.wx.rawrain). | Optional | Fixed 4 bytes | p. 84/64 |

A letter is an element only when its full value follows and matches the
layout in its row. A defined letter whose value does not match does not
start an element.

### 6.2 Order and end of the data

**[proposed]** In a positionless report the leading elements `c`, `s`,
`g`, `t` are read at fixed places. If one is missing, the tokenizer
reports `syntax` against its ID at the offset where it was expected and
continues. A complete report has no leading elements: after the wind,
every element, gust and temperature included, may come in any order.
The remaining elements of a positionless report may also come in any
order. Reading: [amb.wx.order](#amb.wx.order),
[amb.wx.required](#amb.wx.required).

**[proposed]** An element whose field has already been read in this
report is still tokenized, and the tokenizer reports `unstated` against
it. `wx.wspd` and `wx.snow` are different fields for this purpose.

**[proposed]** The weather data ends at the first byte, after the leading
elements, that does not start an element of section 6.1. A letter that
APRS12c does not define ends the data. Reading:
[amb.wx.letters](#amb.wx.letters), [amb.wx.width](#amb.wx.width).

## 7. Software and unit codes

After the weather data, a report may carry a 1-byte code for the APRS
software at the station and a 2-4 byte code for the weather station unit,
with no separator (p. 83/63). Both are optional, and nothing else is
defined after them.

Listed software codes (p. 83/63): `d`, `M`, `P`, `S`, `W`, `X`. This
reading adds `w` ([err.wx.software-case](#err.wx.software-case)) and
**[agreed]** `O`, `K`, `B` and `Y`
([err.wx.unit-length](#err.wx.unit-length)).

Listed unit codes (p. 83/63): `Dvs`, `HKT`, `PIC`, `RSW`, `U-II`, `U2R`,
`U2k`, `U2kr`, `U5`, `Upkm`. Any other unit code of 2-4 bytes is
allowed. **[agreed]** A unit code has 2-4 bytes; there is no 1-byte unit
code ([err.wx.unit-length](#err.wx.unit-length)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="wx.sw"></a>`wx.sw` | Software code | 1 byte, a letter. A letter outside the listed set gives `unstated`. | Optional | Fixed 1 byte | p. 83/63 |
| <a id="wx.unit"></a>`wx.unit` | Unit code | 2-4 bytes of letters, digits and `'-'`. A code not in the list gives no finding. | Optional | End of information field | p. 83/63 |

**[proposed]** The tail is everything after the weather data. If it is
empty, there is no `wx.sw` and no `wx.unit`. If it is longer than 5
bytes, or holds a byte other than a letter, a digit or `'-'`, it is not a
tail: see [amb.wx.comment](#amb.wx.comment). Otherwise it is split by its
length (reading: [amb.wx.tail](#amb.wx.tail)):

| Tail length | Read as | Finding |
|---|---|---|
| 1 | `wx.sw`. | `unstated` for a letter not in the software list. A digit or `'-'`: `syntax`. |
| 2 | `wx.unit` of 2 bytes. | None. |
| 3 or 4, first byte a letter | In this order: if the bytes after the first form a listed unit code, `wx.sw` + `wx.unit`; otherwise, if the whole tail is a listed unit code, `wx.unit`; otherwise, if the first byte is a listed software code, `wx.sw` + `wx.unit`; otherwise `wx.unit` of 3 or 4 bytes. | `ambiguous` against `wx.sw` at the first byte of the tail, in every case: the tail splits two ways. Also `unstated` when the first byte is read as `wx.sw` and is not in the software list. |
| 3 or 4, first byte a digit or `'-'` | `wx.unit` of 3 or 4 bytes. | None. |
| 5 | `wx.sw` + `wx.unit` of 4 bytes. | `unstated` when the first byte is a letter not in the software list; `syntax` when it is not a letter. |

## 8. Storm data

Storm data describes a tropical storm, hurricane or tropical depression.
It is usually sent as an object, and may also be sent as a position
report or an item (p. 87/67). The storm's direction and speed of motion
are the 7-byte [`ext.csespd`](02-fields.md#ext.csespd) after the symbol
code; the storm fields follow it, where the comment would begin.

**[proposed]** The tokenizer reads storm data when all of these hold
(reading: [amb.storm.placement](#amb.storm.placement)):

- the report is an uncompressed position report (03), object or item
  (05);
- its symbol code is `'@'`;
- the 7 bytes after the symbol code are an
  [`ext.csespd`](02-fields.md#ext.csespd);
- the next byte is `'/'` and the two after it are `TS`, `HC` or `TD`.

**[proposed]** Storm-shaped bytes that these conditions leave as
comment get an `ambiguous` finding where another reading would take
them as storm data ([amb.storm.placement](#amb.storm.placement)).

**[proposed]** With a symbol table byte other than `'/'` or `'\'` the
storm data is still read, and the tokenizer reports `unstated` against
[`sym.table`](02-fields.md#sym.table).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| [`ext.csespd`](02-fields.md#ext.csespd) | Direction and speed of motion | 3 bytes, `'/'`, 3 bytes, directly after the symbol code. | Required | Fixed 7 bytes | p. 87/67 |
| <a id="storm.type"></a>`storm.type` | Storm type | `'/'`, then `TS` (tropical storm), `HC` (hurricane) or `TD` (tropical depression). | Required | Fixed 3 bytes | p. 87/67 |
| <a id="storm.wind"></a>`storm.wind` | Sustained wind | `'/'`, then 3 digits, knots. | Required | Fixed 4 bytes | p. 87/67 |
| <a id="storm.gust"></a>`storm.gust` | Peak gust | `'^'`, then 3 digits, knots. | Required | Fixed 4 bytes | p. 87/67 |
| <a id="storm.press"></a>`storm.press` | Central pressure | `'/'`, then 4 digits, hectopascals. | Required | Fixed 5 bytes | p. 87/67 |
| <a id="storm.rhurr"></a>`storm.rhurr` | Radius of hurricane winds | `'>'`, then 3 digits, nautical miles. | Required | Fixed 4 bytes | p. 87/67 |
| <a id="storm.rts"></a>`storm.rts` | Radius of tropical storm winds | `'&'`, then 3 digits, nautical miles. | Required | Fixed 4 bytes | p. 87/67 |
| <a id="storm.rgale"></a>`storm.rgale` | Radius of 50-knot winds | `'%'`, then 3 digits, nautical miles. | Optional | Fixed 4 bytes | p. 87/67 |

**[proposed]** Once `storm.type` has matched, a later required field that
does not match gives `syntax` against its ID at the offset where it was
expected, and the bytes from there on are the comment. A value written
wholly as `'.'` bytes or wholly as `SP` bytes is accepted and gives
`unstated`. Bytes after the last storm field are the comment of the
report, read by [`cmt.text`](02-fields.md#cmt.text) and the rules of the
carrying format.

## 9. Ambiguities

<a id="amb.wx.rawdti"></a>
### amb.wx.rawdti

- **Open.** `'!'` starts both a position report without timestamp and the
  Ultimeter logging output; `'$'` starts both raw NMEA and the Ultimeter
  packet output (p. 31/17, p. 82/62). APRS12c gives no rule to tell them
  apart. The examples start `!!` and `$ULTW` (p. 82/62).
- **Readings.** (a) Decide by the bytes after the DTI: a second `'!'`, or
  `ULTW`. (b) Try the position or NMEA grammar first and fall back to raw
  weather.
- **Taken.** **[proposed]** (a). A second `'!'` cannot start a position
  (neither a latitude digit nor a valid symbol table byte), so reading (b)
  gives the same result for `!!`. A `'$'` field not followed by `ULTW` is
  NMEA ([03-position.md](03-position.md)). Not visible in the bytes as an
  alternative: decided silently, no `ambiguous` finding.
- **Decoders.**

  | Decoder | What it does | Where |
  |---|---|---|
  | FAP | After a `!` DTI, a second `!` selects the Ultimeter logging parser. `$` with `$ULTW` selects the packet parser; only `$GP` is NMEA. `#` and `*` are not parsed. | `parseaprs`, FAP.pm:2648, 2686 |
  | Dire Wolf | `!!` and `$ULTW` go to its Ultimeter decoder; other `$` is NMEA. The `#` and `*` cases are commented out. | `decode_aprs`, decode_aprs.c:343, 355-363 |
  | aprslib | `#`, `*` and `$` are listed as unsupported formats. `!!` goes to the position parser and fails there. | `parsing/__init__.py`:48-54, 206 |
  | Xastir | Second `!` plus 40 hex-or-dash bytes is Ultimeter logging; `$` plus `ULTW` and 44 hex-or-dash bytes is packet mode; `#` and `*` need 13 hex-or-dash bytes. | `decode_info_field`, db.c:14999, 15144-15173 |
  | aprsc | Marks `!!`, `#`, `*`, `_` and `$ULT` as weather. | `parse_aprs_body`, parse_aprs.c:1205, 1290; `parse_aprs_nmea`, parse_aprs.c:333 |
  | javAPRSlib | `$ULTW` is skipped; `#`, `*` and `_` all go to the same element parser. | `Parser.java`:179, 264-267 |
  | pdn-aprs | `!!`, `#`, `*` and `$ULTW` are raw weather, reported as obsolete; content must be printable ASCII. | `decode.rs`:28, 42-44; `raw_weather`, other.rs:19 |

- **Corpus.** For `!` and `$` packets, the distribution of the first
  bytes after the DTI, and how many `!!` and `$ULTW` fields contain bytes
  other than hex digits and `'-'`.

<a id="amb.wx.status"></a>
### amb.wx.status

- **Open.** Raw and positionless reports are "not recommended" (p. 82/62,
  p. 83/63), not obsolete. UAP 5.19 calls the vendor format obsolete.
- **Readings.** (a) Report `obsolete`. (b) Report nothing. (c) Report
  `discouraged`.
- **Taken.** **[agreed]** (c): a `discouraged` finding at offset 0 of
  every raw and positionless report, given by the `dti` rules of
  [01-frame.md](01-frame.md#7-data-type-identifier), as
  [README section 3](README.md#3-tokenizer-model) assigns that kind to
  forms that are only "not recommended". An earlier draft took (a),
  since `obsolete` does not change the verdict; it was dropped because
  `obsolete` is kept for forms the document marks obsolete. A later
  draft took (b), for want of a fitting kind; it was dropped when the
  README added `discouraged`. This is a question of which finding kind to
  use, not of how the bytes divide: no `ambiguous` finding.
- **Decoders.** pdn-aprs reports raw and positionless weather as obsolete
  (`raw_weather`, other.rs:20; `positionless_weather`, other.rs:32). Dire
  Wolf leaves a note to report it as obsolete (decode_aprs.c:345, 363).
  The others do not distinguish it.
- **Corpus.** Counts of raw and positionless weather packets by form.

<a id="amb.wx.symbol"></a>
### amb.wx.symbol

- **Open.** A complete report is "identified" by the weather symbol,
  written `/_` or `\_` (p. 82/62); `\_` takes an overlay (p. 140/116).
  Not stated: whether an overlay byte as table counts, whether every
  `'_'` report must carry weather, and what a weather-station position
  with nothing after the symbol is (p. 85/65 asks raw and positionless
  stations to send their position separately).
- **Readings.** (a) Code `'_'` with any table byte that
  [`sym.table`](02-fields.md#sym.table) accepts. (b) Only `/_` and `\_`.
  (c) Decide by content (a `g` and `t` at fixed places) rather than
  symbol.
- **Taken.** **[proposed]** (a), as most decoders do. A report whose
  information field ends at the symbol code is a plain position or
  object and gives no finding (section 2). A report with any bytes after
  the position block is weather. If those bytes are not weather data
  (for example a PHG extension and a comment), the tokenizer reports
  `syntax`, and that finding alone is given, although reading (c) would
  take the bytes as a plain position with a comment
  ([README section 3](README.md#3-tokenizer-model), precedence).
  Visible in the bytes: with an overlay or any other table byte that is
  neither `'/'` nor `'\'`, reading (b) would take bytes that (a) accepts
  as weather as a plain position or object with a comment. Such a report
  gives an `ambiguous` finding against `wx.pos` or `wx.obj` at the
  symbol table byte. With `'/'` or `'\'`, (a) and (b) agree and the
  report gives no finding.
- **Decoders.**

  | Decoder | What it does | Where |
  |---|---|---|
  | FAP | Symbol code `'_'`, any table, sends the rest to the weather parser instead of the comment parser. | `parseaprs`, FAP.pm:2624, 2641; `_object_to_decimal`, FAP.pm:1281 |
  | Dire Wolf | Symbol code `'_'`, any table, selects weather; it notes that a `'_'` report carrying PHG and text breaks the format. | `aprs_ll_pos`, decode_aprs.c:930, 974; `aprs_ll_pos_time`:1064, 1084; `aprs_object`:2175, 2193 |
  | aprslib | Symbol code `'_'`, any table. | `parse_position`, position.py:62 |
  | Xastir | Decides by content: for `/` and `@`, a `'/'`, `g` and `t` at fixed offsets; in general, `g` and `t` (and `h`) found in the data. Symbol not checked. | `decode_info_field`, db.c:15029, 15080; `extract_weather`, db.c:3335-3387 |
  | aprsc | Code `'_'` with any valid table byte, overlays included. | `pbuf_fill_pos`, parse_aprs.c:84 |
  | javAPRSlib | Code `'_'`, any table. | `Parser.java`:160, 191 |
  | pdn-aprs | Code `'_'`, any table. | `is_weather_symbol`, comment.rs:19 |

- **Corpus.** Distribution of table bytes among `'_'` reports; how many
  `'_'` reports end at the symbol, and how many have bytes after it that
  do not start with a wind field.

<a id="amb.wx.carriers"></a>
### amb.wx.carriers

- **Open.** Weather is diagrammed for position reports and uncompressed
  objects (p. 85/65, p. 86/66). Compressed objects, items and Mic-E
  reports with a `'_'` symbol are not mentioned, though the data table
  lists raw weather data under objects and items (p. 33/19).
- **Readings.** (a) Apply the weather rules to every format with a `'_'`
  symbol. (b) Only to the diagrammed carriers, plus compressed objects.
  (c) Only to the diagrammed carriers.
- **Taken.** **[proposed]** (b). Compressed objects follow from the "any
  position format" statement (p. 85/65). Items and Mic-E are read by
  their own rules, with no weather tokens.
- **In the bytes.** **[proposed]** Visible, under the test of
  [README section 3](README.md#3-tokenizer-model), in three cases, each
  given an `ambiguous` finding at the first byte after the position
  block:
  - a compressed object with symbol code `'_'` and bytes after the
    block, which this reading reads as weather and reading (c) as an
    object comment, when those bytes would be accepted as
    [`obj.cmt`](05-object-item.md#obj.cmt) with no `syntax` or `value`
    finding;
  - an item with symbol code `'_'`, which this reading reads as an item
    with a comment and reading (a) as weather, when the bytes after its
    position would be accepted as weather data and tail by sections 5
    to 7 with no `syntax` or `value` finding;
  - a Mic-E report with symbol code `'_'`, likewise, when its status
    text would be accepted as weather data and tail by sections 6 and
    7; the finding is then at offset 9, where the status text starts.

  Where this reading itself gives a `syntax` or `value` finding on those
  bytes, that finding alone is given (Precedence). An earlier draft
  called the question not visible.
- **Decoders.** FAP reads weather in objects of both kinds
  (`_object_to_decimal`, FAP.pm:1281) but not in items (FAP.pm:1484
  skips the comment and calls no weather parser). Dire Wolf reads weather
  in both object kinds (`aprs_object`, decode_aprs.c:2175, 2193) and not
  in items (`aprs_item`, decode_aprs.c:2235, has no call to
  `weather_data`). aprslib reads objects through `parse_position`
  (position.py:62) and does not parse items (`)` is in its unsupported
  list, parsing/\_\_init\_\_.py:53). Xastir runs its weather extraction
  on `!` and `=` positions and Mic-E reports (db.c:9526-9552), objects
  (db.c:9872) and items (db.c:9993) alike.
- **Corpus.** Counts of `'_'` symbol use by format (object compressed,
  item, Mic-E).

<a id="amb.wx.order"></a>
### amb.wx.order

- **Open.** The weather data must contain at least wind direction, wind
  speed, gust and temperature, and "the remaining" may come in another
  order (p. 84/64). Not stated: whether the four lead and in that order,
  whether an element may repeat, and which `'s'` is snowfall, since
  snowfall uses the wind-speed letter (p. 84/64).
- **Readings.** (a) The required elements lead in the order of the
  diagram; the rest in any order; an `'s'` after the leading elements is
  snowfall. (b) All elements in any order; the first `'s'` is wind speed.
  (c) As (a) with no repetition.
- **Taken.** **[proposed]** (a), with a repeated element tokenized and
  given `unstated` (section 6.2). Only the positionless report has
  required elements ([amb.wx.required](#amb.wx.required)), so in a
  complete report no element leads, and every `'s'` is snowfall. A
  required element missing from its place gives `syntax`, and that
  finding alone is given, although (b) would accept the bytes
  ([README section 3](README.md#3-tokenizer-model), precedence).
  Otherwise the order is decided silently, with no `ambiguous` finding.
  A repeated element is visible in the bytes; since no listed reading
  accepts those bytes with a different division, it is reported as
  `unstated` rather than `ambiguous`.
- **Decoders.**

  | Decoder | What it does | Where |
  |---|---|---|
  | FAP | Requires wind then `g`, `t` at the start, with fallbacks for missing `g` or `t`; then removes each other element wherever it is found, first match only, so order is free and repeats are left over. Any `'s'` after the start is snowfall. | `_wx_parse`, FAP.pm:2119-2129, 2175 |
  | Dire Wolf | Wind, then `g`, then `t` at fixed places; then any order in a loop, which accepts repeats. An `'s'` in the loop is snowfall. | `weather_data`, decode_aprs.c:3075-3144, 3164-3260 |
  | aprslib | Turns a leading `ddd/sss` into `c`/`s`, then treats the first `'s'` anywhere as wind speed; any order. | `parse_weather_data`, weather.py:48-52 |
  | Xastir | Searches each letter anywhere and removes the first match; snowfall only after a wind speed was found. | `extract_weather`, db.c:3486; `extract_weather_item`, db.c:3155 |
  | javAPRSlib | Matches each letter anywhere in the rest of the packet. | `parseWeatherData`, WeatherParser.java:90-146 |
  | pdn-aprs | Any order; stops at a field already read; snowfall is an `'s'` once the wind speed is known. | `fields`, weather.rs:44 |

- **Corpus.** Observed sequences of element letters; how often a letter
  repeats; where `'s'` appears relative to `t`.

<a id="amb.wx.required"></a>
### amb.wx.required

- **Open.** The minimum-content note asks for the 8-digit timestamp and
  the `c`, `s`, `g` and `t` elements (p. 84/64). That list fits only the
  positionless report; in APRS 1.0.1 the note sat under the positionless
  section (1.0.1 PDF 74), and 12b retitled that section so that it reads
  as covering every report. For complete reports the wind field
  replaces `c` and `s` (p. 85/65), but whether `g` and `t` are still
  required is not stated. One weather object example has no `t`
  (p. 86/66; [err.wx.object-baro](#err.wx.object-baro)).
- **Readings.** (a) The note applies to all forms, with the wind field
  for `c` and `s`; `g` and `t` are required. (b) The note applies only to
  positionless reports, where APRS 1.0.1 placed it; in complete reports
  only the wind is required.
- **Taken.** **[agreed]** (b). In a positionless report a missing `c`,
  `s`, `g` or `t` gives `syntax`. In a complete report `g` and `t` are
  optional elements (section 6.2). An earlier draft took (a), which made
  a missing `g` or `t` in a complete report a `syntax` finding; it was
  dropped because the note's list, with its 8-digit timestamp and its
  `c` and `s`, fits only the positionless form. Where (b) gives `syntax`
  for a positionless report, (a) does too; the readings differ only in
  complete reports, where (b) accepts more. Not visible; no `ambiguous`
  finding.
- **Decoders.** Dire Wolf reports a missing gust or temperature and goes
  on (`weather_data`, decode_aprs.c:3130-3157). pdn-aprs treats a
  complete report without `g` and `t` as a defect (`fields`,
  weather.rs:108). Xastir requires `g` and `t` to recognise weather at all
  (`extract_weather`, db.c:3285-3389). FAP accepts a start with only one of them
  (FAP.pm:2123-2129). aprslib requires all four only for positionless
  (weather.py:66).
- **Corpus.** Share of `'_'` reports with a wind field whose next
  elements are not `g` then `t`.

<a id="amb.wx.unknown"></a>
### amb.wx.unknown

- **Open.** A value that is not known can be sent as dots or as spaces
  in place of the digits (p. 84/64). Not stated: whether one value may
  mix dots, spaces and digits, and whether an unknown element may be
  left out instead.
  The document's own example on p. 85/65 has a gap inside a dotted value
  ([err.wx.unknown-example](#err.wx.unknown-example)).
- **Readings.** (a) A value is all digits (with the sign and decimal
  point allowed for its element), all dots or all spaces. (b) Any mix.
- **Taken.** **[proposed]** (a); a mix gives `syntax`, since the value
  then does not start an element and ends the data. That finding alone
  is given, although (b) would accept the bytes
  ([README section 3](README.md#3-tokenizer-model), precedence). Leaving
  out an optional element is allowed; leaving out a required one is
  [amb.wx.required](#amb.wx.required). Where (a) accepts the bytes, (b)
  divides them the same way; no `ambiguous` finding.
- **Decoders.** Dire Wolf accepts a value that is all dots or all spaces,
  else each byte must be a digit, `'.'` or `'-'` (`getwdata`,
  decode_aprs.c:3043-3052). Xastir's check counts dots and spaces and
  rejects a value where they are neither none nor all
  (`is_weather_data`, db.c:3135). pdn-aprs accepts all dots or all spaces
  (`exact_value`, weather.rs:188). FAP accepts any mix of digits, spaces
  and dots in the leading elements (FAP.pm:2119). aprslib accepts any mix
  of digits, `'-'`, `'.'` and space when finding the run (weather.py:52)
  and decodes only all-digit forms (weather.py:59).
- **Corpus.** Count of weather values mixing digits, `'.'` and `SP`.

<a id="amb.wx.width"></a>
### amb.wx.width

- **Open.** Every element has a fixed width (p. 84/64), but nothing is
  said about values written with more or fewer digits (`h082`, UAP 5.31;
  `b0990`, p. 86/66). The sentence that permits a decimal point in a
  value that is not a whole number sits after the snowfall entry and may
  cover only snowfall or every value (p. 84/64).
- **Readings.** (a) Fixed width; a different width breaks the element.
  (b) A digit run of any length per element. (c) Decimal point only in
  snowfall. (d) Decimal point in any value.
- **Taken.** **[proposed]** (a) and (c). The extra digit of an over-long
  value cannot start an element, so the data ends there and the rest
  fails the tail: `syntax`. The README rule that an over-long field gives
  `value` applies to delimited fields; these have no delimiter, so the
  excess cannot be attributed to the element. The rendered page puts the
  decimal-point sentence in the description column of the snowfall entry
  (p. 84/64). A value of another width, or a decimal point outside
  snowfall, gives that `syntax` finding alone, although (b) or (d) would
  accept the bytes ([README section 3](README.md#3-tokenizer-model),
  precedence). Where (a) and (c) accept the bytes, (b) and (d) divide
  them the same way; no `ambiguous` finding.
- **Decoders.** FAP takes any run of digits, spaces and dots for `g` and
  `t` at the start (FAP.pm:2119), 1-3 digits for `r`, `p`, `P`, `h`, `L`,
  `l` and `s`, and 4-5 for `b` (FAP.pm:2146-2175). Dire Wolf uses fixed
  widths and accepts `'.'` and `'-'` in any value (`getwdata`,
  decode_aprs.c:3049-3054). pdn-aprs uses fixed widths and tolerates, as
  a reported defect, a run from 1 byte up to one more than the width
  (`value`, weather.rs:136-184); it allows a decimal point only in
  snowfall (`exact_value`, weather.rs:198). Xastir uses fixed widths
  (`extract_weather_item`, db.c:3155). aprslib uses fixed widths and
  decodes a decimal point only in snowfall (weather.py:59).
- **Corpus.** Length of the digit run after each element letter; `'.'`
  inside values other than snowfall.

<a id="amb.wx.rawrain"></a>
### amb.wx.rawrain

- **Open.** The raw rain counter `'#'` has no stated width (p. 84/64). The
  luminosity entry says that `L` takes the place of a rain element, but
  not which one, nor whether that rain element is then absent
  (p. 84/64).
- **Readings.** (a) `'#'` takes 3 digits like the others. (b) A digit run
  of any length. (c) `L` replaces a rain element, so the two do not
  occur together. (d) `L` is an ordinary optional element.
- **Taken.** **[proposed]** (a), with an `unstated` finding on every
  `wx.rawrain`, since its width is this reading's and not the
  document's; and (d). Neither is visible as an alternative: where (a)
  matches, (b) splits the bytes the same way, and (c) only rejects
  packets that (d) accepts. A digit run longer than 3 after `'#'` ends
  the data, and the `syntax` finding that follows is the only one,
  although (b) would accept the bytes
  ([README section 3](README.md#3-tokenizer-model), precedence). No
  `ambiguous` finding.
- **Decoders.** Xastir reads `'#'` with 3 bytes (db.c:3493). aprslib and
  pdn-aprs give it 3 (weather.py:52; weather.rs:62). FAP takes any digit
  run (FAP.pm:2180). Dire Wolf's branch meant for `'#'` tests for `'s'`
  again, so it never reads `'#'` (decode_aprs.c:3250). All of them read
  `L` alongside rain elements.
- **Corpus.** Digit-run lengths after `'#'`; co-occurrence of `L` or `l`
  with `r`, `p` and `P`.

<a id="amb.wx.tail"></a>
### amb.wx.tail

- **Open.** The software code (1 byte) and the unit code (2-4 bytes)
  follow the data with no separator (p. 83/63), so `wRSW` can be `w` +
  `RSW` or a 4-byte unit, and `Jim` (p. 84/64) a 3-byte unit or `J` +
  `im`. Software code `P` is also the rain-since-midnight letter. Whether
  software bytes outside the list are allowed is not stated.
- **Readings.** (a) Split by length and by the listed codes, as in
  section 7. (b) The first byte is always the software code when the tail
  is 3-5 bytes. (c) The whole tail is the unit when it is 2-4 bytes.
- **Taken.** **[proposed]** (a). With no 1-byte unit code
  ([err.wx.unit-length](#err.wx.unit-length)), tails of 1, 2 and 5 bytes
  split only one way. Visible in the bytes: a tail of 3 or 4 bytes whose
  first byte is a letter splits two ways, as software code and unit or
  as one unit, and readings (b) and (c) each take one of them. Such a
  tail gives an `ambiguous` finding against `wx.sw` at its first byte,
  also where the listed codes decide the split for (a), as in `wRSW`.
  The order of the tests in section 7 only chooses the tokens. An
  earlier draft gave no finding where the listed codes decided the
  split; that was dropped because reading (c) still divides those bytes
  differently.
- **Decoders.** FAP keeps a tail of 3-5 letters, digits, `'-'` or `'_'` as
  one "software" string and anything else as a comment (FAP.pm:2188). Dire
  Wolf keeps whatever is left as text (decode_aprs.c:3293). pdn-aprs takes
  3-5 bytes, a letter then 2-4 letters, digits, `'-'` or `'_'` not all
  digits, as software + unit (`is_software_and_unit`, weather.rs:247).
  aprslib leaves it in the comment (position.py:69-72). Xastir does not
  read it; a line for a `w` element is commented out (db.c:3503).
- **Corpus.** Distribution of tails after the last element, by length
  and first byte.

<a id="amb.wx.comment"></a>
### amb.wx.comment

- **Open.** No weather diagram has a comment field (p. 83/63, p. 85/65,
  p. 86/66), but the general comment rule says any packet may carry one
  (p. 34/20). Reports with free text after the data are common enough
  that UAP 2.7.1 and 5.33 discuss them and call the text an error.
- **Readings.** (a) Bytes after the data that are not a valid tail are
  not part of the format. (b) They are a comment.
- **Taken.** **[proposed]** (a). They form a `residue` token named after
  `wx.unit` and give `syntax`. That finding alone is given, although (b)
  would accept the bytes as a comment
  ([README section 3](README.md#3-tokenizer-model), precedence). DAO,
  base-91 telemetry and altitude are not looked for in weather reports.
- **Decoders.** FAP, Dire Wolf, aprslib and pdn-aprs keep the bytes as a
  comment (FAP.pm:2188-2191; decode_aprs.c:3293; position.py:70-71;
  `weather_tail`, comment.rs:161, which first lifts base-91 telemetry and
  a DAO out of it and reports the text as a defect).
- **Corpus.** Length distribution of bytes left after the last element
  in `'_'` reports.

<a id="amb.wx.cmpwind"></a>
### amb.wx.cmpwind

- **Open.** In a compressed weather report the `cs` bytes carry the wind
  (p. 86/66). The compression type byte can also say that `cs` holds an
  altitude, and the first `cs` byte can mark a radio range (see 02). What
  a weather report means by that is not stated.
- **Readings.** (a) Tokenize the block by 02 and accept whatever `cs`
  holds. (b) Require `cs` to be course and speed.
- **Taken.** **[proposed]** (a), with an `unstated` finding against
  [`cmp.cs`](02-fields.md#cmp.cs) when, by 02, it is not course and speed.
  Not visible as an alternative: both readings divide the block the same
  way and differ only in whether such a block is accepted. Decided
  silently; no `ambiguous` finding.
- **Decoders.** Dire Wolf takes the wind from the decoded course and
  speed of the block (`weather_data`, decode_aprs.c:3091, 3110). Xastir
  copies the course and speed decoded from the block once it has found
  `g` and `t`, at fixed places or anywhere (`extract_weather`,
  db.c:3285-3323). FAP and aprslib decode the block as for any position;
  not checked further.
- **Corpus.** Distribution of `cs` kinds (course/speed, range, altitude)
  among compressed `'_'` reports.

<a id="amb.wx.letters"></a>
### amb.wx.letters

- **Open.** Only the letters of section 6.1 are defined (p. 84/64). UAP
  2.7.1 advises receivers to ignore unknown letter-and-digits pairs.
- **Readings.** (a) An undefined letter ends the data. (b) An undefined
  letter followed by digits is an extra element.
- **Taken.** **[proposed]** (a). Extra elements are a matter for a
  deviation recogniser (README section 3). The bytes from the undefined
  letter on are read as a tail (section 7) or fail as one
  ([amb.wx.comment](#amb.wx.comment)); a `syntax` finding there is the
  only one given, although (b) would accept the bytes
  ([README section 3](README.md#3-tokenizer-model), precedence). Where
  they form a valid tail, any `ambiguous` finding is that of
  [amb.wx.tail](#amb.wx.tail).
- **Decoders.** Dire Wolf reads an `X` element (decode_aprs.c:3260).
  Xastir reads `F` and `f` (db.c:3495-3497). FAP strips a `v` element
  (FAP.pm:2171). pdn-aprs keeps any undefined letter followed by digits as
  an extra field (`fields`, weather.rs:91-103).
- **Corpus.** Letters, other than the defined ones, followed by digits
  inside weather data.

<a id="amb.storm.placement"></a>
### amb.storm.placement

- **Open.** Storm data begins with the direction/speed in the extension
  slot and continues where the comment would be (p. 87/67, p. 33/19). Not
  stated: whether the `'@'` symbol is required to read it, an overlay on
  that symbol, the byte set of the storm type, an unknown fill, units of
  the direction and speed, what may follow, and how a storm's `/TS` is
  told from other comment data beginning with `'/'`.
- **Readings.** (a) Read storm data only with symbol code `'@'`, after an
  uncompressed position and a course/speed extension, and only when the
  type is one of the three. (b) Read the pattern after any course/speed
  extension. (c) Search for `/TS`, `/HC`, `/TD` anywhere.
- **Taken.** **[proposed]** (a), as in section 8. Bytes after the storm
  fields are the comment.
- **In the bytes.** **[proposed]** Visible, under the test of
  [README section 3](README.md#3-tokenizer-model), where reading (b) or
  (c) would read storm data in bytes that this reading leaves as
  comment: a `/TS`, `/HC` or `/TD` followed by every required storm
  field of section 8 with no `syntax` finding, either directly after an
  `ext.csespd` in a report whose symbol code is not `'@'` (reading (b)),
  or anywhere else in a comment (reading (c)). Those bytes stay comment
  text with an `ambiguous` finding at the `'/'` of the storm type. A
  `/TS`, `/HC` or `/TD` that is not followed by the required fields gives
  no finding, since (b) and (c) would fail there. An earlier draft
  called the question not visible.
- **Decoders.**

  | Decoder | What it does | Where |
  |---|---|---|
  | FAP | Does not parse this. | - |
  | Dire Wolf | Does not parse this. | - |
  | aprslib | Does not parse this. | - |
  | Xastir | Searches the data for `/TS`, `/TD`, `/HC` and three further types (`/TY`, `/ST`, `/SC`), then reads the 7 bytes before it as course/speed; no symbol check. | `extract_storm`, db.c:3567, 3606 |
  | aprsc | Marks `'@'` with any valid table as weather. | `pbuf_fill_pos`, parse_aprs.c:86 |
  | pdn-aprs | Symbol code `'@'`, any table; storm fields after the extension; the `%` field optional; all dots or spaces accepted as unknown. | `is_storm_symbol`, comment.rs:32; `storm`, comment.rs:479 |

  In javAPRSlib and ebarkie/aprs a search of the files read found no
  storm-data parser.
- **Corpus.** Among `'@'` reports, how many match the storm sequence;
  how many reports with another symbol contain `/TS`, `/HC` or `/TD`
  after a course/speed extension.

## 10. Errata

<a id="err.wx.object-dti"></a>
### err.wx.object-dti

The Appendix 1 diagram of the weather object shows `'*'` as the data type
identifier (p. 134/110); chapter 12 shows `';'` (p. 86/66), as do all
object diagrams. The reading follows p. 86/66: a weather object starts
with `';'` and is read by 5.3, and a field starting `'*'` is the Peet
Bros form [`wx.raw.peet`](#wx.raw.peet), as the dispatch of
[01-frame.md](01-frame.md#7-data-type-identifier) has it
([err.dti.star](01-frame.md#err.dti.star) points here).

Origin: already in APRS 1.0.1, which has `';'` in the chapter diagram
(1.0.1 PDF 76) and `'*'` in the Appendix 1 copy (1.0.1 PDF 109). 12b
has both unchanged (12b PDF 88, 139).

<a id="err.wx.object-time"></a>
### err.wx.object-time

The first weather object example on p. 86/66 has no timestamp, although
the diagram on the same page gives the timestamp column 7 bytes and does
not shade it as optional. The reading follows the diagram; the example
gives `syntax`.

Origin: already in APRS 1.0.1, with the same diagram and example
(1.0.1 PDF 76). 12b has it (12b PDF 88).

<a id="err.wx.object-baro"></a>
### err.wx.object-baro

The second weather object example on p. 86/66 ends with `b0990`: four
digits where the pressure takes five. The reading follows the element
widths; under section 7 the bytes `b0990` become a 5-byte tail, software
code `b` with an `unstated` finding and unit `0990`. The example also
has no `t` element, which a complete report does not require
([amb.wx.required](#amb.wx.required)).

Origin: already in APRS 1.0.1 (1.0.1 PDF 76). 12b has it (12b PDF 88).

<a id="err.wx.cmp-example"></a>
### err.wx.cmp-example

The compressed weather example without timestamp on p. 86/66 has 14
bytes between the DTI and the weather data where the compressed block
has 13: a `'>'` sits before the `'_'` symbol code. The timestamped
example on the same page has 13. The reading follows the diagram. Dire
Wolf's source comment lists the same example without the `'>'`
(`weather_data` header, decode_aprs.c:3020, read).

Origin: already in APRS 1.0.1, whose example has the same extra `'>'`
(1.0.1 PDF 76). 12b has it (12b PDF 88).

<a id="err.wx.unknown-example"></a>
### err.wx.unknown-example

The second example on p. 85/65 shows the pressure as `b` followed by a
dot, a gap and three dots; the text layer of the PDF has `'.'`, `SP`,
`'.'`, `'.'`, `'.'`. Read literally it mixes dots and spaces
([amb.wx.unknown](#amb.wx.unknown)). The reading takes it as five dots, a
typesetting gap; Dire Wolf's source comment quotes the same example with
five dots (`weather_data` header, decode_aprs.c:3018, read).

Origin: introduced by the 12b/12c compilation. APRS 1.0.1 has five dots
with no gap (1.0.1 PDF 75, text layer and Markdown extraction); 12b
already has the gap (12b PDF 87).

<a id="err.wx.software-case"></a>
### err.wx.software-case

The list of software codes has upper-case `W` for WinAPRS (p. 83/63),
but every example uses lower-case `w` (`wRSW`, p. 83/63 to p. 86/66),
which UAP 2.7.1 also reads as WinAPRS. The reading follows the examples
and adds `w` to the listed set.

Origin: already in APRS 1.0.1, which lists `W` and writes `wRSW` in its
examples (1.0.1 PDF 73, 75, 76). 12b has it (12b PDF 85).

<a id="err.wx.unit-length"></a>
### err.wx.unit-length

The unit code is said to be 2-4 bytes, but the unit list ends with the
1-byte codes `O` (Otracker), `K` (Kenwood), `B` (Byonics) and `Y`
(Yaesu) (p. 83/63). The APRS 1.1 weather note
(`aprs.org/aprs11/spec-wx.txt`, read through a Wayback Machine snapshot
of 2023, lines 119-121) assigns these four letters as new software type
identifiers; its sentence announces two but names four. **[agreed]** The
reading follows the note and the stated length: `O`, `K`, `B` and `Y`
are software codes (section 7), and a unit code has 2-4 bytes.

Origin: introduced by the 12b/12c compilation, which placed the four
software codes in the unit list. The APRS 1.0.1 unit list has only codes
of 2-4 bytes (1.0.1 PDF 73); 12b already appends the four to it (12b
PDF 85).

<a id="err.wx.wind-units"></a>
### err.wx.wind-units

The wind field after a weather symbol is the `DIR/SPD` extension, whose
speed is in knots (p. 45/27). The weather element `s` is in miles per
hour (p. 84/64), and p. 85/65 says the extension replaces it. The
tokenizer computes no values, so the tokens are unaffected. For the
decoding layer the unit is **[open]**: Dire Wolf and Xastir convert from
knots (decode_aprs.c:3087; db.c:3435), FAP and pdn-aprs treat it as miles
per hour (FAP.pm:2143; comment.rs:90), and aprslib reports it as a course
and speed in knots (common.py:148). UAP 2.7.1 says knots.

Origin: already in APRS 1.0.1, which states all three: knots for the
extension (1.0.1 PDF 37), miles per hour for `s` (1.0.1 PDF 74) and the
replacement (1.0.1 PDF 75). 12b has them unchanged (12b PDF 47, 86, 87).

## 11. Open items

- The unit of the wind speed for the decoding layer
  ([err.wx.wind-units](#err.wx.wind-units)).
- The storm types other than `TS`, `HC` and `TD` read by Xastir, and the
  storm fields' unknown fill, are not in APRS12c; whether a deviation
  recogniser covers them.
- The corpus questions of section 9.
