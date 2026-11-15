# Reading of the legacy APRS documents

| | |
|---|---|
| Status | Draft. Not frozen. Paragraphs and rows are marked **[agreed]**, **[proposed]** or **[open]**, with the meaning that the RFC gives them. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |
| Used by | `qua-legacy-tokenize` and `qua-legacy-fields` (package `qua_network.legacy`), for RFC section 15, step 4. These tools apply 01-frame, 02-fields, 03-position, 04-mic-e, 05-object-item, 06-weather, 07-telemetry, 08-message and 09-other. The decoder of [docs/interop](../interop/README.md) applies 10-values: `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Purpose and premise

The files in this directory record how the legacy tokenizer of this
project reads the bytes of APRS packets. APRS12c is the reference. These
files do not specify QUA Network. They do not restate APRS, and they do
not repair it.

**[agreed]** Premise. The premise has these parts:

- APRS12c is not a coherent specification. It does not delimit all
  fields. It does not specify all byte sets or all actions of the
  receiver.
- APRS12c contradicts itself between pages, between a diagram and its
  examples, and between the editions that it compiles.
- No interpretation can remove these faults, and this project does not
  try to remove them.
- These files are a measurement tool. They have two purposes. First, the
  tokenizer uses them to divide the corpus into fields and to count the
  fields (RFC section 15, step 4). Second, they list the places where
  APRS12c fails, for the divergence catalogue (RFC Appendix E).
- These files make no claim about what APRS means.
- A choice at one place is a working choice for that place only. It is
  not a precedent. Two working choices do not have to agree with each
  other.

**[proposed]** A value file has a third purpose. It states the value that
the bytes of a token give: the unit, the scale and the range that APRS12c
specifies, with the page. The decoder of
[docs/interop](../interop/README.md) applies it. A value file makes no
claim about what the sender meant. [10-values.md](10-values.md) is the
first value file. Each later value file uses its conventions.

Thus, in this project, "conform" means only this: the bytes break no
statement of APRS12c that the rules of section 3 treat as specified.
Deployed decoders can still read a packet that conforms in different
ways.

These files do not copy the text and tables of the legacy documents. Each
rule describes the behaviour in the words of this project and cites the
page of its source.

An earlier draft of this directory decided each open point of APRS12c
separately. It recorded each decision as an interpretation with a status
label. It also added general paragraphs to keep these decisions
consistent with each other. The author dropped that direction for two
reasons:

- It is the same as writing a new edition of APRS, which is not the work
  of this project.
- Most of the decisions had no measurable effect on the corpus.

The author also decided that no decision of that draft continues into
these files. This includes the decisions that recorded a reason of the
author. The general rules replace all of them. The earlier draft stays in
the history of this repository, up to commit `722e30a`.

## 2. Conventions

**Terms.** These files use the terms below with one meaning each. They do
not use other words for these meanings.

| Term | Meaning |
|---|---|
| APRS12c | The reference document of these files (see "Citations"). |
| specify | APRS12c specifies a format, a byte set, a width, a range or a limit. An example shows bytes. |
| interpretation | One possible meaning of text in APRS12c. |
| format | The byte structure of a packet type or of a field. The column "Format" of a rule table gives the format of the field. |
| field | A named part of a packet, at any level. A field can be inside another field, for example the altitude in a comment. |
| Item, Object | With a capital letter, these words are only the APRS Item report and the APRS Object report. |
| text | Bytes with no structure. |
| place | Where a field can be in a packet. "Position" is only a geographic position. |
| marker | A keyword, a symbol or a fixed place that starts a field. |
| accept, reject | An interpretation accepts bytes when the bytes match it. It rejects bytes when they do not match it. |
| conform | Only for the verdict (section 3.2). |
| token, finding, verdict, residue | The outputs of the tokenizer (section 3.2). |
| rule | A row of a rule table. It has an ID. |
| general rule | One of the seven rules of section 3.1, "rule 1" to "rule 7". |
| stricter format | Of two formats, the format that permits fewer byte strings. |
| typing error | A clear error in APRS12c that no other part of APRS12c supports, for example an extra or a missing character. |
| erratum | A catalogue row where two parts of APRS12c disagree, or where APRS12c has a typing error. Its ID starts with `err.`. |
| working choice | The behaviour that the tokenizer uses at one place when no general rule applies. |
| the tokenizer | The tool that applies these files (package `qua_network.legacy`). |
| the author | The author of this project. |
| the sender | The station that made the packet. |
| corpus | The capture of packets. |

**Citations.** `p. N/M` is PDF page N and printed page M of `APRS12c.pdf`,
at the commit above. The printed page numbers do not always increase,
because APRS12c is a compilation. Use the PDF page to find a page. Other
documents have names. `UAP` is `Understanding-APRS-Packets.pdf` in the
same submodule, and a citation of it gives the section.

Errata also cite two earlier editions. They cite them only to show where
a defect first occurs:

- `12b PDF p. N` is a PDF page of `APRS12b.pdf` in the same submodule.
- `1.0.1 PDF p. N` is a PDF page of the original APRS 1.0.1 reference of
  29 August 2000. This edition is not in the repository. The
  [documentation index](../README.md#external-references) links to it.

These two editions are not a reference for the interpretations in these
files.

`APRS-IS q` and `APRS-IS q-alg` are the two APRS-IS pages about the
q-construct, at the snapshots that the documentation index pins. They are
a register in the sense of section 3. APRS12c defers to them when it
names the q-construct (p. 155/131).

**Bytes.** Packets are byte strings, not character strings. These files
use this notation:

- A literal byte is in code font, for example `'!'`.
- These files write a range as `0x21`–`0x7B`.
- `SP` is 0x20.
- "Digit" means `'0'`–`'9'`.

Case is significant, unless a row says otherwise.

**Rules.** Each numbered file has rule tables with these columns:

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|

The ID is in lower case, with dots. It is unique in this directory, and
the tokenizer reports it. Each file owns the prefixes that section 5
lists. These files never use an ID again for a different rule. A rule
table records what APRS12c specifies, with the page. It has no label.

**Catalogue.** Each numbered file lists the places where APRS12c fails
for its formats. The list is one table with these columns:

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|

The ID is `amb.<prefix>.<topic>`. `<prefix>` is one of the rule prefixes
of the file (section 5). `<topic>` is one or more lower-case words,
joined by `.` or `-`. The row has an anchor with the same name,
`<a id="amb.<prefix>.<topic>"></a>`.

The class is one of `unstated`, `conflict` and `ambiguous`. The column
"Rule" gives the general rule of section 3.1 for that class. The last
column tells in one phrase what that rule causes for these bytes. It also
gives the finding, if there is one. A row applies a general rule. It is
not a decision, and it has no label.

**[agreed]** If the general rules do not decide a row, its column "Rule"
contains `none`. Its last column then gives a working choice. A working
choice is the simplest behaviour, and it is not a precedent (section 1).
A run of the field inventory or of a probe can show an effect on more
than 0.01% of the packets of the corpus. Only then does the row go to the
author. While the row waits for the author, it is marked **[open]**.

A catalogue row does not argue for an interpretation. It does not record
what deployed decoders do. Differential testing (RFC Appendix E) finds
how decoders are different. The field inventory counts findings by rule
ID, and it shows how often a row matters.

**[proposed]** **Value files.** A value file has value tables in place of
rule tables. A value table has these columns:

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|

Its IDs follow the rules for rule IDs. The catalogue of a value file has
the last column "What the decoder does". "The decoder" is the tool that
applies a value file. A value file defines its other terms in its section
2. The rows of a value file have no label of their own. The header of the
file states their status.

**Errata.** At some places, two parts of APRS12c disagree. For example,
an example does not match its diagram, a calculation has an error, or two
pages are different. Such a place is a catalogue row of class
`conflict`, with the ID `err.<prefix>.<topic>`. Its ID and its anchor
follow the pattern above. A row keeps its first ID, also when its class
changes later. An error outside the content of APRS12c is not an erratum,
for example a wrong character in the text layer of the PDF.

**Reviewed exceptions.** A file can end with a section that has this
name. An entry in that section departs from the general rules at one
place. The reason is that the author read the passage and found that it
does not say what it means. Each entry is marked **[agreed]** and cites
the page. It tells what the tokenizer does instead, and it gives the
reason of the author. Nothing else in these files departs from the
general rules.

## 3. Interpretation rules and tokenizer model

### 3.1 General rules

**[agreed]** These seven general rules are the complete interpretation.
Each numbered file applies them. The only departures are the reviewed
exceptions (section 2).

**Rule 1. APRS12c specifies the bytes of a field.** The tokenizer follows
what APRS12c specifies.

- Condition: APRS12c specifies the bytes of a field. It uses a format
  diagram, a table or an explicit requirement in its words. The
  requirement can specify a byte set, a width, a count, a delimiter, a
  range or a length limit.
- Finding: If the bytes break the specified format, the tokenizer gives
  `syntax`. If a value is outside a specified range or limit, the
  tokenizer gives `value`. Nothing else gives `syntax` or `value`.
- Ranges of units: A range that the unit itself defines counts as
  specified. These ranges are:
  - minutes and seconds: up to 59;
  - hours: up to 23;
  - a latitude: up to 90;
  - a longitude: up to 180;
  - a bearing or a course: up to 360.
- More than one interpretation: If APRS12c permits more than one
  interpretation, one interpretation that accepts all the bytes is
  sufficient. The tokenizer gives `syntax` or `value` only if every
  interpretation rejects the bytes.
- Text is not an interpretation of this kind. If a marker (a keyword, a
  symbol or a fixed place) starts a structured field, the tokenizer reads
  the bytes as that field. An interpretation of the bytes as a comment or
  as other text does not prevent the finding.
- Obsolete and discouraged formats: If APRS12c marks a format as
  obsolete, the tokenizer gives `obsolete`. If APRS12c advises against a
  format, the tokenizer gives `discouraged`.

**Rule 2. APRS12c does not specify the bytes at a place.** The tokenizer
does not guess.

- Condition: APRS12c has a place for a field, but no requirement for the
  bytes at that place. Examples:
  - a code outside a list that APRS12c does not close;
  - a case that APRS12c does not list;
  - a combination that APRS12c does not mention.
- Finding: `unstated`. This finding has no effect on the verdict.
- Places: The tokenizer looks for a field only where APRS12c names a
  place for it. At any other place, bytes with the format of the field
  stay in the field that contains them, with no finding. That field is
  usually a comment or other text.
  - If APRS12c says only that field A can contain field B, the tokenizer
    looks for B in all of A.
  - If APRS12c specifies one place for B, for example directly after
    another field, the tokenizer looks for B only there.
- Residue: If an unknown code makes the end of the following bytes
  unknown, the rest of the bytes are residue.

**Rule 3. Two parts of APRS12c disagree.** The tokenizer accepts both
parts.

- Condition: Two parts of APRS12c disagree about which bytes are
  permitted.
- Finding: If the bytes match either part, the tokenizer gives no
  finding. The catalogue lists the place as an erratum. These files do
  not say which part is correct.
- Examples: An example packet is a part of APRS12c. It is one of the two
  parts, with the bytes that it shows.
- Typing errors: A typing error is a clear error that no other part of
  APRS12c supports, for example an extra or a missing character. It can
  be in an example, a sentence, a diagram or a table. A typing error
  permits nothing. The catalogue lists it as an erratum.
- If the two parts divide the same bytes into different fields, rule 4
  also applies.

**Rule 4. Two interpretations accept the same bytes.**

- Condition: APRS12c has two interpretations. The two interpretations
  accept the bytes. The two interpretations give different fields, or
  give the bytes different classes.
- Finding: `ambiguous`. The tokenizer puts the finding at the first byte
  where the interpretations are different.
- Token: The tokenizer uses this procedure. The procedure does not
  decide what the sender meant.
  1. If APRS12c permits a structured field here, and the bytes match its
     full format, the bytes are that field.
  2. If not, the bytes are text of the field that contains them.
  3. If two structured fields match, the tokenizer uses the field with
     the stricter format.
- Exception: If every packet of a format has the same ambiguity, and the
  bytes of one packet cannot reduce it, the tokenizer gives no finding.
  The finding would only repeat the count of the format.

**Rule 5. APRS12c names a source outside APRS12c.** Only these sources
count.

- Condition: APRS12c names a register or a definition outside APRS12c
  and defers to it.
- Use: The tokenizer uses that source at the version that this project
  pins. The sources are:
  - `3rdparty/aprs-deviceid` for identifiers of devices and software;
  - the APRS-IS pages for the q-construct;
  - the letter ranges of Maidenhead locators;
  - the sentence frame of NMEA 0183.
- No other source adds a requirement.

**Rule 6. Decoder behaviour and corpus figures do not decide.** What
deployed decoders accept does not change the output of a rule. How often
a format occurs on air also does not change it. The divergence catalogue
and the field inventory record these facts.

**Rule 7. Only a reviewed exception departs from these rules.** An
exception departs from these rules only if the author has reviewed it.
The file records it as a reviewed exception (section 2), with the reason
of the author.

**[proposed]** **The general rules and values.** The seven rules tell what
the tokenizer does. A value file (section 2) applies them to the value of
a token as follows:

- Rule 1: A value has the unit, the scale and the range that APRS12c
  specifies. The arithmetic follows the formula or the example of APRS12c.
- Rule 2: If APRS12c gives the bytes no value, the decoder gives no value.
  If APRS12c leaves a property of a value open, for example its reference,
  the decoder gives the value with a note. The catalogue lists the place.
- Rule 3: If two parts of APRS12c give the same bytes different values,
  the decoder gives no value. If the two parts give the same value, the
  decoder gives that value.
- Rule 4: **[agreed]** If APRS12c permits more than one interpretation,
  the decoder gives the value of the narrowest interpretation. An
  interpretation is narrower than another if it accepts
  fewer byte strings. Thus a field is narrower than text, and the decoder
  gives the value of the field that the tokenizer chose. If no
  interpretation is the narrowest, the decoder gives no value. If the
  tokenizer gives several tokens for one field, the decoder gives the
  value of each token.
- Rules 5, 6 and 7 apply without change.

### 3.2 Output

**[agreed]** The tokenizer is strict. It reports where a packet departs
from the rules of section 3.1. It does not repair the packet. The
divergence catalogue (RFC Appendix E) records the deviations on air. The
tokenizer does not classify them.

**[agreed]** For each packet, the tokenizer produces these outputs:

- **Tokens.** `(rule ID, start, end, depth)`. Start and end are byte
  offsets into the raw TNC2 line. The tokens have these properties:
  - The depth-0 tokens cover the line exactly and in order, with no gap
    and no overlap.
  - If the tokenizer cannot account for some bytes, these bytes are a
    `residue` token. The `residue` token names the rule where the
    tokenizer stopped.
  - If the format specifies the place and the length of a field, the
    field keeps its token when its bytes are wrong.
  - A deeper token is inside one token of the level above. Examples are
    the fields of a Mic-E destination address, the fields inside a
    comment, and the inner packet of a third-party payload.
- **Findings.** `(rule ID, kind, offset)`. The kinds are:

  | Kind | Meaning | Effect on the verdict |
  |---|---|---|
  | `syntax` | The bytes break a specified format (rule 1). | `syntax` |
  | `value` | The bytes match the format, but a value is outside a specified range, or a field is longer than a specified limit (rule 1). | `value` |
  | `ambiguous` | A second interpretation of APRS12c also accepts these bytes (rule 4). | `conform-ambiguous` |
  | `obsolete` | APRS12c marks the format as obsolete. | none |
  | `discouraged` | APRS12c advises against the format. | none |
  | `is-only` | An address that AX.25 cannot contain. It is possible only on APRS-IS. | none |
  | `unstated` | APRS12c has no requirement for the bytes at this place (rule 2). | none |

- **Verdict.** The verdict is the most severe of `conform`,
  `conform-ambiguous`, `value`, `syntax` and `unknown-format`. This list
  is in increasing order of severity. If the tokenizer cannot find the
  data type, the verdict is `unknown-format`.

**[agreed]** The author decided that each format has its own identifier
rule, for example `pos.dti` or `stat.dti`. The token of byte 0 has the
rule ID of this identifier rule. Thus the tokens show the format. The
list is in [01-frame.md section 7](01-frame.md#7-data-type-identifier).

**[agreed]** The tokenizer finds the boundaries of fields. It checks
bytes and specified ranges. It does not calculate values, for example
degrees, knots or decoded telemetry. **[agreed]** The author decided one
exception: a checksum in a format, for example the NMEA `*hh`. The
tokenizer verifies the checksum, because a mismatch shows that the bytes
are not the bytes that the sender sent.

**[proposed]** Values are a separate layer on the tokens and the
findings. A value file states them, and the decoder computes them. The
tokenizer does not change for them.

### 3.3 Counting findings

These paragraphs tell how the tokenizer counts findings and where it puts
them. They describe the output of the tool. They are not interpretations
of APRS12c.

**[agreed]** The author decided this: if bytes already give a `syntax` or
`value` finding, the tokenizer gives only that finding. It does not also
give an `ambiguous`, `unstated` or `obsolete` finding for the same fault.
Thus the tokenizer counts one defect once, at its most severe kind.

**[agreed]** The author decided this: in a field where APRS12c only
recommends printable ASCII, bytes outside 7-bit ASCII give no finding.
Many senders put UTF-8 in these fields, and a finding would hide all
other findings. The field inventory counts these bytes for each field, as
a separate statistic.

**[agreed]** The tokenizer counts and puts findings as follows:

- A field gives a maximum of one `syntax` finding, at its first byte that
  fails.
- If a field is missing, the tokenizer puts its finding at the byte where
  the field was expected. This byte can be the end of the line.
- If consecutive fields are missing at one byte, the tokenizer gives one
  finding, for the first field.
- The tokenizer gives identical findings (the same rule, kind and offset)
  only once.
- If APRS12c specifies a length limit in characters, the tokenizer counts
  the characters of the field as tokenized. Each byte that is not a UTF-8
  continuation byte starts a character. The reason is rule 1: one
  interpretation that accepts the bytes is sufficient.
- If two rules give a finding for one fault at one byte, only the rule
  of the deepest token that contains the byte gives it.

**[agreed]** Kinds. The kinds of findings are as follows:

- These faults give `syntax`:
  - a byte outside a specified byte set;
  - a fixed-width field whose bytes do not match;
  - a missing required field;
  - a list with a number of fields that is not the specified number.
- These faults give `value`:
  - a delimited or variable-length field that is longer or shorter than a
    specified length;
  - a value outside a specified range;
  - a code outside a closed list.
- If APRS12c does not say that a list is open, the list is closed. Words
  such as "such as", "etc." or "include" say that a list is open. A code
  outside an open list gives `unstated`.

**[agreed]** The author decided that a list of software, devices or
other implementations is open, whatever words APRS12c uses for it.
APRS12c cannot limit which implementations exist. **[agreed]** If no
rule accounts for some bytes, they stay in the field of text that
contains them. If there is no such field, the bytes are residue.

## 4. Decoders consulted

The numbered files do not record what deployed decoders do (rule 6). The
earlier draft of this directory recorded it. That draft read the source
code at the commits below, and it did not run the code. The notes are in
the history of this repository at commit `722e30a`. They are a starting
point for the divergence catalogue (RFC Appendix E). This project does
not copy the code, because several of these projects are GPL.

| Decoder | Repository | Commit | Licence | Read |
|---|---|---|---|---|
| Ham::APRS::FAP 1.x (Perl) | <https://github.com/hessu/perl-aprs-fap> | `0447564` | Same terms as Perl | `FAP.pm` |
| Dire Wolf | <https://github.com/wb2osz/direwolf> | `eda1383` | GPL-2.0 | `src/decode_aprs.c` and the files it calls; also `src/digipeater.c` and `src/dwgpsnmea.c` |
| aprslib (Python) | <https://github.com/rossengeorgiev/aprs-python> | `c2a0f18` | GPL-2.0-or-later | `aprslib/parsing/`, `aprslib/base91.py` |
| Xastir | <https://github.com/Xastir/Xastir> | `387d559` | GPL-2.0 | `src/db.c`, `src/util.c`, `src/objects.c` |
| aprsc | <https://github.com/hessu/aprsc> | `963b2e5` | BSD-3-Clause | `src/parse_aprs.c`, `src/incoming.c`, `src/worker.h`; only what an APRS-IS server examines or drops |
| javAPRSlib | <https://github.com/ab0oo/javAPRSlib> | `2a51ce6` | GPL-3.0 / LGPL | `src/main/java/net/ab0oo/aprs/parser/` |
| ebarkie/aprs (Go) | <https://github.com/ebarkie/aprs> | `21df478` | MIT | `*.go` |
| aprs-parser-rs | <https://github.com/Turbo87/aprs-parser-rs> | `e1e1a61` | MIT / Apache-2.0 | `src/` |
| pdn-aprs | <https://github.com/packet-net/aprs-rs> | `4933e3f` | AGPL-3.0 | `src/` |

## 5. Files

| File | Covers | Rule prefixes |
|---|---|---|
| [01-frame.md](01-frame.md) | The TNC2 line, addresses, destination classes, the data type identifier, third-party payloads. | `line`, `addr`, `path`, `dest`, `src`, `dti`, `tp` |
| [02-fields.md](02-fields.md) | Fields that several formats use: timestamps, latitude and longitude, position ambiguity, symbol table and code, the compressed position block, base-91, data extensions, fields in comments. | `time`, `lat`, `lon`, `sym`, `cmp`, `b91`, `ext`, `cmt` |
| [03-position.md](03-position.md) | Position reports, DF reports, Maidenhead beacons, raw NMEA. | `pos`, `df`, `grid`, `nmea` |
| [04-mic-e.md](04-mic-e.md) | Mic-E: destination address, information field, status text. | `mice` |
| [05-object-item.md](05-object-item.md) | Objects, Items, area objects, signposts. | `obj`, `item`, `area` |
| [06-weather.md](06-weather.md) | Weather reports of every format, storm data. | `wx`, `storm` |
| [07-telemetry.md](07-telemetry.md) | Telemetry reports, base-91 comment telemetry, telemetry definition messages. | `tlm` |
| [08-message.md](08-message.md) | Messages, acknowledgements, bulletins, announcements, NWS bulletins, NTS. | `msg`, `bln`, `nws`, `nts` |
| [09-other.md](09-other.md) | Status reports, capabilities, general and directed queries, user-defined data, test packets, frequency specifications in comments. | `stat`, `cap`, `qry`, `udf`, `inv`, `freq` |
| [10-values.md](10-values.md) | Values of the fields of position reports and Mic-E: coordinates, position ambiguity, DAO, course, speed, altitude, symbol, timestamp, data extensions. | `val` |
| [11-values-object.md](11-values-object.md) | Values of the name and the state of Objects and Items. Their position uses the value rules of 10-values. | `val` |
| [12-values-weather.md](12-values-weather.md) | Values of weather reports: wind, the weather fields, the software and unit codes, the MDHM timestamp. | `val` |
| [13-values-telemetry.md](13-values-telemetry.md) | Values of telemetry: the telemetry report, the base-91 block, the definition messages. | `val` |
| [14-values-status.md](14-values-status.md) | Values of status reports: the text, the beam heading and power, the locator. | `val` |
| [examples.json](examples.json) | The expected verdict and findings of each example packet of APRS12c, by page and digest. | — |

## 6. Open items

- `qua-legacy-examples check` compares the example packets of APRS12c
  with these files (RFC section 15, step 4).
  [examples.json](examples.json) contains the verdict that these files
  give each example. These verdicts come from these files, not from a run
  of the tokenizer. If a file changes, whoever changes it derives again
  the entries that it decides. That person uses the same method and does
  not copy the output of the tokenizer.
- Deviation recognisers and the divergence catalogue entries that they
  belong to (RFC Appendix E). Differential testing finds how deployed
  decoders read the places that the catalogue rows list. These files do
  not record it (rule 6). Which deviations get a recogniser is open.
- APRS12c is itself a draft with known issues. If a later draft of
  APRS12c appears, this project checks these files against it page by
  page.
