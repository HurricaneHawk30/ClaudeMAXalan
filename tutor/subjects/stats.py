"""GCSE Statistics, Years 10–11 (docs/ARCHITECTURE_V2.md section 5.1).

The module is called ``stats`` so that it does not shadow the standard-library
``statistics`` module; the subject id is still ``statistics``.  Six generated
skills live here; the two bank skills (data collection, diagrams & correlation)
come from ``packs/statistics.json``.

Every generator is pure: ``generate(level, seed)`` uses only ``random.Random(seed)``.
Answers are computed exactly (Fractions) from the numbers printed in the question.
Quartiles use data sets of size 4k + 3, where the (n + 1)/4 rule and the
"median of each half" method give the same value.
"""
from __future__ import annotations

import math
import random
from dataclasses import replace
from fractions import Fraction
from typing import Callable

from ..content import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, load_pack
from ..content.fmt import (
    build, check_level, fmt_dp, fmt_num, frac_str, is_whole, near_half, num_answer, num_mistake, retry,
)

SUBJECT_ID = "statistics"
Draft = dict


# ================================================================ helpers

def _q(text: str, answer: Answer, solution: str, hint: str, mistakes=()) -> Draft:
    return {"text": text, "answer": answer, "solution": solution, "hint": hint, "mistakes": list(mistakes)}


def _exact(v) -> Answer:
    """An exact number answer (whole number or a short terminating decimal)."""
    return num_answer(v, fmt_num(v))


def _exact_mis(v, fb: str, unit: str = "") -> Mistake | None:
    if v is None:
        return None
    v = Fraction(v)
    d = v.denominator
    while d % 2 == 0:
        d //= 2
    while d % 5 == 0:
        d //= 5
    if d != 1:
        return None            # not a terminating decimal: a student could not type it exactly
    return num_mistake(v, unit, fb)


def _dp(v, dp: int, unit: str = "") -> Answer:
    shown = fmt_dp(v, dp)
    return num_answer(v, f"{shown} {unit}".strip() if unit and unit != "%" else shown + (unit if unit == "%" else ""), dp=dp)


def _dp_mis(v, dp: int, fb: str, unit: str = "") -> Mistake | None:
    if v is None:
        return None
    return num_mistake(v, unit, fb, dp=dp)


def _frac(f: Fraction, simplest: bool = False, shown: str | None = None) -> Answer:
    return Answer(kind="fraction", display=shown or frac_str(f), value=frac_str(f),
                  form="simplest" if simplest else "any")


def _frac_mis(f: Fraction | None, fb: str, shown: str | None = None) -> Mistake | None:
    if f is None:
        return None
    return Mistake(Answer(kind="fraction", display=shown or frac_str(f), value=frac_str(f)), fb)


def _dec(f: Fraction) -> str:
    """A terminating fraction as a decimal: 3/10 -> '0.3'."""
    return fmt_num(f)


def _lst(vals) -> str:
    return ", ".join(fmt_num(v) for v in vals)


def _terminating(f: Fraction, max_dp: int = 2) -> bool:
    return (f * 10 ** max_dp).denominator == 1


def _pn(n) -> str:
    return f"({fmt_num(n)})" if n < 0 else fmt_num(n)


# ============================================================ stratified sampling

_STRATA = (
    ("students", "Year 10", "Year 11", "Year 10 students", "Year 11 students"),
    ("members", "juniors", "seniors", "juniors", "seniors"),
    ("staff", "full-time", "part-time", "full-time staff", "part-time staff"),
    ("workers", "day shift", "night shift", "day-shift workers", "night-shift workers"),
    ("members", "boys", "girls", "boys", "girls"),
)
_PLACES = {"students": "A school", "members": "A club", "staff": "A company", "workers": "A factory"}


def _st_1(rng: random.Random) -> Draft:
    """Fraction of the population in one stratum (fraction, simplest)."""
    who, a_lab, b_lab, a_long, b_long = rng.choice(_STRATA)

    def pick(r):
        na, nb = 10 * r.randint(4, 60), 10 * r.randint(4, 60)
        return (na, nb) if na != nb else None
    na, nb = retry(pick, rng)
    f = Fraction(na, na + nb)
    ms = [_frac_mis(Fraction(na, nb), f"Divide by the total ({na} + {nb} = {na + nb}), not by the number of {b_long}")]
    return _q(f"{_PLACES[who]} has {na} {a_long} and {nb} {b_long}. What fraction of the {who} are {a_long}? "
              "Give your answer as a fraction in its simplest form.",
              _frac(f, simplest=True), f"Total = {na} + {nb} = {na + nb}, so the fraction is {na}/{na + nb} = {frac_str(f)}",
              f"Find the total number of {who} first", ms)


def _stratum_pick(rng: random.Random, exact: bool):
    def pick(r):
        na, nb = r.randint(8, 90) * 10, r.randint(8, 90) * 10
        if exact:
            v = r.choice([4, 5, 8, 10, 20, 25])
            u = r.randint(1, v - 1)
            t = r.randint(5, 40)
            na, nb = u * t, (v - u) * t
            s = v * r.randint(2, 12)
            if na < 40 or nb < 40 or not 20 <= s <= 120 or s > na + nb:
                return None
        else:
            s = r.choice([20, 25, 30, 40, 50, 60, 80, 100])
        N = na + nb
        share = Fraction(na * s, N)
        if exact and share.denominator != 1:
            return None
        if not exact and (share.denominator == 1 or near_half(share, 0)):
            return None
        return na, nb, s, share
    return retry(pick, rng)


def _st_2(rng: random.Random) -> Draft:
    """Size of one stratum's sample (exact)."""
    who, a_lab, b_lab, a_long, b_long = rng.choice(_STRATA)
    na, nb, s, share = _stratum_pick(rng, True)
    N = na + nb
    ms = [_exact_mis(Fraction(nb * s, N), f"That's the number of {b_long} — use the {a_long} in the numerator"),
          _exact_mis(Fraction(s, 2), "A stratified sample is in proportion to the size of each group, not split equally")]
    return _q(f"{_PLACES[who]} has {na} {a_long} and {nb} {b_long}. A stratified sample of {s} {who} is taken. "
              f"How many {a_long} should be in the sample?",
              _exact(share), f"{na} ÷ {N} × {s} = {fmt_num(share)}",
              f"Work out the fraction of all the {who} who are {a_long}, then multiply by the sample size", ms)


def _st_3(rng: random.Random) -> Draft:
    """One stratum's sample, rounded to the nearest whole number."""
    intro, groups, who = rng.choice((
        ("The students in a school club are grouped by year", ("Year 9", "Year 10", "Year 11"), "students"),
        ("The members of a gym are grouped by age", ("under 18", "18 to 60", "over 60"), "members"),
        ("The members of a climbing club are grouped by level", ("beginner", "intermediate", "advanced"), "members"),
    ))

    def pick(r):
        ns = [r.randint(6, 60) * 5 for _ in range(3)]
        s = r.choice([30, 40, 50, 60, 80])
        i = r.randrange(3)
        share = Fraction(ns[i] * s, sum(ns))
        if share.denominator == 1 or near_half(share, 0) or len(set(ns)) < 3:
            return None
        return ns, s, i, share
    ns, s, i, share = retry(pick, rng)
    N = sum(ns)
    name = groups[i]
    table = "; ".join(f"{g[:1].upper() + g[1:]}: {n}" for g, n in zip(groups, ns))
    ms = [_dp_mis(Fraction(s, 3), 0, "A stratified sample is in proportion to the size of each group, not split equally"),
          _dp_mis(Fraction(ns[i] * s, N - ns[i]), 0, f"Divide by the total of all three groups ({N})")]
    return _q(f"{intro}. {table}. A stratified sample of {s} {who} is taken. How many should be from the {name} group? "
              "Give your answer to the nearest whole number.",
              num_answer(share, fmt_dp(share, 0), dp=0),
              f"Total = {N}. {ns[i]} ÷ {N} × {s} = {float(share):.2f}, which rounds to {fmt_dp(share, 0)}",
              "Find the total of all the groups first, then use (group size ÷ total) × sample size", ms)


