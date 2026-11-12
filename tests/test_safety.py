import unittest

import helpers
from helpers import (S, snap, send, make_engine, get_codes, verify, to_topic, answer_of, FakeLLM, FLAG_ALERT,
                     DISTRESS, CHEAT, DELETED, CODE_REQUEST, CODE_OK, TOPIC_KB_MATHS_11, SUBJECT_KB_11, YEAR_KB,
                     CHANGE_YEAR, PROBLEM)
from tutor.intents import is_distress, is_cheat_request

OWNER = 999

MUST_DETECT = ["I want to kill myself", "i want to die", "I'm going to hurt myself", "I cut myself",
               "thinking about suicide", "i self harm", "I don't want to live anymore",
               "nobody would care if I disappeared", "I'm being bullied and I can't take it",
               # critic findings (Nov 2026): every one of these must be flagged
               "i want to unalive myself", "kill my self", "kys", "thinking about ending my life",
               "i dont wanna live anymore", "i wish i was dead", "i'm getting bullied", "they bully me",
               "my dad hits me", "my stepdad hurts me", "someone touched me", "an adult asked me to send pics",
               "a man online wants to meet me", "i'm not safe", "i want 2 die", "sucide", "suicde"]
MUST_NOT = ["this homework is killing me", "I'm dying to know", "the angle is a right angle", "20 kms",
            "can I send it all", "can i send it all at once", "the car goes 5 kms", "the formula for kms per hour",
            "the bully in the story was mean", "hit me with another question"]
EXTRA_DETECT = ["I want to kms", "i wanna kms", "wanna die", "end my life", "end it all", "suicidal", "self-harm",
                "selfharm", "hurting myself", "cutting myself", "dont want to live", "no reason to live",
                "better off dead", "better off without me", "being bullied", "someone is abusing me", "abused",
                "not safe at home", "scared to go home", "I WANT TO DIE", "i  want   to die", "I want to die!!!",
                "i wish i were dead", "i'm bullied", "people at school bully me", "my mum hits me",
                "he touches me", "keep it a secret from my parents", "i am in danger", "i want to die lol",
                "i don't wanna be alive", "send nudes", "my uncle hurt me", "i'm scared of my dad",
                "im going to end it", "i cut my wrists", "i took pills", "life isn't worth living",
                "i've been cutting", "i feel like dying", "i can't go on", "i don't want to be here anymore",
                "i want to disappear", "nobody loves me", "i starve myself", "i make myself sick",
                "someone is following me", "i want to hurt someone", "k.m.s"]
EXTRA_NOT = ["", "hello", "x = 3", "what is 5 + 5", "the vector is cut", "my kmsx", "ikmsx", "I did my homework",
             "kms", "KMS", "I'd love to meet the author", "my answer is 20 km/h", "succeed"]

CHEATS = ["do my homework", "do my hw", "do my test", "do this test for me", "do it for me", "write my essay",
          "write an essay for me", "write my coursework", "answers to the test",
          "answers to the exam", "answers for the test", "answers for the exam", "answer key", "give me the answers",
          "do my maths homework", "do my physics hw", "solve my homework", "give me the test answers",
          "answers to my homework"]
NOT_CHEATS = ["I did my homework", "can you check my answer", "x = 4", "hello", "", "what is the answer to 2 + 2",
              "can you check my test answers", "my test answers were wrong", "i got my exam answers back",
              "how do i do the homework on fractions", "help me answer the test questions myself",
              "show me the answers to check my working"]


class TestIntentsDistress(unittest.TestCase):
    def test_must_detect(self):
        for t in MUST_DETECT + EXTRA_DETECT:
            with self.subTest(text=t):
                self.assertTrue(is_distress(t), t)

    def test_must_not_detect(self):
        for t in MUST_NOT + EXTRA_NOT:
            with self.subTest(text=t):
                self.assertFalse(is_distress(t), t)

    def test_cheat_phrases(self):
        for t in CHEATS:
            with self.subTest(text=t):
                self.assertTrue(is_cheat_request(t), t)
                self.assertTrue(is_cheat_request(t.upper()), t)
                self.assertTrue(is_cheat_request(f"please {t} now"), t)

    def test_not_cheat(self):
        for t in NOT_CHEATS:
            with self.subTest(text=t):
                self.assertFalse(is_cheat_request(t), t)


