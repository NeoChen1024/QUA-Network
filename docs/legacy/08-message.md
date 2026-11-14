# Messages, bulletins and announcements

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]** ([README section 2](README.md#2-conventions)). A reviewed exception is marked **[agreed]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers packets with the identifier `:`:

- messages, acknowledgements and rejections;
- bulletins and announcements;
- NWS bulletins;
- NTS lines;
- the obsolete bulletin without an identifier.

This file also recognises telemetry definition messages and directed
queries. [07-telemetry.md](07-telemetry.md) and
[09-other.md](09-other.md) read them. Offsets count from the identifier,
which is offset 0. Rule prefixes: `msg`, `bln`, `nws`, `nts`.

**Text bytes** are `SP` to `~` and well-formed multi-byte UTF-8
(p. 93/71, p. 96/74; [amb.msg.text](#amb.msg.text)). Any other byte
gives `syntax`. The tokenizer gives one such finding for each field, at
the first such byte. It puts the finding on the rule of the deepest token
that contains the byte.

## 2. Common frame

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.dti"></a>`msg.dti` | Identifier of a message | `:` at offset 0 of a message, an acknowledgement or a rejection. This includes NTS lines. | one identifier rule | 1 byte | p. 31/17; p. 93/71 |
| <a id="bln.dti"></a>`bln.dti` | Identifier of a bulletin | `:` at offset 0 of a bulletin or an announcement. | one identifier rule | 1 byte | p. 96/74 |
| <a id="nws.dti"></a>`nws.dti` | Identifier of an NWS bulletin | `:` at offset 0 of an NWS bulletin. | one identifier rule | 1 byte | p. 97/75 |
| <a id="msg.addr"></a>`msg.addr` | Addressee | Offsets 1 to 9: a name, then `SP` padding to 9 bytes. If the field ends inside the 9 bytes, `syntax` at its end. A bulletin addressee is `bln.addr`. An NWS addressee is `nws.addr`. | yes | 9 bytes | p. 93/71 |
| <a id="msg.addr.name"></a>`msg.addr.name` | Name | The name is letters, digits and `-`, up to the last byte that is not `SP`. The first other byte gives `unstated` ([amb.msg.addressee](#amb.msg.addressee)). This includes an `SP` or a `:` inside the name. An addressee of only `SP` gives `syntax` at offset 1. | yes | the padding or offset 10 | p. 93/71; p. 109/85 |
| <a id="msg.addr.pad"></a>`msg.addr.pad` | Padding | `SP` bytes. | if the name is shorter than 9 bytes | offset 10 | p. 93/71 |
| <a id="msg.sep"></a>`msg.sep` | Separator | `:` at offset 10. Another byte at offset 10, or the end of the field, gives `syntax`. The tokenizer does not look for an earlier `:`. The text then also starts at offset 11. | yes | 1 byte | p. 93/71 |

### 2.1 Kind of packet

The tokenizer checks the addressee first. The addressee identifies
bulletins and NWS bulletins (p. 96/74, p. 97/75). The other kinds have a
station as addressee (p. 90/70, p. 94/72, p. 103/79). Case is
significant. The tokenizer selects the kind in this order:

1. If offsets 1 to 3 are `BLN`, the packet is a bulletin or an
   announcement (section 6). An addressee that matches none of its three
   formats gives `syntax` ([amb.bln.forms](#amb.bln.forms)).
2. If the addressee starts with `NWS-`, the packet is an NWS bulletin
   (section 7).
3. If the text is an acknowledgement or a rejection, the packet is that
   kind (section 4).
4. If the text starts with `PARM.`, `UNIT.`, `EQNS.` or `BITS.`, the
   packet is a telemetry definition message.
   [07 section 4](07-telemetry.md#4-telemetry-definition-messages) reads
   it inside `msg.text` (section 3).
5. If the text is a directed query of
   [09 section 4.1](09-other.md#41-directed-queries), the packet is that
   kind. The query is `?`, then a type of five upper-case letters or
   `PING?`, then an optional heard station
   ([amb.qry.dir](09-other.md#amb.qry.dir)). 09 reads it from offset 11.
   For the 67-character limit of `msg.text`, it is still message text.
6. If none of these applies, the packet is a message (section 3).

Every text of cases 3 to 5 is also message text. Every packet of these
kinds has the same ambiguity. Thus the tokenizer uses the kind with the
stricter format and gives no finding (README rule 4). The token of
byte 0 has one of these rule IDs: `bln.dti`, `nws.dti`, `msg.dti` (cases
3 and 6), [`tlm.def.dti`](07-telemetry.md#tlm.def.dti) or
[`qry.dir.dti`](09-other.md#qry.dir.dti).

## 3. Messages

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.text"></a>`msg.text` | Message text | From offset 11. Text bytes other than `{`. A `{` ends the field. A maximum of 67 characters: the 68th UTF-8 character gives `value` ([amb.msg.text](#amb.msg.text)). Can be empty. | yes, 0 bytes permitted | first `{`, or end of field | p. 93/71 |
| <a id="msg.id.open"></a>`msg.id.open` | Identifier marker | `{`. | no | 1 byte | p. 93/71 |
| <a id="msg.id"></a>`msg.id` | Message number | 1 to 5 letters or digits, to the end of the field. More than 5 letters or digits in sequence give `value` at the sixth byte. Another byte gives `syntax`, also `SP` and CR. If no byte follows `{`, `syntax` at the end. | after `msg.id.open` | end of field | p. 93/71 |
| <a id="msg.id.mm"></a>`msg.id.mm` | Reply-ack own number | Letters or digits before `}`. An empty field gives `syntax` at the `}`. A length other than 2 gives `unstated` ([amb.msg.replyack](#amb.msg.replyack)). | in the reply-ack format | `}` | p. 95/73 |
| <a id="msg.id.close"></a>`msg.id.close` | Reply-ack separator | `}`, the first `}` after `{`. It selects the reply-ack format. | in the reply-ack format | 1 byte | p. 95/73 |
| <a id="msg.id.aa"></a>`msg.id.aa` | Reply-ack acknowledged number | Zero or more letters or digits. A length other than 0 or 2 gives `unstated`. A second `}` gives `syntax`. | no | end of field | p. 95/73 |

The reply-ack format is inside the 5-byte number (p. 95/73). If a
sequence of letters, digits and the `}` is longer than 5 bytes, it gives
`value` at its sixth byte. The tokenizer puts this finding on the field
that contains that byte.

For [`cmt.noarchive`](02-fields.md#cmt.noarchive), these fields are text
(p. 110/86): `msg.text` (not in case 4), `bln.text`, `nws.text` and each
`nts.field`.

## 4. Acknowledgements and rejections

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.ack.kw"></a>`msg.ack.kw` | Keyword | `ack`, in lower case, at offset 11. | yes | 3 bytes | p. 94/72 |
| <a id="msg.rej.kw"></a>`msg.rej.kw` | Keyword | `rej`, in lower case, at offset 11. | yes | 3 bytes | p. 94/72 |
| <a id="msg.ack.num"></a>`msg.ack.num` | Number | 1 to 5 bytes: letters or digits, or a copy of a reply-ack number, `}` included. No byte follows. In a reply-ack number, an `MM` field with a length other than 2 gives `unstated`. An `AA` field with a length other than 0 or 2 also gives `unstated`. | yes | end of field | p. 94/72; p. 95/73 |

If a text is not exactly a keyword and a number, it is message text. It
gives no finding of its own. Examples are `ACK12`, a number of 6 bytes,
and a number followed by `{` ([amb.msg.ack](#amb.msg.ack), section 11).

## 5. Group and special addressees

These addressees are message addressees, with no finding of their own:

- `ALL`, `QST`, `CQ` (p. 96/74);
- `EMAIL` (p. 93/71);
- the station that a definition message describes (p. 90/70);
- the station that a directed query asks (p. 103/79).

Only `BLN` and `NWS-` change the kind of packet.

## 6. Bulletins and announcements

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="bln.addr"></a>`bln.addr` | Bulletin addressee | Offsets 1 to 9: `bln.kw` and one of three formats, with `SP` padding to 9 bytes. The formats are: a digit and 5 `SP` (general bulletin); an upper-case letter and 5 `SP` (announcement); a digit and a group name. If the bytes match none of the three formats, `syntax` at the first byte where every format fails ([amb.bln.forms](#amb.bln.forms)). If the field ends inside the 9 bytes, `syntax` at its end. | yes | 9 bytes | p. 96/74; p. 97/75 |
| <a id="bln.kw"></a>`bln.kw` | Prefix | `BLN` at offsets 1 to 3. | yes | 3 bytes | p. 96/74 |
| <a id="bln.num"></a>`bln.num` | Bulletin identifier | A digit at offset 4. | one of `bln.num`, `bln.ann` | 1 byte | p. 96/74; p. 97/75 |
| <a id="bln.ann"></a>`bln.ann` | Announcement identifier | `A`–`Z` at offset 4, then 5 `SP`. | one of `bln.num`, `bln.ann` | 1 byte | p. 96/74 |
| <a id="bln.group"></a>`bln.group` | Group name | Up to 5 bytes from offset 5, then `SP`. The bytes are as for `msg.addr.name`. | group bulletin only | the padding or offset 10 | p. 97/75 |
| <a id="bln.text"></a>`bln.text` | Bulletin text | From offset 11. Text bytes, `{` included. A maximum of 67 characters, as for `msg.text`. Can be empty. | yes, 0 bytes permitted | end of field | p. 96/74; p. 97/75 |

## 7. National Weather Service bulletins

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nws.addr"></a>`nws.addr` | NWS addressee | Offsets 1 to 9: `NWS-` and a severity word, with `SP` padding. If the field ends inside the 9 bytes, `syntax` at its end. | yes | 9 bytes | p. 97/75 |
| <a id="nws.kw"></a>`nws.kw` | Prefix | `NWS-` at offsets 1 to 4. | yes | 4 bytes | p. 97/75 |
| <a id="nws.level"></a>`nws.level` | Severity word | Up to 5 bytes from offset 5. The words are an open list, "such as" `ADVIS`, `WARN`, `WATCH`. Another word gives `unstated` at offset 5 ([amb.nws.addressee](#amb.nws.addressee)). If these bytes are only `SP`, they give `syntax`. | yes | the padding or offset 10 | p. 97/75 |
| <a id="nws.text"></a>`nws.text` | Bulletin text | From offset 11. n text bytes, with no length limit. The tokenizer looks only for `cmt.noarchive` inside it. | yes, 0 bytes permitted | end of field, or `nws.ref` | p. 97/75 |
| <a id="nws.ref"></a>`nws.ref` | Reference identifier | `{` and 1 to 5 letters or digits, at the end of the field. Gives `ambiguous` at the `{` ([amb.bln.ref](#amb.bln.ref)). | no | end of field | p. 97/75 |

## 8. NTS radiograms

An NTS line is a message whose text starts with `N`, a type byte and `\`
([amb.nts.prefix](#amb.nts.prefix)). Fields separated by `\` follow. The
number of fields is the number that its type permits (p. 98/76). The
tokens of the NTS line are one level below `msg.text`. The 67-character
limit of `msg.text` applies to the whole line.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nts.prefix"></a>`nts.prefix` | Format identifier | `N`, one of `#`, `A`, `P`, `1`–`6`, `S`, `R`, then `\`, at the start of `msg.text` ([amb.nts.prefix](#amb.nts.prefix)). | for this format | 3 bytes | p. 98/76 |
| <a id="nts.field"></a>`nts.field` | Field | Text bytes other than `\`. An empty field gives `unstated` at the place where it was expected. | see below | `\` or end of `msg.text` | p. 98/76 |
| <a id="nts.sep"></a>`nts.sep` | Separator | `\`. | between fields | 1 byte | p. 98/76 |

Number of fields for each type: `#` 8; `A` 1 to 4; `P`, `1`–`6`, `S` 1;
`R` 4. A separator before a field after that number gives `syntax` on
`nts.sep`. Fewer fields give `syntax` on `nts.field` at the end of
`msg.text`.

## 9. Obsolete bulletin format

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="bln.obsolete"></a>`bln.obsolete` | Obsolete bulletin | A bulletin without its `:` identifier. One of the three addressees of `bln.addr` is at offsets 0 to 8. `:` is at offset 9. Bulletin text follows. [01-frame.md](01-frame.md#7-data-type-identifier) tries this format if byte 0 selects no format. One token over the field at depth 0, with `obsolete`. The bulletin fields are one level below ([amb.bln.obsolete](#amb.bln.obsolete)). | — | end of field | p. 98/76 |

## 10. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.msg.addressee"></a>amb.msg.addressee | p. 93/71; p. 109/85 | APRS12c specifies a width and padding for the addressee, but no byte set. APRS12c says that a message sender can be longer than a callsign, in lower case, or with a non-numeric SSID (p. 109/85). The acknowledgement has the message sender as addressee. | unstated | 2 | Letters, digits and `-`, in upper or lower case: no finding. The first other byte of the name gives `unstated`. This includes an `SP` or a `:` inside the name. `bln` or `nws-` in another case is a message addressee, with no finding. |
| <a id="amb.msg.text"></a>amb.msg.text | p. 93/71; p. 96/74; p. 97/75 | The diagram specifies a limit of 67 bytes. The description in APRS12c specifies 67 characters and permits UTF-8. "Printable ASCII or UTF-8 characters" has a second interpretation: any UTF-8 character, control bytes included. | ambiguous | 1; none | `value` only after 67 characters, because every interpretation rejects that (rule 1). Working choice: CR, LF, other C0 bytes and DEL give `syntax`. C1 characters give no finding. |
| <a id="amb.msg.replyack"></a>amb.msg.replyack | p. 95/73 | `{MM}AA` is inside the 5-byte number. APRS12c does not specify the lengths of `MM` and `AA`. | unstated | 2 | More than 5 bytes give `value`. An empty `MM` gives `syntax`. `MM` other than 2, or `AA` other than 0 or 2, gives `unstated`. |
| <a id="amb.msg.ack"></a>amb.msg.ack | p. 93/71; p. 94/72 | Every acknowledgement or rejection is also message text. | ambiguous | 4 | Every packet of this kind has the same ambiguity. The tokenizer uses the acknowledgement or rejection, with no finding. A text can start with `ack` or `rej` and not match all of section 4. Such a text is message text, with no finding ([section 11](#11-reviewed-exceptions)). Upper-case `ACK` is not the keyword: message text, with no finding. |
| <a id="amb.bln.forms"></a>amb.bln.forms | p. 96/74; p. 97/75 | A `BLN` addressee that matches none of the three formats, for example `BLNAWX` or `BLN!`, has two interpretations. It can be a bulletin of a format that APRS12c does not specify, or a message. | ambiguous | 1 | `BLN` at offsets 1 to 3 is a marker that starts a bulletin addressee. Thus the packet is a bulletin, with `syntax` on `bln.addr` at the first byte where every format fails. An interpretation as a message addressee does not prevent this finding. `bln` in another case is a message addressee ([amb.msg.addressee](#amb.msg.addressee)). |
| <a id="amb.bln.ref"></a>amb.bln.ref | p. 96/74; p. 97/75 | The NWS example ends with `{` and 5 letters and digits. APRS12c calls them an identifier for reference. Bulletin text can contain any printable byte. APRS12c names no reference for other bulletins. | ambiguous | 4; 2 | In an NWS bulletin: `nws.ref`, the stricter format. If its bytes give no `syntax` or `value`, `ambiguous` at the `{`. In a bulletin: text. |
| <a id="amb.nws.addressee"></a>amb.nws.addressee | p. 97/75 | The severity words are examples of an open list. APRS12c does not mention other alert prefixes. | unstated | 2 | Another word gives `unstated` on `nws.level`. Other prefixes are message addressees. |
| <a id="amb.nts.prefix"></a>amb.nts.prefix | p. 98/76 | Only the prefix identifies an NTS line. Every NTS line is also message text. | ambiguous | 1, 4 | The prefix is a marker that starts an NTS line. A text with the prefix is an NTS line. Every NTS line has the same ambiguity, so the tokenizer gives no finding for it. If the number of fields is not a number that section 8 permits for the type, the tokenizer gives `syntax`. An interpretation as an ordinary message does not prevent this finding. An empty field gives `unstated` if its position is within the number that the type permits. |
| <a id="amb.bln.obsolete"></a>amb.bln.obsolete | p. 31/17; p. 98/76 | `B` is a "do not use" identifier. APRS12c describes bulletins without `:` as an obsolete format (p. 98/76). | conflict | 3; 1 | A field of that format is `bln.obsolete`, with `obsolete`. Another field that starts with `B` gets the `syntax` finding of "do not use". |
| <a id="err.msg.email-example"></a>err.msg.email-example | p. 93/71 | The e-mail example has `EMAIL` and 5 spaces of padding. This addressee has 10 bytes. | conflict | 3 | A typing error (one extra space). It permits nothing. It gives `syntax` at `msg.sep`. |
| <a id="err.bln.group-example"></a>err.bln.group-example | p. 97/75 | The group bulletin example has `BLN4WX` and 5 spaces. The format specifies 3. | conflict | 3 | A typing error (two extra spaces). It permits nothing. It gives `syntax` at `msg.sep`. |
| <a id="err.bln.padding-marks"></a>err.bln.padding-marks | p. 96/74; p. 136/112 | The diagrams of the chapter show four space marks in a column of 5 bytes. Appendix 1 shows five. | conflict | 3 | The four marks are a typing error. The padding is 5 bytes. |
| <a id="err.msg.replyack-alnum"></a>err.msg.replyack-alnum | p. 93/71; p. 94/72; p. 95/73 | The message number contains letters and digits. The reply-ack format and its acknowledgement put `}` into it. | conflict | 3 | The tokenizer accepts both. One `}` selects the reply-ack format, with no finding. |

## 11. Reviewed exceptions

**[agreed]** Keywords at the start of a message text (p. 93/71,
p. 94/72, p. 103/79). These keywords are not markers that start a field
in the sense of [README rule 1](README.md#31-general-rules):

- the `ack` or `rej` that starts an acknowledgement or a rejection;
- the `'?'` that starts a directed query.

If a text matches the full format of an acknowledgement or a rejection
(section 4), it is that kind. If a text matches the full format of a
directed query ([09 section 4.1](09-other.md#41-directed-queries)), it is
that kind. Any other text that starts with these keywords is message
text, for example `ack` and a sentence, or `'?'` and a question. The
tokenizer gives no finding for the kind that the text does not match.
The author decided this exception, for this reason: these strings and
ordinary text messages are too easy to confuse.

## 12. Open items

None.
