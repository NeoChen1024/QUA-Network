# SPDX-License-Identifier: Apache-2.0
"""The decoder of docs/interop/: the record of one legacy packet.

values.py applies the value rules of docs/legacy/10-values.md to the tokens
of the legacy tokenizer; record.py builds the record of
docs/interop/01-record.md from them. The documents lead: where the code
needs a rule that they do not state, the rule goes into the documents
first.
"""

from qua_network.interop.record import MODES, decode

__all__ = ["MODES", "decode"]
