# Values of Object and Item fields

| | |
|---|---|
| Status | Draft. Not frozen. A paragraph, value rule or catalogue row of this file is **[proposed]** if it has no other label. An **[agreed]** item is a decision of the author. |
| Reference | `APRS12c.pdf` in submodule `3rdparty/aprsspec`, commit `5830d42f`. The conventions and the general rules are in [README](README.md). |
| Used by | The decoder of [docs/interop](../interop/README.md): `qua-legacy-decode` (package `qua_network.interop`). |

## 1. Scope

This file states how the tokens of an Object report and of an Item report
give values. It covers these formats:

- Object reports ([05 section 2](05-object-item.md#2-object-report));
- Item reports ([05 section 3](05-object-item.md#3-item-report)).

The tokens come from [05](05-object-item.md) and [02](02-fields.md). This
file adds no token and changes no finding. The rule prefix is `val`.

An Object or an Item has a name, a state and a position. This file gives
the value rules of the name and of the state. The value rules of
[10-values](10-values.md) give the values of the position tokens
(section 5).

These parts are outside this file:

- the obsolete Object format
  ([05 section 6](05-object-item.md#6-obsolete-object-format));
- the area descriptor, the corridor and the signpost
  ([05 sections 4 and 5](05-object-item.md#4-area-objects));
- weather and storm data on an Object or an Item
  ([05 section 7](05-object-item.md#7-weather-and-storm-data-on-objects));
- a frequency in the name or in the comment
  ([09 section 7](09-other.md#7-frequency-specification)).

## 2. Conventions

The conventions of [10-values section 2](10-values.md#2-conventions) apply
to this file. These are the terms, the value tables, the findings that
concern a value, and the effects.

A name is a byte string. The decoder does not decode it as text. Names
are case-sensitive (p. 76/58, p. 77/59), so the decoder does not change
the case of a name.

## 3. Name and state

| ID | Value | Tokens | Arithmetic | Unit, step and range | Source |
|---|---|---|---|---|---|
| <a id="val.obj.name"></a>`val.obj.name` | Object name | [`obj.name`](05-object-item.md#obj.name) | The 9 bytes of the token without the `SP` bytes at its end. | Byte string, 0 to 9 bytes | p. 76/58 |
| <a id="val.obj.state"></a>`val.obj.state` | Live or killed | [`obj.state`](05-object-item.md#obj.state) | `'*'`: live. `'_'`: killed. | Flag | p. 76/58 |
| <a id="val.item.name"></a>`val.item.name` | Item name | [`item.name`](05-object-item.md#item.name) | All bytes of the token. | Byte string, 3 to 9 bytes | p. 77/59 |
| <a id="val.item.state"></a>`val.item.state` | Live or killed | [`item.state`](05-object-item.md#item.state) | `'!'`: live. `'_'`: killed. | Flag | p. 77/59 |

The `SP` bytes at the end of an Object name are padding (p. 76/58). A `SP`
at the start of the name or inside it is part of the name. APRS12c
specifies no padding for an Item name. Thus every byte of `item.name` is
part of the name, a `SP` at its end included.

A name of nine `SP` bytes gives an empty name
([amb.obj.name](05-object-item.md#amb.obj.name)). Section 6 gives its
effect.

A killed Object or Item has the same tokens as a live one. The decoder
gives the values of its position.

## 4. Timestamp

An Object can have a timestamp, the token
[`obj.time`](05-object-item.md#obj.time). The token is a `time.dhm` or a
`time.hms`. The value rules [val.time.dhm](10-values.md#val.time.dhm) and
[val.time.hms](10-values.md#val.time.hms) give its values. An Item has no
timestamp (p. 77/59).

The tokenizer accepts an Object without a timestamp
([amb.obj.time](05-object-item.md#amb.obj.time)). **[agreed]** For such an
Object, and for an Item, the time of the report is the received time
([amb.val.objtime](#amb.val.objtime)). The decoder uses the received time
only if its input gives it.

**[agreed]** A `syntax` finding on the timestamp of an Object concerns
every value from a later token of the information field. The rule IDs are `time.dhm`,
`time.hms` and `obj.time`. The effect is that of
[10-values section 2.3](10-values.md#23-findings-that-concern-a-value) for
a position report:

- The timestamp has six digits, and the finding is at offset 6: the effect
  is `computable`.
- All other cases: the effect is `none`.

The name and the state are before the timestamp, and each has a fixed
place. Thus this finding does not concern them.

## 5. Position

The position tokens of an Object or an Item are those of a position
report. These value rules of 10-values apply to them without change:

- the uncompressed position and the level
  ([10-values section 4](10-values.md#4-uncompressed-position));
- the symbol ([section 5](10-values.md#5-symbol));
- the compressed position block
  ([section 6](10-values.md#6-compressed-position-block));
- the data extensions ([section 8](10-values.md#8-data-extensions));
- the fields in a comment
  ([section 9](10-values.md#9-fields-in-a-comment)).

These differences apply:

- An Object or an Item has no messaging flag. `val.pos.dti` does not
  apply.
- Under the area symbol `\l`, the tokenizer reads the area descriptor in
  place of a data extension. This file has no value rule for it. The
  symbol and the position keep their values.
- If the Item or the Object is a weather report,
  [12-values-weather](12-values-weather.md) gives the values of the
  weather tokens.
- A `discouraged` finding on `obj.pos` marks a compressed position in an
  Object. It concerns no value.
- A length finding on the comment (`obj.cmt`, `item.cmt`) concerns no
  value.

## 6. Effect of findings

**[agreed]** The effects of the rows for `unstated` on `obj.name`, for
`value` on `item.name` and for the timestamp are decisions of the author.

This table gives the effect of each finding that concerns a value of
section 3. For the position tokens, the table of
[10-values section 10](10-values.md#10-effect-of-findings) applies. A
token that has no row has only findings with the effect `kept`.

| Token | Finding | Value | Effect |
|---|---|---|---|
| `obj.name` | `syntax` (a byte outside the set, or a short token) | `val.obj.name` | `none` |
| `obj.name` | `unstated` (nine `SP` bytes) | `val.obj.name` | `computable`: the empty name |
| `obj.state` | `syntax` | `val.obj.state` | `none` |
| `item.name` | `syntax` (an empty name, or no `'!'` and no `'_'`) | `val.item.name` | `none` |
| `item.name` | `value` (fewer than 3 bytes, or more than 9 bytes) | `val.item.name` | `computable`: all bytes of the token |
| `time.dhm` | `syntax` at offset 6, after six digits | Every value from a later token | `computable` (section 4) |
| `time.dhm`, `time.hms`, `obj.time` | Another `syntax` | Every value from a later token | `none` (section 4) |

The `discouraged` finding on `item.dti` concerns no value. If the token
`item.state` is missing, `val.item.state` gives no value (10-values
section 2.3).

## 7. Catalogue

The last column of this catalogue tells what the decoder does.

| ID | Pages | What APRS12c leaves open | Class | Rule | What the decoder does |
|---|---|---|---|---|---|
| <a id="amb.val.objtime"></a>`amb.val.objtime` | p. 39/23, p. 76/58, p. 77/59 | A receiver can record the received time of "a report without a timestamp". This sentence is in the chapter of position reports. The chapter of Objects and Items does not repeat it. An Item never has a timestamp. | unstated | 2 | The decoder gives the received time as the time of the report, with this note. |

## 8. Reviewed exceptions

None.

## 9. Open items

- Values of the obsolete Object format, the area descriptor, the corridor
  and the signpost.
- The name of an Object or an Item is not a station identifier. Whether a
  record needs both the name and the source to identify an Object is a
  question of [docs/interop](../interop/02-object.md).
