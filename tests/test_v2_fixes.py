"""docs/ARCHITECTURE_V2.md section 10.2: engine fixes after the critic's fuzzing (12 Nov 2026).

One class per fix: typo tolerance (real words, word by word), the "check" cut, numeric hedging,
lesson commands, rubric skip, generator resilience, DISTRESS curriculum words, lone letters on short
problems, lenient runtime loading, choice correction lines, hex answers, skill titles in «My own topic»,
units of a different quantity and random candidate seeds.
"""
import json
import os
import random
import tempfile
import unittest
from unittest import mock

import helpers
from helpers import ERROR, HINT, NOTE_SPELLING, SKIP, TOPIC_START, UNMARKABLE, make_engine, send, verify
from tutor import texts as T
from tutor.content import (Answer, BankError, Problem, Registry, Skill, Subject, Topic, YearSpec, build_choice,
                           build_short, check, fingerprint, load_registry)
from tutor.content import checker, words
from tutor.content.bank import known_words, lenient, load_bank, load_pack, vocabulary_words
from tutor.content.registry import RegistryError, match_skill_ids
from tutor.intents import exact_intent, intent, is_distress, loose_intent

CH = 1

def short(accept, reject=(), form="any"):
    return Answer("short", accept[0], {"accept": list(accept), "reject": list(reject)}, form=form)


def S(accept, text, reject=(), form="any"):
    return check(short(accept, reject, form), text)


def C(options, correct, text):
    return check(Answer("choice", "x", {"options": list(options), "correct": correct}), text).status


OPTIONS = ["Nucleus", "Mitochondria", "Ribosome", "Cell membrane"]

# pairs of real terms one or two edits apart (critic, 12 Nov 2026): (typed, accept)
REAL_PAIRS = [("refraction", "reflection"), ("carbohydrate", "carbohydrase"), ("translation", "translocation"),
              ("homologous", "homozygous"), ("conjugation", "conjunction"), ("collective", "connective"),
              ("conversation", "conservation"), ("prosumer", "producer"), ("shades", "shapes"), ("bakery", "baker"),
              ("decode", "decide"), ("simile", "simple"), ("agility", "ability"), ("inferior", "interior"),
              ("revolve", "resolve")]
PAIR_WORDS = frozenset(w for pair in REAL_PAIRS for w in pair)


def with_known(words_):
    return mock.patch.object(checker, "_known_words", lambda: frozenset(words_))


# ------------------------------------------------------------------ 1. typo tolerance

class TestTypoRealWords(unittest.TestCase):
    """(a) a typed word that is a real word (global known-word set) is never a typo of a different word."""

    def test_real_word_pairs_are_never_typos(self):
        with with_known(PAIR_WORDS):
            for typed, acc in REAL_PAIRS:
                for t, a in ((typed, acc), (acc, typed)):
                    if len(a) < 6:
                        continue                      # not typo-eligible anyway
                    with self.subTest(typed=t, accept=a):
                        self.assertNotEqual(S([a], t).status, "correct")

    def test_the_known_word_rule_is_what_rejects_one_edit_pairs(self):
        # one substitution: without the known-word set these would be typos
        for typed, acc in (("carbohydrate", "carbohydrase"), ("inferior", "interior"), ("simile", "simple")):
            with self.subTest(typed=typed):
                with with_known(()):
                    self.assertEqual(S([acc], typed).status, "correct")
                with with_known({typed}):
                    self.assertNotEqual(S([acc], typed).status, "correct")

    def test_word_forms_of_the_accept_are_still_typos(self):
        with with_known({"alkanes", "translated", "walls"}):
            v = S(["alkane"], "alkanes")
            self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("alkane")))
            self.assertEqual(S(["translate"], "translated").status, "correct")
            self.assertEqual(S(["cell wall"], "cell walls").status, "correct")      # plural of a short word

    def test_shipped_known_words(self):
        known = known_words()
        for w in ("photosynthesis", "reflection", "refraction", "respiration"):
            self.assertIn(w, known)
        self.assertNotIn("photosinthesis", known)
        self.assertEqual(S(["reflection"], "refraction").status, "wrong")
        v = S(["photosynthesis"], "photosinthesis")
        self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("photosynthesis")))

    def test_vocabulary_words(self):
        got = vocabulary_words({"text": "Mitochondria’s role", "options": ["Café-bar", "x2", "it's"],
                                "feedback": {"Résumé": "ok"}})
        self.assertTrue({"mitochondrias", "role", "café", "cafe", "bar", "its", "résumé", "resume", "ok", "x"} <= got)
        self.assertFalse(any(any(c.isdigit() for c in w) for w in got))

    def test_registry_load_builds_the_set(self):
        with mock.patch("tutor.content.bank._KNOWN_WORDS", None):
            with mock.patch("tutor.content.bank.vocabulary_words", return_value={"zzz"}) as vw:
                from tutor.content import bank
                self.assertIn("zzz", bank.known_words())
                self.assertTrue(vw.called)


