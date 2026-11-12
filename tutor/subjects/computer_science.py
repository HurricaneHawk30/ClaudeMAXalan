"""GCSE Computer Science, Years 10–11 (docs/ARCHITECTURE_V2.md section 5.1).

Three generated skills live here (binary & hex, data units, logic gates); the bank
skills (computer systems, networks & security, algorithms & programming) come from
``packs/computer_science.json``.

Every generator is pure: ``generate(level, seed)`` uses only ``random.Random(seed)``.
Every data-size question states "1 kilobyte = 1000 bytes".  Logic expressions are
written with the words AND, OR, NOT and XOR and are fully bracketed, so they read the
same on every exam board.
"""
from __future__ import annotations

import math
import random
from dataclasses import replace
from fractions import Fraction
from itertools import product
from typing import Callable

from ..content import (
    Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, build_choice, build_short, load_pack,
)
from ..content.fmt import build, check_level, fmt_num, fmt_sf, near_half, num_answer, num_mistake, retry

SUBJECT_ID = "computer_science"
Draft = dict

BYTE = "Use 1 byte = 8 bits."
KB = "Use 1 byte = 8 bits and 1 kilobyte = 1000 bytes."
MB = "Use 1 byte = 8 bits, 1 kilobyte = 1000 bytes and 1 megabyte = 1000 kilobytes."


# ================================================================ helpers

def _q(text: str, answer: Answer | None, solution: str, hint: str, mistakes=(), ref: str = "",
       short: tuple | None = None) -> Draft:
    d = {"text": text, "answer": answer, "solution": solution, "hint": hint, "mistakes": list(mistakes), "ref": ref}
    if short is not None:
        d["short"] = short
    return d


def _choice(stem: str, options: list[str], correct: int, solution: str, hint: str,
            feedback: list[str | None] | None = None, ref: str = "") -> Draft:
    return {"choice": (stem, list(options), correct, feedback), "solution": solution, "hint": hint, "ref": ref}


def _num(v, unit: str = "") -> Answer:
    return num_answer(v, f"{fmt_num(v)} {unit}".strip())


def _num_mis(v, fb: str, unit: str = "") -> Mistake | None:
    if v is None:
        return None
    f = Fraction(v)
    d = f.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    if d != 1:
        return None
    return Mistake(num_answer(f, f"{fmt_num(f)} {unit}".strip()), fb)


def _b8(v: int) -> str:
    return format(v, "08b")


def _nib(v: int) -> str:
    s = _b8(v)
    return f"{s[:4]} {s[4:]}"


def _hex(v: int) -> str:
    return format(v, "02X")


def _bits_short(v: int, extra_rejects: dict[str, str] | None = None) -> tuple:
    """accept the 8-bit and the nibble-spaced form; reject listed near misses."""
    accept = [_b8(v), _nib(v)]
    reject: list[str] = []
    fb: dict[str, str] = {}
    for r, f in (extra_rejects or {}).items():
        if r and r not in accept and r.replace(" ", "") != _b8(v) and r not in reject:
            reject.append(r)
            fb[r] = f
    return accept, reject, "any", fb


def _place_sum(v: int) -> str:
    parts = [str(1 << i) for i in range(7, -1, -1) if v >> i & 1]
    return " + ".join(parts)


_HEXDIG = "0123456789ABCDEF"


def _hex_note(d: int) -> str:
    return f"{d} = {_HEXDIG[d]}" if d >= 10 else str(d)


# ====================================================================== binary

def _bi_1(rng: random.Random) -> Draft:
    """8-bit binary -> denary (number)."""
    v = rng.randint(20, 255)
    b = _b8(v)
    rev = int(b[::-1], 2)
    ms = [_num_mis(rev if rev != v else None, "The leftmost bit has the largest place value (128); the rightmost is worth 1")]
    return _q(f"Convert the 8-bit binary number {b} to denary.", _num(v),
              f"Place values 128, 64, 32, 16, 8, 4, 2, 1: {b} = {_place_sum(v)} = {v}",
              "Write the place values above the bits, doubling from the right, then add the place values of the bits that are set", ms)


