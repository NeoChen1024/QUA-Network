# div.overlay-letter: table byte a to j of a compressed position

## Description

In a compressed position, the table bytes `a` to `j` are the overlays
`0` to `9`. The record gives the table byte as the packet has it, and a
symbol number that includes the overlay. `fap` gives the digit as the
table byte. `pythonlib` gives the letter.

## Category

None of RFC Appendix E.2 applies. The sides read the same symbol. They
write it in different forms.

## Example

```
N0CALL>APZ001:!c5L!!<*e7#7P[
```

| Side | Symbol |
|---|---|
| Record | `chars` is `c#`. `classic` is 171, the same number as for `2#`. |
| `fap` | Table `2`, code `#` |
| `pythonlib` | Table `c`, code `#` |

## Frequency

Run r5, path `position.symbol`:

| Parser | `agree` | `differ` |
|---|---|---|
| `fap` | 63,654,324 | 55,642 |
| `pythonlib` | 63,221,949 | 0 |

## Behaviour

`fap` (read): the function for the compressed position replaces `a` to
`j` in the table byte with `0` to `9`.

`pythonlib` (read): it copies the table byte.

## APRS12c

p. 125/101 and p. 126/102. The value row is
[val.sym](../10-values.md#val.sym).

## Decision

- **[open]** Whether `chars` of the record gives the digit in place of
  the letter.
