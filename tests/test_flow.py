import random
import unittest

import helpers
from helpers import (S, snap, send, make_engine, get_codes, verify, to_topic, answer_of, keyboard_problem,
                     YEAR_KB, SUBJECT_KB_11, SUBJECT_KB_MATHS_ONLY, TOPIC_KB_MATHS_11, TOPIC_KB_KS3,
                     TOPIC_KB_PHYSICS, CHANGE_YEAR, CHANGE_SUBJECT, LEGACY_CHANGE, HIGHER_ALGEBRA,
                     CODE_REQUEST, CODE_BAD, CODE_OK, YEAR_ASK, OWN_TOPIC_ASK, OWN_TOPIC_NONE, ERROR,
                     SUBJECT_ASK, TOPIC_ASK, TOPIC_START, YEAR_NOT_READY, ASK_ANSWER_TAIL, TEXT_ONLY)

CH = 1


class FlowCase(unittest.TestCase):
    def setUp(self):
        self.engine, self.store, self.clock = make_engine(flood=100000)
        self.addCleanup(self.store.close)

    def say(self, chat, text, **kw):
        return snap(send(self.engine, chat, text, **kw))

    def student(self, chat=CH):
        return self.store.get_student(chat)

    def assert_problem_msg(self, out, chat, n=1, exam=False):
        """out: one Outgoing; checks it is 'Problem n: <pending text>' (or the exam form)."""
        p = self.store.get_pending(chat)
        self.assertIsNotNone(p)
        if exam:
            marks = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}[p.gen_level]
            self.assertEqual(out.text, helpers.PROBLEM_EXAM(n, marks, p.problem.text))
        else:
            self.assertEqual(out.text, f"Problem {n}: {p.problem.text}{ASK_ANSWER_TAIL}")
        self.assertEqual(p.problem_no, n)

    def reach(self, chat, step):
        verify(self.engine, chat)
        if step == "subject":
            pass
        elif step == "year":
            send(self.engine, chat, CHANGE_YEAR)
        else:
            send(self.engine, chat, "Maths")
            if step == "own_topic":
                send(self.engine, chat, "My own topic")
            elif step == "lesson":
                send(self.engine, chat, HIGHER_ALGEBRA)
        self.assertEqual(self.student(chat).step, step)


class TestCodeGate(FlowCase):
    def test_hello_gets_code_request(self):
        out = send(self.engine, CH, "hello")
        self.assertEqual(len(out), 1)
        self.assertEqual((out[0].chat_id, out[0].text, out[0].keyboard), (CH, CODE_REQUEST, None))

    def test_start_unverified_removes_keyboard(self):
        self.assertEqual(self.say(CH, "/start"), [S(CH, CODE_REQUEST, None, True)])
        self.assertEqual(self.say(CH, "/start@TutorBot"), [S(CH, CODE_REQUEST, None, True)])
        self.assertEqual(self.say(CH, "/start payload"), [S(CH, CODE_REQUEST, None, True)])
        st = self.student()
        self.assertFalse(st.verified)
        self.assertEqual(st.step, "code")
        self.assertEqual(st.year, 11)

    def test_wrong_code(self):
        self.assertEqual(self.say(CH, "ZZZZZZZZ"), [S(CH, CODE_BAD)])
        self.assertEqual(self.say(CH, "ABCDEF"), [S(CH, CODE_BAD)])          # 6 chars: shortest valid shape
        self.assertEqual(self.say(CH, "ABCDEFGHJKLM"), [S(CH, CODE_BAD)])    # 12 chars: longest valid shape
        self.assertFalse(self.student().verified)

    def test_not_code_shaped_repeats_request(self):
        for t in ("ABCDE", "ABCDEFGHJKLMN", "hello", "12", "Maths", "Year 7", CHANGE_YEAR, CHANGE_SUBJECT,
                  "/codes 5", "/students", "/foo", "with space but long enough?"):
            with self.subTest(text=t):
                self.assertEqual(self.say(CH, t), [S(CH, CODE_REQUEST)])

    def test_non_text_before_code(self):
        self.assertEqual(self.say(CH, None), [S(CH, CODE_REQUEST)])

    def test_lowercase_code_with_spaces_and_hyphens(self):
        code = get_codes(self.engine, 1)[0]
        typed = f"{code[:4].lower()} - {code[4:].lower()}"
        out = snap(send(self.engine, CH, typed))
        self.assertEqual(out, [S(CH, CODE_OK), S(CH, SUBJECT_ASK(11), SUBJECT_KB_11)])
        st = self.student()
        self.assertTrue(st.verified)
        self.assertEqual((st.step, st.year), ("subject", 11))

    def test_code_is_one_time(self):
        code = get_codes(self.engine, 1)[0]
        self.assertEqual(snap(send(self.engine, CH, code))[0], S(CH, CODE_OK))
        self.assertEqual(self.say(2, code), [S(2, CODE_BAD)])
        self.assertFalse(self.student(2).verified)
        self.assertEqual(self.say(2, code.lower()), [S(2, CODE_BAD)])

    def test_each_code_works_for_one_chat(self):
        codes = get_codes(self.engine, 3)
        self.assertEqual(len(set(codes)), 3)
        for i, c in enumerate(codes):
            self.assertEqual(self.say(10 + i, c)[0], S(10 + i, CODE_OK))
        self.assertEqual(self.store.count_unused_codes(), 0)

    def test_buttons_before_code_do_not_bypass(self):
        for i, t in enumerate(("Maths", "Year 7", CHANGE_YEAR, CHANGE_SUBJECT, LEGACY_CHANGE, "hint", "skip")):
            self.assertEqual(self.say(50 + i, t), [S(50 + i, CODE_REQUEST)], t)