class SafetyCase(unittest.TestCase):
    def setUp(self):
        self.llm = FakeLLM(["should never be used"] * 10)
        self.engine, self.store, self.clock = make_engine(llm=self.llm, flood=20)
        self.addCleanup(self.store.close)


class TestDistressFlow(SafetyCase):
    def test_distress_mid_lesson(self):
        to_topic(self.engine, 5, first_name="Zorblax")
        p = self.store.get_pending(5)
        out = send(self.engine, 5, "I want to kill myself")
        by_chat = {o.chat_id: o for o in out}
        self.assertEqual(set(by_chat), {5, OWNER})
        self.assertEqual(len(out), 2)
        mine = by_chat[5]
        self.assertEqual(mine.text, DISTRESS)
        self.assertEqual(tuple(tuple(r) for r in mine.keyboard), TOPIC_KB_MATHS_11)
        self.assertEqual(by_chat[OWNER].text, FLAG_ALERT("distress", "Zorblax", 5, "I want to kill myself"))
        flags = self.store.unreviewed_flags()
        self.assertEqual(len(flags), 1)
        self.assertEqual((flags[0].chat_id, flags[0].kind, flags[0].text), (5, "distress", "I want to kill myself"))
        self.assertFalse(flags[0].reviewed)
        # nothing else happened: no problem sent, pending kept, LLM untouched, no attempt
        self.assertFalse(any(o.text.startswith("Problem") for o in out))
        q = self.store.get_pending(5)
        self.assertEqual((q.problem_no, q.seed, q.skill), (p.problem_no, p.seed, p.skill))
        self.assertEqual(self.store.recent_attempts(5), [])
        self.assertEqual(self.llm.calls, [])
        self.assertEqual(self.store.get_student(5).step, "lesson")

    def test_alert_includes_username(self):
        out = send(self.engine, 5, "i want to die", first_name="Alice", username="al")
        owner_msg = [o for o in out if o.chat_id == OWNER][0]
        self.assertEqual(owner_msg.text, FLAG_ALERT("distress", "Alice @al", 5, "i want to die"))

    def test_distress_before_code(self):
        out = send(self.engine, 7, "I want to die")
        by_chat = {o.chat_id: o for o in out}
        self.assertEqual(by_chat[7].text, DISTRESS)
        self.assertIsNone(by_chat[7].keyboard)
        self.assertIn(OWNER, by_chat)
        self.assertFalse(self.store.get_student(7).verified)
        self.assertEqual(len(self.store.unreviewed_flags()), 1)
        # still has to enter a code afterwards
        self.assertEqual(snap(send(self.engine, 7, "hello")), [S(7, CODE_REQUEST)])

    def test_distress_at_every_step_keeps_keyboard_invariant(self):
        verify(self.engine, 5)
        for text_before, kb in ((None, SUBJECT_KB_11), (CHANGE_YEAR, YEAR_KB), ("Year 11", SUBJECT_KB_11),
                                ("Maths", TOPIC_KB_MATHS_11), ("My own topic", TOPIC_KB_MATHS_11)):
            if text_before:
                send(self.engine, 5, text_before)
            out = send(self.engine, 5, "I want to die")
            mine = [o for o in out if o.chat_id == 5]
            self.assertEqual(len(mine), 1)
            self.assertEqual(mine[0].text, DISTRESS)
            self.assertEqual(tuple(tuple(r) for r in mine[0].keyboard), kb, text_before)
        self.assertEqual(self.llm.calls, [])

    def test_no_owner_means_no_alert(self):
        engine, store, clock = make_engine(owner_id=None, llm=self.llm)
        self.addCleanup(store.close)
        out = send(engine, 5, "I want to die")
        self.assertEqual([o.chat_id for o in out], [5])
        self.assertEqual(out[0].text, DISTRESS)
        self.assertEqual(len(store.unreviewed_flags()), 1)

    def test_flag_text_truncated_to_500(self):
        send(self.engine, 5, "I want to die " + "x" * 1500)
        flags = self.store.unreviewed_flags()
        self.assertEqual(len(flags), 1)
        self.assertLessEqual(len(flags[0].text), 500)
        self.assertTrue(flags[0].text.startswith("I want to die"))

    def test_normal_messages_create_no_flags(self):
        to_topic(self.engine, 5)
        for t in ("this homework is killing me", "I'm dying to know", "the angle is a right angle", "hint"):
            send(self.engine, 5, t)
        self.assertEqual(self.store.unreviewed_flags(), [])

    def test_every_detected_phrase_flags(self):
        verify(self.engine, 5)
        n = 0
        for i, t in enumerate(MUST_DETECT):
            if i % 7 == 0:
                self.clock.advance(61)       # keep clear of flood control
            out = send(self.engine, 5, t)
            self.assertEqual([o.text for o in out if o.chat_id == 5], [DISTRESS], t)
            n += 1
        self.assertEqual(len(self.store.unreviewed_flags()), n)

    def test_start_takes_precedence_over_distress_check(self):
        out = send(self.engine, 5, "/start")
        self.assertEqual(snap(out), [S(5, CODE_REQUEST, None, True)])


