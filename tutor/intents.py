"""Pure text-classification helpers."""
from __future__ import annotations

import functools
import re

from .db import CODE_ALPHABET, CODE_LENGTH

_KEEP = set("'%=/^+-*().,")


def normalize(text: str) -> str:
    text = (text or "").lower().replace("’", "'").replace("‘", "'")
    text = "".join(c if (c.isalnum() or c.isspace() or c in _KEEP) else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()


def command_name(text: str) -> str | None:
    text = (text or "").strip()
    if not text.startswith("/"):
        return None
    first = text.split(None, 1)[0]
    return first.split("@", 1)[0].lower()


_CODE_PREFIX = re.compile(r"^(?:(?:my|the|access|your)\s+)*(?:access\s+)?code(?:\s+is)?\s*[:=\-]?\s*", re.IGNORECASE)
_QUOTES = "\"'`“”‘’«»„"


def normalize_code(text: str) -> str | None:
    """The code the student typed, or None if the text is not a code attempt.

    Accepts 'abcd-2345', 'Code: ABCD2345', '"ABCD2345".'. Only text with at least one
    digit, or exactly 8 characters from the code alphabet, counts as an attempt, so
    ordinary words ('thanks', 'hello there') get the code request instead of CODE_BAD.
    """
    if text is None:
        return None
    text = text.strip()
    if text.startswith("/"):
        return None
    text = _CODE_PREFIX.sub("", text).strip()
    text = text.strip(_QUOTES + " .,!?;:").strip()
    code = re.sub(r"[\s\-]+", "", text).upper()
    if not re.fullmatch(r"[A-Z0-9]{6,12}", code):
        return None
    if any(c.isdigit() for c in code):
        return code
    if len(code) == CODE_LENGTH and set(code) <= set(CODE_ALPHABET):
        return code
    return None


def parse_year(text: str) -> tuple[int, str] | None:
    t = (text or "").strip().lower().replace("—", "–")
    if re.fullmatch(r"(?:year\s*|yr\s*|y\s*)?1\s*[-–]\s*6", t):
        return 6, "Year 1–6"
    m = re.fullmatch(r"(?:year\s*|yr\s*|y\s*)?(\d{1,2})", t)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 13:
            return n, f"Year {n}"
    return None


# ------------------------------------------------------------------ safety

# Applied in order to the normalised text before matching (word boundaries on both sides).
_SAFETY_REWRITES = (
    (r"\bwanna\b", "want to"),
    (r"\bwant 2\b", "want to"),
    (r"\bwant too\b", "want to"),
    (r"\bgonna\b", "going to"),
    (r"\b(?:dont|don't|do not)\b", "do not"),
    (r"\b(?:doesnt|doesn't)\b", "does not"),
    (r"\b(?:cant|can't|cannot)\b", "can not"),
    (r"\b(?:im|i'm)\b", "i am"),
    (r"\b(?:ive|i've)\b", "i have"),
    (r"\b(?:isnt|isn't|is not)\b", "is not"),
    (r"\bmy self\b", "myself"),
    (r"\bself[ -]?harm", "self harm"),
    (r"\bsu[ie]?c[ie]?de?\b", "suicide"),            # sucide, suicde, sucid
    (r"\bsuicid(?:le|al+)\b", "suicidal"),
    (r"\bsuiside\b", "suicide"),
    (r"\bpics\b|\bpictures\b|\bphotos\b|\bpic\b|\bphoto\b|\bimages\b", "pics"),
    (r"\bmum\b|\bmom\b|\bmummy\b|\bmommy\b|\bmother\b", "mum"),
    (r"\bdad\b|\bdaddy\b|\bfather\b", "dad"),
)
_SAFETY_REWRITES = tuple((re.compile(p), r) for p, r in _SAFETY_REWRITES)

_DISTRESS = (
    # suicide / self-harm
    "kill myself", "killing myself", "unalive myself", "unalive", "unaliving", "kys", "kill yourself",
    "want to die", "wanting to die", "want to be dead", "wish i was dead", "wish i were dead",
    "wish i was not alive", "wish i was never born", "end my life", "ending my life", "end it all",
    "take my own life", "take my life", "suicide", "suicidal", "self harm", "self harming",
    "hurt myself", "hurting myself", "harm myself", "harming myself", "cut myself", "cutting myself",
    "overdose", "do not want to live", "do not want to be alive", "no reason to live",
    "nothing to live for", "better off dead", "better off without me", "nobody would care if i",
    "no one would care if i", "nobody would miss me", "no one would miss me",
    "want to kms", "going to kms", "about to kms", "should kms", "will kms", "might kms", "k m s",
    "going to end it", "cut my wrists", "cutting my wrists", "slit my wrists", "been cutting", "took pills",
    "taking pills", "took too many pills", "not worth living", "feel like dying", "can not go on",
    "do not want to be here anymore", "want to disappear", "nobody loves me", "no one loves me",
    "starve myself", "starving myself", "make myself sick", "making myself sick", "make myself throw up",
    "want to hurt someone", "want to kill someone", "going to hurt someone",
    # bullying
    "being bullied", "getting bullied", "bullied", "bully me", "bullying me", "bullies me",
    # abuse
    "abused", "abusing me", "abuse me", "abuses me", "hits me", "hitting me", "beats me", "beat me up",
    "hurts me", "touched me", "touches me", "touching me",
    # grooming / exploitation
    "send nudes", "send nude", "nudes", "pics of myself", "pics of me", "asked me to send",
    "wants me to send", "told me to send", "make me send", "wants to meet me", "want to meet me",
    "asked to meet me", "secret from my parents", "secret from my mum", "secret from my dad",
    "secret from my family",
    # not safe: personal forms only ("unsafe", "not safe" and "danger zone" are curriculum words in food
    # safety, D&T and PE answers; docs/ARCHITECTURE_V2.md section 10.2)
    "i am not safe", "i am unsafe", "not feel safe", "feel unsafe", "feeling unsafe", "not safe at home",
    "unsafe at home", "not safe at school", "unsafe at school", "not safe for me", "unsafe for me",
    "not safe here", "we are not safe", "scared to go home", "afraid to go home",
    "is following me", "are following me", "been following me",
)
# "<someone> hit/hurt/kicked me": the person in front avoids flagging "hit me with a question"
_DISTRESS_RE = (
    re.compile(r"\b(?:he|she|they|someone|somebody|mum|dad|step ?dad|step ?mum|parents?|brother|sister|"
               r"uncle|aunt|auntie|grandad|grandpa|grandma|nan|teacher|coach|boyfriend|girlfriend|man|guy|"
               r"adult|people|kids|boys|girls)\s+(?:hit|hurt|kicked|punched|slapped|beat|touched|abused|"
               r"threatened|hits|kicks|punches|slaps|threatens)\s+me\b"),
    re.compile(r"\bscared of (?:my )?(?:mum|dad|step ?dad|step ?mum|parents?|brother|uncle|him|her)\b"),
    # "i am in danger", "my mum is in danger"; not "the danger zone" or "in danger of extinction"
    re.compile(r"\bin danger\b(?! zone)(?! of\b)"),
)

_WORK = (r"(?:(?:maths|math|physics|science|chemistry|biology|english|french|history|geography) )?"
         r"(?:homework|hw|test|exam|assignment|coursework|worksheet|classwork)(?: questions?)?")
_CHEAT_RE = tuple(re.compile(p) for p in (
    rf"\b(?:do|finish|complete|solve|answer) my {_WORK}\b",                 # "do my maths homework"
    rf"\b(?:do|finish|complete|solve|answer) (?:this|the|our) {_WORK} for me\b",
    r"\bdo it for me\b",
    r"\bwrite (?:my|an|the) essay\b",
    r"\bwrite my coursework\b",
    r"\b(?:give|send|tell|get) me (?:the |all the |all )?(?:test |exam |homework |mock )?answers\b",
    r"\b(?:need|want) (?:the |all the )(?:test|exam|homework|mock) answers\b",
    r"\banswers (?:to|for) (?:the|my|this|tomorrow's|tomorrows|our|the next) (?:test|exam|mock|homework|hw)\b",
    r"\banswer key\b",
))

_SKIP_EXACT = {"skip", "next", "pass", "i don't know", "i dont know", "idk", "dunno", "no idea",
               "give up", "i give up", "show answer", "show me the answer",
               "no clue", "not sure", "im not sure", "i'm not sure", "unsure",
               # whole-message forms (docs/ARCHITECTURE_V2.md section 10.2)
               "skip this", "skip this one", "skip it", "next one", "next question", "answer", "the answer",
               "what's the answer", "whats the answer", "what is the answer", "tell me the answer"}
_HINT_EXACT = {"hint", "a hint", "give me a hint", "help", "help me", "stuck", "i'm stuck", "im stuck",
               "i don't get it", "i dont get it", "i don't understand", "i dont understand",
               "how do i start", "what do i do", "explain", "?",
               "another hint", "more help", "clue", "a clue", "i'm confused", "im confused", "confused",
               "how do i do this", "how do i do it", "can you help", "can you help me"}
_HINT_WORDS = ("hint", "help", "stuck", "don't get", "dont get", "don't understand",
               "dont understand", "how do i", "how to")
_SKIP_WORDS = ("skip", "don't know", "dont know", "idk", "give up", "no idea")
# "can I have a hint please" -> "hint"; "I need help" -> "help"
_ASK_HEAD = re.compile(r"^(?:(?:can|could|may) i (?:have|get|see)|i need|i want|i would like|i'd like|"
                       r"give me|show me|need|please)\s+(?:a |an |another |some |more |the )?")
_COURTESY_TAIL = re.compile(r"(?:\s+(?:please|pls|plz|thanks|thank you|thx|now))+$")


@functools.lru_cache(maxsize=4096)
def _phrase_rx(phrase: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])")


