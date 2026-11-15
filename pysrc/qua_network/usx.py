# SPDX-License-Identifier: Apache-2.0
"""Text compression of docs/spec/04-text-compression.md: the format of
Unishox2 with its default preset, for one string, without the templates,
the hexadecimal digits and the UUID of Unishox2.

decode() follows the specification file. It rejects every input that the
file makes invalid.

The specification does not pin an encoder. encode() makes the choices of
the reference implementation of Unishox2 (3rdparty/Unishox2, Apache-2.0),
but it does not use the parts that the file leaves out. Its output is
equal to the output of the library for each text for which the library
does not use those parts; qua-legacy-usx-check compares the two.
encode(text, simple=True) is the smallest encoder that section 8 of the
file allows: it uses no optional part of the format.

This module was written from a reading of unishox2.c at commit 6ec2ff0. It
holds no code of the library. It is a research aid, not a reference.
"""

ALPHA, SYM, NUM, DICT, DELTA = range(5)

# Items of the character sets that are not one character.
SWITCH, CRLF, ESCAPE, RPT, TERM = "switch", "crlf", "escape", "rpt", "term"
SEQUENCES = (b'": "', b'": ', b"</", b'="', b'":"', b"://")
_SEQ = tuple(("seq", i) for i in range(6))

# Section 4: the three character sets, 28 positions each.
SETS = (
    (SWITCH, " ") + tuple("etaoinsrlcdhupmbgwfyvkqjxz"),
    tuple('"{}_<>:\n') + (CRLF,) + tuple("[]\\;'\t@*&?!^|\r~`") + _SEQ[:3],
    (ESCAPE,) + tuple(",.01925-/34678() =+$%#") + _SEQ[3:] + (RPT, TERM),
)

# Section 3.2: the position code, as (value, bits) for each position.
_P_LENS = (2, 3, 3, 4, 4, 4, 4, 4, 5, 5, 6, 6, 6, 7, 7, 7, 7, 7) + (8,) * 10
_P_VALUES = (0x00, 0x40, 0x60, 0x80, 0x90, 0xA0, 0xB0, 0xC0, 0xD0, 0xD8, 0xE0, 0xE4, 0xE8, 0xEC, 0xEE, 0xF0, 0xF2, 0xF4)
_P_VALUES += tuple(range(0xF6, 0x100))
POSITION = tuple((v >> (8 - n), n) for v, n in zip(_P_VALUES, _P_LENS))
_POSITION_OF = {code: i for i, code in enumerate(POSITION)}

# Section 3.3: the set code.
SET_CODE = ((0b00, 2), (0b01, 2), (0b10, 2), (0b110, 3), (0b111, 3))

# Section 3.4: the count. Section 3.5: the code point difference.
COUNT_BITS = (2, 4, 7, 11, 16)
COUNT_BASE = (0, 4, 20, 148, 2196)
DIFF_BITS = (6, 12, 14, 16, 21)
DIFF_BASE = (0, 64, 4160, 20544, 86080)

MIN_REPEAT = 5  # the shortest back-reference
MAX_TEXT = 255


class Malformed(ValueError):
    """The compressed string is not valid. case is the case of section 7."""

    def __init__(self, case, message):
        super().__init__(message)
        self.case = case


class _Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.end = 8 * len(data)

    def read(self, n):
        if self.pos + n > self.end:
            raise Malformed(3, "the bits end inside a code")
        v = 0
        for p in range(self.pos, self.pos + n):
            v = (v << 1) | ((self.data[p >> 3] >> (7 - (p & 7))) & 1)
        self.pos += n
        return v

    def unary(self, limit):
        """The count of 1 bits before a 0 bit; limit 1 bits have no 0 bit."""
        n = 0
        while n < limit and self.read(1):
            n += 1
        return n

    def position(self):
        v = 0
        for n in range(1, 9):
            v = (v << 1) | self.read(1)
            i = _POSITION_OF.get((v, n))
            if i is not None:
                return i
        raise AssertionError("the position code is complete")

    def set_code(self):
        if not self.read(1):
            return SYM if self.read(1) else ALPHA
        if not self.read(1):
            return NUM
        return DELTA if self.read(1) else DICT

    def count(self):
        k = self.unary(4)
        return self.read(COUNT_BITS[k]) + COUNT_BASE[k]


