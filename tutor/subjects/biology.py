"""Biology (GCSE, Years 10–11): generator skills here, bank skills in packs/biology.json.

docs/ARCHITECTURE_V2.md section 5.1. Generators build each problem backwards from a nice
answer with Fractions; a value close to a rounding boundary is never used, and every rounding
instruction and unit is stated in the question. Cell sizes stay within realistic ranges.
"""
from __future__ import annotations

import random
from fractions import Fraction

from ..content import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, load_pack
from ..content.fmt import (
    build, check_level, dec, fmt_dp, fmt_num, fmt_sf, fmt_std, num_answer, num_mistake, retry,
    sig_digits, std_answer, std_mistake, unit,
)

SUBJECT_ID = "biology"
Draft = dict


# ================================================================ helpers

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


def _exact(v, u: str = "") -> Answer:
    return num_answer(v, unit(n(v), u))


def _m(v, u: str, fb: str, sf: int | None = None, dp: int | None = None) -> Mistake | None:
    if v is None:
        return None
    try:
        if float(v) == 0:
            return None
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return None
    if dp is not None:
        return num_mistake(v, u, fb, dp=dp)
    if sf is not None:
        return num_mistake(v, u, fb, sf=sf)
    return num_mistake(v, u, fb)


def _short(v) -> bool:
    """Exact and short enough to show without rounding."""
    f = Fraction(v)
    d = f.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1 and sig_digits(f) <= 4


def _mk(v, u: str, fb: str) -> Mistake | None:
    """A typical wrong value: exact if short, otherwise matched to 2 s.f."""
    if v is None:
        return None
    return _m(v, u, fb) if _short(v) else _m(v, u, fb, sf=2)


DP_TXT = "Give your answer to 1 decimal place."
SF_TXT = "Give your answer to 3 significant figures."
NUMBER_ONLY = "Write the magnification as a number only."

# ========================================================== magnification

# (name, smallest, largest actual length in micrometres)
_OBJECTS = (
    ("red blood cell", 6, 8), ("bacterial cell", 1, 5), ("yeast cell", 3, 8), ("chloroplast", 3, 8),
    ("nucleus", 5, 10), ("animal cell", 10, 30), ("cheek cell", 50, 80), ("plant cell", 20, 100),
    ("palisade cell", 30, 80), ("pollen grain", 20, 80), ("onion cell", 150, 400), ("mitochondrion", 1, 4),
    ("guard cell", 20, 50),
)
_MAGS = (20, 40, 50, 80, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1200, 1500, 2000, 2500, 3000,
         4000, 5000, 6000, 8000, 10000)
_UM_STEPS = (Fraction(1, 2), Fraction(1), Fraction(2), Fraction(5), Fraction(10), Fraction(20), Fraction(25),
             Fraction(50))


