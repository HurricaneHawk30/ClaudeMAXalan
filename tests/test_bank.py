import copy
import json
import os
import tempfile
import unittest

import helpers
from unittest import mock

from tutor.content import (BankError, Registry, check, load_bank, load_registry, register_bank,
                           problem_from_json, problem_to_json, load_pack, BankItem, fingerprint, shuffle_order,
                           CHOICE_LETTERS)
from helpers import NOTE_SPELLING
from tutor.content import bank as bank_mod

SAMPLE = os.path.join(helpers.FIXTURES, "bank_sample.json")
INVALID = os.path.join(helpers.FIXTURES, "bank_invalid.json")
SAMPLE2 = os.path.join(helpers.FIXTURES, "bank_v2_sample.json")
PACK = os.path.join(helpers.FIXTURES, "pack_sample.json")
INVALID_DIR = os.path.join(helpers.FIXTURES, "bank_v2_invalid")


def sample_dict():
    with open(SAMPLE, encoding="utf-8") as f:
        return json.load(f)


class TestBank(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, data, name="b.json"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    # ------------------------------------------------------------ loading
    def test_load_fixture(self):
        subject, skills = load_bank(SAMPLE)
        self.assertEqual((subject.id, subject.title, subject.order), ("testsubj", "Test Subject", 99))
        self.assertEqual([s.id for s in skills], ["testsubj.adding", "testsubj.algebra", "testsubj.writing"])
        self.assertEqual(skills[0].title, "Adding")
        self.assertEqual(skills[0].aliases, ("adding", "addition"))
        self.assertEqual(skills[0].subject, "testsubj")
        self.assertEqual(list(subject.years), [10])
        spec = subject.years[10]
        self.assertEqual([[t.label for t in row] for row in spec.rows], [["Basics"], ["Words"]])
        self.assertEqual(spec.rows[0][0].id, "testsubj.y10.basics")
        self.assertEqual(spec.rows[0][0].skills, ("testsubj.adding", "testsubj.algebra"))
        self.assertEqual(tuple(spec.rows[0][0].level_map), (1, 2, 3, 4, 5))
        self.assertEqual(tuple(spec.rows[1][0].level_map), (1, 2, 3, 4, 5))    # optional key -> default
        self.assertEqual(tuple(spec.past_paper_level_map), (1, 1, 1, 1, 1))

    def test_generation_deterministic_and_well_formed(self):
        _, skills = load_bank(SAMPLE)
        adding = skills[0]
        for level in range(1, 6):
            for seed in range(30):
                p = adding.generate(level, seed)
                self.assertEqual(p, adding.generate(level, seed))
                self.assertEqual((p.skill_id, p.level, p.seed), ("testsubj.adding", level, seed))
                self.assertEqual(problem_from_json(problem_to_json(p)), p)
                self.assertEqual(check(p.answer, p.answer.display).status, "correct")
                self.assertNotIn(p.answer.display, p.hint)

    def test_level_selection_nearest_prefers_lower(self):
        _, skills = load_bank(SAMPLE)
        adding = skills[0]
        lvl1 = {"What is 2 + 3?", "What is 4 + 4?"}
        for seed in range(40):
            self.assertIn(adding.generate(1, seed).text, lvl1)
            self.assertEqual(adding.generate(3, seed).text, "What is 17 + 26?")
            self.assertIn(adding.generate(2, seed).text, lvl1)                       # tie 1 vs 3 -> lower
            self.assertEqual(adding.generate(4, seed).text, "What is 17 + 26?")      # nearest is 3
            self.assertEqual(adding.generate(5, seed).text, "What is 17 + 26?")
        self.assertEqual(adding.generate(2, 0).level, 2)        # Problem carries the requested level
        self.assertEqual(adding.generate(5, 7).level, 5)

    def test_choice_varies_with_seed(self):
        _, skills = load_bank(SAMPLE)
        seen = {skills[0].generate(1, s).text for s in range(60)}
        self.assertEqual(seen, {"What is 2 + 3?", "What is 4 + 4?"})

    def test_mistakes_loaded(self):
        _, skills = load_bank(SAMPLE)
        for seed in range(40):
            p = skills[0].generate(1, seed)
            if p.text == "What is 2 + 3?":
                self.assertEqual(len(p.mistakes), 1)
                self.assertEqual(p.mistakes[0].feedback, "Count again carefully")
                self.assertEqual(p.mistakes[0].answer.display, "6")
                v = check(p.answer, "6", p.mistakes)
                self.assertEqual((v.status, v.feedback), ("wrong", "Count again carefully"))
                break
        else:
            self.fail("question with mistakes never selected")
        p = skills[0].generate(3, 0)
        self.assertEqual(p.mistakes, ())

    def test_answer_keys_expr_and_rubric(self):
        _, skills = load_bank(SAMPLE)
        p = skills[1].generate(2, 1)
        self.assertEqual((p.answer.kind, p.answer.form, p.answer.var), ("expr", "expanded", "x"))
        self.assertEqual(check(p.answer, "x^2+5x+6").status, "correct")
        self.assertEqual(check(p.answer, "(x+2)(x+3)").feedback,
                         "That's equivalent, but the question asks you to expand — multiply out all the brackets")
        r = skills[2].generate(5, 1)
        self.assertEqual((r.answer.kind, r.answer.max_marks), ("rubric", 2))
        self.assertTrue(r.answer.mark_scheme)
        self.assertEqual(check(r.answer, "whatever").status, "unmarkable")

    # ------------------------------------------------------------ registering
    def test_register_into_fresh_registry(self):
        reg = Registry()
        register_bank(reg, SAMPLE)
        self.assertEqual([s.title for s in reg.subjects_for_year(10)], ["Test Subject"])
        self.assertEqual(reg.subjects_for_year(11), [])
        self.assertEqual(reg.years(), [10])
        self.assertEqual(reg.topic_rows("testsubj", 10), [("Basics",), ("Words",)])
        self.assertEqual(reg.match_skills("testsubj", "some addition please"), ["testsubj.adding"])
        self.assertTrue(reg.topic_by_label("testsubj", 10, "Past paper practice").exam)
        self.assertEqual(reg.topic_by_label("testsubj", 10, "past paper practice").level_map, (1, 1, 1, 1, 1))

    def test_register_alongside_builtin_subjects(self):
        reg = load_registry([SAMPLE])
        # v2: shipped banks are auto-loaded; extra banks come last (order 99)
        self.assertEqual([s.title for s in reg.subjects_for_year(10)], helpers.SUBJECT_TITLES_10_11 + ["Test Subject"])
        self.assertEqual([s.title for s in reg.subjects_for_year(11)], helpers.SUBJECT_TITLES_10_11)
        self.assertIsNotNone(reg.skill("testsubj.adding"))
        self.assertIsNotNone(reg.skill("maths.pythagoras"))
        self.assertEqual([s.title for s in load_registry().subjects_for_year(10)], helpers.SUBJECT_TITLES_10_11)

    def test_register_same_bank_twice_fails(self):
        reg = Registry()
        register_bank(reg, SAMPLE)
        with self.assertRaises(Exception):
            register_bank(reg, SAMPLE)

    # ------------------------------------------------------------ validation
    def test_invalid_fixture(self):
        with self.assertRaises(BankError) as cm:
            load_bank(INVALID)
        msg = str(cm.exception)
        self.assertIn("level", msg)
        with self.assertRaises(BankError):
            register_bank(Registry(), INVALID)

    def test_bank_error_is_value_error(self):
        self.assertTrue(issubclass(BankError, ValueError))

    def test_wrong_display_rejected(self):
        d = sample_dict()
        d["skills"][0]["questions"][0]["answer"]["display"] = "7"      # value is 5
        with self.assertRaises(BankError) as cm:
            load_bank(self.write(d))
        self.assertIn("skills", str(cm.exception))

    def test_wrong_display_other_kinds_rejected(self):
        d = sample_dict()
        d["skills"][1]["questions"][0]["answer"]["display"] = "x² + 6x + 5"
        with self.assertRaises(BankError):
            load_bank(self.write(d))
        d = sample_dict()
        d["skills"][0]["questions"][0]["answer"] = {"kind": "set", "display": "1, 2", "value": ["2", "-3"]}
        with self.assertRaises(BankError):
            load_bank(self.write(d))

    def test_level_bounds(self):
        for lvl, ok in ((0, False), (6, False), (-1, False), (1, True), (5, True)):
            with self.subTest(level=lvl):
                d = sample_dict()
                d["skills"][0]["questions"][2]["level"] = lvl
                if ok:
                    load_bank(self.write(d))
                else:
                    with self.assertRaises(BankError):
                        load_bank(self.write(d))

    def test_unknown_kind(self):
        d = sample_dict()
        d["skills"][0]["questions"][0]["answer"]["kind"] = "essay"
        with self.assertRaises(BankError):
            load_bank(self.write(d))

    def test_skill_without_questions(self):
        d = sample_dict()
        d["skills"][0]["questions"] = []
        with self.assertRaises(BankError):
            load_bank(self.write(d))
        d = sample_dict()
        del d["skills"][0]["questions"]
        with self.assertRaises(BankError):
            load_bank(self.write(d))

    def test_missing_fields(self):
        paths = [
            ("subject", lambda d: d.pop("subject")),
            ("skills", lambda d: d.pop("skills")),
            ("subject.id", lambda d: d["subject"].pop("id")),
            ("subject.title", lambda d: d["subject"].pop("title")),
            ("skill.id", lambda d: d["skills"][0].pop("id")),
            ("skill.title", lambda d: d["skills"][0].pop("title")),
            ("q.text", lambda d: d["skills"][0]["questions"][0].pop("text")),
            ("q.answer", lambda d: d["skills"][0]["questions"][0].pop("answer")),
            ("q.level", lambda d: d["skills"][0]["questions"][0].pop("level")),
            ("q.solution", lambda d: d["skills"][0]["questions"][0].pop("solution")),
            ("q.hint", lambda d: d["skills"][0]["questions"][0].pop("hint")),
            ("answer.kind", lambda d: d["skills"][0]["questions"][0]["answer"].pop("kind")),
            ("answer.display", lambda d: d["skills"][0]["questions"][0]["answer"].pop("display")),
        ]
        for name, mutate in paths:
            with self.subTest(missing=name):
                d = copy.deepcopy(sample_dict())
                mutate(d)
                with self.assertRaises(BankError):
                    load_bank(self.write(d))

    def test_rubric_display_not_judged(self):
        d = sample_dict()
        d["skills"][2]["questions"][0]["answer"]["display"] = "Anything at all"
        load_bank(self.write(d))     # rubric answers are never checked


def write_json(tmp, data, name="b.json"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return path


def sample2():
    with open(SAMPLE2, encoding="utf-8") as f:
        return json.load(f)


class TestBankV2(unittest.TestCase):
    """docs/ARCHITECTURE_V2.md section 2.4."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.subject, self.skills = load_bank(SAMPLE2)
        self.mixed = self.skills[0]
        self.levels = self.skills[1]

    def write(self, data, name="b.json"):
        return write_json(self.tmp.name, data, name)

    def item(self, ref):
        return next(i for sk in self.skills for i in sk.items if i.ref == ref)

    # ------------------------------------------------------------ structure
    def test_subject_years_and_topic_ids(self):
        self.assertEqual((self.subject.id, self.subject.title, self.subject.order), ("v2sample", "V2 Sample", 98))
        self.assertEqual(sorted(self.subject.years), [10, 11])
        for y in (10, 11):
            row = self.subject.years[y].rows[0]
            self.assertEqual([(t.id, t.label, t.skills) for t in row],
                             [(f"v2sample.y{y}.mixed", "Mixed kinds", ("v2sample.mixed",)),
                              (f"v2sample.y{y}.levels", "Levels", ("v2sample.levels",))])

    def test_items_refs_levels_kinds(self):
        self.assertEqual([(i.ref, i.level, i.kind) for i in self.mixed.items],
                         [("v2sample.mixed#m01", 1, "choice"), ("v2sample.mixed#m02", 2, "short"),
                          ("v2sample.mixed#m03", 3, "number"), ("v2sample.mixed#m04", 4, "short"),
                          ("v2sample.mixed#m05", 5, "rubric")])
        self.assertTrue(all(isinstance(i, BankItem) for i in self.mixed.items))
        self.assertIsInstance(self.mixed.items, tuple)
        self.assertEqual([i.ref for i in self.levels.items],
                         [f"v2sample.levels#{x}" for x in ("a1", "a2", "a3", "b1", "b2", "c1")])

    def test_render_matches_generate_and_carries_ref(self):
        for it in self.mixed.items:
            for seed in range(6):
                p = it.render(seed)
                self.assertEqual((p.skill_id, p.level, p.seed, p.ref), ("v2sample.mixed", it.level, seed, it.ref))
                self.assertEqual(p, it.render(seed))
                self.assertEqual(problem_from_json(problem_to_json(p)), p)
                q = self.mixed.generate(it.level, seed)
                self.assertEqual(q.level, it.level)

    def test_generator_skills_have_no_items(self):
        reg = load_registry()
        self.assertEqual(reg.skill("maths.pythagoras").items, ())

    def test_ref_without_id_uses_index(self):
        _, skills = load_bank(SAMPLE)
        refs = [i.ref for i in skills[0].items]
        self.assertEqual(len(set(refs)), 3)
        self.assertTrue(all(r.startswith("testsubj.adding#") for r in refs))

    # ------------------------------------------------------------ rendering
    def test_topic_note_prefix(self):
        p = self.item("v2sample.mixed#m01").render(0)
        self.assertTrue(p.text.startswith("[Cells] Which organelle releases energy by respiration?"), p.text)
        self.assertNotIn("[", self.item("v2sample.mixed#m02").render(0).text)

    def test_choice_rendering(self):
        it = self.item("v2sample.mixed#m01")
        options = ["Nucleus", "Mitochondria", "Ribosome", "Cell membrane"]
        for seed in range(15):
            p = it.render(seed)
            order = shuffle_order(4, seed)
            shown = [options[i] for i in order]
            self.assertEqual(p.text, "[Cells] Which organelle releases energy by respiration?\n\n"
                             + "\n".join(f"{CHOICE_LETTERS[i]}) {o}" for i, o in enumerate(shown)))
            self.assertEqual(p.answer.kind, "choice")
            self.assertEqual(p.answer.value, {"options": shown, "correct": shown.index("Mitochondria")})
            self.assertEqual(p.answer.display, f"{CHOICE_LETTERS[shown.index('Mitochondria')]}) Mitochondria")
            self.assertEqual(sorted(m.feedback for m in p.mistakes),
                             ["The membrane controls what enters the cell", "The nucleus stores the DNA"])

    def test_trailing_periods_stripped(self):
        p = self.item("v2sample.mixed#m01").render(0)
        self.assertEqual(p.solution, "Mitochondria release energy by respiration")
        self.assertEqual(p.hint, "Think about where respiration happens")
        p = self.item("v2sample.mixed#m02").render(0)
        self.assertEqual(p.solution, "Plants make glucose by photosynthesis")
        self.assertEqual([m.feedback for m in p.mistakes], ["Respiration releases energy rather than storing it"])
        self.assertEqual(p.mistakes[0].answer.display, "respiration")

    def test_short_rendering_and_checking(self):
        p = self.item("v2sample.mixed#m02").render(3)
        self.assertEqual((p.answer.kind, p.answer.display, p.answer.form), ("short", "photosynthesis", "any"))
        self.assertEqual(check(p.answer, "photosynthesis", p.mistakes).status, "correct")
        v = check(p.answer, "respiration", p.mistakes)
        self.assertEqual((v.status, v.feedback), ("wrong", "Respiration releases energy rather than storing it"))
        v = check(p.answer, "photosynthesys", p.mistakes)
        self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("photosynthesis")))
        p = self.item("v2sample.mixed#m04").render(0)
        self.assertEqual(p.answer.form, "case")
        self.assertEqual(check(p.answer, "co2").feedback, helpers.FORM_CASE)

    def test_number_answer_with_mistake(self):
        p = self.item("v2sample.mixed#m03").render(0)
        self.assertEqual((p.answer.kind, p.answer.display), ("number", "12"))
        v = check(p.answer, "11", p.mistakes)
        self.assertEqual((v.status, v.feedback), ("wrong", "Count again carefully"))

    def test_rubric_rendering(self):
        p = self.item("v2sample.mixed#m05").render(0)
        self.assertEqual((p.answer.kind, p.answer.max_marks), ("rubric", 2))
        self.assertEqual(p.answer.display, "Air molecules scatter short wavelength blue light more than red light.")
        self.assertEqual(p.answer.mark_scheme, "1 mark: scattering. 1 mark: blue scatters most.")

    # ------------------------------------------------------------ selection
    def test_selection_is_seed_modulo_n(self):
        for seed in range(14):
            self.assertEqual(self.levels.generate(1, seed).ref, f"v2sample.levels#a{seed % 3 + 1}")
            self.assertEqual(self.levels.generate(3, seed).ref, f"v2sample.levels#b{seed % 2 + 1}")
            self.assertEqual(self.levels.generate(5, seed).ref, "v2sample.levels#c1")

    def test_nearest_level_ties_prefer_lower(self):
        for seed in range(6):
            self.assertEqual(self.levels.generate(2, seed).ref, f"v2sample.levels#a{seed % 3 + 1}")       # 1 vs 3 -> 1
            self.assertEqual(self.levels.generate(4, seed).ref, f"v2sample.levels#b{seed % 2 + 1}")       # 3 vs 5 -> 3
        self.assertEqual([self.levels.generate(lv, 0).level for lv in range(1, 6)], [1, 2, 3, 4, 5])

    def test_consecutive_seeds_cover_the_level(self):
        refs = {self.levels.generate(1, s).ref for s in range(5, 8)}
        self.assertEqual(len(refs), 3)

    def test_negative_and_big_seeds_do_not_crash(self):
        for seed in (0, 2 ** 31 - 1, 10 ** 12):
            self.assertTrue(self.levels.generate(1, seed).ref)

    # ------------------------------------------------------------ cache
    def test_cache_returns_same_objects(self):
        s1, k1 = load_bank(SAMPLE2)
        s2, k2 = load_bank(SAMPLE2)
        self.assertIs(s1, s2)
        self.assertEqual(len(k1), len(k2))
        for a, b in zip(k1, k2):
            self.assertIs(a, b)

    def test_cache_invalidated_when_file_changes(self):
        d = sample2()
        path = self.write(d)
        a, _ = load_bank(path)
        d["subject"]["title"] = "V2 Sample Changed"
        path = self.write(d)
        b, _ = load_bank(path)
        self.assertEqual((a.title, b.title), ("V2 Sample", "V2 Sample Changed"))

    # ------------------------------------------------------------ cleaning
    def test_aliases_lowercased(self):
        d = sample2()
        d["skills"][0]["aliases"] = ["Mixed Kinds", "MIXED", "Kinds"]
        _, skills = load_bank(self.write(d))
        self.assertEqual(skills[0].aliases, ("mixed kinds", "mixed", "kinds"))

    # ------------------------------------------------------------ registry
    def test_register_v2_bank_year_keys(self):
        reg = Registry()
        register_bank(reg, SAMPLE2)
        self.assertEqual(reg.years(), [10, 11])
        self.assertEqual(reg.topic_rows("v2sample", 11), [("Mixed kinds", "Levels")])
        self.assertEqual(reg.topic("v2sample.y10.levels").label, "Levels")
        self.assertEqual(reg.match_skills("v2sample", "mixed kinds"), ["v2sample.mixed"])

    # ------------------------------------------------------------ packs
    def test_load_pack(self):
        skills = load_pack(PACK, "packsub")
        self.assertEqual([s.id for s in skills], ["packsub.facts"])
        self.assertEqual([i.ref for i in skills[0].items], ["packsub.facts#p01", "packsub.facts#p02"])
        self.assertEqual(skills[0].subject, "packsub")
        p = skills[0].generate(1, 0)
        self.assertEqual(p.answer.kind, "choice")
        self.assertEqual(p.ref, "packsub.facts#p01")
        self.assertIs(load_pack(PACK, "packsub")[0], skills[0])             # cached

    def test_load_pack_by_name_uses_packs_dir(self):
        with open(PACK, encoding="utf-8") as f:
            data = json.load(f)
        write_json(self.tmp.name, data, "packsub.json")
        with mock.patch.object(bank_mod, "PACKS_DIR", self.tmp.name):
            skills = load_pack("packsub", "packsub")
        self.assertEqual([s.id for s in skills], ["packsub.facts"])

    def test_packs_and_banks_dirs_exist(self):
        self.assertTrue(bank_mod.BANKS_DIR.replace("\\", "/").endswith("tutor/subjects/banks"))
        self.assertTrue(bank_mod.PACKS_DIR.replace("\\", "/").endswith("tutor/subjects/packs"))

    def test_pack_errors(self):
        with open(PACK, encoding="utf-8") as f:
            data = json.load(f)
        with self.assertRaises(BankError):
            load_pack(PACK, "othersub")                                      # subject_id mismatch
        bad = json.loads(json.dumps(data))
        bad["skills"][0]["id"] = "other.facts"
        with self.assertRaises(BankError):
            load_pack(self.write(bad, "p1.json"), "packsub")                 # id prefix
        bad = json.loads(json.dumps(data))
        bad["skills"][0]["questions"][0]["choice"]["correct"] = 9
        with self.assertRaises(BankError):
            load_pack(self.write(bad, "p2.json"), "packsub")
        bad = json.loads(json.dumps(data))
        bad["colour"] = 1
        with self.assertRaises(BankError):
            load_pack(self.write(bad, "p3.json"), "packsub")

    # ------------------------------------------------------------ validation
    def test_invalid_fixtures_one_case_per_file(self):
        names = sorted(f for f in os.listdir(INVALID_DIR) if f.endswith(".json") and not f.startswith("_"))
        want = ["accept_reject_overlap", "all_of_the_above", "bad_form", "choice_via_answer_key", "correct_out_of_range",
                "duplicate_id", "duplicate_options", "duplicate_stem", "empty_accept", "feedback_on_correct", "hint_leaks",
                "lone_letter_option", "rubric_no_model", "text_too_long", "two_options", "unknown_key"]
        self.assertEqual([n[:-5] for n in names], want)
        load_bank(os.path.join(INVALID_DIR, "_control_valid.json"))        # the base of every case is valid
        hints = {"two_options": ("option",), "correct_out_of_range": ("correct",), "duplicate_options": ("option",),
                 "all_of_the_above": ("option",), "lone_letter_option": ("option",), "feedback_on_correct": ("feedback",),
                 "empty_accept": ("accept",), "accept_reject_overlap": ("reject", "accept"), "unknown_key": ("colour",),
                 "duplicate_id": ("id",), "duplicate_stem": ("text", "stem", "questions"), "text_too_long": ("text",),
                 "hint_leaks": ("hint",), "bad_form": ("form",), "rubric_no_model": ("model_answer", "rubric"),
                 "choice_via_answer_key": ("answer", "choice")}
        for n in want:
            with self.subTest(case=n):
                with self.assertRaises(BankError) as cm:
                    load_bank(os.path.join(INVALID_DIR, n + ".json"))
                msg = str(cm.exception)
                self.assertIn("skills", msg)                                  # JSON path
                self.assertTrue(any(h in msg for h in hints[n]), msg)

    def mutate(self, fn, name="m.json"):
        d = sample2()
        fn(d)
        return self.write(d, name)

    def assertInvalid(self, fn, label):
        with self.subTest(case=label):
            with self.assertRaises(BankError):
                load_bank(self.mutate(fn, f"{abs(hash(label))}.json"))

    def test_unknown_keys_at_every_level(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        cases = {
            "subject": lambda d: d["subject"].update(bogus=1),
            "skill": lambda d: d["skills"][0].update(bogus=1),
            "question": lambda d: q(d)[0].update(bogus=1),
            "choice": lambda d: q(d)[0]["choice"].update(bogus=1),
            "short": lambda d: q(d)[1]["short"].update(bogus=1),
            "rubric": lambda d: q(d)[4]["rubric"].update(bogus=1),
            "year": lambda d: d["years"]["10,11"].update(bogus=1),
            "topic": lambda d: d["years"]["10,11"]["rows"][0][0].update(bogus=1),
            "top level": lambda d: d.update(bogus=1),
        }
        for label, fn in cases.items():
            self.assertInvalid(fn, "unknown key in " + label)

    def test_question_needs_exactly_one_answer_key(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        self.assertInvalid(lambda d: q(d)[1].update(choice=q(d)[0]["choice"]), "short + choice")
        self.assertInvalid(lambda d: q(d)[1].pop("short"), "none")
        self.assertInvalid(lambda d: q(d)[1].update(rubric=q(d)[4]["rubric"]), "short + rubric")
        self.assertInvalid(lambda d: q(d)[1].update(answer=q(d)[2]["answer"]), "short + answer")
        self.assertInvalid(lambda d: q(d)[2]["answer"].update(kind="short"), "answer.kind short")
        self.assertInvalid(lambda d: q(d)[2]["answer"].update(kind="choice"), "answer.kind choice")

    def test_id_rules(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        for bad in ("", "has space", "x" * 25, "a/b", "ü", "a.b", None, 5):
            self.assertInvalid(lambda d, b=bad: q(d)[0].update(id=b), f"id {bad!r}")
        for ok in ("a", "A_b-9", "x" * 24):
            with self.subTest(id=ok):
                d = sample2()
                q(d)[0]["id"] = ok
                load_bank(self.write(d, f"ok_{len(ok)}.json"))

    def test_level_must_be_int_1_to_5(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        for bad in (0, 6, -1, "1", 1.5, None):
            self.assertInvalid(lambda d, b=bad: q(d)[0].update(level=b), f"level {bad!r}")

    def test_text_solution_hint_rules(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        for key in ("text", "solution", "hint"):
            self.assertInvalid(lambda d, k=key: q(d)[0].update({k: ""}), f"empty {key}")
            self.assertInvalid(lambda d, k=key: q(d)[0].pop(k), f"missing {key}")
        self.assertInvalid(lambda d: q(d)[0].update(solution="x" * 301), "solution 301")
        d = sample2()
        q(d)[0]["solution"] = "x" * 300
        load_bank(self.write(d, "sol300.json"))
        self.assertInvalid(lambda d: q(d)[0].update(topic_note="x" * 41), "topic_note 41")
        self.assertInvalid(lambda d: q(d)[0].update(topic_note="two\nlines"), "topic_note newline")
        d = sample2()
        q(d)[0]["topic_note"] = "x" * 40
        load_bank(self.write(d, "note40.json"))

    def test_rendered_text_limit_600_includes_note_and_options(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        d = sample2()
        stem = "Which organelle releases energy by respiration? "
        q(d)[0]["text"] = stem + "y" * (600 - len(stem) - len("[Cells] ") - 2 - 4 * 3 - len("Nucleus") - len("Mitochondria")
                                         - len("Ribosome") - len("Cell membrane") - 3 - 2)
        load_bank(self.write(d, "t_ok.json"))                              # still within 600 once options are added
        q(d)[0]["text"] = "z" * 580
        with self.assertRaises(BankError):
            load_bank(self.write(d, "t_long.json"))                        # 580 + note + options > 600

    def test_duplicate_stems_ignore_case_punctuation_and_topic_note(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        def fn(d):
            q(d)[1]["text"] = "  WHICH  organelle releases energy by respiration!!  "
            q(d)[1]["short"] = {"accept": ["mitochondria"]}
            q(d)[1]["hint"] = "Think about respiration"
            q(d)[1]["topic_note"] = "Other note"
        self.assertInvalid(fn, "dup stem")

    def test_skill_rules(self):
        sk = lambda d: d["skills"][0]            # noqa: E731
        self.assertInvalid(lambda d: sk(d).update(questions=[]), "no questions")
        self.assertInvalid(lambda d: sk(d).update(title=""), "empty title")
        self.assertInvalid(lambda d: sk(d).update(aliases=[]), "no aliases")
        self.assertInvalid(lambda d: sk(d).update(aliases=["ok", ""]), "empty alias")
        self.assertInvalid(lambda d: sk(d).pop("aliases"), "missing aliases")

    def test_choice_rules(self):
        c = lambda d: d["skills"][0]["questions"][0]["choice"]            # noqa: E731
        self.assertInvalid(lambda d: c(d).update(options=["a1", "b2"], feedback=None), "2 options")
        self.assertInvalid(lambda d: c(d).update(options=[f"o{i}" for i in range(6)], correct=0, feedback=None), "6 options")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "x" * 121), "option 121")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, ""), "empty option")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "two\nlines"), "option newline")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "Mitochondria "), "dup after normalisation")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "None of these"), "none of these")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "Neither of the above"), "neither of the above")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "B or C"), "B or C")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "A & B"), "A & B")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "(a)"), "(a)")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "b"), "b")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "C. Ribosome"), "C. prefix")
        self.assertInvalid(lambda d: c(d)["options"].__setitem__(0, "B) Nucleus"), "B) prefix")
        self.assertInvalid(lambda d: c(d).update(correct="1"), "correct str")
        self.assertInvalid(lambda d: c(d).update(correct=-1), "correct -1")
        self.assertInvalid(lambda d: c(d).update(feedback=[None, None, None]), "feedback length")
        self.assertInvalid(lambda d: c(d).update(feedback=["", None, None, None]), "feedback empty entry")
        self.assertInvalid(lambda d: c(d).update(feedback=[None, "x", None, None]), "feedback on correct")
        # allowed: a group name and a word that merely contains letters
        d = sample2()
        c(d)["options"][0] = "Group A"
        c(d)["options"][2] = "Allosaurus of the above era"
        load_bank(self.write(d, "ok_opts.json"))

    def test_short_rules(self):
        sh = lambda d: d["skills"][0]["questions"][1]["short"]            # noqa: E731
        self.assertInvalid(lambda d: sh(d).update(accept=[]), "empty accept")
        self.assertInvalid(lambda d: sh(d).update(accept=[""]), "blank accept")
        self.assertInvalid(lambda d: sh(d).update(accept=["!!!"]), "accept empty after normalisation")
        self.assertInvalid(lambda d: sh(d).update(accept=["x" * 81]), "accept 81")
        self.assertInvalid(lambda d: sh(d).update(reject=["Photosynthesis"]), "reject = accept")
        self.assertInvalid(lambda d: sh(d).update(reject=["the photosynthesis"]), "reject = accept after article strip")
        self.assertInvalid(lambda d: sh(d).update(form="fuzzy"), "bad form")
        self.assertInvalid(lambda d: sh(d).update(feedback={"digestion": "x"}), "feedback key not in reject")
        self.assertInvalid(lambda d: sh(d).update(feedback={"respiration": ""}), "empty feedback")
        self.assertInvalid(lambda d: sh(d).update(accept="photosynthesis"), "accept not a list")
        for f in ("any", "strict", "case", "pinyin"):
            d = sample2()
            sh(d)["form"] = f
            if f in ("case",):
                sh(d)["reject"] = []
                sh(d)["feedback"] = {}
            sh(d)["accept"] = ["photosynthesis"] if f != "pinyin" else ["guang he zuo yong"]
            load_bank(self.write(d, f"form_{f}.json"))

    def test_short_accept_reject_folded_overlap_for_strict(self):
        d = sample2()
        sh = d["skills"][0]["questions"][1]["short"]
        sh.update(form="strict", accept=["la bibliothèque"], reject=["la bibliotheque"], feedback={})
        with self.assertRaises(BankError):
            load_bank(self.write(d, "fold_overlap.json"))

    def test_rubric_rules(self):
        r = lambda d: d["skills"][0]["questions"][4]["rubric"]            # noqa: E731
        self.assertInvalid(lambda d: r(d).pop("model_answer"), "no model answer")
        self.assertInvalid(lambda d: r(d).pop("mark_scheme"), "no mark scheme")
        self.assertInvalid(lambda d: r(d).pop("max_marks"), "no max marks")
        self.assertInvalid(lambda d: r(d).update(model_answer=""), "empty model")
        self.assertInvalid(lambda d: r(d).update(model_answer="m" * 601), "model 601")
        self.assertInvalid(lambda d: r(d).update(mark_scheme="m" * 601), "scheme 601")
        self.assertInvalid(lambda d: r(d).update(max_marks=0), "marks 0")
        self.assertInvalid(lambda d: r(d).update(max_marks=13), "marks 13")
        self.assertInvalid(lambda d: r(d).update(max_marks="2"), "marks str")
        for ok in (1, 12):
            d = sample2()
            r(d)["max_marks"] = ok
            load_bank(self.write(d, f"marks{ok}.json"))
        d = sample2()
        r(d)["model_answer"] = "m" * 600
        load_bank(self.write(d, "model600.json"))

    def test_hint_must_not_leak(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        self.assertInvalid(lambda d: q(d)[1].update(hint="It is photosynthesis, silly"), "accept in hint")
        self.assertInvalid(lambda d: q(d)[1].update(hint="It is PHOTOSYNTHESIS"), "accept in hint upper")
        self.assertInvalid(lambda d: q(d)[0].update(hint="Try mitochondria"), "option in hint")
        self.assertInvalid(lambda d: q(d)[3].update(hint="It is CO2"), "display (>=3 chars) in hint")
        d = sample2()
        q(d)[1]["hint"] = "Think of photosynthesise or photosynthesising"          # whole words only
        load_bank(self.write(d, "hint_ok.json"))
        d = sample2()
        q(d)[1]["short"]["accept"] = ["O2"]                                     # < 3 chars: allowed in the hint
        q(d)[1]["hint"] = "It is a gas made of two atoms and written O2"
        q(d)[1]["short"].pop("reject"); q(d)[1]["short"].pop("feedback")
        load_bank(self.write(d, "hint_short_ok.json"))

    def test_answer_rules_v1(self):
        q = lambda d: d["skills"][0]["questions"]            # noqa: E731
        self.assertInvalid(lambda d: q(d)[2]["answer"].update(display="13"), "display not correct")
        d = sample2()
        q(d)[2]["mistakes"] = [{"answer": {"kind": "number", "display": "12", "value": 12}, "feedback": "same as answer"},
                               {"answer": {"kind": "number", "display": "11", "value": 11}, "feedback": "Count again carefully"}]
        _, sk = load_bank(self.write(d, "mistake_same.json"))
        p = sk[0].items[2].render(0)
        self.assertEqual([m.feedback for m in p.mistakes], ["Count again carefully"])        # coinciding mistake dropped

    def test_auto_rejects(self):
        d = {"subject": {"id": "autosub", "title": "Auto Sub", "order": 95},
             "skills": [{"id": "autosub.x", "title": "Auto X", "aliases": ["auto x", "autos", "xs"], "questions": [
                 {"id": "a1", "level": 1, "text": "Name the hydrocarbon family with only single bonds. Give the term.",
                  "short": {"accept": ["alkane"]}, "solution": "Alkanes are saturated", "hint": "The name ends in ane"},
                 {"id": "a2", "level": 1, "text": "Which family has a C=C double bond?",
                  "choice": {"options": ["alkene", "alcohol", "ester"], "correct": 0},
                  "solution": "Alkenes have a C=C bond", "hint": "The name ends in ene"},
                 {"id": "a3", "level": 1, "text": "Name the family with a carbon to carbon triple bond. Give the term.",
                  "short": {"accept": ["alkyne"]}, "solution": "Alkynes have a triple bond", "hint": "The name ends in yne"},
                 {"id": "a4", "level": 1, "text": "Name the plural form of the single bond family. Give the word.",
                  "short": {"accept": ["alkanes"]}, "solution": "Plural of alkane", "hint": "Add an s"},
                 {"id": "a5", "level": 1, "text": "Name the compound with formula CH4. Give the name.",
                  "short": {"accept": ["methane"]}, "solution": "CH4 is methane", "hint": "It is the first member of the family"},
                 {"id": "a6", "level": 1, "text": "What is the symbol for sodium chloride? Give the formula.",
                  "short": {"accept": ["NaCl"], "form": "case"}, "solution": "Sodium chloride is NaCl", "hint": "Two symbols"},
                 {"id": "a7", "level": 1, "text": "Name the strict family. Give the word.",
                  "short": {"accept": ["alkane"], "form": "strict"}, "solution": "Alkane", "hint": "The name ends in ane"},
             ]}],
             "years": {"10": {"rows": [[{"id": "autosub.y10.t", "label": "Auto topic", "skills": ["autosub.x"]}]]}}}
        _, sk = load_bank(self.write(d, "auto.json"))
        by = {i.ref.split("#")[1]: i for i in sk[0].items}
        rej = lambda k: by[k].render(0).answer.value["reject"]            # noqa: E731
        self.assertIn("alkene", rej("a1"))
        self.assertIn("alkyne", rej("a1"))
        self.assertNotIn("alkanes", rej("a1"))                              # plural variant of an accept
        self.assertNotIn("alkane", rej("a1"))
        self.assertNotIn("methane", rej("a1"))                              # different first letter
        self.assertNotIn("alcohol", rej("a1"))                              # distance > 2
        self.assertLessEqual(len(rej("a1")), 20)
        p = by["a1"].render(0)
        self.assertEqual(check(p.answer, "alkene", p.mistakes).status, "wrong")
        v = check(p.answer, "alkanes", p.mistakes)
        self.assertEqual((v.status, v.feedback), ("correct", NOTE_SPELLING("alkane")))
        self.assertEqual(check(p.answer, "alkane", p.mistakes).feedback, "")
        self.assertEqual(rej("a6"), [])                                     # form case: no auto-rejects
        self.assertEqual(rej("a7"), [])                                     # form strict: none
        self.assertEqual(rej("a5"), [])                                     # nothing near "methane"

    def test_auto_rejects_cap_at_twenty(self):
        words = [f"alkan{c}{d}" for c in "abcdefghij" for d in "xyz"]          # many near terms, all within distance 2
        qs = [{"id": "t0", "level": 1, "text": "Name the first family. Give the term.", "short": {"accept": ["alkane"]},
               "solution": "Alkane", "hint": "Ends in ane"}]
        for i, w in enumerate(words):
            qs.append({"id": f"t{i + 1}", "level": 1, "text": f"Name family number {i + 1}. Give the term.",
                       "short": {"accept": [w]}, "solution": "Term", "hint": "Think"})
        d = {"subject": {"id": "capsub", "title": "Cap Sub", "order": 94},
             "skills": [{"id": "capsub.x", "title": "Cap X", "aliases": ["cap x", "caps", "cx"], "questions": qs}],
             "years": {"10": {"rows": [[{"id": "capsub.y10.t", "label": "Cap topic", "skills": ["capsub.x"]}]]}}}
        _, sk = load_bank(self.write(d, "cap.json"))
        rej = sk[0].items[0].render(0).answer.value["reject"]
        self.assertGreater(len(rej), 0)
        self.assertLessEqual(len(rej), 20)


if __name__ == "__main__":
    unittest.main()
