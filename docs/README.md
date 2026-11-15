# Documentation index

| Question | Where |
|---|---|
| Why is it designed this way? What was dropped? What is still open? | [`rfc/qua-network-rfc-0.md`](rfc/qua-network-rfc-0.md) |
| What exactly goes on the wire? | `spec/`, one numbered file per topic. A topic moves there from the RFC when it is ready to be worked on as specification text; until then the RFC is the only description. So far: [station identifier](spec/01-station-identifier.md), [icon](spec/02-icon.md), [TLV container](spec/03-tlv.md). |
| Where does a figure come from? | Regenerate it from the corpus with the tools; RFC section 13 gives the method and caveats. The RFC quotes no corpus statistics. `research/` is for a report that fixes a result at a stated capture window, or a reading of third-party code at a stated commit. So far: [free text of the capture](research/01-free-text.md), [Unishox2 implementation](research/02-unishox2-reading.md). |
| What are legacy APRS packets meant to contain, field by field? | [`legacy/`](legacy/README.md): this project's reading of APRS12c, with page citations, the ambiguities it resolves and the errata it found. The legacy tokenizer implements it. |
| What does a decoder give for one legacy packet? How does a gateway translate it, and how is a legacy packet encoded? | [`interop/`](interop/README.md): the record of a legacy packet, its strict and permissive modes, and later the gateway translation and the encoder. Not a QUA Network wire format. So far: [the record, position slice](interop/01-record.md). |
| How does deployed APRS software actually behave? | [`legacy/divergence/`](legacy/divergence/README.md), one file per catalogue entry (RFC Appendix E). [`interop/09-comparison.md`](interop/09-comparison.md) specifies the comparison that finds the entries. |
| What are the conformance values? | [`../vectors/`](../vectors/), checked by `qua-check-vectors`. |

The RFC records direction and rationale and carries a status label on every
item. A specification file states only what an implementer needs and carries
no rationale; while it is a draft its items keep their status labels. Once
a topic has a specification file, that file is authoritative for it, and the
RFC keeps only a summary and the reasons.

## External references

Third-party material is referenced, not copied into this repository.

