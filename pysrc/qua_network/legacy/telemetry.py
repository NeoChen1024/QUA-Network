# SPDX-License-Identifier: Apache-2.0
"""Base-91 comment telemetry: docs/legacy/07-telemetry.md section 3.

The telemetry report and the definition messages of 07 have no reader yet;
only the block found inside a comment is read here, for the formats whose
comments 07 names.
"""

import re

# A run between two bars; base-91 digits exclude '|', so runs are delimited
# by consecutive bars. The lookahead finds runs that share a bar.
_RUN = re.compile(rb"(?=\|([!-{]*)\|)")


def b91_block(scan, s, e, depth, daos):
    """Tokenize the tlm.b91 block of the comment line[s:e], if there is one.

    daos are the cmt.dao candidates of the comment, as (offset, kind). A
    run is a block only when nothing follows it but an optional DAO
    candidate (amb.tlm.b91.order). Returns (start, end) of the block or None.
    """
    line = scan.line
    dao_at = {i for i, _ in daos}
    for m in _RUN.finditer(line, s, e):
        n = len(m.group(1))
        if n % 2 or not 4 <= n <= 14:
            continue
        bs = m.start()
        be = bs + n + 2
        if not (be == e or (be + 5 == e and be in dao_at)):
            continue
        scan.tok("tlm.b91", bs, be, depth)
        d = depth + 1
        for k in range(n // 2):
            rule = "tlm.b91.seq" if k == 0 else "tlm.b91.bits" if k == 6 else "tlm.b91.analog"
            p = bs + 1 + 2 * k
            scan.tok(rule, p, p + 2, d)
        return bs, be
    return None
