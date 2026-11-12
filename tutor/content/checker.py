"""Answer checker (docs/ARCHITECTURE.md section 2.3).

``check(answer, text, mistakes)`` returns a Verdict with one of four
statuses: correct, wrong, unparsed, unmarkable.  Text that does not contain
an answer is never marked wrong.
"""
from __future__ import annotations

import functools
import math
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Iterator, Sequence

from .base import Answer, Mistake
from . import mathexpr

FORM_STANDARD = "That's the right value, but it needs to be in standard form (a × 10^n, with 1 ≤ a < 10)"
FORM_FACTORISED = "That's equivalent, but the question asks you to factorise — write it as brackets multiplied together"
FORM_EXPANDED = "That's equivalent, but the question asks you to expand — multiply out all the brackets"
FORM_SIMPLEST = "That's equivalent, but it isn't in its simplest form yet"
FORM_MIXED = "That's equivalent, but the question asks for a mixed number (a whole number and a fraction, like 2 1/3)"
FORM_FRACTION = "That's close, but the question asks for an exact fraction, not a rounded decimal"
FORM_UNIT = "Check your units — the answer should be in {unit}"

MAX_TEXT = 2000
REL_TOL = 1e-9          # exact answers (no dp / sf): |v - exact| <= REL_TOL * |exact|
ZERO_TOL = 1e-12        # ... and |v| <= ZERO_TOL when the exact answer is 0


@dataclass(frozen=True)
class Verdict:
    status: str          # "correct" | "wrong" | "unparsed" | "unmarkable"
    feedback: str = ""   # for "wrong": form-violation text or matched Mistake.feedback; "" otherwise


_CORRECT = Verdict("correct")
_UNPARSED = Verdict("unparsed")
_UNMARKABLE = Verdict("unmarkable")
_WRONG = Verdict("wrong")


# ------------------------------------------------------------ text helpers

_SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
        "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁻": "-", "⁺": "+"}