def _size(r):
    """(object name, actual length in µm, magnification, image length in mm), all exact and realistic."""
    name, lo, hi = r.choice(_OBJECTS)
    step = r.choice(_UM_STEPS)
    k_lo, k_hi = -(-lo // step), hi // step
    if k_lo > k_hi:
        return None
    a_um = step * r.randrange(int(k_lo), int(k_hi) + 1)
    if a_um <= 0:
        return None
    mag = r.choice(_MAGS)
    i_mm = a_um * mag / 1000
    if not (10 <= i_mm <= 160) or (i_mm * 10).denominator != 1:
        return None
    return name, a_um, mag, i_mm


def _mag_1(rng):
    name, a_um, mag, i_mm = retry(_size, rng)
    a_mm = a_um / 1000
    return _q(f"An image of a {name} is {n(i_mm)} mm long. The actual length of the {name} is {n(a_mm)} mm. "
              f"Calculate the magnification of the image. {NUMBER_ONLY}",
              _exact(mag), f"magnification = image size ÷ actual size = {n(i_mm)} ÷ {n(a_mm)} = {mag}",
              "magnification = size of image ÷ size of real object",
              [_mk(a_mm / i_mm, "", "magnification = image size ÷ actual size — you divided the wrong way round"),
               _mk(a_mm * i_mm, "", "Divide the image size by the actual size — don't multiply")])


def _mag_2(rng):
    name, a_um, mag, i_mm = retry(_size, rng)
    a_mm = a_um / 1000
    if rng.random() < 0.6:
        return _q(f"An image of a {name} is {n(i_mm)} mm long. The magnification is ×{mag}. Calculate the actual "
                  f"length of the {name} in mm.",
                  _exact(a_mm, "mm"), f"actual size = image size ÷ magnification = {n(i_mm)} ÷ {mag} = {n(a_mm)} mm",
                  "Rearrange magnification = image size ÷ actual size to make actual size the subject",
                  [_mk(i_mm * mag, "mm", "actual size = image size ÷ magnification — divide, don't multiply"),
                   _mk(Fraction(mag) / i_mm, "mm", "actual size = image size ÷ magnification — you divided the wrong way round")])
    return _q(f"A {name} is {n(a_mm)} mm long. It is viewed at a magnification of ×{mag}. Calculate the length of "
              f"its image in mm.",
              _exact(i_mm, "mm"), f"image size = magnification × actual size = {mag} × {n(a_mm)} = {n(i_mm)} mm",
              "Rearrange magnification = image size ÷ actual size to make image size the subject",
              [_mk(a_mm / mag, "mm", "image size = magnification × actual size — multiply, don't divide"),
               _mk(Fraction(mag) / a_mm, "mm", "image size = magnification × actual size — multiply, don't divide")])


def _mag_3(rng):
    name, a_um, mag, i_mm = retry(_size, rng)
    a_mm = a_um / 1000
    if rng.random() < 0.5:
        return _q(f"A {name} is {n(a_mm)} mm long. What is its length in micrometres (µm)? (1 mm = 1000 µm)",
                  _exact(a_um, "µm"), f"{n(a_mm)} mm × 1000 = {n(a_um)} µm",
                  "There are 1000 µm in 1 mm, so the number of µm is bigger than the number of mm",
                  [_mk(a_mm / 1000, "µm", "Multiply by 1000 to change mm into µm — the number should get bigger"),
                   _mk(a_mm * 100, "µm", "1 mm = 1000 µm, so multiply by 1000, not 100")])
    return _q(f"A {name} is {n(a_um)} µm long. What is its length in millimetres (mm)? (1 mm = 1000 µm)",
              _exact(a_mm, "mm"), f"{n(a_um)} µm ÷ 1000 = {n(a_mm)} mm",
              "There are 1000 µm in 1 mm, so the number of mm is smaller than the number of µm",
              [_mk(a_um * 1000, "mm", "Divide by 1000 to change µm into mm — the number should get smaller"),
               _mk(a_um / 100, "mm", "1 mm = 1000 µm, so divide by 1000, not 100")])


def _mag_4(rng):
    name, a_um, mag, i_mm = retry(_size, rng)
    i_um = i_mm * 1000
    if rng.random() < 0.5:
        return _q(f"An image of a {name} is {n(i_mm)} mm long. The actual length of the {name} is {n(a_um)} µm. "
                  f"Calculate the magnification. (1 mm = 1000 µm) {NUMBER_ONLY}",
                  _exact(mag), f"{n(i_mm)} mm = {n(i_um)} µm. magnification = {n(i_um)} ÷ {n(a_um)} = {mag}",
                  "Put both lengths into the same unit first",
                  [_mk(i_mm / a_um, "", f"Convert {n(i_mm)} mm into µm first (× 1000) so both lengths use the same unit"),
                   _mk(a_um / i_um, "", "magnification = image size ÷ actual size — you divided the wrong way round")])
    return _q(f"An image of a {name} is {n(i_mm)} mm long. The magnification is ×{mag}. Calculate the actual length "
              f"of the {name} in µm. (1 mm = 1000 µm)",
              _exact(a_um, "µm"), f"actual size = {n(i_mm)} ÷ {mag} = {n(i_mm / mag)} mm = {n(a_um)} µm",
              "Find the actual size in mm first, then convert it into µm",
              [_mk(i_mm / mag, "µm", "That's the size in mm — multiply by 1000 to give µm"),
               _mk(i_mm * mag, "µm", "actual size = image size ÷ magnification — divide, don't multiply")])


# (name, smallest, largest actual length as (mantissa × 10, exponent)) — realistic sizes in metres
_EM_RANGES = {"virus": (Fraction(2, 10 ** 8), Fraction(3, 10 ** 7)), "ribosome": (Fraction(2, 10 ** 8), Fraction(3, 10 ** 8)),
              "bacterial cell": (Fraction(1, 10 ** 6), Fraction(5, 10 ** 6)),
              "mitochondrion": (Fraction(1, 10 ** 6), Fraction(3, 10 ** 6))}


def _mag_5(rng):
    if rng.random() < 0.5:
        def make(r):
            name = r.choice(tuple(_EM_RANGES))
            lo, hi = _EM_RANGES[name]
            e = r.choice(sorted({dec(lo).adjusted(), dec(hi).adjusted()}))
            mant = F(r.randrange(10, 100)) / 10
            a_m = mant * Fraction(10) ** e
            if not (lo <= a_m <= hi):
                return None
            i_mm = r.randrange(15, 121)
            mag = Fraction(i_mm, 1000) / a_m
            if not _rounding_ok(mag, sf=3) or sig_digits(mag) <= 2:
                return None
            return name, mant, e, a_m, i_mm, mag
        name, mant, e, a_m, i_mm, mag = retry(make, rng)
        ans = std_answer(mag, "", round_to_sf=3)
        return _q(f"In an electron micrograph, the image of a {name} is {i_mm} mm long. The actual length of the "
                  f"{name} is {n(mant)} × 10^{e} m. Calculate the magnification. Give your answer in standard form to "
                  f"3 significant figures.",
                  ans, f"{i_mm} mm = {n(Fraction(i_mm, 1000))} m. magnification = {n(Fraction(i_mm, 1000))} ÷ "
                       f"({n(mant)} × 10^{e}) = {ans.display}",
                  "Convert the image size into metres first, then divide by the actual size",
                  [std_mistake(Fraction(i_mm) / a_m, "", f"Convert {i_mm} mm into metres first: ÷ 1000", round_to_sf=3),
                   std_mistake(a_m / Fraction(i_mm, 1000), "", "magnification = image size ÷ actual size — you divided the wrong way round",
                               round_to_sf=3)])

    def make(r):
        name = r.choice(tuple(_EM_RANGES))
        i_mm = r.randrange(15, 121)
        mag = r.choice((12000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 80000, 100000, 120000, 150000,
                        200000, 250000, 300000, 400000, 500000))
        a_m = Fraction(i_mm, 1000) / mag
        lo, hi = _EM_RANGES[name]
        if not (lo <= a_m <= hi) or not _rounding_ok(a_m, sf=3):
            return None
        return name, i_mm, mag, a_m
    name, i_mm, mag, a_m = retry(make, rng)
    ans = std_answer(a_m, "m", round_to_sf=3)
    return _q(f"In an electron micrograph, the image of a {name} is {i_mm} mm long. The magnification is ×{mag:,}. "
              f"Calculate the actual length of the {name} in metres. Give your answer in standard form to 3 "
              f"significant figures.",
              ans, f"actual size = {i_mm} ÷ {mag:,} = {fmt_std(Fraction(i_mm) / mag, 3)} mm = {ans.display}",
              "Find the actual size in mm, then convert it into metres (÷ 1000)",
              [std_mistake(Fraction(i_mm) / mag, "m", "That's the size in mm — divide by 1000 to give metres", round_to_sf=3),
               std_mistake(Fraction(i_mm, 1000) * mag, "m", "actual size = image size ÷ magnification — divide, don't multiply",
                           round_to_sf=3)])


# ============================================================ biology maths

def _pct_change(rng, decrease: bool):
    def make(r):
        if r.random() < 0.7:
            start = F(r.randrange(120, 400)) / 100            # g, 2 d.p.
            ctx = "mass"
        else:
            start = F(r.randrange(80, 300)) / 10              # cm, 1 d.p.
            ctx = "length"
        pct = F(r.randrange(2, 30))
        step = Fraction(1, 100) if ctx == "mass" else Fraction(1, 10)
        delta = round(start * pct / 100 / step) * step
        end = start - delta if decrease else start + delta
        if delta == 0 or end <= 0:
            return None
        v = (end - start) / start * 100
        if not _rounding_ok(v, dp=1):
            return None
        return ctx, start, end, v
    ctx, start, end, v = retry(make, rng)
    if ctx == "mass":
        sol_name = "potato cylinder"
        place = rng.choice(("a concentrated sugar solution", "a strong salt solution")) if decrease else \
            rng.choice(("distilled water", "a very dilute sugar solution"))
        text = (f"A potato cylinder had a mass of {fmt_dp(start, 2)} g. After 30 minutes in {place} its mass was "
                f"{fmt_dp(end, 2)} g. Calculate the percentage change in mass.")
        u_start, u_end = fmt_dp(start, 2), fmt_dp(end, 2)
    else:
        sol_name = "tissue"
        text = (f"A strip of plant tissue was {fmt_dp(start, 1)} cm long. After soaking in "
                f"{'a concentrated salt solution' if decrease else 'distilled water'} it was {fmt_dp(end, 1)} cm long. "
                f"Calculate the percentage change in length.")
        u_start, u_end = fmt_dp(start, 1), fmt_dp(end, 1)
    if decrease:
        text += " Use a minus sign for a decrease."
    text += f" {DP_TXT}"
    change = end - start
    sol = (f"change = {u_end} − {u_start} = {n(change)}. percentage change = {n(change)} ÷ {u_start} × 100 = "
           f"{fmt_dp(v, 1)}%")
    mistakes = [_m(change / end * 100, "%", "Divide the change by the starting value, not the final value", dp=1),
                _m(change / start, "%", "Multiply by 100 to turn the fraction into a percentage", sf=2)]
    if decrease:
        mistakes.insert(0, _m(-v, "%", "The value went down, so the percentage change is negative — include the minus sign", dp=1))
    return _q(text, num_answer(v, unit(fmt_dp(v, 1), "%"), dp=1), sol,
              "percentage change = (final value − starting value) ÷ starting value × 100", mistakes)


def _dm_1(rng):
    return _pct_change(rng, decrease=False)


def _dm_2(rng):
    return _pct_change(rng, decrease=True)


_REPEATS = (
    ("time taken for the starch to be broken down", "s", 30, 200, 0),
    ("number of bubbles released in one minute", "", 12, 60, 0),
    ("volume of oxygen collected in 5 minutes", "cm³", 4, 30, 1),
    ("reaction time in a ruler-drop test", "s", F("0.15"), F("0.40"), 2),
    ("height of the seedling after 10 days", "mm", 20, 90, 0),
)


def _dm_3(rng):
    def make(r):
        what, u, lo, hi, places = r.choice(_REPEATS)
        step = Fraction(1, 10 ** places)
        centre = F(lo) + (F(hi) - F(lo)) * F(r.randrange(0, 101)) / 100
        centre = round(centre / step) * step
        spread = max(step, round(centre * F("0.06") / step) * step)
        k = r.choice((4, 4, 5))
        vals = [centre + spread * r.randrange(-1, 2) for _ in range(k - 1)]
        if len(set(vals)) < 2 or min(vals) <= 0:
            return None
        far = F(r.choice(("1.5", "1.6", "1.8", "2", "0.5", "0.55", "0.6")))
        anomaly = round(centre * far / step) * step
        if anomaly <= 0 or abs(anomaly - centre) < 4 * spread:
            return None
        pos = r.randrange(k)
        allv = vals[:pos] + [anomaly] + vals[pos:]
        mean = sum(vals, Fraction(0)) / len(vals)
        if not _rounding_ok(mean, dp=min(places + 1, 2)):
            return None
        return what, u, places, allv, anomaly, vals, mean
    what, u, places, allv, anomaly, vals, mean = retry(make, rng)
    dp = min(places + 1, 2)
    rtxt = DP_TXT if dp == 1 else "Give your answer to 2 decimal places."
    fmt = (lambda x: fmt_dp(x, places)) if places else (lambda x: n(x))
    shown = ", ".join(unit(fmt(x), u) for x in allv)
    everything = sum(allv, Fraction(0)) / len(allv)
    return _q(f"A student repeated a measurement of the {what}. The results were: {shown}. One result is anomalous. "
              f"Ignore it and calculate the mean of the other results. {rtxt}",
              num_answer(mean, unit(fmt_dp(mean, dp), u), dp=dp),
              f"The anomalous result is {unit(fmt(anomaly), u)}. mean = ({' + '.join(fmt(x) for x in vals)}) ÷ "
              f"{len(vals)} = {unit(fmt_dp(mean, dp), u)}",
              "Find the result that is very different from the others, leave it out, then add up the rest and divide by how many there are",
              [_m(everything, u, f"Leave out the anomalous result ({unit(fmt(anomaly), u)}) before you work out the mean", dp=dp),
               _m(sum(vals, Fraction(0)) / len(allv), u, f"Divide by {len(vals)} — the number of results you added up", dp=dp)])


def _dm_4(rng):
    kind = rng.choice(("oxygen", "oxygen", "enzyme"))
    if kind == "oxygen":
        def make(r):
            vol = F(r.randrange(12, 120)) / 10
            mins = r.choice((3, 4, 5, 6, 7, 8, 9, 10, 12, 15))
            v = vol / mins
            return None if sig_digits(v) <= 3 or not _rounding_ok(v, sf=3) else (vol, mins, v)
        vol, mins, v = retry(make, rng)
        return _q(f"A piece of pondweed released {n(vol)} cm³ of oxygen in {mins} minutes. Calculate the rate of "
                  f"photosynthesis in cm³ of oxygen per minute. {SF_TXT}",
                  num_answer(v, fmt_sf(v, 3) + " cm³/min", sf=3), f"rate = volume ÷ time = {n(vol)} ÷ {mins} = {fmt_sf(v, 3)} cm³/min",
                  "rate = amount of oxygen produced ÷ time taken",
                  [_m(Fraction(mins) / vol, "cm³/min", "Divide the volume by the time, not the time by the volume", sf=3),
                   _m(v / 60, "cm³/min", "That's the rate per second — the question asks for cm³ per minute", sf=3)])

    def make(r):
        t = r.randrange(35, 400)
        v = Fraction(1000, t)
        return None if sig_digits(v) <= 3 or not _rounding_ok(v, sf=3) else (t, v)
    t, v = retry(make, rng)
    return _q(f"In an enzyme experiment, the starch was broken down in {t} s. The rate of reaction is calculated as "
              f"rate = 1000 ÷ time. Calculate the rate. {SF_TXT}",
              num_answer(v, fmt_sf(v, 3), sf=3), f"rate = 1000 ÷ {t} = {fmt_sf(v, 3)}",
              "Put the time into rate = 1000 ÷ time",
              [_m(Fraction(t, 1000), "", "rate = 1000 ÷ time — you divided the wrong way round", sf=3),
               _m(Fraction(1, t), "", "Use the formula given: 1000 ÷ time", sf=3)])


def _dm_5(rng):
    if rng.random() < 0.5:
        def make(r):
            dcm = r.choice((10, 12, 15, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80))
            dm = Fraction(dcm, 100)
            v = 1 / (dm * dm)
            return None if not _rounding_ok(v, sf=3) else (dcm, dm, v)
        dcm, dm, v = retry(make, rng)
        return _q(f"A lamp is placed {dcm} cm from some pondweed. Calculate the relative light intensity using "
                  f"relative light intensity = 1 ÷ d², where d is the distance in metres. {SF_TXT}",
                  num_answer(v, fmt_sf(v, 3), sf=3),
                  f"d = {dcm} cm = {n(dm)} m. d² = {n(dm * dm)}. 1 ÷ {n(dm * dm)} = {fmt_sf(v, 3)}",
                  "Convert the distance into metres, square it, then divide 1 by the answer",
                  [_m(Fraction(1, dcm * dcm), "", "Convert the distance into metres first: ÷ 100", sf=3),
                   _m(1 / dm, "", "Square the distance before dividing: 1 ÷ d²", sf=3),
                   _m(dm * dm, "", "Divide 1 by d² — don't just square the distance", sf=3)])

    def make(r):
        d1, d2 = sorted(r.sample((10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60), 2))
        v = Fraction(d2, d1) ** 2
        return None if not _rounding_ok(v, sf=3) else (d1, d2, v)
    d1, d2, v = retry(make, rng)
    return _q(f"Light intensity is proportional to 1 ÷ d², where d is the distance from the lamp. How many times "
              f"greater is the light intensity at {d1} cm from the lamp than at {d2} cm? {SF_TXT}",
              num_answer(v, fmt_sf(v, 3), sf=3),
              f"intensity ratio = (1 ÷ {d1}²) ÷ (1 ÷ {d2}²) = ({d2} ÷ {d1})² = {fmt_sf(v, 3)}",
              "Work out 1 ÷ d² at each distance, then divide the bigger value by the smaller one",
              [_m(Fraction(d2, d1), "", "Light intensity depends on 1 ÷ d², so square the ratio of the distances", sf=3),
               _m(Fraction(d1, d2) ** 2, "", "The closer lamp gives the brighter light — your answer should be more than 1", sf=3)])


# ============================================================ genetic crosses

# (letter, dominant allele gives, recessive allele gives, organism (plural), one organism, adjective phenotype?)
_TRAITS = (
    ("T", "tall plants", "dwarf plants", "pea plants", "plant", True),
    ("R", "round seeds", "wrinkled seeds", "pea plants", "plant", False),
    ("Y", "yellow seeds", "green seeds", "pea plants", "plant", False),
    ("P", "purple flowers", "white flowers", "pea plants", "plant", False),
    ("B", "black fur", "brown fur", "mice", "mouse", False),
    ("N", "normal wings", "vestigial wings", "fruit flies", "fly", False),
)


class _T:
    """One trait: alleles, phenotype phrases and organism words."""

    def __init__(self, row):
        self.A, self.dom, self.rec, self.org, self.one, self.adj = row
        self.a = self.A.lower()

    def intro(self) -> str:
        return f"In {self.org}, the allele for {self.dom} ({self.A}) is dominant over the allele for {self.rec} ({self.a})."

    def word(self, pheno: str) -> str:
        """'tall' for 'tall plants', else the phrase itself ('round seeds')."""
        return pheno.split()[0] if self.adj else pheno

    def is_(self, pheno: str) -> str:
        """'is tall' / 'has round seeds'."""
        return f"is {self.word(pheno)}" if self.adj else f"has {pheno}"

    def offspring(self, pheno: str) -> str:
        """'tall offspring' / 'offspring with round seeds'."""
        return f"{self.word(pheno)} offspring" if self.adj else f"offspring with {pheno}"

    def plant(self, g: str) -> str:
        """'a plant with genotype Rr' (avoids 'a Rr' / 'an Rr')."""
        return f"a {self.one} with genotype {g}"


def _trait(r) -> _T:
    return _T(r.choice(_TRAITS))


def _frac(v: Fraction) -> Answer:
    s = f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator)
    return Answer(kind="fraction", display=s, value=s)


