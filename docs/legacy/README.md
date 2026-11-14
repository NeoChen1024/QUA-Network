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

**[agreed]** Output. For each packet the tokenizer produces:

- **Tokens.** `(rule ID, start, end, depth)`, as byte offsets into the
  raw TNC2 line. The depth-0 tokens cover the line exactly, in order, with
  no gap and no overlap. Bytes the tokenizer cannot account for form a
  `residue` token, which names the rule at which parsing stopped.
  **[agreed]** A field whose place and extent the format fixes, by
  delimiters, a fixed width or a fixed layout, keeps its own token when
  its bytes are wrong, with one `syntax` finding at the first byte that
  fails; only bytes whose rule cannot be told, at that level or inside
  such a field, are residue. A field cut short by the end of the field
  around it covers the bytes present, and its finding is placed where
  the first missing byte was expected, which may be the end of the
  line. After a field with a finding, reading continues at the next
  field wherever the start of that field can be told. Deeper
  tokens lie inside one token of the level above: the parts of a Mic-E
  destination address, items found inside a comment, the inner packet of a
  third-party payload. **[agreed]** The token of the data type identifier
  byte carries the identifier rule of the format it selects, such as
  `pos.dti` or `stat.dti`, so that the format can be read from the tokens.
  The `dti.*` rules of 01-frame give the dispatch and its findings.
  **[agreed]** That rule is the identifier rule of the most specific
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

**[agreed]** The tokenizer finds boundaries and checks bytes and ranges.
It does not compute values (degrees, knots, decoded telemetry). Decoding is
a separate layer built on the tokens. **[agreed]** The one exception is a
checksum that a form carries, such as the NMEA `*hh`: the tokenizer
verifies it, because a mismatch means the bytes are not what was sent.
**[agreed]** A rule that depends on what the line does not show, such
as the connection a packet arrived on, is not checked.

**[agreed]** An ambiguity that can be seen in the bytes produces an
`ambiguous` finding. It can be seen when another reading listed in an
ambiguity entry would divide or classify these particular bytes
differently: two `!DAO!` candidates in one comment, GGA bits in a
compressed `T` byte whose `c` byte also lies in the course range.

