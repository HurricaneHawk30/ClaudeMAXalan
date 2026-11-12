import unittest
from fractions import Fraction

import helpers  # noqa: F401
from tutor.content import Answer, Mistake, check
from tutor.content.checker import parse_number, parse_fraction, Verdict

FORM_STANDARD = helpers.FORM_STANDARD
FORM_FACTORISED = helpers.FORM_FACTORISED
FORM_EXPANDED = helpers.FORM_EXPANDED
FORM_SIMPLEST = helpers.FORM_SIMPLEST

# (name, Answer, correct, wrong, wrong-with-form [(text, feedback)], unparsed)
TABLE = [
    ("number 4", Answer("number", "4", 4.0),
     ["4", "x = 4", "x=4", "4.0", "Answer: 4", "3x = 12\nx = 4", "4 cm", "+4", "x = 4\nthanks"],
     ["5", "x = -4"], [], ["four", "I think so", ""]),
    ("number 12.5 dp1", Answer("number", "12.5 m/s", 12.5, dp=1),
     ["12.5", "12.5 m/s", "12.5m/s", "v = 12.5 m/s", "12.50", "12.49"], ["12.6", "125"], [], []),
    ("number 7.07 dp1", Answer("number", "7.1", 7.0710678, dp=1),
     ["7.1", "7.07", "7.071"], ["7.0", "7.2"], [], []),
    ("number 1234.5678 sf3", Answer("number", "1230", 1234.5678, sf=3),
     ["1230", "1,230", "1.23 × 10^3"], ["1240", "1200"], [], []),
    ("standard 32000", Answer("number", "3.2 × 10^4", 32000.0, form="standard"),
     ["3.2 × 10^4", "3.2x10^4", "3.2 x 10^4", "3.2*10^4", "3.2 × 10⁴"], ["3.2 × 10^5"],
     [("32000", FORM_STANDARD), ("32 × 10^3", FORM_STANDARD)], []),
    ("standard 0.00045", Answer("number", "4.5 × 10^-4", 0.00045, form="standard"),
     ["4.5 × 10^-4", "4.5×10^(-4)", "4.5 x 10^−4", "4.5 × 10⁻⁴"], ["4.5 × 10^-3"],
     [("0.00045", FORM_STANDARD)], []),
    ("number 25pi dp1", Answer("number", "78.5", 78.5398, dp=1),
     ["78.5", "25π", "25pi"], ["78.6"], [], []),
    ("fraction 3/4", Answer("fraction", "3/4", "3/4"),
     ["3/4", "6/8", "0.75", "x = 3/4", " 3 / 4 "], ["4/3", "0.7"], [], ["three quarters"]),
    ("fraction 7/4", Answer("fraction", "1 3/4", "7/4"),
     ["1 3/4", "7/4", "1.75"], ["1 1/4"], [], []),
    ("fraction 1/3", Answer("fraction", "1/3", "1/3"),
     ["1/3", "2/6", "0.33", "0.333"], ["0.3", "0.34"], [], []),
    ("fraction 3/4 simplest", Answer("fraction", "3/4", "3/4", form="simplest"),
     ["3/4"], ["2/3"], [("6/8", FORM_SIMPLEST), ("0.75", FORM_SIMPLEST)], []),
    ("set 2,-3", Answer("set", "x = 2, x = -3", ["2", "-3"]),
     ["x = 2, x = -3", "x=-3, x=2", "x = 2 or x = -3", "2 and -3", "-3, 2", "x = 2\nx = -3",
      "(x-2)(x+3)=0\nx=2\nx=-3"],
     ["x = 2", "x = 2, x = 3", "x = -2, x = 3"], [], ["both of them"]),
    ("set ordered 20,30", Answer("set", "£20 and £30", ["20", "30"], ordered=True),
     ["£20 and £30", "20, 30", "£20, £30", "20:30"], ["30 and 20", "£25 and £25"], [], []),
    ("assign x=3 y=-1", Answer("assign", "x = 3, y = -1", {"x": "3", "y": "-1"}),
     ["x = 3, y = -1", "y=-1, x=3", "x=3 and y=-1", "(3, -1)", "x = 3\ny = -1"],
     ["x = -1, y = 3", "x = 3, y = 1"], [], ["x is three"]),
    ("expr expanded", Answer("expr", "x² + 5x + 6", "x**2+5*x+6", form="expanded"),
     ["x² + 5x + 6", "x^2+5x+6", "x**2 + 5*x + 6", "5x + x^2 + 6", "6+5x+x²",
      "(x+2)(x+3) = x^2+3x+2x+6 = x^2+5x+6"],
     ["x^2+6x+5", "x^2+5x"], [("(x+2)(x+3)", FORM_EXPANDED)], ["no idea how"]),
    ("expr factorised", Answer("expr", "(x + 2)(x + 3)", "(x+2)*(x+3)", form="factorised"),
     ["(x+2)(x+3)", "(x+3)(x+2)", "(2+x)(3+x)"], ["(x-2)(x-3)", "(x+1)(x+6)"],
     [("x^2+5x+6", FORM_FACTORISED)], []),
    ("expr var n", Answer("expr", "3n + 2", "3*n+2", var="n"),
     ["3n+2", "nth term = 3n + 2", "2 + 3n"], ["3n", "n+3"], [], ["x+2"]),
    ("ratio simplest", Answer("ratio", "2:3", [2, 3], form="simplest"),
     ["2:3", "2 : 3"], ["3:2"], [("4:6", FORM_SIMPLEST)], []),
    ("ratio any", Answer("ratio", "2:3", [2, 3]),
     ["4:6"], ["3:2"], [], []),
]


