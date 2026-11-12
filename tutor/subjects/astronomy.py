"""Astronomy (GCSE, Years 10–11): generator skills here, bank skills in packs/astronomy.json.

docs/ARCHITECTURE_V2.md section 5.1. Every constant a question needs (1 AU, the speed of light,
H₀, 1 pc = 3.26 ly, the formulae) is stated in the question. Values are exact Fractions until the
final rounding, and a value close to a rounding boundary is never used.
"""
from __future__ import annotations

import math
import random
from fractions import Fraction

from ..content import Answer, Mistake, Problem, Skill, Subject, Topic, YearSpec, load_pack
from ..content.fmt import (
    build, check_level, dec, fmt_dp, fmt_num, fmt_sf, fmt_std, num_answer, num_mistake, retry,
    sig_digits, std_answer, std_mistake, unit,
)

SUBJECT_ID = "astronomy"
Draft = dict

AU_KM = Fraction(15) * 10 ** 7                 # 1.50 × 10^8 km
AU_TXT = "Use 1 AU = 1.50 × 10^8 km."
C_KMS = Fraction(3) * 10 ** 5                  # 3.00 × 10^5 km/s
C_TXT = "The speed of light is 3.00 × 10^5 km/s."
PC_LY = Fraction(326, 100)
PC_TXT = "Use 1 parsec (pc) = 3.26 light years (ly)."
H0 = 70
H0_TXT = "Use H₀ = 70 km/s per Mpc."
SF_TXT = "Give your answer to 3 significant figures."
DP_TXT = "Give your answer to 1 decimal place."


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


def _short(v) -> bool:
    try:
        f = Fraction(v)
    except (TypeError, ValueError):
        return False
    d = f.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    return d == 1 and sig_digits(f) <= 4


def _sf3(v, u: str) -> Answer:
    """Exact display when short, else 3 s.f. (the question always asks for 3 s.f.)."""
    return num_answer(v, unit(fmt_sf(v, 3), u), sf=3)


def _m(v, u: str, fb: str, sf: int | None = 3, dp: int | None = None) -> Mistake | None:
    if v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        return None
    if x == 0 or not math.isfinite(x):
        return None
    if dp is not None:
        return num_mistake(v, u, fb, dp=dp)
    if sf is None:
        return num_mistake(v, u, fb)
    return num_mistake(v, u, fb, sf=sf)


def _approx(v) -> str:
    """Working value: exact when short, else 4 s.f. followed by '…'."""
    if _short(v):
        return n(v)
    return fmt_sf(v, 4) + "…"


# ================================================================== orbits

_PLANETS_AU = (("Mercury", "0.39"), ("Venus", "0.72"), ("Mars", "1.52"), ("Jupiter", "5.20"), ("Saturn", "9.58"),
               ("Uranus", "19.2"), ("Neptune", "30.1"))


def _orb_1(rng):
    if rng.random() < 0.5:
        if rng.random() < 0.6:
            name, a_txt = rng.choice(_PLANETS_AU)
            a = F(a_txt)
            what = f"{name}'s mean distance from the Sun is {a_txt} AU"
        else:
            a = F(rng.randrange(15, 46)) / 10
            a_txt = n(a)
            what = f"An asteroid orbits the Sun at a mean distance of {a_txt} AU"
        km = a * AU_KM
        ans = std_answer(km, "km", round_to_sf=3)
        return _q(f"{what}. Convert this distance into kilometres. {AU_TXT} Give your answer in standard form to 3 "
                  f"significant figures.",
                  ans, f"{a_txt} × 1.50 × 10^8 = {ans.display}",
                  "Multiply the number of AU by the number of km in 1 AU",
                  [std_mistake(a / AU_KM, "km", "Multiply by 1.50 × 10^8 to change AU into km — don't divide", round_to_sf=3),
                   std_mistake(a * F("1.5") * 10 ** 6, "km", "Check the power of ten: 1 AU = 1.50 × 10^8 km", round_to_sf=3)])

    def make(r):
        e = r.choice((11, 12, 13))
        mant = F(r.randrange(11, 31 if e == 13 else 99)) / 10      # at most 3.0 × 10^13 km (2 × 10^5 AU)
        km = mant * Fraction(10) ** e
        au = km / AU_KM
        return None if not _rounding_ok(au, sf=3) else (mant, e, km, au)
    mant, e, km, au = retry(make, rng)
    if e == 11:
        body = rng.choice(("A long-period comet at its furthest point", "An icy object in the outer Solar System"))
    else:
        body = rng.choice(("A comet in the Oort cloud", "An icy body in the Oort cloud"))
    ans = std_answer(au, "AU", round_to_sf=3)
    return _q(f"{body} is {n(mant)} × 10^{e} km from the Sun. Express this distance in astronomical units (AU). "
              f"{AU_TXT} Give your answer in standard form to 3 significant figures.",
              ans, f"distance = ({n(mant)} × 10^{e}) ÷ (1.50 × 10^8) = {ans.display}",
              "Divide the distance in km by the number of km in 1 AU",
              [std_mistake(km * AU_KM, "AU", "Divide by 1.50 × 10^8 to change km into AU — don't multiply", round_to_sf=3),
               std_mistake(km / (F("1.5") * 10 ** 6), "AU", "Check the power of ten: 1 AU = 1.50 × 10^8 km", round_to_sf=3)])


