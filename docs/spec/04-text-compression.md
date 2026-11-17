# Text compression

| | |
|---|---|
| Status | Draft. Not frozen. Items carry the labels **[agreed]**, **[proposed]** and **[open]** with the meaning given in the RFC. |
| Rationale | [RFC draft 0, section 5.7](../rfc/qua-network-rfc-0.md#57-text-compression) |
| Vectors | [`vectors/text-compression.json`](../../vectors/text-compression.json) |

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as in
RFC 2119.

## 1. Scope

This file specifies the compressed form of one free-text string: how a
decoder gets the text from the bits, and which inputs are invalid.

It does not specify these:

- Which fields are free text.
- Which characters a text can have, the two forms of a free-text field
  and the choice of the form ([13-strings](13-strings.md) section 5).

Terms:

| Term | Meaning |
|---|---|
| Text | The uncompressed string. It is UTF-8. |
| Compressed string | The bytes that this file specifies. They do not include the length byte. |
| Output | The bytes of the text that the decoder has so far. |
| Code | A group of bits with one meaning. |
| Item | One entry of a character set (section 4). |

## 2. The compressed string

**[agreed]** The compressed form is the format of Unishox2 with the
preset `USX_PSET_DFLT`, for one string. There is no other preset.

**[agreed]** The compressed form does not have these parts of Unishox2:
the templates, the hexadecimal digits and the UUID. A compressed string
that uses one of them is invalid (section 7, case 14).

Sections 3 to 6 state this format. This file is the definition. The
Unishox2 library is not (section 9).

**[agreed]** A length byte comes before the compressed string. Its value
`N` is the length of the text in bytes
([13-strings](13-strings.md) section 5.2).

**[agreed]** These rules apply to the compressed string:

1. A decoder reads bits from the first byte to the last byte. In each
   byte, the first bit is the most significant bit.
2. `N` is 1 or more.
3. The first bit is 1.
4. The decoder then reads codes (section 5) until the output has `N`
   bytes. It reads no code after that.
5. Fewer than 8 bits remain after the last code. The decoder ignores
   them. This file has no rule for their value.

## 3. Codes

### 3.1 Number

A number of `n` bits is an unsigned integer. Its first bit is its most
significant bit.

### 3.2 Step code

A step code has a limit `L`. The decoder reads bits until it reads a 0
bit, or until it has read `L` bits that are 1. The value is the count of
1 bits.

For `L` = 4, the codes are `0`, `10`, `110`, `1110` and `1111`, for the
values 0 to 4.

### 3.3 Position code

A position code gives a position from 0 to 27. Section 4 lists the code
of each position. No code is the start of a different code.

### 3.4 Set code

| Code | Meaning |
|---|---|
| `00` | Letters |
| `01` | Symbols |
| `10` | Digits |
| `110` | Repeat |
| `111` | Unicode |

### 3.5 Count

A count is a step code with the limit 4, and then a number. The step
code gives the row of this table. The count is the number plus the base.

| Step code | Bits of the number | Base | Count |
|---|---|---|---|
| 0 | 2 | 0 | 0 to 3 |
| 1 | 4 | 4 | 4 to 19 |
| 2 | 7 | 20 | 20 to 147 |
| 3 | 11 | 148 | 148 to 2195 |
| 4 | 16 | 2196 | 2196 to 67731 |

### 3.6 Code point

The decoder keeps the previous code point `P`. `P` is 0 at the start. No
state change sets `P` back to 0.

A code point has a step code `k` that is 4 or less. It then has one sign
bit and a number. The difference `d` is the number plus the base.

| `k` | Bits of the number | Base | `d` |
|---|---|---|---|
| 0 | 6 | 0 | 0 to 63 |
| 1 | 12 | 64 | 64 to 4159 |
| 2 | 14 | 4160 | 4160 to 20543 |
| 3 | 16 | 20544 | 20544 to 86079 |
| 4 | 21 | 86080 | 86080 to 2183231 |

The decoder does these steps:

1. If the sign bit is 1, it subtracts `d` from `P`. If not, it adds `d`
   to `P`.
2. It adds the UTF-8 form of the character `P` to the output.

**[agreed]** `P` MUST then be a code point from U+0080 to U+10FFFF, and
not a surrogate (U+D800 to U+DFFF).

## 4. Character sets

There are three sets: Letters, Symbols and Digits.

| Position | Code | Letters | Symbols | Digits |
|---|---|---|---|---|
| 0 | `00` | Switch | `"` | Bytes |
| 1 | `010` | Space | `{` | `,` |
| 2 | `011` | `e` | `}` | `.` |
| 3 | `1000` | `t` | `_` | `0` |
| 4 | `1001` | `a` | `<` | `1` |
| 5 | `1010` | `o` | `>` | `9` |
| 6 | `1011` | `i` | `:` | `2` |
| 7 | `1100` | `n` | LF | `5` |
| 8 | `11010` | `s` | CR LF | `-` |
| 9 | `11011` | `r` | `[` | `/` |
| 10 | `111000` | `l` | `]` | `3` |
| 11 | `111001` | `c` | `\` | `4` |
| 12 | `111010` | `d` | `;` | `6` |
| 13 | `1110110` | `h` | `'` | `7` |
| 14 | `1110111` | `u` | Tab | `8` |
| 15 | `1111000` | `p` | `@` | `(` |
| 16 | `1111001` | `m` | `*` | `)` |
| 17 | `1111010` | `b` | `&` | Space |
| 18 | `11110110` | `g` | `?` | `=` |
| 19 | `11110111` | `w` | `!` | `+` |
| 20 | `11111000` | `f` | `^` | `$` |
| 21 | `11111001` | `y` | `\|` | `%` |
| 22 | `11111010` | `v` | CR | `#` |
| 23 | `11111011` | `k` | `~` | Sequence 3 |
| 24 | `11111100` | `q` | `` ` `` | Sequence 4 |
| 25 | `11111101` | `j` | Sequence 0 | Sequence 5 |
| 26 | `11111110` | `x` | Sequence 1 | Repeated byte |
| 27 | `11111111` | `z` | Sequence 2 | End code |

LF is the byte `0A`, CR is `0D`, Tab is `09` and Space is `20`. CR LF is
the two bytes `0D 0A`.

The sequences:

| Sequence | Bytes |
|---|---|
| 0 | `": "` |
| 1 | `": ` |
| 2 | `</` |
| 3 | `="` |
| 4 | `":"` |
| 5 | `://` |

## 5. Decoding

The decoder has this state:

| Name | Values | At the start |
|---|---|---|
| State | Letters, Digits or Unicode | Letters |
| Upper-case run | On or off | Off |
| `P` (3.6) | A code point | 0 |

The decoder repeats the step of its state until the output has `N`
bytes.

### 5.1 State Letters and state Digits

The decoder reads a position code `p`.

If `p` is not 0, the result is the item at position `p` of the set of
the state (5.4).

If `p` is 0, the decoder reads a set code:

| Set code | Step |
|---|---|
| Symbols | Read a position code `q`. The result is the item at position `q` of Symbols (5.4). |
| Digits | Read a position code `q`. The result is the item at position `q` of Digits (5.4). |
| Repeat | Section 6.1. |
| Unicode | Read a step code `k` with the limit 5. It is the step code of a code point (3.6). Read the rest of the code point. The state does not change. |
| Letters | See below. |

For the set code Letters, the first condition that is true applies:

1. If the state is Digits, the state becomes Letters.
2. If the upper-case run is on, it becomes off.
3. If not, the decoder reads a shift (5.2).

### 5.2 Shift

The decoder reads a position code `p`.

| `p` | Step |
|---|---|
| 0 | Read a set code. It MUST be Letters. The upper-case run becomes on. |
| 1 | The state becomes Unicode. |
| 2 to 27 | The output gets the upper-case form of the letter at position `p`. |

### 5.3 State Unicode

The decoder reads a step code `k` with the limit 5.

If `k` is 4 or less, it is the step code of a code point (3.6). The
decoder reads the rest of the code point.

If `k` is 5, the decoder reads a step code `s` with the limit 4:

| `s` | Step |
|---|---|
| 0 | The output gets a space. |
| 1 | Read a set code (see below). |
| 2 | The output gets a comma. |
| 3 | The output gets a period. |
| 4 | The output gets LF. |

The set code after `s` = 1:

| Set code | Step |
|---|---|
| Letters | The state becomes Letters. |
| Symbols | Read a position code `q`. The result is the item at position `q` of Symbols (5.4). |
| Digits | Read a position code `q`. The result is the item at position `q` of Digits (5.4). |
| Repeat | Section 6.1. |
| Unicode | No effect. |

### 5.4 Items

| Item | Step |
|---|---|
| A letter | The output gets the letter. If the upper-case run is on, it gets the upper-case form. |
| A digit `0` to `9` | The output gets the digit. The state becomes Digits. |
| A different character | The output gets the character. |
| CR LF | The output gets the two bytes. |
| A sequence | The output gets the bytes of the sequence. |
| Repeated byte | Read a count `c`. The output gets its last byte again, `c` + 4 times. |
| Bytes | Section 6.2. |

Only a digit changes the state. A digit changes it from each of the three
states.

## 6. Repeat and bytes

### 6.1 Repeat

The decoder reads a count `a` and then a count `b`. The length is
`a` + 5. The distance is `b` + 4.

The decoder goes back by the distance from the end of the output. It
copies the length in bytes from there to the end of the output.

### 6.2 Bytes

The decoder does these steps:

1. It reads 5 bits. Each of them MUST be 1.
2. It reads a count `n`.
3. It reads `n` numbers of 8 bits. The output gets each as one byte.

The item does not change the state.

## 7. Invalid input

**[agreed]** A compressed string is invalid in each of these cases, and
in no other case:

1. `N` is 0.
2. The first bit is 0.
3. The bits end before the output has `N` bytes. This includes bits that
   end in the middle of a code.
4. A step gives the output more than `N` bytes.
5. 8 bits or more remain after the last code.
6. After the set code Unicode in the state Letters or Digits (5.1), `k`
   is 5.
7. In a shift with `p` = 0 (5.2), the set code is not Letters.
8. The upper-case run is on, and an item is at position 1 of its set.
9. A code point is not in the range of 3.6.
10. An item is the end code.
11. An item is the repeated byte, and the output is empty.
12. In a repeat, the distance is larger than the length of the output.
13. In a repeat, the length is larger than the distance.
14. In the item Bytes (6.2), one of the 5 bits is 0. In Unishox2, such
    bits start a template, hexadecimal digits or a UUID.
15. In the item Bytes, the count `n` is 0.
16. The output of `N` bytes is not valid UTF-8.

**[agreed]** A decoder MUST NOT give a text, or a part of a text, for
an invalid compressed string.

**[agreed]** A receiver that shows the text shows a placeholder in its
place. A person MUST be able to see that the placeholder is not text of
the sender.

**[proposed]** An invalid compressed string does not make the other
fields of the PDU invalid.

**[agreed]** A PDU with an invalid compressed string has no uncompressed
form (RFC 5.4). The check of its signature fails (RFC 5.5).

## 8. Encoding

**[agreed]** This file does not pin an encoder (RFC 5.7).

**[proposed]** A sender MUST send only a compressed string that is valid,
and that decodes to the text.

**[proposed]** An encoder MAY leave out each of these parts of the
format. A decoder MUST have all of them.

- The repeat (6.1).
- The repeated byte.
- The sequences.
- The state Unicode. One code point after the set code Unicode is
  sufficient.
- The upper-case run. A shift for each letter is sufficient.

A text can have characters with no item and no code point: the control
characters below U+0020 other than LF, CR and Tab, and U+007F. Only the
item Bytes can hold these.

A length byte that is too small can give a text that is too short
(section 2, rules 4 and 5). This is not an invalid string.

Example. The text `Hello` has 5 bytes. One valid compressed string is
`87 67 C7 14`:

| Bits | Meaning |
|---|---|
| `1` | The first bit |
| `00` `00` | Position 0 of Letters, then the set code Letters: a shift |
| `1110110` | Position 13: `H` |
| `011` | Position 2: `e` |
| `111000` | Position 10: `l` |
| `111000` | Position 10: `l` |
| `1010` | Position 5: `o` |
| `0` | One bit remains. The decoder ignores it. |

## 9. Relation to the Unishox2 library

This section compares this file with the library of the submodule
`3rdparty/Unishox2`, at commit `6ec2ff0`. The statements about the
library were read in `unishox2.c`.

The library has no length byte. Its decoder stops at the end code or at
the end of the bits. Its encoder writes, after the last code, as much of
the end code as the last byte can hold.

For each case of section 7, the library decoder does this:

| Case | Library decoder |
|---|---|
| 1 | Not applicable. |
| 2 | Ignores the first bit. |
| 3, 11, 12, 15 | Stops with no error. It gives the output that it has. |
| 4 | Not applicable. It has a limit for the output buffer. |
| 5 | Continues to decode. |
| 6 | Reads the step code as in the state Unicode. |
| 7 | Gives the item of the set, as after a shift. |
| 8 | Changes to the state Unicode. It gives no output for the item. |
| 9, 16 | Writes the bytes. It does no check. |
| 10 | Stops. This is its normal end. |
| 13 | Copies bytes that it has not written yet. |
| 14 | Decodes the template, the hexadecimal digits or the UUID. |

The library encoder uses templates, hexadecimal digits and the UUID. Its
output is therefore invalid for some texts. A sender cannot use the
library encoder as it is.

The check of this file against the library is the tool
`qua-legacy-usx-check`.
[`docs/research/03-text-compression-check.md`](../research/03-text-compression-check.md)
has its result.

## 10. Test vectors

`vectors/text-compression.json` has the test vectors. Each vector is one
of two kinds:

| Kind | Keys | A conformant decoder |
|---|---|---|
| A valid string | `text`, `length`, `compressed` | Gives `text` for the bytes `compressed` and the length byte `length`. |
| An invalid string | `length`, `compressed`, `invalid` | Gives no text. `invalid` is the case of section 7 that a decoder finds first, if it reads the bits in their order. |

The vectors are for a decoder. This file does not pin an encoder, so an
encoder can give different bytes for a `text`.

The key `from` states how the vector was made:

| `from` | Meaning |
|---|---|
| `library` | The encoder of the Unishox2 library made `compressed`, at the commit of section 9. For a valid string, the text is the input. For an invalid string, the library used a part that this file leaves out; `note` has the input. |
| `bits` | `vectors_text.py` wrote `compressed` as bits, from sections 3 to 6. It has its own copy of the table of section 4. |

`qua-make-vectors` computes the vectors with `vectors_text.py`. Neither
path uses the decoder of the package. `qua-check-vectors` checks the
vectors against that decoder, `usx.py`.

Each case of section 7 has one vector or more. The valid vectors with
`bits` have each part of the format: the shift, the upper-case run, the
three states, each sequence, each row of a count that a text can have,
the repeat, the repeated byte and the item Bytes. Where bits remain after
the last code, one vector has them as 0 and one has them as 1.

**[agreed]** The texts of the vectors are written for this project. They
are not from the corpus (RFC 5.7).

## 11. Open items

- **[open]** The form of the placeholder of section 7.
- **[open]** What the text form of a PDU shows for an invalid compressed
  string (RFC section 14, question 16).
