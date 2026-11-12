"""Word answers: normalisation, folding and edit distance (docs/ARCHITECTURE_V2.md section 2.3).

Internal helpers for the ``choice`` and ``short`` answer kinds.  Every function is pure
and works on plain ``str``; nothing here raises on odd input.
"""
from __future__ import annotations

import functools
import re
import unicodedata

# ----------------------------------------------------------- characters

_SUBSUP = str.maketrans({
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-", "₊": "+", "₋": "-",
})
_QUOTES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "´": "'", "`": "'", "“": '"', "”": '"', "„": '"',
                         # minus and dash look-alikes, as in the v1 text normalisation ("−18" == "-18")
                         "−": "-", "‒": "-", "–": "-", "‐": "-", "‑": "-"})
_YO = str.maketrans({"ё": "е", "Ё": "Е"})


def char_normalise(s: str) -> str:
    """NFC; curly quotes -> straight; sub/superscript digits and signs -> plain."""
    return unicodedata.normalize("NFC", s).translate(_QUOTES).translate(_SUBSUP)


def has_alnum(s: str) -> bool:
    return any(c.isalnum() for c in s)


def is_letters_spaces(s: str) -> bool:
    return bool(s) and all(c.isalpha() or c == " " for c in s) and not s.isspace()


# --------------------------------------------------------------- folding

_LIGATURES = (("ß", "ss"), ("ẞ", "SS"), ("æ", "ae"), ("Æ", "AE"), ("œ", "oe"), ("Œ", "OE"),
              ("ø", "o"), ("Ø", "O"), ("ł", "l"), ("Ł", "L"))
_GERMAN = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"),
           ("ß", "ss"), ("ẞ", "SS"))


def _is_latin(c: str) -> bool:
    o = ord(c)
    return (c.isascii() and c.isalpha()) or 0xC0 <= o <= 0x24F or 0x1E00 <= o <= 0x1EFF


@functools.lru_cache(maxsize=65536)
def fold(s: str) -> str:
    """Plain fold: drop accents on Latin letters only (é -> e; Cyrillic й, Arabic, CJK untouched)."""
    s = s.translate(_YO)
    for a, b in _LIGATURES:
        if a in s:
            s = s.replace(a, b)
    if s.isascii():
        return s
    out: list[str] = []
    base_latin = False
    for c in unicodedata.normalize("NFKD", s):
        if unicodedata.combining(c):
            if base_latin:
                continue
            out.append(c)
            continue
        base_latin = _is_latin(c)
        out.append(c)
    return unicodedata.normalize("NFC", "".join(out))


def fold_german(s: str) -> str:
    """German variant: ä -> ae, ö -> oe, ü -> ue, ß -> ss, then the plain fold."""
    for a, b in _GERMAN:
        if a in s:
            s = s.replace(a, b)
    return fold(s)


# ----------------------------------------------------------- normalisers

_ARTICLE = re.compile(r"^(?:the|a|an) (?=\S)")
_KEEP_NUM = re.compile(r"(?<=\d)[./](?=\d)|-(?=\d)")


_NO_PUNCT = re.compile(r"[^\W_]*(?: +[^\W_]+)* *")


def _punct_to_space(s: str) -> str:
    """Remove punctuation except inside numbers; '-' and '/' between letters become a space."""
    if _NO_PUNCT.fullmatch(s):
        return s                                # fast path: letters, digits and spaces only
    out: list[str] = []
    n = len(s)
    for i, c in enumerate(s):
        if c.isalnum() or c == " " or unicodedata.category(c).startswith("M"):
            out.append(c)
            continue
        prev = s[i - 1] if i else ""
        nxt = s[i + 1] if i + 1 < n else ""
        if c in "./" and prev.isdigit() and nxt.isdigit():
            out.append(c)                       # 3.5, 1/2
        elif c == "-" and nxt.isdigit():
            out.append(c)                       # -5, 1914-1918, covid-19
        elif c == "-" and nxt.isalpha() and (not prev or prev in " =("):
            out.append(c)                       # y = -x: a minus sign before a letter, not a hyphen
        elif c in "'":
            continue                            # apostrophes are deleted: it's -> its
        elif c == "," and prev.isdigit() and nxt.isdigit():
            continue                            # 1,200 -> 1200
        elif c == ".":
            continue                            # U.K. -> uk, e.g. -> eg
        else:
            out.append(" ")                     # everything else separates words
    return "".join(out)


def _collapse(s: str) -> str:
    return " ".join(s.split())


def casefold(s: str) -> str:
    """str.casefold, but ß stays ß (so "strasse" for "straße" is an accent fold with a note)."""
    if "ß" not in s and "ẞ" not in s:
        return s.casefold()
    return "ß".join(part.casefold() for part in s.replace("ẞ", "ß").split("ß"))


@functools.lru_cache(maxsize=65536)
def norm_basic(s: str) -> str:
    """Form ``any`` without the article rule: casefold and punctuation removed."""
    return _collapse(_punct_to_space(casefold(char_normalise(s)).translate(_YO)))


