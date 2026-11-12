"""Further Maths (Level 2 Further Maths / FSMQ style), Years 10–11: 6 generated skills
(docs/ARCHITECTURE_V2.md section 5.1).

Every generator is pure: ``generate(level, seed)`` uses only ``random.Random(seed)``.
Problems are built backwards from nice answers (integer roots, integer turning points,
Pythagorean triples), and every answer is computed from the numbers exactly as they
are printed in the question.  Matrices are written as "top row (a, b) and bottom row
(c, d)" because Telegram has no fixed-width layout.
"""
from __future__ import annotations

import math
import random
from dataclasses import replace
from fractions import Fraction
from typing import Callable

from ..content import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, build_choice
from ..content.fmt import (
    build, check_level, fmt_dp, fmt_num, frac_str, near_half, num_answer, num_mistake, poly,
    poly_mul, retry, sup, terms,
)

SUBJECT_ID = "further_maths"
Draft = dict
DOTS = "…"


# ================================================================ helpers

def _q(text: str, answer: Answer, solution: str, hint: str, mistakes=(), ref: str = "") -> Draft:
    return {"text": text, "answer": answer, "solution": solution, "hint": hint,
            "mistakes": list(mistakes), "ref": ref}


def _choice(stem: str, options: list[str], correct: int, solution: str, hint: str,
            feedback: list[str | None] | None = None, ref: str = "") -> Draft:
    return {"choice": (stem, list(options), correct, feedback), "solution": solution,
            "hint": hint, "ref": ref}


def _nz(rng: random.Random, lo: int, hi: int) -> int:
    """A non-zero integer in [lo, hi]."""
    return rng.choice([v for v in range(lo, hi + 1) if v != 0])


def _pn(n) -> str:
    """A number inside working: negatives in brackets, e.g. 3 × (-2)."""
    return f"({fmt_num(n)})" if n < 0 else fmt_num(n)


def _sumstr(nums) -> str:
    """[12, -8, -1] -> '12 - 8 - 1'."""
    out = ""
    for i, v in enumerate(nums):
        if i == 0:
            out = fmt_num(v)
        else:
            out += f" - {fmt_num(-v)}" if v < 0 else f" + {fmt_num(v)}"
    return out or "0"


def _p(coeffs: list[int], var: str = "x") -> str:
    return poly(coeffs, var)[0]


def _subst(coeffs: list[int], x0: int) -> str:
    """The polynomial with x replaced by (x0): 'x³ - 4x' at -2 -> '(-2)³ - 4(-2)'."""
    return _p(coeffs).replace("x", f"({x0})")


def _peval(coeffs: list[int], x0) -> int | Fraction:
    v = 0
    for c in coeffs:
        v = v * x0 + c
    return v


def _deriv(coeffs: list[int]) -> list[int]:
    n = len(coeffs) - 1
    out = [c * (n - i) for i, c in enumerate(coeffs[:-1])]
    return out or [0]


def _factor(r: int, var: str = "x") -> str:
    """(x - r) written nicely: r=2 -> '(x - 2)', r=-3 -> '(x + 3)'."""
    return f"({var} - {r})" if r > 0 else f"({var} + {-r})"


def _num(v, prefix: str = "") -> Answer:
    return num_answer(v, f"{prefix}{fmt_num(v)}")


def _num_mis(v, fb: str, prefix: str = "") -> Mistake | None:
    if v is None:
        return None
    return Mistake(num_answer(v, f"{prefix}{fmt_num(v)}"), fb)


def _frac(f: Fraction) -> Answer:
    return Answer(kind="fraction", display=frac_str(f), value=frac_str(f))


def _frac_mis(f: Fraction | None, fb: str) -> Mistake | None:
    if f is None:
        return None
    return Mistake(Answer(kind="fraction", display=frac_str(f), value=frac_str(f)), fb)


def _expr(coeffs: list[int], form: str = "any") -> Answer:
    d, v = poly(coeffs)
    return Answer(kind="expr", display=d, value=v, form=form)


def _expr_mis(coeffs: list[int], fb: str) -> Mistake:
    d, v = poly(coeffs)
    return Mistake(Answer(kind="expr", display=d, value=v), fb)


def _roots(vals: list[int]) -> Answer:
    rs = sorted(vals)
    return Answer(kind="set", display=" or ".join(f"x = {r}" for r in rs), value=[str(r) for r in rs])


def _roots_mis(vals: list[int], fb: str) -> Mistake | None:
    rs = sorted(vals)
    if not rs or len(set(rs)) != len(rs):
        return None
    return Mistake(Answer(kind="set", display=" or ".join(f"x = {r}" for r in rs),
                          value=[str(r) for r in rs]), fb)


def _assign(pairs: list[tuple[str, object]]) -> Answer:
    return Answer(kind="assign", display=", ".join(f"{k} = {frac_str(Fraction(v))}" for k, v in pairs),
                  value={k: frac_str(Fraction(v)) for k, v in pairs})


def _assign_mis(pairs: list[tuple[str, object]], fb: str) -> Mistake:
    return Mistake(_assign(pairs), fb)


def _give(*names: str) -> str:
    return "Give your answer as " + ", ".join(f"{n} = {DOTS}" for n in names)


# ======================================================== functions

def _fn_1(rng: random.Random) -> Draft:
    """f(a) for a quadratic."""
    x0 = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5])
    if rng.random() < 0.5:
        a, b = rng.choice([-3, -2, 2, 3, 4, 5]), 0
    else:
        a, b = rng.choice([-2, 1, 1, 2, 3]), _nz(rng, -6, 6)
    c = rng.randint(-9, 9)
    co = [a, b, c]
    val = _peval(co, x0)
    fx = _p(co)
    sol = f"f({x0}) = {_subst(co, x0)} = {_sumstr([v for v in (a * x0 * x0, b * x0, c) if v])} = {val}"
    ms = []
    if x0 < 0:
        ms.append(_num_mis(-a * x0 * x0 + b * x0 + c,
                           f"({x0})² = {x0 * x0}, not {-x0 * x0}: squaring a negative number gives a positive answer"))
    if a not in (1, -1):
        ms.append(_num_mis((a * x0) ** 2 + b * x0 + c,
                           f"Only x is squared in {fx.split(' ')[0]}: work out ({x0})² first, then multiply by {a}"))
    return _q(f"f(x) = {fx}. Work out f({x0}).", _num(val), sol,
              f"Replace every x with ({x0}) and do the powers before multiplying", ms)


def _fn_2(rng: random.Random) -> Draft:
    """fg(a) or gf(a)."""
    p, q = rng.randint(2, 5), _nz(rng, -9, 9)
    r = _nz(rng, -9, 9)
    lin = [p, q]
    quad = [1, 0, r]
    if rng.random() < 0.5:
        f, g = lin, quad
    else:
        f, g = quad, lin
    a = _nz(rng, -4, 4)
    outer_name, inner_name = ("f", "g") if rng.random() < 0.5 else ("g", "f")
    outer, inner = (f, g) if outer_name == "f" else (g, f)
    mid = _peval(inner, a)
    val = _peval(outer, mid)
    other = _peval(inner, _peval(outer, a))
    comp = f"{outer_name}{inner_name}({a})"
    sol = (f"{inner_name}({a}) = {_subst(inner, a)} = {mid}, so {comp} = "
           f"{outer_name}({mid}) = {_subst(outer, mid)} = {val}")
    ms = [_num_mis(other, f"{comp} means {outer_name}({inner_name}({a})): apply {inner_name} first, then {outer_name}"),
          _num_mis(_peval(f, a) * _peval(g, a), f"{comp} is a composite function, not f({a}) × g({a})")]
    return _q(f"f(x) = {_p(f)} and g(x) = {_p(g)}. Work out {comp}.", _num(val), sol,
              f"{comp} means {outer_name}({inner_name}({a})): work out {inner_name}({a}) first", ms)


