# div.course-zero: course code 0 of a compressed position

## Description

The course of a compressed position is four times its code. The code 0
gives 0 degrees by this formula. The record gives 0. Both parsers give
360.

## Category

Not defined by the specification.

## Example

```
N0CALL>APZ001:!/5L!!<*e7>!P[
```

| Side | Course |
|---|---|
| Record | 0, with `res` 4 |
| `fap` | 360 |
| `pythonlib` | 360 |

## Frequency

Run r2, path `position.course`:

| Parser | `agree` | `differ` |
|---|---|---|
| `fap` | 9,838,518 | 52,251 |
| `pythonlib` | 9,824,925 | 50,914 |

## Behaviour

`fap` (read): the code 0 is a special case that gives 360. Its comment
in the code gives the reason: in the uncompressed format, 0 is "unknown"
and 360 is north.

`pythonlib` (read): the code 0 gives 360. Every other code gives four
times the code.

## APRS12c

p. 45/27, p. 56/38 and p. 57/39. The row is
[amb.val.course0](../10-values.md#amb.val.course0).

## Decision

- **[open]** None yet. The record gives 0 with the note of that row.
