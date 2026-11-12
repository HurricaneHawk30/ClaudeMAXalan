import json
import os
import tempfile
import time
import unittest

import helpers
import spec
from tutor.content import (Answer, Problem, Registry, RegistryError, Skill, Subject, Topic, YearSpec,
                           load_registry, PAST_PAPER_LABEL, MY_OWN_TOPIC_LABEL)

M = "maths."
HA = ["linear_equations", "expand_brackets", "factorise_quadratics", "solve_quadratics", "simultaneous", "nth_term"]
HT = ["pythagoras", "trig_sides", "trig_angles", "sine_rule", "triangle_area_sine", "arcs_sectors"]
FN = ["percentages", "fractions", "ratio", "hcf_lcm", "standard_form"]
FG = ["area_perimeter", "angles", "pythagoras", "circles", "trig_sides"]


def ids(names, prefix=M):
    return tuple(prefix + n for n in names)


KS3_LEVEL_MAP = {7: (1, 1, 2, 2, 3), 8: (1, 2, 2, 3, 3), 9: (1, 2, 3, 3, 4)}
KS3_PAST_MAP = {7: (1, 2, 2, 3, 3), 8: (1, 2, 3, 3, 4), 9: (2, 2, 3, 4, 4)}


def dummy_problem(sid):
    def gen(level, seed):
        return Problem(sid, level, seed, "What is 1 + 1?", Answer("number", "2", 2.0), "1 + 1 = 2", "Count on")
    return gen


def sk(sid, aliases=(), subject=None, title=None):
    sub = subject or sid.split(".")[0]
    return Skill(sid, sub, title or sid.split(".")[1].title(), tuple(aliases), dummy_problem(sid))


def topic(tid, label, skills, **kw):
    return Topic(tid, label, tuple(skills), **kw)


def one_subject(rows, skills=None, sid="s", year=10, order=1):
    skills = skills if skills is not None else [sk("s.a"), sk("s.b")]
    reg = Registry()
    reg.register(Subject(sid, sid.title(), order, {year: YearSpec(rows=rows)}), skills)
    return reg


