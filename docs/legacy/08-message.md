# Messages, bulletins and announcements

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, tokenizer model and decoder commits: [README](README.md). |

## 1. Scope

This file states how the tokenizer reads packets with the data type
identifier `':'`:

- messages to a station or a group, with or without a message
  identifier, including the reply-ack form;
- acknowledgements and rejections;
- general bulletins, announcements and group bulletins;
- National Weather Service bulletins;
- NTS radiograms carried in message text;
- the obsolete bulletin form without a data type identifier.

Two other kinds of `':'` packet are only recognised here and then read
elsewhere: telemetry definition messages
([07-telemetry.md](07-telemetry.md)) and directed station queries
([09-other.md](09-other.md)).

Byte offsets below count from the first byte of the information field;
the data type identifier `':'` is offset 0.
[01-frame.md](01-frame.md#7-data-type-identifier) dispatches on it, and
its token carries the identifier rule of the kind of packet that
section 2.1 decides.

**Text bytes.** Where a rule below says "text bytes", it means: `SP` to
`'~'` (0x20-0x7E), and well-formed multi-byte UTF-8 sequences (p. 93/71,
p. 96/74). Any other byte (a control byte such as CR or LF, 0x7F, a byte
of 0x80 or above that is not part of a well-formed sequence) gives
`syntax`. A field gives one such finding, at its first such byte, on the
most specific rule that holds the byte: an
[`nts.field`](#nts.field) in an NTS line, a field of
[07 section 4](07-telemetry.md#4-telemetry-definition-messages) in a
definition message, and otherwise the text field itself
([README section 3](README.md#3-tokenizer-model), Placing a finding).
An earlier draft gave a finding at every such byte. Reading:
[amb.msg.text](#amb.msg.text).

## 2. Common frame

Every `':'` packet has, after the identifier, a 9-byte addressee and a
second `':'` (p. 93/71, p. 135/111). The identifier's token carries one
of three rules of this file, or a rule of 07 or 09 (section 2.1).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.dti"></a>`msg.dti` | Identifier of a message | `':'` at offset 0 of a message, an acknowledgement or a rejection, NTS lines included (sections 3, 4 and 8). | One of the identifier rules | Fixed 1 byte | p. 31/17, p. 93/71 |
| <a id="bln.dti"></a>`bln.dti` | Identifier of a bulletin | `':'` at offset 0 of a bulletin or announcement (section 6). | One of the identifier rules | Fixed 1 byte | p. 31/17, p. 96/74 |
| <a id="nws.dti"></a>`nws.dti` | Identifier of an NWS bulletin | `':'` at offset 0 of an NWS bulletin (section 7). | One of the identifier rules | Fixed 1 byte | p. 31/17, p. 97/75 |
| <a id="msg.addr"></a>`msg.addr` | Addressee | Offsets 1-9, exactly 9 bytes: a name of 1-9 bytes followed by `SP` bytes to fill 9. Depth-1 tokens `msg.addr.name` and `msg.addr.pad`. Bulletin and NWS addressees are tokenized as `bln.addr` and `nws.addr` instead (sections 6 and 7). Reading: [amb.msg.addressee](#amb.msg.addressee). | Required | Fixed 9 bytes | p. 93/71 |
| <a id="msg.addr.name"></a>`msg.addr.name` | Name | Letters, digits and `'-'`. Another byte from `'!'` to `'~'` other than `':'` gives `unstated`; `SP` inside the name (a space followed by a non-space), `':'`, or a byte outside `'!'`-`'~'` gives `syntax`. An all-space addressee gives `syntax`. | Required | First `SP`, or offset 9 | p. 93/71 |
| <a id="msg.addr.pad"></a>`msg.addr.pad` | Padding | `SP` bytes. | Required when the name is shorter than 9 bytes | Offset 9 | p. 93/71 |
| <a id="msg.sep"></a>`msg.sep` | Separator | `':'` at offset 10. Any other byte there gives `syntax`; the tokenizer does not look for an earlier `':'`. | Required | Fixed 1 byte | p. 93/71 |

**[proposed]** The addressee is part of the information field, not an
AX.25 address. The tokenizer does not check it as a callsign and reports
no `is-only` finding for it. UAP 2.5.2 notes that addressees of Internet
services need not be callsigns.

Where the findings of the addressee go, by
[README section 3](README.md#3-tokenizer-model) (Output, Placing a
finding). The 9 bytes are one fixed field, so one `syntax` finding is
given for them, at the first byte that fails, under the rule of the
name part (`msg.addr.name`, `bln.group` or `nws.level`), the most
specific rule that holds it. For a `SP` inside the name that byte is
the first byte after the padding has begun that is not `SP`. A
`msg.addr` or `nws.addr` whose name part starts with `SP` has no name,
whatever follows, so its finding is at that `SP`, where the name was
expected. A field that ends inside the 9 bytes gives `syntax` at its
end against `msg.addr`, `bln.addr` or `nws.addr`, unless a byte before
its end already failed; this includes a field that ends where the name
part would start, which gives that finding and no finding for the
missing name. A field that ends at offset 10 gives `syntax` against
`msg.sep` at offset 10. Nothing after that is read. When the byte at
offset 10 is present but is not `':'`, the `msg.sep` token keeps it,
and the text is still read from offset 11 and classified by section
2.1.

**[proposed]** The `unstated` finding for other printable bytes of the
name part is given once, at the first of them.

### 2.1 Kind of packet

**[proposed]** After the separator the tokenizer decides the kind of
packet in this order and stops at the first that applies (reading:
[amb.msg.order](#amb.msg.order)):

1. The addressee starts with `BLN`: a bulletin or announcement, section 6.
2. The addressee starts with `NWS-`: an NWS bulletin, section 7.
3. The text after the separator has the shape of an acknowledgement or a
   rejection, section 4.
4. The text starts with `PARM.`, `UNIT.`, `EQNS.` or `BITS.`, in upper
   case: a telemetry definition message, read by
   [07 section 4](07-telemetry.md#4-telemetry-definition-messages)
   (p. 90/70 to p. 92/72). Its text is still `msg.text` for the length
   limit, which a `PARM.` or `UNIT.` list at its stated field maxima
   exceeds by one byte (derived in 07).
5. The text starts with `'?'` and matches a directed station query
   ([09-other.md section 4.1](09-other.md#41-directed-queries),
   p. 103/79): read there. If it does not match, go on to 6.
6. Otherwise: a message, section 3.

In cases 1 and 2 the text can get an `ambiguous` finding where it has
the shape that case 3, 4 or 5 tests and the packet, read as that kind,
would give no `syntax` or `value` finding of its own
([amb.msg.order](#amb.msg.order)).

A finding "of its own" is one that the other reading gives and this
reading does not: this reading gives no finding of the same kind at the
same offset, whatever its rule. A `syntax` or `value` finding that both
readings give elsewhere in the packet does not stop an `ambiguous`
finding ([README section 3](README.md#3-tokenizer-model), Which
findings are the other reading's own). The same holds for every
condition of this kind in this file.

The token of byte 0 carries the identifier rule of the kind decided:
`bln.dti` in case 1, `nws.dti` in case 2, `msg.dti` in cases 3 and 6,
[`tlm.def.dti`](07-telemetry.md#tlm.def.dti) in case 4, and
[`qry.dir.dti`](09-other.md#qry.dir.dti) in case 5
([README section 3](README.md#3-tokenizer-model)). It is assigned once
the kind is decided.

**[proposed]** Tokens of cases 4 and 5. In case 4 this file delimits
the text as in section 3: a `msg.text` token up to the first `'{'`, its
byte and length rules, and the message identifier; 07 tokenizes inside
`msg.text`. In case 5 the text from offset 11 is 09's, at the level of
the addressee, with no `msg.text` token; it is still message text for
the length limit of `msg.text`, whose `value` finding this file gives,
as in case 4 and as [amb.msg.order](#amb.msg.order) assumes. A message
whose text starts
with one of the four keywords in another case is read here as a
message; whether it gets the `ambiguous` finding of
[amb.tlm.keyword](07-telemetry.md#amb.tlm.keyword) is 07's to decide.

**[proposed]** The other readings in this file. Under the conditions
"read as that kind" and "read as a message by section 2.1 from case 3
on", the other reading reads the whole field after the identifier, its
addressee as `msg.addr`. Its rule IDs differ from this reading's; a
`syntax` or `value` finding is its own when this reading gives no
finding of the same kind at the same offset, as
[README section 3](README.md#3-tokenizer-model) (Which findings are
the other reading's own) has it for every other reading. A text that
matches a directed query gets no `syntax` or `value` finding from the
rows of [09-other.md section 4.1](09-other.md#41-directed-queries), which give
none to a matching text; the `value` finding of the `msg.text` length
limit (case 5) is the only one it can give. Whether a definition message (case 4) gives one is 07's to decide. The
bytes that the precedence rule looks at are: the text from offset 11
for [amb.msg.order](#amb.msg.order) and [amb.msg.ack](#amb.msg.ack);
the addressee for [amb.bln.forms](#amb.bln.forms) and for an `NWS-`
word that is not listed ([amb.nws.addressee](#amb.nws.addressee)); and
the whole field after the identifier for an addressee that starts with
`NWS_`, `SKY`, `CWA` or `BOM`, since reading (c) of that entry would
read every byte of it differently. That last finding is given in cases
3, 5 and 6, and is 07's to decide in case 4
([07 section 4](07-telemetry.md#4-telemetry-definition-messages)). The `ambiguous` findings
are given against `bln.text` or `nws.text` at offset 11
([amb.msg.order](#amb.msg.order)), `bln.addr` at offset 4
([amb.bln.forms](#amb.bln.forms)), and `nws.level` at offset 5 or
`msg.addr` at offset 1 ([amb.nws.addressee](#amb.nws.addressee)).

## 3. Messages

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.text"></a>`msg.text` | Message text | From offset 11. Text bytes, except `'{'`. More than 67 bytes gives `value`. May be empty. Reading: [amb.msg.text](#amb.msg.text). | Required, 0 bytes allowed | First `'{'`, or end of information field | p. 93/71 |
| <a id="msg.id.open"></a>`msg.id.open` | Identifier marker | `'{'`. | Optional; its presence asks for an acknowledgement | Fixed 1 byte | p. 93/71 |
| <a id="msg.id"></a>`msg.id` | Message number | 1-5 letters or digits, to the end of the information field. 6 or more letters or digits give `value`; any other byte gives `syntax`. Not used in the reply-ack form. Reading: [amb.msg.id](#amb.msg.id). | Required after `msg.id.open` | End of information field | p. 93/71 |
| <a id="msg.id.mm"></a>`msg.id.mm` | Reply-ack: own number | 2 letters or digits. Another count of letters or digits gives `value`. | Required in the reply-ack form | `'}'` | p. 95/73 |
| <a id="msg.id.close"></a>`msg.id.close` | Reply-ack separator | `'}'`. Its presence alone tells the receiver that the sender handles reply-acks. | Required in the reply-ack form | Fixed 1 byte | p. 95/73 |
| <a id="msg.id.aa"></a>`msg.id.aa` | Reply-ack: acknowledged number | 0 or 2 letters or digits: the number of a message from the addressee that this packet acknowledges. Another count gives `value`. | Optional | End of information field | p. 95/73 |

**[proposed]** The form after `msg.id.open` is the reply-ack form when it
contains `'}'`, and the plain form otherwise. Reading:
[amb.msg.replyack](#amb.msg.replyack).

**[proposed]** The information field ends at the last byte of the frame.
A trailing CR, LF or `SP` is part of the field: after a message number it
makes the number fail (`syntax`), and in text without a number it gives
`syntax` for CR and LF only.

Findings of the identifier parts, by
[README section 3](README.md#3-tokenizer-model) (Kinds by situation,
Placing a finding, Precedence). `msg.id` gives `value` at its sixth
byte, the first byte past the limit, when it starts with six or more
letters or digits, and `syntax` at its first byte that is not a letter
or digit; both can be given, as two independent defects. `msg.id.mm`
and `msg.id.aa` follow the same pattern: `value` at the first byte past 2 letters or
digits; `value` where the first missing letter or digit was expected
when the part is all letters or digits but shorter than allowed, which
is the `'}'` for `msg.id.mm` and the end of the field for `msg.id.aa`;
and `syntax` at the first other byte, a second `'}'` included. An
earlier draft placed the `value` finding of a short part at its first
byte. **[proposed]** A `'{'` with nothing after it gives `syntax`
against `msg.id` at the end of the field, where its first byte was
expected. **[proposed]** An empty `msg.id.mm` is a part shorter than
allowed, and gives `value` at the `'}'`.

**[proposed]** `msg.text` (except in case 4 of section 2.1),
[`bln.text`](#bln.text), [`nws.text`](#nws.text) and, in an NTS line,
each [`nts.field`](#nts.field) are free-text fields for the no-archive
marker: a `'!x!'` inside one is a
[`cmt.noarchive`](02-fields.md#cmt.noarchive) token one level below it.

## 4. Acknowledgements and rejections

An acknowledgement is a message whose text is the letters `ack` followed
by the number being acknowledged; a rejection has `rej` in their place
(p. 94/72). Under the reply-ack scheme the acknowledgement copies the
whole identifier it acknowledges, `}` included (p. 95/73). Neither has an
identifier rule of its own: the token of byte 0 carries
[`msg.dti`](#msg.dti) (section 2.1, case 3).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.ack.kw"></a>`msg.ack.kw` | Keyword | `ack`, lower case, at offset 11. | Required | Fixed 3 bytes | p. 94/72 |
| <a id="msg.rej.kw"></a>`msg.rej.kw` | Keyword | `rej`, lower case, at offset 11. | Required | Fixed 3 bytes | p. 94/72 |
| <a id="msg.ack.num"></a>`msg.ack.num` | Number acknowledged or rejected | Either 1-5 letters or digits, or the reply-ack identifier copied: 2 letters or digits, `'}'`, and 0 or 2 letters or digits. Nothing follows. | Required | End of information field | p. 94/72, p. 95/73 |

**[proposed]** The text has the shape of an acknowledgement or rejection
exactly when it is `ack` or `rej` followed by a `msg.ack.num` and nothing
else. Otherwise it is message text (section 3). The tokenizer reports
`ambiguous` against `msg.text` at offset 11 when the text does not have
that shape but has it once its first three letters are folded to lower
case, such as `ACK12`, which the other reading of
[amb.msg.ack](#amb.msg.ack) accepts as an acknowledgement or rejection.
Other text that starts with `ack` or `rej`, such as `ack` followed by 6
or more letters or digits, a valid `msg.ack.num` followed by a message
identifier (UAP 5.32), `ack` starting a sentence, or `ACKNOWLEDGED`,
is message text and gives no finding from this rule. When the packet
already gives a `syntax` or `value` finding for those bytes, such as a
trailing CR, that finding alone is given. Reading:
[amb.msg.ack](#amb.msg.ack).

## 5. Group and special addressees

APRS12c names addressees that are not stations. None of them changes the
tokens; they are listed so that the tokenizer's reports can be grouped.

- `ALL`, `QST` and `CQ` are read by every station and are never
  acknowledged (p. 95/73, p. 96/74). Other message groups are a receiver's
  local list, not a wire form.
- `EMAIL` is shown as an example of how an e-mail message "could be
  constructed", with the address at the start of the text; APRS itself is
  said not to deliver e-mail (p. 93/71). The text is not tokenized
  further. See [err.msg.email-example](#err.msg.email-example).
- The addressee of a telemetry definition message is the station whose
  telemetry it describes (p. 90/70).
- A directed query is addressed to the station being queried (p. 103/79).
  A message answering `?APRSM` is an ordinary message, numbered and
  acknowledged as usual
  ([amb.qry.response](09-other.md#amb.qry.response)).

**[proposed]** These addressees are tokenized as `msg.addr` with no
further finding.

## 6. Bulletins and announcements

A bulletin addressee is `BLN` followed by a 1-byte identifier and padding
(p. 96/74, p. 97/75, p. 136/112). Bulletins and announcements are not
acknowledged.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="bln.addr"></a>`bln.addr` | Bulletin addressee | Offsets 1-9: `BLN` and the parts below, padded with `SP` to 9 bytes. Depth-1 tokens below. Reading: [amb.bln.forms](#amb.bln.forms). | Required | Fixed 9 bytes | p. 96/74, p. 97/75 |
| <a id="bln.kw"></a>`bln.kw` | Prefix | `BLN` at offsets 1-3. | Required | Fixed 3 bytes | p. 96/74 |
| <a id="bln.num"></a>`bln.num` | Bulletin identifier | One digit at offset 4, followed by 5 `SP` (general bulletin) or by a group name (group bulletin). | One of `bln.num`, `bln.ann` | Fixed 1 byte | p. 96/74, p. 97/75 |
| <a id="bln.ann"></a>`bln.ann` | Announcement identifier | One upper-case letter `'A'`-`'Z'` at offset 4, followed by 5 `SP`. | One of `bln.num`, `bln.ann` | Fixed 1 byte | p. 96/74 |
| <a id="bln.group"></a>`bln.group` | Group name | 1-5 bytes from offset 5, letters, digits and `'-'`, then `SP` to offset 9. Other bytes as for `msg.addr.name`. | Group bulletin only | First `SP`, or offset 9 | p. 97/75 |
| [`msg.addr.pad`](#msg.addr.pad) | Padding | `SP` bytes to offset 9. | Required when the name part is shorter | Offset 9 | p. 96/74 |
| [`msg.sep`](#msg.sep) | Separator | `':'` at offset 10. | Required | Fixed 1 byte | p. 96/74 |
| <a id="bln.text"></a>`bln.text` | Bulletin text | From offset 11. Text bytes, `'{'` included. More than 67 bytes gives `value`. May be empty. | Required, 0 bytes allowed | End of information field, or `bln.ref` | p. 96/74, p. 97/75 |
| <a id="bln.ref"></a>`bln.ref` | Reference identifier | `'{'` followed by 1-5 letters or digits at the very end of the field. The tokenizer reports `ambiguous` at the `'{'` when the bytes are also valid bulletin text: the text from offset 11, `bln.ref` included, is at most 67 bytes. Reading: [amb.bln.ref](#amb.bln.ref). | Optional | End of information field | p. 97/75 |

**[proposed]** An addressee starting with `BLN` that fits none of the
three forms (for example a letter followed by a group name, a lower-case
letter or a punctuation byte at offset 4) is still read as a bulletin
addressee. The tokenizer reports `unstated` against `bln.addr` and
tokenizes the bytes after `BLN` as one depth-1 `bln.group`. It also
gives the `ambiguous` finding of [amb.bln.forms](#amb.bln.forms), at
offset 4, where the packet read as a message would give no `syntax` or
`value` finding of its own.

**[proposed]** The `unstated` finding against `bln.addr` is at offset 4,
the first byte that fits none of the three forms. The `bln.group` token
of such an addressee runs from offset 4 to the first `SP`, and the rest
is `msg.addr.pad`; an addressee with `SP` at offset 4 has no `bln.group`
token. Its bytes are checked as for `msg.addr.name`.

Where the byte at offset 4 already gives `syntax` against `bln.group`,
such as a `':'`, the `unstated` finding against `bln.addr` is not given:
it would report the same defect again
([README section 3](README.md#3-tokenizer-model), Precedence). An
earlier draft gave both.

APRS12c also describes how a receiver files, replaces, clears and
announces bulletins, keyed by sender and identifier, and how often
bulletins and announcements are sent (p. 96/74, p. 99/77). These are
station behaviour across packets and are not tokenized. The same holds
for repeated acknowledgements and their spacing (p. 94/72).

## 7. National Weather Service bulletins

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nws.addr"></a>`nws.addr` | NWS addressee | Offsets 1-9: `NWS-` and a severity word, padded with `SP` to 9 bytes. Depth-1 tokens below. Reading: [amb.nws.addressee](#amb.nws.addressee). | Required | Fixed 9 bytes | p. 97/75 |
| <a id="nws.kw"></a>`nws.kw` | Prefix | `NWS-` at offsets 1-4. | Required | Fixed 4 bytes | p. 97/75 |
| <a id="nws.level"></a>`nws.level` | Severity word | 1-5 letters or digits from offset 5. The document gives `ADVIS`, `WARN` and `WATCH` and leaves the list open; any word is accepted. Other bytes as for `msg.addr.name`. | Required | First `SP`, or offset 9 | p. 97/75 |
| [`msg.addr.pad`](#msg.addr.pad) | Padding | `SP` bytes to offset 9. | Required when the word is shorter than 5 bytes | Offset 9 | p. 97/75 |
| [`msg.sep`](#msg.sep) | Separator | `':'` at offset 10. | Required | Fixed 1 byte | p. 97/75 |
| <a id="nws.text"></a>`nws.text` | Bulletin text | From offset 11. Text bytes, no length limit. Its inner structure is defined outside APRS12c and is not tokenized. | Required | End of information field, or `nws.ref` | p. 97/75 |
| <a id="nws.ref"></a>`nws.ref` | Reference identifier | `'{'` followed by 1-5 letters or digits at the very end of the field; not to be acknowledged. The tokenizer reports `ambiguous` at the `'{'`: the bytes are also valid bulletin text, which has no length limit. Reading: [amb.bln.ref](#amb.bln.ref). | Optional | End of information field | p. 97/75 |

**[proposed]** "Other bytes as for `msg.addr.name`" in the `nws.level`
row means bytes outside its own set of letters and digits: they get the
findings that `msg.addr.name` gives a byte outside its set. A `'-'`
therefore gives `unstated` in `nws.level`, although `msg.addr.name`
allows it. An empty `nws.text`, also one followed by `nws.ref`, gives
`syntax` against `nws.text` at offset 11; under precedence, an
`nws.ref` that starts there then gets no `ambiguous` finding.

## 8. NTS radiograms

An NTS radiogram line is a message whose text starts with a 3-byte
format identifier: `'N'`, a type byte and `'\'` (p. 98/76). The line is an
ordinary message in every other respect, including its message
identifier. The NTS tokens are depth-1 tokens inside `msg.text`.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nts.prefix"></a>`nts.prefix` | Format identifier | `'N'`, then one of `'#'`, `'A'`, `'P'`, `'1'`-`'6'`, `'S'`, `'R'`, then `'\'`, at the start of `msg.text`. Reading: [amb.nts.prefix](#amb.nts.prefix). | Required for this form | Fixed 3 bytes | p. 98/76 |
| <a id="nts.field"></a>`nts.field` | Field | Text bytes other than `'\'`. | See below | `'\'` or end of `msg.text` | p. 98/76 |
| <a id="nts.sep"></a>`nts.sep` | Field separator | `'\'`. | Between fields | Fixed 1 byte | p. 98/76 |

Number of `nts.field` tokens after the prefix, by type byte (p. 98/76):

| Type | Line | Fields |
|---|---|---|
| `#` | Message number, precedence, handling, originator, check, place, time, date | 8 |
| `A` | Address lines | 1 to 4 |
| `P` | Telephone number | 1 |
| `1`-`6` | One line of message text each | 1 |
| `S` | Signature | 1 |
| `R` | Received from, date and time, sent to, date and time | 4 |

**[proposed]** A field count outside its row gives `syntax` against
`nts.prefix`. The 67-byte limit of `msg.text` applies to the whole line,
prefix included (p. 98/76). That the `#`, `A`, `S` and `R` lines are
required, and that there are at most six text lines, are rules about a
set of packets; the tokenizer reads one packet at a time and does not
check them.

**[proposed]** The count is of `nts.field` tokens, as the table says.
An empty field, between two `nts.sep` bytes or between one and the
prefix or the end of `msg.text`, has no token and does not count: a
`'#'` line with an empty field, such as a missing time, has 7 fields
and gives `syntax`, and so does a type `1` line with nothing after the
prefix.

A byte that is not a text byte inside an `nts.field` gets one `syntax`
finding against `nts.field`, the most specific rule that holds it, and
none against `msg.text`, which encloses it
([README section 3](README.md#3-tokenizer-model), Placing a finding);
the `nts.field` row states the same byte set less the separator. An
earlier draft gave the finding against `msg.text` instead.

## 9. Obsolete bulletin form

Some stations sent bulletins and announcements without the `':'` data
type identifier; this form is obsolete, and such packets are to be read
as status reports (p. 98/76). APRS12c gives no layout for it.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="bln.obsolete"></a>`bln.obsolete` | Obsolete bulletin | An information field that starts with `BLN` followed by a digit or an upper-case letter, handed here by [01-frame.md](01-frame.md#7-data-type-identifier) because `'B'` is not an assigned identifier. There is no identifier byte: one token covering the whole field at depth 0, with nothing tokenized inside it; the tokenizer reports `obsolete`. Reading: [amb.bln.obsolete](#amb.bln.obsolete). | - | End of information field | p. 98/76 |

**[proposed]** Since nothing is tokenized inside `bln.obsolete`, it is
not a free-text field: a `'!x!'` in it is no token and gets the
`ambiguous` finding of
[amb.cmt.noarchive](02-fields.md#amb.cmt.noarchive).

## 10. Ambiguities

<a id="amb.msg.addressee"></a>
### amb.msg.addressee

- **Open.** The addressee is 9 bytes padded with spaces (p. 93/71). Its
  byte set, its case and the handling of a short addressee without
  padding are not stated. UAP 2.5.2 says the rules are relaxed for
  Internet services: more than 6 characters and letters in the SSID.
- **Readings.** (a) Exactly 9 bytes, separator at offset 10; name of
  letters, digits and `'-'`. (b) Any 9 bytes. An earlier draft listed a
  further reading, in which the addressee ends at the first `':'` after
  offset 1 with trailing spaces trimmed. It was dropped because the
  document makes the addressee a fixed 9-byte field (p. 93/71).
  javAPRSlib and aprs-parser-rs delimit the addressee at the first
  `':'`, and pdn-aprs tolerates an earlier `':'` (see Decoders;
  [README section 3](README.md#3-tokenizer-model)).
- **Taken.** **[proposed]** (a), with other printable bytes in the name
  reported as `unstated` rather than `syntax`. Lower case is accepted.
  An interior space, a `':'` inside the 9 bytes, or a separator before
  offset 10 gives `syntax`, and that finding alone is given, although
  (b) may accept the bytes
  ([README section 3](README.md#3-tokenizer-model), precedence). Where
  (a) accepts the bytes, (b) divides them the same way; no `ambiguous`
  finding.
- **Decoders.**

  | Decoder | What it does | Where |
  |---|---|---|
  | FAP | 9 bytes of letters, digits, `'_'`, `'-'` and `SP`, then `':'`; trailing spaces trimmed. | `_message_parse`, FAP.pm:1358, 1362 |
  | Dire Wolf | Any 9 bytes, then `':'` at offset 10, else invalid; trailing spaces trimmed; warns about a space between call and SSID. | `aprs_message`, decode_aprs.c:1814, 1859 |
  | aprslib | 9 bytes of letters, digits, `'_'`, `'-'` and `SP`, then `':'`. | `parse_message`, message.py:57 |
  | Xastir | Requires `':'` at offset 10; takes the 9 bytes before it, trailing spaces removed. | `decode_message`, db.c:13640 |
  | aprsc | Takes the recipient up to the first `SP` or `':'`; requires `':'` at offset 10 to parse the message, which it does only for messages to the server itself. | `preparse_aprs_message`, parse_aprs.c:1134; `parse_aprs_message`, parse_aprs.c:1374, 1390 |
  | javAPRSlib | The addressee runs to the first `':'` after offset 2, trimmed and upper-cased; the text starts at offset 11 regardless. | `MessagePacket`, MessagePacket.java:67-79 |
  | aprs-parser-rs | Bytes up to the first `':'` must number exactly 9. | `AprsMessage::decode`, message.rs:27 |
  | pdn-aprs | `':'` at offset 10, or an earlier `':'` as a tolerated defect; printable ASCII; a space or `':'` inside is a tolerated defect. | `decode`, message.rs:21 |

  ebarkie/aprs does not parse messages.
- **Corpus.** Share of `':'` packets whose second `':'` is not at offset
  10; addressees with lower case, interior spaces, or bytes other than
  letters, digits and `'-'`.

<a id="amb.msg.text"></a>
### amb.msg.text

- **Open.** Message text is printable ASCII or UTF-8 with `'{'` excluded
  (p. 93/71), up to 67 characters, but the same page says longer text is
  seen and should be handled. Not stated: what
  "printable" means for UTF-8, whether the 67 counts bytes or characters,
  and control bytes such as a trailing CR (UAP 5.13). Older forms of the
  protocol also excluded `'|'` and `'~'` (APRS 1.0.1, PDF 81); APRS12c
  does not.
- **Readings.** (a) Text bytes as defined in section 1, limit in bytes,
  over-length a `value` finding. (b) Limit in characters. (c) No limit.
- **Taken.** **[proposed]** (a). The diagram's byte row gives 0-67
  (p. 93/71). That the limit counts bytes, not characters, follows
  [README section 3](README.md#3-tokenizer-model) (Length limits).
  `'|'` and `'~'` are text bytes. Text over 67 bytes gives `value`, as
  a field longer than its stated length (Kinds by situation), and that
  finding alone is given, also when (b) or (c) would accept it
  (Precedence). Where (a) accepts the text, so do (b) and (c); no
  `ambiguous` finding. The page also tells receivers to handle longer
  text, which the Kinds bullet for a departure from a sending rule that
  receivers are told to accept would report as `syntax`; which bullet
  applies is open (section 12).
- **Decoders.** FAP accepts bytes 0x20-0x7E and 0x80-0xFE, at least one
  (FAP.pm:1358); an empty text fails. Dire Wolf's message structure
  leaves room for the rest of a 256-byte field, with a comment that the
  67 limit is relaxed (decode_aprs.c:1789). aprslib takes the rest of
  the field (message.py:57) and trims spaces
  (message.py:108). Xastir's header comment lists `'|'`, `'~'` and `'{'`
  as excluded (db.c:13597). pdn-aprs decodes the text as UTF-8 under its
  own options (`decode`, message.rs:101-106).
- **Corpus.** Length distribution of message text in bytes and in UTF-8
  characters; counts of control bytes, of `'|'` and `'~'`, and of
  invalid UTF-8 in message text.

<a id="amb.msg.id"></a>
### amb.msg.id

- **Open.** The identifier is `'{'` and up to 5 letters or digits
  "appended" to the text (p. 93/71). It is not said that nothing may
  follow it, nor what to do with more than 5 bytes, other bytes, a
  trailing CR or space, or more than one `'{'`.
- **Readings.** (a) The first `'{'` ends the text, since text excludes
  `'{'`; the identifier runs to the end. An earlier draft listed two
  further readings: the last `'{'` starts the identifier, and only a
  valid identifier at the very end counts, any other `'{'` being text.
  Both were dropped because they differ from (a) only where they leave a
  `'{'` in the text, which the document excludes (p. 93/71). Xastir,
  aprsc and javAPRSlib take the last `'{'`, aprslib and pdn-aprs only a
  valid identifier at the end (see Decoders;
  [README section 3](README.md#3-tokenizer-model)).
- **Taken.** **[proposed]** (a). With more than one `'{'` the number
  holds a `'{'` and fails. A number that is too long or holds other
  bytes gives `value` or `syntax`. No `ambiguous` finding.
- **Decoders.**

  | Decoder | What it does | Where |
  |---|---|---|
  | FAP | Text without `'{'`, then `'{'`, 1-5 letters or digits, an optional reply-ack part, optional trailing white space; if that does not match, the whole text is the message with no identifier. | `_message_parse`, FAP.pm:1377 |
  | Dire Wolf | First `'{'`; the rest is the number; a CR is removed with a warning; a length outside 1-5 is reported. | `aprs_message`, decode_aprs.c:2039-2053 |
  | aprslib | Only a valid identifier at the end of the field. | `parse_message`, message.py:113, 124 |
  | Xastir | Last `'{'`; takes up to 5 bytes after it. | `decode_message`, db.c:13673-13678 |
  | aprsc | Last `'{'`; the rest is the identifier. | `parse_aprs_message`, parse_aprs.c:1400 |
  | javAPRSlib | Last `'{'`. | `MessagePacket`, MessagePacket.java:73 |
  | aprs-parser-rs | First `'{'`; the rest is the identifier, no check. | `AprsMessage::decode`, message.rs:34 |
  | pdn-aprs | Last `'{'`, accepted only if a valid identifier follows; otherwise the `'{'` stays in the text as a tolerated defect. | `split_message_id`, message.rs:153; `brace_ok`, message.rs:111 |

- **Corpus.** Distribution of the length and byte classes after the
  first and the last `'{'`; share of identifiers ending in CR or `SP`;
  share of packets with more than one `'{'`.

<a id="amb.msg.replyack"></a>
### amb.msg.replyack

- **Open.** The reply-ack form is `{MM}AA`, or `{MM}` with no pending
  acknowledgement (p. 95/73). The lengths of `MM` and `AA` are not
  stated; the text says the scheme sits inside the "5 digit line number".
  `'}'` is not a letter or digit, so the form breaks the rule of p. 93/71
  ([err.msg.replyack-alnum](#err.msg.replyack-alnum)).
- **Readings.** (a) `MM` and `AA` each exactly 2 bytes, `AA` possibly
  empty; this fills the 5 bytes exactly. (b) Each 1-5 bytes, split at the
  first `'}'`. (c) Any lengths with a total of at most 5.
- **Taken.** **[proposed]** (a). Other lengths give `value` against
  `msg.id.mm` or `msg.id.aa`, and that finding alone is given, although
  (b) or (c) may accept the bytes
  ([README section 3](README.md#3-tokenizer-model), precedence). Where
  (a) accepts the bytes, (b) and (c) divide them the same way. No
  `ambiguous` finding.
- **Decoders.** aprslib accepts 2 + 2 or 2 + nothing (message.py:92,
  113). Dire Wolf recognises the form only when `'}'` is the third byte of
  the number (decode_aprs.c:2062). FAP accepts 1-5 and 1-5 or nothing
  (FAP.pm:1377). pdn-aprs accepts 1-5 and 0 or 1-5 (`split_message_id`,
  message.rs:153). Xastir finds `'}'` anywhere in the first 5 bytes after
  `'{'` (db.c:13697), and also a `'}'` in text without an identifier
  (db.c:13740).
- **Corpus.** Length histogram of `MM` and `AA` in identifiers holding
  `'}'`; how many such identifiers exceed 5 bytes.

<a id="amb.msg.ack"></a>
### amb.msg.ack

- **Open.** An acknowledgement's text is "just" `ack` and the number
  (p. 94/72). Not stated: upper-case `ACK`, an acknowledgement that
  carries its own message identifier (UAP 5.32), a trailing CR (UAP
  5.13), and text that starts with `ack` but is a sentence.
- **Readings.** (a) Exactly `ack` or `rej` and a valid number, to the end
  of the field. (b) As (a), case folded. An earlier draft listed a
  further reading that takes any text starting with `ack` or `rej` as an
  acknowledgement or rejection. It was dropped because the document
  gives the text as just the keyword followed by the number, which is
  at most 5 letters or digits (p. 93/71, p. 94/72); Dire Wolf, Xastir,
  aprsc and javAPRSlib read it so (see Decoders;
  [README section 3](README.md#3-tokenizer-model)).
- **Taken.** **[proposed]** (a), lower case only. Any other text that
  starts with `ack` or `rej`, in any case, is read as message text:
  among them `ack` with a valid number and then `{` and an identifier,
  read as a message whose text is the acknowledgement, and `ack` with 6
  or more letters or digits. Reading (b) would take such text as an
  acknowledgement or rejection where only the case differs, so that
  case is visible and gives `ambiguous` (section 4).
- **In the bytes.** Under the test of
  [README section 3](README.md#3-tokenizer-model) a reading counts only
  where it accepts the text. Reading (b) only folds the case and keeps
  the shape of (a), so it counts only for text whose folded form has
  that shape: `ACK12` gives the finding, `ACKNOWLEDGED` does not. The
  finding is `ambiguous` against `msg.text` at offset 11. A trailing CR
  makes the text a message with a control byte: `syntax`, and that
  finding alone is given
  ([README section 3](README.md#3-tokenizer-model), precedence). Text
  that has the shape of (a) is an acknowledgement or rejection under
  both readings and gives no finding. Lower-case `ack` or `rej` followed
  by anything else, an over-long number or an identifier of its own
  included, gives no finding: the reading that accepted it was dropped.
  An earlier draft gave the finding for any text starting with the
  letters in any case; a later one gave it for any text starting with
  lower-case `ack` or `rej`, under the dropped reading.
- **Decoders.**

  | Decoder | What it does | Where |
  |---|---|---|
  | FAP | `ack` or `rej`, then 1-5 letters, digits or `'}'`, then optional white space. | `_message_parse`, FAP.pm:1365, 1372 |
  | Dire Wolf | Any text starting with `ack` or `rej`, case-folded; upper case is reported as an error; the rest is the number; a CR is removed; a `'}'` third byte cuts the number. | `aprs_message`, decode_aprs.c:1970-1992, 1996-2018 |
  | aprslib | `ack`/`rej` with 2 + `'}'` + optional 2, or with 1-5 letters or digits, to the end. | `parse_message`, message.py:92, 101 |
  | Xastir | Text starting with `ack` (lower case) and longer than 3 bytes; up to 5 bytes after it are the number. Its comments list `ack23{` and `ack2Q}3d` as reply-ack forms. | `decode_message`, db.c:13789-13803 |
  | aprsc | Text starting with `ack`, when no identifier was found. | `parse_aprs_message`, parse_aprs.c:1411 |
  | javAPRSlib | Text starting with `ack` or `rej`, case-folded. | `MessagePacket`, MessagePacket.java:82-91 |
  | aprs-parser-rs | Does not distinguish acknowledgements. | - |
  | pdn-aprs | `ack`/`rej`, 1-5 letters or digits, optional `'}'` and reply-ack; an identifier of its own is a tolerated defect. | `ack_id`, message.rs:130 |

- **Corpus.** Counts of `':'` texts that are `ack`/`rej` plus 1-5
  letters or digits; with upper case; with trailing CR or `SP`; with a
  `'{'` identifier after the number.

<a id="amb.msg.order"></a>
### amb.msg.order

- **Open.** APRS12c describes each kind of `':'` packet separately and
  gives no order of tests. A bulletin's text may look like an
  acknowledgement; a message's text may start with `'?'` or a telemetry
  keyword.
- **Readings.** (a) Addressee first, then the shape of the text, as in
  section 2.1. (b) Text first.
- **Taken.** **[proposed]** (a). The addressee is fixed by position, and
  bulletins are never acknowledged (p. 94/72), so an acknowledgement
  shape in a bulletin is bulletin text.
- **In the bytes.** **[proposed]** Visible, under the test of
  [README section 3](README.md#3-tokenizer-model), for a bulletin or an
  NWS bulletin whose text reading (b) would classify by its shape: text
  that has the exact shape of an acknowledgement or rejection
  (section 4), that starts with an upper-case telemetry keyword and fits
  [07 section 4](07-telemetry.md#4-telemetry-definition-messages), or
  that matches a directed query
  ([09-other.md section 4.1](09-other.md#41-directed-queries)), where
  the packet read as that kind, its addressee as `msg.addr` and its text
  under the `msg.text` length limit included, would give no `syntax` or
  `value` finding of its own. That text stays `bln.text` or `nws.text`,
  with an `ambiguous` finding at offset 11, unless this reading already
  gives a
  `syntax` or `value` finding on those bytes. Other text falls through
  the text tests of (b) to the addressee, so both readings make it a
  bulletin and it gets no finding here; a trailing `'{'` is covered by
  [amb.bln.ref](#amb.bln.ref). A packet whose addressee starts with
  neither `BLN` nor `NWS-` is classified by its text under both
  readings. An earlier draft called the question not visible.
- **Decoders.** Dire Wolf tests `BLN`, `NWS`, other weather prefixes,
  telemetry keywords, `'?'`, then `ack`/`rej` (decode_aprs.c:1870-1996).
  pdn-aprs tests `ack`/`rej` first, then bulletins, telemetry and queries
  (message.rs:66-104). Xastir extracts the identifier, then tests
  `ack`, `rej`, `TACTICAL`, `BLN`, then messages to itself, then NWS
  (db.c:13789-14306). aprslib tests bulletins first (message.py:27-43).
- **Corpus.** Counts of bulletin and NWS packets whose text has an
  acknowledgement shape or starts with `'?'`.

<a id="amb.bln.forms"></a>
### amb.bln.forms

- **Open.** A general bulletin is `BLN`, a digit and 5 spaces; a group
  bulletin is `BLN`, a digit and a group name of up to 5 bytes padded to
  5 (p. 96/74, p. 97/75). `BLN`, a digit and 5 spaces is therefore also a
  group bulletin with an empty name. `BLN` with a letter and a name is not
  defined. The group name's byte set and case are not stated.
- **Readings.** (a) An empty name is a general bulletin; a group name is
  1-5 bytes. (b) Any `BLN` prefix is a bulletin and the rest is free.
  (c) Only the three defined shapes are bulletins; others are messages.
- **Taken.** **[proposed]** (a), with other `BLN` shapes read as bulletins
  and given `unstated` (section 6).
- **In the bytes.** **[proposed]** Under the test of
  [README section 3](README.md#3-tokenizer-model): a `BLN` addressee that
  fits none of the three shapes is a bulletin here and a message under
  reading (c). Where the packet, read as a message by section 2.1 from
  case 3 on, would give no `syntax` or `value` finding of its own, it
  gets an
  `ambiguous` finding at offset 4, beside the `unstated` finding of
  section 6. That a general bulletin is also a group bulletin with an
  empty name, and that reading (b) would not divide the name part into
  tokens, is carried by every bulletin of that shape and gives no
  finding. An earlier draft called the question not visible.
- **Decoders.** Dire Wolf treats any `BLN` addressee as a bulletin,
  naming the three shapes and an "other" (decode_aprs.c:1870-1893).
  Xastir treats any `BLN` addressee as a bulletin (db.c:13982). aprslib
  reads `BLN`, a digit and 5 letters, digits, `'_'`, `'-'` or spaces,
  case-folded, as a bulletin (group when the 5 are not blank), and `BLN`,
  an upper-case letter and 5 such bytes as an announcement
  (message.py:27, 43). pdn-aprs accepts the three shapes, tolerates a
  letter with a group name as a defect, and reads other `BLN` addressees
  as messages (`bulletin_kind`, message.rs:171). FAP, javAPRSlib and
  aprs-parser-rs do not distinguish bulletins.
- **Corpus.** Counts of `BLN` addressees by shape: digit + spaces, letter
  + spaces, digit + name, letter + name, lower case, other.

<a id="amb.bln.ref"></a>
### amb.bln.ref

- **Open.** The exclusion of `'{'` is stated for message text only
  (p. 93/71); bulletin text may hold "any" printable character
  (p. 96/74). The NWS example ends with `{` and 5 letters and digits,
  described as a message identifier kept "for reference" and not to be
  acknowledged (p. 97/75).
- **Readings.** (a) `'{'` starts an identifier in every `':'` packet.
  (b) `'{'` is text in bulletins. (c) A trailing `'{'` and 1-5 letters or
  digits is a reference identifier in bulletins and NWS bulletins.
- **Taken.** **[proposed]** (c). It is tokenized as `bln.ref` in
  bulletins and as `nws.ref` in NWS bulletins, following the example.
  Visible in the bytes: reading (b) takes the same bytes as text. Both
  give an `ambiguous` finding at the `'{'`, under the condition below.
  An earlier draft gave none in NWS bulletins, as decided by the
  document's own example; that was dropped because the example does not
  stop reading (b) from dividing the bytes differently.
- **In the bytes.** Under the tests of
  [README section 3](README.md#3-tokenizer-model), reading (b) counts
  only where it accepts the text with the `'{'` and its letters or
  digits in it. NWS text has no length limit, so every `nws.ref` gives
  the finding. Bulletin text has the 67-byte limit, which this reading
  applies to `bln.text` as tokenized, without `bln.ref` (Length
  limits); a `bln.ref` gives the finding only where the text from
  offset 11, `bln.ref` included, is at most 67 bytes, and otherwise reading (b) would give `value`. Where `bln.text`
  alone is over the limit, that `value` finding alone is given
  (precedence). Reading (a) divides a trailing reference the same way as
  (c), and fails on a `'{'` elsewhere, which (c) leaves as text; it adds
  no finding.
- **Decoders.** Xastir extracts an identifier after the last `'{'` before
  testing the addressee, so for bulletins too (db.c:13673). pdn-aprs
  splits a valid trailing identifier off bulletin text
  (message.rs:83). Dire Wolf keeps bulletin and NWS text whole
  (decode_aprs.c:1891, 1913). aprslib's bulletin pattern keeps it in the
  text (message.py:27). FAP splits it for every message (FAP.pm:1377).
- **Corpus.** Share of `BLN` and `NWS-` packets containing `'{'`, and
  the shape of what follows it.

<a id="amb.nws.addressee"></a>
### amb.nws.addressee

- **Open.** The NWS addressee is `NWS-` and a severity word; the words are
  examples and the list is open (p. 97/75). The text format is deferred
  to an external page (p. 97/75). Other prefixes used for weather alerts
  are not mentioned.
- **Readings.** (a) `NWS-` and any 1-5 letters or digits. (b) Only the
  listed words. (c) Also `NWS_`, `SKY`, `CWA` and `BOM` prefixes.
- **Taken.** **[proposed]** (a). Other prefixes are ordinary message
  addressees; `NWS_` gives `unstated` through its `'_'` byte.
- **In the bytes.** **[proposed]** Visible, under the test of
  [README section 3](README.md#3-tokenizer-model), in two cases. An
  `NWS-` addressee whose word is not `ADVIS`, `WARN` or `WATCH` is an NWS
  bulletin here and a message under reading (b); where the packet, read
  as a message by section 2.1 from case 3 on, would give no `syntax` or
  `value` finding of its own, it gets an `ambiguous` finding at offset
  5. An
  addressee starting with `NWS_`, `SKY`, `CWA` or `BOM` is a message
  here and an NWS bulletin under reading (c), which accepts any text
  bytes; it gets an `ambiguous` finding at offset 1, unless the packet
  already gives a `syntax` or `value` finding on those bytes. An earlier
  draft called the question not visible.
- **Decoders.** Dire Wolf accepts `NWS-`, `NWS_`, and `SKY`, `CWA`, `BOM`
  prefixes, and reports `NWS` without `'-'` or `'_'` (decode_aprs.c:1901,
  1916). Xastir accepts `NWS-`, `NWS_`, `BOM-`, `BOM_` (db.c:14306) and
  `SKY` (db.c:14354). aprsc flags `NWS-`, `NWS_` and `SKY`
  (parse_aprs.c:1100-1104). pdn-aprs accepts `NWS-` and `NWS_`
  (`bulletin_kind`, message.rs:172). FAP and aprslib do not distinguish
  them.
- **Corpus.** Counts of addressees starting `NWS`, `SKY`, `CWA`, `BOM`, by
  the byte after the prefix.

<a id="amb.nts.prefix"></a>
### amb.nts.prefix

- **Open.** An NTS line is recognised only by its 3-byte prefix
  (p. 98/76). An ordinary message that happens to start with, say,
  `N1\` reads the same. Whether address lines may stop early is not
  stated.
- **Readings.** (a) Every message text starting with an NTS prefix is an
  NTS line. (b) Only when the field count also fits.
- **Taken.** **[proposed]** (a); a field count that does not fit gives
  `syntax`, and that finding alone is given, although (b) would accept
  the bytes as an ordinary message
  ([README section 3](README.md#3-tokenizer-model), precedence). Address
  lines may number 1 to 4. Where the count fits, (a) and (b) agree; no
  `ambiguous` finding.
- **Decoders.** None of the decoders read parses NTS lines; a search of
  the files read found no NTS handling in FAP, Dire Wolf, aprslib,
  Xastir, aprsc, javAPRSlib, aprs-parser-rs or pdn-aprs.
- **Corpus.** Count of message texts starting with an NTS prefix, and
  their field counts.

<a id="amb.bln.obsolete"></a>
### amb.bln.obsolete

- **Open.** The obsolete bulletin form is described only as bulletins
  sent without the `':'` identifier, to be read now as status
  (p. 98/76). Its layout is not given, and `'B'` is a data type
  identifier marked "do not use" (p. 31/17).
- **Readings.** (a) Recognise a field starting `BLN` and a digit or
  upper-case letter as the obsolete form. (b) Do not recognise it; leave
  it to the handling of unknown identifiers in 01.
- **Taken.** (a), as one token with an `obsolete` finding at its first
  byte, as [README section 3](README.md#3-tokenizer-model) (Obsolete
  and nested forms) requires of an obsolete form the document
  describes: it is recognised when its defining bytes, `BLN` and the
  bulletin identifier byte, match, and its inside is read only as far
  as the document describes it. APRS12c gives it no layout (p. 98/76),
  so nothing inside is tokenized. Not visible as an alternative:
  decided silently, no finding beyond `obsolete`. Under the test of
  README section 3, reading (b) would give the `syntax` finding of a
  "do not use" identifier at byte 0
  ([01-frame.md](01-frame.md#7-data-type-identifier)), so it does not
  count.
- **Decoders.** A search of the files read found no branch for an
  information field starting with `BLN` in any of the decoders; FAP,
  Dire Wolf, aprslib, Xastir and pdn-aprs dispatch on the first byte, and
  none of their dispatch tables has a case for `'B'` (FAP.pm:2579-2760;
  decode_aprs.c:336-500; parsing/__init__.py:158-210; db.c:14979-15410;
  decode.rs:27-55). FAP's last fallback looks for a `'!'` position within
  the first 40 bytes of an unrecognised field (FAP.pm:2747-2750). Xastir
  stores any field it has not decoded, a leading `BLN` included, as the
  station's status text (db.c:15431-15433), which is what p. 98/76 asks
  for.
- **Corpus.** Count of information fields starting with `BLN` and a
  digit or upper-case letter.

## 11. Errata

<a id="err.msg.email-example"></a>
### err.msg.email-example

The e-mail example on p. 93/71 has `EMAIL` and 5 filler spaces before the
separator, 10 bytes where the addressee is 9; the text layer of the PDF
has the same 5 spaces. The reading follows the 9-byte rule; the example
gives `syntax` at `msg.sep`.

Origin: introduced by the 12b/12c compilation. APRS 1.0.1 has `EMAIL`
and 4 space marks, a correct 9-byte addressee (1.0.1 PDF 81, text
layer). 12b already has 5 (12b PDF 95).

<a id="err.bln.group-example"></a>
### err.bln.group-example

The group bulletin example on p. 97/75 has `BLN4WX` followed by 5
spaces, 11 bytes, where the rule allows 3 spaces after a 6-byte prefix.
The reading follows the rule; the example gives `syntax` at `msg.sep`.

Origin: introduced by the 12b/12c compilation. APRS 1.0.1 has `BLN4WX`
and 3 space marks (1.0.1 PDF 84, text layer). 12b already has the longer
padding (12b PDF 99).

<a id="err.bln.padding-marks"></a>
### err.bln.padding-marks

The chapter 14 diagrams of the general bulletin and the announcement
show four space marks in a column counted as 5 bytes (p. 96/74);
Appendix 1 shows five (p. 136/112). The rendered chapter examples show
a gap and four marks; the extracted text gives a plain space and four
marks, 5 in all. The reading follows the byte count of 5.

Origin: introduced by the 12b/12c compilation. APRS 1.0.1 shows five
marks in both diagrams and both examples (1.0.1 PDF 83, text layer). 12b
already has four (12b PDF 98).

<a id="err.msg.replyack-alnum"></a>
### err.msg.replyack-alnum

The message number is letters and digits only (p. 93/71, p. 94/72); the
reply-ack form puts `'}'` into it, and its acknowledgement copies the `'}'`
(p. 95/73). The reading follows p. 95/73 for the reply-ack form and keeps
the letters-and-digits rule for the plain form.

Origin: a merge of APRS 1.0.1 text with a later addendum. The
letters-and-digits rule and the acknowledgement diagrams are 1.0.1 text
(1.0.1 PDF 81, 82), which has no reply-ack form. The reply-ack text is
the December 1999 reply-ack note, listed in Appendix 7 among the merged
APRS 1.1 addendum items (p. 155/131); the 1.0.1 rule was not changed to
admit `'}'`. 12b has the same pairing (12b PDF 95, 97).

## 12. Open items

- Whether a C1 control (U+0080 to U+009F) counts as a printable UTF-8
  character ([amb.msg.text](#amb.msg.text)).
- Whether message or bulletin text over 67 bytes, which p. 93/71,
  p. 96/74 and p. 97/75 tell receivers to handle, is a field over its stated length (`value`) or a
  departure from a sending rule that receivers are told to accept
  (`syntax`): both are bullets of Kinds by situation in
  [README section 3](README.md#3-tokenizer-model)
  ([amb.msg.text](#amb.msg.text)).
- The corpus questions of section 10.
