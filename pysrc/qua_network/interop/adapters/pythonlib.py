# SPDX-License-Identifier: Apache-2.0
"""Adapter for the parser `pythonlib` of docs/interop/09-comparison.md.

The parser is the Python package aprslib of the submodule
3rdparty/aprs-python. This program runs as a process of its own. It calls
the public function `parse` of the package and copies no code of it.

Usage: pythonlib.py LIBDIR

Standard input has one packet per line, as the hexadecimal digits of the
bytes of its TNC2 line. Standard output has one JSON object per packet:
the dictionary that `parse` returns without `raw`, or `error` and
`message` if `parse` raises an exception.
"""
import json
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, sys.argv[1])

import aprslib  # noqa: E402


def main():
    out = sys.stdout
    for digits in sys.stdin:
        # Each byte becomes the character with its number, so that a text
        # of the result gives the bytes of the packet back.
        line = bytes.fromhex(digits.strip()).decode("latin-1")
        try:
            result = aprslib.parse(line)
            result.pop("raw", None)
        except (aprslib.ParseError, aprslib.UnknownFormat) as e:
            result = {"error": type(e).__name__, "message": str(e.args[0]) if e.args else ""}
        except Exception as e:  # a defect of the parser, not of the packet
            result = {"error": "crash", "message": f"{type(e).__name__}: {e}"}
        out.write(json.dumps(result, default=repr) + "\n")


if __name__ == "__main__":
    main()