class TestTypoWordByWord(unittest.TestCase):
    """(b) multi-word answers: same word count, no negation prefix change, each word within tolerance."""

    def test_negation_prefixes(self):
        with with_known(()):
            for acc, typed in (("relatively elastic", "relatively inelastic"), ("context dependent", "context independent"),
                               ("more reactive", "more unreactive"), ("usual", "unusual"), ("native plants", "nonnative plants"),
                               ("legal drugs", "illegal drugs"), ("organised", "disorganised")):
                with self.subTest(typed=typed):
                    self.assertNotEqual(S([acc], typed).status, "correct")
                    self.assertNotEqual(S([typed], acc).status, "correct")

    def test_no_added_or_removed_words(self):
        with with_known(()):
            self.assertNotEqual(S(["Martin Luther King"], "Martin Luther King Q").status, "correct")
            self.assertNotEqual(S(["Martin Luther King"], "Martin Luther").status, "correct")
            self.assertNotEqual(S(["every day"], "everyday").status, "correct")
            self.assertNotEqual(S(["aerial perspective"], "aerial perspective view").status, "correct")

    def test_each_word_keeps_its_first_letter_and_short_words_are_exact(self):
        with with_known(()):
            self.assertEqual(S(["great fire london"], "grat fire london").status, "correct")
            self.assertNotEqual(S(["great fire london"], "great fire nondon").status, "correct")
            self.assertNotEqual(S(["the iron curtain"], "the iron cyrtain cc").status, "correct")
            self.assertNotEqual(S(["cell wall"], "cell wal").status, "correct")       # "wall" < 5 letters
            v = S(["complementary colours"], "complementary colors")
            self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("complementary colours")))

    def test_total_edits(self):
        with with_known(()):
            self.assertNotEqual(S(["stem cells"], "stam celss").status, "correct")      # 2 edits, accept < 10 chars
            self.assertEqual(S(["complementary colours"], "complimentary colors").status, "correct")    # 2 edits

    def test_typo_distance_function(self):
        self.assertEqual(checker.typo_distance("photosinthesis", "photosynthesis"), 1)
        self.assertIsNone(checker.typo_distance("photosinthesys", "photosynthesis"))
        self.assertEqual(checker.typo_distance("phtosynthesys", "photosynthesis"), 2)
        self.assertIsNone(checker.typo_distance("photosynthesis", "photosynthesis"))
        self.assertIsNone(checker.typo_distance("refraction", "reflection", frozenset({"refraction"})))


class TestTypoSubstitutions(unittest.TestCase):
    """(c) distance 2 only for words of 10+ letters, and never two substitutions."""

    def test_osa_subs(self):
        self.assertEqual(words.osa_subs("photosinthesis", "photosynthesis"), (1, 1))
        self.assertEqual(words.osa_subs("conversation", "conservation"), (2, 2))
        self.assertEqual(words.osa_subs("chrmosomes", "chromosome"), (2, 0))
        self.assertEqual(words.osa_subs("mitochondira", "mitochondria"), (1, 0))
        self.assertEqual(words.osa_subs("", "abc"), (3, 0))

    def test_two_substitutions_rejected(self):
        with with_known(()):
            self.assertNotEqual(S(["conservation"], "conversation").status, "correct")
            self.assertNotEqual(S(["photosynthesis"], "photosinthesys").status, "correct")
            self.assertEqual(S(["chromosome"], "chrmosomes").status, "correct")       # 2 edits, no substitution
            self.assertEqual(S(["mitosis"], "mitoxis").status, "correct")             # 1 substitution
            self.assertNotEqual(S(["mitosis"], "mitoxxs").status, "correct")          # 2 edits, < 10 letters

    def test_acceptance_table_rows_still_pass(self):
        for typed, acc in (("photosinthesis", "photosynthesis"), ("photosynthesys", "photosynthesis"),
                           ("alkaen", "alkane"), ("alkanes", "alkane")):
            with self.subTest(typed=typed):
                v = S([acc], typed, ["alkene"] if acc == "alkane" else ["respiration"])
                self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING(acc)))


# ------------------------------------------------------------------ 2. "check" cut

class TestCheckWordCut(unittest.TestCase):
    ACC = ["format check", "format", "picture check"]
    REJ = ["range check", "length check", "presence check", "type check"]

    def test_check_inside_the_answer_is_not_cut(self):
        for t in ("format check or range check", "format check? no, length check", "format check and range check"):
            with self.subTest(text=t):
                self.assertNotEqual(S(self.ACC, t, self.REJ).status, "correct")
        self.assertEqual(S(["format check"], "format check or range check").status, "unparsed")

    def test_answers_and_working_still_work(self):
        self.assertEqual(S(self.ACC, "format check", self.REJ).status, "correct")
        self.assertEqual(S(self.ACC, "picture check", self.REJ).status, "correct")
        self.assertEqual(S(self.ACC, "range check", self.REJ).status, "wrong")
        self.assertEqual(S(self.ACC, "format check because it checks the pattern", self.REJ).status, "correct")
        self.assertEqual(S(["photosynthesis"], "photosynthesis, check: light is absorbed").status, "correct")
        self.assertEqual(S(["format check"], "format check: it makes sure data follows a pattern").status, "correct")
        self.assertEqual(S(["photosynthesis"], "photosynthesis (checking: it uses light)").status, "correct")


