"""Chemistry (GCSE, Years 10–11): generator skills here, bank skills in packs/chemistry.json.

docs/ARCHITECTURE_V2.md section 5.1. Every relative atomic mass, constant and bond energy a
question needs is stated in that question (rule R13). Arithmetic uses Fractions, so values are
exact before rounding, and a value close to a rounding boundary is never used. Every rounding
instruction and unit is in the question text.
"""
from __future__ import annotations

import hashlib
import random
import re
from collections import Counter
from dataclasses import replace
from fractions import Fraction

from ..content import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, build_choice, load_pack
from ..content.fmt import (
    build, check_level, dec, fmt_dp, fmt_num, fmt_sf, fmt_std, num_answer, num_mistake, retry,
    sig_digits, std_answer, std_mistake, unit,
)

SUBJECT_ID = "chemistry"
Draft = dict

# ================================================================ helpers

AR: dict[str, Fraction] = {
    "H": Fraction(1), "Li": Fraction(7), "C": Fraction(12), "N": Fraction(14), "O": Fraction(16),
    "F": Fraction(19), "Na": Fraction(23), "Mg": Fraction(24), "Al": Fraction(27), "Si": Fraction(28),
    "P": Fraction(31), "S": Fraction(32), "Cl": Fraction(71, 2), "K": Fraction(39), "Ca": Fraction(40),
    "Fe": Fraction(56), "Co": Fraction(59), "Cu": Fraction(127, 2), "Zn": Fraction(65), "Br": Fraction(80),
    "Ag": Fraction(108), "Ba": Fraction(137), "Pb": Fraction(207),
}
AVOGADRO = Fraction(602) * 10 ** 21          # 6.02 × 10^23
AVOGADRO_TXT = "Use the Avogadro constant = 6.02 × 10^23 per mole."
RTP_TXT = "One mole of any gas occupies 24 dm³ at room temperature and pressure (RTP)."

_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def chem(f: str) -> str:
    """'H2SO4' -> 'H₂SO₄'; coefficients (at the start, after a space or '·') stay full size."""
    out: list[str] = []
    prev = ""
    for ch in f:
        if ch.isdigit() and (prev.isalpha() or prev == ")" or (prev.isdigit() and out and out[-1] in "₀₁₂₃₄₅₆₇₈₉")):
            out.append(ch.translate(_SUB))
        else:
            out.append(ch)
        prev = ch
    return "".join(out)


def _read_num(s: str, i: int) -> tuple[int, int]:
    j = i
    while j < len(s) and s[j].isdigit():
        j += 1
    return (int(s[i:j]) if j > i else 1), j


def _group(s: str, i: int, mode: str) -> tuple[Counter, int]:
    """Parse atoms from position i up to ')' or the end. mode: 'ok' | 'ignore' | 'last' (mistake models)."""
    c: Counter = Counter()
    while i < len(s):
        ch = s[i]
        if ch == "(":
            inner, i = _group(s, i + 1, mode)
            if i >= len(s) or s[i] != ")":
                raise ValueError(f"unbalanced brackets in {s!r}")
            n, i = _read_num(s, i + 1)
            if mode == "ignore":
                n = 1
            if mode == "last":
                last = list(inner)[-1]
                for el, k in inner.items():
                    c[el] += k * (n if el == last else 1)
            else:
                for el, k in inner.items():
                    c[el] += k * n
        elif ch == ")":
            return c, i
        elif ch.isupper():
            j = i + 1
            while j < len(s) and s[j].islower():
                j += 1
            el = s[i:j]
            if el not in AR:
                raise ValueError(f"unknown element {el!r}")
            n, j = _read_num(s, j)
            c[el] += n
            i = j
        else:
            raise ValueError(f"cannot parse {s!r}")
    return c, i


def atoms(f: str, mode: str = "ok") -> Counter:
    """Atom counts of a formula such as 'Ca(OH)2' or 'CuSO4·5H2O'."""
    total: Counter = Counter()
    for part in f.split("·"):
        m = re.match(r"^(\d+)(.+)$", part)
        k, body = (int(m.group(1)), m.group(2)) if m else (1, part)
        c, i = _group(body, 0, mode)
        if i != len(body):
            raise ValueError(f"cannot parse {f!r}")
        for el, n in c.items():
            total[el] += n * k
    return total


def mr(f: str, mode: str = "ok") -> Fraction:
    return sum((AR[el] * n for el, n in atoms(f, mode).items()), Fraction(0))


def _elements(*formulas: str) -> list[str]:
    seen: list[str] = []
    for f in formulas:
        for el in atoms(f):
            if el not in seen:
                seen.append(el)
    return seen


def ar_text(*formulas: str) -> str:
    """'Relative atomic masses (Ar): Ca = 40, O = 16, H = 1.' for every element in the formulas."""
    els = _elements(*formulas)
    return "Relative atomic masses (Ar): " + ", ".join(f"{el} = {fmt_num(AR[el])}" for el in els) + "."


def n(x) -> str:
    return fmt_num(x)


def F(x) -> Fraction:
    return x if isinstance(x, Fraction) else Fraction(str(x))


def _rounding_ok(v, dp: int | None = None, sf: int | None = None, margin: float = 0.05) -> bool:
    """False when v lies within ``margin`` of a half-unit rounding boundary (an early-rounding trap)."""
    d = abs(dec(v))
    if d == 0:
        return dp is not None
    if dp is None:
        dp = sf - 1 - d.adjusted()
    t = d.scaleb(dp)
    frac = float(t - t.to_integral_value(rounding="ROUND_FLOOR"))
    return abs(frac - 0.5) > margin


def _q(text: str, answer: Answer, solution: str, hint: str, mistakes=()) -> Draft:
    return {"text": text, "answer": answer, "solution": solution, "hint": hint, "mistakes": list(mistakes)}


def _exact(v, u: str) -> Answer:
    return num_answer(v, unit(n(v), u))


def _sf_answer(v, u: str, sf: int = 3) -> Answer:
    """3 s.f. answer; very small values are shown in standard form (any form is accepted)."""
    shown = fmt_std(v, sf) if 0 < abs(v) < Fraction(1, 1000) else fmt_sf(v, sf)
    return num_answer(v, unit(shown, u), sf=sf)


def _dp_answer(v, u: str, dp: int = 1) -> Answer:
    return num_answer(v, unit(fmt_dp(v, dp), u), dp=dp)


def _m(v, u: str, fb: str, sf: int | None = 3, dp: int | None = None) -> Mistake | None:
    """A typical wrong value, matched at the rounding the question asks for."""
    if v is None:
        return None
    try:
        if float(v) == 0:
            return None
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return None
    if dp is not None:
        return num_mistake(v, u, fb, dp=dp)
    if sf is None:
        return num_mistake(v, u, fb)
    return num_mistake(v, u, fb, sf=sf)


def _approx(v) -> str:
    """Working value: exact when short, else 4 s.f. followed by '…'."""
    if sig_digits(v) <= 5 and Fraction(v).denominator in (1, 2, 4, 5, 8, 10, 20, 25, 40, 50, 100, 1000):
        return n(v)
    return fmt_sf(v, 4) + "…"


SF_TXT = "Give your answer to 3 significant figures."
DP_TXT = "Give your answer to 1 decimal place."

# ============================================================ substances

_NAMES = {
    "H2O": "water", "CO2": "carbon dioxide", "NaCl": "sodium chloride", "MgO": "magnesium oxide",
    "CH4": "methane", "NH3": "ammonia", "HCl": "hydrogen chloride", "H2SO4": "sulfuric acid",
    "CaCO3": "calcium carbonate", "NaOH": "sodium hydroxide", "KCl": "potassium chloride", "C2H6": "ethane",
    "SO2": "sulfur dioxide", "CaO": "calcium oxide", "Na2O": "sodium oxide", "Al2O3": "aluminium oxide",
    "Fe2O3": "iron(III) oxide", "C3H8": "propane", "HNO3": "nitric acid", "CuO": "copper(II) oxide",
    "ZnO": "zinc oxide", "MgCl2": "magnesium chloride", "C6H12O6": "glucose", "Na2CO3": "sodium carbonate",
    "CaCl2": "calcium chloride", "SO3": "sulfur trioxide", "NO2": "nitrogen dioxide", "KBr": "potassium bromide",
    "C2H4": "ethene", "H2O2": "hydrogen peroxide", "NaHCO3": "sodium hydrogencarbonate", "C2H5OH": "ethanol",
    "Ca(OH)2": "calcium hydroxide", "Mg(OH)2": "magnesium hydroxide", "Mg(NO3)2": "magnesium nitrate",
    "(NH4)2SO4": "ammonium sulfate", "Al(OH)3": "aluminium hydroxide", "Ca(NO3)2": "calcium nitrate",
    "Cu(NO3)2": "copper(II) nitrate", "Al2(SO4)3": "aluminium sulfate", "Fe(OH)3": "iron(III) hydroxide",
    "Fe(OH)2": "iron(II) hydroxide", "Zn(NO3)2": "zinc nitrate", "Ba(OH)2": "barium hydroxide",
    "Pb(NO3)2": "lead(II) nitrate", "(NH4)2CO3": "ammonium carbonate", "Ca3(PO4)2": "calcium phosphate",
    "Fe2(SO4)3": "iron(III) sulfate", "Al(NO3)3": "aluminium nitrate", "Cu(OH)2": "copper(II) hydroxide",
    "(NH4)3PO4": "ammonium phosphate", "NH4NO3": "ammonium nitrate", "CuSO4": "copper(II) sulfate",
    "KNO3": "potassium nitrate", "CO(NH2)2": "urea", "MgSO4": "magnesium sulfate", "Mg": "magnesium",
    "O2": "oxygen", "Na": "sodium", "Cl2": "chlorine", "Fe": "iron", "CO": "carbon monoxide", "H2": "hydrogen",
    "Zn": "zinc", "ZnCl2": "zinc chloride", "N2": "nitrogen", "FeCl3": "iron(III) chloride", "Al": "aluminium",
    "Na2SO4": "sodium sulfate", "ZnSO4": "zinc sulfate", "K2SO4": "potassium sulfate", "C": "carbon", "Ca": "calcium", "Cu": "copper", "S": "sulfur",
    "CuSO4·5H2O": "hydrated copper(II) sulfate", "MgSO4·7H2O": "hydrated magnesium sulfate",
    "Na2CO3·10H2O": "hydrated sodium carbonate", "CaCl2·2H2O": "hydrated calcium chloride",
    "FeSO4·7H2O": "hydrated iron(II) sulfate", "BaCl2·2H2O": "hydrated barium chloride",
    "ZnSO4·7H2O": "hydrated zinc sulfate", "Na2SO4·10H2O": "hydrated sodium sulfate",
    "MgCl2·6H2O": "hydrated magnesium chloride", "CoCl2·6H2O": "hydrated cobalt(II) chloride",
}