class TestLoaded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = load_registry()

    def test_years(self):
        self.assertEqual(self.reg.years(), [7, 8, 9, 10, 11])

    def test_subjects_for_year(self):
        titles = lambda y: [s.title for s in self.reg.subjects_for_year(y)]  # noqa: E731
        for y in (7, 8, 9):
            self.assertEqual(titles(y), ["Maths"], y)
        for y in (10, 11):
            self.assertEqual(titles(y), helpers.SUBJECT_TITLES_10_11, y)          # section 4, in order
        for y in (1, 6, 12, 13, 0, -1, 99):
            self.assertEqual(self.reg.subjects_for_year(y), [], y)

    def test_subject_lookup(self):
        m = self.reg.subject("maths")
        self.assertEqual((m.id, m.title, m.order), ("maths", "Maths", 10))
        p = self.reg.subject("physics")
        self.assertEqual((p.id, p.title, p.order), ("physics", "Physics", 20))
        self.assertIsNone(self.reg.subject("english"))
        self.assertEqual(self.reg.subject("english_literature").title, "English Literature")
        self.assertEqual(sorted(self.reg.subject("physics").years), [10, 11])
        self.assertEqual(len(helpers.SUBJECT_TITLES_10_11), 35)
        self.assertEqual([s.order for s in self.reg.subjects_for_year(11)],
                         [x["order"] for x in spec.SUBJECTS])
        self.assertEqual([s.id for s in self.reg.subjects_for_year(10)], [x["id"] for x in spec.SUBJECTS])

    def test_topic_rows_maths(self):
        for y in (10, 11):
            self.assertEqual(self.reg.topic_rows("maths", y),
                             [("GCSE Higher: algebra & functions", "GCSE Higher: trig & geometry"),
                              ("GCSE Foundation: number", "GCSE Foundation: geometry")])
        for y in (7, 8, 9):
            self.assertEqual(self.reg.topic_rows("maths", y),
                             [("KS3: number & fractions", "KS3: algebra"),
                              ("KS3: geometry", "KS3: ratio & percentages")])

    def test_topic_rows_physics(self):
        for y in (10, 11):
            self.assertEqual(self.reg.topic_rows("physics", y),
                             [("Forces & motion", "Energy"), ("Electricity", "Density & pressure")])

    def test_topic_rows_of_every_new_subject(self):
        fails = []
        for s in spec.SUBJECTS:
            if s["rows"] is None:
                continue
            want = [tuple(lbl for lbl, _, _ in row) for row in s["rows"]]
            for y in (10, 11):
                got = self.reg.topic_rows(s["id"], y)
                if got != want:
                    fails.append(f"[{s['owner']}] {s['id']} Y{y}: {got} != {want}")
            for y in (7, 8, 9, 12, 13):
                if self.reg.topic_rows(s["id"], y):
                    fails.append(f"[{s['owner']}] {s['id']} Y{y}: must have no topics")
        self.assertEqual(fails, [], "\n".join(fails[:10]))

    def test_new_subject_past_paper_topics(self):
        fails = []
        for s in spec.SUBJECTS:
            if s["rows"] is None:
                continue
            for y in (10, 11):
                t = self.reg.topic_by_label(s["id"], y, PAST_PAPER_LABEL)
                if t is None or not t.exam or t.id != f"{s['id']}.y{y}.past_paper" or t.level_map != (2, 3, 3, 4, 5):
                    fails.append(f"[{s['owner']}] {s['id']} Y{y}: {t}")
        self.assertEqual(fails, [], "\n".join(fails[:10]))

    def test_physics_absent_for_years_7_to_9_and_unknown_gives_empty(self):
        for y in (7, 8, 9, 12, 13, 5):
            self.assertEqual(self.reg.topic_rows("physics", y), [], y)
        self.assertEqual(self.reg.topic_rows("english", 11), [])
        self.assertEqual(self.reg.topic_rows("maths", 12), [])

    def test_year_10_11_maths_topics(self):
        for y in (10, 11):
            t = self.reg.topic_by_label("maths", y, "GCSE Higher: algebra & functions")
            self.assertEqual((t.id, t.skills, t.level_map, t.exam), (f"maths.y{y}.higher_algebra", ids(HA), (1, 2, 3, 4, 5), False))
            t = self.reg.topic_by_label("maths", y, "GCSE Higher: trig & geometry")
            self.assertEqual((t.id, t.skills, t.level_map), (f"maths.y{y}.higher_trig", ids(HT), (1, 2, 3, 4, 5)))
            t = self.reg.topic_by_label("maths", y, "GCSE Foundation: number")
            self.assertEqual((t.id, t.skills, t.level_map), (f"maths.y{y}.foundation_number", ids(FN), (1, 2, 3, 3, 4)))
            t = self.reg.topic_by_label("maths", y, "GCSE Foundation: geometry")
            self.assertEqual((t.id, t.skills, t.level_map), (f"maths.y{y}.foundation_geometry", ids(FG), (1, 2, 3, 3, 4)))

    def test_ks3_topics(self):
        for y in (7, 8, 9):
            num = self.reg.topic_by_label("maths", y, "KS3: number & fractions")
            alg = self.reg.topic_by_label("maths", y, "KS3: algebra")
            geo = self.reg.topic_by_label("maths", y, "KS3: geometry")
            rat = self.reg.topic_by_label("maths", y, "KS3: ratio & percentages")
            self.assertEqual((num.id, alg.id, geo.id, rat.id),
                             tuple(f"maths.y{y}.{s}" for s in ("ks3_number", "ks3_algebra", "ks3_geometry", "ks3_ratio")))
            for t in (num, alg, geo, rat):
                self.assertEqual(t.level_map, KS3_LEVEL_MAP[y], (y, t.id))
                self.assertFalse(t.exam)
            self.assertEqual(set(num.skills), set(ids(["fractions", "hcf_lcm"] + (["standard_form"] if y == 9 else []))))
            self.assertEqual(set(alg.skills), set(ids(["linear_equations", "nth_term"] + (["expand_brackets"] if y == 9 else []))))
            geo_expected = ["angles", "area_perimeter"] + (["circles"] if y >= 8 else []) + (["pythagoras"] if y == 9 else [])
            self.assertEqual(set(geo.skills), set(ids(geo_expected)))
            self.assertEqual(set(rat.skills), set(ids(["percentages", "ratio"])))

    def test_physics_topics(self):
        exp = {"forces": ["speed", "acceleration", "force", "weight"], "energy": ["kinetic_energy", "gpe", "power"],
               "electricity": ["ohms_law", "electrical_power", "charge"], "density_pressure": ["density", "pressure"]}
        labels = {"forces": "Forces & motion", "energy": "Energy", "electricity": "Electricity",
                  "density_pressure": "Density & pressure"}
        for y in (10, 11):
            for slug, names in exp.items():
                t = self.reg.topic_by_label("physics", y, labels[slug])
                self.assertEqual((t.id, t.skills, t.level_map), (f"physics.y{y}.{slug}", ids(names, "physics."), (1, 2, 3, 4, 5)))

    def test_past_paper_topic_is_union_in_order(self):
        union = []
        for n in HA + HT + FN + FG:
            if n not in union:
                union.append(n)
        for y in (10, 11):
            t = self.reg.topic_by_label("maths", y, PAST_PAPER_LABEL)
            self.assertEqual(t.id, f"maths.y{y}.past_paper")
            self.assertEqual(t.label, "Past paper practice")
            self.assertTrue(t.exam)
            self.assertEqual(t.skills, ids(union))
            self.assertEqual(len(t.skills), len(set(t.skills)))
            self.assertEqual(t.level_map, (2, 3, 3, 4, 5))
        for y in (7, 8, 9):
            t = self.reg.topic_by_label("maths", y, PAST_PAPER_LABEL)
            self.assertTrue(t.exam)
            self.assertEqual(t.level_map, KS3_PAST_MAP[y])
            rows = [self.reg.topic_by_label("maths", y, lbl) for r in self.reg.topic_rows("maths", y) for lbl in r]
            self.assertEqual(set(t.skills), {s for r in rows for s in r.skills})
        pt = self.reg.topic_by_label("physics", 11, PAST_PAPER_LABEL)
        self.assertEqual(pt.id, "physics.y11.past_paper")
        self.assertEqual(pt.skills, ids(["speed", "acceleration", "force", "weight", "kinetic_energy", "gpe", "power",
                                         "ohms_law", "electrical_power", "charge", "density", "pressure"], "physics."))
        self.assertEqual(pt.level_map, (2, 3, 3, 4, 5))
        self.assertTrue(pt.exam)

    def test_past_paper_absent_when_no_content(self):
        self.assertIsNone(self.reg.topic_by_label("physics", 8, PAST_PAPER_LABEL))
        self.assertIsNone(self.reg.topic_by_label("maths", 12, PAST_PAPER_LABEL))

    def test_topic_by_label_case_and_trim(self):
        a = self.reg.topic_by_label("maths", 11, "GCSE Higher: algebra & functions")
        self.assertIs(self.reg.topic_by_label("maths", 11, "  gcse higher: ALGEBRA & functions  ").id == a.id, True)
        self.assertEqual(self.reg.topic_by_label("maths", 11, "past PAPER practice").id, "maths.y11.past_paper")
        self.assertIsNone(self.reg.topic_by_label("maths", 11, "Energy"))
        self.assertIsNone(self.reg.topic_by_label("maths", 11, ""))
        self.assertIsNone(self.reg.topic_by_label("maths", 11, MY_OWN_TOPIC_LABEL))
        self.assertIsNone(self.reg.topic_by_label("maths", 7, "GCSE Higher: algebra & functions"))

    def test_topic_by_id(self):
        self.assertEqual(self.reg.topic("maths.y11.higher_algebra").label, "GCSE Higher: algebra & functions")
        self.assertTrue(self.reg.topic("maths.y11.past_paper").exam)
        self.assertEqual(self.reg.topic("physics.y10.energy").label, "Energy")
        self.assertIsNone(self.reg.topic("maths.y11.nonsense"))
        self.assertIsNone(self.reg.topic(""))
        self.assertIsNone(self.reg.topic("own:maths.nonexistent"))

    def test_own_topic(self):
        t = self.reg.own_topic("maths.pythagoras")
        self.assertEqual(t.id, "own:maths.pythagoras")
        self.assertEqual(t.label, "Pythagoras' theorem")
        self.assertEqual(t.skills, ("maths.pythagoras",))
        self.assertEqual(t.level_map, (1, 2, 3, 4, 5))
        self.assertFalse(t.exam)
        self.assertEqual(self.reg.topic("own:maths.pythagoras"), t)

    def test_skill_lookup_and_order(self):
        self.assertEqual(self.reg.skill("maths.ratio").title, "Ratio")
        self.assertEqual(self.reg.skill("physics.ohms_law").subject, "physics")
        self.assertIsNone(self.reg.skill("maths.nope"))
        self.assertEqual([s.id for s in self.reg.skills_of("physics")],
                         [s.id for s in self.reg.skills_of("physics")])
        self.assertEqual(self.reg.skills_of("nothing"), [])
        self.assertEqual(len(self.reg.skills_of("maths")), 20)
        self.assertEqual(len(self.reg.skills_of("physics")), 12)

    def test_fresh_instance_each_call(self):
        self.assertIsNot(load_registry(), load_registry())

    def test_titles_of_selected_skills(self):
        want = {"maths.hcf_lcm": "HCF and LCM", "maths.standard_form": "Standard form",
                "maths.expand_brackets": "Expanding double brackets", "maths.trig_sides": "Trigonometry: missing sides",
                "maths.arcs_sectors": "Arcs and sectors", "physics.ohms_law": "Ohm's law (V = IR)",
                "physics.weight": "Weight (W = mg)", "maths.nth_term": "nth term",
                "maths.triangle_area_sine": "Area of a triangle (½ab sin C)"}
        for sid, title in want.items():
            self.assertEqual(self.reg.skill(sid).title, title)

    def test_match_required_aliases(self):
        want = {
            "maths": {
                "percentage": "percentages", "percentages": "percentages", "percent": "percentages",
                "fraction": "fractions", "fractions": "fractions", "ratio": "ratio", "ratios": "ratio",
                "hcf": "hcf_lcm", "lcm": "hcf_lcm", "highest common factor": "hcf_lcm", "lowest common multiple": "hcf_lcm",
                "standard form": "standard_form", "area": "area_perimeter", "perimeter": "area_perimeter",
                "angles": "angles", "angle facts": "angles", "pythagoras": "pythagoras", "circle": "circles",
                "circles": "circles", "circumference": "circles", "linear equations": "linear_equations",
                "solving equations": "linear_equations", "expanding brackets": "expand_brackets",
                "expand brackets": "expand_brackets", "double brackets": "expand_brackets",
                "factorising": "factorise_quadratics", "factorise": "factorise_quadratics",
                "factorising quadratics": "factorise_quadratics", "solving quadratics": "solve_quadratics",
                "quadratic equations": "solve_quadratics", "simultaneous equations": "simultaneous",
                "simultaneous": "simultaneous", "nth term": "nth_term", "sequences": "nth_term",
                "sohcahtoa": "trig_sides", "trigonometry": "trig_sides", "trig": "trig_sides",
                "missing angle": "trig_angles", "inverse trig": "trig_angles", "sine rule": "sine_rule",
                "ab sin c": "triangle_area_sine", "arc length": "arcs_sectors", "sector": "arcs_sectors",
                "sectors": "arcs_sectors", "arcs": "arcs_sectors",
            },
            "physics": {
                "speed": "speed", "distance time": "speed", "acceleration": "acceleration", "f = ma": "force",
                "f=ma": "force", "resultant force": "force", "newton's second law": "force", "weight": "weight",
                "w=mg": "weight", "gravitational field strength": "weight", "kinetic energy": "kinetic_energy",
                "gpe": "gpe", "gravitational potential energy": "gpe", "potential energy": "gpe", "power": "power",
                "ohm's law": "ohms_law", "ohms law": "ohms_law", "resistance": "ohms_law", "v = ir": "ohms_law",
                "electrical power": "electrical_power", "p=iv": "electrical_power", "charge": "charge",
                "q = it": "charge", "density": "density", "pressure": "pressure",
            },
        }
        for sub, mapping in want.items():
            for text, skill in mapping.items():
                with self.subTest(subject=sub, text=text):
                    res = self.reg.match_skills(sub, text)
                    self.assertTrue(res, f"no match for {text!r}")
                    self.assertEqual(res[0], f"{sub}.{skill}")

    def test_match_electrical_power_beats_power(self):
        res = self.reg.match_skills("physics", "electrical power")
        self.assertEqual(res[0], "physics.electrical_power")
        self.assertEqual(self.reg.match_skills("physics", "power")[0], "physics.power")

    def test_match_none(self):
        for text in ("photosynthesis", "", "   ", "hello world", "migration", "fractional"):
            with self.subTest(text=text):
                self.assertEqual(self.reg.match_skills("maths", text), [])
        self.assertEqual(self.reg.match_skills("physics", "photosynthesis"), [])
        self.assertEqual(self.reg.match_skills("nosuch", "ratio"), [])

    def test_match_is_subject_scoped(self):
        self.assertEqual(self.reg.match_skills("physics", "percentages"), [])
        self.assertEqual(self.reg.match_skills("maths", "ohm's law"), [])

    def test_match_normalisation(self):
        self.assertEqual(self.reg.match_skills("maths", "PYTHAGORAS")[0], "maths.pythagoras")
        self.assertEqual(self.reg.match_skills("maths", "  nth    term  ")[0], "maths.nth_term")
        self.assertEqual(self.reg.match_skills("physics", "Newton’s second law")[0], "physics.force")
        self.assertEqual(self.reg.match_skills("physics", "F   =   ma")[0], "physics.force")
        self.assertEqual(self.reg.match_skills("maths", "help with pythagoras please")[0], "maths.pythagoras")
        self.assertEqual(self.reg.match_skills("maths", "pythagoras’ theorem")[0], "maths.pythagoras")

    def test_match_word_boundaries(self):
        self.assertEqual(self.reg.match_skills("maths", "areas")[0], "maths.area_perimeter")     # optional trailing s
        self.assertEqual(self.reg.match_skills("maths", "hcfs")[0], "maths.hcf_lcm")
        self.assertEqual(self.reg.match_skills("maths", "xratio"), [])
        self.assertEqual(self.reg.match_skills("maths", "ratiox"), [])
        self.assertEqual(self.reg.match_skills("maths", "3ratio"), [])
        self.assertEqual(self.reg.match_skills("maths", "ratio3"), [])

    def test_match_longest_alias_first(self):
        res = self.reg.match_skills("maths", "ratio and percentages")
        self.assertEqual(res[0], "maths.percentages")
        self.assertIn("maths.ratio", res)
        self.assertEqual(len(res), len(set(res)))