def _fn_3(rng: random.Random) -> Draft:
    """Inverse of a linear function (expr)."""
    a, b = rng.randint(2, 9), _nz(rng, -9, 9)
    v = rng.random()
    sb = "-" if b > 0 else "+"
    ab = abs(b)
    if v < 0.45:
        ftxt = _p([a, b])
        disp, val = f"(x {sb} {ab})/{a}", f"(x-({b}))/{a}"
        sol = f"Let y = {ftxt}. Then {a}x = y {sb} {ab}, so x = (y {sb} {ab})/{a}. Swap x and y: f⁻¹(x) = {disp}"
        ms = [Mistake(Answer("expr", f"(x {'+' if b > 0 else '-'} {ab})/{a}", f"(x+({b}))/{a}"),
                      f"Undo + {b} by subtracting {b}: check the sign" if b > 0 else
                      f"Undo - {ab} by adding {ab}: check the sign"),
              Mistake(Answer("expr", f"x/{a} {sb} {ab}", f"x/{a}-({b})"),
                      f"Undo the operations in reverse order: deal with the {ab} before dividing by {a}"),
              Mistake(Answer("expr", f"1/({ftxt})", f"1/({a}*x+({b}))"),
                      "f⁻¹(x) is the inverse function, not 1 ÷ f(x)")]
    elif v < 0.75:
        ftxt = f"(x {'+' if b > 0 else '-'} {ab})/{a}"
        disp, val = _p([a, -b]), f"{a}*x-({b})"
        sol = f"Let y = {ftxt}. Then {a}y = x {'+' if b > 0 else '-'} {ab}, so x = {_p([a, -b], 'y')}. Swap x and y: f⁻¹(x) = {disp}"
        ms = [_expr_mis([a, b], "Undo the addition or subtraction with the opposite operation: check the sign"),
              Mistake(Answer("expr", f"(x {sb} {ab})/{a}", f"(x-({b}))/{a}"),
                      f"f divides by {a}, so the inverse multiplies by {a}")]
    else:
        b = abs(b)
        ftxt = f"{b} - {a}x"
        disp, val = f"({b} - x)/{a}", f"({b}-x)/{a}"
        sol = f"Let y = {ftxt}. Then {a}x = {b} - y, so x = ({b} - y)/{a}. Swap x and y: f⁻¹(x) = {disp}"
        ms = [Mistake(Answer("expr", f"(x - {b})/{a}", f"(x-{b})/{a}"),
                      f"Rearrange carefully: {a}x = {b} - y, so the x term is negative"),
              Mistake(Answer("expr", f"(x + {b})/{a}", f"(x+{b})/{a}"),
                      f"Rearrange carefully: {a}x = {b} - y")]
    return _q(f"f(x) = {ftxt}. Find f⁻¹(x).", Answer("expr", disp, val), sol,
              "Write y = f(x), rearrange to make x the subject, then swap x and y", ms)


def _sub_quad(co: list[int], inner: str) -> str:
    """a(inner)² + b(inner) + c as text."""
    a, b, c = co
    out = ("" if a == 1 else "-" if a == -1 else f"{a}") + f"({inner})²"
    if b:
        out += (" + " if b > 0 else " - ") + ("" if abs(b) == 1 else str(abs(b))) + f"({inner})"
    if c:
        out += f" + {c}" if c > 0 else f" - {-c}"
    return out


def _fn_4(rng: random.Random) -> Draft:
    """fg(x) where the outer function is quadratic (expr, expanded)."""
    a, b, c = rng.choice([1, 1, 2, -1]), rng.randint(-4, 4), rng.randint(-6, 6)
    p, q = rng.choice([1, 2, 3]), _nz(rng, -5, 5)
    quad, lin = [a, b, c], [p, q]
    if rng.random() < 0.5:
        names = ("f", "g")            # f quadratic, g linear: ask fg(x)
    else:
        names = ("g", "f")            # g quadratic, f linear: ask gf(x)
    outer, inner = names
    fdef = _p(quad) if outer == "f" else _p(lin)
    gdef = _p(lin) if outer == "f" else _p(quad)
    comp = [a * p * p, 2 * a * p * q + b * p, a * q * q + b * q + c]
    wrong_order = [p * a, p * b, p * c + q]
    no_middle = [a * p * p, b * p, a * q * q + b * q + c]
    name = f"{outer}{inner}(x)"
    sol = f"{name} = {outer}({_p(lin)}) = {_sub_quad(quad, _p(lin))} = {_p(comp)}"
    ms = [_expr_mis(wrong_order, f"{name} means {outer}({inner}(x)): put {inner}(x) into {outer}, not the other way round"),
          _expr_mis(no_middle, f"({_p(lin)})² has a middle term: ({_p(lin)})({_p(lin)}) = {_p([p * p, 2 * p * q, q * q])}")]
    return _q(f"f(x) = {fdef} and g(x) = {gdef}. Find {name}. Give your answer in the form ax² + bx + c.",
              _expr(comp, "expanded"), sol,
              f"Replace every x in {outer}(x) with ({_p(lin)}), then expand the brackets", ms)


def _fn_5(rng: random.Random) -> Draft:
    """Solve f(x) = g(x) (set)."""
    def pick(r):
        r1, r2 = r.randint(-6, 6), r.randint(-6, 6)
        if r1 == r2:
            return None
        a = r.choice([1, 1, 1, 2])
        m, k = _nz(r, -5, 5), r.randint(-9, 9)
        b = m - a * (r1 + r2)
        c = k + a * r1 * r2
        if abs(b) > 20 or abs(c) > 40:
            return None
        return r1, r2, a, m, k, b, c
    r1, r2, a, m, k, b, c = retry(pick, rng)
    diff = [a, b - m, c - k]
    fac = ("" if a == 1 else f"{a}") + _factor(r1) + _factor(r2)
    if r1 == 0 or r2 == 0:
        nz = r2 if r1 == 0 else r1
        fac = ("" if a == 1 else f"{a}") + "x" + _factor(nz)
    lo, hi = sorted((r1, r2))
    sol = f"{_p([a, b, c])} = {_p([m, k])}, so {_p(diff)} = 0. Factorise: {fac} = 0, so x = {lo} or x = {hi}"
    ms = [_roots_mis([-r1, -r2], "Set each bracket equal to zero: the solution has the opposite sign to the number in the bracket")]
    return _q(f"f(x) = {_p([a, b, c])} and g(x) = {_p([m, k])}. Solve f(x) = g(x).", _roots([r1, r2]), sol,
              "Set the two expressions equal, move everything to one side so it equals 0, then factorise", ms)


# ====================================================== polynomials

def _pol_1(rng: random.Random) -> Draft:
    """f(a) for a cubic."""
    lead = rng.choice([1, 1, 2])
    co = [lead, rng.randint(-6, 6), rng.randint(-6, 6), _nz(rng, -9, 9)]
    x0 = rng.choice([-3, -2, -1, 1, 2, 3])
    val = _peval(co, x0)
    vals = [co[0] * x0 ** 3, co[1] * x0 ** 2, co[2] * x0, co[3]]
    sol = f"f({x0}) = {_subst(co, x0)} = {_sumstr([v for v in vals if v != 0])} = {val}"
    ms = []
    if x0 < 0:
        ms.append(_num_mis(val - 2 * vals[0], f"({x0})³ = {x0 ** 3}: a negative number cubed is negative"))
        if co[1]:
            ms.append(_num_mis(val - 2 * vals[1], f"({x0})² = {x0 * x0}: a negative number squared is positive"))
    d = _q(f"f(x) = {_p(co)}. Work out f({x0}).", _num(val), sol,
           f"Substitute x = {x0} into every term — work out the powers first", ms)
    # used when the value of f equals the number substituted (the hint would give the answer away)
    d["fallback"] = "Replace every x with the number in the brackets, work out the powers first, then add up the terms"
    return d


