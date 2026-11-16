# SPDX-License-Identifier: Apache-2.0
"""Simulate the loss of PDUs on one shared channel, with and without packing
(docs/research/04-packing-collisions.md).

Stations send to one receiver that hears each station. A station hears each
other station with the probability of --hears: 1 gives a channel with no
hidden station, and 0 gives a channel in which each station is hidden from
each other station. Access is p-persistent CSMA.

Each station gets groups of --group PDUs at Poisson times. A station that
packs sends one frame for a group. A station that does not pack sends one
frame for each PDU of the group. A frame is lost if a different frame
overlaps it at the receiver. The model has no capture effect, no bit error
and no relay.

The load is the airtime of all frames as a share of time, if no station
packs. The tool runs four cases for each load: no station packs, each
station packs, half of the stations pack, and one station packs. It prints
the share of the PDUs that are lost.

The tool prints its parameters with the results. A result depends only on
the parameters and on the seeds.
"""

import heapq
import random
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import click

GROUP_DUE, ATTEMPT, SENT = 0, 1, 2
CASES = (("none", 0), ("all", None), ("half", None), ("one", 1))


@dataclass(frozen=True)
class Channel:
    stations: int
    bit_rate: float
    preamble: float
    pdu: int
    frame: int
    persist: float
    slot: float
    detect: float
    groups: int

    def airtime(self, pdus):
        """Seconds of one frame with the given number of PDUs."""
        return self.preamble + (pdus * self.pdu + self.frame) * 8 / self.bit_rate


def run(ch, load, group, hears_share, packers, seed):
    """One run. packers is the number of stations that pack. Returns the
    PDUs sent and the PDUs received, for the stations that pack and for the
    others, and the share of time with a transmission."""
    rng = random.Random(seed)
    n = ch.stations
    hears = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i):
            hears[i][j] = hears[j][i] = rng.random() < hears_share
    packs = [i < packers for i in range(n)]
    rate = load / (n * group * ch.airtime(1))  # groups in a second for one station
    events = [(rng.expovariate(rate), GROUP_DUE, i) for i in range(n)]
    heapq.heapify(events)
    queue = [[] for _ in range(n)]
    start = [-1.0] * n
    end = [-1.0] * n
    waiting = [False] * n  # the station has an event for its next attempt, or it transmits
    sent = []  # (start, end, station, PDUs)
    made = 0
    while events:
        t, kind, i = heapq.heappop(events)
        if kind == GROUP_DUE:
            if made < ch.groups:
                made += 1
                heapq.heappush(events, (t + rng.expovariate(rate), GROUP_DUE, i))
                queue[i].extend([group] if packs[i] else [1] * group)
        else:
            waiting[i] = False
        if not queue[i] or waiting[i]:
            continue
        busy_until = 0.0
        for j in range(n):
            if hears[i][j] and start[j] + ch.detect <= t < end[j]:
                busy_until = max(busy_until, end[j])
        waiting[i] = True
        if busy_until:
            heapq.heappush(events, (busy_until, ATTEMPT, i))
        elif rng.random() < ch.persist:
            pdus = queue[i].pop(0)
            start[i], end[i] = t, t + ch.airtime(pdus)
            sent.append((t, end[i], i, pdus))
            heapq.heappush(events, (end[i], SENT, i))
        else:
            heapq.heappush(events, (t + ch.slot, ATTEMPT, i))
    sent.sort()
    ok = [True] * len(sent)
    latest, at = -1.0, -1
    for k, (s, e, _, _) in enumerate(sent):
        if s < latest:  # it overlaps the frame that ends last so far
            ok[k] = ok[at] = False
        if e > latest:
            latest, at = e, k
    counts = {True: [0, 0], False: [0, 0]}
    busy = 0.0
    for k, (s, e, i, pdus) in enumerate(sent):
        counts[packs[i]][0] += pdus
        counts[packs[i]][1] += pdus if ok[k] else 0
        busy += e - s
    return counts, busy / max(e for _, e, _, _ in sent)


def _job(args):
    return args[1:5], run(*args)


def _lost(c):
    return f"{100 * (1 - c[1] / c[0]):6.2f}%" if c[0] else "      -"