def _bi_2(rng: random.Random) -> Draft:
    """Denary -> 8-bit binary (short)."""
    def pick(r):
        v = r.randint(5, 250)
        return v if _b8(v) != _b8(v)[::-1] else None
    v = retry(pick, rng)
    b = _b8(v)
    rej = {b[::-1]: "The leftmost bit is worth 128: write the bits in order from 128 down to 1"}
    if v < 128:
        rej[b.lstrip("0")] = "That's the right value, but the question asks for 8 bits — include the leading zeros"
    return _q(f"Convert the denary number {v} to an 8-bit binary number.", None,
              f"{v} = {_place_sum(v)}, so in binary it is {b}",
              "Start with 128: if it fits, write 1 and subtract it; then try 64, 32, 16, 8, 4, 2 and 1",
              short=_bits_short(v, rej))


def _bi_3(rng: random.Random) -> Draft:
    """Hex <-> denary (number or short)."""
    def pick(r):
        v = r.randint(17, 255)
        return v if v % 16 != v // 16 else None
    v = retry(pick, rng)
    h = _hex(v)
    hi, lo = divmod(v, 16)
    sol = f"{h}: the first digit {h[0]} = {hi} (sixteens) and the second digit {h[1]} = {lo} (ones), so {hi} × 16 + {lo} = {v}"
    if rng.random() < 0.5:
        ms = [_num_mis(int(h[::-1], 16), "The first hex digit is the number of 16s, the second is the number of 1s")]
        if h.isdigit():
            ms.append(_num_mis(int(h), "Hexadecimal is base 16: the first digit is worth 16, not 10"))
        else:
            ms.append(_num_mis(hi * 10 + lo, "Hexadecimal is base 16: multiply the first digit by 16, not 10"))
        d = _q(f"Convert the hexadecimal number {h} to denary.", _num(v), sol,
               "The left digit counts 16s and the right digit counts 1s; A = 10, B = 11, … F = 15", ms)
        d["fallback"] = "Multiply the left hex digit by sixteen, then add the right digit (A is ten, B is eleven and so on)"
        return d
    rev = h[::-1]
    rej = {rev: f"The first hex digit is the number of 16s: {v} ÷ 16 = {hi} remainder {lo}"}
    d = _q(f"Convert the denary number {v} to hexadecimal.", None,
           f"{v} ÷ 16 = {hi} remainder {lo}. {_hex_note(hi)} and {_hex_note(lo)}, so the hex is {h}",
           "Divide by 16: the whole-number answer is the first digit and the remainder is the second",
           short=([h], [r for r in rej if r != h], "any", {r: f for r, f in rej.items() if r != h}))
    # used when the hex answer is "16" (denary 22): the main hint mentions 16
    d["fallback"] = ("Work out how many sixteens fit into the number: that is the first hex digit, "
                     "and what is left over is the second digit")
    return d


def _bi_4(rng: random.Random) -> Draft:
    """Binary <-> hex (short)."""
    def pick(r):
        v = r.randint(17, 255)
        return v if v % 16 != v // 16 and _b8(v) != _b8(v)[::-1] else None
    v = retry(pick, rng)
    h, b = _hex(v), _b8(v)
    hi, lo = divmod(v, 16)
    if rng.random() < 0.5:
        rej = {h[::-1]: "Convert each group of 4 bits from left to right: the left nibble gives the first hex digit"}
        d = _q(f"Convert the 8-bit binary number {b} to hexadecimal.", None,
               f"Split into nibbles: {b[:4]} = {_hex_note(hi)} and {b[4:]} = {_hex_note(lo)}, so the hex is {h}",
               "Split the bits into two groups of 4 and convert each group to one hex digit",
               short=([h], list(rej), "any", rej))
        d["fallback"] = "Split the bits into two groups of four and turn each group into one hex digit"
        return d
    rej = {_b8(lo * 16 + hi): "Convert the hex digits in order: the first digit gives the left 4 bits"}
    if v < 128:
        rej[b.lstrip("0")] = "That's the right value, but the question asks for 8 bits — include the leading zeros"
    d = _q(f"Convert the hexadecimal number {h} to an 8-bit binary number.", None,
           f"{h[0]} = {b[:4]} and {h[1]} = {b[4:]}, so the binary is {b}",
           "Convert each hex digit into a group of 4 bits (8, 4, 2, 1)",
           short=_bits_short(v, rej))
    d["fallback"] = "Turn each hex digit into a group of four bits, then write the two groups side by side"
    return d