class _Decoder:
    def __init__(self, data, length, events):
        self.r = _Reader(data)
        self.n = length
        self.out = bytearray()
        self.state = ALPHA
        self.all_upper = False
        self.prev = 0
        self.events = events

    def note(self, name):
        if self.events is not None:
            self.events[name] = self.events.get(name, 0) + 1

    def emit(self, b):
        if len(self.out) + len(b) > self.n:
            raise Malformed(4, "the output is longer than the length byte")
        self.out += b

    def run(self):
        r = self.r
        if r.read(1) != 1:
            raise Malformed(2, "the first bit is not 1")
        while len(self.out) < self.n:
            if self.state == DELTA:
                self.delta_state()
            else:
                self.set_state()
        if r.end - r.pos >= 8:
            raise Malformed(5, "bytes after the end of the string")
        try:
            bytes(self.out).decode("utf-8")
        except UnicodeDecodeError:
            raise Malformed(16, "the output is not UTF-8") from None
        return bytes(self.out)

    # Section 5.1: the states Letters and Digits.
    def set_state(self):
        r = self.r
        p = r.position()
        if p != 0:
            self.item(self.state, p)
            return
        h = r.set_code()
        if h == DICT:
            self.repeat()
        elif h == DELTA:
            k = r.unary(5)
            if k == 5:
                raise Malformed(6, "a special code after a single Unicode switch")
            self.code_point(k)
        elif h != ALPHA:
            self.item(h, r.position())
        elif self.state == NUM:
            self.state = ALPHA
        elif self.all_upper:
            self.all_upper = False
        else:
            self.shift()

    # Section 5.2: the shift.
    def shift(self):
        r = self.r
        p = r.position()
        if p == 0:
            if r.set_code() != ALPHA:
                raise Malformed(7, "a set code after a shift")
            self.all_upper = True
        elif p == 1:
            self.state = DELTA
        else:
            self.emit(SETS[ALPHA][p].upper().encode("ascii"))

    # Section 5.3: the state Unicode.
    def delta_state(self):
        r = self.r
        k = r.unary(5)
        if k < 5:
            self.code_point(k)
            return
        s = r.unary(4)
        if s != 1:
            self.emit((b" ", None, b",", b".", b"\n")[s])
            return
        h = r.set_code()
        if h == ALPHA:
            self.state = ALPHA
        elif h == DICT:
            self.repeat()
        elif h != DELTA:
            self.item(h, r.position())

    def code_point(self, k):
        r = self.r
        negative = r.read(1)
        d = r.read(DIFF_BITS[k]) + DIFF_BASE[k]
        self.prev += -d if negative else d
        c = self.prev
        if c < 0x80 or c > 0x10FFFF or 0xD800 <= c <= 0xDFFF:
            raise Malformed(9, "a code point out of range")
        self.emit(chr(c).encode("utf-8"))

    # Section 5.4: one item of a set.
    def item(self, h, p):
        if self.all_upper and p == 1:
            raise Malformed(8, "position 1 in a run of upper-case letters")
        it = SETS[h][p]
        if it is ESCAPE:
            self.escape()
        elif it is CRLF:
            self.emit(b"\r\n")
        elif it is RPT:
            if not self.out:
                raise Malformed(11, "a repeated byte at the start")
            self.note("repeated byte")
            self.emit(self.out[-1:] * (self.r.count() + 4))
        elif it is TERM:
            raise Malformed(10, "the end code")
        elif isinstance(it, tuple):
            self.note("sequence")
            self.emit(SEQUENCES[it[1]])
        elif h == ALPHA and p >= 2:
            self.emit((it.upper() if self.all_upper else it).encode("ascii"))
        else:
            if "0" <= it <= "9":
                self.state = NUM
            self.emit(it.encode("ascii"))

    # Section 6.1: a repeat of earlier bytes.
    def repeat(self):
        r = self.r
        length = r.count() + MIN_REPEAT
        distance = r.count() + MIN_REPEAT - 1
        if distance > len(self.out):
            raise Malformed(12, "a repeat that starts before the string")
        if length > distance:
            raise Malformed(13, "a repeat that is longer than its distance")
        self.note("repeat")
        start = len(self.out) - distance
        self.emit(self.out[start : start + length])

    # Section 6.2: a run of bytes. The other escapes of Unishox2 are invalid.
    def escape(self):
        r = self.r
        k = r.unary(5)
        if k < 5:
            raise Malformed(14, ("a template", "hexadecimal digits", "a UUID", "hexadecimal digits", "a UUID")[k])
        n = r.count()
        if n == 0:
            raise Malformed(15, "an empty run of bytes")
        self.note("bytes")
        self.emit(bytes(r.read(8) for _ in range(n)))


