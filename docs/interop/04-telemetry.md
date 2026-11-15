# Telemetry body and telemetry definition body

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Record | [01-record.md](01-record.md): envelope, modes, value objects, position body |
| Values | [docs/legacy/13-values-telemetry.md](../legacy/13-values-telemetry.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies two bodies of a record:

- the telemetry body, for a telemetry report and for a base-91 block in a
  comment;
- the telemetry definition body, for the four definition messages.

The conventions of [01-record](01-record.md) apply: the modes, the value
objects, the provenance and the notes.

## 2. Uses

**[agreed]** A definition message has its own body. It is not a part of
the telemetry body, and it is not a message body.

**[agreed]** The telemetry body gives raw values
([13-values-telemetry section 2.2](../legacy/13-values-telemetry.md#22-raw-values)).
The decoder does not apply a definition to a report. A reader that wants
the final values joins the records of one station.

**[proposed]** The table gives `uses` for each format:

| Format | `format` | `uses` |
|---|---|---|
| Telemetry report | `tlm.dti` | `["telemetry"]` |
| Position report or Mic-E with a base-91 block | `pos.dti`, `mice.dti` | `["position", "telemetry"]` |
| Definition message | `tlm.def.dti` | `["telemetry_definition"]` |

**[proposed]** A packet has the use `telemetry` in addition to its other
uses if its comment has a `tlm.b91` token. The position body is that of
[01-record section 7](01-record.md#7-position-body), without change.

## 3. Telemetry body

**[proposed]** The telemetry body has these fields:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `sequence` | Code | The sequence number, as an integer. | `val.tlm.seq`, `val.tlm.b91.seq` |
| `analog` | List of quantities | The raw values of the analog channels. Item `i`, from 0, is channel A(`i` + 1). | `val.tlm.analog`, `val.tlm.b91.analog` |
| `digital` | Flags | The eight digital channels. Item `i`, from 0, is channel B(`i` + 1). `true` is the bit 1. | `val.tlm.digital`, `val.tlm.b91.bits` |
| `comment` | Bytes | Only in a telemetry report: the bytes of the `cmt.text` token. | — |

**[proposed]** Each item of `analog` is a value object of its own. The
modes apply to each item separately.

**[proposed]** `analog` has these items:

- In a telemetry report: five items. If the report ends before a value,
  the item is a no-value object. Its `why` gives the `syntax` finding.
- In a base-91 block: one item for each analog pair of the block, 1 to 5
  items.

**[proposed]** A telemetry report always has `sequence` and `digital`. If
the report ends before one of them, the field is a no-value object. A
base-91 block has `digital` only if it has the seventh pair.

**[agreed]** A sequence number that is not three digits has the effect
`computable`, if only digits are between its `'#'` and its `','`. In
permissive mode, `sequence` is their decimal number, with a mark.

**[proposed]** The sequence number `MIC` gives a no-value object. Its
`why` is `["val.tlm.seq"]`.

**[proposed]** The comment of a packet with a base-91 block is the
`comment` of the position body.

### 3.1 Raw values

**[proposed]** A raw value has no record unit. `n` is the count and `f` is
the number of digits after the `'.'`
([13-values-telemetry section 2.1](../legacy/13-values-telemetry.md#21-numbers)).
The record computes `v` and `res` as follows:

| Value | `v` | `res` |
|---|---|---|
| Raw value of a telemetry report | `n` / 10^`f` | 1 / 10^`f` |
| Raw value of a base-91 block | `n` | 1 |
| Coefficient of a definition message | `n` / 10^`f` | 1 / 10^`f` |

### 3.2 Notes

**[proposed]** The decoder gives this note for the telemetry body:

| Row | Field | Condition |
|---|---|---|
| `amb.val.tlmbits` | `digital` | A value from `tlm.digital`. |

## 4. Telemetry definition body

**[proposed]** The telemetry definition body has these fields:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `station` | Bytes | The station that the definition describes: the addressee of the message. | `val.tlm.def.station` |
| `kind` | Code | `"parm"`, `"unit"`, `"eqns"` or `"bits"`. | `val.tlm.def.kind` |
| `names` | List of byte strings | Only for `"parm"`: the names of A1 to A5 and of B1 to B8, in this order. | `val.tlm.parm` |
| `units` | List of byte strings | Only for `"unit"`: the units of A1 to A5 and the labels of B1 to B8, in this order. | `val.tlm.unit` |
| `coefficients` | List of quantities | Only for `"eqns"`: a, b and c of A1, then of A2, up to A5. | `val.tlm.eqns` |
| `sense` | Flags | Only for `"bits"`: the bit sense of B1 to B8. | `val.tlm.bits.sense` |
| `title` | Bytes | Only for `"bits"`: the project title. | `val.tlm.bits.title` |

**[proposed]** Each item of a list is a value object of its own. A list
has one item for each field of the list in the packet, up to the number
of channels. A list that stops early has fewer items. An empty list is
`[]`.

**[agreed]** A name, a unit or a label that is longer than its byte count
is a value in both modes, with no mark
([13-values-telemetry section 6](../legacy/13-values-telemetry.md#6-effect-of-findings)).

**[proposed]** If A1 of `"parm"` or `"unit"` is empty, the packet has no
token for it. The `from` of that item is the token of the list.

**[proposed]** The record leaves out `title` if the packet has no title
token.

**[proposed]** `source` of the envelope is the sender of the message. It
can be another station than `station`.

**[proposed]** The tokens `msg.addr.pad` and `msg.sep` have no value. They
are not in `undecoded`. The message identifier of a definition message is
in `undecoded`, and also each extra field of a list.

## 5. Report time

**[proposed]** A telemetry report and a definition message have no
timestamp. `report_time` follows
[01-record section 6](01-record.md#6-report-time): if the input gives a
received time, `form` is `"received"`. A packet with a base-91 block has
the report time of its position report.

## 6. Examples

### 6.1 Telemetry report

The line is the first example of a telemetry report of APRS12c,
p. 88/68. The record is in strict mode. The input gives no received time.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001:T#005,199,000,255,073,123,01101001",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["telemetry"], "format": "tlm.dti", "verdict": "conform", "findings": [],
 "telemetry": {
  "sequence": {"code": 5, "from": [["tlm.seq", 15, 20]]},
  "analog": [
   {"v": 199, "res": 1, "from": [["tlm.analog", 20, 24]]},
   {"v": 0, "res": 1, "from": [["tlm.analog", 24, 28]]},
   {"v": 255, "res": 1, "from": [["tlm.analog", 28, 32]]},
   {"v": 73, "res": 1, "from": [["tlm.analog", 32, 36]]},
   {"v": 123, "res": 1, "from": [["tlm.analog", 36, 40]]}],
  "digital": {"flags": [false, true, true, false, true, false, false, true], "from": [["tlm.digital", 40, 48]]}},
 "notes": [["amb.val.tlmbits", "telemetry.digital"]],
 "undecoded": []}
```

### 6.2 Definition message

The line has the format of the bit sense example of APRS12c, p. 92/72,
with another station and another title. The record is in strict mode.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001::N0CALL-11:BITS.10110000,Big Balloon",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["telemetry_definition"], "format": "tlm.def.dti", "verdict": "conform", "findings": [],
 "telemetry_definition": {
  "station": {"bytes": "N0CALL-11", "from": [["msg.addr.name", 15, 24]]},
  "kind": {"code": "bits", "from": [["tlm.bits", 25, 50]]},
  "sense": {"flags": [true, false, true, true, false, false, false, false], "from": [["tlm.bits.sense", 30, 38]]},
  "title": {"bytes": "Big Balloon", "from": [["tlm.bits.title", 39, 50]]}},
 "notes": [],
 "undecoded": []}
```

The `','` at offset 38 is the separator of
[amb.tlm.bitsep](../legacy/07-telemetry.md#amb.tlm.bitsep). It belongs to
no token of the body.

## 7. Open items

- **[open]** Whether `sequence` gives `MIC` as a code in place of a
  no-value object.
- **[open]** Whether `digital` gives a value for each bit that is `'0'` or
  `'1'`, if another byte of the digital value is wrong.
- **[open]** Whether the `report_time` of a telemetry report needs a
  note, as an Object without a timestamp has `amb.val.objtime`.
- **[open]** The message identifier of a definition message. It waits for
  the message body.
- **[open]** Whether a record of a definition message also has the use
  `message`, when the message body exists.
