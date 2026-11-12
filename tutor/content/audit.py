"""Content self-checks: ``python3 -m tutor audit [--subject ID | --file PATH]``.

docs/ARCHITECTURE_V2.md sections 2.6 and 7.  Every source (subject module or bank file) is
loaded on its own, so one broken file never hides the others.  Output: one line per skill

    {skill_id}: bank|gen items={n} L1-5={a}/{b}/{c}/{d}/{e} choice={x}% short={y}% rubric={z}%

followed by ``  ERROR: ...`` and ``  WARN: ...`` lines.  Exit code 0 = no ERROR lines.

Besides the bank validation (section 2.4) and lint rules L1-L11, the audit runs the same
per-item consistency checks as tests/test_content_banks.py, so content that passes the audit
is expected to pass the tests.  For generator skills ("gen" lines), L1-5 counts the distinct
problems among 20 seeds per level and the kind shares come from those 100 problems.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable, TextIO

from .base import CHOICE_LETTERS, MY_OWN_TOPIC_LABEL, PAST_PAPER_LABEL, Problem, Skill, Subject, \
    problem_from_json, problem_to_json
from .bank import BANKS_DIR, PACKS_DIR, BankError, known_words, parse_bank_data, parse_pack_data, _read_json
from .checker import FORM_CASE, NOTE_ACCENTS, NOTE_SPELLING, TYPO_MIN_WORD, check, short_typo_eligible
from .fmt import _hint_leaks             # the same rule fmt.build applies (2+ chars as a token, 3+ anywhere)
from .registry import (RESERVED_LABELS, Registry, _norm_label, _subject_modules, bank_files, load_registry,
                       match_skill_ids, register_module)
from . import words

FROZEN = frozenset({"maths", "physics"})
GEN_SEEDS = range(20)
GEN_DETERMINISM_SEEDS = 5          # generated twice and compared (the first seeds of every level)
ITEM_SEEDS = (0, 1)
VARIATION_SEEDS = range(20)

# section 4: id -> (order, title)
SUBJECTS_V2 = {
    "maths": (10, "Maths"), "english_language": (12, "English Language"),
    "english_literature": (14, "English Literature"), "biology": (16, "Biology"),
    "chemistry": (18, "Chemistry"), "physics": (20, "Physics"), "further_maths": (22, "Further Maths"),
    "statistics": (24, "Statistics"), "computer_science": (26, "Computer Science"),
    "astronomy": (28, "Astronomy"), "history": (30, "History"), "geography": (32, "Geography"),
    "religious_studies": (34, "Religious Studies"), "citizenship": (36, "Citizenship"),
    "classical_civilisation": (38, "Classical Civ"), "psychology": (40, "Psychology"),
    "sociology": (42, "Sociology"), "economics": (44, "Economics"), "business": (46, "Business"),
    "media_studies": (48, "Media Studies"), "film_studies": (50, "Film Studies"), "french": (52, "French"),
    "spanish": (54, "Spanish"), "german": (56, "German"), "italian": (58, "Italian"),
    "russian": (60, "Russian"), "latin": (62, "Latin"), "arabic": (64, "Arabic"),
    "mandarin": (66, "Mandarin Chinese"), "music": (68, "Music"), "drama": (70, "Drama"),
    "design_technology": (72, "Design & Tech"), "food_nutrition": (74, "Food & Nutrition"),
    "pe": (76, "PE"), "art_design": (78, "Art & Design"),
}
# section 5: rubric items allowed (L4) and the mix of every bank skill
RUBRIC_SUBJECTS = frozenset({
    "english_language", "english_literature", "history", "geography", "religious_studies", "citizenship",
    "classical_civilisation", "psychology", "sociology", "economics", "business", "media_studies",
    "film_studies", "drama"})
MIXES = {sid: "M1" for sid in RUBRIC_SUBJECTS}
MIXES.update({sid: "M2" for sid in ("statistics", "biology", "chemistry", "computer_science", "astronomy",
                                     "music", "design_technology", "food_nutrition", "pe", "art_design")})
MIXES.update({sid: "M3" for sid in ("french", "spanish", "german", "italian", "russian", "latin")})
MIXES.update({sid: "M4" for sid in ("arabic", "mandarin")})

COMMAND_WORDS = frozenset({"help", "hint", "skip", "pass", "next", "explain"})
_SAFETY_WORDS = re.compile(r"\b(suicid\w*|self[- ]?harm\w*|overdos\w*|abused|bullied|nudes)\b", re.IGNORECASE)
_MARKDOWN = re.compile(r"\*\*|`|\$|\\")
_ARABIC = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
_HANZI = re.compile(r"[一-鿿㐀-䶿]")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")
_BUTTONS = (PAST_PAPER_LABEL, MY_OWN_TOPIC_LABEL, "🎓 Change year", "📘 Change subject",
            "⚙️ Change year / topic", "Year 1–6") + tuple(f"Year {y}" for y in range(1, 14))


# ------------------------------------------------------------------ report

@dataclass
class _Entry:
    header: str
    msgs: list[tuple[str, str]] = field(default_factory=list)     # (ERROR|WARN, text)


class Report:
    def __init__(self) -> None:
        self.entries: list[_Entry] = []
        self._by_key: dict[str, _Entry] = {}

    def entry(self, key: str, header: str | None = None) -> _Entry:
        e = self._by_key.get(key)
        if e is None:
            e = _Entry(header if header is not None else key)
            self._by_key[key] = e
            self.entries.append(e)
        elif header is not None:
            e.header = header
        return e

    def error(self, key: str, msg: str) -> None:
        self.entry(key).msgs.append(("ERROR", msg))

    def warn(self, key: str, msg: str) -> None:
        self.entry(key).msgs.append(("WARN", msg))

    @property
    def errors(self) -> int:
        return sum(1 for e in self.entries for lvl, _ in e.msgs if lvl == "ERROR")

    def write(self, out: TextIO, max_per_entry: int = 40) -> None:
        for e in self.entries:
            print(e.header, file=out)
            shown = e.msgs[:max_per_entry]
            for lvl, msg in shown:
                print(f"  {lvl}: {msg}", file=out)
            if len(e.msgs) > len(shown):
                rest = Counter(lvl for lvl, _ in e.msgs[len(shown):])
                print(f"  ERROR: ... and {len(e.msgs) - len(shown)} more ({dict(rest)})"
                      if rest.get("ERROR") else f"  WARN: ... and {len(e.msgs) - len(shown)} more", file=out)


def _pct(x: int, n: int) -> int:
    return int(100 * x / n + 0.5) if n else 0


def _skill_header(sk: Skill, problems: list[Problem] | None = None) -> str:
    if sk.items:
        lv = Counter(it.level for it in sk.items)
        kinds = Counter(it.kind for it in sk.items)
        n = len(sk.items)
        return (f"{sk.id}: bank items={n} L1-5={'/'.join(str(lv[i]) for i in range(1, 6))} "
                f"choice={_pct(kinds['choice'], n)}% short={_pct(kinds['short'], n)}% "
                f"rubric={_pct(kinds['rubric'], n)}%")
    problems = problems or []
    distinct = [len({p.text for p in problems if p.level == lv}) for lv in range(1, 6)]
    kinds = Counter(p.answer.kind for p in problems)
    n = len(problems)
    return (f"{sk.id}: gen items=0 L1-5={'/'.join(map(str, distinct))} "
            f"choice={_pct(kinds['choice'], n)}% short={_pct(kinds['short'], n)}% rubric={_pct(kinds['rubric'], n)}%")


# ----------------------------------------------------------- per problem

def _fold_plain(s: str) -> str:
    return words.fold(s)


def _check_choice_problem(rep: Report, key: str, where: str, p: Problem) -> None:
    a = p.answer
    opts, c = a.value["options"], a.value["correct"]
    listing = "\n".join(f"{CHOICE_LETTERS[i]}) {o}" for i, o in enumerate(opts))
    if not p.text.endswith("\n\n" + listing):
        rep.error(key, f"{where}: the text does not end with the options in displayed order")
    fb = {m.answer.display: m.feedback for m in p.mistakes}
    for j, o in enumerate(opts):
        v = check(a, CHOICE_LETTERS[j], p.mistakes)
        if j == c:
            if (v.status, v.feedback) != ("correct", ""):
                rep.error(key, f"{where}: the correct letter is judged {v.status}")
            if check(a, CHOICE_LETTERS[j].lower(), p.mistakes).status != "correct":
                rep.error(key, f"{where}: the lower-case correct letter is not accepted")
            v = check(a, o, p.mistakes)
            if v.status != "correct":
                rep.error(key, f"{where}: typing the correct option text {o!r} is judged {v.status} "
                               "(another option may look the same once filler words are removed)")
        else:
            if v.status != "wrong":
                rep.error(key, f"{where}: letter {CHOICE_LETTERS[j]} is judged {v.status}")
            vo = check(a, o, p.mistakes)
            if vo.status == "correct":
                rep.error(key, f"{where}: typing the wrong option text {o!r} is judged correct")
            elif vo.status != "wrong":
                rep.warn(key, f"{where}: typing the wrong option text {o!r} is judged {vo.status} "
                              "(it looks like another option)")
            want = fb.get(f"{CHOICE_LETTERS[j]}) {o}", "")
            if v.feedback != want:
                rep.error(key, f"{where}: letter {CHOICE_LETTERS[j]} feedback {v.feedback!r} != {want!r}")


def swap_typo(key: str, known: frozenset = frozenset()) -> str | None:
    """A typo the checker must accept (section 10.2): two neighbouring letters swapped in the second half
    of the longest word (5+ letters, never its first letter); None when there is no such swap or the
    result is a real word from ``known``."""
    ws = key.split()
    if not ws:
        return None
    j = max(range(len(ws)), key=lambda k: len(ws[k]))
    w = ws[j]
    if len(w) < TYPO_MIN_WORD:
        return None
    i = next((k for k in range(max(1, len(w) // 2), len(w) - 1) if w[k] != w[k + 1]), None)
    if i is None:
        return None
    typo = w[:i] + w[i + 1] + w[i] + w[i + 2:]
    if typo in known or words.fold(typo) in known:
        return None
    ws[j] = typo
    return " ".join(ws)


def _check_short_problem(rep: Report, key: str, where: str, p: Problem) -> None:
    a = p.answer
    accept, reject, form = a.value["accept"], a.value["reject"], a.form
    fb = {m.answer.display: m.feedback for m in p.mistakes}
    for x in accept:
        v = check(a, x, p.mistakes)
        if (v.status, v.feedback) != ("correct", ""):
            rep.error(key, f"{where}: accept {x!r} is judged {v.status}"
                           + (f" with note {v.feedback!r}" if v.feedback else ""))
    disp = a.display
    if form != "case" and check(a, disp.upper(), p.mistakes).status != "correct":
        rep.error(key, f"{where}: upper-case {disp.upper()!r} is not accepted")
    if form == "any" and not re.match(r"(?i)(the|a|an)\b", disp) and not disp.strip().isdigit():
        v = check(a, "the " + disp, p.mistakes)
        if v.status != "correct":
            rep.error(key, f"{where}: 'the {disp}' is judged {v.status}")
    if form in ("any", "strict"):
        folded = _fold_plain(disp)
        others = {words.norm_form(_fold_plain(x), form)[0] for x in list(accept[1:]) + list(reject)}
        fk = words.norm_form(folded, form)[0]
        if folded != disp and fk not in others and fk != words.norm_form(disp, form)[0]:
            v = check(a, folded, p.mistakes)
            if (v.status, v.feedback) != ("correct", NOTE_ACCENTS.format(answer=disp)):
                rep.error(key, f"{where}: accent-free {folded!r} is judged {v.status} note={v.feedback!r}")
    if form == "case" and disp.lower() != disp and disp.lower() not in {x.lower() for x in reject}:
        v = check(a, disp.lower(), p.mistakes)
        if (v.status, v.feedback) != ("wrong", FORM_CASE):
            rep.error(key, f"{where}: lower-case {disp.lower()!r} is judged {v.status} note={v.feedback!r}")
    if form == "any":
        nd = words.norm_any(disp)
        if short_typo_eligible(nd) and nd.isascii():
            t = swap_typo(nd, known_words())
            if t is not None:
                rn = [words.norm_any(r) for r in reject]
                an = {words.norm_any(x) for x in accept}
                if t not in rn and t not in an and all(words.osa(t, r) > 1 for r in rn):
                    v = check(a, t, p.mistakes)
                    if v.status != "correct" or v.feedback not in {NOTE_SPELLING.format(answer=x) for x in accept}:
                        rep.error(key, f"{where}: the typo {t!r} is judged {v.status} note={v.feedback!r}")
    for r in reject:
        v = check(a, r, p.mistakes)
        if v.status != "wrong":
            rep.error(key, f"{where}: reject {r!r} is judged {v.status}")
        elif r in fb and v.feedback != fb[r]:
            rep.error(key, f"{where}: reject {r!r} feedback {v.feedback!r} != {fb[r]!r}")


def _perturb(a) -> str | None:
    if a.kind == "choice":
        c = a.value["correct"]
        return next(CHOICE_LETTERS[j] for j in range(len(a.value["options"])) if j != c)
    if a.kind == "short":
        return "qq" + a.display + "qq"
    return None


def _check_problem(rep: Report, key: str, where: str, p: Problem, again: Problem) -> None:
    if p != again:
        rep.error(key, f"{where}: not deterministic")
        return
    try:
        if problem_from_json(problem_to_json(p)) != p:
            rep.error(key, f"{where}: JSON round trip differs")
    except (TypeError, ValueError) as e:
        rep.error(key, f"{where}: not JSON serialisable ({e})")
    if len(p.text) > 600:
        rep.error(key, f"{where}: text longer than 600 characters ({len(p.text)})")
    if len(p.solution) > 300 or p.solution.rstrip().endswith("."):
        rep.error(key, f"{where}: solution longer than 300 characters or ends with a period")
    a = p.answer
    if a.kind == "rubric":
        if check(a, "anything at all").status != "unmarkable":
            rep.error(key, f"{where}: rubric is not unmarkable")
        return
    v = check(a, a.display, p.mistakes)
    if (v.status, v.feedback) != ("correct", ""):
        rep.error(key, f"{where}: display {a.display!r} is judged {v.status}"
                       + (f" with note {v.feedback!r}" if v.feedback else ""))
        return
    pt = _perturb(a)
    if pt and check(a, pt, p.mistakes).status == "correct":
        rep.error(key, f"{where}: the near miss {pt!r} is judged correct")
    if a.kind == "choice":
        _check_choice_problem(rep, key, where, p)
    elif a.kind == "short":
        _check_short_problem(rep, key, where, p)


class _Letters(list):
    n: int = 0


def _choice_letters(rep: Report, key: str, it) -> "_Letters | None":
    """Correct-letter positions over VARIATION_SEEDS, from the shuffle (cross-checked with real renders)."""
    from .kinds import shuffle_order
    try:
        p0 = it.render(0)
        opts = p0.answer.value["options"]
        n = len(opts)
        o0 = shuffle_order(n, 0, it.ref)
        original = [None] * n
        for j, i in enumerate(o0):
            original[i] = opts[j]
        c = original.index(opts[p0.answer.value["correct"]])
        out = _Letters(shuffle_order(n, seed, it.ref).index(c) for seed in VARIATION_SEEDS)
        out.n = n
        for seed in (0, 1):
            if it.render(seed).answer.value["correct"] != out[seed]:
                rep.error(key, f"L10 {it.ref}: the rendered order does not follow shuffle_order(n, seed, ref)")
                return None
        return out
    except Exception:                # noqa: BLE001 - already reported by the item checks
        return None


def _audit_items(rep: Report, sk: Skill) -> None:
    key = sk.id
    by_n: dict[int, Counter] = defaultdict(Counter)
    for it in sk.items:
        for seed in ITEM_SEEDS:
            where = f"{it.ref} seed={seed}"
            try:
                p = it.render(seed)
                if (p.skill_id, p.level, p.seed, p.ref) != (sk.id, it.level, seed, it.ref):
                    rep.error(key, f"{where}: header {(p.skill_id, p.level, p.seed, p.ref)}")
                _check_problem(rep, key, where, p, it.render(seed))
            except Exception as e:   # noqa: BLE001 - report, never crash the audit
                rep.error(key, f"{where}: raised {type(e).__name__}: {e}")
                break
        if it.kind == "choice":
            letters = _choice_letters(rep, key, it)
            if letters is None:
                continue
            n = letters.n
            for c in letters:
                by_n[n][c] += 1
            if len(set(letters)) < 2:
                rep.error(key, f"L10 {it.ref}: the correct letter takes one value over seeds 0-19")
    for n, cnt in by_n.items():
        total = sum(cnt.values())
        if total < 40:
            continue
        for pos in range(n):
            share = cnt[pos] / total
            if not 0.5 / n <= share <= 1.5 / n:
                rep.error(key, f"L10: letter {CHOICE_LETTERS[pos]} is correct in {share:.0%} of {n}-option renders "
                               f"(allowed {0.5 / n:.0%}-{1.5 / n:.0%}); spread 'correct' evenly over positions "
                               f"0..{n - 1} across this skill's {n}-option questions")


def _audit_generator(rep: Report, sk: Skill) -> list[Problem]:
    key = sk.id
    problems: list[Problem] = []
    for level in range(1, 6):
        for seed in GEN_SEEDS:
            where = f"level {level} seed {seed}"
            try:
                p = sk.generate(level, seed)
                again = sk.generate(level, seed) if seed < GEN_DETERMINISM_SEEDS else p
            except Exception as e:   # noqa: BLE001
                rep.error(key, f"{where}: generate raised {type(e).__name__}: {e}")
                continue
            problems.append(p)
            if (p.skill_id, p.level, p.seed) != (sk.id, level, seed):
                rep.error(key, f"{where}: header {(p.skill_id, p.level, p.seed)}")
            _check_problem(rep, key, where, p, again)
            disp = p.answer.display
            if p.answer.kind not in ("rubric", "choice") and _hint_leaks(disp, p.hint):
                rep.error(key, f"{where}: the hint contains the answer {disp!r}")
    return problems


# ------------------------------------------------------------------ lints

def _dash(s: str) -> str:
    return _norm_label(s)


def _answer_texts(sk: Skill):
    for it in sk.items:
        try:
            a = it.render(0).answer
        except Exception:            # noqa: BLE001 - reported by the item checks
            continue
        if a.kind == "short":
            for x in a.value["accept"]:
                yield it, x, "accept"
        elif a.kind == "choice":
            for o in a.value["options"]:
                yield it, o, "option"


_FILLER_START = re.compile(r"^\s*(?:it'?s|it is|it was|its|i think|maybe|probably|answer|the answer is|known as)\b",
                           re.IGNORECASE)
_NOTE_PREFIX = re.compile(r"^\[[^\]\n]*\]\s*")


def _lint_universal(rep: Report, sk: Skill) -> None:
    """L5, L7, R6, R12 and two audit-only warnings: safe for any file, including test fixtures."""
    from ..intents import intent, is_cheat_request, is_distress
    key = sk.id
    for it in sk.items:
        if it.kind != "short":
            continue
        try:
            p = it.render(0)
        except Exception:            # noqa: BLE001 - reported by the item checks
            continue
        stem = _NOTE_PREFIX.sub("", p.text)
        if re.match(r"(?i)\s*why\b", stem):
            rep.warn(key, f"{it.ref}: a short answer to a 'Why' question is usually typed as 'because ...', "
                          "and lines starting with because/as/since are ignored; ask for the term or use choice")
        for x in p.answer.value["accept"]:
            if _FILLER_START.match(x):
                rep.warn(key, f"{it.ref}: accept {x!r} starts with a filler phrase; the checker also accepts it "
                              "without that phrase")
    for it, text, what in _answer_texts(sk):
        why = ("a distress phrase" if is_distress(text) else "a cheat request" if is_cheat_request(text)
               else f"the {intent(text)!r} command" if intent(text) is not None else None)
        if why:
            rep.error(key, f"L5 {it.ref}: {what} {text!r} reads as {why}")
        if _SAFETY_WORDS.search(text):
            rep.error(key, f"R6 {it.ref}: {what} {text!r} contains a safety word")
        if text.strip().casefold() in COMMAND_WORDS:
            rep.error(key, f"R12 {it.ref}: {what} {text!r} is a command word")
    for it in sk.items:
        try:
            p = it.render(0)
        except Exception:            # noqa: BLE001
            continue
        parts = [p.text, p.solution, p.hint] + [m.feedback for m in p.mistakes]
        if p.answer.kind == "choice":
            parts += list(p.answer.value["options"])
        if p.answer.kind == "rubric":
            parts += [p.answer.display, p.answer.mark_scheme]
        for t in parts:
            if _MARKDOWN.search(t) or any(line.startswith("#") for line in t.splitlines()):
                rep.error(key, f"L7 {it.ref}: Markdown/LaTeX characters in {t[:60]!r}")


def _lint_shipped(rep: Report, subject_id: str, sk: Skill, labels: set[str] | None, titles: set[str]) -> None:
    """L2-L4, L6, L11 and the section 5 mixes for shipped bank skills of new subjects."""
    key = sk.id
    n = len(sk.items)
    lv = Counter(it.level for it in sk.items)
    kinds = Counter(it.kind for it in sk.items)
    if n < 30:
        rep.error(key, f"L2: {n} questions (needs >= 30)")
    low = [L for L in range(1, 6) if lv[L] < 4]
    if low:
        rep.error(key, f"L2: fewer than 4 questions at level(s) {low} ({dict(sorted(lv.items()))})")
    cs = kinds["choice"] + kinds["short"]
    if cs < 0.85 * n:
        rep.error(key, f"L3: choice + short = {cs}/{n} (needs >= 85%)")
    rub = [it for it in sk.items if it.kind == "rubric"]
    if rub:
        if subject_id not in RUBRIC_SUBJECTS:
            rep.error(key, "L4: rubric items are not allowed in this subject")
        bad = [it.ref for it in rub if it.level not in (4, 5)]
        if bad:
            rep.error(key, f"L4: rubric items below level 4: {bad}")
        if len(rub) > int(0.15 * n):
            rep.error(key, f"L4: {len(rub)} rubric items > floor(0.15 x {n}) = {int(0.15 * n)}")
    mix = MIXES.get(subject_id)
    if mix and n:
        ch, sh, ru = kinds["choice"] / n, kinds["short"] / n, kinds["rubric"] / n
        num = (n - kinds["choice"] - kinds["short"] - kinds["rubric"]) / n
        e = 1e-9
        ok = {"M1": 0.55 - e <= ch <= 0.70 + e and 0.20 - e <= sh <= 0.35 + e,
              "M2": 0.55 - e <= ch <= 0.75 + e and 0.25 - e <= sh <= 0.45 + e and not kinds["rubric"]
              and num <= 0.15 + e,
              "M3": 0.40 - e <= ch <= 0.60 + e and 0.40 - e <= sh <= 0.60 + e and not kinds["rubric"],
              "M4": ch >= 0.65 - e and sh <= 0.35 + e and not kinds["rubric"]}[mix]
        if not ok:
            rep.error(key, f"mix {mix} (section 5): choice={ch:.0%} short={sh:.0%} rubric={ru:.0%} "
                           f"number/other={num:.0%}")
    bad_labels = {_dash(x) for x in RESERVED_LABELS + _BUTTONS} | {_dash(t) for t in titles}
    for it, text, what in _answer_texts(sk):
        d = _dash(text)
        if what == "accept" and (d in bad_labels or (labels and d in labels)):
            rep.error(key, f"L6 {it.ref}: accept {text!r} equals a topic label or button text")
        elif what == "option" and labels and d in labels:
            rep.warn(key, f"L6 {it.ref}: option {text!r} equals a topic label")
    if subject_id in ("arabic", "mandarin"):
        for it, text, what in _answer_texts(sk):
            if what == "accept" and (_ARABIC.search(text) or _HANZI.search(text)):
                rep.error(key, f"L11 {it.ref}: accept {text!r} contains Arabic script or hanzi")
    if subject_id == "russian":
        cyr = 0
        for it in sk.items:
            if it.kind == "short":
                try:
                    acc = it.render(0).answer.value["accept"]
                except Exception:    # noqa: BLE001
                    continue
                if any(_CYRILLIC.search(x) for x in acc):
                    cyr += 1
        if cyr > 0.3 * n:
            rep.error(key, f"L11: {cyr}/{n} short answers need Cyrillic typing (> 30%)")


def _lint_aliases(rep: Report, skills: list[Skill]) -> None:
    """L9: >= 3 lowercase aliases; the first alias finds the skill itself and is unique in the subject."""
    firsts = Counter(sk.aliases[0] for sk in skills if sk.aliases)
    for sk in skills:
        if len(sk.aliases) < 3:
            rep.error(sk.id, f"L9: only {len(sk.aliases)} alias(es) (needs >= 3)")
        if any(a != a.lower() or not a.strip() for a in sk.aliases):
            rep.error(sk.id, "L9: aliases must be lowercase and non-empty")
        if not sk.aliases:
            continue
        res = match_skill_ids(skills, sk.aliases[0])
        if not res or res[0] != sk.id:
            rep.error(sk.id, f"L9: the first alias {sk.aliases[0]!r} finds {res[:1] or 'nothing'} first")
        if firsts[sk.aliases[0]] > 1:
            rep.error(sk.id, f"L9: the first alias {sk.aliases[0]!r} is used by {firsts[sk.aliases[0]]} skills")


def _lint_subject(rep: Report, key: str, subject: Subject) -> None:
    """L8 and the section 4 table (titles, order, years) for new subjects."""
    if len(subject.title) > 18:
        rep.error(key, f"L8: subject title {subject.title!r} is longer than 18 characters")
    want = SUBJECTS_V2.get(subject.id)
    if want is None:
        rep.warn(key, f"subject id {subject.id!r} is not in the section 4 list")
    elif (subject.order, subject.title) != want:
        rep.error(key, f"section 4: expected order {want[0]} and title {want[1]!r}, "
                       f"got {subject.order} and {subject.title!r}")
    if want is not None and sorted(subject.years) != [10, 11]:
        rep.error(key, f"section 4: new subjects have Years 10 and 11 only, got {sorted(subject.years)}")
    for y, spec in subject.years.items():
        for row in spec.rows:
            for t in row:
                if len(t.label) > 30:
                    rep.error(key, f"L8: topic label {t.label!r} is longer than 30 characters")


def _lint_raw_ids(rep: Report, key: str, path: str) -> None:
    """L1: every question in shipped files has an id."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return
    if not isinstance(data, dict):
        return
    for s in data.get("skills", []) or []:
        if not isinstance(s, dict):
            continue
        for i, q in enumerate(s.get("questions", []) or []):
            if isinstance(q, dict) and "id" not in q:
                rep.error(key, f"L1: {s.get('id')} questions[{i}] has no id")


