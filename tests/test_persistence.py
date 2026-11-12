import os
import random
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

    def test_delete_student_data(self):
        st = self.s.upsert_seen(5, "Al", "", 1.0)
        self.s.upsert_seen(6, "Bo", "", 1.0)
        self.s.set_level(5, "maths", "t", 3)
        self.s.set_level(6, "maths", "t", 3)
        self.s.set_pending(self.pending())
        self.s.add_attempt(Attempt(5, "maths", "t", "maths.x", 1, 1, True, False, 1.0))
        self.s.add_flag(5, "distress", "x", 1.0)
        self.s.incr_llm_calls(5, "2024-01-01")
        self.s.add_flag(6, "distress", "keep", 1.0)
        self.s.delete_student_data(5)
        self.assertIsNone(self.s.get_student(5))
        self.assertIsNone(self.s.get_pending(5))
        self.assertEqual(self.s.levels(5), [])
        self.assertEqual(self.s.recent_attempts(5), [])
        self.assertEqual(self.s.llm_calls(5, "2024-01-01"), 0)
        self.assertEqual([f.chat_id for f in self.s.unreviewed_flags()], [6])
        self.assertIsNotNone(self.s.get_student(6))
        self.assertEqual(self.s.get_level(6, "maths", "t"), 3)
        self.s.delete_student_data(12345)      # unknown chat is fine


if __name__ == "__main__":
    unittest.main()
