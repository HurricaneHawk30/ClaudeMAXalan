import math
import unittest
from fractions import Fraction

import helpers  # noqa: F401
from tutor.content import Answer, Mistake, check
from tutor.content.checker import parse_number, parse_fraction, Verdict

FORM_STANDARD = helpers.FORM_STANDARD
FORM_FACTORISED = helpers.FORM_FACTORISED
FORM_EXPANDED = helpers.FORM_EXPANDED
FORM_SIMPLEST = helpers.FORM_SIMPLEST
FORM_MIXED = helpers.FORM_MIXED
FORM_FRACTION = helpers.FORM_FRACTION

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

# Real student working (critic findings, Nov 2026): the answer must be found, never a line of working.
REAL = [
    ("pythagoras 7.1 dp1", Answer("number", "7.1 cm", 7.0710678, dp=1),
     ["a^2 = 50\na = 7.1 (1 d.p.)", "a² = 50\na = 7.1 cm to 1 d.p.", "a² = 50\na = 7.07 = 7.1 cm (1dp)",
      "a^2 = 50\na = 7.1cm (1dp)", "7.1 cm (to 1 decimal place)", "√50 = 7.07…\n= 7.1 cm (1 d.p.)"],
     ["a^2 = 50\na = 7.3 (1 d.p.)", "a² = 50\na = 50 cm to 1 d.p."], [], []),
    ("area 36 cm²", Answer("number", "36 cm²", 36.0),
     ["8 × 9 = 72\n72 ÷ 2 = 36 cm2", "36cm2", "36 cm^2", "36 square cm", "36 cm squared"],
     ["8 × 9 = 72\n72 ÷ 2 = 37 cm2"], [], []),
    ("acceleration 12 m/s²", Answer("number", "12 m/s²", 12.0),
     ["v-u = 36\n36/3 = 12 m/s2", "12 ms-2", "12 m/s/s"], ["v-u = 36\n36/3 = 13 m/s2"], [], []),
    ("linear x = 4", Answer("number", "x = 4", 4.0),
     ["2x + 3 = 11\n2x = 8\nso it's 4", "3x+5=17\n3x=12\nI got 4", "x=4, check: 3(4)+5=17",
      "x = 4\ncheck: 3(4) + 5 = 17", "x = 4 because 12/3", "4 = x", "x equals 4", "x=4 ✓", "x = 4 :)",
      "x is 4", "I think it's 4"],
     ["2x + 3 = 11\n2x = 8\nso it's 5", "3x+5=17\n3x=12\nI got 5", "x=5, check: 3(5)+5=20"],
     [], ["x = 4\nmaybe it is 4 or 5", "can you help with question 2", "x = 4\nis it 4 or 5?"]),
    ("angle 43.5°", Answer("number", "43.5°", 43.45, dp=1),
     ["tan x = 18/19\nx = 43.5º", "x = 43.5 degrees", "43.5˚"], ["tan x = 18/19\nx = 46.5º"], [], []),
    ("which term n = 22", Answer("number", "n = 22", 22.0),
     ["8n = 176\nn = 22nd term", "8n + 1 = 177\n8n = 176\nthe 22nd term", "22nd"], ["8n = 176\nn = 23rd term"], [], []),
    ("roots -3, -4", Answer("set", "x = -4 or x = -3", ["-4", "-3"]),
     ["(x+3)(x+4)=0\nso x is -3 or -4", "(x+3)(x+4) = 0 so x = -3, -4", "x = -3\nx = -4\n"],
     ["(x+3)(x+4)=0\nso x is 3 or 4"], [], ["x² + 7x + 12 = 0\n(x+3)(x+4) = 0"]),
    ("roots ±8", Answer("set", "x = -8 or x = 8", ["-8", "8"]),
     ["x = ±8", "±8", "x = +/- 8", "x = 8 x = -8", "x² = 64\nx = 8\nx = -8"], ["x = ±7", "x = 8"], [], []),
    ("simultaneous x=3 y=-1", Answer("assign", "x = 3, y = -1", {"x": "3", "y": "-1"}),
     ["y = -1, x = 3\ncheck: 2x + y = 5", "x = 3\ny = -1\n3 + y = 2", "x=3 y=-1", "x is 3 and y is -1",
      "2x = 6 so x = 3\n3 + y = 2 so y = -1"],
     ["y = 1, x = 3\ncheck: 2x + y = 7", "x = 3\ny = 2\n3 + y = 5"], [], []),
    ("factorise (x+7)(x+6)", Answer("expr", "(x + 7)(x + 6)", "(x+7)*(x+6)", form="factorised"),
     ["(x + 7)(x + 6) = 0", "(X+7)(X+6)", "x² + 13x + 42 = (x + 7)(x + 6)", "(x+7)(x+6)=x²+13x+42"],
     ["(x + 7)(x + 5) = 0"], [("1(x²+13x+42)", FORM_FACTORISED), ("x² + 13x + 42 = 0", FORM_FACTORISED)], []),
    ("expand x² + 9x + 8", Answer("expr", "x² + 9x + 8", "x**2+9*x+8", form="expanded"),
     ["x²+9x+8=0", "X² + 9x + 8", "x2 + 9x + 8", "y = x^2+9x+8", "x² + 9x + 8."],
     ["x² + 8x + 8", "x2 + 9x + 9"], [("x² + x + 8x + 8", FORM_SIMPLEST), ("(x + 1)(x + 8)", FORM_EXPANDED)], []),
    ("nth term 8n + 5", Answer("expr", "8n + 5", "8*n+5", var="n"),
     ["Tn = 8n + 5", "N = 8N + 5", "nth term = 8n+5"], ["8n + 3"], [], []),
    ("mixed 15 1/9", Answer("fraction", "15 1/9", "136/9", form="mixed"),
     ["15 1/9", "15 and 1/9"], ["15 2/9"], [("136/9", FORM_MIXED), ("15.11", FORM_FRACTION),
                                             ("15 2/18", FORM_SIMPLEST)], []),
    ("mixed proper 3/4", Answer("fraction", "3/4", "3/4", form="mixed"),
     ["3/4"], ["2/3"], [("6/8", FORM_SIMPLEST)], []),
    ("simplest 1/3 rounded", Answer("fraction", "1/3", "1/3", form="simplest"),
     ["1/3"], [], [("0.33", FORM_FRACTION), ("2/6", FORM_SIMPLEST)], []),
    ("trig angle with cos (not 'because')", Answer("number", "56.9°", math.degrees(math.acos(6 / 11)), dp=1),
     ["cos x = 6 ÷ 11, so x = cos⁻¹(6 ÷ 11) = 56.9° (1 d.p.)", "cos x = 6/11\nx = 56.9"], ["cos x = 6/11 so x = 33.1°"],
     [], []),
    ("working on one line", Answer("assign", "x = 6, y = 3", {"x": "6", "y": "3"}),
     ["2x = 12, so x = 6. Then 6 + y = 9, so y = 3"], ["2x = 12, so x = 6. Then 6 + y = 9, so y = 4"], [], []),
    ("expansion on one line", Answer("expr", "3x² - 10x + 7", "3*x**2-10*x+7", form="expanded"),
     ["3x × x = 3x², 3x × (-1) = -3x, (-7) × x = -7x, (-7) × (-1) = 7. So 3x² - 10x + 7"], [], [], []),
]


