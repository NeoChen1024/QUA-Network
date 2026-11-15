# Message body and bulletin body

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Record | [01-record.md](01-record.md): envelope, modes, value objects |
| Values | [docs/legacy/15-values-message.md](../legacy/15-values-message.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies two bodies of a record:

- the message body, for a message, an acknowledgement and a rejection;
- the bulletin body, for a bulletin, an announcement and an NWS bulletin.

The conventions of [01-record](01-record.md) apply: the modes, the value
objects, the provenance and the notes.

## 2. Uses

**[proposed]** The table gives `uses` for each format:

| Format | `format` | `uses` |
|---|---|---|
| Message, acknowledgement, rejection, NTS line | `msg.dti` | `["message"]` |
| Bulletin, announcement | `bln.dti` | `["bulletin"]` |
| NWS bulletin | `nws.dti` | `["bulletin"]` |

**[agreed]** An acknowledgement and a rejection have the message body.
They serve the use `message`: they answer a message, and they have its
addressee field. The field `kind` tells them from a message.

**[agreed]** A bulletin has its own body. It has no station as
addressee, and no station acknowledges it (p. 94/72).

**[proposed]** These formats have no body:

- a directed query (`qry.dir.dti`), by the decision on queries
  ([README section 5](README.md#5-open-items));
- the obsolete bulletin format (`bln.obsolete`).

A telemetry definition message has the telemetry definition body
([04-telemetry](04-telemetry.md)).

## 3. Message body

**[proposed]** The message body has these fields:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `addressee` | Bytes | The addressee, without its padding. | `val.msg.addr` |
| `kind` | Code | `"message"`, `"ack"` or `"rej"`. | `val.msg.kind` |
| `text` | Bytes | Only for `"message"`: the message text. | `val.msg.text` |
| `id` | Bytes | For `"message"`: the message number. For `"ack"` and `"rej"`: the number of the message that the packet acknowledges or rejects. | `val.msg.id`, `val.msg.acknum` |
| `reply_ack` | Flag | Only for `"message"`: `true` if the number has the reply-ack format. | `val.msg.replyack` |
| `ack_id` | Bytes | Only for `"message"`: the number of the message that this message also acknowledges. | `val.msg.ackid` |
| `noarchive` | Flag | `true` if the text has the bytes `!x!`. | `val.cmt.noarchive` |

**[proposed]** The record leaves out a field that has no token in the
packet. A message with an empty text has no `text`. A message without a
number has no `id`.

**[proposed]** If the packet has the marker `'{'` and no number after it,
`id` is a no-value object. Its `why` gives the `syntax` finding.

**[proposed]** `source` of the envelope is the sender of the message.

**[proposed]** The fields of an NTS line have no value rule. Its text is
in `text`, and the tokens of its fields are in `undecoded`.

## 4. Bulletin body

**[proposed]** The bulletin body has these fields:

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `kind` | Code | `"bulletin"`, `"announcement"` or `"nws"`. | `val.bln.kind` |
| `id` | Bytes | Only for `"bulletin"` and `"announcement"`: the identifier, one byte. | `val.bln.id` |
| `group` | Bytes | Only for a group bulletin: the group name. | `val.bln.group` |
| `level` | Bytes | Only for `"nws"`: the severity word. | `val.nws.level` |
| `text` | Bytes | The text. | `val.bln.text` |
| `reference` | Bytes | Only for `"nws"`: the reference identifier, without its `'{'`. | `val.nws.ref` |
| `noarchive` | Flag | `true` if the text has the bytes `!x!`. | `val.cmt.noarchive` |

**[proposed]** If the addressee of a `BLN` packet matches no bulletin
format, `kind` and `id` are no-value objects. Their `why` gives the
`syntax` finding on `bln.addr`. The record still gives `text`.

**[proposed]** An NWS bulletin whose text ends with a reference has the
finding `ambiguous` on `nws.ref`. The record gives `reference`, and
`text` does not contain its bytes.

## 5. Report time

**[proposed]** These formats have no timestamp. `report_time` follows
[01-record section 6](01-record.md#6-report-time): if the input gives a
received time, `form` is `"received"`.

## 6. Examples

### 6.1 Message

The line has the format of the first message example of APRS12c,
p. 93/71, with another addressee and another text. The record is in
strict mode. The input gives no received time.

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001::N0CALL-9 :Hello world{003",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["message"], "format": "msg.dti", "verdict": "conform", "findings": [],
 "message": {
  "addressee": {"bytes": "N0CALL-9", "from": [["msg.addr.name", 15, 23]]},
  "kind": {"code": "message", "from": [["msg.dti", 14, 15]]},
  "text": {"bytes": "Hello world", "from": [["msg.text", 25, 36]]},
  "id": {"bytes": "003", "from": [["msg.id", 37, 40]]}},
 "notes": [],
 "undecoded": []}
```

### 6.2 Group bulletin

The line has the format of the group bulletin example of APRS12c,
p. 97/75, with the padding that the format specifies
([err.bln.group-example](../legacy/08-message.md#err.bln.group-example)).

```json
{"record": 0, "mode": "strict", "line": "N0CALL>APZ001::BLN4WX   :Stand by your snowplows",
 "received": null, "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["bulletin"], "format": "bln.dti", "verdict": "conform", "findings": [],
 "bulletin": {
  "kind": {"code": "bulletin", "from": [["bln.num", 18, 19]]},
  "id": {"bytes": "4", "from": [["bln.num", 18, 19]]},
  "group": {"bytes": "WX", "from": [["bln.group", 19, 21]]},
  "text": {"bytes": "Stand by your snowplows", "from": [["bln.text", 25, 48]]}},
 "notes": [],
 "undecoded": []}
```

## 7. Open items

- **[open]** Whether a telemetry definition message also has the use
  `message` ([04-telemetry section 7](04-telemetry.md#7-open-items)).
- **[open]** A record of the obsolete bulletin format.
- **[open]** The values of the fields of an NTS line.