def _poly_k(co: list[int | None]) -> str:
    """Polynomial text where one coefficient (None) is the unknown k."""
    n = len(co) - 1
    out = ""
    for i, c in enumerate(co):
        k = n - i
        name = "x" + (sup(k) if k > 1 else "") if k > 0 else ""
        if c is None:
            out += ("k" if not out else " + k") + name
        elif c != 0:
            out += terms([(c, name)]) if not out else (" - " if c < 0 else " + ") + (
                name if abs(c) == 1 and name else f"{abs(c)}{name}")
    return out


def _pol_2(rng: random.Random) -> Draft:
    """k such that (x - a) is a factor (factor theorem)."""
    def pick(r):
        a = r.choice([-3, -2, -1, 1, 2, 3])
        lead = r.choice([1, 1, 2])
        pos = r.choice([1, 2, 3])                     # index of k in [x³, x², x, 1]
        co = [lead, r.randint(-6, 6), r.randint(-6, 6), r.randint(-9, 9)]
        if pos == 3:
            co[3] = -_peval(co[:3] + [0], a)
            k = co[3]
        else:
            co[pos] = _nz(r, -6, 6)
            co[3] = 0
            co[3] = -_peval(co, a)
            k = co[pos]
        if co[3] == 0 or abs(co[3]) > 60 or abs(k) > 60 or k == 0:
            return None
        return a, co, pos, k
    a, co, pos, k = retry(pick, rng)
    shown = list(co)
    shown[pos] = None
    power = 3 - pos
    coef_k = a ** power
    known = _peval([c if i != pos else 0 for i, c in enumerate(co)], a)
    lin = terms([(coef_k, "k"), (known, "")])
    sol = f"By the factor theorem f({a}) = 0. Substituting x = {a} gives {lin} = 0, so k = {k}"
    ms = []
    coef_m = (-a) ** power
    known_m = _peval([c if i != pos else 0 for i, c in enumerate(co)], -a)
    if coef_m != 0 and known_m % coef_m == 0:
        ms.append(_num_mis(-known_m // coef_m,
                           f"If {_factor(a)} is a factor then f({a}) = 0 — substitute x = {a}, not x = {-a}", "k = "))
    ms.append(_num_mis(-k, "Check the sign when you rearrange to find k", "k = "))
    return _q(f"{_factor(a)} is a factor of f(x) = {_poly_k(shown)}. Find the value of k.",
              _num(k, "k = "), sol,
              f"If {_factor(a)} is a factor, then f({a}) = 0", ms)


def _pol_3(rng: random.Random) -> Draft:
    """Completing the square: x² + bx + c = (x + p)² + q."""
    p = _nz(rng, -6, 6)
    b, c = 2 * p, rng.randint(-12, 12)
    q = c - p * p
    sq = _p([1, b, p * p])
    sol = (f"Halve the coefficient of x: p = {p}. (x {'+' if p > 0 else '-'} {abs(p)})² = {sq}, "
           f"so q = {c} - {p * p} = {q}")
    ms = [_assign_mis([("p", p), ("q", c + p * p)], f"(x + p)² gives an extra {p * p}, so subtract it: q = c - p²"),
          _assign_mis([("p", b), ("q", c - b * b)], "p is half of the coefficient of x"),
          _assign_mis([("p", -p), ("q", q)], "Check the sign of p: (x + p)² expands to x² + 2px + p²")]
    return _q(f"Write {_p([1, b, c])} in the form (x + p)² + q, where p and q are integers. {_give('p', 'q')}",
              _assign([("p", p), ("q", q)]), sol,
              "p is half of the coefficient of x; then subtract p² from the constant", ms)


def _quad_vertex_form(a: int, x0: int, y0: int) -> str:
    lead = "" if a == 1 else "-" if a == -1 else str(a)
    br = "x²" if x0 == 0 else f"{_factor(x0)}²"
    tail = "" if y0 == 0 else (f" + {y0}" if y0 > 0 else f" - {-y0}")
    return f"{lead}{br}{tail}"


def _pol_4(rng: random.Random) -> Draft:
    """Turning point of y = ax² + bx + c (assign x, y)."""
    a = rng.choice([1, 1, -1, 2, 3, -2])
    x0, y0 = _nz(rng, -5, 5), rng.randint(-12, 12)
    b, c = -2 * a * x0, a * x0 * x0 + y0
    co = [a, b, c]
    sol = f"Complete the square: y = {_quad_vertex_form(a, x0, y0)}, so the turning point is ({x0}, {y0})"
    ms = [_assign_mis([("x", -x0), ("y", y0)], "In (x + p)² + q the turning point is at x = -p: check the sign of x")]
    if a != 1 and b % 2 == 0:
        xm = -b // 2
        ms.append(_assign_mis([("x", xm), ("y", _peval(co, xm))],
                              f"Take out the factor of {a} first (or solve dy/dx = 0): x = -b ÷ 2a"))
    return _q(f"Find the coordinates of the turning point of the curve y = {_p(co)}. {_give('x', 'y')}",
              _assign([("x", x0), ("y", y0)]), sol,
              "Complete the square, or differentiate and solve dy/dx = 0", ms)


def _pol_5(rng: random.Random) -> Draft:
    """Solve a cubic given one factor (set)."""
    def pick(r):
        rs = r.sample([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5], 3)
        lead = r.choice([1, 1, 1, 2])
        co = [lead]
        for x in rs:
            co = poly_mul(co, [1, -x])
        if max(abs(c) for c in co) > 120:
            return None
        return rs, lead, co
    rs, lead, co = retry(pick, rng)
    r1, r2, r3 = rs
    quad = [lead]
    for x in (r2, r3):
        quad = poly_mul(quad, [1, -x])
    lo = sorted(rs)
    fac = ("" if lead == 1 else str(lead)) + _factor(r1) + _factor(r2) + _factor(r3)
    sol = (f"Divide by {_factor(r1)}: f(x) = {_factor(r1)}({_p(quad)}). "
           f"Factorise: {fac} = 0, so x = {lo[0]}, x = {lo[1]} or x = {lo[2]}")
    ms = [_roots_mis([-x for x in rs], "Set each bracket equal to zero: the solution has the opposite sign to the number in the bracket"),
          _roots_mis([r2, r3], f"Don't forget the solution from the factor {_factor(r1)} you were given"),
          _roots_mis([r1], "That's one solution — divide by the factor and solve the quadratic for the other two")]
    return _q(f"{_factor(r1)} is a factor of f(x) = {_p(co)}. Solve f(x) = 0.", _roots(rs), sol,
              f"Divide f(x) by {_factor(r1)} to get a quadratic, then factorise it", ms)


# ==================================================== coordinates

def _pt(x, y) -> str:
    return f"({fmt_num(x)}, {fmt_num(y)})"