class TestStartForVerified(FlowCase):
    def test_start_mid_lesson_resumes_without_code(self):
        to_topic(self.engine, CH)
        self.assertIsNotNone(self.store.get_pending(CH))
        self.assertEqual(self.say(CH, "/start"), [S(CH, SUBJECT_ASK(11), SUBJECT_KB_11)])
        st = self.student()
        self.assertTrue(st.verified)
        self.assertEqual(st.step, "subject")
        self.assertIsNone(self.store.get_pending(CH))
        self.assertEqual(self.say(CH, "Maths"), [S(CH, TOPIC_ASK(11), TOPIC_KB_MATHS_11)])

    def test_start_when_verified_at_each_step(self):
        for i, step in enumerate(("subject", "year", "topic", "own_topic", "lesson")):
            chat = 20 + i
            self.reach(chat, step)
            out = self.say(chat, "/start")
            self.assertEqual(out, [S(chat, SUBJECT_ASK(11), SUBJECT_KB_11)], step)
            self.assertTrue(self.student(chat).verified)
            self.assertEqual(self.student(chat).step, "subject")

    def test_start_keeps_year_and_level(self):
        to_topic(self.engine, CH, year=8, topic="KS3: algebra")
        send(self.engine, CH, "/start")
        self.assertEqual(self.student().year, 8)
        self.assertEqual(self.say(CH, "/start"), [S(CH, SUBJECT_ASK(8), SUBJECT_KB_MATHS_ONLY)])

    def test_start_uses_no_code(self):
        verify(self.engine, CH)
        before = self.store.count_unused_codes()
        send(self.engine, CH, "/start")
        self.assertEqual(self.store.count_unused_codes(), before)

    def test_reset_then_start_asks_for_code(self):
        to_topic(self.engine, CH)
        old = get_codes(self.engine, 1)
        send(self.engine, 999, f"/reset {CH}")
        self.assertEqual(self.say(CH, "/start"), [S(CH, CODE_REQUEST, None, True)])
        self.assertEqual(self.say(CH, "hello"), [S(CH, CODE_REQUEST)])
        out = self.say(CH, old[0])
        self.assertEqual(out[0], S(CH, CODE_OK))


