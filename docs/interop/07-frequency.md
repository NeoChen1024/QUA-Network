# Frequency body

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Record | [01-record.md](01-record.md): envelope, modes, value objects, position body |
| Values | [docs/legacy/16-values-frequency.md](../legacy/16-values-frequency.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the frequency body of a record. The decoder gives it
for a packet whose text has a frequency specification. The conventions of
[01-record](01-record.md) apply: the modes, the value objects, the
provenance and the notes.

## 2. Uses

**[agreed]** A frequency specification has its own body. A packet has the
use `frequency` in addition to its other uses.

**[proposed]** A packet has the use `frequency` if its text has one of
these tokens: `freq.mhz`, `freq.uw`, `freq.ghz`, `freq.rx`, `freq.tone`,
`freq.offset`, `freq.range` or `freq.dstar`. The table gives examples of
`uses`:

| Packet | `uses` |
|---|---|
| Position report or Mic-E with a frequency in the comment | `["position", "frequency"]` |
| Object or Item with a frequency in the comment | `["object", "position", "frequency"]` |
| Status report with a frequency in the text | `["status", "frequency"]` |

**[agreed]** The decoder gives the frequency body only in a record that
has a position body or a status body. A format with no body has no
frequency body: its frequency tokens are in `undecoded`. An example is
the obsolete Object format.

**[proposed]** The other bodies do not change. The `comment` of the
position body and the `text` of the status body keep the bytes of the
frequency specification.

## 3. Fields

**[proposed]** The frequency body has these fields:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `frequency` | Quantity | The frequency, in megahertz. | `val.freq.mhz`, `val.freq.uw`, `val.freq.ghz` |
| `rx_frequency` | Quantity | The alternate receive frequency, in megahertz. | `val.freq.rx` |
| `tone_kind` | Code | `"tone"`, `"ctcss"`, `"dcs"`, `"off"` or `"burst"`. With `"ctcss"`, the squelch of a radio also uses the tone. With `"tone"`, it does not. | `val.freq.tone.kind` |
| `tone` | Quantity | The tone frequency, in hertz. Only for the kinds `"tone"`, `"ctcss"` and `"burst"`. | `val.freq.tone` |
| `dcs` | Bytes | The DCS code, three digits. Only for the kind `"dcs"`. | `val.freq.dcs` |
| `narrow` | Flag | `true` if the first letter of the tone is in lower case. | `val.freq.narrow` |
| `offset` | Quantity | The transmit offset, in megahertz. It can be negative. | `val.freq.offset` |
| `range` | List of quantities | Each range of the packet, in kilometres. Each item also has `dir`: `"all"`, `"north"`, `"south"`, `"east"` or `"west"`. | `val.freq.range` |
| `dstar` | Flag | `true` if the text has the D-STAR marker. | `val.freq.dstar` |
| `dstar_repeater` | Bytes | The callsign of the access repeater, without padding. | `val.freq.dstar` |
| `dstar_module` | Bytes | The module letter of the access repeater. | `val.freq.dstar` |

**[proposed]** The record leaves out a field that has no token in the
packet. It leaves out `narrow` if the first letter of the tone is not in
lower case.

**[proposed]** Each item of `range` is a value object of its own. The
items are in the order of the packet.

**[agreed]** A frequency whose `MHz` is in another case is a value in
both modes, with no mark
([16-values-frequency section 6](../legacy/16-values-frequency.md#6-effect-of-findings)).

**[agreed]** A body can have no `frequency`. The text then has the tone,
the offset or the range at its start
([amb.freq.nofreq](../legacy/09-other.md#amb.freq.nofreq)). Text that is
not a frequency specification can start with the same bytes. The note of
section 3.2 marks these values.

**[agreed]** `tone` has the tenths of a hertz if the three digits select a
tone of the list of
[16-values-frequency section 4](../legacy/16-values-frequency.md#4-tone-offset-and-range).
`res` is then 0.1. For every other tone, `tone` is the number of the three
digits, and `res` is 1.

**[agreed]** Three forms of the tone have the effect `computable`. In strict
mode, `tone` is a no-value object, and its `why` has the row ID. In
permissive mode, `tone` has the value, and its `mark` has the row ID:

| Digits | Row ID | Value in permissive mode |
|---|---|---|
| `000` | `"amb.val.tone0"` | 0, with `res` 1 |
| A tone of the list in tenths of a hertz, for example `885` | `"amb.val.tonetenths"` | That tone, for example 88.5, with `res` 0.1 |
| Another number that is not in the list, below 60 or above 300 | `"amb.val.tonerange"` | The number of the digits, with `res` 1 |

### 3.1 Units

**[agreed]** The frequency, the receive frequency and the offset are in
megahertz. The tone is in hertz. The range is in kilometres
([01-record section 4.3](01-record.md#43-units)).

**[proposed]** `n` is the count and `w` is the step of
16-values-frequency. For a tone of the list, both are in hertz with one
digit after the point. The record computes `v` and `res` with this table:

| Unit of 16-values-frequency | Record unit | `v` | `res` |
|---|---|---|---|
| kilohertz | megahertz | `n` / 1000 | `w` / 1000 |
| megahertz | megahertz | `n` | `w` |
| 10 kHz | megahertz | `n` / 100 | `w` / 100 |
| hertz | hertz | `n` | `w` |
| mile | kilometre | `n` · 1.609344 | `w` · 1.609344 |
| kilometre | kilometre | `n` | `w` |

### 3.2 Notes

**[proposed]** The decoder gives these notes for the frequency body:

| Row | Field | Condition |
|---|---|---|
| `amb.val.tone` | `tone` | A value of the kind `"tone"` or `"ctcss"`. |
| `amb.freq.nofreq` | `tone_kind`, `offset`, `range` | A value of that field in a body with no frequency token. |

## 4. Report time

**[proposed]** The frequency body has no time of its own. `report_time`
is that of the other body of the record.

## 5. Example

The line is a position report. Its comment has the format of the examples
of APRS12c, p. 114/90. The record is in strict mode. The input gives no
received time.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001:!4903.50N/07201.75W-146.520MHz T107 +060 R25m Monitoring",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["position", "frequency"], "format": "pos.dti", "verdict": "conform", "findings": [],
 "position": {
  "lat": {"v": 49.05833333333333, "res": 0.00016666666666666666, "from": [["lat", 15, 23]]},
  "lon": {"v": -72.02916666666667, "res": 0.00016666666666666666, "from": [["lon", 24, 33], ["lat", 15, 23]]},
  "ambiguity": {"code": 0, "from": [["lat", 15, 23]]},
  "datum": {"code": "default", "from": []},
  "symbol": {"chars": "/-", "classic": 12, "from": [["sym.table", 23, 24], ["sym.code", 33, 34]]},
  "messaging": {"flag": false, "from": [["pos.dti", 14, 15]]},
  "comment": {"bytes": "146.520MHz T107 +060 R25m Monitoring", "from": [["cmt.text", 34, 70]]},
  "extensions": []},
 "frequency": {
  "frequency": {"v": 146.52, "res": 0.001, "from": [["freq.mhz", 34, 44]]},
  "tone_kind": {"code": "tone", "from": [["freq.tone", 44, 49]]},
  "tone": {"v": 107.2, "res": 0.1, "from": [["freq.tone", 44, 49]]},
  "offset": {"v": 0.6, "res": 0.01, "from": [["freq.offset", 49, 54]]},
  "range": [{"v": 40.2336, "res": 1.609344, "dir": "all", "from": [["freq.range", 54, 59]]}]},
 "notes": [["amb.val.datum", "position.datum"], ["amb.val.tone", "frequency.tone"]],
 "undecoded": []}
```

The values are derived as follows:

- `frequency`: the count is 1000 × 146 + 520 = 146520 kHz, with step 1.
  `v` is 146.52 MHz. `res` is 0.001 MHz.
- `tone`: the three digits are 107. The list has the tone 107.2 Hz. `res`
  is 0.1 Hz.
- `offset`: the count is +60, in units of 10 kHz. `v` is 0.6 MHz. `res`
  is 0.01 MHz.
- `range`: 25 miles × 1.609344 is 40.2336 km.

## 6. Open items

- **[open]** A frequency in the name of an Object.
- **[open]** Whether `comment` and `text` leave out the bytes of the
  frequency specification.