def named(f: str) -> str:
    """'sulfuric acid, H₂SO₄'."""
    return f"{_NAMES[f]}, {chem(f)}" if f in _NAMES else chem(f)


_SIMPLE = ("H2O", "CO2", "NaCl", "MgO", "CH4", "NH3", "HCl", "H2SO4", "CaCO3", "NaOH", "KCl", "C2H6", "SO2",
           "CaO", "Na2O", "Al2O3", "Fe2O3", "C3H8", "HNO3", "CuO", "ZnO", "MgCl2", "C6H12O6", "Na2CO3", "CaCl2",
           "SO3", "NO2", "KBr", "C2H4", "H2O2", "NaHCO3", "C2H5OH")
_BRACKETS = ("Ca(OH)2", "Mg(OH)2", "Mg(NO3)2", "(NH4)2SO4", "Al(OH)3", "Ca(NO3)2", "Cu(NO3)2", "Al2(SO4)3",
             "Fe(OH)3", "Fe(OH)2", "Zn(NO3)2", "Ba(OH)2", "Pb(NO3)2", "(NH4)2CO3", "Ca3(PO4)2", "Fe2(SO4)3",
             "Al(NO3)3", "Cu(OH)2", "(NH4)3PO4")
_HYDRATES = ("CuSO4·5H2O", "MgSO4·7H2O", "Na2CO3·10H2O", "CaCl2·2H2O", "FeSO4·7H2O", "BaCl2·2H2O",
             "ZnSO4·7H2O", "Na2SO4·10H2O", "MgCl2·6H2O", "CoCl2·6H2O")
# (compound, element or "H2O" for water of crystallisation)
_PERCENT = (("NH4NO3", "N"), ("(NH4)2SO4", "N"), ("H2O", "O"), ("CO2", "C"), ("Fe2O3", "Fe"), ("CaCO3", "Ca"),
            ("CuSO4", "Cu"), ("NaCl", "Na"), ("CH4", "H"), ("MgO", "Mg"), ("CaCO3", "O"), ("H2SO4", "S"),
            ("NH3", "N"), ("KNO3", "K"), ("Al2O3", "Al"), ("C6H12O6", "C"), ("NaOH", "Na"), ("CO(NH2)2", "N"),
            ("CuSO4·5H2O", "H2O"), ("MgSO4·7H2O", "H2O"), ("C2H5OH", "C"), ("Ca(OH)2", "Ca"), ("Na2CO3", "Na"),
            ("SO2", "S"), ("Fe2O3", "O"), ("NaCl", "Cl"), ("C3H8", "H"), ("Na2CO3·10H2O", "H2O"))
_ELEMENT_NAMES = {"H": "hydrogen", "C": "carbon", "N": "nitrogen", "O": "oxygen", "Na": "sodium", "Mg": "magnesium",
                  "Al": "aluminium", "S": "sulfur", "Cl": "chlorine", "K": "potassium", "Ca": "calcium",
                  "Fe": "iron", "Cu": "copper"}

# ================================================================== Mr


def _mr_text(f: str) -> str:
    return f"Calculate the relative formula mass (Mr) of {named(f)}. {ar_text(f)}"


def _mr_working(f: str) -> str:
    parts = []
    for el, k in atoms(f).items():
        parts.append(f"{k} × {n(AR[el])}" if k > 1 else n(AR[el]))
    return " + ".join(parts)


def _mr_1(rng):
    f = rng.choice(_SIMPLE)
    v = mr(f)
    once = sum((AR[el] for el in atoms(f)), Fraction(0))
    return _q(_mr_text(f), _exact(v, ""), f"Mr = {_mr_working(f)} = {n(v)}",
              "Add up the Ar of every atom in the formula — the small number after a symbol tells you how many atoms",
              [_m(once, "", "Multiply each Ar by the number of atoms of that element (the small number after its symbol)", sf=None)])


def _mr_2(rng):
    f = rng.choice(_BRACKETS)
    v = mr(f)
    return _q(_mr_text(f), _exact(v, ""), f"Mr = {_mr_working(f)} = {n(v)}",
              "The small number after a bracket multiplies every atom inside the bracket",
              [_m(mr(f, "last"), "", "The number after the bracket multiplies everything inside the bracket, not just the last atom", sf=None),
               _m(mr(f, "ignore"), "", "Don't forget the number after the bracket: it multiplies everything inside", sf=None)])


def _mr_3(rng):
    f = rng.choice(_HYDRATES)
    salt, water = f.split("·")
    k = int(re.match(r"\d+", water).group(0))
    v = mr(f)
    return _q(_mr_text(f), _exact(v, ""),
              f"Mr of {chem(salt)} = {n(mr(salt))}, Mr of {k}H₂O = {k} × 18 = {18 * k}. Mr = {n(mr(salt))} + {18 * k} = {n(v)}",
              "Work out the Mr of the salt and of one water molecule, then add on the right number of water molecules",
              [_m(mr(salt) + 18, "", f"The {k} in front of H₂O means {k} water molecules: add {k} × 18", sf=None),
               _m(mr(salt), "", f"Include the water of crystallisation: add {k} × 18", sf=None)])


def _pct_1(rng):
    def make(r):
        f, el = r.choice(_PERCENT)
        total = mr(f)
        if el == "H2O":
            k = int(re.match(r"\d+", f.split("·")[1]).group(0))
            part = 18 * k
            once = Fraction(18)
        else:
            k = atoms(f)[el]
            part = AR[el] * k
            once = AR[el]
        v = part / total * 100
        if not _rounding_ok(v, dp=1):
            return None
        return f, el, k, part, once, total, v
    f, el, k, part, once, total, v = retry(make, rng)
    what = "water" if el == "H2O" else _ELEMENT_NAMES[el]
    text = f"Calculate the percentage by mass of {what} in {named(f)}. {ar_text(f)} {DP_TXT}"
    top = f"{k} × 18 = {n(part)}" if el == "H2O" else (f"{k} × {n(AR[el])} = {n(part)}" if k > 1 else n(part))
    sol = f"Mr = {n(total)}. Mass of {what} = {top}. % = {n(part)} ÷ {n(total)} × 100 = {fmt_dp(v, 1)}%"
    return _q(text, _dp_answer(v, "%"), sol,
              f"Work out the Mr first, then the total mass of {what} in one formula unit",
              [_m(once / total * 100 if k > 1 else None, "%",
                  f"There {'are' if k > 1 else 'is'} {k} {'molecules' if el == 'H2O' else 'atoms'} of {what} in the formula — multiply by {k}", dp=1),
               _m(part / total, "%", "Multiply by 100 to turn the fraction into a percentage", dp=1)])


_ISOTOPES = (
    ("chlorine", ((35, 75), (37, 25))),
    ("copper", ((63, 69), (65, 31))),
    ("bromine", ((79, 51), (81, 49))),
    ("boron", ((10, 20), (11, 80))),
    ("lithium", ((6, "7.5"), (7, "92.5"))),
    ("gallium", ((69, 60), (71, 40))),
    ("rubidium", ((85, 72), (87, 28))),
    ("magnesium", ((24, 79), (25, 10), (26, 11))),
    ("silicon", ((28, 92), (29, 5), (30, 3))),
    ("silver", ((107, 52), (109, 48))),
)


def _ar_5(rng):
    if rng.random() < 0.5:
        name, iso = rng.choice(_ISOTOPES)
        iso = tuple((a, F(p)) for a, p in iso)
        label = name
        lst = ", ".join(f"{name}-{a} ({n(p)}%)" for a, p in iso)
        text = (f"A sample of {name} contains these isotopes: {lst}. Calculate the relative atomic mass (Ar) of "
                f"{name} in this sample. {DP_TXT}")
    else:
        def make(r):
            a = r.randrange(20, 120)
            b = a + r.choice((1, 2, 2))
            p = r.randrange(10, 91)
            v = Fraction(a * p + b * (100 - p), 100)
            return None if not _rounding_ok(v, dp=1) else ((a, F(p)), (b, F(100 - p)))
        iso = retry(make, rng)
        label = "element X"
        lst = " and ".join(f"X-{a} ({n(p)}%)" for a, p in iso)
        text = (f"Element X has two isotopes: {lst}. Calculate the relative atomic mass (Ar) of element X. {DP_TXT}")
    v = sum((a * p for a, p in iso), Fraction(0)) / 100
    mean = Fraction(sum(a for a, _ in iso), len(iso))
    working = " + ".join(f"({a} × {n(p)})" for a, p in iso)
    sol = f"Ar = [{working}] ÷ 100 = {n(sum((a * p for a, p in iso), Fraction(0)))} ÷ 100 = {fmt_dp(v, 1)}"
    return _q(text, _dp_answer(v, ""), sol,
              "Multiply each mass number by its percentage, add the results, then divide by 100",
              [_m(mean, "", f"Don't just average the mass numbers — weight each one by its percentage abundance", dp=1),
               _m(v * 100, "", "Divide the total by 100 (the percentages add up to 100)", dp=1)])


# ================================================================ moles

_NICE_N = ("0.1", "0.2", "0.25", "0.4", "0.5", "0.75", "1", "1.5", "2", "2.5", "3", "4", "5", "0.05", "0.15", "0.3")
_MOLE_SUBSTANCES = ("H2O", "CO2", "NaCl", "MgO", "CH4", "NH3", "H2SO4", "CaCO3", "NaOH", "KCl", "CaO", "Fe2O3",
                    "HNO3", "CuO", "MgCl2", "C6H12O6", "Na2CO3", "CaCl2", "SO2", "O2", "N2", "Cl2", "C2H5OH",
                    "Ca(OH)2", "CuSO4", "KNO3", "NH4NO3", "Al2O3")


def _mol_1(rng):
    f = rng.choice(_MOLE_SUBSTANCES)
    m_r = mr(f)
    nn = F(rng.choice(_NICE_N))
    mass = nn * m_r
    if sig_digits(mass) > 4:
        nn = F(rng.choice(("0.5", "1", "2", "4")))
        mass = nn * m_r
    return _q(f"Calculate the number of moles in {n(mass)} g of {named(f)}. The Mr of {chem(f)} is {n(m_r)}.",
              _exact(nn, "mol"), f"moles = mass ÷ Mr = {n(mass)} ÷ {n(m_r)} = {n(nn)} mol",
              "moles = mass ÷ Mr",
              [_m(mass * m_r, "mol", "moles = mass ÷ Mr — divide, don't multiply", sf=None),
               _m(m_r / mass, "mol", "moles = mass ÷ Mr — you divided the wrong way round", sf=3)])


def _mol_2(rng):
    f = rng.choice(_MOLE_SUBSTANCES)
    m_r = mr(f)
    nn = F(rng.choice(_NICE_N))
    mass = nn * m_r
    return _q(f"Calculate the mass of {n(nn)} mol of {named(f)}. The Mr of {chem(f)} is {n(m_r)}. Give your answer in grams.",
              _exact(mass, "g"), f"mass = moles × Mr = {n(nn)} × {n(m_r)} = {n(mass)} g",
              "Rearrange moles = mass ÷ Mr to make mass the subject",
              [_m(nn / m_r, "g", "mass = moles × Mr — multiply, don't divide", sf=3),
               _m(m_r / nn, "g", "mass = moles × Mr — multiply, don't divide", sf=3)])