KEPLER_TXT = "Use Kepler's third law, T² = a³ (T = orbital period in years, a = mean distance from the Sun in AU)."


def _orb_2(rng):
    def make(r):
        if r.random() < 0.35:
            a = F(r.choice(("4", "9", "16", "25", "0.25", "2.25", "6.25", "36")))
        else:
            a = F(r.randrange(5, 400)) / 10
            if a == 1:
                return None
        t = math.sqrt(float(a) ** 3)
        exact = Fraction(t).limit_denominator(1000) if float(Fraction(t).limit_denominator(1000)) == t else None
        if exact is None and not _rounding_ok(t, sf=3):
            return None
        return a, t, exact
    a, t, exact = retry(make, rng)
    body = rng.choice(("An asteroid", "A comet", "A dwarf planet", "A planet"))
    val = exact if exact is not None else t
    return _q(f"{body} orbits the Sun at a mean distance of {n(a)} AU. {KEPLER_TXT} Calculate its orbital period. "
              f"Give your answer in years to 3 significant figures.",
              _sf3(val, "years"), f"T² = a³ = {n(a)}³ = {_approx(a ** 3)}, so T = √{_approx(a ** 3)} = {fmt_sf(val, 3)} years",
              "Cube the distance, then take the square root",
              [_m(a ** 3, "years", "T² = a³, so take the square root of a³ at the end"),
               _m(float(a) ** (2 / 3), "years", "T² = a³: cube a first, then square-root — not the other way round"),
               _m(a * a, "years", "T² = a³: cube the distance (a × a × a), then take the square root")])


def _orb_3(rng):
    def make(r):
        if r.random() < 0.35:
            t = F(r.choice(("8", "27", "64", "125", "0.125", "3.375", "1000", "216")))
        else:
            t = F(r.randrange(5, 300)) / 2
            if t == 1:
                return None
        a = float(t) ** (2 / 3)
        exact = Fraction(round(a * 1000), 1000) if abs(a * 1000 - round(a * 1000)) < 1e-9 else None
        if exact is None and not _rounding_ok(a, sf=3):
            return None
        return t, a, exact
    t, a, exact = retry(make, rng)
    body = rng.choice(("An asteroid", "A comet", "A dwarf planet", "A planet"))
    val = exact if exact is not None else a
    return _q(f"{body} takes {n(t)} years to orbit the Sun. {KEPLER_TXT} Calculate its mean distance from the Sun. "
              f"Give your answer in AU to 3 significant figures.",
              _sf3(val, "AU"), f"a³ = T² = {n(t)}² = {_approx(t * t)}, so a = ∛{_approx(t * t)} = {fmt_sf(val, 3)} AU",
              "Square the period, then take the cube root",
              [_m(float(t) ** 1.5, "AU", "a³ = T²: square T, then take the cube root — not the other way round"),
               _m(t * t, "AU", "a³ = T², so take the cube root of T² at the end"),
               _m(math.sqrt(float(t)), "AU", "a³ = T²: square T first, then take the cube root")])


