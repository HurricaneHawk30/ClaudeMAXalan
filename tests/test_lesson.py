import re
import unittest
from fractions import Fraction

import helpers
from helpers import (S, snap, send, make_engine, verify, to_topic, to_demo_topic, answer_of, perturb, demo_registry,
                     DEMO_FLAGS, DEMO_TOPIC_KB, TOPIC_KB_MATHS_11, TOPIC_KB_KS3, HIGHER_ALGEBRA, FOUNDATION_NUMBER,
                     CORRECT, WRONG, WHY_FALLBACK, HINT, HINT_AGAIN, SKIP, UNPARSED, OFFTOPIC, UNMARKABLE, ERROR,
                     FORM_SIMPLEST, FORM_STANDARD, PROBLEM, PROBLEM_EXAM, TOPIC_START, TOPIC_ASK, FakeLLM,
                     CHANGE_YEAR)

CH = 1


class LessonCase(unittest.TestCase):
    def setUp(self):
        self.engine, self.store, self.clock = make_engine(flood=100000)
        self.addCleanup(self.store.close)

    def say(self, text, chat=CH):
        return send(self.engine, chat, text)

    def pending(self, chat=CH):
        return self.store.get_pending(chat)

    def level(self, chat=CH):
        st = self.store.get_student(chat)
        return self.store.get_level(chat, st.subject, st.topic)

    def solve(self, chat=CH):
        return self.say(answer_of(self.store, chat), chat)

    def start(self, topic=HIGHER_ALGEBRA, **kw):
        return to_topic(self.engine, CH, topic=topic, **kw)


class TestCorrect(LessonCase):
    def test_correct_answer_levels_up_and_advances(self):
        self.start()
        p1 = self.pending()
        self.assertEqual((p1.level, p1.problem_no, p1.hints_given), (1, 1, 0))
        out = self.solve()
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].text, CORRECT(p1.problem.solution))
        self.assertIsNone(out[0].keyboard)
        p2 = self.pending()
        self.assertEqual(out[1].text, PROBLEM(2, p2.problem.text))
        self.assertEqual(tuple(tuple(r) for r in out[1].keyboard), TOPIC_KB_MATHS_11)
        self.assertEqual((p2.level, p2.problem_no, p2.hints_given), (2, 2, 0))
        self.assertEqual(self.level(), 2)

    def test_correct_picks_another_skill_when_topic_has_several(self):
        self.start()
        for _ in range(6):
            before = self.pending().skill
            self.solve()
            self.assertNotEqual(self.pending().skill, before)

    def test_level_caps_at_five(self):
        self.start()
        for i in range(9):
            self.solve()
            self.assertEqual(self.level(), min(5, 2 + i))
            self.assertLessEqual(self.pending().level, 5)
        self.assertEqual(self.pending().level, 5)
        self.assertEqual(self.pending().problem_no, 10)

    def test_level_map_applied(self):
        self.start(topic=FOUNDATION_NUMBER)
        expected_gen = (1, 2, 3, 3, 4)
        for lvl in range(1, 6):
            p = self.pending()
            self.assertEqual((p.level, p.gen_level), (lvl, expected_gen[lvl - 1]))
            self.assertEqual(p.problem.level, p.gen_level)
            self.solve()

    def test_level_map_identity_for_higher(self):
        self.start()
        for lvl in range(1, 6):
            p = self.pending()
            self.assertEqual((p.level, p.gen_level), (lvl, lvl))
            self.solve()

    def test_ks3_level_map_year7(self):
        self.start(topic="KS3: algebra", year=7)
        gens = []
        for _ in range(5):
            gens.append(self.pending().gen_level)
            self.solve()
        self.assertEqual(gens, [1, 1, 2, 2, 3])

    def test_attempt_recorded_for_correct(self):
        self.start()
        p = self.pending()
        self.solve()
        att = self.store.recent_attempts(CH)
        self.assertEqual(len(att), 1)
        a = att[0]
        self.assertTrue(a.correct)
        self.assertFalse(a.skipped)
        self.assertEqual((a.skill, a.level, a.gen_level, a.chat_id), (p.skill, 1, p.gen_level, CH))
        self.assertEqual(a.subject, "maths")
        self.assertEqual(a.topic, "maths.y11.higher_algebra")
        self.assertEqual(a.ts, self.clock())

    def test_answer_with_working_and_prefix_is_accepted(self):
        self.start()
        ans = answer_of(self.store, CH)
        out = self.say(f"I worked it out\nso the answer is\nAnswer: {ans}")
        self.assertTrue(out[0].text.startswith("✅ Correct!"), out[0].text)


