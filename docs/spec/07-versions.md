# Versions

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.10](../rfc/qua-network-rfc-0.md#510-versions) |
| Vectors | None. |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the version numbers of the protocol, the version
byte, the compatibility that the protocol guarantees, and the version
that a change of the specification needs.

It does not specify these:

- The other fields of the header (RFC 5.1).
- The version marker of the text form (RFC 5.4).

## 2. Version numbers

**[agreed]** The protocol has a major version and a minor version. Two
implementations have the same version if both numbers are the same.

**[agreed]** The first version is 1.0: the major version is 1 and the
minor version is 0. It is the version of the first freeze of the
specification.

## 3. Version byte

**[agreed]** The header carries the major version and the minor version.
The two numbers share the version byte. The version byte is the first
byte of the PDU. A receiver reads it before every other field.

**[agreed]** The bits of the version byte, from the most significant
bit:

| Bits | Content |
|---|---|
| 3 | Major version, 0 to 7 |
| 4 | Minor version, 0 to 15 |
| 1 | Always 1 |

A comparison of two version bytes as numbers gives the order of the
versions.

The version byte of version 1.0 is `21`: the bits `001`, `0000` and `1`.

## 4. Compatibility

**[agreed]** The protocol guarantees backward compatibility only inside
one major version.

**[agreed]** Inside one major version, a receiver can decode every PDU.
It skips a TLV that it does not know (RFC 5.2). It builds the same
uncompressed form as every other receiver (RFC 5.4).

## 5. Changes of the specification

**[agreed]** The rules of this section apply from the first freeze of
the specification. Before it, a draft can change without a new version.

### 5.1 A change that breaks compatibility

**[agreed]** A change breaks compatibility if it has one of these
effects:

- It changes how an existing station, relay or gateway reads the value
  of a field.
- It clearly changes what a station, a relay or a gateway does with data
  that it receives.

As a result, existing stations, relays and gateways can no longer
reasonably interoperate with the changed ones.

**[agreed]** The test uses a receiver of an earlier minor version. This
receiver gets a PDU that is valid after the change. The change breaks
compatibility if the receiver does one of these:

- It rejects the PDU or one of its fields.
- It reads a different value from a field that it knows.
- It acts differently on the PDU: relay, deduplication, authentication
  or acknowledgement.
- It builds a different uncompressed form (RFC 5.4).

**[agreed]** The same test applies in the other direction: a receiver of
the later minor version gets a PDU of the earlier one.

**[agreed]** These changes do not break compatibility:

- A new TLV that holds no compressed field and that an earlier receiver
  can skip, if the other fields keep their meaning without it.
- A new value in a list that the specification leaves open, if it is not
  a new compressed field format.

### 5.2 A new compressed field format

**[agreed]** A new compressed field format is one of these:

- A new compressed form, such as a new codec or a new preset.
- A new TLV that holds a compressed field.

**[agreed]** A major version does not get a new compressed field format.

### 5.3 The version that a change needs

**[agreed]** The first row that applies gives the version:

| Change | Version |
|---|---|
| It adds a compressed field format | A new major version |
| It breaks compatibility | A new major version |
| A different change | A new minor version |

## 6. Open items

These are also in the RFC (section 14, question 23).

- **[open]** What a receiver does with a PDU of a major version that it
  does not know.
- **[open]** The values that the specification reserves as "ignore". By
  the test of 5.1, a value that a decoder rejects today cannot get a
  meaning in a later minor version.
- **[open]** What happens when one of the two fields of the version byte
  is full.
- **[open]** The version byte of a PDU that follows a draft, before the
  first freeze.