# ------------------------------------------------------------------ 3. numeric hedging

class TestNumericHedging(unittest.TestCase):
    def test_one_or_two_digit_accepts_need_exactly_one_number(self):
        for acc, t in ((["7"], "7 or 8"), (["7"], "8 or 7"), (["7"], " ".join(str(i) for i in range(1, 13))),
                       (["10"], "10½"), (["64"], "64 1/2"), (["35"], "34, 35, 36"), (["10"], "10-11"),
                       (["10"], "10/11"), (["7"], "7 or maybe 9")):
            with self.subTest(text=t):
                self.assertEqual(S(acc, t).status, "wrong")
        for acc, t in ((["7"], "7"), (["7"], "it is 7"), (["64"], "£64"), (["35"], "35%"), (["10"], "10 kJ"),
                       (["42"], "6 × 7 = 42"), (["7"], "about 7")):
            with self.subTest(text=t):
                self.assertEqual(S(acc, t).status, "correct")

    def test_negation_is_unparsed(self):
        for t in ("not 1843", "1843 is wrong", "it isn't 1843", "1843 is incorrect", "never 1843"):
            with self.subTest(text=t):
                self.assertEqual(S(["1843"], t).status, "unparsed")

    def test_years_allow_a_day_next_to_a_month_only(self):
        for t in ("11 November 1918", "November 11, 1918", "11th of November 1918", "on 4 Aug 1918", "1918"):
            with self.subTest(text=t):
                self.assertEqual(S(["1918"], t).status, "correct")
        for t in ("in 1918 after 4 years", "1918 or 1919", "1914-1918", "40 1918"):
            with self.subTest(text=t):
                self.assertEqual(S(["1918"], t).status, "wrong")

    def test_bc_is_not_the_ad_year(self):
        self.assertEqual(S(["79"], "79 BC").status, "wrong")
        self.assertEqual(S(["79"], "79 BCE").status, "wrong")
        self.assertEqual(S(["79"], "AD 79").status, "correct")
        self.assertEqual(S(["79"], "79 AD").status, "correct")

    def test_spaced_binary_still_works(self):
        acc = ["00101101", "0010 1101"]
        self.assertEqual(S(acc, "0010 1101").status, "correct")
        self.assertEqual(S(acc, "00101101").status, "correct")
        self.assertNotEqual(S(acc, "0010 1101 or 0010 1100").status, "correct")
        self.assertEqual(S(["00101101"], "00101101 or 00101100").status, "wrong")


# ------------------------------------------------------------------ 4/5. lesson commands and rubric skip

def command_registry():
    """A choice item whose correct option contains "help", a short item whose accept is "pass" and an
    extended-practice item whose model answer contains "how to", "help" and "give up"."""
    def choice_gen(level, seed):
        text, ans, mist = build_choice("Why did the government start the scheme?",
                                       ["To help first-time buyers get a home", "To raise taxes", "To build roads"],
                                       0, seed)
        return Problem("cmd.choice", level, seed, text, ans, "It helped first-time buyers", "Think about who it was for",
                       mist, ref="cmd.choice#q1")

    def short_gen(level, seed):
        ans, mist = build_short(["pass"], ["dribble"])
        return Problem("cmd.short", level, seed, "What do you call giving the ball to a teammate? Give the term.",
                       ans, "Giving the ball to a teammate is a pass", "It is not a dribble", mist, ref="cmd.short#q1")

    def essay_gen(level, seed):
        model = "People help each other; I would explain how to give up bad habits and how to stay healthy"
        return Problem("cmd.essay", level, seed + 0 * level, f"Explain how to stay healthy ({seed % 3}).",
                       Answer("rubric", model, None, mark_scheme="1 mark per point", max_marks=2),
                       "Healthy habits matter", "Think about habits", ref=f"cmd.essay#e{seed % 3}")

    def num_gen(level, seed):
        r = random.Random(seed)
        a, b = r.randint(10, 49), r.randint(10, 49)
        return Problem("cmd.num", level, seed, f"What is {a} + {b}?", Answer("number", str(a + b), float(a + b)),
                       f"{a} + {b} = {a + b}", "Add the units first")

    skills = [Skill("cmd.choice", "cmd", "Choice", ("choice",), choice_gen),
              Skill("cmd.short", "cmd", "Short", ("short",), short_gen),
              Skill("cmd.essay", "cmd", "Essay", ("essay",), essay_gen),
              Skill("cmd.num", "cmd", "Numbers", ("numbers",), num_gen)]
    rows = ((Topic("cmd.y11.choice", "Choice", ("cmd.choice",)), Topic("cmd.y11.short", "Short", ("cmd.short",))),
            (Topic("cmd.y11.essay", "Essay", ("cmd.essay",)), Topic("cmd.y11.essay_num", "Essay or numbers",
                                                                     ("cmd.essay", "cmd.num"))))
    reg = Registry()
    reg.register(Subject("cmd", "Cmd", 1, {11: YearSpec(rows=rows)}), skills)
    return reg


