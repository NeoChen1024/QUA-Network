# Reading of the legacy APRS documents

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |
| Used by | `qua-legacy-tokenize` and `qua-legacy-fields` (package `qua_network.legacy`), RFC section 15, step 4. They read 01-frame, 02-fields, 03-position, 04-mic-e, 05-object-item, 06-weather, 07-telemetry, 08-message and 09-other. |

## 1. Purpose and premise

The files in this directory record how this project's legacy tokenizer
reads the bytes of APRS packets, with APRS12c as the reference. They do
not specify QUA Network, and they do not restate or repair APRS.

**[agreed]** Premise. APRS12c is not a coherent specification. It leaves
fields undelimited, byte sets and receiver actions unstated, and it
contradicts itself between pages, between a diagram and its examples, and
between the editions it compiles. No reading can remove this, and this
project does not try to. The reading is a measuring instrument: it exists
so that the corpus can be divided into fields and counted (RFC section
15, step 4), and so that the places where the document fails are listed
for the divergence catalogue (RFC Appendix E). It makes no claim about
what APRS means. A choice made at one place is a working choice for that
place; it sets no precedent, and two choices need not agree with each
other.

"Conforms" in this project therefore means only that the bytes break no
statement of APRS12c that the rules of section 3 treat as stated. A
packet that conforms may still be read differently by every deployed
decoder.

The text and tables of the legacy documents are not reproduced. Each rule
is described in this project's own words and cites the page it comes from.

An earlier draft of this directory decided every open point of APRS12c
one by one, each as a reading with a status label, and added general
paragraphs to keep those decisions consistent with each other. As the
author decided, that direction is dropped: it amounts to writing a new
edition of APRS, which is not this project's work, and most of the
decisions had no measurable effect on the corpus. As the author decided,
none of the individual decisions of that draft is carried over, including
those that recorded a reason of the author's: the general rules replace
them all. They remain in the history of this repository, up to commit
`722e30a`.

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
edition is a reference for the reading itself. `APRS-IS q` and
`APRS-IS q-alg` name the two APRS-IS pages on the q-construct, at the
snapshots the documentation index pins; they are a register in the
sense of section 3, to which APRS12c defers by naming the q-construct
(p. 155/131).

**Bytes.** Packets are byte strings, not text. A literal byte is written
in code, `'!'`; a range as `0x21`–`0x7B`; `SP` is 0x20. "Digit" means
`'0'`–`'9'`. Case is significant unless an entry says otherwise.

**Rules.** Each file has rule tables with the columns

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|

The ID is lower case and dotted, unique across this directory, and is what
the tokenizer reports. Each file owns the prefixes listed in section 5. An
ID is never reused for a different rule. A rule table states what APRS12c
states, with the page; it carries no label.

**Catalogue.** Each file lists the places where APRS12c fails for its
formats, in one table with the columns

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|

The ID is `amb.<prefix>.<topic>`, where `<prefix>` is one of the rule
prefixes of the file (section 5) and `<topic>` is one or more lower-case
words joined by `.` or `-`; the row carries an anchor of the same name,
`<a id="amb.<prefix>.<topic>"></a>`. The class is one of `unstated`,
`conflict` and `ambiguous`, and the rule is the general rule of section
3.1 that the class falls under. The last column says, in one phrase, what
follows from that rule for these bytes and which finding, if any, is
given. A row is an application of a general rule, not a decision, and
carries no label.

**[agreed]** A row that the general rules do not settle has `none` in its
rule column, and its last column gives a working choice: the simplest
behaviour, which sets no precedent (section 1). Such a row goes to the
author only when a run of the field inventory or of a probe shows that it
touches more than 0.01% of the packets of the capture. It is marked
**[open]** while it waits for the author.

A catalogue row does not argue for a reading, and does not record what
deployed decoders do: how decoders differ is found by differential
testing (RFC Appendix E), and how often a row matters is read from the
field inventory, which counts findings by rule ID.

**Errata.** A place where two parts of APRS12c disagree (an example that
does not fit its diagram, an arithmetic error, two pages that differ) is
a catalogue row of class `conflict` with the ID `err.<prefix>.<topic>`,
formed and anchored as above. A row keeps the ID it was first given,
also when its class turns out to be another. A fault that lies outside the document's
content, such as a wrong character in the PDF's text layer, is not an
erratum.

