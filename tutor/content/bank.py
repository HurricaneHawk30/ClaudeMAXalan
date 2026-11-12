"""JSON question banks and packs (docs/ARCHITECTURE_V2.md section 2.4; v1 section 2.5).

A bank file (``tutor/subjects/banks/<subject_id>.json``) is a complete subject and is
loaded automatically.  A pack file (``tutor/subjects/packs/<subject_id>.json``) holds only
skills; a Python subject module loads it with ``load_pack``.  Every validation failure
raises ``BankError`` whose message starts with the JSON path of the problem.
"""
from __future__ import annotations

import copy
import json
import os
import re
from dataclasses import dataclass, fields, replace
from typing import Callable

from .base import (
    ANSWER_KINDS, SHORT_FORMS, Answer, BankItem, Mistake, Problem, Skill, Subject, Topic, YearSpec,
)
from .checker import check, short_typo_eligible
from .kinds import _choice_problem, _choice_semantics, _short_problem, _short_semantics, build_choice, build_short
from .registry import Registry
from . import words

_TUTOR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANKS_DIR = os.path.join(_TUTOR_DIR, "subjects", "banks")
PACKS_DIR = os.path.join(_TUTOR_DIR, "subjects", "packs")

MAX_TEXT = 600
MAX_SOLUTION = 300
MAX_NOTE = 40
MAX_RUBRIC = 600
MAX_AUTO_REJECTS = 20


class BankError(ValueError):
    """The question bank is invalid; the message starts with the JSON path."""


_ANSWER_KEYS = {f.name for f in fields(Answer)}
_V1_KINDS = tuple(k for k in ANSWER_KINDS if k not in ("choice", "short"))
_FORMS = {
    "number": ("any", "standard"),
    "fraction": ("any", "simplest", "mixed"),
    "expr": ("any", "expanded", "factorised"),
    "ratio": ("any", "simplest"),
}
_KEYS_BANK = {"subject", "skills", "years"}
_KEYS_PACK = {"subject_id", "skills"}
_KEYS_SUBJECT = {"id", "title", "order"}
_KEYS_SKILL = {"id", "title", "aliases", "questions"}
_KEYS_QUESTION = {"id", "level", "text", "topic_note", "solution", "hint", "answer", "choice", "short",
                  "rubric", "mistakes"}
_KEYS_CHOICE = {"options", "correct", "feedback"}
_KEYS_SHORT = {"accept", "reject", "form", "feedback"}
_KEYS_RUBRIC = {"model_answer", "mark_scheme", "max_marks"}
_KEYS_YEAR = {"rows", "past_paper_level_map"}
_KEYS_TOPIC = {"id", "label", "skills", "level_map"}
_KEYS_MISTAKE = {"answer", "feedback"}
_ANSWER_TYPES = ("answer", "choice", "short", "rubric")
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,24}$")


# ------------------------------------------------------------- helpers

def _err(path: str, msg: str) -> BankError:
    return BankError(f"{path}: {msg}")


def _obj(d: object, path: str, allowed: set[str]) -> dict:
    if not isinstance(d, dict):
        raise _err(path, f"expected an object, got {type(d).__name__}")
    unknown = sorted(set(d) - allowed)
    if unknown:
        raise _err(path, f"unknown key(s) {unknown}; allowed: {sorted(allowed)}")
    return d


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


def _int(d: dict, key: str, path: str, lo: int, hi: int) -> int:
    v = _req(d, key, path, int)
    assert isinstance(v, int)
    if not lo <= v <= hi:
        raise _err(f"{path}.{key}", f"must be an integer in {lo}..{hi}, got {v}")
    return v


def _clean(s: str) -> str:
    """Trailing periods stripped (solutions, hints and feedback never end with '.')."""
    return s.strip().rstrip(".").rstrip()


def _level_map(v: object, path: str) -> tuple:
    if (not isinstance(v, list) or len(v) != 5
            or any(isinstance(x, bool) or not isinstance(x, int) or not 1 <= x <= 5 for x in v)):
        raise _err(path, "must be a list of 5 integers in 1..5")
    return tuple(v)


