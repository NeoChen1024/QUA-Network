# Weather body

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Record | [01-record.md](01-record.md): envelope, modes, value objects, position body. [02-object.md](02-object.md): object body. |
| Values | [docs/legacy/12-values-weather.md](../legacy/12-values-weather.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the weather body of a record. The decoder gives it for
a positionless weather report and for a complete weather report. The
conventions of [01-record](01-record.md) apply: the modes, the value
objects, the provenance and the notes.

## 2. Uses

**[agreed]** A weather report with a position has the uses `position` and
`weather`. The position body is that of
[01-record section 7](01-record.md#7-position-body).

**[proposed]** The table gives `uses` for each format:

| Format | `format` | `uses` |
|---|---|---|
| Complete report in a position report | `wx.pos` | `["position", "weather"]` |
| Complete report on an Object | `wx.obj` | `["object", "position", "weather"]` |
| Complete report on an Item | `item.dti` | `["object", "position", "weather"]` |
| Positionless report | `wx.pl` | `["weather"]` |

**[proposed]** An Item is a weather report if both conditions are true
([05 section 7](../legacy/05-object-item.md#7-weather-and-storm-data-on-objects)):

- its symbol code is `'_'`;
- at least one byte follows its position.

A raw weather report has no body.

## 3. Fields

**[proposed]** The weather body has these fields. Each value comes from
the value rule in the last column.

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `wind_direction` | Quantity | Degrees clockwise from north. | `val.wx.wind`, `val.cmp.wind`, `val.wx.wdir` |
| `wind_speed` | Quantity | Metres per second. | `val.wx.wind`, `val.cmp.wind`, `val.wx.wspd` |
| `gust` | Quantity | Metres per second. | `val.wx.gust` |
| `temperature` | Quantity | Kelvin. | `val.wx.temp` |
| `rain_1h` | Quantity | Rain in the last hour, in metres. | `val.wx.rain1h` |
| `rain_24h` | Quantity | Rain in the last 24 hours, in metres. | `val.wx.rain24h` |
| `rain_midnight` | Quantity | Rain since midnight, in metres. | `val.wx.rainmid` |
| `snow_24h` | Quantity | Snowfall in the last 24 hours, in metres. | `val.wx.snow` |
| `humidity` | Quantity | Percent. | `val.wx.hum` |
| `pressure` | Quantity | Pascal. | `val.wx.baro` |
| `luminosity` | Quantity | Watts per square metre. | `val.wx.lum` |
| `software` | Code | The software code, as a byte string of one byte. | `val.wx.sw` |
| `unit` | Bytes | The unit code. | `val.wx.unit` |
| `comment` | Bytes | Only in a record with no position body: the bytes of the `cmt.text` token. | — |

**[proposed]** The record leaves out a field that has no token in the
packet. These cases give a no-value object:

- The value of the field is unknown fill. `why` is `["unknown"]`.
- **[agreed]** The wind field is `000/000`. `wind_direction` has the
  `why` `["amb.val.calm"]`. `wind_speed` has the effect `computable`: in
  strict mode it has the same `why`, and in permissive mode it is 0, with
  the mark `["amb.val.calm"]`.
- The wind field has the direction 0 and a speed. `wind_direction` has
  the `why` `["amb.val.wdir0"]`.
- A required field is missing: the wind field of an uncompressed complete
  report, or `c`, `s`, `g` or `t` of a positionless report. `why` gives
  the `syntax` finding. If the complete report has a `c` or an `s` field
  at the start of its data, that field gives the wind
  ([amb.wx.leading](../legacy/06-weather.md#amb.wx.leading)).
- A finding has the effect `none`, or `computable` in strict mode
  ([12-values-weather section 6](../legacy/12-values-weather.md#6-effect-of-findings)).

**[proposed]** If a field occurs more than once, the field has the effect
`computable`. In permissive mode, the field has the number of the first
token, with a mark. `from` lists every token of the field.

**[proposed]** In a record with a position body, the comment after the
weather data is the `comment` of the position body. Thus the comment of a
packet has one place for every format that has a position.

**[proposed]** The position body of a weather report has no `course` and
no `speed`. The wind field takes their place in the packet.

### 3.1 Units

**[agreed]** The wind speed and the gust are in metres per second. The
temperature is in kelvin. Rain and snowfall are in metres. The pressure is
in pascal. The luminosity is in watts per square metre.

**[agreed]** Humidity is in percent. This is one more exception to the SI
units of [01-record section 4.3](01-record.md#43-units).

**[agreed]** The speed of the wind field is in knots before the
conversion
([12-values-weather section 4](../legacy/12-values-weather.md#4-wind)).
A `wind_speed` from the wind field or from a compressed block has the
note `err.wx.wind-units`.

**[proposed]** `n` is the count and `w` is the step of 12-values-weather.
For a value with a `'.'`, both are at the scale of the value: `n` / 10^`f`
and 1 / 10^`f`. The record computes `v` and `res` with this table:

| Unit of 12-values-weather | Record unit | `v` | `res` |
|---|---|---|---|
| degree | degree | `n` | `w` |
| knot | metre per second | `n` · 1852 / 3600 | `w` · 1852 / 3600 |
| 1.08^`k` − 1 knots (compressed wind) | metre per second | (1.08^`k` − 1) · 1852 / 3600 | 0.08 · 1.08^`k` · 1852 / 3600 |
| mile per hour | metre per second | `n` · 0.44704 | `w` · 0.44704 |
| degree Fahrenheit | kelvin | (`n` + 459.67) · 5 / 9 | `w` · 5 / 9 |
| hundredth of an inch | metre | `n` · 0.000254 | `w` · 0.000254 |
| inch | metre | `n` · 0.0254 | `w` · 0.0254 |
| percent | percent | `n` | `w` |
| tenth of a hectopascal | pascal | `n` · 10 | `w` · 10 |
| watt per square metre | watt per square metre | `n` | `w` |

**[proposed]** The factors come from these sources:

- Mile per hour: the units conversion table of APRS12c gives 0.44704 m/s
  (p. 149/125).
- Degree Fahrenheit: APRS12c gives C = (F − 32) · 5 / 9 (p. 149/125). The
  kelvin is the degree Celsius plus 273.15, by the definition of the SI.
  Thus K = (F + 459.67) · 5 / 9 (derived).
- Inch: the table of APRS12c gives the foot as 0.3048 m. An inch is 1/12
  foot, that is 0.0254 m (derived).

### 3.2 Notes

**[proposed]** The decoder gives these notes for the weather body:

| Row | Field | Condition |
|---|---|---|
| `err.wx.wind-units` | `wind_speed` | A value from `ext.dirspd` or from `cmp.cs.wind`. |
| `amb.val.wdir0` | `wind_direction` | A value 0 from a `c` field or from `cmp.cs.wind`. |
| `amb.val.midnight` | `rain_midnight` | Always. |
| `amb.val.baroref` | `pressure` | Always. |
| `amb.wx.tail` | `software`, `unit` | Always. |
| `amb.val.mdhmyear` | `report_time` | A `utc` from an MDHM timestamp. |

## 4. Report time

**[proposed]** The `report_time` of a positionless report has the form
`"mdhm"`. Its members are `month`, `day`, `hour`, `minute` and `zone`
([val.time.mdhm](../legacy/12-values-weather.md#val.time.mdhm)). The zone
is `"utc"`. `res` is 60.

**[proposed]** APRS12c gives no year for this timestamp
([amb.val.mdhmyear](../legacy/12-values-weather.md#amb.val.mdhmyear)). The
decoder finds `utc` as follows:

1. The candidates are the date and time in three years. These are the
   year of the received time, the year before and the year after. The
   decoder leaves out a candidate on a day that the month does not have.
2. The decoder takes the candidate nearest to the received time. If two
   are equally near, it takes the earlier candidate.

This rule follows the rule of
[01-record section 6](01-record.md#6-report-time) for DHM and HMS. If
there is no received time, `utc` is absent.

**[proposed]** A complete report has the report time of its position
report or of its Object. A `syntax` finding on that timestamp concerns
every field of the weather body, as it concerns the position body.

## 5. Example

The line is the first example of a complete weather report of APRS12c,
p. 85/65. The record is in strict mode. The input gives no received time.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001:!4903.50N/07201.75W_220/004g005t077r000p000P000h50b09900wRSW",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["position", "weather"], "format": "wx.pos", "verdict": "conform", "findings": [],
 "position": {
  "lat": {"v": 49.05833333333333, "res": 0.00016666666666666666, "from": [["lat", 15, 23]]},
  "lon": {"v": -72.02916666666667, "res": 0.00016666666666666666, "from": [["lon", 24, 33], ["lat", 15, 23]]},
  "ambiguity": {"code": 0, "from": [["lat", 15, 23]]},
  "datum": {"code": "default", "from": []},
  "symbol": {"chars": "/_", "classic": 62, "from": [["sym.table", 23, 24], ["sym.code", 33, 34]]},
  "messaging": {"flag": false, "from": [["wx.pos", 14, 15]]},
  "extensions": []},
 "weather": {
  "wind_direction": {"v": 220, "res": 1, "from": [["ext.dirspd", 34, 41]]},
  "wind_speed": {"v": 2.057777777777778, "res": 0.5144444444444445, "from": [["ext.dirspd", 34, 41]]},
  "gust": {"v": 2.2352, "res": 0.44704, "from": [["wx.gust", 41, 45]]},
  "temperature": {"v": 298.15, "res": 0.5555555555555556, "from": [["wx.temp", 45, 49]]},
  "rain_1h": {"v": 0, "res": 0.000254, "from": [["wx.rain1h", 49, 53]]},
  "rain_24h": {"v": 0, "res": 0.000254, "from": [["wx.rain24h", 53, 57]]},
  "rain_midnight": {"v": 0, "res": 0.000254, "from": [["wx.rainmid", 57, 61]]},
  "humidity": {"v": 50, "res": 1, "from": [["wx.hum", 61, 64]]},
  "pressure": {"v": 99000, "res": 10, "from": [["wx.baro", 64, 70]]},
  "software": {"code": "w", "from": [["wx.sw", 70, 71]]},
  "unit": {"bytes": "RSW", "from": [["wx.unit", 71, 74]]}},
 "notes": [["amb.val.datum", "position.datum"], ["err.wx.wind-units", "weather.wind_speed"],
  ["amb.val.midnight", "weather.rain_midnight"], ["amb.val.baroref", "weather.pressure"],
  ["amb.wx.tail", "weather.software"], ["amb.wx.tail", "weather.unit"]],
 "undecoded": []}
```

The values are derived as follows:

- `wind_speed`: 4 knots × 1852 / 3600 is 2.0578 m/s.
- `gust`: 5 mph × 0.44704 is 2.2352 m/s.
- `temperature`: (77 + 459.67) × 5 / 9 is 298.15 K, that is 25 °C.
- `pressure`: 9900 tenths of a hectopascal is 99000 Pa.
- `classic`: the code `'_'` is 0x5F. In the primary table, the number is
  0x5F − 33 = 62.

## 6. Open items

- **[open]** The place of the comment. This file puts it in the position
  body if the record has one. Another option is one comment field in the
  envelope for every format.
- **[open]** The values of storm data and of raw weather reports.
