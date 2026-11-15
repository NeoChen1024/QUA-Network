# div.wind-unit: unit of the 7-byte wind field

## Description

A complete weather report has its wind in a 7-byte field, direction and
speed. The record reads the speed in knots. `fap` reads it in miles per
hour. `pythonlib` gives the field as the course and the speed of the
station.

## Category

Ambiguous, and implementations read it differently.

## Example

```
N0CALL>APZ001:!4903.50N/07201.75W_220/004g005t077
```

| Side | Result |
|---|---|
| Record | Wind speed 7.408 km/h: 4 knots. |
| `fap` | Wind speed 1.8 m/s: 4 miles per hour, with one digit after the point. |
| `pythonlib` | Course 220 and speed 7.408 km/h. No wind direction and no wind speed. |

## Frequency

Run r5:

| Parser | Path | `agree` | `differ` | `ours-only` | `theirs-only` |
|---|---|---|---|---|---|
| `fap` | `weather.wind_speed` | 5,829,302 | 1,682,413 | 46,012 | 67,391 |
| `pythonlib` | `weather.wind_speed` | 317,478 | 3,305 | 7,236,577 | 32 |
| `pythonlib` | `position.course` | 9,824,925 | 50,914 | 5 | 7,093,607 |

For `fap`, a small speed can agree: the two units then differ by less
than half of the resolution.

## Behaviour

`fap` (read): the weather function converts the speed of the wind field
with its constant for miles per hour. It uses the same constant for the
gust.

`pythonlib` (read): for the symbol `_`, it reads a data extension first.
That step takes the wind field as a course and a speed in knots. The
weather step then finds no wind field.

## APRS12c

p. 45/27 states knots for the 7-byte field. p. 84/64 states miles per
hour for the `s` field. p. 85/65 says that the wind field replaces the
`c` and `s` fields, and states no unit. The row is
[err.wx.wind-units](../06-weather.md#err.wx.wind-units).

## Decision

- **[agreed]** The record reads the speed in knots
  ([12-values-weather](../12-values-weather.md#val.wx.wind)).
- **[open]** What a gateway does with a wind speed whose unit the sender
  did not state.
