"""SQLite storage (standard library only)."""
from __future__ import annotations

import contextlib
import logging
import os
import secrets
import sqlite3
from dataclasses import dataclass
from typing import ContextManager, Iterable

from .content import Problem, problem_from_json, problem_to_json

log = logging.getLogger(__name__)

CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"     # no 0/O, 1/I/L
CODE_LENGTH = 8

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS codes (
  code TEXT PRIMARY KEY, created_at REAL NOT NULL, used_by INTEGER, used_at REAL);
CREATE TABLE IF NOT EXISTS students (
  chat_id INTEGER PRIMARY KEY, first_name TEXT NOT NULL DEFAULT '', username TEXT NOT NULL DEFAULT '',
  verified INTEGER NOT NULL DEFAULT 0,
  step TEXT NOT NULL DEFAULT 'code' CHECK (step IN ('code','year','subject','topic','own_topic','lesson')),
  year INTEGER NOT NULL DEFAULT 11, subject TEXT, topic TEXT,
  created_at REAL NOT NULL, last_seen REAL NOT NULL);
CREATE TABLE IF NOT EXISTS progress (
  chat_id INTEGER NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL,
  level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5), PRIMARY KEY (chat_id, subject, topic));
CREATE TABLE IF NOT EXISTS pending (
  chat_id INTEGER PRIMARY KEY, subject TEXT NOT NULL, topic TEXT NOT NULL, skill TEXT NOT NULL,
  level INTEGER NOT NULL, gen_level INTEGER NOT NULL, seed INTEGER NOT NULL, problem_no INTEGER NOT NULL,
  problem_json TEXT NOT NULL, hints_given INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, subject TEXT NOT NULL, topic TEXT NOT NULL,
  skill TEXT NOT NULL, level INTEGER NOT NULL, gen_level INTEGER NOT NULL,
  correct INTEGER NOT NULL, skipped INTEGER NOT NULL DEFAULT 0, ts REAL NOT NULL);
CREATE INDEX IF NOT EXISTS attempts_chat_ts ON attempts (chat_id, ts);
CREATE TABLE IF NOT EXISTS flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, kind TEXT NOT NULL,
  text TEXT NOT NULL, ts REAL NOT NULL, reviewed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS llm_usage (
  chat_id INTEGER NOT NULL, day TEXT NOT NULL, calls INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (chat_id, day));
