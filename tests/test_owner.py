import re
import unittest

import helpers
from helpers import (S, snap, send, make_engine, get_codes, verify, to_topic, answer_of, perturb, stamp, CODE_RE,
                     CODES_USAGE, STUDENT_USAGE, RESET_USAGE, NO_STUDENTS, NO_FLAGS, CODE_REQUEST, CODE_OK,
                     CODE_BAD, SUBJECT_ASK, SUBJECT_KB_11, FakeLLM)

OWNER = 999


class OwnerCase(unittest.TestCase):
    def setUp(self):
        self.engine, self.store, self.clock = make_engine(flood=100000)
        self.addCleanup(self.store.close)

    def own(self, text):
        return send(self.engine, OWNER, text)

    def own_text(self, text):
        out = self.own(text)
        self.assertEqual(len(out), 1, out)
        self.assertEqual(out[0].chat_id, OWNER)
        return out[0].text


class TestCodes(OwnerCase):
    def test_codes_3(self):
        text = self.own_text("/codes 3")
        lines = text.split("\n")
        self.assertEqual(lines[0], "🔑 3 new codes:")
        self.assertEqual(len(lines), 4)
        for c in lines[1:]:
            self.assertRegex(c, CODE_RE)
        self.assertEqual(len(set(lines[1:])), 3)
        self.assertEqual(self.store.count_unused_codes(), 3)

    def test_codes_singular(self):
        text = self.own_text("/codes 1")
        self.assertTrue(text.startswith("🔑 1 new code:\n"))
        self.assertNotIn("codes:", text)
        self.assertEqual(len(text.split("\n")), 2)

    def test_codes_boundaries(self):
        self.assertEqual(len(get_codes(self.engine, 50)), 50)
        self.assertEqual(self.store.count_unused_codes(), 50)

    def test_codes_alphabet(self):
        codes = get_codes(self.engine, 50)
        self.assertEqual(len(set(codes)), 50)
        for c in codes:
            self.assertEqual(len(c), 8)
            self.assertLessEqual(set(c), set("ABCDEFGHJKMNPQRSTUVWXYZ23456789"))   # literal alphabet of section 0.5
            self.assertFalse(set(c) & set("01OIL"))

    def test_codes_usage(self):
        for t in ("/codes 0", "/codes 51", "/codes abc", "/codes -1", "/codes 1.5", "/codes 1000"):
            with self.subTest(text=t):
                self.assertEqual(self.own_text(t), CODES_USAGE)
        self.assertEqual(self.store.count_unused_codes(), 0)

    def test_codes_with_bot_suffix(self):
        text = self.own_text("/codes@TutorBot 2")
        self.assertTrue(text.startswith("🔑 2 new codes:\n"))
        self.assertEqual(self.store.count_unused_codes(), 2)

    def test_generated_codes_are_redeemable(self):
        codes = get_codes(self.engine, 2)
        for i, c in enumerate(codes):
            self.assertEqual(send(self.engine, 10 + i, c)[0].text, CODE_OK)

    def test_non_owner_cannot_get_codes(self):
        out = snap(send(self.engine, 5, "/codes 3"))
        self.assertEqual(out, [S(5, CODE_REQUEST)])
        self.assertEqual(self.store.count_unused_codes(), 0)
        verify(self.engine, 6)
        before = self.store.count_unused_codes()
        out = send(self.engine, 6, "/codes 3")
        self.assertNotIn("🔑", out[0].text)
        self.assertEqual(self.store.count_unused_codes(), before)

    def test_non_owner_cannot_use_other_owner_commands(self):
        for t in ("/students", "/student 5", "/reset 5", "/flags", "/stats"):
            with self.subTest(text=t):
                out = send(self.engine, 5, t)
                self.assertEqual(snap(out), [S(5, CODE_REQUEST)])

    def test_no_owner_configured(self):
        engine, store, clock = make_engine(owner_id=None, flood=100000)
        self.addCleanup(store.close)
        out = send(engine, OWNER, "/codes 3")
        self.assertEqual(snap(out), [S(OWNER, CODE_REQUEST)])
        self.assertEqual(store.count_unused_codes(), 0)

    def test_unknown_slash_command_from_owner_is_normal_flow(self):
        self.assertEqual(snap(self.own("/foo")), [S(OWNER, CODE_REQUEST)])

    def test_owner_exempt_from_flood(self):
        for i in range(60):
            self.assertEqual(len(self.own("/stats")), 1, i)


