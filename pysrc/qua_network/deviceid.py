# SPDX-License-Identifier: Apache-2.0
"""Device identification from the destination callsign (tocall).

Uses the aprs-deviceid database (3rdparty/aprs-deviceid/tocalls.yaml) and
its documented lookup: an exact match first, then the wildcard entry with
the longest literal match. In a pattern, '?' is any character, lower-case
'n' is a digit and '*' is any remainder.

Mic-E packets carry position in the destination field and cannot be looked
up this way.
"""

import re
from functools import cache
from pathlib import Path

import yaml

MIC_E_TYPES = frozenset({b"`", b"'"})
_WILDCARD = {"?": ".", "n": "[0-9]", "*": ".*"}

# The register of the submodule, at the commit the repository pins, located
# from the package so that it is found whatever the working directory.
PINNED = Path(__file__).resolve().parents[2] / "3rdparty" / "aprs-deviceid" / "tocalls.yaml"


@cache
def pinned_register():
    """The parsed register at PINNED, read once per process."""
    try:
        with open(PINNED, "rb") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        raise RuntimeError(
            f"aprs-deviceid register not found at {PINNED}; the legacy tokenizer reads the"
            " Mic-E device suffixes and the dest.tocall identifiers from it (docs/legacy/README.md"
            " section 3). Check out the submodule: git submodule update --init 3rdparty/aprs-deviceid"
        ) from None


@cache
def pinned_index():
    """A DeviceIndex of the tocalls of the pinned register."""
    return DeviceIndex(pinned_register()["tocalls"])


class DeviceIndex:
    def __init__(self, entries):
        self._exact = {}
        wild = []
        for entry in entries:
            pattern = str(entry["tocall"])
            literals = sum(c not in _WILDCARD for c in pattern)
            if literals == len(pattern):
                self._exact[pattern] = entry
            else:
                regex = re.compile("".join(_WILDCARD.get(c) or re.escape(c) for c in pattern))
                wild.append((literals, regex, entry))
        wild.sort(key=lambda w: -w[0])
        self._wild = [(regex, entry) for _, regex, entry in wild]
        self._cache = {}

    @classmethod
    def load(cls, path):
        with open(path, "rb") as fh:
            return cls(yaml.safe_load(fh)["tocalls"])

    def lookup(self, tocall):
        """Database entry for a destination callsign without SSID, or None."""
        try:
            return self._cache[tocall]
        except KeyError:
            entry = self._exact.get(tocall)
            if entry is None:
                entry = next((e for regex, e in self._wild if regex.fullmatch(tocall)), None)
            self._cache[tocall] = entry
            return entry
