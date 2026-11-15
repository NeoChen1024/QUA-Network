# Values of status report fields

| | |
|---|---|
| Status | Draft. Not frozen. A paragraph, value rule or catalogue row of this file is **[proposed]** if it has no other label. An **[agreed]** item is a decision of the author. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of a status report give values
([09 section 2](09-other.md#2-status-reports)). The tokens come from
[09](09-other.md), [02](02-fields.md) and [03](03-position.md). This file
adds no token and changes no finding. The rule prefix is `val`.

These parts are outside this file:

- the position of a locator (section 4);
- a frequency in the status text
  ([09 section 7](09-other.md#7-frequency-specification));
- the status text of Mic-E. It is the comment of a position
  ([10-values section 9](10-values.md#9-fields-in-a-comment)).

## 2. Conventions

The conventions of [10-values section 2](10-values.md#2-conventions) apply
to this file. These are the terms, the value tables, the findings that
concern a value, and the effects.

The status text is a byte string. The decoder does not decode it as text.

## 3. Timestamp and text

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.stat.text"></a>`val.stat.text` | Status text | [`stat.text`](09-other.md#stat.text) | Without a locator: all bytes of the token. After a locator: the bytes of the token without its first byte, the `SP`. | Byte string | p. 104/80, p. 106/82 |
| <a id="val.stat.beam"></a>`val.stat.beam` | Beam heading, effective radiated power | [`stat.beam`](09-other.md#stat.beam) | `b` is the three bytes of the token. Heading: `h = b[1] − 48` for a digit, `h = b[1] − 55` for a letter. The heading is 10 · `h`. Power: `k = b[2] − 48`. The power is 10 · `k`². | Heading in degrees, step 10, 0 to 350. Power in watts, `k` 1 to 27, 10 to 7290. | p. 105/81 |

The timestamp of a status report is a `time.dhm` token in the zulu form
([`stat.time`](09-other.md#stat.time)). The value rule
[val.time.dhm](10-values.md#val.time.dhm) gives its values.

After a locator, the first byte of the text is a `SP` (p. 105/81). It
separates the text from the symbol. Thus it is not a byte of the value.

The bytes of `stat.beam` are the last three bytes of the status text.
They are also bytes of `val.stat.text`. The same applies to a frequency
and to the bytes `!x!` in the text.

The power of APRS12c is a table of 27 codes (p. 105/81). Each row of the
table is 10 · `k`² watts, where `k` is the place of the row, from 1. The
formula above gives the same numbers (derived).

The bytes `!x!` in the status text are a
[`cmt.noarchive`](02-fields.md#cmt.noarchive) token. The value rule
[val.cmt.noarchive](10-values.md#val.cmt.noarchive) gives the flag.

## 4. Locator and symbol

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.stat.loc"></a>`val.stat.loc` | Maidenhead locator | [`grid.loc`](03-position.md#grid.loc) inside [`stat.grid`](09-other.md#stat.grid) | All bytes of the token. | Byte string, 4 or 6 bytes | p. 105/81, p. 106/82 |

The symbol after the locator has the tokens `sym.table` and `sym.code`.
The value rule [val.sym](10-values.md#val.sym) gives its value.

This file gives the locator as its bytes. It gives no latitude and no
longitude for it. That conversion needs the definition of the Maidenhead
system, and this project pins no version of it yet
([README](README.md), general rule 5).

## 5. Effect of findings

This table gives the effect of each finding that concerns a value of
sections 3 and 4. For `sym.table`, `sym.code` and `time.dhm`, the table
of [10-values section 10](10-values.md#10-effect-of-findings) applies. A
token that has no row has only findings with the effect `kept`.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `grid.loc` | `syntax` (a lower-case letter) | Locator | **[agreed]** `kept`: the bytes as the packet has them |
| `stat.text` | `syntax` (a byte that is not a text byte) | Status text | `kept`: the value is a byte string |
| `stat.text` | `value` (the text is too long) | Status text | `kept` |

**[agreed]** A receiver can get the letters of a locator in lower case
(p. 105/81). Thus the locator keeps its value in both modes. The decoder
does not change the case. The `syntax` finding of the tokenizer stays.

## 6. Catalogue

This file adds no row. The note of the locator is
[amb.stat.grid](09-other.md#amb.stat.grid).

## 7. Reviewed exceptions

None.

## 8. Open items

- The position of a locator. It waits for a pinned definition of the
  Maidenhead system.
- Whether `val.stat.text` leaves out the bytes of `stat.beam`.