class TestStudents(OwnerCase):
    def test_none(self):
        self.assertEqual(self.own_text("/students"), NO_STUDENTS)

    def test_listing(self):
        verify(self.engine, 1)
        send(self.engine, 1, "Maths")
        self.clock.advance(120)
        send(self.engine, 2, "hello", first_name="Alice", username="al")
        text = self.own_text("/students")
        lines = text.split("\n")
        self.assertEqual(lines[0], "👥 Students (2):")
        self.assertEqual(len(lines), 3)
        d2 = stamp(self.clock())
        d1 = stamp(self.clock() - 120)
        self.assertEqual(lines[1], f"2 · Alice @al · ⛔ not verified · Year 11 · — · last seen {d2}")
        m = re.fullmatch(r"1 · Zorblax · ✅ verified · Year 11 · (.+) · last seen " + re.escape(d1), lines[2])
        self.assertIsNotNone(m, lines[2])
        self.assertIn(m.group(1), ("maths", "Maths"))

    def test_order_is_last_seen_desc(self):
        for chat in (1, 2, 3):
            send(self.engine, chat, "hello")
            self.clock.advance(60)
        send(self.engine, 1, "hello")
        lines = self.own_text("/students").split("\n")[1:]
        self.assertEqual([l.split(" · ")[0] for l in lines], ["1", "3", "2"])


class TestStudentDetail(OwnerCase):
    def test_usage_and_not_found(self):
        self.assertEqual(self.own_text("/student"), STUDENT_USAGE)
        self.assertEqual(self.own_text("/student abc"), STUDENT_USAGE)
        self.assertEqual(self.own_text("/student 12345"), "Student 12345 not found.")

    def test_detail(self):
        to_topic(self.engine, 5)
        send(self.engine, 5, answer_of(self.store, 5))
        send(self.engine, 5, perturb(self.store.get_pending(5).problem.answer))
        send(self.engine, 5, "skip")
        text = self.own_text("/student 5")
        self.assertTrue(text.startswith("👤 Zorblax (chat 5)\nStatus: "), text)
        self.assertIn("\nYear 11 · Subject: ", text)
        self.assertIn(" · Topic: ", text)
        self.assertIn("\nLevels: ", text)
        self.assertRegex(text, r"\nAttempts: \d+ \(1 correct\)\nRecent:\n")
        recent = text.split("Recent:\n", 1)[1].split("\n")
        self.assertEqual(len(recent), 3)
        d = stamp(self.clock())
        pats = [r"✅", r"❌", r"⏭"]
        for line, mark in zip(reversed(recent), pats):          # recent is newest first
            self.assertRegex(line, r"^" + re.escape(d) + r" maths\.\w+ L\d " + mark + r"$")

    def test_detail_with_username(self):
        send(self.engine, 5, "hello", first_name="Alice", username="al")
        self.assertTrue(self.own_text("/student 5").startswith("👤 Alice @al (chat 5)\n"))

    def test_detail_for_student_without_attempts(self):
        send(self.engine, 5, "hello")
        text = self.own_text("/student 5")
        self.assertIn("Attempts: 0 (0 correct)", text)


class TestReset(OwnerCase):
    def test_reset_requires_new_code(self):
        to_topic(self.engine, 5)
        old_code = get_codes(self.engine, 1)[0]
        self.assertEqual(self.own_text("/reset 5"), "✅ Student 5 has been reset — they need a new code.")
        self.assertFalse(self.store.get_student(5).verified)
        self.assertEqual(snap(send(self.engine, 5, "hello")), [S(5, CODE_REQUEST)])
        self.assertEqual(snap(send(self.engine, 5, "ZZZZZZZZ")), [S(5, CODE_BAD)])
        out = send(self.engine, 5, old_code)          # a fresh, unused code works
        self.assertEqual(out[0].text, CODE_OK)
        self.assertTrue(self.store.get_student(5).verified)

    def test_old_used_code_fails_after_reset(self):
        code = get_codes(self.engine, 1)[0]
        send(self.engine, 5, code)
        self.own("/reset 5")
        self.assertEqual(snap(send(self.engine, 5, code)), [S(5, CODE_BAD)])

    def test_reset_usage_and_not_found(self):
        self.assertEqual(self.own_text("/reset"), RESET_USAGE)
        self.assertEqual(self.own_text("/reset abc"), RESET_USAGE)
        self.assertEqual(self.own_text("/reset 4242"), "Student 4242 not found.")

    def test_reset_clears_lesson_access(self):
        to_topic(self.engine, 5)
        self.own("/reset 5")
        out = send(self.engine, 5, "3")
        self.assertEqual(out[0].text, CODE_REQUEST)


