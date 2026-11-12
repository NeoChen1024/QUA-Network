# QUA Network

An open specification attempt at modernizing APRS.

A research project on a redesign of the APRS application protocol:
one versioned binary PDU with a lossless text form, independent of AX.25 and
of the physical layer, specified in a document rather than by an
implementation.

The project is exploratory. Nothing is frozen, including the name: "QUA
Network" is a working name and may be replaced by a better one. It comes
from the Q code QUA, "Here is news of ..." followed by a call sign. Earlier
drafts used "APRS-next".

APRS is a registered trademark of its owner. QUA Network is an independent
project and is not affiliated with or endorsed by that owner.

- [RFC draft 0](docs/rfc/qua-network-rfc-0.md): requirements and design direction.
- [Documentation index](docs/README.md).
- `vectors/`: conformance test vectors.
- `pysrc/qua_network/`: research tools for capturing and measuring APRS-IS
  traffic and for checking the vectors.

## Tools

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e .
```

| Command | Purpose |
|---|---|
| `qua-is-logger` | Log the APRS-IS full feed to hourly raw files. |
| `qua-corpus-import` | Convert raw corpus files to Parquet, losslessly. |
| `qua-length-stats` | Payload and frame length statistics over the corpus. |
| `qua-check-vectors` | Recompute the conformance vectors and compare. |
| `qua-icon-stats` | Size of the candidate icon bitmap forms on BDF font glyphs. |
| `qua-icon-encode` | Encode a 16 by 16 picture as an icon bitmap field; produce the icon bitmap vectors. |

Each command documents its options under `--help`. The raw corpus lives in
`corpus/` and derived products in `work/`; neither is in Git.

## Licence

Documentation is under CC BY 4.0, conformance vectors under CC0 1.0 and code
under Apache-2.0. See [LICENSE.md](LICENSE.md) for the details, including
the patent statement, and [CONTRIBUTING.md](CONTRIBUTING.md) for how
contributions are licensed.
