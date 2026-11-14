# Status, capabilities, queries and other formats

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. |
| Reference | `APRS12c.pdf` chapters 15, 16, 18, 19 and 20, in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, reading rules and tokenizer model: [README](README.md). |

## 1. Scope

The information fields that [01-frame.md](01-frame.md) dispatches to `>`
(status), `<` (station capabilities), `?` (general query), `{`
(user-defined) and `,` (invalid or test data); directed queries, which
[08-message.md](08-message.md) hands over from a message text; and the
frequency specification of chapter 18 at the start of a comment or of
status text. Net and meeting codes, node naming conventions, frequencies
in messages and DX cluster spots are not tokenized.

## 2. Status reports

`'>'`, then a timestamp, or a locator with a symbol, or neither, then text
(p. 104/80 to p. 106/82).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="stat.dti"></a>`stat.dti` | Identifier | `'>'` | Required | 1 byte | p. 31/17, p. 104/80 |
| <a id="stat.time"></a>`stat.time` | Timestamp | DHM zulu only: six digits and `'z'`, a [`time.dhm`](02-fields.md#time.dhm) token. Six digits and `'/'` or `'h'` are status text. | Optional | 7 bytes | p. 104/80 |
| <a id="stat.grid"></a>`stat.grid` | Locator with symbol | Directly after `'>'`, never with a timestamp: [`grid.loc`](03-position.md#grid.loc) of 6 or 4 bytes (6 tried first), [`sym.table`](02-fields.md#sym.table), [`sym.code`](02-fields.md#sym.code), then SP or the end of the field; these three are tokens one level deeper. Letters are sent in upper case: lower case gives `syntax` on `grid.loc` ([amb.stat.grid](#amb.stat.grid)). | Optional | The symbol code | p. 105/81, p. 106/82 |
| <a id="stat.text"></a>`stat.text` | Status text | The rest, checked as [`cmt.text`](02-fields.md#cmt.text). At most 62 characters without timestamp or locator, 55 after a timestamp, 54 after a locator counting the leading SP; more gives `value` at the first character past the limit ([amb.stat.len](#amb.stat.len)). | Optional | End of field | p. 104/80, p. 106/82 |
| <a id="stat.beam"></a>`stat.beam` | Beam heading and power | The last three bytes of the text when they are `'^'`, a digit or `'A'`–`'Z'`, and a byte 0x31–0x4B; otherwise plain text. A token one level below `stat.text`. | Optional | End of field | p. 105/81 |
| <a id="stat.freq"></a>`stat.freq` | Frequency | Section 7 at the start of `stat.text`, after the SP that follows a locator. | Optional | — | p. 111/87, p. 115/91 |

In `stat.text` only a frequency at its start, a beam heading at its end
and `'!x!'` ([`cmt.noarchive`](02-fields.md#cmt.noarchive), p. 110/86)
are looked for.

## 3. Station capabilities

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="cap.dti"></a>`cap.dti` | Identifier | `'<'` | Required | 1 byte | p. 31/17, p. 101/77 |
| <a id="cap.item"></a>`cap.item` | Capability | A token, or a token, `'='` and a value; items separated by `cap.sep`. An empty item, or one of SP only, gives `syntax`. | At least one | `','` or end of field | p. 101/77 |
| <a id="cap.sep"></a>`cap.sep` | Separator | `','` | Between items | 1 byte | p. 101/77 |
| <a id="cap.token"></a>`cap.token` | Token | One or more bytes other than `','` and `'='`; no byte set is stated. Only SP before `'='` gives `syntax`. | Required | `'='`, `','` or end of field | p. 101/77 |
| <a id="cap.value"></a>`cap.value` | Value | One or more bytes other than `','`; no byte set is stated. Nothing after `'='` gives `syntax`. The values of `MSG_CNT` and `LOC_CNT` are counts: a byte other than a digit gives `syntax`. | Optional | `','` or end of field | p. 101/77 |
| <a id="cap.pad"></a>`cap.pad` | Padding | SP before or after a token or value, a token of its own, with `ambiguous` at its first byte ([amb.cap.form](#amb.cap.form)). | Optional | The next byte that is not SP | p. 155/131 |

Each item is a `cap.item` token with its `cap.pad`, `cap.token` and
`cap.value` one level deeper; the `'='` has no token.

## 4. General queries

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="qry.dti"></a>`qry.dti` | Identifier | `'?'` | Required | 1 byte | p. 31/17, p. 102/78 |
| <a id="qry.type"></a>`qry.type` | Query type | Upper-case letters: `APRS`, `IGATE`, `WX`. Another upper-case type gives `unstated` ([amb.qry.type](#amb.qry.type)); any other byte `syntax` at the first such byte; an empty type `syntax`. | Required | The next `'?'` | p. 101/77, p. 102/78 |
| <a id="qry.end"></a>`qry.end` | Closing mark | `'?'`; missing gives `syntax` where it was expected, and reading goes on only where a footprint starts there. | Required | 1 byte | p. 102/78 |
| <a id="qry.fp"></a>`qry.fp` | Target footprint | `qry.lat`, `','`, `qry.lon`, `','`, `qry.radius`, all or none, as tokens one level deeper ([amb.qry.fp](#amb.qry.fp)). Bytes that do not start with a number, a missing `','`, or bytes after the radius give `syntax` on `qry.fp`; bytes it cannot place are a residue. | Optional | End of field | p. 102/78 |
| <a id="qry.lat"></a>`qry.lat` | Latitude | SP (north) or `'-'` (south), then digits, optionally `'.'` and digits. A missing sign or `'+'` gives `syntax`; over 90 `value`. | In `qry.fp` | `','` | p. 102/78 |
| <a id="qry.lon"></a>`qry.lon` | Longitude | As `qry.lat`, SP east and `'-'` west, up to 180. | In `qry.fp` | `','` | p. 102/78 |
| <a id="qry.radius"></a>`qry.radius` | Radius | Exactly 4 digits, miles; a byte that is not a digit, or a missing one, gives `syntax`. | In `qry.fp` | 4 bytes | p. 102/78 |

A missing part gives `syntax` on its own rule where it was expected.

### 4.1 Directed queries

A message whose text is `'?'`, a query type and optionally the callsign
of a heard station, with no message identifier (p. 103/79).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="qry.dir.dti"></a>`qry.dir.dti` | Identifier | `':'` at offset 0 of a message whose text matches this section. | Required | 1 byte | p. 31/17, p. 103/79 |
| <a id="qry.dir.mark"></a>`qry.dir.mark` | Query mark | `'?'` at offset 11 | Required | 1 byte | p. 103/79 |
| <a id="qry.dir.type"></a>`qry.dir.type` | Query type | 5 bytes: `APRSD`, `APRSH`, `APRSM`, `APRSO`, `APRSP`, `APRSS`, `APRST` or `PING?`; another type gives `unstated` ([amb.qry.dir](#amb.qry.dir)). | Required | 5 bytes | p. 101/77, p. 103/79 |
| <a id="qry.dir.sep"></a>`qry.dir.sep` | Separator | One SP directly before `qry.dir.call` ([err.qry.directed](#err.qry.directed)). | Optional | 1 byte | p. 103/79 |
| <a id="qry.dir.call"></a>`qry.dir.call` | Heard station | 1 to 9 letters, digits or `'-'`. Meant for `APRSH`; with another type `unstated`. | Optional | SP or end of field | p. 101/77, p. 103/79 |
| <a id="qry.dir.pad"></a>`qry.dir.pad` | Padding | SP to the end of the field; with no callsign, every SP after the type. | Optional | End of field | p. 103/79 |

A text with `'{'` is a message: directed queries never carry a message
identifier (p. 103/79). A text that starts with `'?'` and does not match
these rows is message text with no finding
([08 section 11](08-message.md#11-reviewed-exceptions)). The text of a
directed query counts toward the 67-character limit of
[`msg.text`](08-message.md#msg.text) ([08 section 2.1](08-message.md#21-kind-of-packet), case 5).

## 5. User-defined data

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="udf.dti"></a>`udf.dti` | Identifier | `'{'` | Required | 1 byte | p. 31/17, p. 121/97 |
| <a id="udf.user"></a>`udf.user` | User ID | One byte; `'{'` is experimental. Outside 0x21–0x7E: `unstated`. Missing: `syntax` at the end of the field. | Required | 1 byte | p. 121/97 |
| <a id="udf.type"></a>`udf.type` | Packet type | One byte. Outside 0x21–0x7E: `unstated`. Missing: `syntax`. | Required | 1 byte | p. 121/97 |
| <a id="udf.data"></a>`udf.data` | Data | Any bytes; printable ASCII is only recommended, so no finding. A `'!x!'` in it is [`cmt.noarchive`](02-fields.md#cmt.noarchive) one level deeper (p. 110/86). | Optional | End of field | p. 110/86, p. 121/97 |

The list of assigned user IDs (p. 122/98) is not checked.

## 6. Invalid or test data

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="inv.dti"></a>`inv.dti` | Identifier | `','` | Required | 1 byte | p. 31/17, p. 123/99 |
| <a id="inv.data"></a>`inv.data` | Data | Any bytes, possibly none; no finding. A `'!x!'` in it is `cmt.noarchive` one level deeper. | Optional | End of field | p. 110/86, p. 123/99 |

## 7. Frequency specification

A frequency is looked for in the first bytes of the free text of a
position comment (fixed or automatic), of an object or item comment, of
the Mic-E status text and of status text (p. 111/87, p. 112/88,
p. 115/91): at the start of `cmt.text` after any data extension, as
[03-position.md](03-position.md), [05-object-item.md](05-object-item.md)
and [04-mic-e.md](04-mic-e.md#5-status-text) place it, and at `stat.freq`.
Nowhere else. Its tokens lie one level below the text that holds them.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="freq.lead"></a>`freq.lead` | Delimiter | One `'/'` or SP directly before a frequency. | Optional | 1 byte | p. 115/91 |
| <a id="freq.mhz"></a>`freq.mhz` | Frequency in MHz | 3 digits, `'.'`, 3 digits, `MHz`; or 3 digits, `'.'`, 2 digits, SP, `MHz`. `MHz` is sent in that case: another case is recognised and gives `syntax` at its first differing byte ([amb.freq.case](#amb.freq.case)). | Optional | 10 bytes | p. 113/89, p. 114/90 |
| <a id="freq.uw"></a>`freq.uw` | Frequency above 999 MHz | As `freq.mhz`, with a letter `'A'`–`'O'` for the leading digits. | Optional | 10 bytes | p. 119/95, p. 120/96 |
| <a id="freq.ghz"></a>`freq.ghz` | Frequency in GHz | 3 bytes each a digit or a leading SP, at least one digit, `'.'`, 3 digits, `GHz`. | Optional | 10 bytes | p. 119/95 |
| <a id="freq.rx"></a>`freq.rx` | Alternate receive frequency | SP, 3 digits, `'.'`, 3 digits, `rx`; only directly after a frequency. | Optional | 10 bytes | p. 114/90, p. 115/91 |
| <a id="freq.tone"></a>`freq.tone` | Tone | SP, then `'T'`, `'C'` or `'D'` and 3 digits, or `Toff`, `1750`, `l750`; a lower-case first letter marks narrow modulation. | Optional | 4 bytes, then SP or end of text | p. 114/90, p. 117/93 |
| <a id="freq.offset"></a>`freq.offset` | Transmit offset | SP, `'+'` or `'-'`, 3 digits in 10 kHz, up to 9.90 MHz: over 990 gives `value` at the sign. | Optional | 4 bytes, then SP or end of text | p. 114/90, p. 117/93 |
| <a id="freq.range"></a>`freq.range` | Range | SP, `'R'` or one of `'N'`, `'S'`, `'E'`, `'W'`, 2 digits, `'m'` or `'k'`; at most one per letter. | Optional | 4 bytes, then SP or end of text | p. 114/90, p. 115/91 |
| <a id="freq.dstar"></a>`freq.dstar` | D-STAR marker | `D-STAR`, then SP, or `'>'` and an 8-byte repeater name (a callsign of upper-case letters and digits padded with SP to 6 bytes, SP, a module letter). After a frequency and an optional offset, or at the start of the text. | Optional | 7 or 15 bytes | p. 116/92 |
| <a id="freq.obj"></a>`freq.obj` | Left-justified items | Where the text starts with no frequency, `freq.tone`, `freq.offset` and `freq.range` are read from its start, the first with no SP before it ([amb.freq.nofreq](#amb.freq.nofreq)). | Optional | — | p. 114/90, p. 115/91 |

After a frequency the items are `freq.rx`, `freq.tone`, `freq.offset`,
`freq.range`, in that order, each optional; `freq.dstar` can follow the
frequency or its offset, and nothing is read after it. An item token
includes its leading SP. Bytes that fit no item in its place are text.

## 8. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.stat.grid"></a>`amb.stat.grid` | p. 105/81, p. 106/82 | A locator report is also valid plain status text; a locator and symbol may be followed by text without the required SP. | ambiguous | 4, 5 | Locator and symbol followed by SP or the end are `stat.grid`, with no finding, as every instance carries the plain-text reading. Without the SP, or with a first-pair letter outside `'A'`–`'R'` (Maidenhead), the bytes are `stat.text`, with no finding. A subsquare letter outside `'A'`–`'X'` is no subsquare. |
| <a id="amb.stat.len"></a>`amb.stat.len` | p. 104/80, p. 106/82 | The limits are in "characters", and the text may hold UTF-8. | ambiguous | 1 | Counted in characters (each byte that is not a UTF-8 continuation byte starts one), the reading that accepts more. |
| <a id="amb.cap.form"></a>`amb.cap.form` | p. 101/77, p. 155/131 | No byte set for tokens and values; whether SP may surround them; whether a value may hold `'='`. | ambiguous | 2, 3, 4 | No byte set is checked, and a further `'='` in a value gives no finding. SP around a token or value, as in the IGate report of p. 155/131, is `cap.pad` with `ambiguous`. |
| <a id="amb.qry.type"></a>`amb.qry.type` | p. 101/77, p. 102/78 | A directed or unlisted type in the general form; a station ignores queries it does not recognise. | unstated | 2 | `unstated` on `qry.type`. |
| <a id="amb.qry.fp"></a>`amb.qry.fp` | p. 102/78 | The footprint is described for `APRS` only, while the general diagram carries it for every type. | ambiguous | 1 | A footprint after any general type, with no finding. |
| <a id="amb.qry.dir"></a>`amb.qry.dir` | p. 101/77, p. 103/79 | Whether a `'?'` text with an unlisted type is a query or a message; the separator and padding of the callsign ([err.qry.directed](#err.qry.directed)). | ambiguous | 2, 3, 4 | A text of `'?'`, a type of five upper-case letters or `PING?`, and an optional callsign is a directed query, the more specific form, with `unstated` on an unlisted type; every instance carries the message reading, so no `ambiguous`. Other texts are messages, with no finding, also when they start with `'?'` ([08 section 11](08-message.md#11-reviewed-exceptions)). |
| <a id="amb.qry.response"></a>`amb.qry.response` | p. 93/71, p. 101/77, p. 103/79 | Responses carry no message identifier, yet the `APRSM` example answer ends in `{003`. | conflict | 3 | Nothing marks a packet as a response: no effect. |
| <a id="amb.freq.case"></a>`amb.freq.case` | p. 114/90 | `MHz` is required in mixed case when sent, and case is to be ignored on receipt. | ambiguous | 1 | Another case is recognised as the frequency and gives `syntax`: the sending rule fixes the bytes. |
| <a id="amb.freq.items"></a>`amb.freq.items` | p. 112/88, p. 114/90, p. 115/91 | The examples put tone, offset and range in that order; no order is stated; range is shown with two digits only. | ambiguous | 1, 2 | Items are read in that order; an item out of order, or a range of three digits, is text with no finding. |
| <a id="amb.freq.nofreq"></a>`amb.freq.nofreq` | p. 114/90, p. 115/91 | Left-justified items are stated in general on p. 115/91 and shown for frequency objects only. | ambiguous | 1 | Left-justified items are read wherever a frequency is looked for and none is found, with no finding. |
| <a id="amb.freq.objname"></a>`amb.freq.objname` | p. 113/89, p. 116/92, p. 117/93 | Nothing separates a frequency object name from another name of digits and a point; padding is not addressed. | ambiguous | 2 | Names are not classified; the comment of every object and item is read alike. No finding. |
| <a id="err.stat.grid"></a>`err.stat.grid` | p. 12/2, p. 105/81, p. 106/82 | The locator diagram makes the text 1 to 54 bytes and required; two examples have none. | conflict | 3 | Both accepted: the text is optional. |
| <a id="err.cap.bracket"></a>`err.cap.bracket` | p. 31/17, p. 101/77, p. 155/131 | Appendix 7 writes the IGate report after a "left bracket", as `IGate` with SP after the commas; chapter 15 uses `'<'` and `IGATE`. | conflict | 3 | "Left bracket" is a slip of the pen: it allows nothing. `'<'` is the identifier, and a `'['` field is read by its own format. The SP after the commas: [amb.cap.form](#amb.cap.form). |
| <a id="err.qry.response"></a>`err.qry.response` | p. 102/78 | The example answer `/3402.78N11714.02W-` has the timestamp identifier with no timestamp and no table byte. | conflict | 3 | A plain slip: it allows nothing; the position formats of 03-position apply. |
| <a id="err.qry.directed"></a>`err.qry.directed` | p. 103/79 | The diagram has no separator and needs no padding; the `APRSH` example puts a SP first and pads to 9 bytes. | conflict | 3 | Both forms accepted. |
| <a id="err.freq.netmtg"></a>`err.freq.netmtg` | p. 116/92, p. 117/93 | The `NETxxxxxx` and `MTGxxxx` templates do not match their examples. | conflict | 3 | Neither is tokenized: no effect. |
| <a id="err.freq.optional"></a>`err.freq.optional` | p. 116/92, p. 117/93 | All four name forms end in identifying bytes that the next page calls optional. | conflict | 3 | Both accepted; names are not classified: no effect. |

## 9. Reviewed exceptions

None.

## 10. Open items

- Whether a tone can stand between a frequency and `D-STAR`: the page
  names only the offset there (p. 116/92).