def _labels(subject: Subject | None) -> set[str]:
    if subject is None:
        return set()
    return {_dash(t.label) for spec in subject.years.values() for row in spec.rows for t in row}


# ---------------------------------------------------------------- sources

def _is_shipped(path: str) -> bool:
    d = os.path.realpath(os.path.dirname(os.path.abspath(path)))
    return d in (os.path.realpath(BANKS_DIR), os.path.realpath(PACKS_DIR))


def _audit_skills(rep: Report, subject_id: str, skills: list[Skill], *, shipped: bool,
                  labels: set[str] | None, titles: set[str]) -> None:
    for sk in skills:
        if sk.items:
            rep.entry(sk.id, _skill_header(sk))
            _audit_items(rep, sk)
            _lint_universal(rep, sk)
            if shipped and subject_id not in FROZEN:
                _lint_shipped(rep, subject_id, sk, labels, titles)
        else:
            rep.entry(sk.id, sk.id + ": gen (running)")
            problems = _audit_generator(rep, sk)
            rep.entry(sk.id, _skill_header(sk, problems))
    if shipped and subject_id not in FROZEN:
        _lint_aliases(rep, skills)


def _bad_folder_files(rep: Report) -> None:
    for folder in (BANKS_DIR, PACKS_DIR):
        if os.path.isdir(folder):
            bad = sorted(n for n in os.listdir(folder) if n.endswith(".py") or n == "__pycache__")
            if bad:
                rep.error(f"folder {folder}", f"must hold only .json files, found {bad}")


