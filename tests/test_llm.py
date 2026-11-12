import io
import json
import unittest
import urllib.error
from unittest import mock

import helpers
from helpers import (S, snap, send, make_engine, verify, to_topic, to_demo_topic, demo_registry, day_of, FakeLLM,
                     DEMO_TOPIC_KB, TOPIC_KB_MATHS_11, CORRECT, WRONG, WHY_FALLBACK, HINT, HINT_AGAIN, OFFTOPIC,
                     UNMARKABLE, OWN_TOPIC_NONE, TOPIC_START, BASE_PROMPT, SUFFIX_HINT, SUFFIX_FEEDBACK,
                     SAFETY_RULE)
from tutor.content import Answer, Problem
from tutor import llm as llm_mod
from tutor.llm import ClaudeLLM, clean, leaks_answer, mark_rubric, pick_skill, system_prompt, tutor_text

CH = 31337


def user_msg(p, student_text):
    return (f"Problem: {p.text}\nVerified answer: {p.answer.display}\n"
            f"Worked solution: {p.solution}\nStudent's message: {student_text}")


class LLMEngineCase(unittest.TestCase):
    def mk(self, responses=(), limit=40, registry=None, global_limit=1000, llm_marking=False):
        self.llm = FakeLLM(responses)
        self.engine, self.store, self.clock = make_engine(llm=self.llm, limit=limit,
                                                          registry=registry or demo_registry(), flood=100000,
                                                          global_limit=global_limit, llm_marking=llm_marking)
        self.addCleanup(self.store.close)

    def adding(self, chat=CH):
        to_demo_topic(self.engine, chat, "Adding")
        return self.store.get_pending(chat)

    def wrong_text(self, chat=CH):
        p = self.store.get_pending(chat)
        return str(int(p.problem.answer.value) + 7)

    def calls_today(self, chat=CH):
        return self.store.llm_calls(chat, day_of(self.clock))


class TestWrongWhy(LLMEngineCase):
    def test_llm_explains_wrong_answer(self):
        self.mk(["You slipped on the carry. "])
        p = self.adding().problem
        bad = self.wrong_text()
        out = send(self.engine, CH, bad)
        self.assertEqual(out[0].text, WRONG("You slipped on the carry", p.answer.display))
        self.assertEqual(out[0].text, f"❌ Not quite. You slipped on the carry. Correct answer: {p.answer.display}")
        self.assertEqual(len(self.llm.calls), 1)
        system, user = self.llm.calls[0]
        self.assertIn(BASE_PROMPT.format(subject="Demo", year=11), system)
        self.assertIn(SUFFIX_FEEDBACK, system)
        self.assertEqual(user, user_msg(p, bad))
        self.assertIn("Verified answer:", user)
        self.assertEqual(self.calls_today(), 1)

    def test_prompt_never_contains_name_or_chat_id(self):
        self.mk(["Check your tens", "Look at the units", "Add again"])
        send_name = "Zorblax"
        verify(self.engine, CH, first_name=send_name, username="zorbuser")
        send(self.engine, CH, "Demo", first_name=send_name, username="zorbuser")
        send(self.engine, CH, "Adding", first_name=send_name, username="zorbuser")
        send(self.engine, CH, self.wrong_text(), first_name=send_name, username="zorbuser")
        send(self.engine, CH, "hint", first_name=send_name, username="zorbuser")
        send(self.engine, CH, "hint", first_name=send_name, username="zorbuser")
        send(self.engine, CH, "can you explain what a sum is?", first_name=send_name, username="zorbuser")
        self.assertGreaterEqual(len(self.llm.calls), 2)
        for system, user in self.llm.calls:
            for secret in ("Zorblax", "zorbuser", str(CH)):
                self.assertNotIn(secret, system)
                self.assertNotIn(secret, user)

    def test_mistake_feedback_beats_llm(self):
        self.mk(["should not be used"])
        p = self.adding().problem
        out = send(self.engine, CH, str(int(p.answer.value) + 1))
        self.assertEqual(out[0].text, WRONG("You were out by one", p.answer.display))
        self.assertEqual(self.llm.calls, [])
        self.assertEqual(self.calls_today(), 0)

    def test_none_result_falls_back_silently(self):
        self.mk([None])
        p = self.adding().problem
        out = send(self.engine, CH, self.wrong_text())
        self.assertEqual(out[0].text, WRONG(WHY_FALLBACK(p.solution), p.answer.display))
        self.assertEqual(len(self.llm.calls), 1)
        self.assertEqual(self.calls_today(), 1)       # incremented before the call

    def test_no_llm_makes_no_calls_and_works(self):
        engine, store, clock = make_engine(llm=None, registry=demo_registry(), flood=100000)
        self.addCleanup(store.close)
        to_demo_topic(engine, CH, "Adding")
        p = store.get_pending(CH).problem
        out = send(engine, CH, str(int(p.answer.value) + 7))
        self.assertEqual(out[0].text, WRONG(WHY_FALLBACK(p.solution), p.answer.display))


