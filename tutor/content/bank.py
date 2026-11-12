"""JSON question banks (docs/ARCHITECTURE.md section 2.5)."""
from __future__ import annotations

import copy
import json
import random
from dataclasses import fields
from typing import Callable

from .base import (
    ANSWER_KINDS, Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec,
)
from .checker import check
from .registry import Registry


class BankError(ValueError):
    """The question bank is invalid; the message contains the JSON path."""


_ANSWER_KEYS = {f.name for f in fields(Answer)}
_FORMS = {
    "number": ("any", "standard"),
    "fraction": ("any", "simplest"),
    "expr": ("any", "expanded", "factorised"),
    "ratio": ("any", "simplest"),
}


def _err(path: str, msg: str) -> BankError:
    return BankError(f"{path}: {msg}")


def _req(d: dict, key: str, path: str, typ: type | tuple) -> object:
    if not isinstance(d, dict):
        raise _err(path, "expected an object")
    if key not in d:
        raise _err(path, f"missing field {key!r}")
    v = d[key]
    if isinstance(v, bool) and typ not in (bool, (bool,)) and (
            typ is int or (isinstance(typ, tuple) and int in typ)):
        raise _err(f"{path}.{key}", "expected a number, got a boolean")
    if not isinstance(v, typ):
        raise _err(f"{path}.{key}", f"wrong type {type(v).__name__}")
    return v


def _str(d: dict, key: str, path: str) -> str:
    v = _req(d, key, path, str)
    assert isinstance(v, str)
    if not v.strip():
        raise _err(f"{path}.{key}", "must not be empty")
    return v


def _level_map(v: object, path: str) -> tuple:
    if (not isinstance(v, list) or len(v) != 5
            or any(isinstance(x, bool) or not isinstance(x, int) or not 1 <= x <= 5 for x in v)):
        raise _err(path, "must be a list of 5 integers in 1..5")
    return tuple(v)


def _num_str(v: object, path: str) -> str:
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise _err(path, "expected a number or a numeric string")
    return str(v)


def _build_answer(d: object, path: str) -> Answer:
    if not isinstance(d, dict):
        raise _err(path, "expected an object")
    unknown = set(d) - _ANSWER_KEYS
    if unknown:
        raise _err(path, f"unknown key(s) {sorted(unknown)}")
    kind = _req(d, "kind", path, str)
    if kind not in ANSWER_KINDS:
        raise _err(f"{path}.kind", f"unknown kind {kind!r}")
    display = _str(d, "display", path)
    kw: dict = {"kind": kind, "display": display}
    for key in ("dp", "sf", "max_marks"):
        if key in d and d[key] is not None:
            v = d[key]
            if isinstance(v, bool) or not isinstance(v, int):
                raise _err(f"{path}.{key}", "must be an integer")
            kw[key] = v
    if kw.get("dp") is not None and not 0 <= kw["dp"] <= 3:
        raise _err(f"{path}.dp", "must be in 0..3")
    if kw.get("sf") is not None and kw["sf"] < 2:
        raise _err(f"{path}.sf", "must be >= 2")
    if "form" in d:
        form = d["form"]
        if not isinstance(form, str) or form not in _FORMS.get(kind, ("any",)):
            raise _err(f"{path}.form", f"invalid form {form!r} for kind {kind!r}")
        kw["form"] = form
    if "ordered" in d:
        if not isinstance(d["ordered"], bool):
            raise _err(f"{path}.ordered", "must be true or false")
        kw["ordered"] = d["ordered"]
    if "var" in d:
        v = d["var"]
        if not isinstance(v, str) or len(v) != 1 or not v.isalpha():
            raise _err(f"{path}.var", "must be a single letter")
        kw["var"] = v
    if "mark_scheme" in d:
        if not isinstance(d["mark_scheme"], str):
            raise _err(f"{path}.mark_scheme", "must be a string")
        kw["mark_scheme"] = d["mark_scheme"]

    vp = f"{path}.value"
    if kind == "rubric":
        if kw.get("max_marks", 0) <= 0:
            raise _err(f"{path}.max_marks", "rubric needs max_marks > 0")
    else:
        if "value" not in d:
            raise _err(path, "missing field 'value'")
        v = d["value"]
        if kind == "number":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise _err(vp, "number value must be a number")
            kw["value"] = float(v)
        elif kind == "fraction":
            kw["value"] = _num_str(v, vp)
        elif kind == "set":
            if not isinstance(v, list) or not v:
                raise _err(vp, "set value must be a non-empty list")
            kw["value"] = [_num_str(x, f"{vp}[{i}]") for i, x in enumerate(v)]
        elif kind == "assign":
            if not isinstance(v, dict) or not v:
                raise _err(vp, "assign value must be a non-empty object")
            kw["value"] = {str(k): _num_str(x, f"{vp}.{k}") for k, x in v.items()}
        elif kind == "expr":
            if not isinstance(v, str) or not v.strip():
                raise _err(vp, "expr value must be a string")
            kw["value"] = v
        elif kind == "ratio":
            if (not isinstance(v, list) or len(v) < 2
                    or any(isinstance(x, bool) or not isinstance(x, int) or x <= 0 for x in v)):
                raise _err(vp, "ratio value must be a list of >= 2 positive integers")
            kw["value"] = list(v)
    return Answer(**kw)


