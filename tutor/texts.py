"""All user-facing texts and keyboards, verbatim from docs/ARCHITECTURE.md section 4
and docs/ARCHITECTURE_V2.md section 3.1."""
from __future__ import annotations

from typing import Iterable, Sequence

from .content import CHOICE_LETTERS
from .messages import Keyboard

# 4.1 kept from the original flow
CODE_REQUEST = "🔐 Please enter your access code to start the lesson."
CODE_BAD = "❌ That code isn't valid. Please check it and try again."
CODE_OK = "✅ Code accepted — welcome! You're all set."
YEAR_ASK = "🎓 Great! Which year group are you in? Tap the button below (British school system, Year 1–13)."
TOPIC_ASK = "📚 What are you working on right now? Here's what students usually study in Year {year} — tap one, or choose «My own topic»."
OWN_TOPIC_ASK = "✍️ Tell me what you'd like to practise and I'll set problems on it."
TOPIC_START = "🎯 Got it — switching to «{topic}». Let's start with an easy one."
PROBLEM = "Problem {n}: {text}\n\nSend me your answer (and show your working!) 😊"
CORRECT = "✅ Correct! {solution}."
WRONG = "❌ Not quite. {why}. Correct answer: {answer}"

# 4.2 new
SUBJECT_ASK = "📘 Which subject would you like to study? (Year {year}, British curriculum)"
YEAR_NOT_READY = "🚧 Sorry — I don't have lessons for {year_label} yet. Please choose another year group."
PROBLEM_EXAM = "Problem {n} ({marks} mark{s}): {text}\n\nSend me your answer (and show your working!) 😊"
WHY_FALLBACK = "Here's the method: {solution}"
HINT = "💡 Hint: {hint}"
HINT_AGAIN = "💡 Hint: {hint}\n\nStill stuck? Type «skip» and I'll show you the full solution."
HINT_LLM = "💡 {text}"
LLM_CHAT = "{text}"
SKIP = "👀 No problem — here's how to do it: {solution}. Answer: {answer}"
UNPARSED = "🤔 I couldn't find an answer in that. Put your final answer on the last line — or type «hint» for a hint, or «skip» to see the solution."
OFFTOPIC = "🙂 Let's keep our focus on {subject}! Have a go at Problem {n} — or type «hint» for a hint, or «skip» to see the solution."
CHEAT = "🙅 I can't do homework, write essays or give out test answers for you — but I can help you learn to do it yourself, step by step! Pick a topic below or choose «My own topic» and we'll practise together. 💪"
DISTRESS = "💙 I'm really sorry you're feeling like this, and thank you for telling me. You don't have to deal with it on your own. Please talk to a parent, a teacher or another adult you trust as soon as you can. If you are in danger right now, contact your local emergency services straight away. I'm here to help with your schoolwork whenever you're ready."
OWN_TOPIC_NONE = "🤷 Sorry — I can't set problems on that yet. Tap one of the topics below, or describe what you'd like to practise in a different way."
UNMARKABLE = "📝 I can't mark written answers automatically yet, so here's a model answer to compare with yours: {answer}"
TEXT_ONLY = "📝 I can only read text for now — please type your answer."
DELETED = "🗑️ Done — I've deleted your data. If you'd like to come back, send /start and enter a new access code."
ERROR = "⚠️ Sorry, something went wrong. Please try again."

# v2 (docs/ARCHITECTURE_V2.md section 3.1)
PROBLEM_CHOICE = "Problem {n}: {text}\n\nReply with the letter of your answer — tap a button below 😊"
PROBLEM_CHOICE_EXAM = "Problem {n} (1 mark): {text}\n\nReply with the letter of your answer — tap a button below 😊"
PROBLEM_SHORT = "Problem {n}: {text}\n\nSend me your answer — just the word or short phrase 😊"
PROBLEM_SHORT_EXAM = "Problem {n} (1 mark): {text}\n\nSend me your answer — just the word or short phrase 😊"
PROBLEM_RUBRIC = ("Problem {n} (extended practice, {marks} mark{s}): {text}\n\n"
                  "Write your answer, then I'll show you a model answer to compare with yours 😊")
