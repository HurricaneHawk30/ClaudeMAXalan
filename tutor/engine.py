"""Conversation engine: Incoming -> list[Outgoing]. The only I/O is the injected LLM."""
from __future__ import annotations

import collections
import logging
import random
import time
from typing import Callable

from . import texts as T
from .config import Config
from .content import MY_OWN_TOPIC_LABEL, Registry, Topic, check, load_registry
from .db import Attempt, Pending, Store, Student
from .intents import (command_name, intent, is_cheat_request, is_distress, normalize_code,
                      parse_year)
from .llm import LLM, mark_rubric, pick_skill, tutor_text
from .messages import Incoming, Keyboard, Outgoing
from .owner import OWNER_COMMANDS, handle_owner

log = logging.getLogger(__name__)

EXAM_MARKS = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}
MATH_CHARS = "=+-*/^²√π"


def _trim(s: str) -> str:
    """Strip a trailing '. ' so texts can be put into templates that add their own period."""
    return (s or "").rstrip(". \n\t")


def _day(now: float) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(now))


class Engine:
    def __init__(self, store: Store, config: Config, registry: Registry | None = None,
                 llm: LLM | None = None, clock: Callable[[], float] = time.time,
                 rng: random.Random | None = None) -> None:
        self.store = store
        self.config = config
        self.registry = registry if registry is not None else load_registry()
        self.llm = llm
        self.clock = clock
        self.rng = rng if rng is not None else random.Random()
        self._flood: dict[int, collections.deque] = {}
        self._now = 0.0

    # ------------------------------------------------------------------ entry
    def handle(self, msg: Incoming) -> list[Outgoing]:
        if msg.chat_type != "private":
            return []
        try:
            with self.store.transaction():
                return self._handle(msg)
        except Exception:
            log.exception("error while handling a message from chat %s", msg.chat_id)
            return [Outgoing(msg.chat_id, T.ERROR)]

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

        # 2. flood control
        if not is_owner and self._flooded(msg.chat_id, now):
            return []

        # 3. register the student
        st = self.store.upsert_seen(msg.chat_id, msg.first_name, msg.username, now)
        if st.verified and st.step == "code":
            st.step = "subject"

        # 4. delete data
        if cmd == "/delete_my_data":
            self.store.delete_student_data(msg.chat_id)
            return [Outgoing(msg.chat_id, T.DELETED, remove_keyboard=True)]

        # 5. /start
        if cmd == "/start":
            if not st.verified:
                st.step = "code"
                self.store.save_student(st)
                return [Outgoing(msg.chat_id, T.CODE_REQUEST, remove_keyboard=True)]
            self.store.clear_pending(st.chat_id)
            st.step = "subject"
            return self._finish(st, self._subject_reply(st))

        # 6. distress
        if msg.text is not None and is_distress(text):
            self.store.add_flag(msg.chat_id, "distress", text, now)
            out = [Outgoing(msg.chat_id, T.DISTRESS, keyboard=self._current_kb(st))]
            if owner_id is not None:
                out.append(Outgoing(owner_id, T.FLAG_ALERT.format(
                    kind="distress", name=self._name(st), chat_id=msg.chat_id, text=text[:300])))
            self.store.save_student(st)
            return out

        # 7. access code
        if not st.verified:
            code = normalize_code(text) if msg.text is not None else None
            if code is None:
                return [Outgoing(msg.chat_id, T.CODE_REQUEST)]
            if not self.store.redeem_code(code, msg.chat_id, now):
                return [Outgoing(msg.chat_id, T.CODE_BAD)]
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
        return (self.llm is not None
                and self.store.llm_calls(chat_id, _day(self._now)) < self.config.llm_daily_limit)

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
        return self._topic_kb(st)

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
                      prev_text: str | None) -> Outgoing:
        skill = self.registry.skill(skill_id)
        if skill is None:
            raise RuntimeError(f"unknown skill {skill_id}")
        gen = topic.level_map[level - 1]
        problem = None
        seed = 0
        for _ in range(4):
            seed = self.rng.randrange(1, 2 ** 31)
            problem = skill.generate(gen, seed)
            if problem.text != prev_text:
                break
        self.store.set_pending(Pending(
            chat_id=st.chat_id, subject=st.subject, topic=topic.id, skill=skill_id, level=level,
            gen_level=gen, seed=seed, problem_no=number, problem=problem, hints_given=0,
            created_at=self._now))
        if topic.exam:
            marks = EXAM_MARKS[gen]
            body = T.PROBLEM_EXAM.format(n=number, marks=marks, s="" if marks == 1 else "s", text=problem.text)
        else:
            body = T.PROBLEM.format(n=number, text=problem.text)
        return Outgoing(st.chat_id, body, keyboard=self._topic_kb(st))

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
        kb = self._topic_kb(st)
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
                    self._next_problem(st, topic, p.skill, level, p.problem_no + 1, problem.text)]

        if answer.kind == "rubric":
            return self._rubric_reply(st, p, topic, text)

        verdict = check(answer, text, problem.mistakes)

        if verdict.status == "correct":
            self._record(st, p, True, False)
            level = self._set_level(st, p, p.level + 1)
            return [Outgoing(st.chat_id, T.CORRECT.format(solution=_trim(problem.solution))),
                    self._next_problem(st, topic, self._other_skill(topic, p.skill), level,
                                       p.problem_no + 1, problem.text)]

        if verdict.status == "wrong":
            self._record(st, p, False, False)
            level = self._set_level(st, p, p.level - 1)
            why = _trim(verdict.feedback)
            if not why:
                why = _trim(self._tutor("feedback", st, p, text) or "")
            if not why:
                why = _trim(T.WHY_FALLBACK.format(solution=_trim(problem.solution)))
            return [Outgoing(st.chat_id, T.WRONG.format(why=why, answer=answer.display)),
                    self._next_problem(st, topic, p.skill, level, p.problem_no + 1, problem.text)]

        if verdict.status == "unmarkable":
            return self._unmarkable(st, p, topic)

        # unparsed
        chat = self._tutor("chat", st, p, text)
        if chat:
            return [Outgoing(st.chat_id, T.LLM_CHAT.format(text=chat), keyboard=kb)]
        if any(c.isdigit() for c in text) or any(c in text for c in MATH_CHARS):
            return [Outgoing(st.chat_id, T.UNPARSED, keyboard=kb)]
        subj = self.registry.subject(p.subject)
        return [Outgoing(st.chat_id, T.OFFTOPIC.format(subject=subj.title if subj else p.subject,
                                                       n=p.problem_no), keyboard=kb)]

    def _unmarkable(self, st: Student, p: Pending, topic: Topic) -> list[Outgoing]:
        return [Outgoing(st.chat_id, T.UNMARKABLE.format(answer=p.problem.answer.display)),
                self._next_problem(st, topic, p.skill, p.level, p.problem_no + 1, p.problem.text)]

    def _rubric_reply(self, st: Student, p: Pending, topic: Topic, text: str) -> list[Outgoing]:
        marked = None
        if self._llm_allowed(st.chat_id):
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
                                       p.problem_no + 1, p.problem.text)]
        level = self._set_level(st, p, p.level - 1)
        why = _trim(fb) or _trim(T.WHY_FALLBACK.format(solution=_trim(p.problem.solution)))
        return [Outgoing(st.chat_id, T.WRONG.format(why=why, answer=p.problem.answer.display)),
                self._next_problem(st, topic, p.skill, level, p.problem_no + 1, p.problem.text)]
