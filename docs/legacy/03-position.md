# Position, DF, locator and NMEA reports

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions, the general rules and the tokenizer model are in [README](README.md). |

## 1. Scope

This file covers the information fields that
[01-frame.md](01-frame.md#dti) passes to the position formats:

- position reports (`!`, `=`, `/`, `@`), in both position formats;
- DF reports;
- the Agrelo DF format (`%`);
- the Maidenhead locator beacon (`[`);
- raw NMEA (`$`).

The rule prefixes are `pos`, `df`, `grid` and `nmea`.
[02-fields.md](02-fields.md) reads the shared fields.
[06-weather.md](06-weather.md) reads weather reports and storm data.

The format `!!` never comes to this file. A `$ULTW` field comes to this
file only if it is also an NMEA sentence
([amb.dti.shared](01-frame.md#amb.dti.shared)). The token of byte 0 has
the rule ID `pos.dti`, `df.agrelo.dti`, `grid.dti` or `nmea.dti`. The
`dti` rules of 01 give any finding at this byte.

## 2. Position reports

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.dti"></a>`pos.dti` | Identifier | `!` or `=` (no timestamp), `/` or `@` (timestamp). `=` and `@` mark messaging capability. | Yes | 1 byte | p. 39/23, p. 50/32 |
| <a id="pos.time"></a>`pos.time` | Timestamp | After `/` or `@` only: [`time.dhm`](02-fields.md#time.dhm) or [`time.hms`](02-fields.md#time.hms). Always the 7 bytes of the format, read as [02 section 2](02-fields.md#2-timestamps) says. The position follows these bytes. A missing timestamp gives `syntax`. `time.mdhm` is only for positionless weather, and the tokenizer does not look for it: eight digits give `syntax` at offset 6. | For `/`, `@` | 7 bytes | p. 38/22, p. 50/32 |
| <a id="pos.form"></a>`pos.form` | Form selector | Not a token. A digit starts `pos.unc`. `/`, `\`, `A`–`Z` and `a`–`j` start `pos.cmp`. Any other byte gives `syntax`, and the rest of the bytes are residue. | Yes | — | p. 55/37, p. 125/101 |
| <a id="pos.unc"></a>`pos.unc` | Uncompressed position | Not a token: [`lat`](02-fields.md#lat), [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon), [`sym.code`](02-fields.md#sym.code). | One of the two | 19 bytes | p. 50/32 |
| <a id="pos.cmp"></a>`pos.cmp` | Compressed position | [`cmp.block`](02-fields.md#cmp.block). | One of the two | 13 bytes | p. 55/37, p. 59/41 |
| <a id="pos.wx"></a>`pos.wx` | Weather hand-off | Symbol code `_`, any table, with at least one byte after the position block. [06](06-weather.md) reads those bytes as [`wx.pos`](06-weather.md#wx.pos), and the token of byte 0 has the rule ID `wx.pos` ([amb.pos.wxsym](#amb.pos.wxsym), [06 amb.wx.symbol](06-weather.md#amb.wx.symbol)). | — | End of field | p. 82/62, p. 85/65 |
| <a id="pos.null"></a>`pos.null` | Null position | Not a token: `0000.00N`, `00000.00W`, with no finding, with any symbol ([amb.lat.null](02-fields.md#amb.lat.null)). | — | — | p. 42/26 |

### 2.1 After an uncompressed position

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.ext"></a>`pos.ext` | Data extension | The slot of [02 section 7.1](02-fields.md#71-the-extension-slot). With symbol `\l`: [`ext.area`](02-fields.md#ext.area) if it matches ([amb.pos.ext](#amb.pos.ext)). In other cases: `ext.csespd`, `ext.phgr`, `ext.phg`, `ext.rng` or `ext.dfs`. After an `ext.csespd`: storm data if the symbol code is `@`, under any table byte ([06 section 8](06-weather.md#8-storm-data)). If there is no storm data: bearing and NRQ ([02 section 7.4](02-fields.md#74-bearing-and-nrq)). | No | 7 bytes (9 for `ext.phgr`) | p. 45/27, p. 51/33 |
| <a id="pos.cmt"></a>`pos.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), after the extension, the bearing (section 3) or storm data (06). A maximum of 43 characters. A maximum of 36 after an extension ([amb.pos.cmtlen](#amb.pos.cmtlen)). A maximum of 28 after bearing and NRQ. The tokenizer counts characters as [02 section 8.1](02-fields.md#81-comment-field) says. A longer comment gives `value`. | No | End of field | p. 50/32, p. 51/33 |

The tokenizer looks for the fields of
[02 section 8.2](02-fields.md#82-items-found-inside-a-comment) in
`pos.cmt`, `pos.cmpcmt` and `df.cmt`.

### 2.2 After a compressed position

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="pos.cmpcmt"></a>`pos.cmpcmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), a maximum of 40 characters. A longer comment gives `value`. For an extension at its start, or the area descriptor under `\l`, see [amb.pos.cmpext](#amb.pos.cmpext). | No | End of field | p. 59/41 |

## 3. DF reports

A DF report is a position report in the uncompressed format with the DF
symbol. It has an extension, and bearing and NRQ after the extension. A
report with the DF symbol and no bearing is an ordinary position report.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="df.sym"></a>`df.sym` | DF symbol | Not a token: `sym.table` `/` and `sym.code` `\`. An overlay makes a different symbol. | Yes | — | p. 52/34 |
| <a id="df.ext"></a>`df.ext` | Extension | `pos.ext`: [`ext.csespd`](02-fields.md#ext.csespd), or, by the diagrams, any extension ([err.df.ext](#err.df.ext)). A course of `000` marks a fixed station. | Yes | 7 or 9 bytes | p. 48/30, p. 52/34 |
| <a id="df.brg"></a>`df.brg` | Bearing and NRQ | [`ext.brgnrq`](02-fields.md#ext.brgnrq) directly after `df.ext`, read as [02 section 7.4](02-fields.md#74-bearing-and-nrq) says. | Yes | 8 bytes | p. 48/30, p. 52/34, p. 53/35 |
| <a id="df.cmt"></a>`df.cmt` | Comment | [`cmt.text`](02-fields.md#cmt.text), a maximum of 28 characters. A longer comment gives `value`. | No | End of field | p. 52/34, p. 53/35 |

## 4. Agrelo DF format

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="df.agrelo.dti"></a>`df.agrelo.dti` | Identifier | `%`. | Yes | 1 byte | p. 31/17, p. 138/114 |
| <a id="df.agrelo"></a>`df.agrelo` | Agrelo report | Bearing (3 digits), `/`, quality (1 digit). Other bytes give `syntax`. A bearing above 360 gives `value` at its first digit. For bytes after these five, see [amb.df.agrelo](#amb.df.agrelo). | Yes | 5 bytes | p. 138/114, p. 153/129 |

## 5. Maidenhead locator beacon

The `[` identifier is obsolete. 01 gives the finding.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="grid.dti"></a>`grid.dti` | Identifier | `[`. | Yes | 1 byte | p. 42/26, p. 51/33 |
| <a id="grid.loc"></a>`grid.loc` | Locator | Two letters `A`–`R`, two digits, then optionally two letters `A`–`X` ([amb.grid.range](#amb.grid.range), [amb.grid.form](#amb.grid.form)). The sender sends the letters in upper case. Lower case gives `syntax` at the first lower-case letter ([amb.grid.case](#amb.grid.case)). [`stat.grid`](09-other.md#stat.grid), [`mice.grid`](04-mic-e.md#mice.grid) and [`dest.grid`](01-frame.md#dest.grid) also use this rule. | Yes | 4 or 6 bytes | p. 42/26, p. 51/33, p. 105/81, p. 150/126, p. 152/128 |
| <a id="grid.close"></a>`grid.close` | Closing bracket | `]` directly after `grid.loc`. | No | 1 byte | p. 51/33 |
| <a id="grid.cmt"></a>`grid.cmt` | Comment | The rest of the field. It uses the comment byte set of [`cmt.text`](02-fields.md#cmt.text) (`syntax` on `grid.cmt`) and has no length limit. The tokenizer looks for the altitude and `'!x!'` in it. A beacon is not a position report, so the tokenizer does not look for the DAO. | No | End of field | p. 34/20, p. 51/33 |

## 6. Raw NMEA

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="nmea.dti"></a>`nmea.dti` | Identifier | `$`. A field can start with `$ULTW`. Then the `$` is `nmea.dti` only if this file reads the field as a sentence with no `syntax` or `value` finding. In that case, `dti` also gives `ambiguous` at offset 1 ([amb.dti.shared](01-frame.md#amb.dti.shared)). APRS12c discourages sending raw GPS data: `discouraged` here. | Yes | 1 byte | p. 52/34 |
| <a id="nmea.addr"></a>`nmea.addr` | Address field | 5 bytes `A`–`Z`: talker and sentence type. Other bytes give `syntax` ([amb.nmea.sentence](#amb.nmea.sentence)). | Yes | `,` or `*` | p. 42/26, p. 52/34 |
| <a id="nmea.field"></a>`nmea.field` | Data field | `,`, then bytes `0x20`–`0x7E` other than `,`, `*` and `$`. One token for each field. The tokenizer does not check the content. | Yes, at least one | `,`, `*` or `nmea.end` | p. 52/34 |
| <a id="nmea.cks"></a>`nmea.cks` | Checksum | `*` and two hex digits. The tokenizer compares them with the exclusive-or of the bytes between `$` and `*`. A mismatch gives `value` at the first digit ([amb.nmea.checksum](#amb.nmea.checksum)). Bytes after the checksum, up to `nmea.end`, are residue with `syntax` ([amb.nmea.end](#amb.nmea.end)). | No | 3 bytes | p. 52/34 |
| <a id="nmea.end"></a>`nmea.end` | Sentence terminator | CR LF at the end of the field, after the checksum or the last field ([amb.nmea.end](#amb.nmea.end)). | No | 2 bytes | p. 42/26, p. 52/34 |
| <a id="nmea.len"></a>`nmea.len` | Sentence length | Not a token: 25 to 209 bytes after `$`, counted with or without `nmea.end`. Other lengths give `value` at `nmea.dti`. | — | — | p. 52/34 |

## 7. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.pos.ext"></a>`amb.pos.ext` | p. 45/27, p. 49/31, p. 51/33, p. 78/60 | The area descriptor is one of the extensions that can follow position data (p. 45/27). The position diagrams list four other kinds. | conflict | 3, 4 | With symbol `\l`, a slot that matches `ext.area` is that descriptor, the stricter format, with `ambiguous` at its first byte. With other symbols, the tokenizer does not look for the descriptor. |
| <a id="amb.pos.cmpext"></a>`amb.pos.cmpext` | p. 45/27, p. 54/36, p. 59/41 | An extension after a compressed position. | conflict | 3, 4 | As [amb.ext.compressed](02-fields.md#amb.ext.compressed): under `\l` the area descriptor, in other cases a format of step 3. |
| <a id="amb.pos.wxsym"></a>`amb.pos.wxsym` | p. 51/33, p. 82/62, p. 85/65 | Symbol `_` identifies a weather report. APRS12c does not address a `_` position with an ordinary comment, or with nothing after it. | ambiguous | 1 | Nothing after the block: a position report, with no finding. Bytes after the block: the symbol is a marker that starts weather data. The bytes go to 06. 06 reads them as a weather report: its data, then a tail or a comment ([amb.wx.symbol](06-weather.md#amb.wx.symbol)). An interpretation of all the bytes as a comment does not prevent the finding for a missing wind field. |
| <a id="amb.pos.cmtlen"></a>`amb.pos.cmtlen` | p. 46/28, p. 50/32, p. 51/33 | A maximum of 43 bytes after the symbol "in all cases", and 36 after an extension of 7 bytes. PHGR has 9. | conflict | 3 | 36 characters after `ext.phgr`. |
| <a id="err.df.ext"></a><a id="amb.df.ext"></a>`err.df.ext` (also `amb.df.ext`) | p. 45/27, p. 48/30, p. 52/34, p. 53/35 | The description in APRS12c puts bearing and NRQ after a course and speed. The DF diagrams put them after any of four extensions. | conflict | 3, 4 | DF symbol after another extension, with a bearing of 360 or less: `ext.brgnrq`, with `ambiguous` at its first byte, and `df.cmt` after it. A larger bearing there: comment text, no finding. |
| <a id="amb.df.detect"></a>`amb.df.detect` | p. 45/27, p. 52/34 | Bearing and NRQ after a course and speed are "only meaningful" with the DF symbol. The description in APRS12c specifies no symbol (p. 45/27). | ambiguous | 4 | Another symbol after `ext.csespd`, with a bearing of 360 or less: `ext.brgnrq`, with `ambiguous` at its first byte, and a comment limit of 28. |
| <a id="amb.df.agrelo"></a>`amb.df.agrelo` | p. 34/20, p. 138/114 | The format is only a diagram. APRS12c does not say whether anything follows it. But APRS12c permits a comment after the data of any packet (p. 34/20). | conflict | none | Working choice: bytes after the fifth field are residue with `syntax`. |
| <a id="amb.grid.form"></a>`amb.grid.form` | p. 42/26, p. 51/33 | `[IO91SX` without `]`: a locator of 6 bytes, or 4 bytes and a comment. | ambiguous | 4 | Upper-case letters in range: `grid.loc` of 6 bytes, the stricter format. It gives `ambiguous` at byte 5 when the first four bytes match. Other letters: the interpretation with 4 bytes, which accepts the bytes, with no finding. |
| <a id="amb.grid.range"></a>`amb.grid.range` | p. 51/33, p. 150/126 | The letter ranges come only from the Maidenhead system that APRS12c names. | ambiguous | 5, 1 | First pair outside `A`–`R`: `syntax`. A subsquare letter outside `A`–`X` without `]`: a locator of 4 bytes and a comment, with no finding. If `]` follows six bytes, the bracket closes a locator of 6 bytes. The tokenizer reads that locator as such: `syntax` at the letter. An interpretation of the bytes as a comment does not prevent the finding. |
| <a id="amb.grid.case"></a>`amb.grid.case` | p. 105/81, p. 152/128 | APRS12c says that the sender transmits the letters in upper case. A receiver can receive them in either case. | ambiguous | 1 | The requirement for sending restricts the bytes: lower case gives `syntax`. For a subsquare without `]`, see amb.grid.form. |
| <a id="amb.nmea.sentence"></a>`amb.nmea.sentence` | p. 42/26, p. 52/34 | APRS12c specifies the sentence by a reference to NMEA 0183 and by four examples. It recommends five types to receivers. | unstated | none | Working choice: the tokenizer checks the format only. It gives no finding for any talker or type. |
| <a id="amb.nmea.checksum"></a>`amb.nmea.checksum` | p. 52/34 | Three examples contain a checksum, and one has none. APRS12c does not specify the case of the hex digits. | ambiguous | 3, 2 | Missing: no finding. Present: the tokenizer compares it, and a mismatch gives `value` (README section 3.2). Lower-case digits: `unstated`, and the tokenizer still compares them. |
| <a id="amb.nmea.end"></a>`amb.nmea.end` | p. 42/26, p. 52/34 | NMEA 0183 ends a sentence with CR LF. The examples show none. APRS12c does not address bytes after the checksum. | conflict | 5, 3; none | CR LF at the end: `nmea.end`, no finding (rules 5, 3). Working choice: other bytes after the checksum are residue with `syntax`, as for [amb.df.agrelo](#amb.df.agrelo). |

## 8. Reviewed exceptions

None.

## 9. Open items

- A pinned text of NMEA 0183 and of the Maidenhead letter ranges (README
  rule 5). Until then, the NMEA framing and the letter ranges are the
  general ones. These files use them as recalled, not as read from a
  pinned text.
