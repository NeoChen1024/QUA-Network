# Comparison with other parsers

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning that the RFC gives them. A label on a paragraph covers the table that follows it. |
| Rationale | [RFC draft 0](../rfc/qua-network-rfc-0.md): Appendix E |
| Record | [01-record.md](01-record.md) and the body files of this directory |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the comparison of a record with the result that
another parser gives for the same legacy packet. It is steps 1 to 3 of the
method of RFC Appendix E.1. The comparison gives counts and example
packets. It does not decide which side is correct.

This file uses these terms:

| Term | Meaning |
|---|---|
| parser | A program of a third party that decodes legacy packets. |
| adapter | A program of this project that runs one parser on TNC2 lines and writes its results. |
| result | What a parser gives for one packet, as the adapter writes it. |
| view | The fields of a record or of a result that the comparison uses, with one path for each field. |
| path | The name of a field in a view, for example `position.lat`. |

## 2. Parsers

**[agreed]** The comparison starts with two parsers. Each is a submodule
under `3rdparty/`, at a fixed commit:

| Name | Parser | Submodule | Licence, as read in the submodule |
|---|---|---|---|
| `pythonlib` | The Python package aprslib | `3rdparty/aprs-python` | GPL version 2 or later |
| `fap` | The Perl module Ham::APRS::FAP | `3rdparty/perl-aprs-fap` | The terms of Perl: GPL or Artistic License |

**[agreed]** A parser runs as a process of its own. No code of a parser
is in a file of this project.

**[proposed]** The tool prints the commit of each submodule with its
counts. A count is valid for that commit only.

**[open]** The other candidates of RFC Appendix E.1: libfap, the decoder
of Dire Wolf, aprsc, javAPRSlib, Xastir and YAAC.

## 3. Adapters

**[proposed]** Each parser has one adapter. An adapter obeys these rules:

- It reads one packet for each line of its standard input. The line has
  the bytes of the TNC2 line as hexadecimal digits.
- It gives the bytes of the TNC2 line to the public decode function of
  the parser. It does not change them.
- It writes one JSON object for each packet to its standard output, in
  the order of the input.
- It writes the names and the values of the parser as they are. It does
  not convert a unit and does not rename a field.
