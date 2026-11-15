# div.compressed-wind: 7-byte wind field after a compressed position

## Description

A compressed position has its wind in the `cs` bytes. Some senders leave
the `cs` bytes empty and write the 7-byte wind field of the uncompressed
format after the block. The record then gives no weather value: the
bytes are the comment. Both parsers read the weather data.

## Category

Violates the specification but is common on air.

## Example

```
N0CALL>APZ001:!/5L!!<*e7_  G.../...g...t086h62b10140
```

| Side | Temperature | Humidity | Pressure |
|---|---|---|---|
| Record | No value | No value | No value |
| `fap` | 30.0 °C | 62 % | 1014.0 hPa |
| `pythonlib` | 30.0 °C | 62 % | 1014.0 hPa |

The record has the use `weather` with no field. Its comment is
`.../...g...t086h62b10140`.

## Frequency

Run r5, outcome `theirs-only`:

| Parser | `weather.temperature` | `weather.humidity` | `weather.pressure` |
|---|---|---|---|
| `fap` | 687,903 | 612,849 | 797,531 |
| `pythonlib` | 578,843 | 493,629 | 556,249 |

The counts for `fap` include
[div.humidity-width](04-humidity-width.md).

## Behaviour

`fap` (read): for the symbol `_`, it gives the bytes after the position
to the weather function. This is the same for a compressed and for an
uncompressed position. The function accepts a wind field of dots.

`pythonlib` (read): for the symbol `_`, it reads a data extension and
then the weather data, after either position format.

## APRS12c

p. 86/66 puts the wind of a compressed report in the `cs` bytes. The
rows are [`cmp.cs.wind`](../02-fields.md#cmp.cs.wind) and
[amb.wx.cmpwind](../06-weather.md#amb.wx.cmpwind).

## Decision

- **[open]** Whether the permissive mode reads this form.
