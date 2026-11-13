# SPDX-License-Identifier: Apache-2.0
"""Corpus files and TNC2 lines, handled as raw bytes.

A corpus file is what ``qua-is-logger`` writes: one record per line,

    <unix_time>\\t<raw TNC2 line>\\n

Nothing here decodes, normalises or validates packet content.
"""

import glob
import gzip
import os

# q-constructs counted as heard over the air by an IGate.
RF_Q = frozenset({b"qAR", b"qAo", b"qAO"})


def log_files(log_dir):
    """Hourly corpus files in a directory, in name (and therefore time) order."""
    return sorted(glob.glob(os.path.join(log_dir, "aprsis-*.log")) + glob.glob(os.path.join(log_dir, "aprsis-*.log.gz")))


def open_log(path):
    return gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")


def read_records(path):
    """Yield each record of a corpus file without its line terminator.

    A gzip file cut off mid-write raises EOFError after the last complete
    record; the caller decides whether to keep what was read.
    """
    with open_log(path) as fh:
        for raw in fh:
            yield raw.rstrip(b"\r\n")


def split_record(record):
    """Return (unix_time, line). unix_time is the logged ASCII decimal, or None if absent."""
    ts, sep, rest = record.partition(b"\t")
    if sep and ts.replace(b".", b"", 1).isdigit():
        return ts, rest
    return None, record


def unix_ms(ts):
    """Logged time as integer milliseconds, without going through a float."""
    sec, _, frac = ts.partition(b".")
    return int(sec or b"0") * 1000 + int((frac + b"000")[:3])


def split_payload(line):
    """Return (header, payload) split at the first ':'. payload is None when there is no ':'."""
    header, sep, payload = line.partition(b":")
    return (header, payload) if sep else (line, None)


def header_spans(header, base=0):
    """Split an address header into byte spans, without judging their content.

    Returns (source, destination, entries) where each item is a (start, end)
    span of the header, offset by base, and entries lists the path entries
    in order. Separators are not part of any span: source ends at the first
    '>', destination and each entry at the next ',' or the end. Returns None
    when there is no '>'.
    """
    gt = header.find(b">")
    if gt < 0:
        return None
    spans = []
    start = gt + 1
    while True:
        comma = header.find(b",", start)
        if comma < 0:
            spans.append((base + start, base + len(header)))
            break
        spans.append((base + start, base + comma))
        start = comma + 1
    return (base, base + gt), spans[0], spans[1:]


def parse_header(header):
    """Return (source, destination, n_digis, q_construct), or None if the header is not SRC>DST[,path],qA?,gate.

    n_digis counts the addresses between the destination and the q-construct,
    whether or not they were used.
    """
    src, gt, rest = header.partition(b">")
    if not gt or not src:
        return None
    path = rest.split(b",")
    q_idx = next((i for i, p in enumerate(path) if p.startswith(b"qA")), None)
    if q_idx is None:
        return None
    return src, path[0], q_idx - 1, path[q_idx]
