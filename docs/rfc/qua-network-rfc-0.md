# QUA Network: Requirements and Design Direction

An open specification attempt at modernizing APRS.

| | |
|---|---|
| Document | RFC draft 0 (design notes, not yet a wire specification) |
| Date | 2026-11-11 |
| Status | Exploratory. Nothing here is frozen. Sections 5.2, 5.8 and the icon of 5.6 have moved to `docs/spec/`; this document keeps their summary and rationale. |
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
that has a mandatory text form, lossless for content (5.4). The PDU is
placed directly in the frame of whatever link carries it, so the same
packet can cross 1200 baud AFSK, IL2P, LoRa, or an IP trunk without
re-encoding. QUA Network follows the possible uses of APRS loosely. It is
not a copy of APRS (3.2).

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
2. A canonical text representation that maps one-to-one onto the
   uncompressed binary form (5.4), enforced by round-trip test vectors.
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
- G2. A text form, lossless for content, that a person can read, type and
  `grep`.
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
- **[agreed]** A copy of APRS. QUA Network follows the possible uses of APRS
  loosely. It is not an exact copy of APRS. To hold the whole content of a
  legacy APRS packet without loss is not a goal. APRS already has many
  obsolete designs, and many features that remain only for historical
  reasons. A single field can still convert without loss, as the classic
  symbol of 5.6 does.

A translation between APRS and QUA Network at a gateway can therefore lose
information (section 14, question 10). The project still studies where
implementations depart from the APRS documents, and where those documents
contradict themselves (Appendix E, `docs/legacy/`).

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
- **[proposed]** Header contents: protocol version (5.10), flags, source
  callsign and SSID (encoded as in 5.8), a per-source sequence number, hop
  limit, and payload length. Everything else is a TLV.
- **[agreed]** The header also has the type of the PDU. One PDU has one
  type (5.11).
- **[proposed]** The header is 14 bytes, in this layout:

  | Offset | Bytes | Field |
  |---|---|---|
  | 0 | 1 | Version byte (5.10). |
  | 1 | 1 | Hop limit, 3 bits. Flags, 5 bits. |
  | 2 | 1 | Type (5.11). |
  | 3 | 1 | Payload length. |
  | 4 | 8 | Source identifier (5.8), in big-endian order. |
  | 12 | 2 | Sequence number, in big-endian order. |

- **[agreed]** The version byte is the first byte of the PDU. A receiver
  reads it before every other field, so it knows how to read them.
- **[agreed]** The sequence number has 16 bits. A station starts at a
  random value each time that it starts. It adds 1 for each PDU that it
  sends. After 65535, the next number is 0.
- **[agreed]** A sequence number can therefore occur again. A relay or a
  receiver keeps a deduplication entry for a limited time only (6.2).
- **[agreed]** The header has these three flags:

  | Flag | Meaning |
  |---|---|
  | No Internet | A gateway does not carry the PDU from radio to the Internet. |
  | Translated | A gateway made the PDU from a legacy packet (section 14, question 10). |
  | Authenticated | The PDU has an authentication tag (section 10). |

- **[proposed]** In the second byte, from the most significant bit down:
  the hop limit in 3 bits, then the flags No Internet, Translated and
  Authenticated, then 2 reserved bits. A source writes 0 in a reserved
  bit. A receiver ignores a reserved bit.
- **[open]** How a receiver finds the end of the TLV area in a PDU that
  has an authentication tag. The payload length counts both.
- **[proposed]** The header never changes in transit. It carries the hop
  limit chosen by the source, not a count that relays decrement; the number
  of hops used is read from the trailer (5.9). The payload length counts
  the header, the TLVs and any authentication tag, and excludes the
  trailer and the checksum.
- **[agreed]** The PDU carries its own frame checksum, CRC-32C (Castagnoli),
  independent of any link-level check. There is one checksum, at the very
  end of the frame.
  - Parameters: polynomial `0x1EDC6F41` (reflected `0x82F63B78`), initial
    value `0xFFFFFFFF`, input and output reflected, final XOR `0xFFFFFFFF`.
    The check value for the ASCII string `123456789` is `0xE3069283`.
  - It covers everything before it: what the source wrote and the trailer
    of 5.9. A relay, which changes the trailer, recomputes it. An earlier
    version covered only what the source wrote and was never recomputed;
    5.9 records why that was dropped.
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
  The version byte gives this bit (5.10).

The flags hold only what a relay or a gateway needs before it reads a
TLV. In APRS, the path entries `NOGATE` and `RFONLY` have the function of
the flag No Internet.

A station with no permanent storage starts its sequence number again
when it restarts. If it started at 0, the relays near it would have
entries for the same numbers and would drop its new PDUs. The random
start and the time limit of an entry are the answer to this. Dropped: a
sequence number of 32 bits. It costs 2 more bytes in every PDU. With
these two rules, 16 bits are sufficient for deduplication. The sequence
number alone does not prevent a replay (section 14, question 7).

A frame that no relay has changed has 19 bytes that are not TLVs: the
header of 14, the control byte of 5.9 and the checksum of 4. Each hop adds
3 bytes. For comparison, an AX.25 UI frame with no digipeater has 18: the
16 bytes of section 4 and a frame check sequence of 2. Each digipeater
adds 7 (derived).

### 5.2 TLV container

- **[agreed]** Fields are encoded as lightweight TLVs.
- **[agreed]** A receiver MUST be able to skip a TLV it does not understand
  and MUST preserve it when relaying or logging.
- **[agreed]** TLV order is canonical. Two encodings of the same content
  MUST NOT both be valid.
- **[agreed]** Field compression is the one exception. A field that has a
  compressed form is valid without compression, and in any compressed
  encoding that decodes to the same content (5.6, 5.7). The rule above
  applies to the uncompressed form of the PDU (5.4).
- **[agreed]** The value of a TLV is 255 bytes at most
  ([`docs/spec/03-tlv.md`](../spec/03-tlv.md) section 2). A longer value
  cannot fit the PDU limit of section 6, so it has no use.
- **[agreed]** The container follows the option format of CoAP (RFC 7252
  section 3.1): the first byte of a TLV holds the difference between its
  tag and the tag before it in four bits and the length in the other four,
  with extension bytes for larger values. It is specified in
  [`docs/spec/03-tlv.md`](../spec/03-tlv.md).
- **[agreed]** A tag may repeat, for example for several values of one
  telemetry item.
- **[agreed]** Each PDU type has its own tag space (5.11). A tag has a
  meaning only together with the type.

Why this container:

- Tags can only be written in increasing order, so the canonical order is a
  property of the format and not a rule a decoder has to check.
- A TLV whose tag is close to the one before and whose value is 12 bytes or
  less costs one byte of overhead. What matters for size is therefore not
  how large a tag is but how far it is from its neighbours in the same PDU,
  which is a question for the tag table.
- The container is byte oriented: a TLV is skipped by adding to an index,
  and an unknown TLV has a value that the text form can show in hexadecimal
  (5.4). Dense bit-level encodings belong inside a value, as in 5.6 and
  5.8.

Dropped: a strict subset of CBOR with deterministic encoding (RFC 8949
section 4.2), and a custom format that would also be valid CBOR, which was
the earlier preference. A CBOR map with integer keys costs about two bytes a
field plus one for the map, against about one byte here. Its advantage is
existing parsers, but a general parser accepts encodings outside the subset
and so does not enforce the single encoding this design needs; a conforming
decoder would be written for the subset anyway. The statements about CoAP
and CBOR in this section were written from recollection of the two RFCs and
are to be checked against them.

### 5.3 Numeric and text rules

- **[agreed]** No binary floating point on the wire. A quantity is an
  integer with a fixed scale, for example latitude and longitude as int32
  in units of 1e-7 degree, or it is a decimal number (below).
- **[agreed]** WGS84 only.
- **[agreed]** A quantity is in its SI unit, unless that unit is not
  practical for the quantity. Then the specification gives the quantity a
  practical unit. Practical use is more important than agreement with the
  SI.
