# Status body

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Record | [01-record.md](01-record.md): envelope, modes, value objects, position body |
| Values | [docs/legacy/14-values-status.md](../legacy/14-values-status.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the status body of a record. The decoder gives it for
a status report. The conventions of [01-record](01-record.md) apply: the
modes, the value objects, the provenance and the notes.

## 2. Uses

**[proposed]** A record of a status report has one use. `uses` is
`["status"]`. `format` is `stat.dti`.

**[proposed]** A status report with a locator has no position body. The
status body gives the locator as bytes (section 3).

## 3. Fields

**[proposed]** The status body has these fields:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `locator` | Bytes | The Maidenhead locator, as the packet has it. | `val.stat.loc` |
| `symbol` | Object | The symbol after the locator. Its members are those of the `symbol` of the position body ([01-record section 7](01-record.md#7-position-body)). | `val.sym` |
| `text` | Bytes | The status text. After a locator, without the `SP` that starts it. | `val.stat.text` |
| `beam_heading` | Quantity | Degrees clockwise from north. | `val.stat.beam` |
| `beam_power` | Quantity | Effective radiated power, in watts. | `val.stat.beam` |
| `noarchive` | Flag | `true` if the text has the bytes `!x!`. | `val.cmt.noarchive` |

**[agreed]** A locator with lower-case letters is a value in both modes,
with no mark. `locator` has the bytes as the packet has them.

**[proposed]** The record leaves out a field that has no token in the
packet. A status report with no text has no `text`.

**[proposed]** `text` has every byte of the status text. The bytes of the
beam heading, of a frequency and of `!x!` are also in `text`.

**[proposed]** A frequency in the text has no value rule yet. Its tokens
are in `undecoded`.

### 3.1 Units

**[proposed]** The record computes `v` and `res` with this table. `h` and
`k` are the codes of
[val.stat.beam](../legacy/14-values-status.md#val.stat.beam).

| Unit of 14-values-status | Record unit | `v` | `res` |
|---|---|---|---|
| 10 · `h` degrees | degree | 10 · `h` | 10 |
| 10 · `k`² watts | watt | 10 · `k`² | 10 · (2 · `k` + 1) |

`res` of the power is the value of the next code minus the value of this
code, as [01-record section 4.3](01-record.md#43-units) says for a
non-linear unit.

### 3.2 Notes

**[proposed]** The decoder gives this note for the status body:

| Row | Field | Condition |
|---|---|---|
| `amb.stat.grid` | `locator` | Always. |

## 4. Report time

**[proposed]** `report_time` follows
[01-record section 6](01-record.md#6-report-time). A status report with a
timestamp has the form `"dhm"`, in the zone `"utc"`. Without a timestamp,
`form` is `"received"` if the input gives a received time.

## 5. Example

The line is the fourth example of a status report with a locator of
APRS12c, p. 106/82. The record is in strict mode. The input gives no
received time.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001:>IO91SX/- ^B7",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["status"], "format": "stat.dti", "verdict": "conform", "findings": [],
 "status": {
  "locator": {"bytes": "IO91SX", "from": [["grid.loc", 15, 21]]},
  "symbol": {"chars": "/-", "classic": 12, "from": [["sym.table", 21, 22], ["sym.code", 22, 23]]},
  "text": {"bytes": "^B7", "from": [["stat.text", 23, 27]]},
  "beam_heading": {"v": 110, "res": 10, "from": [["stat.beam", 24, 27]]},
  "beam_power": {"v": 490, "res": 150, "from": [["stat.beam", 24, 27]]}},
 "notes": [["amb.stat.grid", "status.locator"]],
 "undecoded": []}
```

The values are derived as follows:

- `beam_heading`: `'B'` is 0x42. `h` is 66 − 55 = 11. The heading is 110
  degrees.
- `beam_power`: `'7'` gives `k` = 7. The power is 10 × 49 = 490 W. `res`
  is 10 × 15 = 150 W.
- `classic`: the code `'-'` is 0x2D. In the primary table, the number is
  0x2D − 33 = 12.

## 6. Open items

- **[open]** Whether a status report with a locator also has a position
  body. The locator gives a cell, not a point.
- **[open]** Whether `text` leaves out the bytes of the beam heading.
- **[open]** The status text of Mic-E is the `comment` of the position
  body. Whether such a packet also has the use `status`.
