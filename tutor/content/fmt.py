"""Private helpers for subject generators (not part of the tutor.content API).

Number formatting and rounding (half-up, decided on exact values), standard
form, fractions, polynomials, degree-based trig, and ``build()`` — the single
place where a generated problem is validated and its mistakes are filtered
through the real checker (docs/ARCHITECTURE.md section 5, general rules).
"""
from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from typing import Iterable, Union

from .base import Answer, Mistake, Problem

Number = Union[int, float, Fraction, Decimal]

MAX_TEXT = 600
MAX_SOLUTION = 300
DEFAULT_HINT = "Write down what you know, then take it one step at a time"
MAX_TRIES = 50

_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
        "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻"}


# ------------------------------------------------------------- decimals

def dec(x: Number) -> Decimal:
    """Exact-ish Decimal for int / Fraction (exact to 40 digits) / float (12 s.f.)."""
    if isinstance(x, bool):
        raise TypeError("bool is not a number here")
    if isinstance(x, Decimal):
        return x
    if isinstance(x, int):
        return Decimal(x)
    if isinstance(x, Fraction):
        with localcontext() as ctx:
            ctx.prec = 40
            return Decimal(x.numerator) / Decimal(x.denominator)
    if isinstance(x, float):
        if not math.isfinite(x):
            raise ValueError(f"not a finite number: {x!r}")
        return Decimal(format(x, ".12g"))
    raise TypeError(f"unsupported number type: {type(x).__name__}")


def _plain(d: Decimal) -> str:
    s = format(d, "f")
    if s.startswith("-") and set(s[1:]) <= set("0."):
        s = s[1:]                      # never show "-0" / "-0.0"
    return s


def round_dp(x: Number, dp: int) -> Decimal:
    """Round half-up to ``dp`` decimal places."""
    return dec(x).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)


def fmt_dp(x: Number, dp: int) -> str:
    """Exactly ``dp`` decimal places: fmt_dp(7, 1) == '7.0'."""
    return _plain(round_dp(x, dp))


def fmt_num(x: Number) -> str:
    """Exact value without trailing zeros (up to 10 significant figures)."""
    d = dec(x)
    if d == d.to_integral_value():
        return _plain(d.quantize(Decimal(1)))
    with localcontext() as ctx:
        ctx.prec = 10
        d = +d
    return _plain(d.normalize())


def round_sf(x: Number, sf: int) -> Decimal:
    """Round half-up to ``sf`` significant figures (keeps trailing zeros)."""
    d = dec(x)
    if d == 0:
        return Decimal(0)
    e = d.adjusted()
    q = d.quantize(Decimal(1).scaleb(e - sf + 1), rounding=ROUND_HALF_UP)
    if q.adjusted() > e:               # 9.96 -> 10.0 at 2 s.f. -> 10
        q = q.quantize(Decimal(1).scaleb(e - sf + 2), rounding=ROUND_HALF_UP)
    return q


def fmt_sf(x: Number, sf: int) -> str:
    """Plain notation rounded to ``sf`` s.f.: 1234.5 -> '1230', 0.012345 -> '0.012'."""
    return _plain(round_sf(x, sf))


def sig_digits(x: Number) -> int:
    """Number of significant digits of an exactly representable decimal value."""
    d = dec(x)
    if d == 0:
        return 1
    return len(d.normalize().as_tuple().digits)


def std_parts(x: Number, sf: int | None = None) -> tuple[str, int]:
    """Mantissa text and exponent: 32000 -> ('3.2', 4); with sf=2, 3e8 -> ('3.0', 8)."""
    d = round_sf(x, sf) if sf else dec(x)
    if d == 0:
        raise ValueError("zero has no standard form")
    e = d.adjusted()
    m = d.scaleb(-e)
    if sf:
        m = m.quantize(Decimal(1).scaleb(-(sf - 1)), rounding=ROUND_HALF_UP)
        return _plain(m), e
    m = m.normalize()
    if m == m.to_integral_value():
        return _plain(m.quantize(Decimal(1))), e
    return _plain(m), e


