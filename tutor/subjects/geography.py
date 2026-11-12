"""Geography (docs/ARCHITECTURE_V2.md section 5.3), Years 10–11.

Topics: Natural hazards | Rivers & coasts / Cities & development | Geographical skills.
The three bank skills (hazards, landscapes, urban) live in ``packs/geography.json``; the
generated skill ``geography.skills_stats`` ("Geographical skills") is defined here.

Ladder for skills_stats (v1 section 5 generator rules apply):
  L1 range or mean -> L2 median or mode -> L3 percentage change (1 d.p.) ->
  L4 interquartile range ((n + 1) ÷ 4 rule) -> L5 population density or map-scale distance.

Every generator is pure: ``generate(level, seed)`` uses only ``random.Random(seed)``, and every
answer is computed from the numbers exactly as they are printed in the question.
"""
from __future__ import annotations

import random
from fractions import Fraction
from typing import Callable

from ..content import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, load_pack
from ..content.fmt import (
    build, check_level, fmt_dp, fmt_num, group, near_half, num_answer, retry,
)

SUBJECT_ID = "geography"

Draft = dict

# (description with {n}, short name for the working, unit, low, high)
DATASETS = (
    ("the daily rainfall (mm) at a weather station over {n} days", "rainfall", "mm", 0, 34),
    ("the width (m) of a river at {n} sites along its course", "width", "m", 2, 30),
    ("the number of pedestrians counted in 5 minutes at {n} sites in a town centre", "count", "", 4, 90),
    ("the length (mm) of {n} pebbles measured on a beach", "length", "mm", 12, 95),
    ("the maximum daily temperature (°C) in a town over {n} days", "temperature", "°C", 6, 31),
    ("the number of cars passing a survey point in 10 minutes on {n} different roads", "count", "", 5, 80),
    ("the depth (cm) of a river at {n} points across the channel", "depth", "cm", 10, 95),
)

CHANGE_CONTEXTS = (
    ("The population of a village", "", 300, 9000),
    ("The number of visitors to a national park in one year", "", 2000, 90000),
    ("The annual rainfall at a weather station", "mm", 450, 2400),
    ("The number of people living in a city's inner area", "", 5000, 80000),
    ("The number of homes in a small town", "", 800, 12000),
    ("The amount of sediment carried past a gauging station in a year (tonnes)", "", 1500, 40000),
)


# ================================================================ helpers

def _q(text: str, answer: Answer, solution: str, hint: str, mistakes=()) -> Draft:
    return {"text": text, "answer": answer, "solution": solution, "hint": hint, "mistakes": list(mistakes)}


def _with_unit(numstr: str, u: str) -> str:
    if not u:
        return numstr
    if u == "°C":
        return numstr + "°C"
    if u == "%":
        return numstr + "%"
    return f"{numstr} {u}"


def _disp(v, u: str, dp: int | None = None) -> str:
    return _with_unit(fmt_dp(v, dp) if dp is not None else fmt_num(v), u)


def _ans(v, u: str, dp: int | None = None) -> Answer:
    return num_answer(v, _disp(v, u, dp), dp=dp)


def _mis(v, u: str, feedback: str, dp: int | None = None) -> Mistake | None:
    if v is None:
        return None
    return Mistake(Answer(kind="number", display=_disp(v, u, dp), value=float(v), dp=dp), feedback)


def _listing(values: list[int]) -> str:
    return ", ".join(str(v) for v in values)


def _intro(rng: random.Random, n: int) -> tuple[str, str, str, int, int]:
    desc, name, u, lo, hi = rng.choice(DATASETS)
    who = rng.choice(("A student", "A geography class", "A fieldwork group", "Priya", "Tom", "Amira", "Josh"))
    return f"{who} recorded {desc.format(n=n)}:", name, u, lo, hi


def _approx(v: Fraction) -> str:
    """Calculator display for working: exact if it has at most 3 d.p., else 3 d.p. followed by '…'."""
    if (v * 1000).denominator == 1:
        return fmt_num(v)
    t = Fraction(int(v * 1000), 1000)
    return fmt_dp(t, 3) + "…"


def _ordinal(k: int) -> str:
    if 10 <= k % 100 <= 20:
        return f"{k}th"
    return f"{k}" + {1: "st", 2: "nd", 3: "rd"}.get(k % 10, "th")


# ================================================================ L1: range or mean

