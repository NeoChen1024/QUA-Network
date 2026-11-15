# SPDX-License-Identifier: Apache-2.0
"""The contents of vectors/text-compression.json, for docs/spec/04-text-compression.md.

This is the path independent of the decoder of usx.py, which
qua-check-vectors checks against the file. It does not import usx.py. A
vector comes from one of two sources: the encoder of the Unishox2 library
(3rdparty/Unishox2, through the shim of qua-legacy-text), or bits that this
module writes from sections 3 to 6 of the file, with its own copy of the
table of section 4.

The texts were written for this project. They are not from the corpus.
"""

import ctypes
import json

BUF = 4096

# ---- section 4, typed again from the table of the file
POS = "00 010 011 1000 1001 1010 1011 1100 11010 11011 111000 111001 111010 1110110 1110111 1111000 1111001 1111010".split()
POS += [format(v, "08b") for v in range(0xF6, 0x100)]
LET = {c: POS[i + 1] for i, c in enumerate(" etaoinsrlcdhupmbgwfyvkqjxz")}
DIG = {c: POS[i + 1] for i, c in enumerate(",.01925-/34678() =+$%#")}
P0 = POS[0]
LETTERS, SYMBOLS, DIGITS, REPEAT, UNICODE = "00", "01", "10", "110", "111"


def step(k, limit):
    return "1" * k + ("0" if k < limit else "")


def count(c):
    for row, (bits, base) in enumerate(((2, 0), (4, 4), (7, 20), (11, 148), (16, 2196))):
        if c < base + (1 << bits):
            return step(row, 4) + format(c - base, f"0{bits}b")


def cp(prev, c):
    d = abs(c - prev)
    for k, (bits, base) in enumerate(((6, 0), (12, 64), (14, 4160), (16, 20544), (21, 86080))):
        if d < base + (1 << bits):
            return step(k, 5) + ("1" if c < prev else "0") + format(d - base, f"0{bits}b")


def raw_cp(k, sign, number):
    bits = (6, 12, 14, 16, 21)[k]
    return step(k, 5) + str(sign) + format(number, f"0{bits}b")


def B(bits, pad="0"):
    bits = bits.replace(" ", "")
    left = -len(bits) % 8
    bits += pad * left
    return bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)), left


def byte8(v):
    return format(v, "08b")


def sym_item(q):
    return P0 + SYMBOLS + POS[q]


def dig_item(q):
    return P0 + DIGITS + POS[q]


SHIFT = P0 + LETTERS
RUN_ON = SHIFT + P0 + LETTERS
TO_UNICODE = SHIFT + POS[1]
ONE_CP = P0 + UNICODE
BYTES = dig_item(0) + "11111"
RPT = POS[26]


