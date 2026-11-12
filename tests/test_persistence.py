import json
import os
import random
import sqlite3
import tempfile
import unittest

import helpers
from helpers import (send, make_engine, get_codes, verify, to_topic, answer_of, FakeClock, CORRECT, CODE_OK,
                     SUBJECT_ASK, CHANGE_YEAR, START)
from tutor.config import Config
from tutor.content import Answer, Problem, Mistake
from tutor.db import Store, Student, Pending, Attempt


class TestRestart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "t.db")

    def reopen(self, rng_seed=12345, clock=None):
        from tutor.engine import Engine
        store = Store(self.path)
        self.addCleanup(store.close)
        cfg = Config(owner_id=999, db_path=self.path)
        engine = Engine(store, cfg, registry=helpers.shared_registry(), llm=None,
                        clock=clock or FakeClock(START + 60), rng=random.Random(rng_seed))
        return engine, store

    def test_lesson_survives_restart(self):
        engine, store, clock = make_engine(path=self.path)
        to_topic(engine, 5, year=10, topic="GCSE Higher: trig & geometry")
        send(engine, 5, answer_of(store, 5))             # level 2, problem 2
        pending = store.get_pending(5)
        self.assertEqual((pending.problem_no, pending.level), (2, 2))
        ans = pending.problem.answer.display
        topic = store.get_student(5).topic
        unused = get_codes(engine, 2)
        store.close()

        engine2, store2 = self.reopen()
        st = store2.get_student(5)
        self.assertTrue(st.verified)
        self.assertEqual((st.year, st.subject, st.topic, st.step), (10, "maths", topic, "lesson"))
        self.assertEqual(store2.get_level(5, "maths", topic), 2)
        p2 = store2.get_pending(5)
        self.assertEqual(p2.problem, pending.problem)
        self.assertEqual((p2.problem_no, p2.seed, p2.skill, p2.level, p2.gen_level),
                         (pending.problem_no, pending.seed, pending.skill, pending.level, pending.gen_level))
        out = send(engine2, 5, ans)
        self.assertEqual(out[0].text, CORRECT(pending.problem.solution))
        self.assertEqual(store2.get_pending(5).problem_no, 3)
        self.assertEqual(store2.get_level(5, "maths", topic), 3)
        self.assertEqual(len(store2.recent_attempts(5)), 2)
        self.assertEqual(store2.count_unused_codes(), 2)
        # unused codes still redeemable
        self.assertEqual(send(engine2, 6, unused[0])[0].text, CODE_OK)

    def test_start_after_restart_needs_no_code(self):
        engine, store, clock = make_engine(path=self.path)
        verify(engine, 5)
        store.close()
        engine2, store2 = self.reopen()
        out = send(engine2, 5, "/start")
        self.assertEqual(out[0].text, SUBJECT_ASK(11))

    def test_used_code_stays_used(self):
        engine, store, clock = make_engine(path=self.path)
        code = get_codes(engine, 1)[0]
        send(engine, 5, code)
        store.close()
        engine2, store2 = self.reopen()
        self.assertEqual(send(engine2, 6, code)[0].text, helpers.CODE_BAD)

    def test_corrupt_pending_does_not_loop_on_error(self):
        engine, store, clock = make_engine(path=self.path)
        to_topic(engine, 5)
        store.conn.execute("UPDATE pending SET problem_json = '{broken' WHERE chat_id = 5")
        out = send(engine, 5, "42")
        self.assertNotEqual(out[0].text, helpers.ERROR)
        self.assertEqual(out[0].text, helpers.TOPIC_ASK(11))
        self.assertIsNone(store.get_pending(5))
        out = send(engine, 5, helpers.HIGHER_ALGEBRA)          # and the lesson goes on
        self.assertTrue(out[-1].text.startswith("Problem 1:"))

    def test_offset_roundtrip(self):
        s = Store(self.path)
        self.assertEqual(s.get_offset(), 0)
        s.set_offset(12345)
        self.assertEqual(s.get_offset(), 12345)
        s.set_offset(12400)
        s.close()
        s2 = Store(self.path)
        self.addCleanup(s2.close)
        self.assertEqual(s2.get_offset(), 12400)

    def test_parent_directory_is_created(self):
        deep = os.path.join(self.tmp.name, "a", "b", "c.db")
        s = Store(deep)
        s.set_offset(1)
        s.close()
        self.assertTrue(os.path.exists(deep))

    def test_memory_store(self):
        s = Store(":memory:")
        self.assertEqual(s.get_offset(), 0)
        s.set_offset(7)
        self.assertEqual(s.get_offset(), 7)
        s.close()