class CmdCase(unittest.TestCase):
    def setUp(self):
        self.engine, self.store, self.clock = make_engine(registry=command_registry(), flood=100000)
        self.addCleanup(self.store.close)

    def go(self, label):
        verify(self.engine, CH)
        send(self.engine, CH, "Cmd")
        return send(self.engine, CH, label)


class TestLessonCommands(CmdCase):
    def test_option_text_with_help_is_marked_not_a_hint(self):
        self.go("Choice")
        out = send(self.engine, CH, "To help first-time buyers get a home")
        self.assertTrue(out[0].text.startswith("✅ Correct!"), out[0].text)

    def test_short_accept_that_is_a_command_word_is_marked(self):
        self.go("Short")
        out = send(self.engine, CH, "pass")
        self.assertTrue(out[0].text.startswith("✅ Correct!"), out[0].text)

    def test_whole_message_commands_still_work_on_wrong_answers(self):
        self.go("Short")
        p = self.store.get_pending(CH)
        out = send(self.engine, CH, "can I have a hint please")
        self.assertEqual(out[0].text, HINT(p.problem.hint))
        out = send(self.engine, CH, "skip")
        self.assertEqual(out[0].text, SKIP(p.problem.solution, p.problem.answer.display))

    def test_phrase_inside_an_answer_counts_only_when_unparsed(self):
        self.go("Short")
        p = self.store.get_pending(CH)
        out = send(self.engine, CH, "I really need help with this one because I am stuck")
        self.assertEqual(out[0].text, HINT(p.problem.hint))            # long text: no answer found -> command
        out = send(self.engine, CH, "dribble help")                   # an answer (a reject) -> marked wrong
        self.assertTrue(out[0].text.startswith("❌ Not quite."), out[0].text)

    def test_rubric_takes_only_whole_message_commands(self):
        self.go("Essay")
        p = self.store.get_pending(CH)
        out = send(self.engine, CH, p.problem.answer.display)        # contains "help", "how to", "give up"
        self.assertEqual(out[0].text, UNMARKABLE(p.problem.answer.display))
        q = self.store.get_pending(CH)
        out = send(self.engine, CH, "I don't know how to start this, help")
        self.assertEqual(out[0].text, UNMARKABLE(q.problem.answer.display))
        r = self.store.get_pending(CH)
        out = send(self.engine, CH, "hint")
        self.assertEqual(out[0].text, HINT(r.problem.hint))

    def test_exact_and_loose_intents(self):
        for t, want in (("can I have a hint please", "hint"), ("hint pls", "hint"), ("I need help", "hint"),
                        ("skip please", "skip"), ("what is the answer", "skip"), ("Skip this one!", "skip"),
                        ("I'm not sure.", "skip")):
            with self.subTest(text=t):
                self.assertEqual(exact_intent(t), want)
                self.assertEqual(intent(t), want)
        for t in ("the government should help people", "how to make glucose", "they give up territory"):
            with self.subTest(text=t):
                self.assertIsNone(exact_intent(t))
                self.assertIsNotNone(loose_intent(t))


class TestRubricSkip(CmdCase):
    def test_skip_on_extended_practice_records_nothing(self):
        verify(self.engine, CH)
        send(self.engine, CH, "Cmd")
        self.store.set_level(CH, "cmd", "cmd.y11.essay", 4)
        send(self.engine, CH, "Essay")                     # starts one level lower: 3
        p = self.store.get_pending(CH)
        self.assertEqual(p.level, 3)
        out = send(self.engine, CH, "skip")
        self.assertEqual(out[0].text, SKIP(p.problem.solution, p.problem.answer.display))
        self.assertEqual(self.store.recent_attempts(CH), [])
        self.assertEqual(self.store.get_level(CH, "cmd", "cmd.y11.essay"), 3)
        q = self.store.get_pending(CH)
        self.assertEqual((q.level, q.problem_no), (3, p.problem_no + 1))

    def test_skip_on_a_marked_problem_still_records(self):
        self.go("Short")
        send(self.engine, CH, "skip")
        self.assertEqual([a.skipped for a in self.store.recent_attempts(CH)], [True])


# ------------------------------------------------------------------ 6. generator resilience