def _num_str(v: object, path: str) -> str:
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise _err(path, "expected a number or a numeric string")
    return str(v)


def _stem_key(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", "", text.casefold()).split())


def _guard(errors: list[str] | None, fn: Callable, *args):
    """Run fn; in collect mode (errors is a list) record a BankError and return None."""
    try:
        return fn(*args)
    except BankError as e:
        if errors is None:
            raise
        errors.append(str(e))
        return None


# ------------------------------------------------------- v1 answer key

def _build_answer(d: object, path: str) -> Answer:
    d = _obj(d, path, _ANSWER_KEYS)
    kind = _req(d, "kind", path, str)
    if kind in ("choice", "short"):
        raise _err(f"{path}.kind", f"use the {kind!r} key of the question, not answer.kind = {kind!r}")
    if kind not in _V1_KINDS:
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


def _build_mistakes(raw: object, path: str, answer: Answer) -> tuple[Mistake, ...]:
    if not isinstance(raw, list):
        raise _err(path, "expected a list")
    out: list[Mistake] = []
    for i, m in enumerate(raw):
        mp = f"{path}[{i}]"
        m = _obj(m, mp, _KEYS_MISTAKE)
        feedback = _clean(_str(m, "feedback", mp))
        if not feedback:
            raise _err(f"{mp}.feedback", "must not be empty")
        if "answer" not in m:
            raise _err(mp, "missing field 'answer'")
        ma = _build_answer(m["answer"], f"{mp}.answer")
        if ma.kind == "rubric":
            raise _err(f"{mp}.answer.kind", "a mistake cannot be a rubric")
        if check(ma, ma.display).status != "correct":
            raise _err(f"{mp}.answer.display", "mistake display is not judged correct for itself")
        if answer.kind != "rubric" and check(answer, ma.display).status == "correct":
            continue  # coincides with the correct answer: dropped
        out.append(Mistake(ma, feedback))
    return tuple(out)


# ------------------------------------------------------------ questions

@dataclass
class _Q:
    path: str
    index: int
    qid: str | None
    level: int
    text: str                      # stem with the topic note, without options
    stem_key: str
    solution: str
    hint: str
    kind: str
    options: tuple = ()
    correct: int = 0
    cfeedback: tuple | None = None
    accept: tuple = ()
    reject: tuple = ()
    form: str = "any"
    sfeedback: dict | None = None
    answer: Answer | None = None   # v1 kinds and rubric
    mistakes: tuple = ()


def _parse_question(q: object, path: str, index: int) -> _Q:
    q = _obj(q, path, _KEYS_QUESTION)
    qid = None
    if "id" in q:
        qid = q["id"]
        if not isinstance(qid, str) or not _ID_RE.match(qid):
            raise _err(f"{path}.id", f"id must match [A-Za-z0-9_-]{{1,24}}, got {qid!r}")
    level = _int(q, "level", path, 1, 5)
    text = _str(q, "text", path).strip()
    solution = _clean(_str(q, "solution", path))
    hint = _clean(_str(q, "hint", path))
    if not solution:
        raise _err(f"{path}.solution", "must not be empty")
    if not hint:
        raise _err(f"{path}.hint", "must not be empty")
    if len(solution) > MAX_SOLUTION:
        raise _err(f"{path}.solution", f"too long ({len(solution)} > {MAX_SOLUTION} characters)")
    note = ""
    if "topic_note" in q:
        note = q["topic_note"]
        if not isinstance(note, str) or not note.strip():
            raise _err(f"{path}.topic_note", "must be a non-empty string")
        if len(note) > MAX_NOTE or "\n" in note or "\r" in note:
            raise _err(f"{path}.topic_note", f"must be at most {MAX_NOTE} characters with no newline")
        note = note.strip()
    present = [k for k in _ANSWER_TYPES if k in q]
    if len(present) != 1:
        raise _err(path, "a question needs exactly one of 'answer', 'choice', 'short' or 'rubric'"
                         + (f" (found {present})" if present else ""))
    if "mistakes" in q and present[0] != "answer":
        raise _err(f"{path}.mistakes", "'mistakes' is only allowed with 'answer'; use choice/short feedback")
    shown = f"[{note}] {text}" if note else text
    spec = _Q(path=path, index=index, qid=qid, level=level, text=shown, stem_key=_stem_key(text),
              solution=solution, hint=hint, kind=present[0])

    if present[0] == "choice":
        cp = f"{path}.choice"
        c = _obj(q["choice"], cp, _KEYS_CHOICE)
        options = _req(c, "options", cp, list)
        correct = _req(c, "correct", cp, int)
        fb = c.get("feedback")
        if fb is not None:
            if not isinstance(fb, list):
                raise _err(f"{cp}.feedback", "must be a list (null or text per option)")
            fb = [x if not isinstance(x, str) else (_clean(x) or x) for x in fb]
        msg = _choice_problem(options, correct, fb)
        if msg:
            raise _err(cp, msg)
        msg = _choice_semantics(tuple(options), correct)
        if msg:
            raise _err(cp, msg)
        spec.kind, spec.options, spec.correct = "choice", tuple(options), correct
        spec.cfeedback = tuple(fb) if fb is not None else None
    elif present[0] == "short":
        sp = f"{path}.short"
        s = _obj(q["short"], sp, _KEYS_SHORT)
        accept = _req(s, "accept", sp, list)
        reject = s.get("reject", [])
        form = s.get("form", "any")
        fb = s.get("feedback")
        if not isinstance(reject, list):
            raise _err(f"{sp}.reject", "must be a list of strings")
        if not isinstance(form, str) or form not in SHORT_FORMS:
            raise _err(f"{sp}.form", f"must be one of {list(SHORT_FORMS)}, got {form!r}")
        if fb is not None:
            if not isinstance(fb, dict):
                raise _err(f"{sp}.feedback", "must be an object {reject: text}")
            fb = {k: (_clean(v) or v) if isinstance(v, str) else v for k, v in fb.items()}
        msg = _short_problem(accept, reject, form, fb)
        if msg:
            raise _err(sp, msg)
        spec.kind, spec.accept, spec.reject, spec.form, spec.sfeedback = \
            "short", tuple(accept), tuple(reject), form, fb
    elif present[0] == "rubric":
        rp = f"{path}.rubric"
        r = _obj(q["rubric"], rp, _KEYS_RUBRIC)
        model = _str(r, "model_answer", rp)
        scheme = _str(r, "mark_scheme", rp)
        if len(model) > MAX_RUBRIC:
            raise _err(f"{rp}.model_answer", f"too long ({len(model)} > {MAX_RUBRIC} characters)")
        if len(scheme) > MAX_RUBRIC:
            raise _err(f"{rp}.mark_scheme", f"too long ({len(scheme)} > {MAX_RUBRIC} characters)")
        marks = _int(r, "max_marks", rp, 1, 12)
        spec.kind = "rubric"
        spec.answer = Answer("rubric", model.strip(), mark_scheme=scheme.strip(), max_marks=marks)
    else:
        ap = f"{path}.answer"
        answer = _build_answer(q["answer"], ap)
        if answer.kind != "rubric":
            v = check(answer, answer.display)
            if v.status != "correct":
                raise _err(f"{ap}.display", f"display {answer.display!r} is not judged correct (got {v.status})")
        spec.kind = answer.kind
        spec.answer = answer
        spec.mistakes = _build_mistakes(q.get("mistakes", []), f"{path}.mistakes", answer)
    return spec


# --------------------------------------------------------- auto-rejects

def _vocabulary(questions: list[_Q]) -> dict[tuple[str, int], list[tuple[int, str]]]:
    """Index of the file's vocabulary (normalised short accepts and choice options) by (first char, length)."""
    seen: set[str] = set()
    index: dict[tuple[str, int], list[tuple[int, str]]] = {}
    order = 0
    for q in questions:
        terms = [words.norm_form(a, q.form)[0] for a in q.accept] if q.kind == "short" else \
            [words.norm_any(o) for o in q.options] if q.kind == "choice" else []
        for t in terms:
            if not t or t in seen or not words.is_letters_spaces(t):
                continue
            seen.add(t)
            index.setdefault((t[0], len(t)), []).append((order, t))
            order += 1
    return index


def _auto_rejects(q: _Q, vocab: dict) -> tuple[str, ...]:
    if q.kind != "short" or q.form != "any":
        return ()
    keys = [words.norm_any(a) for a in q.accept]
    eligible = [k for k in keys if short_typo_eligible(k)]
    if not eligible:
        return ()
    own = set(keys)
    own_fold = {f for k in keys for f in (words.fold(k), words.fold_german(k))}
    listed = {words.norm_any(r) for r in q.reject}
    found: dict[str, tuple[int, int]] = {}
    for a in eligible:
        plurals = {a + "s", a + "es"}
        for ln in range(len(a) - 2, len(a) + 3):
            for order, v in vocab.get((a[0], ln), ()):
                if v in own or v in listed or v in plurals or a in (v + "s", v + "es"):
                    continue
                if words.fold(v) in own_fold or words.fold_german(v) in own_fold:
                    continue
                d = words.osa(v, a, 2)
                if d <= 2 and (v not in found or (d, order) < found[v]):
                    found[v] = (d, order)
    ranked = sorted(found, key=lambda v: found[v])[:MAX_AUTO_REJECTS]
    return tuple(ranked)


# ------------------------------------------------------------- rendering

def _render_fn(skill_id: str, ref: str, q: _Q, reject: tuple[str, ...]) -> Callable[[int], Problem]:
    level, text, solution, hint = q.level, q.text, q.solution, q.hint
    if q.kind == "choice":
        options, correct, fb = q.options, q.correct, q.cfeedback

        def render(seed: int) -> Problem:
            t, ans, mistakes = build_choice(text, options, correct, seed, fb, salt=ref)
            return Problem(skill_id, level, seed, t, ans, solution, hint, mistakes, ref)
    elif q.kind == "short":
        accept, form, sfb = q.accept, q.form, q.sfeedback

        def render(seed: int) -> Problem:
            ans, mistakes = build_short(accept, reject, form, sfb)
            return Problem(skill_id, level, seed, text, ans, solution, hint, mistakes, ref)
    else:
        answer, mistakes0 = q.answer, q.mistakes

        def render(seed: int) -> Problem:
            return Problem(skill_id, level, seed, text, copy.deepcopy(answer), solution, hint,
                           copy.deepcopy(mistakes0), ref)
    return render


def _is_word_char(c: str) -> bool:
    return c.isalnum() or c == "_"


def _word_in(needle: str, hay: str) -> bool:
    """``needle`` occurs in ``hay`` as whole words, case-insensitive (no regex: called thousands of times)."""
    n = needle.strip().casefold()
    if not n:
        return False
    h = hay.casefold()
    start = h.find(n)
    while start != -1:
        end = start + len(n)
        if (start == 0 or not _is_word_char(h[start - 1]) or not _is_word_char(n[0])) and \
                (end == len(h) or not _is_word_char(h[end]) or not _is_word_char(n[-1])):
            return True
        start = h.find(n, start + 1)
    return False


def _check_render(q: _Q, p: Problem) -> None:
    if len(p.text) > MAX_TEXT:
        raise _err(f"{q.path}.text", f"rendered text too long ({len(p.text)} > {MAX_TEXT} characters, "
                                     "including the topic note and the options)")
    leaks: list[str] = []
    if len(p.answer.display.strip()) >= 3:
        leaks.append(p.answer.display)
    if q.kind == "choice" and len(q.options[q.correct].strip()) >= 4:
        leaks.append(q.options[q.correct])
    if q.kind == "short":
        leaks += [a for a in q.accept if len(a.strip()) >= 4]
    for x in leaks:
        if _word_in(x, p.hint):
            raise _err(f"{q.path}.hint", f"the hint gives away the answer ({x!r})")


def _make_generate(skill_id: str, items: tuple[BankItem, ...]) -> Callable[[int, int], Problem]:
    by_level: dict[int, list[BankItem]] = {}
    for it in items:
        by_level.setdefault(it.level, []).append(it)
    levels = sorted(by_level)

    def generate(level: int, seed: int) -> Problem:
        if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 5:
            raise ValueError(f"level must be 1..5, got {level!r}")
        use = min(levels, key=lambda lv: (abs(lv - level), lv > level))
        its = by_level[use]
        p = its[seed % len(its)].render(seed)
        return p if p.level == level else replace(p, level=level)

    return generate


# ----------------------------------------------------------------- skills

@dataclass
class _SkillSpec:
    path: str
    id: str
    title: str
    aliases: tuple[str, ...]
    questions: list[_Q]


def _parse_skill(rs: object, sp: str, errors: list[str] | None) -> _SkillSpec:
    rs = _obj(rs, sp, _KEYS_SKILL)
    kid = _str(rs, "id", sp).strip()
    title = _str(rs, "title", sp).strip()
    aliases = _req(rs, "aliases", sp, list)
    if not aliases or any(not isinstance(a, str) or not a.strip() for a in aliases):
        raise _err(f"{sp}.aliases", "must be a non-empty list of non-empty strings")
    questions = _req(rs, "questions", sp, list)
    if not questions:
        raise _err(f"{sp}.questions", "skill has no questions")
    qs: list[_Q] = []
    ids: dict[str, int] = {}
    stems: dict[str, int] = {}
    for qi, raw in enumerate(questions):
        qp = f"{sp}.questions[{qi}]"
        q = _guard(errors, _parse_question, raw, qp, qi)
        if q is None:
            continue
        if q.qid is not None:
            if q.qid in ids:
                e = _err(f"{qp}.id", f"duplicate id {q.qid!r} (also questions[{ids[q.qid]}])")
                if errors is None:
                    raise e
                errors.append(str(e))
                continue
            ids[q.qid] = qi
        if q.stem_key in stems:
            e = _err(f"{qp}.text", f"duplicate stem (same text as questions[{stems[q.stem_key]}])")
            if errors is None:
                raise e
            errors.append(str(e))
            continue
        stems[q.stem_key] = qi
        qs.append(q)
    if not qs:
        raise _err(f"{sp}.questions", "no valid questions")
    return _SkillSpec(sp, kid, title, tuple(" ".join(a.split()).lower() for a in aliases), qs)


def _finish_skills(specs: list[_SkillSpec], subject_id: str, errors: list[str] | None) -> list[Skill]:
    vocab = _vocabulary([q for s in specs for q in s.questions])
    skills: list[Skill] = []
    for s in specs:
        items: list[BankItem] = []
        for q in s.questions:
            def one(q=q) -> BankItem:
                ref = f"{s.id}#{q.qid if q.qid is not None else q.index}"
                reject = q.reject
                if q.kind == "short":
                    reject = q.reject + _auto_rejects(q, vocab)
                    msg = _short_semantics(q.accept, reject, q.form)
                    if msg:
                        raise _err(f"{q.path}.short", msg)
                render = _render_fn(s.id, ref, q, reject)
                _check_render(q, render(0))
                return BankItem(ref=ref, level=q.level, kind=q.kind, render=render)
            it = _guard(errors, one)
            if it is not None:
                items.append(it)
        if not items:
            if errors is None:
                raise _err(f"{s.path}.questions", "no valid questions")
            continue
        its = tuple(items)
        skills.append(Skill(id=s.id, subject=subject_id, title=s.title, aliases=s.aliases,
                            generate=_make_generate(s.id, its), items=its))
    return skills


def _parse_skills(raw: object, path: str, errors: list[str] | None) -> list[_SkillSpec]:
    if not isinstance(raw, list):
        raise _err(path, "expected a list of skills")
    if not raw:
        raise _err(path, "no skills")
    specs: list[_SkillSpec] = []
    seen: dict[str, int] = {}
    for si, rs in enumerate(raw):
        sp = f"{path}[{si}]"
        spec = _guard(errors, _parse_skill, rs, sp, errors)
        if spec is None:
            continue
        if spec.id in seen:
            e = _err(f"{sp}.id", f"duplicate skill id {spec.id!r}")
            if errors is None:
                raise e
            errors.append(str(e))
            continue
        seen[spec.id] = si
        specs.append(spec)
    return specs


# ------------------------------------------------------------------ years

def _year_keys(key: str, path: str) -> list[int]:
    out = []
    for part in str(key).split(","):
        part = part.strip()
        if not part.isdigit() or not 1 <= int(part) <= 13:
            raise _err(path, f"year key must be a year 1..13 or a comma list like \"10,11\", got {key!r}")
        out.append(int(part))
    if len(set(out)) != len(out):
        raise _err(path, f"year {key!r} lists a year twice")
    return out


def _parse_years(raw: object, skill_ids: set[str], errors: list[str] | None) -> dict[int, YearSpec]:
    if not isinstance(raw, dict):
        raise _err("$.years", "expected an object")
    years: dict[int, YearSpec] = {}
    topic_ids: dict[str, str] = {}
    for ykey, yv in raw.items():
        yp = f"$.years[{ykey!r}]"

        def one_year(ykey=ykey, yv=yv, yp=yp) -> None:
            ys = _year_keys(ykey, yp)
            yv = _obj(yv, yp, _KEYS_YEAR)
            rows_raw = _req(yv, "rows", yp, list)
            if not rows_raw:
                raise _err(f"{yp}.rows", "no rows")
            ykw = {}
            if "past_paper_level_map" in yv:
                ykw["past_paper_level_map"] = _level_map(yv["past_paper_level_map"], f"{yp}.past_paper_level_map")
            parsed_rows: list[list[tuple[str, str, tuple, dict, str]]] = []
            for ri, row in enumerate(rows_raw):
                rp = f"{yp}.rows[{ri}]"
                if not isinstance(row, list) or not 1 <= len(row) <= 2:
                    raise _err(rp, "a row must be a list of 1 or 2 topics")
                prow = []
                for ti, t in enumerate(row):
                    tp = f"{rp}[{ti}]"
                    t = _obj(t, tp, _KEYS_TOPIC)
                    tid = _str(t, "id", tp).strip()
                    label = _str(t, "label", tp).strip()
                    tskills = _req(t, "skills", tp, list)
                    if not tskills or any(not isinstance(k, str) or k not in skill_ids for k in tskills):
                        bad = [k for k in tskills if not isinstance(k, str) or k not in skill_ids]
                        raise _err(f"{tp}.skills", f"must be a non-empty list of skill ids from this file"
                                                   + (f" (unknown: {bad})" if bad else ""))
                    kw = {}
                    if "level_map" in t:
                        kw["level_map"] = _level_map(t["level_map"], f"{tp}.level_map")
                    prow.append((tid, label, tuple(tskills), kw, tp))
                parsed_rows.append(prow)
            for y in ys:
                if y in years:
                    raise _err(yp, f"year {y} is defined twice")
                rows = []
                for prow in parsed_rows:
                    topics = []
                    for tid, label, tskills, kw, tp in prow:
                        real = tid.replace("{year}", str(y))
                        if real in topic_ids:
                            raise _err(f"{tp}.id", f"duplicate topic id {real!r} (put {{year}} in ids "
                                                   "under a multi-year key)")
                        topic_ids[real] = tp
                        topics.append(Topic(id=real, label=label, skills=tskills, **kw))
                    rows.append(tuple(topics))
                years[y] = YearSpec(rows=tuple(rows), **ykw)

        _guard(errors, one_year)
    if not years and errors is None:
        raise _err("$.years", "no years")
    return years


# ------------------------------------------------------------- top level

def _read_json(path: str) -> object:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as e:
        raise BankError(f"$: cannot read {path}: {e.strerror or e}") from e
    except (ValueError, RecursionError) as e:
        raise BankError(f"$: invalid JSON in {path}: {e}") from e


def parse_bank_data(data: object, errors: list[str] | None = None) -> tuple[Subject | None, list[Skill]]:
    """Validate and build a bank.  With ``errors`` (a list) problems are collected, not raised."""
    data = _obj(data, "$", _KEYS_BANK)
    sj = _obj(_req(data, "subject", "$", dict), "$.subject", _KEYS_SUBJECT)
    sid = _str(sj, "id", "$.subject").strip()
    title = _str(sj, "title", "$.subject").strip()
    order = _req(sj, "order", "$.subject", int)
    specs = _parse_skills(_req(data, "skills", "$", list), "$.skills", errors)
    skills = _finish_skills(specs, sid, errors)
    years = _parse_years(_req(data, "years", "$", dict), {s.id for s in skills}, errors)
    if not years:
        return None, skills
    return Subject(id=sid, title=title, order=order, years=years), skills


def parse_pack_data(data: object, subject_id: str, errors: list[str] | None = None) -> list[Skill]:
    data = _obj(data, "$", _KEYS_PACK)
    sid = _req(data, "subject_id", "$", str)
    if sid != subject_id:
        raise _err("$.subject_id", f"is {sid!r}, but the pack was loaded for subject {subject_id!r}")
    raw = _req(data, "skills", "$", list)
    for si, rs in enumerate(raw):
        kid = rs.get("id") if isinstance(rs, dict) else None
        if isinstance(kid, str) and not kid.startswith(subject_id + "."):
            e = _err(f"$.skills[{si}].id", f"skill id {kid!r} must start with {subject_id + '.'!r}")
            if errors is None:
                raise e
            errors.append(str(e))
    specs = _parse_skills(raw, "$.skills", errors)
    specs = [s for s in specs if s.id.startswith(subject_id + ".")]
    return _finish_skills(specs, subject_id, errors)


_BANK_CACHE: dict[tuple, tuple[Subject, list[Skill]]] = {}
_PACK_CACHE: dict[tuple, list[Skill]] = {}


def _file_key(path: str) -> tuple:
    real = os.path.realpath(path)
    try:
        st = os.stat(real)
    except OSError as e:
        raise BankError(f"$: cannot read {path}: {e.strerror or e}") from e
    return real, st.st_mtime_ns, st.st_size


def load_bank(path: str) -> tuple[Subject, list[Skill]]:
    """A complete subject from a bank file; cached by (realpath, mtime_ns, size)."""
    key = _file_key(path)
    hit = _BANK_CACHE.get(key)
    if hit is not None:
        return hit
    subject, skills = parse_bank_data(_read_json(path))
    assert subject is not None
    out = (subject, skills)
    _BANK_CACHE[key] = out
    return out


def register_bank(reg: Registry, path: str) -> None:
    subject, skills = load_bank(path)
    reg.register(subject, skills)


def pack_path(name_or_path: str) -> str:
    if os.sep in name_or_path or "/" in name_or_path or name_or_path.endswith(".json"):
        return name_or_path
    return os.path.join(PACKS_DIR, name_or_path + ".json")


def load_pack(name_or_path: str, subject_id: str) -> list[Skill]:
    """Skills of a pack file ("biology" -> PACKS_DIR/biology.json); cached like load_bank."""
    if not isinstance(name_or_path, str) or not name_or_path:
        raise BankError("$: load_pack needs a pack name or path")
    path = pack_path(name_or_path)
    key = _file_key(path) + (subject_id,)
    hit = _PACK_CACHE.get(key)
    if hit is not None:
        return hit
    skills = parse_pack_data(_read_json(path), subject_id)
    _PACK_CACHE[key] = skills
    return skills
