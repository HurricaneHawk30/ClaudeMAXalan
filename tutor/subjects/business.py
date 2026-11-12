"""Business (GCSE, Years 10–11): docs/ARCHITECTURE_V2.md section 5.4.

Four bank skills live in ``packs/business.json``; this module adds the generator skill
``business.finance_maths`` ("Business calculations": revenue / total cost → gross or net
profit → break-even output (rounded up) → profit margins (1 d.p.) → ARR, closing cash
balance or margin of safety) and registers the subject.

Formulas that exam boards word differently (net profit, ARR) are stated in the question.
Every generator is pure: ``generate(level, seed)`` uses only ``random.Random(seed)``.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction

from ..content.fmt import fmt_dp, retry
from ._social import (
    Draft, gbp, gen_skill, money_answer, money_mistake, num, ok_round, pct_answer, pct_mistake,
    plain_answer, plain_mistake, q, register_subject,
)

SUBJECT_ID = "business"
TITLE = "Business"
ORDER = 46

# (business, product plural, product singular, price range in pennies, monthly quantity range,
#  one-word unit for answers)
_BUSINESSES = (
    ("bakery", "cakes", "cake", 800, 3000, 100, 2000, "cakes"),
    ("phone case company", "phone cases", "phone case", 800, 2500, 200, 5000, "cases"),
    ("candle maker", "candles", "candle", 400, 1800, 200, 4000, "candles"),
    ("bike shop", "bikes", "bike", 15000, 60000, 10, 200, "bikes"),
    ("skateboard maker", "skateboards", "skateboard", 3000, 12000, 20, 600, "skateboards"),
    ("printing firm", "posters", "poster", 300, 1500, 300, 6000, "posters"),
    ("juice company", "bottles of juice", "bottle", 150, 450, 1000, 20000, "bottles"),
)


def _p(pennies: int) -> str:
    return gbp(Fraction(pennies, 100), pennies=True)


def _biz(r: random.Random):
    """A business with a realistic price, variable cost (20–70% of price) and monthly sales."""
    name, many, one, plo, phi, qlo, qhi, word = r.choice(_BUSINESSES)
    step = 100 if phi >= 10000 else 5
    price = r.randrange(plo // step, phi // step + 1) * step
    vc = r.randrange(max(1, price // (5 * step)), max(2, price * 7 // (10 * step)) + 1) * step
    vc = min(vc, price - step)
    qstep = 10 if qhi >= 1000 else 5
    qty = r.randrange(qlo // qstep, qhi // qstep + 1) * qstep
    return name, many, one, price, vc, qty, word


# ---------------------------------------------------------------- L1 revenue / total cost

def _bf_1(rng: random.Random) -> Draft:
    name, many, one, price, vc, qty, _word = _biz(rng)
    if rng.random() < 0.5:
        rev = Fraction(price * qty, 100)
        text = (f"A {name} sells {num(qty)} {many} in a month at {_p(price)} each. Calculate its revenue "
                f"for the month.")
        return q(text, money_answer(rev),
                 f"Revenue = selling price × quantity sold = {_p(price)} × {num(qty)} = {gbp(rev)}",
                 "Revenue = selling price × number sold",
                 [money_mistake(Fraction(price, 100) + qty, "Multiply the price by the quantity — don't add them")])
    fc = rng.randrange(10, 400) * 50
    tvc = Fraction(vc * qty, 100)
    tc = fc + tvc
    text = (f"A {name} has fixed costs of {gbp(fc)} a month. Each {one} has a variable cost of {_p(vc)}. "
            f"It makes {num(qty)} {many} in a month. Calculate its total costs for the month.")
    return q(text, money_answer(tc),
             f"Total variable costs = {_p(vc)} × {num(qty)} = {gbp(tvc)}. Total costs = {gbp(fc)} + "
             f"{gbp(tvc)} = {gbp(tc)}",
             "Total costs = fixed costs + total variable costs",
             [money_mistake(tvc, "That's only the variable costs — add the fixed costs too"),
              money_mistake(fc + Fraction(vc, 100), "Multiply the variable cost per item by the number made, "
                                                   "then add the fixed costs")])


# ---------------------------------------------------------------- L2 gross / net profit

def _bf_2(rng: random.Random) -> Draft:
    name = rng.choice(_BUSINESSES)[0]

    def pick(r: random.Random):
        rev = r.randrange(40, 2000) * 100
        cos = rev * r.randrange(25, 70) // 100 // 50 * 50
        gp = rev - cos
        exp = gp * r.randrange(20, 90) // 100 // 50 * 50
        if cos <= 0 or exp <= 0 or gp - exp <= 0:
            return None
        return rev, cos, exp
    rev, cos, exp = retry(pick, rng)
    gp, np_ = rev - cos, rev - cos - exp
    if rng.random() < 0.5:
        text = (f"In one year, a {name} had revenue of {gbp(rev)}, cost of sales of {gbp(cos)} and other "
                f"operating expenses of {gbp(exp)}. Calculate its gross profit. Use gross profit = revenue − "
                f"cost of sales.")
        return q(text, money_answer(gp),
                 f"Gross profit = {gbp(rev)} − {gbp(cos)} = {gbp(gp)}",
                 "Gross profit only takes away the cost of sales",
                 [money_mistake(np_, "That's net profit — gross profit only takes away the cost of sales"),
                  money_mistake(rev - exp, "Gross profit takes away the cost of sales, not the other expenses")])
    text = (f"In one year, a {name} had revenue of {gbp(rev)}, cost of sales of {gbp(cos)}, and other "
            f"operating expenses and interest of {gbp(exp)} in total. Calculate its net profit. Use net profit = "
            f"gross profit − other operating expenses and interest.")
    return q(text, money_answer(np_),
             f"Gross profit = {gbp(rev)} − {gbp(cos)} = {gbp(gp)}. Net profit = {gbp(gp)} − {gbp(exp)} = {gbp(np_)}",
             "Find gross profit first (revenue − cost of sales)",
             [money_mistake(gp, "That's gross profit — now take away the other operating expenses and interest"),
              money_mistake(rev - exp, "You also need to take away the cost of sales")])


# ---------------------------------------------------------------- L3 break-even (rounded up)

def _bf_3(rng: random.Random) -> Draft:
    def pick(r: random.Random):
        name, many, one, price, vc, qty, word = _biz(r)
        contrib = price - vc
        fc = max(500, contrib * qty * r.randrange(40, 120) // 100 // 10000 * 100)
        be = Fraction(fc * 100, contrib)
        n = math.ceil(be)
        if not 10 <= n <= 30000:
            return None
        return name, many, one, price, vc, contrib, fc, be, n, word
    name, many, one, price, vc, contrib, fc, be, n, word = retry(pick, rng)
    exact = be.denominator == 1
    text = (f"A {name} sells {many} for {_p(price)} each. The variable cost of each {one} is {_p(vc)} and "
            f"its fixed costs are {gbp(fc)} a month. Calculate its break-even output. Give your answer as a "
            f"whole number of {many}, rounding up if needed.")
    shown = num(n)
    sol = (f"Contribution per {one} = {_p(price)} − {_p(vc)} = {_p(contrib)}. Break-even = {gbp(fc)} ÷ "
           f"{_p(contrib)} = " + (f"{shown}" if exact else f"{fmt_dp(be, 2)}…, rounded up to {shown}")
           + f" {many}")
    ms = [plain_mistake(math.ceil(Fraction(fc * 100, price)), "Divide fixed costs by the contribution per item "
                                                             "(price − variable cost), not by the price", word),
          plain_mistake(math.ceil(Fraction(fc * 100, vc)), "Divide by the contribution per item (price − "
                                                          "variable cost), not by the variable cost", word)]
    if not exact:
        ms.append(plain_mistake(n - 1, f"Round up: at {num(n - 1)} {many} the contribution would not quite cover "
                                       f"the fixed costs", word))
    return q(text, plain_answer(n, word), sol,
             "Work out the contribution per item first: selling price − variable cost", ms)


# ---------------------------------------------------------------- L4 profit margins (1 d.p.)

def _bf_4(rng: random.Random) -> Draft:
    name = rng.choice(_BUSINESSES)[0]
    kind = rng.choice(("gpm", "gpm2", "npm", "npm2"))

    def pick(r: random.Random):
        rev = r.randrange(50, 3000) * 100
        cos = rev * r.randrange(25, 75) // 100 // 10 * 10
        gp = rev - cos
        exp = gp * r.randrange(20, 90) // 100 // 10 * 10
        np_ = gp - exp
        if cos <= 0 or exp <= 0 or np_ <= 0:
            return None
        g, n_ = Fraction(100 * gp, rev), Fraction(100 * np_, rev)
        if g.denominator == 1 or n_.denominator == 1 or not ok_round(g, 1) or not ok_round(n_, 1):
            return None
        if fmt_dp(g, 1) == fmt_dp(n_, 1):
            return None
        return rev, cos, gp, exp, np_, g, n_
    rev, cos, gp, exp, np_, g, n_ = retry(pick, rng)
    tail = "Give your answer to 1 decimal place."
    if kind == "gpm":
        text = (f"A {name} had revenue of {gbp(rev)} and gross profit of {gbp(gp)}. Calculate its gross profit "
                f"margin. Use gross profit margin = gross profit ÷ revenue × 100. {tail}")
        sol = f"GPM = {gbp(gp)} ÷ {gbp(rev)} × 100 = {fmt_dp(g, 3)}… = {fmt_dp(g, 1)}%"
        ans, ms = pct_answer(g, 1), [pct_mistake(Fraction(100 * gp, cos), "Divide by revenue, not by the cost "
                                                                           "of sales", dp=1)]
        hint = "Divide gross profit by revenue, then multiply by 100"
    elif kind == "gpm2":
        text = (f"A {name} had revenue of {gbp(rev)} and cost of sales of {gbp(cos)}. Calculate its gross "
                f"profit margin. Use gross profit margin = gross profit ÷ revenue × 100. {tail}")
        sol = (f"Gross profit = {gbp(rev)} − {gbp(cos)} = {gbp(gp)}. GPM = {gbp(gp)} ÷ {gbp(rev)} × 100 = "
               f"{fmt_dp(g, 1)}%")
        ans = pct_answer(g, 1)
        ms = [pct_mistake(Fraction(100 * cos, rev), "That's cost of sales as a percentage of revenue — use gross "
                                                    "profit (revenue − cost of sales)", dp=1),
              pct_mistake(Fraction(100 * gp, cos), "Divide by revenue, not by the cost of sales", dp=1)]
        hint = "Find gross profit first: revenue − cost of sales"
    elif kind == "npm":
        text = (f"A {name} had revenue of {gbp(rev)}, gross profit of {gbp(gp)} and net profit of {gbp(np_)}. "
                f"Calculate its net profit margin. Use net profit margin = net profit ÷ revenue × 100. {tail}")
        sol = f"NPM = {gbp(np_)} ÷ {gbp(rev)} × 100 = {fmt_dp(n_, 3)}… = {fmt_dp(n_, 1)}%"
        ans = pct_answer(n_, 1)
        ms = [pct_mistake(g, "That's the gross profit margin — use net profit", dp=1),
              pct_mistake(Fraction(100 * np_, gp), "Divide by revenue, not by gross profit", dp=1)]
        hint = "Divide net profit by revenue, then multiply by 100"
    else:
        text = (f"A {name} had revenue of {gbp(rev)}, cost of sales of {gbp(cos)}, and other operating expenses "
                f"and interest of {gbp(exp)}. Calculate its net profit margin. Use net profit = revenue − cost of "
                f"sales − other operating expenses and interest, and net profit margin = net profit ÷ revenue × "
                f"100. {tail}")
        sol = (f"Net profit = {gbp(rev)} − {gbp(cos)} − {gbp(exp)} = {gbp(np_)}. NPM = {gbp(np_)} ÷ {gbp(rev)} × "
               f"100 = {fmt_dp(n_, 1)}%")
        ans = pct_answer(n_, 1)
        ms = [pct_mistake(g, "That's the gross profit margin — take away the expenses and interest too", dp=1)]
        hint = "Work out net profit first, then divide it by revenue"
    return q(text, ans, sol, hint, ms)


# ---------------------------------------------------------------- L5 ARR / closing balance / margin of safety

def _arr(rng: random.Random) -> Draft:
    name = rng.choice(_BUSINESSES)[0]

    def pick(r: random.Random):
        cost = r.randrange(10, 300) * 1000
        years = r.randrange(3, 7)
        total = cost + r.randrange(1, 40) * 500 * years
        avg = Fraction(total - cost, years)
        arr = avg / cost * 100
        if not ok_round(arr, 1) or arr >= 60:
            return None
        return cost, years, total, avg, arr
    cost, years, total, avg, arr = retry(pick, rng)
    asset = rng.choice(("a new machine", "a delivery van", "new computer equipment", "new packing equipment"))
    text = (f"A {name} buys {asset} for {gbp(cost)}. Over its {years}-year life, it is expected to bring in "
            f"total returns of {gbp(total)}. Calculate the average rate of return (ARR). Use average annual "
            f"profit = (total returns − cost) ÷ number of years, and ARR = average annual profit ÷ cost × 100. "
            f"Give your answer to 1 decimal place.")
    sol = (f"Total profit = {gbp(total)} − {gbp(cost)} = {gbp(total - cost)}. Average annual profit = "
           f"{gbp(total - cost)} ÷ {years} = {gbp(avg)}. ARR = {gbp(avg)} ÷ {gbp(cost)} × 100 = {fmt_dp(arr, 1)}%")
    return q(text, pct_answer(arr, 1), sol,
             "First take the cost away from the total returns, then share the profit over the years",
             [pct_mistake(Fraction(total, years) / cost * 100, "Take the cost of the investment away from the "
                                                              "total returns before dividing by the years", dp=1),
              pct_mistake(Fraction(total - cost, cost) * 100, f"Divide the total profit by {years} years to get "
                                                             "the average annual profit first", dp=1),
              pct_mistake(avg / total * 100, "Divide the average annual profit by the cost of the investment",
                          dp=1)])


def _closing(rng: random.Random) -> Draft:
    name = rng.choice(_BUSINESSES)[0]

    def pick(r: random.Random):
        opening = r.randrange(-40, 120) * 100
        sales = r.randrange(40, 400) * 100
        other_in = r.randrange(0, 30) * 100
        wages = r.randrange(10, 150) * 100
        rent = r.randrange(5, 40) * 100
        materials = r.randrange(10, 200) * 100
        inflow, outflow = sales + other_in, wages + rent + materials
        closing = opening + inflow - outflow
        if closing == 0 or inflow == outflow or opening == 0:
            return None
        if closing == opening - inflow + outflow:
            return None
        return opening, sales, other_in, wages, rent, materials, inflow, outflow, closing
    opening, sales, other_in, wages, rent, materials, inflow, outflow, closing = retry(pick, rng)
    open_txt = (f"an opening balance of {gbp(opening)}" if opening > 0 else
                f"an opening balance of {gbp(opening)} (an overdraft)")
    ins = f"cash sales of {gbp(sales)}" + (f" and other income of {gbp(other_in)}" if other_in else "")
    text = (f"A {name} starts the month with {open_txt}. During the month it receives {ins}. It pays wages of "
            f"{gbp(wages)}, rent of {gbp(rent)} and {gbp(materials)} for materials. Calculate its closing balance "
            f"for the month. If the balance is negative, include the minus sign.")
    net = inflow - outflow
    sol = (f"Net cash flow = {gbp(inflow)} − {gbp(outflow)} = {gbp(net)}. Closing balance = opening balance + net "
           f"cash flow = {gbp(opening)} + ({gbp(net)}) = {gbp(closing)}")
    if net >= 0:
        sol = sol.replace(f"+ ({gbp(net)})", f"+ {gbp(net)}")
    return q(text, money_answer(closing), sol,
             "Work out the net cash flow (inflows − outflows) first, then add it to the opening balance",
             [money_mistake(net, "That's the net cash flow — add it to the opening balance"),
              money_mistake(opening - net, "Inflows are added and outflows are taken away — check the signs"),
              money_mistake(-closing, "Check the sign of your answer")])


def _mos(rng: random.Random) -> Draft:
    def pick(r: random.Random):
        name, many, one, price, vc, qty, word = _biz(r)
        contrib = price - vc
        unit = 100 if qty >= 1000 else 10
        be = qty * r.randrange(40, 90) // 100 // unit * unit
        fc = Fraction(contrib * be, 100)
        if be < 10 or fc.denominator != 1 or fc < 200:
            return None
        sales = be + max(5, qty * r.randrange(5, 60) // 100 // 5 * 5)
        return name, many, one, price, vc, contrib, be, int(fc), sales, word
    name, many, one, price, vc, contrib, be, fc, sales, word = retry(pick, rng)
    text = (f"A {name} sells {many} for {_p(price)} each. The variable cost of each {one} is {_p(vc)} and its "
            f"fixed costs are {gbp(fc)} a month. It sells {num(sales)} {many} a month. Calculate its margin of "
            f"safety in {many}. Use margin of safety = actual sales − break-even output.")
    sol = (f"Contribution = {_p(price)} − {_p(vc)} = {_p(contrib)}. Break-even = {gbp(fc)} ÷ {_p(contrib)} = "
           f"{num(be)}. Margin of safety = {num(sales)} − {num(be)} = {num(sales - be)} {many}")
    return q(text, plain_answer(sales - be, word), sol,
             "Find the break-even output first: fixed costs ÷ contribution per item",
             [plain_mistake(be, "That's the break-even output — now take it away from actual sales", word),
              plain_mistake(sales, "Take the break-even output away from the actual sales", word)])


def _bf_5(rng: random.Random) -> Draft:
    return rng.choice((_arr, _closing, _mos))(rng)


FINANCE_MATHS = gen_skill(
    SUBJECT_ID, "finance_maths", "Business calculations",
    ("break-even point", "break even calculation", "gross profit margin", "net profit margin", "arr",
     "cash flow forecast", "margin of safety"),
    (_bf_1, _bf_2, _bf_3, _bf_4, _bf_5),
    "Write down the formula first, then put the numbers in",
)

ROWS = (
    (("enterprise", "Enterprise & ideas", ("enterprise",)),
     ("marketing", "Marketing", ("marketing",))),
    (("operations_people", "Operations & people", ("operations_people",)),
     ("finance", "Finance", ("finance", "finance_maths"))),
)

SKILL_ORDER = ("enterprise", "marketing", "operations_people", "finance", "finance_maths")


def register(reg) -> None:
    """Register Business: the pack's bank skills plus the generator skill."""
    register_subject(reg, SUBJECT_ID, TITLE, ORDER, ROWS, SKILL_ORDER, [FINANCE_MATHS])
