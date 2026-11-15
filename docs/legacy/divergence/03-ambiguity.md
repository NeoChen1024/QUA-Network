# div.ambiguity: point of a position with ambiguity

## Description

A position with ambiguity has blanked digits. The record gives the edge
of the box and the size of the box. Both parsers give the centre of the
box.

## Category

Ambiguous, and implementations read it differently.

## Example

```
N0CALL>APZ001:!4903.  N/07201.  W-
```

| Side | Latitude | Longitude |
|---|---|---|
| Record | 49.05, with `res` 1/60 | −72.01666…, with `res` 1/60 |
| `fap` | 49.05833… | −72.025 |
| `pythonlib` | 49.05833… | −72.025 |

All sides give the ambiguity level 2.

## Frequency

Run r2:

| Parser | Path | `agree` | `differ` |
|---|---|---|---|
| `fap` | `position.lat` | 62,673,993 | 1,021,955 |
| `fap` | `position.lon` | 62,664,876 | 1,022,798 |
| `pythonlib` | `position.lat` | 62,190,427 | 1,017,366 |
| `pythonlib` | `position.lon` | 62,181,355 | 1,018,211 |

The centre differs from the edge by exactly half of `res`. The
comparison counts this as `differ`
([09-comparison section 6](../../interop/09-comparison.md#6-comparison)).
These counts include other causes.

## Behaviour

`fap` (read): for each level, it adds half of the blanked unit to the
minutes. For level 4, it adds half a degree.

`pythonlib` (read): it puts the position at the centre of the box. Its
comment in the code says so.

## APRS12c

p. 40/24 and p. 41/25. The row is
[amb.val.ambiguity](../10-values.md#amb.val.ambiguity).

## Decision

- **[agreed]** The record gives the edge of the box that is nearest to
  the equator or to the prime meridian. `res` is the size of the box
  ([01-record section 7.2](../../interop/01-record.md#72-other-rules)).
- **[open]** What a gateway writes for such a position.