def _contains(norm: str, phrase: str) -> bool:
    return _phrase_rx(phrase).search(norm) is not None


def _safety_text(text: str) -> str:
    norm = re.sub(r"[-.,]", " ", normalize(text))
    for rx, rep in _SAFETY_REWRITES:
        norm = rx.sub(rep, norm)
    return re.sub(r"\s+", " ", norm).strip()


def is_distress(text: str) -> bool:
    norm = _safety_text(text)
    if not norm:
        return False
    if any(_contains(norm, p) for p in _DISTRESS):
        return True
    return any(rx.search(norm) for rx in _DISTRESS_RE)


def is_cheat_request(text: str) -> bool:
    norm = normalize(text)
    return any(rx.search(norm) for rx in _CHEAT_RE)


def exact_intent(text: str) -> str | None:
    """"hint" / "skip" when the WHOLE message is a command ("skip", "I'm not sure.", "can I have a hint
    please"), else None.  In a lesson these count before marking, unless the text is the correct answer."""
    if text is None or any(c.isdigit() for c in text):
        return None
    if text.strip() == "?":
        return "hint"
    norm = normalize(text)
    if not norm:
        return None
    bare = norm.strip(" .,!?")             # "I'm not sure." is the exact phrase "i'm not sure"
    canon = _ASK_HEAD.sub("", _COURTESY_TAIL.sub("", bare)).strip()
    for cand in (norm, bare, canon):
        if cand in _SKIP_EXACT:
            return "skip"
        if cand in _HINT_EXACT:
            return "hint"
    return None


def loose_intent(text: str) -> str | None:
    """"hint" / "skip" when a command phrase occurs anywhere in the text ("this is hard, I need help").
    In a lesson these count only when the checker found no answer (docs/ARCHITECTURE_V2.md section 10.2)."""
    if text is None or any(c.isdigit() for c in text):
        return None
    norm = normalize(text)
    if not norm:
        return None
    if any(_contains(norm, p) for p in _HINT_WORDS):
        return "hint"
    if any(_contains(norm, p) for p in _SKIP_WORDS):
        return "skip"
    return None


def intent(text: str) -> str | None:
    """Exact command phrases first, then command phrases anywhere in the text."""
    return exact_intent(text) or loose_intent(text)
