import os
import re
import unittest

import helpers
from helpers import boundary_variants, perturb
from tutor.content import check, load_registry, problem_to_json, problem_from_json

MATHS = [
    "percentages", "fractions", "ratio", "hcf_lcm", "standard_form", "area_perimeter", "angles",
    "pythagoras", "circles", "linear_equations", "expand_brackets", "factorise_quadratics",
    "solve_quadratics", "simultaneous", "nth_term", "trig_sides", "trig_angles", "sine_rule",
    "triangle_area_sine", "arcs_sectors",
]
PHYSICS = ["speed", "acceleration", "force", "weight", "kinetic_energy", "gpe", "power", "ohms_law",
           "electrical_power", "charge", "density", "pressure"]
REQUIRED = [f"maths.{n}" for n in MATHS] + [f"physics.{n}" for n in PHYSICS]
KINDS = ("number", "fraction", "set", "assign", "expr", "ratio", "rubric")
FORMS = {"number": ("any", "standard"), "fraction": ("any", "simplest", "mixed"),
         "expr": ("any", "expanded", "factorised"), "ratio": ("any", "simplest"), "set": ("any",),
         "assign": ("any",), "rubric": ("any",)}
# 60 seeds per skill and level keep the whole suite under a minute; run with TUTOR_FULL_TESTS=1
# (300 seeds) before every deploy.
SEEDS = 300 if os.environ.get("TUTOR_FULL_TESTS") == "1" else 60


def problems_for(skill):
    for level in range(1, 6):
        for seed in range(SEEDS):
            yield level, seed


def audit(skill):
    """Returns a list of failure strings for one skill."""
    fails = []

    def bad(level, seed, msg):
        fails.append(f"{skill.id} L{level} seed={seed}: {msg}")

    for level in range(1, 6):
        texts = set()
        for seed in range(SEEDS):
            try:
                p = skill.generate(level, seed)
                p2 = skill.generate(level, seed)
            except Exception as e:  # noqa: BLE001
                bad(level, seed, f"generate raised {type(e).__name__}: {e}")
                continue
            if p != p2:
                bad(level, seed, "not deterministic")
                continue
            texts.add(p.text)
            a = p.answer
            if (p.skill_id, p.level, p.seed) != (skill.id, level, seed):
                bad(level, seed, f"problem header {(p.skill_id, p.level, p.seed)}")
            if not p.text.strip() or len(p.text) > 600:
                bad(level, seed, f"text length {len(p.text)}")
            if not p.solution.strip() or len(p.solution) > 300:
                bad(level, seed, f"solution length {len(p.solution)}")
            if p.solution.rstrip().endswith("."):
                bad(level, seed, "solution has trailing period")
            if not p.hint.strip():
                bad(level, seed, "empty hint")
            for field in (p.text, p.solution, p.hint):
                if "\\" in field or "`" in field or "**" in field:
                    bad(level, seed, f"markdown/latex in {field[:50]!r}")
            if a.kind not in KINDS:
                bad(level, seed, f"unknown kind {a.kind}")
                continue
            if a.form not in FORMS[a.kind]:
                bad(level, seed, f"form {a.form} invalid for {a.kind}")
            if a.dp is not None and not (0 <= a.dp <= 3):
                bad(level, seed, f"dp {a.dp}")
            if a.sf is not None and a.sf < 2:
                bad(level, seed, f"sf {a.sf}")
            if not a.display.strip():
                bad(level, seed, "empty display")
            try:
                if problem_from_json(problem_to_json(p)) != p:
                    bad(level, seed, "json round-trip differs")
            except Exception as e:  # noqa: BLE001
                bad(level, seed, f"json round-trip raised {e}")
            if a.kind != "rubric":
                v = check(a, a.display)
                if v.status != "correct":
                    bad(level, seed, f"display {a.display!r} judged {v.status} ({v.feedback})")
                pt = perturb(a)
                v = check(a, pt, p.mistakes)
                if v.status == "correct":
                    bad(level, seed, f"perturbed {pt!r} of {a.display!r} judged correct")
                for near in boundary_variants(a):
                    if check(a, near).status == "correct":
                        bad(level, seed, f"near miss {near!r} of {a.display!r} judged correct")
                if len(a.display) >= 3 and a.display in p.hint:
                    bad(level, seed, f"hint contains display {a.display!r}")
            for m in p.mistakes:
                if not m.feedback.strip() or m.feedback.rstrip().endswith("."):
                    bad(level, seed, f"mistake feedback {m.feedback!r}")
                if m.answer.display == a.display:
                    bad(level, seed, "mistake equals correct display")
                v = check(a, m.answer.display, p.mistakes)
                if v.status != "wrong":
                    bad(level, seed, f"mistake {m.answer.display!r} judged {v.status}")
                    continue
                first = next(x for x in p.mistakes if check(x.answer, m.answer.display).status == "correct")
                if v.feedback != first.feedback:
                    bad(level, seed, f"mistake {m.answer.display!r}: feedback {v.feedback!r} != {first.feedback!r}")
        if len(texts) < 2:
            fails.append(f"{skill.id} L{level}: only {len(texts)} distinct text(s) over {SEEDS} seeds")
    return fails


