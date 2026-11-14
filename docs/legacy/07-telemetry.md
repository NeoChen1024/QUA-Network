# Telemetry

| | |
|---|---|
| Status | Draft. Not frozen. |
| Reference | `APRS12c.pdf` chapter 13, p. 88/68 to p. 92/72, with Appendix 1 p. 134/110 and p. 135/111, in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, general rules and tokenizer model: [README](README.md). |

## 1. Scope

The telemetry report (`'T'`), base-91 telemetry in comments, and the text
of the four telemetry definition messages. The identifier `'T'` is
classified by [01-frame.md](01-frame.md); the definition messages travel
as messages, and [08-message.md](08-message.md) delimits their addressee,
text and message identifier and hands the text here. Base-91 digits are
[`b91.digit`](02-fields.md#b91.digit); inside a block `'|'` is the
delimiter (p. 88/68), so a pair's digits run from `'!'` to `'{'`.

Offsets in section 2 count from the `'T'` at offset 0.

## 2. Telemetry report

`'T'`, a sequence number, five analog values, eight digital bits and an
optional comment (p. 88/68, p. 134/110). Each token includes the comma
that ends it.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.dti"></a>`tlm.dti` | Data type identifier | `'T'`. | Yes | 1 byte | p. 31/17, p. 88/68 |
| <a id="tlm.seq"></a>`tlm.seq` | Sequence number | `'#'`, a 3-byte value, `','`; `#MIC` may lack its `','` ([err.tlm.seq](#err.tlm.seq)). Another width gives `syntax` at the first byte that fails; a value other than three digits or `MIC` gives `unstated` ([amb.tlm.seq](#amb.tlm.seq)). | Yes | The `','`, or the `'C'` of `MIC` | p. 88/68, p. 153/129 |
| <a id="tlm.analog"></a>`tlm.analog` | Analog value, five times | Three digits, or a relaxed number ([amb.tlm.value](#amb.tlm.value), [err.tlm.analog](#err.tlm.analog)), then `','`. Other bytes, an empty value included, give `syntax`. The range 000 to 999 admits every three digits. | Yes | The `','` | p. 88/68, p. 134/110, p. 157/133 |
| <a id="tlm.digital"></a>`tlm.digital` | Digital value | <a id="amb.tlm.count"></a>8 bytes, each `'0'` or `'1'`, directly after the fifth value; other bytes give `syntax`. | Yes | 8 bytes | p. 88/68 |
| <a id="tlm.cmt"></a>`tlm.cmt` | Comment | The rest, directly after the eighth bit with no separator (p. 34/20), so a `','` or SP there is its first byte. Read as [`cmt.text`](02-fields.md#cmt.text) with no length limit; no DAO, data extension, base-91 block or frequency is looked for, as their pages name position comments only. | No | End of field | p. 34/20, p. 88/68 |

A report that ends before a required field gives `syntax` where that
field was expected. The token of offset 0 carries `tlm.dti`; a definition
message carries [`tlm.def.dti`](#tlm.def.dti).

## 3. Base-91 comment telemetry

A block may stand in the comment of an uncompressed position report (a DF
report included), a compressed position report and a Mic-E status text,
the three formats p. 88/68 names
([amb.tlm.b91.where](#amb.tlm.b91.where)). It follows the free text, and
only a DAO and, in Mic-E, the device suffix may follow it (p. 88/68).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.b91"></a>`tlm.b91` | Telemetry block | `'\|'`, 2 to 7 pairs of base-91 digits other than `'\|'`, `'\|'`; the pairs are tokens one level deeper. | No | The second `'\|'` | p. 88/68, p. 89/69 |
| <a id="tlm.b91.seq"></a>`tlm.b91.seq` | Sequence counter | The first pair. | Yes | 2 bytes | p. 89/69 |
| <a id="tlm.b91.analog"></a>`tlm.b91.analog` | Analog channel | Pairs 2 to 6; at least one. | Yes | 2 bytes | p. 89/69 |
| <a id="tlm.b91.bits"></a>`tlm.b91.bits` | Binary channels | The seventh pair, only after all five analog pairs. | No | 2 bytes | p. 89/69 |

Two digits give at most 8280, the stated limit, so no pair is out of
range. A run between bars that is not 4 to 14 base-91 digits of even
count, or that is followed by anything but a [`cmt.dao`](02-fields.md#cmt.dao)
and, in Mic-E, the device suffix
([`mice.type.suffix`](04-mic-e.md#mice.type.suffix)), is comment text,
with no finding ([amb.tlm.b91.order](#amb.tlm.b91.order)). The block is
found before the other comment items, and none is looked for inside it,
`'!x!'` included; its bytes count toward the comment's length limit, and
those of a DAO after it do not
([err.cmt.daolimit](02-fields.md#err.cmt.daolimit)).

## 4. Telemetry definition messages

The four messages are addressed to the station whose telemetry they
describe (p. 90/70). Their text, as 08 delimits it, starts with one of
the keywords `PARM.`, `UNIT.`, `EQNS.` or `BITS.`, in upper case
<a id="amb.tlm.keyword"></a>(p. 91/71, p. 92/72); text that starts with
one of them in another case is ordinary message text, with no finding.
Bulletins and NWS bulletins are never definition messages
([08-message.md](08-message.md)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.def.dti"></a>`tlm.def.dti` | Identifier of a definition message | `':'` of a message whose text 08 hands here; carried in place of [`msg.dti`](08-message.md#msg.dti). | Yes | 1 byte | p. 31/17, p. 90/70 |

The tokens below lie inside the message text token. Each list field
includes the comma before it. The bytes of a field are those that 08
allows in message text, other than `','`; another byte gives one `syntax`
finding on the field, at the first such byte. The text limit of
[`msg.text`](08-message.md#msg.text) applies to the whole text
([err.tlm.parmlen](#err.tlm.parmlen)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.parm"></a>`tlm.parm` | Parameter names | `PARM.`, then 0 to 13 fields, for A1 to A5 and B1 to B8 in that order ([amb.tlm.meta](#amb.tlm.meta)). A fourteenth field gives `syntax` at its `','`. | Keyword | End of text | p. 91/71, p. 134/110 |
| <a id="tlm.parm.name"></a>`tlm.parm.name` | One name | A1: 1 to 7 bytes; A2 to B8: `','` and the name, the counts including the comma. A longer name, or an empty A1 before a `','`, gives `value`. | No | Next `','` or end | p. 91/71 |
| <a id="tlm.unit"></a>`tlm.unit` | Units and labels | `UNIT.`, then fields as `tlm.parm`. | Keyword | End of text | p. 91/71, p. 135/111 |
| <a id="tlm.unit.label"></a>`tlm.unit.label` | One unit or label | As `tlm.parm.name`. | No | Next `','` or end | p. 91/71 |
| <a id="tlm.eqns"></a>`tlm.eqns` | Equation coefficients | `EQNS.`, then 0 to 15 fields, a, b and c for A1 to A5 in that order. A sixteenth field gives `syntax` at its `','`. | Keyword | End of text | p. 92/72, p. 135/111 |
| <a id="tlm.eqns.coef"></a>`tlm.eqns.coef` | One coefficient | A number of n bytes; one that is not a relaxed number gives `unstated` at its first byte ([amb.tlm.eqns](#amb.tlm.eqns)). | No | Next `','` or end | p. 92/72 |
| <a id="tlm.bits"></a>`tlm.bits` | Bit sense and project title | `BITS.`, then the parts below. | Keyword | End of text | p. 92/72, p. 135/111 |
| <a id="tlm.bits.sense"></a>`tlm.bits.sense` | Bit sense | 8 bytes, each `'0'` or `'1'`, B1 to B8; other or missing bytes give `syntax`. | Yes | 8 bytes | p. 92/72 |
| <a id="tlm.bits.title"></a>`tlm.bits.title` | Project title | 0 to 23 bytes after the bits, or after a `','` there ([amb.tlm.bitsep](#amb.tlm.bitsep)); longer gives `value`. | No | End of text | p. 92/72 |

Longest name, unit or label, the comma not counted, from the byte counts
of p. 91/71:

| Channel | A1 | A2 | A3, A4 | A5 | B1 | B2 | B3 to B5 | B6 to B8 |
|---|---|---|---|---|---|---|---|---|
| Bytes | 7 | 6 | 5 | 4 | 5 | 4 | 3 | 2 |

## 5. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.tlm.seq"></a>`amb.tlm.seq` | p. 88/68 | The sequence is a 3-character value, "typically" three digits or `MIC`; other values are not addressed. | unstated | 2 | Three bytes other than three digits or `MIC`, `mic` included, give `unstated`. |
| <a id="amb.tlm.value"></a>`amb.tlm.value` | p. 88/68, p. 134/110 | Longer values with decimal points and an optional leading minus are described, not their exact syntax: a trailing point, `'+'`, an exponent. | ambiguous | 1 | An optional `'-'`, then digits with at most one `'.'` and at least one digit, conforms, `1.` included; `'+'`, an exponent or an empty value gives `syntax`. |
| <a id="amb.tlm.b91.where"></a>`amb.tlm.b91.where` | p. 88/68 | Chapter 13 names three position formats and asks itself whether leaving out objects was intended. | unstated | 2 | Blocks are looked for in those formats only; elsewhere a run of block shape is text, with no finding. |
| <a id="amb.tlm.b91.order"></a>`amb.tlm.b91.order` | p. 35/21, p. 88/68 | The DAO may stand anywhere in a position comment (p. 35/21); the block comes before any DAO (p. 88/68). | conflict | 3, 4 | A DAO before or after the block conforms. A block followed by a DAO candidate while other candidates stand in the comment is a block only under the reading that keeps that candidate ([amb.cmt.dao](02-fields.md#amb.cmt.dao)): `ambiguous` on `tlm.b91` at its first byte. |
| <a id="amb.tlm.meta"></a>`amb.tlm.meta` | p. 91/71 | Whether a list may stop before its first field; the name lengths are said to be widely ignored. | ambiguous | 1 | A keyword with no list conforms, with no finding. The byte counts stay limits: the note advises receivers, so a longer field gives `value`. |
| <a id="amb.tlm.eqns"></a>`amb.tlm.eqns` | p. 92/72 | The notation of a coefficient is not stated; the example has integers, decimals, a leading point and a minus. | unstated | 2 | A coefficient that is not a relaxed number, an empty one included, gives `unstated`. |
| <a id="amb.tlm.bitsep"></a>`amb.tlm.bitsep` | p. 92/72, p. 135/111 | A `','` after the bits is a separator by the example and part of the title by the diagram. | ambiguous | 4 | The separator, which constrains the byte, is the more specific reading: the title starts after it and its limit counts from there. No finding, as every such message carries the question. |
| <a id="err.tlm.seq"></a>`err.tlm.seq` | p. 88/68, p. 134/110, p. 153/129 | The text lets `MIC` lack its comma; the diagrams fix five bytes, `#nnn,` in Appendix 1. | conflict | 3 | `#MIC` with or without its `','` conforms. |
| <a id="err.tlm.analog"></a>`err.tlm.analog` | p. 88/68, p. 134/110 | The diagrams fix 4-byte values; the third example has `45.7` and `-7.3`. | conflict | 3 | Three digits and the relaxed number both conform. |
| <a id="err.tlm.bits"></a>`err.tlm.bits` | p. 92/72 | The BITS diagram has no separator; the example has `','`. | conflict | 3 | Both conform; tokens by [amb.tlm.bitsep](#amb.tlm.bitsep). |
| <a id="err.tlm.parmlen"></a>`err.tlm.parmlen` | p. 91/71, p. 93/71, p. 135/111 | The `PARM.` and `UNIT.` byte counts allow a 68-byte text; message text has at most 67. | conflict | 3 | A text whose fields are all within their counts conforms; the `value` finding of `msg.text` is withdrawn for it. |
| <a id="err.tlm.b91count"></a>`err.tlm.b91count` | p. 34/20, p. 88/68 | The same as [err.b91.users](02-fields.md#err.b91.users). | conflict | 3 | No bytes are affected. |

## 6. Reviewed exceptions

None.

## 7. Open items

None.
