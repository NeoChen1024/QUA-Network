# div.humidity-width: humidity with three digits

## Description

The humidity field is `h` and two digits. Some senders write three
digits, for example `h100` or `h078`. `pythonlib` reads two digits.
`fap` reads up to three digits. The record reads two digits, with two
exceptions: `100`, and three digits that start with `0`.

## Category

Violates the specification but is common on air.

## Example

```
N0CALL>APZ001:!4903.50N/07201.75W_220/004g005t077h100b10190
```

| Side | Humidity | Pressure |
|---|---|---|
| Record, strict mode | No value | No value |
| Record, permissive mode | 100 %, with a mark | 1019 hPa, with a mark |
| `fap` | 100 % | 1019.0 hPa |
| `pythonlib` | 10 % | No value. The comment is `0b10190`. |

An earlier draft of the record gave the humidity 10 % in both modes,
with no finding. The bytes `0b10190` were the comment.

```
N0CALL>APZ001:!4903.50N/07201.75W_220/004g005t077h078b10190
```

| Side | Humidity | Pressure |
|---|---|---|
| Record, strict mode | No value | No value |
| Record, permissive mode | 78 %, with a mark | 1019 hPa, with a mark |
| `fap` | 78 % | 1019.0 hPa |
| `pythonlib` | 7 % | No value. The comment is `8b10190`. |

An earlier draft of the record gave the humidity 7 % for this packet in
both modes, with no finding.

## Frequency

Run r5:

| Parser | Path | `agree` | `differ` | `ours-only` | `theirs-only` |
|---|---|---|---|---|---|
| `fap` | `weather.humidity` | 8,039,711 | 0 | 13,535 | 612,849 |
| `fap` | `weather.pressure` | 7,941,960 | 0 | 8,651 | 797,531 |
| `pythonlib` | `weather.humidity` | 7,814,882 | 230,789 | 7,215 | 493,629 |

The `theirs-only` counts include
[div.compressed-wind](10-compressed-wind.md). They also include the
bytes `h000`, for which both parsers give 100 and the record gives no
value.

In this run, the record reads three digits as the decision below says.
The inspected examples of `pythonlib`, `differ` show two causes:

- the bytes `h100`: the record gives 100, and the parser gives 10;
- three digits that start with `0`, for example `h078`: the record
  gives 78, and the parser gives 7.

An earlier run on the same input, with the decoder at `6f138d7`, had
the rule for `h100` only. In that run, `fap` had the
outcome `differ` for 50,735 humidity values. The inspected examples were
three digits that start with `0`.

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

- **[agreed]** The tokenizer reads `h100` as one humidity field, with the
  finding `ambiguous`
  ([06-weather section 10](../06-weather.md#10-reviewed-exceptions)). In
  strict mode, the humidity has no value. In permissive mode, it is 100,
  with a mark.
- **[agreed]** The fields after `h100` have the same effect
  ([12-values-weather section 6](../12-values-weather.md#6-effect-of-findings)).
- **[agreed]** The tokenizer reads three digits that start with `0`, for
  example `h078`, in the same way. In permissive mode, the humidity is
  the number of the three digits, with a mark.
- **[proposed]** `h000` gives no humidity in both modes. The number 0 is
  below the range. `fap` gives 100 for these bytes.
- **[agreed]** For every other humidity with three digits, the record
  reads two digits.