def _fmistake(v: Fraction, fb: str) -> Mistake | None:
    if v <= 0:
        return None
    s = f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator)
    return Mistake(Answer(kind="fraction", display=s, value=s), fb)


def _pun_1(rng):
    t = _trait(rng)
    het, homo = t.A + t.a, t.a + t.a
    ask = rng.choice(("rec", "dom", "het", "homrec"))
    q = {"rec": t.is_(t.rec), "dom": t.is_(t.dom), "het": f"has the genotype {het}",
         "homrec": f"has the genotype {homo}"}[ask]
    first, second = (het, homo) if rng.random() < 0.5 else (homo, het)
    text = (f"{t.intro()} {t.plant(first)[0].upper() + t.plant(first)[1:]} is crossed with {t.plant(second)}. "
            f"What is the probability that an offspring {q}? Give your answer as a fraction.")
    sol = f"Punnett square {het} × {homo}: offspring are {het}, {het}, {homo}, {homo}. 2 out of 4 = 1/2"
    return _q(text, _frac(Fraction(1, 2)), sol,
              f"Draw a Punnett square: the gametes are {t.A} and {t.a} from one parent, {t.a} and {t.a} from the other",
              [_fmistake(Fraction(1, 4), f"In a {het} × {homo} cross, 2 of the 4 offspring boxes match — not 1"),
               _fmistake(Fraction(3, 4), f"That's the result for {het} × {het} — here one parent is {homo}")])


