"""Optional LLM helper. The bot is fully functional without it."""
from __future__ import annotations

import dataclasses
import json
import logging
import re
import urllib.error
import urllib.request
from typing import Protocol

from .content import Answer, Problem, check

log = logging.getLogger(__name__)

API_URL = "https://api.anthropic.com/v1/messages"

BASE_PROMPT = (
    "You are a friendly, patient tutor for secondary-school students (age 11–16) in the British school "
    "system, helping with {subject} (Year {year}). Reply in simple English, plain text only (no Markdown, "
    "no LaTeX), at most 80 words. Only help with schoolwork; if the student goes off-topic, kindly steer "
    "them back to the problem. Never do homework, write essays or give test answers for them — teach step "
    "by step instead. Never ask for personal information. The correct answer below was verified by a "
    "computer and is always right: never contradict it."
)

SAFETY_RULE = (
    " Safety comes first: if the student mentions harm, danger, abuse, bullying, self-harm or being very "
    "upset or unsafe, do NOT steer them back to the problem; kindly tell them to talk to a trusted adult "
    "(a parent, carer or teacher) as soon as possible, and to contact emergency services if they are in "
    "danger right now."
)

_SUFFIX = {
    "hint": " Do NOT reveal the answer or the final value. Give at most one next step." + SAFETY_RULE,
    "chat": " Do NOT reveal the answer or the final value. Give at most one next step." + SAFETY_RULE,
    "feedback": (" The student's answer was wrong. In 1–2 sentences, kindly explain where their working "
                 "most likely went wrong. Do not start with 'Not quite' and do not restate the correct answer."
                 + SAFETY_RULE),
    "pick": (" Your task: choose which skill from the list best matches what the student wants to practise. "
             "Reply with only the skill id exactly as written, or NONE if nothing matches."),
    "mark": (" Your task: mark the student's written answer against the mark scheme. Reply with only JSON "
             "like {\"marks\": 2, \"feedback\": \"one or two kind sentences\"}."),
}


class LLM(Protocol):
    def complete(self, system: str, user: str, max_tokens: int = 300) -> str | None: ...


class ClaudeLLM:
    def __init__(self, api_key: str, model: str, timeout: float = 20.0) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, system: str, user: str, max_tokens: int = 300) -> str | None:
        try:
            body = json.dumps({
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            }).encode("utf-8")
            req = urllib.request.Request(API_URL, data=body, method="POST", headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            })
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            blocks = payload.get("content") or []
            return "".join(b.get("text", "") for b in blocks
                           if isinstance(b, dict) and b.get("type") == "text").strip()
        except urllib.error.HTTPError as e:
            log.warning("LLM call failed: HTTP %s", e.code)
        except Exception as e:  # never raise into the engine
            log.warning("LLM call failed: %s", type(e).__name__)
        return None


def system_prompt(subject_title: str, year: int, mode: str) -> str:
    return BASE_PROMPT.format(subject=subject_title, year=year) + _SUFFIX.get(mode, "")


def clean(text: str, max_words: int = 80) -> str:
    text = re.sub(r"[*_`#]", "", text or "").strip()
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "…"
    return text


_NUM_TOKEN = re.compile(
    r"(?<![\w.])[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"          # 1,200 / 7.07 / -3
    r"(?:\s*/\s*\d+(?:\.\d+)?)?"                                     # 3/4
    r"(?:\s*(?:×|x|X|\*)\s*10\s*(?:(?:\^|\*\*)\s*\(?[-+−]?\d+\)?|[⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+))?"   # × 10^4
    r"(?:\s*(?:π|pi))?"
)