class TestWrong(LessonCase):
    def wrong_texts(self, p, answer_text):
        opts = {WRONG(WHY_FALLBACK(p.problem.solution), p.problem.answer.display)}
        for m in p.problem.mistakes:
            opts.add(WRONG(m.feedback, p.problem.answer.display))
        return opts

    def test_wrong_levels_down_same_skill_and_format(self):
        self.start()
        self.solve()                     # level 2
        self.assertEqual(self.level(), 2)
        p = self.pending()
        bad = perturb(p.problem.answer)
        out = self.say(bad)
        self.assertEqual(len(out), 2)
        self.assertIn(out[0].text, self.wrong_texts(p, bad))
        self.assertTrue(out[0].text.startswith("❌ Not quite. "))
        self.assertTrue(out[0].text.endswith(f". Correct answer: {p.problem.answer.display}"))
        self.assertEqual(self.level(), 1)
        q = self.pending()
        self.assertEqual(q.skill, p.skill)
        self.assertEqual((q.problem_no, q.level), (p.problem_no + 1, 1))
        self.assertEqual(out[1].text, PROBLEM(q.problem_no, q.problem.text))
        self.assertEqual(tuple(tuple(r) for r in out[1].keyboard), TOPIC_KB_MATHS_11)

    def test_wrong_at_level_1_stays_at_1(self):
        self.start()
        self.say(perturb(self.pending().problem.answer))
        self.assertEqual(self.level(), 1)
        self.assertEqual(self.pending().level, 1)

    def test_wrong_attempt_recorded(self):
        self.start()
        p = self.pending()
        self.say(perturb(p.problem.answer))
        a = self.store.recent_attempts(CH)[0]
        self.assertFalse(a.correct)
        self.assertFalse(a.skipped)
        self.assertEqual(a.skill, p.skill)

    def test_mistake_feedback_used_when_matched(self):
        # find a problem with a mistake via the loop; the matching feedback must reach the student
        self.start()
        for _ in range(60):
            p = self.pending()
            if p.problem.mistakes:
                m = p.problem.mistakes[0]
                out = self.say(m.answer.display)
                self.assertEqual(out[0].text, WRONG(m.feedback, p.problem.answer.display))
                return
            self.solve()
        self.skipTest("no problem with mistakes met")

    def test_wrong_never_exposes_nothing_else_changes_topic(self):
        self.start()
        self.say(perturb(self.pending().problem.answer))
        self.assertEqual(self.store.get_student(CH).step, "lesson")
        self.assertEqual(self.store.get_student(CH).topic, "maths.y11.higher_algebra")


class TestFormFeedbackInWrong(unittest.TestCase):
    def setUp(self):
        self.engine, self.store, self.clock = make_engine(registry=demo_registry(), flood=100000)
        self.addCleanup(self.store.close)

    def test_simplest_form(self):
        to_demo_topic(self.engine, CH, "Fractions only")
        p = self.store.get_pending(CH)
        fr = Fraction(p.problem.answer.value)
        unsimplified = f"{2 * fr.numerator}/{2 * fr.denominator}"
        out = send(self.engine, CH, unsimplified)
        self.assertEqual(out[0].text, WRONG(FORM_SIMPLEST, p.problem.answer.display))
        self.assertEqual(out[0].text, f"❌ Not quite. {FORM_SIMPLEST}. Correct answer: {p.problem.answer.display}")
        self.assertEqual(self.store.get_pending(CH).skill, "demo.frac")
        self.assertFalse(self.store.recent_attempts(CH)[0].correct)

    def test_standard_form(self):
        to_demo_topic(self.engine, CH, "Standard only")
        p = self.store.get_pending(CH)
        plain = str(int(p.problem.answer.value))
        out = send(self.engine, CH, plain)
        self.assertEqual(out[0].text, WRONG(FORM_STANDARD, p.problem.answer.display))
        self.assertIn("standard form (a × 10^n, with 1 ≤ a < 10)", out[0].text)

    def test_correct_form_is_accepted(self):
        to_demo_topic(self.engine, CH, "Standard only")
        out = send(self.engine, CH, answer_of(self.store, CH))
        self.assertTrue(out[0].text.startswith("✅ Correct! "))


