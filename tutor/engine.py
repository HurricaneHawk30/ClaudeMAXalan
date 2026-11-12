"""Conversation engine: Incoming -> list[Outgoing]. The only I/O is the injected LLM."""
from __future__ import annotations

import collections
import logging
import random
import time
from typing import Callable

from . import texts as T
from .config import Config
from .content import MY_OWN_TOPIC_LABEL, Problem, Registry, Topic, check, fingerprint, letters_text, load_registry
from .db import Attempt, Pending, Store, Student
from .intents import (command_name, intent, is_cheat_request, is_distress, normalize_code,
                      parse_year)
from .llm import LLM, mark_rubric, pick_skill, tutor_text
from .messages import Incoming, Keyboard, Outgoing
from .owner import OWNER_COMMANDS, handle_owner

log = logging.getLogger(__name__)

EXAM_MARKS = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}
REROLL_TRIES = 40               # candidate seeds tried when choosing the next problem (repeat avoidance)
MATH_CHARS = "=+-*/^²√π"
BAD_CODE_ALERT_AFTER = 10       # wrong codes from one chat within BAD_CODE_WINDOW -> one owner alert
BAD_CODE_WINDOW = 3600.0


def where(e: BaseException) -> str:
    """Exception type and the innermost code location, never the message (it may contain student text)."""
    tb = e.__traceback__
    loc = ""
    while tb is not None:
        loc = f"{tb.tb_frame.f_code.co_filename.rsplit('/', 1)[-1]}:{tb.tb_lineno}"
        tb = tb.tb_next
    return f"{type(e).__name__} at {loc}" if loc else type(e).__name__


def _trim(s: str) -> str:
    """Strip a trailing '. ' so texts can be put into templates that add their own period."""
    return (s or "").rstrip(". \n\t")


def _day(now: float) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(now))


def _choice_count(problem: Problem) -> int:
    """Number of options of a choice problem (0 if the value is malformed)."""
    v = problem.answer.value
    opts = v.get("options") if isinstance(v, dict) else None
    return len(opts) if isinstance(opts, (list, tuple)) and 1 <= len(opts) <= 5 else 0


def _problem_message(problem: Problem, number: int, exam: bool, gen: int) -> str:
    """The problem text for each answer kind (docs/ARCHITECTURE_V2.md section 3.2)."""
    kind = problem.answer.kind
    if kind == "choice":
        return (T.PROBLEM_CHOICE_EXAM if exam else T.PROBLEM_CHOICE).format(n=number, text=problem.text)
    if kind == "short":
        return (T.PROBLEM_SHORT_EXAM if exam else T.PROBLEM_SHORT).format(n=number, text=problem.text)
    if kind == "rubric":
        marks = problem.answer.max_marks
        return T.PROBLEM_RUBRIC.format(n=number, marks=marks, s="" if marks == 1 else "s", text=problem.text)
    if exam:
        marks = EXAM_MARKS[gen]
        return T.PROBLEM_EXAM.format(n=number, marks=marks, s="" if marks == 1 else "s", text=problem.text)
    return T.PROBLEM.format(n=number, text=problem.text)


