"""Shared helpers for the tutor engine tests.

Golden texts are hard-coded here on purpose (docs/ARCHITECTURE.md section 4);
tutor/texts.py is never imported by the tests.
"""
import math
import os
import random
import re
import sys
import time
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

START = 1_700_000_000.0   # 2023-11-14 22:13:20 UTC
CODE_RE = re.compile(r"^[A-HJ-NP-Z2-9]{8}$")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

# --------------------------------------------------------------------------
# Golden texts (section 4), hard-coded
# --------------------------------------------------------------------------
CODE_REQUEST = "🔐 Please enter your access code to start the lesson."
CODE_BAD = "❌ That code isn't valid. Please check it and try again."
CODE_OK = "✅ Code accepted — welcome! You're all set."
YEAR_ASK = "🎓 Great! Which year group are you in? Tap the button below (British school system, Year 1–13)."
OWN_TOPIC_ASK = "✍️ Tell me what you'd like to practise and I'll set problems on it."
ASK_ANSWER_TAIL = "\n\nSend me your answer (and show your working!) 😊"
HINT_AGAIN_TAIL = "\n\nStill stuck? Type «skip» and I'll show you the full solution."
UNPARSED = "🤔 I couldn't find an answer in that. Put your final answer on the last line — or type «hint» for a hint, or «skip» to see the solution."
CHEAT = "🙅 I can't do homework, write essays or give out test answers for you — but I can help you learn to do it yourself, step by step! Pick a topic below or choose «My own topic» and we'll practise together. 💪"
DISTRESS = "💙 I'm really sorry you're feeling like this, and thank you for telling me. You don't have to deal with it on your own. Please talk to a parent, a teacher or another adult you trust as soon as you can. If you are in danger right now, contact your local emergency services straight away. I'm here to help with your schoolwork whenever you're ready."
OWN_TOPIC_NONE = "🤷 Sorry — I can't set problems on that yet. Tap one of the topics below, or describe what you'd like to practise in a different way."
TEXT_ONLY = "📝 I can only read text for now — please type your answer."
DELETED = "🗑️ Done — I've deleted your data. If you'd like to come back, send /start and enter a new access code."
ERROR = "⚠️ Sorry, something went wrong. Please try again."

NO_STUDENTS = "No students yet."
CODES_USAGE = "Usage: /codes N (N = 1–50)"
STUDENT_USAGE = "Usage: /student CHAT_ID"
RESET_USAGE = "Usage: /reset CHAT_ID"
NO_FLAGS = "No new flags."

FORM_STANDARD = "That's the right value, but it needs to be in standard form (a × 10^n, with 1 ≤ a < 10)"
FORM_FACTORISED = "That's equivalent, but the question asks you to factorise — write it as brackets multiplied together"
FORM_EXPANDED = "That's equivalent, but the question asks you to expand — multiply out all the brackets"
FORM_SIMPLEST = "That's equivalent, but it isn't in its simplest form yet"

CHANGE_YEAR = "🎓 Change year"
CHANGE_SUBJECT = "📘 Change subject"
LEGACY_CHANGE = "⚙️ Change year / topic"
PAST = "Past paper practice"
OWN = "My own topic"

BASE_PROMPT = (
    "You are a friendly, patient tutor for secondary-school students (age 11–16) in the British "
    "school system, helping with {subject} (Year {year}). Reply in simple English, plain text only "
    "(no Markdown, no LaTeX), at most 80 words. Only help with schoolwork; if the student goes "
    "off-topic, kindly steer them back to the problem. Never do homework, write essays or give test "
    "answers for them — teach step by step instead. Never ask for personal information. The correct "
    "answer below was verified by a computer and is always right: never contradict it."
)
SUFFIX_HINT = "Do NOT reveal the answer or the final value. Give at most one next step."
SUFFIX_FEEDBACK = ("The student's answer was wrong. In 1–2 sentences, kindly explain where their working "
                   "most likely went wrong. Do not start with 'Not quite' and do not restate the correct answer.")


def SUBJECT_ASK(year):
    return f"📘 Which subject would you like to study? (Year {year}, British curriculum)"


def TOPIC_ASK(year):
    return (f"📚 What are you working on right now? Here's what students usually study in "
            f"Year {year} — tap one, or choose «My own topic».")


