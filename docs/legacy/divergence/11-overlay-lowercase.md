# div.overlay-lowercase: table byte a to j outside the compressed format

## Description

The table bytes `a` to `j` are the overlays `0` to `9` in the compressed
format only. Some senders write them in an uncompressed position or in a
Mic-E report. Both parsers then decode nothing of the packet. The record
gives the position. In strict mode, it gives no symbol. In permissive
mode, it gives the symbol with the repair `repair.overlay-lowercase`.

## Category

Violates the specification but is common on air. This is the nearest
category of RFC Appendix E.2. The count below does not show that these
bytes are common.

## Example

```
N0CALL>APZ001:!4903.50Na07201.75W-
```

| Side | Result |
|---|---|
| Record, strict mode | A position. `symbol` has no value. Its `why` is the `syntax` finding of `sym.table`. |
| Record, permissive mode | A position. `chars` is `a-`. `classic` is 539, the same number as for `0-`. The mark is the ID of the repair. |
| `fap` | No result |
| `pythonlib` | No result |

```
N0CALL>T7PQ22:`(_fn"Oja
```

| Side | Result |
|---|---|
| Record, strict mode | A position. `symbol` has no value. Its `why` is the `syntax` finding of `mice.sym.table`. |
| Record, permissive mode | A position. `chars` is `aj`. `classic` is 2796. The mark is the ID of the repair. |
| `fap` | No result |
| `pythonlib` | No result |

The verdict of the record is `syntax` in both modes.

## Frequency

No path of a run has a count for these packets, because the parsers give
no result for them. They are in the class `ours-only` of each parser.

A run of `qua-legacy-decode --stats` in permissive mode, at the commit
that adds this entry, on the input of run r6 (84,560,319 packets):

| Count | Records |
|---|---|
| Records with a position body | 64,168,927 |
| `position.symbol` with the mark of the repair | 8,828 |
| `position.symbol` with the repair and no value, because the symbol code has a `syntax` finding | 57 |

No `status.symbol` has the mark in this run.

## Behaviour

`fap` (read): for an uncompressed position and for Mic-E, the table byte
has to be `/`, `\`, `A` to `Z` or `0` to `9`. If not, the parser gives
the error `sym_inv_table` and no result.

`pythonlib` (read): the expressions for an uncompressed position and for
Mic-E accept only these table bytes. Another byte gives no match, and
the parser gives no result.

The two examples were run through both parsers. Each gave no result.

## APRS12c

p. 125/101 and p. 126/102. The rows are
[`sym.table`](../02-fields.md#sym.table) and
[`mice.sym.table`](../04-mic-e.md#mice.sym.table).

## Decision

- **[agreed]** The tokenizer of docs/legacy gives `syntax` for these
  bytes. Rule 1 applies.
- **[agreed]** Permissive mode has the repair
  [repair.overlay-lowercase](../../interop/01-record.md#repair.overlay-lowercase).
  The table byte gives the overlay `0` to `9`. RFC 5.6 requires this
  conversion of a gateway.
- An earlier draft of the record had this rule with no ID, and the mark
  of the symbol was the `syntax` finding.