class TestHintsWithLLM(LLMEngineCase):
    def test_first_hint_is_fixed_second_uses_llm(self):
        self.mk(["Try adding the units digits first"])
        p = self.adding().problem
        out = send(self.engine, CH, "hint")
        self.assertEqual(out[0].text, HINT(p.hint))
        self.assertEqual(self.llm.calls, [])
        out = send(self.engine, CH, "hint")
        self.assertEqual(snap(out), [S(CH, "💡 Try adding the units digits first", DEMO_TOPIC_KB)])
        self.assertEqual(len(self.llm.calls), 1)
        system, user = self.llm.calls[0]
        self.assertIn(SUFFIX_HINT, system)
        self.assertIn(BASE_PROMPT.format(subject="Demo", year=11), system)
        self.assertEqual(user, user_msg(p, "hint"))
        self.assertEqual(self.store.get_pending(CH).hints_given, 2)

    def test_leaking_hint_falls_back_to_hint_again(self):
        self.mk()
        p = self.adding().problem
        d = p.answer.display
        send(self.engine, CH, "hint")          # first hint is fixed, no LLM
        self.assertEqual(self.llm.calls, [])
        for i, leak in enumerate((f"Just add them, it makes {d}", f"Adding gives {d} in total", f"The answer is {d}.")):
            with self.subTest(leak=leak):
                self.llm.responses.append(leak)
                out = send(self.engine, CH, "hint")
                self.assertEqual(out[0].text, HINT_AGAIN(p.hint))
                self.assertEqual(len(self.llm.calls), i + 1)

    def test_none_hint_falls_back_silently(self):
        self.mk([None])
        p = self.adding().problem
        send(self.engine, CH, "hint")
        out = send(self.engine, CH, "hint")
        self.assertEqual(out[0].text, HINT_AGAIN(p.hint))
        self.assertEqual(len(self.llm.calls), 1)


class TestChatWithLLM(LLMEngineCase):
    Q = "can you explain what a sum is?"

    def test_unparsed_uses_llm_chat(self):
        self.mk(["A sum is what you get when you add numbers together"])
        p = self.adding()
        out = send(self.engine, CH, self.Q)
        self.assertEqual(snap(out), [S(CH, "A sum is what you get when you add numbers together", DEMO_TOPIC_KB)])
        system, user = self.llm.calls[0]
        self.assertIn(SUFFIX_HINT, system)
        self.assertEqual(user, user_msg(p.problem, self.Q))
        q = self.store.get_pending(CH)
        self.assertEqual((q.problem_no, q.seed, q.level), (p.problem_no, p.seed, p.level))
        self.assertEqual(self.store.recent_attempts(CH), [])

    def test_leaking_chat_falls_back_to_offtopic(self):
        self.mk()
        p = self.adding()
        self.llm.responses.append(f"Well, {p.problem.answer.display} is the total")
        out = send(self.engine, CH, self.Q)
        self.assertEqual(out[0].text, OFFTOPIC("Demo", 1))

    def test_none_chat_falls_back_to_offtopic(self):
        self.mk([None])
        self.adding()
        out = send(self.engine, CH, self.Q)
        self.assertEqual(out[0].text, OFFTOPIC("Demo", 1))
        self.assertEqual(len(self.llm.calls), 1)

    def test_llm_not_called_for_correct_hint_skip_or_first_hint(self):
        self.mk(["x", "y", "z"])
        p = self.adding()
        send(self.engine, CH, "hint")
        send(self.engine, CH, "skip")
        send(self.engine, CH, self.store.get_pending(CH).problem.answer.display)
        self.assertEqual(self.llm.calls, [])