class TestV2Loading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def broken(self, text="{ this is not json"):
        path = os.path.join(self.tmp.name, "broken.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_strict_load_raises_on_a_broken_extra_bank(self):
        with self.assertRaises(Exception):
            load_registry([self.broken()])
        with self.assertRaises(Exception):
            load_registry([self.broken('{"subject": {"id": "x"}}')])
        with self.assertRaises(Exception):
            load_registry([os.path.join(self.tmp.name, "missing.json")])

    def test_strict_is_the_default(self):
        with self.assertRaises(Exception):
            load_registry(banks=[self.broken()], strict=True)

    def test_non_strict_skips_the_broken_source_and_collects_errors(self):
        with self.assertLogs(level="WARNING"):
            reg = load_registry([self.broken()], strict=False)
        self.assertEqual(len(reg.load_errors), 1)
        msg = reg.load_errors[0]
        self.assertTrue(msg.startswith("subject source "), msg)
        self.assertIn(" failed: ", msg)
        self.assertEqual([s.title for s in reg.subjects_for_year(10)][:2], ["Maths", "English Language"])
        self.assertIsNotNone(reg.skill("maths.pythagoras"))

    def test_non_strict_good_bank_plus_bad_bank(self):
        good = os.path.join(helpers.FIXTURES, "bank_sample.json")
        with self.assertLogs(level="WARNING"):
            reg = load_registry([self.broken(), good], strict=False)
        self.assertEqual(len(reg.load_errors), 1)
        self.assertIsNotNone(reg.skill("testsubj.adding"))

    def test_shipped_content_loads_without_errors_when_non_strict(self):
        reg = load_registry(strict=False)
        self.assertEqual(reg.load_errors, [], "\n".join(reg.load_errors))

    def test_load_errors_empty_for_strict_registry(self):
        self.assertEqual(load_registry().load_errors, [])

    def test_load_registry_is_fast(self):
        t0 = time.time()
        load_registry()
        self.assertLess(time.time() - t0, 10.0)

    def test_extra_bank_duplicating_a_subject_fails_strictly(self):
        path = os.path.join(helpers.FIXTURES, "bank_sample.json")
        with self.assertRaises(Exception):
            load_registry([path, path])


class TestV2Labels(unittest.TestCase):
    def test_letters_a_to_e_are_reserved(self):
        for lbl in ("A", "B", "C", "D", "E"):
            with self.subTest(label=lbl):
                with self.assertRaises(RegistryError):
                    one_subject(((topic("t1", lbl, ["s.a"]),),))
        one_subject(((topic("t1", "F", ["s.a"]),),))               # only A-E

    def test_labels_are_dash_insensitive(self):
        reg = one_subject(((topic("t1", "Germany 1890–1945", ["s.a"]),),))
        for text in ("Germany 1890–1945", "germany 1890-1945", "Germany 1890—1945", "  GERMANY 1890-1945 "):
            with self.subTest(text=text):
                t = reg.topic_by_label("s", 10, text)
                self.assertIsNotNone(t)
                self.assertEqual(t.id, "t1")

    def test_dash_variants_collide_as_duplicate_labels(self):
        with self.assertRaises(RegistryError):
            one_subject(((topic("t1", "Germany 1890–1945", ["s.a"]),), (topic("t2", "Germany 1890-1945", ["s.b"]),)))

    def test_aliases_are_accent_insensitive(self):
        reg = one_subject(((topic("t1", "T", ["s.a"]),),), [sk("s.a", ["passé composé", "foo"]), sk("s.b", ["zzz"])])
        for text in ("passe compose", "PASSÉ COMPOSÉ", "help with passe compose please", "passé composé"):
            with self.subTest(text=text):
                self.assertEqual(reg.match_skills("s", text), ["s.a"])
        self.assertEqual(reg.match_skills("s", "passe composee"), [])

    def test_shipped_french_alias_without_accents(self):
        reg = load_registry()
        res = reg.match_skills("french", "passe compose")
        self.assertTrue(res and res[0] == "french.grammar", f"[content-5a Languages-a] {res}")


class TestMatchOrdering(unittest.TestCase):
    def test_ties_by_registration_order(self):
        reg = one_subject(((topic("s.t", "T", ["s.b", "s.a"]),),),
                          [sk("s.b", ["foo"]), sk("s.a", ["foo"])])
        self.assertEqual(reg.match_skills("s", "foo"), ["s.b", "s.a"])
        self.assertEqual([x.id for x in reg.skills_of("s")], ["s.b", "s.a"])

    def test_score_beats_registration_order(self):
        reg = one_subject(((topic("s.t", "T", ["s.a", "s.b"]),),),
                          [sk("s.a", ["foo"]), sk("s.b", ["foo bar"])])
        self.assertEqual(reg.match_skills("s", "foo bar"), ["s.b", "s.a"])

    def test_half_sign_normalised(self):
        reg = one_subject(((topic("s.t", "T", ["s.a"]),),), [sk("s.a", ["1/2 turn"]), sk("s.b", ["zzz"])])
        self.assertEqual(reg.match_skills("s", "a ½ turn"), ["s.a"])


class TestRegisterErrors(unittest.TestCase):
    def rows(self, *labels_per_row, prefix="t"):
        n = 0
        rows = []
        for r in labels_per_row:
            row = []
            for lbl in r:
                n += 1
                row.append(topic(f"{prefix}{n}", lbl, ["s.a"]))
            rows.append(tuple(row))
        return tuple(rows)

    def test_valid_baseline(self):
        reg = one_subject(self.rows(("Alpha", "Beta"), ("Gamma",)))
        self.assertEqual(reg.topic_rows("s", 10), [("Alpha", "Beta"), ("Gamma",)])
        self.assertEqual(reg.years(), [10])

    def test_valid_same_label_in_different_years(self):
        reg = Registry()
        spec1 = YearSpec(rows=((topic("t1", "Alpha", ["s.a"]),),))
        spec2 = YearSpec(rows=((topic("t2", "Alpha", ["s.a"]),),))
        reg.register(Subject("s", "S", 1, {10: spec1, 11: spec2}), [sk("s.a")])
        self.assertEqual(reg.years(), [10, 11])

    def test_duplicate_subject(self):
        reg = one_subject(self.rows(("Alpha",)))
        with self.assertRaises(RegistryError):
            reg.register(Subject("s", "S2", 2, {10: YearSpec(rows=((topic("x1", "X", ["s.c"]),),))}), [sk("s.c")])

    def test_duplicate_skill_across_subjects_and_within_list(self):
        reg = one_subject(self.rows(("Alpha",)))
        with self.assertRaises(RegistryError):
            reg.register(Subject("u", "U", 2, {10: YearSpec(rows=((topic("u1", "U", ["s.a"]),),))}), [sk("s.a", subject="u")])
        reg2 = Registry()
        with self.assertRaises(RegistryError):
            reg2.register(Subject("s", "S", 1, {10: YearSpec(rows=((topic("t1", "Alpha", ["s.a"]),),))}), [sk("s.a"), sk("s.a")])

    def test_skill_subject_mismatch(self):
        reg = Registry()
        with self.assertRaises(RegistryError):
            reg.register(Subject("s", "S", 1, {10: YearSpec(rows=((topic("t1", "Alpha", ["s.a"]),),))}),
                         [sk("s.a", subject="other")])

    def test_unknown_skill_in_topic(self):
        with self.assertRaises(RegistryError):
            one_subject(((topic("t1", "Alpha", ["s.missing"]),),))

    def test_duplicate_topic_id(self):
        with self.assertRaises(RegistryError):
            one_subject(((topic("same", "Alpha", ["s.a"]), topic("same", "Beta", ["s.a"])),))
        reg = Registry()
        with self.assertRaises(RegistryError):
            reg.register(Subject("s", "S", 1, {10: YearSpec(rows=((topic("same", "Alpha", ["s.a"]),),)),
                                               11: YearSpec(rows=((topic("same", "Beta", ["s.a"]),),))}), [sk("s.a")])

    def test_duplicate_label_within_year(self):
        with self.assertRaises(RegistryError):
            one_subject(((topic("t1", "Alpha", ["s.a"]),), (topic("t2", "Alpha", ["s.a"]),)))
        with self.assertRaises(RegistryError):
            one_subject(((topic("t1", "Alpha", ["s.a"]), topic("t2", "Alpha", ["s.b"])),))

    def test_reserved_labels(self):
        for lbl in ("Past paper practice", "My own topic", "🎓 Change year", "📘 Change subject"):
            with self.subTest(label=lbl):
                with self.assertRaises(RegistryError):
                    one_subject(((topic("t1", lbl, ["s.a"]),),))

    def test_bad_level_maps(self):
        for lm in ((1, 2, 3, 4), (1, 2, 3, 4, 5, 5), (0, 1, 2, 3, 4), (1, 2, 3, 4, 6), (), (1, 2, 3, 4, -1)):
            with self.subTest(level_map=lm):
                with self.assertRaises(RegistryError):
                    one_subject(((topic("t1", "A", ["s.a"], level_map=lm),),))

    def test_good_level_map_boundaries(self):
        one_subject(((topic("t1", "A", ["s.a"], level_map=(1, 1, 1, 1, 1)),),))
        one_subject(((topic("t1", "A", ["s.a"], level_map=(5, 5, 5, 5, 5)),),))

    def test_row_size(self):
        with self.assertRaises(RegistryError):
            one_subject(((),))
        with self.assertRaises(RegistryError):
            one_subject(((topic("t1", "A", ["s.a"]), topic("t2", "B", ["s.a"]), topic("t3", "C", ["s.a"])),))
        one_subject(((topic("t1", "A", ["s.a"]), topic("t2", "B", ["s.a"])),))   # 2 is fine

    def test_subjects_sorted_by_order(self):
        reg = Registry()
        for sid, order in (("c", 30), ("a", 10), ("b", 20)):
            reg.register(Subject(sid, sid.upper(), order, {10: YearSpec(rows=((topic(f"{sid}.t", "Topic", [f"{sid}.k"]),),))}),
                         [sk(f"{sid}.k")])
        self.assertEqual([s.id for s in reg.subjects_for_year(10)], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