def audit_file(rep: Report, path: str, titles: set[str] | None = None) -> str | None:
    """Audit one bank or pack file (collecting every error).  Returns its subject id."""
    key = f"file {path}"
    try:
        data = _read_json(path)
    except BankError as e:
        rep.error(key, str(e))
        return None
    shipped = _is_shipped(path)
    errors: list[str] = []
    subject: Subject | None = None
    if isinstance(data, dict) and "subject_id" in data and "subject" not in data:
        sid = data.get("subject_id")
        if not isinstance(sid, str) or not sid:
            rep.error(key, "$.subject_id: must be a non-empty string")
            return None
        try:
            skills = parse_pack_data(data, sid, errors)
        except BankError as e:
            errors.append(str(e))
            skills = []
        labels = None                       # the module owns the labels: skipped
    else:
        try:
            subject, skills = parse_bank_data(data, errors)
        except BankError as e:
            errors.append(str(e))
            skills = []
        sid = subject.id if subject else (data.get("subject", {}) or {}).get("id", "?") \
            if isinstance(data, dict) else "?"
        labels = _labels(subject)
        if subject is not None and not errors:
            try:
                Registry().register(subject, skills)
            except Exception as e:      # noqa: BLE001
                errors.append(f"registry: {type(e).__name__}: {e}")
    for e in errors:
        rep.error(key, e)
    if shipped:
        _lint_raw_ids(rep, key, path)
        if subject is not None and subject.id not in FROZEN:
            _lint_subject(rep, key, subject)
    all_titles = set(titles or ()) | {t for _, t in SUBJECTS_V2.values()}
    _audit_skills(rep, str(sid), skills, shipped=shipped, labels=labels, titles=all_titles)
    if not errors and not skills:
        rep.error(key, "no skills loaded")
    if key in rep._by_key:                 # noqa: SLF001
        rep.entry(key).header = key + ":"
    return str(sid)