def flaky_registry(fail):
    """Topic "Flaky" = skills flaky.a (raises when fail(seed) is true) and flaky.b (always works)."""
    def gen_a(level, seed):
        if fail(seed):
            raise ZeroDivisionError("bad seed")
        return Problem("flaky.a", level, seed, f"A: what is {seed % 97} + 1?",
                       Answer("number", str(seed % 97 + 1), float(seed % 97 + 1)), "add one", "count on")

    def gen_b(level, seed):
        return Problem("flaky.b", level, seed, f"B: what is {seed % 89} + 2?",
                       Answer("number", str(seed % 89 + 2), float(seed % 89 + 2)), "add two", "count on")

    skills = [Skill("flaky.a", "flaky", "A", ("aaa",), gen_a), Skill("flaky.b", "flaky", "B", ("bbb",), gen_b)]
    rows = ((Topic("flaky.y11.both", "Flaky", ("flaky.a", "flaky.b")), Topic("flaky.y11.a", "Only A", ("flaky.a",))),)
    reg = Registry()
    reg.register(Subject("flaky", "Flaky", 1, {11: YearSpec(rows=rows)}), skills)
    return reg


class TestGeneratorResilience(unittest.TestCase):
    def start(self, fail, label):
        self.engine, self.store, _ = make_engine(registry=flaky_registry(fail), flood=100000)
        self.addCleanup(self.store.close)
        verify(self.engine, CH)
        send(self.engine, CH, "Flaky")
        return send(self.engine, CH, label)

    def test_some_seeds_raise(self):
        with self.assertLogs("tutor.engine", level="ERROR"):
            for _ in range(5):
                out = self.start(lambda seed: seed % 2 == 1, "Only A")
                self.assertEqual(out[0].text, TOPIC_START("Only A"))
                p = self.store.get_pending(CH)
                self.assertEqual((p.skill, p.seed % 2), ("flaky.a", 0))

    def test_a_skill_that_always_raises_falls_back_to_another_skill(self):
        with self.assertLogs("tutor.engine", level="ERROR"):
            for _ in range(6):
                out = self.start(lambda seed: True, "Flaky")
                self.assertNotIn(ERROR, [o.text for o in out])
                p = self.store.get_pending(CH)
                self.assertEqual(p.skill, "flaky.b")
                self.assertEqual(self.store.recent_seen(CH, "flaky.b"), [fingerprint(p.problem)])
                out = send(self.engine, CH, p.problem.answer.display)     # the lesson goes on
                self.assertTrue(out[0].text.startswith("✅"))
                self.assertEqual(self.store.get_pending(CH).skill, "flaky.b")

    def test_error_only_when_nothing_works(self):
        with self.assertLogs("tutor.engine", level="ERROR"):
            out = self.start(lambda seed: True, "Only A")
        self.assertEqual([o.text for o in out], [ERROR])


# ------------------------------------------------------------------ 7. DISTRESS on curriculum words

class TestDistressCurriculumWords(unittest.TestCase):
    def test_curriculum_answers_are_not_distress(self):
        for t in ("not safe", "unsafe", "danger zone", "the danger zone", "food left in the danger zone is unsafe",
                  "it is not safe to eat", "unsafe working practices", "Unsafe", "in danger of extinction",
                  "Keep food out of the danger zone (5-63 °C)", "food in danger zone"):
            with self.subTest(text=t):
                self.assertFalse(is_distress(t))

    def test_personal_forms_are_distress(self):
        for t in ("i'm not safe", "I am not safe", "i don't feel safe", "I dont feel safe at all", "not safe at home",
                  "i feel unsafe", "im unsafe", "it isn't safe at home", "i am in danger", "my mum is in danger",
                  "it's not safe for me", "suicide", "I want to die"):
            with self.subTest(text=t):
                self.assertTrue(is_distress(t))

    def test_flag_names_the_open_problem(self):
        engine, store, _ = make_engine(registry=command_registry(), flood=100000)
        self.addCleanup(store.close)
        verify(engine, CH)
        send(engine, CH, "Cmd")
        send(engine, CH, "Short")
        out = send(engine, CH, "suicide")
        owner = [o for o in out if o.chat_id == 999][0]
        self.assertEqual(owner.text, helpers.FLAG_ALERT("distress", "Zorblax", CH, "suicide", "cmd.short#q1"))
        self.assertEqual(store.unreviewed_flags()[0].text, "[open problem: cmd.short#q1] suicide")
        listing = send(engine, 999, "/flags")[0].text
        self.assertIn("[open problem: cmd.short#q1] suicide", listing)

    def test_flag_without_open_problem_is_unchanged(self):
        engine, store, _ = make_engine(registry=command_registry(), flood=100000)
        self.addCleanup(store.close)
        out = send(engine, CH, "i want to die")
        owner = [o for o in out if o.chat_id == 999][0]
        self.assertEqual(owner.text, helpers.FLAG_ALERT("distress", "Zorblax", CH, "i want to die"))
        self.assertEqual(store.unreviewed_flags()[0].text, "i want to die")