CORRECT_NOTE = "✅ Correct! {solution}. {note}"
CHOICE_UNPARSED = "🤔 Please reply with just one letter: {letters}. Or type «hint» for a hint, or «skip» to see the solution."
SHORT_UNPARSED = ("🤔 I couldn't find one clear answer in that. Send just the word or short phrase — "
                  "or type «hint» for a hint, or «skip» to see the solution.")
WHY_FACT = "Here's why: {solution}"

# Keyboards
CHANGE_YEAR = "🎓 Change year"
CHANGE_SUBJECT = "📘 Change subject"
LEGACY_CHANGE = "⚙️ Change year / topic"
PAST_PAPER = "Past paper practice"
MY_OWN_TOPIC = "My own topic"

YEAR_KB: Keyboard = (
    ("Year 7", "Year 8", "Year 9"),
    ("Year 10", "Year 11", "Year 12"),
    ("Year 13", "Year 1–6"),
)


def subject_kb(titles: Iterable[str]) -> Keyboard:
    titles = list(titles)
    rows = tuple(tuple(titles[i:i + 2]) for i in range(0, len(titles), 2))
    return rows + ((CHANGE_YEAR,),)


def topic_kb(rows: Sequence[Sequence[str]]) -> Keyboard:
    return tuple(tuple(r) for r in rows) + (
        (PAST_PAPER, MY_OWN_TOPIC),
        (CHANGE_YEAR, CHANGE_SUBJECT),
    )


def choice_kb(n: int, rows: Sequence[Sequence[str]]) -> Keyboard:
    """The letter row (A..) on top of the usual lesson keyboard."""
    return (tuple(CHOICE_LETTERS[:n]),) + topic_kb(rows)


# 4.3 owner texts
CODES = "🔑 {n} new code{s}:\n{codes}"
CODES_USAGE = "Usage: /codes N (N = 1–50)"
NO_STUDENTS = "No students yet."
STUDENTS = "👥 Students ({n}):\n{lines}"
STUDENTS_LINE = "{chat_id} · {name} · {status} · Year {year} · {subject} · last seen {date}"
STUDENT = (
    "👤 {name} (chat {chat_id})\nStatus: {status}\nYear {year} · Subject: {subject} · Topic: {topic}\n"
    "Levels: {levels}\nAttempts: {total} ({correct} correct)\nRecent:\n{recent}"
)
STUDENT_RECENT_LINE = "{datetime} {skill} L{level} {mark}"
STUDENT_USAGE = "Usage: /student CHAT_ID"
RESET_USAGE = "Usage: /reset CHAT_ID"
NOT_FOUND = "Student {chat_id} not found."
RESET_OK = "✅ Student {chat_id} has been reset — they need a new code."
NO_FLAGS = "No new flags."
FLAGS = "🚩 {n} new flag{s}:\n{lines}\nWhen you have dealt with them, send /flags done {last}"
FLAGS_LINE = "#{id} {datetime} {kind} · chat {chat_id} ({name}): {text}"
FLAGS_DONE = "✅ {n} flag{s} marked as reviewed."
FLAGS_USAGE = "Usage: /flags (list new flags), /flags done [N] (mark flags up to #N as reviewed)"
FLAG_ALERT = "🚩 Safety flag ({kind}) from {name} (chat {chat_id}):\n\"{text}\"\nUse /student {chat_id} for details."
# docs/ARCHITECTURE_V2.md section 10.2: with a problem open, the alert and the stored flag name it,
# so the owner can tell a curriculum answer from a real disclosure
FLAG_PROBLEM = "Open problem: {ref} (the message may be an answer to it)"
FLAG_TEXT_REF = "[open problem: {ref}] {text}"
CODE_ALERT = "🚩 {n} wrong access codes from {name} (chat {chat_id}) in the last hour — someone may be guessing codes. Use /student {chat_id} for details."
STATS = (
    "📊 Stats\nStudents: {total} ({verified} verified, {active7} active in 7 days)\n"
    "Attempts: {today} today, {week} in 7 days ({acc}% correct)\nUnused codes: {codes}\n"
    "LLM calls today: {llm}\nUnreviewed flags: {flags}"
)
