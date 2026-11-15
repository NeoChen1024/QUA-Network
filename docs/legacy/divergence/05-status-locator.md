# div.status-locator: locator at the start of a status text

## Description

A status report can start with a Maidenhead locator and a symbol. The
record gives the locator and the symbol as fields, and the text without
them. Both parsers give all bytes as the status text.

## Category

None of RFC Appendix E.2 applies. APRS12c specifies this format, and the
parsers do not decode it.

## Example

```
N0CALL>APZ001:>IO91SX/- My house
```

| Side | Status text |
|---|---|
| Record | `My house`, with the locator `IO91SX` and the symbol `/-` as fields |
| `fap` | `IO91SX/- My house` |
| `pythonlib` | `IO91SX/- My house` |

## Frequency

Run r5, path `status.text`:

| Parser | `agree` | `differ` |
|---|---|---|
| `fap` | 6,858,435 | 83,930 |
| `pythonlib` | 6,858,518 | 83,847 |

## Behaviour

`fap` (read): after an optional timestamp, the status is all bytes that
remain.

`pythonlib` (read): the same, without the spaces at both ends.

## APRS12c

p. 105/81 and p. 106/82. The value rows are
[val.stat.loc](../14-values-status.md#val.stat.loc) and
[val.stat.text](../14-values-status.md#val.stat.text).

## Decision

- **[open]** None yet. A text that is not a locator can start with the
  same bytes.
