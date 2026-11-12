"""Owner commands: return plain texts, the engine wraps them."""
from __future__ import annotations

import time

from . import texts as T
from .content import Registry
from .db import Student, Store

OWNER_COMMANDS = ("/codes", "/students", "/student", "/reset", "/flags", "/stats")


def _date(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts))


def _name(st: Student | None) -> str:
    if st is None:
        return "unknown"
    name = st.first_name or "?"
    return name + (f" @{st.username}" if st.username else "")


def _plural(n: int) -> str:
    return "" if n == 1 else "s"


def _parse_chat_id(args: list[str]) -> int | None:
    if len(args) != 1:
        return None
    try:
        return int(args[0])
    except ValueError:
        return None


def handle_owner(cmd: str, args: list[str], *, store: Store, now: float, registry: Registry) -> list[str]:
    if cmd == "/codes":
        n = None
        if len(args) == 1 and args[0].isdigit():
            n = int(args[0])
        if n is None or not 1 <= n <= 50:
            return [T.CODES_USAGE]
        codes = store.add_codes(n, now)
        return [T.CODES.format(n=n, s=_plural(n), codes="\n".join(codes))]

    if cmd == "/students":
        students = store.list_students(50)
        if not students:
            return [T.NO_STUDENTS]
        lines = []
        for st in students:
            subj = registry.subject(st.subject) if st.subject else None
            lines.append(T.STUDENTS_LINE.format(
                chat_id=st.chat_id, name=_name(st),
                status="✅ verified" if st.verified else "⛔ not verified",
                year=st.year, subject=(subj.title if subj else (st.subject or "—")),
                date=_date(st.last_seen)))
        return [T.STUDENTS.format(n=len(students), lines="\n".join(lines))]

    if cmd == "/student":
        chat_id = _parse_chat_id(args)
        if chat_id is None:
            return [T.STUDENT_USAGE]
        st = store.get_student(chat_id)
        if st is None:
            return [T.NOT_FOUND.format(chat_id=chat_id)]
        subj = registry.subject(st.subject) if st.subject else None
        topic = registry.topic(st.topic) if st.topic else None
        level_parts = []
        for _s, topic_id, level in store.levels(chat_id):
            t = registry.topic(topic_id)
            level_parts.append(f"{t.label if t else topic_id}: L{level}")
        total, correct = store.attempt_stats(0, chat_id)
        recent = []
        for a in store.recent_attempts(chat_id, 10):
            mark = "⏭" if a.skipped else ("✅" if a.correct else "❌")
            recent.append(T.STUDENT_RECENT_LINE.format(
                datetime=_date(a.ts), skill=a.skill, level=a.level, mark=mark))
        return [T.STUDENT.format(
            name=_name(st), chat_id=chat_id,
            status="✅ verified" if st.verified else "⛔ not verified",
            year=st.year, subject=(subj.title if subj else "—"),
            topic=(topic.label if topic else (st.topic or "—")),
            levels="; ".join(level_parts) or "—", total=total, correct=correct,
            recent="\n".join(recent) or "—")]

    if cmd == "/reset":
        chat_id = _parse_chat_id(args)
        if chat_id is None:
            return [T.RESET_USAGE]
        st = store.get_student(chat_id)
        if st is None:
            return [T.NOT_FOUND.format(chat_id=chat_id)]
        st.verified = False
        st.step = "code"
        store.save_student(st)
        store.clear_pending(chat_id)
        store.clear_seen(chat_id)
        return [T.RESET_OK.format(chat_id=chat_id)]

    if cmd == "/flags":
        # Listing never marks anything: delivery happens later, in the adapter, and may fail.
        # The owner confirms with "/flags done [N]" once the flags have been dealt with.
        flags = store.unreviewed_flags()
        if not args:
            if not flags:
                return [T.NO_FLAGS]
            lines = [T.FLAGS_LINE.format(id=f.id, datetime=_date(f.ts), kind=f.kind, chat_id=f.chat_id,
                                         name=_name(store.get_student(f.chat_id)), text=f.text)
                     for f in flags]
            return [T.FLAGS.format(n=len(flags), s=_plural(len(flags)), lines="\n".join(lines),
                                   last=flags[-1].id)]
        if args[0].lower() not in ("done", "ok") or len(args) > 2:
            return [T.FLAGS_USAGE]
        upto = None
        if len(args) == 2:
            try:
                upto = int(args[1].lstrip("#"))
            except ValueError:
                return [T.FLAGS_USAGE]
        done = [f.id for f in flags if upto is None or f.id <= upto]
        if not done:
            return [T.NO_FLAGS]
        store.mark_flags_reviewed(done)
        store.delete_reviewed_orphan_flags()
        return [T.FLAGS_DONE.format(n=len(done), s=_plural(len(done)))]

    if cmd == "/stats":
        students = store.list_students(1_000_000)
        day_start = now - (now % 86400)
        week_total, week_correct = store.attempt_stats(now - 7 * 86400)
        today_total, _ = store.attempt_stats(day_start)
        acc = round(100 * week_correct / week_total) if week_total else 0
        return [T.STATS.format(
            total=len(students), verified=sum(1 for s in students if s.verified),
            active7=sum(1 for s in students if s.last_seen >= now - 7 * 86400),
            today=today_total, week=week_total, acc=acc, codes=store.count_unused_codes(),
            llm=store.llm_calls_total(time.strftime("%Y-%m-%d", time.gmtime(now))),
            flags=len(store.unreviewed_flags()))]

    return []
