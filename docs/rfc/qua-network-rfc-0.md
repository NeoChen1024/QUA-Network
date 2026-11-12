# QUA Network: Requirements and Design Direction

An open specification attempt at modernizing APRS.

| | |
|---|---|
| Document | RFC draft 0 (design notes, not yet a wire specification) |
| Date | 2026-11-11 |
| Status | Exploratory. Nothing here is frozen. Sections 5.8 and the icon of 5.6 have moved to `docs/spec/`; this document keeps their summary and rationale. |
| Name | "QUA Network" is a working name and may be replaced by a better one. Earlier drafts used "APRS-next". |
| Author | Kelei Chen <chenkolei@gmail.com> |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119. They describe the requirements this draft proposes for a future
specification; they do not describe an existing implementation.

Each design item carries one of three labels:

- **[agreed]** the direction was settled during the design discussion.
- **[proposed]** a concrete proposal that still needs review or measurement.
- **[open]** an unresolved question.

## 1. Summary

QUA Network is a redesign of the APRS application protocol. It keeps callsigns
as addresses and runs on existing KISS TNCs, but it does not depend on
AX.25, and it replaces the ad hoc text formats with one versioned binary PDU
that has a mandatory, lossless text form. The PDU is placed directly in the
frame of whatever link carries it, so the same packet can cross 1200 baud
AFSK, IL2P, LoRa, or an IP trunk without re-encoding.

The name comes from the Q code QUA, "Here is news of ..." followed by a
call sign, which is what a station's beacon is, whatever it carries:
position, a message, telemetry or weather. A name that listed functions
would leave most of them out, as "Packet Reporting System" did.

"QUA Network" is a working name. It replaced the earlier working name
"APRS-next", it is not fixed, and it may be replaced in turn if a better
one is found. It has also not been checked for trademark conflicts.
Anything derived from it, such as the `QUA1` marker in the text sketch of
5.4, is provisional in the same way, and no constant that goes on the wire
or into a hash input is to be built from the name until it is settled.

The four ideas that everything else depends on:

1. One self-contained PDU: a small fixed header plus TLV fields, with its own
   source, sequence number and integrity check.
2. A canonical text representation that maps one-to-one onto the binary form,
   enforced by round-trip test vectors.
3. One MTU everywhere: every conformant link carries the largest legal PDU,
   so gateways forward packets unmodified. Channel occupancy is bounded by an
   airtime budget, not by a second, smaller byte limit.
4. Feature semantics defined in the protocol, with a written specification
   that exists independently of any implementation.

## 2. Lessons from existing systems

### 2.1 APRS

APRS put the application layer directly on AX.25 UI frames in the early 1990s
and grew by accretion. The problems this draft responds to:

| Area | Problem |
|---|---|
| Encoding | Many unrelated text formats (uncompressed, compressed base-91, Mic-E, weather, telemetry, objects, items, messages). Parsers are dominated by special cases. |
| Versioning | No version field and no formal extension mechanism. Unknown content cannot be skipped safely. |
| Units and time | Feet, knots, several timestamp formats (DHM, HMS, local or zulu), position ambiguity expressed by blanking digits. |
| Stateful decoding | Telemetry needs separate PARM/UNIT/EQNS packets before a value can be interpreted. |
| Header abuse | Mic-E stores position in the destination address. WIDEn-N stores hop count in an SSID. |
| Routing | Flooding with no standard rate limiting; legacy aliases (RELAY, TRACE) still in circulation. |
| Medium access | No normative channel-access rules. Hidden-terminal collisions are common. |
| PHY | 1200 baud Bell 202 AFSK without FEC; a single bit error loses the frame. |
| Authentication | None on air. The APRS-IS passcode is a public function of the callsign. |
| Messaging | Acknowledgement and retry behaviour is underspecified and differs by client. |
| Internet side | q-constructs and gateway provenance were retrofitted. |
| Governance | The effective standard is spread across the 1.0 spec, addenda and drafts. Client behaviour such as SmartBeaconing is not specified. |

The state of the documentation is itself part of the problem. The APRS
Documentation Project (Appendix D) records that the 1.0.1 reference is
obsolete, that the corrections approved in 2004 were never merged into it,
that the later 1.2 material mixes widely implemented features with ideas
that went nowhere, and that no digipeater specification was ever produced.

The terms the reference was published under made this worse. The 1.0
reference, and the 1.2 compilation that reproduces its notice, state
"Copyright 2000 APRS Working Group, All rights reserved" and allow copying
"for non-commercial purposes only" (read in `APRS12c.pdf`, Appendix D).

- Copying was permitted and modification was not, so nobody outside the
  Working Group could publish a corrected edition. The later compilation
  has to describe itself as independent and unofficial.
- The rights belong to a group with no legal existence and no successor.
  Once it stopped meeting, nobody could change the terms.
- The non-commercial condition leaves open whether a manufacturer may
  reproduce the text in a manual or in firmware.
- The name is a registered trademark, and the same notice attributes it to
  two different parties.
- Other reference material, including the symbol list on aprs.org, carries
  no licence statement at all.

Two things APRS got right and QUA Network keeps:

- Features are defined at the packet level, so every client sees the same
  network. Clients differ in user interface, not in capability.
- KISS is a thin, public, stable host-to-radio interface. Any software works
  with any TNC, and it has survived more than thirty years.

A third property is social rather than technical: because APRS-IS is public
and sites such as aprs.fi display every packet, interoperability defects are
visible to everyone.

### 2.2 Meshtastic and MeshCore

These notes are the assessment reached in the design discussion and should be
re-verified before being cited publicly.

- Meshtastic is open source, but the protocol is defined by the reference
  firmware. Routing and rebroadcast behaviour are not specified outside the
  code, and protocol version changes have broken compatibility between
  firmware generations.
- MeshCore keeps the firmware thin and puts feature logic in companion apps.
  Several apps exist, some closed source, and their features do not
  interoperate.
- Both lack a written specification for the layer where behaviour lives:
  firmware in one case, the application in the other.
- Encryption by default keeps Meshtastic out of amateur bands and prevents
  passive monitoring by third parties. Neither system has a public gateway
  layer comparable to APRS-IS.

The conclusion: open source code is not an open protocol. A protocol is open
when a second, independent implementation can be written from the document.

## 3. Goals and non-goals

### 3.1 Goals

- G1. A single, versioned, extensible packet format.
- G2. A lossless text form that a person can read, type and `grep`.
- G3. Independence from the physical layer, including links slower than
  1200 baud AFSK.
- G4. A core position report that fits every conformant link without
  fragmentation.
- G5. Source authentication that works without a central registry and without
  encrypting content.
- G6. Inter-area trunks over arbitrary point-to-point links, RF or IP.
- G7. A specification with conformance test vectors, validated against a
  corpus of real APRS traffic.

### 3.2 Non-goals

- Confidentiality. Content stays in the clear, as amateur regulations require.
- A new modulation. QUA Network defines framing semantics and reuses existing
  PHYs.
- Replacing APRS-IS on day one. Coexistence and gatewaying are expected.

### 3.3 Device baseline

- **[agreed]** The smallest device the specification designs for is a current
  microcontroller of the Raspberry Pi Pico or ESP32-S3 class. Hardware limits
  of 1990s and 2000s TNCs and handhelds are not a design constraint.
- Consequences: UTF-8 text, hash functions and elliptic-curve operations are
  assumed to be available, and a device with a display is assumed to be able
  to hold a bitmap glyph set (see 5.6).

## 4. Architecture

```
+-------------------------------------------------------------+
| Application semantics (position, message, object, ...)      |  defined in spec
+-------------------------------------------------------------+
| QUA Network PDU: header + TLVs  <->  canonical text         |  link-independent
+-------------------------------------------------------------+
| Link framing: HDLC (KISS TNC) | IL2P | LoRa frame | UDP/TCP |
+-------------------------------------------------------------+
| PHY: AFSK 1200 | FSK 9600+ | LoRa | 802.11 | ...            |
+-------------------------------------------------------------+
```

- **[agreed]** The PDU is the unit of exchange. Deduplication, signatures and
  integrity checks are computed on the PDU and never on the link envelope.
- **[agreed]** The PDU goes directly into the link's frame. A link supplies
  framing and error detection. Addressing, identification, routing state
  and everything else are in the PDU.