# (description, radius in km as Fraction, its text, period value, period unit, seconds per unit)
_ORBITS = (
    ("The Moon orbits the Earth", F("384000"), "3.84 × 10^5 km", F("27.3"), "days", 86400),
    ("The International Space Station orbits the Earth", F("6780"), "6780 km", F("92.7"), "minutes", 60),
    ("The Earth orbits the Sun", F("150000000"), "1.50 × 10^8 km", F("365"), "days", 86400),
    ("A geostationary satellite orbits the Earth", F("42200"), "42 200 km", F("24"), "hours", 3600),
)


def _orb_4(rng):
    if rng.random() < 0.5:
        desc, r_km, r_txt, per, per_u, secs = rng.choice(_ORBITS)
    else:
        # a real Earth orbit: the period follows from the radius (GM of the Earth = 398 600 km³/s²)
        r_km = F(rng.randrange(68, 421)) * 100
        t_real = 2 * math.pi * math.sqrt(float(r_km) ** 3 / 398600)
        if t_real < 300 * 60:
            per, per_u, secs = F(fmt_sf(t_real / 60, 3)), "minutes", 60
        else:
            per, per_u, secs = F(fmt_sf(t_real / 3600, 3)), "hours", 3600
        desc, r_txt = "A satellite orbits the Earth", f"{n(r_km)} km"
    t_s = per * secs
    v = 2 * math.pi * float(r_km) / float(t_s)
    if not _rounding_ok(v, sf=3):
        return _orb_4(random.Random(rng.randrange(2 ** 31)))
    unit_word = per_u if per != 1 else per_u[:-1]
    conv = {"days": "× 24 × 60 × 60", "hours": "× 60 × 60", "minutes": "× 60"}[per_u]
    text = (f"{desc} in a circular orbit of radius {r_txt}. One orbit takes {n(per)} {unit_word}. Calculate its orbital "
            f"speed using v = 2πr ÷ T. Give your answer in km/s to 3 significant figures.")
    sol = (f"T = {n(per)} {conv} = {n(t_s)} s. v = 2π × {r_txt.replace(' km', '')} ÷ {n(t_s)} = {fmt_sf(v, 3)} km/s")
    return _q(text, num_answer(v, f"{fmt_sf(v, 3)} km/s", sf=3), sol,
              f"Convert the period into seconds first, then use v = 2πr ÷ T",
              [_m(float(r_km) / float(t_s), "km/s", "Use the circumference of the orbit: distance = 2πr"),
               _m(2 * math.pi * float(r_km) / float(per), "km/s", f"Convert the period into seconds first ({conv})"),
               _m(math.pi * float(r_km) / float(t_s), "km/s", "The circumference is 2πr, not πr")])


def _orb_5(rng):
    if rng.random() < 0.5:
        def make(r):
            d = F(r.randrange(3, 120)) / 10
            minutes = d * AU_KM / C_KMS / 60
            return None if not _rounding_ok(minutes, sf=3) else (d, minutes)
        d, minutes = retry(make, rng)
        body = rng.choice(("a space probe", "a planet", "an asteroid", "a comet"))
        secs = d * AU_KM / C_KMS
        text = (f"Light travels from the Sun to {body} {n(d)} AU away. {AU_TXT} {C_TXT} Calculate how long the light "
                f"takes. Give your answer in minutes to 3 significant figures.")
        sol = (f"distance = {n(d)} × 1.50 × 10^8 = {fmt_std(d * AU_KM)} km. time = distance ÷ speed = "
               f"{_approx(secs)} s = {_approx(secs)} ÷ 60 = {fmt_sf(minutes, 3)} minutes")
    else:
        def make(r):
            mant = F(r.randrange(11, 99)) / 10
            e = r.choice((7, 8, 9))
            km = mant * Fraction(10) ** e
            minutes = km / C_KMS / 60
            return None if not _rounding_ok(minutes, sf=3) else (mant, e, km, minutes)
        mant, e, km, minutes = retry(make, rng)
        secs = km / C_KMS
        body = rng.choice(("a space probe", "a planet", "a comet"))
        text = (f"A radio signal is sent from Earth to {body} {n(mant)} × 10^{e} km away. Radio waves travel at the "
                f"speed of light. {C_TXT} Calculate how long the signal takes to arrive. Give your answer in minutes "
                f"to 3 significant figures.")
        sol = (f"time = distance ÷ speed = ({n(mant)} × 10^{e}) ÷ (3.00 × 10^5) = {_approx(secs)} s = "
               f"{_approx(secs)} ÷ 60 = {fmt_sf(minutes, 3)} minutes")
    return _q(text, num_answer(minutes, f"{fmt_sf(minutes, 3)} min", sf=3), sol,
              "time = distance ÷ speed — make sure the distance is in km, then convert the seconds into minutes",
              [_m(secs, "min", "That's the time in seconds — divide by 60 to get minutes"),
               _m(secs / 3600, "min", "There are 60 seconds in a minute — divide the seconds by 60, not 3600")])


