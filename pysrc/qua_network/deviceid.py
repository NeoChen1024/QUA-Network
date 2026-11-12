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

import yaml

MIC_E_TYPES = frozenset({b"`", b"'"})
_WILDCARD = {"?": ".", "n": "[0-9]", "*": ".*"}


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