def _bi_5(rng: random.Random) -> Draft:
    """8-bit addition (with or without overflow), or a logical shift (short)."""
    v = rng.random()
    if v < 0.35:
        def pick(r):
            a, b = r.randint(10, 200), r.randint(10, 200)
            return (a, b) if a + b <= 255 and a & b else None
        a, b = retry(pick, rng)
        s = a + b
        rej = {_b8(a ^ b): "Remember to carry: 1 + 1 = 10 in binary, so write 0 and carry 1"}
        return _q(f"Add the 8-bit binary numbers {_b8(a)} and {_b8(b)}. Give your answer as an 8-bit binary number.", None,
                  f"Add column by column from the right, carrying 1 when a column adds up to 2 or more: "
                  f"{_b8(a)} + {_b8(b)} = {_b8(s)} (check: {a} + {b} = {s})",
                  "Work from the right: 0 + 0 = 0, 0 + 1 = 1, 1 + 1 = 0 carry 1, 1 + 1 + 1 = 1 carry 1",
                  short=_bits_short(s, rej))
    if v < 0.6:
        def pick(r):
            a, b = r.randint(100, 250), r.randint(100, 250)
            return (a, b) if a + b > 255 else None
        a, b = retry(pick, rng)
        s = a + b
        nine = format(s, "09b")
        low = _b8(s & 0xFF)
        rej = {low: "That's only the lowest 8 bits — include the carry bit on the left to give all 9 bits"}
        return _q(f"Add the 8-bit binary numbers {_b8(a)} and {_b8(b)}. The answer does not fit in 8 bits, so an "
                  "overflow error would occur in an 8-bit register. Give the full 9-bit result.", None,
                  f"Add column by column from the right, carrying 1 when a column adds up to 2 or more: "
                  f"{_b8(a)} + {_b8(b)} = {nine} (check: {a} + {b} = {s}, which is more than 255)",
                  "Work from the right, carrying 1 each time a column adds up to 2 or more; the last carry becomes the 9th bit",
                  short=([nine], list(rej), "any", rej))
    left = rng.random() < 0.55
    n = rng.randint(1, 3)

    def pick(r):
        x = r.randint(3, 250)
        res = (x << n) & 0xFF if left else x >> n
        other = x >> n if left else (x << n) & 0xFF
        return (x, res, other) if res and res != other and res != x else None
    x, res, other = retry(pick, rng)
    word = "left" if left else "right"
    places = "1 place" if n == 1 else f"{n} places"
    lost = (x << n) > 0xFF if left else x & ((1 << n) - 1)
    effect = (f"multiplies the value by {1 << n}" if left else f"divides the value by {1 << n}") if not lost else \
        "and the bits shifted out are lost"
    rej = {_b8(other): f"A {word} shift moves every bit towards the {word}"}
    return _q(f"Apply a logical {word} shift of {places} to the 8-bit binary number {_b8(x)}. Bits shifted out are lost "
              f"and 0s fill the empty places. Give the 8-bit result.", None,
              f"Move every bit {places} to the {word} and fill with 0s: {_b8(x)} becomes {_b8(res)} "
              f"({'this ' + effect if not lost else effect.replace('and ', '')})",
              f"Move each bit {places} to the {word}; any bits that fall off the end are lost",
              short=_bits_short(res, rej))


# ================================================================== data units

def _du_1(rng: random.Random) -> Draft:
    """Bits <-> bytes, or bytes -> kilobytes."""
    v = rng.random()
    if v < 0.35:
        k = rng.randint(2, 250)
        return _q(f"How many bytes are there in {8 * k} bits? {KB}", _num(k, "bytes"),
                  f"{8 * k} ÷ 8 = {k} bytes", "There are 8 bits in every byte",
                  [_num_mis(64 * k, "Divide by 8 to go from bits to bytes — there are fewer bytes than bits", "bytes")])
    if v < 0.7:
        k = rng.randint(2, 250)
        return _q(f"How many bits are there in {k} bytes? {KB}", _num(8 * k, "bits"),
                  f"{k} × 8 = {8 * k} bits", "There are 8 bits in every byte",
                  [_num_mis(Fraction(k, 8), "Multiply by 8 to go from bytes to bits — there are more bits than bytes", "bits")])
    n = 100 * rng.randint(3, 900)
    kb = Fraction(n, 1000)
    return _q(f"Convert {n} bytes to kilobytes. {KB}", _num(kb, "KB"),
              f"{n} ÷ 1000 = {fmt_num(kb)} KB", "Kilobytes are bigger than bytes, so divide",
              [_num_mis(n * 1000, "Divide by 1000 to go from bytes to kilobytes", "KB"),
               _num_mis(Fraction(n, 8), "The question says 1 kilobyte = 1000 bytes: divide by 1000", "KB")])