def _pun_2(rng):
    t = _trait(rng)
    het, homd, homr = t.A + t.a, t.A + t.A, t.a + t.a
    ask = rng.choice(("rec", "dom", "het", "homdom"))
    q, v = {"rec": (t.is_(t.rec), Fraction(1, 4)), "dom": (t.is_(t.dom), Fraction(3, 4)),
            "het": (f"has the genotype {het}", Fraction(1, 2)),
            "homdom": (f"has the genotype {homd}", Fraction(1, 4))}[ask]
    text = (f"{t.intro()} Two heterozygous {t.org} ({het} × {het}) are crossed. What is the probability that an "
            f"offspring {q}? Give your answer as a fraction.")
    sol = f"Punnett square {het} × {het}: offspring are {homd}, {het}, {het}, {homr}. "
    sol += {"rec": f"Only {homr} gives the recessive phenotype: 1/4",
            "dom": f"{homd}, {het} and {het} all show the dominant phenotype: 3/4",
            "het": f"2 of the 4 are {het}: 2/4 = 1/2",
            "homdom": f"1 of the 4 is {homd}: 1/4"}[ask]
    mistakes = {
        "rec": [_fmistake(Fraction(3, 4), "That's the probability of the dominant phenotype"),
                _fmistake(Fraction(1, 2), f"Only {homr} shows the recessive phenotype — that's 1 box out of 4")],
        "dom": [_fmistake(Fraction(1, 4), "That's the probability of the recessive phenotype"),
                _fmistake(Fraction(1, 2), f"{het} offspring show the dominant phenotype too — count {homd} and both {het} boxes")],
        "het": [_fmistake(Fraction(1, 4), f"Two of the four boxes are {het}"),
                _fmistake(Fraction(3, 4), f"Count only the {het} boxes — {homd} is not heterozygous")],
        "homdom": [_fmistake(Fraction(3, 4), f"Only one box is {homd} — {het} is heterozygous"),
                   _fmistake(Fraction(1, 2), f"Only one box is {homd} — the two {het} boxes are heterozygous")],
    }[ask]
    return _q(text, _frac(v), sol, f"Draw a Punnett square with gametes {t.A} and {t.a} from each parent", mistakes)