# ---- valid, from the library encoder
LIB_VALID = [
    "Hello",
    "a",
    " ",
    "QUA Network test",
    "N0CALL-7 mobile, 12.5V 23.4C",
    "Monitoring 145.500 MHz FM",
    "WX STATION ONLINE",
    "testing testing testing",
    "----------",
    "==========================",
    "Grüße aus Köln",
    "température 21°C",
    "Привет, мир",
    "台北市 天氣晴",
    "こんにちは",
    "73 de N0CALL 👍",
    '{"temp": 21.5, "hum": 60}',
    "line 1\r\nline 2\nline 3\tend",
    "https://example.org/a?b=c&d=e",
    "<b>bold</b>",
    "Net at 20:00 on 145.500, all welcome!",
    "UPPER lower Mixed 123 abc",
    "a\u0007b",
    "x" * 255,
    "The quick brown fox jumps over the lazy dog. " * 5,
]
# ---- the library encoder uses a part that the file leaves out
LIB_LEFT_OUT = [
    "deadbeef01234567",
    "id 0123456789abcdef0123",
    "123e4567-e89b-12d3-a456-426614174000",
    "2026-11-16T10:30:00",
    "time 2026-11-16 10:30:00 ok",
    "DEADBEEF0123",
]
# ---- valid, written as bits
hello = "1" + SHIFT + LET["h"] + LET["e"] + LET["l"] + LET["l"] + LET["o"]
HAND = [
    ("Hello", hello, "the example of section 8"),
    ("Hell", hello, "the length byte is smaller than the text of the sender", 4),
    ("at", "1" + LET["a"] + LET["t"], "two letters"),
    ("Hi", "1" + SHIFT + LET["h"] + LET["i"], "a shift"),
    ("WX", "1" + RUN_ON + LET["w"] + LET["x"], "the upper-case run"),
    ("WXe", "1" + RUN_ON + LET["w"] + LET["x"] + P0 + LETTERS + LET["e"], "the upper-case run goes off"),
    ("73", "1" + dig_item(13) + DIG["3"], "a digit changes the state to Digits"),
    ("73e", "1" + dig_item(13) + DIG["3"] + P0 + LETTERS + LET["e"], "the state changes back to Letters"),
    ("!", "1" + sym_item(19), "one symbol"),
    ('": "', "1" + sym_item(25), "sequence 0"),
    ('": ', "1" + sym_item(26), "sequence 1"),
    ("</", "1" + sym_item(27), "sequence 2"),
    ('="', "1" + dig_item(23), "sequence 3"),
    ('":"', "1" + dig_item(24), "sequence 4"),
    ("://", "1" + dig_item(25), "sequence 5"),
    ("\r\n", "1" + sym_item(8), "CR LF"),
    ("\r\t\n", "1" + sym_item(22) + sym_item(14) + sym_item(7), "CR, Tab, LF"),
    ("é", "1" + ONE_CP + cp(0, 0xE9), "one code point"),
    ("ée", "1" + ONE_CP + cp(0, 0xE9) + LET["e"], "one code point does not change the state"),
    ("éé", "1" + ONE_CP + cp(0, 0xE9) + ONE_CP + cp(0xE9, 0xE9), "a difference of 0"),
    ("👍", "1" + ONE_CP + cp(0, 0x1F44D), "a code point with k = 4"),
    ("\U0010ffff", "1" + ONE_CP + cp(0, 0x10FFFF), "the last code point"),
    ("\u0080", "1" + ONE_CP + cp(0, 0x80), "the first code point"),
    (
        "台北 ,.\ne",
        "1"
        + TO_UNICODE
        + cp(0, 0x53F0)
        + cp(0x53F0, 0x5317)
        + step(5, 5)
        + step(0, 4)
        + step(5, 5)
        + step(2, 4)
        + step(5, 5)
        + step(3, 4)
        + step(5, 5)
        + step(4, 4)
        + step(5, 5)
        + step(1, 4)
        + LETTERS
        + LET["e"],
        "the state Unicode and its five codes",
    ),
    (
        "台!7e",
        "1"
        + TO_UNICODE
        + cp(0, 0x53F0)
        + step(5, 5)
        + step(1, 4)
        + SYMBOLS
        + POS[19]
        + step(5, 5)
        + step(1, 4)
        + DIGITS
        + POS[13]
        + P0
        + LETTERS
        + LET["e"],
        "items from the state Unicode; a digit changes the state to Digits",
    ),
    (
        "台北",
        "1" + TO_UNICODE + cp(0, 0x53F0) + step(5, 5) + step(1, 4) + UNICODE + cp(0x53F0, 0x5317),
        "the set code Unicode in the state Unicode has no effect",
    ),
    ("eeeeeeeeee", "1" + LET["e"] * 5 + P0 + REPEAT + count(0) + count(1), "a repeat with the length 5 and the distance 5"),
    (
        "abcdefabcde",
        "1" + "".join(LET[c] for c in "abcdef") + P0 + REPEAT + count(0) + count(2),
        "a repeat with the length 5 and the distance 6",
    ),
    ("eeeee", "1" + LET["e"] + dig_item(26) + count(0), "the repeated byte, 4 times"),
    ("e" * 15, "1" + LET["e"] + dig_item(26) + count(10), "a count of the second row"),
    ("e" * 105, "1" + LET["e"] + dig_item(26) + count(100), "a count of the third row"),
    ("e" * 153, "1" + LET["e"] + dig_item(26) + count(148), "a count of the fourth row"),
    ("\u0007", "1" + BYTES + count(1) + byte8(7), "the item Bytes"),
    (
        "\u0001e\u007f",
        "1" + BYTES + count(1) + byte8(1) + LET["e"] + BYTES + count(1) + byte8(0x7F),
        "the item Bytes does not change the state",
    ),
    ("é", "1" + BYTES + count(2) + byte8(0xC3) + byte8(0xA9), "the item Bytes holds the UTF-8 form of a character"),
]