_UNITS = (("kilobytes", "KB", "bytes", "bytes"), ("megabytes", "MB", "kilobytes", "KB"),
          ("gigabytes", "GB", "megabytes", "MB"))


def _du_2(rng: random.Random) -> Draft:
    """KB <-> MB <-> GB."""
    big, bs, small, ss = rng.choice(_UNITS[1:])
    rule = (f"Use 1 kilobyte = 1000 bytes and 1 {big[:-1]} = 1000 {small}." if big != "megabytes" else
            "Use 1 kilobyte = 1000 bytes and 1 megabyte = 1000 kilobytes.")
    if rng.random() < 0.5:
        x = Fraction(rng.randint(12, 950), 10)
        val = x * 1000
        return _q(f"Convert {fmt_num(x)} {bs} to {small}. {rule}", _num(val, ss),
                  f"{fmt_num(x)} × 1000 = {fmt_num(val)} {ss}", f"There are 1000 {small} in 1 {big[:-1]}",
                  [_num_mis(x / 1000, f"{small.capitalize()} are smaller, so there are more of them: multiply by 1000", ss)])
    n = rng.randint(120, 95000) // 10 * 10
    val = Fraction(n, 1000)
    return _q(f"Convert {n} {ss} to {big}. {rule}", _num(val, bs),
              f"{n} ÷ 1000 = {fmt_num(val)} {bs}", f"There are 1000 {small} in 1 {big[:-1]}, so divide",
              [_num_mis(n * 1000, f"{big.capitalize()} are bigger, so there are fewer of them: divide by 1000", bs)])


def _du_3(rng: random.Random) -> Draft:
    """Image file size in kilobytes."""
    def pick(r):
        w, h = r.choice([40, 50, 64, 80, 100, 120, 128, 160, 200, 256, 300, 400, 500, 640, 800, 1024]), \
            r.choice([30, 40, 48, 50, 60, 64, 80, 100, 120, 150, 200, 240, 300, 480, 600, 768])
        d = r.choice([1, 2, 4, 8, 8, 16, 24, 24])
        kb = Fraction(w * h * d, 8000)
        return (w, h, d, kb) if (kb * 100).denominator == 1 else None
    w, h, d, kb = retry(pick, rng)
    bits = w * h * d
    ms = [_num_mis(Fraction(bits, 1000), "Divide by 8 to change bits into bytes before dividing by 1000", "KB"),
          _num_mis(Fraction(bits, 8), "That's the size in bytes — divide by 1000 to get kilobytes", "KB"),
          _num_mis(Fraction(w * h, 8000), f"Multiply by the colour depth ({d} bits per pixel)", "KB")]
    return _q(f"An image is {w} pixels wide and {h} pixels high, with a colour depth of {d} bit{'s' if d > 1 else ''}. "
              f"Work out the file size in kilobytes. Ignore any metadata. {KB}",
              _num(kb, "KB"), f"{w} × {h} × {d} = {bits} bits; ÷ 8 = {fmt_num(Fraction(bits, 8))} bytes; "
                              f"÷ 1000 = {fmt_num(kb)} KB",
              "File size in bits = width × height × colour depth", ms)