- **[agreed]** AX.25 is not a layer of QUA Network. It exists only as an
  optional compatibility encapsulation on HDLC links (7.2).
- **[agreed]** KISS remains the host interface to a TNC. It does not depend
  on AX.25.
- **[agreed]** Other PHYs are allowed, so that operators can build
  point-to-point high-speed inter-area trunks.

An earlier revision kept AX.25 as the access-network link layer. It was
dropped because nothing it supplied was still needed: the PDU has its own
identifier, which an AX.25 address cannot hold (5.8); routing state is in
the PDU, not the via field; and identification is satisfied by the source
in the PDU under a published encoding. What remained was 16 bytes per frame
(destination 7, source 7, control 1, PID 1), with the source duplicated and
the destination unused. In existing traffic the AX.25 header is a
substantial share of the mean frame (section 13).

## 5. PDU format

### 5.1 Header

- **[agreed]** The header is minimal. No application data may be placed in
  link-layer address fields.
- **[proposed]** Header contents: protocol version, flags, source callsign and
  SSID (encoded as in 5.8), a per-source sequence number, hop limit, and
  payload length. Everything else is a TLV.
- **[proposed]** The header never changes in transit. It carries the hop
  limit chosen by the source, not a count that relays decrement; the number
  of hops used is read from the hop trace (5.9). The payload length counts
  up to and including the integrity check and excludes the hop trace.
- **[agreed]** The PDU carries its own frame checksum, CRC-32C (Castagnoli),
  independent of any link-level check.
  - Parameters: polynomial `0x1EDC6F41` (reflected `0x82F63B78`), initial
    value `0xFFFFFFFF`, input and output reflected, final XOR `0xFFFFFFFF`.
    The check value for the ASCII string `123456789` is `0xE3069283`.
  - It covers what the source wrote, the header and all TLVs, and not the
    hop trace (5.9).
  - A CRC is kept, in preference to a truncated hash, because it detects
    every error burst of 32 bits or less with certainty and every small
    number of scattered bit errors at these frame lengths. A truncated hash
    gives only a probability. CRC-32C is chosen over the older IEEE 802.3
    CRC-32 for its better error-detection properties at short lengths; the
    exact Hamming distance figures are to be confirmed against Koopman's
    tables.
- **[proposed]** The checksum is always present, including in authenticated
  PDUs. A TESLA MAC cannot be verified until its key is disclosed later
  (10.4), so relays and receivers need a check they can evaluate at once.
- **[open]** The byte order of the checksum on the wire, to be fixed with the
  header layout.
- **[proposed]** The least significant bit of the first byte of a PDU is 1.
  In AX.25 the first byte of a frame is an address byte whose low bit, the
  extension bit, is always 0. An AX.25 parser therefore sees an address
  field of length 1, which is not a multiple of 7, and rejects the frame,
  and a QUA Network receiver can tell the two kinds of frame apart from that
  one bit. Both can share a channel and a single HDLC decoder (7.1).

### 5.2 TLV container

- **[agreed]** Fields are encoded as lightweight TLVs.
- **[agreed]** A receiver MUST be able to skip a TLV it does not understand
  and MUST preserve it when relaying or logging.
- **[agreed]** TLV order is canonical. Two encodings of the same content
  MUST NOT both be valid.
- **[open]** Custom TLV or a strict subset of CBOR with deterministic encoding
  (RFC 8949 section 4.2). A custom format saves bytes and excludes unwanted
  features (indefinite lengths, floats, tags). A CBOR subset gets existing
  parsers. The preference so far is a custom format designed so that it is
  also a valid CBOR subset.

### 5.3 Numeric and text rules

- **[agreed]** No floating point on the wire. All quantities are integers with
  a fixed scale, for example latitude and longitude as int32 in units of
  1e-7 degree, altitude as a signed integer in centimetres.
- **[agreed]** SI units and WGS84 only.
- **[agreed]** Time is an integer count from a fixed epoch in UTC.
- **[proposed]** Precision or uncertainty is an explicit field. Blanked digits
  are not used.
- **[agreed]** Strings are UTF-8.
- **[agreed]** Telemetry is self-describing or refers to a registered schema.
  A value MUST NOT depend on a separate definition packet having been heard.

### 5.4 Canonical text representation

- **[agreed]** Every PDU has exactly one text representation, and every valid
  text representation has exactly one PDU. The mapping is lossless in both
  directions.
- **[agreed]** The text form is one line of printable ASCII, with fixed
  whitespace rules and a single escaping rule for strings. It should be
  possible to type a packet by hand on a keyboard-only terminal.
- **[agreed]** Unknown TLVs appear in text as a generic tag-plus-hex field, so
  that software which does not implement an extension still round-trips it.
- **[agreed]** The text form carries a version marker that corresponds to the
  binary version field.
- **[proposed]** Fixed-scale integers are printed either as the raw integer or
  as a decimal with a fixed number of fraction digits, never both.

A non-normative sketch of what a position report might look like:

```
QUA1 N0CALL-9 seq=1042 hop=2 pos=24.2500000,120.6700000 alt=152.00 sym=/> cmt="mobile"
```

### 5.5 Conformance

- **[agreed]** The specification ships round-trip test vectors. An
  implementation conforms only if binary to text to binary is bit-identical
  for every vector, including vectors with unknown TLVs.
- **[agreed]** Signatures are computed over the binary form. Because the
  mapping is bijective, a text log is sufficient to re-verify them.

### 5.6 Symbols

A station's symbol is one field with two forms. A PDU carries one of them.

