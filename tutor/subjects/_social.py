"""Private helpers for Psychology, Economics and Business (docs/ARCHITECTURE_V2.md section 5.4).

Not a subject module (the leading underscore keeps the registry from importing it as one).
It holds what the three modules share:

- ``gen_skill``: wraps five level functions into a pure, deterministic generator skill
  (``random.Random(seed)`` only; every problem goes through ``fmt.build``);
- ``register_subject``: loads the subject's pack, checks that the pack and the generators
  together provide exactly the skills of section 5.4, builds the Years 10–11 topic rows and
  registers everything in the order of section 5.4;
- small number/text helpers (money with thousands commas, percentages, plurals).
"""
from __future__ import annotations

import random
from decimal import Decimal
from fractions import Fraction
from typing import Callable, Iterable, Sequence

from ..content import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, load_pack
from ..content.fmt import (
    build, check_level, dec, fmt_dp, fmt_num, is_whole, near_half, num_answer, round_dp,
)

YEARS = (10, 11)
LEVEL_MAP = (1, 2, 3, 4, 5)
PAST_PAPER_LEVEL_MAP = (2, 3, 3, 4, 5)

Draft = dict
LevelFn = Callable[[random.Random], Draft]
# One keyboard row: up to two (slug, label, skill names) entries.
Row = Sequence[tuple[str, str, Sequence[str]]]


# ================================================================ drafts

def q(text: str, answer: Answer, solution: str, hint: str,
      mistakes: Iterable[Mistake | None] = ()) -> Draft:
    """A problem draft for ``fmt.build`` (validated there)."""
    return {"text": text, "answer": answer, "solution": solution, "hint": hint,
            "mistakes": list(mistakes)}


# ================================================================ numbers

def gbp(x, pennies: bool = False) -> str:
    """Money with thousands commas: '£1,250', '£1,250.50', '-£300'.

    Values that are not whole pounds always show 2 decimal places; ``pennies=True``
    forces 2 decimal places (for answers given "to the nearest penny").
    """
    d = dec(x)
    sign = "-" if d < 0 else ""
    d = abs(d)
    if pennies or not is_whole(d):
        body = format(round_dp(d, 2), ",.2f")
    else:
        body = format(int(d), ",")
    return f"{sign}£{body}"


def cur(symbol: str, x, pennies: bool = True) -> str:
    """Another currency ('$', '€') in the same style as ``gbp``."""
    return gbp(x, pennies).replace("£", symbol)


def num(x) -> str:
    """A whole number with thousands commas, or an exact decimal: '12,500', '3.75'."""
    if is_whole(x):
        return format(int(dec(x)), ",")
    return fmt_num(x)


def pct(x, dp: int | None = None) -> str:
    """'14.6%' (rounded half-up to ``dp`` places) or the exact value: '12.5%'."""
    return (fmt_dp(x, dp) if dp is not None else fmt_num(x)) + "%"


def money_answer(x, pennies: bool = False) -> Answer:
    """A £ answer; with ``pennies`` the question must ask for the nearest penny (dp=2)."""
    return num_answer(x, gbp(x, pennies), dp=2 if pennies else None)


def money_mistake(x, feedback: str, pennies: bool = False) -> Mistake | None:
    v = _finite(x)
    if v is None:
        return None
    return Mistake(Answer(kind="number", display=gbp(x, pennies), value=v,
                          dp=2 if pennies else None), feedback)


def pct_answer(x, dp: int | None = None) -> Answer:
    return num_answer(x, pct(x, dp), dp=dp)


def pct_mistake(x, feedback: str, dp: int | None = None) -> Mistake | None:
    v = _finite(x)
    if v is None:
        return None
    return Mistake(Answer(kind="number", display=pct(x, dp), value=v, dp=dp), feedback)


def plain_answer(x, unit_word: str = "", dp: int | None = None) -> Answer:
    shown = fmt_dp(x, dp) if dp is not None else num(x)
    return num_answer(x, f"{shown} {unit_word}".strip(), dp=dp)