def _du_4(rng: random.Random) -> Draft:
    """Sound file size, 3 significant figures."""
    def pick(r):
        rate = r.choice([8000, 11025, 16000, 22050, 44100, 48000])
        depth = r.choice([8, 16, 16, 24])
        t = r.choice([5, 10, 12, 15, 20, 30, 45, 60, 90, 120, 150, 180])
        ch = r.choice([1, 1, 2])
        bits = rate * depth * t * ch
        mb = Fraction(bits, 8 * 10 ** 6)
        unit = ("megabytes", "MB", mb) if mb >= 1 else ("kilobytes", "KB", mb * 1000)
        if near_half(unit[2], sf=3):
            return None
        return rate, depth, t, ch, bits, unit
    rate, depth, t, ch, bits, (uname, us, val) = retry(pick, rng)
    div = 8 * 10 ** 6 if us == "MB" else 8000
    chan = "mono (1 channel)" if ch == 1 else "stereo (2 channels)"
    ms = [num_mistake(Fraction(bits * 8, div), us, "Divide the number of bits by 8 to get bytes", sf=3)]
    if ch == 2:
        ms.append(num_mistake(Fraction(bits, 2 * div), us, "Stereo has 2 channels, so multiply by 2", sf=3))
    ms.append(num_mistake(Fraction(bits * (1000 if us == "MB" else 1), div), us,
                          "Check the unit conversion: divide by 1000 for each step from bytes", sf=3))
    steps = (f"{rate} × {depth} × {t}" + (" × 2" if ch == 2 else "") + f" = {bits} bits; ÷ 8 = {bits // 8} bytes; "
             + (f"÷ 1 000 000 = {fmt_num(Fraction(bits, 8 * 10 ** 6))} MB" if us == "MB" else
                f"÷ 1000 = {fmt_num(Fraction(bits, 8000))} KB"))
    shown = fmt_sf(val, 3)
    tail = "" if Fraction(shown) == val else f" = {shown} {us} (3 s.f.)"
    return _q(f"A sound is recorded for {t} seconds with a sample rate of {rate} Hz and a sample resolution (bit depth) "
              f"of {depth} bits, in {chan}. Work out the file size in {uname}. Ignore any metadata. {MB} "
              "Give your answer to 3 significant figures.",
              num_answer(val, f"{shown} {us}", sf=3), f"{steps}{tail}",
              "File size in bits = sample rate × bit depth × seconds × number of channels", ms)


def _du_5(rng: random.Random) -> Draft:
    """Colours from n bits, bits needed for k colours, or a file size from the number of colours."""
    v = rng.random()
    if v < 0.35:
        n = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 24])
        c = 2 ** n
        return _q(f"How many different colours can be represented with a colour depth of {n} bit{'s' if n > 1 else ''}?",
                  _num(c), f"Each bit doubles the number of colours: 2 to the power {n} = {c}",
                  "With n bits there are 2 × 2 × … × 2 (n times) different patterns",
                  [_num_mis(2 * n, f"n bits give 2 to the power n colours, not 2 × n"),
                   _num_mis(n * n if n * n != c else None, f"n bits give 2 to the power n colours, not n²")])
    if v < 0.7:
        def pick(r):
            k = r.randint(3, 300)
            return k if k & (k - 1) else None
        k = retry(pick, rng)
        n = math.ceil(math.log2(k))
        return _q(f"An image uses {k} different colours. What is the minimum colour depth (number of bits per pixel) needed?",
                  _num(n), f"{n - 1} bits give {2 ** (n - 1)} colours, which is not enough; {n} bits give {2 ** n} colours, "
                           f"so {n} bits are needed",
                  "Find the smallest power of 2 that is at least as big as the number of colours",
                  [_num_mis(n - 1, f"{n - 1} bits give only {2 ** (n - 1)} colours, which is fewer than {k}")])

    def pick(r):
        k = r.choice([3, 4, 5, 6, 8, 10, 12, 16, 20, 32, 50, 64, 100, 128, 200, 256])
        n = max(1, math.ceil(math.log2(k)))
        w, h = r.choice([10, 20, 25, 40, 50, 64, 80, 100, 120, 200]), r.choice([10, 16, 20, 30, 40, 50, 60, 100])
        return (k, n, w, h) if (w * h * n) % 8 == 0 else None
    k, n, w, h = retry(pick, rng)
    size = w * h * n // 8
    return _q(f"An image is {w} × {h} pixels and uses {k} different colours. It is stored using the minimum colour depth "
              f"for {k} colours. Work out the file size in bytes. Ignore any metadata. {BYTE}",
              _num(size, "bytes"), f"{k} colours need {n} bit{'s' if n > 1 else ''} per pixel (2 to the power {n} = {2 ** n}). "
                                   f"{w} × {h} × {n} = {w * h * n} bits; ÷ 8 = {size} bytes",
              "First work out how many bits per pixel are needed for that many colours",
              [_num_mis(Fraction(w * h * k, 8), "Use the number of bits per pixel, not the number of colours", "bytes"),
               _num_mis(w * h * n, "That's the size in bits — divide by 8 for bytes", "bytes")])


# ====================================================================== logic