_CROSSES = {
    # cross: genotype counts out of 4
    "Aa x Aa": {"AA": 1, "Aa": 2, "aa": 1},
    "Aa x aa": {"Aa": 2, "aa": 2},
    "AA x aa": {"Aa": 4},
    "AA x Aa": {"AA": 2, "Aa": 2},
}


def _geno(code: str, A: str, a: str) -> str:
    return code.replace("A", "\0").replace("a", a).replace("\0", A)


def _pun_3(rng):
    def make(r):
        cross = r.choice(tuple(_CROSSES))
        counts = _CROSSES[cross]
        ask = r.choice(("dom", "rec", "het"))
        if ask == "dom":
            k = counts.get("AA", 0) + counts.get("Aa", 0)
        elif ask == "rec":
            k = counts.get("aa", 0)
        else:
            k = counts.get("Aa", 0)
        if k == 0 or k == 4:
            return None
        return cross, counts, ask, k
    cross, counts, ask, k = retry(make, rng)
    t = _trait(rng)
    p1, p2 = (_geno(x, t.A, t.a) for x in cross.split(" x "))
    q = {"dom": f"show the dominant phenotype ({t.word(t.dom)})",
         "rec": f"show the recessive phenotype ({t.word(t.rec)})",
         "het": f"have the genotype {t.A + t.a}"}[ask]
    text = (f"{t.intro()} {t.plant(p1)[0].upper() + t.plant(p1)[1:]} is crossed with {t.plant(p2)}. "
            f"What percentage of the offspring would you expect to {q}?")
    boxes = ", ".join(_geno(g, t.A, t.a) for g, c in counts.items() for _ in range(c))
    v = Fraction(k * 25)
    sol = f"Punnett square {p1} × {p2}: {boxes}. {k} out of 4 = {n(v)}%"
    other = 100 - v
    return _q(text, num_answer(v, f"{n(v)}%"), sol,
              "Draw a Punnett square, count the boxes that match, then turn the fraction out of 4 into a percentage",
              [_m(Fraction(k, 4), "%", "Give the answer as a percentage: multiply the fraction by 100"),
               _m(other if other != v else None, "%",
                  "That's the percentage of the other offspring — check which phenotype or genotype the question asks about")])