- **[agreed]** **Classic form.** An APRS symbol, as one unsigned 16-bit
  number. APRS has 94 symbol codes (ASCII 33 to 126) in each of two tables,
  and a symbol of the alternate table can carry one overlay character, `0`
  to `9` or `A` to `Z`. That is 94 + 94 * 37 = 3,572 symbols:

  | Symbol | Number |
  |---|---|
  | Primary table (`/`), code `c` | `c - 33`, from 0 to 93 |
  | Alternate table (`\`), code `c`, overlay digit `d` | `94 + (c - 33) * 37 + d`, from 94 to 3,571 |

  The overlay digit `d` uses the digit table of 5.8: 0 for no overlay, 1 to
  10 for `0` to `9`, 11 to 36 for `A` to `Z`. Numbers from 3,572 upward are
  invalid. Every valid number is a different symbol, and conversion in both
  directions is arithmetic, with no mapping table.
- **[agreed]** Every valid legacy symbol crosses a gateway in both
  directions without loss. A legacy symbol that is not valid (a table
  character other than `/`, `\`, `0` to `9` or `A` to `Z`, or a code outside
  ASCII 33 to 126) has no classic form.
- **[proposed]** A gateway translating a legacy packet whose symbol is not
  valid sends the PDU without a symbol, and the receiver draws its default.
  In existing traffic such packets are rare, and most of them are damaged
  or are not position reports at all (section 13).
- **[agreed]** A gateway converts the lower-case table characters `a` to
  `j` to the overlay digits `0` to `9`. APRS defines them for the compressed
  position format only, but some senders use them in the uncompressed
  format as well, and the conversion is applied in every format. No valid
  table character is lower case, so nothing else is affected.
- **[proposed]** In canonical text the classic form is written as the two
  APRS characters, table or overlay first: `/>`, `\k`, `L#`.
- **[agreed]** **Unicode form.** A short UTF-8 string: a single symbol or
  emoji, an emoji sequence made of a few code points, or ordinary text such
  as a two-letter label. Receivers render it as text.
- **[agreed]** The Unicode form has a length limit expressed in bytes, because
  bytes are what airtime depends on and the check is trivial. **[proposed]**
  The limit is 8 bytes. That holds a single emoji, an emoji with a variation
  selector or a skin-tone modifier, a keycap, a two-letter regional flag, or
  a short text label. Longer sequences (multi-person ZWJ sequences,
  subdivision flags) do not fit; the icon below covers what they were for.
- **[proposed]** The string MUST be valid UTF-8 and MUST NOT contain control
  characters. Beyond that it is opaque to the protocol: no normalisation is
  required and no sequence is interpreted. Two different strings are two
  different symbols, even if some renderer draws them alike. Senders SHOULD
  use fully-qualified emoji sequences as published by Unicode.
- **[agreed]** The symbol is display only, in both forms. Software MUST NOT
  derive behaviour from it. What a station is and what a packet contains are
  stated by the fields present (a weather TLV, a digipeater capability), not
  by the picture. This removes the APRS coupling in which a symbol such as
  `_` also announces the payload format.
- **[proposed]** A receiver that cannot draw a Unicode symbol draws the parts
  it can, or a generic placeholder. New Unicode versions therefore need no
  protocol change.
- In canonical text the Unicode form uses the ordinary string escaping rule
  of 5.4, so the text representation stays printable ASCII.
- **[agreed]** Fonts are outside the scope of this specification. A device
  MAY use any font. As a convenience for embedded designs, which need a
  bitmap font that includes CJK characters, two starting points are GNU
  Unifont at 16 pixels and Fusion Pixel Font at 8, 10 and 12 pixels.

#### Icon

The icon is specified in [`docs/spec/02-icon.md`](../spec/02-icon.md). This
section keeps the summary and the reasons.

A station can also send a small picture of its own: a 16 by 16 one-bit
bitmap with a foreground and a background colour of one byte each, in an
optional TLV beside the symbol. The bitmap is sent plain, or as run lengths
when that is shorter. It does not replace the symbol. The icon is
bound to the symbol it is sent with, a receiver holds at most one icon per
station, and a station withdraws its icon by sending a different symbol
without one.

Why it is built this way:

- An icon needs no font on the receiver and looks the same everywhere. In
  exchange it has no meaning a program can search or filter on, it cannot
  be redrawn at a higher resolution, and in canonical text it is the one
  part of a station's appearance that is not practical to type by hand.
  That is why the symbol stays beside it.
- Binding the icon to the symbol gives a way to withdraw it without a
  separate message, and keeps a meaningful fallback for receivers that do
  not support icons or have not yet received one. An earlier version made
  the symbol field a bare placeholder while an icon was in use; it was
  dropped because such receivers would then have nothing to show.
- One icon per station, replaced by the next, keeps a receiver's memory
  bounded by the number of stations it tracks.
- The colours use the part of the xterm 256-colour palette that has fixed
  values. The first sixteen entries are a terminal's system colours and
  differ between terminals, so they cannot name a colour; the value 0 is
  reused for "device default" and "transparent" and the other fifteen are
  invalid. A device needs no table beyond the six cube levels.
- The icon is not sent in every beacon, for the same reason as unchanged
  comment text (5.7). Every packet remains fully decodable without it.
- Arbitrary pictures will appear on public maps, which is why a gateway or
  display service is allowed to decline to show them.

**[agreed]** The bitmap has two forms and no more: plain, at 32 bytes, or
each row XORed with the one above and the resulting bit stream coded as
alternating run lengths in Elias gamma. The rules of 5.7 apply: the
run-length form if and only if it is strictly shorter, one exactly specified
encoder, test vectors, and a decoder that rejects a non-canonical encoding.
The details of the bit stream are in the specification file.

`qua-icon-stats` measures the forms on the glyphs of bitmap fonts, each
centred in the 16 by 16 cell. The fonts are the BDF sources kept in the
u8g2 repository (commit `ab9e48b2`, 2026-06-27; run on 2026-11-12). Open
Iconic at 16 pixels is the closest to what a station would draw. Sizes are
mean bytes; "used" is the share of glyphs for which the run-length form is
shorter than 32 bytes.

| Test set | Glyphs | Run-length form | Used |
|---|---|---|---|
| Open Iconic, 16 by 16 (`open_iconic_all_2x`) | 223 | 19.6 | 97.3% |
| Siji, 12 by 12 (`siji`) | 624 | 13.2 | 100% |
| Unifont symbols and dingbats, U+2600 to U+27BF | 448 | 20.1 | 96.9% |
| Unifont emoji blocks, U+1F300 to U+1F64F, U+1F680 to U+1F6FF, U+1F900 to U+1FAFF | 1,316 | 22.7 | 98.6% |
| of which emoticons, U+1F600 to U+1F64F | 80 | 28.3 | 97.5% |
| Unifont CJK ideographs, U+4E00 to U+9FFF | 20,991 | 28.7 | 73.6% |

Drawn icons come to a little under two thirds of the plain size, small ones
to under half, and glyphs that fill the cell, such as faces and ideographs,
hardly compress. Without the row XOR the Open Iconic set comes to 23.8
bytes.

Dropped alternatives:

- Leaving out the last run, which a decoder can infer because the bitmap
  always has 256 pixels. It measured about one byte shorter on every test
  set. Dropped as too particular a rule for that gain: the decoder would
  end on "all remaining bits are zero" in place of a pixel count.
- Cropping to the bounding box and sending the pixels inside it. A
  hand-drawn icon is expected to fill nearly the whole 16 by 16 cell, so
  there is little to crop. In the first one-off measurement, on font
  glyphs, it came out about the same as the run-length form.
- An adaptive arithmetic coder with a causal pixel context. Its ideal code
  length in the first one-off measurement was two or three bytes below the
  run-length form, which a real coder approaches but does not reach. A
  picture of 256 pixels is too short for the model to adapt, and a fixed
  probability table would write one font's statistics into the format.
- Deflate, which was longer than the plain bitmap on a third or more of the
  symbols and emoji in the same measurement.

The first one-off measurement used the 16 by 16 glyphs of GNU Unifont
18.0.01 and a script that was not kept; its figures are not reproducible
and are quoted here only for the dropped alternatives.

**[agreed]** 16 by 16 pixels at one bit each is the only size of the icon.
A larger icon or one with more colours is not ruled out for a later
version, as a separate TLV; none is designed here.

A bitmap with more than two colours was considered and dropped for this
icon. A one-off
test reduced the roughly 1,200 glyphs of Noto Color Emoji to 16 by 16 and
coded them with run lengths: three colours plus transparency came to about
50 bytes with its palette, seven colours to about 80, and fifteen to well
over 100, with the cheaper variants visibly degraded. A station that wants
a colour picture already has one in the Unicode symbol form at 4 to 8
bytes, drawn by the receiver's own font. The icon is for devices without
such a font and for pictures Unicode does not have, and for those a shape
and two colours cost two bytes more than the shape alone.

### 5.7 Text compression

- **[agreed]** Only free-text string fields are compressed (comment, status,
  message body). Tags, lengths and binary values are sent as they are. The
  TLV structure is always readable without decompressing anything.
- **[agreed]** The method is Unishox2, a codec designed for short Unicode
  strings.
- **[agreed]** The sender compresses each string as a trial. If the result is
  not strictly shorter than the UTF-8 original, the string is sent unchanged
  (passthrough). Unishox2 can expand some inputs, so this rule is required.
- **[proposed]** Each text field carries a marker saying which form it holds:
  passthrough or compressed. If per-string preset selection is adopted (see
  "Choice of preset" below), the marker becomes a preset number, with 0 for
  passthrough.
- **[proposed]** Because the rule is "compressed if and only if strictly
  shorter", the form is determined by the content, and the binary-to-text
  round trip of 5.4 holds. A decoder MUST reject a field that is marked
  compressed but is not what the canonical encoder produces for that string.
  Recompressing and comparing is cheap at these lengths.
- **[proposed]** The specification pins the allowed Unishox2 preset or
  presets and one exact encoder behaviour for each, and ships test vectors
  taken from real corpus strings. Two independent implementations must
  produce identical bytes.
- The canonical text form shows the decompressed string. Compression is not
  visible in text.
- The short Unicode symbol of 5.6 is not compressed; at 8 bytes or less
  there is nothing to gain.

#### What Unishox2 contains

Unishox2 has no static dictionary, which is why it satisfies the
no-dictionary rule. Its README states that static dictionaries arrive in
Unishox3, and that Unishox2 remains supported for cases where there is no
room to store them. **[agreed]** QUA Network uses Unishox2 and does not follow
it to Unishox3.

The word "dictionary" in Unishox2's own description means something else:

| Mechanism | What it is |
|---|---|
| Entropy coding | A fixed prefix-free code for each character. |
| "Dictionary coding" | A back-reference to a run that already occurred earlier in the same string. There is no external dictionary. |
| Delta coding | Unicode characters coded as differences between code points. |

What it does embed is small, and is selected by a preset:

- The prefix-code table, which decides which classes of character get the
  shorter codes.
- Six frequently occurring sequences. In the default preset these are
  markup punctuation: `": "`, `": `, `</`, `="`, `":"` and `://`. The text
  presets use English fragments instead: ` the `, ` and `, `tion`, ` with`,
  `ing`, `ment`. There are also URL and JSON variants.
- A few templates for date, time and telephone-number formats.

This is a light prior, of a different order from a vocabulary that goes out
of date.

#### Choice of preset

**[open]** Not decided. The reference implementation defines 17 presets
(`USX_PSET_DFLT`, `USX_PSET_ALPHA_ONLY`, `USX_PSET_FAVOR_ALPHA`,
`USX_PSET_NO_DICT`, `USX_PSET_URL` and others). Three ways to use them:

| Approach | Who decides | Extra bits | Canonical |
|---|---|---|---|
| One preset for everything | The specification | none | by construction |
| A. Preset fixed per field type | The specification | none | by construction |
| B. Preset chosen per string | The content, by rule | a small preset number per string | needs the rule below |

**B is the leading candidate. It is not fixed.** A comment field holds URLs,
English sentences, Chinese, frequencies and more, so a preset fixed by
field type is barely a choice. Selecting per string also removes the
language-bias concern: a preset with English fragments is used only on
strings where it actually wins.

If B is adopted, these rules keep the encoding canonical (**[proposed]**):

- Compress the string with every allowed preset and take the shortest
  result.
- On a tie, take the lowest preset number.
- If no result is strictly shorter than the UTF-8 original, send
  passthrough.
- The marker of each text field is the preset number, 0 meaning
  passthrough.
- A decoder reruns the same rule on the decoded string and rejects the
  field if the sender's choice is not the canonical one.

Costs of B:

- The allowed set has to be small, three or four presets, so that the
  marker is 2 bits. Each extra preset is one more compression pass on both
  sides and one more set of conformance vectors.
- Every allowed preset needs an encoder that two implementations reproduce
  byte for byte. A preset with back-references keeps the determinism
  question open (see `USX_PSET_NO_DICT` below).

Other considerations, whichever approach is taken:

- The default preset's sequences are punctuation and are neutral between
  languages. A text preset builds in English fragments, which do nothing
  for Chinese or Japanese comments.
- `USX_PSET_NO_DICT` is described in the source as the preset for input
  with no repeating sequences. It appears to disable back-references. If
  so, it removes the one part of the encoder where a matching strategy has
  to be chosen, which would make byte-identical output across
  implementations much easier to guarantee. Repeats inside a comment of a
  few dozen bytes are rare, so the loss should be small. Both points are to
  be confirmed by reading the encoder and by measurement.
- Unishox2 also accepts custom presets. A preset built from APRS traffic
  would be a small dictionary that ages, which the no-dictionary rule
  excludes.

The decision waits for the corpus measurement (section 15): the total
length with the best preset per string, against the total with the single
best preset overall. A difference of a percent or two does not justify the
extra rules.

#### Risk to manage

Unishox2's behaviour is in practice defined by its reference
implementation. Adopting it by reference would repeat pitfall 11. The
specification therefore has to state the encoder precisely, or cite the
published Unishox2 description and back it with test vectors. Whether the
reference encoder is fully deterministic across platforms is to be checked.

An earlier revision considered compressing the whole body, TLV structure
included. It was dropped: binary values barely compress, structural
redundancy is better removed by a dense TLV encoding, and it needed a
mandatory method identifier in the header and a decompression step at every
filtering gateway, for little expected gain.

Related, and possibly a larger saving: a station need not send the same
comment in every beacon. The specification can recommend that unchanged text
is sent every Nth beacon. Each packet stays self-contained; a receiver that
remembers the last comment does so for display only.

### 5.8 Callsign encoding

The encoding is specified in
[`docs/spec/01-station-identifier.md`](../spec/01-station-identifier.md).
This section keeps the summary and the reasons.

A station identifier, callsign and SSID together, is a fixed 64-bit value.
It is used wherever a station is named: the source in the header, a message
addressee, a path entry. The low 63 bits hold 12 base-37 digits. The SSID
is the last digit or the last two, the top bit says which, and the callsign
takes the remaining 11 or 10 digits. One digit table serves both parts: 0
is padding, `/` or "no SSID" depending on position, 1 to 10 are `0` to `9`,
and 11 to 36 are `A` to `Z`.

Why it is built this way:

- Digit 0 does double duty in the callsign. A callsign never begins with
  `/`, so leading zeros are padding and every other zero is a `/`. The
  callsign needs no separate padding symbol, its value is the callsign read
  as an ordinary base-37 number, and every digit pattern decodes to a
  different string. Nothing has to be rejected there except the empty
  callsign.
- With a one-digit SSID the callsign has 11 digits, the same length as the
  FT8 non-standard callsign. Every real callsign FT8 can express is
  representable, with no SSID or a one-character SSID. Only an 11-character
  callsign with a two-character SSID cannot be expressed.
- **[agreed]** FT8 is a reference for this design, not a compatibility
  target. The alphabet is FT8's without the space. FT8 packs the callsign
  in base 38 with a space for padding (`pack77_4` in WSJT-X
  `lib/77bit/packjt77.f90`); values here are not numerically equal to
  FT8's, and need not be.
- The format covers every identifier that is legal on APRS-IS, where the
  SSID may be one or two alphanumeric characters and the total is at most
  nine characters. SSIDs outside the AX.25 range are in real use there
  (section 13).
- The one-character SSID `0` is excluded because AX.25 cannot distinguish
  SSID 0 from no SSID, and APRS-IS forbids writing `-0`.
- An identifier that does not fit an AX.25 address matters only for
  gateways to legacy APRS and for the optional AX.25 encapsulation (7.2).
  APRS itself has the same limit: such stations exist only on APRS-IS and
  reach RF, if at all, as text inside third-party packets.

Two earlier layouts were dropped: a separate 6-bit SSID field, which could
not hold two-character SSIDs, and base-38 packing with a space as padding
or separator, which needed several rejection rules to be canonical.

### 5.9 Hop trace

Each station that relays a PDU records itself in a trace at the end of the
frame.

```
| header | TLVs | integrity check / auth tag | hop trace |
  written by the source, never changed         appended by relays
```

- **[agreed]** The hop trace is a TLV at the very end of the frame. A relay
  appends one entry to it. Nothing is reserved in advance, so a PDU that is
  never relayed carries no trace at all.
- **[agreed]** An entry is a 24-bit hash of the relay's identifier: the first
  3 bytes of BLAKE3 over the 8-byte identifier of 5.8 in big-endian order.
- **[agreed]** A hash is sufficient identification because every relay also
  transmits its full identifier periodically in its own beacons. FT8 works
  the same way: a non-standard callsign is sent in full in some messages
  and referred to by a 10, 12 or 22-bit hash in others.
- A receiver resolves an entry against the stations it has heard. An entry
  it cannot resolve is shown as the hash. Gateways and network-wide
  services can resolve all of them.
- With about 100 relays in range, the chance that any two share a 24-bit
  hash is about 0.03%.

Rules that make appending work, all **[proposed]**:

- The trace comes after the integrity check and authentication tag. What
  the source wrote ends there, and everything after it is trace. A relay
  recomputes nothing, and a receiver needs no list of fields to skip when
  verifying.
- Hops used is the number of entries. Remaining hops is the header's hop
  limit minus that number. A relay does not forward a PDU whose trace is
  full.
- A source leaves room for its own hop limit: the size of the PDU as sent,
  plus the trace for that many hops, MUST NOT exceed the MTU of 6.1. At 3
  bytes per hop plus 2 for the TLV tag and length, a limit of 7 hops
  reserves 23 bytes. Any relay on the path can then always append.
- A relay that finds its own hash in the trace does not forward the PDU.
  This is a second guard against loops, after deduplication.

Properties to keep in mind:

- The trace is outside authentication. Anyone can forge or delete entries,
  so it is diagnostic information and never a basis for trust. Deleting
  entries lets a PDU travel further than its source intended; deduplication
  on `(source, sequence number)` limits the effect.
- The trace is protected hop by hop by the link's own error detection.
- In canonical text the trace is written as the hash values, not as
  resolved callsigns. Resolution belongs to the display. The same PDU
  therefore has a different text form after each hop, differing only in
  the trace.

Test vectors:

| Identifier | 8 bytes, big-endian | Hop hash |
|---|---|---|
| `N0CALL` | `0000000E5BEBEB3D` | `A8E2C0` |
| `N0CALL-7` | `0000000E5BEBEB45` | `FF0D58` |
| `N0CALL-15` | `8000021349190021` | `4F68FE` |
| `BV5AB-33` | `80000007B01E3AF5` | `A40801` |
| `PJ4/KA1ABC` | `01C577F1F48964A5` | `902929` |
| `YW18FIFA/MM-A` | `589FF5E2D11F7466` | `6FF4AF` |

Computed with the `blake3` Python package (1.0.11).

## 6. Size budget

### 6.1 One MTU

- **[agreed]** There is a single size limit. Every conformant link MUST carry
  a PDU of the maximum legal size. The guaranteed MTU and the hard cap are
  the same number.
- **[agreed]** That number is set by the 255-byte packet limit shared by
  common sub-GHz transceivers, including LoRa (Appendix A).
- **[proposed]** The link envelope on such a radio comes out of the same 255
  bytes, so the PDU limit is somewhat lower. The exact value (for example
  240 bytes, leaving 15 for the envelope) is fixed when the LoRa and FSK
  bindings are drafted.
- Existing traffic supports this: all but a very small share of RF-origin
  APRS payloads are 255 bytes or shorter (section 13), so the limit matches
  what 1200 baud networks carry today.

An earlier revision of this draft had a 128-byte guaranteed MTU below a
255-byte hard cap, with gateways removing optional TLVs to fit smaller links.
That design was dropped. It required a droppable class on every TLV, a
`truncated` flag, split authentication coverage, and a rule for content that
could not be shortened, and the hardware survey gave no reason for a lower
floor. With one MTU, a gateway forwards a PDU unmodified or does not forward
it.

### 6.2 Gateways do not modify packets

- **[agreed]** A gateway MUST NOT remove TLVs, shorten values, or otherwise
  alter a PDU. The only thing a relay does to a frame is append to the hop
  trace (5.9).
- **[agreed]** Access links never fragment. On a half-duplex broadcast channel
  one lost fragment loses the packet, there is no retransmission, and every
  receiver must hold reassembly state.
- **[agreed]** The deduplication key is `(source, sequence number)`, not a
  hash of the frame bytes, because the hop trace grows in transit.
- **[proposed]** Link-level fragmentation MAY exist on point-to-point trunks
  that have ARQ. Access-network receivers never see it.

### 6.3 Airtime

A byte limit does not bound channel occupancy. A maximum-size PDU takes about
1.7 s at 1200 baud before preamble, and 8 to 9 s at LoRa SF12 (Appendix B).

- **[proposed]** Each station has an airtime budget per link, expressed as a
  fraction of time over a window. Beacon-rate rules (section 9) are derived
  from it. Senders, not gateways, are responsible for staying inside it.
- **[proposed]** The specification gives recommended sizes per packet class,
  so that routine beacons stay small even though the MTU allows more. The
  values come from the re-encoded corpus (section 15).

### 6.4 Recommended bitrate

The specification does not divide links into conformant and non-conformant
by speed. It recommends a bitrate and lets the airtime budget do the rest.

- **[agreed]** Every link that carries QUA Network carries the full MTU. A slow
  link is still a conformant link.
- **[proposed]** Access links SHOULD run at a recommended minimum bitrate. For
  LoRa the reference point is a setting of about 3.5 kbit/s, comparable to
  the Meshtastic "Medium Fast" preset (SF9 at 250 kHz). SF8 at 125 kHz gives
  about 3.1 kbit/s in half the bandwidth and may suit band plans built around
  125 kHz channels. At these rates a maximum-size PDU takes roughly 0.6 to
  0.7 s, less than the same PDU at 1200 baud AFSK.
- **[proposed]** Slower settings are permitted. A station or gateway
  transmitting on a slow link is bound by the same airtime budget (6.3), so
  it sends fewer packets. What a gateway does not have budget to forward, it
  does not forward. This is ordinary rate limiting, and it never involves
  altering a packet.
- A radio whose frame is smaller than the MTU (802.15.4 at 127 bytes, for
  example) cannot carry a full PDU at any bitrate. **[proposed]** Its binding
  MAY use link-level fragmentation on that link only, in the manner of
  6LoWPAN, invisible to the rest of the network. Otherwise the radio is out
  of scope.

### 6.5 Long content

- **[agreed]** Content that does not fit in one PDU is segmented by the sender
  at the application layer. Each segment is an independent valid PDU with its
  own sequence number, carrying a message identifier, a segment index and the
  segment total. Segments are acknowledged and retransmitted individually,
  and a receiver can display the segments it has.
- **[agreed]** Segment boundaries fall on UTF-8 code point boundaries, so
  every segment is valid text on its own.
- **[agreed]** Gateways do not segment on behalf of a source. A gateway cannot
  issue sequence numbers for another station and cannot re-authenticate the
  result.
- With the single MTU, a rough estimate leaves somewhat over 200 bytes of
  message text per PDU, against 67 characters in APRS today. A visible
  share of existing messages sits exactly at that limit (section 13), and
  most messages will fit in one PDU. The exact figure depends on the final header.

## 7. Link bindings

| Link | Native binding | AX.25 encapsulation |
|---|---|---|
| HDLC links, such as a KISS TNC | PDU directly in the HDLC frame | Optional, for compatibility with existing AX.25 facilities |
| LoRa and other PHYs | PDU directly in that PHY's frame | Not defined |

### 7.1 Native binding on HDLC links

- **[agreed]** On a KISS TNC the PDU is the content of the HDLC frame. The TNC
  supplies flags, bit stuffing and the 16-bit FCS. There is no address,
  control or PID field.
- **[proposed]** Coexistence with legacy APRS on the same channel relies on
  the first-byte rule of 5.1. A receiver takes each HDLC frame with a good
  FCS and looks at the low bit of the first byte: 1 is QUA Network, 0 is
  AX.25.
- FX.25 wraps a whole HDLC frame and does not look inside, so it applies
  unchanged.
- Whether deployed TNCs pass frames that are not AX.25 has to be tested per
  device. A reading of the Dire Wolf source (GitHub master) suggests it
  does: a frame arriving over KISS is checked only for length, with a
  minimum of 15 bytes; a received frame with a good FCS is passed on
  without address validation unless bit-fixing is enabled; and its address
  counting looks for the first byte with the low bit set and requires that
  position to be a multiple of 7, which is the behaviour the first-byte
  rule depends on. This was read, not run. Dire Wolf's display, digipeater
  and IGate functions assume AX.25 content and may misbehave.
- Consequence: a PDU on an HDLC link is at least 15 bytes. Any realistic PDU
  is longer.

### 7.2 Optional AX.25 encapsulation

- **[agreed]** An AX.25 UI encapsulation is defined as an optional
  compatibility binding, on HDLC links only. It is for paths that must pass
  through unmodified AX.25 facilities. It is not defined for LoRa or any
  other PHY.
- What it is for:
  - Existing digipeaters, which repeat UI frames without software changes.
    They do not append to the hop trace or deduplicate on the PDU, so
    traffic repeated this way bypasses QUA Network routing rules.
  - Satellite and ISS digipeaters, which repeat only AX.25 UI frames.
- **[proposed]** The PDU travels in a UI frame with a dedicated PID value (to
  be selected; it must not collide with assigned values). Legacy TNCs pass
  an unknown PID to the host unchanged.
- **[agreed]** The via field is not used for QUA Network routing state. It is
  set only as the legacy facility being traversed requires.
- **[open]** What the AX.25 source and destination addresses hold, in
  particular for a station whose identifier does not fit an AX.25 address
  (5.8).

### 7.3 Other links

- **[agreed]** LoRa carries the PDU directly in the LoRa frame. There is no
  AX.25 and no TNC-2 text header. **[proposed]** The recommended setting is
  about 3.5 kbit/s (6.4). Slower settings are allowed and are limited by the
  airtime budget.
- **[proposed]** IL2P replaces HDLC framing and adds Reed-Solomon FEC. It is
  the reference medium-speed link. IL2P is built around the AX.25 header;
  whether its transparent mode carries a native PDU is to be confirmed
  against the IL2P specification. If not, IL2P links use 7.2.
- **[proposed]** IP trunks carry PDUs over UDP, or batched over a stream.

### 7.4 Host interface

- **[agreed]** The radio-to-host interface has a formal specification of its
  own and is kept deliberately thin, in the spirit of KISS. It MUST NOT be a
  private API of one application.
- For TNCs, that interface is KISS itself.

### 7.5 What the native binding gives up

- Legacy stations cannot decode QUA Network frames at all. On a shared channel
  this is a matter of community acceptance as much as engineering.
- An AX.25 via field records the full callsign of each station that repeated
  a frame. QUA Network records a 24-bit hash per hop instead (5.9), and
  relies on each relay's own beacons for its full identifier.

## 8. Routing

### 8.1 Access network

- **[agreed]** Flooding within an area is bounded by the hop limit in the
  header, counted against the hop trace (5.9), and suppressed by
  `(source, sequence number)` deduplication.
- **[proposed]** Digipeaters apply rate limiting and per-source fairness.

### 8.2 Inter-area trunks

- **[agreed]** The access network is a flooding domain. Trunks are routed. A
  trunk MUST NOT simply extend the flood.
- **[proposed]** The first gateway stamps an origin area identifier.
- **[proposed]** Trunk peers subscribe with filters (bounding box, packet
  class, addressee), modelled on APRS-IS server filters.
- **[proposed]** Message routing follows last-heard area: gateways remember
  where each callsign was last heard and forward messages there, with a
  bounded fallback when the location is unknown.
- **[proposed]** Trunks batch several PDUs per link frame.
- **[open, deferred]** A packed format for high-speed links, in which a trunk
  carries many PDUs in a denser combined encoding. This is a later concern
  and is deliberately left undesigned. Whatever is chosen MUST unpack to the
  original PDUs bit for bit, so that sequence numbers and authentication are
  unaffected.

### 8.3 Internet gateways

- **[agreed]** Gateway provenance (who received the packet, on which port,
  through which gateways) is a first-class field, designed in from the start.

## 9. Medium access

- **[agreed]** The specification defines channel-access rules. They are not
  left to implementers.
- **[proposed]** Baseline: CSMA with specified persistence and randomised
  backoff. Beacon-rate adaptation, in the manner of SmartBeaconing, is
  specified normatively.
- **[open]** Time-slotted access using GPS time, modelled on AIS SOTDMA.
  Stations already have GPS time, so slotting is cheap and gives fairness.
  How this coexists with legacy APRS stations on a shared channel is unsolved.

## 10. Authentication

### 10.1 Threat model

- Content is public. There is no confidentiality requirement and therefore no
  harvest-now-decrypt-later exposure.
- The goal is to detect impersonation of an established station. Preventing
  every first-contact impersonation is explicitly out of scope, and the
  specification MUST say so.
- Forgery attempts cost airtime. At 1200 baud an attacker can send fewer than
  about 100,000 packets a day, which is what makes short authentication tags
  acceptable.

### 10.2 Why not sign every packet

An Ed25519 signature is 64 bytes: longer than the median APRS payload today
(section 13), about 0.43 s at 1200 baud, and more than 2 s at
LoRa SF12. A signify-style signature adds a
2-byte algorithm identifier and an 8-byte key number, for 74 bytes. Signing
every packet is not acceptable.

### 10.3 Hash function

- **[agreed]** BLAKE3 is the only hash function in the specification. The
  frame checksum of 5.1 is CRC-32C; it is an error-detecting code, not a
  hash, and is the one exception to "BLAKE3 everywhere". It is
  used for hop trace entries (5.9), for the TESLA hash chain, for message
  authentication codes through its keyed mode, and wherever else a hash is
  needed, including the Schnorr challenge and the hash of an off-air key.
- One primitive keeps microcontroller implementations small. BLAKE3's keyed
  mode is a MAC by construction, so no HMAC wrapper is needed.
- **[proposed]** Each use has its own domain separation, so that a value
  computed for one purpose can never be valid for another. BLAKE3's
  key-derivation mode with a fixed context string per use is the intended
  mechanism. Hop trace entries are the plain hash, as specified in 5.9.
- The cryptographic uses remain subject to the review called for below.

### 10.4 Proposed scheme

All of section 10.4 is **[proposed]** and needs review by a cryptographer
before any of it is treated as sound.

- **Replay protection.** The per-source sequence number is mandatory core
  content.
- **Per-packet authentication: TESLA.** Each station maintains a hash chain.
  Each packet carries a short MAC (4 to 8 bytes). The MAC key is disclosed in
  a later packet (10 to 16 bytes), after a fixed delay. Receivers verify the
  key against the chain and then the buffered MAC. This needs loose time
  synchronisation, which GPS provides, and only a hash function, which suits
  microcontrollers. Galileo OSNMA uses the same construction for navigation
  message authentication. Overhead is roughly 20 bytes per packet.
- **Identity beacon.** Every 10 to 30 minutes a station sends a beacon with
  its full 32-byte public key, validity, and the current chain root, signed
  by that key. This should fit within about 100 bytes.
- **Short signatures.** The identity beacon uses a Schnorr signature in
  `(e, s)` form on the Ed25519 curve, with a truncated challenge: 48 bytes
  with a 128-bit challenge, or 40 bytes with a 64-bit challenge at reduced
  forgery resistance. This is not wire-compatible with standard Ed25519 and
  gives up batch verification.
- **No key identifier.** The key is looked up by callsign. At most one byte
  of key index is kept for rotation.
- **Signature coverage.** Signatures and MACs cover everything the source
  wrote: the header and all TLVs. The hop trace follows the authentication
  tag and is not covered (5.9).
- **Unsigned packets** remain valid. Clients show them as unverified, and
  gateways MAY restrict some classes, such as messages, to verified sources.

### 10.5 Trust without a central registry

- **[agreed]** Keys are announced on air in the identity beacon. A central
  registry MUST NOT be required for the protocol to operate.
- **[agreed]** Trust on first use, with key continuity: a new key is accepted
  only when the old key endorses it.
- **[agreed]** Two mutually unendorsed keys for one callsign put both into a
  conflict state. The client warns; it does not pick one.
- **[proposed]** Infrastructure attestation: digipeaters and gateways MAY
  publish statements that they have heard a given key under a given callsign
  continuously for N days. Agreement among several independent stations is
  stronger than first use alone. This is an accumulation of observations, not
  a certificate authority.
- **[proposed]** Optional external anchors: a station MAY bind its key to an
  existing callsign credential (for example an ARRL LoTW certificate)
  published off air through DNS or a web page. Clients MAY consult it. On-air
  behaviour never depends on it.
- **[agreed]** Verification status is displayed in tiers (first use only,
  continuity for N days, attested by k stations, externally anchored), never
  as a single check mark.

### 10.6 Algorithm agility and quantum computers

- Published resource estimates for breaking 256-bit elliptic curves fell
  sharply during 2026, to the order of tens of thousands of physical qubits
  on proposed architectures. These are estimates for machines that do not yet
  exist. The trend still matters for a protocol meant to last decades.
- **[agreed]** Signature and key fields carry an algorithm identifier. A
  receiver treats an unknown algorithm as unsigned.
- The TESLA layer is hash-based and is not affected by Shor's algorithm.
- **[proposed]** Chain rollover is endorsed by the previous chain (a MAC under
  a key from the old chain) as well as by the signature, so that recovering a
  station's elliptic-curve private key is not sufficient to take over an
  established identity.
- Post-quantum signatures do not fit on air (Falcon-512: about 666 bytes of
  signature and 897 bytes of public key; ML-DSA-44 is larger). **[proposed]**
  They belong in the off-air anchor, with only a hash of the post-quantum key
  sent on air.

## 11. Governance

- **[agreed]** Specification first. The document defines both the wire format
  and the behaviour: routing, retries, channel access, beacon rates.
- **[agreed]** Packet types, TLV tags and algorithm identifiers are allocated
  from registries. Symbols need no registry of their own: the classic form
  is defined by APRS and the Unicode form by Unicode (5.6).
- **[agreed]** No client-only features. Anything a user can do must be
  expressible as standard packets that every conformant client renders.
- **[agreed]** At least two independent implementations before the format is
  frozen.
- **[agreed]** The specification is published under CC BY 4.0, which allows
  modification, redistribution and commercial use. Test vectors and
  registries are under CC0 1.0, and so are the code, constants and tables
  inside the documents, so that an implementation under any licence can
  copy them. Project code is under Apache-2.0.
- **[agreed]** Contributions come in under those same licences, with a
  sign-off and a patent non-assertion. No rights are assigned to a person
  or an organisation, so the terms do not depend on anyone continuing to
  exist.
- **[agreed]** "APRS" is a registered trademark of another party and is not
  part of the project's name. The project refers to APRS only to say what
  it is derived from and is not affiliated with the trademark's owner.
- **[open]** The final name. "QUA Network" is the current working name and
  is not fixed. Once a name is chosen it has to be checked against existing
  trademarks, and a rule is needed for its use: the licence permits
  modified versions of the text, and which of them may use the name is a
  separate matter.

## 12. Pitfalls to avoid

1. Application data in link-layer fields (Mic-E, WIDEn-N).
2. More than one valid encoding of the same content.
3. Floating point on the wire.
4. Decoding that depends on state from other packets.
5. Fragmentation on a broadcast access channel.
6. Whole-packet hashes as the deduplication key when a field changes in
   transit.
7. Authentication that covers a field which relays modify.
8. A signature on every packet.
9. A mandatory central key registry.
10. A binary verified badge that hides how weak first-use trust is.
11. A protocol defined by its reference implementation.
12. Feature logic that lives in one client.
13. An undocumented or private host interface.
14. Extending the flooding domain across trunks.
15. Treating a byte limit as a channel-occupancy limit. Airtime needs its
    own budget.
16. Encryption by default, which removes passive monitoring and excludes
    amateur bands.
17. No algorithm identifier, which makes a cryptographic migration a protocol
    change.
18. Design decisions made without measurement against real traffic.
19. Gateways altering packet content to fit a smaller link. It needs a
    droppable class, a truncation flag and split authentication coverage, and
    it has no good answer for packets whose text is the content.
20. Gateways segmenting or re-originating packets on behalf of a source.
21. A PDU limit equal to the radio's frame limit, leaving no room for the
    link envelope.
22. Behaviour derived from the display symbol.
23. Designing for the hardware limits of legacy TNCs and handhelds.
24. A specification that may be copied but not modified. Errata cannot be
    merged and corrected editions cannot be published.
25. Rights held by a body with no legal existence or successor.
26. A non-commercial condition on the specification text.
27. Reference material published with no licence statement.
28. A project name that depends on someone else's trademark.

## 13. Measurements from the APRS-IS corpus

This draft does not quote corpus statistics. The capture is still running,
so a figure written here would be out of date at once. Figures are
regenerated from the corpus with the tools of Appendix C when they are
needed, and are then stated together with the capture window and packet
count they came from.

### 13.1 Method

- Source: APRS-IS full feed, `rotate.aprs.net:10152`, receive-only login.
  The capture began on 2026-11-04 and continues, with gaps at reconnects.
- Stored as raw TNC2 lines prefixed with a Unix timestamp, bytes preserved,
  one file per hour.
- Lengths are byte lengths of the information field. The on-air frame size is
  estimated as `14 + 7 * digis + 2 + payload + 2`.
- Origin is classified by q-construct: `qAR`, `qAO` and `qAo` count as RF,
  everything else as IS. This classification is known to be inaccurate
  (13.4).

### 13.2 What is measured

| Measurement | Tool |
|---|---|
| Origin by q-construct | `qua-length-stats` |
| Payload and estimated frame length distribution | `qua-length-stats` |
| Digipeater path length | `qua-length-stats` |
| Payload length by data type | `qua-length-stats` |
| Sending software and devices by destination callsign | `qua-tocall-stats` |
| Source SSID classes | one-off script, not yet in the package |

### 13.3 Observations

These are the qualitative results the design relies on. They held in the
runs made so far and are to be re-checked against a current run before
anything is decided on them.

- A 255-byte limit excludes a negligible share of RF payloads, before any
  re-encoding. Judging by per-type maxima, most of what it excludes is
  user-defined (`{`) packets.
- Position reports of all kinds are the large majority of RF traffic. The
  efficiency of the core position encoding dominates channel load.
- The median Mic-E payload is about half that of the most common text
  position format, and still clearly shorter when the 7 bytes it places in
  the destination address are counted. Binary position encoding is worth
  roughly a factor of two on existing traffic.
- Message payloads pile up at the 67-character limit. It is a wall that
  users reach.
- Objects and user-defined packets produce the long tail.
- A few percent of RF packets begin with a byte that is not a standard data
  type identifier, spread over a large number of distinct byte values. This
  is a lower bound on traffic that a strict parser rejects.
- The mean digipeater path is a little over one address, and the AX.25
  header averages roughly a third of the mean frame.
- Position reports whose symbol is not a valid table character and code
  are rare. Where they occur the cause is usually not an unusual symbol:
  the packet is not a position report, the two characters are swapped or
  repeated, or a gateway has altered bytes in transit and shifted the
  field.
- A substantial minority of packets on the feed carry a source SSID that
  AX.25 cannot express: a letter, a number above 15, or two characters.
  These stations exist only on APRS-IS.

### 13.4 Caveats

- `qAr` is RF-origin and is counted as IS.
- A noticeable share of packets with an RF q-construct carry `TCPIP` in
  their path and did not come from a radio. They are concentrated in a
  small number of destination callsigns. Until the classification excludes
  them (section 15, step 1), every "RF-origin" result is contaminated.
- `qAS` does not reveal origin and may contain RF-origin packets.
- APRS-IS deduplicates, and deduplication differs between servers.
- The sample is biased toward regions with gateway coverage.
- The frame estimate counts unused path entries and ignores bit stuffing,
  flags and the transmit preamble. At 1200 baud the preamble (TXDELAY) can
  exceed the frame in airtime, so real channel occupancy is higher.
- The frame estimate assumes AX.25. LoRa APRS sends the TNC-2 text form on
  air, so its header is text and is longer than the binary AX.25 address
  field. LoRa-origin packets need a separate estimate once they are
  separated out.
- The reading that the most common non-standard first bytes (`N`, `K`, `W`,
  `A`) are plain-text identification beacons starting with a callsign is an
  inference from the distribution. It has not been checked by sampling.
- `qAO` as a proxy for receive-only (often LoRa) gateways is approximate.
- The SSID classes were counted over the whole feed, RF and IS together,
  as packets and not as distinct stations. The class that AX.25 cannot
  express also includes malformed sources and lower-case SSIDs, which were
  not separated.
- Traffic mix may differ by weekday, season and event.

## 14. Open questions

1. TLV container: custom, or a strict CBOR subset (5.2).
2. The exact PDU limit below 255 bytes, given the link envelope (6.1).
3. The airtime budget: its value, its window, and how it is expressed per PHY
   (6.3).
4. The recommended bitrate and the reference LoRa setting: SF9 at 250 kHz
   or SF8 at 125 kHz, checked against regional band plans (6.4).
5. Whether deployed KISS TNCs and soft modems pass frames that are not
   AX.25, and whether IL2P's transparent mode carries a native PDU (7.1,
   7.3).