def _hand():
    hand_out = []
    for text, bits, note, *more in HAND:
        for pad in "01":
            data, left = B(bits, pad)
            if left == 0 and pad == "1":
                continue
            if more:
                tail = f"; {left + more[0]} bits remain after the last code"
            elif left == 0:
                tail = "; no bit remains after the last code"
            elif left == 1:
                tail = f"; 1 bit remains after the last code, and it is {pad}"
            else:
                tail = f"; {left} bits remain after the last code, and each is {pad}"
            hand_out.append((text, data, note + tail))
    return hand_out


# ---- invalid, written as bits
BAD = [
    (1, 0, "1" + LET["e"], "N is 0"),
    (1, 0, "", "N is 0, and there are no bytes"),
    (2, 1, "0" + LET["e"], None),
    (2, 5, "0" + hello[1:], "the example of section 8 with the first bit 0"),
    (3, 1, "", "no bytes"),
    (3, 2, "1" + LET["e"], "the bits end in a shift"),
    (3, 5, hello[:24], "the example of section 8 without its last byte"),
    (3, 2, "1" + LET["e"] + POS[27][:4], "the bits end inside a position code"),
    (4, 1, "1" + sym_item(27), "a sequence of 2 bytes"),
    (4, 1, "1" + sym_item(8), "CR LF"),
    (4, 1, "1" + ONE_CP + cp(0, 0xE9), "a code point of 2 bytes"),
    (4, 4, "1" + LET["e"] + dig_item(26) + count(0), "the repeated byte gives 4 bytes, and 3 are left"),
    (4, 255, "1" + LET["e"] + dig_item(26) + count(2196), "a count of the fifth row is always too large"),
    (4, 9, "1" + LET["e"] * 5 + P0 + REPEAT + count(0) + count(1), "a repeat of 5 bytes, and 4 are left"),
    (5, 5, hello + "0" * 9, "the example of section 8 and one more byte"),
    (5, 3, hello, "the example of section 8 with N = 3: 11 bits remain"),
    (5, 1, "1" + LET["e"] + "1" * 12, None),
    (6, 1, "1" + ONE_CP + step(5, 5), None),
    (7, 1, "1" + SHIFT + P0 + SYMBOLS, "the set code Symbols"),
    (7, 1, "1" + SHIFT + P0 + DIGITS, "the set code Digits"),
    (7, 1, "1" + SHIFT + P0 + REPEAT, "the set code Repeat"),
    (7, 1, "1" + SHIFT + P0 + UNICODE, "the set code Unicode"),
    (8, 1, "1" + RUN_ON + POS[1], "position 1 of Letters, the space"),
    (8, 1, "1" + RUN_ON + sym_item(1), "position 1 of Symbols"),
    (8, 1, "1" + RUN_ON + dig_item(1), "position 1 of Digits"),
    (9, 1, "1" + ONE_CP + raw_cp(0, 0, 63), "U+003F"),
    (9, 2, "1" + ONE_CP + raw_cp(1, 0, 63), "U+007F"),
    (9, 1, "1" + ONE_CP + raw_cp(0, 1, 1), "below 0"),
    (9, 3, "1" + ONE_CP + cp(0, 0xD800), "U+D800, a surrogate"),
    (9, 3, "1" + ONE_CP + cp(0, 0xDFFF), "U+DFFF, a surrogate"),
    (9, 4, "1" + ONE_CP + cp(0, 0x110000), "above U+10FFFF"),
    (9, 4, "1" + ONE_CP + cp(0, 0xE9) + ONE_CP + cp(0xE9, 0x41), "the second code point is U+0041"),
    (10, 1, "1" + dig_item(27), None),
    (10, 2, "1" + LET["e"] + dig_item(27), "the end code where the library encoder puts it"),
    (11, 4, "1" + dig_item(26) + count(0), None),
    (12, 5, "1" + P0 + REPEAT + count(0) + count(1), "the output is empty"),
    (12, 8, "1" + LET["e"] * 3 + P0 + REPEAT + count(0) + count(1), "the distance is 5, and the output has 3 bytes"),
    (13, 11, "1" + LET["e"] * 5 + P0 + REPEAT + count(1) + count(1), "the length is 6, and the distance is 5"),
    (13, 9, "1" + LET["e"] * 4 + P0 + REPEAT + count(0) + count(0), "the length is 5, and the distance is 4"),
    (14, 1, "1" + dig_item(0) + "0" + "0" * 8, "the 5 bits start with 0: a template of Unishox2"),
    (14, 1, "1" + dig_item(0) + "10" + "0" * 8, "the 5 bits start with 10: hexadecimal digits"),
    (14, 1, "1" + dig_item(0) + "110" + "0" * 8, "the 5 bits start with 110: a UUID"),
    (14, 1, "1" + dig_item(0) + "1110" + "0" * 8, "the 5 bits start with 1110: hexadecimal digits"),
    (14, 1, "1" + dig_item(0) + "11110" + "0" * 8, "the 5 bits are 11110: a UUID"),
    (15, 1, "1" + BYTES + count(0), None),
    (16, 1, "1" + BYTES + count(1) + byte8(0xFF), "the byte FF"),
    (16, 1, "1" + BYTES + count(1) + byte8(0xC3), "the first byte of a character of 2 bytes"),
    (16, 2, "1" + BYTES + count(2) + byte8(0xC0) + byte8(0x80), "an overlong form"),
    (16, 3, "1" + BYTES + count(3) + byte8(0xED) + byte8(0xA0) + byte8(0x80), "a surrogate in UTF-8"),
    (16, 2, "1" + BYTES + count(1) + byte8(0xC3) + LET["e"], None),
]