def _pun_4(rng):
    t = _trait(rng)
    het, homd, homr = t.A + t.a, t.A + t.A, t.a + t.a
    kind = rng.choice(("pheno_hh", "pheno_hh", "pheno_hr", "geno_hh"))
    dom_o, rec_o = t.offspring(t.dom), t.offspring(t.rec)
    if kind == "geno_hh":
        text = (f"{t.intro()} Two heterozygous {t.org} ({het} × {het}) are crossed. Give the expected ratio of "
                f"offspring genotypes {homd} : {het} : {homr} in its simplest form.")
        ans = Answer(kind="ratio", display="1:2:1", value=[1, 2, 1], form="simplest")
        sol = f"Punnett square: {homd}, {het}, {het}, {homr}. {homd} : {het} : {homr} = 1 : 2 : 1"
        mistakes = [Mistake(Answer(kind="ratio", display="3:1", value=[3, 1]),
                            f"That's the ratio of phenotypes — give the ratio of the three genotypes {homd} : {het} : {homr}"),
                    Mistake(Answer(kind="ratio", display="1:1:2", value=[1, 1, 2]),
                            f"Check the order: {homd} first, then {het}, then {homr}")]
        hint = f"Draw a Punnett square with gametes {t.A} and {t.a} from each parent and count each genotype"
    elif kind == "pheno_hh":
        text = (f"{t.intro()} Two heterozygous {t.org} ({het} × {het}) are crossed. Give the expected ratio of "
                f"{dom_o} to {rec_o} in its simplest form.")
        ans = Answer(kind="ratio", display="3:1", value=[3, 1], form="simplest")
        sol = f"Punnett square: {homd}, {het}, {het}, {homr}. 3 have the dominant phenotype and 1 the recessive: 3 : 1"
        mistakes = [Mistake(Answer(kind="ratio", display="1:3", value=[1, 3]),
                            f"Check the order: {dom_o} first, then {rec_o}"),
                    Mistake(Answer(kind="ratio", display="1:2:1", value=[1, 2, 1]),
                            "That's the ratio of genotypes — the question asks about phenotypes"),
                    Mistake(Answer(kind="ratio", display="1:1", value=[1, 1]),
                            f"{het} offspring also show the dominant phenotype — count {homd} and both {het} boxes")]
        hint = f"Draw a Punnett square with gametes {t.A} and {t.a} from each parent, then count the phenotypes"
    else:
        first, second = (het, homr) if rng.random() < 0.5 else (homr, het)
        text = (f"{t.intro()} {t.plant(first)[0].upper() + t.plant(first)[1:]} is crossed with {t.plant(second)}. "
                f"Give the expected ratio of {dom_o} to {rec_o} in its simplest form.")
        ans = Answer(kind="ratio", display="1:1", value=[1, 1], form="simplest")
        sol = f"Punnett square: {het}, {het}, {homr}, {homr}. 2 dominant and 2 recessive phenotype: 2 : 2 = 1 : 1"
        mistakes = [Mistake(Answer(kind="ratio", display="3:1", value=[3, 1]),
                            f"That's the ratio for {het} × {het} — here one parent is {homr}"),
                    Mistake(Answer(kind="ratio", display="1:3", value=[1, 3]),
                            f"That's not the ratio for {het} × {homr} — count the boxes again")]
        hint = f"Draw a Punnett square: gametes {t.A} and {t.a} from one parent, {t.a} and {t.a} from the other"
    return _q(text, ans, sol, hint, mistakes)