def TOPIC_START(label):
    return f"🎯 Got it — switching to «{label}». Let's start with an easy one."


def YEAR_NOT_READY(label):
    return f"🚧 Sorry — I don't have lessons for {label} yet. Please choose another year group."


def PROBLEM(n, text):
    return f"Problem {n}: {text}{ASK_ANSWER_TAIL}"


def PROBLEM_EXAM(n, marks, text):
    s = "" if marks == 1 else "s"
    return f"Problem {n} ({marks} mark{s}): {text}{ASK_ANSWER_TAIL}"


def CORRECT(solution):
    return f"✅ Correct! {solution.rstrip('. ')}."


def WRONG(why, answer):
    return f"❌ Not quite. {why.rstrip('. ')}. Correct answer: {answer}"


def WHY_FALLBACK(solution):
    return f"Here's the method: {solution.rstrip('. ')}"


def HINT(hint):
    return f"💡 Hint: {hint}"


def HINT_AGAIN(hint):
    return f"💡 Hint: {hint}{HINT_AGAIN_TAIL}"


def SKIP(solution, answer):
    return f"👀 No problem — here's how to do it: {solution.rstrip('. ')}. Answer: {answer}"


def OFFTOPIC(subject, n):
    return (f"🙂 Let's keep our focus on {subject}! Have a go at Problem {n} — "
            f"or type «hint» for a hint, or «skip» to see the solution.")


def UNMARKABLE(answer):
    return f"📝 I can't mark written answers automatically yet, so here's a model answer to compare with yours: {answer}"


def FLAG_ALERT(kind, name, chat, text):
    return (f"🚩 Safety flag ({kind}) from {name} (chat {chat}):\n\"{text}\"\n"
            f"Use /student {chat} for details.")


# --------------------------------------------------------------------------
# Keyboards (section 4.2)
# --------------------------------------------------------------------------
YEAR_KB = (("Year 7", "Year 8", "Year 9"), ("Year 10", "Year 11", "Year 12"), ("Year 13", "Year 1–6"))
SUBJECT_KB_11 = (("Maths", "Physics"), (CHANGE_YEAR,))
SUBJECT_KB_MATHS_ONLY = (("Maths",), (CHANGE_YEAR,))
BOTTOM = ((PAST, OWN), (CHANGE_YEAR, CHANGE_SUBJECT))


def topic_kb(rows):
    return tuple(tuple(r) for r in rows) + BOTTOM


MATHS_ROWS_10_11 = (("GCSE Higher: algebra & functions", "GCSE Higher: trig & geometry"),
                    ("GCSE Foundation: number", "GCSE Foundation: geometry"))
MATHS_ROWS_KS3 = (("KS3: number & fractions", "KS3: algebra"), ("KS3: geometry", "KS3: ratio & percentages"))
PHYSICS_ROWS = (("Forces & motion", "Energy"), ("Electricity", "Density & pressure"))
TOPIC_KB_MATHS_11 = topic_kb(MATHS_ROWS_10_11)
TOPIC_KB_KS3 = topic_kb(MATHS_ROWS_KS3)
TOPIC_KB_PHYSICS = topic_kb(PHYSICS_ROWS)

HIGHER_ALGEBRA = "GCSE Higher: algebra & functions"
FOUNDATION_NUMBER = "GCSE Foundation: number"


# --------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------
class FakeClock:
    def __init__(self, start=START):
        self.now = float(start)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds
        return self.now


class FakeLLM:
    """Returns queued items (str or None); records (system, user) calls."""

    def __init__(self, responses=()):
        self.responses = list(responses)
        self.calls = []

    def complete(self, system, user, max_tokens=300):
        self.calls.append((system, user))
        if self.responses:
            return self.responses.pop(0)
        return None


_SHARED = {}


def shared_registry():
    if "reg" not in _SHARED:
        from tutor.content import load_registry
        _SHARED["reg"] = load_registry()
    return _SHARED["reg"]


def make_engine(llm=None, owner_id=999, limit=40, registry=None, path=":memory:", flood=20):
    from tutor.config import Config
    from tutor.db import Store
    from tutor.engine import Engine
    clock = FakeClock()
    store = Store(path)
    cfg = Config(owner_id=owner_id, llm_daily_limit=limit, flood_per_minute=flood, db_path=path)
    reg = registry if registry is not None else shared_registry()
    engine = Engine(store, cfg, registry=reg, llm=llm, clock=clock, rng=random.Random(7))
    return engine, store, clock


