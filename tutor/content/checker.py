"""Answer checker (docs/ARCHITECTURE.md section 2.3).

``check(answer, text, mistakes)`` returns a Verdict with one of four
statuses: correct, wrong, unparsed, unmarkable.  Text that does not contain
an answer is never marked wrong.
"""
from __future__ import annotations

import math
import re
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

MAX_TEXT = 2000


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

_PREFIX = re.compile(
    r"^\s*(?:(?:the|my|final)\s+)*(?:answers?|ans|so|therefore|thus|hence)\b\s*(?:is|are|=|:|-)?\s*",
    re.IGNORECASE,
)


def _normalise(s: str) -> str:
    s = s.replace("−", "-").replace("–", "-").replace("‒", "-").replace(" ", " ")
    s = s.replace("’", "'")
    return s


def _superscripts_to_caret(s: str) -> str:
    return _SUP_RUN.sub(lambda m: "^(" + "".join(_SUP[c] for c in m.group()) + ")", s)


def _lines(text: str) -> list[str]:
    text = _normalise((text or "")[:MAX_TEXT])
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _strip_prefix(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = _PREFIX.sub("", s, count=1)
    return s.strip()


def _tail(line: str) -> str:
    """Text after the last '=' or '≈', with answer-prefixes and trailing punctuation removed."""
    line = _strip_prefix(line)
    cut = max(line.rfind("="), line.rfind("≈"))
    if cut >= 0:
        line = line[cut + 1:]
    line = _strip_prefix(line)
    return line.strip().rstrip(".,;!? ").strip()


def _pieces(text: str) -> Iterator[str]:
    """Candidate answer pieces: last line first, then earlier lines."""
    for line in reversed(_lines(text)):
        piece = _tail(line)
        if piece:
            yield piece


# --------------------------------------------------------------- numbers

_NUMTOK = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+,\d{1,2}(?!\d)|\d+(?:\.\d+)?|\.\d+)"
_UNIT_PART = r"[A-Za-zµΩ°%]+(?:\^\(?[+-]?\d+\)?)?"
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


def _strip_currency_unit(piece: str) -> str | None:
    """Remove currency symbols and a trailing unit.  None if a unit-like tail is malformed."""
    s = _superscripts_to_caret(piece).strip()
    s = re.sub(r"^([+-]?)\s*[£$€]\s*", r"\1", s)
    s = s.rstrip(".,;!? ").strip()
    m = _UNIT_END.search(s)
    if m:
        base = s[:m.start()].rstrip()
        if not base:
            return None
        s = base
    return s


@dataclass
class _Num:
    value: float
    surface: str                       # int | decimal | frac | mixed | std | pi
    std: tuple[Decimal, int] | None = None
    frac: Fraction | None = None       # exact value for int/decimal/frac/mixed
    lowest: bool = True                # frac/mixed: written in lowest terms
    dp: int = 0                        # decimal places written (decimal surface)


def _num_info(piece: str) -> _Num | None:
    if not piece or len(piece) > 80:
        return None
    s = _superscripts_to_caret(piece)
    # standard form (before unit stripping so '10^4 m' still works through the unit pass below)
    s0 = re.sub(r"^([+-]?)\s*[£$€]\s*", r"\1", s).strip().rstrip(".,;!? ").strip()
    for cand in (s0, _strip_currency_unit(piece)):
        if not cand:
            continue
        m = _STD_RE2.match(cand) or _STD_RE.match(cand)
        if m:
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
            return _Num(val, "std", std=(mant, exp))
    m = _PI_RE.match(s0)
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
        return _Num(float(kv) * math.pi, "pi")
    s1 = _strip_currency_unit(piece)
    if s1 is None or not s1:
        return None
    m = _MIXED_RE.match(s1)
    if m:
        d = int(m.group("d"))
        if d == 0:
            return None
        w, n = int(m.group("w")), int(m.group("n"))
        val = Fraction(w) + Fraction(n, d)
        if m.group("s") == "-":
            val = -val
        return _Num(float(val), "mixed", frac=val, lowest=(math.gcd(n, d) == 1 and n < d))
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
        return _Num(float(val), "frac", frac=val, lowest=simple)
    m = _PLAIN_RE.match(s1)
    if m:
        val = _tok_to_fraction(m.group("n"))
        if val is None:
            return None
        if m.group("s") == "-":
            val = -val
        tok = m.group("n")
        if val.denominator == 1 and "." not in tok and not re.search(r"\d,\d{1,2}$", tok):
            return _Num(float(val), "int", frac=val)
        dp = len(tok.split(".")[1]) if "." in tok else len(tok.split(",")[-1])
        return _Num(float(val), "decimal", frac=val, dp=dp)
    return None