# ------------------------------------------------------------------ 8. lone letters on short problems

class TestLoneLetterOnShort(unittest.TestCase):
    def test_letter_is_unparsed(self):
        for t in ("B", "b", "(c)", "D.", "a)", "E"):
            with self.subTest(text=t):
                self.assertEqual(S(["photosynthesis"], t).status, "unparsed")
        self.assertEqual(S(["7"], "B").status, "unparsed")

    def test_letter_that_is_an_accept_or_reject(self):
        self.assertEqual(S(["A", "blood group A"], "A").status, "correct")
        self.assertEqual(S(["AB"], "B", ["B"]).status, "wrong")
        v = S(["C"], "c", form="case")                      # a symbol: the capital-letter feedback, not unparsed
        self.assertEqual((v.status, v.feedback), ("wrong", checker.FORM_CASE))
        self.assertEqual(S(["C"], "C", form="case").status, "correct")

    def test_engine_reply(self):
        engine, store, _ = make_engine(registry=command_registry(), flood=100000)
        self.addCleanup(store.close)
        verify(engine, CH)
        send(engine, CH, "Cmd")
        send(engine, CH, "Short")
        out = send(engine, CH, "B")
        self.assertEqual(out[0].text, T.SHORT_UNPARSED)
        self.assertEqual(store.recent_attempts(CH), [])


# ------------------------------------------------------------------ 9. lenient runtime loading

def bank_with_broken_question():
    good = [{"id": f"q{i}", "level": 1 + i % 5, "text": f"Which number comes after {i}? Choose one.",
             "choice": {"options": [str(i + 1), str(i + 2), str(i + 3)], "correct": 0},
             "solution": f"{i + 1} comes after {i}", "hint": "Count on by one"} for i in range(1, 6)]
    broken = {"id": "bad", "level": 2, "text": "Name the green pigment in leaves.",
              "short": {"accept": ["chlorophyll"]}, "solution": "It is chlorophyll",
              "hint": "It is called chlorophyll"}                              # the hint gives the answer away
    lost = {"id": "lost", "title": "Lost skill", "aliases": ["lost"],
            "questions": [{"id": "x1", "level": 1, "text": "Broken?", "choice": {"options": ["A1"], "correct": 0},
                           "solution": "s", "hint": "h"}]}
    return {"subject": {"id": "lenient", "title": "Lenient", "order": 99},
            "skills": [{"id": "lenient.numbers", "title": "Numbers", "aliases": ["numbers"],
                        "questions": good[:3] + [broken] + good[3:]}, lost],
            "years": {"11": {"rows": [[{"id": "lenient.y11.n", "label": "Numbers",
                                        "skills": ["lenient.numbers", "lenient.lost"]},
                                       {"id": "lenient.y11.l", "label": "Lost only", "skills": ["lenient.lost"]}]]}}}


class TestLenientLoading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, data, name):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_bank_keeps_the_working_questions(self):
        path = self.write(bank_with_broken_question(), "lenient.json")
        with self.assertRaises(BankError):
            load_bank(path)                                       # strict: unchanged
        errors = []
        with self.assertLogs("tutor.content", level="WARNING"):
            with lenient(errors):
                subject, skills = load_bank(path)
        self.assertEqual([s.id for s in skills], ["lenient.numbers"])
        self.assertEqual(len(skills[0].items), 5)
        self.assertTrue(any("questions[3].hint" in e for e in errors), errors)
        self.assertTrue(all(e.startswith("lenient.json: skipped ") for e in errors), errors)
        topics = [t for row in subject.years[11].rows for t in row]
        self.assertEqual([(t.label, t.skills) for t in topics], [("Numbers", ("lenient.numbers",))])
        with self.assertRaises(BankError):
            load_bank(path)                                       # the lenient result is never served strictly

    def test_registry_non_strict_records_and_keeps_the_subject(self):
        path = self.write(bank_with_broken_question(), "lenient.json")
        with self.assertRaises(BankError):
            load_registry(banks=[path])
        with self.assertLogs("tutor.content", level="WARNING"):
            reg = load_registry(banks=[path], strict=False)
        self.assertIn("lenient", [s.id for s in reg.subjects_for_year(11)])
        self.assertEqual(len(reg.skill("lenient.numbers").items), 5)
        mine = [e for e in reg.load_errors if "lenient.json" in e]
        self.assertTrue(mine and all(e.startswith("subject source lenient.json: ") for e in mine), mine)

    def test_pack(self):
        data = {"subject_id": "lenient", "skills": bank_with_broken_question()["skills"]}
        path = self.write(data, "pack.json")
        with self.assertRaises(BankError):
            load_pack(path, "lenient")
        errors = []
        with self.assertLogs("tutor.content", level="WARNING"):
            with lenient(errors):
                skills = load_pack(path, "lenient")
        self.assertEqual([(s.id, len(s.items)) for s in skills], [("lenient.numbers", 5)])
        self.assertTrue(errors)

    def test_registry_drops_missing_skills_from_module_topics(self):
        def gen(level, seed):
            return Problem("mod.a", level, seed, "1 + 1?", Answer("number", "2", 2.0), "2", "add")
        rows = ((Topic("mod.y11.t", "Both", ("mod.a", "mod.gone")), Topic("mod.y11.u", "Gone", ("mod.gone",))),)
        subject = Subject("mod", "Mod", 5, {11: YearSpec(rows=rows)})
        skills = [Skill("mod.a", "mod", "A", ("aaa",), gen)]
        with self.assertRaises(RegistryError):
            Registry().register(subject, skills)
        reg = Registry()
        reg.lenient = True
        with self.assertLogs("tutor.content", level="WARNING"):
            reg.register(subject, skills)
        self.assertEqual(reg.topic_rows("mod", 11), [("Both",)])
        self.assertEqual(reg.topic("mod.y11.t").skills, ("mod.a",))
        self.assertEqual(len(reg.load_errors), 2)


