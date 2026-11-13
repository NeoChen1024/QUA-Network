# SPDX-License-Identifier: Apache-2.0
"""Tokens, findings and verdicts (docs/legacy/README.md section 3)."""

from typing import NamedTuple

KINDS = ("syntax", "value", "ambiguous", "obsolete", "discouraged", "is-only", "unstated")

# Increasing severity. "unknown-format" is set directly, not derived from a kind.
VERDICTS = ("conform", "conform-ambiguous", "value", "syntax", "unknown-format")
_KIND_VERDICT = {"ambiguous": 1, "value": 2, "syntax": 3}

# Name of the rule in a residue token whose format has no reader yet. It is
# not a rule of the reading: such a packet has no verdict yet.
UNREAD = "unread"


class Token(NamedTuple):
    rule: str
    start: int
    end: int
    depth: int
    # For a residue token: the rule at which parsing stopped.
    stop: str | None = None


class Finding(NamedTuple):
    rule: str
    kind: str
    offset: int


class Scan:
    """What the tokenizer found in one line."""

    __slots__ = ("line", "tokens", "findings", "_seen", "_missing", "unknown_format", "unread")

    def __init__(self, line):
        self.line = line
        self.tokens = []
        self.findings = []
        self._seen = set()
        # Offsets where a missing field has given its syntax finding.
        self._missing = set()
        self.unknown_format = False
        # Formats whose reader is not written yet; the packet has no verdict.
        self.unread = []

    def tok(self, rule, start, end, depth=0, stop=None):
        self.tokens.append(Token(rule, start, end, depth, stop))

    def find(self, rule, kind, offset):
        # Identical findings are given once (README section 3).
        f = Finding(rule, kind, offset)
        if f not in self._seen:
            self._seen.add(f)
            self.findings.append(f)

    def missing(self, rule, offset):
        """A required field is missing at offset: syntax where it was
        expected. Only the first of consecutive missing fields that fail at
        one byte gives it (README section 3, Missing fields at one byte)."""
        if offset not in self._missing:
            self._missing.add(offset)
            self.find(rule, "syntax", offset)

    def withdraw(self, kind, offsets):
        """Take back the findings of kind at offsets, where a rule already
        reports those bytes (README section 3, Precedence). They stay seen, so
        a later identical finding is not given either."""
        if offsets:
            self.findings = [f for f in self.findings if f.kind != kind or f.offset not in offsets]

    def retag(self, start, depth, rule):
        """Give the identifier token at (start, depth) the rule of the format
        the packet is classified as (README section 3)."""
        for i, t in enumerate(self.tokens):
            if t.start == start and t.depth == depth and t.end == start + 1:
                self.tokens[i] = t._replace(rule=rule)
                return

    def residue(self, start, end, depth, stop, fault=False):
        """A residue token naming stop. fault gives its syntax finding at
        start, on stop, unless a missing field already gave one at that byte
        (README section 3, Missing fields at one byte)."""
        if end > start:
            self.tok("residue", start, end, depth, stop)
            if fault and start not in self._missing:
                self.find(stop, "syntax", start)

    def verdict(self):
        """The verdict, or None while some format of the packet is unread."""
        if self.unknown_format:
            return VERDICTS[4]
        if self.unread:
            return None
        worst = 0
        for f in self.findings:
            worst = max(worst, _KIND_VERDICT.get(f.kind, 0))
        return VERDICTS[worst]

    def check_cover(self):
        """True when the depth-0 tokens cover the line exactly, in order."""
        pos = 0
        for t in self.tokens:
            if t.depth:
                continue
            if t.start != pos or t.end < t.start:
                return False
            pos = t.end
        return pos == len(self.line)

    def sorted_tokens(self):
        return sorted(self.tokens, key=lambda t: (t.start, t.depth, -t.end))