def parse_number(s: str) -> float | None:
    """Parse the answer in ``s`` as a number (see the formats in the architecture doc)."""
    if not isinstance(s, str):
        return None
    for piece in _pieces(s):
        info = _num_info(piece)
        if info is not None:
            return info.value
    return None


def parse_fraction(s: str) -> Fraction | None:
    """Parse ``s`` as an exact Fraction (fraction, mixed number or decimal)."""
    if not isinstance(s, str):
        return None
    for piece in _pieces(s):
        info = _num_info(piece)
        if info is not None and info.frac is not None:
            return info.frac
    return None


def _within(v: float, exact: float, dp: int | None, sf: int | None) -> bool:
    if dp is not None:
        return abs(v - exact) <= 0.5 * 10 ** (-dp) + 1e-9
    if sf is not None and exact != 0:
        tol = 0.5 * 10 ** (math.floor(math.log10(abs(exact))) - sf + 1)
        return abs(v - exact) <= tol * (1 + 1e-9) + 1e-12
    return abs(v - exact) <= 1e-6 * max(1.0, abs(exact))


def _exact_value(value: object) -> float | None:
    """Convert an Answer.value element (float | str like '1/2') to float."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        info = _num_info(value.strip())
        if info is not None:
            return info.value
    return None


# ----------------------------------------------------------- kind: number

def _check_number(a: Answer, text: str) -> Verdict:
    exact = _exact_value(a.value)
    if exact is None:
        return _UNMARKABLE
    info = None
    for piece in _pieces(text):
        info = _num_info(piece)
        if info is not None:
            break
    if info is None:
        return _UNPARSED
    if not _within(info.value, exact, a.dp, a.sf):
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
    info = None
    for piece in _pieces(text):
        cand = _num_info(piece)
        if cand is not None and cand.frac is not None:
            info = cand
            break
    if info is None:
        return _UNPARSED
    fr = info.frac
    simplest = a.form == "simplest"
    if fr == exact:
        if simplest:
            if info.surface == "decimal":
                return Verdict("wrong", FORM_SIMPLEST)
            if info.surface in ("frac", "mixed") and not info.lowest:
                return Verdict("wrong", FORM_SIMPLEST)
        return _CORRECT
    # rounded decimal for a non-terminating value
    if (info.surface == "decimal" and info.dp >= 2 and not _is_terminating(exact)
            and abs(fr - exact) <= Fraction(1, 2 * 10 ** info.dp)):
        if simplest:
            return Verdict("wrong", FORM_SIMPLEST)
        return _CORRECT
    return _WRONG


# ------------------------------------------------------ kinds: set, assign

_SEP_SPLIT = re.compile(r"\s*(?:,|;|&|\band\b|\bor\b)\s*", re.IGNORECASE)
_SEP_SPLIT_ORDERED = re.compile(r"\s*(?:,|;|&|:|\band\b|\bor\b)\s*", re.IGNORECASE)
_VAR_NUM = re.compile(
    r"(?<![A-Za-z])(?P<v>[A-Za-z])\s*=\s*(?P<n>[+-]?\s*\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)"
)


def _num_from_piece(piece: str) -> float | None:
    piece = piece.strip()
    if "=" in piece:
        piece = piece[piece.rfind("=") + 1:]
    piece = _strip_prefix(piece).strip().rstrip(".,;!? ").strip()
    piece = piece.strip("(){}[] ")
    info = _num_info(piece)
    return info.value if info else None


def _line_numbers(line: str, ordered: bool) -> list[float] | None:
    line = _strip_prefix(line)
    line = line.strip().strip("{}[]").strip()
    # a line like "(3, -1)": drop one pair of enclosing parentheses
    if line.startswith("(") and line.endswith(")") and line.count("(") == 1:
        line = line[1:-1]
    # protect thousands separators ("1,200")
    line = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "\x00", line)
    splitter = _SEP_SPLIT_ORDERED if ordered else _SEP_SPLIT
    out: list[float] = []
    for part in splitter.split(line):
        part = part.replace("\x00", ",")
        if not part.strip():
            continue
        v = _num_from_piece(part)
        if v is None:
            return None
        out.append(v)
    return out or None


def _regex_pairs(text: str) -> list[tuple[str, float]]:
    out = []
    for m in _VAR_NUM.finditer(_normalise((text or "")[:MAX_TEXT])):
        info = _num_info(m.group("n").replace(" ", ""))
        if info is not None:
            out.append((m.group("v"), info.value))
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
    got: list[float] | None = None
    seen_any = False
    for line in reversed(_lines(text)):
        nums = _line_numbers(line, a.ordered)
        if nums is None:
            continue
        seen_any = True
        if len(nums) == n:
            got = nums
            break
    if got is None:
        pairs = _regex_pairs(text)
        if pairs:
            seen_any = True
        if len(pairs) >= n:
            got = [v for _, v in pairs[-n:]]
    if got is None:
        return _WRONG if seen_any else _UNPARSED
    if a.ordered:
        ok = all(_within(g, w, a.dp, None) for g, w in zip(got, want))
    else:
        ok = _match_multiset(got, want, a.dp)
    return _CORRECT if ok else _WRONG


def _check_assign(a: Answer, text: str) -> Verdict:
    if not isinstance(a.value, dict) or not a.value:
        return _UNMARKABLE
    want = {k: _exact_value(v) for k, v in a.value.items()}
    if any(v is None for v in want.values()):
        return _UNMARKABLE
    pairs = _regex_pairs(text)
    last: dict[str, float] = {}
    for var, val in pairs:
        last[var] = val
    got: dict[str, float] | None = None
    if all(v in last for v in want):
        got = {v: last[v] for v in want}
    else:
        names = sorted(want)
        for line in reversed(_lines(text)):
            nums = _line_numbers(line, False)
            if nums is not None and len(nums) == len(names):
                got = dict(zip(names, nums))
                break
    if got is None:
        has_number = bool(pairs) or any(
            _line_numbers(ln, False) is not None for ln in _lines(text))
        return _WRONG if has_number else _UNPARSED
    ok = all(_within(got[k], want[k], a.dp, None) for k in want)
    return _CORRECT if ok else _WRONG


# ------------------------------------------------------------- kind: expr

def _check_expr(a: Answer, text: str) -> Verdict:
    if not isinstance(a.value, str) or not a.var:
        return _UNMARKABLE
    try:
        mathexpr.parse(a.value, a.var)
    except mathexpr.ExprError:
        return _UNMARKABLE
    for piece in _pieces(text):
        eq = mathexpr.equivalent(piece, a.value, a.var)
        if eq is None:
            continue
        if not eq:
            return _WRONG
        if a.form == "expanded" and not mathexpr.is_expanded(piece, a.var):
            return Verdict("wrong", FORM_EXPANDED)
        if a.form == "factorised" and not mathexpr.is_factorised(piece, a.var):
            return Verdict("wrong", FORM_FACTORISED)
        return _CORRECT
    return _UNPARSED


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
