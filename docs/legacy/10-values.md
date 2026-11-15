# Values of position fields

| | |
|---|---|
| Status | Draft. Not frozen. Every paragraph, value rule and catalogue row of this file is **[proposed]**. The author has not reviewed this file. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of a position report give values. A value
is a number, a flag or a code, with the unit that APRS12c states. The file
covers these formats:

- position reports, uncompressed and compressed
  ([03 section 2](03-position.md#2-position-reports));
- the fields that DF reports share with position reports;
- Mic-E ([04](04-mic-e.md)).

The tokens come from [02](02-fields.md), [03](03-position.md) and
[04](04-mic-e.md). This file adds no token and changes no finding. The rule
prefix is `val`.

[11-values-object](11-values-object.md) gives the values of Objects and
Items. It uses the value rules of this file for their position.
[12-values-weather](12-values-weather.md) gives the values of weather
reports. [13-values-telemetry](13-values-telemetry.md) gives the values
of telemetry, the base-91 block in a comment included.
[14-values-status](14-values-status.md) gives the values of status
reports. [15-values-message](15-values-message.md) gives the values of
messages and bulletins. The area descriptor, locators,
frequencies and the symbols in the address fields are also outside this
file.

[README section 3.1](README.md#31-general-rules) states how the general
rules apply to values. This file applies them and decides nothing more.

## 2. Conventions

### 2.1 Terms

This file uses the terms of README section 2 and these terms:

| Term | Meaning |
|---|---|
| value | A number, a flag or a code that a value rule gives. |
| value rule | A row of a value table. Its ID starts with `val.`. |
| unit | The unit that APRS12c states for a value, for example the degree, the knot or the foot. |
| scale | A value is an integer count `n`. The scale is the part of the unit that one count is, for example 1/6000 degree. |
| step | The smallest difference between two values that the bytes can give, in counts. For an exponential value (section 6), the count is the exponent `k`, and the step is 1. |
| received time | The time at which the receiver got the packet. The input of the decoder can give it. |
| level | The position ambiguity level, 0 to 4 ([`lat.amb`](02-fields.md#lat.amb)). |
| effect | What a finding does to a value: `kept`, `computable` or `none` (section 2.4). |
| note | The ID of a catalogue row that applies to a value of one packet. |
| the decoder | The tool that applies this file. |

### 2.2 Value tables

Each value table has these columns:

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|

The ID is unique in this directory. The column "Tokens" names the tokens
that the value uses. The column "Arithmetic" uses this notation:

- `b[i]` is the byte at offset `i` of the token, as a number.
- `d[i]` is the digit at offset `i`, that is `b[i]` − 0x30.
- `v(t)` is the base-91 number of token `t`. Each byte gives its value
  minus 33, and the first byte is the most significant
  ([`b91.digit`](02-fields.md#b91.digit)).
- `div` and `mod` are the integer quotient and remainder.

All arithmetic of this file is on integers. Thus a value of this file has
no precision that the bytes do not carry. The record of
[docs/interop](../interop/01-record.md#43-units) converts the values to its
own units.

A latitude is positive to the north. A longitude is positive to the east.
APRS12c states this sign only for the compressed format (p. 56/38). This
file uses the same sign for all formats.

### 2.3 Findings that concern a value

A finding concerns a value if both conditions are true:

- The rule ID of the finding is the ID of a token that the value uses. The
  checks `lat.amb`, `lon.amb` and `mice.dest` count as the IDs of the tokens
  `lat`, `lon` and `dest.mice` with its children.
- The offset of the finding is inside the token or at its end.

These limits apply:

- `val.lon` uses `lat` only for its level. A finding on `lat` concerns
  `val.lon` only if its rule ID is `lat.amb`.
- **[proposed]** `val.mice.lon` uses bytes 1 to 4 of the destination only
  for the level of `val.mice.lat` (step 5 of section 7). A finding on
  bytes 1 to 4 concerns `val.mice.lon` only if it is `syntax` on
  `mice.dest`: a blank before a digit.
- **[agreed]** In a position report, a `syntax` finding on the timestamp
  concerns every value from a later token of the information field. The
  rule IDs are `time.dhm`, `time.hms` and `pos.time`. The timestamp fixes
  the offset of the later fields, so a timestamp with a wrong format can
  move them. The effect has two cases:
  - The timestamp has six digits, and the finding is at offset 6: the
    effect is `computable`.
  - All other cases: the effect is `none`.
- One finding can have more than one cause. For example, `value` on `lat`
  comes from tens of minutes 6 to 9, or from minutes at 90 degrees. The
  decoder finds the cause from the bytes of the token.
- **[proposed]** `ambiguous` on `cmt.alt` or `cmt.alt.neg` has two causes:
  several altitudes, and an overlap with another token. The tokenizer
  gives one finding for both. The decoder finds an overlap from the
  tokens at the same depth whose bytes overlap the altitude.

If a value uses a token that is missing, the value is `none`.

### 2.4 Effects

Section 10 gives an effect for each finding that concerns a value:

- `kept`: The finding does not change the value.
- `computable`: The arithmetic of this file gives a number in the range of
  the quantity. But APRS12c gives the bytes no meaning. If the number is
  outside the range of the quantity, the effect is `none`.
- `none`: The bytes give no value.

A value with no finding has the effect `kept`. If several findings concern
a value, the most severe effect applies. The order is `none`, then
`computable`, then `kept`. Under the general rules, only `kept` gives a
value. `computable` marks bytes that a reader outside these rules can still
use. [docs/interop](../interop/01-record.md) uses the
effects for its modes.

## 3. Identifier and timestamp

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.pos.dti"></a>`val.pos.dti` | Timestamp flag, messaging flag | [`pos.dti`](03-position.md#pos.dti) | Timestamp: `'/'` or `'@'`. Messaging: `'='` or `'@'`. | Two flags | p. 39/23 |
| <a id="val.mice.dti"></a>`val.mice.dti` | Fix age | [`mice.dti`](04-mic-e.md#mice.dti) | 0x60 and 0x1C: current. 0x1D: old. 0x27: old, or current from a TM-D700 ([amb.val.micefix](#amb.val.micefix)). | `current` or `old` | p. 64/46 |
| <a id="val.time.dhm"></a>`val.time.dhm` | Day, hour, minute, zone | [`time.dhm`](02-fields.md#time.dhm) | Day `10·d[0] + d[1]`. Hour `10·d[2] + d[3]`. Minute `10·d[4] + d[5]`. `'z'`: UTC. `'/'`: local time. | Step 1 minute. Day 1–31, hour 0–23, minute 0–59. No month and no year. | p. 38/22 |
| <a id="val.time.hms"></a>`val.time.hms` | Hour, minute, second | [`time.hms`](02-fields.md#time.hms) | Hour, minute and second from the three digit pairs. UTC. | Step 1 second. No date. | p. 38/22 |

If a report has no timestamp, the time of the report is the received time
(p. 39/23). The decoder uses the received time only if its input gives it.
APRS12c does not say which month, year or date a timestamp has
([amb.val.timewindow](#amb.val.timewindow)).

## 4. Uncompressed position

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.lat.amb"></a>`val.lat.amb` | Level | [`lat`](02-fields.md#lat) | The number of `SP` at offsets 6, 5, 3, 2 of `lat`, counted in that order up to the first digit. | 0 to 4 | p. 40/24 |
| <a id="val.lat"></a>`val.lat` | Latitude | `lat` | A blanked digit counts as 0. `n = s · (6000 · (10·d[0] + d[1]) + 100 · (10·d[2] + d[3]) + 10·d[5] + d[6])`. `s` is +1 for `'N'` and −1 for `'S'`. | Scale 1/6000 degree, that is 0.01 minute. Step from the level (table below). `\|n\|` up to 540000. | p. 39/23, p. 40/24 |
| <a id="val.lon"></a>`val.lon` | Longitude | [`lon`](02-fields.md#lon), `lat` | The level of `lat` covers the first *level* offsets of 7, 6, 4, 3 of `lon`. A covered byte counts as 0, also if it is a digit. A `SP` that the level does not cover gives a value only under the effect of section 10. `n = s · (6000 · (100·d[0] + 10·d[1] + d[2]) + 100 · (10·d[3] + d[4]) + 10·d[6] + d[7])`. `s` is +1 for `'E'` and −1 for `'W'`. | Scale 1/6000 degree. Step as `val.lat`. `\|n\|` up to 1080000. | p. 39/23, p. 40/24 |

| Level | Precision that APRS12c states (p. 40/24) | Step |
|---|---|---|
| 0 | 0.01 minute | 1 |
| 1 | 0.1 minute | 10 |
| 2 | 1 minute | 100 |
| 3 | 10 minutes | 1000 |
| 4 | 1 degree | 6000 |

The level of the latitude applies to the longitude (p. 40/24). The example
on that page has all digits in the longitude. It says that the hundredths
of both coordinates can have any value. Thus the decoder ignores the
covered digits of the longitude.

The magnitude of `n` is the smallest magnitude that the digits permit.
Thus `n` is the edge of the box of p. 40/24 that is nearest to the equator
or to the prime meridian. It is not the centre of the box. The step gives
the size of the blanked digits. What the blanked digits mean is open
([amb.val.ambiguity](#amb.val.ambiguity)).

The null position gives `n` = 0 for both coordinates. The decoder gives
these values, with the note [amb.lat.null](02-fields.md#amb.lat.null).

## 5. Symbol

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.sym"></a>`val.sym` | Table, overlay, code | [`sym.table`](02-fields.md#sym.table) and [`sym.code`](02-fields.md#sym.code), [`cmp.table`](02-fields.md#cmp.table) and [`cmp.code`](02-fields.md#cmp.code), or [`mice.sym.table`](04-mic-e.md#mice.sym.table) and [`mice.sym.code`](04-mic-e.md#mice.sym.code) | Table byte `'/'`: primary table, no overlay. `'\'`: alternate table, no overlay. `'0'`–`'9'` and `'A'`–`'Z'`: alternate table, with that byte as overlay. `'a'`–`'j'` in `cmp.table`: alternate table, overlay `'0'` + (`b[0]` − 0x61). Code: the byte of the code token. | Table, overlay byte or none, code `'!'`–`'~'` | p. 125/101, p. 126/102 |

The symbol in the information field has precedence over the symbol in the
destination and the symbol of the source SSID (p. 127/103). Every format of
this file has a symbol in the information field. Thus the decoder does not
read the other symbols for these formats
([amb.val.symbol](#amb.val.symbol)). The decoder gives an overlay on any
symbol of the alternate table ([amb.sym.overlay](02-fields.md#amb.sym.overlay)).

## 6. Compressed position block

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.cmp.lat"></a>`val.cmp.lat` | Latitude | [`cmp.lat`](02-fields.md#cmp.lat) | `n = 34283340 − v(cmp.lat)` | Scale 1/380926 degree. Step 1. `n` from −34283340 to 34283340. | p. 56/38 |
| <a id="val.cmp.lon"></a>`val.cmp.lon` | Longitude | [`cmp.lon`](02-fields.md#cmp.lon) | `n = v(cmp.lon) − 34283340` | Scale 1/190463 degree. Step 1. `n` from −34283340 to 34283340. | p. 56/38 |
| <a id="val.cmp.crs"></a>`val.cmp.crs` | Course | [`cmp.cs.crs`](02-fields.md#cmp.cs.crs) | `n = 4 · (b[0] − 33)` | Degrees. Step 4. 0 to 356 ([amb.val.course0](#amb.val.course0)). | p. 56/38, p. 57/39 |
| <a id="val.cmp.spd"></a>`val.cmp.spd` | Speed | `cmp.cs.crs` | `k = b[1] − 33`. Speed = 1.08^`k` − 1. | Knots. Factor 1.08. `k` 0 to 91. | p. 57/39 |
| <a id="val.cmp.rng"></a>`val.cmp.rng` | Range | [`cmp.cs.rng`](02-fields.md#cmp.cs.rng) | `k = b[1] − 33`. Range = 2 · 1.08^`k`. | "Miles" ([amb.val.miles](#amb.val.miles)). Factor 1.08. `k` 0 to 91. | p. 57/39 |
| <a id="val.cmp.alt"></a>`val.cmp.alt` | Altitude | [`cmp.cs.alt`](02-fields.md#cmp.cs.alt) | `k = 91 · (b[0] − 33) + b[1] − 33`. Altitude = 1.002^`k`. | Feet ([amb.val.altref](#amb.val.altref)). Factor 1.002. `k` 0 to 8372. | p. 58/40 |
| <a id="val.cmp.t"></a>`val.cmp.t` | Fix age, NMEA source, origin | [`cmp.t`](02-fields.md#cmp.t) | `t = b[0] − 33`. Fix age `(t div 32) mod 2`: 0 old, 1 current. Source `(t div 8) mod 4`: 0 other, 1 GLL, 2 GGA, 3 RMC. Origin `t mod 8`: a code of the table of p. 57/39. | Codes | p. 57/39 |

The products 90 × 380926 and 180 × 190463 are both 34283340 (derived).
Thus `n` of `val.cmp.lat` is 380926 times the latitude in degrees. `n` of
`val.cmp.lon` is 190463 times the longitude in degrees. The example `<*e7`
of p. 56/38 gives `n` = −13856184, that is −72.750004 degrees (derived).
APRS12c gives −72.75.

The base-91 set includes `'|'` with the value 91
([err.b91.range](02-fields.md#err.b91.range)). The decoder uses this value.
Thus `k` can be 91.

Speed, range and altitude are exponential values. Under this file, the
value is the integer `k`, with the step 1. The formula gives the quantity.
One step multiplies the quantity by the factor of the row. For example,
`7P` gives course 88 and `k` = 47, which is 36.2 knots (p. 57/39). `S]`
gives `k` = 4610, which is 10004 feet (p. 58/40).

If `c` is `SP`, the block has no course, speed, range or altitude. `T` then
has no meaning (p. 56/38, p. 57/39). The decoder gives no value for `cs`
and `T`. The compressed block has no position ambiguity.

## 7. Mic-E

[04 section 3](04-mic-e.md#3-destination-address) gives the digit or blank
and the flag of each destination byte. A byte has flag 1 if it is a
standard 1 or a custom 1. In bytes 4, 5 and 6, flag 1 means North, +100
and West.

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.mice.lat"></a>`val.mice.lat` | Latitude, level | [`mice.dest.a`](04-mic-e.md#mice.dest.a) to [`mice.dest.we`](04-mic-e.md#mice.dest.we) | The six bytes give the digits `D1` to `D6`. A blank counts as 0. `n = s · (6000 · (10·D1 + D2) + 100 · (10·D3 + D4) + 10·D5 + D6)`. `s` is +1 if byte 4 has flag 1, −1 if not. The level is the number of blanks, counted from byte 6. | As `val.lat` | p. 62/44, p. 71/53 |
| <a id="val.mice.lon"></a>`val.mice.lon` | Longitude | [`mice.lon.deg`](04-mic-e.md#mice.lon.deg), [`mice.lon.min`](04-mic-e.md#mice.lon.min), [`mice.lon.hun`](04-mic-e.md#mice.lon.hun), bytes 5 and 6 of the destination | Steps 1 to 6 below. | As `val.lon`. Degrees 0 to 179. | p. 65/47 to p. 67/49, p. 71/53, p. 72/54 |
| <a id="val.mice.spd"></a>`val.mice.spd` | Speed | [`mice.sp`](04-mic-e.md#mice.sp), [`mice.dc`](04-mic-e.md#mice.dc) | `S = 10 · (b(sp) − 28) + (b(dc) − 28) div 10`. If `S` ≥ 800, subtract 800. | Knots. Step 1. 0 to 799. | p. 67/49, p. 70/52 |
| <a id="val.mice.crs"></a>`val.mice.crs` | Course | `mice.dc`, [`mice.se`](04-mic-e.md#mice.se) | `C = 100 · ((b(dc) − 28) mod 10) + b(se) − 28`. If `C` ≥ 400, subtract 400. `C` = 0 is an unknown course: no value. | Degrees. Step 1. 1 to 360. 360 is north. | p. 67/49, p. 70/52 |
| <a id="val.mice.msg"></a>`val.mice.msg` | Mic-E message | `mice.dest.a`, `mice.dest.b`, `mice.dest.c` | `A`, `B`, `C` are the flags of bytes 1 to 3. All 0: emergency. If each flag 1 is standard: standard message `i = 7 − (4A + 2B + C)`. If each flag 1 is custom: custom message `i`. A mix: no value ([amb.mice.dest](04-mic-e.md#amb.mice.dest)). | `emergency`, or `standard` or `custom` with `i` 0 to 6 | p. 63/45 |
| <a id="val.mice.alt"></a>`val.mice.alt` | Altitude | [`mice.alt`](04-mic-e.md#mice.alt) | `n = v(first three bytes) − 10000` | Metres above mean sea level. Step 1. −10000 to 751943. | p. 74/56 |
| <a id="val.mice.msgcap"></a>`val.mice.msgcap` | Messaging flag | [`mice.type.prefix`](04-mic-e.md#mice.type.prefix) | 0x60: messaging. 0x27: no messaging. `'>'` and `']'`: no value. | Flag | p. 73/55 |

The decoder computes `val.mice.lon` in these steps:

1. `D` = byte of `mice.lon.deg` − 28. If byte 5 has flag 1, add 100.
2. If `D` is 180 to 189, subtract 80. If `D` is 190 to 199, subtract 190.
3. `M` = byte of `mice.lon.min` − 28. If `M` ≥ 60, subtract 60.
4. `H` = byte of `mice.lon.hun` − 28.
5. Apply the level of `val.mice.lat`. Level 1: `H = H − H mod 10`. Level 2:
   `H` = 0. Level 3: also `M = M − M mod 10`. Level 4: also `M` = 0.
6. `n = s · (6000·D + 100·M + H)`. `s` is −1 if byte 6 has flag 1, +1 if
   not.

A blank destination byte keeps its flag (p. 62/44). Step 5 follows the
example of p. 71/53 and p. 72/54, where level 2 removes the hundredths.
APRS12c shows no other level. Levels 1, 3 and 4 follow the digit order of
`val.lon` (derived).

The example of p. 71/53 subtracts 80 and 4. The steps subtract 800 and 400
([err.mice.example](04-mic-e.md#err.mice.example)). The two give the same
speed and course for every byte from 0x1C to 0x7F (derived). Thus the
value stands (rule 3).

The status text can contain the fields of sections 8 and 9. Their value
rules apply there too.

## 8. Data extensions

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.ext.csespd"></a>`val.ext.csespd` | Course, speed | [`ext.csespd`](02-fields.md#ext.csespd) | Course `100·d[0] + 10·d[1] + d[2]`. Speed `100·d[4] + 10·d[5] + d[6]`. `000/000`, `.../...` and two `SP` halves: unknown, no values. A half of `'.'` or `SP`: no value for that half. Course `000` with a speed: no course ([amb.val.course0](#amb.val.course0)). | Course in degrees clockwise from north, step 1, 1 to 360 ([amb.val.course0](#amb.val.course0)). Speed in knots, step 1, 0 to 999. | p. 45/27 |
| <a id="val.ext.phg"></a>`val.ext.phg` | Power, height, gain, directivity | [`ext.phg`](02-fields.md#ext.phg), [`ext.phgr`](02-fields.md#ext.phgr) | Power `d[3]²`. Height `10 · 2^(b[4] − 0x30)`. Gain `d[5]`. Directivity: `d[6]` = 0 is omni, 1 to 8 give `45 · d[6]`, 9 gives no value. | Watts, 0 to 81. Feet above the average local terrain. dBi. Degrees. | p. 46/28 |
| <a id="val.ext.phgr"></a>`val.ext.phgr` | Beacon rate | `ext.phgr` | A digit gives `d[7]`. `'A'` and higher give `b[7] − 0x37` ([amb.val.phgcodes](#amb.val.phgcodes)). | Beacons per hour | p. 46/28 |
| <a id="val.ext.rng"></a>`val.ext.rng` | Range | [`ext.rng`](02-fields.md#ext.rng) | `1000·d[3] + 100·d[4] + 10·d[5] + d[6]` | "Miles", 0 to 9999 ([amb.val.miles](#amb.val.miles)) | p. 47/29 |
| <a id="val.ext.dfs"></a>`val.ext.dfs` | Strength, height, gain, directivity | [`ext.dfs`](02-fields.md#ext.dfs) | Strength `d[3]`. Height, gain and directivity as `val.ext.phg`. | S-points 0 to 9. Feet. dB ([amb.val.dfsgain](#amb.val.dfsgain)). Degrees. | p. 47/29, p. 48/30 |
| <a id="val.ext.brgnrq"></a>`val.ext.brgnrq` | Bearing, N, R, Q | [`ext.brgnrq`](02-fields.md#ext.brgnrq), [`ext.csespd`](02-fields.md#ext.csespd), `sym.table`, `sym.code` | Bearing `100·d[1] + 10·d[2] + d[3]`. N `d[5]`. Range `2^d[6]`. Q `d[7]`. If N = 0, N, R and Q have no value. Station: see below. | Bearing in degrees, 0 to 360 ([amb.val.bearing](#amb.val.bearing)). N: 1 to 8 are hits relative to the period, and 8 is 100%. 9 is a manual report. Range in "miles", 1 to 512. Q: a code. The table of p. 49/31 gives its beam width. | p. 48/30, p. 49/31 |

In a DF report, course `000` marks a fixed station, and another course
marks a moving station (p. 45/27). The decoder gives this as the station
value of `val.ext.brgnrq`, if both conditions are true:

- the symbol is the DF symbol;
- an `ext.csespd` with digits in the course is before the `ext.brgnrq`.

The station value is `fixed` for the course `000`, and `moving` for a
course from `001` to `360`. In all other cases, the station has no value.

The decoder gives values only for bytes in the packet. It does not give
the assumed values of a station without PHG (p. 47/29). It does not
compute the range circle of PHG
([err.ext.phgrange](02-fields.md#err.ext.phgrange)). The height is in
feet, so [err.ext.phgheight](02-fields.md#err.ext.phgheight) has no
effect.

## 9. Fields in a comment

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.cmt.alt"></a>`val.cmt.alt` | Altitude | [`cmt.alt`](02-fields.md#cmt.alt) | The six digits after `'/A='`, in decimal | Feet ([amb.val.altref](#amb.val.altref)). Step 1. 0 to 999999. | p. 43/27 |
| <a id="val.cmt.alt.neg"></a>`val.cmt.alt.neg` | Altitude | [`cmt.alt.neg`](02-fields.md#cmt.alt.neg) | Minus the five digits after `'/A=-'`, in decimal | Feet. Step 1. −99999 to 0. | p. 43/27 |
| <a id="val.dao.datum"></a>`val.dao.datum` | Datum | [`cmt.dao`](02-fields.md#cmt.dao) | The byte `D`. `'W'` or `'w'`: WGS84. `'N'` or `'n'`: NAD27. `'O'` or `'o'`: OSGB36. Other letters: a datum that APRS12c does not name. A digit: a local datum. Another byte of the base-91 set: APRS12c reserves it. No `cmt.dao`: the default datum ([amb.val.datum](#amb.val.datum)). | Code | p. 35/21, p. 36/22 |
| <a id="val.dao.lat"></a>`val.dao.lat` | Latitude with added precision | `cmt.dao`, and `val.lat` or `val.mice.lat` | Upper-case `D`, digit `A`: `n' = 10·n + s·(b(A) − 0x30)`, scale 1/60000 degree, step 1. Lower-case `D`: `a = b(A) − 33`, from 0 to 90. `n' = 1000·n + s·11·a`, scale 1/6000000 degree, step 11. `A` = `SP`: no added precision. | Degrees, at the scale of the case | p. 36/22, p. 37/23 |
| <a id="val.dao.lon"></a>`val.dao.lon` | Longitude with added precision | `cmt.dao`, and `val.lon` or `val.mice.lon` | As `val.dao.lat`, with `O` in place of `A`. | As `val.dao.lat` | p. 36/22, p. 37/23 |
| <a id="val.cmt.noarchive"></a>`val.cmt.noarchive` | No-archive flag | [`cmt.noarchive`](02-fields.md#cmt.noarchive) | Present | Flag | p. 110/86 |

`s` in `val.dao.lat` and `val.dao.lon` is the sign of the hemisphere
letter. The added digits extend the minutes of the position (p. 37/23).
Thus they increase the magnitude, also to the south and to the west.

The lower-case form multiplies the base-91 value by 1.10 and appends the
result after the hundredths of a minute (p. 37/23). The example `!wAb!`
gives `a` = 32, which adds 352 counts of 0.00001 minute. APRS12c writes
this as `DDMM.mm352`. The value of `':'` is 25
([err.cmt.daoexample](02-fields.md#err.cmt.daoexample)).

The decoder applies the added precision only if all these conditions are
true:

- the position is uncompressed or Mic-E ([amb.val.daobase](#amb.val.daobase));
- the level is 0;
- the `cmt.dao` token has no `unstated` finding;
- `a` is 90 or less ([amb.val.daorange](#amb.val.daorange)).

If a condition is false, the decoder gives the datum and no added
precision. The coordinate is then the value of the base position. An
`ambiguous` finding on `cmt.dao`, for example for several
candidates ([amb.cmt.dao](02-fields.md#amb.cmt.dao)), gives no datum and no
added precision.

## 10. Effect of findings

This table gives the effect of each finding that concerns a value. A token
that has no row here has only findings with the effect `kept`. A length
finding on a comment (`pos.cmt`, `pos.cmpcmt`, `df.cmt`) concerns no value.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `time.dhm`, `time.hms` | `syntax` at offsets 0–5, or a short token | All | `none` |
| `time.dhm` | `syntax` at offset 6: `'Z'` | All | `computable`: the digits as DHM, with the zone UTC |
| `time.dhm` | `syntax` at offset 6: another byte, `'H'` included | All | `none` |
| `time.dhm`, `time.hms` | `value` (a number out of range) | All | `none` |
| `time.dhm` | `syntax` at offset 6, after six digits | Every value from a later token | `computable` (section 2.3) |
| `time.dhm`, `time.hms`, `pos.time` | Another `syntax` | Every value from a later token | `none` (section 2.3) |
| `time.dhm` | `discouraged` (`'/'`) | All | `kept`, local time |
| `lat`, `lon` | `syntax`, also `syntax` on `lat.amb` | The coordinate of the token | `none` |
| `lat` | `syntax` on `lat.amb` | `val.lon` | `none`: the level has no value |
| `lat` | A finding with the rule ID `lat` | `val.lon` | `kept` |
| `lat` | `syntax`, also `syntax` on `lat.amb` | `val.lat.amb` | `none` |
| `lat` | Another finding | `val.lat.amb` | `kept` |
| `lat`, `lon` | `value`: tens of minutes 6–9 | The coordinate of the token | `computable` ([amb.val.minutes](#amb.val.minutes)) |
| `lat`, `lon` | `value`: degrees above 90 or 180, or minutes at 90 or 180 | The coordinate of the token | `none` |
| `lon` | `unstated` on `lon.amb` (a `SP` that the level does not cover) | `val.lon` | `computable`: the `SP` counts as 0. The step is that of the lowest level that covers every `SP` of `lon`. |
| `sym.table`, `mice.sym.table`, `cmp.table` | `syntax` | `val.sym` | `none` |
| `sym.code`, `mice.sym.code`, `cmp.code` | `syntax` | `val.sym` | `none` |
| `cmp.lat`, `cmp.lon` | `syntax` | The coordinate | `none` |
| `cmp.lat`, `cmp.lon` | `value` (beyond 90 S or 180 E) | The coordinate | `none` |
| `cmp.cs`, `cmp.cs.*` | `syntax` | Course, speed, range, altitude | `none` |
| `cmp.t` | `syntax` | `val.cmp.t`, and the value of the `cs` token | `none` |
| `cmp.t` | `value` (bits 7–6 not 0) | `val.cmp.t` | `computable` |
| `cmp.t` | `value` (bits 7–6 not 0) | The value of the `cs` token | `kept` |
| `dest.mice`, `mice.dest.*` | `syntax` | The values that use the token | `none` |
| `dest.mice` | `value`: degrees above 90, or minutes at 90 | `val.mice.lat` | `none` |
| `dest.mice` | `value`: tens of minutes above 5 | `val.mice.lat` | `computable` ([amb.val.minutes](#amb.val.minutes)) |
| `dest.mice` | `value` | `val.mice.lon`, `val.mice.msg` | `kept` |
| `dest.mice` | `unstated` ([amb.mice.dest](04-mic-e.md#amb.mice.dest)) | `val.mice.msg` | `none` |
| `dest.mice` | `unstated` | `val.mice.lat`, `val.mice.lon` | `kept` |
| `mice.lon.deg`, `mice.lon.min` | `value` (outside the table) | `val.mice.lon` | `computable` |
| `mice.lon.*`, `mice.sp`, `mice.se` | `syntax` | The values that use the token | `none` |
| `mice.dc` | `syntax` | `val.mice.spd`, `val.mice.crs` | `none` |
| `mice.dc` | `value`: `(b − 28) mod 10` is 8 or 9 | `val.mice.spd` | `computable` |
| `mice.dc` | `value`: `(b − 28) mod 10` is 8 or 9 | `val.mice.crs` | `none` |
| `mice.dc` | `value`: course above 360 | `val.mice.spd` | `kept` |
| `mice.dc` | `value`: course above 360 | `val.mice.crs` | `none` |
| `mice.dti` | `obsolete` | `val.mice.dti` | `kept` |
| `mice.alt` | `syntax` | `val.mice.alt` | `none` |
| `mice.alt` | `discouraged` (not first) | `val.mice.alt` | `kept` |
| `mice.alt` | `ambiguous`: the token overlaps another token ([amb.cmt.overlap](02-fields.md#amb.cmt.overlap)) | `val.mice.alt` | `computable`: neither field is the narrowest interpretation |
| `ext.csespd` | `value` (course 361–999) | Course | `none` |
| `ext.csespd` | `value` (course 361–999) | Speed | `kept` |
| `ext.csespd` | `unstated` and `ambiguous` (halves of different kinds, [amb.ext.csespd](02-fields.md#amb.ext.csespd)) | The half with digits | `computable`: APRS12c does not specify this pair (`unstated`) |
| `ext.phg`, `ext.phgr`, `ext.dfs` | `value` (directivity `'9'`) | Directivity | `none` |
| `ext.phg`, `ext.phgr`, `ext.dfs` | `value` (directivity `'9'`) | Other values of the token | `kept` |
| `ext.brgnrq` | `value` (bearing above 360) | Bearing | `none` |
| `ext.brgnrq` | `value` (bearing above 360) | N, R, Q | `kept` |
| Any extension | `ambiguous` ([amb.ext.compressed](02-fields.md#amb.ext.compressed), [amb.df.detect](03-position.md#amb.df.detect)) | All | `kept`: the field is the narrowest interpretation (README section 3.1) |
| `cmt.alt`, `cmt.alt.neg` | `syntax` | The altitude | `none` |
| `cmt.alt`, `cmt.alt.neg` | `ambiguous`: several altitudes ([amb.cmt.alt](02-fields.md#amb.cmt.alt)) | The altitude | `kept` ([amb.val.altitudes](#amb.val.altitudes)) |
| `cmt.alt`, `cmt.alt.neg` | `ambiguous`: the token overlaps another token ([amb.cmt.overlap](02-fields.md#amb.cmt.overlap)) | The altitude | `computable`: neither field is the narrowest interpretation |
| `cmt.dao` | `unstated` | `val.dao.lat`, `val.dao.lon` | `none` |
| `cmt.dao` | `unstated` | `val.dao.datum` | `kept`: the byte `D` |
| `cmt.dao` | `ambiguous` | `val.dao.*` | `none` |

**[open]** The two rows for `val.lat.amb` come from the decoder. In
Mic-E, the level is a value of `val.mice.lat`. Thus `computable` and
`none` on the Mic-E latitude also apply to its level. Whether the two
formats agree is open.

## 11. Catalogue

The last column of this catalogue tells what the decoder does, because the
tokenizer gives no values.

| ID | Pages | What APRS12c leaves open | Class | Rule | What the decoder does |
|---|---|---|---|---|---|
| <a id="amb.val.ambiguity"></a>`amb.val.ambiguity` | p. 40/24, p. 41/25 | One page shows a box: the blanked digits can have any value. The next page rejects the box and specifies a circle, centred on the given position. Neither says which number a blanked digit is. | conflict | 3; none | Working choice: a blanked digit counts as 0. The step gives the size of the blanked digits. `n` is an edge of the box, not a position. The decoder gives no centre and no radius. |
| <a id="amb.val.minutes"></a>`amb.val.minutes` | p. 39/23, p. 62/44 | Minutes have the tens 0 to 5. APRS12c gives no meaning to the tens 6 to 9. | unstated | 2 | The tokenizer gives `value`. Effect `computable`: the arithmetic gives a number, for example 49° 63.50' as 50° 03.50'. |
| <a id="amb.val.timewindow"></a>`amb.val.timewindow` | p. 38/22, p. 39/23 | A DHM timestamp has no month and no year. An HMS timestamp has no date. APRS12c does not say which date applies. | unstated | 2 | The decoder gives the fields of the timestamp and no date under this file. A date is a choice of [docs/interop](../interop/01-record.md#6-report-time). |
| <a id="amb.val.localtime"></a>`amb.val.localtime` | p. 38/22 | Local time has no offset to UTC. | unstated | 2 | The decoder gives the fields with the zone "local", and no UTC time. |
| <a id="amb.val.course0"></a>`amb.val.course0` | p. 45/27, p. 56/38, p. 57/39 | The uncompressed course is 001 to 360, and the pair `000/000` is unknown. Course `000` with a speed is outside that range, and APRS12c gives it a meaning only in a DF report. A compressed `c` of `'!'` gives course 0 by the formula, and APRS12c does not say if 0 is north or unknown. | unstated | 2 | Uncompressed course `000` with a speed: no course. Compressed course 0: the value 0, with this note. |
| <a id="amb.val.miles"></a>`amb.val.miles` | p. 47/29, p. 48/30, p. 57/39, p. 149/125 | Ranges are in "miles". The range fields name no kind of mile. The units conversion table gives the mile as 1.609344 km and lists the nautical mile separately. The ambiguity circle uses nautical miles and says so (p. 41/25). | ambiguous | 1 | The mile of the conversion table: the statute mile. Under this file, the value is the number of miles. |
| <a id="amb.val.altref"></a>`amb.val.altref` | p. 43/27, p. 58/40, p. 74/56 | APRS12c does not state the reference surface of the comment altitude or of the compressed altitude. It states mean sea level only for the Mic-E altitude. | unstated | 2 | The decoder gives these altitudes with the reference "not stated". |
| <a id="amb.val.altitudes"></a>`amb.val.altitudes` | p. 43/27, p. 58/40, p. 74/56 | A packet can have several altitudes: in the comment, in the compressed block and in the Mic-E status text. APRS12c gives no precedence. | ambiguous | 4 | The decoder gives every altitude, with its token. |
| <a id="err.val.cmpspeed"></a>`err.val.cmpspeed` | p. 54/36, p. 57/39 | The list of advantages gives the speed accuracy in mph. The formula and its example give knots. | conflict | 3 | No effect on values. The accuracy statement does not state the unit of the field. |
| <a id="amb.val.datum"></a>`amb.val.datum` | p. 35/21, p. 36/22, p. 37/23 | Without a DAO, the datum is WGS84 or the datum of a local agreement, for example OSGB36 in the UK. APRS12c names only three of the 26 letter datums. | unstated | 2 | No DAO: the datum is "default". A letter other than `W`, `N` or `O`: the letter, with no named datum. |
| <a id="amb.val.daobase"></a>`amb.val.daobase` | p. 36/22, p. 37/23 | The added digits extend `DDMM.mm`. APRS12c does not address a compressed position or a position with ambiguity. | unstated | 2 | The decoder gives the datum and no added precision. |
| <a id="amb.val.daorange"></a>`amb.val.daorange` | p. 34/20, p. 37/23 | The base-91 digits of the DAO go from 00 to 90. The base-91 set includes `'\|'`, value 91. | conflict | 1 | Value 91 is outside the specified range. No added precision for that coordinate. |
| <a id="err.val.daostep"></a>`err.val.daostep` | p. 36/22, p. 37/23 | The precision is "the nearest 91/ten thousandth" of a minute. The scaling by 1.10 gives steps of 1.1/10000 minute. | conflict | 3 | No effect on values. The scaling and its example give the value. |
| <a id="amb.val.micefix"></a>`amb.val.micefix` | p. 64/46 | 0x27 marks old data, or current data from a TM-D700. | ambiguous | 4 | No fix age for 0x27. |
| <a id="amb.val.symbol"></a>`amb.val.symbol` | p. 127/103 | APRS12c does not say if the other symbols apply when the symbol of the information field has a fault. | unstated | 2 | The decoder does not use the symbols of the address fields. |
| <a id="amb.val.phgcodes"></a>`amb.val.phgcodes` | p. 46/28 | Height codes after `';'` and rates after `'A'` continue "and so on". | ambiguous | 1 | The decoder continues each series by the byte value. |
| <a id="amb.val.dfsgain"></a>`amb.val.dfsgain` | p. 46/28, p. 48/30 | DFS is PHG with the power replaced. The PHG gain is in dBi, and the DFS gain is in dB. | ambiguous | 1 | The DFS table specifies dB. The decoder gives the DFS gain in dB. |
| <a id="amb.val.bearing"></a>`amb.val.bearing` | p. 48/30 | APRS12c does not say whether the bearing is from true or magnetic north. | unstated | 2 | The decoder gives degrees, with no reference. |

## 12. Reviewed exceptions

None.

## 13. Open items

- Values of the area descriptor, locators, frequencies and the
  symbols in the address fields
  ([01 section 11](01-frame.md#11-open-items)).
- A list of the expected values of the worked examples of APRS12c, by page
  and digest, as [examples.json](examples.json) does for verdicts. The
  pages are p. 37/23, p. 56/38, p. 57/39, p. 58/40, p. 71/53 and p. 74/56.
- The position in the Mic-E status text, which has precedence over the
  Mic-E position (p. 72/54). The tokenizer does not look for it
  ([amb.mice.extension](04-mic-e.md#amb.mice.extension)).
- A run of the decoder over the corpus. The run finds the rows of section
  11 that affect more than 0.01% of the packets (README section 2).
- **[open]** A finding at the end of a token also concerns the next
  token, if that token starts there (section 2.3). For example, `syntax`
  on byte 4 of a Mic-E destination concerns `val.mice.msg`. The decoder
  follows section 2.3.
- **[open]** A DAO on a coordinate that has a `computable` step. If the
  level is 0 and `lon` has a `SP` that the level does not cover, section 9
  applies the DAO. The result then has the step of the DAO, but the
  hundredths are not known. One option: no added precision for a
  coordinate with a `computable` finding.
- Two range checks that [02](02-fields.md) does not have. The tokenizer
  gives no finding for course `000` with a speed (p. 45/27). It gives no
  finding for a base-91 DAO digit of 91 (p. 37/23). This file changes no
  finding, so both rows give the effect directly.
