# QUA Network — Agent guide

QUA Network is a specification-first redesign of the APRS application protocol.
The deliverable is a document from which an independent implementation can be
written; code in this repository exists to measure, verify and exercise it.

"QUA Network" is a working name and may change again. Do not build it into
anything that would be costly to rename: wire-format constants, text-form
markers, hash context strings or registry names. The package and command
names are provisional too. The project was first drafted as "APRS-next". Do
not put "APRS" into a name of anything in this project.

## Sources of truth

- [Documentation index](docs/README.md): routes design-rationale questions to
  `docs/rfc/`, normative wire-format questions to `docs/spec/`, and
  measurement questions to `docs/research/`.
- [RFC draft](docs/rfc/qua-network-rfc-0.md): design direction, rationale,
  dropped alternatives, open questions. Its Appendix D lists the legacy APRS
  references.
- `docs/spec/`: specification drafts, one numbered file per topic. A topic
  that has a file there is specified there and nowhere else.
- `vectors/`: machine-readable conformance vectors. Tables in the documents
  are copies; when they disagree, the vector file is authoritative.
- `3rdparty/`: pinned upstream references.
  The [documentation index](docs/README.md#external-references) lists these
  and the references that are linked instead of stored.
- Tool `--help` owns usage and options.

Keep this guide about workflow. Update the owning document when a rule
changes; link to it instead of restating formats, constants or figures here.

## Decision status

- Every design item carries `[agreed]`, `[proposed]` or `[open]`. Only the
  author changes a label. Do not promote an item, or write new text as
  `[agreed]`, because it seems reasonable; add it as `[proposed]` or `[open]`.
- When a design is replaced, keep a short note of what was dropped and why.
  Do not silently delete it.
- A change that resolves or raises a question updates the open-questions and
  next-steps lists in the same edit. A new class of mistake goes in the
  pitfalls list.
- Section numbers are cross-referenced throughout. After adding, removing or
  moving a section, check every reference to it.
- RFC 2119 keywords appear only in requirements, in capitals. Do not use them
  in rationale or description.
- Section 10 (authentication) is unreviewed. Do not describe any part of it
  as secure or sound.

## RFC and specification files

- When a topic has a file in `docs/spec/`, change the rules there. The RFC
  section keeps a short summary, the reasons and the dropped alternatives,
  and links to the file. Do not restate formats, tables or rules in both.
- A specification file states what an implementer must do and carries no
  rationale. Reasons go in the RFC section it links to.
- Items in a specification draft keep their status labels until the file is
  frozen. The rules under "Decision status" apply to them unchanged.
- A specification file lists its own open items. A cross-cutting question
  also stays in the RFC's open-questions list.
- Moving a topic out of the RFC keeps its section number in place, so that
  existing references stay valid.

## Numbers and claims

- The RFC is a reference for design direction and is not kept in step with
  the corpus. Do not write corpus statistics into it. The capture is still
  growing, so figures are regenerated with the tools when they are needed;
  the RFC states only the qualitative observation and points to its
  measurement section.
- A corpus figure reported anywhere (a task response, a research report)
  comes from a run of a tool in this repository and names the capture
  window and packet count of that run. Never fill in a plausible value, and
  do not carry a figure over from an earlier run as if it were current.
- Other figures in a document are cited to a source, derived in the text,
  or explicitly marked unverified.
- Statements about third-party behaviour (Dire Wolf, Unishox2, IL2P,
  transceiver datasheets) say whether they were read, run or recalled, and
  against which version or commit.

## Test vectors

- A vector is computed by a path independent of the code it will be used to
  check (a separate script, a published check value, a different library),
  and the document records how.
- Fixed wire values are compatibility contracts. Changing an existing vector
  is a format change and needs the author's decision; adding vectors is not.
- Round-trip agreement between an encoder and its own decoder is not
  evidence that either is correct.
- Run `qua-check-vectors` after touching `vectors/`, `identifier.py`, `icon.py`, or
  any document table that quotes a vector.

## Data safety

- `corpus/` holds the raw capture and is read-only. `work/` holds derived
  products. Neither is committed; documents quote only the example packets
  they need.
- Corpus lines are raw bytes, not UTF-8. Read them as bytes; do not decode,
  normalise or strip them. In Parquet, packet content is a `binary` column,
  never `string`.
- The raw corpus is the source of truth and is still being collected.
  Parquet under `work/` is a derived cache; bring it up to date with
  `qua-corpus-import` before measuring.
- Project-owned Parquet writers use Zstandard level 3 explicitly:
  `compression="zstd", compression_level=3`.
- Publish completed outputs by rename. Do not overwrite an existing product
  in place.

## Python tools

- Python lives in `pysrc/qua_network/`. Runtime dependencies are in
  `requirements.txt`, consumed by `pyproject.toml`, with minimum versions
  (`>=`) and no lockfile. A new dependency needs a reason.
- Use Click for CLIs, with a `cli` entry point registered in
  `pyproject.toml` under the `qua-` prefix.
- Use tqdm for progress, updated per file or per batch and not per packet.
  When stdout carries results, progress and diagnostics go to stderr.
- Use pyarrow for tabular reads and writes. Process the corpus in bounded
  batches; do not load a whole capture into memory.
- Use the `blake3` package for hashing. No other hash function appears in
  the tools unless a document requires it.
- An analysis with no dependency between records in different files runs in
  parallel with one corpus file as the unit of work, through `parallel.py`.
  Workers return per-file results that the parent merges; the result must
  not depend on completion order. Only an analysis that needs state carried
  across files (per-station history, deduplication) runs sequentially.
- Search the package for an existing parser or counter before writing
  another. Corpus files and TNC2 line splitting belong to `tnc2.py`;
  identifier encoding and hop hashes belong to `identifier.py`; icon colour
  values belong to `icon.py`.
- A measurement tool prints the input file range and the packet count
  alongside its results, so a figure can be traced to a run.

## Licensing and third-party material

- [LICENSE.md](LICENSE.md) owns the licensing terms: documentation is
  CC BY 4.0, `vectors/` is CC0 1.0, code is Apache-2.0. New Python files
  start with `# SPDX-License-Identifier: Apache-2.0`.
- Commits are signed off (`git commit -s`), as
  [CONTRIBUTING.md](CONTRIBUTING.md) requires.
- Third-party code is referenced, not copied: a submodule under
  `3rdparty/`, or a recorded repository URL and commit hash. Several are
  GPL; no code from them enters this project's own files.
- Do not copy text or tables from the APRS protocol reference or the AX.25
  specification into project files. Their terms do not allow it. Describe
  the behaviour in your own words and cite the source; a short quotation
  with attribution is the limit.
- Do not modify submodule contents.

## Specification versus implementation

- The specification leads. If implementing something exposes an ambiguity or
  a gap, fix the document first; behaviour must not be defined by what the
  code happens to do.
- Do not add a feature to an implementation that the documents do not
  describe.
- The Python package is a research aid, not a reference implementation.

## Language and style

- Project files are in English, including documentation and comments.
  Preserve quoted packets and external identifiers as they are. User
  communication need not be English.
- Python targets 3.11+. Black (132 columns) and isort (Black profile), as
  configured in `pyproject.toml` and the pre-commit hooks.
- Comments explain intent, invariants or non-obvious control flow, not
  individual statements.

## Local toolchain and verification

- Use the repository-root `./.venv`, managed by uv. Do not fall back to
  system Python. Create it with `uv venv .venv` only if absent, and install
  with `uv pip install --python .venv/bin/python -e .`.
- Test a corpus tool on a single hourly file before a full run.
- Do not add automated tests unless asked. Validate with representative
  input and direct inspection of the output, and report what was checked.