class TestAcceptanceTable(unittest.TestCase):
    def test_table(self):
        for name, ans, correct, wrong, wrong_form, unparsed in TABLE:
            for t in correct:
                with self.subTest(case=name, kind="C", text=t):
                    v = check(ans, t)
                    self.assertEqual((v.status, v.feedback), ("correct", ""))
            for t in wrong:
                with self.subTest(case=name, kind="W", text=t):
                    v = check(ans, t)
                    self.assertEqual(v.status, "wrong")
                    self.assertEqual(v.feedback, "")
            for t, fb in wrong_form:
                with self.subTest(case=name, kind="WF", text=t):
                    v = check(ans, t)
                    self.assertEqual((v.status, v.feedback), ("wrong", fb))
            for t in unparsed:
                with self.subTest(case=name, kind="U", text=t):
                    self.assertEqual(check(ans, t).status, "unparsed")

    def test_display_is_always_correct(self):
        for name, ans, *_ in TABLE:
            with self.subTest(case=name):
                self.assertEqual(check(ans, ans.display).status, "correct")

    def test_rubric_always_unmarkable(self):
        a = Answer("rubric", "Model answer", None, mark_scheme="x", max_marks=2)
        for t in ("anything", "", "42", "Model answer", "x = 4"):
            with self.subTest(text=t):
                self.assertEqual(check(a, t).status, "unmarkable")

    def test_form_texts_verbatim_and_no_trailing_period(self):
        from tutor.content import checker
        self.assertEqual(checker.FORM_STANDARD, FORM_STANDARD)
        self.assertEqual(checker.FORM_FACTORISED, FORM_FACTORISED)
        self.assertEqual(checker.FORM_EXPANDED, FORM_EXPANDED)
        self.assertEqual(checker.FORM_SIMPLEST, FORM_SIMPLEST)
        for t in (FORM_STANDARD, FORM_FACTORISED, FORM_EXPANDED, FORM_SIMPLEST):
            self.assertFalse(t.endswith("."))

    def test_verdict_defaults(self):
        self.assertEqual(Verdict("correct").feedback, "")