@functools.lru_cache(maxsize=65536)
def norm_any(s: str) -> str:
    """Form ``any``: casefold, punctuation removed, one leading article dropped."""
    s = norm_basic(s)
    m = _ARTICLE.match(s)
    if m:
        s = s[m.end():]
    return s


def norm_strict_spaced(s: str) -> str:
    """Form ``strict`` before removing spaces (kept for word counts and containment)."""
    s = casefold(char_normalise(s)).translate(_YO)
    return _collapse(_punct_to_space(s))


def norm_strict(s: str) -> str:
    return norm_strict_spaced(s).replace(" ", "")


_CASE_DROP = re.compile(r"[\s.,;:!?\"']+")


def norm_case(s: str) -> str:
    """Form ``case``: no casefolding; whitespace and . , ; : ! ? \" ' removed."""
    return _CASE_DROP.sub("", char_normalise(s).translate(_YO))


_TONE_DIGIT = re.compile(r"(?<=[^\W\d_])[1-5]")


def norm_pinyin(s: str) -> str:
    """Form ``pinyin``: casefold, tone marks and tone numbers dropped, no spaces/apostrophes/hyphens."""
    s = char_normalise(s).casefold()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = s.replace("v", "u")                     # common keyboard spelling of ü (lv = lü)
    s = _TONE_DIGIT.sub("", s)
    return "".join(c for c in s if c.isalnum())


@functools.lru_cache(maxsize=65536)
def norm_form(s: str, form: str) -> tuple[str, str]:
    """(key, spaced copy) for a short-answer form."""
    if form == "strict":
        spaced = norm_strict_spaced(s)
        return spaced.replace(" ", ""), spaced
    if form == "case":
        key = norm_case(s)
        return key, _collapse(char_normalise(s))
    if form == "pinyin":
        key = norm_pinyin(s)
        return key, _collapse(char_normalise(s))
    key = norm_any(s)
    return key, key


# --------------------------------------------------------------- distance

def osa(a: str, b: str, cap: int | None = None) -> int:
    """Restricted Damerau-Levenshtein (optimal string alignment) distance.

    With ``cap``, any distance above ``cap`` is reported as ``cap + 1`` (fast exit).
    """
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if cap is not None and abs(la - lb) > cap:
        return cap + 1
    if not la or not lb:
        d = max(la, lb)
        return d if cap is None else min(d, cap + 1)
    prev2: list[int] = []
    prev = list(range(lb + 1))
    prev_min = 0
    for i in range(1, la + 1):
        ca = a[i - 1]
        cur = [i] + [0] * lb
        row_min = i
        for j in range(1, lb + 1):
            cb = b[j - 1]
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                v = min(v, prev2[j - 2] + 1)
            cur[j] = v
            if v < row_min:
                row_min = v
        # later cells come from this row, or from the previous one via a transposition (+1)
        if cap is not None and min(row_min, prev_min + 1) > cap:
            return cap + 1
        prev2, prev, prev_min = prev, cur, row_min
    d = prev[lb]
    return d if cap is None else min(d, cap + 1)


def osa_subs(a: str, b: str) -> tuple[int, int]:
    """(OSA distance, fewest substitutions over all optimal alignments).

    "photosinthesis" -> "photosynthesis" is (1, 1); "conversation" -> "conservation" is (2, 2);
    "chrmosomes" -> "chromosome" is (2, 0).  Meant for single words (quadratic, no cap).
    """
    la, lb = len(a), len(b)
    # cells hold (distance, substitutions); tuples compare lexicographically
    d = [[(0, 0)] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = (i, 0)
    for j in range(lb + 1):
        d[0][j] = (j, 0)
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            dl, ds = d[i - 1][j]
            il, is_ = d[i][j - 1]
            best = min((dl + 1, ds), (il + 1, is_))
            sd, ss = d[i - 1][j - 1]
            best = min(best, (sd, ss) if a[i - 1] == b[j - 1] else (sd + 1, ss + 1))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                td, ts = d[i - 2][j - 2]
                best = min(best, (td + 1, ts))
            d[i][j] = best
    return d[la][lb]


# ------------------------------------------------------------ word rules
# docs/ARCHITECTURE_V2.md section 10.2 (typo tolerance works word by word)

NEGATION_PREFIXES = ("non", "dis", "un", "in", "im", "ir", "il")


def prefix_change(x: str, y: str) -> bool:
    """One word is the other with a negation prefix added, removed or swapped (elastic / inelastic)."""
    for p in NEGATION_PREFIXES:
        if x == p + y or y == p + x:
            return True
        for q in NEGATION_PREFIXES:
            if p != q and x.startswith(p) and y.startswith(q) and x[len(p):] == y[len(q):]:
                return True
    return False


def word_form(x: str, y: str) -> bool:
    """x and y are regular forms of one word: -s, -es, -ed, -ing (alkane / alkanes, translate / translated)."""
    for a, b in ((x, y), (y, x)):
        if a in (b + "s", b + "es", b + "ed", b + "ing"):
            return True
        if b.endswith("e") and a in (b + "d", b[:-1] + "ing"):
            return True
        if b.endswith("y") and len(b) > 2 and a in (b[:-1] + "ies", b[:-1] + "ied"):
            return True
    return False