class TestSubjectAndTopic(FlowCase):
    def setUp(self):
        super().setUp()
        verify(self.engine, CH)

    def test_maths_gives_exact_topic_keyboard(self):
        self.assertEqual(self.say(CH, "Maths"), [S(CH, TOPIC_ASK(11), TOPIC_KB_MATHS_11)])
        self.assertEqual(self.student().step, "topic")
        self.assertEqual(self.student().subject, "maths")

    def test_subject_case_insensitive(self):
        self.assertEqual(self.say(CH, "  maths "), [S(CH, TOPIC_ASK(11), TOPIC_KB_MATHS_11)])

    def test_physics_year_11(self):
        out = self.say(CH, "Physics")
        self.assertEqual(out, [S(CH, TOPIC_ASK(11), TOPIC_KB_PHYSICS)])
        self.assertEqual(self.student().subject, "physics")

    def test_unknown_subject_repeats_subject_ask(self):
        for t in ("English", "blah", "42", "🙂"):
            self.assertEqual(self.say(CH, t), [S(CH, SUBJECT_ASK(11), SUBJECT_KB_11)], t)
        self.assertEqual(self.student().step, "subject")

    def test_topic_start(self):
        send(self.engine, CH, "Maths")
        out = send(self.engine, CH, HIGHER_ALGEBRA)
        self.assertEqual(len(out), 2)
        self.assertEqual((out[0].text, out[0].keyboard), (TOPIC_START(HIGHER_ALGEBRA), None))
        self.assert_problem_msg(out[1], CH, 1)
        self.assertEqual(tuple(tuple(r) for r in out[1].keyboard), TOPIC_KB_MATHS_11)
        st = self.student()
        self.assertEqual((st.step, st.topic), ("lesson", "maths.y11.higher_algebra"))

    def test_topic_label_case_insensitive_uses_canonical_label(self):
        send(self.engine, CH, "Maths")
        out = send(self.engine, CH, "gcse foundation: NUMBER")
        self.assertEqual(out[0].text, TOPIC_START("GCSE Foundation: number"))

    def test_every_topic_button_starts_a_lesson(self):
        send(self.engine, CH, "Maths")
        for label in [lbl for r in helpers.MATHS_ROWS_10_11 for lbl in r] + ["Past paper practice"]:
            with self.subTest(label=label):
                out = send(self.engine, CH, label)
                self.assertEqual(out[0].text, TOPIC_START(label))
                self.assert_problem_msg(out[-1], CH, 1, exam=(label == "Past paper practice"))

    def test_topic_step_garbage_repeats_topic_ask(self):
        send(self.engine, CH, "Maths")
        for t in ("blah", "Energy", "42", "hint", "skip"):
            with self.subTest(text=t):
                self.assertEqual(self.say(CH, t), [S(CH, TOPIC_ASK(11), TOPIC_KB_MATHS_11)])
        self.assertEqual(self.student().step, "topic")

    def test_switch_topic_mid_lesson(self):
        to_topic(self.engine, CH)
        first = self.store.get_pending(CH)
        out = send(self.engine, CH, "GCSE Higher: trig & geometry")
        self.assertEqual(out[0].text, TOPIC_START("GCSE Higher: trig & geometry"))
        p = self.store.get_pending(CH)
        self.assertEqual((p.topic, p.problem_no), ("maths.y11.higher_trig", 1))
        self.assertTrue(p.skill.startswith("maths."))
        self.assertIn(p.skill, [
            "maths.pythagoras", "maths.trig_sides", "maths.trig_angles", "maths.sine_rule",
            "maths.triangle_area_sine", "maths.arcs_sectors"])
        self.assertNotEqual(first.topic, p.topic)