class TestHint(LessonCase):
    def test_first_hint_then_again(self):
        self.start()
        p = self.pending()
        out = self.say("hint")
        self.assertEqual(snap(out), [S(CH, HINT(p.problem.hint), TOPIC_KB_MATHS_11)])
        self.assertEqual(self.pending().hints_given, 1)
        out = self.say("hint")
        self.assertEqual(snap(out), [S(CH, HINT_AGAIN(p.problem.hint), TOPIC_KB_MATHS_11)])
        self.assertEqual(self.pending().hints_given, 2)
        out = self.say("I'm stuck")
        self.assertEqual(out[0].text, HINT_AGAIN(p.problem.hint))
        self.assertEqual(self.pending().hints_given, 3)

    def test_hint_keeps_the_problem(self):
        self.start()
        p = self.pending()
        self.say("hint")
        q = self.pending()
        self.assertEqual((q.problem_no, q.seed, q.skill, q.level), (p.problem_no, p.seed, p.skill, p.level))
        self.assertEqual(self.store.recent_attempts(CH), [])
        self.assertEqual(self.level(), 1)

    def test_hint_phrases(self):
        phrases = ("hint", "Hint", "give me a hint", "help", "Help me", "stuck", "how do i start", "?",
                   "i don't get it", "what do i do", "explain")
        for i, phrase in enumerate(phrases):
            with self.subTest(phrase=phrase):
                chat = 300 + i
                to_topic(self.engine, chat)
                self.assertTrue(self.say(phrase, chat)[0].text.startswith("💡 Hint: "), phrase)

    def test_hint_hints_given_resets_for_new_problem(self):
        self.start()
        self.say("hint")
        self.solve()
        self.assertEqual(self.pending().hints_given, 0)
        self.assertTrue(self.say("hint")[0].text == HINT(self.pending().problem.hint))


class TestSkip(LessonCase):
    def test_skip_records_skipped_attempt_and_moves_on(self):
        self.start()
        self.solve()                 # level 2
        p = self.pending()
        out = self.say("skip")
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0].text, SKIP(p.problem.solution, p.problem.answer.display))
        q = self.pending()
        self.assertEqual(out[1].text, PROBLEM(p.problem_no + 1, q.problem.text))
        self.assertEqual(q.skill, p.skill)
        self.assertEqual(q.level, 1)
        self.assertEqual(self.level(), 1)
        a = self.store.recent_attempts(CH)[0]
        self.assertTrue(a.skipped)
        self.assertFalse(a.correct)
        self.assertEqual(a.skill, p.skill)

    def test_skip_phrases(self):
        phrases = ("skip", "Skip", "next", "pass", "I don't know", "idk", "dunno", "no idea", "give up",
                   "I give up", "show answer", "show me the answer")
        for i, phrase in enumerate(phrases):
            with self.subTest(phrase=phrase):
                chat = 400 + i
                to_topic(self.engine, chat)
                out = self.say(phrase, chat)
                self.assertTrue(out[0].text.startswith("👀 No problem — here's how to do it: "), phrase)
                self.assertEqual(len(self.store.recent_attempts(chat, 100)), 1)
                self.assertTrue(self.store.recent_attempts(chat)[0].skipped)

    def test_skip_at_level_1_stays_1(self):
        self.start()
        self.say("skip")
        self.assertEqual(self.level(), 1)

    def test_attempt_order_newest_first(self):
        self.start()
        self.solve()
        self.say(perturb(self.pending().problem.answer))
        self.say("skip")
        att = self.store.recent_attempts(CH)
        self.assertEqual([(a.correct, a.skipped) for a in att], [(False, True), (False, False), (True, False)])
        self.assertEqual(len(self.store.recent_attempts(CH, 2)), 2)