def decode(data, length, events=None):
    """The string of `length` bytes that the bits of data hold. Raises
    Malformed for an input that the specification makes invalid. events, if
    given, is a dict that gets a count for each optional part that the
    input uses."""
    if not 1 <= length <= MAX_TEXT:
        raise Malformed(1, "the length byte is 0")
    return _Decoder(data, length, events).run()


# --- Encoder ----------------------------------------------------------------

_CODE = {}
for _h, _set in enumerate(SETS):
    for _p, _it in enumerate(_set):
        if isinstance(_it, str) and len(_it) == 1 and _it > " ":
            _CODE[ord(_it)] = (_h, _p)
            if "a" <= _it <= "z":
                _CODE[ord(_it) - 32] = (_h, _p)
_SEQ_CODE = ((SYM, 25), (SYM, 26), (SYM, 27), (NUM, 23), (NUM, 24), (NUM, 25))


class _Writer:
    def __init__(self):
        self.acc = 0
        self.n = 0

    def put(self, value, bits):
        self.acc = (self.acc << bits) | value
        self.n += bits

    def unary(self, k, limit):
        self.put((1 << k) - 1, k)
        if k < limit:
            self.put(0, 1)

    def count(self, c):
        k = max(i for i in range(5) if c >= COUNT_BASE[i])
        self.unary(k, 4)
        self.put(c - COUNT_BASE[k], COUNT_BITS[k])

    def bytes(self, bits):
        """The first `bits` bits, in whole bytes; the last byte takes the
        bits that follow."""
        size = (bits + 7) // 8
        return ((self.acc >> (self.n - 8 * size)) & ((1 << (8 * size)) - 1)).to_bytes(size, "big")


