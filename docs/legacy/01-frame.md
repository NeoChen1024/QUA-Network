# Frame, addresses and data type

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |

## 1. Scope

This file reads the parts of a packet that come before any format: the
TNC2 monitor line as APRS-IS carries it, the source, destination and path
addresses, the classes a destination address falls into, the meaning of
the destination and source SSIDs, the data type identifier and the
dispatch it drives, and third-party payloads.

The input is one line without its record terminator. APRS12c defines the
binary AX.25 UI frame (p. 22/12) and, for third-party traffic only, the
TNC-2 text of an address header (p. 107/83, p. 108/84). The text form of
an ordinary packet is described in UAP §1. Frame fields that the text form
does not show (flags, control 0x03, PID 0xF0, FCS, the C and H bits) are
not tokenized. The no-archive marker, which p. 110/86 lets appear
anywhere in a packet, is read by
[`cmt.noarchive`](02-fields.md#cmt.noarchive).

Conventions, finding kinds and verdicts are those of the
[README](README.md). Rule IDs in this file use the prefixes `line`,
`addr`, `path`, `dest`, `src`, `dti` and `tp`.

## 2. The line

The line is: source address, `>`, destination address, zero or more
path entries each introduced by `,`, then `:`, then the information
field.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="line.header"></a>`line.header` | Address header | The span from the first byte of the line to the byte before `line.sep`. Contains `addr.src`, `line.gt`, `addr.dest` and the path (section 4). Not a token itself; the tokens inside it are. | yes | `line.sep` ([amb.line.split](#amb.line.split)) | p. 107/83; UAP §1 |
| <a id="line.gt"></a>`line.gt` | Source terminator | `>`, 1 byte. | yes | 1 byte | p. 107/83; UAP §1 |
| <a id="line.sep"></a>`line.sep` | Header terminator | `:`, 1 byte: the first `:` in the line. A line with no `:` gives `syntax` and verdict `unknown-format`. | yes | 1 byte | p. 107/83; UAP §1 |
| <a id="line.info"></a>`line.info` | Information field | Any byte values 0x00–0xFF, 1 to 256 bytes. An empty field gives `syntax`. More than 256 bytes gives `value` at byte 257 ([amb.line.length](#amb.line.length)). Its first byte is `dti` (section 7). | yes | end of line | p. 22/12; p. 23/13 |

## 3. Addresses

An address is written in one of two ways. The AX.25 form is what an RF
frame can carry. Anything else that the line holds in an address position
is read as an address that only APRS-IS can carry.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="addr.src"></a>`addr.src` | Source address | `addr.call` with optional `addr.ssid`, or `addr.is`. A `*` after it gives `syntax`. | yes | `line.gt` | p. 22/12; p. 107/83; UAP §1.1 |
| <a id="addr.dest"></a>`addr.dest` | Destination address | `addr.call` with optional `addr.ssid`, or `addr.is`. Empty gives `syntax`. A `*` after it gives `syntax`. Its class is given by section 5. | yes | `,` or `line.sep` | p. 22/12; p. 25/13; UAP §1.2 |
| <a id="addr.call"></a>`addr.call` | Callsign, AX.25 form | 1 to 6 bytes, each `A`–`Z` or a digit. | yes, in the AX.25 form | `-`, `*`, `,`, `>` or `:` | p. 22/12; p. 107/83; UAP §1 |
| <a id="addr.ssid"></a>`addr.ssid` | SSID, AX.25 form | `-` then `1`–`9`, or `1` followed by `0`–`5`. SSID 0 is written by leaving the suffix out. **[agreed]** After an `addr.call`, the suffix `-0`, or `-0` and one more digit (`N0CALL-0`, `N0CALL-01`), is a wrong text form of an address that AX.25 can carry: this rule gives `syntax`, and the address is not `addr.is`. Two digits above 15 give `value` ([amb.addr.form](#amb.addr.form)). | no | `*`, `,`, `>` or `:` | p. 107/83; UAP §1.1 |
| <a id="addr.is"></a>`addr.is` | Address only APRS-IS can carry | Not in the AX.25 form and not an `addr.call` with a suffix that `addr.ssid` reports, but 1 to 9 bytes, each 0x21–0x7E other than `>`, `,`, `:` and `*`. One token for the whole address; gives `is-only`. Anything else in an address position gives `syntax` ([amb.addr.form](#amb.addr.form)). | — | as the position it is in | p. 108/84; UAP ch. 4 |

## 4. The path

The path is the list of entries after the destination. APRS12c allows 0
to 8 digipeater addresses (p. 22/12, p. 107/83). On APRS-IS the servers
append a q-construct and the name of the entry point after the RF path
(UAP ch. 4); APRS12c names the q-construct only once and refers the reader
to the APRS-IS documentation (p. 155/131). Those entries are classified,
not rejected.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="path.sep"></a>`path.sep` | Entry separator | `,`, 1 byte, before each entry. Two adjacent separators, or one directly before `line.sep`, leave an empty entry: `syntax`. **[proposed]** An empty entry does not count toward the limit of 8. | per entry | 1 byte | p. 107/83; UAP §5.6 |
| <a id="path.digi"></a>`path.digi` | Digipeater entry | `addr.call` with optional `addr.ssid`, or `addr.is`, then optional `path.used`. Every entry before `path.q`, or every entry if there is none. More than 8 gives `value` at the ninth. | no | `,` or `line.sep` | p. 22/12; p. 107/83 |
| <a id="path.used"></a>`path.used` | Used marker | `*` directly after the address of a `path.digi`. It marks the entry heard; all entries before it count as used. A second `*` among the `path.digi` entries gives `syntax` ([amb.path.used](#amb.path.used)). | no | 1 byte | p. 107/83; p. 20/10; UAP §1.3.1 |
| <a id="path.obsolete"></a>`path.obsolete` | Obsolete alias | A `path.digi` whose callsign is exactly `RELAY`, `TRACE` or `WIDE` (no digit), with any SSID. Gives `obsolete`. | no | — | p. 20/10; p. 155/131; UAP §5.5 |
| <a id="path.nogate"></a>`path.nogate` | Gating block | A `path.digi` whose callsign is `NOGATE` or `RFONLY`. Classified; no finding, wherever it stands. | no | — | p. 110/86 |
| <a id="path.q"></a>`path.q` | q-construct | `q`, `A`, then one byte `A`–`Z` or `a`–`z`, as a whole entry, no `*`. The first such entry. **[proposed]** An entry `qA?*` is not `path.q`; before the first q-construct it is read as `path.digi`. Gives `is-only` ([amb.path.q](#amb.path.q)). | no | `,` or `line.sep` | p. 155/131; UAP ch. 4 |
| <a id="path.is"></a>`path.is` | Entry after the q-construct | 1 or more bytes, each 0x21–0x7E other than `,` and `:`. AX.25 form gives no finding; anything else gives `is-only`. **[proposed]** The text-form SSID rules of `addr.ssid` are not applied here: `N0CALL-0` is simply not in the AX.25 form. A trailing `*` gives `unstated`. | no | `,` or `line.sep` | UAP ch. 4 |

## 5. Destination classes

APRS12c lists six uses of the destination address (p. 25/13) and does not
say how to choose between them when an address fits more than one. The
reading takes them in this order **[proposed]**
([amb.dest.class](#amb.dest.class)); the first that matches is the class,
and the class is a depth-1 token inside `addr.dest` **[proposed]** that
covers the callsign; a [`dest.ssid`](#dest.ssid) token follows it when
there is an SSID:

1. `dest.mice` when the data type identifier is a Mic-E one (0x1C, 0x1D,
   `'` or `` ` ``), whatever the address holds.
2. `dest.aprs`.
3. `dest.tocall`.
4. `dest.symnn`.
5. `dest.sym`.
6. `dest.generic`.
7. `dest.grid`.
8. `dest.altnet`.

A destination that takes class 3 or 6 and also matches `dest.grid` gives
`ambiguous` at the first byte of `addr.dest`
([amb.dest.class](#amb.dest.class)). **[proposed]** So does a
destination of any class other than `dest.mice` whose six bytes are two
upper-case letters, two digits and two upper-case letters and fit
`dest.grid` only with a letter outside the Maidenhead ranges
([amb.grid.range](03-position.md#amb.grid.range)). **[agreed]** A
locator-shaped destination with lower-case letters, which only APRS-IS
can carry, is not `dest.grid`; it falls to the next class without a
finding of its own. For a third-party packet the outer destination is
classified with the outer data type identifier and the inner one with
the inner identifier.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="dest.mice"></a>`dest.mice` | Mic-E destination | Six bytes and the SSID, read by [04-mic-e.md](04-mic-e.md), including what the SSID means there. | when the identifier is Mic-E | end of the callsign | p. 26/12; ch. 10 |
| <a id="dest.aprs"></a>`dest.aprs` | Obsolete generic | Exactly `APRS`. Gives `obsolete`. | — | end of the callsign | p. 29/19; p. 107/83 |
| <a id="dest.tocall"></a>`dest.tocall` | Software or device identifier | `AP` then 1 to 4 bytes, each `A`–`Z` or a digit. `APZ` + anything is the experimental block. The registry is external and not checked. | — | end of the callsign | p. 25/13; UAP §1.2, §5.3 |
| <a id="dest.symnn"></a>`dest.symnn` | Numbered symbol | `GPSC` (primary table) or `GPSE` (alternate table), then two digits. The number is the symbol code byte minus 0x20, so `01` to `94`; `00` or `95`–`99` gives `value`. No overlay. | — | end of the callsign | p. 27/17; p. 85/65; p. 126/102; p. 139/115 to p. 141/117 |
| <a id="dest.sym"></a>`dest.sym` | Lettered symbol | `GPS`, `SPC` or `SYM`, then the two bytes `xy` of the table below, then an optional overlay `z`: a digit or `A`–`Z`. On RF a missing overlay is a space; the text form shows 5 bytes ([amb.dest.symfill](#amb.dest.symfill)). An overlay on a primary-table `xy` gives `value`. Whether an alternate symbol is overlay-capable is not checked ([amb.sym.overlay](02-fields.md#amb.sym.overlay)). | — | end of the callsign | p. 27/17; p. 85/65; p. 126/102; p. 139/115 to p. 141/117 |
| <a id="dest.generic"></a>`dest.generic` | Generic beacon address | One of the prefixes `ALL`, `AP`, `CQ`, `DF`, `DGPS`, `DRILL`, `DX`, `GPS`, `ID`, `JAVA`, `MAIL`, `MICE`, `QST`, `QTH`, `RTCM`, `SKY`, `SPACE`, `SPC`, `SYM`, `TEL`, `TEST`, `TLM`, `WX`, extended by zero or more bytes `A`–`Z` or digits to at most 6 bytes; or exactly `BEACON`. | — | end of the callsign | p. 29/19 |
| <a id="dest.grid"></a>`dest.grid` | Locator destination | The 6-byte form of [`grid.loc`](03-position.md#grid.loc), upper case only, every letter in its Maidenhead range ([amb.grid.range](03-position.md#amb.grid.range)). Gives `obsolete`. | — | end of the callsign | p. 28/18; p. 42/26 |
| <a id="dest.altnet"></a>`dest.altnet` | Alternate net | Any destination not taken above, including callsigns and digipeater aliases. No finding. | — | end of the callsign | p. 29/19; UAP §5.2 |
| <a id="dest.ssid"></a>`dest.ssid` | Destination SSID | The `addr.ssid` of the destination. Non-zero on any class other than `dest.mice` gives `obsolete` ([amb.dest.ssid](#amb.dest.ssid)). **[proposed]** Not given when `addr.ssid` already reports the suffix (`syntax` or `value`). | no | — | p. 22/12; p. 25/13; p. 27/17; p. 29/19; UAP §1.2.1 |

The two bytes `xy` of `dest.sym`, as given by Appendix 2 (p. 139/115 to
p. 141/117), follow a fixed pattern by symbol code range. The second byte
steps through the listed range in the same order as the symbol code:

| Symbol code | Primary-table `xy` | Alternate-table `xy` |
|---|---|---|
| `!` to `/` (0x21–0x2F) | `B` + (`B` to `P`) | `O` + (`B` to `P`) |
| `0` to `9` | `P` + the same digit | `A` + the same digit |
| `:` to `@` (0x3A–0x40) | `M` + (`R` to `X`) | `N` + (`R` to `X`) |
| `A` to `Z` | `P` + the same letter | `A` + the same letter |
| `[` to `` ` `` (0x5B–0x60) | `H` + (`S` to `X`) | `D` + (`S` to `X`) |
| `a` to `z` | `L` + the same letter in upper case | `S` + the same letter in upper case |
| `{` to `~` (0x7B–0x7E) | `J` + (`1` to `4`) | `Q` + (`1` to `4`) |

A `GPS`, `SPC` or `SYM` destination whose bytes 4 and 5 are not a pair
from this table is `dest.generic`.

## 6. Source SSID

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="src.ssid"></a>`src.ssid` | Source SSID | The `addr.ssid` of `addr.src`, 1 to 15. APRS12c gives each value a fixed primary-table icon for stand-alone trackers that have no other way to send a symbol (p. 127/103); the symbol in the information field comes first, then the destination symbol, then this one. P. 85/65 applies the same two fallbacks, a symbol destination and source SSID 11 for a balloon, to raw and positionless weather stations ([06-weather.md](06-weather.md#1-scope)). The tokenizer records the SSID and reports nothing ([amb.src.ssid](#amb.src.ssid)). | no | — | p. 22/12; p. 29/19; p. 85/65; p. 124/100; p. 127/103; p. 128/104 |

## 7. Data type identifier

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="dti"></a>`dti` | Data type identifier | Byte 0 of `line.info`, and only byte 0 ([amb.dti.offset](#amb.dti.offset)). Selects the format by the table below. The `dti` rules give the dispatch and the findings of the table; the token of byte 0 carries the identifier rule of the most specific format the packet is classified as, such as [`pos.dti`](03-position.md#pos.dti), [`wx.pos`](06-weather.md#wx.pos) or [`tp.dti`](#tp.dti), listed below the table ([README section 3](README.md#3-tokenizer-model)). | yes | 1 byte | p. 23/13; p. 31/17; p. 154/130 |
| <a id="dti.unknown"></a>`dti.unknown` | Undispatched field | The whole of `line.info` when the identifier selects no format and neither obsolete form below the table matches. Verdict `unknown-format`; the finding is given in the table below ([amb.dti.undefined](#amb.dti.undefined)). **[proposed]** This holds inside a third-party payload too: the data type of the packet cannot be determined. | — | end of `line.info` | p. 31/17; p. 123/99 |

The dispatch, by byte value of `dti`. "Class" is the document's own
category; "Read in" is where the rest of the field is tokenized, and
where the identifier rule that the byte-0 token carries is defined.
"Finding at `dti`" is the finding the `dti` rules give at byte 0.

| Byte | Class | Read in | Finding at `dti` |
|---|---|---|---|
| 0x00–0x1B | not listed | `dti.unknown` | `unstated` |
| 0x1C, 0x1D | Mic-E, Rev 0 beta units | [04-mic-e.md](04-mic-e.md) | as 04 decides |
| 0x1E–0x20 | not listed | `dti.unknown` | `unstated` |
| `!` | position, no timestamp, no messaging; Ultimeter 2000 when byte 1 is `!` | [03-position.md](03-position.md); [06-weather.md](06-weather.md) for `!!` ([amb.dti.shared](#amb.dti.shared)) | `discouraged` for `!!` (p. 82/62); none otherwise |
| `"`, `(`, `-`, `\`, `]`, `^` | unused | `dti.unknown` | `unstated` |
| `#`, `*` | Peet Bros U-II weather station | [06-weather.md](06-weather.md) | `discouraged` (p. 82/62) |
| `$` | raw GPS (NMEA); Ultimeter 2000 when the field starts `$ULTW` | [03-position.md](03-position.md); [06-weather.md](06-weather.md) for `$ULTW` ([amb.dti.shared](#amb.dti.shared)) | `discouraged` for NMEA (p. 52/34) and for `$ULTW` (p. 82/62) |
| `%` | Agrelo DFJr / MicroFinder | [03-position.md](03-position.md) | none |
| `&`, `+`, `.` | reserved (map feature, shelter data, space weather) | `dti.unknown` | `unstated` |
| `'`, `` ` `` | Mic-E | [04-mic-e.md](04-mic-e.md) | none |
| `)` | item | [05-object-item.md](05-object-item.md) | none |
| `,` | invalid or test data | [09-other.md](09-other.md) | none |
| `/`, `@` | position with timestamp, without and with messaging | [03-position.md](03-position.md) | none |
| `0`–`9`, `A`–`S`, `U`–`Z`, `a`–`z`, `\|`, `~` | do not use | `dti.unknown` | `syntax` |
| `:` | message, bulletin, announcement, directed query, telemetry definition | [08-message.md](08-message.md) | none |
| `;` | object | [05-object-item.md](05-object-item.md) | none |
| `<` | station capabilities | [09-other.md](09-other.md) | none |
| `=` | position, no timestamp, with messaging | [03-position.md](03-position.md) | none |
| `>` | status | [09-other.md](09-other.md) | none |
| `?` | query | [09-other.md](09-other.md) | none |
| `T` | telemetry | [07-telemetry.md](07-telemetry.md) | none |
| `[` | Maidenhead locator beacon | [03-position.md](03-position.md) | `obsolete` |
| `_` | weather report without position | [06-weather.md](06-weather.md) | `discouraged` (p. 83/63) |
| `{` | user-defined | [09-other.md](09-other.md) | none |
| `}` | third-party traffic | section 8 | none |
| 0x7F–0xFF | not listed | `dti.unknown` | `unstated` |

The `discouraged` findings for raw and positionless weather are those of
[06-weather.md section 2](06-weather.md#2-recognition), given here at
byte 0.

**[proposed]** The rule carried by the byte-0 token is the identifier
rule of the most specific format the packet is classified as. It is
assigned once classification is complete, so it can depend on bytes
after byte 0: on the symbol code for weather, and on the addressee and
text for a `:` packet. The identifier rules are:

| Byte | Identifier rules |
|---|---|
| 0x1C, 0x1D, `'`, `` ` `` | [`mice.dti`](04-mic-e.md#mice.dti) |
| `!`, `=`, `/`, `@` | [`pos.dti`](03-position.md#pos.dti); [`wx.pos`](06-weather.md#wx.pos) for a weather report; [`wx.raw.ultlog.dti`](06-weather.md#wx.raw.ultlog.dti) for `!!` |
| `#`, `*` | [`wx.raw.peet`](06-weather.md#wx.raw.peet) |
| `$` | [`nmea.dti`](03-position.md#nmea.dti); [`wx.raw.ultpkt.dti`](06-weather.md#wx.raw.ultpkt.dti) for `$ULTW` |
| `%` | [`df.agrelo.dti`](03-position.md#df.agrelo.dti) |
| `)` | [`item.dti`](05-object-item.md#item.dti) |
| `,` | [`inv.dti`](09-other.md#inv.dti) |
| `:` | [`msg.dti`](08-message.md#msg.dti) for messages, acknowledgements and rejections; [`bln.dti`](08-message.md#bln.dti); [`nws.dti`](08-message.md#nws.dti); [`tlm.def.dti`](07-telemetry.md#tlm.def.dti); [`qry.dir.dti`](09-other.md#qry.dir.dti) ([08 section 2.1](08-message.md#21-kind-of-packet)) |
| `;` | [`obj.dti`](05-object-item.md#obj.dti); [`wx.obj`](06-weather.md#wx.obj) for a weather report |
| `<` | [`cap.dti`](09-other.md#cap.dti) |
| `>` | [`stat.dti`](09-other.md#stat.dti) |
| `?` | [`qry.dti`](09-other.md#qry.dti) |
| `T` | [`tlm.dti`](07-telemetry.md#tlm.dti) |
| `[` | [`grid.dti`](03-position.md#grid.dti) |
| `_` | [`wx.pl`](06-weather.md#wx.pl) |
| `{` | [`udf.dti`](09-other.md#udf.dti) |
| `}` | [`tp.dti`](#tp.dti) |

A field read as `dti.unknown` has no identifier rule.

Packets that fit no format are, per p. 123/99, non-APRS beacons that a
program can show as status. The tokenizer does not: they stay
`dti.unknown` **[proposed]** ([amb.dti.undefined](#amb.dti.undefined)).

An assigned identifier is a byte whose row in the dispatch table names
a file to read it. Every other byte, whether not listed, unused,
reserved or "do not use", is not assigned. **[agreed]** Before a field
whose byte 0 is not assigned becomes `dti.unknown`, two obsolete forms
without an identifier are tried, in this order: the object of
[`obj.obsolete`](05-object-item.md#obj.obsolete), then the bulletin of
[`bln.obsolete`](08-message.md#bln.obsolete). When one matches, the
field is read by that rule, which gives `obsolete`; that finding
replaces the finding of the table above, and the verdict is not
`unknown-format`.

**[proposed]** Token structure. For an obsolete object there is no
identifier byte: the `obj.obsolete` token covers the whole field at
depth 0, and the object field tokens of
[05-object-item section 2](05-object-item.md#2-object-report) lie one
level deeper. For an obsolete bulletin there is no identifier byte
either: the `bln.obsolete` token covers the whole field at depth 0, with
nothing tokenized inside it. An earlier draft said only that byte 0 is
part of the first token of the rule that matched.

## 8. Third-party payloads

A `}` field carries a whole packet from another network: an inner address
header in TNC-2 text, then the original information field unchanged
(p. 107/83 to p. 110/86). The inner header has its own source and
destination, optionally the original path, then the third-party network
identifier and the receiving gateway marked used. The inner information
field is tokenized from `dti` again, one depth level down.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tp.dti"></a>`tp.dti` | Identifier | `}`, 1 byte: the byte-0 token of this field carries `tp.dti`. | yes | 1 byte | p. 31/17; p. 108/84 |
| <a id="tp.src"></a>`tp.src` | Original source | `addr.call` with optional `addr.ssid`; or 1 to 9 bytes, each 0x21–0x7E other than `>`, `:` and `*`, which gives `is-only`. A `*` gives `syntax` ([amb.tp.header](#amb.tp.header)). | yes | `>` | p. 108/84; p. 109/85 |
| <a id="tp.gt"></a>`tp.gt` | Source terminator | `>`, 1 byte. | yes | 1 byte | p. 108/84 |
| <a id="tp.dest"></a>`tp.dest` | Original destination | As `addr.dest`, classified by section 5 with the inner identifier. | yes | `,` | p. 108/84 |
| <a id="tp.path"></a>`tp.path` | Retained original path | Zero or more entries, each `,` then an address as `path.digi`, `path.q` or `path.is`, without `*`. **[proposed]** The token includes the `,`; the entry is read one level below it under the rules of section 4, including the limit of 8 and the obsolete and gating classes, without `path.used`. A `*` here gives `syntax` ([amb.tp.header](#amb.tp.header)). | no | the `,` before `tp.net` | p. 108/84; p. 138/114 |
| <a id="tp.net"></a>`tp.net` | Network identifier | `,` then an address, AX.25 form or `addr.is` (`TCPIP` in the examples), without `*`. | yes | `,` | p. 108/84 |
| <a id="tp.gate"></a>`tp.gate` | Receiving gateway | `,` then `addr.call` with optional `addr.ssid`, then `*`. A missing `*`, or an address not in the AX.25 form, gives `syntax` ([amb.tp.header](#amb.tp.header)). It is the last entry of the inner header. | yes | `tp.sep` | p. 108/84; p. 109/85 |
| <a id="tp.sep"></a>`tp.sep` | Inner header end | `:`, the first `:` after `tp.dti`. | yes | 1 byte | p. 108/84 ([amb.tp.header](#amb.tp.header)) |
| <a id="tp.info"></a>`tp.info` | Original information field | Tokenized from `dti` at depth + 1, under every rule of this directory. An empty field gives `syntax` under this rule. A further `}` is followed ([amb.tp.nest](#amb.tp.nest)). | yes | end of the enclosing field | p. 108/84; p. 110/86 |
| <a id="tp.aea"></a>`tp.aea` | AEA-form inner header | Every address separated by `>` instead of `,`: source, any retained digipeaters, the network identifier, the gateway with `*`, then the original destination, then `:`. Gives `obsolete` ([amb.tp.aea](#amb.tp.aea)). **[proposed]** Recognised when there is no `,`, at least four non-empty addresses, and exactly one `*`, at the end of the second-to-last address. Each address is read one level below; the last is classified as a destination by section 5. | no | `tp.sep` | p. 137/113; p. 138/114 |

## 9. Ambiguities

<a id="amb.line.split"></a>
### amb.line.split

**Open in the document.** APRS12c shows the TNC-2 header only as a
diagram ending in `:` (p. 107/83). It does not say whether a `:` can
occur inside an address, nor what ends the header if it does.

**Readings.** (a) The header ends at the first `:` of the line. (b) It
ends at the first `:` after a well-formed address list.

**Reading taken.** **[proposed]** (a). No address byte set in this file
admits `:`, so on a line whose header (a) accepts, the first `:` is also
the first one after a well-formed address list, and (b) ends the header
at the same byte. The two differ only on lines where (a) already gives
`syntax` in the header, and that finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence). No
`ambiguous` finding.

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| FAP | Splits at the first `:`. | `parseaprs`, FAP.pm:2460 |
| Dire Wolf | Splits at the first `:`, then the source at `>`. | `ax25_from_text`, ax25_pad.c:445, 465 |
| aprslib | Splits at the first `:`. | `parse`, parsing/\_\_init\_\_.py:108 |
| Xastir | Takes the source up to the first `>`, then the path up to the next `:`. | `decode_ax25_line`, db.c:16505–16510 |
| aprsc | Header ends at the first `:`; the `>` is looked for in the first 10 bytes only. | `incoming_parse`, incoming.c:905, 914; `CALLSIGNLEN_MAX`, worker.h:48 |
| javAPRSlib | Source up to the first `>`, header up to the first `:`. | `Parser.parse`, Parser.java:80–90 |
| aprs-parser-rs | Splits at the first `:`, then at `>`. | `decode_textual`, packet.rs:26–37 |
| pdn-aprs | Splits at the first `:`. | `decode_tnc2_line`, packet.rs:231 |

**Corpus question.** How many lines have a `:` before their first `>`?

<a id="amb.line.length"></a>
### amb.line.length

**Open in the document.** The information field is 1 to 256 bytes in the
frame diagram (p. 22/12). Nothing says what a receiver does with a longer
one.

**Readings.** (a) Over 256 bytes is malformed. (b) It is a value beyond a
stated limit. (c) No limit applies on APRS-IS.

**Reading taken.** **[proposed]** (b): `value` at byte 257, as for every
stated length limit in this directory. Visible in the bytes, since (c)
would accept them; the `value` finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).

**Decoders (read).** Xastir drops a field over 256 bytes
(`decode_ax25_line`, db.c:16712). Dire Wolf copies at most 2048 bytes
(`ax25_from_text`, ax25_pad.c:578; `AX25_MAX_INFO_LEN`, ax25_pad.h:36).
FAP and aprslib apply no limit in the functions read (FAP.pm:2445–2776;
parsing/\_\_init\_\_.py:86–155). aprsc's `incoming_parse` checks no
length of the information field (incoming.c:858 on); a limit of 512
bytes on the whole line is defined (`PACKETLEN_MAX`, worker.h:52), but
where it applies to client input was not checked.

**Corpus question.** How many information fields exceed 256 bytes, and
from which sources?

<a id="amb.addr.form"></a>
### amb.addr.form

**Open in the document.** On RF an address is a callsign of one to six
characters, each a capital letter or a digit, and its SSID, 0 to 15, is
shown only when it is not zero (p. 107/83; UAP §1.1). A third-party
source is 1 to 9 printable bytes other than `>` (p. 108/84). UAP ch. 4
says APRS-IS sources and server names need not follow the AX.25 form.
Nothing says which other address positions can hold such names, what
byte set they have, or how `-0`, `-01` or a letter SSID are read.

**Readings.** (a) Every address in the AX.25 form, else `syntax`. (b) The
AX.25 form gives no finding; other names of 1 to 9 visible bytes give
`is-only` in any address position. (c) Relaxed rules only for the source
and after the q-construct; the destination strict.

**Reading taken.** **[proposed]** (b), with the byte set 0x21–0x7E less
the four separators `>` `,` `:` `*`. **[agreed]** An explicit `-0` and
an SSID with a leading zero, such as `N0CALL-0` and `N0CALL-01`, are a
wrong text form of an address that AX.25 can carry, not an address only
APRS-IS can carry: [`addr.ssid`](#addr.ssid) gives `syntax`, and there
is no `is-only` finding. **[proposed]** A numeric SSID over 15 gives
`value`, also from `addr.ssid`. Where another reading would accept
those bytes, the `syntax` or `value` finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).
**[proposed]** The choice of (b) gives no `ambiguous` finding. On an
address in the AX.25 form the three readings agree. On any other
address (a) gives `syntax`, and so does (c) everywhere but the source
and the entries after the q-construct; a reading that fails does not
count (README section 3). Where (c) accepts such an address, it takes
the same bytes as one address that the AX.25 form cannot hold, as (b)
does.

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| FAP | Source: 1–9 of letters, digits, `-`, any case. Destination: AX.25 form, upper case only, `-0` and a leading zero accepted, SSID under 16. Path from APRS-IS: 1–9 of letters, digits, `-`, any case; a 32-digit upper-case hex entry allowed after a q-construct. | `parseaprs`, FAP.pm:2475, 2515, 2551–2562; `check_ax25_call`, FAP.pm:2048 |
| Dire Wolf | Third-party payloads are parsed non-strict: up to 11 letters or digits, any case, and an SSID of up to 2 letters or digits, rejected only when its leading digits read above 15; `-0` accepted. In strict mode, used elsewhere, 6 bytes, upper case and a digit SSID. | `ax25_parse_addr`, ax25_pad.c:782–894; called non-strict at decode_aprs.c:259 |
| aprslib | Source: 1–9 bytes, letters or digits with an optional `-` suffix of letters or digits, any case. Destination: AX.25 form, upper case only, `-0` and a leading zero accepted. Path: 1–9 of letters, digits, `-`, any case, optional `*`. | `parse_header`, parsing/common.py:33–60; `validate_callsign`, common.py:19–30 |
| Xastir | Source: any 1–9 printable bytes (internet names), after a trailing `*` is dropped. Path entries: letters, digits, `-`, at most 9 bytes, at most one `*` each, at most 9 addresses with the destination; a `-0` or `-0n` SSID near the end of the path is rewritten. | `valid_inet_name`, util.c:3520; `valid_path`, util.c:3050–3236; call at db.c:16732 |
| aprsc | Source and destination: at most 9 bytes in all, letters or digits, then optionally `-` and one or more letters or digits. Path: the same, with a trailing `*` allowed and an SSID of 1–2 bytes not starting `0`; a 32-byte entry allowed after the q-construct. | `check_invalid_src_dst`, incoming.c:502; `check_invalid_path_callsign`, incoming.c:606 |
| aprs-parser-rs | No length or byte check on textual addresses beyond valid UTF-8 and a non-empty callsign and SSID; `-0` becomes no SSID. | `Callsign::new`, callsign.rs:21–50; `Callsign::decode_textual`, callsign.rs:70–80 |
| pdn-aprs | 1–9 letters, digits or `-` in every header position. | `Address::is_valid`, packet.rs:28 |
| ebarkie/aprs | AX.25 form only, any case, SSID 0–15 with `-0` accepted; IS-only names fail the frame pattern. | `reFrame`, frame_tnc2.go:16–19 |

**Corpus question.** By position (source, destination, path before and
after the q-construct): how many addresses are not in the AX.25 form, and
of those, how many use bytes other than letters, digits and `-`? How many
SSIDs are written `-0` or with a leading zero?

<a id="amb.path.used"></a>
### amb.path.used

**Open in the document.** APRS12c shows one `*` after the digipeater
heard (p. 107/83). UAP §1.3.1 says there is at most one and that all
earlier entries are implied used; UAP §5.30 shows IGates that mark two
entries and treats it as a fault. APRS12c does not say how to read more
than one.

**Readings.** (a) One `*` at most; a second is malformed. (b) Any number;
the last one marks the station heard.

**Reading taken.** **[proposed]** (a): the second `*` among `path.digi`
entries gives `syntax`. Visible in the bytes, since (b) would accept
them; the `syntax` finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).

**Decoders (read).** FAP keeps a flag per entry and accepts any number
(FAP.pm:2551–2553). Dire Wolf marks all earlier entries used on each `*`
(ax25_pad.c:552–556). aprslib accepts any number (common.py:59).
Xastir rejects two `*` in one entry but not one in each of several
(util.c:3163, 3189–3192). aprs-parser-rs propagates the last `*`
backwards (packet.rs:55–66). pdn-aprs reports more than one as an error
unless tolerated (packet.rs:282–284).

**Corpus question.** How many RF paths carry more than one `*`, and are
the extra ones adjacent?

<a id="amb.path.q"></a>
### amb.path.q

**Open in the document.** The q-construct and server names are not
defined in APRS12c; p. 155/131 only names the q-construct. UAP ch. 4
shows `qAR`, `qAO`, `qAC` followed by an IGate or server name.

**Readings.** (a) Treat `q`-entries as ordinary path entries. (b)
Recognise `q` + `A` + letter as a q-construct, and everything after it
as APRS-IS entries.

**Reading taken.** **[proposed]** (b). The tokenizer does not check the
third byte against a list, since the list is in a document outside the
references. Entries after the q-construct are not counted against the
limit of 8. **[proposed]** Every q-construct carries the question,
whichever entries follow it, and the bytes of one packet cannot narrow
it, so it is decided by the reading
([README section 3](README.md#3-tokenizer-model)): `is-only` is the
only finding, with no `ambiguous` beside it.

**Decoders (read).** FAP notes any 3-byte `q..` entry and then allows a
32-digit hex entry (FAP.pm:2554–2557). aprslib takes the entry after a
`q..` that is second to last as the receiving station (common.py:68–70).
Dire Wolf upper-cases a `qA` entry so that its AX.25 parser accepts it
(ax25_pad.c:533–536). Xastir has no q-construct handling in `valid_path`
and counts it as a hop (util.c:3155–3236). aprsc treats any 3-byte entry
starting `q` as the q-construct (`check_path_calls`, incoming.c:674).
aprs-parser-rs accepts exactly ten q-constructs by name; any other
`q`-entry is read as a callsign (via.rs:12–22, 69–83). pdn-aprs takes
the first entry that is `q`, an upper-case letter, then a letter of
either case, in the outer header only (packet.rs:375–380, 426–429).

**Corpus question.** Which `q`-entries occur, how many paths have more
than one, and how long are the entries that follow them?

<a id="amb.dest.class"></a>
### amb.dest.class

**Open in the document.** The destination uses of p. 25/13 overlap: `AP*`
is a generic address and also covers every software identifier and the
obsolete `APRS`; `GPS*`, `SPC*`, `SYM*` are generic and also the symbol
forms; a six-byte locator can fit other classes; ALTNET is everything
else. No precedence is given.

**Readings.** (a) Choose by data type identifier first (Mic-E), then by a
fixed order of the address forms. (b) Report every class of the address
forms that matches; a destination that the identifier makes Mic-E is
`dest.mice` only.

An earlier draft listed a further reading, choosing by the address
alone, as (b), and let the old (c), now (b), report other classes
beside `dest.mice`. With a Mic-E identifier the destination carries
Mic-E data (p. 26/12, p. 60/42), so classifying it by its shape alone
ignores the selector and contradicts that statement. It is decoder
behaviour, not a reading
([README section 3](README.md#3-tokenizer-model)), and gives no
finding. Which of the decoders read do this was not checked beyond the
statements below.

**Reading taken.** **[proposed]** (a), in the order of section 5: the
more specific form before the wildcard that also covers it, current forms
before the obsolete locator, ALTNET last. When a destination taken as
`dest.tocall` or `dest.generic` also fits `dest.grid`, the tokenizer
gives `ambiguous`; the other overlaps are decided by the order without a
finding.

**In the bytes.** **[proposed]** By the tests of
[README section 3](README.md#3-tokenizer-model):

- With a Mic-E identifier both readings take the destination as
  `dest.mice`. A Mic-E destination that also fits another class gives
  no finding, since only a classification by shape, which is decoder
  behaviour, would read it otherwise.
- Every `APRS`, every `dest.tocall` and every `dest.symnn` or `dest.sym`
  also fits `dest.generic`. Reading (b) would report both classes, but
  every instance of those forms carries the overlap, and the bytes of
  one packet cannot narrow it: decided by the order, no finding.
- A destination taken as `dest.tocall` or `dest.generic` whose six
  bytes also fit the 6-byte form of [`grid.loc`](03-position.md#grid.loc)
  is one the bytes pick out. Read as `dest.grid`, as (b) also reads it,
  it is accepted with only the `obsolete` finding of that class. It
  gets `ambiguous` at the first byte of `addr.dest`.

**Decoders (read).** Dire Wolf looks up the device identifier for every
identifier other than `'` and `` ` `` (decode_aprs.c:325–334), and takes
a destination symbol only when the information field has none
(decode_aprs.c:514–524; `symbols_from_dest_or_src`, symbols.c:572).
aprslib accepts a packet with no known format as a beacon only when the
destination matches its list of generic prefixes, which adds `AIR`,
`ZIP` and `UIDIGI` to the document's list (parsing/\_\_init\_\_.py:141–152).
FAP reads a destination symbol only for NMEA packets and only from
`GPS` and `SPC` addresses (FAP.pm:820–886, 923). Xastir reads a
destination symbol only for NMEA records, from `GPS`, `SPC` and `SYM`
without the numbered forms (`id_callsign`, db.c:2262–2470; calls at
db.c:8458, 8677, 8892).

**Corpus question.** For each destination, which classes of section 5
match? How many destinations of packets with a non-Mic-E identifier fit
the Mic-E or locator patterns?

<a id="amb.dest.ssid"></a>
### amb.dest.ssid

**Open in the document.** A non-zero destination SSID is a generic
digipeater path on p. 22/12 and p. 25/13, reserved for generic
digipeating on p. 29/19, and obsolete with no known implementation on
p. 27/17 (see [err.dest.ssid](#err.dest.ssid)). No receiver action is
given.

**Readings.** (a) Ignore it. (b) Report it as the obsolete path form.
(c) Treat it as malformed.

**Reading taken.** **[proposed]** (b): `obsolete` for any class other
than `dest.mice`. Every non-zero destination SSID carries the question,
and the bytes of one packet cannot narrow it, so it is decided by the
reading ([README section 3](README.md#3-tokenizer-model)); `obsolete`
is the only finding, with no `ambiguous` beside it.

**Decoders (read).** FAP accepts any SSID 0–15 on the destination and
gives it no meaning (FAP.pm:2515; `check_ax25_call`, FAP.pm:2048).
Dire Wolf reads the destination for a warning about `NOGATE` or `RFONLY`
there, for the device identifier, the symbol and Mic-E
(decode_aprs.c:216–223, 287, 332, 1438); no use of the destination SSID
as a path was found in decode_aprs.c, and a comment in digipeater.c
records that the conversion was removed (digipeater.c:885). aprslib
accepts SSID 0–15 and gives it no meaning (common.py:19–30, 56). Xastir:
no use found in `valid_path` or `id_callsign`.

**Corpus question.** How often is the destination SSID non-zero, by
destination class, Mic-E excluded?

<a id="amb.dest.symfill"></a>
### amb.dest.symfill

**Open in the document.** On RF the overlay byte `z` of `GPSxyz` is a
space when there is no overlay, since an AX.25 address has six bytes
(p. 126/102). The text form shows an address without its padding (UAP
§5.29), and the precedence example writes `GPSMV` (p. 127/103).

**Readings.** (a) Five bytes in the text form mean no overlay. (b) Six
bytes are needed.

**Reading taken.** **[proposed]** (a). Under (b) a five-byte `GPSxy`,
`SPCxy` or `SYMxy` would be `dest.generic`, which accepts it, instead of
`dest.sym`. **[proposed]** Every five-byte symbol destination carries
the question, and the bytes of one packet cannot narrow it, so it is
decided by the reading
([README section 3](README.md#3-tokenizer-model)): no `ambiguous`
finding.

**Decoders (read).** FAP accepts 2 or 3 bytes after the prefix
(FAP.pm:826–876). Dire Wolf reads bytes 4 and 5 and takes byte 6 as an
overlay only if it is a digit or upper-case letter (symbols.c:620–668).
Xastir reads up to three bytes after the prefix (db.c:2280–2470).
aprslib does not read destination symbols (no use in parsing/).

**Corpus question.** Length distribution of `GPS`, `SPC` and `SYM`
destinations, and how many of them have bytes 4–5 in the table of
section 5.

<a id="amb.src.ssid"></a>
### amb.src.ssid

**Open in the document.** P. 29/19 says APRS reads a non-zero source
SSID as a display icon, but only for stand-alone trackers (p. 29/19,
p. 124/100). The SSID recommendations on p. 128/104 give the same
numbers unrelated roles (see [err.src.ssid](#err.src.ssid)). A receiver
cannot tell from the bytes which applies.

**Readings.** (a) Apply the icon when the packet has no other symbol.
(b) Apply it only to formats without a symbol field. (c) Never.

**Reading taken.** **[proposed]** The tokenizer reports nothing; the
choice belongs to the decoding layer, which applies the precedence of
p. 127/103. **[proposed]** The three readings tokenize the SSID alike
and differ only in what the decoding layer makes of it, so none divides
or classifies the bytes differently: not visible in the bytes
([README section 3](README.md#3-tokenizer-model)), no finding.

**Decoders (read).** Dire Wolf uses the source SSID only when the
identifier is `$` (symbols.c:693–703). Xastir uses it for NMEA records,
then lets a `GPS`, `SPC` or `SYM` destination override it
(`id_callsign`, db.c:2262–2280). FAP and aprslib do not use it (no use in
FAP.pm or parsing/).

**Corpus question.** How many packets with a non-zero source SSID carry
no symbol in the information field and no symbol destination?

<a id="amb.dti.offset"></a>
### amb.dti.offset

**Open in the document.** The identifier is the first byte of the
information field (p. 23/13). Appendix 7 says a "page 18 X1J exception"
was abandoned in 2012 and the `!` identifier is now only at the start
(p. 154/130), but this edition does not describe the old rule (see
[err.dti.x1j](#err.dti.x1j)). UAP §5.28 shows an IGate that puts bytes
in front of the identifier.

**Readings.** (a) Byte 0 only. This is the one reading of the text.

An earlier draft listed two more, which are decoder behaviour, not
readings ([README section 3](README.md#3-tokenizer-model)): (b) a `!`
found later, within the first 40 bytes, contradicts p. 154/130, which
puts the `!` identifier only at the start; (c) stripping known prefixes
before reading byte 0 contradicts p. 23/13, which makes the first byte
of the field the identifier. In the table below, FAP, aprslib, aprsc
and pdn-aprs search for a later `!`, and Xastir strips a prefix.

**Reading taken.** **[proposed]** (a): no later `!` is looked for and no
prefix is stripped. Such packets are left to a deviation recogniser. No
finding is given beyond the one that byte 0 already gives in the table
of section 7; the decoder behaviour above gives no `ambiguous` finding.

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| FAP | When byte 0 selects nothing, looks for a `!` at offsets 0–39 of the information field and parses a position after it. | `parseaprs`, FAP.pm:2737–2767 |
| Dire Wolf | Byte 0 only; reports an unknown identifier. | `decode_aprs`, decode_aprs.c:178–183, 336–502 |
| aprslib | When byte 0 is not otherwise handled, parses a position after a `!` at offsets 1–40 of the information field. | `_try_toparse_body`, parsing/\_\_init\_\_.py:206–209; `parse_position`, position.py:18–20 |
| Xastir | Byte 0 only, after stripping a `thenet ... ) ` prefix, in any case, left by TNC X-1J4. | `extract_TNC_text`, db.c:15723–15745, called at db.c:16711 |
| aprsc | Looks for a `!` in the first 40 bytes, but then tests the `!` byte itself as the start of the position, so as read this branch yields no position. | `parse_aprs_body`, parse_aprs.c:1308–1326 |
| pdn-aprs | Looks for a `!` in the first 40 bytes, as a tolerated warning. | `not_aprs`, decode.rs:63–79 |

**Corpus question.** Among fields whose byte 0 is not a listed
identifier, how many hold a `!` followed by a valid position within the
first 40 bytes, and at what offsets?

<a id="amb.dti.undefined"></a>
### amb.dti.undefined

**Open in the document.** The table of p. 31/17 marks values unused,
reserved or "do not use", and lists no control byte other than 0x1C and
0x1D, nor space, DEL or bytes from 0x80. It does not say what a receiver
does with any of them. P. 123/99 lets programs treat anything that fits
no format as a status report.

**Readings.** (a) Reject. (b) Unknown format, kept as opaque bytes. (c)
Read as status text.

**Reading taken.** **[proposed]** (b): one `dti.unknown` token, verdict
`unknown-format`, with `syntax` for "do not use" values (a stated
prohibition) and `unstated` for the rest. **[agreed]** Before that
verdict, the two obsolete forms without an identifier are tried, the
object of `obj.obsolete` first and then the bulletin of `bln.obsolete`
(section 7), since p. 80/62 and p. 98/76 describe them. A match gives
`obsolete` in place of the finding at `dti`. Where (c) would accept a
"do not use" field, the `syntax` finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).
**[proposed]** Otherwise no `ambiguous` finding: (a) fails on every
such field and does not count, and (c) would read as status text every
field that reaches `dti.unknown` or an obsolete form. Every such field
carries that question, and the bytes of one packet cannot narrow it, so
it is decided by the reading (README section 3).

**Decoders (read).** FAP returns no result unless the fallback of
[amb.dti.offset](#amb.dti.offset) finds a position; it also accepts a
body starting `DX de` as a DX spot (FAP.pm:2727–2731). Dire Wolf reports
the identifier as unknown (decode_aprs.c:178–183) and decodes the
non-standard `t` and `m` (decode_aprs.c:471–488). aprslib raises
`UnknownFormat` for the unused and reserved values in its table and
accepts other fields as beacons only for generic destinations
(parsing/\_\_init\_\_.py:47–65, 141–152). Xastir stores the field as
status text unless the identifier is `~`, `,`, `&` or `?`
(db.c:15233–15239, 15396–15438). javAPRSlib returns digits, `A`–`S` and
`U`–`Z` with no information decoded (Parser.java:141–145).

**Corpus question.** Histogram of byte 0 over the corpus, split into
defined, unused, reserved, "do not use" and not listed.

<a id="amb.dti.shared"></a>
### amb.dti.shared

**Open in the document.** `!` is both a position report and the
Ultimeter 2000 logging form; `$` is both raw NMEA and the Ultimeter 2000
packet form (p. 31/17). Chapter 5 gives no selector; chapter 12 shows
`!!` and `$ULTW` (p. 82/62).

**Readings.** (a) Select by the bytes that follow: `!!`, `$ULTW`. (b)
Read a position or NMEA sentence unless it fails.

**Reading taken.** **[proposed]** (a). A position cannot start with `!`
(neither a digit nor a symbol table identifier), so `!!` is never also
a position. **[proposed]** A field that starts `$ULTW` is also an NMEA
sentence in one case: when byte 5 is a letter `A`–`Z` and byte 6 is
`,`, the five bytes after `$` are a valid
[`nmea.addr`](03-position.md#nmea.addr). A hex digit `A`–`F` after
`ULTW` can therefore start either. Where (b), reading the whole field
as NMEA by 03-position, would itself give no `syntax` or `value`
finding, the field gets `ambiguous` at offset 1, the finding that
[amb.wx.rawdti](06-weather.md#amb.wx.rawdti) gives against
`wx.raw.ultpkt`. Every other field divides the same way under both
readings: where (a) reads a position or an NMEA sentence, (b) reads the
same. A `!` or `$` field that fails as a position or as NMEA would be
raw weather under (b), but (a) already reports it as `syntax`, which
alone is given ([README section 3](README.md#3-tokenizer-model),
Precedence).

**Decoders (read).** FAP: `!` then `!` is Ultimeter; `$GP` is NMEA,
`$ULTW` weather, other `$` fields not parsed (FAP.pm:2648–2651,
2679–2689). Dire Wolf: `!!` and `$ULTW` are Ultimeter, other `$` NMEA
(decode_aprs.c:343–371). aprslib: `$` unsupported; `!!` fails as a
position (parsing/\_\_init\_\_.py:47–49; position.py:47–59, 89, 140–141).
Xastir: `!` then `!` and 40 hex digits or dashes, `ULTW` then 44
(db.c:14999, 15173). aprsc: `!!` is weather (parse_aprs.c:1205–1208).
pdn-aprs: `!!` and `$ULTW` first (decode.rs:28, 44).

**Corpus question.** How many `!` fields have `!` at byte 1, and how many
`$` fields start `$ULTW` against each NMEA address field?

<a id="amb.tp.header"></a>
### amb.tp.header

**Open in the document.** The inner header diagram gives "original source
and destination" 3–99 bytes, then network identifier and gateway with
`*` (p. 108/84). The prose lets the original path be kept for
diagnostics. Appendix 1 relabels the first column "source path header
without unused digipeaters, `*` or `:`" (p. 138/114). The inner source
can hold any printable byte but `>`, so the end of the header and the
place of the network identifier are not fixed by the diagram alone. The
form of the gateway address is not stated; the examples use the RF
callsign of the gateway, which is also the outer source (p. 109/85).

**Readings.** (a) The header ends at the first `:` after `}`; its last
two entries are network identifier and gateway; earlier entries are the
retained path. (b) The inner path is exactly network identifier and
gateway (UAP §2.6). (c) The header ends at the `:` after the `*`.

**Reading taken.** **[proposed]** (a), with the inner source excluding
`:`. A `*` anywhere but on the gateway gives `syntax`. The gateway is
read in the AX.25 form, since it is the station that sent the packet on
RF. Where (b) or (c) would divide an inner header that gives one of
these `syntax` findings differently, that finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence).
**[proposed]** On an inner header that (a) reads with no `syntax`
finding, the only `*` is on the last entry before the first `:`, so (c)
ends the header at the same byte. (b), which admits exactly the
network identifier and the gateway, reads the same entries when no
original path is kept, and fails when one is, since it would then take
a path entry as the network identifier and find a `*` past the
gateway. A reading that fails does not count. No `ambiguous` finding.

**Decoders (read).**

| Decoder | What it does | Where |
|---|---|---|
| FAP | Does not decode third-party traffic; the field falls to the `!` search of [amb.dti.offset](#amb.dti.offset). | FAP.pm:47; FAP.pm:2737–2767 |
| Dire Wolf | Parses the payload as a whole TNC-2 line in non-strict mode: first `:`, then `>`, path split at `,`; entries after the eighth are dropped without an error. | decode_aprs.c:247–276; `ax25_from_text`, ax25_pad.c:445–557 |
| aprslib | Parses the payload with the full line parser. | `parse_thirdparty`, thirdparty.py:10–21 |
| Xastir | Source up to `>`, path up to the next `:`, path under 100 bytes and checked by `valid_path`. | `extract_third_party`, db.c:15615–15700 |
| aprsc | First `:` after `}`; `>` within 10 bytes; checks source and destination; needs at least two path entries. Drops a packet whose inner path holds `,TCPIP` or `,TCPXX`. | `parse_aprs_3rdparty`, parse_aprs.c:1016–1073; incoming.c:974–983 |
| pdn-aprs | Same line parser, source allowed any 1–9 bytes 0x20–0x7E other than `>` and `:`. | `decode_tnc2_line`, packet.rs:229–297; `is_third_party_source`, packet.rs:40 |

**Corpus question.** In `}` fields: how many inner headers have entries
besides network identifier and gateway, none or several `*`, a `:`
before the `>`, or a gateway not in the AX.25 form?

<a id="amb.tp.nest"></a>
### amb.tp.nest

**Open in the document.** Nothing says whether the original information
field can itself start with `}`.

**Readings.** (a) Follow it, one level deeper each time. (b) Stop after
one level and keep the rest opaque.

**Reading taken.** **[proposed]** (a). Each further level gives
`unstated` at its `tp.dti`. The 256-byte field bounds the depth. Every
nested `}` carries the question, and the bytes of one packet cannot
narrow it, so it is decided by the reading
([README section 3](README.md#3-tokenizer-model)): `unstated` is the
only finding, with no `ambiguous` beside it.

**Decoders (read).** Dire Wolf calls `decode_aprs` on the payload, which
handles a further `}` the same way (decode_aprs.c:247–270). aprslib
calls `parse` again (thirdparty.py:15). aprsc calls `parse_aprs_body`
on the inner field, which dispatches `}` again (parse_aprs.c:1072,
1300–1302). Xastir unwraps once; an inner `}` reaches the status
fallback (db.c:16773–16776, 15431–15433). FAP and javAPRSlib do not
decode `}` (FAP.pm:47; Parser.java:274–276). pdn-aprs decodes the inner
packet with the same entry point (other.rs:381–389); no depth limit was
seen in the functions read.

**Corpus question.** How many `}` payloads start with `}` again, and to
what depth?

<a id="amb.tp.aea"></a>
### amb.tp.aea

**Open in the document.** Appendix 1 shows an AEA form of the source path
header and of the third-party header, "obsolete, shown for historical
reference only" (p. 137/113, p. 138/114), while p. 108/84 requires the
TNC-2 form. The AEA third-party diagram has no separator between its
first column and the network identifier (see [err.tp.aea](#err.tp.aea)).

**Readings.** (a) Recognise the AEA form inside `}` with `obsolete`. (b)
Do not recognise it.

**Reading taken.** **[proposed]** (a), with `>` as the missing separator,
as in the example that APRS 1.0.1 gave with the same diagram (1.0.1 PDF
p. 95). An inner header with no `,` and at least four `>`-separated
addresses, one of them followed by `*`, is `tp.aea`. At line level
APRS-IS carries TNC-2 text (UAP §1, ch. 4), so an AEA line header gives
`syntax`, and that finding alone is given
([README section 3](README.md#3-tokenizer-model), Precedence). An inner
header with no `,` cannot be read in the TNC-2 form, which puts a `,`
before `tp.net` and `tp.gate`, and one with a `,` is never `tp.aea`.
**[proposed]** So (b) fails on every inner header that (a) reads as
`tp.aea`, and a reading that fails does not count: no `ambiguous`
finding.

**Decoders (read).** Xastir converts an AEA path to TNC-2 order
(`valid_path`, util.c:3238–3283). FAP states it supports TNC-2 only
(FAP.pm:2495). Dire Wolf, aprslib and aprsc split the inner path at `,`
only (ax25_pad.c:525; common.py:48; `check_path_calls`, incoming.c:670,
called from parse_aprs.c:1059).

**Corpus question.** How many `}` payloads have an inner header without
`,` and with several `>`?

## 10. Errata

Each entry ends with an "Origin" line: where the defect first appears.
APRS 1.0.1 pages are PDF pages of the 2000 edition; 12b pages are PDF
pages of `APRS12b.pdf` in the same submodule.

<a id="err.line.flag"></a>
### err.line.flag

The frame diagram gives the closing flag 1 byte (p. 22/12), the Appendix 1
copy 2 bytes (p. 129/105); Appendix 7 records the correction to 1
(p. 154/130). Not visible in the text form. The reading follows
p. 22/12.

Origin: already in APRS 1.0.1, where the chapter diagram gives 1 (1.0.1
PDF p. 22) and the Appendix 1 copy 2 (1.0.1 PDF p. 104). The APRS 1.1
addendum lists the correction, which Appendix 7 marks as merged, but the
Appendix 1 copy was never changed. 12b has the same split (12b PDF p. 23
and p. 134).

<a id="err.dest.ssid"></a>
### err.dest.ssid

A non-zero destination SSID "specifies a generic APRS digipeater path"
(p. 22/12, p. 25/13), is "reserved for generic APRS digipeating"
(p. 29/19), and is obsolete with no known implementation (p. 27/17). The
reading follows p. 27/17 ([amb.dest.ssid](#amb.dest.ssid)).

Origin: introduced by the 12b/12c compilation. APRS 1.0.1 treats the
mechanism as current throughout (1.0.1 PDF p. 22, p. 23, p. 25–26). The
note declaring it obsolete is new in 12b (12b PDF p. 28/18), and the
older sentences on the other pages were left as they were; 12b already
has the contradiction.

<a id="err.dest.sym"></a>
### err.dest.sym

`SYM` addresses are "reserved for future use" on p. 27/17, a generic
destination on p. 29/19, and interchangeable with `GPS` and `SPC` on
p. 126/102. P. 29/19 also names `SPCL` where the list has `SPC*`. The
reading follows p. 126/102 and the list of p. 29/19.

Origin: already in APRS 1.0.1: the list and the `SPCL` sentence (1.0.1
PDF p. 23), the reservation (1.0.1 PDF p. 24) and the interchangeable
forms (1.0.1 PDF p. 102). 12b carries all of them (12b PDF p. 28, p. 30,
p. 131).

<a id="err.dest.example"></a>
### err.dest.example

P. 126/102 gives `GPS30` for the car symbol; by the `GPSCnn` rule and
Appendix 2 it is `GPSC30`. The precedence example of p. 127/103 writes
`GPSMV` in five bytes while p. 126/102 says the address is six. The
reading follows the rules; [amb.dest.symfill](#amb.dest.symfill) covers
the second point.

Origin: both are already in APRS 1.0.1 (`GPS30` on 1.0.1 PDF p. 102,
`GPSMV` on 1.0.1 PDF p. 103), and 12b has both (12b PDF p. 131, p. 132).

<a id="err.dest.chapref"></a>
### err.dest.chapref

P. 27/17, p. 29/19, p. 40/24 and p. 85/65 refer to "Chapter 20: APRS
Symbols"; in this edition symbols are chapter 21 (p. 124/100) and
chapter 20 is "Other Packets" (p. 123/99). Citations in this directory
use the page.

Origin: introduced by the 12b/12c compilation. In APRS 1.0.1 symbols are
chapter 20 and the references are right (1.0.1 PDF p. 24, p. 26, p. 34,
p. 75). 12b inserted a new chapter 18, the frequency specification,
which moved user-defined data, other packets and symbols down by one,
without the references being renumbered; 12b already has the error
(12b PDF p. 28, p. 30, p. 42, p. 87). The chapter headings of 1.0.1 and
12b were checked in their Markdown extractions. The same defect was
also entered as [err.sym.chapter](02-fields.md#err.sym.chapter), which
now points here.

<a id="err.src.ssid"></a>
### err.src.ssid

The SSID icon table (p. 127/103) and the SSID recommendations
(p. 128/104) give the same numbers different meanings, for example `-5`
yacht against other networks, `-12` jeep against one-way trackers. The
reading takes neither in the tokenizer ([amb.src.ssid](#amb.src.ssid)).

Origin: a merge of APRS 1.0.1 text with the APRS 1.1 addendum. The icon
rule and table are from 1.0.1 (1.0.1 PDF p. 26, p. 103), which has no
recommendations table. The recommendations come from the 1.1 item "SSID
Conventions in user calls" (listed on p. 154/130), and were printed next
to the icon table without a note on which applies. 12b has both (12b
PDF p. 132, p. 133).

<a id="err.dti.star"></a>
### err.dti.star

The same defect as
[err.wx.object-dti](06-weather.md#err.wx.object-dti), which records it
with its origin: the weather object uses `;` in chapter 12 (p. 86/66)
and `*` in Appendix 1 (p. 134/110). For the dispatch of section 7 the
chapter is followed: `*` is the Peet Bros identifier
([`wx.raw.peet`](06-weather.md#wx.raw.peet)) and `;` the object.

<a id="err.dti.x1j"></a>
### err.dti.x1j

Appendix 7 corrects a "page 18 X1J exception" (p. 154/130) that this
edition does not contain. The reading follows the correction: the
identifier is byte 0 ([amb.dti.offset](#amb.dti.offset)).

Origin: introduced by the 12b/12c compilation. The exception is in APRS
1.0.1 on its printed page 18 (1.0.1 PDF p. 28), with an example on 1.0.1
PDF p. 42; the page number in the correction is that of 1.0.1. 12b
removed the rule and the example but kept the correction that refers to
them; 12b already has the dangling reference.

<a id="err.tp.header"></a>
### err.tp.header

The inner header's first column is "original source and destination",
3–99 bytes (p. 108/84), longer than a source and destination can be; the
Appendix 1 copy calls it a source path header without unused
digipeaters, `*` or `:`, n bytes (p. 138/114). The source path header
digipeater part is 0–81 bytes on p. 107/83 and 0–80 on p. 137/113. The
reading applies the address limits only and no total
([amb.tp.header](#amb.tp.header)).

Origin: two sources. The 0–81 against 0–80 split is already in APRS
1.0.1 (1.0.1 PDF p. 94 against p. 112). The column label is new in 12c:
in 1.0.1 (1.0.1 PDF p. 95) and in 12b (12b PDF p. 111) the chapter
diagram has the Appendix 1 label, with which 3–99 bytes agrees. 12b does
not have the mismatch of label and length.

<a id="err.tp.aea"></a>
### err.tp.aea

The AEA third-party diagram (p. 138/114) has no separator column between
the source path header and the network identifier, so the byte between
them is not given. The reading takes `>` ([amb.tp.aea](#amb.tp.aea)).

Origin: already in APRS 1.0.1, whose chapter and Appendix 1 diagrams
have the same gap (1.0.1 PDF p. 95, p. 113). There the chapter example
showed `>` in that place. 12b dropped the AEA form from the chapter as
deprecated (12b PDF p. 109) and with it the example, keeping only the
Appendix 1 diagram (12b PDF p. 143).

<a id="err.tp.example"></a>
### err.tp.example

The four copies of the message in the third-party walkthrough
(p. 109/85) show the gap in `Hi Ian` at different widths, although the
information field is not to change. The byte content cannot be
determined from the PDF; the reading keeps the rule that the inner field
is the original unchanged.

Origin: introduced when chapter 17 was rewritten for 12b (Appendix 7
lists the overhaul among the 1.2 changes, p. 157/133). The APRS 1.0.1
walkthrough shows one space in every copy (1.0.1 PDF p. 96, rendered);
12b already has the differing widths (12b PDF p. 112, rendered).

## 11. Open items

- The APRS-IS q-construct document is not among the references. If it is
  added, `path.q` and `path.is` are checked against it
  ([amb.path.q](#amb.path.q)).
- Whether the `is-only` byte set of `addr.is` admits space, which
  "printable ASCII" on p. 108/84 can be read to include.
- Whether `dest.tocall` is checked against the aprs-deviceid registry in
  a later layer (UAP §5.3 shows unregistered identifiers).
- Cross-cutting: the reading treats a destination SSID and a source SSID
  as values only; their meanings belong to a decoding layer not yet
  written.