- **[agreed]** A practical unit can differ from the SI unit by a decimal
  prefix, by a factor that is not a power of ten, or by an offset.
- **[agreed]** Temperature is in degrees Celsius, not in kelvin.
- **[agreed]** Speed is in kilometres per hour, not in metres per second.
- **[agreed]** Pressure is in hectopascals, not in pascals.
- **[agreed]** Speed is a decimal number (below), not an integer with a
  fixed scale. An aircraft exceeds 255 km/h, the range of one byte.
- **[agreed]** Wind speed is a speed. It is in kilometres per hour too.
- **[agreed]** One quantity has one unit. The specification fixes it, and
  a sender cannot choose another. No field holds a prefix.
- **[agreed]** A quantity in this rule is one kind of use, not one
  physical dimension. Altitude, range and rain depth are lengths, and they
  are three quantities.
- **[agreed]** The SI unit is not practical if, for the usual values of
  the quantity, it needs more bytes or gives text that is hard to read.
- **[agreed]** A practical unit is a unit of daily metric use. The mile
  per hour, the knot and the degree Fahrenheit are not practical units in
  this sense.
- **[agreed]** Time is an integer count from a fixed epoch in UTC.
- **[proposed]** Precision or uncertainty is an explicit field. Blanked digits
  are not used.
- **[agreed]** Strings are UTF-8.
- **[agreed]** Telemetry is self-describing or refers to a registered schema.
  A value MUST NOT depend on a separate definition packet having been heard.
- **[agreed]** A gateway that translates a legacy value to a unit of this
  section rounds the value. A reasonable loss is acceptable (3.2). The
  rounding rule is not written (section 14, question 10).

An earlier revision allowed no floating point of any kind. Every quantity
was an integer with a fixed scale, and altitude was a signed integer in
centimetres. The author replaced it when the decimal number was added.

An earlier revision allowed SI units only. The author replaced it. The
reason is that the SI unit is not always the practical one. An air
temperature in kelvin is harder to read than one in degrees Celsius. In
the decimal number below, it also needs one more byte: 25.3 °C has the
significand 253, and 298.45 K has the significand 29845, which does not
fit 12 bits.

A first decision of this revision kept speed in metres per second. The
author replaced it. Kilometres per hour is the unit of daily use. Its step
of 1 also fits a vehicle speed: in metres per second, a step of 0.1 is
finer than needed and a step of 1 is too coarse. A client can show a speed
in another unit.

1 knot is exactly 1.852 km/h. A whole number of knots or of miles per
hour, rounded to a whole number of kilometres per hour, converts back to
the same number. The rounding error is 0.5 km/h at most, which is 0.27
knot or 0.31 mile per hour (derived).

Pressure in hectopascals and in pascals needs the same bytes, because the
exponent of the decimal number holds the prefix. The reason for the
hectopascal is the text form: `1013.2` is easier to read than `101320`.

With two units for one quantity, one value has two encodings: 1000 pF and
0.001 µF. This is the reason for the one-unit rule.

#### Decimal number

The integer rule above fits a quantity with a known range and one
resolution. It does not fit a quantity with a wide range, such as speed or
altitude. It also does not fit a telemetry value with no registered
schema, because that value has no fixed scale. The decimal number is for
these cases.

- **[agreed]** A decimal number is a significand `m` and an exponent `e`.
  Its value is `m` × 10^`e`. The definition of a field states whether the
  field is a decimal number or an integer with a fixed scale.
- **[agreed]** Altitude is a decimal number, in metres.
- **[agreed]** A decimal number has one of four formats. Each is in
  big-endian order, with `e` before `m`. `e` and `m` are two's-complement
  integers. No format is longer than 4 bytes.

  | Bytes | Bits of `e` | Range of `e` | Bits of `m` | Range of `m` |
  |---|---|---|---|---|
  | 1 | 4 | −8 to 7 | 4 | −8 to 7 |
  | 2 | 4 | −8 to 7 | 12 | −2048 to 2047 |
  | 3 | 4 | −8 to 7 | 20 | −524288 to 524287 |
  | 4 | 8 | −128 to 127 | 24 | −8388608 to 8388607 |

- **[agreed]** The length of the TLV gives the format.
- **[agreed]** A TLV therefore holds one decimal number at most, and the
  number is the last field of the TLV.
- **[agreed]** Zero has one encoding: one byte, with `m` 0 and `e` 0. For
  every other finite value, `m` MUST NOT be a multiple of 10.
- **[agreed]** A sender MUST use the shortest format that holds `m` and
  `e`.
- **[agreed]** The format has two special values, in the 1-byte format
  only. The byte `70` (`m` 0, `e` 7) is positive infinity. The byte `80`
  (`m` 0, `e` −8) is negative infinity.
- **[agreed]** Positive infinity states that the value is greater than
  every value that the sender can give. Negative infinity states that it
  is less than every such value. An infinity is not an error code.
- **[agreed]** The definition of a field states whether the field allows
  an infinity.
- **[agreed]** A decoder MUST reject an infinity in a field that does not
  allow it.
- **[agreed]** The format has no "not a number".
- **[agreed]** The other 13 encodings of 1 byte with `m` 0 stay invalid.
  The specification does not reserve them for a later use.
- **[agreed]** A sender that has no value omits the TLV.
- **[agreed]** A decoder MUST reject a decimal number that is not in this
  form. The cases are these:
  - `m` is a multiple of 10 and is not 0;
  - `m` is 0, and the bytes are not `00`, `70` or `80`;
  - a shorter format holds `m` and `e`.
- **[agreed]** If `e` is from −8 to 7, the text form is the plain decimal
  value, with no exponent notation: `25.3`, `-12.7`, `0.12`, `85000`.
- **[agreed]** The plain form has no `+` sign. Its integer part is `0`, or
  starts with a digit from 1 to 9. Its fraction has 8 digits at most and
  does not end in `0`. The text `-0` is invalid.
- **[agreed]** If `e` is outside −8 to 7, the text form is `m`, the
  letter `e` and the exponent, each as an integer: `3e9`, `-15e-12`. Such a
  value has no plain form.
- **[agreed]** The text form of positive infinity is `inf`. The text
  form of negative infinity is `-inf`.
- **[agreed]** A parser MUST reject a text that breaks these rules, or
  whose value has no encoding.

With these rules, one value has one encoding and one text form. `m` and
`e` are unique for a value, because `m` has no factor of 10. The
conversion to text moves the decimal point and needs no rounding.

In the formats of 1 to 3 bytes, the first hexadecimal digit is `e`. The
bytes `F0 FD` have `e` = −1 and `m` = 253, the value 25.3.

Examples, derived by hand. They are not test vectors.

| Value | `m` | `e` | Bytes |
|---|---|---|---|
| 0 | 0 | 0 | 1 |
| 100 | 1 | 2 | 1 |
| 25.3 | 253 | −1 | 2 |
| −12.7 | −127 | −1 | 2 |
| 853.4 | 8534 | −1 | 3 |
| 1013.2 | 10132 | −1 | 3 |
| 10668.25 | 1066825 | −2 | 4 |
| 3 × 10^9 | 3 | 9 | 4 |
| positive infinity | 0 | 7 | 1 |
| negative infinity | 0 | −8 | 1 |

An infinity covers a sensor at the end of its range, and a quantity that
is infinite, such as the standing wave ratio of an open line. The two
infinities keep the order of values: every finite value is between them.
"Not a number" does not, and a sender with no value omits the TLV. This is
why the format has the first and not the second.

The two infinities use encodings that are invalid without them, so no
finite value is lost. Each has one encoding. A later minor version cannot
add a special value, because a decoder of this version rejects the
encoding (section 14, question 23). The decision is therefore made now.

The author does not reserve the other 13 encodings, for two reasons. An integer with a fixed scale has no code for an absent value, so
a code in the decimal number would serve one kind of number only. A code
in the manner of "not a number" is also easy to misuse.

An earlier proposal of this revision had no special value. The author
added the infinities. The author first considered the 4-byte format for
them. One format is sufficient for a single encoding, and the 1-byte
format costs 3 bytes less.

