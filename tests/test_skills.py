import os
import re
import unittest

import helpers
import spec
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
# v2 section 7: REQUIRED = v1 ids plus every generator (G) skill of section 5 except the optional extras
V2_GENERATORS = [sid for sid, info in spec.SKILLS.items() if info["kind"] == "G" and sid not in spec.OPTIONAL_EXTRAS]
REQUIRED = [f"maths.{n}" for n in MATHS] + [f"physics.{n}" for n in PHYSICS] + V2_GENERATORS
KINDS = ("number", "fraction", "set", "assign", "expr", "ratio", "rubric", "choice", "short")
FORMS = {"number": ("any", "standard"), "fraction": ("any", "simplest", "mixed"),
         "expr": ("any", "expanded", "factorised"), "ratio": ("any", "simplest"), "set": ("any",),
         "assign": ("any",), "rubric": ("any",), "choice": ("any",), "short": ("any", "strict", "case", "pinyin")}
GEN_SUBJECTS = ["maths", "physics"] + [s["id"] for s in spec.SUBJECTS
                                       if any(i["kind"] == "G" and k.startswith(s["id"] + ".") for k, i in spec.SKILLS.items())]
OWNER = {s["id"]: s["owner"] for s in spec.SUBJECTS}
# 30 seeds per skill and level by default (docs/ARCHITECTURE_V2.md section 7); TUTOR_FULL_TESTS=1 runs 300.
SEEDS = 300 if os.environ.get("TUTOR_FULL_TESTS") == "1" else 30


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
            if a.kind == "choice" and not p.ref.startswith(skill.id + "#"):
                bad(level, seed, f"choice problem without a ref '<skill_id>#...': {p.ref!r}")
            if a.kind == "choice" and not 3 <= len(a.value["options"]) <= 5:
                bad(level, seed, f"{len(a.value['options'])} options")
            if a.kind != "rubric":
                v = check(a, a.display)
                if v.status != "correct" or v.feedback:
                    bad(level, seed, f"display {a.display!r} judged {v.status} ({v.feedback})")
                pt = perturb(a)
                v = check(a, pt, p.mistakes)
                if v.status == "correct":
                    bad(level, seed, f"perturbed {pt!r} of {a.display!r} judged correct")
                for near in boundary_variants(a):
                    if check(a, near).status == "correct":
                        bad(level, seed, f"near miss {near!r} of {a.display!r} judged correct")
                if a.kind == "choice":
                    for j, opt in enumerate(a.value["options"]):
                        if j != a.value["correct"] and check(a, "ABCDE"[j], p.mistakes).status != "wrong":
                            bad(level, seed, f"wrong letter {'ABCDE'[j]} not judged wrong")
                        if len(opt) >= 4 and j == a.value["correct"] and re.search(r"(?i)\b" + re.escape(opt) + r"\b", p.hint):
                            bad(level, seed, f"hint contains the correct option {opt!r}")
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