def _st_4(rng: random.Random) -> Draft:
    """Both strata's sample sizes (ordered set)."""
    who, a_lab, b_lab, a_long, b_long = rng.choice(_STRATA)

    def pick(r):
        na, nb = r.randint(8, 90) * 10, r.randint(8, 90) * 10
        s = r.choice([20, 25, 30, 40, 50, 60])
        sa = Fraction(na * s, na + nb)
        if na == nb or near_half(sa, 0):
            return None
        return na, nb, s, sa
    na, nb, s, sa = retry(pick, rng)
    N = na + nb
    sb = s - sa
    ra, rb = fmt_dp(sa, 0), fmt_dp(sb, 0)
    ans = Answer(kind="set", display=f"{ra} and {rb}", value=[frac_str(sa), frac_str(sb)], dp=0, ordered=True)
    ms = []
    if ra != rb:
        ms.append(Mistake(Answer(kind="set", display=f"{rb} and {ra}", value=[frac_str(sb), frac_str(sa)], dp=0,
                                 ordered=True), f"Give the numbers in the order asked: {a_long} first, then {b_long}"))
    half = Fraction(s, 2)
    ms.append(Mistake(Answer(kind="set", display=f"{fmt_num(half)} and {fmt_num(half)}",
                             value=[frac_str(half), frac_str(half)], dp=0, ordered=True),
                      "A stratified sample is in proportion to the size of each group, not split equally"))
    rounding = "" if sa.denominator == 1 else " Round each answer to the nearest whole number."
    sol_a = fmt_num(sa) if sa.denominator == 1 else f"{float(sa):.2f}"
    sol_b = fmt_num(sb) if sb.denominator == 1 else f"{float(sb):.2f}"
    return _q(f"{_PLACES[who]} has {na} {a_long} and {nb} {b_long}. A stratified sample of {s} {who} is taken. "
              f"How many {a_long} and how many {b_long} should be in the sample?{rounding} "
              f"Give the two numbers in the order {a_long}, {b_long}.",
              ans, f"{a_long.capitalize()}: {na} ÷ {N} × {s} = {sol_a}; {b_long}: {nb} ÷ {N} × {s} = {sol_b}. "
                   f"So {ra} and {rb}",
              "Each group's share of the sample is (group size ÷ total) × sample size", ms)


_CAPTURE = (("fish", "lake"), ("rabbits", "field"), ("newts", "pond"), ("ladybirds", "garden"),
            ("butterflies", "nature reserve"), ("snails", "wood"))


def _st_5(rng: random.Random) -> Draft:
    """Capture–recapture (Petersen) estimate."""
    animal, place = rng.choice(_CAPTURE)

    def pick(r):
        m = r.randint(15, 120)
        rec = r.randint(3, 20)
        c = r.randint(rec + 10, 160)
        if (m * c) % rec or c <= rec or m <= rec:
            return None
        return m, c, rec
    m, c, rec = retry(pick, rng)
    n = m * c // rec
    if rng.random() < 0.7:
        ms = [_exact_mis(Fraction(m * rec, c), "Use N = (number marked × size of second sample) ÷ number of marked in the second sample"),
              _exact_mis(m * c, f"Divide by the {rec} marked {animal} found in the second sample")]
        return _q(f"Ecologists catch {m} {animal} in a {place}, mark them and release them. Later they catch {c} {animal}, "
                  f"and {rec} of these are marked. Use the capture–recapture (Petersen) method to estimate "
                  f"the number of {animal} in the {place}.",
                  _exact(n), f"N = ({m} × {c}) ÷ {rec} = {m * c} ÷ {rec} = {n}",
                  "Assume the fraction marked in the second sample matches the fraction marked in the whole population",
                  ms)
    ms = [_exact_mis(Fraction(n * c, m), "The fraction marked in the second sample should equal the fraction marked overall: marked ÷ total"),
          _exact_mis(Fraction(m * n, c), "Rearrange N = (M × C) ÷ R to make R the subject")]
    return _q(f"There are about {n} {animal} in a {place}. Ecologists catch {m} of them, mark them and release them. "
              f"Later they catch {c} {animal}. Using the capture–recapture (Petersen) method, how many of these "
              "would you expect to be marked?",
              _exact(rec), f"R = (M × C) ÷ N = ({m} × {c}) ÷ {n} = {rec}",
              f"The fraction of marked {animal} in the second sample should be the same as {m} out of {n}", ms)


# ======================================================================== averages