class TestUnparsedVsOfftopic(LessonCase):
    def test_offtopic_for_plain_words(self):
        self.start()
        p = self.pending()
        out = self.say("what is for lunch today")
        self.assertEqual(snap(out), [S(CH, OFFTOPIC("Maths", p.problem_no), TOPIC_KB_MATHS_11)])

    def test_unparsed_when_symbols_or_digits(self):
        self.start()
        for t in ("a + b", "a * b", "√ something"):
            with self.subTest(text=t):
                self.assertEqual(snap(self.say(t)), [S(CH, UNPARSED, TOPIC_KB_MATHS_11)])

    def test_unparsed_does_not_change_state(self):
        self.start()
        p = self.pending()
        self.say("what is for lunch today")
        self.say("a + b")
        q = self.pending()
        self.assertEqual((q.problem_no, q.seed, q.skill, q.level, q.hints_given),
                         (p.problem_no, p.seed, p.skill, p.level, p.hints_given))
        self.assertEqual(self.store.recent_attempts(CH), [])
        self.assertEqual(self.level(), 1)

    def test_offtopic_uses_current_problem_number(self):
        self.start()
        self.solve()
        self.solve()
        self.assertEqual(self.say("hello there")[0].text, OFFTOPIC("Maths", 3))

    def test_offtopic_names_the_subject(self):
        to_topic(self.engine, 2, subject="Physics", topic="Energy")
        self.assertEqual(self.say("what is for lunch today", 2)[0].text, OFFTOPIC("Physics", 1))


class TestPastPaper(LessonCase):
    def test_marks_follow_the_levels(self):
        self.start(topic="Past paper practice")
        seen = []
        for _ in range(6):
            p = self.pending()
            marks = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}[p.gen_level]
            seen.append((p.level, p.gen_level, marks))
            self.assertEqual(p.gen_level, (2, 3, 3, 4, 5)[p.level - 1])
            reply = self.solve()
            self.assertEqual(reply[-1].text, PROBLEM_EXAM(p.problem_no + 1, {1: 1, 2: 2, 3: 2, 4: 3, 5: 4}[self.pending().gen_level],
                                                          self.pending().problem.text))
        self.assertEqual([m for _, _, m in seen], [2, 2, 2, 3, 4, 4])

    def test_first_message_is_exam_style(self):
        out = self.start(topic="Past paper practice")
        p = self.pending()
        self.assertEqual(out[0].text, TOPIC_START("Past paper practice"))
        self.assertEqual(out[1].text, PROBLEM_EXAM(1, 2, p.problem.text))
        self.assertTrue(re.match(r"^Problem 1 \(2 marks\): ", out[1].text))
        self.assertEqual(p.topic, "maths.y11.past_paper")

    def test_singular_mark(self):
        out = self.start(topic="Past paper practice", year=7)     # KS3 past map starts at generator level 1
        p = self.pending()
        self.assertEqual(p.gen_level, 1)
        self.assertEqual(out[1].text, PROBLEM_EXAM(1, 1, p.problem.text))
        self.assertTrue(out[1].text.startswith("Problem 1 (1 mark): "))

    def test_regular_topic_is_not_exam_style(self):
        out = self.start()
        self.assertTrue(out[1].text.startswith("Problem 1: "))
        self.assertNotIn(" mark", out[1].text.split(":")[0])


class TestReentry(LessonCase):
    def test_reentering_topic_starts_one_level_lower(self):
        self.start()
        for _ in range(3):
            self.solve()
        self.assertEqual(self.level(), 4)
        out = self.say(HIGHER_ALGEBRA)
        self.assertEqual(out[0].text, TOPIC_START(HIGHER_ALGEBRA))
        self.assertEqual(self.level(), 3)
        p = self.pending()
        self.assertEqual((p.level, p.problem_no), (3, 1))

    def test_reentering_at_level_1_stays_1(self):
        self.start()
        self.say(HIGHER_ALGEBRA)
        self.assertEqual(self.level(), 1)
        self.assertEqual(self.pending().level, 1)

    def test_reentering_at_level_5_gives_4(self):
        self.start()
        for _ in range(5):
            self.solve()
        self.assertEqual(self.level(), 5)
        self.say(HIGHER_ALGEBRA)
        self.assertEqual(self.level(), 4)

    def test_level_survives_switching_topics(self):
        self.start()
        self.solve()
        self.solve()
        self.assertEqual(self.level(), 3)
        self.say("GCSE Higher: trig & geometry")
        self.say(HIGHER_ALGEBRA)
        self.assertEqual(self.level(), 2)

    def test_reentering_via_own_topic(self):
        verify(self.engine, 7)
        send(self.engine, 7, "Maths")
        send(self.engine, 7, "My own topic")
        send(self.engine, 7, "ratio")
        for _ in range(3):
            self.solve(7)
        self.assertEqual(self.store.get_level(7, "maths", "own:maths.ratio"), 4)
        send(self.engine, 7, "My own topic")
        send(self.engine, 7, "ratio")
        self.assertEqual(self.store.get_level(7, "maths", "own:maths.ratio"), 3)