def _mol_3(rng):
    def make(r):
        f = r.choice(_MOLE_SUBSTANCES)
        mass = F(r.randrange(20, 500)) / 10
        v = mass / mr(f)
        if not _rounding_ok(v, sf=3) or sig_digits(v) <= 3:
            return None
        return f, mass, v
    f, mass, v = retry(make, rng)
    m_r = mr(f)
    once = sum((AR[el] for el in atoms(f)), Fraction(0))
    return _q(f"Calculate the number of moles in {n(mass)} g of {named(f)}. {ar_text(f)} {SF_TXT}",
              _sf_answer(v, "mol"), f"Mr = {_mr_working(f)} = {n(m_r)}. moles = {n(mass)} ÷ {n(m_r)} = {fmt_sf(v, 3)} mol",
              f"Work out the Mr of {chem(f)} first, then use moles = mass ÷ Mr",
              [_m(mass * m_r, "mol", "moles = mass ÷ Mr — divide, don't multiply"),
               _m(m_r / mass, "mol", "moles = mass ÷ Mr — you divided the wrong way round"),
               _m(mass / once if once != m_r else None, "mol",
                  "Check the Mr: multiply each Ar by the number of atoms of that element")])


# (equation, {formula: coefficient}, [(given, find), ...])
_REACTIONS = (
    ("2Mg + O2 → 2MgO", {"Mg": 2, "O2": 1, "MgO": 2}, (("Mg", "MgO"),)),
    ("CaCO3 → CaO + CO2", {"CaCO3": 1, "CaO": 1, "CO2": 1}, (("CaCO3", "CaO"), ("CaCO3", "CO2"))),
    ("2Na + Cl2 → 2NaCl", {"Na": 2, "Cl2": 1, "NaCl": 2}, (("Na", "NaCl"), ("Cl2", "NaCl"))),
    ("4Na + O2 → 2Na2O", {"Na": 4, "O2": 1, "Na2O": 2}, (("Na", "Na2O"),)),
    ("Fe2O3 + 3CO → 2Fe + 3CO2", {"Fe2O3": 1, "CO": 3, "Fe": 2, "CO2": 3}, (("Fe2O3", "Fe"),)),
    ("CH4 + 2O2 → CO2 + 2H2O", {"CH4": 1, "O2": 2, "CO2": 1, "H2O": 2}, (("CH4", "H2O"), ("CH4", "CO2"))),
    ("2H2 + O2 → 2H2O", {"H2": 2, "O2": 1, "H2O": 2}, (("H2", "H2O"), ("O2", "H2O"))),
    ("Zn + 2HCl → ZnCl2 + H2", {"Zn": 1, "HCl": 2, "ZnCl2": 1, "H2": 1}, (("Zn", "ZnCl2"),)),
    ("CuO + H2SO4 → CuSO4 + H2O", {"CuO": 1, "H2SO4": 1, "CuSO4": 1, "H2O": 1}, (("CuO", "CuSO4"),)),
    ("C3H8 + 5O2 → 3CO2 + 4H2O", {"C3H8": 1, "O2": 5, "CO2": 3, "H2O": 4}, (("C3H8", "CO2"), ("C3H8", "H2O"))),
    ("2NaOH + H2SO4 → Na2SO4 + 2H2O", {"NaOH": 2, "H2SO4": 1, "Na2SO4": 1, "H2O": 2}, (("NaOH", "Na2SO4"),)),
    ("N2 + 3H2 → 2NH3", {"N2": 1, "H2": 3, "NH3": 2}, (("N2", "NH3"), ("H2", "NH3"))),
    ("2Fe + 3Cl2 → 2FeCl3", {"Fe": 2, "Cl2": 3, "FeCl3": 2}, (("Fe", "FeCl3"),)),
    ("4Al + 3O2 → 2Al2O3", {"Al": 4, "O2": 3, "Al2O3": 2}, (("Al", "Al2O3"),)),
    ("Mg + 2HCl → MgCl2 + H2", {"Mg": 1, "HCl": 2, "MgCl2": 1, "H2": 1}, (("Mg", "MgCl2"),)),
    ("CaCO3 + 2HCl → CaCl2 + H2O + CO2", {"CaCO3": 1, "HCl": 2, "CaCl2": 1, "H2O": 1, "CO2": 1},
     (("CaCO3", "CaCl2"), ("CaCO3", "CO2"))),
    ("2Al2O3 → 4Al + 3O2", {"Al2O3": 2, "Al": 4, "O2": 3}, (("Al2O3", "Al"),)),
    ("C6H12O6 → 2C2H5OH + 2CO2", {"C6H12O6": 1, "C2H5OH": 2, "CO2": 2}, (("C6H12O6", "C2H5OH"),)),
)


def _check_balanced() -> None:
    for eq, coef, pairs in _REACTIONS:
        left, right = eq.split(" → ")
        sides = []
        for side in (left, right):
            c: Counter = Counter()
            for term in side.split(" + "):
                m = re.match(r"^(\d*)(.+)$", term)
                k = int(m.group(1)) if m.group(1) else 1
                if coef.get(m.group(2)) != k:
                    raise ValueError(f"coefficient mismatch in {eq!r}")
                for el, x in atoms(m.group(2)).items():
                    c[el] += x * k
            sides.append(c)
        if sides[0] != sides[1]:
            raise ValueError(f"unbalanced equation {eq!r}")
        for a, b in pairs:
            if a not in coef or b not in coef:
                raise ValueError(f"bad pair in {eq!r}")


_check_balanced()


def _reacting(r, nice_moles: bool):
    """(equation, given, find, mass_given, moles_given, ratio, mass_find) built backwards from nice moles."""
    eq, coef, pairs = r.choice(_REACTIONS)
    a, b = r.choice(pairs)
    ratio = Fraction(coef[b], coef[a])
    if nice_moles:
        na = F(r.choice(("0.05", "0.1", "0.15", "0.2", "0.25", "0.3", "0.4", "0.5", "0.75", "1", "1.5", "2")))
    else:
        na = F(r.choice(("0.1", "0.2", "0.25", "0.5", "1")))
    ma = na * mr(a)
    mb = na * ratio * mr(b)
    if sig_digits(ma) > 4 or ma < 1:
        return None
    if not _rounding_ok(mb, sf=3):
        return None
    return eq, a, b, ma, na, ratio, mb


def _ratio_words(eq: str, a: str, b: str, ratio: Fraction) -> str:
    return f"{chem(a)} : {chem(b)} = {ratio.denominator} : {ratio.numerator}"


def _mol_4(rng):
    eq, a, b, ma, na, ratio, mb = retry(lambda r: _reacting(r, True), rng)
    text = (f"{chem(eq)}. Calculate the mass of {named(b)} made from {n(ma)} g of {named(a)}. "
            f"{ar_text(a, b)} {SF_TXT}")
    sol = (f"Mr of {chem(a)} = {n(mr(a))}, so moles of {chem(a)} = {n(ma)} ÷ {n(mr(a))} = {n(na)} mol. "
           f"Ratio {_ratio_words(eq, a, b, ratio)}, so moles of {chem(b)} = {n(na * ratio)} mol. "
           f"Mass = {n(na * ratio)} × {n(mr(b))} = {fmt_sf(mb, 3)} g")
    return _q(text, _sf_answer(mb, "g"), sol,
              f"Find the moles of {chem(a)} first, then use the balancing numbers in the equation",
              [_m(na * mr(b) if ratio != 1 else None, "g",
                  f"Use the balancing numbers: {_ratio_words(eq, a, b, ratio)}"),
               _m(na / ratio * mr(b) if ratio != 1 else None, "g",
                  f"The ratio is the wrong way round: {_ratio_words(eq, a, b, ratio)}"),
               _m(ma, "g", "Masses are not conserved one-for-one between substances — convert to moles first")])


def _mol_5(rng):
    kind = rng.choice(("moles", "mass_molecules", "mass_atoms"))
    if kind == "moles":
        def make(r):
            nn = F(r.randrange(11, 500)) / 100
            v = nn * AVOGADRO
            return None if not _rounding_ok(v, sf=3) else (nn, v)
        nn, v = retry(make, rng)
        f = rng.choice(("H2O", "CO2", "CH4", "NH3", "O2", "N2"))
        text = (f"How many molecules are there in {n(nn)} mol of {named(f)}? {AVOGADRO_TXT} "
                f"Give your answer in standard form to 3 significant figures.")
        sol = f"number of molecules = moles × Avogadro constant = {n(nn)} × 6.02 × 10^23 = {fmt_std(v, 3)}"
        hint = "Multiply the number of moles by the Avogadro constant"
        mistakes = [std_mistake(nn / AVOGADRO, "", "Multiply the moles by the Avogadro constant — don't divide", round_to_sf=3)]
    else:
        def make(r):
            if kind == "mass_atoms":
                f = r.choice(("C", "Mg", "Na", "Fe", "Ca", "Al", "Cu", "S"))
            else:
                f = r.choice(("H2O", "CO2", "CH4", "NH3", "O2", "N2", "C2H6", "SO2"))
            nn = F(r.choice(("0.1", "0.2", "0.25", "0.4", "0.5", "1.5", "2", "2.5", "3", "0.05", "0.3")))
            mass = nn * mr(f)
            v = nn * AVOGADRO
            if sig_digits(mass) > 4 or not _rounding_ok(v, sf=3):
                return None
            return f, nn, mass, v
        f, nn, mass, v = retry(make, rng)
        what = "atoms" if kind == "mass_atoms" else "molecules"
        text = (f"How many {what} are there in {n(mass)} g of {named(f)}? {ar_text(f)} {AVOGADRO_TXT} "
                f"Give your answer in standard form to 3 significant figures.")
        sol = (f"Mr = {n(mr(f))}" if kind != "mass_atoms" else f"Ar = {n(mr(f))}") + \
            f". moles = {n(mass)} ÷ {n(mr(f))} = {n(nn)} mol. {what} = {n(nn)} × 6.02 × 10^23 = {fmt_std(v, 3)}"
        hint = "Convert the mass into moles first, then multiply by the Avogadro constant"
        mistakes = [std_mistake(mass * AVOGADRO, "", "Convert the mass into moles first (moles = mass ÷ Mr)", round_to_sf=3),
                    std_mistake(mr(f) * AVOGADRO, "", "Use moles = mass ÷ Mr before multiplying by the Avogadro constant",
                                round_to_sf=3)]
    return _q(text, std_answer(v, "", round_to_sf=3), sol, hint, mistakes)


# ========================================================= concentration

_SOLUTES = ("sodium chloride", "copper(II) sulfate", "sodium hydroxide", "potassium nitrate", "glucose",
            "magnesium sulfate", "sodium carbonate", "potassium chloride")
