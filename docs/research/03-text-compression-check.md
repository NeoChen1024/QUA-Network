# Check of the text compression against the Unishox2 library

| | |
|---|---|
| Kind | Research report. It fixes a result at one capture window. It is not a specification. |
| Question | [`docs/spec/04-text-compression.md`](../spec/04-text-compression.md); RFC 5.7; RFC section 14, question 16 |
| Tool | `qua-legacy-usx-check` |

## 1. Run

| | |
|---|---|
| Input | `aprsis-20261104-03.log` to `aprsis-20261114-11.log`, 249 files |
| Packets | 84,560,319 |
| Decoder of the records | Permissive mode |
| Tool | The version of the commit that changes this report to this run |
| Unishox2 | Run from the submodule `3rdparty/Unishox2`, at commit `6ec2ff0` |
| Output | `work/legacy/usx-check-r2.txt` |

The capture is the APRS-IS full feed. It is not a sample of radio
traffic. RFC 13.4 gives the caveats.

An earlier run of this report was for the format with the templates, the
hexadecimal digits and the UUID. The author removed these parts from the
specification. This run is for the format without them.

## 2. Method

The module `usx.py` has a decoder and an encoder. They were written from
a reading of the library source, and the specification file states the
same rules. The module holds no code of the library.

The tool takes the free texts of the records, as
[01-free-text](01-free-text.md) section 2 gives them. It checks a text
that is valid UTF-8 and has 1 to 255 bytes. A text counts once for each
corpus file that has it. A column "by packet" counts a text once for each
packet that holds it.

The library is the path that is independent of `usx.py`. Agreement of the
encoder of `usx.py` with its own decoder is not evidence.

The encoder makes the choices of the library, but it does not use the
three parts that the specification leaves out. The simple encoder uses no
optional part of the format (section 8 of the specification file).

The checks:

1. **Library output.** The decoder gives the text for the bytes of the
   library with the preset `USX_PSET_DFLT`, or it rejects them because
   they use a part that is left out.
2. **Encoder.** The decoder and the library both give the text for the
   bytes of the encoder. If the decoder accepts the bytes of the library,
   the bytes of the encoder are equal to them.
3. **Simple encoder.** The decoder and the library both give the text
   for its bytes.
4. **Changed input.** The tool changes the bytes of the encoder, 4
   times for each text. If the decoder gives a text for the changed
   input, the library must give the same bytes at the start of its
   output.

The changes of check 4 are a function of the text. A second run gives the
same result.

## 3. Texts

| | Texts |
|---|---|
| Checked | 14,716,372 |
| Checked, by packet | 65,217,518 |
| Not checked: longer than 255 bytes | 168,186 |
| Not checked: not valid UTF-8 | 137,232 |

The library encoder failed for 0 texts.

## 4. Output of the library

| Result of the decoder | Texts |
|---|---|
| Gives the text | 12,929,257 |
| Rejects: the output uses a part that is left out | 1,787,115 |
| A different result | 0 |

The parts that are left out, in the output of the library:

| Part | Texts | Share | By packet | Share |
|---|---|---|---|---|
| Template | 215,625 | 1.465% | 383,338 | 0.588% |
| Hexadecimal digits | 1,571,490 | 10.679% | 3,812,457 | 5.846% |
| UUID | 0 | 0.000% | 0 | 0.000% |

## 5. Encoder and decoder

| Check | Texts that agree | Texts in the check |
|---|---|---|
| The decoder gives the text for the output of the encoder | 14,716,372 | 14,716,372 |
| The library gives the text for the output of the encoder | 14,716,372 | 14,716,372 |
| The decoder gives the text for the output of the simple encoder | 14,716,372 | 14,716,372 |
| The library gives the text for the output of the simple encoder | 14,716,372 | 14,716,372 |
| The encoder gives the bytes of the library | 12,929,257 | 12,929,257 |

## 6. Size

The size of a text follows the rule of RFC 5.7: one length byte and the
compressed bytes, or the text if that is not shorter. The counts are by
packet.

| Form | Bytes | Share of the text bytes |
|---|---|---|
| Text | 2,427,634,988 | |
| Library, with the parts that are left out | 2,075,182,793 | 85.482% |
| Encoder | 2,076,711,068 | 85.545% |
| Simple encoder | 2,120,458,754 | 87.347% |
| Encoder, every text compressed | 2,093,448,824 | 86.234% |

In the last row, a sender compresses every text. A text that does not
become shorter is then longer than the text. With the rule of RFC 5.7,
the compressed form is shorter for 52,038,281 texts by packet,
79.792% of the texts.

## 7. Optional parts of the format

The table gives the texts for which the output of the encoder uses a
part. One text can use more than one part.

| Part | Texts | Share | By packet | Share |
|---|---|---|---|---|
| No optional part | 12,360,484 | 83.991% | 52,002,501 | 79.737% |
| Repeat (6.1) | 1,467,421 | 9.971% | 7,020,568 | 10.765% |
| Sequence | 897,329 | 6.097% | 6,205,908 | 9.516% |
| Repeated byte | 184,494 | 1.254% | 881,864 | 1.352% |
| Bytes (6.2) | 31,761 | 0.216% | 70,166 | 0.108% |

## 8. Changed input

| Change | Inputs | Decoder rejects | Decoder gives a text, library agrees | Decoder gives a text, library differs |
|---|---|---|---|---|
| One bit changed | 11,737,678 | 6,151,449 | 5,586,229 | 0 |
| Last byte removed | 11,881,148 | 11,881,148 | 0 | 0 |
| One byte added at the end | 11,688,076 | 11,688,076 | 0 | 0 |
| Length byte 1 larger | 11,851,078 | 11,851,078 | 0 | 0 |
| Length byte 1 smaller | 11,707,508 | 9,561,933 | 2,145,575 | 0 |

The decoder gave a text that the library does not give for 0 of
58,865,488 inputs.

The rejects by case of section 7 of the specification file:

| Case | Inputs |
|---|---|
| 1 | 4,254 |
| 2 | 58,611 |
| 3 | 24,578,654 |
| 4 | 612,715 |
| 5 | 23,504,701 |
| 6 | 14,204 |
| 7 | 369,766 |
| 8 | 238,866 |
| 9 | 934,519 |
| 10 | 51,536 |
| 11 | 1,516 |
| 12 | 167,138 |
| 13 | 130,435 |
| 14 | 463,179 |
| 15 | 877 |
| 16 | 2,713 |

Each case occurs.

## 9. What the result shows

- The decoder and the library give the text for the output of the
  encoder, for 14,716,372 and 14,716,372 of 14,716,372 texts.
- The output of the library is valid under the specification file for
  12,929,257 of 14,716,372 texts. For the others, it uses a part that
  is left out.
- The removal of the three parts costs 0.063 percentage points of
  the text bytes.
- The simple encoder is 1.802 percentage points larger than
  the encoder.
- To compress every text costs 0.689 percentage points more than
  the rule of RFC 5.7.
- A length byte that is 1 too small is not always invalid. The decoder
  gave a text for 2,145,575 of 11,707,508 such inputs. That text is the
  correct text without its last byte. RFC 5.7 accepts this.
- The check does not show that the decoder is correct for input that no
  encoder of this report produces. The changed inputs test this only in
  part.