def _l1(rng: random.Random) -> Draft:
    if rng.random() < 0.5:
        return _l1_range(rng)
    return _l1_mean(rng)


def _l1_range(rng: random.Random) -> Draft:
    n = rng.randint(6, 8)
    intro, name, u, lo, hi = _intro(rng, n)

    def pick(r):
        vals = [r.randint(lo, hi) for _ in range(n)]
        if max(vals) - min(vals) < 5:
            return None
        return vals
    vals = retry(pick, rng)
    big, small = max(vals), min(vals)
    rng_v = big - small
    text = f"{intro}\n{_listing(vals)}\nWork out the range."
    sol = f"Range = highest − lowest = {big} − {small} = {_disp(rng_v, u)}"
    ms = [_mis(big, u, "That's the highest value — the range is the highest value minus the lowest value")]
    first_last = vals[0] - vals[-1]
    if first_last > 0 and first_last != rng_v:
        ms.append(_mis(first_last, u, "Use the highest and lowest values, not the first and last ones"))
    return _q(text, _ans(rng_v, u), sol, "Find the highest and the lowest values first", ms)


def _l1_mean(rng: random.Random) -> Draft:
    n = rng.randint(5, 7)
    intro, name, u, lo, hi = _intro(rng, n)

    def pick(r):
        m = r.randint(lo + 3, hi - 3)
        vals = [r.randint(lo, hi) for _ in range(n - 1)]
        last = n * m - sum(vals)
        if not lo <= last <= hi:
            return None
        vals.append(last)
        r.shuffle(vals)
        if len(set(vals)) < 3:
            return None
        return vals, m
    vals, m = retry(pick, rng)
    total = sum(vals)
    text = f"{intro}\n{_listing(vals)}\nWork out the mean."
    sol = f"Total = {total}, and there are {n} values, so mean = {total} ÷ {n} = {_disp(m, u)}"
    ms = [_mis(total, u, f"That's the total — now divide it by the number of values ({n})")]
    alt = Fraction(total, n - 1)
    if alt.denominator == 1:
        ms.append(_mis(alt, u, f"Count the values again — there are {n} of them"))
    return _q(text, _ans(m, u), sol, "Add up all the values, then divide by how many values there are", ms)


# ================================================================ L2: median or mode

def _l2(rng: random.Random) -> Draft:
    if rng.random() < 0.5:
        return _l2_median(rng)
    return _l2_mode(rng)


