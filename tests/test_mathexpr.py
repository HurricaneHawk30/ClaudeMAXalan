import math
import time
import unittest

import helpers  # noqa: F401  (puts the repo root on sys.path)
from tutor.content import mathexpr as mx
from tutor.content.mathexpr import (ExprError, parse, evaluate, equivalent, is_expanded, is_factorised,
                                   is_simplified)


def val(s, x=3.0, var="x"):
    return evaluate(parse(s, var), {var: x})


class TestEvaluate(unittest.TestCase):
    def test_implicit_multiplication(self):
        cases = [
            ("2x", 3, 6), ("3(x+1)", 3, 12), ("(x+1)(x+2)", 3, 20), ("x(x+1)", 3, 12),
            ("x²", 3, 9), ("2x²", 3, 18), ("-x", 3, -3), ("x³", 2, 8), ("(x+1)x", 3, 12),
            ("(x+1)2", 3, 8), ("(x+1)(x+2)(x+3)", 1, 24), ("5x + x^2 + 6", 2, 20),
        ]
        for s, x, want in cases:
            with self.subTest(expr=s):
                self.assertAlmostEqual(val(s, x), want)

    def test_operators_and_unicode(self):
        cases = [("x^2", 3, 9), ("x**2", 3, 9), ("2×x", 3, 6), ("2·x", 3, 6), ("x÷2", 3, 1.5),
                 ("x−1", 3, 2), ("+x", 3, 3), ("2*x+1", 3, 7), ("x/2", 3, 1.5), ("x**10", 1, 1)]
        for s, x, want in cases:
            with self.subTest(expr=s):
                self.assertAlmostEqual(val(s, x), want)

    def test_pi(self):
        self.assertAlmostEqual(evaluate(parse("2π"), {"x": 0.0}), 2 * math.pi)
        self.assertAlmostEqual(evaluate(parse("pi*x"), {"x": 2.0}), 2 * math.pi)

    def test_other_variable(self):
        self.assertAlmostEqual(val("3n+2", 4, "n"), 14)
        with self.assertRaises(ExprError):
            parse("3x+2", "n")

    def test_unknown_letters_rejected(self):
        for s in ("y+1", "x+y", "abc", "sin(x)", "abs(x)"):
            with self.subTest(expr=s):
                with self.assertRaises(ExprError):
                    parse(s)

    def test_syntax_errors(self):
        for s in ("", "x+", "(x", "x)", "x ++* 2", "2 3 4 +"):
            with self.subTest(expr=s):
                with self.assertRaises(ExprError):
                    evaluate(parse(s), {"x": 1.0})

    def test_division_by_zero(self):
        with self.assertRaises(ExprError):
            evaluate(parse("1/x"), {"x": 0.0})

    def test_exponent_limit_boundary(self):
        self.assertAlmostEqual(val("x**10", 2), 1024)
        with self.assertRaises(ExprError):
            evaluate(parse("x**11"), {"x": 2.0})


class TestAttacks(unittest.TestCase):
    def assert_rejected_fast(self, s):
        t = time.time()
        with self.assertRaises(ExprError):
            evaluate(parse(s), {"x": 2.0})
        self.assertLess(time.time() - t, 1.0)

    def test_attack_inputs(self):
        attacks = [
            "__import__('os')", "x**99999", "9**9**9", "x" * 1000, "(" * 500, "((((" * 100 + "x" + "))))" * 100,
            "x.real", "10**10**10", "lambda: 1", "x if 1 else 2", "[x]", "x;1", "exec('1')",
            "__import__('os').system('true')", "'a'*99999999", "x" + "+x" * 150, "(x)" * 150,
        ]
        for s in attacks:
            with self.subTest(expr=s[:40]):
                self.assert_rejected_fast(s)

    def test_length_limit_boundary(self):
        ok = "+".join(["x"] * 50)           # 99 chars, 99 nodes at most
        self.assertAlmostEqual(val(ok, 1), 50)
        with self.assertRaises(ExprError):
            parse("1+" * 120 + "1")         # 241 chars