_VOL_DM3 = ("0.1", "0.2", "0.25", "0.4", "0.5", "1", "2", "2.5")


def _conc_1(rng):
    def make(r):
        v = F(r.choice(_VOL_DM3))
        c = F(r.choice(("2", "4", "5", "8", "10", "12", "15", "16", "20", "25", "30", "40", "50", "60", "80")))
        m = c * v
        return None if (m.denominator != 1 and m * 10 != int(m * 10)) else (v, c, m)
    v, c, m = retry(make, rng)
    s = rng.choice(_SOLUTES)
    return _q(f"{n(m)} g of {s} is dissolved in water to make {n(v)} dm³ of solution. Calculate the concentration "
              f"of the solution in g/dm³.",
              _exact(c, "g/dm³"), f"concentration = mass ÷ volume = {n(m)} ÷ {n(v)} = {n(c)} g/dm³",
              "concentration (g/dm³) = mass (g) ÷ volume (dm³)",
              [_m(m * v, "g/dm³", "concentration = mass ÷ volume — divide, don't multiply", sf=None),
               _m(v / m, "g/dm³", "concentration = mass ÷ volume — you divided the wrong way round")])


def _conc_2(rng):
    vcm = rng.choice((50, 100, 200, 250, 400, 500))
    c = F(rng.choice(("4", "5", "8", "10", "12", "16", "20", "24", "25", "30", "40", "50", "60")))
    m = c * vcm / 1000
    s = rng.choice(_SOLUTES)
    vd = Fraction(vcm, 1000)
    if rng.random() < 0.5:
        return _q(f"{n(m)} g of {s} is dissolved in water to make {vcm} cm³ of solution. Calculate the concentration "
                  f"of the solution in g/dm³.",
                  _exact(c, "g/dm³"), f"{vcm} cm³ = {vcm} ÷ 1000 = {n(vd)} dm³. concentration = {n(m)} ÷ {n(vd)} = {n(c)} g/dm³",
                  f"Convert {vcm} cm³ into dm³ first: 1 dm³ = 1000 cm³",
                  [_m(m / vcm, "g/dm³", f"Convert the volume into dm³ first: {vcm} ÷ 1000 = {n(vd)} dm³"),
                   _m(m / (Fraction(vcm, 100)), "g/dm³", "1 dm³ = 1000 cm³, so divide the volume by 1000, not 100")])
    return _q(f"A solution of {s} has a concentration of {n(c)} g/dm³. Calculate the mass of {s} in {vcm} cm³ of "
              f"this solution. Give your answer in grams.",
              _exact(m, "g"), f"{vcm} cm³ = {n(vd)} dm³. mass = concentration × volume = {n(c)} × {n(vd)} = {n(m)} g",
              f"Convert {vcm} cm³ into dm³, then use mass = concentration × volume",
              [_m(c * vcm, "g", f"Convert the volume into dm³ first: {vcm} ÷ 1000 = {n(vd)} dm³"),
               _m(c / vd, "g", "mass = concentration × volume — multiply, don't divide")])


_ACIDS_ALKALIS = ("hydrochloric acid", "sodium hydroxide", "nitric acid", "potassium hydroxide", "sulfuric acid")


def _conc_3(rng):
    vcm = rng.choice((20, 25, 50, 100, 200, 250, 400, 500))
    c = F(rng.choice(("0.05", "0.1", "0.2", "0.25", "0.4", "0.5", "0.8", "1", "1.5", "2")))
    nn = c * vcm / 1000
    s = rng.choice(_ACIDS_ALKALIS)
    vd = Fraction(vcm, 1000)
    if rng.random() < 0.6:
        return _q(f"A solution contains {n(nn)} mol of {s} in {vcm} cm³. Calculate its concentration in mol/dm³.",
                  _exact(c, "mol/dm³"), f"{vcm} cm³ = {n(vd)} dm³. concentration = moles ÷ volume = {n(nn)} ÷ {n(vd)} = {n(c)} mol/dm³",
                  f"Convert {vcm} cm³ into dm³, then divide the moles by the volume",
                  [_m(nn / vcm, "mol/dm³", f"Convert the volume into dm³ first: {vcm} ÷ 1000 = {n(vd)} dm³"),
                   _m(nn * vd, "mol/dm³", "concentration = moles ÷ volume — divide, don't multiply")])
    return _q(f"How many moles of {s} are there in {vcm} cm³ of a {n(c)} mol/dm³ solution?",
              _exact(nn, "mol"), f"{vcm} cm³ = {n(vd)} dm³. moles = concentration × volume = {n(c)} × {n(vd)} = {n(nn)} mol",
              f"Convert {vcm} cm³ into dm³, then use moles = concentration × volume",
              [_m(c * vcm, "mol", f"Convert the volume into dm³ first: {vcm} ÷ 1000 = {n(vd)} dm³"),
               _m(c / vd, "mol", "moles = concentration × volume — multiply, don't divide")])


_ONE_TO_ONE = (("hydrochloric acid", "sodium hydroxide", "HCl + NaOH → NaCl + H2O"),
               ("nitric acid", "potassium hydroxide", "HNO3 + KOH → KNO3 + H2O"),
               ("hydrochloric acid", "potassium hydroxide", "HCl + KOH → KCl + H2O"),
               ("nitric acid", "sodium hydroxide", "HNO3 + NaOH → NaNO3 + H2O"))


def _titre(r) -> Fraction:
    return Fraction(r.randrange(360, 571) * 5, 100)          # 18.00 .. 28.50 cm³, ending in 0 or 5


def _conc_4(rng):
    unknown_is_alkali = rng.random() < 0.5

    def make(r):
        acid, alkali, eq = r.choice(_ONE_TO_ONE)
        known_c = F(r.choice(("0.1", "0.05", "0.2", "0.15")))
        t = _titre(r)
        if unknown_is_alkali:          # known acid in the burette (titre), unknown alkali 25.0 cm³ in the flask
            nk = known_c * t / 1000
            unknown = nk / F("0.025")
        else:                          # unknown acid in the burette (titre), known alkali 25.0 cm³ in the flask
            nk = known_c * F("25.0") / 1000
            unknown = nk / (t / 1000)
        return None if not _rounding_ok(unknown, sf=3) else (acid, alkali, eq, known_c, t, nk, unknown)
    acid, alkali, eq, known_c, t, nk, unknown = retry(make, rng)
    tt = fmt_dp(t, 2)
    if unknown_is_alkali:
        text = (f"{chem(eq)}. In a titration, 25.0 cm³ of {alkali} solution was neutralised by {tt} cm³ of "
                f"{fmt_sf(known_c, 3)} mol/dm³ {acid}. Calculate the concentration of the {alkali} solution in mol/dm³. {SF_TXT}")
        sol = (f"moles of acid = {fmt_sf(known_c, 3)} × {tt} ÷ 1000 = {n(nk)} mol. Ratio 1 : 1, so moles of alkali = {n(nk)} mol. "
               f"concentration = {n(nk)} ÷ 0.025 = {fmt_sf(unknown, 3)} mol/dm³")
    else:
        text = (f"{chem(eq)}. In a titration, {tt} cm³ of {acid} neutralised 25.0 cm³ of {fmt_sf(known_c, 3)} mol/dm³ "
                f"{alkali}. Calculate the concentration of the {acid} in mol/dm³. {SF_TXT}")
        sol = (f"moles of alkali = {fmt_sf(known_c, 3)} × 25.0 ÷ 1000 = {n(nk)} mol. Ratio 1 : 1, so moles of acid = {n(nk)} mol. "
               f"concentration = {n(nk)} ÷ {n(t / 1000)} = {fmt_sf(unknown, 3)} mol/dm³")
    wrong_way = known_c * known_c / unknown
    return _q(text, _sf_answer(unknown, "mol/dm³"), sol,
              "Work out the moles of the solution whose concentration you know, then use the 1 : 1 ratio",
              [_m(wrong_way, "mol/dm³", "Check which volume goes with which solution: moles = concentration × its own volume"),
               _m(nk, "mol/dm³", "That's the number of moles — divide by the volume in dm³ to get the concentration")])


def _conc_5(rng):
    if rng.random() < 0.5:
        def make(r):
            base = r.choice(("sodium hydroxide", "potassium hydroxide"))
            known = r.choice(("base", "acid"))
            c_known = F(r.choice(("0.1", "0.2", "0.05", "0.15")))
            t = _titre(r)
            v = F("25.0")
            if known == "base":       # base of known concentration in the burette, unknown acid in the flask
                n_base = c_known * t / 1000
                n_acid = n_base / 2
                c = n_acid / (v / 1000)
            else:                     # acid of known concentration in the burette, unknown base in the flask
                n_acid = c_known * t / 1000
                n_base = n_acid * 2
                c = n_base / (v / 1000)
            return None if not _rounding_ok(c, sf=3) else (base, known, c_known, t, c, n_acid, n_base)
        base, known, c_known, t, c, n_acid, n_base = retry(make, rng)
        formula = "NaOH" if base.startswith("sodium") else "KOH"
        salt = "Na2SO4" if formula == "NaOH" else "K2SO4"
        eq = chem(f"H2SO4 + 2{formula} → {salt} + 2H2O")
        tt = fmt_dp(t, 2)
        if known == "base":
            text = (f"{eq}. In a titration, {tt} cm³ of {fmt_sf(c_known, 3)} mol/dm³ {base} neutralised 25.0 cm³ of sulfuric "
                    f"acid. Calculate the concentration of the sulfuric acid in mol/dm³. {SF_TXT}")
            sol = (f"moles of {formula} = {fmt_sf(c_known, 3)} × {tt} ÷ 1000 = {n(n_base)} mol. Ratio H₂SO₄ : {formula} = 1 : 2, "
                   f"so moles of H₂SO₄ = {n(n_acid)} mol. concentration = {n(n_acid)} ÷ 0.025 = {fmt_sf(c, 3)} mol/dm³")
            no_ratio, wrong_ratio = n_base / F("0.025"), n_base * 2 / F("0.025")
        else:
            text = (f"{eq}. In a titration, {tt} cm³ of {fmt_sf(c_known, 3)} mol/dm³ sulfuric acid neutralised 25.0 cm³ of "
                    f"{base}. Calculate the concentration of the {base} in mol/dm³. {SF_TXT}")
            sol = (f"moles of H₂SO₄ = {fmt_sf(c_known, 3)} × {tt} ÷ 1000 = {n(n_acid)} mol. Ratio H₂SO₄ : {formula} = 1 : 2, "
                   f"so moles of {formula} = {n(n_base)} mol. concentration = {n(n_base)} ÷ 0.025 = {fmt_sf(c, 3)} mol/dm³")
            no_ratio, wrong_ratio = n_acid / F("0.025"), n_acid / 2 / F("0.025")
        return _q(text, _sf_answer(c, "mol/dm³"), sol,
                  "Find the moles of the solution you know about, then use the 1 : 2 ratio from the equation",
                  [_m(no_ratio, "mol/dm³", f"Use the ratio from the equation: H₂SO₄ : {formula} = 1 : 2"),
                   _m(wrong_ratio, "mol/dm³", f"The ratio is the wrong way round: 1 H₂SO₄ reacts with 2 {formula}")])
    # gas volumes at RTP
    gas = rng.choice(("CO2", "O2", "H2", "N2", "CH4", "NH3", "Cl2", "SO2"))
    nn = F(rng.choice(("0.05", "0.1", "0.2", "0.25", "0.4", "0.5", "0.75", "1.5", "2", "2.5")))
    mass = nn * mr(gas)
    vol = nn * 24
    if rng.random() < 0.5:
        text = (f"Calculate the volume of {n(mass)} g of {named(gas)} gas at room temperature and pressure. "
                f"{ar_text(gas)} {RTP_TXT} Give your answer in dm³.")
        sol = f"moles = {n(mass)} ÷ {n(mr(gas))} = {n(nn)} mol. volume = {n(nn)} × 24 = {n(vol)} dm³"
        return _q(text, _exact(vol, "dm³"), sol, "Convert the mass into moles, then multiply by 24 dm³",
                  [_m(mass * 24, "dm³", "Convert the mass into moles first (moles = mass ÷ Mr)"),
                   _m(nn / 24, "dm³", "volume = moles × 24 — multiply, don't divide")])
    text = (f"What mass of {named(gas)} gas occupies {n(vol)} dm³ at room temperature and pressure? "
            f"{ar_text(gas)} {RTP_TXT} Give your answer in grams.")
    sol = f"moles = {n(vol)} ÷ 24 = {n(nn)} mol. mass = {n(nn)} × {n(mr(gas))} = {n(mass)} g"
    return _q(text, _exact(mass, "g"), sol, "Find the moles of gas first: moles = volume ÷ 24",
              [_m(vol * 24 * mr(gas), "g", "moles of gas = volume ÷ 24 — divide, don't multiply"),
               _m(nn, "g", "That's the number of moles — multiply by the Mr to get the mass")])


