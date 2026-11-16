# div.humidity-width: humidity with three digits

## Description

The humidity field is `h` and two digits. Some senders write three
digits, for example `h100` or `h078`. `pythonlib` reads two digits.
`fap` reads up to three digits. The record reads two digits in strict
mode. In permissive mode, it reads three digits with the repair
`repair.humidity-width`.

## Category

Violates the specification but is common on air.

## Example

```
N0CALL>APZ001:!4903.50N/07201.75W_220/004g005t077h100b10190
```

| Side | Humidity | Pressure |
|---|---|---|
| Record, strict mode | 10 %. The comment is `0b10190`. | No value |
| Record, permissive mode | 100 %, with the mark of the repair | 1019 hPa, with the mark of the repair |
| `fap` | 100 % | 1019.0 hPa |
| `pythonlib` | 10 % | No value. The comment is `0b10190`. |

```
N0CALL>APZ001:!4903.50N/07201.75W_220/004g005t077h078b10190
```

| Side | Humidity | Pressure |
|---|---|---|
| Record, strict mode | 7 %. The comment is `8b10190`. | No value |
| Record, permissive mode | 78 %, with the mark of the repair | 1019 hPa, with the mark of the repair |
| `fap` | 78 % | 1019.0 hPa |
| `pythonlib` | 7 % | No value. The comment is `8b10190`. |

## Frequency

Run r6, in permissive mode:

| Parser | Path | `agree` | `differ` | `ours-only` | `theirs-only` |
|---|---|---|---|---|---|
| `fap` | `weather.humidity` | 8,039,711 | 0 | 9,757 | 612,849 |
| `fap` | `weather.pressure` | 7,944,304 | 0 | 8,651 | 795,187 |
| `pythonlib` | `weather.humidity` | 7,811,104 | 230,789 | 7,215 | 497,407 |
| `pythonlib` | `weather.pressure` | 7,726,410 | 0 | 226,186 | 556,249 |

The `theirs-only` counts include
[div.compressed-wind](10-compressed-wind.md).

The inspected examples of `pythonlib`, `differ` show two causes:

- the bytes `h100`: the record gives 100, and the parser gives 10;
- three digits that start with `0`, for example `h078`: the record
  gives 78, and the parser gives 7.

Run r5 had the same input. In that run, the tokenizer itself read `h100`
and three digits that start with `0` as one field, and read two digits
of each other humidity. Against run r5, run r6 has these differences:

- `fap`, `weather.humidity`: `ours-only` is 3,778 less.
- `fap`, `weather.pressure`: 2,344 values moved from `theirs-only` to
  `agree`.
- `pythonlib`, `weather.humidity`: 3,778 values moved from `agree` to
  `theirs-only`.
- `pythonlib`, `weather.pressure`: `ours-only` is 2,344 more.

These are the packets with three digits that the earlier rule did not
read as one field. The cause was not inspected in the examples.

No run was made in strict mode. In strict mode, the record reads two
digits, as `pythonlib` does.

## Behaviour

`fap` (read): after the wind and the temperature, it searches the rest
of the text for each field letter. The humidity is `h` and one to three
digits. A value above 100 gives no humidity. The search is not at a
fixed place, so it also finds a field after bytes that are not weather
data.

`pythonlib` (read): the humidity is `h` and two bytes. The fields are
one sequence from the start of the data. The sequence ends at the first
byte that starts no field.

## APRS12c

p. 84/64: `h` and two digits, and `00` is 100 %. The row is
[`wx.hum`](../06-weather.md#wx.hum).

## Decision

- **[agreed]** The tokenizer of docs/legacy reads two digits. The bytes
  `h100` are the humidity 10, and the weather data ends at the last `0`
  ([06-weather section 10](../06-weather.md#10-reviewed-exceptions)).
  Rule 6 applies: what senders write and what a parser reads do not
  change the reading.
- **[agreed]** Permissive mode has the repair
  [repair.humidity-width](../../interop/01-record.md#repair.humidity-width).
  With the repair, an `h` with three digits is one humidity field, and
  the decoder reads the fields after it. The values have the mark of the
  repair.
- **[agreed]** The range 1 to 100 applies to the number of the three
  digits. Thus `h255` and `h000` give no humidity in permissive mode.
  `fap` gives 100 for `h000`.
- An earlier decision made `h100`, and three digits that start with
  `0`, reviewed exceptions of the tokenizer, with the finding
  `ambiguous`. The author dropped it. 06-weather section 10 gives the
  reasons.
