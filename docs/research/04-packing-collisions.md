# Collisions with several PDUs in one frame

| | |
|---|---|
| Kind | Research report. It fixes the result of a simulation with stated parameters. It is not a specification, and it is not a measurement of a real channel. |
| Question | RFC 7.1, "More than one PDU in a frame"; [`docs/spec/08-pdu.md`](../spec/08-pdu.md) section 7.1 |
| Tool | `qua-channel-sim` |

## 1. Run

| | |
|---|---|
| Command | `qua-channel-sim -j 12`, with the default value of each option |
| Tool | The version of the commit that adds this report |
| Seeds | 0 to 15, for each case |
| Output | `work/sim/channel-sim-r1.txt` |

The tool does not read the corpus. A result depends only on the
parameters and on the seeds. The run under CPython and a run under PyPy
gave the same output.

## 2. Question

A link unit can hold more than one PDU. A frame with several PDUs is on
the channel for a longer time than a frame with one PDU. Does this cause
more collisions?

## 3. Model

- One channel has 30 stations and one receiver. The receiver hears each
  station.
- A station hears each other station with a probability `h`. With `h`
  = 1, the channel has no hidden station. With `h` = 0, each station is
  hidden from each other station.
- Each station gets groups of PDUs at Poisson times. A group has 2 or 4
  PDUs. One run has 40000 groups for all stations together.
- A station that packs sends one frame for a group. A station that does
  not pack sends one frame for each PDU of the group.
- Access is p-persistent CSMA. If the station hears no carrier, it
  transmits with the probability `p`. If not, it waits for one slot and
  tries again. If it hears a carrier, it waits for the end of that
  transmission.
- A frame is lost if a different frame overlaps it at the receiver.
- The load is the airtime of all frames as a share of time, if no
  station packs.

The parameters:

| Parameter | Value | Source |
|---|---|---|
| Bit rate | 1200 bit/s | The AFSK link of RFC 7.1 |
| Preamble | 0.3 s | Assumed. The author gives 200 to 500 ms for TXDELAY. |
| PDU | 28 bytes | A Position PDU with coordinates ([10-position](../spec/10-position.md) section 5) |
| Flags and FCS | 4 bytes for each frame | Two flags and the FCS of HDLC. Bit stuffing is not counted. |
| `p` | 64/256 | Assumed: the KISS persistence value 63. pico_tnc has this default. |
| Slot | 0.1 s | Assumed. pico_tnc has this default. |
| Carrier detection | 0.02 s after the start of a transmission | Assumed |

The defaults of pico_tnc were read in the source (`tnc.c`, `send.c`) at
commit `0711f6b` (2025-08-22), not run. Its default TXDELAY is 100
flags. This is 0.667 s at 1200 bit/s (derived), more than the preamble
of this run.

A frame with 1 PDU takes 0.513 s. A frame with 2 PDUs takes 0.700 s, and
a frame with 4 PDUs takes 1.073 s.

The run has four cases for each load: no station packs, each station
packs, 15 of the 30 stations pack, and 1 station packs.

## 4. Results

The figures are the share of the PDUs that are lost. In the columns
"half" and "one", the first figure is for the stations that pack and the
second is for the other stations.

Groups of 2 PDUs:

| `h` | Load | None packs | All pack | Half: pack / others | One: pack / others |
|---|---|---|---|---|---|
| 1 | 0.05 | 1.13% | 0.22% | 0.58% / 0.80% | 0.90% / 1.13% |
| 1 | 0.1 | 2.40% | 0.51% | 1.21% / 1.61% | 2.01% / 2.32% |
| 1 | 0.2 | 5.30% | 1.29% | 2.83% / 3.58% | 4.48% / 5.15% |
| 1 | 0.4 | 12.56% | 3.71% | 7.53% / 8.75% | 11.16% / 12.26% |
| 0.5 | 0.05 | 4.70% | 3.37% | 4.34% / 3.91% | 4.80% / 4.64% |
| 0.5 | 0.1 | 9.22% | 6.70% | 8.27% / 7.67% | 9.87% / 9.07% |
| 0.5 | 0.2 | 17.89% | 13.09% | 16.16% / 15.10% | 18.86% / 17.76% |
| 0.5 | 0.4 | 34.23% | 25.38% | 31.05% / 28.92% | 36.33% / 33.91% |
| 0 | 0.05 | 7.99% | 6.40% | 7.71% / 6.71% | 8.95% / 7.94% |
| 0 | 0.1 | 15.46% | 12.44% | 14.89% / 13.04% | 16.97% / 15.27% |
| 0 | 0.2 | 28.48% | 23.23% | 27.65% / 24.47% | 31.04% / 28.17% |
| 0 | 0.4 | 49.01% | 41.20% | 47.40% / 42.97% | 53.22% / 48.51% |

