# div.ack-number: acknowledgement whose number has a `}`

## Description

An acknowledgement can copy a number of the reply-ack format, for
example `ack3C}`. The record gives the bytes before the `}` as the
number. `fap` gives the `}` as part of the number. `pythonlib` reads the
packet as an acknowledgement only if the number has two bytes before the
`}`.

## Category

Not defined by the specification.

## Example

```
N0CALL>APZ001::N0CALL-9 :ack3C}
N0CALL>APZ001::N0CALL-9 :ack1}
```

| Side | `ack3C}` | `ack1}` |
|---|---|---|
| Record | Acknowledgement of `3C` | Acknowledgement of `1` |
| `fap` | Acknowledgement of `3C}` | Acknowledgement of `1}` |
| `pythonlib` | Acknowledgement of `3C` | A message with the text `ack1}` |

## Frequency

Run r5:

| Parser | Path | `agree` | `differ` |
|---|---|---|---|
| `fap` | `message.id` | 416,529 | 7,685 |
| `pythonlib` | `message.id` | 423,425 | 112 |
| `pythonlib` | `message.kind` | 823,350 | 155 |

## Behaviour

`fap` (read): the number of an acknowledgement is one to five bytes.
Each is a letter, a digit or `}`.

`pythonlib` (read): it tries two forms. The first is two letters or
digits, a `}`, and zero or two more. The second is one to five letters
or digits. Another text is a message.

## APRS12c

p. 94/72 and p. 95/73. The rows are
[amb.msg.replyack](../08-message.md#amb.msg.replyack) and
[val.msg.acknum](../15-values-message.md#val.msg.acknum).

## Decision

- **[proposed]** The record gives the bytes before the first `}`
  ([06-message](../../interop/06-message.md)).