class StoreCase(unittest.TestCase):
    def setUp(self):
        self.s = Store(":memory:")
        self.addCleanup(self.s.close)


class TestStoreCodes(StoreCase):
    def test_add_and_redeem(self):
        codes = self.s.add_codes(5, 100.0)
        self.assertEqual(len(codes), 5)
        self.assertEqual(len(set(codes)), 5)
        for c in codes:
            self.assertRegex(c, helpers.CODE_RE)
        self.assertEqual(self.s.count_unused_codes(), 5)
        self.assertTrue(self.s.redeem_code(codes[0], 1, 101.0))
        self.assertEqual(self.s.count_unused_codes(), 4)
        self.assertFalse(self.s.redeem_code(codes[0], 1, 102.0))
        self.assertFalse(self.s.redeem_code(codes[0], 2, 102.0))
        self.assertFalse(self.s.redeem_code("NOTACODE", 2, 102.0))
        self.assertEqual(self.s.count_unused_codes(), 4)

    def test_add_zero(self):
        self.assertEqual(self.s.add_codes(0, 1.0), [])


class TestStoreStudents(StoreCase):
    def test_upsert_seen_defaults(self):
        st = self.s.upsert_seen(5, "Al", "al", 100.0)
        self.assertEqual((st.chat_id, st.first_name, st.username, st.verified, st.step, st.year, st.subject, st.topic),
                         (5, "Al", "al", False, "code", 11, None, None))
        self.assertEqual((st.created_at, st.last_seen), (100.0, 100.0))

    def test_upsert_seen_updates_last_seen_only(self):
        self.s.upsert_seen(5, "Al", "al", 100.0)
        st = self.s.get_student(5)
        st.verified = True
        st.step = "subject"
        st.year = 9
        self.s.save_student(st)
        st2 = self.s.upsert_seen(5, "Alan", "alan", 200.0)
        self.assertTrue(st2.verified)
        self.assertEqual((st2.step, st2.year), ("subject", 9))
        self.assertEqual(st2.created_at, 100.0)
        self.assertEqual(st2.last_seen, 200.0)
        self.assertEqual(st2.first_name, "Alan")

    def test_get_unknown(self):
        self.assertIsNone(self.s.get_student(404))

    def test_save_roundtrip(self):
        st = self.s.upsert_seen(5, "Al", "", 100.0)
        st.verified, st.step, st.year, st.subject, st.topic = True, "lesson", 8, "maths", "maths.y8.ks3_algebra"
        self.s.save_student(st)
        got = self.s.get_student(5)
        self.assertEqual(got, st)

    def test_list_order_and_limit(self):
        for i, t in enumerate((10.0, 30.0, 20.0)):
            self.s.upsert_seen(i + 1, f"n{i}", "", t)
        self.assertEqual([x.chat_id for x in self.s.list_students()], [2, 3, 1])
        self.assertEqual([x.chat_id for x in self.s.list_students(limit=2)], [2, 3])

    def test_levels(self):
        self.assertEqual(self.s.get_level(5, "maths", "t1"), 1)
        self.s.set_level(5, "maths", "t1", 4)
        self.s.set_level(5, "maths", "t2", 2)
        self.s.set_level(5, "maths", "t1", 5)
        self.assertEqual(self.s.get_level(5, "maths", "t1"), 5)
        self.assertEqual(sorted(self.s.levels(5)), [("maths", "t1", 5), ("maths", "t2", 2)])
        self.assertEqual(self.s.levels(6), [])
        self.assertEqual(self.s.get_level(6, "maths", "t1"), 1)