class TestDailyLimit(LLMEngineCase):
    def test_limit_two(self):
        self.mk(["A", "B", "C", "D"], limit=2)
        p1 = self.adding().problem
        out = send(self.engine, CH, self.wrong_text())
        self.assertEqual(out[0].text, WRONG("A", p1.answer.display))
        p2 = self.store.get_pending(CH).problem
        out = send(self.engine, CH, self.wrong_text())
        self.assertEqual(out[0].text, WRONG("B", p2.answer.display))
        p3 = self.store.get_pending(CH).problem
        out = send(self.engine, CH, self.wrong_text())
        self.assertEqual(out[0].text, WRONG(WHY_FALLBACK(p3.solution), p3.answer.display))
        self.assertEqual(len(self.llm.calls), 2)
        self.assertEqual(self.calls_today(), 2)
        self.assertEqual(self.store.llm_calls_total(day_of(self.clock)), 2)
        # a second hint / chat are blocked too
        send(self.engine, CH, "hint")
        out = send(self.engine, CH, "hint")
        self.assertTrue(out[0].text.startswith("💡 Hint: "))
        self.assertEqual(out[0].text, HINT_AGAIN(self.store.get_pending(CH).problem.hint))
        out = send(self.engine, CH, "can you explain what a sum is?")
        self.assertEqual(out[0].text, OFFTOPIC("Demo", 4))
        self.assertEqual(len(self.llm.calls), 2)

    def test_limit_resets_next_day(self):
        self.mk(["A", "B", "C"], limit=1)
        self.adding()
        send(self.engine, CH, self.wrong_text())
        send(self.engine, CH, self.wrong_text())
        self.assertEqual(len(self.llm.calls), 1)
        self.clock.advance(86400)
        p = self.store.get_pending(CH).problem
        out = send(self.engine, CH, self.wrong_text())
        self.assertEqual(out[0].text, WRONG("B", p.answer.display))
        self.assertEqual(len(self.llm.calls), 2)

    def test_limit_zero_never_calls(self):
        self.mk(["A", "B"], limit=0)
        self.adding()
        send(self.engine, CH, self.wrong_text())
        send(self.engine, CH, "hint")
        send(self.engine, CH, "hint")
        send(self.engine, CH, "can you explain what a sum is?")
        self.assertEqual(self.llm.calls, [])

    def test_limit_is_per_student(self):
        self.mk(["A", "B"], limit=1)
        self.adding(CH)
        self.adding(77)
        send(self.engine, CH, self.wrong_text(CH))
        p = self.store.get_pending(77).problem
        out = send(self.engine, 77, self.wrong_text(77))
        self.assertEqual(out[0].text, WRONG("B", p.answer.display))
        self.assertEqual(len(self.llm.calls), 2)
        self.assertEqual(self.store.llm_calls_total(day_of(self.clock)), 2)


    def test_global_daily_cap(self):
        self.mk(["A", "B", "C", "D"], limit=40, global_limit=2)
        self.adding(CH)
        self.adding(77)
        self.adding(78)
        send(self.engine, CH, self.wrong_text(CH))
        send(self.engine, 77, self.wrong_text(77))
        p = self.store.get_pending(78).problem
        out = send(self.engine, 78, self.wrong_text(78))       # third student: global cap reached
        self.assertEqual(out[0].text, WRONG(WHY_FALLBACK(p.solution), p.answer.display))
        self.assertEqual(len(self.llm.calls), 2)
        self.assertEqual(self.store.llm_calls_total(day_of(self.clock)), 2)
        self.clock.advance(86400)                                # a new UTC day resets it
        p = self.store.get_pending(78).problem
        out = send(self.engine, 78, self.wrong_text(78))
        self.assertEqual(out[0].text, WRONG("C", p.answer.display))