def _audit_module(rep: Report, name: str, titles: set[str]) -> list[str]:
    """Register one subject module on its own and audit its subjects.  Returns their ids."""
    key = f"source {name}"
    reg = Registry()
    try:
        register_module(reg, name)
    except Exception as e:              # noqa: BLE001
        rep.error(key, f"{type(e).__name__}: {e}")
        rep.entry(key).header = key + ":"
        return []
    ids = list(reg._subjects)           # noqa: SLF001 - registration order
    for sid in ids:
        subject = reg.subject(sid)
        assert subject is not None
        if sid not in FROZEN:
            _lint_subject(rep, f"subject {sid}", subject)
        _audit_skills(rep, sid, reg.skills_of(sid), shipped=True, labels=_labels(subject), titles=titles)
    return ids


def _all_titles() -> set[str]:
    return {t for _, t in SUBJECTS_V2.values()}


def audit_all(rep: Report) -> None:
    titles = _all_titles()
    _bad_folder_files(rep)
    _, names = _subject_modules()
    loaded: set[str] = set()
    for name in names:
        loaded.update(_audit_module(rep, name, titles))
    for path in bank_files():
        sid = audit_file(rep, path, titles)
        if sid:
            loaded.add(sid)
    if os.path.isdir(PACKS_DIR):
        for name in sorted(os.listdir(PACKS_DIR)):
            if name.endswith(".json") and not name.startswith("_") and name[:-5] not in loaded:
                audit_file(rep, os.path.join(PACKS_DIR, name), titles)
    try:
        load_registry(strict=True)
    except Exception as e:              # noqa: BLE001
        rep.error("registry", f"the sources do not load together: {type(e).__name__}: {e}")