6. Time-slotted access and coexistence with legacy stations (9).
7. Cryptographic review of the TESLA parameters, the truncated Schnorr
   challenge, and the chain rollover construction (10.4, 10.6).
8. The format and distribution of infrastructure attestations (10.5).
9. Area identifiers: how they are assigned and by whom (8.2).
10. Migration: translation between legacy APRS and QUA Network at gateways is
    lossy in at least one direction. What is preserved, and how is the loss
    marked?
11. Message reliability: acknowledgement, retry policy and segment
    retransmission.
12. Regional variation in traffic mix, and whether the MTU decision should
    follow the worst region.
13. Packed format for high-speed trunks (8.2). Deferred.
14. Recommended sizes per packet class (6.3).
15. The byte limit of the Unicode symbol form, proposed as 8 (5.6).
16. Unishox2: whether presets are chosen per string (the leading
    candidate) or one preset is pinned; which presets are allowed; how the
    encoder is specified independently of the reference implementation; and
    whether it is deterministic across platforms (5.7).
17. Use of the unused identifier values: the all-zero identifier, and
    37^12 up to 2^63 in the low 63 bits. Also whether the SSID positions
    use base 36 so that no SSID pattern needs rejecting (5.8).
18. In the optional AX.25 encapsulation, what the address fields hold,
    especially for an identifier that does not fit an AX.25 address (5.8,
    7.2).