def _squash(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").lower().replace("−", "-").replace("×", "x").replace("*", "x"))


def _candidates(text: str, answer: Answer) -> list[str]:
    """Numbers and expressions in ``text`` that could be (an equivalent of) the answer."""
    if answer.kind == "expr":
        var = re.escape(answer.var or "x")
        runs = re.findall(rf"[0-9{var}{var.upper()}()+\-−*/^²³.×· ]+", text)
        return [r.strip() for r in runs if re.search(var, r, re.IGNORECASE) and re.search(r"[\d+\-−*/^²³()]", r)]
    return [m.group(0).strip() for m in _NUM_TOKEN.finditer(text)]


def leaks_answer(text: str, answer: Answer, problem_text: str = "") -> bool:
    """True if ``text`` gives away the answer.

    Either the display (lowercased, no spaces, len >= 2) is a substring, a number of the display
    appears as a standalone token, or any number / expression in the text has the answer's value
    (checked with the real checker, ignoring the required form: 0.75 for 3/4, 32000 for 3.2 × 10^4,
    7.07 for 7.1, 1,200 for 1200). Numbers and expressions copied from the question are ignored by
    the value test.
    """
    display = (answer.display or "").lower()
    squashed = re.sub(r"\s+", "", display)
    low = (text or "").lower()
    if len(squashed) >= 2 and squashed in re.sub(r"\s+", "", low):
        return True
    for num in re.findall(r"\d+(?:\.\d+)?", display):
        if re.search(r"(?<![\d.])" + re.escape(num) + r"(?![\d]|\.\d)", low):
            return True
    if answer.kind == "rubric" or not text:
        return False
    loose = dataclasses.replace(answer, form="any")
    question = _squash(problem_text)
    for cand in _candidates(text, answer):
        if not cand or (question and _squash(cand) in question):
            continue
        try:
            if check(loose, cand).status == "correct":
                return True
        except Exception:  # noqa: BLE001 - a checker problem must never break the LLM path
            continue
    return False


def _user_message(problem: Problem, student_text: str) -> str:
    return (f"Problem: {problem.text}\nVerified answer: {problem.answer.display}\n"
            f"Worked solution: {problem.solution}\nStudent's message: {(student_text or '')[:500]}")


def tutor_text(llm: LLM, mode: str, problem: Problem, student_text: str,
               subject_title: str, year: int) -> str | None:
    try:
        raw = llm.complete(system_prompt(subject_title, year, mode), _user_message(problem, student_text))
    except Exception as e:
        log.warning("LLM error: %s", type(e).__name__)
        return None
    if not raw:
        return None
    out = clean(raw)
    if not out:
        return None
    if mode in ("hint", "chat") and leaks_answer(out, problem.answer, problem.text):
        return None
    return out


def pick_skill(llm: LLM, text: str, skills: list[tuple[str, str]]) -> str | None:
    if not skills:
        return None
    listing = "\n".join(f"{sid}: {title}" for sid, title in skills)
    user = f"Skills:\n{listing}\nStudent wants to practise: {(text or '')[:300]}"
    try:
        raw = llm.complete(system_prompt("school subjects", 11, "pick"), user, max_tokens=30)
    except Exception as e:
        log.warning("LLM error: %s", type(e).__name__)
        return None
    if not raw:
        return None
    answer = raw.strip().strip("\"'`. \n")
    ids = {sid for sid, _ in skills}
    return answer if answer in ids else None


def mark_rubric(llm: LLM, problem: Problem, student_text: str) -> tuple[int, str] | None:
    a = problem.answer
    user = (f"Problem: {problem.text}\nModel answer: {a.display}\nMark scheme: {a.mark_scheme}\n"
            f"Maximum marks: {a.max_marks}\nStudent's answer: {(student_text or '')[:800]}")
    try:
        raw = llm.complete(system_prompt("", 11, "mark"), user, max_tokens=200)
    except Exception as e:
        log.warning("LLM error: %s", type(e).__name__)
        return None
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        marks = int(data["marks"])
        feedback = clean(str(data.get("feedback", "")))
    except (ValueError, KeyError, TypeError):
        return None
    return max(0, min(a.max_marks, marks)), feedback