def audit_subject(rep: Report, subject_id: str) -> bool:
    """Audit only the source that registers ``subject_id``.  False if no source does."""
    titles = _all_titles()
    bank = os.path.join(BANKS_DIR, subject_id + ".json")
    if os.path.isfile(bank):
        audit_file(rep, bank, titles)
        return True
    _, names = _subject_modules()
    ordered = [n for n in names if n == subject_id] + [n for n in names if n != subject_id]
    failures: list[tuple[str, str]] = []
    for name in ordered:
        reg = Registry()
        try:
            register_module(reg, name)
        except Exception as e:          # noqa: BLE001
            if name == subject_id:
                rep.error(f"source {name}", f"{type(e).__name__}: {e}")
                rep.entry(f"source {name}").header = f"source {name}:"
                _audit_pack_if_any(rep, subject_id, titles)
                return True
            failures.append((name, f"{type(e).__name__}: {e}"))
            continue
        if reg.subject(subject_id) is not None:
            _audit_module(rep, name, titles)
            return True
    pack = os.path.join(PACKS_DIR, subject_id + ".json")
    if os.path.isfile(pack):
        for name, msg in failures:
            rep.error(f"source {name}", msg)
        audit_file(rep, pack, titles)
        return True
    for name, msg in failures:
        rep.warn(f"source {name}", f"failed to load (it may own subject {subject_id!r}): {msg}")
    return False


def _audit_pack_if_any(rep: Report, subject_id: str, titles: set[str]) -> None:
    pack = os.path.join(PACKS_DIR, subject_id + ".json")
    if os.path.isfile(pack):
        audit_file(rep, pack, titles)


def run(subject: str | None = None, file: str | None = None, out: TextIO | None = None) -> int:
    """CLI entry point; returns the exit code (0 = no ERROR lines)."""
    out = out or sys.stdout
    rep = Report()
    if file:
        audit_file(rep, file)
    elif subject:
        if not audit_subject(rep, subject):
            rep.error(f"subject {subject}", "no source registers this subject")
    else:
        audit_all(rep)
    rep.write(out)
    n = rep.errors
    print(f"audit: {n} error(s)", file=out)
    return 0 if n == 0 else 1


def summary_lines(reg: Registry) -> Iterable[str]:   # pragma: no cover - convenience for --check
    yield f"Subjects: {len({s.id for y in reg.years() for s in reg.subjects_for_year(y)})} loaded"
    for e in reg.load_errors:
        yield e