class Engine:
    def __init__(self, store: Store, config: Config, registry: Registry | None = None,
                 llm: LLM | None = None, clock: Callable[[], float] = time.time,
                 rng: random.Random | None = None) -> None:
        self.store = store
        self.config = config
        # a broken content file never stops the bot: it is logged and skipped (docs/ARCHITECTURE_V2.md D7)
        self.registry = registry if registry is not None else load_registry(strict=False)
        self.llm = llm
        self.clock = clock
        self.rng = rng if rng is not None else random.Random()
        self._flood: dict[int, collections.deque] = {}
        self._bad_codes: dict[int, collections.deque] = {}
        self._code_alerted: dict[int, float] = {}
        self._now = 0.0

    # ------------------------------------------------------------------ entry
    def handle(self, msg: Incoming) -> list[Outgoing]:
        if msg.chat_type != "private":
            return []
        try:
            with self.store.transaction():
                return self._handle(msg)
        except Exception as e:
            log.error("error while handling a message from chat %s: %s", msg.chat_id, where(e))
            return [Outgoing(msg.chat_id, T.ERROR)]

    def on_delivery_failed(self, chat_id: int) -> None:
        """The adapter could not deliver a reply to ``chat_id``: forget the pending problem so the
        student's next answer is never marked against a problem they have not seen."""
        try:
            with self.store.transaction():
                self.store.clear_pending(chat_id)
        except Exception as e:
            log.error("could not clear pending for chat %s: %s", chat_id, where(e))

    def _handle(self, msg: Incoming) -> list[Outgoing]:
        now = self._now = self.clock()
        text = (msg.text or "")[:2000].strip()
        cmd = command_name(text)
        owner_id = self.config.owner_id
        is_owner = owner_id is not None and msg.user_id == owner_id

        # 1. owner commands
        if is_owner and cmd in OWNER_COMMANDS:
            args = text.split()[1:]
            replies = handle_owner(cmd, args, store=self.store, now=now, registry=self.registry)
            return [Outgoing(owner_id, r) for r in replies]

        # 2. distress comes before flood control: it is always flagged, alerted and answered
        if msg.text is not None and cmd not in ("/start", "/delete_my_data") and is_distress(text):
            if not is_owner:
                self._flooded(msg.chat_id, now)          # counts towards the window, never dropped
            return self._distress(msg, text, now)

        # 3. flood control
        if not is_owner and self._flooded(msg.chat_id, now):
            return []

        # 4. register the student
        st = self._seen(msg, now)

        # 5. delete data
        if cmd == "/delete_my_data":
            self.store.delete_student_data(msg.chat_id)
            return [Outgoing(msg.chat_id, T.DELETED, remove_keyboard=True)]

        # 6. /start
        if cmd == "/start":
            if not st.verified:
                st.step = "code"
                self.store.save_student(st)
                return [Outgoing(msg.chat_id, T.CODE_REQUEST, remove_keyboard=True)]
            self.store.clear_pending(st.chat_id)
            st.step = "subject"
            return self._finish(st, self._subject_reply(st))

        # 7. access code
        if not st.verified:
            code = normalize_code(text) if msg.text is not None else None
            if code is None:
                return [Outgoing(msg.chat_id, T.CODE_REQUEST)]
            if not self.store.redeem_code(code, msg.chat_id, now):
                return [Outgoing(msg.chat_id, T.CODE_BAD)] + self._bad_code_alert(st, now)
            st.verified = True
            st.step = "subject"
            out = [Outgoing(msg.chat_id, T.CODE_OK)] + self._subject_reply(st)
            return self._finish(st, out)

        # 8. non-text
        if msg.text is None:
            self.store.save_student(st)
            return [Outgoing(msg.chat_id, T.TEXT_ONLY, keyboard=self._current_kb(st))]

        # 9. change buttons
        if text in (T.CHANGE_YEAR, T.LEGACY_CHANGE):
            self.store.clear_pending(st.chat_id)
            st.step = "year"
            return self._finish(st, [Outgoing(st.chat_id, T.YEAR_ASK, keyboard=T.YEAR_KB)])
        if text == T.CHANGE_SUBJECT:
            self.store.clear_pending(st.chat_id)
            st.step = "subject"
            return self._finish(st, self._subject_reply(st))

        # 10. topic buttons
        if st.step in ("topic", "own_topic", "lesson") and self._subject_ok(st):
            if text.strip().lower() == MY_OWN_TOPIC_LABEL.lower():
                self.store.clear_pending(st.chat_id)
                st.step = "own_topic"
                return self._finish(st, [Outgoing(st.chat_id, T.OWN_TOPIC_ASK, keyboard=self._topic_kb(st))])
            topic = self.registry.topic_by_label(st.subject, st.year, text)
            if topic is not None:
                return self._finish(st, self._start_topic(st, topic))

        # 11. cheat requests
        if is_cheat_request(text):
            return self._finish(st, [Outgoing(st.chat_id, T.CHEAT, keyboard=self._current_kb(st))])

        # 12. by step
        return self._finish(st, self._by_step(st, text))

    # --------------------------------------------------------------- helpers
    def _seen(self, msg: Incoming, now: float) -> Student:
        st = self.store.upsert_seen(msg.chat_id, msg.first_name, msg.username, now)
        if st.verified and st.step == "code":
            st.step = "subject"
        return st

    def _distress(self, msg: Incoming, text: str, now: float) -> list[Outgoing]:
        st = self._seen(msg, now)
        self.store.add_flag(msg.chat_id, "distress", text, now)
        out = [Outgoing(msg.chat_id, T.DISTRESS, keyboard=self._current_kb(st))]
        owner_id = self.config.owner_id
        if owner_id is not None:
            out.append(Outgoing(owner_id, T.FLAG_ALERT.format(
                kind="distress", name=self._name(st), chat_id=msg.chat_id, text=text[:300])))
        self.store.save_student(st)
        return out

    def _bad_code_alert(self, st: Student, now: float) -> list[Outgoing]:
        """One owner alert per chat per hour once a chat has sent 10 wrong codes within an hour."""
        window = self._bad_codes.setdefault(st.chat_id, collections.deque())
        while window and window[0] <= now - BAD_CODE_WINDOW:
            window.popleft()
        window.append(now)
        owner_id = self.config.owner_id
        if owner_id is None or len(window) < BAD_CODE_ALERT_AFTER:
            return []
        if now - self._code_alerted.get(st.chat_id, -BAD_CODE_WINDOW - 1) < BAD_CODE_WINDOW:
            return []
        self._code_alerted[st.chat_id] = now
        return [Outgoing(owner_id, T.CODE_ALERT.format(n=len(window), name=self._name(st), chat_id=st.chat_id))]

    def _finish(self, st: Student, out: list[Outgoing]) -> list[Outgoing]:
        self.store.save_student(st)
        return out

    def _flooded(self, chat_id: int, now: float) -> bool:
        window = self._flood.setdefault(chat_id, collections.deque())
        while window and window[0] <= now - 60:
            window.popleft()
        if len(window) >= self.config.flood_per_minute:
            return True
        window.append(now)
        return False

    @staticmethod
    def _name(st: Student) -> str:
        return (st.first_name or "?") + (f" @{st.username}" if st.username else "")

    def _llm_allowed(self, chat_id: int) -> bool:
        if self.llm is None:
            return False
        day = _day(self._now)
        return (self.store.llm_calls(chat_id, day) < self.config.llm_daily_limit
                and self.store.llm_calls_total(day) < self.config.llm_global_daily_limit)

    def _count_llm(self, chat_id: int) -> None:
        self.store.incr_llm_calls(chat_id, _day(self._now))

    def _tutor(self, mode: str, st: Student, p: Pending, text: str) -> str | None:
        if not self._llm_allowed(st.chat_id):
            return None
        subj = self.registry.subject(p.subject)
        self._count_llm(st.chat_id)
        return tutor_text(self.llm, mode, p.problem, text, subj.title if subj else p.subject, st.year)

    def _subject_ok(self, st: Student) -> bool:
        if not st.subject:
            return False
        return any(s.id == st.subject for s in self.registry.subjects_for_year(st.year))

    def _subject_kb(self, st: Student) -> Keyboard:
        return T.subject_kb(s.title for s in self.registry.subjects_for_year(st.year))

    def _topic_kb(self, st: Student) -> Keyboard:
        return T.topic_kb(self.registry.topic_rows(st.subject, st.year))

    def _current_kb(self, st: Student) -> Keyboard | None:
        if not st.verified or st.step == "code":
            return None
        if st.step == "year":
            return T.YEAR_KB
        if st.step == "subject" or not self._subject_ok(st):
            if self.registry.subjects_for_year(st.year):
                return self._subject_kb(st)
            return T.YEAR_KB
        if st.step == "lesson":
            p = self.store.get_pending(st.chat_id)
            if p is not None:
                return self._lesson_kb(st, p.problem)
        return self._topic_kb(st)

    def _lesson_kb(self, st: Student, problem: Problem | None) -> Keyboard:
        """topic_kb, with the letter row on top while a multiple-choice problem is open."""
        rows = self.registry.topic_rows(st.subject, st.year)
        if problem is not None and problem.answer.kind == "choice":
            n = _choice_count(problem)
            if n:
                return T.choice_kb(n, rows)
        return T.topic_kb(rows)

    def _subject_reply(self, st: Student) -> list[Outgoing]:
        if not self.registry.subjects_for_year(st.year):
            st.step = "year"
            return [Outgoing(st.chat_id, T.YEAR_NOT_READY.format(year_label=f"Year {st.year}"),
                             keyboard=T.YEAR_KB)]
        st.step = "subject"
        return [Outgoing(st.chat_id, T.SUBJECT_ASK.format(year=st.year), keyboard=self._subject_kb(st))]

    def _topic_ask(self, st: Student) -> list[Outgoing]:
        st.step = "topic"
        return [Outgoing(st.chat_id, T.TOPIC_ASK.format(year=st.year), keyboard=self._topic_kb(st))]

    # ---------------------------------------------------------------- steps
    def _by_step(self, st: Student, text: str) -> list[Outgoing]:
        if st.step == "year":
            parsed = parse_year(text)
            if parsed is None:
                return [Outgoing(st.chat_id, T.YEAR_ASK, keyboard=T.YEAR_KB)]
            year, label = parsed
            if not self.registry.subjects_for_year(year):
                return [Outgoing(st.chat_id, T.YEAR_NOT_READY.format(year_label=label), keyboard=T.YEAR_KB)]
            st.year = year
            st.subject = None
            st.topic = None
            return self._subject_reply(st)

        if st.step == "subject" or not self._subject_ok(st):
            if st.step == "subject":
                wanted = text.strip().lower()
                for s in self.registry.subjects_for_year(st.year):
                    if s.title.lower() == wanted:
                        st.subject = s.id
                        st.topic = None
                        return self._topic_ask(st)
            return self._subject_reply(st)

        if st.step == "topic":
            return [Outgoing(st.chat_id, T.TOPIC_ASK.format(year=st.year), keyboard=self._topic_kb(st))]

        if st.step == "own_topic":
            ids = self.registry.match_skills(st.subject, text)
            skill_id = ids[0] if ids else None
            if skill_id is None and self._llm_allowed(st.chat_id):
                self._count_llm(st.chat_id)
                skills = [(s.id, s.title) for s in self.registry.skills_of(st.subject)]
                skill_id = pick_skill(self.llm, text, skills)
            if skill_id is not None and self.registry.skill(skill_id) is not None:
                return self._start_topic(st, self.registry.own_topic(skill_id))
            return [Outgoing(st.chat_id, T.OWN_TOPIC_NONE, keyboard=self._topic_kb(st))]

        # lesson
        p = self.store.get_pending(st.chat_id)
        if p is None:
            return self._topic_ask(st)
        return self._lesson_reply(st, p, text)

    # --------------------------------------------------------------- lesson
    def _start_topic(self, st: Student, topic: Topic) -> list[Outgoing]:
        st.step = "lesson"
        st.topic = topic.id
        level = max(1, self.store.get_level(st.chat_id, st.subject, topic.id) - 1)
        self.store.set_level(st.chat_id, st.subject, topic.id, level)
        skill_id = self.rng.choice(list(topic.skills))
        return [Outgoing(st.chat_id, T.TOPIC_START.format(topic=topic.label)),
                self._next_problem(st, topic, skill_id, level, 1, None)]

    def _next_problem(self, st: Student, topic: Topic, skill_id: str, level: int, number: int,
                      prev: Problem | None) -> Outgoing:
        skill = self.registry.skill(skill_id)
        if skill is None:
            raise RuntimeError(f"unknown skill {skill_id}")
        gen = topic.level_map[level - 1]
        seed, problem = self._choose(st.chat_id, skill, gen, prev)
        self.store.add_seen(st.chat_id, skill_id, fingerprint(problem))
        self.store.set_pending(Pending(
            chat_id=st.chat_id, subject=st.subject, topic=topic.id, skill=skill_id, level=level,
            gen_level=gen, seed=seed, problem_no=number, problem=problem, hints_given=0,
            created_at=self._now))
        return Outgoing(st.chat_id, _problem_message(problem, number, topic.exam, gen),
                        keyboard=self._lesson_kb(st, problem))

    def _choose(self, chat_id: int, skill, gen: int, prev: Problem | None) -> tuple[int, Problem]:
        """Repeat avoidance (docs/ARCHITECTURE_V2.md section 3.2): never the previous problem, never two
        extended-practice problems in a row, and the least recently seen problem when all were seen."""
        recent = self.store.recent_seen(chat_id, skill.id)
        base = self.rng.randrange(1, 2 ** 31 - REROLL_TRIES)
        prev_fp = fingerprint(prev) if prev is not None else None
        fallback: tuple[int, int, Problem] | None = None       # (index in recent, seed, problem)
        for k in range(REROLL_TRIES):
            seed = base + k
            p = skill.generate(gen, seed)
            fp = fingerprint(p)
            if prev is not None and (fp == prev_fp or p.text == prev.text):
                continue
            if prev is not None and prev.answer.kind == "rubric" and p.answer.kind == "rubric":
                continue
            if fp not in recent:
                return seed, p
            idx = recent.index(fp)
            if fallback is None or idx > fallback[0]:
                fallback = (idx, seed, p)
        if fallback is not None:
            return fallback[1], fallback[2]
        return base, skill.generate(gen, base)          # last resort; may repeat

    def _record(self, st: Student, p: Pending, correct: bool, skipped: bool) -> None:
        self.store.add_attempt(Attempt(
            chat_id=st.chat_id, subject=p.subject, topic=p.topic, skill=p.skill, level=p.level,
            gen_level=p.gen_level, correct=correct, skipped=skipped, ts=self._now))

    def _set_level(self, st: Student, p: Pending, level: int) -> int:
        level = max(1, min(5, level))
        self.store.set_level(st.chat_id, p.subject, p.topic, level)
        return level

    def _other_skill(self, topic: Topic, current: str) -> str:
        others = [s for s in topic.skills if s != current]
        return self.rng.choice(others) if others else current

    def _lesson_reply(self, st: Student, p: Pending, text: str) -> list[Outgoing]:
        topic = self.registry.topic(p.topic)
        if topic is None or self.registry.skill(p.skill) is None:
            self.store.clear_pending(st.chat_id)
            return self._topic_ask(st)
        problem = p.problem
        answer = problem.answer
        kb = self._lesson_kb(st, problem)
        want = intent(text)

        if want == "hint":
            if p.hints_given == 0:
                reply = T.HINT.format(hint=problem.hint)
            else:
                extra = self._tutor("hint", st, p, text)
                reply = T.HINT_LLM.format(text=extra) if extra else T.HINT_AGAIN.format(hint=problem.hint)
            p.hints_given += 1
            self.store.set_pending(p)
            return [Outgoing(st.chat_id, reply, keyboard=kb)]

        if want == "skip":
            self._record(st, p, False, True)
            level = self._set_level(st, p, p.level - 1)
            return [Outgoing(st.chat_id, T.SKIP.format(solution=_trim(problem.solution), answer=answer.display)),
                    self._next_problem(st, topic, p.skill, level, p.problem_no + 1, problem)]

        if answer.kind == "rubric":
            return self._rubric_reply(st, p, topic, text)

        verdict = check(answer, text, problem.mistakes)

        if verdict.status == "correct":
            self._record(st, p, True, False)
            level = self._set_level(st, p, p.level + 1)
            note = _trim(verdict.feedback)
            if note:
                body = T.CORRECT_NOTE.format(solution=_trim(problem.solution), note=verdict.feedback.strip())
            else:
                body = T.CORRECT.format(solution=_trim(problem.solution))
            return [Outgoing(st.chat_id, body),
                    self._next_problem(st, topic, self._other_skill(topic, p.skill), level,
                                       p.problem_no + 1, problem)]

        if verdict.status == "wrong":
            self._record(st, p, False, False)
            level = self._set_level(st, p, p.level - 1)
            why = _trim(verdict.feedback)
            if not why:
                why = _trim(self._tutor("feedback", st, p, text) or "")
            if not why:
                fallback = T.WHY_FACT if answer.kind in ("choice", "short") else T.WHY_FALLBACK
                why = _trim(fallback.format(solution=_trim(problem.solution)))
            return [Outgoing(st.chat_id, T.WRONG.format(why=why, answer=answer.display)),
                    self._next_problem(st, topic, p.skill, level, p.problem_no + 1, problem)]

        if verdict.status == "unmarkable":
            return self._unmarkable(st, p, topic)

        # unparsed
        chat = self._tutor("chat", st, p, text)
        if chat:
            return [Outgoing(st.chat_id, T.LLM_CHAT.format(text=chat), keyboard=kb)]
        if answer.kind == "choice":
            return [Outgoing(st.chat_id, T.CHOICE_UNPARSED.format(letters=letters_text(_choice_count(problem) or 3)),
                             keyboard=kb)]
        if answer.kind == "short":
            return [Outgoing(st.chat_id, T.SHORT_UNPARSED, keyboard=kb)]
        if any(c.isdigit() for c in text) or any(c in text for c in MATH_CHARS):
            return [Outgoing(st.chat_id, T.UNPARSED, keyboard=kb)]
        subj = self.registry.subject(p.subject)
        return [Outgoing(st.chat_id, T.OFFTOPIC.format(subject=subj.title if subj else p.subject,
                                                       n=p.problem_no), keyboard=kb)]

    def _unmarkable(self, st: Student, p: Pending, topic: Topic) -> list[Outgoing]:
        return [Outgoing(st.chat_id, T.UNMARKABLE.format(answer=p.problem.answer.display)),
                self._next_problem(st, topic, p.skill, p.level, p.problem_no + 1, p.problem)]

    def _rubric_reply(self, st: Student, p: Pending, topic: Topic, text: str) -> list[Outgoing]:
        marked = None
        if self.config.llm_marking and self._llm_allowed(st.chat_id):
            self._count_llm(st.chat_id)
            marked = mark_rubric(self.llm, p.problem, text)
        if marked is None:
            return self._unmarkable(st, p, topic)
        marks, fb = marked
        full = marks >= p.problem.answer.max_marks
        self._record(st, p, full, False)
        if full:
            level = self._set_level(st, p, p.level + 1)
            return [Outgoing(st.chat_id, T.CORRECT.format(solution=_trim(fb or p.problem.solution))),
                    self._next_problem(st, topic, self._other_skill(topic, p.skill), level,
                                       p.problem_no + 1, p.problem)]
        level = self._set_level(st, p, p.level - 1)
        why = _trim(fb) or _trim(T.WHY_FALLBACK.format(solution=_trim(p.problem.solution)))
        return [Outgoing(st.chat_id, T.WRONG.format(why=why, answer=p.problem.answer.display)),
                self._next_problem(st, topic, p.skill, level, p.problem_no + 1, p.problem)]
