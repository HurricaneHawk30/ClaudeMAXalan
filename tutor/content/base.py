from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable

PAST_PAPER_LABEL = "Past paper practice"
MY_OWN_TOPIC_LABEL = "My own topic"
ANSWER_KINDS = ("number", "fraction", "set", "assign", "expr", "ratio", "rubric", "choice", "short")
CHOICE_LETTERS = "ABCDE"
SHORT_FORMS = ("any", "strict", "case", "pinyin")


@dataclass(frozen=True)
class Answer:
    kind: str                    # one of ANSWER_KINDS
    display: str                 # canonical text shown after "Correct answer: "; check(answer, display) MUST be "correct" (except rubric)
    value: object = None         # number: float (exact, unrounded) | fraction: "p/q" or "p" | set: list[str] of numbers ("2", "-3", "1/2", "2.5")
                                 # assign: dict[str, str] var->number str | expr: str in Python syntax ("x**2+5*x+6") | ratio: list[int] | rubric: None
                                 # choice: {"options": list[str] (displayed order, 3..5), "correct": int}; display "B) Mitochondria"
                                 # short: {"accept": list[str] (>= 1), "reject": list[str]}; display = accept[0]
    dp: int | None = None        # number / set elements: decimal places stated in the question (0..3)
    sf: int | None = None        # number: significant figures stated (>= 2)
    form: str = "any"            # number: any|standard  fraction: any|simplest|mixed  expr: any|expanded|factorised  ratio: any|simplest
                                 # short: any|strict|case|pinyin (SHORT_FORMS)  choice: any
    ordered: bool = False        # set: order matters (shares of a ratio)
    var: str = "x"               # expr: the single variable letter ("x" or "n")
    mark_scheme: str = ""        # rubric only (display = model answer)
    max_marks: int = 0           # rubric only


@dataclass(frozen=True)
class Mistake:
    answer: Answer               # a typical wrong answer (never equal to the correct one)
    feedback: str                # kind, specific, no trailing period, e.g. "It looks like you found 15% but didn't add it on"


@dataclass(frozen=True)
class Problem:
    skill_id: str
    level: int                   # generator level 1..5
    seed: int
    text: str                    # question only (no "Problem N:"), plain text, states rounding + units
    answer: Answer
    solution: str                # short worked solution, no trailing period, <= 300 chars
    hint: str                    # a first step; must not contain answer.display
    mistakes: tuple[Mistake, ...] = ()
    ref: str = ""                # stable id of the underlying question: "<skill_id>#<question id>" for bank items; "" = none


@dataclass(frozen=True)
class BankItem:
    ref: str                              # "<skill_id>#<question id>", unique across the registry
    level: int                            # level written in the file, 1..5
    kind: str                             # answer kind
    render: Callable[[int], Problem]      # seed -> Problem(level=self.level, seed=seed, ref=self.ref); pure


@dataclass(frozen=True)
class Skill:
    id: str                      # "<subject>.<name>", e.g. "maths.pythagoras"
    subject: str
    title: str                   # human label, used as topic label for «My own topic»
    aliases: tuple[str, ...]     # lowercase phrases for free-text matching
    generate: Callable[[int, int], Problem]   # (level 1..5, seed) -> Problem; pure & deterministic (random.Random(seed))
    items: tuple[BankItem, ...] = ()          # bank skills: every question in file order; generator skills: ()


@dataclass(frozen=True)
class Topic:
    id: str                      # stable, stored in DB
    label: str                   # exact button text
    skills: tuple[str, ...]      # skill ids, non-empty
    level_map: tuple[int, int, int, int, int] = (1, 2, 3, 4, 5)   # student level (index+1) -> generator level
    exam: bool = False           # True only for past-paper topics


@dataclass(frozen=True)
class YearSpec:
    rows: tuple[tuple[Topic, ...], ...]          # keyboard rows, 1–2 topics each
    past_paper_level_map: tuple[int, int, int, int, int] = (2, 3, 3, 4, 5)


@dataclass(frozen=True)
class Subject:
    id: str                      # "maths"
    title: str                   # exact button text, "Maths"
    order: int                   # button order (ascending)
    years: dict[int, YearSpec]   # only years with content


def fingerprint(p: Problem) -> str:
    """Identity of a problem for repeat avoidance: the bank ref, else a hash of the text."""
    if p.ref:
        return p.ref
    text = " ".join(p.text.split()).casefold()
    return "t:" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- JSON

def _answer_to_dict(a: Answer) -> dict:
    return {
        "kind": a.kind,
        "display": a.display,
        "value": a.value,
        "dp": a.dp,
        "sf": a.sf,
        "form": a.form,
        "ordered": a.ordered,
        "var": a.var,
        "mark_scheme": a.mark_scheme,
        "max_marks": a.max_marks,
    }


def _answer_from_dict(d: dict) -> Answer:
    value = d.get("value")
    kind = d.get("kind")
    # JSON has no tuples; Answer.value only ever holds lists/dicts/scalars,
    # so a plain round-trip is exact.
    return Answer(
        kind=kind,
        display=d["display"],
        value=value,
        dp=d.get("dp"),
        sf=d.get("sf"),
        form=d.get("form", "any"),
        ordered=bool(d.get("ordered", False)),
        var=d.get("var", "x"),
        mark_scheme=d.get("mark_scheme", ""),
        max_marks=int(d.get("max_marks", 0)),
    )


def problem_to_json(p: Problem) -> str:
    d = {
        "skill_id": p.skill_id,
        "level": p.level,
        "seed": p.seed,
        "text": p.text,
        "answer": _answer_to_dict(p.answer),
        "solution": p.solution,
        "hint": p.hint,
        "mistakes": [
            {"answer": _answer_to_dict(m.answer), "feedback": m.feedback}
            for m in p.mistakes
        ],
        "ref": p.ref,
    }
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def problem_from_json(s: str) -> Problem:
    d = json.loads(s)
    return Problem(
        skill_id=d["skill_id"],
        level=int(d["level"]),
        seed=int(d["seed"]),
        text=d["text"],
        answer=_answer_from_dict(d["answer"]),
        solution=d["solution"],
        hint=d["hint"],
        mistakes=tuple(
            Mistake(answer=_answer_from_dict(m["answer"]), feedback=m["feedback"])
            for m in d.get("mistakes", [])
        ),
        ref=d.get("ref", "") or "",
    )