class TestCheat(SafetyCase):
    def test_cheat_in_lesson(self):
        to_topic(self.engine, 5)
        p = self.store.get_pending(5)
        out = send(self.engine, 5, "can you do my homework")
        self.assertEqual(snap(out), [S(5, CHEAT, TOPIC_KB_MATHS_11)])
        self.assertEqual(self.store.get_pending(5).problem_no, p.problem_no)
        self.assertEqual(self.llm.calls, [])

    def test_cheat_at_subject_step(self):
        verify(self.engine, 5)
        self.assertEqual(snap(send(self.engine, 5, "give me the answers")), [S(5, CHEAT, SUBJECT_KB_11)])

    def test_cheat_before_code_asks_for_code(self):
        self.assertEqual(snap(send(self.engine, 5, "give me the answers")), [S(5, CODE_REQUEST)])

    def test_not_cheat_goes_to_lesson_flow(self):
        to_topic(self.engine, 5)
        for t in ("I did my homework", "can you check my answer"):
            out = send(self.engine, 5, t)
            self.assertNotEqual(out[0].text, CHEAT, t)

    def test_cheat_button_precedence(self):
        # a topic button is handled before the cheat check
        to_topic(self.engine, 5)
        out = send(self.engine, 5, "GCSE Higher: trig & geometry")
        self.assertNotEqual(out[0].text, CHEAT)


class TestDeleteMyData(SafetyCase):
    def test_delete_everything_except_unreviewed_safety_flags(self):
        to_topic(self.engine, 5)
        send(self.engine, 5, answer_of(self.store, 5))
        send(self.engine, 5, "I want to die")
        send(self.engine, OWNER, "/stats")
        out = send(self.engine, 5, "/delete_my_data")
        self.assertEqual(snap(out), [S(5, DELETED, None, True)])
        self.assertIsNone(self.store.get_student(5))
        self.assertIsNone(self.store.get_pending(5))
        self.assertEqual(self.store.recent_attempts(5), [])
        self.assertEqual(self.store.levels(5), [])
        self.assertEqual(self.store.llm_calls(5, helpers.day_of(self.clock)), 0)
        # the safeguarding record stays, unchanged, until the owner has reviewed it
        flags = [f for f in self.store.unreviewed_flags() if f.chat_id == 5]
        self.assertEqual([(f.kind, f.text) for f in flags], [("distress", "I want to die")])
        self.assertTrue(send(self.engine, OWNER, "/flags")[0].text.startswith("🚩 1 new flag:"))
        send(self.engine, OWNER, "/flags done")
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM flags WHERE chat_id = 5").fetchone()[0], 0)

    def test_reviewed_flags_are_deleted_with_the_data(self):
        send(self.engine, 5, "I want to die")
        send(self.engine, OWNER, "/flags done")
        send(self.engine, 5, "/delete_my_data")
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM flags WHERE chat_id = 5").fetchone()[0], 0)

    def test_next_message_needs_a_code(self):
        to_topic(self.engine, 5)
        send(self.engine, 5, "/delete_my_data")
        self.assertEqual(snap(send(self.engine, 5, "hello")), [S(5, CODE_REQUEST)])
        self.assertEqual(snap(send(self.engine, 5, "/start")), [S(5, CODE_REQUEST, None, True)])
        code = get_codes(self.engine, 1)[0]
        out = send(self.engine, 5, code)
        self.assertEqual(out[0].text, CODE_OK)

    def test_delete_for_unknown_or_unverified_chat(self):
        out = send(self.engine, 8, "/delete_my_data")
        self.assertEqual(snap(out), [S(8, DELETED, None, True)])
        self.assertIsNone(self.store.get_student(8))

    def test_delete_does_not_touch_other_students(self):
        to_topic(self.engine, 5)
        to_topic(self.engine, 6)
        send(self.engine, 5, "/delete_my_data")
        self.assertIsNotNone(self.store.get_student(6))
        self.assertIsNotNone(self.store.get_pending(6))

    def test_delete_via_bot_suffix(self):
        to_topic(self.engine, 5)
        out = send(self.engine, 5, "/delete_my_data@TutorBot")
        self.assertEqual(out[0].text, DELETED)