# ======================================================= yield & economy

def _yield_1(rng):
    def make(r):
        theo = F(r.randrange(40, 400)) / 10
        frac = F(r.randrange(45, 98)) / 100
        actual = round(theo * frac * 10) / F(10)
        v = actual / theo * 100
        return None if (actual <= 0 or actual >= theo or not _rounding_ok(v, dp=1)) else (theo, actual, v)
    theo, actual, v = retry(make, rng)
    prod = rng.choice(("copper(II) sulfate crystals", "magnesium oxide", "aspirin", "zinc chloride", "sodium chloride",
                       "calcium oxide", "iron"))
    return _q(f"A student's reaction could make a maximum of {fmt_dp(theo, 1)} g of {prod}. The student actually made "
              f"{fmt_dp(actual, 1)} g. Calculate the percentage yield. {DP_TXT}",
              _dp_answer(v, "%"), f"percentage yield = actual ÷ theoretical × 100 = {fmt_dp(actual, 1)} ÷ {fmt_dp(theo, 1)} × 100 = {fmt_dp(v, 1)}%",
              "percentage yield = mass actually made ÷ maximum theoretical mass × 100",
              [_m(theo / actual * 100, "%", "Divide the actual mass by the theoretical mass, not the other way round", dp=1),
               _m(actual / theo, "%", "Multiply by 100 to turn the fraction into a percentage", sf=2)])


def _ae_2(rng):
    def make(r):
        useful = F(r.randrange(20, 300))
        waste = F(r.randrange(10, 300))
        if r.random() < 0.3:
            useful += Fraction(1, 2)
        total = useful + waste
        v = useful / total * 100
        return None if not _rounding_ok(v, dp=1) else (useful, waste, total, v)
    useful, waste, total, v = retry(make, rng)
    return _q(f"A reaction makes a useful product and a waste product. The total Mr of all the reactants is "
              f"{n(total)}. The total Mr of the useful product formed is {n(useful)}. Calculate the atom economy "
              f"of the reaction. {DP_TXT}",
              _dp_answer(v, "%"), f"atom economy = Mr of useful product ÷ total Mr of reactants × 100 = {n(useful)} ÷ {n(total)} × 100 = {fmt_dp(v, 1)}%",
              "atom economy = total Mr of the useful product ÷ total Mr of all the reactants × 100",
              [_m(useful / waste * 100, "%", "Divide by the total Mr of all the reactants, not the waste product", dp=1),
               _m(waste / total * 100, "%", "That's the percentage that is wasted — use the useful product", dp=1),
               _m(useful / total, "%", "Multiply by 100 to give a percentage", sf=2)])


def _yield_3(rng):
    eq, a, b, ma, na, ratio, mb = retry(lambda r: _reacting(r, True), rng)
    text = (f"{chem(eq)}. Calculate the theoretical (maximum) mass of {named(b)} that can be made from {n(ma)} g "
            f"of {named(a)}. {ar_text(a, b)} {SF_TXT}")
    sol = (f"moles of {chem(a)} = {n(ma)} ÷ {n(mr(a))} = {n(na)} mol. {_ratio_words(eq, a, b, ratio)}, so moles of "
           f"{chem(b)} = {n(na * ratio)} mol. Mass = {n(na * ratio)} × {n(mr(b))} = {fmt_sf(mb, 3)} g")
    return _q(text, _sf_answer(mb, "g"), sol,
              f"Find the moles of {chem(a)} first, then use the balancing numbers in the equation",
              [_m(na * mr(b) if ratio != 1 else None, "g",
                  f"Use the balancing numbers: {_ratio_words(eq, a, b, ratio)}"),
               _m(na / ratio * mr(b) if ratio != 1 else None, "g",
                  f"The ratio is the wrong way round: {_ratio_words(eq, a, b, ratio)}"),
               _m(ma, "g", "Convert the mass into moles first — masses don't transfer one-for-one")])


def _yield_4(rng):
    def make(r):
        out = _reacting(r, True)
        if out is None:
            return None
        eq, a, b, ma, na, ratio, mb = out
        if sig_digits(mb) > 4:
            return None
        frac = F(r.randrange(55, 96)) / 100
        actual = round(mb * frac * 10) / F(10)
        v = actual / mb * 100
        if actual <= 0 or actual >= mb or not _rounding_ok(v, dp=1):
            return None
        return eq, a, b, ma, na, ratio, mb, actual, v
    eq, a, b, ma, na, ratio, mb, actual, v = retry(make, rng)
    text = (f"{chem(eq)}. A student used {n(ma)} g of {named(a)} and made {fmt_dp(actual, 1)} g of {chem(b)}. "
            f"Calculate the percentage yield. {ar_text(a, b)} {DP_TXT}")
    sol = (f"moles of {chem(a)} = {n(ma)} ÷ {n(mr(a))} = {n(na)} mol, so moles of {chem(b)} = {n(na * ratio)} mol. "
           f"Theoretical mass = {n(na * ratio)} × {n(mr(b))} = {n(mb)} g. % yield = {fmt_dp(actual, 1)} ÷ {n(mb)} × 100 = {fmt_dp(v, 1)}%")
    wrong_theo = na * mr(b)
    return _q(text, _dp_answer(v, "%"), sol,
              f"First work out the theoretical mass of {chem(b)}, then use percentage yield = actual ÷ theoretical × 100",
              [_m(actual / wrong_theo * 100 if ratio != 1 else None, "%",
                  f"Use the balancing numbers to find the theoretical mass: {_ratio_words(eq, a, b, ratio)}", dp=1),
               _m(actual / ma * 100, "%", f"Compare with the theoretical mass of {chem(b)}, not the mass of {chem(a)} used", dp=1),
               _m(mb / actual * 100, "%", "Divide the actual mass by the theoretical mass, not the other way round", dp=1)])


# (equation, {formula: coefficient}, reactants, useful product)
_AE_REACTIONS = (
    ("CaCO3 → CaO + CO2", {"CaCO3": 1, "CaO": 1, "CO2": 1}, ("CaCO3",), "CaO"),
    ("Fe2O3 + 3CO → 2Fe + 3CO2", {"Fe2O3": 1, "CO": 3, "Fe": 2, "CO2": 3}, ("Fe2O3", "CO"), "Fe"),
    ("C6H12O6 → 2C2H5OH + 2CO2", {"C6H12O6": 1, "C2H5OH": 2, "CO2": 2}, ("C6H12O6",), "C2H5OH"),
    ("2H2O2 → 2H2O + O2", {"H2O2": 2, "H2O": 2, "O2": 1}, ("H2O2",), "O2"),
    ("CH4 + H2O → CO + 3H2", {"CH4": 1, "H2O": 1, "CO": 1, "H2": 3}, ("CH4", "H2O"), "H2"),
    ("Zn + H2SO4 → ZnSO4 + H2", {"Zn": 1, "H2SO4": 1, "ZnSO4": 1, "H2": 1}, ("Zn", "H2SO4"), "ZnSO4"),
    ("Mg + 2HCl → MgCl2 + H2", {"Mg": 1, "HCl": 2, "MgCl2": 1, "H2": 1}, ("Mg", "HCl"), "MgCl2"),
    ("2NaCl + 2H2O → 2NaOH + Cl2 + H2", {"NaCl": 2, "H2O": 2, "NaOH": 2, "Cl2": 1, "H2": 1}, ("NaCl", "H2O"), "NaOH"),
    ("2NaCl + 2H2O → 2NaOH + Cl2 + H2", {"NaCl": 2, "H2O": 2, "NaOH": 2, "Cl2": 1, "H2": 1}, ("NaCl", "H2O"), "Cl2"),
    ("CuO + H2SO4 → CuSO4 + H2O", {"CuO": 1, "H2SO4": 1, "CuSO4": 1, "H2O": 1}, ("CuO", "H2SO4"), "CuSO4"),
    ("2Al2O3 → 4Al + 3O2", {"Al2O3": 2, "Al": 4, "O2": 3}, ("Al2O3",), "Al"),
    ("C2H5OH → C2H4 + H2O", {"C2H5OH": 1, "C2H4": 1, "H2O": 1}, ("C2H5OH",), "C2H4"),
    ("2Mg + O2 → 2MgO", {"Mg": 2, "O2": 1, "MgO": 2}, ("Mg", "O2"), "MgO"),
)


def _check_ae() -> None:
    for eq, coef, reac, useful in _AE_REACTIONS:
        left, right = eq.split(" → ")
        tot = []
        for side in (left, right):
            c: Counter = Counter()
            for term in side.split(" + "):
                m = re.match(r"^(\d*)(.+)$", term)
                k = int(m.group(1)) if m.group(1) else 1
                if coef.get(m.group(2)) != k:
                    raise ValueError(f"coefficient mismatch in {eq!r}")
                for el, x in atoms(m.group(2)).items():
                    c[el] += x * k
            tot.append(c)
        if tot[0] != tot[1] or useful not in coef:
            raise ValueError(f"bad atom-economy reaction {eq!r}")


