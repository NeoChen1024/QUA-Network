# Mic-E

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` chapter 10, p. 60/42 to p. 74/56, in submodule `3rdparty/aprsspec`, commit `5830d42f`. Conventions, tokenizer model and decoder commits: [README](README.md). |

## 1. Scope

This file reads APRS12c chapter 10: how a packet is recognised as Mic-E,
the six bytes and the SSID of the destination address, the eight bytes
that follow the data type identifier, and the status text after them.

Items that the status text shares with other comments are owned
elsewhere: data extensions and comment items in
[02-fields.md](02-fields.md), base-91 comment telemetry
[`tlm.b91`](07-telemetry.md#tlm.b91) in [07-telemetry.md](07-telemetry.md),
frequencies (`freq.*`) in
[09-other.md](09-other.md#7-frequency-specification). The destination
address as a TNC2 field (where it ends, how its SSID is written) belongs
to [01-frame.md](01-frame.md); this file reads its content once the data
type identifier says Mic-E.

Offsets in this file count from the first byte of the information field,
which is offset 0. Destination bytes are numbered 1 to 6.

## 2. Recognition

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.dti"></a>`mice.dti` | Data type identifier | 0x60 (current data) or 0x27 (old data). 0x1C and 0x1D are the Rev 0 beta forms and give an `obsolete` finding. | Required | 1 byte | p. 31/17, p. 64/46 |
| <a id="mice.fixed"></a>`mice.fixed` | Fixed part | Offsets 1 to 8, section 4. An information field shorter than 9 bytes gives a `syntax` finding here. | Required | 8 bytes | p. 64/46, p. 65/47 |

The token of byte 0 carries `mice.dti`, so that the tokens show the
packet as Mic-E ([README section 3](README.md#3-tokenizer-model)).

**[proposed]** The data type identifier alone makes a packet Mic-E
([amb.mice.recognition](#amb.mice.recognition)). A destination that does not
fit section 3 gives `syntax` findings on the destination rules; the
information field is tokenised all the same. A destination of Mic-E shape
under any other data type identifier is not Mic-E; its class is decided by
[01-frame.md](01-frame.md).

The symbol code comes before the symbol table identifier in Mic-E, the
reverse of the other position formats (p. 64/46).

0x60 and 0x27 mark current and old data, but the TM-D700 sends 0x27 for
current data (p. 32/18, p. 64/46). The tokenizer gives no finding for
either and does not use the difference.

## 3. Destination address

The destination callsign of a Mic-E packet is six bytes. Each byte holds
one latitude digit, or a blank for position ambiguity, together with one
flag. Bytes 1 to 3 carry the position comment bits A, B and C; byte 4 the
latitude hemisphere; byte 5 the longitude offset; byte 6 the longitude
hemisphere (p. 61/43, p. 62/44).

Meaning of each byte value, in this project's arrangement:

| Byte | Digit | Flag in bytes 1 to 3 | Flag in bytes 4, 5, 6 |
|---|---|---|---|
| `'0'`–`'9'` | byte − 0x30 | 0 | South, +0, East |
| `'A'`–`'J'` | byte − 0x41 | custom 1 | not allowed |
| `'K'` | blank | custom 1 | not allowed |
| `'L'` | blank | 0 | South, +0, East |
| `'P'`–`'Y'` | byte − 0x50 | standard 1 | North, +100, West |
| `'Z'` | blank | standard 1 | North, +100, West |

Any other byte, including `'M'` to `'O'` and lower-case letters, gives a
`syntax` finding on the rule for its position
([amb.mice.dest](#amb.mice.dest)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.dest"></a>`mice.dest` | Destination callsign | Exactly 6 bytes, each from the set of its position below. The parts are tokens one level deeper. | Required | 6 bytes, then the SSID or the end of the address ([01-frame.md](01-frame.md)) | p. 61/43, p. 62/44 |
| <a id="mice.dest.a"></a>`mice.dest.a` | Byte 1: tens of latitude degrees, bit A | Set of bytes 1 to 3. A blank gives a `syntax` finding. | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.b"></a>`mice.dest.b` | Byte 2: units of latitude degrees, bit B | Set of bytes 1 to 3. A blank gives a `syntax` finding. | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.c"></a>`mice.dest.c` | Byte 3: tens of minutes, bit C | Set of bytes 1 to 3. | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.ns"></a>`mice.dest.ns` | Byte 4: units of minutes, North or South | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.lonoff"></a>`mice.dest.lonoff` | Byte 5: tenths of minutes, longitude offset | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44, p. 65/47 |
| <a id="mice.dest.we"></a>`mice.dest.we` | Byte 6: hundredths of minutes, East or West | `'0'`–`'9'`, `'L'`, `'P'`–`'Z'` | Required | 1 byte | p. 62/44 |
| <a id="mice.dest.ssid"></a>`mice.dest.ssid` | Destination SSID | 0: the digipeater field gives the path. 1 to 15: a generic path code, which gives an `obsolete` finding. | Optional | per [01-frame.md](01-frame.md) | p. 27/17, p. 64/46 |

Checks on the six bytes taken together:

- The digits read as degrees (bytes 1 and 2), minutes (bytes 3 and 4) and
  hundredths (bytes 5 and 6). A value outside the range of
  [`lat`](02-fields.md#lat) gives a `value` finding.
- Blanks stand for position ambiguity as in
  [`lat.amb`](02-fields.md#lat.amb): they replace digits from byte 6
  leftwards, at most four of them, so bytes 1 and 2 never hold one
  (p. 40/24, p. 62/44, p. 71/53). A blank followed by a digit gives a
  `syntax` finding. The same ambiguity applies to the longitude, whose
  bytes are never blanked (p. 71/53, p. 72/54).
- Bits A, B and C all 0 is the emergency comment; standard ones only give
  M0 to M6, custom ones only give C0 to C6 (p. 63/45). **[proposed]** A
  mixture of standard and custom ones gives a `value` finding: the
  document calls the result unknown, and no comment type has that code
  ([amb.mice.dest](#amb.mice.dest)).

## 4. Information field

Offsets 1 to 6 carry the longitude, speed and course, each byte offset by
28 (0x1C) (p. 64/46). Every byte outside 0x1C–0x7F gives a `syntax`
finding. A byte inside that range that the document's encoding tables do
not use gives a `value` finding ([amb.mice.offtable](#amb.mice.offtable)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.lon.deg"></a>`mice.lon.deg` | Longitude degrees, d+28 | Used: 0x26–0x7F. Offset +0 (byte 5): 0x26–0x7F are 10° to 99°. Offset +100: 0x76–0x7F are 0° to 9°, 0x6C–0x75 are 100° to 109°, 0x26–0x6B are 110° to 179°. 0x1C–0x25 give a `value` finding. | Required | 1 byte | p. 65/47, p. 66/48 |
| <a id="mice.lon.min"></a>`mice.lon.min` | Longitude minutes, m+28 | Used: 0x58–0x61 are 0 to 9 minutes, 0x26–0x57 are 10 to 59. 0x1C–0x25 and 0x62–0x7F give a `value` finding. | Required | 1 byte | p. 66/48, p. 67/49 |
| <a id="mice.lon.hun"></a>`mice.lon.hun` | Longitude hundredths of minutes, h+28 | 0x1C–0x7F; byte − 0x1C is 0 to 99. | Required | 1 byte | p. 67/49 |
| <a id="mice.sp"></a>`mice.sp` | Speed, hundreds and tens of knots, SP+28 | 0x1C–0x7F. 0x30–0x6B are 20 to 79 tens of knots. 0x1C–0x2F and 0x6C–0x7F are two codings of 0 to 19 tens. | Required | 1 byte | p. 67/49, p. 68/50 |
| <a id="mice.dc"></a>`mice.dc` | Speed units and course hundreds, DC+28 | With n = byte − 0x1C: n div 10 is the units of knots, (n mod 10) mod 4 the hundreds of degrees. n mod 10 of 0–3 and of 4–7 are two codings of the same value. Used: 0x1C–0x7D with n mod 10 at most 7. n mod 10 of 8 or 9 gives a `value` finding. | Required | 1 byte | p. 69/51, p. 70/52 |
| <a id="mice.se"></a>`mice.se` | Course tens and units, SE+28 | 0x1C–0x7F; byte − 0x1C is 0 to 99. | Required | 1 byte | p. 70/52 |
| <a id="mice.sym.code"></a>`mice.sym.code` | Symbol code | As [`sym.code`](02-fields.md#sym.code). | Required | 1 byte | p. 64/46, p. 71/53 |
| <a id="mice.sym.table"></a>`mice.sym.table` | Symbol table identifier | As [`sym.table`](02-fields.md#sym.table) in an uncompressed position ([amb.mice.symtable](#amb.mice.symtable)). | Required | 1 byte | p. 64/46 |

The course is 100 × ((n mod 10) mod 4) of `mice.dc` plus the value of
`mice.se`. 0 means unknown and 360 north (p. 67/49). A course from 361
to 399 can be coded and gives a `value` finding. Any speed the three bytes
can code lies in 0 to 799 knots, the stated range, so speed needs no
check.

**[proposed]** Either coding of `mice.sp` and of `mice.dc` is accepted in
any combination, with no finding ([amb.mice.scheme](#amb.mice.scheme)).

## 5. Status text

Everything from offset 9 to the end of the information field is the
status text (p. 72/54). APRS12c places its parts as follows, all of them
optional; the order is this file's reading where the document does not
fix it:

```
offset 9                                                         end
[prefix] [altitude] [locator] [extension] text [telemetry] [DAO] [suffix]
```

The obsolete Mic-E telemetry takes the place of the prefix
([amb.mice.byte9](#amb.mice.byte9)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="mice.status"></a>`mice.status` | Status text | Offset 9 to the end. Free text is [`cmt.text`](02-fields.md#cmt.text). No length limit is stated. The parts below are tokens one level deeper. | Optional | End of information field | p. 72/54 |
| <a id="mice.tlm"></a>`mice.tlm` | Obsolete telemetry | 0x1D at offset 9, then 5 bytes of any value. Gives an `obsolete` finding. **[proposed]** Bytes after it are read as status text with an `unstated` finding. | Optional | 6 bytes | p. 72/54, p. 157/133 |
| <a id="mice.type.prefix"></a>`mice.type.prefix` | Device type prefix | One byte at offset 9: `'>'` (Kenwood handheld), `']'` (Kenwood mobile), 0x60 (other maker, messaging capable) or 0x27 (other maker, not messaging capable). | Optional | 1 byte | p. 73/55 |
| <a id="mice.alt"></a>`mice.alt` | Altitude | Three [`b91.digit`](02-fields.md#b91.digit) bytes, then `'}'`. Value minus 10000 is metres. **[proposed]** Only directly after the prefix, or at offset 9 when there is none ([amb.mice.alt](#amb.mice.alt)). | Optional | The `'}'` | p. 74/56, p. 153/129, p. 154/130 |
| <a id="mice.grid"></a>`mice.grid` | Maidenhead locator | [`grid.loc`](03-position.md#grid.loc): two letters `'A'`–`'R'`, two digits, optionally two letters `'A'`–`'X'` ([amb.grid.range](03-position.md#amb.grid.range)); then `'/'` `'G'`; then SP when free text follows, which belongs to this token. Lower-case letters give a `syntax` finding. **[proposed]** After the prefix and any altitude ([amb.mice.grid](#amb.mice.grid)). | Optional | The `'G'`, or the SP after it | p. 42/26, p. 73/55, p. 152/128 |
| <a id="mice.type.suffix"></a>`mice.type.suffix` | Device type suffix | **[proposed]** After a `'>'` or `']'` prefix: a last byte `'='`, `'^'` or `'&'`. After a 0x60 or 0x27 prefix: the last two bytes. Raw bytes, nothing stripped first ([amb.mice.suffix](#amb.mice.suffix)). **[agreed]** After a 0x60 or 0x27 prefix, a single byte left where the two-byte suffix stands gives a `syntax` finding: a fixed-width field that does not fit ([amb.mice.pipe](#amb.mice.pipe)). | Optional | End of information field | p. 73/55, p. 88/68 |

**[proposed]** Between these parts the status text is read as a position
comment ([amb.mice.extension](#amb.mice.extension)):

- one data extension, [`ext.phg`](02-fields.md#ext.phg),
  [`ext.phgr`](02-fields.md#ext.phgr), [`ext.rng`](02-fields.md#ext.rng)
  or [`ext.dfs`](02-fields.md#ext.dfs), only at the start of the free
  text;
- [`cmt.alt`](02-fields.md#cmt.alt), [`cmt.dao`](02-fields.md#cmt.dao)
  and [`cmt.noarchive`](02-fields.md#cmt.noarchive) where their own rules
  place them;
- a frequency (`freq.*`) at the start of the free text, after any data
  extension, as
  [09-other.md section 7](09-other.md#7-frequency-specification)
  places it;
- [`tlm.b91`](07-telemetry.md#tlm.b91), searched for only in the bytes
  before the suffix ([amb.mice.pipe](#amb.mice.pipe)).

A standard APRS position inside the status text, which p. 72/54 says
overrides the encoded one, is not read as a position; its bytes are free
text with an `ambiguous` finding when they would be accepted as a
position ([amb.mice.extension](#amb.mice.extension)).

## 6. APRS-IS transport

Offsets 1 to 6 can hold 0x1C–0x1F and 0x7F, and the obsolete telemetry
any byte. The document asks that Mic-E data be converted for networks that
do not keep binary data intact and converted back on return to RF, and
gives no method (p. 74/56).

**[proposed]** The tokenizer reads a Mic-E packet taken from APRS-IS
exactly as one taken from RF: raw bytes, with no escape form recognised
([amb.mice.transport](#amb.mice.transport)). Bytes that a TNC2 line cannot
carry at all are a matter for [01-frame.md](01-frame.md).

## 7. Ambiguities

Decoder behaviour below was read in the source at the commits listed in
the [README](README.md#4-decoders-consulted), not run.

<a id="amb.mice.recognition"></a>
### amb.mice.recognition

- **Open.** The identifier table assigns 0x60 and 0x27 to Mic-E data
  (p. 31/17). Chapter 10 does not say what a receiver does with a Mic-E
  identifier and a destination that cannot be decoded (p. 60/42 to
  p. 64/46).
- **Readings.** (a) The identifier decides; a bad destination is an error
  in a Mic-E packet. An earlier draft also listed (b): both the
  identifier and a destination of Mic-E shape are needed, and otherwise
  the packet is not Mic-E. Classing the packet by the shape of its
  destination contradicts the identifier table, which makes these bytes
  Mic-E by themselves, so by
  [README section 3](README.md#3-tokenizer-model) it is decoder
  behaviour, not a listed reading, and gives no finding. None of the
  decoders read classes such a packet as another format: each decodes it
  as Mic-E or refuses it (table below).
- **Reading taken.** **[proposed]** (a), as every decoder read does it.
  The destination is checked by section 3, and bytes that do not fit it
  give `syntax` or `value` on the destination rules. No other reading is
  listed, so the question gives no `ambiguous` finding.
- **Decoders.**

  | Decoder | Reads | Where |
  |---|---|---|
  | FAP | Identifier 0x27 or 0x60 with at least 9 bytes; 0x1C and 0x1D noted as obsolete and not handled. Destination of exactly 6 bytes from the Mic-E set, or an error and no position. The set test ignores case, but a lower-case letter then fails the ambiguity test, so it is refused as well. | `FAP.pm:2580-2586`; `_mice_to_decimal`, `FAP.pm:1637-1647`, `FAP.pm:1686-1704` |
  | Dire Wolf | Identifier 0x27 or 0x60, at least 9 bytes. Destination bytes outside the set print an error; decoding continues with digit 0. | `decode_aprs.c:373-376`; `mic_e_digit`, `decode_aprs.c:1359-1400`; `aprs_mic_e`, `decode_aprs.c:1403-1606` |
  | aprslib | Identifier 0x27 or 0x60. Destination of 6 bytes matching upper-case letters and digits, with `'L'`–`'Z'` in bytes 4 to 6, or an error. `'M'`–`'O'` pass that test but then fail the ambiguity test, so they are refused too. | `__init__.py:188-191`; `parse_mice`, `mice.py:46-51`, `mice.py:65-79` |
  | Xastir | Identifier 0x27 or 0x60, with 0x1C and 0x1D commented out. Destination decoded by bit masks with no set check. | `db.c:15123-15131`; `decode_Mic_E`, `db.c:12313-12424` |
  | aprsc | Identifier 0x27 or 0x60, at least 9 bytes. Destination of exactly 6 bytes from the set, case significant, or the packet is not parsed further. | `parse_aprs.c:1191-1197`; `parse_aprs_mice`, `parse_aprs.c:597-621` |
  | pdn-aprs | Identifiers 0x27, 0x60, 0x1C, 0x1D, the last two with an obsolete note. Destination from the set, or refused. | `decode.rs:30-34`; `mic_e.rs:53-56` |
  | javAPRSlib | Destination of 6 bytes. The set test meant for bytes 1 to 3 is applied to bytes 2 to 4, and the one for bytes 4 to 6 to bytes 5 and 6 only; byte 1 is not tested. | `PositionParser.java:205-221` |
  | aprs-parser-rs | A destination byte outside the set is an error. | `decode_callsign`, `mic_e.rs:375-405` |

- **Corpus question.** Among packets with a Mic-E identifier, how many
  destinations fail section 3, and how? Among packets with another
  identifier, how many destinations would pass it?

<a id="amb.mice.dest"></a>
### amb.mice.dest

- **Open.** The encoding table lists `'0'`–`'9'`, `'A'`–`'L'` and
  `'P'`–`'Z'`, and excludes `'A'`–`'K'` from bytes 4 to 6 (p. 62/44). It
  gives no action for other bytes, for lower case, for blanks that are not
  trailing or that fall in the degrees, or for a mixture of standard and
  custom bits beyond calling it unknown (p. 63/45).
- **Readings.** (a) Strict: such bytes are errors. An earlier draft also
  listed (b), decoding what can be decoded. That gives a byte outside the
  table a value the table does not assign (p. 62/44), reads a blank where
  the ambiguity rule places none (p. 40/24), and gives mixed bits a
  meaning where p. 63/45 calls the result unknown. It contradicts those
  statements, so by [README section 3](README.md#3-tokenizer-model) it
  is decoder behaviour (Dire Wolf, aprslib, Xastir, aprsc, below), not a
  listed reading, and gives no finding.
- **Reading taken.** **[proposed]** (a). Bytes outside the set of their
  position, lower case included, give `syntax`. Blanks follow
  [`lat.amb`](02-fields.md#lat.amb). Mixed standard and custom bits give
  `value`. Each case is a finding at the byte concerned. No other
  reading is listed, so there is no `ambiguous` finding.
- **Decoders.** FAP: a set test that ignores case, followed by a
  translation that does not, so lower case is refused; blanks trailing and
  at most four (`FAP.pm:1642`, `FAP.pm:1686-1705`); mixed bits are kept as
  a bit string (`FAP.pm:1738-1743`). Dire Wolf: blanks read as digit 0,
  not tracked; mixed bits give an "unknown" type
  (`decode_aprs.c:1359-1400`, `decode_aprs.c:1625-1636`). aprslib: blanks
  trailing, at most four (`mice.py:77-84`, `mice.py:151`); mixed bits are
  looked up in the custom table (`mice.py:118-125`). Xastir: no set or
  blank check; custom bits are not told apart from standard ones
  (`db.c:12313-12424`). aprsc: blank in bytes 1 or 2 refused; blanks
  elsewhere not checked for being trailing (`parse_aprs.c:665-669`).
  pdn-aprs: blanks trailing, none in the degrees; mixed bits unknown
  (`mic_e.rs:58-94`).
- **Corpus question.** For packets with a Mic-E identifier: the byte
  values at each destination position, and the patterns of blanks.

<a id="amb.mice.offtable"></a>
### amb.mice.offtable

- **Open.** The decoding steps accept bytes the encoding tables do not
  use: longitude degrees 0x1C–0x25, minutes 0x1C–0x25 and 0x62–0x7F, and
  DC bytes with remainder 8 or 9. They also produce courses 361 to 399.
  No action is stated (p. 65/47 to p. 70/52).
- **Readings.** (a) Only table values. (b) Whatever the steps decode.
- **Reading taken.** **[proposed]** (a): such bytes give `value`, and
  bytes outside 0x1C–0x7F give `syntax`. Visible in the bytes. Reading
  (b) would decode the bytes that give `value`, but that finding alone
  is given, with no `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence).
