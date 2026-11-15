# Free text of the capture: repetition and Unishox2

| | |
|---|---|
| Kind | Research report. It fixes a result at one capture window. It is not a specification. |
| Question | RFC section 15, step 11; RFC 5.7; RFC 5.11 |
| Tool | `qua-legacy-text` |

## 1. Run

| | |
|---|---|
| Input | `aprsis-20261104-03.log` to `aprsis-20261114-11.log`, 249 files |
| Packets | 84,560,319 |
| Decoder | Permissive mode, at commit `25507fe` |
| Tool | At commit `71191f4` |
| Unishox2 | Run from the submodule `3rdparty/Unishox2`, at commit `6ec2ff0` |
| Output | `work/legacy/text-r1.txt` |

The capture is the APRS-IS full feed. It is not a sample of radio
traffic. RFC 13.4 gives the caveats.

## 2. Method

The decoder of `docs/interop/` gives a record for each packet. The tool
reads these texts from a record:

| Text | Field of the record |
|---|---|
| Comment | `position.comment` of a record with no object |
| Object comment | `position.comment` of a record with an object |
| Status text | `status.text` |
| Message text | `message.text` |
| Bulletin text | `bulletin.text` |

The tool does not count an empty text.

**Repetition.** A text repeats if it is equal, byte for byte, to the text
before it of the same kind from the same source. For an object comment,
the object name is part of the key. The tool does not measure repetition
for a message or a bulletin.

**Compression.** The tool compresses each text with each of the 17
presets of Unishox2. It decompresses the result and compares it with the
text. A preset fails for a text if the two differ. The size of a text
under a preset follows the rule of RFC 5.7:

- If one length byte and the compressed bytes are shorter than the text,
  the size is their sum.
- If not, the size is the length of the text.
- If the preset fails, the size is the length of the text.

The tool does not compress a text that is not valid UTF-8, or that is
longer than 255 bytes. The script of a text is the script with the most
code points outside ASCII.

Each count is weighted by packets: a text that 100 packets hold counts
100 times.

## 3. Texts

| Text | Texts | Bytes | Mean bytes |
|---|---|---|---|
| Comment | 47,407,719 | 1,706,613,608 | 36.0 |
| Object comment | 10,562,240 | 476,207,085 | 45.1 |
| Status text | 6,944,506 | 290,010,541 | 41.8 |
| Message text | 687,924 | 24,622,522 | 35.8 |
| Bulletin text | 89,399 | 3,635,532 | 40.7 |

The capture has 53,402,756 records with a position and no object.
88.774% of them have a comment. It has 10,766,171 records with
an object. 98.106% of them have a comment.

## 4. Repetition

| Text | Keys | Texts | Repeats | Share of texts | Bytes in repeats | Share of bytes |
|---|---|---|---|---|---|---|
| Comment | 112,561 | 47,407,719 | 38,099,240 | 80.365% | 1,240,123,901 | 72.666% |
| Object comment | 34,556 | 10,562,240 | 8,871,923 | 83.997% | 367,561,200 | 77.185% |
| Status text | 18,701 | 6,944,506 | 5,748,859 | 82.783% | 226,290,773 | 78.028% |

A key is one source, or one object of one source.

The measurement gives a lower limit. A comment with one value that
changes, such as a voltage or a counter, is not a repeat.

## 5. Scripts

| Script | Texts | Bytes | Texts tried | Texts over 255 bytes |
|---|---|---|---|---|
| ascii | 61,228,317 | 2,196,773,929 | 61,162,678 | 65,639 |
| cjk | 2,103,069 | 145,106,031 | 2,000,559 | 102,510 |
| latin | 1,789,905 | 128,075,694 | 1,778,983 | 10,922 |
| not utf-8 | 289,615 | 12,830,290 | 0 | 0 |
| other | 167,471 | 7,450,881 | 167,463 | 8 |
| greek | 56,113 | 4,520,630 | 56,113 | 0 |
| thai | 49,587 | 5,985,467 | 44,011 | 5,576 |
| hebrew or arabic | 5,198 | 283,928 | 5,198 | 0 |
| cyrillic | 2,513 | 62,438 | 2,513 | 0 |

The tool tried 65,217,518 of the 65,691,788 texts.

## 6. Unishox2: all presets

The table gives the size of all tried texts under one preset. The share
is of the 2,427,634,988 bytes tried.

