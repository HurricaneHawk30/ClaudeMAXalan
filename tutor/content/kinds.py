"""Builders for the ``choice`` and ``short`` answer kinds (docs/ARCHITECTURE_V2.md section 2.2).

Both builders validate their input (section 2.4 rules 7 and 8) and raise ``ValueError``
with a readable message.  Validation results are cached per distinct option / answer set,
so rendering the same question again is cheap.
"""
from __future__ import annotations

import functools
import random
import re
from typing import Mapping, Sequence

from .base import CHOICE_LETTERS, SHORT_FORMS, Answer, Mistake
from . import words

MAX_OPTION = 120
MAX_SHORT = 80

_BAN_ALL = re.compile(r"\b(all|none|both|neither) of (the )?(above|these)\b", re.IGNORECASE)
_BAN_LETTERS = re.compile(r"\b[A-E]\s*(and|or|&|,)\s*[A-E]\b")
_BAN_LONE = re.compile(r"^\(?[A-Ea-e]\)?$")
_BAN_PREFIX = re.compile(r"^[A-E][).:]\s")


def shuffle_order(n: int, seed: int) -> list[int]:
    """Displayed order of n options for this seed (deterministic)."""
    order = list(range(n))
    random.Random(f"choice:{seed}").shuffle(order)
    return order


def letters_text(n: int) -> str:
    """3 -> "A, B or C"; 4 -> "A, B, C or D"; 5 -> "A, B, C, D or E"."""
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= len(CHOICE_LETTERS):
        raise ValueError(f"letters_text: n must be 1..{len(CHOICE_LETTERS)}, got {n!r}")
    letters = list(CHOICE_LETTERS[:n])
    if n == 1:
        return letters[0]
    return ", ".join(letters[:-1]) + " or " + letters[-1]


# ----------------------------------------------------------------- choice

def _choice_problem(options: Sequence[str], correct: int, feedback) -> str | None:
    """The first broken rule-7 condition as text, or None."""
    if isinstance(options, (str, bytes)) or not isinstance(options, Sequence):
        return "options must be a list of strings"
    n = len(options)
    if not 3 <= n <= len(CHOICE_LETTERS):
        return f"needs 3 to 5 options, got {n}"
    for i, o in enumerate(options):
        if not isinstance(o, str):
            return f"option {i} is not a string"
        if not o.strip() or len(o) > MAX_OPTION:
            return f"option {i} must be 1..{MAX_OPTION} characters, got {len(o)}"
        if "\n" in o or "\r" in o:
            return f"option {i} contains a newline"
        if _BAN_ALL.search(o):
            return f"option {i} {o!r}: no 'all/none/both/neither of the above' options"
        if _BAN_LETTERS.search(o):
            return f"option {i} {o!r}: options must not refer to other letters (e.g. 'A and B')"
        if _BAN_LONE.match(o.strip()):
            return f"option {i} {o!r}: a lone letter is not allowed as an option"
        if _BAN_PREFIX.match(o):
            return f"option {i} {o!r}: must not start like a letter label ('A) ')"
    keys = [words.fold(words.norm_any(o)) for o in options]
    for i, k in enumerate(keys):
        if not k:
            return f"option {i} {options[i]!r} is empty after normalisation"
        if k in keys[:i]:
            return f"options {keys.index(k)} and {i} are the same after normalisation ({k!r})"
    if isinstance(correct, bool) or not isinstance(correct, int) or not 0 <= correct < n:
        return f"correct must be an integer 0..{n - 1}, got {correct!r}"
    if feedback is not None:
        if isinstance(feedback, (str, bytes)) or not isinstance(feedback, Sequence) or len(feedback) != n:
            return f"feedback must be a list of {n} entries (null or text), one per option"
        for i, fb in enumerate(feedback):
            if fb is not None and (not isinstance(fb, str) or not fb.strip()):
                return f"feedback {i} must be null or a non-empty string"
        if feedback[correct] is not None:
            return "feedback for the correct option must be null"
    return None


@functools.lru_cache(maxsize=8192)
def _choice_semantics(options: tuple[str, ...], correct: int) -> str | None:
    """Rule 7, last point: on the seed-0 render the display is correct and every other letter wrong."""
    from .checker import check
    order = shuffle_order(len(options), 0)
    shown = [options[i] for i in order]
    c = order.index(correct)
    ans = Answer("choice", f"{CHOICE_LETTERS[c]}) {shown[c]}", {"options": shown, "correct": c})
    v = check(ans, ans.display)
    if v.status != "correct" or v.feedback:
        return f"display {ans.display!r} is not judged correct by the checker (got {v.status})"
    for j in range(len(shown)):
        if j != c and check(ans, CHOICE_LETTERS[j]).status != "wrong":
            return f"letter {CHOICE_LETTERS[j]} is not judged wrong"
    return None


def choice_error(options: Sequence[str], correct: int, feedback=None) -> str | None:
    """Why these choice inputs break rule 7, or None when they are valid."""
    msg = _choice_problem(options, correct, feedback)
    if msg is None:
        msg = _choice_semantics(tuple(options), correct)
    return msg