**[agreed]** A listed reading is a reading of the document's text. A
way of reading the bytes that contradicts an explicit statement of
APRS12c is recorded in the entry as decoder behaviour, not as a reading,
and produces no finding. Recognising such packets is the work of the
deviation recognisers. **[agreed]** A listed reading comes from the
document's text, or from a question that the text leaves open. A way
of reading that adds something the document never mentions, such as a
prefix or a form that only some decoders take, is decoder behaviour
too, even where it contradicts nothing.

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
**[agreed]** The same holds for a finding derived from those bytes: a
check across several fields, or an `obsolete` or `unstated` finding on
the same defect, is not given where a rule already reports the bytes as
`syntax` or `value`. Defects that are independent of each other keep
their own findings. **[agreed]** As the author decided, a finding for a
missing field reports the byte where it is placed, where the field was
expected, although that byte belongs to the token that follows: no
`ambiguous` finding is given on bytes that include it
([06-weather amb.wx.tail](06-weather.md#amb.wx.tail)).

**[agreed]** Which findings are the other reading's own. A finding of
the other reading is shared with this reading, and does not count
against it, when this reading gives a finding of the same kind at the
same offset. The rule ID is not compared: two readings name the same
bytes with different rules by construction.

**[agreed]** Placing a finding. A field gives at most one `syntax`
finding, at its first failing byte. A `syntax` or `value` finding goes
on the most specific rule whose bytes are at fault, at the first byte
at fault: the first byte past a limit, or the place where a missing
byte was expected. An `ambiguous` finding goes on the rule this reading
gives the bytes, at the first byte where the readings divide them
differently. An entry may state an exception, and then says so.

**[agreed]** Placing an `unstated` or `obsolete` finding. As the author
decided, these findings are placed as Placing a finding places the
others. An `obsolete` finding goes on the rule of the obsolete form, at
the first byte of its token. An `unstated` finding goes on the rule
whose form or value the document leaves unstated for what was found,
at the first byte of what was found:

- a form the document does not state, such as an unlisted code or a
  combination it does not list: the first byte of the form, with its
  letter or opening delimiter;
- a value written in a way the document does not state, such as a
  checksum in lower-case hexadecimal: the first byte of the value;
- a byte outside a set the rule states: that byte;
- a field that fits none of its stated forms: the first byte after the
  part that every stated form shares;
- nothing, at a place where the rule allows something but does not
  require it: the place where it was expected.

An `SP` or other separator between the form and what comes before it
is not part of what was found. An entry may state an exception, and
then says so. An earlier draft also gave an element of unstated width
as an example of the first case. As the author decided, its only
instance, the raw rain counter, gets no such finding
([06-weather amb.wx.rawrain](06-weather.md#amb.wx.rawrain)).

**[agreed]** A field defined as another rule. As the author decided, a
field that a format defines as an instance of a rule of another entry,
such as a status timestamp defined as
[`time.dhm`](02-fields.md#time.dhm), is tokenized as that rule: its
token carries that rule's ID, and its bytes give that rule's findings.
The field's own ID names it in the tables and in the findings that
only the field gives, such as a missing field (When a fixed field is
present). The timestamps of [`pos.time`](03-position.md#pos.time) and
[`obj.time`](05-object-item.md#obj.time) are read this way. A field
whose bytes are only read or checked as those of another rule, and
that has a limit or findings of its own, keeps its own ID, as
[`stat.text`](09-other.md#stat.text) checked as `cmt.text` and
[`tp.dest`](01-frame.md#tp.dest) read as `addr.dest` do.

**[agreed]** When a fixed field is present. As the author decided, the
entry of a field whose place and width the format fixes names the test
that makes the field present. When the test fails, the field is
missing: it uses no byte, gives `syntax` against its ID at the byte
where it was expected, as any missing field does (Kinds by situation;
Placing a finding), and reading continues at that same byte. Where an
entry names no test, the field is always present: its fixed bytes are
its token even when they are wrong, with one `syntax` finding at the
first byte that fails (Output). Only a place that holds no byte at all,
because the field around it has ended, leaves such a field missing,
which is the empty required field of Kinds by situation. A place where
several forms can stand names no test either: when none of them
matches, the finding goes on the selector rule of the place, or, where
it has none, on the form the entry takes by default, as Forms that can
stand at one place says. The timestamps
[`pos.time`](03-position.md#pos.time) and
[`obj.time`](05-object-item.md#obj.time) name no test and are always
the seven bytes the layout fixes. The wind field of a complete weather
report and the leading elements of a positionless report name one
([06-weather sections 5.1](06-weather.md#51-uncompressed-position) and
[6.2](06-weather.md#62-order-and-end-of-the-data)). Where a missing
field's finding stands beside others at its byte, Precedence and
Missing fields at one byte decide.

**[agreed]** One byte may carry several findings from different rules.
Each keeps its own rule ID; they are not merged. Identical findings
(the same rule, kind and offset) are given once.

**[agreed]** One fault, two rules. When two rules would each give a
finding at the same byte for the same fault, only the finding on the
more specific rule is given, as Placing a finding asks. The case
in point is a Mic-E destination with a lower-case letter, or with more
than six bytes in its callsign part: the part rule or `mice.dest` of
[04-mic-e](04-mic-e.md#3-destination-address) reports the byte, and
`addr.dest` gives no `syntax` finding there. **[agreed]** The address
field still reports its other faults as on any address, such as its
SSID or a `'*'` after it
([04-mic-e section 3](04-mic-e.md#3-destination-address)). Findings for different
faults keep their own rules, by the paragraph above, also at one byte.
This is the default; an entry may state an exception, and then says
so. **[proposed]** The more specific rule is the one whose field is
narrower, or the one of the format the packet is read as over the
general rule of 01-frame.

**[agreed]** Missing fields at one byte. As the author decided, when
consecutive missing fields fail at the same byte, only the first gives
its `syntax` finding. The later missing fields at that byte, and a
residue that starts at that byte, give no finding: the bytes there are
not what the format expects next, which is one fault, and the first
finding reports it (compare Precedence). Their tokens are unchanged:
a missing field still has none, and the residue keeps its token and
the rule it names. The rule covers missing fields and residues only; a
token read from that byte keeps its own findings (One byte may carry
several findings). The case in point is a positionless weather report
whose four leading places all hold other bytes: it gives one finding,
on the wind direction, where it would otherwise give one for each
leading element and one for the residue after them
([06-weather section 6.2](06-weather.md#62-order-and-end-of-the-data)).
**[agreed]** A count finding given at the end of a field, where the
next separator of a list was expected, reports fields missing there
and counts as a missing field for this rule, as for an NTS line whose
last field is empty
([08-message section 8](08-message.md#8-nts-radiograms)).
An earlier draft did not say whether such findings were one fault or
several, and the files gave one finding for each missing field and
for the residue.

**[agreed]** The "In the bytes" paragraph of an ambiguity entry that
only applies the tests of this section to the reading taken is not a
decision of its own. It carries no label, takes the status of the
reading it applies, and is checked against these tests rather than
decided. When the reading changes, the paragraph is derived again. A
paragraph that builds the other reading, or states something the tests
do not give, is a decision and keeps its label. The same holds for any
text in the files that only applies an **[agreed]** rule of this
section to a case: it cites the rule and carries no label of its own.

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

**[agreed]** Classes that a keyword declares. Where APRS12c itself
names a byte string as the identifier of a class, the class is
declared by that keyword: when the bytes match it, they are that
class, and the faults that follow are reported inside the class, by
its own rules. The keywords are the data type identifiers, the
addressees `BLN` and `NWS-`, the telemetry keywords `PARM.`, `UNIT.`,
`EQNS.` and `BITS.`, the NTS format identifier `N`, type byte,
`'\'` of p. 98/76, and, as the author decided, the altitude marker
`'/A='`, with which p. 43/27 introduces both altitude forms of comment
text. A class with no such keyword, recognised by its shape alone,
follows the paragraph above. Message text that starts
with `'?'` is not a keyword class: the query type is the text itself
(p. 103/79), so a directed query is recognised by its whole shape
([08-message section 2.1](08-message.md#21-kind-of-packet), case 5;
[09-other section 4.1](09-other.md#41-directed-queries)). The D-STAR
marker and the prefixes of the data extensions are decided in their
own entries. **[agreed]** As the author decided, when the bytes of one
packet match several keywords, the classes nest. The first keyword in
the bytes declares a class. A later keyword counts only in a field
that the innermost class holding that field names for it (Where
comment items are looked for; Obsolete and nested forms), and then
declares a class inside that one; in any other field its bytes are
whatever that field holds. The data type identifier `':'` thus
declares the `':'` class, an addressee `BLN` or `NWS-` declares the
bulletin or NWS bulletin class inside it, and a telemetry keyword at
the start of a bulletin's text is bulletin text, since the bulletin
class names no field for it
([08-message section 2.1](08-message.md#21-kind-of-packet)). Two
altitudes in one comment each declare a class inside the class that
holds the comment, not one inside the other. An earlier draft let the first
keyword in the bytes declare the class and counted a later keyword
only in a field that this class named for it. The data type
identifier comes first in the bytes of every packet, so that wording
did not say how an addressee keyword after it declares a class, and
the files called the addressee the first keyword. A later draft
nested each class inside the one declared before it, which put a
second altitude of a comment inside the first.

**[agreed]** Items that stop fitting. As the author decided, an item
that a keyword declares in free text, and whose bytes stop fitting its
form, ends at its last fitting byte, and at the latest where its width
ends. Its one `syntax`
finding goes at the first byte that does not fit, which is where its
token ends: a byte of the wrong class, the place where a byte was
expected when the field ends first, or a byte that the form excludes
right after its width, such as a seventh digit after the six of an
altitude. The bytes after the token are text of the field again.
Unlike a field whose extent the format fixes (Output), such an item
does not keep its full width. The altitude after its keyword `'/A='`
is the case in point ([02-fields section 8.2](02-fields.md#cmt.alt)).
A form recognised by its shape alone is not such an item: the
paragraph on such forms above decides whether bytes that do not fit
it are the form or text. An earlier draft stated this paragraph for
any item found in free text. A later one said that in free text such
a form that does not fit is always text, which the fixed places and
delimiters of that paragraph do not bear out.

**[agreed]** Symbols that a format names. Where the diagram or the
rule text of a format fixes the symbol table byte, that byte is
matched as it stands: the DF symbol `/\` (diagrams and text of
p. 52/34 and p. 53/35), the area object `\l` (p. 78/60), the signpost
`\m` (p. 80/62), the storm symbols `\@` and `/@` (p. 87/67) and the
`/G` of a Mic-E locator (p. 73/55). Another table byte, or an overlay
character in its place, makes a different symbol: since 2007 every
alternate symbol may take each of 36 overlays (p. 141/117), and
chapter 18 uses overlaid symbols as symbols of their own (p. 118/94,
p. 119/95). Where the diagram leaves the table byte open, any table
byte counts. The complete weather formats name only the symbol code
`'_'` (p. 85/65) and leave their table column open (p. 85/65,
p. 86/66), and `\_` takes an overlay (p. 140/116), so a weather report
may have any table byte. A wider reading, that a named `'\'` stands
for the alternate table and so accepts any overlay (p. 125/101 writes
a generic alternate symbol as `\$`), stays a listed reading: an
overlaid `l`, `m` or `@` report that this reading would read as the
named item gets an `ambiguous` finding by the tests above, and
Precedence applies.

**[agreed]** Pages that disagree. When parts of APRS12c disagree, the
format diagram and the explicit rule text are followed over an example.
Between two rule texts, the page about the format in question is
followed over a general page. An example may fill a gap that the
diagram leaves, such as a separator it does not draw or a sign, but may
not override what the diagram shows; an example of the earlier edition
APRS 1.0.1 may fill such a gap where APRS12c gives none, unless a later
text sets that example aside. Between texts of different editions, the
later text is followed: a later text sets an earlier one aside when it
says so, and also when it defines a form that the earlier text rules
out, as the Mic-E type codes of the APRS 1.2 addendum do for the 1.0.1
prohibition on p. 72/54. Each such case
is recorded as an erratum, whichever side is followed.

**[agreed]** A form that the text describes, even without a full
syntax, is a form the document defines: bytes of that form get no
finding, and the strict bullet of the next paragraph applies only to
bytes outside the description.

**[agreed]** Forms that can stand at one place. They are tried in a fixed
order: a form that a marker byte or keyword selects first, then the
more specific form before the wildcard that covers it, then a current
form before an obsolete one. The first that matches is taken. An
overlap that every instance carries gives no finding. When no form
matches, one `syntax` finding goes on the selector rule of the place;
where a place has no selector rule, the entry names the form that is
taken by default and carries the finding, as `time.dhm` does for a
seven-byte timestamp. A delimiter ends a field at its first
occurrence, unless the field's content may hold it; a form anchored at
the end of a field, such as an NWS reference after `'{'`, is read from
the end.

**[agreed]** Kinds by situation. The files report like situations
with the same kind:

- A byte outside the byte set that a rule states: `syntax`.
- A fixed-width field whose bytes do not fit, including a value written
  with more or fewer digits than its width: `syntax`. Nothing delimits
  the field, so excess bytes cannot be counted against it.
- A delimited or variable-length field that is not empty and is longer
  or shorter than a stated length: `value`, at the first byte past the
  limit when it is too long.
- **[agreed]** An empty required field is a missing field: `syntax`
  where its first byte was expected. A list with too few or too many
  fields is a matter of structure: `syntax` at the separator, or the
  end, where the count departs from the one stated; the fields after it
  keep their tokens. A list whose fields come in groups, such as the
  three coefficients of a telemetry channel, that stops inside a group
  has too few fields.
- A value outside a stated range, or a code outside the closed set of
  values that a table or a form defines: `value`.
- A code that a stated prohibition covers ("do not use"): `syntax`.
- A code outside a list that the document does not close, or whose
  list it leaves to a register kept elsewhere, at a place the document
  leaves open for it, or a combination of pieces that are each allowed
  and about which the document says nothing: `unstated`. Where the
  document says that other codes are allowed, as a list given with
  "such as" or "etc." does: no finding. **[agreed]** The code keeps its
  token when its extent is known. When an unknown code leaves the
  extent unknown, as an element letter the document does not define,
  reading stops there and the bytes from it are judged as whatever may
  stand next: a tail, a residue, or `unknown-format`.
- **[agreed]** A register kept outside APRS12c, to which the document
  defers, is used at the version this project pins, and the entry names
  that version. The Mic-E device codes and the software identifiers of
  `dest.tocall` are checked against `3rdparty/aprs-deviceid` this way:
  new devices appear faster than the document is revised, so the
  register, not the document's examples, is the list. A list that is
  defined elsewhere but kept as no versioned register, such as the
  q-construct codes of APRS-IS or the sentence types of NMEA 0183, is
  checked by shape only, together with any checksum the form carries.
- **[agreed]** A range that the document takes from a source it names,
  such as the Maidenhead letter ranges, counts as stated.
- **[agreed]** Where the listed readings differ only in how much they
  accept (a byte set, a range, contiguity, a count), the narrowest
  reading that the text supports is taken, and the wider ones are
  tested for an `ambiguous` finding by the tests of this section. A
  range that the unit itself implies counts as stated, so a value past
  it gives `value`: minutes and seconds `00` to `59`, a bearing or
  course up to 360, a latitude up to 90 and a longitude up to 180, and
  base-91 coordinates within those. Where the document calls the wider
  form interchangeable with the narrow one, the wider is stated and is
  taken as it stands.
- **[agreed]** A byte pattern outside every form the document defines,
  such as a relaxed number or a fill that no form shows, is not that
  form. At a place the format fixes it gives `syntax`; in free text it
  is text, with no finding. Recognising the wider forms that senders
  use and decoders accept is the work of the deviation recognisers. An
  earlier draft accepted such forms with `unstated`.
- A form marked obsolete: `obsolete`. A form that is only "not
  recommended", discouraged or advised against: `discouraged`.
- **[agreed]** Bytes outside 7-bit ASCII in a field where APRS12c only
  recommends printable ASCII: no finding. Many senders put UTF-8 there,
  and a finding would bury everything else. The field inventory counts
  such bytes per field as a statistic of its own, outside the findings.
- A departure from a stated sending rule that receivers are told to
  accept, such as the case of a locator or of `MHz`: `syntax`.
  **[agreed]** A length over a stated limit stays `value`, by the
  bullet on lengths above, even where receivers are told to accept
  longer text, as they are for message and bulletin text (p. 93/71,
  p. 96/74, p. 97/75) and for telemetry names and units (p. 91/71).
- **[agreed]** Letter case. Case is significant (section 2). Where the
  document states a case as a sending rule that receivers are told to
  accept, another case is recognised and gives `syntax`, as above.
  Where it states the case with no such allowance, another case is not
  the form: the bytes are text or another class, with an `ambiguous`
  finding where the reading that folds case accepts the whole field.
  Where it states no case, another case is recognised and gives
  `unstated`. What decoders accept does not change the kind.
- A mixture of forms that are each allowed: no finding where the
  document calls them interchangeable, `value` where it calls the
  combination unknown, and `unstated` where it says nothing. A mixture
  inside one value is a field that does not fit, as above.

**[agreed]** Obsolete and nested forms. An obsolete form the document
describes is recognised when its own defining bytes match; it gets
`obsolete` at its first byte, and its inside is read only as far as the
document describes it. A structure the document describes one level
deep is read the same way where it recurs deeper, with `unstated` at
each further level. A form at a place the document does not describe
for it is not recognised there.

**[agreed]** Where comment items are looked for. An item that a field
of free text can hold, such as the altitude, the DAO, the base-91
telemetry block, a data extension (PHG, RNG, DFS and the other forms
of chapter 7), a frequency, or the braces of a corridor or signpost,
is recognised only in the fields that its own chapter of APRS12c names
for it. The same shape in any other field is text, with no finding.
This is the last sentence of Obsolete and nested forms applied to
items: a form at a place the document does not describe for it is not
recognised there. The exception is `'!x!'`, which p. 110/86 attaches
to any packet that contains it, and which is looked for in all free
text, as [amb.cmt.noarchive](02-fields.md#amb.cmt.noarchive) decides.
[02-fields section 8.2](02-fields.md#82-items-found-inside-a-comment)
lists the fields that each item is looked for in.

**[agreed]** Fixed spots and repeats. An item that the document places
at a fixed spot of a field, such as the start of a comment, is read
only there, and only once. Where the text leaves the spot open, an
example of the document may fix it (Pages that disagree). Later bytes
of the item's shape are text; they give an `ambiguous` finding where
the reading that takes them as the item accepts the whole field, by
the tests above and Precedence. An item that the document lets stand
anywhere in a field is recorded wherever it appears, and two or more
occurrences in one field give an `ambiguous` finding on each, as the
altitude, the DAO and `'!x!'` do.

**[agreed]** Separators and padding that a diagram does not show. A byte
between two fields that the diagram does not show, such as an extra `,`
or `SP` padding, belongs to the next field, which is usually text. It
gets `ambiguous` where a reading of the document's text takes it as a
separator and accepts the whole field, and no finding where every
instance of the form carries it. The entry names the text that the
separator comes from.

**[agreed]** Length limits count bytes, not characters, of the field as
tokenized, including the items found inside it, except an item that a
page of the document says does not count; the entry cites that page.
Where limits nest, such as a field inside `msg.text` or a comment
inside `line.info`, each is checked on its own rule, and the excess is
reported at the first byte past each limit.

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
  to (RFC Appendix E). Each way of reading that an entry records as
  decoder behaviour (section 3) gives no finding and is left to them;
  which of them get a recogniser is open. Some files list candidates in
  their own open items.
- APRS12c is itself a draft with known issues. When a later draft of the
  reference appears, this reading is checked against it page by page.