class TestFlood(SafetyCase):
    def test_21st_message_is_dropped(self):
        for i in range(20):
            self.assertEqual(len(send(self.engine, 5, "hello")), 1, i)
        self.assertEqual(send(self.engine, 5, "hello"), [])
        self.assertEqual(send(self.engine, 5, "hello"), [])
        self.clock.advance(61)
        self.assertEqual(len(send(self.engine, 5, "hello")), 1)

    def test_other_chats_unaffected(self):
        for _ in range(25):
            send(self.engine, 5, "hello")
        self.assertEqual(len(send(self.engine, 6, "hello")), 1)

    def test_sliding_window(self):
        for _ in range(20):
            send(self.engine, 5, "hello")
        self.clock.advance(30)
        self.assertEqual(send(self.engine, 5, "hello"), [])
        self.clock.advance(31)       # t = 61 since the first burst
        self.assertEqual(len(send(self.engine, 5, "hello")), 1)

    def test_owner_exempt(self):
        for i in range(40):
            self.assertEqual(len(send(self.engine, OWNER, "/stats")), 1, i)

    def test_dropped_messages_have_no_side_effects(self):
        verify(self.engine, 5)
        for _ in range(25):
            send(self.engine, 5, "hello")
        self.assertEqual(send(self.engine, 5, "hello"), [])
        self.assertEqual(self.store.unreviewed_flags(), [])
        self.assertEqual(self.store.recent_attempts(5), [])

    def test_distress_is_never_dropped_by_flood_control(self):
        verify(self.engine, 5)
        for _ in range(25):
            send(self.engine, 5, "hello")
        self.assertEqual(send(self.engine, 5, "hello"), [])          # flooded
        out = send(self.engine, 5, "I want to die")
        self.assertEqual([o.text for o in out if o.chat_id == 5], [DISTRESS])
        self.assertEqual([o.chat_id for o in out if o.chat_id == OWNER], [OWNER])
        self.assertEqual(len(self.store.unreviewed_flags()), 1)
        self.assertEqual(send(self.engine, 5, "hello"), [])          # still flooded for normal messages
        for _ in range(5):
            send(self.engine, 5, "kill my self")
        self.assertEqual(len(self.store.unreviewed_flags()), 6)
        self.assertEqual(self.llm.calls, [])

    def test_distress_from_unverified_flooded_chat(self):
        for _ in range(25):
            send(self.engine, 9, "hello")
        out = send(self.engine, 9, "my dad hits me")
        self.assertEqual([o.text for o in out if o.chat_id == 9], [DISTRESS])
        self.assertIsNone([o for o in out if o.chat_id == 9][0].keyboard)
        self.assertEqual(len(self.store.unreviewed_flags()), 1)

    def test_configurable_limit(self):
        engine, store, clock = make_engine(flood=3)
        self.addCleanup(store.close)
        self.assertEqual([len(send(engine, 5, "hi")) for _ in range(5)], [1, 1, 1, 0, 0])


class TestGroupChats(SafetyCase):
    def test_groups_are_ignored(self):
        for ct in ("group", "supergroup", "channel"):
            with self.subTest(chat_type=ct):
                self.assertEqual(send(self.engine, -100123, "hello", chat_type=ct), [])
                self.assertEqual(send(self.engine, -100123, "/start", chat_type=ct), [])
                self.assertEqual(send(self.engine, -100123, "I want to die", chat_type=ct), [])
        self.assertIsNone(self.store.get_student(-100123))
        self.assertEqual(self.store.unreviewed_flags(), [])

    def test_owner_commands_ignored_in_groups(self):
        self.assertEqual(send(self.engine, OWNER, "/codes 3", chat_type="group"), [])
        self.assertEqual(self.store.count_unused_codes(), 0)

    def test_private_still_works(self):
        self.assertEqual(snap(send(self.engine, 5, "hello", chat_type="private")), [S(5, CODE_REQUEST)])


if __name__ == "__main__":
    unittest.main()