# ------------------------------------------------------------------ 10. choice correction lines

class TestChoiceCorrections(unittest.TestCase):
    def test_correction_names_a_second_letter(self):
        for t in ("A\nsorry I meant B", "A\nsorry, B", "A\noops B", "A\nno wait, B", "A\nwait C", "A\nI meant B",
                  "A\ni mean B"):
            with self.subTest(text=t):
                self.assertEqual(C(OPTIONS, 1, t), "unparsed")
        self.assertEqual(C(OPTIONS, 1, "sorry I meant B"), "correct")
        self.assertEqual(C(OPTIONS, 1, "B\nsorry I meant B"), "correct")

    def test_trailing_certainty_words(self):
        for t in ("B I think", "B is correct", "B is the answer", "B definitely", "B 100%", "b, i guess",
                  "B for sure", "B is right", "B is the correct answer", "B probably"):
            with self.subTest(text=t):
                self.assertEqual(C(OPTIONS, 1, t), "correct")
                self.assertEqual(C(OPTIONS, 2, t), "wrong")

    def test_article_plus_option_is_that_option(self):
        nums = ["100", "50", "25", "75"]
        self.assertEqual(C(nums, 0, "A 100%"), "correct")      # the letter A, not "a 100"
        self.assertEqual(C(nums, 1, "A 100%"), "wrong")
        temps = ["0 °C", "−18 °C or below", "10 °C", "5 °C"]
        self.assertEqual(C(temps, 1, "a −18 °C or below"), "correct")
        self.assertEqual(C(temps, 0, "a −18 °C or below"), "wrong")
        opts = ["I wanted to swim, but the pool was closed.", "Because the pool was closed, I went home.", "It rained."]
        self.assertEqual(C(opts, 0, "a Because the pool was closed, I went home."), "wrong")
        self.assertEqual(C(opts, 1, "a Because the pool was closed, I went home."), "correct")
        q = ["Asking customers", "Inspecting at the end", "Checking quality at every stage so faults are prevented"]
        self.assertEqual(C(q, 2, "a Checking quality at every stage so faults are prevented"), "correct")


# ------------------------------------------------------------------ 11. hexadecimal

class TestHexAnswers(unittest.TestCase):
    def test_hex_notations(self):
        for t in ("A2", "a2", "0xA2", "0xa2", "A2h", "a2H", "A2 hex", "A2 in hex", "A2 hexadecimal", "it's A2"):
            with self.subTest(text=t):
                self.assertEqual(S(["A2"], t).status, "correct")
        for t in ("A3", "0xA3", "2A", "2Ah"):
            with self.subTest(text=t):
                self.assertEqual(S(["A2"], t, ["2A"]).status, "wrong")

    def test_digit_only_hex(self):
        for t in ("27", "0x27", "27h", "27 hex"):
            with self.subTest(text=t):
                self.assertEqual(S(["27"], t).status, "correct")
        self.assertEqual(S(["27"], "0x72").status, "wrong")

    def test_words_are_not_hex(self):
        self.assertEqual(S(["face"], "0xface").status, "wrong")


# ------------------------------------------------------------------ 12. skill titles in «My own topic»

class TestTitleMatching(unittest.TestCase):
    def test_every_shipped_title_finds_its_skill(self):
        reg = helpers.shared_registry()
        for y in (10, 11):
            for subj in reg.subjects_for_year(y):
                for sk in reg.skills_of(subj.id):
                    for t in (sk.title, sk.title.lower(), sk.title.upper(), sk.title.replace("&", "and"),
                              f"I want to practise {sk.title}"):
                        with self.subTest(text=t):
                            self.assertEqual(reg.match_skills(subj.id, t)[:1], [sk.id])

    def test_title_words_in_any_order(self):
        def gen(level, seed):
            raise AssertionError
        skills = [Skill("e.reading", "e", "Reading & structure", ("inference",), gen),
                  Skill("e.writing", "e", "Writing skills", ("persuasive",), gen),
                  Skill("e.power", "e", "Power", ("power",), gen),
                  Skill("e.epower", "e", "Electrical power", ("electrical power",), gen),
                  Skill("e.tri", "e", "Area of a triangle", ("sine rule area",), gen)]
        self.assertEqual(match_skill_ids(skills, "structure and reading"), ["e.reading"])
        self.assertEqual(match_skill_ids(skills, "my writing skills"), ["e.writing"])
        self.assertEqual(match_skill_ids(skills, "electrical power")[0], "e.epower")       # longest match first
        self.assertEqual(match_skill_ids(skills, "longest side of right triangles"), [])    # one word is not enough
        self.assertEqual(match_skill_ids(skills, "triangle area"), ["e.tri"])


