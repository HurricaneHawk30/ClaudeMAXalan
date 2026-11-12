"""Pure text-classification helpers."""
from __future__ import annotations

import re

_KEEP = set("'%=/^+-*().,")


def normalize(text: str) -> str:
    text = (text or "").lower().replace("’", "'").replace("‘", "'")
    text = "".join(c if (c.isalnum() or c.isspace() or c in _KEEP) else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()


def command_name(text: str) -> str | None:
    text = (text or "").strip()
    if not text.startswith("/"):
        return None
    first = text.split(None, 1)[0]
    return first.split("@", 1)[0].lower()


def normalize_code(text: str) -> str | None:
    if text is None:
        return None
    text = text.strip()
    if text.startswith("/"):
        return None
    code = re.sub(r"[\s\-]+", "", text).upper()
    if re.fullmatch(r"[A-Z0-9]{6,12}", code):
        return code
    return None


def parse_year(text: str) -> tuple[int, str] | None:
    t = (text or "").strip().lower().replace("—", "–")
    if re.fullmatch(r"(?:year\s*|yr\s*|y\s*)?1\s*[-–]\s*6", t):
        return 6, "Year 1–6"
    m = re.fullmatch(r"(?:year\s*|yr\s*|y\s*)?(\d{1,2})", t)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 13:
            return n, f"Year {n}"
    return None


_DISTRESS = (
    "kill myself", "want to die", "wanna die", "end my life", "end it all", "suicide", "suicidal",
    "self harm", "self-harm", "selfharm", "hurt myself", "hurting myself", "cut myself",
    "cutting myself", "don't want to live", "dont want to live", "no reason to live",
    "better off dead", "better off without me", "nobody would care if i", "being bullied",
    "abused", "abusing me", "not safe at home", "scared to go home",
)

_CHEAT = (
    "do my homework", "do my hw", "do my test", "do this test for me", "do it for me",
    "write my essay", "write an essay for me", "write my coursework", "test answers",
    "exam answers", "answers to the test", "answers to the exam", "answers for the test",
    "answers for the exam", "answer key", "give me the answers",
)

_SKIP_EXACT = {"skip", "next", "pass", "i don't know", "i dont know", "idk", "dunno", "no idea",
               "give up", "i give up", "show answer", "show me the answer"}
_HINT_EXACT = {"hint", "a hint", "give me a hint", "help", "help me", "stuck", "i'm stuck", "im stuck",
               "i don't get it", "i dont get it", "i don't understand", "i dont understand",
               "how do i start", "what do i do", "explain", "?"}
_HINT_WORDS = ("hint", "help", "stuck", "don't get", "dont get", "don't understand",
               "dont understand", "how do i", "how to")
_SKIP_WORDS = ("skip", "don't know", "dont know", "idk", "give up", "no idea")


def _contains(norm: str, phrase: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", norm) is not None


def is_distress(text: str) -> bool:
    norm = normalize(text)
    if not norm:
        return False
    if re.search(r"(?<![a-z0-9])kms(?![a-z0-9])", norm):
        return True
    return any(p in norm for p in _DISTRESS)


def is_cheat_request(text: str) -> bool:
    norm = normalize(text)
    return any(p in norm for p in _CHEAT)


def intent(text: str) -> str | None:
    if text is None or any(c.isdigit() for c in text):
        return None
    if text.strip() == "?":
        return "hint"
    norm = normalize(text)
    if not norm:
        return None
    if norm in _SKIP_EXACT:
        return "skip"
    if norm in _HINT_EXACT:
        return "hint"
    if any(_contains(norm, p) for p in _HINT_WORDS):
        return "hint"
    if any(_contains(norm, p) for p in _SKIP_WORDS):
        return "skip"
    return None