_check_ae()


def _ae_5(rng):
    def make(r):
        eq, coef, reac, useful = r.choice(_AE_REACTIONS)
        total = sum((coef[f] * mr(f) for f in reac), Fraction(0))
        top = coef[useful] * mr(useful)
        v = top / total * 100
        if v >= 100 or not _rounding_ok(v, dp=1):
            return None
        return eq, coef, reac, useful, total, top, v
    eq, coef, reac, useful, total, top, v = retry(make, rng)
    species = list(coef)
    text = (f"{chem(eq)}. Calculate the atom economy for making {named(useful)} in this reaction. "
            f"{ar_text(*species)} {DP_TXT}")
    parts = " + ".join(f"{coef[f]} × {n(mr(f))}" if coef[f] > 1 else n(mr(f)) for f in reac)
    if len(reac) > 1 or coef[reac[0]] > 1:
        parts = f"{parts} = {n(total)}"
    useful_txt = f"{coef[useful]} × {n(mr(useful))} = {n(top)}" if coef[useful] > 1 else n(top)
    sol = (f"Total Mr of reactants = {parts}. Mr of useful product = {useful_txt}. "
           f"Atom economy = {n(top)} ÷ {n(total)} × 100 = {fmt_dp(v, 1)}%")
    no_coef_total = sum((mr(f) for f in reac), Fraction(0))
    no_coef = mr(useful) / no_coef_total * 100
    return _q(text, _dp_answer(v, "%"), sol,
              "Atom economy = total Mr of the useful product ÷ total Mr of all the reactants × 100 — use the balancing numbers",
              [_m(no_coef if no_coef != v and no_coef < 100 else None, "%",
                  "Multiply each Mr by its balancing number in the equation before adding", dp=1),
               _m(mr(useful) / total * 100 if coef[useful] > 1 else None, "%",
                  f"There are {coef[useful]} {chem(useful)} in the equation — multiply its Mr by {coef[useful]}", dp=1)])


# ================================================================= rates

def _rate_1(rng):
    rate = F(rng.choice(("0.01", "0.02", "0.025", "0.04", "0.05", "0.08", "0.1", "0.12", "0.15", "0.2", "0.25")))
    t = rng.choice((10, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200))
    m = rate * t
    what = rng.choice(("marble chips reacted with hydrochloric acid", "magnesium ribbon reacted with acid",
                       "a reaction flask gave off carbon dioxide"))
    return _q(f"In an experiment, {what}. The mass of the flask went down by {n(m)} g in {t} s. Calculate the mean "
              f"rate of reaction in g/s.",
              _exact(rate, "g/s"), f"mean rate = mass lost ÷ time = {n(m)} ÷ {t} = {n(rate)} g/s",
              "mean rate of reaction = amount of product formed (or reactant used) ÷ time",
              [_m(Fraction(t) / m, "g/s", "Divide the mass by the time, not the time by the mass"),
               _m(m * t, "g/s", "Divide the mass by the time — don't multiply", sf=None)])


def _rate_2(rng):
    def make(r):
        rate = F(r.choice(("0.2", "0.25", "0.4", "0.5", "0.6", "0.75", "0.8", "1", "1.2", "1.5", "2", "2.5")))
        mins = F(r.choice(("1", "1.5", "2", "2.5", "3", "4", "5")))
        v = rate * 60 * mins
        return (rate, mins, v) if v.denominator == 1 else None
    rate, mins, v = retry(make, rng)
    word = "minute" if mins == 1 else "minutes"
    secs = 60 * mins
    return _q(f"A reaction produced {n(v)} cm³ of hydrogen gas in {n(mins)} {word}. Calculate the mean rate of "
              f"reaction in cm³/s.",
              _exact(rate, "cm³/s"), f"{n(mins)} {word} = {n(secs)} s. mean rate = {n(v)} ÷ {n(secs)} = {n(rate)} cm³/s",
              "Convert the time into seconds first, then divide the volume by the time",
              [_m(v / mins, "cm³/s", f"That's the rate per minute — convert {n(mins)} {word} into seconds first (× 60)"),
               _m(v / (mins * 100), "cm³/s", "There are 60 seconds in a minute, not 100")])


def _rate_3(rng):
    def make(r):
        t1 = r.choice((10, 20, 30, 40, 60))
        dt = r.choice((10, 20, 30, 40, 50, 60))
        rate = F(r.choice(("0.2", "0.3", "0.4", "0.5", "0.6", "0.8", "0.9", "1.2", "1.5")))
        v1 = r.randrange(8, 40)
        v2 = v1 + rate * dt
        if v2.denominator != 1:
            return None
        return t1, t1 + dt, v1, v2, rate
    t1, t2, v1, v2, rate = retry(make, rng)
    return _q(f"The volume of gas collected in a reaction was {v1} cm³ at {t1} s and {n(v2)} cm³ at {t2} s. "
              f"Calculate the mean rate of reaction between {t1} s and {t2} s in cm³/s.",
              _exact(rate, "cm³/s"),
              f"change in volume = {n(v2)} − {v1} = {n(v2 - v1)} cm³; time taken = {t2} − {t1} = {t2 - t1} s; "
              f"mean rate = {n(v2 - v1)} ÷ {t2 - t1} = {n(rate)} cm³/s",
              "Find the change in volume and the change in time between the two readings",
              [_m(v2 / t2, "cm³/s", f"Use the change between the two readings, not just the reading at {t2} s"),
               _m(v2 / (t2 - t1), "cm³/s", f"Use the change in volume: {n(v2)} − {v1}"),
               _m((v2 - v1) / t2, "cm³/s", f"Use the change in time: {t2} − {t1}")])


def _rate_4(rng):
    if rng.random() < 0.5:
        def make(r):
            metal = r.choice(("Mg", "Zn", "Ca"))
            mass = F(r.randrange(5, 60)) / 100
            t = r.choice((20, 25, 30, 40, 45, 50, 60, 75, 80, 90, 120))
            v = mass / AR[metal] / t
            return None if not _rounding_ok(v, sf=3) or sig_digits(v) <= 3 else (metal, mass, t, v)
        metal, mass, t, v = retry(make, rng)
        nm = mass / AR[metal]
        text = (f"{n(mass)} g of {_NAMES[metal]} reacted completely with excess acid in {t} s. Calculate the mean "
                f"rate at which the {_NAMES[metal]} was used up, in mol/s. Relative atomic mass (Ar): {metal} = "
                f"{n(AR[metal])}. {SF_TXT}")
        ans = _sf_answer(v, "mol/s")
        sol = (f"moles of {metal} = {n(mass)} ÷ {n(AR[metal])} = {_approx(nm)} mol. mean rate = {_approx(nm)} ÷ {t} = "
               f"{ans.display}")
        return _q(text, ans, sol, "Convert the mass into moles first, then divide by the time",
                  [_m(mass / t, "mol/s", "That's the rate in g/s — convert the mass into moles first"),
                   _m(mass * AR[metal] / t, "mol/s", "moles = mass ÷ Ar — divide, don't multiply")])
    def make(r):
        vol = r.randrange(12, 240)
        t = r.choice((20, 30, 40, 50, 60, 80, 90, 100, 120))
        v = Fraction(vol, 24000) / t
        return None if not _rounding_ok(v, sf=3) or sig_digits(v) <= 3 else (vol, t, v)
    vol, t, v = retry(make, rng)
    nm = Fraction(vol, 24000)
    text = (f"A reaction produced {vol} cm³ of carbon dioxide in {t} s. One mole of any gas occupies 24 000 cm³ at "
            f"room temperature and pressure. Calculate the mean rate of reaction in mol/s. {SF_TXT}")
    ans = _sf_answer(v, "mol/s")
    sol = f"moles of gas = {vol} ÷ 24 000 = {_approx(nm)} mol. mean rate = {_approx(nm)} ÷ {t} = {ans.display}"
    return _q(text, ans, sol, "Convert the volume of gas into moles first, then divide by the time",
              [_m(Fraction(vol, t), "mol/s", "That's the rate in cm³/s — convert the volume into moles first"),
               _m(Fraction(vol, 24) / t, "mol/s", "One mole of gas is 24 000 cm³ — divide the volume by 24 000, not 24")])


def _rate_5(rng):
    kind = rng.choice(("mass", "gas", "gas_min"))
    if kind == "mass":
        rate = F(rng.choice(("0.02", "0.04", "0.05", "0.1", "0.15", "0.2", "0.25")))
        t = rng.choice((20, 30, 40, 50, 60, 80, 100, 120))
        m = rate * t
        return _q(f"A reaction loses mass at a mean rate of {n(rate)} g/s. How long does it take to lose {n(m)} g? "
                  f"Give your answer in seconds.",
                  _exact(t, "s"), f"time = mass lost ÷ rate = {n(m)} ÷ {n(rate)} = {t} s",
                  "Rearrange mean rate = mass lost ÷ time to make time the subject",
                  [_m(m * rate, "s", "time = mass lost ÷ rate — divide, don't multiply"),
                   _m(rate / m, "s", "time = mass lost ÷ rate — you divided the wrong way round")])
    rate = F(rng.choice(("0.2", "0.25", "0.4", "0.5", "0.8", "1.2", "1.5", "2", "2.5")))
    if kind == "gas":
        t = rng.choice((15, 20, 24, 30, 40, 45, 60, 80, 90))
        v = rate * t
        if v.denominator != 1:
            t, v = 40, rate * 40
        return _q(f"A reaction gives off gas at a mean rate of {n(rate)} cm³/s. How long does it take to collect "
                  f"{n(v)} cm³ of gas? Give your answer in seconds.",
                  _exact(t, "s"), f"time = volume ÷ rate = {n(v)} ÷ {n(rate)} = {t} s",
                  "Rearrange mean rate = volume ÷ time to make time the subject",
                  [_m(v * rate, "s", "time = volume ÷ rate — divide, don't multiply"),
                   _m(rate / v, "s", "time = volume ÷ rate — you divided the wrong way round")])
    mins = rng.choice((2, 3, 4, 5, 6, 8, 10))
    v = rate * 60 * mins
    return _q(f"A reaction gives off gas at a mean rate of {n(rate)} cm³/s. How many minutes does it take to collect "
              f"{n(v)} cm³ of gas?",
              _exact(mins, "min"), f"time = {n(v)} ÷ {n(rate)} = {n(60 * mins)} s = {n(60 * mins)} ÷ 60 = {mins} minutes",
              "Find the time in seconds first, then convert it into minutes",
              [_m(v / rate / 3600, "min", "There are 60 seconds in a minute — divide the seconds by 60"),
               _m(v * rate / 60, "min", "time = volume ÷ rate — divide, don't multiply")])


# ================================================================ Rf values

def _rf_text_round(v) -> str:
    return fmt_dp(v, 2)


