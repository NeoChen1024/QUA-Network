# Unishox2: what an independent implementation needs

| | |
|---|---|
| Kind | Research report. It records a reading of third-party code at one commit. It is not a specification. |
| Question | RFC 5.7; RFC section 14, question 16 |
| Source | `unishox2.c` and `unishox2.h` of the submodule `3rdparty/Unishox2`, at commit `6ec2ff0` (2026-10-28) |

Each statement about Unishox2 in this file was read in that source, if
the text does not say otherwise. The library was also run on the texts of
the capture ([01-free-text](01-free-text.md)).

The question is how much work an independent encoder and an independent
decoder are, for the presets `DFLT` and `NO_DICT`. RFC 5.7 pins the
decoder and does not pin an encoder.

## 1. Size of the reference implementation

The counts are lines of code, without empty lines and comment lines.

| Part | Lines | Necessary for one preset and one string |
|---|---|---|
| Tables and their setup | 67 | Yes |
| Encoder: helper functions | 196 | Yes |
| Encoder: main loop | 315 | Yes |
| Encoder: search for a repeat in the same string | 31 | For `DFLT` only, and optional |
| Encoder: search for a repeat in earlier strings | 50 | No |
| Decoder: bit and code readers | 143 | Yes |
| Decoder: main loop | 272 | Yes |
| Decoder: copy of a repeat | 40 | About 14 lines, for `DFLT` only |

The library can also compress an array of strings, with repeats between
them. RFC 5.7 compresses one string, so this part is not necessary.

## 2. What a decoder implements

A compressed string is a sequence of bits. A decoder for one preset has
these parts:

1. Three character sets of 28 positions each: letters, symbols and
   digits. One prefix code, of 2 to 8 bits, selects the position.
2. A second prefix code selects the set. It is the only table that
   differs between `DFLT` and `NO_DICT` (section 3).
3. The state: the current set, one upper-case letter, and a run of
   upper-case letters.
4. A count code with five ranges, for lengths and distances.
5. A Unicode code point as a signed difference from the code point
   before, in five ranges of 6 to 21 bits. In this state, the space, the
   comma, the period and the line feed have codes of their own.
6. Six fixed sequences of the preset. For both presets they are `": "`,
   `": `, `</`, `="`, `":"` and `://`.
7. A run of one repeated character.
8. Hexadecimal digits in 4 bits each: a run with a count, in lower or
   upper case, and a UUID of 32 digits.
9. Four templates: a date and time, a date, a telephone number and a
   time. The digits of a template are in 1 to 4 bits each.
10. A run of raw bytes, for bytes that are not valid UTF-8.
11. Codes for the line feed, the carriage return, both together, and the
    tab.
12. The end of the string (section 4).
13. For `DFLT` only: a repeat of bytes that occur earlier in the same
    string, as a length and a distance.

An encoder can leave out the parts 6 to 9 and 13. The decoder cannot,
because another encoder can use them.

## 3. `DFLT` and `NO_DICT`

The two presets have the same character sets, the same sequences and the
same templates. They differ in the code that selects the set:

| Set | `DFLT` | `NO_DICT` |
|---|---|---|
| Letters | `00` | `00` |
| Symbols | `01` | `01` |
| Digits | `10` | `10` |
| Repeat of earlier bytes | `110` | None |
| Unicode | `111` | `11` |

The effects are these:

- **Decoder.** `NO_DICT` has no repeat. The decoder is about 14 lines
  shorter. The specification needs three rules less: for a distance that
  starts before the string, for a length that passes the end of the
  output, and for a length that is larger than the distance.
- **Encoder.** With `NO_DICT`, an encoder has no search for a repeat. In
  the reference, the search is 31 lines. It compares each position with
  each earlier position, which is a small cost for a string of 255 bytes.
- **Encoder with `DFLT`.** RFC 5.7 does not pin an encoder. An encoder
  for `DFLT` can also leave out the search. Its output is then a little
  larger than the output of `NO_DICT`, because the Unicode code has 3
  bits and not 2.
- **Size.** With the reference encoder, `DFLT` gives 85.482% and
  `NO_DICT` gives 86.765% of the text bytes of the capture
  ([01-free-text section 6](01-free-text.md#6-unishox2-all-presets)).

The last rule of the decoder needs a note. The reference copies a repeat
with one block copy. If the length is larger than the distance, the copy
reads bytes that the decoder has not written yet. The reference encoder
does not produce such a repeat. A specification for `DFLT` must reject
it, or define its result.

## 4. Work that is the same for both presets

Most of the work does not depend on the choice.

- **The end of the string.** The reference decoder stops when the bits
  end or when it reads the end code. The reference encoder writes only
  the part of the end code that fits the last byte. RFC 5.7 gives the
  length of the uncompressed string in a length byte, so a specification
  can stop at that length. It then needs a rule for the bits that remain.
- **Malformed input.** The reference decoder has about 30 places where it
  stops on input that it cannot read. In each, it returns the output that
  it has, with no error. A specification must state for each case that
  the decoder rejects the field (RFC section 14, question 16).
- **Unicode.** The decoder adds each difference to the code point before
  and writes the result as UTF-8. It does not check the result. A
  surrogate, a value above U+10FFFF, a negative value or a value below
  U+0080 gives bytes that are not valid UTF-8. A run of raw bytes can
  also give such bytes. RFC 5.3 requires UTF-8, so a specification must
  reject these.
- **Parts with no clear use here.** The templates, the UUID and the
  hexadecimal run are for other kinds of text. A decoder still needs
  them. How often they occur in the texts of the capture is not measured.
- **More than one encoding.** One string has many valid compressed forms.
  RFC 5.2 allows this for a compressed field.

Not checked: whether the result of the library depends on the platform.
The code uses the type `char` for input bytes, and that type is signed on
some platforms and unsigned on others.

## 5. Estimate

These figures are estimates by the writer of this report. They are not
measured.

| Implementation | Lines of C |
|---|---|
| Decoder for `NO_DICT`, one string | About 300 |
| Decoder for `DFLT`, one string | About 315 |
| Smallest encoder: no repeat, no template, no hexadecimal run | About 250 |
| Encoder with the same output as the reference | About 550 |

## 6. Result

After this report, the author chose `DFLT` as the only preset (RFC 5.7).
The decoder specification is
[`docs/spec/04-text-compression.md`](../spec/04-text-compression.md). The
two items below are as the report first gave them.

**[proposed]** `DFLT` is the better candidate.

- The decoders of the two presets differ by about 14 lines and three
  rules. The parts that are hard to specify are the same for both.
- An encoder for `DFLT` can be as simple as an encoder for `NO_DICT`,
  because the specification does not pin an encoder.
- `DFLT` gives the smaller size on the capture.

**[proposed]** The next step is a decoder specification in `docs/spec/`
and a decoder written from it. The texts of the capture then test that
decoder against the reference.

## 7. Open items

- **[open]** How often each part of section 2 occurs in the texts of the
  capture. A part that never occurs is a candidate to make invalid.
- **[open]** Whether the specification can make the templates, the UUID,
  the hexadecimal run and the run of raw bytes invalid. The reference
  encoder produces them, so it could then not be the encoder.
- **[open]** The rule for the bits after the last byte of the string.
