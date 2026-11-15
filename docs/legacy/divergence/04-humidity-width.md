# div.humidity-width: humidity with three digits

## Description

The humidity field is `h` and two digits. Some senders write three
digits, for example `h100`. `pythonlib` reads two digits. `fap` reads up
to three digits. The record reads two digits, with an exception for
`100`.

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

## Frequency

Run r2:

| Parser | Path | `agree` | `differ` | `ours-only` | `theirs-only` |
|---|---|---|---|---|---|
| `fap` | `weather.humidity` | 7,998,793 | 50,735 | 13,535 | 603,032 |
| `fap` | `weather.pressure` | 7,883,539 | 0 | 7,468 | 855,952 |
| `pythonlib` | `weather.humidity` | 7,872,443 | 183,045 | 7,215 | 483,812 |

The `theirs-only` counts include
[div.compressed-wind](10-compressed-wind.md).

In this run, the record reads `h100` as the decision below says. The
inspected examples show these causes:

- `pythonlib`, `differ`: the bytes `h100`. The record gives 100, and the
  parser gives 10.
- `fap`, `differ`: three digits that start with `0`, for example `h078`.
  The record gives 7, and the parser gives 78.

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
- **[open]** Another humidity with three digits, for example `h078`. The
  record reads two digits.