"""


@dataclass
class Student:
    chat_id: int
    first_name: str
    username: str
    verified: bool
    step: str
    year: int
    subject: str | None
    topic: str | None
    created_at: float
    last_seen: float


@dataclass
class Pending:
    chat_id: int
    subject: str
    topic: str
    skill: str
    level: int
    gen_level: int
    seed: int
    problem_no: int
    problem: Problem
    hints_given: int
    created_at: float


@dataclass
class Attempt:
    chat_id: int
    subject: str
    topic: str
    skill: str
    level: int
    gen_level: int
    correct: bool
    skipped: bool
    ts: float


@dataclass
class Flag:
    id: int
    chat_id: int
    kind: str
    text: str
    ts: float
    reviewed: bool


_STUDENT_COLS = ("chat_id, first_name, username, verified, step, year, subject, topic, "
                 "created_at, last_seen")


def _student(row) -> Student:
    return Student(row[0], row[1], row[2], bool(row[3]), row[4], row[5], row[6], row[7], row[8], row[9])


class Store:
    def __init__(self, path: str, busy_timeout: float = 15.0) -> None:
        self.path = path
        if path != ":memory:":
            parent = os.path.dirname(os.path.abspath(path))
            os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False, timeout=busy_timeout)
        self.conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout * 1000)}")
        if path != ":memory:":
            self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.executescript(SCHEMA)
        self.conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', '1')")

    def close(self) -> None:
        self.conn.close()

    def transaction(self) -> ContextManager:
        return self._transaction()

    def _rollback(self) -> None:
        if self.conn.in_transaction:
            try:
                self.conn.execute("ROLLBACK")
            except sqlite3.Error as e:
                log.error("rollback failed: %s", type(e).__name__)

    @contextlib.contextmanager
    def _transaction(self):
        self._rollback()                    # never start inside a transaction left open by a failure
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self
        except BaseException:
            self._rollback()
            raise
        try:
            self.conn.execute("COMMIT")
        except BaseException:
            self._rollback()                # a failed COMMIT must not leave the transaction open
            raise

    # offset
    def get_offset(self) -> int:
        row = self.conn.execute("SELECT value FROM meta WHERE key = 'tg_offset'").fetchone()
        try:
            return int(row[0]) if row else 0
        except ValueError:
            return 0

    def set_offset(self, offset: int) -> None:
        self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('tg_offset', ?)", (str(int(offset)),))

    # codes
    def add_codes(self, n: int, now: float) -> list[str]:
        codes: list[str] = []
        while len(codes) < n:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            try:
                self.conn.execute("INSERT INTO codes (code, created_at) VALUES (?, ?)", (code, now))
            except sqlite3.IntegrityError:
                continue
            codes.append(code)
        return codes

    def redeem_code(self, code: str, chat_id: int, now: float) -> bool:
        # "used" means used_at is set: used_by may later be cleared by delete_student_data
        cur = self.conn.execute(
            "UPDATE codes SET used_by = ?, used_at = ? WHERE code = ? AND used_at IS NULL",
            (chat_id, now, code))
        return cur.rowcount == 1

    def count_unused_codes(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM codes WHERE used_at IS NULL").fetchone()[0]

    # students
    def get_student(self, chat_id: int) -> Student | None:
        row = self.conn.execute(
            f"SELECT {_STUDENT_COLS} FROM students WHERE chat_id = ?", (chat_id,)).fetchone()
        return _student(row) if row else None

    def upsert_seen(self, chat_id: int, first_name: str, username: str, now: float) -> Student:
        st = self.get_student(chat_id)
        if st is None:
            self.conn.execute(
                "INSERT INTO students (chat_id, first_name, username, verified, step, year, created_at, last_seen) "
                "VALUES (?, ?, ?, 0, 'code', 11, ?, ?)", (chat_id, first_name or "", username or "", now, now))
        else:
            self.conn.execute(
                "UPDATE students SET first_name = ?, username = ?, last_seen = ? WHERE chat_id = ?",
                (first_name or st.first_name, username or st.username, now, chat_id))
        return self.get_student(chat_id)  # type: ignore[return-value]

    def save_student(self, s: Student) -> None:
        self.conn.execute(
            "UPDATE students SET first_name = ?, username = ?, verified = ?, step = ?, year = ?, "
            "subject = ?, topic = ?, last_seen = ? WHERE chat_id = ?",
            (s.first_name, s.username, int(s.verified), s.step, s.year, s.subject, s.topic,
             s.last_seen, s.chat_id))

    def list_students(self, limit: int = 50) -> list[Student]:
        rows = self.conn.execute(
            f"SELECT {_STUDENT_COLS} FROM students ORDER BY last_seen DESC, chat_id LIMIT ?", (limit,)).fetchall()
        return [_student(r) for r in rows]

    def delete_student_data(self, chat_id: int) -> None:
        """Delete everything about a chat EXCEPT unreviewed safety flags: safeguarding records
        stay (unchanged) until the owner has reviewed them with /flags done."""
        for table in ("students", "progress", "pending", "attempts", "llm_usage"):
            self.conn.execute(f"DELETE FROM {table} WHERE chat_id = ?", (chat_id,))
        self.conn.execute("DELETE FROM flags WHERE chat_id = ? AND reviewed = 1", (chat_id,))
        self.conn.execute("UPDATE codes SET used_by = NULL WHERE used_by = ?", (chat_id,))

    # progress
    def get_level(self, chat_id: int, subject: str, topic: str) -> int:
        row = self.conn.execute(
            "SELECT level FROM progress WHERE chat_id = ? AND subject = ? AND topic = ?",
            (chat_id, subject, topic)).fetchone()
        return row[0] if row else 1

    def set_level(self, chat_id: int, subject: str, topic: str, level: int) -> None:
        level = max(1, min(5, int(level)))
        self.conn.execute(
            "INSERT OR REPLACE INTO progress (chat_id, subject, topic, level) VALUES (?, ?, ?, ?)",
            (chat_id, subject, topic, level))

    def levels(self, chat_id: int) -> list[tuple[str, str, int]]:
        rows = self.conn.execute(
            "SELECT subject, topic, level FROM progress WHERE chat_id = ? ORDER BY subject, topic",
            (chat_id,)).fetchall()
        return [(r[0], r[1], r[2]) for r in rows]

    # pending
    def get_pending(self, chat_id: int) -> Pending | None:
        row = self.conn.execute(
            "SELECT chat_id, subject, topic, skill, level, gen_level, seed, problem_no, problem_json, "
            "hints_given, created_at FROM pending WHERE chat_id = ?", (chat_id,)).fetchone()
        if not row:
            return None
        try:
            problem = problem_from_json(row[8])
        except Exception as e:  # noqa: BLE001 - any corruption (bad JSON, missing fields, wrong types)
            # an unreadable stored problem must not break every message: drop it
            log.warning("dropping unreadable pending problem for chat %s (%s)", chat_id, type(e).__name__)
            self.clear_pending(chat_id)
            return None
        return Pending(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],
                       problem, row[9], row[10])

    def set_pending(self, p: Pending) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO pending (chat_id, subject, topic, skill, level, gen_level, seed, "
            "problem_no, problem_json, hints_given, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (p.chat_id, p.subject, p.topic, p.skill, p.level, p.gen_level, p.seed, p.problem_no,
             problem_to_json(p.problem), p.hints_given, p.created_at))

    def clear_pending(self, chat_id: int) -> None:
        self.conn.execute("DELETE FROM pending WHERE chat_id = ?", (chat_id,))

    # attempts
    def add_attempt(self, a: Attempt) -> None:
        self.conn.execute(
            "INSERT INTO attempts (chat_id, subject, topic, skill, level, gen_level, correct, skipped, ts) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (a.chat_id, a.subject, a.topic, a.skill, a.level, a.gen_level, int(a.correct),
             int(a.skipped), a.ts))

    def recent_attempts(self, chat_id: int, limit: int = 10) -> list[Attempt]:
        rows = self.conn.execute(
            "SELECT chat_id, subject, topic, skill, level, gen_level, correct, skipped, ts FROM attempts "
            "WHERE chat_id = ? ORDER BY ts DESC, id DESC LIMIT ?", (chat_id, limit)).fetchall()
        return [Attempt(r[0], r[1], r[2], r[3], r[4], r[5], bool(r[6]), bool(r[7]), r[8]) for r in rows]

    def attempt_stats(self, since: float, chat_id: int | None = None) -> tuple[int, int]:
        sql = "SELECT COUNT(*), COALESCE(SUM(correct), 0) FROM attempts WHERE ts >= ?"
        args: list = [since]
        if chat_id is not None:
            sql += " AND chat_id = ?"
            args.append(chat_id)
        row = self.conn.execute(sql, args).fetchone()
        return int(row[0]), int(row[1])

    # flags
    def add_flag(self, chat_id: int, kind: str, text: str, now: float) -> int:
        cur = self.conn.execute(
            "INSERT INTO flags (chat_id, kind, text, ts) VALUES (?, ?, ?, ?)",
            (chat_id, kind, (text or "")[:500], now))
        return int(cur.lastrowid)

    def unreviewed_flags(self) -> list[Flag]:
        rows = self.conn.execute(
            "SELECT id, chat_id, kind, text, ts, reviewed FROM flags WHERE reviewed = 0 ORDER BY id").fetchall()
        return [Flag(r[0], r[1], r[2], r[3], r[4], bool(r[5])) for r in rows]

    def mark_flags_reviewed(self, ids: Iterable[int]) -> None:
        for i in ids:
            self.conn.execute("UPDATE flags SET reviewed = 1 WHERE id = ?", (i,))

    def delete_reviewed_orphan_flags(self) -> None:
        """Reviewed flags of students who deleted their data are removed for good."""
        self.conn.execute("DELETE FROM flags WHERE reviewed = 1 AND chat_id NOT IN (SELECT chat_id FROM students)")

    # llm usage
    def llm_calls(self, chat_id: int, day: str) -> int:
        row = self.conn.execute(
            "SELECT calls FROM llm_usage WHERE chat_id = ? AND day = ?", (chat_id, day)).fetchone()
        return row[0] if row else 0

    def incr_llm_calls(self, chat_id: int, day: str) -> None:
        self.conn.execute(
            "INSERT INTO llm_usage (chat_id, day, calls) VALUES (?, ?, 1) "
            "ON CONFLICT(chat_id, day) DO UPDATE SET calls = calls + 1", (chat_id, day))

    def llm_calls_total(self, day: str) -> int:
        row = self.conn.execute("SELECT COALESCE(SUM(calls), 0) FROM llm_usage WHERE day = ?", (day,)).fetchone()
        return int(row[0])
