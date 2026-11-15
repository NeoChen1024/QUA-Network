# div.comment: fields removed from the comment

## Description

A position can have fields inside its comment: an altitude, a DAO and a
base-91 telemetry block. Each side removes some of them from the comment
that it gives. The sides do not remove the same bytes.

An earlier draft of the record gave all bytes of the comment. For the
example, it gave `/Digi text/A=000100`.

## Category

Not defined by the specification. APRS12c specifies the fields inside
the comment. It does not say what the comment is after a parser reads
them.

## Example

```
N0CALL>APZ001:!4903.50N/07201.75W#PHG5132/Digi text/A=000100
```

| Side | Comment |
|---|---|
| Record | `Digi text` |
| `fap` | `Digi text` |
| `pythonlib` | `Digi text` |

## Frequency

Run r2, path `position.comment`:

| Parser | `agree` | `differ` | `ours-only` | `theirs-only` |
|---|---|---|---|---|
| `fap` | 53,420,382 | 3,422,287 | 615,842 | 1,506,476 |
| `pythonlib` | 51,749,590 | 5,198,320 | 39,748 | 2,633,548 |

These counts include other causes. The inspected examples show these:

- the weather data of [div.compressed-wind](10-compressed-wind.md);
- the type bytes of Mic-E before and after the text, which `fap` keeps
  in the comment;
- a `/` or a space at the start of a comment with no data extension.

## Behaviour

`fap` (read): the function for the comment does these steps in order.

1. It removes a data extension at the start.
2. It removes the first altitude.
3. It removes a base-91 telemetry block.
4. It removes the last DAO, if the DAO is valid.
5. It removes one `/` or one white-space byte at the start.
6. It removes the bytes that are not printable, and the white space at
   both ends.

`pythonlib` (read): it removes the same four fields. It then removes one
`/` at the start, and the spaces at both ends.

Neither parser removes a frequency specification.

## APRS12c

The altitude is on p. 43/27. The numbered files have the tokens
[`cmt.alt`](../02-fields.md#cmt.alt) and
[`cmt.dao`](../02-fields.md#cmt.dao), and
[07-telemetry](../07-telemetry.md) has the base-91 block.

## Decision

- **[agreed]** The `comment` of the record leaves out the altitude
  ([01-record section 7.1](../../interop/01-record.md#71-comment)).
- **[proposed]** It also leaves out the DAO and the base-91 block.
- **[agreed]** It leaves out a `/` after a data extension.
- **[open]** A `/` or a space at the start of a comment that has no data
  extension before it. The parsers remove it. The record keeps it.
- **[open]** The frequency specification
  ([07-frequency section 6](../../interop/07-frequency.md#6-open-items)).