- It writes a byte above 0x7F as the character that has that number.
  Thus a text of a result compares with a byte string of a record
  ([01-record section 4.1](01-record.md#41-byte-strings)).
- If the parser rejects the packet, the adapter writes the error that the
  parser gives.

**[proposed]** The table gives the decode function and the options:

| Name | Function | Options |
|---|---|---|
| `pythonlib` | `aprslib.parse`, with the line as text | None. |
| `fap` | `Ham::APRS::FAP::parseaprs`, with the line as bytes | None: the defaults of the module. |

**[proposed]** The adapter of `pythonlib` runs on the Python interpreter
that runs the tool. The adapter of `fap` runs on the `perl` of the system.
The module needs the Perl module Date::Calc.

## 4. View of a record

**[proposed]** The view of a record has a path for each field of the
table, if the field has a value. A no-value object gives no path.

| Path | Field of the record | Compared as |
|---|---|---|
| `position.lat`, `position.lon`, `position.course`, `position.speed` | The field of the position body | Number |
| `position.altitude` | The first item of `altitude` that has a value | Number |
| `position.ambiguity` | `code` of `ambiguity` | Equal |
| `position.symbol` | `chars` of `symbol` | Equal |
| `position.messaging` | `flag` of `messaging` | Equal |
| `position.comment` | `bytes` of `comment` | Text |
| `object.name` | `bytes` of `name` | Text |
| `object.live` | `flag` of `live` | Equal |
| `weather.wind_direction`, `weather.wind_speed`, `weather.gust`, `weather.temperature`, `weather.rain_1h`, `weather.rain_24h`, `weather.rain_midnight`, `weather.snow_24h`, `weather.humidity`, `weather.pressure`, `weather.luminosity` | The field of the weather body | Number |
| `message.kind` | `code` of `kind` | Equal |
| `message.addressee`, `message.text`, `message.id` | `bytes` of the field | Text |
| `bulletin.kind` | `code` of `kind` | Equal |
| `bulletin.id`, `bulletin.group`, `bulletin.text` | `bytes` of the field | Text |
| `status.text` | `bytes` of `text` | Text |
| `telemetry.sequence` | `code` of `sequence` | Equal |
| `telemetry.analog[i]` | Item `i` of `analog` | Number |
| `telemetry.digital` | `flags` of `digital` | Equal |
| `capabilities.items` | An object: each name of `items` with its value, or `null` | Equal |

**[open]** The view has no path for these parts:

- the report time, the datum and the fix;
- the extensions of the position body;
- the telemetry definition body and the frequency body;
- the envelope.

## 5. Views of the parsers

**[proposed]** The view of a result has the same paths. The tables give
the name of the parser for each path. A path is in the view only if the
result has that name. The record unit applies to each number.

### 5.1 `pythonlib`

**[proposed]** The parser decodes a packet if `parse` returns. The
formats `beacon` and `invalid` are an exception: the parser gives them
for a packet that it does not decode.

| Path | Name in the result | Conversion |
|---|---|---|
| `position.lat`, `position.lon` | `latitude`, `longitude` | None. |
| `position.course`, `position.speed`, `position.altitude` | `course`, `speed`, `altitude` | None. |
| `position.ambiguity` | `posambiguity` | None. |
| `position.symbol` | `symbol_table`, then `symbol` | None. |
| `position.messaging` | `messagecapable` | None. |
| `position.comment` | `comment`, if the result has `latitude` | None. |
| `object.name`, `object.live` | `object_name`, `alive` | None. |
| `weather.wind_speed`, `weather.gust` | `wind_speed`, `wind_gust` of `weather` | Metres per second: multiply by 3.6. |
| `weather.rain_midnight`, `weather.snow_24h` | `rain_since_midnight`, `snow` of `weather` | None. |
| The other weather paths | The same name in `weather` | None. |
| `message.kind` | `response`, if `format` is `message` | `"message"` if the result has no `response`. |
| `message.addressee`, `message.text`, `message.id` | `addresse`, `message_text`, `msgNo` | None. |
| `bulletin.kind` | `format` | `"announcement"` for `announcement`. `"bulletin"` for `bulletin` and `group-bulletin`. |
| `bulletin.id` | `bid`, or `aid` for an announcement | None. |
| `bulletin.group`, `bulletin.text` | `identifier`, `message_text` | None. |
| `status.text` | `status` | None. |
| `telemetry.sequence`, `telemetry.analog[i]`, `telemetry.digital` | `seq`, `vals`, `bits` of `telemetry` | `bits`: the byte `'1'` is `true`. |

### 5.2 `fap`

**[proposed]** The parser decodes a packet if `parseaprs` returns a true
value.

| Path | Name in the result | Conversion |
|---|---|---|
| `position.lat`, `position.lon` | `latitude`, `longitude` | None. |
| `position.course`, `position.speed`, `position.altitude` | `course`, `speed`, `altitude` | None. |
| `position.ambiguity` | `posambiguity` | None. |
| `position.symbol` | `symboltable`, then `symbolcode` | None. |
| `position.messaging` | `messaging` | 1 is `true`. |
| `position.comment` | `comment`, if the result has `latitude` | None. |
| `object.name` | `objectname` or `itemname` | None. |
| `object.live` | `alive` | 1 is `true`. |
| `weather.wind_speed`, `weather.gust` | `wind_speed`, `wind_gust` of `wx` | Metres per second: multiply by 3.6. |
| `weather.temperature` | `temp` of `wx` | None. |
| The other weather paths | The same name in `wx` | None. |
| `message.kind` | `"message"` if the result has `message`. If not: `"ack"` for `messageack`, `"rej"` for `messagerej`. | |
| `message.addressee`, `message.text` | `destination`, `message` | None. |
| `message.id` | `messageid`. For an ack or a rej: `messageack` or `messagerej`. | None. |
| `bulletin.text` | `message`, if `destination` starts with `BLN` | None. The parser has no bulletin: it gives a message. The view then has no message path. |
| `status.text` | `status` | None. |
| `telemetry.sequence`, `telemetry.analog[i]`, `telemetry.digital` | `seq`, `vals`, `bits` of `telemetry` | `bits`: the byte `'1'` is `true`. |
| `capabilities.items` | `capabilities` | None. |

## 6. Comparison

**[proposed]** The comparison uses one mode of the decoder for a run. It
puts each packet in one class for each parser:

| Class | The record has a use | The parser decodes the packet |
|---|---|---|
| `both` | Yes | Yes |
| `ours-only` | Yes | No |
| `theirs-only` | No | Yes |
| `neither` | No | No |

**[proposed]** For a packet of the class `both`, the comparison gives one
outcome for each path that a view has:

| Outcome | Condition |
|---|---|
| `agree` | Both views have the path, and the two values agree. |
| `differ` | Both views have the path, and the two values do not agree. |
| `ours-only` | Only the view of the record has the path. |
| `theirs-only` | Only the view of the result has the path. |

**[agreed]** Two numbers agree if they differ by less than half of the
`res` of the record. A difference of exactly half does not agree. An
example is a position with ambiguity: the record gives the edge of the
box, and a parser can give its centre. The tool keeps this outcome stable
against the rounding error of the doubles. The rule of
[01-record section 4.6](01-record.md#46-numbers) is for two decoders that
make records. It does not apply here: a parser can round its numbers.

**[proposed]** These rules apply to the other values:

- If the result gives a number as text, the comparison uses the number.
- Two texts agree if they have the same bytes after the removal of the
  spaces at the start and at the end.
- A text that is then empty gives no path, on either side.
- Two other values agree if they are equal.

## 7. Output

**[proposed]** The tool `qua-legacy-compare` prints these items:

- the range of input files, the packet count and the mode;
- for each parser, the commit of its submodule;
- for each parser, the count of each class;
- for each parser and each path, the count of each outcome.

**[proposed]** The tool can print example lines for each count. These
lines are corpus lines. A document quotes a packet of its own instead,
with the source `N0CALL`.

**[proposed]** A difference becomes an entry of the divergence catalogue
after step 4 of the method. In that step, a person reads the code of the
parser and records the cause.

**[agreed]** The catalogue is in
[docs/legacy/divergence](../legacy/divergence/README.md).

## 8. Open items

- **[open]** The paths that section 4 leaves out.
- **[open]** A comparison of the parsers with each other, without the
  record.
- **[open]** Whether a run in strict mode adds information to a run in
  permissive mode.