def send(engine, chat, text, user=None, first_name="Zorblax", username="", chat_type="private"):
    from tutor.messages import Incoming
    return engine.handle(Incoming(chat_id=chat, user_id=chat if user is None else user, text=text,
                                  first_name=first_name, username=username, chat_type=chat_type))


def get_codes(engine, n, owner=999):
    out = send(engine, owner, f"/codes {n}")
    codes = []
    for o in out:
        for line in o.text.splitlines():
            if CODE_RE.match(line):
                codes.append(line)
    return codes


def verify(engine, chat, first_name="Zorblax", username="", owner=999):
    code = get_codes(engine, 1, owner)[0]
    return send(engine, chat, code, first_name=first_name, username=username)


def to_topic(engine, chat, subject="Maths", topic=HIGHER_ALGEBRA, year=None, first_name="Zorblax"):
    """Verify the chat, optionally switch year, pick subject and topic. Returns the replies of the topic pick."""
    verify(engine, chat, first_name=first_name)
    if year is not None:
        send(engine, chat, CHANGE_YEAR, first_name=first_name)
        send(engine, chat, f"Year {year}", first_name=first_name)
    send(engine, chat, subject, first_name=first_name)
    return send(engine, chat, topic, first_name=first_name)


def answer_of(store, chat):
    return store.get_pending(chat).problem.answer.display


def snap(replies):
    """Normalise Outgoing objects to comparable tuples (chat, text, keyboard, remove_keyboard)."""
    return [(o.chat_id, o.text, None if o.keyboard is None else tuple(tuple(r) for r in o.keyboard),
             bool(o.remove_keyboard)) for o in replies]


def S(chat, text, kb=None, remove=False):
    return (chat, text, kb, remove)


def day_of(clock):
    return time.strftime("%Y-%m-%d", time.gmtime(clock()))


def stamp(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts))


def keyboard_problem(replies, chat, titles=("Maths", "Physics", "Demo")):
    """Section 3.7 invariant. Returns None when fine, else a description."""
    mine = [o for o in replies if o.chat_id == chat]
    if not mine:
        return None
    last = mine[-1]
    if last.text == ERROR:
        return None
    for o in mine[:-1]:
        if o.keyboard is not None or o.remove_keyboard:
            return f"keyboard on a non-last message: {o.text[:40]!r}"
    kb = None if last.keyboard is None else tuple(tuple(r) for r in last.keyboard)
    if kb is None:
        return f"last message has no keyboard: {last.text[:60]!r}"
    if kb == YEAR_KB:
        return None
    flat = [b for row in kb for b in row]
    if CHANGE_YEAR in flat and (CHANGE_SUBJECT in flat or any(t in flat for t in titles)):
        return None
    return f"bad keyboard {kb!r} on {last.text[:60]!r}"


def flat(kb):
    return [b for row in kb for b in row]


# --------------------------------------------------------------------------
# perturb (section 6)
# --------------------------------------------------------------------------
def _fmt(x):
    s = f"{x:.9f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _frac_str(fr):
    return str(fr.numerator) if fr.denominator == 1 else _fmt(float(fr))


def perturb(answer):
    k = answer.kind
    if k == "number":
        v = float(answer.value)
        nv = v + max(1.0, abs(v) * 0.5)
        if answer.form == "standard":
            e = math.floor(math.log10(abs(nv)))
            m = nv / (10 ** e)
            return f"{_fmt(m)} × 10^{e}"
        return _fmt(nv)
    if k == "fraction":
        return str(Fraction(answer.value) + 1)
    if k == "set":
        vals = [Fraction(x) for x in answer.value]
        new = [_frac_str(max(vals) + 1)] + [str(x) for x in answer.value[1:]]
        return ", ".join(new)
    if k == "assign":
        items = list(answer.value.items())
        first_k, first_v = items[0]
        parts = [f"{first_k} = {_frac_str(Fraction(first_v) + 1)}"] + [f"{a} = {b}" for a, b in items[1:]]
        return ", ".join(parts)
    if k == "expr":
        return f"({answer.value})+1"
    if k == "ratio":
        parts = list(answer.value)
        return ":".join(str(x) for x in [parts[0] + 1] + parts[1:])
    return ""


