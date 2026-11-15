# Capabilities body

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Record | [01-record.md](01-record.md): envelope, modes, value objects, position body |
| Values | [docs/legacy/17-values-capabilities.md](../legacy/17-values-capabilities.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the capabilities body of a record. The decoder gives
it for a station capabilities packet. The conventions of
[01-record](01-record.md) apply: the modes, the value objects, the
provenance and the notes.

## 2. Uses

**[agreed]** A station capabilities packet has a body.

**[proposed]** A record of a station capabilities packet has one use.
`uses` is `["capabilities"]`. `format` is `cap.dti`.

## 3. Fields

**[proposed]** The capabilities body has one field:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `items` | List of byte strings | One item for each capability, in the order of the packet. `bytes` is the name. An item with a value also has `value`, a byte string. | `val.cap.name`, `val.cap.value` |

**[agreed]** The name and the value are byte strings. The decoder gives
no number for a value, and it gives no meaning to a name.

**[proposed]** Each item is a value object of its own. The modes apply to
each item separately. `from` of an item has the `cap.token` token, and
then the `cap.value` token if the item has one.

**[proposed]** An item with no value is a no-value object without `value`.
Its `from` is the `cap.item` token.

**[proposed]** A packet with no capability has `items` `[]`.

### 3.1 Notes

**[proposed]** The decoder gives this note for the capabilities body:

| Row | Field | Condition |
|---|---|---|
| `amb.cap.form` | `items` | An item with `bytes` whose capability has a `cap.pad` token. |

## 4. Report time

**[proposed]** A station capabilities packet has no timestamp.
`report_time` follows [01-record section 6](01-record.md#6-report-time):
if the input gives a received time, `form` is `"received"`.

## 5. Example

The line has the capabilities that APRS12c defines (p. 101/77). The record
is in strict mode. The input gives no received time.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001:<IGATE,MSG_CNT=43,LOC_CNT=14",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["capabilities"], "format": "cap.dti", "verdict": "conform", "findings": [],
 "capabilities": {
  "items": [
   {"bytes": "IGATE", "from": [["cap.token", 15, 20]]},
   {"bytes": "MSG_CNT", "value": "43", "from": [["cap.token", 21, 28], ["cap.value", 29, 31]]},
   {"bytes": "LOC_CNT", "value": "14", "from": [["cap.token", 32, 39], ["cap.value", 40, 42]]}]},
 "notes": [],
 "undecoded": []}
```

## 6. Open items

- **[open]** Whether the counts of an IGate are numbers.
- **[open]** Whether an item is an object with the members `name` and
  `value`, in place of a byte string with `value`.
