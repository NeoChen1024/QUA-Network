# Interoperation with the legacy network

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[proposed]** and **[open]** with the meaning that the RFC gives them. An **[agreed]** item is a decision of the author. |
| Rationale | [RFC draft 0](../rfc/qua-network-rfc-0.md): section 3.2, section 14 question 10, Appendix E |
| Reading of APRS12c | [docs/legacy](../legacy/README.md), in particular its value files: [10-values.md](../legacy/10-values.md), [11-values-object.md](../legacy/11-values-object.md), [12-values-weather.md](../legacy/12-values-weather.md), [13-values-telemetry.md](../legacy/13-values-telemetry.md), [14-values-status.md](../legacy/14-values-status.md), [15-values-message.md](../legacy/15-values-message.md), [16-values-frequency.md](../legacy/16-values-frequency.md), [17-values-capabilities.md](../legacy/17-values-capabilities.md) |

## 1. Purpose

This directory specifies how this project exchanges content with the
legacy APRS network. It covers these parts:

- the record: what the decoder gives for one legacy packet
  ([01-record.md](01-record.md));
- later, the translation between a record and QUA Network PDUs at a
  gateway;
- later, the encoder from a record to a legacy packet.

**[proposed]** The record has three purposes:

1. Measurement. The record gives the values and the resolution of legacy
   fields in the corpus. These are input to the TLV design (RFC 5.2;
   section 15, steps 4 and 6).
2. Translation at a gateway. The translation can lose information (RFC
   3.2, section 14 question 10).
3. Comparison of parsers. The record is the common record of RFC Appendix
   E.1, step 2. The comparison converts the output of each parser to it.

## 2. What this directory is not

**[proposed]** These statements limit this directory:

- The record is not a QUA Network wire format. RFC 5.10 does not apply to
  it. The rules of RFC 5.3 apply only to the PDUs that a gateway writes.
- The record is not a lossless model of legacy packets (RFC 3.2). It gives
  the values that each use needs. It keeps the TNC2 line, so a reader can
  trace a value to its bytes.
- This directory does not interpret APRS12c. [docs/legacy](../legacy/README.md)
  does, and the decoder follows it.
- The record does not use the units of APRS12c. It gives each quantity in
  a record unit. It is the unit of RFC 5.3, if the RFC names one
  ([01-record section 4.3](01-record.md#43-units)). It does not keep the
  integer counts of docs/legacy. The TNC2 line keeps the bytes.
- The legacy AX.25 frame of the encoder is not the AX.25 encapsulation of
  RFC 7.2. The encapsulation is a binding of QUA Network PDUs.

## 3. Conventions

The status labels have the meaning that the RFC gives them. Only the
author changes a label. The key words MUST, MUST NOT, SHOULD, SHOULD NOT
and MAY are used as in RFC 2119. They occur only in requirements.

These files use the terms of [docs/legacy README section 2](../legacy/README.md#2-conventions)
and of [10-values section 2.1](../legacy/10-values.md#21-terms). They also
use these terms:

| Term | Meaning |
|---|---|
| legacy packet | A packet of the APRS network, as a TNC2 line or as an AX.25 frame. |
| record | The output of the decoder for one legacy packet. |
| use | What a part of a record is for: position, message, bulletin, telemetry, telemetry definition, weather, object, status, capabilities or frequency. A use is not a legacy format. One packet can have more than one use. A record names its uses in `uses`. |
| envelope | The fields that every record has. |
| body | The fields of one use, for example the position body. A record has one body for each use of the packet. |
| the decoder | The tool that makes records. It runs the tokenizer and applies the value files of docs/legacy. |
| strict mode, permissive mode | The two modes of the decoder ([01-record section 3](01-record.md#3-modes)). |
| byte string | Bytes as received. The decoder does not decode them as text. |
| mark | A finding that a value has in permissive mode. |
| value | What a value rule of 10-values gives. A quantity of a record gives it as `v`, in the record unit. For a non-linear code, `v` is the quantity that the formula of 10-values gives, not the code. |
| record unit | The unit of `v` that [01-record section 4.3](01-record.md#43-units) fixes for a field, for example the metre. "Unit" alone is the unit of 10-values. |
| resolution | The difference between a value and the next value that the bytes can give, in the record unit. In a record, it is `res`. For a linear unit, it is the step of 10-values in the record unit. |
| received time | The time at which the receiver got the packet. For a corpus record, it is the logged time. |

## 4. Files

| File | Covers |
|---|---|
| [01-record.md](01-record.md) | The record: envelope, modes, representation of values, the position body, JSON lines, examples. |
| [02-object.md](02-object.md) | The object body, for Objects and Items. |
| [03-weather.md](03-weather.md) | The weather body, for positionless and complete weather reports. |
| [04-telemetry.md](04-telemetry.md) | The telemetry body, for telemetry reports and base-91 blocks, and the telemetry definition body. |
| [05-status.md](05-status.md) | The status body, for status reports. |
| [06-message.md](06-message.md) | The message body, for messages, acknowledgements and rejections, and the bulletin body. |
| [07-frequency.md](07-frequency.md) | The frequency body, for a frequency specification in a comment or a status text. |
| [08-capabilities.md](08-capabilities.md) | The capabilities body, for station capabilities. |

## 5. Open items

This directory defers these items. Each is **[open]**.

- **[agreed]** These formats get no body: queries, user-defined data,
  test data, the Maidenhead locator beacon, the obsolete Object format and
  a packet whose identifier the tokenizer does not recognise. Station
  capabilities have a body ([08-capabilities](08-capabilities.md)).
- **[agreed]** Raw weather reports and raw NMEA sentences get no body
  now. The author decides again after the differential tests.
- The encoder, from a record to a legacy packet. Its output is a TNC2 line,
  as the corpus records it, or an AX.25 frame for a KISS TNC. An encoder
  and a decoder can agree on a round trip. This is not evidence that
  either is correct.
- The gateway mapping between a record and the TLVs of QUA Network (RFC
  5.2, 5.3, 5.6). This mapping depends on section 14 question 10 of the
  RFC.
- Differential tests against existing parsers (RFC Appendix E, section 15
  step 10). The comparison converts each parser output to the record.
- The station identifier of the source. Some legacy addresses have no
  clear QUA Network identifier ([spec 01](../spec/01-station-identifier.md)).
  Examples are `-01` against `-1`, lower case, and addresses that occur
  only on APRS-IS.