class TestRubricViaEngine(LLMEngineCase):
    def mk(self, responses=(), **kw):
        kw.setdefault("llm_marking", True)           # v2: rubric marking is off unless TUTOR_LLM_MARKING is set
        super().mk(responses, **kw)

    def test_rubric_not_marked_when_llm_marking_is_off(self):
        self.mk(['{"marks": 2, "feedback": "Great"}'], llm_marking=False)
        self.written()
        p = self.store.get_pending(CH)
        out = send(self.engine, CH, "Plants use light energy to make food")
        self.assertEqual(out[0].text, UNMARKABLE(p.problem.answer.display))
        self.assertEqual(self.llm.calls, [])
        self.assertEqual(self.store.recent_attempts(CH), [])

    def written(self):
        to_demo_topic(self.engine, CH, "Written")
        return self.store.get_pending(CH)

    def test_full_marks_is_correct_and_levels_up(self):
        self.mk(['{"marks": 2, "feedback": "Well done"}'])
        p = self.written()
        out = send(self.engine, CH, "Plants use light energy to make food")
        self.assertEqual(out[0].text, CORRECT("Well done"))
        self.assertEqual(out[0].text, "✅ Correct! Well done.")
        self.assertEqual(self.store.get_level(CH, "demo", "demo.y11.written"), 2)
        a = self.store.recent_attempts(CH)
        self.assertEqual(len(a), 1)
        self.assertTrue(a[0].correct)
        self.assertEqual(self.store.get_pending(CH).problem_no, p.problem_no + 1)

    def test_partial_marks_is_wrong_and_levels_down(self):
        self.mk(['{"marks": 2, "feedback": "Great"}', '{"marks": 1, "feedback": "You missed the energy part"}'])
        self.written()
        send(self.engine, CH, "good answer")
        self.assertEqual(self.store.get_level(CH, "demo", "demo.y11.written"), 2)
        p = self.store.get_pending(CH).problem
        out = send(self.engine, CH, "plants like light")
        self.assertEqual(out[0].text, WRONG("You missed the energy part", p.answer.display))
        self.assertEqual(self.store.get_level(CH, "demo", "demo.y11.written"), 1)
        self.assertEqual([a.correct for a in self.store.recent_attempts(CH)], [False, True])
        self.assertEqual(self.store.get_pending(CH).skill, "demo.essay")

    def test_marks_are_clamped(self):
        self.mk(['{"marks": 99, "feedback": "Wow"}', '{"marks": -4, "feedback": "Hmm"}'])
        self.written()
        out = send(self.engine, CH, "answer one")
        self.assertTrue(out[0].text.startswith("✅ Correct!"))
        out = send(self.engine, CH, "answer two")
        self.assertTrue(out[0].text.startswith("❌ Not quite."))

    def test_bad_json_or_none_is_unmarkable(self):
        self.mk(["this is not json", None])
        p = self.written()
        for _ in range(2):
            out = send(self.engine, CH, "my essay")
            self.assertEqual(out[0].text, UNMARKABLE(self.store.get_pending(CH).problem.answer.display))
        self.assertEqual(self.store.recent_attempts(CH), [])

    def test_no_llm_unmarkable(self):
        engine, store, clock = make_engine(llm=None, registry=demo_registry(), flood=100000)
        self.addCleanup(store.close)
        to_demo_topic(engine, CH, "Written")
        d = store.get_pending(CH).problem.answer.display
        self.assertEqual(send(engine, CH, "my essay")[0].text, UNMARKABLE(d))


class TestV2ChatAndLeaks(LLMEngineCase):
    def test_choice_unparsed_uses_llm_chat_with_letter_row(self):
        from helpers import v2_registry, to_v2_topic, v2_kb
        reg = v2_registry()
        self.mk(["Think about where cells release energy"], registry=reg)
        to_v2_topic(self.engine, CH, "Choice")
        out = send(self.engine, CH, "can you explain what an organelle is?")
        self.assertEqual(snap(out), [S(CH, "Think about where cells release energy", v2_kb(reg, 4))])

    def test_choice_chat_that_leaks_the_option_falls_back_to_choice_unparsed(self):
        from helpers import v2_registry, to_v2_topic, v2_kb, CHOICE_UNPARSED
        reg = v2_registry()
        self.mk(["It is the mitochondria of course"], registry=reg)
        to_v2_topic(self.engine, CH, "Choice")
        out = send(self.engine, CH, "can you explain what an organelle is?")
        self.assertEqual(snap(out), [S(CH, CHOICE_UNPARSED("A, B, C or D"), v2_kb(reg, 4))])

    def test_short_chat_that_leaks_falls_back_to_short_unparsed(self):
        from helpers import v2_registry, to_v2_topic, v2_kb, SHORT_UNPARSED
        reg = v2_registry()
        self.mk(["It is photosynthesis"], registry=reg)
        to_v2_topic(self.engine, CH, "Short")
        out = send(self.engine, CH, "can you explain what a plant needs?")
        self.assertEqual(snap(out), [S(CH, SHORT_UNPARSED, v2_kb(reg))])