Groups of 4 PDUs:

| `h` | Load | None packs | All pack | Half: pack / others | One: pack / others |
|---|---|---|---|---|---|
| 1 | 0.05 | 1.52% | 0.12% | 0.70% / 0.89% | 1.26% / 1.47% |
| 1 | 0.1 | 3.11% | 0.26% | 1.45% / 1.81% | 2.72% / 3.04% |
| 1 | 0.2 | 6.62% | 0.63% | 3.27% / 3.95% | 5.78% / 6.46% |
| 1 | 0.4 | 14.62% | 1.79% | 7.70% / 8.75% | 13.51% / 14.34% |
| 0.5 | 0.05 | 4.50% | 2.51% | 4.00% / 3.26% | 5.36% / 4.45% |
| 0.5 | 0.1 | 8.93% | 5.09% | 7.67% / 6.42% | 10.06% / 8.69% |
| 0.5 | 0.2 | 17.38% | 10.04% | 15.12% / 12.86% | 19.70% / 17.10% |
| 0.5 | 0.4 | 33.14% | 19.62% | 28.87% / 24.74% | 36.73% / 32.46% |
| 0 | 0.05 | 7.35% | 4.92% | 7.09% / 5.48% | 8.69% / 7.34% |
| 0 | 0.1 | 14.17% | 9.63% | 13.49% / 10.68% | 16.77% / 14.01% |
| 0 | 0.2 | 26.48% | 18.33% | 25.47% / 20.33% | 31.36% / 26.10% |
| 0 | 0.4 | 46.06% | 33.30% | 44.56% / 36.50% | 53.59% / 45.58% |

The airtime share of the channel, measured in the run: with groups of 2,
a load of 0.2 becomes 0.136 if each station packs. With groups of 4, it
becomes 0.105.

In the case "one", the one station sent about 42,000 PDUs with groups of
2 and about 85,000 PDUs with groups of 4, in the 16 runs together.

## 5. What the results show

- If each station packs, fewer PDUs are lost than if no station packs.
  This is so in each row.
- With no hidden station, the gain is large. A collision then occurs
  only at the start of a transmission, and packing makes the number of
  transmissions smaller. The one station that packs also loses fewer
  PDUs than before.
- With hidden stations, a station that packs loses more PDUs than a
  station that does not pack on the same channel. The longer frame is
  open to a collision for a longer time.
- With hidden stations, one station that packs alone loses more PDUs
  than it lost with short frames: 31.04% and not 28.48% at `h` = 0, a
  load of 0.2 and groups of 2. The other stations gain a little.
- With half of the stations packing, each station loses fewer PDUs than
  in the case in which no station packs.

A station that packs alone on a channel with hidden stations therefore
pays a small cost, and the channel gains. The gain for each station
comes when many stations pack.

## 6. Limits

- The model has no capture effect, no bit error and no relay. A real
  receiver can decode the stronger of two frames. A bit error loses each
  PDU of a frame, and a longer frame has more bits.
- Each PDU has 28 bytes. A larger PDU makes the preamble a smaller part
  of the frame, so packing saves less.
- In the model, the PDUs of a group are due at one time. A station that
  holds a PDU back to pack it is not in the model.
- The preamble, the slot, `p` and the carrier detection time are
  assumed values. They were not measured on a TNC. A longer preamble
  makes the saving of packing larger.
- One collision loses each PDU of a frame together. The figures count
  PDUs, so they do not show this.