class TestExtraction(unittest.TestCase):
    A = Answer("number", "4", 4.0)

    def test_extraction_variants(self):
        for t in ("so x = 4", "Therefore x = 4", "ans 4", "answer: 4", "x ≈ 4", "£4", "$4", "€4",
                  "4 cm²", "4%", "4°", "x = 2 + 2 = 4", "working\n\nx = 4\n\n", "4\n"):
            with self.subTest(text=t):
                if t == "4%":
                    continue   # percent sign stripped: value 4
                self.assertEqual(check(self.A, t).status, "correct")

    def test_percent_stripped(self):
        self.assertEqual(check(Answer("number", "15%", 15.0), "15%").status, "correct")

    def test_money_and_units(self):
        a = Answer("number", "£24.50", 24.5, dp=2)
        for t in ("£24.50", "24.5", "£24.5", "24.50 pounds"):
            with self.subTest(text=t):
                self.assertEqual(check(a, t).status, "correct")

    def test_negative_forms(self):
        a = Answer("number", "-4", -4.0)
        for t in ("-4", "−4", "x = -4", "x = −4"):
            with self.subTest(text=t):
                self.assertEqual(check(a, t).status, "correct")
        self.assertEqual(check(a, "4").status, "wrong")

    def test_boundaries_dp(self):
        a = Answer("number", "12.5", 12.5, dp=1)
        self.assertEqual(check(a, "12.55").status, "correct")     # exactly half a unit
        self.assertEqual(check(a, "12.56").status, "wrong")
        self.assertEqual(check(a, "12.45").status, "correct")
        self.assertEqual(check(a, "12.44").status, "wrong")

    def test_no_dp_no_sf_tolerance(self):
        a = Answer("number", "1000000", 1000000.0)
        self.assertEqual(check(a, "1000000").status, "correct")
        self.assertEqual(check(a, "1000000.5").status, "correct")    # within 1e-6 relative
        self.assertEqual(check(a, "1000010").status, "wrong")

    def test_decimal_comma_and_thousands(self):
        self.assertEqual(check(Answer("number", "4.5", 4.5), "4,5").status, "correct")
        self.assertEqual(check(Answer("number", "1200", 1200.0), "1,200").status, "correct")

    def test_garbage_inputs_do_not_raise(self):
        for t in ("", " ", "\n\n", "💥", "=", "= =", "x =", "1/0", "10^999999", "9" * 400, "((((", "\x00",
                  "/", "e", "-", "+", "1..2", "1/2/3", "∞"):
            for name, ans, *_ in TABLE:
                with self.subTest(text=t[:20], case=name):
                    v = check(ans, t)
                    self.assertIn(v.status, ("correct", "wrong", "unparsed", "unmarkable"))

    def test_empty_and_words_unparsed(self):
        for kind_ans in (Answer("number", "4", 4.0), Answer("fraction", "3/4", "3/4"),
                         Answer("set", "1, 2", ["1", "2"]), Answer("ratio", "1:2", [1, 2]),
                         Answer("assign", "x = 1, y = 2", {"x": "1", "y": "2"}),
                         Answer("expr", "x + 1", "x+1")):
            with self.subTest(kind=kind_ans.kind):
                self.assertEqual(check(kind_ans, "").status, "unparsed")
                self.assertEqual(check(kind_ans, "no idea").status, "unparsed")