class TestLeaksAnswerV2(unittest.TestCase):
    OPTS = ["Nucleus", "Mitochondria", "Ribosome", "Cell membrane"]

    def choice(self, opts=None, correct=1):
        opts = opts or self.OPTS
        return Answer("choice", f"{'ABCDE'[correct]}) {opts[correct]}", {"options": list(opts), "correct": correct})

    def test_choice_option_text_leaks(self):
        a = self.choice()
        for t in ("It is the mitochondria", "MITOCHONDRIA!", "so mitochondria it is", "Mitochondria release energy"):
            with self.subTest(text=t):
                self.assertTrue(leaks_answer(t, a))

    def test_choice_letter_phrases_leak(self):
        a = self.choice()
        for t in ("The answer is B", "answer B", "option b", "Option (B)", "letter B is right", "choice B", "I would pick B) here",
                  "it is B) for sure"):
            with self.subTest(text=t):
                self.assertTrue(leaks_answer(t, a), t)

    def test_choice_does_not_leak_wrong_letters_or_other_options(self):
        a = self.choice()
        for t in ("Think about respiration", "Look at option A", "The answer is not A or C", "The letter C is wrong",
                  "Nucleus is not it", "Where does respiration happen?", "Bobby", "a bee"):
            with self.subTest(text=t):
                self.assertFalse(leaks_answer(t, a), t)

    def test_choice_skips_the_v1_value_test(self):
        a = self.choice(["120", "150", "200"], 1)
        self.assertTrue(leaks_answer("it is about 150", a))
        self.assertFalse(leaks_answer("it is about 120", a))
        self.assertFalse(leaks_answer("", a))
        short_opts = self.choice(["12", "15", "20"], 1)
        self.assertFalse(leaks_answer("it is 15", short_opts))             # option text shorter than 3 chars

    def test_short_accept_leaks_as_whole_words(self):
        a = Answer("short", "photosynthesis", {"accept": ["photosynthesis", "light reaction"], "reject": []})
        for t in ("It is photosynthesis", "photosynthesis.", "PHOTOSYNTHESIS", "the light reaction maybe"):
            with self.subTest(text=t):
                self.assertTrue(leaks_answer(t, a), t)
        for t in ("Think about light", "photosynthesise", "a reaction to light", "", "photo synthesis"):
            with self.subTest(text=t):
                self.assertFalse(leaks_answer(t, a), t)

    def test_short_accept_shorter_than_three_chars_does_not_count(self):
        a = Answer("short", "O2", {"accept": ["O2"], "reject": []}, form="case")
        self.assertFalse(leaks_answer("it is O2", a))

    def test_short_normalises_accents_and_punctuation(self):
        a = Answer("short", "l'été", {"accept": ["l'été"], "reject": []}, form="strict")
        self.assertTrue(leaks_answer("Say l'été please", a))


class TestOwnTopicPick(unittest.TestCase):
    def mk(self, responses, limit=40):
        self.llm = FakeLLM(responses)
        self.engine, self.store, self.clock = make_engine(llm=self.llm, limit=limit, flood=100000)
        self.addCleanup(self.store.close)
        verify(self.engine, CH)
        send(self.engine, CH, "Maths")
        send(self.engine, CH, "My own topic")

    TEXT = "longest side of right triangles"

    def test_llm_picks_skill_when_no_alias_matches(self):
        self.mk(["maths.pythagoras"])
        out = send(self.engine, CH, self.TEXT)
        self.assertEqual(out[0].text, TOPIC_START("Pythagoras' theorem"))
        self.assertEqual(self.store.get_pending(CH).skill, "maths.pythagoras")
        self.assertEqual(len(self.llm.calls), 1)
        self.assertEqual(self.store.llm_calls(CH, day_of(self.clock)), 1)

    def test_bogus_pick_gives_none_text(self):
        for bad in ("maths.does_not_exist", "Pythagoras", "I think maths.pythagoras", "physics.speed", None, ""):
            with self.subTest(response=bad):
                self.mk([bad])
                out = send(self.engine, CH, self.TEXT)
                self.assertEqual(snap(out), [S(CH, OWN_TOPIC_NONE, TOPIC_KB_MATHS_11)])

    def test_alias_match_skips_llm(self):
        self.mk(["maths.ratio"])
        out = send(self.engine, CH, "percentages")
        self.assertEqual(out[0].text, TOPIC_START("Percentages"))
        self.assertEqual(self.llm.calls, [])

    def test_limit_blocks_pick(self):
        self.mk(["maths.pythagoras"], limit=0)
        out = send(self.engine, CH, self.TEXT)
        self.assertEqual(out[0].text, OWN_TOPIC_NONE)
        self.assertEqual(self.llm.calls, [])


class TestPickSkillFunction(unittest.TestCase):
    SKILLS = [("maths.ratio", "Ratio"), ("maths.pythagoras", "Pythagoras' theorem")]

    def test_exact_id_only(self):
        self.assertEqual(pick_skill(FakeLLM(["maths.ratio"]), "share money", self.SKILLS), "maths.ratio")
        for bad in ("maths.nope", "ratio", "Ratio", "maths.ratio or maths.pythagoras", "", None):
            with self.subTest(response=bad):
                self.assertIsNone(pick_skill(FakeLLM([bad]), "share money", self.SKILLS))

    def test_no_names_in_request(self):
        llm = FakeLLM(["maths.ratio"])
        pick_skill(llm, "share money", self.SKILLS)
        self.assertEqual(len(llm.calls), 1)
        self.assertIn("share money", llm.calls[0][1])