**Reviewed exceptions.** A file may end with a section of this name. An
entry there departs from the general rules at one place, because the
author has read the passage and found that it does not say what it
means. Each entry is **[agreed]**, cites the page, states what the
tokenizer does instead, and gives the author's reason. Nothing else in
these files departs from the general rules.

## 3. Reading rules and tokenizer model

### 3.1 General rules

**[agreed]** These seven rules are the whole of the reading. Everything
in the numbered files applies them, except the reviewed exceptions
(section 2).

1. **What is stated is followed.** Where APRS12c fixes the bytes of a
   field, by a format diagram, a table or explicit rule text (a byte
   set, a width, a count, a delimiter, a range, a length limit), bytes
   that break it give `syntax`, and a value outside a stated range or
   limit gives `value`. Nothing else gives either finding. A range that
   the unit itself defines counts as stated: minutes and seconds up to
   59, hours up to 23, a latitude up to 90, a longitude up to 180, a
   bearing or course up to 360. Where the text can be read in more than
   one way, bytes conform when at least one reading accepts all of them;
   `syntax` or `value` is given only when every reading rejects them.
   Free text is not such a reading: once a keyword, a symbol or a fixed
   place announces a structured field, the bytes are judged as that
   field, and taking them as comment or other free text instead does
   not make them conform. A form the document marks obsolete gives `obsolete`; one it advises
   against gives `discouraged`.
2. **What is not stated is not guessed.** Where the document provides a
   place but gives no rule for what was found there (a code outside a
   list it does not close, a case it does not give, a combination it
   does not mention), the finding is `unstated`, which does not affect
   the verdict. The tokenizer does not look for a field at a place the
   document does not name for it: bytes of that shape there stay in the
   field that holds them, usually a comment or other free text, with no
   finding. Where the document says only that a field can hold an item,
   the whole field is the place; where it fixes a spot, such as
   directly after another field, only that spot is. Where an unknown
   code leaves the extent of what follows unknown, the rest is residue.
3. **Where the document contradicts itself, both sides are accepted.**
   When two parts of APRS12c disagree about what is allowed, bytes that
   satisfy either part conform, with no finding, and the place is listed
   as an erratum. The reading does not say which part is right. An
   example packet is part of the document and counts as one of the
   sides, in the form it shows. The exception is a passage that is
   plainly a slip of the pen, whether an example, a sentence, a diagram
   or a table, such as a stray or missing character that nothing else
   in the document supports: it is listed as an erratum and allows
   nothing.
   Where the two parts would divide the same bytes into different
   fields, rule 4 applies as well.
4. **Where two readings fit the same bytes, the finding is
   `ambiguous`.** When the document's text can be read in two ways that
   would both accept these bytes but divide or classify them
   differently, the packet gets an `ambiguous` finding at the first byte
   where the two differ. The token follows a fixed default that takes no
   side on what was meant: at a place where the document allows a
   structured field, bytes that match the whole stated shape of that
   field are that field, and bytes that do not are text of the field
   that holds them. Where two structured fields both match, the more
   specific one is taken, the one whose shape constrains more of the
   bytes, as the more specific rule carries a finding (section 3.3).
   An ambiguity that
   every instance of a form carries, and that the bytes of one packet
   cannot narrow, gives no finding: it would only repeat the count of
   the form.
5. **Outside sources count only where APRS12c names them.** A register
   or definition kept elsewhere is used where the document defers to it
   by name, at the version this project pins: `3rdparty/aprs-deviceid`
   for device and software identifiers, the APRS-IS pages for the
   q-construct, the Maidenhead letter ranges, NMEA 0183 sentence
   framing. No other source adds a rule.
6. **Decoder behaviour and corpus figures are recorded, never decisive.**
   What deployed decoders accept and how often a form occurs on air do
   not change what a rule gives. They belong to the divergence catalogue
   and the field inventory.
7. **Only an exception the author has reviewed departs from these
   rules.** It is written as a reviewed exception (section 2), with the
   author's reason.

### 3.2 Output

**[agreed]** The tokenizer is strict. It reports where a packet departs
from the rules of section 3.1 and does not repair it. Deviations seen on
air are the subject of the divergence catalogue (RFC Appendix E), not of
the tokenizer.

**[agreed]** For each packet the tokenizer produces:

