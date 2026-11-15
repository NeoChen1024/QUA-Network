# Values of weather fields

| | |
|---|---|
| Status | Draft. Not frozen. A paragraph, value rule or catalogue row of this file is **[proposed]** if it has no other label. An **[agreed]** item is a decision of the author. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of a weather report give values. It
covers these formats:

- the positionless report
  ([06 section 4](06-weather.md#4-positionless-weather-report));
- complete reports in a position report, an Object or an Item
  ([06 section 5](06-weather.md#5-complete-weather-reports)).

The tokens come from [06](06-weather.md) and [02](02-fields.md). This file
adds no token and changes no finding. The rule prefix is `val`.

A complete report has a position. The value rules of
[10-values](10-values.md) give the values of its position tokens. A
weather report on an Object or an Item also has the values of
[11-values-object](11-values-object.md).

These parts are outside this file:

- raw weather reports. APRS12c does not specify their content
  ([06 section 3](06-weather.md#3-raw-weather-reports));
- storm data ([06 section 8](06-weather.md#8-storm-data));
- the raw rain counter `#`, which is not a token
  ([amb.wx.rawrain](06-weather.md#amb.wx.rawrain)).

## 2. Conventions

The conventions of [10-values section 2](10-values.md#2-conventions) apply
to this file. These are the terms, the value tables, the findings that
concern a value, and the effects.

### 2.1 Numbers of a weather field

A weather field is one letter and a value of fixed width
([06 section 6.1](06-weather.md#61-elements)). The value has one of three
forms. Each form gives a number as follows:

- Digits only: the decimal number `n`. The scale is one unit.
- Digits with one `'.'`: `n` is the decimal number of the digits without
  the `'.'`. `f` is the number of digits after the `'.'`. The scale is
  10^−`f` units. For example, `1.5` gives `n` = 15 at the scale 0.1.
- Unknown fill, `'.'` and `SP` only: the value is unknown. The decoder
  gives no value.

The step is 1 count in each form. A temperature can start with `'-'`.
Then `n` is negative.

### 2.2 Fields with more than one token

A report can contain a weather field more than once. The tokenizer then
gives `unstated` on each repeated token
([amb.wx.order](06-weather.md#amb.wx.order)). A value of this file uses
every token of its field in the report. The first token gives the number.
Thus a finding on a repeated token concerns the value of the field.

In a complete report, the wind field is the first token of the wind
direction. A later `c` field is a repeated token.

## 3. Timestamp

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.time.mdhm"></a>`val.time.mdhm` | Month, day, hour, minute | [`time.mdhm`](02-fields.md#time.mdhm) | Month `10·d[0] + d[1]`. Day, hour and minute from the next three digit pairs. UTC. | Step 1 minute. Month 1–12, day 1–31, hour 0–23, minute 0–59. No year. | p. 38/22, p. 83/63 |

A positionless report always has this timestamp. APRS12c does not say
which year it has ([amb.val.mdhmyear](#amb.val.mdhmyear)).

A complete report has the timestamp of its position report or of its
Object. The value rules of
[10-values section 3](10-values.md#3-identifier-and-timestamp) and
[11-values-object section 4](11-values-object.md#4-timestamp) apply. A
`syntax` finding on that timestamp concerns every value from a later
token, the weather values included.

## 4. Wind

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.wx.wind"></a>`val.wx.wind` | Wind direction, wind speed | [`ext.dirspd`](02-fields.md#ext.dirspd) | Direction: the number of bytes 0 to 2 (section 2.1). Speed: the number of bytes 4 to 6. `000/000`: unknown ([amb.val.calm](#amb.val.calm)). A half of unknown fill: no value for that half. Direction 0 with a speed: no direction ([amb.val.wdir0](#amb.val.wdir0)). | Direction in degrees clockwise from north, above 0 up to 360. Speed in knots ([err.wx.wind-units](06-weather.md#err.wx.wind-units)). | p. 45/27, p. 85/65 |
| <a id="val.cmp.wind"></a>`val.cmp.wind` | Wind direction, wind speed | [`cmp.cs.wind`](02-fields.md#cmp.cs.wind) | Direction `4 · (b[0] − 33)`. `k = b[1] − 33`. Speed = 1.08^`k` − 1. | Direction in degrees, step 4, 0 to 356 ([amb.val.wdir0](#amb.val.wdir0)). Speed in knots, factor 1.08, `k` 0 to 91. | p. 56/38, p. 57/39, p. 86/66 |
| <a id="val.wx.wdir"></a>`val.wx.wdir` | Wind direction | [`wx.wdir`](06-weather.md#wx.wdir) | The number of the value (section 2.1). | Degrees. 0 to 360 ([amb.val.wdir0](#amb.val.wdir0)). | p. 84/64 |
| <a id="val.wx.wspd"></a>`val.wx.wspd` | Wind speed | [`wx.wspd`](06-weather.md#wx.wspd) | The number of the value. | Miles per hour. Sustained wind over one minute. | p. 84/64 |
| <a id="val.wx.gust"></a>`val.wx.gust` | Gust | [`wx.gust`](06-weather.md#wx.gust) | The number of the value. | Miles per hour. Peak wind in the last 5 minutes. | p. 84/64 |

**[agreed]** The speed of the wind field `ext.dirspd` is in knots.
APRS12c states this unit for the 7-byte wind field (p. 45/27). It states
miles per hour for the `s` field (p. 84/64), and the wind field replaces
the `c` and `s` fields in a complete report (p. 85/65). The sentence
about the replacement states no unit. Thus the statement of p. 45/27
gives the unit. The decoder gives the speed with the note
[err.wx.wind-units](06-weather.md#err.wx.wind-units).

**[agreed]** The wind field `000/000` means "unknown or not relevant"
(p. 45/27). It gives no direction. For the speed, it has the effect
`computable`, with the number 0 ([amb.val.calm](#amb.val.calm)). This
effect comes from the bytes, not from a finding.

A complete report with no wind field can have a `c` field and an `s`
field at the start of its data
([amb.wx.leading](06-weather.md#amb.wx.leading)). `val.wx.wdir` and
`val.wx.wspd` then give the wind. This speed is in miles per hour.

The compressed wind uses the arithmetic of
[val.cmp.crs](10-values.md#val.cmp.crs) and
[val.cmp.spd](10-values.md#val.cmp.spd). Its speed is in knots and has the
same note.

A report can have a compressed block whose `cs` bytes are not the wind
([amb.wx.cmpwind](06-weather.md#amb.wx.cmpwind)). Such a report has no
wind value from the block. The value rules of 10-values section 6 give
the value of its `cs` token.

## 5. Other weather fields

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.wx.temp"></a>`val.wx.temp` | Temperature | [`wx.temp`](06-weather.md#wx.temp) | The number of the value, with its sign. | Degrees Fahrenheit. −99 to 999. | p. 84/64 |
| <a id="val.wx.rain1h"></a>`val.wx.rain1h` | Rain in the last hour | [`wx.rain1h`](06-weather.md#wx.rain1h) | The number of the value. | Hundredths of an inch | p. 84/64 |
| <a id="val.wx.rain24h"></a>`val.wx.rain24h` | Rain in the last 24 hours | [`wx.rain24h`](06-weather.md#wx.rain24h) | The number of the value. | Hundredths of an inch | p. 84/64 |
| <a id="val.wx.rainmid"></a>`val.wx.rainmid` | Rain since midnight | [`wx.rainmid`](06-weather.md#wx.rainmid) | The number of the value. | Hundredths of an inch ([amb.val.midnight](#amb.val.midnight)) | p. 84/64 |
| <a id="val.wx.hum"></a>`val.wx.hum` | Humidity | [`wx.hum`](06-weather.md#wx.hum) | The bytes `00` give 100. The bytes `100` give 100 ([amb.wx.hum100](06-weather.md#amb.wx.hum100)). Any other value gives its number. | Percent. 1 to 100. | p. 84/64 |
| <a id="val.wx.baro"></a>`val.wx.baro` | Barometric pressure | [`wx.baro`](06-weather.md#wx.baro) | The number of the value. | Tenths of a hectopascal ([amb.val.baroref](#amb.val.baroref)) | p. 84/64 |
| <a id="val.wx.lum"></a>`val.wx.lum` | Luminosity | [`wx.lum`](06-weather.md#wx.lum), [`wx.lumk`](06-weather.md#wx.lumk) | `wx.lum`: the number of the value. `wx.lumk`: 1000 more than the number of the value. | Watts per square metre. `wx.lum` 0 to 999, `wx.lumk` 1000 to 1999. | p. 84/64 |
| <a id="val.wx.snow"></a>`val.wx.snow` | Snowfall in the last 24 hours | [`wx.snow`](06-weather.md#wx.snow) | The number of the value. | Inches | p. 84/64 |
| <a id="val.wx.sw"></a>`val.wx.sw` | Software code | [`wx.sw`](06-weather.md#wx.sw) | The byte. | Code | p. 83/63 |
| <a id="val.wx.unit"></a>`val.wx.unit` | Unit code | [`wx.unit`](06-weather.md#wx.unit) | The bytes. | Byte string, 1 to 4 bytes | p. 83/63 |

`wx.lum` and `wx.lumk` are tokens of one field, the luminosity. The first
of them in the report gives the value.

The tokenizer divides the bytes after the data into a software code and a
unit code ([amb.wx.tail](06-weather.md#amb.wx.tail)). The decoder gives
both codes as the tokenizer divides them, with the note `amb.wx.tail`.

A positionless report requires the fields `c`, `s`, `g` and `t`. If one
of them is missing, the tokenizer gives `syntax` and no token. The value
is then `none`.

## 6. Effect of findings

This table gives the effect of each finding that concerns a value of
sections 3 to 5. For the position tokens, the table of
[10-values section 10](10-values.md#10-effect-of-findings) applies. A
token that has no row has only findings with the effect `kept`.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `time.mdhm` | `syntax` | All | `none` |
| `time.mdhm` | `value` (a number out of range) | All | `none` |
| `ext.dirspd` | No finding: the bytes `000/000` | Direction | `none` |
| `ext.dirspd` | No finding: the bytes `000/000` | Speed | `computable`: 0 |
| `ext.dirspd` | `syntax` at offsets 0–3, or no token | Direction, speed | `none` |
| `ext.dirspd` | `syntax` at offset 4 or later | Direction | `kept` |
| `ext.dirspd` | `syntax` at offset 4 or later | Speed | `none` |
| `ext.dirspd` | `value` (direction above 360) | Direction | `none` |
| `ext.dirspd` | `value` (direction above 360) | Speed | `kept` |
| `cmp.cs.wind` | `syntax` | Direction, speed | `none` |
| `cmp.t` | `syntax` | Direction and speed of `cmp.cs.wind` | `none` |
| `cmp.t` | `value` | Direction and speed of `cmp.cs.wind` | `kept` |
| A weather field of 06 section 6.1 | `syntax` | The value of the field | `none` |
| `wx.wdir` | `value` (above 360) | Direction | `none` |
| `wx.temp` | `value` (`-00`) | Temperature | `computable`: 0 |
| A weather field of 06 section 6.1 | `unstated` (a repeated field) | The value of the field | `computable`: the number of the first token (section 2.2) |
| `wx.sw` | `unstated` (a code that is not listed) | Software code | `kept`: the list is open |
| `wx.hum` | `ambiguous` (the bytes `100`) | Humidity | `computable`: 100 |
| `wx.hum` | `ambiguous` (the bytes `100`) | The value of each weather field, `wx.sw` and `wx.unit` after that token | `computable`: the value of the field |
| `dti` | `discouraged` (positionless report) | All | `kept` |

**[agreed]** The bytes `h100` have the effect `computable` on the
humidity. In strict mode, the humidity has no value. In permissive mode,
it is 100, with a mark
([06 section 10](06-weather.md#10-reviewed-exceptions)).

**[agreed]** The same finding has the effect `computable` on each
field after the `h100` token. These bytes are fields only if `h100` is
the humidity. If not, they are text.

A `syntax` finding on `ext.dirspd` at the byte after the symbol code
means that the wind field is missing
([06 section 5.1](06-weather.md#51-uncompressed-position)). The report
then has no `ext.dirspd` token.

## 7. Catalogue

The last column of this catalogue tells what the decoder does.

| ID | Pages | What APRS12c leaves open | Class | Rule | What the decoder does |
|---|---|---|---|---|---|
| <a id="amb.val.wdir0"></a>`amb.val.wdir0` | p. 45/27, p. 56/38, p. 84/64 | The direction of the wind field is 001 to 360. Direction `000` with a speed is outside that range. APRS12c gives the `c` field no range. A compressed `c` of `'!'` gives the direction 0 by the formula. APRS12c does not say if 0 is north or unknown. | unstated | 2 | Wind field with direction 0 and a speed: no direction. A `c` field of 0 and a compressed direction 0: the value 0, with this note. |
| <a id="amb.val.mdhmyear"></a>`amb.val.mdhmyear` | p. 38/22, p. 83/63 | An MDHM timestamp has no year. APRS12c does not say which year applies. | unstated | 2 | The decoder gives the fields of the timestamp and no year under this file. A year is a choice of [docs/interop](../interop/03-weather.md#4-report-time). |
| <a id="amb.val.midnight"></a>`amb.val.midnight` | p. 84/64 | Rain "since midnight" names no time zone. | unstated | 2 | The decoder gives the value, with this note. |
| <a id="amb.val.baroref"></a>`amb.val.baroref` | p. 84/64 | APRS12c does not say if the barometric pressure is the pressure at the station or the pressure reduced to sea level. | unstated | 2 | The decoder gives the value, with this note. |
| <a id="amb.val.calm"></a>`amb.val.calm` | p. 45/27 | `000/000` in the wind field means "unknown or not relevant". A station with no wind has the same bytes. | ambiguous | 1 | **[agreed]** The decoder follows the statement of p. 45/27: no direction, and no speed under the general rules. The speed has the effect `computable`, with the number 0. |

## 8. Reviewed exceptions

None.

## 9. Open items

- The effect of `unstated` on a repeated weather field. This file gives
  `computable`, with the number of the first token.
- The effect of `value` on `wx.temp` (`-00`). This file gives
  `computable`.
- A report with both `wx.lum` and `wx.lumk`. The tokenizer gives no
  finding. This file gives the first token.
- A `syntax` finding on a missing leading field of a positionless report
  does not concern a later token of the same field, because its offset is
  not in that token (10-values section 2.3).
- Values of storm data and of raw weather reports.
