# Telemetry

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` chapter 13, p. 88/68 to p. 92/72, with Appendix 1 p. 134/110 and p. 135/111, in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, tokenizer model and decoder commits: [README](README.md). |

## 1. Scope

This file reads APRS12c chapter 13: the telemetry report with identifier
`'T'`, base-91 telemetry carried in comments, and the text of the four
telemetry definition messages.

The identifier `'T'` is classified by [01-frame.md](01-frame.md). The
definition messages travel in the message format of
[08-message.md](08-message.md), which delimits their addressee, their
text and any message identifier, and hands the text here by the order of
its [section 2.1](08-message.md#21-kind-of-packet); this file reads the
text. Base-91 digits are [`b91.digit`](02-fields.md#b91.digit), `'!'` to
`'{'`.

Offsets in section 2 count from the first byte of the information field,
which holds `'T'` at offset 0.

## 2. Telemetry report

The report is `'T'`, a sequence number, five analog values, eight digital
bits and an optional comment (p. 88/68, p. 134/110). Each token below
includes the comma that ends it, as the diagrams count it.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.dti"></a>`tlm.dti` | Data type identifier | `'T'` at offset 0. | Required | 1 byte | p. 31/17, p. 88/68 |
| <a id="tlm.seq"></a>`tlm.seq` | Sequence number | `'#'`, then three digits and `','`, or `'MIC'` with an optional `','`. A digit run of another length is a delimited field outside its stated length and gives a `value` finding ([amb.tlm.seq](#amb.tlm.seq); [README section 3](README.md#3-tokenizer-model), Kinds by situation). | Required | The `','`, or the `'C'` of `MIC` when no comma follows | p. 88/68, p. 153/129 |
| <a id="tlm.analog"></a>`tlm.analog` | Analog value, five times | Three digits, 000 to 999, then `','`. **[agreed]** Also a relaxed number: an optional `'-'`, then digits, or digits `'.'` digits, or `'.'` digits, with no finding. Anything else, an empty value included, gives `syntax` ([amb.tlm.value](#amb.tlm.value); an empty value is a missing field, [README section 3](README.md#3-tokenizer-model), Kinds by situation). | Required | The `','` | p. 88/68, p. 134/110, p. 157/133 |
| <a id="tlm.digital"></a>`tlm.digital` | Digital value | Eight bytes, each `'0'` or `'1'`. | Required | 8 bytes | p. 88/68 |
| <a id="tlm.cmt"></a>`tlm.cmt` | Comment | The rest, directly after the eighth bit, read as [`cmt.text`](02-fields.md#cmt.text). No length limit is stated. | Optional | End of information field | p. 88/68, p. 152/128 |

The token of byte 0 carries `tlm.dti`, so that the tokens show the
packet as a telemetry report
([README section 3](README.md#3-tokenizer-model)). Base-91 telemetry
has no identifier of its own: it is found in a comment. A definition
message shares the identifier `':'` with the other message kinds and
carries [`tlm.def.dti`](#tlm.def.dti) (section 4).

A report that ends before its required fields are all present has too
few fields and gives `syntax` at the end, where the first byte of the
first missing field was expected; an empty analog value is a missing
field and gives `syntax` where its first byte was expected
([README section 3](README.md#3-tokenizer-model), Output; Kinds by
situation). **[proposed]** All five analog values and the digital value
are required ([amb.tlm.count](#amb.tlm.count)).

A `','` or SP directly after the eighth bit is the first byte of the
comment and gives no finding: no text of APRS12c puts a separator there
([amb.tlm.count](#amb.tlm.count);
[README section 3](README.md#3-tokenizer-model), Separators and
padding). An earlier draft gave such a byte an `ambiguous` finding.

Positions of findings, where the rows leave them open, by
[README section 3](README.md#3-tokenizer-model) (Output, Placing a
finding):

- `tlm.seq`: a digit run longer than three gives `value` at its fourth
  digit, the first byte past the limit, and a shorter one where its
  first missing digit was expected, which is the `','`; a byte that
  fits neither form gives `syntax` there, and `'#'` directly followed
  by `','` gives it at that `','`. An earlier draft placed the `value`
  finding of a short run at its first digit. The `syntax` byte is the
  first byte that fails, the first one at which the bytes fit neither
  `'#'` and digits nor `'#MIC'`, which is the later of the two places
  where the forms stop matching: `#MIX,` gives it at the `'X'`, `#M12,`
  at the `'1'`, and `#MI,` at the `','` where `'C'` was expected. A
  field that does not start with `'#'` gives it at its first byte. The
  `','` fixes the extent of the field. When no `','` follows and the
  field is not `'#'` followed only by digits, nothing delimits the
  sequence, its extent cannot be told, and the bytes from offset 1 to
  the end are residue; this includes a field that does not start with
  `'#'`, such as a `'T'` followed by plain text.
