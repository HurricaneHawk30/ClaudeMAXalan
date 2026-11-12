"""docs/ARCHITECTURE_V2.md sections 3.2 and 3.3: repeat avoidance and the `seen` table."""
import os
import tempfile
import unittest

import helpers
from helpers import send, make_engine, verify, to_topic, SKIP
from tutor.config import Config
from tutor.content import Registry, register_bank, fingerprint
from tutor.db import Store, SEEN_KEEP

REPEAT = os.path.join(helpers.FIXTURES, "repeat_bank.json")
CH = 1


def repeat_registry():
    reg = Registry()
    register_bank(reg, REPEAT)
    return reg


class RepeatCase(unittest.TestCase):
    def setUp(self):
        self.reg = repeat_registry()
        self.engine, self.store, self.clock = make_engine(registry=self.reg, flood=100000)
        self.addCleanup(self.store.close)

    def start(self, topic, chat=CH):
        verify(self.engine, chat)
        send(self.engine, chat, "Repeat Test")
        return send(self.engine, chat, topic)

    def ref(self, chat=CH):
        return self.store.get_pending(chat).problem.ref

    def skip_refs(self, n, chat=CH):
        refs = [self.ref(chat)]
        for _ in range(n - 1):
            out = send(self.engine, chat, "skip")
            self.assertTrue(out[0].text.startswith("👀"), out[0].text)
            refs.append(self.ref(chat))
        return refs


class TestNoRepeats(RepeatCase):
    def test_six_item_level_gives_six_different_refs_then_the_least_recently_seen(self):
        self.start("Six items")
        refs = self.skip_refs(6)
        self.assertEqual(len(set(refs)), 6, refs)
        self.assertTrue(all(r.startswith("rep.six#s") for r in refs))
        self.assertEqual(self.store.get_level(CH, "rep", "rep.y11.six"), 1)         # skipping at level 1 stays at 1
        out = send(self.engine, CH, "skip")
        self.assertEqual(self.ref(), refs[0])               # the 7th problem is the oldest one seen
        send(self.engine, CH, "skip")
        self.assertEqual(self.ref(), refs[1])
        send(self.engine, CH, "skip")
        self.assertEqual(self.ref(), refs[2])

    def test_never_the_same_problem_twice_in_a_row(self):
        self.start("Six items")
        prev = self.ref()
        for _ in range(40):
            send(self.engine, CH, "skip")
            cur = self.ref()
            self.assertNotEqual(cur, prev)
            prev = cur

    def test_two_item_level_alternates(self):
        self.start("Two items")
        refs = self.skip_refs(10)
        self.assertEqual(len(set(refs)), 2)
        for a, b, c in zip(refs, refs[1:], refs[2:]):
            self.assertNotEqual(a, b)
            self.assertEqual(a, c)

    def test_wrong_answers_also_avoid_the_repeat(self):
        self.start("Six items")
        refs = [self.ref()]
        for _ in range(5):
            send(self.engine, CH, "zzz not an answer 12")        # unparsed: no new problem
            self.assertEqual(self.ref(), refs[-1])
            send(self.engine, CH, "skip")
            refs.append(self.ref())
        self.assertEqual(len(set(refs)), 6)

    def test_correct_answers_move_to_a_different_item(self):
        self.start("Six items")
        for _ in range(8):
            before = self.ref()
            p = self.store.get_pending(CH)
            send(self.engine, CH, p.problem.answer.display)
            self.assertNotEqual(self.ref(), before)

    def test_generator_skills_never_repeat_consecutively(self):
        engine, store, clock = make_engine(flood=100000)
        self.addCleanup(store.close)
        to_topic(engine, 7, topic="GCSE Foundation: number")
        prev = store.get_pending(7).problem
        for _ in range(40):
            send(engine, 7, "skip")
            cur = store.get_pending(7).problem
            self.assertNotEqual(cur.text, prev.text)
            self.assertNotEqual(fingerprint(cur), fingerprint(prev))
            prev = cur

    def test_students_have_independent_histories(self):
        self.start("Six items", chat=1)
        self.start("Six items", chat=2)
        a = self.skip_refs(6, chat=1)
        b = self.skip_refs(6, chat=2)
        self.assertEqual(len(set(a)), 6)
        self.assertEqual(len(set(b)), 6)
        self.assertEqual(len(self.store.recent_seen(1, "rep.six")), 6)
        self.assertEqual(len(self.store.recent_seen(2, "rep.six")), 6)


class TestNeverTwoRubricInARow(RepeatCase):
    def test_no_two_rubric_problems_in_a_row(self):
        self.start("Mixed items")
        kinds = [self.store.get_pending(CH).problem.answer.kind]
        for _ in range(50):
            if kinds[-1] == "rubric":
                out = send(self.engine, CH, "my long written answer")
                self.assertTrue(out[0].text.startswith("📝"), out[0].text)
            else:
                send(self.engine, CH, "skip")
            kinds.append(self.store.get_pending(CH).problem.answer.kind)
        self.assertIn("rubric", kinds)
        self.assertIn("choice", kinds)
        for a, b in zip(kinds, kinds[1:]):
            self.assertFalse(a == "rubric" and b == "rubric", kinds)
        self.assertEqual(self.store.recent_attempts(CH)[0].skipped, True)