def fmt_std(x: Number, sf: int | None = None) -> str:
    """'3.2 × 10^4', '6.3 × 10^-4'."""
    m, e = std_parts(x, sf)
    return f"{m} × 10^{e}"


def near_half(x: Number, dp: int | None = None, sf: int | None = None) -> bool:
    """True if ``x`` lies (almost) exactly on a rounding boundary — avoid such problems."""
    d = dec(x)
    if d == 0:
        return False
    if dp is None:
        if sf is None:
            return False
        dp = sf - 1 - d.adjusted()
    t = abs(d).scaleb(dp)
    frac = t - t.to_integral_value(rounding="ROUND_FLOOR")
    return abs(frac - Decimal("0.5")) < Decimal("1e-6")


def is_whole(x: Number) -> bool:
    d = dec(x)
    return d == d.to_integral_value()


# --------------------------------------------------------------- display

def money(x: Number) -> str:
    """'£45' or '£45.60' (never shows sub-penny values)."""
    if is_whole(x):
        return "£" + fmt_num(x)
    return "£" + fmt_dp(x, 2)


def group(x: Number) -> str:
    """Thousands commas for text (12,000); non-integers are shown with fmt_num."""
    if is_whole(x):
        return f"{int(dec(x)):,}"
    return fmt_num(x)


def money_text(x: Number) -> str:
    """Money for question text: '£12,000', '£45.60'."""
    if is_whole(x):
        return "£" + group(x)
    return "£" + fmt_dp(x, 2)


def unit(numstr: str, u: str) -> str:
    """Attach a unit: '£' is a prefix; '%' and '°' attach directly; others after a space."""
    if not u:
        return numstr
    if u == "£":
        return "£" + numstr
    if u in ("%", "°"):
        return numstr + u
    return f"{numstr} {u}"


def sup(k: int) -> str:
    return "".join(_SUP[c] for c in str(k))


def frac_str(f: Fraction) -> str:
    """'3/4', '-3/4', '2'."""
    f = Fraction(f)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def mixed_str(f: Fraction) -> str:
    """'1 3/4', '2', '3/4' (positive values only)."""
    f = Fraction(f)
    if f < 0:
        return "-" + mixed_str(-f)
    w, r = divmod(f.numerator, f.denominator)
    if r == 0:
        return str(w)
    if w == 0:
        return f"{r}/{f.denominator}"
    return f"{w} {r}/{f.denominator}"


def coef_term(c: int, name: str, first: bool) -> str:
    """One signed term of a sum: coef_term(-1, 'x', False) == ' - x'."""
    a = abs(c)
    body = (name if a == 1 and name else f"{a}{name}")
    if first:
        return ("-" if c < 0 else "") + body
    return (" - " if c < 0 else " + ") + body


def terms(pairs: Iterable[tuple[int, str]]) -> str:
    """Join (coef, name) pairs, skipping zeros: [(2,'x'),(-1,'y'),(3,'')] -> '2x - y + 3'."""
    out = ""
    for c, name in pairs:
        if c == 0:
            continue
        out += coef_term(c, name, not out)
    return out or "0"


def poly(coeffs: list[int], var: str = "x") -> tuple[str, str]:
    """Polynomial from highest power down -> (display 'x² - 5x + 6', value 'x**2-5*x+6')."""
    n = len(coeffs) - 1
    disp, val = [], []
    for i, c in enumerate(coeffs):
        k = n - i
        if c == 0:
            continue
        name = var + (sup(k) if k > 1 else "") if k > 0 else ""
        disp.append((c, name))
        if k == 0:
            v = str(abs(c))
        else:
            p = var if k == 1 else f"{var}**{k}"
            v = p if abs(c) == 1 else f"{abs(c)}*{p}"
        val.append(("-" if c < 0 else ("+" if val else "")) + v)
    if not disp:
        return "0", "0"
    return terms(disp), "".join(val)