19. Hop trace details: the tag and length encoding of the trailing TLV, and
    the maximum hop limit (5.9).
20. Whether identification through the PDU source alone satisfies local
    regulations where QUA Network is deployed.
21. The icon TLV: the order of its fields and how often it is repeated
    (5.6).
22. The final name ("QUA Network" is a working name), its check against
    existing trademarks, and the rule for its use by modified versions of
    the specification (11).

## 15. Next steps

1. Fix the origin classification (`qAr`; exclude `TCPIP` paths explicitly).
2. Extract packets above 255 bytes and all `{` packets; identify senders and
   PHY.
3. Separate LoRa traffic by destination tocall.
4. Parse the corpus into semantic records, taking APRS12c (Appendix D) as
   the reference for intended meaning. Record the true parse-failure rate
   and the distribution of comment length.
5. Train a zstd dictionary on the corpus and record per-packet compressed
   size as an approximate lower bound for any candidate encoding.
6. Draft the header and TLV tag table. Re-encode the corpus. Report, per
   candidate: the length distribution per packet class and the resulting
   airtime per PHY.
7. Check semantic round trip: APRS to semantic record to QUA Network to
   semantic record must be equal.
8. Publish the canonical text grammar and the first test vectors.
9. Consider publishing the raw corpus.
10. Build the divergence catalogue by differential testing of existing
    parsers against the corpus (Appendix E).