_GATES = {
    "AND": lambda a, b: a & b,
    "OR": lambda a, b: a | b,
    "XOR": lambda a, b: a ^ b,
    "NAND": lambda a, b: 1 - (a & b),
    "NOR": lambda a, b: 1 - (a | b),
}
_GATE_RULE = {
    "AND": "AND outputs 1 only when both inputs are 1",
    "OR": "OR outputs 1 when at least one input is 1",
    "XOR": "XOR outputs 1 only when the inputs are different",
    "NOT": "NOT outputs the opposite of its input",
}
_BIT = "Give your answer as 0 or 1."

# Expressions are trees: "A" | ("NOT", e) | (gate, e1, e2).


def _ev(e, env: dict[str, int]) -> int:
    if isinstance(e, str):
        return env[e]
    if e[0] == "NOT":
        return 1 - _ev(e[1], env)
    return _GATES[e[0]](_ev(e[1], env), _ev(e[2], env))


def _tx(e, top: bool = True) -> str:
    if isinstance(e, str):
        return e
    inner = f"NOT {_tx(e[1], False)}" if e[0] == "NOT" else f"{_tx(e[1], False)} {e[0]} {_tx(e[2], False)}"
    return inner if top else f"({inner})"


def _steps(e, env: dict[str, int]) -> list[str]:
    """Working, innermost first: 'A AND B = 1 AND 0 = 0'."""
    if isinstance(e, str):
        return []
    out = []
    for child in e[1:]:
        out += _steps(child, env)
    vals = [_ev(c, env) for c in e[1:]]
    shown = f"NOT {vals[0]}" if e[0] == "NOT" else f"{vals[0]} {e[0]} {vals[1]}"
    out.append(f"{_tx(e)} = {shown} = {_ev(e, env)}")
    return out


def _no_not(e):
    """The same expression with every NOT left out (a common slip)."""
    if isinstance(e, str):
        return e
    if e[0] == "NOT":
        return _no_not(e[1])
    return (e[0], _no_not(e[1]), _no_not(e[2]))


def _has_not(e) -> bool:
    return not isinstance(e, str) and (e[0] == "NOT" or any(_has_not(c) for c in e[1:]))


def _vars(e) -> list[str]:
    if isinstance(e, str):
        return [e]
    return sorted(set(v for c in e[1:] for v in _vars(c)))


_EXPR2 = (       # two gates
    ("NOT", ("AND", "A", "B")), ("NOT", ("OR", "A", "B")), ("AND", ("NOT", "A"), "B"),
    ("OR", "A", ("NOT", "B")), ("OR", ("AND", "A", "B"), "C"), ("AND", ("OR", "A", "B"), "C"),
    ("OR", ("NOT", "A"), "B"), ("AND", "A", ("NOT", "B")),
)
_EXPR3 = (       # three inputs, three gates
    ("OR", ("AND", "A", "B"), ("NOT", "C")), ("AND", ("OR", "A", "B"), ("NOT", "C")),
    ("OR", ("NOT", ("AND", "A", "B")), "C"), ("OR", ("AND", "A", ("NOT", "B")), "C"),
    ("NOT", ("AND", ("OR", "A", "B"), "C")), ("AND", ("OR", "A", "C"), ("OR", "B", "C")),
    ("OR", ("XOR", "A", "B"), "C"), ("AND", ("NOT", "A"), ("OR", "B", "C")),
    ("AND", ("AND", "A", "B"), ("NOT", "C")),
)


def _inputs(env: dict[str, int]) -> str:
    parts = [f"{k} = {v}" for k, v in sorted(env.items())]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def _eval_problem(rng: random.Random, e) -> Draft:
    env = {v: rng.randint(0, 1) for v in _vars(e)}
    out = _ev(e, env)
    ms = []
    if _has_not(e) and _ev(_no_not(e), env) != out:
        ms.append(_num_mis(_ev(_no_not(e), env), "Don't forget to apply the NOT"))
    if e in (("OR", ("AND", "A", "B"), "C"), ("AND", ("OR", "A", "B"), "C")):
        alt = (e[1][0], "A", (e[0], "B", "C"))           # brackets in the wrong place
        if _ev(alt, env) != out:
            ms.append(_num_mis(_ev(alt, env), "Work out the bracket first, then the gate outside it"))
    return _q(f"Q = {_tx(e)}. Work out Q when {_inputs(env)}. {_BIT}", _num(out),
              "Work from the inside out: " + "; ".join(_steps(e, env)) + f", so Q = {out}",
              "Work from the innermost brackets outwards, writing down each result", ms)


