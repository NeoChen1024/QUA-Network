# Values of station capabilities

| | |
|---|---|
| Status | Draft. Not frozen. A paragraph, value rule or catalogue row of this file is **[proposed]** if it has no other label. An **[agreed]** item is a decision of the author. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of a station capabilities packet give
values ([09 section 3](09-other.md#3-station-capabilities)). The tokens
come from [09](09-other.md). This file adds no token and changes no
finding. The rule prefix is `val`.

## 2. Conventions

The conventions of [10-values section 2](10-values.md#2-conventions) apply
to this file. These are the terms, the value tables, the findings that
concern a value, and the effects.

## 3. Capabilities

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.cap.name"></a>`val.cap.name` | Name of a capability | [`cap.token`](09-other.md#cap.token) | All bytes of the token. | Byte string | p. 101/77 |
| <a id="val.cap.value"></a>`val.cap.value` | Value of a capability | [`cap.value`](09-other.md#cap.value) | All bytes of the token. | Byte string | p. 101/77 |

**[agreed]** The name and the value of a capability are byte strings.
This file gives no number for a value, also not for the counts `MSG_CNT`
and `LOC_CNT`. APRS12c defines three capabilities only (p. 101/77), and
packets have many others.

Each `cap.item` token gives one capability. A capability has a name. It
has a value only if it has a `cap.value` token.

The tokens `cap.sep` and `cap.pad` have no value. The bytes of `cap.pad`
are not bytes of the name or of the value
([amb.cap.form](09-other.md#amb.cap.form)).

An empty capability has no `cap.item` token. It gives no capability.

## 4. Effect of findings

This table gives the effect of each finding that concerns a value of
section 3. A token that has no row has only findings with the effect
`kept`.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `cap.item` | `syntax` (only `SP`) | That capability | `none` |
| `cap.token` | `syntax` (only `SP` before `'='`) | That capability | `none` |
| `cap.value` | `syntax`, and the capability has no `cap.value` token (nothing after `'='`) | That capability | `none` |
| `cap.value` | `syntax`, and the capability has a `cap.value` token (a count with a byte that is not a digit) | That capability | `kept`: the value is a byte string |
| `cap.pad` | `ambiguous` ([amb.cap.form](09-other.md#amb.cap.form)) | That capability | `kept`: the name and the value are the bytes without the padding |

A finding concerns a capability if its offset is in the `cap.item` token
or at its end.

## 5. Catalogue

This file adds no row.

## 6. Reviewed exceptions

None.

## 7. Open items

- Whether the counts of an IGate have numbers as values.
- Whether a capability with a name and a `syntax` finding on its value
  keeps its name.