def _pun_5(rng):
    if rng.random() < 0.5:
        t = _trait(rng)
        het, homr = t.A + t.a, t.a + t.a
        cross = rng.choice(("hh", "hh", "hr"))
        total = rng.randrange(10, 101) * 4
        ask = rng.choice(("dom", "rec"))
        if cross == "hh":
            frac = Fraction(3, 4) if ask == "dom" else Fraction(1, 4)
            parents = f"Two heterozygous {t.org} ({het} × {het}) are crossed"
            other = 1 - frac
        else:
            frac = Fraction(1, 2)
            parents = f"{t.plant(het)[0].upper() + t.plant(het)[1:]} is crossed with {t.plant(homr)}"
            other = None
        pheno = t.dom if ask == "dom" else t.rec
        v = frac * total
        what = f"be {t.word(pheno)}" if t.adj else f"have {pheno}"
        text = (f"{t.intro()} {parents}, and {total} offspring are produced. How many of the offspring would you "
                f"expect to {what}?")
        sol = f"Expected fraction = {frac.numerator}/{frac.denominator}. {frac.numerator}/{frac.denominator} × {total} = {n(v)}"
        return _q(text, _exact(v), sol,
                  "Use a Punnett square to find the fraction of offspring with that phenotype, then multiply by the total",
                  [_mk(other * total if other is not None else None, "",
                       "That's the number with the other phenotype — check which one the question asks about"),
                   _mk(Fraction(total, 2) if frac != Fraction(1, 2) else None, "",
                       "Use the Punnett square: the fraction is not 1/2 for this cross")])
    kind = rng.choice(("cf_both", "cf_neither", "hr_both"))
    if kind == "hr_both":
        t = _trait(rng)
        het, homr = t.A + t.a, t.a + t.a
        text = (f"{t.intro()} {t.plant(het)[0].upper() + t.plant(het)[1:]} is crossed with {t.plant(homr)}. Two "
                f"offspring are chosen. What is the probability that both of them have the genotype {homr}? Give your "
                f"answer as a fraction.")
        v = Fraction(1, 4)
        sol = f"P(one offspring is {homr}) = 1/2. P(both) = 1/2 × 1/2 = 1/4"
        mistakes = [_fmistake(Fraction(1, 2), "That's for one offspring — multiply the probabilities for the two offspring"),
                    _fmistake(Fraction(1), "Multiply the probabilities, don't add them")]
        hint = "Find the probability for one offspring first, then multiply for two"
    else:
        lead = ("Cystic fibrosis is an inherited disorder caused by a recessive allele (f). The dominant allele is F. "
                "Two parents are both carriers (Ff).")
        if kind == "cf_both":
            text = (f"{lead} They have two children. What is the probability that both children have cystic fibrosis? "
                    f"Give your answer as a fraction.")
            v = Fraction(1, 16)
            sol = "P(one child is ff) = 1/4. P(both children) = 1/4 × 1/4 = 1/16"
            mistakes = [_fmistake(Fraction(1, 4), "That's for one child — multiply the probabilities for the two children"),
                        _fmistake(Fraction(1, 2), "Multiply the probabilities for the two children, don't add them"),
                        _fmistake(Fraction(1, 8), "Multiply 1/4 by 1/4: 1 × 1 = 1 and 4 × 4 = 16")]
        else:
            text = (f"{lead} They have two children. What is the probability that neither child has cystic fibrosis? "
                    f"Give your answer as a fraction.")
            v = Fraction(9, 16)
            sol = "P(one child does not have it) = 3/4 (FF, Ff, Ff). P(neither) = 3/4 × 3/4 = 9/16"
            mistakes = [_fmistake(Fraction(3, 4), "That's for one child — multiply the probabilities for the two children"),
                        _fmistake(Fraction(1, 16), "That's the probability that both children have it"),
                        _fmistake(Fraction(15, 16), "That's the probability that at least one child does not have it")]
        hint = "Use a Punnett square for Ff × Ff to find the probability for one child, then multiply for two children"
    return _q(text, _frac(v), sol, hint, mistakes)