- **Tokens.** `(rule ID, start, end, depth)`, as byte offsets into the
  raw TNC2 line. The depth-0 tokens cover the line exactly, in order,
  with no gap and no overlap. Bytes the tokenizer cannot account for
  form a `residue` token, which names the rule at which parsing stopped.
  A field whose place and extent the format fixes keeps its token when
  its bytes are wrong. Deeper tokens lie inside one token of the level
  above: the parts of a Mic-E destination address, items found inside a
  comment, the inner packet of a third-party payload.
- **Findings.** `(rule ID, kind, offset)`. The kinds are:

  | Kind | Meaning | Effect on the verdict |
  |---|---|---|
  | `syntax` | The bytes break a stated layout (rule 1). | `syntax` |
  | `value` | The bytes fit, but a value is outside a stated range, or a field is longer than a stated limit (rule 1). | `value` |
  | `ambiguous` | A second reading of the document's text also fits these bytes (rule 4). | `conform-ambiguous` |
  | `obsolete` | The form is marked obsolete. | none |
  | `discouraged` | APRS12c advises against the form. | none |
  | `is-only` | An address that AX.25 cannot carry; possible only on APRS-IS. | none |
  | `unstated` | The document gives no rule for what was found (rule 2). | none |

- **Verdict.** The most severe of `conform`, `conform-ambiguous`,
  `value`, `syntax`, `unknown-format`, in increasing order.
  `unknown-format` is given when the data type cannot be determined.

**[agreed]** As the author decided, each format has an identifier rule of
its own, such as `pos.dti` or `stat.dti`, carried by the token of the
data type identifier byte, so that the format can be read from the
tokens. The list is in
[01-frame.md section 7](01-frame.md#7-data-type-identifier).

**[agreed]** The tokenizer finds boundaries and checks bytes and stated
ranges. It does not compute values (degrees, knots, decoded telemetry).
**[agreed]** As the author decided, the one exception is a checksum that
a form carries, such as the NMEA `*hh`: the tokenizer verifies it,
because a mismatch means the bytes are not what was sent.

### 3.3 Counting findings

These paragraphs say how findings are counted and placed. They are
properties of the tool's output, not readings of APRS12c.

**[agreed]** As the author decided, when bytes already give a `syntax` or
`value` finding, that finding alone is given, and no `ambiguous`,
`unstated` or `obsolete` finding beside it for the same fault, so that
one defect is counted once, at its most severe kind.

**[agreed]** As the author decided, bytes outside 7-bit ASCII in a field
where APRS12c only recommends printable ASCII give no finding: many
senders put UTF-8 there, and a finding would bury everything else. The
field inventory counts such bytes per field as a statistic of its own.

**[agreed]** A field gives at most one `syntax` finding, at its first
failing byte. A missing field gives its finding at the byte where it was
expected, which may be the end of the line; consecutive missing fields at
one byte give one finding, on the first. Identical findings (the same
rule, kind and offset) are given once. A length limit that the document gives in
characters is counted in characters of the field as tokenized, each byte
that is not a UTF-8 continuation byte starting one, since by rule 1 one
accepting reading is enough. When two rules would each give a finding at one byte
for one fault, only the more specific rule gives it.

**[agreed]** Kinds. A byte outside a stated byte set, a fixed-width
field whose bytes do not fit, a missing required field and a list with a
number of fields other than the one stated give `syntax`. A delimited or
variable-length field longer or shorter than a stated length, a value
outside a stated range and a code outside a closed list give `value`. A
list is closed unless the document says it is not, as "such as", "etc."
or "include" do; a code outside an open list gives `unstated`.
**[agreed]** As the author decided, a list that names software, devices
or other implementations is open, whatever its wording: the document
cannot limit which implementations exist. **[agreed]** Bytes
that no rule accounts for stay in the free-text field that holds them;
where there is none, they are residue.

## 4. Decoders consulted

The numbered files do not record what deployed decoders do (rule 6). The
earlier draft of this directory did, from source code read and not run at
the commits below; those notes are in the history of this repository at
commit `722e30a` and are a starting point for the divergence catalogue
(RFC Appendix E). The code is not copied: several of these projects are
GPL.

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
  to (RFC Appendix E). How deployed decoders read the places that the
  catalogue rows list is found by differential testing, not recorded in
  these files (rule 6); which deviations get a recogniser is open.
- APRS12c is itself a draft with known issues. When a later draft of the
  reference appears, this reading is checked against it page by page.