class _Encoder:
    def __init__(self, s, simple):
        self.s = s
        self.w = _Writer()
        self.state = ALPHA
        self.simple = simple

    def switch(self):
        if self.state == DELTA:
            self.w.put(0b1111110, 7)
        else:
            self.w.put(0, 2)

    def set(self, h):
        self.w.put(*SET_CODE[h])

    def code(self, h, p):
        if h == ALPHA:
            if self.state != ALPHA:
                self.switch()
                self.set(ALPHA)
                self.state = ALPHA
        elif h == SYM:
            self.switch()
            self.set(SYM)
        elif self.state != NUM:
            self.switch()
            self.set(NUM)
            it = SETS[NUM][p]
            if isinstance(it, str) and "0" <= it <= "9":
                self.state = NUM
        self.w.put(*POSITION[p])

    def escape(self):
        self.switch()
        self.set(NUM)
        self.w.put(0, 2)

    def match(self, at):
        """The longest earlier occurrence of the bytes at `at`: (length - 5,
        distance - 4), or None."""
        s, n = self.s, len(self.s)
        best = None
        for j in range(at - MIN_REPEAT, -1, -1):
            k = at
            while k < n and j + k - at < at and s[k] == s[j + k - at]:
                k += 1
            while k < n and s[k] >> 6 == 2:
                k -= 1  # do not end inside a UTF-8 character
            extra = k - at - MIN_REPEAT
            if extra > 0 and (best is None or extra > best[0]):
                best = (extra, at - j - MIN_REPEAT + 1)
        return best

    def run(self):
        s, n, w = self.s, len(self.s), self.w
        all_upper = False
        prev = 0
        w.put(1, 1)
        at = 0
        while at < n:
            if self.simple:
                at, all_upper, prev = self.char(at, all_upper, prev)
                continue
            if at < n - MIN_REPEAT + 1:
                m = self.match(at)
                if m:
                    self.switch()
                    self.set(DICT)
                    w.count(m[0])
                    w.count(m[1])
                    at += m[0] + MIN_REPEAT
                    continue
            c = s[at]
            if at and n > 4 and at < n - 4 and c == s[at - 1] == s[at + 1] == s[at + 2] == s[at + 3]:
                run = at + 4
                while run < n and s[run] == c:
                    run += 1
                self.code(NUM, 26)
                w.count(run - at - 4)
                at = run
                continue
            for i, seq in enumerate(SEQUENCES):
                if s.startswith(seq, at):
                    self.code(*_SEQ_CODE[i])
                    at += len(seq)
                    break
            else:
                at, all_upper, prev = self.char(at, all_upper, prev)
        # The reference writes as much of the end code as fits the last byte.
        used = w.n
        if self.state != NUM:
            self.switch()
            self.set(NUM)
        w.put(0xFF, 8)
        return w.bytes(used)

    def char(self, at, all_upper, prev):
        s, n, w = self.s, len(self.s), self.w
        c = s[at]
        upper = 0x41 <= c <= 0x5A
        if not upper and all_upper:
            all_upper = False
            self.switch()
            self.set(ALPHA)
            self.state = ALPHA
        if upper and not all_upper:
            if self.state == NUM:
                self.switch()
                self.set(ALPHA)
                self.state = ALPHA
            self.switch()
            self.set(ALPHA)
            if self.state == DELTA:
                self.state = ALPHA
                self.switch()
                self.set(ALPHA)
        if 32 <= c <= 126:
            if upper and not all_upper and at + 4 < n and all(0x41 <= x <= 0x5A for x in s[at : at + 5]):
                self.switch()
                self.set(ALPHA)
                self.state = ALPHA
                all_upper = True
            if self.state == DELTA and c in (0x20, 0x2C, 0x2E):
                w.put(0b11111, 5)
                w.unary({0x20: 0, 0x2C: 2, 0x2E: 3}[c], 4)
            elif c == 0x20:
                w.put(*POSITION[17 if self.state == NUM else 1])
            else:
                self.code(*_CODE[c])
            return at + 1, all_upper, prev
        if c == 13 and at + 1 < n and s[at + 1] == 10:
            self.code(SYM, 8)
            return at + 2, all_upper, prev
        if c == 10:
            if self.state == DELTA:
                w.put(0b111111111, 9)
            else:
                self.code(SYM, 7)
            return at + 1, all_upper, prev
        if c in (13, 9):
            self.code(SYM, 22 if c == 13 else 14)
            return at + 1, all_upper, prev
        if c >= 0x80:
            size = 2 if c < 0xE0 else 3 if c < 0xF0 else 4
            point = ord(s[at : at + size].decode("utf-8"))
            at += size
            if self.state != DELTA:
                if at < n and s[at] >= 0x80:
                    if self.state != ALPHA:
                        self.switch()
                        self.set(ALPHA)
                    self.switch()
                    self.set(ALPHA)
                    w.put(*POSITION[1])
                    self.state = DELTA
                else:
                    self.switch()
                    self.set(DELTA)
            d = abs(point - prev)
            k = max(i for i in range(5) if d >= DIFF_BASE[i])
            w.unary(k, 5)
            w.put(1 if prev > point else 0, 1)
            w.put(d - DIFF_BASE[k], DIFF_BITS[k])
            return at, all_upper, point
        # A control character starts a run of raw bytes. The reference
        # continues the run up to the next character outside ASCII or the
        # next run of one repeated byte. The simple encoder ends it at the
        # first byte that has a code.
        end = at + 1
        while end < n and s[end] < 0x80:
            if self.simple:
                if s[end] >= 32 and s[end] != 127 or s[end] in (9, 10, 13):
                    break
            elif end < n - 4 and s[end] == s[end - 1] == s[end + 1] == s[end + 2] == s[end + 3]:
                break
            end += 1
        self.escape()
        w.put(0b11111, 5)
        w.count(end - at)
        for p in range(at, end):
            w.put(s[p], 8)
        return end, all_upper, prev


def encode(text, simple=False):
    """The bits of the compressed form of text, as whole bytes. text is
    valid UTF-8 of 1 to 255 bytes. The result has no length byte. With
    simple, the encoder uses no optional part of the format."""
    if not 1 <= len(text) <= MAX_TEXT:
        raise ValueError("the text has 1 to 255 bytes")
    text.decode("utf-8")
    return _Encoder(text, simple).run()
