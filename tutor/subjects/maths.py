"""Maths: 20 generated skills and the Years 7–11 topic maps (docs/ARCHITECTURE.md section 5).

Every generator is pure: ``generate(level, seed)`` uses only ``random.Random(seed)``.
Problems are built backwards from nice answers; every answer is computed from the
numbers exactly as they are printed in the question text.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Callable

from ..content.base import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec
from ..content.fmt import (
    acosd, asind, atand, build, check_level, cosd, fmt_dp, fmt_num, frac_str, group,
    is_whole, lin_factor, mixed_str, money, money_text, near_half, num_answer,
    num_mistake, poly, poly_mul, retry, sig_digits, signed, sind, std_answer,
    std_mistake, sup, tand, terms, unit,
)

SUBJECT_ID = "maths"

NAMES = ("Amy", "Ben", "Chloe", "Dev", "Ella", "Finn", "Grace", "Harry", "Isla", "Jack",
         "Leah", "Mia", "Noah", "Omar", "Priya", "Sam", "Tom", "Zara")
ITEMS = ("a jacket", "a bike", "a TV", "a laptop", "a phone", "a sofa", "a games console",
         "a pair of trainers", "a watch", "a camera")
LENGTH_UNITS = ("cm", "cm", "m", "mm")

Draft = dict


# ================================================================ helpers

def _q(text: str, answer: Answer, solution: str, hint: str,
       mistakes: list[Mistake | None] | tuple = ()) -> Draft:
    return {"text": text, "answer": answer, "solution": solution, "hint": hint,
            "mistakes": list(mistakes)}


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _disp(v, u: str = "", dp: int | None = None) -> str:
    if u == "£":
        if dp is not None or not is_whole(v):
            return "£" + fmt_dp(v, 2 if dp is None else dp)
        return money(v)
    return unit(fmt_dp(v, dp) if dp is not None else fmt_num(v), u)


def _ans(v, u: str = "", dp: int | None = None) -> Answer:
    return num_answer(v, _disp(v, u, dp), dp=dp)


def _mis(v, u: str, fb: str, dp: int | None = None) -> Mistake | None:
    return num_mistake(v, u, fb, dp=dp)


def _approx(v: float) -> str:
    """Calculator display for working: 3 d.p. followed by '…' when inexact."""
    r3 = round(v, 3)
    if abs(v - r3) < 1e-9:
        return fmt_num(r3)
    t = math.trunc(v * 1000) / 1000
    return f"{t:.3f}…"


def _pick_coprime(rng: random.Random, lo: int, hi: int, d: int) -> int:
    cands = [n for n in range(lo, hi) if math.gcd(n, d) == 1]
    return rng.choice(cands)


def _frac_answer(f: Fraction, simplest: bool = True, mixed: bool = False, prefix: str = "") -> Answer:
    shown = mixed_str(f) if mixed else frac_str(f)
    return Answer(kind="fraction", display=prefix + shown, value=frac_str(f),
                  form="simplest" if simplest else "any")


def _frac_mis(num: int, den: int, fb: str, prefix: str = "") -> Mistake | None:
    if den == 0:
        return None
    f = Fraction(num, den)
    return Mistake(Answer(kind="fraction", display=prefix + frac_str(f), value=frac_str(f)), fb)


def _fmis(f: Fraction | None, fb: str, prefix: str = "") -> Mistake | None:
    if f is None:
        return None
    return Mistake(Answer(kind="fraction", display=prefix + frac_str(f), value=frac_str(f)), fb)


def _x_answer(x: Fraction, var: str = "x") -> Answer:
    x = Fraction(x)
    if x.denominator == 1:
        return num_answer(x, f"{var} = {x.numerator}")
    return Answer(kind="fraction", display=f"{var} = {frac_str(x)}", value=frac_str(x))


def _x_mis(x: Fraction | None, fb: str, var: str = "x") -> Mistake | None:
    if x is None:
        return None
    return Mistake(_x_answer(Fraction(x), var), fb)


def _safe_div(a, b) -> Fraction | None:
    if b == 0:
        return None
    return Fraction(a) / Fraction(b)


def _expr_answer(coeffs: list[int], var: str = "x", form: str = "expanded") -> Answer:
    d, v = poly(coeffs, var)
    return Answer(kind="expr", display=d, value=v, form=form, var=var)


def _expr_mis(coeffs: list[int], fb: str, var: str = "x") -> Mistake:
    d, v = poly(coeffs, var)
    return Mistake(Answer(kind="expr", display=d, value=v, var=var), fb)


def _factors(fs: list[tuple[int, int]], var: str = "x") -> tuple[str, str]:
    parts = [lin_factor(m, p, var) for m, p in fs]
    return "".join(d for d, _ in parts), "*".join(v for _, v in parts)


def _fact_answer(fs: list[tuple[int, int]]) -> Answer:
    d, v = _factors(fs)
    return Answer(kind="expr", display=d, value=v, form="factorised")


def _fact_mis(fs: list[tuple[int, int]], fb: str) -> Mistake:
    d, v = _factors(fs)
    return Mistake(Answer(kind="expr", display=d, value=v), fb)


def _roots_answer(roots: list[int]) -> Answer:
    rs = sorted(roots)
    return Answer(kind="set", display=" or ".join(f"x = {r}" for r in rs),
                  value=[str(r) for r in rs])


def _roots_mis(roots: list, fb: str) -> Mistake | None:
    rs = sorted(roots)
    if len(set(rs)) != len(rs):
        return None
    return Mistake(Answer(kind="set", display=" or ".join(f"x = {fmt_num(r)}" for r in rs),
                          value=[fmt_num(r) for r in rs]), fb)


def _assign(x: int, y: int) -> Answer:
    return Answer(kind="assign", display=f"x = {x}, y = {y}", value={"x": str(x), "y": str(y)})


def _assign_mis(x: int, y: int, fb: str) -> Mistake:
    return Mistake(_assign(x, y), fb)


def _std_txt(m: Fraction, e: int) -> str:
    return f"{fmt_num(m)} × 10^{e}"


def _pf(n: int) -> dict[int, int]:
    out: dict[int, int] = {}
    p = 2
    while p * p <= n:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def _pf_str(fac: dict[int, int]) -> str:
    return " × ".join(f"{p}{sup(e) if e > 1 else ''}" for p, e in sorted(fac.items()) if e > 0)


def _lcm(a: int, b: int) -> int:
    return a * b // math.gcd(a, b)


def _sq_root(s: int, u: str) -> tuple[Answer, str, str]:
    """(answer, value text for working, rounding sentence) for √s."""
    r = math.isqrt(s)
    if r * r == s:
        return _ans(r, u), str(r), ""
    v = math.sqrt(s)
    return _ans(v, u, 1), _approx(v), " Give your answer to 1 decimal place."


def _root_mis(s: float, u: str, fb: str) -> Mistake | None:
    if s is None or s <= 0:
        return None
    r = math.isqrt(int(s)) if float(s).is_integer() else -1
    if r >= 0 and r * r == s:
        return _mis(r, u, fb)
    return _mis(math.sqrt(s), u, fb, dp=1)


def _sqrt_ok(s: int) -> bool:
    """True if √s is a perfect square or is not on a 1 d.p. rounding boundary."""
    r = math.isqrt(s)
    return r * r == s or not near_half(math.sqrt(s), 1)


# ============================================================ percentages

def _pct_1(rng: random.Random) -> Draft:
    p = rng.choice((10, 25, 50))
    if p == 10:
        amt = rng.randrange(2, 60) * 10
    elif p == 25:
        amt = rng.randrange(2, 50) * 4
    else:
        amt = rng.randrange(2, 100) * 2
    u = rng.choice(("£", "£", "kg", "m", "g", "cm"))
    ans = Fraction(amt * p, 100)
    way, by = {10: ("10% is one tenth, so divide by 10", 10),
               25: ("25% is one quarter, so divide by 4", 4),
               50: ("50% is one half, so divide by 2", 2)}[p]
    hint = {10: "10% is the same as one tenth", 25: "25% is the same as one quarter",
            50: "50% is the same as one half"}[p]
    wrong = {10: (Fraction(amt, 100), "That's 1% — to find 10%, divide by 10"),
             25: (Fraction(amt, 25), "To find 25%, divide by 4 (25% is one quarter), not by 25"),
             50: (Fraction(amt * 2), "50% is one half, so divide by 2 rather than multiplying")}[p]
    return _q(f"Work out {p}% of {_disp(amt, u)}.", _ans(ans, u),
              f"{way}: {_disp(amt, u)} ÷ {by} = {_disp(ans, u)}", hint,
              [_mis(wrong[0], u, wrong[1]),
               _mis(amt - ans, u, f"That's what is left after taking off {p}% — the question asks for {p}% of the amount")])


def _pct_2(rng: random.Random) -> Draft:
    def pick(r):
        p, amt = r.randrange(3, 98), r.randrange(12, 500)
        return None if (p * amt) % 10 in (0, 5) else (p, amt)
    p, amt = retry(pick, rng)
    u = rng.choice(("kg", "m", "km", "litres", "g", "cm"))
    ans = Fraction(p * amt, 100)
    d = fmt_num(Fraction(p, 100))
    fb = f"Check the decimal point: {p}% = {p} ÷ 100 = {d}"
    return _q(f"Work out {p}% of {amt} {u}. Give your answer to 1 decimal place.",
              _ans(ans, u, 1),
              f"{p}% = {d}, so {d} × {amt} = {fmt_num(ans)} = {_disp(ans, u, 1)} (1 d.p.)",
              f"Write {p}% as a decimal by dividing {p} by 100, then multiply by {amt}",
              [_mis(ans * 10, u, fb, dp=1), _mis(ans / 10, u, fb, dp=1)])


def _pct_3(rng: random.Random) -> Draft:
    item = rng.choice(ITEMS)
    up = rng.random() < 0.5
    p = rng.choice((3, 5, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 60))
    price = rng.randrange(4, 120) * 5
    change = Fraction(price * p, 100)
    new = price + change if up else price - change
    P, C, N = money(price), _disp(change, "£"), _disp(new, "£")
    if up:
        text = f"{_cap(item)} costs {money_text(price)}. Its price goes up by {p}%. Work out the new price."
        sol = f"{p}% of {P} = {C}, so the new price is {P} + {C} = {N}"
        hint = f"Find {p}% of {money_text(price)} first, then add it on"
        ms = [_mis(change, "£", f"It looks like you found {p}% but didn't add it on"),
              _mis(price - change, "£", f"This is an increase, so add the {p}% on rather than taking it off")]
    else:
        text = (f"In a sale, {item} that normally costs {money_text(price)} is reduced by {p}%. "
                f"Work out the sale price.")
        sol = f"{p}% of {P} = {C}, so the sale price is {P} − {C} = {N}"
        hint = f"Find {p}% of {money_text(price)} first, then take it off"
        ms = [_mis(change, "£", f"It looks like you found the {p}% reduction but didn't take it off"),
              _mis(price + change, "£", f"This is a reduction, so take the {p}% off rather than adding it on")]
    return _q(text, _ans(new, "£"), sol, hint, ms)


def _pct_4(rng: random.Random) -> Draft:
    if rng.random() < 0.5:
        orig, p = rng.randrange(1, 50) * 100, rng.randrange(2, 61)
    else:
        orig, p = rng.randrange(2, 60) * 20, rng.randrange(1, 13) * 5
    up = rng.random() < 0.5
    change = orig * p // 100
    new = orig + change if up else orig - change
    word = "increase" if up else "decrease"
    if rng.random() < 0.5:
        text = (f"The price of {rng.choice(ITEMS)} changes from {money_text(orig)} to "
                f"{money_text(new)}. Work out the percentage {word}.")
        o_s, c_s = money(orig), money(change)
    else:
        place = rng.choice(("a museum", "a zoo", "a cinema", "a theme park", "a library"))
        text = (f"The number of visitors to {place} went from {group(orig)} one year to "
                f"{group(new)} the next year. Work out the percentage {word}.")
        o_s, c_s = group(orig), group(change)
    by_new = Fraction(change * 100, new)
    return _q(text, _ans(p, "%"),
              f"The {word} is {c_s}. {change} ÷ {orig} × 100 = {p}%",
              f"Work out the {word} first, then divide it by the original amount",
              [_mis(by_new, "%", f"Divide the change by the original amount ({o_s}), not by the new amount",
                    dp=None if is_whole(by_new) else 1),
               _mis(Fraction(p, 100), "", "Multiply by 100 to turn the decimal into a percentage"),
               _mis(change, "", "That's the actual change — divide it by the original amount and multiply by 100")])


def _pct_5(rng: random.Random) -> Draft:
    kind = rng.choice(("rev_up", "rev_down", "compound", "depreciate"))
    if kind in ("rev_up", "rev_down"):
        orig = rng.randrange(2, 100) * 20
        p = rng.randrange(1, 13) * 5
        item = rng.choice(ITEMS)
        if kind == "rev_up":
            new = orig * (100 + p) // 100
            mult = fmt_num(Fraction(100 + p, 100))
            text = (f"After a {p}% increase, the price of {item} is {money_text(new)}. "
                    f"Work out the price before the increase.")
            sol = f"The new price is {100 + p}% of the original, so the original = {money(new)} ÷ {mult} = {money(orig)}"
            hint = f"The new price is {100 + p}% of the original price"
            ms = [_mis(Fraction(new * (100 - p), 100), "£",
                       f"The {p}% was added to the original price, not the new one — divide by {mult} instead of taking {p}% off")]
        else:
            new = orig * (100 - p) // 100
            mult = fmt_num(Fraction(100 - p, 100))
            text = (f"In a sale, all prices are reduced by {p}%. {_cap(item)} costs "
                    f"{money_text(new)} in the sale. Work out its original price.")
            sol = f"The sale price is {100 - p}% of the original, so the original = {money(new)} ÷ {mult} = {money(orig)}"
            hint = f"The sale price is {100 - p}% of the original price"
            ms = [_mis(Fraction(new * (100 + p), 100), "£",
                       f"The {p}% was taken off the original price, not the sale price — divide by {mult} instead of adding {p}% on")]
        return _q(text, _ans(orig, "£"), sol, hint, ms)

    def pick(r):
        if kind == "compound":
            P = r.choice((500, 800, 1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000))
            rate = r.choice((Fraction(3, 2), Fraction(2), Fraction(5, 2), Fraction(3), Fraction(7, 2),
                             Fraction(4), Fraction(9, 2), Fraction(5), Fraction(6)))
            n = r.randrange(2, 7)
            m = 1 + rate / 100
        else:
            P = r.choice((6000, 8000, 10000, 12000, 15000, 18000, 20000, 24000))
            rate = Fraction(r.choice((5, 8, 10, 12, 15, 20, 25)))
            n = r.randrange(2, 6)
            m = 1 - rate / 100
        A = P * m ** n
        return None if near_half(A, 2) else (P, rate, n, m, A)
    P, rate, n, m, A = retry(pick, rng)
    ms_, rs = fmt_num(m), fmt_num(rate)
    shown = "£" + fmt_dp(A, 2)
    sol_tail = f"{money(P)} × {ms_}{sup(n)} = {shown} (to the nearest penny)"
    if kind == "compound":
        text = (f"{money_text(P)} is invested in a savings account that pays {rs}% compound interest "
                f"per year. Work out the value of the investment after {n} years. "
                f"Give your answer to the nearest penny.")
        sol = f"Multiplier = 1 + {rs} ÷ 100 = {ms_}. {sol_tail}"
        ms = [_mis(P * (1 + rate * n / 100), "£",
                   f"That's simple interest — with compound interest you multiply by {ms_} once for every year", dp=2),
              _mis(A - P, "£", f"That's only the interest — add it to the {money(P)} that was invested", dp=2)]
    else:
        text = (f"A car is bought for {money_text(P)}. Its value falls by {rs}% each year. "
                f"Work out its value after {n} years. Give your answer to the nearest penny.")
        sol = f"Multiplier = 1 − {rs} ÷ 100 = {ms_}. {sol_tail}"
        ms = [_mis(P * (1 - rate * n / 100), "£",
                   f"That takes {rs}% of the original price off every year — the {rs}% comes off the new, lower value each year, so multiply by {ms_} once for every year", dp=2),
              _mis(P - A, "£", f"That's how much value the car has lost — take it away from {money(P)}", dp=2)]
    return _q(text, num_answer(A, shown, dp=2), sol, f"Each year the amount is multiplied by {ms_}", ms)


# ============================================================== fractions

def _fr_1(rng: random.Random) -> Draft:
    q = rng.randrange(3, 13)
    p = _pick_coprime(rng, q + 1, 3 * q, q) if rng.random() < 0.2 else _pick_coprime(rng, 1, q, q)
    k = rng.randrange(2, 10)
    a, b = p * k, q * k
    return _q(f"Write {a}/{b} as a fraction in its simplest form.",
              _frac_answer(Fraction(p, q)),
              f"The highest common factor of {a} and {b} is {k}: {a} ÷ {k} = {p} and {b} ÷ {k} = {q}, so the answer is {p}/{q}",
              f"Find the highest common factor of {a} and {b}, then divide the top and the bottom by it",
              [_frac_mis(q, p, "Keep the numerator on the top and the denominator on the bottom")])


def _fr_2(rng: random.Random) -> Draft:
    def pick(r):
        op = r.choice("+-")
        if r.random() < 0.5:
            d = r.randrange(5, 16)
            a, b = _pick_coprime(r, 1, d, d), _pick_coprime(r, 1, d, d)
            if op == "-" and a < b:
                a, b = b, a
            if a == b:
                return None
            res = Fraction(a + b, d) if op == "+" else Fraction(a - b, d)
            if res.denominator == 1:
                return None
            num = a + b if op == "+" else a - b
            word = "add" if op == "+" else "subtract"
            sol = f"The denominators are the same, so {word} the numerators: {a} {'+' if op == '+' else '−'} {b} = {num}, giving {num}/{d}"
            if res.denominator != d:
                sol += f" = {frac_str(res)}"
            ms = [_frac_mis(num, 2 * d, "Keep the denominator the same — only add the numerators")] if op == "+" else []
            return (f"Work out {a}/{d} {op} {b}/{d}.", res, sol,
                    "The denominators are already the same, so you only need to work with the numerators", ms)
        d1 = r.randrange(2, 7)
        m = r.randrange(2, 5)
        d2 = d1 * m
        a, b = _pick_coprime(r, 1, d1, d1), _pick_coprime(r, 1, d2, d2)
        x1, y1, x2, y2 = (a, d1, b, d2) if r.random() < 0.5 else (b, d2, a, d1)
        f1, f2 = Fraction(x1, y1), Fraction(x2, y2)
        if op == "-" and f1 < f2:
            x1, y1, x2, y2, f1, f2 = x2, y2, x1, y1, f2, f1
        res = f1 + f2 if op == "+" else f1 - f2
        if res <= 0 or res.denominator == 1:
            return None
        n1, n2 = x1 * d2 // y1, x2 * d2 // y2
        num = n1 + n2 if op == "+" else n1 - n2
        sym = "+" if op == "+" else "−"
        sol = f"Write {a}/{d1} as {a * m}/{d2}. Then {n1}/{d2} {sym} {n2}/{d2} = {num}/{d2}"
        if res.denominator != d2:
            sol += f" = {frac_str(res)}"
        word = "add" if op == "+" else "subtract"
        ms = [_frac_mis(x1 + x2 if op == "+" else x1 - x2, y1 + y2 if op == "+" else y1 - y2,
                        f"You can't {word} the denominators — write both fractions with denominator {d2} first"),
              _frac_mis(x1 + x2 if op == "+" else x1 - x2, d2,
                        f"When you change {a}/{d1} into {d2}ths, multiply the numerator by {m} as well")]
        return (f"Work out {x1}/{y1} {op} {x2}/{y2}.", res, sol,
                f"Write {a}/{d1} as an equivalent fraction with denominator {d2}", ms)
    text, res, sol, hint, ms = retry(pick, rng)
    text = text.replace("-", "−") + " Give your answer as a fraction in its simplest form."
    return _q(text, _frac_answer(res), sol, hint, ms)


def _fr_3(rng: random.Random) -> Draft:
    def pick(r):
        d1, d2 = r.randrange(2, 13), r.randrange(2, 13)
        if d1 == d2 or d1 % d2 == 0 or d2 % d1 == 0:
            return None
        a, b = _pick_coprime(r, 1, d1, d1), _pick_coprime(r, 1, d2, d2)
        op = r.choice("+-")
        f1, f2 = Fraction(a, d1), Fraction(b, d2)
        if op == "-" and f1 < f2:
            a, b, d1, d2, f1, f2 = b, a, d2, d1, f2, f1
        res = f1 + f2 if op == "+" else f1 - f2
        if res <= 0 or res.denominator == 1:
            return None
        return a, d1, b, d2, op, res
    a, d1, b, d2, op, res = retry(pick, rng)
    L = _lcm(d1, d2)
    A, B = a * L // d1, b * L // d2
    num = A + B if op == "+" else A - B
    sym, word = ("+", "add") if op == "+" else ("−", "subtract")
    sol = (f"Use the common denominator {L}: {a}/{d1} = {A}/{L} and {b}/{d2} = {B}/{L}. "
           f"{A}/{L} {sym} {B}/{L} = {num}/{L}")
    if res.denominator != L:
        sol += f" = {frac_str(res)}"
    return _q(f"Work out {a}/{d1} {sym} {b}/{d2}. Give your answer as a fraction in its simplest form.",
              _frac_answer(res), sol, f"Find a common denominator for {d1} and {d2}",
              [_frac_mis(a + b if op == "+" else a - b, d1 + d2 if op == "+" else d1 - d2,
                         f"You can't {word} the denominators — change both fractions to the same denominator first"),
               _frac_mis(a + b if op == "+" else a - b, L,
                         "When you change the denominator, multiply the numerator by the same number")])


def _fr_4(rng: random.Random) -> Draft:
    b, d = rng.randrange(2, 11), rng.randrange(2, 11)
    a, c = _pick_coprime(rng, 1, b, b), _pick_coprime(rng, 1, d, d)
    if rng.random() < 0.5:
        res = Fraction(a * c, b * d)
        sol = f"Multiply the numerators and the denominators: {a} × {c} = {a * c} and {b} × {d} = {b * d}, so {a * c}/{b * d}"
        if res.denominator != b * d:
            sol += f" = {frac_str(res)}"
        return _q(f"Work out {a}/{b} × {c}/{d}. Give your answer in its simplest form.",
                  _frac_answer(res), sol, "Multiply the numerators together and the denominators together",
                  [_frac_mis(a * d, b * c, "That's what you get when you divide — to multiply, just multiply the tops and multiply the bottoms"),
                   _frac_mis(a + c, b + d, "To multiply fractions, multiply the numerators and the denominators — don't add them")])
    res = Fraction(a * d, b * c)
    sol = f"Flip the second fraction and multiply: {a}/{b} × {d}/{c} = {a * d}/{b * c}"
    if res.denominator != b * c or res.denominator == 1:
        sol += f" = {frac_str(res)}"
    return _q(f"Work out {a}/{b} ÷ {c}/{d}. Give your answer in its simplest form.",
              _frac_answer(res), sol, f"Dividing by {c}/{d} is the same as multiplying by {d}/{c}",
              [_frac_mis(a * c, b * d, "To divide, flip the second fraction and then multiply"),
               _frac_mis(b * c, a * d, "Flip the second fraction (the one you are dividing by), not the first one")])


def _fr_5(rng: random.Random) -> Draft:
    def part(r, lo, hi):
        d = r.randrange(2, 10)
        n = _pick_coprime(r, 1, d, d)
        w = r.randrange(lo, hi + 1)
        return w, Fraction(n, d)

    def pick(r):
        (w1, f1), (w2, f2) = part(r, 1, 4), part(r, 1, 3)
        F1, F2 = w1 + f1, w2 + f2
        op = r.choice("+−×÷")
        if op == "−" and F1 < F2:
            w1, f1, w2, f2, F1, F2 = w2, f2, w1, f1, F2, F1
        res = {"+": F1 + F2, "−": F1 - F2, "×": F1 * F2, "÷": F1 / F2}[op]
        if res < 1 or res.denominator == 1:
            return None
        return w1, f1, w2, f2, F1, F2, op, res
    w1, f1, w2, f2, F1, F2, op, res = retry(pick, rng)
    i1, i2 = frac_str(F1), frac_str(F2)
    if op in "+−":
        L = _lcm(F1.denominator, F2.denominator)
        A, B = F1.numerator * L // F1.denominator, F2.numerator * L // F2.denominator
        num = A + B if op == "+" else A - B
        sol = f"As improper fractions: {i1} {op} {i2} = {A}/{L} {op} {B}/{L} = {num}/{L} = {mixed_str(res)}"
    elif op == "×":
        sol = (f"As improper fractions: {i1} × {i2} = {F1.numerator * F2.numerator}/"
               f"{F1.denominator * F2.denominator} = {mixed_str(res)}")
    else:
        sol = (f"As improper fractions, then flip the second: {i1} × {F2.denominator}/{F2.numerator} = "
               f"{F1.numerator * F2.denominator}/{F1.denominator * F2.numerator} = {mixed_str(res)}")
    ms: list[Mistake | None] = []
    if op == "×":
        ms.append(_fmis(w1 * w2 + f1 * f2, "You can't multiply the whole numbers and the fractions separately — change them to improper fractions first"))
    elif op == "÷":
        ms.append(_fmis(Fraction(w1, w2) + f1 / f2, "You can't divide the whole numbers and the fractions separately — change them to improper fractions first"))
        ms.append(_fmis(F1 * F2, "To divide, flip the second fraction and then multiply"))
    elif op == "+":
        ms.append(_fmis(w1 + w2 + Fraction(f1.numerator + f2.numerator, f1.denominator + f2.denominator),
                        "Add the fractions using a common denominator — don't add the denominators"))
    elif f1 < f2:
        ms.append(_fmis(w1 - w2 + f2 - f1, "The second fraction is bigger, so you can't just swap them round — borrow 1 from the whole number or use improper fractions"))
    return _q(f"Work out {mixed_str(F1)} {op} {mixed_str(F2)}. Give your answer as a mixed number in its simplest form.",
              _frac_answer(res, mixed=True), sol, "Change both mixed numbers into improper fractions first", ms)


# ================================================================== ratio

_UNIT_PAIRS = (("cm", "m", 100, 5), ("g", "kg", 1000, 50), ("minutes", "hours", 60, 5),
               ("p", "£", 100, 5), ("mm", "cm", 10, 1))


def _ratio_answer(parts: list[int], simplest: bool = True) -> Answer:
    return Answer(kind="ratio", display=" : ".join(str(x) for x in parts), value=list(parts),
                  form="simplest" if simplest else "any")


def _ratio_mis(parts: list[int], fb: str) -> Mistake | None:
    if any(x <= 0 for x in parts):
        return None
    return Mistake(Answer(kind="ratio", display=" : ".join(str(x) for x in parts), value=list(parts)), fb)


def _simplify(parts: list[int]) -> list[int]:
    g = 0
    for x in parts:
        g = math.gcd(g, x)
    return [x // g for x in parts]


def _amount(n: int, small: str, big: str, which: str) -> str:
    if which == "small":
        return f"{n}p" if small == "p" else f"{n} {small}"
    if big == "£":
        return f"£{n}"
    if big == "hours" and n == 1:
        return "1 hour"
    return f"{n} {big}"


def _ratio_1(rng: random.Random) -> Draft:
    if rng.random() < 0.3:
        def pick(r):
            small, big, f, step = r.choice(_UNIT_PAIRS)
            B = r.randrange(1, 6)
            s = r.randrange(1, (f * B * 2) // step) * step
            if s == f * B:
                return None
            parts = _simplify([s, f * B])
            if max(parts) > 60 or parts[0] == parts[1]:
                return None
            return small, big, f, B, s, parts
        small, big, f, B, s, parts = retry(pick, rng)
        a_txt, b_txt = _amount(s, small, big, "small"), _amount(B, small, big, "big")
        conv = f"{b_txt} = {_amount(f * B, small, big, 'small')}"
        g = s // parts[0]
        return _q(f"Write {a_txt} : {b_txt} as a ratio in its simplest form.",
                  _ratio_answer(parts),
                  f"Use the same units: {conv}. So {s} : {f * B}, and dividing both by {g} gives {parts[0]} : {parts[1]}",
                  "Change both amounts into the same units first",
                  [_ratio_mis(_simplify([s, B]), f"Change both amounts into the same units first: {conv}"),
                   _ratio_mis([parts[1], parts[0]], "Keep the parts in the same order as in the question")])
    if rng.random() < 0.25:
        def pick3(r):
            p = [r.randrange(1, 8) for _ in range(3)]
            return p if _simplify(p) == p and len(set(p)) > 1 else None
        parts = retry(pick3, rng)
    else:
        def pick2(r):
            a, b = r.randrange(1, 10), r.randrange(1, 10)
            return [a, b] if a != b and math.gcd(a, b) == 1 else None
        parts = retry(pick2, rng)
    k = rng.randrange(2, 13)
    big = [x * k for x in parts]
    shown = " : ".join(str(x) for x in big)
    return _q(f"Write {shown} in its simplest form.", _ratio_answer(parts),
              f"Divide every part by the highest common factor, {k}: {' : '.join(str(x) for x in parts)}",
              f"Find the highest common factor of {', '.join(str(x) for x in big[:-1])} and {big[-1]}",
              [_ratio_mis(list(reversed(parts)), "Keep the parts in the same order as in the question")])


def _shares_answer(vals: list[int]) -> Answer:
    shown = [money(v) for v in vals]
    disp = shown[0] + " and " + shown[1] if len(vals) == 2 else ", ".join(shown[:-1]) + " and " + shown[-1]
    return Answer(kind="set", display=disp, value=[str(v) for v in vals], ordered=True)


def _shares_mis(vals: list, fb: str) -> Mistake | None:
    if any(not is_whole(v) for v in vals):
        return None
    vals = [int(v) for v in vals]
    m = _shares_answer(vals)
    return Mistake(m, fb)


def _ratio_2(rng: random.Random) -> Draft:
    def pick(r):
        a, b = r.randrange(1, 10), r.randrange(1, 10)
        return (a, b) if a != b and math.gcd(a, b) == 1 else None
    a, b = retry(pick, rng)
    u = rng.randrange(2, 31)
    total = (a + b) * u
    n1, n2 = rng.sample(NAMES, 2)
    sol = (f"{a} + {b} = {a + b} parts, so 1 part = {money(total)} ÷ {a + b} = {money(u)}. "
           f"{n1}: {a} × {money(u)} = {money(a * u)}, {n2}: {b} × {money(u)} = {money(b * u)}")
    ms = [_shares_mis([b * u, a * u], f"Check the order: {n1} gets {a} parts, so give {n1}'s share first")]
    if total % a == 0 and total % b == 0:
        ms.append(_shares_mis([total // a, total // b],
                              f"Add the parts first: {a} + {b} = {a + b} parts, then find one part"))
    return _q(f"{n1} and {n2} share {money_text(total)} in the ratio {a} : {b}. Work out how much each of them gets. Give {n1}'s share first.",
              _shares_answer([a * u, b * u]), sol, "Add the parts of the ratio to find the total number of parts", ms)


def _ratio_3(rng: random.Random) -> Draft:
    def pick(r):
        p = [r.randrange(1, 8) for _ in range(3)]
        return p if _simplify(p) == p and len(set(p)) > 1 else None
    parts = retry(pick, rng)
    u = rng.randrange(2, 21)
    s = sum(parts)
    total = s * u
    names = rng.sample(NAMES, 3)
    vals = [x * u for x in parts]
    sol = (f"{' + '.join(str(x) for x in parts)} = {s} parts, so 1 part = {money(total)} ÷ {s} = {money(u)}. "
           + ", ".join(f"{nm}: {x} × {money(u)} = {money(x * u)}" for nm, x in zip(names, parts)))
    ms = []
    if total % 3 == 0:
        ms.append(_shares_mis([total // 3] * 3, f"Share it in the ratio, not equally — add the parts first ({s} parts)"))
    ms.append(_shares_mis(list(reversed(vals)), f"Keep the order of the ratio: {names[0]} gets {parts[0]} parts"))
    return _q(f"{names[0]}, {names[1]} and {names[2]} share {money_text(total)} in the ratio "
              f"{parts[0]} : {parts[1]} : {parts[2]}. Work out how much each person gets, in that order.",
              _shares_answer(vals), sol, "Add the parts of the ratio to find the total number of parts", ms)


def _ratio_4(rng: random.Random) -> Draft:
    def pick(r):
        a, b = r.randrange(1, 10), r.randrange(1, 10)
        return (a, b) if a != b and math.gcd(a, b) == 1 else None
    a, b = retry(pick, rng)
    u = rng.randrange(2, 26)
    n1, n2 = rng.sample(NAMES, 2)
    known = a * u
    head = (f"{n1} and {n2} share some money in the ratio {a} : {b}. {n1} gets {money_text(known)}. ")
    start = f"{a} parts = {money(known)}, so 1 part = {money(known)} ÷ {a} = {money(u)}. "
    hint = f"{n1}'s {a} parts are worth {money_text(known)} — find the value of 1 part"
    as_total = Fraction(known * b, a + b)
    if rng.random() < 0.6:
        return _q(head + f"How much does {n2} get?", _ans(b * u, "£"),
                  start + f"{n2} gets {b} × {money(u)} = {money(b * u)}", hint,
                  [_mis(as_total, "£", f"{money(known)} is {n1}'s share, not the total — {a} parts are worth {money(known)}",
                        dp=2),
                   _mis(known + (b - a), "£", "Ratios work by multiplying, not adding — find the value of 1 part first")])
    total = (a + b) * u
    return _q(head + "How much money do they share altogether?", _ans(total, "£"),
              start + f"Total = {a + b} × {money(u)} = {money(total)}", hint,
              [_mis(b * u, "£", f"That's {n2}'s share — add {n1}'s {money(known)} to get the total"),
               _mis(known, "£", f"{money(known)} is only {n1}'s share — find 1 part, then multiply by {a + b} parts")])


def _ratio_5(rng: random.Random) -> Draft:
    def pick(r):
        a, b = r.randrange(2, 10), r.randrange(1, 9)
        return (a, b) if a > b and math.gcd(a, b) == 1 else None
    a, b = retry(pick, rng)
    u = rng.randrange(2, 21)
    diff = (a - b) * u
    n1, n2 = rng.sample(NAMES, 2)
    head = (f"{n1} and {n2} share some money in the ratio {a} : {b}. "
            f"{n1} gets {money_text(diff)} more than {n2}. ")
    start = f"The difference is {a} − {b} = {a - b} parts = {money(diff)}, so 1 part = {money(u)}. "
    hint = f"The difference between their shares is {a} − {b} = {a - b} parts"
    common = [_mis(u, "£", "That's the value of 1 part — now multiply it by the number of parts you need")]
    one_part = f"The difference {money(diff)} is {a - b} parts, not 1 part — divide by {a - b} first"
    if rng.random() < 0.5:
        total = (a + b) * u
        return _q(head + "How much money do they share altogether?", _ans(total, "£"),
                  start + f"Total = {a + b} × {money(u)} = {money(total)}", hint,
                  common + [_mis(diff, "£", f"{money(diff)} is the difference between the shares, not the total"),
                            _mis(diff * (a + b), "£", one_part) if a - b > 1 else None])
    return _q(head + f"How much does {n2} get?", _ans(b * u, "£"),
              start + f"{n2} gets {b} × {money(u)} = {money(b * u)}", hint,
              common + [_mis(a * u, "£", f"That's {n1}'s share — {n2} gets {b} parts"),
                        _mis(diff * b, "£", one_part) if a - b > 1 else None])


# ================================================================ HCF/LCM

def _smaller_common_factor(h: int) -> int:
    for p in range(2, h + 1):
        if h % p == 0:
            return h // p
    return 1


def _hcf_1(rng: random.Random) -> Draft:
    def pick(r):
        h, m, n = r.randrange(2, 13), r.randrange(2, 8), r.randrange(2, 8)
        return (h, m, n) if m != n and math.gcd(m, n) == 1 else None
    h, m, n = retry(pick, rng)
    a, b = h * m, h * n
    return _q(f"Find the highest common factor (HCF) of {a} and {b}.", _ans(h),
              f"{a} = {h} × {m} and {b} = {h} × {n}, and {m} and {n} have no common factor, so the HCF is {h}",
              f"List the factors of {min(a, b)} and find the biggest one that also divides into {max(a, b)}",
              [_mis(h * m * n, "", "That's the LCM — the HCF is the biggest number that divides into both"),
               _mis(_smaller_common_factor(h), "", "That is a common factor, but there is a higher one")])


def _lcm_2(rng: random.Random) -> Draft:
    def pick(r):
        a, b = r.randrange(2, 16), r.randrange(2, 16)
        return (a, b) if a != b and a % b and b % a else None
    a, b = retry(pick, rng)
    L, big, small = _lcm(a, b), max(a, b), min(a, b)
    mults = ", ".join(str(big * i) for i in range(1, L // big + 1))
    return _q(f"Find the lowest common multiple (LCM) of {a} and {b}.", _ans(L),
              f"Multiples of {big}: {mults}. The first one that is also a multiple of {small} is {L}",
              f"Write out the multiples of {big} until you reach one that {small} also divides into",
              [_mis(a * b, "", f"{a * b} is a common multiple, but not the lowest one"),
               _mis(math.gcd(a, b), "", f"That's the HCF — the LCM is the smallest number that both {a} and {b} divide into")])


def _hcf_3(rng: random.Random) -> Draft:
    def pick(r):
        h, m, n = r.randrange(4, 31), r.randrange(2, 10), r.randrange(2, 10)
        if m == n or math.gcd(m, n) != 1:
            return None
        a, b = h * m, h * n
        return (h, a, b) if 30 <= a <= 250 and 30 <= b <= 250 else None
    h, a, b = retry(pick, rng)
    L = _lcm(a, b)
    pa, pb = _pf_str(_pf(a)), _pf_str(_pf(b))
    if rng.random() < 0.5:
        return _q(f"Find the highest common factor (HCF) of {a} and {b}.", _ans(h),
                  f"{a} = {pa} and {b} = {pb}. The common prime factors give the HCF: {_pf_str(_pf(h))} = {h}",
                  f"Write {a} and {b} as products of prime factors",
                  [_mis(L, "", "That's the LCM — the HCF is the biggest number that divides into both"),
                   _mis(_smaller_common_factor(h), "", "That is a common factor, but there is a higher one")])
    return _q(f"Find the lowest common multiple (LCM) of {a} and {b}.", _ans(L),
              f"{a} = {pa} and {b} = {pb}. Take every prime with its highest power: {_pf_str(_pf(L))} = {L}",
              f"Write {a} and {b} as products of prime factors",
              [_mis(h, "", "That's the HCF — the LCM is the smallest number that both numbers divide into"),
               _mis(a * b, "", f"{a * b} is a common multiple, but not the lowest one")])


def _hcf_4(rng: random.Random) -> Draft:
    def pick(r):
        ea = {p: r.choice((0, 1, 1, 2, 3)) for p in (2, 3)}
        eb = {p: r.choice((0, 1, 1, 2, 3)) for p in (2, 3)}
        for p in (5, 7):
            ea[p], eb[p] = r.choice((0, 0, 1, 2)), r.choice((0, 0, 1, 2))
        A = math.prod(p ** e for p, e in ea.items())
        B = math.prod(p ** e for p, e in eb.items())
        h = math.gcd(A, B)
        if A == B or h == 1 or A > 5000 or B > 5000:
            return None
        if sum(1 for e in ea.values() if e) < 2 or sum(1 for e in eb.values() if e) < 2:
            return None
        return ea, eb, A, B, h
    ea, eb, A, B, h = retry(pick, rng)
    L = _lcm(A, B)
    hi_shared = math.prod(p ** max(ea[p], eb[p]) for p in ea if ea[p] and eb[p])
    head = f"A = {_pf_str(ea)} and B = {_pf_str(eb)}. "
    if rng.random() < 0.5:
        return _q(head + "Find the highest common factor (HCF) of A and B. Write your answer as an ordinary number.",
                  _ans(h), f"Take the primes in both, with the lower power: {_pf_str(_pf(h))} = {h}",
                  "For the HCF, use only the primes that appear in both, each with the lower power",
                  [_mis(L, "", "That's the LCM — for the HCF use only the shared primes with the lower power"),
                   _mis(hi_shared, "", "For the HCF use the lower power of each shared prime, not the higher one")])
    return _q(head + "Find the lowest common multiple (LCM) of A and B. Write your answer as an ordinary number.",
              _ans(L), f"Take every prime that appears, with the higher power: {_pf_str(_pf(L))} = {L}",
              "For the LCM, use every prime that appears, each with the higher power",
              [_mis(h, "", "That's the HCF — for the LCM use every prime with its higher power"),
               _mis(A * B, "", "A × B is a common multiple, but not the lowest — use each prime once with its higher power")])


def _hcf_5(rng: random.Random) -> Draft:
    kind = rng.choice(("bus", "lights", "ribbon", "packs"))
    if kind in ("bus", "lights"):
        def pick(r):
            lo, hi = (6, 31) if kind == "bus" else (4, 25)
            a, b = r.randrange(lo, hi), r.randrange(lo, hi)
            if a == b or a % b == 0 or b % a == 0 or _lcm(a, b) > 180:
                return None
            if math.gcd(a, b) == 1 and r.random() < 0.7:
                return None              # prefer pairs where the LCM is less than a × b
            return a, b
        a, b = retry(pick, rng)
        L = _lcm(a, b)
        if kind == "bus":
            text = (f"Bus A leaves the bus station every {a} minutes. Bus B leaves every {b} minutes. "
                    f"Both buses leave together at 9 am. How many minutes later will they next leave together?")
            u = "minutes"
        else:
            text = (f"Two lights flash at the same moment. One flashes every {a} seconds and the other every "
                    f"{b} seconds. After how many seconds will they next flash at the same time?")
            u = "seconds"
        return _q(text, _ans(L, u), f"This is the LCM of {a} and {b}: {_pf_str(_pf(a))} and {_pf_str(_pf(b))} give {_pf_str(_pf(L))} = {L}",
                  f"You need the first number that both {a} and {b} divide into",
                  [_mis(a * b, u, f"They do meet again after {a * b} {u}, but they meet earlier than that — find the lowest common multiple"),
                   _mis(math.gcd(a, b), u, f"That's the HCF — you need a number that both {a} and {b} divide into (the LCM)")])

    def pick(r):
        h, m, n = r.randrange(3, 25), r.randrange(2, 10), r.randrange(2, 10)
        return (h, m, n) if m != n and math.gcd(m, n) == 1 and h * max(m, n) <= 200 else None
    h, m, n = retry(pick, rng)
    A, B = h * m, h * n
    sol = f"This is the HCF of {A} and {B}: {A} = {h} × {m} and {B} = {h} × {n}, so the HCF is {h}"
    hint = f"You need the biggest number that divides into both {A} and {B}"
    if kind == "ribbon":
        text = (f"Two pieces of ribbon are {A} cm and {B} cm long. Both are cut into pieces that are all the "
                f"same length, as long as possible, with nothing left over. How long is each piece?")
        u = "cm"
    else:
        name = rng.choice(NAMES)
        text = (f"{name} has {A} pencils and {B} rubbers. They are all put into identical packs, with nothing "
                f"left over. What is the greatest number of packs that can be made?")
        u = "packs"
    return _q(text, _ans(h, u), sol, hint,
              [_mis(_lcm(A, B), u, f"That's the LCM — you need a number that divides into both {A} and {B}"),
               _mis(_smaller_common_factor(h), u, "That works, but it isn't the greatest possible — find the highest common factor")])


# ========================================================== standard form

_MANT = tuple(Fraction(s) for s in ("1.2", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5", "6",
                                    "7", "8", "9", "1.1", "1.6", "2.4"))


def _mantissa(rng: random.Random, digits: int) -> int:
    if digits == 1:
        return rng.randrange(1, 10)
    lo, hi = 10 ** (digits - 1) + 1, 10 ** digits
    while True:
        k = rng.randrange(lo, hi)
        if k % 10:
            return k


def _terminating(f: Fraction) -> bool:
    d = f.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def _sf_1(rng: random.Random) -> Draft:
    digits = rng.choice((2, 2, 3))
    m_int = _mantissa(rng, digits)
    e = rng.randrange(3, 10)
    value = m_int * 10 ** (e - digits + 1)
    ans = std_answer(value)
    return _q(f"Write {group(value)} in standard form.", ans,
              f"Put the decimal point after the first digit and count how many places it moves: {e} places, so {group(value)} = {ans.display}",
              "Write it as a number between 1 and 10 multiplied by a power of 10",
              [std_mistake(Fraction(value, 10), "", f"Count how many places the decimal point moves — it's {e}, not {e - 1}"),
               std_mistake(value * 10, "", f"Count how many places the decimal point moves — it's {e}, not {e + 1}")])


def _sf_2(rng: random.Random) -> Draft:
    digits = rng.choice((1, 2, 2, 3))
    m_int = _mantissa(rng, digits)
    e = rng.randrange(-7, -1)
    mant = Fraction(m_int, 10 ** (digits - 1))
    value = mant * Fraction(10) ** e
    ans = std_answer(value)
    return _q(f"Write {fmt_num(value)} in standard form.", ans,
              f"Move the decimal point {-e} places to the right to get {fmt_num(mant)}, so the power of 10 is {e}: {ans.display}",
              "Numbers less than 1 have a negative power of 10 in standard form",
              [std_mistake(mant * Fraction(10) ** (-e), "", "Numbers less than 1 have a negative power of 10"),
               std_mistake(mant * Fraction(10) ** (e + 1), "", f"Count the places carefully: the decimal point moves {-e} places")])


def _sf_3(rng: random.Random) -> Draft:
    digits = rng.choice((2, 2, 3))
    m_int = _mantissa(rng, digits)
    mant = Fraction(m_int, 10 ** (digits - 1))
    e = rng.randrange(2, 8) if rng.random() < 0.5 else rng.randrange(-5, 0)
    value = mant * Fraction(10) ** e
    disp = group(value) if is_whole(value) else fmt_num(value)
    way = "right" if e > 0 else "left"
    fb = f"Move the decimal point exactly {abs(e)} places to the {way}"
    return _q(f"Write {_std_txt(mant, e)} as an ordinary number.", num_answer(value, disp),
              f"Move the decimal point {abs(e)} places to the {way}: {_std_txt(mant, e)} = {disp}",
              (f"10^{e} means multiplying by 10, {e} times" if e > 0 else f"10^{e} means dividing by 10, {-e} times"),
              [_mis(value * 10, "", fb), _mis(value / 10, "", fb)])


def _sf_4(rng: random.Random) -> Draft:
    if rng.random() < 0.5:
        m1, m2 = rng.choice(_MANT), rng.choice(_MANT)
        e1, e2 = rng.randrange(-4, 9), rng.randrange(-4, 9)
        prod, s = m1 * m2, e1 + e2
        value = prod * Fraction(10) ** s
        ans = std_answer(value)
        sol = (f"{fmt_num(m1)} × {fmt_num(m2)} = {fmt_num(prod)} and 10^{e1} × 10^{e2} = 10^{s}, "
               f"so {_std_txt(prod, s)}")
        if prod >= 10:
            sol += f" = {ans.display}"
        ms = [std_mistake(prod * Fraction(10) ** (e1 * e2) if e1 * e2 != s else None, "",
                          "When you multiply powers of 10, add the powers — don't multiply them")]
        if prod >= 10:
            ms.append(std_mistake(value / 100, "", "When the front number is divided by 10, the power of 10 goes up by 1"))
        return _q(f"Work out ({_std_txt(m1, e1)}) × ({_std_txt(m2, e2)}). Give your answer in standard form.",
                  ans, sol, "Multiply the front numbers, then add the powers of 10", ms)

    def pick(r):
        m1, m2 = r.choice(_MANT), r.choice(_MANT)
        q = m1 / m2
        return (m1, m2, q) if m1 != m2 and _terminating(q) and sig_digits(q) <= 3 else None
    m1, m2, q = retry(pick, rng)
    e1, e2 = rng.randrange(3, 10), rng.randrange(-3, 7)
    s = e1 - e2
    value = q * Fraction(10) ** s
    ans = std_answer(value)
    sol = f"{fmt_num(m1)} ÷ {fmt_num(m2)} = {fmt_num(q)} and 10^{e1} ÷ 10^{e2} = 10^{s}, so {_std_txt(q, s)}"
    if q < 1:
        sol += f" = {ans.display}"
    return _q(f"Work out ({_std_txt(m1, e1)}) ÷ ({_std_txt(m2, e2)}). Give your answer in standard form.",
              ans, sol, "Divide the front numbers, then subtract the powers of 10",
              [std_mistake(q * Fraction(10) ** (e1 + e2) if e2 != 0 else None, "",
                           "When you divide powers of 10, subtract the powers — don't add them")])


def _sf_5(rng: random.Random) -> Draft:
    def pick(r):
        neg = r.random() < 0.25
        e1 = r.randrange(-6, -1) if neg else r.randrange(3, 9)
        gap = r.choice((0, 1, 1, 2))
        e2 = e1 - gap
        m1, m2 = Fraction(_mantissa(r, 2), 10), Fraction(_mantissa(r, 2), 10)
        A, B = m1 * Fraction(10) ** e1, m2 * Fraction(10) ** e2
        op = r.choice("+-")
        if op == "-" and A <= B:
            return None
        return m1, e1, m2, e2, A, B, op
    m1, e1, m2, e2, A, B, op = retry(pick, rng)
    R = A + B if op == "+" else A - B
    ans = std_answer(R)
    sym, word = ("+", "add") if op == "+" else ("−", "subtract")
    show = (lambda v: group(v) if is_whole(v) else fmt_num(v))
    ms = []
    if e1 != e2:
        ms.append(std_mistake((m1 + m2 if op == "+" else m1 - m2) * Fraction(10) ** e1, "",
                              f"The powers of 10 are different, so you can't just {word} the front numbers — write both as ordinary numbers first"))
    if op == "+":
        ms.append(std_mistake((m1 + m2) * Fraction(10) ** (e1 + e2), "",
                              "Don't add the powers when adding numbers — write both as ordinary numbers first"))
    return _q(f"Work out ({_std_txt(m1, e1)}) {sym} ({_std_txt(m2, e2)}). Give your answer in standard form.",
              ans, f"As ordinary numbers: {show(A)} {sym} {show(B)} = {show(R)} = {ans.display}",
              f"Write both numbers as ordinary numbers (or with the same power of 10) before you {word}", ms)


# ====================================================== area & perimeter

def _ap_1(rng: random.Random) -> Draft:
    u = rng.choice(LENGTH_UNITS)
    if rng.random() < 0.2:
        s = rng.randrange(3, 21)
        return _q(f"A square has sides of {s} {u}. Work out its perimeter.", _ans(4 * s, u),
                  f"Perimeter = 4 × {s} = {4 * s} {u}", "A square has four equal sides",
                  [_mis(s * s, u + "²", "That's the area — the perimeter is the distance all the way round"),
                   _mis(2 * s, u, "A square has four sides — add all four")])
    L = rng.randrange(4, 21)
    W = rng.randrange(2, L)
    P = 2 * (L + W)
    return _q(f"A rectangle is {L} {u} long and {W} {u} wide. Work out its perimeter.", _ans(P, u),
              f"Perimeter = {L} + {W} + {L} + {W} = {P} {u}",
              "The perimeter is the total distance all the way round the edge",
              [_mis(L * W, u + "²", "That's the area — the perimeter is the distance all the way round"),
               _mis(L + W, u, f"That's only two of the sides — add all four: {L} + {W} + {L} + {W}")])


def _ap_2(rng: random.Random) -> Draft:
    u = rng.choice(LENGTH_UNITS)
    if rng.random() < 0.5:
        L = rng.randrange(3, 21)
        W = rng.randrange(2, L)
        return _q(f"A rectangle is {L} {u} long and {W} {u} wide. Work out its area.", _ans(L * W, u + "²"),
                  f"Area = length × width = {L} × {W} = {L * W} {u}²", "Area of a rectangle = length × width",
                  [_mis(2 * (L + W), u, "That's the perimeter — area = length × width"),
                   _mis(L + W, u, "For area, multiply the length by the width")])
    b, h = rng.randrange(2, 21), rng.randrange(2, 21)
    A = Fraction(b * h, 2)
    return _q(f"A triangle has a base of {b} {u} and a perpendicular height of {h} {u}. Work out its area.",
              _ans(A, u + "²"), f"Area = ½ × base × height = ½ × {b} × {h} = {fmt_num(A)} {u}²",
              "Area of a triangle = ½ × base × perpendicular height",
              [_mis(b * h, u + "²", "Remember to halve: area of a triangle = ½ × base × height")])


def _ap_3(rng: random.Random) -> Draft:
    u = rng.choice(LENGTH_UNITS)
    if rng.random() < 0.5:
        b, h = rng.randrange(4, 21), rng.randrange(3, 16)
        s = h + rng.randrange(1, 6)
        return _q(f"A parallelogram has a base of {b} {u}, slanted sides of {s} {u} and a perpendicular height of {h} {u}. Work out its area.",
                  _ans(b * h, u + "²"), f"Area = base × perpendicular height = {b} × {h} = {b * h} {u}²",
                  "Area of a parallelogram = base × perpendicular height",
                  [_mis(b * s, u + "²", f"Use the perpendicular height ({h} {u}), not the slanted side"),
                   _mis(Fraction(b * h, 2), u + "²", "A parallelogram is not a triangle — don't halve: area = base × height")])
    a = rng.randrange(3, 21)
    b = rng.randrange(3, 21)
    while b == a:
        b = rng.randrange(3, 21)
    h = rng.randrange(2, 13)
    A = Fraction((a + b) * h, 2)
    return _q(f"A trapezium has parallel sides of {a} {u} and {b} {u}. The perpendicular distance between them is {h} {u}. Work out its area.",
              _ans(A, u + "²"), f"Area = ½ × (a + b) × h = ½ × ({a} + {b}) × {h} = {fmt_num(A)} {u}²",
              "Area of a trapezium = ½ × (sum of the parallel sides) × height",
              [_mis((a + b) * h, u + "²", "Remember to halve: area = ½ × (a + b) × h"),
               _mis(Fraction(a * b * h, 2), u + "²", "Add the parallel sides together first: ½ × (a + b) × h")])


def _ap_4(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    W, H = rng.randrange(6, 21), rng.randrange(5, 16)
    a, b = rng.randrange(1, W - 1), rng.randrange(1, H - 1)
    head = (f"A rectangle measures {W} {u} by {H} {u}. A smaller rectangle measuring {a} {u} by {b} {u} "
            f"is cut from one corner, leaving an L-shape. ")
    if rng.random() < 0.6:
        A = W * H - a * b
        return _q(head + "Work out the area of the L-shape.", _ans(A, u + "²"),
                  f"Big rectangle {W} × {H} = {W * H} {u}², small one {a} × {b} = {a * b} {u}², so {W * H} − {a * b} = {A} {u}²",
                  "Find the area of the big rectangle, then take away the part that was cut out",
                  [_mis(W * H + a * b, u + "²", "The small rectangle is cut away, so subtract its area"),
                   _mis(W * H, u + "²", f"Don't forget to take away the {a} by {b} rectangle")])
    P = 2 * (W + H)
    return _q(head + "Work out the perimeter of the L-shape.", _ans(P, u),
              f"The two new inside edges ({a} {u} and {b} {u}) replace the two pieces that were cut off, so the perimeter is the same as the big rectangle's: 2 × ({W} + {H}) = {P} {u}",
              "Work out the length of every edge of the L-shape, then add them all",
              [_mis(P - a - b, u, "Cutting out a corner doesn't change the perimeter here: the two new inside edges are as long as the two missing pieces"),
               _mis(W * H - a * b, u + "²", "That's the area — the perimeter is the distance all the way round")])


def _ap_5(rng: random.Random) -> Draft:
    u = rng.choice(LENGTH_UNITS)
    kind = rng.choice(("rect_area", "tri_area", "rect_perim", "square"))
    if kind == "rect_area":
        W = rng.randrange(2, 16)
        L = rng.randrange(W + 1, 21)
        A = L * W
        return _q(f"A rectangle has an area of {A} {u}² and a length of {L} {u}. Work out its width.", _ans(W, u),
                  f"Area = length × width, so width = {A} ÷ {L} = {W} {u}", "Area = length × width — so divide the area by the length",
                  [_mis(A - L, u, "Area = length × width, so divide the area by the length"),
                   _mis(A * L, u, "Area = length × width, so divide the area by the length (don't multiply)")])
    if kind == "tri_area":
        b, h = rng.randrange(2, 21), rng.randrange(2, 21)
        A = Fraction(b * h, 2)
        return _q(f"A triangle has an area of {fmt_num(A)} {u}² and a base of {b} {u}. Work out its perpendicular height.",
                  _ans(h, u), f"Area = ½ × base × height, so height = 2 × {fmt_num(A)} ÷ {b} = {h} {u}",
                  "Area = ½ × base × height — multiply the area by 2 first",
                  [_mis(A / b, u, "Area = ½ × base × height, so height = 2 × area ÷ base — remember to double")])
    if kind == "rect_perim":
        W = rng.randrange(2, 16)
        L = rng.randrange(W + 1, 21)
        P = 2 * (L + W)
        return _q(f"A rectangle has a perimeter of {P} {u} and a length of {L} {u}. Work out its width.", _ans(W, u),
                  f"The two lengths make {2 * L} {u}, so the two widths make {P} − {2 * L} = {P - 2 * L} {u}. Width = {P - 2 * L} ÷ 2 = {W} {u}",
                  "The perimeter is made of two lengths and two widths",
                  [_mis(P - L, u, "The perimeter includes two lengths and two widths, so subtract both lengths"),
                   _mis(P - 2 * L, u, "That's both widths together — halve it to get one width")])
    s = rng.randrange(3, 16)
    A = s * s
    return _q(f"A square has an area of {A} {u}². Work out the length of one side.", _ans(s, u),
              f"Area = side × side, so side = √{A} = {s} {u}", "Area of a square = side × side",
              [_mis(Fraction(A, 4), u, "Area of a square = side × side, so take the square root (dividing by 4 is for the perimeter)"),
               _mis(Fraction(A, 2), u, "Area of a square = side × side, so take the square root")])


# ================================================================= angles

_POLY_NAMES = {5: "pentagon", 6: "hexagon", 8: "octagon", 9: "nonagon", 10: "decagon", 12: "dodecagon"}


def _ang_1(rng: random.Random) -> Draft:
    a = rng.randrange(15, 166)
    while a == 90:
        a = rng.randrange(15, 166)
    return _q(f"Two angles lie on a straight line. One of them is {a}°. Work out the size of the other angle.",
              _ans(180 - a, "°"), f"Angles on a straight line add up to 180°: 180° − {a}° = {180 - a}°",
              "Angles on a straight line add up to 180 degrees",
              [_mis(360 - a, "°", "Angles on a straight line add up to 180°, not 360°"),
               _mis(90 - a if a < 90 else None, "°", "90° is a right angle — angles on a straight line add up to 180°")])


def _ang_2(rng: random.Random) -> Draft:
    def pick(r):
        a, b = r.randrange(20, 141), r.randrange(15, 141)
        return (a, b) if 180 - a - b >= 10 and a != b else None
    a, b = retry(pick, rng)
    c = 180 - a - b
    return _q(f"Two angles in a triangle are {a}° and {b}°. Work out the size of the third angle.",
              _ans(c, "°"), f"Angles in a triangle add up to 180°: 180° − {a}° − {b}° = {c}°",
              "Angles in a triangle add up to 180 degrees",
              [_mis(360 - a - b, "°", "Angles in a triangle add up to 180°, not 360°"),
               _mis(a + b, "°", "That's the two angles added together — now subtract the total from 180°")])


def _ang_3(rng: random.Random) -> Draft:
    kind = rng.choice(("point", "point", "iso_apex", "iso_base", "vert"))
    if kind == "point":
        def pick(r):
            xs = [r.randrange(30, 151) for _ in range(3)]
            rest = 360 - sum(xs)
            return (xs, rest) if 20 <= rest <= 170 else None
        xs, rest = retry(pick, rng)
        return _q(f"Four angles meet at a point. Three of them are {xs[0]}°, {xs[1]}° and {xs[2]}°. Work out the size of the fourth angle.",
                  _ans(rest, "°"), f"Angles around a point add up to 360°: 360° − {xs[0]}° − {xs[1]}° − {xs[2]}° = {rest}°",
                  "Angles around a point add up to 360 degrees",
                  [_mis(180 - sum(xs) if sum(xs) < 180 else None, "°", "Angles around a point add up to 360°, not 180°"),
                   _mis(sum(xs), "°", "That's the three angles added together — now subtract the total from 360°")])
    if kind == "iso_apex":
        apex = rng.randrange(10, 71) * 2
        base = (180 - apex) // 2
        return _q(f"An isosceles triangle has an angle of {apex}° between its two equal sides. Work out the size of each of the other two angles.",
                  _ans(base, "°"), f"The other two angles are equal: (180° − {apex}°) ÷ 2 = {base}°",
                  "The two base angles of an isosceles triangle are equal, and all three angles add up to 180 degrees",
                  [_mis(180 - apex, "°", f"The other two angles share the {180 - apex}° equally, so halve it")])
    if kind == "iso_base":
        base = rng.randrange(20, 86)
        apex = 180 - 2 * base
        return _q(f"In an isosceles triangle, the two equal angles are each {base}°. Work out the size of the third angle.",
                  _ans(apex, "°"), f"180° − {base}° − {base}° = {apex}°",
                  "There are two equal angles, and all three angles add up to 180 degrees",
                  [_mis(180 - base, "°", f"There are two angles of {base}°, so subtract both from 180°")])
    a = rng.randrange(20, 161)
    while a == 90:
        a = rng.randrange(20, 161)
    return _q(f"Two straight lines cross at a point. One of the four angles formed is {a}°. What is the size of the angle vertically opposite it?",
              _ans(a, "°"), f"Vertically opposite angles are equal, so it is {a}°",
              "Vertically opposite angles are equal",
              [_mis(180 - a, "°", f"Vertically opposite angles are equal — {180 - a}° is the angle next to it"),
               _mis(360 - a, "°", "Vertically opposite angles are equal")])


def _ang_4(rng: random.Random) -> Draft:
    n = rng.choice((5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36))
    ext = 360 // n
    inner = 180 - ext
    shape = f"regular {_POLY_NAMES[n]} ({n} sides)" if n in _POLY_NAMES else f"regular polygon with {n} sides"
    return _q(f"Work out the size of each interior angle of a {shape}.", _ans(inner, "°"),
              f"Exterior angle = 360° ÷ {n} = {ext}°, so interior angle = 180° − {ext}° = {inner}°",
              "Find one exterior angle first: 360 degrees divided by the number of sides",
              [_mis(ext, "°", "That's the exterior angle — the interior angle is 180° minus it"),
               _mis((n - 2) * 180, "°", f"That's the total of all the interior angles — divide it by {n} to get one angle")])


def _ang_5(rng: random.Random) -> Draft:
    kind = rng.choice(("ext", "int", "line", "triangle"))
    if kind in ("ext", "int"):
        n = rng.choice((5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45))
        ext = 360 // n
        if kind == "ext":
            return _q(f"Each exterior angle of a regular polygon is {ext}°. How many sides does the polygon have?",
                      _ans(n, "sides"), f"The exterior angles add up to 360°, so number of sides = 360° ÷ {ext}° = {n}",
                      "The exterior angles of any polygon add up to 360 degrees",
                      [_mis(Fraction(180, ext), "sides", "The exterior angles add up to 360°, not 180° — divide 360° by the exterior angle")])
        inner = 180 - ext
        wrong = Fraction(360, inner)
        return _q(f"Each interior angle of a regular polygon is {inner}°. How many sides does the polygon have?",
                  _ans(n, "sides"), f"Exterior angle = 180° − {inner}° = {ext}°, so number of sides = 360° ÷ {ext}° = {n}",
                  "Work out one exterior angle first (interior + exterior = 180 degrees)",
                  [_mis(wrong, "sides", f"Divide 360° by the exterior angle (180° − {inner}° = {ext}°), not by the interior angle",
                        dp=None if is_whole(wrong) else 1)])
    if kind == "line":
        def pick(r):
            x, a, b = r.randrange(10, 41), r.randrange(1, 6), r.randrange(1, 6)
            c = r.randrange(-10, 31)
            d = 180 - (a + b) * x - c
            if a * x + c < 10 or b * x + d < 10 or c == 0 or d == 0 or abs(d) > 60:
                return None
            return x, a, b, c, d
        x, a, b, c, d = retry(pick, rng)
        e1, e2 = poly([a, c])[0], poly([b, d])[0]
        wrong = Fraction(360 - c - d, a + b)
        return _q(f"Two angles on a straight line are ({e1})° and ({e2})°. Work out the value of x.",
                  _x_answer(Fraction(x)),
                  f"({e1}) + ({e2}) = 180, so {a + b}x {signed(c + d)} = 180, {a + b}x = {180 - c - d}, x = {x}",
                  "Angles on a straight line add up to 180 degrees — add the two expressions and set them equal to that",
                  [_x_mis(wrong, "Angles on a straight line add up to 180°, not 360°")])

    def pick(r):
        x, a, b = r.randrange(10, 41), r.randrange(2, 5), r.randrange(1, 4)
        c = 180 - (1 + a + b) * x
        if c == 0 or abs(c) > 40 or b * x + c < 10:
            return None
        return x, a, b, c
    x, a, b, c = retry(pick, rng)
    e3 = poly([b, c])[0]
    wrong = Fraction(360 - c, 1 + a + b)
    return _q(f"The angles of a triangle are x°, {a}x° and ({e3})°. Work out the value of x.",
              _x_answer(Fraction(x)),
              f"x + {a}x + {e3} = 180, so {1 + a + b}x {signed(c)} = 180, {1 + a + b}x = {180 - c}, x = {x}",
              "The angles in a triangle add up to 180 degrees — add the three expressions and set them equal to that",
              [_x_mis(wrong, "Angles in a triangle add up to 180°, not 360°")])


# ============================================================= Pythagoras

_TRIPLES = ((3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29), (9, 40, 41))


def _py_1(rng: random.Random) -> Draft:
    def pick(r):
        a, b, c = r.choice(_TRIPLES)
        k = r.randrange(1, 6)
        return (a * k, b * k, c * k) if c * k <= 100 else None
    a, b, c = retry(pick, rng)
    if rng.random() < 0.5:
        a, b = b, a
    u = rng.choice(LENGTH_UNITS)
    return _q(f"A right-angled triangle has two shorter sides of {a} {u} and {b} {u}. Work out the length of the hypotenuse.",
              _ans(c, u), f"{a}² + {b}² = {a * a} + {b * b} = {c * c}, so the hypotenuse = √{c * c} = {c} {u}",
              "Square the two shorter sides and add them together",
              [_mis(a + b, u, f"Square the sides first: {a}² + {b}², then square root"),
               _mis(a * a + b * b, u, "Don't forget to take the square root at the end")])


def _py_2(rng: random.Random) -> Draft:
    def pick(r):
        a, b = r.randrange(2, 21), r.randrange(2, 21)
        s = a * a + b * b
        r_ = math.isqrt(s)
        if a == b or r_ * r_ == s or near_half(math.sqrt(s), 1):
            return None
        return a, b, s
    a, b, s = retry(pick, rng)
    u = rng.choice(LENGTH_UNITS)
    v = math.sqrt(s)
    return _q(f"A right-angled triangle has two shorter sides of {a} {u} and {b} {u}. Work out the length of the hypotenuse. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"{a}² + {b}² = {a * a} + {b * b} = {s}, so the hypotenuse = √{s} = {_approx(v)} = {_disp(v, u, 1)} (1 d.p.)",
              "Square the two shorter sides and add them together",
              [_mis(a + b, u, f"Square the sides first: {a}² + {b}², then square root"),
               _root_mis(abs(a * a - b * b), u, "To find the hypotenuse, add the squares — don't subtract")])


def _py_3(rng: random.Random) -> Draft:
    def pick(r):
        if r.random() < 0.4:
            a, b, c = r.choice(_TRIPLES)
            k = r.randrange(1, 5)
            a, b, c = a * k, b * k, c * k
            if r.random() < 0.5:
                a, b = b, a
            return c, a
        c = r.randrange(5, 26)
        a = r.randrange(2, c)
        return (c, a) if _sqrt_ok(c * c - a * a) else None
    c, a = retry(pick, rng)
    u = rng.choice(LENGTH_UNITS)
    d = c * c - a * a
    ans, shown, rounding = _sq_root(d, u)
    return _q(f"A right-angled triangle has a hypotenuse of {c} {u}. One of the other sides is {a} {u}. Work out the length of the third side.{rounding}",
              ans, f"{c}² − {a}² = {c * c} − {a * a} = {d}, so the side = √{d} = {shown}" + (f" = {ans.display} (1 d.p.)" if rounding else f" {u}"),
              "This side is not the hypotenuse, so subtract the squares",
              [_root_mis(c * c + a * a, u, f"You're finding a shorter side, so subtract: {c}² − {a}²"),
               _mis(c - a, u, "Square the sides first, subtract, then square root")])


def _py_4(rng: random.Random) -> Draft:
    def pick(r):
        x1, y1, x2, y2 = (r.randrange(-8, 11) for _ in range(4))
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 or dy == 0 or not _sqrt_ok(dx * dx + dy * dy):
            return None
        if not (min(x1, x2, y1, y2) < 0):
            return None if r.random() < 0.5 else (x1, y1, x2, y2)
        return x1, y1, x2, y2
    x1, y1, x2, y2 = retry(pick, rng)
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    s = dx * dx + dy * dy
    ans, shown, rounding = _sq_root(s, "")
    wdx, wdy = abs(abs(x2) - abs(x1)), abs(abs(y2) - abs(y1))
    sol = (f"Horizontal distance = {dx}, vertical distance = {dy}. {dx}² + {dy}² = {dx * dx} + {dy * dy} = {s}, "
           f"so AB = √{s} = {shown}" + (f" = {ans.display} (1 d.p.)" if rounding else ""))
    return _q(f"Work out the distance between the points A({x1}, {y1}) and B({x2}, {y2}).{rounding}",
              ans, sol, "Find the difference in the x-coordinates and in the y-coordinates, then use Pythagoras",
              [_mis(dx + dy, "", "Square the two differences, add them, then square root"),
               _root_mis(wdx * wdx + wdy * wdy if (wdx, wdy) != (dx, dy) else None, "",
                         "Careful with the negative coordinates — subtracting a negative number means adding")])


def _py_5(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    if rng.random() < 0.5:
        def pick(r):
            b = r.randrange(2, 11) * 2
            s = r.randrange(b // 2 + 1, 21)
            return (b, s) if _sqrt_ok(s * s - (b // 2) ** 2) else None
        b, s = retry(pick, rng)
        hb = b // 2
        d = s * s - hb * hb
        ans, shown, rounding = _sq_root(d, u)
        return _q(f"An isosceles triangle has two equal sides of {s} {u} and a base of {b} {u}. Work out its perpendicular height.{rounding}",
                  ans, f"The height cuts the base in half: {hb} {u}. {s}² − {hb}² = {s * s} − {hb * hb} = {d}, so height = √{d} = {shown}" + (f" = {ans.display} (1 d.p.)" if rounding else f" {u}"),
                  "The perpendicular height cuts the base in half, making two right-angled triangles",
                  [_root_mis(s * s - b * b if s > b else None, u, f"Use half the base ({hb} {u}) — the height meets the base at its midpoint"),
                   _root_mis(s * s + hb * hb, u, "The equal side is the hypotenuse, so subtract the squares")])

    def pick(r):
        a, b, c = r.randrange(2, 16), r.randrange(2, 16), r.randrange(2, 16)
        return (a, b, c) if _sqrt_ok(a * a + b * b + c * c) else None
    a, b, c = retry(pick, rng)
    s = a * a + b * b + c * c
    ans, shown, rounding = _sq_root(s, u)
    return _q(f"A cuboid measures {a} {u} by {b} {u} by {c} {u}. Work out the length of its longest diagonal, from one corner to the opposite corner through the inside of the cuboid.{rounding}",
              ans, f"d² = {a}² + {b}² + {c}² = {a * a} + {b * b} + {c * c} = {s}, so d = √{s} = {shown}" + (f" = {ans.display} (1 d.p.)" if rounding else f" {u}"),
              "Use Pythagoras in 3D: square all three lengths and add them",
              [_root_mis(a * a + b * b, u, "That's the diagonal of one face — the longest diagonal uses all three lengths"),
               _mis(a + b + c, u, "Square each length, add them, then square root")])


# ================================================================ circles

def _dp1_pick(rng: random.Random, make: Callable[[random.Random], tuple]) -> tuple:
    def pick(r):
        out = make(r)
        return None if near_half(out[0], 1) else out
    return retry(pick, rng)


def _ci_1(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, d = _dp1_pick(rng, lambda r: (lambda d: (math.pi * d, d))(r.randrange(2, 31)))
    return _q(f"A circle has a diameter of {d} {u}. Work out its circumference. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"C = π × d = π × {d} = {_approx(v)} = {_disp(v, u, 1)} (1 d.p.)",
              "Circumference = π × diameter",
              [_mis(math.pi * d / 2, u, f"You used the radius — C = π × diameter, so use {d} {u}", dp=1),
               _mis(2 * math.pi * d, u, "C = π × diameter (or 2 × π × radius) — you doubled the diameter", dp=1),
               _mis(math.pi * (d / 2) ** 2, u, "That's the area — circumference = π × diameter", dp=1)])


def _ci_2(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, r_ = _dp1_pick(rng, lambda r: (lambda x: (2 * math.pi * x, x))(r.randrange(2, 26)))
    return _q(f"A circle has a radius of {r_} {u}. Work out its circumference. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"C = 2 × π × r = 2 × π × {r_} = {_approx(v)} = {_disp(v, u, 1)} (1 d.p.)",
              "Circumference = 2 × π × radius (or π × diameter)",
              [_mis(math.pi * r_, u, "C = 2πr — you need to double the radius (or use the diameter)", dp=1),
               _mis(math.pi * r_ * r_, u, "That's the area — circumference = 2πr", dp=1)])


def _ci_3(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, r_ = _dp1_pick(rng, lambda r: (lambda x: (math.pi * x * x, x))(r.randrange(2, 21)))
    return _q(f"A circle has a radius of {r_} {u}. Work out its area. Give your answer to 1 decimal place.",
              _ans(v, u + "²", 1), f"A = π × r² = π × {r_}² = {_approx(v)} = {_disp(v, u + '²', 1)} (1 d.p.)",
              "Area of a circle = π × radius²",
              [_mis(2 * math.pi * r_, u + "²", "That's the circumference — area = πr²", dp=1),
               _mis(math.pi * r_, u + "²", "Square the radius first: A = π × r × r", dp=1),
               _mis((math.pi * r_) ** 2, u + "²", "Only the radius is squared: A = π × r²", dp=1)])


def _ci_4(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, d = _dp1_pick(rng, lambda r: (lambda x: (math.pi * (x / 2) ** 2, x))(r.randrange(4, 31)))
    return _q(f"A circle has a diameter of {d} {u}. Work out its area. Give your answer to 1 decimal place.",
              _ans(v, u + "²", 1), f"r = {d} ÷ 2 = {fmt_num(Fraction(d, 2))} {u}, so A = π × {fmt_num(Fraction(d, 2))}² = {_approx(v)} = {_disp(v, u + '²', 1)} (1 d.p.)",
              "Halve the diameter to get the radius, then use area = π × radius²",
              [_mis(math.pi * d * d, u + "²", "Halve the diameter first to get the radius, then square it", dp=1),
               _mis(math.pi * d, u + "²", "That's the circumference — area = πr²", dp=1)])


def _ci_5(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    if rng.random() < 0.5:
        v, A = _dp1_pick(rng, lambda r: (lambda a: (math.sqrt(a / math.pi), a))(r.randrange(20, 1001)))
        return _q(f"A circle has an area of {A} {u}². Work out its radius. Give your answer to 1 decimal place.",
                  _ans(v, u, 1), f"A = πr², so r² = {A} ÷ π = {_approx(A / math.pi)} and r = √{_approx(A / math.pi)} = {_disp(v, u, 1)} (1 d.p.)",
                  "Rearrange A = πr²: divide the area by π, then square root",
                  [_mis(A / math.pi, u, "Don't forget to square root: r = √(A ÷ π)", dp=1),
                   _mis(A / (2 * math.pi), u, "Area = πr², not 2πr — divide by π and then square root", dp=1)])
    v, d = _dp1_pick(rng, lambda r: (lambda x: (math.pi * x / 2 + x, x))(r.randrange(4, 31)))
    curve = math.pi * d / 2
    return _q(f"A semicircle has a diameter of {d} {u}. Work out its perimeter. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"Curved edge = π × {d} ÷ 2 = {_approx(curve)}. Perimeter = {_approx(curve)} + {d} = {_disp(v, u, 1)} (1 d.p.)",
              "The perimeter is half of the circumference plus the straight edge",
              [_mis(curve, u, f"Don't forget to add the straight edge (the diameter, {d} {u})", dp=1),
               _mis(math.pi * d + d, u, f"Only half of the circle is curved — use π × {d} ÷ 2", dp=1)])


# ======================================================= linear equations

def _le_1(rng: random.Random) -> Draft:
    kind = rng.choice(("add", "sub", "mul", "div"))
    x = rng.randrange(1, 21)
    a = rng.randrange(2, 13)
    if kind == "add":
        b = x + a
        return _q(f"Solve x + {a} = {b}.", _x_answer(Fraction(x)), f"Subtract {a} from both sides: x = {b} − {a} = {x}",
                  f"Do the opposite of adding {a}: subtract {a} from both sides",
                  [_x_mis(Fraction(b + a), f"To undo + {a}, subtract {a} from both sides")])
    if kind == "sub":
        b = x
        x = b + a
        return _q(f"Solve x − {a} = {b}.", _x_answer(Fraction(x)), f"Add {a} to both sides: x = {b} + {a} = {x}",
                  f"Do the opposite of subtracting {a}: add {a} to both sides",
                  [_x_mis(Fraction(b - a), f"To undo − {a}, add {a} to both sides")])
    if kind == "mul":
        x = rng.randrange(1, 13)
        b = a * x
        return _q(f"Solve {a}x = {b}.", _x_answer(Fraction(x)), f"Divide both sides by {a}: x = {b} ÷ {a} = {x}",
                  f"{a}x means {a} × x, so divide both sides by {a}",
                  [_x_mis(Fraction(b - a), f"{a}x means {a} × x, so divide both sides by {a}"),
                   _x_mis(Fraction(b * a), f"{a}x means {a} × x — to undo it, divide by {a}")])
    b = rng.randrange(2, 13)
    x = a * b
    return _q(f"Solve x/{a} = {b}.", _x_answer(Fraction(x)), f"Multiply both sides by {a}: x = {b} × {a} = {x}",
              f"x is divided by {a}, so multiply both sides by {a}",
              [_x_mis(Fraction(b, a), f"x is divided by {a}, so multiply both sides by {a}")])


def _le_2(rng: random.Random) -> Draft:
    a = rng.randrange(2, 10)
    x = rng.randrange(-10, 16)
    b = rng.choice([v for v in range(-20, 21) if v])
    c = a * x + b
    undo = f"subtract {b}" if b > 0 else f"add {-b}"
    return _q(f"Solve {a}x {signed(b)} = {c}.", _x_answer(Fraction(x)),
              f"{_cap(undo)} on both sides: {a}x = {c - b}. Divide by {a}: x = {x}",
              f"First {undo} on both sides",
              [_x_mis(Fraction(c + b, a), f"To undo {signed(b)}, you need to {undo} — check the sign"),
               _x_mis(Fraction(c, a) - b, f"Undo the {signed(b)} first, then divide by {a}")])


def _le_3(rng: random.Random) -> Draft:
    a = rng.randrange(2, 7)
    x = rng.randrange(-6, 13)
    if rng.random() < 0.7:
        b = rng.choice([v for v in range(-9, 10) if v])
        c = a * (x + b)
        return _q(f"Solve {a}(x {signed(b)}) = {c}.", _x_answer(Fraction(x)),
                  f"Expand: {a}x {signed(a * b)} = {c}, so {a}x = {c - a * b} and x = {x}",
                  f"Expand the bracket first (or divide both sides by {a})",
                  [_x_mis(Fraction(c - b, a), f"Multiply both terms in the bracket by {a}: {a}(x {signed(b)}) = {a}x {signed(a * b)}"),
                   _x_mis(Fraction(c, a) + b, f"After dividing by {a} you get x {signed(b)} = {fmt_num(Fraction(c, a))} — undo the {signed(b)} carefully")])
    k = rng.randrange(2, 5)
    b = rng.choice([v for v in range(-9, 10) if v])
    c = a * (k * x + b)
    return _q(f"Solve {a}({k}x {signed(b)}) = {c}.", _x_answer(Fraction(x)),
              f"Expand: {a * k}x {signed(a * b)} = {c}, so {a * k}x = {c - a * b} and x = {x}",
              f"Expand the bracket first: multiply both terms inside by {a}",
              [_x_mis(Fraction(c - b, a * k), f"Multiply both terms in the bracket by {a}: {a}({k}x {signed(b)}) = {a * k}x {signed(a * b)}"),
               _x_mis(Fraction(c - a * b, k), f"After expanding you have {a * k}x, so divide by {a * k}")])


def _le_4(rng: random.Random) -> Draft:
    def pick(r):
        c = r.randrange(1, 8)
        a = r.randrange(c + 1, 11)
        x = r.randrange(-8, 13)
        b = r.choice([v for v in range(-15, 16) if v])
        d = (a - c) * x + b
        return (a, b, c, d, x) if d != 0 else None
    a, b, c, d, x = retry(pick, rng)
    lhs, rhs = poly([a, b])[0], poly([c, d])[0]
    return _q(f"Solve {lhs} = {rhs}.", _x_answer(Fraction(x)),
              f"Subtract {c}x from both sides: {a - c}x {signed(b)} = {d}. Then {a - c}x = {d - b}, so x = {x}",
              f"Get the x terms on one side: subtract {c}x from both sides",
              [_x_mis(Fraction(d + b, a - c), f"When you move {signed(b)} to the other side it becomes {signed(-b)}"),
               _x_mis(Fraction(d - b, a + c), f"Subtract {c}x from both sides — don't add it")])


def _frac_expr(top: str, den: int) -> str:
    return f"({top})/{den}" if " " in top else f"{top}/{den}"


def _le_5(rng: random.Random) -> Draft:
    kind = rng.choice(("simple", "coef", "two", "both"))
    if kind == "simple":
        b = rng.randrange(2, 7)
        c = rng.randrange(-5, 11)
        a = rng.choice([v for v in range(-9, 10) if v])
        x = b * c - a
        top = poly([1, a])[0]
        return _q(f"Solve {_frac_expr(top, b)} = {c}.", _x_answer(Fraction(x)),
                  f"Multiply both sides by {b}: {top} = {b * c}, so x = {x}",
                  f"Multiply both sides by {b} first",
                  [_x_mis(Fraction(b * (c - a)), f"Multiply both sides by {b} first, then deal with the {signed(a)}"),
                   _x_mis(Fraction(b * c + a), f"When you move {signed(a)} across, it becomes {signed(-a)}")])
    if kind == "coef":
        a, cden = rng.randrange(2, 6), rng.randrange(2, 7)
        d = rng.randrange(-5, 11)
        b = rng.choice([v for v in range(-9, 10) if v])
        x = Fraction(cden * d - b, a)
        top = poly([a, b])[0]
        tail = "" if x.denominator == 1 else " Give your answer as a fraction."
        return _q(f"Solve {_frac_expr(top, cden)} = {d}.{tail}", _x_answer(x),
                  f"Multiply both sides by {cden}: {top} = {cden * d}. Then {a}x = {cden * d - b}, so x = {frac_str(x)}",
                  f"Multiply both sides by {cden} first",
                  [_x_mis(Fraction((d - b) * cden, a), f"Multiply both sides by {cden} first: {top} = {cden * d}"),
                   _x_mis(Fraction(cden * d + b, a), f"Undo the {signed(b)} by doing the opposite: {signed(-b)}")])
    if kind == "two":
        def pick(r):
            p, q = r.randrange(2, 7), r.randrange(2, 7)
            return (p, q) if p != q else None
        p, q = retry(pick, rng)
        L = _lcm(p, q)
        t = rng.choice([v for v in range(-3, 7) if v])
        x = L * t
        c = x // p + x // q
        return _q(f"Solve x/{p} + x/{q} = {c}.", _x_answer(Fraction(x)),
                  f"Multiply every term by {L}: {L // p}x + {L // q}x = {c * L}, so {L // p + L // q}x = {c * L} and x = {x}",
                  f"Multiply every term by {L}, the lowest common multiple of {p} and {q}",
                  [_x_mis(Fraction(c * (p + q)), f"You can't add the denominators — multiply every term by {L} first")])

    def pick(r):
        b, d = r.randrange(2, 7), r.randrange(2, 7)
        if b == d:
            return None
        x, t = r.randrange(-6, 10), r.randrange(-3, 6)
        a = b * t - x
        c = d * t - x
        return (a, b, c, d, x) if a != c else None
    a, b, c, d, x = retry(pick, rng)
    lt, rt = poly([1, a])[0], poly([1, c])[0]
    wrong = _safe_div(d * c - b * a, b - d)
    return _q(f"Solve {_frac_expr(lt, b)} = {_frac_expr(rt, d)}.", _x_answer(Fraction(x)),
              f"Cross-multiply: {d}({lt}) = {b}({rt}), so {poly([d, d * a])[0]} = {poly([b, b * c])[0]}. "
              f"Then {d - b}x = {b * c - d * a}, so x = {x}",
              f"Multiply both sides by {b} and by {d} (cross-multiply)",
              [_x_mis(wrong, f"Multiply each side by the OTHER side's denominator: {d}({lt}) = {b}({rt})")])


# ======================================================== expand brackets

def _ex_1(rng: random.Random) -> Draft:
    a, b = rng.sample(range(1, 10), 2)
    co = poly_mul([1, a], [1, b])
    ans = _expr_answer(co)
    return _q(f"Expand and simplify (x + {a})(x + {b}).", ans,
              f"x × x = x², x × {b} = {b}x, {a} × x = {a}x, {a} × {b} = {a * b}. So x² + {a}x + {b}x + {a * b} = {ans.display}",
              "Multiply each term in the first bracket by each term in the second (a grid or FOIL helps)",
              [_expr_mis([1, 0, a * b], f"Don't forget the middle terms: x × {b} and {a} × x"),
               _expr_mis([1, a + b, a + b], f"The last term is {a} × {b}, not {a} + {b}"),
               _expr_mis([1, a * b, a + b], f"Add {a}x and {b}x for the middle term, and multiply {a} × {b} for the last term")])


def _nonzero(rng: random.Random, lo: int, hi: int) -> int:
    return rng.choice([v for v in range(lo, hi + 1) if v])


def _ex_2(rng: random.Random) -> Draft:
    def pick(r):
        a, b = _nonzero(r, -9, 9), _nonzero(r, -9, 9)
        return (a, b) if a != b and (a < 0 or b < 0) else None
    a, b = retry(pick, rng)
    co = poly_mul([1, a], [1, b])
    ans = _expr_answer(co)
    f1, f2 = lin_factor(1, a)[0], lin_factor(1, b)[0]
    return _q(f"Expand and simplify {f1}{f2}.", ans,
              f"x² {signed(b)}x {signed(a)}x {signed(a * b)} = {ans.display}",
              "Multiply each term in the first bracket by each term in the second — watch the signs",
              [_expr_mis([1, -(a + b), a * b], f"Check the middle term: {a}x + {b}x = {a + b}x"),
               _expr_mis([1, a + b, -(a * b)], f"Check the sign of the last term: {a} × {b} = {a * b}"),
               _expr_mis([1, 0, a * b], "Don't forget the two middle terms")])


def _ex_3(rng: random.Random) -> Draft:
    a = rng.randrange(2, 6)
    b, c = _nonzero(rng, -9, 9), _nonzero(rng, -9, 9)
    co = poly_mul([a, b], [1, c])
    ans = _expr_answer(co)
    f1, f2 = lin_factor(a, b)[0], lin_factor(1, c)[0]
    return _q(f"Expand and simplify {f1}{f2}.", ans,
              f"{a}x × x = {a}x², {a}x × {c} = {a * c}x, {b} × x = {b}x, {b} × {c} = {b * c}. So {ans.display}",
              f"Multiply {a}x by both terms in the second bracket, then {b} by both terms",
              [_expr_mis([a, b + c, b * c], f"Multiply {a}x by {c} as well: {a}x × {c} = {a * c}x"),
               _expr_mis([1, a * c + b, b * c], f"{a}x × x = {a}x², not x²"),
               _expr_mis([a, a * c + b, -(b * c)], f"Check the sign of the last term: {b} × {c} = {b * c}")])


def _ex_4(rng: random.Random) -> Draft:
    if rng.random() < 0.5:
        a = rng.choice((1, 1, 2, 3))
        b = _nonzero(rng, -9, 9)
        if a > 1 and math.gcd(a, b) != 1:
            b = 1 if b > 0 else -1
        co = poly_mul([a, b], [a, b])
        ans = _expr_answer(co)
        f = lin_factor(a, b)[0]
        return _q(f"Expand and simplify {f}².", ans,
                  f"{f}² = {f}{f} = {ans.display}",
                  f"{f}² means {f} × {f}",
                  [_expr_mis([a * a, 0, b * b], f"Squaring a bracket means multiplying it by itself: {f}{f} — don't forget the middle term"),
                   _expr_mis([a * a, a * b, b * b], f"There are two middle terms ({a * b}x each), giving {2 * a * b}x"),
                   _expr_mis([a, 2 * a * b, b * b], f"({a}x)² = {a * a}x², not {a}x²") if a > 1 else None])
    a, c = rng.randrange(2, 6), rng.randrange(2, 6)
    b, d = _nonzero(rng, -9, 9), _nonzero(rng, -9, 9)
    co = poly_mul([a, b], [c, d])
    ans = _expr_answer(co)
    f1, f2 = lin_factor(a, b)[0], lin_factor(c, d)[0]
    return _q(f"Expand and simplify {f1}{f2}.", ans,
              f"{a}x × {c}x = {a * c}x², {a}x × {d} = {a * d}x, {b} × {c}x = {b * c}x, {b} × {d} = {b * d}. So {ans.display}",
              "Multiply each term in the first bracket by each term in the second",
              [_expr_mis([a * c, a * d, b * d], f"Remember both middle terms: {a}x × {d} and {b} × {c}x"),
               _expr_mis([a * c, b + d, b * d], f"Multiply across properly: the x terms are {a}x × {d} and {b} × {c}x"),
               _expr_mis([a * c, a * d + b * c, -(b * d)], f"Check the sign of the last term: {b} × {d} = {b * d}")])


def _ex_5(rng: random.Random) -> Draft:
    a, b, c = (_nonzero(rng, -6, 6) for _ in range(3))
    quad = poly_mul([1, a], [1, b])
    co = poly_mul(quad, [1, c])
    ans = _expr_answer(co)
    fs = "".join(lin_factor(1, v)[0] for v in (a, b, c))
    qd = poly(quad)[0]
    return _q(f"Expand and simplify {fs}.", ans,
              f"First {lin_factor(1, a)[0]}{lin_factor(1, b)[0]} = {qd}. Then ({qd}){lin_factor(1, c)[0]} = {ans.display}",
              "Expand two of the brackets first, then multiply the result by the third bracket",
              [_expr_mis([1, quad[1], quad[2] + c], f"Multiply every term of ({qd}) by both x and {c}"),
               _expr_mis(co[:-1] + [-co[-1]], f"Check the sign of the number term: {a} × {b} × {c} = {a * b * c}")])


# ================================================== factorising quadratics

def _fa_1(rng: random.Random) -> Draft:
    p, q = rng.sample(range(1, 10), 2)
    ex = poly([1, p + q, p * q])[0]
    ans = _fact_answer([(1, p), (1, q)])
    pairs = [(i, p * q // i) for i in range(1, p * q + 1) if (p * q) % i == 0 and i + p * q // i != p + q]
    ms = [_fact_mis([(1, -p), (1, -q)], f"Check the signs: the numbers must multiply to {p * q} and add to +{p + q}")]
    if pairs:
        i, j = rng.choice(pairs)
        ms.append(_fact_mis([(1, i), (1, j)], f"{i} and {j} multiply to {p * q}, but they need to add to {p + q} as well"))
    return _q(f"Factorise {ex}.", ans,
              f"Find two numbers that multiply to {p * q} and add to {p + q}: {p} and {q}. So {ans.display}",
              f"Find two numbers that multiply to give {p * q} and add to give {p + q}", ms)


def _fa_2(rng: random.Random) -> Draft:
    def pick(r):
        p, q = _nonzero(r, -9, 9), _nonzero(r, -9, 9)
        return (p, q) if p != q and p + q != 0 and (p < 0 or q < 0) else None
    p, q = retry(pick, rng)
    ex = poly([1, p + q, p * q])[0]
    ans = _fact_answer([(1, p), (1, q)])
    return _q(f"Factorise {ex}.", ans,
              f"Find two numbers that multiply to {p * q} and add to {p + q}: {p} and {q}. So {ans.display}",
              f"Find two numbers that multiply to give {p * q} and add to give {p + q}",
              [_fact_mis([(1, -p), (1, -q)], f"Check the signs: the numbers must multiply to {p * q} and add to {p + q}"),
               _fact_mis([(1, -p), (1, q)], f"Check the signs: the numbers must multiply to {p * q} and add to {p + q}")])


def _fa_3(rng: random.Random) -> Draft:
    if rng.random() < 0.6:
        k, a = 1, rng.randrange(1, 13)
    else:
        def pick(r):
            k, a = r.randrange(2, 6), r.randrange(1, 10)
            return (k, a) if math.gcd(k, a) == 1 else None
        k, a = retry(pick, rng)
    ex = poly([k * k, 0, -a * a])[0]
    ans = _fact_answer([(k, a), (k, -a)])
    kx = "x" if k == 1 else f"{k}x"
    ms = [_fact_mis([(k, -a), (k, -a)], f"{ex} has no middle term, so the signs in the two brackets must be different"),
          _fact_mis([(k, a), (k, a)], f"{ex} has no middle term, so the signs in the two brackets must be different")]
    if k > 1:
        ms.append(_fact_mis([(1, a), (1, -a)], f"{k * k}x² = ({k}x)², so each bracket needs {k}x"))
    return _q(f"Factorise {ex}.", ans,
              f"This is a difference of two squares: ({kx})² − {a}², so {ans.display}",
              "Look for a difference of two squares: a² − b² = (a + b)(a − b)", ms)


def _fa_pick(rng: random.Random, negatives: bool) -> tuple[int, int, int, int]:
    def pick(r):
        m, n = r.choice(((1, 2), (1, 3), (1, 5), (2, 3), (1, 7), (2, 5), (1, 4), (3, 4)))
        if negatives:
            p, q = _nonzero(r, -9, 9), _nonzero(r, -9, 9)
            if p > 0 and q > 0:
                return None
        else:
            p, q = r.randrange(1, 10), r.randrange(1, 10)
        if math.gcd(m, p) != 1 or math.gcd(n, q) != 1 or (m, p) == (n, q):
            return None
        b = m * q + n * p
        if b == 0:
            return None
        if r.random() < 0.5:
            m, p, n, q = n, q, m, p
        return m, p, n, q
    return retry(pick, rng)


def _fa_ax(rng: random.Random, negatives: bool) -> Draft:
    m, p, n, q = _fa_pick(rng, negatives)
    A, B, C = m * n, m * q + n * p, p * q
    ex = poly([A, B, C])[0]
    ans = _fact_answer([(m, p), (n, q)])
    split = f"{A}x² {signed(m * q)}x {signed(n * p)}x {signed(C)}"
    ms: list[Mistake | None] = [
        _fact_mis([(m, -p), (n, -q)], f"Check the signs: expanding should give {signed(B)}x and {signed(C)}"),
        _fact_mis([(m, q), (n, p)], f"Expand your brackets to check — the middle term should be {B}x"),
    ]
    if negatives:
        ms.append(_fact_mis([(m, -p), (n, q)], f"Check the signs: expanding should give {signed(B)}x and {signed(C)}"))
    return _q(f"Factorise {ex}.", ans,
              f"{A} × {C} = {A * C}; two numbers that multiply to {A * C} and add to {B} are {m * q} and {n * p}. "
              f"Split the middle term: {split}, then group to get {ans.display}",
              f"Multiply {A} × {C} = {A * C}, then find two numbers that multiply to {A * C} and add to {B}", ms)


def _fa_4(rng: random.Random) -> Draft:
    return _fa_ax(rng, False)


def _fa_5(rng: random.Random) -> Draft:
    return _fa_ax(rng, True)


# ====================================================== solving quadratics

def _sq_1(rng: random.Random) -> Draft:
    r_ = rng.randrange(2, 13)
    k = r_ * r_
    v = rng.random()
    if v < 0.5:
        eq = f"x² = {k}"
        first = ""
    elif v < 0.75:
        eq = f"x² − {k} = 0"
        first = f"Add {k} to both sides: x² = {k}. "
    else:
        a = rng.randrange(2, 6)
        eq = f"{a}x² = {a * k}"
        first = f"Divide both sides by {a}: x² = {k}. "
    ms = [_roots_mis([r_], f"Don't forget the negative solution: (−{r_})² = {k} too")]
    if v < 0.5:
        ms.append(_roots_mis([Fraction(k, 2)], "x² means x × x, not 2 × x — take the square root"))
    return _q(f"Solve {eq}.", _roots_answer([r_, -r_]), f"{first}x = ±√{k}, so x = {r_} or x = −{r_}",
              "Get x² on its own, then take the square root of both sides — there are two answers", ms)


def _sq_2(rng: random.Random) -> Draft:
    if rng.random() < 0.25:
        r_ = _nonzero(rng, -9, 9)
        f = lin_factor(1, -r_)[0]
        return _q(f"Solve x{f} = 0.", _roots_answer([0, r_]),
                  f"Either x = 0 or {f[1:-1]} = 0, so x = 0 or x = {r_}",
                  "If two things multiply to give 0, one of them must be 0",
                  [_roots_mis([r_], "x = 0 is also a solution, because the x outside the bracket can be 0"),
                   _roots_mis([0, -r_], "Set the bracket equal to zero and solve — the sign changes")])

    def pick(r):
        a, b = _nonzero(r, -9, 9), _nonzero(r, -9, 9)
        return (a, b) if a != b and a != -b else None
    r1, r2 = retry(pick, rng)
    f1, f2 = lin_factor(1, -r1)[0], lin_factor(1, -r2)[0]
    return _q(f"Solve {f1}{f2} = 0.", _roots_answer([r1, r2]),
              f"Set each bracket equal to zero: {f1[1:-1]} = 0 gives x = {r1}, and {f2[1:-1]} = 0 gives x = {r2}",
              "If two brackets multiply to give 0, one of the brackets must be 0",
              [_roots_mis([-r1, -r2], "Set each bracket equal to zero and solve — the answer has the opposite sign to the number in the bracket")])


def _sq_monic(rng: random.Random, both_negative: bool) -> Draft:
    def pick(r):
        if both_negative:
            a, b = r.randrange(-9, 0), r.randrange(-9, 0)
        else:
            a, b = _nonzero(r, -9, 9), _nonzero(r, -9, 9)
            if a < 0 and b < 0:
                return None
        return (a, b) if a != b and a + b != 0 else None
    r1, r2 = retry(pick, rng)
    B, C = -(r1 + r2), r1 * r2
    fac = _factors([(1, -r1), (1, -r2)])[0]
    if not both_negative and rng.random() < 0.3:
        lhs = poly([1, B, 0])[0]
        text = f"Solve {lhs} = {-C}."
        sol = f"Rearrange: {poly([1, B, C])[0]} = 0. Factorise: {fac} = 0, so x = {r1} or x = {r2}"
    else:
        text = f"Solve {poly([1, B, C])[0]} = 0."
        sol = f"Factorise: {fac} = 0, so x = {r1} or x = {r2}"
    return _q(text, _roots_answer([r1, r2]), sol,
              f"Get 0 on one side, then factorise: find two numbers that multiply to {C} and add to {B}",
              [_roots_mis([-r1, -r2], "You've found the numbers in the brackets — now set each bracket equal to zero, which changes the signs")])


def _sq_3(rng: random.Random) -> Draft:
    return _sq_monic(rng, True)


def _sq_4(rng: random.Random) -> Draft:
    return _sq_monic(rng, False)


def _sq_5(rng: random.Random) -> Draft:
    def pick(r):
        a, b = _nonzero(r, -9, 9), _nonzero(r, -9, 9)
        return (a, b) if a != b and a + b != 0 else None
    r1, r2 = retry(pick, rng)
    k = rng.randrange(2, 6)
    co = [k, -k * (r1 + r2), k * r1 * r2]
    fac = _factors([(1, -r1), (1, -r2)])[0]
    return _q(f"Solve {poly(co)[0]} = 0.", _roots_answer([r1, r2]),
              f"Divide every term by {k}: {poly([1, -(r1 + r2), r1 * r2])[0]} = 0. Factorise: {fac} = 0, so x = {r1} or x = {r2}",
              f"Every term has a common factor of {k} — divide by it first",
              [_roots_mis([-r1, -r2], "Set each bracket equal to zero and solve — the answer has the opposite sign to the number in the bracket")])


# ================================================ simultaneous equations

def _eq(a: int, b: int, c: int) -> str:
    return f"{terms([(a, 'x'), (b, 'y')])} = {c}"


def _sim_text(e1: str, e2: str) -> str:
    return f"Solve the simultaneous equations\n{e1}\n{e2}"


def _sim_ms(x: int, y: int, check_eq: str) -> list[Mistake | None]:
    out: list[Mistake | None] = []
    if x != y:
        out.append(_assign_mis(y, x, f"Check which value is x and which is y by substituting back into {check_eq}"))
    if y != 0:
        out.append(_assign_mis(x, -y, f"Check the sign of y by substituting your values back into {check_eq}"))
    return out


def _si_1(rng: random.Random) -> Draft:
    y = rng.randrange(1, 15)
    x = rng.randrange(y + 1, 21)
    s, d = x + y, x - y
    e1, e2 = _eq(1, 1, s), _eq(1, -1, d)
    return _q(_sim_text(e1, e2), _assign(x, y),
              f"Add the equations: 2x = {s + d}, so x = {x}. Then {x} + y = {s}, so y = {y}",
              "Add the two equations together — the y terms cancel out", _sim_ms(x, y, e2))


def _si_2(rng: random.Random) -> Draft:
    def pick(r):
        x, y = _nonzero(r, -5, 10), _nonzero(r, -5, 10)
        a, d, b = r.randrange(1, 6), r.randrange(1, 6), r.randrange(1, 6)
        same = r.random() < 0.5
        if same and a == d:
            return None
        return x, y, a, d, b, same
    x, y, a, d, b, same = retry(pick, rng)
    b2 = b if same else -b
    c1, c2 = a * x + b * y, d * x + b2 * y
    e1, e2 = _eq(a, b, c1), _eq(d, b2, c2)
    if same:
        k = a - d
        sol = f"Subtract the second equation from the first: {terms([(k, 'x')])} = {c1 - c2}, so x = {x}. Substitute into the first: {a * x} {signed(b)}y = {c1}, so y = {y}"
        hint = "The y terms are the same, so subtract one equation from the other"
    else:
        k = a + d
        sol = f"Add the equations: {k}x = {c1 + c2}, so x = {x}. Substitute into the first: {a * x} {signed(b)}y = {c1}, so y = {y}"
        hint = "The y terms have opposite signs, so add the two equations"
    return _q(_sim_text(e1, e2), _assign(x, y), sol, hint, _sim_ms(x, y, e1))


def _si_3(rng: random.Random) -> Draft:
    def pick(r):
        x, y = _nonzero(r, -6, 10), _nonzero(r, -6, 10)
        e, k = r.randrange(1, 5), r.randrange(2, 5)
        b = e * k
        a, d = r.randrange(1, 8), r.randrange(1, 6)
        if a == k * d or b > 12:
            return None
        return x, y, a, b, d, e, k
    x, y, a, b, d, e, k = retry(pick, rng)
    c1, c2 = a * x + b * y, d * x + e * y
    e1, e2 = _eq(a, b, c1), _eq(d, e, c2)
    m = _eq(k * d, k * e, k * c2)
    diff = a - k * d
    sol = (f"Multiply the second equation by {k}: {m}. Subtract it from the first: {diff}x = {c1 - k * c2}, "
           f"so x = {x}. Substitute x = {x} into either equation to get y = {y}")
    return _q(_sim_text(e1, e2), _assign(x, y), sol,
              f"Multiply the second equation by {k} so that the y terms match", _sim_ms(x, y, e2))


def _si_4(rng: random.Random) -> Draft:
    def pick(r):
        x, y = _nonzero(r, -6, 9), _nonzero(r, -6, 9)
        a, d = r.randrange(2, 8), r.randrange(2, 8)
        b, e = r.randrange(2, 8) * r.choice((1, 1, -1)), r.randrange(2, 8) * r.choice((1, 1, -1))
        if abs(b) == abs(e) or abs(b) % abs(e) == 0 or abs(e) % abs(b) == 0:
            return None
        if a * e - b * d == 0 or a == d:
            return None
        return x, y, a, b, d, e
    x, y, a, b, d, e = retry(pick, rng)
    c1, c2 = a * x + b * y, d * x + e * y
    e1, e2 = _eq(a, b, c1), _eq(d, e, c2)
    m1, m2 = abs(e), abs(b)
    n1, n2 = _eq(a * m1, b * m1, c1 * m1), _eq(d * m2, e * m2, c2 * m2)
    if (b * m1 > 0) == (e * m2 > 0):
        k, rhs, how = a * m1 - d * m2, c1 * m1 - c2 * m2, "Subtract"
    else:
        k, rhs, how = a * m1 + d * m2, c1 * m1 + c2 * m2, "Add"
    sol = (f"Multiply the first by {m1} and the second by {m2}: {n1} and {n2}. {how}: {k}x = {rhs}, "
           f"so x = {x}. Substitute to get y = {y}")
    return _q(_sim_text(e1, e2), _assign(x, y), sol,
              f"Multiply the first equation by {m1} and the second by {m2} so the y terms are the same size",
              _sim_ms(x, y, e1))


def _si_5(rng: random.Random) -> Draft:
    def pick(r):
        x, y = r.randrange(-8, 9), r.randrange(-8, 9)
        m, a, b = _nonzero(r, -4, 4), _nonzero(r, -6, 6), _nonzero(r, -6, 6)
        if a + b * m == 0 or (x >= 0 and y >= 0) or x == y:
            return None
        return x, y, m, a, b
    x, y, m, a, b = retry(pick, rng)
    k = y - m * x
    c = a * x + b * y
    line = f"y = {poly([m, k])[0]}"
    e2 = _eq(a, b, c)
    sol = (f"Substitute {line} into {e2}: {terms([(a, 'x')])} {signed(b)}({poly([m, k])[0]}) = {c}, so "
           f"{terms([(a + b * m, 'x')])} {signed(b * k)} = {c}, giving x = {x}. Then y = {m}({x}) {signed(k)} = {y}")
    if k == 0:
        sol = (f"Substitute {line} into {e2}: {terms([(a + b * m, 'x')])} = {c}, giving x = {x}. Then y = {m} × {x} = {y}")
    return _q(_sim_text(line, e2), _assign(x, y), sol,
              f"Substitute the expression for y into the other equation",
              _sim_ms(x, y, e2))


# ================================================================ nth term

def _seq(f: Callable[[int], int], n: int) -> str:
    return ", ".join(str(f(i)) for i in range(1, n + 1)) + ", ..."


def _nt_1(rng: random.Random) -> Draft:
    a = rng.randrange(-5, 21)
    d = _nonzero(rng, -6, 9)
    n = rng.choice((10, 10, 10, 12, 15, 20, 50, 100))
    ans = a + (n - 1) * d
    way = f"goes up by {d}" if d > 0 else f"goes down by {-d}"
    jumps = f"{a} + {n - 1} × {d}" if d > 0 else f"{a} − {n - 1} × {-d}"
    return _q(f"Here is a sequence: {_seq(lambda i: a + (i - 1) * d, 4)} Work out the {n}th term.", _ans(ans),
              f"The sequence {way} each time. The {n}th term = {jumps} = {ans}",
              f"Find the difference between the terms, then count the jumps from the 1st term to the {n}th",
              [_mis(a + n * d, "", f"From the 1st term to the {n}th term there are {n - 1} jumps, not {n}"),
               _mis(n * d, "", f"Start from the first term ({a}) and add {n - 1} jumps of {d}")])


def _nt_2(rng: random.Random) -> Draft:
    d = rng.randrange(2, 10)
    c = rng.randrange(-5, 11)
    a = d + c
    ans = _expr_answer([d, c], var="n", form="any")
    diff_txt = "the same" if c == 0 else (f"{c} more" if c > 0 else f"{-c} less")
    return _q(f"Here are the first five terms of a sequence: {_seq(lambda i: d * i + c, 5)} Find an expression for the nth term.",
              ans, f"The terms go up by {d}, so compare with {d}n: {d}, {2 * d}, {3 * d}, ... "
                   f"Each term is {diff_txt}, so the nth term is {ans.display}",
              "The difference between the terms tells you the number in front of n",
              [_expr_mis([1, d], f"The difference ({d}) goes in front of n: {d}n", var="n"),
               _expr_mis([d, a], f"Check with n = 1: {d} × 1 + {a} = {d + a}, but the first term is {a} — the number on the end comes from the term before the first one", var="n")])


def _nt_3(rng: random.Random) -> Draft:
    k = rng.randrange(2, 10)
    a = rng.randrange(max(1, 3 * k - 25), 31)
    c = a + k
    ans = Answer(kind="expr", display=f"{c} - {k}n", value=f"{c}-{k}*n", var="n")
    return _q(f"Here are the first five terms of a sequence: {_seq(lambda i: c - k * i, 5)} Find an expression for the nth term.",
              ans, f"The terms go down by {k}, so the nth term contains −{k}n. When n = 1, −{k} + {c} = {a}, so the nth term is {ans.display}",
              "The sequence is going down, so the number in front of n is negative",
              [_expr_mis([k, c], f"The sequence is going down, so it's −{k}n, not +{k}n", var="n"),
               _expr_mis([-k, a], f"Check with n = 1: −{k} + {a} = {a - k}, but the first term is {a} — the number on the end is the term before the first one ({c})", var="n")])


def _nt_4(rng: random.Random) -> Draft:
    d = rng.randrange(2, 10)
    c = rng.randrange(-9, 12)
    n = rng.randrange(8, 61)
    V = d * n + c
    form = poly([d, c], "n")[0]
    fb2 = f"Undo the {signed(c)} first, then divide by {d}"
    if rng.random() < 0.5:
        text = f"The nth term of a sequence is {form}. Which term of the sequence is equal to {V}?"
        sol = f"Solve {form} = {V}: {d}n = {V - c}, so n = {n}. It is the {n}th term"
        hint = f"Set {form} equal to {V} and solve for n"
    else:
        text = f"Here is a sequence: {_seq(lambda i: d * i + c, 4)} Which term of the sequence is equal to {V}?"
        sol = f"The nth term is {form}. Solve {form} = {V}: {d}n = {V - c}, so n = {n}. It is the {n}th term"
        hint = f"Find the nth term first, then set it equal to {V} and solve"
    return _q(text, num_answer(n, f"n = {n}"), sol, hint,
              [_x_mis(Fraction(V + c, d), fb2, var="n") if c else None,
               _mis(d * V + c, "", f"Don't put {V} in place of n — set the nth term equal to {V} and solve for n")])


def _nt_5(rng: random.Random) -> Draft:
    a = rng.choice((1, 1, 2, 3))
    b, c = rng.randrange(-5, 6), rng.randrange(-5, 11)
    ans = _expr_answer([a, b, c], var="n", form="any")
    f = (lambda i: a * i * i + b * i + c)
    resid = [f(i) - a * i * i for i in range(1, 4)]
    an2 = "n²" if a == 1 else f"{a}n²"
    lin = poly([b, c], "n")[0]
    return _q(f"Here are the first five terms of a quadratic sequence: {_seq(f, 5)} Find an expression for the nth term.",
              ans, f"The second difference is {2 * a}, so the n² term is {an2}. Subtracting {an2} leaves "
                   f"{', '.join(str(x) for x in resid)}, ..., which is {lin}. So the nth term is {ans.display}",
              "Find the second difference — halve it to get the number in front of n²",
              [_expr_mis([2 * a, b, c], "The number in front of n² is half of the second difference", var="n"),
               _expr_mis([a, b, b + c], "For the linear part, the number on the end is the term before the first one (the zero term), not the first term", var="n")
               if b else None])


# ======================================================= trig: sides

def _trig_pick(rng: random.Random, f: Callable[[random.Random], tuple]) -> tuple:
    def pick(r):
        out = f(r)
        if out is None or near_half(out[0], 1) or out[0] <= 0:
            return None
        return out
    return retry(pick, rng)


def _side(rng: random.Random, lo: int = 4, hi: int = 31) -> Fraction:
    if rng.random() < 0.3:
        return Fraction(rng.randrange(lo * 10, hi * 10), 10)
    return Fraction(rng.randrange(lo, hi))


def _angle(rng: random.Random, lo: int = 15, hi: int = 76) -> int:
    a = rng.randrange(lo, hi)
    return a + 1 if a == 45 else a


def _ts_1(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, h, t = _trig_pick(rng, lambda r: (lambda h, t: (float(h) * sind(t), h, t))(_side(r), _angle(r)))
    hs = fmt_num(h)
    return _q(f"In a right-angled triangle, the hypotenuse is {hs} {u} long and one of the angles is {t}°. Work out the length of the side opposite the {t}° angle. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"sin {t}° = opposite ÷ hypotenuse, so opposite = {hs} × sin {t}° = {_approx(v)} = {_disp(v, u, 1)} (1 d.p.)",
              "Opposite and hypotenuse go together in SOH: sin = opposite ÷ hypotenuse",
              [_mis(float(h) * cosd(t), u, "Opposite and hypotenuse go with sin, not cos (SOH CAH TOA)", dp=1),
               _mis(float(h) * math.sin(t), u, "Check your calculator is in degrees mode (D), not radians", dp=1),
               _mis(float(h) / sind(t), u, "opposite = hypotenuse × sin θ — multiply, don't divide", dp=1)])


def _ts_2(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, h, t = _trig_pick(rng, lambda r: (lambda h, t: (float(h) * cosd(t), h, t))(_side(r), _angle(r)))
    hs = fmt_num(h)
    return _q(f"In a right-angled triangle, the hypotenuse is {hs} {u} long and one of the angles is {t}°. Work out the length of the side adjacent to the {t}° angle (the side next to it that is not the hypotenuse). Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"cos {t}° = adjacent ÷ hypotenuse, so adjacent = {hs} × cos {t}° = {_approx(v)} = {_disp(v, u, 1)} (1 d.p.)",
              "Adjacent and hypotenuse go together in CAH: cos = adjacent ÷ hypotenuse",
              [_mis(float(h) * sind(t), u, "Adjacent and hypotenuse go with cos, not sin (SOH CAH TOA)", dp=1),
               _mis(float(h) * math.cos(t), u, "Check your calculator is in degrees mode (D), not radians", dp=1),
               _mis(float(h) / cosd(t), u, "adjacent = hypotenuse × cos θ — multiply, don't divide", dp=1)])


def _ts_3(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, a, t = _trig_pick(rng, lambda r: (lambda a, t: (float(a) * tand(t), a, t))(_side(r, 3, 21), _angle(r, 15, 71)))
    as_ = fmt_num(a)
    return _q(f"In a right-angled triangle, one of the angles is {t}°. The side adjacent to this angle (not the hypotenuse) is {as_} {u}. Work out the length of the side opposite the {t}° angle. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"tan {t}° = opposite ÷ adjacent, so opposite = {as_} × tan {t}° = {_approx(v)} = {_disp(v, u, 1)} (1 d.p.)",
              "Opposite and adjacent go together in TOA: tan = opposite ÷ adjacent",
              [_mis(float(a) / tand(t), u, "opposite = adjacent × tan θ — multiply, don't divide", dp=1),
               _mis(float(a) * sind(t), u, "Opposite and adjacent go with tan, not sin (SOH CAH TOA)", dp=1),
               _mis(float(a) * math.tan(t), u, "Check your calculator is in degrees mode (D), not radians", dp=1)])


def _ts_4(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    kind = rng.choice(("opp_hyp", "adj_hyp", "opp_adj"))
    fns = {"opp_hyp": (sind, "BC", "AC"), "adj_hyp": (cosd, "AB", "AC"), "opp_adj": (tand, "BC", "AB")}
    fn, given, want = fns[kind]
    v, s, t = _trig_pick(rng, lambda r: (lambda s, t: (float(s) / fn(t), s, t))(_side(r, 3, 21), _angle(r, 20, 71)))
    ss = fmt_num(s)
    name = {sind: "sin", cosd: "cos", tand: "tan"}[fn]
    role = {"BC": "opposite angle A", "AB": "adjacent to angle A"}[given]
    wrole = {"AC": "the hypotenuse", "AB": "adjacent to angle A"}[want]
    alt = {"opp_hyp": (cosd, "BC is opposite angle A, so use sin, not cos"),
           "adj_hyp": (sind, "AB is adjacent to angle A, so use cos, not sin"),
           "opp_adj": (sind, "BC is opposite and AB is adjacent, so use tan")}[kind]
    return _q(f"Triangle ABC has a right angle at B. Angle A = {t}° and {given} = {ss} {u}. Work out the length of {want}. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"{given} is {role} and {want} is {wrole}, so {name} {t}° = {given} ÷ {want}. "
                             f"{want} = {ss} ÷ {name} {t}° = {_approx(v)} = {_disp(v, u, 1)} (1 d.p.)",
              f"{want} is {wrole}. Decide which ratio links {want} with {given}, then rearrange",
              [_mis(float(s) * fn(t), u, f"{want} is on the bottom of the fraction, so divide: {want} = {ss} ÷ {name} {t}°", dp=1),
               _mis(float(s) / alt[0](t), u, alt[1], dp=1)])


def _ts_5(rng: random.Random) -> Draft:
    kind = rng.choice(("tower", "ladder", "kite", "cliff"))
    if kind == "tower":
        v, d, t = _trig_pick(rng, lambda r: (lambda d, t: (d * tand(t), d, t))(r.randrange(10, 81), _angle(r, 20, 66)))
        return _q(f"From a point on level ground {d} m from the foot of a vertical tower, the angle of elevation of the top of the tower is {t}°. Work out the height of the tower. Give your answer to 1 decimal place.",
                  _ans(v, "m", 1), f"The height is opposite the {t}° angle and {d} m is adjacent, so height = {d} × tan {t}° = {_approx(v)} = {_disp(v, 'm', 1)} (1 d.p.)",
                  "Draw a right-angled triangle: the height is opposite the angle and the distance along the ground is adjacent",
                  [_mis(d * sind(t), "m", f"The {d} m is adjacent and the height is opposite, so use tan", dp=1),
                   _mis(d / tand(t), "m", f"height = {d} × tan {t}° — multiply, don't divide", dp=1)])
    if kind in ("ladder", "kite"):
        L_lo, L_hi = (3, 13) if kind == "ladder" else (20, 101)
        v, L, t = _trig_pick(rng, lambda r: (lambda L, t: (L * sind(t), L, t))(r.randrange(L_lo, L_hi), _angle(r, 50 if kind == "ladder" else 25, 81 if kind == "ladder" else 71)))
        if kind == "ladder":
            text = (f"A {L} m ladder leans against a vertical wall. The ladder makes an angle of {t}° with the horizontal ground. "
                    f"How far up the wall does the ladder reach? Give your answer to 1 decimal place.")
        else:
            text = (f"A kite is flying on a straight string {L} m long. The string makes an angle of {t}° with the horizontal. "
                    f"How high is the kite above the hand holding the string? Give your answer to 1 decimal place.")
        return _q(text, _ans(v, "m", 1), f"The {L} m is the hypotenuse and the height is opposite the {t}° angle, so height = {L} × sin {t}° = {_approx(v)} = {_disp(v, 'm', 1)} (1 d.p.)",
                  "The length is the hypotenuse and the height is opposite the angle",
                  [_mis(L * cosd(t), "m", f"The height is opposite the {t}° angle, so use sin, not cos", dp=1),
                   _mis(L * tand(t), "m", f"The {L} m is the hypotenuse, so use sin, not tan", dp=1)])
    v, h, t = _trig_pick(rng, lambda r: (lambda h, t: (h / tand(t), h, t))(r.randrange(20, 121), _angle(r, 15, 61)))
    return _q(f"From the top of a vertical cliff {h} m high, the angle of depression of a boat at sea is {t}°. How far is the boat from the foot of the cliff? Give your answer to 1 decimal place.",
              _ans(v, "m", 1), f"The angle at the boat is also {t}°. The cliff ({h} m) is opposite it and the distance is adjacent, so distance = {h} ÷ tan {t}° = {_approx(v)} = {_disp(v, 'm', 1)} (1 d.p.)",
              "The angle of depression from the cliff top equals the angle of elevation from the boat",
              [_mis(h * tand(t), "m", f"The distance is adjacent to the {t}° angle at the boat, so divide: {h} ÷ tan {t}°", dp=1),
               _mis(h / sind(t), "m", "Opposite and adjacent go with tan, not sin", dp=1)])


# ====================================================== trig: angles

def _deg_ans(v: float) -> Answer:
    return num_answer(v, unit(fmt_dp(v, 1), "°"), dp=1)


def _ang_pick(rng: random.Random, f: Callable[[random.Random], tuple]) -> tuple:
    def pick(r):
        out = f(r)
        if out is None or near_half(out[0], 1):
            return None
        return out
    return retry(pick, rng)


def _ta_1(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, o, a = _ang_pick(rng, lambda r: (lambda o, a: (atand(o / a), o, a) if o != a else None)(r.randrange(2, 21), r.randrange(2, 21)))
    return _q(f"In a right-angled triangle, the side opposite angle x is {o} {u} and the side adjacent to angle x is {a} {u}. Work out the size of angle x. Give your answer to 1 decimal place.",
              _deg_ans(v), f"tan x = {o} ÷ {a}, so x = tan⁻¹({o} ÷ {a}) = {_approx(v)}° = {fmt_dp(v, 1)}° (1 d.p.)",
              "Opposite and adjacent: use tan x = opposite ÷ adjacent, then the inverse (shift tan)",
              [_mis(atand(a / o), "°", "Opposite goes on top: tan x = opposite ÷ adjacent", dp=1),
               _mis(math.atan(o / a), "°", "Your calculator is in radians — switch it to degrees mode (D)", dp=1),
               _mis(Fraction(o, a), "", "That's the value of tan x — now use tan⁻¹ to find the angle", dp=2)])


def _ta_2(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, o, h = _ang_pick(rng, lambda r: (lambda o, h: (asind(o / h), o, h) if o < h else None)(r.randrange(2, 20), r.randrange(3, 26)))
    return _q(f"In a right-angled triangle, the hypotenuse is {h} {u} and the side opposite angle x is {o} {u}. Work out the size of angle x. Give your answer to 1 decimal place.",
              _deg_ans(v), f"sin x = {o} ÷ {h}, so x = sin⁻¹({o} ÷ {h}) = {_approx(v)}° = {fmt_dp(v, 1)}° (1 d.p.)",
              "Opposite and hypotenuse: use sin x = opposite ÷ hypotenuse, then the inverse (shift sin)",
              [_mis(acosd(o / h), "°", "Opposite and hypotenuse go with sin: x = sin⁻¹(opposite ÷ hypotenuse)", dp=1),
               _mis(math.asin(o / h), "°", "Your calculator is in radians — switch it to degrees mode (D)", dp=1),
               _mis(atand(o / h), "°", "The longest side is the hypotenuse, so use sin, not tan", dp=1)])


def _ta_3(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, a, h = _ang_pick(rng, lambda r: (lambda a, h: (acosd(a / h), a, h) if a < h else None)(r.randrange(2, 20), r.randrange(3, 26)))
    return _q(f"In a right-angled triangle, the hypotenuse is {h} {u} and the side adjacent to angle x is {a} {u}. Work out the size of angle x. Give your answer to 1 decimal place.",
              _deg_ans(v), f"cos x = {a} ÷ {h}, so x = cos⁻¹({a} ÷ {h}) = {_approx(v)}° = {fmt_dp(v, 1)}° (1 d.p.)",
              "Adjacent and hypotenuse: use cos x = adjacent ÷ hypotenuse, then the inverse (shift cos)",
              [_mis(asind(a / h), "°", "Adjacent and hypotenuse go with cos: x = cos⁻¹(adjacent ÷ hypotenuse)", dp=1),
               _mis(math.acos(a / h), "°", "Your calculator is in radians — switch it to degrees mode (D)", dp=1)])


def _ta_4(rng: random.Random) -> Draft:
    kind = rng.choice(("ladder", "ramp", "kite"))
    if kind == "ladder":
        v, L, d = _ang_pick(rng, lambda r: (lambda L, d: (acosd(float(d) / L), L, d) if d < L * Fraction(3, 5) else None)(
            r.randrange(3, 11), Fraction(r.randrange(5, 50), 10)))
        ds = fmt_num(d)
        return _q(f"A {L} m ladder leans against a vertical wall. The foot of the ladder is {ds} m from the wall, on level ground. Work out the angle between the ladder and the ground. Give your answer to 1 decimal place.",
                  _deg_ans(v), f"The ladder is the hypotenuse and the {ds} m is adjacent to the angle, so cos x = {ds} ÷ {L} and x = cos⁻¹({ds} ÷ {L}) = {fmt_dp(v, 1)}° (1 d.p.)",
                  "The ladder is the hypotenuse; the distance along the ground is adjacent to the angle you want",
                  [_mis(asind(float(d) / L), "°", "That's the angle between the ladder and the wall — the ground is adjacent to the angle you want, so use cos", dp=1),
                   _mis(atand(float(d) / L), "°", "The ladder is the hypotenuse, so use cos, not tan", dp=1)])
    if kind == "ramp":
        v, h, d = _ang_pick(rng, lambda r: (lambda h, d: (atand(float(h) / d), h, d))(Fraction(r.randrange(2, 30), 10), r.randrange(3, 16)))
        hs = fmt_num(h)
        return _q(f"A ramp rises {hs} m over a horizontal distance of {d} m. Work out the angle the ramp makes with the horizontal. Give your answer to 1 decimal place.",
                  _deg_ans(v), f"The rise is opposite the angle and the horizontal distance is adjacent, so tan x = {hs} ÷ {d} and x = tan⁻¹({hs} ÷ {d}) = {fmt_dp(v, 1)}° (1 d.p.)",
                  "The rise is opposite the angle and the horizontal distance is adjacent",
                  [_mis(atand(d / float(h)), "°", f"Opposite (the rise) goes on top: tan x = {hs} ÷ {d}", dp=1),
                   _mis(asind(float(h) / d), "°", "The horizontal distance is adjacent, not the hypotenuse — use tan", dp=1)])
    v, L, h = _ang_pick(rng, lambda r: (lambda L, h: (asind(h / L), L, h) if h < L else None)(r.randrange(20, 101), r.randrange(10, 80)))
    return _q(f"A kite is flying on a straight string {L} m long. The kite is {h} m higher than the hand holding the string. Work out the angle the string makes with the horizontal. Give your answer to 1 decimal place.",
              _deg_ans(v), f"The string is the hypotenuse and the height is opposite the angle, so sin x = {h} ÷ {L} and x = sin⁻¹({h} ÷ {L}) = {fmt_dp(v, 1)}° (1 d.p.)",
              "The string is the hypotenuse; the height is opposite the angle",
              [_mis(acosd(h / L), "°", "The height is opposite the angle, so use sin, not cos", dp=1),
               _mis(atand(h / L), "°", "The string is the hypotenuse, so use sin, not tan", dp=1)])


def _ta_5(rng: random.Random) -> Draft:
    kind = rng.choice(("base", "apex", "rect"))
    u = rng.choice(("cm", "m"))
    if kind in ("base", "apex"):
        def mk(r):
            b = r.randrange(4, 25)
            s = r.randrange(b // 2 + 2, 26)
            half = Fraction(b, 2)
            if kind == "base":
                return acosd(float(half) / s), b, s
            return 2 * asind(float(half) / s), b, s
        v, b, s = _ang_pick(rng, mk)
        hb = fmt_num(Fraction(b, 2))
        head = f"An isosceles triangle has two equal sides of {s} {u} and a base of {b} {u}. "
        hint = "Split the isosceles triangle down the middle into two right-angled triangles"
        if kind == "base":
            return _q(head + "Work out the size of one of its base angles. Give your answer to 1 decimal place.",
                      _deg_ans(v), f"Split it into two right-angled triangles: half the base = {hb} {u}. cos x = {hb} ÷ {s}, so x = cos⁻¹({hb} ÷ {s}) = {fmt_dp(v, 1)}° (1 d.p.)",
                      hint, [_mis(acosd(b / s) if b < s else None, "°", f"Use half the base ({hb} {u}) in the right-angled triangle", dp=1),
                             _mis(asind(float(Fraction(b, 2)) / s), "°", "Half the base is adjacent to the base angle, so use cos", dp=1)])
        half_angle = asind(float(Fraction(b, 2)) / s)
        return _q(head + "Work out the size of the angle between the two equal sides. Give your answer to 1 decimal place.",
                  _deg_ans(v), f"Split it into two right-angled triangles: half the base = {hb} {u}. Half the angle = sin⁻¹({hb} ÷ {s}) = {_approx(half_angle)}°, so the angle = 2 × {_approx(half_angle)}° = {fmt_dp(v, 1)}° (1 d.p.)",
                  hint, [_mis(half_angle, "°", "That's half of the angle at the top — double it", dp=1)])

    def mk(r):
        L, W = r.randrange(4, 21), r.randrange(2, 20)
        if W >= L:
            return None
        return 2 * atand(W / L), L, W
    v, L, W = _ang_pick(rng, mk)
    half = atand(W / L)
    return _q(f"A rectangle is {L} {u} long and {W} {u} wide. Its two diagonals are drawn. Work out the acute angle between the two diagonals. Give your answer to 1 decimal place.",
              _deg_ans(v), f"Angle between a diagonal and the long side = tan⁻¹({W} ÷ {L}) = {_approx(half)}°. The diagonals cut each other in half, so the acute angle between them is 2 × {_approx(half)}° = {fmt_dp(v, 1)}° (1 d.p.)",
              "First find the angle between a diagonal and the longer side",
              [_mis(half, "°", "That's the angle between a diagonal and the side — the angle between the diagonals is double it", dp=1),
               _mis(180 - v, "°", "That's the obtuse angle between the diagonals — the question asks for the acute one", dp=1)])


# =============================================================== sine rule

def _sr_1(rng: random.Random) -> Draft:
    def mk(r):
        A, B = r.randrange(25, 111), r.randrange(25, 111)
        if A + B > 160 or abs(A - B) < 5:
            return None
        a = _side(r, 5, 21)
        return float(a) * sind(B) / sind(A), A, B, a
    v, A, B, a = _trig_pick(rng, mk)
    as_ = fmt_num(a)
    return _q(f"In triangle ABC, angle A = {A}°, angle B = {B}° and BC = {as_} cm. Work out the length of AC. Give your answer to 1 decimal place.",
              _ans(v, "cm", 1), f"AC ÷ sin {B}° = BC ÷ sin {A}°, so AC = {as_} × sin {B}° ÷ sin {A}° = {_approx(v)} = {fmt_dp(v, 1)} cm (1 d.p.)",
              "Pair each side with the angle opposite it: BC is opposite angle A, and AC is opposite angle B",
              [_mis(float(a) * sind(A) / sind(B), "cm", "Each side goes with the angle opposite it — AC is opposite angle B, so AC = BC × sin B ÷ sin A", dp=1),
               _mis(float(a) * sind(B), "cm", f"Use the whole sine rule: divide by sin {A}° as well", dp=1)])


def _sr_2(rng: random.Random) -> Draft:
    def mk(r):
        A, B = r.randrange(25, 101), r.randrange(25, 101)
        C = 180 - A - B
        if C < 20 or len({A, B, C}) < 3:
            return None
        c = _side(r, 5, 21)
        return float(c) * sind(A) / sind(C), A, B, C, c
    v, A, B, C, c = _trig_pick(rng, mk)
    cs = fmt_num(c)
    return _q(f"In triangle ABC, angle A = {A}°, angle B = {B}° and AB = {cs} cm. Work out the length of BC. Give your answer to 1 decimal place.",
              _ans(v, "cm", 1), f"Angle C = 180° − {A}° − {B}° = {C}°. BC ÷ sin {A}° = AB ÷ sin {C}°, so BC = {cs} × sin {A}° ÷ sin {C}° = {_approx(v)} = {fmt_dp(v, 1)} cm (1 d.p.)",
              "AB is opposite angle C, so work out angle C first",
              [_mis(float(c) * sind(A) / sind(B), "cm", f"AB is opposite angle C, so first find C = 180° − {A}° − {B}°", dp=1),
               _mis(float(c) * sind(B) / sind(C), "cm", f"BC is opposite angle A, so use sin {A}° on the top", dp=1)])


def _sr_3(rng: random.Random) -> Draft:
    def mk(r):
        A, B = r.randrange(35, 81), r.randrange(20, 76)
        if A + B > 160 or abs(A - B) < 5:
            return None
        a = r.randrange(6, 21)
        b = Fraction(fmt_dp(a * sind(B) / sind(A), 1))
        s = float(b) * sind(A) / a
        if not 0 < s < 0.98:
            return None
        return asind(s), A, a, b, s
    v, A, a, b, s = _ang_pick(rng, mk)
    bs = fmt_num(b)
    alt = a * sind(A) / float(b)
    return _q(f"In triangle ABC, BC = {a} cm, AC = {bs} cm and angle A = {A}°. Angle B is acute. Work out the size of angle B. Give your answer to 1 decimal place.",
              _deg_ans(v), f"sin B ÷ {bs} = sin {A}° ÷ {a}, so sin B = {bs} × sin {A}° ÷ {a} = {_approx(s)} and B = sin⁻¹({_approx(s)}) = {fmt_dp(v, 1)}° (1 d.p.)",
              "Use the sine rule with the angles on top: sin B ÷ AC = sin A ÷ BC",
              [_mis(asind(alt) if alt < 1 else None, "°", "Pair each side with the angle opposite it: BC is opposite A and AC is opposite B", dp=1)])


def _sr_4(rng: random.Random) -> Draft:
    def mk(r):
        P, Q = r.randrange(30, 81), r.randrange(30, 81)
        S = 180 - P - Q
        if S < 25 or P == Q:
            return None
        d = r.randrange(5, 31)
        return d * sind(Q) / sind(S), P, Q, S, d
    v, P, Q, S, d = _trig_pick(rng, mk)
    if rng.random() < 0.5:
        text = (f"Two coastguard stations, P and Q, are {d} km apart. A ship S is positioned so that angle SPQ = {P}° and "
                f"angle SQP = {Q}°. Work out the distance PS. Give your answer to 1 decimal place.")
        u = "km"
    else:
        text = (f"Two people, P and Q, stand {d} m apart on level ground and look at a hot-air balloon S. Angle SPQ = {P}° "
                f"and angle SQP = {Q}°. Work out the distance PS. Give your answer to 1 decimal place.")
        u = "m"
    return _q(text, _ans(v, u, 1),
              f"Angle PSQ = 180° − {P}° − {Q}° = {S}°. PS is opposite angle Q and PQ is opposite angle S, so PS = {d} × sin {Q}° ÷ sin {S}° = {_approx(v)} = {fmt_dp(v, 1)} {u} (1 d.p.)",
              "Find the third angle of triangle PQS first, then use the sine rule",
              [_mis(d * sind(Q) / sind(P), u, f"PQ is opposite the angle at S, so use S = 180° − {P}° − {Q}° = {S}°", dp=1),
               _mis(d * sind(P) / sind(S), u, f"PS is opposite the angle at Q, so use sin {Q}°, not sin {P}°", dp=1)])


def _sr_5(rng: random.Random) -> Draft:
    def mk(r):
        A, C = r.randrange(20, 126), r.randrange(20, 126)
        B = 180 - A - C
        if B < 15 or len({A, B, C}) < 3:
            return None
        a = Fraction(r.randrange(40, 200), 10)
        return float(a) * sind(B) / sind(A), A, B, C, a
    v, A, B, C, a = _trig_pick(rng, mk)
    as_ = fmt_num(a)
    return _q(f"In triangle ABC, angle A = {A}°, angle C = {C}° and BC = {as_} cm. Work out the length of AC. Give your answer to 1 decimal place.",
              _ans(v, "cm", 1), f"Angle B = 180° − {A}° − {C}° = {B}°. AC ÷ sin {B}° = BC ÷ sin {A}°, so AC = {as_} × sin {B}° ÷ sin {A}° = {_approx(v)} = {fmt_dp(v, 1)} cm (1 d.p.)",
              "AC is opposite angle B, so work out angle B first",
              [_mis(float(a) * sind(C) / sind(A), "cm", f"AC is opposite angle B — work out B = 180° − {A}° − {C}° first", dp=1),
               _mis(float(a) * sind(A) / sind(B), "cm", "Pair each side with the angle opposite it: AC ÷ sin B = BC ÷ sin A", dp=1)])


# ========================================================= ½ab sin C area

def _tas_1(rng: random.Random) -> Draft:
    v, a, b, C = _trig_pick(rng, lambda r: (lambda a, b, C: (0.5 * a * b * sind(C), a, b, C))(r.randrange(4, 16), r.randrange(4, 16), r.randrange(20, 151)))
    return _q(f"Triangle ABC has AB = {a} cm, AC = {b} cm and angle A = {C}°. Work out the area of the triangle. Give your answer to 1 decimal place.",
              _ans(v, "cm²", 1), f"Area = ½ × {a} × {b} × sin {C}° = {_approx(v)} = {fmt_dp(v, 1)} cm² (1 d.p.)",
              "Area = ½ × a × b × sin C, where C is the angle between sides a and b",
              [_mis(a * b * sind(C), "cm²", "Remember the ½: area = ½ab sin C", dp=1),
               _mis(0.5 * a * b, "cm²", f"Multiply by sin {C}° as well: area = ½ab sin C", dp=1)])


def _tas_2(rng: random.Random) -> Draft:
    def mk(r):
        a, b = Fraction(r.randrange(25, 150), 10), Fraction(r.randrange(25, 150), 10)
        C = r.randrange(20, 161)
        return 0.5 * float(a) * float(b) * sind(C), a, b, C
    v, a, b, C = _trig_pick(rng, mk)
    as_, bs = fmt_num(a), fmt_num(b)
    return _q(f"Triangle PQR has PQ = {as_} cm, PR = {bs} cm and angle QPR = {C}°. Work out the area of the triangle. Give your answer to 1 decimal place.",
              _ans(v, "cm²", 1), f"Area = ½ × {as_} × {bs} × sin {C}° = {_approx(v)} = {fmt_dp(v, 1)} cm² (1 d.p.)",
              "Area = ½ × a × b × sin C, using the two sides either side of the angle",
              [_mis(float(a) * float(b) * sind(C), "cm²", "Remember the ½: area = ½ab sin C", dp=1),
               _mis(0.5 * float(a) * float(b), "cm²", f"Multiply by sin {C}° as well: area = ½ab sin C", dp=1)])


def _tas_3(rng: random.Random) -> Draft:
    def mk(r):
        a, C = r.randrange(5, 16), r.randrange(25, 151)
        b_true = r.randrange(4, 16)
        area_exact = 0.5 * a * b_true * sind(C)
        if near_half(area_exact, 1):
            return None
        area = Fraction(fmt_dp(area_exact, 1))
        return 2 * float(area) / (a * sind(C)), a, C, area
    v, a, C, area = _trig_pick(rng, mk)
    ar = fmt_num(area)
    return _q(f"Triangle PQR has an area of {ar} cm². PQ = {a} cm and angle QPR = {C}°. Work out the length of PR. Give your answer to 1 decimal place.",
              _ans(v, "cm", 1), f"{ar} = ½ × {a} × PR × sin {C}°, so PR = 2 × {ar} ÷ ({a} × sin {C}°) = {_approx(v)} = {fmt_dp(v, 1)} cm (1 d.p.)",
              "Put the numbers into area = ½ab sin C and rearrange to find the missing side",
              [_mis(float(area) / (a * sind(C)), "cm", "Don't forget the ½ in the formula: PR = 2 × area ÷ (PQ × sin P)", dp=1),
               _mis(2 * float(area) / a, "cm", f"Divide by sin {C}° as well", dp=1)])


def _tas_4(rng: random.Random) -> Draft:
    def mk(r):
        a, b = r.randrange(5, 16), r.randrange(5, 16)
        area = r.randrange(5, int(0.5 * a * b * 0.95) + 1)
        s = 2 * area / (a * b)
        if not 0.15 < s < 0.97:
            return None
        return asind(s), a, b, area, s
    v, a, b, area, s = _ang_pick(rng, mk)
    return _q(f"Triangle ABC has an area of {area} cm². AB = {a} cm, AC = {b} cm and angle A is acute. Work out the size of angle A. Give your answer to 1 decimal place.",
              _deg_ans(v), f"{area} = ½ × {a} × {b} × sin A, so sin A = 2 × {area} ÷ ({a} × {b}) = {_approx(s)} and A = sin⁻¹({_approx(s)}) = {fmt_dp(v, 1)}° (1 d.p.)",
              "Put the numbers into area = ½ab sin C, rearrange to find sin A, then use sin⁻¹",
              [_mis(asind(area / (a * b)), "°", "Remember the ½: sin A = 2 × area ÷ (AB × AC)", dp=1)])


def _tas_5(rng: random.Random) -> Draft:
    def mk(r):
        a, b = _side(r, 4, 16), _side(r, 3, 13)
        t = r.randrange(25, 156)
        if t == 90:
            return None
        return float(a) * float(b) * sind(t), a, b, t
    v, a, b, t = _trig_pick(rng, mk)
    as_, bs = fmt_num(a), fmt_num(b)
    return _q(f"A parallelogram has sides of {as_} cm and {bs} cm. One of its angles is {t}°. Work out the area of the parallelogram. Give your answer to 1 decimal place.",
              _ans(v, "cm²", 1), f"A diagonal splits it into two identical triangles, so area = 2 × ½ × {as_} × {bs} × sin {t}° = {as_} × {bs} × sin {t}° = {_approx(v)} = {fmt_dp(v, 1)} cm² (1 d.p.)",
              "A diagonal splits a parallelogram into two identical triangles",
              [_mis(0.5 * float(a) * float(b) * sind(t), "cm²", "That's one triangle — a parallelogram is two identical triangles, so don't halve", dp=1),
               _mis(float(a) * float(b), "cm²", f"The sides are not perpendicular, so multiply by sin {t}° as well", dp=1)])


# ========================================================= arcs and sectors

def _arc_1(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    semi = rng.random() < 0.5
    frac_, name = (Fraction(1, 2), "semicircle") if semi else (Fraction(1, 4), "quarter circle")
    v, r_ = _trig_pick(rng, lambda r: (lambda x: (2 * math.pi * x * float(frac_), x))(r.randrange(2, 21)))
    part = "half" if semi else "a quarter"
    return _q(f"A {name} has a radius of {r_} {u}. Work out the length of its curved edge (the arc). Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"The arc is {part} of the circumference: {frac_str(frac_)} × 2 × π × {r_} = {_approx(v)} = {fmt_dp(v, 1)} {u} (1 d.p.)",
              f"The arc is {part} of the full circumference, 2πr",
              [_mis(2 * math.pi * r_, u, f"That's the full circumference — the arc of a {name} is {part} of it", dp=1),
               _mis(math.pi * r_ * r_ * float(frac_), u, "That's the area — arc length uses the circumference, 2πr", dp=1),
               _mis(math.pi * r_ * float(frac_), u, "The circumference is 2πr (or πd), not πr", dp=1)])


def _arc_angle(rng: random.Random) -> int:
    while True:
        t = rng.randrange(4, 69) * 5
        if t not in (90, 180, 270):
            return t


def _arc_2(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, r_, t = _trig_pick(rng, lambda r: (lambda x, t: (t / 360 * 2 * math.pi * x, x, t))(r.randrange(2, 21), _arc_angle(r)))
    return _q(f"A sector of a circle has radius {r_} {u} and angle {t}°. Work out the arc length. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"Arc length = {t}/360 × 2 × π × {r_} = {_approx(v)} = {fmt_dp(v, 1)} {u} (1 d.p.)",
              "Arc length = (angle ÷ 360) × 2πr",
              [_mis(t / 360 * math.pi * r_ * r_, u, "That's the sector area — for arc length use 2πr", dp=1),
               _mis(t / 360 * math.pi * r_, u, "The full circumference is 2πr, so use 2 × π × r", dp=1)])


def _arc_3(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, r_, t = _trig_pick(rng, lambda r: (lambda x, t: (t / 360 * math.pi * x * x, x, t))(r.randrange(2, 21), _arc_angle(r)))
    return _q(f"A sector of a circle has radius {r_} {u} and angle {t}°. Work out the area of the sector. Give your answer to 1 decimal place.",
              _ans(v, u + "²", 1), f"Sector area = {t}/360 × π × {r_}² = {_approx(v)} = {fmt_dp(v, 1)} {u}² (1 d.p.)",
              "Sector area = (angle ÷ 360) × πr²",
              [_mis(t / 360 * 2 * math.pi * r_, u + "²", "That's the arc length — for area use πr²", dp=1),
               _mis(math.pi * r_ * r_, u + "²", f"That's the whole circle — multiply by {t}/360", dp=1)])


def _arc_4(rng: random.Random) -> Draft:
    u = rng.choice(("cm", "m"))
    v, r_, t = _trig_pick(rng, lambda r: (lambda x, t: (t / 360 * 2 * math.pi * x + 2 * x, x, t))(r.randrange(2, 21), _arc_angle(r)))
    arc = t / 360 * 2 * math.pi * r_
    return _q(f"A sector of a circle has radius {r_} {u} and angle {t}°. Work out the perimeter of the sector. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"Arc = {t}/360 × 2 × π × {r_} = {_approx(arc)}. Perimeter = arc + 2 radii = {_approx(arc)} + {2 * r_} = {_approx(v)} = {fmt_dp(v, 1)} {u} (1 d.p.)",
              "The perimeter of a sector is the arc plus the two straight radii",
              [_mis(arc, u, "That's just the arc — add the two straight radii as well", dp=1),
               _mis(arc + r_, u, f"There are two radii, so add 2 × {r_}", dp=1)])


def _arc_5(rng: random.Random) -> Draft:
    kind = rng.choice(("angle_arc", "angle_area", "radius_area"))
    u = rng.choice(("cm", "m"))
    if kind == "angle_arc":
        def mk(r):
            x, t = r.randrange(3, 21), r.randrange(20, 300)
            L = Fraction(fmt_dp(t / 360 * 2 * math.pi * x, 1))
            return float(L) / (2 * math.pi * x) * 360, x, L
        v, x, L = _ang_pick(rng, mk)
        Ls = fmt_num(L)
        return _q(f"A sector of a circle has radius {x} {u} and arc length {Ls} {u}. Work out the angle of the sector. Give your answer to 1 decimal place.",
                  _deg_ans(v), f"{Ls} = θ/360 × 2 × π × {x}, so θ = {Ls} × 360 ÷ (2 × π × {x}) = {_approx(v)} = {fmt_dp(v, 1)}° (1 d.p.)",
                  "Arc length = (θ ÷ 360) × 2πr — put the numbers in and rearrange for θ",
                  [_mis(float(L) / (math.pi * x) * 360, "°", "The circumference is 2πr, not πr", dp=1),
                   _mis(float(L) / (math.pi * x * x) * 360, "°", "That uses the area formula — arc length uses 2πr", dp=1)])
    if kind == "angle_area":
        def mk(r):
            x, t = r.randrange(3, 16), r.randrange(20, 300)
            A = Fraction(fmt_dp(t / 360 * math.pi * x * x, 1))
            return float(A) / (math.pi * x * x) * 360, x, A
        v, x, A = _ang_pick(rng, mk)
        As = fmt_num(A)
        return _q(f"A sector of a circle has radius {x} {u} and area {As} {u}². Work out the angle of the sector. Give your answer to 1 decimal place.",
                  _deg_ans(v), f"{As} = θ/360 × π × {x}², so θ = {As} × 360 ÷ (π × {x * x}) = {_approx(v)} = {fmt_dp(v, 1)}° (1 d.p.)",
                  "Sector area = (θ ÷ 360) × πr² — put the numbers in and rearrange for θ",
                  [_mis(float(A) / (2 * math.pi * x) * 360, "°", "That uses the arc-length formula — sector area uses πr²", dp=1)])

    def mk(r):
        x, t = r.randrange(3, 16), _arc_angle(r)
        A = Fraction(fmt_dp(t / 360 * math.pi * x * x, 1))
        return math.sqrt(float(A) * 360 / (math.pi * t)), t, A
    v, t, A = _trig_pick(rng, mk)
    As = fmt_num(A)
    r2 = float(A) * 360 / (math.pi * t)
    return _q(f"A sector has an angle of {t}° and an area of {As} {u}². Work out the radius of the circle. Give your answer to 1 decimal place.",
              _ans(v, u, 1), f"{As} = {t}/360 × π × r², so r² = {As} × 360 ÷ ({t} × π) = {_approx(r2)} and r = √{_approx(r2)} = {fmt_dp(v, 1)} {u} (1 d.p.)",
              "Sector area = (θ ÷ 360) × πr² — rearrange for r², then square root",
              [_mis(r2, u, "Don't forget to square root at the end", dp=1)])


# ============================================================== registration

def _skill(name: str, title: str, aliases: tuple[str, ...],
           levels: tuple[Callable[[random.Random], Draft], ...],
           fallback: str) -> Skill:
    sid = f"{SUBJECT_ID}.{name}"
    if len(levels) != 5:
        raise ValueError(f"{sid}: needs 5 levels")

    def generate(level: int, seed: int) -> Problem:
        check_level(level)
        rng = random.Random(seed)
        d = levels[level - 1](rng)
        return build(sid, level, seed, fallback_hint=fallback, **d)

    generate.__name__ = f"generate_{name}"
    generate.__qualname__ = generate.__name__
    return Skill(id=sid, subject=SUBJECT_ID, title=title, aliases=aliases, generate=generate)


SKILLS: tuple[Skill, ...] = (
    _skill("percentages", "Percentages",
           ("percentage", "percentages", "percent", "percentage increase", "percentage decrease",
            "percentage change", "reverse percentage", "compound interest", "depreciation"),
           (_pct_1, _pct_2, _pct_3, _pct_4, _pct_5),
           "Write the percentage as a fraction or decimal of the original amount first"),
    _skill("fractions", "Fractions",
           ("fraction", "fractions", "mixed number", "mixed numbers", "simplifying fractions",
            "adding fractions", "dividing fractions", "multiplying fractions"),
           (_fr_1, _fr_2, _fr_3, _fr_4, _fr_5),
           "Write the fractions with a common denominator, or change mixed numbers to improper fractions"),
    _skill("ratio", "Ratio",
           ("ratio", "ratios", "sharing in a ratio", "share in a ratio", "simplifying ratios"),
           (_ratio_1, _ratio_2, _ratio_3, _ratio_4, _ratio_5),
           "Work out how many parts there are and what one part is worth"),
    _skill("hcf_lcm", "HCF and LCM",
           ("hcf", "lcm", "highest common factor", "lowest common multiple", "prime factors",
            "prime factorisation", "common factors", "common multiples"),
           (_hcf_1, _lcm_2, _hcf_3, _hcf_4, _hcf_5),
           "Write each number as a product of prime factors"),
    _skill("standard_form", "Standard form",
           ("standard form", "scientific notation"),
           (_sf_1, _sf_2, _sf_3, _sf_4, _sf_5),
           "Standard form is a number between one and ten multiplied by a power of ten"),
    _skill("area_perimeter", "Area and perimeter",
           ("area", "perimeter", "area and perimeter", "compound shapes", "trapezium", "parallelogram"),
           (_ap_1, _ap_2, _ap_3, _ap_4, _ap_5),
           "Write down the formula for the shape first, then put the numbers in"),
    _skill("angles", "Angles",
           ("angles", "angle facts", "angles in a triangle", "angles on a straight line",
            "interior angles", "exterior angles", "polygons", "polygon angles"),
           (_ang_1, _ang_2, _ang_3, _ang_4, _ang_5),
           "Decide which angle fact to use: a straight line, a triangle, a point or a polygon"),
    _skill("pythagoras", "Pythagoras' theorem",
           ("pythagoras", "pythagoras' theorem", "pythagoras theorem", "pythagorean"),
           (_py_1, _py_2, _py_3, _py_4, _py_5),
           "Decide whether you are finding the hypotenuse (add the squares) or a shorter side (subtract)"),
    _skill("circles", "Circles",
           ("circle", "circles", "circumference", "area of a circle", "semicircle"),
           (_ci_1, _ci_2, _ci_3, _ci_4, _ci_5),
           "Check whether you are given the radius or the diameter, then choose the right formula"),
    _skill("linear_equations", "Linear equations",
           ("linear equations", "solving equations", "linear equation", "equation", "solve equations"),
           (_le_1, _le_2, _le_3, _le_4, _le_5),
           "Do the same thing to both sides, undoing the operations one at a time"),
    _skill("expand_brackets", "Expanding double brackets",
           ("expanding brackets", "expand brackets", "double brackets", "expanding", "expand",
            "expanding double brackets", "triple brackets"),
           (_ex_1, _ex_2, _ex_3, _ex_4, _ex_5),
           "Multiply every term in one bracket by every term in the other, then collect like terms"),
    _skill("factorise_quadratics", "Factorising quadratics",
           ("factorising", "factorise", "factorising quadratics", "factorize", "factorizing",
            "difference of two squares", "factorise quadratics"),
           (_fa_1, _fa_2, _fa_3, _fa_4, _fa_5),
           "Look for two numbers that multiply to the last term and add to the middle coefficient"),
    _skill("solve_quadratics", "Solving quadratics",
           ("solving quadratics", "quadratic equations", "quadratic equation", "quadratics",
            "quadratic", "solve quadratics"),
           (_sq_1, _sq_2, _sq_3, _sq_4, _sq_5),
           "Get zero on one side, factorise, then set each bracket equal to zero"),
    _skill("simultaneous", "Simultaneous equations",
           ("simultaneous equations", "simultaneous", "simultaneous equation"),
           (_si_1, _si_2, _si_3, _si_4, _si_5),
           "Make the coefficients of one letter the same, then add or subtract the equations"),
    _skill("nth_term", "nth term",
           ("nth term", "sequences", "sequence", "quadratic sequence", "arithmetic sequence",
            "linear sequence"),
           (_nt_1, _nt_2, _nt_3, _nt_4, _nt_5),
           "Find the difference between consecutive terms first"),
    _skill("trig_sides", "Trigonometry: missing sides",
           ("sohcahtoa", "trigonometry", "trig", "missing side", "missing sides", "right-angled trigonometry"),
           (_ts_1, _ts_2, _ts_3, _ts_4, _ts_5),
           "Label the sides opposite, adjacent and hypotenuse, then pick sin, cos or tan"),
    _skill("trig_angles", "Trigonometry: missing angles",
           ("missing angle", "inverse trig", "missing angles", "inverse trigonometry"),
           (_ta_1, _ta_2, _ta_3, _ta_4, _ta_5),
           "Label the sides you know, pick sin, cos or tan, then use the inverse function"),
    _skill("sine_rule", "Sine rule",
           ("sine rule", "the sine rule"),
           (_sr_1, _sr_2, _sr_3, _sr_4, _sr_5),
           "Pair each side with the angle opposite it: a ÷ sin A = b ÷ sin B"),
    _skill("triangle_area_sine", "Area of a triangle (½ab sin C)",
           ("ab sin c", "1/2ab sin c", "1/2 ab sin c", "half ab sin c", "area of a triangle using sine"),
           (_tas_1, _tas_2, _tas_3, _tas_4, _tas_5),
           "Use area = ½ab sin C, where C is the angle between the two sides"),
    _skill("arcs_sectors", "Arcs and sectors",
           ("arc length", "sector", "sectors", "arcs", "arc", "sector area", "area of a sector"),
           (_arc_1, _arc_2, _arc_3, _arc_4, _arc_5),
           "A sector is a fraction of the circle: angle ÷ 360"),
)


# ================================================================== topics

def _m(name: str) -> str:
    return f"{SUBJECT_ID}.{name}"


_GCSE_ROWS = (
    (("higher_algebra", "GCSE Higher: algebra & functions",
      ("linear_equations", "expand_brackets", "factorise_quadratics", "solve_quadratics", "simultaneous", "nth_term"),
      (1, 2, 3, 4, 5)),
     ("higher_trig", "GCSE Higher: trig & geometry",
      ("pythagoras", "trig_sides", "trig_angles", "sine_rule", "triangle_area_sine", "arcs_sectors"),
      (1, 2, 3, 4, 5))),
    (("foundation_number", "GCSE Foundation: number",
      ("percentages", "fractions", "ratio", "hcf_lcm", "standard_form"), (1, 2, 3, 3, 4)),
     ("foundation_geometry", "GCSE Foundation: geometry",
      ("area_perimeter", "angles", "pythagoras", "circles", "trig_sides"), (1, 2, 3, 3, 4))),
)

_KS3_LEVEL_MAPS = {7: ((1, 1, 2, 2, 3), (1, 2, 2, 3, 3)),
                   8: ((1, 2, 2, 3, 3), (1, 2, 3, 3, 4)),
                   9: ((1, 2, 3, 3, 4), (2, 2, 3, 4, 4))}


def _gcse_year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"maths.y{y}.{slug}", label=label, skills=tuple(_m(s) for s in skills), level_map=lm)
              for slug, label, skills, lm in row)
        for row in _GCSE_ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def _ks3_year(y: int) -> YearSpec:
    lm, past = _KS3_LEVEL_MAPS[y]
    number = ["fractions", "hcf_lcm"] + (["standard_form"] if y == 9 else [])
    algebra = ["linear_equations", "nth_term"] + (["expand_brackets"] if y == 9 else [])
    geometry = (["angles", "area_perimeter"] + (["circles"] if y >= 8 else [])
                + (["pythagoras"] if y == 9 else []))
    ratio = ["percentages", "ratio"]

    def t(slug: str, label: str, skills: list[str]) -> Topic:
        return Topic(id=f"maths.y{y}.{slug}", label=label, skills=tuple(_m(s) for s in skills), level_map=lm)
    rows = ((t("ks3_number", "KS3: number & fractions", number), t("ks3_algebra", "KS3: algebra", algebra)),
            (t("ks3_geometry", "KS3: geometry", geometry), t("ks3_ratio", "KS3: ratio & percentages", ratio)))
    return YearSpec(rows=rows, past_paper_level_map=past)


def make_subject() -> Subject:
    years = {y: _ks3_year(y) for y in (7, 8, 9)}
    years.update({y: _gcse_year(y) for y in (10, 11)})
    return Subject(id=SUBJECT_ID, title="Maths", order=10, years=years)


def register(reg) -> None:
    """Register Maths and its skills with a tutor.content Registry."""
    reg.register(make_subject(), list(SKILLS))