def _l2_median(rng: random.Random) -> Draft:
    n = rng.choice((6, 8))
    intro, name, u, lo, hi = _intro(rng, n)

    def pick(r):
        vals = [r.randint(lo, hi) for _ in range(n)]
        s = sorted(vals)
        unsorted_mid = Fraction(vals[n // 2 - 1] + vals[n // 2], 2)
        med = Fraction(s[n // 2 - 1] + s[n // 2], 2)
        if unsorted_mid == med or len(set(vals)) < n - 1:
            return None
        return vals, s, med, unsorted_mid
    vals, s, med, unsorted_mid = retry(pick, rng)
    a, b = s[n // 2 - 1], s[n // 2]
    text = f"{intro}\n{_listing(vals)}\nWork out the median."
    sol = (f"In order: {_listing(s)}. The middle two values are {a} and {b}, "
           f"so the median = ({a} + {b}) ÷ 2 = {_disp(med, u)}")
    ms = [_mis(unsorted_mid, u, "Put the values in order before finding the middle")]
    mean = Fraction(sum(vals), n)
    if (mean * 2).denominator == 1 and mean != med:
        ms.append(_mis(mean, u, "That's the mean — the median is the middle value when the data is in order"))
    return _q(text, _ans(med, u), sol,
              f"Put the values in order. With {n} values, the median is halfway between the middle two", ms)


def _l2_mode(rng: random.Random) -> Draft:
    n = rng.randint(7, 9)
    intro, name, u, lo, hi = _intro(rng, n)

    def pick(r):
        mode = r.randint(lo + 1, hi - 1)
        pool = [v for v in range(lo, hi + 1) if v != mode]
        if len(pool) < n - 3:
            return None
        others = r.sample(pool, n - 3)
        vals = others + [mode] * 3
        r.shuffle(vals)
        return vals, mode
    vals, mode = retry(pick, rng)
    text = f"{intro}\n{_listing(vals)}\nWhat is the mode?"
    sol = f"{mode} appears 3 times, more often than any other value, so the mode = {_disp(mode, u)}"
    ms = []
    if max(vals) != mode:
        ms.append(_mis(max(vals), u, "That's the highest value — the mode is the value that appears most often"))
    s = sorted(vals)
    med = s[n // 2] if n % 2 else None
    if med is not None and med != mode:
        ms.append(_mis(med, u, "That's the median — the mode is the value that appears most often"))
    return _q(text, _ans(mode, u), sol, "Look for the value that appears most often", ms)


# ================================================================ L3: percentage change (1 d.p.)

def _l3(rng: random.Random) -> Draft:
    ctx, u, lo, hi = rng.choice(CHANGE_CONTEXTS)
    up = rng.random() < 0.5

    def pick(r):
        old = r.randint(lo, hi)
        pct = r.randint(3, 60)
        delta = old * pct // 100 + r.randint(-old // 50, old // 50)
        if delta <= 0:
            return None
        new = old + delta if up else old - delta
        if new <= 0:
            return None
        change = Fraction(abs(new - old) * 100, old)
        if change < 1 or near_half(change, dp=1):
            return None
        by_new = Fraction(abs(new - old) * 100, new)
        if near_half(by_new, dp=1):
            return None
        return old, new, change, by_new
    old, new, change, by_new = retry(pick, rng)
    word = "increase" if up else "decrease"
    verb = "rose" if up else "fell"
    o_s, n_s = _with_unit(group(old), u), _with_unit(group(new), u)
    diff = abs(new - old)
    text = (f"{ctx} {verb} from {o_s} to {n_s}. Work out the percentage {word}. "
            f"Give your answer to 1 decimal place.")
    if (change * 10).denominator == 1:
        sol = f"Change = {group(diff)}. {group(diff)} ÷ {group(old)} × 100 = {fmt_dp(change, 1)}%"
    else:
        sol = (f"Change = {group(diff)}. {group(diff)} ÷ {group(old)} × 100 = {_approx(change)} "
               f"= {fmt_dp(change, 1)}% (1 d.p.)")
    ms = [_mis(by_new, "%", "Divide the change by the original value, not the new one", dp=1),
          _mis(diff, "", "That's the actual change — divide it by the original value and multiply by 100")]
    if not up:
        ms.append(_mis(-change, "%", "Right size — but a percentage decrease is written as a positive number", dp=1))
    return _q(text, _ans(change, "%", 1), sol,
              f"Find the change first, then divide it by the original value ({group(old)}) and multiply by 100", ms)


# ================================================================ L4: interquartile range

def _l4(rng: random.Random) -> Draft:
    n = rng.choice((7, 11))
    intro, name, u, lo, hi = _intro(rng, n)

    def pick(r):
        if hi - lo + 1 < n:
            return None
        vals = r.sample(range(lo, hi + 1), n)
        s = sorted(vals)
        k = (n + 1) // 4
        lq, uq = s[k - 1], s[3 * k - 1]
        bad = vals[3 * k - 1] - vals[k - 1]
        return vals, s, k, lq, uq, bad
    vals, s, k, lq, uq, bad = retry(pick, rng)
    iqr = uq - lq
    text = (f"{intro}\n{_listing(vals)}\nWork out the interquartile range. "
            f"Use the (n + 1) ÷ 4 rule to find the quartiles.")
    sol = (f"In order: {_listing(s)}. (n + 1) ÷ 4 = {k}, so the lower quartile is the {_ordinal(k)} value ({lq}) "
           f"and the upper quartile is the {_ordinal(3 * k)} value ({uq}). IQR = {uq} − {lq} = {_disp(iqr, u)}")
    ms = [_mis(s[-1] - s[0], u, "That's the range — the interquartile range is the upper quartile minus the lower quartile")]
    if bad > 0 and bad != iqr:
        ms.append(_mis(bad, u, "Put the values in order before finding the quartiles"))
    return _q(text, _ans(iqr, u), sol,
              f"Put the values in order. With {n} values, the lower quartile is the {_ordinal(k)} value", ms)


# ================================================================ L5: population density or map scale

REGIONS = ("A district", "A county", "An island", "A rural region", "A city borough", "A national park")


def _l5(rng: random.Random) -> Draft:
    if rng.random() < 0.5:
        return _l5_density(rng)
    return _l5_scale(rng)


def _l5_density(rng: random.Random) -> Draft:
    def pick(r):
        area = r.randint(25, 900)
        pop = r.randint(12, 900) * 1000 + r.choice((0, 0, 500, 250))
        dens = Fraction(pop, area)
        if dens < 5 or dens > 20000 or near_half(dens, dp=0):
            return None
        return pop, area, dens
    pop, area, dens = retry(pick, rng)
    place = rng.choice(REGIONS)
    text = (f"{place} has a population of {group(pop)} and an area of {area} km². "
            f"Work out its population density in people per km². Give your answer to the nearest whole number.")
    shown = fmt_dp(dens, 0)
    sol = (f"Population density = population ÷ area = {group(pop)} ÷ {area} = {_approx(dens)} "
           f"= {shown} people/km² (nearest whole number)")
    ans = num_answer(dens, f"{shown} people/km²", dp=0)
    ms = []
    inv = Fraction(area, pop)
    if inv >= Fraction(1, 1000):
        ms.append(Mistake(Answer(kind="number", display=fmt_dp(inv, 3), value=float(inv), dp=3),
                          "Divide the population by the area, not the area by the population"))
    return _q(text, ans, sol, "Population density = number of people ÷ area", ms)


def _l5_scale(rng: random.Random) -> Draft:
    scale = rng.choice((25000, 50000))
    tenths = rng.randint(12, 150)          # map distance 1.2 cm .. 15.0 cm
    if scale == 25000 and tenths % 2:
        tenths += 1                        # keeps the answer to at most 2 d.p. (cm ÷ 4)
    cm = Fraction(tenths, 10)
    km = cm * scale / 100000
    per_cm = Fraction(scale, 100000)
    scale_txt = "1:25 000" if scale == 25000 else "1:50 000"
    what = rng.choice(("two villages", "two farms", "a church and a school", "two road junctions",
                       "a bridge and a waterfall", "two campsites"))
    text = (f"On a {scale_txt} map, {what} are {fmt_dp(cm, 1)} cm apart. "
            f"What is the real distance between them in km?")
    sol = (f"On a {scale_txt} map, 1 cm represents {group(scale)} cm = {fmt_num(per_cm)} km, "
           f"so {fmt_dp(cm, 1)} × {fmt_num(per_cm)} = {fmt_num(km)} km")
    ans = num_answer(km, f"{fmt_num(km)} km")
    ms = [
        Mistake(Answer(kind="number", display=f"{fmt_num(cm * scale)} km", value=float(cm * scale)),
                "That's the distance in centimetres — divide by 100,000 to change it into kilometres"),
        Mistake(Answer(kind="number", display=f"{fmt_num(cm * scale / 1000)} km", value=float(cm * scale / 1000)),
                "There are 100,000 cm in 1 km, not 1,000"),
        Mistake(Answer(kind="number", display=f"{fmt_num(cm)} km", value=float(cm)),
                f"On a {scale_txt} map, 1 cm does not represent 1 km — it represents {group(scale)} cm"),
    ]
    return _q(text, ans, sol,
              f"Multiply the map distance by {group(scale)} to get centimetres, then change centimetres into kilometres",
              ms)


# ================================================================ skill

def _skill(name: str, title: str, aliases: tuple[str, ...],
           levels: tuple[Callable[[random.Random], Draft], ...], fallback: str) -> Skill:
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


SKILLS_STATS = _skill(
    "skills_stats", "Geographical skills",
    ("geographical skills", "map scale", "population density", "statistics", "percentage change",
     "interquartile range", "mean median mode", "range", "map skills", "fieldwork data"),
    (_l1, _l2, _l3, _l4, _l5),
    "Write down what the question gives you, then use the method step by step")


# ================================================================ subject

_ROWS = (
    (("hazards", "Natural hazards", ("geography.hazards",)),
     ("landscapes", "Rivers & coasts", ("geography.landscapes",))),
    (("urban", "Cities & development", ("geography.urban",)),
     ("skills", "Geographical skills", ("geography.skills_stats",))),
)


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"{SUBJECT_ID}.y{y}.{slug}", label=label, skills=skills, level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Geography", order=32, years={10: _year(10), 11: _year(11)})


def register(reg) -> None:
    """Register Geography: the bank skills from packs/geography.json plus the generated skill."""
    bank_skills = load_pack(SUBJECT_ID, SUBJECT_ID)
    reg.register(make_subject(), list(bank_skills) + [SKILLS_STATS])
