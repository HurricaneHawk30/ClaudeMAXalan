"""Economics (GCSE, Years 10–11): docs/ARCHITECTURE_V2.md section 5.4.

Four bank skills live in ``packs/economics.json``; this module adds four generator skills
and registers the subject:

- ``economics.elasticity`` "Price elasticity": % change (1 d.p.) → PED from percentages
  (2 d.p.) → PED from prices and quantities → PES → new quantity from PED;
- ``economics.firms_maths`` "Costs, revenue & profit": TR → TC → profit → average cost
  (£, nearest penny) → profit at an output read from a table;
- ``economics.interest`` "Interest & savings": simple → compound (nearest penny) → real
  interest rate → % change of savings → years to reach a target;
- ``economics.macro_maths`` "Macro calculations": inflation from the CPI → GDP growth % →
  real growth → currency conversion (2 d.p.) → balance of trade (with its sign).

Sign conventions are stated in every question (PED: "include the minus sign"; balances and
real rates: "use a minus sign for a deficit / a negative value"). Every formula a GCSE board
might write differently is given in the question. Rates and prices are hypothetical.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction

from ..content import Answer, Mistake
from ..content.fmt import fmt_dp, fmt_num, num_answer, retry
from ._social import (
    Draft, cap, cur, frac, gbp, gen_skill, money_answer, money_mistake, num, ok_round, pct,
    pct_answer, pct_mistake, plain_answer, plain_mistake, q, register_subject,
)

SUBJECT_ID = "economics"
TITLE = "Economics"
ORDER = 44

NAMES = ("Amy", "Ben", "Chloe", "Dev", "Ella", "Finn", "Grace", "Harry", "Isla", "Jack",
         "Leah", "Mia", "Noah", "Omar", "Priya", "Sam", "Tom", "Zara")
# (product, lowest and highest price in pennies)
PRODUCTS = (("cinema tickets", 600, 1500), ("bus tickets", 100, 500), ("cups of coffee", 200, 450),
            ("magazines", 200, 700), ("bags of apples", 100, 400), ("phone cases", 500, 2000),
            ("pizzas", 600, 1600), ("concert tickets", 2000, 8000), ("sandwiches", 200, 600),
            ("gym passes", 500, 1500))
# (good, unit plural, unit singular, lowest and highest price per unit in pennies)
GOODS = (("strawberries", "punnets", "punnet", 100, 400), ("eggs", "boxes", "box", 100, 400),
         ("timber", "planks", "plank", 300, 1500), ("coffee beans", "kilograms", "kilogram", 500, 2000),
         ("wheat", "tonnes", "tonne", 15000, 30000), ("flowers", "bunches", "bunch", 200, 1000))


def _p(pennies: int) -> str:
    """Pennies -> '£2.40' (always 2 d.p. for prices)."""
    return gbp(Fraction(pennies, 100), pennies=True)


def _ped_answer(v: Fraction) -> Answer:
    return num_answer(v, fmt_dp(v, 2), dp=2)


def _ped_mistake(v: Fraction | None, fb: str) -> Mistake | None:
    if v is None:
        return None
    return Mistake(Answer(kind="number", display=fmt_dp(v, 2), value=float(v), dp=2), fb)


def _pn(x) -> str:
    """A number inside a calculation: negatives in brackets, e.g. 3 ÷ (-15)."""
    return f"({fmt_num(x)})" if x < 0 else fmt_num(x)


def _signed_pct(v: Fraction) -> str:
    return ("+" if v > 0 else "") + pct(v)


_PED_RULE = "Use PED = % change in quantity demanded ÷ % change in price."
_PED_ROUND = "Give your answer to 2 decimal places and include the minus sign."
_PES_RULE = "Use PES = % change in quantity supplied ÷ % change in price."


# ======================================================== elasticity

def _el_1(rng: random.Random) -> Draft:
    """Percentage change (1 d.p.), asked as a positive increase or decrease."""
    item, lo, hi = rng.choice(PRODUCTS)
    of_price = rng.random() < 0.5
    up = rng.random() < 0.5

    def pick(r: random.Random):
        if of_price:
            a = r.randrange(lo // 5, hi // 5 + 1) * 5
            d = r.randrange(1, max(2, a // 20)) * 5
        else:
            a = r.randrange(20, 600) * 10
            d = r.randrange(1, a // 30 + 2) * 10
        b = a + d if up else a - d
        if b <= 0:
            return None
        p = Fraction(100 * d, a)
        if p.denominator == 1 or not ok_round(p, 1):
            return None
        by_new = Fraction(100 * d, b)
        if fmt_dp(by_new, 1) == fmt_dp(p, 1):
            return None
        return a, b, d, p, by_new
    a, b, d, p, by_new = retry(pick, rng)
    word = "increase" if up else "decrease"
    if of_price:
        A, B, D = _p(a), _p(b), _p(d)
        text = (f"The price of {item} {'rises' if up else 'falls'} from {A} to {B}. Calculate the "
                f"percentage {word} in price. Give your answer to 1 decimal place.")
        change = Fraction(d, 100)
        ms_change = money_mistake(change, "That's the change in price — divide it by the original price "
                                          "and multiply by 100", pennies=True)
    else:
        A, B, D = num(a), num(b), num(d)
        text = (f"Weekly sales of {item} {'rise' if up else 'fall'} from {A} to {B}. Calculate the "
                f"percentage {word} in quantity demanded. Give your answer to 1 decimal place.")
        ms_change = plain_mistake(d, "That's the actual change — divide it by the original quantity "
                                     "and multiply by 100")
    return q(text, pct_answer(p, 1),
             f"Change = {D}. Percentage {word} = {D} ÷ {A} × 100 = {fmt_dp(p, 3)}… = {fmt_dp(p, 1)}% (1 d.p.)",
             "Find the change first, then divide it by the original value and multiply by 100",
             [pct_mistake(by_new, "Divide the change by the original value (before the change), not the "
                                  "new value", dp=1), ms_change])


def _el_2(rng: random.Random) -> Draft:
    """PED from two percentage changes (2 d.p., with its minus sign)."""
    item = rng.choice(PRODUCTS)[0]
    up = rng.random() < 0.5

    def pick(r: random.Random):
        p = r.randrange(2, 26)
        qq = r.randrange(1, 41)
        if p == qq:
            return None
        v = Fraction(qq, p)
        if not Fraction(1, 10) <= v <= 4 or not ok_round(v, 2) or not ok_round(1 / v, 2):
            return None
        if fmt_dp(v, 2) == fmt_dp(1 / v, 2):
            return None
        return p, qq
    p, qq = retry(pick, rng)
    if up:
        text = (f"The price of {item} rises by {p}%. As a result, the quantity demanded falls by {qq}%. "
                f"Calculate the price elasticity of demand (PED). {_PED_RULE} {_PED_ROUND}")
        dq, dp_ = -qq, p
    else:
        text = (f"The price of {item} falls by {p}%. As a result, the quantity demanded rises by {qq}%. "
                f"Calculate the price elasticity of demand (PED). {_PED_RULE} {_PED_ROUND}")
        dq, dp_ = qq, -p
    v = Fraction(dq, dp_)
    sol = (f"% change in quantity demanded = {_signed_pct(Fraction(dq))}, % change in price = "
           f"{_signed_pct(Fraction(dp_))}. PED = {dq} ÷ {_pn(dp_)} = {fmt_dp(v, 2)}")
    return q(text, _ped_answer(v), sol,
             "Write each change as a percentage with a + or − sign, then divide quantity by price",
             [_ped_mistake(-v, "PED is negative because price and quantity demanded move in opposite "
                               "directions — include the minus sign"),
              _ped_mistake(1 / v, "You've divided the wrong way round — the % change in quantity demanded "
                                  "goes on top"),
              _ped_mistake(-1 / v, "You've divided the wrong way round — the % change in quantity demanded "
                                   "goes on top")])


def _pq_values(r: random.Random, p_choices: tuple[int, ...], q_max: int, lo: int, hi: int):
    """Price (pennies, multiple of 20, in lo..hi) and quantity (multiple of 100) with whole % changes."""
    a = r.randrange(max(1, lo // 20), hi // 20 + 1) * 20
    p = r.choice(p_choices)
    q0 = r.randrange(2, 101) * 100
    qq = r.randrange(1, q_max + 1)
    return a, p, q0, qq


def _el_3(rng: random.Random) -> Draft:
    """PED from prices and quantities."""
    item, lo, hi = rng.choice(PRODUCTS)
    up = rng.random() < 0.5

    def pick(r: random.Random):
        a, p, q0, qq = _pq_values(r, (5, 10, 15, 20, 25, 30), 60, lo, hi)
        if p == qq or (not up and qq >= 100):
            return None
        v = Fraction(qq, p)
        if not Fraction(1, 5) <= v <= 3 or not ok_round(v, 2) or fmt_dp(v, 2) == fmt_dp(1 / v, 2):
            return None
        return a, p, q0, qq
    a, p, q0, qq = retry(pick, rng)
    da = a * p // 100
    dqty = q0 * qq // 100
    if up:
        b, q1 = a + da, q0 - dqty
        moves = (f"rose from {_p(a)} to {_p(b)}", f"fell from {num(q0)} to {num(q1)}")
        dq, dpc = -qq, p
    else:
        b, q1 = a - da, q0 + dqty
        moves = (f"fell from {_p(a)} to {_p(b)}", f"rose from {num(q0)} to {num(q1)}")
        dq, dpc = qq, -p
    v = Fraction(dq, dpc)
    text = (f"When the price of {item} {moves[0]}, the quantity demanded {moves[1]} a week. "
            f"Calculate the PED. {_PED_RULE} {_PED_ROUND}")
    sol = (f"% change in Qd = {num(q1 - q0)} ÷ {num(q0)} × 100 = {dq}%. % change in price = "
           f"{_p(b - a) if b > a else '-' + _p(a - b)} ÷ {_p(a)} × 100 = {dpc}%. PED = {dq} ÷ {_pn(dpc)} = {fmt_dp(v, 2)}")
    new_base = Fraction(q1 - q0, q1) / Fraction(b - a, b)
    return q(text, _ped_answer(v), sol,
             "Work out the percentage change in quantity demanded and in price, each from its original value",
             [_ped_mistake(-v, "PED is negative because price and quantity demanded move in opposite "
                               "directions — include the minus sign"),
              _ped_mistake(1 / v, "You've divided the wrong way round — the % change in quantity demanded "
                                  "goes on top"),
              _ped_mistake(new_base, "Use the original values (before the change) as the base for each "
                                     "percentage change")])


def _el_4(rng: random.Random) -> Draft:
    """PES from prices and quantities (positive, 2 d.p.)."""
    good, unit_word, one, lo, hi = rng.choice(GOODS)

    def pick(r: random.Random):
        a = r.randrange(lo // 20, hi // 20 + 1) * 20
        p = r.choice((4, 5, 8, 10, 12, 15, 20, 25))
        q0 = r.randrange(2, 101) * 100
        qq = r.randrange(1, 61)
        if p == qq:
            return None
        v = Fraction(qq, p)
        if not Fraction(1, 5) <= v <= 3 or not ok_round(v, 2) or fmt_dp(v, 2) == fmt_dp(1 / v, 2):
            return None
        if (a * p) % 100 or (q0 * qq) % 100:
            return None
        return a, p, q0, qq
    a, p, q0, qq = retry(pick, rng)
    b, q1 = a + a * p // 100, q0 + q0 * qq // 100
    v = Fraction(qq, p)
    text = (f"When the market price of {good} rose from {_p(a)} to {_p(b)} per {one}, the quantity "
            f"supplied rose from {num(q0)} to {num(q1)} {unit_word} a week. Calculate the price "
            f"elasticity of supply (PES). {_PES_RULE} Give your answer to 2 decimal places.")
    new_base = Fraction(q1 - q0, q1) / Fraction(b - a, b)
    sol = (f"% change in Qs = {num(q1 - q0)} ÷ {num(q0)} × 100 = {qq}%. % change in price = "
           f"{_p(b - a)} ÷ {_p(a)} × 100 = {p}%. PES = {qq} ÷ {p} = {fmt_dp(v, 2)}")
    return q(text, _ped_answer(v), sol,
             "Work out both percentage changes from the original values, then divide quantity by price",
             [_ped_mistake(1 / v, "You've divided the wrong way round — the % change in quantity supplied "
                                  "goes on top"),
              _ped_mistake(-v, "PES is positive: price and quantity supplied move in the same direction"),
              _ped_mistake(new_base, "Use the original values (before the change) as the base for each "
                                     "percentage change")])


_PED_VALUES = tuple(Fraction(x) for x in ("-0.2", "-0.3", "-0.4", "-0.5", "-0.6", "-0.8", "-1.2",
                                           "-1.4", "-1.5", "-1.6", "-2", "-2.5"))


def _el_5(rng: random.Random) -> Draft:
    """New quantity demanded from PED and a price change."""
    item = rng.choice(PRODUCTS)[0]
    up = rng.random() < 0.5

    def pick(r: random.Random):
        e = r.choice(_PED_VALUES)
        p = r.choice((4, 5, 6, 8, 10, 12, 15, 20, 25))
        dq = e * (p if up else -p)                    # % change in quantity demanded
        if abs(dq) >= 60:
            return None
        q0 = r.randrange(4, 201) * 50
        q1 = q0 * (1 + dq / 100)
        if q1.denominator != 1 or q1 <= 0:
            return None
        return e, p, dq, q0, int(q1)
    e, p, dq, q0, q1 = retry(pick, rng)
    text = (f"The price elasticity of demand (PED) for {item} is {fmt_num(e)}. The price "
            f"{'rises' if up else 'falls'} by {p}%. Before the change, {num(q0)} {item} were sold each week. "
            f"Calculate the new quantity demanded each week. Use % change in quantity demanded = "
            f"PED × % change in price.")
    change = abs(q1 - q0)
    wrong_dir = q0 * (1 - dq / 100)
    sol = (f"% change in Qd = {fmt_num(e)} × {p if up else _pn(-p)} = {fmt_num(dq)}%. "
           f"{fmt_num(dq)}% of {num(q0)} = {'-' if dq < 0 else '+'}{num(change)}, so the new quantity is {num(q1)}")
    ms = [plain_mistake(change, f"That's the change in quantity — apply it to the original {num(q0)}"),
          plain_mistake(wrong_dir, "Check the direction: a price rise makes quantity demanded fall, and a "
                                   "price fall makes it rise")]
    alt = q0 * (1 + Fraction(p if up else -p) / e / 100)
    if alt > 0 and alt.denominator == 1:
        ms.append(plain_mistake(alt, "Multiply PED by the % change in price — don't divide"))
    return q(text, plain_answer(q1), sol,
             "First work out the percentage change in quantity demanded", ms)


ELASTICITY = gen_skill(
    SUBJECT_ID, "elasticity", "Price elasticity",
    ("price elasticity of demand", "ped", "pes", "elasticity"),
    (_el_1, _el_2, _el_3, _el_4, _el_5),
    "Elasticity compares two percentage changes: quantity on top, price underneath",
)


# ======================================================== firms maths

# (firm, plural, singular, price range in pennies, quantity range, quantity step)
_FIRMS = (("bakery", "loaves", "loaf", 100, 450, 200, 5000, 10),
          ("T-shirt printer", "T-shirts", "T-shirt", 600, 2500, 100, 3000, 10),
          ("juice bar", "smoothies", "smoothie", 250, 650, 200, 4000, 10),
          ("furniture maker", "chairs", "chair", 4000, 20000, 20, 400, 5),
          ("candle maker", "candles", "candle", 300, 1800, 100, 3000, 10),
          ("pottery studio", "mugs", "mug", 500, 2500, 50, 2000, 10),
          ("cake shop", "cakes", "cake", 800, 3500, 50, 1500, 5))
# cheap items priced in pence: (seller, plural, price range in pence)
_PENCE = (("bakery", "bread rolls", 35, 95), ("café", "biscuits", 40, 99),
          ("market stall", "apples", 30, 80), ("tuck shop", "bottles of water", 50, 99))


def _firm(r: random.Random):
    """A firm with a realistic price, variable cost (20–70% of price) and quantity."""
    firm, many, one, plo, phi, qlo, qhi, qstep = r.choice(_FIRMS)
    price = r.randrange(plo // 5, phi // 5 + 1) * 5
    vc = r.randrange(max(1, price // 25), max(2, price * 7 // 50) + 1) * 5
    qty = r.randrange(qlo // qstep, qhi // qstep + 1) * qstep
    fc = r.randrange(10, 400) * 50
    return firm, many, one, price, min(vc, price - 5), qty, fc


def _fm_1(rng: random.Random) -> Draft:
    """Total revenue = price × quantity (sometimes with the price in pence)."""
    if rng.random() < 0.4:
        seller, many, lo, hi = rng.choice(_PENCE)
        pence = rng.randrange(lo, hi + 1)
        qty = rng.randrange(20, 400) * 10
        tr = Fraction(pence * qty, 100)
        text = (f"A {seller} sells {num(qty)} {many} at {pence}p each. Calculate its total revenue "
                f"in pounds.")
        return q(text, money_answer(tr),
                 f"Total revenue = price × quantity = {pence}p × {num(qty)} = {num(pence * qty)}p = {gbp(tr)}",
                 "Total revenue = price × quantity sold — then change pence into pounds",
                 [plain_mistake(pence * qty, "That's in pence — divide by 100 to change it into pounds")])
    firm, many, one, price, vc, qty, fc = _firm(rng)
    tr = Fraction(price * qty, 100)
    text = (f"A {firm} sells {num(qty)} {many} at {_p(price)} each. It costs {_p(vc)} to make each "
            f"{one}. Calculate the {firm}'s total revenue.")
    return q(text, money_answer(tr),
             f"Total revenue = price × quantity = {_p(price)} × {num(qty)} = {gbp(tr)}",
             "Total revenue = price × quantity sold (costs are not used)",
             [money_mistake(Fraction((price - vc) * qty, 100), "Total revenue is just price × quantity — "
                                                               "don't take any costs off"),
              money_mistake(Fraction(vc * qty, 100), "That's the total variable cost — use the selling price")])


def _fm_2(rng: random.Random) -> Draft:
    """Total cost = fixed cost + variable cost per unit × quantity."""
    firm, many, one, price, vc, qty, fc = _firm(rng)
    tvc = Fraction(vc * qty, 100)
    tc = fc + tvc
    text = (f"A {firm} has fixed costs of {gbp(fc)} a month. The variable cost of each {one} is {_p(vc)}. "
            f"In one month it makes {num(qty)} {many}. Calculate its total cost for the month.")
    return q(text, money_answer(tc),
             f"Total variable cost = {_p(vc)} × {num(qty)} = {gbp(tvc)}. Total cost = {gbp(fc)} + {gbp(tvc)} = {gbp(tc)}",
             "Total cost = fixed costs + (variable cost per unit × quantity)",
             [money_mistake(tvc, "That's only the variable costs — add the fixed costs too"),
              money_mistake(fc + Fraction(vc, 100), "Multiply the variable cost per unit by the number made "
                                                   "before adding the fixed costs")])


def _fm_3(rng: random.Random) -> Draft:
    """Profit = total revenue − total cost."""
    def pick(r: random.Random):
        firm, many, one, price, vc, qty, fc = _firm(r)
        tr = Fraction(price * qty, 100)
        tc = fc + Fraction(vc * qty, 100)
        if tr - tc <= 0:
            return None
        return firm, many, one, price, vc, qty, fc, tr, tc
    firm, many, one, price, vc, qty, fc, tr, tc = retry(pick, rng)
    tvc = tc - fc
    text = (f"A {firm} sells {num(qty)} {many} at {_p(price)} each. Its fixed costs are {gbp(fc)} and the "
            f"variable cost of each {one} is {_p(vc)}. Calculate its profit.")
    sol = (f"TR = {_p(price)} × {num(qty)} = {gbp(tr)}. TC = {gbp(fc)} + {_p(vc)} × {num(qty)} = {gbp(tc)}. "
           f"Profit = {gbp(tr)} − {gbp(tc)} = {gbp(tr - tc)}")
    return q(text, money_answer(tr - tc), sol,
             "Work out total revenue and total cost first, then subtract",
             [money_mistake(tr - fc, "You also need to take off the variable costs"),
              money_mistake(tr - tvc, "You also need to take off the fixed costs"),
              money_mistake(tr, "That's total revenue — profit = total revenue − total cost")])


def _fm_4(rng: random.Random) -> Draft:
    """Average cost per unit (£, nearest penny)."""
    def pick(r: random.Random):
        firm, many, one, price, vc, qty, fc = _firm(r)
        tc = fc + Fraction(vc * qty, 100)
        ac = tc / qty
        if ac.denominator == 1 or not ok_round(ac, 2) or not ok_round(Fraction(fc, qty), 2):
            return None
        return firm, many, one, vc, qty, fc, tc, ac
    firm, many, one, vc, qty, fc, tc, ac = retry(pick, rng)
    if rng.random() < 0.5:
        text = (f"A {firm} has fixed costs of {gbp(fc)} and a variable cost of {_p(vc)} per {one}. It makes "
                f"{num(qty)} {many}. Calculate the average cost per {one}. Give your answer to the "
                f"nearest penny.")
        sol = (f"TC = {gbp(fc)} + {_p(vc)} × {num(qty)} = {gbp(tc)}. AC = {gbp(tc)} ÷ {num(qty)} = "
               f"{gbp(ac, pennies=True)} (nearest penny)")
        ms = [money_mistake(Fraction(fc, qty), "That's average fixed cost — add the variable cost per unit "
                                               "as well", pennies=True),
              money_mistake(tc, "That's the total cost — divide it by the number made")]
        hint = "Work out total cost first, then divide it by the number made"
    else:
        text = (f"It costs a {firm} a total of {gbp(tc)} to make {num(qty)} {many}. Calculate the average "
                f"cost per {one}. Give your answer to the nearest penny.")
        sol = f"Average cost = total cost ÷ quantity = {gbp(tc)} ÷ {num(qty)} = {gbp(ac, pennies=True)} (nearest penny)"
        ms = [money_mistake(tc, "That's the total cost — divide it by the number made")]
        hint = "Average cost = total cost ÷ number of units"
    return q(text, money_answer(ac, pennies=True), sol, hint, ms)


def _fm_5(rng: random.Random) -> Draft:
    """Profit (or loss) at one output, read from a total cost table."""
    def pick(r: random.Random):
        firm, many, one, price, vc, _qty, _fc = _firm(r)
        step = r.choice((50, 100, 200)) if price < 4000 else r.choice((10, 20, 50))
        outs = [step * k for k in range(1, 6)]
        fc = r.randrange(10, 60) * 100
        base = max(50, (vc * step // 100) // 50 * 50)      # cost of each block, rising a little
        inc = r.randrange(0, 4) * 50
        tcs, run = [], fc
        for k in range(5):
            run += base + inc * k
            tcs.append(run)
        i = r.randrange(0, 5)
        profit = Fraction(price * outs[i], 100) - tcs[i]
        if profit == 0:
            return None
        return firm, many, price, outs, tcs, i, profit
    firm, many, price, outs, tcs, i, profit = retry(pick, rng)
    rows = "\n".join(f"{num(o)} {many}: total cost {gbp(c)}" for o, c in zip(outs, tcs))
    text = (f"A {firm} sells {many} for {_p(price)} each. The table shows its total costs.\n{rows}\n"
            f"Calculate the profit when it makes and sells {num(outs[i])} {many}. If it makes a loss, give "
            f"a negative answer.")
    tr = Fraction(price * outs[i], 100)
    sol = (f"TR = {_p(price)} × {num(outs[i])} = {gbp(tr)}. Profit = TR − TC = {gbp(tr)} − {gbp(tcs[i])} = "
           f"{gbp(profit)}" + (" (a loss)" if profit < 0 else ""))
    ms = [money_mistake(-profit, "Profit = total revenue − total cost — check you subtracted the right way "
                                 "round"),
          money_mistake(tr, "That's total revenue — subtract the total cost from it")]
    for j in (i - 1, i + 1):
        if 0 <= j < 5:
            ms.append(money_mistake(tr - tcs[j], f"Use the total cost for {num(outs[i])} {many}, not for "
                                                 f"{num(outs[j])}"))
    return q(text, money_answer(profit), sol,
             "Work out total revenue at that output, then subtract the total cost from the table", ms)


FIRMS_MATHS = gen_skill(
    SUBJECT_ID, "firms_maths", "Costs, revenue & profit",
    ("total revenue", "costs", "profit", "average cost", "fixed cost", "variable cost"),
    (_fm_1, _fm_2, _fm_3, _fm_4, _fm_5),
    "Total revenue = price × quantity, total cost = fixed + variable, profit = revenue − cost",
)


# ======================================================== interest

_RATES = tuple(Fraction(x) for x in ("1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5", "6"))


def _in_1(rng: random.Random) -> Draft:
    """Simple interest: the interest earned, or the total in the account."""
    name = rng.choice(NAMES)
    p = rng.randrange(5, 100) * 100
    r = rng.choice(_RATES)
    n = rng.randrange(2, 7)
    interest = p * r * n / 100
    one_year = p * r / 100
    total = p + interest
    if rng.random() < 0.5:
        text = (f"{name} saves {gbp(p)} in an account that pays {pct(r)} simple interest per year. "
                f"How much interest does {name} earn in {n} years?")
        return q(text, money_answer(interest),
                 f"One year's interest = {pct(r)} of {gbp(p)} = {gbp(one_year)}. "
                 f"Over {n} years: {gbp(one_year)} × {n} = {gbp(interest)}",
                 "Find one year's interest first, then multiply by the number of years",
                 [money_mistake(one_year, f"That's one year's interest — multiply it by {n}"),
                  money_mistake(total, "That's the total in the account — the question asks only for the "
                                       "interest")])
    text = (f"{name} saves {gbp(p)} in an account that pays {pct(r)} simple interest per year. How much "
            f"is in the account after {n} years? No money is added or taken out.")
    return q(text, money_answer(total),
             f"One year's interest = {pct(r)} of {gbp(p)} = {gbp(one_year)}. Over {n} years: {gbp(interest)}. "
             f"Total = {gbp(p)} + {gbp(interest)} = {gbp(total)}",
             "Find one year's interest, multiply by the number of years, then add it to the savings",
             [money_mistake(interest, f"That's only the interest — add it to the {gbp(p)} saved"),
              money_mistake(p + one_year, f"That's after 1 year — simple interest is earned every year for {n} years")])


def _in_2(rng: random.Random) -> Draft:
    """Compound interest, nearest penny."""
    name = rng.choice(NAMES)

    def pick(r: random.Random):
        p = r.randrange(4, 100) * 100
        rate = r.choice(_RATES)
        n = r.randrange(2, 6)
        a = p * (1 + rate / 100) ** n
        if not ok_round(a, 2) or a.denominator == 1:
            return None
        return p, rate, n, a
    p, rate, n, a = retry(pick, rng)
    m = 1 + rate / 100
    text = (f"{name} saves {gbp(p)} in an account that pays {pct(rate)} compound interest per year. "
            f"No money is added or taken out. How much is in the account after {n} years? Give your answer "
            f"to the nearest penny.")
    simple = p * (1 + rate * n / 100)
    return q(text, money_answer(a, pennies=True),
             f"Multiplier = 1 + {fmt_num(rate)} ÷ 100 = {fmt_num(m)}. {gbp(p)} × {fmt_num(m)}^{n} = "
             f"{gbp(a, pennies=True)} (nearest penny)",
             f"Each year the amount is multiplied by the same number — find it from the {pct(rate)}",
             [money_mistake(simple, "That's simple interest — with compound interest, each year's interest is "
                                    "added on before the next year's is worked out", pennies=True),
              money_mistake(a - p, f"That's only the interest — add it to the {gbp(p)} saved", pennies=True)])


def _in_3(rng: random.Random) -> Draft:
    """Real interest rate = nominal rate − inflation (may be negative)."""
    def pick(r: random.Random):
        i = Fraction(r.randrange(5, 81), 10)
        infl = Fraction(r.randrange(5, 91), 10)
        if i == infl:
            return None
        return i, infl
    i, infl = retry(pick, rng)
    real = i - infl
    text = (f"A bank pays a nominal interest rate of {pct(i)} a year on savings. The rate of inflation is "
            f"{pct(infl)}. Calculate the real interest rate. Use real interest rate = nominal interest "
            f"rate − rate of inflation. If your answer is negative, include the minus sign.")
    tail = " (negative: savings lose purchasing power)" if real < 0 else ""
    return q(text, pct_answer(real),
             f"Real interest rate = {pct(i)} − {pct(infl)} = {pct(real)}{tail}",
             "Take the rate of inflation away from the nominal interest rate",
             [pct_mistake(-real, "Subtract inflation from the nominal rate, not the other way round"),
              pct_mistake(i + infl, "Subtract the rate of inflation — don't add it")])


def _in_4(rng: random.Random) -> Draft:
    """Percentage change of savings (1 d.p.)."""
    name = rng.choice(NAMES)
    up = rng.random() < 0.6

    def pick(r: random.Random):
        a = r.randrange(20, 800) * 10
        d = r.randrange(1, a // 40 + 2) * 5
        b = a + d if up else a - d
        if b <= 0:
            return None
        p = Fraction(100 * d, a)
        if p.denominator == 1 or not ok_round(p, 1):
            return None
        by_new = Fraction(100 * d, b)
        if fmt_dp(by_new, 1) == fmt_dp(p, 1):
            return None
        return a, b, d, p, by_new
    a, b, d, p, by_new = retry(pick, rng)
    word = "increase" if up else "decrease"
    how = "rise" if up else "fall"
    text = (f"{name}'s savings {how} from {gbp(a)} to {gbp(b)} over one year. Calculate the percentage "
            f"{word}. Give your answer to 1 decimal place.")
    return q(text, pct_answer(p, 1),
             f"Change = {gbp(d)}. {gbp(d)} ÷ {gbp(a)} × 100 = {fmt_dp(p, 3)}… = {fmt_dp(p, 1)}% (1 d.p.)",
             "Find the change, then divide it by the original amount and multiply by 100",
             [pct_mistake(by_new, "Divide by the original amount (before the change), not the new amount", dp=1),
              money_mistake(d, "That's the change in pounds — divide it by the original amount and multiply "
                               "by 100")])


def _in_5(rng: random.Random) -> Draft:
    """Whole years until compound savings first reach a target."""
    name = rng.choice(NAMES)

    def pick(r: random.Random):
        p = r.randrange(5, 100) * 100
        rate = r.choice(_RATES[2:])
        target = p + r.randrange(1, 9) * p // 10
        target = (target // 100) * 100
        if target <= p:
            return None
        m = 1 + rate / 100
        vals = [Fraction(p)]
        while vals[-1] < target and len(vals) < 40:
            vals.append(vals[-1] * m)
        n = len(vals) - 1
        if not 3 <= n <= 15:
            return None
        # keep clear of the boundary: the year before is at least 0.2% short, the year itself 0.2% over
        if vals[n] < target * Fraction(1002, 1000) or vals[n - 1] > target * Fraction(998, 1000):
            return None
        simple_n = math.ceil(Fraction(target - p) / (p * rate / 100))
        return p, rate, target, n, vals, simple_n
    p, rate, target, n, vals, simple_n = retry(pick, rng)
    text = (f"{name} saves {gbp(p)} in an account that pays {pct(rate)} compound interest per year. No money "
            f"is added or taken out. After how many whole years will the savings first be worth at least "
            f"{gbp(target)}?")
    m = fmt_num(1 + rate / 100)
    sol = (f"Multiply by {m} each year: after {n - 1} years {gbp(vals[n - 1], pennies=True)} (not enough), "
           f"after {n} years {gbp(vals[n], pennies=True)}. So {n} years")
    ms = [plain_mistake(n - 1, f"After {n - 1} years the savings are only {gbp(vals[n - 1], pennies=True)} — "
                               f"not yet {gbp(target)}", "years")]
    if simple_n != n:
        ms.append(plain_mistake(simple_n, "That's how long it takes with simple interest — with compound "
                                          "interest you also earn interest on the interest", "years"))
    return q(text, plain_answer(n, "years"), sol,
             f"Multiply the savings by {m} once for each year until they reach the target", ms)


INTEREST = gen_skill(
    SUBJECT_ID, "interest", "Interest & savings",
    ("compound interest", "simple interest", "real interest rate"),
    (_in_1, _in_2, _in_3, _in_4, _in_5),
    "Interest is a percentage of the amount saved — check whether it is simple or compound",
)


# ======================================================== macro maths

def _bn(x: Fraction) -> str:
    """'£2,150 billion', '-£18.4 billion'."""
    sign = "-" if x < 0 else ""
    return f"{sign}£{num(abs(x))} billion"


def _bn_answer(x: Fraction) -> Answer:
    return num_answer(x, _bn(x))


def _bn_mistake(x: Fraction, fb: str) -> Mistake:
    return Mistake(Answer(kind="number", display=_bn(x), value=float(x)), fb)


def _mm_1(rng: random.Random) -> Draft:
    """Inflation rate from two CPI values (1 d.p.)."""
    def pick(r: random.Random):
        a = Fraction(r.randrange(1000, 1400), 10)
        d = Fraction(r.randrange(3, 101), 10)
        b = a + d
        infl = d / a * 100
        if not ok_round(infl, 1) or fmt_dp(infl, 1) == fmt_dp(d, 1):
            return None
        if fmt_dp(d / b * 100, 1) == fmt_dp(infl, 1):
            return None
        return a, b, d, infl
    a, b, d, infl = retry(pick, rng)
    A, B, D = fmt_dp(a, 1), fmt_dp(b, 1), fmt_num(d)
    text = (f"In a country, the Consumer Prices Index (CPI) rose from {A} to {B} over one year. Calculate "
            f"the rate of inflation for that year. Give your answer to 1 decimal place.")
    return q(text, pct_answer(infl, 1),
             f"Rise = {B} − {A} = {D} index points. Inflation = {D} ÷ {A} × 100 = {fmt_dp(infl, 3)}… = "
             f"{fmt_dp(infl, 1)}% (1 d.p.)",
             "Find the rise in the index, then divide by the index at the start of the year and multiply by 100",
             [plain_mistake(d, "That's the rise in index points — divide it by the starting index and multiply "
                               "by 100"),
              pct_mistake(d / b * 100, "Divide by the index at the start of the year, not the end", dp=1)])


def _mm_2(rng: random.Random) -> Draft:
    """GDP growth as a percentage change (1 d.p., minus sign for a fall)."""
    up = rng.random() < 0.75

    def pick(r: random.Random):
        a = r.randrange(300, 3000)
        d = r.randrange(2, max(3, a // 20))
        b = a + d if up else a - d
        g = Fraction(100 * d, a)
        if g.denominator == 1 or not ok_round(g, 1):
            return None
        if fmt_dp(Fraction(100 * d, b), 1) == fmt_dp(g, 1):
            return None
        return a, b, d, g
    a, b, d, g = retry(pick, rng)
    change = g if up else -g
    text = (f"A country's real GDP changed from £{num(a)} billion to £{num(b)} billion in one year. Calculate "
            f"the percentage change in real GDP. Give your answer to 1 decimal place. If GDP fell, include a "
            f"minus sign.")
    sol = (f"Change = {'+' if up else '-'}£{num(d)} billion. {'+' if up else '-'}{num(d)} ÷ {num(a)} × 100 = "
           f"{fmt_dp(change, 1)}% (1 d.p.)")
    ms = [pct_mistake(Fraction(100 * (b - a), b), "Divide the change by the GDP at the start, not the end",
                      dp=1),
          _bn_mistake(Fraction(b - a), "That's the change in £ billion — divide it by the starting GDP and "
                                       "multiply by 100")]
    if not up:
        ms.append(pct_mistake(g, "GDP fell, so the percentage change is negative — include the minus sign", dp=1))
    return q(text, pct_answer(change, 1), sol,
             "Find the change in GDP, then divide by the GDP at the start and multiply by 100", ms)


def _mm_3(rng: random.Random) -> Draft:
    """Real growth ≈ nominal growth − inflation."""
    def pick(r: random.Random):
        g = Fraction(r.randrange(5, 101), 10)
        infl = Fraction(r.randrange(5, 81), 10)
        if g == infl:
            return None
        return g, infl
    g, infl = retry(pick, rng)
    real = g - infl
    text = (f"In one year, a country's nominal GDP grew by {pct(g)} and the rate of inflation was "
            f"{pct(infl)}. Calculate the real growth rate. Use real growth = nominal growth − inflation. "
            f"If your answer is negative, include the minus sign.")
    tail = " (real output fell)" if real < 0 else ""
    return q(text, pct_answer(real),
             f"Real growth = {pct(g)} − {pct(infl)} = {pct(real)}{tail}",
             "Take inflation away from the nominal growth rate",
             [pct_mistake(-real, "Subtract inflation from nominal growth, not the other way round"),
              pct_mistake(g + infl, "Subtract inflation — don't add it")])


# (symbol or "", name, word used after a number when there is no symbol, rate range in cents)
_FX = (("", "US dollars", "dollars", 110, 145), ("€", "euros", "euros", 105, 125))


def _fx(sym: str, word: str, x, pennies: bool = True) -> str:
    """'€406.00' or '444.50 dollars' (no '$': plain text rules forbid it)."""
    if sym:
        return cur(sym, x, pennies)
    body = gbp(x, pennies)[1:] if x >= 0 else "-" + gbp(-x, pennies)[2:]
    return f"{body} {word}"


def _mm_4(rng: random.Random) -> Draft:
    """Currency conversion at a stated (hypothetical) exchange rate, 2 d.p."""
    sym, name, word, lo, hi = rng.choice(_FX)
    to_foreign = rng.random() < 0.5

    def pick(r: random.Random):
        rate = Fraction(r.randrange(lo, hi + 1), 100)
        amt = r.randrange(4, 400) * 5
        res = amt * rate if to_foreign else amt / rate
        if not ok_round(res, 2):
            return None
        other = amt / rate if to_foreign else amt * rate
        return rate, amt, res, other
    rate, amt, res, other = retry(pick, rng)
    R = fmt_dp(rate, 2)
    one_pound = f"£1 = {sym}{R}" if sym else f"£1 = {R} {name}"
    if to_foreign:
        text = (f"Suppose the exchange rate is {one_pound}. Convert {gbp(amt)} into {name}. Give your "
                f"answer to 2 decimal places.")
        ans = num_answer(res, _fx(sym, word, res), dp=2)
        sol = f"Pounds to {name}: multiply by the rate. {gbp(amt)} × {R} = {_fx(sym, word, res)}"
        ms = [Mistake(Answer(kind="number", display=_fx(sym, word, other), value=float(other), dp=2),
                      f"To change pounds into {name}, multiply by the exchange rate — don't divide")]
        hint = f"Each £1 is worth {R} {name}"
    else:
        amount = _fx(sym, word, amt, pennies=False) if sym else f"{num(amt)} {name}"
        text = (f"A tourist changes {amount} into pounds at an exchange rate of {one_pound}. How many pounds "
                f"does the tourist get? Give your answer to the nearest penny.")
        ans = money_answer(res, pennies=True)
        sol = f"{cap(name)} to pounds: divide by the rate. {num(amt)} ÷ {R} = {gbp(res, pennies=True)}"
        ms = [money_mistake(other, f"To change {name} into pounds, divide by the exchange rate — don't "
                                   "multiply", pennies=True)]
        hint = f"Each £1 costs {R} {name}, so work out how many lots of {R} there are"
    return q(text, ans, sol, hint, ms)


def _mm_5(rng: random.Random) -> Draft:
    """Balance of trade (goods, or goods and services), with its sign."""
    def b(r: random.Random, lo: int, hi: int) -> Fraction:
        return Fraction(r.randrange(lo * 10, hi * 10), 10)
    if rng.random() < 0.5:
        def pick(r: random.Random):
            x, m = b(r, 50, 600), b(r, 50, 600)
            if x == m or abs(x - m) > 120:
                return None
            return x, m
        x, m = retry(pick, rng)
        bal = x - m
        text = (f"In one year, a country exported goods worth £{fmt_num(x)} billion and imported goods worth "
                f"£{fmt_num(m)} billion. Calculate its balance of trade in goods. Give your answer in "
                f"£ billion and use a minus sign for a deficit.")
        sol = (f"Balance of trade = exports − imports = {fmt_num(x)} − {fmt_num(m)} = {_bn(bal)}"
               + (" (a deficit)" if bal < 0 else " (a surplus)"))
        return q(text, _bn_answer(bal), sol, "Balance of trade = exports − imports",
                 [_bn_mistake(-bal, "Balance of trade = exports − imports — check the order and the sign")])

    def pick2(r: random.Random):
        xg, mg, xs, ms_ = b(r, 100, 500), b(r, 100, 500), b(r, 50, 300), b(r, 50, 300)
        bal = (xg + xs) - (mg + ms_)
        if bal == 0 or abs(bal) > 150 or xg == mg or xs == ms_:
            return None
        if bal == xg - mg or bal == xs - ms_:
            return None
        return xg, mg, xs, ms_, bal
    xg, mg, xs, ms_, bal = retry(pick2, rng)
    text = (f"In one year, a country exported goods worth £{fmt_num(xg)} billion and services worth "
            f"£{fmt_num(xs)} billion. It imported goods worth £{fmt_num(mg)} billion and services worth "
            f"£{fmt_num(ms_)} billion. Calculate its balance of trade in goods and services. Give your answer "
            f"in £ billion and use a minus sign for a deficit.")
    sol = (f"Exports = {fmt_num(xg)} + {fmt_num(xs)} = {fmt_num(xg + xs)}. Imports = {fmt_num(mg)} + "
           f"{fmt_num(ms_)} = {fmt_num(mg + ms_)}. Balance = {fmt_num(xg + xs)} − {fmt_num(mg + ms_)} = {_bn(bal)}")
    return q(text, _bn_answer(bal), sol,
             "Add up all exports and all imports first, then work out exports − imports",
             [_bn_mistake(-bal, "Balance of trade = exports − imports — check the order and the sign"),
              _bn_mistake(xg - mg, "That's only the balance for goods — include services too"),
              _bn_mistake(xs - ms_, "That's only the balance for services — include goods too")])


MACRO_MATHS = gen_skill(
    SUBJECT_ID, "macro_maths", "Macro calculations",
    ("inflation rate", "gdp growth", "exchange rate conversion", "balance of trade"),
    (_mm_1, _mm_2, _mm_3, _mm_4, _mm_5),
    "Write down the formula first, then put the numbers in",
)


ROWS = (
    (("markets", "Markets & prices", ("markets", "elasticity")),
     ("firms", "Firms & production", ("firms", "firms_maths"))),
    (("money_work", "Money, banks & work", ("money_work", "interest")),
     ("national", "The national economy", ("national", "macro_maths"))),
)

SKILL_ORDER = ("markets", "elasticity", "firms", "firms_maths", "money_work", "interest",
               "national", "macro_maths")


def register(reg) -> None:
    """Register Economics: the pack's bank skills plus the four generator skills."""
    register_subject(reg, SUBJECT_ID, TITLE, ORDER, ROWS, SKILL_ORDER,
                     [ELASTICITY, FIRMS_MATHS, INTEREST, MACRO_MATHS])