# ------------------------------------------------------------------ 13. units of a different quantity

class TestUnitsOfAnotherQuantity(unittest.TestCase):
    def num(self, display, value, text):
        return check(Answer("number", display, float(value)), text)

    def test_unknown_display_unit(self):
        self.assertEqual(self.num("15 L/min", 15, "15 cm"), checker.Verdict("wrong", checker.FORM_UNIT.format(unit="L/min")))
        self.assertEqual(self.num("15 L/min", 15, "15 l").status, "wrong")
        for t in ("15", "15 L/min", "15 l/min", "15 litres per minute", "it is 15 L/min"):
            with self.subTest(text=t):
                self.assertEqual(self.num("15 L/min", 15, t).status, "correct")
        v = self.num("0.8 cm³/s", 0.8, "0.8 cm³")
        self.assertEqual((v.status, v.feedback), ("wrong", checker.FORM_UNIT.format(unit="cm³/s")))

    def test_celsius(self):
        self.assertEqual(self.num("75 °C", 75, "75 cm"), checker.Verdict("wrong", checker.FORM_UNIT.format(unit="°C")))
        for t in ("75", "75 °C", "75°C", "75 degrees", "75 C", "75 deg", "75 celsius"):
            with self.subTest(text=t):
                self.assertEqual(self.num("75 °C", 75, t).status, "correct")
        self.assertEqual(self.num("67°", 67, "67°C").status, "wrong")

    def test_known_units_unchanged(self):
        self.assertEqual(self.num("3.5 m", 3.5, "350 cm").status, "correct")
        self.assertEqual(self.num("3.5 m", 3.5, "3.5 s"), checker.Verdict("wrong", checker.FORM_UNIT.format(unit="m")))
        self.assertEqual(self.num("20 cm²", 20, "20 cm").feedback, checker.FORM_UNIT.format(unit="cm²"))


# ------------------------------------------------------------------ 14. random candidate seeds

class TestRandomCandidateSeeds(unittest.TestCase):
    def test_candidates_are_not_consecutive(self):
        seen_seeds = []

        def gen(level, seed):
            seen_seeds.append(seed)
            return Problem("r.a", level, seed, f"Q{seed % 3}", Answer("number", "1", 1.0), "s", "h", ref=f"r.a#q{seed % 3}")

        skill = Skill("r.a", "r", "R", ("r",), gen)
        engine, store, _ = make_engine(registry=helpers.demo_registry(), flood=100000)
        self.addCleanup(store.close)
        for k in range(3):
            store.add_seen(CH, "r.a", f"r.a#q{k}")             # everything seen: every candidate is tried
        engine._choose(CH, skill, 1, None)
        self.assertEqual(len(seen_seeds), 40)
        steps = {b - a for a, b in zip(seen_seeds, seen_seeds[1:])}
        self.assertNotEqual(steps, {1})
        self.assertGreater(len(set(s % 7 for s in seen_seeds)), 3)

    def test_bank_items_are_not_walked_in_file_order(self):
        """Ten items, five already seen: the next item is any unseen one, not the one after the seen run."""
        def make(i):
            return lambda seed: Problem("r.b", 1, seed, f"Q{i}", Answer("number", "1", 1.0), "s", "h", ref=f"r.b#q{i}")

        from tutor.content import BankItem
        items = tuple(BankItem(f"r.b#q{i}", 1, "number", make(i)) for i in range(10))

        def gen(level, seed):
            return items[seed % 10].render(seed)

        skill = Skill("r.b", "r", "R", ("r",), gen, items)
        firsts = set()
        for rng_seed in range(30):
            engine, store, _ = make_engine(registry=helpers.demo_registry(), flood=100000)
            engine.rng = random.Random(rng_seed)
            for i in range(5):
                store.add_seen(CH, "r.b", f"r.b#q{i}")
            _, p = engine._choose(CH, skill, 1, None)
            self.assertNotIn(p.ref, {f"r.b#q{i}" for i in range(5)})
            firsts.add(p.ref)
            store.close()
        self.assertGreaterEqual(len(firsts), 4)          # the old walk almost always gave r.b#q5


if __name__ == "__main__":
    unittest.main()
