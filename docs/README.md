# Documentation index

| Question | Where |
|---|---|
| Why is it designed this way? What was dropped? What is still open? | [`rfc/qua-network-rfc-0.md`](rfc/qua-network-rfc-0.md) |
| What exactly goes on the wire? | `spec/`, one numbered file per topic. A topic moves there from the RFC when it is ready to be worked on as specification text; until then the RFC is the only description. So far: [station identifier](spec/01-station-identifier.md), [icon](spec/02-icon.md), [TLV container](spec/03-tlv.md). |
| Where does a figure come from? | Regenerate it from the corpus with the tools; RFC section 13 gives the method and caveats. The RFC quotes no corpus statistics. `research/` is for a report that fixes a result at a stated capture window. Not started. |
| What are legacy APRS packets meant to contain, field by field? | [`legacy/`](legacy/README.md): this project's reading of APRS12c, with page citations, the ambiguities it resolves and the errata it found. The legacy tokenizer implements it. |
| How does deployed APRS software actually behave? | `divergence/`, one file per catalogue entry (RFC Appendix E). Not started. |
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
| Unishox2 | submodule `3rdparty/Unishox2` | The text compression codec of RFC 5.7, and the reference encoder its behaviour is checked against. |
| aprs-deviceid | submodule `3rdparty/aprs-deviceid` | Destination callsign to software and device, for `qua-tocall-stats`. CC BY-SA 2.0. |
| GNU Unifont | <https://unifoundry.com/unifont/> | A 16-pixel bitmap Unicode font with CJK coverage, suggested as a starting point for embedded designs (RFC 5.6). |
| Fusion Pixel Font | submodule `3rdparty/fusion-pixel-font` | Bitmap fonts with CJK coverage at 8, 10 and 12 pixels, suggested likewise (RFC 5.6). Fonts under OFL 1.1, build tools under MIT. |
| u8g2 | <https://github.com/olikraus/u8g2>, `tools/font/bdf/` | BDF sources of icon fonts (Open Iconic, Siji) and of Unifont, as test sets for `qua-icon-stats` (RFC 5.6). Read at commit `ab9e48b2`. Each font carries its own licence. |
| APRS Protocol Reference 1.0.1, 29 August 2000 | <http://www.aprs.org/doc/APRS101.PDF>; aprs.org blocks automated clients, so the copy consulted was fetched through <https://web.archive.org/web/2023id_/http://www.aprs.org/doc/APRS101.PDF> | The original that APRS12c compiles. Used to tell defects inherited from 1.0.1 from those introduced later (`legacy/`). |
| AX.25 Link Access Protocol v2.2, July 1998 | <https://www.ax25.net/AX25.2.2-Jul%2098-2.pdf> | Legacy framing: the address field layout behind the first-byte rule (RFC 5.1) and the optional encapsulation (RFC 7.2). |

The AX.25 document is linked rather than stored because it is copyrighted by
TAPR and ARRL. The copy consulted is 2,842,014 bytes, 135 pages, SHA-256
`5a4aac0bc10a69c5c983c35d5a84cc47ff204fa785a765fa1d2d6dd620131350`.

APRS 1.0.1 is linked for the same reason (copyright 2000 APRS Working
Group). The copy consulted is 3,173,392 bytes, 128 pages, SHA-256
`31df2904d982f83621ebb16ed379e4da3b5507db0dba7c9513e3815ff1ed62f8`.

Searchable Markdown copies of the APRS documents and the AX.25 PDF are made
locally with `qua-spec-extract`, into `work/refs/text/` by default. They are
never committed.
