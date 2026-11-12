"""Physics (GCSE, Years 10–11): 12 generated skills (docs/ARCHITECTURE.md section 5).

Shared ladder: L1 direct substitution (whole numbers), L2 rearranging, L3 one unit
conversion, L4 rearranging plus a conversion, L5 two-step or standard form (2–3 s.f.).
All arithmetic uses Fractions so answers are exact; g = 9.8 N/kg is stated whenever used.
Exact answers with more than 3 significant figures ask for 3 s.f. instead.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Callable

from ..content.base import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec
from ..content.fmt import (
    build, check_level, fmt_num, fmt_sf, fmt_std, near_half, num_answer, num_mistake,
    retry, sig_digits, std_answer, std_mistake, unit,
)

SUBJECT_ID = "physics"
G = Fraction(49, 5)                      # 9.8 N/kg
G_TXT = "Use g = 9.8 N/kg."

Draft = dict


# ================================================================ helpers

def _q(text: str, answer: Answer, solution: str, hint: str, mistakes=()) -> Draft:
    return {"text": text, "answer": answer, "solution": solution, "hint": hint,
            "mistakes": list(mistakes)}


def F(x) -> Fraction:
    """Exact value from an int, a Fraction or a decimal string such as '2.5'."""
    return x if isinstance(x, Fraction) else Fraction(str(x))


def n(x) -> str:
    """Number for question text / working."""
    return fmt_num(x)


def _terminating(v: Fraction) -> bool:
    d = Fraction(v).denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1


def _is_short(v) -> bool:
    return isinstance(v, (int, Fraction)) and _terminating(Fraction(v)) and sig_digits(Fraction(v)) <= 3


def _final(v, u: str, sf: int = 3) -> tuple[Answer, str, str]:
    """(answer, rounding sentence for the question, value text for the working)."""
    if _is_short(v):
        return num_answer(v, unit(n(v), u)), "", unit(n(v), u)
    shown = unit(fmt_sf(v, sf), u)
    return (num_answer(v, shown, sf=sf), f" Give your answer to {sf} significant figures.",
            f"{_approx(v)} = {shown} ({sf} s.f.)")


def _rounding_ok(v, sf: int = 3) -> bool:
    return _is_short(v) or not near_half(v, sf=sf)


def _approx(v) -> str:
    x = float(v)
    r = round(x, 3)
    if abs(x - r) < 1e-9:
        return fmt_num(r)
    return f"{math.trunc(x * 1000) / 1000:.3f}…"


def _m(v, u: str, fb: str) -> Mistake | None:
    """A typical wrong value: exact if short, otherwise matched to 2 s.f."""
    if v is None:
        return None
    try:
        if float(v) == 0:
            return None
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return None
    if _is_short(v):
        return num_mistake(v, u, fb)
    return num_mistake(v, u, fb, sf=2)


def _div(a, b) -> Fraction | None:
    return None if b == 0 else F(a) / F(b)


def _choice(rng: random.Random, xs) -> Fraction:
    return F(rng.choice(xs))


def _picked(rng: random.Random, make: Callable[[random.Random], tuple | None], sf: int = 3) -> tuple:
    """Retry ``make`` until its first value (the answer) is safe to round."""
    def f(r):
        out = make(r)
        if out is None or not _rounding_ok(out[0], sf):
            return None
        return out
    return retry(f, rng)


# ================================================================== speed

_MOVERS = (("a cyclist", 3, 12), ("a runner", 2, 8), ("a car", 10, 35), ("a train", 15, 50),
           ("a bird", 5, 20), ("a horse", 4, 15))


def _speed_1(rng):
    who, lo, hi = rng.choice(_MOVERS)
    v, t = rng.randrange(lo, hi + 1), rng.randrange(2, 21)
    d = v * t
    the = "the " + who.split(" ", 1)[1]
    return _q(f"{who.capitalize()} travels {d} m in {t} s. Calculate the average speed of {the} in m/s.",
              num_answer(v, f"{v} m/s"), f"speed = distance ÷ time = {d} ÷ {t} = {v} m/s",
              "speed = distance ÷ time",
              [_m(Fraction(t, d), "m/s", "Speed = distance ÷ time — you divided the time by the distance"),
               _m(d * t, "m/s", "Divide the distance by the time — don't multiply")])


def _speed_2(rng):
    who, lo, hi = rng.choice(_MOVERS)
    v, t = rng.randrange(lo, hi + 1), rng.randrange(5, 61)
    d = v * t
    the = "the " + who.split(" ", 1)[1]
    if rng.random() < 0.5:
        return _q(f"{who.capitalize()} travels at a constant speed of {v} m/s for {t} s. Calculate the distance {the} travels.",
                  num_answer(d, f"{d} m"), f"distance = speed × time = {v} × {t} = {d} m",
                  "distance = speed × time",
                  [_m(Fraction(v, t), "m", "distance = speed × time — multiply, don't divide"),
                   _m(Fraction(t, v), "m", "distance = speed × time — multiply, don't divide")])
    return _q(f"{who.capitalize()} travels {d} m at a constant speed of {v} m/s. Calculate the time taken.",
              num_answer(t, f"{t} s"), f"time = distance ÷ speed = {d} ÷ {v} = {t} s",
              "Rearrange speed = distance ÷ time to make time the subject",
              [_m(d * v, "s", "time = distance ÷ speed — divide, don't multiply"),
               _m(Fraction(v, d), "s", "time = distance ÷ speed — you divided the wrong way round")])


def _speed_3(rng):
    if rng.random() < 0.5:
        v = _choice(rng, ("1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5", "6"))
        mins = rng.randrange(2, 11)
        d = v * 60 * mins
        return _q(f"A runner covers {n(d)} m in {mins} minutes. Calculate the runner's average speed in m/s.",
                  num_answer(v, f"{n(v)} m/s"), f"{mins} minutes = {mins} × 60 = {60 * mins} s. speed = {n(d)} ÷ {60 * mins} = {n(v)} m/s",
                  f"Convert {mins} minutes into seconds first",
                  [_m(d / mins, "m/s", f"Convert {mins} minutes into seconds first: {mins} × 60 = {60 * mins} s")])
    v = _choice(rng, ("0.2", "0.25", "0.3", "0.4", "0.5", "0.6", "0.75", "0.8", "1.2", "1.5"))
    t = rng.randrange(2, 11)
    dcm = v * t * 100
    return _q(f"A toy car travels {n(dcm)} cm in {t} s. Calculate its speed in m/s.",
              num_answer(v, f"{n(v)} m/s"), f"{n(dcm)} cm = {n(dcm / 100)} m. speed = {n(dcm / 100)} ÷ {t} = {n(v)} m/s",
              f"Convert {n(dcm)} cm into metres first",
              [_m(dcm / t, "m/s", f"Convert {n(dcm)} cm into metres first: {n(dcm)} ÷ 100 = {n(dcm / 100)} m")])


def _speed_4(rng):
    if rng.random() < 0.5:
        v, mins = rng.randrange(5, 31), rng.randrange(2, 11)
        d = v * 60 * mins
        return _q(f"A car travels at a constant speed of {v} m/s for {mins} minutes. How far does it travel? Give your answer in metres.",
                  num_answer(d, f"{d} m"), f"{mins} minutes = {60 * mins} s. distance = {v} × {60 * mins} = {d} m",
                  f"Convert {mins} minutes into seconds, then use distance = speed × time",
                  [_m(v * mins, "m", f"Convert {mins} minutes into seconds first: {mins} × 60 = {60 * mins} s"),
                   _m(Fraction(v * 60, mins), "m", "distance = speed × time — multiply, don't divide")])
    v = rng.randrange(10, 41)
    t = rng.randrange(2, 21) * 50
    d = v * t
    dkm = Fraction(d, 1000)
    return _q(f"A train travels {n(dkm)} km at a constant speed of {v} m/s. How long does the journey take, in seconds?",
              num_answer(t, f"{t} s"), f"{n(dkm)} km = {d} m. time = distance ÷ speed = {d} ÷ {v} = {t} s",
              f"Convert {n(dkm)} km into metres, then use time = distance ÷ speed",
              [_m(dkm / v, "s", f"Convert {n(dkm)} km into metres first: × 1000"),
               _m(d * v, "s", "time = distance ÷ speed — divide, don't multiply")])


def _speed_5(rng):
    kind = rng.choice(("average", "average", "signal", "light"))
    if kind == "average":
        def make(r):
            v1, v2 = r.randrange(2, 21), r.randrange(2, 21)
            t1, t2 = r.randrange(10, 121), r.randrange(10, 121)
            if v1 == v2:
                return None
            avg = Fraction(v1 * t1 + v2 * t2, t1 + t2)
            return avg, v1, v2, t1, t2
        avg, v1, v2, t1, t2 = _picked(rng, make)
        d1, d2 = v1 * t1, v2 * t2
        ans, tail, shown = _final(avg, "m/s")
        return _q(f"A cyclist rides {d1} m in {t1} s and then {d2} m in {t2} s. Calculate her average speed for the whole journey.{tail}",
                  ans, f"Total distance = {d1 + d2} m, total time = {t1 + t2} s. Average speed = {d1 + d2} ÷ {t1 + t2} = {shown}",
                  "Average speed = total distance ÷ total time",
                  [_m(Fraction(v1 + v2, 2), "m/s", "Average speed = total distance ÷ total time — don't average the two speeds")])
    c = F("3.0") * 10 ** 8
    if kind == "signal":
        T = _choice(rng, ("1.5", "2.5", "4", "6", "0.02", "0.004", "120", "0.5", "8"))
        d = c * T
        ans = std_answer(d, "m")
        return _q(f"A radio signal travels at 3.0 × 10^8 m/s. Calculate how far it travels in {n(T)} s. Give your answer in standard form.",
                  ans, f"distance = speed × time = 3.0 × 10^8 × {n(T)} = {ans.display}",
                  "distance = speed × time",
                  [std_mistake(c / T, "m", "distance = speed × time — multiply, don't divide")])
    place, dist = rng.choice((("the Moon", F("3.84") * 10 ** 8), ("the Sun", F("1.5") * 10 ** 11),
                              ("Venus (at its closest)", F("4.2") * 10 ** 10), ("Mars (at its closest)", F("5.4") * 10 ** 10)))
    t = dist / c
    ans, tail, shown = _final(t, "s")
    return _q(f"Light travels at 3.0 × 10^8 m/s. {place[0].upper() + place[1:]} is {fmt_std(dist)} m from the Earth. Calculate the time it takes light to travel from {place.split(' (')[0]} to the Earth.{tail}",
              ans, f"time = distance ÷ speed = {fmt_std(dist)} ÷ 3.0 × 10^8 = {shown}",
              "time = distance ÷ speed",
              [_m(dist * c, "s", "time = distance ÷ speed — divide, don't multiply"),
               _m(c / dist, "s", "time = distance ÷ speed — you divided the wrong way round")])


# =========================================================== acceleration

def _acc_1(rng):
    a = _choice(rng, ("1", "1.5", "2", "2.5", "3", "4", "5", "0.5"))
    t = rng.randrange(2, 11)
    u = 0 if rng.random() < 0.4 else rng.randrange(2, 11)
    v = u + a * t
    if u == 0:
        text = f"A sprinter accelerates from rest to {n(v)} m/s in {t} s. Calculate her acceleration."
        sol = f"a = change in velocity ÷ time = {n(v)} ÷ {t} = {n(a)} m/s²"
    else:
        text = f"A car speeds up from {u} m/s to {n(v)} m/s in {t} s. Calculate its acceleration."
        sol = f"a = (v − u) ÷ t = ({n(v)} − {u}) ÷ {t} = {n(v - u)} ÷ {t} = {n(a)} m/s²"
    return _q(text, num_answer(a, f"{n(a)} m/s²"), sol, "acceleration = change in velocity ÷ time",
              [_m(v / t if u else None, "m/s²", f"Use the change in velocity: {n(v)} − {u} = {n(v - u)} m/s"),
               _m(t / (v - u), "m/s²", "acceleration = change in velocity ÷ time — you divided the wrong way round"),
               _m((v - u) * t, "m/s²", "Divide the change in velocity by the time — don't multiply")])


def _acc_2(rng):
    a = _choice(rng, ("0.5", "1", "1.5", "2", "2.5", "3", "4"))
    t = rng.randrange(2, 13)
    u = rng.randrange(1, 15)
    v = u + a * t
    if rng.random() < 0.5:
        return _q(f"A cyclist travelling at {u} m/s accelerates at {n(a)} m/s² for {t} s. Calculate her final velocity.",
                  num_answer(v, f"{n(v)} m/s"), f"change in velocity = a × t = {n(a)} × {t} = {n(a * t)} m/s, so v = {u} + {n(a * t)} = {n(v)} m/s",
                  "Find the change in velocity (a × t), then add it to the starting velocity",
                  [_m(a * t, "m/s", f"That's the change in velocity — add on the starting velocity ({u} m/s)"),
                   _m(u * a * t if u != 1 else None, "m/s", "Add the change in velocity to the starting velocity: v = u + a × t")])
    return _q(f"A car accelerates at {n(a)} m/s² from {u} m/s to {n(v)} m/s. How long does this take?",
              num_answer(t, f"{t} s"), f"t = change in velocity ÷ a = ({n(v)} − {u}) ÷ {n(a)} = {t} s",
              "Rearrange acceleration = change in velocity ÷ time to make time the subject",
              [_m((v - u) * a, "s", "time = change in velocity ÷ acceleration — divide, don't multiply"),
               _m(v / a, "s", f"Use the change in velocity: {n(v)} − {u} = {n(v - u)} m/s")])


def _acc_3(rng):
    def make(r):
        a = _choice(r, ("0.05", "0.1", "0.15", "0.2", "0.25", "0.3", "0.4", "0.5"))
        mins = r.randrange(1, 6)
        dv = a * 60 * mins
        if dv > 40 or dv.denominator != 1:
            return None
        return a, mins, dv
    a, mins, dv = retry(make, rng)
    u = rng.randrange(0, 11)
    v = u + dv
    start = "rest" if u == 0 else f"{u} m/s"
    return _q(f"A train speeds up from {start} to {n(v)} m/s in {mins} minute{'s' if mins > 1 else ''}. Calculate its acceleration in m/s².",
              num_answer(a, f"{n(a)} m/s²"), f"{mins} minute{'s' if mins > 1 else ''} = {60 * mins} s. a = {n(dv)} ÷ {60 * mins} = {n(a)} m/s²",
              "Convert the time into seconds first",
              [_m(dv / mins, "m/s²", f"Convert {mins} minute{'s' if mins > 1 else ''} into seconds first: {mins} × 60 = {60 * mins} s")])


def _acc_4(rng):
    def make(r):
        a = _choice(r, ("0.05", "0.1", "0.2", "0.25", "0.5"))
        mins = _choice(r, ("0.5", "1", "1.5", "2", "3"))
        dv = a * 60 * mins
        if dv > 50 or dv * 2 != int(dv * 2):
            return None
        return a, mins, dv
    a, mins, dv = retry(make, rng)
    u = rng.randrange(2, 15)
    v = u + dv
    secs = 60 * mins
    return _q(f"A train travelling at {u} m/s accelerates at {n(a)} m/s² for {n(mins)} minutes. Calculate its final velocity.",
              num_answer(v, f"{n(v)} m/s"), f"{n(mins)} minutes = {n(secs)} s. Change in velocity = {n(a)} × {n(secs)} = {n(dv)} m/s, so v = {u} + {n(dv)} = {n(v)} m/s",
              "Convert the time into seconds, then use v = u + a × t",
              [_m(u + a * mins, "m/s", f"Convert {n(mins)} minutes into seconds first: × 60"),
               _m(dv, "m/s", f"That's the change in velocity — add on the starting velocity ({u} m/s)")])


def _acc_5(rng):
    if rng.random() < 0.6:
        def make(r):
            u, v, s = r.randrange(0, 21), r.randrange(5, 41), r.randrange(10, 201)
            a = Fraction(v * v - u * u, 2 * s)
            if v <= u or near_half(a, sf=2):
                return None
            return a, u, v, s
        a, u, v, s = _picked(rng, make, sf=2)
        ans = num_answer(a, f"{fmt_sf(a, 2)} m/s²", sf=2)
        start = "rest" if u == 0 else f"{u} m/s"
        return _q(f"A car accelerates from {start} to {v} m/s over a distance of {s} m. Calculate its acceleration. Use v² − u² = 2as. Give your answer to 2 significant figures.",
                  ans, f"a = (v² − u²) ÷ 2s = ({v * v} − {u * u}) ÷ {2 * s} = {_approx(a)} = {ans.display} (2 s.f.)",
                  "Rearrange v² − u² = 2as to make a the subject",
                  [num_mistake(Fraction((v - u) ** 2, 2 * s), "m/s²", "Square each speed first: v² − u², not (v − u)²", sf=2) if u else None,
                   num_mistake(Fraction(v * v - u * u, s), "m/s²", "Divide by 2s, not just s", sf=2)])

    def make(r):
        u, s = r.randrange(8, 36), r.randrange(10, 121)
        a = Fraction(u * u, 2 * s)
        return None if near_half(a, sf=2) else (a, u, s)
    a, u, s = _picked(rng, make, sf=2)
    ans = num_answer(a, f"{fmt_sf(a, 2)} m/s²", sf=2)
    return _q(f"A car travelling at {u} m/s brakes and comes to a stop in a distance of {s} m. Calculate its deceleration. Use v² − u² = 2as. Give your answer to 2 significant figures.",
              ans, f"v = 0, so u² = 2as and a = {u}² ÷ (2 × {s}) = {u * u} ÷ {2 * s} = {_approx(a)} = {ans.display} (2 s.f.)",
              "The final velocity is 0 — put the numbers into v² − u² = 2as",
              [num_mistake(Fraction(u * u, s), "m/s²", "Divide by 2s, not just s", sf=2),
               num_mistake(Fraction(u, 2 * s), "m/s²", "Square the speed: u² = u × u", sf=2)])


# ================================================================== force

def _force_1(rng):
    if rng.random() < 0.5:
        m, a, what = rng.randrange(2, 51), rng.randrange(1, 11), rng.choice(("box", "trolley", "sledge", "crate"))
    else:
        m, a, what = rng.randrange(8, 21) * 100, rng.randrange(1, 5), "car"
    f = m * a
    return _q(f"A {m} kg {what} accelerates at {a} m/s². Calculate the resultant force on the {what}.",
              num_answer(f, f"{f} N"), f"F = m × a = {m} × {a} = {f} N", "Use F = m × a",
              [_m(Fraction(m, a), "N", "F = m × a — multiply the mass by the acceleration"),
               _m(Fraction(a, m), "N", "F = m × a — multiply, don't divide"),
               _m(m + a, "N", "F = m × a — multiply, don't add")])


def _force_2(rng):
    m = rng.choice((rng.randrange(2, 41), rng.randrange(6, 21) * 100))
    a = _choice(rng, ("0.5", "1", "1.5", "2", "2.5", "3", "4", "5"))
    f = m * a
    if rng.random() < 0.5:
        return _q(f"A resultant force of {n(f)} N acts on an object of mass {m} kg. Calculate its acceleration.",
                  num_answer(a, f"{n(a)} m/s²"), f"a = F ÷ m = {n(f)} ÷ {m} = {n(a)} m/s²",
                  "Rearrange F = m × a to make a the subject",
                  [_m(f * m, "m/s²", "a = F ÷ m — divide, don't multiply"),
                   _m(m / f, "m/s²", "a = F ÷ m — you divided the wrong way round")])
    return _q(f"A resultant force of {n(f)} N gives an object an acceleration of {n(a)} m/s². Calculate the mass of the object.",
              num_answer(m, f"{m} kg"), f"m = F ÷ a = {n(f)} ÷ {n(a)} = {m} kg",
              "Rearrange F = m × a to make m the subject",
              [_m(f * a, "kg", "m = F ÷ a — divide, don't multiply"),
               _m(a / f, "kg", "m = F ÷ a — you divided the wrong way round")])


def _force_3(rng):
    mg = rng.randrange(2, 19) * 50
    a = _choice(rng, ("0.5", "1", "1.5", "2", "2.5", "3", "4", "5", "6"))
    f = Fraction(mg, 1000) * a
    return _q(f"A {mg} g trolley accelerates at {n(a)} m/s². Calculate the resultant force on it.",
              num_answer(f, f"{n(f)} N"), f"{mg} g = {n(Fraction(mg, 1000))} kg. F = m × a = {n(Fraction(mg, 1000))} × {n(a)} = {n(f)} N",
              f"Convert {mg} g into kilograms first",
              [_m(mg * a, "N", f"Convert {mg} g into kilograms first: {mg} ÷ 1000 = {n(Fraction(mg, 1000))} kg")])


def _force_4(rng):
    mg = rng.randrange(1, 11) * 50
    a = rng.randrange(2, 21)
    f = Fraction(mg * a, 1000)
    return _q(f"A resultant force of {n(f)} N acts on a {mg} g ball. Calculate the acceleration of the ball.",
              num_answer(a, f"{a} m/s²"), f"{mg} g = {n(Fraction(mg, 1000))} kg. a = F ÷ m = {n(f)} ÷ {n(Fraction(mg, 1000))} = {a} m/s²",
              f"Convert {mg} g into kilograms, then rearrange F = m × a",
              [_m(f / mg, "m/s²", f"Convert {mg} g into kilograms first: {mg} ÷ 1000 = {n(Fraction(mg, 1000))} kg"),
               _m(f * Fraction(mg, 1000), "m/s²", "a = F ÷ m — divide, don't multiply")])


def _force_5(rng):
    if rng.random() < 0.5:
        m = rng.randrange(6, 21) * 100
        a = _choice(rng, ("0.5", "1", "1.5", "2", "2.5", "3"))
        t = rng.randrange(2, 11)
        u = rng.randrange(0, 16)
        v = u + a * t
        f = m * a
        start = "rest" if u == 0 else f"{u} m/s"
        return _q(f"A car of mass {m} kg speeds up from {start} to {n(v)} m/s in {t} s. Calculate the resultant force on the car.",
                  num_answer(f, f"{n(f)} N"), f"a = ({n(v)} − {u}) ÷ {t} = {n(a)} m/s². F = m × a = {m} × {n(a)} = {n(f)} N",
                  "Find the acceleration first, then use F = m × a",
                  [_m(m * v / t if u else None, "N", f"Use the change in velocity ({n(v)} − {u}) to find the acceleration"),
                   _m(m * (v - u), "N", "Divide the change in velocity by the time to get the acceleration first")])

    def make(r):
        m = r.randrange(6, 21) * 100
        drive = r.randrange(10, 61) * 100
        resist = r.randrange(2, drive // 100) * 100
        return Fraction(drive - resist, m), m, drive, resist
    a, m, drive, resist = _picked(rng, make)
    ans, tail, shown = _final(a, "m/s²")
    return _q(f"A car of mass {m} kg has a driving force of {drive} N. The total resistive force on it is {resist} N. Calculate its acceleration.{tail}",
              ans, f"Resultant force = {drive} − {resist} = {drive - resist} N. a = F ÷ m = {drive - resist} ÷ {m} = {shown}",
              "Find the resultant force first: driving force − resistive force",
              [_m(Fraction(drive, m), "m/s²", f"First find the resultant force: {drive} − {resist} = {drive - resist} N"),
               _m(Fraction(drive + resist, m), "m/s²", "The resistive force acts against the driving force, so subtract it")])


# ================================================================= weight

_THINGS = ("bag of potatoes", "suitcase", "dog", "bike", "box of books", "child", "sack of flour")
_PLANETS = (("the Moon", "1.6"), ("Mars", "3.7"), ("Jupiter", "25"))


def _weight_1(rng):
    m = rng.randrange(2, 121)
    w = G * m
    what = rng.choice(_THINGS)
    return _q(f"Calculate the weight of a {m} kg {what}. {G_TXT}",
              num_answer(w, f"{n(w)} N"), f"W = m × g = {m} × 9.8 = {n(w)} N", "Use W = m × g",
              [_m(10 * m, "N", "Use g = 9.8 N/kg, as the question says"),
               _m(Fraction(m) / G, "N", "W = m × g — multiply, don't divide")])


def _weight_2(rng):
    m = rng.randrange(2, 121)
    w = G * m
    return _q(f"An object has a weight of {n(w)} N. Calculate its mass. {G_TXT}",
              num_answer(m, f"{m} kg"), f"m = W ÷ g = {n(w)} ÷ 9.8 = {m} kg",
              "Rearrange W = m × g to make m the subject",
              [_m(w * G, "kg", "m = W ÷ g — divide, don't multiply"),
               _m(w / 10, "kg", "Use g = 9.8 N/kg, as the question says")])


def _weight_3(rng):
    mg = rng.randrange(1, 20) * 50
    w = G * Fraction(mg, 1000)
    what = rng.choice(("apple", "phone", "book", "football", "bag of sugar", "tin of beans"))
    return _q(f"Calculate the weight of a {mg} g {what}. {G_TXT}",
              num_answer(w, f"{n(w)} N"), f"{mg} g = {n(Fraction(mg, 1000))} kg. W = {n(Fraction(mg, 1000))} × 9.8 = {n(w)} N",
              f"Convert {mg} g into kilograms first",
              [_m(G * mg, "N", f"Convert {mg} g into kilograms first: {mg} ÷ 1000 = {n(Fraction(mg, 1000))} kg")])


def _weight_4(rng):
    mg = rng.randrange(1, 20) * 50
    w = G * Fraction(mg, 1000)
    what = rng.choice(("apple", "phone", "book", "football", "bag of sugar", "tin of beans"))
    return _q(f"A {what} has a weight of {n(w)} N. Calculate its mass in grams. {G_TXT}",
              num_answer(mg, f"{mg} g"), f"m = W ÷ g = {n(w)} ÷ 9.8 = {n(Fraction(mg, 1000))} kg = {mg} g",
              "Rearrange W = m × g to find the mass in kg, then convert to grams",
              [_m(Fraction(mg, 1000), "g", "That's the mass in kilograms — multiply by 1000 to get grams"),
               _m(w * G * 1000, "g", "m = W ÷ g — divide, don't multiply")])


def _weight_5(rng):
    if rng.random() < 0.6:
        m = rng.randrange(40, 101)
        place, gp = rng.choice(_PLANETS)
        gp_ = F(gp)
        we, wp = G * m, gp_ * m
        return _q(f"An astronaut has a weight of {n(we)} N on Earth, where g = 9.8 N/kg. Calculate her weight on {place}, where g = {gp} N/kg.",
                  num_answer(wp, f"{n(wp)} N"), f"Mass = {n(we)} ÷ 9.8 = {m} kg. Weight on {place} = {m} × {gp} = {n(wp)} N",
                  "Find her mass first — mass is the same everywhere",
                  [_m(we / gp_, "N", f"Find her mass first: m = {n(we)} ÷ 9.8 = {m} kg, then multiply by {gp}"),
                   _m(we * gp_, "N", f"Find her mass first by dividing by 9.8, then multiply by {gp}")])
    mant = _choice(rng, ("1.2", "1.5", "2.4", "3.6", "4.5", "6.2", "7.5", "8.1"))
    e = rng.randrange(4, 9)
    m = mant * 10 ** e
    w = G * m
    what = "ship" if e >= 6 else "lorry" if e == 4 else "train"
    ans = std_answer(w, "N", round_to_sf=3)
    return _q(f"A {what} has a mass of {fmt_std(m)} kg. Calculate its weight. {G_TXT} Give your answer in standard form to 3 significant figures.",
              ans, f"W = m × g = {fmt_std(m)} × 9.8 = {ans.display} (3 s.f.)", "Use W = m × g",
              [std_mistake(m * 10, "N", "Use g = 9.8 N/kg, as the question says", round_to_sf=3),
               std_mistake(m / G, "N", "W = m × g — multiply, don't divide", round_to_sf=3)])


# ========================================================= kinetic energy

def _ke_1(rng):
    m, v = rng.randrange(1, 81), rng.randrange(1, 31)
    e = Fraction(m * v * v, 2)
    what = rng.choice(("ball", "runner", "dog", "cyclist", "trolley", "go-kart"))
    return _q(f"Calculate the kinetic energy of a {m} kg {what} moving at {v} m/s.",
              num_answer(e, f"{n(e)} J"), f"Ek = ½ × m × v² = ½ × {m} × {v}² = ½ × {m} × {v * v} = {n(e)} J",
              "Use Ek = ½ × m × v²",
              [_m(m * v * v, "J", "Remember the ½: Ek = ½ × m × v²"),
               _m(Fraction(m * v, 2), "J", f"Square the speed: v² = {v} × {v} = {v * v}"),
               _m(Fraction(m * v, 2) ** 2, "J", "Only the speed is squared: Ek = ½ × m × v²")])


def _ke_2(rng):
    m, v = rng.randrange(1, 21), rng.randrange(2, 21)
    e = Fraction(m * v * v, 2)
    if rng.random() < 0.5:
        return _q(f"A {m} kg ball has {n(e)} J of kinetic energy. Calculate its speed.",
                  num_answer(v, f"{v} m/s"), f"v² = 2 × Ek ÷ m = 2 × {n(e)} ÷ {m} = {v * v}, so v = √{v * v} = {v} m/s",
                  "Rearrange Ek = ½mv² to find v², then square root",
                  [_m(v * v, "m/s", "Don't forget the square root: v = √(2 × Ek ÷ m)"),
                   _m(math.sqrt(e / m), "m/s", "Multiply Ek by 2 first: v² = 2 × Ek ÷ m")])
    return _q(f"A ball moving at {v} m/s has {n(e)} J of kinetic energy. Calculate its mass.",
              num_answer(m, f"{m} kg"), f"m = 2 × Ek ÷ v² = 2 × {n(e)} ÷ {v * v} = {m} kg",
              "Rearrange Ek = ½mv² to make m the subject",
              [_m(e / (v * v), "kg", "Remember the ½: m = 2 × Ek ÷ v²"),
               _m(2 * e / v, "kg", f"Square the speed: v² = {v * v}")])


def _ke_3(rng):
    if rng.random() < 0.5:
        mg, v = rng.randrange(1, 19) * 50, rng.randrange(2, 31)
        mk = Fraction(mg, 1000)
        e = mk * v * v / 2
        return _q(f"A {mg} g ball is moving at {v} m/s. Calculate its kinetic energy.",
                  num_answer(e, f"{n(e)} J"), f"{mg} g = {n(mk)} kg. Ek = ½ × {n(mk)} × {v}² = {n(e)} J",
                  f"Convert {mg} g into kilograms first",
                  [_m(Fraction(mg * v * v, 2), "J", f"Convert {mg} g into kilograms first: {mg} ÷ 1000 = {n(mk)} kg")])
    m, v = rng.randrange(8, 21) * 100, rng.randrange(5, 31)
    e = Fraction(m * v * v, 2)
    ekj = e / 1000
    return _q(f"A car of mass {m} kg is moving at {v} m/s. Calculate its kinetic energy in kJ.",
              num_answer(ekj, f"{n(ekj)} kJ"), f"Ek = ½ × {m} × {v}² = {n(e)} J = {n(ekj)} kJ",
              "Work out Ek in joules, then divide by 1000 to get kJ",
              [_m(e, "kJ", "That's the energy in joules — divide by 1000 to get kJ"),
               _m(m * v * v / Fraction(1000), "kJ", "Remember the ½: Ek = ½ × m × v²")])


def _ke_4(rng):
    m, v = rng.choice((800, 1000, 1200, 1500, 2000)), rng.randrange(5, 31)
    e = Fraction(m * v * v, 2)
    ekj = e / 1000
    return _q(f"A car of mass {m} kg has {n(ekj)} kJ of kinetic energy. Calculate its speed.",
              num_answer(v, f"{v} m/s"), f"{n(ekj)} kJ = {n(e)} J. v² = 2 × {n(e)} ÷ {m} = {v * v}, so v = {v} m/s",
              f"Convert {n(ekj)} kJ into joules, then rearrange Ek = ½mv²",
              [_m(math.sqrt(2 * ekj / m), "m/s", f"Convert {n(ekj)} kJ into joules first: × 1000"),
               _m(v * v, "m/s", "Don't forget the square root at the end")])


def _ke_5(rng):
    if rng.random() < 0.5:
        m = rng.randrange(8, 21) * 100
        u, v = rng.randrange(2, 20), rng.randrange(10, 36)
        if v <= u:
            u, v = v - 1 if v > 1 else 1, u + 2
        de = Fraction(m * (v * v - u * u), 2)
        ans, tail, shown = _final(de, "J")
        return _q(f"A car of mass {m} kg speeds up from {u} m/s to {v} m/s. Calculate the increase in its kinetic energy.{tail}",
                  ans, f"Ek before = ½ × {m} × {u}² = {n(Fraction(m * u * u, 2))} J, after = ½ × {m} × {v}² = {n(Fraction(m * v * v, 2))} J. Increase = {shown}",
                  "Work out the kinetic energy at each speed, then subtract",
                  [_m(Fraction(m * (v - u) ** 2, 2), "J", "Work out the kinetic energy at each speed and subtract — don't square the difference in speed"),
                   _m(Fraction(m * v * v, 2), "J", "That's the final kinetic energy — subtract the kinetic energy it had at the start")])
    mant = _choice(rng, ("1.2", "1.5", "2.0", "2.5", "3.5", "4.0", "6.0", "8.0"))
    m = mant * 10 ** 4
    v = rng.randrange(6, 26) * 10
    e = m * v * v / 2
    ans = std_answer(e, "J", round_to_sf=2)
    return _q(f"An aeroplane of mass {fmt_std(m)} kg is flying at {v} m/s. Calculate its kinetic energy. Give your answer in standard form to 2 significant figures.",
              ans, f"Ek = ½ × {fmt_std(m)} × {v}² = {fmt_std(e)} = {ans.display} (2 s.f.)",
              "Use Ek = ½ × m × v²",
              [std_mistake(m * v * v, "J", "Remember the ½: Ek = ½ × m × v²", round_to_sf=2),
               std_mistake(m * v / 2, "J", "Square the speed: v²", round_to_sf=2)])


# ===================================================================== GPE

def _gpe_1(rng):
    m, h = rng.randrange(1, 81), rng.randrange(1, 51)
    e = G * m * h
    return _q(f"A {m} kg box is lifted through a height of {h} m. Calculate the gain in its gravitational potential energy. {G_TXT}",
              num_answer(e, f"{n(e)} J"), f"Ep = m × g × h = {m} × 9.8 × {h} = {n(e)} J", "Use Ep = m × g × h",
              [_m(10 * m * h, "J", "Use g = 9.8 N/kg, as the question says"),
               _m(m * h, "J", "Multiply by g as well: Ep = m × g × h")])


def _gpe_2(rng):
    m, h = rng.randrange(2, 81), rng.randrange(2, 51)
    e = G * m * h
    if rng.random() < 0.5:
        return _q(f"A {m} kg climber gains {n(e)} J of gravitational potential energy. How high does she climb? {G_TXT}",
                  num_answer(h, f"{h} m"), f"h = Ep ÷ (m × g) = {n(e)} ÷ ({m} × 9.8) = {h} m",
                  "Rearrange Ep = m × g × h to make h the subject",
                  [_m(e / m, "m", "Divide by g as well: h = Ep ÷ (m × g)"),
                   _m(e / (10 * m), "m", "Use g = 9.8 N/kg, as the question says")])
    return _q(f"An object gains {n(e)} J of gravitational potential energy when it is lifted {h} m. Calculate its mass. {G_TXT}",
              num_answer(m, f"{m} kg"), f"m = Ep ÷ (g × h) = {n(e)} ÷ (9.8 × {h}) = {m} kg",
              "Rearrange Ep = m × g × h to make m the subject",
              [_m(e / h, "kg", "Divide by g as well: m = Ep ÷ (g × h)"),
               _m(e / (10 * h), "kg", "Use g = 9.8 N/kg, as the question says")])


def _gpe_3(rng):
    if rng.random() < 0.5:
        mg, h = rng.randrange(1, 19) * 50, rng.randrange(1, 11)
        mk = Fraction(mg, 1000)
        e = mk * G * h
        return _q(f"A {mg} g ball is lifted through a height of {h} m. Calculate the gain in its gravitational potential energy. {G_TXT}",
                  num_answer(e, f"{n(e)} J"), f"{mg} g = {n(mk)} kg. Ep = {n(mk)} × 9.8 × {h} = {n(e)} J",
                  f"Convert {mg} g into kilograms first",
                  [_m(mg * G * h, "J", f"Convert {mg} g into kilograms first: {mg} ÷ 1000 = {n(mk)} kg")])
    m, hcm = rng.randrange(1, 21), rng.randrange(1, 20) * 10
    hm = Fraction(hcm, 100)
    e = G * m * hm
    return _q(f"A {m} kg bag is lifted onto a shelf {hcm} cm higher. Calculate the gain in its gravitational potential energy. {G_TXT}",
              num_answer(e, f"{n(e)} J"), f"{hcm} cm = {n(hm)} m. Ep = {m} × 9.8 × {n(hm)} = {n(e)} J",
              f"Convert {hcm} cm into metres first",
              [_m(G * m * hcm, "J", f"Convert {hcm} cm into metres first: {hcm} ÷ 100 = {n(hm)} m")])


def _gpe_4(rng):
    m, h = rng.randrange(2, 21) * 5, rng.randrange(2, 31)
    e = G * m * h
    ekj = e / 1000
    return _q(f"A {m} kg crate gains {n(ekj)} kJ of gravitational potential energy when it is lifted. How high is it lifted? {G_TXT}",
              num_answer(h, f"{h} m"), f"{n(ekj)} kJ = {n(e)} J. h = {n(e)} ÷ ({m} × 9.8) = {h} m",
              f"Convert {n(ekj)} kJ into joules, then rearrange Ep = m × g × h",
              [_m(ekj / (G * m), "m", f"Convert {n(ekj)} kJ into joules first: × 1000"),
               _m(e / m, "m", "Divide by g as well: h = Ep ÷ (m × g)")])


def _gpe_5(rng):
    if rng.random() < 0.6:
        def make(r):
            h = r.randrange(2, 46)
            return math.sqrt(2 * 9.8 * h), h
        v, h = _picked(rng, make)
        mass = _choice(rng, ("0.2", "0.5", "1.5", "2"))
        ans = num_answer(v, f"{fmt_sf(v, 3)} m/s", sf=3)
        return _q(f"A {n(mass)} kg ball is dropped from a height of {h} m. Assume all of its gravitational potential energy is transferred to kinetic energy. Calculate its speed just before it hits the ground. {G_TXT} Give your answer to 3 significant figures.",
                  ans, f"mgh = ½mv², so v² = 2gh = 2 × 9.8 × {h} = {n(2 * G * h)} and v = √{n(2 * G * h)} = {_approx(v)} = {ans.display} (3 s.f.)",
                  "Set mgh equal to ½mv² — the mass cancels",
                  [num_mistake(2 * G * h, "m/s", "Don't forget the square root at the end", sf=2),
                   num_mistake(math.sqrt(9.8 * h), "m/s", "Ek = ½mv² and Ep = mgh, so v² = 2gh", sf=3),
                   num_mistake(math.sqrt(20 * h), "m/s", "Use g = 9.8 N/kg, as the question says", sf=3)])
    m = rng.randrange(6, 21) * 100
    h = rng.randrange(10, 81)
    e = G * m * h
    ans = std_answer(e, "J", round_to_sf=3)
    return _q(f"A lift of mass {m} kg is raised through a height of {h} m. Calculate the gain in its gravitational potential energy. {G_TXT} Give your answer in standard form to 3 significant figures.",
              ans, f"Ep = m × g × h = {m} × 9.8 × {h} = {n(e)} J = {ans.display} (3 s.f.)", "Use Ep = m × g × h",
              [std_mistake(10 * m * h, "J", "Use g = 9.8 N/kg, as the question says", round_to_sf=3),
               std_mistake(m * h, "J", "Multiply by g as well: Ep = m × g × h", round_to_sf=3)])


# ================================================================== power

def _power_1(rng):
    p, t = rng.randrange(5, 201), rng.randrange(2, 61)
    e = p * t
    return _q(f"A motor transfers {e} J of energy in {t} s. Calculate its power.",
              num_answer(p, f"{p} W"), f"P = E ÷ t = {e} ÷ {t} = {p} W", "power = energy transferred ÷ time",
              [_m(e * t, "W", "Power = energy ÷ time — divide, don't multiply"),
               _m(Fraction(t, e), "W", "Power = energy ÷ time — you divided the wrong way round")])


def _power_2(rng):
    if rng.random() < 0.5:
        p, t = rng.choice((40, 60, 100, 500, 800, 1200, 2000)), rng.randrange(10, 301)
        e = p * t
        return _q(f"A {p} W lamp is switched on for {t} s. How much energy does it transfer?",
                  num_answer(e, f"{e} J"), f"E = P × t = {p} × {t} = {e} J",
                  "Rearrange power = energy ÷ time to make energy the subject",
                  [_m(Fraction(p, t), "J", "energy = power × time — multiply, don't divide"),
                   _m(Fraction(t, p), "J", "energy = power × time — multiply, don't divide")])
    p, t = rng.choice((500, 1000, 1200, 1500, 2000, 2500, 3000)), rng.randrange(5, 121)
    e = p * t
    return _q(f"How long does it take a {p} W kettle to transfer {e} J of energy?",
              num_answer(t, f"{t} s"), f"t = E ÷ P = {e} ÷ {p} = {t} s",
              "Rearrange power = energy ÷ time to make time the subject",
              [_m(e * p, "s", "time = energy ÷ power — divide, don't multiply"),
               _m(Fraction(p, e), "s", "time = energy ÷ power — you divided the wrong way round")])


def _power_3(rng):
    if rng.random() < 0.5:
        p, t = rng.randrange(10, 31) * 100, rng.randrange(3, 25) * 10
        e = p * t
        ekj = Fraction(e, 1000)
        return _q(f"A kettle transfers {n(ekj)} kJ of energy in {t} s. Calculate its power in watts.",
                  num_answer(p, f"{p} W"), f"{n(ekj)} kJ = {e} J. P = {e} ÷ {t} = {p} W",
                  f"Convert {n(ekj)} kJ into joules first",
                  [_m(ekj / t, "W", f"Convert {n(ekj)} kJ into joules first: × 1000")])
    p, mins = rng.randrange(5, 101), rng.randrange(2, 11)
    e = p * 60 * mins
    return _q(f"A motor transfers {e} J of energy in {mins} minutes. Calculate its power.",
              num_answer(p, f"{p} W"), f"{mins} minutes = {60 * mins} s. P = {e} ÷ {60 * mins} = {p} W",
              f"Convert {mins} minutes into seconds first",
              [_m(Fraction(e, mins), "W", f"Convert {mins} minutes into seconds first: {mins} × 60 = {60 * mins} s")])


def _power_4(rng):
    if rng.random() < 0.5:
        p, mins = rng.choice((500, 1000, 1500, 2000, 2500, 3000)), rng.randrange(2, 16)
        e = p * 60 * mins
        return _q(f"A {p} W heater is switched on for {mins} minutes. How much energy does it transfer, in joules?",
                  num_answer(e, f"{e} J"), f"{mins} minutes = {60 * mins} s. E = P × t = {p} × {60 * mins} = {e} J",
                  f"Convert {mins} minutes into seconds, then use energy = power × time",
                  [_m(p * mins, "J", f"Convert {mins} minutes into seconds first: {mins} × 60 = {60 * mins} s")])
    p, t = rng.choice((1000, 1500, 2000, 2500, 3000)), rng.randrange(3, 31) * 10
    e = p * t
    ekj = Fraction(e, 1000)
    return _q(f"How many seconds does it take a {p} W kettle to transfer {n(ekj)} kJ of energy?",
              num_answer(t, f"{t} s"), f"{n(ekj)} kJ = {e} J. t = E ÷ P = {e} ÷ {p} = {t} s",
              f"Convert {n(ekj)} kJ into joules, then rearrange power = energy ÷ time",
              [_m(ekj / p, "s", f"Convert {n(ekj)} kJ into joules first: × 1000"),
               _m(e * p, "s", "time = energy ÷ power — divide, don't multiply")])


def _power_5(rng):
    if rng.random() < 0.6:
        def make(r):
            m, h, t = r.randrange(2, 21) * 5, r.randrange(2, 31), r.randrange(4, 61)
            return G * m * h / t, m, h, t
        p, m, h, t = _picked(rng, make)
        ans, tail, shown = _final(p, "W")
        e = G * m * h
        return _q(f"A motor lifts a {m} kg load through a height of {h} m in {t} s. Calculate the useful power output of the motor. {G_TXT}{tail}",
                  ans, f"Energy transferred = m × g × h = {m} × 9.8 × {h} = {n(e)} J. P = {n(e)} ÷ {t} = {shown}",
                  "Work out the energy transferred (m × g × h) first, then divide by the time",
                  [_m(Fraction(m * h, t), "W", "The energy transferred is m × g × h — include g = 9.8 N/kg"),
                   _m(e, "W", "That's the energy — divide it by the time to get the power")])
    pw = _choice(rng, ("1.2", "1.5", "1.8", "2.4", "3.6"))
    hours = rng.randrange(1, 6)
    p = pw * 10 ** 9
    e = p * 3600 * hours
    ans = std_answer(e, "J", round_to_sf=2)
    return _q(f"A power station has a power output of {fmt_std(p)} W. Calculate the energy it transfers in {hours} hour{'s' if hours > 1 else ''}. Give your answer in standard form to 2 significant figures.",
              ans, f"{hours} hour{'s' if hours > 1 else ''} = {3600 * hours} s. E = P × t = {fmt_std(p)} × {3600 * hours} = {ans.display} (2 s.f.)",
              "Convert the time into seconds, then use energy = power × time",
              [std_mistake(p * hours, "J", f"Convert {hours} hour{'s' if hours > 1 else ''} into seconds first: × 3600", round_to_sf=2),
               std_mistake(p * 60 * hours, "J", "There are 3600 seconds in an hour (60 × 60)", round_to_sf=2)])


# ============================================================= Ohm's law

def _ohm_1(rng):
    i, r = rng.randrange(1, 11), rng.randrange(2, 61)
    v = i * r
    return _q(f"A current of {i} A flows through a {r} Ω resistor. Calculate the potential difference across the resistor.",
              num_answer(v, f"{v} V"), f"V = I × R = {i} × {r} = {v} V", "Use V = I × R",
              [_m(Fraction(r, i), "V", "V = I × R — multiply, don't divide"),
               _m(Fraction(i, r), "V", "V = I × R — multiply, don't divide")])


def _ohm_2(rng):
    i = _choice(rng, ("0.5", "1", "1.5", "2", "2.5", "3", "4", "0.25"))
    r = rng.randrange(2, 49)
    v = i * r
    if rng.random() < 0.5:
        return _q(f"A {n(v)} V supply drives a current of {n(i)} A through a lamp. Calculate the resistance of the lamp.",
                  num_answer(r, f"{r} Ω"), f"R = V ÷ I = {n(v)} ÷ {n(i)} = {r} Ω", "Rearrange V = I × R to make R the subject",
                  [_m(v * i, "Ω", "R = V ÷ I — divide, don't multiply"),
                   _m(i / v, "Ω", "R = V ÷ I — you divided the wrong way round")])
    return _q(f"A potential difference of {n(v)} V is applied across a {r} Ω resistor. Calculate the current through it.",
              num_answer(i, f"{n(i)} A"), f"I = V ÷ R = {n(v)} ÷ {r} = {n(i)} A", "Rearrange V = I × R to make I the subject",
              [_m(v * r, "A", "I = V ÷ R — divide, don't multiply"),
               _m(r / v, "A", "I = V ÷ R — you divided the wrong way round")])


def _ohm_3(rng):
    ima, r = rng.randrange(1, 19) * 50, rng.randrange(1, 21) * 10
    ia = Fraction(ima, 1000)
    v = ia * r
    return _q(f"A current of {ima} mA flows through a {r} Ω resistor. Calculate the potential difference across it.",
              num_answer(v, f"{n(v)} V"), f"{ima} mA = {n(ia)} A. V = I × R = {n(ia)} × {r} = {n(v)} V",
              f"Convert {ima} mA into amps first",
              [_m(ima * r, "V", f"Convert {ima} mA into amps first: {ima} ÷ 1000 = {n(ia)} A")])


def _ohm_4(rng):
    if rng.random() < 0.5:
        r, ima = rng.randrange(1, 51) * 10, rng.randrange(1, 21) * 10
        v = Fraction(r * ima, 1000)
        return _q(f"The potential difference across a resistor is {n(v)} V and the current through it is {ima} mA. Calculate the resistance.",
                  num_answer(r, f"{r} Ω"), f"{ima} mA = {n(Fraction(ima, 1000))} A. R = V ÷ I = {n(v)} ÷ {n(Fraction(ima, 1000))} = {r} Ω",
                  f"Convert {ima} mA into amps, then rearrange V = I × R",
                  [_m(v / ima, "Ω", f"Convert {ima} mA into amps first: {ima} ÷ 1000 = {n(Fraction(ima, 1000))} A")])
    ima, r = rng.randrange(1, 31) * 10, rng.choice((50, 100, 150, 200, 250, 300, 400, 500, 600))
    v = Fraction(ima * r, 1000)
    return _q(f"A {n(v)} V supply is connected across a {r} Ω resistor. Calculate the current in mA.",
              num_answer(ima, f"{ima} mA"), f"I = V ÷ R = {n(v)} ÷ {r} = {n(Fraction(ima, 1000))} A = {ima} mA",
              "Rearrange V = I × R to find the current in amps, then convert to mA",
              [_m(Fraction(ima, 1000), "mA", "That's the current in amps — multiply by 1000 to get milliamps"),
               _m(v * r, "mA", "I = V ÷ R — divide, don't multiply")])


def _ohm_5(rng):
    i = _choice(rng, ("0.1", "0.2", "0.25", "0.4", "0.5", "1", "1.5", "2"))
    r1, r2 = rng.randrange(2, 31), rng.randrange(2, 31)
    while r2 == r1:
        r2 = rng.randrange(2, 31)
    v = i * (r1 + r2)
    head = f"A {r1} Ω resistor and a {r2} Ω resistor are connected in series to a {n(v)} V battery. "
    if rng.random() < 0.5:
        return _q(head + "Calculate the current in the circuit.", num_answer(i, f"{n(i)} A"),
                  f"Total resistance = {r1} + {r2} = {r1 + r2} Ω. I = V ÷ R = {n(v)} ÷ {r1 + r2} = {n(i)} A",
                  "In series, add the resistances to find the total resistance",
                  [_m(v / r1, "A", f"In series, add the resistances first: {r1} + {r2} = {r1 + r2} Ω"),
                   _m(v / r1 + v / r2, "A", f"In series, add the resistances first: {r1} + {r2} = {r1 + r2} Ω")])
    v1 = i * r1
    return _q(head + f"Calculate the potential difference across the {r1} Ω resistor.", num_answer(v1, f"{n(v1)} V"),
              f"Total resistance = {r1 + r2} Ω, so I = {n(v)} ÷ {r1 + r2} = {n(i)} A. V = I × R = {n(i)} × {r1} = {n(v1)} V",
              "Find the current first using the total resistance",
              [_m(v / 2, "V", "The potential difference is shared in proportion to the resistances, not equally"),
               _m(v * r1 / r2, "V", "Find the current first using the total resistance, then use V = I × R")])


# ======================================================== electrical power

def _ep_1(rng):
    i, v = rng.randrange(1, 11), rng.choice((3, 6, 9, 12, 24, 230))
    p = i * v
    return _q(f"A device connected to a {v} V supply draws a current of {i} A. Calculate its power.",
              num_answer(p, f"{p} W"), f"P = I × V = {i} × {v} = {p} W", "Use P = I × V",
              [_m(Fraction(v, i), "W", "P = I × V — multiply, don't divide"),
               _m(Fraction(i, v), "W", "P = I × V — multiply, don't divide")])


def _ep_2(rng):
    v = rng.choice((6, 12, 24, 230))
    i = _choice(rng, ("0.5", "1", "2", "2.5", "4", "5", "8", "10", "13"))
    p = i * v
    if rng.random() < 0.5:
        return _q(f"A {n(p)} W appliance is connected to a {v} V supply. Calculate the current it draws.",
                  num_answer(i, f"{n(i)} A"), f"I = P ÷ V = {n(p)} ÷ {v} = {n(i)} A", "Rearrange P = I × V to make I the subject",
                  [_m(p * v, "A", "I = P ÷ V — divide, don't multiply"),
                   _m(v / p, "A", "I = P ÷ V — you divided the wrong way round")])
    return _q(f"An appliance has a power of {n(p)} W and draws a current of {n(i)} A. Calculate the potential difference across it.",
              num_answer(v, f"{v} V"), f"V = P ÷ I = {n(p)} ÷ {n(i)} = {v} V", "Rearrange P = I × V to make V the subject",
              [_m(p * i, "V", "V = P ÷ I — divide, don't multiply"),
               _m(i / p, "V", "V = P ÷ I — you divided the wrong way round")])


def _ep_3(rng):
    ima, v = rng.randrange(1, 19) * 50, rng.choice((3, 6, 9, 12, 24))
    ia = Fraction(ima, 1000)
    p = ia * v
    return _q(f"A {v} V torch bulb draws a current of {ima} mA. Calculate its power.",
              num_answer(p, f"{n(p)} W"), f"{ima} mA = {n(ia)} A. P = I × V = {n(ia)} × {v} = {n(p)} W",
              f"Convert {ima} mA into amps first",
              [_m(ima * v, "W", f"Convert {ima} mA into amps first: {ima} ÷ 1000 = {n(ia)} A")])


def _ep_4(rng):
    v, ima = rng.choice((3, 5, 6, 9, 12, 24)), rng.randrange(1, 21) * 10
    p = Fraction(v * ima, 1000)
    return _q(f"A device with a power of {n(p)} W draws a current of {ima} mA. Calculate the potential difference across it.",
              num_answer(v, f"{v} V"), f"{ima} mA = {n(Fraction(ima, 1000))} A. V = P ÷ I = {n(p)} ÷ {n(Fraction(ima, 1000))} = {v} V",
              f"Convert {ima} mA into amps, then rearrange P = I × V",
              [_m(p / ima, "V", f"Convert {ima} mA into amps first: {ima} ÷ 1000 = {n(Fraction(ima, 1000))} A"),
               _m(p * Fraction(ima, 1000), "V", "V = P ÷ I — divide, don't multiply")])


def _ep_5(rng):
    if rng.random() < 0.5:
        i, r = _choice(rng, ("0.5", "1", "1.5", "2", "3", "4", "5")), rng.randrange(2, 41)
        p = i * i * r
        return _q(f"A current of {n(i)} A flows through a {r} Ω resistor. Calculate the power transferred in the resistor.",
                  num_answer(p, f"{n(p)} W"), f"P = I² × R = {n(i)}² × {r} = {n(i * i)} × {r} = {n(p)} W", "Use P = I² × R",
                  [_m(i * r, "W", "That's the potential difference (I × R) — power = I² × R"),
                   _m(i * r * r, "W", "Square the current, not the resistance: P = I² × R"),
                   _m(2 * i * r, "W", "I² means I × I, not 2 × I")])
    v, i, mins = rng.choice((6, 12, 24, 230)), rng.randrange(1, 6), rng.randrange(2, 11)
    e = v * i * 60 * mins
    return _q(f"A {v} V motor draws a current of {i} A for {mins} minutes. Calculate the energy transferred.",
              num_answer(e, f"{e} J"), f"P = I × V = {i} × {v} = {i * v} W. {mins} minutes = {60 * mins} s, so E = {i * v} × {60 * mins} = {e} J",
              "Find the power (P = I × V), then energy = power × time in seconds",
              [_m(v * i * mins, "J", f"Convert {mins} minutes into seconds first: {mins} × 60 = {60 * mins} s"),
               _m(v * i, "J", "That's the power — multiply by the time in seconds to get the energy")])


# ================================================================= charge

def _charge_1(rng):
    i, t = rng.randrange(1, 11), rng.randrange(2, 61)
    q = i * t
    return _q(f"A current of {i} A flows for {t} s. Calculate the charge that flows.",
              num_answer(q, f"{q} C"), f"Q = I × t = {i} × {t} = {q} C", "Use Q = I × t",
              [_m(Fraction(t, i), "C", "Q = I × t — multiply, don't divide"),
               _m(Fraction(i, t), "C", "Q = I × t — multiply, don't divide")])


def _charge_2(rng):
    i = _choice(rng, ("0.5", "1", "1.5", "2", "2.5", "3", "4", "5"))
    t = rng.randrange(4, 121)
    q = i * t
    if rng.random() < 0.5:
        return _q(f"A charge of {n(q)} C flows through a lamp in {t} s. Calculate the current.",
                  num_answer(i, f"{n(i)} A"), f"I = Q ÷ t = {n(q)} ÷ {t} = {n(i)} A", "Rearrange Q = I × t to make I the subject",
                  [_m(q * t, "A", "I = Q ÷ t — divide, don't multiply"),
                   _m(t / q, "A", "I = Q ÷ t — you divided the wrong way round")])
    return _q(f"A current of {n(i)} A flows through a wire. How long does it take for {n(q)} C of charge to flow?",
              num_answer(t, f"{t} s"), f"t = Q ÷ I = {n(q)} ÷ {n(i)} = {t} s", "Rearrange Q = I × t to make t the subject",
              [_m(q * i, "s", "t = Q ÷ I — divide, don't multiply"),
               _m(i / q, "s", "t = Q ÷ I — you divided the wrong way round")])


def _charge_3(rng):
    if rng.random() < 0.5:
        i, mins = rng.randrange(1, 11), rng.randrange(2, 11)
        q = i * 60 * mins
        return _q(f"A current of {i} A flows for {mins} minutes. Calculate the charge that flows.",
                  num_answer(q, f"{q} C"), f"{mins} minutes = {60 * mins} s. Q = {i} × {60 * mins} = {q} C",
                  f"Convert {mins} minutes into seconds first",
                  [_m(i * mins, "C", f"Convert {mins} minutes into seconds first: {mins} × 60 = {60 * mins} s")])
    ima, t = rng.randrange(1, 19) * 50, rng.randrange(2, 61)
    ia = Fraction(ima, 1000)
    q = ia * t
    return _q(f"A current of {ima} mA flows for {t} s. Calculate the charge that flows.",
              num_answer(q, f"{n(q)} C"), f"{ima} mA = {n(ia)} A. Q = {n(ia)} × {t} = {n(q)} C",
              f"Convert {ima} mA into amps first",
              [_m(ima * t, "C", f"Convert {ima} mA into amps first: {ima} ÷ 1000 = {n(ia)} A")])


def _charge_4(rng):
    if rng.random() < 0.5:
        i, mins = _choice(rng, ("0.25", "0.5", "0.75", "1.5", "2", "2.5", "3")), rng.randrange(1, 11)
        q = i * 60 * mins
        return _q(f"A charge of {n(q)} C flows through a lamp in {mins} minute{'s' if mins > 1 else ''}. Calculate the current.",
                  num_answer(i, f"{n(i)} A"), f"{mins} minute{'s' if mins > 1 else ''} = {60 * mins} s. I = Q ÷ t = {n(q)} ÷ {60 * mins} = {n(i)} A",
                  "Convert the time into seconds, then rearrange Q = I × t",
                  [_m(q / mins, "A", f"Convert {mins} minute{'s' if mins > 1 else ''} into seconds first: × 60")])
    ima, t = rng.randrange(1, 21) * 50, rng.randrange(2, 61)
    q = Fraction(ima * t, 1000)
    return _q(f"How long, in seconds, does it take for {n(q)} C of charge to flow when the current is {ima} mA?",
              num_answer(t, f"{t} s"), f"{ima} mA = {n(Fraction(ima, 1000))} A. t = Q ÷ I = {n(q)} ÷ {n(Fraction(ima, 1000))} = {t} s",
              f"Convert {ima} mA into amps, then rearrange Q = I × t",
              [_m(q / ima, "s", f"Convert {ima} mA into amps first: {ima} ÷ 1000 = {n(Fraction(ima, 1000))} A")])


def _charge_5(rng):
    i = _choice(rng, ("0.2", "0.25", "0.5", "1", "1.5", "2"))
    mins, v = rng.randrange(1, 11), rng.choice((1.5, 3, 6, 9, 12, 24, 230))
    v = F(str(v))
    q = i * 60 * mins
    e = q * v
    ans, tail, shown = _final(e, "J")
    return _q(f"A current of {n(i)} A flows through a {n(v)} V lamp for {mins} minute{'s' if mins > 1 else ''}. Calculate the energy transferred. Use Q = I × t and E = Q × V.{tail}",
              ans, f"t = {60 * mins} s, so Q = {n(i)} × {60 * mins} = {n(q)} C. E = Q × V = {n(q)} × {n(v)} = {shown}",
              "Find the charge first (Q = I × t, with t in seconds), then use E = Q × V",
              [_m(i * mins * v, "J", f"Convert {mins} minute{'s' if mins > 1 else ''} into seconds first: × 60"),
               _m(q, "J", "That's the charge — now use E = Q × V to find the energy")])


# ================================================================ density

_MATERIALS = (("aluminium", "2.7"), ("iron", "7.8"), ("copper", "8.9"), ("lead", "11.3"),
              ("glass", "2.5"), ("gold", "19.3"), ("brass", "8.5"), ("granite", "2.6"))


def _dens_1(rng):
    rho, vol = rng.randrange(1, 13), rng.randrange(2, 51)
    m = rho * vol
    return _q(f"A stone has a mass of {m} g and a volume of {vol} cm³. Calculate its density in g/cm³.",
              num_answer(rho, f"{rho} g/cm³"), f"density = mass ÷ volume = {m} ÷ {vol} = {rho} g/cm³",
              "density = mass ÷ volume",
              [_m(Fraction(vol, m), "g/cm³", "density = mass ÷ volume — you divided the wrong way round"),
               _m(m * vol, "g/cm³", "density = mass ÷ volume — divide, don't multiply")])


def _dens_2(rng):
    name, r = rng.choice(_MATERIALS)
    rho = F(r)
    vol = rng.randrange(2, 51) * (10 if rho.denominator != 1 else 1)
    m = rho * vol
    if rng.random() < 0.5:
        return _q(f"{name.capitalize()} has a density of {r} g/cm³. Calculate the mass of a {vol} cm³ block of {name}.",
                  num_answer(m, f"{n(m)} g"), f"mass = density × volume = {r} × {vol} = {n(m)} g",
                  "Rearrange density = mass ÷ volume to make mass the subject",
                  [_m(vol / rho, "g", "mass = density × volume — multiply, don't divide"),
                   _m(rho / vol, "g", "mass = density × volume — multiply, don't divide")])
    return _q(f"{name.capitalize()} has a density of {r} g/cm³. Calculate the volume of a piece of {name} with a mass of {n(m)} g.",
              num_answer(vol, f"{vol} cm³"), f"volume = mass ÷ density = {n(m)} ÷ {r} = {vol} cm³",
              "Rearrange density = mass ÷ volume to make volume the subject",
              [_m(m * rho, "cm³", "volume = mass ÷ density — divide, don't multiply"),
               _m(rho / m, "cm³", "volume = mass ÷ density — you divided the wrong way round")])


def _dens_3(rng):
    name, r = rng.choice(_MATERIALS)
    rho = F(r)
    vol = rng.randrange(1, 31) * 10
    mg = rho * vol
    mkg = mg / 1000
    return _q(f"A block of {name} has a mass of {n(mkg)} kg and a volume of {vol} cm³. Calculate its density in g/cm³.",
              num_answer(rho, f"{r} g/cm³"), f"{n(mkg)} kg = {n(mg)} g. density = {n(mg)} ÷ {vol} = {r} g/cm³",
              f"Convert {n(mkg)} kg into grams first",
              [_m(mkg / vol, "g/cm³", f"Convert {n(mkg)} kg into grams first: × 1000")])


def _dens_4(rng):
    name, r = rng.choice(_MATERIALS)
    rho = F(r)
    vol = rng.randrange(1, 21) * 50
    mg = rho * vol
    mkg = mg / 1000
    if rng.random() < 0.5:
        return _q(f"{name.capitalize()} has a density of {r} g/cm³. Calculate the mass, in kg, of a {vol} cm³ block of {name}.",
                  num_answer(mkg, f"{n(mkg)} kg"), f"mass = {r} × {vol} = {n(mg)} g = {n(mkg)} kg",
                  "Find the mass in grams (density × volume), then convert to kilograms",
                  [_m(mg, "kg", "That's the mass in grams — divide by 1000 to get kilograms"),
                   _m(Fraction(vol) / rho / 1000, "kg", "mass = density × volume — multiply, don't divide")])
    return _q(f"{name.capitalize()} has a density of {r} g/cm³. Calculate the volume, in cm³, of {n(mkg)} kg of {name}.",
              num_answer(vol, f"{vol} cm³"), f"{n(mkg)} kg = {n(mg)} g. volume = {n(mg)} ÷ {r} = {vol} cm³",
              f"Convert {n(mkg)} kg into grams, then use volume = mass ÷ density",
              [_m(mkg / rho, "cm³", f"Convert {n(mkg)} kg into grams first: × 1000"),
               _m(mg * rho, "cm³", "volume = mass ÷ density — divide, don't multiply")])


def _dens_5(rng):
    name, r = rng.choice(_MATERIALS)
    rho = F(r)
    if rng.random() < 0.5:
        a, b, c = rng.randrange(1, 11), rng.randrange(1, 11), rng.randrange(2, 11)
        vol = a * b * c
        m = rho * vol
        return _q(f"A block measures {a} cm × {b} cm × {c} cm and has a mass of {n(m)} g. Calculate its density in g/cm³.",
                  num_answer(rho, f"{r} g/cm³"), f"Volume = {a} × {b} × {c} = {vol} cm³. density = {n(m)} ÷ {vol} = {r} g/cm³",
                  "Work out the volume of the block first (length × width × height)",
                  [_m(m / (a + b + c), "g/cm³", "Volume of a cuboid = length × width × height, not the sum"),
                   _m(vol / m, "g/cm³", "density = mass ÷ volume — you divided the wrong way round")])
    vol = rng.randrange(5, 41)
    start = rng.randrange(20, 81)
    end = start + vol
    m = rho * vol
    return _q(f"The water level in a measuring cylinder rises from {start} cm³ to {end} cm³ when a stone of mass {n(m)} g is lowered into it. Calculate the density of the stone in g/cm³.",
              num_answer(rho, f"{r} g/cm³"), f"Volume of stone = {end} − {start} = {vol} cm³. density = {n(m)} ÷ {vol} = {r} g/cm³",
              "The stone's volume is the rise in the water level",
              [_m(m / end, "g/cm³", f"The stone's volume is the rise in water level: {end} − {start} = {vol} cm³"),
               _m(m / start, "g/cm³", f"The stone's volume is the rise in water level: {end} − {start} = {vol} cm³")])


# =============================================================== pressure

def _pres_1(rng):
    p, a = rng.randrange(2, 101) * 10, rng.randrange(2, 11)
    f = p * a
    return _q(f"A force of {f} N acts on an area of {a} m². Calculate the pressure.",
              num_answer(p, f"{p} Pa"), f"pressure = force ÷ area = {f} ÷ {a} = {p} Pa", "pressure = force ÷ area",
              [_m(Fraction(a, f), "Pa", "pressure = force ÷ area — you divided the wrong way round"),
               _m(f * a, "Pa", "pressure = force ÷ area — divide, don't multiply")])


def _pres_2(rng):
    p = rng.randrange(1, 51) * 100
    a = _choice(rng, ("0.5", "1.5", "2", "2.5", "3", "4", "5", "0.2"))
    f = p * a
    if rng.random() < 0.5:
        return _q(f"A pressure of {p} Pa acts on an area of {n(a)} m². Calculate the force.",
                  num_answer(f, f"{n(f)} N"), f"force = pressure × area = {p} × {n(a)} = {n(f)} N",
                  "Rearrange pressure = force ÷ area to make force the subject",
                  [_m(p / a, "N", "force = pressure × area — multiply, don't divide"),
                   _m(a / p, "N", "force = pressure × area — multiply, don't divide")])
    return _q(f"A force of {n(f)} N produces a pressure of {p} Pa. Calculate the area it acts on.",
              num_answer(a, f"{n(a)} m²"), f"area = force ÷ pressure = {n(f)} ÷ {p} = {n(a)} m²",
              "Rearrange pressure = force ÷ area to make area the subject",
              [_m(f * p, "m²", "area = force ÷ pressure — divide, don't multiply"),
               _m(p / f, "m²", "area = force ÷ pressure — you divided the wrong way round")])


def _pres_3(rng):
    def make(r):
        p, a_cm = r.randrange(2, 101) * 500, r.randrange(1, 41) * 10
        f = Fraction(p * a_cm, 10000)
        return (p, a_cm, f) if sig_digits(f) <= 3 and f >= 1 else None
    p, a_cm, f = retry(make, rng)
    a_m = Fraction(a_cm, 10000)
    return _q(f"A force of {n(f)} N acts on an area of {a_cm} cm². Calculate the pressure in pascals (Pa).",
              num_answer(p, f"{p} Pa"), f"{a_cm} cm² = {a_cm} ÷ 10 000 = {n(a_m)} m². pressure = {n(f)} ÷ {n(a_m)} = {p} Pa",
              f"Convert {a_cm} cm² into m² first (1 m² = 10 000 cm²)",
              [_m(f / a_cm, "Pa", f"Convert {a_cm} cm² into m² first: ÷ 10 000"),
               _m(f / Fraction(a_cm, 100), "Pa", "1 m² = 10 000 cm², so divide by 10 000, not 100")])


def _pres_4(rng):
    def make(r):
        p, a_cm = r.randrange(2, 101) * 500, r.randrange(1, 41) * 10
        f = Fraction(p * a_cm, 10000)
        return (p, a_cm, f) if sig_digits(f) <= 3 and f >= 1 else None
    p, a_cm, f = retry(make, rng)
    a_m = Fraction(a_cm, 10000)
    return _q(f"A pressure of {p} Pa acts on an area of {a_cm} cm². Calculate the force.",
              num_answer(f, f"{n(f)} N"), f"{a_cm} cm² = {n(a_m)} m². force = pressure × area = {p} × {n(a_m)} = {n(f)} N",
              f"Convert {a_cm} cm² into m², then use force = pressure × area",
              [_m(p * a_cm, "N", f"Convert {a_cm} cm² into m² first: ÷ 10 000"),
               _m(Fraction(p * a_cm, 100), "N", "1 m² = 10 000 cm², so divide by 10 000, not 100")])


def _pres_5(rng):
    if rng.random() < 0.65:
        def make(r):
            m = r.randrange(4, 41) * 5
            l, w = F(r.randrange(2, 16)) / 10, F(r.randrange(2, 16)) / 10
            return G * m / (l * w), m, l, w
        p, m, l, w = _picked(rng, make)
        ans, tail, shown = _final(p, "Pa")
        wt, area = G * m, l * w
        return _q(f"A crate of mass {m} kg rests on a floor. Its base measures {n(l)} m by {n(w)} m. Calculate the pressure it exerts on the floor. {G_TXT}{tail}",
                  ans, f"Force = weight = {m} × 9.8 = {n(wt)} N. Area = {n(l)} × {n(w)} = {n(area)} m². pressure = {n(wt)} ÷ {n(area)} = {shown}",
                  "The force on the floor is the crate's weight (W = m × g)",
                  [_m(m / area, "Pa", "The force is the crate's weight: W = m × g, not the mass"),
                   _m(wt / (l + w), "Pa", "Area of the base = length × width, not length + width")])
    f = rng.randrange(2, 13) * 5
    k = rng.randrange(1, 10)
    a = F(k) / 10 ** 6
    p = f / a
    ans = std_answer(p, "Pa", round_to_sf=2)
    return _q(f"A drawing pin is pushed into a board with a force of {f} N. The area of its point is {k} × 10^-6 m². Calculate the pressure under the point. Give your answer in standard form to 2 significant figures.",
              ans, f"pressure = force ÷ area = {f} ÷ ({k} × 10^-6) = {ans.display} (2 s.f.)",
              "pressure = force ÷ area — take care with the power of 10",
              [std_mistake(f * a, "Pa", "pressure = force ÷ area — divide, don't multiply", round_to_sf=2),
               std_mistake(f / (F(k) / 10 ** 4), "Pa", "Check the power of 10: the area is k × 10^-6 m²", round_to_sf=2)])


# ============================================================ registration

def _skill(name: str, title: str, aliases: tuple[str, ...], levels: tuple, fallback: str) -> Skill:
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
    _skill("speed", "Speed", ("speed", "distance time", "average speed", "distance-time", "speed distance time"),
           (_speed_1, _speed_2, _speed_3, _speed_4, _speed_5), "Use speed = distance ÷ time and check the units"),
    _skill("acceleration", "Acceleration", ("acceleration", "deceleration", "accelerate", "change in velocity"),
           (_acc_1, _acc_2, _acc_3, _acc_4, _acc_5), "Use acceleration = change in velocity ÷ time"),
    _skill("force", "Force (F = ma)", ("f=ma", "resultant force", "newton's second law", "force", "forces"),
           (_force_1, _force_2, _force_3, _force_4, _force_5), "Use F = m × a, with the mass in kilograms"),
    _skill("weight", "Weight (W = mg)", ("weight", "w=mg", "gravitational field strength", "mass and weight"),
           (_weight_1, _weight_2, _weight_3, _weight_4, _weight_5), "Use W = m × g, with the mass in kilograms"),
    _skill("kinetic_energy", "Kinetic energy", ("kinetic energy", "kinetic", "ek=1/2mv^2"),
           (_ke_1, _ke_2, _ke_3, _ke_4, _ke_5), "Use Ek = ½ × m × v², with the mass in kilograms"),
    _skill("gpe", "Gravitational potential energy",
           ("gpe", "gravitational potential energy", "potential energy", "ep=mgh", "mgh"),
           (_gpe_1, _gpe_2, _gpe_3, _gpe_4, _gpe_5), "Use Ep = m × g × h, with the mass in kg and the height in m"),
    _skill("power", "Power", ("power", "watts", "work done and power"),
           (_power_1, _power_2, _power_3, _power_4, _power_5), "Use power = energy ÷ time, with the time in seconds"),
    _skill("ohms_law", "Ohm's law (V = IR)",
           ("ohm's law", "ohms law", "resistance", "v=ir", "potential difference", "resistors in series"),
           (_ohm_1, _ohm_2, _ohm_3, _ohm_4, _ohm_5), "Use V = I × R, with the current in amps"),
    _skill("electrical_power", "Electrical power (P = IV)",
           ("electrical power", "p=iv", "p=i^2r", "power in circuits"),
           (_ep_1, _ep_2, _ep_3, _ep_4, _ep_5), "Use P = I × V, with the current in amps"),
    _skill("charge", "Charge (Q = It)", ("charge", "q=it", "electric charge", "coulombs"),
           (_charge_1, _charge_2, _charge_3, _charge_4, _charge_5), "Use Q = I × t, with the current in amps and the time in seconds"),
    _skill("density", "Density", ("density", "densities"),
           (_dens_1, _dens_2, _dens_3, _dens_4, _dens_5), "Use density = mass ÷ volume and check the units"),
    _skill("pressure", "Pressure", ("pressure", "p=f/a", "pascals"),
           (_pres_1, _pres_2, _pres_3, _pres_4, _pres_5), "Use pressure = force ÷ area, with the area in m²"),
)


_ROWS = (
    (("forces", "Forces & motion", ("speed", "acceleration", "force", "weight")),
     ("energy", "Energy", ("kinetic_energy", "gpe", "power"))),
    (("electricity", "Electricity", ("ohms_law", "electrical_power", "charge")),
     ("density_pressure", "Density & pressure", ("density", "pressure"))),
)


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"physics.y{y}.{slug}", label=label,
                    skills=tuple(f"{SUBJECT_ID}.{s}" for s in skills), level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Physics", order=20, years={10: _year(10), 11: _year(11)})


def register(reg) -> None:
    """Register Physics (Years 10–11) and its skills with a tutor.content Registry."""
    reg.register(make_subject(), list(SKILLS))