The largest significand of the 4-byte format has 7 digits. A value with
more significant digits has no encoding. The author accepts this limit. A
value that large does not need a resolution that fine: an altitude above
83 km does not need centimetres.

Dropped: a 4-byte format with a 6-bit exponent and a 26-bit significand,
and a format of 5 bytes or more. The first is not aligned to bytes. The
second has no known use.

The plain text form stops at an exponent of −8 or 7. Outside that range,
the plain form of a value can have more than 100 digits, so the text uses
exponent notation.

An earlier proposal of this revision had 2 and 3 bytes only. To keep
large values in range, it let `m` be a multiple of 10 if `e` was 7. The
4-byte format replaces that exception: a value with an exponent above 7
uses it. The author asked for the larger exponent, to record very large
values.

Prior work: IEEE 11073-20601 defines the SFLOAT type, with the same 4-bit
decimal exponent and 12-bit significand in 2 bytes. It reserves five
significand values for special values such as "not a number". This
statement comes from two secondary sources, read on 2026-11-15: the HL7
Personal Health Device implementation guide, and the documentation of the
Nordic nRF Connect SDK 2.3.0. The standard itself was not read. The same
standard defines a FLOAT type of 4 bytes. That it has an 8-bit exponent
and a 24-bit significand is recalled, not read.

Dropped: binary floating point in 16 bits, as bfloat16 or as IEEE 754
binary16. Three reasons:

- A decimal text and a binary value do not map one-to-one (5.4). The
  specification would need a rule for the shortest decimal text, and a
  parser would have to reject every other text. A signature check from a
  text log (5.5) would then depend on that conversion in every
  implementation.
- bfloat16 has 8 significant bits. Between 512 and 1024 its step is
  2^9 / 2^7 = 4, so it cannot hold a pressure to 1 hPa.
- binary16 has 11 significant bits, and its largest value is
  (2 − 2^−10) × 2^15 = 65504. A light level of 85000 lx does not fit.

### 5.4 Canonical text representation

- **[agreed]** QUA Network defines two representations of a PDU: binary and
  text. The mapping between them is one-to-one when the PDU has no
  compressed field. Such a PDU has exactly one text form. A valid text form
  converts to exactly one such PDU. The mapping is lossless in both
  directions.
- **[agreed]** The mapping holds between implementations of the same
  version (5.10). An implementation of an earlier minor version writes a
  TLV of a later minor version as hex, so its text form is different.
- **[agreed]** The mapping makes no claim about a legacy APRS packet. A
  translation between APRS and QUA Network can lose information (3.2).
- **[agreed]** A compressed field is an icon bitmap in the gap form (5.6)
  or a string marked compressed (5.7). A fixed encoding, such as the
  identifier of 5.8, is not a compressed field.
- **[agreed]** The uncompressed form of a PDU has the same content and no
  compressed field. In it, every icon bitmap is in the plain form, and
  every string is passthrough.
- **[agreed]** Every receiver MUST be able to decode every compressed form
  that the specification defines. The decoder rules are the same for every
  receiver, so every receiver of one major version builds the same
  uncompressed form (5.10).
- **[agreed]** The specification fixes, for one major version, the TLVs
  that can hold a compressed field (5.10). A receiver skips a TLV that it
  does not know, or shows it as hex. That TLV holds no compressed field,
  so the receiver still builds the same uncompressed form.
