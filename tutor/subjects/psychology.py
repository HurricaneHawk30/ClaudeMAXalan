"""Psychology (GCSE, Years 10–11): docs/ARCHITECTURE_V2.md section 5.4.

Four bank skills live in ``packs/psychology.json``; this module adds the generator skill
``psychology.stats`` ("Psychology maths": mean → median/mode/range → percentage of
participants (1 d.p.) → ratio in simplest form → standard form or an estimate) and
registers the subject with its four topics.

Every generator is pure: ``generate(level, seed)`` uses only ``random.Random(seed)``.
Studies in the generated questions are hypothetical ("a psychologist..."), never real data.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction

from ..content import Answer, Mistake
from ..content.fmt import fmt_dp, fmt_num, fmt_sf, near_half, retry, round_sf, std_answer, std_mistake
from ._social import (
    Draft, gen_skill, num, ok_round, pct_answer, pct_mistake, plain_answer, plain_mistake, q,
    register_subject,
)

SUBJECT_ID = "psychology"
TITLE = "Psychology"
ORDER = 40

# (what is measured, plural noun for the answer, low, high, sentence before the data)
_SCORES = (
    ("words recalled", "words", 4, 18,
     "In a memory experiment, {n} participants each saw a list of 20 words. "
     "The number of words each participant recalled was:"),
    ("digits recalled", "digits", 4, 11,
     "In a digit span test, {n} participants tried to recall a sequence of digits. "
     "The longest sequence each participant recalled correctly was (number of digits):"),
    ("seconds", "seconds", 12, 70,
     "In a problem-solving study, {n} participants each solved a puzzle. "
     "The time each participant took, in seconds, was:"),
    ("conforming answers", "answers", 0, 12,
     "In a conformity study, {n} participants each answered 12 critical questions. "
     "The number of times each participant went along with the wrong group answer was:"),
    ("hours of sleep", "hours", 4, 11,
     "In a sleep study, {n} participants recorded how long they slept one night. "
     "The number of hours each participant slept (to the nearest hour) was:"),
    ("points", "points", 10, 40,
     "In a mindset study, {n} students completed a questionnaire scored out of 40. "
     "Their scores were:"),
)


_MEAN_ASK = {
    "words": "Work out the mean number of words recalled.",
    "digits": "Work out the mean number of digits recalled.",
    "seconds": "Work out the mean time in seconds.",
    "answers": "Work out the mean number of times a participant went along with the group.",
    "hours": "Work out the mean number of hours slept.",
    "points": "Work out the mean score.",
}


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _listing(values: list[int]) -> str:
    return ", ".join(str(v) for v in values)


def _median(values: list[int]) -> Fraction:
    s = sorted(values)
    n = len(s)
    if n % 2:
        return Fraction(s[n // 2])
    return Fraction(s[n // 2 - 1] + s[n // 2], 2)


def _shown(x: Fraction) -> str:
    return fmt_num(x)


# ------------------------------------------------------------------ L1 mean

def _st_1(rng: random.Random) -> Draft:
    what, noun, lo, hi, intro = rng.choice(_SCORES)

    def pick(r: random.Random):
        n = r.randrange(5, 9)
        m = r.randrange(lo + 2, hi - 1)
        vals = [r.randrange(lo, hi + 1) for _ in range(n - 1)]
        last = m * n - sum(vals)
        if not lo <= last <= hi:
            return None
        vals.append(last)
        r.shuffle(vals)
        if len(set(vals)) < 3:
            return None
        return n, m, vals
    n, m, vals = retry(pick, rng)
    total = sum(vals)
    text = intro.format(n=n) + "\n" + _listing(vals) + "\n" + _MEAN_ASK[noun]
    med = _median(vals)
    ms: list[Mistake | None] = [
        plain_mistake(total, f"That's the total — now divide it by the number of participants ({n})"),
    ]
    if med != m:
        ms.append(plain_mistake(med, "That's the median (the middle value) — for the mean, add up "
                                     "all the values and divide by how many there are"))
    wrong_n = Fraction(total, n - 1)
    ms.append(plain_mistake(wrong_n, f"Count the values again: there are {n} of them, so divide by {n}",
                            dp=None if wrong_n.denominator == 1 else 1))
    return q(text, plain_answer(m),
             f"Total = {' + '.join(str(v) for v in vals)} = {total}. Mean = {total} ÷ {n} = {m}",
             "Add up all the values, then divide by how many values there are", ms)


# ------------------------------------------------------- L2 median / mode / range

def _st_2(rng: random.Random) -> Draft:
    kind = rng.choice(("median", "mode", "range"))
    what, noun, lo, hi, intro = rng.choice(_SCORES)

    if kind == "median":
        def pick(r: random.Random):
            n = r.choice((6, 8))
            vals = [r.randrange(lo, hi + 1) for _ in range(n)]
            if len(set(vals)) < n - 1:
                return None
            unsorted_mid = Fraction(vals[n // 2 - 1] + vals[n // 2], 2)
            if unsorted_mid == _median(vals):
                return None
            return n, vals, unsorted_mid
        n, vals, unsorted_mid = retry(pick, rng)
        med = _median(vals)
        s = sorted(vals)
        a, b = s[n // 2 - 1], s[n // 2]
        text = intro.format(n=n) + "\n" + _listing(vals) + "\nWork out the median."
        sol = (f"In order: {_listing(s)}. There are {n} values, so the median is halfway between "
               f"the {_ordinal(n // 2)} and {_ordinal(n // 2 + 1)} values: ({a} + {b}) ÷ 2 = {_shown(med)}")
        mean = Fraction(sum(vals), n)
        ms = [plain_mistake(unsorted_mid, "Put the values in order from smallest to largest before "
                                          "finding the middle", dp=None),
              plain_mistake(mean, "That's the mean — the median is the middle value once the data "
                                  "are in order", dp=None if mean.denominator in (1, 2) else 1)]
        return q(text, plain_answer(med), sol,
                 "Write the values in order first, then find the middle", ms)

    if kind == "mode":
        def pick(r: random.Random):
            n = r.randrange(7, 10)
            mode = r.randrange(lo, hi + 1)
            reps = r.choice((2, 3))
            others = r.sample([v for v in range(lo, hi + 1) if v != mode], n - reps)
            vals = [mode] * reps + others
            r.shuffle(vals)
            if reps == mode:
                return None
            return vals, mode, reps
        vals, mode, reps = retry(pick, rng)
        text = intro.format(n=len(vals)) + "\n" + _listing(vals) + "\nWhat is the mode?"
        ms = [plain_mistake(reps, f"{reps} is how many times the mode appears — the mode is the value "
                                  f"itself"),
              plain_mistake(_median(vals), "That's the median — the mode is the value that appears "
                                           "most often", dp=None)]
        return q(text, plain_answer(mode),
                 f"{mode} appears {reps} times, more often than any other value, so the mode is {mode}",
                 "Look for the value that appears most often", ms)

    def pick_r(r: random.Random):
        n = r.randrange(6, 10)
        vals = [r.randrange(lo, hi + 1) for _ in range(n)]
        rng_ = max(vals) - min(vals)
        if rng_ < 3 or vals[0] in (max(vals), min(vals)) or vals[-1] in (max(vals), min(vals)):
            return None
        return vals
    vals = retry(pick_r, rng)
    big, small = max(vals), min(vals)
    first_last = abs(vals[-1] - vals[0])
    text = intro.format(n=len(vals)) + "\n" + _listing(vals) + "\nWork out the range."
    ms = [plain_mistake(big, "The range is the largest value minus the smallest value"),
          plain_mistake(first_last, "Use the largest and smallest values, not the first and last ones "
                                    "in the list")]
    return q(text, plain_answer(big - small), f"Range = largest − smallest = {big} − {small} = {big - small}",
             "Find the largest and the smallest values first", ms)


# ------------------------------------------------------- L3 percentage (1 d.p.)

_PCT_CONTEXTS = (
    ("In an obedience study, {k} of the {n} participants obeyed every instruction.",
     "obeyed every instruction", "did not obey every instruction"),
    ("In a conformity study, {k} of the {n} participants conformed at least once.",
     "conformed at least once", "never conformed"),
    ("In a serial position study, {k} of the {n} participants recalled the last word on the list.",
     "recalled the last word", "did not recall the last word"),
    ("In a questionnaire, {k} of the {n} students said they revise with music playing.",
     "said they revise with music playing", "did not say this"),
    ("In a field experiment, {k} of the {n} passers-by stopped to pick up the dropped papers.",
     "stopped to pick up the papers", "did not stop"),
    ("In a sleep study, {k} of the {n} participants reported a dream when they were woken.",
     "reported a dream", "did not report a dream"),
    ("In a perception study, {k} of the {n} participants saw the ambiguous figure as a letter.",
     "saw the figure as a letter", "did not see it as a letter"),
)


def _st_3(rng: random.Random) -> Draft:
    ctx, did, did_not = rng.choice(_PCT_CONTEXTS)

    def pick(r: random.Random):
        n = r.randrange(21, 91)
        k = r.randrange(3, n - 2)
        p = Fraction(100 * k, n)
        if p.denominator == 1 or not ok_round(p, 1) or not ok_round(100 - p, 1):
            return None
        if fmt_dp(p, 1) == fmt_dp(100 - p, 1):
            return None
        return n, k, p
    n, k, p = retry(pick, rng)
    text = (ctx.format(k=k, n=n) + f" What percentage of the participants {did}? "
            "Give your answer to 1 decimal place.")
    if "students" in ctx or "passers-by" in ctx:
        who = "students" if "students" in ctx else "passers-by"
        text = (ctx.format(k=k, n=n) + f" What percentage of the {who} {did}? "
                "Give your answer to 1 decimal place.")
    ms = [pct_mistake(100 - p, f"That's the percentage who {did_not} — use the {k}, not the {n - k}", dp=1),
          plain_mistake(Fraction(k, n), "That's the fraction as a decimal — multiply by 100 to make it a "
                                        "percentage", dp=2)]
    return q(text, pct_answer(p, 1),
             f"{k} ÷ {n} × 100 = {fmt_dp(p, 3)}… = {fmt_dp(p, 1)}% (1 d.p.)",
             f"Divide {k} by {n}, then multiply by 100", ms)


# ------------------------------------------------------- L4 ratio, simplest form

_RATIO_CONTEXTS = (
    ("In an experiment, {a} participants were in the experimental condition and {b} were in the "
     "control condition. Write the ratio of experimental to control participants in its simplest form."),
    ("In a conformity study, {a} participants conformed at least once and {b} never conformed. "
     "Write the ratio of participants who conformed to those who never conformed in its simplest form."),
    ("An opportunity sample contains {a} girls and {b} boys. Write the ratio of girls to boys in its "
     "simplest form."),
    ("In a questionnaire, {a} students agreed with a statement and {b} disagreed. Write the ratio of "
     "students who agreed to students who disagreed in its simplest form."),
    ("In a field experiment, {a} people helped a stranger and {b} people walked past. Write the ratio of "
     "people who helped to people who walked past in its simplest form."),
    ("In a memory study, {a} participants used rehearsal and {b} used imagery. Write the ratio of "
     "rehearsal users to imagery users in its simplest form."),
)


def _st_4(rng: random.Random) -> Draft:
    ctx = rng.choice(_RATIO_CONTEXTS)

    def pick(r: random.Random):
        p, qq = r.randrange(1, 10), r.randrange(1, 10)
        if p == qq or math.gcd(p, qq) != 1:
            return None
        g = r.randrange(2, 13)
        if (p + qq) * g > 160:
            return None
        return p, qq, g
    p, qq, g = retry(pick, rng)
    a, b = p * g, qq * g
    ans = Answer(kind="ratio", display=f"{p}:{qq}", value=[p, qq], form="simplest")
    ms = [Mistake(Answer(kind="ratio", display=f"{qq}:{p}", value=[qq, p], form="any"),
                  "Keep the order the question uses — the first group in the question comes first"),
          Mistake(Answer(kind="ratio", display=f"{p}:{p + qq}", value=[p, p + qq], form="any"),
                  "That compares one group with the total — compare the two groups with each other")]
    return q(ctx.format(a=a, b=b), ans,
             f"{a}:{b}. The highest common factor of {a} and {b} is {g}, so divide both by {g}: "
             f"{p}:{qq}",
             f"Find the highest common factor of {a} and {b}", ms)


# ------------------------------------------------------- L5 standard form or estimate

def _round1(x: Fraction) -> Fraction:
    return Fraction(round_sf(x, 1))


def _st_5(rng: random.Random) -> Draft:
    kind = rng.choice(("big", "small", "estimate", "estimate"))
    if kind == "big":
        def pick(r: random.Random):
            digits = r.choice((2, 2, 3))
            m = r.randrange(10 ** (digits - 1) + 1, 10 ** digits)
            if m % 10 == 0:
                return None
            e = r.randrange(5, 10)
            return m * 10 ** (e - digits + 1), e
        n, e = retry(pick, rng)
        ctx = rng.choice(("An online psychology survey was completed {n} times. Write {n} in standard form.",
                          "A psychology video has been watched {n} times. Write {n} in standard form.",
                          "A researcher's data file contains {n} reaction-time measurements. "
                          "Write {n} in standard form."))
        shown = num(n)
        return q(ctx.format(n=shown), std_answer(n),
                 f"Move the decimal point {e} places to the left to get a number between 1 and 10, "
                 f"so {shown} = {std_answer(n).display}",
                 "Write a number between 1 and 10, then count how many places the decimal point moves",
                 [std_mistake(n * 10, "", "Count the places again — the power of 10 is one too big"),
                  std_mistake(Fraction(n, 10), "", "Count the places again — the power of 10 is one too small")])
    if kind == "small":
        def pick(r: random.Random):
            digits = r.choice((1, 2, 2))
            m = r.randrange(10 ** (digits - 1), 10 ** digits) if digits > 1 else r.randrange(2, 10)
            if digits > 1 and m % 10 == 0:
                return None
            e = r.randrange(2, 6)
            return Fraction(m, 10 ** (e + digits - 1)), e
        x, e = retry(pick, rng)
        shown = fmt_num(x)
        ctx = rng.choice(("In a reaction-time experiment, the difference between two conditions was "
                          "{x} seconds. Write {x} in standard form.",
                          "A brain-scanning study records a signal that lasts {x} seconds. "
                          "Write {x} in standard form."))
        ans = std_answer(x)
        return q(ctx.format(x=shown), ans,
                 f"The first non-zero digit is {e} places after the decimal point, so {shown} = {ans.display}",
                 "For a number less than 1 the power of 10 is negative",
                 [std_mistake(x * 10 ** (2 * e), "", "A number less than 1 has a negative power of 10"),
                  std_mistake(x * 10, "", "Count the places again — the power of 10 is one too big"),
                  std_mistake(x / 10, "", "Count the places again — the power of 10 is one too small")])

    # estimate by rounding each number to 1 significant figure
    def pick_e(r: random.Random):
        a = r.randrange(21, 990)
        b = Fraction(r.randrange(21, 130), 10)
        if b.denominator == 1 or a % 10 == 0:
            return None
        if near_half(a, sf=1) or near_half(b, sf=1):
            return None
        ra, rb = _round1(Fraction(a)), _round1(b)
        est = ra * rb
        exact = a * b
        if est == exact or ra == a:
            return None
        return a, b, ra, rb, est, exact
    a, b, ra, rb, est, exact = retry(pick_e, rng)
    ctx = rng.choice((
        "A psychologist surveys {a} students. On average, each student says they revise for {b} hours "
        "a week. Estimate the total number of hours revised each week by rounding each number to "
        "1 significant figure.",
        "In a study, {a} participants each spent {b} minutes on a memory test. Estimate the total time "
        "in minutes by rounding each number to 1 significant figure.",
        "A sleep researcher studies {a} people who each sleep for an average of {b} hours a night. "
        "Estimate the total hours slept in one night by rounding each number to 1 significant figure.",
    ))
    sa, sb = num(a), fmt_num(b)
    return q(ctx.format(a=sa, b=sb), plain_answer(est),
             f"{sa} ≈ {num(ra)} and {sb} ≈ {fmt_num(rb)} (1 s.f.), so the estimate is "
             f"{num(ra)} × {fmt_num(rb)} = {num(est)}",
             "Round each number so it has only one non-zero digit, then multiply",
             [plain_mistake(exact, "That's the exact answer — round each number to 1 significant figure "
                                   "first, then multiply"),
              plain_mistake(Fraction(round_sf(exact, 1)), "Round each number to 1 significant figure "
                                                           "before multiplying, not the answer at the end")])


STATS = gen_skill(
    SUBJECT_ID, "stats", "Psychology maths",
    ("psychology maths", "mean median mode", "percentages", "ratio", "standard form", "estimating"),
    (_st_1, _st_2, _st_3, _st_4, _st_5),
    "Write down what the question gives you, then take it one step at a time",
)

ROWS = (
    (("memory_perception", "Memory & perception", ("memory_perception",)),
     ("development_brain", "Development & the brain", ("development_brain",))),
    (("social_influence", "Social influence", ("social_influence",)),
     ("research_methods", "Research methods", ("research_methods", "stats"))),
)

SKILL_ORDER = ("memory_perception", "development_brain", "social_influence", "research_methods", "stats")


def register(reg) -> None:
    """Register Psychology: the pack's bank skills plus the generator skill."""
    register_subject(reg, SUBJECT_ID, TITLE, ORDER, ROWS, SKILL_ORDER, [STATS])