# Ladder kinds written in section 5.1 ("Ladder L1 -> L5"): skill -> {level: (kind, dp, sf, form)}; None = not stated
LADDER = {
    "further_maths.functions": {3: ("expr", None, None, None), 4: ("expr", None, None, "expanded"), 5: ("set", None, None, None)},
    "further_maths.polynomials": {3: ("assign", None, None, None), 4: ("assign", None, None, None), 5: ("set", None, None, None)},
    "further_maths.coordinates": {1: ("assign", None, None, None), 2: ("fraction", None, None, None),
                                  3: ("fraction", None, None, None), 4: ("number", 1, None, None),
                                  5: ("assign", None, None, None)},
    "further_maths.calculus": {1: ("expr", None, None, None), 2: ("expr", None, None, None), 3: ("number", None, None, None),
                               4: ("set", None, None, None), 5: ("assign", None, None, None)},
    "further_maths.matrices": {3: ("assign", None, None, None), 4: ("choice", None, None, None), 5: ("assign", None, None, None)},
    "further_maths.trigonometry": {1: ("choice", None, None, None), 2: ("fraction", None, None, None),
                                   3: ("set", 1, None, None), 4: ("set", None, None, None), 5: ("fraction", None, None, None)},
    "statistics.stratified": {1: ("fraction", None, None, "simplest"), 4: ("set", None, None, None)},
    "statistics.averages": {4: ("number", 1, None, None)},
    "statistics.spread": {5: ("number", 2, None, None)},
    "statistics.spearman": {3: ("number", 2, None, None), 4: ("number", 2, None, None), 5: ("number", 3, None, None)},
    "statistics.probability": {1: ("fraction", None, None, "simplest")},
    "biology.magnification": {5: ("number", None, 3, "standard")},
    "biology.data_maths": {1: ("number", 1, None, None), 4: ("number", None, 3, None), 5: ("number", None, 3, None)},
    "biology.punnett": {1: ("fraction", None, None, None), 4: ("ratio", None, None, "simplest")},
    "chemistry.mr": {4: ("number", 1, None, None), 5: ("number", 1, None, None)},
    "chemistry.moles": {3: ("number", None, 3, None), 4: ("number", None, 3, None), 5: ("number", None, 3, "standard")},
    "chemistry.concentration": {4: ("number", None, 3, None)},
    "chemistry.yield_economy": {1: ("number", 1, None, None), 3: ("number", None, 3, None)},
    "chemistry.rates": {4: ("number", None, 3, None)},
    "chemistry.rf_values": {1: ("number", 2, None, None), 5: ("choice", None, None, None)},
    "computer_science.binary": {1: ("number", None, None, None), 2: ("short", None, None, None), 5: ("short", None, None, None)},
    "computer_science.data_units": {4: ("number", None, 3, None)},
    "computer_science.logic": {1: ("number", None, None, None), 3: ("choice", None, None, None)},
    "astronomy.orbits": {1: ("number", None, 3, "standard")},
    "astronomy.distances": {5: ("number", 1, None, None)},
    "geography.skills_stats": {3: ("number", 1, None, None)},
    "economics.elasticity": {1: ("number", 1, None, None), 2: ("number", 2, None, None)},
    "economics.firms_maths": {4: ("number", 2, None, None)},
    "economics.interest": {2: ("number", 2, None, None)},
    "economics.macro_maths": {4: ("number", 2, None, None)},
    "business.finance_maths": {4: ("number", 1, None, None)},
    "psychology.stats": {3: ("number", 1, None, None), 4: ("ratio", None, None, "simplest")},
}