class TestParsers(unittest.TestCase):
    def test_parse_number(self):
        cases = [("4", 4), ("4.5", 4.5), ("-3", -3), ("+3", 3), ("−3", -3), ("1,200", 1200), ("4,5", 4.5),
                 ("1/2", 0.5), ("1 1/2", 1.5), ("50%", 50), ("3.2 × 10^4", 32000), ("3.2x10^4", 32000),
                 ("3.2*10^4", 32000), ("3.2 × 10⁴", 32000), ("10^(-4)", 1e-4), ("10^−4", 1e-4),
                 ("10⁻⁴", 1e-4), ("2π", 2 * 3.141592653589793), ("2pi", 2 * 3.141592653589793),
                 ("  7 ", 7), ("0", 0)]
        for s, want in cases:
            with self.subTest(text=s):
                got = parse_number(s)
                self.assertIsNotNone(got)
                self.assertAlmostEqual(got, want, places=9)

    def test_parse_number_none(self):
        for s in ("", "three", "abc", "x", "four cm", "I think so"):
            with self.subTest(text=s):
                self.assertIsNone(parse_number(s))

    def test_parse_fraction(self):
        self.assertEqual(parse_fraction("3/4"), Fraction(3, 4))
        self.assertEqual(parse_fraction("1 3/4"), Fraction(7, 4))
        self.assertEqual(parse_fraction("0.75"), Fraction(3, 4))
        self.assertEqual(parse_fraction("5"), Fraction(5))
        self.assertEqual(parse_fraction("6/8"), Fraction(3, 4))
        self.assertIsNone(parse_fraction("three quarters"))
        self.assertIsNone(parse_fraction(""))


class TestMistakes(unittest.TestCase):
    A = Answer("number", "4", 4.0)
    M5 = Mistake(Answer("number", "5", 5.0), "You added instead of subtracting")
    M6 = Mistake(Answer("number", "6", 6.0), "You forgot to divide")

    def test_feedback_matches_mistake(self):
        v = check(self.A, "5", [self.M5, self.M6])
        self.assertEqual((v.status, v.feedback), ("wrong", "You added instead of subtracting"))
        v = check(self.A, "x = 6", [self.M5, self.M6])
        self.assertEqual((v.status, v.feedback), ("wrong", "You forgot to divide"))

    def test_non_matching_wrong_has_empty_feedback(self):
        v = check(self.A, "7", [self.M5, self.M6])
        self.assertEqual((v.status, v.feedback), ("wrong", ""))

    def test_first_match_wins(self):
        dup = Mistake(Answer("number", "5", 5.0), "Second feedback")
        self.assertEqual(check(self.A, "5", [self.M5, dup]).feedback, "You added instead of subtracting")
        self.assertEqual(check(self.A, "5", [dup, self.M5]).feedback, "Second feedback")

    def test_correct_ignores_mistakes(self):
        v = check(self.A, "4", [self.M5])
        self.assertEqual((v.status, v.feedback), ("correct", ""))

    def test_unparsed_ignores_mistakes(self):
        v = check(self.A, "hello", [self.M5])
        self.assertEqual((v.status, v.feedback), ("unparsed", ""))

    def test_no_mistakes_default(self):
        self.assertEqual(check(self.A, "5").feedback, "")
        self.assertEqual(check(self.A, "5", ()).feedback, "")

    def test_form_violation_has_priority_over_mistakes(self):
        a = Answer("number", "3.2 × 10^4", 32000.0, form="standard")
        m = Mistake(Answer("number", "32000", 32000.0), "Convert it")
        v = check(a, "32000", [m])
        self.assertEqual((v.status, v.feedback), ("wrong", FORM_STANDARD))

    def test_mistake_of_set_and_expr_kind(self):
        a = Answer("set", "x = 2, x = -3", ["2", "-3"])
        m = Mistake(Answer("set", "x = -2, x = 3", ["-2", "3"]), "Signs swapped")
        self.assertEqual(check(a, "x = -2, x = 3", [m]).feedback, "Signs swapped")
        e = Answer("expr", "(x + 2)(x + 3)", "(x+2)*(x+3)", form="factorised")
        me = Mistake(Answer("expr", "(x - 2)(x - 3)", "(x-2)*(x-3)", form="factorised"), "Check your signs")
        self.assertEqual(check(e, "(x-2)(x-3)", [me]).feedback, "Check your signs")


if __name__ == "__main__":
    unittest.main()
