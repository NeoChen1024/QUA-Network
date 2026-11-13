# Reading of the legacy APRS documents

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |
| Used by | `qua-legacy-tokenize` and `qua-legacy-fields` (package `qua_network.legacy`), RFC section 15, step 4. They read 01-frame, 02-fields, 03-position, 04-mic-e, 05-object-item, 06-weather, 07-telemetry, 08-message and 09-other. |

## 1. Purpose

The files in this directory state, field by field, how this project reads
the legacy APRS documents: what a tokenizer recognises, where each field
starts and ends, and what it reports. They do not specify QUA Network.

APRS12c leaves many places open: optional fields with no delimiter, byte
sets it does not state, receiver actions it does not give, and passages that
contradict each other. A tokenizer that claims to check conformance has to
decide each of these. The decisions are made here, in writing, and the
tokenizer implements this reading. "Conforms" in this project means
"conforms to this reading". Where the reading had to choose, the entry says
so and carries a status label.

The text and tables of the legacy documents are not reproduced. Each rule
is described in this project's own words and cites the page it comes from.

## 2. Conventions

**Citations.** `p. N/M` is PDF page N, printed page M, of `APRS12c.pdf` at
the commit above. The printed numbers are not monotonic, because the
document is a compilation; the PDF page is the one to look up. Other
documents are named: `UAP` is `Understanding-APRS-Packets.pdf` in the same
submodule, cited by section. Errata also cite two earlier editions, only
to say where a defect first appears: `12b PDF p. N` is a PDF page of
`APRS12b.pdf` in the same submodule, and `1.0.1 PDF p. N` a PDF page of
the original APRS 1.0.1 reference of 29 August 2000, which is not in the
repository and is linked from the
[documentation index](../README.md#external-references). Neither
edition is a reference for the reading itself.

**Bytes.** Packets are byte strings, not text. A literal byte is written
in code, `'!'`; a range as `0x21`–`0x7B`; `SP` is 0x20. "Digit" means
`'0'`–`'9'`. Case is significant unless an entry says otherwise.

**Rules.** Each file has rule tables with the columns

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|

The ID is lower case and dotted, unique across this directory, and is what
the tokenizer reports. Each file owns the prefixes listed in section 5. An
ID is never reused for a different rule. A rule that restates an
unambiguous statement of APRS12c carries no label; a rule that depends on a
reading names the ambiguity entry that decides it.

**Ambiguities.** Each has a heading `amb.<prefix>.<topic>`, where
`<prefix>` is one of the rule prefixes of the file that holds it
(section 5) and `<topic>` is one or more lower-case words joined by `.`
or `-`. The heading is preceded by an anchor of the same name,
`<a id="amb.<prefix>.<topic>"></a>`, and links to it use that name. The
entry gives:

- what the document leaves open, with pages;
- the readings a parser could take;
- the reading taken, with its status label;
- whether the question can be seen in the bytes, and so whether it
  produces an `ambiguous` finding (section 3);
- what deployed decoders do (section 4), stated as read in their source at
  the commit given;
- the corpus question whose answer would confirm or overturn the reading.

**Errata.** A place where APRS12c is wrong by its own rules (an example
that does not fit its diagram, an arithmetic error, two pages that
disagree) has a heading `err.<prefix>.<topic>`, formed and anchored as an
ambiguity heading. The entry says which side the reading follows, and
ends with an "Origin" line: where the defect first appears, given as one
of inherited from APRS 1.0.1, a merge of 1.0.1 text with a later
addendum, within an addendum, or introduced by the 12b/12c compilation,
with the 1.0.1 and 12b pages checked. One defect has one entry; another
file that depends on it links there, and an entry that turned out to
duplicate another keeps its heading as a pointer. An entry found not to
be an error is deleted, and its ID is not reused. A fault that lies
outside the document's content, such as a wrong character in the PDF's
text layer or a decoder that copied one, is a note in the entry it
affects, not an erratum.

## 3. Tokenizer model

**[agreed]** The tokenizer is strict. It reports where a packet departs
from this reading and does not repair it. Known deviations seen on air are
recognised separately, afterwards, by named recognisers that run only on
what the strict pass could not account for. Each recogniser corresponds to
an entry of the divergence catalogue (RFC Appendix E). They never change
the strict result.

**[proposed]** Output. For each packet the tokenizer produces:

- **Tokens.** `(rule ID, start, end, depth)`, as byte offsets into the
  raw TNC2 line. The depth-0 tokens cover the line exactly, in order, with
  no gap and no overlap. Bytes the tokenizer cannot account for form a
  `residue` token, which names the rule at which parsing stopped.
  **[proposed]** A field whose extent its delimiters fix keeps its own
  token when its bytes are wrong, with the finding; only bytes whose rule
  cannot be told, at that level or inside such a field, are residue. A
  finding for a byte that is missing is placed where that byte was
  expected, which may be the end of the line. Deeper
  tokens lie inside one token of the level above: the parts of a Mic-E
  destination address, items found inside a comment, the inner packet of a
  third-party payload. **[agreed]** The token of the data type identifier
  byte carries the identifier rule of the format it selects, such as
  `pos.dti` or `stat.dti`, so that the format can be read from the tokens.
  The `dti.*` rules of 01-frame give the dispatch and its findings.
  **[proposed]** That rule is the identifier rule of the most specific
  format the packet is classified as, and it is assigned once
  classification is complete, not when byte 0 is read. A position or
  object report that carries weather carries `wx.pos` or `wx.obj`; a `:`
  packet carries the rule of the kind that 08-message section 2.1
  decides. The list of identifier rules is in
  [01-frame.md section 7](01-frame.md#7-data-type-identifier). A form
  without an identifier byte has no such token.
- **Findings.** `(rule ID, kind, offset)`. The kinds are:

  | Kind | Meaning | Effect on the verdict |
  |---|---|---|
  | `syntax` | The bytes do not match the rule. | `syntax` |
  | `value` | The bytes match, but a value is outside its stated range, or a field is longer than its stated limit. | `value` |
  | `ambiguous` | Another reading listed in an ambiguity entry would also match these bytes. | `conform-ambiguous` |
  | `obsolete` | The form is valid but marked obsolete. | none |
  | `discouraged` | The form is valid, but APRS12c calls it not recommended or advises against it. | none |
  | `is-only` | An address that AX.25 cannot carry; possible only on APRS-IS. | none |
  | `unstated` | The document gives no rule for what was found. | none |

- **Verdict.** The most severe of `conform`, `conform-ambiguous`, `value`,
  `syntax`, `unknown-format`, in increasing order. `unknown-format` is
  given when the data type cannot be determined.
  While the reader of a format is not written, the field after its
  identifier byte is a residue token that names `unread`, and a packet
  with such a field has no verdict. This is a state of the
  implementation, not a rule of the reading.

**[proposed]** The tokenizer finds boundaries and checks bytes and ranges.
It does not compute values (degrees, knots, decoded telemetry). Decoding is
a separate layer built on the tokens. **[agreed]** The one exception is a
checksum that a form carries, such as the NMEA `*hh`: the tokenizer
verifies it, because a mismatch means the bytes are not what was sent.

**[agreed]** An ambiguity that can be seen in the bytes produces an
`ambiguous` finding. It can be seen when another reading listed in an
ambiguity entry would divide or classify these particular bytes
differently: two `!DAO!` candidates in one comment, GGA bits in a
compressed `T` byte whose `c` byte also lies in the course range.

**[agreed]** A listed reading is a reading of the document's text. A
way of reading the bytes that contradicts an explicit statement of
APRS12c is recorded in the entry as decoder behaviour, not as a reading,
and produces no finding. Recognising such packets is the work of the
deviation recognisers.

**[agreed]** The other reading counts only when it would accept the
whole field, or the whole report, that the bytes belong to. Only
findings that the other reading itself would produce count against it:
a `syntax` or `value` finding that both readings would give elsewhere in
the packet does not suppress the `ambiguous` finding. Each ambiguity
entry that gives an `ambiguous` finding says on which bytes, and under
which condition the other reading would accept them.

**[agreed]** Precedence. When the reading already reports the bytes as
a `syntax` or `value` finding, that finding alone is given, and no
`ambiguous` finding beside it, so that one defect is counted once.

**[agreed]** One byte may carry several findings from different rules.
Each keeps its own rule ID; they are not merged. Identical findings
(the same rule, kind and offset) are given once.

**[agreed]** An ambiguity that every instance of a form carries, and
that the bytes of one packet cannot narrow, is decided by the reading
and produces no finding. The example is whether seven bytes after a
symbol that fit a data extension are one, or the start of a comment: a
finding there would mark every extension. Each ambiguity entry says
which of the two cases it is.

**[agreed]** A form recognised by its shape alone, at a place where
free text or another class of the same field can also stand, is that
form only when no class before it takes the bytes and its bytes lie
within the form's ranges. Otherwise the bytes are what else stands
there, with no finding of the form: no `syntax`, and no `ambiguous`
finding from a reading that would widen the ranges. A Maidenhead
locator is the case in point: in a status text, a destination address
or the comment of a `[` beacon, locator-shaped bytes with a letter out
of range are text or another class, and a destination such as `AP51WX`
that a tocall takes is not a locator. Where the format fixes the place
of the form or closes it with a delimiter of its own (the locator right
after `[`, one closed by `]` or by the `/G` of a Mic-E status), the
bytes are the form, and bytes out of range give `syntax`. A form
defined by shape alone otherwise catches unrelated text too often to
report on it.

**[proposed]** Kinds by situation. The files report like situations
with the same kind:

- A byte outside the byte set that a rule states: `syntax`.
- A fixed-width field whose bytes do not fit, including a value written
  with more or fewer digits than its width: `syntax`. Nothing delimits
  the field, so excess bytes cannot be counted against it.
- A delimited or variable-length field longer or shorter than a stated
  length: `value`, at the first byte past the limit when it is too long.
- A value outside a stated range, or a code outside the closed set of
  values that a table or a form defines: `value`.
- A code that a stated prohibition covers ("do not use"): `syntax`.
- A code outside a list that the document does not close, or anything
  else for which it gives no rule: `unstated`. Where the document says
  that other codes are allowed: no finding.
- A form marked obsolete: `obsolete`. A form that is only "not
  recommended", discouraged or advised against: `discouraged`.
- **[agreed]** Bytes outside 7-bit ASCII in a field where APRS12c only
  recommends printable ASCII: no finding. Many senders put UTF-8 there,
  and a finding would bury everything else. The field inventory counts
  such bytes per field as a statistic of its own, outside the findings.
- A departure from a stated sending rule that receivers are told to
  accept, such as the case of a locator or of `MHz`: `syntax`.
- A mixture of forms that are each allowed: no finding where the
  document calls them interchangeable, `value` where it calls the
  combination unknown, and `unstated` where it says nothing. A mixture
  inside one value is a field that does not fit, as above.

## 4. Decoders consulted

Deployed behaviour is taken from source code, read and not run, at these
commits. The code is not copied: several of these projects are GPL, and
this directory describes their behaviour in its own words only.

| Decoder | Repository | Commit | Licence | Read |
|---|---|---|---|---|
| Ham::APRS::FAP 1.x (Perl) | <https://github.com/hessu/perl-aprs-fap> | `0447564` | Same terms as Perl | `FAP.pm` |
| Dire Wolf | <https://github.com/wb2osz/direwolf> | `eda1383` | GPL-2.0 | `src/decode_aprs.c` and the files it calls; also `src/digipeater.c` and `src/dwgpsnmea.c` |
| aprslib (Python) | <https://github.com/rossengeorgiev/aprs-python> | `c2a0f18` | GPL-2.0-or-later | `aprslib/parsing/`, `aprslib/base91.py` |
| Xastir | <https://github.com/Xastir/Xastir> | `387d559` | GPL-2.0 | `src/db.c`, `src/util.c`, `src/objects.c` |
| aprsc | <https://github.com/hessu/aprsc> | `963b2e5` | BSD-3-Clause | `src/parse_aprs.c`, `src/incoming.c`, `src/worker.h`; only what an APRS-IS server inspects or drops |
| javAPRSlib | <https://github.com/ab0oo/javAPRSlib> | `2a51ce6` | GPL-3.0 / LGPL | `src/main/java/net/ab0oo/aprs/parser/` |
| ebarkie/aprs (Go) | <https://github.com/ebarkie/aprs> | `21df478` | MIT | `*.go` |
| aprs-parser-rs | <https://github.com/Turbo87/aprs-parser-rs> | `e1e1a61` | MIT / Apache-2.0 | `src/` |
| pdn-aprs | <https://github.com/packet-net/aprs-rs> | `4933e3f` | AGPL-3.0 | `src/` |

An entry that cites a decoder names it and the function or line it read.

## 5. Files

| File | Covers | Rule prefixes |
|---|---|---|
| [01-frame.md](01-frame.md) | The TNC2 line, addresses, destination classes, the data type identifier, third-party payloads. | `line`, `addr`, `path`, `dest`, `src`, `dti`, `tp` |
| [02-fields.md](02-fields.md) | Fields shared by several formats: timestamps, latitude and longitude, position ambiguity, symbol table and code, the compressed position block, base-91, data extensions, items found in comments. | `time`, `lat`, `lon`, `sym`, `cmp`, `b91`, `ext`, `cmt` |
| [03-position.md](03-position.md) | Position reports, DF reports, Maidenhead beacons, raw NMEA. | `pos`, `df`, `grid`, `nmea` |
| [04-mic-e.md](04-mic-e.md) | Mic-E: destination address, information field, status text. | `mice` |
| [05-object-item.md](05-object-item.md) | Objects, items, area objects, signposts. | `obj`, `item`, `area` |
| [06-weather.md](06-weather.md) | Weather reports of every form, storm data. | `wx`, `storm` |
| [07-telemetry.md](07-telemetry.md) | Telemetry reports, base-91 comment telemetry, telemetry definition messages. | `tlm` |
| [08-message.md](08-message.md) | Messages, acknowledgements, bulletins, announcements, NWS bulletins, NTS. | `msg`, `bln`, `nws`, `nts` |
| [09-other.md](09-other.md) | Status reports, capabilities, general and directed queries, user-defined data, test packets, frequency specifications in comments. | `stat`, `cap`, `qry`, `udf`, `inv`, `freq` |
| [examples.json](examples.json) | The expected verdict and findings of each example packet of APRS12c, by page and digest. | — |

## 6. Open items

- The example packets of APRS12c are checked against this reading
  (RFC section 15, step 4): [examples.json](examples.json) holds the
  verdict this reading gives each example, derived from these files
  without running the tokenizer, and `qua-legacy-examples check`
  compares. When a file changes, the entries it decides are derived
  again in the same way, not copied from the tokenizer's output.
- Deviation recognisers and the divergence catalogue entries they belong
  to (RFC Appendix E).
- APRS12c is itself a draft with known issues. When a later draft of the
  reference appears, this reading is checked against it page by page.