def build_choice(stem: str, options: Sequence[str], correct: int, seed: int,
                 feedback: Sequence[str | None] | None = None) -> tuple[str, Answer, tuple[Mistake, ...]]:
    """(text, answer, mistakes) for a multiple-choice question, options shuffled by ``seed``."""
    if not isinstance(stem, str) or not stem.strip():
        raise ValueError("choice: the stem must be a non-empty string")
    msg = choice_error(options, correct, feedback)
    if msg:
        raise ValueError(f"choice: {msg}")
    n = len(options)
    order = shuffle_order(n, seed)
    shown = [options[i] for i in order]
    c = order.index(correct)
    text = stem.rstrip() + "\n\n" + "\n".join(f"{L}) {opt}" for L, opt in zip(CHOICE_LETTERS, shown))
    answer = Answer("choice", f"{CHOICE_LETTERS[c]}) {shown[c]}", {"options": list(shown), "correct": c})
    mistakes = []
    if feedback is not None:
        for j, orig in enumerate(order):
            fb = feedback[orig]
            if j == c or fb is None:
                continue
            mistakes.append(Mistake(
                Answer("choice", f"{CHOICE_LETTERS[j]}) {shown[j]}", {"options": list(shown), "correct": j}), fb))
    return text, answer, tuple(mistakes)


# ------------------------------------------------------------------ short

def _short_problem(accept, reject, form, feedback) -> str | None:
    if form not in SHORT_FORMS:
        return f"form must be one of {', '.join(SHORT_FORMS)}, got {form!r}"
    if isinstance(accept, (str, bytes)) or not isinstance(accept, Sequence) or not accept:
        return "accept must be a non-empty list of strings"
    keys = []
    for i, a in enumerate(accept):
        if not isinstance(a, str) or not 1 <= len(a) <= MAX_SHORT or not a.strip():
            return f"accept {i} must be a string of 1..{MAX_SHORT} characters"
        k = words.norm_form(a, form)[0]
        if not k:
            return f"accept {i} {a!r} is empty after normalisation"
        keys.append(k)
    if isinstance(reject, (str, bytes)) or not isinstance(reject, Sequence):
        return "reject must be a list of strings"
    folding = form in ("any", "strict")
    a_fold = {f for k in keys for f in (words.fold(k), words.fold_german(k))} if folding else set()
    for i, r in enumerate(reject):
        if not isinstance(r, str) or not r.strip():
            return f"reject {i} must be a non-empty string"
        k = words.norm_form(r, form)[0]
        if not k:
            return f"reject {i} {r!r} is empty after normalisation"
        if k in keys:
            return f"reject {i} {r!r} equals an accepted answer after normalisation"
        if folding and (words.fold(k) in a_fold or words.fold_german(k) in a_fold):
            return f"reject {i} {r!r} equals an accepted answer once accents are ignored"
    if feedback is not None:
        if not isinstance(feedback, Mapping):
            return "feedback must be an object {reject: text}"
        for k, v in feedback.items():
            if k not in reject:
                return f"feedback key {k!r} is not in reject"
            if not isinstance(v, str) or not v.strip():
                return f"feedback for {k!r} must be a non-empty string"
    return None


@functools.lru_cache(maxsize=8192)
def _short_semantics(accept: tuple[str, ...], reject: tuple[str, ...], form: str) -> str | None:
    from .checker import check
    ans = Answer("short", accept[0], {"accept": list(accept), "reject": list(reject)}, form=form)
    v = check(ans, ans.display)
    if v.status != "correct" or v.feedback:
        got = v.status + (f" with note {v.feedback!r}" if v.feedback else "")
        return f"display {ans.display!r} is not judged correct by the checker (got {got})"
    for r in reject:
        v = check(ans, r)
        if v.status != "wrong":
            return f"reject {r!r} is not judged wrong (got {v.status})"
    return None


def short_error(accept: Sequence[str], reject: Sequence[str] = (), form: str = "any",
                feedback: Mapping[str, str] | None = None) -> str | None:
    """Why these short-answer inputs break rule 8, or None when they are valid."""
    msg = _short_problem(accept, reject, form, feedback)
    if msg is None:
        msg = _short_semantics(tuple(accept), tuple(reject), form)
    return msg


def build_short(accept: Sequence[str], reject: Sequence[str] = (), form: str = "any",
                feedback: Mapping[str, str] | None = None) -> tuple[Answer, tuple[Mistake, ...]]:
    """(answer, mistakes) for a short word / phrase answer; display = accept[0]."""
    msg = short_error(accept, reject, form, feedback)
    if msg:
        raise ValueError(f"short: {msg}")
    answer = Answer("short", accept[0], {"accept": list(accept), "reject": list(reject)}, form=form)
    mistakes = []
    if feedback:
        for r in reject:
            fb = feedback.get(r)
            if fb:
                mistakes.append(Mistake(Answer("short", r, {"accept": [r], "reject": []}, form=form), fb))
    return answer, tuple(mistakes)
