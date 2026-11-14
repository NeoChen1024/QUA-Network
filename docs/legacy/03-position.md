# Position, DF, locator and NMEA reports

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, the general rules and the tokenizer model are in [README.md](README.md). |

## 1. Scope

The information fields that [01-frame.md](01-frame.md#dti) dispatches to
position formats: position reports (`!`, `=`, `/`, `@`) in both position
forms, DF reports, the Agrelo DF format (`%`), the Maidenhead locator
beacon (`[`) and raw NMEA (`$`). Rule prefixes `pos`, `df`, `grid`,
`nmea`. The shared fields are read by [02-fields.md](02-fields.md);
weather reports and storm data by [06-weather.md](06-weather.md). The
form `!!` never reaches this file, and a `$ULTW` field only when it is
also an NMEA sentence ([amb.dti.shared](01-frame.md#amb.dti.shared)). The byte-0 token carries
`pos.dti`, `df.agrelo.dti`, `grid.dti` or `nmea.dti`, and any finding
there is given by the `dti` rules of 01.

## 2. Position reports

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.dti"></a>`pos.dti` | Identifier | `!` or `=` (no timestamp), `/` or `@` (timestamp). `=` and `@` mark messaging capability. | Yes | 1 byte | p. 39/23, p. 50/32 |
| <a id="pos.time"></a>`pos.time` | Timestamp | After `/` or `@` only: [`time.dhm`](02-fields.md#time.dhm) or [`time.hms`](02-fields.md#time.hms), always the 7 bytes the layout fixes, read as [02 section 2](02-fields.md#2-timestamps) says; the position follows them. Missing gives `syntax`. `time.mdhm` belongs to positionless weather only and is not looked for: eight digits give `syntax` at offset 6. | For `/`, `@` | 7 bytes | p. 38/22, p. 50/32 |
| <a id="pos.form"></a>`pos.form` | Form selector | Not a token. A digit starts `pos.unc`; `/`, `\`, `A`–`Z`, `a`–`j` start `pos.cmp`; any other byte gives `syntax` and the rest of the field is residue. | Yes | — | p. 55/37, p. 125/101 |
| <a id="pos.unc"></a>`pos.unc` | Uncompressed position | Not a token: [`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code). | One of the two | 19 bytes | p. 50/32 |
| <a id="pos.cmp"></a>`pos.cmp` | Compressed position | [`cmp.block`](02-fields.md#cmp.block). | One of the two | 13 bytes | p. 55/37, p. 59/41 |
| <a id="pos.wx"></a>`pos.wx` | Weather hand-off | Symbol code `_`, any table, with at least one byte after the position block: those bytes are read by [06](06-weather.md) as [`wx.pos`](06-weather.md#wx.pos), and the byte-0 token carries `wx.pos` ([amb.pos.wxsym](#amb.pos.wxsym), [06 amb.wx.symbol](06-weather.md#amb.wx.symbol)). | — | End of field | p. 82/62, p. 85/65 |
| <a id="pos.null"></a>`pos.null` | Null position | Not a token: `0000.00N`, `00000.00W`, with no finding, whatever the symbol ([amb.lat.null](02-fields.md#amb.lat.null)). | — | — | p. 42/26 |

### 2.1 After an uncompressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.ext"></a>`pos.ext` | Data extension | The slot of [02 section 7.1](02-fields.md#71-the-extension-slot): with symbol `\l`, [`ext.area`](02-fields.md#ext.area) when it fits ([amb.pos.ext](#amb.pos.ext)); otherwise `ext.csespd`, `ext.phgr`, `ext.phg`, `ext.rng` or `ext.dfs`. After an `ext.csespd`: storm data with symbol `@` under any table byte ([06 section 8](06-weather.md#8-storm-data)), else bearing and NRQ ([02 section 7.4](02-fields.md#74-bearing-and-nrq)). | No | 7 bytes (9 for `ext.phgr`) | p. 45/27, p. 51/33 |
| <a id="pos.cmt"></a>`pos.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), after the extension, the bearing (section 3) or storm data (06). At most 43 characters, 36 after an extension ([amb.pos.cmtlen](#amb.pos.cmtlen)), 28 after bearing and NRQ, counted as [02 section 8.1](02-fields.md#81-comment-field) says; a longer one gives `value`. | No | End of field | p. 50/32, p. 51/33 |

The items of [02 section 8.2](02-fields.md#82-items-found-inside-a-comment)
are looked for in `pos.cmt`, `pos.cmpcmt` and `df.cmt`.

### 2.2 After a compressed position

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.cmpcmt"></a>`pos.cmpcmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), at most 40 characters; longer gives `value`. An extension at its start, the area descriptor under `\l`: [amb.pos.cmpext](#amb.pos.cmpext). | No | End of field | p. 59/41 |

## 3. DF reports

A position report in the uncompressed form with the DF symbol, an
extension and bearing and NRQ after it. A report with the DF symbol and
no bearing is an ordinary position report.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="df.sym"></a>`df.sym` | DF symbol | Not a token: `sym.table` `/` and `sym.code` `\`. An overlay makes another symbol. | Yes | — | p. 52/34 |
| <a id="df.ext"></a>`df.ext` | Extension | `pos.ext`: [`ext.csespd`](02-fields.md#ext.csespd), or by the diagrams any extension ([err.df.ext](#err.df.ext)). A course of `000` marks a fixed station. | Yes | 7 or 9 bytes | p. 48/30, p. 52/34 |
| <a id="df.brg"></a>`df.brg` | Bearing and NRQ | [`ext.brgnrq`](02-fields.md#ext.brgnrq) directly after `df.ext`, read as [02 section 7.4](02-fields.md#74-bearing-and-nrq) says. | Yes | 8 bytes | p. 48/30, p. 52/34, p. 53/35 |
| <a id="df.cmt"></a>`df.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), at most 28 characters; longer gives `value`. | No | End of field | p. 52/34, p. 53/35 |

## 4. Agrelo DF format

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="df.agrelo.dti"></a>`df.agrelo.dti` | Identifier | `%`. | Yes | 1 byte | p. 31/17, p. 138/114 |
| <a id="df.agrelo"></a>`df.agrelo` | Agrelo report | Bearing (3 digits), `/`, quality (1 digit). Other bytes give `syntax`; a bearing above 360 gives `value` at its first digit. Bytes after these five: [amb.df.agrelo](#amb.df.agrelo). | Yes | 5 bytes | p. 138/114, p. 153/129 |

## 5. Maidenhead locator beacon

The `[` identifier is obsolete; 01 gives the finding.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="grid.dti"></a>`grid.dti` | Identifier | `[`. | Yes | 1 byte | p. 42/26, p. 51/33 |
| <a id="grid.loc"></a>`grid.loc` | Locator | Two letters `A`–`R`, two digits, then optionally two letters `A`–`X` ([amb.grid.range](#amb.grid.range), [amb.grid.form](#amb.grid.form)). Letters are sent in upper case; lower case gives `syntax` at the first such letter ([amb.grid.case](#amb.grid.case)). Also used by [`stat.grid`](09-other.md#stat.grid), [`mice.grid`](04-mic-e.md#mice.grid) and [`dest.grid`](01-frame.md#dest.grid). | Yes | 4 or 6 bytes | p. 42/26, p. 51/33, p. 105/81, p. 150/126, p. 152/128 |
| <a id="grid.close"></a>`grid.close` | Closing bracket | `]` directly after `grid.loc`. | No | 1 byte | p. 51/33 |
| <a id="grid.cmt"></a>`grid.cmt` | Comment | The rest of the field, with the comment byte set of [`cmt.text`](02-fields.md#cmt.text) (`syntax` on `grid.cmt`) and no length limit. It holds the altitude and `'!x!'`; a beacon is not a position report, so the DAO is not looked for. | No | End of field | p. 34/20, p. 51/33 |

## 6. Raw NMEA

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nmea.dti"></a>`nmea.dti` | Identifier | `$`, when the field does not start `$ULTW`, or does and reads as a sentence here with no `syntax` or `value` finding; then `dti` also gives `ambiguous` at offset 1 ([amb.dti.shared](01-frame.md#amb.dti.shared)). Sending raw GPS data is discouraged: `discouraged` here. | Yes | 1 byte | p. 52/34 |
| <a id="nmea.addr"></a>`nmea.addr` | Address field | 5 bytes `A`–`Z`: talker and sentence type; else `syntax` ([amb.nmea.sentence](#amb.nmea.sentence)). | Yes | `,` or `*` | p. 42/26, p. 52/34 |
| <a id="nmea.field"></a>`nmea.field` | Data field | `,` then bytes `0x20`–`0x7E` other than `,`, `*` and `$`; one token per field; content not checked. | Yes, at least one | `,`, `*` or `nmea.end` | p. 52/34 |
| <a id="nmea.cks"></a>`nmea.cks` | Checksum | `*` and two hex digits, compared with the exclusive-or of the bytes between `$` and `*`; a mismatch gives `value` at the first digit ([amb.nmea.checksum](#amb.nmea.checksum)). Bytes after it, up to `nmea.end`, are residue with `syntax` ([amb.nmea.end](#amb.nmea.end)). | No | 3 bytes | p. 52/34 |
| <a id="nmea.end"></a>`nmea.end` | Sentence terminator | CR LF at the end of the field, after the checksum or the last field ([amb.nmea.end](#amb.nmea.end)). | No | 2 bytes | p. 42/26, p. 52/34 |
| <a id="nmea.len"></a>`nmea.len` | Sentence length | Not a token: 25 to 209 bytes after `$`, counted with or without `nmea.end`; else `value` at `nmea.dti`. | — | — | p. 52/34 |

## 7. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.pos.ext"></a>`amb.pos.ext` | p. 45/27, p. 49/31, p. 51/33, p. 78/60 | The area descriptor is among the extensions that may follow position data (p. 45/27); the position diagrams list four other kinds. | conflict | 3, 4 | With symbol `\l`, a slot that fits `ext.area` is that descriptor, the more specific form, with `ambiguous` at its first byte. Under other symbols the descriptor is not looked for. |
| <a id="amb.pos.cmpext"></a>`amb.pos.cmpext` | p. 45/27, p. 54/36, p. 59/41 | An extension after a compressed position. | conflict | 3, 4 | As [amb.ext.compressed](02-fields.md#amb.ext.compressed): under `\l` the area descriptor, otherwise a form of step 3. |
| <a id="amb.pos.wxsym"></a>`amb.pos.wxsym` | p. 51/33, p. 82/62, p. 85/65 | Symbol `_` identifies a weather report; a `_` position with an ordinary comment, or with nothing after it, is not addressed. | ambiguous | 1 | Nothing after the block: a position report, no finding. With bytes after it, the symbol announces weather data: they go to 06, which reads them as a weather report, its data and then a tail or a comment ([amb.wx.symbol](06-weather.md#amb.wx.symbol)). Reading all of them as a comment does not make a report without its wind field conform. |
| <a id="amb.pos.cmtlen"></a>`amb.pos.cmtlen` | p. 46/28, p. 50/32, p. 51/33 | At most 43 bytes after the symbol "in all cases", and 36 after a 7-byte extension; PHGR has 9. | conflict | 3 | 36 characters after `ext.phgr`. |
| <a id="err.df.ext"></a><a id="amb.df.ext"></a>`err.df.ext` (also `amb.df.ext`) | p. 45/27, p. 48/30, p. 52/34, p. 53/35 | The text puts bearing and NRQ after a course and speed; the DF diagrams after any of four extensions. | conflict | 3, 4 | DF symbol after another extension, bearing at most 360: `ext.brgnrq`, `ambiguous` at its first byte, `df.cmt` after it. A larger bearing there: comment text, no finding. |
| <a id="amb.df.detect"></a>`amb.df.detect` | p. 45/27, p. 52/34 | Bearing and NRQ after a course and speed are "only meaningful" with the DF symbol; p. 45/27 sets no symbol. | ambiguous | 4 | Another symbol after `ext.csespd`, bearing at most 360: `ext.brgnrq`, `ambiguous` at its first byte, comment limit 28. |
| <a id="amb.df.agrelo"></a>`amb.df.agrelo` | p. 34/20, p. 138/114 | The format is only a diagram; whether anything follows is not said, while p. 34/20 lets any packet carry a comment after its data. | conflict | none | Working choice: bytes after the fifth field are residue with `syntax`. |
| <a id="amb.grid.form"></a>`amb.grid.form` | p. 42/26, p. 51/33 | `[IO91SX` without `]`: a 6-byte locator, or 4 bytes and a comment. | ambiguous | 4 | Upper-case letters in range: 6-byte `grid.loc`, the more specific, `ambiguous` at byte 5 when the first four bytes fit. Other letters: the 4-byte reading, the one that accepts, no finding. |
| <a id="amb.grid.range"></a>`amb.grid.range` | p. 51/33, p. 150/126 | The letter ranges come only from the Maidenhead system the document names. | ambiguous | 5, 1 | First pair outside `A`–`R`: `syntax`. A subsquare letter outside `A`–`X` without `]`: 4-byte locator, comment, no finding. With `]` after six bytes, the bracket closes a 6-byte locator, which is judged as such: `syntax` at the letter; reading the letters and the `]` as comment does not make them conform. |
| <a id="amb.grid.case"></a>`amb.grid.case` | p. 105/81, p. 152/128 | Letters are transmitted in upper case and may be received in either. | ambiguous | 1 | The sending rule fixes the bytes: lower case gives `syntax`. In a subsquare without `]`, see amb.grid.form. |
| <a id="amb.nmea.sentence"></a>`amb.nmea.sentence` | p. 42/26, p. 52/34 | The sentence is given by reference to NMEA 0183 and by four examples; five types are recommended to receivers. | unstated | none | Working choice: the shape only, and no finding for any talker or type. |
| <a id="amb.nmea.checksum"></a>`amb.nmea.checksum` | p. 52/34 | Three examples carry a checksum, one none; the case of the hex digits is not given. | ambiguous | 3, 2 | Missing: no finding. Present: compared, a mismatch gives `value` (README section 3.2). Lower-case digits: `unstated`, still compared. |
| <a id="amb.nmea.end"></a>`amb.nmea.end` | p. 42/26, p. 52/34 | NMEA 0183 ends a sentence with CR LF; the examples show none; bytes after the checksum are not addressed. | conflict | 5, 3; none | CR LF at the end: `nmea.end`, no finding (rules 5, 3). Working choice: other bytes after the checksum are residue with `syntax`, as for [amb.df.agrelo](#amb.df.agrelo). |

## 8. Reviewed exceptions

None.

## 9. Open items

- A pinned text of NMEA 0183 and of the Maidenhead letter ranges (README
  rule 5). Until then the NMEA framing and the letter ranges are the
  general ones, recalled, not read.
