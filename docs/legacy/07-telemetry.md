# Telemetry

| | |
|---|---|
| Status | Draft. Not frozen. |
| Reference | `APRS12c.pdf` chapter 13, p. 88/68 to p. 92/72, with Appendix 1 p. 134/110 and p. 135/111, in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers the telemetry report (`'T'`), base-91 telemetry in
comments, and the text of the four telemetry definition messages.
[01-frame.md](01-frame.md) classifies the identifier `'T'`. The
definition messages are messages.
[08-message.md](08-message.md) delimits their addressee, text and
message identifier. This file reads their text.

Base-91 digits are [`b91.digit`](02-fields.md#b91.digit). Inside a
block, `'|'` is the delimiter (p. 88/68). Thus the digits of a pair are
in the range `'!'` to `'{'`.

Offsets in section 2 count from the `'T'` at offset 0.

## 2. Telemetry report

A telemetry report contains `'T'`, a sequence number, five analog
values, eight digital bits and an optional comment (p. 88/68,
p. 134/110). Each token includes the comma that ends it.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.dti"></a>`tlm.dti` | Data type identifier | `'T'`. | Yes | 1 byte | p. 31/17, p. 88/68 |
| <a id="tlm.seq"></a>`tlm.seq` | Sequence number | `'#'`, a 3-byte value, `','`. `#MIC` can be without its `','` ([err.tlm.seq](#err.tlm.seq)). Another width gives `syntax` at the first byte that fails. A value other than three digits or `MIC` gives `unstated` ([amb.tlm.seq](#amb.tlm.seq)). | Yes | The `','`, or the `'C'` of `MIC` | p. 88/68, p. 153/129 |
| <a id="tlm.analog"></a>`tlm.analog` | Analog value, five times | Three digits or a relaxed number ([amb.tlm.value](#amb.tlm.value), [err.tlm.analog](#err.tlm.analog)), then `','`. Other bytes give `syntax`. An empty value also gives `syntax`. The range 000 to 999 permits all values of three digits. | Yes | The `','` | p. 88/68, p. 134/110, p. 157/133 |
| <a id="tlm.digital"></a>`tlm.digital` | Digital value | <a id="amb.tlm.count"></a>8 bytes, each `'0'` or `'1'`, directly after the fifth value. Other bytes give `syntax`. | Yes | 8 bytes | p. 88/68 |
| <a id="tlm.cmt"></a>`tlm.cmt` | Comment | The rest of the field, directly after the eighth bit, with no separator (p. 34/20). Thus a `','` or SP there is its first byte. The tokenizer reads it as [`cmt.text`](02-fields.md#cmt.text) with no length limit. It does not look for a DAO, data extension, base-91 block or frequency, because their pages name only position comments. | No | End of field | p. 34/20, p. 88/68 |

If a report ends before a required field, the tokenizer gives `syntax`
where that field was expected. The token of byte 0 has the rule ID
`tlm.dti`. In a definition message, the token of byte 0 has the rule ID
[`tlm.def.dti`](#tlm.def.dti).

## 3. Base-91 comment telemetry

A block can be in the comment of the three formats that APRS12c names
(p. 88/68, [amb.tlm.b91.where](#amb.tlm.b91.where)):

- an uncompressed position report, a DF report included;
- a compressed position report;
- a Mic-E status text.

The block follows the text. Only a DAO, and in Mic-E the device suffix,
can follow the block (p. 88/68).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.b91"></a>`tlm.b91` | Telemetry block | `'\|'`, 2 to 7 pairs of base-91 digits other than `'\|'`, `'\|'`. The pairs are tokens one level below the block. | No | The second `'\|'` | p. 88/68, p. 89/69 |
| <a id="tlm.b91.seq"></a>`tlm.b91.seq` | Sequence counter | The first pair. | Yes | 2 bytes | p. 89/69 |
| <a id="tlm.b91.analog"></a>`tlm.b91.analog` | Analog channel | Pairs 2 to 6. At least one is present. | Yes | 2 bytes | p. 89/69 |
| <a id="tlm.b91.bits"></a>`tlm.b91.bits` | Binary channels | The seventh pair, only after all five analog pairs. | No | 2 bytes | p. 89/69 |

Two digits have a maximum value of 8280, which is the limit that
APRS12c specifies. Thus no pair is out of range. A run between bars is
comment text, with no finding, in these cases
([amb.tlm.b91.order](#amb.tlm.b91.order)):

- It is not 4 to 14 base-91 digits of even count.
- It is followed by anything other than a
  [`cmt.dao`](02-fields.md#cmt.dao) and, in Mic-E, the device suffix
  ([`mice.type.suffix`](04-mic-e.md#mice.type.suffix)).

The tokenizer finds the block before the other comment fields. It looks
for no comment field inside the block, `'!x!'` included. The bytes of
the block count toward the length limit of the comment. The bytes of a
DAO after the block do not count
([err.cmt.daolimit](02-fields.md#err.cmt.daolimit)).

## 4. Telemetry definition messages

The addressee of the four messages is the station whose telemetry they
describe (p. 90/70). 08 delimits their text. The text starts with one
of the keywords `PARM.`, `UNIT.`, `EQNS.` or `BITS.`, in upper case
<a id="amb.tlm.keyword"></a>(p. 91/71, p. 92/72). If the text starts
with one of these keywords in another case, it is ordinary message text,
with no finding. Bulletins and NWS bulletins are never definition
messages ([08-message.md](08-message.md)).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.def.dti"></a>`tlm.def.dti` | Identifier of a definition message | The `':'` of a message whose text 08 passes to this file. The token has this rule ID in place of [`msg.dti`](08-message.md#msg.dti). | Yes | 1 byte | p. 31/17, p. 90/70 |

The tokens below are inside the message text token. Each list field
includes the comma before it. The bytes of a field are the bytes that 08
permits in message text, other than `','`. Another byte gives one
`syntax` finding on the field, at the first such byte. The text limit of
[`msg.text`](08-message.md#msg.text) applies to the whole text
([err.tlm.parmlen](#err.tlm.parmlen)).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.parm"></a>`tlm.parm` | Parameter names | `PARM.`, then 0 to 13 fields for A1 to A5 and B1 to B8, in that order ([amb.tlm.meta](#amb.tlm.meta)). A fourteenth field gives `syntax` at its `','`. | Keyword | End of text | p. 91/71, p. 134/110 |
| <a id="tlm.parm.name"></a>`tlm.parm.name` | One name | A1: 1 to 7 bytes. A2 to B8: `','` and the name. The counts include the comma. A longer name gives `value`. An empty A1 before a `','` also gives `value`. | No | Next `','` or end | p. 91/71 |
| <a id="tlm.unit"></a>`tlm.unit` | Units and labels | `UNIT.`, then fields as in `tlm.parm`. | Keyword | End of text | p. 91/71, p. 135/111 |
| <a id="tlm.unit.label"></a>`tlm.unit.label` | One unit or label | As `tlm.parm.name`. | No | Next `','` or end | p. 91/71 |
| <a id="tlm.eqns"></a>`tlm.eqns` | Equation coefficients | `EQNS.`, then 0 to 15 fields: a, b and c for A1 to A5, in that order. A sixteenth field gives `syntax` at its `','`. | Keyword | End of text | p. 92/72, p. 135/111 |
| <a id="tlm.eqns.coef"></a>`tlm.eqns.coef` | One coefficient | A number of n bytes. A coefficient that is not a relaxed number gives `unstated` at its first byte ([amb.tlm.eqns](#amb.tlm.eqns)). | No | Next `','` or end | p. 92/72 |
| <a id="tlm.bits"></a>`tlm.bits` | Bit sense and project title | `BITS.`, then the fields below. | Keyword | End of text | p. 92/72, p. 135/111 |
| <a id="tlm.bits.sense"></a>`tlm.bits.sense` | Bit sense | 8 bytes, each `'0'` or `'1'`, for B1 to B8. Other bytes or missing bytes give `syntax`. | Yes | 8 bytes | p. 92/72 |
| <a id="tlm.bits.title"></a>`tlm.bits.title` | Project title | 0 to 23 bytes after the bits, or after a `','` there ([amb.tlm.bitsep](#amb.tlm.bitsep)). A longer title gives `value`. | No | End of text | p. 92/72 |

The table below gives the maximum length of a name, unit or label,
without the comma. The values come from the byte counts of p. 91/71.

| Channel | A1 | A2 | A3, A4 | A5 | B1 | B2 | B3 to B5 | B6 to B8 |
|---|---|---|---|---|---|---|---|---|
| Bytes | 7 | 6 | 5 | 4 | 5 | 4 | 3 | 2 |

## 5. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.tlm.seq"></a>`amb.tlm.seq` | p. 88/68 | The sequence number is a 3-character value, "typically" three digits or `MIC`. APRS12c says nothing about other values. | unstated | 2 | Three bytes other than three digits or `MIC` give `unstated`. This includes `mic`. |
| <a id="amb.tlm.value"></a>`amb.tlm.value` | p. 88/68, p. 134/110 | APRS12c describes longer values with decimal points and an optional leading minus. It does not specify their exact syntax, for example a trailing point, `'+'` or an exponent. | ambiguous | 1 | An optional `'-'`, then digits with at most one `'.'` and at least one digit, gives no finding. This includes `1.`. A `'+'`, an exponent or an empty value gives `syntax`. |
| <a id="amb.tlm.b91.where"></a>`amb.tlm.b91.where` | p. 88/68 | Chapter 13 names three position formats. It asks itself if the omission of Objects is intentional. | unstated | 2 | The tokenizer looks for blocks in those formats only. In other formats, a run that matches the block format is text, with no finding. |
| <a id="amb.tlm.b91.order"></a>`amb.tlm.b91.order` | p. 35/21, p. 88/68 | The DAO can be at any place in a position comment (p. 35/21). But the block comes before any DAO (p. 88/68). | conflict | 3, 4 | A DAO before or after the block gives no finding. A block can be followed by a DAO candidate while the comment contains other candidates. Then it is a block only in the interpretation that keeps that candidate ([amb.cmt.dao](02-fields.md#amb.cmt.dao)). The tokenizer then gives `ambiguous` on `tlm.b91` at its first byte. |
| <a id="amb.tlm.meta"></a>`amb.tlm.meta` | p. 91/71 | APRS12c does not say if a list can stop before its first field. It says that implementations widely ignore the name lengths. | ambiguous | 1 | A keyword with no list gives no finding. The byte counts are still limits, because the note gives advice to receivers. Thus a longer field gives `value`. |
| <a id="amb.tlm.eqns"></a>`amb.tlm.eqns` | p. 92/72 | APRS12c does not specify the notation of a coefficient. The example contains integers, decimals, a leading point and a minus. | unstated | 2 | A coefficient that is not a relaxed number gives `unstated`. This includes an empty coefficient. |
| <a id="amb.tlm.bitsep"></a>`amb.tlm.bitsep` | p. 92/72, p. 135/111 | In the example, a `','` after the bits is a separator. In the diagram, it is part of the title. | ambiguous | 4 | The separator restricts the byte, so the separator is the stricter format. The title starts after the separator, and its limit counts from there. The tokenizer gives no finding, because every such message has the same ambiguity. |
| <a id="err.tlm.seq"></a>`err.tlm.seq` | p. 88/68, p. 134/110, p. 153/129 | The description in APRS12c permits `MIC` without its comma. The diagrams specify five bytes, `#nnn,` in Appendix 1. | conflict | 3 | `#MIC` with or without its `','` gives no finding. |
| <a id="err.tlm.analog"></a>`err.tlm.analog` | p. 88/68, p. 134/110 | The diagrams specify 4-byte values. The third example contains `45.7` and `-7.3`. | conflict | 3 | The tokenizer accepts both three digits and the relaxed number. |
| <a id="err.tlm.bits"></a>`err.tlm.bits` | p. 92/72 | The BITS diagram has no separator. The example has `','`. | conflict | 3 | The tokenizer accepts both. It makes the tokens as [amb.tlm.bitsep](#amb.tlm.bitsep) says. |
| <a id="err.tlm.parmlen"></a>`err.tlm.parmlen` | p. 91/71, p. 93/71, p. 135/111 | The byte counts of `PARM.` and `UNIT.` permit a 68-byte text. Message text has a maximum of 67 characters. | conflict | 3 | If all fields of a text are within their counts, the tokenizer withdraws the `value` finding of `msg.text`. |
| <a id="err.tlm.b91count"></a>`err.tlm.b91count` | p. 34/20, p. 88/68 | This is the same erratum as [err.b91.users](02-fields.md#err.b91.users). | conflict | 3 | The erratum affects no bytes. |

## 6. Reviewed exceptions

None.

## 7. Open items

None.