# =============================================================== distances

def _dist_1(rng):
    def make(r):
        x = F(r.randrange(11, 999)) / 10
        return x
    x = retry(make, rng)
    if rng.random() < 0.5:
        v = x * PC_LY
        if not _rounding_ok(v, sf=3):
            return _dist_1(random.Random(rng.randrange(2 ** 31)))
        return _q(f"A star is {n(x)} pc from the Earth. {PC_TXT} Calculate its distance in light years. {SF_TXT}",
                  _sf3(v, "ly"), f"{n(x)} × 3.26 = {fmt_sf(v, 3)} ly",
                  "A light year is shorter than a parsec, so the number of light years is bigger",
                  [_m(x / PC_LY, "ly", "Multiply by 3.26 to change parsecs into light years — the number should get bigger")])
    v = x / PC_LY
    if not _rounding_ok(v, sf=3):
        return _dist_1(random.Random(rng.randrange(2 ** 31)))
    return _q(f"A star is {n(x)} light years from the Earth. {PC_TXT} Calculate its distance in parsecs. {SF_TXT}",
              _sf3(v, "pc"), f"{n(x)} ÷ 3.26 = {fmt_sf(v, 3)} pc",
              "A parsec is longer than a light year, so the number of parsecs is smaller",
              [_m(x * PC_LY, "pc", "Divide by 3.26 to change light years into parsecs — the number should get smaller")])


_PARALLAX_STARS = (("Proxima Centauri", "0.768"), ("Sirius", "0.379"), ("Barnard's Star", "0.547"),
                   ("Vega", "0.130"), ("Altair", "0.195"), ("Procyon", "0.285"))
PARALLAX_TXT = "Use d = 1 ÷ p, where d is the distance in parsecs and p is the parallax angle in arcseconds."


def _dist_2(rng):
    kind = rng.choice(("nice", "real", "reverse"))
    if kind == "reverse":
        d = F(rng.choice(("2", "4", "5", "8", "10", "20", "25", "40", "50", "12.5", "2.5")))
        p = 1 / d
        return _q(f"A star is {n(d)} pc from the Earth. {PARALLAX_TXT} Calculate its parallax angle in arcseconds.",
                  num_answer(p, f"{n(p)} arcseconds"), f"p = 1 ÷ d = 1 ÷ {n(d)} = {n(p)} arcseconds",
                  "Rearrange d = 1 ÷ p to make p the subject",
                  [_m(d, "arcseconds", "p = 1 ÷ d — divide 1 by the distance", sf=None)])
    if kind == "nice":
        p = F(rng.choice(("0.5", "0.25", "0.2", "0.1", "0.125", "0.05", "0.04", "0.02", "0.025", "0.08", "0.01")))
        star = "A star"
    else:
        star, p_txt = rng.choice(_PARALLAX_STARS)
        p = F(p_txt)
    d = 1 / p
    p_txt = fmt_dp(p, 3) if kind == "real" else n(p)
    if _short(d):
        ans, tail, shown = num_answer(d, f"{n(d)} pc"), "", f"{n(d)} pc"
    else:
        ans, tail, shown = _sf3(d, "pc"), f" {SF_TXT}", f"{fmt_sf(d, 3)} pc"
    return _q(f"{star} has a parallax angle of {p_txt} arcseconds. {PARALLAX_TXT} Calculate its distance from the "
              f"Earth in parsecs.{tail}",
              ans, f"d = 1 ÷ p = 1 ÷ {p_txt} = {shown}",
              "Divide 1 by the parallax angle",
              [_m(p, "pc", "d = 1 ÷ p — divide 1 by the parallax angle", sf=None),
               _m(d * PC_LY, "pc", "d = 1 ÷ p gives the distance in parsecs — don't convert it into light years")])