class TestYearAndSubjectSwitching(FlowCase):
    STEPS = ("year", "subject", "topic", "own_topic", "lesson")

    def test_change_year_from_every_step_both_buttons(self):
        n = 100
        for step in self.STEPS:
            for button in (CHANGE_YEAR, LEGACY_CHANGE):
                n += 1
                with self.subTest(step=step, button=button):
                    self.reach(n, step)
                    self.assertEqual(self.say(n, button), [S(n, YEAR_ASK, YEAR_KB)])
                    st = self.student(n)
                    self.assertEqual(st.step, "year")
                    self.assertTrue(st.verified)
                    self.assertIsNone(self.store.get_pending(n))

    def test_change_subject_from_every_step(self):
        n = 200
        for step in self.STEPS:
            n += 1
            with self.subTest(step=step):
                self.reach(n, step)
                self.assertEqual(self.say(n, CHANGE_SUBJECT), [S(n, SUBJECT_ASK(11), SUBJECT_KB_11)])
                self.assertEqual(self.student(n).step, "subject")
                self.assertIsNone(self.store.get_pending(n))
                self.assertEqual(self.say(n, "Physics"), [S(n, TOPIC_ASK(11), TOPIC_KB_PHYSICS)])

    def test_year_selection_updates_year(self):
        verify(self.engine, CH)
        send(self.engine, CH, CHANGE_YEAR)
        self.assertEqual(self.say(CH, "Year 7"), [S(CH, SUBJECT_ASK(7), SUBJECT_KB_MATHS_ONLY)])
        self.assertEqual(self.student().year, 7)
        self.assertEqual(self.student().step, "subject")
        self.assertEqual(self.say(CH, "Maths"), [S(CH, TOPIC_ASK(7), TOPIC_KB_KS3)])

    def test_year_variants_accepted(self):
        verify(self.engine, CH)
        for text, year in (("Year 9", 9), ("year 8", 8), ("Y9", 9), ("10", 10), ("Year 10", 10)):
            with self.subTest(text=text):
                send(self.engine, CH, CHANGE_YEAR)
                out = send(self.engine, CH, text)
                self.assertEqual(out[0].text, SUBJECT_ASK(year))
                self.assertEqual(self.student().year, year)

    def test_subjects_per_year(self):
        verify(self.engine, CH)
        for year, kb in ((7, SUBJECT_KB_MATHS_ONLY), (8, SUBJECT_KB_MATHS_ONLY), (9, SUBJECT_KB_MATHS_ONLY),
                         (10, SUBJECT_KB_11), (11, SUBJECT_KB_11)):
            send(self.engine, CH, CHANGE_YEAR)
            self.assertEqual(self.say(CH, f"Year {year}"), [S(CH, SUBJECT_ASK(year), kb)])

    def test_physics_hidden_in_year_8(self):
        verify(self.engine, CH)
        send(self.engine, CH, CHANGE_YEAR)
        send(self.engine, CH, "Year 8")
        self.assertEqual(self.say(CH, "Physics"), [S(CH, SUBJECT_ASK(8), SUBJECT_KB_MATHS_ONLY)])
        self.assertEqual(self.student().step, "subject")

    def test_year_not_ready_keeps_year(self):
        verify(self.engine, CH)
        send(self.engine, CH, CHANGE_YEAR)
        send(self.engine, CH, "Year 8")
        for label in ("Year 1–6", "Year 12", "Year 13"):
            with self.subTest(label=label):
                send(self.engine, CH, CHANGE_YEAR)
                self.assertEqual(self.say(CH, label), [S(CH, YEAR_NOT_READY(label), YEAR_KB)])
                self.assertEqual(self.student().year, 8)
                self.assertEqual(self.student().step, "year")

    def test_year_1_to_6_with_hyphen(self):
        verify(self.engine, CH)
        send(self.engine, CH, CHANGE_YEAR)
        out = self.say(CH, "Year 1-6")
        self.assertEqual(out[0][1], YEAR_NOT_READY("Year 1–6"))
        self.assertEqual(self.student().year, 11)

    def test_year_step_garbage_repeats_year_ask(self):
        verify(self.engine, CH)
        send(self.engine, CH, CHANGE_YEAR)
        for t in ("hello", "Year 14", "Year 0", "banana", "Maths"):
            with self.subTest(text=t):
                self.assertEqual(self.say(CH, t), [S(CH, YEAR_ASK, YEAR_KB)])
                self.assertEqual(self.student().step, "year")

    def test_year_not_ready_then_valid_year(self):
        verify(self.engine, CH)
        send(self.engine, CH, CHANGE_YEAR)
        send(self.engine, CH, "Year 12")
        self.assertEqual(self.say(CH, "Year 10"), [S(CH, SUBJECT_ASK(10), SUBJECT_KB_11)])


class TestOwnTopic(FlowCase):
    def setUp(self):
        super().setUp()
        verify(self.engine, CH)
        send(self.engine, CH, "Maths")

    def test_my_own_topic_prompt(self):
        self.assertEqual(self.say(CH, "My own topic"), [S(CH, OWN_TOPIC_ASK, TOPIC_KB_MATHS_11)])
        self.assertEqual(self.student().step, "own_topic")

    def test_my_own_topic_from_lesson(self):
        send(self.engine, CH, HIGHER_ALGEBRA)
        self.assertIsNotNone(self.store.get_pending(CH))
        self.assertEqual(self.say(CH, "my own topic"), [S(CH, OWN_TOPIC_ASK, TOPIC_KB_MATHS_11)])
        self.assertIsNone(self.store.get_pending(CH))

    def test_match_starts_topic_with_skill_title(self):
        send(self.engine, CH, "My own topic")
        out = send(self.engine, CH, "pythagoras")
        self.assertEqual(out[0].text, TOPIC_START("Pythagoras' theorem"))
        self.assert_problem_msg(out[1], CH, 1)
        p = self.store.get_pending(CH)
        self.assertEqual(p.skill, "maths.pythagoras")
        self.assertEqual(self.student().topic, "own:maths.pythagoras")
        self.assertEqual(self.student().step, "lesson")

    def test_match_in_a_sentence(self):
        send(self.engine, CH, "My own topic")
        out = send(self.engine, CH, "I need help with percentages please")
        self.assertEqual(out[0].text, TOPIC_START("Percentages"))

    def test_no_match_gives_own_topic_none_and_can_retry(self):
        send(self.engine, CH, "My own topic")
        self.assertEqual(self.say(CH, "photosynthesis"), [S(CH, OWN_TOPIC_NONE, TOPIC_KB_MATHS_11)])
        self.assertIsNone(self.store.get_pending(CH))
        out = send(self.engine, CH, "ratio")
        self.assertEqual(out[0].text, TOPIC_START("Ratio"))

    def test_topic_button_works_in_own_topic_step(self):
        send(self.engine, CH, "My own topic")
        out = send(self.engine, CH, "Past paper practice")
        self.assertEqual(out[0].text, TOPIC_START("Past paper practice"))

    def test_other_subject_alias_does_not_match(self):
        send(self.engine, CH, "My own topic")
        self.assertEqual(self.say(CH, "ohm's law"), [S(CH, OWN_TOPIC_NONE, TOPIC_KB_MATHS_11)])