class TestStorePendingAttemptsFlags(StoreCase):
    def pending(self):
        prob = Problem("maths.x", 2, 77, "What is 2 + 2?", Answer("number", "4", 4.0, dp=0), "2 + 2 = 4",
                       "Count on", (Mistake(Answer("number", "5", 5.0), "Off by one"),))
        return Pending(chat_id=5, subject="maths", topic="t1", skill="maths.x", level=3, gen_level=3, seed=77,
                       problem_no=4, problem=prob, hints_given=1, created_at=50.0)

    def test_pending_roundtrip(self):
        p = self.pending()
        self.assertIsNone(self.s.get_pending(5))
        self.s.set_pending(p)
        self.assertEqual(self.s.get_pending(5), p)
        p.problem_no = 5
        self.s.set_pending(p)
        self.assertEqual(self.s.get_pending(5).problem_no, 5)
        self.s.clear_pending(5)
        self.assertIsNone(self.s.get_pending(5))
        self.s.clear_pending(5)      # idempotent

    def test_attempts(self):
        for i in range(12):
            self.s.add_attempt(Attempt(5, "maths", "t1", "maths.x", 2, 2, i % 3 == 0, False, 100.0 + i))
        self.s.add_attempt(Attempt(6, "maths", "t1", "maths.x", 1, 1, True, False, 300.0))
        got = self.s.recent_attempts(5)
        self.assertEqual(len(got), 10)
        self.assertEqual(got[0].ts, 111.0)
        self.assertEqual(len(self.s.recent_attempts(5, 3)), 3)
        self.assertEqual(self.s.attempt_stats(0.0, 5), (12, 4))
        self.assertEqual(self.s.attempt_stats(0.0), (13, 5))
        self.assertEqual(self.s.attempt_stats(109.5, 5), (2, 0))
        self.assertEqual(self.s.attempt_stats(1000.0), (0, 0))

    def test_flags(self):
        a = self.s.add_flag(5, "distress", "x" * 800, 10.0)
        b = self.s.add_flag(6, "distress", "short", 11.0)
        self.assertNotEqual(a, b)
        flags = self.s.unreviewed_flags()
        self.assertEqual([f.id for f in flags], [a, b])
        self.assertEqual(len(flags[0].text), 500)
        self.assertEqual((flags[1].chat_id, flags[1].kind, flags[1].text, flags[1].reviewed), (6, "distress", "short", False))
        self.s.mark_flags_reviewed([a])
        self.assertEqual([f.id for f in self.s.unreviewed_flags()], [b])
        self.s.mark_flags_reviewed([])
        self.assertEqual(len(self.s.unreviewed_flags()), 1)

    def test_llm_counters(self):
        self.assertEqual(self.s.llm_calls(5, "2024-01-01"), 0)
        self.s.incr_llm_calls(5, "2024-01-01")
        self.s.incr_llm_calls(5, "2024-01-01")
        self.s.incr_llm_calls(6, "2024-01-01")
        self.s.incr_llm_calls(5, "2024-01-02")
        self.assertEqual(self.s.llm_calls(5, "2024-01-01"), 2)
        self.assertEqual(self.s.llm_calls_total("2024-01-01"), 3)
        self.assertEqual(self.s.llm_calls_total("2024-01-02"), 1)
        self.assertEqual(self.s.llm_calls_total("2030-01-01"), 0)

    def test_transaction_commit_and_rollback(self):
        with self.s.transaction():
            self.s.set_offset(10)
        self.assertEqual(self.s.get_offset(), 10)
        with self.assertRaises(RuntimeError):
            with self.s.transaction():
                self.s.set_offset(99)
                self.s.add_flag(5, "k", "t", 1.0)
                raise RuntimeError("boom")
        self.assertEqual(self.s.get_offset(), 10)
        self.assertEqual(self.s.unreviewed_flags(), [])

    def test_commit_failure_rolls_back_and_next_transaction_works(self):
        real = self.s.conn

        class FailingCommit:
            """Delegates to the real connection but fails the next COMMIT once."""
            def __init__(self):
                self.fail = True

            def execute(self, sql, *args):
                if sql.strip().upper() == "COMMIT" and self.fail:
                    self.fail = False
                    raise sqlite3.OperationalError("disk I/O error")
                return real.execute(sql, *args)

            def __getattr__(self, name):
                return getattr(real, name)

        self.s.conn = FailingCommit()
        with self.assertRaises(sqlite3.OperationalError):
            with self.s.transaction():
                self.s.set_offset(42)
        self.assertFalse(real.in_transaction)              # not left open
        self.assertEqual(self.s.get_offset(), 0)           # rolled back
        with self.s.transaction():                         # the next message works
            self.s.set_offset(43)
        self.assertEqual(self.s.get_offset(), 43)
        self.s.conn = real

    def test_stale_open_transaction_is_rolled_back_before_begin(self):
        self.s.conn.execute("BEGIN")
        self.s.set_offset(5)
        with self.s.transaction():
            self.s.set_offset(6)
        self.assertEqual(self.s.get_offset(), 6)

    def test_corrupt_pending_is_dropped(self):
        self.s.set_pending(self.pending())
        for bad in ("{not json", "{}", '{"skill_id": 1}', "null", "[]"):
            with self.subTest(json=bad):
                self.s.set_pending(self.pending())
                self.s.conn.execute("UPDATE pending SET problem_json = ? WHERE chat_id = 5", (bad,))
                with self.assertLogs("tutor.db", level="WARNING"):
                    self.assertIsNone(self.s.get_pending(5))
                self.assertEqual(self.s.conn.execute("SELECT COUNT(*) FROM pending").fetchone()[0], 0)

    def test_busy_timeout_is_configurable(self):
        s = Store(":memory:", busy_timeout=60)
        self.addCleanup(s.close)
        self.assertEqual(s.conn.execute("PRAGMA busy_timeout").fetchone()[0], 60000)
        self.assertGreaterEqual(self.s.conn.execute("PRAGMA busy_timeout").fetchone()[0], 15000)

    def test_delete_student_data(self):
        st = self.s.upsert_seen(5, "Al", "", 1.0)
        self.s.upsert_seen(6, "Bo", "", 1.0)
        self.s.set_level(5, "maths", "t", 3)
        self.s.set_level(6, "maths", "t", 3)
        self.s.set_pending(self.pending())
        self.s.add_attempt(Attempt(5, "maths", "t", "maths.x", 1, 1, True, False, 1.0))
        reviewed = self.s.add_flag(5, "distress", "old", 1.0)
        self.s.mark_flags_reviewed([reviewed])
        self.s.add_flag(5, "distress", "x", 1.0)
        self.s.incr_llm_calls(5, "2024-01-01")
        self.s.add_flag(6, "distress", "keep", 1.0)
        self.s.delete_student_data(5)
        self.assertIsNone(self.s.get_student(5))
        self.assertIsNone(self.s.get_pending(5))
        self.assertEqual(self.s.levels(5), [])
        self.assertEqual(self.s.recent_attempts(5), [])
        self.assertEqual(self.s.llm_calls(5, "2024-01-01"), 0)
        # unreviewed safety flags stay unchanged until reviewed; reviewed ones are deleted
        self.assertEqual([(f.chat_id, f.text) for f in self.s.unreviewed_flags()], [(5, "x"), (6, "keep")])
        self.assertEqual(self.s.conn.execute("SELECT COUNT(*) FROM flags WHERE chat_id = 5").fetchone()[0], 1)
        self.s.mark_flags_reviewed([f.id for f in self.s.unreviewed_flags() if f.chat_id == 5])
        self.s.delete_reviewed_orphan_flags()
        self.assertEqual(self.s.conn.execute("SELECT COUNT(*) FROM flags WHERE chat_id = 5").fetchone()[0], 0)
        self.assertIsNotNone(self.s.get_student(6))
        self.assertEqual(self.s.get_level(6, "maths", "t"), 3)
        self.s.delete_student_data(12345)      # unknown chat is fine