# ============================================================ registration

def _skill(name: str, title: str, aliases: tuple[str, ...], levels: tuple, fallback: str) -> Skill:
    sid = f"{SUBJECT_ID}.{name}"
    if len(levels) != 5:
        raise ValueError(f"{sid}: needs 5 levels")

    def generate(level: int, seed: int) -> Problem:
        check_level(level)
        rng = random.Random(seed)
        d = levels[level - 1](rng)
        return build(sid, level, seed, fallback_hint=fallback, **d)

    generate.__name__ = f"generate_{name}"
    generate.__qualname__ = generate.__name__
    return Skill(id=sid, subject=SUBJECT_ID, title=title, aliases=aliases, generate=generate)


GEN_SKILLS: tuple[Skill, ...] = (
    _skill("magnification", "Magnification",
           ("magnification", "image size", "actual size", "microscope calculation", "magnification calculation",
            "micrometres"),
           (_mag_1, _mag_2, _mag_3, _mag_4, _mag_5), "magnification = image size ÷ actual size, with both in the same unit"),
    _skill("data_maths", "Biology maths",
           ("percentage change in mass", "rate of photosynthesis", "biology maths", "inverse square law",
            "anomalous result", "percentage change"),
           (_dm_1, _dm_2, _dm_3, _dm_4, _dm_5), "Write down the formula first, then substitute the values"),
    _skill("punnett", "Genetic crosses",
           ("punnett square", "genetic cross", "probability of offspring", "genotype", "phenotype",
            "monohybrid cross", "genetic crosses"),
           (_pun_1, _pun_2, _pun_3, _pun_4, _pun_5), "Draw a Punnett square with the gametes of each parent on the sides"),
)

_ROWS = (
    (("cells", "Cells & transport", ("cells", "magnification")),
     ("organisation", "Organisation & disease", ("organisation",))),
    (("bioenergetics", "Bioenergetics & homeostasis", ("bioenergetics", "data_maths")),
     ("genetics_ecology", "Genetics & ecology", ("genetics_ecology", "punnett"))),
)
_ORDER = ("cells", "magnification", "organisation", "bioenergetics", "data_maths", "genetics_ecology", "punnett")


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"{SUBJECT_ID}.y{y}.{slug}", label=label,
                    skills=tuple(f"{SUBJECT_ID}.{s}" for s in skills), level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Biology", order=16, years={10: _year(10), 11: _year(11)})


def skills() -> list[Skill]:
    """Generator skills plus the bank skills from packs/biology.json, in topic order."""
    by_id = {s.id: s for s in GEN_SKILLS}
    for s in load_pack(SUBJECT_ID, SUBJECT_ID):
        if s.id in by_id:
            raise ValueError(f"{s.id} is defined twice")
        by_id[s.id] = s
    wanted = [f"{SUBJECT_ID}.{x}" for x in _ORDER]
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise ValueError(f"biology: missing skills {missing}")
    return [by_id[w] for w in wanted] + [s for k, s in by_id.items() if k not in wanted]


def register(reg) -> None:
    """Register Biology (Years 10–11) with a tutor.content Registry."""
    reg.register(make_subject(), skills())
