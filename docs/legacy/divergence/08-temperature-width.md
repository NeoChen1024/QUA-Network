# div.temperature-width: temperature with more than three bytes

## Description

The temperature field is `t` and three bytes. Some senders write more
bytes, for example `t0122` or `t-225`. The record reads three bytes.
`fap` reads all digits that follow.

## Category

Violates the specification but is common on air.

## Example

```
N0CALL>APZ001:!4903.50N/07201.75W_220/004g005t0122r000
```

| Side | Temperature | Rain in the last hour |
|---|---|---|
| Record | −11.1 °C, from `012` | No value. |
| `fap` | 50.0 °C, from `0122` | 0.0 mm |
| `pythonlib` | −11.1 °C, from `012` | No value. The comment is `2r000`. |

## Frequency

Run r5, path `weather.temperature`:

| Parser | `agree` | `differ` |
|---|---|---|
| `fap` | 8,307,331 | 14,303 |
| `pythonlib` | 8,331,304 | 4 |

## Behaviour

`fap` (read): the temperature is `t`, an optional `-`, and every digit,
space or point that follows. The pattern has no upper limit.

`pythonlib` (read): the temperature is `t` and three bytes.

## APRS12c

p. 84/64. The row is [`wx.temp`](../06-weather.md#wx.temp).

## Decision

- **[open]** None yet. The value that the sender meant is not known:
  `t0122` can be 12 or 122.