def rounding_audit(skill):
    """Section 5: every rounding instruction must be in the question text (kept separate so that a deviation here
    does not hide other failures of the property test)."""
    fails = []
    for level in range(1, 6):
        for seed in range(SEEDS):
            p = skill.generate(level, seed)
            a, t = p.answer, p.text.lower()
            if a.dp is not None and a.dp >= 1 and not any(k in t for k in ("decimal place", "nearest", "d.p")):
                fails.append(f"{skill.id} L{level} seed={seed}: dp={a.dp} but text states no rounding: {p.text[:80]!r}")
            if a.sf is not None and "significant figure" not in t:
                fails.append(f"{skill.id} L{level} seed={seed}: sf={a.sf} but text states no significant figures: {p.text[:80]!r}")
    return fails


_ONE_PLURAL = re.compile(r"(?<![\d.,])1 (?:parts|minutes|hours|seconds|terms)\b")
_ORDINAL = re.compile(r"\b(\d+)(st|nd|rd|th)\b")
_STD_DIVISION = re.compile(r"÷ [\d.]+ × 10\^")


def _suffix(n):
    return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def content_audit(skill):
    """Critic findings (Nov 2026): wording bugs, physics rounding, time units, mixed-number form."""
    from tutor.content.fmt import fmt_sf, fmt_std
    fails = []
    for level in range(1, 6):
        for seed in range(SEEDS):
            p = skill.generate(level, seed)
            a = p.answer
            where = f"{skill.id} L{level} seed={seed}"
            for field in [p.text, p.solution, p.hint] + [m.feedback for m in p.mistakes]:
                if _ONE_PLURAL.search(field):
                    fails.append(f"{where}: '1 ...s' in {field[:80]!r}")
                for m in _ORDINAL.finditer(field):
                    if m.group(2) != _suffix(int(m.group(1))):
                        fails.append(f"{where}: ordinal {m.group(0)!r}")
                if _STD_DIVISION.search(field):
                    fails.append(f"{where}: division by standard form without brackets in {field[:80]!r}")
            if "mixed number" in p.text and a.form != "mixed":
                fails.append(f"{where}: asks for a mixed number but form={a.form}")
            if skill.subject != "physics" or a.kind != "number":
                continue
            if not float(a.value).is_integer():
                if a.sf is None and a.dp is None:
                    fails.append(f"{where}: non-integer exact answer {a.display!r} without rounding")
                elif a.sf is not None:
                    rounded = fmt_std(a.value, a.sf) if a.form == "standard" else fmt_sf(a.value, a.sf)
                    if check(a, rounded).status != "correct":
                        fails.append(f"{where}: correctly rounded {rounded!r} not accepted")
            if a.display.endswith(" s") and "second" not in p.text:
                fails.append(f"{where}: time answer but the question does not say 'seconds'")
    return fails


class TestSkills(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = load_registry()

    def test_required_ids_exist(self):
        self.assertEqual(len(REQUIRED), 32)
        for sid in REQUIRED:
            with self.subTest(skill=sid):
                self.assertIsNotNone(self.reg.skill(sid))

    def test_every_skill_belongs_to_its_subject(self):
        for sub in ("maths", "physics"):
            for sk in self.reg.skills_of(sub):
                self.assertEqual(sk.subject, sub)
                self.assertTrue(sk.id.startswith(sub + "."))
                self.assertTrue(sk.title.strip())
                self.assertTrue(sk.aliases)

    def _run_subject(self, subject_id):
        fails = []
        skills = self.reg.skills_of(subject_id)
        self.assertTrue(skills)
        for sk in skills:
            fails.extend(audit(sk))
        self.assertEqual(len(fails), 0,
                         f"{len(fails)} failure(s); first 10:\n" + "\n".join(fails[:10]))

    def _run_rounding(self, subject_id):
        fails = []
        for sk in self.reg.skills_of(subject_id):
            fails.extend(rounding_audit(sk))
        by_skill = sorted({f.split(" L")[0] for f in fails})
        self.assertEqual(len(fails), 0,
                         f"{len(fails)} problem(s) in skills {by_skill}; first 5:\n" + "\n".join(fails[:5]))

    def test_maths_rounding_stated(self):
        self._run_rounding("maths")

    def test_physics_rounding_stated(self):
        self._run_rounding("physics")

    def _run_content(self, subject_id):
        fails = []
        for sk in self.reg.skills_of(subject_id):
            fails.extend(content_audit(sk))
        self.assertEqual(len(fails), 0, f"{len(fails)} problem(s); first 10:\n" + "\n".join(fails[:10]))

    def test_maths_content(self):
        self._run_content("maths")

    def test_physics_content(self):
        self._run_content("physics")

    def test_maths_property(self):
        self._run_subject("maths")

    def test_physics_property(self):
        self._run_subject("physics")


if __name__ == "__main__":
    unittest.main()