class TestSkills(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = load_registry()

    def owner(self, sid):
        return OWNER.get(sid.split(".")[0], "frozen")

    def test_required_ids_exist(self):
        self.assertEqual(len(REQUIRED), 32 + len(V2_GENERATORS))
        self.assertGreaterEqual(len(V2_GENERATORS), 40)
        missing = [f"[{self.owner(s)}] {s}" for s in REQUIRED if self.reg.skill(s) is None]
        self.assertEqual(missing, [], f"{len(missing)} required generator skill(s) missing: {missing[:12]}")

    def test_required_generators_have_no_items(self):
        bad = [f"[{self.owner(s)}] {s}" for s in REQUIRED if self.reg.skill(s) is not None and self.reg.skill(s).items]
        self.assertEqual(bad, [])

    def test_every_skill_belongs_to_its_subject(self):
        for sub in GEN_SUBJECTS:
            for sk in self.reg.skills_of(sub):
                self.assertEqual(sk.subject, sub)
                self.assertTrue(sk.id.startswith(sub + "."))
                self.assertTrue(sk.title.strip())
                self.assertTrue(sk.aliases)

    def generators(self, subject_id):
        return [sk for sk in self.reg.skills_of(subject_id) if not sk.items]

    def _run_subject(self, subject_id):
        fails = []
        skills = self.generators(subject_id)
        if not skills:
            self.fail(f"[{self.owner(subject_id)}] no generator skills loaded for {subject_id}")
        for sk in skills:
            fails.extend(f"[{self.owner(sk.id)}] {f}" for f in audit(sk))
        self.assertEqual(len(fails), 0, f"{len(fails)} failure(s); first 10:\n" + "\n".join(fails[:10]))

    def _run_rounding(self, subject_id):
        fails = []
        for sk in self.generators(subject_id):
            fails.extend(f"[{self.owner(sk.id)}] {f}" for f in rounding_audit(sk))
        by_skill = sorted({f.split(" L")[0] for f in fails})
        self.assertEqual(len(fails), 0,
                         f"{len(fails)} problem(s) in skills {by_skill}; first 5:\n" + "\n".join(fails[:5]))

    def _run_content(self, subject_id):
        fails = []
        for sk in self.generators(subject_id):
            fails.extend(f"[{self.owner(sk.id)}] {f}" for f in content_audit(sk))
        self.assertEqual(len(fails), 0, f"{len(fails)} problem(s); first 10:\n" + "\n".join(fails[:10]))

    def test_ladder_kinds(self):
        fails = []
        seeds = range(min(SEEDS, 20))
        for sid, levels in LADDER.items():
            sk = self.reg.skill(sid)
            if sk is None:
                fails.append(f"[{self.owner(sid)}] {sid}: missing")
                continue
            for level, (kind, dp, sf, form) in levels.items():
                for seed in seeds:
                    a = sk.generate(level, seed).answer
                    got = (a.kind, a.dp, a.sf, a.form)
                    if a.kind != kind or (dp is not None and a.dp != dp) or (sf is not None and a.sf != sf) \
                            or (form is not None and a.form != form):
                        fails.append(f"[{self.owner(sid)}] {sid} L{level} seed={seed}: {got} != {(kind, dp, sf, form)}")
                        break
        self.assertEqual(len(fails), 0, f"{len(fails)} ladder deviation(s); first 12:\n" + "\n".join(fails[:12]))

    def test_computer_science_states_the_kilobyte_convention(self):
        fails = []
        sk = self.reg.skill("computer_science.data_units")
        if sk is None:
            self.fail("[content-1 STEM] computer_science.data_units missing")
        for level in range(1, 6):
            for seed in range(SEEDS):
                t = sk.generate(level, seed).text
                if re.search(r"(?i)\b(kilobytes?|kb|megabytes?|mb|gigabytes?|gb)\b", t) and "1 kilobyte = 1000 bytes" not in t:
                    fails.append(f"L{level} seed={seed}: {t[:80]!r}")
        self.assertEqual(fails, [], f"[content-1 STEM] data-size questions must say 'Use 1 kilobyte = 1000 bytes': {fails[:3]}")

    def test_computer_science_code_has_no_double_star(self):
        for sk in self.generators("computer_science"):
            for level in range(1, 6):
                for seed in range(min(SEEDS, 30)):
                    p = sk.generate(level, seed)
                    self.assertNotIn("**", p.text + p.solution + p.hint, f"[content-1 STEM] {sk.id}")

    def test_choice_generator_problems_vary_and_have_refs(self):
        fails = []
        for sid in ("further_maths.matrices", "further_maths.trigonometry", "computer_science.logic", "chemistry.rf_values"):
            sk = self.reg.skill(sid)
            if sk is None:
                continue
            for level in range(1, 6):
                for seed in range(min(SEEDS, 30)):
                    p = sk.generate(level, seed)
                    if p.answer.kind == "choice" and not p.ref.startswith(sid + "#"):
                        fails.append(f"[{self.owner(sid)}] {sid} L{level} seed={seed}: ref {p.ref!r}")
                        break
        self.assertEqual(fails, [])


def _add_subject_tests():
    for sub in GEN_SUBJECTS:
        for name, fn in (("property", "_run_subject"), ("rounding_stated", "_run_rounding"), ("content", "_run_content")):
            def t(self, sub=sub, fn=fn):
                getattr(self, fn)(sub)
            t.__name__ = f"test_{sub}_{name}"
            setattr(TestSkills, t.__name__, t)


_add_subject_tests()


if __name__ == "__main__":
    unittest.main()