def lin_factor(m: int, p: int, var: str = "x") -> tuple[str, str]:
    """(m·var + p) -> ('(2x + 3)', '(2*x+3)'); m > 0, p != 0."""
    d, v = poly([m, p], var)
    return f"({d})", f"({v})"


def poly_mul(a: list[int], b: list[int]) -> list[int]:
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def signed(n: Number) -> str:
    """'+ 3' / '- 3' for building equations."""
    return f"- {fmt_num(-n)}" if n < 0 else f"+ {fmt_num(n)}"


# ------------------------------------------------------------------ trig

def sind(a: float) -> float:
    return math.sin(math.radians(a))


def cosd(a: float) -> float:
    return math.cos(math.radians(a))


def tand(a: float) -> float:
    return math.tan(math.radians(a))


def asind(x: float) -> float:
    return math.degrees(math.asin(x))


def acosd(x: float) -> float:
    return math.degrees(math.acos(x))


def atand(x: float) -> float:
    return math.degrees(math.atan(x))


# ---------------------------------------------------------------- answers

EXACT_QUANTUM = Decimal("0.00001")


def safe_exact(value: Number) -> bool:
    """True if an EXACT answer (no dp/sf) is safe under the checker's default tolerance.

    With neither dp nor sf the checker accepts |v - exact| <= 1e-6 * max(1, |exact|),
    which is an ABSOLUTE 1e-6 for |exact| < 1 (e.g. it would accept 4.5 × 10^-8 for
    4.5 × 10^-7).  So exact answers below 1 must be multiples of 0.00001: then every
    other value written to the same precision differs by at least 10x the tolerance.
    """
    d = dec(value)
    if abs(d) >= 1:
        return True
    return (d / EXACT_QUANTUM) == (d / EXACT_QUANTUM).to_integral_value()


def num_answer(value: Number, display: str, dp: int | None = None, sf: int | None = None,
               form: str = "any") -> Answer:
    v = float(value)
    if not math.isfinite(v):
        raise ValueError("answer value must be finite")
    if dp is not None and dp not in (0, 1, 2, 3):
        raise ValueError(f"dp must be 0..3, got {dp}")
    if sf is not None and sf < 2:
        raise ValueError(f"sf must be >= 2, got {sf}")
    return Answer(kind="number", display=display, value=v, dp=dp, sf=sf, form=form)


def _finite(value: object) -> float | None:
    try:
        v = float(value)            # type: ignore[arg-type]
    except (OverflowError, ZeroDivisionError, ValueError, TypeError):
        return None
    return v if math.isfinite(v) else None


def num_mistake(value: Number, u: str, feedback: str, dp: int | None = None,
                sf: int | None = None) -> Mistake | None:
    """A numeric mistake shown with the same unit; None if the value is not usable."""
    v = _finite(value)
    if v is None:
        return None
    if dp is not None:
        shown = fmt_dp(value, dp)
    elif sf is not None:
        shown = fmt_sf(value, sf) if v != 0 else "0"
    else:
        shown = fmt_num(value)
    if u == "£":
        shown = shown if dp is not None or is_whole(value) else fmt_dp(value, 2)
    return Mistake(Answer(kind="number", display=unit(shown, u), value=v, dp=dp, sf=sf), feedback)


def std_answer(value: Number, u: str = "", round_to_sf: int | None = None) -> Answer:
    """A number answer that must be written in standard form (form="standard").

    Without ``round_to_sf`` the value is exact and shown exactly; with it the
    question asks for that many s.f. and the display is rounded.
    """
    if round_to_sf is not None:
        if round_to_sf < 2:
            raise ValueError("sf must be >= 2")
        disp = unit(fmt_std(value, round_to_sf), u)
        return Answer(kind="number", display=disp, value=float(dec(value)), sf=round_to_sf,
                      form="standard")
    disp = unit(fmt_std(value), u)
    return Answer(kind="number", display=disp, value=float(dec(value)), form="standard")