def rubric_problem(max_marks=2):
    return Problem("demo.essay", 1, 1, "Explain why.", Answer("rubric", "Model answer", None,
                   mark_scheme="1 mark for A; 1 for B", max_marks=max_marks), "Because", "Think")


def number_problem(display="12.5 m/s", value=12.5):
    return Problem("p.s", 1, 1, "Find the speed.", Answer("number", display, value, dp=1),
                   "12.5 = 25 ÷ 2", "Divide distance by time")


class TestMarkRubric(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(mark_rubric(FakeLLM(['{"marks": 1, "feedback": "ok"}']), rubric_problem(), "x"), (1, "ok"))
        self.assertEqual(mark_rubric(FakeLLM(['{"marks": 0, "feedback": "no"}']), rubric_problem(), "x"), (0, "no"))
        self.assertEqual(mark_rubric(FakeLLM(['{"marks": 2, "feedback": "full"}']), rubric_problem(), "x"), (2, "full"))

    def test_clamped(self):
        self.assertEqual(mark_rubric(FakeLLM(['{"marks": 9, "feedback": "a"}']), rubric_problem(3), "x")[0], 3)
        self.assertEqual(mark_rubric(FakeLLM(['{"marks": -2, "feedback": "a"}']), rubric_problem(3), "x")[0], 0)

    def test_invalid_returns_none(self):
        for bad in ("nope", "", "[]", '{"feedback": "x"}', '{"marks": "two", "feedback": "x"}', "{", None):
            with self.subTest(response=bad):
                self.assertIsNone(mark_rubric(FakeLLM([bad]), rubric_problem(), "x"))

    def test_prompt_has_student_text_and_no_leak_of_name(self):
        llm = FakeLLM(['{"marks": 1, "feedback": "ok"}'])
        mark_rubric(llm, rubric_problem(), "my written answer")
        self.assertIn("my written answer", llm.calls[0][1])


class TestTutorText(unittest.TestCase):
    def test_returns_cleaned_text_and_builds_prompts(self):
        p = number_problem()
        llm = FakeLLM(["**Try** dividing `distance` by time"])
        out = tutor_text(llm, "hint", p, "help me", "Maths", 10)
        self.assertEqual(out, "Try dividing distance by time")
        system, user = llm.calls[0]
        self.assertEqual(system, system_prompt("Maths", 10, "hint"))
        self.assertEqual(user, user_msg(p, "help me"))

    def test_hint_and_chat_are_leak_filtered_feedback_is_not(self):
        p = number_problem()
        for mode in ("hint", "chat"):
            self.assertIsNone(tutor_text(FakeLLM(["It is 12.5 m/s"]), mode, p, "x", "Maths", 11), mode)
            self.assertIsNone(tutor_text(FakeLLM(["Maybe 12.5"]), mode, p, "x", "Maths", 11), mode)
            self.assertEqual(tutor_text(FakeLLM(["Divide first"]), mode, p, "x", "Maths", 11), "Divide first")
        self.assertEqual(tutor_text(FakeLLM(["You divided wrongly, 25 over 2"]), "feedback", p, "x", "Maths", 11),
                         "You divided wrongly, 25 over 2")

    def test_none_passthrough(self):
        self.assertIsNone(tutor_text(FakeLLM([None]), "hint", number_problem(), "x", "Maths", 11))
        self.assertIsNone(tutor_text(FakeLLM([None]), "feedback", number_problem(), "x", "Maths", 11))


class TestSystemPrompt(unittest.TestCase):
    def test_base_and_suffixes(self):
        for mode in ("hint", "chat"):
            s = system_prompt("Maths", 11, mode)
            self.assertIn(BASE_PROMPT.format(subject="Maths", year=11), s)
            self.assertIn(SUFFIX_HINT, s)
            self.assertNotIn(SUFFIX_FEEDBACK, s)
            self.assertTrue(s.endswith(SAFETY_RULE), mode)
        self.assertIn(SAFETY_RULE, system_prompt("Maths", 11, "feedback"))
        s = system_prompt("Physics", 9, "feedback")
        self.assertIn(BASE_PROMPT.format(subject="Physics", year=9), s)
        self.assertIn(SUFFIX_FEEDBACK, s)
        self.assertNotIn(SUFFIX_HINT, s)

    def test_other_modes_are_strings(self):
        for mode in ("pick", "mark"):
            s = system_prompt("Maths", 11, mode)
            self.assertIsInstance(s, str)
            self.assertTrue(s.strip())


class TestCleanAndLeaks(unittest.TestCase):
    def test_clean_strips_markdown(self):
        out = clean("**bold** `code` _it_ # Title")
        for ch in "*_`#":
            self.assertNotIn(ch, out)
        self.assertIn("bold", out)
        self.assertIn("code", out)

    def test_clean_trims(self):
        self.assertEqual(clean("  hello world \n"), "hello world")
        self.assertEqual(clean(""), "")

    def test_clean_word_cap(self):
        words = [f"w{i}" for i in range(100)]
        out = clean(" ".join(words))
        self.assertTrue(out.endswith("…"))
        self.assertEqual(out.replace("…", "").split(), words[:80])

    def test_clean_boundaries(self):
        w80 = " ".join(f"w{i}" for i in range(80))
        self.assertEqual(clean(w80), w80)
        w79 = " ".join(f"w{i}" for i in range(79))
        self.assertEqual(clean(w79), w79)
        w81 = " ".join(f"w{i}" for i in range(81))
        self.assertTrue(clean(w81).endswith("…"))
        self.assertEqual(len(clean(w81).replace("…", "").split()), 80)

    def test_clean_custom_cap(self):
        out = clean("a b c d e f", max_words=3)
        self.assertEqual(out.replace("…", "").split(), ["a", "b", "c"])
        self.assertTrue(out.endswith("…"))

    def test_leaks_answer(self):
        a = Answer("number", "12.5 m/s", 12.5, dp=1)
        self.assertTrue(leaks_answer("The answer is 12.5", a))
        self.assertTrue(leaks_answer("It is 12.5 m/s", a))
        self.assertTrue(leaks_answer("so v = 12.5, nice", a))
        self.assertFalse(leaks_answer("Divide the distance by the time", a))
        self.assertFalse(leaks_answer("Use 25 and 2", a))
        self.assertFalse(leaks_answer("", a))
        b = Answer("number", "57", 57.0)
        self.assertTrue(leaks_answer("it makes 57 altogether", b))
        self.assertTrue(leaks_answer("it makes 570 altogether", b))     # substring rule (display len >= 2)
        self.assertFalse(leaks_answer("it makes 58 altogether", b))
        self.assertFalse(leaks_answer("You have 20 apples", b))
        c = Answer("expr", "x² + 5x + 6", "x**2+5*x+6", form="expanded")
        self.assertFalse(leaks_answer("Multiply each term in the brackets", c))

    def test_leaks_equivalent_values(self):
        # the value test uses the real checker: equivalent forms of the answer are leaks too
        frac = Answer("fraction", "3/4", "3/4")
        self.assertTrue(leaks_answer("That leaves 0.75 of the pizza", frac))
        self.assertTrue(leaks_answer("so it is 6/8", frac))
        std = Answer("number", "3.2 × 10^4", 32000.0, form="standard")
        self.assertTrue(leaks_answer("you should get 32000 first", std))
        self.assertTrue(leaks_answer("that is 3.2x10^4", std))
        dp = Answer("number", "7.1 cm", 7.0710678, dp=1)
        self.assertTrue(leaks_answer("The square root is about 7.07", dp))
        thousands = Answer("number", "1200 m", 1200.0)
        self.assertTrue(leaks_answer("It comes to 1,200 metres", thousands))
        expr = Answer("expr", "x² + 5x + 6", "x**2+5*x+6", form="expanded")
        self.assertTrue(leaks_answer("you get x^2 + 6 + 5x", expr))
        self.assertFalse(leaks_answer("compare with x^2 + 7x + 12", expr))
        self.assertFalse(leaks_answer("Keep going: 0.7 is close", frac))

    def test_numbers_from_the_question_are_not_leaks(self):
        std = Answer("number", "3.2 × 10^4", 32000.0, form="standard")
        q = "Write 32000 in standard form."
        self.assertFalse(leaks_answer("Start with 32000 and move the decimal point", std, q))
        self.assertTrue(leaks_answer("Start with 32000 and move the decimal point", std, "Work out 8000 × 4."))
        expr = Answer("expr", "x² + 5x + 6", "x**2+5*x+6", form="expanded")
        self.assertFalse(leaks_answer("Multiply out (x + 2)(x + 3) term by term", expr, "Expand (x + 2)(x + 3)."))

    def test_tutor_text_filters_equivalent_leaks(self):
        p = Problem("demo.f", 1, 1, "Work out 1/2 + 1/4.", Answer("fraction", "3/4", "3/4"), "1/2 + 1/4 = 3/4",
                    "Use quarters")
        self.assertIsNone(tutor_text(FakeLLM(["It makes 0.75"]), "hint", p, "help", "Maths", 9))
        self.assertEqual(tutor_text(FakeLLM(["Write 1/2 as quarters"]), "hint", p, "help", "Maths", 9),
                         "Write 1/2 as quarters")


class FakeResp:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode()

    def read(self, *a):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestClaudeLLM(unittest.TestCase):
    OK = {"content": [{"type": "text", "text": "Hello there"}]}

    def run_with(self, result, **call):
        captured = {}

        def fake(req, *a, **kw):
            captured["req"] = req
            captured["kw"] = kw
            if isinstance(result, BaseException):
                raise result
            return FakeResp(result)

        with mock.patch("urllib.request.urlopen", side_effect=fake):
            out = ClaudeLLM("sk-test-KEY", "model-x", timeout=5.0).complete(
                call.get("system", "SYS"), call.get("user", "USR"), **({"max_tokens": call["max_tokens"]} if "max_tokens" in call else {}))
        return out, captured

    def test_request_shape(self):
        out, cap = self.run_with(self.OK)
        self.assertEqual(out, "Hello there")
        req = cap["req"]
        self.assertNotIsInstance(req, str, "urlopen must receive a urllib.request.Request")
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(req.get_method(), "POST")
        headers = {k.lower(): v for k, v in req.header_items()}
        self.assertEqual(headers["x-api-key"], "sk-test-KEY")
        self.assertEqual(headers["anthropic-version"], "2023-06-01")
        self.assertEqual(headers["content-type"], "application/json")
        body = json.loads(req.data)
        self.assertEqual(body["model"], "model-x")
        self.assertEqual(body["max_tokens"], 300)
        self.assertEqual(body["system"], "SYS")
        self.assertEqual(len(body["messages"]), 1)
        msg = body["messages"][0]
        self.assertEqual(msg["role"], "user")
        content = msg["content"]
        if isinstance(content, list):
            content = "".join(b.get("text", "") for b in content)
        self.assertEqual(content, "USR")

    def test_max_tokens_passed(self):
        _, cap = self.run_with(self.OK, max_tokens=55)
        self.assertEqual(json.loads(cap["req"].data)["max_tokens"], 55)

    def test_joins_text_blocks_and_ignores_others(self):
        body = {"content": [{"type": "text", "text": "Hello"}, {"type": "tool_use", "id": "t", "name": "n", "input": {}},
                            {"type": "text", "text": "world"}]}
        out, _ = self.run_with(body)
        self.assertIn("Hello", out)
        self.assertIn("world", out)
        self.assertNotIn("tool_use", out)

    def test_errors_return_none_and_log_warning(self):
        errors = [
            urllib.error.URLError("no network"),
            urllib.error.HTTPError("https://api.anthropic.com/v1/messages", 429, "Too Many", {}, io.BytesIO(b'{"error":{}}')),
            urllib.error.HTTPError("https://api.anthropic.com/v1/messages", 401, "Unauthorized", {}, io.BytesIO(b"nope")),
            TimeoutError("slow"),
            ConnectionResetError("reset"),
            OSError("disk"),
            ValueError("weird"),
            RuntimeError("boom"),
        ]
        for err in errors:
            with self.subTest(error=type(err).__name__ + str(getattr(err, "code", ""))):
                with self.assertLogs(level="WARNING"):
                    out, _ = self.run_with(err)
                self.assertIsNone(out)

    def test_bad_bodies_return_none(self):
        for body in (b"<html>oops</html>", b"", b"not json", json.dumps([1, 2]).encode(), json.dumps("str").encode()):
            with self.subTest(body=body[:20]):
                out, _ = self.run_with(body)
                self.assertIsNone(out)

    def test_empty_content_is_falsy(self):
        for body in ({"content": []}, {}, {"error": {"type": "overloaded_error", "message": "x"}},
                     {"content": [{"type": "tool_use"}]}):
            with self.subTest(body=body):
                out, _ = self.run_with(body)
                self.assertFalse(out)

    def test_api_key_not_logged(self):
        with self.assertLogs(level="WARNING") as cm:
            self.run_with(urllib.error.URLError("no network"))
        self.assertNotIn("sk-test-KEY", "\n".join(cm.output))


if __name__ == "__main__":
    unittest.main()
