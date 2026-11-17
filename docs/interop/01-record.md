# Record of a legacy packet

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Rationale | [RFC draft 0](../rfc/qua-network-rfc-0.md): [3.2](../rfc/qua-network-rfc-0.md#32-non-goals), [5.3](../rfc/qua-network-rfc-0.md#53-numeric-and-text-rules), [5.6](../rfc/qua-network-rfc-0.md#56-symbols), [Appendix E](../rfc/qua-network-rfc-0.md#appendix-e-divergence-catalogue) |
| Values | [docs/legacy/10-values.md](../legacy/10-values.md) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the record that the decoder gives for one legacy
packet. It specifies the envelope and the position body. The position body
covers position reports (uncompressed and compressed), DF reports, Mic-E,
Objects, Items and complete weather reports. [02-object.md](02-object.md)
specifies the object body. [03-weather.md](03-weather.md) specifies the
weather body. [04-telemetry.md](04-telemetry.md) specifies the telemetry
body and the telemetry definition body. [05-status.md](05-status.md)
specifies the status body. [06-message.md](06-message.md) specifies the
message body and the bulletin body. [07-frequency.md](07-frequency.md)
specifies the frequency body. [08-capabilities.md](08-capabilities.md)
specifies the capabilities body.
The other uses get their bodies later ([README section 5](README.md#5-open-items)).

## 2. Input

**[proposed]** The input of the decoder is one TNC2 line, as raw bytes.
The input can also give the received time and its resolution. For a
corpus record, the received time is the logged time. Its resolution is
0.001 s, the resolution of the logged decimal. This is not the accuracy of
the time.

**[proposed]** The decoder runs the tokenizer on the line. Then it applies
the value rules of the value files of docs/legacy to the tokens
([10-values](../legacy/10-values.md),
[11-values-object](../legacy/11-values-object.md),
[12-values-weather](../legacy/12-values-weather.md),
[13-values-telemetry](../legacy/13-values-telemetry.md),
[14-values-status](../legacy/14-values-status.md),
[15-values-message](../legacy/15-values-message.md),
[16-values-frequency](../legacy/16-values-frequency.md),
[17-values-capabilities](../legacy/17-values-capabilities.md)). It MUST NOT read a value from bytes outside the tokens that the value rule
names.

**[proposed]** If the line is a third-party packet, the record describes
the inner packet. The envelope gives the outer header in `outer`.

## 3. Modes

**[proposed]** The decoder runs in one of two modes. Each record states
its mode. [10-values section 10](../legacy/10-values.md#10-effect-of-findings)
gives the effect of each finding on a value.

| Effect | Strict mode | Permissive mode |
|---|---|---|
| `kept` | The value. | The value. |
| `computable` | No value. `why` gives the findings. | The value. `mark` gives the findings. |
| `none` | No value. `why` gives the findings. | No value. `why` gives the findings. |

**[proposed]** The modes apply to each value separately. A record in
strict mode can have values and no-value objects together.

**[agreed]** Permissive mode also applies repairs (3.1). A repair is not
an interpretation of APRS12c.

**[proposed]** The finding kinds have these consequences in both modes:

- Each finding has the effect that 10-values section 10 gives it. Most
  `unstated`, `obsolete`, `discouraged` and `is-only` findings have the
  effect `kept`.
- **[agreed]** An `ambiguous` finding does not remove a value in strict
  mode. The decoder gives the value of the narrowest interpretation
  ([docs/legacy README section 3.1](../legacy/README.md#31-general-rules)).
  If no interpretation is the narrowest, 10-values gives the effect.
- Every finding stays in `findings`.
- Verdict `unknown-format`: The record has no body. The information field
  is in `undecoded`.

The verdict of the tokenizer does not change between the modes, unless
a repair applies (3.1).

### 3.1 Repairs

**[agreed]** Permissive mode applies repairs. Strict mode applies no
repair. A repair is not an interpretation of APRS12c, and it is not a
part of [docs/legacy](../legacy/README.md).

**[agreed]** A repair is for bytes of a sender that break a format that
APRS12c specifies. Each repair has an ID that starts with `repair.`.
Each repair names the entry of the
[divergence catalogue](../legacy/divergence/README.md) that records
these bytes.

**[agreed]** A repair states the bytes that it applies to. It states
the tokens that the tokenizer gives for these bytes in place of the
tokens of docs/legacy. A repair can leave the tokens as they are. In
permissive mode, the tokens, the findings and the verdict of a record
are those of the tokenizer with the repairs.

**[proposed]** A repair gives the effect `computable` to each value that
it names. The mark of such a value is the ID of the repair.

| ID | Bytes | Tokens with the repair | Values with the mark | Entry |
|---|---|---|---|---|
| <a id="repair.overlay-lowercase"></a>`repair.overlay-lowercase` | A table byte `'a'`–`'j'` in `sym.table` or `mice.sym.table`. | The tokens of docs/legacy. The `syntax` finding of the table byte stays. | The symbol. | [div.overlay-lowercase](../legacy/divergence/11-overlay-lowercase.md) |
| <a id="repair.humidity-width"></a>`repair.humidity-width` | In weather data, an `h` at a place where a weather field can start, with three digits after it. | One `wx.hum` token of 4 bytes. The tokenizer reads the weather fields after it. | The humidity. Each weather field, the software code and the unit code after the token. | [div.humidity-width](../legacy/divergence/04-humidity-width.md) |

**[agreed]** With `repair.overlay-lowercase`, the table byte gives the
overlay `'0'`–`'9'`, as [val.sym](../legacy/10-values.md#val.sym) gives
it for the compressed format. RFC 5.6 requires this conversion of a
gateway. The `syntax` finding of the table byte has no effect on the
symbol. The mark of the symbol is the ID of the repair.

An earlier draft gave this rule in section 3, with no ID. The mark of
the symbol was then the `syntax` finding.

**[agreed]** The humidity of `repair.humidity-width` is the number of
the three digits. The range of
[val.wx.hum](../legacy/12-values-weather.md#val.wx.hum) applies: 1 to
100. A number outside the range gives no value
([10-values section 2.4](../legacy/10-values.md#24-effects)). Thus the
bytes `h255` and `h000` give no humidity. The three bytes `000` are not
100. Only the two bytes `00` are 100.

**[agreed]** The comment has no mark of a repair. With
`repair.humidity-width`, the comment is the bytes after the weather data
that the tokenizer reads with the repair. It can be different from the
comment of strict mode. The author's reason: APRS12c says too little
about a comment for a mark to have a clear meaning there.

Without the repair, the bytes `h100` are the humidity 10, and the
weather data ends at the last `0`
([06 section 10](../legacy/06-weather.md#10-reviewed-exceptions)).
Strict mode gives this.

The repair can take a byte that the sender did not mean as a digit of
the humidity: the first byte of a tail or of a comment that starts with
a digit, after a humidity of two digits.

An earlier draft had no repairs. The tokenizer itself read `h100`, and
`h` with three digits that start with `0`, as a reviewed exception of
docs/legacy, with the finding `ambiguous`. The author dropped that
design. Its reasons did not agree with the general rules of docs/legacy.

## 4. Representation

### 4.1 Byte strings

**[proposed]** The decoder does not decode a byte string. In JSON, a byte
string is a string in which each byte becomes the character with the same
number, from U+0000 to U+00FF. A reader gets the bytes back by encoding the string
as ISO 8859-1. The tokenizer uses the same rule for `--json`. Thus a UTF-8
comment shows as several characters for one character of the sender.

### 4.2 Value objects

**[proposed]** Each value of a record is a JSON object of one of these
kinds:

| Kind | Members | Content |
|---|---|---|
| Quantity | `v`, `res`, `from` | `v` is the value in the record unit of the field (4.3). `res` is the resolution, in the same unit. Both are numbers (4.6). |
| Flag | `flag`, `from` | `true` or `false`. |
| Flags | `flags`, `from` | A list of `true` and `false`, in the order that the field states. |
| Code | `code`, `from` | A string or an integer, as the value rule states. |
| Bytes | `bytes`, `from` | A byte string (4.1). |
| No value | `why`, `from` | The value is absent for a reason. |

`from` is the provenance (4.4). Each kind can also have `mark` (section 3).
`mark` is a list. Each item is a finding, as `[rule, kind, offset]`, or
the ID of a catalogue row whose effect is `computable`, for example
`"amb.val.calm"`, or the ID of a repair (3.1), for example
`"repair.humidity-width"`.

A quantity has no member that names its record unit. Section 4.3 fixes the
record unit of each field. A quantity also has no integer count. The count of
10-values stays in the bytes of `line`.

A field can be a list of value objects, for example `analog` of the
telemetry body. Each item is then a value object of its own, with its own
`from`.

Three parts of a record are not plain value objects:

- An item of `altitude` is a quantity that also has `ref` (section 7).
- `report_time` (section 6) and `symbol` (section 7) are objects with
  their own members. If one of them has no value, it is a no-value object.
- A value object inside the `values` of an extension has no `from`. It
  takes the `from` of its item (section 7).

`why` is a list. Each item is one of these:

- a finding of the tokenizer, as `[rule, kind, offset]`;
- the ID of a catalogue row, for example `"amb.val.micefix"`;
- the string `"unknown"`, if APRS12c gives the bytes the meaning
  "unknown", for example `000/000`;
- **[proposed]** the ID of the value rule, for example
  `"val.mice.msgcap"`, if the value rule itself gives no value and no
  finding or catalogue row applies. Examples are the type bytes `'>'` and
  `']'`, N = 0 in NRQ, a DF station that is not known, and a half `'...'`
  of `ext.csespd`.

If the format of the packet has no token for a field, the record leaves
the field out. If the format has the field, and the token is missing
because the packet ends early, the field is a no-value object. Its `why`
gives the `syntax` finding.

**[proposed]** That finding is the last `syntax` finding in the
information field. The tokenizer stopped there. An item of `altitude`
with no value is a no-value object without `ref`.

### 4.3 Units

**[agreed]** The record gives each quantity in the record unit that this
section fixes. QUA Network does not use the units of APRS, and in
particular not its non-linear codes. The record states the value of a
quantity, not the form of its bytes. Round-trip accuracy with APRS is not
a goal.

**[agreed]** If the specification names the unit of a quantity
([docs/spec/06-numbers-units](../spec/06-numbers-units.md#3-units)),
the record unit is that unit:

| Quantity | Record unit |
|---|---|
| Latitude, longitude | degree |
| Altitude | metre |
| Speed, wind speed, gust | kilometre per hour |
| Temperature | degree Celsius |
| Pressure | hectopascal |

**[agreed]** The specification names no unit for the other quantities of
a record.
For each, this file applies the rules of RFC 5.3: the SI unit, or a unit
of daily metric use if the SI unit is not practical. Rain and snowfall
have the same unit.

| Quantity | Record unit | Rule of RFC 5.3 |
|---|---|---|
| Height above the average terrain | metre | SI unit |
| Power | watt | SI unit |
| Luminosity | watt per square metre | SI unit |
| Time | second | SI unit |
| Tone | hertz | SI unit |
| Range | kilometre | Practical unit |
| Frequency, transmit offset | megahertz | Practical unit |
| Rain, snowfall | millimetre | Practical unit |

**[agreed]** These quantities keep the units below:

- Angles are in degrees, not in radians.
- Gain, signal strength and beacon rate keep the units of 10-values: dBi
  or dB, S-points and beacons per hour.
- Humidity is in percent ([03-weather section 3.1](03-weather.md#31-units)).

**[agreed]** One quantity has one record unit in every body. A quantity
is one kind of use, as in the specification. Height, range and rain are
lengths, and they are three quantities.

**[proposed]** No value object names a unit or a prefix.

**[agreed]** A quantity keeps its resolution. The resolution is
information of the packet, not a form of its bytes.

**[agreed]** The conversion to the record unit is in this file. 10-values
keeps the units of APRS12c, because it is the interpretation of APRS12c.

An earlier draft gave each quantity as the integer count of 10-values,
with its unit and its step. The author dropped it, for the reasons in the
first item of this section.

An earlier draft gave each quantity in an SI unit: speed in metres per
second, temperature in kelvin, pressure in pascals, and range, rain and
snowfall in metres. RFC 5.3 then allowed a practical unit. The author
asked for the units of RFC 5.3 in the record.

**[proposed]** 10-values gives most quantities as an integer count with a
step in counts. This file calls the count `n` and the step `w`. For a
non-linear unit, this file calls the code `k`: the integer that the
formula of 10-values takes. The record computes `v` and `res` with the
table below. If 10-values states no step for a value, the step is 1.

| Unit of 10-values | Record unit | `v` | `res` |
|---|---|---|---|
| 1/6000 degree | degree | `n` / 6000 | `w` / 6000 |
| 1/60000 degree | degree | `n` / 60000 | `w` / 60000 |
| 1/6000000 degree | degree | `n` / 6000000 | `w` / 6000000 |
| 1/380926 degree | degree | `n` / 380926 | `w` / 380926 |
| 1/190463 degree | degree | `n` / 190463 | `w` / 190463 |
| degree | degree | `n` | `w` |
| 45 · `k` degrees (directivity) | degree | 45 · `k` | 45 |
| knot | kilometre per hour | `n` · 1.852 | `w` · 1.852 |
| 1.08^`k` − 1 knots (compressed speed) | kilometre per hour | (1.08^`k` − 1) · 1.852 | 0.08 · 1.08^`k` · 1.852 |
| foot | metre | `n` · 0.3048 | `w` · 0.3048 |
| 1.002^`k` feet (compressed altitude) | metre | 1.002^`k` · 0.3048 | 0.002 · 1.002^`k` · 0.3048 |
| 10 · 2^`k` feet (PHG and DFS height) | metre | 10 · 2^`k` · 0.3048 | 10 · 2^`k` · 0.3048 |
| metre | metre | `n` | `w` |
| mile | kilometre | `n` · 1.609344 | `w` · 1.609344 |
| 2 · 1.08^`k` miles (compressed range) | kilometre | 2 · 1.08^`k` · 1.609344 | 0.16 · 1.08^`k` · 1.609344 |
| 2^`k` miles (DF range) | kilometre | 2^`k` · 1.609344 | 2^`k` · 1.609344 |
| `k`² watts (PHG power) | watt | `k`² | 2 · `k` + 1 |
| dBi | dBi | `n` | `w` |
| dB | dB | `n` | `w` |
| S-point | S-point | `n` | `w` |
| beacons per hour | beacons per hour | `n` | `w` |
| minute of time (DHM timestamp) | second | Section 6 | 60 · `w` |
| second of time (HMS timestamp) | second | Section 6 | `w` |

**[proposed]** For a linear unit, `res` is `w` times the factor of the
row. A position with ambiguity has the step of its level. Thus its `res`
is the size of the blanked digits.

**[proposed]** For a non-linear unit, `res` is the value of the next code
minus the value of this code. The rows above give this difference. For
the highest code, the formula of the row with `k` + 1 gives `res` in the
same way.

A value in degrees says nothing about the datum. The position body gives
the datum.

**[agreed]** A mile is the statute mile, 1.609344 km. APRS12c names no
kind of mile at the range fields. Its units conversion table gives the
mile as 1.609344 km and lists the nautical mile separately (p. 149/125,
[amb.val.miles](../legacy/10-values.md#amb.val.miles)).

**[proposed]** The factors of the knot, the foot and the mile come from
the units conversion table of APRS12c (p. 149/125). The table gives the
knot as 0.51444 m/s with a repeating last digit. That is 1852 / 3600 m/s,
or 1.852 km/h (derived). RFC 5.3 gives the same factor.

**[proposed]** A gateway rounds `v` to the integer scale or to the decimal
number of the specification. For a quantity that the specification names,
the gateway does not convert the unit. The rounding rule belongs to the gateway mapping
([README section 5](README.md#5-open-items)).

### 4.4 Provenance

**[proposed]** `from` lists the tokens that a value uses, as
`[rule, start, end]`. Start and end are the byte offsets of the tokenizer
in `line`. If a value uses all children of a token, `from` can name the
token instead of the children. A value that comes from the absence of a
token has an empty `from`, for example the default datum.

### 4.5 Notes

**[proposed]** `notes` lists the catalogue rows that apply to the values
of the record, as `[row ID, field]`. The field is a path such as
`"position.lat"`. A value in an extension has the path
`position.extensions[i].values.<name>`, where `i` is the index of the
item, from 0. A row of [10-values section 11](../legacy/10-values.md#11-catalogue)
or of another file of docs/legacy can be a note, for example
[amb.lat.null](../legacy/02-fields.md#amb.lat.null).

**[proposed]** A note applies only to a value that the record gives. A
no-value object gives its catalogue rows in `why`. The notes follow the
order of the fields of the object body, then of section 7, then of the
weather body, then of the telemetry body, then of the status body, then
`report_time`.
[03-weather section 3.2](03-weather.md#32-notes) lists the notes of the
weather body. [04-telemetry section 3.2](04-telemetry.md#32-notes) lists
the note of the telemetry body. Each pair occurs
once. The decoder gives these notes:

| Row | Field | Condition |
|---|---|---|
| `amb.val.ambiguity` | `lat`, `lon` | The step of the base position is more than one count. The decoder tests this before it applies a DAO. |
| `amb.lat.null` | `lat`, `lon` | An uncompressed position where both counts are 0. |
| `amb.val.minutes` | `lat`, `lon` | A `computable` value from tens of minutes 6 to 9. |
| `amb.val.daobase` | `lat`, `lon` | A DAO with precision bytes, and a compressed position or a level above 0. |
| `amb.val.daorange` | `lat`, `lon` | The base-91 digit of the DAO for the coordinate is 91. |
| `amb.val.datum` | `datum` | `"default"`, or a letter other than `W`, `N` and `O` in either case. |
| `amb.val.altref` | `altitude` | A comment altitude or a compressed altitude. |
| `amb.val.altitudes` | `altitude` | More than one item with a value. |
| `amb.val.course0` | `course` | A compressed course 0. |
| `amb.val.bearing` | `bearing` | Always. |
| `amb.val.dfsgain` | `gain` of `val.ext.dfs` | Always. |
| `amb.val.phgcodes` | `height`, `rate` | A height code after `';'`, or a rate code after `'A'`. |
| `amb.val.timewindow` | `report_time` | A `utc` from a timestamp. |
| `amb.val.localtime` | `report_time` | The zone is local. |
| `amb.obj.name` | `name` of the object body | An Object name of nine `SP` bytes, in permissive mode. |
| `amb.val.objtime` | `report_time` | The form `"received"` in a record of an Object or an Item. |

The rows `err.val.cmpspeed` and `err.val.daostep` have no effect on
values. Thus they are not notes. `amb.val.micefix` is an item of `why`.

### 4.6 Numbers

**[agreed]** `v` can be a floating-point number.

**[proposed]** `v`, `res`, `received` and the `utc` and `res` of
`report_time` are JSON numbers. Each can have a fraction. The decoder
computes them as IEEE 754 binary64 numbers ("doubles").

**[proposed]** Each number is the double nearest to the exact result of
its formula, as far as the implementation can compute it. Two
implementations can differ by several units in the last place.

**[proposed]** A tool that writes records MUST write each number with
enough digits that a reader gets the same double back. It can write a
number with no fraction without a decimal point. A reader treats `88` and
`88.0` as the same number.

**[agreed]** A comparison of two records uses this rule for the numbers
of a quantity or of `report_time`:

- `r` is the smaller of the two resolutions.
- Two values `v` agree if they differ by less than `r` / 1000.
- Two resolutions agree under the same condition.
- `received` agrees under the same rule, with the resolution of the
  received time.

**[proposed]** Other members agree only if they are equal. Examples are
codes, flags, byte strings and the fields of a timestamp.

## 5. Envelope

**[proposed]** Every record has these fields:

| Field | JSON | Content |
|---|---|---|
| `record` | Integer | The layout of this file. 0 while this file is a draft. |
| `mode` | `"strict"` or `"permissive"` | Section 3. |
| `line` | Byte string | The TNC2 line, as the input gives it. |
| `received` | Number or `null` | The received time, in seconds since the Unix epoch. It can have a fraction (4.6). |
| `source` | Byte string | The bytes of `addr.src`, or of `tp.src` for a third-party packet. |
| `destination` | Byte string | The bytes of `addr.dest`, or of `tp.dest`. |
| `path` | List of byte strings | One item for each path entry, in order: the bytes between the separators, with the `'*'` if the entry has one. For a third-party packet, the entries of `tp.net` and `tp.gate`. |
| `outer` | Object | Only for a third-party packet: `source`, `destination` and `path` of the outer header. |
| `uses` | List of strings | The names of the uses of the packet. Each name is the key of a body. The names are `"object"`, `"position"`, `"weather"`, `"telemetry"`, `"telemetry_definition"`, `"status"`, `"message"`, `"bulletin"`, `"capabilities"` and `"frequency"`, in this order. The list is empty if the record has no body. |
| `format` | String | The rule ID of the identifier token, for example `pos.dti`, `mice.dti` or `wx.pos`. |
| `verdict` | String or `null` | The verdict of the tokenizer. `null` if the tokenizer has no reader for the format. |
| `findings` | List | Every finding of the tokenizer, as `[rule, kind, offset]`. |
| `report_time` | Object | Section 6. |
| `object` | Object | The object body ([02-object](02-object.md)). Present if the identifier is `obj.dti`, `item.dti` or `wx.obj`. |
| `position` | Object | The position body (section 7). Present if the identifier is `pos.dti`, `mice.dti`, `obj.dti`, `item.dti`, `wx.pos` or `wx.obj`. |
| `weather` | Object | The weather body ([03-weather](03-weather.md)). Present for a weather report. |
| `telemetry` | Object | The telemetry body ([04-telemetry](04-telemetry.md)). Present for a telemetry report and for a packet with a base-91 block. |
| `telemetry_definition` | Object | The telemetry definition body ([04-telemetry](04-telemetry.md#4-telemetry-definition-body)). Present if the identifier is `tlm.def.dti`. |
| `status` | Object | The status body ([05-status](05-status.md)). Present if the identifier is `stat.dti`. |
| `message` | Object | The message body ([06-message](06-message.md)). Present if the identifier is `msg.dti`. |
| `bulletin` | Object | The bulletin body ([06-message](06-message.md#4-bulletin-body)). Present if the identifier is `bln.dti` or `nws.dti`. |
| `capabilities` | Object | The capabilities body ([08-capabilities](08-capabilities.md)). Present if the identifier is `cap.dti`. |
| `frequency` | Object | The frequency body ([07-frequency](07-frequency.md)). Present if the text of the packet has a frequency specification. |
| `notes` | List | Section 4.5. |
| `undecoded` | List | Each token of the information field that no value rule reads, as `[rule, start, end]`. The bytes are in `line`. The list includes such tokens inside `cmt.text`. `cmt.text` itself is in the body. Residue is listed. |

**[agreed]** The record names its uses, in `uses`.

**[proposed]** A record has one body for each use of the packet. One
packet can have more than one use, so `uses` is a list.

**[agreed]** A body does not contain another body. An Object has the uses
`object` and `position`. A weather report with a position has the uses
`position` and `weather`. Thus the position body is the same for every
format that has a position.

An earlier draft had no field for the use. The presence of a body stated
the use. The author prefers a name.

**[proposed]** For a third-party packet, `path` has every entry of the
inner header after the destination. These are the `tp.path` entries,
then `tp.net` and `tp.gate`. For nested third-party packets, the record
describes the innermost packet. `outer` gives the header of the line.

**[proposed]** If the line has no `':'`, the tokenizer gives no header
tokens. Then `format`, `source` and `destination` are `null`, and `path`
is empty. If a header has no `'>'`, `source` and `destination` are
`null`, and `path` is empty.

**[proposed]** `undecoded` lists the outermost tokens that the body does
not read. A token is read if a value rule reads it, or if it is the
comment of the body. The identifier token of a record with a body is also
read: `format` gives it. A token that contains a read token is also read. A
record with no body reads no token. If `c` of a compressed block is
`SP`, no value rule reads `cmp.cs.none` and `cmp.t` (10-values section 6).

## 6. Report time

**[proposed]** `report_time` has these members:

| Member | Content |
|---|---|
| `form` | `"dhm"`, `"hms"`, `"mdhm"` or `"received"`. |
| `month`, `day`, `hour`, `minute`, `second` | The fields of the timestamp, as integers ([val.time.dhm](../legacy/10-values.md#val.time.dhm), [val.time.hms](../legacy/10-values.md#val.time.hms), [val.time.mdhm](../legacy/12-values-weather.md#val.time.mdhm)). |
| `zone` | `"utc"` or `"local"`. |
| `utc` | Seconds since the Unix epoch, or absent. The number can have a fraction (4.6). It counts days of 86400 seconds and no leap seconds, as POSIX time does. |
| `res` | The resolution of `utc`, in seconds: 60 for DHM and MDHM, 1 for HMS, the resolution of the received time for `"received"`. Absent if `utc` is absent. |
| `from` | Provenance (4.4). |
| `mark` | Permissive mode only (section 3). |

**[proposed]** If the packet has no timestamp, `form` is `"received"`. Then
`utc` is the received time (p. 39/23). If there is no received time,
`report_time` is absent.

**[proposed]** If a timestamp has no value (section 3), `report_time` is a
no-value object (4.2).

**[proposed]** If the format has no body yet and has a timestamp token,
`report_time` is absent. No value rule applies to that timestamp yet.

**[agreed]** An Object without a timestamp and an Item have the form
`"received"`, with the note `amb.val.objtime`
([02-object section 4](02-object.md#4-position-body-and-report-time)).

**[agreed]** APRS12c gives no date for a timestamp
([amb.val.timewindow](../legacy/10-values.md#amb.val.timewindow)). The
decoder finds the `utc` of a UTC timestamp as follows:

1. For DHM, the candidates are the day and time in three months. These
   are the month of the received time, the month before and the month
   after. The decoder leaves out a candidate on a day that the month does
   not have.
2. For HMS, the candidates are the time on three days. These are the day
   of the received time, the day before and the day after.
3. The decoder takes the candidate nearest to the received time. If two
   are equally near, it takes the earlier candidate.

If there is no received time, or the zone is local, `utc` is absent. A
`utc` that the decoder finds from a timestamp has the note
`amb.val.timewindow`. The date is a choice of this file. APRS12c and
10-values give none.

## 7. Position body

**[proposed]** The position body has these fields. Each value comes from
the value rule in the last column. Section 4.3 gives the conversion to the
record unit.

| Field | Kind | Content | Value rule |
|---|---|---|---|
| `lat` | Quantity | Latitude in degrees. With an applied DAO, at the resolution of the DAO. | `val.lat`, `val.cmp.lat`, `val.mice.lat`, `val.dao.lat` |
| `lon` | Quantity | Longitude, as `lat`. | `val.lon`, `val.cmp.lon`, `val.mice.lon`, `val.dao.lon` |
| `ambiguity` | Code | The level, 0 to 4. Absent for a compressed position. | `val.lat.amb`, `val.mice.lat` |
| `datum` | Code | The `D` byte of the DAO as a byte string, or `"default"`. | `val.dao.datum` |
| `altitude` | List of quantities | Every altitude of the packet, in metres. Each item also has `ref`: `"msl"` or `"unstated"`. | `val.cmt.alt`, `val.cmt.alt.neg`, `val.cmp.alt`, `val.mice.alt` |
| `course` | Quantity | Course in degrees. | `val.ext.csespd`, `val.cmp.crs`, `val.mice.crs` |
| `speed` | Quantity | Speed in kilometres per hour. | `val.ext.csespd`, `val.cmp.spd`, `val.mice.spd` |
| `symbol` | Object | `chars`: the table byte and the code byte, in that order, as a byte string. `classic`: the number of RFC 5.6 as an integer, if the symbol has one. `from`. | `val.sym` |
| `messaging` | Flag | Messaging flag. Absent for an Object or an Item. | `val.pos.dti`, `val.mice.msgcap` |
| `fix` | Code | Fix age: `"current"` or `"old"`. | `val.mice.dti`, `val.cmp.t` |
| `comment` | Bytes | The bytes of the `cmt.text` token, without the tokens of section 7.1. In Mic-E, the `cmt.text` inside `mice.status`. | — |
| `extensions` | List | Values that have no field of their own (below). | — |

### 7.1 Comment

**[agreed]** The `comment` leaves out the bytes of each altitude token
that is directly inside the `cmt.text` token: `cmt.alt` and `cmt.alt.neg`.
The `altitude` field has their values. A data extension is before the
`cmt.text` token. Thus the `comment` does not have its bytes.

**[proposed]** The `comment` also leaves out the bytes of each `cmt.dao`
token and of each `tlm.b91` token that is directly inside the `cmt.text`
token.

**[agreed]** The `comment` leaves out a `/` after a data extension. The
rule has these conditions:

- a data extension token, with a rule ID that starts with `ext.`, ends
  where the `cmt.text` token starts;
- after the removal of the tokens above, the first byte that remains is
  `/`.

The record removes that one byte. An example is `PHG5132/Digi`: the
`comment` is `Digi`.

**[proposed]** These rules apply to the `comment`:

- The `comment` has the other bytes of the `cmt.text` token, in their
  order. The record does not remove a space.
- The record leaves out a token of the list also if its field has no
  value. The `line` keeps the bytes.
- If no byte remains, the record leaves out `comment`.
- `from` names the `cmt.text` token.
- The `comment` keeps the bytes of a frequency specification
  ([07-frequency section 6](07-frequency.md#6-open-items)).

**[proposed]** These rules apply only to the `comment` of the position
body. The `comment` of another body has all bytes of its token.

Dropped: an earlier draft gave all bytes of the `cmt.text` token. The
altitude was then in two fields of the record. The parsers of
[09-comparison](09-comparison.md) remove it from the comment. They also
remove the `/` after a data extension
([div.comment](../legacy/divergence/01-comment.md)).

### 7.2 Other rules

**[agreed]** If a position has ambiguity, `v` is the edge of the box
that is nearest to the equator or to the prime meridian. A blanked digit
counts as 0 ([amb.val.ambiguity](../legacy/10-values.md#amb.val.ambiguity)).
`res` is the size of the box.

**[proposed]** The classic symbol number follows RFC 5.6. `c` is the code
byte. `d` is the overlay number of the identifier digit table: 0 for no
overlay, 1 to 10 for `'0'`–`'9'`, 11 to 36 for `'A'`–`'Z'`. The number is:

- primary table: `c` − 33;
- alternate table: 94 + (`c` − 33) · 37 + `d`.

**[proposed]** In a weather report, the wind field takes the place of the
course and the speed. The position body then has no `course` and no
`speed` ([03-weather section 3](03-weather.md#3-fields)).

**[proposed]** The course and the speed come from the fixed part of the
format: `ext.csespd` in the slot, `cmp.cs.crs`, or the Mic-E bytes. An
`ext.csespd` after a compressed block, or in a Mic-E status text, is an
item of `extensions` with the rule `val.ext.csespd`.

**[agreed]** If the timestamp of a position report has a `syntax`
finding, the finding concerns every field of the position body except
`messaging`
([10-values section 2.3](../legacy/10-values.md#23-findings-that-concern-a-value)).
If only byte 7 of the timestamp is wrong, the effect is `computable`. In
all other cases, each of these fields is a no-value object.

**[proposed]** If `val.dao.lat` or `val.dao.lon` gives no value, `lat` or
`lon` is the value of the base position. If `val.dao.datum` gives no
value, `datum` is a no-value object.

**[proposed]** These cases change the fields of the body:

- If `c` of a compressed block is `SP`, the body has no `course`,
  `speed` and `fix`, and no item `val.cmp.t` (10-values section 6).
- If the kind of `cs` is not known, `course` and `speed` are no-value
  objects. Examples are `cmp.cs` with `syntax`, and a block that ends
  early.
- If the byte after the identifier starts no position format
  (`pos.form`), `lat`, `lon` and `symbol` are no-value objects. The body
  then has no `ambiguity` and no `datum`.
- A Mic-E type byte `'>'` or `']'` gives `messaging` as a no-value object.
- A Mic-E emergency gives the item `val.mice.msg` with `kind` only. The
  value rule gives no number for it, so `values` has no `index`.

**[proposed]** An item of `extensions` has these members:

- `rule`: the ID of the value rule, for example `val.ext.phg`;
- `from`: the tokens;
- `values`: an object of named value objects.

**[proposed]** The items are in the order of the first token of their
`from`. An `ext.phgr` token gives two items with the same `from`:
`val.ext.phg`, then `val.ext.phgr`.

**[proposed]** These value rules give extensions. The table gives the
names in `values`, their kinds and their record units.

| Value rule | Name | Kind | Content |
|---|---|---|---|
| `val.ext.csespd` (outside the fixed part) | `course`, `speed` | Quantity | As the fields `course` and `speed`. |
| `val.ext.phg` | `power` | Quantity | Watts. |
| | `height` | Quantity | Metres above the average local terrain. |
| | `gain` | Quantity | dBi. |
| | `directivity` | Quantity or Code | Degrees. The digit 0 gives the code `"omni"`. |
| `val.ext.phgr` | `rate` | Quantity | Beacons per hour. |
| `val.ext.rng` | `range` | Quantity | Kilometres. |
| `val.ext.dfs` | `strength` | Quantity | S-points. |
| | `height`, `gain`, `directivity` | As `val.ext.phg` | The gain is in dB. |
| `val.ext.brgnrq` | `bearing` | Quantity | Degrees. |
| | `hits` | Code | The integer N. |
| | `range` | Quantity | Kilometres. |
| | `quality` | Code | The integer Q. |
| | `station` | Code | `"fixed"` or `"moving"`. |
| `val.cmp.rng` | `range` | Quantity | Kilometres. |
| `val.cmp.t` | `source`, `origin` | Code | The NMEA source and the origin. |
| `val.mice.msg` | `kind`, `index` | Code | The message kind and its number. |
| `val.cmt.noarchive` | `noarchive` | Flag | `true`. |

**[open]** A position body can also need the position in a Mic-E status
text ([amb.mice.extension](../legacy/04-mic-e.md#amb.mice.extension)) and
the symbols of the address fields. Neither has a value rule yet.

## 8. Serialisation

**[proposed]** A tool writes one JSON object per record, one record per
line, in UTF-8. The members are those of sections 5 to 7. Numbers follow
section 4.6. No field name contains the word APRS.

**[proposed]** A record ends at the byte LF. A byte string can contain
U+0085 and other control characters without an escape. Thus a reader
splits the records at LF only.

**[proposed]** The tools that read the tokenizer run under PyPy, where
pyarrow is not available. Thus the record is JSON. A separate tool under
CPython can convert records to Parquet. That tool writes each byte string
as a `binary` column.

## 9. Examples

The tokens and the findings below come from `qua-legacy-tokenize --json`
on the same lines. A standalone Python script computed the values. The
script reads the bytes of each line and applies 10-values and
section 4.3. It uses exact rational arithmetic and then takes the nearest
double. It does not import the project package.

Each example has the received time 1794268920.25 s
(2026-11-10T00:02:00.250Z). The input gives it to 0.001 s. An
example shows one record on several lines for reading.

### 9.1 Uncompressed, with timestamp and ambiguity, strict mode

```json
{"record": 0, "mode": "strict",
 "line": "N0CALL>APZ001,WIDE1-1:@092345z4903.5 N/07201.75W>088/036 Test /A=001234",
 "received": 1794268920.25,
 "source": "N0CALL", "destination": "APZ001", "path": ["WIDE1-1"],
 "uses": ["position"], "format": "pos.dti", "verdict": "conform", "findings": [],
 "report_time": {"form": "dhm", "day": 9, "hour": 23, "minute": 45, "zone": "utc",
                 "utc": 1794267900, "res": 60, "from": [["time.dhm", 23, 30]]},
 "position": {
  "lat": {"v": 49.05833333333333, "res": 0.0016666666666666668, "from": [["lat", 30, 38]]},
  "lon": {"v": -72.02833333333334, "res": 0.0016666666666666668, "from": [["lon", 39, 48], ["lat", 30, 38]]},
  "ambiguity": {"code": 1, "from": [["lat", 30, 38]]},
  "datum": {"code": "default", "from": []},
  "altitude": [{"v": 376.1232, "res": 0.3048, "ref": "unstated", "from": [["cmt.alt", 62, 71]]}],
  "course": {"v": 88, "res": 1, "from": [["ext.csespd", 49, 56]]},
  "speed": {"v": 66.672, "res": 1.852, "from": [["ext.csespd", 49, 56]]},
  "symbol": {"chars": "/>", "classic": 29, "from": [["sym.table", 38, 39], ["sym.code", 48, 49]]},
  "messaging": {"flag": true, "from": [["pos.dti", 22, 23]]},
  "comment": {"bytes": " Test ", "from": [["cmt.text", 56, 71]]},
  "extensions": []},
 "notes": [["amb.val.ambiguity", "position.lat"], ["amb.val.ambiguity", "position.lon"],
           ["amb.val.datum", "position.datum"], ["amb.val.altref", "position.altitude"],
           ["amb.val.timewindow", "report_time"]],
 "undecoded": []}
```

- `lat`: Level 1, so the last digit counts as 0. The count is 49 · 6000 +
  3 · 100 + 50 = 294350, with step 10. `v` is 294350 / 6000 degree, that
  is 49° 03.50' N. `res` is 10 / 6000 degree, that is 0.1 minute.
- `lon`: The level covers offset 7, the digit `'5'`. The count is 72 ·
  6000 + 1 · 100 + 70 = 432170, west, so −432170. `v` is −432170 / 6000
  degree. `res` is as for `lat`.
- `altitude`: The count is 1234 feet, with step 1. `v` is 1234 · 0.3048
  m. `res` is 0.3048 m.
- `course`: The count is 88 degrees, with step 1.
- `speed`: The count is 36 knots, with step 1. `v` is 36 · 1.852 =
  66.672 km/h. `res` is 1.852 km/h.
- `utc`: 2026-11-09T23:45Z is nearer to the received time than the same
  day and time in October or December. `res` is one minute.
- `symbol`: `'>'` is 62, and 62 − 33 = 29.

### 9.2 Compressed, strict mode

The block is the example of APRS12c p. 58/40.

```json
{"record": 0, "mode": "strict",
 "line": "N0CALL>APZ001:=/5L!!<*e7>7P[",
 "received": 1794268920.25,
 "source": "N0CALL", "destination": "APZ001", "path": [],
 "uses": ["position"], "format": "pos.dti", "verdict": "conform", "findings": [],
 "report_time": {"form": "received", "utc": 1794268920.25, "res": 0.001, "from": []},
 "position": {
  "lat": {"v": 49.5, "res": 2.6251817938392235e-06, "from": [["cmp.lat", 16, 20]]},
  "lon": {"v": -72.75000393777269, "res": 5.250363587678447e-06, "from": [["cmp.lon", 20, 24]]},
  "datum": {"code": "default", "from": []},
  "course": {"v": 88, "res": 4, "from": [["cmp.cs.crs", 25, 27]]},
  "speed": {"v": 67.1016865366879, "res": 5.516294922935032, "from": [["cmp.cs.crs", 25, 27]]},
  "symbol": {"chars": "/>", "classic": 29, "from": [["cmp.table", 15, 16], ["cmp.code", 24, 25]]},
  "messaging": {"flag": true, "from": [["pos.dti", 14, 15]]},
  "fix": {"code": "current", "from": [["cmp.t", 27, 28]]},
  "extensions": [{"rule": "val.cmp.t", "from": [["cmp.t", 27, 28]],
                  "values": {"source": {"code": "RMC"}, "origin": {"code": 2}}}]},
 "notes": [["amb.val.datum", "position.datum"]],
 "undecoded": []}
```

- `lat`: `5L!!` is 20 · 91³ + 43 · 91² = 15427503. The count is 34283340
  − 15427503 = 18855837. `v` is 18855837 / 380926 = 49.5 degrees. `res`
  is 1 / 380926 degree.
- `lon`: `<*e7` is 20427156. The count is 20427156 − 34283340 =
  −13856184. `v` is −13856184 / 190463, about −72.750004 degrees. `res`
  is 1 / 190463 degree.
- `course`: `'7'` − 33 = 22. The count is 4 · 22 = 88 degrees, with step
  4.
- `speed`: `'P'` − 33 = 47 = `k`. 1.08^47 − 1 is about 36.232 knots. p.
  57/39 gives 36.2 knots. `v` is (1.08^47 − 1) · 1.852 km/h. `res` is
  0.08 · 1.08^47 · 1.852 km/h.
- `cmp.t`: `'['` − 33 = 58, binary 111010: current fix, source RMC, origin
  2.
- `report_time`: The packet has no timestamp. `utc` is the received time.
  The input gives the time to 0.001 s, so `res` is 0.001 s.

### 9.3 Mic-E with ambiguity, strict mode

The destination is the ambiguity example of APRS12c p. 71/53. The first
nine bytes of the information field are the example of the same page.

```json
{"record": 0, "mode": "strict",
 "line": "N0CALL>T4SQZZ:`(_fn\"Oj/\"4T}",
 "received": 1794268920.25,
 "source": "N0CALL", "destination": "T4SQZZ", "path": [],
 "uses": ["position"], "format": "mice.dti", "verdict": "conform", "findings": [],
 "report_time": {"form": "received", "utc": 1794268920.25, "res": 0.001, "from": []},
 "position": {
  "lat": {"v": 44.516666666666666, "res": 0.016666666666666666, "from": [["dest.mice", 7, 13]]},
  "lon": {"v": -112.11666666666666, "res": 0.016666666666666666,
          "from": [["mice.lon.deg", 15, 16], ["mice.lon.min", 16, 17], ["mice.lon.hun", 17, 18], ["dest.mice", 7, 13]]},
  "ambiguity": {"code": 2, "from": [["dest.mice", 7, 13]]},
  "datum": {"code": "default", "from": []},
  "altitude": [{"v": 61, "res": 1, "ref": "msl", "from": [["mice.alt", 23, 27]]}],
  "course": {"v": 251, "res": 1, "from": [["mice.dc", 19, 20], ["mice.se", 20, 21]]},
  "speed": {"v": 37.04, "res": 1.852, "from": [["mice.sp", 18, 19], ["mice.dc", 19, 20]]},
  "symbol": {"chars": "/j", "classic": 73, "from": [["mice.sym.table", 22, 23], ["mice.sym.code", 21, 22]]},
  "fix": {"code": "current", "from": [["mice.dti", 14, 15]]},
  "extensions": [{"rule": "val.mice.msg",
                  "from": [["mice.dest.a", 7, 8], ["mice.dest.b", 8, 9], ["mice.dest.c", 9, 10]],
                  "values": {"kind": {"code": "standard"}, "index": {"code": 2}}}]},
 "notes": [["amb.val.ambiguity", "position.lat"], ["amb.val.ambiguity", "position.lon"],
           ["amb.val.datum", "position.datum"]],
 "undecoded": []}
```

- `lat`: `T4SQZZ` gives 4, 4, 3, 1 and two blanks, level 2. Byte 4 `'Q'`
  has flag 1, so north. The count is (44 · 60 + 31) · 100 = 267100, with
  step 100. `v` is 267100 / 6000 degree, that is 44° 31' N. `res` is 100
  / 6000 degree, that is 1 minute.
- `lon`: `'('` − 28 = 12, plus 100 because byte 5 `'Z'` has flag 1: 112.
  `'_'` − 28 = 67, minus 60: 7. Level 2 sets the hundredths to 0. Byte 6
  `'Z'` has flag 1, so west. The count is −(112 · 6000 + 7 · 100) =
  −672700. `v` is −672700 / 6000 degree. `res` is as for `lat`.
- `speed`: 10 · 82 + 6 div 10 = 820, minus 800: the count is 20 knots.
  `v` is 20 · 1.852 = 37.04 km/h. `res` is 1.852 km/h.
- `course`: 100 · (6 mod 10) + 51 = 651, minus 400: 251 degrees.
- `altitude`: `"4T` is 1 · 8281 + 19 · 91 + 51 = 10061, minus 10000: the
  count is 61 m, with step 1.
- `val.mice.msg`: bits 1, 0, 1, all standard: 7 − 5 = 2.
- No `messaging`: the status text has no prefix byte.

### 9.4 The two modes on one packet

The line `N0CALL>APZ001:!4963.50Na07201.75W-` gives `value` on `lat` at
offset 17 (tens of minutes `'6'`). It also gives `syntax` on `sym.table`
at offset 23 (`'a'`). The verdict is `syntax`. These are the fields that
differ between the modes:

```json
{"mode": "strict",
 "lat": {"why": [["lat", "value", 17]], "from": [["lat", 15, 23]]},
 "symbol": {"why": [["sym.table", "syntax", 23]], "from": [["sym.table", 23, 24], ["sym.code", 33, 34]]}}

{"mode": "permissive",
 "lat": {"v": 50.05833333333333, "res": 0.00016666666666666666, "from": [["lat", 15, 23]],
         "mark": [["lat", "value", 17]]},
 "symbol": {"chars": "a-", "classic": 539, "from": [["sym.table", 23, 24], ["sym.code", 33, 34]],
            "mark": ["repair.overlay-lowercase"]}}
```

- `lat`: The count is 49 · 6000 + 63 · 100 + 50 = 300350, with step 1.
  `v` is 300350 / 6000 degree, that is 50° 03.50' N. `res` is 1 / 6000
  degree. The permissive record also has the note `amb.val.minutes`.
- `symbol`: With `repair.overlay-lowercase` (3.1), `'a'` gives the
  overlay `'0'`, digit 1. `'-'` − 33 = 12. 94 + 12 · 37 + 1 = 539. The
  `syntax` finding stays in `findings`, and the verdict is `syntax` in
  both modes.
- `lon` is the same in both modes. The count is −432175, so `v` is
  −72.02916666666667 and `res` is 1 / 6000 degree. The finding has the
  rule ID `lat`, so it does not concern `val.lon`.

## 10. Open items

- **[open]** The other uses, the encoder, the gateway mapping and the
  differential tests ([README section 5](README.md#5-open-items)).
- **[proposed]** The order of the names in `uses`: `object`, `position`,
  `weather`, `telemetry`, `telemetry_definition`, `status`, `message`,
  `bulletin`, `capabilities`, `frequency`.
- **[open]** Whether `source` also gives a QUA Network identifier
  ([spec 01 section 8](../spec/01-station-identifier.md#8-mapping-to-an-ax25-address)).
- **[open]** `fix` exists only for the compressed format and Mic-E. A
  report with a timestamp can also be old (p. 39/23). The record does not
  give this as a fix age.
- **[open]** Input from an AX.25 frame, for the radio side of a gateway.
  The decoder reads TNC2 lines only.
- **[open]** For a value with no blanked digits, the record does not state
  whether the sender rounded or truncated. `res` gives the size of the
  interval, not its position.
- **[open]** The names in `values` of each extension (section 7).
- **[open]** An inner header in the AEA form
  ([amb.tp.aea](../legacy/01-frame.md#amb.tp.aea)). The decoder takes
  the first address as `source`, the last as `destination`, and the
  others as `path`.
- **[open]** The headers between the line and the innermost packet of a
  nested third-party packet. The record does not give them.
- **[open]** The report time of a format that has no body yet and has a
  timestamp (section 6).