def _lg_1(rng: random.Random) -> Draft:
    """One gate (number 0/1)."""
    g = rng.choice(["AND", "OR", "XOR", "NOT", "AND", "OR"])
    if g == "NOT":
        a = rng.randint(0, 1)
        return _q(f"A = {a}. What is the output of NOT A? {_BIT}", _num(1 - a),
                  f"NOT flips its input, so NOT {a} = {1 - a}", "NOT gives the opposite of its input",
                  [_num_mis(a, "NOT flips the input: 0 becomes 1 and 1 becomes 0")])
    a, b = rng.randint(0, 1), rng.randint(0, 1)
    out = _GATES[g](a, b)
    other = {"AND": "OR", "OR": "AND", "XOR": "OR"}[g]
    ms = [_num_mis(_GATES[other](a, b) if _GATES[other](a, b) != out else None, _GATE_RULE[g])]
    return _q(f"A = {a} and B = {b}. What is the output of A {g} B? {_BIT}", _num(out),
              f"{_GATE_RULE[g]}, so {a} {g} {b} = {out}",
              f"Think about the rule for an {g} gate" if g != "OR" else "Think about the rule for an OR gate", ms)


def _lg_2(rng: random.Random) -> Draft:
    """Two gates."""
    return _eval_problem(rng, rng.choice(_EXPR2))


def _lg_3(rng: random.Random) -> Draft:
    """Name the gate (choice; one ref per gate and form)."""
    g = rng.choice(["AND", "OR", "XOR", "NOT"])
    form = "table" if rng.random() < 0.6 else "desc"
    if g == "NOT":
        others = rng.sample(["AND", "OR", "XOR"], 2) + ["NAND"]
    else:
        others = rng.sample([x for x in ("AND", "OR", "XOR", "NAND", "NOR") if x != g], 3)
    options = [g] + others
    fb: list[str | None] = [None]
    if form == "table":
        if g == "NOT":
            stem = "Which logic gate has this truth table?\nA | Q\n0 | 1\n1 | 0"
            fb += [f"{o} has two inputs — this gate has only one input, and it flips it" for o in others]
        else:
            rows = "\n".join(f"{a} {b} | {_GATES[g](a, b)}" for a, b in product((0, 1), repeat=2))
            stem = f"Which logic gate has this truth table?\nA B | Q\n{rows}"
            for o in others:
                a, b = next((a, b) for a, b in product((0, 1), repeat=2) if _GATES[o](a, b) != _GATES[g](a, b))
                fb.append(f"{o} would give Q = {_GATES[o](a, b)} when A = {a} and B = {b}")
    else:
        desc = {"AND": "outputs 1 only when both of its inputs are 1",
                "OR": "outputs 1 when at least one of its inputs is 1",
                "XOR": "outputs 1 only when its two inputs are different",
                "NOT": "has one input and outputs the opposite of that input"}[g]
        stem = f"Which logic gate {desc}?"
        fb += [_GATE_RULE.get(o, f"{o} is {'NOT AND' if o == 'NAND' else 'NOT OR'}: it gives the opposite of {o[1:]}")
               for o in others]
    sol = f"This is the {g} gate: it {_GATE_RULE[g].split(' ', 1)[1]}"
    return _choice(stem, options, 0, sol,
                   "Check each row: when is the output on?" if form == "table" else
                   "Picture the truth table for each gate", fb, ref=f"{form}_{g}")


def _lg_4(rng: random.Random) -> Draft:
    """A 3-input expression."""
    return _eval_problem(rng, rng.choice(_EXPR3))


def _lg_5(rng: random.Random) -> Draft:
    """How many rows of a truth table give Q = 1."""
    if rng.random() < 0.35:
        e = rng.choice([x for x in _EXPR2 if "C" not in _vars(x)])
    else:
        e = rng.choice(_EXPR3)
    names = _vars(e)
    rows = list(product((0, 1), repeat=len(names)))
    ones = [r for r in rows if _ev(e, dict(zip(names, r)))]
    count, n = len(ones), len(rows)
    ins = "two inputs A and B" if len(names) == 2 else "three inputs A, B and C"
    listed = "; ".join("".join(map(str, r)) for r in ones) if ones else "none"
    return _q(f"Q = {_tx(e)}, with {ins}. The truth table has {n} rows. In how many rows is Q = 1?", _num(count),
              f"Check every row ({''.join(names)}). Q = 1 for {listed}: {count} row{'s' if count != 1 else ''}",
              "List every combination of inputs and work out Q for each row",
              [_num_mis(n - count if n - count != count else None, "That's the number of rows where Q = 0")])


