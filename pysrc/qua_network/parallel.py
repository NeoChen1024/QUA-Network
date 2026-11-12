# SPDX-License-Identifier: Apache-2.0
"""Run a per-file analysis across corpus files in parallel."""

import os
from multiprocessing import Pool

import click
from tqdm import tqdm

jobs_option = click.option(
    "-j",
    "--jobs",
    type=click.IntRange(min=1),
    default=os.process_cpu_count() or 1,
    show_default="CPU count",
    help="Worker processes; one file is one unit of work.",
)


def _call(task):
    func, path = task
    return path, func(path)


def map_files(func, files, jobs):
    """Yield (path, func(path)) for every file, in completion order.

    func must be picklable (a module-level function or a functools.partial
    of one) and its results must be mergeable in any order.
    """
    if jobs == 1 or len(files) <= 1:
        for path in tqdm(files, unit="file"):
            yield path, func(path)
        return
    with Pool(min(jobs, len(files))) as pool:
        yield from tqdm(pool.imap_unordered(_call, [(func, f) for f in files]), total=len(files), unit="file")