| Preset | Size in bytes | Share | Texts that are shorter compressed | Texts for which the preset fails |
|---|---|---|---|---|
| `URL` | 2,044,778,076 | 84.229% | 80.140% | 0 |
| `FAVOR_ALPHA` | 2,050,150,895 | 84.451% | 83.926% | 0 |
| `ALPHA_NUM_SYM_ONLY` | 2,068,711,781 | 85.215% | 82.814% | 2,274,163 |
| `ALPHA_NUM_SYM_ONLY_TXT` | 2,068,711,781 | 85.215% | 82.814% | 2,274,163 |
| `XML` | 2,075,182,763 | 85.482% | 79.869% | 0 |
| `DFLT` | 2,075,182,793 | 85.482% | 79.869% | 0 |
| `HTML` | 2,085,955,996 | 85.925% | 79.719% | 0 |
| `JSON` | 2,085,976,637 | 85.926% | 79.717% | 0 |
| `FAVOR_DICT` | 2,102,117,037 | 86.591% | 77.325% | 0 |
| `NO_UNI` | 2,103,978,940 | 86.668% | 76.792% | 2,273,815 |
| `NO_DICT` | 2,106,328,683 | 86.765% | 79.726% | 0 |
| `NO_UNI_FAVOR_TEXT` | 2,112,327,629 | 87.012% | 76.721% | 2,273,815 |
| `JSON_NO_UNI` | 2,114,452,701 | 87.099% | 76.640% | 2,273,815 |
| `FAVOR_SYM` | 2,161,544,563 | 89.039% | 67.027% | 0 |
| `FAVOR_UMLAUT` | 2,168,046,050 | 89.307% | 66.254% | 0 |
| `ALPHA_NUM_ONLY` | 2,206,926,069 | 90.908% | 56.456% | 21,882,310 |
| `ALPHA_ONLY` | 2,408,507,295 | 99.212% | 7.249% | 59,076,461 |

With the best preset for each text, the size is 1,973,997,156
bytes, 81.314%. This figure does not count a marker for the
preset. For 11.526% of the texts, no preset gives a shorter form.

The presets with failures cannot encode every character: they have no
code for one or more of the character sets.

## 7. Unishox2: by kind and by script

The columns give the size as a share of the bytes tried.

| Text | Texts tried | Bytes tried | Best preset for each text | `DFLT` | `NO_DICT` | No preset is shorter |
|---|---|---|---|---|---|---|
| Comment | 47,066,792 | 1,642,560,060 | 82.075% | 86.200% | 87.443% | 13.674% |
| Object comment | 10,533,053 | 472,523,213 | 80.283% | 84.057% | 85.708% | 3.801% |
| Status text | 6,843,322 | 284,418,281 | 78.585% | 83.748% | 84.613% | 7.669% |
| Message text | 685,451 | 24,527,238 | 82.305% | 85.300% | 87.077% | 22.329% |
| Bulletin text | 88,900 | 3,606,196 | 78.120% | 82.692% | 83.696% | 3.349% |

| Script | Texts tried | Bytes tried | Best preset for each text | `DFLT` | `NO_DICT` | No preset is shorter |
|---|---|---|---|---|---|---|
| ascii | 61,162,678 | 2,176,743,214 | 81.306% | 85.770% | 87.054% | 11.749% |
| cjk | 2,000,559 | 108,908,514 | 84.942% | 86.797% | 87.967% | 7.559% |
| latin | 1,778,983 | 125,152,594 | 78.994% | 80.393% | 81.846% | 8.789% |
| greek | 56,113 | 4,520,630 | 91.534% | 91.819% | 92.872% | 6.840% |
| thai | 44,011 | 4,515,549 | 50.443% | 51.753% | 51.870% | 0.000% |
| cyrillic | 2,513 | 62,438 | 86.343% | 90.267% | 90.258% | 1.074% |
| hebrew or arabic | 5,198 | 283,928 | 90.899% | 94.669% | 94.669% | 0.500% |
| other | 167,463 | 7,448,121 | 81.608% | 83.633% | 84.265% | 11.539% |

## 8. What the figures show

- Most of the text bytes are repeats. For the comment, the share is
  72.666%. A preset removes about 15% of the text bytes.
  To send a text only when it changes saves more than to compress it.
- The best preset for each text is 2.915 percentage points better than
  the best single preset, `URL`.
- `DFLT` is 1.283 percentage points better than `NO_DICT`.
- `DFLT` and `NO_DICT` fail for no text.