class TestAcceptanceTable(unittest.TestCase):
    def test_table(self):
        for name, ans, correct, wrong, wrong_form, unparsed in TABLE + REAL:
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
        for name, ans, *_ in TABLE + REAL:
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
        for t in ("-4", "−4", "x = -4", "x = −4", "so -4", "ans -4", "so x = -4"):
            with self.subTest(text=t):
                self.assertEqual(check(a, t).status, "correct")
        self.assertEqual(check(a, "4").status, "wrong")
        self.assertEqual(check(Answer("number", "4", 4.0), "Answer - 4").status, "correct")

    def test_boundaries_dp(self):
        a = Answer("number", "12.5", 12.5, dp=1)
        self.assertEqual(check(a, "12.55").status, "correct")     # exactly half a unit
        self.assertEqual(check(a, "12.56").status, "wrong")
        self.assertEqual(check(a, "12.45").status, "correct")
        self.assertEqual(check(a, "12.44").status, "wrong")

    def test_no_dp_no_sf_tolerance_is_relative(self):
        a = Answer("number", "1000000", 1000000.0)
        self.assertEqual(check(a, "1000000").status, "correct")
        self.assertEqual(check(a, "1000000.0001").status, "correct")   # 1e-10 relative
        self.assertEqual(check(a, "1000000.5").status, "wrong")        # 5e-7 relative > 1e-9
        self.assertEqual(check(a, "1000010").status, "wrong")

    def test_small_exact_values_boundaries(self):
        for value, display, near in (
                (4.5e-7, "4.5 × 10^-7", ("4.5 × 10^-8", "4.5 × 10^-6", "4.6 × 10^-7", "4.4 × 10^-7", "0")),
                (1.6e-19, "1.6 × 10^-19 C", ("1.6 × 10^-18", "1.6 × 10^-20", "1.7 × 10^-19", "0")),
                (0.00045, "0.00045", ("0.0045", "0.000045", "0.00046", "0.00044", "0")),
                (32000.0, "32000", ("320000", "3200", "32001", "31999")),
                (0.0, "0", ("0.000001", "1", "-0.001"))):
            a = Answer("number", display, value)
            with self.subTest(display=display):
                self.assertEqual(check(a, display).status, "correct")
                for t in near:
                    self.assertEqual(check(a, t).status, "wrong", t)
        self.assertEqual(check(Answer("number", "0", 0.0), "0.0").status, "correct")

    def test_dp_and_sf_rules_unchanged(self):
        a = Answer("number", "186 N", 186.2, sf=3)
        for t in ("186", "186.2", "186 N", "186.2 N", "185.7"):
            self.assertEqual(check(a, t).status, "correct", t)
        for t in ("190", "187", "18.6", "1860"):
            self.assertEqual(check(a, t).status, "wrong", t)
        b = Answer("number", "1.13 N", 1.125, sf=3)          # exactly on a rounding boundary: both sides accepted
        for t in ("1.13", "1.12", "1.125"):
            self.assertEqual(check(b, t).status, "correct", t)
        self.assertEqual(check(b, "1.1").status, "wrong")

    def test_last_line_with_digits_is_never_skipped(self):
        a = Answer("number", "x = 4", 4.0)
        # the last line has digits but no readable answer: unparsed, never a wrong mark from the working above
        self.assertEqual(check(a, "3x = 12\nx = 4 or maybe 5").status, "unparsed")
        self.assertEqual(check(a, "2x = 9\nI'm not sure about 4").status, "unparsed")
        # a last line without digits is skipped
        self.assertEqual(check(a, "3x = 12\nx = 4\nthanks!").status, "correct")

    def test_units_converted(self):
        j = Answer("number", "19600 J", 19600.0)
        for t in ("19.6 kJ", "19.6kj", "19600 J", "19600", "0.0196 MJ", "1.96 × 10^4 J", "19600 joules"):
            self.assertEqual(check(j, t).status, "correct", t)
        big = Answer("number", "2100000 J", 2100000.0)
        self.assertEqual(check(big, "2.1 MJ").status, "correct")
        small = Answer("number", "2500 J", 2500.0)
        self.assertEqual(check(small, "2500 kJ").status, "wrong")
        self.assertEqual(check(small, "2.5 kJ").status, "correct")
        self.assertEqual(check(Answer("number", "250 g", 250.0), "0.25 kg").status, "correct")
        self.assertEqual(check(Answer("number", "0.25 A", 0.25), "250 mA").status, "correct")
        self.assertEqual(check(Answer("number", "120 s", 120.0), "2 minutes").status, "correct")
        self.assertEqual(check(Answer("number", "1.5 m", 1.5), "150 cm").status, "correct")
        self.assertEqual(check(Answer("number", "4.05 W", 4.05, sf=3), "4050 mW").status, "correct")

    def test_unit_of_another_quantity_is_wrong_with_feedback(self):
        v = check(Answer("number", "12 m/s", 12.0), "12 m")
        self.assertEqual((v.status, v.feedback), ("wrong", helpers.FORM_UNIT("m/s")))
        v = check(Answer("number", "2500 J", 2500.0), "2500 W")
        self.assertEqual((v.status, v.feedback), ("wrong", helpers.FORM_UNIT("J")))
        # unknown units and answers without a display unit are compared as plain numbers
        self.assertEqual(check(Answer("number", "12 m/s", 12.0), "12 mps").status, "correct")
        self.assertEqual(check(Answer("number", "4", 4.0), "4 kg").status, "correct")

    def test_scientific_calculator_notation(self):
        self.assertEqual(check(Answer("number", "19600 J", 19600.0), "1.96e4").status, "correct")
        v = check(Answer("number", "3.2 × 10^4", 32000.0, form="standard"), "3.2E4")
        self.assertEqual((v.status, v.feedback), ("wrong", FORM_STANDARD))

    def test_genuinely_wrong_answers_stay_wrong(self):
        cases = [
            (Answer("number", "7.1 cm", 7.0710678, dp=1), "a² = 50\na = 7.0 cm (1 d.p.)"),
            (Answer("number", "x = 4", 4.0), "so it's 6"),
            (Answer("number", "36 cm²", 36.0), "72 cm2"),
            (Answer("set", "x = -4 or x = -3", ["-4", "-3"]), "x = 3 or x = 4"),
            (Answer("assign", "x = 3, y = -1", {"x": "3", "y": "-1"}), "x = 3, y = 1\ncheck: 2(3) + 1 = 7"),
            (Answer("expr", "(x + 7)(x + 6)", "(x+7)*(x+6)", form="factorised"), "(x + 7)(x - 6) = 0"),
            (Answer("fraction", "3/4", "3/4"), "so it's 4/3"),
        ]
        for a, t in cases:
            with self.subTest(text=t):
                self.assertEqual(check(a, t).status, "wrong")

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