- **Decoders.** FAP and aprsc accept degrees 0x26–0x7F, minutes
  0x26–0x61, DC 0x1C–0x7D and the other three bytes 0x1C–0x7F
  (`FAP.pm:1653`; `parse_aprs.c:631-639`); aprslib the same
  (`mice.py:52-53`). Dire Wolf range-checks degrees against the offset
  flag, minutes and hundredths, not speed or course
  (`decode_aprs.c:1495-1575`).
  Xastir refuses only bytes above 0x7F (`db.c:12272-12281`). pdn-aprs:
  degrees 38–127, minutes 38–97, others 28–127; a course above 360 is
  dropped as a tolerated defect (`mic_e.rs:101-151`). None checks the DC
  remainder.
- **Corpus question.** For each of offsets 1 to 6, the bytes outside the
  table values.

<a id="amb.mice.scheme"></a>
### amb.mice.scheme

- **Open.** SP and DC each have two codings of the same value
  (p. 68/50, p. 69/51). Whether one packet may mix them, or a sender must
  keep to one, is not stated.
- **Readings.** (a) Any mixture. (b) One coding per packet.
- **Reading taken.** **[proposed]** (a). The document calls both equally
  valid and its decoding steps handle either.
- **In the bytes.** **[proposed]** Visible, but with no finding under
  the test of [README section 3](README.md#3-tokenizer-model). A packet
  can mix the codings only where `mice.sp` lies in 0x1C–0x2F or
  0x6C–0x7F, the speeds with two codings. Reading (b) would refuse the
  packets whose `mice.sp` and `mice.dc` bytes it takes to be of
  different codings, and a reading that fails does not count; on the
  packets it accepts it gives every byte the value this reading gives
  it. An earlier draft called the question decided by the reading,
  which the README keeps for a question that the bytes cannot narrow;
  these bytes can show a mixture.
- **Decoders.** All read compute speed and course with the same
  arithmetic for both codings (`FAP.pm:1800-1813`;
  `decode_aprs.c:1640-1646`; `mice.py:164-172`; `db.c:12470-12482`;
  `mic_e.rs:133-141`).
- **Corpus question.** Which coding SP and DC use, crossed with the
  device prefix and suffix.

<a id="amb.mice.symtable"></a>
### amb.mice.symtable

- **Open.** Chapter 10 names the symbol table byte but not its set, nor
  whether overlays are `'0'`–`'9'` as in uncompressed positions or
  `'a'`–`'j'` as in compressed ones (p. 64/46, p. 125/101).
- **Readings.** (a) The uncompressed set. (b) The compressed set.
- **Reading taken.** **[proposed]** (a), as all decoders read do it.
  Visible in the bytes. An overlay `'a'`–`'j'`, which reading (b)
  accepts, gets the finding of [`sym.table`](02-fields.md#sym.table)
  alone, with no `ambiguous` beside it
  ([README section 3](README.md#3-tokenizer-model), Precedence). A digit
  overlay, which reading (b) does not accept, gets no finding.
- **Decoders.** `'/'`, `'\'`, `'A'`–`'Z'`, `'0'`–`'9'` in FAP
  (`FAP.pm:1653`), Dire Wolf (`decode_aprs.c:1613-1621`), aprslib
  (`mice.py:52-53`), Xastir (`db.c:12213-12244`) and aprsc
  (`parse_aprs.c:639`); pdn-aprs calls its uncompressed symbol check
  (`mic_e.rs:153`).
- **Corpus question.** Table bytes of Mic-E packets.

<a id="amb.mice.byte9"></a>
### amb.mice.byte9

- **Open.** Offset 9 has overlapping meanings. 0x60 and 0x27 are the
  obsolete telemetry flags and the status text is not to start with
  them (p. 72/54); the next page makes them the prefix of other makers'
  devices (p. 73/55); the release notes call the telemetry deprecated and
  replaced by the type codes (p. 157/133). The obsolete telemetry and the
  status text are presented as alternatives (p. 60/42, p. 64/46).
- **Readings.** (a) 0x60 and 0x27 are always prefixes. (b) They are
  telemetry flags when 4 (after 0x60) or 10 (after 0x27) hexadecimal
  digits follow. (c) Always telemetry flags.
- **Reading taken.** **[proposed]** (a). 0x1D followed by five bytes is
  `mice.tlm`. When the bytes after a 0x60 or 0x27 prefix also match
  reading (b), with hexadecimal digits of either case, the tokenizer
  reports `ambiguous`. Visible in the bytes, as that finding. A SP at
  offset 9, which UAP 2.2.1 attributes to the original Mic-E, is free
  text.
- **In the bytes.** **[proposed]** The `ambiguous` finding is at offset
  9. Under the test of [README section 3](README.md#3-tokenizer-model)
  it is given only where reading (b) would accept the status text: four
  hexadecimal digits follow 0x60, or ten follow 0x27, from offset 10,
  and reading (b), taking the bytes after them as status text with no
  prefix and so no suffix, gives no `syntax` or `value` finding of its
  own. A finding that both readings give on the same bytes does not
  count against (b) and does not suppress the `ambiguous` finding. Where
  this reading reports the bytes that (b) takes as telemetry as `syntax`
  or `value`, such as a lower-case locator from offset 10, that finding
  alone is given (Precedence). An earlier draft also withheld the
  finding wherever this reading reported any byte of the status text.
- **Decoders.**

  | Decoder | Reads | Where |
  |---|---|---|
  | FAP | 0x27 and 4 hexadecimal digits is two telemetry channels, the reverse of p. 72/54, which gives 0x60 for two. The five-channel test is written with the UTF-8 bytes of U+2018 instead of 0x60 (see the note below), so a 0x60 flag never matches it. Prefixes are otherwise left in the comment. | `_mice_to_decimal`, `FAP.pm:1834-1847` |
  | Dire Wolf | No telemetry. Prefix and suffix are matched against its device table. | `aprs_mic_e`, `decode_aprs.c:1696`; `deviceid_decode_mice`, `deviceid.c:678-735` |
  | aprslib | 0x27 and 10, or 0x60 and 4, lower-case hexadecimal digits are telemetry. No prefix handling. | `mice.py:186-197` |
  | Xastir | `'>'` and `']'` are prefixes. 0x1D only turns off its check for bytes above 0x7F. | `db.c:12496-12509`; `db.c:12289` |
  | aprsc | Does not read the status text. | `parse_aprs_mice`, `parse_aprs.c:584` |
  | pdn-aprs | 0x1D and 5 bytes is obsolete telemetry. 0x60, 0x27, `'>'`, `']'` and SP are prefixes. | `mic_e.rs:189-204` |

- **Note.** The PDF text layer gives the 0x60 identifier, minutes code
  and telemetry flag as U+2018 on p. 31/17, p. 32/18, p. 64/46,
  p. 66/48, p. 71/53 and p. 72/54; p. 73/55 has 0x60. The rendered
  glyph is a grave accent (p. 72/54 checked at 110 dpi), and the byte is
  0x60 throughout. The APRS 1.0.1 PDF has the same text layer (pdftotext,
  PDF p. 27, 28, 56, 58, 63 and 64), and 12b has it on the corresponding
  pages. Text copied from the layer carries the wrong character, as
  FAP's five-channel test shows.
- **Corpus question.** The byte at offset 9; after 0x60 or 0x27, how often
  4 or 10 hexadecimal digits follow, and how often an altitude.

<a id="amb.mice.suffix"></a>
### amb.mice.suffix

- **Open.** The suffix is the last one or two bytes, its length depends on
  the prefix, and the list of two-byte suffixes is deferred to an external
  file (p. 73/55). Chapter 13 requires the device code to stand at the
  end of the packet (p. 88/68). A trailing CR or SP, or a run of 0xFF
  before the suffix, breaks that rule (UAP 2.2, UAP 5.10, UAP 5.24,
  UAP 5.26). The Kenwood suffix bytes can also end ordinary text.
- **Readings.** (a) By shape, as in section 5. (b) By the external list.
  An earlier draft also listed (c): (a) or (b) after stripping trailing
  CR, LF and SP. Taking the suffix from bytes that are not the last
  contradicts p. 88/68, so by
  [README section 3](README.md#3-tokenizer-model) it is decoder
  behaviour (Dire Wolf strips one trailing CR, below), not a listed
  reading, and gives no finding.
- **Reading taken.** **[proposed]** (a) on the raw bytes. When a 0x60 or
  0x27 prefix leaves no byte after the prefix and any altitude, there is
  no suffix and the tokenizer reports `unstated`. **[agreed]** When it
  leaves one byte, that byte gives `syntax` on `mice.type.suffix`
  (section 5). **[proposed]** When the two bytes are not one of the
  five examples on p. 73/55, it reports `unstated`, since the document
  gives no list. Trailing CR, LF and SP, and 0xFF runs, are left to
  deviation recognisers. Whether a last `'='`, `'^'` or `'&'` after a
  Kenwood prefix is a suffix or the end of the text is an ambiguity that
  every Kenwood suffix carries and that the bytes of one packet cannot
  narrow; the reading decides it, with no finding
  ([README section 3](README.md#3-tokenizer-model)).
- **In the bytes.** **[proposed]** Reading (b) cannot be applied to the
  bytes until a version of the external list is chosen (section 9), so
  it gives no finding; a pair outside the examples carries `unstated`
  instead. A status text that ends in CR, LF or SP has its suffix taken
  from its last bytes as they stand, with no `ambiguous` finding. An
  earlier draft gave one where reading (c) would have taken the suffix
  from the bytes before such a run.
- **Decoders.** Dire Wolf strips one trailing CR, then matches prefix and
  suffix against its device table; prefix and suffix are removed only
  when an entry matches (`decode_aprs.c:1683-1696`,
  `deviceid.c:696-736`). pdn-aprs drops 0xFF bytes as a tolerated defect,
  then matches against a built-in list (`mic_e.rs:181-208`;
  `mic_e_suffix_len`, `deviceid.rs:119-134`). FAP, aprslib and Xastir have
  no suffix handling; it stays in the comment (`FAP.pm:1869-1874`,
  `mice.py:217-218`, `db.c:12706-12721`).
- **Corpus question.** The last three bytes of the status text, by prefix
  byte; how often the text ends in CR or SP, or holds 0xFF.

<a id="amb.mice.pipe"></a>
### amb.mice.pipe

- **Open.** The Byonics suffixes begin with `'|'`, the delimiter of
  base-91 telemetry, and the telemetry block comes before the suffix
  (p. 73/55, p. 88/68). A trailing `'|'` and one byte can be read either
  way.
- **Readings.** (a) Take the suffix first, then search for telemetry in
  what is left. (b) Pair the `'|'` bytes first.
- **Reading taken.** **[proposed]** (a).
- **In the bytes.** **[proposed]** The readings divide the bytes
  differently only when the bytes between the last `'|'` before the
  suffix and the suffix's own `'|'` fit
  [`tlm.b91`](07-telemetry.md#tlm.b91): pairing the bars first would
  make them a block. In every other case the two readings agree.
  **[agreed]** Reading (b) fails in that case, so no `ambiguous` finding
  is given. A suffix that starts with `'|'` follows a 0x60 or 0x27
  prefix, which calls for a two-byte suffix (section 5); once the block
  has taken the `'|'`, one byte is left where that suffix stands, and
  `mice.type.suffix` gives `syntax` on it. Reading (b) produces that
  finding itself, so under the test of
  [README section 3](README.md#3-tokenizer-model) it does not accept
  the status text. An earlier draft gave an `ambiguous` finding at the
  suffix's `'|'` in that case.
- **Decoders.** Dire Wolf and pdn-aprs remove the suffix before looking
  for telemetry (`decode_aprs.c:1696-1716`; `mic_e.rs:206-208`,
  `mic_e.rs:275`). FAP and aprslib search the whole remainder with a
  pattern, so the result depends on the pattern (`FAP.pm:1859`,
  `FAP.pm:1405`; `mice.py:211`, `telemetry.py:18`).
- **Corpus question.** Mic-E status texts with an odd number of `'|'`, or
  ending in `'|'` and one byte.

<a id="amb.mice.alt"></a>
### amb.mice.alt

- **Open.** The altitude is to be first after the type byte (p. 74/56,
  p. 154/130). A later `xxx}` is not addressed, nor is the order of
  altitude and locator, whose examples also stand first (p. 73/55). The
  name "type byte" is used for the prefix here and for the suffix on
  p. 88/68.
- **Readings.** (a) Only at the start, after any prefix. (b) Anywhere.
- **Reading taken.** **[proposed]** (a). A later match of three base-91
  digits and `'}'` is free text.
- **In the bytes.** **[proposed]** Visible, under the test of
  [README section 3](README.md#3-tokenizer-model), where reading (b)
  would accept the match as the altitude: there is no altitude at the
  start, and the four bytes lie wholly in free text, not inside another
  part of section 5. Such a match gives an `ambiguous` finding at its
  first byte. Reading (b) reads every other byte as this reading does,
  so a `syntax` or `value` finding elsewhere in the status text is
  given by both and does not suppress the `ambiguous` finding. When an
  altitude stands at the start, both readings take that one and a later
  match is text under both, with no finding. An earlier draft gave the
  finding for every later match, and a later one withheld it wherever
  the status text had a `syntax` or `value` finding.
- **Decoders.** Dire Wolf: only at the start of what is left once a
  prefix and suffix found in its device table are removed; with an
  unlisted device the prefix stays and no altitude is read after it
  (`decode_aprs.c:1696-1714`). Xastir: only at the start, after
  `'>'` or `']'` (`db.c:12513-12538`). FAP: the first match anywhere
  (`FAP.pm:1850`). aprslib: the last match anywhere (`mice.py:201`).
  pdn-aprs: at the start; a later one as a tolerated defect
  (`mic_e.rs:210-270`).
- **Corpus question.** The offset of the first altitude-shaped match in
  the status text, relative to the prefix.

<a id="amb.mice.grid"></a>
### amb.mice.grid

- **Open.** Only six-character locators followed by `/G` are shown
  (p. 73/55); p. 42/26 allows four or six characters in general. Case,
  other symbols, and the place of the locator relative to an altitude are
  not stated.
- **Readings.** (a) Four or six characters, then `/G`. (b) Six only.
  (c) Any symbol after the locator.
- **Reading taken.** **[proposed]** (a), after the prefix and any
  altitude. Without `/G` the bytes are free text. Upper case, per the
  rule that locators are sent in upper case (p. 152/128); lower case
  gives `syntax`. Whether a four-character locator is one, which reading
  (b) denies, is carried by every four-character locator and gives no
  finding ([README section 3](README.md#3-tokenizer-model)). Reading (c)
  is visible in the bytes: where a locator is followed by a
  [`sym.table`](02-fields.md#sym.table) byte and a
  [`sym.code`](02-fields.md#sym.code) byte other than `/G`, the bytes
  are free text with an `ambiguous` finding at the first locator byte.
  **[proposed]** Under the test of README section 3 this holds only
  where reading (c) would accept the locator: it stands where
  `mice.grid` may stand, after the prefix and any altitude, its letters
  are upper case, the two symbol bytes give no `syntax` or `value`
  finding of their own, and the symbol is followed by SP, by the end of
  the status text, or by the telemetry, DAO or suffix that section 5
  places after the text. Otherwise (c) fails as well, and the bytes are
  free text with no finding. A `syntax` or `value` finding elsewhere in
  the status text, which reading (c) gives as well, does not suppress
  the `ambiguous` finding. An earlier draft did not state these
  conditions, and a later one also withheld the finding wherever the
  status text had another `syntax` or `value` finding.
- **Decoders.** Of those read, only pdn-aprs looks for a locator in the
  Mic-E status: four or six characters and `/G`, after the altitude, any
  case; text straight after it without a SP is a tolerated defect
  (`mic_e.rs:218-236`;
  `locator_len`, `mic_e.rs:312-325`). Dire Wolf reads locators only in
  status reports (`decode_aprs.c:2447`, `decode_aprs.c:2481`). FAP,
  aprslib and Xastir have no locator code in their Mic-E functions.
- **Corpus question.** Status texts starting, after prefix and altitude,
  with two letters and two digits; what follows them.

<a id="amb.mice.extension"></a>
### amb.mice.extension

- **Open.** The status text may carry any position comment item such as
  PHG, and a standard APRS position that overrides the encoded one; the
  placement of either is not stated, and the editor marks the position
  passage as unclear (p. 72/54, p. 157/133).
- **Readings.** (a) Extensions only at the start of the free text.
  (b) Anywhere. For the position: (c) not looked for; (d) looked for.
- **Reading taken.** **[proposed]** (a) and (c). Visible in the bytes
  where readings (b) or (d) would divide them differently: a later run
  that fits [`ext.phg`](02-fields.md#ext.phg),
  [`ext.phgr`](02-fields.md#ext.phgr), [`ext.rng`](02-fields.md#ext.rng)
  or [`ext.dfs`](02-fields.md#ext.dfs), or a run anywhere in the text
  that fits an uncompressed position ([`lat`](02-fields.md#lat),
  [`sym.table`](02-fields.md#sym.table), [`lon`](02-fields.md#lon),
  [`sym.code`](02-fields.md#sym.code)), is free text with an `ambiguous`
  finding at its first byte. **[proposed]** Under the test of
  [README section 3](README.md#3-tokenizer-model) "fits" means that the
  run matches those rules with no `syntax` or `value` finding of theirs,
  and that it lies wholly in free text, not inside another part of
  section 5 or an item found in the text; otherwise reading (b) or (d)
  fails on it and there is no finding. A `syntax` or `value` finding
  elsewhere in the status text, which (b) or (d) gives as well, does
  not suppress the `ambiguous` finding. An earlier draft did not state
  these conditions, and a later one also withheld the finding wherever
  the status text had another `syntax` or `value` finding.
- **Decoders.** pdn-aprs reads a data extension at the start of the text
  (`mic_e.rs:238-243`). Dire Wolf passes the text to its comment parser,
  which has no PHG rule; PHG is read only by its data extension parser,
  which the Mic-E path does not call (`decode_aprs.c:1712-1716`;
  `process_comment`, `decode_aprs.c:4391`; `decode_aprs.c:4187`). FAP and
  aprslib read altitude, telemetry and DAO
  only (`FAP.pm:1830-1875`; `mice.py:184-218`). None of those read looks
  for a position in the status text.
- **Corpus question.** Status texts whose free text starts with `PHG`,
  `RNG` or `DFS`; texts holding a latitude and longitude pattern.

<a id="amb.mice.transport"></a>
### amb.mice.transport

- **Open.** The conversion for networks that do not keep binary data is
  required but not given (p. 74/56). A non-printing byte replaced by SP
  cannot be detected, because SP is a valid value of `mice.lon.hun`,
  `mice.sp`, `mice.dc` and `mice.se`.
- **Readings.** (a) Raw bytes on APRS-IS. (b) Some escape form.
- **Reading taken.** **[proposed]** (a).
- **In the bytes.** **[proposed]** Decided by the reading, with no
  finding ([README section 3](README.md#3-tokenizer-model)). Reading (b)
  names no escape form, so it divides no packet's bytes differently,
  and a byte replaced on the way is not visible: the question is
  carried by every Mic-E packet, and its bytes cannot narrow it.
- **Decoders.** aprsc, an APRS-IS server, checks the raw byte ranges
  including 0x1C–0x1F and 0x7F (`parse_aprs.c:631-639`). FAP has an
  option that repairs one known corruption, where non-printing bytes were
  replaced by spaces and then collapsed (`FAP.pm:1653-1679`).
- **Corpus question.** Mic-E information fields from APRS-IS holding
  0x1C–0x1F or 0x7F, against those holding SP at the same offsets.

## 8. Errata

<a id="err.mice.example"></a>
### err.mice.example

The worked example on p. 71/53 subtracts 80 from the SP byte less 28,
and 4 from the DC remainder. The steps on p. 70/52 subtract 800 from the
speed and 400 from the course. Both give 20 knots and 251° for the
example, but subtracting 4 fails for the DC coding whose remainders are
0 to 3. The reading follows p. 70/52.

Origin: already in APRS 1.0.1, with the steps on PDF p. 62 (printed 52)
and the worked example on PDF p. 63 (printed 53). 12b has it.

<a id="err.mice.sptable"></a>
### err.mice.sptable

The SP table on p. 68/50 labels the codes 0x3A and 0x3B as 300–310 and
310–320 knots. Every other row covers ten knots, and the decoding steps
give 300–309 and 310–319. The reading follows the decoding steps.

Origin: already in APRS 1.0.1, in the SP table on PDF p. 60 (printed 50).
12b has it.

<a id="err.mice.setable"></a>
### err.mice.setable

The SE table on p. 70/52 heads its byte column `m+28` and its second half
"Long Mins", headings of the minutes table. The rows are course tens and
units. The reading follows the rows and the text.

Origin: already in APRS 1.0.1, PDF p. 62 (printed 52). 12b has it.

<a id="err.mice.status"></a>
### err.mice.status

p. 72/54 says the status text is not to start with 0x60 or 0x27; p. 73/55
gives those bytes as the required prefix of other makers' devices. The
reading follows p. 73/55 and the release note on p. 157/133
([amb.mice.byte9](#amb.mice.byte9)).

Origin: a merge of APRS 1.0.1 text with a later addendum. The
prohibition and the telemetry flags are 1.0.1 text, PDF p. 64 (printed
54), written when only the Kenwood `'>'` and `']'` codes existed (PDF
p. 65). The 0x60 and 0x27 prefixes come from the Mic-E type codes of the
APRS 1.2 addendum, which the release history on p. 157/133 lists. The
compilation marked the telemetry obsolete but kept the prohibition. 12b
already has both.

<a id="err.mice.binary"></a>
### err.mice.binary

p. 64/46 says the information field never uses full 8-bit binary values,
since all are offset by 28; the 0x1D telemetry on p. 72/54 carries five
raw 8-bit values. The reading allows any byte in `mice.tlm` only.

Origin: already in APRS 1.0.1, PDF p. 56 and p. 64 (printed 46 and 54).
12b and 12c only add the obsolete mark to the telemetry. 12b has it.

## 9. Open items

- APRS12c defers the list of device suffixes to the aprs-deviceid
  repository. Whether the tokenizer reads that list, and at which version,
  is open; until then `mice.type.suffix` is read by shape only.
- The corpus questions in section 7.
- ebarkie/aprs has no Mic-E decoder in the files read, and javAPRSlib's
  handling of the status text has not been read.
