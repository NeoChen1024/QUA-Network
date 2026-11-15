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
| Tool | The version of the commit that adds this report |
| Unishox2 | Run from the submodule `3rdparty/Unishox2`, at commit `6ec2ff0` |
| Output | `work/legacy/usx-check-r1.txt` |

The capture is the APRS-IS full feed. It is not a sample of radio
traffic. RFC 13.4 gives the caveats.

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

The checks:

1. **Encoder.** The bytes of the encoder are equal to the bytes of the
   library with the preset `USX_PSET_DFLT`.
2. **Decoder.** The decoder gives the text for the bytes of the library.
3. **Simple encoder.** The simple encoder uses no optional part of the
   format (section 8 of the specification file). The decoder and the
   library both give the text for its bytes.
4. **Changed input.** The tool changes the bytes of the library, 4
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

## 4. Encoder and decoder

| Check | Texts that agree | Texts that differ |
|---|---|---|
| The encoder gives the bytes of the library | 14,716,372 | 0 |
| The decoder gives the text for the output of the library | 14,716,372 | 0 |
| The decoder gives the text for the output of the simple encoder | 14,716,372 | 0 |
| The library gives the text for the output of the simple encoder | 14,716,372 | 0 |

## 5. Size

The size follows the rule of RFC 5.7: one length byte and the compressed
bytes, or the text if that is not shorter. The counts are by packet.

| Form | Bytes | Share of the text bytes |
|---|---|---|
| Text | 2,427,634,988 | |
| Encoder with the choices of the library | 2,075,182,793 | 85.482% |
| Simple encoder | 2,120,458,754 | 87.347% |

## 6. Optional parts of the format

The table gives the texts for which the output of the library uses a
part. One text can use more than one part.

| Part | Texts | Share | By packet | Share |
|---|---|---|---|---|
| No optional part | 10,841,290 | 73.668% | 48,450,435 | 74.291% |
| Hexadecimal digits (6.2) | 1,587,201 | 10.785% | 3,841,722 | 5.891% |
| Repeat (6.1) | 1,459,832 | 9.920% | 7,007,445 | 10.745% |
| Sequence | 897,329 | 6.097% | 6,205,908 | 9.516% |
| Template (6.2) | 217,079 | 1.475% | 387,672 | 0.594% |
| Repeated byte | 158,541 | 1.077% | 845,749 | 1.297% |
| Bytes of 8 bits (6.2) | 31,761 | 0.216% | 70,166 | 0.108% |
| UUID (6.2) | 0 | 0.000% | 0 | 0.000% |

## 7. Changed input

| Change | Inputs | Decoder rejects | Decoder gives a text, library agrees | Decoder gives a text, library differs |
|---|---|---|---|---|
| One bit changed | 11,737,283 | 6,117,347 | 5,619,936 | 0 |
| Last byte removed | 11,881,931 | 11,881,931 | 0 | 0 |
| One byte added at the end | 11,688,474 | 11,688,474 | 0 | 0 |
| Length byte 1 larger | 11,851,050 | 11,851,050 | 0 | 0 |
| Length byte 1 smaller | 11,706,750 | 9,595,778 | 2,110,972 | 0 |

The decoder gave a text that the library does not give for 0 of
58,865,488 inputs.

The rejects by case of section 7 of the specification file:

| Case | Inputs |
|---|---|
| 1 | 4,246 |
| 2 | 59,045 |
| 3 | 24,663,459 |
| 4 | 813,670 |
| 5 | 23,444,253 |
| 6 | 14,372 |
| 7 | 383,505 |
| 8 | 242,074 |
| 9 | 931,240 |
| 10 | 50,585 |
| 11 | 1,340 |
| 12 | 173,685 |
| 13 | 137,791 |
| 14 | 23,701 |
| 15 | 153,536 |
| 16 | 35,357 |
| 17 | 2,721 |

Each case occurs.

## 8. What the result shows

- The encoder of `usx.py` gives the bytes of the library for
  14,716,372 of 14,716,372 texts.
- The output of the library is valid under the specification file for
  14,716,372 of 14,716,372 texts.
- A length byte that is 1 too small is not always invalid. The decoder
  gave a text for 2,110,972 of 11,706,750 such inputs. That text is the
  correct text without its last byte.
- The check does not show that the decoder is correct for input that no
  encoder of this report produces. The changed inputs test this only in
  part.