V1_SCHEMA = """
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

V1_PROBLEM = {"skill_id": "maths.percentages", "level": 2, "seed": 77, "text": "What is 10% of 50?",
              "answer": {"kind": "number", "display": "5", "value": 5.0, "dp": None, "sf": None, "form": "any",
                         "ordered": False, "var": "x", "mark_scheme": "", "max_marks": 0},
              "solution": "10% of 50 = 5", "hint": "Divide by 10", "mistakes": []}      # a v1 row: no "ref"


class TestSchemaMigration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "v1.db")

    def build_v1(self, version="1"):
        conn = sqlite3.connect(self.path)
        conn.executescript(V1_SCHEMA)
        conn.execute("INSERT INTO meta (key, value) VALUES ('schema_version', ?)", (version,))
        conn.execute("INSERT INTO students (chat_id, verified, step, year, subject, topic, created_at, last_seen) "
                     "VALUES (5, 1, 'lesson', 11, 'maths', 'maths.y11.foundation_number', 1.0, 2.0)")
        conn.execute("INSERT INTO pending (chat_id, subject, topic, skill, level, gen_level, seed, problem_no, problem_json, "
                     "hints_given, created_at) VALUES (5, 'maths', 'maths.y11.foundation_number', 'maths.percentages', 2, 2, "
                     "77, 3, ?, 0, 3.0)", (json.dumps(V1_PROBLEM),))
        conn.execute("INSERT INTO progress (chat_id, subject, topic, level) VALUES (5, 'maths', 'maths.y11.foundation_number', 2)")
        conn.commit()
        conn.close()

    def version(self, store):
        return store.conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0]

    def test_v1_database_is_migrated_to_version_2(self):
        self.build_v1()
        store = Store(self.path)
        self.addCleanup(store.close)
        self.assertEqual(self.version(store), "2")
        tables = {r[0] for r in store.conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertIn("seen", tables)
        cols = [r[1] for r in store.conn.execute("PRAGMA table_info(seen)")]
        self.assertEqual(cols, ["id", "chat_id", "skill", "fp"])
        idx = {r[0] for r in store.conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
        self.assertIn("seen_chat_skill", idx)

    def test_v1_pending_row_loads_with_empty_ref(self):
        self.build_v1()
        store = Store(self.path)
        self.addCleanup(store.close)
        p = store.get_pending(5)
        self.assertIsNotNone(p)
        self.assertEqual(p.problem.ref, "")
        self.assertEqual((p.problem.skill_id, p.problem.text, p.problem_no, p.seed), ("maths.percentages", "What is 10% of 50?", 3, 77))
        self.assertEqual(p.problem.answer.display, "5")
        self.assertEqual(store.get_level(5, "maths", "maths.y11.foundation_number"), 2)
        self.assertTrue(store.get_student(5).verified)

    def test_v1_data_survives_and_seen_is_usable(self):
        self.build_v1()
        store = Store(self.path)
        self.addCleanup(store.close)
        self.assertEqual(store.recent_seen(5, "maths.percentages"), [])
        store.add_seen(5, "maths.percentages", "t:abc")
        self.assertEqual(store.recent_seen(5, "maths.percentages"), ["t:abc"])

    def test_engine_continues_a_v1_lesson(self):
        import random as _r
        from tutor.engine import Engine
        self.build_v1()
        store = Store(self.path)
        self.addCleanup(store.close)
        engine = Engine(store, Config(owner_id=999, db_path=self.path), registry=helpers.shared_registry(), llm=None,
                        clock=FakeClock(START + 60), rng=_r.Random(3))
        out = send(engine, 5, "5")
        self.assertEqual(out[0].text, CORRECT("10% of 50 = 5"))
        self.assertEqual(store.get_pending(5).problem_no, 4)

    def test_reopening_is_idempotent_and_fresh_db_is_version_2(self):
        Store(self.path).close()
        store = Store(self.path)
        self.addCleanup(store.close)
        self.assertEqual(self.version(store), "2")
        store.close()
        store = Store(self.path)
        self.addCleanup(store.close)
        self.assertEqual(self.version(store), "2")
        self.assertEqual(store.conn.execute("SELECT COUNT(*) FROM meta WHERE key = 'schema_version'").fetchone()[0], 1)
        mem = Store(":memory:")
        self.addCleanup(mem.close)
        self.assertEqual(self.version(mem), "2")

    def test_newer_version_warns_and_continues(self):
        self.build_v1(version="3")
        with self.assertLogs(level="WARNING"):
            store = Store(self.path)
        self.addCleanup(store.close)
        self.assertEqual(self.version(store), "3")
        self.assertIsNotNone(store.get_pending(5))
        store.add_seen(5, "s", "x")
        self.assertEqual(store.recent_seen(5, "s"), ["x"])


if __name__ == "__main__":
    unittest.main()