class TestRubricAndErrors(unittest.TestCase):
    def setUp(self):
        DEMO_FLAGS["boom"] = False
        self.addCleanup(DEMO_FLAGS.update, {"boom": False})
        self.engine, self.store, self.clock = make_engine(registry=demo_registry(), flood=100000)
        self.addCleanup(self.store.close)

    def test_rubric_without_llm_is_unmarkable(self):
        to_demo_topic(self.engine, CH, "Written")
        p = self.store.get_pending(CH)
        out = send(self.engine, CH, "Plants need light to make food")
        self.assertEqual(out[0].text, UNMARKABLE(p.problem.answer.display))
        self.assertEqual(len(out), 2)
        q = self.store.get_pending(CH)
        self.assertEqual((q.skill, q.level, q.problem_no), ("demo.essay", p.level, p.problem_no + 1))
        self.assertEqual(self.store.recent_attempts(CH), [])
        self.assertEqual(self.store.get_level(CH, "demo", "demo.y11.written"), 1)
        self.assertEqual(tuple(tuple(r) for r in out[1].keyboard), DEMO_TOPIC_KB)

    def test_demo_subject_keyboards(self):
        verify(self.engine, CH)
        out = send(self.engine, CH, "/start")
        self.assertEqual(snap(out), [S(CH, helpers.SUBJECT_ASK(11), helpers.DEMO_SUBJECT_KB)])

    def test_generator_error_gives_error_and_rolls_back(self):
        verify(self.engine, CH)
        send(self.engine, CH, "Demo")
        DEMO_FLAGS["boom"] = True
        with self.assertLogs(level="ERROR"):
            out = send(self.engine, CH, "Fragile")
        self.assertEqual(snap(out), [S(CH, ERROR)])
        st = self.store.get_student(CH)
        self.assertEqual(st.step, "topic")
        self.assertTrue(st.verified)
        self.assertIsNone(self.store.get_pending(CH))
        DEMO_FLAGS["boom"] = False
        out = send(self.engine, CH, "Arithmetic")
        self.assertEqual(out[0].text, TOPIC_START("Arithmetic"))
        self.assertEqual(self.store.get_student(CH).step, "lesson")

    def test_error_mid_lesson_rolls_back_attempt_level_and_pending(self):
        to_demo_topic(self.engine, CH, "Fragile")
        p = self.store.get_pending(CH)
        DEMO_FLAGS["boom"] = True
        with self.assertLogs(level="ERROR"):
            out = send(self.engine, CH, p.problem.answer.display)
        self.assertEqual(snap(out), [S(CH, ERROR)])
        self.assertEqual(self.store.recent_attempts(CH), [])
        self.assertEqual(self.store.get_level(CH, "demo", "demo.y11.fragile"), 1)
        q = self.store.get_pending(CH)
        self.assertEqual((q.problem_no, q.seed, q.hints_given), (p.problem_no, p.seed, p.hints_given))
        DEMO_FLAGS["boom"] = False
        out = send(self.engine, CH, p.problem.answer.display)
        self.assertEqual(out[0].text, CORRECT(p.problem.solution))
        self.assertEqual(self.store.get_pending(CH).problem_no, 2)

    def test_demo_wrong_uses_mistake_feedback(self):
        to_demo_topic(self.engine, CH, "Adding")
        p = self.store.get_pending(CH)
        n = int(p.problem.answer.value)
        out = send(self.engine, CH, str(n + 1))
        self.assertEqual(out[0].text, WRONG("You were out by one", str(n)))
        out = send(self.engine, CH, str(self.store.get_pending(CH).problem.answer.value + 7))
        self.assertIn("Here's the method: ", out[0].text)

    def test_demo_correct_text(self):
        to_demo_topic(self.engine, CH, "Adding")
        p = self.store.get_pending(CH)
        out = send(self.engine, CH, p.problem.answer.display)
        self.assertEqual(out[0].text, f"✅ Correct! {p.problem.solution}.")
        self.assertEqual(self.store.get_pending(CH).skill, "demo.add")      # only one skill in the topic


if __name__ == "__main__":
    unittest.main()