def std_mistake(value: Number, u: str, feedback: str,
                round_to_sf: int | None = None) -> Mistake | None:
    """A mistake written in standard form (its own form is "any")."""
    v = _finite(value)
    if v is None or v == 0:
        return None
    if round_to_sf is not None:
        return Mistake(Answer(kind="number", display=unit(fmt_std(value, round_to_sf), u),
                              value=v, sf=round_to_sf), feedback)
    return Mistake(Answer(kind="number", display=unit(fmt_std(value), u), value=v), feedback)


def mistake(answer: Answer, feedback: str) -> Mistake:
    return Mistake(answer, feedback)


# ------------------------------------------------------------------ build

# "a"/"A" before a vowel sound: eight..., eleven, eighteen (and their thousands), a/e/i/o words.
_AN_NEXT = r"(?=(?:8|11(?!\d)|18(?!\d)|11\d{3}(?!\d)|18\d{3}(?!\d)|[aeioAEIO]))"
_ARTICLE_UPPER = re.compile(r"(^|[.!?]\s+|\n)A " + _AN_NEXT)
_ARTICLE_LOWER = re.compile(r"(?<![\w'])a " + _AN_NEXT)


def fix_articles(s: str) -> str:
    """'A 800 kg car' -> 'An 800 kg car', 'a apple' -> 'an apple'.

    Uppercase 'A' is changed only at the start of a sentence, so point labels such
    as 'angle A is acute' are never touched.
    """
    s = _ARTICLE_UPPER.sub(lambda m: m.group(1) + "An ", s)
    return _ARTICLE_LOWER.sub("an ", s)


def _clean(s: str) -> str:
    s = s.strip()
    while s.endswith("."):
        s = s[:-1].rstrip()
    return s


def build(skill_id: str, level: int, seed: int, text: str, answer: Answer, solution: str,
          hint: str, mistakes: Iterable[Mistake | None] = (),
          fallback_hint: str = DEFAULT_HINT) -> Problem:
    """Validate a generated problem and keep only mistakes the checker attributes correctly.

    Raises ValueError for a broken problem (a bug in a generator): never show it.
    """
    from .checker import check   # local import: checker is a sibling module

    text = fix_articles(text.strip())
    solution = fix_articles(_clean(solution))
    hint = fix_articles(_clean(hint))
    fallback_hint = _clean(fallback_hint)
    if not text or not solution or not hint:
        raise ValueError(f"{skill_id} L{level} seed {seed}: empty text/solution/hint")
    if len(text) > MAX_TEXT:
        raise ValueError(f"{skill_id} L{level} seed {seed}: text too long ({len(text)})")
    if len(solution) > MAX_SOLUTION:
        raise ValueError(f"{skill_id} L{level} seed {seed}: solution too long ({len(solution)})")
    if answer.kind != "rubric" and check(answer, answer.display).status != "correct":
        raise ValueError(f"{skill_id} L{level} seed {seed}: display {answer.display!r} fails check")
    disp = answer.display.lower()
    if disp and disp in hint.lower():
        hint = fallback_hint
        if disp in hint.lower():
            hint = DEFAULT_HINT
    kept: list[Mistake] = []
    seen: set[str] = set()
    for m in mistakes:
        if m is None:
            continue
        fb = _clean(m.feedback)
        if not fb or m.answer.display in seen or m.answer.display == answer.display:
            continue
        m = Mistake(m.answer, fb)
        if check(m.answer, m.answer.display).status != "correct":
            continue
        v = check(answer, m.answer.display, tuple(kept) + (m,))
        if v.status == "wrong" and v.feedback == fb:
            kept.append(m)
            seen.add(m.answer.display)
    return Problem(skill_id=skill_id, level=level, seed=seed, text=text, answer=answer,
                   solution=solution, hint=hint, mistakes=tuple(kept))


def check_level(level: object) -> int:
    if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 5:
        raise ValueError(f"level must be an integer 1..5, got {level!r}")
    return level


def retry(fn, rng, tries: int = MAX_TRIES):
    """Call ``fn(rng)`` until it returns non-None (bounded)."""
    for _ in range(tries):
        out = fn(rng)
        if out is not None:
            return out
    raise RuntimeError("generator could not build a valid problem")
