# SPDX-License-Identifier: Apache-2.0
"""Tokenize one TNC2 line under the reading of docs/legacy/."""

from qua_network.legacy.frame import header, info_field
from qua_network.legacy.message import read as read_message
from qua_network.legacy.mice import read as read_mice
from qua_network.legacy.model import Scan
from qua_network.legacy.objects import read as read_objects
from qua_network.legacy.position import read as read_position
from qua_network.legacy.weather import read as read_weather

# Format readers by the docs/legacy file that specifies them. A format with
# no reader yet leaves its field after byte 0 as residue, and the packet
# has no verdict (Scan.unread).
READERS = {
    "03-position": read_position,
    "04-mic-e": read_mice,
    "05-object-item": read_objects,
    "06-weather": read_weather,
    "08-message": read_message,
}


def tokenize(line, readers=READERS):
    """Return the Scan of one raw TNC2 line (bytes, no line terminator)."""
    scan = Scan(line)
    sep = line.find(b":")
    if sep < 0:
        scan.residue(0, len(line), 0, "line.sep")
        scan.find("line.sep", "syntax", len(line))
        scan.unknown_format = True
        return scan
    dti = line[sep + 1] if sep + 1 < len(line) else -1
    header(scan, sep, dti)
    scan.tok("line.sep", sep, sep + 1)
    info_field(scan, sep + 1, len(line), 0, readers)
    return scan


def show_bytes(b):
    """Printable ASCII as is, everything else as \\xNN."""
    return "".join(chr(c) if 0x20 <= c < 0x7F and c != 0x5C else "\\\\" if c == 0x5C else f"\\x{c:02x}" for c in b)
