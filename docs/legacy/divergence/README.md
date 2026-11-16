# Divergence catalogue

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning that the RFC gives them. |
| Rationale | [RFC draft 0](../../rfc/qua-network-rfc-0.md): Appendix E |
| Method | [docs/interop/09-comparison.md](../../interop/09-comparison.md) |

## 1. Purpose

This directory is the divergence catalogue of RFC Appendix E. An entry
records one place where a deployed parser gives a result that is
different from the record of this project, or from another parser.

**[proposed]** These statements limit this directory:

- An entry does not say which side is correct.
- An entry does not change a rule of the numbered files of
  [docs/legacy](../README.md). Rule 6 of that README applies.
- An entry can be a reason to change the record of
  [docs/interop](../../interop/README.md). The author decides each
  change.
- An entry can be the reason for a repair of permissive mode
  ([01-record section 3.1](../../interop/01-record.md#31-repairs)). The
  entry then names the repair in its decision.
- The numbered files list the places where APRS12c fails. If such a row
  exists for an entry, the entry links to it.

## 2. Terms

| Term | Meaning |
|---|---|
| parser | A program of a third party that decodes legacy packets ([09-comparison section 2](../../interop/09-comparison.md#2-parsers)). |
| record | The output of the decoder of this project for one legacy packet. |
| entry | One file of this directory. |
| run | One execution of `qua-legacy-compare` on corpus files (section 5). |
| path | The name of a compared field, for example `position.lat` ([09-comparison section 4](../../interop/09-comparison.md#4-view-of-a-record)). |

## 3. Entry format

**[agreed]** The catalogue is in this directory. Each entry is one
numbered file. An entry has these parts, as RFC Appendix E.3 lists them:

| Part | Content |
|---|---|
| Description | What is different, in one paragraph. |
| Category | A category of RFC Appendix E.2. |
| Example | A packet, and what each side gives for it. |
| Frequency | Counts of a run. |
| Behaviour | What each parser does, and how this project knows it. |
| APRS12c | The pages, and the row of the numbered files if one exists. |
| Decision | What QUA Network or the record does about it, with a status label. |

**[proposed]** These rules apply to an entry:

- The ID of an entry starts with `div.`.
- An example packet is written for the entry. Its source is `N0CALL`. It
  is not a corpus line.
- The example gives what each side returns for that packet in a run of
  the tool. The parsers are at the commits of section 4.
- A statement about the code of a parser says "read". The commit is that
  of section 4.
- A frequency names its run.
- If no category of RFC Appendix E.2 applies, the entry says so.

## 4. Parsers

**[proposed]** The statements of the entries apply to these versions:

| Name | Parser | Submodule | Commit |
|---|---|---|---|
| `fap` | Ham::APRS::FAP, version 1.21 | `3rdparty/perl-aprs-fap` | `0447564` |
| `pythonlib` | aprslib | `3rdparty/aprs-python` | `c2a0f18` |

## 5. Runs

| Run | Input files | Packets | Mode of the decoder | Decoder and tool at commit |
|---|---|---|---|---|
| r5 | `aprsis-20261104-03.log` to `aprsis-20261114-11.log`, 249 files | 84,560,319 | permissive | `25507fe` |
| r6 | The files of run r5 | 84,560,319 | permissive | The commit that adds this run |

**[proposed]** A run counts packets for each path, not for each cause.
An entry gives the counts of its paths. The cause is what the inspected
examples of the run show and what the code of the parser says. The count
of one cause alone is not measured.

Run r6 differs from run r5 in the humidity rule only
([04-humidity-width.md](04-humidity-width.md)). Only that entry uses run
r6. In run r6, three paths have counts that are different from run r5:
`weather.humidity`, `weather.pressure` and `position.comment`.

The classes of run r5 and of run r6 are the same:

| Parser | `both` | `ours-only` | `theirs-only` | `neither` |
|---|---|---|---|---|
| `fap` | 83,053,600 | 530,770 | 82,963 | 892,986 |
| `pythonlib` | 76,488,477 | 7,095,893 | 113,001 | 862,948 |

## 6. Entries

| File | ID | Difference |
|---|---|---|
| [01-comment.md](01-comment.md) | `div.comment` | The fields that a parser removes from the comment of a position. |
| [02-wind-unit.md](02-wind-unit.md) | `div.wind-unit` | The unit of the wind speed in the 7-byte wind field. |
| [03-ambiguity.md](03-ambiguity.md) | `div.ambiguity` | The point that a position with ambiguity gives. |
| [04-humidity-width.md](04-humidity-width.md) | `div.humidity-width` | A humidity field with three digits. |
| [05-status-locator.md](05-status-locator.md) | `div.status-locator` | A Maidenhead locator at the start of a status text. |
| [06-overlay-letter.md](06-overlay-letter.md) | `div.overlay-letter` | The table byte `a` to `j` of a compressed position. |
| [07-course-zero.md](07-course-zero.md) | `div.course-zero` | The course code 0 of a compressed position. |
| [08-temperature-width.md](08-temperature-width.md) | `div.temperature-width` | A temperature field with more than three bytes. |
| [09-ack-number.md](09-ack-number.md) | `div.ack-number` | An acknowledgement whose number has a `}`. |
| [10-compressed-wind.md](10-compressed-wind.md) | `div.compressed-wind` | A 7-byte wind field after a compressed position. |

## 7. Open items

- **[open]** A count for each cause. The tool counts for each path only.
- **[open]** A category for a format that APRS12c specifies and that a
  parser does not decode. RFC Appendix E.2 has none.
- **[open]** The other parsers of RFC Appendix E.1.
- **[open]** Run r5 shows these differences too. They have no entry yet,
  and no person has read the code for them:
  - the messaging flag of Mic-E, which only the record gives;
  - a Mic-E course of 0 and the pair `000/000`, for which `fap` gives the
    course 0;
  - the wind field `000/000`, for which `fap` gives the direction 0;
  - a base-91 telemetry block with fewer than five values, for which
    `pythonlib` gives 0 for each absent value;
  - a telemetry report with more than eight digital bits;
  - a packet with bytes before the `!`, which `fap` decodes as a
    position;
  - raw weather reports and raw NMEA sentences, which `fap` decodes and
    for which the record has no body;
  - a snowfall field, which `pythonlib` can read as the wind speed;
  - a compressed altitude together with an altitude in the comment.