def _rf_1(rng):
    def make(r):
        d = F(r.randrange(50, 121)) / 10
        s = F(r.randrange(5, int(d * 10) - 4)) / 10
        v = s / d
        return None if not _rounding_ok(v, dp=2) else (s, d, v)
    s, d, v = retry(make, rng)
    return _q(f"In a paper chromatography experiment, a spot moved {n(s)} cm from the start line. The solvent front "
              f"moved {n(d)} cm from the start line. Calculate the Rf value of the spot. Give your answer to 2 decimal places.",
              num_answer(v, fmt_dp(v, 2), dp=2), f"Rf = distance moved by spot ÷ distance moved by solvent = {n(s)} ÷ {n(d)} = {fmt_dp(v, 2)}",
              "Rf = distance moved by the substance ÷ distance moved by the solvent",
              [_m(d / s, "", "Divide the spot distance by the solvent distance — an Rf value is always less than 1", dp=2)])


def _rf_2(rng):
    def make(r):
        d = F(r.randrange(50, 121)) / 10
        smm = r.randrange(5, int(d * 10) - 4)
        v = F(smm) / 10 / d
        return None if not _rounding_ok(v, dp=2) else (smm, d, v)
    smm, d, v = retry(make, rng)
    return _q(f"A spot on a chromatogram moved {smm} mm from the start line. The solvent front moved {n(d)} cm from "
              f"the start line. Calculate the Rf value of the spot. Give your answer to 2 decimal places.",
              num_answer(v, fmt_dp(v, 2), dp=2),
              f"{smm} mm = {n(F(smm) / 10)} cm. Rf = {n(F(smm) / 10)} ÷ {n(d)} = {fmt_dp(v, 2)}",
              "Put both distances into the same unit first (10 mm = 1 cm)",
              [_m(F(smm) / d, "", f"Convert {smm} mm into cm first: {smm} ÷ 10 = {n(F(smm) / 10)} cm", dp=2),
               _m(d / (F(smm) / 10), "", "Divide the spot distance by the solvent distance — an Rf value is always less than 1", dp=2)])


def _rf_3(rng):
    def make(r):
        rf = F(r.randrange(10, 96)) / 100
        d = F(r.randrange(50, 121)) / 10
        s = rf * d
        return None if not _rounding_ok(s, dp=1) else (rf, d, s)
    rf, d, s = retry(make, rng)
    return _q(f"A substance has an Rf value of {n(rf)} in a solvent. In a chromatography experiment the solvent front "
              f"moved {n(d)} cm from the start line. How far did the substance move from the start line? Give your answer "
              f"in cm to 1 decimal place.",
              _dp_answer(s, "cm", 1), f"distance moved by substance = Rf × distance moved by solvent = {n(rf)} × {n(d)} = {fmt_dp(s, 1)} cm",
              "Rearrange Rf = distance moved by substance ÷ distance moved by solvent",
              [_m(d / rf, "cm", "Multiply the Rf value by the solvent distance — don't divide", dp=1)])


def _rf_4(rng):
    def make(r):
        rf = F(r.randrange(15, 91)) / 100
        s = F(r.randrange(10, 80)) / 10
        d = s / rf
        return None if (d > 20 or d < 3 or not _rounding_ok(d, dp=1)) else (rf, s, d)
    rf, s, d = retry(make, rng)
    return _q(f"A spot with an Rf value of {n(rf)} moved {n(s)} cm from the start line. How far did the solvent front "
              f"move from the start line? Give your answer in cm to 1 decimal place.",
              _dp_answer(d, "cm", 1), f"distance moved by solvent = distance moved by spot ÷ Rf = {n(s)} ÷ {n(rf)} = {fmt_dp(d, 1)} cm",
              "Rearrange Rf = distance moved by substance ÷ distance moved by solvent",
              [_m(s * rf, "cm", "Divide the spot distance by the Rf value — don't multiply", dp=1)])


_DYES = ("Red dye", "Yellow dye", "Blue dye", "Green dye", "Orange dye", "Purple dye")


def _rf_5(rng):
    def make(r):
        refs = sorted(r.sample(range(10, 91, 5), 4))
        if min(b - a for a, b in zip(refs, refs[1:])) < 10:
            return None
        k = r.randrange(4)
        target = Fraction(refs[k], 100)
        d = F(r.choice(("6.0", "8.0", "10.0", "12.0", "5.0", "7.5")))
        s = target * d
        if s * 10 != int(s * 10):
            return None
        return refs, k, d, s
    refs, k, d, s = retry(make, rng)
    names = rng.sample(_DYES, 4)
    table = "; ".join(f"{nm} {fmt_dp(Fraction(v, 100), 2)}" for nm, v in zip(names, refs))
    stem = (f"Rf values of four dyes in the same solvent: {table}. On a chromatogram of an unknown dye, the spot moved "
            f"{fmt_dp(s, 1)} cm and the solvent front moved {fmt_dp(d, 1)} cm from the start line. Which dye is the "
            f"unknown dye?")
    rf = fmt_dp(Fraction(refs[k], 100), 2)
    feedback = [None if i == k else f"That dye's Rf is {fmt_dp(Fraction(v, 100), 2)}, but the unknown's Rf is {fmt_dp(s, 1)} ÷ {fmt_dp(d, 1)} = {rf}"
                for i, v in enumerate(refs)]
    text, answer, mistakes = build_choice(stem, names, k, rng.randrange(2 ** 31), feedback)
    d = _q(text, answer, f"Rf = {fmt_dp(s, 1)} ÷ {fmt_dp(d, 1)} = {rf}, which matches the {names[k].lower()}",
           "Calculate the Rf value of the unknown spot first, then compare it with the table", mistakes)
    # one ref per underlying question, whatever order the options are shown in
    d["ref"] = f"{SUBJECT_ID}.rf_values#L5-" + hashlib.sha1(stem.encode("utf-8")).hexdigest()[:12]
    return d


# =========================================================== bond energies

BONDS: dict[str, int] = {
    "H–H": 436, "Cl–Cl": 243, "H–Cl": 432, "Br–Br": 193, "H–Br": 366, "I–I": 151, "H–I": 299, "F–F": 158,
    "H–F": 568, "O=O": 498, "O–H": 464, "C–H": 413, "C=O": 805, "C–C": 347, "C=C": 612, "N≡N": 945,
    "N–H": 391, "C–Cl": 346, "C–Br": 276,
}

# (equation, bonds broken, bonds made, description of the bonds in each molecule)
_BE_SIMPLE = (
    ("H2 + Cl2 → 2HCl", {"H–H": 1, "Cl–Cl": 1}, {"H–Cl": 2}),
    ("H2 + Br2 → 2HBr", {"H–H": 1, "Br–Br": 1}, {"H–Br": 2}),
    ("H2 + I2 → 2HI", {"H–H": 1, "I–I": 1}, {"H–I": 2}),
    ("H2 + F2 → 2HF", {"H–H": 1, "F–F": 1}, {"H–F": 2}),
    ("2HI → H2 + I2", {"H–I": 2}, {"H–H": 1, "I–I": 1}),
    ("2HBr → H2 + Br2", {"H–Br": 2}, {"H–H": 1, "Br–Br": 1}),
    ("2HCl → H2 + Cl2", {"H–Cl": 2}, {"H–H": 1, "Cl–Cl": 1}),
    ("2HF → H2 + F2", {"H–F": 2}, {"H–H": 1, "F–F": 1}),
)
_BE_MULTI = (
    ("2H2 + O2 → 2H2O", {"H–H": 2, "O=O": 1}, {"O–H": 4},
     "Each H₂ has one H–H bond, O₂ has one O=O bond and each H₂O has two O–H bonds."),
    ("CH4 + 2O2 → CO2 + 2H2O", {"C–H": 4, "O=O": 2}, {"C=O": 2, "O–H": 4},
     "CH₄ has four C–H bonds, each O₂ has one O=O bond, CO₂ has two C=O bonds and each H₂O has two O–H bonds."),
    ("N2 + 3H2 → 2NH3", {"N≡N": 1, "H–H": 3}, {"N–H": 6},
     "N₂ has one N≡N bond, each H₂ has one H–H bond and each NH₃ has three N–H bonds."),
    ("2NH3 → N2 + 3H2", {"N–H": 6}, {"N≡N": 1, "H–H": 3},
     "Each NH₃ has three N–H bonds, N₂ has one N≡N bond and each H₂ has one H–H bond."),
    ("2H2O → 2H2 + O2", {"O–H": 4}, {"H–H": 2, "O=O": 1},
     "Each H₂O has two O–H bonds, each H₂ has one H–H bond and O₂ has one O=O bond."),
    ("C2H4 + H2 → C2H6", {"C=C": 1, "C–H": 4, "H–H": 1}, {"C–C": 1, "C–H": 6},
     "C₂H₄ has one C=C bond and four C–H bonds, H₂ has one H–H bond, and C₂H₆ has one C–C bond and six C–H bonds."),
    ("CH4 + Cl2 → CH3Cl + HCl", {"C–H": 4, "Cl–Cl": 1}, {"C–H": 3, "C–Cl": 1, "H–Cl": 1},
     "CH₄ has four C–H bonds, Cl₂ has one Cl–Cl bond, CH₃Cl has three C–H bonds and one C–Cl bond, and HCl has one H–Cl bond."),
    ("C2H4 + Br2 → C2H4Br2", {"C=C": 1, "C–H": 4, "Br–Br": 1}, {"C–C": 1, "C–H": 4, "C–Br": 2},
     "C₂H₄ has one C=C bond and four C–H bonds, Br₂ has one Br–Br bond, and C₂H₄Br₂ has one C–C bond, four C–H bonds and two C–Br bonds."),
)


def _total(bonds: dict[str, int]) -> int:
    return sum(BONDS[b] * k for b, k in bonds.items())


def _bond_list(*groups: dict[str, int]) -> str:
    names: list[str] = []
    for g in groups:
        for b in g:
            if b not in names:
                names.append(b)
    return "Bond energies in kJ/mol: " + ", ".join(f"{b} = {BONDS[b]}" for b in names) + "."


def _sum_txt(bonds: dict[str, int]) -> str:
    if len(bonds) == 1:
        (b, k), = bonds.items()
        return f"{k} × {BONDS[b]}" if k > 1 else str(BONDS[b])
    return " + ".join(f"({k} × {BONDS[b]})" if k > 1 else str(BONDS[b]) for b, k in bonds.items())


def _signed(v: int) -> str:
    """Text form with a real minus sign: '+185', '−103'."""
    return f"+{v}" if v > 0 else f"−{-v}" if v < 0 else "0"


def _signed_display(v: int) -> str:
    return f"+{v}" if v > 0 else str(v)


SIGN_TXT = "Give the sign: + for endothermic, − for exothermic."


def _be_pick(rng) -> tuple[str, dict, dict, str]:
    """A simple diatomic reaction, or a larger one whose bonds are described in the question."""
    if rng.random() < 0.5:
        eq, broken, made = rng.choice(_BE_SIMPLE)
        return eq, broken, made, ""
    return rng.choice(_BE_MULTI)


