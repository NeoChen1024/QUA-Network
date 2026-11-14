# Frame, addresses and data type

| | |
|---|---|
| Status | Draft. Not frozen. A catalogue row that waits for the author is marked **[open]** ([README section 2](README.md#2-conventions)). |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. See [RFC Appendix D](../rfc/qua-network-rfc-0.md#appendix-d-reference-documents). |

## 1. Scope

This file covers the fields of a packet that come before any format:

- the TNC2 line;
- the source, destination and path addresses;
- the destination classes;
- the source SSID;
- the data type identifier, and how it selects a format;
- third-party payloads.

The input is one line without its terminator. The tokenizer does not
tokenize the frame fields that the TNC2 line does not show: flags,
control, PID, FCS, and the C and H bits.
[`cmt.noarchive`](02-fields.md#cmt.noarchive) reads the no-archive
marker. Rule prefixes: `line`, `addr`, `path`, `dest`, `src`, `dti`,
`tp`.

## 2. The line

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="line.header"></a>`line.header` | Address header | Source address, `line.gt`, destination address, then zero or more path entries. A `,` comes before each path entry. This rule has no token of its own. | yes | `line.sep` | p. 107/83 |
| <a id="line.gt"></a>`line.gt` | Source terminator | `>`, 1 byte. A header without `>` gives `syntax` here, and the header is a `residue`. | yes | 1 byte | p. 107/83 |
| <a id="line.sep"></a>`line.sep` | Header terminator | `:`, the first `:` in the line ([amb.line.split](#amb.line.split)). A line without `:` gives `syntax` and the verdict `unknown-format`. | yes | 1 byte | p. 107/83 |
| <a id="line.info"></a>`line.info` | Information field | 1 to 256 bytes of any value. Its first byte is `dti`. An empty field gives `syntax`. More than 256 bytes give `value` at byte 257. | yes | end of line | p. 22/12; p. 23/13 |

## 3. Addresses

Every address of the header is in the AX.25 format (p. 22/12,
p. 107/83). A source can also be any short printable name (p. 108/84;
[amb.addr.form](#amb.addr.form)).

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="addr.src"></a>`addr.src` | Source address | `addr.call` with an optional `addr.ssid` (as `src.ssid`), or `addr.is`. An empty address gives `syntax`. | yes | `line.gt` | p. 22/12; p. 107/83; p. 108/84 |
| <a id="addr.dest"></a>`addr.dest` | Destination address | `addr.call` with an optional `addr.ssid` (as `dest.ssid`). Section 5 gives its class. Any other address gives `syntax` on this rule, at its first byte that does not match. An empty address gives `syntax`. A `*` at the end gives `syntax` at the `*`. The `*` is a `residue` one level below the token. If the destination is a Mic-E destination, this rule gives no finding at a byte where [04-mic-e section 3](04-mic-e.md#3-destination-address) gives a finding. The rule of 04 section 3 gives the finding. | yes | `,` or `line.sep` | p. 22/12; p. 107/83 |
| <a id="addr.call"></a>`addr.call` | Callsign | 1 to 6 bytes. Each byte is `A`–`Z` or a digit. | yes | `-`, `*`, `,`, `>` or `:` | p. 22/12; p. 107/83 |
| <a id="addr.ssid"></a>`addr.ssid` | SSID | `-` then 1 to 15. The TNC2 line does not show SSID 0. `-0` or `-00` gives `syntax`. `-01` to `-09` gives `unstated` ([amb.addr.form](#amb.addr.form)). Two digits above 15 give `value`. If the address is a source and this rule gives `syntax` or `value`, the address is `addr.is` instead. | no | `*`, `,`, `>` or `:` | p. 107/83 |
| <a id="addr.is"></a>`addr.is` | Name at a source | Places: `addr.src` and the first address of [`tp.aea`](#tp.aea). An address that the rules above do not read. 1 to 9 bytes 0x20–0x7E, other than `>`. A `:` cannot occur ([amb.line.split](#amb.line.split)). One token, with `is-only`. Other bytes give `syntax` at the first byte outside the set or at the tenth byte. | — | `>` | p. 108/84 |

## 4. The path

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="path.sep"></a>`path.sep` | Entry separator | `,` before each entry. An empty entry gives `syntax` at its separator. It counts toward the 8 of `path.digi`. | per entry | 1 byte | p. 107/83 |
| <a id="path.digi"></a>`path.digi` | Digipeater entry | `addr.call` with an optional `addr.ssid`, then an optional `path.used`. Every entry before `path.q` is a `path.digi`. Any other address gives `syntax` on this rule, at its first byte that does not match. More than 8 entries give `syntax` at the separator before the ninth entry. | no | `,` or `line.sep` | p. 22/12; p. 107/83 |
| <a id="path.used"></a>`path.used` | Heard marker | `*` directly after a `path.digi` address. It shows that the digipeater heard the packet. One per path. Each further `*` gives `syntax` at that `*`. | no | 1 byte | p. 107/83 |
| <a id="path.obsolete"></a>`path.obsolete` | Obsolete alias | A `path.digi` with the callsign `RELAY`, `TRACE` or `WIDE`, with any SSID. Gives `obsolete`. | no | — | p. 20/10; p. 155/131 |
| <a id="path.nogate"></a>`path.nogate` | Gating block | A `path.digi` with the callsign `NOGATE` or `RFONLY`. No finding. | no | — | p. 110/86 |
| <a id="path.q"></a>`path.q` | q-construct | The first entry that is `q`, `A` and one letter, with no `*`. A `qA?*` entry is a `path.digi`. Gives `is-only`. For its other findings, see the list below the table. | no | `,` or `line.sep` | p. 155/131; APRS-IS q; APRS-IS q-alg |
| <a id="path.is"></a>`path.is` | Entry after the q-construct | 1 or more bytes 0x21–0x7E, other than `,` and `:`. Another byte gives `syntax`. An entry in the AX.25 format gives no finding. Any other entry gives `is-only`. A `*` at the end gives `unstated` ([amb.path.q](#amb.path.q)). These entries do not count toward the 8. | no | `,` or `line.sep` | APRS-IS q |

The tokenizer checks `path.q` against the APRS-IS definition that APRS12c
names (`APRS-IS q`, `APRS-IS q-alg`, p. 155/131). These cases give a
finding:

- A code outside the list of that definition gives `value`.
- `qAX` is deprecated and gives `obsolete`.
- The algorithm rejects `qAZ`, and `qAC` after a path that is not exactly
  `TCPIP*`. These codes give `syntax`.
- A missing call after the code gives `syntax` at the end of the entry.
- A second call after a code other than `qAI` gives `syntax` on
  `path.is`, at its separator.
- A call that is repeated after the construct gives `syntax` on
  `path.is`, at its first byte.

## 5. Destination classes

The class is a depth-1 token inside `addr.dest`. It covers the callsign.
If there is an SSID, a `dest.ssid` token follows it. If a destination is
not in the AX.25 format, the tokenizer classifies it by its bytes as they
appear in the line.

The tokenizer uses the first class that matches, in this order. First
comes the class that the identifier selects (`dest.mice`). After it,
each format comes before a wider format that also covers it
([amb.dest.class](#amb.dest.class)). For a third-party packet, the
tokenizer classifies the outer destination with the outer identifier. It
classifies the inner destination with the inner identifier.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="dest.mice"></a>`dest.mice` | Mic-E destination | Any destination, if the identifier is 0x1C, 0x1D, `'` or `` ` ``. [04-mic-e.md](04-mic-e.md) reads it. If the destination is not in the AX.25 format, the tokenizer divides it at its first `-`. The callsign field comes first. `dest.ssid` follows, with the findings of `addr.ssid`. | with a Mic-E identifier | end of the callsign | p. 26/12 |
| <a id="dest.aprs"></a>`dest.aprs` | Obsolete generic | Exactly `APRS`. Gives `obsolete`. | — | end of the callsign | p. 29/19 |
| <a id="dest.tocall"></a>`dest.tocall` | Device identifier | `AP` and 1 to 4 bytes. Each byte is `A`–`Z` or a digit. The tokenizer looks it up in the register that APRS12c names (p. 25/13): `3rdparty/aprs-deviceid/tocalls.yaml` at `c50d026`. It uses the lookup of the register: first an exact entry, then the longest wildcard. If the register does not list the identifier, the tokenizer gives `unstated` at the first byte of `addr.dest`. | — | end of the callsign | p. 25/13 |
| <a id="dest.symnn"></a>`dest.symnn` | Numbered symbol | `GPSC` or `GPSE` and two digits, `01` to `94`. Another number gives `value`. | — | end of the callsign | p. 27/17; p. 126/102; p. 139/115–p. 141/117 |
| <a id="dest.sym"></a>`dest.sym` | Lettered symbol | `GPS`, `SPC` or `SYM`, then a pair `xy` of the table below, then an optional overlay. The overlay is a digit or `A`–`Z`. The TNC2 line does not show the space that fills an address without an overlay. Thus 5 bytes mean no overlay. An overlay on a primary-table pair gives `value`. | — | end of the callsign | p. 27/17; p. 107/83; p. 126/102; p. 139/115–p. 141/117 |
| <a id="dest.generic"></a>`dest.generic` | Generic address | `ALL`, `AP`, `CQ`, `DF`, `DGPS`, `DRILL`, `DX`, `GPS`, `ID`, `JAVA`, `MAIL`, `MICE`, `QST`, `QTH`, `RTCM`, `SKY`, `SPACE`, `SPC`, `SYM`, `TEL`, `TEST`, `TLM` or `WX`. Bytes `A`–`Z` or digits can follow, to a maximum of 6 bytes in total. Or `BEACON`. | — | end of the callsign | p. 29/19 |
| <a id="dest.grid"></a>`dest.grid` | Locator | The 6-byte [`grid.loc`](03-position.md#grid.loc), in upper case. Each letter is in its Maidenhead range ([amb.grid.range](03-position.md#amb.grid.range)). Gives `obsolete`. | — | end of the callsign | p. 28/18 |
| <a id="dest.altnet"></a>`dest.altnet` | Alternate net | Any other destination. No finding. | — | end of the callsign | p. 29/19 |
| <a id="dest.ssid"></a>`dest.ssid` | Destination SSID | The `addr.ssid` of the destination. No finding of its own ([amb.dest.ssid](#amb.dest.ssid)). | no | — | p. 22/12; p. 25/13; p. 27/17; p. 29/19 |

The table below gives the pairs `xy` of `dest.sym`. The pairs come from
Appendix 2 (p. 139/115 to p. 141/117). In each row, the second byte goes
through its range in the order of the symbol codes.

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

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="src.ssid"></a>`src.ssid` | Source SSID | The `addr.ssid` of `addr.src`. Its meaning is a value: an icon for a tracker without another symbol, or a station type. No finding ([amb.src.ssid](#amb.src.ssid)). | no | — | p. 22/12; p. 29/19; p. 127/103; p. 128/104 |

## 7. Data type identifier

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="dti"></a>`dti` | Data type identifier | Byte 0 of `line.info`, and only byte 0 (p. 23/13, confirmed on p. 154/130; [err.dti.x1j](#err.dti.x1j)). It selects the format by the table below. It gives the findings of that table. The token of byte 0 has the rule ID of the identifier rule of the format that the tokenizer selects. | yes | 1 byte | p. 23/13; p. 31/17 |
| <a id="dti.unknown"></a>`dti.unknown` | Undispatched field | The whole `line.info`, if byte 0 selects no format and no obsolete format below matches. Verdict `unknown-format`. This also applies inside a third-party payload ([amb.dti.undefined](#amb.dti.undefined)). | — | end of `line.info` | p. 31/17; p. 123/99 |

| Byte | Class | Read in | Finding at `dti` |
|---|---|---|---|
| 0x1C, 0x1D, `'`, `` ` `` | Mic-E | [04-mic-e.md](04-mic-e.md) | as 04-mic-e gives |
| `!` | position without timestamp; Ultimeter 2000 if byte 1 is `!` | [03-position.md](03-position.md); [06-weather.md](06-weather.md) for `!!` | `discouraged` for `!!` (p. 82/62) |
| `#`, `*` | Peet Bros U-II ([err.dti.star](#err.dti.star)) | [06-weather.md](06-weather.md) | `discouraged` (p. 82/62) |
| `$` | raw GPS; Ultimeter 2000 if the field starts with `$ULTW` ([amb.dti.shared](#amb.dti.shared)) | [03-position.md](03-position.md); [06-weather.md](06-weather.md) for `$ULTW` | `discouraged` (p. 52/34; p. 82/62) |
| `%` | Agrelo DF | [03-position.md](03-position.md) | none |
| `)` | Item | [05-object-item.md](05-object-item.md) | `discouraged` (p. 77/59) |
| `,` | invalid or test data | [09-other.md](09-other.md) | none |
| `/`, `@`, `=` | position | [03-position.md](03-position.md) | none |
| `:` | message and its kinds | [08-message.md](08-message.md) | none |
| `;` | Object | [05-object-item.md](05-object-item.md) | none |
| `<`, `>`, `?`, `{` | capabilities, status, query, user-defined | [09-other.md](09-other.md) | none |
| `T` | telemetry | [07-telemetry.md](07-telemetry.md) | none |
| `[` | Maidenhead locator beacon | [03-position.md](03-position.md) | `obsolete` |
| `_` | weather without position | [06-weather.md](06-weather.md) | `discouraged` (p. 83/63) |
| `}` | third-party traffic | section 8 | none |
| `"`, `(`, `-`, `\`, `]`, `^`, `&`, `+`, `.` | unused or reserved | `dti.unknown` | `unstated` |
| `0`–`9`, `A`–`S`, `U`–`Z`, `a`–`z`, `\|`, `~` | do not use | `dti.unknown` | `syntax` |
| 0x00–0x1B, 0x1E–0x20, 0x7F–0xFF | not listed | `dti.unknown` | `value` |

The token of byte 0 has one of these rule IDs:

| Byte | Identifier rules |
|---|---|
| 0x1C, 0x1D, `'`, `` ` `` | [`mice.dti`](04-mic-e.md#mice.dti) |
| `!`, `=`, `/`, `@` | [`pos.dti`](03-position.md#pos.dti); [`wx.pos`](06-weather.md#wx.pos) for a weather report; [`wx.raw.ultlog.dti`](06-weather.md#wx.raw.ultlog.dti) for `!!` |
| `#`, `*` | [`wx.raw.peet`](06-weather.md#wx.raw.peet) |
| `$` | [`nmea.dti`](03-position.md#nmea.dti), also for a `$ULTW` field that the tokenizer reads as NMEA ([amb.dti.shared](#amb.dti.shared)); [`wx.raw.ultpkt.dti`](06-weather.md#wx.raw.ultpkt.dti) for any other `$ULTW` |
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

If byte 0 of a field selects no format, the field becomes `dti.unknown`.
Before that, the tokenizer tries two obsolete formats without an
identifier, in this order:

1. the Object of [`obj.obsolete`](05-object-item.md#obj.obsolete);
2. the bulletin of [`bln.obsolete`](08-message.md#bln.obsolete).

If one of them matches, the tokenizer reads the field by that rule. The
token of that rule covers the whole field at depth 0. The `obsolete`
finding of that rule replaces the finding at `dti`.

Byte 0 can select a format other than the Item and the Object (`)` and
`;`). In this case, the tokenizer uses the obsolete Object instead only
if both of these conditions are true:

- the obsolete Object matches;
- the format of byte 0 also reads the field with no `syntax` or `value`
  finding.

The tokenizer then gives `ambiguous` on `obj.obsolete` at offset 0
([amb.obj.obsolete](05-object-item.md#amb.obj.obsolete)).

## 8. Third-party payloads

A `}` field contains an inner TNC-2 header and the original information
field, with no change (p. 107/83 to p. 110/86). The tokenizer reads the
inner field again from `dti`, one level below.

| ID | Field | Format | Required | Ends at | Source |
|---|---|---|---|---|---|
| <a id="tp.dti"></a>`tp.dti` | Identifier | `}`. The token of byte 0 has the rule ID `tp.dti`. | yes | 1 byte | p. 31/17; p. 108/84 |
| <a id="tp.src"></a>`tp.src` | Original source | One of two formats. First: `addr.call` with an optional `addr.ssid`, where `addr.ssid` gives no `syntax` or `value`. Second: 1 to 9 bytes 0x20–0x7E, other than `>`; this format gives `is-only` ([amb.tp.header](#amb.tp.header)). Other bytes give `syntax` at the first byte outside the set or at the tenth byte. | yes | `>` | p. 108/84; p. 109/85 |
| <a id="tp.gt"></a>`tp.gt` | Source terminator | `>`. If it is missing, the header gives `syntax` here, and the header is a `residue`. | yes | 1 byte | p. 108/84 |
| <a id="tp.dest"></a>`tp.dest` | Original destination | The same as `addr.dest`. The tokenizer classifies it with the inner identifier. Any other address gives `syntax` on this rule. | yes | `,` | p. 108/84 |
| <a id="tp.path"></a>`tp.path` | Retained original path | Zero or more entries. Each entry is a token that includes its `,`. The tokenizer reads each entry one level below, by the rules of section 4, `path.used` included. An empty entry gives `syntax` at its `,`. | no | the `,` before `tp.net` | p. 108/84; p. 138/114 |
| <a id="tp.net"></a>`tp.net` | Network identifier | `,` and an address in the AX.25 format, with no `*`. Any other address gives `syntax` on this rule, at its first byte that does not match. A `*` gives `syntax` at the `*`. An empty address gives `syntax`. | yes | `,` | p. 108/84 |
| <a id="tp.gate"></a>`tp.gate` | Receiving gateway | `,`, `addr.call` with an optional `addr.ssid`, then `*`. It is the last entry. An address not in the AX.25 format, or a missing `*`, gives one `syntax` finding, at the first incorrect byte. If the header has fewer than two entries after the destination, `syntax` at `tp.sep`. | yes | `tp.sep` | p. 108/84 |
| <a id="tp.sep"></a>`tp.sep` | Inner header end | The first `:` after `tp.dti` ([amb.line.split](#amb.line.split)). If it is missing, `syntax` at the end of the field. The rest is a `residue`, and the verdict is `unknown-format`. | yes | 1 byte | p. 108/84 |
| <a id="tp.info"></a>`tp.info` | Original information field | The tokenizer reads it from `dti`, one level below. An empty field gives `syntax`. | yes | end of the enclosing field | p. 108/84 |
| <a id="tp.aea"></a>`tp.aea` | AEA inner header | The tokenizer recognises this format by three conditions. The header has no `,`. It has at least four non-empty addresses separated by `>`. It has one `*`, at the end of the second-to-last address. The addresses are: source, retained digipeaters, network identifier, gateway with `*`, original destination. Gives `obsolete`. The tokenizer reads each address one level below. It reads the last address as a destination by section 5. The source can be `addr.is`. Any other address not in the AX.25 format gives one `syntax` on `tp.aea`, at the first such byte. The `>` before the network identifier gives `unstated` ([err.tp.aea](#err.tp.aea)). | no | `tp.sep` | p. 138/114 |

## 9. Catalogue

| ID | Pages | What APRS12c leaves open | Class | Rule | What the tokenizer does |
|---|---|---|---|---|---|
| <a id="amb.line.split"></a>amb.line.split | p. 107/83; p. 108/84 | The header ends at `:`. But APRS12c permits any printable byte other than `>` in a source, `:` included (p. 108/84). | ambiguous | none | Working choice: the header ends at the first `:` of the line. Thus a source that contains `:` gives `syntax` at `line.gt`. The same applies to `tp.src` and `tp.sep`. |
| <a id="amb.line.aea"></a>amb.line.aea | p. 107/83; p. 137/113 | APRS12c shows the AEA source path header as an obsolete format next to the TNC-2 header. APRS12c does not say if it describes the line that the tokenizer receives. | unstated | none | Working choice: the tokenizer does not recognise it at line level. An AEA line header gets the findings of the TNC-2 interpretation. |
| <a id="amb.addr.form"></a>amb.addr.form | p. 22/12; p. 107/83; p. 108/84; p. 109/85 | APRS12c puts every header address in the AX.25 format (p. 107/83). It permits a source of any 1 to 9 printable bytes other than `>` (p. 108/84). APRS12c does not specify the digits of an SSID with a leading zero. | conflict | 3; 2 | At a source, the tokenizer accepts an address that either side accepts. An address that the AX.25 format rejects is `addr.is`, with `is-only`. This includes `-0`, an SSID above 15 and a `*` at the end. At other places: the AX.25 format, and other bytes give `syntax`. `-01` to `-09`: `unstated`. The tokenizer reads them as the AX.25 format, the stricter format. |
| <a id="amb.path.q"></a>amb.path.q | p. 155/131 | APRS12c names the q-construct and defers to the APRS-IS pages. These pages specify the codes, and that a call follows the code. They do not specify the format of the entries after the q-construct. | unstated | 2; 5 | The tokenizer checks `path.q` against those pages. `path.is` accepts printable entries. It gives `is-only` for an entry that is not in the AX.25 format, and `unstated` for a `*` at the end. |
| <a id="amb.dest.class"></a>amb.dest.class | p. 25/13; p. 26/12; p. 27/17; p. 28/18; p. 29/19 | The destination formats overlap. APRS12c does not specify which format has priority. | ambiguous | 4 | The tokenizer uses the class with the stricter format (section 5). `APRS`, every tocall and every symbol destination are also generic addresses: no finding. A tocall or a generic address can also be a locator, for example `AP51WX`. Then its class gives `ambiguous` at the first byte of `addr.dest`. |
| <a id="amb.dest.ssid"></a>amb.dest.ssid | p. 22/12; p. 25/13; p. 27/17; p. 29/19 | Different pages give a non-zero destination SSID different meanings: a live path, reserved, or obsolete ([err.dest.ssid](#err.dest.ssid)). | conflict | 3 | `dest.ssid`, no finding. |
| <a id="amb.src.ssid"></a>amb.src.ssid | p. 29/19; p. 127/103; p. 128/104 | APRS12c does not specify which meaning of a non-zero source SSID applies ([err.src.ssid](#err.src.ssid)). | conflict | 3 | `src.ssid`, no finding. The meaning is a value. |
| <a id="amb.dti.undefined"></a>amb.dti.undefined | p. 31/17; p. 123/99 | APRS12c specifies no receiver action for unused, reserved, "do not use" and unlisted identifiers. APRS12c permits programs to show such packets as status (p. 123/99). | unstated | 2; 1 | `dti.unknown`, verdict `unknown-format`. At `dti`: "do not use" gives `syntax`. Unused or reserved gives `unstated`. A byte that the closed table does not list gives `value` (README section 3.3). |
| <a id="amb.dti.shared"></a>amb.dti.shared | p. 31/17; p. 82/62 | `!` and `$` each name two formats. APRS12c specifies no way to select one of them. | ambiguous | 4 | `!!` cannot be a position, so it is Ultimeter. If a `$ULTW` field is also an NMEA sentence with no `syntax` or `value`, the tokenizer reads it as NMEA, the stricter format. It gives `ambiguous` on `dti` at offset 1. Any other `$ULTW` field is Ultimeter. |
| <a id="amb.tp.header"></a>amb.tp.header | p. 108/84; p. 138/114 | APRS12c permits any printable byte other than `>` in the original source, and keeps the original path (p. 108/84). Its diagram shows the header with no unused digipeaters, no `*` and no `:` (p. 138/114). | conflict | 3 | The tokenizer accepts bytes that either side accepts. Thus a `*` in `tp.src` or in a retained entry gives no finding. The last two entries are the network identifier and the gateway. The entries before them are `tp.path`. |
| <a id="amb.tp.nest"></a>amb.tp.nest | p. 108/84 | APRS12c does not say if the inner field can also start with `}`. | unstated | 2 | The tokenizer reads each nested field one level below. It gives `unstated` at each nested `tp.dti`. |
| <a id="amb.tp.aea"></a>amb.tp.aea | p. 108/84; p. 138/114 | APRS12c requires the TNC-2 header (p. 108/84). It still shows an AEA format, as obsolete (p. 138/114). | conflict | 3; 1 | `tp.aea`, with `obsolete`, where its row recognises it. The tokenizer reads a header that almost matches as TNC-2. |
| <a id="err.line.flag"></a>err.line.flag | p. 22/12; p. 129/105; p. 154/130 | The closing flag is 1 byte on p. 22/12 and 2 bytes on p. 129/105. APRS12c corrects it to 1 byte (p. 154/130). | conflict | 3 | The TNC2 line does not show the flag. The tokenizer does nothing. |
| <a id="err.dest.ssid"></a>err.dest.ssid | p. 22/12; p. 25/13; p. 27/17; p. 29/19 | A non-zero destination SSID is a live generic path on p. 22/12 and p. 25/13. It is reserved on p. 29/19 and obsolete on p. 27/17. | conflict | 3 | No finding ([amb.dest.ssid](#amb.dest.ssid)). |
| <a id="err.dest.sym"></a>err.dest.sym | p. 27/17; p. 29/19; p. 126/102 | `SYM` addresses are reserved on p. 27/17, generic on p. 29/19, and a symbol format on p. 126/102. The description in APRS12c names `SPCL`, but the list on the same page has `SPC*` (p. 29/19). | conflict | 3 | `SYMxy` is `dest.sym`. Other `SYM` addresses are `dest.generic`. No finding. |
| <a id="err.dest.example"></a>err.dest.example | p. 126/102 | APRS12c shows the car symbol as `GPS30`. The requirement of APRS12c and Appendix 2 specify `GPSC30`. | conflict | 3 | A typing error (a missing `C`). It permits nothing. `GPS30` is `dest.generic`. |
| <a id="err.dest.chapref"></a>err.dest.chapref | p. 27/17; p. 29/19; p. 40/24; p. 85/65; p. 123/99; p. 124/100 | APRS12c refers to "Chapter 20: APRS Symbols". In this edition, that chapter is chapter 21. | conflict | 3 | No effect on bytes. |
| <a id="err.src.ssid"></a>err.src.ssid | p. 127/103; p. 128/104 | The SSID icon table and the SSID recommendations give different meanings to the same numbers. | conflict | 3 | No effect on bytes. |
| <a id="err.dti.star"></a>err.dti.star | p. 31/17; p. 86/66; p. 134/110 | On p. 86/66, the weather Object starts with `;`. In the format diagram of p. 134/110, it starts with `*`, the Peet Bros identifier ([err.wx.object-dti](06-weather.md#err.wx.object-dti)). | conflict | 3 | A typing error in the diagram (`*` for `;`). It permits nothing. Every `*` field is Peet Bros. |
| <a id="err.dti.x1j"></a>err.dti.x1j | p. 154/130 | A correction refers to a "page 18 X1J exception". This edition does not contain it. | conflict | 3 | No effect on bytes. The identifier is byte 0. |
| <a id="err.tp.header"></a>err.tp.header | p. 107/83; p. 108/84; p. 137/113; p. 138/114 | The first column of the inner header is 3–99 bytes on p. 108/84 and n bytes on p. 138/114. The path field of the source path header is 0–81 bytes on p. 107/83 and 0–80 bytes on p. 137/113. | conflict | 3 | The tokenizer checks no total length, because one side accepts any length. The limits for each address apply. |
| <a id="err.tp.aea"></a>err.tp.aea | p. 138/114 | The AEA third-party diagram has no column between the source path header and the network identifier. Thus APRS12c does not specify the byte at that place. | unstated | 2 | `unstated` on `tp.aea` at the `>` before the network identifier. |
| <a id="err.tp.example"></a>err.tp.example | p. 109/85 | The copies of `Hi Ian` show the gap with different widths. But APRS12c requires that the field does not change. | conflict | 3 | No requirement about packet bytes. Only the examples are different. |

## 10. Reviewed exceptions

None.

## 11. Open items

- The meanings of the destination SSID and the source SSID belong to a
  decoding layer. The symbol priority of p. 127/103 also belongs to this
  layer. This layer does not exist yet.
