# Values of message and bulletin fields

| | |
|---|---|
| Status | Draft. Not frozen. A paragraph, value rule or catalogue row of this file is **[proposed]** if it has no other label. An **[agreed]** item is a decision of the author. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of these formats give values:

- messages, acknowledgements and rejections
  ([08 sections 3 and 4](08-message.md#3-messages));
- bulletins and announcements
  ([08 section 6](08-message.md#6-bulletins-and-announcements));
- NWS bulletins
  ([08 section 7](08-message.md#7-national-weather-service-bulletins)).

The tokens come from [08](08-message.md) and [02](02-fields.md). This
file adds no token and changes no finding. The rule prefix is `val`.

These parts are outside this file:

- the fields of an NTS line
  ([08 section 8](08-message.md#8-nts-radiograms)). The line is a
  message, and its text has a value;
- the obsolete bulletin format
  ([08 section 9](08-message.md#9-obsolete-bulletin-format));
- directed queries ([09 section 4.1](09-other.md#41-directed-queries));
- telemetry definition messages. Their values are in
  [13-values-telemetry](13-values-telemetry.md#5-definition-messages).

## 2. Conventions

The conventions of [10-values section 2](10-values.md#2-conventions) apply
to this file. These are the terms, the value tables, the findings that
concern a value, and the effects.

An addressee, a text and a message number are byte strings. The decoder
does not decode them as text and does not change their case. A message
number is not an integer: `003` and `3` are different numbers.

## 3. Messages

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.msg.addr"></a>`val.msg.addr` | Addressee | [`msg.addr.name`](08-message.md#msg.addr.name) | All bytes of the token. | Byte string, 1 to 9 bytes | p. 93/71 |
| <a id="val.msg.text"></a>`val.msg.text` | Message text | [`msg.text`](08-message.md#msg.text) | All bytes of the token. | Byte string | p. 93/71 |
| <a id="val.msg.id"></a>`val.msg.id` | Message number | [`msg.id`](08-message.md#msg.id), or [`msg.id.mm`](08-message.md#msg.id.mm) in the reply-ack format | All bytes of the token. | Byte string, 1 to 5 bytes | p. 93/71, p. 95/73 |
| <a id="val.msg.replyack"></a>`val.msg.replyack` | Reply-ack capability | [`msg.id.close`](08-message.md#msg.id.close) | Present: the sender accepts a reply-ack. | Flag | p. 95/73 |
| <a id="val.msg.ackid"></a>`val.msg.ackid` | Number that the message acknowledges | [`msg.id.aa`](08-message.md#msg.id.aa) | All bytes of the token. | Byte string | p. 95/73 |

The padding of the addressee, the separator `msg.sep` and the marker
`msg.id.open` hold no value.

A message can have no text token, because the text is empty. The decoder
then gives no text.

In the reply-ack format, the number of the message is the `MM` field. The
`AA` field is the number of a message that the sender received from the
addressee (p. 95/73). If `AA` is empty, the packet has no `msg.id.aa`
token, and the message acknowledges nothing.

The bytes `!x!` in a text are a
[`cmt.noarchive`](02-fields.md#cmt.noarchive) token. The value rule
[val.cmt.noarchive](10-values.md#val.cmt.noarchive) gives the flag. The
bytes are also bytes of the text.

An NTS line is a message. `val.msg.text` gives its text, with the prefix
and the separators.

## 4. Acknowledgements and rejections

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.msg.kind"></a>`val.msg.kind` | Kind | [`msg.ack.kw`](08-message.md#msg.ack.kw), [`msg.rej.kw`](08-message.md#msg.rej.kw) | `msg.ack.kw`: acknowledgement. `msg.rej.kw`: rejection. Neither token: message. | Code | p. 94/72 |
| <a id="val.msg.acknum"></a>`val.msg.acknum` | Number that the packet acknowledges or rejects | [`msg.ack.num`](08-message.md#msg.ack.num) | The bytes of the token before its first `'}'`. Without a `'}'`: all bytes. | Byte string, 1 to 5 bytes | p. 94/72, p. 95/73 |

An acknowledgement of a reply-ack message has a copy of the number
`MM}AA`. Only `MM` identifies the message that it acknowledges
(p. 95/73, step 7). The decoder does not give the `AA` of the copy.

## 5. Bulletins

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.bln.kind"></a>`val.bln.kind` | Kind | [`bln.num`](08-message.md#bln.num), [`bln.ann`](08-message.md#bln.ann), [`nws.dti`](08-message.md#nws.dti) | `bln.num`: bulletin. `bln.ann`: announcement. `nws.dti`: NWS bulletin. | Code | p. 96/74, p. 97/75 |
| <a id="val.bln.id"></a>`val.bln.id` | Bulletin or announcement identifier | `bln.num` or `bln.ann` | The byte of the token. | Byte string, 1 byte: a digit or a letter `A` to `Z` | p. 96/74 |
| <a id="val.bln.group"></a>`val.bln.group` | Group name | [`bln.group`](08-message.md#bln.group) | All bytes of the token. | Byte string, 1 to 5 bytes | p. 97/75 |
| <a id="val.nws.level"></a>`val.nws.level` | Severity word | [`nws.level`](08-message.md#nws.level) | All bytes of the token. | Byte string, 1 to 5 bytes | p. 97/75 |
| <a id="val.bln.text"></a>`val.bln.text` | Bulletin text | [`bln.text`](08-message.md#bln.text), [`nws.text`](08-message.md#nws.text) | All bytes of the token. | Byte string | p. 96/74, p. 97/75 |
| <a id="val.nws.ref"></a>`val.nws.ref` | Reference identifier | [`nws.ref`](08-message.md#nws.ref) | The bytes of the token after its `'{'`. | Byte string, 1 to 5 bytes | p. 97/75 |

A bulletin has no addressee value. Its addressee field holds the kind,
the identifier and the group.

The text of an NWS bulletin does not contain the bytes of `nws.ref`.

## 6. Effect of findings

This table gives the effect of each finding that concerns a value of
sections 3 to 5. A token that has no row has only findings with the
effect `kept`.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `msg.addr`, `msg.addr.name` | `syntax` | Addressee | `none` |
| `msg.addr.name` | `unstated` (a byte other than a letter, a digit or `'-'`) | Addressee | **[agreed]** `kept` |
| `msg.sep` | `syntax` | Addressee, kind, and the values of a bulletin addressee | **[agreed]** `computable` |
| `msg.sep` | `syntax` | The number of an acknowledgement or a rejection | `computable` |
| `msg.sep` | `syntax` | Text, message number, acknowledged number, reference identifier, no-archive flag | **[agreed]** `none` |
| `msg.text`, `bln.text`, `nws.text` | `syntax` (a byte that is not a text byte) | Text | `kept`: the value is a byte string |
| `msg.text`, `bln.text` | `value` (the text is too long) | Text | `kept` |
| `msg.id` | `syntax` | Message number | `none` |
| `msg.id` | `value` (more than 5 bytes) | Message number | `computable`: all bytes of the token |
| `msg.id.mm` | `syntax` (an empty field) | Message number | `none` |
| `msg.id.mm` | `unstated` (a length other than 2) | Message number | `computable`: all bytes of the token |
| `msg.id.aa` | `syntax` (a second `'}'`) | Acknowledged number | `none` |
| `msg.id.aa` | `unstated` (a length other than 0 or 2) | Acknowledged number | `computable`: all bytes of the token |
| `msg.id.mm`, `msg.id.close`, `msg.id.aa` | `value` (the number is longer than 5 bytes) | Message number, acknowledged number | `computable` |
| `msg.ack.num` | `unstated` | Acknowledged number | `computable` |
| `bln.addr` | `syntax` | Kind, identifier, group | `none` |
| `bln.group` | `unstated` | Group name | `computable`: all bytes of the token |
| `nws.addr`, `nws.level` | `syntax` | Severity word | `none` |
| `nws.level` | `unstated` (a word that is not listed) | Severity word | `kept`: the list is open |
| `nws.ref` | `ambiguous` ([amb.bln.ref](08-message.md#amb.bln.ref)) | Reference identifier, text | `kept`: the reference is the narrowest interpretation |
| `nws.ref` | `syntax` | Reference identifier | `none` |
| `nws.ref` | `value` | Reference identifier | `computable` |

**[agreed]** An addressee name with a byte other than a letter, a digit
or `'-'` is a value in both modes. APRS12c states no set of bytes for the
name, and the bytes of the token are certain.

**[agreed]** If the byte at the place of `msg.sep` is not `':'`, the
decoder does not search for a `':'` at another place. The addressee field
still has its fixed place. Thus the addressee is `computable`. The start
of the text is not certain. In the capture, most such packets have an
addressee field of 10 bytes, and their text starts one byte later. Thus
the text and the numbers after it are `none`.

An acknowledgement, a rejection and a telemetry definition message are
different: the tokenizer finds their keyword at the fixed place of the
text. Their values after the keyword are `computable`
([13-values-telemetry section 6](13-values-telemetry.md#6-effect-of-findings)).

If the token of a required value is missing, the value is `none`. The
finding of the field that the packet ends in is the reason.

## 7. Catalogue

This file adds no row.

## 8. Reviewed exceptions

None.

## 9. Open items

- The effect of `syntax` on `msg.sep` for the number of an
  acknowledgement or a rejection.
- An addressee field of 10 bytes is common in the capture. It is a
  candidate entry of the divergence catalogue (RFC Appendix E).
- The effect of `unstated` on the lengths of `MM` and `AA`. APRS12c
  states no length for them. This file gives `computable`.
- The effect of `value` on a message number of more than 5 bytes.
- Whether the addressees `ALL`, `QST`, `CQ` and `EMAIL` have a value of
  their own ([08 section 5](08-message.md#5-group-and-special-addressees)).
  This file gives them as an addressee.
- Values of the fields of an NTS line.
- Values of the obsolete bulletin format.