def _be_1(rng):
    eq, broken, made, note = _be_pick(rng)
    note = f" {note}" if note else ""
    v = _total(broken)
    return _q(f"{chem(eq)}.{note} Calculate the total energy needed to break all the bonds in the reactants, in kJ/mol. "
              f"{_bond_list(broken, made)}",
              _exact(v, "kJ/mol"), f"Energy to break bonds = {_sum_txt(broken)} = {v} kJ/mol",
              "List every bond in the reactant molecules, then add up their bond energies",
              [_m(_total(made), "kJ/mol", "Those are the bonds in the products — use the bonds in the reactants", sf=None),
               _m(sum(BONDS[b] for b in broken), "kJ/mol",
                  "Count how many of each bond there are — use the balancing numbers", sf=None)])


def _be_2(rng):
    eq, broken, made, note = _be_pick(rng)
    note = f" {note}" if note else ""
    v = _total(made)
    return _q(f"{chem(eq)}.{note} Calculate the total energy released when the bonds in the products are made, in kJ/mol. "
              f"{_bond_list(broken, made)}",
              _exact(v, "kJ/mol"), f"Energy released making bonds = {_sum_txt(made)} = {v} kJ/mol",
              "List every bond in the product molecules, then add up their bond energies",
              [_m(_total(broken), "kJ/mol", "Those are the bonds in the reactants — use the bonds in the products", sf=None),
               _m(sum(BONDS[b] for b in made), "kJ/mol",
                  "Count how many of each bond there are — use the balancing numbers", sf=None)])


def _dh_draft(eq: str, broken: dict, made: dict, note: str = "") -> Draft:
    b, m = _total(broken), _total(made)
    v = b - m
    note = f" {note}" if note else ""
    text = (f"{chem(eq)}.{note} Calculate the overall energy change for this reaction in kJ/mol. "
            f"{_bond_list(broken, made)} {SIGN_TXT}")
    sol = (f"Bonds broken = {_sum_txt(broken)} = {b} kJ/mol. Bonds made = {_sum_txt(made)} = {m} kJ/mol. "
           f"Energy change = {b} − {m} = {_signed(v)} kJ/mol")
    once_b = sum(BONDS[x] for x in broken)
    once_m = sum(BONDS[x] for x in made)
    return _q(text, num_answer(v, f"{_signed_display(v)} kJ/mol"), sol,
              "Energy change = energy needed to break bonds − energy released making bonds",
              [_m(-v, "kJ/mol", "Energy change = bonds broken − bonds made: check the sign", sf=None),
               _m(b + m, "kJ/mol", "Subtract the energy released making bonds from the energy needed to break bonds", sf=None),
               _m(once_b - once_m if once_b - once_m not in (v, -v) else None, "kJ/mol",
                  "Count how many of each bond there are — use the balancing numbers", sf=None)])


def _be_3(rng):
    eq, broken, made = rng.choice(_BE_SIMPLE)
    return _dh_draft(eq, broken, made)


def _be_4(rng):
    eq, broken, made, note = rng.choice(_BE_MULTI)
    return _dh_draft(eq, broken, made, note)


def _be_5(rng):
    pool = tuple((e, b, m, "") for e, b, m in _BE_SIMPLE) + _BE_MULTI

    def make(r):
        eq, broken, made, note = r.choice(pool)
        both = set(broken) & set(made)
        cands = [("broken", x) for x in broken if x not in both] + [("made", x) for x in made if x not in both]
        side, x = r.choice(cands)
        return eq, broken, made, note, side, x
    eq, broken, made, note, side, x = retry(make, rng)
    dh = _total(broken) - _total(made)
    k = broken[x] if side == "broken" else made[x]
    known = {b: v for b, v in BONDS.items() if b != x}
    names = []
    for g in (broken, made):
        for b in g:
            if b != x and b not in names:
                names.append(b)
    data = ", ".join(f"{b} = {known[b]}" for b in names)
    note = f" {note}" if note else ""
    text = (f"{chem(eq)}.{note} The overall energy change for this reaction is {_signed(dh)} kJ/mol. "
            f"Bond energies in kJ/mol: {data}. Calculate the bond energy of the {x} bond in kJ/mol.")
    b_rest = sum(BONDS[b] * c for b, c in broken.items() if b != x)
    m_rest = sum(BONDS[b] * c for b, c in made.items() if b != x)
    if side == "broken":
        # dh = b_rest + k·X − m_total  →  X = (dh + m_total − b_rest) / k
        m_total = _total(made)
        top = dh + m_total - b_rest
        sol = (f"Energy change = bonds broken − bonds made, so {_signed(dh)} = ({b_rest} + {k}X) − {m_total}" if k > 1
               else f"Energy change = bonds broken − bonds made, so {_signed(dh)} = ({b_rest} + X) − {m_total}") if b_rest else (
            f"Energy change = bonds broken − bonds made, so {_signed(dh)} = {k}X − {m_total}" if k > 1
            else f"Energy change = bonds broken − bonds made, so {_signed(dh)} = X − {m_total}")
        wrong_sign = Fraction(-dh + m_total - b_rest, k)
    else:
        # dh = b_total − (m_rest + k·X)  →  X = (b_total − m_rest − dh) / k
        b_total = _total(broken)
        top = b_total - m_rest - dh
        sol = (f"Energy change = bonds broken − bonds made, so {_signed(dh)} = {b_total} − ({m_rest} + {k}X)" if k > 1
               else f"Energy change = bonds broken − bonds made, so {_signed(dh)} = {b_total} − ({m_rest} + X)") if m_rest else (
            f"Energy change = bonds broken − bonds made, so {_signed(dh)} = {b_total} − {k}X" if k > 1
            else f"Energy change = bonds broken − bonds made, so {_signed(dh)} = {b_total} − X")
        wrong_sign = Fraction(b_total - m_rest + dh, k)
    v = Fraction(top, k)
    if v != BONDS[x]:
        raise ValueError("bond energy algebra failed")
    sol += f". {k}X = {top}, so X = {n(v)} kJ/mol" if k > 1 else f". X = {n(v)} kJ/mol"
    return _q(text, _exact(v, "kJ/mol"), sol,
              "Write energy change = bonds broken − bonds made, with the unknown bond as X, then solve for X",
              [_m(top if k > 1 else None, "kJ/mol", f"There are {k} {x} bonds — divide by {k} to get one bond", sf=None),
               _m(wrong_sign if wrong_sign > 0 else None, "kJ/mol",
                  "Check the sign of the energy change when you rearrange", sf=None)])


# ============================================================ registration

def _skill(name: str, title: str, aliases: tuple[str, ...], levels: tuple, fallback: str) -> Skill:
    sid = f"{SUBJECT_ID}.{name}"
    if len(levels) != 5:
        raise ValueError(f"{sid}: needs 5 levels")

    def generate(level: int, seed: int) -> Problem:
        check_level(level)
        rng = random.Random(seed)
        d = dict(levels[level - 1](rng))
        ref = d.pop("ref", "")
        p = build(sid, level, seed, fallback_hint=fallback, **d)
        return replace(p, ref=ref) if ref else p

    generate.__name__ = f"generate_{name}"
    generate.__qualname__ = generate.__name__
    return Skill(id=sid, subject=SUBJECT_ID, title=title, aliases=aliases, generate=generate)


GEN_SKILLS: tuple[Skill, ...] = (
    _skill("mr", "Relative formula mass",
           ("relative formula mass", "mr", "relative atomic mass", "percentage by mass", "formula mass",
            "isotope abundance", "water of crystallisation"),
           (_mr_1, _mr_2, _mr_3, _pct_1, _ar_5), "Add up the relative atomic masses of all the atoms in the formula"),
    _skill("moles", "Moles",
           ("moles calculation", "moles", "mole", "reacting masses", "avogadro", "avogadro constant", "number of moles"),
           (_mol_1, _mol_2, _mol_3, _mol_4, _mol_5), "Use moles = mass ÷ Mr"),
    _skill("concentration", "Concentration & gas volumes",
           ("concentration", "g/dm3", "mol/dm3", "titration", "molar gas volume", "titration calculation",
            "gas volume"),
           (_conc_1, _conc_2, _conc_3, _conc_4, _conc_5), "Convert volumes into dm³ (÷ 1000) before you use them"),
    _skill("yield_economy", "Percentage yield & atom economy",
           ("percentage yield", "atom economy", "theoretical yield", "yield"),
           (_yield_1, _ae_2, _yield_3, _yield_4, _ae_5), "Percentage yield = actual ÷ theoretical × 100"),
    _skill("rates", "Rates of reaction",
           ("mean rate of reaction", "rate of reaction", "rate calculation", "mean rate", "rates calculation"),
           (_rate_1, _rate_2, _rate_3, _rate_4, _rate_5), "Mean rate = amount of product formed ÷ time taken"),
    _skill("rf_values", "Chromatography Rf values",
           ("rf value", "chromatography calculation", "rf values", "retention factor", "rf"),
           (_rf_1, _rf_2, _rf_3, _rf_4, _rf_5), "Rf = distance moved by the substance ÷ distance moved by the solvent"),
    _skill("bond_energy", "Bond energies",
           ("bond energies", "bond energy", "energy change calculation", "bond enthalpy", "bonds broken bonds made"),
           (_be_1, _be_2, _be_3, _be_4, _be_5), "Energy change = bonds broken − bonds made"),
)

_ROWS = (
    (("atoms_bonding", "Atoms, bonding & structure", ("atoms_bonding", "mr")),
     ("quantitative", "Quantitative chemistry", ("moles", "concentration", "yield_economy"))),
    (("reactions", "Reactions, rates & energy", ("reactions", "rates")),
     ("organic_earth", "Organic, analysis & Earth", ("organic_earth", "rf_values"))),
)
_ORDER = ("atoms_bonding", "mr", "moles", "concentration", "yield_economy", "reactions", "rates", "organic_earth",
          "rf_values", "bond_energy")


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"{SUBJECT_ID}.y{y}.{slug}", label=label,
                    skills=tuple(f"{SUBJECT_ID}.{s}" for s in skills), level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Chemistry", order=18, years={10: _year(10), 11: _year(11)})


def skills() -> list[Skill]:
    """Generator skills plus the bank skills from packs/chemistry.json, in topic order."""
    by_id = {s.id: s for s in GEN_SKILLS}
    for s in load_pack(SUBJECT_ID, SUBJECT_ID):
        if s.id in by_id:
            raise ValueError(f"{s.id} is defined twice")
        by_id[s.id] = s
    wanted = [f"{SUBJECT_ID}.{x}" for x in _ORDER]
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise ValueError(f"chemistry: missing skills {missing}")
    return [by_id[w] for w in wanted] + [s for k, s in by_id.items() if k not in wanted]


def register(reg) -> None:
    """Register Chemistry (Years 10–11) with a tutor.content Registry."""
    reg.register(make_subject(), skills())