# ============================================================== registration

def _skill(name: str, title: str, aliases: tuple[str, ...],
           levels: tuple[Callable[[random.Random], Draft], ...], fallback: str) -> Skill:
    sid = f"{SUBJECT_ID}.{name}"
    if len(levels) != 5:
        raise ValueError(f"{sid}: needs 5 levels")

    def generate(level: int, seed: int) -> Problem:
        check_level(level)
        rng = random.Random(seed)
        d = dict(levels[level - 1](rng))
        ref = d.pop("ref", "")
        level_fallback = d.pop("fallback", "") or fallback   # a problem whose method differs gives its own
        ch = d.pop("choice", None)
        sh = d.pop("short", None)
        if ch is not None:
            stem, options, correct, feedback = ch
            text, answer, ms = build_choice(stem, options, correct, seed, feedback)
            d.update(text=text, answer=answer, mistakes=list(ms))
        elif sh is not None:
            accept, reject, form, feedback = sh
            answer, ms = build_short(accept, reject, form, feedback)
            d.update(answer=answer, mistakes=list(ms) + list(d.get("mistakes", [])))
        p = build(sid, level, seed, fallback_hint=level_fallback, **d)
        return replace(p, ref=f"{sid}#{ref}") if ref else p

    generate.__name__ = f"generate_{name}"
    generate.__qualname__ = generate.__name__
    return Skill(id=sid, subject=SUBJECT_ID, title=title, aliases=aliases, generate=generate)


GEN_SKILLS: tuple[Skill, ...] = (
    _skill("binary", "Binary & hexadecimal",
           ("binary conversion", "binary", "denary", "hexadecimal", "hex", "binary addition", "binary shift",
            "binary shifts", "overflow", "nibble"),
           (_bi_1, _bi_2, _bi_3, _bi_4, _bi_5),
           "Write out the binary place values first, doubling from the right"),
    _skill("data_units", "Data units & file sizes",
           ("file size", "image file size", "sound file size", "bits and bytes", "colour depth", "sample rate",
            "data units", "kilobytes", "megabytes", "file sizes"),
           (_du_1, _du_2, _du_3, _du_4, _du_5),
           "Work in bits first, then divide by 8 for bytes and by 1000 for each bigger unit"),
    _skill("logic", "Logic gates & truth tables",
           ("logic gates", "truth table", "boolean logic", "and gate", "or gate", "not gate", "xor",
            "truth tables", "logic gate", "boolean"),
           (_lg_1, _lg_2, _lg_3, _lg_4, _lg_5),
           "AND needs both inputs on, OR needs at least one input on, NOT flips its input"),
)

_ROWS = (
    (("data_rep", "Data representation", ("binary", "data_units")),
     ("systems", "Computer systems", ("systems",))),
    (("networks", "Networks & security", ("networks",)),
     ("algorithms", "Algorithms & programming", ("algorithms", "logic"))),
)
_ORDER = ("binary", "data_units", "systems", "networks", "algorithms", "logic")


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"{SUBJECT_ID}.y{y}.{slug}", label=label,
                    skills=tuple(f"{SUBJECT_ID}.{s}" for s in skills), level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Computer Science", order=26, years={10: _year(10), 11: _year(11)})


def all_skills() -> list[Skill]:
    """Generator skills plus the bank skills from packs/computer_science.json, in topic order."""
    by_id = {sk.id: sk for sk in GEN_SKILLS}
    for sk in load_pack("computer_science", SUBJECT_ID):
        by_id[sk.id] = sk
    ordered = [by_id.pop(f"{SUBJECT_ID}.{n}") for n in _ORDER if f"{SUBJECT_ID}.{n}" in by_id]
    return ordered + list(by_id.values())


def register(reg) -> None:
    """Register Computer Science (generators + pack) with a tutor.content Registry."""
    reg.register(make_subject(), all_skills())