- **[agreed]** The text form shows the uncompressed content of a compressed
  field. A PDU with a compressed field therefore has the same text form as
  its uncompressed form. Its text form converts to the uncompressed form.
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
QUA1 N0CALL-9 position seq=1042 hop=2 pos=24.2500000,120.6700000 alt=152
```

An earlier revision claimed the mapping for every PDU, compressed fields
included. Section 5.7 proposed a canonical encoder to make that true, and
5.6 applied the same rules to the icon. The author narrowed the mapping to
the case with no field compression. The reason is that the rules become
simpler and an implementation becomes easier to write.

The earlier revision also did not consider implementations of different
versions. The mapping has a meaning only between implementations of the
same version.

### 5.5 Conformance

- **[agreed]** The specification ships round-trip test vectors. An
  implementation conforms only if binary to text to binary is bit-identical
  for every vector with no compressed field, including vectors with unknown
  TLVs.
- **[agreed]** For a vector with a compressed field, binary to text gives
  the text of the content. Text to binary gives the uncompressed form.
- **[agreed]** The source computes a signature over the uncompressed form
  of the PDU (5.4). The uncompressed form does not depend on the form that
  the source chose, so the rules are much simpler.
- **[agreed]** In the uncompressed form, a string is passthrough and has
  no length byte (5.7). Every TLV length and the payload length of 5.1 are
  those of the uncompressed form. The other header fields are as sent.
- **[agreed]** A receiver that verifies a signature first rebuilds the
  uncompressed form. A text log is sufficient for this, because the text
  form converts to the uncompressed form (5.4). The author considers the
  cost of decompression acceptable for the devices of 3.3.
- **[agreed]** The PDU limit of section 6 applies to the bytes as sent and
  to the uncompressed form (5.7).
- **[agreed]** The uncompressed value of every field fits a TLV (5.2).
  This follows from the limit on the uncompressed form.
- **[agreed]** The limit on the uncompressed form counts the largest hop
  trace that the PDU can get (5.9). The hop trace therefore takes room from
  the PDU. The author accepts this, so that the protocol is rigorous.
- **[agreed]** The largest hop trace is the control byte and 3 bytes for
  each hop of the hop limit of the PDU. The frame with the uncompressed
  form, that trailer and the checksum fits the MTU of 6.1.
- **[agreed]** A signature does not show which form the source used. A
  relay or a gateway that changes the form does not obey 6.2, and the
  signature still verifies. The author accepts this. The content is more
  important than the bytes as sent.
- The frame checksum of 5.1 is a different check. It covers the bytes as
  sent.

An earlier revision computed signatures over the bytes as sent. It relied
on the canonical encoder of 5.7, so that a text log gave the same bytes.
The author replaced it. The uncompressed form does not change when a
sender compresses a field, so the rules are much simpler.

An earlier decision let the uncompressed form be longer than the PDU
limit, if the bytes as sent fitted. The author replaced it with the first
item of 5.7, for the reason given there.

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
optional TLV beside the symbol. The bitmap is sent plain, or in a compressed
form that is often shorter. It does not replace the symbol. The icon is
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
  not show icons or have not yet received one. An earlier version made
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
each row XORed with the one above and the distances between the set bits
of the result coded in Elias gamma (the gap form). The gap form has one
exactly specified bit stream, test vectors, and a decoder that rejects a
malformed gap form. The details of the bit stream are in the specification
file.

**[agreed]** A sender can use either form, and a decoder accepts both.
The specification file recommends the gap form when it is shorter, because
it costs less airtime.

**[agreed]** The gap form has no length byte of the kind that 5.7 gives a
compressed string. An icon bitmap is always 32 bytes before compression,
and the length byte is for fields of variable length.

An earlier revision applied the canonical encoder rule of 5.7 to the icon:
the gap form if and only if it was strictly shorter. A decoder accepted a
longer plain form as an exception. To reject that plain form, a decoder
would have to compute the gap form of every plain bitmap. The author
dropped the rule for the same reason as the rule of 5.7. The checks of the
gap form bit stream in the specification file stay as they were.

Rows of a drawn picture resemble their neighbours, so the row XOR leaves
mostly zeros with single set bits where an outline moves, and a gap is one
short code for each of those bits.

`qua-icon-stats` measures the forms on the glyphs of bitmap fonts, each
centred in the 16 by 16 cell. The fonts are the BDF sources kept in the
u8g2 repository (commit `ab9e48b2`, 2026-06-27; run on 2026-11-12). Open
Iconic at 16 pixels is the closest to what a station would draw. Sizes are
mean bytes before the fallback to the plain form; "used" is the share of
glyphs for which the gap form is shorter than 32 bytes.

| Test set | Glyphs | Gap form | Used | Alternating run lengths |
|---|---|---|---|---|
| Open Iconic, 16 by 16 (`open_iconic_all_2x`) | 223 | 18.2 | 100% | 19.6 |
| Siji, 12 by 12 (`siji`) | 624 | 12.5 | 100% | 13.2 |
| Unifont symbols and dingbats, U+2600 to U+27BF | 448 | 18.9 | 98.0% | 20.1 |
| Unifont emoji blocks, U+1F300 to U+1F64F, U+1F680 to U+1F6FF, U+1F900 to U+1FAFF | 1,316 | 21.7 | 98.9% | 22.7 |
| of which emoticons, U+1F600 to U+1F64F | 80 | 26.7 | 100% | 28.3 |
| Unifont CJK ideographs, U+4E00 to U+9FFF | 20,991 | 27.9 | 80.1% | 28.7 |

Drawn icons come to a little under three fifths of the plain size, small
ones to about two fifths, and glyphs that fill the cell, such as faces and
ideographs, hardly compress.

The gap form is weak where the row XOR leaves long runs of set bits, which
happens when whole rows alternate: horizontal stripes one pixel high and a
checkerboard stay in the plain form, and stripes two pixels high come to 23
bytes (these three are in `vectors/icon-bitmap.json`). Alternating run
lengths code such patterns in a few bytes. The test sets hold few of them.

Dropped alternatives:

- Alternating run lengths in place of gaps: one bit for the first value,
  then the length of every run of equal bits in Elias gamma. This was the
  agreed form before the gap form replaced it. It is about one byte longer
  on every test set (last column above), because a set bit standing alone
  costs a code of its own, and its decoder carries the current value as
  extra state.
- Leaving out the last run of that form, which a decoder can infer because
  the bitmap always has 256 pixels. It measured about one byte shorter.
  Dropped as too particular a rule for that gain.
- Other predictions in place of the row above, each with alternating run
  lengths: the pixel to the left, the XOR of left, above and above-left, a
  majority of those three, a column-wise or serpentine scan, and a header
  that selects the best of four predictions for each icon. None was better
  than the row above except the selectable one, by under one byte, for
  four predictors in every decoder.
- Simple LZ77 forms on bytes and on bits, with and without the row XOR,
  each with an optimal parse. All were longer than alternating run lengths,
  by one and a half bytes or more: 32 bytes are too few to build a history,
  and a row that resembles the one above is not a copy of it.
- Tokens in the manner of QOI (repeat the previous unit, refer to one seen
  earlier, a small difference, a literal) with a row or a byte as the unit.
  About equal to alternating run lengths with rows, longer with bytes.
- Cropping to the bounding box and sending the pixels inside it. A
  hand-drawn icon is expected to fill nearly the whole 16 by 16 cell, so
  there is little to crop. In the first one-off measurement, on font
  glyphs, it came out about the same as alternating run lengths.
- An adaptive arithmetic coder with a causal pixel context. Its ideal code
  length in the first one-off measurement was two or three bytes below
  alternating run lengths, which a real coder approaches but does not reach. A
  picture of 256 pixels is too short for the model to adapt, and a fixed
  probability table would write one font's statistics into the format.
- Deflate, which was longer than the plain bitmap on a third or more of the
  symbols and emoji in the same measurement.

The first one-off measurement used the 16 by 16 glyphs of GNU Unifont
18.0.01 and a script that was not kept. The predictions, LZ77 forms and
QOI-like tokens were measured on 2026-11-12 on the Open Iconic, Siji and
Unifont symbol sets above, with one-off scripts that were not kept either.
These figures are not reproducible and are quoted here only for the dropped
alternatives.

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

- **[agreed]** Compression saves airtime. It is not a way to send content
  that does not fit the PDU limit in its uncompressed form. The
  uncompressed form of a PDU MUST fit the PDU limit of section 6.
- **[agreed]** Of the string fields, only free-text fields are compressed
  (comment, status, message body). The only other compressed field is the
  icon bitmap of 5.6. Tags, lengths and other binary values are sent as
  they are. The TLV structure is always readable without decompressing
  anything.
- **[agreed]** The method is Unishox2, a codec designed for short Unicode
  strings.
- **[agreed]** A sender SHOULD compress each string as a trial. It SHOULD
  send the compressed form only if that form is strictly shorter than the
  UTF-8 original. Otherwise it SHOULD send the string unchanged
  (passthrough). Unishox2 can expand some inputs. Passthrough is therefore
  always allowed.
- **[agreed]** A compressed string starts with a length byte. The length
  byte gives the length of the uncompressed string, in bytes. A
  passthrough string has no length byte.
- **[agreed]** Only a compressed field of variable length has a length
  byte. A TLV value is 255 bytes at most (5.2), so one byte is sufficient.
- **[agreed]** The length byte counts as part of the compressed form when
  the sender compares the lengths.
- **[agreed]** A decoder does not run an encoder. It does not reject a
  field because the sender did not choose the shortest form.
- **[open]** Which malformed compressed strings a decoder rejects
  (section 14, question 16).
- **[proposed]** Each text field carries a marker saying which form it holds:
  passthrough or compressed. If per-string preset selection is adopted (see
  "Choice of preset" below), the marker becomes a preset number, with 0 for
  passthrough.
- **[open]** How a text field carries the marker. A passthrough string has
  no length byte, so the marker is not a byte of a passthrough string.
  Whether the length byte holds the preset number is also open (section
  14, question 16).
- **[agreed]** The specification pins the exact decoder behaviour of every
  compressed form that it allows. It does not pin an encoder. Two
  independent decoders give the same string for the same field.
- **[proposed]** The specification pins the allowed Unishox2 preset or
  presets, and ships test vectors taken from real corpus strings.
- The canonical text form shows the uncompressed string. Compression is not
  visible in text.
- The short Unicode symbol of 5.6 is not compressed; at 8 bytes or less
  there is nothing to gain.

An earlier revision proposed a canonical encoder. A sender used the
compressed form if and only if it was strictly shorter. The specification
pinned one exact encoder behaviour. A decoder recompressed each string and
rejected any other bytes. The purpose was the round trip of 5.4 for a
compressed string. The author dropped the decoder check and the pinned
encoder, because they were too strict and made the rules too complex.

The trial rule of the sender was a requirement. The author changed it to a
recommendation, together with the canonical encoder and for the same
reason. The icon rule of 5.6 changed in the same way.

**[open]** The details of Unishox2 in this section are still under study:
the presets and the exact decoder. The author considers a reduced Unishox2
implementation that has only the presets that this project can use. It
would make the work simpler and let the specification freeze (section 14,
question 16).

The first item of this section has these consequences:

- Whether the sender segments content depends on the content only. It does
  not depend on how well an encoder compresses, and the specification does
  not pin an encoder.
- A frame that a receiver rebuilds from the text form fits the limit,
  with every hop trace that the frame can get (5.5).
- A receiver needs a buffer of one PDU limit only.

The cost is that compression cannot put a longer text into one PDU. The
sender segments that text (6.5).

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

**[agreed]** The candidates are `USX_PSET_DFLT` and `USX_PSET_NO_DICT`.
The author narrowed the choice to these two after the measurement of
section 15, step 11. **[open]** Which of the two.

**[proposed]** The specification allows one preset for every string.
Approach B below is then not used. In the measurement, the best preset
for each string is only a little better than the best single preset, and
that figure does not count the marker
([`docs/research/01-free-text.md`](../research/01-free-text.md)).

**[proposed]** `USX_PSET_DFLT` is the better of the two candidates
([`docs/research/02-unishox2-reading.md`](../research/02-unishox2-reading.md)).
The decoders of the two differ little, and an encoder for either can
leave out the search for a repeat, because the specification does not pin
an encoder.

The text below records the choice as it was before the measurement. The
reference implementation defines 17 presets
(`USX_PSET_DFLT`, `USX_PSET_ALPHA_ONLY`, `USX_PSET_FAVOR_ALPHA`,
`USX_PSET_NO_DICT`, `USX_PSET_URL` and others). Three ways to use them:

| Approach | Who decides | Extra bits |
|---|---|---|
| One preset for everything | The specification | none |
| A. Preset fixed per field type | The specification | none |
| B. Preset chosen per string | The sender | a small preset number per string |

Every compressed string also has the length byte of this section. Whether
the preset number is part of the length byte is open (section 14,
question 16).

**B was the leading candidate before the measurement.** A comment field holds URLs,
English sentences, Chinese, frequencies and more, so a preset fixed by
field type is barely a choice. Selecting per string also removes the
language-bias concern: a preset with English fragments is used only on
strings where it actually wins.

If B is adopted, these rules apply (**[proposed]**):

- The marker of each text field is the preset number, 0 meaning
  passthrough.
- The sender chooses the preset. A sender that wants the shortest result
  compresses the string with every allowed preset and compares.
- A decoder uses the preset that the marker gives. It does not check the
  choice of the sender.

An earlier revision made the choice canonical. The sender took the
shortest result, and the lowest preset number on a tie. A decoder reran
the rule and rejected any other choice. The author dropped this with the
canonical encoder above, for the same reason.

Costs of B:

- The allowed set has to be small, three or four presets, so that the
  marker is 2 bits. Each extra preset is one more compression pass for a
  sender that compares, and one more set of conformance vectors.
- Every allowed preset needs a decoder definition that is exact enough for
  two implementations to give the same string.

Other considerations, whichever approach is taken:

- The default preset's sequences are punctuation and are neutral between
  languages. A text preset builds in English fragments, which do nothing
  for Chinese or Japanese comments.
- `USX_PSET_NO_DICT` is described in the source as the preset for input
  with no repeating sequences. It has no code for a back-reference, so its
  encoder has no search for a repeat (read at commit `6ec2ff0`). On the
  capture, it gives a slightly larger size than the default preset. The
  two research reports above have the reading and the figures.
- Unishox2 also accepts custom presets. A preset built from APRS traffic
  would be a small dictionary that ages, which the no-dictionary rule
  excludes.

The decision waited for the corpus measurement (section 15): the total
length with the best preset per string, against the total with the single
best preset overall. A difference of a percent or two does not justify the
extra rules. The measurement is now made
([`docs/research/01-free-text.md`](../research/01-free-text.md)).

#### Risk to manage

Unishox2's behaviour is in practice defined by its reference
implementation. Adopting it by reference would repeat pitfall 11. The
specification therefore has to state the decoder precisely, or cite the
published Unishox2 description and back it with test vectors. The encoder
does not have to give the same bytes on every platform. No decoder
compares bytes, and the signature covers the uncompressed form (5.5).

An earlier revision considered compressing the whole body, TLV structure
included. It was dropped: binary values barely compress, structural
redundancy is better removed by a dense TLV encoding, and it needed a
mandatory method identifier in the header and a decompression step at every
filtering gateway, for little expected gain.

Related, and a larger saving: a station need not send the same comment
in every beacon. In the measurement, most comments are equal to the
comment before from the same station. The PDU types of 5.11 use this: the
text is in the station information PDU, which a station sends seldom.

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

Each station that relays a PDU records itself in a trailer near the end of
the frame.

```
| header | TLVs | auth tag | control | entry, entry, ... | CRC-32C |
  written by the source      the trailer, written by relays  recomputed by relays