class TestEquivalent(unittest.TestCase):
    def test_equivalent_true(self):
        cases = [("(x+2)(x+3)", "x^2+5x+6"), ("x²+5x+6", "x**2+5*x+6"), ("(x+1)^2", "x^2+2x+1"),
                 ("(2+x)(3+x)", "(x+3)(x+2)"), ("x/x", "1"), ("2(x+1)", "2x+2"), ("-(x-1)", "1-x")]
        for a, b in cases:
            with self.subTest(a=a, b=b):
                self.assertIs(equivalent(a, b), True)
                self.assertIs(equivalent(b, a), True)

    def test_equivalent_false(self):
        cases = [("x^2+5x+6", "x^2+6x+5"), ("x^2+5x", "x^2+5x+6"), ("(x-2)(x-3)", "(x+2)(x+3)"),
                 ("x", "x+0.001"), ("3x", "x+3")]
        for a, b in cases:
            with self.subTest(a=a, b=b):
                self.assertIs(equivalent(a, b), False)

    def test_none_when_unparsable(self):
        self.assertIsNone(equivalent("x+", "x"))
        self.assertIsNone(equivalent("x", "y"))
        self.assertIsNone(equivalent("", "x"))
        self.assertIsNone(equivalent("__import__('os')", "x"))

    def test_other_var(self):
        self.assertIs(equivalent("3n+2", "2+3n", "n"), True)
        self.assertIs(equivalent("3n+2", "3n", "n"), False)
        self.assertIsNone(equivalent("3x+2", "3n+2", "n"))

    def test_too_few_valid_points_is_not_equivalent(self):
        # 1/(x-x) fails at every point, so there are < 3 valid points
        self.assertIsNot(equivalent("1/(x-x)", "1/(x-x)"), True)

    def test_points_constant(self):
        self.assertEqual(tuple(mx.POINTS), (-2.3, -1.1, 0.7, 1.9, 3.4, 5.6))


class TestForms(unittest.TestCase):
    def test_is_expanded(self):
        yes = ["x^2+5x+6", "3x", "x^2", "5x+x^2+6", "2x+2", "x² + 5x + 6"]
        no = ["(x+2)(x+3)", "2(x+1)", "x(x+1)", "(x+1)^2", "3(x-4)"]
        for s in yes:
            with self.subTest(expr=s):
                self.assertTrue(is_expanded(s))
        for s in no:
            with self.subTest(expr=s):
                self.assertFalse(is_expanded(s))

    def test_is_factorised(self):
        yes = ["(x+2)(x+3)", "x(x+1)", "(x+1)^2", "-(x+1)(x+2)", "2(x+1)", "(x-5)(x+5)", "(x+3)²",
               "2(x+3)(x+4)", "(2x+3)(x-4)"]
        no = ["x^2+5x+6", "x^2", "3x", "x+1", "x^2-25", "1(x^2+13x+42)", "2(x^2+5x+6)", "(x^2+13x+42)·1",
              "-(x^2+5x+6)", "x·x"]
        for s in yes:
            with self.subTest(expr=s):
                self.assertTrue(is_factorised(s))
        for s in no:
            with self.subTest(expr=s):
                self.assertFalse(is_factorised(s))

    def test_is_simplified(self):
        yes = ["x^2+5x+6", "5x + x^2 + 6", "6+5x+x²", "x²", "3x", "(x+2)(x+3)", "2x² - 3x"]
        no = ["x² + x + 8x + 8", "x^2+3x+2x+6", "x + x", "x² + 5x + 4 + 2", "2x·x + x²"]
        for s in yes:
            with self.subTest(expr=s):
                self.assertTrue(is_simplified(s))
        for s in no:
            with self.subTest(expr=s):
                self.assertFalse(is_simplified(s))

    def test_parse_is_cached_and_still_safe(self):
        self.assertIs(parse("x^2+1"), parse("x^2+1"))
        for bad in (None, 5, ["x"]):
            with self.assertRaises(ExprError):
                parse(bad)
        self.assertIsNone(equivalent(None, "x"))

    def test_forms_with_other_var(self):
        self.assertTrue(is_expanded("3n+2", "n"))
        self.assertTrue(is_factorised("(n+1)(n+2)", "n"))


if __name__ == "__main__":
    unittest.main()