def _av_1(rng: random.Random) -> Draft:
    """Mean of a list."""
    ctx = rng.choice((("goals scored by a team in", "matches"), ("marks scored by", "students in a quiz"),
                      ("hours of sleep recorded on", "nights"), ("books read by", "students in a month")))

    def pick(r):
        n = r.randint(5, 8)
        mean = r.randint(3, 18)
        vals = [r.randint(max(0, mean - 8), mean + 8) for _ in range(n - 1)]
        last = n * mean - sum(vals)
        if not 0 <= last <= mean + 12:
            return None
        vals.append(last)
        r.shuffle(vals)
        return vals, mean
    vals, mean = retry(pick, rng)
    n = len(vals)
    srt = sorted(vals)
    med = Fraction(srt[(n - 1) // 2] + srt[n // 2], 2)
    ms = [_exact_mis(Fraction(sum(vals), n - 1), f"Divide by the number of values, which is {n}"),
          _exact_mis(med, "That's the median — the mean is the total divided by the number of values")]
    return _q(f"Here are the {ctx[0]} {n} {ctx[1]}: {_lst(vals)}. Work out the mean.",
              _exact(mean), f"Total = {sum(vals)}, and there are {n} values, so the mean = {sum(vals)} ÷ {n} = {mean}",
              "Add up all the values, then divide by how many values there are", ms)


def _av_2(rng: random.Random) -> Draft:
    """Median of an even number of values."""
    def pick(r):
        n = r.choice([6, 8, 10])
        vals = [r.randint(1, 40) for _ in range(n)]
        srt = sorted(vals)
        a, b = srt[n // 2 - 1], srt[n // 2]
        if a == b or vals == srt:
            return None
        ua, ub = vals[n // 2 - 1], vals[n // 2]
        return vals, srt, a, b, ua, ub
    vals, srt, a, b, ua, ub = retry(pick, rng)
    n = len(vals)
    med = Fraction(a + b, 2)
    ms = [_exact_mis(Fraction(ua + ub, 2), "Put the values in order first, then find the middle"),
          _exact_mis(a, f"With {n} values there are two middle values: the median is halfway between {a} and {b}"),
          _exact_mis(b, f"With {n} values there are two middle values: the median is halfway between {a} and {b}"),
          _exact_mis(Fraction(sum(vals), n), "That's the mean — the median is the middle value when the data is in order")]
    return _q(f"Find the median of these {n} numbers: {_lst(vals)}.",
              _exact(med), f"In order: {_lst(srt)}. The middle two values are {a} and {b}, so the median = ({a} + {b}) ÷ 2 = {fmt_num(med)}",
              "Write the numbers in order first; with an even number of values the median is halfway between the middle two", ms)


_FREQ_CTX = (("pets owned by", "students", "Number of pets", "pets per student"),
             ("goals scored by a team in", "matches", "Goals", "goals per match"),
             ("people living in", "houses", "Number of people", "people per house"),
             ("siblings of", "students", "Number of siblings", "siblings per student"))


def _av_3(rng: random.Random) -> Draft:
    """Mean from a frequency table (1 d.p.)."""
    what, who, head, per = rng.choice(_FREQ_CTX)
    start = 1 if head == "Number of people" else 0

    def pick(r):
        xs = list(range(start, start + r.choice([5, 6])))
        fs = [r.randint(1, 15) for _ in xs]
        mean = Fraction(sum(x * f for x, f in zip(xs, fs)), sum(fs))
        return None if near_half(mean, 1) else (xs, fs, mean)
    xs, fs, mean = retry(pick, rng)
    tot_f = sum(fs)
    tot_fx = sum(x * f for x, f in zip(xs, fs))
    ms = [_dp_mis(Fraction(tot_fx, len(xs)), 1, f"Divide by the total frequency ({tot_f}), not by the number of rows"),
          _dp_mis(Fraction(sum(xs), len(xs)), 1, "Multiply each value by its frequency before you add them up"),
          _dp_mis(Fraction(tot_f, len(xs)), 1, "Work out frequency × value for each row, then divide the total by the total frequency")]
    return _q(f"The table shows the number of {what} {tot_f} {who}.\n{head}: {_lst(xs)}\nFrequency: {_lst(fs)}\n"
              f"Work out the mean number of {per}. Give your answer to 1 decimal place.",
              _dp(mean, 1),
              f"Total of frequency × value = {tot_fx}; total frequency = {tot_f}. Mean = {tot_fx} ÷ {tot_f} = {float(mean):.3f}… = {fmt_dp(mean, 1)}",
              "Multiply each value by its frequency, add these up, then divide by the total frequency", ms)


_GROUP_CTX = (("times, t minutes, that", "people waited at a bus stop", "t", "minutes", "waiting time"),
              ("heights, h cm, of", "plants", "h", "cm", "height"),
              ("masses, m kg, of", "parcels", "m", "kg", "mass"),
              ("journey times, t minutes, of", "students", "t", "minutes", "journey time"))


def _av_4(rng: random.Random) -> Draft:
    """Estimated mean from grouped data (1 d.p.)."""
    what, who, var, unit, name = rng.choice(_GROUP_CTX)

    def pick(r):
        w = r.choice([2, 4, 5, 10, 20])
        lo0 = r.choice([0, 0, w])
        k = r.choice([4, 5])
        fs = [r.randint(2, 18) for _ in range(k)]
        mids = [Fraction(lo0 + i * w) + Fraction(w, 2) for i in range(k)]
        est = sum(m * f for m, f in zip(mids, fs)) / sum(fs)
        return None if near_half(est, 1) else (w, lo0, k, fs, mids, est)
    w, lo0, k, fs, mids, est = retry(pick, rng)
    classes = [f"{lo0 + i * w} < {var} ≤ {lo0 + (i + 1) * w}" for i in range(k)]
    tot_f = sum(fs)
    tot = sum(m * f for m, f in zip(mids, fs))
    ups = sum((lo0 + (i + 1) * w) * f for i, f in enumerate(fs))
    lows = sum((lo0 + i * w) * f for i, f in enumerate(fs))
    ms = [_dp_mis(Fraction(ups, tot_f), 1, "Use the midpoint of each class, not the upper bound"),
          _dp_mis(Fraction(lows, tot_f), 1, "Use the midpoint of each class, not the lower bound"),
          _dp_mis(tot / k, 1, f"Divide by the total frequency ({tot_f}), not by the number of classes")]
    return _q(f"The table shows the {what} {tot_f} {who}.\n{name.capitalize()}: {', '.join(classes)}\n"
              f"Frequency: {_lst(fs)}\nWork out an estimate of the mean {name}. Give your answer to 1 decimal place.",
              _dp(est, 1, unit),
              f"Midpoints: {_lst(mids)}. Total of frequency × midpoint = {fmt_num(tot)}; total frequency = {tot_f}. "
              f"Estimate = {fmt_num(tot)} ÷ {tot_f} = {fmt_dp(est, 1)} {unit}",
              "Use the midpoint of each class as its value, multiply by the frequency, add, then divide by the total frequency",
              ms)


def _av_5(rng: random.Random) -> Draft:
    """Missing value, a value added, or a combined mean."""
    v = rng.random()
    if v < 0.35:
        def pick(r):
            n = r.randint(5, 8)
            mean = r.randint(5, 20)
            known = [r.randint(max(1, mean - 9), mean + 9) for _ in range(n - 1)]
            miss = n * mean - sum(known)
            return (n, mean, known, miss) if 1 <= miss <= 40 else None
        n, mean, known, miss = retry(pick, rng)
        ms = [_exact_mis(mean * (n - 1) - sum(known), f"There are {n} numbers, so the total is {n} × {mean}"),
              _exact_mis(Fraction(sum(known), n - 1), "That's the mean of the other numbers — use total = mean × number of values")]
        return _q(f"The mean of {n} numbers is {mean}. {n - 1} of the numbers are {_lst(known)}. Work out the other number.",
                  _exact(miss), f"Total of all {n} = {n} × {mean} = {n * mean}. Total of the {n - 1} given = {sum(known)}. "
                                f"Missing number = {n * mean} - {sum(known)} = {miss}",
                  "Use total = mean × number of values", ms)
    if v < 0.6:
        def pick(r):
            n = r.randint(4, 9)
            m1 = r.randint(5, 20)
            m2 = m1 + r.choice([-2, -1, 1, 2, 3])
            new = (n + 1) * m2 - n * m1
            return (n, m1, m2, new) if 0 <= new <= 60 else None
        n, m1, m2, new = retry(pick, rng)
        ms = [_exact_mis(m2 - m1, "Compare totals, not means: total after - total before"),
              _exact_mis(n * m2 - n * m1, f"After adding a number there are {n + 1} values, so the new total is {n + 1} × {m2}")]
        return _q(f"The mean of {n} numbers is {m1}. One more number is added and the mean of all {n + 1} numbers is now {m2}. "
                  "Work out the number that was added.",
                  _exact(new), f"Total before = {n} × {m1} = {n * m1}. Total after = {n + 1} × {m2} = {(n + 1) * m2}. "
                               f"Number added = {(n + 1) * m2} - {n * m1} = {new}",
                  "Work out the total before and the total after", ms)

    def pick(r):
        n1, n2 = r.randint(10, 35), r.randint(10, 35)
        m1, m2 = r.randint(40, 85), r.randint(40, 85)
        cm = Fraction(n1 * m1 + n2 * m2, n1 + n2)
        if n1 == n2 or m1 == m2 or near_half(cm, 1):
            return None
        return n1, n2, m1, m2, cm
    n1, n2, m1, m2, cm = retry(pick, rng)
    ms = [_dp_mis(Fraction(m1 + m2, 2), 1, "The groups are different sizes, so weight each mean by the number of students")]
    return _q(f"In a test, {n1} students in class A had a mean mark of {m1}, and {n2} students in class B had a mean mark of {m2}. "
              "Work out the mean mark of all the students. Give your answer to 1 decimal place.",
              _dp(cm, 1), f"Total marks = {n1} × {m1} + {n2} × {m2} = {n1 * m1 + n2 * m2}. "
                          f"Mean = {n1 * m1 + n2 * m2} ÷ {n1 + n2} = {fmt_dp(cm, 1)}",
              "Work out the total marks for each class (mean × number of students)", ms)


# ============================================================================ spread

def _sp_1(rng: random.Random) -> Draft:
    """Range."""
    if rng.random() < 0.4:
        def pick(r):
            vals = [r.randint(-8, 15) for _ in range(r.randint(6, 9))]
            return vals if min(vals) < 0 < max(vals) and vals[0] != min(vals) else None
        vals = retry(pick, rng)
        ctx = f"Here are the midday temperatures, in °C, in a town on {len(vals)} days: {_lst(vals)}."
        u = "°C"
    else:
        def pick(r):
            vals = [r.randint(10, 95) for _ in range(r.randint(6, 9))]
            return vals if vals[0] != min(vals) or vals[-1] != max(vals) else None
        vals = retry(pick, rng)
        ctx = f"Here are the marks of {len(vals)} students in a test: {_lst(vals)}."
        u = ""
    hi, lo = max(vals), min(vals)
    rg = hi - lo
    ms = [_exact_mis(vals[-1] - vals[0], "Use the largest and smallest values, not the last and first in the list")]
    if lo < 0:
        ms.append(_exact_mis(hi + lo, f"Subtracting a negative number adds: {hi} - ({lo}) = {hi} + {-lo}"))
    disp = f"{rg}{u}" if u else str(rg)
    return _q(f"{ctx} Work out the range.", num_answer(rg, disp),
              f"Range = largest - smallest = {hi} - {_pn(lo)} = {rg}{u}",
              "Range = largest value - smallest value", ms)


def _quartile_data(rng: random.Random):
    def pick(r):
        n = r.choice([7, 11, 15])
        vals = r.sample(range(5, 80), n)
        return vals if vals != sorted(vals) else None
    vals = retry(pick, rng)
    srt = sorted(vals)
    n = len(vals)
    q = (n + 1) // 4
    return vals, srt, n, srt[q - 1], srt[(n + 1) // 2 - 1], srt[3 * q - 1], q


def _sp_2(rng: random.Random) -> Draft:
    """Lower or upper quartile."""
    vals, srt, n, lq, med, uq, q = _quartile_data(rng)
    upper = rng.random() < 0.5
    want, other = (uq, lq) if upper else (lq, uq)
    pos = 3 * q if upper else q
    name = "upper" if upper else "lower"
    ms = [_exact_mis(med, "That's the median — the quartiles are a quarter and three quarters of the way through the ordered data"),
          _exact_mis(other, f"That's the {'lower' if upper else 'upper'} quartile"),
          _exact_mis(vals[pos - 1], "Put the data in order before counting along")]
    return _q(f"Here are {n} numbers: {_lst(vals)}. Find the {name} quartile.",
              _exact(want), f"In order: {_lst(srt)}. The {name} quartile is the "
                            f"{'3(n + 1) ÷ 4' if upper else '(n + 1) ÷ 4'} = {pos}{_th(pos)} value, which is {want}",
              f"Put the numbers in order; the {name} quartile is the {'3(n + 1) ÷ 4' if upper else '(n + 1) ÷ 4'}th value", ms)


def _th(n: int) -> str:
    return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _sp_3(rng: random.Random) -> Draft:
    """Interquartile range."""
    vals, srt, n, lq, med, uq, q = _quartile_data(rng)
    iqr = uq - lq
    ms = [_exact_mis(srt[-1] - srt[0], "That's the range — the IQR uses the quartiles: upper quartile - lower quartile"),
          _exact_mis(uq - med, "IQR = upper quartile - lower quartile, not upper quartile - median")]
    return _q(f"Here are {n} numbers: {_lst(vals)}. Work out the interquartile range.",
              _exact(iqr), f"In order: {_lst(srt)}. Lower quartile = {q}{_th(q)} value = {lq}; upper quartile = "
                           f"{3 * q}{_th(3 * q)} value = {uq}. IQR = {uq} - {lq} = {iqr}",
              "Order the data, find the lower and upper quartiles, then subtract", ms)


def _sp_4(rng: random.Random) -> Draft:
    """Outlier limits: LQ - 1.5 × IQR or UQ + 1.5 × IQR."""
    def pick(r):
        lq = r.randint(10, 60)
        iqr = r.choice(list(range(4, 41, 2)))
        return lq, lq + iqr, iqr
    lq, uq, iqr = retry(pick, rng)
    upper = rng.random() < 0.6
    lim = Fraction(uq) + Fraction(3, 2) * iqr if upper else Fraction(lq) - Fraction(3, 2) * iqr
    name = "upper" if upper else "lower"
    ms = [_exact_mis(Fraction(3, 2) * iqr, f"That's 1.5 × IQR — now {'add it to the upper' if upper else 'subtract it from the lower'} quartile"),
          _exact_mis(uq + iqr if upper else lq - iqr, "Multiply the IQR by 1.5 first"),
          _exact_mis(Fraction(lq) + Fraction(3, 2) * iqr if upper else Fraction(uq) - Fraction(3, 2) * iqr,
                     f"The {name} limit uses the {name} quartile")]
    return _q(f"A data set has lower quartile {lq} and upper quartile {uq}. An outlier is a value more than 1.5 × IQR "
              f"below the lower quartile or more than 1.5 × IQR above the upper quartile. Work out the {name} limit for outliers: "
              f"values {'above' if upper else 'below'} this limit are outliers.",
              _exact(lim), f"IQR = {uq} - {lq} = {iqr}; 1.5 × {iqr} = {fmt_num(Fraction(3, 2) * iqr)}. "
                           f"{name.capitalize()} limit = {uq if upper else lq} {'+' if upper else '-'} "
                           f"{fmt_num(Fraction(3, 2) * iqr)} = {fmt_num(lim)}",
              "Work out the IQR first, then 1.5 × IQR", ms)


_SD_FORMULA = "standard deviation = √(Σx² ÷ n - mean²)"


def _sp_5(rng: random.Random) -> Draft:
    """Standard deviation to 2 d.p. (formula given)."""
    if rng.random() < 0.55:
        def pick(r):
            n = r.choice([5, 6])
            vals = [r.randint(1, 20) for _ in range(n)]
            mean = Fraction(sum(vals), n)
            var = Fraction(sum(v * v for v in vals), n) - mean * mean
            sd = math.sqrt(var)
            if var == 0 or near_half(sd, 2) or mean.denominator not in (1, 2, 5):
                return None
            return vals, n, mean, var, sd
        vals, n, mean, var, sd = retry(pick, rng)
        sx2 = sum(v * v for v in vals)
        data = f"Here are {n} numbers: {_lst(vals)}."
        var_txt = fmt_num(var) if _terminating(var, 4) else fmt_dp(var, 4) + "…"
        sol = (f"Σx = {sum(vals)}, so the mean = {fmt_num(mean)}. Σx² = {sx2}. "
               f"SD = √({sx2} ÷ {n} - {fmt_num(mean)}²) = √{var_txt} = {fmt_dp(sd, 2)}")
        samp = math.sqrt(float(var) * n / (n - 1))
    else:
        def pick(r):
            n = r.choice([10, 20, 25, 40, 50])
            mean = Fraction(r.randint(30, 300), 10)
            var = Fraction(r.randint(4, 400), 4)
            sx = mean * n
            sx2 = (var + mean * mean) * n
            if sx.denominator != 1 or sx2.denominator != 1:
                return None
            sd = math.sqrt(var)
            if near_half(sd, 2):
                return None
            return n, mean, var, sd, int(sx), int(sx2)
        n, mean, var, sd, sx, sx2 = retry(pick, rng)
        data = f"For a set of {n} values, Σx = {sx} and Σx² = {sx2}."
        sol = (f"Mean = {sx} ÷ {n} = {fmt_num(mean)}. SD = √({sx2} ÷ {n} - {fmt_num(mean)}²) = "
               f"√{fmt_num(var)} = {fmt_dp(sd, 2)}")
        samp = math.sqrt(float(var) * n / (n - 1))
    ms = [_dp_mis(var, 2, "That's the variance — take the square root to get the standard deviation"),
          _dp_mis(samp, 2, "Use the formula given: divide by n, not n - 1"),
          _dp_mis(math.sqrt(float(var + mean * mean - mean)) if var + mean * mean > mean else None, 2,
                  "Square the mean before you subtract it")]
    return _q(f"{data} Use the formula {_SD_FORMULA} to work out the standard deviation. Give your answer to 2 decimal places.",
              _dp(sd, 2), sol, "Work out the mean and Σx² first, then put them into the formula", ms)


# ========================================================================== spearman

_RS_FORMULA = "rs = 1 - 6Σd² ÷ (n(n² - 1))"
_PAIRS = (   # (x name, x range, y name, y range, step, sign of the expected correlation, the cases)
    ("hours of revision", (1, 30), "test mark", (20, 99), 1, 1, "students"),
    ("height in cm", (140, 190), "arm span in cm", (135, 195), 1, 1, "people"),
    ("temperature in °C", (10, 32), "ice creams sold", (15, 95), 1, 1, "days"),
    ("price in pence", (40, 250), "number sold", (10, 90), 1, -1, "products"),
    ("age in years", (1, 15), "value in £", (1500, 18000), 100, -1, "cars"),
    ("hours of sunshine", (1, 12), "visitors to a beach", (50, 900), 10, 1, "days"),
)


def _sm_1(rng: random.Random) -> Draft:
    """Rank a value."""
    def pick(r):
        n = r.randint(5, 8)
        vals = r.sample(range(10, 99), n)
        return vals
    vals = retry(pick, rng)
    n = len(vals)
    v = rng.choice(vals)
    largest = rng.random() < 0.5
    order = sorted(vals, reverse=largest)
    rank = order.index(v) + 1
    ms = [_exact_mis(n + 1 - rank, f"Rank 1 is the {'largest' if largest else 'smallest'} value here"),
          _exact_mis(vals.index(v) + 1, "Put the values in order first — the rank is the position in the ordered list")]
    return _q(f"Rank these {n} values, giving the {'largest' if largest else 'smallest'} value rank 1: {_lst(vals)}. "
              f"What is the rank of {v}?",
              _exact(rank), f"In order ({'largest' if largest else 'smallest'} first): {_lst(order)}. {v} is in position {rank}",
              f"Write the values in order, starting with the {'largest' if largest else 'smallest'}", ms)


def _corr_ranks(r: random.Random, n: int, sign: int = 0) -> list[int]:
    """A rank permutation of 1..n that is loosely correlated with 1..n (sign -1: with n..1)."""
    base = list(range(1, n + 1))
    if sign < 0 or (sign == 0 and r.random() < 0.3):
        base.reverse()
    for _ in range(r.randint(1, n)):
        i = r.randrange(n - 1)
        base[i], base[i + 1] = base[i + 1], base[i]
    return base


def _sm_2(rng: random.Random) -> Draft:
    """Σd² from two sets of ranks."""
    n = rng.choice([5, 6])
    names = "PQRSTU"[:n]
    r1 = rng.sample(range(1, n + 1), n)
    r2 = _corr_ranks(rng, n)
    r2 = [r2[r1[i] - 1] for i in range(n)]          # judge 2 roughly agrees with judge 1
    ds = [a - b for a, b in zip(r1, r2)]
    sd2 = sum(d * d for d in ds)
    if sd2 == 0:
        r2[0], r2[1] = r2[1], r2[0]
        ds = [a - b for a, b in zip(r1, r2)]
        sd2 = sum(d * d for d in ds)
    ms = [_exact_mis(sum(abs(d) for d in ds), "Square each difference before adding them up")]
    return _q(f"Two judges ranked {n} contestants {', '.join(names[:-1])} and {names[-1]}.\n"
              f"Judge 1: {', '.join(f'{c} {k}' for c, k in zip(names, r1))}\n"
              f"Judge 2: {', '.join(f'{c} {k}' for c, k in zip(names, r2))}\n"
              "Work out Σd², where d is the difference between the two ranks for each contestant.",
              _exact(sd2), f"d = {', '.join(fmt_num(d) for d in ds)}; d² = {', '.join(str(d * d) for d in ds)}; Σd² = {sd2}",
              "For each contestant, subtract the two ranks, square the answer, then add them all up", ms)


def _rs(n: int, sd2: int) -> Fraction:
    return 1 - Fraction(6 * sd2, n * (n * n - 1))


def _sm_3(rng: random.Random) -> Draft:
    """rs from Σd² and n (2 d.p.)."""
    def pick(r):
        n = r.randint(6, 12)
        mx = n * (n * n - 1) // 3
        sd2 = 2 * r.randint(1, mx // 2 - 1)
        rs = _rs(n, sd2)
        return None if near_half(rs, 2) or rs.denominator == 1 else (n, sd2, rs)
    n, sd2, rs = retry(pick, rng)
    den = n * (n * n - 1)
    ms = [_dp_mis(Fraction(6 * sd2, den), 2, "Don't forget to subtract from 1: rs = 1 - 6Σd² ÷ (n(n² - 1))"),
          _dp_mis(1 - Fraction(6 * sd2, n * n * n), 2, "The bottom of the fraction is n(n² - 1), not n³")]
    return _q(f"For {n} pairs of data, Σd² = {sd2}. Use the formula {_RS_FORMULA} to work out Spearman's rank "
              "correlation coefficient. Give your answer to 2 decimal places.",
              _dp(rs, 2), f"rs = 1 - (6 × {sd2}) ÷ ({n} × {n * n - 1}) = 1 - {6 * sd2} ÷ {den} = {fmt_dp(rs, 2)}",
              f"Put n = {n} and Σd² = {sd2} into the formula; work out n(n² - 1) first", ms)


def _raw_pairs(rng: random.Random, n: int, ctx):
    _, (xlo, xhi), _, (ylo, yhi), step, sign, _ = ctx

    def pick(r):
        xr = list(range(1, n + 1))
        yr = _corr_ranks(r, n, sign)
        xs = sorted(r.sample(range(xlo, xhi + 1), n), reverse=True)            # rank 1 = largest
        ys = sorted(r.sample(range(ylo, yhi + 1, step), n), reverse=True)
        order = r.sample(range(n), n)
        xv = [xs[xr[i] - 1] for i in order]
        yv = [ys[yr[i] - 1] for i in order]
        rx = [xr[i] for i in order]
        ry = [yr[i] for i in order]
        sd2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
        return (xv, yv, rx, ry, sd2) if sd2 > 0 else None
    return retry(pick, rng)


def _sm_raw(rng: random.Random, n: int, dp: int) -> Draft:
    ctx = rng.choice(_PAIRS)
    a, b, cases = ctx[0], ctx[2], ctx[6]

    def pick(r):
        out = _raw_pairs(r, n, ctx)
        rs = _rs(n, out[4])
        return None if near_half(rs, dp) else out + (rs,)
    xv, yv, rx, ry, sd2, rs = retry(pick, rng)
    neg = 1 - Fraction(6 * sum((x - (n + 1 - y)) ** 2 for x, y in zip(rx, ry)), n * (n * n - 1))
    ms = [_dp_mis(neg, dp, "Rank both variables in the same direction (largest = 1 for both, or smallest = 1 for both)"),
          _dp_mis(Fraction(6 * sd2, n * (n * n - 1)), dp, "Don't forget to subtract from 1")]
    dpw = "2 decimal places" if dp == 2 else "3 decimal places"
    return _q(f"The table shows the {a} and the {b} for {n} {cases}.\n{a[:1].upper() + a[1:]}: {_lst(xv)}\n"
              f"{b[:1].upper() + b[1:]}: {_lst(yv)}\nRank each variable, then calculate Spearman's rank correlation coefficient "
              f"using {_RS_FORMULA}. Give your answer to {dpw}.",
              _dp(rs, dp), f"Ranks (largest = 1): {_lst(rx)} and {_lst(ry)}. Σd² = {sd2}. "
                           f"rs = 1 - (6 × {sd2}) ÷ ({n} × {n * n - 1}) = {fmt_dp(rs, dp)}",
              "Rank each row separately (largest = 1), find d for each pair, then Σd²", ms)


def _sm_4(rng: random.Random) -> Draft:
    return _sm_raw(rng, 5, 2)


def _sm_5(rng: random.Random) -> Draft:
    return _sm_raw(rng, 7, 3)


# ======================================================================= probability

_COLOURS = ("red", "blue", "green", "yellow", "white", "black")
_DICE = (("a number greater than 4", {5, 6}), ("a number less than 3", {1, 2}), ("an even number", {2, 4, 6}),
         ("an odd number", {1, 3, 5}), ("a prime number", {2, 3, 5}), ("a multiple of 3", {3, 6}),
         ("a factor of 6", {1, 2, 3, 6}), ("a square number", {1, 4}), ("a number greater than 1", {2, 3, 4, 5, 6}))


def _pb_1(rng: random.Random) -> Draft:
    """Probability of a single event (fraction, simplest)."""
    if rng.random() < 0.35:
        name, s = rng.choice(_DICE)
        p = Fraction(len(s), 6)
        ms = [_frac_mis(Fraction(len(s), 6 - len(s)), "Divide by the total number of outcomes (6), not by the number of other outcomes")]
        p_txt = f"{len(s)}/6" + ("" if p.denominator == 6 else f" = {frac_str(p)}")   # no "5/6 = 5/6"
        return _q(f"A fair six-sided dice is rolled. What is the probability of getting {name}? "
                  "Give your answer as a fraction in its simplest form.",
                  _frac(p, simplest=True), f"The outcomes are {_lst(sorted(s))}: {len(s)} out of 6, so P = {p_txt}",
                  "List the outcomes that work, then divide by the total number of outcomes", ms)
    cols = rng.sample(_COLOURS, 3)

    def pick(r):
        ns = [r.randint(1, 12) for _ in cols]
        return ns if Fraction(ns[0], sum(ns)).denominator != 1 else None
    ns = retry(pick, rng)
    tot = sum(ns)
    p = Fraction(ns[0], tot)
    ms = [_frac_mis(Fraction(ns[0], tot - ns[0]), f"Divide by the total number of counters ({tot}), not by the number of other counters")]
    return _q(f"A bag contains {ns[0]} {cols[0]}, {ns[1]} {cols[1]} and {ns[2]} {cols[2]} counters. One counter is taken at random. "
              f"What is the probability that it is {cols[0]}? Give your answer as a fraction in its simplest form.",
              _frac(p, simplest=True), f"There are {tot} counters and {ns[0]} are {cols[0]}, so P = {ns[0]}/{tot}"
                                       + ("" if p.denominator == tot else f" = {frac_str(p)}"),
              "Probability = number of ways it can happen ÷ total number of outcomes", ms)


def _pb_2(rng: random.Random) -> Draft:
    """Expected frequency."""
    v = rng.random()
    if v < 0.4:
        def pick(r):
            p = Fraction(r.choice([5, 15, 25, 35, 45, 55, 65, 12, 18, 24, 32]), 100)
            n = r.choice([100, 200, 300, 400, 500, 600, 800, 1000])
            e = p * n
            return (p, n, e) if e.denominator == 1 else None
        p, n, e = retry(pick, rng)
        ms = [_exact_mis((1 - p) * n, "That's the expected number of tails — use the probability of heads")]
        return _q(f"The probability that a biased coin lands on heads is {_dec(p)}. The coin is thrown {n} times. "
                  "Work out an estimate for the number of times it lands on heads.",
                  _exact(e), f"Expected frequency = probability × number of trials = {_dec(p)} × {n} = {fmt_num(e)}",
                  "Expected frequency = probability × number of trials", ms)
    if v < 0.7:
        def pick(r):
            d = r.choice([4, 5, 8, 10, 12])
            k = r.randint(1, d - 1)
            n = d * r.randint(5, 40)
            return (Fraction(k, d), n) if math.gcd(k, d) == 1 else None
        p, n = retry(pick, rng)
        e = p * n
        ms = [_exact_mis((1 - p) * n, "That's the expected number of times it does NOT land on red"),
              _exact_mis(Fraction(n, p.denominator), f"Multiply by {p.numerator} as well: expected frequency = {frac_str(p)} × {n}")]
        return _q(f"The probability that a spinner lands on red is {frac_str(p)}. The spinner is spun {n} times. "
                  "How many times would you expect it to land on red?",
                  _exact(e), f"Expected frequency = {frac_str(p)} × {n} = {fmt_num(e)}",
                  "Expected frequency = probability × number of trials", ms)

    def pick(r):
        n1 = r.choice([40, 50, 60, 80, 100, 120, 150, 200])
        k = r.randint(3, n1 // 3)
        n2 = r.choice([200, 300, 400, 500, 600, 1000])
        e = Fraction(k * n2, n1)
        return (n1, k, n2, e) if e.denominator == 1 and n2 > n1 else None
    n1, k, n2, e = retry(pick, rng)
    ms = [_exact_mis(Fraction(k * n1, n2), f"Relative frequency = {k} ÷ {n1}; multiply it by {n2}"),
          _exact_mis(k + n2 - n1, "Use relative frequency × number of trials, not a difference")]
    return _q(f"In an experiment, a drawing pin landed point up {k} times in {n1} throws. The pin is thrown {n2} more times. "
              "Use the relative frequency to estimate how many of these throws land point up.",
              _exact(e), f"Relative frequency = {k}/{n1}. Estimate = {k}/{n1} × {n2} = {fmt_num(e)}",
              "Find the relative frequency (successes ÷ trials) first", ms)


def _pb_3(rng: random.Random) -> Draft:
    """P(not A) or P(A or B) for mutually exclusive outcomes."""
    cols = rng.sample(_COLOURS, 4)

    def pick(r):
        ps = [Fraction(r.randint(1, 9) * 5, 100) for _ in range(3)]
        rest = 1 - sum(ps)
        return (ps, rest) if rest > 0 and len(set(ps)) == 3 else None
    ps, rest = retry(pick, rng)
    table = ", ".join(f"P({c}) = {_dec(p)}" for c, p in zip(cols, ps))
    if rng.random() < 0.5:
        ms = [_frac_mis(sum(ps), "The probabilities add up to 1, so subtract the total of the others from 1", shown=_dec(sum(ps))),
              _frac_mis(1 - ps[0], f"Subtract all three given probabilities from 1, not just P({cols[0]})", shown=_dec(1 - ps[0]))]
        return _q(f"A spinner can land on {cols[0]}, {cols[1]}, {cols[2]} or {cols[3]}. {table}. "
                  f"Work out P({cols[3]}).",
                  _frac(rest, shown=_dec(rest)),
                  f"The probabilities add up to 1: P({cols[3]}) = 1 - ({_dec(ps[0])} + {_dec(ps[1])} + {_dec(ps[2])}) = {_dec(rest)}",
                  "All the probabilities must add up to 1", ms)
    i, j = rng.sample(range(3), 2)
    p = ps[i] + ps[j]
    ms = [_frac_mis(ps[i] * ps[j], "These outcomes are mutually exclusive, so add the probabilities (don't multiply)",
                    shown=_dec(ps[i] * ps[j])),
          _frac_mis(1 - p, f"That's the probability of NOT getting {cols[i]} or {cols[j]}", shown=_dec(1 - p))]
    return _q(f"A spinner can land on {cols[0]}, {cols[1]}, {cols[2]} or {cols[3]}. {table}. "
              f"Work out the probability that it lands on {cols[i]} or {cols[j]}.",
              _frac(p, shown=_dec(p)), f"Mutually exclusive outcomes: add. {_dec(ps[i])} + {_dec(ps[j])} = {_dec(p)}",
              "The spinner can't land on two colours at once, so use the addition rule", ms)


def _pb_4(rng: random.Random) -> Draft:
    """Independent events: P(A and B) or P(neither)."""
    ctx = rng.choice((("Ali's bus is late", "it rains"), ("Ben wins his tennis match", "Ben wins his chess match"),
                      ("a light bulb is faulty", "a battery is faulty"), ("Mia scores a penalty", "Leo scores a penalty")))

    def pick(r):
        a, b = Fraction(r.randint(1, 9), 10), Fraction(r.randint(1, 9), 10)
        return (a, b) if a != b else None
    a, b = retry(pick, rng)
    if rng.random() < 0.6:
        p = a * b
        ms = [_frac_mis(a + b if a + b <= 1 else None, "For independent events, multiply: P(A and B) = P(A) × P(B)",
                        shown=_dec(a + b))]
        return _q(f"The probability that {ctx[0]} is {_dec(a)}. The probability that {ctx[1]} is {_dec(b)}. "
                  "The events are independent. Work out the probability that both happen.",
                  _frac(p, shown=_dec(p)), f"P(both) = {_dec(a)} × {_dec(b)} = {_dec(p)}",
                  "For independent events, P(A and B) = P(A) × P(B)", ms)
    p = (1 - a) * (1 - b)
    ms = [_frac_mis(a * b, "That's the probability that both happen — use the probabilities that each does NOT happen",
                    shown=_dec(a * b)),
          _frac_mis(1 - a * b, "Work out P(not A) × P(not B)", shown=_dec(1 - a * b))]
    return _q(f"The probability that {ctx[0]} is {_dec(a)}. The probability that {ctx[1]} is {_dec(b)}. "
              "The events are independent. Work out the probability that neither happens.",
              _frac(p, shown=_dec(p)), f"P(neither) = (1 - {_dec(a)}) × (1 - {_dec(b)}) = {_dec(1 - a)} × {_dec(1 - b)} = {_dec(p)}",
              "Find the probability that each one does NOT happen, then multiply", ms)


def _pb_5(rng: random.Random) -> Draft:
    """Two picks without replacement (fraction, simplest)."""
    c1, c2 = rng.sample(_COLOURS[:4], 2)
    r_, b_ = rng.randint(2, 9), rng.randint(2, 9)
    n = r_ + b_
    v = rng.randrange(3)
    den = n * (n - 1)
    if v == 0:
        p = Fraction(r_ * (r_ - 1), den)
        what = f"both counters are {c1}"
        sol = f"P = {r_}/{n} × {r_ - 1}/{n - 1} = {r_ * (r_ - 1)}/{den} = {frac_str(p)}"
        ms = [_frac_mis(Fraction(r_ * r_, n * n), "Without replacement there is one fewer counter for the second pick")]
    elif v == 1:
        p = Fraction(2 * r_ * b_, den)
        what = f"one counter is {c1} and the other is {c2}"
        sol = f"P = {c1} then {c2} + {c2} then {c1} = {r_}/{n} × {b_}/{n - 1} + {b_}/{n} × {r_}/{n - 1} = {2 * r_ * b_}/{den} = {frac_str(p)}"
        ms = [_frac_mis(Fraction(r_ * b_, den), f"There are two orders: {c1} then {c2}, or {c2} then {c1}"),
              _frac_mis(Fraction(2 * r_ * b_, n * n), "Without replacement there is one fewer counter for the second pick")]
    else:
        p = Fraction(r_ * (r_ - 1) + b_ * (b_ - 1), den)
        what = "both counters are the same colour"
        sol = (f"P = both {c1} + both {c2} = {r_}/{n} × {r_ - 1}/{n - 1} + {b_}/{n} × {b_ - 1}/{n - 1} = "
               f"{r_ * (r_ - 1) + b_ * (b_ - 1)}/{den} = {frac_str(p)}")
        ms = [_frac_mis(Fraction(r_ * r_ + b_ * b_, n * n), "Without replacement there is one fewer counter for the second pick"),
              _frac_mis(Fraction(r_ * (r_ - 1), den), f"Add the probability that both are {c2} too")]
    return _q(f"A bag contains {r_} {c1} counters and {b_} {c2} counters. Two counters are taken at random without "
              f"replacement. Work out the probability that {what}. Give your answer as a fraction in its simplest form.",
              _frac(p, simplest=True), sol,
              "Draw a tree diagram: the second branch has one fewer counter in the bag", ms)


# ==================================================================== index numbers

# (item, lowest and highest realistic base price in pence). Every range is at least 100p wide and
# contains a whole number of pounds, so _ix_1 always finds a base price for any index number.
_GOODS = (("a loaf of bread", 90, 200), ("a litre of milk", 80, 180), ("a cinema ticket", 600, 1400),
          ("a bus fare", 150, 400), ("a kilogram of apples", 150, 350), ("a box of cereal", 150, 450))
_INDEX_1 = tuple(i for i in range(85, 146) if i != 100)      # a fall of up to 15% or a rise of up to 45%


def _money(p: Fraction) -> str:
    return "£" + fmt_dp(p, 2)


def _ix_1(rng: random.Random) -> Draft:
    """Index number from two prices."""
    item, lo, hi = rng.choice(_GOODS)
    idx = rng.choice(_INDEX_1)
    step = 100 // math.gcd(idx, 100)                   # base price (pence) must make base × idx ÷ 100 whole
    base = step * rng.randint(-(-lo // step), hi // step)
    new = Fraction(base * idx, 100)
    y0 = rng.randint(2012, 2018)
    y1 = y0 + rng.randint(2, 6)
    p0, p1 = Fraction(base, 100), Fraction(int(new), 100)
    ms = [_exact_mis(Fraction(base * 100, int(new)), f"Divide the {y1} price by the base-year ({y0}) price"),
          _exact_mis(idx - 100, "The index number includes the base of 100: index = 100 + percentage change")]
    return _q(f"The price of {item} was {_money(p0)} in {y0} and {_money(p1)} in {y1}. Using {y0} as the base year (index 100), "
              f"work out the index number for {y1}.",
              _exact(idx), f"Index = ({_money(p1)} ÷ {_money(p0)}) × 100 = {idx}",
              "Index number = (price in the year ÷ price in the base year) × 100", ms)


def _ix_2(rng: random.Random) -> Draft:
    """Price from an index number (£, 2 d.p.)."""
    item, lo, hi = rng.choice(_GOODS)

    def pick(r):
        base = Fraction(r.randint(lo, hi), 100)
        idx = Fraction(r.randint(850, 1450), 10)
        price = base * idx / 100
        if idx == 100 or near_half(price, 2) or (price * 100).denominator == 1:
            return None
        return base, idx, price
    base, idx, price = retry(pick, rng)
    y0 = rng.randint(2012, 2018)
    y1 = y0 + rng.randint(2, 6)
    ms = [_dp_mis(base * 100 / idx, 2, "Multiply by the index ÷ 100 — don't divide", "£"),
          _dp_mis(base + idx / 100, 2, "Multiply the base price by index ÷ 100, don't add", "£")]
    return _q(f"The price of {item} was {_money(base)} in {y0}. Using {y0} as the base year, the index number for {y1} "
              f"is {fmt_num(idx)}. Work out the price in {y1}. Give your answer to the nearest penny.",
              num_answer(price, _money(price), dp=2),
              f"Price = {_money(base)} × {fmt_num(idx)} ÷ 100 = £{fmt_num(price)} = {_money(price)}",
              "Price in the year = base price × index ÷ 100", ms)


def _ix_3(rng: random.Random) -> Draft:
    """Percentage change between two index numbers."""
    def pick(r):
        i1 = r.choice([80, 96, 104, 110, 112, 115, 120, 125, 130, 140, 150, 160, 175, 200])
        pct = r.choice([5, 8, 10, 12, 15, 20, 25, -5, -10, -20, 4, 6])
        i2 = Fraction(i1 * (100 + pct), 100)
        return (i1, pct, i2) if (i2 * 10).denominator == 1 and i2 != 100 else None
    i1, pct, i2 = retry(pick, rng)
    y1 = rng.randint(2015, 2019)
    y2 = y1 + rng.randint(2, 4)
    word = "increase" if pct > 0 else "decrease"
    ms = [_exact_mis(abs(i2 - i1), f"That's the change in index points — divide it by the {y1} index ({i1}) to get a percentage", "%"),
          _exact_mis(abs(i2 - 100), f"That's the change since the base year — compare with the {y1} index instead", "%")]
    return _q(f"The price index of a product (base year 2010 = 100) was {i1} in {y1} and {fmt_num(i2)} in {y2}. "
              f"Work out the percentage {word} in the price from {y1} to {y2}.",
              num_answer(abs(pct), f"{abs(pct)}%"),
              f"Change = {fmt_num(i2)} - {i1} = {fmt_num(i2 - i1)}. Percentage change = {fmt_num(i2 - i1)} ÷ {i1} × 100 = {pct}%, "
              f"a {abs(pct)}% {word}",
              f"Percentage change = (change in index ÷ the {y1} index) × 100", ms)


def _ix_4(rng: random.Random) -> Draft:
    """Chain base index, or the overall change from two chain base indices."""
    if rng.random() < 0.55:
        item, lo, hi = rng.choice(_GOODS)

        def pick(r):
            # realistic year-on-year changes: between 8% cheaper and 15% dearer
            p1 = r.randint(lo, hi)
            p2 = p1 + r.randint(-(p1 * 8 // 100), p1 * 15 // 100)
            p3 = p2 + r.randint(-(p2 * 8 // 100), p2 * 15 // 100)
            ci = Fraction(p3 * 100, p2)
            return None if near_half(ci, 1) or p2 == p3 or p1 == p2 else (p1, p2, p3, ci)
        p1, p2, p3, ci = retry(pick, rng)
        y = rng.randint(2016, 2021)
        pr = [_money(Fraction(p, 100)) for p in (p1, p2, p3)]
        ms = [_dp_mis(Fraction(p3 * 100, p1), 1, f"A chain base index compares with the year before ({y + 1}), not with {y}"),
              _dp_mis(Fraction(p2 * 100, p3), 1, f"Divide the {y + 2} price by the {y + 1} price")]
        return _q(f"The price of {item} was {pr[0]} in {y}, {pr[1]} in {y + 1} and {pr[2]} in {y + 2}. "
                  f"Work out the chain base index number for {y + 2}. Give your answer to 1 decimal place.",
                  _dp(ci, 1), f"Chain base index = ({pr[2]} ÷ {pr[1]}) × 100 = {float(ci):.3f}… = {fmt_dp(ci, 1)}",
                  "A chain base index compares each year with the year before: (this year's price ÷ last year's price) × 100",
                  ms)

    def pick(r):
        a, b = r.choice([102, 103, 104, 105, 106, 108, 110, 112, 95, 96, 98]), r.choice([102, 104, 105, 110, 115, 120, 97, 90])
        tot = Fraction(a * b, 100) - 100
        return None if near_half(tot, 1) or a == b or tot <= 0 else (a, b, tot)
    a, b, tot = retry(pick, rng)
    y = rng.randint(2016, 2021)
    word = "increase"
    ms = [_dp_mis((a - 100) + (b - 100), 1, f"Multiply the index numbers as decimals ({fmt_num(Fraction(a, 100))} × {fmt_num(Fraction(b, 100))}), don't add the percentages", "%")]
    return _q(f"The chain base index numbers for the price of a product are {a} for {y + 1} and {b} for {y + 2}. "
              f"Work out the overall percentage {word} in the price from {y} to {y + 2}. Give your answer to 1 decimal place.",
              _dp(tot, 1, "%"), f"Overall multiplier = {fmt_num(Fraction(a, 100))} × {fmt_num(Fraction(b, 100))} = "
                                f"{fmt_num(Fraction(a * b, 10000))}, so the price changed by {fmt_dp(tot, 1)}%",
              "Turn each chain index into a multiplier (105 → 1.05), then multiply them", ms)


def _ix_5(rng: random.Random) -> Draft:
    """Moving average or weighted index number."""
    if rng.random() < 0.7:
        q4 = rng.random() < 0.6
        k = 4 if q4 else 3

        def pick(r):
            vals = [r.randint(20, 90) for _ in range(8)]
            start = r.randint(1, 8 - k)                 # 0-based start of the window (not the first)
            avg = Fraction(sum(vals[start:start + k]), k)
            if not q4 and near_half(avg, 1):
                return None
            return vals, start, avg
        vals, start, avg = retry(pick, rng)
        labels = [f"Q{(i % 4) + 1} {2022 + i // 4}" for i in range(8)]
        data = ", ".join(f"{lab}: {v}" for lab, v in zip(labels, vals))
        window = labels[start:start + k]
        what = f"the {k}-point moving average for {window[0]} to {window[-1]}"
        shift = vals[start - 1:start - 1 + k]
        ms = [_exact_mis(sum(vals[start:start + k]), f"Divide the total by {k}") if q4 else
              _dp_mis(sum(vals[start:start + k]), 1, f"Divide the total by {k}"),
              (_exact_mis(Fraction(sum(shift), k), f"Start the moving average at {window[0]}") if q4 else
               _dp_mis(Fraction(sum(shift), k), 1, f"Start the moving average at {window[0]}"))]
        rnd = "" if q4 else " Give your answer to 1 decimal place."
        ans = _exact(avg) if q4 else _dp(avg, 1)
        sol = f"({' + '.join(str(v) for v in vals[start:start + k])}) ÷ {k} = {sum(vals[start:start + k])} ÷ {k} = " + (
            fmt_num(avg) if q4 else fmt_dp(avg, 1))
        return _q(f"Quarterly sales (in thousands) of a shop were: {data}. Work out {what}.{rnd}",
                  ans, sol, f"Add the {k} values in the window, then divide by {k}", ms)
    items = rng.sample(("food", "transport", "clothing", "energy", "housing", "leisure"), 3)

    def pick(r):
        idx = [r.randint(95, 140) for _ in range(3)]
        w = [r.randint(1, 6) for _ in range(3)]
        wi = Fraction(sum(i * x for i, x in zip(idx, w)), sum(w))
        return None if near_half(wi, 1) or len(set(w)) == 1 else (idx, w, wi)
    idx, w, wi = retry(pick, rng)
    data = "; ".join(f"{it.capitalize()}: index {i}, weight {x}" for it, i, x in zip(items, idx, w))
    ms = [_dp_mis(Fraction(sum(idx), 3), 1, "Multiply each index by its weight before adding"),
          _dp_mis(Fraction(sum(i * x for i, x in zip(idx, w)), 3), 1, f"Divide by the total of the weights ({sum(w)}), not by 3")]
    return _q(f"A weighted index is made from three items. {data}. Work out the weighted index number. "
              "Give your answer to 1 decimal place.",
              _dp(wi, 1), f"Σ(index × weight) = {' + '.join(f'{i} × {x}' for i, x in zip(idx, w))} = "
                          f"{sum(i * x for i, x in zip(idx, w))}; Σweights = {sum(w)}. Weighted index = {fmt_dp(wi, 1)}",
              "Weighted index = Σ(index × weight) ÷ Σ(weights)", ms)


# ==================================================================== registration

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


GEN_SKILLS: tuple[Skill, ...] = (
    _skill("stratified", "Stratified sampling",
           ("stratified sample", "capture recapture", "petersen", "stratified sampling", "capture-recapture",
            "petersen method"),
           (_st_1, _st_2, _st_3, _st_4, _st_5),
           "Each group's share of the sample matches its share of the population"),
    _skill("averages", "Averages",
           ("estimated mean", "mean", "median", "mode", "averages", "frequency table", "average",
            "combined mean", "grouped data"),
           (_av_1, _av_2, _av_3, _av_4, _av_5),
           "Mean = total ÷ number of values"),
    _skill("spread", "Measures of spread",
           ("interquartile range", "range", "iqr", "quartiles", "standard deviation", "outlier",
            "outliers", "lower quartile", "upper quartile", "measures of spread"),
           (_sp_1, _sp_2, _sp_3, _sp_4, _sp_5),
           "Put the data in order first"),
    _skill("spearman", "Spearman's rank",
           ("spearman's rank", "spearman", "rank correlation", "spearmans rank",
            "spearman's rank correlation coefficient"),
           (_sm_1, _sm_2, _sm_3, _sm_4, _sm_5),
           "Rank each variable separately, then find the differences d"),
    _skill("probability", "Probability",
           ("tree diagram", "probability", "expected frequency", "independent events", "relative frequency",
            "tree diagrams", "mutually exclusive", "without replacement"),
           (_pb_1, _pb_2, _pb_3, _pb_4, _pb_5),
           "Probability = number of ways it can happen ÷ total number of outcomes"),
    _skill("index_numbers", "Index numbers & time series",
           ("chain base index", "index numbers", "moving average", "time series", "weighted index",
            "index number", "moving averages", "chain base index numbers"),
           (_ix_1, _ix_2, _ix_3, _ix_4, _ix_5),
           "Index number = (value ÷ base value) × 100"),
)

_ROWS = (
    (("collecting", "Collecting data", ("data_collection", "stratified")),
     ("averages_spread", "Averages & spread", ("averages", "spread"))),
    (("diagrams", "Diagrams & correlation", ("diagrams", "spearman")),
     ("probability", "Probability & index numbers", ("probability", "index_numbers"))),
)
_ORDER = ("data_collection", "stratified", "averages", "spread", "diagrams", "spearman", "probability",
          "index_numbers")


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"{SUBJECT_ID}.y{y}.{slug}", label=label,
                    skills=tuple(f"{SUBJECT_ID}.{s}" for s in skills), level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Statistics", order=24, years={10: _year(10), 11: _year(11)})


def all_skills() -> list[Skill]:
    """Generator skills plus the bank skills from packs/statistics.json, in topic order."""
    by_id = {sk.id: sk for sk in GEN_SKILLS}
    for sk in load_pack("statistics", SUBJECT_ID):
        by_id[sk.id] = sk
    ordered = [by_id.pop(f"{SUBJECT_ID}.{n}") for n in _ORDER if f"{SUBJECT_ID}.{n}" in by_id]
    return ordered + list(by_id.values())


def register(reg) -> None:
    """Register Statistics (generators + pack) with a tutor.content Registry."""
    reg.register(make_subject(), all_skills())
