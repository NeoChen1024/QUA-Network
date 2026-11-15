# SPDX-License-Identifier: Apache-2.0
"""CRC-32C (Castagnoli), with the parameters of docs/spec/08-pdu.md. It is the checksum
of a PDU and the function of the hop trace entries (RFC 5.9)."""


def crc32c(data):
    """The CRC-32C of data, bit by bit. Short inputs only: it is not fast."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF
