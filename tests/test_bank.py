import copy
import json
import os
import tempfile
import unittest

import helpers
from tutor.content import (BankError, Registry, check, load_bank, load_registry, register_bank,
                           problem_from_json, problem_to_json)

SAMPLE = os.path.join(helpers.FIXTURES, "bank_sample.json")
INVALID = os.path.join(helpers.FIXTURES, "bank_invalid.json")


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
        self.assertEqual([s.title for s in reg.subjects_for_year(10)], ["Maths", "Physics", "Test Subject"])
        self.assertEqual([s.title for s in reg.subjects_for_year(11)], ["Maths", "Physics"])
        self.assertIsNotNone(reg.skill("testsubj.adding"))
        self.assertIsNotNone(reg.skill("maths.pythagoras"))
        self.assertEqual([s.title for s in load_registry().subjects_for_year(10)], ["Maths", "Physics"])   # not auto-loaded

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


if __name__ == "__main__":
    unittest.main()