@click.command(help=__doc__, context_settings={"help_option_names": ["-h", "--help"], "show_default": True})
@click.option("--stations", type=click.IntRange(min=2), default=30, help="Stations on the channel.")
@click.option("--bit-rate", type=float, default=1200.0, help="Bits in a second.")
@click.option("--preamble", type=float, default=0.3, help="Seconds before the first frame of a transmission (TXDELAY).")
@click.option("--pdu", type=click.IntRange(min=1), default=28, help="Bytes of one PDU.")
@click.option("--frame", type=click.IntRange(min=0), default=4, help="Bytes of flags and FCS for one frame.")
@click.option("--persist", type=click.IntRange(0, 255), default=63, help="The persistence value of KISS: p is (value + 1) / 256.")
@click.option("--slot", type=float, default=0.1, help="Seconds of one slot of the persistence.")
@click.option(
    "--detect", type=float, default=0.02, help="Seconds from the start of a transmission to the detection of its carrier."
)
@click.option("--group", "groups_of", type=click.IntRange(min=2), multiple=True, default=(2, 4), help="PDUs in one group.")
@click.option(
    "--hears",
    type=click.FloatRange(0, 1),
    multiple=True,
    default=(1.0, 0.5, 0.0),
    help="Share of station pairs that hear each other.",
)
@click.option("--load", type=float, multiple=True, default=(0.05, 0.1, 0.2, 0.4), help="Airtime share if no station packs.")
@click.option("--groups", type=click.IntRange(min=1), default=40000, help="Groups in one run, for all stations together.")
@click.option("--seeds", type=click.IntRange(min=1), default=16, help="Runs for each case. The seeds are 0, 1, 2 and so on.")
@click.option("-j", "--jobs", type=click.IntRange(min=1), default=1, help="Worker processes.")
def cli(stations, bit_rate, preamble, pdu, frame, persist, slot, detect, groups_of, hears, load, groups, seeds, jobs):
    ch = Channel(stations, bit_rate, preamble, pdu, frame, (persist + 1) / 256, slot, detect, groups)
    packers = {"none": 0, "all": stations, "half": stations // 2, "one": 1}
    work = [
        (ch, x, m, h, packers[name], seed)
        for m in groups_of
        for h in hears
        for x in load
        for name, _ in CASES
        for seed in range(seeds)
    ]
    total = {}
    with ProcessPoolExecutor(jobs) as pool:
        for key, (counts, busy) in pool.map(_job, work, chunksize=1):
            entry = total.setdefault(key, ({True: [0, 0], False: [0, 0]}, [0.0]))
            for c in counts:
                entry[0][c][0] += counts[c][0]
                entry[0][c][1] += counts[c][1]
            entry[1][0] += busy / seeds
    echo = click.echo
    echo(f"stations={stations}  bit rate={bit_rate:g}  preamble={preamble:g} s  PDU={pdu} B  frame={frame} B")
    echo(f"persistence={persist} (p={ch.persist:.4f})  slot={slot:g} s  detect={detect:g} s  groups={groups}  seeds=0..{seeds - 1}")
    for m in groups_of:
        echo(
            f"\n== groups of {m} PDUs: a frame with 1 PDU has {ch.airtime(1):.3f} s, a frame with {m} PDUs has {ch.airtime(m):.3f} s =="
        )
        echo("  hears  load   none     all      half: pack / others   one: pack / others   airtime: none  all   PDUs of the one")
        for h in hears:
            for x in load:
                c = {name: total[(x, m, h, packers[name])] for name, _ in CASES}
                echo(
                    f"  {h:<5g}  {x:<5g}  {_lost(c['none'][0][False])}  {_lost(c['all'][0][True])}  "
                    f"{_lost(c['half'][0][True])} / {_lost(c['half'][0][False])}    "
                    f"{_lost(c['one'][0][True])} / {_lost(c['one'][0][False])}    "
                    f"{c['none'][1][0]:.3f}  {c['all'][1][0]:.3f}  {c['one'][0][True][0]}"
                )


if __name__ == "__main__":
    cli()