11. Run Unishox2 over the free-text fields extracted from the corpus,
    once per candidate preset: bytes saved per packet, the share of strings
    that fall back to passthrough, and the result by script (Latin, CJK,
    Cyrillic and others). Record the best preset for each string, and
    compare the total with per-string selection against the total with the
    single best preset. Also measure how often a station repeats its
    previous comment unchanged.
12. Test the native HDLC binding on real equipment: send frames whose first
    byte has the low bit set through Dire Wolf and through hardware KISS
    TNCs, and confirm that they are transmitted and received intact, and
    that legacy APRS software on the channel ignores them.
13. Implement the icon's run-length form (5.6) and add test vectors
    computed by an independent path, including
    bitmaps a decoder must reject. Extend the measurement of 5.6 to the
    APRS symbol table drawn at 16 by 16.

## Appendix A. Transceiver packet limits

Recalled from datasheets during the discussion and **not yet verified**.
Check each figure before relying on it.

| Transceiver | Mode | FIFO | Single-packet limit |
|---|---|---|---|
| SX127x | LoRa | 256 B | 255 B |
| SX127x | FSK/OOK | 64 B | 2047 B with FIFO refill |
| SX126x, LR11xx | LoRa | 256 B | 255 B |
| SX1231 / RFM69 | FSK | 66 B | 255 B, refill above 66 B |
| CC1101 | FSK | 64 B | 255 B, or infinite-length mode |
| CC1120 / CC1200 | FSK | 128 B | 255 B, or infinite-length mode |
| CC13x2 | proprietary, 802.15.4g | configurable | 255 B typical, 2047 B in 802.15.4g |
| Si446x | FSK | 64 B | 8191 B with refill |
| AX5043 | FSK | 256 B | 255 B |
| AT86RF212B | 802.15.4 | n/a | 127 B PSDU |
| nRF905 | GFSK | 32 B | 32 B |