def _dist_3(rng):
    d = rng.choice((10, 15, 20, 25, 30, 40, 45, 50, 60, 75, 80, 100, 120, 150, 200, 250, 300, 400, 500))
    v = H0 * d
    gal = rng.choice(("A galaxy", "A distant galaxy", "A spiral galaxy", "An elliptical galaxy"))
    return _q(f"{gal} is {d} Mpc from the Earth. {H0_TXT} Use Hubble's law, v = H₀ × d, to calculate the speed at "
              f"which the galaxy is moving away from us, in km/s.",
              num_answer(v, f"{v} km/s"), f"v = H₀ × d = 70 × {d} = {v} km/s",
              "Multiply the Hubble constant by the distance in Mpc",
              [_m(Fraction(d, H0), "km/s", "v = H₀ × d — multiply, don't divide"),
               _m(Fraction(H0, d), "km/s", "v = H₀ × d — multiply, don't divide")])


def _dist_4(rng):
    if rng.random() < 0.5:
        d = rng.choice((20, 30, 40, 50, 60, 80, 100, 120, 150, 200, 250, 300, 350, 400, 450, 500))
        v = H0 * d
        ans, tail, shown = num_answer(d, f"{d} Mpc"), "", f"{d} Mpc"
        dv = Fraction(d)
    else:
        def make(r):
            v = r.randrange(30, 400) * 100
            dv = Fraction(v, H0)
            if dv.denominator == 1 or not _rounding_ok(dv, sf=3):
                return None
            return v, dv
        v, dv = retry(make, rng)
        ans, tail, shown = _sf3(dv, "Mpc"), f" {SF_TXT}", f"{fmt_sf(dv, 3)} Mpc"
    gal = rng.choice(("A galaxy", "A distant galaxy", "A spiral galaxy", "An elliptical galaxy"))
    return _q(f"{gal} is moving away from the Earth at {v:,} km/s. {H0_TXT} Use Hubble's law, v = H₀ × d, to calculate "
              f"its distance in Mpc.{tail}",
              ans, f"d = v ÷ H₀ = {v:,} ÷ 70 = {shown}",
              "Rearrange v = H₀ × d to make d the subject",
              [_m(v * H0, "Mpc", "d = v ÷ H₀ — divide, don't multiply"),
               _m(Fraction(H0, v), "Mpc", "d = v ÷ H₀ — you divided the wrong way round")])


DM_TXT = "Use m − M = 5 log₁₀(d) − 5, where d is the distance in parsecs."


