# Values of telemetry fields

| | |
|---|---|
| Status | Draft. Not frozen. A paragraph, value rule or catalogue row of this file is **[proposed]** if it has no other label. An **[agreed]** item is a decision of the author. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of telemetry give values. It covers these
formats:

- the telemetry report
  ([07 section 2](07-telemetry.md#2-telemetry-report));
- the base-91 block in a comment
  ([07 section 3](07-telemetry.md#3-base-91-comment-telemetry));
- the four definition messages
  ([07 section 4](07-telemetry.md#4-telemetry-definition-messages)).

The tokens come from [07](07-telemetry.md) and [08](08-message.md). This
file adds no token and changes no finding. The rule prefix is `val`.

A base-91 block is in the comment of a packet that has a position. The
value rules of [10-values](10-values.md) give the values of the position
tokens.

These parts are outside this file:

- the message identifier of a definition message
  ([08 section 3](08-message.md));
- the use of the definitions on the values of a report (section 2.2).

## 2. Conventions

The conventions of [10-values section 2](10-values.md#2-conventions) apply
to this file. These are the terms, the value tables, the findings that
concern a value, and the effects.

### 2.1 Numbers

An analog value and a coefficient are numbers in the notation of
[amb.tlm.value](07-telemetry.md#amb.tlm.value). The notation is an
optional `'-'`, then digits with at most one `'.'`. It has at least one
digit. The notation gives a number as follows:

- `n` is the decimal number of the digits without the `'.'`.
- `f` is the number of digits after the `'.'`. Without a `'.'`, `f` is 0.
- The number is `n` at the scale 10^−`f`. With a `'-'`, `n` is negative.

The step is 1 count at that scale. For example, `-7.3` gives `n` = −73 at
the scale 0.1, and `.53` gives `n` = 53 at the scale 0.01.

### 2.2 Raw values

**[agreed]** The decoder gives each telemetry value as the packet has it.
This is the raw value of APRS12c (p. 92/72). The decoder does not apply
the coefficients of a definition message to it. It also does not apply
the bit sense, a name or a unit.

A raw value has no unit. A definition message of the same station can
give it one. That message is another packet.

### 2.3 Channels

APRS12c names the five analog channels A1 to A5 and the eight digital
channels B1 to B8 (p. 91/71). A value of this file that is a list has its
items in this order.

## 3. Telemetry report

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.tlm.seq"></a>`val.tlm.seq` | Sequence number | [`tlm.seq`](07-telemetry.md#tlm.seq) | Three digits `d` after the `'#'`: `100·d[0] + 10·d[1] + d[2]`. `MIC`: no number. | Integer, 0 to 999 | p. 88/68 |
| <a id="val.tlm.analog"></a>`val.tlm.analog` | Analog values A1 to A5 | [`tlm.analog`](07-telemetry.md#tlm.analog), five tokens | For each token: the number of its bytes without the `','` (section 2.1). The first token is A1. | Raw value. Three digits: 0 to 999. | p. 88/68 |
| <a id="val.tlm.digital"></a>`val.tlm.digital` | Digital values B1 to B8 | [`tlm.digital`](07-telemetry.md#tlm.digital) | Byte `i` of the token, from 0, gives B(`i` + 1). `'1'` is 1, `'0'` is 0 ([amb.val.tlmbits](#amb.val.tlmbits)). | Eight bits | p. 88/68, p. 89/69 |

The sequence number `MIC` is not a number. The decoder gives no sequence
number for it. This is not a finding.

The comment of a telemetry report is the `cmt.text` token after the
digital value ([`tlm.cmt`](07-telemetry.md#tlm.cmt)). It is a byte
string.

A report can end before a required field. The tokenizer then gives
`syntax` and no token for that field and for each later field. Each of
these values is `none`.

## 4. Base-91 block

`b` is the two bytes of a pair. The number of a pair is
`91·(b[0] − 33) + (b[1] − 33)`
([`b91.digit`](02-fields.md#b91.digit)).

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.tlm.b91.seq"></a>`val.tlm.b91.seq` | Sequence number | [`tlm.b91.seq`](07-telemetry.md#tlm.b91.seq) | The number of the pair. | Integer, 0 to 8280 | p. 89/69 |
| <a id="val.tlm.b91.analog"></a>`val.tlm.b91.analog` | Analog values | [`tlm.b91.analog`](07-telemetry.md#tlm.b91.analog), 1 to 5 tokens | For each token: the number of the pair. The first token is A1. | Raw value, 0 to 8280, step 1 | p. 89/69 |
| <a id="val.tlm.b91.bits"></a>`val.tlm.b91.bits` | Digital values B1 to B8 | [`tlm.b91.bits`](07-telemetry.md#tlm.b91.bits) | `n` is the number of the pair. B(`i` + 1) is bit `i` of `n`, for `i` from 0 to 7. Bit 0 is the least significant bit. | Eight bits | p. 89/69 |

A block has only the channels that it sends. The decoder gives no value
for a channel that the block does not have. This is not a finding.

Bits 8 to 12 of `n` are reserved (p. 89/69). The decoder does not read
them.

## 5. Definition messages

A definition message is a message. Its addressee is the station whose
telemetry it describes (p. 90/70).

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.tlm.def.station"></a>`val.tlm.def.station` | Station that the definition describes | [`msg.addr.name`](08-message.md#msg.addr.name) | All bytes of the token. | Byte string, 1 to 9 bytes | p. 90/70, p. 93/71 |
| <a id="val.tlm.def.kind"></a>`val.tlm.def.kind` | Kind of definition | [`tlm.parm`](07-telemetry.md#tlm.parm), [`tlm.unit`](07-telemetry.md#tlm.unit), [`tlm.eqns`](07-telemetry.md#tlm.eqns) or [`tlm.bits`](07-telemetry.md#tlm.bits) | The keyword: `PARM.` gives `parm`, `UNIT.` gives `unit`, `EQNS.` gives `eqns`, `BITS.` gives `bits`. | Code | p. 91/71, p. 92/72 |
| <a id="val.tlm.parm"></a>`val.tlm.parm` | Names of A1 to A5 and B1 to B8 | [`tlm.parm.name`](07-telemetry.md#tlm.parm.name) | For each field of the list: its bytes without the `','` before it. | List of 0 to 13 byte strings | p. 91/71 |
| <a id="val.tlm.unit"></a>`val.tlm.unit` | Units of A1 to A5 and labels of B1 to B8 | [`tlm.unit.label`](07-telemetry.md#tlm.unit.label) | As `val.tlm.parm`. | List of 0 to 13 byte strings | p. 91/71 |
| <a id="val.tlm.eqns"></a>`val.tlm.eqns` | Coefficients a, b and c of A1 to A5 | [`tlm.eqns.coef`](07-telemetry.md#tlm.eqns.coef) | For each field of the list: the number of its bytes without the `','` before it (section 2.1). | List of 0 to 15 numbers | p. 92/72 |
| <a id="val.tlm.bits.sense"></a>`val.tlm.bits.sense` | Bit sense of B1 to B8 | [`tlm.bits.sense`](07-telemetry.md#tlm.bits.sense) | Byte `i` of the token, from 0, gives B(`i` + 1). | Eight bits | p. 92/72 |
| <a id="val.tlm.bits.title"></a>`val.tlm.bits.title` | Project title | [`tlm.bits.title`](07-telemetry.md#tlm.bits.title) | All bytes of the token. | Byte string, 1 to 23 bytes | p. 92/72 |

The fields of a list are the bytes between its commas. Field `k`, from 1,
is for the channel at place `k` of the order A1 to A5, then B1 to B8. In
`val.tlm.eqns`, the fields 1 to 3 are a, b and c of A1, the fields 4 to 6
are those of A2, and so on.

A list can stop at any field (p. 91/71, p. 92/72). The decoder gives no
item for a channel that the list does not have. A field between two
commas can be empty. An empty name, unit or label is the empty byte
string.

If A1 of `PARM.` or `UNIT.` is empty, the tokenizer gives no token for
it. The field is still the first field of the list.

A list can have more fields than channels. The tokenizer then gives
`syntax` at the `','` of the first extra field. No value rule reads an
extra field.

The keyword tells which values a message has. `tlm.bits` has no title
token if no byte follows the bit sense, or its separator.

## 6. Effect of findings

This table gives the effect of each finding that concerns a value of
sections 3 to 5. For the position tokens of a packet with a base-91
block, the table of
[10-values section 10](10-values.md#10-effect-of-findings) applies. A
token that has no row has only findings with the effect `kept`.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `tlm.seq` | `syntax`, and the bytes between `'#'` and `','` are 1 to 9 digits | Sequence number | **[agreed]** `computable`: the decimal number of the digits |
| `tlm.seq` | Another `syntax` | Sequence number | `none` |
| `tlm.seq` | `unstated` (three bytes that are not digits and not `MIC`) | Sequence number | `none` |
| `tlm.analog` | `syntax` | The value of that token | `none` |
| `tlm.digital` | `syntax` | Digital values | `none` |
| `msg.addr`, `msg.addr.name` | `syntax` | Station | `none` |
| `msg.addr.name` | `unstated` (a byte other than a letter, a digit or `'-'`) | Station | `computable`: all bytes of the token |
| `msg.sep` | `syntax` | Station and every value of the text | `computable` |
| `msg.text` | `value` (the text is too long) | All | `kept` |
| `tlm.parm.name`, `tlm.unit.label` | `syntax` in the field (a byte that is not a text byte) | That name, unit or label | `none` |
| `tlm.parm.name`, `tlm.unit.label` | `value` (the field is too long) | That name, unit or label | **[agreed]** `kept` |
| `tlm.parm.name`, `tlm.unit.label` | `value` (A1 is empty) | That name, unit or label | `computable`: the empty byte string |
| `tlm.parm.name`, `tlm.unit.label`, `tlm.eqns.coef` | `syntax` at the `','` of an extra field | The values of the list | `kept` |
| `tlm.eqns.coef` | `syntax` in the field | That coefficient | `none` |
| `tlm.eqns.coef` | `unstated` (not a number of section 2.1) | That coefficient | `none` |
| `tlm.bits.sense` | `syntax` | Bit sense | `none` |
| `tlm.bits.title` | `syntax` | Title | `none` |
| `tlm.bits.title` | `value` (more than 23 bytes) | Title | `computable`: all bytes of the token |
| `tlm.b91` | `ambiguous` ([amb.tlm.b91.order](07-telemetry.md#amb.tlm.b91.order)) | Every value of the block | `computable` |

**[agreed]** A name, a unit or a label that is longer than its byte
count keeps its value in both modes. APRS12c says that many
implementations ignore these counts, and that a new application handles
what is in common use (p. 91/71). The `value` finding of the tokenizer
stays.

The fields of a telemetry report are between commas. Thus a `syntax`
finding in one field does not move a later field. It concerns only the
value of its own field.

A report can end directly after an analog value, with no `','`. The
tokenizer then gives `syntax` at the end of that token. The value is
`none`, because the end of the report can cut the number short. In a
report with fewer than five analog values, these bytes can also be the
digital value.

The byte at the place of `msg.sep` can be another byte than `':'`. The
text then still starts at its fixed place
([`msg.sep`](08-message.md#msg.sep)). This is why the effect is
`computable` and not `none`.

A base-91 block is in a position report or in Mic-E. A `syntax` finding
on the timestamp of a position report concerns every value from a later
token ([10-values section 2.3](10-values.md#23-findings-that-concern-a-value)).
These include the values of the block.

## 7. Catalogue

The last column of this catalogue tells what the decoder does.

| ID | Pages | What APRS12c leaves open | Class | Rule | What the decoder does |
|---|---|---|---|---|---|
| <a id="amb.val.tlmbits"></a>`amb.val.tlmbits` | p. 88/68, p. 89/69, p. 92/72 | APRS12c does not say which of the eight bytes of the digital value is B1. The diagram of the `BITS.` message has B1 first. The example of the base-91 block writes the number 1 as `10000000` and says that B1 is 1. | unstated | 2 | The first byte is B1. The decoder gives the value, with this note. |

## 8. Reviewed exceptions

None.

## 9. Open items

- The effect of `syntax` on `tlm.digital`. This file gives `none` for all
  eight bits, also if only one byte is wrong.
- The effect of `value` on a title, and on an empty A1. This file gives
  `computable`, as
  [11-values-object](11-values-object.md#6-effect-of-findings) does for
  an Item name.
- The effect of `ambiguous` on `tlm.b91`.
- The message identifier of a definition message has no value rule yet.
  The value file of messages will give it.