The recurring 255 comes from an 8-bit length field and a 256-byte buffer. It
is a property of the host interface, not of the radio channel.

Reading this table against the single MTU of section 6.1: every device except
the last two can send a 255-byte packet. Those with a 64 to 128 byte FIFO
need a driver that refills the FIFO during transmission. The 802.15.4 radio
(127 bytes) and the nRF905 (32 bytes) fall below the MTU. They need
link-level fragmentation in their own binding or are out of scope (6.4).

## Appendix B. Approximate link throughput

Order-of-magnitude figures for capacity planning, excluding preamble and
channel-access overhead.

| PHY | Approximate throughput |
|---|---|
| AFSK 1200 baud | 150 B/s |
| FSK 9600 baud | 1.2 kB/s |
| LoRa SF7, 125 kHz | 600 B/s |
| LoRa SF9, 250 kHz (about 3.5 kbit/s) | 440 B/s |
| LoRa SF8, 125 kHz (about 3.1 kbit/s) | 390 B/s |
| LoRa SF12, 125 kHz | 30 B/s |

At SF12 a 255-byte packet occupies the channel for roughly 8 to 9 seconds.

## Appendix C. Tooling

The tools are the Python package in `pysrc/qua_network/`, installed as
commands.

- `qua-is-logger`: connects to the APRS-IS full feed and appends raw
  packet lines to hourly files, with reconnect and clean shutdown. Restarts
  begin a new file; gaps are accepted.
