# Frame, addresses and data type

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that the general rules of the [README](README.md#31-general-rules) do not settle is marked **[open]**. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |

## 1. Scope

The parts of a packet that come before any format: the TNC2 line, the
source, destination and path addresses, the destination classes, the
source SSID, the data type identifier and its dispatch, and third-party
payloads. The input is one line without its terminator. Frame fields
that the text form does not show (flags, control, PID, FCS, the C and H
bits) are not tokenized. The no-archive marker is read by
[`cmt.noarchive`](02-fields.md#cmt.noarchive). Rule prefixes: `line`,
`addr`, `path`, `dest`, `src`, `dti`, `tp`.

## 2. The line

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="line.header"></a>`line.header` | Address header | Source address, `line.gt`, destination address, then zero or more path entries each after `,`. Not a token itself. | yes | `line.sep` | p. 107/83 |
| <a id="line.gt"></a>`line.gt` | Source terminator | `>`, 1 byte. A header without `>` gives `syntax` here, and the header is a `residue`. | yes | 1 byte | p. 107/83 |
| <a id="line.sep"></a>`line.sep` | Header terminator | `:`, the first in the line ([amb.line.split](#amb.line.split)). A line without `:` gives `syntax` and verdict `unknown-format`. | yes | 1 byte | p. 107/83 |
| <a id="line.info"></a>`line.info` | Information field | 1 to 256 bytes of any value; its first byte is `dti`. Empty gives `syntax`; more than 256 bytes gives `value` at byte 257. | yes | end of line | p. 22/12; p. 23/13 |

## 3. Addresses

Every address of the header is in the AX.25 form (p. 22/12, p. 107/83).
A source may also be any short printable name (p. 108/84;
[amb.addr.form](#amb.addr.form)).

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="addr.src"></a>`addr.src` | Source address | `addr.call` with optional `addr.ssid` (as `src.ssid`), or `addr.is`. Empty gives `syntax`. | yes | `line.gt` | p. 22/12; p. 107/83; p. 108/84 |
| <a id="addr.dest"></a>`addr.dest` | Destination address | `addr.call` with optional `addr.ssid` (as `dest.ssid`); its class is given by section 5. Any other address gives `syntax` on this rule at its first byte that does not fit; empty gives `syntax`; a trailing `*` gives `syntax` at the `*`, a `residue` below the token. On a Mic-E destination that finding is not given at a byte that [04-mic-e section 3](04-mic-e.md#3-destination-address) reports, the more specific rule. | yes | `,` or `line.sep` | p. 22/12; p. 107/83 |
| <a id="addr.call"></a>`addr.call` | Callsign | 1 to 6 bytes, each `A`–`Z` or a digit. | yes | `-`, `*`, `,`, `>` or `:` | p. 22/12; p. 107/83 |
| <a id="addr.ssid"></a>`addr.ssid` | SSID | `-` then 1 to 15; SSID 0 is not written. `-0` or `-00` gives `syntax`; `-01` to `-09` gives `unstated` ([amb.addr.form](#amb.addr.form)); two digits above 15 give `value`. At a source an address that gives `syntax` or `value` here is `addr.is` instead. | no | `*`, `,`, `>` or `:` | p. 107/83 |
| <a id="addr.is"></a>`addr.is` | Name at a source | At `addr.src` and the first address of [`tp.aea`](#tp.aea), an address not read above: 1 to 9 bytes 0x20–0x7E other than `>` (a `:` cannot occur, [amb.line.split](#amb.line.split)). One token, `is-only`. Anything else gives `syntax` at the first byte outside the set or at the tenth byte. | — | `>` | p. 108/84 |

## 4. The path

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="path.sep"></a>`path.sep` | Entry separator | `,` before each entry. An empty entry gives `syntax` at its separator and counts toward the 8 of `path.digi`. | per entry | 1 byte | p. 107/83 |
| <a id="path.digi"></a>`path.digi` | Digipeater entry | `addr.call` with optional `addr.ssid`, then optional `path.used`; every entry before `path.q`. Any other address gives `syntax` on this rule at its first byte that does not fit. More than 8 entries give `syntax` at the separator before the ninth. | no | `,` or `line.sep` | p. 22/12; p. 107/83 |
| <a id="path.used"></a>`path.used` | Heard marker | `*` directly after a `path.digi` address: the digipeater heard. One per path; each further `*` gives `syntax` at that `*`. | no | 1 byte | p. 107/83 |
| <a id="path.obsolete"></a>`path.obsolete` | Obsolete alias | A `path.digi` whose callsign is `RELAY`, `TRACE` or `WIDE`, any SSID. Gives `obsolete`. | no | — | p. 20/10; p. 155/131 |
| <a id="path.nogate"></a>`path.nogate` | Gating block | A `path.digi` whose callsign is `NOGATE` or `RFONLY`. No finding. | no | — | p. 110/86 |
| <a id="path.q"></a>`path.q` | q-construct | The first entry that is `q`, `A` and one letter, without `*`; a `qA?*` entry is a `path.digi`. Gives `is-only`. Checked against the APRS-IS definition that p. 155/131 names (`APRS-IS q`, `APRS-IS q-alg`): a code outside its list gives `value`; `qAX`, deprecated, gives `obsolete`; `qAZ`, and `qAC` unless the path before it is exactly `TCPIP*`, which the algorithm rejects, give `syntax`; a missing call after the code gives `syntax` at the end of the entry; a second call after any code but `qAI` gives `syntax` on `path.is` at its separator; a call repeated after the construct gives `syntax` on `path.is` at its first byte. | no | `,` or `line.sep` | p. 155/131; APRS-IS q; APRS-IS q-alg |
| <a id="path.is"></a>`path.is` | Entry after the q-construct | 1 or more bytes 0x21–0x7E other than `,` and `:`; another byte gives `syntax`. The AX.25 form gives no finding, any other entry `is-only`, a trailing `*` `unstated` ([amb.path.q](#amb.path.q)). Not counted toward the 8. | no | `,` or `line.sep` | APRS-IS q |

## 5. Destination classes

The class is a depth-1 token inside `addr.dest` covering the callsign,
followed by a `dest.ssid` token when there is an SSID. A destination
not in the AX.25 form is classified by its bytes as written. The first
class that matches, in this order, is taken: the identifier first, then
each form before the wider one that also covers it
([amb.dest.class](#amb.dest.class)). For a third-party packet the outer
destination is classified with the outer identifier and the inner one
with the inner identifier.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="dest.mice"></a>`dest.mice` | Mic-E destination | Any destination when the identifier is 0x1C, 0x1D, `'` or `` ` ``; read by [04-mic-e.md](04-mic-e.md). One not in the AX.25 form is divided at its first `-`: the callsign part, then `dest.ssid` with the findings of `addr.ssid`. | with a Mic-E identifier | end of the callsign | p. 26/12 |
| <a id="dest.aprs"></a>`dest.aprs` | Obsolete generic | Exactly `APRS`. Gives `obsolete`. | — | end of the callsign | p. 29/19 |
| <a id="dest.tocall"></a>`dest.tocall` | Device identifier | `AP` and 1 to 4 bytes `A`–`Z` or digits, looked up in the register that p. 25/13 names, `3rdparty/aprs-deviceid/tocalls.yaml` at `c50d026`, with its own lookup (exact entry, then the longest wildcard). An identifier it does not list gives `unstated` at the first byte of `addr.dest`. | — | end of the callsign | p. 25/13 |
| <a id="dest.symnn"></a>`dest.symnn` | Numbered symbol | `GPSC` or `GPSE` and two digits, `01` to `94`; another number gives `value`. | — | end of the callsign | p. 27/17; p. 126/102; p. 139/115–p. 141/117 |
| <a id="dest.sym"></a>`dest.sym` | Lettered symbol | `GPS`, `SPC` or `SYM`, then a pair `xy` of the table below, then an optional overlay, a digit or `A`–`Z`. The space that fills an address without overlay is not written in the text form, so 5 bytes mean no overlay. An overlay on a primary-table pair gives `value`. | — | end of the callsign | p. 27/17; p. 107/83; p. 126/102; p. 139/115–p. 141/117 |
| <a id="dest.generic"></a>`dest.generic` | Generic address | `ALL`, `AP`, `CQ`, `DF`, `DGPS`, `DRILL`, `DX`, `GPS`, `ID`, `JAVA`, `MAIL`, `MICE`, `QST`, `QTH`, `RTCM`, `SKY`, `SPACE`, `SPC`, `SYM`, `TEL`, `TEST`, `TLM` or `WX`, extended by `A`–`Z` or digits to at most 6 bytes; or `BEACON`. | — | end of the callsign | p. 29/19 |
| <a id="dest.grid"></a>`dest.grid` | Locator | The 6-byte [`grid.loc`](03-position.md#grid.loc), upper case, every letter in its Maidenhead range ([amb.grid.range](03-position.md#amb.grid.range)). Gives `obsolete`. | — | end of the callsign | p. 28/18 |
| <a id="dest.altnet"></a>`dest.altnet` | Alternate net | Any other destination. No finding. | — | end of the callsign | p. 29/19 |
| <a id="dest.ssid"></a>`dest.ssid` | Destination SSID | The `addr.ssid` of the destination. No finding of its own ([amb.dest.ssid](#amb.dest.ssid)). | no | — | p. 22/12; p. 25/13; p. 27/17; p. 29/19 |

The pairs `xy` of `dest.sym`, derived from Appendix 2 (p. 139/115 to
p. 141/117): the second byte steps through the range in the order of
the symbol code.

| Symbol code | Primary-table `xy` | Alternate-table `xy` |
|---|---|---|
| `!` to `/` | `B` + (`B` to `P`) | `O` + (`B` to `P`) |
| `0` to `9` | `P` + the digit | `A` + the digit |
| `:` to `@` | `M` + (`R` to `X`) | `N` + (`R` to `X`) |
| `A` to `Z` | `P` + the letter | `A` + the letter |
| `[` to `` ` `` | `H` + (`S` to `X`) | `D` + (`S` to `X`) |
| `a` to `z` | `L` + the letter in upper case | `S` + the letter in upper case |
| `{` to `~` | `J` + (`1` to `4`) | `Q` + (`1` to `4`) |

## 6. Source SSID

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="src.ssid"></a>`src.ssid` | Source SSID | The `addr.ssid` of `addr.src`. Its meaning, an icon for trackers without another symbol or a station type, is a value; no finding ([amb.src.ssid](#amb.src.ssid)). | no | — | p. 22/12; p. 29/19; p. 127/103; p. 128/104 |

## 7. Data type identifier

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="dti"></a>`dti` | Data type identifier | Byte 0 of `line.info`, and only byte 0 (p. 23/13, confirmed by p. 154/130; [err.dti.x1j](#err.dti.x1j)). Selects the format by the table below and gives its findings. The token of byte 0 carries the identifier rule of the format the packet is classified as. | yes | 1 byte | p. 23/13; p. 31/17 |
| <a id="dti.unknown"></a>`dti.unknown` | Undispatched field | The whole of `line.info` when byte 0 selects no format and no obsolete form below matches. Verdict `unknown-format`, also inside a third-party payload ([amb.dti.undefined](#amb.dti.undefined)). | — | end of `line.info` | p. 31/17; p. 123/99 |

| Byte | Class | Read in | Finding at `dti` |
|---|---|---|---|
| 0x1C, 0x1D, `'`, `` ` `` | Mic-E | [04-mic-e.md](04-mic-e.md) | as 04 gives |
| `!` | position without timestamp; Ultimeter 2000 when byte 1 is `!` | [03-position.md](03-position.md); [06-weather.md](06-weather.md) for `!!` | `discouraged` for `!!` (p. 82/62) |
| `#`, `*` | Peet Bros U-II ([err.dti.star](#err.dti.star)) | [06-weather.md](06-weather.md) | `discouraged` (p. 82/62) |
| `$` | raw GPS; Ultimeter 2000 when the field starts `$ULTW` ([amb.dti.shared](#amb.dti.shared)) | [03-position.md](03-position.md); [06-weather.md](06-weather.md) for `$ULTW` | `discouraged` (p. 52/34; p. 82/62) |
| `%` | Agrelo DF | [03-position.md](03-position.md) | none |
| `)` | item | [05-object-item.md](05-object-item.md) | `discouraged` (p. 77/59) |
| `,` | invalid or test data | [09-other.md](09-other.md) | none |
| `/`, `@`, `=` | position | [03-position.md](03-position.md) | none |
| `:` | message and its kinds | [08-message.md](08-message.md) | none |
| `;` | object | [05-object-item.md](05-object-item.md) | none |
| `<`, `>`, `?`, `{` | capabilities, status, query, user-defined | [09-other.md](09-other.md) | none |
| `T` | telemetry | [07-telemetry.md](07-telemetry.md) | none |
| `[` | Maidenhead locator beacon | [03-position.md](03-position.md) | `obsolete` |
| `_` | weather without position | [06-weather.md](06-weather.md) | `discouraged` (p. 83/63) |
| `}` | third-party traffic | section 8 | none |
| `"`, `(`, `-`, `\`, `]`, `^`, `&`, `+`, `.` | unused or reserved | `dti.unknown` | `unstated` |
| `0`–`9`, `A`–`S`, `U`–`Z`, `a`–`z`, `\|`, `~` | do not use | `dti.unknown` | `syntax` |
| 0x00–0x1B, 0x1E–0x20, 0x7F–0xFF | not listed | `dti.unknown` | `value` |

The identifier rules that the byte-0 token carries:

| Byte | Identifier rules |
|---|---|
| 0x1C, 0x1D, `'`, `` ` `` | [`mice.dti`](04-mic-e.md#mice.dti) |
| `!`, `=`, `/`, `@` | [`pos.dti`](03-position.md#pos.dti); [`wx.pos`](06-weather.md#wx.pos) for a weather report; [`wx.raw.ultlog.dti`](06-weather.md#wx.raw.ultlog.dti) for `!!` |
| `#`, `*` | [`wx.raw.peet`](06-weather.md#wx.raw.peet) |
| `$` | [`nmea.dti`](03-position.md#nmea.dti), also for a `$ULTW` field read as NMEA ([amb.dti.shared](#amb.dti.shared)); [`wx.raw.ultpkt.dti`](06-weather.md#wx.raw.ultpkt.dti) for any other `$ULTW` |
| `%` | [`df.agrelo.dti`](03-position.md#df.agrelo.dti) |
| `)` | [`item.dti`](05-object-item.md#item.dti) |
| `,` | [`inv.dti`](09-other.md#inv.dti) |
| `:` | [`msg.dti`](08-message.md#msg.dti), [`bln.dti`](08-message.md#bln.dti), [`nws.dti`](08-message.md#nws.dti), [`tlm.def.dti`](07-telemetry.md#tlm.def.dti) or [`qry.dir.dti`](09-other.md#qry.dir.dti) ([08 section 2.1](08-message.md#21-kind-of-packet)) |
| `;` | [`obj.dti`](05-object-item.md#obj.dti); [`wx.obj`](06-weather.md#wx.obj) for a weather report |
| `<` | [`cap.dti`](09-other.md#cap.dti) |
| `>` | [`stat.dti`](09-other.md#stat.dti) |
| `?` | [`qry.dti`](09-other.md#qry.dti) |
| `T` | [`tlm.dti`](07-telemetry.md#tlm.dti) |
| `[` | [`grid.dti`](03-position.md#grid.dti) |
| `_` | [`wx.pl`](06-weather.md#wx.pl) |
| `{` | [`udf.dti`](09-other.md#udf.dti) |
| `}` | [`tp.dti`](#tp.dti) |

Before a field whose byte 0 selects no format becomes `dti.unknown`,
two obsolete forms without an identifier are tried, in this order: the
object of [`obj.obsolete`](05-object-item.md#obj.obsolete), then the
bulletin of [`bln.obsolete`](08-message.md#bln.obsolete). A match is
read by that rule, whose token covers the whole field at depth 0 and
whose `obsolete` finding replaces the finding at `dti`. Where byte 0
selects a format other than the item and the object (`)` and `;`), the
obsolete object is taken instead only when it matches and that format
also reads the field with no `syntax` or `value` finding, with
`ambiguous` on `obj.obsolete` at offset 0
([amb.obj.obsolete](05-object-item.md#amb.obj.obsolete)).

## 8. Third-party payloads

A `}` field carries an inner TNC-2 header and the original information
field unchanged (p. 107/83 to p. 110/86). The inner field is read from
`dti` again, one depth level down.

| ID | Field | Layout | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tp.dti"></a>`tp.dti` | Identifier | `}`; the byte-0 token carries `tp.dti`. | yes | 1 byte | p. 31/17; p. 108/84 |
| <a id="tp.src"></a>`tp.src` | Original source | `addr.call` with optional `addr.ssid` without a suffix that `addr.ssid` reports as `syntax` or `value`; or 1 to 9 bytes 0x20–0x7E other than `>`, which gives `is-only` ([amb.tp.header](#amb.tp.header)). Anything else gives `syntax` at the first byte outside the set or at the tenth byte. | yes | `>` | p. 108/84; p. 109/85 |
| <a id="tp.gt"></a>`tp.gt` | Source terminator | `>`. Without it the header gives `syntax` here and is a `residue`. | yes | 1 byte | p. 108/84 |
| <a id="tp.dest"></a>`tp.dest` | Original destination | As `addr.dest`, classified with the inner identifier; any other address gives `syntax` on this rule. | yes | `,` | p. 108/84 |
| <a id="tp.path"></a>`tp.path` | Retained original path | Zero or more entries, each a token that includes its `,`, read one level below by the rules of section 4, `path.used` included. An empty entry gives `syntax` at its `,`. | no | the `,` before `tp.net` | p. 108/84; p. 138/114 |
| <a id="tp.net"></a>`tp.net` | Network identifier | `,` and an address in the AX.25 form, without `*`. Any other address gives `syntax` on this rule at its first byte that does not fit; a `*` gives `syntax` at the `*`; empty gives `syntax`. | yes | `,` | p. 108/84 |
| <a id="tp.gate"></a>`tp.gate` | Receiving gateway | `,`, `addr.call` with optional `addr.ssid`, then `*`; the last entry. One `syntax` finding for an address not in the AX.25 form or a missing `*`, at the first byte at fault. When the header has fewer than two entries after the destination, `syntax` at `tp.sep`. | yes | `tp.sep` | p. 108/84 |
| <a id="tp.sep"></a>`tp.sep` | Inner header end | The first `:` after `tp.dti` ([amb.line.split](#amb.line.split)). Without it, `syntax` at the end of the field, the rest a `residue`, and verdict `unknown-format`. | yes | 1 byte | p. 108/84 |
| <a id="tp.info"></a>`tp.info` | Original information field | Read from `dti` at depth + 1. Empty gives `syntax`. | yes | end of the enclosing field | p. 108/84 |
| <a id="tp.aea"></a>`tp.aea` | AEA inner header | Recognised when the header has no `,`, at least four non-empty `>`-separated addresses and one `*`, at the end of the second-to-last: source, retained digipeaters, network identifier, gateway with `*`, original destination. Gives `obsolete`. Each address is read one level below, the last as a destination by section 5; the source may be `addr.is`; any other address not in the AX.25 form gives one `syntax` on `tp.aea`, at the first such byte. The `>` before the network identifier gives `unstated` ([err.tp.aea](#err.tp.aea)). | no | `tp.sep` | p. 138/114 |

## 9. Catalogue

| ID | Pages | What the document leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.line.split"></a>amb.line.split | p. 107/83; p. 108/84 | The header ends at `:`, but p. 108/84 lets a source hold any printable byte but `>`, `:` included. | ambiguous | 1 | **[open]** By rule 1 a source holding `:` conforms. Default: the header ends at the first `:` of the line, so such a line gives `syntax` at `line.gt`; the same for `tp.src` and `tp.sep`. |
| <a id="amb.line.aea"></a>amb.line.aea | p. 107/83; p. 137/113 | The AEA source path header is shown as an obsolete form beside the TNC-2 one; whether it describes the line that the tokenizer receives is not said. | unstated | 2 | **[open]** Default: not recognised at line level; an AEA line header gets the findings of the TNC-2 reading. |
| <a id="amb.addr.form"></a>amb.addr.form | p. 22/12; p. 107/83; p. 108/84; p. 109/85 | P. 107/83 puts every header address in the AX.25 form; p. 108/84 lets a source be any 1 to 9 printable bytes but `>`. The digit form of an SSID with a leading zero is not given. | conflict | 3; 2 | At a source, an address either side accepts conforms: `addr.is`, `is-only`, for `-0`, an SSID above 15 or a trailing `*` too. Elsewhere the AX.25 form, else `syntax`. `-01` to `-09`: `unstated`, read as the AX.25 form, the more specific. |
| <a id="amb.path.q"></a>amb.path.q | p. 155/131 | APRS12c names the q-construct and defers to the APRS-IS pages, which give the codes and that a call follows, but no byte form for the entries after it. | unstated | 2; 5 | `path.q` checked by those pages; `path.is` takes printable entries, `is-only` when not in the AX.25 form, `unstated` for a trailing `*`. |
| <a id="amb.dest.class"></a>amb.dest.class | p. 25/13; p. 26/12; p. 27/17; p. 28/18; p. 29/19 | The destination uses overlap and no precedence is given. | ambiguous | 4 | The more specific class is taken (section 5). `APRS`, every tocall and every symbol destination are also generic: no finding. A tocall or generic address that is also a locator, such as `AP51WX`, gives `ambiguous` on its class at the first byte of `addr.dest`. |
| <a id="amb.dest.ssid"></a>amb.dest.ssid | p. 22/12; p. 25/13; p. 27/17; p. 29/19 | A non-zero destination SSID is a live path, reserved, or obsolete, depending on the page ([err.dest.ssid](#err.dest.ssid)). | conflict | 3 | `dest.ssid`, no finding. |
| <a id="amb.src.ssid"></a>amb.src.ssid | p. 29/19; p. 127/103; p. 128/104 | Which meaning of a non-zero source SSID applies ([err.src.ssid](#err.src.ssid)). | conflict | 3 | `src.ssid`, no finding; the meaning is a value. |
| <a id="amb.dti.undefined"></a>amb.dti.undefined | p. 31/17; p. 123/99 | No receiver action for unused, reserved, "do not use" and unlisted identifiers; p. 123/99 lets programs show such packets as status. | unstated | 2; 1 | `dti.unknown`, verdict `unknown-format`. At `dti`: "do not use" `syntax`; unused or reserved `unstated`; a byte the closed table does not list `value` (README section 3.3). |
| <a id="amb.dti.shared"></a>amb.dti.shared | p. 31/17; p. 82/62 | `!` and `$` each name two formats with no selector. | ambiguous | 4 | `!!` cannot be a position: Ultimeter. A `$ULTW` field that is also an NMEA sentence without `syntax` or `value` is read as NMEA, the more specific shape, with `ambiguous` on `dti` at offset 1; any other `$ULTW` field is Ultimeter. |
| <a id="amb.tp.header"></a>amb.tp.header | p. 108/84; p. 138/114 | P. 108/84 lets the original source hold any printable byte but `>` and keep the original path; p. 138/114 gives the header without unused digipeaters, `*` or `:`. | conflict | 3 | Bytes that either side accepts conform: a `*` in `tp.src` or a retained entry gives no finding. The last two entries are network identifier and gateway; earlier ones are `tp.path`. |
| <a id="amb.tp.nest"></a>amb.tp.nest | p. 108/84 | Whether the carried field may itself start with `}`. | unstated | 2 | Read one level deeper each time, `unstated` at each nested `tp.dti`. |
| <a id="amb.tp.aea"></a>amb.tp.aea | p. 108/84; p. 138/114 | P. 108/84 requires the TNC-2 header; p. 138/114 still shows an AEA form, obsolete. | conflict | 3; 1 | `tp.aea`, `obsolete`, as its row recognises it; a near-miss is read as TNC-2. |
| <a id="err.line.flag"></a>err.line.flag | p. 22/12; p. 129/105; p. 154/130 | The closing flag is 1 byte on p. 22/12 and 2 on p. 129/105; p. 154/130 corrects to 1. | conflict | 3 | Not in the text form; nothing. |
| <a id="err.dest.ssid"></a>err.dest.ssid | p. 22/12; p. 25/13; p. 27/17; p. 29/19 | A non-zero destination SSID is a live generic path on p. 22/12 and p. 25/13, reserved on p. 29/19, obsolete on p. 27/17. | conflict | 3 | No finding ([amb.dest.ssid](#amb.dest.ssid)). |
| <a id="err.dest.sym"></a>err.dest.sym | p. 27/17; p. 29/19; p. 126/102 | `SYM` addresses are reserved on p. 27/17, generic on p. 29/19, a symbol form on p. 126/102; p. 29/19 names `SPCL` where its list has `SPC*`. | conflict | 3 | `SYMxy` is `dest.sym`, otherwise `dest.generic`; no finding. |
| <a id="err.dest.example"></a>err.dest.example | p. 126/102 | The car symbol is given as `GPS30`, where the rule and Appendix 2 give `GPSC30`. | conflict | 3 | A slip of the pen (a missing `C`): it allows nothing; `GPS30` is `dest.generic`. |
| <a id="err.dest.chapref"></a>err.dest.chapref | p. 27/17; p. 29/19; p. 40/24; p. 85/65; p. 123/99; p. 124/100 | References to "Chapter 20: APRS Symbols", which is chapter 21 in this edition. | conflict | 3 | No effect on bytes. |
| <a id="err.src.ssid"></a>err.src.ssid | p. 127/103; p. 128/104 | The SSID icon table and the SSID recommendations give the same numbers other meanings. | conflict | 3 | No effect on bytes. |
| <a id="err.dti.star"></a>err.dti.star | p. 31/17; p. 86/66; p. 134/110 | The weather object starts with `;` on p. 86/66 and with `*`, the Peet Bros identifier, in the format diagram of p. 134/110 ([err.wx.object-dti](06-weather.md#err.wx.object-dti)). | conflict | 3 | A slip of the pen in the diagram (`*` for `;`): it allows nothing. Every `*` field is Peet Bros. |
| <a id="err.dti.x1j"></a>err.dti.x1j | p. 154/130 | A correction refers to a "page 18 X1J exception" that this edition does not contain. | conflict | 3 | No effect on bytes; the identifier is byte 0. |
| <a id="err.tp.header"></a>err.tp.header | p. 107/83; p. 108/84; p. 137/113; p. 138/114 | The inner header's first column is 3–99 bytes on p. 108/84 and n on p. 138/114; the path part of the source path header is 0–81 bytes on p. 107/83 and 0–80 on p. 137/113. | conflict | 3 | No total length is checked, since one side accepts any; the per-address limits apply. |
| <a id="err.tp.aea"></a>err.tp.aea | p. 138/114 | The AEA third-party diagram has no column between the source path header and the network identifier, so the byte there is not given. | unstated | 2 | `unstated` on `tp.aea` at the `>` before the network identifier. |
| <a id="err.tp.example"></a>err.tp.example | p. 109/85 | The copies of `Hi Ian` show the gap at different widths, though the field must not change. | conflict | 3 | No rule on packet bytes; only the examples differ. |

## 10. Reviewed exceptions

None.

## 11. Open items

- [amb.line.split](#amb.line.split) and [amb.line.aea](#amb.line.aea)
  are open.
- The meanings of the destination and source SSIDs, and the symbol
  precedence of p. 127/103, belong to a decoding layer not yet written.