# --------------------------------------------------------------------------
# Deterministic demo registry (custom subject) for lesson / llm tests
# --------------------------------------------------------------------------
DEMO_FLAGS = {"boom": False}
DEMO_ROWS = (("Arithmetic", "Adding"), ("Written", "Fragile"), ("Fractions only", "Standard only"))
DEMO_TOPIC_KB = topic_kb(DEMO_ROWS)
DEMO_SUBJECT_KB = (("Demo",), (CHANGE_YEAR,))


def demo_registry():
    from tutor.content import (Answer, Mistake, Problem, Registry, Skill, Subject, Topic, YearSpec)

    def add_gen(sid):
        def gen(level, seed):
            if sid == "demo.fragile" and DEMO_FLAGS["boom"]:
                raise RuntimeError("generator exploded")
            r = random.Random(seed)
            a, b = r.randint(10, 49), r.randint(10, 49)
            s = a + b
            return Problem(sid, level, seed, f"What is {a} + {b}?",
                           Answer("number", str(s), float(s)), f"{a} + {b} = {s}", "Add the units first",
                           (Mistake(Answer("number", str(s + 1), float(s + 1)), "You were out by one"),))
        return gen

    def mul_gen(level, seed):
        r = random.Random(seed)
        a, b = r.randint(3, 12), r.randint(3, 12)
        p = a * b
        return Problem("demo.mul", level, seed, f"What is {a} × {b}?",
                       Answer("number", str(p), float(p)), f"{a} × {b} = {p}", "Use your times tables")

    def frac_gen(level, seed):
        r = random.Random(seed)
        a, b = r.choice([(3, 4), (2, 3), (5, 6)])
        return Problem("demo.frac", level, seed, f"Write {2 * a}/{2 * b} in its simplest form.",
                       Answer("fraction", f"{a}/{b}", f"{a}/{b}", form="simplest"),
                       f"Divide top and bottom by 2 to get {a}/{b}", "Find a common factor")

    def std_gen(level, seed):
        r = random.Random(seed)
        n = r.choice([32000, 45000, 120000])
        e = len(str(n)) - 1
        m = n / 10 ** e
        disp = f"{m:g} × 10^{e}"
        return Problem("demo.std", level, seed, f"Write {n} in standard form.",
                       Answer("number", disp, float(n), form="standard"),
                       f"{n} = {disp}", "Move the decimal point")

    def essay_gen(level, seed):
        return Problem("demo.essay", level, seed, "Explain why plants need light.",
                       Answer("rubric", "Because plants need light for photosynthesis", None,
                              mark_scheme="1 mark for light; 1 mark for energy", max_marks=2),
                       "Plants use light for photosynthesis", "Think about energy")

    def sk(sid, title, aliases, gen):
        return Skill(sid, "demo", title, tuple(aliases), gen)

    skills = [
        sk("demo.add", "Adding", ["adding", "addition"], add_gen("demo.add")),
        sk("demo.mul", "Multiplying", ["multiplying"], mul_gen),
        sk("demo.fragile", "Fragile", ["fragile"], add_gen("demo.fragile")),
        sk("demo.frac", "Simplest fractions", ["simplest fractions"], frac_gen),
        sk("demo.std", "Standard forms", ["standard forms"], std_gen),
        sk("demo.essay", "Essays", ["essay"], essay_gen),
    ]
    rows = (
        (Topic("demo.y11.arith", "Arithmetic", ("demo.add", "demo.mul")),
         Topic("demo.y11.adding", "Adding", ("demo.add",))),
        (Topic("demo.y11.written", "Written", ("demo.essay",)),
         Topic("demo.y11.fragile", "Fragile", ("demo.fragile",))),
        (Topic("demo.y11.frac", "Fractions only", ("demo.frac",)),
         Topic("demo.y11.std", "Standard only", ("demo.std",))),
    )
    reg = Registry()
    reg.register(Subject("demo", "Demo", 1, {11: YearSpec(rows=rows)}), skills)
    return reg


def to_demo_topic(engine, chat, topic, first_name="Zorblax"):
    verify(engine, chat, first_name=first_name)
    send(engine, chat, "Demo", first_name=first_name)
    return send(engine, chat, topic, first_name=first_name)