| Reference | Where | Used for |
|---|---|---|
| APRS Documentation Project (WB2OSZ) | submodule `3rdparty/aprsspec` | What legacy APRS packets are meant to say. See RFC Appendix D for the role of each document. |
| Unishox2 | submodule `3rdparty/Unishox2` | The text compression codec of RFC 5.7, and the implementation that decoder behaviour is checked against. |
| aprs-deviceid | submodule `3rdparty/aprs-deviceid` | Destination callsign to software and device, for `qua-tocall-stats`; the Mic-E device suffixes and the `dest.tocall` identifiers that the legacy tokenizer checks, at commit `c50d026` ([docs/legacy/04-mic-e.md](legacy/04-mic-e.md#amb.mice.suffix), [docs/legacy/01-frame.md](legacy/01-frame.md#dest.tocall)). Read at run time, not copied. CC BY-SA 2.0. |
| aprs-symbols (aprs.fi set, OH7LZB) | submodule `3rdparty/aprs-symbols` | How the symbols of the primary and alternate tables and the overlay characters are drawn, as examples (PNG sheets at several sizes, and the vector source). Not used by any tool. Licensing is per symbol, listed in its `COPYRIGHT.md`: some CC BY-SA 2.0 or public domain, many of unknown origin, a few brand logos. Nothing from it is copied into this repository. |
| aprs-symbol-index (aprs.fi index, OH7LZB) | submodule `3rdparty/aprs-symbol-index`, at commit `68a2734` (2014-06-24) | A machine-readable list of the 185 symbols of the primary and alternate tables, each with its destination-callsign code and a short description (`symbols.csv`, with JSON, XML and YAML versions under `generated/`); overlaid symbols are not listed. Consulted for the names of symbols (`legacy/`). Not used by any tool. CC BY-SA 4.0. Nothing from it is copied into this repository. |
| GNU Unifont | <https://unifoundry.com/unifont/> | A 16-pixel bitmap Unicode font with CJK coverage, suggested as a starting point for embedded designs (RFC 5.6). |
| Fusion Pixel Font | submodule `3rdparty/fusion-pixel-font` | Bitmap fonts with CJK coverage at 8, 10 and 12 pixels, suggested likewise (RFC 5.6). Fonts under OFL 1.1, build tools under MIT. |
| aprslib (aprs-python) | submodule `3rdparty/aprs-python`, at commit `c2a0f18` (2022-09-21) | A parser of legacy packets, for the differential tests of RFC Appendix E ([interop/09-comparison.md](interop/09-comparison.md)). `qua-legacy-compare` runs it as a process of its own. GPL version 2 or later. Nothing from it is copied into this repository. |
| Ham::APRS::FAP (perl-aprs-fap) | submodule `3rdparty/perl-aprs-fap`, at commit `0447564` (2026-02-16), version 1.21 | A parser of legacy packets, used likewise. It needs the Perl module Date::Calc. The terms of Perl: GPL or Artistic License. Nothing from it is copied into this repository. |
| u8g2 | <https://github.com/olikraus/u8g2>, `tools/font/bdf/` | BDF sources of icon fonts (Open Iconic, Siji) and of Unifont, as test sets for `qua-icon-stats` (RFC 5.6). Read at commit `ab9e48b2`. Each font carries its own licence. |
| APRS Protocol Reference 1.0.1, 29 August 2000 | <http://www.aprs.org/doc/APRS101.PDF>; aprs.org blocks automated clients, so the copy consulted was fetched through <https://web.archive.org/web/2023id_/http://www.aprs.org/doc/APRS101.PDF> | The original that APRS12c compiles. Used to tell defects inherited from 1.0.1 from those introduced later (`legacy/`). |
| APRS-IS q-construct definition (AE5PL): "q Construct" and "q Algorithm" | <https://aprs-is.net/q.aspx> and <https://aprs-is.net/qalgorithm.aspx>; pinned as the Wayback snapshots <https://web.archive.org/web/20251121184238id_/https://www.aprs-is.net/q.aspx> and <https://web.archive.org/web/20260210071804id_/https://aprs-is.net/qalgorithm.aspx> | What a q-construct in an APRS-IS path means, which APRS12c names but does not define (`legacy/`, 01-frame `path.q`). aprsc (`legacy/README.md` section 4) is read as an implementation of it. |
| AX.25 Link Access Protocol v2.2, July 1998 | <https://www.ax25.net/AX25.2.2-Jul%2098-2.pdf> | Legacy framing: the address field layout behind the first-byte rule (RFC 5.1) and the optional encapsulation (RFC 7.2). |

The AX.25 document is linked rather than stored because it is copyrighted by
TAPR and ARRL. The copy consulted is 2,842,014 bytes, 135 pages, SHA-256
`5a4aac0bc10a69c5c983c35d5a84cc47ff204fa785a765fa1d2d6dd620131350`.

APRS 1.0.1 is linked for the same reason (copyright 2000 APRS Working
Group). The copy consulted is 3,173,392 bytes, 128 pages, SHA-256
`31df2904d982f83621ebb16ed379e4da3b5507db0dba7c9513e3815ff1ed62f8`.

The APRS-IS pages carry a copyright notice of AE5PL and no licence, so
they are linked too, and the copies consulted are kept under `work/`.
The live pages carry no version; the Wayback snapshots above are the
pinned versions. The copies are 11,996 bytes, SHA-256
`4fecdc7f3237bdaba289700a1c31351a3df3faaaad3d9bd87d414382c745480b`
(q Construct), and 7,537 bytes, SHA-256
`68ec642c9386a1b4dce03f41906e4e05bfb9d4ec3a63ed336c4a7ef7a5d47734`
(q Algorithm, which states it was last updated on 1 June 2012).

Searchable Markdown copies of the APRS documents and the AX.25 PDF are made
locally with `qua-spec-extract`, into `work/refs/text/` by default. They are
never committed.