_SUP_RUN = re.compile("[" + "".join(_SUP) + "]+")
_VULGAR = {"½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4", "⅕": "1/5", "⅖": "2/5",
           "⅗": "3/5", "⅘": "4/5", "⅙": "1/6", "⅚": "5/6", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"}

_PREFIX = re.compile(
    r"^\s*(?:(?:the|my|final)\s+)*(?:answers?|ans|so|therefore|thus|hence)\b\s*(?:is|are|=|:|-(?=\s))?\s*",
    re.IGNORECASE,
)
# a line that only checks / verifies an answer given above it
_VERIFY_LINE = re.compile(r"^\W*(?:check(?:ing)?|verify(?:ing)?|substitut\w*|sub)\b", re.IGNORECASE)
# working after the answer on the same line: "x = 4, check: 3(4) + 5 = 17", "x = 4 because 12/3"
_CUT = re.compile(r"[,;]?\s*\(?\b(?:check(?:ing)?|because|coz|since)\b", re.IGNORECASE)   # not "cos": trig
# "... so x = 4": the answer is after the last connector
_CONNECT = re.compile(r"\b(?:so|therefore|thus|hence)\b|=>|⇒", re.IGNORECASE)
_PAREN_NOTE = re.compile(r"\s*\(([^()]*)\)\s*$")
_ROUND_NOTE = re.compile(
    r"(?:\s+(?:(?:correct|rounded|accurate)\s+)?to\s+|\s+|^)(?:\d+|one|two|three|four)\s*"
    r"(?:d\.?\s*p\.?|s\.?\s*f\.?|decimal\s+places?|significant\s+fig(?:ure)?s?|sig\.?\s*figs?)\s*\.?\s*$",
    re.IGNORECASE)
_SMILEY = re.compile(r"(?:(?:^|\s+)(?:[:;]-?[)(DPp]|<3|xD|XD)|\s*\b(?:lol|lmao|haha|hehe|pls|please)\b)\s*$")
_PM = re.compile(r"\+\s*/\s*-|\+\s*-(?=\s*\d)")


def _normalise(s: str) -> str:
    s = s.replace("−", "-").replace("–", "-").replace("‒", "-").replace(" ", " ")
    s = s.replace("’", "'").replace("º", "°").replace("˚", "°").replace("＝", "=")
    for k, v in _VULGAR.items():
        if k in s:
            s = re.sub(rf"(?<=\d){k}", " " + v, s).replace(k, v)
    return s


def _superscripts_to_caret(s: str) -> str:
    return _SUP_RUN.sub(lambda m: "^(" + "".join(_SUP[c] for c in m.group()) + ")", s)


def _lines(text: str) -> list[str]:
    text = _normalise((text or "")[:MAX_TEXT])
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _has_digit(s: str) -> bool:
    return re.search(r"\d", s) is not None


def _strip_prefix(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = _PREFIX.sub("", s, count=1)
    return s.strip()


def _strip_junk(s: str) -> str:
    """Remove trailing punctuation, ticks, emoji and smileys."""
    prev = None
    while prev != s:
        prev = s
        s = _SMILEY.sub("", s)
        while s:
            c = s[-1]
            cat = unicodedata.category(c)
            if c in " \t.,;!?" or (cat in ("So", "Sk", "Mn", "Cf", "Co") and c not in "°^"):
                s = s[:-1]
                continue
            break
    return s.strip()


def _clean_line(line: str, kind: str, has_content=_has_digit) -> str:
    """Remove what follows an answer on its line: checks, reasons, rounding notes, ticks."""
    m = _CUT.search(line)
    if m and m.start() > 0 and has_content(line[:m.start()]):
        line = line[:m.start()]
    if kind in ("number", "fraction", "set", "expr"):
        parts = _CONNECT.split(line)
        if len(parts) > 1 and has_content(parts[-1]):
            line = parts[-1]
    prev = None
    while prev != line:
        prev = line
        line = _strip_junk(line)
        m = _PAREN_NOTE.search(line)
        if m and has_content(line[:m.start()]):
            inner = m.group(1)
            note = re.search(r"[A-Za-z]{3,}", inner) if kind == "expr" else re.search(r"[A-Za-z]", inner)
            if note:
                line = line[:m.start()]
        m = _ROUND_NOTE.search(line)
        if m and m.start() > 0 and has_content(line[:m.start()]):
            line = line[:m.start()]
    return line.strip()


def _tail(line: str) -> str:
    """Text after the last '=' or '≈', with answer-prefixes and trailing punctuation removed."""
    line = _strip_prefix(line)
    cut = max(line.rfind("="), line.rfind("≈"))
    if cut >= 0:
        line = line[cut + 1:]
    line = _strip_prefix(line)
    return line.strip().rstrip(".,;!? ").strip()


# ----------------------------------------------------- phrase answer lines

_ORDINAL = re.compile(r"(?<=\d)(?:st|nd|rd|th)\b", re.IGNORECASE)
_EQUALS_WORD = re.compile(r"\bis\s+equal\s+to\b|\bequals?\b", re.IGNORECASE)
_VAR_IS = re.compile(r"(?<![A-Za-z'])([A-Za-z])\s+(?:is|was|=)\s+", re.IGNORECASE)
_FILLER = (
    "i", "i'm", "im", "i've", "ive", "i'd", "think", "reckon", "guess", "believe", "it's", "its", "it", "is",
    "was", "got", "get", "gets", "make", "makes", "made", "found", "find", "came", "out", "worked",
    "calculated", "the", "answer", "ans", "my", "final", "so", "therefore", "thus", "hence", "then",
    "which", "gives", "giving", "would", "be", "should", "must", "that", "this", "term", "about",
    "approximately", "approx", "around", "roughly", "equal", "to", "of", "value", "result", "are",
    "ok", "okay", "hmm", "um", "umm", "well", "yes", "yeah", "maybe", "probably", "pretty", "sure",
    "and", "nearly", "almost", "exactly", "just",
)
_FILLER_RE = re.compile(r"(?<![\w'])(?:" + "|".join(re.escape(w) for w in sorted(_FILLER, key=len, reverse=True))
                        + r")(?![\w'])", re.IGNORECASE)


def _phrase(line: str) -> str:
    """'so it's 4', 'I got 4', 'n = 22nd term', 'x is 4' -> a bare answer ('4', 'n = 22')."""
    s = _ORDINAL.sub("", line)
    s = _EQUALS_WORD.sub("=", s)
    s = _VAR_IS.sub(r"\1 = ", s)
    s = _FILLER_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


_SQUARE = (
    (re.compile(r"\b(?:square|sq\.?)\s+(mm|cm|m|km)\b", re.IGNORECASE), r"\1²"),
    (re.compile(r"\b(mm|cm|m|km)\s+squared\b", re.IGNORECASE), r"\1²"),
    (re.compile(r"\bcubic\s+(mm|cm|m)\b", re.IGNORECASE), r"\1³"),
    (re.compile(r"\b(mm|cm|m)\s+cubed\b", re.IGNORECASE), r"\1³"),
    (re.compile(r"(\d)\s+and\s+(\d+\s*/\s*\d+)\b"), r"\1 \2"),       # "15 and 1/9"
)


def _answer_line(text: str, has_content=_has_digit) -> str | None:
    """The answer line: the last non-empty line with content that is not a check line.

    Earlier lines are used ONLY when the lines below them have no content (no digit),
    so working above an unparsable answer is never marked.
    """
    for line in reversed(_lines(text)):
        if not has_content(line) or _VERIFY_LINE.match(line):
            continue
        return line
    return None


def _number_pieces(text: str) -> Iterator[str]:
    """Candidate answer strings for number / fraction kinds, best first (all from ONE line)."""
    line = _answer_line(text)
    if line is None:
        return
    line = _clean_line(line, "number")
    for rx, rep in _SQUARE:
        line = rx.sub(rep, line)
    yield _tail(line)
    parts = re.split(r"=|≈", line)
    if len(parts) > 1:
        for part in reversed(parts):
            part = _strip_prefix(part).strip().rstrip(".,;!? ")
            if part and not re.fullmatch(r"[A-Za-z]", part):
                yield part
    yield _tail(_phrase(line))


# --------------------------------------------------------------- numbers

_NUMTOK = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+,\d{1,2}(?!\d)|\d+(?:\.\d+)?|\.\d+)"
_UNIT_PART = r"(?![xX×]\s*\d|[eE][+-]?\d)[A-Za-zµμΩ°%]+(?:\^?\(?[+-]?\d+\)?)?"
_UNIT_END = re.compile(rf"(?<=[\d)])\s*{_UNIT_PART}(?:[/·*]{_UNIT_PART})*$")

_STD_RE = re.compile(
    rf"^(?P<m>[+-]?\s*{_NUMTOK})?\s*(?:(?:[×xX*·]|\\times)\s*)?10\s*(?:\^|\*\*)\s*\(?\s*(?P<e>[+-]?\s*\d{{1,3}})\s*\)?$"
)
_STD_RE2 = re.compile(
    rf"^(?P<m>[+-]?\s*{_NUMTOK})\s*(?:[×xX*·]|\\times)\s*10\s*(?:\^|\*\*)\s*\(?\s*(?P<e>[+-]?\s*\d{{1,3}})\s*\)?$"
)
_PI_RE = re.compile(rf"^(?P<k>[+-]?\s*{_NUMTOK})?\s*(?:π|pi|PI|Pi)$")
_MIXED_RE = re.compile(r"^(?P<s>[+-]?)\s*(?P<w>\d+)\s+(?P<n>\d+)\s*/\s*(?P<d>\d+)$")
_FRAC_RE = re.compile(rf"^(?P<s>[+-]?)\s*(?P<n>{_NUMTOK})\s*/\s*(?P<d>{_NUMTOK})$")
_PLAIN_RE = re.compile(rf"^(?P<s>[+-]?)\s*(?P<n>{_NUMTOK})$")
_SCI_RE = re.compile(r"^(?P<m>[+-]?\d+(?:\.\d+)?)[eE](?P<e>[+-]?\d{1,3})$")      # calculator "1.96E4"


def _tok_to_fraction(tok: str) -> Fraction | None:
    tok = tok.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", tok):
        tok = tok.replace(",", "")
    elif re.fullmatch(r"\d+,\d{1,2}", tok):
        tok = tok.replace(",", ".")
    try:
        return Fraction(tok)
    except (ValueError, ZeroDivisionError):
        return None


@dataclass
class _Num:
    value: float
    surface: str                       # int | decimal | frac | mixed | std | pi
    std: tuple[Decimal, int] | None = None
    frac: Fraction | None = None       # exact value for int/decimal/frac/mixed
    lowest: bool = True                # frac/mixed: written in lowest terms
    dp: int = 0                        # decimal places written (decimal surface)
    unit: str = ""                     # unit written after the number ("kJ", "cm^(2)")


def _std_num(m: re.Match, unit: str) -> _Num | None:
    mant_s = m.group("m")
    if mant_s is None:
        mant_s = "1"
    sign = -1 if mant_s.strip().startswith("-") else 1
    mf = _tok_to_fraction(mant_s.strip().lstrip("+-").strip())
    if mf is None:
        return None
    try:
        exp = int(m.group("e").replace(" ", ""))
    except ValueError:
        return None
    if abs(exp) > 300:
        return None
    mant = Decimal(mf.numerator) / Decimal(mf.denominator) * sign
    try:
        val = float(Decimal(mant).scaleb(exp))
    except (InvalidOperation, OverflowError):
        return None
    if math.isinf(val) or math.isnan(val):
        return None
    return _Num(val, "std", std=(mant, exp), unit=unit)


def _num_info(piece: str) -> _Num | None:
    if not piece or len(piece) > 80:
        return None
    s = _superscripts_to_caret(piece).strip()
    s = re.sub(r"^([+-]?)\s*[£$€]\s*", r"\1", s).strip().rstrip(".,;!? ").strip()
    if not s:
        return None
    base, unit = s, ""
    m = _UNIT_END.search(s)
    if m:
        b = s[:m.start()].rstrip()
        if b:
            base, unit = b, s[m.start():].strip()
    cands = ((s, ""), (base, unit)) if base != s else ((s, ""),)
    for cand, u in cands:
        m = _STD_RE2.match(cand) or _STD_RE.match(cand)
        if m:
            return _std_num(m, u)
        m = _PI_RE.match(cand)
        if m:
            k = m.group("k")
            if k is None:
                kv = Fraction(1)
            else:
                sign = -1 if k.strip().startswith("-") else 1
                kv = _tok_to_fraction(k.strip().lstrip("+-").strip())
                if kv is None:
                    return None
                kv *= sign
            return _Num(float(kv) * math.pi, "pi", unit=u)
    s1 = base
    m = _MIXED_RE.match(s1)
    if m:
        d = int(m.group("d"))
        if d == 0:
            return None
        w, n = int(m.group("w")), int(m.group("n"))
        val = Fraction(w) + Fraction(n, d)
        if m.group("s") == "-":
            val = -val
        return _Num(float(val), "mixed", frac=val, lowest=(math.gcd(n, d) == 1 and n < d), unit=unit)
    m = _FRAC_RE.match(s1)
    if m:
        a, b = _tok_to_fraction(m.group("n")), _tok_to_fraction(m.group("d"))
        if a is None or b is None or b == 0:
            return None
        val = a / b
        if m.group("s") == "-":
            val = -val
        simple = (a.denominator == 1 and b.denominator == 1
                  and math.gcd(a.numerator, b.numerator) == 1)
        return _Num(float(val), "frac", frac=val, lowest=simple, unit=unit)
    m = _PLAIN_RE.match(s1)
    if m:
        val = _tok_to_fraction(m.group("n"))
        if val is None:
            return None
        if m.group("s") == "-":
            val = -val
        tok = m.group("n")
        if val.denominator == 1 and "." not in tok and not re.search(r"\d,\d{1,2}$", tok):
            return _Num(float(val), "int", frac=val, unit=unit)
        dp = len(tok.split(".")[1]) if "." in tok else len(tok.split(",")[-1])
        return _Num(float(val), "decimal", frac=val, dp=dp, unit=unit)
    m = _SCI_RE.match(s1)
    if m:
        try:
            val = float(Decimal(m.group("m")).scaleb(int(m.group("e"))))
        except (InvalidOperation, OverflowError, ValueError):
            return None
        if math.isfinite(val):
            return _Num(val, "sci", unit=unit)
    return None


def _extract_num(text: str, need_frac: bool = False) -> _Num | None:
    for piece in _number_pieces(text):
        info = _num_info(piece)
        if info is not None and (not need_frac or info.frac is not None):
            return info
    return None


def parse_number(s: str) -> float | None:
    """Parse the answer in ``s`` as a number (see the formats in the architecture doc)."""
    if not isinstance(s, str):
        return None
    info = _extract_num(s)
    return info.value if info else None


def parse_fraction(s: str) -> Fraction | None:
    """Parse ``s`` as an exact Fraction (fraction, mixed number or decimal)."""
    if not isinstance(s, str):
        return None
    info = _extract_num(s, need_frac=True)
    return info.frac if info else None


def _within(v: float, exact: float, dp: int | None, sf: int | None) -> bool:
    if dp is not None:
        return abs(v - exact) <= 0.5 * 10 ** (-dp) + 1e-9
    if sf is not None and exact != 0:
        tol = 0.5 * 10 ** (math.floor(math.log10(abs(exact))) - sf + 1)
        return abs(v - exact) <= tol * (1 + 1e-9)
    if exact == 0:
        return abs(v) <= ZERO_TOL
    return abs(v - exact) <= REL_TOL * abs(exact)


def _exact_value(value: object) -> float | None:
    """Convert an Answer.value element (float | str like '1/2') to float."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, str):
        info = _num_info(value.strip())
        if info is not None:
            return info.value
    return None


# ------------------------------------------------------------------ units

_UNITS: dict[str, tuple[str, float]] = {}
_UNITS_CI: dict[str, tuple[str, float]] = {}


def _units(dim: str, factor: float, exact: tuple[str, ...], ci: tuple[str, ...] = ()) -> None:
    for u in exact:
        _UNITS[u] = (dim, factor)
    for u in ci:
        _UNITS_CI[u.lower()] = (dim, factor)


_units("energy", 1, ("J",), ("j", "joule", "joules"))
_units("energy", 1e3, ("kJ",), ("kj",))
_units("energy", 1e6, ("MJ",))
_units("energy", 1e-3, ("mJ",))
_units("power", 1, ("W",), ("w", "watt", "watts"))
_units("power", 1e3, ("kW",), ("kw",))
_units("power", 1e6, ("MW",))
_units("power", 1e-3, ("mW",))
_units("force", 1, ("N",), ("n", "newton", "newtons"))
_units("force", 1e3, ("kN",), ("kn",))
_units("force", 1e-3, ("mN",))
_units("pd", 1, ("V",), ("v", "volt", "volts"))
_units("pd", 1e3, ("kV",), ("kv",))
_units("pd", 1e-3, ("mV",))
_units("current", 1, ("A",), ("a", "amp", "amps", "ampere", "amperes"))
_units("current", 1e-3, ("mA",), ("ma", "milliamps"))
_units("current", 1e-6, ("µA", "μA", "uA"))
_units("charge", 1, ("C",), ("c", "coulomb", "coulombs"))
_units("charge", 1e-3, ("mC",))
_units("charge", 1e-6, ("µC", "μC", "uC"))
_units("resistance", 1, ("Ω",), ("ohm", "ohms"))
_units("resistance", 1e3, ("kΩ",), ("kohm", "kohms"))
_units("mass", 1, ("kg",), ("kg", "kgs", "kilogram", "kilograms"))
_units("mass", 1e-3, ("g",), ("g", "gram", "grams", "gramme", "grammes"))
_units("mass", 1e-6, ("mg",))
_units("length", 1, ("m",), ("m", "metre", "metres", "meter", "meters"))
_units("length", 1e-2, ("cm",), ("cm", "centimetre", "centimetres", "centimeter", "centimeters"))
_units("length", 1e-3, ("mm",), ("mm", "millimetre", "millimetres", "millimeter", "millimeters"))
_units("length", 1e3, ("km",), ("km", "kilometre", "kilometres", "kilometer", "kilometers"))
_units("area", 1, ("m2",), ("m2",))
_units("area", 1e-4, ("cm2",), ("cm2",))
_units("area", 1e-6, ("mm2",), ("mm2",))
_units("area", 1e6, ("km2",), ("km2",))
_units("volume", 1, ("m3",), ("m3",))
_units("volume", 1e-6, ("cm3",), ("cm3", "ml"))
_units("volume", 1e-9, ("mm3",), ("mm3",))
_units("volume", 1e-3, ("l", "L"), ("litre", "litres", "liter", "liters"))
_units("time", 1, ("s",), ("s", "sec", "secs", "second", "seconds"))
_units("time", 60, ("min",), ("min", "mins", "minute", "minutes"))
_units("time", 3600, ("h",), ("h", "hr", "hrs", "hour", "hours"))
_units("speed", 1, ("m/s",), ("m/s", "ms-1", "m/sec"))
_units("speed", 1e-2, ("cm/s",), ("cm/s",))
_units("speed", 1e3, ("km/s",), ("km/s",))
_units("speed", 1 / 3.6, ("km/h",), ("km/h", "kmh", "kph", "km/hr"))
_units("acceleration", 1, ("m/s2",), ("m/s2", "ms-2", "m/s/s"))
_units("pressure", 1, ("Pa",), ("pa", "pascal", "pascals", "n/m2"))
_units("pressure", 1e3, ("kPa",), ("kpa",))
_units("pressure", 1e4, ("N/cm2",), ("n/cm2",))
_units("density", 1000, ("g/cm3",), ("g/cm3",))
_units("density", 1, ("kg/m3",), ("kg/m3",))
_units("angle", 1, ("°",), ("°", "deg", "degree", "degrees"))


def _unit_key(u: str) -> str:
    return re.sub(r"[\s^()]", "", u)


def _unit_of(u: str) -> tuple[str, float] | None:
    key = _unit_key(u)
    if not key:
        return None
    return _UNITS.get(key) or _UNITS_CI.get(key.lower())


@functools.lru_cache(maxsize=4096)
def _display_unit(display: str) -> str:
    info = _extract_num(display)
    return info.unit if info else ""


# ----------------------------------------------------------- kind: number

def _check_number(a: Answer, text: str) -> Verdict:
    exact = _exact_value(a.value)
    if exact is None:
        return _UNMARKABLE
    info = _extract_num(text)
    if info is None:
        return _UNPARSED
    value = info.value
    want_unit = _display_unit(a.display) if info.unit else ""
    if want_unit:
        got_u, want_u = _unit_of(info.unit), _unit_of(want_unit)
        if got_u and want_u:
            if got_u[0] != want_u[0]:
                return Verdict("wrong", FORM_UNIT.format(unit=want_unit))
            value = value * got_u[1] / want_u[1]
    if not _within(value, exact, a.dp, a.sf):
        return _WRONG
    if a.form == "standard":
        if info.std is None or not (1 <= abs(info.std[0]) < 10):
            return Verdict("wrong", FORM_STANDARD)
    return _CORRECT


# --------------------------------------------------------- kind: fraction

def _is_terminating(fr: Fraction) -> bool:
    d = fr.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def _check_fraction(a: Answer, text: str) -> Verdict:
    try:
        exact = Fraction(str(a.value).strip())
    except (ValueError, ZeroDivisionError):
        return _UNMARKABLE
    info = _extract_num(text, need_frac=True)
    if info is None:
        return _UNPARSED
    fr = info.frac
    form = a.form
    if fr == exact:
        if form in ("simplest", "mixed"):
            if info.surface in ("frac", "mixed") and not info.lowest:
                return Verdict("wrong", FORM_SIMPLEST)
        if form == "simplest" and info.surface == "decimal":
            return Verdict("wrong", FORM_SIMPLEST)
        if form == "mixed" and exact.denominator != 1:
            if abs(exact) > 1 and info.surface != "mixed":
                return Verdict("wrong", FORM_MIXED)
            if info.surface == "decimal":
                return Verdict("wrong", FORM_MIXED)
        if form == "mixed" and exact.denominator == 1 and info.surface == "decimal":
            return Verdict("wrong", FORM_SIMPLEST)
        return _CORRECT
    # rounded decimal for a non-terminating value
    if (info.surface == "decimal" and info.dp >= 2 and not _is_terminating(exact)
            and abs(fr - exact) <= Fraction(1, 2 * 10 ** info.dp)):
        if form in ("simplest", "mixed"):
            return Verdict("wrong", FORM_FRACTION)
        return _CORRECT
    return _WRONG


# ------------------------------------------------------ kinds: set, assign

_SEP_SPLIT = re.compile(r"\s*(?:,|;|&|\band\b|\bor\b)\s*", re.IGNORECASE)
_SEP_SPLIT_ORDERED = re.compile(r"\s*(?:,|;|&|:|\band\b|\bor\b)\s*", re.IGNORECASE)
_LABEL = re.compile(r"^[A-Za-z][A-Za-z']*\d?(?:\s+[A-Za-z][A-Za-z']*){0,3}$")
_LABEL_WORDS = re.compile(r"^((?:[A-Za-z][A-Za-z']*\d?\s+){1,4})(?=[£$€+\-±.\d])")
_LABEL_VERB = re.compile(r"\s+(?:is|gets|got|has|equals|was)$", re.IGNORECASE)
_ASSIGN_RE = re.compile(r"([A-Za-z])\s*=\s*([+-]?\s*\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)")
_OPS = "+-*/×÷^=−·"

Pair = tuple  # (label | None, value)


def _parse_part(part: str) -> list[Pair] | None:
    part = part.strip().strip("{}[]").strip()
    if not part:
        return []
    label = None
    if "=" in part:
        segs = part.split("=")
        lhs = segs[0].strip()
        if not _LABEL.match(lhs) or any(re.search(r"[A-Za-z]", m) for m in segs[1:-1]):
            return None
        label, part = lhs, segs[-1].strip()
    else:
        m = _LABEL_WORDS.match(part)
        if m:
            label = _LABEL_VERB.sub("", m.group(1).strip()) or None
            part = part[m.end():]
    part = part.strip()
    pm = part.startswith("±")
    if pm:
        part = part[1:].strip()
    info = _num_info(part)
    if info is None:
        return None
    if pm:
        return [(label, info.value), (label, -info.value)]
    return [(label, info.value)]


def _parse_values_line(line: str, ordered: bool) -> list[Pair] | None:
    """Values of an answer line ('x = 2 or x = -3', '£20 and £30', '(3, -1)', 'x = ±8'); None if not one."""
    line = _strip_prefix(line)
    line = _PM.sub("±", line)
    line = line.strip().strip("{}[]").strip()
    if line.startswith("(") and line.endswith(")") and line.count("(") == 1:
        line = line[1:-1]
    line = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "\x00", line)
    splitter = _SEP_SPLIT_ORDERED if ordered else _SEP_SPLIT
    out: list[Pair] = []
    for part in splitter.split(line):
        got = _parse_part(part.replace("\x00", ","))
        if got is None:
            return None
        out += got
    return out or None


def _answer_block(text: str, ordered: bool, enough) -> list[Pair]:
    """Values from the bottom-most run of answer lines.

    Working and check lines BELOW the answer ('check: 2x + y = 5', '3 + y = 2') are
    skipped; the run stops at the first working line above it, or as soon as
    ``enough(values)`` is true.
    """
    block: list[list[Pair]] = []
    for line in reversed(_lines(text)):
        if not _has_digit(line):
            continue
        if _VERIFY_LINE.match(line):
            if block:
                break
            continue
        vals = _parse_values_line(_clean_line(line, "set"), ordered)
        if vals is None:
            if block:
                break
            continue
        block.insert(0, vals)
        if enough([v for b in block for v in b]):
            break
    return [v for b in block for v in b]


def _explicit_assignments(text: str) -> list[Pair]:
    """'var = number' assignments whose left side is a bare letter and right side a bare number."""
    out: list[Pair] = []
    for line in _lines(text):
        if _VERIFY_LINE.match(line):
            continue
        line = _clean_line(line, "assign")      # no "so ..." cut: 'so x = 6. Then ... so y = 3' keeps both
        for m in _ASSIGN_RE.finditer(line):
            start = m.start(1)
            if start > 0 and (line[start - 1].isalnum() or line[start - 1] in "_.)"):
                continue
            before = line[:start].rstrip()
            if before and before[-1] in _OPS:
                continue
            after = line[m.end(2):]
            if after[:1] and (after[0].isalnum() or after[0] in "(^²³_"
                              or (after[0] == "." and after[1:2].isdigit())):
                continue
            nxt = after.lstrip()[:1]
            if nxt and nxt in _OPS:
                continue
            info = _num_info(m.group(2).replace(" ", ""))
            if info is not None:
                out.append((m.group(1), info.value))
    return out


def _match_multiset(got: list[float], want: list[float], dp: int | None) -> bool:
    if len(got) != len(want):
        return False
    remaining = list(got)
    for w in want:
        for i, g in enumerate(remaining):
            if _within(g, w, dp, None):
                del remaining[i]
                break
        else:
            return False
    return True


def _check_set(a: Answer, text: str) -> Verdict:
    if not isinstance(a.value, (list, tuple)) or not a.value:
        return _UNMARKABLE
    want = [_exact_value(v) for v in a.value]
    if any(w is None for w in want):
        return _UNMARKABLE
    n = len(want)
    got = [v for _, v in _answer_block(text, a.ordered, lambda vals: len(vals) >= n)]
    if not got:
        got = [v for _, v in _explicit_assignments(text)][-n:]
    if not got:
        return _UNPARSED
    if a.ordered:
        ok = len(got) == n and all(_within(g, w, a.dp, None) for g, w in zip(got, want))
    else:
        ok = _match_multiset(got, want, a.dp)
    return _CORRECT if ok else _WRONG


def _check_assign(a: Answer, text: str) -> Verdict:
    if not isinstance(a.value, dict) or not a.value:
        return _UNMARKABLE
    want = {k: _exact_value(v) for k, v in a.value.items()}
    if any(v is None for v in want.values()):
        return _UNMARKABLE
    names = sorted(want)

    def assigned(pairs: list[Pair]) -> dict[str, float] | None:
        got: dict[str, float] = {}
        loose: list[float] = []
        for label, val in pairs:
            key = (label or "").strip()
            key = key if key in want else key.lower() if key.lower() in want else None
            if key is None:
                if not label:
                    loose.append(val)
                continue
            got.setdefault(key, val)
        missing = [k for k in names if k not in got]
        if missing and len(loose) == len(missing):
            got.update(zip(missing, loose))
        return got if all(k in got for k in names) else None

    block = _answer_block(text, False, lambda vals: assigned(vals) is not None)
    got = assigned(block)
    if got is None:
        last: dict[str, float] = {}
        for var, val in _explicit_assignments(text):
            last[var] = val
        if all(k in last for k in names):
            got = {k: last[k] for k in names}
    if got is None:
        return _WRONG if block or _explicit_assignments(text) else _UNPARSED
    ok = all(_within(got[k], want[k], a.dp, None) for k in want)
    return _CORRECT if ok else _WRONG


# ------------------------------------------------------------- kind: expr

def _expr_has_content(var: str):
    rx = re.compile(rf"\d|(?<![A-Za-z]){re.escape(var)}(?![A-Za-z])", re.IGNORECASE)
    return lambda s: rx.search(s) is not None


def _expr_normalise(s: str, var: str) -> str:
    up = var.upper()
    if up != var:
        s = re.sub(rf"(?<![A-Za-z]){up}(?![A-Za-z])", var, s)          # "X² + 9x" -> "x² + 9x"
    return re.sub(rf"(?<![A-Za-z]){var}([23])(?![\d.])", rf"{var}^\1", s)   # "x2" -> "x^2"


def _form_problem(a: Answer, expr: str) -> str:
    if a.form == "expanded":
        if not mathexpr.is_expanded(expr, a.var):
            return FORM_EXPANDED
        if not mathexpr.is_simplified(expr, a.var):
            return FORM_SIMPLEST
    if a.form == "factorised" and not mathexpr.is_factorised(expr, a.var):
        return FORM_FACTORISED
    return ""


def _check_expr(a: Answer, text: str) -> Verdict:
    if not isinstance(a.value, str) or not a.var:
        return _UNMARKABLE
    try:
        mathexpr.parse(a.value, a.var)
    except mathexpr.ExprError:
        return _UNMARKABLE
    content = _expr_has_content(a.var)
    line = _answer_line(text, content)
    if line is None:
        return _UNPARSED
    line = _expr_normalise(_clean_line(line, "expr", content), a.var)
    has_var = re.compile(rf"(?<![A-Za-z]){re.escape(a.var)}").search
    cands: list[tuple[str, bool]] = []
    for part in re.split(r"=|≈", line):
        p = _strip_prefix(part).strip().rstrip(".,;!? ").strip()
        if not p or not has_var(p):
            continue
        eq = mathexpr.equivalent(p, a.value, a.var)
        if eq is not None:
            cands.append((p, eq))
    if not cands:
        return _UNPARSED
    for p, eq in cands:
        if eq and not _form_problem(a, p):
            return _CORRECT
    p, eq = cands[-1]
    if not eq:
        return _WRONG
    return Verdict("wrong", _form_problem(a, p))


# ------------------------------------------------------------ kind: ratio

_RATIO_RE = re.compile(r"(?<![\d.])\d+(?:\s*:\s*\d+)+(?![\d.])")


def _check_ratio(a: Answer, text: str) -> Verdict:
    if not isinstance(a.value, (list, tuple)) or len(a.value) < 2:
        return _UNMARKABLE
    try:
        want = [int(v) for v in a.value]
    except (TypeError, ValueError):
        return _UNMARKABLE
    if any(w <= 0 for w in want):
        return _UNMARKABLE
    got: list[int] | None = None
    for line in reversed(_lines(text)):
        if _VERIFY_LINE.match(line):
            continue
        found = _RATIO_RE.findall(line)
        if found:
            got = [int(x) for x in re.split(r"\s*:\s*", found[-1])]
            break
    if got is None:
        return _UNPARSED
    if len(got) != len(want) or any(g <= 0 for g in got):
        return _WRONG
    if got == want:
        return _CORRECT
    if any(g * want[0] != got[0] * w for g, w in zip(got, want)):
        return _WRONG
    # proportional but different parts
    g = 0
    for x in got:
        g = math.gcd(g, x)
    if a.form == "simplest" and g != 1:
        return Verdict("wrong", FORM_SIMPLEST)
    return _CORRECT


# -------------------------------------------------------------- dispatcher

_KINDS = {
    "number": _check_number,
    "fraction": _check_fraction,
    "set": _check_set,
    "assign": _check_assign,
    "expr": _check_expr,
    "ratio": _check_ratio,
}


def _check_core(answer: Answer, text: str) -> Verdict:
    if answer.kind == "rubric":
        return _UNMARKABLE
    fn = _KINDS.get(answer.kind)
    if fn is None:
        return _UNMARKABLE
    if not isinstance(text, str):
        text = ""
    return fn(answer, text)


def check(answer: Answer, text: str, mistakes: Sequence[Mistake] = ()) -> Verdict:
    v = _check_core(answer, text)
    if v.status == "wrong" and not v.feedback:
        for m in mistakes:
            if _check_core(m.answer, text).status == "correct":
                return Verdict("wrong", m.feedback)
    return v