def _build_question(q: object, path: str, skill_id: str) -> tuple[int, dict]:
    if not isinstance(q, dict):
        raise _err(path, "expected an object")
    level = _req(q, "level", path, int)
    if not 1 <= level <= 5:
        raise _err(f"{path}.level", f"level must be in 1..5, got {level}")
    text = _str(q, "text", path)
    solution = _str(q, "solution", path)
    hint = _str(q, "hint", path)
    if "answer" not in q:
        raise _err(path, "missing field 'answer'")
    answer = _build_answer(q["answer"], f"{path}.answer")
    if answer.kind != "rubric":
        v = check(answer, answer.display)
        if v.status != "correct":
            raise _err(f"{path}.answer.display",
                       f"display {answer.display!r} is not judged correct (got {v.status})")
    raw_m = q.get("mistakes", [])
    if not isinstance(raw_m, list):
        raise _err(f"{path}.mistakes", "expected a list")
    mistakes: list[Mistake] = []
    for i, m in enumerate(raw_m):
        mp = f"{path}.mistakes[{i}]"
        if not isinstance(m, dict):
            raise _err(mp, "expected an object")
        feedback = _str(m, "feedback", mp)
        if "answer" not in m:
            raise _err(mp, "missing field 'answer'")
        ma = _build_answer(m["answer"], f"{mp}.answer")
        if ma.kind == "rubric":
            raise _err(f"{mp}.answer.kind", "a mistake cannot be a rubric")
        if check(ma, ma.display).status != "correct":
            raise _err(f"{mp}.answer.display", "mistake display is not judged correct for itself")
        if answer.kind != "rubric" and check(answer, ma.display).status == "correct":
            continue  # coincides with the correct answer: dropped
        mistakes.append(Mistake(ma, feedback))
    return level, {"text": text, "answer": answer, "solution": solution,
                   "hint": hint, "mistakes": tuple(mistakes)}


def _make_generate(skill_id: str, by_level: dict[int, list[dict]]) -> Callable[[int, int], Problem]:
    levels = sorted(by_level)

    def generate(level: int, seed: int) -> Problem:
        if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 5:
            raise ValueError(f"level must be 1..5, got {level!r}")
        use = min(levels, key=lambda l: (abs(l - level), l > level))
        q = random.Random(seed).choice(by_level[use])
        return Problem(
            skill_id=skill_id, level=level, seed=seed, text=q["text"],
            answer=copy.deepcopy(q["answer"]), solution=q["solution"], hint=q["hint"],
            mistakes=copy.deepcopy(q["mistakes"]))

    return generate


def load_bank(path: str) -> tuple[Subject, list[Skill]]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as e:
        raise BankError(f"$: cannot read {path}: {e.strerror or e}") from e
    except (ValueError, RecursionError) as e:
        raise BankError(f"$: invalid JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise BankError("$: expected an object")

    sj = _req(data, "subject", "$", dict)
    sid = _str(sj, "id", "$.subject")
    title = _str(sj, "title", "$.subject")
    order = _req(sj, "order", "$.subject", int)

    raw_skills = _req(data, "skills", "$", list)
    if not raw_skills:
        raise _err("$.skills", "no skills")
    skills: list[Skill] = []
    seen: set[str] = set()
    for si, rs in enumerate(raw_skills):
        sp = f"$.skills[{si}]"
        kid = _str(rs, "id", sp)
        if kid in seen:
            raise _err(f"{sp}.id", f"duplicate skill id {kid!r}")
        seen.add(kid)
        stitle = _str(rs, "title", sp)
        aliases = _req(rs, "aliases", sp, list)
        if any(not isinstance(a, str) or not a.strip() for a in aliases):
            raise _err(f"{sp}.aliases", "must be a list of non-empty strings")
        questions = _req(rs, "questions", sp, list)
        if not questions:
            raise _err(f"{sp}.questions", "skill has no questions")
        by_level: dict[int, list[dict]] = {}
        for qi, q in enumerate(questions):
            level, built = _build_question(q, f"{sp}.questions[{qi}]", kid)
            by_level.setdefault(level, []).append(built)
        skills.append(Skill(
            id=kid, subject=sid, title=stitle,
            aliases=tuple(a.lower() for a in aliases),
            generate=_make_generate(kid, by_level)))

    raw_years = _req(data, "years", "$", dict)
    years: dict[int, YearSpec] = {}
    for ykey, yv in raw_years.items():
        yp = f"$.years[{ykey!r}]"
        try:
            year = int(ykey)
        except (TypeError, ValueError):
            raise _err(yp, "year key must be an integer") from None
        rows_raw = _req(yv, "rows", yp, list)
        rows: list[tuple[Topic, ...]] = []
        for ri, row in enumerate(rows_raw):
            rp = f"{yp}.rows[{ri}]"
            if not isinstance(row, list) or not 1 <= len(row) <= 2:
                raise _err(rp, "a row must be a list of 1 or 2 topics")
            topics = []
            for ti, t in enumerate(row):
                tp = f"{rp}[{ti}]"
                tid = _str(t, "id", tp)
                label = _str(t, "label", tp)
                tskills = _req(t, "skills", tp, list)
                if not tskills or any(not isinstance(k, str) or k not in seen for k in tskills):
                    raise _err(f"{tp}.skills", "must be a non-empty list of skill ids from this bank")
                kw = {}
                if "level_map" in t:
                    kw["level_map"] = _level_map(t["level_map"], f"{tp}.level_map")
                topics.append(Topic(id=tid, label=label, skills=tuple(tskills), **kw))
            rows.append(tuple(topics))
        ykw = {}
        if "past_paper_level_map" in yv:
            ykw["past_paper_level_map"] = _level_map(
                yv["past_paper_level_map"], f"{yp}.past_paper_level_map")
        years[year] = YearSpec(rows=tuple(rows), **ykw)
    if not years:
        raise _err("$.years", "no years")
    return Subject(id=sid, title=title, order=order, years=years), skills


def register_bank(reg: Registry, path: str) -> None:
    subject, skills = load_bank(path)
    reg.register(subject, skills)