def _co_1(rng: random.Random) -> Draft:
    """Midpoint (assign x, y)."""
    def pick(r):
        x1, y1 = r.randint(-8, 10), r.randint(-8, 10)
        x2 = x1 + 2 * r.randint(-6, 6)
        y2 = y1 + 2 * r.randint(-6, 6)
        return None if (x1, y1) == (x2, y2) or x1 == x2 or y1 == y2 else (x1, y1, x2, y2)
    x1, y1, x2, y2 = retry(pick, rng)
    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
    sol = (f"Midpoint = (({x1} + {_pn(x2)}) ÷ 2, ({y1} + {_pn(y2)}) ÷ 2) = "
           f"({x1 + x2} ÷ 2, {y1 + y2} ÷ 2) = ({mx}, {my})")
    ms = [_assign_mis([("x", (x2 - x1) // 2), ("y", (y2 - y1) // 2)],
                      "For the midpoint, add the coordinates and halve — don't subtract them")]
    return _q(f"Point A is at {_pt(x1, y1)} and point B is at {_pt(x2, y2)}. Find the coordinates of the midpoint of AB. {_give('x', 'y')}",
              _assign([("x", mx), ("y", my)]), sol,
              "The midpoint is the mean of the x-coordinates and the mean of the y-coordinates", ms)


def _co_2(rng: random.Random) -> Draft:
    """Gradient through two points (fraction)."""
    def pick(r):
        x1, y1, x2, y2 = (r.randint(-8, 9) for _ in range(4))
        return None if x1 == x2 or y1 == y2 else (x1, y1, x2, y2)
    x1, y1, x2, y2 = retry(pick, rng)
    dy, dx = y2 - y1, x2 - x1
    m = Fraction(dy, dx)
    sol = f"Gradient = change in y ÷ change in x = ({y2} - {_pn(y1)}) ÷ ({x2} - {_pn(x1)}) = {dy} ÷ {_pn(dx)} = {frac_str(m)}"
    ms = [_frac_mis(Fraction(dx, dy), "Gradient = change in y ÷ change in x — you divided the other way up"),
          _frac_mis(-m, "Subtract the coordinates in the same order on the top and on the bottom")]
    return _q(f"Work out the gradient of the line through A{_pt(x1, y1)} and B{_pt(x2, y2)}. "
              "Give your answer as a whole number or a fraction.",
              _frac(m), sol, "Gradient = (difference in y) ÷ (difference in x)", ms)


def _co_3(rng: random.Random) -> Draft:
    """Gradient perpendicular to a given line (fraction)."""
    v = rng.random()
    c = _nz(rng, -9, 9)
    if v < 0.35:
        mi = _nz(rng, -6, 6)
        m = Fraction(mi)
        eq = f"y = {_p([mi, c])}"
        first = f"L is already in the form y = mx + c, so its gradient is {mi}"
    else:
        def pick(r):
            a, b = _nz(r, -7, 7), r.randint(2, 7)
            return (a, b) if math.gcd(abs(a), b) == 1 else None
        a, b = retry(pick, rng)
        if v < 0.7:                                  # ax + by = c  ->  m = -a/b
            eq = f"{terms([(a, 'x'), (b, 'y')])} = {c}"
            m = Fraction(-a, b)
            first = f"Rearrange: {b}y = {_p([-a, c])}, so y = ({_p([-a, c])})/{b} and the gradient of L is {frac_str(m)}"
        else:                                        # by = ax + c  ->  m = a/b
            eq = f"{b}y = {_p([a, c])}"
            m = Fraction(a, b)
            first = f"Divide by {b}: the gradient of L is {frac_str(m)}"
    perp = -1 / m
    sol = f"{first}. Perpendicular gradient = -1 ÷ {_pn(m) if m.denominator == 1 else '(' + frac_str(m) + ')'} = {frac_str(perp)}"
    ms = [_frac_mis(m, "That's the gradient of L itself — perpendicular gradients multiply to give -1"),
          _frac_mis(-m, "Flip the fraction as well as changing the sign: the perpendicular gradient is -1 ÷ m"),
          _frac_mis(1 / m, "Change the sign as well as flipping the fraction: the perpendicular gradient is -1 ÷ m")]
    return _q(f"Line L has equation {eq}. Find the gradient of a line perpendicular to L. "
              "Give your answer as a whole number or a fraction.",
              _frac(perp), sol,
              "Rearrange into the form y = mx + c to find the gradient of L, then take the negative reciprocal", ms)


def _co_4(rng: random.Random) -> Draft:
    """Distance between two points (1 d.p.)."""
    def pick(r):
        dx, dy = r.randint(1, 12), r.randint(1, 12)
        s = dx * dx + dy * dy
        if math.isqrt(s) ** 2 == s or near_half(math.sqrt(s), 1):
            return None
        x1, y1 = r.randint(-8, 8), r.randint(-8, 8)
        x2 = x1 + dx * r.choice([1, -1])
        y2 = y1 + dy * r.choice([1, -1])
        return x1, y1, x2, y2, s
    x1, y1, x2, y2, s = retry(pick, rng)
    d = math.sqrt(s)
    dx, dy = x2 - x1, y2 - y1
    sol = f"Distance = √(({x2} - {_pn(x1)})² + ({y2} - {_pn(y1)})²) = √({_pn(dx)}² + {_pn(dy)}²) = √{s} = {fmt_dp(d, 1)} (1 d.p.)"
    ms = [num_mistake(s, "", "Don't forget to take the square root at the end", dp=1),
          num_mistake(abs(dx) + abs(dy), "", "Use Pythagoras: square the differences, add them, then square root", dp=1)]
    return _q(f"Work out the distance between A{_pt(x1, y1)} and B{_pt(x2, y2)}. Give your answer to 1 decimal place.",
              num_answer(d, fmt_dp(d, 1), dp=1), sol,
              "Find the difference in x and the difference in y, then use Pythagoras", ms)


def _co_5(rng: random.Random) -> Draft:
    """Centre and radius from the general form of a circle (assign a, b, r)."""
    def pick(r):
        a, b, rad = r.randint(-6, 6), r.randint(-6, 6), r.randint(2, 9)
        if a == 0 and b == 0:
            return None
        F = a * a + b * b - rad * rad
        return a, b, rad, F
    a, b, rad, F = retry(pick, rng)
    eq = terms([(1, "x²"), (1, "y²"), (-2 * a, "x"), (-2 * b, "y"), (F, "")])
    sq_x = "x²" if a == 0 else f"{_factor(a)}²"
    sq_y = "y²" if b == 0 else f"{_factor(b, 'y')}²"
    sol = (f"Complete the square: {sq_x} + {sq_y} = {_sumstr([v for v in (-F, a * a, b * b) if v])} = {rad * rad}. "
           f"Centre ({a}, {b}), radius √{rad * rad} = {rad}")
    ms = [_assign_mis([("a", -a), ("b", -b), ("r", rad)],
                      "The centre of (x - a)² + (y - b)² = r² is (a, b): the signs change from the equation"),
          _assign_mis([("a", a), ("b", b), ("r", rad * rad)], f"That's r² — the radius is the square root of {rad * rad}")]
    return _q(f"A circle has equation {eq} = 0. Its centre is (a, b) and its radius is r. Find a, b and r. "
              f"{_give('a', 'b', 'r')}",
              _assign([("a", a), ("b", b), ("r", rad)]), sol,
              "Complete the square for the x terms and for the y terms to get (x - a)² + (y - b)² = r²", ms)


# ======================================================== calculus

def _ca_1(rng: random.Random) -> Draft:
    """d/dx of kxⁿ (expr)."""
    n, k = rng.randint(2, 6), _nz(rng, -9, 9)
    y = [k] + [0] * n
    d = _deriv(y)
    sol = f"Multiply by the power and reduce the power by 1: dy/dx = {k} × {n}x{sup(n - 1) if n > 2 else ''} = {_p(d)}"
    ms = [_expr_mis([k] + [0] * (n - 1), "Multiply by the power as well as reducing it by 1"),
          _expr_mis([k * n] + [0] * n, "After multiplying by the power, reduce the power by 1")]
    return _q(f"y = {_p(y)}. Find dy/dx.", _expr(d), sol,
              "To differentiate axⁿ, multiply by n and reduce the power by 1", ms)


def _ca_2(rng: random.Random) -> Draft:
    """Differentiate a polynomial (expr)."""
    def pick(r):
        deg = r.choice([3, 3, 4])
        co = [_nz(r, -5, 6)] + [r.randint(-9, 9) for _ in range(deg - 1)] + [_nz(r, -9, 9)]
        return co if sum(1 for c in co if c) >= 3 and any(co[1:-1]) else None
    y = retry(pick, rng)
    d = _deriv(y)
    sol = f"Differentiate term by term: dy/dx = {_p(d)} (the constant {y[-1]} differentiates to 0)"
    shifted = list(y[:-1])
    ms = [_expr_mis(d[:-1] + [d[-1] + y[-1]] if len(d) else [y[-1]],
                    f"The constant {y[-1]} differentiates to 0"),
          _expr_mis(shifted, "Multiply each term by its power before reducing the power by 1")]
    return _q(f"y = {_p(y)}. Find dy/dx.", _expr(d), sol,
              "Differentiate one term at a time: axⁿ becomes naxⁿ⁻¹, and a constant becomes 0", ms)


def _ca_3(rng: random.Random) -> Draft:
    """Gradient of a curve at a point (number)."""
    def pick(r):
        deg = r.choice([2, 3, 3])
        co = [_nz(r, -3, 4)] + [r.randint(-8, 8) for _ in range(deg)]
        x0 = _nz(r, -3, 4)
        g = _peval(_deriv(co), x0)
        return (co, x0, g) if abs(g) <= 150 else None
    co, x0, g = retry(pick, rng)
    d = _deriv(co)
    sol = f"dy/dx = {_p(d)}. At x = {x0}: dy/dx = {_subst(d, x0)} = {g}"
    ms = [_num_mis(_peval(co, x0), f"That's the y-coordinate — differentiate first, then substitute x = {x0} into dy/dx")]
    return _q(f"Find the gradient of the curve y = {_p(co)} at the point where x = {x0}.", _num(g), sol,
              f"Find dy/dx, then substitute x = {x0}", ms)


def _stat_cubic(rng: random.Random, p: int, q: int) -> tuple[list[int], int]:
    """A cubic with dy/dx = g(x - p)(x - q); returns (coefficients, g)."""
    d0 = rng.randint(-9, 9)
    if (p + q) % 2 == 0 and rng.random() < 0.5:
        return [1, -3 * (p + q) // 2, 3 * p * q, d0], 3
    return [2, -3 * (p + q), 6 * p * q, d0], 6


def _ca_4(rng: random.Random) -> Draft:
    """x-coordinates of stationary points (set)."""
    p, q = rng.sample([-4, -3, -2, -1, 0, 1, 2, 3, 4, 5], 2)
    co, g = _stat_cubic(rng, p, q)
    d = _deriv(co)
    quad = [c // g for c in d]
    lo, hi = sorted((p, q))
    fac = "".join("x" if r == 0 else _factor(r) for r in (lo, hi))
    sol = f"dy/dx = {_p(d)} = 0. Divide by {g}: {_p(quad)} = 0, so {fac} = 0 and x = {lo} or x = {hi}"
    ms = [_roots_mis([-p, -q], "Set each bracket equal to zero: the solution has the opposite sign to the number in the bracket")]
    return _q(f"Find the x-coordinates of the stationary points of the curve y = {_p(co)}.", _roots([p, q]), sol,
              "At a stationary point dy/dx = 0: differentiate, set equal to 0 and solve", ms)


def _ca_5(rng: random.Random) -> Draft:
    """A stationary point (assign x, y)."""
    if rng.random() < 0.65:
        def pick(r):
            p, q = r.randint(1, 4), r.randint(-4, -1)
            co, g = _stat_cubic(r, p, q)
            return (p, q, co, g) if max(abs(_peval(co, p)), abs(_peval(co, q))) <= 150 else None
        p, q, co, g = retry(pick, rng)
        want_pos = rng.random() < 0.5
        x0, other = (p, q) if want_pos else (q, p)
        y0 = _peval(co, x0)
        d = _deriv(co)
        quad = [c // g for c in d]
        sol = (f"dy/dx = {_p(d)} = 0 gives {_p(quad)} = 0, so x = {min(p, q)} or x = {max(p, q)}. "
               f"Take x = {x0}: y = {_subst(co, x0)} = {y0}")
        ms = [_assign_mis([("x", other), ("y", _peval(co, other))],
                          f"That's the other stationary point — the question asks for the one where x is {'positive' if want_pos else 'negative'}")]
        return _q(f"The curve y = {_p(co)} has two stationary points. Find the coordinates of the stationary point "
                  f"where x is {'positive' if want_pos else 'negative'}. {_give('x', 'y')}",
                  _assign([("x", x0), ("y", y0)]), sol,
                  "Solve dy/dx = 0, choose the right x, then substitute it into the equation of the curve", ms)
    a = rng.choice([-3, -2, 2, 3])
    x0, y0 = _nz(rng, -4, 4), rng.randint(-15, 15)
    co = [a, -2 * a * x0, a * x0 * x0 + y0]
    d = _deriv(co)
    sol = f"dy/dx = {_p(d)} = 0 gives x = {x0}. Then y = {_subst(co, x0)} = {y0}"
    ms = [_assign_mis([("x", -x0), ("y", _peval(co, -x0))], "Solve dy/dx = 0 carefully: check the sign of x")]
    return _q(f"Find the coordinates of the stationary point of the curve y = {_p(co)}. {_give('x', 'y')}",
              _assign([("x", x0), ("y", y0)]), sol,
              "Differentiate, solve dy/dx = 0, then substitute x back into the equation of the curve", ms)


# ======================================================== matrices

_POS = (("top-left", 0, 0), ("top-right", 0, 1), ("bottom-left", 1, 0), ("bottom-right", 1, 1))


def _mt(m) -> str:
    return f"top row ({m[0][0]}, {m[0][1]}) and bottom row ({m[1][0]}, {m[1][1]})"


def _rand_mat(rng: random.Random, lo: int, hi: int) -> list[list[int]]:
    return [[rng.randint(lo, hi) for _ in range(2)] for _ in range(2)]


def _mul(a, b) -> list[list[int]]:
    return [[a[i][0] * b[0][j] + a[i][1] * b[1][j] for j in range(2)] for i in range(2)]


def _ma_1(rng: random.Random) -> Draft:
    """An entry of kA."""
    a = _rand_mat(rng, -6, 9)
    k = rng.choice([2, 3, 4, 5, -2, -3])
    name, i, j = rng.choice(_POS)
    e = a[i][j]
    val = k * e
    ms = [_num_mis(k + e, f"Multiply each entry by {k} — don't add {k}")]
    d = _q(f"Matrix A has {_mt(a)}. Work out the {name} entry of {k}A.", _num(val),
           f"Multiply every entry of A by {k}: the {name} entry is {k} × {_pn(e)} = {val}",
           f"{k}A means multiply every entry of A by {k}", ms)
    # used when the entry is 1, so k × entry = k and the hint would give the answer away
    d["fallback"] = f"Find the {name} entry of A, then multiply it by the number in front of A"
    return d


def _ma_2(rng: random.Random) -> Draft:
    """An entry of AB."""
    a, b = _rand_mat(rng, -5, 6), _rand_mat(rng, -5, 6)
    name, i, j = rng.choice(_POS)
    ab, ba = _mul(a, b), _mul(b, a)
    val = ab[i][j]
    rows = ("top", "bottom")
    cols = ("first", "second")
    sol = (f"{name.capitalize()} entry = {rows[i]} row of A × {cols[j]} column of B = "
           f"{a[i][0]} × {_pn(b[0][j])} + {_pn(a[i][1])} × {_pn(b[1][j])} = {val}")
    ms = [_num_mis(ba[i][j], "Order matters: AB uses the rows of A and the columns of B"),
          _num_mis(a[i][j] * b[i][j], "Matrices are not multiplied entry by entry — multiply a row of A by a column of B"),
          _num_mis(a[i][0] * b[j][0] + a[i][1] * b[j][1], "Use a column of B, not a row of B")]
    return _q(f"Matrix A has {_mt(a)}. Matrix B has {_mt(b)}. Work out the {name} entry of AB.", _num(val), sol,
              f"Multiply the {rows[i]} row of A by the {cols[j]} column of B, then add", ms)


def _ma_3(rng: random.Random) -> Draft:
    """Image of a point under a matrix (assign x, y)."""
    def pick(r):
        m = _rand_mat(r, -3, 4)
        if m[0][0] * m[1][1] - m[0][1] * m[1][0] == 0 or m[0][1] == m[1][0]:
            return None
        return m
    m = retry(pick, rng)
    x, y = _nz(rng, -5, 5), _nz(rng, -5, 5)
    ix, iy = m[0][0] * x + m[0][1] * y, m[1][0] * x + m[1][1] * y
    tx, ty = m[0][0] * x + m[1][0] * y, m[0][1] * x + m[1][1] * y
    sol = (f"Multiply M by the column ({x}, {y}): x = {m[0][0]} × {_pn(x)} + {_pn(m[0][1])} × {_pn(y)} = {ix}, "
           f"y = {m[1][0]} × {_pn(x)} + {_pn(m[1][1])} × {_pn(y)} = {iy}")
    ms = [_assign_mis([("x", tx), ("y", ty)], "Multiply the rows of M by the column (x, y), not the columns of M")]
    return _q(f"Matrix M has {_mt(m)}. Find the image of the point {_pt(x, y)} under the transformation "
              f"represented by M. {_give('x', 'y')}",
              _assign([("x", ix), ("y", iy)]), sol,
              "Write the point as a column vector and multiply: M × (x, y)", ms)


_TRANSFORMS = {
    "refl_x": ([[1, 0], [0, -1]], "Reflection in the x-axis"),
    "refl_y": ([[-1, 0], [0, 1]], "Reflection in the y-axis"),
    "refl_yx": ([[0, 1], [1, 0]], "Reflection in the line y = x"),
    "refl_ynx": ([[0, -1], [-1, 0]], "Reflection in the line y = -x (that is, x + y = 0)"),
    "rot90": ([[0, -1], [1, 0]], "Rotation 90° anticlockwise about the origin"),
    "rot270": ([[0, 1], [-1, 0]], "Rotation 90° clockwise about the origin"),
    "rot180": ([[-1, 0], [0, -1]], "Rotation 180° about the origin"),
}
_CONFUSE = {
    "refl_x": ("refl_y", "rot180", "refl_yx"),
    "refl_y": ("refl_x", "rot180", "refl_ynx"),
    "refl_yx": ("refl_ynx", "rot90", "rot270"),
    "refl_ynx": ("refl_yx", "rot270", "rot90"),
    "rot90": ("rot270", "refl_yx", "refl_ynx"),
    "rot270": ("rot90", "refl_ynx", "refl_yx"),
    "rot180": ("refl_x", "refl_y", "rot90"),
}


def _enl(k: int) -> tuple[list[list[int]], str]:
    return [[k, 0], [0, k]], f"Enlargement, scale factor {k}, centre the origin"


def _ma_4(rng: random.Random) -> Draft:
    """Name the transformation (choice; one ref per transformation)."""
    keys = list(_TRANSFORMS)
    v = rng.randrange(len(keys) + 2)
    if v < len(keys):
        key = keys[v]
        m, name = _TRANSFORMS[key]
        others = [(_TRANSFORMS[o][0], _TRANSFORMS[o][1]) for o in _CONFUSE[key]]
    else:
        k = rng.choice([2, 3, 4])
        key = f"enl{k}"
        m, name = _enl(k)
        k2 = rng.choice([x for x in (2, 3, 4, 5) if x != k])
        others = [_enl(k2), _TRANSFORMS["refl_yx"], _TRANSFORMS["rot90"]]
    options = [name] + [o[1] for o in others]
    c1, c2 = (m[0][0], m[1][0]), (m[0][1], m[1][1])
    fb: list[str | None] = [None]
    for om, _ in others:
        oc1, oc2 = (om[0][0], om[1][0]), (om[0][1], om[1][1])
        if oc1 != c1:
            fb.append(f"That would send (1, 0) to {_pt(*oc1)}, but M sends (1, 0) to {_pt(*c1)}")
        else:
            fb.append(f"That would send (0, 1) to {_pt(*oc2)}, but M sends (0, 1) to {_pt(*c2)}")
    sol = (f"M sends (1, 0) to {_pt(*c1)} and (0, 1) to {_pt(*c2)} (the columns of M), "
           f"so M is a {name[0].lower() + name[1:]}")
    return _choice(f"Matrix M has {_mt(m)}. Which transformation does M represent?", options, 0, sol,
                   "Find the images of (1, 0) and (0, 1): they are the columns of M", fb, ref=key)


def _ma_5(rng: random.Random) -> Draft:
    """A product of two matrices (assign a, b, c, d)."""
    def pick(r):
        m, n = _rand_mat(r, -4, 5), _rand_mat(r, -4, 5)
        return (m, n) if _mul(m, n) != _mul(n, m) else None
    def pick_sq(r):
        x = _rand_mat(r, -4, 5)
        return x if _mul(x, x) != [[x[i][j] ** 2 for j in range(2)] for i in range(2)] else None

    if rng.random() < 0.25:
        m = retry(pick_sq, rng)
        prod = _mul(m, m)
        what, txt = "M²", f"Matrix M has {_mt(m)}. Work out M²."
        sol_pre = "M² = M × M"
        ms = [_assign_mis(list(zip("abcd", [m[i][j] ** 2 for i in range(2) for j in range(2)])),
                          "M² means M × M: multiply rows by columns, don't square each entry")]
    else:
        m, n = retry(pick, rng)
        prod = _mul(m, n)
        what, txt = "MN", f"Matrix M has {_mt(m)}. Matrix N has {_mt(n)}. Work out MN."
        sol_pre = "Multiply rows of M by columns of N"
        nm = _mul(n, m)
        ms = [_assign_mis(list(zip("abcd", [nm[i][j] for i in range(2) for j in range(2)])),
                          "Order matters: MN uses the rows of M and the columns of N"),
              _assign_mis(list(zip("abcd", [m[i][j] * n[i][j] for i in range(2) for j in range(2)])),
                          "Matrices are not multiplied entry by entry — multiply a row by a column")]
    vals = [prod[0][0], prod[0][1], prod[1][0], prod[1][1]]
    sol = f"{sol_pre}: {what} has top row ({vals[0]}, {vals[1]}) and bottom row ({vals[2]}, {vals[3]})"
    return _q(f"{txt[:-1]}, writing it with top row (a, b) and bottom row (c, d). {_give('a', 'b', 'c', 'd')}",
              _assign(list(zip("abcd", vals))), sol,
              "Each entry is a row of the first matrix times a column of the second: multiply pairs and add", ms)


# ==================================================== trigonometry

_EXACT = {   # value text -> exact value used to compare
    "0": 0.0, "1/2": 0.5, "1/√2": 1 / math.sqrt(2), "√3/2": math.sqrt(3) / 2, "1": 1.0,
    "1/√3": 1 / math.sqrt(3), "√3": math.sqrt(3),
}
_TABLE = {
    ("sin", 0): "0", ("sin", 30): "1/2", ("sin", 45): "1/√2", ("sin", 60): "√3/2", ("sin", 90): "1",
    ("cos", 0): "1", ("cos", 30): "√3/2", ("cos", 45): "1/√2", ("cos", 60): "1/2", ("cos", 90): "0",
    ("tan", 0): "0", ("tan", 30): "1/√3", ("tan", 45): "1", ("tan", 60): "√3",
}
_NEAR = {"0": ("1", "1/2"), "1/2": ("√3/2", "1/√2"), "1/√2": ("1/2", "√3/2"), "√3/2": ("1/2", "1/√2"),
         "1": ("0", "√3/2"), "1/√3": ("√3", "1/2"), "√3": ("1/√3", "√3/2")}


def _tr_1(rng: random.Random) -> Draft:
    """Exact value of sin/cos/tan of 0, 30, 45, 60, 90 (choice; one ref per value)."""
    fn, ang = rng.choice(sorted(_TABLE))
    val = _TABLE[(fn, ang)]
    near = [x for x in _NEAR[val]]
    pool = [x for x in _EXACT if x != val and x not in near]
    others = near + [rng.choice(pool)]
    options = [val] + others
    fb: list[str | None] = [None]
    for o in others:
        same = [f"{f} {a}°" for (f, a), t in sorted(_TABLE.items(), key=lambda kv: (kv[0][1], kv[0][0]))
                if t == o and (f, a) != (fn, ang)]
        fb.append(f"{o} is the value of {same[0]}" if same else None)
    ratio = {"sin": "opposite ÷ hypotenuse", "cos": "adjacent ÷ hypotenuse", "tan": "opposite ÷ adjacent"}[fn]
    if ang == 45:
        sol = f"{fn} 45° = {val}: in a right-angled triangle with angles 45°, 45° and sides 1, 1 and √2, {fn} = {ratio}"
    elif ang in (30, 60):
        sol = (f"{fn} {ang}° = {val}: half of an equilateral triangle of side 2 has sides 1, √3 and 2, "
               f"with 30° opposite the side 1; {fn} = {ratio}")
    else:
        sol = f"{fn} {ang}° = {val}, from the graph of y = {fn} x"
    hint = ("Sketch a right-angled triangle with angles 45°, 45° and two sides of 1" if ang == 45 else
            "Sketch half of an equilateral triangle with side 2: the sides are 1, √3 and 2" if ang in (30, 60) else
            f"Think about the graph of y = {fn} x at x = {ang}°")
    return _choice(f"What is the exact value of {fn} {ang}°?", options, 0, sol, hint, fb, ref=f"{fn}{ang}")


_TERMS = (   # (text, exact value, value if the square is forgotten or None)
    ("sin 30°", Fraction(1, 2), None), ("cos 60°", Fraction(1, 2), None), ("tan 45°", Fraction(1), None),
    ("sin 90°", Fraction(1), None), ("cos 0°", Fraction(1), None),
    ("sin² 45°", Fraction(1, 2), None), ("cos² 45°", Fraction(1, 2), None),
    ("sin² 60°", Fraction(3, 4), None), ("cos² 30°", Fraction(3, 4), None),
    ("sin² 30°", Fraction(1, 4), Fraction(1, 2)), ("cos² 60°", Fraction(1, 4), Fraction(1, 2)),
    ("tan² 60°", Fraction(3), None), ("tan² 30°", Fraction(1, 3), None),
    ("sin 60° × tan 60°", Fraction(3, 2), None), ("cos 30° × tan 30°", Fraction(1, 2), None),
    ("tan 30° × tan 60°", Fraction(1), None), ("sin 45° × cos 45°", Fraction(1, 2), None),
)


def _tr_2(rng: random.Random) -> Draft:
    """Exact value of an expression in sin/cos/tan (fraction)."""
    def pick(r):
        (t1, v1, w1), (t2, v2, w2) = r.sample(_TERMS, 2)
        c1, c2 = r.choice([1, 1, 2, 3, 4]), r.choice([1, 1, 2, 3])
        sgn = r.choice([1, -1])
        val = c1 * v1 + sgn * c2 * v2
        if val == 0 or (" × " in t1 and " × " in t2):
            return None
        return t1, v1, w1, t2, v2, w2, c1, c2, sgn, val
    t1, v1, w1, t2, v2, w2, c1, c2, sgn, val = retry(pick, rng)

    def term(c, t):
        return t if c == 1 else f"{c} {t}" if " × " not in t else f"{c} × {t}"
    op = "+" if sgn > 0 else "-"
    expr = f"{term(c1, t1)} {op} {term(c2, t2)}"
    sol = (f"{t1} = {frac_str(v1)} and {t2} = {frac_str(v2)}, so {expr} = "
           f"{frac_str(c1 * v1)} {op} {frac_str(c2 * v2)} = {frac_str(val)}")
    ms = []
    if w1 is not None or w2 is not None:
        wv = c1 * (w1 if w1 is not None else v1) + sgn * c2 * (w2 if w2 is not None else v2)
        sq = t1 if w1 is not None else t2
        ms.append(_frac_mis(wv, f"{sq} means ({sq.replace('²', '')})²: square the exact value"))
    return _q(f"Find the exact value of {expr}. Give your answer as a whole number or a fraction.", _frac(val), sol,
              "Replace each trig value with its exact value first (sin² x means (sin x)²)", ms)


def _deg_set(vals: list[float]) -> Answer:
    rs = sorted(vals)
    return Answer(kind="set", display=" or ".join(f"x = {fmt_dp(v, 1)}°" for v in rs),
                  value=[f"{v:.10f}" for v in rs], dp=1)


def _deg_mis(vals: list[float], fb: str) -> Mistake | None:
    if not vals:
        return None
    rs = sorted(vals)
    return Mistake(Answer(kind="set", display=" or ".join(f"x = {fmt_dp(v, 1)}°" for v in rs),
                          value=[f"{v:.10f}" for v in rs], dp=1), fb)


_K_DEC = [k / 10 for k in range(-9, 10) if k not in (0, 5, -5)] + [0.25, 0.35, 0.65, 0.75, -0.25, -0.35, -0.65, -0.75]


def _tr_3(rng: random.Random) -> Draft:
    """Solve sin x = k or cos x = k for 0° ≤ x ≤ 360° (set, 1 d.p.)."""
    def pick(r):
        fn = r.choice(["sin", "cos"])
        k = r.choice(_K_DEC)
        if fn == "sin":
            a = math.degrees(math.asin(k))
            sols = [a, 180 - a] if k > 0 else [180 - a, 360 + a]
        else:
            a = math.degrees(math.acos(k))
            sols = [a, 360 - a]
        if any(near_half(s, 1) for s in sols + [a]):
            return None
        return fn, k, a, sols
    fn, k, a, sols = retry(pick, rng)
    ks = fmt_num(k)
    lo, hi = sorted(sols)
    both = f"x = {fmt_dp(lo, 1)}° or x = {fmt_dp(hi, 1)}°"
    if fn == "sin" and k > 0:
        sol = f"α = sin⁻¹({ks}) = {fmt_dp(a, 1)}°. The other solution is 180° - α, so {both}"
        ms = [_deg_mis([a], "There are two solutions between 0° and 360° — use the symmetry of the sine graph"),
              _deg_mis([a, 360 - a], "For sine the second solution is 180° - α, not 360° - α")]
    elif fn == "sin":
        sol = (f"α = sin⁻¹({ks}) = {fmt_dp(a, 1)}°, which is outside the range. "
               f"The solutions are 180° - α and 360° + α, so {both}")
        ms = [_deg_mis([a, 180 - a], f"{fmt_dp(a, 1)}° is outside 0° to 360°: add 360° to it"),
              _deg_mis([360 + a], "There are two solutions between 0° and 360° — use the symmetry of the sine graph")]
    else:
        sol = f"α = cos⁻¹({ks}) = {fmt_dp(a, 1)}°. The other solution is 360° - α, so {both}"
        ms = [_deg_mis([a], "There are two solutions between 0° and 360° — use the symmetry of the cosine graph"),
              _deg_mis([a, 180 - a], "For cosine the second solution is 360° - α, not 180° - α")]
    return _q(f"Solve {fn} x = {ks} for 0° ≤ x ≤ 360°. Give your answers to 1 decimal place.",
              _deg_set(sols), sol,
              f"Use {fn}⁻¹ on your calculator for the first solution, then use the graph of y = {fn} x to find the second", ms)


def _tr_4(rng: random.Random) -> Draft:
    """Solve tan x = k (or an equation that rearranges to it) for 0° ≤ x ≤ 360° (set, 1 d.p.)."""
    def pick(r):
        v = r.random()
        if v < 0.4:
            k = Fraction(r.choice([2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 25, 35]), 10) * r.choice([1, -1])
            eq = f"tan x = {fmt_num(k)}"
            pre = ""
            kshow = fmt_num(k)
        elif v < 0.75:
            a, b = r.randint(2, 5), _nz(r, -7, 7)
            k = Fraction(b, a)
            eq = f"{a} tan x {'-' if b > 0 else '+'} {abs(b)} = 0"
            pre = f"tan x = {frac_str(k)}. "
            kshow = frac_str(k)
        else:
            a, b = r.randint(2, 5), _nz(r, -5, 5)
            if abs(b) == a:
                return None
            k = Fraction(b, a)
            eq = f"{a} sin x = {b} cos x" if abs(b) != 1 else f"{a} sin x = {'-' if b < 0 else ''}cos x"
            pre = f"Divide by cos x: tan x = {frac_str(k)}. "
            kshow = frac_str(k)
        al = math.degrees(math.atan(float(k)))
        sols = [al, al + 180] if al > 0 else [al + 180, al + 360]
        if any(near_half(s, 1) for s in sols + [al]):
            return None
        return eq, k, al, sols, pre, kshow
    eq, k, al, sols, pre, kshow = retry(pick, rng)
    lo, hi = sorted(sols)
    sol = (f"{pre}α = tan⁻¹({kshow}) = {fmt_dp(al, 1)}°. tan repeats every 180°, "
           f"so x = {fmt_dp(lo, 1)}° or x = {fmt_dp(hi, 1)}°")
    ms = [_deg_mis([lo], "There are two solutions between 0° and 360° — tan x repeats every 180°")]
    if al < 0:
        ms.append(_deg_mis([al + 180], f"{fmt_dp(al, 1)}° is outside 0° to 360° — add 180° and 360° to get both solutions"))
    else:
        ms.append(_deg_mis([al, 180 - al], "For tan the second solution is 180° + α, not 180° - α"))
    return _q(f"Solve {eq} for 0° ≤ x ≤ 360°. Give your answers to 1 decimal place.", _deg_set(sols), sol,
              "Get tan x on its own, use tan⁻¹, then add 180°", ms)


_TRIPLES = ((3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29))


def _tr_5(rng: random.Random) -> Draft:
    """sin² x + cos² x = 1 and tan x = sin x / cos x (fraction)."""
    a, b, c = rng.choice(_TRIPLES)
    if rng.random() < 0.5:
        a, b = b, a                       # a = opposite, b = adjacent, c = hypotenuse
    obtuse = rng.random() < 0.3
    vals = {"sin": Fraction(a, c), "cos": Fraction(b, c), "tan": Fraction(a, b)}
    if obtuse:
        vals["cos"], vals["tan"] = -vals["cos"], -vals["tan"]
    given, want = rng.choice([("sin", "cos"), ("sin", "tan"), ("cos", "sin"), ("cos", "tan"), ("tan", "sin"), ("tan", "cos")]
                             if not obtuse else [("sin", "cos"), ("sin", "tan")])
    val = vals[want]
    kind = "obtuse" if obtuse else "acute"
    if given == "tan":
        step = f"tan x = {a}/{b}, so take opposite {a} and adjacent {b}: hypotenuse = √({a}² + {b}²) = {c}"
    elif given == "sin":
        step = f"cos² x = 1 - ({a}/{c})² = {c * c - a * a}/{c * c}, so cos x = {'-' if obtuse else ''}{b}/{c}"
    else:
        step = f"sin² x = 1 - ({b}/{c})² = {c * c - b * b}/{c * c}, so sin x = {a}/{c}"
    if obtuse:
        step += " (cos is negative for an obtuse angle)"
    tail = f"{want} x = {frac_str(val)}"
    sol = step if tail in step else f"{step}. So {tail}" + (" (tan x = sin x ÷ cos x)" if want == "tan" else "")
    ms = []
    if want == "tan":
        ms.append(_frac_mis(1 / val, "tan x = sin x ÷ cos x (opposite ÷ adjacent) — you divided the other way up"))
    if obtuse:
        ms.append(_frac_mis(-val, "x is obtuse, so cos x and tan x are negative"))
    if given == "sin" and want == "cos":
        ms.append(_frac_mis(1 - vals["sin"], "Use sin² x + cos² x = 1: square the sine first, then take a square root"))
    return _q(f"Given that {given} x = {frac_str(vals[given])} and x is {kind}, find the exact value of {want} x.",
              _frac(val), sol, "Use sin² x + cos² x = 1 and tan x = sin x ÷ cos x (or sketch a right-angled triangle)", ms)


# ==================================================== registration

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
        level_fallback = d.pop("fallback", "") or fallback   # a level whose method differs gives its own
        ch = d.pop("choice", None)
        if ch is not None:
            stem, options, correct, feedback = ch
            text, answer, ms = build_choice(stem, options, correct, seed, feedback)
            d.update(text=text, answer=answer, mistakes=list(ms))
        p = build(sid, level, seed, fallback_hint=level_fallback, **d)
        return replace(p, ref=f"{sid}#{ref}") if ref else p

    generate.__name__ = f"generate_{name}"
    generate.__qualname__ = generate.__name__
    return Skill(id=sid, subject=SUBJECT_ID, title=title, aliases=aliases, generate=generate)


SKILLS: tuple[Skill, ...] = (
    _skill("functions", "Functions",
           ("composite function", "inverse function", "functions", "fg(x)", "domain", "composite functions",
            "inverse functions", "function notation"),
           (_fn_1, _fn_2, _fn_3, _fn_4, _fn_5),
           "Write out what the function notation means before you substitute"),
    _skill("polynomials", "Factor theorem & completing the square",
           ("factor theorem", "remainder theorem", "completing the square", "cubic", "turning point",
            "cubics", "polynomials", "polynomial"),
           (_pol_1, _pol_2, _pol_3, _pol_4, _pol_5),
           "If (x - a) is a factor of f(x), then f(a) = 0"),
    _skill("coordinates", "Coordinate geometry",
           ("equation of a circle", "coordinate geometry", "midpoint", "perpendicular gradient",
            "distance between points", "gradient", "circle equation", "perpendicular lines"),
           (_co_1, _co_2, _co_3, _co_4, _co_5),
           "Sketch the points first and label the differences in x and in y"),
    _skill("calculus", "Differentiation",
           ("differentiation", "differentiate", "dy/dx", "stationary points", "gradient function",
            "calculus", "stationary point", "derivative"),
           (_ca_1, _ca_2, _ca_3, _ca_4, _ca_5),
           "Differentiate term by term: axⁿ becomes naxⁿ⁻¹"),
    _skill("matrices", "Matrices",
           ("matrix multiplication", "matrices", "matrix", "identity matrix", "transformation matrix",
            "transformation matrices", "2x2 matrices"),
           (_ma_1, _ma_2, _ma_3, _ma_4, _ma_5),
           "Multiply a row of the first matrix by a column of the second"),
    _skill("trigonometry", "Trigonometry",
           ("exact trig values", "trig equations", "trig identities", "sin cos tan", "exact values",
            "trigonometric equations", "trigonometric identities"),
           (_tr_1, _tr_2, _tr_3, _tr_4, _tr_5),
           "Sketch the graph of sin, cos or tan between 0° and 360°"),
)


# ========================================================= topics

_ROWS = (
    (("algebra", "Algebra & functions", ("functions", "polynomials")),
     ("coordinates", "Coordinate geometry", ("coordinates",))),
    (("calculus", "Calculus", ("calculus",)),
     ("matrices_trig", "Matrices & trigonometry", ("matrices", "trigonometry"))),
)


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"{SUBJECT_ID}.y{y}.{slug}", label=label,
                    skills=tuple(f"{SUBJECT_ID}.{s}" for s in skills), level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Further Maths", order=22, years={10: _year(10), 11: _year(11)})


def register(reg) -> None:
    """Register Further Maths and its skills with a tutor.content Registry."""
    reg.register(make_subject(), list(SKILLS))