def _library_pairs(texts):
    """Each text with the output of the library encoder. The library decoder
    gives the text back."""
    from qua_network.legacy_text import _library

    dll = _library()
    for f in (dll.qua_usx_dflt_compress, dll.qua_usx_dflt_decompress):
        f.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        f.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(BUF)
    out = []
    for text in texts:
        b = text.encode("utf-8")
        n = dll.qua_usx_dflt_compress(b, len(b), buf, BUF)
        if n <= 0:
            raise RuntimeError(f"the library encoder gives {n}")
        data = buf.raw[:n]
        ctypes.memset(buf, 0, BUF)
        m = dll.qua_usx_dflt_decompress(data, len(data), buf, BUF)
        if buf.raw[: max(m, 0)] != b:
            raise RuntimeError(f"the library decoder does not give the text {text!r}")
        out.append((text, data))
    return out


def vectors():
    out = []

    def valid(text, data, origin, note=None):
        b = text.encode("utf-8")
        if not 1 <= len(b) <= 255:
            raise ValueError("a text has 1 to 255 bytes")
        v = {"text": text, "length": len(b), "compressed": data.hex().upper(), "from": origin}
        if note:
            v["note"] = note
        out.append(v)

    def invalid(n, data, case, origin, note=None):
        v = {"length": n, "compressed": data.hex().upper(), "invalid": case, "from": origin}
        if note:
            v["note"] = note
        out.append(v)

    for text, data in _library_pairs(LIB_VALID):
        valid(text, data, "library")
    for text, data, note in _hand():
        valid(text, data, "bits", note)
    for case, n, bits, note in BAD:
        invalid(n, B(bits)[0], case, "bits", note)
    for text, data in _library_pairs(LIB_LEFT_OUT):
        invalid(len(text.encode("utf-8")), data, 14, "library", "the library encoder gives this for the text " + json.dumps(text))
    return out