def plain_mistake(x, feedback: str, unit_word: str = "", dp: int | None = None) -> Mistake | None:
    v = _finite(x)
    if v is None:
        return None
    shown = fmt_dp(x, dp) if dp is not None else num(x)
    return Mistake(Answer(kind="number", display=f"{shown} {unit_word}".strip(), value=v, dp=dp),
                   feedback)


def _finite(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v


def ok_round(x, dp: int) -> bool:
    """True when ``x`` is safe to ask for at ``dp`` places (not on a rounding boundary)."""
    return not near_half(x, dp)


def frac(x) -> Fraction:
    """Exact Fraction of an int, a Fraction or a decimal string such as '2.35'."""
    if isinstance(x, str):
        return Fraction(Decimal(x))
    return Fraction(x)


def plural(n: int, word: str, many: str | None = None) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {many or word + 's'}"


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


# ================================================================ skills

def gen_skill(subject_id: str, name: str, title: str, aliases: Sequence[str],
              levels: Sequence[LevelFn], fallback_hint: str) -> Skill:
    """A generator skill: ``generate(level, seed)`` is pure and uses only Random(seed)."""
    sid = f"{subject_id}.{name}"
    if len(levels) != 5:
        raise ValueError(f"{sid}: needs exactly 5 level functions")
    aliases = tuple(a.lower() for a in aliases)
    if len(aliases) < 3 or any(not a.strip() for a in aliases):
        raise ValueError(f"{sid}: needs at least 3 non-empty aliases")
    fns = tuple(levels)

    def generate(level: int, seed: int) -> Problem:
        check_level(level)
        rng = random.Random(seed)
        draft = fns[level - 1](rng)
        return build(sid, level, seed, fallback_hint=fallback_hint, **draft)

    generate.__name__ = f"generate_{name}"
    generate.__qualname__ = generate.__name__
    return Skill(id=sid, subject=subject_id, title=title, aliases=aliases, generate=generate)


def make_subject(subject_id: str, title: str, order: int, rows: Sequence[Row]) -> Subject:
    """Years 10 and 11 with the same rows; topic ids ``<subject>.y<year>.<slug>``."""
    years: dict[int, YearSpec] = {}
    for y in YEARS:
        spec_rows = tuple(
            tuple(Topic(id=f"{subject_id}.y{y}.{slug}", label=label,
                        skills=tuple(f"{subject_id}.{s}" for s in skills),
                        level_map=LEVEL_MAP)
                  for slug, label, skills in row)
            for row in rows)
        years[y] = YearSpec(rows=spec_rows, past_paper_level_map=PAST_PAPER_LEVEL_MAP)
    return Subject(id=subject_id, title=title, order=order, years=years)


def register_subject(reg, subject_id: str, title: str, order: int, rows: Sequence[Row],
                     skill_order: Sequence[str], generators: Sequence[Skill]) -> None:
    """Load ``packs/<subject_id>.json``, add the generator skills and register the subject.

    Raises ValueError if the pack plus the generators do not give exactly the skills in
    ``skill_order`` (so a missing or misnamed skill fails the strict tests loudly).
    """
    bank_skills = list(load_pack(subject_id, subject_id))
    by_id: dict[str, Skill] = {}
    for s in list(bank_skills) + list(generators):
        if s.id in by_id:
            raise ValueError(f"{subject_id}: skill {s.id} is defined twice")
        by_id[s.id] = s
    wanted = [f"{subject_id}.{n}" for n in skill_order]
    missing = [sid for sid in wanted if sid not in by_id]
    extra = sorted(set(by_id) - set(wanted))
    if missing or extra:
        raise ValueError(f"{subject_id}: missing skills {missing}, unexpected skills {extra}")
    reg.register(make_subject(subject_id, title, order, rows), [by_id[sid] for sid in wanted])