```

- **[agreed]** A relay appends one entry. No entry is reserved in advance,
  so a PDU that is never relayed carries a trailer of one byte.
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

The trailer:

- **[agreed]** The trailer has a fixed layout and is not a TLV: one control
  byte, then the entries of 3 bytes each in the order of the hops. Every
  frame has a trailer; the source writes the control byte. It
  replaces an earlier design in which the trace was a TLV at the end of the
  frame, outside the checksum and protected only by whatever check the
  link had.
- **[agreed]** The trailer is covered by the one checksum of the frame
  (5.1), which comes after it. A link cannot be assumed to have a check of
  its own: a PDU sent as the bare payload of a LoRa or FSK packet has only
  what this format gives it.
- **[agreed]** The control byte, from the most significant bit down:

  | Bits | Field |
  |---|---|
  | 1 | Set if the PDU has crossed a path that is not radio. |
  | 1 | Reserved. |
  | 3 | Entry count: the number of entries in this trailer. |
  | 3 | Hops remaining. |

- **[agreed]** The entries may be fewer than the hops taken. When a trailer
  no longer fits, the oldest entries are dropped and the trailer keeps the
  identity of the most recent hops only.
- **[agreed]** The entry count is always the number of entries present,
  whether or not any were dropped. The trailer is 1 byte plus 3 for each
  entry, so a frame can be taken apart without knowing its length from the
  link. The hops taken are the hop limit of the header minus the hops
  remaining, and the trace is truncated when the entry count is less than
  that.
- **[proposed]** A source writes a control byte with the hops remaining
  equal to its hop limit and every other bit 0.
- **[proposed]** A frame is invalid if the hops remaining are more than the
  hop limit, or the entry count is more than the hops taken.
- **[proposed]** With 3 bits of hops remaining, the hop limit is at most 7.
- **[proposed]** A relay copies the reserved bit, and a receiver ignores
  it.
- **[agreed]** A station sets the first bit when it transmits on radio a
  PDU that it received over a path that is not radio. **[proposed]** It
  acts as a relay in doing so and adds its entry. No station clears the
  bit.
- **[agreed]** A gateway that carries a PDU from radio to the Internet does
  not touch the frame. What it knows about the reception belongs to
  gateway provenance (8.3).

Relaying, all **[proposed]**:

- A relay forwards a PDU only if the checksum is good, the trailer is
  valid, at least one hop remains, and its own hash is not among the
  entries. The last condition is a second guard against loops,
  after deduplication.
- To forward, it appends its entry, lowers the hops remaining by one and
  recomputes the checksum. It changes nothing before the trailer.
- If the frame with the new entry would exceed the MTU of 6.1, the relay
  first drops entries from the front of the trace, oldest first, and only
  as many as are needed. It MUST NOT drop entries for any other reason.
- A source that sets a hop limit above 0 MUST leave room for one entry:
  the size of the PDU as sent plus 3 bytes MUST NOT exceed the MTU of 6.1.
  It SHOULD leave room for the whole path, 3 bytes for each hop of its
  limit, which is 21 bytes at a limit of 7. Any relay on
  the path can then always forward, and none has to truncate.
- The limit on the uncompressed form already counts the whole path (5.5).
  How that rule and the two rules above fit together is to be reviewed.

Properties to keep in mind:

- The checksum is recomputed at every hop, so it shows that a frame arrived
  as the last transmitter sent it, and not that it is what the source
  wrote. A relay that damages a PDU in its own memory, between checking it
  and sending it on, sends the damage out under a good checksum. AX.25
  digipeating has the same property: a digipeater changes the address field
  and so recomputes the frame check sequence. Only authentication
  (section 10) covers a PDU from end to end.
- The trailer is outside authentication, and a CRC is not authentication.
  Anyone can forge or delete entries, so the trace is diagnostic
  information and never a basis for trust. Raising the hops remaining or
  deleting entries lets a PDU travel further than its source intended;
  deduplication on `(source, sequence number)` limits the effect. In a PDU
  that is not authenticated the same holds for the hop limit and for
  everything else.
- The hop limit stays in the header although relays decide on the hops
  remaining. In the header it is covered by the source's signature or MAC
  (section 10), so in an authenticated PDU a changed hop limit is found
  when the PDU is verified. Because hops remaining above the hop limit are
  invalid, the limit also bounds what tampering with the control byte can
  gain: the hops remaining can be put back up to the source's limit and no
  further. Verification can come after forwarding (10.4), so this exposes
  tampering more than it prevents it. The header's hop limit is also what
  gives the hops taken and shows that a trace was truncated.
- A truncated trace has lost its oldest entries, and with them the relay
  that heard the source directly. What it keeps, the most recent hops, is
  what the loop guard above needs most: a PDU bouncing between neighbours
  finds its last relays still listed.
- In canonical text the trace is written as the hash values, not as
  resolved callsigns. Resolution belongs to the display. The same PDU
  therefore has a different text form after each hop, differing only in
  the trace.

Dropped:

- Two checksums: one written by the source over its own part and never
  changed, and a second over the trailer, recomputed by relays. It kept an
  end-to-end check on the content and let a station use a PDU whose trailer
  alone was damaged. Dropped by the author in favour of a single checksum:
  4 bytes less on every relayed frame, and one rule for what the checksum
  covers.
- A trailer that exists only once a PDU has been relayed, and so always
  has at least one entry. It saved the 4 bytes of a second checksum on
  frames that were never relayed. With one checksum it saves one byte, and
  costs a dependence on the link for the length of the frame, to tell a
  frame with a trailer from one without.
- Taking the hop limit out of the header once every frame had a control
  byte, since relays only need the hops remaining. Kept, for the reasons
  above.
- A second TLV area for what relays add. It would cost one more byte for
  each hop, and nothing but the trace is added in transit.
- A copy of the hop limit in the control byte. The same value in two
  places needed a rule for when they differ.
- Four bits of hops remaining with four reserved bits, and the number of
  entries derived as the hop limit minus the hops remaining. It could not
  express a truncated trace, so a source had to reserve room for every hop
  of its limit or the PDU could not be relayed that far.

**[open]** The use of the reserved bit. One candidate, not adopted, is a
flag set when the PDU has passed between radio links of different kinds,
for example from a LoRa channel to a 1200 baud one.

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

### 5.10 Versions

- **[agreed]** The protocol has a major version and a minor version. Two
  implementations have the same version when both numbers are the same.
- **[agreed]** The protocol guarantees backward compatibility only inside
  one major version.
- **[agreed]** Therefore a major version does not get a new compressed
  field format.
- **[agreed]** A change that adds no compressed field format and breaks no
  compatibility needs only a new minor version.
- **[agreed]** A new compressed field format is one of these, and each
  needs a new major version:
  - a new compressed form, such as a new codec or a new preset;
  - a new TLV that holds a compressed field.
- **[agreed]** Inside one major version, a receiver can decode every PDU.
  It skips a TLV that it does not know (5.2), and it builds the same
  uncompressed form as every other receiver (5.4).
- **[agreed]** A change breaks compatibility if it has one of these
  effects. As a result, existing stations, relays and gateways can no
  longer reasonably interoperate with the changed ones:
  - it changes how an existing station, relay or gateway reads the value
    of a field;
  - it clearly changes what a station, a relay or a gateway does with
    data that it receives.
- **[agreed]** The test is a receiver of an earlier minor version that
  gets a PDU that is valid after the change. The change breaks
  compatibility if that receiver does one of these:
  - it rejects the PDU or one of its fields;
  - it reads a different value from a field that it knows;
  - it acts differently on the PDU: relay, deduplication, authentication
    or acknowledgement;
  - it builds a different uncompressed form (5.4).
- **[agreed]** The same test applies in the other direction: a receiver
  of the later minor version that gets a PDU of the earlier one.
- **[agreed]** These changes do not break compatibility:
  - a new TLV that holds no compressed field and that an earlier receiver
    can skip, if the other fields keep their meaning without it;
  - a new value in a list that the specification leaves open, if it is not
    a new compressed field format.
- **[agreed]** The header carries the major version and the minor version.
  The version marker of the text form follows the header (5.4).
- **[agreed]** The two numbers share the version byte, which is the first
  byte of the PDU (5.1). From the most significant bit down, the byte has
  the major version in 3 bits, the minor version in 4 bits, and one bit
  that is always 1.
- A comparison of two version bytes as numbers gives the order of the
  versions.

An earlier proposal gave each number 4 bits. It was in conflict with the
first-byte rule of 5.1: with the version in the first byte, the minor
version could only be odd. The author replaced it. The minor version has
the larger field, because a new TLV needs only a new minor version, so
this number grows faster.

The specification can fix the compressed field formats, because few fields
need compression. In practice these are the strings and the bitmap. The
other fields are compact binary encodings of data.

### 5.11 PDU types

- **[agreed]** One PDU has one type. The header gives the type (5.1). A
  PDU does not mix the content of two types.
- **[agreed]** Each type has its own tag space (5.2). A later extension
  can then add a TLV to one type and not change another type.
- **[agreed]** The definition of a type is its schema: the list of the
  TLVs that a PDU of the type can hold.
- **[agreed]** A subgroup is a set of TLVs that stations often send
  together, for example the coordinates and the altitude. The
  specification defines a subgroup once. The schema of a type includes a
  subgroup by reference.
- **[agreed]** The schema of a type can include the position subgroup, if
  the content of the type belongs to a place. A weather PDU is an example.
- **[agreed]** A subgroup is a logical unit of the specification. It has
  no effect on the wire format: a PDU has no mark for a subgroup, and a
  decoder reads the TLVs of a subgroup as it reads every other TLV.
- **[agreed]** Each schema states the tags of the TLVs of a subgroup that
  it includes. The tags of one subgroup can therefore differ between two
  types.
- **[proposed]** The type field is one byte.
- **[proposed]** The types are these:

  | Type | Content | Sent | Legacy APRS use |
  |---|---|---|---|
  | Position | Coordinates, altitude, course, speed. | When the station moves. | Position report, Mic-E, compressed position |
  | Station information | Symbol (5.6), comment or status text (5.7), frequency, software. | Seldom. | Comment, status report, frequency specification |
  | Weather | Weather values, in the units of 5.3. The position subgroup. | At a fixed interval. | Weather report |
  | Telemetry | Values that describe themselves (5.3). | At a fixed interval. | Telemetry report and its definition packets |
  | Message | Addressee, message identifier, text, acknowledgement, segment (6.5). | On an event. | Message, bulletin |
  | Identity and keys | The content of section 10. | Seldom. | None |

- **[proposed]** A receiver keeps, for each station, the most recent PDU
  of each type. A new PDU of a type replaces the earlier PDU of that type
  as a whole. A TLV that the new PDU does not have has no value.
- **[proposed]** A relay forwards a PDU of a type that it does not know.
  The header is the same for every type. The text form of such a PDU has
  the number of the type, and each TLV as a tag and hexadecimal digits
  (5.4).
- **[proposed]** A new type needs only a new minor version (5.10).
- The packet class of 6.3 and of the trunk filters of 8.2 is the type.
- **[agreed]** An object is not a type. The object name is a subgroup
  that the schema of a type can include. If a PDU has an object name, its
  content describes that object. If it has none, its content describes the
  source.
- **[agreed]** The Object and the Item of APRS are one thing here: a PDU
  with an object name. The position of a repeater is a position PDU with
  the name of the repeater. Its frequency is a station information PDU
  with the same name.
- **[proposed]** A receiver keeps the most recent PDU of each type for
  each object of a source, as it does for the source itself.
- **[open]** Which types include the object name, and how a source states
  that an object no longer exists.

An object as a type of its own was not adopted. Its schema would hold a
position, a text and weather data together, which is the mix that a type
prevents.

Why a PDU has one type:

- Content with different rates does not travel together. A position
  changes when the station moves. A comment, a frequency and a symbol
  almost never change. In APRS, a comment is part of each position
  report, so a station sends it again each time. 5.7 has the same
  observation.
- An absent field has one meaning. In a PDU that can hold any mix of
  fields, a position with no comment can mean that the comment did not
  change, or that the station removed it. With types, the rule above
  decides.
- The core position report of goal G4 has a size limit. A PDU that can
  hold any TLV has none.
- A rule for one kind of traffic reads one field: a trunk filter, a
  recommended size, or a rule that only verified sources send messages
  (10.4).

A cost is that a station sends more PDUs. Each PDU has the 19 bytes of
5.1, and a preamble and a channel access on air. The measurement of
section 15, step 11 gives how often stations send the same comment again.

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
- The uncompressed form of the PDU also fits the limit (5.7).
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
  alter a PDU. The only part of a frame a relay changes is the trailer that
  holds the hop trace (5.9).
- A change of the form of a compressed field alters the PDU (5.5).
- **[agreed]** Access links never fragment. On a half-duplex broadcast channel
  one lost fragment loses the packet, there is no retransmission, and every
  receiver must hold reassembly state.
- **[agreed]** The deduplication key is `(source, sequence number)`, not a
  hash of the frame bytes, because the hop trace grows in transit.
- **[agreed]** A relay or a receiver keeps a deduplication entry for a
  limited time. A sequence number can occur again (5.1). **[open]** The
  length of that time.
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
- The uncompressed form fits the limit (5.7), so compression does not
  change whether the sender segments content.
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
- **[agreed]** Gateway provenance is not part of the PDU. A gateway does
  not change a PDU (6.2). The provenance travels next to the PDU, in the
  envelope of the link that carries the PDU between gateways (7.3, 8.2).
- **[open]** The format of that envelope.

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
- **Signature coverage.** Signatures and MACs cover the content of
  everything the source wrote: the header and all TLVs, in the uncompressed
  form of the PDU (5.5). They do not cover the choice of compressed form.
  The hop trace follows the authentication tag and is not covered (5.9).
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
2. More than one valid encoding of the same content, other than the field
   compression of 5.2.
3. Binary floating point on the wire.
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
29. A requirement that a format hold every packet of the protocol it
    replaces without loss. The format then has to keep the obsolete designs
    of that protocol.
30. A canonical encoding that a decoder enforces by running the encoder.
    It is too strict, and it makes the rules too complex.
31. Compression used to send content that does not fit the size limit in
    its uncompressed form.
32. Two units for one quantity. One value then has two encodings.
33. A unit chosen for agreement with the SI where another unit is the
    practical one.
34. A special value of a number used as an error code.
35. One fact in two places of a packet, such as a second copy of the hop
    limit (5.9). A rule is then necessary for the case that the two
    differ.
36. Content with different rates in one packet. The station then sends
    the part that does not change again with each part that does.
37. A packet in which an absent field can mean "not changed" or
    "removed".

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
| Repetition of free text, and its size under each Unishox2 preset | `qua-legacy-text` |

### 13.3 Observations

These are the qualitative results the design relies on. They held in the
runs made so far and are to be re-checked against a current run before
anything is decided on them.

- Most comments and status texts are equal to the text before from the
  same station. To send a text only when it changes saves more than to
  compress it (`docs/research/01-free-text.md`).
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

1. TLV container: the size of the tag space, whether tag bits tell a
   receiver what to do with an unknown TLV, and the tag table of each
   PDU type (5.2, 5.11).
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
   challenge, and the chain rollover construction (10.4, 10.6). Also of a
   signature or a MAC over the uncompressed form instead of the bytes as
   sent (5.5). Also of replay protection: the sequence number has 16 bits
   and starts at a random value (5.1), so 10.4 cannot rely on it alone.
8. The format and distribution of infrastructure attestations (10.5).
9. Area identifiers: how they are assigned and by whom (8.2).
10. Migration: a translation between legacy APRS and QUA Network at a
    gateway can lose information (3.2). Which kinds of legacy packet does a
    gateway translate? What does it do with a legacy packet that has no QUA
    Network form? Who is the source of a translated PDU, and who issues
    its sequence number (6.5)? A translated PDU has the flag Translated of
    5.1.
    How does a gateway round a value, and how much loss is reasonable
    (5.3)? `docs/interop/` holds the work on the translation.
11. Message reliability: acknowledgement, retry policy and segment
    retransmission.
12. Regional variation in traffic mix, and whether the MTU decision should
    follow the worst region.
13. Packed format for high-speed trunks (8.2). Deferred.
14. Recommended sizes per packet class (6.3).
15. The byte limit of the Unicode symbol form, proposed as 8 (5.6).
16. Unishox2 (5.7):
    - Which preset: `USX_PSET_DFLT` or `USX_PSET_NO_DICT`? The author
      narrowed the choice to these two. One preset for every string is
      proposed (5.7).
    - Which parts of the Unishox2 format does the specification make
      invalid, if any? `docs/research/02-unishox2-reading.md` lists the
      parts.
    - How is the decoder specified independently of the reference
      implementation? Does a reduced implementation with only the allowed
      presets replace the reference implementation?
    - Which malformed compressed strings does a decoder reject? What does
      it do when the length byte gives a wrong length?
    - How does a text field mark its form and its preset, and is the
      preset number part of the length byte? A preset number there leaves
      fewer bits for the length.
    - What does a receiver do with a PDU whose uncompressed form does not
      fit the PDU limit?
17. Use of the unused identifier values: the all-zero identifier, and
    37^12 up to 2^63 in the low 63 bits. Also whether the SSID positions
    use base 36 so that no SSID pattern needs rejecting (5.8).
18. In the optional AX.25 encapsulation, what the address fields hold,
    especially for an identifier that does not fit an AX.25 address (5.8,
    7.2).
19. Hop trace details: the use of the reserved bit of the control byte,
    and how the trailer, including a truncated one, appears in canonical
    text (5.9).
20. Whether identification through the PDU source alone satisfies local
    regulations where QUA Network is deployed.
21. The icon TLV: the order of its fields and how often it is repeated
    (5.6).
22. The final name ("QUA Network" is a working name), its check against
    existing trademarks, and the rule for its use by modified versions of
    the specification (11).
23. Versions (5.10):
    - What does a receiver do with a PDU of a major version that it does
      not know?
    - Under the test of 5.10, a value that a decoder rejects today cannot
      get a meaning in a later minor version. Which values does the
      specification reserve as "ignore" instead? This waits for the
      definition of the formats.
    - The version byte holds 8 major versions and 16 minor versions. What
      happens when one of the two fields is full?
24. Decimal number and units (5.3):
    - The rule against a multiple of 10 removes the digit count as a
      statement of resolution. Is that correct, given the precision item
      of 5.3?
    - Which other fields are decimal numbers? Altitude and speed are
      agreed. The weather values are candidates.
    - Which fields allow an infinity?
    - A TLV holds one decimal number at most, and no number has a code
      for an absent value. How does a telemetry TLV hold several values,
      and how does it show that one value is absent?
    - What states the unit of a telemetry value: the tag, or a unit code
      in the value? This belongs with the tag table (question 1).
    - Which other quantities get a practical unit? Dose rate, electric
      charge and capacitance are candidates.
    - The record of `docs/interop/` gives speed in metres per second,
      temperature in kelvin and pressure in pascals. The record is not a
      wire format, so the units can differ. Does the record change to the
      units of 5.3?
25. Header (5.1):
    - The positions of the flags in the second byte, and the use of the
      two reserved bits.
    - How a receiver finds the end of the TLV area in a PDU that has an
      authentication tag.
    - The exact rule for the flag No Internet: which stations obey it,
      and whether it also applies to a trunk (8.2).
    - How long a relay or a receiver keeps a deduplication entry (6.2).
26. The envelope that carries gateway provenance next to a PDU (8.3).
27. PDU types (5.11):
    - The list of types and the schema of each.
    - The list of subgroups.
    - Which types include the object name, and how a source states that
      an object no longer exists.
    - Are the comment and the status text one field or two?
    - Is a bulletin a message to a group?
    - Do the station capabilities and the queries of APRS get a form?
    - Which type numbers are for experiments?
    - The interval of each type, with the airtime budget of 6.3.

## 15. Next steps

1. Fix the origin classification (`qAr`; exclude `TCPIP` paths explicitly).
2. Extract packets above 255 bytes and all `{` packets; identify senders and
   PHY.
3. Separate LoRa traffic by destination tocall.
4. Divide the corpus into fields, taking APRS12c (Appendix D) as the
   reference for intended meaning. One purpose is to learn which fields
   occur in the corpus and how large their values are. The other is to
   list where APRS12c fails, for the divergence catalogue (Appendix E).
   The purpose is not to define a record that holds every legacy packet
   (3.2).

   The reading of APRS12c that the parser follows is written down first,
   in `docs/legacy/`. Then a strict tokenizer records every field's
   position on the raw bytes, and a field inventory counts presence, sizes
   and co-occurrence as input to the TLV tag table (5.2). Record the true
   parse-failure rate and the distribution of comment length.

   A decoder on the tokens then gives the values of the fields.
   `docs/legacy/10-values.md` states the values, and `docs/interop/`
   specifies the record that the decoder gives.
5. Train a zstd dictionary on the corpus and record per-packet compressed
   size as an approximate lower bound for any candidate encoding.
6. Draft the header and TLV tag table. Re-encode the corpus. Report, per
   candidate: the length distribution per packet class and the resulting
   airtime per PHY. The re-encoding can drop legacy content that has no
   QUA Network field (3.2). It measures size and airtime only. The header
   fields are in 5.1, and the PDU types are in 5.11. The schema and the
   tag table of each type are the part that remains.
7. Dropped. An earlier revision listed a check of a semantic round trip
   here: APRS to semantic record to QUA Network to semantic record, with
   equal records. The author dropped the check. It tested a goal that QUA
   Network does not have: to record legacy packet content without loss
   (3.2). The round trip that the specification requires is inside its own
   format (5.4, 5.5), and step 8 covers it. The number stays so that step
   numbers do not change.
8. Publish the canonical text grammar and the first test vectors,
   including vectors with a compressed field (5.5).
9. Consider publishing the raw corpus.
10. Build the divergence catalogue by differential testing of existing
    parsers against the corpus (Appendix E).
11. Run Unishox2 over the free-text fields extracted from the corpus,
    once per candidate preset: bytes saved per packet, the share of strings
    that fall back to passthrough, and the result by script (Latin, CJK,
    Cyrillic and others). Record the best preset for each string, and
    compare the total with per-string selection against the total with the
    single best preset. Also measure how often a station repeats its
    previous comment unchanged. Done for one capture window:
    `docs/research/01-free-text.md`.
12. Test the native HDLC binding on real equipment: send frames whose first
    byte has the low bit set through Dire Wolf and through hardware KISS
    TNCs, and confirm that they are transmitted and received intact, and
    that legacy APRS software on the channel ignores them.
13. Extend the icon measurement of 5.6 to the APRS symbol table drawn at
    16 by 16.
14. Study a reduced Unishox2 implementation that has only the presets that
    QUA Network can use (5.7; section 14, question 16).
15. When the formats of the decimal number of 5.3 are settled, move it
    to `docs/spec/` and write test vectors. Include encodings that a
    decoder rejects (section 14, question 24).
16. List the quantities that the protocol carries, each with its unit
    (5.3). This goes with the tag table of step 6.

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
- `qua-icon-encode`: encodes a 16 by 16 picture as an icon bitmap field,
  and produces the icon bitmap vectors by a path independent of the
  encoder that `qua-check-vectors` checks.
- `qua-spec-extract`: extracts the reference PDFs of Appendix D to
  Markdown for reading and search, keeping what their typography means
  (Courier for literal data, highlight for literal characters, shading for
  optional fields). The output stays under `work/`, because the documents'
  terms do not allow their text into this repository.
- `qua-legacy-tokenize`: shows how the strict legacy tokenizer reads
  packets, following the reading in `docs/legacy/`: tokens with their byte
  offsets, findings and verdict.
- `qua-legacy-fields`: field inventory over the corpus under that reading:
  per rule, the packets carrying it, token count, byte length
  distribution and bytes outside 7-bit ASCII; verdicts and findings with
  example packets. Every file of `docs/legacy/` has a reader, so every
  packet gets a verdict.
- `qua-legacy-decode`: gives the record of `docs/interop/` for each packet,
  or counts of the fields over the corpus.
- `qua-legacy-compare`: compares the records with the results of other
  parsers, for the divergence catalogue (Appendix E).
- `qua-legacy-text`: measures the free text of the corpus: how often a
  station sends the same text again, and the size of each text under each
  preset of Unishox2 (section 15, step 11).
- `qua-legacy-examples`: collects the example packets of APRS12c from
  the working copy under `work/` and checks the verdict of each against
  a project-owned expectation list, which names the examples by page and
  digest and does not hold their bytes.

## Appendix D. Reference documents

The APRS Documentation Project, maintained by WB2OSZ (the author of Dire
Wolf): <https://github.com/wb2osz/aprsspec>

| Document | Use for QUA Network |
|---|---|
| `APRS12c.pdf` | Unofficial compilation of the 1.0.1 reference and the updates since 2000. The working reference for what existing packets are meant to say. Draft, with known issues. |
| `APRS101.pdf` | Since aprsspec commit `029684a` a one-page notice that 1.0.1 is obsolete, not the reference itself. The original 1.0.1 (TAPR, 29 August 2000, 128 pages) is linked below; it shows which defects of APRS12c are inherited from it. |
| `Understanding-APRS-Packets.pdf` | Explains real packets and lists common mistakes. A starting list for the divergence catalogue. |
| `APRS-Digipeater-Algorithm.pdf` | A written digipeater algorithm, filling a gap the original working group left. Input to section 8.1. |
| `Minimizing-APRS-Collisions.pdf` | Input to section 9. |
| `APRS-Symbols.pdf` | Symbol table with on-air encoding. Defines the symbols that the classic form numbers (5.6). |
| `APRS-Information-Services.pdf` | Input to gateway and service design. |

Also referenced there: the AX.25 2.2 specification, the 1.1 addendum and the
1.2 proposal pages on aprs.org, and an IGate operation guide in the Dire Wolf
documentation.

The original APRS 1.0.1 reference is not in the repository. It is linked,
with the hash of the copy consulted, in the
[documentation index](../README.md#external-references).

Local Markdown copies of these PDFs and of the AX.25 2.2 specification are
made with `qua-spec-extract` (Appendix C). They are working copies for
search; the PDF stays the reference, and a citation gives its page.

APRS12c leaves many points open and contradicts itself in places. How this
project reads it, field by field, including every point where it had to
choose and the errors it found in the document, is recorded in
[`docs/legacy/`](../legacy/README.md).

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
2. Normalise each parser's output into one common record, so that the
   outputs can be compared. This record exists only for the comparison. It
   is not a QUA Network format. A draft of it is in `docs/interop/`.
3. Compare. Every packet on which parsers disagree, or which some accept and
   others reject, becomes a catalogue entry.
4. Read the relevant code to find the cause, and record it.

The reading in `docs/legacy/` lists the places where APRS12c is silent,
ambiguous or contradicts itself, without recording what decoders do there.
An earlier draft of it noted, for each such place, what several of these
decoders do as read in their source; those notes remain in the repository
history (`docs/legacy/README.md` section 4 gives the commit). They are a
starting point for step 4, not a substitute for steps 1 to 3: they show
what the code does, not how often it matters.

This finds the differences that occur in real traffic and attaches a
frequency to each, so they can be ranked. Reading code alone finds many
theoretical differences without showing which ones matter.

### E.2 Categories

| Category | Meaning for QUA Network |
|---|---|
| Violates the specification but is common on air | Gateways translating legacy traffic must tolerate it. |
| Not defined by the specification | If QUA Network keeps this use, its specification defines it explicitly. |
| Ambiguous, and implementations read it differently | If QUA Network keeps this use, its definition has one reading only. |
| De facto extension outside the specification | Decide whether to adopt it as a registered TLV. |

### E.3 Entry format

Each entry records: a short description, the category, example packets from
the corpus, frequency in the corpus, how each parser behaves, the relevant
specification text if any, and the decision taken for QUA Network.

The catalogue is in `docs/legacy/divergence/`, one file per entry. The
comparison that finds the entries is specified in
`docs/interop/09-comparison.md`.

### E.4 Handling third-party code

Implementations are referenced, not copied. Use git submodules or record the
repository and commit hash, so that each observation is tied to a specific
version and licences (several are GPL) stay separate from this project.
