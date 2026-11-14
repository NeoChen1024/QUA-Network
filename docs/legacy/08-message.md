# Messages, bulletins and announcements

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that the general rules of the [README](README.md#31-general-rules) do not settle is marked **[open]**; a reviewed exception is marked **[agreed]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions and tokenizer model: [README](README.md). |

## 1. Scope

Packets with the identifier `:`: messages, acknowledgements and
rejections, bulletins and announcements, NWS bulletins, NTS lines, and
the obsolete bulletin without an identifier. Telemetry definition
messages and directed queries are recognised here and read by
[07-telemetry.md](07-telemetry.md) and [09-other.md](09-other.md).
Offsets count from the identifier, offset 0. Rule prefixes: `msg`,
`bln`, `nws`, `nts`.

**Text bytes** are `SP` to `~` and well-formed multi-byte UTF-8
(p. 93/71, p. 96/74; [amb.msg.text](#amb.msg.text)). Any other byte
gives `syntax`, once per field, at the first such byte, on the most
specific rule that holds it.

## 2. Common frame

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.dti"></a>`msg.dti` | Identifier of a message | `:` at offset 0 of a message, acknowledgement or rejection, NTS lines included. | one identifier rule | 1 byte | p. 31/17; p. 93/71 |
| <a id="bln.dti"></a>`bln.dti` | Identifier of a bulletin | `:` at offset 0 of a bulletin or announcement. | one identifier rule | 1 byte | p. 96/74 |
| <a id="nws.dti"></a>`nws.dti` | Identifier of an NWS bulletin | `:` at offset 0 of an NWS bulletin. | one identifier rule | 1 byte | p. 97/75 |
| <a id="msg.addr"></a>`msg.addr` | Addressee | Offsets 1 to 9: a name, then `SP` padding to 9 bytes. A field that ends inside the 9 bytes gives `syntax` at its end. Bulletin and NWS addressees are `bln.addr` and `nws.addr`. | yes | 9 bytes | p. 93/71 |
| <a id="msg.addr.name"></a>`msg.addr.name` | Name | Up to the last byte that is not `SP`. Letters, digits and `-`; the first other byte, an inner `SP` or `:` included, gives `unstated` ([amb.msg.addressee](#amb.msg.addressee)). Only `SP` gives `syntax` at offset 1. | yes | the padding or offset 10 | p. 93/71; p. 109/85 |
| <a id="msg.addr.pad"></a>`msg.addr.pad` | Padding | `SP` bytes. | when the name is shorter than 9 bytes | offset 10 | p. 93/71 |
| <a id="msg.sep"></a>`msg.sep` | Separator | `:` at offset 10. Another byte there, or the end of the field, gives `syntax`; no earlier `:` is looked for, and the text still starts at offset 11. | yes | 1 byte | p. 93/71 |

### 2.1 Kind of packet

The addressee decides first, since bulletins and NWS bulletins are
defined by it (p. 96/74, p. 97/75) and the other kinds are addressed to
a station (p. 90/70, p. 94/72, p. 103/79); case is significant:

1. `BLN` at offsets 1 to 3: a bulletin or announcement, section 6; an
   addressee of none of its three forms gives `syntax`
   ([amb.bln.forms](#amb.bln.forms)).
2. `NWS-`: an NWS bulletin, section 7.
3. The text is an acknowledgement or rejection, section 4.
4. The text starts with `PARM.`, `UNIT.`, `EQNS.` or `BITS.`: a
   telemetry definition message, read by
   [07 section 4](07-telemetry.md#4-telemetry-definition-messages)
   inside `msg.text` (section 3).
5. The text is a directed query of
   [09 section 4.1](09-other.md#41-directed-queries): `?`, a type of five
   upper-case letters or `PING?`, and an optional heard station
   ([amb.qry.dir](09-other.md#amb.qry.dir)), read there from offset 11;
   it is still message text for the 67-character limit of `msg.text`.
6. Otherwise a message, section 3.

Every text of cases 3 to 5 is also message text, an ambiguity that every
instance carries: the more specific kind is taken, with no finding
(README rule 4). The byte-0 token carries `bln.dti`, `nws.dti`,
`msg.dti` (cases 3 and 6), [`tlm.def.dti`](07-telemetry.md#tlm.def.dti)
or [`qry.dir.dti`](09-other.md#qry.dir.dti).

## 3. Messages

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.text"></a>`msg.text` | Message text | From offset 11; text bytes except `{`, which ends it. At most 67 characters: the 68th UTF-8 character gives `value` ([amb.msg.text](#amb.msg.text)). May be empty. | yes, 0 bytes allowed | first `{`, or end of field | p. 93/71 |
| <a id="msg.id.open"></a>`msg.id.open` | Identifier marker | `{`. | no | 1 byte | p. 93/71 |
| <a id="msg.id"></a>`msg.id` | Message number | 1 to 5 letters or digits, to the end of the field. A run of more than 5 gives `value` at its sixth byte; another byte, `SP` and CR included, gives `syntax`; nothing after `{` gives `syntax` at the end. | after `msg.id.open` | end of field | p. 93/71 |
| <a id="msg.id.mm"></a>`msg.id.mm` | Reply-ack own number | Letters or digits before `}`. Empty gives `syntax` at the `}`. A length other than 2 gives `unstated` ([amb.msg.replyack](#amb.msg.replyack)). | in the reply-ack form | `}` | p. 95/73 |
| <a id="msg.id.close"></a>`msg.id.close` | Reply-ack separator | `}`, the first after `{`; it selects the reply-ack form. | in the reply-ack form | 1 byte | p. 95/73 |
| <a id="msg.id.aa"></a>`msg.id.aa` | Reply-ack acknowledged number | Letters or digits, possibly none; a length other than 0 or 2 gives `unstated`. A second `}` gives `syntax`. | no | end of field | p. 95/73 |

The reply-ack form sits within the 5-byte number (p. 95/73): a run of
letters, digits and the `}` longer than 5 gives `value` at its sixth
byte, on the part that holds it. `msg.text` (outside case 4),
`bln.text`, `nws.text` and each `nts.field` are free text for
[`cmt.noarchive`](02-fields.md#cmt.noarchive) (p. 110/86).

## 4. Acknowledgements and rejections

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="msg.ack.kw"></a>`msg.ack.kw` | Keyword | `ack`, lower case, at offset 11. | yes | 3 bytes | p. 94/72 |
| <a id="msg.rej.kw"></a>`msg.rej.kw` | Keyword | `rej`, lower case, at offset 11. | yes | 3 bytes | p. 94/72 |
| <a id="msg.ack.num"></a>`msg.ack.num` | Number | 1 to 5 bytes: letters or digits, or a reply-ack number copied, `}` included; nothing follows. Reply-ack parts of a length other than 2, and 0 or 2, give `unstated`. | yes | end of field | p. 94/72; p. 95/73 |

A text that is not exactly a keyword and a number, such as `ACK12`, a
number of 6 bytes or a number followed by `{`, is message text with no
finding of its own ([amb.msg.ack](#amb.msg.ack), section 11).

## 5. Group and special addressees

`ALL`, `QST`, `CQ` (p. 96/74), `EMAIL` (p. 93/71), the station a
definition message describes (p. 90/70) and the station a directed
query asks (p. 103/79) are message addressees with no finding of their
own; only `BLN` and `NWS-` change the kind of packet.

## 6. Bulletins and announcements

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="bln.addr"></a>`bln.addr` | Bulletin addressee | Offsets 1 to 9: `bln.kw` and one of three forms, padded with `SP` to 9 bytes: a digit and 5 `SP` (general bulletin), an upper-case letter and 5 `SP` (announcement), a digit and a group name. Bytes of none of the three forms give `syntax` at the first byte at which every form fails ([amb.bln.forms](#amb.bln.forms)); a field that ends inside the 9 bytes gives `syntax` at its end. | yes | 9 bytes | p. 96/74; p. 97/75 |
| <a id="bln.kw"></a>`bln.kw` | Prefix | `BLN` at offsets 1 to 3. | yes | 3 bytes | p. 96/74 |
| <a id="bln.num"></a>`bln.num` | Bulletin identifier | A digit at offset 4. | one of `bln.num`, `bln.ann` | 1 byte | p. 96/74; p. 97/75 |
| <a id="bln.ann"></a>`bln.ann` | Announcement identifier | `A`–`Z` at offset 4, followed by 5 `SP`. | one of `bln.num`, `bln.ann` | 1 byte | p. 96/74 |
| <a id="bln.group"></a>`bln.group` | Group name | Up to 5 bytes from offset 5, then `SP`; bytes as for `msg.addr.name`. | group bulletin only | the padding or offset 10 | p. 97/75 |
| <a id="bln.text"></a>`bln.text` | Bulletin text | From offset 11; text bytes, `{` included. At most 67 characters, as for `msg.text`. May be empty. | yes, 0 bytes allowed | end of field | p. 96/74; p. 97/75 |

## 7. National Weather Service bulletins

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nws.addr"></a>`nws.addr` | NWS addressee | Offsets 1 to 9: `NWS-` and a severity word, padded with `SP`. A field that ends inside the 9 bytes gives `syntax` at its end. | yes | 9 bytes | p. 97/75 |
| <a id="nws.kw"></a>`nws.kw` | Prefix | `NWS-` at offsets 1 to 4. | yes | 4 bytes | p. 97/75 |
| <a id="nws.level"></a>`nws.level` | Severity word | Up to 5 bytes from offset 5. The words are an open list, "such as" `ADVIS`, `WARN`, `WATCH`: another word gives `unstated` at offset 5 ([amb.nws.addressee](#amb.nws.addressee)). Only `SP` gives `syntax`. | yes | the padding or offset 10 | p. 97/75 |
| <a id="nws.text"></a>`nws.text` | Bulletin text | From offset 11; text bytes, n of them, no length limit. Not tokenized further. | yes, 0 bytes allowed | end of field, or `nws.ref` | p. 97/75 |
| <a id="nws.ref"></a>`nws.ref` | Reference identifier | `{` and 1 to 5 letters or digits at the very end of the field. Gives `ambiguous` at the `{` ([amb.bln.ref](#amb.bln.ref)). | no | end of field | p. 97/75 |

## 8. NTS radiograms

An NTS line is a message whose text starts with `N`, a type byte and
`\` ([amb.nts.prefix](#amb.nts.prefix)), followed by `\`-separated
fields, as many as its type allows (p. 98/76). Its tokens lie one level
below `msg.text`, whose 67-character limit covers the whole line.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nts.prefix"></a>`nts.prefix` | Format identifier | `N`, one of `#`, `A`, `P`, `1`–`6`, `S`, `R`, then `\`, at the start of `msg.text` ([amb.nts.prefix](#amb.nts.prefix)). | for this form | 3 bytes | p. 98/76 |
| <a id="nts.field"></a>`nts.field` | Field | Text bytes other than `\`. An empty field gives `unstated` where it was expected. | see below | `\` or end of `msg.text` | p. 98/76 |
| <a id="nts.sep"></a>`nts.sep` | Separator | `\`. | between fields | 1 byte | p. 98/76 |

Fields by type: `#` 8; `A` 1 to 4; `P`, `1`–`6`, `S` 1; `R` 4. A
separator before a field past that number gives `syntax` on `nts.sep`;
fewer fields give `syntax` on `nts.field` at the end of `msg.text`.

## 9. Obsolete bulletin form

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="bln.obsolete"></a>`bln.obsolete` | Obsolete bulletin | A bulletin without its `:` identifier: one of the three addressees of `bln.addr` at offsets 0 to 8, `:` at offset 9, then bulletin text. Tried by [01-frame.md](01-frame.md#7-data-type-identifier) when byte 0 selects no format. One token over the field at depth 0, `obsolete`; the bulletin fields one level below ([amb.bln.obsolete](#amb.bln.obsolete)). | — | end of field | p. 98/76 |

## 10. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.msg.addressee"></a>amb.msg.addressee | p. 93/71; p. 109/85 | The addressee has a width and padding but no byte set; p. 109/85 says a message sender, whom the acknowledgement addresses, may be longer than a callsign, in lower case, or with a non-numeric SSID. | unstated | 2 | Letters, digits and `-`, either case: no finding. The first other byte of the name, an inner `SP` or `:` included, gives `unstated`. `bln` or `nws-` in another case is a message addressee, no finding. |
| <a id="amb.msg.text"></a>amb.msg.text | p. 93/71; p. 96/74; p. 97/75 | The limit is 67 bytes in the diagram and 67 characters, UTF-8 allowed, in the text. "Printable ASCII or UTF-8 characters" can also be read as any UTF-8 character, control bytes included. | ambiguous | 1 | `value` only past 67 characters, which every reading rejects. **[open]** By rule 1 a control byte would conform under the second reading; default: CR, LF, other C0 bytes and DEL give `syntax`, C1 characters no finding. |
| <a id="amb.msg.replyack"></a>amb.msg.replyack | p. 95/73 | `{MM}AA` sits within the 5-byte number, but the lengths of `MM` and `AA` are not given. | unstated | 2 | More than 5 bytes gives `value`; an empty `MM` `syntax`; `MM` other than 2 or `AA` other than 0 or 2 `unstated`. |
| <a id="amb.msg.ack"></a>amb.msg.ack | p. 93/71; p. 94/72 | Every acknowledgement or rejection is also message text. | ambiguous | 4 | Carried by every instance: the acknowledgement or rejection, no finding. A text that starts with `ack` or `rej` and does not match section 4 as a whole is message text, no finding ([section 11](#11-reviewed-exceptions)). Upper-case `ACK` is not the keyword: message text, no finding. |
| <a id="amb.bln.forms"></a>amb.bln.forms | p. 96/74; p. 97/75 | A `BLN` addressee of none of the three forms, such as `BLNAWX` or `BLN!`, may be a bulletin of a form not given or a message. | ambiguous | 1 | `BLN` at offsets 1 to 3 announces a bulletin addressee: a bulletin, with `syntax` on `bln.addr` at the first byte at which every form fails; reading the addressee as a message's does not make it conform. `bln` in another case is a message addressee ([amb.msg.addressee](#amb.msg.addressee)). |
| <a id="amb.bln.ref"></a>amb.bln.ref | p. 96/74; p. 97/75 | The NWS example ends in `{` and 5 letters and digits, called an identifier kept for reference; bulletin text may hold any printable byte, and no reference is named for other bulletins. | ambiguous | 4; 2 | In an NWS bulletin, `nws.ref`, the more specific, with `ambiguous` at the `{` unless its bytes give `syntax` or `value`. In a bulletin, text. |
| <a id="amb.nws.addressee"></a>amb.nws.addressee | p. 97/75 | The severity words are examples of an open list; other alert prefixes are not mentioned. | unstated | 2 | Another word gives `unstated` on `nws.level`. Other prefixes are message addressees. |
| <a id="amb.nts.prefix"></a>amb.nts.prefix | p. 98/76 | An NTS line is recognised only by its prefix; every NTS line is also message text. | ambiguous | 1, 4 | The prefix announces an NTS line: a text with it is an NTS line, with no finding for the message reading, which every instance carries. A field count outside its type's gives `syntax` (section 8); reading the text as a plain message does not make it conform. An empty field within the count gives `unstated`. |
| <a id="amb.bln.obsolete"></a>amb.bln.obsolete | p. 31/17; p. 98/76 | `B` is a "do not use" identifier, and p. 98/76 describes bulletins sent without `:` as an obsolete form. | conflict | 3; 1 | A field of that form is `bln.obsolete`, `obsolete`; another field starting `B` gets the `syntax` of "do not use". |
| <a id="err.msg.email-example"></a>err.msg.email-example | p. 93/71 | The e-mail example has `EMAIL` and 5 filler spaces, a 10-byte addressee. | conflict | 3 | A slip of the pen (one stray space): it allows nothing, and gives `syntax` at `msg.sep`. |
| <a id="err.bln.group-example"></a>err.bln.group-example | p. 97/75 | The group bulletin example has `BLN4WX` and 5 spaces, where the form gives 3. | conflict | 3 | A slip of the pen (two stray spaces): it allows nothing, and gives `syntax` at `msg.sep`. |
| <a id="err.bln.padding-marks"></a>err.bln.padding-marks | p. 96/74; p. 136/112 | The chapter diagrams draw four space marks in a column of 5 bytes; Appendix 1 draws five. | conflict | 3 | The four marks are a slip of the pen: the padding is 5 bytes. |
| <a id="err.msg.replyack-alnum"></a>err.msg.replyack-alnum | p. 93/71; p. 94/72; p. 95/73 | The message number is letters and digits; the reply-ack form and its acknowledgement put `}` into it. | conflict | 3 | Both accepted: one `}` selects the reply-ack form, with no finding. |

## 11. Reviewed exceptions

**[agreed]** Keywords at the start of a message text (p. 93/71,
p. 94/72, p. 103/79). The `ack` or `rej` that starts an acknowledgement
or rejection and the `'?'` that starts a directed query do not announce
a field in the sense of
[README rule 1](README.md#31-general-rules). A text that matches the
whole shape of an acknowledgement or rejection (section 4) or of a
directed query ([09 section 4.1](09-other.md#41-directed-queries)) is
that kind; any other text that starts with them, such as `ack` and a
sentence or `'?'` and a question, is message text, with no finding for
the kind it does not match. As the author decided, the reason is that
these strings mix too easily with ordinary text messages.

## 12. Open items

- [amb.msg.text](#amb.msg.text) is open.