- `tlm.analog` and `tlm.eqns.coef`: `syntax` is at the first byte where
  the bytes stop fitting the relaxed number, or at the `','` or end of
  the text when a byte is missing there (an empty value, `1.`, `-`). A
  value that runs to the end of the field with no `','` after it gives
  `syntax` at the end, where the `','` was expected. The optional `'-'`
  may stand before each of the three forms, as the value `-7.3` of the
  third example on p. 88/68 requires: the example fills a gap of the
  description ([README section 3](README.md#3-tokenizer-model), Pages
  that disagree).

**[proposed]** `tlm.cmt` is searched for the items of
[02-fields.md](02-fields.md#82-items-found-inside-a-comment) section
8.2, as any `cmt.text` is, with no length limit. **[agreed]** The search
of [amb.ext.count](02-fields.md#amb.ext.count) does not cover it: a
report without a position has no data extension under any reading. No
base-91 block (section 3) and no frequency
([09-other.md section 7](09-other.md#7-frequency-specification)) is
looked for in it. An intermediate draft extended that search to
`tlm.cmt`; it was dropped when 02 limited the search to reports that
carry a position.

The original range of an analog value is 000 to 255; version 1.2 allows
000 to 999 (p. 88/68, p. 157/133), so no three-digit value gives a
finding. Which byte of `tlm.digital` is B1 is not stated in the report
section; the BITS diagram runs B1 to B8 from left to right (p. 92/72).
That is a matter for decoding and gives no finding.

## 3. Base-91 comment telemetry

A block of base-91 telemetry can stand in the comment of an uncompressed
position, a compressed position or a Mic-E packet. It comes after the
free text and before any `!DAO!` or Mic-E device suffix (p. 88/68 to
p. 90/70).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.b91"></a>`tlm.b91` | Telemetry block | `'\|'` (0x7C), 2 to 7 pairs of [`b91.digit`](02-fields.md#b91.digit) bytes, `'\|'`: 4 to 14 bytes between the bars, an even number. The pairs are tokens one level deeper. | Optional | The second `'\|'` | p. 88/68, p. 89/69 |
| <a id="tlm.b91.seq"></a>`tlm.b91.seq` | Sequence counter | The first pair. | Required | 2 bytes | p. 89/69 |
| <a id="tlm.b91.analog"></a>`tlm.b91.analog` | Analog channel | Pairs 2 to 6; at least one. | Required | 2 bytes | p. 89/69 |
| <a id="tlm.b91.bits"></a>`tlm.b91.bits` | Binary channels | The seventh pair, present only after all five analog pairs. The least significant bit is B1 and the eighth B8; bits 9 to 13 are reserved. | Optional | 2 bytes | p. 89/69 |

Two base-91 digits give 0 to 8280, the stated limit, so no pair can be
out of range. A run between bars of odd length, of fewer than 4 or more
than 14 bytes, or holding a byte outside `'!'` to `'{'`, is not a block
and stays comment text.

Finding a block:

- A run that fits `tlm.b91` is a block only when nothing follows it
  but an optional [`cmt.dao`](02-fields.md#cmt.dao) and, in Mic-E, the
  device suffix [`mice.type.suffix`](04-mic-e.md#mice.type.suffix). A
  run followed by anything else is comment text, with no finding, under
  every listed reading of [amb.tlm.b91.order](#amb.tlm.b91.order)
  ([README section 3](README.md#3-tokenizer-model)). At most one run in a
  comment can be a block ([amb.tlm.b91.where](#amb.tlm.b91.where)).
- In Mic-E, the device suffix is taken off first and only the bytes before
  it are searched ([04-mic-e.md](04-mic-e.md#amb.mice.pipe)).
- **[proposed]** A block is one of the items found inside a comment of
  [02-fields.md](02-fields.md#82-items-found-inside-a-comment) section
  8.2, searched for independently of the others. A
  [`cmt.dao`](02-fields.md#cmt.dao) candidate that overlaps a block is
  therefore recorded too, and both get an `ambiguous` finding. Whether
  that is wanted is open in [02-fields.md](02-fields.md#11-open-items).
- The bytes of a block count towards the comment's length limit, as the
  bytes of every item found inside a field do
  ([README section 3](README.md#3-tokenizer-model), Length limits);
  whether those of a DAO count is decided in
  [amb.cmt.length](02-fields.md#amb.cmt.length).

Where blocks are looked for:

- **[proposed]** In the comment of the position reports of
  [03-position.md](03-position.md), uncompressed and compressed, and in
  the Mic-E status text.
- **[proposed]** In the comment of object and item reports, a candidate
  is recorded with an `unstated` finding, since chapter 13 names only the
  three position formats and itself asks why objects are left out
  ([amb.tlm.b91.where](#amb.tlm.b91.where)).
- Nowhere else.

## 4. Telemetry definition messages

The four messages are addressed to the station whose telemetry they
describe, which need not be the sender (p. 90/70). Their text, as
[08-message.md](08-message.md) delimits it, starts with a five-byte
keyword.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.def.dti"></a>`tlm.def.dti` | Identifier of a definition message | `':'` at offset 0 of a message whose text 08 hands here (case 4 of its [section 2.1](08-message.md#21-kind-of-packet)). The token of byte 0 carries this ID in place of [`msg.dti`](08-message.md#msg.dti), as the identifier rule of the most specific format ([README section 3](README.md#3-tokenizer-model), Output). | Required | 1 byte | p. 31/17, p. 90/70 |

The tokens of the table below lie inside the message text token.

**[proposed]** The keyword is exactly `PARM.`, `UNIT.`, `EQNS.` or
`BITS.` in upper case; text starting otherwise is an ordinary message,
with an `ambiguous` finding when it starts with one of the keywords in
another case and the rest of it would fit that message
([amb.tlm.keyword](#amb.tlm.keyword)). Bulletin and NWS
addressees are tested first by 08, so their text is never a definition
message; any other addressee does not change the reading.
An earlier draft gave an addressee starting with `NWS_`, `SKY`, `CWA`
or `BOM` the `ambiguous` finding of
[amb.nws.addressee](08-message.md#amb.nws.addressee) in a definition
message; the reading of that entry that took such an addressee as an
NWS bulletin was dropped as decoder behaviour.

Each list token below includes the comma before it, as the diagrams
count it. The bytes of a field are those that
[08-message.md](08-message.md) allows in message text, other than
`','`. A byte outside them gives one `syntax` finding against the
field's own rule, at the first such byte in the field, and none
against `msg.text`: the field is the most specific rule that holds it
([README section 3](README.md#3-tokenizer-model), Placing a finding).
An earlier draft left such a byte to the `syntax` finding of
`msg.text`. The length limit of [`msg.text`](08-message.md#msg.text) applies
to the whole text, keyword included. **[proposed]** It applies even
where every field is within its own limit
([err.tlm.parmlen](#err.tlm.parmlen)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tlm.parm"></a>`tlm.parm` | Parameter names | `PARM.`, then up to 13 fields for A1 to A5 and B1 to B8, separated by `','`. The list may stop after any field. | Required keyword | End of message text | p. 91/71, p. 134/110 |
| <a id="tlm.parm.name"></a>`tlm.parm.name` | One name | A1: 1 or more bytes. A2 to B8: `','` and 0 or more bytes. Limits in the table below; a longer name gives a `value` finding. | Optional | The next `','` or the end | p. 91/71 |
| <a id="tlm.unit"></a>`tlm.unit` | Units and labels | `UNIT.`, then fields as `tlm.parm`: units for A1 to A5, labels for B1 to B8. | Required keyword | End of message text | p. 91/71, p. 135/111 |
| <a id="tlm.unit.label"></a>`tlm.unit.label` | One unit or label | As `tlm.parm.name`, with the same limits. | Optional | The next `','` or the end | p. 91/71 |
| <a id="tlm.eqns"></a>`tlm.eqns` | Equation coefficients | `EQNS.`, then up to 15 numbers: a, b and c for A1, then for A2, up to A5, separated by `','`. The list may stop after the last coefficient of any channel; a list that stops inside a channel's three has too few fields (below). | Required keyword | End of message text | p. 92/72, p. 135/111 |
| <a id="tlm.eqns.coef"></a>`tlm.eqns.coef` | One coefficient | An empty field is a missing field and gives `syntax` ([README section 3](README.md#3-tokenizer-model), Kinds by situation). **[proposed]** Otherwise the relaxed number of `tlm.analog`; anything else gives `syntax` ([amb.tlm.eqns](#amb.tlm.eqns)). | Optional | The next `','` or the end | p. 92/72 |
| <a id="tlm.bits"></a>`tlm.bits` | Bit sense and project title | `BITS.`, then the parts below. | Required keyword | End of message text | p. 92/72, p. 135/111 |
| <a id="tlm.bits.sense"></a>`tlm.bits.sense` | Bit sense | Eight bytes, each `'0'` or `'1'`, B1 to B8 from left to right. | Required | 8 bytes | p. 92/72 |
| <a id="tlm.bits.title"></a>`tlm.bits.title` | Project title | 0 to 23 bytes directly after the bits; a longer title gives a `value` finding. A first byte `','` belongs to the title and gives an `ambiguous` finding ([amb.tlm.bitsep](#amb.tlm.bitsep); [README section 3](README.md#3-tokenizer-model), Separators and padding). | Optional | End of message text | p. 92/72 |

Longest name, unit or label, the leading comma not counted, derived from
the byte counts on p. 91/71, which include it:

| Channel | A1 | A2 | A3, A4 | A5 | B1 | B2 | B3 to B5 | B6 to B8 |
|---|---|---|---|---|---|---|---|---|
| Bytes | 7 | 6 | 5 | 4 | 5 | 4 | 3 | 2 |

The document notes that these limits are widely ignored (p. 91/71); an
over-long field still gives `value`, as for any field over a stated
limit.

Field counts and empty fields, by
[README section 3](README.md#3-tokenizer-model) (Kinds by situation). A
fourteenth field in `PARM.` or `UNIT.`, or a sixteenth in `EQNS.`, is a
field too many: one `syntax` finding, against the field's rule at the
`','` that starts the first extra field, and the fields after it keep
their tokens. An A1 field that is empty with a `','` after it is a
missing field and gives `syntax` at that `','`, where its first byte was
expected, as decided by the author; an earlier draft gave `value` there,
as a field shorter than its stated length. An `EQNS.` list that stops
inside a channel's three coefficients has too few fields and gives
`syntax` against `tlm.eqns.coef` at the end of the list, where the next
coefficient was expected, as decided by the author; an earlier draft let
the list stop after any field with no finding. A keyword with nothing
after it gives an `unstated` finding, as
[amb.tlm.meta](#amb.tlm.meta) decides: no field of the list is
required, since its earliest stopping point is not stated, so an empty
list is not a missing field; A1 is required only when a `','` follows
it.

**[proposed]** Positions of the other findings. The `unstated` finding
of an empty list is against `tlm.parm`, `tlm.unit` or `tlm.eqns`, at the
byte after the keyword. A coefficient that fits the relaxed number gives
no finding: unlike `tlm.analog`, `tlm.eqns.coef` has no stricter form
beside it.

A `BITS.` text that ends before the eighth bit gives `syntax` at its end,
where the first missing bit was expected, against `tlm.bits.sense`
([README section 3](README.md#3-tokenizer-model), Output).

## 5. Ambiguities

Decoder behaviour below was read in the source at the commits listed in
the [README](README.md#4-decoders-consulted), not run.

<a id="amb.tlm.seq"></a>
### amb.tlm.seq

- **Open.** The sequence number is a three-character value, "typically"
  three digits or `MIC`, and `MIC` may lack its comma (p. 88/68,
  p. 153/129). Appendix 1 shows only `#nnn,` (p. 134/110). Longer numbers,
  other characters and the case of `MIC` are not addressed.
- **Readings.** (a) Exactly three digits, or `MIC`. (b) Any digit run up
  to the comma. (c) Any letters or digits up to the comma.
- **Reading taken.** **[proposed]** (a), with a digit run of another
  length giving `value` (a field outside its stated length) and other
  bytes, lower-case `mic` included, giving `syntax`. Visible in the bytes.
  Readings (b) and (c) would accept some of these bytes, but the `value`
  or `syntax` finding alone is given, with no `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence).
- **In the bytes.** **[proposed]** Reading (b) takes every sequence
  that this reading accepts with the same bytes. Reading (c) does too,
  except for `MIC` with no `','` after it: it would run the sequence on
  to the first `','`, taking the first analog value with it, and so
  read one analog field fewer. Under the test of README section 3 that
  counts only where reading (c) still accepts the report: where it
  gives no `syntax` or `value` finding of its own. Reading (c) accepts,
  for example, a report whose first value is all digits and whose
  comment starts with the rest of a relaxed number (zero or more
  digits, then optionally `'.'` and digits), a `','` and eight bytes
  `'0'` or `'1'`, which it takes as the end of the fifth value and the
  digital value.

  This paragraph only applies the tests of
  [README section 3](README.md#3-tokenizer-model) to that reading. A
  finding of reading (c) is shared, and not its own, when this reading
  gives a finding of the same kind at the same offset, whatever its
  rule (Which findings are the other reading's own). So where both
  readings fail at one byte under different `tlm.*` rules, the finding
  is shared: `T#MIC199,000,255,073,123,` gives `syntax` at its end
  against `tlm.digital` here and against `tlm.analog` under reading
  (c), and gets the `ambiguous` finding. An earlier draft compared the
  rule as well, counted such a pair as reading (c)'s own, and gave no
  `ambiguous` finding there. The finding is against `tlm.analog`, the
  rule this reading gives offset 5, the byte after `MIC` and the first
  byte that the readings divide differently (Placing a finding); an
  earlier draft put it against `tlm.seq`. A `syntax` or `value` finding
  that both readings give elsewhere in the report does not suppress the
  `ambiguous` finding. That includes a report that ends early at the
  same byte under both readings, such as `T#MIC199,000,255,073`: both
  give `syntax` against `tlm.analog` at the end. An earlier draft
  withheld the finding wherever the report had such a finding. Another
  earlier draft listed the accepting comment shapes as digits, `','`
  and eight bits only, and said that reading (c) fails in every other
  report; that left out a fifth value with a `'.'` and the shared
  findings, and was replaced by the test above. A `syntax` or `value`
  finding that this reading alone gives does suppress it (Precedence):
  for example a digital value with a digit other than `'0'` or `'1'`,
  which reading (c) takes into its fifth value and accepts.
- **Decoders.**

  | Decoder | Reads | Where |
  |---|---|---|
  | FAP | `T#`, then any number of digits and `','`; `MIC` is not accepted. | `FAP.pm:2723`; `_telemetry_parse`, `FAP.pm:2357` |
  | Dire Wolf | The text up to the first `','` read as an integer, so `MIC199` becomes one field and the values shift. | `telemetry_data_original`, `telemetry.c:316-333` |
  | pdn-aprs | `MIC` with an optional comma; otherwise letters or digits of any length up to `','`. | `report`, `telemetry.rs:20-36` |
  | aprslib | Does not parse telemetry reports. | `__init__.py:60` |
  | Xastir | Treats them as status text. | `db.c:15242-15249` |
  | aprsc | Parses nothing in them. | `parse_aprs_telem`, `parse_aprs.c:568-576` |
  | javAPRSlib | Telemetry parsing commented out. | `Parser.java:255-258` |

- **Corpus question.** The bytes between `T#` and the first comma.

<a id="amb.tlm.value"></a>
### amb.tlm.value

- **Open.** The diagram has fixed four-byte fields (p. 88/68,
  p. 134/110). The text says that longer values with a decimal point and
  a leading minus are common, that most applications accept them and that
  others are encouraged to (p. 88/68, p. 134/110), without giving their
  syntax: a leading `'+'`, an exponent, an empty field, a trailing point
  and length are not addressed.
- **Readings.** (a) Three digits only. (b) A signed decimal as in
  section 2. (c) Any bytes between commas.
- **Reading taken.** **[agreed]** (a) and (b), both without a finding;
  anything else `syntax`. The text describes the relaxed form and
  encourages receivers to accept it, so it is a form the document
  defines ([README section 3](README.md#3-tokenizer-model)); reading it
  as `syntax` would contradict that text. Its shape is the one the
  text describes, a leading minus and a decimal point, which is also
  what FAP and pdn-aprs accept, less the trailing point that pdn-aprs
  also takes. An earlier draft gave each relaxed value an `unstated`
  finding. A relaxed value gets no `ambiguous` finding: reading (c)
  takes it with the same boundaries and as the same field, and reading
  (a) does not match it. Bytes that give `syntax` here, which reading
  (c) would accept, get that finding alone, with no `ambiguous` beside
  it ([README section 3](README.md#3-tokenizer-model), Precedence). The
  document encourages receivers to accept the relaxed form and does not
  advise senders against it, so it gives no `discouraged` finding.
- **Decoders.** FAP: an optional `'-'`, then digits, or digits, `'.'`
  and digits, or `'.'` and digits; empty values allowed
  (`FAP.pm:2362-2377`). Dire Wolf: any text between commas, converted as
  a floating-point number; an empty value is unknown
  (`telemetry.c:335-352`). pdn-aprs: an optional `'-'`, digits with at
  most one `'.'` and at least one digit; an empty value is missing
  (`telemetry.rs:40-58`; `is_decimal`, `message.rs:323-327`). aprslib,
  Xastir, aprsc and javAPRSlib do not parse the report
  ([amb.tlm.seq](#amb.tlm.seq)).
- **Corpus question.** Analog fields that are three digits, other digit
  runs, signed decimals, empty, or something else.

<a id="amb.tlm.count"></a>
### amb.tlm.count

- **Open.** The diagram has five analog values and the digital value
  (p. 88/68). Fewer values, a missing digital value, or a separator before
  the comment are not addressed.
- **Readings.** (a) Exactly five values and eight bits. (b) One to five
  values; bits only after all five. An earlier draft listed a third
  reading, a comma or space before the comment, and gave an `ambiguous`
  finding at a comment whose first byte is `','` or SP. No text of
  APRS12c puts a separator there: both report diagrams place the
  comment directly after the digital value (p. 88/68, p. 134/110), and
  no example has a comment. By
  [README section 3](README.md#3-tokenizer-model) (Separators and
  padding) such a byte belongs to the comment, and with no text of the
  document to name it gets no finding.
- **Reading taken.** **[proposed]** (a). Visible in the bytes.
- **In the bytes.** The comment starts with the byte after the eighth
  bit, as above. A report that reading (b) would accept gets the
  `syntax` finding of the first missing field alone, with no
  `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence).
- **Decoders.** FAP: up to five values, fewer accepted; the sixth field,
  if any, is the bits, padded with `'0'` to eight (`FAP.pm:2361-2387`).
  Dire Wolf: the eight bytes after the fifth comma are the bits and the
  rest the comment; fewer fields are reported and decoded anyway
  (`telemetry.c:354-394`). pdn-aprs: bits only after five values, the
  comment directly after them; fewer fields tolerated as a defect
  (`telemetry.rs:60-75`).
- **Corpus question.** The number of comma-separated fields in `T#`
  reports, and the byte after the eight bits.

<a id="amb.tlm.b91.where"></a>
### amb.tlm.b91.where

- **Open.** Chapter 13 names the uncompressed, compressed and Mic-E
  position formats, and asks itself whether leaving out objects was
  intended (p. 88/68). How to find the block in a comment that holds
  other `'|'` bytes is not stated.
- **Readings.** (a) Only the three named formats. (b) Any comment. An
  earlier draft also listed, for a comment with several runs between
  bars, (c) the first block, (d) the last block and (e) every block,
  and took (e) with an `ambiguous` finding on each of several
  candidates. Chapter 13 places the block after the free text with
  only a DAO or the Mic-E device code after it (p. 88/68), so a run
  followed by anything else is not a block, and at most one run in a
  comment meets that: a later run would stand in the bytes after an
  earlier one, which may hold only a DAO. Choosing among several runs
  therefore takes a run that p. 88/68 does not allow, and by
  [README section 3](README.md#3-tokenizer-model) it is decoder
  behaviour (Dire Wolf and aprslib take the first, FAP and pdn-aprs the
  last, below), not a listed reading, and gives no finding.
- **Reading taken.** **[proposed]** (a), with a block in an object or
  item comment recorded under an `unstated` finding. Visible in the
  bytes, as that finding.
- **In the bytes.** In an object or item comment the block is a block
  token, as reading (b) would have it; the `unstated` finding marks the
  place, and the readings do not divide the bytes differently, so there
  is no `ambiguous` finding
  ([README section 3](README.md#3-tokenizer-model)).
- **Decoders.** FAP: in position, object and item comments and in Mic-E;
  the last block, 2 to 7 pairs (`_comments_to_decimal`, `FAP.pm:1199`;
  `FAP.pm:1859`; `_comment_telemetry`, `FAP.pm:1405`). Dire Wolf: in its
  comment parser, called for positions, Mic-E, objects and items; the
  first block, 2 to 7 pairs (`process_comment`, `decode_aprs.c:4499`,
  `decode_aprs.c:4701-4715`; callers `decode_aprs.c:986`, `1096`, `1712`,
  `1716`, `2205`, `2303`, and its data extension parser at `4154` to
  `4230`). aprslib: in position and object comments and in Mic-E; the
  first `'|'` followed by 4 to 14 base-91 digits and `'|'` is taken, and
  if that run is of odd length no block is read at all
  (`common.py:124`, called at `position.py:76`; `mice.py:211`;
  `telemetry.py:18-20`). pdn-aprs:
  in the comment decoder shared by positions, objects and items, and in
  Mic-E; only the last two `'|'` of the comment are tried
  (`decode.rs:128`, `object.rs:60`, `object.rs:87`;
  `find_telemetry`, `comment.rs:595-607`). Xastir: no base-91 telemetry
  code was found in `db.c` or `util.c`.
- **Corpus question.** Blocks by packet type; comments holding more than
  one block.

<a id="amb.tlm.b91.order"></a>
### amb.tlm.b91.order

- **Open.** Chapter 6 lets `!DAO!` stand anywhere in the comment
  (p. 35/21); chapter 13 puts the block after the free text and before any
  DAO (p. 88/68).
- **Readings.** (a) Block, then DAO, then suffix, and nothing else after
  the block. (b) Block and DAO in either order, as chapter 6 lets the
  DAO stand anywhere. An earlier draft let reading (b) also allow text
  after the block. Chapter 13 requires the block to come after the free
  text (p. 88/68), so that part contradicts it, and by
  [README section 3](README.md#3-tokenizer-model) it is decoder
  behaviour (every decoder read, below), not a listed reading, and
  gives no finding.
- **Reading taken.** A run of block shape followed by bytes other than
  an optional [`cmt.dao`](02-fields.md#cmt.dao) and, in Mic-E, the
  device suffix is comment text, with no finding, under both listed
  readings; recognising a block followed by text is left to a deviation
  recogniser ([README section 3](README.md#3-tokenizer-model)).
  **[proposed]** (a): the block comes before the DAO.
- **In the bytes.** A DAO before a block that nothing but the suffix
  follows is found where it stands under both readings
  ([02-fields.md](02-fields.md#82-items-found-inside-a-comment) section
  8.2), so the readings divide no bytes differently, and there is no
  `ambiguous` finding ([README section 3](README.md#3-tokenizer-model)). An earlier draft gave one at the first `'|'` of
  a run followed by text, which only the dropped part of reading (b)
  took as a block.
- **Decoders.** All read accept either order and text after the block:
  FAP takes the block out first and then looks for a DAO in the rest
  (`FAP.pm:1199-1207`); Dire Wolf matches each anywhere
  (`decode_aprs.c:4701`, `decode_aprs.c:4732`); aprslib takes the block
  and then a DAO (`common.py:124-127`); pdn-aprs finds the block first
  and then the last DAO outside it (`comment.rs:179-181`,
  `find_dao`, `comment.rs:622`).
- **Corpus question.** In comments with both, which comes first, and what
  follows the block.

<a id="amb.tlm.keyword"></a>
### amb.tlm.keyword

- **Open.** The keywords are shown in upper case (p. 91/71, p. 92/72). A
  different case, and a keyword in a message to a station that sends no
  telemetry, are not addressed.
- **Readings.** (a) Exact upper case. (b) Any case.
- **Reading taken.** **[proposed]** (a); other text is an ordinary
  message. Visible in the bytes: a text that starts with one of the four
  keywords in another case, which reading (b) would take as a definition
  message, is message text with an `ambiguous` finding at its first byte.
  Whether the addressee sends telemetry cannot be seen in the packet and
  gives no finding.
- **In the bytes.** By the tests of
  [README section 3](README.md#3-tokenizer-model), the finding is given
  only when the rest of the text, read as that definition message, fits
  section 4 with no `syntax` or `value` finding of reading (b)'s own:
  for example `Bits.` followed by eight `'0'` or `'1'` bytes. Text such
  as `bits. of the plan` would fail as a `BITS.` message, so it gives no
  finding. A finding that both readings give, such as the length limit
  of [`msg.text`](08-message.md#msg.text), does not suppress the
  `ambiguous` finding. An earlier draft gave the finding for every such
  keyword. The finding is against [`msg.text`](08-message.md#msg.text),
  the rule this reading gives the bytes (Placing a finding). A finding
  of reading (b) is shared when this reading gives one of the same kind
  at the same offset, whatever its rule (Which findings are the other
  reading's own). A byte that is not a text byte, such as a control
  byte among the eight bits of `Bits.`, gives `syntax` at that byte
  against `msg.text` here and against `tlm.bits.sense` under reading
  (b); the finding is shared, and the `ambiguous` finding is given. An
  earlier draft compared the rule as well, counted such a finding as
  reading (b)'s own, and gave no `ambiguous` finding there.
- **Decoders.** Dire Wolf: exact; the definitions are stored for the
  addressee (`decode_aprs.c:1935-1953`). aprslib: exact (`telemetry.py:46`).
  pdn-aprs: exact (`telemetry_metadata`, `message.rs:197-202`). FAP: any
  case, only flagged as a telemetry message (`_message_parse`,
  `FAP.pm:1389`).
- **Corpus question.** Message texts starting with one of the keywords in
  another case.

<a id="amb.tlm.meta"></a>
### amb.tlm.meta

- **Open.** The name and unit limits are said to be widely ignored
  (p. 91/71). The field bytes, empty fields, more than 13 fields and an
  empty list are not addressed.
- **Readings.** (a) Limits enforced. (b) Split on commas, no limits.
- **Reading taken.** Extra fields, and an empty A1 field with a `','`
  after it, give `syntax` as section 4 sets out
  ([README section 3](README.md#3-tokenizer-model), Kinds by
  situation); an earlier draft gave the empty A1 field `value`.
  **[proposed]** (a) as `value` findings; empty fields after A1 allowed,
  as the byte counts include the comma. **[agreed]** An empty list gives `unstated`: the document
  says nothing about where the list may stop. Visible in the bytes. Reading (b)
  would accept the over-long and extra fields, but the `value` or
  `syntax` finding alone is given, with no `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence).
- **Decoders.** Dire Wolf: up to 13 fields, limits ignored; an empty
  field keeps the earlier value, and so does a name of `'-'`
  (`telemetry.c:602-611`, `telemetry.c:681-691`). aprslib: the first 13
  fields, each at most 20 bytes (`telemetry.py:54-60`). pdn-aprs: at most
  13 fields, or the text
  is not taken as metadata; the message identifier is split off first
  (`message.rs:203-219`). FAP: no field parsing (`FAP.pm:1389`).
- **Corpus question.** Field lengths at each position; empty fields; lists
  of more than 13 fields.

<a id="amb.tlm.eqns"></a>
### amb.tlm.eqns

- **Open.** The coefficient syntax is not stated; the example has
  integers, decimals, a leading point and a leading minus (p. 92/72). The
  list may stop at any field, even inside a channel's three.
- **Readings.** (a) The relaxed number of `tlm.analog`. (b) Also
  exponents. (c) Empty fields allowed.
- **Reading taken.** An empty field, a sixteenth field, and a list that
  stops inside a channel's three coefficients give `syntax`, as
  section 4 sets out ([README section 3](README.md#3-tokenizer-model),
  Kinds by situation); the last was decided by the author. An earlier
  draft took a list of any length up to 15 without a finding.
  **[proposed]** (a). Visible in the bytes. Readings (b) and (c) would
  accept an exponent or an empty field, but the `syntax` finding alone
  is given, with no `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence).
- **Decoders.** Dire Wolf: each field converted as a floating-point
  number; an empty field and a count other than 15 are reported
  (`telemetry.c:763-787`). aprslib: an optional `'-'`, digits with an
  optional point, or empty; the first 15 (`telemetry.py:67-75`).
  pdn-aprs: decimals with an optional exponent; trailing commas and spaces
  ignored; at most 15 (`message.rs:220-245`).
- **Corpus question.** Coefficients that are not plain signed decimals;
  the number of coefficients per message.

<a id="amb.tlm.bitsep"></a>
### amb.tlm.bitsep

- **Open.** The BITS diagram puts the title directly after the eight bits
  (p. 92/72, p. 135/111); the example has a comma between them.
- **Readings.** (a) No separator; a comma is part of the title.
  (b) A comma is required. (c) A comma is optional.
- **Reading taken.** (a), as
  [README section 3](README.md#3-tokenizer-model) (Separators and
  padding) requires of a byte that the diagram does not show: the `','`
  belongs to the title, the next field, and gets an `ambiguous` finding
  because the example on p. 92/72, a text of the document, takes it as
  a separator. Visible in the bytes, as that finding. When such a
  title, its `','` counted, is longer than 23 bytes, the `value` finding
  of `tlm.bits.title` alone is given, with no `ambiguous` beside it
  (Precedence).
- **In the bytes.** The finding is at that `','`, the byte after the
  eighth bit. Readings (b) and (c) take the bytes after
  it as the title, one byte shorter, and every other byte as this
  reading does, so under the test of README section 3 they accept the
  message wherever this reading does. A `syntax` or `value` finding
  elsewhere in the message is given by every reading and does not
  suppress the `ambiguous` finding. An earlier draft gave the finding
  only where the message text had no such finding.
- **Decoders.** Dire Wolf: skips one comma after the bits if present
  (`telemetry.c:878`). aprslib: requires the comma, and a title of at most
  23 bytes (`telemetry.py:88`). pdn-aprs: splits at the first comma and
  requires exactly eight bits before it (`message.rs:249-258`).
- **Corpus question.** The byte after the eight bits in `BITS.` messages;
  title lengths with and without that byte.

## 6. Errata

<a id="err.tlm.seq"></a>
### err.tlm.seq

Chapter 13 and the release notes allow `MIC` as the sequence, with or
without a comma (p. 88/68, p. 153/129), and give the example
`T#MIC199,...`. Both report diagrams give the sequence field a fixed five
bytes, which `MIC` without its comma does not fill, and the Appendix 1
diagram writes it `#nnn,` (p. 88/68, p. 134/110). The reading follows
the chapter text.

Origin: already in APRS 1.0.1: the `MIC` text, the `T#MIC199` example
and the five-byte field on PDF p. 78 (printed 68), and `#nnn,` in the
Appendix 1 diagram on PDF p. 109. 12b has it.

<a id="err.tlm.analog"></a>
### err.tlm.analog

Both report diagrams give each analog value a fixed four bytes
(p. 88/68, p. 134/110); the third example on p. 88/68 has values such as
`45.7` and `-7.3`, which fit only the relaxed form described in the text.
The reading takes both ([amb.tlm.value](#amb.tlm.value)).

Origin: a merge of APRS 1.0.1 diagrams with later text. The fixed
four-byte fields are in the 1.0.1 diagrams (PDF p. 78 and p. 109). The
paragraph on longer signed decimal values, the Appendix 1 note and the
third example are not in 1.0.1; 12b already has them, its example with
`7.0` where 12c has `-7.3` (12b PDF p. 90). The range 000 to 999 comes
from an APRS 1.2 addendum proposal listed on p. 157/133; it does not
change the field width.

<a id="err.tlm.bits"></a>
### err.tlm.bits

The BITS diagram has no separator between the bits and the title; the
example has a comma (p. 92/72). The reading follows the diagram
([amb.tlm.bitsep](#amb.tlm.bitsep)).

Origin: already in APRS 1.0.1, in the diagram and example on PDF p. 80
(printed 70) and the Appendix 1 diagram on PDF p. 110. 12b has it.

<a id="err.tlm.parmlen"></a>
### err.tlm.parmlen

The byte counts of the `PARM.` and `UNIT.` diagrams (p. 91/71) allow a
text longer than a message may carry. Derived here: the keyword is 5
bytes and the thirteen fields at most 7, 7, 6, 6, 5, 6, 5, 4, 4, 4, 3, 3
and 3 bytes, commas included, which is 63; the whole text is 68 bytes.
The message text limit is 67 (p. 93/71, p. 135/111;
[`msg.text`](08-message.md#msg.text)).

Readings: (a) the message limit holds, and a text of 68 bytes gives the
`value` finding of `msg.text`; (b) the field limits take precedence, and
a definition message whose every field is within its limit gets no
`msg.text` finding. **[proposed]** (a): the definition messages are
messages, and the field limits are each kept separately, so a 68-byte
text is reported once, by `msg.text`, and no finding is given here.

Origin: already in APRS 1.0.1: the same byte counts on 1.0.1 PDF p. 79
and the 67-byte message text on PDF p. 81, and both again in Appendix 1
on PDF p. 109 and p. 110. 12b has it (12b PDF p. 93 and p. 95).

<a id="err.tlm.b91count"></a>
### err.tlm.b91count

A duplicate of [err.b91.users](02-fields.md#err.b91.users), which
records that p. 34/20 names two users of base-91 where p. 88/68 names
four, and its origin. The digit range itself is read in
[`b91.digit`](02-fields.md#b91.digit).

## 7. Open items

- The corpus questions in section 5.
- Chapter 13 lists telemetry for three position formats only; whether
  status reports or weather reports can carry a block is not addressed,
  and this reading does not look for one there (UAP 5.33 shows one in a
  weather report).
- ebarkie/aprs has no telemetry decoder in the files read.