- `qua-length-stats`: constant-memory histogram statistics over the
  corpus: origin, payload and frame length, path length, per-type length.
- `qua-tocall-stats`: sending software and devices by destination
  callsign, resolved against the aprs-deviceid database.
- `qua-corpus-import`: converts the raw hourly files to Parquet without
  loss, for faster repeated measurement.
- `qua-check-vectors`: recomputes the test vectors of 5.1 and 5.9 and of
  the station identifier and icon specifications from `vectors/` and
  compares.
- `qua-icon-stats`: size of the candidate icon bitmap forms on the glyphs
  of BDF fonts.

## Appendix D. Reference documents

The APRS Documentation Project, maintained by WB2OSZ (the author of Dire
Wolf): <https://github.com/wb2osz/aprsspec>

| Document | Use for QUA Network |
|---|---|
| `APRS12c.pdf` | Unofficial compilation of the 1.0.1 reference and the updates since 2000. The working reference for what existing packets are meant to say. Draft, with known issues. |
| `APRS101.pdf` | The original 1.0.1 reference. Obsolete; kept for comparison only. |
| `Understanding-APRS-Packets.pdf` | Explains real packets and lists common mistakes. A starting list for the divergence catalogue. |
| `APRS-Digipeater-Algorithm.pdf` | A written digipeater algorithm, filling a gap the original working group left. Input to section 8.1. |
| `Minimizing-APRS-Collisions.pdf` | Input to section 9. |
| `APRS-Symbols.pdf` | Symbol table with on-air encoding. Defines the symbols that the classic form numbers (5.6). |
| `APRS-Information-Services.pdf` | Input to gateway and service design. |

Also referenced there: the AX.25 2.2 specification, the 1.1 addendum and the
1.2 proposal pages on aprs.org, and an IGate operation guide in the Dire Wolf
documentation.

## Appendix E. Divergence catalogue

QUA Network has to know how deployed software actually behaves, which differs
from what the documents say. The catalogue records every place where
implementations depart from the specification or from each other.

### E.1 Method

Differential testing is the main method. Reading source code is the follow-up
for explaining a difference once it has been found.

1. Run the corpus through several independent parsers. Candidates, to be
   confirmed: aprslib (Python), Ham::APRS::FAP (Perl) or its C port libfap,
   the Dire Wolf decoder, aprsc, javAPRSlib, Xastir, YAAC.
2. Normalise each parser's output into the same semantic record.
3. Compare. Every packet on which parsers disagree, or which some accept and
   others reject, becomes a catalogue entry.
4. Read the relevant code to find the cause, and record it.

This finds the differences that occur in real traffic and attaches a
frequency to each, so they can be ranked. Reading code alone finds many
theoretical differences without showing which ones matter.

### E.2 Categories

| Category | Meaning for QUA Network |
|---|---|
| Violates the specification but is common on air | Gateways translating legacy traffic must tolerate it. |
| Not defined by the specification | QUA Network must define it explicitly. |
| Ambiguous, and implementations read it differently | The canonical encoding must remove the ambiguity. |
| De facto extension outside the specification | Decide whether to adopt it as a registered TLV. |

### E.3 Entry format

Each entry records: a short description, the category, example packets from
the corpus, frequency in the corpus, how each parser behaves, the relevant
specification text if any, and the decision taken for QUA Network.

### E.4 Handling third-party code

Implementations are referenced, not copied. Use git submodules or record the
repository and commit hash, so that each observation is tied to a specific
version and licences (several are GPL) stay separate from this project.