class TestFlags(OwnerCase):
    def test_none(self):
        self.assertEqual(self.own_text("/flags"), NO_FLAGS)

    def test_listing_does_not_mark_reviewed(self):
        send(self.engine, 5, "I want to die")
        text = self.own_text("/flags")
        d = stamp(self.clock())
        self.assertEqual(text, f"🚩 1 new flag:\n#1 {d} distress · chat 5 (Zorblax): I want to die\n"
                               f"When you have dealt with them, send /flags done 1")
        self.assertEqual(self.own_text("/flags"), text)               # still there: delivery may have failed
        self.assertEqual(len(self.store.unreviewed_flags()), 1)

    def test_flags_done_marks_reviewed(self):
        send(self.engine, 5, "I want to die")
        self.assertEqual(self.own_text("/flags done"), helpers.FLAGS_DONE(1))
        self.assertEqual(self.own_text("/flags"), NO_FLAGS)
        self.assertEqual(self.store.unreviewed_flags(), [])
        self.assertEqual(self.own_text("/flags done"), NO_FLAGS)

    def test_flags_done_up_to_id_keeps_newer_flags(self):
        send(self.engine, 5, "I want to die")
        send(self.engine, 6, "i cut myself", first_name="Bob", username="bb")
        listing = self.own_text("/flags")
        self.assertTrue(listing.endswith("send /flags done 2"), listing)
        send(self.engine, 7, "my dad hits me")              # arrives after the owner read the list
        self.assertEqual(self.own_text("/flags done 2"), helpers.FLAGS_DONE(2))
        self.assertEqual([f.chat_id for f in self.store.unreviewed_flags()], [7])
        self.assertEqual(self.own_text("/flags ok #3"), helpers.FLAGS_DONE(1))

    def test_flags_usage(self):
        for t in ("/flags all", "/flags done x", "/flags done 1 2"):
            with self.subTest(text=t):
                self.assertEqual(self.own_text(t), helpers.FLAGS_USAGE)

    def test_multiple_flags_plural_and_order(self):
        send(self.engine, 5, "I want to die")
        send(self.engine, 6, "i cut myself", first_name="Bob", username="bb")
        lines = self.own_text("/flags").split("\n")
        self.assertEqual(lines[0], "🚩 2 new flags:")
        self.assertTrue(lines[1].startswith("#1 "))
        self.assertTrue(lines[2].startswith("#2 "))
        self.assertTrue(lines[2].endswith("distress · chat 6 (Bob @bb): i cut myself"), lines[2])
        self.own("/flags done")
        self.assertEqual(self.own_text("/flags"), NO_FLAGS)

    def test_new_flag_after_review_is_listed(self):
        send(self.engine, 5, "I want to die")
        self.own("/flags done")
        send(self.engine, 5, "thinking about suicide")
        text = self.own_text("/flags")
        self.assertTrue(text.startswith("🚩 1 new flag:\n#2 "), text)


class TestStats(OwnerCase):
    def test_fresh(self):
        text = self.own_text("/stats")
        self.assertTrue(text.startswith("📊 Stats\n"))
        self.assertIn("Students: 0", text)

    def test_exact_stats(self):
        c1, c2 = get_codes(self.engine, 2)
        send(self.engine, 1, c1)
        send(self.engine, 1, "Maths")
        send(self.engine, 1, helpers.HIGHER_ALGEBRA)
        send(self.engine, 1, answer_of(self.store, 1))
        send(self.engine, 1, perturb(self.store.get_pending(1).problem.answer))
        send(self.engine, 2, "hello")
        expected = ("📊 Stats\nStudents: 2 (1 verified, 2 active in 7 days)\n"
                    "Attempts: 2 today, 2 in 7 days (50% correct)\nUnused codes: 1\n"
                    "LLM calls today: 0\nUnreviewed flags: 0")
        self.assertEqual(self.own_text("/stats"), expected)

    def test_week_window(self):
        send(self.engine, 1, "hello")
        self.clock.advance(8 * 86400)
        text = self.own_text("/stats")
        self.assertIn("Students: 1 (0 verified, 0 active in 7 days)", text)

    def test_counts_flags_and_llm(self):
        llm = FakeLLM(["why"])
        engine, store, clock = make_engine(llm=llm, flood=100000)
        self.addCleanup(store.close)
        send(engine, 5, "I want to die")
        text = send(engine, OWNER, "/stats")[0].text
        self.assertIn("Unreviewed flags: 1", text)
        self.assertIn("LLM calls today: 0", text)


class TestHandleOwnerDirect(OwnerCase):
    def test_returns_list_of_strings(self):
        from tutor.owner import handle_owner, OWNER_COMMANDS
        self.assertEqual(tuple(OWNER_COMMANDS), ("/codes", "/students", "/student", "/reset", "/flags", "/stats"))
        out = handle_owner("/codes", ["2"], store=self.store, now=self.clock(), registry=helpers.shared_registry())
        self.assertIsInstance(out, list)
        self.assertTrue(all(isinstance(x, str) for x in out))
        self.assertTrue(out[0].startswith("🔑 2 new codes:\n"))
        out = handle_owner("/students", [], store=self.store, now=self.clock(), registry=helpers.shared_registry())
        self.assertEqual(out, [NO_STUDENTS])
        out = handle_owner("/codes", ["x"], store=self.store, now=self.clock(), registry=helpers.shared_registry())
        self.assertEqual(out, [CODES_USAGE])


if __name__ == "__main__":
    unittest.main()