class TestMisc(FlowCase):
    def test_non_text_when_verified(self):
        to_topic(self.engine, CH)
        self.assertEqual(self.say(CH, None), [S(CH, TEXT_ONLY, TOPIC_KB_MATHS_11)])
        verify(self.engine, 2)
        self.assertEqual(self.say(2, None), [S(2, TEXT_ONLY, SUBJECT_KB_11)])
        send(self.engine, 2, CHANGE_YEAR)
        self.assertEqual(self.say(2, None), [S(2, TEXT_ONLY, YEAR_KB)])

    def test_very_long_text_does_not_crash(self):
        to_topic(self.engine, CH)
        out = send(self.engine, CH, "9" * 5000)
        self.assertNotEqual(out[0].text, ERROR)
        self.assertIsNone(keyboard_problem(out, CH))

    def test_replies_go_to_the_right_chat(self):
        a = to_topic(self.engine, 1)
        b = to_topic(self.engine, 2)
        self.assertTrue(all(o.chat_id == 1 for o in a))
        self.assertTrue(all(o.chat_id == 2 for o in b))

    def test_two_students_are_independent(self):
        to_topic(self.engine, 1)
        to_topic(self.engine, 2, topic="GCSE Foundation: number")
        self.assertEqual(self.store.get_pending(1).topic, "maths.y11.higher_algebra")
        self.assertEqual(self.store.get_pending(2).topic, "maths.y11.foundation_number")


class TestKeyboardInvariant(FlowCase):
    POOL = ["Maths", "Physics", "Year 7", "Year 8", "Year 10", "Year 11", "Year 12", "Year 13", "Year 1–6",
            CHANGE_YEAR, CHANGE_SUBJECT, LEGACY_CHANGE, "My own topic", "Past paper practice", "hint", "skip",
            "42", "x=3", "pythagoras", "photosynthesis", "do my homework", "I want to die", "", " ", "😀",
            HIGHER_ALGEBRA, "KS3: algebra", "Forces & motion", "Energy", "/start", "?", "help me", "stuck",
            "I give up", "1/2", "£20 and £30", "GCSE Foundation: number", "Electricity", "Density & pressure",
            "KS3: geometry", "banana", "x = 2, x = -3", "3:4", "7" * 3000, None, "idk", "/delete_my_data_not"]

    def test_invariant_in_scripted_paths(self):
        verify(self.engine, CH)
        script = ["Maths", "My own topic", "nonsense", "pythagoras", "hint", "hint", "skip", "banana",
                  CHANGE_SUBJECT, "Physics", "Energy", "42", CHANGE_YEAR, "Year 12", "Year 8", "Physics", "Maths",
                  "Past paper practice", "do my homework", "I want to die", None, "/start", "Maths",
                  "KS3: algebra", LEGACY_CHANGE, "Year 10", "Maths", HIGHER_ALGEBRA]
        for t in script:
            out = send(self.engine, CH, t)
            self.assertNotIn(ERROR, [o.text for o in out], t)
            self.assertIsNone(keyboard_problem(out, CH), f"after {t!r}")

    def test_invariant_in_random_walk(self):
        rnd = random.Random(2024)
        verify(self.engine, CH)
        for i in range(400):
            t = rnd.choice(self.POOL)
            if t == "42" and rnd.random() < 0.5 and self.store.get_pending(CH) is not None:
                t = answer_of(self.store, CH)
            out = send(self.engine, CH, t)
            self.assertNotIn(ERROR, [o.text for o in out], f"step {i}: {t!r}")
            self.assertTrue(self.student().verified, f"step {i}: {t!r}")
            prob = keyboard_problem(out, CH)
            self.assertIsNone(prob, f"step {i} after {t!r}: {prob}")
            for o in out:
                self.assertIn(o.chat_id, (CH, 999))


if __name__ == "__main__":
    unittest.main()