class TestSeenRecords(RepeatCase):
    def test_engine_records_each_problem_newest_first(self):
        self.start("Six items")
        refs = self.skip_refs(4)
        self.assertEqual(self.store.recent_seen(CH, "rep.six"), list(reversed(refs)))
        self.assertEqual(self.store.recent_seen(CH, "rep.two"), [])

    def test_generator_problems_use_text_fingerprints(self):
        engine, store, clock = make_engine(flood=100000)
        self.addCleanup(store.close)
        to_topic(engine, 7, topic="GCSE Foundation: number")
        p = store.get_pending(7)
        seen = store.recent_seen(7, p.skill)
        self.assertEqual(seen, [fingerprint(p.problem)])
        self.assertTrue(seen[0].startswith("t:"))

    def test_delete_my_data_clears_seen(self):
        self.start("Six items")
        self.skip_refs(3)
        self.assertTrue(self.store.recent_seen(CH, "rep.six"))
        out = send(self.engine, CH, "/delete_my_data")
        self.assertEqual(out[0].text, helpers.DELETED)
        self.assertEqual(self.store.recent_seen(CH, "rep.six"), [])
        rows = self.store.conn.execute("SELECT COUNT(*) FROM seen WHERE chat_id = ?", (CH,)).fetchone()[0]
        self.assertEqual(rows, 0)

    def test_reset_clears_seen(self):
        self.start("Six items")
        self.skip_refs(3)
        send(self.engine, 999, f"/reset {CH}")
        self.assertEqual(self.store.recent_seen(CH, "rep.six"), [])

    def test_other_chats_keep_their_seen_rows(self):
        self.start("Six items", chat=1)
        self.start("Six items", chat=2)
        self.skip_refs(3, chat=1)
        self.skip_refs(3, chat=2)
        send(self.engine, 1, "/delete_my_data")
        self.assertEqual(len(self.store.recent_seen(2, "rep.six")), 3)


class TestSeenStore(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)

    def test_constants_and_order(self):
        self.assertEqual(SEEN_KEEP, 30)
        self.assertEqual(self.store.recent_seen(1, "s"), [])
        for i in range(5):
            self.store.add_seen(1, "s", f"fp{i}")
        self.assertEqual(self.store.recent_seen(1, "s"), ["fp4", "fp3", "fp2", "fp1", "fp0"])
        self.assertEqual(self.store.recent_seen(1, "s", limit=2), ["fp4", "fp3"])
        self.assertEqual(self.store.recent_seen(1, "other"), [])
        self.assertEqual(self.store.recent_seen(2, "s"), [])

    def test_pruned_to_30_newest(self):
        for i in range(45):
            self.store.add_seen(1, "s", f"fp{i}")
        got = self.store.recent_seen(1, "s")
        self.assertEqual(len(got), 30)
        self.assertEqual(got[0], "fp44")
        self.assertEqual(got[-1], "fp15")
        n = self.store.conn.execute("SELECT COUNT(*) FROM seen WHERE chat_id=1 AND skill='s'").fetchone()[0]
        self.assertEqual(n, 30)
        self.assertEqual(len(self.store.recent_seen(1, "s", limit=100)), 30)

    def test_pruning_is_per_chat_and_skill(self):
        for i in range(35):
            self.store.add_seen(1, "a", f"x{i}")
            self.store.add_seen(1, "b", f"y{i}")
            self.store.add_seen(2, "a", f"z{i}")
        for chat, skill in ((1, "a"), (1, "b"), (2, "a")):
            self.assertEqual(len(self.store.recent_seen(chat, skill)), 30)

    def test_re_adding_moves_to_newest_without_duplicates(self):
        for i in range(4):
            self.store.add_seen(1, "s", f"fp{i}")
        self.store.add_seen(1, "s", "fp1")
        self.assertEqual(self.store.recent_seen(1, "s"), ["fp1", "fp3", "fp2", "fp0"])

    def test_custom_keep(self):
        for i in range(10):
            self.store.add_seen(1, "s", f"fp{i}", keep=3)
        self.assertEqual(self.store.recent_seen(1, "s"), ["fp9", "fp8", "fp7"])

    def test_delete_student_data_removes_seen(self):
        self.store.add_seen(1, "s", "a")
        self.store.add_seen(2, "s", "b")
        self.store.delete_student_data(1)
        self.assertEqual(self.store.recent_seen(1, "s"), [])
        self.assertEqual(self.store.recent_seen(2, "s"), ["b"])

    def test_unique_constraint_and_index_exist(self):
        rows = self.store.conn.execute("SELECT name FROM sqlite_master WHERE tbl_name = 'seen'").fetchall()
        names = {r[0] for r in rows}
        self.assertIn("seen", names)
        self.assertIn("seen_chat_skill", names)


class TestSeenPersistence(unittest.TestCase):
    def test_persists_across_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.db")
            store = Store(path)
            for i in range(3):
                store.add_seen(5, "s", f"fp{i}")
            store.close()
            store2 = Store(path)
            self.addCleanup(store2.close)
            self.assertEqual(store2.recent_seen(5, "s"), ["fp2", "fp1", "fp0"])

    def test_engine_restart_keeps_avoiding_repeats(self):
        import random
        from tutor.engine import Engine
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.db")
            reg = repeat_registry()
            engine, store, clock = make_engine(registry=reg, path=path, flood=100000)
            verify(engine, CH)
            send(engine, CH, "Repeat Test")
            send(engine, CH, "Six items")
            refs = [store.get_pending(CH).problem.ref]
            for _ in range(2):
                send(engine, CH, "skip")
                refs.append(store.get_pending(CH).problem.ref)
            store.close()
            store2 = Store(path)
            self.addCleanup(store2.close)
            engine2 = Engine(store2, Config(owner_id=999, db_path=path), registry=reg, llm=None,
                             clock=helpers.FakeClock(helpers.START + 60), rng=random.Random(99))
            for _ in range(3):
                send(engine2, CH, "skip")
                refs.append(store2.get_pending(CH).problem.ref)
            self.assertEqual(len(set(refs)), 6, refs)


if __name__ == "__main__":
    unittest.main()
