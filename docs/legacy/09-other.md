# Status, capabilities, queries and other formats

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. |
| Reference | `APRS12c.pdf` chapters 15, 16, 18, 19 and 20, in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers the information fields that [01-frame.md](01-frame.md)
passes on for these identifiers:

- `>` (status);
- `<` (station capabilities);
- `?` (general query);
- `{` (user-defined);
- `,` (invalid or test data).

It also covers directed queries, which [08-message.md](08-message.md)
passes on from a message text. It also covers the frequency specification
of chapter 18 at the start of a comment or of status text. The tokenizer
makes no tokens for net and meeting codes, node naming conventions,
frequencies in messages and DX cluster spots.

## 2. Status reports

A status report is `'>'`, then a timestamp, a locator with a symbol, or
neither, then text (p. 104/80 to p. 106/82).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="stat.dti"></a>`stat.dti` | Identifier | `'>'` | Required | 1 byte | p. 31/17, p. 104/80 |
| <a id="stat.time"></a>`stat.time` | Timestamp | DHM zulu only: six digits and `'z'`, a [`time.dhm`](02-fields.md#time.dhm) token. Six digits and `'/'` or `'h'` are status text. | Optional | 7 bytes | p. 104/80 |
| <a id="stat.grid"></a>`stat.grid` | Locator with symbol | Directly after `'>'`, never with a timestamp: [`grid.loc`](03-position.md#grid.loc) of 6 or 4 bytes (the tokenizer tries 6 first), [`sym.table`](02-fields.md#sym.table), [`sym.code`](02-fields.md#sym.code). Then SP or the end of the field. These three fields are tokens one level below `stat.grid`. The sender sends the letters in upper case. Lower case gives `syntax` on `grid.loc` ([amb.stat.grid](#amb.stat.grid)). | Optional | The symbol code | p. 105/81, p. 106/82 |
| <a id="stat.text"></a>`stat.text` | Status text | The rest, checked as [`cmt.text`](02-fields.md#cmt.text). A maximum of 62 characters without timestamp or locator. A maximum of 55 after a timestamp. A maximum of 54 after a locator, counting the leading SP. A longer text gives `value` at the first character past the limit ([amb.stat.len](#amb.stat.len)). | Optional | End of field | p. 104/80, p. 106/82 |
| <a id="stat.beam"></a>`stat.beam` | Beam heading and power | The last three bytes of the text, if they are `'^'`, a digit or `'A'`–`'Z'`, and a byte 0x31–0x4B. If not, these bytes are text. A token one level below `stat.text`. | Optional | End of field | p. 105/81 |
| <a id="stat.freq"></a>`stat.freq` | Frequency | Section 7 at the start of `stat.text`, after the SP that follows a locator. | Optional | — | p. 111/87, p. 115/91 |

In `stat.text`, the tokenizer looks only for these fields:

- a frequency at its start;
- a beam heading at its end;
- `'!x!'` ([`cmt.noarchive`](02-fields.md#cmt.noarchive), p. 110/86).

## 3. Station capabilities

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cap.dti"></a>`cap.dti` | Identifier | `'<'` | Required | 1 byte | p. 31/17, p. 101/77 |
| <a id="cap.item"></a>`cap.item` | Capability | A `cap.token`, or a `cap.token`, `'='` and a `cap.value`. `cap.sep` separates the capabilities. An empty capability, or one of only SP, gives `syntax`. | At least one | `','` or end of field | p. 101/77 |
| <a id="cap.sep"></a>`cap.sep` | Separator | `','` | Between capabilities | 1 byte | p. 101/77 |
| <a id="cap.token"></a>`cap.token` | Token | One or more bytes other than `','` and `'='`. APRS12c specifies no byte set. A `cap.token` of only SP before `'='` gives `syntax`. | Required | `'='`, `','` or end of field | p. 101/77 |
| <a id="cap.value"></a>`cap.value` | Value | One or more bytes other than `','`. APRS12c specifies no byte set. If nothing follows `'='`, the `cap.value` gives `syntax`. The values of `MSG_CNT` and `LOC_CNT` are counts: a byte that is not a digit gives `syntax`. | Optional | `','` or end of field | p. 101/77 |
| <a id="cap.pad"></a>`cap.pad` | Padding | SP before or after a `cap.token` or a `cap.value`. It is a token of its own, with `ambiguous` at its first byte ([amb.cap.form](#amb.cap.form)). | Optional | The next byte that is not SP | p. 155/131 |

Each capability is a `cap.item` token. Its `cap.pad`, `cap.token` and
`cap.value` are tokens one level below it. The `'='` has no token.

## 4. General queries

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="qry.dti"></a>`qry.dti` | Identifier | `'?'` | Required | 1 byte | p. 31/17, p. 102/78 |
| <a id="qry.type"></a>`qry.type` | Query type | Upper-case letters: `APRS`, `IGATE`, `WX`. Another upper-case type gives `unstated` ([amb.qry.type](#amb.qry.type)). Any other byte gives `syntax` at the first such byte. An empty type gives `syntax`. | Required | The next `'?'` | p. 101/77, p. 102/78 |
| <a id="qry.end"></a>`qry.end` | Closing mark | `'?'`. If it is missing, it gives `syntax` where it was expected. Then the tokenizer continues only if a footprint starts there. | Required | 1 byte | p. 102/78 |
| <a id="qry.fp"></a>`qry.fp` | Target footprint | `qry.lat`, `','`, `qry.lon`, `','`, `qry.radius`, all or none, as tokens one level below `qry.fp` ([amb.qry.fp](#amb.qry.fp)). These give `syntax` on `qry.fp`: bytes that do not start with a number, a missing `','`, or bytes after the radius. Bytes that the tokenizer cannot place are residue. | Optional | End of field | p. 102/78 |
| <a id="qry.lat"></a>`qry.lat` | Latitude | SP (north) or `'-'` (south), then digits, optionally `'.'` and digits. A missing sign or `'+'` gives `syntax`. Over 90 gives `value`. | In `qry.fp` | `','` | p. 102/78 |
| <a id="qry.lon"></a>`qry.lon` | Longitude | As `qry.lat`, with SP for east and `'-'` for west, up to 180. | In `qry.fp` | `','` | p. 102/78 |
| <a id="qry.radius"></a>`qry.radius` | Radius | Exactly 4 digits, in miles. A byte that is not a digit, or a missing byte, gives `syntax`. | In `qry.fp` | 4 bytes | p. 102/78 |

A missing field gives `syntax` on its own rule where it was expected.

### 4.1 Directed queries

A directed query is a message with no message identifier (p. 103/79).
Its text is `'?'`, a query type and optionally the callsign of a heard
station.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="qry.dir.dti"></a>`qry.dir.dti` | Identifier | `':'` at offset 0 of a message whose text matches this section. | Required | 1 byte | p. 31/17, p. 103/79 |
| <a id="qry.dir.mark"></a>`qry.dir.mark` | Query mark | `'?'` at offset 11 | Required | 1 byte | p. 103/79 |
| <a id="qry.dir.type"></a>`qry.dir.type` | Query type | 5 bytes: `APRSD`, `APRSH`, `APRSM`, `APRSO`, `APRSP`, `APRSS`, `APRST` or `PING?`. Another type gives `unstated` ([amb.qry.dir](#amb.qry.dir)). | Required | 5 bytes | p. 101/77, p. 103/79 |
| <a id="qry.dir.sep"></a>`qry.dir.sep` | Separator | One SP directly before `qry.dir.call` ([err.qry.directed](#err.qry.directed)). | Optional | 1 byte | p. 103/79 |
| <a id="qry.dir.call"></a>`qry.dir.call` | Heard station | 1 to 9 letters, digits or `'-'`. It is for `APRSH`. With another type, it gives `unstated`. | Optional | SP or end of field | p. 101/77, p. 103/79 |
| <a id="qry.dir.pad"></a>`qry.dir.pad` | Padding | SP up to the end of the field. If there is no callsign, every SP after the type. | Optional | End of field | p. 103/79 |

A text with `'{'` is a message: directed queries never contain a message
identifier (p. 103/79). A text that starts with `'?'` and does not match
these rows is message text, with no finding
([08 section 11](08-message.md#11-reviewed-exceptions)). The text of a
directed query counts toward the limit of 67 characters of
[`msg.text`](08-message.md#msg.text)
([08 section 2.1](08-message.md#21-kind-of-packet), case 5).

## 5. User-defined data

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="udf.dti"></a>`udf.dti` | Identifier | `'{'` | Required | 1 byte | p. 31/17, p. 121/97 |
| <a id="udf.user"></a>`udf.user` | User ID | One byte. `'{'` is experimental. Outside 0x21–0x7E: `unstated`. Missing: `syntax` at the end of the field. | Required | 1 byte | p. 121/97 |
| <a id="udf.type"></a>`udf.type` | Packet type | One byte. Outside 0x21–0x7E: `unstated`. Missing: `syntax`. | Required | 1 byte | p. 121/97 |
| <a id="udf.data"></a>`udf.data` | Data | Any bytes. APRS12c only recommends printable ASCII, so there is no finding. A `'!x!'` in it is [`cmt.noarchive`](02-fields.md#cmt.noarchive) one level below (p. 110/86). | Optional | End of field | p. 110/86, p. 121/97 |

The tokenizer does not check the list of assigned user IDs (p. 122/98).

## 6. Invalid or test data

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="inv.dti"></a>`inv.dti` | Identifier | `','` | Required | 1 byte | p. 31/17, p. 123/99 |
| <a id="inv.data"></a>`inv.data` | Data | Any bytes, possibly none. No finding. A `'!x!'` in it is `cmt.noarchive` one level below. | Optional | End of field | p. 110/86, p. 123/99 |

## 7. Frequency specification

The tokenizer looks for a frequency in the first bytes of the text of
these fields (p. 111/87, p. 112/88, p. 115/91):

- a position comment (fixed or automatic);
- the comment of an Object or an Item;
- the Mic-E status text;
- status text.

The places are the start of `cmt.text` after any data extension, as
[03-position.md](03-position.md), [05-object-item.md](05-object-item.md)
and [04-mic-e.md](04-mic-e.md#5-status-text) place it, and `stat.freq`.
The tokenizer looks for a frequency in no other place. Its tokens are one
level below the text that contains them.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="freq.lead"></a>`freq.lead` | Delimiter | One `'/'` or SP directly before a frequency. | Optional | 1 byte | p. 115/91 |
| <a id="freq.mhz"></a>`freq.mhz` | Frequency in MHz | 3 digits, `'.'`, 3 digits, `MHz`. Or: 3 digits, `'.'`, 2 digits, SP, `MHz`. The sender sends `MHz` in that case. The tokenizer recognises another case, and it gives `syntax` at its first byte that differs ([amb.freq.case](#amb.freq.case)). | Optional | 10 bytes | p. 113/89, p. 114/90 |
| <a id="freq.uw"></a>`freq.uw` | Frequency above 999 MHz | As `freq.mhz`, with a letter `'A'`–`'O'` for the leading digits. | Optional | 10 bytes | p. 119/95, p. 120/96 |
| <a id="freq.ghz"></a>`freq.ghz` | Frequency in GHz | 3 bytes, each a digit or a leading SP, with at least one digit. Then `'.'`, 3 digits, `GHz`. | Optional | 10 bytes | p. 119/95 |
| <a id="freq.rx"></a>`freq.rx` | Alternate receive frequency | SP, 3 digits, `'.'`, 3 digits, `rx`. Only directly after a frequency. | Optional | 10 bytes | p. 114/90, p. 115/91 |
| <a id="freq.tone"></a>`freq.tone` | Tone | SP, then `'T'`, `'C'` or `'D'` and 3 digits, or `Toff`, `1750`, `l750`. A lower-case first letter marks narrow modulation. | Optional | 4 bytes, then SP or end of text | p. 114/90, p. 117/93 |
| <a id="freq.offset"></a>`freq.offset` | Transmit offset | SP, `'+'` or `'-'`, 3 digits in 10 kHz, up to 9.90 MHz. A value over 990 gives `value` at the sign. | Optional | 4 bytes, then SP or end of text | p. 114/90, p. 117/93 |
| <a id="freq.range"></a>`freq.range` | Range | SP, `'R'` or one of `'N'`, `'S'`, `'E'`, `'W'`, 2 digits, `'m'` or `'k'`. A maximum of one for each letter. | Optional | 4 bytes, then SP or end of text | p. 114/90, p. 115/91 |
| <a id="freq.dstar"></a>`freq.dstar` | D-STAR marker | `D-STAR`, then SP, or `'>'` and a repeater name of 8 bytes. The name is a callsign of upper-case letters and digits, padded with SP to 6 bytes, then SP and a module letter. After a frequency and an optional offset, or at the start of the text. | Optional | 7 or 15 bytes | p. 116/92 |
| <a id="freq.obj"></a>`freq.obj` | Left-justified items | If the text does not start with a frequency, the tokenizer reads `freq.tone`, `freq.offset` and `freq.range` from its start. The first of them has no SP before it ([amb.freq.nofreq](#amb.freq.nofreq)). | Optional | — | p. 114/90, p. 115/91 |

After a frequency, the fields are `freq.rx`, `freq.tone`, `freq.offset`
and `freq.range`, in that order. Each is optional. `freq.dstar` can follow
the frequency or its offset, and the tokenizer reads nothing after it.
The token of each of these fields includes its leading SP. Bytes that
match no field at their place are text.

## 8. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.stat.grid"></a>`amb.stat.grid` | p. 105/81, p. 106/82 | A locator report is also valid status text. Text without the required SP can follow a locator and symbol. | ambiguous | 4, 5 | A locator and a symbol followed by SP or the end are `stat.grid`. There is no finding, because every packet of this format has the same ambiguity. Without the SP, or with a first-pair letter outside `'A'`–`'R'` (Maidenhead), the bytes are `stat.text`, with no finding. A subsquare letter outside `'A'`–`'X'` is not a subsquare. |
| <a id="amb.stat.len"></a>`amb.stat.len` | p. 104/80, p. 106/82 | The limits are in "characters", and the text can contain UTF-8. | ambiguous | 1 | The tokenizer counts characters: each byte that is not a UTF-8 continuation byte starts one. This is the interpretation that accepts more. |
| <a id="amb.cap.form"></a>`amb.cap.form` | p. 101/77, p. 155/131 | APRS12c specifies no byte set for `cap.token` and `cap.value`. It does not say whether SP can be around them, or whether a value can contain `'='`. | ambiguous | 2, 3, 4 | The tokenizer checks no byte set. A further `'='` in a value gives no finding. SP around a `cap.token` or a `cap.value`, as in the IGate report of p. 155/131, is `cap.pad` with `ambiguous`. |
| <a id="amb.qry.type"></a>`amb.qry.type` | p. 101/77, p. 102/78 | A directed or unlisted type in the general format. A station ignores queries that it does not recognise. | unstated | 2 | `unstated` on `qry.type`. |
| <a id="amb.qry.fp"></a>`amb.qry.fp` | p. 102/78 | APRS12c describes the footprint for `APRS` only, but the general diagram has it for every type. | ambiguous | 1 | A footprint after any general type, with no finding. |
| <a id="amb.qry.dir"></a>`amb.qry.dir` | p. 101/77, p. 103/79 | Whether a `'?'` text with an unlisted type is a query or a message. The separator and the padding of the callsign ([err.qry.directed](#err.qry.directed)). | ambiguous | 2, 3, 4 | A text of `'?'`, a type of five upper-case letters or `PING?`, and an optional callsign is a directed query, the stricter format. An unlisted type gives `unstated`. Every packet of this format has the same ambiguity, so there is no `ambiguous`. Other texts are messages, with no finding, also when they start with `'?'` ([08 section 11](08-message.md#11-reviewed-exceptions)). |
| <a id="amb.qry.response"></a>`amb.qry.response` | p. 93/71, p. 101/77, p. 103/79 | Responses contain no message identifier. But the `APRSM` example answer ends in `{003`. | conflict | 3 | Nothing marks a packet as a response: no effect. |
| <a id="amb.freq.case"></a>`amb.freq.case` | p. 114/90 | APRS12c requires `MHz` in mixed case when the sender sends it. A receiver is to ignore case. | ambiguous | 1 | The tokenizer recognises another case as the frequency, and it gives `syntax`: the requirement for sending restricts the bytes. |
| <a id="amb.freq.items"></a>`amb.freq.items` | p. 112/88, p. 114/90, p. 115/91 | The examples put tone, offset and range in that order. APRS12c specifies no order. It shows range with two digits only. | ambiguous | 1, 2 | The tokenizer reads the fields in that order. A field out of order, or a range of three digits, is text with no finding. |
| <a id="amb.freq.nofreq"></a>`amb.freq.nofreq` | p. 114/90, p. 115/91 | APRS12c describes left-justified fields in general (p. 115/91). APRS12c shows them for frequency Objects only. | ambiguous | 1 | The tokenizer reads left-justified fields wherever it looks for a frequency and finds none. No finding. |
| <a id="amb.freq.objname"></a>`amb.freq.objname` | p. 113/89, p. 116/92, p. 117/93 | Nothing separates the name of a frequency Object from another name of digits and a point. APRS12c does not address padding. | ambiguous | 2 | The tokenizer does not classify names. It reads the comment of every Object and Item in the same way. No finding. |
| <a id="err.stat.grid"></a>`err.stat.grid` | p. 12/2, p. 105/81, p. 106/82 | The locator diagram makes the text 1 to 54 bytes and required. Two examples have none. | conflict | 3 | The tokenizer accepts both: the text is optional. |
| <a id="err.cap.bracket"></a>`err.cap.bracket` | p. 31/17, p. 101/77, p. 155/131 | Appendix 7 writes the IGate report after a "left bracket", as `IGate` with SP after the commas. Chapter 15 uses `'<'` and `IGATE`. | conflict | 3 | "Left bracket" is a typing error: it permits nothing. `'<'` is the identifier. The tokenizer reads a `'['` field by its own format. For the SP after the commas, see [amb.cap.form](#amb.cap.form). |
| <a id="err.qry.response"></a>`err.qry.response` | p. 102/78 | The example answer `/3402.78N11714.02W-` has the timestamp identifier with no timestamp and no table byte. | conflict | 3 | A clear typing error: it permits nothing. The position formats of 03-position apply. |
| <a id="err.qry.directed"></a>`err.qry.directed` | p. 103/79 | The diagram has no separator and needs no padding. The `APRSH` example puts a SP first and pads to 9 bytes. | conflict | 3 | The tokenizer accepts both formats. |
| <a id="err.freq.netmtg"></a>`err.freq.netmtg` | p. 116/92, p. 117/93 | The `NETxxxxxx` and `MTGxxxx` templates do not match their examples. | conflict | 3 | The tokenizer makes tokens for neither: no effect. |
| <a id="err.freq.optional"></a>`err.freq.optional` | p. 116/92, p. 117/93 | All four name formats end in identifying bytes that the next page calls optional. | conflict | 3 | The tokenizer accepts both. It does not classify names: no effect. |

## 9. Reviewed exceptions

None.

## 10. Open items

- Whether a tone can be between a frequency and `D-STAR`. The page names
  only the offset at that place (p. 116/92).