def _dist_5(rng):
    kind = rng.choice(("M", "m", "mod"))

    def make(r):
        d = r.choice((r.randrange(2, 100), r.randrange(10, 100) * 10, r.randrange(10, 100) * 100))
        mod = 5 * math.log10(d) - 5
        if kind == "M":
            app = F(r.randrange(-10, 150)) / 10          # apparent magnitude m
            v = float(app) - mod
            ok = -10 <= v <= 16
        elif kind == "m":
            app = F(r.randrange(-50, 150)) / 10          # absolute magnitude M
            v = float(app) + mod
            ok = -1.5 <= v <= 22
        else:
            app = F(0)
            v = mod
            ok = True
        if not ok or not _rounding_ok(v, dp=1) or abs(v) < 0.05:
            return None
        return d, mod, app, v
    d, mod, app, v = retry(make, rng)
    star = "A star"
    if kind == "M":
        text = (f"{star} is {d} pc from the Earth and has an apparent magnitude m = {fmt_dp(app, 1)}. {DM_TXT} "
                f"Calculate its absolute magnitude M. {DP_TXT}")
        sol = (f"m − M = 5 log₁₀({d}) − 5 = {_approx(mod)}, so M = {fmt_dp(app, 1)} − {_approx(mod)} = {fmt_dp(v, 1)}")
        wrong = [_m(float(app) + mod, "", "M = m − (5 log₁₀(d) − 5): subtract the distance modulus, don't add it", dp=1),
                 _m(float(app) - 5 * math.log10(d), "", "The distance modulus is 5 log₁₀(d) − 5 — don't forget the − 5", dp=1)]
    elif kind == "m":
        text = (f"{star} is {d} pc from the Earth and has an absolute magnitude M = {fmt_dp(app, 1)}. {DM_TXT} "
                f"Calculate its apparent magnitude m. {DP_TXT}")
        sol = (f"m − M = 5 log₁₀({d}) − 5 = {_approx(mod)}, so m = {fmt_dp(app, 1)} + {_approx(mod)} = {fmt_dp(v, 1)}")
        wrong = [_m(float(app) - mod, "", "m = M + (5 log₁₀(d) − 5): add the distance modulus, don't subtract it", dp=1),
                 _m(float(app) + 5 * math.log10(d), "", "The distance modulus is 5 log₁₀(d) − 5 — don't forget the − 5", dp=1)]
    else:
        text = f"{star} is {d} pc from the Earth. {DM_TXT} Calculate its distance modulus, m − M. {DP_TXT}"
        sol = f"m − M = 5 × log₁₀({d}) − 5 = 5 × {_approx(math.log10(d))} − 5 = {fmt_dp(v, 1)}"
        wrong = [_m(5 * math.log10(d), "", "Don't forget to subtract 5 at the end", dp=1),
                 _m(5 * math.log(d) - 5, "", "Use log base 10 (the log button), not ln", dp=1)]
    return _q(text, num_answer(v, fmt_dp(v, 1), dp=1), sol,
              "Work out 5 log₁₀(d) − 5 first, using the log button on your calculator", wrong)


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
    _skill("orbits", "Orbits & Kepler's third law",
           ("kepler's third law", "orbital period", "astronomical unit", "orbital speed", "kepler", "light travel time"),
           (_orb_1, _orb_2, _orb_3, _orb_4, _orb_5), "Write down the formula given in the question, then substitute"),
    _skill("distances", "Distances & Hubble's law",
           ("hubble's law", "light year", "parsec", "parallax calculation", "distance modulus", "hubble constant"),
           (_dist_1, _dist_2, _dist_3, _dist_4, _dist_5), "Write down the formula given in the question, then substitute"),
)

_ROWS = (
    (("earth_moon_sun", "Earth, Moon & Sun", ("earth_moon_sun",)),
     ("solar_system", "The Solar System", ("solar_system", "orbits"))),
    (("stars_galaxies", "Stars & galaxies", ("stars_galaxies", "distances")),
     ("observing", "Observing the sky", ("observing",))),
)
_ORDER = ("earth_moon_sun", "solar_system", "orbits", "stars_galaxies", "distances", "observing")


def _year(y: int) -> YearSpec:
    rows = tuple(
        tuple(Topic(id=f"{SUBJECT_ID}.y{y}.{slug}", label=label,
                    skills=tuple(f"{SUBJECT_ID}.{s}" for s in skills), level_map=(1, 2, 3, 4, 5))
              for slug, label, skills in row)
        for row in _ROWS)
    return YearSpec(rows=rows, past_paper_level_map=(2, 3, 3, 4, 5))


def make_subject() -> Subject:
    return Subject(id=SUBJECT_ID, title="Astronomy", order=28, years={10: _year(10), 11: _year(11)})


def skills() -> list[Skill]:
    """Generator skills plus the bank skills from packs/astronomy.json, in topic order."""
    by_id = {s.id: s for s in GEN_SKILLS}
    for s in load_pack(SUBJECT_ID, SUBJECT_ID):
        if s.id in by_id:
            raise ValueError(f"{s.id} is defined twice")
        by_id[s.id] = s
    wanted = [f"{SUBJECT_ID}.{x}" for x in _ORDER]
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise ValueError(f"astronomy: missing skills {missing}")
    return [by_id[w] for w in wanted] + [s for k, s in by_id.items() if k not in wanted]


def register(reg) -> None:
    """Register Astronomy (Years 10–11) with a tutor.content Registry."""
    reg.register(make_subject(), skills())
